# Mount Citations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a session's writes cite records held in its read mounts. Make the
single-corpus check, the world audit and the corpus-local belief read handle
cross-corpus evidence honestly. Discharge cut 44 (J16–J21).

**Architecture:**
- `corpus.py` gains `MountCitations`, a per-refusal-chain view over the write root and
  the read mounts. It opens each read mount lazily inside that mount's non-queuing
  capture hold, refuses an address two corpora hold, refuses a citation across
  differing contract identities, and answers producers as the session's union.
- `CorpusWriter` takes `read_mounts` and runs its refusal chain inside one citation
  scope. The session passes its normalized read mounts.
- `eligibility_outcome` classifies an inadmissible edge as `unmet` or `unresolved`.
  - `corpus_check` reports `unresolved` as a warning.
  - `audit_world` re-judges eligibility through a captured, total citation reader.
- A corpus-local `gather` refuses an input the corpus does not hold.

**Tech Stack:** Python 3.11+ under `uv`, pytest, `nodes` records, the `atoms` engine
behind `root.py`, the acceptance harness and the N2 audit.

**Spec:** `docs/superpowers/specs/2026-10-01-mount-citations-design.md`. It was approved
2026-10-01 after six review rounds (§12) and amended at planning (§13: B4's
supersession, the foreseen re-targets, `eligibility_outcome`). Read it first. Its
decision numbers are cited throughout.

## Global Constraints

- **Baseline:** branch `cross-mount-eligibility` at the plan's commit, branched from
  `main` at `eef8749`. Work in `.worktrees/cross-mount-eligibility`, which is locked
  "on WORK_ROOT storage". Paths shown to the user carry the
  `.worktrees/cross-mount-eligibility/` prefix. Run pytest from the canonical path
  (`cd "$(pwd -P)"`).
- **The cut is 44.** No branch holds a cut above 43 on 2026-10-01. Task 0 re-scans
  before freezing. The runner chains `cut43_acceptance.py`, which is on `main`.
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  - For this lane: `MountCitations` reaches the capture hold through the existing
    `_operation_lock_for` in `corpus.py`, and the lane adds no write primitive. Task 2
    runs both inventories and `test_capability_boundary.py` green.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
  - Here that is Task 7, with `(cut44, 44, (24, 24, 6))`.
- **The declared accounting is 24 arms, 24 declaration units and 6 rows (J16–J21).**
  - J16 has 13 arms: `J16-a` through `J16-m`.
  - J17, J18 and J19 have 2, 2 and 5: `J17-a`/`J17-b`, `J18-a`/`J18-b`,
    `J19-a` through `J19-e`.
  - J20 and J21 have one each: `J20-a`, `J21-a`.
- **Frozen pins stay byte-exact, except the two re-targets spec §13 foresees.**
  - These must still occur exactly once after this lane's edits:
    - cut 32's `        reading = self._view if view is None else view\n        self._refuse_supersedes_same_kind(node, view=reading)\n`;
    - every pinned `self._refuse(record, document_validated=True…)` call site;
    - cut 20's `        producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))\n`
      in `acquisition.py`.
  - Re-target **F4** in `test_n2_cut20.py`'s `_LIVE_SABOTAGES` (Task 2) and **B4b** in
    `test_n2_cut22.py`'s `_LIVE_SABOTAGES` (Task 5). Never edit a frozen declaration
    module.
  - Tasks 2–5 each end with `tests/test_arm_staleness.py`. Zero stale is the exit
    condition. A stale arm other than F4 and B4b is a finding against the spec: stop
    and report it.
- **Long runs are harness-tracked.** Run the cut runner and the gate through the Bash
  tool with `run_in_background: true`, piping through `tee` into
  `~/d/beliefs/.work/acceptance/cut44-*.log`. Never `setsid nohup`, `&` or
  `detached.sh`. On a harness cap kill, park `--reason environment` and report.
- **Tests:** `just test-one <args>` (paths relative to `python/`) while working, and
  `just test-fast` before each commit. There are no TypeScript changes.
- **Commits:** conventional commits with no attribution trailers. Run `tasks check`
  before each commit.

## Review Focus

1. **A citation whose read mount is mid-write when the session cites nothing there.** A
   person writing a proposition expects it to be written. Only citing writes open
   mounts (decision 5). Pinned by
   `test_a_write_citing_nothing_opens_no_mount_while_a_mount_is_held` in Task 2.
2. **An exception inside the refusal chain after a read mount opened.** The next write
   must not find a stale hold. A person expects the following write to proceed. Pinned
   by `test_a_refused_citing_write_releases_every_mount_hold` in Task 2.
3. **Two writers on one write root, one with read mounts and one without** (writer state
   is shared per root). The library writer must keep today's behaviour. Pinned by
   `test_a_library_writer_beside_a_mounted_writer_reads_its_own_root_only` in Task 2.
4. **`corpus_check` over a corpus whose assessment cites a run held elsewhere** (not only
   a dataset). A person expects a warning, not an error. Pinned by
   `test_an_unheld_run_is_eligibility_unresolved` in Task 3.
5. **`audit_world` over an epoch that covers the citing corpus but not the cited one.** A
   person expects `eligibility-unmet`, with the audit completing. Pinned by
   `test_j19_an_uncovered_holder_is_unmet` in Task 4.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-10-01-conformance-cut-44.md` (new), the writer-session design §7, `README.md`, the guide, `python/tests/test_designs_corpus.py`, the ledger, the roadmap | freeze, bank J16–J21 (Task 0) |
| `python/src/beliefs/errors.py`; `python/src/beliefs/corpus.py` (`MountCitations`, `_SessionOverlay`); `python/tests/test_mount_citations.py` (new) | the mount view (Task 1) |
| `python/src/beliefs/acquisition.py` (`reports=`); `corpus.py` (`EligibilityOutcome`, `eligibility_outcome`, the writer's scope, `_refuse_cited`, `_refuse_facets`, `_refuse_ineligible`); `python/src/beliefs/session/__init__.py`; `test_mount_citations.py`, `test_session_writer.py`, `acceptance/test_n2_cut20.py` | the writer and the session (Task 2) |
| `corpus.py` (`_record_findings`' arm); `python/tests/test_read_side.py` | J18 (Task 3) |
| `python/src/beliefs/audit.py`; `python/tests/test_world_audit.py` | J19 (Task 4) |
| `python/src/beliefs/evaluation.py`; `python/tests/test_domain_facet_read.py`, `python/tests/test_world_view.py`, `acceptance/test_n2_cut22.py` | J20, J21, B4b (Task 5) |
| `python/tests/acceptance/test_mount_citations_acceptance.py` (new) | durable J16–J21 (Task 6) |
| `python/tests/n2_arms_cut44.py`, `python/tests/acceptance/n2_arms_cut44.py`, `python/tests/acceptance/test_n2_cut44.py`, `python/tools/cut44_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, recent-cut row (Task 7) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | the next addendum (Task 8) |
| `docs/plans/<date>-conformance-cut-44-results.md` (new), the session-mounts spec, the guide, the ledger, the roadmap | discharge (Task 9) |

---

### Task 0: Freeze cut 44, bank J16–J21

**Files:**
- Create: `docs/designs/2026-10-01-conformance-cut-44.md`
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (§7 table), `python/tests/test_designs_corpus.py`, `README.md`, `docs/guide/contracts-and-adoption.md`, `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md` (through `python/tools/roadmap_status.py`), the spec's Status line, tasks

- [ ] **Step 1: Confirm 44 is unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes); do git ls-tree -r --name-only $b docs/designs | grep -o "conformance-cut-4[4-9]" | sort -u | sed "s|^|$b: |"; done; echo scan done
```
Expected: only `scan done`. Any `-44` or higher means stop and ask.

- [ ] **Step 2: Bank J16–J21.**
  - Append the six rows to the writer-session design's §7 table, byte for byte from
    the spec's §7 (`grep -n '^| \*\*J1[6-9]\*\*\|^| \*\*J2[01]\*\*' docs/superpowers/specs/2026-10-01-mount-citations-design.md`).
  - Put this line above them: "J16–J21 banked with conformance cut 44's freeze
    (`../superpowers/specs/2026-10-01-mount-citations-design.md` §7); J21 supersedes
    B4's absent-dataset clause (spec §13)."
  - In `test_designs_corpus.py`, change `range(1, 16)` to `range(1, 22)`.
  - `cd python && uv run --frozen python tools/roadmap_status.py` prints
    `Closed X of Y`; the new total is Y + 6. Update README, the guide's totals, the
    ledger (J16–J21 open under the new boundary `mount-citations`, `write-path` lane
    reopened) and the roadmap's accounting and Appendix A.
  - The roadmap's *On the path* section now names `mount-citations` as the
    second-project milestone's remaining kernel prerequisite (spec §9).

- [ ] **Step 3: Write the cut document** on cut 43's shape
  (`docs/designs/2026-09-27-conformance-cut-43.md`):
  - **Header:** `**Status:** frozen 2026-10-01, before implementation; J16–J21 are open`,
    the spec and plan paths, and "Numbered after cut 43 under roadmap rule 1".
  - **§1:** spec §1, condensed.
  - **§2, the boundary:** the file map's Tasks 1–5.
  - **§3, selection:** J16–J21 and the unit table from Task 7 Step 1.
  - **§4, accounting:** "**24 arms, 24 declaration units**, six rows; recent-cut row
    `(24, 24, 6)`", plus Task 6's acceptance case count: 10.
  - **§5, N2 and acceptance obligations:**
    - the arm table from Task 7 Step 1;
    - the F4 and B4b re-targets (spec §13);
    - B4's absent-dataset clause cited as superseded by J21, and B4b sharing J21a's
      mutation;
    - `PREFIX_RUNNERS = ("cut43_acceptance.py",)`;
    - `PHASE_MODULES = ("test_mount_citations_acceptance.py", "test_n2_cut44.py")`.
  - **§6, second reader:**
    - J17-b's check holds the mount's lock from a second holder (a library writer's
      `_state.lock`), not the session's own;
    - J19-c's post-capture mutation happens after `open_world_view` returns;
    - J16-g's symlink is a key of `mounts`, not a configured root.
  - **§7, limitations:** spec §10.

- [ ] **Step 4: Step children.** Update the spec's Status line to "approved 2026-10-01;
  frozen as cut 44 on 2026-10-01". File one child per task under `beliefs-9ce6e4`:

```bash
tasks edit beliefs-9ce6e4 --plan mount-citations
tasks add "Task 0: Freeze cut 44, bank J16–J21" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 0: Freeze cut 44, bank J16–J21" --complexity low --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 1: The mount view" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 1: The mount view — \`MountCitations\`" --complexity high --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 2: The writer and the session" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 2: The writer and the session" --complexity high --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 3: The single-corpus check (J18)" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 3: The single-corpus check reports what it cannot see (J18)" --complexity mid --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 4: The world audit (J19)" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 4: The world audit judges eligibility over the capture (J19)" --complexity high --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 5: Belief reads (J20, J21)" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 5: Belief reads — J20's proof, J21's refusal, B4b" --complexity mid --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 6: The acceptance module" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 6: The acceptance module — \`test_mount_citations_acceptance.py\`" --complexity high --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 7: Declarations, guard, runner, recent-cut row" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 7: Declarations, guard, runner, the recent-cut row; run the cut" --complexity mid --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 8: The reproduction re-run" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 8: The reproduction re-run" --complexity low --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 9: Results, re-rank, amendments" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 9: The results record, the re-rank, and the amendments" --complexity mid --process direct --agent claude-code/claude-opus-5-5
tasks add "Task 10: Final review, gate, merge" --parent beliefs-9ce6e4 --plan mount-citations --step "Task 10: Final review, gate, merge" --complexity mid --process direct --agent claude-code/claude-opus-5-5
```
Then `tasks dep` each child on its predecessor, and start Task 0's child.

- [ ] **Step 5: Verify and commit**

```bash
just test-one tests/test_designs_corpus.py tests/test_check_guide.py
tasks done <Task 0's id> "cut 44 frozen; J16–J21 banked"
tasks check && git add docs README.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut): freeze conformance cut 44, mount citations; bank J16–J21"
git rev-parse --short HEAD; sha256sum docs/designs/2026-10-01-conformance-cut-44.md
```
Record `CUT44_FREEZE_COMMIT` and `CUT44_FROZEN_SHA256` for Task 7.

---

### Task 1: The mount view — `MountCitations`

**Files:**
- Modify: `python/src/beliefs/errors.py`, `python/src/beliefs/corpus.py`
- Create: `python/tests/test_mount_citations.py`

