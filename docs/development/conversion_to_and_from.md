# Bidirectional Type Conversion in Kind

This document outlines the mechanisms for converting standard Python types to `Kind` objects and vice-versa, enhancing the framework's interoperability and ease of use.

## Concept

The `Kind` framework provides a seamless way to represent native Python data structures as `Kind` objects, allowing them to participate in the graph-based data model. This is achieved through:

1.  **`Kind.from_object(obj)`**: One class method converts any supported value into a `Kind` instance and records the original value as the `Kind`'s `origin` (the first non-None origin given wins). There are no per-type factories (`from_int`, `from_list`, ...).
2.  **`to_kind(obj)`** (in `kind.core.kind`): A function form of `Kind.from_object`.
3.  **`kind.to(target_type)`**: The way back: parses the Kind's name into a value of `target_type`.

The rule is the same as for any name: equal content means the same (interned) Kind.

## Supported Types and Examples

### Scalars: `int`, `float`, `str`, `bool`, `None`

A scalar becomes the Kind of its text.

```python
from kind import Kind
from kind.core.kind import to_kind

for value in (123, 123.45, "hello", True, None):
    kind = Kind.from_object(value)
    print(f"{kind.name!r}, origin: {kind.origin!r}")
# '123', origin: 123
# '123.45', origin: 123.45
# 'hello', origin: 'hello'
# 'True', origin: True
# 'None', origin: None

print(to_kind(456) is Kind('456'))  # True
print(Kind('123').to(int))          # 123
```

### Containers: `list`, `tuple`, `set`, `dict`

A container becomes the Kind named by its content, with its items as children and a `has_kind` relation to `Kind('list')` (or `tuple`, `set`, `dict`). A dict's values hang under their keys.

```python
from kind import Kind

for value in ([1, "two", True], (1, "two", True), {"one_val", "two_val"}, {"x": 10, "y": "twenty"}):
    kind = Kind.from_object(value)
    print(f"{kind.name!r}, children: {[c.name for c in kind.children]}, "
          f"has_kind: {[k.name for k in kind.relations.get('has_kind')]}")
# "[1, 'two', True]", children: ['1', 'two', 'True'], has_kind: ['list']
# "(1, 'two', True)", children: ['1', 'two', 'True'], has_kind: ['tuple']
# "set({'one_val', 'two_val'})", children: ['one_val', 'two_val'], has_kind: ['set']
# "{'x': 10, 'y': 'twenty'}", children: ['x', 'y'], has_kind: ['dict']

print(Kind.from_object([1, 2]).to(list))  # [1, 2]
```

### Nested Conversions

`Kind.from_object` converts nested data recursively; every container keeps its value as `origin`.

```python
from kind import Kind

s = Kind.from_object({"a": [1, {"b": True}], "c": (None,)})
print(s.name)
# {'a': [1, {'b': True}], 'c': (None,)}

key_a = s.children[0]
list_kind = key_a.children[0]
print(f"List Kind: {list_kind.name}, Origin: {list_kind.origin}")
# List Kind: [1, {'b': True}], Origin: [1, {'b': True}]

nested_dict_kind = list_kind.children[1]
key_b = nested_dict_kind.children[0]
print(f"Boolean Kind: {key_b.children[0].name}, Origin: {key_b.children[0].origin}")
# Boolean Kind: True, Origin: True
```

Because names are interned, a key such as `Kind('a')` is shared by every dict that has the key `'a'`, and so are the values hung under it.
