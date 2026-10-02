# Plan: an explicit KindSpace, and what belongs in the core

**Status: DECIDED AND IMPLEMENTED, 2026-10-02.** This page is kept as the record of the decision:
the reasoning and the measurements that led to it. The author answered all three questions with
the proposals below: KindSpace now, scheduling as a separate distribution (`scheduler/`, package
`kind_scheduler`), and time opt-in (`import kind.time`). The code is the source of truth.
Two details changed from the plan:
- time is opt-in by import, not a packaging extra: it has no third-party dependencies, so an extra
  would install nothing;
- `kind-scheduler` lives in this repository as its own distribution rather than in a new one.

Result, measured:
- the core is 2 230 lines, plus `kind.time` at 476;
- `kind-scheduler` is 342 lines;
- `kind` has 4 runtime dependencies (`orjson`, `anyio`, `PyYAML`, `tomli-w`; `tomli` on 3.10);
- `import kind` takes ~33 ms;
- the test fixture is `with KindSpace(): yield`.

## 1. KindSpace: global state made explicit

### The problem, measured

Everything that makes a Kind *a Kind* lives in class attributes of `BaseKind`, i.e. in one
process-wide namespace:

| state | where | used at |
|---|---|---|
| the pool (`name → Kind`) | `BaseKind._pool` | ~40 references across `base_kind.py`, `kind.py`, `time_dim.py` |
| creation order | `BaseKind._numbered` (AVL tree) | `first/last/seek/each`, `time_head` |
| counters | `BaseKind._write_cursor`, `_auto_counter` | creation positions, `Kind.next()` |
| the lock | `BaseKind._lock` (one `RLock`) | every graph mutation |
| the cap | `BaseKind.max_kinds` | creation |

Consequences that have already cost something:

- **Tests** need an autouse fixture that swaps five class attributes before each test
  (`tests/conftest.py`). The per-file versions of that fixture were wrong for months: they swapped
  `BaseKind._pool` while `Kind` used its own.
- **One universe per process.** Two independent graphs, for example two documents being parsed or
  two customers' data in a server, share names, so `from_json` *merges* into whatever already exists.
  That merge is documented as "by design", but it is only by design because there is no
  alternative.
- **Concurrency** is one `RLock` for everything. Threads working on unrelated graphs still
  serialize, and there is no test of the "thread-safe" claim.
- **Lifetime** is per process. With the strong pool (decided 2026-10-02), the only way to drop a
  whole graph is to `forget` its names one by one.

### Proposal

A `KindSpace` object owns the five pieces of state. A context variable selects the current space,
so the everyday API does not change:

```text
from kind import Kind, KindSpace

Kind("Stock")                        # the default space, exactly as today

with KindSpace() as space:           # a fresh universe
    Kind("Stock").has_kind(Kind("Security"))
    data = Kind("Stock").to_json()   # serializes inside this space
# leaving the block drops the space and every Kind in it, in O(1)

other = KindSpace(max_kinds=10_000)  # untrusted input gets its own capped space
with other:
    root = Kind.from_json(untrusted)   # cannot touch Kinds in the default space
```

Design decisions inside the proposal:

1. **`contextvars.ContextVar`, not a thread-local.** It is correct for threads *and* for
   asyncio/trio tasks, which the scheduler already uses.
2. **A Kind remembers its space** (one slot). Linking or relating Kinds from different spaces
   raises a clear error: an edge across spaces would make lifetimes undefined.
3. **One lock per space.** Unrelated graphs stop contending.
4. **Mixins stay class-level.** They are behaviour, not data: one registry for the process, as
   today (`lock_mixins()` keeps its meaning).
5. **The test fixture shrinks** to `with KindSpace(): yield`.

Cost estimate: about 150 changed lines (`base_kind.py`, `kind.py`, the `time_dim` view, the
conftest), plus one new module of about 60 lines. No change for code that never mentions a space.

Risk: Kinds created in a space and kept after it closes would be orphans. Proposal: closing a
space marks its Kinds as detached, and using a detached Kind raises an error that says why.

## 2. What belongs in the core

Measured on 2026-10-02 (`*.py` lines):

| group | modules | lines | belongs to the concept "a Kind"? |
|---|---|---:|---|
| core | base_kind, kind, kind_namespace, relations, graph_traversal, lazy_kind, collections, avl_tree, index, path | 1 423 | yes |
| extension | maturing, mixinability, mixin_validator, protocols | 484 | yes: how a Kind grows and freezes |
| visual | visual (Graphviz; Mermaid/ASCII are in core) | 152 | yes, as an optional extra (already `kind[visual]`) |
| time | time_dim, timeline, time_arithmetics | 447 | partly: "a Kind named like a date" is a *use* of Kinds |
| scheduling | schedule, batch_processing, bin/scheduler | 331 | **no**: it schedules Python functions; a Kind can be a schedule, nothing more |

### Proposal

- **Keep** core, extension and visual in `kind`.
- **Make time an optional extra** (`kind[time]`): import it as `kind.time`, and register its
  mixins only when it is imported. This is the one place where lazy loading would pay off.
- **Move scheduling out**, into a separate package (`kind-scheduler`), or delete it if nothing
  uses it. It brings three dependencies (`croniter`, `typer`, and most of the `anyio` usage), its
  own CLI and its own security surface (the `allowed_modules` allowlist), and none of it is about
  Kinds.

After the move, `kind` would be about 2 100 lines with 4 runtime dependencies (`orjson`, `PyYAML`,
`tomli-w`, and `anyio`, which the async Graphviz renderers `a_to_svg`/`a_to_png` use), plus `graphviz`
for `[visual]`.

## Questions for the author

1. KindSpace: implement as proposed, implement later, or not at all?
2. Scheduling: a separate package, or delete?
3. Time: an optional extra, or keep it built in?
