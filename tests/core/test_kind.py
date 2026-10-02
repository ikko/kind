import pytest
from kind.core.kind import Kind
from kind.core.kind_namespace import k
from kind.core.lazy_kind import SENTINEL

class NonConvertibleObject:
    pass

def test_kind_index_property():
    kind = Kind("test_index")
    assert kind._index is SENTINEL
    index_obj = kind.index
    assert index_obj is not SENTINEL
    assert kind._index is index_obj
    # Ensure it's a KindIndex instance (or its mock if mocked)
    assert hasattr(index_obj, 'insert') # Basic check for KindIndex methods

def test_kind_metadata_property():
    kind = Kind("test_metadata")
    assert kind._metadata is SENTINEL
    metadata_obj = kind.metadata
    assert metadata_obj is not SENTINEL
    assert kind._metadata is metadata_obj
    # Ensure it's a DefDict instance (or its mock if mocked)
    assert hasattr(metadata_obj, '__setitem__') # Basic check for DefDict methods

def test_kind_context_property():
    kind = Kind("test_context")
    assert kind._context is SENTINEL
    context_obj = kind.context
    assert context_obj is not SENTINEL
    assert kind._context is context_obj
    # Ensure it's a DefDict instance (or its mock if mocked)
    assert hasattr(context_obj, '__setitem__') # Basic check for DefDict methods

def test_kind_elevated_attributes_set_and_get():
    kind = Kind("test_elevated_attrs")
    kind.dynamic_attr = "value1"
    assert kind.dynamic_attr == "value1"
    assert kind._elevated_attributes["dynamic_attr"] == "value1"

def test_kind_elevated_attributes_overwrite_existing():
    kind = Kind("test_elevated_attrs_overwrite")
    kind.dynamic_attr = "original_value"
    kind.dynamic_attr = "new_value"
    assert kind.dynamic_attr == "new_value"
    assert kind._elevated_attributes["dynamic_attr"] == "new_value"

def test_kind_elevated_attributes_delete():
    kind = Kind("test_elevated_attrs_delete")
    kind.temp_attr = "to_delete"
    assert kind.temp_attr == "to_delete"
    del kind.temp_attr
    assert "temp_attr" not in kind._elevated_attributes
    assert callable(kind.temp_attr)

def test_kind_elevated_attributes_delete_non_existent():
    kind = Kind("test_elevated_attrs_delete_non_existent")
    with pytest.raises(AttributeError):
        del kind.non_existent_attr

def test_kind_append_child():
    parent = Kind("parent")
    child = Kind("child")
    parent.append(child)
    assert child in parent.children
    assert parent in child.parents

def test_kind_append_lazy_kind_child():
    from kind.core.lazy_kind import LazyKind
    parent = Kind("parent_lazy")
    lazy_child = LazyKind("lazy_child_name")
    parent.append(lazy_child)
    assert lazy_child in parent.children
    assert parent in lazy_child.parents

def test_kind_append_non_kind_object():
    parent = Kind("parent_non_kind")
    non_kind_obj = "string_child"
    child_kind = parent.append(non_kind_obj)
    assert isinstance(child_kind, Kind)
    assert child_kind.name == "string_child"
    assert child_kind in parent.children
    assert parent in child_kind.parents

def test_kind_append_duplicate_child():
    parent = Kind("parent_duplicate")
    child = Kind("child_duplicate")
    parent.append(child)
    initial_children_len = len(parent.children)
    parent.append(child) # Appending again should not add duplicate
    assert len(parent.children) == initial_children_len

def test_kind_add_child():
    parent = Kind("parent_add")
    child = Kind("child_add")
    parent.add(child)
    assert child in parent.children
    assert parent in child.parents

def test_kind_add_duplicate_child():
    parent = Kind("parent_add_duplicate")
    child = Kind("child_add_duplicate")
    parent.add(child)
    initial_children_len = len(parent.children)
    parent.add(child) # Adding again should not add duplicate
    assert len(parent.children) == initial_children_len

def test_kind_relate_unrelate():
    s1 = Kind("s1_relate")
    s2 = Kind("s2_relate")

    s1.relate(s2, how="friend")
    assert s2 in s1.relations.get("friend")
    assert s1 in s2.relations.get("_inverse_friend")

    s1.unrelate(s2)
    assert s2 not in s1.relations.get("friend")
    assert s1 not in s2.relations.get("_inverse_friend")

def test_kind_relate_with_specific_how():
    s1 = Kind("s1_how")
    s2 = Kind("s2_how")
    s1.relate(s2, how="parent_of")
    assert s2 in s1.relations.get("parent_of")
    assert s1 in s2.relations.get("_inverse_parent_of")

