# Changelog

## [v0.3.0] - 2026-10-02
### Fixed (found by verifying the documentation against the code)
- **Identity is fixed**: assigning `name`, `children`, `parents` or another identity or structure slot raises `AttributeError` with a hint. Before, `kind.name = 'z'` silently broke the pool and the hash.
- **Edges are symmetric**: `reparent()` used to leave one-sided edges, and mishandled self-loops. It now detaches the Kind completely; a property test checks every edge on both ends after any sequence of edits.
- **Freezing and closed spaces cover every change**: `unrelate`, `reparent`, deleting a neighbour, the index, and direct calls on `children`/`parents`/relation sets. Multi-step edits check every Kind they touch before changing any.
- **Reads iterate snapshots** taken under the space lock, so a concurrent `relate` no longer breaks `to_mmd`/`to_json`/traversals. `KindIndex` mutations take the space lock.
- **`to_ascii` marks parent lines** (`^ name`) and prints each family edge once, so `from_ascii` restores the family component of any Kind from depth-first output.
- **Entering a closed space** raises `SpaceError` instead of making the closed space current.
- **Time**: a space mixing naive and aware datetimes raises `ValueError` with a hint, and time-only names are non-temporal (the message says "date or datetime").
- **`kind-scheduler`**: a `Scheduler` with a schedule file refuses, at add time, jobs whose function a file cannot name (lambda, nested function, method).
- **Edge sets change only through Kind's edge methods**: a direct `add`/`discard`/`clear` on `children`, `parents` or a relation set raises `AttributeError` with a hint, so edge symmetry holds without exception.
- **Settled `metadata`/`context`**: on a frozen Kind or in a closed space, a write raises `FrozenKindError`/`SpaceError`, and reading a missing key raises `KeyError` instead of inserting it.
- **Serialized input is shape-checked**: `from_json`/`from_yaml`/`from_toml` of input that is not a list of nodes raise `ValueError` with a hint, not `KeyError`.
- **`Kind.to(T)`** reads back what `from_object` writes: JSON, else a Python literal (`ast.literal_eval`); no code is evaluated.
- **`apply_mixin_to_instance`** binds `self` to the Kind.
- **`head()`/`tail()`** return the first/last Kind of the `Kind.next()` chain by default. Before, their defaults were arbitrary (`head` stopped at position 5, `tail` with `-10.0` never moved), and the parameter names stated the opposite bound; now `head(not_before=None)` and `tail(not_after=None)`.
### Changed
- `FrozenKindError` is exported from `kind`.
- **Documentation restructured for engineers.** Pages: README; concepts (the contract); API reference; errors (every message checked by a test); performance (one complexity table); architecture; tutorial; how-to guides; examples; history. Gates check that every page is reachable from the README, that the API reference covers the public surface, and that claims are precise (no filler words, no "DAG", no unscoped "thread-safe").

## [v0.2.0] - 2026-10-02
### Added
- **`KindSpace`** (`from kind import KindSpace, current_space, SpaceError`): a separate universe of names with its own pool, creation order, counters, lock and `max_kinds`. `Kind(name)` uses the current space (a context variable: right for asyncio/trio tasks and anyio worker threads; plain threads need `contextvars.copy_context().run`). Leaving `with KindSpace():` closes the space: its Kinds are dropped, and survivors are read-only. Edges across spaces raise `SpaceError`; equality is name *and* space; `kind.space` names a Kind's space.
### Changed
- **Time is opt-in**: `kind.time` (`dim`, `timeline`, `arithmetic`) attaches its mixins on `import kind.time` (or on first use of the `kind.td`/`kind.tl` aliases). The core no longer gives every Kind `as_date`, `period` and the like; `kind.add_time`/`subtract_time` moved to `kind.time`.
- **The cap is per space**: `KindSpace(max_kinds=N)` replaces `Kind.max_kinds`.
### Quality
- **Static security scan**: `make security` runs bandit on `kind` and `kind_scheduler` (in CI too). Result: no medium or high findings; the medium-severity `eval` that v0.0.10's `register_mixin` had (B307) is gone. Two `random` uses (view shuffle and sample) are marked as not cryptographic; asserts are skipped project-wide because they state invariants, not security checks.
### Removed
- **Scheduling left the package**: it is now the separate distribution `kind-scheduler` (`scheduler/`, package `kind_scheduler`, CLI `kind-scheduler`). `kind` no longer depends on `croniter` or `typer`.

