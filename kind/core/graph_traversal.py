"""This module provides GraphTraversal: iterative DFS/BFS over a Kind graph.

Neighbours of a Kind are visited group by group — children and parents in the order
family_mode names (parents are skipped for "children_only"), then forward relations —
and by name within each group. Each Kind's edges are read from a snapshot taken under
its space's lock.
"""
from collections import deque
from typing import Literal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind

TraverseMode = Literal["dfs", "bfs"]
FamilyMode = Literal["children_first", "parents_first", "children_only"]
INVERSE_PREFIX = "_inverse_"


class GraphTraversal:
    def __init__(self, root: 'Kind', traverse_mode: TraverseMode = "dfs", family_mode: FamilyMode = "children_first"):
        if traverse_mode not in ("dfs", "bfs"):
            raise ValueError(f"Unknown traverse_mode: {traverse_mode!r} (expected 'dfs' or 'bfs')")
        if family_mode not in ("children_first", "parents_first", "children_only"):
            raise ValueError(f"Unknown family_mode: {family_mode!r} "
                             f"(expected 'children_first', 'parents_first' or 'children_only')")
        self.root = root
        self.traverse_mode = traverse_mode
        self.family_mode = family_mode

    def _neighbours(self, kind: 'Kind', include_relations: bool) -> list:
        by_name = lambda kinds: sorted(kinds, key=lambda neighbour: neighbour.name)
        children, parents, relations = kind._snapshot()
        children = by_name(children)
        parents = [] if self.family_mode == "children_only" else by_name(p for p in parents if p != self.root)
        family = [*parents, *children] if self.family_mode == "parents_first" else [*children, *parents]
        related = by_name(r for how, rs in relations if not how.startswith(INVERSE_PREFIX) for r in rs)
        return family + related if include_relations else family

    def _walk(self, include_relations: bool):
        """Yields (kind, depth) once per reachable Kind, in traversal order."""
        frontier = deque([(self.root, 0)])
        take = frontier.pop if self.traverse_mode == "dfs" else frontier.popleft
        visited = set()
        while frontier:
            kind, depth = take()
            if kind in visited:
                continue
            visited.add(kind)
            yield kind, depth
            neighbours = [(n, depth + 1) for n in self._neighbours(kind, include_relations) if n not in visited]
            frontier.extend(reversed(neighbours) if self.traverse_mode == "dfs" else neighbours)

    def traverse(self) -> list['Kind']:
        return [kind for kind, _ in self._walk(include_relations=self.family_mode != "children_only")]

    def traverse_family(self) -> list['Kind']:
        """Kinds reachable over children and parents only: the part to_ascii() draws as an outline."""
        return [kind for kind, _ in self._walk(include_relations=False)]

    def _family_edges(self, kind: 'Kind') -> list:
        """(neighbour, marker) for every family edge of `kind`: '-' for a child, '^' for a parent."""
        by_name = lambda kinds: sorted(kinds, key=lambda neighbour: neighbour.name)
        children, parents, _ = kind._snapshot()
        child_edges = [(child, "-") for child in by_name(children)]
        parent_edges = [] if self.family_mode == "children_only" else [(parent, "^") for parent in by_name(parents)]
        return parent_edges + child_edges if self.family_mode == "parents_first" else child_edges + parent_edges

    def to_ascii(self) -> str:
        """One line per family edge, each printed once: `- name` is a child of the line above it,
        `^ name` a parent. A Kind is expanded where it first appears; later appearances only
        record the edge. Relations follow in a separate section.

        Depth-first output (the default) is an outline, and `Kind.from_ascii` reads it back
        exactly. Breadth-first output interleaves branches, so it is for display only.
        """
        lines: list[str] = []
        relations: set[tuple[str, str, str]] = set()
        frontier = deque([(self.root, 0, "-")])
        take = frontier.pop if self.traverse_mode == "dfs" else frontier.popleft
        expanded, printed_edges = set(), set()
        while frontier:
            kind, depth, marker = take()
            lines.append(f"{'  ' * depth}{marker} {kind.name}")
            if kind in expanded:
                continue
            expanded.add(kind)
            for how, related_kinds in kind._snapshot()[2]:
                if not how.startswith(INVERSE_PREFIX):
                    relations.update((kind.name, how, related.name) for related in related_kinds)
            pending = []
            for neighbour, edge_marker in self._family_edges(kind):
                edge = (kind, neighbour) if edge_marker == "-" else (neighbour, kind)
                if edge not in printed_edges:
                    printed_edges.add(edge)
                    pending.append((neighbour, depth + 1, edge_marker))
            frontier.extend(reversed(pending) if self.traverse_mode == "dfs" else pending)
        if relations:
            lines += ["", "--- Relations ---"]
            lines += [f"{source} --{how}--> {target}" for source, how, target in sorted(relations)]
        return "\n".join(lines)
