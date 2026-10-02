# Serialize a graph

Every format writes the **connected component** of a Kind (everything reachable over children, parents and relations, in either direction) as names, child edges and forward relations. Nothing else of a Kind survives a round trip. Reading interns names into the current space, so it merges into Kinds that already exist there.

## What each format keeps

| | JSON / YAML / TOML | ASCII | Mermaid |
|---|---|---|---|
| names | yes | yes | yes |
| child edges | yes, in insertion order | yes, children sorted by name | yes, in insertion order |
| forward relations (`how`) | yes, re-sorted by target name | yes, sorted | yes, sorted by target name |
| `node_shape` | no | no | yes |
| `origin`, `metadata`, `context`, elevated attributes | no | no | no |
| frozen state | no | no | no |
| `Kind.next()` chain, creation order | no | no | no |
| Kinds not connected to the root | no | no | no |

Writers: [`to_json`](../reference/api.md#kindto_json), [`to_yaml`](../reference/api.md#kindto_yaml), [`to_toml`](../reference/api.md#kindto_toml), [`to_ascii`](../reference/api.md#kindto_ascii), [`to_mmd`](../reference/api.md#kindto_mmd). Readers: the matching `Kind.from_*` classmethods and [`from_mmd`](../reference/api.md#from_mmd) (in `kind.builtin.visual`, also a mixin on every Kind).

```python
from kind import Kind, KindSpace

with KindSpace(name='source'):
    store = Kind('Store', origin={'id': 7})
    store.metadata['region'] = 'EU'
    store.node_shape = 'round'
    store.append(Kind('Shelf'))
    store.append(Kind('Aisle'))
    store.relate(Kind('Supplier'), how='buys_from')
    store.relate(Kind('Bank'), how='buys_from')
    store.freeze()
    text = store.to_json()

with KindSpace(name='copy'):
    copy = Kind.from_json(text)
    print([child.name for child in copy.children])
    print([kind.name for kind in copy.relations.get('buys_from')])
    print(copy.origin, dict(copy.metadata), copy.node_shape, copy.frozen)
```
<details>
<summary>Outcome</summary>

```text
['Shelf', 'Aisle']
['Bank', 'Supplier']
None {} None False
```
</details>

Store what the table drops yourself, keyed by name, next to the graph text.

## ASCII: an exact round trip of depth-first output

`to_ascii()` draws `- name` for a child and `^ name` for a parent, expands each Kind once, and lists relations after `--- Relations ---`. [`Kind.from_ascii`](../reference/api.md#kindfrom_ascii) reads depth-first output (the default) back so that writing it again gives the same text. Breadth-first output interleaves branches and is for display only.

```python
from kind import Kind, KindSpace

with KindSpace(name='source'):
    root = Kind('Store')
    root.append(Kind('Shelf')).append(Kind('Item'))
    root.append(Kind('Aisle'))
    root.relate(Kind('Bank'), how='pays')
    text = root.to_ascii()
print(text)

with KindSpace(name='copy'):
    print(Kind.from_ascii(text).to_ascii() == text)
```
<details>
<summary>Outcome</summary>

```text
- Store
  - Aisle
  - Shelf
    - Item

--- Relations ---
Store --pays--> Bank
True
```
</details>

## Mermaid keeps shapes

```python
from kind import Kind, KindSpace
from kind.builtin.visual import from_mmd

with KindSpace(name='source'):
    root = Kind('API')
    root.node_shape = 'round'
    root.append(Kind('Database'))
    text = root.to_mmd()
print(text)

with KindSpace(name='copy'):
    print(from_mmd(text).node_shape)
```
<details>
<summary>Outcome</summary>

```text
graph LR
API(API)
Database[Database]
    API --> Database
round
```
</details>

## Reading merges by name

A node whose name already exists in the current space extends that Kind; read into a fresh space when that is not what you want. An empty document raises [`ValueError`](../reference/errors.md#valueerror):

```python
from kind import Kind

try:
    Kind.from_yaml('')
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
No kinds found in the YAML input.
```
</details>

For input you do not control, see [untrusted input](untrusted_input.md).

## Values to Kinds and back

[`Kind.from_object`](../reference/api.md#kindfrom_object) (and `to_kind` in `kind.core.kind`) turns a value into a Kind: a scalar becomes the Kind of its text, a container the Kind of its canonical text (dict keys and set members sorted, recursively) with its items as children and a `has_kind` relation to `Kind('list')`, `Kind('tuple')`, `Kind('set')` or `Kind('dict')`. Equal values are one Kind. The value is kept as `origin` (first non-`None` origin wins). [`Kind.to`](../reference/api.md#kindto) reads the name back as JSON, else as a Python literal (`ast.literal_eval`, no code evaluated), so `'True'`, `'None'` and `"{'a': 1}"` convert back too.

```python
from kind import Kind

kind = Kind.from_object({'b': 2, 'a': 1})
print(kind.name, kind is Kind.from_object({'a': 1, 'b': 2}))
print([child.name for child in kind.children], [k.name for k in kind.relations.get('has_kind')])
print(Kind.from_object([1, 2]).to(list), Kind('123').to(int), kind.to(dict), Kind.from_object(None).to(type(None)))
try:
    Kind('Store').to(int)
except TypeError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
{'a': 1, 'b': 2} True
['b', 'a'] ['dict']
[1, 2] 123 {'a': 1, 'b': 2} None
Cannot convert Kind 'Store' to int: the name is neither JSON nor a Python literal.
```
</details>

A dict's values hang under their keys, and keys are ordinary Kinds of the space: `Kind('a')` collects the values of every converted dict that has the key `'a'`. The children keep the dict's insertion order; only the name is canonical.