def test_kind_unrelate_with_specific_how():
    s1 = Kind("s1_unrelate_how")
    s2 = Kind("s2_unrelate_how")
    s1.relate(s2, how="knows")
    s1.relate(s2, how="likes") # Add another relationship

    s1.unrelate(s2, how="knows")
    assert s2 not in s1.relations.get("knows")
    assert s2 in s1.relations.get("likes")

    # Ensure inverse is also removed correctly
    assert s1 not in s2.relations.get("_inverse_knows")
    assert s1 in s2.relations.get("_inverse_likes")

def test_dynamic_relation_single_arg():
    s_person = k.person
    s_car = k.car
    s_person.drives(s_car)
    assert s_car in s_person.relations.get("drives")
    assert s_person in s_car.relations.get("_inverse_drives")

def test_dynamic_relation_multiple_args():
    s_person = k.person
    s_drums = k.drums
    s_guitar = k.guitar
    s_person.interested_in(s_drums, s_guitar)
    assert s_drums in s_person.relations.get("interested_in")
    assert s_guitar in s_person.relations.get("interested_in")
    assert s_person in s_drums.relations.get("_inverse_interested_in")
    assert s_person in s_guitar.relations.get("_inverse_interested_in")

def test_dynamic_relation_kwargs_single_value():
    s_person = k.person
    s_war_zones = k.war_zones
    s_person.avoids(war_zones=s_war_zones)
    assert s_war_zones in s_person.relations.get("war_zones")
    assert s_person in s_war_zones.relations.get("_inverse_war_zones")

def test_dynamic_relation_kwargs_list_value():
    s_musical_track = k.musical_track
    s_musician_joe = k.musician_joe
    s_song_writer_jane = k.song_writer_jane
    s_musical_track.authored_by(authors=[s_musician_joe, s_song_writer_jane])
    assert s_musician_joe in s_musical_track.relations.get("authors")
    assert s_song_writer_jane in s_musical_track.relations.get("authors")
    assert s_musical_track in s_musician_joe.relations.get("_inverse_authors")
    assert s_musical_track in s_song_writer_jane.relations.get("_inverse_authors")

def test_dynamic_relation_mixed_args_kwargs():
    s_person = k.person
    s_drums = k.drums
    s_guitar = k.guitar
    s_singing = k.singing
    s_dancing = k.dancing
    s_war_zones = k.war_zones

    s_person.interested_in(s_drums, s_guitar, likes=[s_singing, s_dancing], avoids=s_war_zones)

    assert s_drums in s_person.relations.get("interested_in")
    assert s_guitar in s_person.relations.get("interested_in")
    assert s_singing in s_person.relations.get("likes")
    assert s_dancing in s_person.relations.get("likes")
    assert s_war_zones in s_person.relations.get("avoids")

    assert s_person in s_drums.relations.get("_inverse_interested_in")
    assert s_person in s_guitar.relations.get("_inverse_interested_in")
    assert s_person in s_singing.relations.get("_inverse_likes")
    assert s_person in s_dancing.relations.get("_inverse_likes")
    assert s_person in s_war_zones.relations.get("_inverse_avoids")

def test_dynamic_relation_chained_calls():
    s_person = k.person
    s_drums = k.drums
    s_guitar = k.guitar
    s_singing = k.singing
    s_dancing = k.dancing
    s_war_zones = k.war_zones

    s_person.interested_in(s_drums, s_guitar).likes(s_singing, s_dancing).avoids(s_war_zones)

    assert s_drums in s_person.relations.get("interested_in")
    assert s_guitar in s_person.relations.get("interested_in")
    assert s_singing in s_person.relations.get("likes")
    assert s_dancing in s_person.relations.get("likes")
    assert s_war_zones in s_person.relations.get("avoids")

    assert s_person in s_drums.relations.get("_inverse_interested_in")
    assert s_person in s_guitar.relations.get("_inverse_interested_in")
    assert s_person in s_singing.relations.get("_inverse_likes")
    assert s_person in s_dancing.relations.get("_inverse_likes")
    assert s_person in s_war_zones.relations.get("_inverse_avoids")

def test_dynamic_relation_no_args_raises_error():
    s_person = k.person
    with pytest.raises(TypeError):
        s_person.some_relation()

def test_dynamic_relation_non_kind_args_raises_error():
    s_person = k.person
    non_convertible = NonConvertibleObject()
    with pytest.raises(TypeError):
        s_person.some_relation(non_convertible)

def test_dynamic_relation_kwargs_non_kind_value_raises_error():
    s_person = k.person
    non_convertible = NonConvertibleObject()
    with pytest.raises(TypeError):
        s_person.some_relation(item=non_convertible)

def test_dynamic_relation_kwargs_list_non_kind_value_raises_error():
    s_person = k.person
    non_convertible = NonConvertibleObject()
    with pytest.raises(TypeError):
        s_person.some_relation(items=[non_convertible])

