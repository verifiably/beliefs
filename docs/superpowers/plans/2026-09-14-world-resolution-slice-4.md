# World resolution slice 4 — implementation plan

**Status:** plan drafted 2026-09-14 against the approved design; awaiting review.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the view-query evaluator over the world read view, select W7, select W8b and W8's two runnable conflicts over existing code, and discharge them as conformance cut 28.

**Architecture:** A new `world/selection.py` exposes `evaluate_query(view, query) -> Selection`, a pure function of an open `WorldReadView` and a parsed `ViewQuery`: it refuses damage and drift at entry, locates every address the query names before denoting anything, denotes the four v1 predicates as sets of live addresses over one enumeration of the capture, walks closures from the anchor's live address through an evaluator-owned adjacency that reports an absent inbound source instead of dropping it, validates every record it reads or selects, and returns a sorted selection with a projection and identity. `view_query.stored_query` bridges a resolved view record to its query; `errors.SelectionRefused` carries a closed reason set. W8/W8b are read as durable arms over `derive.address_map`, `consolidate` and `move` as they stand. The cut is frozen first and discharged through its own runner after cut 27's.

**Tech Stack:** Python 3.13 via `uv run --frozen`, pytest with `pytest-xdist`, pydantic v2 `Node` models from `nodes` 2.0, the `atoms` durable engine on the certified volume for acceptance, PyYAML for fixtures; ruff and pyright as the gate.

**Spec:** `docs/superpowers/specs/2026-09-13-world-resolution-slice-4-design.md` (reviewed twice, approved 2026-09-14 at `0e8600b`). Every task cites its section; read the spec first — the plan argues from it.

## Global Constraints

- Work on branch `design/world-resolution-slice-4` in `.worktrees/world-resolution-slice-4`; every path below is relative to the repository root, and every path you show the user is prefixed `.worktrees/world-resolution-slice-4/`. Conventional commits; no AI-attribution trailer; no `/home/<user>` or absolute Dropbox paths in code or docs.
- Run every Python command from `python/` with `uv run --frozen …`; system python lacks `beliefs`. Never pass `-q` to pytest (addopts already sets it, and `-qq` drops the summary line); read the final `N passed` line before claiming a count.
- Fast loop: `uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py`. Before each commit: `uv run --frozen ruff check . && uv run --frozen pyright` (pyright takes no path argument). The pre-commit hook runs `just check` when `python/` is staged and `just hook-pre-commit-docs` otherwise; `ts/node_modules` exists (`just setup` ran).
- Tracker: `tasks start <id>` before a task's first step, `tasks note <id> "<what landed>"` and `tasks done <id> "<result>"` at its last, `tasks check` before every commit. Never edit `tasks/*.md` directly. The parent is `beliefs-0e523a`; the step ids are listed in the **Task ids** section below.
- The evaluator opens nothing, names no `current`, reads no coordination record and consults no profile (spec decision 1). It takes exactly `WorldReadView`; a `ReadView` is a `TypeError` at entry.
- No refusal borrows `NotPresent`, `Unknown` or `RecordNotPresent` (spec §3.4, §5): `SelectionRefused` is raised, never returned, and nothing that refuses enters `absent` or `unresolved`.
- The evaluator serves addresses and never a record: the private enumeration it reads (`WorldReadView._mapped_records`) hands out retained objects that must not be mutated and must not leave `beliefs.world` (spec §3.2).
- `derive.py`, `relocation.py`, `corpus.py` and `world/view.py`'s served surface are read, not rewritten (spec §6, §7). The only `view.py` change is the private accessor.
- Frozen files (`n2_arms_cut*.py`, cut documents, declaration tables of cuts ≤ 27) are never edited. A task that displaces a line a frozen cited-not-run guard matches records the arm in `python/tests/cited_not_run.py`'s `stale_arms`; a live guard gets a dated re-target. `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py` passes after Tasks 2 and 3.
- N2 rows are `<unit>-<letter>` (`W7-a`, `W8b-c`); cut 28's `unit_of` parses exactly that. Every durable arm runs on the certified volume; a capability refusal is an error, never a skip.
- Shared surfaces this lane rewrites (roadmap rule 3): `errors.py`, `view_query.py`, `decode.py`, `world/__init__.py`, `world/view.py` (private accessor only), `python/tools/roadmap_status.py`, `python/tests/test_designs_corpus.py`, `README.md`, the ledger, the roadmap, the guide, the world-addressing design (dated notes on W7, W8, W8b), the slice 2b design (dated note), the adoption ledger.
- The cut is frozen before implementation (Task 1) and its §§2–7 are byte-exact from the freeze commit onward; §1 stays editable. The number is 28 unless a sibling worktree has claimed it first — Task 1 checks every worktree and branch.

## Task ids

Created 2026-09-14 against this plan; each task's first step names its id.

- Task 1: `beliefs-cb9581`
- Task 2: `beliefs-6b28db`
- Task 3: `beliefs-9454aa`
- Task 4: `beliefs-d1c305`
- Task 5: `beliefs-35d582`
- Task 6: `beliefs-7d4299`
- Task 7: `beliefs-10efda`
- Task 8: `beliefs-0160ea`
- Task 9: `beliefs-902cd5`

---

## File structure

| path | responsibility |
|---|---|
| `docs/designs/2026-09-14-conformance-cut-28.md` | the frozen cut: boundary, selection, accounting, obligations |
| `python/src/beliefs/errors.py` | `SelectionRefused` |
| `python/src/beliefs/view_query.py` | `stored_query(node) -> ViewQuery` |
| `python/src/beliefs/decode.py` | `stored_claim_terms(node) -> tuple[tuple[str, ...], tuple[str, ...]]`, the profile-independent shape check factored out of `claim_from_stored` |
| `python/src/beliefs/world/view.py` | `WorldReadView._mapped_records()`, the private enumeration |
| `python/src/beliefs/world/selection.py` (new) | `SELECTION_VERSION`, `Unresolved`, `Selection`, `evaluate_query`, the query adjacency |
| `python/src/beliefs/world/__init__.py` | re-exports `Selection`, `Unresolved`, `evaluate_query` |
| `python/tests/test_view_query.py` | Task 2's `stored_query` arms |
| `python/tests/test_world_selection.py` (new) | Tasks 3–5: the evaluator's unit arms and the topic-world fixture |
| `python/tests/test_world_conflicts.py` (new) | Task 6: W8 and W8b unit arms over existing code |
| `python/tests/acceptance/test_world_selection_acceptance.py` (new), `python/tests/acceptance/n2_arms_cut28.py` (new, canonical), `python/tests/acceptance/test_n2_cut28.py` (new) | durable arms, declarations, guard |
| `python/tools/cut28_acceptance.py` (new), `python/tools/roadmap_status.py` | the runner and cut 28's accounting row |
| `docs/designs/2026-08-02-world-addressing-design.md` (W7, W8, W8b cells), `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` (§13 note), `docs/guide/identity-world-and-change.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/foundations.md` | dated notes |
| `docs/plans/<date>-conformance-cut-28-results.md`, ledger, roadmap, README | discharge |

---

### Task 1: Freeze conformance cut 28

**Files:**
- Create: `docs/designs/2026-09-14-conformance-cut-28.md`
- Modify: `README.md:97` (design list, after the cut 27 row), `docs/guide/contracts-and-adoption.md:6-24` (`sources:` list), `python/tests/test_designs_corpus.py:252-262` (`_COUNT_WORDS`, only if the next number word is missing)

**Interfaces:**
- Produces: the three declaration units `W7`, `W8`, `W8b` cited verbatim by Task 7's `DECLARATION_UNITS`; the literals `PREFIX_RUNNERS = ("cut27_acceptance.py",)` and `PHASE_MODULES = ("test_world_selection_acceptance.py", "test_n2_cut28.py")` cited by Task 8; the freeze sha and sha256 cited by Task 7's guard.

- [ ] **Step 0: `tasks start beliefs-cb9581`**

The nine step tasks already exist under `beliefs-0e523a` (the **Task ids** section); they were created against this plan on 2026-09-14. Do not add them again.

- [ ] **Step 1: Confirm the number is free**

```bash
for wt in $(git worktree list --porcelain | awk '/^worktree /{print $2}'); do ls "$wt/docs/designs" | grep -c "conformance-cut-28"; done
git log --all --oneline -- 'docs/designs/*cut-28*' | head -3
```
Expected: every count is `0` and the log is empty. If not, use the next free number everywhere below and in every later task.

- [ ] **Step 2: Write the cut document**

Follow `docs/designs/2026-09-13-conformance-cut-27.md` section for section. Header:

```markdown
# Conformance cut 28 — view evaluation and the W8/W8b discharge

**Status:** frozen 2026-09-14 before implementation.
**Frozen:** 2026-09-14, before implementation, on `design/world-resolution-slice-4`
**Design:** `../superpowers/specs/2026-09-13-world-resolution-slice-4-design.md`, reviewed twice 2026-09-14
**Numbered after** cut 27 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).
```

`## 1. What this cut is` — spec §1's first four paragraphs (the language exists and nothing evaluates it; the read side is complete; W7 asks for the join; the W8/W8b audit), then cut 5's selection-rule sentence: "The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial."

`## 2. The boundary` — `In scope:` bullets at file-and-symbol granularity from this plan's file-structure table (`errors.py`: `SelectionRefused`; `view_query.py`: `stored_query`; `decode.py`: `stored_claim_terms`; `world/view.py`: `_mapped_records`; `world/selection.py`: `SELECTION_VERSION`, `Unresolved`, `Selection`, `evaluate_query`; `world/__init__.py`: the exports; the four test modules; the runner and `roadmap_status.py`; the dated notes, ledger, roadmap, guide, README and results record). `Out of scope:` bullets: W9 and W14 (`authority-labels`, tier 3; slice 2b's assignment of W14 to slice 4 does not stand, spec §8 item 1); W8's ambiguous-search-term conflict (deferred to `authority-labels` with W9, ledger artifact 11; re-homed at discharge, spec §8 item 2); R23's rules-store clauses and W8a's `instrument-certification` arm (`contract-cut`); `beliefs-48214e` and `beliefs-24b42b` (filed, not prerequisites); `derive.py`, `relocation.py`, `corpus.py` and every served method of `world/view.py`, which are read and not rewritten; `next` and `publish`, which consume the evaluator and are not built here.

`## 3. Selection` — one subsection per row:

```markdown
### W7 — closes
A topic record in one corpus whose query names records in the other is found under every predicate form — `addresses` selects exactly the named dataset and contributes its corpus alone; `kinds` selects both corpora's datasets and contributes both; `closure` from the first corpus's run over `produces` selects the second's dataset and not the run; `references-term` selects the second's proposition and never a dataset; a two-clause query selects and contributes both — each complete, each with the identity equal across two opens at one epoch. With the second corpus absent, `addresses` refuses `address-not-present` naming it, `closure` from the present anchor returns an incomplete selection with one not-present step naming the dataset, `kinds` returns an incomplete selection naming the corpus in `absent`, and a closure anchored in the absent corpus refuses `address-not-present` naming the anchor; every incomplete identity differs from the complete one and none is the empty set or `unknown`. Reordered clauses, predicates and corpus registration give one projection. A drifted view refuses `corpus-drifted` and a damaged one `corpus-damaged`; a retired anchor over a cycle selects what the live anchor selects; a dangling target is `unknown` and an absent inbound source `not-present`, both reported and neither dropped; a retired and a live address of one record select it once; a term in an argument and in a restriction both select, a malformed claim facet refuses naming the record, and a stale-hash proposition whose edit removed the term refuses rather than yielding empty; a stale selected record refuses; `clauses: []` is complete and empty; a `ReadView` is a `TypeError`. Selected: unit `W7`. **Deferred:** nothing.

### W8 — part, duplicate-location and address-conflict conflicts
Two records at one canonical address in two corpora refuse the build with a `duplicate-location` finding naming both claims in the capture's sorted order and no carrier, the same code, ref and claims in the other registration order; `consolidate` with the authored survivor repairs it, the rebuild publishes, the view serves one record, and swapping `keep` gives the mirror; `move` into the occupied destination refuses `DuplicateLocation` thereafter. Two `source` records at one derived address whose identifier maps differ refuse the build as `duplicate-location` before any basis is read, `consolidate` refuses `HistoryDisagreement` whichever is `keep` and writes nothing, and a source whose stored id is not its derived address refuses `SourceAddressDisagreement` at the write boundary. Selected: unit `W8`. **Deferred:** the ambiguous-search-term conflict, which needs the pinned authority snapshot (ledger artifact 11) and is W9's arm restated (`authority-labels`).

### W8b — closes, over existing code
One `uid` under two canonical addresses is `uid-corruption`, offers no repair, and `consolidate` over the pair refuses `AddressDisagreement`; two records at one canonical address in two corpora are `duplicate-location` both with a shared `uid` and with distinct `uid`s, the same code and ref; corruption outranks duplication when one `uid` does both; each corpus's own `corpus_check` reports neither. Selected: unit `W8b`. **Deferred:** nothing.

### Boundary invariants
No refusal borrows `NotPresent`, `Unknown` or `RecordNotPresent`; the evaluator opens nothing and reads no coordination record; every record read or selected passes the facade's validation rule; nothing is written by evaluation; the world view's served surface is unchanged.
```

