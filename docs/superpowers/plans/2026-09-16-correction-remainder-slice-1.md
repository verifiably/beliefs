# Correction Remainder Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make retraction standing a property of the read — the enumeration derived from the view, node-arm targets subtracted before decoding, route-arm targets retired in the lineage walk — and discharge C7, C3's coverage clauses and C10's audit arm at conformance cut 33.

**Architecture:** `corpus.py` names the one standing fold (`retraction_standing`) and a corpus-local enumeration; `world/view.py` carries the bound epoch's enumeration and producer-snapshot identity, checked against the receipt at open; `lineage.py` gains route identities, a `retired` map, effective routes and walk-scoped absences; `evaluation.gather` dereferences every found retraction, refolds standing, refuses disagreement and unreadability, skips subtracted records before decoding, scopes the closure's enumeration to its own inputs, and hands the derived snapshot and enumeration to `belief.evaluate_traced`, which takes `retractions=` as an argument. Four src-touching follow-ups ride; the reproduction re-derives in a fresh process; cut 33 freezes before any code and discharges on the certified volume.

**Tech Stack:** Python 3.11+ (`uv run --frozen` from `python/`), pytest, `nodes.core`, the N2 harness (`python/tests/test_n2.py`, `n2_arms.py`, `arm_staleness.py`), `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md` (cleared for planning 2026-09-16 after four reviews, review log §14).

## Global Constraints

- **Baseline is `main` at `25ab84c`** (spec header). Work in the worktree `.worktrees/correction-remainder` (branch `design/correction-remainder`); every path below is relative to the repository root, and paths shown to the user carry the worktree prefix.
- Frozen declarations (`n2_arms_cut*.py`) and frozen cut bodies (§§2–7 of every cut document) stay byte-exact; a pinned line the refactor moves is re-targeted in the live guard, never in the frozen file (spec §8.5).
- `SuppliedContext` has no `retractions` member; `evaluate` and `evaluate_traced` take `retractions=` and refuse without it (spec decision 1, §4 "the handoff"). Nothing coerces or repairs a stored record; every refusal names a stable code.
- The closure's enumeration is input-scoped (spec decision 10); the standing fold runs over every found retraction (decision 3); a found retraction the evaluator cannot read refuses (`RetractionUnreadable`), a disagreement refuses (`RetractionResolutionDisagreement`), an absent one answers `unavailable-corpus-absent` (decision 4).
- `science.belief.v1`'s answers over every existing fixture are unchanged except where a retraction stands; P1–P9 green at every commit.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (ruff, pyright, biome, tsc, `tasks check`; ~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row(s) or invariant(s) it serves.

---

## File map

| File | Responsibility |
| --- | --- |
| `python/src/beliefs/errors.py` | `RetractionUnreadable`, `RetractionResolutionDisagreement`, `ProducerSnapshotMismatch` (Task 1) |
| `python/src/beliefs/closure.py` | `RETRACTION_UPHELD`, `RETRACTION_OVERTURNED` beside `RetractionEnumeration` (Task 1) |
| `python/src/beliefs/corpus.py` | `retraction_standing`, `local_retraction_enumeration`, `ReadView.corpus_id`; `standing_in_local_view` over the shared fold; `lineage_snapshot` reads each route's `identity` (Tasks 1, 3) |
| `python/src/beliefs/world/epoch.py` | `_standing_retractions` calls the shared fold; the two resolution constants imported from `closure` (Task 1) |
| `python/src/beliefs/world/view.py` | the enumeration and the producer-snapshot identity parsed and checked at `open_world_view`; `retraction_enumeration()`, `producer_snapshot_identity()` (Task 2) |
| `python/src/beliefs/lineage.py` | `Route.identity`, `LineageSnapshot.retired`, `retire`, `effective_routes`, `effective_tag`, `absences`; `_closure`, `divergence_state`, `_absent_references`, `snapshot_projection` over effective routes (Task 3) |
| `python/src/beliefs/belief.py` | `SuppliedContext` without `retractions`; `evaluate_traced`/`evaluate` with `retractions=` (Task 4) |
| `python/src/beliefs/evaluation.py` | `gather`: dereference, fold, refuse, subtract, scope, absences, the retired snapshot; `evaluate_over_traced`'s handoff; the `assesses`-edge filter (`beliefs-010c6e`) (Task 4) |
| `python/src/beliefs/verification.py` | docstring: where the G8 §7a clause lives (Task 4) |
| `python/src/beliefs/composite.py` | inherits through `evaluate_over_traced`; the tidy of `beliefs-b1245d` (Tasks 4, 5) |
| `python/src/beliefs/audit.py` | `_recompute` runs `check_spec_target` (`beliefs-0521da`) (Task 5) |
| `python/src/beliefs/contract/base.py`, `decode.py`, `estimand.py` | the three closed sets total in code (`beliefs-1dd03f`) (Task 5) |
| `python/tools/reproduction/belief.py` | `context()` without `retractions` (Task 6) |
| `python/tests/test_standing_read.py`, `test_world_standing.py` (new); `test_lineage.py`, `test_local_standing.py`, `test_world_view.py`, `test_retract.py`, `test_composite_reading.py`, `test_belief.py`, `test_evaluation.py`, `test_deletion_rows.py`, `test_reproduction_driver.py`, `verification_fixtures.py`, `domain_facet_fixtures.py`, `acceptance/test_deletion_acceptance.py`, `acceptance/test_confinement_acceptance.py`, `acceptance/test_world_view_acceptance.py` | unit coverage and the contract edits (Tasks 1–5) |
| `python/tests/acceptance/test_correction_acceptance.py`, `python/tests/n2_arms_cut33.py`, `python/tests/acceptance/n2_arms_cut33.py`, `python/tests/acceptance/test_n2_cut33.py`, `python/tools/cut33_acceptance.py` | the eleven declaration units, the sabotages, the guard, the runner (Task 7) |
| `docs/designs/2026-09-16-conformance-cut-33.md`, `docs/plans/2026-09-16-conformance-cut-33-results.md`, the ledger, the roadmap, the guide, `README.md`, the composite-claims design (limitation 16), the reproduction record §12 | freeze, discharge, amendments (Tasks 0, 6, 8) |

**One correction to the spec, found while planning and recorded in its review log at Task 0.** Spec §10 says "every pinned closure digest moves with the `retired` key". The reproduction's answer is a `NoBelief` (record §3 step 8: `no-eligible-assessment`; 2026-09-08 `no-directional-outcome`), and a `NoBelief` carries no `belief_input_digest`, so there is no pinned digest to move. What the re-run measures is narrower and stated as such in §12 of the record: the same answer, with the enumeration now derived (`found=()`, `coverage=(corpus_id,)`) rather than supplied. Nothing is recreated and nothing is moved aside — no contract succeeded — so §10's "moved aside to `.work/reproduction/mm30.cut32`" does not happen; Task 6 says why in the record.

---

### Task 0: Freeze cut 33 and file the tasks