## [v0.1.0] - 2026-10-02
### Changed
- **Renamed from `symb` to `kind`**: the distribution, the package and the CLI. `Symbol` → `Kind`, `BaseSymbol` → `BaseKind`, `SymbolNamespace` → `KindNamespace`, `to_sym` → `to_kind`, and the namespace object `s` → `k` (`from kind import k`). The console script is `kind-scheduler`, because `kind` is the Kubernetes-in-Docker binary. Earlier entries below use the new names.
- **Requires Python >= 3.10.**
- **One strong intern pool**: one pool for all Kind classes, a symbol table as in Lisp and Ruby. A name is the same entity, state included, until `kind.delete()` or `Kind.forget(name)` ends it; `max_kinds` caps the pool (`KindLimitError`) for names from untrusted input.
- **`origin` defaults to `None`**; the first non-`None` origin given wins. `kind.ref` is a settable alias of `origin`.
- **Per-instance freezing**: `kind.freeze()`, `kind.frozen`, and `kind.immute()` (elevate → slim → freeze) act on one Kind; a frozen Kind raises `FrozenKindError` on any attribute, edge or relation change. The process-wide mixin registry lock is `lock_mixins()` / `mixins_locked()`.
- **`register_mixin(value, name=None, target_class=None, safe=True, expand=True)`**: refuses strings (no `eval`), private/dunder names, and core names unless `safe=False`; replacing a registered mixin is allowed. The validator checks the signature only (first parameter `self`); a mixin is trusted code.
- **`slim()`** drops only elevated attributes whose value is `SENTINEL` (unless protected); no `gc.collect()`. **`elevate()`** keeps keys that name Kind methods or read-only properties in metadata, with a warning.
- **`to_mmd()`** takes no `mode`: `graph LR`, sorted node declarations with shapes, then `A --> B` / `A -- how --> B` edges. Graphviz output (`to_dot`, `to_svg`, `to_png`, `a_to_svg`, `a_to_png`, DOT names escaped) and `from_mmd` live in `kind.builtin.visual` as mixins on every Kind; `KindRender(kind)` wraps only the Graphviz renderers.
- **Traversal**: `to_ascii(traverse_mode, family_mode)` and `GraphTraversal(root, traverse_mode, family_mode)` (`family_mode` also accepts `'children_only'`); `kind.tree()` walks children only, `kind.graph()` children, parents and relations.
- **Relations**: `a.relate(b, how=...)`, `a.unrelate(b, how=None)`, and dynamic verbs (`a.has_kind(b)`) for any public name; relations hold strong references.
- **Serialization**: `to_json`/`to_yaml`/`to_toml` dump only the connected component of the Kind; `from_*` merge into existing Kinds by name.
- **`Kind.from_object`**: scalars become the Kind of their text (`123` → `Kind('123')`); containers become a Kind named by their canonical content (dict keys and set members sorted, so equal values are one Kind), with items as children and a `has_kind` relation to `Kind('list')` (or `tuple`/`set`/`dict`).
- **Creation order**: `Kind.next()` chains `kind_0`, `kind_1`, …; `Kind.first()`/`last()`/`len()`/`seek(pos)`/`each(start)` cover the pool in creation order (`len()` is O(1)). `insert(child, at)` places a child at list index `at`.
- **`children`/`parents` are `OrderedKindSet`**: ordered, O(1) membership, no duplicates.
- **Time dimension**: a name that is not ISO 8601 has no time; `as_date`, `hour` and the like raise `ValueError` instead of assuming today at midnight, and `kind.time_head` / `kind.time_tail` include only temporal Kinds. `KindHeadTailView` operations are named for what they return: filters `filter_by_*` (a view; `filter_by_weekday(n)`, `filter_by_workday()`), selectors `first/last/nth/closest/furthest` (a Kind), reshapers `reversed/shuffled/sample/unique` (a view), aggregates `map/reduce/sum/min/max/average/median/mode/std/variance/percentile/quantile/count/is_empty/any/all/none/span` (a value).
- **Scheduler**: `Scheduler(schedule_file=None, allowed_modules=(), now=datetime.datetime.now)`; `ScheduledJob(func, args=(), kwargs=None, schedule=..., id=None)`; `run_due_jobs()` runs one deterministic step. `process_batch(batch, func, new_thread=True)` and `a_process_batch(batch, func)`.
### Added
- **`Timeline.overlap(other)`**: returns a Timeline of the common periods.
- **`Kind.forget(name)`**, **`max_kinds`** and **`KindLimitError`**: explicit lifetime for names.
- **`Kind.ls()`** lists the registered mixins and **`kind.stat()`** reports this Kind's own state; the module that guessed "mixins" from every class in the package (`kind/core/mixins.py`) is removed.
- **`from_mmd`** raises `ValueError` on a line it cannot read, instead of an `AttributeError`.
### Quality
- Every runnable Python block in README.md and docs/ runs in the test suite (86 blocks; 6 opt out with a stated reason).
- Property-based tests (Hypothesis) for the AVL tree, `OrderedKindSet`, serialization round trips and canonical names; a mutation check confirmed each catches a deliberate fault.
- `mypy` is clean for Python 3.10–3.14 (`make typecheck`); CI runs lint, type check and tests on 3.10, 3.11, 3.12, 3.13 and 3.14. The 3.10–3.13 runs found a documentation example that only worked on 3.14 (deferred annotations).
### Security
- **Schedule files** may only name functions from `allowed_modules` (CLI: `kind-scheduler -f FILE -m MODULE add|list|remove|run`).
- **`register_mixin`** no longer evaluates strings.
- **DOT output** escapes Kind names, so a name cannot inject Graphviz attributes.
### Removed
- The global `freeze()` / `is_frozen()` (see per-instance freezing above), `apply_mixin` (use `apply_mixin_to_instance`), `Kind.prev()`, the length cache, `que()`, `graph_mode`, the `mode` argument of `to_mmd()`, `KindRender.to_mmd`/`to_ascii`, the `from_int`/`from_float`/`from_str`/`from_bool`/`from_none`/`from_enum`/`from_list` constructors (use `Kind.from_object` / `to_kind`), the `new_process`/`new_thread` flags of `ScheduledJob`, and the `new_process` flag of `process_batch`.
- Modules `kind/builtin/red_black_tree.py` (`AVLTree` remains), `kind/core/kindable.py`, `kind/core/lazy.py`, `kind/core/type_var_t.py`, `kind/utils/memory.py` and `kind/config.py`; `SENTINEL` lives in `kind/core/lazy_kind.py`.
- `filter_by_timezone` and `filter_by_dst` (they always returned an empty view), and the `filter_by_` prefix on operations that do not filter.
- The plan for lazy loading of builtins (`import kind` takes ~35 ms with them).
- Import-time `logging.basicConfig` calls: the library no longer configures root logging.
### Fixed
- **Installable package**: the `symb` 0.0.10 wheel installed top-level `core`, `builtin`, `bin` and `utils` packages, so `import symb` failed after `pip install`. All imports are now absolute (`kind.core…`), and the wheel contains only `kind/`.
- **One copy of each module**: mixin discovery imported `symb.core.*` while the rest of the code used `core.*`, so two distinct `Symbol` classes were loaded.

