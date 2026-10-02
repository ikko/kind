"""This module defines BaseKind: the interned, name-identified node every Kind is built on.

One name has one identity per space (see kind.core.space): all classes in the hierarchy
share the space's pool, so `BaseKind('A') is Kind('A')` holds whichever was created
first, as long as the first one is at least as specific as the one requested.

The pool holds its Kinds strongly, like a Lisp or Ruby symbol table: a name stays the
same entity, with its state, until `delete()` or `Kind.forget(name)` removes it, or its
space is closed. A weak pool would be invisible only for stateless values such as
interned strings; a Kind carries state, so collecting it would silently lose data.
`KindSpace(max_kinds=...)` caps a pool when names come from untrusted input.
"""
from typing import Any, Optional

from kind.core.space import KindSpace, SpaceError, current_space


class KindLimitError(RuntimeError):
    """Raised when creating a Kind would exceed its space's max_kinds."""


class BaseKind:
    __slots__ = (
        'name',
        'origin',
        'parents',
        'children',
        '_position',
        '_next',
        '_prev',
        '__weakref__',
        'node_shape',
        '_space',
    )

    name: str
    origin: Any
    parents: Any
    children: Any
    _position: float
    _next: Optional['BaseKind']
    _prev: Optional['BaseKind']
    node_shape: Optional[str]
    _space: KindSpace

    def __new__(cls, name: str, origin: Optional[Any] = None):
        if not isinstance(name, str):
            raise TypeError(f"{cls.__name__} name must be a string, got {type(name).__name__}. "
                            f"Hint: use Kind.from_object(value) to convert other values.")
        space = current_space()
        with space.lock:
            if space.closed:
                raise SpaceError(f"Cannot create {name!r}: {space!r} is closed. Hint: create it inside an open space.")
            existing = space.pool.get(name)
            if existing is not None:
                if not isinstance(existing, cls):
                    raise TypeError(
                        f"'{name}' already exists as {type(existing).__name__}, so it cannot also be a "
                        f"{cls.__name__}: one name has one identity. Hint: create it as {cls.__name__} "
                        f"first, or delete() the existing one.")
                if origin is not None and existing.origin is None:
                    object.__setattr__(existing, 'origin', origin)  # the first given origin wins
                return existing

            if space.max_kinds is not None and len(space.pool) >= space.max_kinds:
                raise KindLimitError(
                    f"Cannot create {name!r}: {space!r} already holds max_kinds={space.max_kinds} Kinds. "
                    f"Hint: delete() or Kind.forget() Kinds you no longer need, or raise the space's max_kinds.")
            obj = super().__new__(cls)
            obj._init_slots(name, origin, space)
            space.pool[name] = obj
            space.order.add(obj, obj._position)
            return obj

    def _init_slots(self, name: str, origin: Optional[Any], space: KindSpace) -> None:
        set_slot = object.__setattr__
        set_slot(self, '_space', space)
        set_slot(self, 'name', name)
        set_slot(self, 'origin', origin)
        set_slot(self, 'parents', [])
        set_slot(self, 'children', [])
        set_slot(self, '_position', space.next_position())
        set_slot(self, '_next', None)
        set_slot(self, '_prev', None)
        set_slot(self, 'node_shape', None)

    @property
    def space(self) -> KindSpace:
        """The space this Kind belongs to."""
        return self._space

    @property
    def _lock(self):
        return self._space.lock

    def __repr__(self):
        return f"{type(self).__name__}('{self.name}')"

    def __str__(self):
        return self.name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseKind):
            return NotImplemented  # lets LazyKind (or any wrapper) answer for itself
        return self.name == other.name and self._space is other._space  # same name, same universe

    def __hash__(self) -> int:
        return hash(self.name)

    def __lt__(self, other):
        """Kinds order by creation position."""
        if isinstance(other, BaseKind):
            return self._position < other._position
        return NotImplemented


def _to_kind(x: Any) -> 'BaseKind':
    """Converts an object to a BaseKind instance."""
    if isinstance(x, BaseKind):
        return x
    elif isinstance(x, str):
        return BaseKind(x)
    elif hasattr(x, 'name'):
        return BaseKind(x.name)
    raise TypeError(f"Cannot convert {repr(x)} instance of {type(x)} to BaseKind")
