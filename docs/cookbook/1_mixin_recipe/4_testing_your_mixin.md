# [`«kind»`](https://github.com/ikko/kind) cookbook

**Recipes for Symbolic Mastery**

_Recipe 1: How to Create a Mixin?_

---

# 1.4 Testing Your Mixin: Ensuring Robustness

Thoroughly testing your mixins is crucial to ensure their correctness, reliability, and proper integration within the `kind` framework. This section outlines best practices for testing mixins, covering both synchronous and asynchronous functionalities.

## Principles of Mixin Testing

1.  **Isolation:** Test the mixin's logic in isolation as much as possible. While a mixin is designed to extend a `Kind`, its core functionality should be verifiable independently.
2.  **Integration:** Test how the mixin integrates with `Kind` objects and how its methods behave when called through a `Kind` instance.
3.  **Edge Cases:** Cover edge cases, such as empty graphs, kinds with no children, or complex graph structures.
4.  **Asynchronous Behavior:** For asynchronous methods, use `anyio`'s testing utilities (e.g., `@pytest.mark.anyio`) to properly manage the asynchronous execution context.

## Example: Testing the `DescendantCounterMixin`

Let's create a test file (e.g., `tests/test_descendant_counter_mixin.py`) for the `DescendantCounterMixin` we implemented earlier.

```python
# tests/test_descendant_counter_mixin.py

import pytest
from kind import Kind
from kind.core.mixinability import register_mixin
from my_counter_mixin import DescendantCounterMixin # Assuming my_counter_mixin.py is in your PYTHONPATH

@pytest.fixture
def sample_kind_graph():
    register_mixin(DescendantCounterMixin)  # idempotent: re-registering replaces the same mixin
    # A
    # |\
    # B C
    # |
    # D
    # E (independent)
    a = Kind("A")
    b = Kind("B")
    c = Kind("C")
    d = Kind("D")
    e = Kind("E")

    a.append(b)
    a.append(c)
    b.append(d)
    # c.append(d) # D is also a descendant of C, but only counted once

    return a, b, c, d, e

def test_count_descendants_sync(sample_kind_graph):
    a, b, c, d, e = sample_kind_graph

    # Isolation: call the mixin's function directly with a Kind as `self`
    assert DescendantCounterMixin.count_descendants(a) == 3

    # Integration: the registered method on the Kind itself
    # Test A: should have B, C, D as descendants (3 unique)
    assert a.count_descendants() == 3

    # Test B: should have D as descendant (1 unique)
    assert b.count_descendants() == 1

    # Test C: should have no descendants in this specific graph setup
    assert c.count_descendants() == 0

    # Test D and E: no descendants
    assert d.count_descendants() == 0
    assert e.count_descendants() == 0

@pytest.mark.anyio
async def test_a_count_descendants_async(sample_kind_graph):
    a, b, c, d, e = sample_kind_graph

    # Test A
    assert await a.a_count_descendants() == 3

    # Test B
    assert await b.a_count_descendants() == 1

    # Test C
    assert await c.a_count_descendants() == 0

    # Test D and E
    assert await d.a_count_descendants() == 0
    assert await e.a_count_descendants() == 0
```

**Explanation:**

*   **`@pytest.fixture` `sample_kind_graph`:** This fixture registers the mixin and sets up a consistent `Kind` graph for all tests, ensuring reproducibility. Kinds are interned by name for the whole process, so use names that no other test gives a different shape.
*   **`test_count_descendants_sync`:** This test function verifies the synchronous `count_descendants` method, once in isolation (the plain function with a `Kind` as `self`) and once integrated (called on the `Kind`).
*   **`@pytest.mark.anyio` `test_a_count_descendants_async`:** This test function verifies the asynchronous `a_count_descendants` method. The `@pytest.mark.anyio` decorator (from the pytest plugin that ships with `anyio`) is essential for running asynchronous test functions.
*   **Assertions:** We use `assert` statements to compare the actual results from the mixin methods with the expected values.

## Running the Tests

To run these tests, ensure you have `pytest` and `anyio` installed (`pip install pytest anyio`). Then, navigate to your project's root directory in the terminal and run:

```bash
pytest tests/test_descendant_counter_mixin.py
```

This will execute the tests and report any failures. Comprehensive testing ensures that your mixin behaves as expected and integrates seamlessly with the `kind` framework.