**Interfaces:**
- Produces:
  - `errors.CitationContractMismatch(ContractMismatch)`, constructed as
    `CitationContractMismatch(root: Path, namespace: str, held: str, writer: str)`.
  - `corpus.MountCitations(own: ReadView, own_profile: ProfileSpec, read_mounts: Sequence[Path])`,
    with these methods:
    - `holder(ref) -> ReadView | None`;
    - `resolve`, `holds`, `get`;
    - `producers(dataset, *, aliases=()) -> tuple[str, ...]`;
    - `iter_stored()`;
    - `overlay(base) -> _SessionOverlay`;
    - `close()`.
  - `corpus._SessionOverlay(citations, base)`, with `resolve`, `holds`, `get`,
    `producers`, `iter_stored`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_mount_citations.py`:

```python
"""Mount citations (mount-citations design, cut 44): the mount view, the writer's
refusal chain over read mounts, and the session's wiring. Roots W, M and M3 pin
`TYPED` (the testing contract and the fixture `biology`, so `typed_estimand()`'s
`testing/affects` decodes); M2 pins `TYPED_OTHER`, another `biology` identity
(decision 3's mismatch); M4 pins `TESTING_ONLY`, a namespace set without `biology`."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut3 import typed_applicability, typed_estimand
from nodes.core.errors import RefError
from nodes.core.write_plan import DefaultExecutor
from domain_facet_fixtures import profile_with, testing_contract
from profiles import pins_for

from beliefs.profile import compile_profile, shipped_base_contract

from beliefs import stored
from beliefs.corpus import CorpusWriter, MountCitations, ReadView, _operation_lock_for, _root_state_for
from beliefs.errors import AddressMapConflict, BuildContended, CitationContractMismatch

TYPED = profile_with()
TYPED_OTHER = profile_with("other")
TESTING_ONLY = compile_profile(shipped_base_contract(), [testing_contract(None)])


def adopted(root: Path, profile=TYPED) -> CorpusWriter:
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile)
    if not (root / "corpus.yaml").exists():
        writer.adopt_manifest(profile=pins_for(profile))
    return writer


def observed(seed: str, *, actor: str = ACTOR, retrieval: str | None = None):
    payload = {"locator": "instrument:fixture", "attested_by": actor}
    if retrieval is not None:
        payload["retrieval"] = retrieval
    return stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation=payload)


def run_over(slug: str, *datasets, produces=()):
    return stored.run_node(slug, title=slug, spec="analysis-spec:s1", observes=[d if isinstance(d, str) else d.id for d in datasets], produces=list(produces))


def proposition(slug: str):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


def assessment(slug: str, run, prop):
    return stored.assessment_node(
        slug, title=slug, spec="analysis-spec:s1", run=run.id, proposition=prop.id if not isinstance(prop, str) else prop,
        outcome="supported", interpretation_rule="rule:threshold",
        estimand=typed_estimand(), applicability=typed_applicability(),
    )


@pytest.fixture()
def roots(tmp_path):
    made = {name: tmp_path / name for name in ("w", "m", "m2", "m3", "m4")}
    for name, root in made.items():
        adopted(root, {"m2": TYPED_OTHER, "m4": TESTING_ONLY}.get(name, TYPED))
    return {name: root.resolve() for name, root in made.items()}


def citations(roots, *names):
    own = ReadView.opened_at(roots["w"])
    return MountCitations(own, TYPED, [roots[name] for name in names])


def test_holder_is_the_one_corpus_holding_a_ref(roots):
    d = adopted(roots["m"]).add(observed("d"))
    view = citations(roots, "m", "m3")
    try:
        holder = view.holder(d.id)
        assert holder is not None and holder.corpus_id == ReadView.opened_at(roots["m"]).corpus_id
        assert view.holds(d.id) and view.get(d.id).id == d.id
        assert view.holder("proposition:nowhere") is None
        with pytest.raises(RefError):
            view.get("proposition:nowhere")
    finally:
        view.close()


def test_a_ref_held_twice_refuses_duplicate_location_naming_both(roots):
    """J17-a's check."""
    d = adopted(roots["m"]).add(observed("d"))
    adopted(roots["m3"]).add(observed("d"))
    view = citations(roots, "m", "m3")
    try:
        with pytest.raises(AddressMapConflict) as refused:
            view.holder(d.id)
    finally:
        view.close()
    ids = sorted(ReadView.opened_at(roots[name]).corpus_id for name in ("m", "m3"))
    assert refused.value.finding.code == "duplicate-location"
    assert refused.value.finding.detail == ", ".join(ids)


def test_a_held_read_mount_lock_refuses_build_contended(roots):
    """J17-b's check: another holder owns M's operation lock."""
    d = adopted(roots["m"]).add(observed("d"))
    view = citations(roots, "m")
    try:
        with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
            view.holder(d.id)
    finally:
        view.close()


def test_read_mounts_open_lazily_and_close_releases_their_holds(roots):
    view = citations(roots, "m")
    with _operation_lock_for(roots["m"]):  # nothing opened yet, so nothing contends
        pass
    view.holder("proposition:anything")
    with pytest.raises(BuildContended):  # the capture hold is held until close
        with _operation_lock_for(roots["m"]).capture():
            pass
    view.close()
    with _operation_lock_for(roots["m"]).capture():
        pass


def test_a_citation_into_a_differing_namespace_identity_refuses(roots):
    """J16-d's unit: M2 pins another `biology` identity than W's."""
    p = adopted(roots["m2"], TYPED_OTHER).add(proposition("p2"))
    view = citations(roots, "m2")
    try:
        with pytest.raises(CitationContractMismatch) as refused:
            view.holder(p.id)
    finally:
        view.close()
    assert refused.value.namespace == "biology" and refused.value.root == roots["m2"]


def test_a_namespace_only_the_writer_pins_does_not_refuse(roots):
    p = adopted(roots["m4"], TESTING_ONLY).add(proposition("p4"))
    view = citations(roots, "m4")
    try:
        assert view.holder(p.id) is not None
    finally:
        view.close()


def test_producers_are_the_union_over_the_session_dangling_edges_included(roots):
    target = dataset_ref("future")
    adopted(roots["w"]).add(run_over("rw", produces=[target]))
    adopted(roots["m"]).add(run_over("rm", produces=[target]))
    view = citations(roots, "m")
    try:
        assert view.producers(target) == ("run:rm", "run:rw")
    finally:
        view.close()


def test_the_session_overlay_resolves_into_mounts_and_unions_producers(roots):
    d = adopted(roots["m"]).add(observed("d"))
    adopted(roots["m3"]).add(run_over("r3", produces=[d.id]))
    view = citations(roots, "m", "m3")
    try:
        overlay = view.overlay(ReadView.opened_at(roots["w"]))
        assert overlay.resolve(d.id) == d.id and overlay.get(d.id).id == d.id
        assert overlay.producers(d.id) == ("run:r3",)
    finally:
        view.close()
```

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_mount_citations.py`
Expected: an `ImportError` on `MountCitations` and `CitationContractMismatch`.

- [ ] **Step 3: Implement.** In `errors.py`, beside `ContractMismatch`:

```python
class CitationContractMismatch(ContractMismatch):
    """A citation's holder pins another identity of a namespace the writer pins
    (mount-citations decision 3): decoding under either profile would equate two
    contracts, so the citation refuses instead."""

    def __init__(self, root: Path, namespace: str, held: str, writer: str) -> None:
        self.root, self.namespace, self.held, self.writer = root, namespace, held, writer
        super().__init__(
            f"{root}: the cited corpus pins {held} for {namespace!r}; this writer pins {writer} "
            "(mount-citations decision 3)"
        )
```

Then, in `corpus.py` after `_CapturedCheckView`, add the two classes. Import
`AddressMapConflict` and `CitationContractMismatch` from `beliefs.errors` and
`ExitStack` from `contextlib`, unless they are already imported.

```python
class MountCitations:
    """Citation reads over a session's write root and read mounts
    (mount-citations decisions 1–5, §3.1). A read mount opens at its first use,
    inside its own capture hold, which never queues; `close` releases every hold.
    One instance serves one refusal chain."""

    def __init__(self, own: ReadView, own_profile: ProfileSpec, read_mounts: Sequence[Path]) -> None:
        self._own = own
        self._own_profile = own_profile
        self._roots = tuple(read_mounts)
        self._opened: dict[Path, ReadView] = {}
        self._holds = ExitStack()

    def close(self) -> None:
        try:
            self._holds.close()
        finally:
            self._opened.clear()

    def _read_mount(self, root: Path) -> ReadView:
        view = self._opened.get(root)
        if view is None:
            self._holds.enter_context(_operation_lock_for(root).capture())
            view = self._opened[root] = ReadView.opened_at(root)
        return view

    def _read_views(self) -> Iterator[tuple[Path, ReadView]]:
        for root in self._roots:
            yield root, self._read_mount(root)

    def _holders(self, ref: str, base: ReadView | _ImportView) -> list[tuple[Path | None, ReadView | _ImportView]]:
        found: list[tuple[Path | None, ReadView | _ImportView]] = [(None, base)] if base.holds(ref) else []
        found.extend((root, view) for root, view in self._read_views() if view.holds(ref))
        return found

    def _one(self, ref: str, base: ReadView | _ImportView) -> ReadView | _ImportView | None:
        """Decision 4: one holder or a refusal, never a pick by corpus order."""
        found = self._holders(ref, base)
        if not found:
            return None
        if len(found) > 1:
            corpora = ", ".join(sorted(self._corpus_id(root) for root, _ in found))
            raise AddressMapConflict(
                Finding("error", "duplicate-location", ref, corpora,
                        f"{ref}: held by corpora {corpora}; a citation never picks a holder by corpus order")
            )
        root, view = found[0]
        if root is not None:
            self._refuse_contract_mismatch(root)
        return view

    def _corpus_id(self, root: Path | None) -> str:
        return self._own.corpus_id if root is None else self._opened[root].corpus_id

    def _refuse_contract_mismatch(self, root: Path) -> None:
        from beliefs.world import load_manifest

        pinned = load_manifest(root).profile.domains
        for namespace, identity in sorted(self._own_profile.activated_contracts.items()):
            held = pinned.get(namespace)
            if held is not None and held != f"{namespace}:{identity}":
                raise CitationContractMismatch(root, namespace, held, f"{namespace}:{identity}")

    def holder(self, ref: str) -> ReadView | None:
        return cast("ReadView | None", self._one(ref, self._own))

    def resolve(self, ref: str) -> str | None:
        view = self.holder(ref)
        return None if view is None else view.resolve(ref)

    def holds(self, ref: str) -> bool:
        return self.holder(ref) is not None

    def get(self, ref: str) -> Node:
        view = self.holder(ref)
        if view is None:
            raise RefError(f"{ref}: no session corpus holds it")
        return view.get(ref)

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        """Decision 3a: the union over the write root and every read mount, held or
        dangling, whether or not anything holds `dataset`."""
        found = set(self._own.producers(dataset, aliases=aliases))
        for _root, view in self._read_views():
            found.update(view.producers(dataset, aliases=aliases))
        return tuple(sorted(found))

    def iter_stored(self) -> Iterator[Node]:
        yield from self._own.iter_stored()
        for _root, view in self._read_views():
            yield from view.iter_stored()

    def overlay(self, base: ReadView | _ImportView) -> _SessionOverlay:
        return _SessionOverlay(self, base)


class _SessionOverlay:
    """An import path's acquisition-boundary view (decision 3a): `base` (the
    overlay, or the write root) first, then the read mounts, one holder or a
    refusal; producers are the union."""

    def __init__(self, citations: MountCitations, base: ReadView | _ImportView) -> None:
        self._citations = citations
        self._base = base

    def resolve(self, ref: str) -> str | None:
        view = self._citations._one(ref, self._base)
        return None if view is None else view.resolve(ref)

    def holds(self, ref: str) -> bool:
        return self._citations._one(ref, self._base) is not None

    def get(self, ref: str) -> Node:
        view = self._citations._one(ref, self._base)
        if view is None:
            raise RefError(f"{ref}: neither the overlay nor a read mount holds it")
        return view.get(ref)

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        found = set(self._base.producers(dataset, aliases=aliases))
        for _root, view in self._citations._read_views():
            found.update(view.producers(dataset, aliases=aliases))
        return tuple(sorted(found))

    def iter_stored(self) -> Iterator[Node]:
        yield from self._base.iter_stored()
        for _root, view in self._citations._read_views():
            yield from view.iter_stored()
```

- [ ] **Step 4: Run them to see them pass**

Run: `just test-one tests/test_mount_citations.py`
Expected: 8 passed. Then run `just test-one tests/test_capability_boundary.py`, which
expects it to stay green.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 1's id> "MountCitations and the session overlay"
tasks check && git add python/src/beliefs/errors.py python/src/beliefs/corpus.py python/tests/test_mount_citations.py tasks
git commit -m "feat(corpus): the mount view for citations over read mounts (cut 44)"
```

---

### Task 2: The writer and the session

**Files:**
- Modify: `python/src/beliefs/acquisition.py`, `python/src/beliefs/corpus.py`, `python/src/beliefs/session/__init__.py`, `python/tests/test_mount_citations.py`, `python/tests/test_session_writer.py`, `python/tests/acceptance/test_n2_cut20.py`

**Interfaces:**
- Consumes: `MountCitations`, `_SessionOverlay` (Task 1).
- Produces:
  - `acquisition.validity_refusal(view, node, profile, *, reports: ReportView | None = None)`.
  - `corpus.EligibilityOutcome(reason: str, unresolved: tuple[str, ...] = ())`.
  - `corpus.eligibility_outcome(view, node, profile, *, judge=None, reports: Callable[[str], ReportView] | None = None) -> EligibilityOutcome | None`.
  - `corpus.eligibility_refusal(...)`: the same arguments, returning `str | None`.
  - `CorpusWriter(..., read_mounts: Collection[Path] | None = None)`.
  - The session passes `read_mounts`.

- [ ] **Step 1: Write the failing writer tests.** Append to `test_mount_citations.py`:

```python
from fixtures_cut3 import report as acquisition_report
from test_corpus_write import OperationRecorder

