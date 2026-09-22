# Publication Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the coordination contract's versioned amendment declaring `publication` and `publication-binding`, their deterministic records, the `publish` operation kind and act family, the evidence-bearing publish intent, and the intent-position judgment over a chain-derived inventory, with the step-0 intent door and the step-8 binding door, and discharge W17 and Y1–Y4 as conformance cut 39.

**Architecture:** The contract ships as `contracts/coordination/v1` (the former test fixture, byte-for-byte in content) and `v2` (its successor). `beliefs/intents/publish.py` holds the destination union, the anchor and the sealed `PublishIntent` with its one codec. `beliefs/publication.py` holds the two addresses, the content rules and the deterministic factories. `beliefs/coordination.py` gains `standing_at`, a pure judgment over a `MomentSeam` that `root.py` builds from the engine: it replays each mounted root's committed registrations up to a bound, reads and matches every inventoried revision, and classifies unaccounted files by a chain re-read. `beliefs/publication_doors.py` holds `_open_publication` (step 0) and `_bind_publication` (step 8, through `execute_fulfilling_guarded`) and the orphan fold. Neither door has a public route.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, `nodes` records, the acceptance harness under `python/tests/acceptance/` and the N2 audit (`n2_arms.py`, `test_n2.py`).

**Spec:** `docs/superpowers/specs/2026-09-22-publication-records-design.md`, approved 2026-09-22 at `cb19908` after two user reviews (its §16 review log). Read it first; every task cites its sections and decisions.

## Global Constraints

