# Errors

Every error `kind` raises on purpose, with the condition that triggers it. Messages end with a
`Hint:` where there is a usual fix. The block at the end of this page triggers each one and checks
the exact message, so this page cannot drift from the code.

## `kind`

### `FrozenKindError`
Subclass of `AttributeError`. Raised when a frozen Kind (`freeze()`, `immute()`) is asked to change:
- attribute write or delete;
- `append`, `insert`, `relate`, `unrelate`, `reparent`, `delete`, `patch`, its `index`;
- a write to its `metadata` or `context`;
- an edit of another Kind that would change it, such as deleting the child of a frozen parent.

The edit is refused before anything changes.

### `SpaceError`
Subclass of `RuntimeError`. Raised when:
- an edge or relation would join Kinds of two spaces;
- a Kind of a closed space is asked to change (reading it is fine);
- a closed space is entered again;
- the default space is closed.

### `KindLimitError`
Subclass of `RuntimeError`. Raised when creating a new name would exceed the current space's
`max_kinds`. Existing names still resolve.

### `AttributeError`
Raised when:
- a private name (`kind._x`) or a name the class defines failed;
- a time property is read without `import kind.time`;
- `name`, `children`, `parents` or another identity or structure slot is assigned or deleted;
- `children`, `parents` or a relation set is changed directly instead of through `append`,
  `insert`, `relate`, `unrelate`, `reparent` or `delete`.

### `TypeError`
Raised for:
- `Kind(name)` with a non-`str` name;
- a name that already exists as a less specific class (`BaseKind('p')`, then `Kind('p')`);
- `Kind.from_object` of a value that is neither a scalar, a container nor JSON-serializable;
- `Kind.to(T)` of a name that is neither JSON nor a Python literal;
- `register_mixin` given a string.

### `ValueError`
Raised for:
- a time property of a Kind whose name is not an ISO 8601 date or datetime;
- ordering a space that mixes naive and timezone-aware datetimes (`time_head`);
- `from_json`/`from_yaml`/`from_toml`/`from_ascii` of empty input, and `from_json`/`from_yaml`/
  `from_toml` of input that is not a list of `{'name': str, 'children': [str], 'relations': {how: [str]}}`
  (malformed JSON is `orjson.JSONDecodeError`, also a `ValueError`);
- an unknown `traverse_mode` or `family_mode`;
- an unknown `filter_by_time_of_day` value.

### `KeyError`
Raised by deleting a missing key from a `DefDict` (`kind.metadata`, `kind.context`); the message
names the key. On a frozen Kind or in a closed space, reading a missing key also raises `KeyError`
(an open Kind's `DefDict` would create the key instead).

### `ImportError`
Raised by the Graphviz renderers (`to_dot`, `to_svg`, `to_png` and their async forms) when the
`graphviz` package is missing (`pip install 'kind[visual]'`). SVG and PNG also need the Graphviz
`dot` executable.

### Refusals that do not raise
`register_mixin` returns `False` and logs the reason at ERROR level for a refused name (private,
core, or the registry is locked), so a set of registrations can be attempted together.

## `kind-scheduler`

### `CallableNotAllowedError`
Subclass of `PermissionError`. A schedule file or the CLI names a function outside
`allowed_modules` / `--allow-module`. It is raised while loading, before anything runs.

### Scheduler `TypeError` and `ValueError`
- `TypeError`: a `ScheduledJob` without a schedule, or with an unsupported schedule type.
- `ValueError`:
  - a schedule string that is neither cron nor ISO 8601;
  - a job added to a `Scheduler` with a `schedule_file` whose function a file cannot name
    (a lambda, nested function or method).

## Every message, checked

```python
import kind
import kind.time
from kind import FrozenKindError, Kind, KindLimitError, KindSpace, SpaceError
from kind.core.base_kind import BaseKind
from kind.core.mixinability import register_mixin
from kind_scheduler import CallableNotAllowedError, ScheduledJob, Scheduler, resolve_callable


def message(action):
    try:
        action()
    except Exception as error:
        return f"{type(error).__name__}: {error}"
    raise AssertionError("no error")


frozen = Kind("frozen").freeze()
assert message(lambda: frozen.append(Kind("b"))) == (
    "FrozenKindError: Kind 'frozen' is frozen (immute()/freeze()); it cannot change. "
    "Hint: change it before maturing, or build a new Kind.")

assert message(lambda: setattr(Kind("c"), "name", "z")) == (
    "AttributeError: 'name' is part of Kind 'c''s identity or structure and cannot be assigned. "
    "Hint: use append/insert/relate/delete to change edges; a different name is a different Kind.")

assert message(lambda: Kind(1)) == (
    "TypeError: Kind name must be a string, got int. Hint: use Kind.from_object(value) to convert other values.")

BaseKind("plain")
assert message(lambda: Kind("plain")) == (
    "TypeError: 'plain' already exists as BaseKind, so it cannot also be a Kind: one name has one identity. "
    "Hint: create it as Kind first, or delete() the existing one.")

outside = Kind("outside")
with KindSpace(name="capped", max_kinds=1) as capped:
    inside = Kind("inside")
    assert message(lambda: Kind("one too many")) == (
        "KindLimitError: Cannot create 'one too many': KindSpace('capped', 1 kinds) already holds max_kinds=1 Kinds. "
        "Hint: delete() or Kind.forget() Kinds you no longer need, or raise the space's max_kinds.")
    assert message(lambda: inside.append(outside)).startswith(
        "SpaceError: Cannot link 'inside' in KindSpace('capped', 1 kinds) to 'outside' in KindSpace(")

assert message(lambda: inside.relate(outside)) == (
    "SpaceError: Kind 'inside' belongs to a closed space; it can be read but not changed.")
assert message(lambda: capped.__enter__()) == (
    "SpaceError: KindSpace('capped', closed) is closed and cannot be entered again. Hint: open a new KindSpace().")

assert message(lambda: Kind("tuesday").as_date) == (
    "ValueError: Kind 'tuesday' is not an ISO 8601 date or datetime. "
    "Hint: time properties need an ISO 8601 name such as '2026-10-02' or '2026-10-02T13:45:00'.")

assert message(lambda: register_mixin("x")) == (
    "TypeError: register_mixin got the string 'x'; strings are not evaluated. "
    "Hint: pass the function, class or module object itself.")

assert message(lambda: resolve_callable("os.system", [])) == (
    "CallableNotAllowedError: Refusing to import 'os.system': module 'os' is not in allowed_modules []. "
    "Hint: pass allowed_modules=['os'] (CLI: --allow-module os) only if you trust the schedule file.")

assert message(lambda: ScheduledJob(print, schedule="nope")) == (
    "ValueError: Schedule 'nope' is neither a cron expression nor an ISO 8601 datetime.")

print("all messages as documented")
```