from beliefs.errors import AcquisitionBoundaryRefused, EligibilityUnmet, FacetPayloadRefused, ImportRefused

IMPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-10-01T00:00:00Z", "closed_at": "2026-10-01T00:00:01Z"}


def mounted_writer(roots, *names, profile=TYPED, port=False):
    root = roots["w"]
    operation_port = OperationRecorder(root, authority=FULL, profile=profile) if port else None
    return CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile, operation_port=operation_port,
                        read_mounts=[roots[name] for name in names])


def test_an_assessment_over_a_mount_dataset_and_proposition_is_written(roots):
    """J16-a's and J16-b's check."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = mounted_writer(roots, "m")
    run = w.add(run_over("r", d))
    held = w.add(assessment("a", run, p))
    assert ReadView.opened_at(roots["w"]).holds(held.id)
    assert not ReadView.opened_at(roots["m"]).holds(held.id)


def test_a_verification_of_a_mount_assessment_is_written(roots):
    """J16-c's check."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    run = m.add(run_over("r", d))
    a = m.add(assessment("a", run, p))
    value = stored.assessment_value(ReadView.opened_at(roots["m"]).get(a.id), profile=TYPED)
    w = mounted_writer(roots, "m")
    w.add(stored.verification_node("v", title="v", assessment=value.identity(), assessment_ref=a.id,
                                   scope="clean-environment", verdict="passed"))


def test_a_citation_across_differing_identities_refuses(roots):
    """J16-d's check."""
    m2 = adopted(roots["m2"], TYPED_OTHER)
    p2 = m2.add(proposition("p2"))
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", "m2")
    run = w.add(run_over("r", d))
    with pytest.raises(CitationContractMismatch):
        w.add(assessment("a", run, p2))


def test_an_assessment_over_a_dataset_a_third_mount_produces_refuses(roots):
    """J16-f's check: producers are the session's."""
    d = adopted(roots["m"]).add(observed("d"))
    p = adopted(roots["m"]).add(proposition("p"))
    adopted(roots["m3"]).add(run_over("r3", produces=[d.id]))
    w = mounted_writer(roots, "m", "m3")
    run = w.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet, match="run:r3"):
        w.add(assessment("a", run, p))


def test_a_candidate_named_by_a_mount_runs_dangling_edge_refuses(roots):
    adopted(roots["m"]).add(run_over("rm", produces=[dataset_ref("future")]))
    w = mounted_writer(roots, "m")
    with pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w.add(observed("future"))


def test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses(roots):
    """J16-h's check."""
    w = mounted_writer(roots, "m")
    plain = w.add(stored.dataset_node(title="plain", resources=pinned("plain")))
    adopted(roots["m"]).add(run_over("rm", produces=[plain.id]))
    candidate = plain.model_copy(deep=True)
    candidate.facets["empirical-observation"] = {"locator": "instrument:fixture", "attested_by": ACTOR}
    with pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w.revise(candidate)


def test_an_acquired_dataset_a_mount_run_produces_refuses(roots):
    """J16-i's check, at the seam `holdings/acquire.py` calls."""
    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    dataset = observed("got", retrieval=report.id)
    adopted(roots["m"]).add(run_over("rm", produces=[dataset.id]))
    w = mounted_writer(roots, "m")
    with w._citing(), pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w._refuse_acquired_dataset(dataset, report)


def test_an_imported_run_producing_a_mount_observation_refuses(roots):
    """J16-j's check: the reverse direction."""
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", port=True)
    with pytest.raises(ImportRefused) as refused:
        w.import_bundle([run_over("ri", produces=[d.id])], **IMPORT)
    assert refused.value.member == "run:ri"
    assert isinstance(refused.value.__cause__, AcquisitionBoundaryRefused)
    with pytest.raises(AcquisitionBoundaryRefused):
        w.add(run_over("rw", produces=[d.id]))


def test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses(roots):
    """J16-k's check: retrieval reports stay with their dataset."""
    m = adopted(roots["m"], TYPED)
    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    m_port = CorpusWriter(roots["m"], DefaultExecutor, authority=FULL, profile=TYPED,
                          operation_port=OperationRecorder(roots["m"], authority=FULL, profile=TYPED))
    m_port.import_bundle([report], **IMPORT)
    w = mounted_writer(roots, "m")
    with pytest.raises(FacetPayloadRefused, match="facet-retrieval-unresolved"):
        w.add(observed("split", retrieval=report.id))
    assert m.read_view.holds(report.id)


def test_an_assessment_over_a_raw_split_dataset_refuses(roots):
    """J16-l's check: eligibility reads a dataset's report in its own corpus."""
    from fixtures_cut4 import raw_write

    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    CorpusWriter(roots["m"], DefaultExecutor, authority=FULL, profile=TYPED,
                 operation_port=OperationRecorder(roots["m"], authority=FULL, profile=TYPED)).import_bundle([report], **IMPORT)
    split = observed("split", retrieval=report.id)
    raw_write(roots["w"], split)
    p = adopted(roots["m"]).add(proposition("p"))
    w = mounted_writer(roots, "m")
    w._reconstruct()
    run = w.add(run_over("r", split))
    with pytest.raises(EligibilityUnmet, match="facet-retrieval-unresolved"):
        w.add(assessment("a", run, p))


def test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses(roots):
    """J16-m's check: imports resolve locally and judge producers over the session."""
    w = mounted_writer(roots, "m", port=True)
    d = w.add(observed("d"))
    run = w.add(run_over("r", d))
    p = w.add(proposition("p"))
    adopted(roots["m"]).add(run_over("rm", produces=[d.id]))
    with pytest.raises(ImportRefused) as refused:
        w.import_bundle([assessment("a", run, p)], **IMPORT)
    assert refused.value.member == "assessment:a"
    assert isinstance(refused.value.__cause__, EligibilityUnmet) and "run:rm" in str(refused.value.__cause__)


def test_without_read_mounts_the_writes_refuse_as_today(roots):
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = adopted(roots["w"])
    run = w.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet, match="unresolved"):
        w.add(assessment("a", run, p))


def test_a_write_citing_nothing_opens_no_mount_while_a_mount_is_held(roots):
    """Review Focus 1, and J17's negative."""
    w = mounted_writer(roots, "m")
    with _root_state_for(roots["m"], DefaultExecutor).lock:
        w.add(proposition("q"))


def test_a_citing_write_while_a_mount_is_held_refuses_build_contended(roots):
    """A run's `observes` is not read at write time; the assessment through it cites."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = mounted_writer(roots, "m")
    run = w.add(run_over("r", d))
    with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p))
    assert not ReadView.opened_at(roots["w"]).holds("assessment:a")


def test_an_assessment_citing_only_write_root_records_still_contends(roots):
    """J17's negative: decision 5 opens every read mount to rule out a second holder."""
    w = mounted_writer(roots, "m")
    d, p = w.add(observed("d")), w.add(proposition("p"))
    run = w.add(run_over("r", d))
    with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p))


def test_a_refused_citing_write_releases_every_mount_hold(roots):
    """Review Focus 2."""
    adopted(roots["m2"], TYPED_OTHER).add(proposition("p2"))
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", "m2")
    run = w.add(run_over("r", d))
    with pytest.raises(CitationContractMismatch):
        w.add(assessment("a", run, "proposition:p2"))
    for name in ("m", "m2"):
        with _operation_lock_for(roots[name]).capture():
            pass


def test_a_library_writer_beside_a_mounted_writer_reads_its_own_root_only(roots):
    """Review Focus 3: writer state is shared per root; the read mounts are not."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    mounted = mounted_writer(roots, "m")
    run = mounted.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet):
        adopted(roots["w"]).add(assessment("a", run, p))


def test_read_mounts_refuse_the_writers_own_root_and_repeats(roots, tmp_path):
    link = tmp_path / "alias"
    link.symlink_to(roots["w"])
    with pytest.raises(ValueError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[link])
    with pytest.raises(ValueError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[roots["m"], roots["m"]])
    with pytest.raises(TypeError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[str(roots["m"])])
```

Also add these two to `test_mount_citations.py`:
- the analysis-spec case, through `TESTING_PROFILE` roots;
- the composite case, through `build_composite` over M's `biology/affects` propositions.

Each copies its existing single-root test, with the target held in M:
- `test_corpus_write.py`, the `typed_writer` spec-target test;
- `test_composite_boundary.py`'s first composite add.

Name them `test_a_spec_targeting_a_mount_proposition_is_written` and
`test_a_composite_over_mount_propositions_is_written`. Each test gives every root it
uses the profile that existing test uses, so decision 3 does not fire.

- [ ] **Step 2: The session tests.** Append to `test_session_writer.py`, after `_two_roots`.
  `V2T` adds the testing contract to `V2M`, so the assessments' `testing/affects`
  estimand decodes:

```python
from domain_facet_fixtures import testing_contract

V2T = compile_profile(shipped_base_contract(), [testing_contract(None)], coordination=shipped_coordination(2))


def _two_typed_roots(tmp_path, monkeypatch):
    a, b = mounted_root(tmp_path / "a", V2T), mounted_root(tmp_path / "b", V2T)
    _stub_durable_seams(monkeypatch)
    return a.resolve(), b.resolve(), WorldConfig(tmp_path / "world", WORLD, (a, b))


def test_the_session_writer_cites_its_read_mounts(tmp_path, monkeypatch):
    """J16-e's check."""
    a, b, config = _two_typed_roots(tmp_path, monkeypatch)
    library = CorpusWriter(b, DefaultExecutor, authority=FULL, profile=V2T)
    d = library.add(stored.dataset_node(title="d", resources=pinned("d"),
                                        empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}))
    p = library.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    session = _open(config, tmp_path, write_root=a, profile=V2T, mounts={a: V2T, b: V2T})
    w = session.scoped(RequiredCapabilities.for_kinds({"run", "assessment"}, {}), "A")
    session.claim_invocation("A", "assess", "d" * 64)
    run = w.add(stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id]))
    w.add(stored.assessment_node("a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id,
                                 outcome="supported", interpretation_rule="rule:threshold",
                                 estimand=typed_estimand(), applicability=typed_applicability()))
    session.close_invocation("A", {"done": []})
    session.close()


def test_a_symlinked_write_root_mount_key_is_filtered_after_normalization(tmp_path, monkeypatch):
    """J16-g's check: the alias of the write root never reaches the writer."""
    a, b, config = _two_typed_roots(tmp_path, monkeypatch)
    alias = tmp_path / "alias-a"
    alias.symlink_to(a)
    library = CorpusWriter(b, DefaultExecutor, authority=FULL, profile=V2T)
    p = library.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    d = library.add(
        stored.dataset_node(title="d", resources=pinned("d"),
                            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}))
    session = _open(config, tmp_path, write_root=a, profile=V2T, mounts={alias: V2T, b: V2T})
    w = session.scoped(RequiredCapabilities.for_kinds({"run", "assessment"}, {}), "A")
    session.claim_invocation("A", "assess", "d" * 64)
    run = w.add(stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id]))
    w.add(stored.assessment_node("a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id,
                                 outcome="supported", interpretation_rule="rule:threshold",
                                 estimand=typed_estimand(), applicability=typed_applicability()))  # cites: opens the mounts
    session.close_invocation("A", {"done": []})
    session.close()
```
Add `pinned`, `typed_estimand`, `typed_applicability`, `ACTOR`, `stored`,
`compile_profile`, `shipped_base_contract` and `shipped_coordination` to that module's
imports if they are absent.

- [ ] **Step 3: Run them to see them fail**

Run: `just test-one tests/test_mount_citations.py tests/test_session_writer.py -k "mount or symlinked or cites"`
Expected: `TypeError: ... unexpected keyword argument 'read_mounts'` and the J16 cases
failing.

- [ ] **Step 4: `validity_refusal` takes `reports`.** In `acquisition.py`, add the
  `ReportView` protocol beside `ProducerView`, and change only the retrieval block:

```python
class ReportView(Protocol):
    def holds(self, ref: str) -> bool: ...
    def get(self, ref: str) -> Node: ...


def validity_refusal(view: ProducerView, node: Node, profile: ProfileSpec, *, reports: ReportView | None = None) -> str | None:
    """`None` when `node` carries a valid acquisition-boundary declaration. The
    retrieval report is read through `reports`, the dataset's own corpus, when
    given (mount-citations decision 3a)."""
    ...  # unchanged down to the retrieval block
    retrieval = payload.get("retrieval")
    if retrieval is not None:
        held = view if reports is None else reports
        if not held.holds(retrieval):
            return f"facet-retrieval-unresolved: {retrieval}"
        facet = held.get(retrieval).facets.get("act-report")
```
Keep the `producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))` line
byte-exact; cut 20 pins it.

- [ ] **Step 5: `eligibility_outcome`.** In `corpus.py`, replace `eligibility_refusal`
  with the pair below. The reason strings are today's, byte for byte.

```python
@dataclass(frozen=True)
class EligibilityOutcome:
    """Why an `assesses` edge is inadmissible (mount-citations decision 7): the
    edge is `unresolved` when it rests on references the reading view does not
    hold and nothing held is valid; otherwise it is `unmet`."""

    reason: str
    unresolved: tuple[str, ...] = ()