- **Baseline is `main` at `2b875a7`** (`git merge-base main design/publish`). Work in the worktree `.worktrees/publish` (branch `design/publish`, locked "on WORK_ROOT storage"). Every path below is relative to the repository root, and paths shown to the user carry the `.worktrees/publish/` prefix. The main checkout is `~/d/beliefs`. Exports for a worktree on `WORK_ROOT`: `SCIENCE_MM30_ROOT` and every `SCIENCE_CUT*_ROOT` name the **main checkout's** `.work/…` (memory `worktree-on-work-root-needs-cut-root-exports`; about 190 `CapabilityUnavailable` failures mean a missing export, not a regression). For the fast loop: `export SCIENCE_CUT4_ROOT=~/d/beliefs/.cut4-acceptance SCIENCE_CUT10_ROOT=~/d/beliefs/.lifecycle-wrappers-test`. Run pytest from the canonical worktree path (`cd "$(pwd -P)"`) — an `ELOOP` from `open_root` is the `.worktrees` symlink in the cwd (memory `run-pytest-from-the-canonical-worktree-path`).
- **The worktree's sibling dependencies resolve under `.worktrees/`.** `python/pyproject.toml` pins `verifiably-atoms` and `verifiably-nodes` as editable paths `../../atoms/python` and `../../nodes/python`; `cd python && uv run --frozen python -c "import atoms, nodes, beliefs"` prints nothing on success. `just setup` has run.
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions. — For this lane (spec §6, §11.4): the `FileState` comparison and the `ABSENT` singleton reach `coordination.py` only as `MomentSeam` members built in `root.py` (`moment_seam()`); `coordination.py`, `publication.py`, `publication_doors.py` and `intents/publish.py` import nothing of `atoms`. `_bind_publication` calls `execute_fulfilling_guarded`, an inventoried primitive (`test_permit_boundary.py` `PRIMITIVE_ATTRIBUTES`), so it joins `WRITE_ENTRY_POINTS` as `"publication_doors.py:_bind_publication": "publish"` and gains a `Case` (Task 6). `_open_publication` writes only through `CorpusWriter._append_operation_intent`, already inventoried; its new `payload=` keyword adds no caller. Tasks 1, 5 and 6 each run `test_permit_boundary.py`, `test_permit_entry_points.py` and `test_capability_boundary.py` green; the results record states the inventories were checked in both directions.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. — Here that is Task 8, Step 4, with `(cut39, 39, (13, 13, 5))` — or `(cut39, 39, (12, 12, 5))` if Task 0 Step 3 finds no durable rollback and W17-p-f is declared unrun (the row count stays 5; W17 is then read partial).
- **Frozen declarations and frozen cut bodies stay byte-exact.** Cut 39 chains **cut 38's** runner (`PREFIX_RUNNERS = ("cut38_acceptance.py",)`) and re-targets nothing unless Task 1's staleness run says otherwise: `coordination.py`, `corpus.py`, `permit.py`, `report.py`, `stored.py` and `intents/shapes.py` are pinned by earlier live arms (cuts 14, 19, 35, 38), so every edit in those files must leave each pinned `before` string occurring exactly once. Tasks 1, 2, 3 and 5 end by running `tests/test_arm_staleness.py`; a stale prior arm means an edit moved a pinned line — restore the line's spelling and place the new code beside it, never edit a prior declaration (memory `staleness-probe-baseline-is-the-trees-output`).
- **Decisions the code must honour verbatim** (spec §2): two slices, this one owning every record and every source-root write (1); the contract ships as `v1` (the fixture, same content identity) and `v2` (`lineage: {successor: <v1 identity>}`, adding the two kinds and `composite`/`composes`), `shipped_coordination()` returning v2 (2); the publish intent is the domain-tagged `science.publish-intent.v1` carrying the pinned view, the destination, `binding_tips`, `marker_tips`, and one anchor per mount other than the written root, captured under the written root's lock (3); presence at a position is the chain's inventory at each root's bound — committed registrations only, every inventoried file present, content-matched and well-formed, removals and rewrites `history-violated`, unaccounted files classified by a chain re-read (4, §6); the marker's `published_from`, `destination`, `selection` and `supersedes_markers` and the binding's bound `(corpus_id, marker, artifact)` are facet fields, a marker carries no relations, a binding exactly its `supersedes` to `binding_tips` (5); deterministic identity by the factory only, `mint_coordination` and `revise_coordination` refusing both kinds with `KindNotMintedHere` (6); a `publish` act family, `KIND_ACTS` mapping both kinds to `{"publish"}`, `RequiredCapabilities.coordination()` keeping the eight ordinary kinds, `publishes()` returning `publish` over `publication-binding` plus `corpus-write` over `act-report`, admitted through a closed `KERNEL_REQUIREMENTS` while every ordinary route naming `publish` still refuses (7); the act-report amendment banks one entry kind, `publication-binding`, with `bound`, `predecessor-not-standing` and `evidence-refused` (8); the destination is the closed `local`/`remote` union, canonical (9); `publish` opens only through its domain intent — `OperationIntent("publish", …)` raises and a domainless `publish` triple decodes `malformed` (10); `predecessor-not-standing` is the detection of a broken single-writer obligation, reached in the arm by an injected second writer (11).
- **Detached runs go through a reaping wrapper** (Processes rule): the cut runner and the gate outlive a turn, so each is launched by `~/d/beliefs/.work/acceptance/detached.sh` (exists; `test -x` it, and if missing recreate it from `docs/superpowers/plans/2026-09-21-l13-preimage.md`'s Global Constraints). Launch: `setsid nohup ~/d/beliefs/.work/acceptance/detached.sh <log> <cmd…> > /dev/null 2>&1 &`. The end-of-turn report that leaves it running names the process-group id (`cat <log>.pid`) and the stop command (`kill -TERM -- "-$(cat <log>.pid)"`), after `host-load --section session` has listed what the session's scope left. After exit, check the process group is gone before reporting nothing left.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row or invariant it serves. Run every `pytest` from `python/` with `uv run --frozen`. No TypeScript changes; both `CONTRACT.yaml` copies of the base contract unchanged.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-09-22-publication-design.md` (new) | the Y table's owner: Y1–Y4 banked (Task 0); the second slice appends |
| `docs/designs/<freeze date>-conformance-cut-39.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py`, the ledger | the freeze, the Y table registration, the row total (Task 0) |
| `python/tests/test_publication_engine_order.py` (new) | the write-ahead pin and the rollback probe (Task 0) |
| `python/src/beliefs/contracts/coordination/v1/CONTRACT.yaml`, `…/v2/CONTRACT.yaml` (new) | the shipped coordination contract (Task 1) |
| `python/src/beliefs/profile.py` | `shipped_coordination` (Task 1) |
| `python/src/beliefs/coordination.py` | `PUBLICATION_KINDS`, `ORDINARY_COORDINATION_KINDS`, `COORDINATION_KINDS` (Task 1); `Anchor`, `MomentSeam`, `PositionRefused`, `ChainBound`, `bounds`, `inventory`, `present_revisions`, `standing_at` (Task 5) |
| `python/src/beliefs/permit.py` | the `publish` family, `KIND_ACTS`, `KERNEL_REQUIREMENTS`, `publishes()`, `coordination()` (Task 1) |
| `python/src/beliefs/corpus.py` | `KindNotMintedHere` in both family doors (Task 1); `CoordinationResolver.mounted()` (Task 5); `_append_operation_intent(payload=)` (Task 6) |
| `python/src/beliefs/errors.py` | `KindNotMintedHere` (Task 1); `PublicationRefused` (Task 6) |
| `python/tests/coordination_fixtures.py` | loads v1 from the package (Task 1) |
| `python/tests/test_coordination_contract.py`, `test_permit.py`, `test_coordination_write.py` | Task 1's tests |
| `python/src/beliefs/report.py`, `python/src/beliefs/stored.py`, `python/src/beliefs/boundary.py`, `python/src/beliefs/intents/shapes.py` | the `publish` kind, the entry and three outcomes, the stored mirror, decision 10, `_mint_publish_report` (Task 2); the publish shape, dispatch, `mismatch` and `completion` (Task 3) |
| `python/tests/test_act_report.py`, `test_intent_shapes.py` | Tasks 2–3 tests (`ls tests | grep -i 'report\|shape'` names the existing modules; add to them) |
| `python/src/beliefs/intents/publish.py` (new) | `Destination`, `PublishIntent`, `encode_publish_intent`, `decode_publish_intent` (Task 3) |
| `python/src/beliefs/intents/reduce.py` | the `publish` shape literal (Task 3) |
| `python/src/beliefs/publication.py` (new), `python/tests/test_publication.py` (new) | addresses, identities, content rules, factories, `marker_consistent` (Task 4) |
| `python/src/beliefs/root.py`, `python/tests/test_standing_at.py` (new) | `moment_seam()` and `standing_at` over a fake and a real seam (Task 5) |
| `python/src/beliefs/publication_doors.py` (new), `python/tests/test_publication_doors.py` (new), `test_permit_boundary.py`, `test_permit_entry_points.py` | the two doors and the orphan fold (Task 6) |
| `python/tests/acceptance/test_publication_records_acceptance.py` (new) | the declaration units (Task 7) |
| `python/tests/n2_arms_cut39.py` (new), `python/tests/acceptance/n2_arms_cut39.py` (new shim), `python/tests/acceptance/test_n2_cut39.py` (new), `python/tools/cut39_acceptance.py` (new), `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, the recent-cut row (Task 8) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | §18 (Task 9) |
| `docs/plans/<date>-conformance-cut-39-results.md` (new), the ledger, the roadmap, `python/tools/roadmap_status.py`, the coordination, layer and act-report designs, `docs/guide/foundations.md`, `docs/guide/open-questions.md`, `README.md`, tasks | discharge and amendments (Task 10) |

---

### Task 0: Freeze cut 39, bank the Y table, pin the engine order

**Files:**
- Create: `docs/designs/2026-09-22-publication-design.md`, `docs/designs/<freeze date>-conformance-cut-39.md`, `python/tests/test_publication_engine_order.py`
- Modify: `python/tests/test_designs_corpus.py` (`GUARANTEE_TABLES`, `TABLE_OWNERS`, the number-word table), `README.md` (the designs count and table row, the row total and table count), `docs/guide/contracts-and-adoption.md`, the ledger (`Current state`: Y1–Y4 open under `publish`), the roadmap's accounting paragraph and Appendix A (via `python/tools/roadmap_status.py`), the spec (planning note), tasks through the CLI

**Interfaces:**
- Produces: the frozen §§2–7 the guard pins (Task 8 reads its freeze commit and body digest); the unit inventory every later task builds against; `ROLLBACK_MEANS` — the verdict of Step 3 that Task 7's W17-p-f uses or declares unrun.

- [ ] **Step 1: Confirm cut 39 is unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -q "conformance-cut-39\|conformance-cut-4[0-9]" && echo "claimed on $b"; done; echo scan done
git worktree list
```
Expected: `scan done` alone; the only worktrees are `main` and `.worktrees/publish` (memory `cut-number-check-scans-every-worktree`).

- [ ] **Step 2: Pin the write-ahead order** — `python/tests/test_publication_engine_order.py`. The spec's re-read classification (§6, "A file the chain does not account for") relies on the engine appending a registration before any effect; `atoms` `coordinator/execute.py` `_run_under_lease` does (`append_entry` at line 171, the effect loop from line 183). This test pins it from beliefs' side, on the certified volume, by observing the chain at the moment the create effect runs:

```python
"""The engine order the publication judgment relies on (publication-records
design §6): a registration is in the chain before its create effect runs, and
an effect failure after registration rolls back durably. Tests may import
`atoms`; only `root.py` does among the source modules."""

from __future__ import annotations

import os
import shutil
from itertools import count
from pathlib import Path

import pytest
from authority import FULL
from atoms.coordinator import execute as engine_execute  # the effect table the test patches, as atoms' own tests do
from nodes.core.write_plan import CreateOp

from beliefs.root import init_corpus_root, log_seam, metadata_root_for, open_corpus
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView
from profiles import BASE, pins_for

_counter = count()


@pytest.fixture()
def durable_root(work_directory):
    root = work_directory / f"engine-order-{os.getpid()}-{next(_counter)}"
    try:
        init_corpus_root(root, authority=FULL)
        open_corpus(root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _registrations(root: Path) -> list[RegisteredEntryView]:
    view = log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return [entry for entry in view.entries if type(entry) is RegisteredEntryView]


def test_a_registration_is_in_the_chain_before_its_create_effect_runs(durable_root, monkeypatch):
    seen: list[bool] = []
    apply = engine_execute.create_file.apply

    def observing(*args, **kwargs):
        # Read the chain file directly: the lease holds the project lock, so the
        # observation is of the durable entries already appended, not of a new inspection.
        seen.append(any(path == "probe/a.md" for entry in _registrations_unlocked(durable_root) for path, _ in entry.final))
        return apply(*args, **kwargs)

    monkeypatch.setattr(engine_execute.create_file, "apply", observing)
    port = open_corpus(durable_root, authority=FULL, profile=BASE)._operation_port
    port.execute([CreateOp(path="probe/a.md", content=b"probe\n")])
    assert seen == [True]


def test_an_effect_failure_after_registration_rolls_back_durably(durable_root, monkeypatch):
    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(engine_execute.create_file, "apply", failing)
    port = open_corpus(durable_root, authority=FULL, profile=BASE)._operation_port
    with pytest.raises(Exception):
        port.execute([CreateOp(path="probe/b.md", content=b"probe\n")])
    monkeypatch.undo()
    view = log_seam().inspect_registered(durable_root)
    assert type(view) is WellFormedView
    (registration,) = [e for e in view.entries if type(e) is RegisteredEntryView and any(p == "probe/b.md" for p, _ in e.final)]
    (settlement,) = [e for e in view.entries if type(e) is SettledEntryView and e.registration == registration.digest]
    assert settlement.committed is False
    assert not (durable_root / "probe/b.md").exists()
```

`_registrations_unlocked` reads the chain without taking the project lock the lease already holds. Write it from `root.py`'s detached inspector — `log_seam().inspect_detached(root)` is a read-only scan with no lock (`world/verify.py` `LogSeam` docstring) — and filter `RegisteredEntryView` exactly as `_registrations` does. If `inspect_detached` refuses a registered live root, read the entries from the chain directory with `atoms.chain.read` in the test (tests may import the engine) and say so in a one-line comment.

```bash
cd python && uv run --frozen pytest tests/test_publication_engine_order.py -q
```
Expected: 2 passed. If the first fails with `seen == [False]`, the engine does not append before its effects and the spec's re-read classification is unsound: stop, `tasks note` the finding, and park the task `--reason decision`; nothing later is built on an unpinned order.

- [ ] **Step 3: Settle `ROLLBACK_MEANS`.** The second test above is the durable means W17-p-f needs (spec §11.2): monkeypatching `atoms.coordinator.execute.create_file.apply` to raise after registration leaves a `RegisteredEntryView` and a `SettledEntryView(committed=False)` in the chain and no file — `atoms`' own caught-rollback technique (`tests/test_coordinator_run.py:173`). If it passes, `ROLLBACK_MEANS = "patched create effect"`, and W17-p-f is declared. If it fails on the certified volume, W17-p-f is declared **unrun**, the accounting in Global Constraints and Task 8 takes its `(12, 12, 5)` form, and the results record reads W17 **partial** (memory `cut-classification-any-unrun-arm-is-partial`). Add one probe to the same module, which Task 6's retry and Task 7's W17-p-f depend on — whether a second fulfilling registration for the same intent is admitted after a rolled-back one:

```python
def test_a_rolled_back_fulfilment_leaves_the_intent_open_for_a_retry(durable_root, monkeypatch):
    writer = open_corpus(durable_root, authority=FULL, profile=BASE)
    port = writer._operation_port
    digest = writer._append_operation_intent("audit", "f" * 32, FULL.actor)

    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(engine_execute.create_file, "apply", failing)
    with pytest.raises(Exception):
        port.execute_fulfilling([CreateOp(path="probe/c.md", content=b"one\n")], digest)
    monkeypatch.undo()
    port.execute_fulfilling([CreateOp(path="probe/c.md", content=b"one\n")], digest)
    assert (durable_root / "probe/c.md").read_bytes() == b"one\n"
```

If this third test fails with the engine refusing the second fulfilment, record `RETRY_AFTER_ROLLBACK = "fresh intent"`: Task 7's W17-p-f then commits its retry as a fresh publish rather than a second `_bind_publication` under the same intent, and its "present once" assertion is about that publish's binding. Otherwise `RETRY_AFTER_ROLLBACK = "same intent"`. Write both verdicts into the cut document's §5 (Step 5) and into a `tasks note`.

- [ ] **Step 4: Bank the Y table** — `docs/designs/2026-09-22-publication-design.md`:

```markdown
# Publication — the guarantee table

**Status:** banked 2026-09-22 with conformance cut 39's freeze; the Y table's
owner (`python/tests/test_designs_corpus.py` `TABLE_OWNERS`). Y1–Y4 are the
publication-records slice's (`../superpowers/specs/2026-09-22-publication-records-design.md`
§10); the publish act's slice appends its own rows here.

The act is specified by the user and autonomy layer design §6.1
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`); the
records, the intent and the intent-position judgment by the slice spec above.
W17's intent-position arm stays in the world-addressing table and is read by
the same cut.

| row | guarantee |
|---|---|
```
followed by the four Y rows copied byte-for-byte from the spec's §10 table (`grep -n '^| \*\*Y[1-4]\*\*' docs/superpowers/specs/2026-09-22-publication-records-design.md`).

`python/tests/test_designs_corpus.py`: add `"Y": ("Y1", "Y2", "Y3", "Y4"),` to `GUARANTEE_TABLES` after `"U"`, and `"Y": "2026-09-22-publication-design.md",` to `TABLE_OWNERS`. The corpus total moves from 216 to 220 rows and from 20 to 21 tables: update `README.md`'s total and table count (the test `test_the_readme_states_the_corpus_row_total` names the phrases), the ledger's `Current state` (Y1–Y4 open under `publish`, beside W17's remainder), and the roadmap's accounting paragraph ("188 of 220 rows closed, with 32 open") and Appendix A, regenerated: `cd python && uv run --frozen python tools/roadmap_status.py` — expected `Closed 188 of 220; open 32.`

- [ ] **Step 5: Write the cut document** on cut 38's shape (`sed -n 1,140p docs/designs/2026-09-22-conformance-cut-38.md` first). Header:

```markdown
# Conformance cut 39 — publication records

**Status:** frozen <date>, before implementation; W17 and Y1–Y4 are open
**Design:** `../superpowers/specs/2026-09-22-publication-records-design.md`, approved 2026-09-22 at `cb19908` after two user reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-22-publication-records.md`.
**Numbered after** cut 38 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 39 or above at freeze; cut 38 is the highest discharged runner.
```

§1 what the cut is (spec §1, condensed: the coordination contract ships as v1 and v2; the two kinds, their deterministic records and content rules; the `publish` kind, family and evidence-bearing intent; the intent-position judgment over the chain's inventory; the two internal doors; W17 closes and Y1–Y4 open and close; off the path). §2 the boundary: every file in this plan's file map from Task 1 to Task 8, and "Frozen declarations and cut bodies through cut 38 remain byte-exact." §3 selection: the W17 row from the world-addressing design (`grep -n '^| \*\*W17\*\*' docs/designs/2026-08-02-world-addressing-design.md`, whole line), the four Y rows from Step 4's table, then the unit table copied from spec §11.2 (thirteen rows, W17-p-a through Y4-c, the assertion column verbatim). §3.2 rows not read: "W17's ordinary-family arms were closed by cut 14 and are not re-read; the frozen cut-14 text's 'pure function of a constructed chain prefix' is superseded by citation (coordination design §11.6 and this cut's W17-p units), not edited." §4 accounting: "**13 declaration units** (or 12 with W17-p-f unrun, Task 0 Step 3) over five rows; W17 closes (partial if W17-p-f is unrun) and Y1–Y4 close. 188 of 220 → 193 of 220." §5 N2 and acceptance obligations: the sabotage table from spec §11.3 with a `module` column (Task 8 Step 1 fills the module per arm), `ROLLBACK_MEANS` and `RETRY_AFTER_ROLLBACK` from Step 3, "`PREFIX_RUNNERS = ("cut38_acceptance.py",)`" and "`PHASE_MODULES = ("test_publication_records_acceptance.py", "test_n2_cut39.py")`". §6 second reader: check that W17-p-a's second writer commits its supersession between the step-0 tip read and `append_intent` (a port wrapper, not a thread) and that the refusal comes from the guard's recomputation; that W17-p-c's anchor is the one the intent carries, read back from the chain; that W17-p-e's refusals are raised by the inventory, not by the resolver's live read; that Y2-a's clock advances on every read; that Y4-a counts `execute_fulfilling_guarded` calls on a wrapper over the durable port. §7 limitations: spec §14 items 1–6.

- [ ] **Step 6: README, guide, the number word, the planning note in the spec**

`README.md`: the designs count word +2 (the cut document and the Y table's owner), and two table rows after cut 38's:

```markdown
| `2026-09-22-publication-design.md` | the publication guarantee table (Y): Y1–Y4 from the publication-records slice; the publish act appends its own |
| `<freeze date>-conformance-cut-39.md` | the frozen publication-records cut: the coordination contract's v2 amendment, the publish intent and the intent-position judgment; W17 and Y1–Y4 read, 13 declaration units, the cut 38 runner as prefix |
```

`docs/guide/contracts-and-adoption.md`: after the cut-38 discharge paragraph, add

```markdown
Cut 39 is frozen and not yet discharged: publication records — the
coordination contract's v2 amendment declaring `publication` and
`publication-binding`, the evidence-bearing publish intent, and the
intent-position judgment over the chain's inventory
(`../designs/<freeze date>-conformance-cut-39.md`).
```
and add the cut-39 path to the cut list. `python/tests/test_designs_corpus.py`: add the number word(s) the new designs count needs beside the last entry.

In the spec, under §16's review log, add: "- 2026-09-22 — at planning, two gaps resolved: `completion` admits `PublishIntent` (its type check refused anything but `OperationIntent` and `AssessmentRunIntent`, so §5's 'completion itself is unchanged' and §8's inclusion of `completion` were wrong), and the Y table's owner is `../../designs/2026-09-22-publication-design.md`, since `TABLE_OWNERS` resolves under `docs/designs/`. The doors live in `beliefs/publication_doors.py`; `standing_at` takes the address's kind explicitly." and change §5's sentence "`completion` itself is unchanged." to "`completion` admits a `PublishIntent` beside the two intents it reads today (planning note, §16)." and delete "and `completion`" from §8's first sentence.

The plan's step children exist (filed with the plan: `beliefs-ff3c13` Task 0, `beliefs-7085c4` Task 1, `beliefs-ba621b` Task 2, `beliefs-3ae33c` Task 3, `beliefs-cce5e6` Task 4, `beliefs-ec5974` Task 5, `beliefs-eae370` Task 6, `beliefs-4857f1` Task 7, `beliefs-5b44e2` Task 8, `beliefs-d9ed0e` Task 9, `beliefs-d477a1` Task 10, `beliefs-fc5063` Task 11, each depending on its predecessor). `tasks start` each before its task and `tasks done` it in the task's commit.

- [ ] **Step 7: Verify and commit the freeze**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py tests/test_publication_engine_order.py -q
cd .. && tasks note beliefs-d7d7d1 "Cut 39 frozen: 13 units (W17-p-a..f, Y1-a, Y1-b, Y2-a, Y3-a, Y4-a..c); ROLLBACK_MEANS=<verdict>; RETRY_AFTER_ROLLBACK=<verdict>; chains cut 38."
tasks check && git add docs README.md python/tests/test_designs_corpus.py python/tests/test_publication_engine_order.py tasks
git commit -m "docs(cut): freeze conformance cut 39, publication records; bank the Y table"
git rev-parse HEAD
```
Record the full commit hash: Task 8's guard pins it as `CUT39_FREEZE_COMMIT`, and `sha256sum docs/designs/<freeze date>-conformance-cut-39.md` as `CUT39_FROZEN_SHA256`.

---

### Task 1: The shipped coordination contract, the two kinds, the `publish` family

**Files:**
- Create: `python/src/beliefs/contracts/coordination/v1/CONTRACT.yaml`, `python/src/beliefs/contracts/coordination/v2/CONTRACT.yaml`
- Modify: `python/src/beliefs/profile.py`, `python/src/beliefs/coordination.py:26-27`, `python/src/beliefs/permit.py:30-60,150-196`, `python/src/beliefs/corpus.py` (`mint_coordination`, `revise_coordination`), `python/src/beliefs/errors.py`, `python/tests/coordination_fixtures.py:20-78`
- Test: `python/tests/test_coordination_contract.py`, `python/tests/test_permit.py`, `python/tests/test_coordination_write.py`

**Interfaces:**
- Produces: `beliefs.profile.shipped_coordination(version: int = 2) -> CoordinationContract`; `beliefs.coordination.ORDINARY_COORDINATION_KINDS: tuple[str, ...]` (the eight), `PUBLICATION_KINDS = ("publication", "publication-binding")`, `COORDINATION_KINDS = (*ORDINARY_COORDINATION_KINDS, *PUBLICATION_KINDS)`; `beliefs.permit.ACT_FAMILIES` with `"publish"`, `KERNEL_REQUIREMENTS: frozenset[WritePermit]`, `RequiredCapabilities.publishes() -> RequiredCapabilities`; `beliefs.errors.KindNotMintedHere(WriteRefused)`; `coordination_fixtures.coordination_profile(base_contract, *, document=None, version=1)`.

- [ ] **Step 1: Write the v1 file.** Dump the fixture document to YAML and check the content identity survives:

```bash
cd python && mkdir -p src/beliefs/contracts/coordination/v1 src/beliefs/contracts/coordination/v2
uv run --frozen python - <<'EOF'
import yaml, sys
sys.path.insert(0, "tests")
from coordination_fixtures import COORDINATION_DOCUMENT
from beliefs.contract.coordination import parse_coordination_contract
text = "# The coordination contract, version 1 — coordination-and-view-kinds design §5.\n" + yaml.safe_dump(COORDINATION_DOCUMENT, sort_keys=False, allow_unicode=True)
open("src/beliefs/contracts/coordination/v1/CONTRACT.yaml", "w").write(text)
from beliefs.contract.document import parse_document
fixture = parse_coordination_contract(COORDINATION_DOCUMENT, source="fixture", predecessor=None)
shipped = parse_coordination_contract(parse_document(text, source="v1"), source="v1", predecessor=None)
assert shipped.content_identity == fixture.content_identity
print(shipped.content_identity)
EOF
```
Keep the printed identity: v2's `lineage` names it.

- [ ] **Step 2: Write the v2 file** — v1's text with `version: 2`, `lineage: {successor: <v1 identity>}`, `description: Project coordination records; version 2 adds the publication kinds (publication-records design §3)`, `composite` appended to `query_vocabulary.kinds`, `composes` appended to `query_vocabulary.relations`, and two kinds appended to `kinds`:

```yaml
  publication:
    fields: [name, body, author, at, event_token, published_from, destination, selection, supersedes_markers]
    query_versions: []
  publication-binding:
    fields: [name, body, author, at, event_token, view, destination, corpus_id, marker, artifact]
    query_versions: []
```

- [ ] **Step 3: Write the failing tests** — append to `python/tests/test_coordination_contract.py`:

```python
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination


def test_the_shipped_v1_is_the_former_fixture():
    from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract

    assert shipped_coordination(1).content_identity == coordination_contract(COORDINATION_DOCUMENT).content_identity


def test_v2_succeeds_v1_and_adds_exactly_the_publication_kinds_and_the_composite_vocabulary():
    v1, v2 = shipped_coordination(1), shipped_coordination(2)
    assert v2.predecessor == v1.content_identity and v2.version == 2
    assert set(v2.kinds) - set(v1.kinds) == {"publication", "publication-binding"}
    assert set(v2.query_kinds) - set(v1.query_kinds) == {"composite"}
    assert set(v2.query_relations) - set(v1.query_relations) == {"composes"}
    assert shipped_coordination() is v2


def test_v2_compiles_over_the_shipped_base():
    profile = compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))
    assert {"publication", "publication-binding"} <= set(profile.coordination_kinds)
    assert "composite" in profile.coordination_query_kinds and "composes" in profile.coordination_query_relations


def test_an_unknown_version_is_refused():
    import pytest
    from beliefs.errors import ProfileError

    with pytest.raises(ProfileError):
        shipped_coordination(3)
```

Append to `python/tests/test_permit.py`:

```python
from beliefs.permit import KERNEL_REQUIREMENTS, RequiredCapabilities, WritePermit, scoped_authority


def test_publishes_constructs_exactly_the_kernel_requirement():
    required = RequiredCapabilities.publishes()
    assert required.permit == WritePermit(frozenset({"publication-binding", "act-report"}), frozenset({"publish", "corpus-write"}))
    assert KERNEL_REQUIREMENTS == frozenset({required.permit})
    assert scoped_authority(required, "publisher").permit == required.permit


@pytest.mark.parametrize(
    "build",
    [
        lambda: RequiredCapabilities.for_kinds(["publication-binding"], {}),
        lambda: RequiredCapabilities(WritePermit(frozenset({"publication-binding"}), frozenset({"publish"}))),
        lambda: RequiredCapabilities(
            WritePermit(frozenset({"publication-binding", "act-report", "task"}), frozenset({"publish", "corpus-write"}))
        ),
    ],
    ids=["for_kinds", "direct", "widened"],
)
def test_every_ordinary_route_naming_publish_still_refuses(build):
    with pytest.raises(ValueError, match="a requirement names only command-reachable families"):
        build()


def test_the_coordination_requirement_excludes_the_publication_kinds():
    kinds = RequiredCapabilities.coordination().permit.kinds
    assert not kinds & {"publication", "publication-binding"}
    assert len(kinds) == 8
```

The existing test at `test_permit.py:178` (every declaration requirement is command-reachable) gains `if required.permit in KERNEL_REQUIREMENTS: continue` at the top of its loop body, and the `ACT_FAMILIES` assertion (if one spells the set) gains `"publish"`; `COMMAND_REACHABLE_FAMILIES == {"corpus-write", "run", "holdings"}` at line 44 stays.

Append to `python/tests/test_coordination_write.py`:

```python
@pytest.mark.parametrize("kind", ["publication", "publication-binding"])
def test_the_family_doors_refuse_the_publication_kinds(tmp_path, base_contract, kind):
    from beliefs.errors import KindNotMintedHere

    profile = coordination_profile(base_contract, version=2)
    writer, _resolver = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(project).address
    with pytest.raises(KindNotMintedHere):
        writer.mint_coordination(kind, project=address, content={})
    with pytest.raises(KindNotMintedHere):
        writer.revise_coordination(kind, CoordinationAddress(address.project, A), predecessors=(B,), content={})
```

- [ ] **Step 4: Run to see them fail**

```bash
cd python && uv run --frozen pytest tests/test_coordination_contract.py tests/test_permit.py tests/test_coordination_write.py -q
```
Expected: failures naming `shipped_coordination`, `KERNEL_REQUIREMENTS`, `KindNotMintedHere` and the `version` keyword.

- [ ] **Step 5: Implement.**

`profile.py`, beside `shipped_domain_contract`:

```python
@cache
def shipped_coordination(version: int = 2) -> CoordinationContract:
    """The coordination contract carried by this package (publication-records
    design decision 2): version 1, and version 2 parsed as its successor."""
    from beliefs.contract.coordination import parse_coordination_contract
    from beliefs.contract.document import parse_document

    if version not in (1, 2):
        raise ProfileError(f"this package ships coordination contract versions 1 and 2, not {version!r}")
    source = f"beliefs/contracts/coordination/v{version}/CONTRACT.yaml"
    text = resources.files("beliefs").joinpath(f"contracts/coordination/v{version}/CONTRACT.yaml").read_text(encoding="utf-8")
    predecessor = None if version == 1 else shipped_coordination(1)
    return parse_coordination_contract(parse_document(text, source=source), source=source, predecessor=predecessor)
```

`coordination.py:26-27`:

```python
VIEW_KINDS = ("project", "question", "hypothesis", "topic", "theme")
ORDINARY_COORDINATION_KINDS = (*VIEW_KINDS, "task", "decision", "note")
PUBLICATION_KINDS = ("publication", "publication-binding")
"""Minted only by the publish doors (publication-records design decision 6)."""
COORDINATION_KINDS = (*ORDINARY_COORDINATION_KINDS, *PUBLICATION_KINDS)
```
Add the two new names to `__all__`. `EXCLUDED_MUTATION_KINDS` and `_refuse_family_kinds` in `corpus.py` are built from `COORDINATION_KINDS` and need no edit (spec §3).

`permit.py`:

```python
ActFamily = Literal["corpus-write", "run", "holdings", "registry", "epoch", "lifecycle", "publish"]

ACT_FAMILIES: frozenset[str] = frozenset(
    {"corpus-write", "run", "holdings", "registry", "epoch", "lifecycle", "publish"}
)
"""The closed enumeration. `publish` is not command-reachable (publication-records design decision 7)."""
```
`_COORDINATION_KINDS` becomes the ten names and gains `_ORDINARY_COORDINATION_KINDS` (the eight); in `KIND_ACTS` replace the coordination spread with

```python
        **{kind: _CORPUS_WRITE for kind in _ORDINARY_COORDINATION_KINDS},
        "publication": frozenset({"publish"}),
        "publication-binding": frozenset({"publish"}),
```
Then, after `KIND_ACTS`:

```python
_PUBLICATION_PERMIT = WritePermit(frozenset({"publication-binding", "act-report"}), frozenset({"publish", "corpus-write"}))
KERNEL_REQUIREMENTS: frozenset[WritePermit] = frozenset({_PUBLICATION_PERMIT})
"""The one closed exception to command reachability (decision 7): the
publication requirement the publish doors cite. Every other permit naming a
non-command-reachable family is refused, exactly as before."""
```
(`WritePermit` is defined below `KIND_ACTS`; place these two names after the `WritePermit` class.) In `RequiredCapabilities.__post_init__`:

```python
        if not self.permit.act_families <= COMMAND_REACHABLE_FAMILIES and self.permit not in KERNEL_REQUIREMENTS:
            raise ValueError("a requirement names only command-reachable families")
```
`coordination()` returns `cls(WritePermit(frozenset(_ORDINARY_COORDINATION_KINDS), _CORPUS_WRITE))`; `publishes()` returns `cls(_PUBLICATION_PERMIT)`. `WritePermit` is frozen and hashable (a dataclass over two frozensets and a bool); if it is not hashable, add `eq=True, frozen=True` is already the case — verify with `hash(WritePermit.full())` in the REPL before relying on the frozenset.

`errors.py`, beside `PredecessorMismatch`:

```python
class KindNotMintedHere(WriteRefused):
    """A kind the ordinary coordination doors never mint: `publication` and
    `publication-binding` are minted only by the publish doors
    (publication-records design decision 6)."""
```

`corpus.py`, first statement of both `mint_coordination` and `revise_coordination`, before `self._authority.require(...)`:

```python
        if kind in PUBLICATION_KINDS:
            raise KindNotMintedHere(f"{kind!r} is minted only by the publish doors")
```
(import `PUBLICATION_KINDS` from `beliefs.coordination` and `KindNotMintedHere` from `beliefs.errors` in the existing import blocks). The refusal precedes the permit check so that a permit naming the kind still cannot route it here.

`coordination_fixtures.py`: replace the spelled `COORDINATION_DOCUMENT` literal with

```python
from importlib import resources

from beliefs.contract.document import parse_document

COORDINATION_DOCUMENT = parse_document(
    resources.files("beliefs").joinpath("contracts/coordination/v1/CONTRACT.yaml").read_text(encoding="utf-8"),
    source="beliefs/contracts/coordination/v1/CONTRACT.yaml",
)
```
and `coordination_profile` gains `version`:

```python
def coordination_profile(base_contract, *, document=None, version=1):
    if version == 2:
        assert document is None, "a v2 profile is the shipped contract"
        from beliefs.profile import shipped_coordination

        return compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))
    return compile_profile(shipped_base_contract(), [], coordination=coordination_contract(document))
```

- [ ] **Step 6: Run the targeted suites, the permit inventories, and staleness**

```bash
cd python && uv run --frozen pytest tests/test_coordination_contract.py tests/test_permit.py tests/test_coordination_write.py tests/test_coordination.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py tests/test_arm_staleness.py -q
just test-fast
```
Expected: all green. A `test_permit_entry_points.py` failure over `KIND_ACTS`' key set means a kind list was missed; a stale prior arm means a pinned line in `coordination.py`, `permit.py` or `corpus.py` moved — restore its spelling.

- [ ] **Step 7: Commit**

```bash
tasks check && git add python/src/beliefs/contracts/coordination python/src/beliefs/profile.py python/src/beliefs/coordination.py python/src/beliefs/permit.py python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(coordination): ship contract v1 and v2, the publication kinds and the publish family — Y1"
```

---

### Task 2: The act-report amendment — the `publish` kind and its one entry

**Files:**
- Modify: `python/src/beliefs/report.py:53,79-92,236-360`, `python/src/beliefs/stored.py:866-940`, `python/src/beliefs/intents/shapes.py:127-138`, `python/src/beliefs/boundary.py` (beside `_mint_audit_report`)
- Test: the act-report unit module (`ls python/tests | grep -i 'report'`; add to `test_report.py` or its equivalent), `python/tests/test_intent_shapes.py` (or the module `grep -ln 'decode_intent' python/tests/test_*.py` names)

**Interfaces:**
- Produces: `report.OPERATION_KINDS` with `"publish"` (nine); `report.PublicationBindingEntry(subject: str, outcome: BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused)`; `report.BindingBound(binding: str, corpus_id: str, marker: str)`; `report.BindingPredecessorNotStanding(corpus_id: str, marker: str, remotely_revealed: bool, tips: tuple[str, ...])`; `report.BindingEvidenceRefused(corpus_id: str, marker: str, remotely_revealed: bool, reason: str)`; `report.EVIDENCE_REFUSAL_REASONS: tuple[str, ...]`; `boundary._mint_publish_report(intent, *, observer: str, instrument: str, opened_at: str, closed_at: str, entry: PublicationBindingEntry) -> ActReport`.

- [ ] **Step 1: Write the failing tests** (in the act-report unit module):

```python
import pytest

from beliefs import stored
from beliefs.errors import MalformedRecord
from beliefs.report import (
    EVIDENCE_REFUSAL_REASONS,
    OPERATION_KINDS,
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    OperationIntent,
    PublicationBindingEntry,
    _mint_report,
)

SUBJECT = "coord:" + "a" * 32 + "/" + "b" * 32


def publish_report(outcome):
    return _mint_report(
        operation="publish", event_token="c" * 32, actor="actor", observer="actor",
        instrument="beliefs.publish", opened_at="2026-09-22T00:00:00Z", closed_at="2026-09-22T00:00:01Z",
        entries=(PublicationBindingEntry(SUBJECT, outcome),),
    )


@pytest.mark.parametrize(
    "outcome",
    [
        BindingBound("d" * 32, "e" * 32, "f" * 32),
        BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32, "2" * 32)),
        BindingEvidenceRefused("e" * 32, "f" * 32, False, "mounts-changed"),
    ],
    ids=["bound", "predecessor-not-standing", "evidence-refused"],
)
def test_each_publish_outcome_round_trips_through_the_stored_mirror(outcome):
    report = publish_report(outcome)
    node = stored.act_report_node(report)
    facet = stored.act_report_facet(node)
    (entry,) = facet["entries"]
    assert entry["kind"] == "publication-binding" and entry["subject"] == SUBJECT
    assert set(entry) == {"kind", "subject", "outcome"}


def test_publish_is_in_the_closed_set_but_never_an_operation_intent():
    assert "publish" in OPERATION_KINDS and len(OPERATION_KINDS) == 9
    with pytest.raises(MalformedRecord, match="opens only through its domain intent"):
        OperationIntent("publish", "c" * 32, "actor")


def test_the_evidence_refusal_reasons_are_closed():
    assert EVIDENCE_REFUSAL_REASONS == (
        "mounts-changed", "anchor-unplaced", "chain-absent", "chain-malformed", "revision-missing",
        "revision-mismatch", "revision-malformed", "history-violated", "unregistered-revision", "tips-disagree",
    )
    with pytest.raises(MalformedRecord):
        BindingEvidenceRefused("e" * 32, "f" * 32, False, "other")


@pytest.mark.parametrize("field, value", [("remotely_revealed", "yes"), ("tips", ["not-hex"])])
def test_the_stored_mirror_refuses_a_malformed_publish_outcome(field, value):
    report = publish_report(BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32,)))
    node = stored.act_report_node(report)
    node.facets["act-report"]["entries"][0]["outcome"][field] = value
    with pytest.raises(MalformedRecord):
        stored.act_report_facet(node)
```

In the intent-shape module:

```python
from beliefs.identity import v1
from beliefs.intents.shapes import Unrecognized, decode_intent


def test_a_domainless_publish_triple_is_malformed_not_an_operation():
    payload = v1.encode({"kind": "publish", "event_token": "c" * 32, "actor": "actor"})
    decoded = decode_intent("0" * 64, payload)
    assert type(decoded) is Unrecognized and decoded.code == "intent-payload-malformed" and decoded.detail == "operation"
```

- [ ] **Step 2: Run to see them fail** — `cd python && uv run --frozen pytest <the two modules> -q`; expected import errors for the new names.

- [ ] **Step 3: Implement.** `report.py`: `OPERATION_KINDS` gains `"publish"` in sorted position (`("acquisition", "audit", "consolidate", "corpus-write", "import", "move", "publish", "re-check", "run-attempt")`). `OperationIntent.__post_init__` gains, after the closed-set check:

```python
        if self.kind == "publish":
            raise MalformedRecord("publish opens only through its domain intent, science.publish-intent.v1")
```
Beside the other outcomes:

```python
EVIDENCE_REFUSAL_REASONS = (
    "mounts-changed", "anchor-unplaced", "chain-absent", "chain-malformed", "revision-missing",
    "revision-mismatch", "revision-malformed", "history-violated", "unregistered-revision", "tips-disagree",
)
_HEX32 = re.compile(r"[0-9a-f]{32}")


def _require_hex32(value: object, where: str) -> None:
    if type(value) is not str or _HEX32.fullmatch(value) is None:
        raise MalformedRecord(f"{where} must be 32 lowercase hexadecimal characters")


@sealed
@final
@dataclass(frozen=True)
class BindingBound:
    binding: str
    corpus_id: str
    marker: str

    def __post_init__(self) -> None:
        for name in ("binding", "corpus_id", "marker"):
            _require_hex32(getattr(self, name), f"bound {name}")


@sealed
@final
@dataclass(frozen=True)
class BindingPredecessorNotStanding:
    corpus_id: str
    marker: str
    remotely_revealed: bool
    tips: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "refusal corpus id")
        _require_hex32(self.marker, "refusal marker")
        if type(self.remotely_revealed) is not bool:
            raise MalformedRecord("remotely_revealed must be a bool")
        if type(self.tips) is not tuple or list(self.tips) != sorted(set(self.tips)):
            raise MalformedRecord("tips must be a strictly ascending tuple")
        for tip in self.tips:
            _require_hex32(tip, "refusal tip")


@sealed
@final
@dataclass(frozen=True)
class BindingEvidenceRefused:
    corpus_id: str
    marker: str
    remotely_revealed: bool
    reason: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "refusal corpus id")
        _require_hex32(self.marker, "refusal marker")
        if type(self.remotely_revealed) is not bool:
            raise MalformedRecord("remotely_revealed must be a bool")
        if self.reason not in EVIDENCE_REFUSAL_REASONS:
            raise MalformedRecord(f"evidence refusal reason {self.reason!r} is outside {EVIDENCE_REFUSAL_REASONS}")


@sealed
@final
@dataclass(frozen=True)
class PublicationBindingEntry:
    subject: str
    outcome: BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused

    def __post_init__(self) -> None:
        _require_str(self.subject, "publication binding entry subject")
        _require_outcome(self, self.outcome)
```
(`import re` at the top.) Extend `Outcome`, `Entry`, `_ALLOWED_OUTCOMES` (`PublicationBindingEntry: (BindingBound, BindingPredecessorNotStanding, BindingEvidenceRefused)`), `_ENTRY_KINDS` (`"publication-binding"`), `_OUTCOME_TYPES` (`"bound"`, `"predecessor-not-standing"`, `"evidence-refused"`), and `__all__`. `_outcome_facet` already turns a tuple into a list and leaves a bool as a bool.

`stored.py` `_REPORT_ENTRY_OUTCOMES` gains

```python
    "publication-binding": {
        "bound": ("binding", "corpus_id", "marker"),
        "predecessor-not-standing": ("corpus_id", "marker", "remotely_revealed", "tips"),
        "evidence-refused": ("corpus_id", "marker", "remotely_revealed", "reason"),
    },
```
and `_valid_report_entry`'s field loop becomes

```python
    for field in fields:
        value = outcome[field]
        if field == "remotely_revealed":
            if type(value) is not bool:
                return False
        elif field == "tips":
            if not isinstance(value, list) or any(
                type(member) is not str or re.fullmatch(r"[0-9a-f]{32}", member) is None for member in value
            ):
                return False
        elif outcome_type == "imported-records" or field == "retired_uids":
            if not isinstance(value, list) or any(type(member) is not str for member in value):
                return False
        elif type(value) is not str:
            return False
```
(place the two new branches *before* the existing `if`, so its lines stay byte-identical for any pinned arm; check with `tests/test_arm_staleness.py`).

`intents/shapes.py`, the domainless branch at line 127:

```python
    if set(value) == {"kind", "event_token", "actor"} and value.get("kind") == "publish":
        return _malformed(digest, "operation")
```
inserted immediately **before** the existing `if set(value) == {"kind", "event_token", "actor"} and value.get("kind") in OPERATION_KINDS:` line.

`boundary.py`, beside `_mint_audit_report`, on its shape:

```python
def _mint_publish_report(
    intent, *, observer: str, instrument: str, opened_at: str, closed_at: str, entry: PublicationBindingEntry
) -> ActReport:
    """The publish report: exactly one publication-binding entry (publication-records design §7)."""
    if getattr(intent, "kind", None) != "publish":
        raise MalformedRecord("a publish report closes a publish intent")
    if type(entry) is not PublicationBindingEntry:
        raise MalformedRecord("a publish report carries one publication-binding entry")
    return _mint_report(
        operation="publish", event_token=intent.event_token, actor=intent.actor, observer=observer,
        instrument=instrument, opened_at=opened_at, closed_at=closed_at, entries=(entry,),
    )
```
(`intent` is Task 3's `PublishIntent`; the attribute check keeps this task independent of it.)

- [ ] **Step 4: Run** — the two modules, then `tests/test_arm_staleness.py`, then `just test-fast`. Expected green.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/report.py python/src/beliefs/stored.py python/src/beliefs/intents/shapes.py python/src/beliefs/boundary.py python/tests tasks
git commit -m "feat(report): the publish operation kind and its publication-binding entry — Y3, Y4"
```

---

### Task 3: The publish intent — `beliefs/intents/publish.py`

**Files:**
- Create: `python/src/beliefs/intents/publish.py`, `python/tests/test_publish_intent.py`
- Modify: `python/src/beliefs/intents/shapes.py` (`DecodedIntent`, the dispatch, `mismatch`), `python/src/beliefs/report.py` (`completion`), `python/src/beliefs/intents/reduce.py` (the shape literal, if `IntentQualification.shape` is a `Literal`), `python/src/beliefs/coordination.py` (`Anchor`)

**Interfaces:**
- Consumes: Task 2's `OPERATION_KINDS`.
- Produces: `beliefs.coordination.Anchor(corpus_id: str, genesis: str, head: str)`; `beliefs.intents.publish.PUBLISH_INTENT_DOMAIN = "science.publish-intent.v1"`; `Destination(type: Literal["local", "remote"], locator: str)` with `Destination.local(path: str)`, `Destination.remote(url: str)`, `.projection() -> dict[str, str]`, `Destination.from_projection(value: object) -> Destination`; `PublishIntent(kind: str, event_token: str, actor: str, at: str, view: CoordinationAddress, destination: Destination, binding_tips: tuple[str, ...], marker_tips: tuple[tuple[str, str], ...], anchors: tuple[Anchor, ...])`; `encode_publish_intent(intent: PublishIntent) -> bytes`; `decode_publish_intent(payload: bytes) -> PublishIntent` (raises `MalformedRecord`); `shapes.DecodedIntent.shape` gains `"publish"`.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_publish_intent.py`:

```python
import pytest

from beliefs.coordination import Anchor, CoordinationAddress
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination, PublishIntent, decode_publish_intent, encode_publish_intent
from beliefs.intents.shapes import DecodedIntent, ReportEvidence, Unrecognized, decode_intent, mismatch
from beliefs.report import CLOSED, UNFINISHED, Registration, completion

VIEW = CoordinationAddress("a" * 32, "b" * 32, "c" * 32)


def intent(**changes) -> PublishIntent:
    values = dict(
        kind="publish", event_token="d" * 32, actor="actor", at="2026-09-22T00:00:00Z", view=VIEW,
        destination=Destination.local("/srv/published/mm30"), binding_tips=("1" * 32,),
        marker_tips=(("e" * 32, "f" * 32),), anchors=(Anchor("0" * 32, "9" * 64, "8" * 64),),
    )
    values.update(changes)
    return PublishIntent(**values)


def test_the_intent_round_trips_byte_exactly():
    value = intent()
    payload = encode_publish_intent(value)
    assert decode_publish_intent(payload) == value
    assert encode_publish_intent(decode_publish_intent(payload)) == payload


@pytest.mark.parametrize(
    "changes",
    [
        {"binding_tips": ("2" * 32, "1" * 32)},
        {"binding_tips": ("1" * 32, "1" * 32)},
        {"marker_tips": (("e" * 32, "f" * 32), ("a" * 32, "f" * 32))},
        {"anchors": (Anchor("1" * 32, "9" * 64, "8" * 64), Anchor("0" * 32, "9" * 64, "8" * 64))},
        {"view": CoordinationAddress("a" * 32, "b" * 32)},
        {"at": "yesterday"},
        {"kind": "audit"},
        {"event_token": "short"},
    ],
    ids=["tips-order", "tips-duplicate", "markers-order", "anchors-order", "view-unpinned", "at", "kind", "token"],
)
def test_every_malformed_field_is_refused(changes):
    with pytest.raises(MalformedRecord):
        intent(**changes)


def test_destinations_are_canonical():
    assert Destination.local("/srv/published/../published/mm30/") == Destination.local("/srv/published/mm30")
    with pytest.raises(MalformedRecord):
        Destination("local", "relative/path")
    with pytest.raises(MalformedRecord):
        Destination("local", "//host/share")
    assert Destination.remote("HTTPS://Example.org/a").locator == Destination.remote("https://example.org/a").locator


def test_decode_intent_dispatches_the_domain_and_mismatch_qualifies_by_a_publish_report():
    payload = encode_publish_intent(intent())
    decoded = decode_intent("0" * 64, payload)
    assert type(decoded) is DecodedIntent and decoded.shape == "publish"
    assert mismatch(decoded, ReportEvidence("publish", "d" * 32)) is None
    assert mismatch(decoded, ReportEvidence("audit", "d" * 32)) == "wrong-kind"
    assert mismatch(decoded, ReportEvidence("publish", "e" * 32)) == "wrong-token"


def test_a_malformed_payload_under_the_domain_is_malformed():
    payload = v1.encode({"domain": "science.publish-intent.v1", "kind": "publish"})
    decoded = decode_intent("0" * 64, payload)
    assert type(decoded) is Unrecognized and decoded.code == "intent-payload-malformed" and decoded.detail == "publish"


def test_completion_reads_a_publish_intent():
    from test_act_report_publish import publish_report  # Task 2's helper; move it to a shared fixture module if the test module is named otherwise
    from beliefs.report import BindingBound

    report = publish_report(BindingBound("d" * 32, "e" * 32, "f" * 32))
    value = intent(event_token=report.event_token)
    assert completion(value, (Registration(value.event_token, "r"),), {"r": report}) == CLOSED
    assert completion(value, (), {}) == UNFINISHED
```
Adjust the `publish_report` import to wherever Task 2 put it.

- [ ] **Step 2: Run to see them fail.**

- [ ] **Step 3: Implement.** In `coordination.py`, beside `CoordinationRevision`:

```python
@sealed
@final
@dataclass(frozen=True)
class Anchor:
    """One mounted root's head at a publish intent (publication-records design decision 3)."""

    corpus_id: str
    genesis: str
    head: str

    def __post_init__(self) -> None:
        if _HEX.fullmatch(self.corpus_id) is None:
            raise MalformedRecord("anchor corpus_id must be 32 lowercase hexadecimal characters")
        for name in ("genesis", "head"):
            if re.fullmatch(r"[0-9a-f]{64}", getattr(self, name)) is None:
                raise MalformedRecord(f"anchor {name} must be a 64-lowercase-hex entry digest")
```

`python/src/beliefs/intents/publish.py`:

```python
"""The publish intent (publication-records design §5): a domain-tagged payload
carrying its own evidence. Pure: one codec, one sealed value."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, final

from beliefs.coordination import Anchor, CoordinationAddress
from beliefs.errors import CanonicalTextRefused, MalformedRecord
from beliefs.identity import v1
from beliefs.permit import require_actor
from beliefs.sealed import sealed

__all__ = ["PUBLISH_INTENT_DOMAIN", "Destination", "PublishIntent", "decode_publish_intent", "encode_publish_intent"]

PUBLISH_INTENT_DOMAIN = "science.publish-intent.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
_FIELDS = frozenset(
    {"domain", "kind", "event_token", "actor", "at", "view", "destination", "binding_tips", "marker_tips", "anchors"}
)


@sealed
@final
@dataclass(frozen=True)
class Destination:
    """The closed destination union (decision 9)."""

    type: Literal["local", "remote"]
    locator: str

    def __post_init__(self) -> None:
        if self.type == "local":
            if (
                type(self.locator) is not str
                or not self.locator.startswith("/")
                or self.locator.startswith("//")
                or posixpath.normpath(self.locator) != self.locator
            ):
                raise MalformedRecord(f"a local destination is an absolute, normalized POSIX path, not {self.locator!r}")
        elif self.type == "remote":
            from beliefs.holdings.records import url_locator

            try:
                canonical = url_locator(self.locator).url
            except (MalformedRecord, ValueError) as caught:
                raise MalformedRecord(f"a remote destination is a canonical URL: {caught}") from caught
            if canonical != self.locator:
                raise MalformedRecord(f"remote destination {self.locator!r} is not the canonical spelling")
        else:
            raise MalformedRecord(f"destination type {self.type!r} is outside local and remote")

    @classmethod
    def local(cls, path: str) -> Destination:
        if type(path) is not str or not path.startswith("/"):
            raise MalformedRecord("a local destination must be absolute")
        return cls("local", posixpath.normpath(path))

    @classmethod
    def remote(cls, url: str) -> Destination:
        from beliefs.holdings.records import url_locator

        return cls("remote", url_locator(url).url)

    def projection(self) -> dict[str, str]:
        return {"type": self.type, "locator": self.locator}

    @classmethod
    def from_projection(cls, value: object) -> Destination:
        if not isinstance(value, dict) or set(value) != {"type", "locator"}:
            raise MalformedRecord("a destination is exactly {type, locator}")
        return cls(value["type"], value["locator"])


def _strictly_ascending(values: tuple, where: str) -> None:
    if list(values) != sorted(set(values)):
        raise MalformedRecord(f"{where} must be strictly ascending")


@sealed
@final
@dataclass(frozen=True)
class PublishIntent:
    kind: str
    event_token: str
    actor: str
    at: str
    view: CoordinationAddress
    destination: Destination
    binding_tips: tuple[str, ...]
    marker_tips: tuple[tuple[str, str], ...]
    anchors: tuple[Anchor, ...]

    def __post_init__(self) -> None:
        if self.kind != "publish":
            raise MalformedRecord("a publish intent's kind is publish")
        if type(self.event_token) is not str or _HEX32.fullmatch(self.event_token) is None:
            raise MalformedRecord("a publish intent's event token is 32 lowercase hex")
        require_actor(self.actor)
        if type(self.at) is not str or _RFC3339.fullmatch(self.at) is None:
            raise MalformedRecord("a publish intent's at is an RFC3339 timestamp")
        try:
            datetime.fromisoformat(self.at)
        except ValueError as caught:
            raise MalformedRecord("a publish intent's at is a calendar timestamp") from caught
        if type(self.view) is not CoordinationAddress or self.view.revision is None:
            raise MalformedRecord("a publish intent names its view pinned to the resolved revision")
        if type(self.destination) is not Destination:
            raise MalformedRecord("a publish intent's destination is a Destination")
        if type(self.binding_tips) is not tuple or any(type(t) is not str or _HEX32.fullmatch(t) is None for t in self.binding_tips):
            raise MalformedRecord("binding tips are 32-hex revision ids")
        _strictly_ascending(self.binding_tips, "binding tips")
        if type(self.marker_tips) is not tuple or any(
            type(pair) is not tuple or len(pair) != 2 or any(type(m) is not str or _HEX32.fullmatch(m) is None for m in pair)
            for pair in self.marker_tips
        ):
            raise MalformedRecord("marker tips are (corpus_id, marker uid) pairs of 32-hex")
        _strictly_ascending(self.marker_tips, "marker tips")
        if type(self.anchors) is not tuple or any(type(a) is not Anchor for a in self.anchors):
            raise MalformedRecord("anchors are Anchor values")
        _strictly_ascending(tuple(a.corpus_id for a in self.anchors), "anchors by corpus_id")


def encode_publish_intent(intent: PublishIntent) -> bytes:
    if type(intent) is not PublishIntent:
        raise MalformedRecord("encode_publish_intent takes a PublishIntent")
    return v1.encode(
        {
            "domain": PUBLISH_INTENT_DOMAIN,
            "kind": intent.kind,
            "event_token": intent.event_token,
            "actor": intent.actor,
            "at": intent.at,
            "view": str(intent.view),
            "destination": intent.destination.projection(),
            "binding_tips": list(intent.binding_tips),
            "marker_tips": [list(pair) for pair in intent.marker_tips],
            "anchors": [{"corpus_id": a.corpus_id, "genesis": a.genesis, "head": a.head} for a in intent.anchors],
        }
    )


def decode_publish_intent(payload: bytes) -> PublishIntent:
    try:
        value = v1.decode(payload)
    except CanonicalTextRefused as caught:
        raise MalformedRecord("a publish intent payload is not canonical text") from caught
    if not isinstance(value, dict) or set(value) != _FIELDS or value["domain"] != PUBLISH_INTENT_DOMAIN:
        raise MalformedRecord("a publish intent carries exactly its closed field set under its domain")
    try:
        intent = PublishIntent(
            kind=value["kind"],
            event_token=value["event_token"],
            actor=value["actor"],
            at=value["at"],
            view=CoordinationAddress.parse(value["view"]),
            destination=Destination.from_projection(value["destination"]),
            binding_tips=tuple(value["binding_tips"]),
            marker_tips=tuple(tuple(pair) for pair in value["marker_tips"]),
            anchors=tuple(Anchor(**anchor) for anchor in value["anchors"]),
        )
    except (TypeError, ValueError, KeyError) as caught:
        raise MalformedRecord(f"a publish intent field is malformed: {caught}") from caught
    if encode_publish_intent(intent) != payload:
        raise MalformedRecord("a publish intent payload is not its canonical encoding")
    return intent
```
(`v1.decode` is exported by `identity/v1.py`'s `__all__`; if `Anchor(**anchor)` receives a mapping with other keys it raises `TypeError`, which is caught.)

`intents/shapes.py`: `DecodedIntent.shape: Literal["assessment-run", "operation", "holdings", "publish"]` and `value` gains `| PublishIntent` (import under `TYPE_CHECKING` to keep the import graph acyclic; `intents/publish.py` imports nothing from `shapes`). In the domain branch, beside the holdings test:

```python
        if sniffed["domain"] == PUBLISH_INTENT_DOMAIN:
            from beliefs.intents.publish import decode_publish_intent

            try:
                return DecodedIntent(digest, "publish", decode_publish_intent(payload))
            except MalformedRecord:
                return _malformed(digest, "publish")
```
In `mismatch`, immediately before the `if type(evidence) is ObservationEvidence:` fall-through at the end:

```python
    if intent.shape == "publish":
        if type(evidence) is ReportEvidence:
            if evidence.operation != "publish":
                return "wrong-kind"
            return None if evidence.event_token == value.event_token else "wrong-token"
        return "wrong-purpose"
```

`report.py` `completion`: the type check becomes

```python
    from beliefs.intents.publish import PublishIntent

    if type(intent) not in (OperationIntent, AssessmentRunIntent, PublishIntent):
        raise MalformedRecord("completion requires an operation intent")
```
and the `DecodedIntent` construction's shape becomes `"assessment-run" if type(intent) is AssessmentRunIntent else "publish" if type(intent) is PublishIntent else "operation"`. The `Intent` alias gains `PublishIntent` under `TYPE_CHECKING`.

`intents/reduce.py`: if `IntentQualification.shape` is typed as a `Literal`, add `"publish"`; `grep -n 'shape:' src/beliefs/intents/reduce.py` settles it.

- [ ] **Step 4: Run** — `tests/test_publish_intent.py`, the shape and reduce modules (`grep -ln 'reduce_chain\|decode_intent' tests/test_*.py`), `tests/test_arm_staleness.py`, `just test-fast`. Expected green.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/intents python/src/beliefs/report.py python/src/beliefs/coordination.py python/tests tasks
git commit -m "feat(intents): the evidence-bearing publish intent — Y3, W17"
```

---

### Task 4: The records — `beliefs/publication.py`

**Files:**
- Create: `python/src/beliefs/publication.py`, `python/tests/test_publication.py`

**Interfaces:**
- Consumes: Task 1's `PUBLICATION_KINDS`; Task 3's `Destination`, `PublishIntent`.
- Produces: `binding_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress`; `marker_address(view, destination) -> CoordinationAddress`; `binding_uid(event_token: str) -> str`; `marker_uid(event_token: str) -> str`; `binding_record(intent: PublishIntent, *, corpus_id: str, marker: str, artifact: str) -> Node`; `marker_record(intent: PublishIntent, *, world_id: str, epoch: str, selection: tuple[str, ...]) -> Node`; `publication_content_malformed(node: Node) -> bool`; `marker_consistent(node: Node) -> bool`; `BINDING_KIND = "publication-binding"`, `MARKER_KIND = "publication"`.

The spec's `marker_record(intent, *, world_id, epoch, view_revision, selection)` loses `view_revision`: the intent's `view` is pinned to it (§5), so a separate argument could only disagree with it.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_publication.py`:

```python
import pytest
from nodes.core.frontmatter import node_to_markdown

from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.intents.publish import Destination
from beliefs.publication import (
    binding_address,
    binding_record,
    marker_address,
    marker_consistent,
    marker_record,
    publication_content_malformed,
)
from test_publish_intent import intent

VIEW = CoordinationAddress("a" * 32, "b" * 32)
HERE = Destination.local("/srv/published/mm30")


def test_the_two_addresses_differ_and_share_the_project():
    binding, marker = binding_address(VIEW, HERE), marker_address(VIEW, HERE)
    assert binding != marker and binding.project == marker.project == VIEW.project


def test_two_spellings_of_one_directory_are_one_address():
    assert binding_address(VIEW, Destination.local("/srv/published/./mm30")) == binding_address(VIEW, HERE)


def test_a_project_view_has_addresses_too():
    assert binding_address(CoordinationAddress("a" * 32), HERE).local is not None


def test_both_records_are_byte_functions_of_their_inputs():
    value = intent()
    first = binding_record(value, corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    second = binding_record(value, corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    assert node_to_markdown(first) == node_to_markdown(second)
    assert coordination_revision(first).predecessors == tuple(
        f"publication-binding:{first.facets['coordination']['project']}.{first.facets['coordination']['local']}.{tip}"
        for tip in value.binding_tips
    )
    marker = marker_record(value, world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1", "proposition:p2"))
    assert node_to_markdown(marker) == node_to_markdown(
        marker_record(value, world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1", "proposition:p2"))
    )
    assert marker.relations == [] and not publication_content_malformed(marker) and not publication_content_malformed(first)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda n: n.facets["coordination"].__setitem__("event_token", "0" * 32),
        lambda n: n.facets["coordination"].__setitem__("destination", {"type": "local", "locator": "/elsewhere"}),
        lambda n: n.facets["coordination"]["published_from"].__setitem__("view", "coord:" + "c" * 32 + "/" + "d" * 32 + "@" + "e" * 32),
    ],
    ids=["token", "destination", "view"],
)
def test_marker_consistency_is_self_contained(mutate):
    marker = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    assert marker_consistent(marker)
    mutate(marker)
    assert not marker_consistent(marker)


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", "other"), ("body", "text"), ("event_token", "short"), ("corpus_id", "x"), ("marker", "x"),
        ("artifact", "x"), ("view", "coord:" + "a" * 32), ("destination", {"type": "local", "locator": "rel"}),
    ],
)
def test_every_binding_field_rule_refuses(field, value):
    node = binding_record(intent(), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    if field in {"name", "body"}:
        node = node.model_copy(update={"title" if field == "name" else "body": value})
    else:
        node.facets["coordination"][field] = value
    assert publication_content_malformed(node)


@pytest.mark.parametrize(
    "field, value",
    [
        ("selection", []), ("selection", ["b", "a"]), ("supersedes_markers", [["b" * 32, "c" * 32], ["a" * 32, "c" * 32]]),
        ("published_from", {"world_id": "7" * 32}),
    ],
)
def test_every_marker_field_rule_refuses(field, value):
    node = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    node.facets["coordination"][field] = value
    assert publication_content_malformed(node)
```
(`Node.model_copy` is pydantic's; if `nodes`' `Node` is not a pydantic model, rebuild the node with `Node(**{**node.__dict__, "title": value})` — `grep -n 'class Node' $(uv run --frozen python -c "import nodes, os; print(os.path.dirname(nodes.__file__))")/core/node.py` settles it.)

- [ ] **Step 2: Run to see them fail.**

- [ ] **Step 3: Implement** `python/src/beliefs/publication.py`:

```python
"""Publication records (publication-records design §3–§4): the two addresses per
(view, destination), deterministic identities, the closed content rules, the
factories, and the self-contained marker check. Pure: no clock, no randomness,
no I/O — every byte is a function of the intent and the named arguments."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination

if TYPE_CHECKING:
    from beliefs.intents.publish import PublishIntent

__all__ = [
    "BINDING_KIND",
    "MARKER_KIND",
    "binding_address",
    "binding_record",
    "binding_uid",
    "marker_address",
    "marker_consistent",
    "marker_record",
    "marker_uid",
    "publication_content_malformed",
]

BINDING_KIND = "publication-binding"
MARKER_KIND = "publication"
_BINDING_ADDRESS_DOMAIN = "science.publication-binding-address.v1"
_MARKER_ADDRESS_DOMAIN = "science.publication-address.v1"
_BINDING_UID_DOMAIN = "science.publication-binding.v1"
_MARKER_UID_DOMAIN = "science.publication.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_BINDING_FIELDS = frozenset({"project", "local", "author", "at", "event_token", "view", "destination", "corpus_id", "marker", "artifact"})
_MARKER_FIELDS = frozenset({"project", "local", "author", "at", "event_token", "published_from", "destination", "selection", "supersedes_markers"})


def _address(domain: str, view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    if type(view) is not CoordinationAddress or type(destination) is not Destination:
        raise MalformedRecord("an address derives from a CoordinationAddress and a Destination")
    unpinned = view.unpinned()
    local = v1.digest(domain, [unpinned.project, unpinned.local or "", destination.projection()])[:32]
    return CoordinationAddress(unpinned.project, local)


def binding_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    return _address(_BINDING_ADDRESS_DOMAIN, view, destination)


def marker_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    return _address(_MARKER_ADDRESS_DOMAIN, view, destination)


def binding_uid(event_token: str) -> str:
    return v1.digest(_BINDING_UID_DOMAIN, event_token)[:32]


def marker_uid(event_token: str) -> str:
    return v1.digest(_MARKER_UID_DOMAIN, event_token)[:32]


def _node(kind: str, address: CoordinationAddress, uid: str, facet: dict[str, object], predecessors: tuple[str, ...]) -> Node:
    from beliefs.corpus import CorpusWriter

    content = {"name": kind, "body": "", **{name: value for name, value in facet.items() if name not in {"project", "local"}}}
    predecessor_nodes = tuple(
        Node(id=f"{kind}:{address.project}.{address.local}.{tip}", uid=tip, kind=kind, title=kind, body="", facets={}, relations=[])
        for tip in predecessors
    )
    return CorpusWriter._coordination_node(kind, address, uid, content, predecessors=predecessor_nodes)


def binding_record(intent: PublishIntent, *, corpus_id: str, marker: str, artifact: str) -> Node:
    address = binding_address(intent.view, intent.destination)
    facet: dict[str, object] = {
        "author": intent.actor,
        "at": intent.at,
        "event_token": intent.event_token,
        "view": str(intent.view.unpinned()),
        "destination": intent.destination.projection(),
        "corpus_id": corpus_id,
        "marker": marker,
        "artifact": artifact,
    }
    node = _node(BINDING_KIND, address, binding_uid(intent.event_token), facet, intent.binding_tips)
    if publication_content_malformed(node):
        raise MalformedRecord("a binding's content is outside its closed rule")
    return node


def marker_record(intent: PublishIntent, *, world_id: str, epoch: str, selection: tuple[str, ...]) -> Node:
    address = marker_address(intent.view, intent.destination)
    facet: dict[str, object] = {
        "author": intent.actor,
        "at": intent.at,
        "event_token": intent.event_token,
        "published_from": {"world_id": world_id, "epoch": epoch, "view": str(intent.view)},
        "destination": intent.destination.projection(),
        "selection": list(selection),
        "supersedes_markers": [list(pair) for pair in intent.marker_tips],
    }
    node = _node(MARKER_KIND, address, marker_uid(intent.event_token), facet, ())
    if publication_content_malformed(node):
        raise MalformedRecord("a marker's content is outside its closed rule")
    return node
```
`published_from` carries `view` pinned (the spec's `view_revision` is the pin, §4 note above), so its closed shape is `{world_id, epoch, view}`; the spec's table row "`{world_id, epoch, view, view_revision}`" is corrected in Step 5 below.

```python
def _ascending_strings(value: object, pattern: re.Pattern[str] | None, *, nonempty: bool) -> bool:
    return (
        type(value) is list
        and (bool(value) or not nonempty)
        and all(type(member) is str and (pattern is None or pattern.fullmatch(member)) for member in value)
        and value == sorted(set(value))
    )


def publication_content_malformed(node: Node) -> bool:
    """The closed per-kind rule beside `_validated_coordination_content` (spec §3)."""
    try:
        revision = coordination_revision(node)
    except MalformedRecord:
        return True
    facet = node.facets[stored.COORDINATION_FACET]
    if node.kind not in (BINDING_KIND, MARKER_KIND) or node.title != node.kind or node.body != "":
        return True
    if type(facet.get("event_token")) is not str or _HEX32.fullmatch(facet["event_token"]) is None:
        return True
    try:
        destination = Destination.from_projection(facet.get("destination"))
    except MalformedRecord:
        return True
    if node.kind == BINDING_KIND:
        if set(facet) != _BINDING_FIELDS or revision.address.local is None:
            return True
        try:
            view = CoordinationAddress.parse(facet["view"])
        except ValueError:
            return True
        return (
            view.revision is not None
            or any(type(facet[name]) is not str or _HEX32.fullmatch(facet[name]) is None for name in ("corpus_id", "marker"))
            or type(facet["artifact"]) is not str
            or _HEX64.fullmatch(facet["artifact"]) is None
            or binding_address(view, destination) != revision.address
            or node.uid != binding_uid(facet["event_token"])
        )
    if set(facet) != _MARKER_FIELDS or node.relations:
        return True
    source = facet["published_from"]
    if not isinstance(source, dict) or set(source) != {"world_id", "epoch", "view"}:
        return True
    try:
        view = CoordinationAddress.parse(source["view"])
    except ValueError:
        return True
    pairs = facet["supersedes_markers"]
    return (
        view.revision is None
        or type(source["world_id"]) is not str or _HEX32.fullmatch(source["world_id"]) is None
        or type(source["epoch"]) is not str or _HEX64.fullmatch(source["epoch"]) is None
        or not _ascending_strings(facet["selection"], None, nonempty=True)
        or type(pairs) is not list
        or any(type(p) is not list or len(p) != 2 or any(type(m) is not str or _HEX32.fullmatch(m) is None for m in p) for p in pairs)
        or [list(p) for p in sorted({tuple(p) for p in pairs})] != pairs
        or node.uid != marker_uid(facet["event_token"])
        or marker_address(view, destination) != revision.address
    )


def marker_consistent(node: Node) -> bool:
    """Recompute the marker's uid, address and id from its own event token,
    view and destination (spec §4); `False` on any difference or any rule failure."""
    if node.kind != MARKER_KIND or publication_content_malformed(node):
        return False
    facet = node.facets[stored.COORDINATION_FACET]
    view = CoordinationAddress.parse(facet["published_from"]["view"])
    destination = Destination.from_projection(facet["destination"])
    address = marker_address(view, destination)
    uid = marker_uid(facet["event_token"])
    return (
        node.uid == uid
        and coordination_revision(node).address == address
        and node.id == f"{MARKER_KIND}:{address.project}.{address.local}.{uid}"
    )
```
The pair list must be strictly ascending with no duplicates, and the marker branch checks its own uid and address, so a marker whose identity disagrees with its content is malformed at the rule and inconsistent at `marker_consistent`.

`_node` builds predecessor stubs only to hand `_coordination_node` their ids; it reads nothing else from them. If the executor finds `_coordination_node` reading more than `node.id` from a predecessor (`sed -n '/def _coordination_node/,/return node/p' src/beliefs/corpus.py`), pass the ids through a small local helper that builds the same `Relation` list instead.

- [ ] **Step 4: Run** `tests/test_publication.py` and `just test-fast`; expected green.

- [ ] **Step 5: Correct the spec's `published_from` row** — in §3's table, `` `{world_id, epoch, view, view_revision}`: 32-hex, 64-hex, canonical `coord:` address, 32-hex `` becomes `` `{world_id, epoch, view}`: 32-hex, 64-hex, canonical `coord:` address pinned to the view revision ``, and §4's `marker_record` signature drops `view_revision`; add a §16 line: "at planning (Task 4): the view revision is the pin on `published_from.view` and the intent's `view`, so no separate argument or field carries it."

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/src/beliefs/publication.py python/tests/test_publication.py docs/superpowers/specs/2026-09-22-publication-records-design.md tasks
git commit -m "feat(publication): deterministic marker and binding records, two addresses, self-contained marker check — Y2"
```

---

### Task 5: The judgment — `MomentSeam` and `standing_at`

**Files:**
- Modify: `python/src/beliefs/coordination.py` (the judgment), `python/src/beliefs/root.py` (`moment_seam`), `python/src/beliefs/corpus.py` (`CoordinationResolver.mounted`)
- Create: `python/tests/test_standing_at.py`

**Interfaces:**
- Consumes: Task 3's `Anchor`; Task 4's `publication_content_malformed`; `world/events.place`; `world/logmodel` views.
- Produces:

```python
PositionRefusalReason = Literal["mounts-changed", "anchor-unplaced", "chain-absent", "chain-malformed",
    "revision-missing", "revision-mismatch", "revision-malformed", "history-violated", "unregistered-revision"]

@dataclass(frozen=True)
class PositionRefused:
    reason: PositionRefusalReason
    detail: str

@dataclass(frozen=True)
class MomentSeam:
    inspect: Callable[[Path], ChainView]
    absent_state: object
    is_file: Callable[[object], bool]
    file_matches: Callable[[object, bytes], bool]

@dataclass(frozen=True)
class ChainBound:
    root: Path
    corpus_id: str
    view: WellFormedView
    head: int

def bounds(mounts: Mapping[Path, str], *, written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam) -> tuple[ChainBound, ...] | PositionRefused
def inventory(bound: ChainBound, prefix: str, seam: MomentSeam) -> dict[str, object] | PositionRefused
def present_records(bound: ChainBound, prefix: str, seam: MomentSeam) -> tuple[tuple[str, bytes], ...] | PositionRefused
def standing_at(mounts: Mapping[Path, str], address: CoordinationAddress, kind: str, *, written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam) -> tuple[CoordinationRevision, ...] | PositionRefused
```
`root.moment_seam() -> MomentSeam`; `CoordinationResolver.mounted() -> Mapping[Path, str]` (resolved root → `corpus_id`, from each mount's manifest, in the resolver's path order).

`present_records` is the shared half: every inventoried path's bytes, read and matched, plus the unaccounted-file classification. `standing_at` decodes those bytes as revisions of the address's kind; Task 6's orphan fold uses `present_records` over report paths.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_standing_at.py`, over a fake seam whose `inspect` returns hand-built `WellFormedView`s (reuse `tests/test_world_events.py`'s builders: `sed -n 1,40p tests/test_world_events.py` names `settlement`, `digest` and the genesis/registration builders) and whose states are plain tuples:

```python
from pathlib import Path

import pytest
from nodes.core.frontmatter import node_to_markdown

from beliefs.coordination import Anchor, MomentSeam, PositionRefused, standing_at
from beliefs.publication import binding_address, binding_record
from test_publish_intent import intent
from test_world_events import genesis, registered, settlement, digest  # the builders that file defines

ABSENT = ("absent",)


def file_state(data: bytes) -> tuple[str, bytes]:
    return ("file", data)


SEAM_BASE = dict(absent_state=ABSENT, is_file=lambda s: s[0] == "file", file_matches=lambda s, data: s == ("file", data))


def chain(*entries):
    """A WellFormedView over `entries` (genesis first)."""
    from beliefs.world.logmodel import WellFormedView

    return WellFormedView(genesis=entries[0], entries=tuple(entries), tip=entries[-1].digest, pending=())


def creation(tx: str, path: str, data: bytes, *, committed: bool = True):
    reg = registered(digest(f"reg-{tx}"), tx, initial=((path, ABSENT),), final=((path, file_state(data)),))
    return reg, settlement(digest(f"set-{tx}"), reg.digest, tx, committed=committed)
```

Then one test per row of spec §6's tables and each §11.1 bullet for `standing_at`: a first publication (empty inventory) → `()`; A then B superseding A, both committed before the bound → tips `(B,)`; B's file deleted → `revision-missing`; B's bytes replaced → `revision-mismatch`; B's bytes not a revision → `revision-malformed`; a committed registration moving B's path to `ABSENT` → `history-violated`; B's registration rolled back → tips `(A,)`, no refusal; B committed after the written root's position → tips `(A,)`; an other-root anchor whose head is before B's settlement → tips `(A,)`; an anchor naming another genesis → `anchor-unplaced`; a mount whose `inspect` answers `AbsentView()` → `chain-absent`, `MalformedView(...)` → `chain-malformed`; a mount set with an extra corpus → `mounts-changed`; a file at the address no registration creates → `unregistered-revision`; a file whose only creating registration is rolled back → not present, no refusal; the rolled-back-then-retried creation (two registrations, one rolled back, one committed) → present once. Build the revision bytes with `node_to_markdown(binding_record(intent(...), ...)).encode()` so each file is a real binding revision at `binding_address(VIEW, HERE)`; the fake root directory is `tmp_path / <name>`, and the test writes the bytes at the relative path the registration names.

- [ ] **Step 2: Run to see them fail.**

- [ ] **Step 3: Implement.** In `coordination.py` (imports: `Callable`, `Mapping`, `Sequence` from `collections.abc`; `Path`; `WellFormedView`, `RegisteredEntryView`, `SettledEntryView`, `AbsentView`, `MalformedView`, `ChainView` from `beliefs.world.logmodel`; `place` from `beliefs.world.events` — both are pure modules; import them inside the functions if a cycle appears at import time, and say so in a comment):

```python
def bounds(
    mounts: Mapping[Path, str], *, written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam
) -> tuple[ChainBound, ...] | PositionRefused:
    """Each mounted root's bound (spec §6): the written root's is the entry
    `position`; every other root's is its anchor's placement."""
    written = Path(written).resolve()
    by_corpus = {anchor.corpus_id: anchor for anchor in anchors}
    if written not in mounts or set(mounts.values()) != {mounts[written], *by_corpus} or mounts[written] in by_corpus:
        return PositionRefused("mounts-changed", "the mounted corpora are not the written root plus the anchored ones")
    found: list[ChainBound] = []
    for root, corpus_id in mounts.items():
        view = seam.inspect(root)
        if type(view) is AbsentView:
            return PositionRefused("chain-absent", str(root))
        if type(view) is MalformedView:
            return PositionRefused("chain-malformed", f"{root}: {view.defect.kind}")
        if root == written:
            heads = [index for index, entry in enumerate(view.entries) if entry.digest == position]
            if len(heads) != 1:
                return PositionRefused("anchor-unplaced", f"{root}: the position {position} is no entry of the chain")
            found.append(ChainBound(root, corpus_id, view, heads[0]))
            continue
        anchor = by_corpus[corpus_id]
        placement = place(view, genesis_digest=anchor.genesis, head_digest=anchor.head)
        if placement is None:
            return PositionRefused("anchor-unplaced", f"{root}: the anchor does not place in the live chain")
        found.append(ChainBound(root, corpus_id, view, placement.head))
    return tuple(found)


def _committed_in_order(view: WellFormedView, head: int) -> list[RegisteredEntryView]:
    """Committed registrations whose settlement is at or before `head`, in settlement order."""
    registrations = {entry.digest: entry for entry in view.entries if type(entry) is RegisteredEntryView}
    ordered: list[RegisteredEntryView] = []
    for index, entry in enumerate(view.entries[: head + 1]):
        if type(entry) is SettledEntryView and entry.committed and entry.registration in registrations:
            ordered.append(registrations[entry.registration])
    return ordered


def inventory(bound: ChainBound, prefix: str, seam: MomentSeam) -> dict[str, object] | PositionRefused:
    """Replay the committed registrations up to the bound over paths under `prefix` (spec §6)."""
    state: dict[str, object] = {}
    for registration in _committed_in_order(bound.view, bound.head):
        for path, post in registration.final:
            if not path.startswith(prefix):
                continue
            prior = state.get(path, seam.absent_state)
            if prior == seam.absent_state and post == seam.absent_state:
                continue
            if prior != seam.absent_state or not seam.is_file(post):
                return PositionRefused("history-violated", f"{bound.root}: {path} was removed or rewritten")
            state[path] = post
    return state


def _created_anywhere(view: WellFormedView, seam: MomentSeam) -> dict[str, list[tuple[object, bool | None]]]:
    settled = {entry.registration: entry.committed for entry in view.entries if type(entry) is SettledEntryView}
    created: dict[str, list[tuple[object, bool | None]]] = {}
    for entry in view.entries:
        if type(entry) is RegisteredEntryView:
            for path, post in entry.final:
                if seam.is_file(post):
                    created.setdefault(path, []).append((post, settled.get(entry.digest)))
    return created


def present_records(bound: ChainBound, prefix: str, seam: MomentSeam) -> tuple[tuple[str, bytes], ...] | PositionRefused:
    """Every inventoried path's bytes, read and matched; every unaccounted file classified."""
    expected = inventory(bound, prefix, seam)
    if type(expected) is PositionRefused:
        return expected
    found: list[tuple[str, bytes]] = []
    for path in sorted(expected):
        file = bound.root / path
        if not file.is_file():
            return PositionRefused("revision-missing", f"{bound.root}: {path}")
        data = file.read_bytes()
        if not seam.file_matches(expected[path], data):
            return PositionRefused("revision-mismatch", f"{bound.root}: {path}")
        found.append((path, data))
    directory, _, stem = prefix.rpartition("/")
    listed = sorted(
        f"{directory}/{candidate.name}" for candidate in (bound.root / directory).glob(f"{stem}*") if candidate.is_file()
    ) if (bound.root / directory).is_dir() else []
    unaccounted = [path for path in listed if path not in expected]
    if unaccounted:
        reread = seam.inspect(bound.root)
        if type(reread) is not WellFormedView:
            return PositionRefused("chain-malformed", f"{bound.root}: the re-read is not well-formed")
        created = _created_anywhere(reread, seam)
        for path in unaccounted:
            if path not in created:
                return PositionRefused("unregistered-revision", f"{bound.root}: {path}")
    return tuple(found)


def standing_at(
    mounts: Mapping[Path, str],
    address: CoordinationAddress,
    kind: str,
    *,
    written: Path,
    position: str,
    anchors: Sequence[Anchor],
    seam: MomentSeam,
) -> tuple[CoordinationRevision, ...] | PositionRefused:
    """The standing tips of `address` at the intent's position (spec §6): the
    family's one tip rule over the chain's inventory at each root's bound."""
    from nodes.core.frontmatter import node_from_bytes

    from beliefs.publication import publication_content_malformed

    found = bounds(mounts, written=written, position=position, anchors=anchors, seam=seam)
    if type(found) is PositionRefused:
        return found
    prefix = f"{kind}/{address.project}.{address.local}."
    by_uid: dict[str, CoordinationRevision] = {}
    for bound in found:
        records = present_records(bound, prefix, seam)
        if type(records) is PositionRefused:
            return records
        for path, data in records:
            try:
                node = node_from_bytes(data)
                revision = coordination_revision(node)
            except Exception:  # any decode failure of inventoried bytes is the one refusal below
                return PositionRefused("revision-malformed", f"{bound.root}: {path}")
            if node.kind != kind or revision.address != address or (kind in PUBLICATION_KINDS and publication_content_malformed(node)):
                return PositionRefused("revision-malformed", f"{bound.root}: {path}")
            prior = by_uid.get(node.uid)
            if prior is not None and prior.node != node:
                return PositionRefused("revision-mismatch", f"{node.uid}: unequal copies across mounts")
            by_uid[node.uid] = revision
    return standing_tips(tuple(by_uid.values()))
```
If `node_from_bytes`' exceptions are a closed set (`grep -n 'raise' $(uv run --frozen python -c "import nodes, os; print(os.path.dirname(nodes.__file__))")/core/frontmatter.py`), catch exactly those plus `MalformedRecord` instead of `Exception`, per the core rule against defensive catches.

`corpus.py` `CoordinationResolver`:

```python
    def mounted(self) -> Mapping[Path, str]:
        """Each mounted root and its corpus id, in the resolver's path order (publication-records design §6)."""
        from beliefs.world import load_manifest

        return MappingProxyType({root: load_manifest(root).corpus_id for root in self._mounts})
```

`root.py`, beside `log_seam()`:

```python
def _is_file_state(state: object) -> bool:
    return type(state) is FileState


def _file_matches(state: object, data: bytes) -> bool:
    return type(state) is FileState and state.content_hash == "sha256:" + sha256(data).hexdigest()


_MOMENT_SEAM = MomentSeam(
    inspect=_inspect_registered,
    absent_state=ABSENT,
    is_file=_is_file_state,
    file_matches=_file_matches,
)


def moment_seam() -> MomentSeam:
    """The production seam of the intent-position judgment (publication-records
    design §6): the engine's `FileState` comparison and `ABSENT`, as callables."""
    return _MOMENT_SEAM
```
(`FileState` from `atoms.core.fingerprint`, which `root.py` already imports from; `sha256` from `hashlib`; `_file_state` at `root.py:1094` spells the same `"sha256:"` prefix — use it: `state == _file_state(data)` would also compare mode and length, which a created file carries as `CREATED_FILE_MODE`; compare `content_hash` alone, since the mode is the engine's and the bytes are what the judgment reads.)

Add to `test_standing_at.py` one certified-volume test through `moment_seam()` over a real root: mint a binding through a raw `CorpusWriter._corpus.add`-free route is not available before Task 6, so this test uses an ordinary coordination kind (`task`) at an address, minted through `open_corpus(...).mint_coordination` and `revise_coordination` on a `durable_coordination_roots`-style pair, and asserts `standing_at(resolver.mounted(), address, "task", …)` equals the resolver's own `tips(address)` at the current tip (the judgment agrees with the live rule when nothing moved). The acceptance module (Task 7) exercises the binding kind durably.

- [ ] **Step 4: Run** — `tests/test_standing_at.py`, `tests/test_capability_boundary.py` (no `atoms` import outside `root.py`), `tests/test_arm_staleness.py`, `just test-fast`. Expected green.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/coordination.py python/src/beliefs/root.py python/src/beliefs/corpus.py python/tests/test_standing_at.py tasks
git commit -m "feat(coordination): standing_at over the chain's inventory, through the moment seam — W17"
```

---

### Task 6: The doors and the orphan fold — `beliefs/publication_doors.py`

**Files:**
- Create: `python/src/beliefs/publication_doors.py`, `python/tests/test_publication_doors.py`
- Modify: `python/src/beliefs/corpus.py` (`_append_operation_intent`), `python/src/beliefs/errors.py` (`PublicationRefused`), `python/tests/test_permit_boundary.py` (`WRITE_ENTRY_POINTS`), `python/tests/test_permit_entry_points.py` (`CASES`)

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces:

```python
PUBLISH_INSTRUMENT = "beliefs.publish"

@dataclass(frozen=True)
class OpenedPublication:
    intent: PublishIntent
    digest: str            # the intent entry's digest: its position in the written root

@dataclass(frozen=True)
class BindingOutcome:
    report: ActReport
    binding: Node | None   # present iff the outcome is BindingBound

def _open_publication(writer: CorpusWriter, resolver: CoordinationResolver, *, view: CoordinationAddress,
                      destination: Destination, clock: Callable[[], str], seam: MomentSeam,
                      port: OperationPort | None = None) -> OpenedPublication
def _bind_publication(writer: CorpusWriter, resolver: CoordinationResolver, opened: OpenedPublication, *,
                      corpus_id: str, marker: str, artifact: str, remotely_revealed: bool,
                      clock: Callable[[], str], seam: MomentSeam, port: OperationPort | None = None) -> BindingOutcome
def marker_tips_at(mounts: Mapping[Path, str], view: CoordinationAddress, destination: Destination, *,
                   written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam,
                   binding_tips: tuple[CoordinationRevision, ...]) -> tuple[tuple[str, str], ...] | PositionRefused
```
`errors.PublicationRefused(WriteRefused)` with `reason: str` and `tips: tuple[str, ...] = ()`.

The observer is the intent's actor and the instrument `PUBLISH_INSTRUMENT` — the spec names neither; one fixed instrument string is what the other boundary reports carry (cut 38's `audit` takes its instrument from the caller because an audit has several evaluators; publish has one).

- [ ] **Step 1: Write the failing tests** — `python/tests/test_publication_doors.py`, portable, over two writers on `tmp_path` roots with the v2 profile and a `RecordingPort`-style fake (reuse `tests/test_operation_writes.py`'s `RecordingPort`: `grep -n 'class RecordingPort' -A40 tests/test_operation_writes.py`) and a fake `MomentSeam` built from the recording port's appended entries. Where a portable chain view is too costly to fake faithfully, move the case to Task 7's durable module and keep here only what the fake port can show:
  - every pre-intent refusal appends nothing: a v1-pinned writer (`ValidationRefused`, "`publication-binding` is not declared by the mounted coordination contract"), a view that does not resolve (`PublicationRefused("view-unresolved")`), a divergent view (`PublicationRefused("divergent-view", tips=…)`), an authority without `publish` (`PermitExceeded`), a `PositionRefused` from the judgment (`PublicationRefused(<reason>)`);
  - the intent's bytes: `decode_publish_intent` of the appended payload equals `opened.intent`; anchors in `corpus_id` order; `binding_tips` empty for a first publication;
  - `_append_operation_intent(payload=…)` refuses a payload whose kind, token or actor disagrees with the arguments (`MalformedRecord`), and appends exactly the given bytes otherwise;
  - `_bind_publication` refuses an authority without `publish` before any effect.

- [ ] **Step 2: Run to see them fail.**

- [ ] **Step 3: Implement.** `corpus.py` `_append_operation_intent` gains a keyword and one branch; the existing lines stay (their spelling is pinned by cut 38's arms):

```python
    def _append_operation_intent(
        self, kind: str, token: str, intent_actor: str, *, port: OperationPort | None = None, payload: bytes | None = None
    ) -> str:
```
and replace the single line `digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))` with

```python
        encoded = _encode_operation_intent(kind, token, self.authority.actor) if payload is None else self._checked_domain_intent(kind, token, payload)
        digest = operation_port.append_intent(encoded)
```
and add

```python
    def _checked_domain_intent(self, kind: str, token: str, payload: bytes) -> bytes:
        """A pre-encoded domain intent (publication-records design §6 step 0): its
        kind, token and actor must be the ones this append is called with."""
        from beliefs.intents.publish import decode_publish_intent

        if kind != "publish":
            raise MalformedRecord("only the publish intent is pre-encoded")
        decoded = decode_publish_intent(payload)
        if (decoded.kind, decoded.event_token, decoded.actor) != (kind, token, self.authority.actor):
            raise MalformedRecord("the pre-encoded intent disagrees with its kind, token or actor")
        return payload
```
Check first with `grep -n "operation_port.append_intent(_encode_operation_intent" python/tests/n2_arms_cut*.py`: if a live arm pins that exact line, keep it and add the payload path as an `if payload is not None:` block above it that appends and returns early instead.

`errors.py`:

```python
class PublicationRefused(WriteRefused):
    """A publish door refused before its intent (publication-records design §6)."""

    def __init__(self, reason: str, *, tips: tuple[str, ...] = ()) -> None:
        super().__init__(reason)
        self.reason = reason
        self.tips = tips
```

`python/src/beliefs/publication_doors.py`:

```python
"""The publish doors (publication-records design §6): step 0 appends the
evidence-bearing intent; step 8 commits the binding revision with its report,
or the refusal report alone. Neither has a public route."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from nodes.core.frontmatter import node_from_bytes
from nodes.core.node import Node

from beliefs import boundary, stored
from beliefs.coordination import (
    Anchor,
    CoordinationAddress,
    CoordinationRefused,
    CoordinationRevision,
    MomentSeam,
    PositionRefused,
    bounds,
    present_records,
    standing_at,
)
from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import MalformedRecord, PublicationRefused, ValidationRefused
from beliefs.intents.publish import Destination, PublishIntent, decode_publish_intent, encode_publish_intent
from beliefs.permit import RequiredCapabilities
from beliefs.publication import BINDING_KIND, binding_address, binding_record
from beliefs.report import (
    ActReport,
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    PublicationBindingEntry,
)
from beliefs.runrecord import OperationPort
from beliefs.world.logmodel import AbsentView, IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView

PUBLISH_INSTRUMENT = "beliefs.publish"


@dataclass(frozen=True)
class OpenedPublication:
    intent: PublishIntent
    digest: str


@dataclass(frozen=True)
class BindingOutcome:
    report: ActReport
    binding: Node | None


def _require(writer: CorpusWriter) -> None:
    """The publication requirement (decision 7), checked before any effect."""
    permit = RequiredCapabilities.publishes().permit
    for family, kinds in (("publish", ("publication-binding",)), ("corpus-write", ("act-report",))):
        assert family in permit.act_families and set(kinds) <= permit.kinds
        writer.authority.require(family, kinds)


def _reports_at(bound, view: CoordinationAddress, destination: Destination, seam: MomentSeam):
    """Every publish intent for (view, destination) within the bound, with the
    report its committed fulfilment created, read and matched (spec §6)."""
    entries = bound.view.entries[: bound.head + 1]
    committed = {e.registration for e in entries if type(e) is SettledEntryView and e.committed}
    fulfilment = {e.fulfills: e for e in entries if type(e) is RegisteredEntryView and e.fulfills is not None and e.digest in committed}
    for entry in entries:
        if type(entry) is not IntentEntryView:
            continue
        try:
            intent = decode_publish_intent(entry.payload)
        except MalformedRecord:
            continue  # another shape's intent, or a malformed one: the audit's to report, not the fold's
        if intent.view.unpinned() != view.unpinned() or intent.destination != destination:
            continue
        registration = fulfilment.get(entry.digest)
        if registration is None:
            continue
        paths = [path for path, post in registration.final if path.startswith("act-report/") and seam.is_file(post)]
        if len(paths) != 1:
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: a publish fulfilment creates {len(paths)} reports")
            continue
        records = present_records(bound, paths[0], seam)
        if type(records) is PositionRefused:
            yield intent, records
            continue
        ((_, data),) = records
        facet = stored.act_report_facet(node_from_bytes(data))
        (row,) = facet["entries"]
        yield intent, row["outcome"]


def marker_tips_at(
    mounts: Mapping[Path, str], view: CoordinationAddress, destination: Destination, *,
    written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam,
    binding_tips: tuple[CoordinationRevision, ...],
) -> tuple[tuple[str, str], ...] | PositionRefused:
    found = bounds(mounts, written=written, position=position, anchors=anchors, seam=seam)
    if type(found) is PositionRefused:
        return found
    orphans: set[tuple[str, str]] = set()
    retired: set[tuple[str, str]] = set()
    for bound in found:
        for intent, outcome in _reports_at(bound, view, destination, seam):
            if type(outcome) is PositionRefused:
                return outcome
            shared = outcome["type"] == "bound" or outcome.get("remotely_revealed") is True
            if outcome["type"] != "bound" and outcome.get("remotely_revealed") is True:
                orphans.add((outcome["corpus_id"], outcome["marker"]))
            if shared:
                retired.update(intent.marker_tips)
    bound_markers = {
        (revision.node.facets[stored.COORDINATION_FACET]["corpus_id"], revision.node.facets[stored.COORDINATION_FACET]["marker"])
        for revision in binding_tips
    }
    return tuple(sorted(bound_markers | (orphans - retired)))
```
`present_records(bound, paths[0], seam)` treats the report's exact path as its own prefix: the inventory replays that one path, the file must be present and match, and the directory listing under `act-report/` with that stem finds only it. A report is create-only at a digest-named path (`stored.act_report_node`), so this is the same evidence rule as a revision's.

```python
def _judge(writer, resolver, opened: OpenedPublication, seam: MomentSeam):
    intent = opened.intent
    mounts = resolver.mounted()
    written = Path(writer.root).resolve()
    address = binding_address(intent.view, intent.destination)
    tips = standing_at(mounts, address, BINDING_KIND, written=written, position=opened.digest, anchors=intent.anchors, seam=seam)
    if type(tips) is PositionRefused:
        return tips, None
    markers = marker_tips_at(
        mounts, intent.view, intent.destination, written=written, position=opened.digest,
        anchors=intent.anchors, seam=seam, binding_tips=tips,
    )
    return tips, markers


def _open_publication(
    writer: CorpusWriter, resolver: CoordinationResolver, *, view: CoordinationAddress, destination: Destination,
    clock: Callable[[], str], seam: MomentSeam, port: OperationPort | None = None,
) -> OpenedPublication:
    _require(writer)
    profile = resolver.profile(writer.root)
    if profile is None or BINDING_KIND not in profile.coordination_kinds:
        raise ValidationRefused("publication-binding is not declared by the mounted coordination contract")
    with writer._operation:
        resolved = resolver.resolve(view.unpinned())
        if resolved is None:
            raise PublicationRefused("view-unresolved")
        if type(resolved) is CoordinationRefused:
            raise PublicationRefused("divergent-view", tips=resolved.tips)
        mounts = resolver.mounted()
        written = Path(writer.root).resolve()
        anchors: list[Anchor] = []
        for root, corpus_id in mounts.items():
            if root == written:
                continue
            chain = seam.inspect(root)
            if type(chain) is AbsentView:
                raise PublicationRefused("chain-absent")
            if type(chain) is not WellFormedView:
                raise PublicationRefused("chain-malformed")
            anchors.append(Anchor(corpus_id, chain.genesis.digest, chain.tip))
        anchors.sort(key=lambda anchor: anchor.corpus_id)
        own = seam.inspect(written)
        if type(own) is not WellFormedView:
            raise PublicationRefused("chain-absent" if type(own) is AbsentView else "chain-malformed")
        address = binding_address(view, destination)
        tips = standing_at(mounts, address, BINDING_KIND, written=written, position=own.tip, anchors=anchors, seam=seam)
        if type(tips) is PositionRefused:
            raise PublicationRefused(tips.reason)
        markers = marker_tips_at(
            mounts, view, destination, written=written, position=own.tip, anchors=anchors, seam=seam, binding_tips=tips,
        )
        if type(markers) is PositionRefused:
            raise PublicationRefused(markers.reason)
        token = secrets.token_hex(16)
        intent = PublishIntent(
            kind="publish", event_token=token, actor=writer.authority.actor, at=clock(),
            view=view.unpinned().pinned(resolved.uid), destination=destination,
            binding_tips=tuple(sorted(revision.node.uid for revision in tips)),
            marker_tips=markers, anchors=tuple(anchors),
        )
        digest = writer._append_operation_intent("publish", token, intent.actor, port=port, payload=encode_publish_intent(intent))
        return OpenedPublication(intent, digest)
```

```python
def _bind_publication(
    writer: CorpusWriter, resolver: CoordinationResolver, opened: OpenedPublication, *,
    corpus_id: str, marker: str, artifact: str, remotely_revealed: bool,
    clock: Callable[[], str], seam: MomentSeam, port: OperationPort | None = None,
) -> BindingOutcome:
    _require(writer)
    operation_port = writer._require_bound_port(port)
    intent = opened.intent
    subject = str(binding_address(intent.view, intent.destination))
    binding = binding_record(intent, corpus_id=corpus_id, marker=marker, artifact=artifact)
    writer._refuse_rendering(binding)
    closed_at = clock()

    def report_of(outcome) -> ActReport:
        return boundary._mint_publish_report(
            intent, observer=intent.actor, instrument=PUBLISH_INSTRUMENT, opened_at=intent.at,
            closed_at=closed_at, entry=PublicationBindingEntry(subject, outcome),
        )

    success = report_of(BindingBound(binding.uid, corpus_id, marker))
    plan = [writer._create_op(binding), writer._create_op(stored.act_report_node(success))]
    judged: dict[str, object] = {}

    def guard(_view) -> str | None:
        tips, markers = _judge(writer, resolver, opened, seam)
        if type(tips) is PositionRefused or type(markers) is PositionRefused:
            reason = tips.reason if type(tips) is PositionRefused else markers.reason
            judged["outcome"] = BindingEvidenceRefused(corpus_id, marker, remotely_revealed, reason)
        elif not set(intent.binding_tips) <= {revision.node.uid for revision in tips}:
            judged["outcome"] = BindingPredecessorNotStanding(
                corpus_id, marker, remotely_revealed, tuple(sorted(revision.node.uid for revision in tips))
            )
        elif tuple(sorted(r.node.uid for r in tips)) != intent.binding_tips or markers != intent.marker_tips:
            judged["outcome"] = BindingEvidenceRefused(corpus_id, marker, remotely_revealed, "tips-disagree")
        else:
            return None
        return type(judged["outcome"]).__name__

    def fallback(_reason: str):
        return [writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]

    writer._state.unresolved = True
    reason = operation_port.execute_fulfilling_guarded(plan, opened.digest, guard=guard, fallback=fallback)
    writer._reconstruct()
    if reason is None:
        return BindingOutcome(success, binding)
    return BindingOutcome(report_of(judged["outcome"]), None)
```
`execute_fulfilling_guarded` runs the guard under the written root's lock (`root.py:1039`); the guard reads other roots through the seam without their locks, bounded by the intent's anchors, which is the point of the anchors.

`test_permit_boundary.py` `WRITE_ENTRY_POINTS` gains `"publication_doors.py:_bind_publication": "publish",`. `test_permit_entry_points.py` gains a `Case`:

```python
    Case("publication_doors.py:_bind_publication", "publish", ("publication-binding", "act-report"), False, _prepare_publication, _bind_publication, _corpus_probe),
```
with `_prepare_publication` building a v2-profiled writer and resolver over `work / "corpus"` on `_prepare_corpus(port=True)`'s shape and opening a publication (`_open_publication` with a fixed clock and `moment_seam()` — the entry-point cases run on the certified volume like `_append_operation_intent`'s), and `_bind_publication` calling the door with fixed `corpus_id`, `marker`, `artifact` and `remotely_revealed=False`. Read `_prepare_corpus` and `_append_operation_intent`'s case first (`sed -n 240,330p tests/test_permit_entry_points.py`) and follow their state-dictionary pattern exactly.

- [ ] **Step 4: Run** — `tests/test_publication_doors.py`, `tests/test_permit_boundary.py`, `tests/test_permit_entry_points.py`, `tests/test_capability_boundary.py`, `tests/test_arm_staleness.py`, `just test-fast`. Expected green; the permit inventories closed in both directions.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/publication_doors.py python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(publication): the step-0 intent door, the step-8 binding door and the orphan fold — W17, Y4"
```

---

### Task 7: The acceptance module — real roots on the certified volume

**Files:**
- Create: `python/tests/acceptance/test_publication_records_acceptance.py`

**Interfaces:**
- Consumes: Tasks 1–6; `tests/acceptance/conftest.py`'s `work_directory`; `coordination_fixtures.content_for`, `raw_add`; `test_url_retrieval_acceptance.py`'s `intents` and `reduce` helpers (`sed -n 25,120p tests/acceptance/test_url_retrieval_acceptance.py`); `test_coordination_acceptance.py`'s W18 exclusion test for Y1-b's belief scenario (`grep -n 'belief_input_digest' tests/acceptance/test_coordination_acceptance.py`); Task 0's `ROLLBACK_MEANS` and `RETRY_AFTER_ROLLBACK`.
- Produces: thirteen test functions (twelve if W17-p-f is unrun) whose names Task 8's `UNIT_CHECKS` cites.

- [ ] **Step 1: Write the module.** Header, fixture and helpers:

```python
"""Conformance cut 39 — publication records (publication-records design §11.2).
Thirteen declaration units over real roots on the certified volume."""

from __future__ import annotations

import os
import shutil
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest
from authority import FULL
from atoms.coordinator import execute as engine_execute  # W17-p-f's rollback, as Task 0 pinned it
from coordination_fixtures import content_for, coordination_profile, raw_add
from nodes.core.frontmatter import node_to_markdown
from profiles import pins_for

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused, coordination_revision, standing_at
from beliefs.corpus import CoordinationResolver
from beliefs.errors import ImportRefused, KindNotMintedHere, PublicationRefused, ValidationRefused
from beliefs.intents.publish import Destination, decode_publish_intent
from beliefs.publication import BINDING_KIND, binding_address, binding_record, binding_uid, marker_record
from beliefs.publication_doors import _bind_publication, _open_publication
from beliefs.report import BindingBound, BindingEvidenceRefused, BindingPredecessorNotStanding
from beliefs.root import init_corpus_root, metadata_root_for, moment_seam, open_corpus

LOCAL = Destination.local("/srv/published/mm30")
REMOTE = Destination.remote("https://example.org/published/mm30")
_counter = count()


class Clock:
    """Advances one second on every read (Y2-a's sabotage is a clock read in the factory)."""

    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-22T00:00:{self.n:02d}Z"


@pytest.fixture()
def pair(work_directory, base_contract, monkeypatch):
    """Two v2-mounted roots whose path order is the reverse of their corpus-id order."""
    profile = coordination_profile(base_contract, version=2)
    stem = f"publication-{os.getpid()}-{next(_counter)}"
    roots = (work_directory / f"{stem}-a", work_directory / f"{stem}-b")
    ids = iter(("f" * 32, "0" * 32))
    try:
        for root in roots:
            init_corpus_root(root, authority=FULL)
            monkeypatch.setattr("beliefs.corpus.secrets", SimpleNamespace(token_hex=lambda _: next(ids)))
            open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
            monkeypatch.undo()
        resolver = CoordinationResolver(dict.fromkeys(roots, profile))
        writers = tuple(open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=profile) for root in roots)
        project = writers[0].mint_coordination("project", content=content_for("project"))
        yield SimpleNamespace(roots=roots, resolver=resolver, writers=writers, profile=profile,
                              view=coordination_revision(project).address)
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def publish(pair, side: int = 0, *, destination=LOCAL, remotely_revealed=False, resolver=None, clock=None, port=None):
    """Steps 0 and 8 back to back: the slice's whole source-root write."""
    resolver = resolver or pair.resolver
    clock = clock or Clock()
    writer = pair.writers[side]
    opened = _open_publication(writer, resolver, view=pair.view, destination=destination, clock=clock, seam=moment_seam(), port=port)
    outcome = _bind_publication(
        writer, resolver, opened, corpus_id="1" * 32, marker=opened.intent.event_token, artifact="2" * 64,
        remotely_revealed=remotely_revealed, clock=clock, seam=moment_seam(),
    )
    return opened, outcome


def tips(pair, destination=LOCAL) -> CoordinationRefused | object:
    return pair.resolver.resolve(binding_address(pair.view, destination))
```
(`monkeypatch.setattr("beliefs.corpus.secrets", …)` is how `test_w12…` in `test_coordination_acceptance.py` fixes minted ids; `adopt_manifest` mints the corpus id with `secrets.token_hex(16)` at `corpus.py:2254`. The marker uid argument is a stand-in 32-hex: no marker exists in this slice, and `_bind_publication` records what its caller names.)

Then the thirteen units — each asserts exactly its spec §11.2 row:

```python
def test_w17_p_a_a_second_writer_between_tip_read_and_append_is_refused_durably(pair):
    first, _ = publish(pair)                              # B1, a first publication
    inner = pair.writers[0]._operation_port

    class SecondWriter:
        """Stands in for a second process on the same root (decision 11): before
        the intent is appended, it commits a whole publish superseding B1."""

        root, profile, authority = inner.root, inner.profile, inner.authority
        fired = False

        def append_intent(self, payload):
            if not self.fired:
                self.fired = True
                publish(pair)                             # B3 supersedes B1, committed before this intent
            return inner.append_intent(payload)

        def __getattr__(self, name):
            return getattr(inner, name)

    opened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam(), port=SecondWriter())
    assert opened.intent.binding_tips == (binding_uid(first.intent.event_token),)
    outcome = _bind_publication(pair.writers[0], pair.resolver, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                                artifact="2" * 64, remotely_revealed=False, clock=Clock(), seam=moment_seam())
    (entry,) = outcome.report.entries
    assert type(entry.outcome) is BindingPredecessorNotStanding and outcome.binding is None
    assert not any(p.name.endswith(f"{binding_uid(opened.intent.event_token)}.md") for p in (pair.roots[0] / BINDING_KIND).iterdir())
    assert _closed_durably(pair.roots[0], opened)
```
`_closed_durably(root, opened)` reads the chain (`intents` and `reduce` from the URL-retrieval acceptance module) and asserts the intent at `opened.digest` qualifies `matched`/closed against its report. Write the helper above the tests. The `SecondWriter` wrapper is passed as `port=`; `_require_bound_port` compares `root`, `authority` and `profile`, which it forwards.

```python
def test_w17_p_b_a_supersession_after_the_intent_commits_a_lawful_sibling_durably(pair):
    publish(pair)                                         # B1
    opened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    publish(pair)                                         # B3 supersedes B1, after this intent
    outcome = _bind_publication(pair.writers[0], pair.resolver, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                                artifact="2" * 64, remotely_revealed=False, clock=Clock(), seam=moment_seam())
    assert type(outcome.report.entries[0].outcome) is BindingBound
    divergent = tips(pair)
    assert type(divergent) is CoordinationRefused and divergent.reason == "divergent-view" and len(divergent.tips) == 2
    publish(pair)                                         # the repair supersedes both
    assert tips(pair).kind == BINDING_KIND


def test_w17_p_c_a_revision_past_its_anchor_is_not_present_durably(pair):
    publish(pair, side=1)                                 # B1 in the other root
    opened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    _, later = publish(pair, side=1)                      # B3 in the other root, after the anchor
    decoded = decode_publish_intent(_payload_at(pair.roots[0], opened.digest))
    present = standing_at(pair.resolver.mounted(), binding_address(pair.view, LOCAL), BINDING_KIND,
                          written=pair.roots[0], position=opened.digest, anchors=decoded.anchors, seam=moment_seam())
    assert {r.node.uid for r in present} == set(opened.intent.binding_tips)
    assert later.binding.uid not in {r.node.uid for r in present}
    reopened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    assert later.binding.uid in reopened.intent.binding_tips


def test_w17_p_d_mount_order_moves_neither_anchors_nor_tips_durably(pair):
    publish(pair)
    forward = CoordinationResolver(dict(zip(pair.roots, (pair.profile,) * 2)))
    backward = CoordinationResolver(dict(zip(reversed(pair.roots), (pair.profile,) * 2)))
    first = _open_publication(pair.writers[0], forward, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    second = _open_publication(pair.writers[0], backward, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    assert (first.intent.binding_tips, first.intent.marker_tips) == (second.intent.binding_tips, second.intent.marker_tips)
    assert [a.corpus_id for a in first.intent.anchors] == sorted(a.corpus_id for a in first.intent.anchors)
    assert [a.corpus_id for a in first.intent.anchors] == ["0" * 32]          # the other root, whose path sorts last
    assert first.intent.anchors[0].corpus_id == second.intent.anchors[0].corpus_id
```
(`_payload_at(root, digest)` returns the `IntentEntryView.payload` at that digest from `log_seam().inspect_registered(root)`.)

W17-p-d's anchor order is by `corpus_id`: with ids `"f"*32` (path `-a`) and `"0"*32` (path `-b`), writing from `-a` anchors only `-b`. To make the sort observable, add a third root to this one test (mint it with id `"8"*32` under a path `-0` that sorts first), so the anchors are `("0"*32, "8"*32)` while the path order is `(-0, -b)` → ids `("8"*32, "0"*32)`; assert the intent carries `("0"*32, "8"*32)`.

```python
@pytest.mark.parametrize("damage", ["missing", "mismatch", "unregistered"])
def test_w17_p_e_the_chain_not_the_directory_says_which_revisions_exist_durably(pair, damage):
    publish(pair)                                         # A
    _, second = publish(pair)                             # B supersedes A
    path = pair.roots[0] / BINDING_KIND / f"{binding_address(pair.view, LOCAL).project}.{binding_address(pair.view, LOCAL).local}.{second.binding.uid}.md"
    if damage == "missing":
        path.unlink()
        expected = "revision-missing"
    elif damage == "mismatch":
        path.write_bytes(path.read_bytes() + b"\n")
        expected = "revision-mismatch"
    else:
        stray = binding_record(_intent_like(second), corpus_id="3" * 32, marker="4" * 32, artifact="5" * 64)
        raw_add(pair.roots[0], stray)
        expected = "unregistered-revision"
    with pytest.raises(PublicationRefused) as refused:
        _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    assert refused.value.reason == expected
```
(`_intent_like(outcome)` decodes the intent the outcome closed and returns it with a different `event_token` — `dataclasses.replace(intent, event_token="7" * 32)` — so the stray is a valid binding revision at the address that no registration created. The file may need `chmod u+w` before the rewrite: the engine creates records with `CREATED_FILE_MODE`; restore nothing — the fixture's roots are discarded.)

```python
def test_w17_p_f_a_rolled_back_creation_is_absent_and_its_retry_present_once_durably(pair, monkeypatch):
    publish(pair, side=1)                                 # B1 in the other root
    opened = _open_publication(pair.writers[1], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())

    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(engine_execute.create_file, "apply", failing)
    with pytest.raises(Exception):
        _bind_publication(pair.writers[1], pair.resolver, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                          artifact="2" * 64, remotely_revealed=False, clock=Clock(), seam=moment_seam())
    monkeypatch.undo()
    judged = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    assert len(judged.intent.binding_tips) == 1           # B1 alone: the rolled-back binding is not present, and nothing refused
    # RETRY_AFTER_ROLLBACK == "same intent": bind again under `opened`; otherwise publish afresh from side 1
    retried = _bind_publication(pair.writers[1], pair.resolver, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                                artifact="2" * 64, remotely_revealed=False, clock=Clock(), seam=moment_seam())
    again = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    assert again.intent.binding_tips == (retried.binding.uid,)
```
If Task 0 recorded `RETRY_AFTER_ROLLBACK = "fresh intent"`, replace the `retried = …` call with `_, retried = publish(pair, side=1)`. If `ROLLBACK_MEANS` is unrun, delete this test and W17-p-f from Task 8's declaration. Between the rollback and the retry, the arm also writes the would-be binding bytes raw at their path (`node_to_markdown(binding_record(opened.intent, …))` via `path.write_bytes`) and asserts the judgment from side 0 neither refuses nor counts it (classified by the rolled-back registration), then unlinks it before the retry — the "its file, if left" clause of spec §11.2.

```python
def test_y1_a_version_and_door_refusals_durably(work_directory, base_contract, pair):
    v1_profile = coordination_profile(base_contract, version=1)
    root = work_directory / f"publication-v1-{os.getpid()}-{next(_counter)}"
    try:
        init_corpus_root(root, authority=FULL)
        open_corpus(root, authority=FULL, profile=v1_profile).adopt_manifest(profile=pins_for(v1_profile))
        resolver = CoordinationResolver({root: v1_profile})
        writer = open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=v1_profile)
        project = writer.mint_coordination("project", content=content_for("project"))
        with pytest.raises(ValidationRefused):
            _open_publication(writer, resolver, view=coordination_revision(project).address, destination=LOCAL, clock=Clock(), seam=moment_seam())
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)
    writer = pair.writers[0]
    for kind in ("publication", "publication-binding"):
        with pytest.raises(KindNotMintedHere):
            writer.mint_coordination(kind, project=pair.view, content={})
    _, outcome = publish(pair)
    with pytest.raises(Exception):                        # the ordinary add refuses coordination kinds (_refuse_family_kinds)
        writer.add(outcome.binding)
    with pytest.raises(ImportRefused):
        writer.import_bundle([outcome.binding], observer="o", instrument="i", opened_at="2026-09-22T00:00:00Z", closed_at="2026-09-22T00:00:01Z")
```
Replace `pytest.raises(Exception)` for `add` with the exact type `_refuse_family_kinds` raises (`sed -n '/def _refuse_family_kinds/,/^    def /p' src/beliefs/corpus.py`).

```python
def test_y1_b_publication_records_are_inert_to_the_world_and_to_belief_durably(...):
    ...
```
Write Y1-b on `test_coordination_acceptance.py`'s W18 exclusion test's shape: the same belief scenario over a v2-profiled root; record the world-index maps and the answer's `belief_input_digest`; commit a binding through `publish(...)` and raw-add a `marker_record(...)`; assert the maps and the digest are unchanged.

```python
def test_y2_a_the_committed_binding_is_the_factory_of_its_decoded_intent_durably(pair):
    opened, outcome = publish(pair, clock=Clock())
    decoded = decode_publish_intent(_payload_at(pair.roots[0], opened.digest))
    rebuilt = binding_record(decoded, corpus_id="1" * 32, marker=opened.intent.event_token, artifact="2" * 64)
    on_disk = (pair.roots[0] / pair.writers[0]._relative_path(outcome.binding)).read_bytes()
    assert on_disk == node_to_markdown(rebuilt).encode("utf-8") == node_to_markdown(
        binding_record(decoded, corpus_id="1" * 32, marker=opened.intent.event_token, artifact="2" * 64)
    ).encode("utf-8")


def test_y3_a_the_audit_reads_publish_intents_by_their_domain_durably(pair):
    opened, _ = publish(pair)
    unclosed = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    port = pair.writers[0]._operation_port
    malformed = port.append_intent(b'{"domain":"science.publish-intent.v1","kind":"publish"}')
    bare = port.append_intent(b'{"actor":"actor","event_token":"' + b"c" * 32 + b'","kind":"publish"}')
    rows, findings = _reduced(pair.roots[0])
    assert rows[opened.digest] == "matched" and rows[unclosed.digest] != "matched"
    assert {f.ref for f in findings if f.code == "intent-payload-malformed"} >= {malformed, bare}
```
(`_reduced(root)` returns `{row.digest: row.reading}` and the findings from `reduce_chain` over the root's chain and records — the URL-retrieval module's `reduce` helper; adjust the attribute names to `IntentQualification`'s fields.)

```python
def test_y4_a_one_fulfilling_submission_each_way_and_no_binding_on_refusal_durably(pair):
    counted = _CountingPort(pair.writers[0]._operation_port)
    _, success = publish(pair, port=None)                 # through the writer's own port, counted by patching it:
    ...
```
Write Y4-a with `_CountingPort`, a forwarding wrapper counting `execute_fulfilling_guarded` calls, passed as `port=` to both doors: one success (count 1, binding on disk) and one refusal produced by binding with a resolver that mounts only the written root (`mounts-changed`: the intent anchored two) — count 1, the report's outcome `BindingEvidenceRefused`, and no binding file for that intent's uid.

```python
def test_y4_b_a_remotely_revealed_refusal_is_an_orphan_until_a_shared_publish_retires_it_durably(pair):
    one_root = CoordinationResolver({pair.roots[0]: pair.profile})
    opened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=REMOTE, clock=Clock(), seam=moment_seam())
    refused = _bind_publication(pair.writers[0], one_root, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                                artifact="2" * 64, remotely_revealed=True, clock=Clock(), seam=moment_seam())
    assert type(refused.report.entries[0].outcome) is BindingEvidenceRefused
    orphan = ("1" * 32, opened.intent.event_token)
    carrying, _ = publish(pair, destination=REMOTE)
    assert orphan in carrying.intent.marker_tips
    after = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=REMOTE, clock=Clock(), seam=moment_seam())
    assert orphan not in after.intent.marker_tips
    local = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=LOCAL, clock=Clock(), seam=moment_seam())
    _bind_publication(pair.writers[0], one_root, local, corpus_id="1" * 32, marker=local.intent.event_token,
                      artifact="2" * 64, remotely_revealed=False, clock=Clock(), seam=moment_seam())
    assert ("1" * 32, local.intent.event_token) not in publish(pair)[0].intent.marker_tips


def test_y4_c_a_lost_refusal_report_refuses_rather_than_dropping_the_orphan_durably(pair):
    one_root = CoordinationResolver({pair.roots[0]: pair.profile})
    opened = _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=REMOTE, clock=Clock(), seam=moment_seam())
    refused = _bind_publication(pair.writers[0], one_root, opened, corpus_id="1" * 32, marker=opened.intent.event_token,
                                artifact="2" * 64, remotely_revealed=True, clock=Clock(), seam=moment_seam())
    (pair.roots[0] / pair.writers[0]._relative_path(stored.act_report_node(refused.report))).unlink()
    with pytest.raises(PublicationRefused) as caught:
        _open_publication(pair.writers[0], pair.resolver, view=pair.view, destination=REMOTE, clock=Clock(), seam=moment_seam())
    assert caught.value.reason == "revision-missing"
