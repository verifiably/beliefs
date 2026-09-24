# Publish Act, Local — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the governed publish act for a local destination — step-0 selection, refusals, snapshot and request; staging, head export, sibling, replication and restore; the step-8 binding with the lifecycle entries; exact resumption; marker-required arrival — and discharge Y5–Y10 as conformance cut 40.

**Architecture:** `beliefs/durable.py` is the create-only write. `beliefs/publish_request.py` holds the pure step-0 pieces: the closure rule, the pins derivation, and the snapshot and request codecs. `report.py` gains four lifecycle entry kinds and one ordered-sequence rule, which the constructors, the stored mirror and the orphan fold all read. `publication_doors.py` gains `expected_view`, `lifecycle`, the pre-binding refusal door and the attempt's completion reading. `corpus.py` gains two staging doors. `beliefs/publish.py` is the act: `publish`, `resume_publish` and `pending_publishes`, built from named step functions over `root.py`'s lifecycle wrappers. `beliefs/publication_arrival.py` is the recipient's door.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, `nodes` records, the acceptance harness under `python/tests/acceptance/` and the N2 audit.

**Spec:** `docs/superpowers/specs/2026-09-23-publish-act-local-design.md`, approved 2026-09-23 at `8cd59d3` after one user review (its §18). Read it first; every task cites its sections and decisions.

## Global Constraints

- **Baseline is `main` at `b9cd8b6`** (`git merge-base main design/publish`). Work in `.worktrees/publish` (branch `design/publish`, locked "on WORK_ROOT storage"). Paths below are relative to the repository root; paths shown to the user carry the `.worktrees/publish/` prefix. The main checkout is `~/d/beliefs`. For the fast loop in the worktree: `export SCIENCE_CUT4_ROOT=$(readlink -f ~/d/beliefs)/.cut4-acceptance SCIENCE_CUT10_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test`, and run pytest from the canonical path (`cd "$(pwd -P)"`): about 190 `CapabilityUnavailable` failures mean a missing export, and `ELOOP` from `open_root` means the `.worktrees` symlink is in the cwd (memories `worktree-on-work-root-needs-cut-root-exports`, `run-pytest-from-the-canonical-worktree-path`).
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  - For this lane: `publish.py`, `publish_request.py`, `durable.py` and `publication_arrival.py` import nothing of `atoms`. `publish.py` reaches the lifecycle only through `root.py`'s wrappers and `LifecycleState` as `root.py` re-exports it.
  - Three new callers of primitives join `WRITE_ENTRY_POINTS` with a `Case` each (Task 5):
    - `"corpus.py:CorpusWriter._stage_record": "corpus-write"`, since `self._corpus.add` is a primitive (`test_permit_boundary.py` `_is_primitive_call`);
    - `"corpus.py:CorpusWriter._stage_marker": "publish"`;
    - `"publication_doors.py:_refuse_publication": "publish"`, which calls `execute_fulfilling`.
  - Tasks 3 and 5 run `test_permit_boundary.py`, `test_permit_entry_points.py` and `test_capability_boundary.py` green.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. Here that is Task 9, Step 4, with `(cut40, 40, (15, 15, 6))`.
- **The declared accounting is 15 arms, 15 declaration units, 6 rows (Y5–Y10)**, unless Task 0's engine probes refuse a fact an arm relies on. In that case the arm is declared unrun, the row is reported **partial**, and the cut document freezes the reduced counts (memory `cut-classification-any-unrun-arm-is-partial`). Every later mention of the accounting reads the frozen cut document's §4.
- **Frozen declarations and cut bodies stay byte-exact.** Cut 40 chains **cut 39's** runner (`PREFIX_RUNNERS = ("cut39_acceptance.py",)`). Cut 39's live arms pin these lines, and every edit must leave each occurring **exactly once in its module**:
  - `publication_doors.py`:
    - `        tips, markers = _judge(writer, resolver, opened, seam)`
    - the `tips = standing_at(…position=opened.digest…)` line in `_judge`
    - `        anchors.sort(key=lambda anchor: anchor.corpus_id)`
    - `    binding = binding_record(intent, corpus_id=corpus_id, marker=marker, artifact=artifact)`
    - `        return [writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]`
    - `            if outcome["type"] != "bound" and outcome.get("remotely_revealed") is True:`
    - `        if type(records) is PositionRefused:\n            yield intent, records\n            continue`
  - `corpus.py`: `revise_coordination`'s seven-line guard block (cut 39's Y1-a).
  - Tasks 2, 3, 5 and 6 end by running `tests/test_arm_staleness.py`. A stale prior arm means an edit moved a pinned line: restore its spelling and put the new code beside it. Never edit a prior declaration (memory `staleness-probe-baseline-is-the-trees-output`).
- **Decisions the code must honour verbatim** (spec §2):
  1. local first, and a `remote` destination refuses `ValidationRefused("remote destinations arrive in cut 41")`;
  2. the selection is snapshotted at step 0 into `selection.v1`, written create-only before `request.v1`, and every later step reads only the snapshot;
  3. the act reads `current_epoch(world)`, never builds an epoch, and evaluates before the written root's lock; `_open_publication` re-checks the pin (`view-revised`);
  4. a local destination is a container, holding `<destination>/<corpus_id>`, its `.metadata` sibling (`metadata_root_for`) and `<destination>/<corpus_id>.head-artifact.v1`;
  5. staging is written through `_stage_record` and `_stage_marker` only;
  6. `publishes()` is the one kernel permit for the whole act (`publish` over `publication-binding` and `publication`; `corpus-write` over `act-report` and every world kind; `lifecycle`; `registry`), and every acceptance arm publishes under exactly `scoped_authority(RequiredCapabilities.publishes(), ACTOR)`;
  7. one terminal report per attempt, its lifecycle entries in step order;
  8. resumption by reinvocation;
  9. resuming requires the intent's actor;
  10. `admit_publication` is its own door.
- **Detached runs go through the reaping wrapper** (Processes rule). Launch the cut runner and the gate with `setsid nohup ~/d/beliefs/.work/acceptance/detached.sh <log> <cmd…> > /dev/null 2>&1 &`, after `test -x` on the wrapper. The end-of-turn report that leaves one running names its process group (`cat <log>.pid`) and the stop command (`kill -TERM -- "-$(cat <log>.pid)"`), after `host-load --section session`.
- **Commits:**
  - Use conventional commits, with no attribution trailers.
  - Run `tasks check` before every commit.
  - Use `just test-fast` while working. Never run the full suite after every edit (AGENTS.md).
  - Run every `pytest` from `python/` with `uv run --frozen`.
  - Make no TypeScript changes, and leave both `CONTRACT.yaml` copies of the base contract unchanged.

## Review Focus

These are the inputs a person meets that the spec's arms do not pin. Each line names the test that pins it and the task that owns it.

1. **A selection whose records carry a relation `source` other than themselves.** `topic_nodes`' `d_a` carries `r_b → d_a`. The closure must read both endpoints and resolve each through the view, so a stored alias does not read as missing. Pinned by `test_closure_reads_both_endpoints_and_resolves_aliases` in Task 4.
2. **A destination path that is a file, a symlink, or the operations root itself.** Each must refuse `destination-unusable` before the intent, rather than letting `replicate_root` fail after the intent. Pinned by `test_destination_checks` in Task 4.
3. **A second `publish` of the same view to the same destination while the first attempt's staging is still on disk** (the first crashed and was never resumed). The second must use its own token's directories and never touch the first's. Pinned by `test_two_attempts_do_not_share_directories` in Task 8, inside Y8-a's module.
4. **A resume whose caller holds another actor, or whose `staging_profile` disagrees with the request's pins.** Both must refuse with nothing written, not as a terminal report. Pinned by `test_resume_refuses_another_actor_and_another_profile_writing_nothing` in Task 6.
5. **An operations root on a path containing a symlink** (the `.worktrees` case). `write_create_only` must work on the resolved path, and the act resolves `operations_root` and `destination.locator` once, at entry. Pinned by `test_write_create_only_resolves_its_directory` in Task 1.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-09-22-publication-design.md` | Y5–Y10 appended (Task 0) |
| `docs/designs/<freeze date>-conformance-cut-40.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py`, the ledger, the roadmap | freeze and totals: 226 rows (Task 0) |
| `python/tests/test_publish_engine_order.py` (new) | the engine facts the act relies on (Task 0) |
| `python/src/beliefs/durable.py` (new), `python/tests/test_durable.py` (new) | `write_create_only`, `ensure_directory` (Task 1) |
| `python/src/beliefs/errors.py` | `CreateOnlyCollision` (Task 1); `PublicationRefused` gains `refs`, `corpus_ids`, `field`; `PublicationArrivalRefused` (Task 3) |
| `python/src/beliefs/report.py`, `python/src/beliefs/stored.py`, `python/src/beliefs/boundary.py` | lifecycle entries and outcomes, `publish_sequence_error`, `publish_entries_from_facet`, the stored mirror, `_mint_publish_report(lifecycle=)`, `_mint_publish_refusal` (Task 2) |
| `python/src/beliefs/publication_doors.py` | `PreBinding` and the fold (Task 2); `expected_view`, `lifecycle`, `_refuse_publication`, `AttemptReading`, `attempt_reading` (Task 5) |
| `python/tests/test_report.py`, `python/tests/test_publication_doors.py` | Task 2's and Task 5's unit tests |
| `python/src/beliefs/permit.py`, `python/tests/test_permit.py` | the widened `publishes()` (Task 3) |
| `python/src/beliefs/publish_request.py` (new), `python/tests/test_publish_request.py` (new) | closure, pins, snapshot, request (Task 4) |
| `python/src/beliefs/corpus.py` | `_stage_record`, `_stage_marker` (Task 5) |
| `python/tests/test_permit_boundary.py`, `python/tests/test_permit_entry_points.py` | three entry points and their `Case`s (Task 5) |
| `python/src/beliefs/publish.py` (new), `python/tests/test_publish.py` (new) | the act (Task 6) |
| `python/src/beliefs/publication_arrival.py` (new), `python/tests/test_publication_arrival.py` (new) | `admit_publication` (Task 7) |
| `python/tests/acceptance/test_publish_act_acceptance.py` (new) | the fifteen units (Task 8) |
| `python/tests/n2_arms_cut40.py`, `python/tests/acceptance/n2_arms_cut40.py`, `python/tests/acceptance/test_n2_cut40.py`, `python/tools/cut40_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, recent-cut row (Task 9) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | §19 (Task 10) |
| `docs/plans/<date>-conformance-cut-40-results.md` (new) and the amended documents | discharge (Task 11) |

---

### Task 0: Freeze cut 40, bank Y5–Y10, pin the engine facts

**Files:**
- Create: `docs/designs/<freeze date>-conformance-cut-40.md`, `python/tests/test_publish_engine_order.py`
- Modify: `docs/designs/2026-09-22-publication-design.md`, `python/tests/test_designs_corpus.py`, `README.md`, `docs/guide/contracts-and-adoption.md`, the ledger, the roadmap (via `python/tools/roadmap_status.py`), the spec (planning notes), tasks through the CLI

**Interfaces:**
- Produces:
  - the frozen cut body the guard pins (Task 9 reads its freeze commit and digest);
  - the engine verdicts `INIT_RETRY`, `ADMIT_RETRY`, `EXPORT_STABLE`, `REPLICATE_RETRY`, `REPLICATE_AFTER_RESTORE` and `READ_SERVICEABLE`, each `"holds"` or a refusal text, which decide whether any arm is declared unrun, and `FOREIGN_REPLICA`, the exception type a foreign occupant raises.

- [ ] **Step 1: Confirm cut 40 is unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -q "conformance-cut-4[0-9]" && echo "claimed on $b"; done; echo scan done
git worktree list
```
Expected: `scan done` alone, and the worktrees are `main` and `.worktrees/publish` (memory `cut-number-check-scans-every-worktree`).

- [ ] **Step 2: Pin the engine facts** in `python/tests/test_publish_engine_order.py`. The act's resumption (spec §2 decision 8, §9) reinvokes each lifecycle operation and trusts its predicate. These tests pin that the predicates converge, from beliefs' side, on the certified volume:

```python
"""The engine facts the publish act's resumption relies on (publish-act-local
design §2 decision 8, §9): each reinvoked lifecycle operation converges on the
state its first call left. Tests may import `atoms`; the source modules do not."""

from __future__ import annotations

import os
import shutil
from itertools import count

import pytest
from authority import FULL
from profiles import BASE, pins_for

from beliefs.root import (
    LifecycleState,
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import Fresh, WorldConfig
from beliefs.world.anchors import CorpusSubject
from beliefs.world.registry import load_manifest
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.corpus import ReadView

_counter = count()


@pytest.fixture()
def staged(certified_work):
    """A corpus admitted into its own one-carrier world, as step 1 builds it."""
    stem = certified_work / f"publish-engine-{os.getpid()}-{next(_counter)}"
    corpus, world_root, export = stem / "staging", stem / "world", stem / "dest" / "exported"
    (stem / "dest").mkdir(parents=True)
    try:
        init_corpus_root(corpus, authority=FULL)
        open_corpus(corpus, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        config = WorldConfig(world_root, "e" * 32, (corpus,))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus, provenance=Fresh())
        yield corpus, config, world, export
    finally:
        for path in (corpus, world_root, export):
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)
        shutil.rmtree(stem, ignore_errors=True)


def test_init_retry_converges(staged):
    """INIT_RETRY: both initializers, reinvoked, change nothing and raise nothing."""
    corpus, config, _, _ = staged
    init_corpus_root(corpus, authority=FULL)
    init_world_root(config, authority=FULL)
    open_world(config, authority=FULL)


def test_admit_retry_converges(staged):
    """ADMIT_RETRY: the same fresh adoption again returns an equal record."""
    corpus, config, world, _ = staged
    again = open_world(config, authority=FULL).admit(corpus, provenance=Fresh())
    assert again.manifest.corpus_id == load_manifest(corpus).corpus_id


def test_export_is_stable(staged):
    """EXPORT_STABLE: a pure function of the chain."""
    corpus, _, world, _ = staged
    subject = CorpusSubject(load_manifest(corpus).corpus_id)
    assert export_head_artifact(world, subject) == export_head_artifact(world, subject)


def test_replicate_retry_after_completion_converges(staged):
    """REPLICATE_RETRY: a completed replication, retried exactly, returns the
    same operation id and leaves the replica read-only and unserviceable."""
    corpus, _, _, export = staged
    first = replicate_root(corpus, export, authority=FULL)
    second = replicate_root(corpus, export, authority=FULL)
    assert first == second
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_UNSERVICEABLE


def test_replicate_retry_after_restore_converges(staged):
    """REPLICATE_AFTER_RESTORE: a replication retried exactly after its copy was
    restored returns the same operation id and leaves the copy serviceable —
    the resume after a crash past step 6 reinvokes it (finding 2)."""
    corpus, _, world, export = staged
    corpus_id = load_manifest(corpus).corpus_id
    artifact = export_head_artifact(world, CorpusSubject(corpus_id))
    first = replicate_root(corpus, export, authority=FULL)
    restore_root(export, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=FULL)
    assert replicate_root(corpus, export, authority=FULL) == first
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE


def test_replicate_over_a_foreign_serviceable_root_refuses(staged, certified_work):
    """FOREIGN_REPLICA: another corpus's serviceable replica at the export path
    refuses this replication. The exception type is recorded for Task 8."""
    corpus, _, world, export = staged
    other = certified_work / f"publish-engine-foreign-{os.getpid()}-{next(_counter)}"
    try:
        init_corpus_root(other, authority=FULL)
        open_corpus(other, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        replicate_root(other, export, authority=FULL)
        with pytest.raises(Exception) as refused:
            replicate_root(corpus, export, authority=FULL)
        print(f"FOREIGN_REPLICA = {type(refused.value).__module__}.{type(refused.value).__name__}")
    finally:
        shutil.rmtree(other, ignore_errors=True)
        shutil.rmtree(metadata_root_for(other), ignore_errors=True)


def test_a_restored_replica_reads_and_stays_serviceable(staged):
    """READ_SERVICEABLE: restore against the exported artifact validates, and a
    ReadView opens the serviceable copy (admit_publication's read)."""
    corpus, _, world, export = staged
    corpus_id = load_manifest(corpus).corpus_id
    artifact = export_head_artifact(world, CorpusSubject(corpus_id))
    replicate_root(corpus, export, authority=FULL)
    report = restore_root(export, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=FULL)
    assert report.outcome == "validated"
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE
    assert tuple(ReadView.opened_at(export).iter_stored()) == ()
```

```bash
cd python && uv run --frozen pytest tests/test_publish_engine_order.py -q
```
Expected: 7 passed (run with `-s` once to read the printed `FOREIGN_REPLICA` type). Record each verdict as `"holds"`, and `FOREIGN_REPLICA` as the printed exception type: Task 8's foreign-occupant test asserts exactly it.
- `test_replicate_over_a_foreign_serviceable_root_refuses` probes an unserviceable foreign replica. If the engine instead *accepts* it (the probe fails because nothing raised), a foreign occupant would be adopted as this attempt's copy: park `--reason decision`, since the spec's identity argument rests on that refusal.
- If `test_admit_retry_converges` fails, the admission record type may name its field differently. Read `AdmissionRecord` (`grep -n "class AdmissionRecord" -A12 src/beliefs/world/registry.py`), fix the assertion's attribute, and re-run. Only a raised refusal counts as a failing fact.
- If a fact fails, `tasks note beliefs-328507` the refusal text. Then park `--reason decision`: every resumption row the spec lists depends on these six, so nothing later is built on an unpinned fact.
- `ReadView` is imported from `beliefs.corpus`; if that fails, find its home with `grep -rn "^class ReadView" src/beliefs`.

- [ ] **Step 3: Bank Y5–Y10.** Append the six rows to the table in `docs/designs/2026-09-22-publication-design.md`, copied byte for byte from the spec's §13 (`grep -n '^| \*\*Y\(5\|6\|7\|8\|9\|10\)\*\*' docs/superpowers/specs/2026-09-23-publish-act-local-design.md`). Change its status line to: "Y1–Y4 closed at cut 39; Y5–Y10 banked with conformance cut 40's freeze (`../superpowers/specs/2026-09-23-publish-act-local-design.md` §13)".

In `python/tests/test_designs_corpus.py`, change `"Y": ("Y1", "Y2", "Y3", "Y4"),` to `"Y": ("Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "Y10"),`. The total moves from 220 to 226 rows. The table count stays at twenty-one. Update:
- `README.md` ("**226 rows** across **twenty-one frozen tables**");
- `docs/guide/contracts-and-adoption.md` (its "220 rows across twenty-one" sentence and its totals line);
- the ledger's `Current state` (Y5–Y10 open under `publish`);
- the roadmap's accounting paragraph ("193 of 226 rows closed, with 33 open") and Appendix A, regenerated with `cd python && uv run --frozen python tools/roadmap_status.py`. Expected: `Closed 193 of 226; open 33.`

- [ ] **Step 4: Write the cut document.** Use cut 39's shape (`sed -n 1,120p docs/designs/2026-09-23-conformance-cut-39.md` first). Header:

```markdown
# Conformance cut 40 — the publish act, local

**Status:** frozen <date>, before implementation; Y5–Y10 are open
**Design:** `../superpowers/specs/2026-09-23-publish-act-local-design.md`, approved 2026-09-23 at `8cd59d3` after one user review; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-23-publish-act-local.md`.
**Numbered after** cut 39 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 40 or above at freeze.
```

Then these sections:
- **§1, what the cut is:** spec §1, condensed.
- **§2, the boundary:** every file in this plan's file map from Task 1 to Task 9, and "Frozen declarations and cut bodies through cut 39 remain byte-exact."
- **§3, selection:** the six Y rows from Step 3, then the unit table from spec §14.2 as amended by Step 5's planning notes (fifteen rows, Y5-a through Y10-b, with the assertion column).
- **§4, accounting:** "**15 arms, 15 declaration units**, six rows; Y5–Y10 open and close; recent-cut row `(15, 15, 6)`; Task 8 passes <n>; 193 of 226 → 199 of 226". Here `<n>` is fifteen plus the parametrized cases Task 8 declares: Y5-a's refusal cases and Y9-a's boundaries. Write the number Task 8's parametrization yields, counted from the plan's Task 8 code. If Step 2 left a fact unrun, state which arm is unrun, the reduced counts, and that the row is **partial**.
- **§5, N2 and acceptance obligations:** the sabotage table from Task 9 Step 1, the six engine verdicts and `FOREIGN_REPLICA` from Step 2, `PREFIX_RUNNERS = ("cut39_acceptance.py",)` and `PHASE_MODULES = ("test_publish_act_acceptance.py", "test_n2_cut40.py")`.
- **§6, second reader:** check that:
  - every arm publishes under exactly `publishes()`;
  - Y6-a's drift happens after the intent is appended and before the snapshot is written;
  - Y7-a counts `_stage_record` calls on the resume;
  - Y9-a's crashes discard in-memory state (fresh `open_corpus`) before `resume_publish`;
  - Y10-b's root verifies its chain, so the refusal is the marker check's.
- **§7, limitations:** spec §16.

- [ ] **Step 5: README, guide, the planning notes in the spec.** In `README.md`:
- add 1 to the designs count word;
- add a table row after cut 39's: `| \`<freeze date>-conformance-cut-40.md\` | the frozen publish-act cut: request, snapshot, staging, export, the local reveal, resumption and marker-required arrival; Y5–Y10 read, 15 declaration units, the cut 39 runner as prefix |`.

In `docs/guide/contracts-and-adoption.md`, add the frozen-not-discharged paragraph and the cut-40 path to the cut list, both on cut 39's shape. `test_designs_corpus.py`'s number word table needs no entry, since the count stays twenty-one.

Append this planning note under the spec's §18. It records every interface the plan fixes where the spec named another, or named none:

```markdown
- 2026-09-23 — at planning (plan `../plans/2026-09-23-publish-act-local.md`):
  - **The staging profile is the caller's.** The kernel has no function that
    compiles a `ProfileSpec` from pin identities, and `adopt_manifest` writes
    only its writer's own profile's pins. So `publish` and `resume_publish` take
    `staging_profile: ProfileSpec`, and step 0 refuses `profile-disagrees`
    (a new `PublicationRefused` reason, before the intent) when its pins are not
    the derived pins. A resume with another profile refuses `ValidationRefused`
    and writes nothing, like an actor mismatch (decision 9).
  - **`_stage_record` applies the record-local refusals only**: document
    validation, already minted, the rendering equal to the snapshot text, and
    collision. It skips the view-reading refusals `_refuse` also applies
    (supersedes and assesses targets, composite members, verification), since
    population runs in id order, not dependency order, and every selected
    record passed those checks where it was minted.
  - **`staging-corrupt` carries `refs`**, a tuple of zero or one record ids,
    not a nullable record. The identity encoding refuses null, and
    `corpus_id` is always known, since every staging-corrupt case is found
    after the manifest exists.
  - **`PublishRefused` carries the last entry's outcome type** (for example
    `staging-corrupt` or `predecessor-not-standing`), not the report. A resume
    that finds a closed attempt reads the outcome from the chain's report and
    holds no `ActReport` value. `Unresolved` is named `PublishUnresolved`,
    since `world.selection.Unresolved` exists.
  - **The completion reading is `publication_doors.attempt_reading`.** It reads
    the written chain by the fold's own rule (`_reports_at`): no committed
    fulfilment is `unfinished`; a report that is present, matching and
    qualifying is `closed`; a report the fold refuses is `indeterminate`.
  - **The head artifact's content identity** (the binding's `artifact`) is the
    SHA-256 of the artifact's canonical bytes, the bytes the sibling holds.
  - **`_bind_publication(lifecycle=())` and `_open_publication(expected_view=None)`
    default to cut 39's behaviour.** Cut 39's frozen tests call both doors
    bare, and the ordered-sequence rule admits a lone binding entry, which the
    act never writes.
  - **Crashes are injected by monkeypatching the act's named step functions**
    (`beliefs.publish._initialize`, `_populate`, `_admit_and_export`,
    `_write_sibling`, `_replicate`, `_restore`, `_bind`, `_discard`), not
    through a fault parameter on the act.
  - **Six arms are reshaped so that each check sees its sabotage:**
    - Y5-a's sabotage makes the closure read relation targets only. The rule is
      one loop over every world relation, so a `composes`-only sabotage would
      need a special case the code does not have; the composite amendment is
      pinned by a unit test instead.
    - Y6-a's drift is committed between the intent and the snapshot write, and
      its sabotage re-evaluates the selection after the intent. The written
      root is not a world corpus, so the drift is a record added to a
      contributing corpus.
    - Y9-c asserts that `pending_publishes` lists a crashed attempt and omits a
      done one and a requestless intent. Its sabotage drops the `unfinished`
      filter: `pending_publishes` enumerates request files, so a requestless
      intent is never a candidate.
    - Y9-d's sabotage skips step 9 on the done branch of `resume_publish`.
    - Y10-a also admits nothing from a plain replica with no marker, and its
      sabotage removes the marker count. `marker_consistent` is not
      independently observable: the content rule already checks uid and
      address, and the id follows from both.
    - Y10-b's sabotage checks selection membership one way only.
  - **The destination and the operations root are resolved once, at entry**
    (`Path.resolve()`), and neither may lie inside the other.
```

Update spec §3's `PublishOutcome` table and §14's two tables to match these notes, and change the spec's `Status` line to "approved 2026-09-23; frozen as cut 40 on <date>".

The plan's step children exist, filed with the plan, each depending on its predecessor:
- Task 0 `beliefs-e55483`, Task 1 `beliefs-64c176`, Task 2 `beliefs-95368c`, Task 3 `beliefs-871506`;
- Task 4 `beliefs-bd21d1`, Task 5 `beliefs-b07d23`, Task 6 `beliefs-c58c49` (high), Task 7 `beliefs-a3bce5`;
- Task 8 `beliefs-20eae3` (high), Task 9 `beliefs-c5e5ea`, Task 10 `beliefs-53192c`, Task 11 `beliefs-b103bf`, Task 12 `beliefs-e9d93c`.

`tasks start` each child before its task, and `tasks done` it in that task's commit. Every `<Task N's id>` below is its id from this list.

- [ ] **Step 6: Verify and commit the freeze**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py tests/test_publish_engine_order.py -q
cd .. && tasks note beliefs-328507 "Cut 40 frozen: INIT_RETRY, ADMIT_RETRY, EXPORT_STABLE, REPLICATE_RETRY, REPLICATE_AFTER_RESTORE, READ_SERVICEABLE = <verdicts>; FOREIGN_REPLICA = <type>; accounting 15/15/6; chains cut 39."
tasks check && git add docs README.md python/tests/test_designs_corpus.py python/tests/test_publish_engine_order.py tasks
git commit -m "docs(cut): freeze conformance cut 40, the publish act (local); bank Y5–Y10"
git rev-parse HEAD; sha256sum docs/designs/*-conformance-cut-40.md
```
Record the commit hash as `CUT40_FREEZE_COMMIT` and the digest as `CUT40_FROZEN_SHA256`, both for Task 9.

---

### Task 1: The durable create-only write

**Files:**
- Create: `python/src/beliefs/durable.py`, `python/tests/test_durable.py`
- Modify: `python/src/beliefs/errors.py`

**Interfaces:**
- Produces:
  - `write_create_only(path: Path, data: bytes) -> Literal["created", "present"]`, which raises `CreateOnlyCollision`;
  - `ensure_directory(path: Path) -> None`;
  - `CreateOnlyCollision(WriteRefused)` with `.path`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_durable.py`:

```python
"""The durable create-only write (publish-act-local design §4.4)."""

from __future__ import annotations

import os

import pytest

from beliefs import durable
from beliefs.durable import ensure_directory, write_create_only
from beliefs.errors import CreateOnlyCollision


def test_a_fresh_name_is_created_and_fsynced(tmp_path):
    target = tmp_path / "request.v1"
    assert write_create_only(target, b"one") == "created"
    assert target.read_bytes() == b"one"
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_identical_bytes_at_the_name_are_present(tmp_path):
    target = tmp_path / "request.v1"
    write_create_only(target, b"one")
    assert write_create_only(target, b"one") == "present"


def test_different_bytes_at_the_name_collide_and_leave_the_file(tmp_path):
    target = tmp_path / "request.v1"
    write_create_only(target, b"one")
    with pytest.raises(CreateOnlyCollision) as caught:
        write_create_only(target, b"two")
    assert caught.value.path == target and target.read_bytes() == b"one"
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_a_leftover_temporary_is_removed_first(tmp_path):
    (tmp_path / ".request.v1.0123456789abcdef.tmp").write_bytes(b"partial")
    write_create_only(tmp_path / "request.v1", b"one")
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_the_final_name_never_shows_partial_bytes(tmp_path, monkeypatch):
    def failing_link(src, dst):
        raise OSError("cut before the link")

    monkeypatch.setattr(durable.os, "link", failing_link)
    with pytest.raises(OSError):
        write_create_only(tmp_path / "request.v1", b"one")
    assert not (tmp_path / "request.v1").exists()


def test_a_retry_after_a_death_before_the_directory_fsync_syncs_it(tmp_path, monkeypatch):
    real = durable._fsync_directory

    def dying(directory):
        raise OSError("died after the link, before the directory fsync")

    monkeypatch.setattr(durable, "_fsync_directory", dying)
    with pytest.raises(OSError):
        write_create_only(tmp_path / "request.v1", b"one")
    assert (tmp_path / "request.v1").read_bytes() == b"one"
    synced = []
    monkeypatch.setattr(durable, "_fsync_directory", lambda directory: synced.append(directory) or real(directory))
    assert write_create_only(tmp_path / "request.v1", b"one") == "present"
    assert synced == [tmp_path.resolve()]


def test_write_create_only_resolves_its_directory(tmp_path):
    """Review Focus 5: a symlinked directory component is resolved, not refused."""
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "link").symlink_to(real)
    assert write_create_only(tmp_path / "link" / "request.v1", b"one") == "created"
    assert (real / "request.v1").read_bytes() == b"one"


def test_data_must_be_bytes(tmp_path):
    with pytest.raises(TypeError):
        write_create_only(tmp_path / "request.v1", "one")  # type: ignore[arg-type]


def test_ensure_directory_creates_every_missing_component(tmp_path):
    ensure_directory(tmp_path / "a" / "b" / "c")
    assert (tmp_path / "a" / "b" / "c").is_dir()
    ensure_directory(tmp_path / "a" / "b" / "c")


def test_ensure_directory_refuses_a_file_in_the_way(tmp_path):
    (tmp_path / "a").write_bytes(b"")
    with pytest.raises(FileExistsError):
        ensure_directory(tmp_path / "a" / "b")
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_durable.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'beliefs.durable'`.

- [ ] **Step 3: Implement.** In `errors.py`, beside `PublicationRefused`:

```python
class CreateOnlyCollision(WriteRefused):
    """A create-only name already holds other bytes (publish-act-local design §4.4)."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"{path}: a create-only name already holds other bytes")
        self.path = path
```
(add `from pathlib import Path` to `errors.py`'s imports if it is not there). `python/src/beliefs/durable.py`:

```python
"""The durable create-only write (layer design §6.1 step 0; publish-act-local
design §4.4): temporary name, fsync, a create-only link, fsync of the directory.
Partial bytes never appear at the final name. Plain POSIX, outside every root —
the operations root and the head artifact's sibling have no engine boundary."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Literal

from beliefs.errors import CreateOnlyCollision

__all__ = ["ensure_directory", "write_create_only"]


def _fsync_directory(directory: Path) -> None:
    handle = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def ensure_directory(path: Path) -> None:
    """Create every missing component of `path`, fsyncing each new entry's parent."""
    target = Path(path).resolve()
    missing: list[Path] = []
    probe = target
    while not probe.exists():
        missing.append(probe)
        probe = probe.parent
    for directory in reversed(missing):
        directory.mkdir()
        _fsync_directory(directory.parent)
    if not target.is_dir():
        raise FileExistsError(f"{target} exists and is not a directory")


def write_create_only(path: Path, data: bytes) -> Literal["created", "present"]:
    """Publish `data` at `path` create-only: identical bytes already there are
    `present`, different bytes raise `CreateOnlyCollision`."""
    if type(data) is not bytes:
        raise TypeError("a create-only write takes bytes")
    target = Path(path).parent.resolve() / Path(path).name
    directory = target.parent
    for leftover in directory.glob(f".{target.name}.*.tmp"):
        leftover.unlink()
    temporary = directory / f".{target.name}.{secrets.token_hex(8)}.tmp"
    handle = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(handle, view)
            view = view[written:]
        os.fsync(handle)
    finally:
        os.close(handle)
    try:
        os.link(temporary, target)
    except FileExistsError:
        temporary.unlink()
        if target.read_bytes() != data:
            raise CreateOnlyCollision(target) from None
        # an earlier call may have died after its link and before its directory
        # fsync: the retry completes that obligation before answering (finding 5)
        _fsync_directory(directory)
        return "present"
    except BaseException:
        temporary.unlink()
        raise
    temporary.unlink()
    _fsync_directory(directory)
    return "created"
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_durable.py -q`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/durable.py python/src/beliefs/errors.py python/tests/test_durable.py tasks
git commit -m "feat(publish): the durable create-only write (Y6, Y8)"
```

---

### Task 2: The lifecycle entries, the ordered sequence, and the fold

**Files:**
- Modify: `python/src/beliefs/report.py`, `python/src/beliefs/stored.py` (`_valid_report_entry`, `act_report_facet`), `python/src/beliefs/boundary.py` (`_mint_publish_report`, new `_mint_publish_refusal`), `python/src/beliefs/publication_doors.py` (`PreBinding`, `_reports_at`, `marker_tips_at`)
- Test: `python/tests/test_report.py`, `python/tests/test_publication_doors.py`

**Interfaces:**
- Produces:
  - outcomes `RequestCorrupt(reason)`, `Staged(corpus_id, records)`, `StagingCorrupt(corpus_id, reason, refs)`, `Exported(corpus_id, artifact)`, `ExportCollision(corpus_id, sibling)`, `Revealed(corpus_id)` and `RevealRefused(corpus_id, verdict)`;
  - entries `PublicationRequestEntry`, `PublicationStagingEntry`, `PublicationExportEntry` and `PublicationRevealEntry`, each `(subject, outcome)`;
  - `publish_sequence_error(entries) -> str | None` and `publish_entries_from_facet(entries: object) -> tuple[Entry, ...]`, the second raising `MalformedRecord`;
  - `outcome_type(outcome) -> str`;
  - `boundary._mint_publish_report(intent, *, observer, instrument, opened_at, closed_at, entry, lifecycle=())` and `boundary._mint_publish_refusal(intent, *, observer, instrument, opened_at, closed_at, entries)`;
  - `publication_doors.PreBinding(outcome: str)`.

- [ ] **Step 1: Write the failing tests.** Append to `python/tests/test_report.py`:

```python
# --- publish-act-local §7: the lifecycle entries and the ordered sequence ------

from beliefs.report import (
    Exported,
    ExportCollision,
    PublicationExportEntry,
    PublicationRequestEntry,
    PublicationRevealEntry,
    PublicationStagingEntry,
    RequestCorrupt,
    Revealed,
    RevealRefused,
    Staged,
    StagingCorrupt,
    publish_entries_from_facet,
    publish_sequence_error,
)

_S = "coord:" + "a" * 32 + "/" + "d" * 32
_C = "1" * 32


def _lifecycle(stop: str | None = None):
    staged = PublicationStagingEntry(_S, Staged(_C, 3))
    exported = PublicationExportEntry(_S, Exported(_C, "f" * 64))
    revealed = PublicationRevealEntry(_S, Revealed(_C))
    return {
        None: (staged, exported, revealed),
        "staging": (PublicationStagingEntry(_S, StagingCorrupt(_C, "extra", ("dataset:x",))),),
        "export": (staged, PublicationExportEntry(_S, ExportCollision(_C, f"{_C}.head-artifact.v1"))),
        "reveal": (staged, exported, PublicationRevealEntry(_S, RevealRefused(_C, "refuted"))),
    }[stop]


def _binding():
    return PublicationBindingEntry(_S, BindingBound("c" * 32, _C, "2" * 32))


@pytest.mark.parametrize(
    "entries",
    [
        (PublicationRequestEntry(_S, RequestCorrupt("snapshot-mismatch")),),
        _lifecycle("staging"),
        _lifecycle("export"),
        _lifecycle("reveal"),
        (*_lifecycle(), _binding()),
        (_binding(),),                                     # cut 39's lone binding entry
    ],
    ids=["request", "staging", "export", "reveal", "bound", "lone-binding"],
)
def test_the_admitted_publish_sequences(entries):
    assert publish_sequence_error(entries) is None


@pytest.mark.parametrize(
    "entries",
    [
        (),
        _lifecycle(),                                      # every lifecycle entry succeeded, no binding
        (_lifecycle()[1], _lifecycle()[0], _lifecycle()[2], _binding()),   # out of order
        (*_lifecycle("staging"), _lifecycle()[1]),         # an entry after a refusal
        (_lifecycle()[0], _binding()),                     # a binding after a partial lifecycle
        (PublicationRequestEntry(_S, RequestCorrupt("undecodable")), _binding()),
        (PublicationStagingEntry("coord:other", Staged(_C, 1)), *_lifecycle()[1:], _binding()),  # two subjects
    ],
    ids=["empty", "no-binding", "order", "after-refusal", "partial", "request-then-binding", "subjects"],
)
def test_every_other_sequence_is_refused(entries):
    assert publish_sequence_error(entries) is not None


@pytest.mark.parametrize(
    "build",
    [
        lambda: RequestCorrupt("other"),
        lambda: Staged(_C, 0),
        lambda: Staged(_C, True),
        lambda: Staged("x", 1),
        lambda: StagingCorrupt(_C, "extra", ("a", "b")),
        lambda: StagingCorrupt(_C, "pins-foreign", ["dataset:x"]),
        lambda: StagingCorrupt(_C, "unknown", ()),
        lambda: Exported(_C, "f" * 63),
        lambda: ExportCollision(_C, "other.head-artifact.v1"),
        lambda: RevealRefused(_C, "validated"),
    ],
)
def test_each_lifecycle_outcome_refuses_its_malformed_forms(build):
    with pytest.raises(MalformedRecord):
        build()


def test_the_stored_form_decodes_to_the_same_sequence():
    from beliefs.report import _entry_facet

    entries = (*_lifecycle(), _binding())
    assert publish_entries_from_facet([_entry_facet(e) for e in entries]) == entries
    with pytest.raises(MalformedRecord):
        publish_entries_from_facet([_entry_facet(e) for e in _lifecycle()])


def test_the_publish_report_mints_the_lifecycle_before_the_binding(publish_intent_value):
    from beliefs.boundary import _mint_publish_refusal, _mint_publish_report

    times = {"observer": "o", "instrument": "beliefs.publish", "opened_at": "2026-09-23T00:00:00Z", "closed_at": "2026-09-23T00:00:01Z"}
    report = _mint_publish_report(publish_intent_value, entry=_binding(), lifecycle=_lifecycle(), **times)
    assert report.entries == (*_lifecycle(), _binding())
    refused = _mint_publish_refusal(publish_intent_value, entries=_lifecycle("export"), **times)
    assert refused.entries == _lifecycle("export")
    with pytest.raises(MalformedRecord):
        _mint_publish_refusal(publish_intent_value, entries=(*_lifecycle(), _binding()), **times)
    with pytest.raises(MalformedRecord):
        _mint_publish_report(publish_intent_value, entry=_binding(), lifecycle=_lifecycle("staging"), **times)
```
Add a `publish_intent_value` fixture at the top of the new block that returns `test_publish_intent.intent()` (the builder `test_publication_doors.py` imports). Put `import pytest` and the existing `MalformedRecord`, `BindingBound` and `PublicationBindingEntry` imports beside the module's current imports if they are not there.

Append to `python/tests/test_publication_doors.py` a report builder with explicit entries and the fold tests:

```python
# --- publish-act-local §7: the fold reads the ordered sequence (Y9-e's unit) -----


def _sequence_chain(tmp_path, sequences):
    """One written root; per item, a publish intent and a committed fulfilment
    whose report carries `entries` (built by the callable from the marker)."""
    from beliefs.boundary import _mint_publish_refusal, _mint_publish_report
    from beliefs.report import PublicationBindingEntry as Binding

    root = (tmp_path / "written").resolve()
    (root / "act-report").mkdir(parents=True)
    entries = [genesis_entry(b"g", label="seq-genesis")]
    for k, build in enumerate(sequences):
        value = intent(event_token=str(k) * 32, binding_tips=(), marker_tips=())
        opened = IntentEntryView(digest=digest(f"seq-intent-{k}"), payload=encode_publish_intent(value))
        body = build("ab"[k] * 32)
        times = {"observer": value.actor, "instrument": "beliefs.publish", "opened_at": value.at, "closed_at": value.at}
        if type(body[-1]) is Binding:
            report = boundary._mint_publish_report(value, entry=body[-1], lifecycle=body[:-1], **times)
        else:
            report = _mint_publish_refusal(value, entries=body, **times)
        node = stored.act_report_node(report)
        path = path_for_node_id(node.id)
        data = node_to_markdown(node).encode("utf-8")
        (root / path).write_bytes(data)
        created = RegisteredEntryView(
            digest=digest(f"seq-reg-{k}"), txid=f"seq-{k}", initial=((path, ABSENT),), final=((path, file_state(data)),),
            fulfills=opened.digest,
        )
        entries += [opened, created, settlement(digest(f"seq-set-{k}"), created.digest, f"seq-{k}", committed=True)]
    return root, chain(*entries)


def _subject():
    return "coord:" + "a" * 32 + "/" + "d" * 32


def _full(marker):
    from beliefs.report import Exported, PublicationExportEntry, PublicationRevealEntry, PublicationStagingEntry, Revealed, Staged

    s = _subject()
    return (
        PublicationStagingEntry(s, Staged("1" * 32, 2)),
        PublicationExportEntry(s, Exported("1" * 32, "f" * 64)),
        PublicationRevealEntry(s, Revealed("1" * 32)),
        PublicationBindingEntry(s, BindingBound("c" * 32, "1" * 32, marker)),
    )


def _staging_corrupt(_marker):
    from beliefs.report import PublicationStagingEntry, StagingCorrupt

    return (PublicationStagingEntry(_subject(), StagingCorrupt("1" * 32, "extra", ("dataset:x",))),)


def test_a_full_success_report_folds_as_its_binding(tmp_path):
    root, view = _sequence_chain(tmp_path, [_full])
    assert _fold(root, view) == ()          # bound, not remote: no orphan; no binding tips passed


def test_a_pre_binding_refusal_folds_to_nothing_and_does_not_refuse(tmp_path):
    root, view = _sequence_chain(tmp_path, [_staging_corrupt, _full])
    assert _fold(root, view) == ()


def test_the_fold_yields_pre_binding_for_a_refusal_before_the_binding(tmp_path):
    from beliefs.coordination import ChainBound
    from beliefs.publication_doors import PreBinding, _reports_at

    root, view = _sequence_chain(tmp_path, [_staging_corrupt])
    bound = ChainBound(root, "9" * 32, view, len(view.entries) - 1, True)
    ((_, outcome),) = list(_reports_at(bound, VIEW, HERE, seam_over({root: view})))
    assert outcome == PreBinding("staging-corrupt")
```
`VIEW`, `HERE` and `_fold` are the module's existing names. If `intent()` builds a view or destination other than `VIEW`/`HERE`, pass them as it accepts (`sed -n '/^def intent/,/^def /p' tests/test_publish_intent.py`).

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_report.py tests/test_publication_doors.py -q -k "sequence or lifecycle or stored_form or mints_the_lifecycle or pre_binding or full_success"`
Expected: an `ImportError` for `Exported` (and friends).

- [ ] **Step 3: Implement in `report.py`.** After `binding_outcome_from_facet`:

```python
REQUEST_CORRUPT_REASONS = ("undecodable", "intent-disagrees", "snapshot-missing", "snapshot-mismatch", "snapshot-undecodable")
STAGING_CORRUPT_REASONS = ("pins-foreign", "hole", "extra", "bytes", "marker")
REVEAL_REFUSED_VERDICTS = ("refuted", "unresolvable", "malformed")
_HEX64 = re.compile(r"[0-9a-f]{64}")


@sealed
@final
@dataclass(frozen=True)
class RequestCorrupt:
    reason: str

    def __post_init__(self) -> None:
        if self.reason not in REQUEST_CORRUPT_REASONS:
            raise MalformedRecord(f"request-corrupt reason {self.reason!r} is outside {REQUEST_CORRUPT_REASONS}")


@sealed
@final
@dataclass(frozen=True)
class Staged:
    corpus_id: str
    records: int

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "staged corpus id")
        if type(self.records) is not int or self.records < 1:
            raise MalformedRecord("staged records is a positive exact int")