def eligibility_outcome(
    view: ReadView | _ImportView | _CheckView | _CapturedCheckView | MountCitations,
    node: Node,
    profile: ProfileSpec,
    *,
    judge: ProducerView | None = None,
    reports: Callable[[str], ReportView] | None = None,
) -> EligibilityOutcome | None:
    """S7's cross-node predicate. `view` finds the run and its datasets; `judge`
    answers each dataset's producers (the session's, decision 3a); `reports`
    names the corpus holding a dataset's retrieval report."""
    if not any(relation.predicate == stored.ASSESSES for relation in node.relations):
        return None
    facet = node.facets.get(stored.ASSESSMENT_FACET)
    run_ref = facet.get("run") if isinstance(facet, dict) else None
    if not isinstance(run_ref, str) or not run_ref:
        return EligibilityOutcome("the assessment names no run")
    if not view.holds(run_ref):
        return EligibilityOutcome(f"the run {run_ref!r} resolves to no node in this corpus", (run_ref,))
    run = view.get(run_ref)
    observed = stored.inputs_of(run, stored.OBSERVES)
    if not observed:
        return EligibilityOutcome(f"the run {run_ref!r} has no observes input; reads inputs never confer eligibility")
    judging = view if judge is None else judge
    reasons: list[str] = []
    unresolved: list[str] = []
    for dataset_ref in observed:
        if not view.holds(dataset_ref):
            reasons.append(f"{dataset_ref}: unresolved")
            unresolved.append(dataset_ref)
            continue
        reason = validity_refusal(judging, view.get(dataset_ref), profile, reports=None if reports is None else reports(dataset_ref))
        if reason is None:
            return None
        reasons.append(f"{dataset_ref}: {reason}")
    return EligibilityOutcome(
        f"no observes input of {run_ref!r} carries a valid empirical-observation facet ({'; '.join(reasons)})",
        tuple(unresolved),
    )


def eligibility_refusal(
    view: ReadView | _ImportView | _CheckView | _CapturedCheckView | MountCitations,
    node: Node,
    profile: ProfileSpec,
    *,
    judge: ProducerView | None = None,
    reports: Callable[[str], ReportView] | None = None,
) -> str | None:
    """`eligibility_outcome`'s reason alone: the write boundary's and frozen callers' form."""
    outcome = eligibility_outcome(view, node, profile, judge=judge, reports=reports)
    return None if outcome is None else outcome.reason
```
Import `ProducerView` and `ReportView` from `beliefs.acquisition`, beside
`validity_refusal`. `MountCitations` is defined later in the module. The annotation is
lazy (`from __future__ import annotations` is at the top of `corpus.py`), so ordering
does not matter. Keep `_record_findings`' call as `eligibility_refusal(check, node, profile)`
until Task 3.

- [ ] **Step 6: The writer.**
  - `__init__` gains `read_mounts: Collection[Path] | None = None` after
    `snapshot_resolver`. Before `root = Path(root)`:

```python
        if read_mounts is not None and any(not isinstance(path, Path) for path in read_mounts):
            raise TypeError("read_mounts holds Paths")
        own = Path(root).resolve()
        resolved = [path.resolve() for path in read_mounts or ()]
        if own in resolved or len(set(resolved)) != len(resolved):
            raise ValueError("read_mounts names the writer's own root, or one root twice (mount-citations §3.2)")
        self._read_mounts: tuple[Path, ...] = tuple(sorted(resolved))
        self._citations: MountCitations | None = None
```
  - The scope and the view, beside `_view`:

```python
    @contextmanager
    def _citing(self) -> Iterator[None]:
        """One citation scope per refusal chain (decision 5): read mounts open
        lazily inside it and their holds release when the outermost scope ends."""
        if not self._read_mounts or self._citations is not None:
            yield
            return
        self._citations = MountCitations(self._view, self._profile, self._read_mounts)
        try:
            yield
        finally:
            citations, self._citations = self._citations, None
            citations.close()

    def _citation_view(self) -> ReadView | MountCitations:
        if not self._read_mounts:
            return self._view
        if self._citations is None:
            raise RuntimeError("a citation read outside a citation scope (mount-citations decision 5)")
        return self._citations
```
  - `_refuse` becomes a wrapper. Rename the existing method to `_refuse_cited`, leaving
    every line of its body as it is, and insert one line at the top of the body:
    `view = self._citation_view() if view is None else view`. Then add:

```python
    def _refuse(
        self,
        node: Node,
        *,
        document_validated: bool = False,
        view: ReadView | _ImportView | None = None,
        provenance: bool = False,
    ) -> None:
        with self._citing():
            self._refuse_cited(node, document_validated=document_validated, view=view, provenance=provenance)
```
  - `_preflight_replace_locked`: do the same. Rename it to `_preflight_replace_cited`,
    leave its lines unchanged, and add a wrapper `_preflight_replace_locked(self, node,
    *, provenance=False)` that runs it inside `with self._citing():`. Change its
    `self._refuse_ineligible(node)` to
    `self._refuse_ineligible(node, view=self._citation_view())`, and its
    `self._refuse_facets(node, provenance=provenance)` to pass the same view.
  - `_refuse_ineligible`:

```python
    def _refuse_ineligible(self, node: Node, *, view: ReadView | _ImportView | MountCitations | None = None) -> None:
        """S7's write boundary. An import overlay finds the run and its datasets
        through itself and judges them with the session's producers; every other
        path reads the citation view (mount-citations §3.1)."""
        reading = self._view if view is None else view
        judge: ProducerView | None = None
        reports: Callable[[str], ReportView] | None = None
        if self._read_mounts:
            citations = self._citations
            assert citations is not None, "eligibility is judged inside a citation scope"
            if isinstance(reading, _ImportView):
                judge, reports = citations.overlay(reading), (lambda _ref: reading)
            else:
                judge, reports = reading, citations.holder
        reason = eligibility_refusal(reading, node, self._profile, judge=judge, reports=reports)
        if reason is not None:
            raise EligibilityUnmet(f"{node.id}: the assesses edge is inadmissible because {reason}")
```
  - `_refuse_facets`: open a scope, and judge through the session:

```python
    def _refuse_facets(self, node: Node, *, view: ReadView | _ImportView | MountCitations | None = None, provenance: bool = False) -> None:
        """§5.2: registry, payload, bearer, actor, and acquisition validity. With
        read mounts, bearer and validity are judged over the session; a retrieval
        report is read in the record's own corpus (decision 3a)."""
        self._refuse_facet_shapes(node)
        with self._citing():
            reading = self._citation_view() if view is None else view
            local = reading if isinstance(reading, _ImportView) else self._view
            judged = self._citations.overlay(reading) if self._citations is not None and isinstance(reading, _ImportView) else reading
            reason = bearer_refusal(judged, node)
            if reason is not None:
                raise AcquisitionBoundaryRefused(reason)
            ...  # the actor check, unchanged
                reason = validity_refusal(judged, node, self._profile, reports=local)
            ...  # the remainder, unchanged
```
    Re-indent the rest of the body into the `with` block unchanged.
  - The remaining checks of decision 2 already take `view=…` from `_refuse_cited`, which
    now always passes a non-`None` view. `_refuse_verification` and
    `_refuse_estimand_target_mismatch` receive `self._view if view is None else view`,
    which evaluates to the citation view. Leave those lines unchanged.

- [ ] **Step 7: The session.** In `session/__init__.py`, directly after `resolver =
  _mount_resolver(mounted)`:

```python
    read_mounts = tuple(sorted(path for path in mounted if path != root)) if mounted is not None else ()
```
  In `writer_factory`'s `CorpusWriter(...)` call, after
  `snapshot_resolver=snapshot_resolver,`, add `            read_mounts=read_mounts,`.
  An empty tuple is the no-mount writer, as decision 6 requires.

- [ ] **Step 8: Re-target cut 20's F4** in `acceptance/test_n2_cut20.py`'s
  `_LIVE_SABOTAGES`:

```python
    "F4": Sabotage(
        module="corpus.py",
        before="        reason = validity_refusal(judging, view.get(dataset_ref), profile, reports=None if reports is None else reports(dataset_ref))\n",
        after='        reason = None if stored.EMPIRICAL_OBSERVATION_FACET in view.get(dataset_ref).facets else "absent"\n',
    ),
```

- [ ] **Step 9: Run them to see them pass, then the boundaries**

```bash
just test-one tests/test_mount_citations.py tests/test_session_writer.py tests/test_corpus_write.py tests/test_facet_seams.py tests/test_import_bundle.py tests/test_dataset_revision.py
just test-one tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_arm_staleness.py
```
Expected: all pass. `test_arm_staleness.py` must report zero stale with F4 re-targeted.

- [ ] **Step 10: Commit**

```bash
just test-fast
tasks done <Task 2's id> "writer cites read mounts; session passes its normalized read mounts; F4 re-targeted"
tasks check && git add python/src/beliefs python/tests/test_mount_citations.py python/tests/test_session_writer.py python/tests/acceptance/test_n2_cut20.py tasks
git commit -m "feat(corpus): writes cite read mounts; acquisition invariants over the session (cut 44)"
```

---

### Task 3: The single-corpus check reports what it cannot see (J18)

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`_record_findings`' eligibility arm), `python/tests/test_read_side.py`

**Interfaces:**
- Consumes: `eligibility_outcome`, `EligibilityOutcome` (Task 2).
- Produces: `_record_findings(check, profile, scope, disagreeing, *, citations=None)`.
  `citations` is any object with `eligibility(node, profile) -> EligibilityOutcome | None`;
  Task 4 supplies one. `ELIGIBILITY_CODES = frozenset({"eligibility-unmet", "eligibility-unresolved"})`.

- [ ] **Step 1: Write the failing tests** in `test_read_side.py`, beside the S7 cases.
  Reuse `admissible_corpus` and `observed_dataset`:

```python
def test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved(tmp_path):
    """J18-a's check."""
    view = admissible_corpus(tmp_path, observes=[dataset_ref("elsewhere")])
    findings = corpus_check(view, BASE)
    assert [(f.severity, f.code, f.ref, f.detail) for f in findings] == [
        ("warning", "eligibility-unresolved", "assessment:a1", dataset_ref("elsewhere"))
    ]


def test_an_unheld_run_is_eligibility_unresolved(tmp_path):
    """Review Focus 4."""
    view = admissible_corpus(tmp_path)
    node = view.get("assessment:a1").model_copy(deep=True)
    node.facets[stored.ASSESSMENT_FACET]["run"] = "run:elsewhere"
    raw_write(view._corpus.store.root, stored.stamp_semantic_identity(node))
    findings = corpus_check(reopen(view._corpus.store.root), BASE)
    assert ("warning", "eligibility-unresolved", "assessment:a1", "run:elsewhere") in [
        (f.severity, f.code, f.ref, f.detail) for f in findings
    ]


def test_one_held_invalid_and_one_unheld_dataset_is_unresolved(tmp_path):
    """J18-b's check."""
    plain = stored.dataset_node(title="plain", resources=[{"name": "x", "digest": "sha256:" + "ef" * 32}])
    view = admissible_corpus(tmp_path, observes=[plain.id, dataset_ref("elsewhere")], extra=(plain,))
    assert [(f.severity, f.code) for f in corpus_check(view, BASE)] == [("warning", "eligibility-unresolved")]
```
If `admissible_corpus` has no `extra` parameter, add one (`extra: tuple[Node, ...] = ()`,
seeded beside its nodes). The existing S7 tests are the negatives (all held, all
invalid → `eligibility-unmet`) and must stay green unchanged.

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_read_side.py -k "unresolved"`
Expected: FAIL, reported as `eligibility-unmet` errors.

- [ ] **Step 3: Implement the arm.** In `_record_findings`, add the keyword parameter
  `citations: _EligibilityReader | None = None`, with this protocol:

```python
class _EligibilityReader(Protocol):
    def eligibility(self, node: Node, profile: ProfileSpec) -> EligibilityOutcome | None: ...


ELIGIBILITY_CODES = frozenset({"eligibility-unmet", "eligibility-unresolved"})
```
  Replace the arm's first two lines (`reason = eligibility_refusal(check, node, profile)`,
  `if reason is not None:`) with the lines below. Every line from
  `for relation in node.relations:` down stays as it is:

```python
        outcome = eligibility_outcome(check, node, profile) if citations is None else citations.eligibility(node, profile)
        if outcome is not None and outcome.unresolved:
            findings.append(
                Finding(
                    severity="warning",
                    code="eligibility-unresolved",
                    ref=node.id,
                    detail=", ".join(outcome.unresolved),
                    message=f"{node.id}: eligibility rests on {', '.join(outcome.unresolved)}, which this read does not hold; audit_world judges it",
                )
            )
        elif outcome is not None:
            reason = outcome.reason
```
  The `for relation in node.relations:` block is now under the `elif`, at its existing
  indentation. Its `code="eligibility-unmet",` line is byte-exact.

- [ ] **Step 4: Run them to see them pass**

Run: `just test-one tests/test_read_side.py tests/test_audit.py tests/acceptance/test_durable_corpus.py tests/test_arm_staleness.py`
Expected: pass, zero stale.

- [ ] **Step 5: Commit**

```bash
just test-fast
tasks done <Task 3's id> "corpus_check reports eligibility-unresolved for citations it cannot see"
tasks check && git add python/src/beliefs/corpus.py python/tests/test_read_side.py tasks
git commit -m "feat(corpus): the corpus check reports unresolved eligibility as a warning (J18)"
```

---

### Task 4: The world audit judges eligibility over the capture (J19)

