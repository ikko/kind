# [`«kind»`](https://github.com/ikko/kind) cookbook
**Recipes for Symbolic Mastery**

_Recipe 1: How to Create a Mixin?_

---

# 1.3 Implementing Your First Mixin: A Practical Example

Let's walk through a practical example of creating a simple mixin for the `kind` framework. This mixin will add a new capability to `Kind` objects: the ability to count the total number of descendants (children, grandchildren, etc.) in their respective sub-graphs.

## Step 1: Define the Mixin Class

Create a new Python file (e.g., `my_counter_mixin.py`) and define your mixin class. Remember to import `Kind` and any other necessary modules.

<!-- doc-example: module my_counter_mixin -->
```python
# my_counter_mixin.py

from kind.core.kind import Kind
from typing import Set

class DescendantCounterMixin:
    def count_descendants(self: Kind) -> int:
        """Counts the total number of unique descendants for this kind."""
        seen_kinds: Set[Kind] = set()
        queue = list(self.children)

        while queue:
            current_kind = queue.pop(0)
            if current_kind not in seen_kinds:
                seen_kinds.add(current_kind)
                for child in current_kind.children:
                    queue.append(child)
        return len(seen_kinds)

    async def a_count_descendants(self: Kind) -> int:
        """Asynchronously counts the total number of unique descendants for this kind."""
        # For simplicity, this async version just calls the sync version
        # In a real-world scenario, this might involve async I/O or CPU-bound tasks
        # that are offloaded to a thread pool using anyio.to_thread.run_sync
        return self.count_descendants()

```

**Explanation:**

*   The `DescendantCounterMixin` class has no `__init__`: once registered, its methods live on the `Kind` class, so `self` is the `Kind` being extended.
*   `count_descendants` is a synchronous method that performs a breadth-first search to find all unique descendants.
*   `a_count_descendants` is the asynchronous counterpart. For this simple example, it just calls the synchronous version. In a more complex scenario, you might use `anyio.to_thread.run_sync` to offload heavy computation to a thread pool, or perform actual asynchronous operations.

## Step 2: Apply the Mixin to a Kind

To use your mixin, register it with `register_mixin`, which attaches its public methods to every `Kind` (to extend a single `Kind` only, use `apply_mixin_to_instance(kind, mixin)`; both live in `kind.core.mixinability`):

```python
# main.py (or a test file)

from kind.core.kind import Kind
from kind.core.mixinability import register_mixin
from my_counter_mixin import DescendantCounterMixin

# Register the mixin: count_descendants and a_count_descendants appear on every Kind
register_mixin(DescendantCounterMixin)

# Create some kinds to form a graph
a = Kind("A")
b = Kind("B")
c = Kind("C")
d = Kind("D")
e = Kind("E")

a.append(b)
a.append(c)
b.append(d)
c.append(e)
c.append(d)  # D is also a descendant of C

# Now you can call the mixin methods on the Kind itself
print(f"Kind A has {a.count_descendants()} descendants.")


# For asynchronous methods, use await
async def main():
    print(f"Kind A has {await a.a_count_descendants()} descendants (async).")


if __name__ == "__main__":
    import anyio

    anyio.run(main)
```

**Expected Output:**

```
Kind A has 4 descendants.
Kind A has 4 descendants (async).
```

**Explanation:**

*   We create a sample `Kind` graph.
*   `register_mixin(DescendantCounterMixin)` attaches the mixin's public methods to the `Kind` class. It refuses names that already belong to the `Kind` API (unless `safe=False`) and logs why.
*   We then call `count_descendants()` and `a_count_descendants()` directly on `a`.

This example demonstrates the basic process of defining a mixin and applying it to a `Kind` object. The next step will involve writing tests to ensure your mixin behaves as expected.