@sealed
@final
@dataclass(frozen=True)
class StagingCorrupt:
    corpus_id: str
    reason: str
    refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "staging-corrupt corpus id")
        if self.reason not in STAGING_CORRUPT_REASONS:
            raise MalformedRecord(f"staging-corrupt reason {self.reason!r} is outside {STAGING_CORRUPT_REASONS}")
        if type(self.refs) is not tuple or len(self.refs) > 1 or any(type(ref) is not str or not ref for ref in self.refs):
            raise MalformedRecord("staging-corrupt refs are a tuple of at most one record id")


@sealed
@final
@dataclass(frozen=True)
class Exported:
    corpus_id: str
    artifact: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "exported corpus id")
        if type(self.artifact) is not str or _HEX64.fullmatch(self.artifact) is None:
            raise MalformedRecord("an exported artifact identity is 64 lowercase hex")


@sealed
@final
@dataclass(frozen=True)
class ExportCollision:
    corpus_id: str
    sibling: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "export-collision corpus id")
        if self.sibling != f"{self.corpus_id}.head-artifact.v1":
            raise MalformedRecord("an export collision names the corpus's own sibling")


@sealed
@final
@dataclass(frozen=True)
class Revealed:
    corpus_id: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "revealed corpus id")


@sealed
@final
@dataclass(frozen=True)
class RevealRefused:
    corpus_id: str
    verdict: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "reveal-refused corpus id")
        if self.verdict not in REVEAL_REFUSED_VERDICTS:
            raise MalformedRecord(f"reveal-refused verdict {self.verdict!r} is outside {REVEAL_REFUSED_VERDICTS}")
```
Add the seven to `Outcome`. After `PublicationBindingEntry`, add four entry classes shaped like it (`subject: str`, `outcome: <union>`, `_require_str` then `_require_outcome`): `PublicationRequestEntry` (`RequestCorrupt`), `PublicationStagingEntry` (`Staged | StagingCorrupt`), `PublicationExportEntry` (`Exported | ExportCollision`) and `PublicationRevealEntry` (`Revealed | RevealRefused`). Add them to `Entry`, and extend the three tables:

```python
    PublicationRequestEntry: (RequestCorrupt,),
    PublicationStagingEntry: (Staged, StagingCorrupt),
    PublicationExportEntry: (Exported, ExportCollision),
    PublicationRevealEntry: (Revealed, RevealRefused),
```
```python
    PublicationRequestEntry: "publication-request",
    PublicationStagingEntry: "publication-staging",
    PublicationExportEntry: "publication-export",
    PublicationRevealEntry: "publication-reveal",
```
```python
    RequestCorrupt: "request-corrupt",
    Staged: "staged",
    StagingCorrupt: "staging-corrupt",
    Exported: "exported",
    ExportCollision: "export-collision",
    Revealed: "revealed",
    RevealRefused: "reveal-refused",
```
After the tables:

```python
_LIFECYCLE_ENTRIES = (PublicationStagingEntry, PublicationExportEntry, PublicationRevealEntry)
_LIFECYCLE_SUCCESS = {PublicationStagingEntry: Staged, PublicationExportEntry: Exported, PublicationRevealEntry: Revealed}


def publish_sequence_error(entries: object) -> str | None:
    """`None` iff `entries` are a publish report's sequence (publish-act-local
    §7): a request refusal alone; staging, export, reveal in order, each but the
    last succeeding and the last refusing; the whole successful lifecycle then
    the binding; or the binding alone (cut 39's door, called bare)."""
    if type(entries) is not tuple or not entries or any(type(e) not in _ENTRY_KINDS for e in entries):
        return "a publish report carries a non-empty tuple of entries"
    if len({e.subject for e in entries}) != 1:
        return "every entry of a publish report names the one binding address"
    kinds = tuple(type(e) for e in entries)
    if kinds == (PublicationRequestEntry,):
        return None
    if kinds[-1] is PublicationBindingEntry:
        if kinds[:-1] not in ((), _LIFECYCLE_ENTRIES):
            return "a binding entry follows the whole lifecycle or nothing"
        if any(type(e.outcome) is not _LIFECYCLE_SUCCESS[type(e)] for e in entries[:-1]):
            return "a binding follows a lifecycle that succeeded at every step"
        return None
    if kinds != _LIFECYCLE_ENTRIES[: len(kinds)]:
        return "lifecycle entries run staging, export, reveal, in that order"
    if any(type(e.outcome) is not _LIFECYCLE_SUCCESS[type(e)] for e in entries[:-1]):
        return "only the last lifecycle entry refuses"
    if type(entries[-1].outcome) is _LIFECYCLE_SUCCESS[kinds[-1]]:
        return "a lifecycle sequence ends at a refusal or at the binding"
    return None


_LIFECYCLE_OUTCOMES: dict[str, dict[str, type]] = {
    "publication-request": {"request-corrupt": RequestCorrupt},
    "publication-staging": {"staged": Staged, "staging-corrupt": StagingCorrupt},
    "publication-export": {"exported": Exported, "export-collision": ExportCollision},
    "publication-reveal": {"revealed": Revealed, "reveal-refused": RevealRefused},
}
_LIFECYCLE_ENTRY_TYPES = {
    "publication-request": PublicationRequestEntry,
    "publication-staging": PublicationStagingEntry,
    "publication-export": PublicationExportEntry,
    "publication-reveal": PublicationRevealEntry,
}


def lifecycle_outcome_from_facet(kind: str, outcome: object) -> Outcome:
    """A lifecycle outcome's stored form, decoded through its typed constructor,
    so the stored mirror and the values share one rule set. Raises
    `MalformedRecord` on anything else."""
    types = _LIFECYCLE_OUTCOMES.get(kind)
    if types is None or not isinstance(outcome, dict) or outcome.get("type") not in types:
        raise MalformedRecord(f"a {kind} outcome names one of {sorted(types or ())}")
    value_type = types[outcome["type"]]
    names = {field.name for field in dataclasses.fields(value_type)}
    if set(outcome) != {"type", *names}:
        raise MalformedRecord(f"a {outcome['type']} outcome carries exactly {sorted(names)}")
    values = {name: outcome[name] for name in names}
    if "refs" in values:
        if type(values["refs"]) is not list:
            raise MalformedRecord("refs are a list in the stored form")
        values["refs"] = tuple(values["refs"])
    return value_type(**values)


def publish_entries_from_facet(entries: object) -> tuple[Entry, ...]:
    """A publish report's stored entries as values, in one ordered sequence."""
    if type(entries) is not list:
        raise MalformedRecord("a publish report's entries are a list")
    decoded: list[Entry] = []
    for row in entries:
        if not isinstance(row, dict) or set(row) != {"kind", "subject", "outcome"} or type(row["subject"]) is not str:
            raise MalformedRecord("a publish entry carries exactly kind, subject and outcome")
        if row["kind"] == "publication-binding":
            decoded.append(PublicationBindingEntry(row["subject"], binding_outcome_from_facet(row["outcome"])))
        elif row["kind"] in _LIFECYCLE_ENTRY_TYPES:
            entry_type = _LIFECYCLE_ENTRY_TYPES[row["kind"]]
            decoded.append(entry_type(row["subject"], lifecycle_outcome_from_facet(row["kind"], row["outcome"])))
        else:
            raise MalformedRecord(f"{row['kind']!r} is not a publish entry kind")
    sequence = tuple(decoded)
    if (problem := publish_sequence_error(sequence)) is not None:
        raise MalformedRecord(problem)
    return sequence
```
Add the public spelling of an outcome's type, which the act and the fold both read:

```python
def outcome_type(outcome: Outcome) -> str:
    return _OUTCOME_TYPES[type(outcome)]
```
Export the new names (and `outcome_type`) in `__all__`. `_require_outcome` raises `OutcomeRefused` for a wrong outcome type. Keep that error, since `test_report.py` already pins it for the other entries.

- [ ] **Step 4: The stored mirror** (`stored.py`). In `_REPORT_ENTRY_OUTCOMES` add

```python
    # the lifecycle kinds' fields are their typed constructors' too
    "publication-request": {"request-corrupt": ()},
    "publication-staging": {"staged": (), "staging-corrupt": ()},
    "publication-export": {"exported": (), "export-collision": ()},
    "publication-reveal": {"revealed": (), "reveal-refused": ()},
```
In `_valid_report_entry`, right after the `publication-binding` branch:

```python
    if kind in ("publication-request", "publication-staging", "publication-export", "publication-reveal"):
        try:
            report_values.lifecycle_outcome_from_facet(kind, entry.get("outcome"))
        except MalformedRecord:
            return False
        return True
```
In `act_report_facet`, after the `any(not _valid_report_entry(...))` check:

```python
    if facet["operation"] == "publish":
        try:
            report_values.publish_entries_from_facet(facet["entries"])
        except MalformedRecord as caught:
            raise MalformedRecord(f"{node.id}: malformed publish report: {caught}") from caught
