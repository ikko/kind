# Freeze a Kind before sharing it

After [`kind.freeze()`](../reference/api.md#kindfreeze) a Kind refuses every change to its own attributes and to every edge, relation or index entry that touches it, with [`FrozenKindError`](../reference/errors.md#frozenkinderror). Writes to its `metadata` and `context` are refused at the top level only (`FrozenKindError`; reading a missing key raises `KeyError` and creates nothing): values nested inside them stay mutable. Freezing is per Kind; neighbours stay mutable except for edges to the frozen Kind. A frozen Kind cannot be unfrozen.

## What freeze blocks

| change | frozen Kind `a` |
|---|---|
| set or delete an attribute (`a.color = ...`, `a.origin = ...`, `a.node_shape = ...`) | refused |
| `a.append(x)`, `x.append(a)`, `a.insert(...)`, `a.relate(x)`, `x.relate(a)`, `a.unrelate(x)` | refused |
| direct set mutation: `a.children.add(x)`, `x.parents.discard(a)`, `a.relations.add(...)` | refused for every Kind, frozen or not (`AttributeError`): edge sets change only through Kind methods |
| `x.delete()` / `Kind.forget(x.name)` for a parent, child or related Kind `x` of `a` | refused (it would change `a`'s edges) |
| `a.index.insert(...)`, `a.clear_context()`, `a.elevate()`, `a.slim()` | refused |
| `a.metadata['k'] = v`, `a.context['k'] = v` | refused |
| `a.metadata['missing']` (read) | `KeyError`; nothing is created |
| `a.metadata['tags'].append(v)` (a nested value) | **allowed** |
| changes to a neighbour that do not touch `a` (`b.relate(c)`) | allowed |

```python
from kind import Kind, FrozenKindError

catalog = Kind('Catalog')
item = catalog.append(Kind('Item'))
catalog.metadata['tags'] = ['retail']
catalog.freeze()

try:
    catalog.append(Kind('Discount'))
except FrozenKindError as error:
    print(error)
try:
    item.delete()                      # would remove the edge Catalog -> Item
except FrozenKindError as error:
    print(error)
try:
    catalog.metadata['owner'] = 'ops'
except FrozenKindError as error:
    print(error)
try:
    catalog.metadata['owner']
except KeyError as error:
    print('KeyError', error)

catalog.metadata['tags'].append('b2b')  # nested values are not frozen
print(catalog.metadata['tags'], catalog.frozen)
```
<details>
<summary>Outcome</summary>

```text
Kind 'Catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
Kind 'Catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
Kind 'Catalog' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
KeyError 'owner'
['retail', 'b2b'] True
```
</details>

Freeze nested data you share by storing values that cannot change in place (tuples, `frozenset`, `types.MappingProxyType`) before calling `freeze()`.

## Mature, then freeze

[`kind.immute()`](../reference/api.md#kindimmute) runs `elevate()` (metadata entries become attributes), `slim()` (drops elevated attributes that hold no value) and `freeze()` in that order, on this Kind only. Keys naming a Kind method, a read-only property, a structural slot (`name`, `children`, ...) or a private name stay in metadata with a warning.

```python
import warnings
from kind import Kind

product = Kind('Product')
product.metadata['price'] = 10
product.metadata['tree'] = 'not a method override'
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    product.immute()
print(product.price, product.frozen, dict(product.metadata))
print(caught[0].message)
```
<details>
<summary>Outcome</summary>

```text
10 True {'tree': 'not a method override'}
Cannot elevate 'tree' on Kind 'Product': it is a Kind method or read-only property.
```
</details>

## A closed space has the same effect on all its Kinds

Kinds of a closed [`KindSpace`](../reference/api.md#kindspace) refuse the same changes with [`SpaceError`](../reference/errors.md#spaceerror) instead, and writes to their `metadata`/`context` raise `SpaceError` at the top level too. See [isolate a graph](isolate_a_graph.md).