`## 4. Accounting` — exactly:

```markdown
Three guarantee rows are read, **2 full/closed** (W7, W8b), 1 partial (W8), and **3 declaration units** carry them: `W7`, `W8`, `W8b`. W8's remainder is its ambiguous-search-term conflict, re-homed to `authority-labels` at discharge (§2); `world-resolution` then retains no guarantee row.
```

`## 5. N2 and acceptance obligations` — numbered as cut 27's: (1) the inventory is exactly the three units, single-homed; (2) every durable arm runs on the certified volume, refusal is an error and never a skip; (3) the runner, quoting `PREFIX_RUNNERS = ("cut27_acceptance.py",)` and `PHASE_MODULES = ("test_world_selection_acceptance.py", "test_n2_cut28.py")`; (4) the 23 declared arms cover every sabotage site: in `world/selection.py` (the entry damage check skipped; the entry drift check skipped; an unknown address no longer refusing; not-present collapsed into unknown; clauses intersected instead of unioned; the anchor included in its closure; the closure started from the literal anchor string; an absent inbound source dropped; `unresolved` omitted from the projection; `absent` omitted from the projection; selected records served unvalidated; candidate propositions read unvalidated; `references-term` matched on arguments only; a malformed claim facet read as not referencing; the world-only type check widened), in `decode.py` (claim terms normalized before comparison), in `world/derive.py` (the uid check dropped; the address check dropped; addresses checked before uids; `duplicate-location` keyed on `uid` equality), in `relocation.py` (`consolidate` accepting two addresses; `consolidate` choosing a survivor when histories differ; `move` overwriting an occupied destination); (5) `test_n2_cut28.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree; (6) prior declarations frozen, no check reclaimed; (7) this document and its declaration inventory pinned by digest before discharge.

The sites in (4) count fifteen in `selection.py`, one in `decode.py`, four in `derive.py` and three in `relocation.py`: **23 arms**.

`## 6. Second reader` — the spec's two review passes on 2026-09-14 (§11 there): four findings, then one. `## 7. Limitations` — one line each: every predicate is an enumeration of the capture, with no per-epoch index (spec §9 item 1); no closure-over-selection predicate (spec §9 item 2); W8's search-term conflict is unrun and re-homed, not closed; `next` and `publish` are not built and their refusal rules over `Selection` are stated, not exercised; serial per-corpus captures (slice 1 limitation 1) carry.

- [ ] **Step 3: Add the document to the README list and the guide's sources**

In `README.md` add a row after line 97 in the same format: `| \`2026-09-14-conformance-cut-28.md\` | the frozen slice 4 cut: view-query evaluation over the world read view, W7, and the W8/W8b discharge over existing code |`. Bump the stated count of designs by one (the sentence `test_the_readme_states_how_many_designs_there_are` reads; extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` if the next number word is missing). In `docs/guide/contracts-and-adoption.md`'s front-matter `sources:` list add `  - ../designs/2026-09-14-conformance-cut-28.md` in date order.

- [ ] **Step 4: Run the design-corpus guards**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider`
Expected: every test passes (the row total stays 196; no row is minted).

- [ ] **Step 5: Commit the freeze and pin it**

```bash
git add docs README.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut28): freeze conformance cut 28"
git rev-parse HEAD
sha256sum docs/designs/2026-09-14-conformance-cut-28.md
tasks note beliefs-0e523a "cut 28 frozen at <sha>, sha256 <digest>"
tasks done beliefs-cb9581 "cut 28 frozen at <sha>"
```
Task 7 pins both values.

---

### Task 2: `SelectionRefused`, `stored_query` and the private enumeration

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `CorpusDamaged`, about line 440), `python/src/beliefs/view_query.py` (append), `python/src/beliefs/world/view.py:113` (after `iter_stored`)
- Test: `python/tests/test_view_query.py`, `python/tests/test_world_view.py`

**Interfaces:**
- Produces: `errors.SelectionRefused(reason, *, refs, corpus_ids=())` with `REASONS`, `.reason`, `.refs`, `.corpus_ids`; `view_query.stored_query(node: Node) -> ViewQuery`; `WorldReadView._mapped_records() -> Iterator[tuple[str, Node]]`. Tasks 3–5 consume all three.

- [ ] **Step 1: `tasks start beliefs-6b28db`, then write the failing tests**

Append to `python/tests/test_view_query.py`:

```python
from coordination_fixtures import raw_coordination_node

from beliefs.errors import MalformedRecord
from beliefs.view_query import Kinds, stored_query

A = "a" * 32
C = "c" * 32
D = "d" * 32
KINDS_QUERY = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset"]}]}]}


def test_stored_query_reads_a_view_revisions_query():
    topic = raw_coordination_node("topic", A, C, local=D, query=KINDS_QUERY)
    query = stored_query(topic)
    assert query.clauses[0].predicates == (Kinds(("dataset",)),)
    assert query.projection() == KINDS_QUERY


def test_stored_query_refuses_a_non_view_kind_and_a_missing_query():
    task = raw_coordination_node("task", A, C, local=D)
    with pytest.raises(MalformedRecord, match="not a view revision"):
        stored_query(task)
    topic = raw_coordination_node("topic", A, C, local=D)
    del topic.facets["coordination"]["query"]
    with pytest.raises(MalformedRecord, match="carries a query"):
        stored_query(topic)


def test_stored_query_reports_a_corrupt_stored_query_as_the_record():
    topic = raw_coordination_node("topic", A, C, local=D, query={"version": "science.view-query.v9", "clauses": []})
    with pytest.raises(MalformedRecord, match=f"{topic.id}: stored view query does not parse"):
        stored_query(topic)
```

Append to `python/tests/test_world_view.py`, inside `TestCapture` or at module level:

```python
def test_mapped_records_enumerate_what_iter_stored_yields_without_copying(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)
    view = open_world_view(world, published)
    pairs = list(view._mapped_records())
    assert [node.id for _, node in pairs] == [node.id for node in view.iter_stored()]
    assert [corpus for corpus, _ in pairs] == [view.corpus_of(node.id) for _, node in pairs]
    first = pairs[0][1]
    assert pairs[0][1] is first and next(iter(view._mapped_records()))[1] is first
```

Add a `SelectionRefused` shape test to `python/tests/test_view_query.py`:

```python
from beliefs.errors import SelectionRefused


def test_selection_refused_carries_a_closed_reason_and_sorted_references():
    refused = SelectionRefused("address-not-present", refs=["dataset:b", "dataset:a"], corpus_ids=["b" * 32])
    assert (refused.reason, refused.refs, refused.corpus_ids) == ("address-not-present", ("dataset:a", "dataset:b"), ("b" * 32,))
    assert "dataset:a, dataset:b" in str(refused) and ("b" * 32) in str(refused)
    with pytest.raises(ValueError, match="not a selection refusal reason"):
        SelectionRefused("absent", refs=["x"])
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_view_query.py tests/test_world_view.py -k "stored_query or selection_refused or mapped_records"`
Expected: FAIL with `ImportError` (`stored_query`, `SelectionRefused`) and `AttributeError` (`_mapped_records`).

- [ ] **Step 3: Implement**

`python/src/beliefs/errors.py`, after `CorpusDamaged`:

```python
class SelectionRefused(ScienceError):
    """A view query could not be evaluated over this world view (world
    resolution slice 4 §3.4): one class, a closed reason, the offending
    references sorted. No reason says where a record is — that is
    `NotPresent`'s and `RecordNotPresent`'s job — and every reason says the
    question could not be answered."""

    REASONS = ("corpus-damaged", "corpus-drifted", "address-unknown", "address-not-present", "record-malformed")

    def __init__(self, reason: str, *, refs: "Sequence[str]", corpus_ids: "Sequence[str]" = ()) -> None:
        if reason not in self.REASONS:
            raise ValueError(f"{reason!r} is not a selection refusal reason")
        self.reason = reason
        self.refs = tuple(sorted(set(refs)))
        self.corpus_ids = tuple(sorted(set(corpus_ids)))
        where = f" in {', '.join(self.corpus_ids)}" if self.corpus_ids else ""
        super().__init__(f"view evaluation refused ({reason}): {', '.join(self.refs)}{where}")
```

`Sequence` is already imported in `errors.py` (check the module head; if not, add `from collections.abc import Sequence` there).

`python/src/beliefs/view_query.py`, appended (imports at the top: `from collections.abc import Mapping`, `from nodes.core.node import Node`, `from beliefs.coordination import VIEW_KINDS`, `from beliefs.errors import MalformedRecord`):

```python
def stored_query(node: Node) -> ViewQuery:
    """The parsed query of a stored view revision (world resolution slice 4
    §3.1) — the one bridge from a record the caller resolved live to the
    query the evaluator takes. The write boundary guarantees the stored form
    parses, so a parse failure here is corruption and is reported as the
    record, never repaired."""
    if not isinstance(node, Node) or node.kind not in VIEW_KINDS:
        raise MalformedRecord(f"{getattr(node, 'id', node)!r}: not a view revision")
    facet = node.facets.get(stored.COORDINATION_FACET)
    if not isinstance(facet, Mapping) or "query" not in facet:
        raise MalformedRecord(f"{node.id}: a view revision carries a query in its coordination facet")
    try:
        return parse_view_query(facet["query"])
    except ValueError as caught:
        raise MalformedRecord(f"{node.id}: stored view query does not parse: {caught}") from caught
```

`python/src/beliefs/world/view.py`, after `iter_stored`:

```python
    def _mapped_records(self) -> Iterator[tuple[str, Node]]:
        """`(corpus_id, retained record)` for every mapped record of a present
        corpus, in `iter_stored`'s order and **without copying**. For
        `beliefs.world` only: the evaluator (slice 4 §3.2) reads kinds and
        facets and hands out addresses, and nothing it reads leaves it. A
        caller that would serve one of these objects uses `get`."""
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield corpus_id, self._held[corpus_id][uid]
```

- [ ] **Step 4: Run the tests, the staleness probes and the gate**

Run: `cd python && uv run --frozen pytest tests/test_view_query.py tests/test_world_view.py tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: PASS, summary line names the count.

Run: `uv run --frozen ruff check . && uv run --frozen pyright`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note beliefs-6b28db "SelectionRefused, stored_query, WorldReadView._mapped_records"
tasks done beliefs-6b28db "the refusal class, the record-to-query bridge and the private enumeration"
git add python/src python/tests tasks
git commit -m "feat(world): SelectionRefused, stored_query and the view's private enumeration"
```

---

### Task 3: `Selection` and `evaluate_query` over `kinds` and `addresses`

**Files:**
- Create: `python/src/beliefs/world/selection.py`, `python/tests/test_world_selection.py`
- Modify: `python/src/beliefs/world/__init__.py` (import and `__all__`)

**Interfaces:**
- Consumes: `WorldReadView` (`damaged`, `drift`, `locate`, `resolve`, `corpus_of`, `stamp`, `_mapped_records`), `corpus.validated_node`, `view_query.{ViewQuery, Clause, Kinds, ReferencesTerm, Closure, Addresses}`, `errors.SelectionRefused`, `identity.v1.digest`, `world.read.{BoundStamp, NotPresent, Resolved, Unknown}`.
- Produces: `SELECTION_VERSION = "science.view-selection.v1"`; `Unresolved(source, predicate, target, state, corpus_id)` with `projection()` and `sort_key`; `Selection(stamp, query, selected, contributing, absent, unresolved)` with `complete`, `projection()`, `identity()`; `evaluate_query(view, query) -> Selection`; the internal seam `_denote(view, predicate, held, unresolved) -> set[str]` that Tasks 4 and 5 extend for `ReferencesTerm` and `Closure`. Both raise `NotImplementedError` in this task.

