"""Round trips through JSON, YAML and TOML: a Kind serializes the graph it belongs to, and only that."""
from collections import deque

import orjson
import pytest

from kind.core.space import current_space
from kind.core.kind import tomllib  # stdlib on 3.11+, the tomli backport on 3.10
import yaml

from kind import Kind

FORMATS = {
    "json": (Kind.to_json, Kind.from_json, orjson.loads),
    "yaml": (Kind.to_yaml, Kind.from_yaml, yaml.safe_load),
    "toml": (Kind.to_toml, Kind.from_toml, lambda text: tomllib.loads(text)["kinds"]),
}


def connected_names(root: Kind) -> set[str]:
    """Independent oracle: names reachable over children, parents and relations in any direction."""
    seen, queue = {root}, deque([root])
    while queue:
        kind = queue.popleft()
        related = [r for _, kinds in kind.relations.items() for r in kinds]
        for neighbour in [*kind.children, *kind.parents, *related]:
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return {kind.name for kind in seen}


def edges(names: set[str], pool) -> dict:
    return {name: (sorted(c.name for c in pool[name].children),
                   {how: sorted(k.name for k in kinds) for how, kinds in pool[name].relations.items()
                    if not how.startswith("_inverse_")})
            for name in names}


@pytest.mark.parametrize("fmt", FORMATS)
def test_round_trip_rebuilds_the_connected_graph(fmt, kind_fixture, reset_pool):
    dump, load, parse = FORMATS[fmt]
    root = kind_fixture["Gene"]
    expected_names = connected_names(root)
    expected_edges = edges(expected_names, {k.name: k for k in kind_fixture.values()})
    text = dump(root)
    assert {node["name"] for node in parse(text)} == expected_names

    reset_pool()
    rebuilt_root = load(text)
    pool = current_space().pool
    assert set(pool) == expected_names
    assert edges(expected_names, pool) == expected_edges
    assert parse(dump(rebuilt_root)) == parse(text)


@pytest.mark.parametrize("fmt", FORMATS)
def test_dump_leaves_out_unconnected_kinds(fmt):
    dump, _, parse = FORMATS[fmt]
    a = Kind("a")
    a.append(Kind("b"))
    secret = Kind("unrelated secret")  # alive in the pool, not connected to a
    assert {node["name"] for node in parse(dump(a))} == {"a", "b"}
    assert secret.name in current_space().pool


@pytest.mark.parametrize("fmt", FORMATS)
def test_loading_merges_into_existing_kinds_by_name(fmt):
    """Interning is the point: a parsed name *is* the live Kind of that name."""
    dump, load, _ = FORMATS[fmt]
    victim = Kind("victim")
    text = dump(Kind("victim").add(Kind("evil")))
    victim.children.clear()
    Kind("evil").parents.clear()
    load(text)
    assert [child.name for child in victim.children] == ["evil"]


def test_load_rejects_empty_input():
    with pytest.raises(ValueError, match="No kinds found"):
        Kind.from_json("[]")
