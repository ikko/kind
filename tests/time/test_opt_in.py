"""kind.time is opt-in: the core attaches no time properties until it is imported."""
import subprocess
import sys

PROBE = """
import kind
from kind.core.base_kind import BaseKind
before = 'as_date' in vars(BaseKind)
{enable}
after = 'as_date' in vars(BaseKind)
print(before, after)
"""


def run(enable: str) -> str:
    result = subprocess.run([sys.executable, "-c", PROBE.format(enable=enable)], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_core_alone_has_no_time_properties():
    assert run("") == "False False"


def test_import_kind_time_attaches_them():
    assert run("import kind.time") == "False True"


def test_an_alias_into_kind_time_opts_in_too():
    assert run("kind.td") == "False True"


def test_without_the_opt_in_a_time_property_says_what_is_missing():
    probe = (
        "import kind\n"
        "try:\n"
        "    kind.Kind('2024-01-01').as_date\n"
        "except AttributeError as error:\n"
        "    print(error)\n"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)
    assert "time is opt-in" in result.stdout and "import kind.time" in result.stdout
