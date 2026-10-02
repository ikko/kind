"""Kind.from_object: scalars by their text, containers by their content, with a has_kind edge."""
import pytest

from kind.core.kind import Kind, to_kind


@pytest.mark.parametrize("value, name", [
    (123, "123"), (123.45, "123.45"), ("hello", "hello"), (True, "True"), (False, "False"), (None, "None"),
])
def test_scalar_becomes_the_kind_of_its_text(value, name):
    kind = Kind.from_object(value)
    assert kind is Kind(name)
    assert kind.origin == value and type(kind.origin) is type(value)


def test_to_kind_is_from_object():
    assert to_kind(7) is Kind.from_object(7)


@pytest.mark.parametrize("value, name, kind_of_container", [
    ([1, "two", True], "[1, 'two', True]", "list"),
    ((1, "two", True), "(1, 'two', True)", "tuple"),
])
def test_sequence_becomes_the_kind_of_its_content(value, name, kind_of_container):
    kind = Kind.from_object(value)
    assert kind.name == name
    assert kind.origin == value
    assert [child.name for child in kind.children] == ["1", "two", "True"]
    assert list(kind.relations.get("has_kind")) == [Kind(kind_of_container)]


def test_equal_content_is_the_same_kind_and_different_content_is_not():
    assert Kind.from_object([1, 2]) is Kind.from_object([1, 2])
    assert Kind.from_object([1, 2]) is not Kind.from_object([3, 4])
    assert [c.name for c in Kind.from_object([3, 4]).children] == ["3", "4"]  # no merging across lists


def test_equal_dicts_are_one_kind_whatever_their_key_order():
    assert Kind.from_object({"b": 2, "a": 1}) is Kind.from_object({"a": 1, "b": 2})
    assert Kind.from_object({"b": 2, "a": 1}).name == "{'a': 1, 'b': 2}"
    assert Kind.from_object([{"y": 1, "x": (1,)}]).name == "[{'x': (1,), 'y': 1}]"  # nested too


def test_dict_keys_are_children_and_values_hang_under_their_key():
    kind = Kind.from_object({"a": 1, "b": "two"})
    assert kind.name == "{'a': 1, 'b': 'two'}"
    assert [child.name for child in kind.children] == ["a", "b"]
    assert [child.name for child in kind.children[0].children] == ["1"]
    assert [child.name for child in kind.children[1].children] == ["two"]
    assert list(kind.relations.get("has_kind")) == [Kind("dict")]


def test_set_name_is_independent_of_iteration_order():
    kind = Kind.from_object({"one_val", "two_val", "true_val"})
    assert kind.name == "set({'one_val', 'true_val', 'two_val'})"
    assert {child.name for child in kind.children} == {"one_val", "two_val", "true_val"}
    assert Kind.from_object(set()).name == "set()"


def test_json_serializable_object_uses_its_json_text():
    import datetime
    when = datetime.date(2026, 10, 2)
    assert Kind.from_object(when).name == '"2026-10-02"'


def test_unconvertible_object_raises_with_a_hint():
    class CustomClass:
        pass

    with pytest.raises(TypeError, match="Hint"):
        to_kind(CustomClass())


@pytest.mark.parametrize("kind_name, target, expected", [
    ("42", int, 42), ("4.5", float, 4.5), ("[1, 2]", list, [1, 2]), ("true", bool, True), ("plain", str, "plain"),
])
def test_to_converts_the_name_back(kind_name, target, expected):
    assert Kind(kind_name).to(target) == expected


def test_to_refuses_non_json_names():
    with pytest.raises(TypeError, match="Cannot convert"):
        Kind("not json").to(int)