```

- [ ] **Step 2: Run on the certified volume**

```bash
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut39-dev uv run --frozen pytest tests/acceptance/test_publication_records_acceptance.py -q -p no:cacheprovider
```
Expected: 13 passed (plus W17-p-e's three parametrized cases counted as one unit). Every failure here is a finding against Tasks 1–6, not a test to loosen: fix the source, or record the finding in the results record §7 and park if it needs a design change (`--reason decision`).

- [ ] **Step 3: Commit**

```bash
tasks check && git add python/tests/acceptance/test_publication_records_acceptance.py tasks
git commit -m "test(cut39): the publication-records acceptance module — W17, Y1–Y4"
```

---

### Task 8: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut39.py`, `python/tests/acceptance/n2_arms_cut39.py` (the re-export shim, cut 38's with `38` → `39`), `python/tests/acceptance/test_n2_cut39.py`, `python/tools/cut39_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit and body digest; Task 7's test names.
- Produces: `CUT39_ARMS` (13), `DECLARATION_UNITS` (13), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS`, `PHASE_MODULES`, `TOOLS`, `ACCEPTANCE`, `PYTHON_ROOT`, `declared_accounting`.

- [ ] **Step 1: The declaration** — `python/tests/n2_arms_cut39.py` on cut 38's shape (`sed -n 1,80p tests/n2_arms_cut38.py`). `DECLARATION_UNITS = ("W17-p-a", "W17-p-b", "W17-p-c", "W17-p-d", "W17-p-e", "W17-p-f", "Y1-a", "Y1-b", "Y2-a", "Y3-a", "Y4-a", "Y4-b", "Y4-c")` (drop `W17-p-f` if unrun); `_MODULE = "acceptance/test_publication_records_acceptance.py"`; `UNIT_CHECKS` maps each unit to its Task 7 function; `unit_of` is the identity (one arm per unit). Every `before` is copied **from the tree** after Task 7 (`grep -n` the site, copy the exact lines) and checked with `source.count(before) == 1`. The arms, one per unit (spec §11.3):

| arm | module | before (the site) | after |
|---|---|---|---|
| W17-p-a | `publication_doors.py` | the guard's `tips, markers = _judge(writer, resolver, opened, seam)` line | `tips, markers = tuple(SimpleNamespace(node=SimpleNamespace(uid=uid, facets={})) for uid in intent.binding_tips), intent.marker_tips` (trust the intent) |
| W17-p-b | `publication_doors.py` | `_judge`'s `standing_at(…, position=opened.digest, …)` call | the same call with `position=seam.inspect(written).tip` (judged at commit) |
| W17-p-c | `coordination.py` | `bounds`' `found.append(ChainBound(root, corpus_id, view, placement.head))` | `found.append(ChainBound(root, corpus_id, view, len(view.entries) - 1))` |
| W17-p-d | `publication_doors.py` | `anchors.sort(key=lambda anchor: anchor.corpus_id)` | `pass  # anchors left in mount-path order` |
| W17-p-e | `coordination.py` | `standing_at`'s `records = present_records(bound, prefix, seam)` and the two lines after it | the resolver's live read: `records = tuple((p.relative_to(bound.root).as_posix(), p.read_bytes()) for p in sorted((bound.root / kind).glob(f"{address.project}.{address.local}.*.md")))` |
| W17-p-f | `coordination.py` | `_committed_in_order`'s `if type(entry) is SettledEntryView and entry.committed and entry.registration in registrations:` | the same line without `and entry.committed` |
| Y1-a | `corpus.py` | `revise_coordination`'s two-line `KindNotMintedHere` guard, and `mint_coordination`'s | both removed (one arm; spell `before` over `mint_coordination`'s and let the check's second door assertion see `revise_coordination`'s) — if one `before` cannot cover both sites, remove `mint_coordination`'s only |
| Y1-b | `permit.py` or `corpus.py` | the site that keeps coordination kinds out of the world-index maps (`grep -n 'COORDINATION_KINDS\|WORLD_KINDS' src/beliefs/world/*.py src/beliefs/corpus.py`; choose the one Y1-b's assertion reaches) | that membership test widened to admit `publication-binding` |
| Y2-a | `publication.py` | `binding_record`'s `"at": intent.at,` | `"at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),` |
| Y3-a | `intents/shapes.py` | the three-line `if sniffed["domain"] == PUBLISH_INTENT_DOMAIN:` dispatch head | removed, so a publish payload falls to `intent-domain-unrecognized` |
| Y4-a | `publication_doors.py` | `fallback`'s `return [writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]` | `return [*plan, writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]` |
| Y4-b | `publication_doors.py` | `if outcome["type"] != "bound" and outcome.get("remotely_revealed") is True:` | `if outcome["type"] == "predecessor-not-standing" and outcome.get("remotely_revealed") is True:` |
| Y4-c | `publication_doors.py` | `_reports_at`'s `if type(records) is PositionRefused:\n            yield intent, records\n            continue` | `if type(records) is PositionRefused:\n            continue` |

Where a `before` is described rather than spelled, spell it at declaration time from the tree so that `source.count(before) == 1`, and make each `after` syntactically valid — run `python -c "import ast; ast.parse(open(p).read())"` over each sabotaged text through `n2_arms.py`'s own sabotage helper before pinning (the staleness probe's parse check, `beliefs-1b0827`, is not in the shared harness yet). The guard's `homed` assertion is `{unit: 1 for unit in DECLARATION_UNITS}`.

- [ ] **Step 2: The guard** — `python/tests/acceptance/test_n2_cut39.py`: copy `test_n2_cut38.py`, then: import `CUT38_ARMS` and add it to `PRIOR_ARMS`; add `"python/tests/n2_arms_cut38.py": "<sha>"` to `FROZEN_PRIOR_CUT_FILES` (`git log -1 --format=%h -- python/tests/n2_arms_cut38.py`); `FROZEN_CUT` → the cut-39 document; `CUT39_FREEZE_COMMIT` and `CUT39_FROZEN_SHA256` from Task 0 Step 7; `FROZEN_DECLARATION = "python/tests/n2_arms_cut39.py"` and `CUT39_DECLARATION_SHA256 = sha256sum` of it once final; the inventory test asserts the thirteen units and `len(CUT39_ARMS) == 13`; `test_every_acceptance_test_the_arms_name_exists` parses the acceptance module with `ast`, collects every `def test_*`, and asserts that the set of function names `UNIT_CHECKS` cites is a subset with exactly `len(DECLARATION_UNITS)` members; the freeze test asserts `"**13 declaration units**" in current` and `'("cut38_acceptance.py",)' in current`.

- [ ] **Step 3: The runner** — `python/tools/cut39_acceptance.py`: cut 38's with `cut=39`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut39"`, `PREFIX_RUNNERS = ("cut38_acceptance.py",)`, `PHASE_MODULES = ("test_publication_records_acceptance.py", "test_n2_cut39.py")`, `declared_accounting` asserting `rows == {"W17", "Y1", "Y2", "Y3", "Y4"}`, and on success:

```python
        print("guarantee rows exercised: 5 (5 newly closed: W17, Y1, Y2, Y3, Y4)", flush=True)
```
(with W17-p-f unrun: `"guarantee rows exercised: 5 (4 newly closed: Y1, Y2, Y3, Y4; W17 partial on its rollback arm)"`).

- [ ] **Step 4: The recent-cut row** — `python/tests/test_recent_cut_acceptance.py`: `import cut39_acceptance as cut39`; add `(cut39, 39, (13, 13, 5))` and id `"cut39"` to the parametrization; add

```python
    if cut == 39:
        assert "guarantee rows exercised: 5 (5 newly closed: W17, Y1, Y2, Y3, Y4)" in output
```

- [ ] **Step 5: Guard green, then the cut on the certified volume**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut39-dev uv run --frozen pytest tests/acceptance/test_n2_cut39.py -q -p no:cacheprovider -k "not fails_under_its_own_sabotage"
```
Expected green. Then the full N2 audit and the chained runner, detached:

```bash
cd ~/d/beliefs/.worktrees/publish/python && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 39); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut39-runner.log uv run --frozen python tools/cut39_acceptance.py > /dev/null 2>&1 &
sleep 2; echo "runner process group $(cat ~/d/beliefs/.work/acceptance/cut39-runner.log.pid)"
```
If the turn ends before the wrapper does, report that process-group id and `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut39-runner.log.pid)"` as the stop. Read the log when it exits; expected tail: three `[cut39 phase n/3]` lines, `declared arms: 13 (= 13 declaration units; 5 guarantee rows)`, the rows-exercised line, exit 0. Every arm `sound`; every check `resolved`. A `stale` verdict means a `before` no longer matches — fix the declaration, never the source.

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/tests/n2_arms_cut39.py python/tests/acceptance/n2_arms_cut39.py python/tests/acceptance/test_n2_cut39.py python/tools/cut39_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut39): N2 declarations, guard, runner and the recent-cut row — W17, Y1–Y4"
```

---

### Task 9: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §18)

- [ ] **Step 1: Run** — `export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30`; confirm `test -f "$SCIENCE_MM30_ROOT/state.json"`; read `rederived_belief` and `rederived_equal` and copy the file to the scratchpad. From `python/`: `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight` (must say `ok`; on a host-load refusal, `tasks park beliefs-d9ed0e "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`), then `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`. Nothing is recreated or moved aside: the base contract did not succeed (the coordination contract is not pinned by mm30's manifest). `grep -n 'publication\|publish\|coordination' python/tools/reproduction/*.py` shows what the driver reaches; expected nothing of this slice.

