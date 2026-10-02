"""This module provides GraphTraversal: iterative DFS/BFS over a Kind graph.

Neighbours of a Kind are visited group by group — children and parents in the order
family_mode names (parents are skipped for "children_only"), then forward relations —
and by name within each group.
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
        children = by_name(kind.children)
        parents = [] if self.family_mode == "children_only" else by_name(p for p in kind.parents if p != self.root)
        family = [*parents, *children] if self.family_mode == "parents_first" else [*children, *parents]
        related = by_name(r for how, rs in kind.relations.items() if not how.startswith(INVERSE_PREFIX) for r in rs)
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

    def to_ascii(self) -> str:
        lines: list[str] = []
        relations: set[tuple[str, str, str]] = set()
        for kind, depth in self._walk(include_relations=False):
            lines.append(f"{'  ' * depth}- {kind.name}")
            for how, related_kinds in kind.relations.items():
                if not how.startswith(INVERSE_PREFIX):
                    relations.update((kind.name, how, related.name) for related in related_kinds)
        if relations:
            lines += ["", "--- Relations ---"]
            lines += [f"{source} --{how}--> {target}" for source, how, target in sorted(relations)]
        return "\n".join(lines)
