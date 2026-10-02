"""This module provides custom collection classes for Kind objects.

It includes an OrderedKindSet, which is a set of Kinds that maintains insertion order.
"""
import threading


class OrderedKindSet:
    def __init__(self, items=None):
        self._dict = dict()
        self._lock = threading.RLock()
        self._length = 0
        if items:
            for item in items:
                self.add(item)

    def add(self, kind: 'Kind'):
        with self._lock:
            if kind.name not in self._dict:
                self._dict[kind.name] = kind
                self._length += 1
            else:
                self._dict[kind.name].patch(kind)

    def __iter__(self):
        return iter(self._dict.values())

    def __len__(self):
        return self._length

    def __contains__(self, kind):
        return kind.name in self._dict