- [ ] **Step 1: `tasks start beliefs-9454aa`, then write the fixture and the failing tests**

Create `python/tests/test_world_selection.py`:

```python
"""View-query evaluation over the world read view (slice 4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from coordination_fixtures import raw_coordination_node
from fixtures_cut4 import raw_write
from nodes.core.corpus import Corpus
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from test_evaluation import CLAIM_FACET, GENE, PHENO
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import SelectionRefused, SemanticHashStale
from beliefs.view_query import ViewQuery, parse_view_query, stored_query
from beliefs.world.selection import SELECTION_VERSION, Selection, Unresolved, evaluate_query
from beliefs.world.view import open_world_view

PROJECT = "1" * 32
TOPIC = "2" * 32
REVISION = "3" * 32


def query(*clauses: list[dict]) -> ViewQuery:
    return parse_view_query({"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]})


def topic_nodes():
    """ALPHA: d_a (carrying a `produces` relation whose declared source is
    BETA's r_b — the world inbound index files edges from held records only,
    so the edge that must survive BETA's absence lives on d_a), r_a (produces
    d_b), the project and topic records. BETA: d_b, r_b, p_b (claim binding
    GENE and PHENO)."""
    d_a = stored.dataset_node("d-a", title="d-a")
    d_b = stored.dataset_node("d-b", title="d-b")
    r_a = stored.run_node("r-a", title="r-a", spec="s", produces=[d_b.id])
    r_b = stored.run_node("r-b", title="r-b", spec="s", produces=[])
    d_a.relations.append(Relation(source=r_b.id, predicate="produces", target=d_a.id))
    p_b = stored.proposition_node("p-b", title="p-b", claim=CLAIM_FACET)
    project = raw_coordination_node("project", PROJECT, "4" * 32)
    return (d_a, r_a, project), (d_b, r_b, p_b)


def topic_world(tmp_path: Path, *clauses: list[dict], alpha_extra=(), beta_extra=(), without=()):
    """The topic world; `without` drops fixture records by id before publication."""
    alpha, beta = topic_nodes()
    alpha = tuple(n for n in alpha if n.id not in without)
    beta = tuple(n for n in beta if n.id not in without)
    topic = raw_coordination_node(
        "topic", PROJECT, REVISION, local=TOPIC,
        query={"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]},
    )
    roots = corpora(tmp_path, {ALPHA: (*alpha, *alpha_extra, topic), BETA: (*beta, *beta_extra)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    return world, roots, published, topic


def evaluate_topic(world, roots, published, topic):
    """The caller's half: resolve the record live, then evaluate bound."""
    record = Corpus(roots[ALPHA]).get(topic.id)
    return evaluate_query(open_world_view(world, published), stored_query(record))


class TestAddressesAndKinds:
    def test_addresses_select_exactly_the_named_record_and_contribute_its_corpus(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-b",)
        assert selection.contributing == (BETA,)
        assert selection.complete and selection.absent == () and selection.unresolved == ()
        assert selection.stamp.packaging_identity == published.packaging_identity

    def test_kinds_select_both_corpora_and_contribute_both(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-a", "dataset:d-b")
        assert selection.contributing == (ALPHA, BETA)

    def test_clauses_union_and_predicates_intersect(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path,
            [{"kinds": ["dataset"]}, {"addresses": ["dataset:d-b"]}],
            [{"kinds": ["run"]}],
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-b", "run:r-a", "run:r-b")

    def test_empty_clauses_are_a_complete_empty_selection(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path)
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == () and selection.contributing == () and selection.complete

    def test_a_retired_and_a_live_address_select_the_record_once(self, tmp_path):
        renamed = stored.dataset_node("d-new", title="d-new")
        renamed.deprecated_ids = ["dataset:d-old"]
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:d-old", "dataset:d-new"]}], alpha_extra=(renamed,)
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-new",)


class TestIdentityAndDeterminism:
    def test_the_projection_is_the_documented_shape_and_the_identity_is_its_digest(self, tmp_path):
        from beliefs.identity import v1

        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        selection = evaluate_topic(world, roots, published, topic)
        projection = selection.projection()
        assert projection == {
            "version": SELECTION_VERSION,
            "epoch": published.packaging_identity,
            "query": selection.query.projection(),
            "selected": ["dataset:d-b"],
            "contributing": [BETA],
            "absent": [],
            "unresolved": [],
        }
        assert selection.identity() == v1.digest(SELECTION_VERSION, projection)

    def test_two_opens_at_one_epoch_and_reordered_authoring_agree(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"kinds": ["dataset"]}, {"addresses": ["dataset:d-b"]}], [{"kinds": ["run"]}]
        )
        first = evaluate_topic(world, roots, published, topic)
        reordered = query([{"kinds": ["run"]}], [{"addresses": ["dataset:d-b"]}, {"kinds": ["dataset"]}])
        second = evaluate_query(open_world_view(world, published), reordered)
        assert first.projection() == second.projection() and first.identity() == second.identity()

    def test_registration_order_does_not_move_the_projection(self, tmp_path):
        alpha, beta = topic_nodes()
        forward = corpora(tmp_path / "f", {ALPHA: alpha, BETA: beta})
        backward = corpora(tmp_path / "b", {BETA: beta, ALPHA: alpha})
        selections = []
        for roots in (forward, backward):
            world = world_over(roots[ALPHA].parent, roots)
            published = publish(world, (ALPHA, BETA), hold_shipped(world))
            selections.append(evaluate_query(open_world_view(world, published), query([{"kinds": ["dataset"]}])))
        assert selections[0].selected == selections[1].selected == ("dataset:d-a", "dataset:d-b")
        assert selections[0].contributing == selections[1].contributing


class TestEntryRefusals:
    def test_a_corpus_read_view_is_refused_by_type(self, tmp_path):
        world, roots, published, _topic = topic_world(tmp_path)
        with pytest.raises(TypeError, match="WorldReadView"):
            evaluate_query(ReadView.opened_at(roots[ALPHA]), query([{"kinds": ["dataset"]}]))  # type: ignore[arg-type]

    def test_a_drifted_view_refuses_and_the_earlier_capture_still_evaluates(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        before = open_world_view(world, published)
        node = Corpus(roots[BETA]).get("dataset:d-b")
        node.relations.append(Relation(source=node.id, predicate="cites", target="dataset:d-a"))
        (roots[BETA] / "dataset" / "d-b.md").write_text(node_to_markdown(node), encoding="utf-8")
        after = open_world_view(world, published)
        moved = [report.corpus_id for report in after.drift() if report.captured_state != report.published_state]
        assert moved == [BETA]
        with pytest.raises(SelectionRefused) as caught:
            evaluate_query(after, stored_query(Corpus(roots[ALPHA]).get(topic.id)))
        assert caught.value.reason == "corpus-drifted" and caught.value.refs == (BETA,)
        assert evaluate_query(before, stored_query(Corpus(roots[ALPHA]).get(topic.id))).complete

    def test_records_outside_the_map_report_unmapped_under_equal_states_and_do_not_refuse(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        view = open_world_view(world, published)
        (report,) = [r for r in view.drift() if r.corpus_id == ALPHA]
        assert report.captured_state == report.published_state and report.unmapped  # the project and topic uids
        assert evaluate_query(view, stored_query(Corpus(roots[ALPHA]).get(topic.id))).complete

    def test_a_damaged_view_refuses_before_drift_is_read(self, tmp_path):
        from test_world_view import damage

        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        damage(roots[BETA], "parse-error")
        view = open_world_view(world, published, on_damage="report")
        with pytest.raises(SelectionRefused) as caught:
            evaluate_query(view, stored_query(Corpus(roots[ALPHA]).get(topic.id)))
        assert caught.value.reason == "corpus-damaged" and caught.value.refs == (BETA,)

    def test_an_unknown_address_refuses_naming_every_unknown_one(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:never", "dataset:d-b"]}], [{"addresses": ["run:never"]}]
        )
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-unknown"
        assert caught.value.refs == ("dataset:never", "run:never") and caught.value.corpus_ids == ()

    def test_a_not_present_address_refuses_naming_its_corpus_and_never_reads_as_empty(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        make_absent(roots, BETA)
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-not-present"
        assert caught.value.refs == ("dataset:d-b",) and caught.value.corpus_ids == (BETA,)

    def test_unknown_outranks_not_present_and_the_two_never_share_a_refusal(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:d-b", "dataset:never"]}]
        )
        make_absent(roots, BETA)
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-unknown" and caught.value.refs == ("dataset:never",)


class TestAbsenceAndValidation:
    def test_kinds_over_an_absent_corpus_is_incomplete_and_names_it(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        complete = evaluate_topic(world, roots, published, topic)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert partial.selected == ("dataset:d-a",) and partial.absent == (BETA,) and not partial.complete
        assert partial.projection()["absent"] == [BETA]  # the member itself, not only the identity
        assert partial.identity() != complete.identity()

    def test_absent_alone_moves_the_identity(self, tmp_path):
        """`clauses: []` selects nothing either way, so only `absent` differs."""
        world, roots, published, topic = topic_world(tmp_path)
        complete = evaluate_topic(world, roots, published, topic)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert complete.selected == partial.selected == () and complete.contributing == partial.contributing == ()
        assert partial.projection()["absent"] == [BETA] and partial.identity() != complete.identity()

    def test_a_selected_record_with_a_stale_hash_refuses(self, tmp_path):
        stale = stored.dataset_node("d-s", title="d-s")
        stale.facets["dataset"]["resources"] = [{"digest": "f" * 64}]  # edited after stamping: stale on disk
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}], alpha_extra=(stale,))
        with pytest.raises(SemanticHashStale):
            evaluate_topic(world, roots, published, topic)
```

The stale record is staged *before* publication — the epoch capture is `iter_stored`'s unvalidated read (`epoch.py:1188`), so the record is mapped and the view is not drifted; the refusal is validation's, not drift's.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py`
Expected: FAIL at collection with `ModuleNotFoundError: beliefs.world.selection`.

- [ ] **Step 3: Write the module**

Create `python/src/beliefs/world/selection.py`:

```python
"""View-query evaluation over the world read view.

World resolution slice 4 §3. `evaluate_query` is a pure function of an open
`WorldReadView` and a parsed `ViewQuery`: it opens nothing, names no
`current`, reads no coordination record and consults no profile. It refuses
a damaged or drifted capture at entry, locates every address the query
names before denoting anything, and reports absence and dangling steps on
the selection instead of folding them into it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, final

from nodes.core.node import Node

from beliefs.corpus import validated_node
from beliefs.errors import SelectionRefused
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import Addresses, Closure, Kinds, Predicate, ReferencesTerm, ViewQuery
from beliefs.world.read import BoundStamp, NotPresent, Unknown
from beliefs.world.view import WorldReadView

__all__ = ["SELECTION_VERSION", "Selection", "Unresolved", "evaluate_query"]

SELECTION_VERSION = "science.view-selection.v1"

UnresolvedState = Literal["not-present", "unknown"]


@final
@dataclass(frozen=True)
class Unresolved:
    """One closure step that reached nothing, with the state `locate` gave
    its target and, for `not-present`, the absent corpus."""

    source: str
    predicate: str
    target: str
    state: UnresolvedState
    corpus_id: str | None

    def __post_init__(self) -> None:
        if self.state not in ("not-present", "unknown"):
            raise ValueError(f"{self.state!r} is not an unresolved state")
        if (self.corpus_id is None) != (self.state == "unknown"):
            raise ValueError("a not-present step names its corpus and an unknown one names none")

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.source, self.predicate, self.target)

    def projection(self) -> dict[str, object]:
        return {
            "source": self.source,
            "predicate": self.predicate,
            "target": self.target,
            "state": self.state,
            "corpus_id": [] if self.corpus_id is None else [self.corpus_id],
        }


@sealed
@final
@dataclass(frozen=True)
class Selection:
    """What a query denotes at one publication (§3.1). `complete` is derived
    and not a projection member: a member could disagree with the two it is
    computed from."""

    stamp: BoundStamp
    query: ViewQuery
    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    absent: tuple[str, ...]
    unresolved: tuple[Unresolved, ...]

    @property
    def complete(self) -> bool:
        return not self.absent and all(step.state != "not-present" for step in self.unresolved)

    def projection(self) -> dict[str, object]:
        return {
            "version": SELECTION_VERSION,
            "epoch": self.stamp.packaging_identity,
            "query": self.query.projection(),
            "selected": list(self.selected),
            "contributing": list(self.contributing),
            "absent": list(self.absent),
            "unresolved": [step.projection() for step in self.unresolved],
        }

    def identity(self) -> str:
        return v1.digest(SELECTION_VERSION, self.projection())


Held = Mapping[str, tuple[str, Node]]
"""Live address -> (corpus_id, retained record), one enumeration of the capture."""


def evaluate_query(view: WorldReadView, query: ViewQuery) -> Selection:
    """Denote `query` over `view` (§3.2), or refuse."""
    if type(view) is not WorldReadView:
        raise TypeError(
            f"evaluate_query takes a WorldReadView, not {type(view).__name__}: a corpus-local selection is the "
            "fb-2026-07-30-019 defect W7 exists to refuse"
        )
    if not isinstance(query, ViewQuery):
        raise TypeError(f"evaluate_query takes a parsed ViewQuery, not {type(query).__name__}")
    if view.damaged():
        raise SelectionRefused("corpus-damaged", refs=[report.corpus_id for report in view.damaged()])
    moved = [report.corpus_id for report in view.drift() if report.captured_state != report.published_state]
    if moved:
        # A report whose states agree lists records outside the world map by
        # construction (coordination and prose kinds); only a moved state refuses.
        raise SelectionRefused("corpus-drifted", refs=moved)
    _require_located(view, query.addresses())

    held: dict[str, tuple[str, Node]] = {node.id: (corpus_id, node) for corpus_id, node in view._mapped_records()}
    unresolved: dict[tuple[str, str, str], Unresolved] = {}
    selected: set[str] = set()
    for clause in query.clauses:
        members: set[str] | None = None
        for predicate in clause.predicates:
            denoted = _denote(view, predicate, held, unresolved)
            members = denoted if members is None else members & denoted
        selected |= members or set()

    for address in selected:
        validated_node(held[address][1])
    contributing = sorted({held[address][0] for address in selected})
    return Selection(
        stamp=view.stamp,
        query=query,
        selected=tuple(sorted(selected)),
        contributing=tuple(contributing),
        absent=view.absent(),
        unresolved=tuple(sorted(unresolved.values(), key=lambda step: step.sort_key)),
    )


def _require_located(view: WorldReadView, addresses: tuple[str, ...]) -> None:
    """Every address the query names resolves, or the evaluation refuses
    naming each offender of the worst state; unknown and not-present never
    share one refusal (W6)."""
    unknown: list[str] = []
    not_present: list[tuple[str, str]] = []
    for address in addresses:
        located = view.locate(address)
        if type(located) is Unknown:
            unknown.append(address)
        elif type(located) is NotPresent:
            corpus_id = view.corpus_of(address)
            assert corpus_id is not None
            not_present.append((address, corpus_id))
    if unknown:
        raise SelectionRefused("address-unknown", refs=unknown)
    if not_present:
        raise SelectionRefused(
            "address-not-present",
            refs=[address for address, _ in not_present],
            corpus_ids=[corpus_id for _, corpus_id in not_present],
        )


def _denote(
    view: WorldReadView,
    predicate: Predicate,
    held: Held,
    unresolved: dict[tuple[str, str, str], Unresolved],
) -> set[str]:
    if isinstance(predicate, Kinds):
        kinds = set(predicate.values)
        return {address for address, (_, node) in held.items() if node.kind in kinds}
    if isinstance(predicate, Addresses):
        resolved: set[str] = set()
        for address in predicate.values:
            live = view.resolve(address)
            assert live is not None, address  # _require_located ran
            resolved.add(live)
        return resolved
    if isinstance(predicate, ReferencesTerm):
        raise NotImplementedError("references-term lands in Task 4")
    if isinstance(predicate, Closure):
        raise NotImplementedError("closure lands in Task 5")
    raise TypeError(f"{type(predicate).__name__} is not a v1 predicate")
```

In `python/src/beliefs/world/__init__.py` add `from beliefs.world.selection import Selection, Unresolved, evaluate_query` beside the `view` import and the three names to `__all__` in alphabetical position (`"Selection"`, `"Unresolved"` among the classes; `"evaluate_query"` among the functions).

- [ ] **Step 4: Run the tests and the gate**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py tests/test_world_view.py tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: every test in `TestAddressesAndKinds`, `TestIdentityAndDeterminism`, `TestEntryRefusals` and `TestAbsenceAndValidation` passes; the staleness probes pass.

Run: `uv run --frozen ruff check . && uv run --frozen pyright`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note beliefs-9454aa "world/selection.py: Selection, Unresolved, evaluate_query over kinds and addresses; entry refusals; identity"
tasks done beliefs-9454aa "the evaluator's skeleton, kinds and addresses, entry refusals, identity"
git add python/src python/tests tasks
git commit -m "feat(world): evaluate_query over the world read view, kinds and addresses"
```

---

### Task 4: `references-term` with validation before the facet read

**Files:**
- Modify: `python/src/beliefs/decode.py` (after `claim_from_stored`), `python/src/beliefs/world/selection.py` (`_denote`, new `_binds_term`)
- Test: `python/tests/test_decode.py` (or the module that tests `claim_from_stored`; find it with `grep -rl claim_from_stored python/tests`), `python/tests/test_world_selection.py`

**Interfaces:**
- Consumes: Task 3's `_denote` seam and `held`; `decode._wire_parts` and `decode.MalformedWireClaim`.
- Produces: `decode.stored_claim_terms(node) -> tuple[tuple[str, ...], tuple[str, ...]]` — `(argument terms, restriction terms)` after the shape check, no profile; the `ReferencesTerm` branch; `_binds_term(node: Node, term: str) -> bool`, which validates first and translates `MalformedWireClaim` into `record-malformed`.

- [ ] **Step 1: `tasks start beliefs-d1c305`, then write the failing tests**

Append to `python/tests/test_world_selection.py`:

```python
class TestReferencesTerm:
    def test_a_term_in_an_argument_selects_the_proposition_and_never_a_dataset(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("proposition:p-b",) and selection.contributing == (BETA,)

    def test_a_term_in_a_qualifier_restriction_selects(self, tmp_path):
        qualified = stored.proposition_node(
            "p-q", title="p-q",
            claim={**CLAIM_FACET, "qualifiers": {"tissue": {"quantifier": "some", "restriction": "EX:liver"}}},
        )
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": "EX:liver"}], beta_extra=(qualified,))
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("proposition:p-q",)

    def test_a_term_absent_everywhere_selects_nothing_and_refuses_nothing(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": "EX:nothing"}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == () and selection.complete

    def test_the_term_is_compared_as_stored_without_normalization(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE.upper()}])
        assert evaluate_topic(world, roots, published, topic).selected == ()

    @pytest.mark.parametrize(
        "claim",
        [
            {**CLAIM_FACET, "args": "not-a-list"},
            {**CLAIM_FACET, "args": [GENE, 7]},
            {**CLAIM_FACET, "qualifiers": {"tissue": {"restriction": "EX:liver"}}},  # no quantifier
            {**CLAIM_FACET, "qualifiers": {"tissue": {"quantifier": "some", "restriction": "EX:liver", "extra": 1}}},
            {k: v for k, v in CLAIM_FACET.items() if k != "layer"},
        ],
    )
    def test_a_malformed_claim_facet_refuses_naming_the_record(self, tmp_path, claim):
        broken = stored.proposition_node("p-x", title="p-x", claim=claim)
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE}], beta_extra=(broken,))
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "record-malformed" and caught.value.refs == ("proposition:p-x",)

    def test_a_stale_edit_that_removed_the_term_refuses_rather_than_yielding_empty(self, tmp_path):
        stale = stored.proposition_node("p-s", title="p-s", claim=CLAIM_FACET)
        stale.facets["proposition"]["args"] = ["EX:other", PHENO]  # edited after stamping: the stamp covers GENE
        world, roots, published, topic = topic_world(
            tmp_path, [{"references-term": GENE}], beta_extra=(stale,), without=("proposition:p-b",),
        )
        with pytest.raises(SemanticHashStale):
            evaluate_topic(world, roots, published, topic)
```

The corrupt non-match: with `p-b` dropped, the only proposition is the stale one whose stored `args` no longer hold `GENE`, so an unvalidated scan would yield the empty selection; the arm requires the refusal.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py -k ReferencesTerm`
Expected: FAIL with `NotImplementedError: references-term lands in Task 4`.

- [ ] **Step 3: Implement**

In `python/src/beliefs/decode.py`, after `claim_from_stored`, factor its pre-delegation shape check into a public reader that never needs a profile (the `WireClaim` still never leaves the module):

```python
def stored_claim_terms(node: Node) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The argument terms and the qualifier restriction terms of a stored
    proposition's claim facet, after `_wire_parts`' shape check and before any
    profile is consulted (world resolution slice 4 §3.2). Every ill-formed
    facet refuses with `MalformedWireClaim`, exactly as `claim_from_stored`
    refuses before delegating; nothing is typed or resolved."""
    if not isinstance(node, Node) or node.kind != "proposition":
        raise MalformedWireClaim(f"stored_claim_terms reads a proposition node, found {type(node).__name__}")
    facet = node.facets.get("proposition")
    if not isinstance(facet, Mapping):
        raise MalformedWireClaim(f"{node.id}: no covered claim facet")
    keys = set(facet)
    if keys != _STORED_CLAIM_KEYS:
        missing, extra = sorted(_STORED_CLAIM_KEYS - keys), sorted(keys - _STORED_CLAIM_KEYS)
        raise MalformedWireClaim(f"{node.id}: claim facet missing {missing}, extra {extra}; refused, never repaired")
    if isinstance(facet["args"], str) or not isinstance(facet["args"], Sequence):
        raise MalformedWireClaim(f"{node.id}: args is not a sequence")
    if not isinstance(facet["qualifiers"], Mapping):
        raise MalformedWireClaim(f"{node.id}: qualifiers is not a mapping")
    _, terms, qualifier_bodies, _, _ = _wire_parts(
        WireClaim(
            operator=facet["operator"],
            args=tuple(facet["args"]),
            qualifiers=facet["qualifiers"],
            polarity=facet["polarity"],
            layer=facet["layer"],
        )
    )
    return tuple(terms), tuple(body["restriction"] for body in qualifier_bodies.values())
```

Then make `claim_from_stored` call the same checks by delegating its shape half to this function's body (extract `_stored_wire(node) -> WireClaim` used by both if that reads cleaner; the constraint is one shape check, not two copies). Add one test beside `claim_from_stored`'s: a well-formed facet returns `((GENE, PHENO), ())` and a qualifier lacking `quantifier` raises `MalformedWireClaim`.

In `selection.py` import `from beliefs.decode import MalformedWireClaim, stored_claim_terms` and add the helper, then replace the `ReferencesTerm` branch:

```python
def _binds_term(node: Node, term: str) -> bool:
    """Whether a proposition's stored claim binds `term` as an argument or a
    qualifier restriction (§3.2 step 3). The record is validated **before**
    its facet is read, and the facet's shape is `decode`'s own check; a
    violation is corruption and refuses, never "does not reference". No
    decode against a profile, no normalization: the term is compared as
    stored."""
    validated_node(node)
    try:
        args, restrictions = stored_claim_terms(node)
    except MalformedWireClaim:
        raise SelectionRefused("record-malformed", refs=[node.id]) from None
    return term in args or term in restrictions
```

and in `_denote`:

```python
    if isinstance(predicate, ReferencesTerm):
        return {
            address
            for address, (_, node) in held.items()
            if node.kind == "proposition" and _binds_term(node, predicate.value)
        }
```

- [ ] **Step 4: Run the tests and the gate**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py`
Expected: PASS.

Run: `uv run --frozen ruff check . && uv run --frozen pyright`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note beliefs-d1c305 "references-term denotation: validated before the facet read, malformed facet refuses, compared as stored"
tasks done beliefs-d1c305 "references-term"
git add python/src python/tests tasks
git commit -m "feat(world): references-term denotation with validation before the facet read"
```

---

### Task 5: `closure` from the live anchor through the query adjacency

**Files:**
- Modify: `python/src/beliefs/world/selection.py` (`_denote`, new `_InboundAdjacency`, `_QueryAdjacency`, `_classify`)
- Test: `python/tests/test_world_selection.py`

**Interfaces:**
- Consumes: `corpus.RelationAdjacency(view, predicate, "outbound")`, `traversal.{closure, Step, RelationEntry}`, `view.inbound`, `view.live_id`, `view.locate`, `view.corpus_of`.
- Produces: the `Closure` branch; every unresolved step entered into Task 3's `unresolved` map.