**Files:**
- Create: `docs/designs/2026-09-16-conformance-cut-33.md`
- Modify: `docs/superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md` (§14, the planning correction above), `README.md` (the design table gains the cut row; "Every conformance cut through **cut 32**" stays until discharge), `docs/guide/contracts-and-adoption.md` (`sources` gains the cut document; a "Cut 33 is frozen and not yet discharged" line after cut 32's)
- Tasks: already filed (Step 3); `tasks start beliefs-9429af`

**Interfaces:**
- Produces: the freeze commit `CUT33_FREEZE_COMMIT` and the cut document's SHA-256, both pinned by Task 7's guard; the task ids every later commit closes.

- [x] **Step 1: Confirm the baseline and the lane**

Run `git -C /mnt/ssd/Dropbox/beliefs log --oneline -1` and confirm `main` is at `25ab84c` or a descendant that touches none of the shared surfaces (`evaluation.py`, `belief.py`, `closure.py`, `corpus.py`, `lineage.py`, `world/view.py`, `world/epoch.py`); if it moved, `git rebase main` in the worktree, re-read spec §1's baseline claims against the tree, and record any drift in the spec's §14 before continuing. Run `tasks prime` inside the worktree: `beliefs-aa27da` is `doing`, owned by this branch; no other kernel lane is open (roadmap lane table: `world-read`, `mutation`, `acquisition`, `cross-repo` all "waits" or closed). Note it: `tasks note beliefs-aa27da "lane admitted under rule 6 at cut 33: no kernel lane open, tier 1 on-path empty"`.

- [x] **Step 2: Claim the cut number**

`git worktree list`, then `ls <each worktree>/docs/designs/*conformance-cut-3[3-9]*.md` and `for b in $(git branch --format='%(refname:short)'); do git ls-tree -r --name-only $b docs/designs | grep -i 'cut-3[3-9]'; done`. Nothing may match; if something does, the number is the next unclaimed one and every `33` below moves with it (concurrency rule 1). The highest discharged runner is `python/tools/cut32_acceptance.py` (`PREFIX_RUNNERS` for Task 7).

- [x] **Step 3: The tasks are filed**

Filed at the planning commit so `tasks check` links every heading: the slice-1 task is `beliefs-dc4e56` (child of `beliefs-aa27da`, carrying the spec and this plan), its step children are `beliefs-9429af` (Task 0), `beliefs-3f6f07` (1), `beliefs-57fb55` (2), `beliefs-738d42` (3), `beliefs-d5512a` (4), `beliefs-8d4109` (5), `beliefs-2a75e1` (6), `beliefs-d25046` (7), `beliefs-f4a89c` (8), and the four riders (`beliefs-0521da`, `beliefs-1dd03f`, `beliefs-010c6e`, `beliefs-b1245d`) are reparented under it. `tasks start <step>` before each task, `tasks done <step> "<what landed>"` in its commit; `S1` below means `beliefs-dc4e56`.

- [x] **Step 4: Write and freeze the cut document**

Write `docs/designs/2026-09-16-conformance-cut-33.md` on cut 32's shape (`docs/designs/2026-09-16-conformance-cut-32.md`): a `**Status:**` line ("frozen 2026-09-16, before implementation; C7, C3's coverage clauses and C10's audit arm are open"); §1 what this cut is (spec §1, condensed; the slice design cited by its `docs/superpowers/specs/` path — a slice design stays there, as the six world-resolution slices did); §2 the boundary — the files in the file map above, named as the surfaces a sabotage may land in; §3 selection — the eleven declaration units single-homed, each with its frozen row text quoted where it has one:

| unit | row | what it reads |
|---|---|---|
| C7-a | C7 | conflict of two routes, retire one → certifiable over the survivor |
| C7-b | C7 | retire both → `not-certified` with `lineage-incomplete` |
| C7-c | C7 | the stored basis facet byte-unchanged throughout; `retract` writes one record |
| C3-a | C3 | a standing retraction in an uncovered corpus → digest unchanged; the coverage declaration a digest member (the isolated closure check) |
| C3-b | C3 | an in-coverage `move` → digest unchanged, the receipts record the new states |
| C10-a | C10 | four raw-written refused shapes reported by `audit_corpus` and `audit_world` as `retraction-target-invalid` |
| BI-1 | — | node standing subtracts an assessment at the read |
| BI-2 | — | the amended G8 clause: a retracted verification leaves the read set (three cases) |
| BI-3 | — | the enumeration is the view's and input-scoped (matching and unrelated retractions together) |
| BI-4 | — | an unreadable found retraction refuses |
| BI-5 | — | a resolution disagreement refuses |

with the clauses of C3 and C10 that stay open named (C10's `instrument-certification` eligibility → `contract-cut`); §4 accounting — "**11 declaration units**, six against rows and five boundary invariants; C7 closes, C3 closes, C10 stays part"; §5 N2 and acceptance obligations — spec §8.3's table, one arm per unit, the `before` blocks written in Task 7 against the tree at freeze; `PREFIX_RUNNERS = ("cut32_acceptance.py",)`; §6 second reader — the overstated-coverage attack, and the two things a reader must check: that BI-1/BI-2 read through `evaluate_over` with no test-side filtering, and that C3-a's closure check varies only `retractions.coverage`; §7 limitations — spec §11, restated. Add the cut row to `README.md`'s design table (the row shape cut 32's uses, status "frozen"); in `docs/guide/contracts-and-adoption.md` add the cut document to `sources` and, after the cut-32 line, "Cut 33 is frozen and not yet discharged: correction-remainder slice 1, standing reaches the evaluator (C7, C3's coverage clauses, C10's audit arm; `../designs/2026-09-16-conformance-cut-33.md`)". Append the planning correction (file map, above) to the spec's §14. Run `cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green — `test_the_newest_cut_document_says_it_is_discharged` reads the newest *results* record's cut, still 32, so a frozen 33 passes.

```bash
tasks done beliefs-9429af "cut 33 frozen"
git add docs/designs/2026-09-16-conformance-cut-33.md README.md docs/guide/contracts-and-adoption.md docs/superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md tasks
git commit -m "docs(cut): freeze conformance cut 33, correction-remainder slice 1"
```

Record the commit hash: `git rev-parse HEAD` is `CUT33_FREEZE_COMMIT`; `sha256sum docs/designs/2026-09-16-conformance-cut-33.md` is `CUT33_FROZEN_SHA256` (Task 7).

---

### Task 1: Errors, the shared fold, the local enumeration

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `RetractionGroundsMissing`, line ~1128), `python/src/beliefs/closure.py` (beside `RetractionEnumeration`, line 59), `python/src/beliefs/corpus.py` (`standing_in_local_view` at 949–970; `ReadView` at 241; `__all__` at ~147–166), `python/src/beliefs/world/epoch.py` (`_standing_retractions` at 1271–1321; the constants at 916–918)
- Test: `python/tests/test_standing_read.py` (new), `python/tests/test_local_standing.py` (unchanged assertions), `python/tests/test_world_build.py` (unchanged)

**Interfaces:**
- Produces: `errors.RetractionUnreadable(ref: str, cause: str)` (`RecordError`; `.ref`, `.cause`), `errors.RetractionResolutionDisagreement(ref, recorded, computed)` (`RecordError`), `errors.ProducerSnapshotMismatch(supplied, bound)` (`RecordError`); `closure.RETRACTION_UPHELD = "upheld"`, `closure.RETRACTION_OVERTURNED = "overturned"`; `corpus.retraction_standing(view, facets) -> Mapping[str, bool]`; `corpus.local_retraction_enumeration(view: ReadView) -> RetractionEnumeration`; `ReadView.corpus_id -> str`.

- [x] **Step 1: The errors and the constants**

In `errors.py`, after `RetractionGroundsMissing`:

```python
class RetractionUnreadable(RecordError):
    """A found retraction the evaluator cannot read — its facet, its stamp, its
    target's exact resolution or content identity, or its route — so standing
    is undecidable for every input it might name (correction-remainder slice 1
    §4, decision 4). The audit names the record; `delete` is the remedy."""

    def __init__(self, ref: str, cause: str) -> None:
        super().__init__(f"{ref}: standing is undecidable: {cause}")
        self.ref = ref
        self.cause = cause


class RetractionResolutionDisagreement(RecordError):
    """The evaluator's standing fold and the enumeration's recorded resolution
    disagree for one retraction — the epoch folded per corpus and a `move`
    separated a counter-retraction from what it counters (slice 1 §11.1)."""

    def __init__(self, ref: str, recorded: str, computed: str) -> None:
        super().__init__(f"{ref}: the enumeration records {recorded!r} but the standing fold computes {computed!r}")
        self.ref, self.recorded, self.computed = ref, recorded, computed


class ProducerSnapshotMismatch(RecordError):
    """A world read was handed a producer-snapshot identity that is not the
    bound epoch's (slice 1 decision 2)."""

    def __init__(self, supplied: str, bound: str) -> None:
        super().__init__(f"the supplied producer snapshot {supplied!r} is not the bound epoch's {bound!r}")
        self.supplied, self.bound = supplied, bound
```

Add the three names to `errors.__all__` if the module keeps one (check `grep -n "__all__" python/src/beliefs/errors.py`; follow what it does for `RetractionGroundsMissing`).

In `closure.py`, directly above `class RetractionEnumeration`:

```python
RETRACTION_OVERTURNED = "overturned"
RETRACTION_UPHELD = "upheld"
RETRACTION_RESOLUTIONS: tuple[str, ...] = (RETRACTION_OVERTURNED, RETRACTION_UPHELD)
"""The closed resolution vocabulary a found retraction carries — a capture's
per-corpus fold (`epoch`) and the corpus-local enumeration (`corpus`) both
spell it here, so the closure member and both producers share one set."""
```

Add the three to `closure.__all__`. In `epoch.py`, replace lines 916–918 with

```python
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_RESOLUTIONS, RETRACTION_UPHELD  # noqa: E402 — re-exported under the names cut 7 pinned
```

placed with the other imports at the top of the module (move it there; keep the docstring that followed the constants, now under the import). Run `cd python && uv run --frozen ruff check src/beliefs/world/epoch.py` — if ruff refuses the placement, keep the three names as `RETRACTION_OVERTURNED = closure.RETRACTION_OVERTURNED` assignments at their original lines instead.

- [x] **Step 2: The failing tests for the fold and the local enumeration**

Create `python/tests/test_standing_read.py`:

```python
"""Standing at the read (correction-remainder slice 1): the fold, the local
enumeration, and — from Task 4 on — `gather`'s subtraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import ACTOR, FULL
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_local_standing import assessment, retracts

from beliefs import corpus, stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, RetractionEnumeration
from beliefs.corpus import CorpusWriter, ReadView, local_retraction_enumeration, retraction_standing
from beliefs.errors import RetractionUnreadable


def adopted(tmp_path: Path, name: str = "corpus") -> CorpusWriter:
    """A corpus with a manifest: `ReadView.corpus_id` reads one, and
    `test_local_standing.seed` writes none (spec §8.1)."""
    writer = CorpusWriter(tmp_path / name, DefaultExecutor, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return writer


def test_the_local_enumeration_is_empty_with_the_manifest_coverage(tmp_path):
    writer = adopted(tmp_path)
    view = writer.read_view
    assert view.corpus_id == writer.corpus_id
    assert local_retraction_enumeration(view) == RetractionEnumeration(found=(), coverage=(writer.corpus_id,))


def test_the_local_enumeration_folds_standing_and_keys_by_id(tmp_path):
    writer = adopted(tmp_path)
    target = writer.add(assessment())
    first = writer.retract(retracts(target, "t1"))
    counter = writer.retract(retracts(first, "t2"))
    view = writer.read_view
    found = dict(local_retraction_enumeration(view).found)
    assert found == {first.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
    facets = {n.id: corpus._validated_retraction_facet(n) for n in view.iter_stored() if n.kind == "retraction"}
    standing = retraction_standing(view, facets)
    assert standing[first.id] is False and standing[counter.id] is True and standing[target.id] is True
    assert corpus.standing_in_local_view(view, target.id) is True  # the only retraction of the target is overturned


def test_a_manifest_less_corpus_cannot_declare_coverage(tmp_path):
    from fixtures_cut4 import raw_write, reopen

    raw_write(tmp_path / "bare", assessment())
    with pytest.raises(Exception):  # the manifest loader's own refusal, unchanged
        local_retraction_enumeration(reopen(tmp_path / "bare")).coverage


def test_a_raw_retraction_the_capture_validator_refuses_is_unreadable_at_the_enumeration(tmp_path):
    from fixtures_cut4 import raw_write

    writer = adopted(tmp_path)
    target = writer.add(assessment())
    node = retracts(target, "t1")
    node.facets[stored.RETRACTION_FACET].pop("grounds")
    raw_write(writer.root, stored.stamp_semantic_identity(node))
    with pytest.raises(RetractionUnreadable) as refused:
        local_retraction_enumeration(ReadView.opened_at(writer.root))
    assert refused.value.ref == node.id
    assert refused.value.cause == f"{node.id}: malformed retraction facet"
```

`assessment()` and `retracts()` are `test_local_standing.py`'s. Seed the real write boundary's dataset, run, and proposition prerequisites before adding the assessment, as `test_retract.py` does. `reopen` and `raw_write` are `fixtures_cut4.py`'s. The capture validator deliberately reports the closed-layout refusal as the generic `malformed retraction facet`; `RetractionUnreadable.cause` preserves that message byte-for-byte and chains the original `MalformedRecord`. If `writer.root` is not the attribute name, use what `CorpusWriter` exposes (`grep -n "def root" python/src/beliefs/corpus.py`).

Run: `cd python && uv run --frozen pytest tests/test_standing_read.py -q`
Expected: FAIL — `ImportError: cannot import name 'local_retraction_enumeration'`.

- [x] **Step 3: The fold, the local enumeration, `corpus_id`**

In `corpus.py`, replace `standing_in_local_view` (lines 949–970) with the fold and the reading over it:

```python
def retraction_standing(
    view: ReadView | WorldReadView, facets: Mapping[str, Mapping[str, object]]
) -> Mapping[str, bool]:
    """The graph half of standing, over validated retraction facets keyed by
    retraction id: `standing[x]` is whether `x` — a target or a retraction —
    is not named by any standing retraction. Node-arm targets are resolved
    through `view.resolve`, as the corpus-local judgement and the epoch's
    capture both resolve them; route-arm retractions subtract no node
    standing and enter as vertices only. A cycle is `RetractionCycleMalformed`.
    The one fold: `standing_in_local_view` and `epoch._standing_retractions`
    both read it (slice 1 decision 8)."""
    targets: dict[str, list[str]] = {}
    for address, facet in facets.items():
        target = cast(Mapping[str, str], facet["target"])
        if target["arm"] != "node":
            continue
        resolved = view.resolve(target["ref"])
        if resolved is not None:
            targets.setdefault(resolved, []).append(address)
    graph = {target: tuple(sorted(retractions)) for target, retractions in targets.items()}
    standing: dict[str, bool] = {}
    for target in _acyclic_postorder(graph):
        standing[target] = not any(standing[retraction] for retraction in graph.get(target, ()))
    for address in facets:
        standing.setdefault(address, True)
    return MappingProxyType(standing)


def local_retraction_enumeration(view: ReadView) -> RetractionEnumeration:
    """The corpus-local retraction enumeration: every stored retraction with
    its folded resolution, under the coverage this corpus alone declares
    (slice 1 §3.1). Validated with the capture's validator, as the epoch
    build validates; a record it refuses is `RetractionUnreadable` here, so
    decision 4's promise holds whichever validator meets the record first."""
    facets: dict[str, Mapping[str, object]] = {}
    for node in view.iter_stored():
        if node.kind != "retraction":
            continue
        try:
            facets[node.id] = _validated_retraction_facet(node)
        except ScienceError as caught:
            raise RetractionUnreadable(node.id, str(caught)) from caught
    standing = retraction_standing(view, facets)
    found = tuple(sorted((ref, RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED) for ref in facets))
    return RetractionEnumeration(found=found, coverage=(view.corpus_id,))


def standing_in_local_view(view: ReadView, ref: str) -> bool:
    """Whether `ref` has no standing node-arm retraction in this corpus.

    This is deliberately non-authoritative and corpus-local. Route-arm targets
    name an embedded route, not a record, so they never subtract node standing.
    Every retraction is put through the boundary's target validation first,
    so a drifted target refuses the judgement rather than being folded.
    """
    facets: dict[str, Mapping[str, object]] = {}
    for stored_node in view.iter_stored():
        if stored_node.kind != "retraction":
            continue
        retraction = view.get(stored_node.id)
        facets[retraction.id] = CorpusWriter._validated_retraction(retraction)
        CorpusWriter._resolve_retraction_target(retraction, view)
    standing = retraction_standing(view, facets)
    return standing.get(view.resolve(ref) or ref, True)
```

The last line is byte-identical to the baseline's (cut 5's `_STANDING_DISABLED` pins it). **Imports: `corpus.py` may not import `closure` at module level** — `closure → facet_read → corpus` closes a cycle and `ReadView` is then partially initialized at import (reproduced). So `local_retraction_enumeration` begins with a function-local `from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, RetractionEnumeration`, and the return annotation's name comes from an `if TYPE_CHECKING:` block at the top of the module (`from beliefs.closure import RetractionEnumeration`), the way `WorldReadView` is already annotated there. `RetractionUnreadable` from `beliefs.errors` at module level; `ScienceError` is already imported (the check code uses it). Add `"retraction_standing"`, `"local_retraction_enumeration"` to `__all__`.

In `class ReadView`, after `opened_at`:

```python
    @property
    def corpus_id(self) -> str:
        """The manifest's corpus identity — what the corpus-local enumeration
        declares as coverage. A corpus without a readable manifest cannot
        declare coverage; the loader's refusal is the answer."""
        from beliefs.world import load_manifest

        return load_manifest(self._corpus.store.root).corpus_id
```

In `epoch.py`, replace the body of `_standing_retractions` (keep the signature and the docstring) with:

```python
    return corpus_module.retraction_standing(view, facets)
```

where `corpus_module` is however `epoch.py` reaches `beliefs.corpus` (it imports names from it at line 106; add `retraction_standing` to that import and call it directly). The docstring's "computed for every retraction at once instead of one at a time" sentence is replaced by "the one fold, `corpus.retraction_standing`, which `standing_in_local_view` also reads"; the rest stands.

Run: `cd python && uv run --frozen pytest tests/test_standing_read.py tests/test_local_standing.py tests/test_world_build.py tests/test_world_receipts.py -q`
Expected: PASS.

- [x] **Step 4: The staleness probe over cuts 5 and 7**

Run `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut32.py::test_prior_declarations_are_frozen_and_no_check_is_reclaimed -q` (the frozen files are untouched) and then the probe itself: `uv run --frozen python -m arm_staleness --cuts 5 7` — if the module has no CLI, run `uv run --frozen pytest tests/test_arm_staleness.py -q -k "cut5 or cut7"`; read `tests/arm_staleness.py`'s docstring for the invocation. Every arm of cuts 5 and 7 must still be `sound`; a `stale` arm whose `before` string moved is re-targeted in the live guard by the mechanism `test_n2_cut25.py`'s `RETARGETED_ROWS` established (never in the frozen file), and recorded in the task note. Expected: nothing stale — no cut-7 arm pins a line inside `_standing_retractions`' body, and cut 5's pinned return line is verbatim.

- [x] **Step 5: Commit**

```bash
tasks check
git add python/src/beliefs/errors.py python/src/beliefs/closure.py python/src/beliefs/corpus.py python/src/beliefs/world/epoch.py python/tests/test_standing_read.py
git commit -m "feat(correction): one standing fold, the corpus-local enumeration, ReadView.corpus_id (BI-3, BI-4)"
```

---

### Task 2: The world view carries the epoch's enumeration and snapshot identity

**Files:**
- Modify: `python/src/beliefs/world/view.py` (`open_world_view` at 206; `_opened` at 73; the class attributes at 55–68)
- Test: `python/tests/test_world_view.py` (a new class `TestTheEpochsEnumeration`)

**Interfaces:**
- Consumes: `derive.retraction_enumeration`, `derive.retraction_enumeration_identity`, `read._thawed`, `epoch.Epoch.receipts[member].document / .subject_identity`.
- Produces: `WorldReadView.retraction_enumeration() -> RetractionEnumeration`, `WorldReadView.producer_snapshot_identity() -> str`; `EpochMalformed` at open for a carried enumeration that does not parse or does not recompute to the receipt's subject.

- [x] **Step 1: The failing tests**

Append to `python/tests/test_world_view.py`:

```python
class TestTheEpochsEnumeration:
    def test_the_view_carries_the_receipts_enumeration_and_the_producer_subject(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        receipt = published.receipts["retraction-receipt.yaml"]
        from beliefs.world import derive

        assert view.retraction_enumeration() == derive.retraction_enumeration(
            read._thawed(receipt.document["enumeration"])
        )
        assert view.retraction_enumeration().coverage == (ALPHA, BETA)
        assert view.producer_snapshot_identity() == published.receipts["producer-receipt.yaml"].subject_identity

    def test_an_edited_enumeration_that_no_longer_digests_to_the_subject_refuses_the_open(self, tmp_path):
        from dataclasses import replace as _replace

        from beliefs.errors import EpochMalformed

        world, roots, published = two_corpus_world(tmp_path)
        carrier = published.receipts["retraction-receipt.yaml"]
        document = dict(carrier.document)
        document["enumeration"] = {"found": [["retraction:forged", "upheld"]], "coverage": list(published.coverage and (ALPHA, BETA))}
        forged = _replace(carrier, document=document) if hasattr(carrier, "__dataclass_fields__") else carrier
        receipts = dict(published.receipts)
        receipts["retraction-receipt.yaml"] = forged
        edited = _replace(published, receipts=receipts)
        with pytest.raises(EpochMalformed, match="does not digest to the subject"):
            open_world_view(world, edited)

    def test_a_carried_enumeration_that_does_not_parse_refuses_the_open(self, tmp_path):
        from dataclasses import replace as _replace

        from beliefs.errors import EpochMalformed

        world, roots, published = two_corpus_world(tmp_path)
        carrier = published.receipts["retraction-receipt.yaml"]
        document = dict(carrier.document)
        document["enumeration"] = {"found": "not-a-list", "coverage": [ALPHA, BETA]}
        receipts = dict(published.receipts)
        receipts["retraction-receipt.yaml"] = _replace(carrier, document=document)
        with pytest.raises(EpochMalformed, match="not .*projection"):
            open_world_view(world, _replace(published, receipts=receipts))
```

`_ReceiptCarrier` is a dataclass (`epoch.py:290`; check `@dataclass` above it — if it is a plain class, construct the forged carrier with `epoch._ReceiptCarrier(**{**vars(carrier), "document": document})`). `Epoch` is a frozen dataclass, so `dataclasses.replace` works on it.

Run: `cd python && uv run --frozen pytest tests/test_world_view.py::TestTheEpochsEnumeration -q`
Expected: FAIL — `AttributeError: 'WorldReadView' object has no attribute 'retraction_enumeration'`.

- [x] **Step 2: Parse and check at the open**

In `view.py`, after `stamp = _stamp(published)` at the top of `open_world_view`, before the lock:

```python
    enumeration = _carried_enumeration(published)
    producer_identity = published.receipts["producer-receipt.yaml"].subject_identity
    if producer_identity is None:
        raise EpochMalformed(f"{published.packaging_identity}: the producer receipt names no subject identity")
```

and the helper, at module level below `open_world_view`:

```python
def _carried_enumeration(published: epoch.Epoch) -> RetractionEnumeration:
    """§7.6's enumeration, lifted from `retraction-receipt.yaml`'s `enumeration`
    key — an epoch has no enumeration document — thawed from the deep-frozen
    parse the open performed, and accepted only when it digests to the subject
    the receipt names (slice 1 §3.1). An edited receipt would otherwise feed
    the belief digest an enumeration nothing checked."""
    receipt = published.receipts["retraction-receipt.yaml"]
    carried = receipt.document.get("enumeration")
    if not isinstance(carried, Mapping):
        raise EpochMalformed(f"{published.packaging_identity}: retraction-receipt.yaml carries no enumeration mapping")
    try:
        enumeration = derive.retraction_enumeration(_thawed(carried))
    except Exception as caught:  # noqa: BLE001 — any refusal here is the same finding
        raise EpochMalformed(
            f"{published.packaging_identity}: the carried enumeration is not §7.6's projection: {caught}"
        ) from caught
    identity = derive.retraction_enumeration_identity(enumeration)
    if identity != receipt.subject_identity:
        raise EpochMalformed(
            f"{published.packaging_identity}: the carried enumeration does not digest to the subject the receipt "
            f"names ({identity} != {receipt.subject_identity})"
        )
    return enumeration
```

Imports: `from beliefs.closure import RetractionEnumeration`, `from beliefs.errors import EpochMalformed` (add to the existing `errors` import), `from beliefs.world import derive, epoch, registry`, and `_thawed` added to the existing `from beliefs.world.read import ...` line. Thread both values through `_opened` (new keyword parameters `retractions: RetractionEnumeration` and `producer_snapshot: str`, assigned to `view._retractions` and `view._producer_snapshot`; declare both in the class's attribute block), pass them at the end of `open_world_view`, and add the two methods after `published_producers`:

```python
    def retraction_enumeration(self) -> RetractionEnumeration:
        """The enumeration the bound epoch published — the evaluator's, never
        a caller's (slice 1 decision 1)."""
        return self._retractions

    def producer_snapshot_identity(self) -> str:
        """The bound epoch's producer-snapshot subject identity, which a
        supplied one must equal (slice 1 decision 2)."""
        return self._producer_snapshot
```

Run: `cd python && uv run --frozen pytest tests/test_world_view.py -q`
Expected: PASS.

- [x] **Step 3: Commit**

```bash
tasks check
git add python/src/beliefs/world/view.py python/tests/test_world_view.py
git commit -m "feat(world): the read view carries the epoch's enumeration and producer subject, checked at open (BI-3)"
```

---

### Task 3: Lineage — route identities, retirement, effective routes, walk absences

**Files:**
- Modify: `python/src/beliefs/lineage.py` (`Route` at 92, `LineageSnapshot` at 170, `divergence_state` at 216, `_closure` at 250, `_absent_references` at 329, `_route_projection` at 354, `snapshot_projection` at 371, `__all__`), `python/src/beliefs/corpus.py` (`lineage_snapshot` at 1119–1175)
- Test: `python/tests/test_lineage.py`

**Interfaces:**
- Produces: `Route.identity: str | None = None`; `LineageSnapshot.retired: Mapping[str, tuple[str, ...]]` (default empty); `lineage.retire(snapshot, retired: Mapping[str, Iterable[str]]) -> LineageSnapshot`; `lineage.effective_routes(snapshot, dataset) -> tuple[Route, ...]`; `lineage.effective_tag(snapshot, dataset) -> Literal["single", "conflict", "retired"]`; `lineage.absences(snapshot) -> tuple[Absence, ...]`; the projection's per-dataset `retired` list and per-route `identity` list.

- [x] **Step 1: The failing tests**

Append to `python/tests/test_lineage.py` (the `route` helper at the top gains an `identity: str | None = None` keyword passed through to `Route`):

```python
from beliefs.lineage import absences, effective_routes, effective_tag, retire


def conflict_snapshot(*, retired: dict[str, tuple[str, ...]] | None = None, not_present=None) -> LineageSnapshot:
    """x with two routes to distinct ancestors a and b, y with one route to c."""
    snapshot = LineageSnapshot(
        roots=("x", "y"),
        bases={
            "x": Basis(tag="conflict", routes=tuple(sorted(
                (route("x", "a", identity="route:a"), route("x", "b", identity="route:b")),
                key=lambda r: (r.stored_ancestor,)))),
            "y": Basis(tag="single", routes=(route("y", "c", identity="route:c"),)),
        },
        producers={},
        not_present=not_present or {},
    )
    return retire(snapshot, retired or {})


class TestRetirement:
    def test_effective_tag_follows_the_survivors(self):
        assert effective_tag(conflict_snapshot(), "x") == "conflict"
        assert effective_tag(conflict_snapshot(retired={"x": ("route:a",)}), "x") == "single"
        assert effective_tag(conflict_snapshot(retired={"x": ("route:a", "route:b")}), "x") == "retired"
        assert effective_tag(conflict_snapshot(retired={"y": ("route:c",)}), "y") == "retired"
        assert [r.stored_ancestor for r in effective_routes(conflict_snapshot(retired={"x": ("route:a",)}), "x")] == ["b"]

    def test_retiring_one_conflicting_route_certifies_over_the_survivor(self):
        assert certify(conflict_snapshot(), ("x",), ("y",)).findings == ("lineage-divergent",)
        result = certify(conflict_snapshot(retired={"x": ("route:a",)}), ("x",), ("y",))
        assert result.state == "independent" and result.findings == ()

    def test_retiring_every_route_is_incomplete_never_single(self):
        result = certify(conflict_snapshot(retired={"x": ("route:a", "route:b")}), ("x",), ("y",))
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings and "lineage-divergent" not in result.findings

    def test_divergence_runs_against_the_survivor(self):
        snapshot = conflict_snapshot(retired={"x": ("route:a",)})
        producers = {"x": (Producer(stored_run="run-x", resolved_run="run-x", transforms=("t",)),)}
        snapshot = LineageSnapshot(roots=snapshot.roots, bases=snapshot.bases, producers=producers, retired=snapshot.retired)
        # the survivor's transforms are (); the producer's ("t",) diverge from it
        assert divergence_state(snapshot, "x") == "divergent"
        with pytest.raises(BasisTagMismatch):
            divergence_state(conflict_snapshot(), "x")
        with pytest.raises(BasisTagMismatch):
            divergence_state(conflict_snapshot(retired={"x": ("route:a", "route:b")}), "x")

    def test_the_projection_carries_retired_and_identities_and_moves(self):
        plain = snapshot_projection(conflict_snapshot())
        assert plain["bases"]["x"]["retired"] == [] and plain["bases"]["y"]["retired"] == []
        assert [r["identity"] for r in plain["bases"]["x"]["routes"]] == [["route:a"], ["route:b"]]
        assert plain["divergence"]["x"] == "divergent"
        one = snapshot_projection(conflict_snapshot(retired={"x": ("route:a",)}))
        assert one["bases"]["x"]["retired"] == ["route:a"] and one["divergence"]["x"] == "undiverged"
        both = snapshot_projection(conflict_snapshot(retired={"x": ("route:a", "route:b")}))
        assert both["divergence"]["x"] == "incomplete"
        assert plain != one != both
        no_identity = snapshot_projection(LineageSnapshot(roots=("z",), bases={"z": Basis(tag="single", routes=(route("z", "w"),))}, producers={}))
        assert no_identity["bases"]["z"]["routes"][0]["identity"] == []

    def test_swapping_identities_swaps_the_survivor_and_the_projection(self):
        swapped = LineageSnapshot(
            roots=("x", "y"),
            bases={
                "x": Basis(tag="conflict", routes=tuple(sorted(
                    (route("x", "a", identity="route:b"), route("x", "b", identity="route:a")),
                    key=lambda r: (r.stored_ancestor,)))),
                "y": Basis(tag="single", routes=(route("y", "c", identity="route:c"),)),
            },
            producers={},
        )
        original = retire(conflict_snapshot(), {"x": ("route:a",)})
        swapped = retire(swapped, {"x": ("route:a",)})
        assert [r.stored_ancestor for r in effective_routes(original, "x")] == ["b"]
        assert [r.stored_ancestor for r in effective_routes(swapped, "x")] == ["a"]
        assert snapshot_projection(original) != snapshot_projection(swapped)

    def test_retire_keeps_only_datasets_with_a_basis_and_refuses_unsorted(self):
        snapshot = retire(conflict_snapshot(), {"x": ("route:b", "route:a"), "elsewhere": ("route:z",)})
        assert dict(snapshot.retired) == {"x": ("route:a", "route:b")}
        with pytest.raises(MalformedSnapshot):
            LineageSnapshot(roots=("x",), bases={}, producers={}, retired={"x": ("route:b", "route:a")})
        with pytest.raises(MalformedSnapshot):
            LineageSnapshot(roots=("x",), bases={}, producers={}, retired={"x": ("route:a", "route:a")})


class TestWalkAbsences:
    def test_an_absence_on_a_retired_branch_blocks_nothing(self):
        snapshot = conflict_snapshot(retired={"x": ("route:a",)}, not_present={"a": "c2"})
        assert absences(snapshot) == ()
        assert certify(snapshot, ("x",), ("y",)).state == "independent"

    def test_an_absence_on_the_surviving_route_blocks(self):
        snapshot = conflict_snapshot(retired={"x": ("route:a",)}, not_present={"b": "c2"})
        assert absences(snapshot) == (Absence("b", "c2"),)

    def test_an_absence_beneath_an_unretired_conflict_is_not_reached(self):
        snapshot = conflict_snapshot(not_present={"a": "c2"})
        assert absences(snapshot) == ()
        result = certify(snapshot, ("x",), ("y",))
        assert result.state == "not-certified" and result.findings == ("lineage-divergent",)

    def test_an_absent_root_and_a_producer_absence_are_still_reached(self):
        snapshot = LineageSnapshot(
            roots=("x",), bases={}, producers={"x": (Producer(stored_run="run-x", resolved_run=None, transforms=(), absent=("c9",)),)},
            not_present={"x": "c2"},
        )
        assert absences(snapshot) == (Absence("run-x", "c9"), Absence("x", "c2"))
```

Run: `cd python && uv run --frozen pytest tests/test_lineage.py -q`
Expected: FAIL — `ImportError: cannot import name 'absences'`.

- [x] **Step 2: Implement**

In `lineage.py`:

`Route` gains a trailing field `identity: str | None = None` (docstring: "the identity the stamped basis records for this route, or `None` when it records none — what a route-arm retraction names; a route without one is never retired"). `_route_sort_key` is unchanged (identity is not part of the order, so a conflict basis sorts as before).

`LineageSnapshot` gains `retired: Mapping[str, tuple[str, ...]] = field(default_factory=dict)` after `not_present`, and `__post_init__` gains, before the proxies are set:

```python
        for dataset, identities in self.retired.items():
            if (
                type(dataset) is not str
                or type(identities) is not tuple
                or not all(type(i) is str and i for i in identities)
                or list(identities) != sorted(set(identities))
            ):
                raise MalformedSnapshot("a snapshot's retired map holds sorted, distinct route identities per dataset")
        object.__setattr__(self, "retired", MappingProxyType(dict(self.retired)))
```

Then, after `LineageSnapshot`:

```python
def retire(snapshot: LineageSnapshot, retired: Mapping[str, Iterable[str]]) -> LineageSnapshot:
    """The same snapshot with `retired` set — restricted to datasets that carry
    a basis, since a route arm resolving to a dataset outside the walk retires
    nothing the walk reads (slice 1 §4). Sorted and deduplicated here so the
    caller hands over what it found and the snapshot spells it one way."""
    kept = {dataset: tuple(sorted(set(identities))) for dataset, identities in retired.items() if dataset in snapshot.bases}
    return LineageSnapshot(
        roots=snapshot.roots, bases=snapshot.bases, producers=snapshot.producers, not_present=snapshot.not_present, retired=kept
    )


def effective_routes(snapshot: LineageSnapshot, dataset: str) -> tuple[Route, ...]:
    """The basis's routes minus the retired ones — what the walk reads. A route
    with no identity cannot be named by a retirement and always survives."""
    retired = frozenset(snapshot.retired.get(dataset, ()))
    return tuple(r for r in snapshot.bases[dataset].routes if r.identity is None or r.identity not in retired)


def effective_tag(snapshot: LineageSnapshot, dataset: str) -> str:
    """`conflict` for two or more surviving routes, `single` for one, `retired`
    for none: a stored conflict with one survivor is effectively single, and a
    stored single whose route is retired is effectively retired — never
    silently single (C7)."""
    count = len(effective_routes(snapshot, dataset))
    return "conflict" if count >= 2 else "single" if count == 1 else "retired"
```

`divergence_state`: replace the two lines `if basis.tag != "single": raise BasisTagMismatch(...)` / `route = basis.routes[0]` with

```python
    tag = effective_tag(snapshot, dataset)
    if tag != "single":
        raise BasisTagMismatch(
            f"divergence_state is defined only against an effectively single basis; {dataset!r} is {tag!r}"
        )
    route = effective_routes(snapshot, dataset)[0]
```

(the `basis = snapshot.bases[dataset]` line stays for the `KeyError` it raises on an unknown dataset; the docstring's "Defined only against a `single` basis" becomes "against an effectively single basis — one surviving route (slice 1 §5)").

`_closure`: replace from `if basis.tag == "conflict":` through the `for r in basis.routes:` loop with

```python
        tag = effective_tag(snapshot, dataset)
        if tag == "conflict":
            findings.append("lineage-divergent")
            continue  # decided on the tag alone, before resolution or comparison
        if tag == "retired":
            findings.append("lineage-incomplete")  # every route retired: no standing ancestry, never silently single
            continue
        for r in effective_routes(snapshot, dataset):
            if r.resolved_run is None or r.resolved_ancestor is None:
                findings.append("lineage-incomplete")
                continue
            stack.append(r.resolved_ancestor)
```

`_absent_references` collects only what the walk examined: `_closure` adds a dataset to `inspected` and then stops on a `conflict` or a `retired` effective tag before reading any route or producer, so an absence beneath either is not examined and must not be collected (reproduced: the unretired-conflict fixture otherwise yields `Absence("a", "c2")`). Replace its loop body with

```python
    for dataset in inspected:
        basis = snapshot.bases.get(dataset)
        if basis is not None:
            if effective_tag(snapshot, dataset) != "single":
                continue  # the walk stopped here on the tag alone and examined no route or producer
            for route in effective_routes(snapshot, dataset):
                for ref in (route.stored_run, route.stored_ancestor):
                    if ref in snapshot.not_present:
                        named[ref] = snapshot.not_present[ref]
        for producer in snapshot.producers.get(dataset, ()):
            if producer.absent:
                named[producer.stored_run] = producer.absent[0]
```

(a basisless dataset keeps its producer check, as `_closure` does). Add after it:

```python
def absences(snapshot: LineageSnapshot) -> tuple[Absence, ...]:
    """The absences the effective walk from `snapshot.roots` reaches — what a
    belief evaluation records as `absent` from its lineage (slice 1 §4). An
    absence beneath a retired route, a conflict or an unresolved route is not
    reached, and `certify` answers `not-certified` for those on its own."""
    inspected, _findings = _walk_all(snapshot, snapshot.roots)
    return _absent_references(snapshot, inspected, snapshot.roots)
```

`_route_projection` gains `"identity": [] if route.identity is None else [route.identity],`. `snapshot_projection`: the `bases` comprehension emits `{"tag": basis.tag, "routes": [...], "retired": list(snapshot.retired.get(dataset, ()))}`, and `divergence` becomes

```python
    divergence = {}
    for dataset in snapshot.bases:
        tag = effective_tag(snapshot, dataset)
        divergence[dataset] = "divergent" if tag == "conflict" else "incomplete" if tag == "retired" else divergence_state(snapshot, dataset)
```

Add `retire`, `effective_routes`, `effective_tag`, `absences` to `__all__`; `Iterable` to the `collections.abc` import.

In `corpus.lineage_snapshot`, the `Route(...)` construction gains `identity=identity` where, above it:

```python
            identity = route.get("identity")
            if identity is not None and (type(identity) is not str or not identity):
                raise MalformedRecord(f"{dataset}: a stamped basis route's identity is a non-empty string when present")
```

Run: `cd python && uv run --frozen pytest tests/test_lineage.py tests/test_read_side.py tests/test_world_view.py tests/test_belief.py tests/test_evaluation.py -q`
Expected: PASS — every existing digest assertion that pins a literal projection must be updated for the two new keys (`retired`, `identity`); a test asserting a *literal* digest string moves (`grep -rn '"lineage"' python/tests | head` finds them). A test asserting equality between two projections built the same way does not.

- [x] **Step 3: Commit**

```bash
tasks check
git add python/src/beliefs/lineage.py python/src/beliefs/corpus.py python/tests/test_lineage.py
git commit -m "feat(lineage): route identities, retirement, effective routes and walk absences (C7)"
```

---

### Task 4: The evaluator — derived enumeration, subtraction at the read, the handoff

**Files:**
- Modify: `python/src/beliefs/belief.py` (`SuppliedContext` at 224–246; `evaluate_traced` at 258; `evaluate` at 441; `build_closure` call at ~423), `python/src/beliefs/evaluation.py` (`gather` at 210–340; `evaluate_over_traced` at 343–386; imports), `python/src/beliefs/verification.py` (docstring lines 9–13), `docs/designs/2026-09-12-composite-claims-design.md` (limitation 16, a dated note)
- Modify (the contract edits, spec §8.5): `python/tests/test_belief.py` (`scenario`, every `evaluate(`/`evaluate_traced(` call), `test_evaluation.py`, `test_composite_reading.py`, `test_deletion_rows.py`, `test_world_view.py` (`world_kwargs`), `test_reproduction_driver.py`, `verification_fixtures.py`, `domain_facet_fixtures.py` (`kwargs_for`), `acceptance/test_deletion_acceptance.py`, `acceptance/test_confinement_acceptance.py`, `acceptance/test_world_view_acceptance.py`, `acceptance/test_n2_cut5.py` (the C4/C5/C6 checks call `evaluate` with `**kwargs`)
- Test: `python/tests/test_standing_read.py` (extended), `python/tests/test_world_standing.py` (new), `python/tests/test_composite_reading.py` (one test), `python/tests/test_retract.py` (one test)

**Interfaces:**
- Consumes: Task 1's fold, enumeration and errors; Task 2's view methods; Task 3's `retire`, `absences`.
- Produces: `SuppliedContext(snapshot, producer_snapshot_identity, node_corpus, pins)`; `evaluate_traced(*, proposition, records, availability, context, retractions, binding, profile)` and `evaluate(...)` likewise; `gather` returning `EvaluationInputs` with the derived `retractions` (input-scoped) and the retired `snapshot`.

- [x] **Step 1: `SuppliedContext`, `evaluate_traced`, `evaluate`**

In `belief.py`: delete the `retractions: RetractionEnumeration` field from `SuppliedContext` (line 231) and its mention in the class docstring; `evaluate_traced` and `evaluate` each gain a keyword-only parameter `retractions: RetractionEnumeration,` after `context`; `evaluate` passes it through; the `build_closure(...)` call in step 9 passes `retractions=retractions`. `RetractionEnumeration` stays imported (it is now a parameter type).

- [x] **Step 2: The contract edits and the two read prerequisites**

Three migrations, then the mechanical pass. They are edits to test fixtures only, and the green checkpoint for them is at the end of Step 4 (the suite cannot be green between Step 1 and the new `gather`).

*Manifests.* `ReadView.corpus_id` reads a manifest, and `domain_facet_fixtures.seed`'s `Path` branch raw-writes none (reproduced: `ManifestMissing`). In `seed`, after `corpus.mkdir(...)`, write one exactly as `test_world_build.corpus_at` does — `(corpus / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, LOCAL_CORPUS_ID, PINS)))` with `from fixtures_cut6 import PINS`, `from beliefs.world import registry`, and a module constant `LOCAL_CORPUS_ID = "c1" + "0" * 30` (32 lower-hex characters, so the local coverage reads `("c1000…",)`). If `ReadView.get`'s base-pin check then refuses reads under `profile_with()` (`_require_base_pin`), build the manifest's pins from `pins_for(profile_with())` instead of `PINS` and record which in a task note. Every other raw-written corpus a test reads through `gather`/`evaluate_over` gets the same line (grep: `raw_write(` in `test_deletion_rows.py`, `verification_fixtures.py`, `test_evaluation.py`, `test_composite_reading.py`; the acceptance modules use `durable_writer`, which adopts one). A fixture whose *point* is a manifest-less corpus (`grep -rn "ManifestMissing" python/tests`) keeps it and asserts the refusal.

*The producer identity on world reads.* `gather` now refuses a supplied `producer_snapshot_identity` that is not the bound epoch's, and every world-read site inherits `"producer-snapshot-1"` from `kwargs_for` (reproduced). In `test_world_view.world_kwargs` set `producer_snapshot_identity=view.producer_snapshot_identity()` in the `replace(...)`; grep `producer-snapshot-1` across `python/tests` (nine files: `domain_facet_fixtures.py`, `test_belief.py`, `test_closure.py`, `test_composite_reading.py`, `test_deletion_rows.py`, `test_evaluation.py`, `verification_fixtures.py`, `acceptance/test_deletion_acceptance.py`, `acceptance/test_durable_records.py`) and at each site that evaluates over a `WorldReadView`, replace the placeholder with the view's; corpus-local sites keep it (a corpus-local read has no epoch to check against).

*The enumeration.* Mechanical, one pass: everywhere a `SuppliedContext(` is constructed with `retractions=`, delete that argument; everywhere `evaluate(` or `evaluate_traced(` is called, add `retractions=`. The two fixture builders make most of it one edit each: in `test_belief.scenario`, delete `retractions=` from the context and add `"retractions": RetractionEnumeration(found=(), coverage=("c1",))` to `kwargs` (and `retractions: RetractionEnumeration` to `_Scenario`); in `domain_facet_fixtures.kwargs_for`, delete `retractions=` from the context and add `"retractions": RetractionEnumeration(found=(), coverage=("c1",))` to the returned dict — callers that pass `**kwargs_for(...)` to `evaluate` now carry it, and callers that pass it to `gather`/`evaluate_over` must drop the key (`{k: v for k, v in kwargs.items() if k != "retractions"}`) — write a helper `over_kwargs(kwargs)` in `domain_facet_fixtures.py` that does that and use it at every `gather(`/`evaluate_over(`/`evaluate_over_traced(` site. `test_world_view.world_kwargs` loses its `retractions=replace(...)` line. `acceptance/test_world_view_acceptance.py:343` loses the same. `test_reproduction_driver.py` and the reproduction driver's `context()` (Task 6 finishes the driver; here only what the test imports). No green checkpoint here: `gather` still constructs `EvaluationInputs(retractions=context.retractions)` until Step 4 rewrites it. Tests whose assertions pinned `coverage == ("c1",)` on a corpus-local closure now read `(LOCAL_CORPUS_ID,)`; update them as they surface in Step 4's run.

- [x] **Step 3: The failing tests for `gather`**

Append to `python/tests/test_standing_read.py`:

```python
from dataclasses import replace

from domain_facet_fixtures import kwargs_for, over_kwargs, profile_with, seed

from beliefs.admission import Admitted, AdmissionRefused, admit
from beliefs.belief import Belief, NoBelief, evaluate
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED, lifecycle_state
from beliefs.errors import ProducerSnapshotMismatch, RetractionUnreadable
from beliefs.evaluation import evaluate_over, evaluate_over_traced, gather
from beliefs.lineage import LineageSnapshot


def seeded(tmp_path, *, outcomes=("supported", "refuted")):
    """The domain-facet scenario in a writer-adopted corpus: `assessment:a-1`
    (`run:run-a` over `dataset:d-a`) and `assessment:a-2` (`run:run-b` over
    `dataset:d-b`), each carrying one clean-environment pass (`verification:v-1`,
    `verification:v-2`), both roots basisless so the pair certifies independent.
    `outcomes` is the one knob this slice adds to `seed` (a second parameter,
    default `("supported", "supported")` so every existing caller is unchanged):
    with a-2 refuting, the baseline belief is 0 and subtracting a-1 moves it to
    -1 — cut 5's C4 arithmetic through `evaluate_over` instead of a test-side
    filter."""
    profile = profile_with()
    writer = CorpusWriter(tmp_path / "scratch", DefaultExecutor, authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    seed(writer, axis="rows", outcomes=outcomes)
    return writer, profile


def fresh(writer) -> ReadView:
    """A view opened after the last write — a raw write past the boundary is
    not in the writer's index, and the writer's view would not find it."""
    return ReadView.opened_at(writer.root)


def gathered(writer, profile, view=None):
    view = view or fresh(writer)
    kwargs = over_kwargs(kwargs_for(view, profile))
    return kwargs, gather(view, "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})


A1, A2, V1, V2 = "assessment:a-1", "assessment:a-2", "verification:v-1", "verification:v-2"


class TestSubtractionAtTheRead:
    def test_a_retracted_assessment_leaves_the_read_set_before_decoding(self, tmp_path):
        writer, profile = seeded(tmp_path)
        _kwargs, baseline = gathered(writer, profile)
        retraction = writer.retract(retracts(writer.read_view.get(A1), "t1"))
        _kwargs, after = gathered(writer, profile)
        gone = {a.identity() for a in baseline.assessments} - {a.identity() for a in after.assessments}
        assert len(gone) == 1
        assert ("retraction", retraction.id) in after.read_trace
        assert not any(kind == "assessment" and ref in gone for kind, ref in after.read_trace)
        assert ("retraction", retraction.id) in after.declared_refs()
        assert after.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
        assert after.retractions.coverage == (writer.corpus_id,)
        assert after.closure().digest() != baseline.closure().digest()

    def test_a_counter_retraction_returns_the_assessment_with_a_third_digest(self, tmp_path):
        writer, profile = seeded(tmp_path)
        a = gathered(writer, profile)[1].closure().digest()
        first = writer.retract(retracts(writer.read_view.get(A1), "t1"))
        b = gathered(writer, profile)[1].closure().digest()
        counter = writer.retract(retracts(first, "t2"))
        _kwargs, after = gathered(writer, profile)
        assert len(after.assessments) == 2
        assert dict(after.retractions.found) == {first.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
        assert len({a, b, after.closure().digest()}) == 3

    def test_the_answer_moves_through_evaluate_over_with_no_test_side_filter(self, tmp_path):
        writer, profile = seeded(tmp_path)  # a-1 supports, a-2 refutes: 0
        kwargs, _inputs = gathered(writer, profile)
        before = evaluate_over(fresh(writer), "proposition:p", **kwargs)
        writer.retract(retracts(writer.read_view.get(A1), "t1"))
        kwargs, inputs = gathered(writer, profile)
        after = evaluate_over(fresh(writer), "proposition:p", **kwargs)
        assert isinstance(before, Belief) and isinstance(after, Belief)
        assert before.value == 0 and after.value == -1
        assert inputs.closure().digest() == after.belief_input_digest

    def test_a_supplied_enumeration_is_a_type_error_and_a_pre_retired_snapshot_refuses(self, tmp_path):
        writer, profile = seeded(tmp_path)
        kwargs = kwargs_for(writer.read_view, profile)
        with pytest.raises(TypeError):
            replace(kwargs["context"], retractions=RetractionEnumeration(found=(), coverage=()))
        snapshot = kwargs["context"].snapshot
        # Construct the forbidden input directly: retire() drops entries for these basisless roots.
        pre = replace(kwargs["context"], snapshot=replace(snapshot, retired={snapshot.roots[0]: ("route:x",)}))
        assert pre.snapshot.retired
        with pytest.raises(MalformedRecord, match="may not pre-retire"):
            gather(writer.read_view, "proposition:p", context=pre, profile=profile, resolution=kwargs["resolution"], binding=kwargs["binding"])

    def test_evaluate_without_retractions_is_a_type_error(self):
        from test_belief import scenario

        kwargs = dict(scenario())
        kwargs.pop("retractions")
        with pytest.raises(TypeError):
            evaluate(**kwargs)
```

(`MalformedRecord` imported from `beliefs.errors`.) Then the verification cases and the unreadable cases:

```python
class TestTheAmendedG8Clause:
    """A retracted verification leaves the read set; `active` recomputes over
    what remains (spec decision 5). Read two ways: the belief value through
    `evaluate_over` (a-1 admitted → 0, a-1 not admitted → -1 with a-2 refuting
    alone) and the gate itself, `admit(assessment, run, observations,
    verifications)`, which answers `Admitted` or `AdmissionRefused`."""

    def _gate(self, writer, profile):
        """The gate's answer, the lifecycle state it rests on (the gate's reason
        does not distinguish `invalidated` from `not-admitted`), and the belief."""
        kwargs, inputs = gathered(writer, profile)
        identity = stored.assessment_reference(writer.read_view.get(A1)).identity()
        a1 = next(a for a in inputs.assessments if a.identity() == identity)
        gate = admit(a1, inputs.runs[a1.run], kwargs["availability"].observations, inputs.verifications)
        state = lifecycle_state(tuple(v for v in inputs.verifications if v.assessment == identity))
        return gate, state, evaluate_over(fresh(writer), "proposition:p", **kwargs)

    def test_retracting_a_false_failure_admits_iff_a_standing_pass_remains(self, tmp_path):
        writer, profile = seeded(tmp_path)  # a-1 carries v-1, a clean-environment pass
        a1 = writer.read_view.get(A1)
        failing = writer.add(verification_for(a1, scope="clean-environment", verdict="failed", slug="fail"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == INVALIDATED and answer.value == -1
        writer.retract(retracts(failing, "false-failure"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, Admitted) and state == ADMITTED and answer.value == 0
        writer.retract(retracts(writer.read_view.get(V1), "false-pass"))  # the only standing pass
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == NOT_ADMITTED and answer.value == -1

    def test_retracting_a_resolution_restores_the_failure_it_named(self, tmp_path):
        writer, profile = seeded(tmp_path)
        a1 = writer.read_view.get(A1)
        failing = writer.add(verification_for(a1, scope="clean-environment", verdict="failed", slug="fail"))
        resolution = writer.add(verification_for(a1, scope="clean-environment", verdict="passed", slug="fix", supersedes=failing.id))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, Admitted) and state == ADMITTED and answer.value == 0
        writer.retract(retracts(resolution, "false-resolution"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == INVALIDATED and answer.value == -1


class TestUnreadableAndAbsent:
    def test_a_stale_target_ref_restamped_is_unreadable(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        node = retracts(writer.read_view.get(A1), "t1")
        node.facets[stored.RETRACTION_FACET]["target"]["ref"] = "assessment:gone"
        node.facets[stored.RETRACTION_FACET]["target"]["resolved"] = "assessment:gone"
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        with pytest.raises(RetractionUnreadable) as refused:
            gathered(writer, profile, fresh(writer))  # a fresh view: the writer's index does not hold a raw write
        assert refused.value.ref == node.id

    def test_a_canonical_retraction_with_wrong_content_identity_is_unreadable(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        target = writer.read_view.get(A1)
        node = stored.retraction_node(
            title="t1",
            target=stored.NodeTarget(target.id, target.id, "sha256:" + "ab" * 32),
            reason="defective-code",
            rationale="the record is invalid",
            grounds=("verification:v1",),
            actor=ACTOR,
            event_token="t1",
        )
        CorpusWriter._validated_retraction(node)  # canonical shape; the target identity check must refuse it
        raw_write(writer.root, node)
        with pytest.raises(RetractionUnreadable, match="content identity"):
            gathered(writer, profile, fresh(writer))

    def test_a_stale_stamp_is_unreadable_too(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        node = retracts(writer.read_view.get(A1), "t1")
        stamped = stored.stamp_semantic_identity(node)
        stamped.facets[stored.RETRACTION_FACET]["rationale"] = "edited after the stamp"
        raw_write(writer.root, stamped)
        with pytest.raises(RetractionUnreadable, match="semantic-hash-stale|stale"):
            gathered(writer, profile, fresh(writer))
```

`AdmissionRefused(assessment, reason)` carries one prefix-stable reason for every verification-state refusal (`not-admitted-verification-state: …`, `admission.py:74`), so the `invalidated`/`not-admitted` distinction is read from `verification.lifecycle_state` over the gathered verifications, as above. `seed` gains `outcomes: tuple[str, str] = ("supported", "supported")` and uses `outcomes[0]`/`outcomes[1]` for a-1/a-2's `outcome=`. `verification_for` is a module-local helper written at the top of the test file, on `test_deletion_rows._verification`'s shape (line 290 there):

```python
def verification_for(assessment, *, scope: str, verdict: str, slug: str, supersedes: str | None = None):
    return stored.verification_node(
        slug,
        title=slug,
        assessment=stored.assessment_reference(assessment).identity(),
        assessment_ref=assessment.id,
        scope=scope,
        verdict=verdict,
        supersedes=supersedes,
    )
```

Create `python/tests/test_world_standing.py`:

```python
"""Standing over a world read: the epoch's enumeration, its scope, coverage,
relocation, absence and the split (correction-remainder slice 1 §6, §8.1)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from domain_facet_fixtures import over_kwargs, profile_with
from test_local_standing import retracts
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent, split_evaluation_world, world_kwargs

from beliefs import stored
from beliefs.belief import Belief, NoBelief
from beliefs.closure import RETRACTION_UPHELD, build_closure
from beliefs.corpus import CorpusWriter
from beliefs.errors import ProducerSnapshotMismatch, RetractionResolutionDisagreement
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.relocation import move
from beliefs.world.view import open_world_view


def writer_at(root: Path, profile) -> CorpusWriter:
    from nodes.core.write_plan import DefaultExecutor

    return CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile)


def evaluation(world, published, profile):
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile)  # sets producer_snapshot_identity from the view (Step 2)
    inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile, resolution=kwargs["resolution"], binding=kwargs["binding"])
    answer, _admission = evaluate_over_traced(view, "proposition:p", **over_kwargs(kwargs))
    return view, inputs, answer


def support_in(view, corpus_id):
    return next(n for n in view.captured_records(corpus_id) if n.id == "assessment:a-1")


class TestTheEpochsEnumerationReachesBelief:
    def test_a_retraction_in_coverage_subtracts_and_the_closure_carries_the_epochs_member(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        _view, before, _answer = evaluation(world, published, profile)
        alpha = writer_at(roots[ALPHA], profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        rebuilt = publish(world, (ALPHA, BETA), hold_shipped(world))
        view, after, answer = evaluation(world, rebuilt, profile)
        assert len(after.assessments) == len(before.assessments) - 1
        assert after.retractions == replace(view.retraction_enumeration(), found=((retraction.id, RETRACTION_UPHELD),))
        assert isinstance(answer, Belief) and after.closure().digest() == answer.belief_input_digest

    def test_a_supplied_snapshot_identity_that_is_not_the_epochs_refuses(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        context = replace(kwargs["context"], producer_snapshot_identity="producer-snapshot-1")
        with pytest.raises(ProducerSnapshotMismatch):
            gather(view, "proposition:p", context=context, profile=profile, resolution=kwargs["resolution"], binding=kwargs["binding"])


class TestC3Coverage:
    def test_an_uncovered_retraction_moves_nothing_and_the_widening_reaches_it(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        move(alpha, beta, retraction.id)  # the retraction now lives in BETA; its target stays in ALPHA
        narrow = publish(world, (ALPHA,), hold_shipped(world))
        _view, inputs, _answer = evaluation(world, narrow, profile)
        assert inputs.retractions.found == () and inputs.retractions.coverage == (ALPHA,)
        assert len(inputs.assessments) == 2
        wide = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, widened, _answer = evaluation(world, wide, profile)
        assert widened.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
        assert len(widened.assessments) == 1

    def test_the_coverage_declaration_is_a_digest_member_in_isolation(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        _view, inputs, _answer = evaluation(world, published, profile_with())
        narrow = inputs.closure().digest()
        wide = replace(inputs, retractions=replace(inputs.retractions, coverage=(*inputs.retractions.coverage, "9" * 32))).closure().digest()
        assert narrow != wide

    def test_an_in_coverage_move_leaves_the_digest_and_moves_the_receipts(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        target = support_in(open_world_view(world, published), ALPHA)
        alpha.retract(retracts(target, "t1"))
        first = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, before, _answer = evaluation(world, first, profile)
        move(alpha, beta, target.id)
        second = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, after, _answer = evaluation(world, second, profile)
        assert after.closure().digest() == before.closure().digest()
        assert dict(second.coverage) != dict(first.coverage)  # both corpus states moved


class TestAbsence:
    def test_a_found_retraction_in_an_absent_corpus_is_the_absence_answer(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        move(alpha, beta, retraction.id)
        wide = publish(world, (ALPHA, BETA), hold_shipped(world))
        make_absent(roots, BETA)
        _view, inputs, answer = evaluation(world, wide, profile)
        assert inputs.assessments == () and (retraction.id, BETA) in inputs.absent
        assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"


class TestTheSplit:
    def test_a_counter_retraction_moved_away_refuses_the_disagreement(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        first = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        counter = alpha.retract(retracts(first, "t2"))
        together = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, inputs, _answer = evaluation(world, together, profile)
        assert dict(inputs.retractions.found)[first.id] == "overturned"
        move(alpha, beta, counter.id)
        split = publish(world, (ALPHA, BETA), hold_shipped(world))
        assert dict(open_world_view(world, split).retraction_enumeration().found)[first.id] == "upheld"
        with pytest.raises(RetractionResolutionDisagreement) as refused:
            evaluation(world, split, profile)
        assert refused.value.ref == first.id
```

`move(source, destination, ref, *, observer, instrument, opened_at, closed_at)` is `relocation.py:88`'s signature; the four act-report fields are `test_relocation.py`'s `MOVE_FIELDS` — import it (`from test_relocation import MOVE_FIELDS`) and call `move(alpha, beta, ref, **MOVE_FIELDS)` at every site above. `split_evaluation_world(tmp_path, beta_refs=())` puts every seeded record in ALPHA and leaves BETA empty but registered and covered, which is what these fixtures need.

Add to `python/tests/test_composite_reading.py` one test: a composite whose one member's only supporting assessment is retracted reads that member as `NoBelief("no-eligible-assessment")` (or `no-directional-outcome`, whichever the member's remaining evidence yields) through `read_composite` with no filtering — construct it from the module's existing composite fixture, retract the support with `writer.retract(retracts(...))`, and assert the row's answer changed from the pre-retraction read.

Add to `python/tests/test_retract.py` one test beside `test_retract_refuses_a_route_absent_from_the_stamped_basis`: retracting a present route (the module's `stored.RouteTarget(...)` fixture) leaves the dataset's `stored.stored_semantic_hash` and its `lineage-basis` facet equal before and after, and the corpus holds exactly one more record.

Run: `cd python && uv run --frozen pytest tests/test_standing_read.py tests/test_world_standing.py -q`
Expected: FAIL — `gather` still reads retracted records; `ProducerSnapshotMismatch` not raised; `retractions` still the caller's.

- [x] **Step 4: `gather`**

Replace `gather`'s body (evaluation.py 210–340) with the following; the parts that are unchanged from the baseline are marked, and the `assesses`-edge filter is `beliefs-010c6e`'s.

```python
def gather(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
) -> EvaluationInputs:
    """Resolve one proposition's belief inputs from a corpus, tracing each
    value at the moment it is handed out.

    Standing is decided here, before any assessment is read (correction-
    remainder slice 1 §4): the retraction enumeration is the view's — the
    bound epoch's for a world read, the corpus's own fold for a corpus-local
    read — never the caller's; every found retraction is dereferenced and the
    fold recomputed over what it names; a node-arm target of a standing
    retraction is skipped before it is decoded; a route-arm target retires
    its route in the lineage snapshot. Dereferencing a retraction outside the
    closure is a lookup, as decoding every verification to select some is.
    """
    from beliefs.corpus import CorpusWriter, local_retraction_enumeration
    from beliefs.world.view import WorldReadView

    world = isinstance(view, WorldReadView)
    if world and context.node_corpus:
        raise MalformedRecord(
            "node_corpus is derived from a world read and must be supplied empty; a caller may not relocate a record"
        )
    if context.snapshot.retired:
        raise MalformedRecord("a supplied lineage snapshot carries no retirement; a caller may not pre-retire a route")
    if world:
        bound = view.producer_snapshot_identity()
        if context.producer_snapshot_identity != bound:
            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)
    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)

    # --- standing, before any assessment is read ------------------------------
    absent: list[tuple[str, str]] = []
    trace: list[ReadRef] = []
    facets: dict[str, Mapping[str, object]] = {}
    for ref, _recorded in enumeration.found:
        try:
            corpus_id = _absence_of(view, ref)
            if corpus_id is not None:
                absent.append((ref, corpus_id))
                continue
            node = view.get(ref)  # a lookup; traced below only if the closure carries it
            facet = CorpusWriter._validated_retraction(node)
            target = cast(Mapping[str, str], facet["target"])
            target_ref = target["ref"] if target["arm"] == "node" else target["dataset"]
            corpus_id = _absence_of(view, target_ref)
            if corpus_id is not None:
                absent.append((target_ref, corpus_id))
                continue
            CorpusWriter._resolve_retraction_target(node, view)  # exact resolution, content identity, route presence
        except (ScienceError, RefError) as caught:
            raise RetractionUnreadable(ref, str(caught)) from caught
        facets[ref] = facet
    if absent:
        return _absent_inputs(proposition, context, enumeration, tuple(sorted(set(absent))), tuple(trace), binding, world)
    standing = retraction_standing(view, facets)
    for ref, recorded in enumeration.found:
        computed = RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED
        if computed != recorded:
            raise RetractionResolutionDisagreement(ref, recorded, computed)
    subtracted: set[str] = set()
    retired: dict[str, set[str]] = {}
    for ref, facet in facets.items():
        if not standing[ref]:
            continue
        target = cast(Mapping[str, str], facet["target"])
        if target["arm"] == "node":
            subtracted.add(target["resolved"])
        else:
            retired.setdefault(target["resolved"], set()).add(target["route_identity"])

    attribution: dict[str, set[str]] = {}
    matched: list[AssessmentValue] = []
    proposition_refs: list[str] = []
    visited: set[str] = set()  # this proposition's assessment ids, subtracted included (decision 10)
    for node in view.iter_stored():
        if node.kind != "assessment":
            continue
        # beliefs-010c6e: membership by the `assesses` edge, before any decode.
        targets = [r.target for r in node.relations if r.predicate == stored.ASSESSES]
        wanted = view.resolve(proposition) or proposition
        if not any((view.resolve(target) or target) == wanted for target in targets):
            continue  # a lookup, not a value handed out — membership by the edge, never by decoding
        visited.add(node.id)
        if node.id in subtracted:
            continue  # a standing retraction names it: a lookup, never decoded
        value = stored.assessment_value(node, profile=profile)
        if value.proposition != proposition:
            raise MalformedRecord(
                f"{node.id}: the assesses edge names {proposition!r} but the facet names {value.proposition!r}"
            )
        matched.append(value)
        if world:
            corpus_id = view.corpus_of(node.id)
            assert corpus_id is not None  # A served record has a location in this epoch.
            attribution.setdefault(value.identity(), set()).add(corpus_id)
        trace.append(("assessment", value.identity()))
        proposition_refs.extend(targets)
    ids = frozenset(a.identity() for a in matched)

    # --- runs and observed facets: unchanged from the baseline ------------------
    runs: dict[str, RunValue] = {}
    observed: dict[tuple[str, str, str], FacetRead] = {}
    for a in matched:
        ...  # the baseline's loop, verbatim (lines 245–279)
    snapshot = retire(context.snapshot, retired)
    absent.extend((entry.ref, entry.corpus_id) for entry in absences(snapshot))
    rows = tuple(observed[key] for key in sorted(observed))

    verifications: list[Verification] = []
    verification_ids: set[str] = set()
    for node in view.iter_stored():
        if node.kind != "verification":
            continue
        names = {r.target for r in node.relations if r.predicate == stored.VERIFIES}
        if not any(view.resolve(name) in visited for name in names if view.resolve(name) is not None):
            continue  # membership by the `verifies` edge, never by decoding (decision 10)
        verification_ids.add(node.id)
        if node.id in subtracted:
            continue  # the amended G8 clause (§7a): it leaves the read set; `active` recomputes over what remains
        value = stored.verification_value(node)
        if _verification_selected(value, ids):
            verifications.append(value)
            trace.append(("verification", value.ref))

    # --- the closure's enumeration: this proposition's inputs, transitively (decision 10)
    scope = visited | verification_ids | set(snapshot.bases)
    taken: set[str] = set()
    grew = True
    while grew:
        grew = False
        for ref, facet in facets.items():
            if ref in taken:
                continue
            target = cast(Mapping[str, str], facet["target"])
            if target["resolved"] in scope or target["resolved"] in taken:
                taken.add(ref)
                grew = True
    scoped = RetractionEnumeration(
        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),
        coverage=enumeration.coverage,
    )
    trace.extend(("retraction", ref) for ref, _recorded in scoped.found)

    # --- the claim, consulted, attribution: unchanged from the baseline ----------
    claim: Claim | None = None
    for ref in dict.fromkeys(proposition_refs):
        ...  # verbatim (lines 292–306)
    ledger: dict[str, list[str]] = {}
    ...  # verbatim (lines 308–322)
    return EvaluationInputs(
        proposition=proposition,
        assessments=tuple(matched),
        runs=runs,
        verifications=tuple(verifications),
        snapshot=snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=scoped,
        consulted=consulted,
        binding=(binding.rule, binding.implementation),
        claim=claim,
        read_trace=tuple(trace),
        observed_facets=rows,
        absent=tuple(sorted(set(absent))),
        node_corpus=MappingProxyType(dict(node_corpus)),
    )
```

Two things about that body. The `...  # verbatim` markers stand for the baseline's own lines, copied without change — the runs/observed loop (245–279), the claim loop (292–306) and the ledger/consulted block (308–322); nothing in them changes. The verification membership test resolves the `verifies` target through `view.resolve` so a deprecated id still matches (`stored.VERIFIES` is `"verifies"`, `stored.py:234`); a verification whose `verifies` names an assessment of another proposition is not this closure's, as before.

The early return on absence (decision 4, spec §4):

```python
def _absent_inputs(
    proposition: str,
    context: SuppliedContext,
    enumeration: RetractionEnumeration,
    absent: tuple[tuple[str, str], ...],
    trace: tuple[ReadRef, ...],
    binding: PolicyBinding,
    world: bool,
) -> EvaluationInputs:
    """No selection runs over a partial fold: an `EvaluationInputs` whose only
    content is the absence, which `evaluate_over_traced` answers as
    `unavailable-corpus-absent`."""
    return EvaluationInputs(
        proposition=proposition,
        assessments=(),
        runs={},
        verifications=(),
        snapshot=context.snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=RetractionEnumeration(found=(), coverage=enumeration.coverage),
        consulted=(),
        binding=(binding.rule, binding.implementation),
        claim=None,
        read_trace=trace,
        observed_facets=(),
        absent=absent,
        node_corpus=MappingProxyType({} if world else dict(context.node_corpus)),
    )
```

Check `EvaluationInputs.__post_init__` (if any) admits `consulted=()`; if it requires a non-empty tuple, pass what `consulted_contracts` returns for an empty closure — read `consulted.py:49–61`: it raises on no corpora, so `()` is the honest value here, and the guard must not run on the absence path.

`evaluate_over_traced` (343–386): replace `context = replace(context, node_corpus=inputs.node_corpus)` and the call with

```python
    context = replace(context, node_corpus=inputs.node_corpus, snapshot=inputs.snapshot)
    return evaluate_traced(
        proposition=proposition,
        records=inputs.records(),
        availability=availability,
        context=context,
        retractions=inputs.retractions,
        binding=binding,
        profile=profile,
    )
```

and add `except RetractionUnreadable as exc: return Refused(f"retraction-unreadable: {exc}"), NotReached()` and `except RetractionResolutionDisagreement as exc: return Refused(f"retraction-resolution-disagreement: {exc}"), NotReached()` beside the existing `except` arms **only if** the spec's tests expect a `Refused` — they expect the exception (`pytest.raises`), so do **not** add those arms; a `RecordError` propagates as `MalformedRecord` does today.

Imports in `evaluation.py`: `RefError` from `nodes.core.errors`; `cast` from `typing`; `from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, Closure, RetractionEnumeration, build_closure`; `from beliefs.corpus import ReadView, _absence_of, retraction_standing, run_value`; `from beliefs.errors import (..., ProducerSnapshotMismatch, RetractionResolutionDisagreement, RetractionUnreadable, ScienceError)`; `from beliefs.lineage import LineageSnapshot, absences, retire`. `CorpusWriter` and `local_retraction_enumeration` are imported inside `gather` as `WorldReadView` is (the module-level import of `CorpusWriter` may be a cycle; try the module level first and fall back to the function-local import if it is).

`verification.py` docstring, lines 9–13: replace with

> "Active" here means **not superseded by a later verification that explicitly references it**. The amended definition (correction-lifecycle §7a) also excludes targets of a standing retraction; that clause lives at the read — `evaluation.gather` drops a retracted verification from the read set before it is decoded, so a retracted resolution no longer supersedes the failure it named — and this module computes over what the read handed out (correction-remainder slice 1, decision 5).

`docs/designs/2026-09-12-composite-claims-design.md`, under limitation 16 in §13: append a dated line — "*Discharged 2026-09-16 by correction-remainder slice 1 (`../superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md`, decision 5): `gather` subtracts a retracted assessment or verification before decoding, and the identification column inherits it through `evaluate_over_traced` with no change of its own.*"

Run: `cd python && uv run --frozen pytest tests/test_standing_read.py tests/test_world_standing.py tests/test_composite_reading.py tests/test_retract.py tests/test_belief.py tests/test_evaluation.py tests/test_world_view.py tests/test_deletion_rows.py tests/test_local_standing.py -q`
Expected: PASS — this is the green checkpoint Step 2 deferred: every test that passed at the baseline passes here with an identical answer, except assertions that pinned the old coverage literal or a projection literal (updated as they surface). Then `just test-fast` green.

- [x] **Step 5: Commit**

```bash
tasks check
git add python/src/beliefs/belief.py python/src/beliefs/evaluation.py python/src/beliefs/verification.py python/tests docs/designs/2026-09-12-composite-claims-design.md
git commit -m "feat(evaluation): standing reaches the evaluator — derived enumeration, subtraction at the read, retirement, the handoff (C7, C3, BI-1..BI-5)"
tasks done beliefs-010c6e "gather filters assessments by their assesses edge before decoding; verifications by their verifies edge"
```

(`tasks done` writes the task record; amend it into the same commit: `git add tasks && git commit --amend --no-edit`.)

---

Task 4 executed 2026-09-17: derived enumeration and retirement reach the
read wrapper, with all caller migrations and the edge-selection rider.
Static `just test-fast`: 4945 passed, 2 skipped; focused evaluator/guard checks
and 46 durable migration checks passed. Live cut18 M1 and cut32 U4-a were
retargeted after measured drift and independently returned baseline
`resolved` / mutation `sound`; frozen declarations remain unchanged.

### Task 5: The riders — audit_world's spec-target check, total estimand sets, the composite tidy

**Files:**
- Modify: `python/src/beliefs/audit.py` (`_recompute` at 518–531), `python/src/beliefs/contract/base.py` (the `EstimandGrammar(...)` construction at 384–389), `python/src/beliefs/decode.py` (the `if kind == "levels": ... else:` at 389), `python/src/beliefs/estimand.py` (`check_estimate`/`check_uncertainty` at 383–404 and the `measure.scale` branch at 207), `python/src/beliefs/composite.py`, `python/src/beliefs/corpus.py` (`_refuse_composite`)
- Test: `python/tests/test_world_audit.py`, `python/tests/test_base_contract.py`, `python/tests/test_estimand.py` (or the module that tests `decode`'s wire estimand), `python/tests/test_composite.py`, `test_belief.py`, `test_evaluation.py`

**Interfaces:**
- Produces: `audit_world` reports `spec-target-contradicted`; `MalformedContract` at parse for a closed set not exactly the implemented tags; `estimand.SUPPORTED_CONTRAST_KINDS`, `SUPPORTED_SCALES`, `SUPPORTED_UNCERTAINTY_KINDS`.

- [x] **Step 1: `beliefs-0521da` — the failing test**

In `python/tests/test_world_audit.py`, beside the existing spec test (`grep -n "analysis-spec\|spec-" python/tests/test_world_audit.py`), add a test that seeds a world with a raw-written `analysis-spec` whose estimand names a different claim identity than its target proposition carries (the fixture `test_audit.py` uses for `spec-target-contradicted` under `audit_corpus` — reuse its builder), publishes an epoch over it, runs `audit_world`, and asserts one `Finding` with `code == "spec-target-contradicted"` for that ref.

Run: `cd python && uv run --frozen pytest tests/test_world_audit.py -q -k spec_target`
Expected: FAIL — no such finding.

- [x] **Step 2: `beliefs-0521da` — the line**

In `audit._recompute`, replace `return check_analysis_spec(node, profile=profile)` with

```python
    if node.kind == "analysis-spec":
        check_analysis_spec(node, profile=profile)  # restores, or raises as before
        return check_spec_target(view, node, profile=profile)
```

Run the test: PASS. Commit: `git commit -m "fix(audit): audit_world runs check_spec_target so spec-target-contradicted is reachable in the world audit"` with `tasks done beliefs-0521da "..."` amended in.

- [x] **Step 3: `beliefs-1dd03f` — the failing tests**

In `python/tests/test_base_contract.py`, add three tests that parse the shipped base document with one closed set widened (`contrast_kinds: [levels, continuous, ordinal]`; `scales: [additive, multiplicative, log]`; `uncertainty_kinds: [interval, standard-error, credible]`) and assert `MalformedContract` naming the unoperable tag (`match="ordinal"` etc.); and one that narrows a set (`scales: [additive]`) and asserts `MalformedContract` too (a set the kernel implements more of is not the contract's set either — "exactly the tags the kernel implements"). In the module that tests `decode`'s wire estimand, add a test that a wire contrast with `kind` in the grammar but not `levels`/`continuous` cannot arise (the grammar refuses first), and in `test_estimand.py` a test that `check_estimate(Decimal("1"), "log")` raises `MeasureRefused` (or the module's scale-refusal class) rather than passing as additive.

Run: FAIL.

- [x] **Step 4: `beliefs-1dd03f` — the sets**

In `estimand.py`, near the top:

```python
SUPPORTED_CONTRAST_KINDS: tuple[str, ...] = ("continuous", "levels")
SUPPORTED_SCALES: tuple[str, ...] = ("additive", "multiplicative")
SUPPORTED_UNCERTAINTY_KINDS: tuple[str, ...] = ("interval", "standard-error")
"""The three closed sets this implementation operates. A base contract declares
each set and the parser refuses a declaration that is not exactly one of
these (beliefs-1dd03f): a widened set would be accepted and silently
mis-interpreted by the dispatches below, and a narrowed one would declare
less than the kernel does."""
```

In `contract/base.py`, after the `EstimandGrammar(...)` construction:

```python
    for name, declared, supported in (
        ("contrast_kinds", estimand_grammar.contrast_kinds, SUPPORTED_CONTRAST_KINDS),
        ("scales", estimand_grammar.scales, SUPPORTED_SCALES),
        ("uncertainty_kinds", estimand_grammar.uncertainty_kinds, SUPPORTED_UNCERTAINTY_KINDS),
    ):
        if set(declared) != set(supported):
            unoperable = sorted(set(declared) ^ set(supported))
            raise MalformedContract(
                f"{estimand_where}: {name} declares {sorted(declared)}, not the set this implementation operates "
                f"{sorted(supported)}; {unoperable} is not operable here (a later grammar version arrives with its "
                "interpretation, never ahead of it)"
            )
```

(import the three from `beliefs.estimand`; if that import is circular — `estimand.py` importing `contract`? check with `grep -n "^from beliefs" python/src/beliefs/estimand.py` — place the three constants in `contract/base.py` beside `SUPPORTED_SHAPES` instead and import them into `estimand.py`.) In `decode.py` at 389, `else:` becomes `elif kind == "continuous":` with a trailing `else: raise MalformedWireEstimand(f"contrast.kind {kind!r} is declared but not operable")`. In `estimand.py`, wherever `scale == "multiplicative"` is tested with additive as the implicit else (lines 207, 385, 399), add first `if scale not in SUPPORTED_SCALES: raise <the function's refusal class>(f"scale {scale!r} is not operable")` — one guard at the top of `check_estimate` and `check_uncertainty`, and one before line 207's test. The TypeScript parser (`ts/src/contract.ts`) reads the same document; add the same exactness check there (`grep -n "estimand_grammar\|contrast_kinds" ts/src/contract.ts`) and a vitest case in `ts/tests/declarations.test.ts` mirroring the widened-set refusal, so both implementations refuse the same document (the parity the `contract-cut` will freeze).

Run: `cd python && uv run --frozen pytest tests/test_base_contract.py tests/test_estimand.py tests/test_decode.py -q` and `cd ts && npm test -- declarations` green; then `just test-fast`. Commit: `git commit -m "fix(contract): the estimand grammar's three closed sets are exactly the operable tags, in both implementations"` with `tasks done beliefs-1dd03f "..."`.

- [x] **Step 5: `beliefs-b1245d` — the composite tidy**

Read the task body (`tasks show beliefs-b1245d --pretty`) — it is the list. Each item, in order, with the tests that pin it:

1. The relations-count/order check inlined in `audit.check_composite` and `corpus._refuse_composite`: fold into one helper `composite.check_composes_relations(node, facet) -> str | None` (returns the refusal text or `None`) beside `classify`; both callers call it. Tests: the existing U6-b/U7 tests still pass.
2. The node-outcome loop duplicated between `build_composite` and `read_composite` with differing refusal text: one private `_member_outcomes(...)` used by both; the refusal text becomes one string (update the one test that matched the other).
3. The four `NotReached` arms asserted only through the answer: in `test_composite_reading.py`, assert `admission` is `NotReached()` for each of fixtures-unheld, fixture failure, gather exception, corpus-absent.
4. The tautological first-projection tests in `test_belief.py` and `test_evaluation.py`: add a one-line comment above each — "P1–P9 carry the proof that the first projection is the answer; this pins only that the tuple's first member is what `evaluate` returns."
5. `check_composite` returning `_unchecked` on the first absent-corpus member: continue past absent members and report a dangling sibling when its corpus is present (`test_audit.py`: a composite with one absent member and one dangling member reports the dangling one).
6. `_refuse_cycle`'s recursion → the iterative DFS `corpus._acyclic_postorder` already spells (reuse it, or an iterative copy in `composite.py` if importing `corpus` is a cycle).
7. The unconditional `skip` in `test_composite.py`: remove it or give it a real condition.
8. `audit.py`'s function-scope `_absence_of` import (line 348) → module level.

Every U8 `before` string in `python/tests/n2_arms_cut32.py` must still occur exactly once: after the edits run `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut32.py::test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable -q`; a pinned line the tidy moved is re-targeted in the **live** guard by the `RETARGETED_ROWS` mechanism, never in `n2_arms_cut32.py` (frozen), and noted on the task.

Run `just test-fast` green. Commit: `git commit -m "refactor(composite): one relations check, one member-outcome loop, iterative cycle refusal, the NotReached arms asserted"` with `tasks done beliefs-b1245d "..."`.

---

### Task 6: The reproduction re-derives under the derived enumeration

**Files:**
- Modify: `python/tools/reproduction/belief.py` (`context()` at 47–54), `docs/designs/2026-09-05-mm30-reproduction.md` (append §12)
- Test: `python/tests/test_reproduction_driver.py` (already green from Task 4 if it imports `context`)

**Interfaces:**
- Consumes: Task 4's `SuppliedContext`.
- Produces: `state.json` on the certified corpus with a fresh `rederived_belief`, `rederived_equal`; record §12.

- [x] **Step 1: The driver**

In `python/tools/reproduction/belief.py`, `context()` loses `retractions=RetractionEnumeration(found=(), coverage=(st["corpus_id"],))` and the `RetractionEnumeration` import. The docstring line above it ("supplied: this exercise builds no epoch") stays for the snapshot identity.

- [x] **Step 2: Re-derive in a fresh process**

`paths.py` resolves "the main checkout" through the worktree's **real** path, which on this host is under `WORK_ROOT` (`/mnt/ssd3/work/beliefs/.worktrees/…`), so its default lands beside the WORK_ROOT parent where no `state.json` exists (`beliefs-51ffdf` records the defect). Set the root explicitly to the existing corpus: `export SCIENCE_MM30_ROOT=/mnt/ssd/Dropbox/beliefs/.work/reproduction/mm30` and confirm `test -f "$SCIENCE_MM30_ROOT/state.json"` before either command. Then from `python/`: `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight` (it must say `ok`; on a refusal for host load, `tasks park <task> "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`), then `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`. Read `state.json`: `rederived_belief` is the same `NoBelief` payload as before (`no-directional-outcome` per record §10/§11 — read the prior value from the file before running and quote both), `rederived_equal` is `true`. Nothing is minted and nothing is moved aside: no contract succeeded, so the corpus is not recreated (the plan's correction to spec §10).

- [x] **Step 3: §12**

Append to `docs/designs/2026-09-05-mm30-reproduction.md`:

```markdown
## 12. Addendum — standing reaches the evaluator, 2026-09-16

Re-run under correction-remainder slice 1 (`../superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md`; cut 33). No contract succeeded, so the corpus was neither recreated nor moved aside: `.work/reproduction/mm30` is the cut-32 state, read in place, and `mm30.cut22` / `mm30.cut31` are untouched.

### 12.1 What changed in the driver

Step 8 and step 10a no longer supply a retraction enumeration. `SuppliedContext` has no such member: `gather` derives it from the corpus — every stored retraction with its folded resolution, under the manifest's corpus id as coverage — and hands it to the evaluator on `EvaluationInputs` (slice 1 decisions 1 and 10). The producer-snapshot identity stays supplied (`no-epoch-published`; no epoch is built here) and is the one member of the context this exercise still declares rather than reads.

### 12.2 What the re-run reached

`reproduction.rederive`, 2026-09-16, in a fresh process: `rederived_belief` = `<the payload, quoted>`, equal to the recorded step-8 answer (`rederived_equal: true`). The corpus holds no retraction, so the derived enumeration is `found=()`, `coverage=(<corpus id>,)` — byte for byte the declaration the driver used to supply, now computed. The answer is a `NoBelief` and carries no `belief_input_digest`, so the slice's projection change (`retired` and `identity` on every lineage basis) moves no pinned digest here; it is measured by `test_lineage.py` and the cut's C7 arms, not by this corpus.

### 12.3 What this addendum does not claim

That a retraction in the mm30 corpus would subtract: none exists, and minting one is the dogfood's work, not the reproduction's. That the answer would survive an epoch: none is built. The transition measured is the driver's supplied member becoming a derived one with the same value.
```

Fill the two `<…>` from `state.json` before committing. Run `cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q` green.

```bash
tasks check
git add python/tools/reproduction/belief.py docs/designs/2026-09-05-mm30-reproduction.md
git commit -m "docs(reproduction): re-derive under the derived enumeration; addendum §12"
```

---

### Task 7: Acceptance, the N2 declaration, the guard and the runner

**Files:**
- Create: `python/tests/acceptance/test_correction_acceptance.py`, `python/tests/n2_arms_cut33.py`, `python/tests/acceptance/n2_arms_cut33.py` (the re-export shim, on `acceptance/n2_arms_cut32.py`'s shape), `python/tests/acceptance/test_n2_cut33.py`, `python/tools/cut33_acceptance.py`

**Interfaces:**
- Consumes: the frozen cut document and `CUT33_FREEZE_COMMIT` (Task 0); every module above.
- Produces: C7-a..c, C3-a..b, C10-a, BI-1..5 discharged on the certified volume; the guard pinning the freeze commit, the cut document's SHA-256 and the declaration's SHA-256.

- [ ] **Step 1: The acceptance module**

`python/tests/acceptance/test_correction_acceptance.py`, one test per declaration unit, over the `durable_writer` fixture (`acceptance/conftest.py`; `TESTING_PROFILE`) for the corpus-local units and a durable world (the `durable_root`-shaped world the cut-23 module `test_world_view_acceptance.py` builds; reuse its helpers) for the C3 units. Each test is the unit test of Task 4 re-composed over the durable root, named exactly as `UNIT_CHECKS` names it:

- `test_c7a_retiring_one_conflicting_route_certifies_over_the_survivor` — a dataset with a stamped two-route conflict basis (the shape `test_retract.py`'s route fixture stamps, two routes with identities `route:one`, `route:two`, distinct ancestors both held), an assessment observing it, a second assessment over a disjoint dataset; `evaluate_over` before: the pair is edged (not independent); `retract` the `route:one` arm; after: the closure's `lineage.divergence[<dataset>] == "undiverged"` and `bases[<dataset>].retired == ["route:one"]`, and the pair certifies `independent` (read the certification through the belief value's change under `BELIEF_V1`, or through `certify(inputs.snapshot, roots_a, roots_b)` over the gathered snapshot — assert both).
- `test_c7b_retiring_every_route_is_not_certified_with_lineage_incomplete` — continue: retract `route:two`; `certify(...)` over the gathered snapshot is `not-certified` with `lineage-incomplete` and without `lineage-divergent`.
- `test_c7c_the_stored_basis_is_byte_unchanged_and_retract_writes_one_record` — the dataset's markdown bytes on disk and `stored_semantic_hash` equal before and after each `retract`; the record count grows by exactly one per call.
- `test_c3a_an_uncovered_retraction_moves_nothing_and_coverage_is_a_digest_member` — the `move` fixture of `test_world_standing.py::TestC3Coverage` (both halves) over the durable world.
- `test_c3b_an_in_coverage_move_leaves_the_digest_and_moves_the_receipts` — likewise.
- `test_c10a_raw_written_refused_shapes_are_reported_by_both_audits` — raw-write four retractions (node arm naming a `note`-kind record, a `proposition`, a `run`; route arm naming a route absent from the basis) past the boundary with `fixtures_cut4.raw_write`; `audit_corpus` and `audit_world` each report `retraction-target-invalid` for each of the four refs.
- `test_bi1_node_standing_subtracts_at_the_read` — `test_standing_read.py::TestSubtractionAtTheRead::test_the_answer_moves_through_evaluate_over_with_no_test_side_filter` over the durable writer.
- `test_bi2_a_retracted_verification_leaves_the_read_set` — the three cases of `TestTheAmendedG8Clause` through `evaluate_over` and `admit`.
- `test_bi3_the_enumeration_is_the_views_and_input_scoped` — over the durable world: a standing retraction against `proposition:p`'s assessment **and** one against an unrelated proposition's assessment (seed a second proposition with its own assessment); `gather` for `proposition:p` carries exactly the first in `found` with the epoch's resolution; the unrelated proposition's digest is unchanged by the first retraction (gather it before and after); `SuppliedContext(retractions=...)` is a `TypeError`.
- `test_bi4_an_unreadable_found_retraction_refuses` — the three unreadable shapes.
- `test_bi5_a_resolution_disagreement_refuses` — `TestTheSplit` over the durable world.

- [ ] **Step 2: The declaration file**

`python/tests/n2_arms_cut33.py` on `n2_arms_cut32.py`'s shape: `DECLARATION_UNITS = ("C7-a", "C7-b", "C7-c", "C3-a", "C3-b", "C10-a", "BI-1", "BI-2", "BI-3", "BI-4", "BI-5")`, `UNIT_CHECKS` mapping each to its acceptance test, `CO_CITED = ()`, `unit_of` (rows are exactly the units here — no letter suffix beyond the unit's own), and `CUT33_ARMS`, one per unit, `before` copied verbatim from the tree at freeze:

| unit | module | `before` (the line as the tree spells it after Tasks 1–4) | `after` |
|---|---|---|---|
| C7-a | `lineage.py` | `    return tuple(r for r in snapshot.bases[dataset].routes if r.identity is None or r.identity not in retired)` | `    return tuple(snapshot.bases[dataset].routes)` |
| C7-b | `lineage.py` | `            findings.append("lineage-incomplete")  # every route retired: no standing ancestry, never silently single` | `            pass  # every route retired: no standing ancestry, never silently single` |
| C7-c | `corpus.py` | `            return self._corpus.add(record)` inside `CorpusWriter.retract` — if that line occurs more than once in the module, widen `before` to include the preceding `raise RelocationTargetMissing(` block's last line so the block is unique | the same, preceded by a facet rewrite: `self._corpus.replace(...)` dropping the retired route from the target dataset's `lineage-basis` (use whatever update primitive `revise` uses — `grep -n "ReplaceOp\|def revise" corpus.py`) |
| C3-a | `closure.py` | `            "coverage": list(retractions.coverage),` | `            "coverage": [],` |
| C3-b | `evaluation.py` | `    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)` | `    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)\n    if world:\n        enumeration = RetractionEnumeration(enumeration.found, tuple(f"{c}@{s}" for c, s in view.stamp.coverage))` |
| C10-a | `corpus.py` | the `Finding(` block whose `code="retraction-target-invalid"` (lines 1432–1438 at baseline), copied whole | the `except ScienceError as refused:` arm's body replaced by `continue` |
| BI-1 | `evaluation.py` | `        if node.id in subtracted:\n            continue  # a standing retraction names it: a lookup, never decoded` | `        if False:\n            continue  # a standing retraction names it: a lookup, never decoded` |
| BI-2 | `evaluation.py` | `        if node.id in subtracted:\n            continue  # the amended G8 clause (§7a): it leaves the read set; \`active\` recomputes over what remains` | `        if False:` … |
| BI-3 | `evaluation.py` | `        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),` | `        found=tuple(sorted(enumeration.found)),` |
| BI-4 | `evaluation.py` | `        except (ScienceError, RefError) as caught:\n            raise RetractionUnreadable(ref, str(caught)) from caught` | `        except (ScienceError, RefError):\n            continue` |
| BI-5 | `evaluation.py` | `        if computed != recorded:\n            raise RetractionResolutionDisagreement(ref, recorded, computed)` | `        if False:\n            raise RetractionResolutionDisagreement(ref, recorded, computed)` |

Every `before` must occur exactly once in its module and the mutated module must `ast.parse` (`test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable`); the two `subtracted` lines differ by their comments, which is why the comments are part of the pinned strings. `python/tests/acceptance/n2_arms_cut33.py` re-exports the five names as `acceptance/n2_arms_cut32.py` does.

- [ ] **Step 3: The guard and the runner**

`python/tests/acceptance/test_n2_cut33.py` on `test_n2_cut32.py`'s shape: `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-16-conformance-cut-33.md"`, `CUT33_FREEZE_COMMIT` and `CUT33_FROZEN_SHA256` from Task 0's Step 4, `FROZEN_DECLARATION = "python/tests/n2_arms_cut33.py"` with its SHA-256 pinned after the declaration is final, `FROZEN_PRIOR_CUT_FILES` = cut 32's dict plus `"python/tests/n2_arms_cut32.py": "<cut 32's declaration commit — git log -1 --format=%h -- python/tests/n2_arms_cut32.py>"`, `PRIOR_ARMS` extended with `CUT32_ARMS`, no `UNAUDITED_UNIT` (every unit homes an arm — the accounting test asserts `homed == {unit: 1 for unit in DECLARATION_UNITS}` and `len(CUT33_ARMS) == 11`), the freeze-pin test asserting `"**11 declaration units**"` and `'("cut32_acceptance.py",)'` in the current document, `test_every_acceptance_test_the_arms_name_exists` over `test_correction_acceptance.py`, and the audit over every arm with the staleness baseline from the tree. `python/tools/cut33_acceptance.py` is `cut32_acceptance.py` with `32→33`, `PREFIX_RUNNERS = ("cut32_acceptance.py",)`, `PHASE_MODULES = ("test_correction_acceptance.py", "test_n2_cut33.py")`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut33"`, and `declared_accounting` importing from `n2_arms_cut33` (rows counted from `UNIT_CHECKS`).

- [ ] **Step 4: Freeze the declaration, discharge, commit**

Pin `CUT33_DECLARATION_SHA256`; run `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut33.py -q -k "not sabotage"` for the accounting and pins, then on the certified volume `SCIENCE_CUT33_ROOT=/mnt/ssd/Dropbox/beliefs/.work/acceptance/cut33 uv run --frozen python tools/cut33_acceptance.py` — the runner's `DEFAULT_WORK` resolves the main checkout through the worktree's real path and lands under `WORK_ROOT` on this host (Task 6's note; `beliefs-51ffdf`), so the root is set explicitly to the main checkout's `.work/acceptance/cut33`, beside cut 32's, on the certified volume; the runner exports `SCIENCE_CUT4_ROOT`…`SCIENCE_CUT33_ROOT` to the prefix chain itself. ~190 `CapabilityUnavailable` failures mean a root is on uncertified storage, not a regression (memory `worktree-on-work-root-needs-cut-root-exports`), then `just hook-pre-push`. Record both summary lines (the runner's and pytest's) for the results record. Every arm `sound`, the baseline `resolved`, no `stale`.

```bash
tasks check
git add python/tests/acceptance python/tests/n2_arms_cut33.py python/tools/cut33_acceptance.py
git commit -m "test(cut): discharge conformance cut 33 — C7, C3's coverage clauses, C10's audit arm, BI-1..5"
```

---

### Task 8: Results record, ledger, roadmap, guide, amendments, slice 2 filed

**Files:**
- Create: `docs/plans/2026-09-16-conformance-cut-33-results.md`
- Modify: `docs/designs/2026-09-16-conformance-cut-33.md` (the `**Status:**` line only), `docs/superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md` (the `**Status:**` line), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`: the `correction-remainder` row now "C8, C9" with C7, C3 closed and C10's audit arm read; the summary names cut 33 and every label the results record's `Remaining boundary` names), `docs/plans/2026-08-29-implementation-roadmap.md` (rewritten whole: `Ranked at: cut 33`; the boundary index row `correction-remainder | C8, C9; C10's certification arm stays with contract-cut | 1, off the path`; tier 1's off-path table row 1 placement text; the lane table's `mutation` row "open at cut 33, slice 1 discharged, slice 2 next"; Appendix A regenerated by `python/tools/roadmap_status.py`; Appendix B rows C3 and C7 removed, C10's entry narrowed, C8/C9 unchanged; the count "175 of 216 rows closed, 41 open"), `docs/guide/contracts-and-adoption.md` (the cut-33 line rewritten as discharged; the corpus totals), `README.md` ("Every conformance cut through **cut 33**"; the design table row status; "The latest discharged boundary is cut 33"), `docs/guide/claims-and-belief.md` or `foundations.md` (one sentence where retraction standing is described: it now reaches the evaluator at the read — `grep -rn "standing" docs/guide/*.md` finds the place), `docs/designs/2026-08-03-correction-lifecycle-design.md` (a dated note under §4 "Per instantiation": the assessment, verification and route instantiations landed at cut 33 through the read; snapshot and narrowing are slice 2's)
- Tasks: `tasks done` the step children as their commits land; the slice-1 task at the results commit; two ideas filed (spec §11 items 1 and 5); the slice-2 task filed under `beliefs-aa27da` with spec §12 as its body

- [ ] **Step 1: The two status lines**

The cut document's `**Status:**` → "discharged 2026-09-16 on the certified volume; results: `../plans/2026-09-16-conformance-cut-33-results.md`" (§§2–7 untouched under the guard's pin); the slice design's `**Status:**` → "discharged at conformance cut 33 on 2026-09-16; results: ../../plans/2026-09-16-conformance-cut-33-results.md".

- [ ] **Step 2: The results record**

On cut 32's shape (`docs/plans/2026-09-16-conformance-cut-32-results.md`): §1 what ran (both summary lines, the arms' verdicts, the staleness baseline); §2 accounting — the eleven units, C7 closed, C3 closed, C10 part on its `instrument-certification` arm, the global count 175 of 216; §3 evidence — corrections carried by the cut document, deviations from the plan (each reviewed and taken, with the reason), limitations found at review (spec §11 restated, plus anything found while implementing); §4 reproduction measurement (the record's §12, summarized: the derived enumeration equals the supplied one; no digest to move); §5 `## Remaining boundary` — **must name at least one guarantee-row label**: C8 and C9 (slice 2, the snapshot target, spec §12), C10's certification arm (`contract-cut`), and the two ideas filed; §6 main integration (filled at merge); §7 execution rulings.

- [ ] **Step 3: Ledger, roadmap, guide, README, the two amendments**

Edit as the Files block says. The roadmap is rewritten whole and carries no dated corrections; its `Cut 33 (2026-09-16)` paragraph beside the cut-31 and cut-32 ones says: the first slice of the third off-path lane under rule 6 discharges C7 and C3 and reads C10's audit arm; it re-ranks nothing on the path; `correction-remainder` stays row 1 off the path with C8, C9 for slice 2. Run `cd python && uv run --frozen python tools/roadmap_status.py` and paste Appendix A; then `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green — `test_the_ledger_summary_names_the_newest_remaining_boundary`, `test_the_newest_cut_document_says_it_is_discharged` and `test_the_roadmap_and_ledger_name_the_same_boundaries` all read cut 33 now.

- [ ] **Step 4: Tasks**

```bash
tasks add "Roadmap: a world-wide standing fold at derivation, not capture" --status idea --tag conformance --tag world-read \
  -b "Slice 1 §11.1: epoch._standing_retractions folds per corpus, so a counter-retraction moved apart from what it counters is upheld in both corpora; the evaluator refuses the disagreement (RetractionResolutionDisagreement) rather than compute a wrong standing. The remedy is a fold over the whole capture at derivation — a new version of the retraction-enumeration rule, its fixtures and receipt identity. Slice 2's or contract-cut's to schedule."
tasks add "Should the audit report a certification that retirement would change?" --status idea --tag conformance --tag correction \
  -b "Slice 1 §11.5: corpus.lineage_snapshot returns retired empty and audit.check_lineage_basis reads the stored basis; retirement is a belief-input fact only. Decide whether an audit should report a dataset whose effective certification differs from its stored basis's."
S2=$(tasks add "Correction remainder, slice 2 — the snapshot target (C8, C9)" --parent beliefs-aa27da -p 3 --size l --complexity high --tag migration --tag mutation --tag correction \
  -b "Spec-to-be: slice 1 design §12. A third retraction arm, snapshot, naming an epoch subject by kind and identity; retracted joins the receipt outcomes and the snapshot-state reduction; import_epoch refuses a retracted producer snapshot before any write; audit_epochs and snapshot_state report retracted; a computation whose supplied producer_snapshot_identity is retracted refuses; narrowing is build_epoch under narrower coverage then retract naming the old identity with successor the new one; the mount negative. Closes the boundary." | jq -r .id)
tasks dep "$S2" --on beliefs-dc4e56
tasks done beliefs-dc4e56 "slice 1 discharged at cut 33: standing reaches the evaluator; C7 and C3 closed, C10's audit arm read; results docs/plans/2026-09-16-conformance-cut-33-results.md"
tasks check
git add docs README.md tasks
git commit -m "docs(cut): discharge conformance cut 33; correction-remainder slice 1 closes C7 and C3"
```

`beliefs-aa27da` stays open (C8, C9); `beliefs-eacbe2` (`contract-cut`) gains no dependency here — the base contract is unamended by this slice (no grammar, kind or relation changed; the estimand-set exactness is an implementation check, not a document change).

- [ ] **Step 5: Merge**

Per the repository's convention every cut merges `--no-ff` into `main` after its results record lands; the memory `execution-ledgers-are-durable-artifacts` says the rulings ledger must be committed to a tracked path before the worktree is removed. From the main checkout: `git merge --no-ff design/correction-remainder -m "merge: correction remainder slice 1 — conformance cut 33"`, then `just gate` on the merged tree, then record the merge commit in the results record's §6 in a follow-up commit (`docs(cut33): record merged-main verification`), as cut 32 did (`81c68c9`). The worktree stays for slice 2 (rule 4: one worktree per lane).

---

## Self-review

**Spec coverage.** §2 decision 1 → Tasks 1, 2, 4 (`SuppliedContext`, the two enumerations); decision 2 → Task 4 (`ProducerSnapshotMismatch`, the handoff); decision 3 → Task 4 (the refold and `RetractionResolutionDisagreement`); decision 4 → Tasks 1, 4 (`RetractionUnreadable` at both validators; the absence path and `_absent_inputs`); decision 5 → Task 4 (the two `subtracted` skips; the docstring; the composite note); decisions 6, 7 → Task 3 (`retired`, `Route.identity`, the projection) and Task 4 (`retire` in `gather`); decision 8 → Task 1 (the fold); decision 9 → no code (a bound; stated in the cut document's §7); decision 10 → Task 4 (`visited`, `verification_ids`, `scope`, `taken`, `scoped`); decision 11 → Tasks 4, 5; §3.1 → Tasks 1, 2; §3.2 → Task 1; §4 → Task 4 (every paragraph: dereference/fold, assessments, verifications, the snapshot and `absences`, the widened-absence consequence, the closure's enumeration, the handoff, the early return); §5 → Task 3; §6 → Task 4's `test_world_standing.py` and Task 7's C3-a/C3-b; §7 → Task 7's C10-a (no code); §8.1 → Tasks 1–4 (every listed test has a task); §8.2, §8.3, §8.4 → Task 7; §8.5 → Tasks 1 (probe), 4 (the frozen acceptance modules), 5 (cut 32's U8 pins); §9 → the file map; §10 → Task 6 with the planning correction; §11 → Task 8 (ideas 1 and 5 filed; the rest restated); §12 → Task 8 (the slice-2 task); §13 → Tasks 0, 8.

**Placeholder scan.** The `...  # verbatim` markers in Task 4 name baseline line ranges that are copied unchanged, not written anew — they are references to existing code, with the lines given. `<…>` in Task 6's §12 are two values read from `state.json` at execution and named as such. Task 7's `before` strings are the lines Task 4 writes, and the guard's exactly-once test is what holds them.

**Review corrections (2026-09-16, six findings, all taken).** Task 1 imports `closure` inside `local_retraction_enumeration` (module-level closes `closure → facet_read → corpus`); Task 3's `_absent_references` follows the walk's stopping rules (an unretired conflict examines no route); Task 1's counter-retraction test expects the target standing (`True`); Task 4's recipes use the real seed (`a-1`/`a-2`, `v-1`/`v-2`, a new `outcomes` knob), `admit`'s real signature and result types, fresh views after raw writes, and the two read prerequisites (manifests on raw-written fixtures; the view's producer identity on world reads) with the green checkpoint after the new `gather`; Task 6 and Task 7 set `SCIENCE_MM30_ROOT` / `SCIENCE_CUT33_ROOT` explicitly because `paths.py` and the runner resolve the main checkout through the worktree's real path.

**Review corrections (2026-09-17, two test recipes).** Task 4 constructs the forbidden nonempty `retired` map directly, bypassing `retire`'s basis filter, and constructs a canonical retraction naming a wrong target content identity so shape validation passes and target resolution supplies the refusal.

**Type consistency.** `retraction_standing(view, facets: Mapping[str, Mapping[str, object]]) -> Mapping[str, bool]` in Tasks 1, 4; `local_retraction_enumeration(view: ReadView) -> RetractionEnumeration` in Tasks 1, 4, 7; `RETRACTION_UPHELD`/`RETRACTION_OVERTURNED` from `closure` in Tasks 1, 4, 7; `WorldReadView.retraction_enumeration()` / `.producer_snapshot_identity()` (methods, not properties) in Tasks 2, 4, 7; `retire(snapshot, retired)`, `effective_routes`, `effective_tag`, `absences(snapshot)` in Tasks 3, 4, 7; `Route.identity: str | None = None` in Tasks 3, 4; `evaluate_traced(..., retractions=)`, `evaluate(..., retractions=)` in Tasks 4, 6, 7; `RetractionUnreadable(ref, cause)`, `RetractionResolutionDisagreement(ref, recorded, computed)`, `ProducerSnapshotMismatch(supplied, bound)` in Tasks 1, 4, 7; `over_kwargs` in `domain_facet_fixtures.py` in Tasks 4, 7.
