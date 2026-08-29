# Implementation roadmap — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the dated, living roadmap at `docs/plans/2026-08-29-implementation-roadmap.md`, the ledger table it is joined to by stable ids, the script that recomputes the open-row inventory, and the guard that holds the two documents to the same boundary set.

**Architecture:** Documentation plus one small tool and one test. `python/tools/roadmap_status.py` pins each cut's live accounting as sourced data and prints every guarantee row's live status (§3.1's rule, G4's override included). The ledger's `Current state` table gains an `id` column and twenty promoted rows. The roadmap carries a `## Boundary index` (the id set), the three tier tables and ride-along table by id, and an appendix holding the script's output and the spec's per-row classification. `test_the_roadmap_and_ledger_name_the_same_boundaries` asserts id uniqueness in each document, set equality between them, and that `Ranked at` names the newest results record's cut.

**Tech Stack:** Markdown; Python 3 (`uv run` from `python/`); pytest; `python/tools/check_guide.py`.

**Spec:** `docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md` — read it first; §3.3 and §4 are copied into the roadmap verbatim, and §6 defines the guard.

## Global Constraints

- Work in this worktree on branch `docs/roadmap`; paths are relative to the worktree root.
- Curation rules 1–5 still bind (`2026-08-28-current-state-documentation-curation-design.md` §3): evidence-backed claims; frozen cut bodies, plans, execution ledgers and results records untouched; no implementation status in design headers; fail closed; no ordering in the ledger.
- Cut 3 has **two** accounting tables. The live one is §4 (lines 218–219: 15 full, 19 part). The one under `## Appendix A — the frozen text, preserved verbatim` (17 full) is superseded and must not be read.
- Boundary ids are kebab-case, backticked, in the first column of the ledger table and of the roadmap's `Boundary index`; the 24 ids are exactly those in spec §3.4. Every reference to a boundary in the roadmap uses its id.
- The roadmap header line is exactly `**Ranked at:** cut 11, against the ledger's Current state (2026-08-28)`.
- The only edits to the ledger's guarded section: the `id` column, the promoted rows, the restated entry-rule sentence, and the one link sentence. Nothing else in the ledger changes.
- Pytest: `addopts` sets `-q`; run `cd python && set -o pipefail && uv run pytest tests/<file> | tail -3`.
- Conventional commits, no AI-attribution trailer.

---

### Task 1: The accounting script

**Files:**
- Create: `python/tools/roadmap_status.py`

**Interfaces:**
- Produces: `uv run python tools/roadmap_status.py` prints the per-table live-status table and the closed/open counts; Task 4 pins its output in the roadmap's Appendix A. Exposes `live_status() -> dict[str, tuple[str, int]]` mapping every row to `("full"|"part"|"never"|"reopened", cut)`.

- [ ] **Step 1: Write the script**