- [ ] **Step 1: `tasks start beliefs-35d582`, then write the failing tests**

Append to `python/tests/test_world_selection.py`:

```python
class TestClosure:
    def test_out_from_the_run_selects_the_other_corpus_dataset_and_not_the_run(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-b",) and selection.contributing == (BETA,)
        assert selection.complete and selection.unresolved == ()

    def test_in_from_the_dataset_selects_the_producing_run_in_the_other_corpus(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "dataset:d-b", "predicates": ["produces"], "direction": "in"}}]
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("run:r-a",) and selection.contributing == (ALPHA,)

    def test_both_walks_both_ways_and_excludes_the_anchor(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "dataset:d-b", "predicates": ["produces"], "direction": "both"}}]
        )
        selection = evaluate_topic(world, roots, published, topic)
        # d-b <-produces- r-a; r-a has no other produces edge; d-b produces nothing.
        assert selection.selected == ("run:r-a",)

    def test_a_dangling_target_is_reported_unknown_and_never_selected(self, tmp_path):
        d_x = stored.dataset_node("d-x", title="d-x")
        d_x.relations.append(Relation(source=d_x.id, predicate="cites", target="dataset:never"))
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "dataset:d-x", "predicates": ["cites"], "direction": "out"}}],
            alpha_extra=(d_x,),
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == () and selection.complete
        assert selection.unresolved == (Unresolved("dataset:d-x", "cites", "dataset:never", "unknown", None),)

    def test_a_traversed_target_in_an_absent_corpus_is_an_incomplete_selection_not_a_refusal(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]
        )
        complete = evaluate_topic(world, roots, published, topic)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert partial.selected == () and partial.absent == (BETA,) and not partial.complete
        assert partial.unresolved == (Unresolved("run:r-a", "produces", "dataset:d-b", "not-present", BETA),)
        assert partial.projection()["unresolved"] == [
            {"source": "run:r-a", "predicate": "produces", "target": "dataset:d-b", "state": "not-present", "corpus_id": [BETA]}
        ]
        assert partial.identity() != complete.identity()

    def test_an_anchor_in_an_absent_corpus_refuses(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "dataset:d-b", "predicates": ["produces"], "direction": "in"}}]
        )
        assert evaluate_topic(world, roots, published, topic).selected == ("run:r-a",)
        make_absent(roots, BETA)
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-not-present" and caught.value.refs == ("dataset:d-b",)

    def test_an_absent_inbound_source_is_reported_not_present_and_not_dropped(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"closure": {"anchor": "dataset:d-a", "predicates": ["produces"], "direction": "in"}}]
        )
        assert evaluate_topic(world, roots, published, topic).selected == ("run:r-b",)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert partial.selected == () and not partial.complete
        assert partial.unresolved == (Unresolved("dataset:d-a", "produces", "run:r-b", "not-present", BETA),)

    def test_a_retired_anchor_over_a_cycle_selects_what_the_live_anchor_selects(self, tmp_path):
        a = stored.dataset_node("cyc-a", title="a")
        b = stored.dataset_node("cyc-b", title="b")
        a.relations.append(Relation(source=a.id, predicate="cites", target=b.id))
        b.relations.append(Relation(source=b.id, predicate="cites", target=a.id))
        a.deprecated_ids = ["dataset:cyc-a-old"]
        live_q = [{"closure": {"anchor": "dataset:cyc-a", "predicates": ["cites"], "direction": "out"}}]
        retired_q = [{"closure": {"anchor": "dataset:cyc-a-old", "predicates": ["cites"], "direction": "out"}}]
        world, roots, published, _topic = topic_world(tmp_path, live_q, alpha_extra=(a, b))
        view = open_world_view(world, published)
        assert evaluate_query(view, query(live_q)).selected == ("dataset:cyc-b",)
        assert evaluate_query(view, query(retired_q)).selected == ("dataset:cyc-b",)

    def test_two_predicates_walk_both_and_steps_are_reported_once(self, tmp_path):
        d_x = stored.dataset_node("d-x", title="d-x")
        d_x.relations.append(Relation(source=d_x.id, predicate="cites", target="dataset:never"))
        d_x.relations.append(Relation(source=d_x.id, predicate="reads", target="dataset:never"))
        world, roots, published, topic = topic_world(
            tmp_path,
            [{"closure": {"anchor": "dataset:d-x", "predicates": ["cites", "reads"], "direction": "out"}}],
            alpha_extra=(d_x,),
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert [(s.predicate, s.target) for s in selection.unresolved] == [("cites", "dataset:never"), ("reads", "dataset:never")]
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py -k Closure`
Expected: FAIL with `NotImplementedError: closure lands in Task 5`.

- [ ] **Step 3: Implement**

In `selection.py` add the imports `from beliefs.corpus import RelationAdjacency, validated_node` (extend the existing line) and `from beliefs.traversal import Adjacency, RelationEntry, Step, closure`, then:

```python
class _InboundAdjacency:
    """Inbound edges under one predicate over the world view, reporting a
    mapped source in an absent corpus as a step that resolves to nothing
    (spec decision 3) where `RelationAdjacency._inbound` drops it."""

    def __init__(self, view: WorldReadView, predicate: str) -> None:
        self._view = view
        self._predicate = predicate

    def steps(self, ref: str) -> tuple[Step, ...]:
        steps: list[Step] = []
        for position, edge in enumerate(self._view.inbound(ref)):
            if edge.relation.predicate != self._predicate:
                continue
            if edge.source_uid is None:
                steps.append(
                    Step(
                        stored=edge.relation.source,
                        resolved=None,
                        entry=RelationEntry(source=ref, position=position, predicate=self._predicate, target=edge.relation.source),
                    )
                )
                continue
            source_id = self._view.live_id(edge.source_uid)
            steps.append(
                Step(
                    stored=source_id,
                    resolved=source_id,
                    entry=RelationEntry(source=ref, position=position, predicate=self._predicate, target=source_id),
                )
            )
        return tuple(steps)


class _QueryAdjacency:
    """One `closure` predicate's adjacencies, composed in predicate order
    then direction order (§3.3)."""

    def __init__(self, view: WorldReadView, predicates: tuple[str, ...], direction: str) -> None:
        parts: list[Adjacency] = []
        for predicate in predicates:
            if direction in ("out", "both"):
                parts.append(RelationAdjacency(view, predicate, "outbound"))
            if direction in ("in", "both"):
                parts.append(_InboundAdjacency(view, predicate))
        self._parts = tuple(parts)

    def steps(self, ref: str) -> tuple[Step, ...]:
        return tuple(step for part in self._parts for step in part.steps(ref))


def _classify(view: WorldReadView, entry: RelationEntry) -> Unresolved:
    located = view.locate(entry.target)
    if type(located) is NotPresent:
        corpus_id = view.corpus_of(entry.target)
        assert corpus_id is not None
        return Unresolved(entry.source, entry.predicate, entry.target, "not-present", corpus_id)
    assert type(located) is Unknown, entry
    return Unresolved(entry.source, entry.predicate, entry.target, "unknown", None)
```

and in `_denote`:

```python
    if isinstance(predicate, Closure):
        live = view.resolve(predicate.anchor)
        assert live is not None, predicate.anchor  # _require_located ran; the walk starts from the live address (§3.2 step 3)
        reach = closure(live, _QueryAdjacency(view, predicate.predicates, predicate.direction))
        for entry in reach.unresolved:
            assert isinstance(entry, RelationEntry), entry
            step = _classify(view, entry)
            unresolved.setdefault(step.sort_key, step)
        return set(reach.reached)
```

- [ ] **Step 4: Run the tests and the gate**

Run: `cd python && uv run --frozen pytest tests/test_world_selection.py tests/test_world_view.py`
Expected: PASS.

If `test_both_walks_both_ways_and_excludes_the_anchor` reaches `dataset:d-a` through `r-a`'s other edges, read the fixture: `r-a` produces only `d-b`, so the `both` walk from `d-b` reaches `r-a` inbound and then nothing further outbound from `r-a` except `d-b` itself (already seen). The expected set is `("run:r-a",)`.

Run: `uv run --frozen ruff check . && uv run --frozen pyright`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note beliefs-35d582 "closure denotation: live anchor, query adjacency with reported absent inbound sources, unresolved classified by locate"
tasks done beliefs-35d582 "closure"
git add python/src python/tests tasks
git commit -m "feat(world): closure denotation from the live anchor through the query adjacency"
```

---

### Task 6: W8 and W8b unit arms over existing code

**Files:**
- Create: `python/tests/test_world_conflicts.py`

**Interfaces:**
- Consumes: `test_world_epoch.{admitted_world, publish, epochs_tree}`, `test_world_build.{ALPHA, BETA}`, `relocation.{consolidate, move}`, `corpus.corpus_check`, `errors.{AddressMapConflict, AddressDisagreement, HistoryDisagreement, DuplicateLocation, SourceAddressDisagreement}`, `test_relocation._writer` and `CONSOLIDATE_FIELDS`, `test_identifier_correction.{A, B, ADDR_B, REPORT}`.
- Produces: the unit-level readings Task 7 lifts onto the certified volume, one function per §4 bullet.

- [ ] **Step 1: `tasks start beliefs-7d4299`, then write the tests**

These arms read code that already passes; they are written to fail under Task 7's sabotages, so write each assertion to name the exact property.

```python
"""W8 and W8b read over existing code (slice 4 §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_cut4 import raw_write
from nodes.core.corpus import Corpus
from profiles import WITH_BIOLOGY
from test_identifier_correction import A, B, ADDR_B, REPORT
from test_relocation import CONSOLIDATE_FIELDS, MOVE_FIELDS, _writer
from test_world_build import ALPHA, BETA, make_world
from test_world_epoch import admitted_world, derivation_bindings, epochs_tree, publish

GAMMA = "c" * 32

from beliefs import relocation, stored
from beliefs.corpus import ReadView, corpus_check
from beliefs.errors import (
    AddressDisagreement,
    AddressMapConflict,
    DuplicateLocation,
    HistoryDisagreement,
    SourceAddressDisagreement,
)
from beliefs.world import registry
from beliefs.world.view import open_world_view


def conflict_world(tmp_path: Path, *, coverage=(ALPHA, BETA), twin_of="dataset:a", same_address=True, same_uid=False):
    """Two admitted corpora, BETA holding a twin of ALPHA's record."""
    world, recorder, bindings, roots = admitted_world(tmp_path, coverage)
    original = Corpus(roots[coverage[0]]).get(twin_of)
    twin = original.model_copy(deep=True, update={
        "id": original.id if same_address else "dataset:twin",
        "uid": original.uid if same_uid else "d" * 32,
    })
    raw_write(roots[coverage[1]], twin)
    return world, recorder, bindings, roots, original, twin


class TestW8DuplicateLocation:
    def test_the_build_refuses_naming_both_claims_and_no_carrier(self, tmp_path):
        world, _r, bindings, roots, original, _twin = conflict_world(tmp_path)
        before = epochs_tree(world)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        finding = caught.value.finding
        assert finding.code == "duplicate-location" and finding.ref == original.id
        assert finding.detail.index(ALPHA) < finding.detail.index(BETA)  # the capture's sorted order
        assert "resolve with consolidate" in finding.message and str(roots[ALPHA]) not in finding.detail
        assert epochs_tree(world) == before

    def test_the_other_registration_order_gives_the_same_code_ref_and_claims(self, tmp_path):
        _world, _r, _b, roots, _o, _t = conflict_world(tmp_path)
        findings = []
        for name, order in (("f", (roots[ALPHA], roots[BETA])), ("b", (roots[BETA], roots[ALPHA]))):
            world = make_world(tmp_path / name, *order)
            for corpus_root in order:
                world.admit(corpus_root, provenance=registry.Fresh())
            with pytest.raises(AddressMapConflict) as caught:
                publish(world, (ALPHA, BETA), derivation_bindings(world))
            findings.append(caught.value.finding)
        assert (findings[0].code, findings[0].ref, findings[0].detail) == (findings[1].code, findings[1].ref, findings[1].detail)
        assert findings[0].code == "duplicate-location"

    @pytest.mark.parametrize("keep_first", [True, False])
    def test_consolidate_repairs_with_the_authored_survivor_and_the_rebuild_publishes(self, tmp_path, keep_first):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        record = stored.source_node(title="kept", identifiers={"doi": "10.1234/abc"})
        left.add(record)
        right.add(record.model_copy(deep=True, update={"uid": "e" * 32}))
        keep, other = (left, right) if keep_first else (right, left)
        survivor, _, _ = relocation.consolidate((keep, record.id), (other, record.id), **CONSOLIDATE_FIELDS)
        assert survivor.uid == keep.read_view.get(record.id).uid
        assert other.read_view.resolve(record.id) is None

    def test_move_into_the_occupied_destination_refuses_thereafter(self, tmp_path):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        record = stored.source_node(title="kept", identifiers={"doi": "10.1234/abc"})
        left.add(record)
        right.add(record.model_copy(deep=True))
        with pytest.raises(DuplicateLocation):
            relocation.move(left, right, record.id, **MOVE_FIELDS)