- [ ] **Step 2: Append §18** on §17's shape — `## 18. Addendum — publication records, <date>`: §18.1 what changed (the coordination contract's v1 and v2, the two kinds, the publish intent and the judgment; none reached by the driver — quote the grep and mm30's manifest pins, which name no coordination contract); §18.2 what the re-run reached — the same `NoBelief` payload as §17.2 (quote both), `rederived_equal: true`, `state.json` byte-identical (`diff` against the copy, both SHA-256s); §18.3 what this addendum does not claim (that mm30 publishes anything; the success criterion needs no publish).

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under publication records; nothing moves"
```

---

### Task 10: The results record, the re-rank, and the amendments

**Files:**
- Create: `docs/plans/<date>-conformance-cut-39-results.md`
- Modify: the cut document (`**Status:**` only), the spec (`**Status:**`), the ledger, the roadmap, `python/tools/roadmap_status.py`, `docs/designs/2026-08-31-coordination-and-view-kinds-design.md`, `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`, `docs/designs/2026-08-11-act-report-design.md`, `docs/designs/2026-09-22-publication-design.md` (status line), `docs/guide/foundations.md`, `docs/guide/open-questions.md`, `docs/guide/contracts-and-adoption.md`, `README.md`, tasks

- [ ] **Step 1: The results record** on cut 38's shape (`docs/plans/2026-09-22-conformance-cut-38-results.md`): §1 what ran (both summary lines verbatim from the runner log; the per-unit table); §2 accounting (W17 closed — or partial with W17-p-f unrun; Y1–Y4 closed; **193 of 220**, or 192); §3 evidence — the planning notes the spec carries (§16), deviations from the plan, every "read at freeze" choice, `ROLLBACK_MEANS` and `RETRY_AFTER_ROLLBACK`, the inventories checked in both directions (`WRITE_ENTRY_POINTS` gained `publication_doors.py:_bind_publication` with its `Case`; no other caller of a primitive), the corrections the cut document carries; §4 the reproduction (§18); §5 `## Remaining boundary` — must name `publish`'s remainder (the second slice, `beliefs-328507`: the request record, the selection snapshot, staging, export, reveal, the recovery table, transport, arrival) and L1 under `persistence-cut`; §6 main integration (filled at merge); §7 execution rulings.