```python
"""Live status of every guarantee row, from the cuts' own accounting.

Spec: docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md §3.1.
A row's historical status is the highest it reached across the cuts' full/part
accounting; its live status overrides that to open where a later source names
the row open at a widened obligation. Run from `python/`:

    uv run python tools/roadmap_status.py
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location(
    "test_designs_corpus", ROOT / "python" / "tests" / "test_designs_corpus.py"
)
assert _spec is not None and _spec.loader is not None
_corpus = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_corpus)
GUARANTEE_TABLES: dict[str, list[str]] = _corpus.GUARANTEE_TABLES

#: Each cut's rows read in full and in part, with the section that states them.
#: Cut 3's live table is §4 (15 full, 19 part); its Appendix A preserves the
#: pre-amendment 17/17 table and is not a source.
ACCOUNTING: dict[int, tuple[str, str, str]] = {
    1: ("review-disposition-and-conformance-cut-1 §5", "M4, M7, M9, M10, M11, M13", "M5"),
    2: ("conformance-cut-2 §4", "G1, G2b, G6, P2–P9, M6, M8", "G2c, G3, G8, G9, S5, S6, P1, D3, D6, D7, N2"),
    3: ("conformance-cut-3 §4 (not Appendix A)",
        "G2a, G4, M2, R1, R3, R6, R7, R8, R11, R14, R17, R18, T3, T6, T8",
        "G9, N2, R2, R4, R5, R9, R10, R12, R13, R16, R19, R20, R21, R22, R23, T1, T2, T4, T5"),
    4: ("conformance-cut-4 §4.1 and §4.2", "S7, S8, W3", "G9, N2, R19, R22, R23, S1, S1a, S5"),
    5: ("conformance-cut-5 accounting", "S2, S3, S4, G7, C1, C2, C4, C5", "M5, T1, T2, M3, R20, C3, C6, C10, G2c, G8"),
    6: ("conformance-cut-6 accounting", "X4, X6", "X5, W13"),
    7: ("conformance-cut-7 accounting", "X1, X3, X7, X8, X9, X10, X11", "X2, X5, X12, W8a"),
    8: ("conformance-cut-8-results §1", "L3, L5, L9, L11, L12", "L1, L2, L4, L7, L8, L10, L13"),
    9: ("conformance-cut-9-results §1", "L6", "L2, L4, L10, W13"),
    10: ("conformance-cut-10-results §1", "H1, H2, H3", "H4, G9, L7, L10"),
    11: ("conformance-cut-11-results §1", "", "L7"),
}

#: Rows a later source names open at a widened obligation, overriding a full read.
REOPENED: dict[str, tuple[str, int]] = {
    "G4": ("conformance-cut-11 §3.2; ledger row 5's note of 2026-08-28", 11),
}

_RANGE = re.compile(r"([GSWRCXNLDMPHT])([0-9]+[a-z]?)–\1?([0-9]+[a-z]?)")


def _expand(cell: str) -> set[str]:
    rows: set[str] = set()
    for token in (t.strip() for t in cell.split(",") if t.strip()):
        span = _RANGE.fullmatch(token)
        if span:
            table = GUARANTEE_TABLES[span.group(1)]
            start = table.index(span.group(1) + span.group(2))
            end = table.index(span.group(1) + span.group(3))
            rows.update(table[start : end + 1])
        else:
            rows.add(token)
    return rows


KNOWN_ROWS: frozenset[str] = frozenset(r for t in GUARANTEE_TABLES.values() for r in t)


def _check_known(rows: set[str], where: str) -> None:
    unknown = sorted(rows - KNOWN_ROWS)
    if unknown:
        raise SystemExit(f"{where} names rows that are not guarantee rows: {unknown}")


def live_status() -> dict[str, tuple[str, int]]:
    status: dict[str, tuple[str, int]] = {}
    for source, full, part in ACCOUNTING.values():
        _check_known(_expand(full) | _expand(part), source)
    _check_known(set(REOPENED), "REOPENED")
    for cut, (_, full, part) in ACCOUNTING.items():
        for row in _expand(full):
            status[row] = ("full", cut)
        for row in _expand(part):
            if status.get(row, ("", 0))[0] != "full":
                status[row] = ("part", cut)
    for row, (_, cut) in REOPENED.items():
        status[row] = ("reopened", cut)
    for table in GUARANTEE_TABLES.values():
        for row in table:
            status.setdefault(row, ("never", 0))
    return status


def main() -> None:
    status = live_status()
    total = sum(len(t) for t in GUARANTEE_TABLES.values())
    closed = sum(1 for s, _ in status.values() if s == "full")
    print("| table | never selected | part — last cut that read it | reopened |")
    print("|---|---|---|---|")
    for prefix, table in GUARANTEE_TABLES.items():
        never = ", ".join(r for r in table if status[r][0] == "never") or "—"
        part = ", ".join(f"{r} (cut {status[r][1]})" for r in table if status[r][0] == "part") or "—"
        reopened = ", ".join(f"{r} (cut {status[r][1]})" for r in table if status[r][0] == "reopened") or "—"
        print(f"| {prefix} | {never} | {part} | {reopened} |")
    print()
    print(f"Closed {closed} of {total}; open {total - closed}.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and check the counts against the spec**

```bash
cd python && set -o pipefail && uv run python tools/roadmap_status.py | tail -1
```

Expected: `Closed 62 of 151; open 89.` Then prove the check fails closed: change `M4` to `BAD` in cut 1's entry, rerun, and expect a non-zero exit with `review-disposition-and-conformance-cut-1 §5 names rows that are not guarantee rows: ['BAD']`; revert the change. If the count differs, the accounting data disagrees with spec §3.1 — compare table by table against the spec's §3.1 table and fix whichever is wrong against the cut document it cites; record any spec correction in the commit message.

- [ ] **Step 3: Lint and commit**

```bash
cd python && set -o pipefail && uv run ruff check tools/roadmap_status.py && uv run pyright tools/roadmap_status.py | tail -1
cd .. && git add python/tools/roadmap_status.py && git commit -m "tools: compute every guarantee row's live status from the cuts' accounting"
```

---

### Task 2: Promote the boundaries into the ledger table

**Files:**
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md:74-90` (the `Remaining implementation boundaries` paragraph, table, and closing paragraph inside `## Current state (2026-08-28)`)