def test_to_ascii_default_tree_traversal():
    # Create a simple tree structure
    root = Kind("Root")
    child1 = Kind("Child1")
    child2 = Kind("Child2")
    grandchild1 = Kind("Grandchild1")

    root.append(child1)
    root.append(child2)
    child1.append(grandchild1)

    expected_output = """
- Root
  - Child1
    - Grandchild1
  - Child2
""".strip()
    
    assert root.to_ascii() == expected_output

def test_to_ascii_dfs_children_first():
    root = Kind("A")
    b = Kind("B")
    c = Kind("C")
    d = Kind("D")
    e = Kind("E")

    root.append(b)
    root.append(c)
    b.append(d)
    c.append(e)

    # Expected DFS (children first) output
    expected_output = """
- A
  - B
    - D
  - C
    - E
""".strip()
    assert root.to_ascii(traverse_mode="dfs", family_mode="children_first") == expected_output

def test_to_ascii_bfs_children_first():
    root = Kind("A")
    b = Kind("B")
    c = Kind("C")
    d = Kind("D")
    e = Kind("E")

    root.append(b)
    root.append(c)
    b.append(d)
    c.append(e)

    # Expected BFS (children first) output
    expected_output = """
- A
  - B
  - C
    - D
    - E
""".strip()
    assert root.to_ascii(traverse_mode="bfs", family_mode="children_first") == expected_output


def test_to_ascii_with_relations():
    s1 = Kind("S1")
    s2 = Kind("S2")
    s3 = Kind("S3")
    s4 = Kind("S4")

    s1.append(s2)
    s1.relate(s3, how="knows")
    s2.relate(s4, how="has_child")

    expected_output = """
- S1
  - S2

--- Relations ---
S1 --knows--> S3
S2 --has_child--> S4
""".strip()
    assert s1.to_ascii() == expected_output

def test_from_ascii_simple_tree():
    ascii_input = """
- Root
  - Child1
    - Grandchild1
  - Child2
""".strip()
    
    reconstructed_root = Kind.from_ascii(ascii_input)

    assert reconstructed_root.name == "Root"
    assert len(reconstructed_root.children) == 2
    assert reconstructed_root.children[0].name == "Child1"
    assert reconstructed_root.children[1].name == "Child2"
    assert len(reconstructed_root.children[0].children) == 1
    assert reconstructed_root.children[0].children[0].name == "Grandchild1"

def test_from_ascii_with_relations():
    ascii_input = """
- S1
  - S2
    - S4

--- Relations ---
S1 --knows--> S3
S2 --has_child--> S4
""".strip()

    reconstructed_s1 = Kind.from_ascii(ascii_input)

    assert reconstructed_s1.name == "S1"
    assert len(reconstructed_s1.children) == 1
    reconstructed_s2 = reconstructed_s1.children[0]
    assert reconstructed_s2.name == "S2"
    assert len(reconstructed_s2.children) == 1
    reconstructed_s4 = reconstructed_s2.children[0]
    assert reconstructed_s4.name == "S4"

    # Check relations
    reconstructed_s3 = Kind._pool.get("S3") # Relations are global, so retrieve from pool
    assert reconstructed_s3 is not None
    assert reconstructed_s3 in reconstructed_s1.relations.get("knows")
    assert reconstructed_s1 in reconstructed_s3.relations.get("_inverse_knows")

    assert reconstructed_s4 in reconstructed_s2.relations.get("has_child")
    assert reconstructed_s2 in reconstructed_s4.relations.get("_inverse_has_child")

def test_roundtrip_simple_tree():
    root = Kind("Root")
    child1 = Kind("Child1")
    child2 = Kind("Child2")
    grandchild1 = Kind("Grandchild1")

    root.append(child1)
    root.append(child2)
    child1.append(grandchild1)

    ascii_output = root.to_ascii()
    reconstructed_root = Kind.from_ascii(ascii_output)

    assert reconstructed_root.name == root.name
    assert len(reconstructed_root.children) == len(root.children)
    assert reconstructed_root.children[0].name == root.children[0].name
    assert reconstructed_root.children[1].name == root.children[1].name
    assert reconstructed_root.children[0].children[0].name == root.children[0].children[0].name

def test_roundtrip_with_relations(reset_pool):
    s1, s2, s3, s4 = (Kind(f"S{i}") for i in range(1, 5))
    s1.append(s2)
    s1.relate(s3, how="knows")
    s2.relate(s4, how="has_child")  # a relation named like a link is still a relation
    ascii_output = s1.to_ascii()

    reset_pool()
    root = Kind.from_ascii(ascii_output)
    assert root is not s1 and root.name == "S1"
    assert [c.name for c in root.children] == ["S2"]
    rebuilt_s2 = root.children[0]
    assert list(rebuilt_s2.children) == []
    assert [k.name for k in root.relations.get("knows")] == ["S3"]
    assert [k.name for k in rebuilt_s2.relations.get("has_child")] == ["S4"]
    assert rebuilt_s2 in Kind("S4").relations.get("_inverse_has_child")
    assert root.to_ascii() == ascii_output
