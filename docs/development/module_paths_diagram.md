# Module Import Paths

This diagram illustrates the most direct import paths to each accessible module in the `kind` library. It provides a clear overview of the library's public API and how its various components can be accessed.

```mermaid
graph TD
    subgraph "Public API"
        A[kind] --> B(kind.s)
        A --> C(kind.Kind)
        A --> D(kind.to_kind)
        A --> E(kind.KindNamespace)
    end

    subgraph "Core Modules"
        C --> F(kind.core.base_kind)
        C --> G(kind.core.kind)
        C --> I(kind.core.maturing)
        C --> J(kind.core.mixinability)
        C --> K(kind.core.mixin_validator)
        C --> L(kind.core.protocols)
        C --> M(kind.core.kindable)
        C --> N(kind.core.time_arithmetics)
        C --> O(kind.core.schedule)
        C --> P(kind.core.batch_processing)
    end

    subgraph "Builtin Extensions"
        C --> Q(kind.builtins.collections)
        C --> R(kind.builtins.time_dim)
        C --> S(kind.builtins.index)
        C --> T(kind.builtins.path)
        C --> U(kind.builtins.visual)
        C --> V(kind.builtins.red_black_tree)
        C --> W(kind.builtins.avl_tree)
        C --> X(kind.builtins.timeline)
    end

    style A fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style B fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style C fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style D fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;
    style E fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000;

    style F fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style G fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style I fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style J fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style K fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style L fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style M fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style N fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style O fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;
    style P fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF;

    style Q fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style R fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style S fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style T fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style U fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style V fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style W fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
    style X fill:#32CD32,stroke:#333,stroke-width:2px,color:#000000;
