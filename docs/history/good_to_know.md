### Index Callable Weight Evaluation
- cause: `TypeError` when comparing callable weight with numerical value during KindIndex insertion.
- reason: The `_insert` function in `KindIndex` (today the insertion lives in `AVLTree.insert`, `kind/builtin/avl_tree.py`) was attempting to directly compare a callable `weight` with `node.eval_weight()` without evaluating the callable first.
- resolution: Modified `_insert` to evaluate the `weight` using `weight(kind)` if it's callable before comparison, ensuring a numerical value is used.
- takeaway: Always ensure that values are of compatible types before comparison, especially when dealing with dynamic or callable attributes.

### Index Callable Weight Argument Mismatch
- cause: `AttributeError` in `dynamic_weight` function during `KindIndex` insertion test.
- reason: The `IndexNode.eval_weight` method (today `AVLNode.eval_weight`) was modified to pass `self.kind` to the callable weight, but the test's `dynamic_weight` function was still expecting an integer argument (e.g., `10`) instead of a `Kind` object.
- resolution: Modified `dynamic_weight` in `tests/builtins/test_index.py` to accept a `Kind` object and derive a numerical weight from its `name` attribute (e.g., `len(kind.name) * 2`). Also, updated the assertion in the test to reflect the correct expected value from `eval_weight()`.
- takeaway: When refactoring, ensure all dependent components (like test functions) are updated to reflect changes in function signatures or expected argument types.

### Mermaid Diagram Non-Deterministic Output
- cause: `AssertionError` in `test_to_mmd_simple_tree` due to non-deterministic order of edges in Mermaid output.
- reason: Although children were sorted before appending, the recursive `walk` function in `to_mmd` could still lead to variations in the final string due to the order of recursive calls.
- resolution: Modified the `to_mmd` function to collect all generated lines (excluding the header) and then sort them alphabetically before joining them into the final Mermaid string. The header is prepended after sorting. Today `to_mmd` is `Kind.to_mmd` in `kind/core/kind.py`: node declarations are sorted, and edges follow a deterministic depth-first walk (children in insertion order, relations by name).
- takeaway: For deterministic output from recursive functions that build strings, especially for visual representations, consider collecting all parts and sorting them before final assembly.

### Import Order of Core Components
- cause: Import errors and circular dependencies when importing `kind` due to eager loading of submodules.
- reason: Initial design loaded all submodules directly in `kind/__init__.py`, leading to issues when certain modules depended on others that were not yet fully initialized or caused circular imports.
- resolution: At the time, core components and builtin submodules were loaded lazily in `kind/__init__.py`. Today lazy loading is not a goal: all imports are absolute, and `import kind` loads `Kind`, `k`, `KindSpace`, `GraphTraversal` and the builtins eagerly (about 30–50 ms, measured 2026-10-02). Time is opt-in (`import kind.time`); the module aliases (`kind.td`, `kind.tl`, `kind.vis`, ...) are resolved on first access through the module-level `__getattr__`, and an alias into `kind.time` opts in to time.
- takeaway: Circular imports are fixed at their cause (absolute imports, a clear layer order), not hidden behind lazy loading; a module-level `__getattr__` is still handy for optional aliases.
