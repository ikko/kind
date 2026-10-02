"""This module defines BaseKind: the interned, name-identified node every Kind is built on.

One name has one identity in a process: all classes in the hierarchy share one pool,
so `BaseKind('A') is Kind('A')` holds whichever was created first, as long as the first
one is at least as specific as the one requested.

The pool holds its Kinds strongly, like a Lisp or Ruby symbol table: a name stays the
same entity, with its state, until `delete()` or `Kind.forget(name)` removes it. A weak
pool would be invisible only for stateless values such as interned strings; a Kind
carries state, so collecting it would silently lose data. `max_kinds` caps the pool
when names come from untrusted input.
"""
import threading
from typing import Any, Optional

from kind.builtin.avl_tree import AVLTree


class KindLimitError(RuntimeError):
    """Raised when creating a Kind would exceed BaseKind.max_kinds."""


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
    )

    _pool: dict = {}
    _numbered: AVLTree = AVLTree()  # every Kind in the pool, by creation position
    max_kinds: Optional[int] = None  # None: unbounded; set it when names come from untrusted input
    _auto_counter: int = 0
    _write_cursor: float = 0.0
    _lock = threading.RLock()

    def __new__(cls, name: str, origin: Optional[Any] = None):
        if not isinstance(name, str):
            raise TypeError(f"{cls.__name__} name must be a string, got {type(name).__name__}. "
                            f"Hint: use Kind.from_object(value) to convert other values.")
        with BaseKind._lock:
            existing = BaseKind._pool.get(name)
            if existing is not None:
                if not isinstance(existing, cls):
                    raise TypeError(
                        f"'{name}' already exists as {type(existing).__name__}, so it cannot also be a "
                        f"{cls.__name__}: one name has one identity. Hint: create it as {cls.__name__} "
                        f"first, or delete() the existing one.")
                if origin is not None and existing.origin is None:
                    object.__setattr__(existing, 'origin', origin)  # the first given origin wins
                return existing

            if cls.max_kinds is not None and len(BaseKind._pool) >= cls.max_kinds:
                raise KindLimitError(
                    f"Cannot create {name!r}: the pool already holds max_kinds={cls.max_kinds} Kinds. "
                    f"Hint: delete() or Kind.forget() Kinds you no longer need, or raise {cls.__name__}.max_kinds.")
            obj = super().__new__(cls)
            obj._init_slots(name, origin)
            BaseKind._pool[name] = obj
            BaseKind._numbered.add(obj, obj._position)
            return obj

    def _init_slots(self, name: str, origin: Optional[Any]) -> None:
        set_slot = object.__setattr__
        set_slot(self, 'name', name)
        set_slot(self, 'origin', origin)
        set_slot(self, 'parents', [])
        set_slot(self, 'children', [])
        set_slot(self, '_position', BaseKind._write_cursor)
        set_slot(self, '_next', None)
        set_slot(self, '_prev', None)
        set_slot(self, 'node_shape', None)
        BaseKind._write_cursor += 1.0

    def __repr__(self):
        return f"{type(self).__name__}('{self.name}')"

    def __str__(self):
        return self.name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseKind):
            return NotImplemented  # lets LazyKind (or any wrapper) answer for itself
        return self.name == other.name

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
