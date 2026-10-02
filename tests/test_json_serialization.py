import pytest
from kind import Kind
import orjson

# Assign the methods to Kind for testing purposes
Kind.to_json = Kind.to_json
Kind.from_json = Kind.from_json

def compare_kind_graphs(original_kinds_map: dict[str, Kind], reconstructed_kinds_map: dict[str, Kind]) -> bool:
    print(f"DEBUG: Original graph nodes: {sorted(original_kinds_map.keys())}")
    print(f"DEBUG: Reconstructed graph nodes: {sorted(reconstructed_kinds_map.keys())}")

    if len(original_kinds_map) != len(reconstructed_kinds_map):
        print(f"Node count mismatch: Original {len(original_kinds_map)}, Reconstructed {len(reconstructed_kinds_map)}")
        return False

    if set(original_kinds_map.keys()) != set(reconstructed_kinds_map.keys()):
        print(f"Node name mismatch: Original {set(original_kinds_map.keys())}, Reconstructed {set(reconstructed_kinds_map.keys())}")
        return False

    for name, orig_kind in original_kinds_map.items():
        reconstructed_kind = reconstructed_kinds_map[name]

        # Compare children
        orig_children_names = sorted([s.name for s in orig_kind.children])
        reconstructed_children_names = sorted([s.name for s in reconstructed_kind.children])
        if orig_children_names != reconstructed_children_names:
            print(f"Children mismatch for {name}: Original {orig_children_names}, Reconstructed {reconstructed_children_names}")
            return False

        # Compare relations (excluding inverse relations)
        orig_relations = {how: sorted([s.name for s in related_kinds])
                          for how, related_kinds in orig_kind.relations.items()
                          if not how.startswith('_inverse_')}
        reconstructed_relations = {how: sorted([s.name for s in related_kinds])
                                   for how, related_kinds in reconstructed_kind.relations.items()
                                   if not how.startswith('_inverse_')}
        if orig_relations != reconstructed_relations:
            print(f"Relations mismatch for {name}: Original {orig_relations}, Reconstructed {reconstructed_relations}")
            return False
    return True

def test_json_round_trip(kind_fixture):
    # 1. Generate a Kind graph using kind_fixture
    original_kinds = kind_fixture # This is already the dictionary of all kinds
    
    # Pick a root for serialization (any kind will do as to_json serializes the whole pool)
    original_root_for_serialization = next(iter(original_kinds.values()))

    print(f"DEBUG: Kind._pool size before serialization: {len(Kind._pool)}")

    # 2. Serialize the graph to a JSON string
    json_string = original_root_for_serialization.to_json()

    # 3. Deserialize the JSON string back into a new Kind graph
    # Clear the Kind._pool to ensure a fresh reconstruction
    Kind._pool.clear()
    print(f"DEBUG: Kind._pool size after clearing for deserialization: {len(Kind._pool)}")
    reconstructed_root = Kind.from_json(json_string) # This populates Kind._pool
    reconstructed_kinds = Kind._pool # Get the full pool of reconstructed kinds
    print(f"DEBUG: Kind._pool size after deserialization: {len(Kind._pool)}")

    # 4. Compare the original graph and the reconstructed graph
    assert compare_kind_graphs(original_kinds, reconstructed_kinds), "Reconstructed graph does not match original."

    # 5. Compare the original serialized string with a re-serialized string
    # Re-serialize the reconstructed graph (using any kind from the reconstructed pool)
    re_serialized_json_string = next(iter(reconstructed_kinds.values())).to_json()
    
    # Due to potential sorting differences in JSON dump, we load both and compare structures
    original_data = orjson.loads(json_string)
    re_serialized_data = orjson.loads(re_serialized_json_string)

    assert original_data == re_serialized_data, "Re-serialized JSON does not match original JSON structure."
