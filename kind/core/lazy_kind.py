"""This module defines LazyKind, a deferred conversion to Kind, and the SENTINEL marker."""
from typing import Any, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind


class _Sentinel:
    """Marks a lazily created part that does not exist yet (distinct from a user-given None)."""
    def __repr__(self) -> str:
        return "<SENTINEL>"


SENTINEL = _Sentinel()


class LazyKind:
    """Wraps a value and converts it with Kind.from_object only when first used."""
    __slots__ = ('_obj', '_kind')

    def __init__(self, obj: Any):
        self._obj = obj
        self._kind: Optional['Kind'] = None

    @property
    def evaluated(self) -> bool:
        return self._kind is not None

    def evaluate(self) -> 'Kind':
        if self._kind is None:
            from kind.core.kind import Kind
            self._kind = Kind.from_object(self._obj)
        return self._kind

    def __getattr__(self, name: str) -> Any:
        return getattr(self.evaluate(), name)

    def __repr__(self) -> str:
        return repr(self._kind) if self.evaluated else f"LazyKind(unevaluated: {self._obj!r})"

    def __str__(self) -> str:
        return str(self._kind) if self.evaluated else f"LazyKind(unevaluated: {self._obj!s})"

    def __eq__(self, other: Any) -> bool:
        return self.evaluate() == other

    def __hash__(self) -> int:
        return hash(self.evaluate())