- [ ] **Step 2: `roadmap_status.py`** — add `39: ("conformance-cut-39-results §2", "W17, Y1, Y2, Y3, Y4", ""),` after the cut-38 entry (with W17-p-f unrun: `"Y1, Y2, Y3, Y4", "W17"`). Regenerate Appendix A: `cd python && uv run --frozen python tools/roadmap_status.py`; expected `Closed 193 of 220; open 27.` (or `192 … 28`).

- [ ] **Step 3: Ledger and roadmap.** The ledger's `Current state`: a built bullet for the shipped coordination contract v1/v2, the publication kinds, the publish intent and the intent-position judgment; W17's text gains "closed <date> at cut 39 (`../plans/<date>-conformance-cut-39-results.md`): the intent-position arm judged over the chain's inventory"; Y1–Y4 closed; `publish` stays in the table with its remainder (the second slice); the summary names cut 39; the totals. The roadmap, rewritten whole: `**Ranked at:** cut 39, against the ledger's Current state (<date>)`; a `**Cut 39 (<date>) discharges publication records**` paragraph after cut 38's (the contract's v2 amendment and `composite`/`composes`; the two kinds and their deterministic records; the `publish` kind and family; the evidence-bearing intent and the chain-inventory judgment; W17 and Y1–Y4 close; the **eighth** off-path lane under rule 6, re-ranking nothing on the path — the first belief publishes nothing; `publish` stays off-path row 1 with its remainder, the second slice); the boundary index's `publish` row: rows "the governed publication act and its records' remaining rows (the second slice)"; the "current accounting" paragraph and one more sentence in the reproduction list ("cut 39 read it in place again and re-derived the same answer with `state.json` byte-identical — mm30's manifest pins no coordination contract"); Appendix A pasted; Appendix B updated. Then:

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```

- [ ] **Step 4: The design amendments** (spec §12):
  - Coordination design, beside §11.6: "> **Amended <date> (publication records, conformance cut 39 — `../superpowers/specs/2026-09-22-publication-records-design.md`):** the intent-position rule's evidence landed with `publish`. The intent carries the frozen tips and one anchor per mounted root other than the written root, and presence at the position is the chain's inventory at each root's bound (committed registrations only; every inventoried revision read and matched; removals refused; unaccounted files classified by a chain re-read under the engine's write-ahead order). W17-p replaces the constructed-prefix arm, and W17 closes. `predecessor-not-standing` is reachable only across processes — the detection of a broken single-writer obligation (ledger row 4)."
  - Layer design §6.1: the four notes spec §12 lists (step 0's tips and the narrowed "cannot be reconstructed" sentence; the marker's facet fields and the two addresses; step 8's orphan fields and retirement; §4.1 citing this slice), each as a dated `> **Amended …**` note at the sentence it qualifies.
  - Act-report design §2 and §6 item 3: "> **Amended <date> (publication records, cut 39):** the operation-kind enum gains `publish` (nine), which opens only through its domain intent `science.publish-intent.v1`; its one entry kind is `publication-binding`, with outcomes `bound`, `predecessor-not-standing` and `evidence-refused`, every refusal carrying `corpus_id`, `marker` and `remotely_revealed`. The lifecycle entries arrive with the publish act."
  - `docs/guide/foundations.md` where it states the intent-position rule: the chain-inventory evidence in one sentence and the citation.
  - `docs/designs/2026-09-22-publication-design.md`: status line "Y1–Y4 closed at cut 39".

- [ ] **Step 5: Guide, README, status lines, tasks** — `docs/guide/contracts-and-adoption.md`: the cut-39 line as discharged, the cut count, totals, the results-record link; `README.md`: "through **cut 39**", the table row's wording ("the discharged publication-records cut…"), "The latest discharged boundary is cut 39". The cut document's Status: `discharged <date> on the certified volume; results: ../plans/<date>-conformance-cut-39-results.md`. The spec's Status: `discharged at conformance cut 39 on <date>; results: ../../plans/<date>-conformance-cut-39-results.md`.

```bash
tasks done beliefs-d477a1 "results record, re-rank at cut 39, amendments"
tasks done beliefs-c80d8c "composite and composes entered the coordination query vocabulary in contract v2 (cut 39)"
tasks check
git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut39): results record, re-rank at cut 39, W17 and Y1–Y4 closed"
```

---

### Task 11: Final review, gate, merge

- [ ] **Step 1: Whole-branch review** — `superpowers:requesting-code-review` over `git diff main...HEAD`, against the spec's decisions (the Global Constraints' "Decisions the code must honour" bullet) and the cut document's §5 table. Land fixes as their own commits; record each in the results record §3.2.

- [ ] **Step 2: The gate**, detached:

```bash
cd ~/d/beliefs/.worktrees/publish && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 39); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut39-gate.log just gate > /dev/null 2>&1 &
sleep 2; echo "gate process group $(cat ~/d/beliefs/.work/acceptance/cut39-gate.log.pid)"
```
If the turn ends before the wrapper does, report that process-group id and `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut39-gate.log.pid)"` as the stop. Read the log at exit; expected the pytest summary line with zero failures (memory `pytest-count-claims-need-the-summary-line`) and the TypeScript suite green.