class TestW8AddressConflict:
    def test_disagreeing_bases_at_one_address_refuse_the_build_before_any_basis_is_read(self, tmp_path):
        world, _r, bindings, roots = admitted_world(tmp_path, (ALPHA, BETA))
        raw_write(roots[ALPHA], stored.source_node(title="p", identifiers=B))
        raw_write(roots[BETA], stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        assert caught.value.finding.code == "duplicate-location" and caught.value.finding.ref == ADDR_B

    @pytest.mark.parametrize("keep_first", [True, False])
    def test_consolidate_refuses_and_no_basis_wins(self, tmp_path, keep_first):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        left.add(stored.source_node(title="p", identifiers=B))
        right.add(stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        keep, other = (left, right) if keep_first else (right, left)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        with pytest.raises(HistoryDisagreement):
            relocation.consolidate((keep, ADDR_B), (other, ADDR_B), rationale="r", **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before

    def test_a_source_at_the_wrong_address_refuses_at_the_write_boundary(self, tmp_path):
        writer = _writer(tmp_path / "only")
        forged = stored.source_node(title="p", identifiers=B).model_copy(update={"id": "source:Chen2023"})
        with pytest.raises(SourceAddressDisagreement):
            writer.add(forged)


class TestW8b:
    def test_one_uid_under_two_addresses_is_corruption_and_no_repair_is_offered(self, tmp_path):
        world, _r, bindings, _roots, original, _twin = conflict_world(tmp_path, same_address=False, same_uid=True)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        finding = caught.value.finding
        assert finding.code == "uid-corruption" and finding.ref == original.uid
        assert "no repair is offered" in finding.message and "consolidate" not in finding.message
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        keep = left.add(stored.source_node(title="kept", identifiers={"doi": "10.1234/kept"}))
        other = right.add(stored.source_node(title="other", identifiers={"doi": "10.1234/other"}).model_copy(update={"uid": keep.uid}))
        with pytest.raises(AddressDisagreement):
            relocation.consolidate((left, keep.id), (right, other.id), **CONSOLIDATE_FIELDS)

    @pytest.mark.parametrize("same_uid", [True, False])
    def test_two_records_at_one_address_are_duplicate_location_with_shared_or_distinct_uids(self, tmp_path, same_uid):
        world, _r, bindings, _roots, original, _twin = conflict_world(tmp_path, same_uid=same_uid)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        assert (caught.value.finding.code, caught.value.finding.ref) == ("duplicate-location", original.id)

    def test_corruption_outranks_duplication(self, tmp_path):
        # A third corpus: a second record sharing the uid inside BETA is a corpus-local
        # `CollisionError` at open, before the world-level ordering check is reached.
        world, _r, bindings, roots, original, _twin = conflict_world(tmp_path, coverage=(ALPHA, BETA, GAMMA), same_uid=True)
        third = original.model_copy(deep=True, update={"id": "dataset:third"})
        raw_write(roots[GAMMA], third)  # the shared uid now also names a third address
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA, GAMMA), bindings)
        assert caught.value.finding.code == "uid-corruption"

    def test_each_corpus_alone_reports_neither(self, tmp_path):
        world, _r, bindings, roots, _o, _t = conflict_world(tmp_path)
        for corpus_id in (ALPHA, BETA):
            publish(world, (corpus_id,), bindings)
            findings = corpus_check(ReadView.opened_at(roots[corpus_id]), WITH_BIOLOGY)
            assert not [f for f in findings if f.code in ("uid-corruption", "duplicate-location")]
```

`sample_nodes(slug_for(corpus_id, coverage))` names each corpus's records by the corpus id's first character (`test_world_build.py:209`), so ALPHA's dataset is `dataset:a` under any multi-corpus coverage; the registration-order test reuses one set of roots under two worlds admitted in opposite order, so the claims are identical and the whole finding is compared.

- [ ] **Step 2: Run them**

Run: `cd python && uv run --frozen pytest tests/test_world_conflicts.py`
Expected: PASS — these read existing code. A failure is a finding about that code or the fixture; record it in `tasks note` and fix the fixture, never the production code, unless the spec's §4 claim is measured false, in which case stop and report.

If `corpus_check` with `WITH_BIOLOGY` refuses because the `sample_nodes` manifest pins `PINS` (biology), that is the intended profile; if it refuses on a base mismatch use `profiles.BASE`.

- [ ] **Step 3: Gate and commit**

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note beliefs-7d4299 "W8 duplicate-location and address-conflict arms and W8b's four arms read over existing code, unit level"
tasks done beliefs-7d4299 "W8/W8b unit arms"
git add python/tests tasks
git commit -m "test(world): W8 and W8b arms over the existing build, consolidate and move"
```

---

### Task 7: Durable arms, N2 declarations and the guard

**Files:**
- Create: `python/tests/acceptance/test_world_selection_acceptance.py`, `python/tests/acceptance/n2_arms_cut28.py` (canonical), `python/tests/acceptance/test_n2_cut28.py`

**Interfaces:**
- Consumes: `test_world_view_acceptance.durable_world` (the certified-volume two-corpus fixture; `make(alpha_nodes, beta_nodes, *, profile=BASE, raw=())` returns `world, {a: alpha, b: beta}, published, a, b` and exposes `make.corpus()`), `coordination_fixtures.{coordination_profile, raw_coordination_node}`, `corpus.CoordinationResolver`, `coordination.CoordinationAddress`, Tasks 2–6's public names, `n2_arms.Arm`/`Sabotage`, `test_n2.audit`/`baseline`, cut 27's guard as the template.
- Produces: `DECLARATION_UNITS = ("W7", "W8", "W8b")`, `CUT28_ARMS` (23 arms), `UNIT_CHECKS`, `unit_of`; the durable tests Task 8's runner names; the pins `CUT28_FREEZE_COMMIT`, `CUT28_FROZEN_SHA256`, `CUT28_DECLARATION_COMMIT`, `CUT28_DECLARATION_SHA256`.

- [ ] **Step 1: `tasks start beliefs-10efda`, then write the durable arms**

Create `python/tests/acceptance/test_world_selection_acceptance.py`. Header and fixtures:

```python
"""Cut 28: view evaluation and the W8/W8b conflicts over certified durable roots."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_coordination_node
from durable_fixture import pinned
from fixtures_cut4 import raw_write
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from profiles import BASE
from test_evaluation import CLAIM_FACET, GENE, PHENO
from test_world_selection import PROJECT, REVISION, TOPIC, query, topic_nodes
from test_world_view import damage
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.

from beliefs import relocation, stored
from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CoordinationResolver, ReadView, corpus_check
from beliefs.errors import (
    AddressDisagreement,
    AddressMapConflict,
    DuplicateLocation,
    HistoryDisagreement,
    SelectionRefused,
    SemanticHashStale,
    SourceAddressDisagreement,
)
from beliefs.root import init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, epoch
from beliefs.world.selection import Unresolved, evaluate_query
from beliefs.world.view import open_world_view
from test_world_receipts import hold_shipped

MOVE_FIELDS = {"observer": "o", "instrument": "i", "opened_at": "2026-09-14T00:00:00Z", "closed_at": "2026-09-14T00:00:01Z"}
CONSOLIDATE_FIELDS = {**MOVE_FIELDS, "rationale": "keep holds the authored record"}
COORDINATION = coordination_profile(None)


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut28-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def topic_record(*clauses):
    return raw_coordination_node(
        "topic", PROJECT, REVISION, local=TOPIC,
        query={"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]},
    )


@pytest.fixture()
def topic(durable_world, scratch):
    """The topic world on the certified volume: the coordination pin in both
    manifests; `alpha_extra`/`beta_extra` go through the durable writer,
    `alpha_raw`/`beta_raw` are raw-written (the corruption arms stage a stale
    stamp the writer would refuse), the project and topic are raw-written into
    ALPHA, and `without` drops fixture records by id — all before publication."""
    def make(*clauses, alpha_extra=(), beta_extra=(), alpha_raw=(), beta_raw=(), without=()):
        alpha_nodes, beta_nodes = topic_nodes()
        alpha_nodes = tuple(n for n in alpha_nodes if n.kind != "project" and n.id not in without)
        beta_nodes = tuple(n for n in beta_nodes if n.id not in without)
        project = next(n for n in topic_nodes()[0] if n.kind == "project")
        a, alpha, left = durable_world.corpus(COORDINATION)
        b, beta, right = durable_world.corpus(COORDINATION)
        for writer, nodes in ((left, (*alpha_nodes, *alpha_extra)), (right, (*beta_nodes, *beta_extra))):
            for node in nodes:
                node = node.model_copy(deep=True)
                if node.kind == "dataset" and not node.facets["dataset"]["resources"]:
                    node.facets["dataset"]["resources"] = pinned()
                    stored.stamp_semantic_identity(node)
                writer.add(node)
        for node in (project, topic_record(*clauses), *alpha_raw):
            raw_write(alpha, node)
        for node in beta_raw:
            raw_write(beta, node)
        config = WorldConfig(scratch / "topic-world", "e" * 32, (alpha, beta))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(alpha, provenance=Fresh())
        world.admit(beta, provenance=Fresh())
        published = epoch.build_epoch(world, coverage=frozenset((a, b)), bindings=hold_shipped(world))
        return world, {a: alpha, b: beta}, published, a, b
    return make


def resolved_query(roots, a):
    """The caller's half: the topic resolves live through the coordination resolver."""
    resolver = CoordinationResolver({roots[a]: COORDINATION})
    record = resolver.resolve(CoordinationAddress(PROJECT, TOPIC))
    assert record is not None and not hasattr(record, "reason"), record
    return stored_query(record)


def absent(roots, corpus_id):
    (roots[corpus_id] / "corpus.yaml").unlink()


def conflict_world(durable_world, scratch, alpha_nodes, beta_nodes, *, twin):
    """Two certified corpora and a world admitting both, BETA holding `twin` raw-written after admission."""
    a, alpha, left = durable_world.corpus()
    b, beta, right = durable_world.corpus()
    for node in alpha_nodes:
        left.add(node)
    for node in beta_nodes:
        right.add(node)
    raw_write(beta, twin)
    config = WorldConfig(scratch / "world", "e" * 32, (alpha, beta))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(alpha, provenance=Fresh())
    world.admit(beta, provenance=Fresh())
    return world, {a: alpha, b: beta}, (a, b), (left, right), hold_shipped(world)
```

`durable_world.corpus(profile)` registers a certified root and adopts `pins_for(profile)`, so both manifests carry the coordination pin the resolver checks; `pinned` is `durable_fixture.pinned` (import it). A dataset passed with empty `resources` is re-stamped after `pinned()` exactly as `durable_world.make` does. Corpus ids are opaque and minted, so every expected `contributing` is written `tuple(sorted((a, b)))`, never `(a, b)`.

Then the durable tests, one per spec §7 bullet, each ending in `_durably`, built from the unit tests of Tasks 3–6 by replacing `topic_world` with the `topic` fixture, `ALPHA`/`BETA` with the returned `a`/`b`, `evaluate_topic` with `evaluate_query(open_world_view(world, published), resolved_query(roots, a))`, and `tmp_path` writers with `durable_world.corpus()` writers. The required functions and what each asserts:

| test | asserts |
|---|---|
| `test_w7_addresses_selects_the_other_corpus_record_and_contributes_its_corpus_durably` | `selected == (dataset:d-b,)`, `contributing == (b,)`, complete; identity equal across two opens |
| `test_w7_kinds_selects_and_contributes_both_corpora_durably` | both datasets, `contributing == tuple(sorted((a, b)))` |
| `test_w7_closure_out_selects_the_other_corpus_dataset_and_not_the_run_durably` | `(dataset:d-b,)`, `(b,)` |
| `test_w7_references_term_selects_the_proposition_and_never_a_dataset_durably` | `(proposition:p-b,)`, `(b,)` |
| `test_w7_two_clauses_select_and_contribute_both_durably` | `addresses` over `dataset:d-a` plus `references-term` GENE: both selected, `contributing == tuple(sorted((a, b)))` |
| `test_w7_the_absent_corpus_refuses_reports_or_names_itself_by_form_durably` | after `absent(roots, b)`: `addresses` → `SelectionRefused("address-not-present")` refs `(dataset:d-b,)` corpora `(b,)`; `closure` out from `run:r-a` → incomplete, `unresolved == (Unresolved("run:r-a","produces","dataset:d-b","not-present", b),)`; `kinds` → incomplete, `absent == (b,)`; each incomplete identity differs from its complete one and none is empty-and-complete |
| `test_w7_a_closure_anchored_in_the_absent_corpus_refuses_durably` | `in` over `produces` from `dataset:d-b` selects `run:r-a` present; refuses `address-not-present` refs `(dataset:d-b,)` absent |
| `test_w7_a_drifted_view_refuses_and_the_earlier_capture_evaluates_durably` | Task 3's drift arm: filter reports by `captured_state != published_state` and assert only `b` moved; then a rebuild (`epoch.build_epoch` with `hold_shipped`) evaluates clean with a different identity |
| `test_w7_a_damaged_view_refuses_durably` | Task 3's damage arm |
| `test_w7_reordered_authoring_and_registration_give_one_projection_durably` | Task 3's two determinism arms, the registration case over two `conflict_world`-style worlds with the corpora admitted in opposite order |
| `test_w7_a_retired_anchor_over_a_cycle_selects_what_the_live_anchor_selects_durably` | Task 5's cycle arm |
| `test_w7_dangling_and_absent_inbound_steps_are_reported_not_dropped_durably` | Task 5's dangling arm and absent-inbound arm |
| `test_w7_a_retired_and_a_live_address_select_once_durably` | Task 3's arm |
| `test_w7_terms_in_arguments_and_restrictions_select_and_a_malformed_facet_refuses_durably` | Task 4's three arms |
| `test_w7_a_stale_edit_that_removed_the_term_refuses_durably` | Task 4's corrupt non-match, staged with `beta_raw=(stale,)` and `without=("proposition:p-b",)` |
| `test_w7_a_stale_selected_record_refuses_durably` | Task 3's arm, staged with `alpha_raw=(stale,)` |
| `test_w7_projection_members_are_asserted_directly_durably` | Task 3's `absent`-alone identity arm over `clauses: []`, plus `projection()["absent"] == [b]` and the literal `projection()["unresolved"]` entry of the closure-out-with-`b`-absent case |
| `test_w7_empty_clauses_and_a_read_view_durably` | `clauses: []` complete and empty; `ReadView` → `TypeError` |
| `test_w7_an_unknown_address_refuses_naming_every_unknown_one_durably` | Task 3's arm: `address-unknown`, every unknown address, no corpus; unknown outranks not-present |
| `test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably` | Task 6's four duplicate-location arms over `conflict_world`, `consolidate` parametrized on `keep`, the rebuild publishing and the view serving one record, `move` refusing `DuplicateLocation` |
| `test_w8_address_conflict_refuses_the_build_and_consolidate_and_the_write_boundary_durably` | Task 6's three address-conflict arms |
| `test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably` | Task 6's arm |
| `test_w8b_duplicate_location_is_the_same_finding_with_shared_or_distinct_uids_durably` | Task 6's arm, both uids |
| `test_w8b_corruption_outranks_duplication_and_a_corpus_alone_reports_neither_durably` | Task 6's last two arms |

For the W8 `source` fixtures use `stored.source_node(title=..., identifiers={"doi": ...})` and for the W8b dataset fixtures the `dataset` twins of Task 6, with `pinned()` resources from `durable_fixture` if the durable writer refuses an empty resource list (as `durable_world.make` does).

Run: `cd python && uv run --frozen pytest tests/acceptance/test_world_selection_acceptance.py`
Expected: all pass on the certified volume (the `work_directory` fixture refuses elsewhere).

- [ ] **Step 2: The declaration module**

Create `python/tests/acceptance/n2_arms_cut28.py` on `n2_arms_cut27.py`'s shape:

```python
"""Cut 28 canonical declaration: W7, W8 and W8b over the slice 4 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W7", "W8", "W8b")
_A = "acceptance/test_world_selection_acceptance.py"
UNIT_CHECKS = {
    "W7": f"{_A}::test_w7_addresses_selects_the_other_corpus_record_and_contributes_its_corpus_durably",
    "W8": f"{_A}::test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably",
    "W8b": f"{_A}::test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-28 row")
    return unit
```

Then `CUT28_ARMS`, 23 `Arm(...)` entries, each with a `Sabotage(module=..., before=<the exact source as landed>, after=<the mutation>)` and `checks=(<the durable test that fails under it>,)`. The `before` text is copied verbatim from the landed code, which is why this module is written last. The mutations, by row:

- `W7-a` `world/selection.py`: `if view.damaged():` → `if False:` → `test_w7_a_damaged_view_refuses_durably`.
- `W7-b` `world/selection.py`: `if moved:` → `if False:` → `test_w7_a_drifted_view_refuses_and_the_earlier_capture_evaluates_durably`.
- `W7-c` `world/selection.py`: in `_require_located`, `if unknown:` → `if False:` (an unknown address no longer refuses) → `test_w7_an_unknown_address_refuses_naming_every_unknown_one_durably`.
- `W7-d` `world/selection.py`: `raise SelectionRefused("address-not-present", …)` → `raise SelectionRefused("address-unknown", refs=[address for address, _ in not_present])` (not-present collapsed into unknown) → `test_w7_the_absent_corpus_refuses_reports_or_names_itself_by_form_durably`.
- `W7-e` `world/selection.py`: `members = denoted if members is None else members & denoted` and `selected |= members or set()` → intersect across clauses (`selected = members if not selected else selected & members`) → `test_w7_two_clauses_select_and_contribute_both_durably`.
- `W7-f` `world/selection.py`: `return set(reach.reached)` → `return set(reach.reached) | {live}` → `test_w7_closure_out_selects_the_other_corpus_dataset_and_not_the_run_durably`.
- `W7-g` `world/selection.py`: `reach = closure(live, …)` → `reach = closure(predicate.anchor, …)` → `test_w7_a_retired_anchor_over_a_cycle_selects_what_the_live_anchor_selects_durably`.
- `W7-h` `world/selection.py`: the `_InboundAdjacency` `if edge.source_uid is None:` block → `continue` (drop it, as `RelationAdjacency._inbound` does) → `test_w7_dangling_and_absent_inbound_steps_are_reported_not_dropped_durably`.
- `W7-i` `world/selection.py`: `"unresolved": [step.projection() for step in self.unresolved],` → `"unresolved": [],` → `test_w7_projection_members_are_asserted_directly_durably` (the literal member; identity inequality alone survives this mutation because `selected` moves too).
- `W7-j` `world/selection.py`: `"absent": list(self.absent),` → `"absent": [],` → the same test (`clauses: []` isolates `absent`, and the member is asserted as a literal).
- `W7-k` `world/selection.py`: `for address in selected:\n        validated_node(held[address][1])` → `pass` → `test_w7_a_stale_selected_record_refuses_durably`.
- `W7-l` `world/selection.py`: in `_binds_term`, `validated_node(node)` → removed → `test_w7_a_stale_edit_that_removed_the_term_refuses_durably`.
- `W7-m` `world/selection.py`: `return term in args or term in restrictions` → `return term in args` → `test_w7_terms_in_arguments_and_restrictions_select_and_a_malformed_facet_refuses_durably`.
- `W7-n` `world/selection.py`: `raise SelectionRefused("record-malformed", refs=[node.id]) from None` → `return False` (a malformed facet reads as "does not reference") → `test_w7_terms_in_arguments_and_restrictions_select_and_a_malformed_facet_refuses_durably`'s malformed-facet assertion.
- `W7-p` `decode.py`: in `stored_claim_terms`, `return tuple(terms), tuple(body["restriction"] for body in qualifier_bodies.values())` → `return tuple(term.lower() for term in terms), tuple(body["restriction"] for body in qualifier_bodies.values())` (terms normalized before comparison) → the same test's `GENE.upper()` negative, written as a distinct assertion.
- `W7-o` `world/selection.py`: `if type(view) is not WorldReadView:` → `if False:` → `test_w7_empty_clauses_and_a_read_view_durably`.
- `W8-a` `world/derive.py`: `if len(locations) > 1:` (the `by_address` loop) → `if False:` → `test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably`.
- `W8-b` `relocation.py`: `if keep_map != other_map:` → `if False:` (a survivor's map wins) → `test_w8_address_conflict_refuses_the_build_and_consolidate_and_the_write_boundary_durably`.
- `W8-c` `relocation.py`: `move`'s occupied-destination check (`raise DuplicateLocation(`… find the exact line) → the check dropped → the duplicate-location durable test's `move` assertion.
- `W8b-a` `world/derive.py`: `if len({address for _, address in locations}) > 1:` → `if False:` → `test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably`.
- `W8b-b` `world/derive.py`: the `by_uid` loop moved below the `by_address` loop (addresses checked before uids, masking corruption as duplication) — one `before` block covering both loops → `test_w8b_corruption_outranks_duplication_and_a_corpus_alone_reports_neither_durably`.
- `W8b-c` `world/derive.py`: `by_address.setdefault(record.address, []).append((corpus_id, record.uid))` → keyed on `(record.address, record.uid)` so distinct uids at one address are not a duplicate → `test_w8b_duplicate_location_is_the_same_finding_with_shared_or_distinct_uids_durably`.
- `W8b-d` `relocation.py`: `if keep_node.id != other_node.id:` → `if False:` → `test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably`.

That is 23 arms: sixteen `W7`, three `W8`, four `W8b`. Every `before` must occur exactly once in its module — run `test_each_sabotage_names_one_real_source_site` (step 3) until it does. If a mutation cannot be made to fail exactly one durable test, add the durable test that isolates it rather than dropping the arm, and record the count in Task 9.

- [ ] **Step 3: The guard**

Create `python/tests/acceptance/test_n2_cut28.py` from `test_n2_cut27.py`: import `CUT28_ARMS, CO_CITED, DECLARATION_UNITS, UNIT_CHECKS, unit_of` from `n2_arms_cut28`; add `from n2_arms_cut27 import CUT27_ARMS` to the prior imports and `*CUT27_ARMS` to `PRIOR_ARMS`; `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-14-conformance-cut-28.md"`; `FROZEN_DECLARATION = "python/tests/acceptance/n2_arms_cut28.py"`; the session fixture's `mktemp("n2-cut28")`. Two commits are pinned: `CUT28_FREEZE_COMMIT` and `CUT28_FROZEN_SHA256` are Task 1's freeze commit and the cut document's digest there; `CUT28_DECLARATION_COMMIT` and `CUT28_DECLARATION_SHA256` are the commit step 4 makes and the declaration's digest there. `FROZEN_PRIOR_CUT_FILES` gains `"python/tests/acceptance/n2_arms_cut27.py": "<the short sha that added it — git log --follow>"`. The inventory test asserts `DECLARATION_UNITS == ("W7", "W8", "W8b")`, `len(CUT28_ARMS) == 23`, and `unit_of` over every row. The pinned-sections test greps `"**3 declaration units**"`, `"Three guarantee rows are read, **2 full/closed** (W7, W8b)"` and `'("cut27_acceptance.py",)'`. The row-parser test's rejects become `("", "D1", "W7-", "W7a", "W7-A", "W7-1", "W7-aa", "W7-a-b")` with `match="is not a cut-28 row"`. `test_the_freeze_commit_and_sections_two_through_seven_are_pinned`, `test_the_declaration_is_byte_exact_against_its_own_commit` and `test_prior_declarations_are_frozen_and_no_check_is_reclaimed` keep cut 27's bodies with the names swapped.

- [ ] **Step 4: Pin the declaration, run the guard, commit**

```bash
git add python/tests/acceptance/n2_arms_cut28.py python/tests/acceptance/test_world_selection_acceptance.py
git commit -m "test(cut28): durable arms and the N2 declaration"
git rev-parse HEAD                                    # → CUT28_DECLARATION_COMMIT
sha256sum python/tests/acceptance/n2_arms_cut28.py    # → CUT28_DECLARATION_SHA256
```

Fill both into `test_n2_cut28.py`, then:

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut28.py`
Expected: every guard test passes — including `test_every_arm_fails_under_its_own_sabotage` (23 sound findings) and the freeze pin.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note beliefs-10efda "23 durable arms on the certified volume; n2_arms_cut28 declared and pinned; guard green"
tasks done beliefs-10efda "cut 28 arms, declarations and guard"
git add python/tests tasks
git commit -m "test(cut28): the freeze guard and pins"
```

---

### Task 8: The runner, the status row and the dated notes

**Files:**
- Create: `python/tools/cut28_acceptance.py`
- Modify: `python/tools/roadmap_status.py:58` (add cut 28's row), `docs/designs/2026-08-02-world-addressing-design.md:1511` (W7's cell), `:1512` (W8's cell), `:1514` (W8b's cell), `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` (§13, appended item), `docs/guide/identity-world-and-change.md:171-180`, `docs/guide/contracts-and-adoption.md:229-231`, `docs/guide/foundations.md:126-128`

- [ ] **Step 1: `tasks start beliefs-0160ea`, then write the runner**

Copy `python/tools/cut27_acceptance.py` to `cut28_acceptance.py` and change: the docstring to `"""Run cut 28 after cut 27 on the certified durable tuple."""`; `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut28-acceptance"`; `PREFIX_RUNNERS = ("cut27_acceptance.py",)`; `PHASE_MODULES = ("test_world_selection_acceptance.py", "test_n2_cut28.py")`; the import to `from n2_arms_cut28 import CUT28_ARMS, DECLARATION_UNITS, unit_of` and the return to count `CUT28_ARMS`; `cut=28`.

- [ ] **Step 2: The status tool's row**

In `python/tools/roadmap_status.py` after line 58 (`27: (...)`) add:

```python
    28: ("conformance-cut-28-results §2", "W7, W8b", "W8"),
```

- [ ] **Step 3: The row notes, the 2b note and the guide**

Each a dated addition; no existing words are removed.

- `2026-08-02-world-addressing-design.md:1511`, at the end of W7's cell: ` **Read 2026-09-14 (cut 28, slice 4 design §3):** the evaluator is `world/selection.py`'s `evaluate_query` over the explicit-epoch `WorldReadView`; the topic in one corpus finds the entity in the other under every v1 predicate form, and a corpus-local evaluation is refused by type rather than fixed per consumer.`
- `2026-08-02-world-addressing-design.md:1512`, at the end of W8's cell: ` **Read 2026-09-14 (cut 28, slice 4 design §4.1):** duplicate location and address conflict are read over the build refusal, `consolidate` and `move` as landed at cuts 16 and 25 and `beliefs-fda0e5`; the ambiguous-search-term conflict is unrun — it needs the pinned authority snapshot (ledger artifact 11) — and is re-homed with W9 to `authority-labels`.`
- `2026-08-02-world-addressing-design.md:1514`, at the end of W8b's cell: ` **Read 2026-09-14 (cut 28, slice 4 design §4.2):** all four arms over `derive.address_map` and `consolidate` as landed; the world view's duplicate-uid refusal at open stays slice 1's invariant and is not this row's build half.`
- `2026-09-10-world-resolution-slice-2b-design.md`, appended to §13 as its last item: `N. **W14's home (2026-09-14).** §12 and this section assigned the label renderer and W14 to slice 4. Slice 4's design §8 item 1 records that the roadmap's boundary index homes W9 and W14 in `authority-labels`, tier 3, blocked on artifact 11, and that a renderer without a pinned snapshot could assert nothing; W14 stays there and slice 4 builds no renderer.` (use the next item number).
- `docs/guide/identity-world-and-change.md:171-180`: after the cut 27 sentence add "Cut 28 adds view-query evaluation over the world read view — a topic's query selects across corpora at an explicit epoch, refusing drift, damage and an address it cannot locate, and reporting absence rather than folding it in — and discharges W8b and W8's runnable conflicts over the existing build, `consolidate` and `move`." Replace "view evaluation remains open." with "W8's ambiguous-search-term conflict waits with W9 on the pinned authority snapshot." Add `- ../designs/2026-09-14-conformance-cut-28.md` to the page's `sources:` list.
- `docs/guide/contracts-and-adoption.md:229-231`: after the cut 27 sentence add "Cut 28 discharges world resolution slice 4 — W7's view evaluation and the W8/W8b conflicts over existing code (`../designs/2026-09-14-conformance-cut-28.md`; `../plans/<date>-conformance-cut-28-results.md`)." — the results path is filled in Task 9.
- `docs/guide/foundations.md:126-128`: after "deliberately not a query engine." add " The evaluator is `evaluate_query` over the world read view, delivered at cut 28."

- [ ] **Step 4: Run the guard sweeps and the whole runner**

Run: `cd python && uv run --frozen pytest tests/test_frozen_guards.py tests/test_arm_staleness.py tests/test_designs_corpus.py -p no:cacheprovider`
Expected: PASS.

Run: `cd python && uv run --frozen python tools/cut28_acceptance.py 2>&1 | tee ../.cut28-acceptance/run.log | tail -30`
Expected: exit 0; the prefix chain through cut 27 green; both phases green; the final line `declared arms: 23 (= 3 declaration units; 3 guarantee rows)`.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note beliefs-0160ea "runner cut28_acceptance.py green over the cut 27 prefix; roadmap_status row; W7/W8/W8b notes; 2b W14 note; guide"
tasks done beliefs-0160ea "the cut 28 runner and the dated notes"
git add python/tools docs tasks
git commit -m "test(cut28): the acceptance runner, and the dated notes on W7, W8, W8b and slice 2b"
```

---

### Task 9: Discharge

**Files:**
- Create: `docs/plans/<date>-conformance-cut-28-results.md` and `docs/plans/<date>-conformance-cut-28-run/{certified.log,check.log,test.log}` — the date is the day the gate runs; every `2026-09-XX` below is that date
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Updated`, the `Current state` heading date, the summary bullet after line 180: "W7 and W8b close at cut 28; W8's ambiguous-search-term conflict is re-homed to `authority-labels`", the `world-resolution` row at line 196 → "the two filed follow-ups: dataset addressing (`beliefs-48214e`) and divergent correction-history reconciliation (`beliefs-24b42b`); no guarantee row remains", the `authority-labels` row at line 204 → `W8's ambiguous-search-term conflict, W9, W14`), `docs/plans/2026-08-29-implementation-roadmap.md` (whole rewrite per its header rule: `**Ranked at:** cut 28`, the cut 27 paragraph replaced by a cut 28 paragraph, Appendix A regenerated by `python/tools/roadmap_status.py`, Appendix B: the `W7, W8` row becomes `W8 | the ambiguous-search-term conflict, W9's arm restated (cut 28 results §5) | authority-labels — tier 3`, the `W8b` row leaves, the `W9, W14` row gains W8; the boundary index and tier-1 row for `world-resolution` read "the two filed follow-ups" with no rows; the tier-3 `authority-labels` row gains W8), `docs/designs/2026-09-14-conformance-cut-28.md` (`Status:` and §1's first sentence only), `docs/superpowers/specs/2026-09-13-world-resolution-slice-4-design.md` (`Status:` → discharged at cut 28, dated), this plan (`Status:`), `README.md` (the "through cut 27" and "latest discharged boundary" sentences → cut 28), `docs/guide/contracts-and-adoption.md` (the results path)

- [ ] **Step 1: `tasks start beliefs-902cd5`, then run the repository gates and retain the transcripts**

From the repository root:

```bash
mkdir -p docs/plans/2026-09-XX-conformance-cut-28-run
(cd python && uv run --frozen python tools/cut28_acceptance.py) > docs/plans/2026-09-XX-conformance-cut-28-run/certified.log 2>&1; echo "exit $?"
just check > docs/plans/2026-09-XX-conformance-cut-28-run/check.log 2>&1; echo "exit $?"
just test  > docs/plans/2026-09-XX-conformance-cut-28-run/test.log  2>&1; echo "exit $?"
grep -E "^[0-9]+ passed" docs/plans/2026-09-XX-conformance-cut-28-run/test.log
```
Expected: three `exit 0`; the pytest summary line and the vitest summary line name their counts. Claim the counts only from those lines.

- [ ] **Step 2: Write the results record**

Sections as cut 27's: `## 1. What ran` (the exact commands, exit codes, the prefix chain, per-phase counts, the `declared arms:` line, the transcript links); `## 2. Accounting and disposition` (W7 and W8b close; W8 part on its ambiguous-search-term conflict, re-homed to `authority-labels`; the closed count moves from 151 to **153** of 196, leaving **43** open — confirm against `roadmap_status.py`'s output); `## 3. Corrections and deviations from the frozen cut` (dated bullets: any fixture measured against §4's claims, any arm count other than 23, any staleness re-target); `## 4. Reproduction measurement` (no new mm30 run; cite cut 22's); `## 5. Remaining boundary` (`world-resolution` retains no guarantee row and the filed follow-ups `beliefs-48214e` and `beliefs-24b42b`; `authority-labels` retains W8's ambiguous-search-term conflict, W9 and W14; `contract-cut` retains R23's rules-store clauses and W8a's `instrument-certification` arm; manifest safety unowned); `## 6. Main integration` after the merge.

- [ ] **Step 3: Regenerate the roadmap's Appendix A and rewrite the ledger's Current state**

Run: `cd python && uv run --frozen python tools/roadmap_status.py` and paste its table; rewrite the roadmap whole per its header rule; update the ledger's `world-resolution` and `authority-labels` rows and the summary; run `uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider` until green — `test_the_roadmap_and_ledger_name_the_same_boundaries` and `test_the_ledger_summary_names_the_newest_remaining_boundary` bind these documents to the record. The summary must name every row label the results record's `Remaining boundary` names (`W8`, `W9`, `W14`, `R23`, `W8a`).

- [ ] **Step 4: Close the tasks and commit**

```bash
tasks done beliefs-902cd5 "cut 28 discharged; results record docs/plans/2026-09-XX-conformance-cut-28-results.md"
tasks note beliefs-d248ba "slice 4 discharged at cut 28: W7 and W8b close, W8's search-term conflict re-homed to authority-labels; the two filed follow-ups remain"
tasks done beliefs-0e523a "slice 4 discharged at cut 28: view evaluation over the world read view; W7, W8b closed; W8 part, re-homed"
tasks check
git add -A docs python/tests python/tools tasks README.md
git commit -m "docs(cut28): discharge conformance cut 28 and re-rank the roadmap"
```

Then merge `design/world-resolution-slice-4` into `main` with `--no-ff`, run `just gate` on `main`, record §6 of the results record, and remove the worktree per the roadmap's lane rules. `beliefs-d248ba` stays open for `beliefs-48214e` and `beliefs-24b42b`; the estimand-typing lane's Task 0 (`beliefs-705507`) re-reads rule 6 next.

---

## Review log

**2026-09-14, first review, eight findings, all resolved.** (1) Every topic
world reports unmapped coordination uids under equal states, so the drift
check refused the W7 positives — the evaluator keys on the state pair, the
spec is amended (§2.1, §3.2, §5), and a unit arm pins the equal-state case
(Task 3). (2) The hand-written claim-shape check admitted a qualifier without
`quantifier` — `decode.stored_claim_terms` factors `_wire_parts`' check out
of `claim_from_stored` and the evaluator translates its refusal (Task 4).
(3) The absent-inbound fixture carried the edge on the absent run, which the
inbound index never files — the relation lives on `d_a` with `r_b` as its
declared source (Task 3). (4) A third same-uid record inside BETA is a
corpus-local `CollisionError` before the world check — it lives in a third
corpus (Task 6). (5) `alpha_extra`/`beta_extra` went through the validating
durable writer — the topic fixture builds its own world with raw staging for
both corpora and keeps `without` (Task 7). (6) Dropping `absent` or
`unresolved` from the projection survived identity inequality — the members
are asserted as literals and `clauses: []` isolates `absent` (Tasks 3, 5, 7).
(7) The registration-order test compared different duplicates — one set of
roots under two worlds admitted in opposite order, the whole finding
compared (Task 6). (8) `contributing` is sorted over minted ids — every
durable expectation is `tuple(sorted((a, b)))` (Task 7).

**2026-09-14, second review, one finding, resolved.** The drift arm still
expected BETA's report first, but ALPHA's equal-state coordination report
precedes it. The assertion now filters reports by changed corpus states and
expects only BETA; the durable counterpart explicitly uses the same filter
(Tasks 3 and 7).