**Interfaces:**
- Produces: the 24 backticked ids in the table's first column that Task 3's guard collects and Task 4's roadmap must match.

- [ ] **Step 1: Replace the paragraph, table, and closing paragraph**

Replace from `**Remaining implementation boundaries with named owners.**` through the paragraph ending `holds this section to whichever record is newest.` with:

```markdown
**Remaining implementation boundaries with named owners.** One row per
boundary: a stable id, what it is, who owns it, and what it blocks. Row order
carries no priority; ordering over these rows lives in
`../plans/2026-08-29-implementation-roadmap.md`. A boundary enters this
table only when a cut's accounting, a results record, or §1's rows prove it
still open; unresolved design areas are not boundaries and are not listed.

| id | boundary | owner | what it blocks |
|---|---|---|---|
| `successor-admission` | **G4** — successor admission; with it R12's boundary-mediated strengthening arm and L7's relabel | the successor-admission slice; `2026-08-26-world-index-intent-boundary-design.md` §5 carries the transferred design and its opening obligations | the fourth of kernel §8.7's recorded-mutation consequences; rows 5 and 7 reading G4 in full |
| `run-confinement` | **R15** and the `clean-environment` arms of R4, R9, R13, R16, R21 | the confinement-capable boundary policy, `2026-08-02-computation-reproducibility-design.md` §4.4b | a real verification reaching `clean-environment`, so admission to belief runs end to end rather than over supplied values |
| `workflow-surface` | the full workflow surface: R2, R16, R20, R21's workflow arms; R23's second-production arm | `2026-08-02-computation-reproducibility-design.md` §6.4 | multi-rule, family, wildcard and definition-equality workflows |
| `consolidate-family` | consolidate, move/rename and deletion: W5, W16; G3, D7; the deletion negatives of G2c, G8, C6, R5; S5's deletion half; R23 and C3's move clauses; M3's replica arm | `2026-08-19-family-adapters-design.md`, which deferred them to their own cut | C7's consolidate surface; the last mutation family |
| `url-retrieval` | the URL retrieval boundary, acquisition orchestration and typed retrieval grants: H4, G9, R10, T5, T7's same-root case | `2026-08-24-world-index-holdings-design.md` §1–§3 | the first acquisition of a dataset from outside the system |
| `world-resolution` | the read side of the world: W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 less its two-projects negative; W8a's coreference arms; S1, S1a and S5's cross-corpus reach; D3; X12 and M3's coreference arms; R23's snapshot clauses | `2026-08-02-world-addressing-design.md` and `2026-08-08-world-address-ruling.md` | resolution states, cross-corpus edges, views, the coreference balance |
| `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | `2026-08-04-domain-extension-boundary-design.md` | the first domain pack |
| `event-level-l8` | **Event-level L8** — the presence/exclusion relation across captured corpus heads | the tamper-evident-log design's own successor work (row 5) | row 5 reading L8 in full |
| `contract-cut` | **The first full contract cut, its executable suite, and N1–N10**; N2's closing doctrine; P1's resolver-negative arm; R22's resolver arm; the `instrument-certification` arms of W8a, X12 and C10; R23's rules-store clauses | sub-problem 5b (row 7) | the normative contract's own guarantees; disposition of the legacy check modules; the conformance-package split (§5) |
| `run-boundary-remainder` | R19; R22's explicit-import and audit arms | `2026-08-02-computation-reproducibility-design.md` | explicit-import derivation validation |
| `formal-model-remainder` | M1; M3's audit and admission-order arms; M5 | `2026-08-04-formal-model-and-claim-calculus-design.md` | refinement evidence for M\* |
| `log-remainder` | L1, L4; L10's relabel | `2026-08-22-log-verification-design.md` | row 5's L rows read in full |
| `act-report-remainder` | T1, T2, T4 | `2026-08-11-act-report-design.md` | the T table in full |
| `packaging-remainder` | X5's relabel; W8a's import-boundary and audit arms | `2026-08-03-world-index-packaging-design.md`; `2026-08-20-world-index-slice-2-design.md` | X5 and W8a read in full |
| `parity-fixture-2` | the second `science.identity.v1` parity fixture, numeric and escape arms | `2026-08-04-formal-model-and-claim-calculus-design.md` §8 (§3 item 8) | cross-language parity of the identity arms tested twice and compared never |
| `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | sub-problem 5a, `2026-08-03-correction-lifecycle-design.md` | the correction lifecycle in full |
| `l13-preimage` | **L13 preimage resolver** — preimage-backed classification of a removed verification | the named `atoms` blob-read seam (`2026-08-03-tamper-evident-log-design.md` §5.3) | row 5 reading L13 in full; until then the held-copy match is a path match |
| `persistence-cut` | X2's persistence-cut arm | the `atoms` A8 certification extended to the publication path, behind `atoms`' own design gate | X2 in full |
| `nodes-remainder` | the reserved-path contract, recoverable construction, digest-id hazards | `nodes` `2026-08-03-nodes-under-the-system-redesign-design.md` (row 3) | audits over damaged corpora; manifest safety |
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot — owed, undesigned | every rendered label; the ambiguous-search refusal |
| `coordination-addressing` | W11, W12; W13's two-projects negative | the project/coordination surface, which no slice has built and whose minting path is undetermined (cut 4 §5) | coordination references |
| `weighted-belief` | S6 arm (h) | the first successor belief policy admitting unequal weights, blocked on ρO3 | weighted belief |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 | an untypeable span minting nothing, end to end |
| `cross-root-publication` | T7's cross-root case | the act-report design's cross-root publication residue | cross-root publication of a provenance reference and its report |

Detailed state, with every dated correction, stays in §1's rows and §3's order
of work. The newest results record
(`../plans/2026-08-27-conformance-cut-11-results.md` §5) names G4, L8 and
L13, and `test_the_ledger_summary_names_the_newest_remaining_boundary` holds
this section to whichever record is newest;
`test_the_roadmap_and_ledger_name_the_same_boundaries` holds this table and
the roadmap to one set of ids.
```

