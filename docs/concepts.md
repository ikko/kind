# Concepts: what a Kind guarantees

A `Kind` is an interned, name-identified node in a directed graph. It stands for a category as
*data*: you create it from a string at runtime, link it to other Kinds, and attach behaviour to all
Kinds through mixins. This page is the contract. Every block on it runs in the test suite, and
the `assert` lines are the claims.

For how a Kind relates to a Python type, see [Kind vs type](kind_vs_type.md). For costs, see
[Performance](performance.md). For every error, see [Errors](reference/errors.md).

## Identity, equality, hashing

- **One name, one object, per space.** `Kind('Stock') is Kind('Stock')` while both are created in
  the same space. `BaseKind` and its subclasses share the pool. A name requested as a more
  specific class than the one it was created as raises `TypeError`.
- **Equality is name *and* space.** The hash is the name, so equal Kinds hash equal.
- **The name is fixed.** `name`, `children`, `parents` and the other identity and structure slots
  cannot be assigned: a different name is a different Kind.
- **`origin` records where a Kind came from.** The first non-`None` origin given wins.

```python
import pytest
from kind import Kind, KindSpace

a = Kind("Stock", origin="ticker list")
assert Kind("Stock") is a and Kind("Stock", origin="other").origin == "ticker list"
assert hash(a) == hash("Stock") and a != "Stock"
with KindSpace():
    assert Kind("Stock") != a            # same name, another space, another entity
with pytest.raises(AttributeError):
    a.name = "Bond"
```

## Lifetime

The pool is **strong**: a Kind keeps its identity and state (origin, metadata, relations) with no
reference held, until one of these ends it:

- `kind.delete()` or `Kind.forget(name)` (its children move up to its parents);
- leaving the `with KindSpace():` block that created it.

Memory therefore grows with the number of distinct names. `KindSpace(max_kinds=N)` makes creation
past `N` raise `KindLimitError`; set it whenever names come from input you do not control. A weak
pool would be invisible only for stateless values such as interned strings; for a Kind, it would
silently drop data.

## Spaces

A `KindSpace` owns a pool, a creation order, counters, a lock and a cap. `Kind(name)` uses the
**current** space, held in a `contextvars.ContextVar`. A process starts in a default space, so code
that never mentions spaces sees a single symbol table.

- **Entering** `with KindSpace() as space:` makes `space` current for the block.
- **Leaving** the block closes the space: it drops its references to its Kinds, O(n), and the GC
  reclaims them once nothing else refers to them. A Kind kept from a closed space can be read; any
  change raises `SpaceError`. A closed space cannot be entered again.
- **Edges cannot cross spaces.** A link or relation between Kinds of two spaces raises `SpaceError`.
- **Context propagation:**
  - asyncio and trio tasks inherit the current space, and so do anyio worker threads
    (`anyio.to_thread.run_sync` copies the context);
  - a plain `threading.Thread` starts in the **default** space unless you run its target through
    `contextvars.copy_context().run`.

```python
import contextvars
import threading
from kind import Kind, KindSpace, current_space
from kind.core.space import DEFAULT_SPACE

with KindSpace() as space:
    seen = {}
    plain = threading.Thread(target=lambda: seen.setdefault("plain", current_space()))
    context = contextvars.copy_context()
    copied = threading.Thread(target=context.run, args=(lambda: seen.setdefault("copied", current_space()),))
    for thread in (plain, copied):
        thread.start()
        thread.join()
assert seen == {"plain": DEFAULT_SPACE, "copied": space}
```

## The graph

- **Shape.** A directed graph; cycles and self-loops are allowed. Traversals (`tree`, `graph`,
  `to_ascii`, `to_mmd`, serialization) keep a visited set, so they terminate on any graph.
- **Family edges.** `a.append(b)` adds `b` to `a.children` and `a` to `b.parents`. Both are
  `OrderedKindSet`s: insertion-ordered, O(1) membership, no duplicates, so appending twice is a no-op.
- **Edges are symmetric.** Every family edge and every relation exists on both ends after any
  sequence of `append`, `relate`, `unrelate`, `reparent` and `delete` (a property test checks this).
  This holds without exception because the sets change only through those methods: `kind.children`,
  `kind.parents` and relation sets are readable, but a direct `add`/`discard`/`clear` on them raises
  `AttributeError` with a hint.
- **Relations.** `a.relate(b, how="owns")` records `b` under `a.relations.get("owns")` and `a` under
  `b.relations.get("_inverse_owns")`. Relations hold their targets strongly, like children do.
- **Removing a node.** `delete()` removes a Kind from its space and its edges, linking each of its
  children to each of its parents; `reparent()` does the linking and detaching but keeps the Kind
  in the pool.

