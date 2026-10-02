# [«kind»](https://github.com/ikko/kind/blob/master/README.md) info

## **A Framework for Symbolic Data Manipulation**

> `kind.py` — A Lazy, Graph-Oriented, Immutable Kind System Concept for Domain-Specific Abstraction

_Inspired by Ruby's [Symbol](https://ruby-doc.org/core-2.5.3/Symbol.html)._

## What is [«kind»](https://github.com/ikko/kind/blob/master/README.md)?

[**«kind»**](https://github.com/ikko/kind/blob/master/README.md) is a namespace DSL. It is a **Python Framework** for creating, manipulating, and analyzing complex, graph-based data structures. It provides a versatile `Kind` object that serves as a node in a dynamic, directed acyclic graph (DAG). The framework is designed to be lean, modular, and extensible, making it suitable for a wide range of applications, from data science and AI to domain-specific modeling.


## Core Concepts

-   **[Kind](topics/1_kind_fundamental_building_block/index.md)**: The fundamental building block. Each kind has a unique name and can be connected to other kinds, forming complex relationships.
-   **[Kind vs type](topics/1_kind_fundamental_building_block/kind_vs_type.md)**: What a Kind shares with a type, where it differs, and why it is not a Haskell kind.
-   **[Flyweight Design](topics/2_flyweight_design/index.md)**: Kinds are unique. `Kind('a')` returns the same object as long as something references it (the pool is weak), saving memory and ensuring consistency.
-   **[Layered Architecture](topics/3_layered_architecture/index.md)**: The core is minimal. Functionality is added through modular, "builtin" extensions for features like date/time handling, advanced collections, and visualization.
-   **[Per-Instance Indexing](topics/4_per_instance_indexing/index.md)**: Every kind has its own private, weighted index of other kinds, allowing for the creation of sophisticated, nested data structures.
-   **[Mixinability](topics/5_mixinability/index.md)**: The framework supports dynamic extension of `Kind` instances at runtime through mixins; a mixin is trusted code, and registration only checks its signature and refuses to replace core names.
-   **[Memory-Aware Maturing](topics/6_memory_aware_maturing/index.md)**: Kinds can be "matured" to optimize memory usage and performance by elevating metadata and removing unused components.
-   **[WIP: Scheduling](topics/7_scheduling/index.md)**: A built-in scheduler allows for deferred execution of functions and methods, specified with cron-like strings, datetime objects, or even other Kinds.


Getting Started
---------------
To begin, simply import the `Kind` or `k` namespace factory:

```python
from kind import Kind, k

# Create kinds
hello = Kind('hello')
world = k.world

# Build relationships
hello.add(world)

# Traverse the graph
print(hello.tree())
print(hello.to_ascii())
```
<details>
<summary>Outcome</summary>

```text
[Kind('hello'), Kind('world')]
- hello
  - world
```
</details>

Running Tests
-------------
To run all tests, execute the following command from the project root directory:

```bash
python -m pytest tests
```


API Highlights
--------------
- **[Kind(name: str)](topics/8_api_highlights/index.md#kindname-str-globally-interned-idempotent-constructor)** — globally interned, idempotent constructor
- **[Kind.next()](topics/8_api_highlights/index.md#kindnext-creates-and-chains-auto-numbered-kinds)** — creates and chains auto-numbered kind (`kind_0`, `kind_1`, …)
- **[kind.append(child) / kind.relate(other, how)](topics/8_api_highlights/index.md#kindappendchild-and-dynamic-relations-link-construction)** — link construction
- **[kind.tree() / .graph()](topics/8_api_highlights/index.md#kindtree--kindgraph--graphtraversal-traversal)** — traversal: children only / children, parents and relations
- **[kind.patch(other)](topics/8_api_highlights/index.md#kindpatchother-structural-merge-of-another-kinds-links)** — merges another Kind's origin (if unset), children, parents and relations (PATCH-like semantics)
- **[kind.to_mmd()](topics/8_api_highlights/index.md#kindto_mmd-outputs-the-graph-in-mermaid-diagram-syntax)** — outputs the graph in Mermaid diagram syntax
- **[kind.to_ascii()](topics/8_api_highlights/index.md#kindto_ascii-outputs-ascii-representation-of-graphs)** — outputs ASCII art representation of graphs
- **[kind.delete()](topics/8_api_highlights/index.md#kinddelete-removes-node-and-its-inverse-references)** — removes node and its inverse references (parents/children)
- **[kind.elevate()](topics/8_api_highlights/index.md#kindelevate-promotes-metadata-to-instance-attributesmethods)** — promotes metadata to instance attributes/methods
- **[kind.slim()](topics/8_api_highlights/index.md#kindslim-drops-elevated-attributes-that-hold-no-value)** — drops elevated attributes that hold no value (`SENTINEL`)
- **[kind.immute()](topics/8_api_highlights/index.md#kindimmute-orchestrates-maturing-process-elevate-slim-freeze)** — orchestrates maturing process (elevate, slim, freeze)
- **[kind.ref](topics/8_api_highlights/index.md#kindref-alias-for-kindorigin-to-track-source-provenance)** — alias for `kind.origin` to track source provenance
- **[Scheduler.add_job(job)](topics/8_api_highlights/index.md#scheduleradd_jobjob-schedules-a-new-job-for-execution)** — schedules a new job for execution

Performance
-----------
For detailed performance analysis and empirical validation of Big O notations, refer to the [Performance Notations and Empirical Validation](development/notations.md) document.

- O(1) kind instantiation (intern pool)
- O(1) relationship linking
- O(V+E) traversal (`tree()`, `graph()`, `to_ascii()`)
- O(log n) creation-order insert/search (`Kind.seek()`, `Kind.each()`) via an AVL tree over float positions

Memory Awareness
----------------
-   **[Memory Awareness](topics/10_memory_awareness/index.md)**: the intern pool is weak — a Kind lives while something references it (children and relations hold strong references)
-   Lazily created `metadata`, `context`, `index` and `relations`; `clear_context()` empties the context

Extensibility:
-------------
- Easily extended with async traversal, typed relations, or backend persistence
- `typing.Protocol` contracts for mixins (`kind.core.protocols`)
- `register_mixin()` (every Kind) and `apply_mixin_to_instance()` (one Kind)
- Compatible with enum reflection and external DSL inputs

Example Use
-----------
- **[Practical Applications](topics/12_example_use/index.md)**: Demonstrates how Kind's core features can be leveraged to solve real-world problems.

Conclusion
----------
- **[Overview](topics/13_conclusion/index.md)**: This module provides a high-performance, semantically rich, thread-safe kind abstraction to power DSLs, runtime graphs, knowledge trees, and dynamic semantic layers. The design emphasizes structural clarity, cache efficiency, and symbolic extensibility.

---
