# API reference

Every public name of `kind`, with its signature, behaviour, cost and failures. Signatures come from `inspect.signature` on the current code. In the cost lines, n is the number of Kinds in the space, V and E are the Kinds and edges a call reaches, d is the largest number of neighbours of one Kind, c and p are the children and parents of the Kind in question. Every exception links to [errors](errors.md). Background is in [concepts](../concepts.md); measured timings are in [performance](../performance.md).

- [Package `kind`](#package-kind)
- [Kind: construction and identity](#kind-construction-and-identity)
- [Kind: graph edges](#kind-graph-edges)
- [Kind: relations](#kind-relations)
- [Kind: traversal and rendering](#kind-traversal-and-rendering)
- [Kind: serialization](#kind-serialization)
- [Kind: creation order and sequence](#kind-creation-order-and-sequence)
- [Kind: conversion](#kind-conversion)
- [Kind: maturing and freeze](#kind-maturing-and-freeze)
- [Kind: introspection](#kind-introspection)
- [Kind: builtin mixins](#kind-builtin-mixins)
- [Kind: time mixins (after `import kind.time`)](#kind-time-mixins-after-import-kindtime)
- [Supporting classes](#supporting-classes)
- [Mixin registry](#mixin-registry)
- [Package `kind.time`](#package-kindtime)
- [Module `kind.builtin.visual`](#module-kindbuiltinvisual)
- [Module aliases](#module-aliases)

## Package `kind`

`import kind` loads the core and registers the builtin mixins (path finding, Graphviz rendering, `from_mmd`); it does not load `kind.time`. `kind.__all__` is the list below.

### `Kind`

`Kind(name: str, origin: Any = None)`

An interned, name-identified node of a directed graph (cycles and self-loops allowed; traversals are cycle-safe). `Kind(name)` returns the Kind of that name in the [current space](#current_space), creating it on first use, so `Kind('A') is Kind('A')`. Every member is listed in the `Kind:` sections below.

### `k`

`k.<name>` and `k['<name>']` return `Kind('<name>')`. The namespace has no members of its own, so every public name is free (`k.next` is `Kind('next')`, not `Kind.next`). A private name raises `AttributeError`, so `hasattr`, `copy` and `pickle` never create Kinds by probing. **Cost:** as [`Kind`](#kind). **Raises:** [`AttributeError`](errors.md#attributeerror) for a name starting with `_`; [`TypeError`](errors.md#typeerror) on assignment.

```python
from kind import k

print(k.Stock is k['Stock'], repr(k.next))
try:
    k.Stock = 1
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
True Kind('next')
KindNamespace is read-only, cannot set Stock to 1
```
</details>

### `FrozenKindError`

Subclass of `AttributeError`, raised when a frozen Kind is asked to change: see [`Kind.freeze`](#kindfreeze) and [errors](errors.md#frozenkinderror).

### `KindLimitError`

Subclass of `RuntimeError`, raised when creating a Kind would exceed its space's `max_kinds`: see [`KindSpace`](#kindspace) and [errors](errors.md#kindlimiterror).

### `KindSpace`

`KindSpace(max_kinds: int | None = None, name: str = 'space')`

One universe of names, with its own pool (`space.pool`, a `dict` from name to Kind), creation order (`space.order`, an AVL tree), `Kind.next()` counter, `threading.RLock` (`space.lock`) and size cap. Used as a context manager it becomes the current space for the block, and leaving the block closes it. Closing drops the space's references to its Kinds; a Kind still referenced elsewhere stays readable, and any change to it raises `SpaceError`. A closed space cannot be entered again. The process starts in a default space (`KindSpace('default')`), which cannot be closed.

Members: `name`, `max_kinds` (`None` is unbounded), `pool`, `order`, `lock`, `closed`, `get(name)` (the Kind or `None`), `name in space`, `len(space)`, `iter(space)` (creation order), `close()`.

**Cost:** `get`, `in`, `len`: O(1); `iter`: O(n); `close`: O(n). **Raises:** [`KindLimitError`](errors.md#kindlimiterror) when a new name would exceed `max_kinds`; [`SpaceError`](errors.md#spaceerror) on entering a closed space, closing the default space, or changing a Kind of a closed space.

```python
from kind import Kind, KindSpace, KindLimitError, SpaceError

with KindSpace(max_kinds=2, name="capped") as space:
    Kind('a'), Kind('b')
    print(space, 'a' in space, [kind.name for kind in space])
    try:
        Kind('c')
    except KindLimitError as error:
        print(error)
survivor = space.get('a')
print(space, survivor)
try:
    with space:
        pass
except SpaceError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
KindSpace('capped', 2 kinds) True ['a', 'b']
Cannot create 'c': KindSpace('capped', 2 kinds) already holds max_kinds=2 Kinds. Hint: delete() or Kind.forget() Kinds you no longer need, or raise the space's max_kinds.
KindSpace('capped', closed) None
KindSpace('capped', closed) is closed and cannot be entered again. Hint: open a new KindSpace().
```
</details>

### `SpaceError`

Subclass of `RuntimeError`, raised for an edge across spaces or a change to a Kind whose space is closed: see [`KindSpace`](#kindspace) and [errors](errors.md#spaceerror).

### `current_space`

`current_space() -> KindSpace`

The space `Kind(name)` looks names up in right now: the innermost open `with KindSpace()` block of this context, else the default space. It is a `contextvars.ContextVar`, so asyncio and trio tasks and anyio worker threads inherit it, and a `threading.Thread` sees the default space unless its target runs under `contextvars.copy_context().run(...)`. **Cost:** O(1).

### `GraphTraversal`

`GraphTraversal(root: Kind, traverse_mode: Literal['dfs', 'bfs'] = 'dfs', family_mode: Literal['children_first', 'parents_first', 'children_only'] = 'children_first')`

Iterative depth- or breadth-first walk from `root` that visits each reachable Kind once. Neighbours come group by group: children and parents in the order `family_mode` names (`children_only` skips parents and relations), then forward relations; each group is sorted by name. Each Kind's edges are read from a snapshot taken under its space's lock.

- `traverse() -> list[Kind]`: every reachable Kind, in visit order.
- `traverse_family() -> list[Kind]`: Kinds reachable over children and parents only.
- `to_ascii() -> str`: the outline [`Kind.to_ascii`](#kindto_ascii) returns.

**Cost:** O(V + E log d). **Raises:** [`ValueError`](errors.md#valueerror) for an unknown mode.

```python
from kind import Kind, GraphTraversal

root = Kind('root')
root.append('b'), root.append('a')
root.relate(Kind('x'), how='uses')
print([kind.name for kind in GraphTraversal(root, 'bfs').traverse()])
try:
    GraphTraversal(root, traverse_mode='random')
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
['root', 'a', 'b', 'x']
Unknown traverse_mode: 'random' (expected 'dfs' or 'bfs')
```
</details>

### `builtin`

The subpackage `kind.builtin`: `OrderedKindSet` (`kind.builtin.collections`), `KindIndex` (`kind.builtin.index`), `AVLTree` (`kind.builtin.avl_tree`), `KindPathMixin` (`kind.builtin.path`), the Graphviz renderers and `from_mmd` (`kind.builtin.visual`), and `apply_builtins()`, which registers the builtin mixins (idempotent; `import kind` already calls it).

### `core`

The subpackage `kind.core`: `Kind`, `BaseKind`, `KindSpace`, `GraphTraversal`, `Relations`, `LazyKind`, the mixin registry (`kind.core.mixinability`) and the namespace `k`.

## Kind: construction and identity

### `Kind.name`

The Kind's name, a `str`. It is the identity within a space and cannot be assigned. **Raises:** [`AttributeError`](errors.md#attributeerror) on assignment or deletion (also for `parents` and `children`).

```python
from kind import Kind

stock = Kind('Stock')
try:
    stock.name = 'Bond'
except AttributeError as error:
    print(error)
try:
    Kind(42)
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
'name' is part of Kind 'Stock''s identity or structure and cannot be assigned. Hint: use append/insert/relate/delete to change edges; a different name is a different Kind.
Kind name must be a string, got int. Hint: use Kind.from_object(value) to convert other values.
```
</details>

`Kind(name)` raises [`TypeError`](errors.md#typeerror) for a non-string name (use [`Kind.from_object`](#kindfrom_object)) and when the name already exists as a less specific class (see [`BaseKind`](#basekind)); [`KindLimitError`](errors.md#kindlimiterror) at the space's cap; [`SpaceError`](errors.md#spaceerror) when the current space is closed. **Cost:** O(1) average for an existing name; O(log n) for a new name (insert into `space.order`).

Two Kinds are equal when they have the same name and the same space; the hash is the name's hash. `<` orders by creation position.

### `Kind.origin`

The value the Kind was made from, or `None`. The first non-`None` origin given wins: `Kind('a', origin=1)` sets it, a later `Kind('a', origin=2)` does not change it. Assignment sets it directly. **Cost:** O(1).

### `Kind.ref`

Read-write alias of [`Kind.origin`](#kindorigin).

### `Kind.node_shape`

A Mermaid shape name used by [`Kind.to_mmd`](#kindto_mmd), or `None` for the default rectangle: `round`, `stadium`, `subroutine`, `cylindrical`, `circle`, `double_circle`, `asymmetric`, `rhombus`, `hexagon`, `parallelogram`, `parallelogram_alt`, `trapezoid`, `trapezoid_alt`. An unknown name renders as the default rectangle.

### `Kind.space`

The [`KindSpace`](#kindspace) the Kind belongs to. **Cost:** O(1).

### `Kind.metadata`

A `DefDict` (a `defaultdict` whose missing keys become nested `defaultdict(dict)`), created on first access. Once the Kind is frozen or its space is closed it is returned as a settled mapping: reading a missing key raises `KeyError` and creates nothing, and a write at the top level raises the same error as any other change; nested values stay mutable. [`Kind.elevate`](#kindelevate) moves its entries onto the Kind. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) on a write when frozen; [`SpaceError`](errors.md#spaceerror) when the space is closed; [`KeyError`](errors.md#keyerror) for a missing key once settled.

### `Kind.context`

A second `DefDict` for transient data, created on first access, settled under the same conditions and with the same errors as [`Kind.metadata`](#kindmetadata). [`Kind.clear_context`](#kindclear_context) empties it.

### `Kind.index`

The Kind's own [`KindIndex`](#kindindex), created on first access.

### Attributes set at runtime

Assigning any other name (`stock.ticker = 'XYZ'`) stores an elevated attribute on that Kind only; reading it returns the value. A public name that is neither an attribute nor elevated is a [dynamic relation verb](#kindrelations). **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) on a frozen Kind; [`SpaceError`](errors.md#spaceerror) when its space is closed.

## Kind: graph edges

`children` and `parents` are [`OrderedKindSet`](#orderedkindset)s: insertion-ordered, no duplicates, O(1) membership. Every edge is recorded on both ends. All edge methods take the space's lock, check every Kind they will change before changing any (a refusal never leaves a half-applied edit), and raise [`SpaceError`](errors.md#spaceerror) for an edge across spaces.

### `Kind.children`

The Kinds directly under this one, in insertion order. Readable; it changes only through [`Kind.append`](#kindappend), [`Kind.insert`](#kindinsert), [`Kind.reparent`](#kindreparent) and [`Kind.delete`](#kinddelete), which keep both ends of every edge. **Raises:** [`AttributeError`](errors.md#attributeerror) on a direct `add`, `discard`, `remove`, `insert`, `pop` or `clear`, for every Kind, frozen or not.

```python
from kind import Kind

parent, child = Kind('parent'), Kind('child')
parent.append(child)
try:
    child.parents.discard(parent)
except AttributeError as error:
    print(error)
print([p.name for p in child.parents])
```
<details>
<summary>Outcome</summary>

```text
The edge sets of Kind 'child' change only through append, insert, relate, unrelate, reparent and delete, which keep both ends of every edge. Hint: call one of those instead of changing children/parents/relations directly.
['parent']
```
</details>

### `Kind.parents`

The Kinds this one is directly under, in insertion order; changes only through Kind methods, as [`Kind.children`](#kindchildren).

### `Kind.append`

`append(self, child: Any) -> Kind`

Links `child` under this Kind and returns the child. A non-Kind value is converted with [`Kind.from_object`](#kindfrom_object); a [`LazyKind`](#lazykind) is evaluated. Appending an existing child does nothing. **Cost:** amortized O(1), plus the conversion. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) if either end is frozen; [`SpaceError`](errors.md#spaceerror) across spaces or for a closed space.

```python
from kind import Kind, KindSpace, SpaceError

with KindSpace(name="left"):
    left = Kind('L')
    with KindSpace(name="right"):
        right = Kind('R')
        try:
            left.append(right)
        except SpaceError as error:
            print(error)
```
<details>
<summary>Outcome</summary>

```text
Cannot link 'L' in KindSpace('left', 1 kinds) to 'R' in KindSpace('right', 1 kinds): an edge across spaces would make their lifetimes undefined. Hint: create both inside the same `with KindSpace():` block.
```
</details>

### `Kind.add`

`add(self, child: Any) -> Kind`

[`Kind.append`](#kindappend) that returns `self`, so calls chain: `a.add(b).add(c)` puts both under `a`, while `a.append(b).append(c)` puts `c` under `b`. **Cost** and **raises:** as `append`.

### `Kind.insert`

`insert(self, child: Any, at: int | None = None) -> Kind`

Places `child` at list index `at` among the children (the end for `None`), moving it if it is already a child; returns `self`. **Cost:** O(c). **Raises:** as [`Kind.append`](#kindappend).

### `Kind.reparent`

`reparent(self) -> None`

Detaches this Kind from the hierarchy: each of its children is linked to each of its parents, then this Kind keeps no parents and no children. A self-loop is dropped. **Cost:** O(p·c) new edges, plus O(siblings) to unlink this Kind from each neighbour's list. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) if this Kind or any neighbour is frozen; [`SpaceError`](errors.md#spaceerror) for a closed space.

### `Kind.delete`

`delete(self) -> None`

Removes the Kind from the graph and from its space: re-parents its children, leaves the `Kind.next()` chain, leaves its own index, removes its relations in both directions, and removes it from `space.pool` and `space.order`. A later `Kind(name)` creates a fresh Kind. **Cost:** as [`Kind.reparent`](#kindreparent), plus O(siblings) per relation and O(log n) for `space.order`. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) if the Kind, a parent, a child or a related Kind is frozen; [`SpaceError`](errors.md#spaceerror) for a closed space.

```python
from kind import Kind

root, middle, leaf = Kind('root'), Kind('middle'), Kind('leaf')
root.append(middle).append(leaf)
middle.delete()
print([kind.name for kind in root.children], Kind('middle') is middle)
```
<details>
<summary>Outcome</summary>

```text
['leaf'] False
```
</details>

### `Kind.pop`

`pop(self) -> Kind`

[`Kind.delete`](#kinddelete), then returns the deleted Kind.

### `Kind.popleft`

`popleft(self) -> Kind | None`

Deletes and returns the first child, or returns `None` when there are no children. **Cost** and **raises:** as [`Kind.delete`](#kinddelete) on that child.

### `Kind.each_children`

`each_children(self) -> Iterator[Kind]`

Iterator over `children` in insertion order. **Cost:** O(1) to create, O(c) to exhaust.

### `Kind.each_parents`

`each_parents(self) -> Iterator[Kind]`

Iterator over `parents` in insertion order. **Cost:** O(1) to create, O(p) to exhaust.

## Kind: relations

A relation is a named, directed edge outside the parent/child hierarchy. `a.relate(b, how='uses')` records `uses → b` on `a` and the inverse `_inverse_uses → a` on `b`. Relations hold strong references and keep insertion order per name.

### `Kind.relations`

The Kind's [`Relations`](#relations), created on first access. Any public name not defined on `Kind` is a relation verb: `a.depends_on(b)` is `a.relate(b, how='depends_on')`, and keyword arguments name the relation (`a.has(color='red')`). Non-Kind arguments are converted with [`Kind.from_object`](#kindfrom_object). Without `import kind.time`, the time attribute names (`as_date`, `hour`, ...) are reserved and raise `AttributeError` instead of becoming verbs. **Raises:** [`AttributeError`](errors.md#attributeerror) for a private name; [`TypeError`](errors.md#typeerror) for a verb called without arguments.

```python
from kind import Kind

app = Kind('app')
app.depends_on(Kind('db'), Kind('cache'))
print({how: [kind.name for kind in kinds] for how, kinds in app.relations.items()})
try:
    app._secret(Kind('db'))
except AttributeError as error:
    print(error)
try:
    app.depends_on()
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
{'depends_on': ['db', 'cache']}
Kind 'app' has no attribute '_secret'
'depends_on' relation requires at least one argument or keyword argument.
```
</details>

### `Kind.relate`

`relate(self, other: Kind, how: str = 'related') -> Kind`

Relates this Kind to `other` under `how` and records the inverse on `other`; returns `self`. Relating twice under the same name does nothing. **Cost:** amortized O(1). **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) if either end is frozen; [`SpaceError`](errors.md#spaceerror) across spaces or for a closed space.

### `Kind.unrelate`

`unrelate(self, other: Kind, how: str | None = None) -> Kind`

Removes the relation to `other` under `how`, or under every name when `how` is `None`, on both ends; returns `self`. **Cost:** O(r) for the Kinds related under one name, O(h + r) when `how` is `None` (h relation names). **Raises:** as [`Kind.relate`](#kindrelate).

### `Kind.patch`

`patch(self, other: Kind) -> Kind`

Merges `other`'s direct links into this Kind: its origin (only if this one has none), its children, its parents and its forward relations. It does not recurse and does not change `other`. Returns `self`. **Cost:** O(edges of `other`). **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) if this Kind or any Kind it would link is frozen, checked before any change.

## Kind: traversal and rendering

### `Kind.tree`

`tree(self) -> list[Kind]`

This Kind and its descendants, depth first, children sorted by name; each Kind once. **Cost:** O(V + E log d).

### `Kind.graph`

`graph(self) -> list[Kind]`

Every Kind reachable through children, parents and forward relations, depth first; each Kind once. **Cost:** O(V + E log d).

```python
from kind import Kind

a, b, c = Kind('a'), Kind('b'), Kind('c')
a.append(b)
c.append(b)
b.relate(Kind('d'), how='uses')
print([kind.name for kind in b.tree()], [kind.name for kind in b.graph()])
```
<details>
<summary>Outcome</summary>

```text
['b'] ['b', 'a', 'c', 'd']
```
</details>

### `Kind.to_mmd`

`to_mmd(self) -> str`

Mermaid flowchart of everything reachable through children and forward relations: `graph LR`, then one sorted declaration per Kind with its [`node_shape`](#kindnode_shape), then the edges in depth-first order, `A --> B` for a child and `A -- how --> B` for a relation. Spaces in names become `_` in node ids. [`Kind.from_mmd`](#kindfrom_mmd) reads it back. **Cost:** O(V log V + E log d).

```python
from kind import Kind

order = Kind('Order')
order.node_shape = 'round'
order.append(Kind('Line Item'))
order.relate(Kind('Customer'), how='placed_by')
print(order.to_mmd())
```
<details>
<summary>Outcome</summary>

```text
graph LR
Customer[Customer]
Line_Item[Line Item]
Order(Order)
    Order --> Line_Item
    Order -- placed_by --> Customer
```
</details>

### `Kind.to_ascii`

`to_ascii(self, traverse_mode: Literal['dfs', 'bfs'] = 'dfs', family_mode: Literal['children_first', 'parents_first'] = 'children_first') -> str`

Indented outline, one line per family edge: `- name` is a child of the line above, `^ name` a parent. A Kind is expanded where it first appears; later appearances only record the edge. Relations follow under `--- Relations ---`, sorted. Depth-first output is read back exactly by [`Kind.from_ascii`](#kindfrom_ascii); breadth-first output interleaves branches and is for display only. **Cost:** O(V + E log d), plus O(R log R) to sort R relations. **Raises:** [`ValueError`](errors.md#valueerror) for an unknown mode.

```python
from kind import Kind

shared = Kind('shared')
Kind('x').append(shared)
Kind('y').append(shared)
shared.relate(Kind('z'), how='uses')
print(Kind('x').to_ascii())
```
<details>
<summary>Outcome</summary>

```text
- x
  - shared
    ^ y

--- Relations ---
shared --uses--> z
```
</details>

### `Kind.head`

`head(self, up_to_position: float = 5.0) -> BaseKind`

Walks back along the [`Kind.next`](#kindnext) chain while the previous Kind's creation position is at least `up_to_position`, and returns where it stops (this Kind if it cannot step). **Cost:** O(steps).

### `Kind.tail`

`tail(self, from_position: float = -10.0) -> BaseKind`

Walks forward along the `Kind.next` chain while the next Kind's creation position is at most `from_position`, and returns where it stops. With the default `-10.0` it does not move. **Cost:** O(steps).

## Kind: serialization

`to_json`, `to_yaml` and `to_toml` dump the connected component of the Kind (children, parents and relations in either direction), sorted by name: one entry per Kind with `name`, `children` (in order) and forward `relations` (names sorted). They do not keep origin, metadata, context, elevated attributes, `node_shape`, the frozen state or the `Kind.next()` chain. The `from_*` methods merge into the current space by name: a node named like an existing Kind extends it. They return the first Kind by name that no other parsed Kind points to. **Cost:** dump O(V log V + E log d); load O(V log n + E). Each node's shape is checked before any Kind is created. A parse stopped by `KindLimitError` is not rolled back: parse into a fresh space and discard it on error. **Raises:** [`ValueError`](errors.md#valueerror) for input with no Kinds, for a node that is not `{'name': str, 'children': [str], 'relations': {how: [str]}}`, and (as `orjson.JSONDecodeError`, a `ValueError`) for text that is not JSON; [`KindLimitError`](errors.md#kindlimiterror) when the space is full.

### `Kind.to_json`

`to_json(self) -> str`

JSON array, indented by two spaces (orjson).

```python
from kind import Kind

a = Kind('a')
a.append('b')
a.relate(Kind('c'), how='uses')
print(Kind('b').to_json())
for text in ('[]', '[{"name": 5}]'):
    try:
        Kind.from_json(text)
    except ValueError as error:
        print(error)
```
<details>
<summary>Outcome</summary>

```text
[
  {
    "name": "a",
    "children": [
      "b"
    ],
    "relations": {
      "uses": [
        "c"
      ]
    }
  },
  {
    "name": "b",
    "children": [],
    "relations": {}
  },
  {
    "name": "c",
    "children": [],
    "relations": {}
  }
]
No kinds found in the JSON input.
JSON node 0 is not {'name': str, 'children': [str], 'relations': {how: [str]}}: {'name': 5}. Hint: produce it with to_json().
```
</details>

### `Kind.from_json`

`from_json(json_string: str) -> Kind` (classmethod)

Reads [`Kind.to_json`](#kindto_json) output.

### `Kind.to_yaml`

`to_yaml(self) -> str`

The same list as YAML (`yaml.safe_dump`, keys in dump order).

### `Kind.from_yaml`

`from_yaml(yaml_string: str) -> Kind` (classmethod)

Reads [`Kind.to_yaml`](#kindto_yaml) output with `yaml.safe_load`.

### `Kind.to_toml`

`to_toml(self) -> str`

The same list as a TOML array of tables under the key `kinds` (`tomli_w`).

### `Kind.from_toml`

`from_toml(toml_string: str) -> Kind` (classmethod)

Reads [`Kind.to_toml`](#kindto_toml) output (`tomllib`, or `tomli` on Python 3.10).

### `Kind.from_ascii`

`from_ascii(ascii_string: str) -> Kind` (classmethod)

Rebuilds the graph from [`Kind.to_ascii`](#kindto_ascii) output and returns the Kind on the first line: `- name` lines are children of the line above, `^ name` lines parents, and a repeated name is the same Kind with one more edge; relation lines are read back too. **Cost:** O(L log n) for L lines. **Raises:** [`ValueError`](errors.md#valueerror) when no line names a Kind.

## Kind: creation order and sequence

Every Kind has a creation position in its space (`0.0`, `1.0`, ...), kept in the AVL tree `space.order`. These classmethods act on the current space.

### `Kind.next`

`next() -> Kind` (classmethod)

Creates `kind_0`, `kind_1`, ... (one counter per space) and links each to the previous one through `_prev`/`_next`. **Cost:** O(log n). **Raises:** as [`Kind`](#kind) construction.

```python
from kind import Kind, KindSpace

with KindSpace(name="sequence"):
    first, second = Kind.next(), Kind.next()
    print(first, second, second.head(up_to_position=0.0), Kind.len(), Kind.seek(1.0))
```
<details>
<summary>Outcome</summary>

```text
kind_0 kind_1 kind_0 2 kind_1
```
</details>

### `Kind.rebind_linear_sequence`

`rebind_linear_sequence(self) -> None`

Removes this Kind from the `Kind.next()` chain and joins its neighbours. [`Kind.delete`](#kinddelete) calls it. **Cost:** O(1).

### `Kind.first`

`first() -> Kind | None` (classmethod)

The earliest created Kind of the current space, or `None` when it is empty. **Cost:** O(log n).

### `Kind.last`

`last() -> Kind | None` (classmethod)

The most recently created Kind of the current space, or `None`. **Cost:** O(log n).

### `Kind.seek`

`seek(pos: float) -> Kind | None` (classmethod)

The Kind created at position `pos` in the current space, or `None`. **Cost:** O(log n).

### `Kind.each`

`each(start: float | Kind | None = None) -> Iterator[Kind]` (classmethod)

Kinds of the current space in creation order, from position `start` (or from a given Kind) on. **Cost:** O(n). **Raises:** [`TypeError`](errors.md#typeerror) for any other `start`, when iteration begins.

```python
from kind import Kind

try:
    list(Kind.each('first'))
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
Invalid start parameter 'first' of type str in each()
```
</details>

### `Kind.len`

`len() -> int` (classmethod)

The number of Kinds in the current space. **Cost:** O(1).

### `Kind.forget`

`forget(name: str) -> bool` (classmethod)

Deletes the Kind called `name` in the current space if there is one, and returns whether there was. **Cost** and **raises:** as [`Kind.delete`](#kinddelete); O(1) when the name is absent.

### `Kind.auto_date`

`auto_date() -> Kind` (classmethod)

`Kind(datetime.date.today().isoformat())`, e.g. `Kind('2026-10-02')`. **Cost:** as [`Kind`](#kind).

### `Kind.auto_datetime`

`auto_datetime() -> Kind` (classmethod)

`Kind(datetime.datetime.now().isoformat())`.

### `Kind.auto_time`

`auto_time() -> Kind` (classmethod)

`Kind(datetime.datetime.now().time().isoformat())`.

## Kind: conversion

### `Kind.from_object`

`from_object(obj: Any) -> Kind` (classmethod)

Converts a value to a Kind and records the value as its origin (the first non-`None` origin wins). A Kind is returned as is; a [`LazyKind`](#lazykind) is evaluated. `None`, `bool`, `int`, `float` and `str` become the Kind of their text (`123` → `Kind('123')`). A `list`, `tuple`, `set`, `frozenset` or `dict` becomes the Kind named by its canonical text (`canonical_repr` in `kind.core.kind`: dict keys and set members sorted by their own canonical form, recursively; lists and tuples keep their order), with its items as children (a dict's values hang under their keys) and a `has_kind` relation to `Kind('list')`, `Kind('tuple')`, `Kind('set')`, `Kind('frozenset')` or `Kind('dict')`. So equal values are one Kind, and a key such as `Kind('a')` is shared by every dict that has the key `'a'`, values included. Any other object is named by its JSON text (orjson). `to_kind(obj)` in `kind.core.kind` is the function form. **Cost:** O(N log N) for a container of N items in total (canonical sorting), plus O(log n) per new Kind. **Raises:** [`TypeError`](errors.md#typeerror) for an object orjson cannot serialize.

```python
from kind import Kind

order = Kind.from_object({'qty': 2, 'item': 'pen'})
print(repr(order), [kind.name for kind in order.children], order.relations.get('has_kind')[0])
print(Kind.from_object({'item': 'pen', 'qty': 2}) is order, Kind.from_object(123).origin)
try:
    Kind.from_object(object())
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
Kind('{'item': 'pen', 'qty': 2}') ['qty', 'item'] dict
True 123
Cannot convert object to Kind: Type is not JSON serializable: object. Hint: give the object a JSON-serializable form, or pass its name.
```
</details>

### `Kind.to`

`to(self, target_type: Type[T]) -> T`

Converts the name back to a value: `str` returns the name; any other type reads the name as JSON, else as a Python literal through `ast.literal_eval` (no code is evaluated), and converts the result with `target_type` unless it already is one. So names that `Kind.from_object` makes from Python values (`'True'`, `'None'`, `"{'a': 1}"`, `"(1, 'x')"`) convert back. **Cost:** O(length of the name). **Raises:** [`TypeError`](errors.md#typeerror) when the name is neither JSON nor a Python literal.

```python
from kind import Kind

print(Kind('[1, 2]').to(list), Kind('3.5').to(float), Kind('True').to(bool), Kind("{'a': 1}").to(dict))
try:
    Kind('Store').to(int)
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
[1, 2] 3.5 True {'a': 1}
Cannot convert Kind 'Store' to int: the name is neither JSON nor a Python literal.
```
</details>

## Kind: maturing and freeze

Maturing turns metadata into attributes and then freezes the Kind. A frozen Kind refuses attribute assignment and deletion, every edge, relation and index change (including the deletion of a neighbour, which would change its edges), `elevate`, `slim` and `clear_context`. Writes to its `metadata` and `context` raise `FrozenKindError` at the top level only: nested values stay mutable. (Edge sets never change through direct calls, frozen or not: see [`Kind.children`](#kindchildren).) A freeze cannot be undone.

### `Kind.frozen`

`True` once [`Kind.freeze`](#kindfreeze) or [`Kind.immute`](#kindimmute) has run. **Cost:** O(1).

### `Kind.freeze`

`freeze(self) -> Kind`

Freezes this Kind and returns it; idempotent. **Cost:** O(1). Later changes raise [`FrozenKindError`](errors.md#frozenkinderror).

```python
from kind import Kind, FrozenKindError

catalog, item = Kind('catalog'), Kind('item')
catalog.append(item)
catalog.metadata['tags']['new'] = True
catalog.freeze()
for change in (lambda: catalog.append('other'), lambda: item.delete(),
               lambda: catalog.metadata.__setitem__('owner', 'ops')):
    try:
        change()
    except FrozenKindError as error:
        print(error)
try:
    catalog.metadata['owner']  # reading a missing key creates nothing
except KeyError as error:
    print('KeyError', error, 'owner' in catalog.metadata)
catalog.metadata['tags']['sale'] = True  # nested values stay mutable
print(dict(catalog.metadata['tags']))
```
<details>
<summary>Outcome</summary>

```text
Kind 'catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
Kind 'catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
Kind 'catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
KeyError 'owner' False
{'new': True, 'sale': True}
```
</details>

### `Kind.elevate`

`elevate(self, merge_strategy: Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth'] = 'smooth') -> Set[str]`

Moves each metadata entry onto the Kind as an attribute and returns the keys moved. When the attribute already holds a value, the new one is merged with `merge_strategy`: `overwrite`, `copy`, `deepcopy`, `patch` (Kinds, via [`Kind.patch`](#kindpatch)), `pipe` (call the new value with the current one), `update` (mappings), `extend` (lists) or `smooth` (recursive merge of mappings; lists extended; a conflicting scalar is added as `<key>_new`). A key naming a structural slot, a private name, a Kind method or a read-only property stays in metadata with a `UserWarning`. **Cost:** O(m) for m metadata entries, plus the merges. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror).

```python
import warnings
from kind import Kind

sensor = Kind('sensor')
sensor.metadata['unit'] = 'C'
sensor.metadata['tree'] = 'shadowed'
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    print(sorted(sensor.elevate()), sensor.unit, dict(sensor.metadata))
print(caught[0].message)
```
<details>
<summary>Outcome</summary>

```text
['unit'] C {'tree': 'shadowed'}
Cannot elevate 'tree' on Kind 'sensor': it is a Kind method or read-only property.
```
</details>

### `Kind.slim`

`slim(self, protected_attributes: Set[str] | None = None) -> None`

Drops elevated attributes whose value is `SENTINEL` (`kind.core.lazy_kind.SENTINEL`, the marker for "no value yet"), except the protected ones. It does not touch slots, mixins or other values. **Cost:** O(a) for a elevated attributes. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror).

### `Kind.immute`

`immute(self, merge_strategy: ... = 'smooth') -> Kind`

[`Kind.elevate`](#kindelevate), then [`Kind.slim`](#kindslim) protecting the keys just elevated, then [`Kind.freeze`](#kindfreeze); returns the Kind. On a frozen Kind it returns at once. **Cost:** O(m + a).

### `Kind.clear_context`

`clear_context(self) -> None`

Empties [`Kind.context`](#kindcontext); does nothing if it was never created. **Cost:** O(entries). **Raises:** [`FrozenKindError`](errors.md#frozenkinderror); [`SpaceError`](errors.md#spaceerror) for a closed space.

## Kind: introspection

### `Kind.footprint`

`footprint(self) -> int`

Bytes (`sys.getsizeof`) of this Kind and its descendants, including names, origins, metadata, context, index and elevated attributes, each object counted once. **Cost:** O(size of the reachable objects).

### `Kind.stat`

`stat(self) -> None`

Prints the Kind's footprint, its numbers of children, parents and forward relation names, its own attributes, the number of registered mixins and its frozen state.

### `Kind.ps`

`ps() -> None` (classmethod)

Prints every Kind of the current space, sorted by name, with its footprint and origin, then the total. **Cost:** O(n log n) plus one footprint per Kind.

### `Kind.ls`

`ls() -> None` (classmethod)

Prints the names of the registered mixins, sorted.

## Kind: builtin mixins

Registered on `BaseKind` by `import kind` (see [`apply_builtins`](#builtin)).

### `Kind.path_to`

`path_to(self, target: Kind) -> list[Kind]`

A path of child links from this Kind to `target`, found depth first, or `[]`. **Cost:** O(V + E).

### `Kind.match`

`match(self, predicate: Callable[[Kind], bool], traversal: str = 'dfs') -> Iterator[Kind]`

Lazily yields this Kind and its descendants for which `predicate` is true, depth first, or breadth first for `traversal='bfs'`. **Cost:** O(V + E) when exhausted.

### `Kind.to_dot`

`to_dot(self, mode: Literal['tree', 'graph'] = 'tree') -> str`

See [`to_dot`](#to_dot).

### `Kind.to_svg`

`to_svg(self, mode='tree') -> str`. See [`to_svg`](#to_svg).

### `Kind.to_png`

`to_png(self, mode='tree') -> bytes`. See [`to_png`](#to_png).

### `Kind.a_to_svg`

`async a_to_svg(self, mode='tree') -> str`. See [`a_to_svg`](#a_to_svg).

### `Kind.a_to_png`

`async a_to_png(self, mode='tree') -> bytes`. See [`a_to_png`](#a_to_png).

### `Kind.from_mmd`

`Kind.from_mmd(mmd_string: str) -> Kind` (staticmethod). See [`from_mmd`](#from_mmd).

## Kind: time mixins (after `import kind.time`)

These attributes exist only after `import kind.time` (or the first access to an alias such as `kind.td`); without it, reading one raises `AttributeError` with a hint. Each reads the time from the Kind's ISO 8601 name (`datetime.datetime.fromisoformat`; a date means midnight). **Raises:** [`ValueError`](errors.md#valueerror) when the name is not an ISO 8601 date or datetime; [`AttributeError`](errors.md#attributeerror) without the opt-in.

<!-- doc-example: not-run — the test suite opts in to kind.time, so the AttributeError cannot happen there -->
```python
from kind import Kind

try:
    Kind('2026-10-02').as_date
except AttributeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
'as_date' is a time property, and time is opt-in. Hint: `import kind.time`.
```
</details>

```python
import kind.time
from kind import Kind

print(Kind('2026-10-02T13:45:00').hour, Kind('2026-10-02').as_date)
try:
    Kind('Stock').as_date
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
13 2026-10-02
Kind 'Stock' is not an ISO 8601 date or datetime. Hint: time properties need an ISO 8601 name such as '2026-10-02' or '2026-10-02T13:45:00'.
```
</details>

### `Kind.as_datetime`

Property: the `datetime.datetime` of the name. **Cost:** O(length of the name).

### `Kind.as_date`

Property: the `datetime.date` part.

### `Kind.as_time`

Property: the `datetime.time` part.

### `Kind.day`

Property: the day of the month.

### `Kind.hour`

Property: the hour.

### `Kind.minute`

Property: the minute.

### `Kind.second`

Property: the second.

### `Kind.time_head`

Property: a [`KindHeadTailView`](#kindheadtailview) of every temporal Kind of this Kind's space (names that parse as ISO 8601), earliest first; other Kinds are skipped. **Cost:** O(n + m log m) per access for m temporal Kinds among n. **Raises:** [`ValueError`](errors.md#valueerror) when the space mixes naive and timezone-aware datetimes.

### `Kind.time_tail`

Property: the same view, latest first. **Cost:** as `time_head`.

### `Kind.period`

Property: the `datetime.timedelta` from the earliest to the latest temporal Kind of the space (zero for fewer than two). It does not depend on which Kind it is read from. **Cost:** as `time_head`.

### `Kind.as_period`

Alias of [`Kind.period`](#kindperiod).

### `Kind.duration`

Alias of [`Kind.period`](#kindperiod).

### `Kind.as_duration`

Alias of [`Kind.period`](#kindperiod).

### `Kind.delta`

Alias of [`Kind.period`](#kindperiod).

### `Kind.as_delta`

Alias of [`Kind.period`](#kindperiod).

## Supporting classes

### `BaseKind`

`kind.core.base_kind.BaseKind(name: str, origin: Any = None)`

The interned node `Kind` extends: the slots `name`, `origin`, `parents`, `children`, `node_shape`, the creation position, the `next()` links and the space, plus `space`, equality (name and space), hashing (name) and ordering (creation position). One pool per space serves every class of the hierarchy: `BaseKind('A')` returns an existing `Kind('A')`, while `Kind('A')` after `BaseKind('A')` raises `TypeError`, because one name has one identity. Mixins register on `BaseKind` by default, so every Kind sees them. **Cost** and **raises:** as [`Kind`](#kind) construction.

```python
from kind import KindSpace
from kind.core.base_kind import BaseKind
from kind import Kind

with KindSpace(name="hierarchy"):
    BaseKind('plain')
    try:
        Kind('plain')
    except TypeError as error:
        print(error)
```
<details>
<summary>Outcome</summary>

```text
'plain' already exists as BaseKind, so it cannot also be a Kind: one name has one identity. Hint: create it as Kind first, or delete() the existing one.
```
</details>

### `OrderedKindSet`

`kind.builtin.collections.OrderedKindSet(items=None, guard=None)`

The type of `children`, `parents` and each relation's targets: an insertion-ordered set of Kinds. `guard`, when given, runs before every change. A Kind's sets get a guard that refuses any change not made by a Kind edge method (`AttributeError`), then applies the freeze and space checks; a free-standing `OrderedKindSet` has no guard.

| member | behaviour | cost |
|---|---|---|
| `add(kind)` / `append(kind)` | add at the end; `False` if present | amortized O(1) |
| `insert(index, kind)` | place at `index`, moving it if present | O(len) |
| `remove(kind)` | remove; `KeyError` if absent | O(len) |
| `discard(kind)` | remove if present | O(len) |
| `pop(index=-1)` | remove and return | O(1) at the end, else O(len) |
| `clear()` | remove all | O(len) |
| `kind in s`, `len(s)`, `s[i]` | membership, size, indexing | O(1) |
| `iter(s)`, `reversed(s)`, `==` (with an `OrderedKindSet`, list or tuple) | in order | O(len) |

**Raises:** [`KeyError`](errors.md#keyerror) from `remove` for an absent Kind; whatever the guard raises ([`AttributeError`](errors.md#attributeerror) for a direct change to a Kind's set, [`FrozenKindError`](errors.md#frozenkinderror), [`SpaceError`](errors.md#spaceerror)).

### `Relations`

`kind.core.relations.Relations(owner)`

Per-Kind map from relation name to an [`OrderedKindSet`](#orderedkindset) of related Kinds; inverse entries are stored under `_inverse_<how>`. `items()`, `iter()` and `len()` include the inverse names; `get(how)` returns the set, or an empty unattached set. `add`/`remove`, and the sets `get` returns, refuse direct changes with `AttributeError`; relations change only through [`Kind.relate`](#kindrelate) and [`Kind.unrelate`](#kindunrelate), which keep the inverse in step. Attribute access with a public name returns the verb proxy described under [`Kind.relations`](#kindrelations). **Cost:** `get`, `add`: O(1) amortized; `remove`: O(r).

### `KindIndex`

`kind.builtin.index.KindIndex(owner: Kind)`

A Kind's own index (`kind.index`): other Kinds sorted by a weight, a number or a function of the Kind, in an AVL tree. `insert(kind, weight)` (re-inserting a Kind replaces its weight), `remove(kind)`, `traverse(order='in')` (in-order list; other orders raise `NotImplementedError`), `map(fn)`, `filter(pred)`, `ascii()` / `to_ascii()`. Insert and search assume each weight is distinct and stable: a function weight is evaluated when the tree compares, so a weight that changes after insertion misplaces the Kind. **Cost:** `insert`, `remove`: O(log k) for k indexed Kinds with distinct, stable weights; `traverse`, `map`, `filter`: O(k). **Raises:** [`FrozenKindError`](errors.md#frozenkinderror) on `insert`/`remove` when the owner is frozen.

```python
from kind import Kind

board = Kind('board')
for name, score in (('ann', 30), ('bob', 10), ('cy', 20)):
    board.index.insert(Kind(name), score)
print([kind.name for kind in board.index.traverse()])
```
<details>
<summary>Outcome</summary>

```text
['bob', 'cy', 'ann']
```
</details>

### `LazyKind`

`kind.core.lazy_kind.LazyKind(obj: Any)`

Wraps a value and converts it with [`Kind.from_object`](#kindfrom_object) on first use: attribute access, equality, hashing or passing it to `append`/`insert`. `evaluated` tells whether that has happened; `evaluate()` forces it. Its `repr` shows `LazyKind(unevaluated: ...)` until then. **Cost:** O(1) until evaluated, then as `from_object`.

```python
from kind.core.lazy_kind import LazyKind
from kind import Kind

pending = LazyKind([1, 2])
print(pending)
Kind('owner').append(pending)
print(pending.evaluated, repr(pending))
```
<details>
<summary>Outcome</summary>

```text
LazyKind(unevaluated: [1, 2])
True Kind('[1, 2]')
```
</details>

## Mixin registry

`kind.core.mixinability`. A mixin is trusted code: registering one is equivalent to editing the class. The registry only guarantees that a mixin cannot silently replace the core API.

### `register_mixin`

`register_mixin(value: Any, name: str | None = None, target_class: type | None = None, safe: bool = True, expand: bool = True) -> bool`

Attaches `value` (a function, property, staticmethod or descriptor) as attribute `name` of `target_class` (default `BaseKind`, so every Kind sees it); a class or module is expanded into its public members when `expand` is true. The name defaults to the function name, or the snake-cased class name without `_mixin`. It returns `True` on success and `False` on a [refusal](errors.md#refusals-that-do-not-raise), which it logs at ERROR level: a private or dunder name; a name the target class or a subclass defines (unless `safe=False`); a function whose first parameter is not `self` (the signature is the only check, the code is not inspected); a locked registry. Registering the same name again replaces the previous mixin. **Raises:** [`TypeError`](errors.md#typeerror) for a string (strings are never evaluated).

```python
from kind import Kind
from kind.core.mixinability import register_mixin

def shout(self) -> str:
    return self.name.upper()

def append(self) -> None:
    pass

print(register_mixin(shout), Kind('quiet').shout(), register_mixin(append))
try:
    register_mixin("lambda self: 1")
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
True QUIET False
register_mixin got the string 'lambda self: 1'; strings are not evaluated. Hint: pass the function, class or module object itself.
```
</details>

### `lock_mixins`

`lock_mixins() -> None`

Locks the registry for the whole process; every later `register_mixin` returns `False`. No public function reverses it.

### `mixins_locked`

`mixins_locked() -> bool`

Whether `lock_mixins()` has run.

### `get_applied_mixins`

`get_applied_mixins() -> dict[str, Any]`

A copy of the registry: mixin name → the attribute it replaced (`None` if it was new).

### `apply_mixin_to_instance`

`apply_mixin_to_instance(instance: Kind, mixin: Any) -> None`

Attaches a mixin to one Kind only, as elevated attributes bound to that Kind like methods: a function becomes `kind.<name>()` with `self` = the Kind; a class contributes its public functions bound to the Kind, its properties evaluated on the Kind now (the value, not a live property), its staticmethods as plain functions, and its other public attributes as they are. The class is not instantiated. **Raises:** [`FrozenKindError`](errors.md#frozenkinderror); [`SpaceError`](errors.md#spaceerror) for a closed space.

## Package `kind.time`

Opt-in: `import kind.time` (or the first access to `kind.time`, `kind.td`, `kind.time_dim`, `kind.tl`, `kind.timeline`) registers the [time mixins](#kind-time-mixins-after-import-kindtime) on every Kind. Modules: `kind.time.dim`, `kind.time.timeline`, `kind.time.arithmetic`.

### `enable`

`enable() -> None`

Registers the time mixins; idempotent, and run once on import.

### `parse_timestamp`

`parse_timestamp(name: str) -> datetime.datetime | None`

The datetime an ISO 8601 name denotes (a date means midnight), or `None`.

### `when`

`when(kind: Kind) -> datetime.datetime`

The datetime of a temporal Kind. **Raises:** [`ValueError`](errors.md#valueerror) for any other Kind.

### `KindTimeDimMixin`

The class whose members `enable()` registers: the properties listed under [Kind: time mixins](#kind-time-mixins-after-import-kindtime).

### `KindHeadTailView`

`KindHeadTailView(items: Iterable[Kind])`

An ordered view over temporal Kinds, returned by `time_head` and `time_tail`; supports `len()`, iteration and indexing. Operations are named for what they return; all are O(m) for m Kinds in the view unless noted.

- Filters → a narrower view: `filter_by_year(year)`, `filter_by_month(year, month)`, `filter_by_day(year, month, day)`, `filter_by_hour(...)`, `filter_by_minute(...)`, `filter_by_second(...)`, `filter_by_weekday(weekday)` (Monday 0), `filter_by_week_of_year(week)`, `filter_by_quarter(quarter)`, `filter_by_time_of_day(name)` (morning 5–12, afternoon 12–17, evening 17–21, night 21–5), `filter_by_leap_year(flag)`, `filter_by_start_of_month()`, `filter_by_end_of_month()`, `filter_by_start_of_year()`, `filter_by_end_of_year()`, `filter_by_start_of_quarter()`, `filter_by_end_of_quarter()`, `filter_by_start_of_week()`, `filter_by_end_of_week()`, `filter_by_weekend()`, `filter_by_workday()` (Monday–Friday), `filter_by_yesterday()`, `filter_by_today()`, `filter_by_tomorrow()`, `filter_by_future()`, `filter_by_past()`, `filter_by_same_day(x)`, `filter_by_same_month(x)`, `filter_by_same_year(x)`, `filter_by_same_quarter(x)`, `filter_by_same_week(x)`, `filter_by_same_weekday(x)`, `filter_by_same_time(x)`, `filter_by_between(start, end)` (inclusive). `x`, `start` and `end` are Kinds or datetimes.
- Selectors → one Kind: `first()`, `last()`, `nth(n)`, `closest(x)`, `furthest(x)`.
- Reshapers → a view: `reversed()`, `shuffled()`, `sample(n)`, `unique()`.
- Aggregates → a value, over `fn(kind)`: `map(fn)`, `reduce(fn, initial)`, `sum(fn)`, `min(fn)`, `max(fn)`, `average(fn)`, `median(fn)`, `mode(fn)` (list of the most frequent), `std(fn)` and `variance(fn)` (population), `percentile(fn, p)`, `quantile(fn, q)` (linear interpolation, O(m log m)); plus `count()`, `is_empty()`, `any(pred)`, `all(pred)`, `none(pred)`, `span()` (last minus first; also the properties `period`, `as_period`, `days`, `seconds`).

**Raises:** [`ValueError`](errors.md#valueerror) for an unknown time of day or a non-temporal Kind as `x`; `IndexError` from selectors on an empty view.

```python
import kind.time
from kind import Kind, KindSpace

with KindSpace(name="calendar"):
    for name in ('2026-10-05', '2026-10-02', '2026-10-03', 'not a date'):
        Kind(name)
    days = Kind('2026-10-02').time_head
    print([kind.name for kind in days], days.filter_by_workday().count(), days.span())
    try:
        days.filter_by_time_of_day('noon')
    except ValueError as error:
        print(error)
```
<details>
<summary>Outcome</summary>

```text
['2026-10-02', '2026-10-03', '2026-10-05'] 2 3 days, 0:00:00
Unknown time of day 'noon'; expected one of ['afternoon', 'evening', 'morning', 'night']
```
</details>

### `Timeline`

`Timeline(periods: list[tuple[datetime, datetime]] | None = None)`

A sorted list of `(start, end)` periods; overlapping periods are kept, not merged. `add_period(start, end)` inserts in order (O(p) for p periods); `overlap(other)` returns a Timeline of the periods both cover (O(p·q)); iteration yields the periods; `to_ascii(resolution=timedelta(days=1))` draws `#` for covered steps and `-` otherwise. **Raises:** [`ValueError`](errors.md#valueerror) when `start >= end`.

```python
import datetime
from kind.time import Timeline

day = lambda d: datetime.datetime(2026, 10, d)
print(list(Timeline([(day(1), day(5))]).overlap(Timeline([(day(3), day(9))]))))
try:
    Timeline([(day(5), day(1))])
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
[(datetime.datetime(2026, 10, 3, 0, 0), datetime.datetime(2026, 10, 5, 0, 0))]
Start datetime must be before end datetime.
```
</details>

### `add_time_objects`

`add_time_objects(obj1, obj2) -> datetime | timedelta`

`datetime + timedelta` (either order) or `timedelta + timedelta`. **Raises:** [`TypeError`](errors.md#typeerror) for other combinations.

### `subtract_time_objects`

`subtract_time_objects(obj1, obj2) -> datetime | timedelta`

`datetime - timedelta`, `datetime - datetime` or `timedelta - timedelta`. **Raises:** [`TypeError`](errors.md#typeerror) for other combinations.

## Module `kind.builtin.visual`

Graphviz output for a Kind graph, and the reader for [`Kind.to_mmd`](#kindto_mmd) output. The functions take the Kind first, so each is also a mixin (`kind.to_dot()`). Graphviz output needs the `visual` extra (`graphviz` Python package) and, for SVG and PNG, the Graphviz `dot` executable. Names are written as escaped DOT string IDs, so a name cannot inject attributes.

### `to_dot`

`to_dot(self: Kind, mode: Literal['tree', 'graph'] = 'tree') -> str`

DOT source: `digraph G { "a" -> "b" ... }`, one line per child edge reachable from the Kind; in `graph` mode forward relations are edges too, labelled with their name. **Cost:** O(V + E). **Raises:** [`ImportError`](errors.md#importerror) without the `graphviz` package.

```python
from kind import Kind

quote = Kind('say "hi"')
quote.append('reply')
quote.relate(Kind('topic'), how='about')
print(quote.to_dot(mode='graph'))
```
<details>
<summary>Outcome</summary>

```text
digraph G {
"say \"hi\"" -> "reply"
"say \"hi\"" -> "topic" [label="about"]
}
```
</details>

### `to_svg`

`to_svg(self: Kind, mode='tree') -> str`

The DOT source rendered to SVG by Graphviz, in a worker thread (`anyio.run`, so it cannot be called from inside a running event loop; use `a_to_svg` there). **Raises:** [`ImportError`](errors.md#importerror); Graphviz errors when `dot` is missing.

### `to_png`

`to_png(self: Kind, mode='tree') -> bytes`

As `to_svg`, rendered to PNG bytes.

### `a_to_svg`

`async a_to_svg(self: Kind, mode='tree') -> str`

`to_svg` for use inside an event loop.

### `a_to_png`

`async a_to_png(self: Kind, mode='tree') -> bytes`

`to_png` for use inside an event loop.

### `from_mmd`

`from_mmd(mmd_string: str) -> Kind`

Rebuilds the graph described by `Kind.to_mmd()` output in the current space and returns its root (the first Kind by name that no edge points to): node declarations give names and shapes (a shape is set only where the Kind has none), `A --> B` appends, `A -- how --> B` relates. A node id without a declaration becomes the Kind named by the id with `_` read as a space. Names merge by interning. **Cost:** O(L log n) for L lines. **Raises:** [`ValueError`](errors.md#valueerror) for a header other than `graph LR`/`graph TD`, an unreadable line, or no Kinds.

```python
from kind import Kind, KindSpace
from kind.builtin.visual import from_mmd

with KindSpace(name="source"):
    order = Kind('Order')
    order.node_shape = 'round'
    order.relate(Kind('Customer'), how='placed_by')
    text = order.to_mmd()
with KindSpace(name="copy"):
    copy = from_mmd(text)
    print(copy, copy.node_shape, [kind.name for kind in copy.relations.get('placed_by')])
try:
    from_mmd('flowchart TB')
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
Order round ['Customer']
Unsupported Mermaid header ['flowchart TB']; expected 'graph LR' or 'graph TD'.
```
</details>

### `KindRender`

`KindRender(root: Kind)`

Thin wrapper exposing `to_dot`, `to_svg`, `to_png`, `a_to_svg`, `a_to_png` (all with `mode`) and `from_mmd` for one Kind: `KindRender(kind).to_svg()` equals `kind.to_svg()`. Mermaid and ASCII output are `Kind` methods, not part of `KindRender`.

## Module aliases

`kind.<alias>` imports a module on first access; aliases into `kind.time` also opt in to time, as `import kind.time` does.

| alias | module |
|---|---|
| `kind.time` | `kind.time` |
| `kind.time_dim`, `kind.td` | `kind.time.dim` |
| `kind.timeline`, `kind.tl` | `kind.time.timeline` |
| `kind.collections`, `kind.coll` | `kind.builtin.collections` |
| `kind.index`, `kind.idx` | `kind.builtin.index` |
| `kind.path` | `kind.builtin.path` |
| `kind.visual`, `kind.vis` | `kind.builtin.visual` |

Any other unknown attribute of `kind` raises [`AttributeError`](errors.md#attributeerror). Scheduling is not part of `kind`: it is the separate distribution [`kind-scheduler`](../../scheduler/README.md).
