"""This module defines Kind: an interned, name-identified graph node.

A Kind stands for a category as data. It has one identity per name (see BaseKind),
children and parents (an ordered DAG), named relations with inverses, lazily created
metadata/context/index, attributes attached at runtime, and a per-instance freeze.
"""
import datetime
import inspect
import re
import warnings
from collections import deque
from itertools import chain
from sys import getsizeof
from typing import Any, Iterable, Iterator, Literal, Optional, Set, Type, TypeVar, Union

import orjson
import tomli_w
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from kind.builtin.collections import OrderedKindSet
from kind.builtin.index import KindIndex
from kind.core.base_kind import BaseKind
from kind.core.graph_traversal import GraphTraversal
from kind.core.lazy_kind import SENTINEL, LazyKind
from kind.core.maturing import DefDict, _apply_merge_strategy
from kind.core.mixinability import apply_mixin_to_instance
from kind.core.mixins import _get_available_mixins
from kind.core.relations import Relations

T = TypeVar("T")
MergeStrategy = Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth']

INVERSE_PREFIX = "_inverse_"

# Mermaid node shapes: node_shape -> (opening, closing) around the label.
MERMAID_SHAPES = {
    "round": ("(", ")"),
    "stadium": ("([", "])"),
    "subroutine": ("[[", "]]"),
    "cylindrical": ("[(", ")]"),
    "circle": ("((", "))"),
    "double_circle": ("(((", ")))"),
    "asymmetric": (">", "]"),
    "rhombus": ("{", "}"),
    "hexagon": ("{{", "}}"),
    "parallelogram": ("[/", "/]"),
    "parallelogram_alt": ("[\\", "\\]"),
    "trapezoid": ("[/", "\\]"),
    "trapezoid_alt": ("[\\", "/]"),
}
DEFAULT_SHAPE = ("[", "]")

# Slots that make up a Kind's identity and place in the graph: never set from metadata.
STRUCTURAL_SLOTS = frozenset({'name', 'parents', 'children', '_position', '_next', '_prev'})


def _is_settable(class_attribute: Any) -> bool:
    """True for slots and properties with a setter: the class-level attributes an instance may set."""
    if isinstance(class_attribute, property):
        return class_attribute.fset is not None
    return inspect.ismemberdescriptor(class_attribute)


class FrozenKindError(AttributeError):
    """Raised when a frozen Kind is asked to change."""


