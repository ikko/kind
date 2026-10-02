import logging

import pytest

from kind import Kind
from kind.core import mixinability
from kind.core.mixinability import get_applied_mixins, lock_mixins, mixins_locked, register_mixin


def test_lock_mixins_is_idempotent_and_refuses_registration(caplog):
    assert not mixins_locked()
    lock_mixins()
    lock_mixins()
    assert mixins_locked()

    def late_mixin(self) -> str:
        return "late"

    with caplog.at_level(logging.ERROR):
        assert register_mixin(late_mixin) is False
    assert "registry is locked" in caplog.text
    assert not hasattr(Kind, "late_mixin")


def test_register_mixin_applies_to_every_kind_and_can_be_replaced():
    def greeting(self) -> str:
        return f"Hello from {self.name}"

    assert register_mixin(greeting, "greeting") is True
    s = Kind("test_kind_for_mixin")
    assert s.greeting() == "Hello from test_kind_for_mixin"

    def other_greeting(self) -> str:
        return "Overwritten!"

    assert register_mixin(other_greeting, "greeting") is True  # a mixin may replace a mixin
    assert s.greeting() == "Overwritten!"
    assert "greeting" in get_applied_mixins()


def test_register_mixin_refuses_strings():
    with pytest.raises(TypeError, match="strings are not evaluated"):
        register_mixin("__import__('os').system('true')", "pwned")


@pytest.mark.parametrize("name", ["append", "delete", "name", "__eq__", "_frozen"])
def test_register_mixin_refuses_core_and_private_names(name):
    def hijack(self) -> None:
        return None

    original = Kind.__dict__.get(name)
    assert register_mixin(hijack, name) is False
    assert Kind.__dict__.get(name) is original


def test_register_mixin_can_replace_core_only_when_asked():
    def custom_repr_name(self) -> str:
        return "custom"

    assert register_mixin(custom_repr_name, "auto_date", target_class=Kind) is False
    original = Kind.__dict__["auto_date"]
    try:
        assert register_mixin(custom_repr_name, "auto_date", target_class=Kind, safe=False) is True
        assert Kind("x").auto_date() == "custom"
    finally:
        Kind.auto_date = original
        mixinability._applied_mixins.pop("auto_date", None)


def test_register_mixin_requires_self():
    def no_self() -> None:
        return None

    assert register_mixin(no_self, "no_self") is False


def test_register_mixin_expands_classes():
    class GreeterMixin:
        def wave(self) -> str:
            return f"{self.name} waves"

        @property
        def shout(self) -> str:
            return self.name.upper()

        @staticmethod
        def helper() -> int:
            return 42

    assert register_mixin(GreeterMixin) is True
    s = Kind("ann")
    assert (s.wave(), s.shout, s.helper()) == ("ann waves", "ANN", 42)


def test_apply_mixin_to_instance_binds_self_to_that_kind():
    from kind.core.mixinability import apply_mixin_to_instance

    def hello(self) -> str:
        return f"hi {self.name}"

    class Extras:
        def wave(self) -> str:
            return f"{self.name} waves"

        @property
        def shout(self) -> str:
            return self.name.upper()

    a, b = Kind("a"), Kind("b")
    apply_mixin_to_instance(a, hello)
    apply_mixin_to_instance(a, Extras)
    assert (a.hello(), a.wave(), a.shout) == ("hi a", "a waves", "A")
    assert callable(b.hello) and b.hello is not a.hello  # b only has the relation verb, not the mixin