- [ ] **Step 3: Close and merge**

```bash
tasks done beliefs-fc5063 "final review, gate green, merged"
tasks done beliefs-d7d7d1 "cut 39 discharged: W17 and Y1–Y4 — the coordination contract's v2 amendment, the publish intent and the intent-position judgment over the chain's inventory"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-d7d7d1 — cut 39 discharged"
cd ~/d/beliefs && git merge --no-ff design/publish -m "merge: publication records — conformance cut 39"
```
`beliefs-1a5157` stays open: the second slice (`beliefs-328507`) is its remainder. Fill the results record's §6 (the merge commit, `just check` on merged `main`) in a `docs(cut39): record merged-main verification` commit. The worktree stays for the second slice (roadmap concurrency rule 4: a lane holds one worktree); do not remove it.

---

## Self-review

**Spec coverage.** §1 → Task 0 (the cut) and the file map; §2 decisions 1 → the split itself (Task 11 leaves `beliefs-1a5157` open for `beliefs-328507`); 2 → Task 1; 3 → Tasks 3 and 6; 4 → Tasks 0 (the engine order), 5 and 7 (W17-p-e, W17-p-f); 5 → Task 4; 6 → Tasks 1 (the doors refuse) and 4 (the factory); 7 → Task 1; 8 → Task 2; 9 → Task 3 (`Destination`); 10 → Task 2; 11 → Task 7 (W17-p-a's second writer). §3 → Tasks 1 and 4; §4 → Task 4; §5 → Task 3; §6 → Tasks 5 and 6; §7 → Task 2; §8 → the staleness and existing-suite runs in Tasks 1–6 (the planning note amends §8's `completion` clause); §9 → the file map; §10 → Tasks 0 (banking) and 10 (closing); §11.1 → Tasks 1–6; §11.2 → Task 7; §11.3–11.4 → Task 8; §12 → Task 10; §13 → Task 0 Step 7 and Task 10 Step 5; §14 → the cut document §7; §15 → nothing to file.

