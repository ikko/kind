# Tutorial

This path goes from one name to a rendered graph in seven steps. Each step adds one mechanism and runs as written. Reference entries are in [reference/api.md](reference/api.md), and failure messages in [reference/errors.md](reference/errors.md).

## 0. Install from the checkout

`kind` needs Python ≥ 3.10. It is private and not published to any index, so you install it from a checkout:

```bash
make install   # editable install of kind[dev,visual] and ./scheduler into ~/.virtualenvs/kind
```

`make install` uses `uv`. The `visual` extra adds the Graphviz bindings used by `to_svg`/`to_png`; Mermaid and ASCII output need nothing extra.

## 1. A name is one Kind

`Kind(name)` returns the one Kind with that name in the current space and creates it on first use. The [`k`](reference/api.md#k) namespace is shorthand for the same lookup: `k.Stock` is `Kind('Stock')`.

```python
from kind import Kind, k

assert Kind("concept_A") is Kind("concept_A")
assert k.concept_A is Kind("concept_A")
print(repr(k.concept_A), str(k.concept_A))

try:
    Kind(123)
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
Kind('concept_A') concept_A
Kind name must be a string, got int. Hint: use Kind.from_object(value) to convert other values.
```
</details>

The pool holds its Kinds strongly. A Kind keeps its state until [`delete()`](reference/api.md#kinddelete) or [`Kind.forget(name)`](reference/api.md#kindforget) removes it, or its space is closed (see [howto/isolate_a_graph.md](howto/isolate_a_graph.md)). Values that are not strings become Kinds through [`Kind.from_object`](reference/api.md#kindfrom_object):

```python
from kind import Kind

print(Kind.from_object(123).name, Kind.from_object({'b': 2, 'a': 1}).name)
print(Kind.from_object({'b': 2, 'a': 1}) is Kind.from_object({'a': 1, 'b': 2}))
```
<details>
<summary>Outcome</summary>

```text
123 {'a': 1, 'b': 2}
True
```
</details>

## 2. Edges: children and parents

[`append(child)`](reference/api.md#kindappend) links a child and returns the child; [`add(child)`](reference/api.md#kindadd) does the same and returns `self`, so calls chain. Both are idempotent. `children` and `parents` are ordered sets: insertion order, O(1) membership, no duplicates. The result is a directed graph (cycles and self-loops allowed; traversals are cycle-safe).

```python
from kind import k

root = k.SystemRoot
root.add(k.SubSystem1).add(k.SubSystem2)
k.SubSystem1.append(k.Disk).append(k.SystemRoot)   # Disk -> SystemRoot closes a cycle

print([c.name for c in root.children], [p.name for p in k.SubSystem1.parents])
print([kind.name for kind in root.tree()])          # children only, depth first, each Kind once
```
<details>
<summary>Outcome</summary>

```text
['SubSystem1', 'SubSystem2'] ['SystemRoot']
['SystemRoot', 'SubSystem1', 'Disk', 'SubSystem2']
```
</details>

[`insert(child, at)`](reference/api.md#kindinsert) places a child at a list position. [`delete()`](reference/api.md#kinddelete) removes a Kind and links its children to its parents.

## 3. Relations: named, directed, with inverses

[`a.relate(b, how)`](reference/api.md#kindrelate) records `b` under `how` on `a`, and `a` under `_inverse_<how>` on `b`. Any public name you call on a Kind that the class does not define works as a relation verb: `a.traded_on(b)` is `a.relate(b, how='traded_on')`. [`unrelate`](reference/api.md#kindunrelate) removes one `how`, or all of them.

```python
from kind import k

k.Stock.traded_on(k.Exchange)
k.Stock.relate(k.Corporation, how="issued_by")
print({how: [kind.name for kind in kinds] for how, kinds in k.Stock.relations.items()})
print([kind.name for kind in k.Exchange.relations.get("_inverse_traded_on")])

k.Stock.unrelate(k.Corporation)
print(list(k.Stock.relations))

try:
    k.Stock._private(k.Exchange)
except AttributeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
{'traded_on': ['Exchange'], 'issued_by': ['Corporation']}
['Stock']
['traded_on']
Kind 'Stock' has no attribute '_private'
```
</details>

## 4. Traversal and rendering

[`tree()`](reference/api.md#kindtree) walks children only. [`graph()`](reference/api.md#kindgraph) also walks parents and forward relations. [`GraphTraversal`](reference/api.md#graphtraversal) offers the same walk breadth first. [`to_mmd()`](reference/api.md#kindto_mmd) emits a Mermaid flowchart and [`to_ascii()`](reference/api.md#kindto_ascii) an indented outline. Both cover everything reachable through children and relations.

```python
from kind import k, GraphTraversal

project = k.ProjectAlpha
project.add(k.TaskDesign).add(k.TaskDevelopment)
k.TaskDevelopment.add(k.SubTaskCoding).add(k.SubTaskTesting)
k.TaskDesign.precedes(k.TaskDevelopment)

print([kind.name for kind in GraphTraversal(project, traverse_mode="bfs").traverse()])
print(project.to_mmd())
print(project.to_ascii())
```
<details>
<summary>Outcome</summary>

```text
['ProjectAlpha', 'TaskDesign', 'TaskDevelopment', 'SubTaskCoding', 'SubTaskTesting']
graph LR
ProjectAlpha[ProjectAlpha]
SubTaskCoding[SubTaskCoding]
SubTaskTesting[SubTaskTesting]
TaskDesign[TaskDesign]
TaskDevelopment[TaskDevelopment]
    ProjectAlpha --> TaskDesign
    TaskDesign -- precedes --> TaskDevelopment
    TaskDevelopment --> SubTaskCoding
    TaskDevelopment --> SubTaskTesting
    ProjectAlpha --> TaskDevelopment
- ProjectAlpha
  - TaskDesign
  - TaskDevelopment
    - SubTaskCoding
    - SubTaskTesting

--- Relations ---
TaskDesign --precedes--> TaskDevelopment
```
</details>

[howto/serialize.md](howto/serialize.md) covers JSON, YAML, TOML and reading these formats back.

## 5. Builtin mixins: path finding

`import kind` registers the builtin mixins on every Kind: path finding (`path_to`, `match`) and Graphviz rendering (`to_dot`, `to_svg`, `to_png`, `from_mmd`). `path_to` follows children depth first and returns `[]` when there is no path.

```python
from kind import k

k.WarehouseA.add(k.FactoryB)
k.FactoryB.add(k.DistributionCenterC)
k.DistributionCenterC.add(k.RetailStoreD)

print([kind.name for kind in k.WarehouseA.path_to(k.RetailStoreD)])
print(k.RetailStoreD.path_to(k.WarehouseA))
```
<details>
<summary>Outcome</summary>

```text
['WarehouseA', 'FactoryB', 'DistributionCenterC', 'RetailStoreD']
[]
```
</details>

## 6. Time is opt-in

Without `import kind.time`, a Kind has no time properties, and reading one raises [`AttributeError`](reference/errors.md#attributeerror):

```text
'as_datetime' is a time property, and time is opt-in. Hint: `import kind.time`.
```

Importing `kind.time` attaches them to every Kind. A Kind whose name is an ISO 8601 date or datetime then has a time; any other name raises [`ValueError`](reference/errors.md#valueerror). `time_head`/`time_tail` view the temporal Kinds of the current space, earliest or latest first.

```python
import kind.time  # opt in
from kind import Kind

drop = Kind("2023-10-26T14:05:10")
back = Kind("2023-10-26T14:05:35")
Kind("2023-10-28")                                   # a Saturday

print(back.as_datetime - drop.as_datetime, drop.hour)
view = drop.time_head
print([kind.name for kind in view], view.filter_by_workday().count())

try:
    Kind("ConnectionDrop").hour
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
0:00:25 14
['2023-10-26T14:05:10', '2023-10-26T14:05:35', '2023-10-28'] 2
Kind 'ConnectionDrop' is not an ISO 8601 date or datetime. Hint: time properties need an ISO 8601 name such as '2026-10-02' or '2026-10-02T13:45:00'.
```
</details>

## 7. Freezing a Kind

[`freeze()`](reference/api.md#kindfreeze) stops one Kind from changing. Its attributes, edges, relations and index can no longer change, and the top level of its `metadata` and `context` becomes read-only. Other Kinds stay mutable. [`immute()`](reference/api.md#kindimmute) first moves `metadata` entries onto attributes, then freezes.

```python
from kind import k, FrozenKindError

order = k.Order_1
order.metadata["status"] = "settled"
order.immute()
print(order.status, order.frozen)

try:
    order.append(k.Refund_1)
except FrozenKindError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
settled True
Kind 'Order_1' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
```
</details>

## Where to go next

- [examples.md](examples.md): domain vignettes, each on a different API path.
- [howto/isolate_a_graph.md](howto/isolate_a_graph.md): separate universes of names with `KindSpace`.
- [howto/untrusted_input.md](howto/untrusted_input.md): capping a space, and what parsing merges.
- [howto/threads_and_async.md](howto/threads_and_async.md): which space a thread or task sees, and what the lock covers.
- [howto/freeze_for_sharing.md](howto/freeze_for_sharing.md): exactly what a frozen Kind refuses.
- [howto/write_a_mixin.md](howto/write_a_mixin.md): adding methods to every Kind.
- [performance.md](performance.md): the cost of each operation.
- Scheduling lives in the separate [`kind-scheduler`](../scheduler/README.md) distribution.
