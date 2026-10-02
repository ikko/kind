"""kind: interned, name-identified Kinds that form a graph of categories as data."""
from kind import builtin, core
from kind.builtin import apply_builtins
from kind.core.base_kind import KindLimitError
from kind.core.batch_processing import a_process_batch, process_batch
from kind.core.graph_traversal import GraphTraversal
from kind.core.kind import Kind
from kind.core.kind_namespace import k
from kind.core.time_arithmetics import add_time_objects, subtract_time_objects

__all__ = ["Kind", "k", "KindLimitError", "GraphTraversal", "a_process_batch", "process_batch",
           "add_time_objects", "subtract_time_objects", "add_time", "subtract_time", "builtin", "core"]

apply_builtins()

_ALIASES = {
    "time_dim": "kind.builtin.time_dim", "td": "kind.builtin.time_dim",
    "collections": "kind.builtin.collections", "coll": "kind.builtin.collections",
    "index": "kind.builtin.index", "idx": "kind.builtin.index",
    "path": "kind.builtin.path",
    "timeline": "kind.builtin.timeline", "tl": "kind.builtin.timeline",
    "visual": "kind.builtin.visual", "vis": "kind.builtin.visual",
    "schedule": "kind.core.schedule",
}
add_time = add_time_objects
subtract_time = subtract_time_objects


def __getattr__(name: str):
    """Module aliases (kind.td, kind.schedule, ...), imported on first access."""
    if name in _ALIASES:
        import importlib
        return importlib.import_module(_ALIASES[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted([*globals(), *_ALIASES])
