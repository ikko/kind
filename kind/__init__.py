"""kind: interned, name-identified Kinds that form a graph of categories as data."""
from kind import builtin, core
from kind.builtin import apply_builtins
from kind.core.base_kind import KindLimitError
from kind.core.space import KindSpace, SpaceError, current_space
from kind.core.graph_traversal import GraphTraversal
from kind.core.kind import FrozenKindError, Kind
from kind.core.kind_namespace import k

__all__ = ["Kind", "k", "FrozenKindError", "KindLimitError", "KindSpace", "SpaceError", "current_space", "GraphTraversal",
           "builtin", "core"]

apply_builtins()

_ALIASES = {
    "time": "kind.time",  # opt-in: the first access enables the time mixins
    "time_dim": "kind.time.dim", "td": "kind.time.dim",
    "timeline": "kind.time.timeline", "tl": "kind.time.timeline",
    "collections": "kind.builtin.collections", "coll": "kind.builtin.collections",
    "index": "kind.builtin.index", "idx": "kind.builtin.index",
    "path": "kind.builtin.path",
    "visual": "kind.builtin.visual", "vis": "kind.builtin.visual",
}


def __getattr__(name: str):
    """Module aliases (kind.td, kind.vis, ...), imported on first access."""
    if name in _ALIASES:
        import importlib
        if _ALIASES[name].startswith("kind.time"):
            importlib.import_module("kind.time")  # an alias into kind.time opts in to time, as `import kind.time` does
        return importlib.import_module(_ALIASES[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted([*globals(), *_ALIASES])