**Files:**
- Modify: `python/src/beliefs/audit.py`, `python/tests/test_world_audit.py`

**Interfaces:**
- Consumes: `_record_findings(..., citations=)`, `ELIGIBILITY_CODES`,
  `eligibility_outcome` (Tasks 2, 3).
- Produces: `audit._CapturedCitations`, private.

- [ ] **Step 1: Write the failing tests** in `test_world_audit.py`. They use the module's
  `corpora`, `world_over`, `publish`, `hold_shipped`, `make_absent`, `damage` and
  `NO_EVIDENCE`:

```python
from coordination_fixtures import raw_add
from fixtures_cut3 import report as acquisition_report
from fixtures_cut3 import typed_applicability, typed_estimand
from dataset_fixtures import pinned

REPORT = stored.act_report_node(acquisition_report(operation="acquisition"))


def _observed(seed, *, retrieval=REPORT.id, facet=True):
    payload = {"locator": "instrument:fixture", "attested_by": "test-actor"}
    if retrieval is not None:
        payload["retrieval"] = retrieval
    return stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation=payload if facet else None)


def _cross_world(tmp_path, *, dataset=None, beta_extra=(), alpha_extra=(), cover=(ALPHA, BETA)):
    """ALPHA (W) holds the run and the assessment; BETA (M) holds the dataset, its report and the proposition."""
    d = dataset or _observed("d")
    p = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    run = stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id])
    a = stored.assessment_node("a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id,
                               outcome="supported", interpretation_rule="rule:threshold",
                               estimand=typed_estimand(), applicability=typed_applicability())
    roots = corpora(tmp_path, {ALPHA: (run, a, *alpha_extra), BETA: (d, REPORT, p, *beta_extra)})
    world = world_over(tmp_path, roots)
    return world, roots, publish(world, cover, hold_shipped(world)), d


def _eligibility(audit, corpus_id=ALPHA):
    return [(f.severity, f.code, f.ref) for f in audit.corpora[corpus_id] if f.code.startswith("eligibility")]


def test_j19_a_supported_cross_corpus_citation_has_no_finding(tmp_path):
    world, _roots, published, _d = _cross_world(tmp_path)
    assert _eligibility(audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)) == []


def test_j19_b_an_absent_holder_is_unresolved(tmp_path):
    world, roots, published, _d = _cross_world(tmp_path)
    make_absent(roots, BETA)
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    (finding,) = [f for f in audit.corpora[ALPHA] if f.code.startswith("eligibility")]
    assert (finding.severity, finding.code) == ("warning", "eligibility-unresolved") and BETA in finding.detail and "absent" in finding.detail


def test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier(tmp_path, monkeypatch):
    import beliefs.world.view as view_module

    world, roots, published, _d = _cross_world(tmp_path)
    opened = view_module.open_world_view

    def then_mutate(*args, **kwargs):
        view = opened(*args, **kwargs)
        for path in (roots[BETA] / "act-report").glob("*.md"):
            path.unlink()  # after the capture: a live read would lose the retrieval report
        return view

    monkeypatch.setattr(view_module, "open_world_view", then_mutate)
    assert _eligibility(audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)) == []


def test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues(tmp_path):
    world, roots, published, _d = _cross_world(tmp_path)
    damage(roots[BETA], "parse-error")
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    (finding,) = [f for f in audit.corpora[ALPHA] if f.code.startswith("eligibility")]
    assert finding.code == "eligibility-unresolved" and "damaged:construction" in finding.detail
    assert ("corpus-damaged" in {f.code for f in audit.corpora[BETA]})


def test_j19_e_an_absent_producer_keeps_the_dataset_produced(tmp_path):
    d = _observed("own")
    p = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    run = stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id])
    a = stored.assessment_node("a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id,
                               outcome="supported", interpretation_rule="rule:threshold",
                               estimand=typed_estimand(), applicability=typed_applicability())
    producer = stored.run_node("rm", title="rm", spec="analysis-spec:s1", produces=[d.id])
    roots = corpora(tmp_path, {ALPHA: (d, REPORT, p, run, a), BETA: (producer,)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    present = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert ("error", "eligibility-unmet", "assessment:a") in _eligibility(present)
    make_absent(roots, BETA)
    absent = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert ("error", "eligibility-unmet", "assessment:a") in _eligibility(absent)


def test_j19_a_malformed_held_record_is_unresolved(tmp_path):
    world, roots, published, d = _cross_world(tmp_path)
    path = next((roots[BETA] / "dataset").glob("*.md"))
    path.write_text(path.read_text().replace("instrument:fixture", "instrument:edited"))  # stale stamp
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    (finding,) = [f for f in audit.corpora[ALPHA] if f.code.startswith("eligibility")]
    assert finding.code == "eligibility-unresolved" and "malformed:semantic-hash-stale" in finding.detail


def test_j19_a_malformed_record_cited_by_an_alias_is_unresolved(tmp_path):
    """Plan review 1, P1: malformedness is keyed by the canonical id."""
    aliased = _observed("d").model_copy(update={"deprecated_ids": ["dataset:old-alias"]})
    aliased = stored.stamp_semantic_identity(aliased)
    p = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    run = stored.run_node("r", title="r", spec="analysis-spec:s1", observes=["dataset:old-alias"])
    a = stored.assessment_node("a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id,
                               outcome="supported", interpretation_rule="rule:threshold",
                               estimand=typed_estimand(), applicability=typed_applicability())
    roots = corpora(tmp_path, {ALPHA: (run, a), BETA: (aliased, REPORT, p)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    path = next((roots[BETA] / "dataset").glob("*.md"))
    path.write_text(path.read_text().replace("instrument:fixture", "instrument:edited"))  # stale stamp
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    (finding,) = [f for f in audit.corpora[ALPHA] if f.code.startswith("eligibility")]
    assert finding.code == "eligibility-unresolved" and "malformed:semantic-hash-stale" in finding.detail


def test_j19_a_known_producer_decides_an_unmapped_dataset_while_a_corpus_is_absent(tmp_path):
    """Plan review 1, P2: a definite producer stays definite; only an unknown one is incomplete."""
    world, roots, published, _d = _cross_world(tmp_path)
    late = _observed("late", retrieval=None)  # no report: only the producer can decide it
    raw_add(roots[ALPHA], late, stored.run_node("rl", title="rl", spec="analysis-spec:s1", produces=[late.id]))
    make_absent(roots, BETA)
    run = stored.run_node("r2", title="r2", spec="analysis-spec:s1", observes=[late.id])
    raw_add(roots[ALPHA], run, stored.assessment_node(
        "a2", title="a2", spec="analysis-spec:s1", run=run.id, proposition="proposition:p", outcome="supported",
        interpretation_rule="rule:threshold", estimand=typed_estimand(), applicability=typed_applicability()))
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert ("error", "eligibility-unmet", "assessment:a2") in _eligibility(audit)


def test_j19_an_unknown_producer_is_unresolved_per_dataset_and_the_scan_continues(tmp_path):
    """Plan review 1, P2: an incomplete dataset does not hide a later valid one."""
    good = _observed("good", retrieval=REPORT.id)
    p = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    roots = corpora(tmp_path, {ALPHA: (good, REPORT, p), BETA: (stored.proposition_node("q", title="q", claim={"operator": "affects"}),)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    drift = _observed("drift", retrieval=REPORT.id)
    run = stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[drift.id, good.id])
    raw_add(roots[ALPHA], drift, run, stored.assessment_node(
        "a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id, outcome="supported",
        interpretation_rule="rule:threshold", estimand=typed_estimand(), applicability=typed_applicability()))
    make_absent(roots, BETA)
    assert _eligibility(audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)) == []
    lonely = stored.run_node("r3", title="r3", spec="analysis-spec:s1", observes=[drift.id])
    raw_add(roots[ALPHA], lonely, stored.assessment_node(
        "a3", title="a3", spec="analysis-spec:s1", run=lonely.id, proposition=p.id, outcome="supported",
        interpretation_rule="rule:threshold", estimand=typed_estimand(), applicability=typed_applicability()))
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    (finding,) = [f for f in audit.corpora[ALPHA] if f.ref == "assessment:a3" and f.code.startswith("eligibility")]
    assert finding.code == "eligibility-unresolved" and "producers-incomplete" in finding.detail


def test_j19_an_unmapped_dataset_that_fails_on_its_own_is_unmet_while_a_corpus_is_absent(tmp_path):
    """Plan review 2, P2: incompleteness applies only to a dataset that would otherwise pass."""
    good_report = REPORT
    p = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    roots = corpora(tmp_path, {ALPHA: (good_report, p), BETA: (stored.proposition_node("q", title="q", claim={"operator": "affects"}),)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    plain = _observed("plain-drift", facet=False)
    run = stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[plain.id])
    raw_add(roots[ALPHA], plain, run, stored.assessment_node(
        "a", title="a", spec="analysis-spec:s1", run=run.id, proposition=p.id, outcome="supported",
        interpretation_rule="rule:threshold", estimand=typed_estimand(), applicability=typed_applicability()))
    make_absent(roots, BETA)
    assert ("error", "eligibility-unmet", "assessment:a") in _eligibility(
        audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY))


def test_j19_an_unobserving_dataset_elsewhere_is_unmet(tmp_path):
    world, _roots, published, _d = _cross_world(tmp_path, dataset=_observed("plain", facet=False))
    assert _eligibility(audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)) == [
        ("error", "eligibility-unmet", "assessment:a")
    ]


def test_j19_an_uncovered_holder_is_unmet(tmp_path):
    """Review Focus 5."""
    world, _roots, published, _d = _cross_world(tmp_path, cover=(ALPHA,))
    assert _eligibility(audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)) == [
        ("error", "eligibility-unmet", "assessment:a")
    ]
```
If `world_over` refuses to admit a root that the coverage does not cover, build the
`cover=(ALPHA,)` world over ALPHA's root alone instead. Keep the assertion.

These tests keep `WITH_BIOLOGY`, because `corpora` pins it in every manifest. The
eligibility arm reads only base content (decision 3), so the assessments'
`testing/affects` estimand is never decoded by the code under test. Records added after
`publish` with `raw_add` are drift: unmapped, and captured.

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_world_audit.py -k j19`
Expected: the supported, absent, damaged, malformed and post-capture cases report
`eligibility-unmet`.

- [ ] **Step 3: Implement** in `audit.py`.
  - Import `_CapturedCheckView`, `EligibilityOutcome`, `eligibility_outcome` and
    `ELIGIBILITY_CODES` from `beliefs.corpus`, `validity_refusal` from
    `beliefs.acquisition`, and `CorpusDamaged` (used by J19-d's sabotage).

```python
class _CapturedCitations:
    """Decision 8's total reader over the captured world, for one citing corpus:
    own corpus first, then the epoch's map; never a live read, never a raise."""

    def __init__(self, view: WorldReadView, citing: str, readable: Mapping[str, _CapturedCheckView],
                 causes: Mapping[str, str], malformed: Mapping[str, Mapping[str, str]]) -> None:
        self._view = view
        self._citing = citing
        self._own = readable[citing]
        self._readable = readable
        self._causes = causes
        self._malformed = malformed
        self._profile: ProfileSpec | None = None
        self.unreadable: dict[str, str] = {}

    def _holder(self, ref: str) -> _CapturedCheckView | None:
        if self._own.holds(ref):
            if self._incomplete(ref):
                self.unreadable[ref] = f"{self._citing} producers-incomplete:{','.join(sorted(self._causes))}"
                return None
            return self._own
        corpus_id = self._view.corpus_of(ref)
        if corpus_id is None or corpus_id == self._citing:
            return None
        cause = self._causes.get(corpus_id)
        holder = self._readable.get(corpus_id)
        if cause is None and holder is not None:
            canonical = holder.resolve(ref)  # an alias names the canonical record the map is keyed by
            if canonical is not None and canonical in self._malformed.get(corpus_id, {}):
                cause = f"malformed:{self._malformed[corpus_id][canonical]}"
        if cause is not None:
            self.unreadable[ref] = f"{corpus_id} {cause}"
            return None
        return self._readable.get(corpus_id)

    def _incomplete(self, ref: str) -> bool:
        """Decision 8, per dataset: an own dataset the epoch never mapped, while a
        covered corpus is unreadable, is uncertain only when it would otherwise
        pass. A missing or malformed facet, a basis, a known producer or an
        unresolved report each decide it definitely, and the scan goes on."""
        if self._view.corpus_of(ref) is not None or not self._causes:
            return False
        node = self._own.get(ref)
        if node.kind != "dataset":
            return False
        return validity_refusal(self, node, self._profile, reports=self._own) is None

    def holds(self, ref: str) -> bool:
        return self._holder(ref) is not None

    def resolve(self, ref: str) -> str | None:
        holder = self._holder(ref)
        return None if holder is None else holder.resolve(ref)

    def get(self, ref: str) -> Node:
        holder = self._holder(ref)
        if holder is None:
            raise RefError(f"{ref}: not readable in this capture")
        return holder.get(ref)

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        found = {producer for view in self._readable.values() for producer in view.producers(dataset, aliases=aliases)}
        found.update(self._view.published_producers(dataset))
        return tuple(sorted(found))

    def eligibility(self, node: Node, profile: ProfileSpec) -> EligibilityOutcome | None:
        self.unreadable = {}
        self._profile = profile
        outcome = eligibility_outcome(self, node, profile, reports=self._holder)
        if outcome is None or not outcome.unresolved:
            return outcome
        if not any(ref in self.unreadable for ref in outcome.unresolved):
            return EligibilityOutcome(outcome.reason)  # only unmapped references: unmet
        return EligibilityOutcome(
            outcome.reason,
            tuple(f"{ref} ({self.unreadable[ref]})" if ref in self.unreadable else ref for ref in outcome.unresolved),
        )