- [ ] **Step 2: Confirm the existing guard still passes and the id count is 24**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -2
cd .. && grep -c -E '^\| `[a-z0-9-]+` \|' docs/designs/2026-08-03-redesign-adoption-ledger.md
```

Expected: all pass (the prose-label guard still finds `G4`, `L8`, `L13` and `cut 11`); count `24`.

- [ ] **Step 3: Commit**

```bash
git add docs/designs/2026-08-03-redesign-adoption-ledger.md
git commit -m "docs(ledger): key the remaining boundaries by stable id and promote every proven-open one"
```

---

### Task 3: The guard, failing on the missing roadmap

**Files:**
- Modify: `python/tests/test_designs_corpus.py` (constants after `_H2`; a helper factored out of `test_the_ledger_summary_names_the_newest_remaining_boundary`; the new test after it)

**Interfaces:**
- Produces: `ROADMAP`, `_BOUNDARY_ID`, `_newest_results_record() -> tuple[int, Path]`, `test_the_roadmap_and_ledger_name_the_same_boundaries`.

- [ ] **Step 1: Add the constants after `_H2`**

```python
ROADMAP = PLANS / "2026-08-29-implementation-roadmap.md"

#: A boundary id in the first column of a table row — the join key between the
#: ledger's Current state table and the roadmap's Boundary index.
_BOUNDARY_ID = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|", re.M)
```

- [ ] **Step 2: Factor the newest-record selection into a helper**

Add before `test_the_ledger_summary_names_the_newest_remaining_boundary`:

```python
def _newest_results_record() -> tuple[int, Path]:
    records = {
        int(m.group(1)): path
        for path in PLANS.glob("*.md")
        if (m := _RESULTS_RECORD.match(path.name))
    }
    assert records, f"no conformance-cut results record under {PLANS}"
    return max(records.items())
