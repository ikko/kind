# Performance

Looking up an existing name costs one dictionary lookup under its space's lock. Everything else
depends on the size of the space (n), the size of the graph you touch (V Kinds, E edges), the number of
neighbours of one Kind (d), or the length of one edge list (siblings). The table below is read off the
code in `kind/`. It is not taken from the measurements, which follow it.

## Complexity

| Operation | Cost | Condition |
|---|---|---|
| `Kind(name)`, name exists | O(1) average | One `dict` lookup in `space.pool` (the hash of a `str` is cached after the first use). |
| `Kind(name)`, new name | O(log n) | AVL insert into `space.order`; n = Kinds in the current space. `KindSpace(max_kinds=...)` adds an O(1) check. |
| `Kind.next()` | O(log n) | Creates a new name, then links `_prev`/`_next` in O(1). |
| `a.append(b)`, `a.add(b)` | O(1) amortized | Both ends are `OrderedKindSet`s (a list plus a set); adding an existing edge does nothing. |
| `a.insert(b, at)` | O(siblings) | `list.insert`, plus a removal first if `b` is already a child. |
| Removing an edge (`children.discard`, `unrelate(b, how)`) | O(siblings) | `list.remove` on the edge list. `unrelate(b)` without `how` also scans every `how` of `a`. |
| `a.relate(b, how)`, `a.has_kind(b)` | O(1) amortized | One add on each end (the forward `how` and the inverse `_inverse_<how>`). |
| `a.reparent()` | O(p·c + Σ siblings) | Links each of the p parents to each of the c children, and removes `a` from every neighbour's edge list. |
| `a.delete()`, `Kind.forget(name)` | O(p·c + Σ siblings + r + log n) | `reparent()`, then the r relations in both directions, then an AVL delete from `space.order`. |
| `a.tree()`, `a.graph()`, `GraphTraversal.traverse()` | O(V + E log d) | Iterative and cycle-safe. Each Kind's neighbours are copied under the lock and sorted by name. |
| `a.to_ascii()` | O(V + E log d) | Same walk as `tree()` and `graph()`, plus sorting the relation lines. |
| `a.to_mmd()` | O(V log V + E log d) | Node declarations are sorted, and relation targets are sorted per `how`. |
| `to_json` / `to_yaml` / `to_toml` | O(V log V + E log d) | Breadth-first over the connected component, which is then sorted by name. |
| `from_json` / `from_yaml` / `from_toml` / `from_ascii` / `from_mmd` | O(V log n + E) | Every node is a `Kind(name)`, then one append or relate per edge. Picking the root sorts the nodes once more. |
| `Kind.from_object(value)` | O(S · D + sorting) | S = items, D = nesting depth: every nested container recomputes its canonical name, and dict keys and set members are sorted. |
| `Kind.first()`, `Kind.last()`, `Kind.seek(pos)` | O(log n) | Leftmost or rightmost path, or a search in `space.order`. |
| `Kind.each(start)` | O(n) | Builds the in-order list of the whole space, then skips the Kinds before `start`. |
| `Kind.len()` | O(1) | `len(space.pool)`. |
| `kind.time_head`, `kind.time_tail`, `kind.period` | O(n + m log m) per access | Parses every name in the space and sorts the m temporal ones. The result is not cached. Needs `import kind.time`. |
| `KindIndex.insert`, `KindIndex.tree.search` | O(log n_index) | Holds only for distinct weights that do not change after insertion. A callable weight is called at every node visited. |
| `KindIndex.remove` | O(log n_index); O(n_index) worst | Equal weights may sit on either side after rotations, so both subtrees are searched. |
| `KindIndex.traverse`, `map`, `filter` | O(n_index) | In-order walk. |
| `kind.path_to(target)`, `kind.match(pred)` | O(V + E) | Children only, cycle-safe. |
| `kind.freeze()`, `kind.frozen` | O(1) | A flag. Every later change checks it first. |
| `kind.immute()` | O(k + a) | k metadata keys, each merged by its strategy (cost of `smooth` grows with the size of the nested values), and a elevated attributes. |
| `kind.footprint()` | O(size of the reachable data) | Walks the descendants and everything attached to them, counting each object once. |
| `KindSpace.close()` | O(n) | Clears the pool and drops the order tree. |