## [v0.0.10] - 2025-07-13
### Added
- **Dynamic Relation Syntax**: Introduced a more intuitive and expressive API for defining relationships between `Kind` instances (e.g., `kind.relates_to(other)` instead of `kind.relate(other, how='relates_to')`). This enhances the readability and semantic clarity of graph construction, aligning with principles of Domain-Specific Languages (DSLs).
- **Comprehensive Serialization/Deserialization**: Added robust capabilities for persisting and reconstructing `Kind` graphs to/from various structured data formats: JSON (`to_json`, `from_json`), YAML (`to_yaml`, `from_yaml`), and TOML (`to_toml`, `from_toml`). This significantly improves data interchange, reproducibility, and integration with external systems.
- **ASCII Graph Round-trip**: Implemented `Kind.from_ascii()` to complement the enhanced `Kind.to_ascii()`, enabling full round-trip serialization of `Kind` graphs into human-readable ASCII representations. This is invaluable for debugging, visualization, and simplified data sharing.
- **Configurable Graph Traversal**: Introduced a dedicated `GraphTraversal` class with parameters (`traverse_mode`, `family_mode`, and `graph_mode`, removed in v0.1.0) for fine-grained control over graph exploration strategies (DFS, BFS, and specific family/general relation traversal orders). This provides greater flexibility for algorithmic development and analysis.
- **PyPI-Optimized Documentation**: Integrated a new `docs/pypi_org/` directory (now `docs/package/`) with scripts (`start.sh`, `update.py`) to generate a PyPI-specific `README.md` that includes rendered SVG diagrams and transformed links. This enhances the project's presentation and accessibility on the Python Package Index.
- **Formalized Development Planning**: Added `docs/plan.md` and `docs/todo.md` to formalize development planning and task tracking, promoting a more structured and transparent project management approach.
- **Software Architecture Overview**: Included `docs/software_architecture.md` to provide a high-level overview of the system's design, aiding in comprehension for new contributors and facilitating architectural discussions.

### Changed
- **Architectural Decomposition**: Performed a significant refactoring of the core `Kind` implementation, decomposing `kind/core/kind.py` into `kind/core/kind.py` (for core `Kind` logic) and `kind/core/kind_namespace.py` (for the `k` namespace and related utilities). This enhances modularity, reduces coupling, and improves maintainability.
- **Module Renaming**: Renamed the `kind/builtins` package to `kind/builtin` for improved naming consistency and adherence to Python's standard library conventions. All internal and external references have been updated accordingly.
- **Python Version Requirement**: Increased the minimum required Python version from `3.6` to `3.8` in `pyproject.toml` (raised to `3.10` in v0.1.0) to leverage modern language features and ensure compatibility with contemporary development environments.
- **Project Metadata**: Updated `pyproject.toml` with comprehensive project metadata, including PyPI classifiers, author information, and explicit URLs for homepage, repository, and documentation. This improves project discoverability and formalizes its distribution.
- **Test Fixture Refinement**: Modified `tests/conftest.py` to introduce a more robust `kind_fixture` that ensures a clean `Kind._pool` state for each test and pre-populates a complex bioinformatics graph for comprehensive testing of graph operations and serialization.

### Fixed
- Minor documentation inconsistencies and code formatting issues across various files.

## [v0.0.6] - 2025-07-10
- Initial release of the package with basic functionality, including:
  - Core `Kind` object with interning mechanism for unique identity.
  - Basic parent-child graph relationships.
  - Mixin-based extensibility for dynamic behavior injection.
  - Preliminary graph traversal capabilities.
  - Memory-aware object management.