**Placeholders.** Every code step carries its body. Four places defer a spelling to the tree by instruction, each with the grep that settles it: the N2 `before` strings (as cut 38's plan did), `_refuse_family_kinds`' exception type, the entry-point `Case`'s prepare helper, and Y1-b's belief scenario (cut 14's W18 test is the template). Three listings that a first draft shortened (the marker pairs' ordering, the chain-view identity checks in `_open_publication`, W17-p-a's first assertion) were written out in full at self-review.

**Type consistency.** `Anchor(corpus_id, genesis, head)`; `Destination(type, locator)`, `.local`, `.remote`, `.projection`, `.from_projection`; `PublishIntent(kind, event_token, actor, at, view, destination, binding_tips, marker_tips, anchors)`; `encode_publish_intent(intent) -> bytes`, `decode_publish_intent(payload) -> PublishIntent`; `binding_address`/`marker_address(view, destination) -> CoordinationAddress`; `binding_uid`/`marker_uid(event_token) -> str`; `binding_record(intent, *, corpus_id, marker, artifact) -> Node`; `marker_record(intent, *, world_id, epoch, selection) -> Node`; `publication_content_malformed(node) -> bool`; `marker_consistent(node) -> bool`; `MomentSeam(inspect, absent_state, is_file, file_matches)`; `PositionRefused(reason, detail)`; `ChainBound(root, corpus_id, view, head)`; `bounds(mounts, *, written, position, anchors, seam)`; `inventory(bound, prefix, seam)`; `present_records(bound, prefix, seam)`; `standing_at(mounts, address, kind, *, written, position, anchors, seam)`; `CoordinationResolver.mounted() -> Mapping[Path, str]`; `moment_seam() -> MomentSeam`; `OpenedPublication(intent, digest)`; `BindingOutcome(report, binding)`; `_open_publication(writer, resolver, *, view, destination, clock, seam, port=None)`; `_bind_publication(writer, resolver, opened, *, corpus_id, marker, artifact, remotely_revealed, clock, seam, port=None)`; `marker_tips_at(mounts, view, destination, *, written, position, anchors, seam, binding_tips)`; `PublicationBindingEntry(subject, outcome)`; `BindingBound(binding, corpus_id, marker)`; `BindingPredecessorNotStanding(corpus_id, marker, remotely_revealed, tips)`; `BindingEvidenceRefused(corpus_id, marker, remotely_revealed, reason)`; `boundary._mint_publish_report(intent, *, observer, instrument, opened_at, closed_at, entry)`; `KindNotMintedHere`, `PublicationRefused(reason, *, tips=())` under `WriteRefused`; `shipped_coordination(version=2)`; `KERNEL_REQUIREMENTS`; `RequiredCapabilities.publishes()`. The spec's `standing_at(resolver, address, *, …, moments)` became `standing_at(mounts, address, kind, *, …, seam)` — the resolver contributes only its mount map, and the kind is explicit (recorded in the spec's planning note, Task 0 Step 6).

## Plan review log

- 2026-09-22 — drafted. Found at planning and resolved: `completion` refused a `PublishIntent` (the spec said it was unchanged); the Y table needs an owner under `docs/designs/` (`TABLE_OWNERS`), banked as `2026-09-22-publication-design.md` at the freeze; `marker_record` loses `view_revision` (the view pin carries it); the engine's write-ahead order (`atoms` `coordinator/execute.py:171` then `:183`) and a durable rollback (`create_file.apply` patched, atoms' own technique) are pinned in Task 0 before anything relies on them.
