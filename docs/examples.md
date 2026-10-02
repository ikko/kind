# Examples

Each vignette models one domain and exercises a different API path. Every block runs as written, and each Outcome is the real output. The [tutorial](tutorial.md) introduces the basics these build on.

| Vignette | API path |
|---|---|
| [Financial instruments](#financial-instruments-relation-verbs-and-node-shapes) | dynamic relation verbs, `node_shape`, `to_mmd` |
| [Deforestation in a supply chain](#deforestation-in-a-supply-chain-match-and-path_to) | `match`, `path_to` |
| [Service dependencies with a cycle](#service-dependencies-with-a-cycle-cycle-safe-traversal) | cycle-safe `tree`/`graph`, `parents_first` ASCII |
| [Aircraft maintenance](#aircraft-maintenance-a-mixin-with-properties) | `register_mixin` with a class |
| [Portfolio by risk](#portfolio-by-risk-a-per-kind-index) | `KindIndex` |
| [Settled transaction](#settled-transaction-maturing-with-immute) | `metadata`, `elevate`, `immute` |
| [Patient journey](#patient-journey-ordered-steps) | `insert(child, at)`, `popleft`, re-parenting |
| [Overlapping bookings](#overlapping-bookings-timeline) | `kind.time.Timeline` |

## Financial instruments: relation verbs and node shapes

Any public name the class does not define acts as a relation verb, and `node_shape` picks the Mermaid shape of a node in [`to_mmd()`](reference/api.md#kindto_mmd). This is the diagram shown in the [README](../README.md).

```python
from kind import k

k.Financial_Instrument.has_kind(k.Stock)
k.Financial_Instrument.has_kind(k.Bond)
k.Stock.traded_on(k.Exchange)
k.Bond.issued_by(k.Corporation)
k.Exchange.located_in(k.Country)
k.Corporation.located_in(k.Country)

k.Financial_Instrument.node_shape = k.Corporation.node_shape = "subroutine"
k.Exchange.node_shape = "rhombus"
k.Stock.node_shape = k.Bond.node_shape = k.Country.node_shape = "round"

print(k.Financial_Instrument.to_mmd())
```
<details>
<summary>Outcome</summary>

```text
graph LR
Bond(Bond)
Corporation[[Corporation]]
Country(Country)
Exchange{Exchange}
Financial_Instrument[[Financial_Instrument]]
Stock(Stock)
    Financial_Instrument -- has_kind --> Bond
    Bond -- issued_by --> Corporation
    Corporation -- located_in --> Country
    Financial_Instrument -- has_kind --> Stock
    Stock -- traded_on --> Exchange
    Exchange -- located_in --> Country
```
</details>

Relations of one `how` come out sorted by name (`Bond` before `Stock`); children keep their insertion order. Two larger Mermaid diagrams of a sample domain, a directory-validation system, are kept as data: [left-to-right](development/directory_validation_lr.mmd) and [top-to-bottom](development/directory_validation_tb.mmd). They use subgraphs, which `to_mmd()` does not emit.

## Deforestation in a supply chain: `match` and `path_to`

[`match(predicate)`](reference/api.md#kindmatch) yields every Kind reachable through children that satisfies the predicate (depth first; `traversal='bfs'` for breadth first). [`path_to(target)`](reference/api.md#kindpath_to) returns the chain of children links that reaches it.

```python
from kind import k

k.Global_Goods_Inc.add(k.Palm_Oil_Processor)
k.Palm_Oil_Processor.add(k.Supplier_A).add(k.Supplier_B)
k.Supplier_A.add(k.Plantation_X)
k.Supplier_B.add(k.Plantation_Y)
k.Plantation_Y.add(k.deforestation_event_2024_Q4)

for event in k.Global_Goods_Inc.match(lambda kind: "deforestation" in kind.name):
    print(" -> ".join(kind.name for kind in k.Global_Goods_Inc.path_to(event)))
```
<details>
<summary>Outcome</summary>

```text
Global_Goods_Inc -> Palm_Oil_Processor -> Supplier_B -> Plantation_Y -> deforestation_event_2024_Q4
```
</details>

## Service dependencies with a cycle: cycle-safe traversal

Edges form a directed graph (cycles and self-loops allowed; traversals are cycle-safe). Every walk visits each Kind once, so a dependency cycle ends the walk instead of looping. [`graph()`](reference/api.md#kindgraph) also follows parents, so starting in the middle of a chain still reaches the whole cycle. `to_ascii(family_mode="parents_first")` lists parents (marked `^`) before children (marked `-`).

```python
from kind import k

k.AuthService.add(k.UserService)
k.UserService.add(k.ProductService)
k.ProductService.add(k.PaymentService)
k.PaymentService.add(k.AuthService)          # closes the cycle
k.ReportingService.add(k.ProductService)     # a second parent of ProductService

print([kind.name for kind in k.AuthService.tree()])
print([kind.name for kind in k.ProductService.graph()])
print(k.ProductService.to_ascii(family_mode="parents_first"))
```
<details>
<summary>Outcome</summary>

```text
['AuthService', 'UserService', 'ProductService', 'PaymentService']
['ProductService', 'PaymentService', 'AuthService', 'UserService', 'ReportingService']
- ProductService
  ^ ReportingService
  ^ UserService
    ^ AuthService
      ^ PaymentService
  - PaymentService
```
</details>

## Aircraft maintenance: a mixin with properties

[`register_mixin`](reference/api.md#register_mixin) with a class attaches its public members, properties included, to every Kind. The mixin keeps its state in `metadata`, so a Kind gains no slots. [howto/write_a_mixin.md](howto/write_a_mixin.md) lists the rules a mixin must follow.

```python
import datetime
from kind import Kind
from kind.core.mixinability import register_mixin

INSPECTION_INTERVAL = datetime.timedelta(days=365)


class AircraftComponentMixin:
    @property
    def last_inspected(self):
        return self.metadata.get("last_inspected")

    @last_inspected.setter
    def last_inspected(self, moment):
        self.metadata["last_inspected"] = moment

    @property
    def next_inspection_due(self):
        return self.last_inspected + INSPECTION_INTERVAL if self.last_inspected else None


register_mixin(AircraftComponentMixin)

engine = Kind("Engine_Turbofan_A320")
engine.last_inspected = datetime.datetime(2025, 1, 15)
print(engine.next_inspection_due, Kind("Wing_Left").next_inspection_due)
```
<details>
<summary>Outcome</summary>

```text
2026-01-15 00:00:00 None
```
</details>

## Portfolio by risk: a per-Kind index

Each Kind owns a [`KindIndex`](reference/api.md#kindindex), created on first access to `kind.index`. It keeps other Kinds ordered by weight in an AVL tree. Inserting a Kind that is already in the index moves it to its new weight. A frozen owner refuses index changes.

```python
from kind import k, FrozenKindError

portfolio = k.MyInvestmentPortfolio
portfolio.index.insert(k.StockA, 0.7)
portfolio.index.insert(k.BondB, 0.2)
portfolio.index.insert(k.MutualFundC, 0.5)
print([kind.name for kind in portfolio.index.traverse()])

portfolio.index.insert(k.StockA, 0.1)                  # re-rated: moves, not duplicated
portfolio.index.remove(k.MutualFundC)
print([kind.name for kind in portfolio.index.traverse()])

portfolio.freeze()
try:
    portfolio.index.insert(k.GoldD, 0.3)
except FrozenKindError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
['BondB', 'MutualFundC', 'StockA']
['StockA', 'BondB']
Kind 'MyInvestmentPortfolio' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
```
</details>

## Settled transaction: maturing with `immute`

[`immute()`](reference/api.md#kindimmute) moves the `metadata` entries onto attributes ([`elevate`](reference/api.md#kindelevate)), drops attributes that hold no value ([`slim`](reference/api.md#kindslim)), then freezes the Kind. A key that names part of a Kind's identity or a Kind method stays in `metadata`, with a warning. After freezing, a write to the top level of `metadata` raises `FrozenKindError`, but nested values stay mutable ([howto/freeze_for_sharing.md](howto/freeze_for_sharing.md)).

```python
import warnings
from kind import FrozenKindError, k

transaction = k.TXN_001
transaction.metadata.update(amount=100.50, currency="USD", status="pending", details={"merchant": "Coffee Shop"})
transaction.metadata["status"] = "settled"
transaction.metadata["name"] = "renamed?"

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    transaction.immute()
print(transaction.amount, transaction.currency, transaction.status, transaction.frozen)
print(caught[0].message, dict(transaction.metadata))

transaction.details["merchant"] = "Bakery"            # nested value: still mutable
try:
    transaction.metadata["note"] = "late"
except FrozenKindError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
100.5 USD settled True
Cannot elevate 'name' on Kind 'TXN_001': it is part of its identity or structure. {'name': 'renamed?'}
Kind 'TXN_001' is frozen (immute()/freeze()); it cannot change. Hint: change it before maturing, or build a new Kind.
```
</details>

## Patient journey: ordered steps

[`insert(child, at)`](reference/api.md#kindinsert) places a child at a list position, moving it if it is already a child. [`popleft()`](reference/api.md#kindpopleft) deletes the first child and returns it. Like [`delete()`](reference/api.md#kinddelete), it links the deleted Kind's children to its parents.

```python
from kind import k

journey = k.Journey_Patient_42
journey.add(k.Consultation_GP).add(k.LabTests).add(k.Discharge)
journey.insert(k.Admission, at=0)
journey.insert(k.Treatment, at=3)
k.Admission.add(k.Triage)                              # a sub-step of Admission
print([step.name for step in journey.children])

done = journey.popleft()
print(done.name, [step.name for step in journey.children])
```
<details>
<summary>Outcome</summary>

```text
['Admission', 'Consultation_GP', 'LabTests', 'Treatment', 'Discharge']
Admission ['Consultation_GP', 'LabTests', 'Treatment', 'Discharge', 'Triage']
```
</details>

## Overlapping bookings: `Timeline`

`kind.time.Timeline` keeps `(start, end)` periods sorted and does not merge them. `overlap(other)` returns one period for each overlapping pair. `to_ascii()` draws one character per day: `#` covered, `-` not. Time is opt-in: the import enables it.

```python
import datetime
from kind.time import Timeline

room = Timeline()
room.add_period(datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 15))
room.add_period(datetime.datetime(2023, 1, 10), datetime.datetime(2023, 1, 20))
guest = Timeline([(datetime.datetime(2023, 1, 5), datetime.datetime(2023, 1, 12))])

print([(start.day, end.day) for start, end in room.overlap(guest)])
print(room.to_ascii())

try:
    room.add_period(datetime.datetime(2023, 2, 2), datetime.datetime(2023, 2, 1))
except ValueError as error:
    print(error)
```
<details>
<summary>Outcome</summary>

```text
[(5, 12), (10, 12)]
###################-
Start datetime must be before end datetime.
```
</details>