```

- [ ] **Step 5: The minting** (`boundary.py`). `_mint_publish_report` gains `lifecycle: tuple[Entry, ...] = ()` after `entry`, and mints `entries=(*lifecycle, entry)` after checking `publish_sequence_error`. Its docstring says "the lifecycle entries in step order, then the one publication-binding entry (publish-act-local §7)". Add beside it:

```python
def _mint_publish_refusal(
    intent: PublishIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """A publish refused before its binding (publish-act-local §7): the lifecycle
    entries reached, the refusing one last, or the request refusal alone."""
    if type(intent) is not PublishIntent:
        raise MalformedRecord("a publish report closes a publish intent")
    if type(entries) is not tuple or not entries or type(entries[-1]) is PublicationBindingEntry:
        raise MalformedRecord("a pre-binding refusal ends before the binding entry")
    if (problem := publish_sequence_error(entries)) is not None:
        raise MalformedRecord(problem)
    return _mint_report(
        operation="publish", event_token=intent.event_token, actor=intent.actor, observer=observer,
        instrument=instrument, opened_at=opened_at, closed_at=closed_at, entries=entries,
    )
```
In `_mint_publish_report`, keep the existing `if type(entry) is not PublicationBindingEntry:` check and message. Then add `if type(lifecycle) is not tuple: raise MalformedRecord(...)` and `if (problem := publish_sequence_error((*lifecycle, entry))) is not None: raise MalformedRecord(problem)`.

- [ ] **Step 6: The fold** (`publication_doors.py`). Add after `BindingOutcome`:

```python
@dataclass(frozen=True)
class PreBinding:
    """A publish report that ends before its binding entry (publish-act-local §7):
    nothing was revealed remotely, so it neither creates nor retires an orphan,
    and it binds no marker."""

    outcome: str  # the last entry's outcome type
```
In `_reports_at`, change the return annotation to `Iterator[tuple[PublishIntent, Mapping[str, object] | PositionRefused | PreBinding]]`. Replace its last block (the `if len(facet["entries"]) != 1 or …` check and the final `yield`) with:

```python
        try:
            entries = publish_entries_from_facet(facet["entries"])
        except MalformedRecord as caught:
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: {paths[0]} is not a publish report: {caught}")
            continue
        if type(entries[-1]) is not PublicationBindingEntry:
            yield intent, PreBinding(str(facet["entries"][-1]["outcome"]["type"]))
            continue
        yield intent, facet["entries"][-1]["outcome"]
```
In `marker_tips_at`'s loop, directly after `if type(outcome) is PositionRefused:\n                return outcome`, add:

```python
            if type(outcome) is PreBinding:
                continue  # refused before its binding: no marker bound, no orphan, nothing retired
```
Import `publish_entries_from_facet` from `beliefs.report`, and add `"PreBinding"` to `__all__`.

- [ ] **Step 7: Run to verify they pass, then the neighbours and the staleness probe**

```bash
cd python && uv run --frozen pytest tests/test_report.py tests/test_publication_doors.py tests/test_stored.py tests/test_publication.py -q
cd python && uv run --frozen pytest tests/test_arm_staleness.py -q
```
Expected: green, with no stale arm. `ls tests | grep -i stored` names the stored-form module if `test_stored.py` does not exist. Cut 39's pinned lines in `publication_doors.py` are untouched: the fold's replaced block pins nothing, and the new `continue` sits between two pinned lines without changing either.

- [ ] **Step 8: Commit**

```bash
tasks check && git add python/src/beliefs/report.py python/src/beliefs/stored.py python/src/beliefs/boundary.py python/src/beliefs/publication_doors.py python/tests/test_report.py python/tests/test_publication_doors.py tasks
git commit -m "feat(report): the publish lifecycle entries, their ordered sequence, and the fold that reads it (Y9)"
```

---

### Task 3: The permit and the refusal values

**Files:**
- Modify: `python/src/beliefs/permit.py` (`_PUBLICATION_PERMIT`), `python/src/beliefs/errors.py` (`PublicationRefused`, `PublicationArrivalRefused`), `python/tests/test_permit.py`

**Interfaces:**
- Produces:
  - `RequiredCapabilities.publishes()`, whose permit is `WritePermit(frozenset({"publication-binding", "publication", "act-report", *stored.WORLD_KINDS}), frozenset({"publish", "corpus-write", "lifecycle", "registry"}))`;
  - `PublicationRefused(reason, *, tips=(), refs=(), corpus_ids=(), field="")`;
  - `PublicationArrivalRefused(reason, *, refs=())`.

- [ ] **Step 1: Update the tests.** In `test_permit.py`, the assertion at line ~175 becomes:

```python
        assert RequiredCapabilities.publishes().permit == WritePermit(
            frozenset({"publication-binding", "publication", "act-report", *stored.WORLD_KINDS}),
            frozenset({"publish", "corpus-write", "lifecycle", "registry"}),
        )
```
(import `stored` from `beliefs`). Add:

```python
def test_the_publication_permit_covers_every_call_the_act_makes():
    """Spec decision 6: the act's registry call (`World.admit`) and lifecycle calls
    run under exactly this permit (user review finding 1)."""
    authority = scoped_authority(RequiredCapabilities.publishes(), "actor")
    authority.require("registry")
    authority.require("lifecycle")
    authority.require("publish", ("publication-binding", "publication"))
    authority.require("corpus-write", ("act-report", *stored.WORLD_KINDS))
```
Run `uv run --frozen pytest tests/test_permit.py -q`. Expected: the two changed tests fail on the old permit.

- [ ] **Step 2: Implement.** In `permit.py`:

```python
_PUBLICATION_PERMIT = WritePermit(
    frozenset({"publication-binding", "publication", "act-report", *_WORLD_KINDS}),
    frozenset({"publish", "corpus-write", "lifecycle", "registry"}),
)
```
`_WORLD_KINDS` is the world-kind tuple `permit.py` can import without a cycle. If `permit.py` cannot import `stored`, compute it from `shipped_base()` as `stored.py` does (`tuple(name for name, kind in shipped_base().kinds.items() if kind.role == "world")`), and state the duplication in a one-line comment. `        return cls(_PUBLICATION_PERMIT)` is cut 17's re-targeted pin: it stays byte-identical.

In `errors.py`, replace `PublicationRefused`'s `__init__` with

```python
    def __init__(
        self, reason: str, *, tips: tuple[str, ...] = (), refs: tuple[str, ...] = (), corpus_ids: tuple[str, ...] = (), field: str = ""
    ) -> None:
        detail = ", ".join(part for part in (",".join(refs), ",".join(corpus_ids), field) if part)
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.tips = tips
        self.refs = refs
        self.corpus_ids = corpus_ids
        self.field = field
```
and add

```python
class PublicationArrivalRefused(WriteRefused):
    """A publication's arrival refused before any write (publish-act-local design §10).
    Not `ArrivalRefused`, verified arrival's `(cause, report, detail)` refusal,
    which `admit_arrival` raises and which passes through `admit_publication`
    unchanged."""

    def __init__(self, reason: str, *, refs: tuple[str, ...] = ()) -> None:
        super().__init__(f"{reason}: {', '.join(refs)}" if refs else reason)
        self.reason = reason
        self.refs = refs
```

- [ ] **Step 3: Run the permit inventories and the staleness probe**

```bash
cd python && uv run --frozen pytest tests/test_permit.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py tests/test_publication_doors.py tests/test_arm_staleness.py -q
```
Expected: green. `test_permit_entry_points.py`'s `_bind_publication` case now runs under the wider permit. Its E1/E2 probes narrow the family and kinds its `Case` names, so they still refuse. If a probe now passes where it refused, the case's `extra_families` must list the new families; add them and note it.

- [ ] **Step 4: Commit**

```bash
tasks check && git add python/src/beliefs/permit.py python/src/beliefs/errors.py python/tests/test_permit.py tasks
git commit -m "feat(permit): one kernel permit covers the whole publish act, registry included (decision 6)"
```

---

### Task 4: The step-0 pieces — `beliefs/publish_request.py`

**Files:**
- Create: `python/src/beliefs/publish_request.py`, `python/tests/test_publish_request.py`

**Interfaces:**
- Consumes: `PublicationRefused` (Task 3); `CorpusPins` (`beliefs.consulted`); `shipped_coordination`; `Destination`; `CoordinationAddress`.
- Produces:
  - `closure_missing(view, selected) -> tuple[str, ...]`;
  - `derive_pins(manifests: Mapping[str, CorpusPins], written: CorpusPins) -> CorpusPins`, which raises `PublicationRefused`;
  - `pins_of(profile: ProfileSpec) -> CorpusPins`;
  - `require_usable(operations_root: Path, destination: Destination, *, forbidden: Sequence[Path]) -> tuple[Path, Path]`, which raises `PublicationRefused`;
  - `Snapshot(event_token, records: tuple[tuple[str, str], ...])` with `.identity()`, `encode_snapshot`, `decode_snapshot`;
  - `PublishRequest(event_token, view, destination, epoch, world_id, pins, selection, staging_world_id)`, `encode_request`, `decode_request`;
  - `staging_world_id_for(event_token) -> str`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_publish_request.py`:

```python
"""Step 0's pure pieces (publish-act-local design §4)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress
from beliefs.errors import MalformedRecord, PublicationRefused
from beliefs.intents.publish import Destination
from beliefs.profile import shipped_coordination
from beliefs.publish_request import (
    PublishRequest,
    Snapshot,
    closure_missing,
    decode_request,
    decode_snapshot,
    derive_pins,
    encode_request,
    encode_snapshot,
    require_usable,
    staging_world_id_for,
)

V2 = "coordination:" + shipped_coordination(2).content_identity
V1 = "coordination:" + shipped_coordination(1).content_identity
BASE_PIN = "science:" + "b" * 64


class FakeView:
    """`get` and `resolve` over a dict; an alias maps to a live id."""

    def __init__(self, nodes, aliases=None):
        self._nodes = {n.id: n for n in nodes}
        self._aliases = aliases or {}

    def get(self, ref):
        return self._nodes[ref]

    def resolve(self, ref):
        ref = self._aliases.get(ref, ref)
        return ref if ref in self._nodes else None


def _run(name, produces=()):
    return stored.run_node(name, title=name, spec="s", produces=list(produces))


def test_a_complete_closure_misses_nothing():
    d = stored.dataset_node(title="d", resources=())
    r = _run("r", produces=[d.id])
    assert closure_missing(FakeView([d, r]), (d.id, r.id)) == ()


def test_an_unselected_relation_target_is_missing():
    d = stored.dataset_node(title="d", resources=())
    r = _run("r", produces=[d.id])
    assert closure_missing(FakeView([d, r]), (r.id,)) == (d.id,)


def test_closure_reads_both_endpoints_and_resolves_aliases():
    """Review Focus 1: a relation carried by its target names its source; an alias resolves first."""
    d = stored.dataset_node(title="d", resources=())
    r = _run("r")
    d.relations.append(Relation(source=r.id, predicate="produces", target=d.id))
    assert closure_missing(FakeView([d, r]), (d.id,)) == (r.id,)
    assert closure_missing(FakeView([d, r], aliases={"run:old": r.id}), (d.id, r.id)) == ()


def test_a_composite_missing_a_member_is_closure_incomplete():
    """The 2026-09-16 amendment: `composes` is a world relation, read by the one rule."""
    p1 = stored.proposition_node("p1", title="p1", claim={"terms": []})
    composite = stored.proposition_node("c", title="c", claim={"terms": []}).model_copy(update={"kind": "composite", "id": "composite:c"})
    composite.relations.append(Relation(source=composite.id, predicate="composes", target=p1.id))
    assert closure_missing(FakeView([p1, composite]), (composite.id,)) == (p1.id,)


def test_an_unresolvable_endpoint_is_missing_by_its_stored_spelling():
    r = _run("r", produces=["dataset:gone"])
    assert closure_missing(FakeView([r]), (r.id,)) == ("dataset:gone",)


def test_pins_union_domains_and_add_the_written_coordination_pin():
    derived = derive_pins(
        {"a" * 32: CorpusPins(BASE_PIN, {"biology": "biology:1"}), "b" * 32: CorpusPins(BASE_PIN, {})},
        CorpusPins(BASE_PIN, {"coordination": V2}),
    )
    assert derived == CorpusPins(BASE_PIN, {"biology": "biology:1", "coordination": V2})


@pytest.mark.parametrize(
    "manifests, written, reason, field",
    [
        ({"a" * 32: CorpusPins(BASE_PIN, {}), "b" * 32: CorpusPins("science:" + "c" * 64, {})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "science_contract"),
        ({"a" * 32: CorpusPins(BASE_PIN, {"biology": "biology:1"}), "b" * 32: CorpusPins(BASE_PIN, {"biology": "biology:2"})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "biology"),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins(BASE_PIN, {}), "coordination-unpinned", ""),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins(BASE_PIN, {"coordination": V1}), "coordination-unpinned", ""),
        ({"a" * 32: CorpusPins(BASE_PIN, {"coordination": V1})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "coordination"),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins("science:" + "c" * 64, {"coordination": V2}), "pins-disagree", "science_contract"),
    ],
    ids=["contract", "domain", "no-coordination", "v1-coordination", "coordination-disagrees", "written-contract"],
)
def test_pins_refusals(manifests, written, reason, field):
    with pytest.raises(PublicationRefused) as caught:
        derive_pins(manifests, written)
    assert caught.value.reason == reason and caught.value.field == field


def test_destination_checks(tmp_path):
    """Review Focus 2: every unusable destination refuses before the intent."""
    ops, dest, corpus = tmp_path / "ops", tmp_path / "dest", tmp_path / "corpus"
    for directory in (ops, dest, corpus):
        directory.mkdir()
    (tmp_path / "file").write_bytes(b"")
    (tmp_path / "link").symlink_to(dest)
    assert require_usable(ops, Destination.local(str(dest)), forbidden=(corpus,)) == (ops.resolve(), dest.resolve())
    # finding 4: a symlinked destination answers its resolved target, which step 0 freezes
    assert require_usable(ops, Destination.local(str(tmp_path / "link")), forbidden=(corpus,)) == (ops.resolve(), dest.resolve())
    for bad in (tmp_path / "missing", tmp_path / "file", ops, ops / "inner", corpus / "inner"):
        if bad == ops / "inner":
            bad.mkdir()
        if bad == corpus / "inner":
            bad.mkdir()
        with pytest.raises(PublicationRefused) as caught:
            require_usable(ops, Destination.local(str(bad)), forbidden=(corpus,))
        assert caught.value.reason == "destination-unusable", bad
    with pytest.raises(PublicationRefused) as caught:
        require_usable(dest / "ops-inside", Destination.local(str(dest)), forbidden=())
    assert caught.value.reason == "operations-root-unusable"
    with pytest.raises(PublicationRefused) as caught:
        require_usable(corpus, Destination.local(str(dest)), forbidden=(corpus,))
    assert caught.value.reason == "operations-root-unusable"


def _snapshot():
    d = stored.dataset_node(title="d", resources=())
    r = _run("r", produces=[d.id])
    records = tuple(sorted((n.id, node_to_markdown(n)) for n in (d, r)))
    return Snapshot("e" * 32, records)


def test_the_snapshot_round_trips_and_its_identity_is_stable():
    snapshot = _snapshot()
    assert decode_snapshot(encode_snapshot(snapshot)) == snapshot
    assert snapshot.identity() == decode_snapshot(encode_snapshot(snapshot)).identity()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: replace(s, records=()),
        lambda s: replace(s, records=tuple(reversed(s.records))),
        lambda s: replace(s, records=(s.records[0], s.records[0])),
        lambda s: replace(s, records=((s.records[0][0], s.records[1][1]), s.records[1])),     # text is another id's
        lambda s: replace(s, records=((s.records[0][0], s.records[0][1] + "\n"), s.records[1])),  # not canonical
        lambda s: replace(s, event_token="x"),
    ],
)
def test_a_malformed_snapshot_is_refused(mutate):
    with pytest.raises(MalformedRecord):
        mutate(_snapshot())


def test_a_non_canonical_snapshot_encoding_is_refused():
    with pytest.raises(MalformedRecord):
        decode_snapshot(encode_snapshot(_snapshot()) + b" ")


def _request(**changes):
    value = PublishRequest(
        event_token="e" * 32,
        view=CoordinationAddress("a" * 32, "b" * 32, "c" * 32),
        destination=Destination.local("/srv/published"),
        epoch="f" * 64,
        world_id="d" * 32,
        pins=CorpusPins(BASE_PIN, {"coordination": V2}),
        selection="0" * 64,
        staging_world_id=staging_world_id_for("e" * 32),
    )
    return replace(value, **changes) if changes else value


def test_the_request_round_trips():
    assert decode_request(encode_request(_request())) == _request()


@pytest.mark.parametrize(
    "changes",
    [
        {"event_token": "E" * 32},
        {"view": CoordinationAddress("a" * 32, "b" * 32)},       # unpinned
        {"epoch": "f" * 63},
        {"world_id": "d" * 31},
        {"selection": "0" * 63},
        {"staging_world_id": "1" * 32},                           # not the token's
    ],
)
def test_a_malformed_request_is_refused(changes):
    with pytest.raises(MalformedRecord):
        _request(**changes)


def test_staging_world_id_is_a_domain_separated_function_of_the_token():
    assert staging_world_id_for("e" * 32) == staging_world_id_for("e" * 32) != staging_world_id_for("f" * 32)
    assert len(staging_world_id_for("e" * 32)) == 32
```
If `stored.proposition_node`'s `claim` argument needs another shape, copy `test_world_selection.py`'s `CLAIM_FACET` import (`from test_evaluation import CLAIM_FACET`). The composite test only needs a node of kind `composite` carrying a `composes` relation. If `CoordinationAddress(project, local, revision)` takes its arguments in another order, copy the `VIEW` construction from `test_publication_doors.py`.

- [ ] **Step 2: Run to verify they fail.** Run `cd python && uv run --frozen pytest tests/test_publish_request.py -q`. Expected: `ModuleNotFoundError: No module named 'beliefs.publish_request'`.

- [ ] **Step 3: Implement** `python/src/beliefs/publish_request.py`:

```python
"""Step 0's pure pieces (publish-act-local design §4): the publication closure,
the destination pins, the usable operations root and destination, and the two
records the operations root holds — the selection snapshot and the request."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from nodes.core.frontmatter import node_from_markdown, node_to_markdown

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress
from beliefs.errors import CanonicalTextRefused, MalformedRecord, PublicationRefused
from beliefs.identity import v1
from beliefs.intents.publish import Destination
from beliefs.profile import ProfileSpec, shipped_coordination

__all__ = [
    "PUBLISHING_COORDINATION",
    "PublishRequest",
    "Snapshot",
    "closure_missing",
    "decode_request",
    "decode_snapshot",
    "derive_pins",
    "encode_request",
    "encode_snapshot",
    "pins_of",
    "require_usable",
    "staging_world_id_for",
]

SELECTION_DOMAIN = "science.publish-selection.v1"
REQUEST_DOMAIN = "science.publish-request.v1"
_STAGING_WORLD_DOMAIN = "science.publish-staging-world.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")

PUBLISHING_COORDINATION = frozenset(
    f"coordination:{shipped_coordination(version).content_identity}"
    for version in (1, 2)
    if "publication" in shipped_coordination(version).kinds
)
"""The coordination pins that authorize a publication marker (spec §4.1 item 6)."""


def closure_missing(view, selected: tuple[str, ...]) -> tuple[str, ...]:
    """Every world-relation endpoint of a selected record outside the selection
    (spec §4.1 item 5), by its live address, or by its stored spelling when it
    does not resolve. `view` answers `get(id)` and `resolve(ref)`."""
    chosen = set(selected)
    missing: set[str] = set()
    for address in selected:
        node = view.get(address)
        for relation in node.relations:
            if relation.predicate not in stored.WORLD_RELATIONS:
                continue
            for endpoint in (relation.source, relation.target):
                if endpoint == node.id:
                    continue
                live = view.resolve(endpoint)
                if live is None:
                    missing.add(endpoint)
                elif live not in chosen:
                    missing.add(live)
    return tuple(sorted(missing))


def derive_pins(manifests: Mapping[str, CorpusPins], written: CorpusPins) -> CorpusPins:
    """The destination's one `CorpusPins` (spec §4.1 item 6): one base contract,
    the union of the contributing domains, and the written root's coordination
    pin, which must authorize `publication`."""
    corpus_ids = tuple(sorted(manifests))
    contracts = {pins.science_contract for pins in manifests.values()} | {written.science_contract}
    if len(contracts) != 1:
        raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field="science_contract")
    domains: dict[str, str] = {}
    for corpus_id in corpus_ids:
        for namespace, pin in sorted(manifests[corpus_id].domains.items()):
            if domains.setdefault(namespace, pin) != pin:
                raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field=namespace)
    coordination = written.domains.get("coordination")
    if coordination not in PUBLISHING_COORDINATION:
        raise PublicationRefused("coordination-unpinned")
    if domains.setdefault("coordination", coordination) != coordination:
        raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field="coordination")
    (science_contract,) = contracts
    return CorpusPins(science_contract, domains)


def pins_of(profile: ProfileSpec) -> CorpusPins:
    """The pins a writer holding `profile` adopts (`CorpusWriter.adopt_manifest`'s rule)."""
    return CorpusPins(
        "science:" + profile.base_contract_identity,
        {namespace: f"{namespace}:{identity}" for namespace, identity in profile.activated_contracts.items()},
    )


def _inside(path: Path, other: Path) -> bool:
    return path == other or other in path.parents


def require_usable(operations_root: Path, destination: Destination, *, forbidden: Sequence[Path]) -> tuple[Path, Path]:
    """The resolved operations root and local destination directory (spec §3,
    §4.1 item 7): both existing directories, neither inside the other, neither
    inside a mounted corpus root or the world root (`forbidden`)."""
    closed = tuple(Path(path).resolve() for path in forbidden)
    ops = Path(operations_root)
    if not ops.is_absolute() or not ops.is_dir() or any(_inside(ops.resolve(), path) for path in closed):
        raise PublicationRefused("operations-root-unusable")
    ops = ops.resolve()
    target = Path(destination.locator)
    if not target.is_dir():
        raise PublicationRefused("destination-unusable")
    target = target.resolve()
    if _inside(target, ops) or _inside(ops, target) or any(_inside(target, path) for path in closed):
        if _inside(ops, target) and not _inside(target, ops):
            raise PublicationRefused("operations-root-unusable")
        raise PublicationRefused("destination-unusable")
    return ops, target


def staging_world_id_for(event_token: str) -> str:
    return v1.digest(_STAGING_WORLD_DOMAIN, event_token)[:32]


def _hex(value: object, pattern: re.Pattern[str], where: str) -> None:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise MalformedRecord(f"{where} is {'32' if pattern is _HEX32 else '64'} lowercase hex")


@dataclass(frozen=True)
class Snapshot:
    """The selected records' canonical text, frozen at step 0 (spec §4.3)."""

    event_token: str
    records: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _hex(self.event_token, _HEX32, "a snapshot's event token")
        if type(self.records) is not tuple or not self.records:
            raise MalformedRecord("a snapshot holds a non-empty tuple of records")
        for row in self.records:
            if type(row) is not tuple or len(row) != 2 or any(type(member) is not str for member in row):
                raise MalformedRecord("a snapshot record is an (id, text) pair of strings")
            try:
                node = node_from_markdown(row[1])
            except Exception as caught:  # nodes and pydantic raise several types for unparseable text
                raise MalformedRecord(f"{row[0]}: a snapshot record's text does not parse: {caught}") from caught
            if node.id != row[0] or node_to_markdown(node) != row[1]:
                raise MalformedRecord(f"{row[0]}: a snapshot record's text is not that record's canonical rendering")
        ids = [row[0] for row in self.records]
        if ids != sorted(set(ids)):
            raise MalformedRecord("a snapshot's records are strictly ascending by id")

    def projection(self) -> dict[str, object]:
        return {
            "domain": SELECTION_DOMAIN,
            "event_token": self.event_token,
            "records": [{"id": record_id, "text": text} for record_id, text in self.records],
        }

    def identity(self) -> str:
        return v1.digest(SELECTION_DOMAIN, self.projection())


def encode_snapshot(snapshot: Snapshot) -> bytes:
    return v1.encode(snapshot.projection())


def _decoded(data: bytes, where: str) -> dict:
    try:
        value = v1.decode(data)
    except (CanonicalTextRefused, ValueError) as caught:
        raise MalformedRecord(f"{where} is not canonical text: {caught}") from caught
    if not isinstance(value, dict):
        raise MalformedRecord(f"{where} is a mapping")
    return value


def decode_snapshot(data: bytes) -> Snapshot:
    value = _decoded(data, "a snapshot")
    if set(value) != {"domain", "event_token", "records"} or value["domain"] != SELECTION_DOMAIN or type(value["records"]) is not list:
        raise MalformedRecord("a snapshot carries exactly its closed field set under its domain")
    if any(type(row) is not dict or set(row) != {"id", "text"} for row in value["records"]):
        raise MalformedRecord("a snapshot record carries exactly id and text")
    snapshot = Snapshot(value["event_token"], tuple((row["id"], row["text"]) for row in value["records"]))
    if encode_snapshot(snapshot) != data:
        raise MalformedRecord("a snapshot is not its canonical encoding")
    return snapshot


@dataclass(frozen=True)
class PublishRequest:
    """Every identity-bearing input of one attempt, frozen at step 0 (spec §4.5)."""

    event_token: str
    view: CoordinationAddress
    destination: Destination
    epoch: str
    world_id: str
    pins: CorpusPins
    selection: str
    staging_world_id: str

    def __post_init__(self) -> None:
        _hex(self.event_token, _HEX32, "a request's event token")
        if type(self.view) is not CoordinationAddress or self.view.revision is None:
            raise MalformedRecord("a request names its view pinned to the resolved revision")
        if type(self.destination) is not Destination:
            raise MalformedRecord("a request's destination is a Destination")
        _hex(self.epoch, _HEX64, "a request's epoch")
        _hex(self.world_id, _HEX32, "a request's world id")
        if type(self.pins) is not CorpusPins:
            raise MalformedRecord("a request's pins are CorpusPins")
        _hex(self.selection, _HEX64, "a request's selection identity")
        if self.staging_world_id != staging_world_id_for(self.event_token):
            raise MalformedRecord("a request's staging world id is its token's")

    def projection(self) -> dict[str, object]:
        return {
            "domain": REQUEST_DOMAIN,
            "event_token": self.event_token,
            "view": str(self.view),
            "destination": self.destination.projection(),
            "epoch": self.epoch,
            "world_id": self.world_id,
            "pins": {"science_contract": self.pins.science_contract, "domains": dict(self.pins.domains)},
            "selection": self.selection,
            "staging_world_id": self.staging_world_id,
        }


_REQUEST_FIELDS = frozenset({"domain", "event_token", "view", "destination", "epoch", "world_id", "pins", "selection", "staging_world_id"})


def encode_request(request: PublishRequest) -> bytes:
    return v1.encode(request.projection())


def decode_request(data: bytes) -> PublishRequest:
    value = _decoded(data, "a request")
    if set(value) != _REQUEST_FIELDS or value["domain"] != REQUEST_DOMAIN:
        raise MalformedRecord("a request carries exactly its closed field set under its domain")
    pins = value["pins"]
    if type(pins) is not dict or set(pins) != {"science_contract", "domains"} or type(pins["domains"]) is not dict:
        raise MalformedRecord("a request's pins carry science_contract and a domains mapping")
    try:
        request = PublishRequest(
            event_token=value["event_token"],
            view=CoordinationAddress.parse(value["view"]),
            destination=Destination.from_projection(value["destination"]),
            epoch=value["epoch"],
            world_id=value["world_id"],
            pins=CorpusPins(pins["science_contract"], pins["domains"]),
            selection=value["selection"],
            staging_world_id=value["staging_world_id"],
        )
    except (TypeError, ValueError) as caught:
        raise MalformedRecord(f"a request field is malformed: {caught}") from caught
    if encode_request(request) != data:
        raise MalformedRecord("a request is not its canonical encoding")
    return request
```
`CorpusPins` must compare equal after the round trip. It wraps `domains` in a `MappingProxyType`, so if equality fails, compare `dict(domains)` in a `__eq__`-free way: construct from `dict(pins["domains"])`, and in the round-trip test compare `projection()`s. `CanonicalTextRefused` is what `v1.decode` raises (see `decode_publish_intent`); keep `ValueError` beside it only if `v1.decode` raises it (`sed -n 166,204p src/beliefs/identity/v1.py`), and otherwise drop it.

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_publish_request.py -q`
Expected: every test passes. A parametrized case that fails on `require_usable`'s nested branch means the branch order is wrong. The rule to restore: an operations root inside the destination is `operations-root-unusable`; everything else is `destination-unusable`.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/publish_request.py python/tests/test_publish_request.py tasks
git commit -m "feat(publish): step-0 closure, pins, snapshot and request (Y5, Y6)"
```

---

### Task 5: The doors — staging, pin re-check, lifecycle binding, pre-binding refusal, completion reading

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`_stage_record` and `_stage_marker` beside `adopt_manifest`), `python/src/beliefs/publication_doors.py`, `python/tests/test_permit_boundary.py`, `python/tests/test_permit_entry_points.py`
- Test: `python/tests/test_publication_doors.py`, `python/tests/test_corpus_write.py` (`ls tests | grep corpus_write` confirms the name)

**Interfaces:**
- Consumes: Task 2's entries and `_mint_publish_refusal`; `marker_consistent` and `publication_content_malformed` (`beliefs.publication`).
- Produces:
  - `CorpusWriter._stage_record(text: str) -> Node` and `CorpusWriter._stage_marker(node: Node) -> Node`;
  - `_open_publication(..., expected_view: CoordinationAddress | None = None)`, which refuses `view-revised`;
  - `_bind_publication(..., lifecycle: tuple[Entry, ...] = ())`;
  - `_refuse_publication(writer, opened, entries, *, clock, port=None) -> ActReport`;
  - `AttemptReading(opened: OpenedPublication, reading: Literal["unfinished", "closed", "indeterminate"], outcome: str | None)` and `attempt_reading(writer, event_token, seam) -> AttemptReading | None`.

- [ ] **Step 1: Write the failing tests.** In `test_corpus_write.py`, use the module's existing tmp-root writer fixture (`sed -n 1,80p tests/test_corpus_write.py`). With `DefaultExecutor` over `tmp_path`, as `test_publication_doors.py`'s `CorpusWriter(root, lambda r: DefaultExecutor(r), authority=FULL, profile=…)` constructs it, add:

```python
# --- publish-act-local §5: the staging doors -----------------------------------

from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_to_markdown
from profiles import pins_for

from beliefs.errors import RecordAlreadyMinted, ValidationRefused
from beliefs.publication import marker_record


def _staging_writer(tmp_path):
    from nodes.core.write_plan import DefaultExecutor

    profile = coordination_profile(None, version=2)
    writer = CorpusWriter(tmp_path / "staging", lambda root: DefaultExecutor(root), authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer


def test_stage_record_writes_the_snapshot_text_byte_for_byte(tmp_path):
    writer = _staging_writer(tmp_path)
    node = stored.run_node("r", title="r", spec="s", produces=["dataset:elsewhere"])   # its target is not staged: no view check
    text = node_to_markdown(node)
    writer._stage_record(text)
    assert (writer.root / writer._relative_path(node)).read_text() == text


def test_stage_record_refuses_a_repeat_and_a_non_world_record(tmp_path):
    writer = _staging_writer(tmp_path)
    node = stored.run_node("r", title="r", spec="s", produces=[])
    writer._stage_record(node_to_markdown(node))
    with pytest.raises(RecordAlreadyMinted):
        writer._stage_record(node_to_markdown(node))
    project = raw_coordination_node("project", "1" * 32, "2" * 32)
    with pytest.raises(ValidationRefused):
        writer._stage_record(node_to_markdown(project))


def test_stage_record_refuses_non_canonical_text(tmp_path):
    writer = _staging_writer(tmp_path)
    node = stored.run_node("r", title="r", spec="s", produces=[])
    with pytest.raises(ValidationRefused):
        writer._stage_record(node_to_markdown(node) + "\n")


def test_stage_marker_writes_only_a_consistent_marker(tmp_path):
    from test_publish_intent import intent

    writer = _staging_writer(tmp_path)
    marker = marker_record(intent(), world_id="d" * 32, epoch="f" * 64, selection=("run:r",))
    writer._stage_marker(marker)
    assert (writer.root / writer._relative_path(marker)).read_text() == node_to_markdown(marker)
    forged = marker.model_copy(update={"uid": "0" * 32})
    with pytest.raises(ValidationRefused):
        writer._stage_marker(forged)


def test_stage_record_refuses_a_facet_the_staging_profile_does_not_declare(tmp_path):
    """Finding 3: an unactivated domain's facet is refused, as `add` refuses it."""
    writer = _staging_writer(tmp_path)
    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    node.facets["biology/gene-axis"] = {"axis": "rows"}
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer._stage_record(node_to_markdown(stored.stamp_semantic_identity(node)))


def test_stage_marker_refuses_under_a_profile_without_coordination_v2(tmp_path):
    """Finding 3: a marker under BASE, which pins no coordination contract, is refused."""
    from nodes.core.write_plan import DefaultExecutor
    from profiles import BASE
    from test_publish_intent import intent

    writer = CorpusWriter(tmp_path / "base", lambda root: DefaultExecutor(root), authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    marker = marker_record(intent(), world_id="d" * 32, epoch="f" * 64, selection=("run:r",))
    with pytest.raises(ValidationRefused, match="kind-unknown"):
        writer._stage_marker(marker)


def test_the_staging_doors_require_their_permits_first(tmp_path):
    writer = _staging_writer(tmp_path)
    node = stored.run_node("r", title="r", spec="s", produces=[])
    narrow = CorpusWriter(writer.root, lambda root: DefaultExecutor(root), authority=lacking(kinds=("run",)), profile=writer.profile)
    with pytest.raises(PermitExceeded):
        narrow._stage_record(node_to_markdown(node))
```
The last test imports `DefaultExecutor`, `lacking` and `PermitExceeded` as the module already does, or adds them. The `intent()` builder in `test_publish_intent.py` names its default view and destination, and `marker_record` needs only the intent.

In `test_publication_doors.py`, add:

