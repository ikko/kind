"""This module provides pathfinding capabilities for Kind objects.

It includes a mixin that adds methods for finding paths between Kinds
and for matching Kinds based on a predicate.
"""
from __future__ import annotations
from typing import Callable, Iterator, List

from core.protocols import KindPathProtocol

class KindPathMixin(KindPathProtocol):
    def path_to(self, target: 'Kind') -> list['Kind']:
        visited = set()
        path = []

        def dfs(node: 'Kind') -> bool:
            if node in visited:
                return False
            visited.add(node)
            path.append(node)
            if node == target:
                return True
            for child in node.children:
                if dfs(child):
                    return True
            path.pop()
            return False

        if dfs(self):
            return path
        return []

    def match(self, predicate: Callable[['Kind'], bool], traversal: str = 'dfs') -> Iterator['Kind']:
        visited = set()

        def dfs(node: 'Kind'):
            if node in visited:
                return
            visited.add(node)
            if predicate(node):
                yield node
            for child in node.children:
                yield from dfs(child)

        def bfs(start: 'Kind'):
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                if predicate(node):
                    yield node
                queue.extend(node.children)

        if traversal == 'bfs':
            yield from bfs(self)
        else:
            yield from dfs(self)

# Attach at runtime:
# Kind.path_to = KindPathMixin.path_to
# Kind.match = KindPathMixin.match
