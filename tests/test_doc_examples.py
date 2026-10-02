"""Every ```python block in README.md and docs/ runs against the current code.

A block may opt out only by saying why, on the line before its fence:

    <!-- doc-example: not-run — <reason> -->

A block that defines a module other blocks import is written to a file first:

    <!-- doc-example: module <name> -->

Each block runs in this process with an empty pool and a restored mixin registry
(see conftest.isolated_kinds), from a scratch working directory.
"""
import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted([ROOT / "README.md", *(ROOT / "docs").rglob("*.md")])
FENCE = re.compile(r"(?:^<!-- doc-example: (?P<kind>not-run|module) ?(?P<arg>[^>]*?) ?-->\n)?^```python\n(?P<code>.*?)^```",
                   re.DOTALL | re.MULTILINE)


def blocks():
    for page in PAGES:
        for number, match in enumerate(FENCE.finditer(page.read_text(encoding="utf-8")), start=1):
            yield page.relative_to(ROOT), number, match["kind"], (match["arg"] or "").strip(" —-"), match["code"]


MODULES = {arg: code for _, _, kind, arg, code in blocks() if kind == "module"}
RUNNABLE = [pytest.param(code, id=f"{page}#{number}") for page, number, kind, _, code in blocks() if kind is None]


@pytest.fixture
def doc_modules(tmp_path, monkeypatch):
    for name, code in MODULES.items():
        (tmp_path / f"{name}.py").write_text(code, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.chdir(tmp_path)  # examples that write files write them here
    yield
    for name in MODULES:
        sys.modules.pop(name, None)


@pytest.mark.filterwarnings("default")  # a reader runs examples with Python's default warnings
@pytest.mark.parametrize("code", RUNNABLE)
@pytest.mark.usefixtures("doc_modules")
def test_documented_example_runs(code, monkeypatch):
    script = types.ModuleType("__main__")  # as if run with `python example.py`
    monkeypatch.setitem(sys.modules, "__main__", script)
    exec(compile(code, "<doc example>", "exec"), script.__dict__)


def test_every_opt_out_says_why():
    unexplained = [f"{page}#{number}" for page, number, kind, arg, _ in blocks() if kind == "not-run" and not arg]
    assert not unexplained, f"not-run blocks without a reason: {unexplained}"


def test_the_pages_have_examples():
    assert len(RUNNABLE) > 80
