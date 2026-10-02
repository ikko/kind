"""ps/ls/stat print real state; package aliases resolve; the mixin validator explains refusals."""
import kind
from kind import Kind
from kind.core.mixin_validator import MixinValidationResult, validate_mixin_callable
from kind.core.mixinability import register_mixin


def test_ps_lists_every_pooled_kind_with_its_origin(capsys):
    Kind("alpha", origin="here").append(Kind("beta"))
    Kind.ps()
    out = capsys.readouterr().out
    assert "alpha" in out and "here" in out and "kind.core.kind.Kind" in out  # beta has no origin
    assert out.strip().splitlines()[-1].startswith("Total")


def test_ls_lists_registered_mixins(capsys):
    def wave(self) -> str:
        return "hi"

    register_mixin(wave)
    Kind.ls()
    out = capsys.readouterr().out
    assert "- wave" in out and "- to_dot" in out and "- time_head" in out
    assert "Scheduler" not in out  # classes that merely live in the package are not mixins


def test_stat_reports_this_kinds_state(capsys):
    a = Kind("a")
    a.append(Kind("b"))
    a.relate(Kind("c"), how="likes")
    a.colour = "red"
    a.stat()
    out = capsys.readouterr().out
    assert "Children: 1  Parents: 0  Relations: 1" in out
    assert "Own attributes: colour" in out and "Frozen: False" in out


def test_package_aliases_resolve_to_modules():
    assert kind.td is kind.time_dim and kind.td.__name__ == "kind.builtin.time_dim"
    assert kind.schedule.__name__ == "kind.core.schedule" and kind.vis is kind.visual
    assert {"td", "schedule", "Kind"} <= set(dir(kind))
    try:
        kind.no_such_thing
    except AttributeError as error:
        assert "no_such_thing" in str(error)
    else:
        raise AssertionError("unknown attribute did not raise")


def test_validator_explains_what_is_wrong():
    def no_self(x) -> None: ...
    def fine(self): ...

    refused = validate_mixin_callable(no_self)
    assert not refused and "'self'" in refused.errors[0] and refused.to_dict()["is_valid"] is False
    accepted = validate_mixin_callable(fine)
    assert accepted and accepted.warnings == ["no return type annotation"]
    assert "Invalid" in repr(refused) and "Valid" in repr(accepted)
    assert isinstance(refused, MixinValidationResult)
    assert not validate_mixin_callable(print)  # a builtin has a signature, but not one bound to self
