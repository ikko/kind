---
title: Kind DSL Core Library
author: Miklós Béky, Symbolic Systems Lab
tags: [DSL, Symbolic Computation, Graphs, Lazy Evaluation, Python]
---

## Overview

`kind.py` implements a **lazy, graph-oriented, freezable kind system** designed as a foundational primitive for domain-specific languages (DSLs), graph transformations, and semantic metadata modeling.

It supports symbolic interning, ordered chaining (`Kind.next()`), DAG tree modeling (`tree`), and polymorphic cross-linking (`relate`), with lazily created parts, per-instance freezing (`freeze()`, `immute()`) and memory-awareness.

## Motivation

- Avoid string duplication in symbolic identities
- Enable semantic modeling via structural relationships
- Design graph-based, introspectable DSLs
- Support polymorphic relationship tagging (`how`)
- Optimize evaluation lazily with O(1) reads and O(log n) inserts
- Track symbolic origin (`.origin`) and memory state

## Core Components

- `Kind`: atomic unit, uniquely interned string identity
- `KindNamespace`: attribute-based creation (e.g. `k.user`, with `from kind import k`)
- `OrderedKindSet`: ordered, deduplicated set with O(1) membership (backs `children` and `parents`)
- `GraphTraversal`: iterative, cycle-safe DFS/BFS traversal (`traverse_mode`, `family_mode`)

## Relations

- **next**: sequential: `Kind.next()` creates `kind_0`, `kind_1`, ... chained via `_prev` / `_next` (there is no `que()` method)
- **tree**: parent-child DAG (`kind.tree()` = children only; `kind.graph()` = children, parents and relations)
- **relate**: polymorphic, typed edge: `a.relate(b, how='x')`, `a.unrelate(b)`, or a dynamic verb such as `a.uses(b)`; stored in `a.relations` by `how`

## Highlights

```python
from kind import k

k.page.append(k.header).append(k.footer)
k.backend.uses(k.database)

print(k.page.to_mmd())  # Mermaid.js format
```
<details>
<summary>Outcome</summary>

```text
graph LR
footer[footer]
header[header]
page[page]
    page --> header
    header --> footer
```
</details>

## Render Pipelines

- `.to_mmd()` — Markdown/HTML embeddable [Mermaid](https://mermaid.js.org) output
- `.to_dot()` / `.to_svg()` / `.to_png()` — Graphviz-based visualization (via `graphviz` Python binding), mixins from `kind.builtin.visual`
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
- Traversal: **O(V + E)**, iterative and cycle-safe
- Creation-order index (AVL tree): **O(log n)** insert

## Memory Behavior

- Controlled origin retention (`Kind.origin`; the first non-None origin given wins)
- Strong pool per `KindSpace`: a name keeps its identity and state until `delete()`, `Kind.forget(name)` or the closing of its space; `KindSpace(max_kinds=N)` caps the pool

## Extensibility

- Mixins (`register_mixin`) add behaviour to every Kind
- Async-ready traversal engine (planned)
- Frontend-ready output formats (Mermaid, SVG, PNG)

---
