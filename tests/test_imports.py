"""Import side effects, measured in a fresh interpreter.

Both properties below describe the intended lazy loading of builtins
(see "lazy loaded" in kind/__init__.py), which is not implemented:
`import kind` eagerly imports kind.core and kind.builtin and applies the
builtin mixins. They are strict xfails so that implementing lazy loading
turns them red, and they get promoted to plain tests.

Until the package switched to absolute imports, these tests ran in the
pytest process and checked `kind.*` names in sys.modules while the code
was loaded as top-level `core`/`builtin`, so they passed whatever the
behaviour was.
"""
import subprocess
import sys

import pytest

LAZY_BUILTINS_NOT_IMPLEMENTED = "kind/__init__.py imports core and builtin eagerly"


def loaded_modules_after(statement: str, module_names: list[str]) -> dict[str, bool]:
    probe = (
        f"import sys\n{statement}\n"
        f"print(','.join(str(name in sys.modules) for name in {module_names!r}))"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)
    return dict(zip(module_names, (flag == "True" for flag in result.stdout.strip().split(","))))


@pytest.mark.xfail(strict=True, reason=LAZY_BUILTINS_NOT_IMPLEMENTED)
def test_core_modules_do_not_import_time_dim():
    loaded = loaded_modules_after(
        "from kind.core import kind, schedule, protocols, time_arithmetics",
        ["kind.builtin.time_dim"],
    )
    assert not loaded["kind.builtin.time_dim"]


@pytest.mark.xfail(strict=True, reason=LAZY_BUILTINS_NOT_IMPLEMENTED)
def test_importing_kind_defers_builtins():
    loaded = loaded_modules_after("import kind", ["kind.builtin.time_dim", "kind.builtin.visual"])
    assert not any(loaded.values())