```
  - In `audit_world`'s per-corpus loop:
    - Record each excluded corpus's scope in `excluded_scope: dict[str, str]` next to
      `excluded.add(corpus_id)`.
    - Keep the captured view and its scopes for the second pass:
      `eligible[corpus_id] = (captured, scope, disagreeing)`, where
      `captured = _CapturedCheckView(view.captured_records(corpus_id))` is the value
      the call already builds.
    - Filter the first pass's eligibility findings out:
      `findings.extend(f for f in _record_findings(captured, profile, scope, disagreeing) if f.code not in ELIGIBILITY_CODES)`.
    - After `malformed[corpus_id] = …`, record
      `malformed_codes[corpus_id] = {f.ref: f.code for f in findings if f.code in MALFORMEDNESS_CODES}`.
  - After the per-corpus loop, before the `for node in view.iter_stored():` recomputation
    loop, run the second pass:

```python
    causes = {corpus_id: "absent" for corpus_id in view.absent()}
    causes.update({report.corpus_id: f"damaged:{report.cause}" for report in view.damaged()})
    causes.update({corpus_id: f"excluded:{scope}" for corpus_id, scope in excluded_scope.items()})
    readable = {corpus_id: captured for corpus_id, (captured, _scope, _disagreeing) in eligible.items()}
    for corpus_id, (captured, scope, disagreeing) in sorted(eligible.items()):
        reader = _CapturedCitations(view, corpus_id, readable, causes, malformed_codes)
        second = _record_findings(captured, profile, scope, disagreeing, citations=reader)
        corpora[corpus_id].extend(f for f in second if f.code in ELIGIBILITY_CODES)
```
    A corpus whose damage is `base-pin` hits `continue` before the record findings, so it
    is never in `eligible`. A `construction`-damaged corpus is in `eligible`, since its
    remainder was audited, and in `causes`. Its own citations read its captured view
    first, and citations into it are unresolved.

- [ ] **Step 4: Run them to see them pass**

Run: `just test-one tests/test_world_audit.py tests/test_audit.py tests/test_arm_staleness.py`
Expected: pass, zero stale.

- [ ] **Step 5: Commit**

```bash
just test-fast
tasks done <Task 4's id> "audit_world judges eligibility across the captured world"
tasks check && git add python/src/beliefs/audit.py python/tests/test_world_audit.py tasks
git commit -m "feat(audit): the world audit judges eligibility over the capture (J19)"
```

---

### Task 5: Belief reads — J20's proof, J21's refusal, B4b

**Files:**
- Modify: `python/src/beliefs/errors.py`, `python/src/beliefs/evaluation.py`, `python/tests/test_domain_facet_read.py`, `python/tests/test_world_view.py`, `python/tests/acceptance/test_n2_cut22.py`

**Interfaces:**
- Produces: `errors.InputOutsideCorpus(MalformedRecord)`, constructed as
  `InputOutsideCorpus(assessment: str, run: str, inputs: tuple[str, ...])`. `gather`
  raises it, and `evaluate_over` returns `Refused("input-outside-corpus: …")`.

- [ ] **Step 1: Rewrite B4b's check and write J21's.** In `test_domain_facet_read.py`,
  replace the body of `test_an_absent_observed_dataset_is_absent_from_gather`, keeping
  its name, which cut 22's frozen declaration pins:

```python
def test_an_absent_observed_dataset_is_absent_from_gather(tmp_path):
    """B4's absent-dataset clause, superseded by J21 (mount-citations spec §13): a
    corpus-local read of an input the corpus does not hold refuses, never drops it."""
    from beliefs.errors import InputOutsideCorpus

    profile = profile_with()
    view = seed(tmp_path, observes_missing=True)
    with pytest.raises(InputOutsideCorpus) as refused:
        gather(view, PROPOSITION_REF, **over_kwargs(_gathered(kwargs_for(view, profile))))
    assert refused.value.run == "run:run-a" and refused.value.inputs == ("dataset:d-missing",)
    answer = evaluate_over(view, PROPOSITION_REF, **over_kwargs(kwargs_for(view, profile)))
    assert isinstance(answer, Refused) and answer.reason.startswith("input-outside-corpus:")
```
  Check `Refused`'s field name in `beliefs.belief` (`reason`, or whatever the existing
  `Refused` assertions in that module read) and use it.

- [ ] **Step 2: J20's proof.** First split `domain_facet_fixtures.seed` in two:
  - `seed_nodes(*, axis="rows", observes_missing=False, claim=None, proposition=PROPOSITION_REF, outcomes=("supported", "supported")) -> list[Node]`
    returns the node list `seed` builds today;
  - `seed` calls it and keeps its writing branch unchanged.

  Task 6 places those nodes across corpora. Then, in `test_world_view.py`, beside
  `TestEvaluationOverTheWorld`:

```python
def test_j20_the_two_installation_split_evaluates_as_one_corpus(tmp_path):
    """J20: assessments and runs in ALPHA (W); the proposition and observed datasets in BETA (M)."""
    from beliefs.evaluation import evaluate_over_traced

    world, _roots, published = split_evaluation_world(
        tmp_path / "split", ("proposition:p", DATASET_D_A, dataset_ref("d-b"))
    )
    view = open_world_view(world, published)
    profile = profile_with()
    kwargs = world_kwargs(view, profile)
    split_answer, split_admission = evaluate_over_traced(view, "proposition:p", **over_kwargs(kwargs))
    inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                    resolution=kwargs["resolution"], binding=kwargs["binding"])
    assert {ref for ref, corpora in inputs.node_corpus.items() if BETA in corpora} >= {DATASET_D_A}
    assert all(ALPHA in corpora for ref, corpora in inputs.node_corpus.items() if ref.startswith("run:"))
    local = seed(tmp_path / "one")
    local_answer, local_admission = evaluate_over_traced(local, "proposition:p", **over_kwargs(kwargs_for(local, profile)))
    assert split_answer == local_answer and split_admission == local_admission
```
  `split_evaluation_world`'s second argument is the refs it moves to BETA. Check its
  signature in the module, and that `DATASET_D_A` and `seed` are importable there. If
  an equality fails only on a field that names a corpus (an attribution or epoch
  member), compare the answer's verdict, set and admission state instead, and record
  the field in the spec's §13. If anything else differs, stop: the world read
  disagrees with the corpus-local read, and that is a finding.

- [ ] **Step 3: Run them to see them fail**

Run: `just test-one tests/test_domain_facet_read.py tests/test_world_view.py -k "absent_observed or j20"`
Expected: the B4b rewrite fails (no `InputOutsideCorpus`). J20 passes or fails;
record which.

- [ ] **Step 4: Implement.** In `errors.py`:

```python
class InputOutsideCorpus(MalformedRecord):
    """A corpus-local read of an assessment whose run names an input the corpus
    does not hold (mount-citations decision 9): read it over a world view."""

    def __init__(self, assessment: str, run: str, inputs: tuple[str, ...]) -> None:
        self.assessment, self.run, self.inputs = assessment, run, inputs
        super().__init__(f"{assessment} rests on {run}, which names {', '.join(inputs)}; this corpus does not hold them")
```
  In `gather`'s run loop, the input-role loop becomes:

```python
        outside: list[str] = []
        for role in stored.INPUT_ROLES:
            for target in stored.inputs_of(run_node, role):
                if not view.holds(target):
                    corpus_id = _absence_of(view, target)
                    if corpus_id is not None:
                        absent.append((target, corpus_id))
                    elif not world:
                        outside.append(target)
        if outside:
            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))
```
  `ref` is the run's typed ref. Insert the two new lines without moving the loop: the
  raise aborts `gather`, so `run_value`'s earlier silent filter never reaches a caller.
  Then, in `_evaluate_over_inputs`, beside the other mappings:

```python
    except InputOutsideCorpus as exc:
        return Refused(f"input-outside-corpus: {exc}"), NotReached(), None
```

- [ ] **Step 5: Re-target B4b** in `acceptance/test_n2_cut22.py`'s `_LIVE_SABOTAGES`.
  It shares J21-a's mutation:

```python
    "B4b": Sabotage(
        module="evaluation.py",
        before="        if outside:\n            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))\n",
        after="",
    ),
```
  If cut 22's guard keys `_LIVE_SABOTAGES` differently from cut 20's, follow its own
  convention.

- [ ] **Step 6: Run them to see them pass**

Run: `just test-one tests/test_domain_facet_read.py tests/test_world_view.py tests/test_evaluation.py tests/test_world_standing.py tests/test_arm_staleness.py`
Expected: pass, zero stale with B4b re-targeted. Any other test that relied on the
silent drop now raises `InputOutsideCorpus`. Each such test is a consequence of J21;
list every one in the spec's §13 and stop if any is a frozen row's check other than
B4b's.

- [ ] **Step 7: Commit**

```bash
just test-fast
tasks done <Task 5's id> "corpus-local gather refuses unheld inputs; J20 proved over the world; B4b re-targeted"
tasks check && git add python/src/beliefs python/tests docs/superpowers/specs tasks
git commit -m "feat(evaluation): a corpus-local read refuses inputs it cannot see (J21); prove the split (J20)"
```

---

### Task 6: The acceptance module — `test_mount_citations_acceptance.py`

**Files:**
- Create: `python/tests/acceptance/test_mount_citations_acceptance.py`

**Interfaces:**
- Consumes: Tasks 1–5 and `domain_facet_fixtures.seed_nodes` (Task 5).
- From `test_session_mounts_acceptance.py` it imports `library_on` and `state`. From
  `test_session_acceptance` it imports `fresh`.

Ten durable cases. Each owns one `mkdtemp` directory under `work_directory`, removed at
teardown, on cut 43's pattern. Every profile activates the testing contract, so
`typed_estimand()`'s `testing/affects` decodes (plan review 1, P2):
- W, the session's write root: testing, the fixture `biology` and coordination v2.
- M and M3: `profile_with()`, which is testing plus the fixture `biology`.
- M2: `profile_with("other")`, another `biology` identity and decision 3's mismatch.
- O: `profile_with()`, the one-corpus baseline for J20.

Mounts are compiled with this module's own `AVAILABLE`, which carries the three
test-local documents.

- [ ] **Step 1: Write the module.**

```python
"""Conformance cut 44 — mount citations (spec §8.2): J16–J21 over real roots on the
certified volume. W (write root) pins testing, the fixture `biology` and
coordination v2; M and M3 pin testing and the fixture `biology`; M2 pins another
`biology` identity; O holds J20's one-corpus baseline."""

from __future__ import annotations

import secrets
import shutil
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace

import pytest
from authority import FULL
from coordination_fixtures import pins_for
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import kwargs_for, over_kwargs, profile_with, seed_nodes, testing_contract
from fixtures_cut3 import typed_applicability, typed_estimand
from profiles import biology
from test_session_acceptance import fresh
from test_session_mounts_acceptance import library_on, state
from test_world_receipts import hold_shipped, publish, world_over
from test_world_view import make_absent

from beliefs import stored
from beliefs.audit import audit_world
from beliefs.belief import NoBelief
from beliefs.corpus import ReadView, _root_state_for, corpus_check, lineage_snapshot
from beliefs.errors import AddressMapConflict, BuildContended, CitationContractMismatch, EligibilityUnmet, InputOutsideCorpus
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.mount import compile_mount_profile
from beliefs.permit import RequiredCapabilities
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination
from beliefs.root import init_corpus_root, open_corpus
from beliefs.session import open_attended_session
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.view import open_world_view
from nodes.core.write_plan import DefaultExecutor

TYPED = profile_with()
TYPED_OTHER = profile_with("other")
W_PROFILE = compile_profile(shipped_base_contract(), [testing_contract(None), biology("fixture")], coordination=shipped_coordination(2))
AVAILABLE = (testing_contract(None), biology("fixture"), biology("other"))
CITING = RequiredCapabilities.for_kinds({"run", "assessment", "proposition", "verification"}, {})


def _adopt(base: Path, name: str, profile) -> Path:
    root = base / name
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
    return root.resolve()


@pytest.fixture()
def corpora(work_directory):
    base = Path(mkdtemp(prefix="cut44-", dir=work_directory)).resolve()
    try:
        yield SimpleNamespace(
            base=base,
            w=_adopt(base, "w", W_PROFILE),
            m=_adopt(base, "m", TYPED),
            m2=_adopt(base, "m2", TYPED_OTHER),
            m3=_adopt(base, "m3", TYPED),
            o=_adopt(base, "o", TYPED),
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)


def open_session(s, roots):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    mounts = {root: compile_mount_profile(root, available=AVAILABLE) for root in roots}
    return open_attended_session(config, s.base / f"ops-{secrets.token_hex(4)}", write_root=s.w, profile=W_PROFILE, mounts=mounts)


def observed(seed):
    return stored.dataset_node(title=seed, resources=pinned(seed),
                               empirical_observation={"locator": "instrument:fixture", "attested_by": "test-actor"})


