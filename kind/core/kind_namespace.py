"""This module provides `k`: attribute and item access that returns interned Kinds.

`k.Stock` and `k['Stock']` both return `Kind('Stock')`. The namespace has no members
of its own, so every public name is free to become a Kind (`k.next` is `Kind('next')`).
Private names raise AttributeError, so introspection (hasattr, copy, pickle) does not
create Kinds as a side effect.
"""
from kind.core.kind import Kind


class KindNamespace:
    """Read-only factory of interned Kinds by attribute or item access."""
    __slots__ = ()

    def __getattr__(self, name: str) -> Kind:
        if name.startswith('_'):
            raise AttributeError(name)
        return Kind(name)

    def __getitem__(self, name: str) -> Kind:
        return Kind(name)

    def __setitem__(self, name, value):
        raise TypeError(f"KindNamespace is read-only, cannot set {name} to {value}")

    def __setattr__(self, name, value):
        raise TypeError(f"KindNamespace is read-only, cannot set {name} to {value}")


k = KindNamespace()
