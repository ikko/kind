"""Gates for the documentation: reachable, precise, and complete where it claims to be.

History (docs/history/) and the changelog are records of what was written at the time, so the
wording gates skip them.
"""
import re
from pathlib import Path

import pytest

import kind
from kind import Kind
from kind.core.base_kind import BaseKind
from kind.core.mixinability import get_applied_mixins

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
LINK_WITH_ANCHOR = re.compile(r"\]\(([^)\s#]*)(?:#([^)\s]*))?\)")
RECORDS = ("docs/history/", "docs/changelog.md")
FILLER = ["powerful", "seamless", "robust", "sophisticated", "meticulous", "elegant", "paramount", "testament",
          "versatile", "empower", "unlock", "leverage", "comprehensive", "crucial", "delve", "cutting-edge",
          "in today's"]


def pages():
    yield from sorted([ROOT / "README.md", *(ROOT / "docs").rglob("*.md"),
                       ROOT / "scheduler" / "README.md", *(ROOT / "scheduler" / "docs").rglob("*.md")])


def current_pages():
    return [p for p in pages() if not any(str(p.relative_to(ROOT)).startswith(r) for r in RECORDS)]


def links_from(page: Path):
    for target in LINK.findall(page.read_text(encoding="utf-8")):
        if not re.match(r"[a-z]+:", target):
            yield (page.parent / target).resolve()


def test_every_page_is_reachable_from_the_readme():
    reachable, frontier = set(), [ROOT / "README.md"]
    while frontier:
        page = frontier.pop()
        if page in reachable or page.suffix != ".md" or not page.exists():
            continue
        reachable.add(page)
        frontier.extend(links_from(page))
    generated = {ROOT / "docs" / "package" / "README.md"}  # the PyPI copy of README.md
    orphans = [str(p.relative_to(ROOT)) for p in pages() if p.resolve() not in reachable and p not in generated]
    assert not orphans, f"pages no link reaches from README.md: {orphans}"


def github_anchors(page: Path) -> set[str]:
    """The ids GitHub gives headings: lowercase, punctuation dropped, spaces to hyphens (code blocks skipped)."""
    text = re.sub(r"^```.*?^```", "", page.read_text(encoding="utf-8"), flags=re.MULTILINE | re.DOTALL)
    return {re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
            for heading in re.findall(r"^#+ (.+)$", text, re.MULTILINE)}


@pytest.mark.parametrize("page", list(pages()), ids=lambda p: str(p.relative_to(ROOT)))
def test_every_relative_link_resolves(page):
    """A link to a missing file or heading fails here, not in a reader's browser."""
    broken = []
    for target, anchor in LINK_WITH_ANCHOR.findall(page.read_text(encoding="utf-8")):
        if re.match(r"[a-z]+:", target):
            continue                                    # http(s), mailto: not checked offline
        resolved = (page.parent / target).resolve() if target else page
        if not resolved.exists():
            broken.append(target)
        elif anchor and resolved.suffix == ".md" and anchor not in github_anchors(resolved):
            broken.append(f"{target}#{anchor}")
    assert not broken, f"broken links in {page.relative_to(ROOT)}: {broken}"


@pytest.mark.parametrize("page", current_pages(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_filler_words(page):
    text = page.read_text(encoding="utf-8").lower()
    found = [word for word in FILLER if re.search(rf"\b{re.escape(word)}", text)]
    assert not found, f"filler in {page.relative_to(ROOT)}: {found}"


@pytest.mark.parametrize("page", current_pages(), ids=lambda p: str(p.relative_to(ROOT)))
def test_graph_and_threading_claims_are_precise(page):
    text = page.read_text(encoding="utf-8")
    assert not re.search(r"\bDAGs?\b|acyclic", text), "the graph allows cycles: say 'directed graph'"
    for match in re.finditer(r"thread-safe|thread safe", text, re.IGNORECASE):
        window = text[max(0, match.start() - 300): match.end() + 300]
        assert "lock" in window.lower(), f"'{match.group()}' without its scope (which lock, which operations)"


def test_the_readme_is_short():
    assert len((ROOT / "README.md").read_text(encoding="utf-8").splitlines()) <= 150


def reference_headings() -> set[str]:
    text = (ROOT / "docs" / "reference" / "api.md").read_text(encoding="utf-8")
    return set(re.findall(r"^#+ `([^`(]+)", text, re.MULTILINE))


def test_the_api_reference_covers_the_public_surface():
    headings = reference_headings()
    mixins = set(get_applied_mixins())  # documented with their module (kind.time, kind.builtin.visual, path)
    own = {name for cls in (Kind, BaseKind) for name in vars(cls) if not name.startswith("_") and name not in mixins}
    public_methods = {f"Kind.{name}" for name in own}
    exported = set(kind.__all__) - {"builtin", "core"}
    missing = sorted(name for name in public_methods | exported if name not in headings)
    assert not missing, f"public names without a heading in docs/reference/api.md: {missing}"
