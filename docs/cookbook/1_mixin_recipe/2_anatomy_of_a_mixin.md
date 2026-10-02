# [`«kind»`](https://github.com/ikko/kind) cookbook
**Recipes for Symbolic Mastery**

_Recipe 1: How to Create a Mixin?_

---

# 1.2 Anatomy of a Mixin: Structure and Protocols

Understanding the internal structure and expected protocols of a mixin is crucial for developing robust and well-integrated extensions within the `kind` framework. A mixin, at its core, is a Python class designed to be composed with `Kind` objects, providing additional behaviors or attributes.

## Core Components of a Mixin

While mixins can vary in complexity, they generally adhere to a common structure:

1.  **`self` is the Kind**: Once registered with `register_mixin`, a mixin's public methods are attached to the `Kind` class, so their first parameter, `self`, is the `Kind` instance itself. A mixin needs no `__init__` and keeps no reference to its `Kind`; per-Kind state belongs in the Kind (e.g. `self.metadata`). Private and dunder names are never registered.

    ```python
    class MyMixin:
        def describe(self) -> str:
            return f"{self.name} has {len(self.children)} children"
    ```

2.  **Methods**: These are the functionalities that the mixin contributes to the `Kind` object. Methods can be synchronous or asynchronous, following the `a_` prefix convention for asynchronous operations.

    ```python
    class MyMixin:
        # ...
        def sync_operation(self, data):
            # Synchronous logic
            return f"Processed {data} synchronously for {self.name}"

        async def a_async_operation(self, data):
            # Asynchronous logic
            await anyio.sleep(0.01) # Simulate async work
            return f"Processed {data} asynchronously for {self.name}"
    ```

3.  **Properties (Optional)**: Mixins can also expose properties that provide computed attributes or controlled access to internal state.

    ```python
    class MyMixin:
        # ...
        @property
        def mixin_status(self):
            # Return some status based on mixin's state
            return "Active"
    ```

## Protocols and Type Hinting

To ensure type safety and facilitate better code analysis, `kind` mixins often leverage Python's `typing.Protocol`. Protocols define the expected interface of a mixin, specifying the methods and attributes it *should* implement. This allows for static type checking and provides clear documentation of a mixin's capabilities without enforcing a rigid inheritance hierarchy.

For example, the `KindVisualProtocol` in `kind.core.protocols` defines the interface for mixins that provide visualization capabilities:

```python
from abc import abstractmethod
from typing import Protocol

class KindVisualProtocol(Protocol):
    @abstractmethod
    def to_dot(self, mode: str = "tree") -> str:
        ...

    @abstractmethod
    def to_svg(self, mode: str = "tree") -> str:
        ...

    @abstractmethod
    def to_png(self, mode: str = "tree") -> bytes:
        ...
```

Mermaid and ASCII rendering (`to_mmd()`, `to_ascii()`) are not part of this protocol: they are methods of `Kind` itself.

When implementing a mixin, it's highly recommended to declare that it adheres to a relevant protocol (if one exists), e.g. by implementing the protocol's methods with the same signatures. This provides a clear contract for how the mixin interacts with the `Kind` framework and other components.

## Mixin Validation

`register_mixin(value, name=None, target_class=None, safe=True, expand=True)` (from `kind.core.mixinability`) guards the core API rather than the code: strings are refused (nothing is evaluated), private and dunder names are always refused, names that already exist in the `Kind` API are refused unless `safe=False`, a previously registered mixin may be replaced, and after `lock_mixins()` nothing more can be registered in the process. For functions, `validate_mixin_callable` (from `kind.core.mixin_validator`, returning a `MixinValidationResult`) checks only the signature: the first parameter must be `self`. It does not detect unsafe code — a mixin is trusted code, like any method of the class.

By understanding these core components and adhering to established protocols, developers can create powerful, maintainable, and well-integrated mixins for the `kind` framework.
