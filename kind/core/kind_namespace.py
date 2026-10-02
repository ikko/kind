import datetime
import gc
import inspect
import warnings
from sys import getsizeof
from typing import Any, Iterator, Literal, Optional, Set, Type, Union

import orjson
from kind.core.lazy import SENTINEL
from kind.core.maturing import _apply_merge_strategy, deep_del

from kind.core.mixinability import freeze, is_frozen
from kind.core.kind import Kind
from kind.core.lazy_kind import LazyKind
from kind.core.mixinability import apply_mixin_to_instance
from kind.core.mixins import _get_available_mixins
from kind.core.type_var_t import T


class KindNamespace:
    """Provides a convenient way to create Kind instances via attribute access."""
    def __getattr__(self, name):
        return Kind(name)

    def __getitem__(self, name):
        return Kind(name)

    def __setitem__(self, name, value):
        raise TypeError(f"KindNamespace is read-only, cannot set {name} to {value}")

    def __setattr__(self, name, value):
        raise TypeError(f"KindNamespace is read-only, cannot set {name} to {value}")

    def patch(self, other: 'Kind') -> 'Kind':
        if other.origin and not self.origin:
            self.origin = other.origin
        for attr in ("children", "parents"):
            existing = getattr(self, attr)
            new = getattr(other, attr)
            for e in new:
                if e not in existing:
                    existing.append(e)
        # Patch relations
        for how, related_kinds in other.relations.items():
            for related_kind in related_kinds:
                self.relate(related_kind, how=how)
        return self

    def relate(self, other: 'Kind', how: str = 'related') -> 'Kind':
        """Establishes a bidirectional relationship with another Kind."""
        with self._lock:
            # Add forward relationship
            self.relations.add(how, other)

            # Establish inverse relationship
            inverse_how = f"_inverse_{how}"
            other.relations.add(inverse_how, self)
        return self

    def unrelate(self, other: 'Kind', how: Optional[str] = None) -> 'Kind':
        """Removes a bidirectional relationship with another Kind."""
        with self._lock:
            # Remove forward relationship
            if how is None:
                # Remove all relationships with 'other'
                hows_to_remove = [h for h, kinds in self.relations.items() if other in kinds]
                for h in hows_to_remove:
                    self.relations.remove(h, other)
            else:
                self.relations.remove(how, other)

            # Remove inverse relationship
            if how is None:
                hows_to_remove_inverse = [h for h, kinds in other.relations.items() if self in kinds and h.startswith('_inverse_')]
                for h in hows_to_remove_inverse:
                    other.relations.remove(h, self)
            else:
                inverse_how = f"_inverse_{how}"
                other.relations.remove(inverse_how, self)
        return self



    @property
    def ref(self) -> Optional[Any]:
        """Alias for .origin, representing the original source or reference of the Kind."""
        return self.origin

    def head(self, up_to_position: float = 5.0):
        cur = self
        while cur._prev and cur._prev._position >= up_to_position:
            cur = cur._prev
        return cur

    def tail(self, from_position: float = -10.0):
        cur = self
        while cur._next and cur._next._position <= from_position:
            cur = cur._next
        return cur

    @classmethod
    def auto_date(cls) -> 'Kind':
        iso = datetime.date.today().isoformat()
        return cls(iso)

    @classmethod
    def auto_datetime(cls) -> 'Kind':
        iso = datetime.datetime.now().isoformat()
        return cls(iso)

    @classmethod
    def auto_time(cls) -> 'Kind':
        iso = datetime.datetime.now().time().isoformat()
        return cls(iso)

    @classmethod
    def next(cls) -> 'Kind':
        with cls._lock:
            last = cls.last()
            name = f"kind_{cls._auto_counter}"
            kind = cls(name)
            kind._position = cls._auto_counter  # Set position for AVLTree
            cls._numbered.insert(cls._numbered.root, kind, kind._position) # Insert into AVLTree
            if last:
                last._next = kind
                kind._prev = last
            cls._auto_counter += 1
        return kind

    @classmethod
    def prev(cls) -> Optional['Kind']:
        with cls._lock:
            if cls._auto_counter <= 0:
                return None
            cls._auto_counter -= 1
            # Search for the kind at the decremented position
            node = cls._numbered.search(cls._auto_counter)
            return node.kind if node else None

    @classmethod
    def first(cls) -> Optional['Kind']:
        node = cls._numbered.min_node()
        return node.value if node else None

    @classmethod
    def last(cls) -> Optional['Kind']:
        node = cls._numbered.max_node()
        return node.value if node else None

    @classmethod
    def len(cls) -> int:
        return cls._numbered.size()

    @classmethod
    def from_object(cls, obj: Any) -> 'Kind':
        """Converts an object to a Kind, acting as a central router."""
        if isinstance(obj, Kind):
            return obj
        if isinstance(obj, LazyKind):
            return obj._kind

        # Conversion functions for different types
        def from_list(value: list) -> 'Kind':
            kind = cls('list', origin=value)
            for item in value:
                kind.append(LazyKind(item))
            return kind

        def from_dict(value: dict) -> 'Kind':
            kind = cls('dict', origin=value)
            for k, v in value.items():
                key_kind = LazyKind(k)
                val_kind = LazyKind(v)
                kind.append(key_kind)
                key_kind.append(val_kind)
            return kind

        def from_tuple(value: tuple) -> 'Kind':
            kind = cls('tuple', origin=value)
            for item in value:
                kind.append(LazyKind(item))
            return kind

        def from_set(value: set) -> 'Kind':
            kind = cls('set', origin=value)
            for item in value:
                kind.append(LazyKind(item))
            return kind

        type_map = {
            list: from_list,
            dict: from_dict,
            tuple: from_tuple,
            set: from_set,
            int: lambda v: cls(str(v), origin=v),
            float: lambda v: cls(str(v), origin=v),
            str: lambda v: cls(v, origin=v),
            bool: lambda v: cls(str(v), origin=v),
            type(None): lambda v: cls('None', origin=v)
        }

        # Try to find a specific from_ method
        obj_type = type(obj)
        if obj_type in type_map:
            return type_map[obj_type](obj)
        else:
            try:
                name = orjson.dumps(obj).decode()
                return cls(name, origin=obj)
            except (TypeError, orjson.JSONEncodeError) as e:
                import logging
                logging.error(f"Cannot convert {obj_type} to Kind: {repr(e)}", exc_info=True)
                raise TypeError(f"Cannot convert {obj_type} to Kind: {repr(e)}")

    @classmethod
    def seek(cls, pos: float) -> Optional['Kind']:
        node = cls._numbered.search(pos)
        return node.value if node else None

    @classmethod
    def each(cls, start: Union[float, 'Kind', None] = None) -> Iterator['Kind']:
        if start is None:
            # Iterate through all kinds in order
            for node in cls._numbered.inorder_traverse():
                yield node.value
        elif isinstance(start, (int, float)):
            # Find the kind at or after the given position and iterate from there
            for node in cls._numbered.inorder_traverse(start_key=start):
                yield node.value
        elif isinstance(start, Kind):
            # Find the starting kind and iterate from there
            for node in cls._numbered.inorder_traverse(start_key=start._position):
                yield node.value
        else:
            raise TypeError(f"Invalid start parameter {repr(start)} instance of {type(start)} in each")

    def each_parents(self) -> Iterator['Kind']:
        return iter(self.parents)

    def each_children(self) -> Iterator['Kind']:
        return iter(self.children)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def elevate(self, merge_strategy: Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth'] = 'smooth') -> Set[str]:
        """Elevates metadata entries to instance attributes/methods based on a merge strategy."""
        if is_frozen():
            warnings.warn(f"Cannot elevate on frozen Kind {self.name}")
            return set()

        elevated_keys = set()
        keys_to_remove = []

        for key, value in list(self.metadata.items()): # Iterate over a copy to allow modification
            if hasattr(self, key) and key not in self.__slots__ and key not in self.__class__.__bases__[0].__slots__:
                # This means it's an existing attribute not in slots, likely from a mixin or dynamic assignment
                current_value = getattr(self, key)
                if key.startswith('__') or inspect.ismethod(current_value) or inspect.isfunction(current_value):
                    warnings.warn(f"Overwriting internal attribute/method '{key}' on Kind {self.name}")
                merged_value = _apply_merge_strategy(current_value, value, merge_strategy)
                setattr(self, key, merged_value)
            elif key in self.__slots__ or key in self.__class__.__bases__[0].__slots__:
                # Attribute is part of __slots__, directly set it
                current_value = getattr(self, key)
                if key.startswith('__') or inspect.ismethod(current_value) or inspect.isfunction(current_value):
                    warnings.warn(f"Overwriting internal attribute/method '{key}' on Kind {self.name}")
                merged_value = _apply_merge_strategy(current_value, value, merge_strategy)
                setattr(self, key, merged_value)
            else:
                # Dynamically add to _elevated_attributes
                self._elevated_attributes[key] = value
            elevated_keys.add(key)
            keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.metadata[key]

        return elevated_keys

    def slim(self, protected_attributes: Optional[Set[str]] = None) -> None:
        """Removes dynamically applied attributes/methods that are not explicitly protected."""
        if is_frozen():
            warnings.warn(f"Cannot slim on frozen Kind {self.name}")
            return

        if protected_attributes is None:
            protected_attributes = set()

        # Combine attributes from __dict__ (if it exists) and __slots__
        all_attributes = list(getattr(self, '__dict__', {}).keys()) \
                       + list(self.__slots__) \
                       + list(self.__class__.__bases__[0].__slots__)

        for attr_name in all_attributes:
            if attr_name not in protected_attributes and not attr_name.startswith('__'):
                try:
                    value = getattr(self, attr_name)
                    if value is SENTINEL:
                        # Use deep_del for a safer deletion
                        deep_del(self, attr_name)
                except AttributeError:
                    # Attribute might not be set, which is fine
                    pass

        # Clean up elevated attributes that are SENTINEL
        for attr_name in list(self._elevated_attributes.keys()):
            if self._elevated_attributes[attr_name] is SENTINEL and attr_name not in protected_attributes:
                del self._elevated_attributes[attr_name]

        gc.collect()  # Explicitly call garbage collector after deletions

    def immute(self, merge_strategy: Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth'] = 'smooth') -> None:
        """Orchestrates the maturing process: elevates metadata, slims down, and freezes the Kind."""
        if is_frozen():
            warnings.warn(f"Kind {self.name} is already frozen. No action taken.")
            return

        # 1. Elevate metadata
        elevated_keys = self.elevate(merge_strategy=merge_strategy)

        # 2. Slim down
        self.slim(protected_attributes=elevated_keys)

        # 3. Freeze the Kind class (global state)
        freeze()

    def clear_context(self) -> None:
        """Clears the context DefDict, performing memory-aware deletion of its contents."""
        if is_frozen():
            warnings.warn(f"Cannot clear context on frozen Kind {self.name}")
            return

        # Iterate over a copy of keys to allow modification during iteration
        for key in list(self.context.keys()):
            # DefDict's __delitem__ will handle logging and potential deep_del for nested DefDicts
            del self.context[key]

    def to(self, target_type: Type[T]) -> T:
        """Converts the Kind to an object of the specified type."""
        try:
            return orjson.loads(self.name)
        except orjson.JSONDecodeError:
            raise TypeError(f"Cannot convert Kind '{self.name}' to {target_type}")

    @classmethod
    def ps(cls):
        """Lists all loaded kinds with their name, footprint, and origin."""
        total_footprint = 0
        output = ["{:<30} {:<15} {:<50}".format("Name", "Footprint (b)", "Origin")]
        output.append("-" * 95)

        for name, kind in sorted(cls._pool.items()):
            footprint = kind.footprint()
            total_footprint += footprint
            origin = kind.origin
            if origin is None:
                origin_str = f"{kind.__class__.__module__}.{kind.__class__.__name__}"
            else:
                origin_str = str(origin)
            output.append("{:<30} {:<15} {:<50}".format(name, footprint, origin_str))

        output.append("-" * 95)
        output.append("{:<30} {:<15}".format("Total", total_footprint))
        print("\n".join(output))

    @classmethod
    def ls(cls):
        """Lists all available mixin modules."""
        mixins = _get_available_mixins()
        print("Available Mixins:")
        for name in sorted(mixins.keys()):
            print(f"- {name}")

    def stat(self):
        """Provides detailed statistics about the kind and its mixins."""

        all_mixins = _get_available_mixins()
        output = [f"Statistics for Kind: '{self.name}'"]
        output.append("\n--- Mixin Analysis ---")
        output.append("{:<30} {:<15} {:<15}".format("Mixin Name", "Footprint (b)", "Slim Tag"))
        output.append("-" * 60)

        footprint_all_loaded = 0
        footprint_after_slim = 0
        slim_mixins = []

        for name, mixin_cls in sorted(all_mixins.items()):
            is_slim_tag = False

            # Create a temporary dummy kind to measure mixin size
            dummy_kind = Kind(f"dummy_for_{name}")
            apply_mixin_to_instance(dummy_kind, mixin_cls)

            footprint = dummy_kind.footprint()
            footprint_all_loaded += footprint

            # Check for non-sentinel values to determine slim tag
            for attr_name in dir(dummy_kind):
                if not attr_name.startswith('__') and not callable(getattr(dummy_kind, attr_name)):
                    try:
                        value = getattr(dummy_kind, attr_name)
                        if value is not SENTINEL:
                            is_slim_tag = True
                            break
                    except AttributeError:
                        pass

            tag = "slim tag" if is_slim_tag else ""
            if is_slim_tag:
                footprint_after_slim += footprint
            else:
                slim_mixins.append(name)

            output.append("{:<30} {:<15} {:<15}".format(name, footprint, tag))

        output.append("-" * 60)

        # 2. Self stats
        current_footprint = self.footprint()
        output.append("\n--- Kind Footprint ---")
        output.append(f"Current Footprint: {current_footprint} bytes")
        output.append(f"Footprint after .slim(): {footprint_after_slim} bytes")
        output.append(f"  (Would remove: {', '.join(slim_mixins)})")
        output.append(f"Footprint with all mixins loaded: {footprint_all_loaded} bytes")

        print("\n".join(output))

    def footprint(self) -> int:
        """Calculates the memory footprint of the kind and its descendants in bytes."""

        memo = set()

        def get_size(obj):
            if id(obj) in memo:
                return 0
            memo.add(id(obj))

            size = getsizeof(obj)
            if isinstance(obj, dict):
                size += sum(get_size(k) + get_size(v) for k, v in obj.items())
            elif isinstance(obj, (list, tuple, set, frozenset)):
                size += sum(get_size(i) for i in obj)
            elif hasattr(obj, '__dict__'):
                size += get_size(obj.__dict__)

            if hasattr(obj, '__slots__'):
                size += sum(get_size(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))

            # Special handling for Kind children to avoid recounting
            if isinstance(obj, Kind):
                # The size of the kind object itself is already counted.
                # Now, add the sizes of its direct attributes and mixins.
                if obj._index is not SENTINEL:
                    size += get_size(obj._index)
                if obj._metadata is not SENTINEL:
                    size += get_size(obj._metadata)
                if obj._context is not SENTINEL:
                    size += get_size(obj._context)
                size += get_size(obj._elevated_attributes)

                # Recursively calculate footprint of children, but avoid double counting
                for child in obj.children:
                    if id(child) not in memo:
                        size += child.footprint()

            return size

        return get_size(self)


k = KindNamespace()
