from kind import Kind
from kind.builtin.collections import OrderedKindSet

def test_ordered_kind_set_creation_and_add():
    # Test creation with no initial kinds
    s_set = OrderedKindSet()
    assert len(s_set) == 0

    # Test adding a single kind
    kind1 = Kind("kind1")
    s_set.add(kind1)
    assert len(s_set) == 1
    assert kind1 in s_set

    # Test adding multiple kinds
    kind2 = Kind("kind2")
    kind3 = Kind("kind3")
    s_set.add(kind2)
    s_set.add(kind3)
    assert len(s_set) == 3
    assert kind2 in s_set
    assert kind3 in s_set

    # Test adding an existing kind (should not increase size)
    s_set.add(kind1)
    assert len(s_set) == 3

    # Test creation with initial kinds
    kind4 = Kind("kind4")
    kind5 = Kind("kind5")
    s_set2 = OrderedKindSet([kind4, kind5])
    assert len(s_set2) == 2
    assert kind4 in s_set2
    assert kind5 in s_set2

def test_ordered_kind_set_iteration_length_and_containment():
    kind1 = Kind("alpha")
    kind2 = Kind("beta")
    kind3 = Kind("gamma")
    s_set = OrderedKindSet([kind1, kind2, kind3])

    # Test length
    assert len(s_set) == 3

    # Test iteration order (should be insertion order)
    expected_order = [kind1, kind2, kind3]
    actual_order = list(s_set)
    assert actual_order == expected_order

    # Test containment
    assert kind1 in s_set
    assert Kind("alpha") in s_set # Should work due to Kind interning
    assert Kind("non_existent") not in s_set

    # Test iteration after adding more elements
    kind4 = Kind("delta")
    s_set.add(kind4)
    expected_order_after_add = [kind1, kind2, kind3, kind4]
    assert list(s_set) == expected_order_after_add

    # Test iteration after removing elements (if remove method exists)
    # Assuming a remove method will be added later if needed for full coverage