```python
def test_a_view_revised_before_the_lock_refuses_and_appends_nothing(tmp_path):
    """Spec §4.2: the pin evaluated before the lock is re-checked under it."""
    pair = _pair(tmp_path)                                   # the module's two-root fixture builder
    stale = pair.view.unpinned().pinned("0" * 32)
    before = _intents(pair)
    with pytest.raises(PublicationRefused) as caught:
        _open_publication(pair.writer, pair.resolver, view=pair.view, destination=HERE, clock=_clock, seam=pair.seam,
                          port=pair.port, expected_view=stale)
    assert caught.value.reason == "view-revised" and _intents(pair) == before


def test_the_binding_carries_its_lifecycle_before_the_binding_entry(tmp_path):
    from beliefs.report import Exported, PublicationExportEntry, PublicationRevealEntry, PublicationStagingEntry, Revealed, Staged

    pair = _pair(tmp_path)
    opened = _open_publication(pair.writer, pair.resolver, view=pair.view, destination=HERE, clock=_clock, seam=pair.seam, port=pair.port)
    subject = str(binding_address(opened.intent.view, HERE))
    lifecycle = (
        PublicationStagingEntry(subject, Staged("1" * 32, 1)),
        PublicationExportEntry(subject, Exported("1" * 32, "9" * 64)),
        PublicationRevealEntry(subject, Revealed("1" * 32)),
    )
    outcome = _bind_publication(pair.writer, pair.resolver, opened, corpus_id="1" * 32, marker="2" * 32, artifact="9" * 64,
                                remotely_revealed=False, clock=_clock, seam=pair.seam, port=pair.port, lifecycle=lifecycle)
    assert outcome.report.entries[:3] == lifecycle and type(outcome.report.entries[3]) is PublicationBindingEntry


def test_the_pre_binding_refusal_writes_its_report_alone_and_fulfils(tmp_path):
    from beliefs.publication_doors import _refuse_publication
    from beliefs.report import PublicationStagingEntry, StagingCorrupt

    pair = _pair(tmp_path)
    opened = _open_publication(pair.writer, pair.resolver, view=pair.view, destination=HERE, clock=_clock, seam=pair.seam, port=pair.port)
    entries = (PublicationStagingEntry(str(binding_address(opened.intent.view, HERE)), StagingCorrupt("1" * 32, "extra", ("run:x",))),)
    report = _refuse_publication(pair.writer, opened, entries, clock=_clock, port=pair.port)
    assert report.entries == entries
    (fulfilled,) = pair.port.fulfilling
    assert fulfilled == opened.digest
```
Build `_pair`, `_intents`, `_clock` and `pair.port`/`pair.seam` from the module's existing step-0/step-8 test scaffolding. The tests at lines 360–450 construct exactly these: a v2 profile over two `tmp_path` roots, a `RecordingPort` and a fake seam. Lift that construction into a `_pair(tmp_path)` helper returning a `SimpleNamespace`, and have the existing tests keep their bodies. `RecordingPort.fulfilling` is the list of `fulfills` digests the recording port saw; if it records them under another name, use that name (`sed -n '/class RecordingPort/,/^class \|^def /p' tests/test_operation_writes.py`).

`attempt_reading` is pinned durably in Task 6's tests: it reads a real chain.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_corpus_write.py tests/test_publication_doors.py -q -k "stage or revised or lifecycle or pre_binding_refusal"`
Expected: `AttributeError: 'CorpusWriter' object has no attribute '_stage_record'`, plus `TypeError`s on the new keywords.

- [ ] **Step 3: Implement the staging doors** in `corpus.py`, after `adopt_manifest`:

```python
    def _stage_record(self, text: str) -> Node:
        """Publish-act-local §5: one snapshot record, written into a staging corpus
        byte for byte as its snapshot text. The ordinary writer's record-local
        guards — document, registry and facet payloads under the staging profile,
        display facet, governed stamp, rendering, collision — and none of the
        view-reading ones, which ran where the record was minted: population runs
        in id order, not dependency order. Nothing but the act calls it."""
        node = node_from_markdown(text)
        self._authority.require("corpus-write", (node.kind,))
        with self._operation:
            self._require_pins_agree()
            if node.kind not in stored.WORLD_KINDS:
                raise ValidationRefused(f"{node.id}: a staged record is a world record")
            self._refuse_invalid(node)
            self._refuse_facet_shapes(node)  # the staging profile's registry and facet payloads (finding 3)
            if stored.display_facet_malformed(node):
                raise ValidationRefused(f"{node.id}: refused by document validation: malformed display facet")
            self._refuse_governed_stamp(node)
            self._refuse_already_minted(node)
            if self._refuse_rendering(node) != text.encode("utf-8"):
                raise ValidationRefused(f"{node.id}: a staged record renders as its snapshot text")
            self._refuse_collision(node)
            return self._corpus.add(node)

    def _stage_marker(self, node: Node) -> Node:
        """Publish-act-local §5: the factory's marker, written last into a staging
        corpus. Only a well-formed, self-consistent marker is written."""
        self._authority.require("publish", ("publication",))
        from beliefs.publication import MARKER_KIND, marker_consistent, publication_content_malformed

        with self._operation:
            self._require_pins_agree()
            if node.kind != MARKER_KIND or publication_content_malformed(node) or not marker_consistent(node):
                raise ValidationRefused(f"{getattr(node, 'id', node)}: a staged marker is a consistent publication record")
            self._refuse_invalid(node)
            self._refuse_facet_shapes(node)  # a profile without coordination v2 does not declare `publication` (finding 3)
            self._refuse_already_minted(node)
            self._refuse_rendering(node)
            self._refuse_collision(node)
            return self._corpus.add(node)
```
Import `node_from_markdown` if `corpus.py` does not already. Check with `grep -n "^from nodes.core.frontmatter" src/beliefs/corpus.py`. `test_permit_boundary.py`'s `requires_before_writing` reads the first top-level statements. `_stage_marker`'s local import after the `require` is not an effect. If the check refuses it, move the import to module level only if doing so creates no cycle (`publication` imports `corpus` lazily, so a module-level import in `corpus.py` of `beliefs.publication` would cycle; keep it local and put it before the `require` if the checker needs the `require` to be the last statement before `with`).

- [ ] **Step 4: Implement the door changes** in `publication_doors.py`.

`_open_publication` gains the keyword `expected_view: CoordinationAddress | None = None` at the end of its signature. Directly after `assert type(resolved) is Node`, add:

```python
        if expected_view is not None and view.unpinned().pinned(resolved.uid) != expected_view:
            # spec §4.2: the selection was evaluated before this lock, against another revision
            raise PublicationRefused("view-revised")
```
`_bind_publication` gains `lifecycle: tuple[Entry, ...] = ()` at the end of its signature, and `report_of` passes `lifecycle=lifecycle` to `boundary._mint_publish_report`. `binding = binding_record(...)`, `tips, markers = _judge(...)` and the fallback's `return` line keep their exact spelling.

Add after `_bind_publication`:

```python
def _refuse_publication(
    writer: CorpusWriter,
    opened: OpenedPublication,
    entries: tuple[Entry, ...],
    *,
    clock: Callable[[], str],
    port: OperationPort | None = None,
) -> ActReport:
    """Publish-act-local §7: a refusal before the binding — the lifecycle entries
    reached, the refusing one last — written alone in one fulfilling transaction.
    Nothing was revealed remotely, so it carries no orphan fields."""
    writer.authority.require("publish", ("publication-binding",))
    writer.authority.require("corpus-write", ("act-report",))
    writer._require_pins_agree()
    operation_port = writer._require_bound_port(port)
    intent = opened.intent
    report = boundary._mint_publish_refusal(
        intent, observer=intent.actor, instrument=PUBLISH_INSTRUMENT, opened_at=intent.at, closed_at=clock(), entries=entries,
    )
    writer._state.unresolved = True
    operation_port.execute_fulfilling([writer._create_op(stored.act_report_node(report))], opened.digest)
    writer._reconstruct()
    return report


@dataclass(frozen=True)
class AttemptReading:
    opened: OpenedPublication
    reading: Literal["unfinished", "closed", "indeterminate"]
    outcome: str | None  # the report's last outcome type when closed


def _token_of(payload: bytes) -> str | None:
    try:
        return decode_publish_intent(payload).event_token
    except MalformedRecord:
        return None


def attempt_reading(writer: CorpusWriter, event_token: str, seam: MomentSeam) -> AttemptReading | None:
    """The completion reading of the publish intent carrying `event_token` on the
    written chain (publish-act-local §9, planning note), read by the fold's own
    rule: no committed fulfilment is `unfinished`; a present, matching,
    qualifying report is `closed`; a report the fold refuses is `indeterminate`.
    `None` when no such intent is on the chain."""
    written = Path(writer.root).resolve()
    view = seam.inspect_written(written)
    if type(view) is not WellFormedView:
        raise MalformedRecord(f"{written}: the written chain is not well formed")
    found = [e for e in view.entries if type(e) is IntentEntryView and _token_of(e.payload) == event_token]
    if not found:
        return None
    if len(found) != 1:
        raise MalformedRecord(f"{written}: {len(found)} publish intents carry token {event_token}")
    intent = decode_publish_intent(found[0].payload)
    opened = OpenedPublication(intent, found[0].digest)
    bound = ChainBound(written, writer.corpus_id, view, len(view.entries) - 1, True)
    for folded, outcome in _reports_at(bound, intent.view, intent.destination, seam):
        if folded.event_token != event_token:
            continue
        if type(outcome) is PositionRefused:
            return AttemptReading(opened, "indeterminate", None)
        if type(outcome) is PreBinding:
            return AttemptReading(opened, "closed", outcome.outcome)
        return AttemptReading(opened, "closed", str(outcome["type"]))
    return AttemptReading(opened, "unfinished", None)
```
Import `Literal` from `typing`, `Entry` from `beliefs.report` and `OperationPort` from `beliefs.runrecord` (already imported), and extend `__all__` with `"AttemptReading"` and `"attempt_reading"`. Confirm `ChainBound`'s constructor order with `grep -n "class ChainBound" -A8 src/beliefs/coordination.py` and match it.

- [ ] **Step 5: The inventories.** In `test_permit_boundary.py`'s `WRITE_ENTRY_POINTS`, after cut 39's entry:

```python
    # 2026-09-23 cut 40: the staging doors write through `_corpus.add`; the pre-binding refusal fulfils.
    "corpus.py:CorpusWriter._stage_record": "corpus-write",
    "corpus.py:CorpusWriter._stage_marker": "publish",
    "publication_doors.py:_refuse_publication": "publish",
```
In `test_permit_entry_points.py`, add three `Case`s on `_bind_publication`'s pattern, whose prepare, act and probe helpers sit at lines ~680–716:
- `Case("corpus.py:CorpusWriter._stage_record", "corpus-write", ("run",), False, _prepare_staging, _stage_record, _staging_probe)`, where `_prepare_staging` adopts a v2 profile over `work` with `DefaultExecutor`, `_stage_record` stages `node_to_markdown(stored.run_node("r", …))` through a writer built with the given authority, and `_staging_probe` is `_corpus_probe(work)`;
- `Case("corpus.py:CorpusWriter._stage_marker", "publish", ("publication",), False, _prepare_staging, _stage_marker, _staging_probe)`, which stages `marker_record(intent(), world_id="d" * 32, epoch="f" * 64, selection=("run:r",))`;
- `Case("publication_doors.py:_refuse_publication", "publish", ("publication-binding", "act-report"), True, _prepare_publication, _refuse, _publication_probe, ("corpus-write",))`, where `_refuse` calls `_refuse_publication(_publication_writer(authority, work), state["opened"], (<a staging-corrupt entry on the opened intent's binding address>,), clock=lambda: _PUBLICATION_AT)`.

- [ ] **Step 6: Run to verify they pass, then the inventories and the staleness probe**

```bash
cd python && uv run --frozen pytest tests/test_corpus_write.py tests/test_publication_doors.py -q
cd python && uv run --frozen pytest tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py tests/test_arm_staleness.py -q
```
Expected: green. `test_the_inventory_is_closed_in_both_directions` fails until all three keys are present, and `test_the_cases_cover_the_inventory_exactly` fails until all three `Case`s are.

- [ ] **Step 7: Commit**

```bash
tasks check && git add python/src/beliefs/corpus.py python/src/beliefs/publication_doors.py python/tests/test_corpus_write.py python/tests/test_publication_doors.py python/tests/test_permit_boundary.py python/tests/test_permit_entry_points.py tasks
git commit -m "feat(publish): staging doors, the pin re-check, the lifecycle binding, the pre-binding refusal and the attempt reading"
```

---

### Task 6: The act — `beliefs/publish.py`

**Files:**
- Create: `python/src/beliefs/publish.py`, `python/tests/test_publish.py`

**Interfaces:**
- Consumes: Tasks 1–5; the `root.py` wrappers (`init_corpus_root`, `init_world_root`, `open_corpus`, `open_world`, `export_head_artifact`, `replicate_root`, `restore_root`, `read_lifecycle_state`, `LifecycleState`, `metadata_root_for`); `current_epoch` (`beliefs.world.read`); `open_world_view` (`beliefs.world.view`); `evaluate_query` (`beliefs.world.selection`); `stored_query`; `ArtifactCarrier` and `ObserverSet` (`beliefs.world.verify`); `CorpusSubject` (`beliefs.world.anchors`); `Fresh`, `WorldConfig`, `load_manifest` (`beliefs.world`).
- Produces:
  - `publish(writer, resolver, world, *, view, destination, operations_root, staging_profile, clock, seam, port=None) -> PublishOutcome` and `resume_publish(writer, resolver, *, event_token, operations_root, staging_profile, clock, seam, port=None) -> PublishOutcome`;
  - `pending_publishes(writer, *, operations_root, seam) -> tuple[str, ...]`;
  - the outcome values `Published(event_token, corpus_id, marker, binding, artifact)`, `PublishRefused(event_token, outcome)` and `PublishUnresolved(event_token, reason)`;
  - the step functions Task 8 monkeypatches: `_initialize`, `_populate`, `_admit_and_export`, `_write_sibling`, `_replicate`, `_restore`, `_bind`, `_discard`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_publish.py`. These are portable: the classifier over raw staging files in `tmp_path`, plus two fixtures on `certified_work` for `attempt_reading` and the resume refusals. Task 8 covers the flows.

```python
"""The act's classifier and its resume refusals (publish-act-local design §5, §9)."""

from __future__ import annotations

import pytest
from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import stored
from beliefs.corpus import CorpusWriter
from authority import FULL
from beliefs.publication import marker_record
from beliefs.publish import _Population, _population
from beliefs.publish_request import Snapshot
from beliefs.report import StagingCorrupt


def _nodes():
    d = stored.dataset_node(title="d", resources=())
    r = stored.run_node("r", title="r", spec="s", produces=[d.id])
    s = stored.run_node("s", title="s", spec="s", produces=[])
    return sorted((d, r, s), key=lambda n: n.id)


@pytest.fixture()
def staging(tmp_path):
    profile = coordination_profile(None, version=2)
    writer = CorpusWriter(tmp_path / "staging", lambda root: DefaultExecutor(root), authority=FULL, profile=profile)
    manifest = writer.adopt_manifest(profile=pins_for(profile))
    nodes = _nodes()
    snapshot = Snapshot("e" * 32, tuple((n.id, node_to_markdown(n)) for n in nodes))
    marker = marker_record(intent(event_token="e" * 32), world_id="d" * 32, epoch="f" * 64, selection=tuple(n.id for n in nodes))
    return writer, manifest.corpus_id, snapshot, marker


def _write(writer, text):
    writer._stage_record(text)


def test_an_empty_staging_is_a_prefix_of_zero(staging):
    writer, corpus_id, snapshot, marker = staging
    assert _population(writer, corpus_id, snapshot, marker) == _Population(0, False)


def test_a_true_prefix_resumes_at_its_length(staging):
    writer, corpus_id, snapshot, marker = staging
    _write(writer, snapshot.records[0][1])
    assert _population(writer, corpus_id, snapshot, marker) == _Population(1, False)


def test_complete_requires_the_marker_byte_equal(staging):
    writer, corpus_id, snapshot, marker = staging
    for _, text in snapshot.records:
        _write(writer, text)
    writer._stage_marker(marker)
    assert _population(writer, corpus_id, snapshot, marker) == _Population(3, True)


def test_a_hole_is_corrupt(staging):
    writer, corpus_id, snapshot, marker = staging
    _write(writer, snapshot.records[1][1])
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "hole", (snapshot.records[0][0],))


def test_an_extra_record_is_corrupt(staging):
    writer, corpus_id, snapshot, marker = staging
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    _write(writer, node_to_markdown(extra))
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "extra", (extra.id,))


def test_a_byte_mismatch_is_corrupt(staging):
    writer, corpus_id, snapshot, marker = staging
    _write(writer, snapshot.records[0][1])
    path = writer.root / writer._relative_path(stored.dataset_node(title="d", resources=()))
    path.chmod(0o644)
    path.write_text(path.read_text() + "\n")
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "bytes", (snapshot.records[0][0],))


def test_a_marker_present_early_or_unequal_is_corrupt(staging):
    writer, corpus_id, snapshot, marker = staging
    writer._stage_marker(marker)
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "marker", (marker.id,))
```
The byte-mismatch test's `path` must be the snapshot's first record's path. Find it with `writer._relative_path(<the node whose id is snapshot.records[0][0]>)`: build `nodes = _nodes()` once and index by id. If a record file's mode forbids writing, the `chmod` restores it.

The resume refusals need a real chain. Add them to Task 8's module (`test_resume_refuses_another_actor_and_another_profile_writing_nothing`, Review Focus 4) rather than here.

- [ ] **Step 2: Run to verify they fail.** Run `cd python && uv run --frozen pytest tests/test_publish.py -q`. Expected: `ModuleNotFoundError: No module named 'beliefs.publish'`.

- [ ] **Step 3: Implement** `python/src/beliefs/publish.py`:

```python
"""The publish act, local (publish-act-local design; layer design §6.1): step 0
selects, refuses, appends the intent and freezes the snapshot and the request;
steps 1–6 stage, admit, export and reveal; step 8 binds; step 9 discards. A
retry reinvokes the same sequence from the request (§9). Every lifecycle call
goes through `root.py`'s wrappers; this module imports nothing of `atoms`."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused, MomentSeam
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.durable import ensure_directory, write_create_only
from beliefs.errors import CreateOnlyCollision, MalformedRecord, PublicationRefused, ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.profile import ProfileSpec
from beliefs.publication import BINDING_KIND, MARKER_KIND, binding_address, binding_uid, marker_record, marker_uid
from beliefs.publication_doors import (
    OpenedPublication,
    _bind_publication,
    _open_publication,
    _refuse_publication,
    attempt_reading,
)
from beliefs.publish_request import (
    PublishRequest,
    Snapshot,
    closure_missing,
    decode_request,
    decode_snapshot,
    derive_pins,
    encode_request,
    encode_snapshot,
    pins_of,
    require_usable,
    staging_world_id_for,
)
from beliefs.report import (
    Entry,
    Exported,
    ExportCollision,
    PublicationExportEntry,
    PublicationRequestEntry,
    PublicationRevealEntry,
    PublicationStagingEntry,
    RequestCorrupt,
    Revealed,
    RevealRefused,
    Staged,
    StagingCorrupt,
    outcome_type,
)
from beliefs.root import (
    LifecycleState,
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.runrecord import OperationPort
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.world.read import current_epoch
from beliefs.world.registry import World
from beliefs.world.selection import evaluate_query
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view

__all__ = ["PublishRefused", "PublishUnresolved", "Published", "pending_publishes", "publish", "resume_publish"]


@dataclass(frozen=True)
class Published:
    event_token: str
    corpus_id: str
    marker: str
    binding: str
    artifact: str


@dataclass(frozen=True)
class PublishRefused:
    event_token: str
    outcome: str  # the report's last outcome type


@dataclass(frozen=True)
class PublishUnresolved:
    event_token: str
    reason: str  # "no-request" | "indeterminate" | "binding-without-report"


PublishOutcome = Published | PublishRefused | PublishUnresolved


@dataclass(frozen=True)
class _Attempt:
    writer: CorpusWriter
    resolver: CoordinationResolver
    opened: OpenedPublication
    request: PublishRequest
    snapshot: Snapshot
    op: Path
    staging_profile: ProfileSpec
    clock: Callable[[], str]
    seam: MomentSeam
    port: OperationPort | None

    @property
    def token(self) -> str:
        return self.opened.intent.event_token

    @property
    def subject(self) -> str:
        return str(binding_address(self.opened.intent.view, self.opened.intent.destination))


@dataclass(frozen=True)
class _Population:
    present: int
    complete: bool


def _require_publishes(writer: CorpusWriter) -> None:
    writer.authority.require("publish", (BINDING_KIND, MARKER_KIND))
    writer.authority.require("corpus-write", ("act-report", *stored.WORLD_KINDS))
    writer.authority.require("lifecycle")
    writer.authority.require("registry")


def _op_dir(operations_root: Path, event_token: str) -> Path:
    return operations_root / "publish" / event_token


# --- step 0 ------------------------------------------------------------------


def publish(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    world: World,
    *,
    view: CoordinationAddress,
    destination: Destination,
    operations_root: Path,
    staging_profile: ProfileSpec,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> PublishOutcome:
    """Publish `view` to a local `destination` (spec §3–§8)."""
    _require_publishes(writer)
    if destination.type != "local":
        raise ValidationRefused("remote destinations arrive in cut 41")
    forbidden = (*resolver.mounted(), *world.config.corpus_roots, world.config.world_root)
    operations_root, resolved_destination = require_usable(operations_root, destination, forbidden=forbidden)
    # spec §4.1 item 7: the resolved path is the destination the intent and the request freeze
    destination = Destination.local(str(resolved_destination))
    resolved = resolver.resolve(view.unpinned())
    if resolved is None:
        raise PublicationRefused("view-unresolved")
    if type(resolved) is CoordinationRefused:
        raise PublicationRefused("divergent-view", tips=resolved.tips)
    assert type(resolved) is Node
    pinned = view.unpinned().pinned(resolved.uid)
    query = stored_query(resolved)
    published = current_epoch(world)
    read = open_world_view(world, published)
    selection = evaluate_query(read, query)
    if not selection.complete:
        absent = {*selection.absent, *(step.corpus_id for step in selection.unresolved if step.corpus_id is not None)}
        raise PublicationRefused("selection-incomplete", corpus_ids=tuple(sorted(absent)))
    if not selection.selected:
        raise PublicationRefused("empty-selection")
    if missing := closure_missing(read, selection.selected):
        raise PublicationRefused("closure-incomplete", refs=missing)
    pins = derive_pins(
        {corpus_id: read.captured_manifest(corpus_id).profile for corpus_id in selection.contributing},
        load_manifest(writer.root).profile,
    )
    if pins_of(staging_profile) != pins:
        raise PublicationRefused("profile-disagrees")
    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)
    opened = _open_publication(
        writer, resolver, view=view.unpinned(), destination=destination, clock=clock, seam=seam, port=port, expected_view=pinned,
    )
    token = opened.intent.event_token
    snapshot = Snapshot(token, records)
    request = PublishRequest(
        event_token=token,
        view=opened.intent.view,
        destination=destination,
        epoch=published.packaging_identity,
        world_id=world.config.world_id,
        pins=pins,
        selection=snapshot.identity(),
        staging_world_id=staging_world_id_for(token),
    )
    op = _op_dir(operations_root, token)
    ensure_directory(op)
    write_create_only(op / "selection.v1", encode_snapshot(snapshot))
    write_create_only(op / "request.v1", encode_request(request))
    attempt = _Attempt(writer, resolver, opened, request, snapshot, op, staging_profile, clock, seam, port)
    return _run(attempt)


# --- steps 1–9 -----------------------------------------------------------------


def _initialize(a: _Attempt) -> tuple[CorpusWriter, World, str] | StagingCorrupt:
    """Step 1, reinvoked on every retry: each initializer's predicate decides."""
    staging, world_root = a.op / "staging", a.op / "world"
    init_corpus_root(staging, authority=a.writer.authority)
    staging_writer = open_corpus(staging, authority=a.writer.authority, profile=a.staging_profile)
    if (staging / "corpus.yaml").exists():
        manifest = load_manifest(staging)
        if manifest.profile != a.request.pins:
            return StagingCorrupt(manifest.corpus_id, "pins-foreign", ())
    else:
        staging_writer.adopt_manifest(profile=a.request.pins)
    corpus_id = load_manifest(staging).corpus_id
    config = WorldConfig(world_root, a.request.staging_world_id, (staging,))
    init_world_root(config, authority=a.writer.authority)
    return staging_writer, open_world(config, authority=a.writer.authority), corpus_id


