# Take names from untrusted input

Every distinct name creates a Kind that stays in its space until it is deleted, so memory grows with the number of names an input can mention. Bound it with `KindSpace(max_kinds=N)`: creating the (N+1)th Kind raises [`KindLimitError`](../reference/errors.md#kindlimiterror). Parse foreign input inside its own capped space, and keep what you accept by name, not by edges: an edge across spaces is refused.

## Cap the space

```python
import json
from kind import Kind, KindSpace, KindLimitError

payload = json.dumps([{"name": f"n{i}", "children": [], "relations": {}} for i in range(5)])
with KindSpace(max_kinds=3, name='inbox') as inbox:
    try:
        Kind.from_json(payload)
    except KindLimitError as error:
        print(error)
    print(len(inbox), [kind.name for kind in inbox])
```
<details>
<summary>Outcome</summary>

```text
Cannot create 'n3': KindSpace('inbox', 3 kinds) already holds max_kinds=3 Kinds. Hint: delete() or Kind.forget() Kinds you no longer need, or raise the space's max_kinds.
3 ['n0', 'n1', 'n2']
```
</details>

A refused parse is not rolled back: the Kinds created before the limit stay. Inside a dedicated space this does not matter, because closing the space drops them all.

## Parsing merges by name

`from_json`, `from_yaml`, `from_toml`, `from_ascii` and `from_mmd` intern names: a node named like an existing Kind of the current space extends that Kind (new children, new relations) instead of creating a separate one. Parsed into your working space, an input can therefore attach edges to Kinds you already have.

```python
from kind import Kind, KindSpace

with KindSpace(name='work'):
    Kind('Account').append(Kind('Owner'))
    root = Kind.from_json('[{"name": "Account", "children": ["Attacker"], "relations": {}},'
                          ' {"name": "Attacker", "children": [], "relations": {}}]')
    print(root is Kind('Account'), [child.name for child in root.children])
```
<details>
<summary>Outcome</summary>

```text
True ['Owner', 'Attacker']
```
</details>

## Malformed input

`from_json`, `from_yaml` and `from_toml` check the shape of every node before creating any Kind, and raise [`ValueError`](../reference/errors.md#valueerror) for a node that is not `{'name': str, 'children': [str], 'relations': {how: [str]}}`.

| input | exception |
|---|---|
| empty list | [`ValueError`](../reference/errors.md#valueerror) `No kinds found in the JSON input.` |
| a node without `"name"`, a non-string name, `children` that is not a list of strings | [`ValueError`](../reference/errors.md#valueerror) `JSON node 0 is not {...}: ... Hint: produce it with to_json().` |
| text that is not JSON | `orjson.JSONDecodeError` (a `ValueError`) |

```python
from kind import Kind, KindSpace

with KindSpace(name='inbox'):
    try:
        Kind.from_json('[{"name": 5}]')
    except ValueError as error:
        print(error)
```
<details>
<summary>Outcome</summary>

```text
JSON node 0 is not {'name': str, 'children': [str], 'relations': {how: [str]}}: {'name': 5}. Hint: produce it with to_json().
```
</details>

## Recipe

1. Open `with KindSpace(max_kinds=N, name=...)` per input.
2. Parse; catch `KindLimitError` and `ValueError` (which includes `orjson.JSONDecodeError`). A parse stopped by `KindLimitError` is not rolled back, so parse into a fresh space and discard it on error.
3. Read what you need (names, children, relations) and rebuild it in your working space with `Kind(name)`; closing the input space drops the rest.

Mixins are never loaded from input: [`register_mixin`](../reference/api.md#register_mixin) refuses strings. Schedule files are code references, so `kind-scheduler` resolves functions only from an allowlist of modules: see [kind-scheduler](../../scheduler/README.md).
