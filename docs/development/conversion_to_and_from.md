# Bidirectional Type Conversion in Kind

This document outlines the mechanisms for converting standard Python types to `Kind` objects and vice-versa, enhancing the framework's interoperability and ease of use.

## Concept

The `Kind` framework provides a seamless way to represent native Python data structures as `Kind` objects, allowing them to participate in the graph-based data model. This is achieved through:

1.  **`Kind.from_<type>` Class Methods**: Factory methods on the `Kind` class that convert a given Python object into a `Kind` instance. These methods handle the creation of the `Kind`'s name and the assignment of the original Python object to the `Kind`'s `origin` attribute.
2.  **`to_kind()` Global Function**: A generic function that dispatches to the appropriate `Kind.from_<type>` method based on the input object's type. This provides a unified interface for converting various Python objects to `Kind` instances.

## Supported Types and Examples

The following standard Python types are supported for bidirectional conversion:

### Primitive Types

-   **`int`**
    ```python
    from kind import Kind, to_kind

    # Using from_int
    s_int = Kind.from_int(123)
    print(f"Kind from int: {s_int.name}, Origin: {s_int.origin}") # Output: Kind from int: 123, Origin: 123

    # Using to_kind
    s_int_2 = to_kind(456)
    print(f"Kind from int (to_kind): {s_int_2.name}, Origin: {s_int_2.origin}") # Output: Kind from int (to_kind): 456, Origin: 456
    ```

-   **`float`**
    ```python
    from kind import Kind, to_kind

    # Using from_float
    s_float = Kind.from_float(123.45)
    print(f"Kind from float: {s_float.name}, Origin: {s_float.origin}") # Output: Kind from float: 123.45, Origin: 123.45

    # Using to_kind
    s_float_2 = to_kind(789.01)
    print(f"Kind from float (to_kind): {s_float_2.name}, Origin: {s_float_2.origin}") # Output: Kind from float (to_kind): 789.01, Origin: 789.01
    ```

-   **`str`**
    ```python
    from kind import Kind, to_kind

    # Using from_str
    s_str = Kind.from_str("hello")
    print(f"Kind from str: {s_str.name}, Origin: {s_str.origin}") # Output: Kind from str: hello, Origin: hello

    # Using to_kind
    s_str_2 = to_kind("world")
    print(f"Kind from str (to_kind): {s_str_2.name}, Origin: {s_str_2.origin}") # Output: Kind from str (to_kind): world, Origin: world
    ```

-   **`bool`**
    ```python
    from kind import Kind, to_kind

    # Using from_bool
    s_bool = Kind.from_bool(True)
    print(f"Kind from bool: {s_bool.name}, Origin: {s_bool.origin}") # Output: Kind from bool: True, Origin: True

    # Using to_kind
    s_bool_2 = to_kind(False)
    print(f"Kind from bool (to_kind): {s_bool_2.name}, Origin: {s_bool_2.origin}") # Output: Kind from bool (to_kind): False, Origin: False
    ```

-   **`None`**
    ```python
    from kind import Kind, to_kind

    # Using from_none
    s_none = Kind.from_none(None)
    print(f"Kind from None: {s_none.name}, Origin: {s_none.origin}") # Output: Kind from None: None, Origin: None

    # Using to_kind
    s_none_2 = to_kind(None)
    print(f"Kind from None (to_kind): {s_none_2.name}, Origin: {s_none_2.origin}") # Output: Kind from None (to_kind): None, Origin: None
    ```

### Collection Types

-   **`list`**
    ```python
    from kind import Kind, to_kind

    my_list = [1, "two", True]
    s_list = Kind.from_list(my_list)
    print(f"Kind from list: {s_list.name}, Origin: {s_list.origin}") # Output: Kind from list: list, Origin: [1, 'two', True]
    print(f"Children: {[c.name for c in s_list.children]}") # Output: Children: ['1', 'two', 'True']

    s_list_2 = to_kind([4, "five", False])
    print(f"Kind from list (to_kind): {s_list_2.name}, Origin: {s_list_2.origin}") # Output: Kind from list (to_kind): list, Origin: [4, 'five', False]
    print(f"Children: {[c.name for c in s_list_2.children]}") # Output: Children: ['4', 'five', 'False']
    ```

