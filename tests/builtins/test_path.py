import pytest
from kind import Kind
from builtin.path import KindPathMixin

# Apply the mixin to Kind for testing purposes
# In a real application, this would be handled by apply_builtins
Kind.path_to = KindPathMixin.path_to
Kind.match = KindPathMixin.match

@pytest.fixture
def simple_graph():
    # A -> B -> C
    # A -> D
    a = Kind("A")
    b = Kind("B")
    c = Kind("C")
    d = Kind("D")

    a.append(b)
    b.append(c)
    a.append(d)
    return a, b, c, d

@pytest.fixture
def disconnected_graph():
    # These kinds are not connected to each other, nor to simple_graph
    x = Kind("X_disconnected")
    y = Kind("Y_disconnected")
    z = Kind("Z_disconnected")
    return x, y, z

@pytest.fixture
def cyclic_graph():
    # A -> B -> C -> A (cycle)
    a = Kind("A_cycle")
    b = Kind("B_cycle")
    c = Kind("C_cycle")

    a.append(b)
    b.append(c)
    c.append(a)
    return a, b, c

def test_path_to_direct_path(simple_graph):
    a, b, c, d = simple_graph
    path = a.path_to(c)
    assert path == [a, b, c]

def test_path_to_no_path(simple_graph, disconnected_graph):
    a, b, c, d = simple_graph
    _, _, z = disconnected_graph # z is not connected to a
    path = a.path_to(z)
    assert path == []

def test_path_to_self(simple_graph):
    a, _, _, _ = simple_graph
    path = a.path_to(a)
    assert path == [a]

def test_path_to_with_cycle(cyclic_graph):
    a, b, c = cyclic_graph
    # Path from A to C should still be found, DFS handles visited nodes
    path = a.path_to(c)
    assert path == [a, b, c]

def test_match_dfs(simple_graph):
    a, b, c, d = simple_graph
    # Predicate: name starts with 'B' or 'C'
    predicate = lambda kind: kind.name.startswith("B") or kind.name.startswith("C")
    matched_kinds = list(a.match(predicate, traversal='dfs'))
    # DFS order: A, B, C, D. Matches: B, C
    assert matched_kinds == [b, c]

def test_match_bfs(simple_graph):
    a, b, c, d = simple_graph
    # Predicate: name starts with 'B' or 'D'
    predicate = lambda kind: kind.name.startswith("B") or kind.name.startswith("D")
    matched_kinds = list(a.match(predicate, traversal='bfs'))
    # BFS order: A, B, D, C. Matches: B, D
    assert matched_kinds == [b, d]

def test_match_no_match(simple_graph):
    a, _, _, _ = simple_graph
    predicate = lambda kind: kind.name == "Z"
    matched_kinds = list(a.match(predicate))
    assert matched_kinds == []

def test_match_all_match(simple_graph):
    a, b, c, d = simple_graph
    predicate = lambda kind: True
    matched_kinds = list(a.match(predicate, traversal='dfs'))
    assert set(matched_kinds) == {a, b, c, d}
