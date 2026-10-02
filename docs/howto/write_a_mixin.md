# Write a mixin

[`register_mixin`](../reference/api.md#register_mixin) sets a function, class or module's public members as attributes of `BaseKind` (or of `target_class`), so every Kind in every space gains them at once. A mixin is trusted code: registering one is the same as editing the class. The registry guarantees only that a mixin cannot silently replace the core API, and that nothing more can be registered after [`lock_mixins()`](../reference/api.md#lock_mixins).

## Rules

| registering | result |
|---|---|
| a function whose first parameter is `self` | set; returns `True` |
| a class or module (with `expand=True`, the default) | each public callable, `staticmethod` or `property` is registered under its own name; returns `True` only if all were |
| a name already registered as a mixin | replaced (logged at INFO) |
| a name the class or a subclass defines (`append`, `tree`, ...) | refused unless `safe=False` |
| a private or dunder name (`_x`, `__x__`) | always refused |
| a function without `self` as first parameter | refused |
| any registration after `lock_mixins()` | refused |
| a string | raises [`TypeError`](../reference/errors.md#typeerror): strings are never evaluated |

A refusal logs the reason at ERROR on the `kind.core.mixinability` logger and returns `False`; it [does not raise](../reference/errors.md#refusals-that-do-not-raise). Check the return value. The validator reads the signature only; it does not judge what the code does.

```python
import logging
import sys
from kind import Kind
from kind.core.mixinability import register_mixin

log = logging.getLogger('kind.core.mixinability')
log.addHandler(logging.StreamHandler(sys.stdout))

def descendant_count(self) -> int:
    """Number of Kinds below this one (each counted once)."""
    return len(self.tree()) - 1

def append(self, child):
    return None

print(register_mixin(descendant_count))
print(register_mixin(append))
try:
    register_mixin("lambda self: 0", "zero")
except TypeError as error:
    print(error)

root = Kind('Root')
root.append(Kind('A')).append(Kind('B'))
print(root.descendant_count())
```
<details>
<summary>Outcome</summary>

```text
True
Refused mixin 'append': 'append' is part of the Kind API (pass safe=False to replace it deliberately).
False
register_mixin got the string 'lambda self: 0'; strings are not evaluated. Hint: pass the function, class or module object itself.
2
```
</details>

## A mixin class

A class is not instantiated: its methods are copied onto the Kind class, so `self` is the Kind. Keep no `__init__` and no instance state in the mixin; store per-Kind data in `self.metadata`, `self.context` or an attribute (`self.x = ...`). `async def` methods work like any coroutine method; the caller awaits them and decides where the work runs.

```python
import asyncio
from kind import Kind
from kind.core.mixinability import register_mixin

class GeoMixin:
    def place(self, latitude: float, longitude: float) -> 'Kind':
        self.metadata['position'] = (latitude, longitude)
        return self

    def where(self) -> str:
        latitude, longitude = self.metadata['position']
        return f"{self.name} @ {latitude}, {longitude}"

    async def a_where(self) -> str:
        return self.where()

print(register_mixin(GeoMixin))
depot = Kind('Depot').place(47.5, 19.04)
print(depot.where())
print(asyncio.run(depot.a_where()))
```
<details>
<summary>Outcome</summary>

```text
True
Depot @ 47.5, 19.04
Depot @ 47.5, 19.04
```
</details>

## One Kind only

[`apply_mixin_to_instance(kind, mixin)`](../reference/api.md#apply_mixin_to_instance) attaches members to that one Kind, bound to it like methods; it refuses a frozen Kind or a Kind of a closed space. A function becomes `kind.<name>()` with `self` = the Kind. A class is not instantiated: its public functions are bound to the Kind, its properties are evaluated on the Kind now (the stored value does not follow later changes), and its staticmethods stay plain functions.

```python
from kind import Kind
from kind.core.mixinability import apply_mixin_to_instance

def shout(self) -> str:
    return self.name.upper()

class Badge:
    @property
    def label(self) -> str:
        return f"[{self.name}]"

    def describe(self) -> str:
        return f"{self.name} has {len(self.children)} children"

alert = Kind('alert')
apply_mixin_to_instance(alert, shout)
apply_mixin_to_instance(alert, Badge)
print(alert.shout(), alert.label, alert.describe())
print('shout' in dir(Kind('other')))
```
<details>
<summary>Outcome</summary>

```text
ALERT [alert] alert has 0 children
False
```
</details>

`hasattr(kind, name)` is always true for a public name, because any unknown public attribute of a Kind is a [dynamic relation verb](../reference/api.md#relations); test with `dir()` or `get_applied_mixins()` instead.

## Lock the registry

Register mixins at start-up, then call `lock_mixins()`; the lock is process-wide and cannot be undone (`mixins_locked()` reports it). Freezing a single Kind is a different mechanism: see [freeze for sharing](freeze_for_sharing.md).

```python
import logging
import sys
from kind.core.mixinability import lock_mixins, mixins_locked, register_mixin

logging.getLogger('kind.core.mixinability').addHandler(logging.StreamHandler(sys.stdout))

def late(self) -> str:
    return 'too late'

lock_mixins()
print(mixins_locked(), register_mixin(late))
```
<details>
<summary>Outcome</summary>

```text
Refused mixin None: the mixin registry is locked (lock_mixins()).
True False
```
</details>

## Opt-in bundles

`kind` registers its builtins on import: path finding (`path_to`, `match`) and Graphviz rendering (`to_dot`, `to_svg`, `to_png`, `a_to_svg`, `a_to_png`, `from_mmd`). Time is a separate bundle: `import kind.time` registers `as_date`, `hour`, `period`, `time_head`, ... on every Kind. Package your own bundle the same way: a module whose import calls `register_mixin`, idempotent, so importing it twice changes nothing.

## Test a mixin

Test the function on its own (it is a plain function of a Kind), then the registered attribute, inside a fresh `KindSpace` so tests do not share Kinds:

```python
from kind import Kind, KindSpace
from kind.core.mixinability import register_mixin

def descendant_count(self) -> int:
    return len(self.tree()) - 1

def test_counts_each_descendant_once():
    with KindSpace(name='test'):
        root = Kind('Root')
        shared = Kind('Shared')
        root.append(Kind('A')).append(shared)
        root.append(Kind('B')).append(shared)
        assert descendant_count(root) == 3

def test_is_registered():
    assert register_mixin(descendant_count)
    with KindSpace(name='test'):
        assert Kind('Leaf').descendant_count() == 0

test_counts_each_descendant_once()
test_is_registered()
print('ok')
```
<details>
<summary>Outcome</summary>

```text
ok
```
</details>

In a pytest suite, restore the registry between tests: `kind.core.mixinability._snapshot_for_testing()` / `_restore_for_testing(snapshot)` and `_unlock_mixins_for_testing()` exist for that (see `tests/conftest.py`).
