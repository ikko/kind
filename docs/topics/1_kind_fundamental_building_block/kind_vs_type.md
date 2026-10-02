# Kind vs type: what is the same, what differs

**In one sentence:** a *type* classifies values in **code**; a `Kind` is one interned, name-identified object that stands for a category in **data**, so classifying becomes an edge in a graph instead of a class in a program.

Every Python code block on this page runs in the test suite (`tests/test_doc_examples.py`); the `assert` lines are the claims.

## What a Kind is, precisely

- **An ordinary object, not a class.** `Kind('Stock')` is an instance of the Python class `Kind` ([kind.py](../../../kind/core/kind.py)). It has no instances of its own.
- **Identity by name.** All Kinds share one pool, so one name means one object, state included, until `delete()` or `Kind.forget(name)` ends it: the pool is a symbol table, as in Lisp and Ruby ([base_kind.py](../../../kind/core/base_kind.py)).
- **Equality and hash by name.**
- **Hierarchy is data:** `children`/`parents` form an ordered graph, and named **relations** carry an inverse (`a.relate(b, how='x')`, or the verb form `a.x(b)`).
- **Extensible at runtime:** mixins attach behaviour to every Kind; elevated attributes attach values to one.
- **Freezable per instance:** `kind.immute()` ends its changes.

```python
from kind import Kind, k

stock = k.Stock                      # the namespace: k.Stock is Kind('Stock')
assert stock is Kind('Stock')        # one name, one object
assert type(stock) is Kind           # a Kind is a value whose Python type is Kind
assert stock == Kind('Stock') and hash(stock) == hash('Stock')
```

## What is the same

| | Python `type` | `Kind` |
|---|---|---|
| **classifies** | a value *is an instance of* a class | a Kind *is related to* a Kind (`has_kind`) |
| **stable identity** | one class object per definition | one Kind per name |
| **hierarchy** | subclassing (MRO) | children/parents and named relations |
| **runtime extension** | attributes on the class, metaclasses | mixins on every Kind, attributes on one |
| **introspection** | `vars`, `inspect`, `__mro__` | `children`, `parents`, `relations`, `tree()`, `graph()` |

## What differs