```

and inside that existing test replace the `records = {...}` / `assert records` / `cut, newest = max(records.items())` lines with `cut, newest = _newest_results_record()`.

- [ ] **Step 3: Add the failing test**

```python
def test_the_roadmap_and_ledger_name_the_same_boundaries() -> None:
    """The ledger's table says what is open; the roadmap says in what order.

    They are joined on backticked ids, never on prose, so rewording a boundary
    breaks nothing. Uniqueness is checked before equality so a duplicated id
    cannot collapse into a passing set, and both differences are reported so
    a boundary that leaves one document cannot linger in the other. Fails
    closed on a missing file, a missing section, or an empty collection.
    """
    ledger = _h2_section(_text(DESIGNS / "2026-08-03-redesign-adoption-ledger.md"), "Current state")
    assert ledger is not None, "the ledger has no `Current state` section"
    ledger_ids = _BOUNDARY_ID.findall(ledger)
    assert ledger_ids, "the ledger's Current state table carries no boundary ids"
    assert len(ledger_ids) == len(set(ledger_ids)), (
        "duplicate ids in the ledger: " + ", ".join(sorted({i for i in ledger_ids if ledger_ids.count(i) > 1}))
    )

    assert ROADMAP.exists(), f"{ROADMAP.name} is absent"
    index = _h2_section(_text(ROADMAP), "Boundary index")
    assert index is not None, f"{ROADMAP.name} has no `Boundary index` section"
    roadmap_ids = _BOUNDARY_ID.findall(index)
    assert roadmap_ids, f"{ROADMAP.name}'s Boundary index carries no ids"
    assert len(roadmap_ids) == len(set(roadmap_ids)), (
        "duplicate ids in the roadmap: " + ", ".join(sorted({i for i in roadmap_ids if roadmap_ids.count(i) > 1}))
    )

    only_ledger = sorted(set(ledger_ids) - set(roadmap_ids))
    only_roadmap = sorted(set(roadmap_ids) - set(ledger_ids))
    assert not only_ledger and not only_roadmap, (
        f"in the ledger but not the roadmap: {only_ledger}; "
        f"in the roadmap but not the ledger: {only_roadmap}"
    )

    cut, newest = _newest_results_record()
    assert f"**Ranked at:** cut {cut}" in _text(ROADMAP), (
        f"the roadmap is not ranked at cut {cut}, the newest results record ({newest.name})"
    )
```

- [ ] **Step 4: Run and watch it fail on the absent roadmap**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py -k same_boundaries 2>&1 | grep -E 'AssertionError: |passed|failed' | head -3
```

Expected: `AssertionError: 2026-08-29-implementation-roadmap.md is absent` and `1 failed`. Any earlier assertion firing means Task 2's table is wrong.

- [ ] **Step 5: Confirm the refactored existing guard still passes**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py -k newest_remaining_boundary | tail -1
```

Expected: `1 passed`. Do **not** commit yet: a commit whose suite is red is not a checkpoint. Task 4 commits this test together with the roadmap that turns it green.

---

### Task 4: The roadmap

**Files:**
- Create: `docs/plans/2026-08-29-implementation-roadmap.md`

**Interfaces:**
- Consumes: Task 1's script output; the 24 ids of Task 2; spec §3.3, §4.1–§4.3.
- Produces: the file Task 3's guard reads; the `## Boundary index` section; the `**Ranked at:**` line.