A frozen Kind or a Kind of a closed space refuses a change before anything is written. Operations that
touch several Kinds (`delete`, `reparent`, `patch`, `unrelate`) check every Kind they will change first,
so a refusal costs one extra pass over those Kinds and never leaves a half-applied edit. The errors are
[`FrozenKindError`](reference/errors.md#frozenkinderror) and
[`SpaceError`](reference/errors.md#spaceerror). The full signatures are in
[reference/api.md](reference/api.md).

## Measurements

Measured on 2026-10-02 on an Intel Core Ultra 5 225 (10 cores) under Linux 6.17, with CPython 3.14.7.
Each size runs in its own `KindSpace`, so n is exactly the number of Kinds created. The per-Kind
traversal and serialization cost rises with n because the root has n − 1 children, which are sorted by
name (the log d term). Timings vary by machine; only their ratios are meaningful.

```python
import time

import kind.time  # opt in: time_head is measured below
from kind import Kind, KindSpace


def per_op_us(operation, repeat):
    start = time.perf_counter()
    for _ in range(repeat):
        operation()
    return (time.perf_counter() - start) / repeat * 1e6


for n in (1_000, 100_000):
    with KindSpace(name=f"bench-{n}"):
        start = time.perf_counter()
        kinds = [Kind(f"node_{i}") for i in range(n)]               # new names: AVL insert into space.order
        create = (time.perf_counter() - start) / n * 1e6
        lookup = per_op_us(lambda: Kind("node_7"), 100_000)        # existing name: one dict lookup
        root = kinds[0]
        start = time.perf_counter()
        for child in kinds[1:]:
            root.append(child)                                      # amortized O(1) per edge
        append = (time.perf_counter() - start) / (n - 1) * 1e6
        tree = per_op_us(root.tree, 3) / n                          # O(V + E log d), per Kind
        dump = per_op_us(root.to_json, 3) / n                       # O(V log V + E log d), per Kind
        length = per_op_us(Kind.len, 100_000)                       # O(1)
        first = per_op_us(Kind.first, 10_000)                       # O(log n)
        print(f"n={n:>6}  create {create:.2f} us  lookup {lookup:.2f} us  append {append:.2f} us  "
              f"tree {tree:.2f} us/Kind  to_json {dump:.2f} us/Kind  len {length:.2f} us  first {first:.2f} us")

with KindSpace(name="bench-time"):
    for day in range(1, 29):
        Kind(f"2026-02-{day:02d}")
    for i in range(1_000):
        Kind(f"word_{i}")
    head = per_op_us(lambda: Kind("word_0").time_head, 100)        # O(n + m log m) over the whole space
    print(f"time_head over 1028 Kinds (28 dates): {head:.1f} us")
```
<details>
<summary>Outcome</summary>

```text
n=  1000  create 4.05 us  lookup 0.14 us  append 0.76 us  tree 0.98 us/Kind  to_json 1.51 us/Kind  len 0.06 us  first 0.35 us
n=100000  create 7.50 us  lookup 0.14 us  append 0.84 us  tree 1.50 us/Kind  to_json 2.71 us/Kind  len 0.06 us  first 0.49 us
time_head over 1028 Kinds (28 dates): 262.2 us
```
</details>

How to read it:

- **Lookup** stays flat as n grows 100-fold: the O(1) average dictionary lookup.
- **Create** roughly doubles over that range: the O(log n) AVL insert, plus allocating the Kind and its two edge sets.
- **Append** and **`Kind.len`** stay near-constant; **`Kind.first`** grows with log n (the walk down the left spine).
- **`time_head`** pays for the 1 000 non-temporal names on every access, because it parses every name in the space. Keep temporal Kinds in their own `KindSpace` when you query them often.
