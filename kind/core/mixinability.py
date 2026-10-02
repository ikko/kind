"""This module provides mixin-based extensibility: attaching behaviour to every Kind at runtime.

A mixin is trusted code: registering one is the same as editing the class. What this
module guarantees is that a mixin cannot silently replace the core API: dunder and
private names are always refused, existing core attributes are refused unless the
caller passes `safe=False`, and once `lock_mixins()` is called nothing more can be
registered. Locking the registry is process-wide; freezing a single Kind is
`Kind.freeze()` and is per instance.
"""
import inspect
import logging
import re
from typing import Any, Dict, Optional

from kind.core.mixin_validator import validate_mixin_callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind

log = logging.getLogger(__name__)

_mixins_locked: bool = False
_applied_mixins: Dict[str, Any] = {}  # mixin name -> the attribute it replaced (None if new)


def lock_mixins() -> None:
    """Locks the mixin registry for the whole process; further registrations are refused."""
    global _mixins_locked
    _mixins_locked = True


def mixins_locked() -> bool:
    return _mixins_locked


def _to_snake_case(text: str) -> str:
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()


def _class_and_subclasses(cls: type) -> list[type]:
    found, stack = [], [cls]
    while stack:
        current = stack.pop()
        found.append(current)
        stack.extend(current.__subclasses__())
    return found


def _refusal(name: str, target_class: type, safe: bool) -> Optional[str]:
    """Returns why `name` may not be set on `target_class`, or None if it may.

    A name is core if the target class or any subclass defines it (a mixin on BaseKind
    named 'append' would be shadowed by Kind.append, which is just as misleading).
    """
    if name.startswith('_'):
        return "private and dunder names are reserved for the core"
    owner = next((cls for cls in _class_and_subclasses(target_class) if name in vars(cls)), None)
    if owner is not None and name not in _applied_mixins and safe:
        return f"'{name}' is part of the {owner.__name__} API (pass safe=False to replace it deliberately)"
    return None


def register_mixin(value: Any, name: Optional[str] = None, target_class: Optional[type] = None,
                   safe: bool = True, expand: bool = True) -> bool:
    """Attaches `value` to `target_class` (default: BaseKind, so every Kind sees it).

    Classes and modules are expanded into their public members. Returns True on
    success; on refusal it logs the reason and returns False.
    """
    if target_class is None:
        from kind.core.base_kind import BaseKind
        target_class = BaseKind
    assert target_class is not None
    if isinstance(value, str):
        raise TypeError(f"register_mixin got the string {value!r}; strings are not evaluated. "
                        f"Hint: pass the function, class or module object itself.")
    if _mixins_locked:
        log.error(f"Refused mixin {name!r}: the mixin registry is locked (lock_mixins()).")
        return False

    if expand and (inspect.isclass(value) or inspect.ismodule(value)):
        members = (inspect.getattr_static(value, attr) if inspect.isclass(value) else getattr(value, attr)
                   for attr in dir(value))
        results = [register_mixin(member, attr, target_class, safe, expand=False)
                   for attr, member in zip(dir(value), members)
                   if not attr.startswith('_') and (isinstance(member, (staticmethod, property)) or callable(member))]
        return all(results)

    if name is None:
        if inspect.isfunction(value) or inspect.ismethod(value):
            name = value.__name__
        else:
            name = _to_snake_case(type(value).__name__).removesuffix('_mixin')

    refusal = _refusal(name, target_class, safe)
    if refusal:
        log.error(f"Refused mixin {name!r}: {refusal}.")
        return False

    if inspect.isfunction(value) or inspect.ismethod(value):
        validation = validate_mixin_callable(value)
        if not validation.is_valid:
            log.error(f"Refused mixin {name!r}: {'; '.join(validation.errors)}.")
            return False
        for warning in validation.warnings:
            log.debug(f"Mixin {name!r}: {warning}")

    if name in _applied_mixins:
        log.info(f"Mixin {name!r} replaces the previously registered mixin.")
    else:
        _applied_mixins[name] = inspect.getattr_static(target_class, name, None)
    setattr(target_class, name, value)
    return True


def get_applied_mixins() -> Dict[str, Any]:
    """Returns a copy of the registered mixins and the attributes they replaced."""
    return _applied_mixins.copy()


def apply_mixin_to_instance(instance: 'Kind', mixin: Any) -> None:
    """Attaches a mixin to one Kind only, bound to that Kind like a method.

    A function becomes `instance.<name>()` with `self` = the Kind; a class contributes its public
    functions (bound to the Kind), properties (evaluated now, on the Kind) and other attributes.
    """
    import types
    instance._ensure_mutable()
    members = ([(attr, inspect.getattr_static(mixin, attr)) for attr in dir(mixin) if not attr.startswith('_')]
               if inspect.isclass(mixin) else [(mixin.__name__, mixin)])
    for name, member in members:
        value: Any
        if isinstance(member, staticmethod):
            value = member.__func__
        elif isinstance(member, property):
            value = member.fget(instance) if member.fget else None
        elif inspect.isfunction(member):
            value = types.MethodType(member, instance)
        else:
            value = member
        instance._elevated_attributes[name] = value


def _snapshot_for_testing() -> dict:
    """Registry state to hand back to _restore_for_testing."""
    from kind.core.base_kind import BaseKind
    return {cls: dict(vars(cls)) for cls in _class_and_subclasses(BaseKind)} | {"applied": dict(_applied_mixins)}


def _restore_for_testing(snapshot: dict) -> None:
    """Removes mixins registered since `snapshot` and puts back what they replaced. Not for production."""
    applied = snapshot.pop("applied")
    for cls, attributes in snapshot.items():
        for name in [n for n in vars(cls) if n not in attributes]:
            delattr(cls, name)
        for name, value in attributes.items():
            if vars(cls).get(name) is not value and name not in ('__dict__', '__weakref__', '__doc__'):
                setattr(cls, name, value)
    _applied_mixins.clear()
    _applied_mixins.update(applied)


def _unlock_mixins_for_testing() -> None:
    """Unlocks the registry so tests stay independent. Not for production use."""
    global _mixins_locked
    _mixins_locked = False
