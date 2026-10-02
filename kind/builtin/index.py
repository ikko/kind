"""This module provides index capabilities for Kind objects.

Each Kind can own an index: other Kinds kept sorted by a weight (a number, or a
function of the Kind), stored in a self-balancing AVL tree.
"""
from typing import Any, Callable, Literal, Union

from kind.builtin.avl_tree import AVLTree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind


class KindIndex:
    def __init__(self, owner: 'Kind'):
        self.owner = owner
        self.tree = AVLTree()
        self._weights: dict = {}  # kind -> the weight it was inserted with

    def insert(self, kind: 'Kind', weight: Union[float, Callable]):
        with self.owner._lock:
            self.owner._ensure_mutable()
            if kind in self._weights:
                self.remove(kind)
            self._weights[kind] = weight
            self.tree.add(kind, weight)

    def map(self, fn: Callable[['Kind'], Any]) -> list[Any]:
        return [fn(kind) for kind in self.traverse(order="in")]

    def filter(self, pred: Callable[['Kind'], bool]) -> list['Kind']:
        return [kind for kind in self.traverse(order="in") if pred(kind)]

    def traverse(self, order: Literal["in", "pre", "post"] = "in") -> list['Kind']:
        if order == "in":
            return self.tree.traverse_inorder()
        # Pre-order and Post-order traversals are not directly supported by AVLTree
        # For now, return in-order for other requests or raise an error
        raise NotImplementedError(f"Traversal order '{order}' not implemented for KindIndex.")

    def remove(self, kind: 'Kind') -> None:
        with self.owner._lock:
            self.owner._ensure_mutable()
            weight = self._weights.pop(kind, None)
            if weight is not None:
                self.tree.remove(weight(kind) if callable(weight) else weight, kind)

    def ascii(self):
        return self.tree.to_ascii()

    def to_ascii(self) -> str:
        return self.ascii()
