"""This module provides an implementation of an AVL tree.

An AVL tree is a self-balancing binary search tree that maintains a balanced height,
ensuring O(log n) search, insertion and deletion.

"""
from __future__ import annotations

from typing import Any, Callable, Iterator, Optional, Union


Weight = Union[float, Callable[[Any], float]]


class AVLNode:
    __slots__ = ('_kind', 'weight', 'height', 'left', 'right')

    def __init__(self, kind: Any, weight: Weight):
        self._kind: Any = kind
        self.weight = weight
        self.height = 1
        self.left: Optional[AVLNode] = None
        self.right: Optional[AVLNode] = None

    @property
    def kind(self) -> Any:
        return self._kind

    def eval_weight(self) -> float:
        return self.weight(self.kind) if callable(self.weight) else self.weight


class AVLTree:
    def __init__(self):
        self.root: Optional[AVLNode] = None

    # --- balancing -------------------------------------------------------

    @staticmethod
    def _height(node: Optional[AVLNode]) -> int:
        return node.height if node else 0

    def _update_height(self, node: AVLNode) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        return self._height(node.left) - self._height(node.right) if node else 0

    def _rotate_left(self, z: AVLNode) -> AVLNode:
        y = z.right
        assert y is not None  # only called when the right subtree is the taller one
        z.right, y.left = y.left, z
        self._update_height(z)
        self._update_height(y)
        return y

    def _rotate_right(self, z: AVLNode) -> AVLNode:
        y = z.left
        assert y is not None  # only called when the left subtree is the taller one
        z.left, y.right = y.right, z
        self._update_height(z)
        self._update_height(y)
        return y

    def _rebalance(self, node: AVLNode) -> AVLNode:
        self._update_height(node)
        balance = self._balance_factor(node)
        if balance > 1:
            assert node.left is not None
            if self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1:
            assert node.right is not None
            if self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    # --- writes ----------------------------------------------------------

    def insert(self, node: Optional[AVLNode], kind: Any, weight: Weight) -> AVLNode:
        """Inserts `kind` under `node` and returns the new subtree root.

        Kept in this shape for KindIndex; prefer `add`, which also maintains `root`.
        """
        if not node:
            return AVLNode(kind, weight)
        value = weight(kind) if callable(weight) else weight
        if value < node.eval_weight():
            node.left = self.insert(node.left, kind, weight)
        else:
            node.right = self.insert(node.right, kind, weight)
        return self._rebalance(node)

    def add(self, kind: Any, weight: Weight) -> None:
        self.root = self.insert(self.root, kind, weight)

    def remove(self, weight: float, kind: Optional[Any] = None) -> Optional[AVLNode]:
        """Removes the node with `weight`; with `kind`, only the node holding that Kind."""
        self.root = self._remove(self.root, weight, kind)
        return self.root

    def _remove(self, node: Optional[AVLNode], weight: float, kind: Optional[Any], _node: Optional[AVLNode] = None) -> Optional[AVLNode]:
        if not node:
            return None
        node_weight = node.eval_weight()
        matches = node is _node if _node is not None else (
            node_weight == weight and (kind is None or node.kind is kind))
        if not matches and weight < node_weight:
            node.left = self._remove(node.left, weight, kind, _node)
        elif not matches:
            # equal weights may sit on either side after rotations, so search both
            node.right = self._remove(node.right, weight, kind, _node)
            if node_weight == weight:
                node.left = self._remove(node.left, weight, kind, _node)
        else:
            if not node.left:
                return node.right
            if not node.right:
                return node.left
            successor = self._min_value_node(node.right)
            node._kind, node.weight = successor._kind, successor.weight
            node.right = self._remove(node.right, successor.eval_weight(), None, successor)
        return self._rebalance(node)

    # --- reads -----------------------------------------------------------

    @staticmethod
    def _min_value_node(node: AVLNode) -> AVLNode:
        while node.left:
            node = node.left
        return node

    def _nodes_inorder(self, reverse: bool = False) -> Iterator[AVLNode]:
        stack: list[AVLNode] = []
        node = self.root
        first, second = ('right', 'left') if reverse else ('left', 'right')
        while stack or node:
            while node:
                stack.append(node)
                node = getattr(node, first)
            node = stack.pop()
            yield node
            node = getattr(node, second)

    def min_node(self) -> Optional[AVLNode]:
        return next(self._nodes_inorder(), None)

    def max_node(self) -> Optional[AVLNode]:
        return next(self._nodes_inorder(reverse=True), None)

    def search(self, weight: float) -> Optional[Any]:
        """Returns the Kind stored with `weight`, or None."""
        node = self.root
        while node:
            node_weight = node.eval_weight()
            if weight == node_weight:
                return node.kind
            node = node.left if weight < node_weight else node.right
        return None

    def traverse_inorder(self, start_weight: Optional[float] = None) -> list[Any]:
        return [node.kind for node in self._nodes_inorder()
                if start_weight is None or node.eval_weight() >= start_weight]

    def size(self) -> int:
        return sum(1 for _ in self._nodes_inorder())

    def __len__(self) -> int:
        return self.size()

    def __iter__(self) -> Iterator[Any]:
        return (node.kind for node in self._nodes_inorder())

    def to_ascii(self) -> str:
        lines = []

        def _walk_ascii(node: Optional[AVLNode], indent: str = ""):
            if node is None:
                return
            _walk_ascii(node.right, indent + "  ")
            lines.append(f"{indent}- {node.kind.name} (W:{node.eval_weight():.2f}, H:{node.height})")
            _walk_ascii(node.left, indent + "  ")

        _walk_ascii(self.root)
        return "\n".join(lines)