- [ ] **Step 1: Capture the script output**

```bash
cd python && uv run python tools/roadmap_status.py
```

Keep the printed table; it is pasted into Appendix A in step 2.

- [ ] **Step 2: Write the document**

The header, the index, and the three tier sections are given in full below. Where a step says *copy from the spec*, copy the named table verbatim from `docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md` — the spec's tables already use ids and cite sources, and the roadmap must not paraphrase them.

```markdown
# Implementation roadmap

**Ranked at:** cut 11, against the ledger's Current state (2026-08-28)
**Method:** `../superpowers/specs/2026-08-29-implementation-roadmap-design.md`
**Recomputed by:** the commit that adds each conformance-cut results record.
This document is a current claim: it is rewritten whole at every re-ranking,
carries no dated corrections, and the previous ranking survives only in git
history.

The adoption ledger's `Current state` table
(`../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-28`)
is the authority for *what* is open; this document is the authority for *in
what order*. The two name the same boundaries by id, and
`test_the_roadmap_and_ledger_name_the_same_boundaries` holds them to it.
Design questions are never rows here; they appear only as a boundary's
*blocked on*, linking `../guide/open-questions.md`.

Ranking is dependency first, then breadth of what a boundary unblocks. A
boundary is **tier 1** when its entry point is designed and nothing outside
its own work must land first; **tier 2** when another boundary here or a
cross-repo seam must land first; **tier 3** when a design question must be
answered first. A prerequisite that is the boundary's own work is not a
prerequisite.

## Boundary index

Every boundary the ledger table lists, by id. This section is the guard's
join key and nothing else; the tiers below carry the ranking.

| id | rows it closes | tier |
|---|---|---|
| `successor-admission` | G4; R12's strengthening arm; L7's relabel | 1 |
| `run-confinement` | R15; R4, R9, R13, R16, R21's confinement arms | 1 |
| `workflow-surface` | R2, R16, R20, R21's workflow arms; R23's second-production arm | 1 |
| `consolidate-family` | W5, W16; G3, D7; G2c, G8, C6, R5's deletion negatives; S5's deletion half; R23 and C3's move clauses; M3's replica arm | 1 |
| `url-retrieval` | H4, G9, R10, T5; T7's same-root case | 1 |
| `world-resolution` | W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 (less one arm); W8a's coreference arms; S1, S1a, S5's cross-corpus reach; D3; X12 and M3's coreference arms; R23's snapshot clauses | 1 |
| `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | 1 |
| `event-level-l8` | L8 | 1 |
| `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12, C10's certification arms; R23's rules-store clauses | 1 |
| `run-boundary-remainder` | R19; R22's import and audit arms | 1, rides with `consolidate-family` |
| `formal-model-remainder` | M1; M3's audit and admission-order arms; M5 | 1, rides with `consolidate-family` |
| `log-remainder` | L1, L4; L10 (relabel) | 1, rides with `event-level-l8` |
| `act-report-remainder` | T1, T2, T4 | 1, rides with `url-retrieval` |
| `packaging-remainder` | X5 (relabel); W8a's import and audit arms | 1, rides with `world-resolution` |
| `parity-fixture-2` | the second `science.identity.v1` fixture | 1, rides with `domain-boundary` |
| `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | 2 |
| `l13-preimage` | L13 | 2 |
| `persistence-cut` | X2 | 2 |
| `nodes-remainder` | `nodes` row 3's three items | 2 |
| `authority-labels` | W9, W14 | 3 |
| `coordination-addressing` | W11, W12; W13's two-projects negative | 3 |
| `weighted-belief` | S6 (h) | 3 |
| `extraction-path` | M12 | 3 |
| `cross-root-publication` | T7's cross-root case | 3 |

