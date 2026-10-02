# Kind Architecture

## Introduction

The `kind` library is a Python framework for creating, manipulating, and reasoning about symbolic data structures. It is designed to be lightweight, extensible, and memory-aware, providing a powerful foundation for a wide range of applications, from data modeling and graph analysis to scheduling and metaprogramming.

At its core, the `kind` library is built upon a layered architecture that separates the fundamental `Kind` class from its extended functionalities. This design promotes modularity, reduces complexity, and allows for a high degree of customization through mixins and builtin extensions.

This document provides a detailed overview of the `kind` library's architecture, including its core components, builtin extensions, and the principles that guide its design.

## Core Architecture

The core architecture of the `kind` library is divided into two main layers: the **Core Layer** and the **Builtin Extensions Layer**.

```mermaid
graph TD
    subgraph "Kind Package"
        A[kind] --> B(kind.core)
        A --> C(kind.builtin)
    end

    subgraph "Core Layer (kind.core)"
        B --> B1[kind.core.base_kind]
        B --> B2[kind.core.kind]
        B --> B3[kind.core.graph_traversal]
        B --> B4[kind.core.maturing]
        B --> B5[kind.core.mixinability]
        B --> B6[kind.core.mixin_validator]
        B --> B7[kind.core.protocols]
        B --> B8[kind.core.relations]
        B --> B9[kind.core.time_arithmetics]
        B --> B10[kind.core.schedule]
        B --> B11[kind.core.batch_processing]
        B --> B12[kind.core.lazy_kind]
        B --> B13[kind.core.kind_namespace]
        B --> B14[kind.core.mixins]
    end

    subgraph "Builtin Extensions Layer (kind.builtin)"
        C --> C1[kind.builtin.collections]
        C --> C2[kind.builtin.time_dim]
        C --> C3[kind.builtin.index]
        C --> C4[kind.builtin.path]
        C --> C5[kind.builtin.visual]
        C --> C7[kind.builtin.avl_tree]
        C --> C8[kind.builtin.timeline]
    end

    B1 -- uses --> C7
    B2 -- uses --> B1
    B2 -- uses --> B3
    B2 -- uses --> B4
    B2 -- uses --> B5
    B2 -- uses --> B8
    B2 -- uses --> B12
    B2 -- uses --> B14
    B2 -- uses --> C1
    B2 -- uses --> C3

    B5 -- uses --> B6
    B8 -- uses --> C1
    B13 -- uses --> B2

    B10 -- uses --> B2

    C2 -- uses --> B2
    C3 -- uses --> B2
    C4 -- uses --> B2
    C4 -- uses --> B7
    C5 -- uses --> B2

    C3 -- uses --> C7

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;

    style B1 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B2 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B3 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B4 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B5 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B6 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B7 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B8 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B9 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B10 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B11 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B12 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B13 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;
    style B14 fill:#ADD8E6,stroke:#333,stroke-width:2px,color:#000000;

    style C1 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C2 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C3 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C4 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C5 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C7 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
    style C8 fill:#90EE90,stroke:#333,stroke-width:2px,color:#000000;
```

### Legend

*   **Yellow Boxes**: Core architectural components.
*   **Blue Boxes**: Core Layer modules.
*   **Green Boxes**: Builtin extension modules.
*   **Light Blue Boxes**: Modules within the `kind.core` layer.
*   **Light Green Boxes**: Modules within the `kind.builtin` layer.
*   Not shown: `kind/__init__.py` (exports `Kind`, `k`, `GraphTraversal`, batch and time helpers) and `kind.bin.scheduler` (the `kind-scheduler` CLI over `kind.core.schedule`).
*   **Arrows**: Indicate dependencies between modules.

### Core Layer (`kind.core`)

The Core Layer provides the fundamental building blocks of the `kind` library. It includes the `Kind` class itself, along with essential services for graph traversal, mixin-based extensibility, and memory management.

*   **`base_kind`**: Defines `BaseKind`, the interned, name-identified node: one weak pool for all classes (a Kind keeps its identity while something references it) and the creation-order index (an `AVLTree`).
*   **`kind`**: Extends the `base_kind` with advanced features such as graph traversal, indexing, relations, per-instance freezing, maturing, Mermaid/ASCII rendering and serialization.
*   **`graph_traversal`**: Provides `GraphTraversal(root, traverse_mode, family_mode)`, iterative DFS/BFS over a `Kind` graph.
*   **`relations`**: Holds a Kind's named relations (strong references) and the dynamic relation verbs (`a.has_kind(b)`).
*   **`lazy_kind`**: Defines `LazyKind` (deferred conversion to `Kind`) and the `SENTINEL` marker.
*   **`kind_namespace`**: Provides `k`, where `k.Stock is Kind('Stock')`.
*   **`mixins`**: Discovers the mixin classes available in `kind.builtin` and `kind.core` (used by `Kind.ls()` and `Kind.stat()`).
*   **`maturing`**: Implements the "maturing" process for `Kind` objects, which involves elevating metadata to first-class attributes and methods.
*   **`mixinability`**: Provides the core functionality for mixin-based extensibility of the `Kind` class (`register_mixin`, `apply_mixin_to_instance`, `lock_mixins`).
*   **`mixin_validator`**: Checks a mixin's signature (first parameter `self`); a mixin is trusted code, so it does not judge what the code does.
*   **`protocols`**: Defines the protocols that govern the behavior of `Kind` objects.
*   **`time_arithmetics`**: Provides functions for performing arithmetic operations on time-related objects.
*   **`schedule`**: Provides the core scheduling logic for the `kind` project.
*   **`batch_processing`**: Provides functions for processing batches of items asynchronously and synchronously.

### Builtin Extensions Layer (`kind.builtin`)

The Builtin Extensions Layer provides a collection of optional modules that extend the functionality of the `Kind` class. These modules are designed to be self-contained and can be used independently of one another.

*   **`collections`**: Provides custom collection classes for `Kind` objects, such as `OrderedKindSet`.
*   **`time_dim`**: Provides time dimension-related functionality for `Kind` objects.
*   **`index`**: Provides index capabilities for `Kind` objects.
*   **`path`**: Provides pathfinding capabilities for `Kind` objects.
*   **`visual`**: Provides Graphviz rendering (`to_dot`, `to_svg`, `to_png`, `a_to_svg`, `a_to_png`) and `from_mmd`, as mixins on every `Kind`; Mermaid and ASCII output belong to `Kind` itself.
*   **`avl_tree`**: An implementation of an AVL tree.
*   **`timeline`**: Provides a `Timeline` class for representing a series of time periods.
