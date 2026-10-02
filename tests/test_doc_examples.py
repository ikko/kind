"""Runs the Python code blocks of documentation pages whose claims are written as asserts.

A page listed here promises that every ```python block on it runs as-is against
the current code; each block starts from an empty pool (see conftest.isolated_kinds).
"""
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"
CHECKED_PAGES = [
    DOCS / "topics" / "1_kind_fundamental_building_block" / "kind_vs_type.md",
]
BLOCK = re.compile(r"^```python\n(.*?)^```", re.DOTALL | re.MULTILINE)


def code_blocks():
    for page in CHECKED_PAGES:
        for number, block in enumerate(BLOCK.findall(page.read_text(encoding="utf-8")), start=1):
            yield pytest.param(block, id=f"{page.stem}-{number}")


@pytest.mark.parametrize("code", list(code_blocks()))
def test_documented_example_runs(code):
    exec(compile(code, "<doc example>", "exec"), {"__name__": "doc_example"})


def test_every_checked_page_has_examples():
    assert all(BLOCK.search(page.read_text(encoding="utf-8")) for page in CHECKED_PAGES)