| dimension | Python `type` (class) | `Kind` | Lisp / Ruby symbol |
|---|---|---|---|
| **identity** | object identity for its lifetime | one per name, until deleted (strong pool) | one per name (per package in Lisp) |
| **equality** | identity by default | by name | by identity |
| **instantiation** | `C()` makes values of type `C` | `Kind(name)` returns the shared node; nothing is *of* a Kind | none: the symbol is the value |
| **membership test** | `isinstance` / `issubclass` | an edge: `b in a.relations.get('has_kind')` | none built in |
| **where defined** | source code (`class`) | data: created from strings at runtime | reader or `intern` / `to_sym` |
| **static checking** | yes, with external checkers ([PEP 484](https://peps.python.org/pep-0484/)) | none: names are runtime strings | none |
| **hierarchy** | a tree/DAG of classes | any labelled graph, cycles included | flat (packages are namespaces) |
| **mutability** | classes mutable; an object's type is fixed | mutable until `kind.immute()`; then frozen | Lisp: cells mutable; Ruby: immutable |

### Membership is an edge, not `isinstance`

A Kind is not a type, so Python's `isinstance` cannot use it. Being "of a kind" is a relation, and its inverse lists the members, which a type cannot do without extra bookkeeping:

```python
import pytest
from kind import Kind, k

apple, Fruit, Food = k.apple, k.Fruit, k.Food
apple.has_kind(Fruit)                # membership: a relation named has_kind
Food.append(Fruit)                   # "subtyping": a child link

assert Fruit in apple.relations.get('has_kind')
assert list(Fruit.relations.get('_inverse_has_kind')) == [apple]   # the members, for free
assert Food.path_to(Fruit) == [Food, Fruit]                        # issubclass, as a path

with pytest.raises(TypeError):
    isinstance(apple, Fruit)         # a Kind is a value, not a type
```

### Converting values records their Python type as data

`Kind.from_object` names a container by its content, and records the container's Python type as a `has_kind` edge to a Kind. The type survives the conversion as data:

```python
from kind import Kind

numbers = Kind.from_object([1, 2])
assert numbers.name == '[1, 2]'
assert [child.name for child in numbers.children] == ['1', '2']
assert list(numbers.relations.get('has_kind')) == [Kind('list')]
assert Kind.from_object([1, 2]) is numbers          # same content, same Kind
```

## A Kind can be a category and a thing at once

Python separates a class from its instances. A Kind does not need to. `Stock` can classify (`Security` members point to it) and act (it is `traded_on` an exchange) in the same graph. Knowledge representation calls this **punning**: OWL 2 lets one name denote both a class and an individual ([OWL 2 New Features §2.4.1](https://www.w3.org/TR/owl2-new-features/#F12:_Punning)), and in RDF Schema "a class may be a member of its own class extension" ([RDFS 1.1](https://www.w3.org/TR/rdf11-schema/)).

```python
from kind import k

k.AAPL.has_kind(k.Stock)             # Stock as a category: AAPL is one
k.Stock.has_kind(k.Security)         # ... and a member of a broader one
k.Stock.traded_on(k.Exchange)        # Stock as a thing: it takes part in relations

assert list(k.Stock.relations.get('_inverse_has_kind')) == [k.AAPL]
assert list(k.Stock.relations.get('has_kind')) == [k.Security]
assert list(k.Stock.relations.get('traded_on')) == [k.Exchange]
```

The philosophers' version is the [type–token distinction](https://plato.stanford.edu/entries/types-tokens/): "homework, homework, homework" is one type and three tokens. A `Kind` is a single *token* (one object) standing for a *type* (a name). It is not necessarily a [natural kind](https://plato.stanford.edu/entries/natural-kinds/): you decide which categories exist.

## The limits that follow from "categories are data"

- **No static checking.** A misspelled name is a new Kind, and a misspelled public relation verb (`a.has_knid(b)`) is a new relation, by design. Only private names (`a._x`) raise `AttributeError`.
- **A name lives until you end it.** The pool is strong, so a Kind keeps its state with no reference held. Why not weak, like `sys.intern`? Losing an interned *string* is unobservable, because a string has no state. Losing a Kind would silently drop its origin, metadata and relations. A name ends by `delete()` / `Kind.forget(name)`, or together with its **space**: `with KindSpace():` opens a separate universe of names that is dropped when the block ends, and `KindSpace(max_kinds=...)` caps one for untrusted input.

```python
import gc
import pytest
from kind import Kind, KindLimitError, KindSpace

Kind('x', origin=1).metadata['note'] = 'kept'   # no reference held
gc.collect()
assert Kind('x').metadata['note'] == 'kept'     # same entity, same state
assert Kind('x', origin=2).origin == 1          # the first given origin wins

Kind.forget('x')                                # the name ends here
assert Kind('x').origin is None

outer = Kind('x')
with KindSpace(max_kinds=2):                    # a separate, capped universe
    assert Kind('x') is not outer                # same name, another entity
    Kind('a')
    with pytest.raises(KindLimitError):
        Kind('one too many')
assert Kind('x') is outer                        # back outside: untouched
```

- **A multiset becomes a set.** `children` hold each Kind once, so `Kind.from_object([1, 1])` has one child.

## "Not a Haskell kind": the name and its neighbours

The word *kind* already means something in several places. This is how to read it here:

| where | what "kind" means there | relation to `kind` |
|---|---|---|
| Haskell / type theory | the **type of a type**: `*` (`Type`), `* -> *` ([Haskell 2010 §4.1.1](https://www.haskell.org/onlinereport/haskell2010/haskellch4.html); GHC's `Data.Kind`) | **unrelated**: a Kind classifies values as data, not type constructors |
| Kubernetes | the `kind` field naming an object's schema (`Deployment`, `Pod`) ([objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/)) | **closest**: a name that classifies a record |
| Go `reflect.Kind` | the underlying category of a type (`Int` for `type MyInt int`) ([pkg.go.dev](https://pkg.go.dev/reflect#Kind)) | similar idea, inside the type system |
| Python `inspect.Parameter.kind` | how an argument binds (`POSITIONAL_ONLY`, …) ([docs](https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind)) | unrelated, same word |
| TypeScript discriminated unions | a `kind: "circle"` tag field that narrows a union ([handbook](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)) | similar: a value that says what something is |

And the command-line tool is `kind-scheduler`, not `kind`, because `kind` is also the [Kubernetes-in-Docker](https://kind.sigs.k8s.io/) binary.

## Why the name

The library was `symb`, short for *symbol*, which was taken. A `Kind` is still a symbol in the Lisp sense: interned, compared by identity, carrying properties ([CLHS `intern`](https://www.lispworks.com/documentation/HyperSpec/Body/f_intern.htm), [Ruby `Symbol`](https://ruby-doc.org/3.3.0/Symbol.html)).

The new name says what it is used for. The author avoids the bare word *type* in every language, because it collides with something sooner or later, and uses *kind* where *type* would be the everyday word. A Kind is the everyday "what kind of thing is this", kept as data.

## Sources

- Python data model (objects, values and types; metaclasses): https://docs.python.org/3/reference/datamodel.html
- `sys.intern`: https://docs.python.org/3/library/sys.html#sys.intern
- PEP 484 (type hints), PEP 544 (protocols): https://peps.python.org/pep-0484/, https://peps.python.org/pep-0544/
- Common Lisp HyperSpec, `intern` and `symbol`: https://www.lispworks.com/documentation/HyperSpec/Body/f_intern.htm, https://www.lispworks.com/documentation/HyperSpec/Body/t_symbol.htm
- Ruby `Symbol`: https://ruby-doc.org/3.3.0/Symbol.html
- Haskell 2010 Report §4.1.1 Kinds: https://www.haskell.org/onlinereport/haskell2010/haskellch4.html
- Kubernetes objects: https://kubernetes.io/docs/concepts/overview/working-with-objects/
- Go `reflect.Kind`: https://pkg.go.dev/reflect#Kind
- Stanford Encyclopedia of Philosophy, *Types and Tokens*: https://plato.stanford.edu/entries/types-tokens/ ; *Natural Kinds*: https://plato.stanford.edu/entries/natural-kinds/
- RDF Schema 1.1: https://www.w3.org/TR/rdf11-schema/ ; OWL 2 punning: https://www.w3.org/TR/owl2-new-features/#F12:_Punning
- B. C. Pierce, *Types and Programming Languages*, ch. 29 "Type Operators and Kinding" (MIT Press, 2002)
