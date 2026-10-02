from kind.core.space import current_space
import pytest
from kind.core.base_kind import BaseKind as Kind, _to_kind

def test_kind_creation_and_interning():
    s1 = Kind("test_kind")
    s2 = Kind("test_kind")
    s3 = Kind("another_kind")

    assert s1 is s2
    assert s1 is not s3
    assert s1.name == "test_kind"
    assert s3.name == "another_kind"
    assert s1.origin is None
    assert s3.origin is None

def test_kind_creation_with_origin():
    obj = {"data": 123}
    s = Kind("test_origin", origin=obj)
    assert s.name == "test_origin"
    assert s.origin is obj

def test_kind_type_error_for_non_string_name():
    with pytest.raises(TypeError, match="Kind name must be a string"):
        Kind(123)
    with pytest.raises(TypeError, match="Kind name must be a string"):
        Kind(None)

def test_kind_position_assignment():
    s1 = Kind("pos_test_1")
    s2 = Kind("pos_test_2")
    s3 = Kind("pos_test_3")

    assert s1._position == 0.0
    assert s2._position == 1.0
    assert s3._position == 2.0

    # Verify write cursor advanced
    assert current_space()._write_cursor == 3.0  # the space's next creation position

def test_kind_pool_and_numbered_insertion():
    s1 = Kind("pool_test_1")
    s2 = Kind("pool_test_2")

    assert "pool_test_1" in current_space().pool
    assert current_space().pool["pool_test_1"] is s1
    assert "pool_test_2" in current_space().pool
    assert current_space().pool["pool_test_2"] is s2

    # Verify insertion into AVLTree
    inorder_traversal = current_space().order.traverse_inorder()
    assert len(inorder_traversal) == 2
    assert inorder_traversal[0] is s1
    assert inorder_traversal[1] is s2

def test_basekind_repr_and_str():
    s = Kind("repr_str_test")
    assert repr(s) == "BaseKind('repr_str_test')"
    assert str(s) == "repr_str_test"

def test_kind_equality_and_hashing():
    s1 = Kind("eq_hash_test")
    s2 = Kind("eq_hash_test")
    s3 = Kind("another_eq_hash_test")

    assert s1 == s2
    assert s1 != s3
    assert hash(s1) == hash(s2)
    assert hash(s1) != hash(s3)

def test_kind_less_than_comparison():
    s1 = Kind("lt_test_1")
    s2 = Kind("lt_test_2")
    s3 = Kind("lt_test_3")

    assert s1 < s2
    assert s2 < s3
    assert s1 < s3
    assert not (s2 < s1)



def test_to_kind_existing_kind():
    s_orig = Kind("existing")
    s_converted = _to_kind(s_orig)
    assert s_converted is s_orig

def test_to_kind_from_string():
    s_converted = _to_kind("from_string")
    assert isinstance(s_converted, Kind)
    assert s_converted.name == "from_string"

def test_to_kind_from_object_with_name_attribute():
    class HasName:
        def __init__(self, name):
            self.name = name
    obj = HasName("object_with_name")
    s_converted = _to_kind(obj)
    assert isinstance(s_converted, Kind)
    assert s_converted.name == "object_with_name"

def test_to_kind_type_error_for_unconvertible_type():
    with pytest.raises(TypeError, match="Cannot convert .* instance of .* to BaseKind"):
        _to_kind(123)
    with pytest.raises(TypeError, match="Cannot convert .* instance of .* to BaseKind"):
        _to_kind([1, 2])
    with pytest.raises(TypeError, match="Cannot convert .* instance of .* to BaseKind"):
        _to_kind(None)