class Kind(BaseKind):
    __slots__ = (
        '_index',
        '_metadata',
        '_context',
        '_elevated_attributes',
        '_relations',
        '_frozen',
    )

    def _init_slots(self, name: str, origin: Optional[Any]) -> None:
        super()._init_slots(name, origin)
        set_slot = object.__setattr__
        set_slot(self, 'parents', OrderedKindSet())
        set_slot(self, 'children', OrderedKindSet())
        set_slot(self, '_elevated_attributes', {})
        set_slot(self, '_index', SENTINEL)
        set_slot(self, '_metadata', SENTINEL)
        set_slot(self, '_context', SENTINEL)
        set_slot(self, '_relations', SENTINEL)
        set_slot(self, '_frozen', False)

    # --- lazily created parts ----------------------------------------------

    @property
    def index(self) -> KindIndex:
        if self._index is SENTINEL:
            object.__setattr__(self, '_index', KindIndex(self))
        return self._index

    @property
    def metadata(self) -> DefDict:
        if self._metadata is SENTINEL:
            object.__setattr__(self, '_metadata', DefDict())
        return self._metadata

    @property
    def context(self) -> DefDict:
        if self._context is SENTINEL:
            object.__setattr__(self, '_context', DefDict())
        return self._context

    @property
    def relations(self) -> Relations:
        if self._relations is SENTINEL:
            object.__setattr__(self, '_relations', Relations(self))
        return self._relations

    @property
    def ref(self) -> Optional[Any]:
        """Alias for .origin: the source this Kind was made from."""
        return self.origin

    @ref.setter
    def ref(self, value: Any) -> None:
        self.origin = value

    # --- attribute protocol ------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """Elevated attributes first; any other public name is a dynamic relation verb.

        `a.has_kind(b)` relates a to b with how='has_kind'. Private names and names the
        class defines (e.g. a property whose getter failed) raise AttributeError instead.
        """
        try:
            elevated = object.__getattribute__(self, '_elevated_attributes')
        except AttributeError:
            raise AttributeError(name) from None
        if name in elevated:
            return elevated[name]
        if name.startswith('_') or hasattr(type(self), name):
            raise AttributeError(f"{type(self).__name__} {self.name!r} has no attribute {name!r}")
        return getattr(self.relations, name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._ensure_mutable()
        if _is_settable(getattr(type(self), name, None)):
            object.__setattr__(self, name, value)
        else:
            self._elevated_attributes[name] = value

    def __delattr__(self, name: str) -> None:
        self._ensure_mutable()
        if name in self._elevated_attributes:
            del self._elevated_attributes[name]
        else:
            object.__delattr__(self, name)

    # --- freezing ----------------------------------------------------------

    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> 'Kind':
        """Makes this Kind immutable: no attribute, edge or relation changes on it afterwards."""
        object.__setattr__(self, '_frozen', True)
        return self

    def _ensure_mutable(self) -> None:
        if object.__getattribute__(self, '_frozen'):
            raise FrozenKindError(f"Kind {self.name!r} is frozen (immute()/freeze()); it cannot change. "
                                  f"Hint: change it before maturing, or build a new Kind.")

    # --- graph construction ------------------------------------------------

    @classmethod
    def _coerce(cls, value: Any) -> 'Kind':
        if isinstance(value, Kind):
            return value
        if isinstance(value, LazyKind):
            return value.evaluate()
        return cls.from_object(value)

    def append(self, child: Any) -> 'Kind':
        """Links `child` under this Kind (idempotent) and returns the child."""
        child = self._coerce(child)
        with self._lock:
            self._ensure_mutable()
            child._ensure_mutable()
            self.children.add(child)
            child.parents.add(self)
        return child

    def add(self, child: Any) -> 'Kind':
        """Like append, but returns self, so calls can be chained."""
        self.append(child)
        return self

    def insert(self, child: Any, at: Optional[int] = None) -> 'Kind':
        """Places `child` at index `at` among the children (moving it if already there)."""
        child = self._coerce(child)
        with self._lock:
            self._ensure_mutable()
            child._ensure_mutable()
            self.children.discard(child)
            self.children.insert(len(self.children) if at is None else at, child)
            child.parents.add(self)
        return self

    def reparent(self) -> None:
        """Connects the children of this Kind directly to its parents."""
        with self._lock:
            for parent in list(self.parents):
                parent.children.discard(self)
                for child in self.children:
                    parent.children.add(child)
                    child.parents.discard(self)
                    child.parents.add(parent)

    def rebind_linear_sequence(self) -> None:
        """Removes this Kind from the Kind.next() chain, joining its neighbours."""
        with self._lock:
            if self._prev is not None:
                object.__setattr__(self._prev, '_next', self._next)
            if self._next is not None:
                object.__setattr__(self._next, '_prev', self._prev)
            object.__setattr__(self, '_prev', None)
            object.__setattr__(self, '_next', None)

    def delete(self) -> None:
        """Removes this Kind from the graph and the pool; its children move up to its parents."""
        with self._lock:
            self._ensure_mutable()
            self.reparent()
            self.rebind_linear_sequence()
            if self._index is not SENTINEL:
                self._index.remove(self)
            for how, related_kinds in list(self.relations.items()):
                for related_kind in list(related_kinds):
                    if how.startswith(INVERSE_PREFIX):
                        related_kind.unrelate(self, how=how[len(INVERSE_PREFIX):])
                    else:
                        self.unrelate(related_kind, how=how)
            for parent in self.parents:
                parent.children.discard(self)
            for child in self.children:
                child.parents.discard(self)
            self.parents.clear()
            self.children.clear()
            self._numbered.remove(self._position, self)
            if BaseKind._pool.get(self.name) is self:
                del BaseKind._pool[self.name]

    def pop(self) -> 'Kind':
        """Deletes this Kind (re-parenting its children) and returns it."""
        self.delete()
        return self

    def popleft(self) -> Optional['Kind']:
        """Deletes and returns the first child, or None."""
        if not self.children:
            return None
        child = self.children[0]
        child.delete()
        return child

    # --- traversal and rendering -------------------------------------------

    def graph(self) -> list['Kind']:
        return GraphTraversal(self, traverse_mode='dfs').traverse()

    def tree(self) -> list['Kind']:
        """This Kind and its descendants, depth first."""
        return GraphTraversal(self, traverse_mode='dfs', family_mode='children_only').traverse()

    def _outgoing(self) -> Iterator[tuple['Kind', str]]:
        """Child edges (how='') then forward relations, in a deterministic order."""
        for child in self.children:
            yield child, ""
        for how, related_kinds in self.relations.items():
            if not how.startswith(INVERSE_PREFIX):
                for related_kind in sorted(related_kinds, key=lambda k: k.name):
                    yield related_kind, how

    def to_mmd(self) -> str:
        """Mermaid flowchart of everything reachable through children and relations."""
        def node_id(kind: 'Kind') -> str:
            return kind.name.replace(" ", "_")

        edges, visited = [], {self}
        stack = [self._outgoing()]
        owners = [self]
        while stack:
            edge = next(stack[-1], None)
            if edge is None:
                stack.pop()
                owners.pop()
                continue
            target, how = edge
            arrow = "-->" if not how else f"-- {how} -->"
            edges.append(f"    {node_id(owners[-1])} {arrow} {node_id(target)}")
            if target not in visited:
                visited.add(target)
                stack.append(target._outgoing())
                owners.append(target)

        declarations = sorted({
            f"{node_id(kind)}{MERMAID_SHAPES.get(kind.node_shape, DEFAULT_SHAPE)[0]}{kind.name}"
            f"{MERMAID_SHAPES.get(kind.node_shape, DEFAULT_SHAPE)[1]}"
            for kind in visited})
        return "\n".join(["graph LR", *declarations, *dict.fromkeys(edges)])

    def to_ascii(self, traverse_mode: Literal["dfs", "bfs"] = "dfs",
                 family_mode: Literal["children_first", "parents_first"] = "children_first") -> str:
        """Indented text rendering of the graph, followed by its relations."""
        return GraphTraversal(self, traverse_mode=traverse_mode, family_mode=family_mode).to_ascii()

    # --- serialization -----------------------------------------------------

    def _component(self) -> list['Kind']:
        """Every Kind connected to this one by children, parents or relations (either direction)."""
        seen, queue = {self}, deque([self])
        while queue:
            kind = queue.popleft()
            neighbours = chain(kind.children, kind.parents,
                               *(related for _, related in kind.relations.items()))
            for neighbour in neighbours:
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return sorted(seen, key=lambda kind: kind.name)

    def _graph_dump(self) -> list[dict]:
        return [{
            "name": kind.name,
            "children": [child.name for child in kind.children],
            "relations": {how: sorted(related.name for related in related_kinds)
                          for how, related_kinds in kind.relations.items()
                          if not how.startswith(INVERSE_PREFIX)},
        } for kind in self._component()]

    @classmethod
    def _graph_load(cls, nodes: list[dict], source: str) -> 'Kind':
        """Builds (or merges into, by name) the Kinds described by `nodes`; returns a root.

        Names are interned: a node named like an existing Kind extends that Kind.
        """
        if not nodes:
            raise ValueError(f"No kinds found in the {source} input.")
        kinds = {node["name"]: cls(node["name"]) for node in nodes}
        for node in nodes:
            current = kinds[node["name"]]
            for child_name in node.get("children", []):
                if child_name in kinds:
                    current.append(kinds[child_name])
            for how, related_names in node.get("relations", {}).items():
                for related_name in related_names:
                    if related_name in kinds:
                        current.relate(kinds[related_name], how=how)
        return cls._pick_root(kinds.values())

    @staticmethod
    def _pick_root(kinds: Iterable['Kind']) -> 'Kind':
        """The first Kind (by name) that no other parsed Kind points to; else the first by name."""
        kinds = sorted(kinds, key=lambda kind: kind.name)
        targets = {target for kind in kinds for target, _ in kind._outgoing()}
        return next((kind for kind in kinds if kind not in targets), kinds[0])

    def to_json(self) -> str:
        return orjson.dumps(self._graph_dump(), option=orjson.OPT_INDENT_2).decode("utf-8")

    @classmethod
    def from_json(cls, json_string: str) -> 'Kind':
        return cls._graph_load(orjson.loads(json_string), "JSON")

    def to_yaml(self) -> str:
        return yaml.safe_dump(self._graph_dump(), sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_string: str) -> 'Kind':
        return cls._graph_load(yaml.safe_load(yaml_string) or [], "YAML")

    def to_toml(self) -> str:
        return tomli_w.dumps({"kinds": self._graph_dump()})  # TOML needs a key above a list of tables

    @classmethod
    def from_toml(cls, toml_string: str) -> 'Kind':
        return cls._graph_load(tomllib.loads(toml_string).get("kinds", []), "TOML")

    @classmethod
    def from_ascii(cls, ascii_string: str) -> 'Kind':
        """Rebuilds a graph from the output of to_ascii()."""
        kinds: dict[str, Kind] = {}
        parent_stack: list[tuple[int, Kind]] = []
        in_relations = False
        for line in ascii_string.strip().split('\n'):
            if line.strip() == "--- Relations ---":
                in_relations = True
                continue
            if in_relations:
                relation = re.match(r'^(.+) --(.+)--> (.+)$', line.strip())
                if relation:
                    source, how, target = relation.groups()
                    source_kind = kinds.setdefault(source, cls(source))
                    source_kind.relate(kinds.setdefault(target, cls(target)), how=how)
                continue
            node = re.match(r'^(\s*)- (.+)$', line)
            if not node:
                continue
            indent, name = len(node.group(1)), node.group(2)
            kind = kinds.setdefault(name, cls(name))
            while parent_stack and parent_stack[-1][0] >= indent:
                parent_stack.pop()
            if parent_stack:
                parent_stack[-1][1].append(kind)
            parent_stack.append((indent, kind))
        if not kinds:
            raise ValueError("No kinds found in the ASCII input.")
        return next((kind for kind in kinds.values() if not kind.parents), next(iter(kinds.values())))

    # --- relations ---------------------------------------------------------

    def patch(self, other: 'Kind') -> 'Kind':
        """Merges another Kind's origin (if unset), children, parents and relations into this one."""
        self._ensure_mutable()
        if other.origin is not None and self.origin is None:
            self.origin = other.origin
        for child in list(other.children):
            self.append(child)
        for parent in list(other.parents):
            parent.append(self)
        for how, related_kinds in list(other.relations.items()):
            if not how.startswith(INVERSE_PREFIX):
                for related_kind in list(related_kinds):
                    self.relate(related_kind, how=how)
        return self

    def relate(self, other: 'Kind', how: str = 'related') -> 'Kind':
        """Relates this Kind to `other` under `how`, recording the inverse on `other`."""
        with self._lock:
            self._ensure_mutable()
            other._ensure_mutable()
            self.relations.add(how, other)
            other.relations.add(f"{INVERSE_PREFIX}{how}", self)
        return self

    def unrelate(self, other: 'Kind', how: Optional[str] = None) -> 'Kind':
        """Removes the relation(s) to `other`: one `how`, or all of them."""
        with self._lock:
            hows = [how] if how is not None else [h for h, kinds in self.relations.items()
                                                  if other in kinds and not h.startswith(INVERSE_PREFIX)]
            for h in hows:
                self.relations.remove(h, other)
                other.relations.remove(f"{INVERSE_PREFIX}{h}", self)
        return self

    # --- the Kind.next() sequence and creation order -----------------------

    def head(self, up_to_position: float = 5.0) -> 'Kind':
        cur = self
        while cur._prev and cur._prev._position >= up_to_position:
            cur = cur._prev
        return cur

    def tail(self, from_position: float = -10.0) -> 'Kind':
        cur = self
        while cur._next and cur._next._position <= from_position:
            cur = cur._next
        return cur

    @classmethod
    def auto_date(cls) -> 'Kind':
        return cls(datetime.date.today().isoformat())

    @classmethod
    def auto_datetime(cls) -> 'Kind':
        return cls(datetime.datetime.now().isoformat())

    @classmethod
    def auto_time(cls) -> 'Kind':
        return cls(datetime.datetime.now().time().isoformat())

    @classmethod
    def next(cls) -> 'Kind':
        """Creates kind_<n> and chains it after the previous Kind.next() result."""
        with cls._lock:
            previous = BaseKind._pool.get(f"kind_{BaseKind._auto_counter - 1}")
            kind = cls(f"kind_{BaseKind._auto_counter}")
            BaseKind._auto_counter += 1
            if previous is not None:
                object.__setattr__(previous, '_next', kind)
                object.__setattr__(kind, '_prev', previous)
        return kind

    @classmethod
    def first(cls) -> Optional['Kind']:
        """The earliest created live Kind."""
        node = cls._numbered.min_node()
        return node.kind if node else None

    @classmethod
    def last(cls) -> Optional['Kind']:
        """The most recently created live Kind."""
        node = cls._numbered.max_node()
        return node.kind if node else None

    @classmethod
    def len(cls) -> int:
        """The number of live Kinds."""
        return cls._numbered.size()

    @classmethod
    def seek(cls, pos: float) -> Optional['Kind']:
        """The live Kind created at position `pos`, or None."""
        return cls._numbered.search(pos)

    @classmethod
    def each(cls, start: Union[float, 'Kind', None] = None) -> Iterator['Kind']:
        """Live Kinds in creation order, optionally from a position or a Kind on."""
        if start is not None and not isinstance(start, (int, float, Kind)):
            raise TypeError(f"Invalid start parameter {start!r} of type {type(start).__name__} in each()")
        start_weight = start._position if isinstance(start, Kind) else start
        yield from cls._numbered.traverse_inorder(start_weight)

    # --- conversion --------------------------------------------------------

    @classmethod
    def from_object(cls, obj: Any) -> 'Kind':
        """Converts a value to a Kind.

        Scalars become the Kind of their text (`123` -> Kind('123')). A container becomes
        the Kind of its content (`[1, 2]` -> Kind('[1, 2]')) with its items as children and
        a `has_kind` relation to the container's kind (Kind('list')). Equal content means
        the same Kind, as for any name.
        """
        if isinstance(obj, Kind):
            return obj
        if isinstance(obj, LazyKind):
            return obj.evaluate()
        if isinstance(obj, (list, tuple, set, frozenset, dict)):
            return cls._from_container(obj)
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return cls(obj if isinstance(obj, str) else str(obj), origin=obj)
        try:
            return cls(orjson.dumps(obj).decode(), origin=obj)
        except (TypeError, orjson.JSONEncodeError) as error:
            raise TypeError(f"Cannot convert {type(obj).__name__} to Kind: {error}. "
                            f"Hint: give the object a JSON-serializable form, or pass its name.") from None

    @classmethod
    def _from_container(cls, value: Union[list, tuple, set, frozenset, dict]) -> 'Kind':
        if isinstance(value, (set, frozenset)):
            items = sorted(value, key=repr)
            name = f"{type(value).__name__}({{{', '.join(map(repr, items))}}})" if items else f"{type(value).__name__}()"
        else:
            items = value
            name = repr(value)
        kind = cls(name, origin=value)
        if isinstance(value, dict):
            for key, val in value.items():
                kind.append(key).append(val)
        else:
            for item in items:
                kind.append(item)
        kind.relate(cls(type(value).__name__), how='has_kind')
        return kind

    def to(self, target_type: Type[T]) -> T:
        """Converts the Kind's name back to a value of `target_type`."""
        if target_type is str:
            return self.name
        try:
            value = orjson.loads(self.name)
        except orjson.JSONDecodeError:
            raise TypeError(f"Cannot convert Kind '{self.name}' to {target_type.__name__}") from None
        return value if isinstance(value, target_type) else target_type(value)

    def each_parents(self) -> Iterator['Kind']:
        return iter(self.parents)

    def each_children(self) -> Iterator['Kind']:
        return iter(self.children)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    # --- maturing: elevate, slim, immute -----------------------------------

    def elevate(self, merge_strategy: MergeStrategy = 'smooth') -> Set[str]:
        """Moves metadata entries onto the Kind as attributes; returns the keys moved.

        A key naming a Kind method or property cannot be elevated (the class attribute
        would hide it) and stays in metadata with a warning.
        """
        self._ensure_mutable()
        elevated = set()
        for key, value in list(self.metadata.items()):
            class_attribute = getattr(type(self), key, None)
            if key in STRUCTURAL_SLOTS or key.startswith('_'):
                warnings.warn(f"Cannot elevate '{key}' on Kind {self.name!r}: it is part of its identity or structure.")
                continue
            if class_attribute is not None and not _is_settable(class_attribute):
                warnings.warn(f"Cannot elevate '{key}' on Kind {self.name!r}: it is a Kind method or read-only property.")
                continue
            if class_attribute is not None:
                current = getattr(self, key)
            else:
                current = self._elevated_attributes.get(key)
            merged = value if current is None else _apply_merge_strategy(current, value, merge_strategy)
            setattr(self, key, merged)
            del self.metadata[key]
            elevated.add(key)
        return elevated

    def slim(self, protected_attributes: Optional[Set[str]] = None) -> None:
        """Drops elevated attributes that hold no value (SENTINEL) unless protected."""
        self._ensure_mutable()
        protected = protected_attributes or set()
        for name in [name for name, value in self._elevated_attributes.items()
                     if value is SENTINEL and name not in protected]:
            del self._elevated_attributes[name]

    def immute(self, merge_strategy: MergeStrategy = 'smooth') -> 'Kind':
        """Matures this Kind: elevate metadata, slim, then freeze it."""
        if self._frozen:
            return self
        self.slim(protected_attributes=self.elevate(merge_strategy=merge_strategy))
        return self.freeze()

    def clear_context(self) -> None:
        """Empties the context."""
        self._ensure_mutable()
        if self._context is not SENTINEL:
            self._context.clear()

    # --- introspection -----------------------------------------------------

    @classmethod
    def ps(cls) -> None:
        """Prints all live Kinds with their footprint and origin."""
        rows = ["{:<30} {:<15} {:<50}".format("Name", "Footprint (b)", "Origin"), "-" * 95]
        total = 0
        for name, kind in sorted(BaseKind._pool.items()):
            footprint = kind.footprint() if isinstance(kind, Kind) else getsizeof(kind)
            total += footprint
            origin = kind.origin if kind.origin is not None else f"{type(kind).__module__}.{type(kind).__name__}"
            rows.append("{:<30} {:<15} {:<50}".format(name, footprint, str(origin)))
        rows += ["-" * 95, "{:<30} {:<15}".format("Total", total)]
        print("\n".join(rows))

    @classmethod
    def ls(cls) -> None:
        """Prints the available mixin classes."""
        print("Available Mixins:")
        for name in sorted(_get_available_mixins()):
            print(f"- {name}")

    def stat(self) -> None:
        """Prints this Kind's footprint and what each available mixin would add to it."""
        rows = [f"Statistics for Kind: '{self.name}'", "\n--- Mixin Analysis ---",
                "{:<30} {:<15}".format("Mixin Name", "Footprint (b)"), "-" * 46]
        for name, mixin_cls in sorted(_get_available_mixins().items()):
            probe = Kind(f"_stat_probe_{name}")
            try:
                apply_mixin_to_instance(probe, mixin_cls)
                rows.append("{:<30} {:<15}".format(name, probe.footprint()))
            except Exception as error:  # a mixin class that cannot be instantiated bare
                rows.append("{:<30} {:<15}".format(name, f"n/a ({type(error).__name__})"))
            finally:
                probe.delete()
        rows += ["-" * 46, "\n--- Kind Footprint ---", f"Current Footprint: {self.footprint()} bytes"]
        print("\n".join(rows))

    def footprint(self) -> int:
        """Bytes used by this Kind and its descendants (each object counted once)."""
        shared = (None, True, False, SENTINEL)
        memo, total, stack = set(), 0, [self]
        while stack:
            obj = stack.pop()
            if id(obj) in memo or any(obj is s for s in shared):
                continue
            memo.add(id(obj))
            total += getsizeof(obj)
            if isinstance(obj, Kind):
                total += getsizeof(obj.parents._items) + getsizeof(obj.children._items)
                stack += [obj.name, obj.origin, obj.node_shape, obj._index, obj._metadata,
                          obj._context, obj._elevated_attributes]
                stack.extend(obj.children)
            elif isinstance(obj, dict):
                stack.extend(obj.keys())
                stack.extend(obj.values())
            elif isinstance(obj, (list, tuple, set, frozenset)):
                stack.extend(obj)
            elif hasattr(obj, '__dict__') and not inspect.isroutine(obj) and not inspect.isclass(obj):
                stack.append(vars(obj))
        return total


def to_kind(obj: Any) -> Kind:
    """Converts an object to a Kind."""
    return Kind.from_object(obj)
