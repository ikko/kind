"""Contracts the review fixed or pinned down: identity, freezing, sequences, traversal, relations, limits."""
import gc

import pytest

from kind import Kind, k
from kind.builtin.timeline import Timeline
from kind.core.base_kind import BaseKind
from kind.core.graph_traversal import GraphTraversal
from kind.core.kind import FrozenKindError


# --- identity -----------------------------------------------------------------

def test_one_name_has_one_identity_across_the_hierarchy():
    kind = Kind("first_as_kind")
    assert BaseKind("first_as_kind") is kind  # a more general request gets the existing Kind


def test_a_name_cannot_be_both_a_base_kind_and_a_kind():
    BaseKind("plain")
    with pytest.raises(TypeError, match="one name has one identity"):
        Kind("plain")


def test_a_name_keeps_its_state_without_any_reference():
    """The pool is strong: a name is the same entity, state included, until deleted."""
    Kind("x").metadata["a"] = 1
    Kind("y", origin="source")
    gc.collect()
    assert Kind("x").metadata["a"] == 1
    assert Kind("y").origin == "source"


def test_forget_and_delete_end_a_name():
    first = Kind("gone", origin=1)
    assert Kind.forget("gone") is True and Kind.forget("gone") is False
    assert "gone" not in Kind._pool and first not in list(Kind.each())
    assert Kind("gone", origin=2).origin == 2  # a new entity


def test_max_kinds_caps_the_pool():
    from kind import KindLimitError
    Kind("one")
    Kind.max_kinds = 2
    Kind("two")
    assert Kind("one") is Kind("one")  # existing names still resolve
    with pytest.raises(KindLimitError, match="Hint"):
        Kind("three")
    Kind.forget("one")
    Kind("three")


def test_first_origin_wins():
    assert Kind("o").origin is None
    assert Kind("o", origin=1).origin == 1
    assert Kind("o", origin=2).origin == 1


# --- attributes and dynamic relations -----------------------------------------

def test_private_typos_raise_and_public_names_are_relation_verbs():
    a = Kind("a")
    with pytest.raises(AttributeError):
        a._typo
    assert not hasattr(a, "_anything")
    a.likes(Kind("b"))
    assert [x.name for x in a.relations.get("likes")] == ["b"]


def test_elevated_attributes_and_ref_alias():
    a = Kind("a")
    a.color = "red"
    a.ref = {"source": "user_input"}
    assert a.color == "red"
    assert a.origin == {"source": "user_input"}
    del a.color
    assert callable(a.color)  # back to being a relation verb


# --- relations ----------------------------------------------------------------

def test_relate_records_an_inverse_and_unrelate_removes_both():
    a, b = Kind("a"), Kind("b")
    a.relate(b, how="owns")
    assert b in a.relations.get("owns") and a in b.relations.get("_inverse_owns")
    a.unrelate(b)
    assert not a.relations.get("owns") and not b.relations.get("_inverse_owns")


def test_relations_keep_their_targets_alive():
    a = Kind("a")
    a.relate(Kind("only_related"), how="refers_to")
    gc.collect()
    assert [x.name for x in a.relations.get("refers_to")] == ["only_related"]


def test_delete_reparents_children_and_drops_relations_both_ways():
    parent, middle, child, other = Kind("parent"), Kind("middle"), Kind("child"), Kind("other")
    parent.append(middle)
    middle.append(child)
    middle.relate(other, how="x")
    other.relate(middle, how="y")
    middle.delete()
    assert list(parent.children) == [child] and list(child.parents) == [parent]
    assert not other.relations.get("_inverse_x") and not other.relations.get("y")
    assert "middle" not in Kind._pool


def test_pop_and_popleft():
    parent = Kind("p")
    first, second = parent.append(Kind("c1")), parent.append(Kind("c2"))
    assert parent.popleft() is first
    assert list(parent.children) == [second]
    assert second.pop() is second and list(parent.children) == []


def test_insert_places_a_child_at_an_index():
    parent = Kind("p")
    a, b, c = Kind("a"), Kind("b"), Kind("c")
    parent.append(a)
    parent.append(b)
    parent.insert(c, at=0)
    parent.insert(b, at=0)
    assert [x.name for x in parent.children] == ["b", "c", "a"]