```python
from kind import Kind

grand, mid, leaf = Kind("grand"), Kind("mid"), Kind("leaf")
grand.append(mid)
mid.append(leaf)
leaf.append(grand)                                   # a cycle is fine
mid.delete()
assert list(grand.children) == [leaf] and list(leaf.parents) == [grand]
assert [k.name for k in grand.tree()] == ["grand", "leaf"]
```

## The namespace `k` and lazily created parts

`k.Stock` and `k['Stock']` are `Kind('Stock')` in the current space. The namespace has no members of
its own, so every public name works, `k.next` included.

A Kind allocates only its name, edges and position up front. `metadata`, `context`, `index` and
`relations` are created on first access. `LazyKind(value)` defers `Kind.from_object(value)` until
the wrapper is first used.

## Attributes and dynamic relation verbs

Attribute lookup on a Kind resolves in this order:

1. class attributes, including registered mixins;
2. attributes set on this Kind (`kind.colour = "red"`, kept in its elevated attributes);
3. otherwise, **any public name is a relation verb**: `a.owns(b)` is `a.relate(b, how="owns")`.

Step 3 is a deliberate trade-off. It keeps graph-building code readable, but a misspelled public
name is a new relation verb rather than an error, and `hasattr(kind, "anything")` is `True`. Private
names (`kind._x`) raise `AttributeError`. So do the time properties when `kind.time` was not
imported: the error tells you to import it.

## Concurrency

- **Mutations** of one space (interning, `append`, `insert`, `relate`, `unrelate`, `reparent`,
  `delete`, the index, `Kind.next`) are serialized by that space's `RLock`. Different spaces never
  contend.
- **Reads** take no lock for their whole duration. Instead, each Kind's children, parents and
  relations are copied under the lock when the read reaches that Kind. A read is therefore
  consistent per Kind, not across the whole graph.
- **Composite operations are not atomic as a whole:** `from_json`/`from_yaml`/`from_toml`/
  `from_ascii`, `Kind.from_object` of a container, `patch`, and any sequence of your own calls.
  Hold `kind.space.lock` around a sequence that must be atomic.

## Freezing

- **What `freeze()` refuses.** On a frozen Kind (or `immute()`, which first elevates and slims),
  every change raises `FrozenKindError`:
  - attribute writes and deletes;
  - every edge, relation and index change;
  - writes to `metadata` and `context` (reading a missing key raises `KeyError` and creates nothing);
  - an edit of *another* Kind that would change it (deleting its child, for example).
- **The check comes first.** Multi-step edits check every Kind they will touch before touching
  any, so a refused edit leaves nothing half-applied.
- **The limit.** `metadata` and `context` are read-only at the top level only: values nested
  inside them stay mutable.
- **Not the same as the mixin registry lock.** `freeze()` is per Kind. Locking the mixin registry
  (`lock_mixins()`) is process-wide and separate.

```python
import pytest
from kind import FrozenKindError, Kind

parent, child = Kind("parent"), Kind("child")
parent.append(child)
parent.freeze()
with pytest.raises(FrozenKindError):
    child.delete()                                   # would change the frozen parent
with pytest.raises(FrozenKindError):
    parent.metadata["note"] = "late"
assert list(parent.children) == [child]              # nothing was half-applied
```

## Mixins

`register_mixin(value, name=None)` attaches a function, property or static method to every Kind
(`BaseKind` and its subclasses). A mixin is trusted code, like any method of the class.

What the registry guarantees:
- strings are refused (nothing is evaluated);
- private and dunder names are always refused;
- a name the class hierarchy already defines is refused unless you pass `safe=False`;
- a previously registered mixin may be replaced;
- after `lock_mixins()`, nothing more can be registered.

`apply_mixin_to_instance(kind, mixin)` attaches to one Kind only. Optional bundles:
- `kind.time`, imported on demand, adds the time properties and views;
- `kind.builtin.visual` adds Graphviz output and is always on.

## Conversion and serialization

- **Scalars.** `Kind.from_object(123)` is `Kind('123')`. Anything else JSON-serializable becomes
  the Kind of its JSON text: an `Enum` member with value 1 becomes `Kind('1')`, origin the member.
  `kind.to(T)` reads a name back, as JSON or a Python literal; it never evaluates code.
- **Containers.** A container becomes the Kind of its canonical content: dict keys and set members
  sorted, recursively, so equal values give one Kind. Its items become children, and a `has_kind`
  relation points to the container's type (`Kind('list')`).
- **Serialization.** `to_json`, `to_yaml` and `to_toml` dump the Kind's connected component:
  names, children order and forward relations. Origin, metadata and attributes are not dumped.
  Loading merges into existing Kinds of the same name in the current space, so load untrusted input
  into a fresh space. Details: [Serialize and round-trip](howto/serialize.md).
