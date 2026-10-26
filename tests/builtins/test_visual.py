import shutil

import pytest

from kind import Kind
from kind.builtin.visual import KindRender, from_mmd

needs_dot = pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz 'dot' executable not on PATH")


@pytest.fixture
def simple_kind_tree():
    # A -> B -> D, A -> C
    a, b, c, d = Kind("A"), Kind("B"), Kind("C"), Kind("D")
    a.append(b)
    a.append(c)
    b.append(d)
    return a, b, c, d


def test_to_mmd_simple_tree(simple_kind_tree):
    a, *_ = simple_kind_tree
    assert a.to_mmd() == "\n".join([
        "graph LR",
        "A[A]", "B[B]", "C[C]", "D[D]",
        "    A --> B",
        "    B --> D",
        "    A --> C",
    ])


def test_to_mmd_cycle_emits_every_edge_once():
    a, b, c, d = (Kind(f"{n}_graph") for n in "ABCD")
    a.append(b)
    b.append(c)
    c.append(d)
    d.append(a)
    edges = [line.strip() for line in a.to_mmd().splitlines() if "-->" in line]
    assert sorted(edges) == ["A_graph --> B_graph", "B_graph --> C_graph", "C_graph --> D_graph", "D_graph --> A_graph"]


def test_to_mmd_shapes_and_relations():
    a, b = Kind("Alpha One"), Kind("Beta")
    a.node_shape = "subroutine"
    b.node_shape = "circle"
    a.relate(b, how="uses")
    mmd = a.to_mmd()
    assert "Alpha_One[[Alpha One]]" in mmd
    assert "Beta((Beta))" in mmd
    assert "    Alpha_One -- uses --> Beta" in mmd


def test_from_mmd_round_trip_keeps_names_shapes_children_and_relations(simple_kind_tree, reset_pool):
    a, b, *_ = simple_kind_tree
    a.node_shape = "rhombus"
    b.relate(Kind("Spaced Name"), how="refers to")
    mmd = a.to_mmd()
    reset_pool()

    root = from_mmd(mmd)
    assert root.name == "A"
    assert root.node_shape == "rhombus"
    assert [child.name for child in root.children] == ["B", "C"]
    rebuilt_b = root.children[0]
    assert [child.name for child in rebuilt_b.children] == ["D"]
    assert [k.name for k in rebuilt_b.relations.get("refers to")] == ["Spaced Name"]
    assert root.to_mmd() == mmd


def test_from_mmd_is_available_on_kind():
    mmd = "graph LR\n    X --> Y"
    assert Kind.from_mmd(mmd).children[0].name == "Y"


def test_to_mmd_quotes_unsafe_names_with_stable_ids():
    root = Kind("interactive/norm")
    root.append(Kind('SIGN IN with password! (#1) "now"'))
    mmd = root.to_mmd()
    lines = mmd.splitlines()
    assert any(line.endswith('["SIGN IN with password! (#35;1) #quot;now#quot;"]') for line in lines)
    assert any(line.endswith('["interactive/norm"]') for line in lines)
    for line in lines[1:]:  # every node id is [A-Za-z0-9_] only
        assert line.strip().split("[")[0].split(" ")[0].replace("_", "").isalnum()
    assert root.to_mmd() == mmd  # stable across calls (sha256 suffix, not hash())


def test_to_mmd_separates_colliding_ids_and_the_reserved_word_end():
    root = Kind("root")
    root.append(Kind("A B"))
    root.append(Kind("A_B"))
    root.append(Kind("end"))
    declarations = [line for line in root.to_mmd().splitlines()[1:] if "-->" not in line]
    ids = [line.split("[")[0] for line in declarations]
    assert len(set(ids)) == len(ids) == 4
    assert "A_B[A_B]" in declarations  # the exact name keeps its plain id
    assert "end" not in ids


def test_from_mmd_round_trip_of_unsafe_names(reset_pool):
    names = ['SIGN IN with password!', 'a "quoted" #tag', 'two\nlines', 'A B', 'A_B', 'end']
    root = Kind("interactive/auth")
    for name in names:
        root.append(Kind(name))
    mmd = root.to_mmd()
    reset_pool()

    rebuilt = from_mmd(mmd)
    assert rebuilt.name == "interactive/auth"
    assert [child.name for child in rebuilt.children] == names
    assert rebuilt.to_mmd() == mmd


def test_to_dot_escapes_quotes_and_backslashes():
    evil = Kind('x" [image="/etc/passwd"] "y\\')
    root = Kind("root")
    root.append(evil)
    dot = root.to_dot()
    assert 'image=' in dot  # the text is kept ...
    assert '"x\\" [image=\\"/etc/passwd\\"] \\"y\\\\"' in dot  # ... but only inside one quoted ID


def test_to_dot_graph_mode_includes_relations():
    a, b = Kind("a"), Kind("b")
    a.relate(b, how="likes")
    assert '"a" -> "b" [label="likes"]' in a.to_dot(mode="graph")
    assert "likes" not in a.to_dot(mode="tree")


def test_to_dot_survives_deep_chains():
    root = node = Kind("n0")
    for i in range(1, 5000):
        node = node.append(Kind(f"n{i}"))
    assert root.to_dot().count("->") == 4999


@needs_dot
def test_to_svg_and_png(simple_kind_tree):
    a, *_ = simple_kind_tree
    svg = KindRender(a).to_svg()
    assert "<svg" in svg and ">D<" in svg
    assert a.to_png().startswith(b"\x89PNG")


@needs_dot
@pytest.mark.anyio
async def test_a_to_svg(simple_kind_tree):
    a, *_ = simple_kind_tree
    assert "<svg" in await KindRender(a).a_to_svg()


def test_to_mmd_direction_td_changes_only_the_header():
    a = Kind("dir_a")
    a.append(Kind("dir_b"))
    left, down = a.to_mmd(), a.to_mmd(direction="TD")
    assert left.startswith("graph LR\n") and down.startswith("graph TD\n")
    assert left.split("\n", 1)[1] == down.split("\n", 1)[1]
    assert from_mmd(down).to_mmd(direction="TD") == down
    with pytest.raises(ValueError):
        a.to_mmd(direction="RL")
