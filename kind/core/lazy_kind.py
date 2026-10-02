
from typing import Any

class LazyKind:
    __slots__ = ('_obj', '_kind')

    def __init__(self, obj: Any):
        self._obj = obj
        self._kind = None

    def __getattr__(self, name: str) -> Any:
        if self._kind is None:
            from .kind import Kind
            self._kind = Kind.from_object(self._obj)
        return getattr(self._kind, name)

    def __repr__(self) -> str:
        if self._kind is None:
            return f"LazyKind(unevaluated: {self._obj!r})"
        return repr(self._kind)

    def __str__(self) -> str:
        if self._kind is None:
            return f"LazyKind(unevaluated: {self._obj!s})"
        return str(self._kind)

    def __eq__(self, other: Any) -> bool:
        if self._kind is None:
            from .kind import Kind
            self._kind = Kind.from_object(self._obj)
        return self._kind == other

    def __hash__(self) -> int:
        if self._kind is None:
            from .kind import Kind
            self._kind = Kind.from_object(self._obj)
        return hash(self._kind)
