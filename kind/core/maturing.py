"""This module implements the "maturing" process for Kind objects.

This process involves elevating metadata to first-class attributes and methods,
slimming down the object by removing unnecessary attributes, and freezing it to prevent further modifications.

The smooth merge strategy uses a recursive Depth-First Search (DFS) approach.
The merge proceeds by:
   1. Initializing merged with all items from current_value.
   2. Iterating through new_value:
       * If a key exists in merged:
           * If both values are mappings, a recursive call to _apply_merge_strategy is made.
           * If both values are lists, extend is used.
           * If both are non-mapping/non-list, the non_mapping_conflict_strategy is applied.
           * If types are mixed (one is mapping/list, the other is not), the new_value overwrites.
       * If a key does not exist in merged, the new_value is simply added.

"""
import copy
import logging
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Callable, Literal, TypeVar

log = logging.getLogger(__name__)

V = TypeVar('V')

class DefDict(defaultdict):
    """A defaultdict of defaultdicts, representing `defaultdict(defaultdict())`."""
    def __init__(self, default_factory: Callable[[], V] = lambda: defaultdict(dict), **kwargs):
        super().__init__(default_factory, **kwargs)

    def __repr__(self):
        return f"DefDict({super().__repr__()})"

    def __missing__(self, key):
        # This ensures that if a key is accessed and not found, a new defaultdict(dict) is created
        # and then returned, allowing for nested assignment like d['a']['b'] = 1
        value = self.default_factory()
        self[key] = value
        return value

    def __delitem__(self, key):
        """Deletes an item, raising KeyError with the key's name if it is missing."""
        if key not in self:
            raise KeyError(f"Key '{key}' not found in DefDict.")
        super().__delitem__(key)


def deep_del(obj: Any, attr: str) -> None:
    """Deletes an attribute and, if its value is a mapping, empties it first.

    Emptying drops the references the mapping holds even if something else still
    references the mapping itself; Python's GC reclaims the rest.
    """
    if not hasattr(obj, attr):
        log.warning(f"Attempted to deep_del non-existent attribute '{attr}' from {obj}")
        return
    value = getattr(obj, attr)
    delattr(obj, attr)
    if isinstance(value, dict):
        value.clear()


MergeStrategy = Literal['overwrite', 'patch', 'copy', 'deepcopy', 'pipe', 'update', 'extend', 'smooth']

def _apply_merge_strategy(current_value: Any, new_value: Any, strategy: MergeStrategy, non_mapping_conflict_strategy: Literal['overwrite', 'keep_current', 'raise_error', 'add_sibling'] = 'add_sibling') -> Any:
    """Applies a merge strategy to combine current and new values."""
    if strategy == 'overwrite':
        return new_value
    elif strategy == 'copy':
        return copy.copy(new_value)
    elif strategy == 'deepcopy':
        return copy.deepcopy(new_value)
    elif strategy == 'patch':
        # This assumes current_value is a Kind and new_value is a Kind
        # We need to import Kind here to avoid circular dependency if Kind is not yet defined
        from kind.core.kind import Kind 
        if isinstance(current_value, Kind) and isinstance(new_value, Kind):
            return current_value.patch(new_value)
        else:
            log.warning("Patch strategy only applies to Kind objects. Overwriting instead.")
            return new_value
    elif strategy == 'pipe':
        # Assumes new_value is a callable that takes current_value as input
        if callable(new_value):
            return new_value(current_value)
        else:
            log.warning("Pipe strategy requires new_value to be callable. Overwriting instead.")
            return new_value
    elif strategy == 'update':
        # Assumes both are dictionaries or have an update method
        if isinstance(current_value, Mapping) and isinstance(new_value, Mapping):
            current_value.update(new_value)
            return current_value
        else:
            log.warning("Update strategy only applies to mappings. Overwriting instead.")
            return new_value
    elif strategy == 'extend':
        # Assumes both are lists or have an extend method
        if isinstance(current_value, list) and isinstance(new_value, list):
            current_value.extend(new_value)
            return current_value
        else:
            log.warning("Extend strategy only applies to lists. Overwriting instead.")
            return new_value
    elif strategy == 'smooth':
        if isinstance(current_value, Mapping) and isinstance(new_value, Mapping):
            merged = type(current_value)() # Preserve type (e.g., dict, defaultdict)
            # Start with all items from current_value
            for k, v in current_value.items():
                merged[k] = v

            # Iterate through new_value and merge
            for k, v in new_value.items():
                if k in merged:
                    # If both are mappings, recursively merge
                    if isinstance(merged[k], Mapping) and isinstance(v, Mapping):
                        merged[k] = _apply_merge_strategy(merged[k], v, 'smooth', non_mapping_conflict_strategy)
                    # If both are lists, extend
                    elif isinstance(merged[k], list) and isinstance(v, list):
                        merged[k].extend(v)
                    # Handle other non-mapping conflicts
                    elif not isinstance(merged[k], Mapping) and not isinstance(v, Mapping):
                        if non_mapping_conflict_strategy == 'overwrite':
                            merged[k] = v
                        elif non_mapping_conflict_strategy == 'keep_current':
                            pass
                        elif non_mapping_conflict_strategy == 'raise_error':
                            raise ValueError(f"Conflict for key '{k}': Cannot merge non-mapping types with 'raise_error' strategy.")
                        elif non_mapping_conflict_strategy == 'add_sibling':
                            log.info(f"Smooth merge: Key '{k}' exists and is not a mapping. Adding as sibling.")
                            merged[f'{k}_new'] = v
                        else:
                            log.warning(f"Unknown non-mapping conflict strategy '{non_mapping_conflict_strategy}'. Overwriting instead.")
                            merged[k] = v
                    else:
                        # One is mapping/list, other is not - overwrite
                        merged[k] = v
                else:
                    # Key not in current_value, just add
                    merged[k] = v
            return merged
        else:
            log.warning("Smooth merge: Non-mapping types. Overwriting instead.")
            return new_value
    else:
        log.warning(f"Unknown merge strategy '{strategy}'. Overwriting instead.")
        return new_value
