"""Property-based tests: the contracts hold for generated inputs, not just for chosen examples."""
import functools
import itertools

import orjson
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from kind import Kind
from kind.builtin.avl_tree import AVLTree
from kind.builtin.collections import OrderedKindSet
from kind.core.graph_traversal import GraphTraversal
from kind.core.space import KindSpace, current_space
from kind.core.kind import canonical_repr, tomllib

# Each example builds Kinds; the pool is reset per test by conftest, and per example here.
PER_EXAMPLE = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])


def in_fresh_space(test):
    """Hypothesis runs many examples in one test: each example gets its own space."""
    @functools.wraps(test)
    def run(*args, **kwargs):
        with KindSpace(name="example"):
            return test(*args, **kwargs)
    return run


# --- AVL tree -------------------------------------------------------------------

def check_avl(node):
    """Returns (height, weights in order) and asserts balance and stored heights on the way."""
    if node is None:
        return 0, []
    left_height, left = check_avl(node.left)
    right_height, right = check_avl(node.right)
    assert abs(left_height - right_height) <= 1, "unbalanced"
    assert node.height == 1 + max(left_height, right_height), "stale height"
    return node.height, left + [node.eval_weight()] + right


class Item:
    def __init__(self, number):
        self.name = str(number)


@PER_EXAMPLE
@given(st.lists(st.tuples(st.integers(0, 50), st.booleans()), max_size=120))
def test_avl_stays_sorted_balanced_and_sized(operations):
    tree, alive = AVLTree(), []
    items = {}
    for number, insert in operations:
        if insert or not alive:
            item = items.setdefault(len(items), Item(len(items)))
            tree.add(item, float(number))
            alive.append((float(number), item))
        else:
            weight, item = alive.pop(number % len(alive))
            tree.remove(weight, item)
    _, weights = check_avl(tree.root)
    assert weights == sorted(weight for weight, _ in alive)
    assert tree.size() == len(alive)
    assert sorted(map(id, tree)) == sorted(id(item) for _, item in alive)


# --- OrderedKindSet against a list model --------------------------------------

OPERATIONS = st.lists(st.tuples(st.sampled_from(["add", "discard", "insert", "pop"]),
                                st.integers(0, 9), st.integers(0, 9)), max_size=80)


@PER_EXAMPLE
@given(OPERATIONS)
@in_fresh_space
def test_ordered_kind_set_matches_a_list_without_duplicates(operations):
    kinds = [Kind(f"k{i}") for i in range(10)]
    subject, model = OrderedKindSet(), []
    for op, which, index in operations:
        kind = kinds[which]
        if op == "add":
            assert subject.add(kind) == (kind not in model)
            if kind not in model:
                model.append(kind)
        elif op == "discard":
            subject.discard(kind)
            if kind in model:
                model.remove(kind)
        elif op == "insert":
            subject.insert(index, kind)
            if kind in model:
                model.remove(kind)
            model.insert(index, kind)
        elif model:
            assert subject.pop(index % len(model)) is model.pop(index % len(model))
        assert subject == model and len(subject) == len(model)
        assert all(kind in subject for kind in model) and not any(kind in subject for kind in kinds if kind not in model)


# --- serialization round trips --------------------------------------------------

GRAPHS = st.tuples(
    st.integers(1, 12),
    st.lists(st.tuples(st.integers(0, 11), st.integers(0, 11)), max_size=25),
    st.lists(st.tuples(st.integers(0, 11), st.sampled_from(["likes", "owns", "has kind"]), st.integers(0, 11)), max_size=15),
)
FORMATS = {
    "json": (Kind.to_json, Kind.from_json, orjson.loads),
    "yaml": (Kind.to_yaml, Kind.from_yaml, yaml.safe_load),
    "toml": (Kind.to_toml, Kind.from_toml, lambda text: tomllib.loads(text)["kinds"]),
}


def build(size, links, relations):
    kinds = [Kind(f"node {i}") for i in range(size)]
    for parent, child in links:
        if parent < size and child < size and parent != child:
            kinds[parent].append(kinds[child])
    for source, how, target in relations:
        if source < size and target < size:
            kinds[source].relate(kinds[target], how=how)
    return kinds


