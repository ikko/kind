"""The guarantees the docs state: identity is fixed, edits are atomic, settled Kinds refuse every change."""
import contextvars
import threading

import pytest

from kind import FrozenKindError, Kind, KindSpace, SpaceError


@pytest.mark.parametrize("slot", ["name", "children", "parents", "_space", "_position"])
def test_identity_and_structure_cannot_be_assigned(slot):
    a = Kind("a")
    with pytest.raises(AttributeError, match="identity or structure"):
        setattr(a, slot, "x")
    with pytest.raises(AttributeError, match="identity or structure"):
        delattr(a, slot)
    assert Kind("a") is a and a.name == "a"


def test_reparent_leaves_every_edge_on_both_ends():
    grand, mid, leaf = Kind("grand"), Kind("mid"), Kind("leaf")
    grand.append(mid)
    mid.append(leaf)
    mid.reparent()
    assert list(mid.parents) == [] and list(mid.children) == []
    assert list(grand.children) == [leaf] and list(leaf.parents) == [grand]


def test_reparent_drops_a_self_loop_and_keeps_both_ends():
    """Found by the edge-symmetry property: a -> b, b -> b, then b.reparent()."""
    a, b = Kind("a"), Kind("b")
    a.append(b)
    b.append(b)
    b.reparent()
    assert list(b.parents) == [] and list(b.children) == [] and list(a.children) == []


def frozen_pair():
    parent, child = Kind("parent"), Kind("child")
    parent.append(child)
    parent.relate(child, how="likes")
    return parent, child


@pytest.mark.parametrize("change", [
    lambda p, c: p.unrelate(c),
    lambda p, c: c.reparent(),
    lambda p, c: c.delete(),                       # would change the frozen parent's children
    lambda p, c: p.index.insert(Kind("x"), 1.0),
], ids=["unrelate", "reparent child", "delete child", "index"])
def test_a_frozen_kind_refuses_every_change(change):
    parent, child = frozen_pair()
    parent.freeze()
    before = (list(parent.children), list(child.parents), list(parent.relations.get("likes")))
    with pytest.raises(FrozenKindError):
        change(parent, child)
    assert (list(parent.children), list(child.parents), list(parent.relations.get("likes"))) == before


@pytest.mark.parametrize("frozen", [False, True])
@pytest.mark.parametrize("change", [
    lambda p, c: p.children.add(Kind("sneak")),
    lambda p, c: p.children.clear(),
    lambda p, c: c.parents.discard(p),          # would leave p -> c one-sided
    lambda p, c: p.relations.get("likes").add(Kind("sneak")),
], ids=["children.add", "children.clear", "parents.discard", "relations add"])
def test_edge_sets_change_only_through_kind_methods(change, frozen):
    parent, child = frozen_pair()
    if frozen:
        parent.freeze()
    with pytest.raises(AttributeError, match="change only through append"):
        change(parent, child)
    assert list(parent.children) == [child] and list(child.parents) == [parent]


def test_patching_from_a_frozen_kind_is_refused_before_any_change():
    parent, child = frozen_pair()
    parent.freeze()
    other = Kind("other")
    with pytest.raises(FrozenKindError):
        other.patch(child)  # would add other as a child of the frozen parent
    assert list(other.parents) == [] and list(parent.children) == [child]


def test_a_refused_edit_is_not_half_applied():
    a, b, c = Kind("a"), Kind("b"), Kind("c")
    a.append(b)
    b.append(c)
    c.freeze()
    with pytest.raises(FrozenKindError):
        b.delete()  # c (a child of b) would be re-parented, and c is frozen
    assert list(a.children) == [b] and list(b.children) == [c]
    assert list(b.parents) == [a] and list(c.parents) == [b] and Kind("b") is b


def test_a_closed_space_refuses_unrelate_and_reparent():
    with KindSpace():
        a, b = Kind("a"), Kind("b")
        a.relate(b)
        a.append(b)
    for change in (lambda: a.unrelate(b), lambda: b.reparent()):
        with pytest.raises(SpaceError, match="closed space"):
            change()


def test_reads_see_a_consistent_snapshot_while_another_thread_writes():
    root = Kind("root")
    stop = threading.Event()
    context = contextvars.copy_context()

    def writer():
        for n in range(3000):  # new relation names keep changing the dict a reader iterates
            if stop.is_set():
                return
            root.relate(Kind(f"r{n}"), how=f"how{n}")

    thread = threading.Thread(target=context.run, args=(writer,))
    thread.start()
    try:
        for _ in range(30):
            root.to_mmd()
            root.graph()
    finally:
        stop.set()
        thread.join()


def test_mixed_naive_and_aware_names_explain_the_problem():
    Kind("2024-01-01T00:00:00")
    with pytest.raises(ValueError, match="naive and timezone-aware"):
        Kind("2024-01-02T00:00:00+00:00").time_head


def test_time_only_names_are_not_temporal():
    noon = Kind("12:00:00")
    with pytest.raises(ValueError, match="not an ISO 8601 date or datetime"):
        noon.hour
    assert noon not in list(Kind("2024-01-01").time_head)


def test_frozen_kind_error_is_exported():
    import kind as package
    assert package.FrozenKindError is FrozenKindError


def test_from_ascii_reads_parent_lines_back_as_parents():
    a, b, c = Kind("a"), Kind("b"), Kind("c")
    a.append(b)
    a.append(c)
    text = b.to_ascii()  # rendered from a child, so `a` appears as a parent
    assert "^ a" in text
    with KindSpace():
        rebuilt = Kind.from_ascii(text)
        assert rebuilt.name == "b" and [p.name for p in rebuilt.parents] == ["a"]
        assert sorted(child.name for child in Kind("a").children) == ["b", "c"]


@pytest.mark.parametrize("name, target, value", [
    ("True", bool, True), ("None", type(None), None), ("{'a': 1}", dict, {"a": 1}), ("(1, 'x')", tuple, (1, "x")),
    ("[1, 2]", list, [1, 2]), ("2.5", float, 2.5),
])
def test_to_reads_back_the_names_from_object_produces(name, target, value):
    assert Kind(name).to(target) == value
    assert Kind.from_object(value).to(target) == value


def test_to_never_evaluates_code():
    with pytest.raises(TypeError, match="neither JSON nor a Python literal"):
        Kind("__import__('os').getcwd()").to(str.__class__)


@pytest.mark.parametrize("text", ['[{"nm": 1}]', '[1, 2]', '[{"name": "a", "children": "b"}]', '[{"name": 3}]',
                                  '{"name": "a"}', '3'])
def test_malformed_serialized_input_is_a_value_error(text):
    with pytest.raises(ValueError, match="Hint: produce it with to_json"):
        Kind.from_json(text)


@pytest.mark.parametrize("load, text", [(Kind.from_toml, "kinds = 3"), (Kind.from_yaml, "name: a"),
                                        (Kind.from_toml, "kinds = [1]")])
def test_malformed_toml_and_yaml_are_value_errors_too(load, text):
    with pytest.raises(ValueError, match="Hint: produce it with to_"):
        load(text)