## Tier 1 — buildable now

Strict order. Row 1 is the next cut.
```

Then *copy from the spec* §4.1's nine-row tier table and its ride-along table (with the sentence "A ride-along is named in the cut that takes it and never stands alone."), then:

```markdown
## Tier 2 — after a named prerequisite lands
```

*copy from the spec* §4.2's table, then:

```markdown
## Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| id | rows | blocked on |
|---|---|---|
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot — [which external authorities are accepted](../guide/open-questions.md#identity-world-and-change) |
| `coordination-addressing` | W11, W12; W13's two-projects negative | whether coordination records are minted through the corpus-write adapter (cut 4 §5; cut 6 §3.2) — [coordination records](../guide/open-questions.md#identity-world-and-change) |
| `weighted-belief` | S6 (h) | ρO3, estimand typing — [weighted belief](../guide/open-questions.md#claims-and-belief) |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 — [higher-order records and extraction](../guide/open-questions.md#claims-and-belief) |
| `cross-root-publication` | T7's cross-root case | [the act-report's residue](../guide/open-questions.md#contracts-and-adoption) |

## Appendix A — live status of every guarantee row at cut 11

Produced by `python/tools/roadmap_status.py` from the cuts' own accounting
(spec §3.1); a row is closed only when no later source reopens it.
```

Paste the script output from step 1 here, then:

```markdown
## Appendix B — classification of every open row

Each open row, its remainder as the last cut states it, and where it goes
(spec §3.2's three classes: schedulable, relabel, limitation).
```

*copy from the spec* §3.3's table and its closing paragraph about `nodes-remainder` and `parity-fixture-2`, then:

```markdown
## Appendix C — limitations, ranked nowhere

Arms banked as unrun by design. The any-unrun-arm rule keeps their rows
`part`; nothing here is work.

| row | arm | banked by |
|---|---|---|
| L7 | u1's non-ancestor spelling — directory-unconstructible on a linear content-addressed chain | cut 8 results §1.1 |
| L2 | u5's `register_root` existing-chain arm — no Science mapping | cut 8 results §1.1 |
| X2 | the interim best-effort-writer negative — the writer was never built | cut 7, X2's entry (lapsed) |
| M3 | the concrete-cycle arms needing a circular fixed point in a controlled identity | cut 5, M3's entry — a limitation unless a construction is found |
```

- [ ] **Step 3: Run the guard and watch it pass**

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -2
```

Expected: all pass, the new guard included. If it reports ids on one side only, the roadmap's index and the ledger table disagree — the ledger (Task 2) is authoritative; fix the index.

- [ ] **Step 4: Verify every link target and anchor in the roadmap resolves**

```bash
cd python && uv run python - <<'EOF'
import re, importlib.util
from pathlib import Path
s = importlib.util.spec_from_file_location("cg", "tools/check_guide.py"); cg = importlib.util.module_from_spec(s); s.loader.exec_module(cg)
p = Path("../docs/plans/2026-08-29-implementation-roadmap.md"); text = p.read_text()
bad = []
for target in re.findall(r"\]\(([^)]+)\)", text):
    path, _, frag = target.partition("#")
    f = (p.parent / path) if path else p
    if not f.exists(): bad.append(target); continue
    if frag and frag not in cg.heading_slugs(f.read_text()): bad.append(target)
assert not bad, f"unresolved: {bad}"
print("every roadmap link resolves")
EOF
```

Expected: `every roadmap link resolves` and exit 0; a broken link or anchor raises `AssertionError: unresolved: [...]` with a non-zero exit. (The roadmap lives under `docs/plans/`, which `check_guide.py` does not sweep, so this is the one place its links are checked.)

- [ ] **Step 5: Commit the roadmap with the guard that reads it**

```bash
git add python/tests/test_designs_corpus.py docs/plans/2026-08-29-implementation-roadmap.md
git commit -m "docs(plans): rank the remaining implementation boundaries at cut 11 and guard the join"
```

---

### Task 5: The guide's maintenance clause and the coordination-record question

**Files:**
- Modify: `docs/guide/README.md` (front matter `updated`; `## Maintaining the guide`)
- Modify: `docs/guide/open-questions.md` (front matter `updated`; the end of `## Identity, world, and change`, after the `Chain verification cost` bullet)

- [ ] **Step 1: `docs/guide/README.md`**

Set `updated: 2026-08-29`. Append to `## Maintaining the guide`, after "…can inspect every local target.":

```markdown

A commit that adds a conformance-cut results record also re-ranks the
[implementation roadmap](../plans/2026-08-29-implementation-roadmap.md) in
the same change: the discharged boundary leaves both the ledger's `Current
state` table and the roadmap, any newly named remainder enters both, and the
roadmap's `Ranked at` line advances to the new cut.
`test_the_roadmap_and_ledger_name_the_same_boundaries` fails until both are
done.
```

- [ ] **Step 2: `docs/guide/open-questions.md`**

Set `updated: 2026-08-29`. After the `Chain verification cost` bullet (the last one under `## Identity, world, and change`), add (the two anchors were computed with `check_guide.heading_slugs` against `## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem` and `### 3.2 W13 — the identity row`):

```markdown
- **Coordination records.** W11 and W12 assert that a world entity is never
  addressed by a `(project identity, local id)` coordination address, and
  that renaming a project breaks no coordination reference. No slice has
  built the project/coordination surface, and whether coordination records
  are minted through the corpus-write adapter at all is undetermined, which
  is why both rows defer rather than gaining a vacuous arm.
  ([cut 4 §5](../designs/2026-08-17-conformance-cut-4.md#5-step-3--fully-deferred-rows-grouped-by-unblocking-subsystem),
  [cut 6 §3.2](../designs/2026-08-20-conformance-cut-6.md#32-w13--the-identity-row))
```

Add both cut documents to the page's `sources:` list, in date order among the existing entries — neither is there today:

```yaml
  - ../designs/2026-08-17-conformance-cut-4.md
  - ../designs/2026-08-20-conformance-cut-6.md
```

- [ ] **Step 3: Run the guide gates**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1
```

Expected: `CHECK_GUIDE_OK` (a wrong slug fails here as "link resolves but its anchor does not"); all tests pass.

- [ ] **Step 4: Commit**

```bash
git add docs/guide/README.md docs/guide/open-questions.md
git commit -m "docs(guide): name the roadmap re-ranking obligation and the coordination-record question"
```

---

### Task 6: Gates, diff review, and closing the design's status

**Files:**
- Modify: `docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md:4` (the `**Status:**` line)

- [ ] **Step 1: Close the design's status**

Replace line 4 of the spec with:

```markdown
**Status:** approved in session; revised 2026-08-29 across four written-spec review rounds; delivered 2026-08-29 on `docs/roadmap` (roadmap at `docs/plans/2026-08-29-implementation-roadmap.md`, ranked at cut 11)
```

- [ ] **Step 2: Full documentation gates, on the tree that will be committed**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1
cd .. && git diff --check main && echo DIFF_CHECK_CLEAN
```

Expected: `CHECK_GUIDE_OK`; every test passed; `DIFF_CHECK_CLEAN`.

- [ ] **Step 3: Diff review against the allowlist**

```bash
git diff main --name-only
```

Expected exactly: `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/guide/README.md`, `docs/guide/open-questions.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/superpowers/plans/2026-08-29-implementation-roadmap.md`, `docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md`, `python/tests/test_designs_corpus.py`, `python/tools/roadmap_status.py`. Anything else is out of scope — revert it. Then confirm the ledger changed only inside its `Current state` section:

```bash
git diff main -- docs/designs/2026-08-03-redesign-adoption-ledger.md | grep -E '^@@'
```

Expected: one hunk, inside lines 41–90.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md
git commit -m "docs(specs): mark the implementation roadmap design delivered"
git log --oneline main..HEAD
```

The branch is then ready for the human-owned `--no-ff` merge into `main`. The next cut — `successor-admission` — is its own brainstorming session against intent-boundary design §5.