def assessment(slug, run, prop_id):
    return stored.assessment_node(slug, title=slug, spec="analysis-spec:s1", run=run.id, proposition=prop_id,
                                  outcome="supported", interpretation_rule="rule:threshold",
                                  estimand=typed_estimand(), applicability=typed_applicability())


def seeded(s):
    m = library_on(s.m, TYPED)
    return m.add(observed("d")), m.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))


def run_then(w, d):
    return w.add(stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id]))  # observes is not read at write time


def test_j16_a_session_cites_a_mount_dataset_and_proposition_durably(corpora):
    s = corpora
    d, p = seeded(s)
    before = state(s.m)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    held = w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert ReadView.opened_at(s.w).holds(held.id) and state(s.m) == before


def test_j16_a_citation_across_differing_identities_refuses_durably(corpora):
    s = corpora
    d, _p = seeded(s)
    p2 = library_on(s.m2, TYPED_OTHER).add(stored.proposition_node("p2", title="p2", claim={"operator": "affects"}))
    session = open_session(s, (s.w, s.m, s.m2))
    w = fresh(session, "A", CITING)
    with pytest.raises(CitationContractMismatch):
        w.add(assessment("a", run_then(w, d), p2.id))
    session.close_invocation("A", {"done": []})
    session.close()


def test_j16_producers_held_in_a_third_mount_refuse_durably(corpora):
    s = corpora
    d, p = seeded(s)
    library_on(s.m3, TYPED).add(stored.run_node("r3", title="r3", spec="analysis-spec:s1", produces=[d.id]))
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    with pytest.raises(EligibilityUnmet, match="run:r3"):
        w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()


def test_j16_no_mount_is_written_durably(corpora):
    s = corpora
    d, p = seeded(s)
    before = {root: state(root) for root in (s.m, s.m3)}
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert {root: state(root) for root in (s.m, s.m3)} == before


def test_j17_a_duplicate_citation_refuses_naming_both_durably(corpora):
    s = corpora
    d, p = seeded(s)
    library_on(s.m3, TYPED).add(observed("d"))
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    run = run_then(w, d)
    with pytest.raises(AddressMapConflict):
        w.add(assessment("a", run, p.id))
    session.close_invocation("A", {"done": []})
    session.close()


def test_j17_a_held_mount_refuses_build_contended_durably(corpora):
    s = corpora
    d, p = seeded(s)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    run = run_then(w, d)
    with _root_state_for(s.m, DefaultExecutor).lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p.id))
    session.close_invocation("A", {"done": []})
    session.close()


def test_j18_the_session_corpus_check_warns_not_errs_durably(corpora):
    s = corpora
    d, p = seeded(s)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert [(f.severity, f.code) for f in corpus_check(ReadView.opened_at(s.w), W_PROFILE)] == [
        ("warning", "eligibility-unresolved")
    ]


def _split_seed(s):
    """J20's fixture: `seed_nodes()`'s proposition and datasets in M, its runs,
    assessments and verifications written in a session on W; the same nodes in O."""
    nodes = seed_nodes()
    in_m = {"proposition:p", dataset_ref("d-a"), dataset_ref("d-b")}
    m, o = library_on(s.m, TYPED), library_on(s.o, TYPED)
    for node in nodes:
        o.add(node)
        if node.id in in_m:
            m.add(node)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    for node in nodes:
        if node.id not in in_m:
            w.add(node)
    session.close_invocation("A", {"done": []})
    session.close()
    roots = {ReadView.opened_at(root).corpus_id: root for root in (s.w, s.m)}
    world = world_over(s.base, roots, name=f"world-{secrets.token_hex(4)}")
    return world, roots, publish(world, tuple(sorted(roots)), hold_shipped(world))


def _world_context(view, pins, kwargs):
    """`pins` are read once, while every manifest is present (plan review 2, P2)."""
    return replace(
        kwargs["context"],
        snapshot=lineage_snapshot(view, (dataset_ref("d-a"), dataset_ref("d-b"))),
        producer_snapshot_identity=view.producer_snapshot_identity(),
        node_corpus={},
        pins=pins,
    )


def test_j19_the_world_audit_supports_the_split_durably(corpora):
    from audit_fixtures import NO_EVIDENCE

    world, _roots, published = _split_seed(corpora)
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=TYPED)
    assert not [f for findings in audit.corpora.values() for f in findings if f.code.startswith("eligibility")]


def test_j20_belief_over_the_world_matches_one_corpus_durably(corpora):
    s = corpora
    world, roots, published = _split_seed(s)
    view = open_world_view(world, published)
    kwargs = kwargs_for(view, TYPED)
    pins = {corpus_id: load_manifest(root).profile for corpus_id, root in roots.items()}
    context = _world_context(view, pins, kwargs)
    split_answer, split_admission = evaluate_over_traced(view, "proposition:p", **over_kwargs({**kwargs, "context": context}))
    local = ReadView.opened_at(s.o)
    local_answer, local_admission = evaluate_over_traced(local, "proposition:p", **over_kwargs(kwargs_for(local, TYPED)))
    assert split_answer == local_answer and split_admission == local_admission
    inputs = gather(view, "proposition:p", context=context, profile=TYPED,
                    resolution=kwargs["resolution"], binding=kwargs["binding"])
    w_id, m_id = ReadView.opened_at(s.w).corpus_id, ReadView.opened_at(s.m).corpus_id
    assert inputs.node_corpus["run:run-a"] == (w_id,) and inputs.node_corpus[dataset_ref("d-a")] == (m_id,)
    # the walk inspected M's dataset through the world view: held, its (empty) producer set captured
    assert context.snapshot.producers[dataset_ref("d-a")] == ()
    assert dataset_ref("d-a") not in context.snapshot.not_present
    make_absent(roots, m_id)
    absent_view = open_world_view(world, published)
    absent_context = _world_context(absent_view, pins, kwargs)
    assert dataset_ref("d-a") not in absent_context.snapshot.producers
    assert absent_context.snapshot.not_present[dataset_ref("d-a")] == m_id
    answer, _admission = evaluate_over_traced(absent_view, "proposition:p", **over_kwargs({**kwargs, "context": absent_context}))
    assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"


def test_j21_a_local_read_of_the_split_refuses_durably(corpora):
    s = corpora
    d, _p = seeded(s)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    q = w.add(stored.proposition_node("q", title="q", claim={"operator": "affects"}))
    w.add(assessment("a", run_then(w, d), q.id))
    session.close_invocation("A", {"done": []})
    session.close()
    view = ReadView.opened_at(s.w)
    kwargs = kwargs_for(view, W_PROFILE)
    with pytest.raises(InputOutsideCorpus):
        gather(view, q.id, context=kwargs["context"], profile=W_PROFILE,
               resolution=kwargs["resolution"], binding=kwargs["binding"])
```
  Check these names against their modules before the first run, and fix the import or
  attribute, not the assertion:
  - `NO_EVIDENCE`'s home;
  - `make_absent`'s module;
  - `NoBelief`'s reason attribute;
  - `node_corpus`'s value type (a tuple or a set);
  - the lineage snapshot's root attribute.

  If `publish` refuses a world whose corpora pin different profiles (W carries
  coordination v2), record that in the spec's §13. Then publish through the epoch
  builder that `acceptance/test_live_selection_acceptance.py` uses for mixed-profile
  worlds, and leave the corpora unchanged. If J20's equality fails only on a field that
  names a corpus or an epoch, compare the verdict, the evidence set and the admission
  state instead, and record the field in §13. Any other difference is a finding: stop.

- [ ] **Step 2: Run on the certified volume**

Run: `just test-one tests/acceptance/test_mount_citations_acceptance.py`
Expected: `10 passed`.

- [ ] **Step 3: Commit**

```bash
tasks done <Task 6's id> "cut 44 acceptance module, 10 durable cases"
tasks check && git add python/tests/acceptance/test_mount_citations_acceptance.py tasks
git commit -m "test(cut44): durable acceptance for mount citations — J16–J21"
```

---

### Task 7: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut44.py`, `python/tests/acceptance/n2_arms_cut44.py` (cut 43's shim with `43` → `44`), `python/tests/acceptance/test_n2_cut44.py`, `python/tools/cut44_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

- [ ] **Step 1: The declaration**, on cut 43's shape (`_arm(row, module, assertion, before, after)`):
  - `DECLARATION_UNITS` is the 24 ids `J16-a` … `J16-m`, `J17-a`, `J17-b`, `J18-a`,
    `J18-b`, `J19-a` … `J19-e`, `J20-a` and `J21-a`.
  - `UNIT_CHECKS` maps each unit to the check in the table below.

  Copy each `before` from the tree and check it with `source.count(before) == 1`. Each
  `after` must parse.

| arm | module | before | after | check |
|---|---|---|---|---|
| J16-a | `corpus.py` | `        self._refuse_ineligible(node, view=view)\n` | `        self._refuse_ineligible(node, view=self._view)\n` | `test_mount_citations.py::test_an_assessment_over_a_mount_dataset_and_proposition_is_written` |
| J16-b | `corpus.py` | `        self._refuse_assesses_target_kind(node, view=reading)\n` | `        self._refuse_assesses_target_kind(node, view=self._view)\n` | the same |
| J16-c | `corpus.py` | `            self._refuse_verification(node, view=self._view if view is None else view)\n` | `            self._refuse_verification(node, view=self._view)\n` | `::test_a_verification_of_a_mount_assessment_is_written` |
| J16-d | `corpus.py` | `        if root is not None:\n            self._refuse_contract_mismatch(root)\n` | `        if False:\n            self._refuse_contract_mismatch(root)\n` | `::test_a_citation_across_differing_identities_refuses` |
| J16-e | `session/__init__.py` | `            read_mounts=read_mounts,\n` | `            read_mounts=(),\n` | `test_session_writer.py::test_the_session_writer_cites_its_read_mounts` |
| J16-f | `corpus.py` | the four-line body of `MountCitations.producers` | `        holder = self.holder(dataset)\n        return () if holder is None else holder.producers(dataset, aliases=aliases)\n` | `::test_an_assessment_over_a_dataset_a_third_mount_produces_refuses` |
| J16-g | `session/__init__.py` | `    read_mounts = tuple(sorted(path for path in mounted if path != root)) if mounted is not None else ()\n` | `    read_mounts = tuple(sorted(Path(key) for key in mounts if Path(key) != root)) if mounts is not None else ()\n` | `test_session_writer.py::test_a_symlinked_write_root_mount_key_is_filtered_after_normalization` |
| J16-h | `corpus.py` | `        self._refuse_facets(restamped, provenance=True)\n` | `        self._refuse_facets(restamped, view=self._view, provenance=True)\n` | `::test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses` |
| J16-i | `corpus.py` | `_SessionOverlay.producers`' `for` loop (two lines) | `        pass\n` | `::test_an_acquired_dataset_a_mount_run_produces_refuses` |
| J16-j | `corpus.py` | `_SessionOverlay.resolve`'s first body line | `        view = self._base if self._base.holds(ref) else None\n` | `::test_an_imported_run_producing_a_mount_observation_refuses` |
| J16-k | `corpus.py` | `            local = reading if isinstance(reading, _ImportView) else self._view\n` | `            local = reading\n` | `::test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses` |
| J16-l | `corpus.py` | `                judge, reports = reading, citations.holder\n` | `                judge, reports = reading, None\n` | `::test_an_assessment_over_a_raw_split_dataset_refuses` |
| J16-m | `corpus.py` | `                judge, reports = citations.overlay(reading), (lambda _ref: reading)\n` | `                judge, reports = None, (lambda _ref: reading)\n` | `::test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses` |
| J17-a | `corpus.py` | `        if len(found) > 1:\n` | `        if False:\n` | `::test_a_ref_held_twice_refuses_duplicate_location_naming_both` |
| J17-b | `corpus.py` | `            self._holds.enter_context(_operation_lock_for(root).capture())\n` | `            pass\n` | `::test_a_held_read_mount_lock_refuses_build_contended` |
| J18-a | `corpus.py` | `        if outcome is not None and outcome.unresolved:\n` | `        if False:\n` | `test_read_side.py::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved` |
| J18-b | `corpus.py` | `        tuple(unresolved),\n    )\n` | `        tuple(unresolved) if len(unresolved) == len(observed) else (),\n    )\n` | `test_read_side.py::test_one_held_invalid_and_one_unheld_dataset_is_unresolved` |
| J19-a | `audit.py` | `        second = _record_findings(captured, profile, scope, disagreeing, citations=reader)\n` | `        second = _record_findings(captured, profile, scope, disagreeing)\n` | `test_world_audit.py::test_j19_a_supported_cross_corpus_citation_has_no_finding` |
| J19-b | `audit.py` | `    causes = {corpus_id: "absent" for corpus_id in view.absent()}\n` | `    causes = {}\n` | `::test_j19_b_an_absent_holder_is_unresolved` |
| J19-c | `audit.py` | `        return self._readable.get(corpus_id)\n` | `        return self._view.corpus_view(ref)\n` | `::test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier` |
| J19-d | `audit.py` | `        if cause is not None:\n            self.unreadable[ref] = f"{corpus_id} {cause}"\n            return None\n` | `        if cause is not None:\n            raise CorpusDamaged(f"eligibility:{ref}", corpus_id, self._view.stamp)\n` | `::test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues` |
| J19-e | `audit.py` | `        found.update(self._view.published_producers(dataset))\n` | `        pass\n` | `::test_j19_e_an_absent_producer_keeps_the_dataset_produced` |
| J20-a | `evaluation.py` | `_facets_held_to_capture(profile, view, target) if world else read_observed_facets(profile, view, target)` | `read_observed_facets(profile, view.corpus_view(stored.typed_ref("run", a.run)) if world else view, target)` | `test_world_view.py::test_j20_the_two_installation_split_evaluates_as_one_corpus` |
| J21-a | `evaluation.py` | `        if outside:\n            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))\n` | `` | `test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather` |

  - **J16-g:** the `after` filters the raw keys, so a symlinked key survives, reaches
    the writer, and is refused there as the writer's own root.
  - **Shared checks:** J16-a and J16-b name one check. List the pair in `CO_CITED`, as
    the n2 declaration format requires for two units citing one test, and follow cut
    43's module for the tuple's shape.
  - **J16-i and J16-j:** spell their `before` from the tree after Task 1, where each is
    unique.
  - **J20-a:** if its line is a live pin elsewhere, the shared `before` is fine because
    this lane does not change it.
  - **J21-a and B4b:** cut 22's re-target (Task 5) uses J21-a's `before`. The two arms
    share the mutation and differ in their check.

- [ ] **Step 2: The guard.** Copy `test_n2_cut43.py` to `test_n2_cut44.py`, then:
  - import `CUT43_ARMS` into `PRIOR_ARMS`, and pin `n2_arms_cut43.py` in
    `FROZEN_PRIOR_CUT_FILES`;
  - set `FROZEN_CUT`, `CUT44_FREEZE_COMMIT`, `CUT44_FROZEN_SHA256`,
    `CUT44_DECLARATION_SHA256` (`sha256sum python/tests/n2_arms_cut44.py`) and
    `FROZEN_ARMS, FROZEN_UNITS = 24, 24`;
  - assert `"**24 arms, 24 declaration units**" in current` and
    `'("cut43_acceptance.py",)' in current`.

  It has no `_LIVE_SABOTAGES`: F4's and B4b's re-targets live in their own guards.

- [ ] **Step 3: The runner.** `python/tools/cut44_acceptance.py`, as cut 43's with:
  - `cut=44`;
  - `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut44"`;
  - `PREFIX_RUNNERS = ("cut43_acceptance.py",)`;
  - `PHASE_MODULES = ("test_mount_citations_acceptance.py", "test_n2_cut44.py")`;
  - `declared_accounting` asserting rows `{"J16", "J17", "J18", "J19", "J20", "J21"}`
    and `(24, 24)`;
  - on success, `print("guarantee rows exercised: 6 (6 newly closed: J16, J17, J18, J19, J20, J21)", flush=True)`.

- [ ] **Step 4: The recent-cut row.** In `test_recent_cut_acceptance.py`:
  - add `import cut44_acceptance as cut44`;
  - add `(cut44, 44, (24, 24, 6))` with id `"cut44"`;
  - add `if cut == 44: assert "guarantee rows exercised: 6 (6 newly closed: J16, J17, J18, J19, J20, J21)" in output`.

- [ ] **Step 5: Guard green, then the cut, harness-tracked.**

```bash
just test-one tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py
```
Then run with the Bash tool, `run_in_background: true`:

```bash
cd ~/d/beliefs/.worktrees/cross-mount-eligibility/python && cd "$(pwd -P)" && export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30 && set -o pipefail && uv run --frozen python tools/cut44_acceptance.py 2>&1 | tee ~/d/beliefs/.work/acceptance/cut44-runner.log
```
Read the log when the harness wakes the session. The expected tail has:
- the phase lines;
- `declared arms: 24 (= 24 declaration units; 6 guarantee rows)`;
- the rows-exercised line;
- exit 0, with every arm `sound`.

How to read a bad verdict:
- `stale` means fix the declaration.
- `vacuous` means reshape the arm and record the change in the spec's §13.
- A background-cap kill means park `--reason environment` and tell the user.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 7's id> "N2 declarations, guard, runner, recent-cut row; cut 44 ran green"
tasks check && git add python/tests/n2_arms_cut44.py python/tests/acceptance/n2_arms_cut44.py python/tests/acceptance/test_n2_cut44.py python/tools/cut44_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut44): N2 declarations, guard, runner and the recent-cut row — J16–J21"
```

---

### Task 8: The reproduction re-run

- [ ] **Step 1: Run** as cut 43's Task 6 did: run the preflight, copy `state.json` first,
  then run `reproduction.rederive`. J21 can move mm30 only if a run there reads an input
  its corpus does not hold. A `Refused("input-outside-corpus…")` where cut 43 got
  `NoBelief` is a finding. Stop and report it with the run, before any amendment.
- [ ] **Step 2: Append the next addendum** to `docs/designs/2026-09-05-mm30-reproduction.md`,
  on the last addendum's shape:
  - what changed: citations over read mounts, the eligibility classes, and J21;
  - what the re-run reached;
  - what it does not claim: mm30 is still one corpus read as a library. The mounted
    measurement is science's `sci-0d00d2` after `sci-dc0381`.
  - Record that mm30's `biology` pin is the shipped pack's, so it can be cited
    (spec §13).

```bash
just test-one tests/test_reproduction_driver.py tests/test_designs_corpus.py
tasks done <Task 8's id> "reproduction re-run under cut 44"
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under mount citations"
```

---

### Task 9: The results record, the re-rank, and the amendments

- [ ] **Step 1: The results record** `docs/plans/<date>-conformance-cut-44-results.md`, on
  cut 43's shape:
  - §1, what ran;
  - §2, accounting: 24 / 24 / 6, J16–J21 closed, and the totals;
  - §3, evidence: the spec's §13 notes; the F4 and B4b re-targets; B4's clause cited as
    superseded; the inventories unchanged; J20's equality and any field it excluded;
  - §4, the reproduction;
  - §5, `## Remaining boundary`: none, with limitations per spec §10;
  - §6, main integration;
  - §7, execution rulings.
