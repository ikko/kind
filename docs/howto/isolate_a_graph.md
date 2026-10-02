# Isolate a graph in its own space

A [`KindSpace`](../reference/api.md#kindspace) is a separate universe of names. Inside `with KindSpace():` every `Kind(name)` is looked up in that space's pool, so a name used inside is unrelated to the same name outside. Leaving the block closes the space: it drops its references to its Kinds in O(n), and Kinds still referenced elsewhere stay readable but refuse every change.

Use a space for a scenario, a request, a test or a parse of foreign input. Code that never opens a space works in the process's default space.

## Same name, different Kind

```python
from kind import Kind, KindSpace, current_space

outer = Kind('Stock')
with KindSpace(name='scenario') as space:
    inner = Kind('Stock')
    inner.append(Kind('Bond'))
    print(inner is outer, inner == outer)   # equality is name AND space
    print(inner.space is space, current_space() is space)
print(current_space() is outer.space)
```
<details>
<summary>Outcome</summary>

```text
False False
True True
True
```
</details>

`Kind.len()`, `first()`, `last()`, `seek()`, `each()`, `next()`, `forget()` and `ps()` act on the current space.

## Edges stay inside one space

An edge or relation between Kinds of two spaces raises [`SpaceError`](../reference/errors.md#spaceerror): a cross-space edge would make the lifetime of one space depend on the other.

```python
from kind import Kind, KindSpace, SpaceError

outer = Kind('Ledger')
with KindSpace(name='scenario'):
    try:
        Kind('Entry').append(outer)
    except SpaceError as error:
        print(error)
```
<details>
<summary>Outcome</summary>

```text
Cannot link 'Entry' in KindSpace('scenario', 1 kinds) to 'Ledger' in KindSpace('default', 1 kinds): an edge across spaces would make their lifetimes undefined. Hint: create both inside the same `with KindSpace():` block.
```
</details>

## A closed space is read-only

Closing clears the pool and the creation order. A Kind you kept a reference to still answers reads; any change raises `SpaceError`, and so do creating a Kind in it and entering it again.

```python
from kind import Kind, KindSpace, SpaceError

with KindSpace(name='scenario') as space:
    kept = Kind('Stock')
    kept.append(Kind('Bond'))

print(space, [child.name for child in kept.children])
try:
    kept.append(Kind('Cash'))
except SpaceError as error:
    print(error)
try:
    with space:
        pass
except SpaceError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
KindSpace('scenario', closed) ['Bond']
Kind 'Stock' belongs to a closed space; it can be read but not changed.
KindSpace('scenario', closed) is closed and cannot be entered again. Hint: open a new KindSpace().
```
</details>

The default space cannot be closed; remove its Kinds with [`Kind.forget`](../reference/api.md#kindforget) or [`Kind.delete`](../reference/api.md#kinddelete).

```python
from kind.core.space import DEFAULT_SPACE, SpaceError

try:
    DEFAULT_SPACE.close()
except SpaceError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
The default space cannot be closed; use Kind.forget() or a KindSpace of your own.
```
</details>

## Which code sees which space

The current space is a context variable. asyncio and trio tasks, and anyio worker threads, inherit it; a plain `threading.Thread` starts in the default space. See [threads and async](threads_and_async.md).
