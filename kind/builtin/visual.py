"""This module renders Kind graphs to Graphviz (DOT, SVG, PNG) and reads Mermaid back.

Mermaid and ASCII output belong to Kind itself (Kind.to_mmd, Kind.to_ascii); this
module adds Graphviz output and `from_mmd`, the inverse of Kind.to_mmd. The functions
take the Kind as their first argument, so they work both as mixins (`kind.to_dot()`)
and through the `KindRender(kind)` wrapper.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, Optional

import anyio
import anyio.to_thread

try:
    import graphviz
    _GRAPHVIZ_AVAILABLE = True
except ImportError:
    _GRAPHVIZ_AVAILABLE = False

if TYPE_CHECKING:
    from kind.core.kind import Kind

Mode = Literal["tree", "graph"]
_EDGE = re.compile(r'^(\S+)\s+(?:--\s+(.+?)\s+)?-->\s+(\S+)$')


def _dot_quote(name: str) -> str:
    """A DOT double-quoted ID: backslashes and quotes escaped, so a name cannot add attributes."""
    return '"' + name.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _require_graphviz() -> None:
    if not _GRAPHVIZ_AVAILABLE:
        raise ImportError("Graphviz is not installed. Hint: pip install 'kind[visual]' and install the "
                          "Graphviz 'dot' executable (e.g. apt install graphviz).")


def to_dot(self: 'Kind', mode: Mode = "tree") -> str:
    """DOT source of the Kind and its descendants; in "graph" mode relations are edges too."""
    _require_graphviz()
    lines, seen, stack = ["digraph G {"], {self}, [self]
    while stack:
        kind = stack.pop()
        targets = [(child, None) for child in kind.children]
        if mode == "graph":
            targets += [(related, how) for how, related_kinds in kind.relations.items()
                        if not how.startswith("_inverse_") for related in related_kinds]
        for target, how in targets:
            label = f' [label={_dot_quote(how)}]' if how else ""
            lines.append(f"{_dot_quote(kind.name)} -> {_dot_quote(target.name)}{label}")
            if target not in seen:
                seen.add(target)
                stack.append(target)
    lines.append("}")
    return "\n".join(lines)


async def a_to_svg(self: 'Kind', mode: Mode = "tree") -> str:
    dot = to_dot(self, mode)
    return await anyio.to_thread.run_sync(lambda: graphviz.Source(dot).pipe(format="svg").decode())


def to_svg(self: 'Kind', mode: Mode = "tree") -> str:
    return anyio.run(a_to_svg, self, mode)


async def a_to_png(self: 'Kind', mode: Mode = "tree") -> bytes:
    dot = to_dot(self, mode)
    return await anyio.to_thread.run_sync(lambda: graphviz.Source(dot).pipe(format="png"))


def to_png(self: 'Kind', mode: Mode = "tree") -> bytes:
    return anyio.run(a_to_png, self, mode)


def from_mmd(mmd_string: str) -> 'Kind':
    """Rebuilds the graph described by Kind.to_mmd() output; returns its root."""
    from kind.core.kind import DEFAULT_SHAPE, MERMAID_SHAPES, MMD_ESCAPES, Kind

    def unquote(label: str) -> str:
        if len(label) < 2 or not (label.startswith('"') and label.endswith('"')):
            return label
        label = label[1:-1]
        for raw, code in reversed(MMD_ESCAPES):
            label = label.replace(code, raw)
        return label

    lines = [line.strip() for line in mmd_string.strip().split('\n') if line.strip()]
    if not lines or lines[0] not in ("graph LR", "graph TD"):
        raise ValueError(f"Unsupported Mermaid header {lines[:1]}; expected 'graph LR' or 'graph TD'.")

    table: dict[Optional[str], tuple[str, str]] = {shape: pair for shape, pair in MERMAID_SHAPES.items()}
    table[None] = DEFAULT_SHAPE
    shapes = sorted(table.items(), key=lambda item: -len(item[1][0]))
    names: dict[str, str] = {}
    node_shapes: dict[str, str] = {}
    edges = []
    for line in lines[1:]:
        edge = _EDGE.match(line)
        if edge:
            edges.append(edge.groups())
            continue
        declared = re.match(r'^[^\[\(\{>]+', line)
        if declared is None:
            raise ValueError(f"Cannot read Mermaid line {line!r}: expected a node declaration or an edge.")
        node_id = declared.group(0)
        rest = line[len(node_id):]
        for shape, (opening, closing) in shapes:
            if rest.startswith(opening) and rest.endswith(closing):
                names[node_id] = unquote(rest[len(opening):len(rest) - len(closing)])
                if shape:
                    node_shapes[node_id] = shape
                break

    def kind_for(node_id: str) -> Kind:
        kind = Kind(names.get(node_id, node_id.replace('_', ' ')))
        if node_id in node_shapes and kind.node_shape is None:
            kind.node_shape = node_shapes[node_id]
        return kind

    kinds = {node_id: kind_for(node_id) for node_id in names}
    for source, how, target in edges:
        source_kind = kinds.setdefault(source, kind_for(source))
        target_kind = kinds.setdefault(target, kind_for(target))
        if how:
            source_kind.relate(target_kind, how=how)
        else:
            source_kind.append(target_kind)
    if not kinds:
        raise ValueError("No kinds found in the Mermaid string.")
    return Kind._pick_root(kinds.values())


class KindRender:
    """Wrapper exposing the Graphviz renderers for one Kind: KindRender(kind).to_svg()."""

    def __init__(self, root: 'Kind'):
        self.root = root

    def to_dot(self, mode: Mode = "tree") -> str:
        return to_dot(self.root, mode)

    async def a_to_svg(self, mode: Mode = "tree") -> str:
        return await a_to_svg(self.root, mode)

    def to_svg(self, mode: Mode = "tree") -> str:
        return to_svg(self.root, mode)

    async def a_to_png(self, mode: Mode = "tree") -> bytes:
        return await a_to_png(self.root, mode)

    def to_png(self, mode: Mode = "tree") -> bytes:
        return to_png(self.root, mode)

    from_mmd = staticmethod(from_mmd)


RENDERERS = (to_dot, a_to_svg, to_svg, a_to_png, to_png)
