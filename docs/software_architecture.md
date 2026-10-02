```mermaid
graph TD
    subgraph Core Infrastructure
        A[Kind Creation & Management] --> B{Kind Class};
        B --> C[BaseKind];
        B --> D[KindNamespace];
        C --> E[WeakValueDictionary for Pooling];
        C --> F[AVLTree for Numbered Kinds];
    end

    subgraph Relational System
        B --> G[relate/unrelate methods];
        G --> H{Relations: how maps to OrderedKindSet, strong refs};
        B --> I[Dynamic __getattr__ verbs, e.g. has_kind];
        I --> J{Relations Class (dict-like)};
        J --> G;
    end

    subgraph Advanced Features
        B --> L[Graph Traversal];
        B --> M[Lazy Loading & Maturing];
        B --> N[Mixinability];
        B --> O[Serialization (orjson)];
    end

    subgraph Built-in Mixins
        P[Builtin Mixins] --> N;
    end

    subgraph User Interaction
        D --> Q[User Code];
        Q --> B;
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#ccf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#9cf,stroke:#333,stroke-width:2px
    style F fill:#9cf,stroke:#333,stroke-width:2px
    style G fill:#f99,stroke:#333,stroke-width:2px
    style H fill:#f99,stroke:#333,stroke-width:2px
    style I fill:#9f9,stroke:#333,stroke-width:2px
    style J fill:#9f9,stroke:#333,stroke-width:2px
    style L fill:#cfc,stroke:#333,stroke-width:2px
    style M fill:#cfc,stroke:#333,stroke-width:2px
    style N fill:#cfc,stroke:#333,stroke-width:2px
    style O fill:#cfc,stroke:#333,stroke-width:2px
    style P fill:#cfc,stroke:#333,stroke-width:2px
    style Q fill:#fc9,stroke:#333,stroke-width:2px
```