# --- freezing -----------------------------------------------------------------

def test_immute_elevates_slims_and_freezes_only_this_kind():
    a, b = Kind("a"), Kind("b")
    a.metadata["version"] = "1.0"
    a.immute()
    assert a.frozen and a.version == "1.0" and "version" not in a.metadata
    for change in (lambda: setattr(a, "x", 1), lambda: a.append(Kind("c")), lambda: b.append(a),
                   lambda: a.relate(b), lambda: b.relate(a), lambda: a.delete(), lambda: a.elevate()):
        with pytest.raises(FrozenKindError):
            change()
    b.append(Kind("c"))  # other Kinds are unaffected
    assert not b.frozen


def test_elevate_refuses_names_of_methods():
    a = Kind("a")
    a.metadata["append"] = "shadow"
    with pytest.warns(UserWarning, match="Cannot elevate 'append'"):
        assert a.elevate() == set()
    assert a.metadata["append"] == "shadow"


@pytest.mark.parametrize("key", ["name", "children", "_position"])
def test_elevate_never_touches_identity_or_structure(key):
    a = Kind("a")
    a.metadata[key] = "hijack"
    with pytest.warns(UserWarning, match="identity or structure"):
        assert a.elevate() == set()
    assert a.name == "a" and Kind._pool["a"] is a


def test_elevate_may_set_origin_and_node_shape():
    a = Kind("a")
    a.metadata["node_shape"] = "round"
    a.metadata["origin"] = {"from": "metadata"}
    assert a.elevate() == {"node_shape", "origin"}
    assert a.node_shape == "round" and a.origin == {"from": "metadata"}


def test_slim_drops_only_unset_elevated_attributes():
    from kind.core.lazy_kind import SENTINEL
    a = Kind("a")
    a.kept, a.empty = 1, SENTINEL
    a.slim()
    assert a.kept == 1 and "empty" not in a._elevated_attributes


# --- the Kind.next() sequence and creation order ------------------------------

def test_next_chains_auto_numbered_kinds():
    k0, k1, k2 = Kind.next(), Kind.next(), Kind.next()
    assert [x.name for x in (k0, k1, k2)] == ["kind_0", "kind_1", "kind_2"]
    assert k0._next is k1 and k1._prev is k0 and k2._prev is k1
    k1.delete()
    assert k0._next is k2 and k2._prev is k0


def test_creation_order_queries():
    a, b, c = Kind("a"), Kind("b"), Kind("c")
    assert Kind.first() is a and Kind.last() is c and Kind.len() == 3
    assert Kind.seek(b._position) is b and Kind.seek(99.0) is None
    assert list(Kind.each()) == [a, b, c]
    assert list(Kind.each(b)) == [b, c] and list(Kind.each(c._position)) == [c]
    with pytest.raises(TypeError):
        list(Kind.each("b"))


# --- traversal ----------------------------------------------------------------

@pytest.fixture
def family():
    root, left, right, leaf, friend = (Kind(n) for n in ("root", "left", "right", "leaf", "friend"))
    root.append(left)
    root.append(right)
    left.append(leaf)
    right.append(leaf)
    leaf.relate(friend, how="knows")
    return root, left, right, leaf, friend


def names(kinds):
    return [kind.name for kind in kinds]


def test_tree_follows_children_only(family):
    root, *_ = family
    assert names(root.tree()) == ["root", "left", "leaf", "right"]


def test_graph_follows_children_parents_and_relations(family):
    root, *_ = family
    assert names(GraphTraversal(root, "dfs").traverse()) == ["root", "left", "leaf", "right", "friend"]  # family before relations
    assert names(GraphTraversal(root, "bfs").traverse()) == ["root", "left", "right", "leaf", "friend"]


def test_parents_first_from_a_leaf(family):
    *_, leaf, _ = family
    assert names(GraphTraversal(leaf, "bfs", "parents_first").traverse()) == ["leaf", "left", "right", "friend", "root"]


@pytest.mark.parametrize("arguments", [{"traverse_mode": "zigzag"}, {"family_mode": "cousins"}])
def test_traversal_rejects_unknown_modes(arguments):
    with pytest.raises(ValueError, match="Unknown"):
        GraphTraversal(Kind("x"), **arguments)


