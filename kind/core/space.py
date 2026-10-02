"""This module defines KindSpace: one universe of names, with its own pool, order, lock and cap.

`Kind('Stock')` is looked up in the *current* space. A process starts with one default
space, so code that never mentions spaces behaves as a single symbol table. A new space
isolates a graph completely:

    with KindSpace() as space:      # a fresh universe, current inside the block
        Kind('Stock')               # unrelated to any 'Stock' outside
    # leaving the block closes the space: it drops its references to its Kinds (O(n));
    # the garbage collector reclaims them once nothing else refers to them

The current space is a context variable, so it is right for threads started with a
copied context and for asyncio/trio tasks (anyio's worker threads copy it too).
"""
import contextvars
import threading
from typing import Any, Iterator, Optional

from kind.builtin.avl_tree import AVLTree


class SpaceError(RuntimeError):
    """Raised for an edge across spaces, or a change to a Kind whose space is closed."""


class KindSpace:
    """A pool of interned Kinds with its own creation order, counters, lock and size cap."""

    def __init__(self, max_kinds: Optional[int] = None, name: str = "space"):
        self.name = name
        self.max_kinds = max_kinds  # None: unbounded; set it when names come from untrusted input
        self.pool: dict[str, Any] = {}
        self.order = AVLTree()  # every Kind in the pool, by creation position
        self.lock = threading.RLock()
        self.closed = False
        self._write_cursor = 0.0
        self._auto_counter = 0
        self._tokens: list[contextvars.Token] = []

    # --- lookup ---------------------------------------------------------------

    def get(self, name: str) -> Optional[Any]:
        return self.pool.get(name)

    def __contains__(self, name: object) -> bool:
        return name in self.pool

    def __len__(self) -> int:
        return len(self.pool)

    def __iter__(self) -> Iterator[Any]:
        """Kinds in creation order."""
        return iter(self.order)

    def next_position(self) -> float:
        position = self._write_cursor
        self._write_cursor += 1.0
        return position

    # --- lifetime -------------------------------------------------------------

    def __enter__(self) -> 'KindSpace':
        if self.closed:
            raise SpaceError(f"{self!r} is closed and cannot be entered again. Hint: open a new KindSpace().")
        self._tokens.append(_current.set(self))
        return self

    def __exit__(self, *exc_info) -> None:
        _current.reset(self._tokens.pop())
        self.close()

    def close(self) -> None:
        """Drops this space's references to its Kinds, O(n); Kinds referenced elsewhere become read-only."""
        if self is DEFAULT_SPACE:
            raise SpaceError("The default space cannot be closed; use Kind.forget() or a KindSpace of your own.")
        with self.lock:
            self.closed = True
            self.pool.clear()
            self.order = AVLTree()

    def __repr__(self) -> str:
        state = "closed" if self.closed else f"{len(self.pool)} kinds"
        return f"KindSpace({self.name!r}, {state})"


DEFAULT_SPACE = KindSpace(name="default")
_current: contextvars.ContextVar[KindSpace] = contextvars.ContextVar("kind_space", default=DEFAULT_SPACE)


def current_space() -> KindSpace:
    """The space `Kind(name)` looks names up in right now."""
    return _current.get()
