# [`«kind»`](https://github.com/ikko/kind) cookbook
**Recipes for Symbolic Mastery**

_Recipe 1: How to Create a Mixin?_

---

# 1.3 Implementing Your First Mixin: A Practical Example

Let's walk through a practical example of creating a simple mixin for the `kind` framework. This mixin will add a new capability to `Kind` objects: the ability to count the total number of descendants (children, grandchildren, etc.) in their respective sub-graphs.

## Step 1: Define the Mixin Class

Create a new Python file (e.g., `my_counter_mixin.py`) and define your mixin class. Remember to import `Kind` and any other necessary modules.

```python
# my_counter_mixin.py

from kind.core.base_kind import Kind
from typing import Set

class DescendantCounterMixin:
    def __init__(self, kind_instance: Kind):
        self.kind = kind_instance

    def count_descendants(self) -> int:
        """Counts the total number of unique descendants for this kind."""
        seen_kinds: Set[Kind] = set()
        queue = list(self.kind.children)

        while queue:
            current_kind = queue.pop(0)
            if current_kind not in seen_kinds:
                seen_kinds.add(current_kind)
                for child in current_kind.children:
                    queue.append(child)
        return len(seen_kinds)

    async def a_count_descendants(self) -> int:
        """Asynchronously counts the total number of unique descendants for this kind."""
        # For simplicity, this async version just calls the sync version
        # In a real-world scenario, this might involve async I/O or CPU-bound tasks
        # that are offloaded to a thread pool using anyio.to_thread.run_sync
        return self.count_descendants()

```

**Explanation:**

*   The `DescendantCounterMixin` class takes a `kind_instance` in its `__init__`, storing a reference to the `Kind` it's extending.
*   `count_descendants` is a synchronous method that performs a breadth-first search to find all unique descendants.
*   `a_count_descendants` is the asynchronous counterpart. For this simple example, it just calls the synchronous version. In a more complex scenario, you might use `anyio.to_thread.run_sync` to offload heavy computation to a thread pool, or perform actual asynchronous operations.

## Step 2: Apply the Mixin to a Kind

To use your mixin, you need to apply it to a `Kind` instance. The `kind` framework provides mechanisms for this, often through a dedicated `apply_mixin` function or by directly instantiating the mixin with the `Kind`.

For demonstration purposes, let's assume a direct application:

```python
# main.py (or a test file)

from kind.core.kind import Kind
from my_counter_mixin import DescendantCounterMixin

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

# Apply the mixin to Kind A
a_with_counter = DescendantCounterMixin(a)

# Now you can call the mixin methods through the mixin instance
print(f"Kind A has {a_with_counter.count_descendants()} descendants.")


# For asynchronous methods, use await
async def main():
    print(f"Kind A has {await a_with_counter.a_count_descendants()} descendants (async).")


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
*   An instance of `DescendantCounterMixin` is created, passing `Kind A` to its constructor.
*   We then call `count_descendants()` and `a_count_descendants()` on the `a_with_counter` instance. Note that the `Kind` framework typically integrates mixins such that their methods appear directly on the `Kind` object itself (e.g., `a.count_descendants()`). The direct instantiation shown here is for illustrative purposes of the mixin's structure.

This example demonstrates the basic process of defining a mixin and applying it to a `Kind` object. The next step will involve writing tests to ensure your mixin behaves as expected.
