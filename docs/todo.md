# To-Do List: Enhanced .to_ascii and New .from_ascii

## Phase 1: Plan and Setup
- [x] Create `docs/plan.md`
- [x] Create `docs/todo.md`

## Phase 2: Enhance `.to_ascii`
- [x] Modify `GraphTraversal.__init__` to accept `traverse_mode`, `family_mode` (no `graph_mode`: relations follow `traverse_mode`).
- [x] Refactor `GraphTraversal.traverse` to implement DFS/BFS for family and general relations.
- [x] Update `GraphTraversal.to_ascii` to format output with relations as explicit `Source --relation_type--> Target` lines.
- [x] Update `Kind.to_ascii` to pass new parameters.

## Phase 3: Implement `.from_ascii`
- [x] Implement `Kind.from_ascii` class method based on the new `to_ascii` relation format.
- [x] Implement parsing logic for kind identification and hierarchy.
- [x] Implement parsing logic for relationship reconstruction.

## Phase 4: Testing
- [x] Write unit tests for enhanced `.to_ascii` (`tests/core/test_kind.py`).
- [x] Write unit tests for new `.from_ascii` (`tests/core/test_kind.py`).
- [x] Write roundtrip tests (`to_ascii` -> `from_ascii`) (`tests/core/test_kind.py`).

## Phase 5: Refinement (Future Iterations)
- [ ] Add error handling for malformed ASCII input in `.from_ascii`.
- [ ] Consider performance optimizations for large graphs.