-   **`dict`**
    ```python
    from kind import Kind, to_kind

    my_dict = {"a": 1, "b": "two"}
    s_dict = Kind.from_dict(my_dict)
    print(f"Kind from dict: {s_dict.name}, Origin: {s_dict.origin}") # Output: Kind from dict: dict, Origin: {'a': 1, 'b': 'two'}
    print(f"Children: {[c.name for c in s_dict.children]}") # Output: Children: ['a', 'b']

    s_dict_2 = to_kind({"x": 10, "y": "twenty"})
    print(f"Kind from dict (to_kind): {s_dict_2.name}, Origin: {s_dict_2.origin}") # Output: Kind from dict (to_kind): dict, Origin: {'x': 10, 'y': 'twenty'}
    print(f"Children: {[c.name for c in s_dict_2.children]}") # Output: Children: ['x', 'y']
    ```

-   **`tuple`**
    ```python
    from kind import Kind, to_kind

    my_tuple = (1, "two", True)
    s_tuple = Kind.from_tuple(my_tuple)
    print(f"Kind from tuple: {s_tuple.name}, Origin: {s_tuple.origin}") # Output: Kind from tuple: tuple, Origin: (1, 'two', True)
    print(f"Children: {[c.name for c in s_tuple.children]}") # Output: Children: ['1', 'two', 'True']

    s_tuple_2 = to_kind((4, "five", False))
    print(f"Kind from tuple (to_kind): {s_tuple_2.name}, Origin: {s_tuple_2.origin}") # Output: Kind from tuple (to_kind): tuple, Origin: (4, 'five', False)
    print(f"Children: {[c.name for c in s_tuple_2.children]}") # Output: Children: ['4', 'five', 'False']
    ```

-   **`set`**
    ```python
    from kind import Kind, to_kind

    my_set = {"one_val", "two_val", "true_val"}
    s_set = Kind.from_set(my_set)
    print(f"Kind from set: {s_set.name}, Origin: {s_set.origin}") # Output: Kind from set: set, Origin: {'one_val', 'two_val', 'true_val'}
    print(f"Children: {[c.name for c in s_set.children]}") # Output: Children: ['one_val', 'two_val', 'true_val'] (order may vary)

    s_set_2 = to_kind({"four_val", "five_val", "false_val"})
    print(f"Kind from set (to_kind): {s_set_2.name}, Origin: {s_set_2.origin}") # Output: Kind from set (to_kind): set, Origin: {'four_val', 'five_val', 'false_val'}
    print(f"Children: {[c.name for c in s_set_2.children]}") # Output: Children: ['four_val', 'five_val', 'false_val'] (order may vary)
    ```

### Nested Conversions

The `to_kind()` function and `Kind.from_<type>` methods handle nested data structures recursively, ensuring that all elements are converted into `Kind` instances and their `origin` attributes are correctly preserved.

```python
from kind import Kind, to_kind

nested_data = {"a": [1, {"b": True}], "c": (None,)}
s = to_kind(nested_data)

print(f"Top-level Kind: {s.name}, Origin: {s.origin}")
# Expected Output:
# Top-level Kind: dict, Origin: {'a': [1, {'b': True}], 'c': (None,)}

# Accessing nested Kinds
key_a = next(c for c in s.children if c.name == "a")
list_kind = key_a.children[0]
print(f"List Kind: {list_kind.name}, Origin: {list_kind.origin}")
# Expected Output:
# List Kind: list, Origin: [1, {'b': True}]

nested_dict_kind = list_kind.children[1]
print(f"Nested Dict Kind: {nested_dict_kind.name}, Origin: {nested_dict_kind.origin}")
# Expected Output:
# Nested Dict Kind: dict, Origin: {'b': True}

key_b = next(c for c in nested_dict_kind.children if c.name == "b")
print(f"Boolean Kind: {key_b.children[0].name}, Origin: {key_b.children[0].origin}")
# Expected Output:
# Boolean Kind: True, Origin: True
```
