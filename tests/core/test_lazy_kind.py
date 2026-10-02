import pytest
from kind import Kind
from core.lazy_kind import LazyKind

def test_lazy_kind_evaluation():
    # Create a list that will be converted to a Kind with LazyKind children
    my_list = [1, 2, 3]

    # Convert the list to a Kind. This should return a concrete Kind.
    list_kind = Kind.from_object(my_list)

    # The list_kind itself should be a Kind instance
    assert isinstance(list_kind, Kind)

    # Its children should be LazyKind instances
    assert len(list_kind.children) == 3
    assert all(isinstance(child, LazyKind) for child in list_kind.children)

    # Access an attribute of the first child to trigger its evaluation
    first_child_lazy = list_kind.children[0]
    _ = first_child_lazy.name

    # Now, the first child should be a concrete Kind instance
    assert isinstance(first_child_lazy._kind, Kind)
    assert first_child_lazy._kind.name == "1"

    # The other children should still be LazyKind instances
    assert isinstance(list_kind.children[1], LazyKind)
    assert isinstance(list_kind.children[2], LazyKind)
