# Insights

Lessons from building and repairing `kind`, kept because each one cost something to learn.
Newest first.

## 2026-10-02 (evening) — verifying the documentation found the bugs

**Check every claim in the docs against the code before rewriting a sentence.** A review for senior
engineers, done by probing each claim, found code defects behind the promises:
- `kind.name = 'z'` corrupted the pool;
- `reparent()` left one-sided edges;
- freeze missed `unrelate`, neighbour deletes and direct set mutation;
- reading a missing key of frozen `metadata` *inserted* it, through `DefDict.__missing__` behind a
  `MappingProxyType`;
- a closed space could be re-entered.

Fixing the code was cheaper than documenting the defects, and the docs could then state the
guarantee without caveats.

**A guarantee holds without exception only if there is one way to break it.** Edge symmetry held for
the methods, but anyone could call `kind.children.add` directly. Making the edge sets accept changes
only from inside Kind's own methods (a `ContextVar` flag) turned "usually symmetric" into
"symmetric", and the property test now holds for any sequence of edits.

**Property tests find the case a person would not write.** `a -> b, b -> b, b.reparent()` (a
self-loop) broke edge symmetry. It took a different random seed to surface it, so the property now
runs 400 examples.

**A text format is round-trippable only in the order it was designed for.** An indented outline is
unambiguous in depth-first order. Breadth-first output interleaves branches, so it is display-only.

## 2026-10-02 (afternoon) — making the global state explicit

**A class attribute is a global variable with a nicer name.** The pool, order, counters, lock and cap
lived on `BaseKind`. Every symptom traced back to that: a five-attribute test fixture that was wrong
for months, `from_json` merging into unrelated data, one lock for all graphs. Moving them into a
`KindSpace` selected by a `ContextVar` kept the everyday API (`Kind('x')`) unchanged. It turned the
fixture into `with KindSpace(): yield` and made "a separate graph" a single line. A `ContextVar`
rather than a thread-local, because the scheduler runs on asyncio/trio, and anyio copies the context
into worker threads.

**Equality must include the universe.** Once two spaces can each hold a `Kind('A')`, name-only
equality would call two different entities equal. Equality is name and space; the hash stays the
name.

**A Python version matrix finds what one interpreter hides.** On 3.14, annotations are evaluated
lazily (PEP 649), so a docs example with `self: Kind` and no import worked. On 3.10–3.13 it raised
`NameError`.

## 2026-10-02 — the symb → kind rename and the review after it

**A rename is a token problem, not a text problem.** Commit `ddeaab2` ("rename symbol to symb")
replaced a substring: `symbolic` became `symbic` in 75 places, and doc links broke. The second
rename split identifiers into components (`_`, digits, camelCase) and changed only components that
were exactly `sym`/`symb`/`symbol`. The reviewed artifact was a table of ~210 distinct tokens, not
~5000 hits. The external concept (Lisp/Ruby symbols, "debug symbols") was put back by hand.

**Rename commits should be pure moves.** When a file's content changes by more than half, git stops
seeing a rename, and `log --follow` loses history. The fix: one commit that only moves paths
(R100), then one that rewrites content.

**A sys.path layout hides a broken package.** `from core.symbol import Symbol`, with a
`sys.path.insert` in conftest, made the tests pass while the published wheel installed top-level
`core/ builtin/ bin/ utils/` and no `symb`. The same layout loaded the core module twice
(`core.symbol` and `symb.core.symbol`): two `Symbol` classes in one process. Absolute imports and a
wheel installed into a fresh venv outside the repo are the test that matters.

**A green test can be vacuous.**
- `test_imports` checked module names that nothing was loaded under, so it passed whatever the
  behaviour was.
- A test nested inside another test's body never ran.
- Duplicated test blocks kept only their second copy.
- An empty test file named a behaviour it never tested.
- 15 failing tests sat behind `skip("rest of second refactor")`; two of them hid data loss.

What found these: pyflakes (redefinition), running in a fresh interpreter, and reading what each
assertion can possibly fail on.

**Weak interning is only invisible for stateless values.** `sys.intern` can drop a string
because nobody can tell; a Kind carries origin, metadata and relations, so collecting it loses
data silently. The pool *looked* weak (`WeakValueDictionary`) while a strong creation-order tree
kept everything alive, so the real semantics were strong. Making the tree weak too made the pool
really weak, and `Kind('x').metadata['a'] = 1` vanished on the next line. The design question was
never memory but *who decides when a name ends*: now `delete()`/`forget()`, with `max_kinds` for
untrusted input. Before "fixing" one of two mechanisms that cancel each other, measure what the
system actually does, not what its parts declare.

**Every edge of one kind should own its target the same way.** Relations held targets in a
`WeakSet` while children were strong, so a Kind connected only by a relation vanished under GC,
and tests passed or failed depending on when the collector ran.

**Class attributes shadow `__getattr__`.** `KindNamespace` carried ~450 lines copied from `Kind`.
Because methods are found before `__getattr__`, `k.next`, `k.first` and `k.ref` returned those
methods instead of Kinds. A dynamic namespace must have (almost) no members of its own.

**`__eq__` must return `NotImplemented` for foreign types.** Returning `False` stops Python from
asking the other operand, so `LazyKind(...) in kind.children` was always False.

**A dynamic catch-all makes errors silent.** Any unknown public attribute is a relation verb, by
design. But private names must still raise: otherwise `hasattr`, copy/pickle probes and internal
typos (`self.related_to` on an unset slot) all "succeed" by returning a function.

**Make time a parameter.** The scheduler tests waited on the real clock (≈20 s, with skips for
"timing issues"). An injectable `now` and a deterministic `run_due_jobs()` step made them exact,
and the suite went from 39 s to under 3 s.

**A security boundary must not depend on trusting a file.** A schedule file named functions by
dotted path and imported them, so loading it could run `os.system`. Resolution is now opt-in per
module (`allowed_modules` / `--allow-module`). `register_mixin` called `eval` on strings: strings
are now refused.

**Respect the author's constraints when adding tools.** The Makefile said ruff was left out for its
size. pyflakes (~100 KB) covers what mattered here (unused, undefined, redefined) and stays within
that constraint.
