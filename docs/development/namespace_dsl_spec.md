---
title: Kind DSL Core Library
author: Miklós Béky, Symbolic Systems Lab
tags: [DSL, Symbolic Computation, Graphs, Lazy Evaluation, Python]
---

## Overview

`kind.py` implements a **lazy, graph-oriented, immutable kind system** designed as a foundational primitive for domain-specific languages (DSLs), graph transformations, and semantic metadata modeling.

It supports symbolic interning, ordered chaining (`que`), DAG tree modeling (`tree`), and polymorphic cross-linking (`relate`), with efficient caching and memory-awareness.

## Motivation

- Avoid string duplication in symbolic identities
- Enable semantic modeling via structural relationships
- Design graph-based, introspectable DSLs
- Support polymorphic relationship tagging (`related_how`)
- Optimize evaluation lazily with O(1) reads and O(log n) inserts
- Track symbolic origin (`.origin`) and memory state

## Core Components

- `Kind`: atomic unit, uniquely interned string identity
- `KindNamespace`: attribute-based creation (e.g. `k.user`)
- `OrderedKindSet`: length-cached deduplicated set
- `GraphTraversal`: lazy, cycle-safe traversal abstraction
- `KindAdapter`: modular traversal and relation modeler

## Relations

- **que**: sequential (`next` / `prev`)
- **tree**: parent-child DAG
- **relate**: polymorphic, typed edge with `.related_how`

## Highlights

```python

from kind.core.kind_namespace import KindNamespace

k = KindNamespace()

k.page.append(k.header).append(k.footer)
k.backend.uses(k.database)

print(k.page.to_mmd())  # Mermaid.js format
```
<details>
<summary>Outcome</summary>

```text
graph TD
    page --> header
    page --> footer
```
</details>

## Render Pipelines

- `.to_mmd()` — Markdown/HTML embeddable [Mermaid](https://mermaid.js.org) output
- `.to_svg()` / `.to_png()` — Graphviz-based visualization (via `graphviz` Python binding)
- Requires optional extra: `kind[visual]`

## Installation

```bash
pip install kind
```
<details>

```text
Collecting kind
Installing collected packages
```
</details>

## Performance

- Kind lookup: **O(1)** (intern pool)
- Tree/graph linking: **O(1)**
- Cache-aware traversal: amortized **O(1)** after first pass
- Insert: **O(log n)** if using sorted/positional structure

## Memory Behavior

- Controlled origin retention (`Kind.origin`)
- GC-aware deletion (respecting `ENABLE_ORIGIN`, `MEMORY_AWARE_DELETE`)

## Extensibility

- `KindAdapter` plugins for new traversal topologies
- Async-ready traversal engine (planned)
- Frontend-ready output formats (Mermaid, SVG, PNG)

---