- [ ] **Step 2:** In `roadmap_status.py`, add
  `44: ("conformance-cut-44-results §2", "J16, J17, J18, J19, J20, J21", ""),` and
  regenerate Appendix A.
- [ ] **Step 3: Ledger and roadmap.**
  - **Ledger:** `mount-citations` is built and closed, and the `write-path` lane is
    closed again.
  - **Roadmap:** `**Ranked at:** cut 44`. Add a `**Cut 44 (<date>) discharges mount
    citations and closes the boundary**` paragraph: tier 1 **on the path**, the
    second-project milestone's last kernel prerequisite. The milestone now waits on
    science's `sci-dc0381`.
- [ ] **Step 4: Amendments.**
  - Append a dated `## Mount-citations amendment — <date>` section to the
    session-mounts spec. §5's cross-corpus targeting paragraph narrows to mutation
    targets, and limitation 4 reads "mutation targets stay in the write root".
  - In the biology-pack design's §7, add one line after B4 citing J21 as its
    absent-dataset clause's successor. That edits no frozen cut document.
  - The guide's `writes-operations-and-publication.md` states the split between
    citations and mutation targets.
- [ ] **Step 5: Status lines, README, guide, tasks**, then commit:

```bash
tasks done <Task 9's id> "results record, re-rank at cut 44, amendments"
tasks check && git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut44): results record, re-rank at cut 44, J16–J21 closed"
```

---

### Task 10: Final review, gate, merge

- [ ] **Step 1: Whole-branch review.** Run `superpowers:requesting-code-review` over
  `git diff main...HEAD`, against:
  - the spec's decisions;
  - the Global Constraints' pins;
  - the Review Focus.

  Land each fix as its own commit and record it in the results record §3.
- [ ] **Step 2: The gate, harness-tracked.** `run_in_background: true`:

```bash
cd ~/d/beliefs/.worktrees/cross-mount-eligibility && cd "$(pwd -P)" && set -o pipefail && just gate 2>&1 | tee ~/d/beliefs/.work/acceptance/cut44-gate.log
```
  Expected: the pytest summary line with zero failures, and TypeScript green.
- [ ] **Step 3: Close and merge**

```bash
tasks done <Task 10's id> "final review, gate green, merged"
tasks done beliefs-9ce6e4 "cut 44 discharged: citations over read mounts, session-wide acquisition invariants, eligibility classes in both checks, corpus-local reads refuse unheld inputs"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-9ce6e4 — cut 44 discharged"
cd ~/d/beliefs && git merge --no-ff cross-mount-eligibility -m "merge: mount citations — conformance cut 44"
```
  Fill the results record's §6 on `main`, then remove the worktree:
  1. run `tt-report`;
  2. check that no host pointer resolves into it;
  3. `git worktree unlock .worktrees/cross-mount-eligibility`;
  4. `git worktree remove .worktrees/cross-mount-eligibility`.

  Tell science's owner that `sci-dc0381` can start.

---

## Self-review

**Spec coverage.**

| Spec section | Where |
|---|---|
| decisions 1, 2, 4, 5, 6 | Tasks 1–2 |
| decision 3 (contract mismatch) | Task 1 (`_refuse_contract_mismatch`), J16-d |
| decision 3a (session producers, both directions, local reports) | Tasks 1–2, J16-f/h/i/j/k/l/m |
| decision 7 | Tasks 2–3 |
| decision 8 | Task 4 |
| decision 9 | Task 5 |
| decision 10 | Task 5 (J20, proof only) |
| decision 11 | Tasks 0, 7 |
| §3.1–§3.4 | Tasks 1–5 |
| §4 | `sci-dc0381` (filed), Task 10's handoff |
| §5, §6 | the Global Constraints' pins |
| §7 | Tasks 0 (bank), 6, 7, 9 (close) |
| §8 | Tasks 1–7 |
| §9 | Task 9 |
| §10 | the cut document §7 |
| §11 | Task 0 Step 4 |
| §13 | Tasks 2 (F4), 5 (B4b, J21), 8 (mm30 pin) |

**Placeholders.** Three are left to the implementer by instruction, each with the exact
module to copy from:
- the analysis-spec and composite cases (Task 2 Step 1), copied from their single-root
  tests;
- the J16-i and J16-j `before` strings (Task 7), spelled from the tree;
- helper import homes (Tasks 5, 6).

**Type consistency.**
- `MountCitations(own, own_profile, read_mounts)`, `.holder`, `.overlay`, `.close`.
- `_SessionOverlay(citations, base)`.
- `EligibilityOutcome(reason, unresolved=())`.
- `eligibility_outcome` and `eligibility_refusal` take `(view, node, profile, *, judge=None, reports=None)`.
- `validity_refusal(view, node, profile, *, reports=None)`.
- `CorpusWriter(..., read_mounts=None)`, `_citing()`, `_citation_view()`.
- `_record_findings(..., citations=None)`, and `_CapturedCitations.eligibility`.
- `InputOutsideCorpus(assessment, run, inputs)`.
- `CitationContractMismatch(root, namespace, held, writer)`.

**Review Focus.** Task 2 (1, 2, 3), Task 3 (4), Task 4 (5).

## Plan review log

- 2026-10-01: drafted from the spec approved after six rounds. Found at planning and
  recorded in the spec's §13:
  - B4's absent-dataset clause is superseded by J21;
  - F4 and B4b are re-targeted;
  - `eligibility_refusal` keeps its string, and `eligibility_outcome` carries the
    classes;
  - mm30's `biology` pin is the shipped pack's;
  - `producers-incomplete` refuses at the first incomplete lookup;
  - the portable fixtures.
- 2026-10-01, plan review round 1: revise, P1 1, P2 5, P3 1, all accepted after
  checking the code. The user also chose to keep J21 and supersede B4's clause by
  citation, and sequential subagent-driven execution with a fresh review per task.
  1. **P1.** Malformedness is keyed by canonical id. `_holder` now resolves an alias to
     the canonical record before checking it, and the alias regression was added.
  2. **P2.** `producers-incomplete` is judged per dataset. A known producer is
     definite, and the scan continues. `_ProducersIncomplete` is gone, and two
     regressions were added. Spec §13 is updated.
  3. **P2.** A run's `observes` is not read at write time. The J17 contention and
     duplicate tests (portable and durable) now cite through an assessment over a
     written run, plus a negative where the assessment cites only W.
  4. **P2.** `typed_estimand()` needs the testing contract. The portable, session and
     durable fixtures now use testing-capable profiles, and the world-audit tests keep
     `WITH_BIOLOGY` with the reason stated.
  5. **P2.** Durable J21 passes `gather`'s four arguments explicitly.
  6. **P2.** Durable J20 compares the split with a one-corpus baseline built from
     `seed_nodes()`, asserts attribution and lineage, and keeps the absent-carrier
     negative.
  7. **P3.** Tasks 0, 6, 7 and 8 run through `just test-one`.
- 2026-10-01, plan review round 2: revise, P2 3, all accepted after checking the code.
  1. Producer incompleteness now applies only when the unmapped dataset would otherwise
     pass. `_incomplete` runs `validity_refusal` with the known producers, so a missing
     facet, a basis, a known producer or an unresolved report each decide the dataset
     definitely. A regression covers a plain drift dataset with a corpus absent.
  2. J20's absent negative reads the pins once, while every manifest is present, and
     reuses them for the absent view.
  3. J20's lineage assertion now checks what the walk captured. While M is present,
     M's dataset is in `producers` (empty) and not in `not_present`. After removal, it
     is in `not_present` with M's id and has no producer entry.

