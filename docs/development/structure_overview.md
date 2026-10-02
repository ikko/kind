## Project Structure

The project is organized into two main packages:

-   `kind.core`: Contains the essential `Kind` class, graph traversal, relations, mixin registry, maturing and scheduling logic.
-   `kind.builtin`: Provides high-level extensions for collections, date/time operations, index, pathfinding, timelines and Graphviz visualization.

```mermaid
graph LR
    A[User Application] --> B(kind)
    B --> C{kind.core}
    B --> D{kind.builtin}
    C --> E[kind.core.kind]
    C --> F[kind.core.graph_traversal]
    C --> G[kind.core.schedule]
    D --> H[kind.builtin.time_dim]
    D --> I[kind.builtin.collections]
    D --> J[kind.builtin.index]
    D --> K[kind.builtin.path]
    D --> L[kind.builtin.visual]
    D --> M[kind.builtin.timeline]
    
    style A fill:#007BFF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style B fill:#228B22,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#800080,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style E fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style F fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style G fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style H fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style I fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style J fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style K fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style L fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style M fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
```

## Software Architecture

```mermaid
graph LR
    subgraph "Kind Package"
        A[kind] --> B(kind.core)
        A --> C(kind.builtin)
    end
    style A fill:#228B22,stroke:#333,stroke-width:2px,color:#FFFFFF;

    subgraph "Core Modules"
        B --> B1[kind.core.kind]
        B --> B2[kind.core.base_kind]
        B --> B10[kind.core.graph_traversal]
        B --> B11[kind.core.relations]
        B --> B3[kind.core.maturing]
        B --> B4[kind.core.mixinability]
        B --> B5[kind.core.mixin_validator]
        B --> B6[kind.core.protocols]
        B --> B8[kind.core.time_arithmetics]
        B --> B9[kind.core.schedule]
    end
    style B fill:#FF8C00,stroke:#333,stroke-width:2px,color:#000000;

    subgraph "Builtin Extensions"
        C --> C1[kind.builtin.collections]
        C --> C2[kind.builtin.time_dim]
        C --> C3[kind.builtin.index]
        C --> C4[kind.builtin.path]
        C --> C5[kind.builtin.visual]
        C --> C7[kind.builtin.avl_tree]
        C --> C8[kind.builtin.timeline]
    end
    style C fill:#800080,stroke:#333,stroke-width:2px,color:#FFFFFF;

    B1 -- uses --> B2
    B1 -- uses --> B10
    B1 -- uses --> B11
    B1 -- uses --> B3
    B1 -- uses --> B4
    B1 -- uses --> C1
    B1 -- uses --> C3
    B2 -- uses --> C7
    B4 -- uses --> B5
    B11 -- uses --> C1
    B9 -- uses --> B1
    C2 -- uses --> B1
    C3 -- uses --> B1
    C4 -- uses --> B1
    C4 -- uses --> B6
    C5 -- uses --> B1
    C3 -- uses --> C7

    style B1 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B2 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B10 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B11 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B3 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B4 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B5 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B6 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B8 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;
    style B9 fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000000;

    style C1 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C2 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C3 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C4 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C5 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C7 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style C8 fill:#9370DB,stroke:#333,stroke-width:2px,color:#FFFFFF;
```