def test_path_to_and_match(family):
    root, left, right, leaf, friend = family
    assert root.path_to(leaf) == [root, left, leaf]
    assert root.path_to(friend) == []  # relations are not paths
    assert names(root.match(lambda kind: kind.name.startswith("l"), traversal="bfs")) == ["left", "leaf"]


# --- limits: deep and cyclic graphs -------------------------------------------

@pytest.fixture
def deep_chain():
    root = node = Kind("n0")
    for i in range(1, 5000):
        node = node.append(Kind(f"n{i}"))
    return root, node


def test_deep_chains_do_not_hit_the_recursion_limit(deep_chain):
    root, tail = deep_chain
    assert root.footprint() > 0
    assert root.to_mmd().count("-->") == 4999
    assert len(root.tree()) == 5000
    assert root.path_to(tail)[-1] is tail
    assert len(Kind.from_json(root.to_json()).tree()) == 5000


def test_cycles_terminate(family):
    root, *_, leaf, _ = family
    leaf.append(root)
    assert root.footprint() > 0
    assert len(root.tree()) == 4
    assert "leaf --> root" in root.to_mmd()


# --- builtins -----------------------------------------------------------------

def test_time_head_and_tail_order_temporal_kinds_only():
    late, early, middle = Kind("2023-01-03"), Kind("2023-01-01"), Kind("2023-01-02")  # created out of order
    Kind("not a date")
    assert list(early.time_head) == [early, middle, late]
    assert list(early.time_tail) == [late, middle, early]


def test_time_properties_refuse_names_that_are_not_dates():
    with pytest.raises(ValueError, match="not a date or time"):
        Kind("tuesday-ish").as_date


def test_view_operations_are_named_for_what_they_return():
    import datetime
    days = [Kind(f"2026-10-0{d}") for d in (5, 3, 4, 10 - 9)]  # Oct 5, 3, 4, 1
    view = days[0].time_head
    assert names(view.filter_by_weekday(0)) == ["2026-10-05"]           # filter -> view (Monday)
    assert names(view.filter_by_workday()) == ["2026-10-01", "2026-10-02"][:1] + ["2026-10-05"]
    assert view.first().name == "2026-10-01" and view.closest(datetime.datetime(2026, 10, 4, 20)).name == "2026-10-05"
    assert names(view.reversed())[0] == "2026-10-05"                      # reshaper -> view
    day_of = lambda kind: kind.day
    assert (view.count(), view.sum(day_of), view.average(day_of), view.median(day_of)) == (4, 13, 3.25, 3.5)
    assert view.quantile(day_of, 0.5) == 3.5 and view.percentile(day_of, 100) == 5
    assert view.span() == datetime.timedelta(days=4)


def test_period_properties_span_the_earliest_to_the_latest_kind():
    import datetime
    start, end = Kind("2023-01-01T10:00:00"), Kind("2023-01-01T11:30:00")
    assert end.period == start.period  # one view over all live Kinds, whichever Kind asks
    expected = datetime.timedelta(hours=1, minutes=30)
    assert {start.period, start.as_period, start.duration, start.as_duration, start.delta, start.as_delta} == {expected}


def test_timeline_overlap():
    import datetime
    d = lambda day: datetime.datetime(2026, 1, day)
    first, second = Timeline([(d(1), d(5)), (d(10), d(12))]), Timeline([(d(4), d(11))])
    assert list(first.overlap(second)) == [(d(4), d(5)), (d(10), d(11))]
    assert list(first.overlap(Timeline())) == []


def test_index_remove_uses_the_weight_the_kind_was_inserted_with():
    owner, a, b = Kind("owner"), Kind("a"), Kind("b")
    owner.index.insert(a, 2.0)
    owner.index.insert(b, 1.0)
    owner.index.insert(a, 3.0)  # re-inserting moves it
    assert names(owner.index.traverse()) == ["b", "a"]
    owner.index.remove(a)
    assert names(owner.index.traverse()) == ["b"]


def test_namespace_never_creates_kinds_for_private_probes():
    before = len(Kind._pool)
    assert not hasattr(k, "__wrapped__")
    assert len(Kind._pool) == before
