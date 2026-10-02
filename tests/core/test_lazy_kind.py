from kind import Kind
from kind.core.lazy_kind import LazyKind


def test_lazy_kind_defers_conversion_until_first_use():
    lazy = LazyKind(42)
    assert not lazy.evaluated
    assert "42" not in Kind._pool  # nothing created yet

    assert lazy.name == "42"  # first attribute access converts
    assert lazy.evaluated
    assert lazy.evaluate() is Kind("42")
    assert lazy == Kind("42") and hash(lazy) == hash(Kind("42"))


def test_lazy_kind_is_accepted_wherever_a_kind_is():
    parent = Kind("parent")
    child = parent.append(LazyKind("child"))
    assert child is Kind("child")
    assert parent.children == [Kind("child")]
    assert Kind.from_object(LazyKind("x")) is Kind("x")


def test_containers_convert_their_items_eagerly():
    """Children must be hashed to be linked, so a container's items become Kinds at once."""
    list_kind = Kind.from_object([1, 2, 3])
    assert [child.name for child in list_kind.children] == ["1", "2", "3"]
    assert all(type(child) is Kind for child in list_kind.children)
