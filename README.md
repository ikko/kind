# kind

Interned, name-identified graph nodes for modelling symbols, categories as data.

## TL;DR

```python
from kind import k

k.girls.dream_about(k.world_peace)       # k.<name> is the one Kind of that name; any public name is a relation verb
k.girls.dream_about(k.good_sleep)
print(k.girls.to_mmd(direction="TD"))    # the same graph as a Mermaid flowchart ("LR" is the default)
```

`Kind('Stock')` returns the one object that stands for "Stock" in the current space. Kinds link
into a directed graph: children and parents, plus named relations with inverses. Behaviour
attaches to every Kind at runtime through mixins, and a Kind can be frozen once it is final. A
category and its members can be modelled without defining a Python class for each
([Kind vs type](docs/kind_vs_type.md)).

**Status:**
- pre-alpha, private (all rights reserved, see [LICENSE](LICENSE));
- not published to PyPI (`Private :: Do Not Upload`);
- Python 3.10–3.14.

## Install (from the checkout)

```bash
make install        # editable install of kind and kind-scheduler into ~/.virtualenvs/kind
make check          # pyflakes, mypy, bandit, tests (including every example in the docs)
```

Or `uv pip install -e ".[dev,visual]" -e ./scheduler` into a venv of your choice. The `visual` extra
installs `graphviz` for SVG and PNG output; Mermaid and ASCII need nothing extra.

## Example

```python
from kind import Kind, KindSpace, k

with KindSpace():                                   # an isolated universe of names
    stock, bond = k.Stock, k.Bond                   # k.Stock is Kind("Stock")
    k.Financial_Instrument.add(stock).add(bond)     # family edges (children)
    stock.traded_on(k.Exchange)                     # any public name is a relation verb
    k.AAPL.has_kind(stock)                          # membership is an edge, not isinstance

    assert Kind("Stock") is stock
    assert [c.name for c in k.Financial_Instrument.children] == ["Stock", "Bond"]
    assert list(stock.relations.get("_inverse_has_kind")) == [k.AAPL]
    print(k.Financial_Instrument.to_mmd())          # Mermaid; also to_ascii, to_json/yaml/toml, to_dot
```

## Guarantees

| property | guarantee | detail |
|---|---|---|
| **identity** | one object per name per space; the name is fixed | [concepts](docs/concepts.md#identity-equality-hashing) |
| **equality, hash** | equal = same name and same space; hash = hash of the name | [concepts](docs/concepts.md#identity-equality-hashing) |
| **lifetime** | the pool is strong: a name lives until `delete()`, `Kind.forget()` or its space closes; `KindSpace(max_kinds=N)` caps it | [concepts](docs/concepts.md#lifetime) |
| **isolation** | `with KindSpace():` is a separate pool, order and lock; no edge crosses spaces | [concepts](docs/concepts.md#spaces) |
| **graph** | directed; cycles and self-loops allowed; traversals terminate; every edge exists on both ends | [concepts](docs/concepts.md#the-graph) |
| **concurrency** | mutations of a space are serialized by its `RLock`; reads iterate per-Kind snapshots; composite operations are not atomic | [concepts](docs/concepts.md#concurrency) |
| **freezing** | a frozen Kind refuses every attribute, edge, relation and index change, including from its neighbours' edits; `metadata`/`context` are read-only at the top level only | [concepts](docs/concepts.md#freezing) |
| **mixins** | trusted code; strings are never evaluated; core and private names are protected | [concepts](docs/concepts.md#mixins) |
| **errors** | every intentional error has a fixed message, mostly with a `Hint:` | [errors](docs/reference/errors.md) |

## What is in the box

| module | content |
|---|---|
| `kind` | `Kind`, `k`, `KindSpace`, relations, traversal, Mermaid/ASCII rendering, JSON/YAML/TOML serialization, maturing (`elevate`, `slim`, `immute`), mixins |
| `kind.time` (opt-in: `import kind.time`) | Kinds named like ISO 8601 dates or datetimes: `as_date`, `hour`, `period`, chronological `time_head`/`time_tail` views, `Timeline` |
| `kind.builtin.visual` | Graphviz output (`to_dot`, `to_svg`, `to_png`) and `from_mmd` |
| [`kind-scheduler`](scheduler/README.md) (separate distribution) | cron and one-off jobs with an allowlist for schedule files, batch processing, the `kind-scheduler` CLI |

## Documentation

- [Tutorial](docs/tutorial.md): from a first Kind to spaces, relations and freezing.
- [Concepts](docs/concepts.md): the contract for identity, lifetime, spaces, graph, concurrency, freezing, mixins and serialization.
- [API reference](docs/reference/api.md) and [errors](docs/reference/errors.md).
- How-to guides:
  - [isolate a graph](docs/howto/isolate_a_graph.md);
  - [handle untrusted input](docs/howto/untrusted_input.md);
  - [serialize and round-trip](docs/howto/serialize.md);
  - [threads and async](docs/howto/threads_and_async.md);
  - [freeze for sharing](docs/howto/freeze_for_sharing.md);
  - [write a mixin](docs/howto/write_a_mixin.md).
- [Performance](docs/performance.md): the complexity of every operation, with measurements.
- [Architecture](docs/architecture.md): modules, data model, extension points.
- [Examples](docs/examples.md): domain models built with Kinds.
- [Kind vs type](docs/kind_vs_type.md): what a Kind shares with a type and where it differs.
- [Changelog](docs/changelog.md) · [history and design records](docs/history/README.md).

Every Python block in this README and in `docs/` runs in the test suite, so the examples match the
code.