def _expected_marker(a: _Attempt) -> Node:
    return marker_record(
        a.opened.intent, world_id=a.request.world_id, epoch=a.request.epoch, selection=tuple(i for i, _ in a.snapshot.records),
    )


def _population(staging: CorpusWriter, corpus_id: str, snapshot: Snapshot, marker: Node) -> _Population | StagingCorrupt:
    """Spec §5's classification: a true prefix, complete, or corrupt."""
    root = Path(staging.root)
    present = {node.id: (root / staging._relative_path(node)).read_bytes() for node in ReadView.opened_at(root).iter_stored()}
    order = [record_id for record_id, _ in snapshot.records]
    extras = sorted(set(present) - set(order) - {marker.id})
    if extras:
        return StagingCorrupt(corpus_id, "extra", (extras[0],))
    n = 0
    for record_id, text in snapshot.records:
        if record_id not in present:
            break
        if present[record_id] != text.encode("utf-8"):
            return StagingCorrupt(corpus_id, "bytes", (record_id,))
        n += 1
    if any(record_id in present for record_id in order[n:]):
        return StagingCorrupt(corpus_id, "hole", (order[n],))
    if marker.id in present:
        if n != len(order) or present[marker.id] != node_to_markdown(marker).encode("utf-8"):
            return StagingCorrupt(corpus_id, "marker", (marker.id,))
        return _Population(n, True)
    return _Population(n, complete=False)


def _populate(a: _Attempt, staging: CorpusWriter, corpus_id: str) -> StagingCorrupt | None:
    """Step 2: continue a true prefix, write the marker last."""
    marker = _expected_marker(a)
    state = _population(staging, corpus_id, a.snapshot, marker)
    if type(state) is StagingCorrupt:
        return state
    assert type(state) is _Population
    if not state.complete:
        for _, text in a.snapshot.records[state.present :]:
            staging._stage_record(text)
        staging._stage_marker(marker)
    again = _population(staging, corpus_id, a.snapshot, marker)
    return again if type(again) is StagingCorrupt else None


def _admit_and_export(a: _Attempt, world: World, corpus_id: str) -> bytes:
    """Step 3: the admission reinvoked (its predicate converges), then the export."""
    world.admit(a.op / "staging", provenance=Fresh())
    return export_head_artifact(world, CorpusSubject(corpus_id))


def _export_root(a: _Attempt, corpus_id: str) -> Path:
    return Path(a.request.destination.locator) / corpus_id


def _sibling(a: _Attempt, corpus_id: str) -> Path:
    return Path(a.request.destination.locator) / f"{corpus_id}.head-artifact.v1"


def _write_sibling(a: _Attempt, corpus_id: str, artifact: bytes) -> ExportCollision | None:
    """Step 5: the create-only sibling."""
    sibling = _sibling(a, corpus_id)
    try:
        write_create_only(sibling, artifact)
    except CreateOnlyCollision:
        return ExportCollision(corpus_id, sibling.name)
    return None


def _serviceable(root: Path) -> bool:
    return root.exists() and read_lifecycle_state(root) is LifecycleState.READ_ONLY_SERVICEABLE


def _replicate(a: _Attempt, corpus_id: str) -> None:
    """Step 6, first half: the exact replication, reinvoked on every retry
    whatever the export root's state (spec §6 step 6): its retained-operation
    check, not the root's serviceability, proves the root is this attempt's. A
    foreign occupant refuses, and the refusal propagates (spec §16 item 6)."""
    replicate_root(a.op / "staging", _export_root(a, corpus_id), authority=a.writer.authority)


def _restore(a: _Attempt, corpus_id: str) -> str:
    """Step 6, second half: the reveal — `restore_root` against the sibling read
    back. Called only after `_replicate` has proven the root is this attempt's."""
    export = _export_root(a, corpus_id)
    if _serviceable(export):
        return "validated"
    observers = ObserverSet((ArtifactCarrier.from_bytes(_sibling(a, corpus_id).read_bytes()),))
    report = restore_root(export, CorpusSubject(corpus_id), observers, authority=a.writer.authority)
    if _serviceable(export):
        return "validated"
    if report.outcome == "validated":
        raise MalformedRecord(f"{export}: restore validated but granted nothing")  # the engine's to explain, not a verdict
    return report.outcome


def _bind(a: _Attempt, corpus_id: str, artifact_identity: str, entries: tuple[Entry, ...]):
    """Step 8: the binding door, carrying the lifecycle entries."""
    return _bind_publication(
        a.writer, a.resolver, a.opened, corpus_id=corpus_id, marker=marker_uid(a.token), artifact=artifact_identity,
        remotely_revealed=False, clock=a.clock, seam=a.seam, port=a.port,
        lifecycle=entries,
    )


def _discard(op: Path) -> None:
    """Step 9: staging and its world go; the request and the snapshot stay."""
    for path in (op / "staging", op / "world"):
        for target in (path, metadata_root_for(path)):
            if target.exists():
                shutil.rmtree(target)


def _refused(a: _Attempt, entries: tuple[Entry, ...]) -> PublishRefused:
    report = _refuse_publication(a.writer, a.opened, entries, clock=a.clock, port=a.port)
    return PublishRefused(a.token, outcome_type(report.entries[-1].outcome))


def _run(a: _Attempt) -> PublishOutcome:
    """Steps 1–9, reinvoked identically on every retry (spec §2 decision 8)."""
    initialized = _initialize(a)
    if type(initialized) is StagingCorrupt:
        return _refused(a, (PublicationStagingEntry(a.subject, initialized),))
    staging, world, corpus_id = initialized
    corrupt = _populate(a, staging, corpus_id)
    if corrupt is not None:
        return _refused(a, (PublicationStagingEntry(a.subject, corrupt),))
    entries: list[Entry] = [PublicationStagingEntry(a.subject, Staged(corpus_id, len(a.snapshot.records)))]
    artifact = _admit_and_export(a, world, corpus_id)
    collision = _write_sibling(a, corpus_id, artifact)
    if collision is not None:
        return _refused(a, (*entries, PublicationExportEntry(a.subject, collision)))
    artifact_identity = sha256(artifact).hexdigest()
    entries.append(PublicationExportEntry(a.subject, Exported(corpus_id, artifact_identity)))
    _replicate(a, corpus_id)
    verdict = _restore(a, corpus_id)
    if verdict != "validated":
        return _refused(a, (*entries, PublicationRevealEntry(a.subject, RevealRefused(corpus_id, verdict))))
    entries.append(PublicationRevealEntry(a.subject, Revealed(corpus_id)))
    outcome = _bind(a, corpus_id, artifact_identity, tuple(entries))
    if outcome.binding is None:
        return PublishRefused(a.token, outcome_type(outcome.report.entries[-1].outcome))
    _discard(a.op)
    return Published(a.token, corpus_id, marker_uid(a.token), outcome.binding.uid, artifact_identity)


# --- resumption (§9) --------------------------------------------------------------


def _binding_present(writer: CorpusWriter, opened: OpenedPublication) -> bool:
    address = binding_address(opened.intent.view, opened.intent.destination)
    binding_id = f"{BINDING_KIND}:{address.project}.{address.local}.{binding_uid(opened.intent.event_token)}"
    return writer._corpus.store.path_for(binding_id).exists()


def _load(op: Path, opened: OpenedPublication) -> tuple[PublishRequest, Snapshot] | RequestCorrupt:
    try:
        request = decode_request((op / "request.v1").read_bytes())
    except MalformedRecord:
        return RequestCorrupt("undecodable")
    intent = opened.intent
    if request.event_token != intent.event_token or request.view != intent.view or request.destination != intent.destination:
        return RequestCorrupt("intent-disagrees")
    if not (op / "selection.v1").is_file():
        return RequestCorrupt("snapshot-missing")
    try:
        snapshot = decode_snapshot((op / "selection.v1").read_bytes())
    except MalformedRecord:
        return RequestCorrupt("snapshot-undecodable")
    if snapshot.identity() != request.selection or snapshot.event_token != intent.event_token:
        return RequestCorrupt("snapshot-mismatch")
    return request, snapshot


