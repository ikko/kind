"""This module provides pathfinding capabilities for Kind objects.

It includes a mixin that adds methods for finding paths between Kinds
and for matching Kinds based on a predicate.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterator

from kind.core.protocols import KindPathProtocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind

class KindPathMixin(KindPathProtocol):
    def path_to(self, target: 'Kind') -> list['Kind']:
        """A path of children links from this Kind to `target` (depth first), or []."""
        came_from = {self: None}
        stack = [self]
        while stack:
            node = stack.pop()
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                return path[::-1]
            for child in reversed(list(node.children)):
                if child not in came_from:
                    came_from[child] = node
                    stack.append(child)
        return []

    def match(self, predicate: Callable[['Kind'], bool], traversal: str = 'dfs') -> Iterator['Kind']:
        visited = set()

        frontier = deque([self])
        take = frontier.popleft if traversal == 'bfs' else frontier.pop
        while frontier:
            node = take()
            if node in visited:
                continue
            visited.add(node)
            if predicate(node):
                yield node
            children = list(node.children)
            frontier.extend(children if traversal == 'bfs' else reversed(children))
