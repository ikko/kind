# 1.3 Layered Architecture: Modularity and Extensibility

The `Kind` framework is designed with a **layered architecture**, a fundamental principle that separates concerns into distinct, hierarchical layers. This approach ensures a lean and stable core while allowing for flexible and modular extension of functionalities. The primary distinction is between the `kind.core` package, which houses the essential building blocks, and the `kind.builtin` package, which provides optional, high-level extensions.

## Core Layer (`kind.core`)

This layer represents the foundational elements of the `Kind` framework. It contains the absolute minimum necessary for a `Kind` object to exist and to participate in graph structures. Key characteristics include:

-   **Minimalism**: Focuses solely on the fundamental definition of a `Kind`, its unique identification (interning within a `KindSpace`), and the basic mechanisms for establishing and managing relationships (parents, children).
-   **Stability**: Designed to be highly stable and rarely change, providing a robust base for all other functionalities.
-   **Independence**: Ideally, this layer has minimal dependencies on higher-level components, ensuring its integrity and reusability.

```mermaid
graph TD
    A[kind.core] --> B[base_kind.py];
    A --> C[graph_traversal.py];
    A --> D[kind.py];
    A --> E[kind_namespace.py];
    A --> F[lazy_kind.py];
    A --> G[maturing.py];
    A --> H[mixin_validator.py];
    A --> I[mixinability.py];
    A --> J[protocols.py];
    A --> K[relations.py];
    A --> L[space.py];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style D fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style F fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style G fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style H fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style I fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style J fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style K fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style L fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
## Builtin Extensions Layer (`kind.builtin`)

This layer comprises a collection of modular extensions that provide specialized functionalities to `Kind` objects. These extensions are designed to be plug-and-play, allowing developers to include only the features relevant to their specific application without bloating the core.

-   **Modularity**: Each module within `kind.builtin` addresses a specific domain (e.g., collections, indexing, path finding, visualization).
-   **Extensibility**: New functionalities can be easily added by creating new modules in this layer, adhering to the framework's extension protocols.
-   **Controlled Dependencies**: While `kind.builtin` modules depend on `kind.core`, the `kind.core` generally remains independent of `kind.builtin`, maintaining the hierarchical integrity.

```mermaid
graph TD
    A[kind.builtin] --> B[avl_tree.py];
    A --> C[collections.py];
    A --> D[index.py];
    A --> E[path.py];
    A --> F[visual.py];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style E fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style F fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
```

## Opt-in Time Layer (`kind.time`)

Time is not part of what a Kind is, so the core does not load it. `import kind.time` attaches the time properties (`as_date`, `hour`, `period`, ...) and the time views (`time_head`, `time_tail`) to every Kind; without it a Kind has no time properties. The aliases `kind.td`, `kind.time_dim`, `kind.tl`, `kind.timeline` and `kind.time` resolve into this package and opt in the same way.

```mermaid
graph TD
    A[kind.time] --> B[__init__.py];
    A --> C[arithmetic.py];
    A --> D[dim.py];
    A --> E[timeline.py];

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style C fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style E fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
```

Scheduling is not part of `kind` either: it lives in the separate [`kind-scheduler`](../../../scheduler/README.md) distribution (package `kind_scheduler`), which depends on `kind`.

## Inter-Layer Communication

The `kind.core` package, particularly `kind.py`, integrates with selected `kind.builtin` modules to enhance its fundamental capabilities. For instance, `KindIndex` from `kind.builtin.index` is used within the `Kind` class to manage per-instance indexing, `OrderedKindSet` from `kind.builtin.collections` holds `children` and `parents`, and `AVLTree` from `kind.builtin.avl_tree` keeps the pooled Kinds in creation order. This controlled dependency allows the core to leverage specialized, well-encapsulated functionalities without compromising its lean design.

### Code Example: Core Leveraging Builtins

```python
# From kind/core/kind.py (abridged)
from kind.builtin.collections import OrderedKindSet
from kind.builtin.index import KindIndex
from kind.core.base_kind import BaseKind
from kind.core.lazy_kind import SENTINEL


class Kind(BaseKind):
    def _init_slots(self, name, origin):
        super()._init_slots(name, origin)
        object.__setattr__(self, 'parents', OrderedKindSet())
        object.__setattr__(self, 'children', OrderedKindSet())
        object.__setattr__(self, '_index', SENTINEL)
        # ... metadata, context and relations are created lazily as well

    @property
    def index(self) -> KindIndex:
        if self._index is SENTINEL:
            object.__setattr__(self, '_index', KindIndex(self))  # Core uses a builtin for indexing
        return self._index
```

### Industry Applications

**High-Tech: Microservices Architecture**
```python
from kind import k

# Core services
k.AuthService.provides(k.UserAuthentication)
k.DataStorageService.provides(k.DataPersistence)

# Specialized services (builtin)
k.PaymentProcessingService.uses(k.AuthService)
k.RecommendationEngine.uses(k.DataStorageService)

print(f"Payment service uses: {[c.name for c in k.PaymentProcessingService.children]}")
```
<details>
<summary>Outcome</summary>

```text
Payment service uses: []
```
</details>

**Low-Tech: Modular Furniture Design**
```python
from kind import k

# Core components
k.BasicFrame.connects_with(k.StandardConnector)

# Add-on modules (builtin)
k.ShelfModule.attaches_to(k.BasicFrame)
k.DrawerModule.attaches_to(k.BasicFrame)

print(f"Basic frame connections: {[c.name for c in k.BasicFrame.children]}")
```
<details>
<summary>Outcome</summary>

```text
Basic frame connections: []
```
</details>

## Conclusion

The layered architecture of the `Kind` framework is a testament to its robust and scalable design. By clearly separating core functionalities from modular extensions, it achieves a balance between minimalism and extensibility, making it adaptable to a wide array of complex symbolic data manipulation tasks while maintaining a clean and maintainable codebase.
