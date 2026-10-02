import pytest
from kind import Kind
from kind.builtin.index import KindIndex

@pytest.fixture
def owner_kind():
    return Kind("owner_index")

@pytest.fixture
def empty_kind_index(owner_kind):
    return KindIndex(owner_kind)

def test_kind_index_instantiation(owner_kind):
    index = KindIndex(owner_kind)
    assert index.owner == owner_kind
    assert index.tree.root is None

def test_kind_index_insertion(empty_kind_index):
    s1 = Kind("kind1")
    s2 = Kind("kind2")
    s3 = Kind("kind3")

    empty_kind_index.insert(s2, 50.0) # Root
    empty_kind_index.insert(s1, 25.0) # Left child
    empty_kind_index.insert(s3, 75.0) # Right child

    # In-order traversal should return kinds sorted by weight
    inorder = empty_kind_index.traverse(order="in")
    assert inorder == [s1, s2, s3]

    # Test inserting with callable weight
    s4 = Kind("kind4")
    def dynamic_weight(kind):
        return len(kind.name) * 2
    empty_kind_index.insert(s4, dynamic_weight)
    # Verify that the kind is in the tree and its weight is correctly evaluated
    assert empty_kind_index.tree.search(dynamic_weight(s4)) is s4

def test_kind_index_traverse_inorder(empty_kind_index):
    s_nodes = [
        (Kind("kind_d"), 40.0),
        (Kind("kind_b"), 20.0),
        (Kind("kind_f"), 60.0),
        (Kind("kind_a"), 10.0),
        (Kind("kind_c"), 30.0),
        (Kind("kind_e"), 50.0),
        (Kind("kind_g"), 70.0),
    ]
    for kind, weight in s_nodes:
        empty_kind_index.insert(kind, weight)

    expected_inorder = [
        Kind("kind_a"), Kind("kind_b"), Kind("kind_c"), Kind("kind_d"),
        Kind("kind_e"), Kind("kind_f"), Kind("kind_g")
    ]
    actual_inorder = empty_kind_index.traverse(order="in")
    assert actual_inorder == expected_inorder

def test_kind_index_map_and_filter(empty_kind_index):
    s_nodes = [
        (Kind("apple"), 10.0),
        (Kind("banana"), 20.0),
        (Kind("cherry"), 30.0),
    ]
    for kind, weight in s_nodes:
        empty_kind_index.insert(kind, weight)

    # Test map
    mapped_names = empty_kind_index.map(lambda s: s.name.upper())
    assert mapped_names == ["APPLE", "BANANA", "CHERRY"]

    # Test filter
    filtered_kinds = empty_kind_index.filter(lambda s: "a" in s.name)
    assert filtered_kinds == [Kind("apple"), Kind("banana")]

def test_kind_index_ascii_representation(empty_kind_index):
    s_nodes = [
        (Kind("root"), 50.0),
        (Kind("left"), 25.0),
        (Kind("right"), 75.0),
    ]
    for kind, weight in s_nodes:
        empty_kind_index.insert(kind, weight)

    expected_ascii = """  - right (W:75.00, H:1)
- root (W:50.00, H:2)
  - left (W:25.00, H:1)"""
    assert empty_kind_index.ascii() == expected_ascii
    assert empty_kind_index.to_ascii() == expected_ascii

