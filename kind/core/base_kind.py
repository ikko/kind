"""This module defines the foundational Kind class and its core instantiation logic.

It serves as a base for the more extensive Kind functionality defined elsewhere,
specifically designed to prevent circular import dependencies.
"""
import threading
from typing import (Optional, Any, TypeVar)
from weakref import WeakValueDictionary

from kind.builtin.avl_tree import AVLTree


T = TypeVar("T")

class BaseKind:
    __slots__ = (
        'name',
        'origin',
        'parents',
        'children',
        'related_to',
        'related_how',
        '_position',
        '_next',
        '_prev',
        '_length_cache',
        '__weakref__',
        'node_shape',
    )

    _pool: WeakValueDictionary[str, 'BaseKind'] = WeakValueDictionary()
    _numbered: AVLTree = AVLTree()
    _auto_counter: int = 0
    _read_cursor: float = 0.0
    _write_cursor: float = 0.0
    _lock = threading.RLock()

    def __new__(cls, name: str, origin: Optional[Any] = None):
        with cls._lock:
            if not isinstance(name, str):
                raise TypeError("BaseKind name must be a string")
            
            # Only intern BaseKind instances if the requested class is exactly BaseKind.
            # Subclasses will handle their own pooling logic.
            if cls is BaseKind and name in BaseKind._pool:
                return BaseKind._pool[name]

            obj = super().__new__(cls)
            object.__setattr__(obj, 'name', name)
            object.__setattr__(obj, 'origin', origin)
            object.__setattr__(obj, 'parents', [])
            object.__setattr__(obj, 'children', [])
            
            object.__setattr__(obj, '_position', cls._write_cursor)
            object.__setattr__(obj, '_next', None)
            object.__setattr__(obj, '_prev', None)
            object.__setattr__(obj, '_length_cache', None)
            object.__setattr__(obj, 'node_shape', None) # Initialize node_shape
            cls._write_cursor += 1.0
            
            # Only add to BaseKind's pool if it's a BaseKind instance being created
            # Subclasses will manage their own pool entries.
            if cls is BaseKind:
                BaseKind._pool[name] = obj
                BaseKind._numbered.root = BaseKind._numbered.insert(BaseKind._numbered.root, obj, obj._position)
            
            return obj

    def __repr__(self):
        return f"BaseKind('{self.name}')"

    def __str__(self):
        return self.name

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, BaseKind) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    # Basic comparison for numbered kinds, more complex logic in kind.py
    def __lt__(self, other):
        # Check if both kinds are in the numbered tree by searching for their positions
        if isinstance(other, BaseKind) and \
           self._numbered.search(self._position) is not None and \
           other._numbered.search(other._position) is not None:
            return self._position < other._position
        raise TypeError("Unordered comparison not supported for non-numbered kinds")

    # Basic JSON serialization, more complex logic in kind.py
    def __orjson__(self):
        return self.name

def _to_kind(x: Any) -> 'BaseKind':
    """Converts an object to a BaseKind instance."""
    if isinstance(x, BaseKind):
        return x
    elif isinstance(x, str):
        return BaseKind(x)
    elif hasattr(x, 'name'):
        return BaseKind(x.name)
    raise TypeError(f"Cannot convert {repr(x)} instance of {type(x)} to BaseKind")


