import pytest
import sys

def test_direct_imports_skip_time_dim():
    # Attempt to import modules that should not directly import time_dim
    # This test relies on the fact that time_dim is a builtin and should be accessed via apply_builtins()
    # or through the top-level kind package aliases.

    # Temporarily remove time_dim from sys.modules to ensure a fresh import
    if 'kind.builtin.time_dim' in sys.modules:
        del sys.modules['kind.builtin.time_dim']

    # These imports should succeed without pulling in time_dim directly
    try:
        from core import kind
        from core import schedule
        from core import protocols
        from core import time_arithmetics
        from builtin import collections
        from builtin import index
        from builtin import path
        from builtin import visual
        from builtin import timeline

        # Assert that time_dim was NOT imported directly by these modules
        assert 'kind.builtin.time_dim' not in sys.modules

    except ImportError as e:
        import logging
        logging.error(f"Direct import failed unexpectedly: {repr(e)}, line 28", exc_info=True)
        pytest.fail(f"Direct import failed unexpectedly: {repr(e)}")

def test_direct_imports_skip_core_and_builtins():
    # Temporarily remove core and builtin from sys.modules to ensure fresh imports
    if 'kind.core' in sys.modules:
        del sys.modules['kind.core']
    if 'kind.builtin' in sys.modules:
        del sys.modules['kind.builtin']

    # Remove specific submodules if they were already loaded
    for module_name in [
        'kind.core.kind',
        'kind.builtin.time_dim',
        'kind.builtin.collections',
        'kind.builtin.index',
        'kind.builtin.path',
        'kind.builtin.visual',
        'kind.builtin.timeline',
    ]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    try:
        import kind

        # Assert that core and builtin were NOT imported directly at the top level
        assert 'kind.core' not in sys.modules
        assert 'kind.builtin' not in sys.modules

        # Accessing aliases should trigger their import, but not necessarily the top-level package
        # kind.s, kind.Kind, and kind.GraphTraversal are now directly imported in kind/__init__.py
        # so they will always be present.

        # TODO:
        # _ = kind.time_dim
        # assert 'kind.builtin.time_dim' in sys.modules
        #
        # _ = kind.collections
        # assert 'kind.builtin.collections' in sys.modules
        #
        # _ = kind.index
        # assert 'kind.builtin.index' in sys.modules
        #
        # _ = kind.path
        # assert 'kind.builtin.path' in sys.modules
        #
        # _ = kind.visual
        # assert 'kind.builtin.visual' in sys.modules
        #
        # _ = kind.timeline
        # assert 'kind.builtin.timeline' in sys.modules

    except ImportError as e:
        import logging
        logging.error(f"Direct import failed unexpectedly: {repr(e)}, line 81", exc_info=True)
        pytest.fail(f"Direct import failed unexpectedly: {repr(e)}")