def shape():
    """Children order and forward relations of every pooled Kind, by name."""
    return {name: ([c.name for c in kind.children],
                   {how: sorted(k.name for k in ks) for how, ks in kind.relations.items() if not how.startswith("_inverse_")})
            for name, kind in current_space().pool.items()}


@PER_EXAMPLE
@given(GRAPHS, st.sampled_from(sorted(FORMATS)))
def test_dump_then_load_rebuilds_the_component(graph, fmt):
    dump, load, parse = FORMATS[fmt]
    with KindSpace(name="original"):
        root = build(*graph)[0]
        component = {node["name"] for node in parse(dump(root))}
        expected = {name: edges for name, edges in shape().items() if name in component}
        text = dump(root)

    with KindSpace(name="rebuilt"):
        load(text)
        assert shape() == expected
        assert dump(Kind(root.name)) == text  # and dumping again gives the same text


# --- canonical names --------------------------------------------------------------

VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=5),
    lambda children: st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=3), children, max_size=4),
    max_leaves=12,
)


@settings(max_examples=150, deadline=None)
@given(st.dictionaries(st.text(max_size=3), VALUES, max_size=5), st.randoms())
def test_equal_dicts_have_one_canonical_name_whatever_the_key_order(mapping, rng):
    keys = list(mapping)
    rng.shuffle(keys)
    reordered = {key: mapping[key] for key in keys}
    assert reordered == mapping
    assert canonical_repr(reordered) == canonical_repr(mapping)


@settings(max_examples=150, deadline=None)
@given(st.frozensets(st.integers() | st.text(max_size=3), max_size=6))
def test_set_names_do_not_depend_on_iteration_order(members):
    names = {canonical_repr(set(order)) for order in itertools.islice(itertools.permutations(members), 6)}
    assert len(names) <= 1


@PER_EXAMPLE
@given(VALUES)
@in_fresh_space
def test_converting_a_value_twice_gives_the_same_kind(value):
    assert Kind.from_object(value) is Kind.from_object(value)


# --- every edge on both ends, whatever the sequence of edits --------------------

EDITS = st.lists(st.tuples(st.sampled_from(["append", "relate", "unrelate", "reparent", "delete"]),
                           st.integers(0, 7), st.integers(0, 7)), max_size=60)


def assert_edges_symmetric(kinds):
    for kind in kinds:
        assert all(kind in child.parents for child in kind.children), f"{kind.name}: child without back-edge"
        assert all(kind in parent.children for parent in kind.parents), f"{kind.name}: parent without back-edge"
        for how, related in kind.relations.items():
            inverse = how[len("_inverse_"):] if how.startswith("_inverse_") else f"_inverse_{how}"
            assert all(kind in other.relations.get(inverse) for other in related), f"{kind.name}: one-sided {how}"


@settings(max_examples=400, deadline=None)  # the self-loop case needed more than the default to show up
@given(EDITS)
@in_fresh_space
def test_edges_stay_symmetric_under_any_edit_sequence(edits):
    kinds = [Kind(f"k{i}") for i in range(8)]
    for op, i, j in edits:
        a, b = kinds[i], kinds[j]
        if op == "append":
            a.append(b)
        elif op == "relate":
            a.relate(b, how="r")
        elif op == "unrelate":
            a.unrelate(b)
        elif op == "reparent":
            a.reparent()
        elif op == "delete" and Kind.forget(a.name):
            kinds[i] = Kind(f"k{i}")  # the name starts afresh
        assert_edges_symmetric(kinds)


@PER_EXAMPLE
@given(GRAPHS, st.sampled_from(["children_first", "parents_first"]))
def test_ascii_round_trip_restores_the_family_edges(graph, family_mode):
    """Depth-first output is an outline, so it reads back exactly; breadth-first output is display only."""
    traverse_mode = "dfs"
    with KindSpace(name="original"):
        start = build(*graph)[-1]  # render from an arbitrary Kind, not only a root
        text = start.to_ascii(traverse_mode=traverse_mode, family_mode=family_mode)
        family = {node.name for node in GraphTraversal(start, family_mode=family_mode).traverse_family()}
        expected = {name: sorted(c.name for c in current_space().get(name).children) for name in family}
    with KindSpace(name="rebuilt"):
        rebuilt = Kind.from_ascii(text)
        assert rebuilt.name == start.name
        assert {name: sorted(c.name for c in current_space().get(name).children) for name in family} == expected