def resume_publish(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    *,
    event_token: str,
    operations_root: Path,
    staging_profile: ProfileSpec,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> PublishOutcome:
    """Resume one attempt from its request (spec §9)."""
    _require_publishes(writer)
    reading = attempt_reading(writer, event_token, seam)
    if reading is None:
        raise ValidationRefused(f"no publish intent carries token {event_token}")
    if writer.authority.actor != reading.opened.intent.actor:
        raise ValidationRefused("a publish resumes only under its intent's actor")
    op = _op_dir(Path(operations_root).resolve(), event_token)
    present = _binding_present(writer, reading.opened)
    if reading.reading == "indeterminate":
        return PublishUnresolved(event_token, "indeterminate")
    if reading.reading == "closed":
        if not present:
            assert reading.outcome is not None
            return PublishRefused(event_token, reading.outcome)
        request = decode_request((op / "request.v1").read_bytes())
        _discard(op)
        return _published_from_disk(writer, reading.opened, request)
    if present:
        return PublishUnresolved(event_token, "binding-without-report")
    if not (op / "request.v1").is_file():
        return PublishUnresolved(event_token, "no-request")
    loaded = _load(op, reading.opened)
    if type(loaded) is RequestCorrupt:
        report = _refuse_publication(writer, reading.opened, (PublicationRequestEntry(
            str(binding_address(reading.opened.intent.view, reading.opened.intent.destination)), loaded),), clock=clock, port=port)
        return PublishRefused(event_token, outcome_type(report.entries[-1].outcome))
    request, snapshot = loaded
    if pins_of(staging_profile) != request.pins:
        raise ValidationRefused("a publish resumes only under a staging profile holding its request's pins")
    return _run(_Attempt(writer, resolver, reading.opened, request, snapshot, op, staging_profile, clock, seam, port))


def _published_from_disk(writer: CorpusWriter, opened: OpenedPublication, request: PublishRequest) -> Published:
    """A done attempt's outcome, read back from its binding revision."""
    address = binding_address(opened.intent.view, opened.intent.destination)
    binding_id = f"{BINDING_KIND}:{address.project}.{address.local}.{binding_uid(opened.intent.event_token)}"
    facet = writer.read_view.get(binding_id).facets[stored.COORDINATION_FACET]
    return Published(opened.intent.event_token, facet["corpus_id"], facet["marker"], binding_uid(opened.intent.event_token), facet["artifact"])


def pending_publishes(writer: CorpusWriter, *, operations_root: Path, seam: MomentSeam) -> tuple[str, ...]:
    """Every request under the operations root whose intent is `unfinished`,
    ascending by token (spec §3)."""
    root = Path(operations_root).resolve() / "publish"
    tokens: list[str] = []
    for request in sorted(root.glob("*/request.v1")) if root.is_dir() else ():
        token = request.parent.name
        reading = attempt_reading(writer, token, seam)
        if reading is not None and reading.reading == "unfinished":
            tokens.append(token)
    return tuple(tokens)
```
The step functions `_initialize`, `_populate`, `_admit_and_export`, `_write_sibling`, `_replicate`, `_restore`, `_bind` and `_discard` are module-level, and `_run` calls them through the module namespace, so Task 8's monkeypatching reaches them. Two lines are Task 9's sabotage sites and must stay unique in `publish.py`: `        lifecycle=entries,` (in `_bind`) and `        _discard(op)` (in `resume_publish`'s closed branch). `_run` spells its call `    _discard(a.op)`.

- [ ] **Step 4: Run to verify they pass, then the boundaries**

```bash
cd python && uv run --frozen pytest tests/test_publish.py tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_arm_staleness.py -q
cd python && uv run --frozen pyright src/beliefs/publish.py src/beliefs/publish_request.py src/beliefs/durable.py
```
Expected: green, and 0 pyright errors. `publish.py` calls no primitive directly, so `WRITE_ENTRY_POINTS` does not gain it. If `test_permit_boundary.py` reports `publish.py:publish` as an unlisted caller, the call it names is a primitive: route it through the door that owns it. Do not add `publish.py` to the inventory.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/publish.py python/tests/test_publish.py tasks
git commit -m "feat(publish): the local publish act — step 0 through step 9, and its resumption (Y5–Y9)"
```

---

### Task 7: Arrival — `beliefs/publication_arrival.py`

**Files:**
- Create: `python/src/beliefs/publication_arrival.py`, `python/tests/test_publication_arrival.py`

**Interfaces:**
- Consumes: `PublicationArrivalRefused` (Task 3); `root.admit_arrival`; `ReplicaOf` and `load_manifest` (`beliefs.world`); `publication_content_malformed` and `marker_consistent`.
- Produces: `admit_publication(world, root, observers) -> tuple[AdmissionRecord, LogReport]`, which raises `PublicationArrivalRefused` with the reasons `marker-absent`, `marker-duplicated`, `marker-malformed`, `marker-inconsistent`, `binding-present` and `selection-mismatch`.

- [ ] **Step 1: Write the failing tests.** Unit tests over hand-built roots in `tmp_path`. `admit_arrival` is monkeypatched to record its call, so these tests prove the checks and the order, and Task 8's Y10 arms prove the admission.

```python
"""Marker-required arrival (publish-act-local design §10)."""

from __future__ import annotations

import pytest
from coordination_fixtures import coordination_profile, raw_add
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import publication_arrival, stored
from beliefs.corpus import CorpusWriter
from authority import FULL
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication import binding_record, marker_record
from beliefs.publication_arrival import admit_publication


@pytest.fixture()
def arriving(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(publication_arrival, "admit_arrival", lambda *args, **kwargs: calls.append((args, kwargs)) or ("record", "report"))
    profile = coordination_profile(None, version=2)
    writer = CorpusWriter(tmp_path / "arriving", lambda root: DefaultExecutor(root), authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    run = stored.run_node("r", title="r", spec="s", produces=[])
    writer._stage_record(__import__("nodes.core.frontmatter", fromlist=["node_to_markdown"]).node_to_markdown(run))
    return writer, run, calls


def _marker(selection):
    return marker_record(intent(), world_id="d" * 32, epoch="f" * 64, selection=selection)


def test_a_consistent_publication_is_handed_to_admit_arrival(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    assert admit_publication("world", writer.root, "observers") == ("record", "report")
    ((args, _),) = calls
    assert args[1] == writer.root.resolve() and args[2].parent_corpus_id == writer.corpus_id


def test_no_marker_refuses_before_admission(arriving):
    writer, _, calls = arriving
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-absent" and calls == []


def test_two_markers_refuse(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    raw_add(writer.root, marker_record(intent(event_token="9" * 32), world_id="d" * 32, epoch="f" * 64, selection=(run.id,)))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-duplicated" and calls == []


def test_a_malformed_marker_refuses(arriving):
    writer, run, calls = arriving
    marker = _marker((run.id,))
    marker.facets[stored.COORDINATION_FACET]["selection"] = ["not an id"]
    raw_add(writer.root, marker)
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-malformed" and calls == []


def test_a_binding_in_the_root_refuses(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    raw_add(writer.root, binding_record(intent(), corpus_id="1" * 32, marker="2" * 32, artifact="3" * 64))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "binding-present" and calls == []


@pytest.mark.parametrize("extra", [True, False], ids=["record-beyond-selection", "selected-record-missing"])
def test_records_other_than_the_selection_refuse(arriving, extra):
    writer, run, calls = arriving
    other = stored.run_node("s", title="s", spec="s", produces=[])
    if extra:
        raw_add(writer.root, other)
        writer._stage_marker(_marker((run.id,)))
    else:
        writer._stage_marker(_marker(tuple(sorted((run.id, other.id)))))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "selection-mismatch" and caught.value.refs == (other.id,) and calls == []
```
`raw_add(root, node)` writes a node's file without a registration (`coordination_fixtures.raw_add`). If its signature differs, adapt the calls to it.

- [ ] **Step 2: Run to verify they fail.** Run `cd python && uv run --frozen pytest tests/test_publication_arrival.py -q`. Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `python/src/beliefs/publication_arrival.py`:

```python
"""Marker-required arrival (publish-act-local design §10; layer design §6.3): a
published corpus is admitted only through its marker, checked before any write,
then through cut 8's arrival act."""

from __future__ import annotations

from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication import BINDING_KIND, MARKER_KIND, marker_consistent, publication_content_malformed
from beliefs.root import admit_arrival
from beliefs.world import ReplicaOf, load_manifest

__all__ = ["admit_publication"]


def admit_publication(world, root: Path, observers):
    """Refuse, before `admit_arrival` writes anything, a root with no marker, two
    markers, a malformed or inconsistent marker, a binding, or records other
    than the marker's selection; then admit it as a replica of itself."""
    root = Path(root).resolve()
    records = tuple(ReadView.opened_at(root).iter_stored())
    markers = [node for node in records if node.kind == MARKER_KIND]
    if not markers:
        raise PublicationArrivalRefused("marker-absent")
    if len(markers) > 1:
        raise PublicationArrivalRefused("marker-duplicated")
    (marker,) = markers
    if publication_content_malformed(marker):
        raise PublicationArrivalRefused("marker-malformed")
    if not marker_consistent(marker):
        raise PublicationArrivalRefused("marker-inconsistent")
    if any(node.kind == BINDING_KIND for node in records):
        raise PublicationArrivalRefused("binding-present")
    held = sorted(node.id for node in records if node.kind != MARKER_KIND)
    selection = list(marker.facets[stored.COORDINATION_FACET]["selection"])
    if held != selection:
        first = sorted(set(held) ^ set(selection))[0]
        raise PublicationArrivalRefused("selection-mismatch", refs=(first,))
    return admit_arrival(world, root, ReplicaOf(load_manifest(root).corpus_id), observers)
```
The binding check runs before the selection check so that a root carrying a binding names that reason. The spec's §10 table lists it last; the planning note records the order.

- [ ] **Step 4: Run to verify they pass.** Run `cd python && uv run --frozen pytest tests/test_publication_arrival.py tests/test_capability_boundary.py -q`. Expected: green.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/publication_arrival.py python/tests/test_publication_arrival.py tasks
git commit -m "feat(publish): marker-required arrival refuses before any write (Y10)"
```

---

### Task 8: The acceptance module — `test_publish_act_acceptance.py`

**Files:**
- Create: `python/tests/acceptance/test_publish_act_acceptance.py`

**Interfaces:**
- Consumes:
  - Tasks 1–7;
  - `tests/acceptance/conftest.py`'s `work_directory`;
  - `test_world_view_acceptance.durable_world` and its `corpus(profile)` helper, `test_world_selection.topic_nodes` and `test_world_receipts.hold_shipped`;
  - `coordination_fixtures.coordination_profile`, `content_for` and `raw_add`;
  - `test_publication_records_acceptance.py`'s `_chain` and `_closed_durably` shapes.
- Produces: fifteen unit test functions, whose names Task 9's `UNIT_CHECKS` cites, plus the Review Focus tests 3 and 4.

- [ ] **Step 1: Write the module header and fixtures**

```python
"""Conformance cut 40 — the publish act, local (publish-act-local design §14.2).
Fifteen declaration units over real roots on the certified volume, each run
under exactly the publication permit (decision 6)."""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from itertools import count
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace

import pytest
from authority import ACTOR, FULL
from coordination_fixtures import content_for, coordination_profile, raw_add
from nodes.core.frontmatter import node_to_markdown
from profiles import BASE, WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for
from test_world_receipts import hold_shipped
from test_world_selection import topic_nodes

from beliefs import publish as act
from beliefs import stored
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.errors import PublicationArrivalRefused, PublicationRefused, SelectionRefused
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publication import binding_record, marker_record, marker_uid
from beliefs.publication_arrival import admit_publication
from beliefs.publication_doors import _open_publication, attempt_reading
from beliefs.publish import Published, PublishRefused, PublishUnresolved, pending_publishes, publish, resume_publish
from beliefs.root import (
    LifecycleState,
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    moment_seam,
    open_corpus,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import Fresh, WorldConfig, epoch, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.publish_request import decode_snapshot
from beliefs.view_query import stored_query
from beliefs.world.read import current_epoch
from beliefs.world.selection import evaluate_query
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view
from durable_fixture import pinned as _pinned
from beliefs.errors import ValidationRefused

AUTHORITY = scoped_authority(RequiredCapabilities.publishes(), ACTOR)
"""Exactly the publication permit: the writers that call `publish` and `resume_publish` bind it."""
SETUP = FULL
"""Fixture construction — corpora, worlds, epochs, the view's revisions — is not
the act under test and runs under the full permit (finding 6)."""
V2 = coordination_profile(None, version=2)
KINDS = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset", "run"]}]}]}
_counter = count()


class Clock:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-23T00:00:{self.n:02d}Z"


class Crash(Exception):
    """A process death at a step boundary: in-memory state is discarded after it."""


def crash(monkeypatch, name: str, *, before: bool = False, on_call: int = 1):
    original = getattr(act, name)
    calls = {"n": 0}

    def crashing(*args, **kwargs):
        calls["n"] += 1
        if before and calls["n"] == on_call:
            raise Crash(name)
        result = original(*args, **kwargs)
        if not before and calls["n"] == on_call:
            raise Crash(name)
        return result

    monkeypatch.setattr(act, name, crashing)


@pytest.fixture()
def source(work_directory, monkeypatch):
    """A source world of two BASE corpora (topic_nodes), a written root under
    coordination v2 holding the view (a project whose query selects datasets and
    runs), an operations root and a destination — all on the certified volume."""
    base = Path(mkdtemp(prefix="cut40-", dir=work_directory)).resolve()
    roots: list[Path] = []

    def corpus(profile=BASE, nodes=()):
        path = base / f"corpus-{next(_counter)}"
        roots.append(path)
        init_corpus_root(path, authority=SETUP)
        writer = open_corpus(path, authority=SETUP, profile=profile)
        manifest = writer.adopt_manifest(profile=pins_for(profile))
        for node in nodes:
            writer.add(node.model_copy(deep=True))
        return manifest.corpus_id, path, writer

    try:
        alpha_nodes, beta_nodes = topic_nodes()
        a, alpha, alpha_writer = corpus(nodes=tuple(n for n in alpha_nodes if n.kind != "project"))
        b, beta, _ = corpus(nodes=beta_nodes)
        world_root = base / "world"
        config = WorldConfig(world_root, "e" * 32, (alpha, beta))
        init_world_root(config, authority=SETUP)
        world = open_world(config, authority=SETUP)
        world.admit(alpha, provenance=Fresh())
        world.admit(beta, provenance=Fresh())
        epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
        written = base / "written"
        roots.append(written)
        init_corpus_root(written, authority=SETUP)
        open_corpus(written, authority=SETUP, profile=V2).adopt_manifest(profile=pins_for(V2))
        resolver = CoordinationResolver({written.resolve(): V2})
        writer = open_corpus(written, authority=SETUP, profile=V2, coordination_resolver=resolver)
        project = writer.mint_coordination("project", content=content_for("project", query=KINDS))
        ops, dest = base / "ops", base / "dest"
        ops.mkdir()
        dest.mkdir()
        publisher = open_corpus(written, authority=AUTHORITY, profile=V2, coordination_resolver=resolver)
        publishing_world = open_world(config, authority=AUTHORITY)  # open_world requires no family
        yield SimpleNamespace(
            setup_writer=writer, setup_world=world,
            base=base, world=publishing_world, alpha=alpha, alpha_writer=alpha_writer, corpus=corpus, written=written, writer=publisher,
            resolver=resolver, view=coordination_revision(project).address, ops=ops, dest=dest, a=a, b=b,
            destination=Destination.local(str(dest)),
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)
        for root in roots:
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def run(s, **changes):
    arguments = dict(view=s.view, destination=s.destination, operations_root=s.ops, staging_profile=V2, clock=Clock(), seam=moment_seam())
    arguments.update(changes)
    return publish(s.writer, s.resolver, s.world, **arguments)


def fresh_writer(s):
    """A new publishing writer over the written root: in-memory state discarded, as after a crash."""
    return open_corpus(s.written, authority=AUTHORITY, profile=V2, coordination_resolver=s.resolver)


def setup_writer(s):
    """A setup writer over the written root, for the view's revisions and raw fixtures."""
    return open_corpus(s.written, authority=SETUP, profile=V2, coordination_resolver=s.resolver)


def resume(s, token):
    return resume_publish(fresh_writer(s), s.resolver, event_token=token, operations_root=s.ops, staging_profile=V2,
                          clock=Clock(), seam=moment_seam())


def _payloads(s) -> list[dict]:
    """The written chain's intent payloads, decoded, in chain order."""
    import json

    view = moment_seam().inspect_written(s.written.resolve())
    return [json.loads(e.payload) for e in view.entries if type(e).__name__ == "IntentEntryView"]


def token_of_last_intent(s) -> str:
    """The newest publish intent's token on the written chain."""
    return [p for p in _payloads(s) if p.get("domain") == "science.publish-intent.v1"][-1]["event_token"]


def _project(s):
    """The view's current revision, resolved live."""
    return s.resolver.resolve(s.view.unpinned())


def _revise_query(s, query) -> None:
    """Revise the view's query (a new project revision superseding the tip) and repoint `s.view`."""
    tip = _project(s)
    revised = setup_writer(s).revise_coordination(
        "project", s.view.unpinned(), predecessors=(tip.uid,), content=content_for("project", query=query),
    )
    s.view = coordination_revision(revised).address


def chain_tip(s) -> str:
    return moment_seam().inspect_written(s.written.resolve()).tip


def published_records(root: Path) -> dict[str, bytes]:
    return {n.id: (root / Path(stored.path_for_id(n.id))).read_bytes() for n in ReadView.opened_at(root).iter_stored()}
```
`published_records` needs a node's relative path. Use `CorpusWriter(root, …)._relative_path(node)` through `open_corpus(root, authority=AUTHORITY, profile=V2)`, or `nodes.core.paths.path_for_node_id(node.id)`, whichever the tree uses (`test_publication_doors.py` imports `path_for_node_id`); replace `stored.path_for_id`. `moment_seam().inspect_written` is the registered inspector cut 39's module uses. If `IntentEntryView` payloads are bytes, `json.loads` accepts them.

- [ ] **Step 2: The units.**

```python
def _query(*kinds):
    return {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": list(kinds)}]}]}


def _pins_disagree(s):
    """Two more corpora whose biology pins disagree, both covered, datasets selected."""
    ids = []
    for profile, title in ((WITH_BIOLOGY, "bio-1"), (WITH_BIOLOGY_OTHER, "bio-2")):
        corpus_id, root, _ = s.corpus(profile, nodes=(stored.dataset_node(title=title, resources=_pinned(title)),))
        config = WorldConfig(s.world.config.world_root, s.world.config.world_id, (*s.world.config.corpus_roots, root))
        s.setup_world = open_world(config, authority=SETUP)
        s.setup_world.admit(root, provenance=Fresh())
        s.world = open_world(config, authority=AUTHORITY)
        ids.append(corpus_id)
    epoch.build_epoch(s.setup_world, coverage=frozenset({s.a, s.b, *ids}), bindings=hold_shipped(s.setup_world))
    _revise_query(s, _query("dataset"))
    return {}


def _coordination_v1(s):
    v1 = coordination_profile(None, version=1)
    written = s.base / "written-v1"
    init_corpus_root(written, authority=SETUP)
    open_corpus(written, authority=SETUP, profile=v1).adopt_manifest(profile=pins_for(v1))
    s.resolver = CoordinationResolver({written.resolve(): v1})
    minted = open_corpus(written, authority=SETUP, profile=v1, coordination_resolver=s.resolver).mint_coordination(
        "project", content=content_for("project", query=KINDS)
    )
    s.writer = open_corpus(written, authority=AUTHORITY, profile=v1, coordination_resolver=s.resolver)
    s.written = written
    s.view = coordination_revision(minted).address
    return {}


def _drift(s):
    s.alpha_writer.add(stored.dataset_node(title="late", resources=_pinned("late")))
    return {}


def _absent(s):
    (s.alpha / "corpus.yaml").unlink()
    return {}


STEP_0 = {
    "empty-selection": (lambda s: _revise_query(s, _query("verification")) or {}, PublicationRefused, ()),
    "closure-incomplete": (lambda s: _revise_query(s, _query("dataset")) or {}, PublicationRefused, ("run:r-b",)),
    "pins-disagree": (_pins_disagree, PublicationRefused, ()),
    "coordination-unpinned": (_coordination_v1, ValidationRefused, ()),
    "selection-incomplete": (_absent, PublicationRefused, ()),
    "destination-unusable": (lambda s: {"destination": Destination.local(str(s.base / "missing"))}, PublicationRefused, ()),
    "operations-root-unusable": (lambda s: {"operations_root": s.written}, PublicationRefused, ()),
    "profile-disagrees": (lambda s: {"staging_profile": BASE}, PublicationRefused, ()),
    "corpus-drifted": (_drift, SelectionRefused, ()),
}


@pytest.mark.parametrize("reason", list(STEP_0))
def test_y5_a_every_step_0_refusal_writes_nothing_durably(source, reason):
    prepare, refusal, refs = STEP_0[reason]
    changes = prepare(source)
    tip = chain_tip(source)
    with pytest.raises(refusal) as caught:
        run(source, **changes)
    if refusal is not ValidationRefused:
        assert caught.value.reason == reason
    if refs:
        assert caught.value.refs == refs
    assert chain_tip(source) == tip and not any(source.ops.rglob("*"))
```
`_revise_query` and the `_coordination_v1` rebinding mutate the `SimpleNamespace` the fixture yields; the fixture's teardown removes `base`, which holds every root they create. `coordination-unpinned` asserts the cut-39 door's `ValidationRefused` (a v1 contract does not declare `publication-binding`), which it raises before the pins are read. If the ordinary `revise_coordination` needs its content's `author` and `at` to differ from the minted revision's, pass `content_for("project", query=query, at="2026-09-02T12:00:01Z")`.

```python
def test_y5_b_a_view_revised_between_evaluation_and_lock_refuses_durably(source, monkeypatch):
    original = act._open_publication

    def revising(writer, resolver, **kwargs):
        setup_writer(source).revise_coordination("project", source.view.unpinned(), predecessors=(source.view.revision,),
                                                 content=content_for("project", query=KINDS, body="revised"))
        return original(writer, resolver, **kwargs)

    monkeypatch.setattr(act, "_open_publication", revising)
    with pytest.raises(PublicationRefused) as caught:
        run(source)
    assert caught.value.reason == "view-revised"
    assert not any(source.ops.rglob("*"))
    assert all(p.get("domain") != "science.publish-intent.v1" for p in _payloads(source))


def test_y6_a_the_selection_is_fixed_before_the_intent_and_a_drift_after_it_strands_nothing_durably(source, monkeypatch):
    original = act._open_publication

    def drifting(writer, resolver, **kwargs):
        opened = original(writer, resolver, **kwargs)
        source.alpha_writer.add(stored.dataset_node(title="late", resources=_pinned("late")))   # the world drifts
        return opened

    monkeypatch.setattr(act, "_open_publication", drifting)
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    with pytest.raises(SelectionRefused) as drifted:
        evaluate_query(open_world_view(source.world, current_epoch(source.world)), stored_query(_project(source)))
    assert drifted.value.reason == "corpus-drifted"
    outcome = resume(source, token)
    assert type(outcome) is Published
    snapshot = act.decode_snapshot((source.ops / "publish" / token / "selection.v1").read_bytes())
    held = published_records(source.dest / outcome.corpus_id)
    assert {i: t.encode() for i, t in snapshot.records} == {i: b for i, b in held.items() if not i.startswith("publication:")}
```
`SelectionRefused.reason` is how cut 28's module reads the refusal; if the attribute is named otherwise, read it as that module does (`grep -n "SelectionRefused" tests/acceptance/test_world_selection_acceptance.py | head -3`).

```python
def test_y6_b_a_rewritten_snapshot_is_request_corrupt_durably(source, monkeypatch):
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    snapshot = source.ops / "publish" / token / "selection.v1"
    snapshot.chmod(0o644)
    snapshot.write_bytes(snapshot.read_bytes().replace(b"r-a", b"r-z"))
    outcome = resume(source, token)
    assert outcome == PublishRefused(token, "request-corrupt")
    reading = attempt_reading(fresh_writer(source), token, moment_seam())
    assert reading.reading == "closed" and not list(source.dest.iterdir())


def test_y7_a_a_crash_after_k_staged_records_resumes_at_k_plus_one_durably(source, monkeypatch):
    staged = {"n": 0}
    original = CorpusWriter._stage_record

    def failing(self, text):
        staged["n"] += 1
        if staged["n"] == 2:
            raise Crash("after one record")
        return original(self, text)

    monkeypatch.setattr(CorpusWriter, "_stage_record", failing)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    counted = {"n": 0}

    def counting(self, text):
        counted["n"] += 1
        return original(self, text)

    monkeypatch.setattr(CorpusWriter, "_stage_record", counting)
    token = token_of_last_intent(source)
    outcome = resume(source, token)
    assert type(outcome) is Published and counted["n"] == 4 - 1    # four selected (d-a, d-b, r-a, r-b); one already staged


def test_y7_b_an_extra_staged_record_is_staging_corrupt_and_staging_is_retained_durably(source, monkeypatch):
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    raw_add(source.ops / "publish" / token / "staging", extra)
    assert resume(source, token) == PublishRefused(token, "staging-corrupt")
    assert (source.ops / "publish" / token / "staging").is_dir() and not list(source.dest.iterdir())


def test_y8_a_a_publication_lands_at_its_corpus_id_and_a_second_lands_beside_it_durably(source):
    first = run(source)
    assert type(first) is Published
    root = source.dest / first.corpus_id
    assert read_lifecycle_state(root) is LifecycleState.READ_ONLY_SERVICEABLE
    assert (source.dest / f"{first.corpus_id}.head-artifact.v1").is_file()
    second = run(source)
    assert type(second) is Published and second.corpus_id != first.corpus_id
    marker = next(n for n in ReadView.opened_at(source.dest / second.corpus_id).iter_stored() if n.kind == "publication")
    assert [first.corpus_id, first.marker] in marker.facets[stored.COORDINATION_FACET]["supersedes_markers"]
    assert (source.dest / first.corpus_id).is_dir()


def test_two_attempts_do_not_share_directories(source, monkeypatch):
    """Review Focus 3: a crashed attempt's staging is never touched by the next."""
    crash(monkeypatch, "_populate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    stale = token_of_last_intent(source)
    before = sorted(p.relative_to(source.ops) for p in (source.ops / "publish" / stale).rglob("*"))
    assert type(run(source)) is Published
    assert sorted(p.relative_to(source.ops) for p in (source.ops / "publish" / stale).rglob("*")) == before


def test_y8_b_a_colliding_sibling_is_export_collision_and_binds_nothing_durably(source, monkeypatch):
    crash(monkeypatch, "_write_sibling", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    (source.dest / f"{corpus_id}.head-artifact.v1").write_bytes(b"someone else's artifact")
    assert resume(source, token) == PublishRefused(token, "export-collision")
    assert not (source.dest / corpus_id).exists()


def test_a_foreign_root_at_the_export_path_binds_nothing_durably(source, monkeypatch):
    """Finding 2: a serviceable replica of another corpus occupying
    `<destination>/<corpus_id>` is refused by `replicate_root`, never taken as
    this attempt's copy; the attempt stays pending (spec §16 item 6)."""
    crash(monkeypatch, "_replicate", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    other_id, other, _ = source.corpus(nodes=(stored.run_node("o", title="o", spec="s", produces=[]),))
    config = WorldConfig(source.base / "foreign-world", "a" * 32, (other,))
    init_world_root(config, authority=SETUP)
    foreign_world = open_world(config, authority=SETUP)
    foreign_world.admit(other, provenance=Fresh())
    artifact = export_head_artifact(foreign_world, CorpusSubject(other_id))
    occupant = source.dest / corpus_id
    replicate_root(other, occupant, authority=SETUP)
    restore_root(occupant, CorpusSubject(other_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=SETUP)
    assert read_lifecycle_state(occupant) is LifecycleState.READ_ONLY_SERVICEABLE
    with pytest.raises(FOREIGN_REPLICA):
        resume(source, token)
    assert _binding_files(source) == []
    assert attempt_reading(fresh_writer(source), token, moment_seam()).reading == "unfinished"
    assert token in pending_publishes(fresh_writer(source), operations_root=source.ops, seam=moment_seam())
```
`FOREIGN_REPLICA` is the exception type Task 0's probe printed, imported at the module's top from where the probe named it. `source.corpus` builds the other corpus under setup authority.

```python
BOUNDARIES = [
    ("_initialize", True), ("_initialize", False), ("_populate", False), ("_admit_and_export", False),
    ("_write_sibling", False), ("_replicate", False), ("_restore", False), ("_bind", True),
]


@pytest.mark.parametrize("step, before", BOUNDARIES, ids=[f"{'before' if b else 'after'}{s}" for s, b in BOUNDARIES])
def test_y9_a_a_crash_at_every_local_step_resumes_to_one_binding_and_one_report_durably(source, monkeypatch, step, before):
    crash(monkeypatch, step, before=before)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    outcome = resume(source, token)
    assert type(outcome) is Published
    reports = _publish_reports(source, token)
    (report,) = reports
    assert [e["kind"] for e in report["entries"]] == [
        "publication-staging", "publication-export", "publication-reveal", "publication-binding",
    ]
    assert len(_binding_files(source)) == 1


def test_y9_a_a_lost_sibling_after_replication_is_rewritten_byte_identically_durably(source, monkeypatch):
    crash(monkeypatch, "_replicate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    sibling = source.dest / f"{corpus_id}.head-artifact.v1"
    kept = sibling.read_bytes()
    sibling.unlink()
    assert type(resume(source, token)) is Published and sibling.read_bytes() == kept


def test_y9_b_a_binding_beside_an_unfinished_intent_is_unresolved_durably(source, monkeypatch):
    crash(monkeypatch, "_bind", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    opened = attempt_reading(fresh_writer(source), token, moment_seam()).opened
    raw_add(source.written, binding_record(opened.intent, corpus_id="1" * 32, marker=marker_uid(token), artifact="3" * 64))
    tip = chain_tip(source)
    assert resume(source, token) == PublishUnresolved(token, "binding-without-report")
    assert chain_tip(source) == tip


def test_y9_c_pending_lists_crashed_attempts_only_durably(source, monkeypatch):
    done = run(source)
    crash(monkeypatch, "_populate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    crashed = token_of_last_intent(source)
    bare = _open_publication(fresh_writer(source), source.resolver, view=source.view.unpinned(), destination=source.destination,
                             clock=Clock(), seam=moment_seam())
    assert pending_publishes(fresh_writer(source), operations_root=source.ops, seam=moment_seam()) == (crashed,)
    assert resume(source, bare.intent.event_token) == PublishUnresolved(bare.intent.event_token, "no-request")
    assert done.event_token not in pending_publishes(fresh_writer(source), operations_root=source.ops, seam=moment_seam())


def test_y9_d_a_crash_inside_step_9_is_finished_by_the_resume_durably(source, monkeypatch):
    crash(monkeypatch, "_discard", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    assert (source.ops / "publish" / token / "staging").is_dir()
    outcome = resume(source, token)
    assert type(outcome) is Published
    assert not (source.ops / "publish" / token / "staging").exists()
    assert (source.ops / "publish" / token / "request.v1").is_file()


def test_y9_e_the_next_publish_reads_success_and_pre_binding_reports_durably(source, monkeypatch):
    first = run(source)
    second = run(source)
    opened = attempt_reading(fresh_writer(source), second.event_token, moment_seam()).opened
    assert (first.corpus_id, first.marker) in opened.intent.marker_tips
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    refused_token = token_of_last_intent(source)
    raw_add(source.ops / "publish" / refused_token / "staging", stored.run_node("zz", title="zz", spec="s", produces=[]))
    assert resume(source, refused_token) == PublishRefused(refused_token, "staging-corrupt")
    third = run(source)
    assert type(third) is Published
    opened = attempt_reading(fresh_writer(source), third.event_token, moment_seam()).opened
    assert all(marker != marker_uid(refused_token) for _, marker in opened.intent.marker_tips)


def test_resume_refuses_another_actor_and_another_profile_writing_nothing(source, monkeypatch):
    """Review Focus 4 (decision 9 and the staging-profile planning note)."""
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    tip = chain_tip(source)
    other = open_corpus(source.written, authority=scoped_authority(RequiredCapabilities.publishes(), "someone-else"),
                        profile=V2, coordination_resolver=source.resolver)
    with pytest.raises(ValidationRefused):
        resume_publish(other, source.resolver, event_token=token, operations_root=source.ops, staging_profile=V2, clock=Clock(), seam=moment_seam())
    with pytest.raises(ValidationRefused):
        resume_publish(fresh_writer(source), source.resolver, event_token=token, operations_root=source.ops, staging_profile=BASE,
                       clock=Clock(), seam=moment_seam())
    assert chain_tip(source) == tip and not (source.ops / "publish" / token / "staging").exists()


def _recipient(source, published_root: Path):
    """The recipient's world: a different world, under its own (setup) authority."""
    config = WorldConfig(source.base / f"recipient-{next(_counter)}", "c" * 32, (published_root,))
    init_world_root(config, authority=SETUP)
    return open_world(config, authority=SETUP)


def test_y10_a_a_second_world_admits_a_publication_and_nothing_without_a_marker_durably(source):
    outcome = run(source)
    root = source.dest / outcome.corpus_id
    world = _recipient(source, root)
    observers = ObserverSet((ArtifactCarrier.from_bytes((source.dest / f"{outcome.corpus_id}.head-artifact.v1").read_bytes()),))
    record, report = admit_publication(world, root, observers)
    assert report.outcome == "validated"
    published = epoch.build_epoch(world, coverage=frozenset({outcome.corpus_id}), bindings=hold_shipped(world))
    view = open_world_view(world, published)
    assert all(view.resolve(i) == i for i, _ in act.decode_snapshot((source.ops / "publish" / outcome.event_token / "selection.v1").read_bytes()).records)
    plain_id, plain, _ = source.corpus(nodes=(stored.run_node("p", title="p", spec="s", produces=[]),))
    other = _recipient(source, plain)
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication(other, plain, observers)
    assert caught.value.reason == "marker-absent"


def test_y10_b_a_verified_root_with_records_beyond_its_selection_is_refused_before_admission_durably(source):
    forged = source.base / "forged-staging"
    init_corpus_root(forged, authority=SETUP)
    writer = open_corpus(forged, authority=SETUP, profile=V2)
    manifest = writer.adopt_manifest(profile=pins_for(V2))
    kept, extra = (stored.run_node(name, title=name, spec="s", produces=[]) for name in ("kept", "extra"))
    writer._stage_record(node_to_markdown(kept))
    writer._stage_record(node_to_markdown(extra))
    opened = _open_publication(source.writer, source.resolver, view=source.view.unpinned(), destination=source.destination,
                               clock=Clock(), seam=moment_seam())
    writer._stage_marker(marker_record(opened.intent, world_id="e" * 32, epoch="f" * 64, selection=(kept.id,)))
    config = WorldConfig(source.base / "forged-world", "b" * 32, (forged,))
    init_world_root(config, authority=SETUP)
    staging_world = open_world(config, authority=SETUP)
    staging_world.admit(forged, provenance=Fresh())
    artifact = export_head_artifact(staging_world, CorpusSubject(manifest.corpus_id))
    copy = source.dest / "forged"
    replicate_root(forged, copy, authority=SETUP)
    observers = ObserverSet((ArtifactCarrier.from_bytes(artifact),))
    assert restore_root(copy, CorpusSubject(manifest.corpus_id), observers, authority=SETUP).outcome == "validated"
    recipient = _recipient(source, copy)
    registry_before = sorted(p.relative_to(recipient.config.world_root) for p in recipient.config.world_root.rglob("*"))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication(recipient, copy, observers)
    assert caught.value.reason == "selection-mismatch" and caught.value.refs == (extra.id,)
    assert sorted(p.relative_to(recipient.config.world_root) for p in recipient.config.world_root.rglob("*")) == registry_before
```
The registry is the recipient world root's own files, so an unchanged tree is an admission that never happened. The forged roots live under `source.base`, which the fixture removes; `metadata_root_for(forged)` and the forged world's metadata sibling sit beside them under the same directory.

`_publish_reports(s, token)` returns the stored act-report facets on the written root whose `operation == "publish"` and `event_token == token`, using `stored.act_report_facet` over `ReadView.opened_at(s.written).iter_stored()`. `_binding_files(s)` lists `s.written / "publication-binding"`.

- [ ] **Step 3: Run on the certified volume**

```bash
cd ~/d/beliefs/.worktrees/publish/python && cd "$(pwd -P)"
SCIENCE_CUT4_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut40-dev uv run --frozen pytest tests/acceptance/test_publish_act_acceptance.py -q -p no:cacheprovider
```
Expected: every test passes. The count is the fifteen units' functions plus Y5-a's nine cases (counting as nine), Y9-a's eight boundaries (eight) and its lost-sibling test, and the Review Focus tests 3 and 4. Write the exact number into the cut document's §4 if Task 0 left a placeholder. Every failure is a finding against Tasks 1–7, not a test to loosen: fix the source, or record the finding and park `--reason decision` if it needs a design change.

- [ ] **Step 4: Commit**

```bash
tasks check && git add python/tests/acceptance/test_publish_act_acceptance.py tasks
git commit -m "test(cut40): the publish-act acceptance module — Y5–Y10"
```

---

### Task 9: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut40.py`, `python/tests/acceptance/n2_arms_cut40.py` (cut 39's shim with `39` → `40`), `python/tests/acceptance/test_n2_cut40.py`, `python/tools/cut40_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit and digest; Task 8's test names.
- Produces: `CUT40_ARMS` (15), `DECLARATION_UNITS` (15), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS` and `PHASE_MODULES`.

- [ ] **Step 1: The declaration.** Write `python/tests/n2_arms_cut40.py` on cut 39's shape (`sed -n 1,60p tests/n2_arms_cut39.py`), with:
- `DECLARATION_UNITS = ("Y5-a", "Y5-b", "Y6-a", "Y6-b", "Y7-a", "Y7-b", "Y8-a", "Y8-b", "Y9-a", "Y9-b", "Y9-c", "Y9-d", "Y9-e", "Y10-a", "Y10-b")`;
- `_MODULE = "acceptance/test_publish_act_acceptance.py"`;
- `UNIT_CHECKS` mapping each unit to its Task 8 function;
- `unit_of` as the identity check.

The arms follow. Copy every `before` from the tree after Task 8 and check it with `source.count(before) == 1`; each `after` must parse.

| arm | module | before | after |
|---|---|---|---|
| Y5-a | `publish_request.py` | `            for endpoint in (relation.source, relation.target):` | `            for endpoint in (relation.target,):` |
| Y5-b | `publication_doors.py` | `        if expected_view is not None and view.unpinned().pinned(resolved.uid) != expected_view:` | `        if False:` |
| Y6-a | `publish.py` | the two statements `    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)\n    opened = _open_publication(` | `    opened = _open_publication(`, with the records line moved after the call as `records = tuple((address, node_to_markdown(open_world_view(world, current_epoch(world)).get(address))) for address in evaluate_query(open_world_view(world, current_epoch(world)), query).selected)`. Write it as a before/after over the whole `opened = …` statement so the after parses. |
| Y6-b | `publish.py` | `    if snapshot.identity() != request.selection or snapshot.event_token != intent.event_token:` | `    if False:` |
| Y7-a | `publish.py` | `    return _Population(n, complete=False)` | `    return _Population(0, complete=False)` |
| Y7-b | `publish.py` | `    if extras:` | `    if False:` |
| Y8-a | `publish.py` | `    return Path(a.request.destination.locator) / corpus_id` | `    return Path(a.request.destination.locator)` |
| Y8-b | `publish.py` | `        write_create_only(sibling, artifact)` | `        sibling.write_bytes(artifact)` |
| Y9-a | `publish.py` | `        lifecycle=entries,` | `        lifecycle=(),` |
| Y9-b | `publish.py` | `        return PublishUnresolved(event_token, "binding-without-report")` | `        pass` |
| Y9-c | `publish.py` | `        if reading is not None and reading.reading == "unfinished":` | `        if reading is not None:` |
| Y9-d | `publish.py` | `        _discard(op)` | `        pass` |
| Y9-e | `publication_doors.py` | `        if type(entries[-1]) is not PublicationBindingEntry:\n            yield intent, PreBinding(` | `        if len(entries) != 1:\n            yield intent, PositionRefused("revision-malformed", "not a publish report")\n            continue\n        if type(entries[-1]) is not PublicationBindingEntry:\n            yield intent, PreBinding(` |
| Y10-a | `publication_arrival.py` | `    if not markers:\n        raise PublicationArrivalRefused("marker-absent")` | `    if False:\n        raise PublicationArrivalRefused("marker-absent")` |
| Y10-b | `publication_arrival.py` | `    if held != selection:` | `    if not set(selection) <= set(held):` |

Each arm's `asserts` text is its spec §13 row clause, in one sentence. Before pinning, run each sabotaged text through `ast.parse` via `n2_arms.py`'s sabotage helper.

- [ ] **Step 2: The guard.** Copy `test_n2_cut39.py` to `python/tests/acceptance/test_n2_cut40.py`, then:
- import `CUT39_ARMS` and add it to `PRIOR_ARMS`;
- add `"python/tests/n2_arms_cut39.py": "<sha>"` to `FROZEN_PRIOR_CUT_FILES` (`git log -1 --format=%h -- python/tests/n2_arms_cut39.py`);
- set `FROZEN_CUT` to the cut-40 document, and `CUT40_FREEZE_COMMIT` and `CUT40_FROZEN_SHA256` from Task 0 Step 6;
- set `FROZEN_DECLARATION = "python/tests/n2_arms_cut40.py"`;
- make the inventory test assert 15 units and 15 arms;
- make the freeze test assert `"**15 arms, 15 declaration units**" in current` and `'("cut39_acceptance.py",)' in current`.

- [ ] **Step 3: The runner.** Write `python/tools/cut40_acceptance.py` as cut 39's with:
- `cut=40`;
- `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut40"`;
- `PREFIX_RUNNERS = ("cut39_acceptance.py",)`;
- `PHASE_MODULES = ("test_publish_act_acceptance.py", "test_n2_cut40.py")`;
- `declared_accounting` asserting `rows == {"Y5", "Y6", "Y7", "Y8", "Y9", "Y10"}` and `(arms, units) == (15, 15)`, with no accounting table;
- on success, `print("guarantee rows exercised: 6 (6 newly closed: Y5, Y6, Y7, Y8, Y9, Y10)", flush=True)`.

- [ ] **Step 4: The recent-cut row.** In `test_recent_cut_acceptance.py`, add `import cut40_acceptance as cut40`, add `(cut40, 40, (15, 15, 6))` with id `"cut40"`, and add

```python
    if cut == 40:
        assert "guarantee rows exercised: 6 (6 newly closed: Y5, Y6, Y7, Y8, Y9, Y10)" in output
```

- [ ] **Step 5: Guard green, then the cut, detached**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
cd ~/d/beliefs/.worktrees/publish/python && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 40); do export SCIENCE_CUT${n}_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut$n; done
test -x ~/d/beliefs/.work/acceptance/detached.sh
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut40-runner.log uv run --frozen python tools/cut40_acceptance.py > /dev/null 2>&1 &
sleep 2; echo "runner process group $(cat ~/d/beliefs/.work/acceptance/cut40-runner.log.pid)"
```
If the turn ends before the wrapper does, report that process group and the stop command, `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut40-runner.log.pid)"`.

Read the log at exit. Expected tail:
- three `[cut40 phase n/3]` lines;
- `declared arms: 15 (= 15 declaration units; 6 guarantee rows)`;
- the rows-exercised line;
- exit 0, with every arm `sound` and every check `resolved`.

A `stale` verdict means a `before` no longer matches: fix the declaration, never the source.

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/tests/n2_arms_cut40.py python/tests/acceptance/n2_arms_cut40.py python/tests/acceptance/test_n2_cut40.py python/tools/cut40_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut40): N2 declarations, guard, runner and the recent-cut row — Y5–Y10"
```

---

### Task 10: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §19)

- [ ] **Step 1: Run.**
  1. `export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30`, then `test -f "$SCIENCE_MM30_ROOT/state.json"` and copy that file to the scratchpad.
  2. From `python/`, run `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight`, which must say `ok`. On a host-load refusal, park with `tasks park <Task 10's id> "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`.
  3. Run `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`.
  4. `grep -n 'publish\|publication\|durable' python/tools/reproduction/*.py` shows what the driver reaches. Expected: nothing of this slice.

- [ ] **Step 2: Append §19** on §18's shape:
- §19.1, what changed: the publish act, its records and the arrival door, none of them reached by the driver.
- §19.2, what the re-run reached: the same `NoBelief` payload, `rederived_equal: true`, and `state.json` byte-identical (the diff and both SHA-256s).
- §19.3, what it does not claim: mm30 publishes nothing.

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under the publish act; nothing moves"
```

---

### Task 11: The results record, the re-rank, and the amendments

**Files:**
- Create: `docs/plans/<date>-conformance-cut-40-results.md`
- Modify: the cut document (`**Status:**`), the spec (`**Status:**`), the ledger, the roadmap, `python/tools/roadmap_status.py`, the layer design, the act-report design, `docs/designs/2026-09-22-publication-design.md` (status line), `docs/guide/contracts-and-adoption.md`, `docs/guide/open-questions.md` if it names the publish act, `README.md`, tasks

- [ ] **Step 1: The results record**, on cut 39's shape (`docs/plans/2026-09-23-conformance-cut-39-results.md`):
- **§1, what ran:** the runner's summary lines verbatim, and the per-unit table.
- **§2, accounting:** 15 arms, 15 units, 6 rows; Y5–Y10 closed; **199 of 226**.
- **§3, evidence:**
  - the spec's planning notes (§18), and deviations from the plan;
  - the five engine verdicts;
  - the inventories checked in both directions (three new entry points, each with its `Case`);
  - the stale-arm probe clean, with cut 39's pinned lines untouched.
- **§4, the reproduction:** §19.
- **§5, `## Remaining boundary`:** cut 41 (`beliefs-3ce305`: transport, remote reveal and orphans, Ruling 12, the remote rows, `divergent-publication`); L1 under `persistence-cut`; and the recovery-table row this cut does not exercise, a bare reservation mid-replication, which is engine-internal and belongs to `persistence-cut`.
- **§6, main integration:** filled at merge.
- **§7, execution rulings.**

- [ ] **Step 2: `roadmap_status.py`.** Add `40: ("conformance-cut-40-results §2", "Y5, Y6, Y7, Y8, Y9, Y10", ""),` after the cut-39 entry, then regenerate Appendix A. Expected: `Closed 199 of 226; open 27.`

- [ ] **Step 3: Ledger and roadmap.**
  - **Ledger `Current state`:** a built bullet for the publish act (local) and marker-required arrival; Y5–Y10 closed; `publish` stays open with cut 41's remainder; the totals.
  - **Roadmap, rewritten whole:**
    - `**Ranked at:** cut 40`;
    - a `**Cut 40 (<date>) discharges the publish act, local**` paragraph, marking it the ninth off-path lane, which re-ranks nothing on the path;
    - the boundary index's `publish` row: "cut 41: remote transport, orphans, `divergent-publication`";
    - the accounting paragraph and one reproduction sentence;
    - Appendix A pasted and Appendix B updated.

- [ ] **Step 4: Amendments** (spec §15):
  - **Layer design §6.1**, dated `> **Amended <date> (publish act, local, conformance cut 40 — `2026-09-23-publish-act-local-design.md`):**` notes at the sentences they qualify:
    - step 0's snapshot and the pin re-check;
    - step 4's container destination;
    - the recovery table's `request-corrupt`, restated for the snapshot.
  - **Act-report design §2 and §6 item 3:** the four entry kinds and the ordered sequence.
  - **`2026-09-22-publication-design.md` status:** "Y5–Y10 closed at cut 40".

- [ ] **Step 5: Status lines, guide, README, tasks.**
  - The cut document's Status: `discharged <date> on the certified volume; results: …`.
  - The spec's Status: `discharged at conformance cut 40 on <date>; results: …`.
  - README: "through **cut 40**", its row's wording, and "The latest discharged boundary is cut 40".
  - The guide's cut-40 line as discharged.

```bash
tasks done <Task 11's id> "results record, re-rank at cut 40, amendments"
tasks check && git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut40): results record, re-rank at cut 40, Y5–Y10 closed"
```

---

### Task 12: Final review, gate, merge

- [ ] **Step 1: Whole-branch review.** Run `superpowers:requesting-code-review` over `git diff main...HEAD`, against the Global Constraints' decisions and the cut document's §5. Land fixes as their own commits and record each in the results record §3.

- [ ] **Step 2: The gate, detached**

```bash
cd ~/d/beliefs/.worktrees/publish && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 40); do export SCIENCE_CUT${n}_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut$n; done
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut40-gate.log just gate > /dev/null 2>&1 &
sleep 2; echo "gate process group $(cat ~/d/beliefs/.work/acceptance/cut40-gate.log.pid)"
```
Read the log at exit. Expected: the pytest summary line with zero failures (memory `pytest-count-claims-need-the-summary-line`) and the TypeScript suite green.

- [ ] **Step 3: Close and merge**

```bash
tasks done <Task 12's id> "final review, gate green, merged"
tasks done beliefs-328507 "cut 40 discharged: Y5–Y10 — the local publish act, its resumption and marker-required arrival"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-328507 — cut 40 discharged"
cd ~/d/beliefs && git merge --no-ff design/publish -m "merge: the publish act, local — conformance cut 40"
```
`beliefs-1a5157` stays open, since cut 41 (`beliefs-3ce305`) is its remainder. Fill the results record's §6 in a `docs(cut40): record merged-main verification` commit. The worktree stays for cut 41.

---

## Self-review

**Spec coverage.**

| Spec section | Where it is built |
|---|---|
| §1 | the file map; Task 0's cut document |
| §2 decision 1 | Task 6's remote refusal and Task 12's open lane |
| §2 decision 2 | Tasks 4 and 6, and Y6 |
| §2 decision 3 | Task 6's `publish` and Task 5's `expected_view` |
| §2 decision 4 | Task 6's `_export_root`, and Y8-a |
| §2 decision 5 | Task 5 |
| §2 decision 6 | Task 3, and `AUTHORITY` in Task 8 |
| §2 decision 7 | Task 2, and Y9-a |
| §2 decision 8 | Task 6's `_run`, and Task 0's probes |
| §2 decision 9 | Task 6's `resume_publish`, and Review Focus 4 |
| §2 decision 10 | Task 7 |
| §3 | Task 6 |
| §4.1 | Tasks 4 and 6 |
| §4.2 | Task 5 |
| §4.3 and §4.5 | Task 4 |
| §4.4 | Task 1 |
| §5 | Tasks 5 and 6 |
| §6 | Task 6 |
| §7 | Tasks 2 and 5 |
| §8 | Task 6 (`_discard`, `_published_from_disk`) |
| §9 | Task 6, with Y9's arms |
| §10 | Task 7 |
| §11 | the staleness runs in Tasks 2, 3, 5 and 6 |
| §12 | the file map |
| §13 | Tasks 0 (bank) and 11 (close) |
| §14.1 | Tasks 1–7 |
| §14.2 | Task 8 |
| §14.3 and §14.4 | Task 9 |
| §15 | Task 11 |
| §16 | the cut document §7 and the results record §5 |
| §17 | Task 0 Step 5 (children) |

**Placeholders.** Three places defer an exact spelling to the tree by instruction, each with the grep or file that settles it:
- the `Case` helpers in Task 5, on `_bind_publication`'s pattern;
- Task 5's lift of the doors-test scaffolding into `_pair`;
- the path helper in Task 8's `published_records`.

At self-review, three first-draft stubs were written out in full: Y5-a's nine cases, Y10-b's forged root, and Task 6's `_refused` and `_restore`, with `outcome_type` moved to Task 2.

**Type consistency.**
- **Records and codecs:** `Snapshot(event_token, records)`, `PublishRequest(event_token, view, destination, epoch, world_id, pins, selection, staging_world_id)`, `_Population(present, complete)`.
- **Report values:** the seven outcomes and four entries as Task 2 defines them; `StagingCorrupt(corpus_id, reason, refs)`, the same order in Tasks 2, 6 and 8; `PreBinding(outcome)`.
- **Doors:** `AttemptReading(opened, reading, outcome)`; `attempt_reading(writer, event_token, seam)`; `_refuse_publication(writer, opened, entries, *, clock, port=None)`; `_open_publication(…, expected_view=None)`; `_bind_publication(…, lifecycle=())`.
- **The act:** `publish(writer, resolver, world, *, view, destination, operations_root, staging_profile, clock, seam, port=None)`; `resume_publish(writer, resolver, *, event_token, operations_root, staging_profile, clock, seam, port=None)`; `pending_publishes(writer, *, operations_root, seam)`; `Published(event_token, corpus_id, marker, binding, artifact)`; `PublishRefused(event_token, outcome)`; `PublishUnresolved(event_token, reason)`.
- **Arrival:** `admit_publication(world, root, observers)`.
- **Errors:** `PublicationArrivalRefused(reason, *, refs=())`, `PublicationRefused(reason, *, tips=(), refs=(), corpus_ids=(), field="")`, `CreateOnlyCollision(path)`.
- **The spec's names the plan renames**, each in the planning note: `Unresolved` → `PublishUnresolved`; `PublishRefused(event_token, report)` → `PublishRefused(event_token, outcome)`; `StagingCorrupt`'s nullable `corpus_id` and `record` → `corpus_id` and `refs`.

**Review Focus.** All five lines have a test in their owning task: Task 4 (1 and 2), Task 8 (3 and 4) and Task 1 (5).

## Plan review log

- 2026-09-23 — drafted. Found at planning and recorded in the spec's planning note (Task 0 Step 5):
  - the caller-supplied staging profile, since there is no pins-to-profile compiler;
  - `_stage_record`'s record-local refusals;
  - `refs` in place of the nullable record, since `v1` refuses null;
  - `PublishRefused` carries the outcome type;
  - `attempt_reading` gives the resume path its completion reading;
  - the artifact identity is the SHA-256 of the canonical bytes;
  - both doors' keywords default to cut 39's behaviour;
  - crash injection by monkeypatching the named step functions;
  - six arms reshaped so each check sees its sabotage (Y5-a, Y6-a, Y9-c, Y9-d, Y10-a, Y10-b).

  Task 0 pins five engine facts before anything relies on them: the initializers, admission, export and replication retries converge, and a restored copy reads.

- 2026-09-24 — user review of the plan, six findings, each verified against the code (the user had probed the staging, permit, destination and retry findings); all taken, and the spec amended to match (its §18):
  1. **`ArrivalRefused` already exists** (`errors.py:379`, raised by `world/verify.py` with `(cause, report, detail)`). The publication door's refusal is `PublicationArrivalRefused`, everywhere in the plan and the spec; verified arrival's refusal passes through unchanged.
  2. **Serviceability was taken as identity.** `_replicate` now reinvokes `replicate_root` on every retry, and `_restore` runs only after it. Task 0 gains two probes: `REPLICATE_AFTER_RESTORE` (a retry after the grant converges) and `FOREIGN_REPLICA` (another corpus's replica at the path refuses, and its exception type is recorded). Task 8 gains `test_a_foreign_root_at_the_export_path_binds_nothing_durably`. The spec records the foreign occupant as a limitation: the attempt stays pending.
  3. **The staging doors skipped the profile.** Both now run `_refuse_invalid` and `_refuse_facet_shapes`, and `_stage_record` also runs the display-facet and governed-stamp checks, the ordinary writer's record-local guards. Two tests pin the probed cases: an unactivated domain facet (`facet-unexpected`) and a marker under `BASE` (`kind-unknown`). The view-reading refusals stay omitted.
  4. **The resolved destination was discarded.** `publish` freezes `Destination.local(str(resolved))` before the intent, and `test_destination_checks` asserts that a symlinked destination answers its target.
  5. **A retry answered `present` without the directory `fsync`.** It now syncs the directory first, with a fault test for a death between the link and the sync.
  6. **The fixture used the publish-only permit for setup.** Corpora, worlds, epochs, the view's revisions, the forged root and the recipient worlds run under `SETUP = FULL`. The publishing writer and the world handed to `publish` bind exactly `publishes()` (`open_world` requires no family).
