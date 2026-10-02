"""This module provides OrderedKindSet: an insertion-ordered set of Kinds.

It backs every Kind's `children` and `parents`: membership is O(1), order and
indexing are kept, and adding a Kind that is already present does nothing.
Because Kinds are interned, "the same name" and "the same object" coincide.
"""
from typing import TYPE_CHECKING, Callable, Iterable, Iterator, Optional

if TYPE_CHECKING:
    from kind.core.kind import Kind


class OrderedKindSet:
    __slots__ = ('_items', '_members', '_guard')

    def __init__(self, items: Optional[Iterable['Kind']] = None, guard: Optional[Callable[[], None]] = None):
        """`guard` runs before every change; a Kind passes its own mutability check, so a frozen
        Kind's children, parents and relations cannot be changed even by direct calls."""
        self._items: list = []
        self._members: set = set()
        self._guard = None
        for item in items or ():
            self.add(item)
        self._guard = guard

    def _check(self) -> None:
        if self._guard is not None:
            self._guard()

    def add(self, kind: 'Kind') -> bool:
        """Adds `kind` at the end; returns False if it was already present."""
        self._check()
        if kind in self._members:
            return False
        self._members.add(kind)
        self._items.append(kind)
        return True

    append = add

    def insert(self, index: int, kind: 'Kind') -> None:
        """Places `kind` at `index`, moving it there if it is already present."""
        self._check()
        self.discard(kind)
        self._members.add(kind)
        self._items.insert(index, kind)

    def remove(self, kind: 'Kind') -> None:
        self._check()
        self._members.remove(kind)
        self._items.remove(kind)

    def discard(self, kind: 'Kind') -> None:
        if kind in self._members:
            self.remove(kind)

    def pop(self, index: int = -1) -> 'Kind':
        self._check()
        kind = self._items.pop(index)
        self._members.discard(kind)
        return kind

    def clear(self) -> None:
        self._check()
        self._items.clear()
        self._members.clear()

    def __contains__(self, kind) -> bool:
        return kind in self._members

    def __iter__(self) -> Iterator['Kind']:
        return iter(self._items)

    def __reversed__(self) -> Iterator['Kind']:
        return reversed(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __eq__(self, other) -> bool:
        if isinstance(other, OrderedKindSet):
            return self._items == other._items
        if isinstance(other, (list, tuple)):
            return self._items == list(other)
        return NotImplemented

    def __repr__(self) -> str:
        return f"OrderedKindSet({self._items!r})"
