# Publish Act, Remote — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the remote half of the publish act: the transport seam the act verifies, the durable transport mark, step 7 with its export evaluation, the orphan-carrying `transport-incomplete`, Ruling 12's `publish-unfinished`, the remote recovery rows, and the recipient's `publication_tip`. Discharge Y11–Y16 as conformance cut 42.

**Architecture:**
- `beliefs/transport.py` is the seam: a `Transport` protocol, the file naming, the local listing and its identity. `tests/transport_fake.py` is its directory-backed double.
- `report.py` gains the `publication-transport` entry and the remote lifecycle. `publication_doors.py`'s fold reads a `transport-incomplete` refusal as an orphan that retires nothing, and it gains `unfinished_attempts`.
- `publish_request.py` gains the mark codec and the remote branch of `require_usable`.
- `publish.py` runs steps 1–6 into `<op>/export`, writes the mark, then runs steps 7–9 over a `_Remote` that holds the mark and never the request. `root.py` gains `evaluate_copy`, which is `restore_root`'s evaluation without its grant.
- `publication_arrival.py` shares the arrival layout rule with `publication_tip`, which reads each held root alone.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, `nodes` records, the acceptance harness under `python/tests/acceptance/` and the N2 audit.

**Spec:** `docs/superpowers/specs/2026-09-26-publish-act-remote-design.md`, approved 2026-09-27 at `e353c2d` after three user reviews (its §16). Read it first. Every task cites its sections and decisions.

## Global Constraints

- **Baseline is `design/publish` at `c95b7c2`**, whose merge-base with `main` is `a38d6ff`. Work in `.worktrees/publish`, branch `design/publish`, which is locked "on WORK_ROOT storage".
  - `main` has moved since `a38d6ff` by docs and task commits only. Task 0 Step 1 checks that `git diff --stat a38d6ff main -- python` is empty. The lane merges `main` only at Task 11.
  - Paths below are relative to the repository root. Paths shown to the user carry the `.worktrees/publish/` prefix. The main checkout is `~/d/beliefs`.
  - Run pytest from the canonical path (`cd "$(pwd -P)"`). `ELOOP` from `open_root` means the `.worktrees` symlink is in the cwd (memory `run-pytest-from-the-canonical-worktree-path`). `tools/checkout.py` resolves the cut roots, so no `SCIENCE_CUT*_ROOT` export is needed except for a standalone cut-10 run (memory `worktree-on-work-root-needs-cut-root-exports`).
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  - For this lane, `transport.py`, `publish.py`, `publish_request.py`, `publication_doors.py` and `publication_arrival.py` import nothing of `atoms`. `evaluate_copy` lives in `root.py`, beside `restore_root`.
  - The lane adds **no new caller of a write primitive**:
    - the mark is a `durable.py` write outside every root;
    - `_refuse_publication` and `_bind_publication` are existing entries;
    - `evaluate_copy`'s grant does nothing, unlike `restore_root.grant`.

    Task 5 runs `test_permit_boundary.py`, `test_permit_entry_points.py` and `test_capability_boundary.py` green. If either inventory reports a new caller, it joins `WRITE_ENTRY_POINTS` with a `Case`, and the planning note records it.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. Here that is Task 8, Step 4, with `(cut42, 42, (14, 14, 6))`.
- **The declared accounting is 14 arms, 14 declaration units and 6 rows (Y11–Y16)**, unless Task 0's engine probes refuse a fact an arm relies on. In that case:
  - the arm is declared unrun;
  - the row is reported **partial**;
  - the cut document freezes the reduced counts (memory `cut-classification-any-unrun-arm-is-partial`).

  Every later mention of the accounting reads the frozen cut document's §4.
- **Frozen declarations and cut bodies stay byte-exact.** Cut 42 chains **cut 41's** runner (`PREFIX_RUNNERS = ("cut41_acceptance.py",)`). The live arms of cuts 39 and 40 pin lines in the modules this lane edits, and every edit must leave each of these occurring **exactly once in its module**:
  - `publish.py`:
    - `    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)` (Y6-a)
    - `    if snapshot.identity() != request.selection or snapshot.event_token != intent.event_token:` (Y6-b)
    - `    return _Population(n, complete=False)` (Y7-a) and `    if extras:` (Y7-b)
    - `    return Path(a.request.destination.locator) / corpus_id` (Y8-a). The remote branch goes *before* it, in the same function.
    - `        write_create_only(sibling, artifact)` (Y8-b)
    - `        lifecycle=entries,` (Y9-a)
    - `        return PublishUnresolved(event_token, "binding-without-report")` (Y9-b)
    - `        if reading is not None and reading.reading == "unfinished":` (Y9-c)
    - `        _discard(op)` (Y9-d). No new call is spelled with this indentation and name; step 9 of the remote act is `    _discard(r.op)`.
  - `publication_doors.py`: cut 39's seven lines (`_judge`'s call, the `standing_at` line in `_judge`, `anchors.sort`, the `binding_record` line, the fallback's `return`, the `remotely_revealed` orphan line, the `PositionRefused` three-liner), plus cut 40's `        if expected_view is not None and view.unpinned().pinned(resolved.uid) != expected_view:` (Y5-b) and `        if type(entries[-1]) is not PublicationBindingEntry:\n            yield intent, PreBinding(` (Y9-e).
  - `publication_arrival.py`: `    if not markers:\n        raise PublicationArrivalRefused("marker-absent")` (Y10-a) and `    if held != selection:` (Y10-b). Both move, unchanged and at the same indentation, into `require_publication_layout` (Task 6).
  - `publish_request.py`: `            for endpoint in (relation.source, relation.target):` (Y5-a).
  - Tasks 2, 3, 4, 5 and 6 end by running `tests/test_arm_staleness.py`. A stale prior arm means an edit moved a pinned line: restore its spelling and put the new code beside it. Never edit a prior declaration (memory `staleness-probe-baseline-is-the-trees-output`).
- **Decisions the code must honour verbatim** (spec §2):
  1. transport is an injected seam, and the act computes the local listing and decides "verified complete" by comparing the two listings;
  2. the mark is written create-only after step 6 validates and before the first `push`;
  3. the orphan rule is asymmetric: a possibly shared marker creates an orphan, and only a certainly shared one retires orphans;
  4. `transport-incomplete` (`abandoned`, `listing-mismatch`, `export-damaged`) is a terminal refusal carrying `(corpus_id, marker)`, and an exception from the seam leaves the attempt `unfinished`;
  5. after the mark, a retry resumes at step 7 from the mark alone:
     - the mark is checked for **identity** against its intent, the export's manifest, its sibling and chain head, and its one marker file by name, and failing that it is `PublishUnresolved("transport-mark-corrupt")`;
     - no record's **content** is read before the export evaluates `validated`: a damaged selected record closes the attempt `export-damaged`, never `transport-mark-corrupt` (plan review, round 1);
     - the marker's content (its shape and its selection count) is checked only after that evaluation;
     - step 7 evaluates the export before every `push`;
  6. step 0 refuses `publish-unfinished` for an `unfinished` attempt with a mark on the same `(view, destination)`;
  7. the remote export root is `<op>/export/<corpus_id>`, and its sibling is `<op>/export/<corpus_id>.head-artifact.v1`;
  8. step 9 keeps the export root, the mark, the request and the snapshot;
  9. `publication_tip` reads each held root alone, with the family's one tip rule;
  10. the recipient's intake is `restore_root` then `admit_publication`, and there is no new door.
- **Long runs are harness-tracked** (Processes rule; plan review, round 1). Run the cut runner and the gate through the Bash tool with `run_in_background: true`, piping through `tee` into a log under `~/d/beliefs/.work/acceptance/`. The harness starts the session's next turn when the process exits, and the session reads the log then. Never detach with `setsid nohup`, `&` or the `detached.sh` wrapper: the harness does not track those, and no turn ends waiting on one. Before the end-of-turn report, `host-load --section session` lists what the session left running.
- **Commits:**
  - Use conventional commits with no attribution trailers.
  - Run `tasks check` before every commit.
  - Use `just test-fast` while working. Never run the full suite after every edit (AGENTS.md).
  - Run every `pytest` from `python/` with `uv run --frozen`.
  - Make no TypeScript changes, and leave both `CONTRACT.yaml` copies of the base contract unchanged.

## Review Focus

These are the inputs a person meets that the spec's arms do not pin. Each line names the test that pins it and the task that owns it.

1. **Two spellings of one remote URL** (a trailing path slash aside, different case in the scheme and host). A person expects them to name one destination, so that `publish-unfinished`, the binding address and supersession agree. `Destination.remote` canonicalizes. Pinned by `test_equivalent_remote_spellings_are_one_destination` in Task 1.
2. **An adapter whose `listing` returns digests in upper case, or omits the sibling.** A person expects anything but an exact match to be refused, never taken as verified. Pinned by `test_a_listing_that_is_not_exact_is_listing_mismatch` in Task 5.
3. **A remote whose `push` raises on every retry**: an adapter that never abandons. A person expects each resume to propagate the error and write nothing. The attempt stays `unfinished`, and the destination stays blocked until the adapter abandons or succeeds (spec decision 4). Pinned by `test_a_push_that_always_raises_writes_nothing_and_keeps_blocking_durably` in Task 7.
4. **An unfinished attempt for another view on the same remote destination.** A person expects it not to block this view's publish, since the check is per `(view, destination)`. Pinned by `test_unfinished_attempts_are_per_view_and_destination` in Task 3.
5. **A recipient that names one held root twice, by path and through a symlink.** A person expects a plain error, not a doubled marker read as `marker-duplicated`. Pinned by `test_a_root_named_twice_is_a_value_error` in Task 6.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-09-22-publication-design.md` | Y11–Y16 appended (Task 0) |
| `docs/designs/<freeze date>-conformance-cut-42.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py`, the ledger, the roadmap | freeze and totals: 237 rows (Task 0) |
| `python/tests/test_publish_remote_engine.py` (new) | the engine facts the act relies on (Task 0) |
| `python/src/beliefs/transport.py` (new), `python/tests/transport_fake.py` (new), `python/tests/test_transport.py` (new) | the seam, the naming, the listings, the fake (Task 1) |
| `python/src/beliefs/report.py`, `python/src/beliefs/stored.py`, `python/tests/test_report.py` | the transport entry, its outcomes, the remote lifecycle (Task 2) |
| `python/src/beliefs/publication_doors.py`, `python/src/beliefs/errors.py`, `python/tests/test_publication_doors.py` | `PreBinding.orphan`, the transport rule, the fold, `unfinished_attempts`, `PublicationRefused(tokens=)` (Task 3) |
| `python/src/beliefs/publish_request.py`, `python/src/beliefs/publish.py` (one line), `python/tests/test_publish_request.py` | the mark codec, the remote `require_usable` (Task 4) |
| `python/src/beliefs/publish.py`, `python/src/beliefs/root.py`, `python/tests/test_publish.py` | the remote act and `evaluate_copy` (Task 5) |
| `python/src/beliefs/publication_arrival.py`, `python/src/beliefs/errors.py`, `python/tests/test_publication_arrival.py` | `require_publication_layout`, `publication_tip`, `PublicationReadingRefused` (Task 6) |
| `python/tests/acceptance/test_publish_remote_acceptance.py` (new) | the fourteen units (Task 7) |
| `python/tests/n2_arms_cut42.py`, `python/tests/acceptance/n2_arms_cut42.py`, `python/tests/acceptance/test_n2_cut42.py`, `python/tools/cut42_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, recent-cut row (Task 8) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | §21 (Task 9) |
| `docs/plans/<date>-conformance-cut-42-results.md` (new) and the amended documents | discharge (Task 10) |

---

### Task 0: Freeze cut 42, bank Y11–Y16, pin the engine facts

**Files:**
- Create: `docs/designs/<freeze date>-conformance-cut-42.md`, `python/tests/test_publish_remote_engine.py`
- Modify: `docs/designs/2026-09-22-publication-design.md`, `python/tests/test_designs_corpus.py`, `README.md`, `docs/guide/contracts-and-adoption.md`, the ledger, the roadmap (through `python/tools/roadmap_status.py`), the spec (planning notes), tasks through the CLI

**Interfaces:**
- Produces:
  - the frozen cut body the guard pins (Task 8 reads its freeze commit and digest);
  - the engine verdicts `EXPORT_LAYOUT`, `CHAIN_HEAD_SERVICEABLE`, `EVALUATE_INTACT`, `EVALUATE_DELETED`, `EVALUATE_ALTERED`, `EVALUATE_WRITES_NOTHING` and `DAMAGE_WRITABLE`, each `"holds"` or a refusal text;
  - `EVALUATE_UNREADABLE` and `EVALUATE_UNDECODABLE`, each either the outcome the evaluation answers or the exception type it raises;
  - `CHAIN_HEAD_DAMAGED`, `CHAIN_HEAD_DELETED` and `CHAIN_HEAD_UNREADABLE`, the exception types the chain head raises over a damaged, deleted and unreadable chain directory, and `EVALUATE_CHAIN_DELETED`, what the evaluation does over a deleted one. Task 5's `root.py` translations catch exactly the types these name (plan review, round 2: a deleted or unreadable chain raises `PreconditionRefused`);
  - `CHAIN_DIR`, the name of the chain directory at the export root's top level, which Task 8's Y16-a sabotage uses.

- [ ] **Step 1: Confirm the baseline and that cut 42 is unclaimed**

```bash
cd ~/d/beliefs
git diff --stat a38d6ff main -- python    # expected: empty
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -q "conformance-cut-4[2-9]" && echo "claimed on $b"; done; echo scan done
git worktree list
```
Expected: an empty diff, then `scan done` alone (memory `cut-number-check-scans-every-worktree`). The worktrees are `main`, `.worktrees/publish` and `.worktrees/session-mounts`; the last holds a spec, not a cut document. If the diff is not empty, merge `main` into `design/publish` first (`git merge --no-ff main`), then rerun `just test-fast`.

- [ ] **Step 2: Pin the engine facts** in `python/tests/test_publish_remote_engine.py`. Step 7's evaluation (spec §4.3) and the resume's mark checks (§4.2) rely on these facts, so these tests pin them from beliefs' side, on the certified volume. The evaluation is probed through `_restore_root` with a grant that does nothing, which is what Task 5's `evaluate_copy` wraps. Tests may import private names and `atoms`; source modules may not.

```python
"""The engine facts the remote publish act relies on (publish-act-remote design
§4.2, §4.3; plan Task 0): a serviceable export root is plain files, its chain
head reads, and restore's evaluation, granting nothing, validates it intact and
refuses it with a selected record deleted or altered, writing nothing."""

from __future__ import annotations

import os
import shutil
import stat
from itertools import count
from pathlib import Path

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from profiles import pins_for

from beliefs import stored
from beliefs.root import (
    LifecycleState,
    _log_seam,
    chain_head_reader,
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
from beliefs.world.anchors import CorpusSubject, decode_head_artifact
from beliefs.world.registry import load_manifest
from beliefs.world.verify import ArtifactCarrier, ObserverSet, _restore_root

V2 = coordination_profile(None, version=2)
_counter = count()


def _grant_nothing(_root: Path) -> None:
    """The evaluation's grant: none."""


def writable(root: Path) -> None:
    """Lift write permission on a serviceable root's tree (DAMAGE_WRITABLE)."""
    for path in (root, *root.rglob("*")):
        if not path.is_symlink():
            os.chmod(path, stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)


@pytest.fixture()
def exported(certified_work):
    """A two-record corpus admitted into its own world, exported, replicated and
    restored: a serviceable export root beside its sibling, as step 6 leaves it."""
    stem = certified_work / f"publish-remote-engine-{os.getpid()}-{next(_counter)}"
    corpus, world_root, container = stem / "staging", stem / "world", stem / "export"
    container.mkdir(parents=True)
    try:
        init_corpus_root(corpus, authority=FULL)
        writer = open_corpus(corpus, authority=FULL, profile=V2)
        writer.adopt_manifest(profile=pins_for(V2))
        records = [stored.run_node(name, title=name, spec="s", produces=[]) for name in ("a", "b")]
        for node in records:
            writer._stage_record(node_to_markdown(node))
        corpus_id = load_manifest(corpus).corpus_id
        config = WorldConfig(world_root, "e" * 32, (corpus,))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus, provenance=Fresh())
        artifact = export_head_artifact(world, CorpusSubject(corpus_id))
        export = container / corpus_id
        (container / f"{corpus_id}.head-artifact.v1").write_bytes(artifact)
        replicate_root(corpus, export, authority=FULL)
        observers = ObserverSet((ArtifactCarrier.from_bytes(artifact),))
        assert restore_root(export, CorpusSubject(corpus_id), observers, authority=FULL).outcome == "validated"
        yield export, corpus_id, observers, artifact, records
    finally:
        for path in (corpus, world_root, stem / "export"):
            if path.exists():
                writable(path)
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)
        for leftover in container.glob("*.metadata") if container.exists() else ():
            shutil.rmtree(leftover, ignore_errors=True)
        shutil.rmtree(stem, ignore_errors=True)


def _evaluate(export: Path, corpus_id: str, observers: ObserverSet) -> str:
    return _restore_root(export, CorpusSubject(corpus_id), observers, seam=_log_seam(), grant=_grant_nothing).outcome


def _tree(root: Path) -> list[tuple[str, bytes | None]]:
    return sorted((str(p.relative_to(root)), p.read_bytes() if p.is_file() else None) for p in root.rglob("*"))


def test_a_serviceable_export_root_holds_only_directories_and_regular_files(exported):
    """EXPORT_LAYOUT, and CHAIN_DIR printed for Task 8's Y16-a sabotage."""
    export, *_ = exported
    for directory, dirnames, filenames in os.walk(export):
        for name in (*dirnames, *filenames):
            path = Path(directory) / name
            assert not path.is_symlink() and (path.is_dir() or path.is_file()), path
    print("TOP LEVEL =", sorted(p.name for p in export.iterdir()))


def test_the_chain_head_reads_a_serviceable_export(exported):
    """CHAIN_HEAD_SERVICEABLE: the sibling's genesis and head are the export's chain head."""
    export, corpus_id, _, artifact, _ = exported
    decoded = decode_head_artifact(artifact)
    assert decoded.subject == CorpusSubject(corpus_id)
    assert (decoded.genesis, decoded.head) == chain_head_reader()(export)


def test_the_evaluation_validates_an_intact_serviceable_export(exported):
    """EVALUATE_INTACT: the no-grant evaluation over a root already serviceable."""
    export, corpus_id, observers, _, _ = exported
    assert _evaluate(export, corpus_id, observers) == "validated"


def test_the_evaluation_writes_nothing(exported):
    """EVALUATE_WRITES_NOTHING: the tree, its metadata sibling and the lifecycle state are unchanged."""
    export, corpus_id, observers, _, _ = exported
    before = (_tree(export), _tree(metadata_root_for(export)), read_lifecycle_state(export))
    _evaluate(export, corpus_id, observers)
    assert (_tree(export), _tree(metadata_root_for(export)), read_lifecycle_state(export)) == before
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE


def test_the_evaluation_refuses_a_deleted_selected_record(exported):
    """EVALUATE_DELETED, and DAMAGE_WRITABLE: lifting write permission is enough to damage it."""
    export, corpus_id, observers, _, records = exported
    writable(export)
    (export / path_for_node_id(records[0].id)).unlink()
    assert _evaluate(export, corpus_id, observers) != "validated"


def test_the_evaluation_refuses_an_altered_selected_record(exported):
    """EVALUATE_ALTERED."""
    export, corpus_id, observers, _, records = exported
    writable(export)
    path = export / path_for_node_id(records[0].id)
    path.write_bytes(path.read_bytes() + b"\n")
    assert _evaluate(export, corpus_id, observers) != "validated"


@pytest.mark.parametrize("damage", ["unreadable", "undecodable"])
def test_the_evaluation_over_an_unreadable_or_undecodable_record(exported, damage):
    """EVALUATE_UNREADABLE and EVALUATE_UNDECODABLE: an outcome other than
    `validated`, or the exception type printed for `root.py` to translate."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    export, corpus_id, observers, _, records = exported
    writable(export)
    path = export / path_for_node_id(records[0].id)
    if damage == "unreadable":
        path.chmod(0)
    else:
        path.write_bytes(b"\x00\xffnot a record")
    try:
        outcome = _evaluate(export, corpus_id, observers)
    except Exception as caught:  # a probe: the type is the finding
        print(f"EVALUATE_{damage.upper()} raises {type(caught).__module__}.{type(caught).__qualname__}")
    else:
        print(f"EVALUATE_{damage.upper()} answers {outcome}")
        assert outcome != "validated"
    finally:
        path.chmod(0o644)


def test_a_damaged_chain_raises_from_the_chain_head(exported):
    """CHAIN_HEAD_DAMAGED: the type `root.export_chain_head` translates."""
    export, *_ = exported
    writable(export)
    chain = export / ".#~chain"  # CHAIN_DIR, as the layout probe prints it
    victim = next(p for p in sorted(chain.rglob("*")) if p.is_file())
    victim.write_bytes(b"garbage")
    with pytest.raises(Exception) as caught:  # a probe: the type is the finding
        chain_head_reader()(export)
    print(f"CHAIN_HEAD_DAMAGED = {type(caught.value).__module__}.{type(caught.value).__qualname__}")


@pytest.mark.parametrize("damage", ["deleted", "unreadable"])
def test_a_missing_or_unreadable_chain_raises_from_the_chain_head(exported, damage):
    """CHAIN_HEAD_DELETED and CHAIN_HEAD_UNREADABLE (the round-2 reviewer saw
    `PreconditionRefused` for both), and EVALUATE_CHAIN_DELETED."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 directories")
    export, corpus_id, observers, _, _ = exported
    writable(export)
    chain = export / ".#~chain"
    if damage == "deleted":
        shutil.rmtree(chain)
    else:
        chain.chmod(0)
    try:
        with pytest.raises(Exception) as caught:  # a probe: the type is the finding
            chain_head_reader()(export)
        print(f"CHAIN_HEAD_{damage.upper()} = {type(caught.value).__module__}.{type(caught.value).__qualname__}")
        if damage == "deleted":
            try:
                print(f"EVALUATE_CHAIN_DELETED answers {_evaluate(export, corpus_id, observers)}")
            except Exception as refused:  # a probe
                print(f"EVALUATE_CHAIN_DELETED raises {type(refused).__module__}.{type(refused).__qualname__}")
    finally:
        if chain.exists():
            chain.chmod(0o755)
```

```bash
cd python && uv run --frozen pytest tests/test_publish_remote_engine.py -q -s 2>&1 | tail -15
```
Expected: `11 passed`, with the `TOP LEVEL =`, `EVALUATE_UNREADABLE`, `EVALUATE_UNDECODABLE`, `CHAIN_HEAD_DAMAGED`, `CHAIN_HEAD_DELETED`, `CHAIN_HEAD_UNREADABLE` and `EVALUATE_CHAIN_DELETED` lines.
- Record `CHAIN_DIR` as the one name in `TOP LEVEL` that is neither a record kind directory nor `corpus.yaml`. The J9 acceptance case removes it as `".#~chain"`; if it differs, change the chain-damage probe's `".#~chain"` to match and rerun.
- Record each other verdict as `"holds"`, and the three printed lines verbatim.
- Task 5's two translations already catch `OSError`, `ChainStateInvalid`, `TransactionHalted` and `PreconditionRefused`, all four imported in `root.py`. If any printed line names another type, both translations catch that type too; import it in `root.py` beside the others.

If one fails:
- **`EVALUATE_DELETED` or `EVALUATE_ALTERED` answers `validated`.** Before deciding, probe `audit_log`, spec §4.3's other candidate. Build a `WorldConfig(<stem>/audit-world, "a" * 32, (export,))` and call `audit_log(config, CorpusSubject(corpus_id), export, observers, actor="probe")`. If it refuses both damages, Task 5's `evaluate_copy` wraps `audit_log` with that single-root configuration, and the planning note says so. If neither call refuses both, the spec says planning stops: `tasks note beliefs-3ce305 "<verdicts>"`, then park `--reason decision`. There is no fallback check.
- **`EVALUATE_INTACT` refuses, or raises** (for example because the hold refuses a read-only serviceable root). Probe `audit_log` the same way, then decide as above.
- **`DAMAGE_WRITABLE` fails** (a `PermissionError` after `writable`). Record how the engine protects the root (`lsattr -R`, the modes). Park `--reason decision`: Y13-c's damage and Y16-c's unreadable file both need a way in.
- **`CHAIN_HEAD_SERVICEABLE` fails.** Record the refusal, then park `--reason decision`: §4.2's check 2 relies on it.

- [ ] **Step 3: Bank Y11–Y16.** Append the six rows to the table in `docs/designs/2026-09-22-publication-design.md`, copied byte for byte from the spec's §10 (`grep -n '^| \*\*Y1[1-6]\*\*' docs/superpowers/specs/2026-09-26-publish-act-remote-design.md`). Change its status line to: "Y1–Y4 closed at cut 39; Y5–Y10 closed at cut 40; Y11–Y16 banked with conformance cut 42's freeze (`../superpowers/specs/2026-09-26-publish-act-remote-design.md` §10)".

In `python/tests/test_designs_corpus.py`, extend the `"Y"` tuple through `"Y16"`. The total moves from 231 to 237 rows, and the table count stays at twenty-two. Update:
- `README.md` ("**237 rows** across **twenty-two frozen tables**");
- `docs/guide/contracts-and-adoption.md` (its totals sentence and line);
- the ledger's `Current state` (Y11–Y16 open under `publish`);
- the roadmap's accounting paragraph ("204 of 237 rows closed, with 33 open") and Appendix A, regenerated with `cd python && uv run --frozen python tools/roadmap_status.py`. Expected: `Closed 204 of 237; open 33.`

- [ ] **Step 4: Write the cut document.** Use cut 41's shape (`sed -n 1,140p docs/designs/2026-09-25-conformance-cut-41.md` first). Header:

```markdown
# Conformance cut 42 — the publish act, remote

**Status:** frozen <date>, before implementation; Y11–Y16 are open
**Design:** `../superpowers/specs/2026-09-26-publish-act-remote-design.md`, approved 2026-09-27 at `e353c2d` after three user reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-27-publish-act-remote.md`.
**Numbered after** cut 41 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 42 or above at freeze.
```

Then these sections:
- **§1, what the cut is:** spec §1, condensed.
- **§2, the boundary:** every file in this plan's file map from Task 1 to Task 8, and "Frozen declarations and cut bodies through cut 41 remain byte-exact."
- **§3, selection:** the six Y rows from Step 3, then the unit table from spec §11.2 as amended by Step 5's planning notes: fourteen rows, Y11-a through Y16-c, with the assertion column.
- **§4, accounting:** "**14 arms, 14 declaration units**, six rows; Y11–Y16 open and close; recent-cut row `(14, 14, 6)`; Task 7 passes <n>; 204 of 237 → 210 of 237".
  - `<n>` is the number of test cases Task 7's module collects: `cd python && uv run --frozen pytest tests/acceptance/test_publish_remote_acceptance.py --collect-only -q | tail -1`, run after Task 7. Until then, write the count from Task 7's code: fourteen units, whose parametrizations make twenty-four cases, plus the three extra tests' seven cases, for 31.
  - If Step 2 left a fact unrun, state which arm is unrun, give the reduced counts, and say that the row is **partial**.
- **§5, N2 and acceptance obligations:**
  - the sabotage table from Task 8 Step 1;
  - the seven engine verdicts and `CHAIN_DIR` from Step 2;
  - `PREFIX_RUNNERS = ("cut41_acceptance.py",)` and `PHASE_MODULES = ("test_publish_remote_acceptance.py", "test_n2_cut42.py")`.
- **§6, second reader:** check that:
  - every arm publishes under exactly `publishes()`;
  - Y12-b counts `_stage_record` calls on the resume;
  - Y13-c damages a *selected* record of the serviceable export and counts `push` calls;
  - Y15-b's P binds before A opens;
  - Y16-b asserts the epoch refusal before reading the tip.
- **§7, limitations:** spec §14.

- [ ] **Step 5: README, guide, and the planning notes in the spec.**
  - `README.md`: add 1 to the designs count word, and add a table row after cut 41's: `| \`<freeze date>-conformance-cut-42.md\` | the frozen remote publish cut: the transport seam, the mark, step 7's evaluation and verification, orphans, \`publish-unfinished\`, the remote recovery rows and \`publication_tip\`; Y11–Y16 read, 14 declaration units, the cut 41 runner as prefix |`.
  - `docs/guide/contracts-and-adoption.md`: add the frozen-not-discharged paragraph and the cut-42 path, both on cut 41's shape.

Append this as the spec's §17. It records every interface the plan fixes where the spec named another, or named none:

```markdown
## 17. Planning notes

- 2026-09-27 — at planning (plan `../plans/2026-09-27-publish-act-remote.md`):
  - **The export evaluation is `root.evaluate_copy(dest_root, subject,
    observers) -> str`**: `_restore_root`'s outcome with a grant that does
    nothing, the recipient's own evaluation, or `"unreadable"` when the copy
    cannot be read to be judged (`OSError`, or the engine refusing its chain
    as state, translated inside `root.py`). Task 0 pinned that it validates an
    intact serviceable export, refuses one with a selected record deleted,
    altered, unreadable or undecodable, and writes nothing. `audit_log` was
    not chosen: it requires the target to be a configured corpus root, and an
    export root is in no world.
  - **§4.2's checks are identity only; the marker's content waits for the
    evaluation** (plan review, round 1). Before anything else, the resume
    checks the mark against its intent, the export's manifest, the sibling's
    SHA-256, subject and chain head (`root.export_chain_head`, which answers
    `None` for a chain the engine refuses as state), and the export's one
    `publication` file by its path. It reads no record's content. It then
    evaluates the export. A failed evaluation closes the attempt
    `transport-incomplete` (`export-damaged`) with its orphan, so a damaged
    selected record never strands the destination as `transport-mark-corrupt`.
    Only after `validated` does it read the marker file and check its shape
    (`publication_content_malformed`, `marker_consistent`), its uid and its
    selection count. A disagreement there is `transport-mark-corrupt`. Step 7
    evaluates again before `push`, binding the uploaded bytes to the judged
    ones. A resume therefore evaluates twice, and a fresh run once.
  - **An `OSError` while reading an export file for either listing is
    `export-damaged`** (§4.3 steps 1 and 3). The listings read every byte, and
    a file the act cannot read is damage the evaluation would also find.
  - **`publication_layout_refusal` is spelled `require_publication_layout(records)
    -> None`**, which raises `PublicationArrivalRefused`. Raising keeps cut
    40's Y10-a and Y10-b pins byte-exact. `publication_tip` catches it and
    raises `PublicationReadingRefused` with the same reason and refs.
  - **The layout check runs on every held root that holds any `publication`
    record**, before the address filter. The address of a malformed marker
    cannot be read, so a root whose only marker is malformed refuses the
    reading rather than being skipped as "another view's".
  - **`capture-damaged` catches exactly the store's four read refusals**:
    `OSError` (an unreadable file answers `PermissionError`, probed),
    `nodes`' `ValidationError` (undecodable bytes, probed), `PlacementError`
    and `CollisionError`. These are `_population`'s three plus `OSError`.
  - **`PublicationReadingRefused(reason, corpus_id, refs=())`**, where
    `corpus_id` is `None` for the two readings that are not one corpus's:
    `supersession-cycle`, and `marker-duplicated` across corpora.
  - **`require_usable` returns the frozen `Destination`** in place of a path:
    the resolved local directory, or the remote destination as given.
  - **The mark codec lives in `publish_request.py`** beside the snapshot and
    request codecs: `TransportMark`, `encode_mark`, `decode_mark`, and
    `MARK_DOMAIN = "science.publish-transport.v1"`.
  - **Steps 7–9 run over `_Remote`**, which holds the writer, the resolver,
    the opened intent, the operations directory, the clock, the seam, the
    port and the transport, and never the request or the snapshot
    (decision 5). A fresh run builds it from `_Attempt.remote()`.
  - **`PublicationRefused` gains `tokens`**, the blocking tokens in
    ascending order.
  - **`PreBinding.orphan` defaults to `None`**, so every existing
    construction and comparison stands.
  - **`publish-unfinished` runs for a remote destination only.** A local
    destination can hold no mark (§4.1), and not reading its chain keeps cut
    40's step-0 refusal order untouched.
  - **The listing identity** is `v1.digest("science.publish-transport-listing.v1",
    <expected listing as a mapping>)`, 64 lowercase hex.
  - **Crashes are injected by monkeypatching the act's named step functions**,
    cut 40's plus `_mark`, `_push` and `_verify`.
  - **Two sabotages are spelled for one-edit form:**
    - Y12-a deletes the mark's write. For a crash inside `push`, that is
      indistinguishable from a mark written after `push` returns.
    - Y16-c reads a damaged root as holding nothing. That is what a
      report-mode capture does to the one unreadable file, over a root
      whose only other content the check does not need.
```

Change the spec's `Status` line to "approved 2026-09-27 at `e353c2d`; frozen as cut 42 on <date>".

The plan's step children, filed with the plan, each depend on their predecessor:
- Task 0 `beliefs-64bb0e`, Task 1 `beliefs-c081cf`, Task 2 `beliefs-bcd9ba`, Task 3 `beliefs-714dc9`;
- Task 4 `beliefs-d83a23`, Task 5 `beliefs-931a45` (high), Task 6 `beliefs-62a70d`, Task 7 `beliefs-a266c7` (high);
- Task 8 `beliefs-9cb720`, Task 9 `beliefs-e4d83f`, Task 10 `beliefs-0382ef`, Task 11 `beliefs-d5feb8`.

`tasks start` each child before its task, and `tasks done` it in that task's commit. Every `<Task N's id>` below is its id from this list.

- [ ] **Step 6: Verify and commit the freeze**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py tests/test_publish_remote_engine.py -q
cd .. && tasks note beliefs-3ce305 "Cut 42 frozen: EXPORT_LAYOUT, CHAIN_HEAD_SERVICEABLE, EVALUATE_INTACT, EVALUATE_DELETED, EVALUATE_ALTERED, EVALUATE_WRITES_NOTHING, DAMAGE_WRITABLE = <verdicts>; CHAIN_DIR = <name>; accounting 14/14/6; chains cut 41."
tasks done <Task 0's id> "cut 42 frozen, Y11–Y16 banked, engine facts pinned"
tasks check && git add docs README.md python/tests/test_designs_corpus.py python/tests/test_publish_remote_engine.py tasks
git commit -m "docs(cut): freeze conformance cut 42, the publish act (remote); bank Y11–Y16"
git rev-parse HEAD; sha256sum docs/designs/*-conformance-cut-42.md
```
Record the commit hash as `CUT42_FREEZE_COMMIT` and the digest as `CUT42_FROZEN_SHA256`, both for Task 8.

---
### Task 1: The transport seam and its fake

**Files:**
- Create: `python/src/beliefs/transport.py`, `python/tests/transport_fake.py`, `python/tests/test_transport.py`

**Interfaces:**
- Produces:
  - `Transport` (protocol): `push(destination, files: Mapping[str, Path]) -> TransportAbandoned | None` and `listing(destination, corpus_id: str) -> Mapping[str, str]`;
  - `TransportAbandoned(detail: str)`;
  - `transport_files(container: Path, corpus_id: str) -> dict[str, Path]`;
  - `local_listing(files: Mapping[str, Path]) -> dict[str, str]`;
  - `listing_identity(listing: Mapping[str, str]) -> str` (64 hex), and `LISTING_DOMAIN`;
  - in `tests/transport_fake.py`: `DirectoryTransport(base)`, with the fields `pushes`, `abandon`, `fail_on_push`, `fail_after_files` and `after_push`, and the methods `remote_dir(destination)` and `materialize(destination, corpus_id, into) -> tuple[Path, bytes]`; and `TransportFault(Exception)`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_transport.py`:

```python
"""The transport seam (publish-act-remote design §3.1), portable: the naming of
an export root's files, the local listing and its identity, and the
directory-backed fake the acceptance module drives."""

from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

import pytest
from transport_fake import DirectoryTransport, TransportFault

from beliefs.errors import MalformedRecord
from beliefs.intents.publish import Destination
from beliefs.transport import TransportAbandoned, listing_identity, local_listing, transport_files

CORPUS = "1" * 32
REMOTE = Destination.remote("https://remote.test/pub")


def _container(tmp_path: Path) -> Path:
    """An export container: a root with a record, a nested record and a hidden chain file, and its sibling."""
    container = tmp_path / "export"
    root = container / CORPUS
    (root / "run").mkdir(parents=True)
    (root / ".#~chain").mkdir()
    (root / "corpus.yaml").write_bytes(b"manifest")
    (root / "run" / "a.md").write_bytes(b"a")
    (root / ".#~chain" / "0001").write_bytes(b"entry")
    (container / f"{CORPUS}.head-artifact.v1").write_bytes(b"artifact")
    return container


def test_every_regular_file_and_the_sibling_are_named(tmp_path):
    container = _container(tmp_path)
    assert sorted(transport_files(container, CORPUS)) == [
        f"{CORPUS}.head-artifact.v1",
        f"{CORPUS}/.#~chain/0001",
        f"{CORPUS}/corpus.yaml",
        f"{CORPUS}/run/a.md",
    ]


def test_the_metadata_sibling_is_never_named(tmp_path):
    container = _container(tmp_path)
    (container / f"{CORPUS}.metadata").mkdir()
    (container / f"{CORPUS}.metadata" / "store").write_bytes(b"engine")
    assert not any("metadata" in name for name in transport_files(container, CORPUS))


@pytest.mark.parametrize("where", ["file", "directory", "sibling"])
def test_a_symlink_refuses(tmp_path, where):
    container = _container(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    if where == "file":
        os.symlink(container / CORPUS / "run" / "a.md", container / CORPUS / "run" / "b.md")
    elif where == "directory":
        os.symlink(target, container / CORPUS / "linked")
    else:
        sibling = container / f"{CORPUS}.head-artifact.v1"
        sibling.rename(target / "artifact")
        os.symlink(target / "artifact", sibling)
    with pytest.raises(MalformedRecord):
        transport_files(container, CORPUS)


def test_a_missing_root_or_sibling_refuses(tmp_path):
    container = _container(tmp_path)
    with pytest.raises(MalformedRecord):
        transport_files(container, "2" * 32)
    (container / f"{CORPUS}.head-artifact.v1").unlink()
    with pytest.raises(MalformedRecord):
        transport_files(container, CORPUS)


def test_the_local_listing_digests_the_bytes(tmp_path):
    files = transport_files(_container(tmp_path), CORPUS)
    assert local_listing(files) == {name: sha256(path.read_bytes()).hexdigest() for name, path in files.items()}


def test_the_listing_identity_is_a_function_of_the_listing_alone():
    one = {"b": "1" * 64, "a": "2" * 64}
    assert listing_identity(one) == listing_identity(dict(sorted(one.items())))
    assert len(listing_identity(one)) == 64 and listing_identity(one) != listing_identity({"a": "2" * 64})


def test_equivalent_remote_spellings_are_one_destination():
    """Review Focus 1: one URL, spelled two ways, is one destination."""
    assert Destination.remote("HTTPS://Remote.Test/pub") == REMOTE
    assert REMOTE.locator == "https://remote.test/pub"


def test_the_fake_round_trips_and_lists_the_whole_namespace(tmp_path):
    container = _container(tmp_path)
    fake = DirectoryTransport(tmp_path / "remote")
    files = transport_files(container, CORPUS)
    assert fake.push(REMOTE, files) is None
    assert fake.listing(REMOTE, CORPUS) == local_listing(files)
    (fake.remote_dir(REMOTE) / CORPUS / "extra").write_bytes(b"x")
    (fake.remote_dir(REMOTE) / ("2" * 32)).mkdir()
    (fake.remote_dir(REMOTE) / ("2" * 32) / "other").write_bytes(b"y")
    listed = fake.listing(REMOTE, CORPUS)
    assert f"{CORPUS}/extra" in listed and not any(name.startswith("2" * 32) for name in listed)


def test_the_fakes_faults(tmp_path):
    container = _container(tmp_path)
    files = transport_files(container, CORPUS)
    fake = DirectoryTransport(tmp_path / "remote", fail_after_files=1)
    with pytest.raises(TransportFault):
        fake.push(REMOTE, files)
    assert len(fake.listing(REMOTE, CORPUS)) == 1
    fake.fail_after_files = None
    assert fake.push(REMOTE, files) is None
    root, sibling = fake.materialize(REMOTE, CORPUS, tmp_path / "copy")
    assert sibling == b"artifact" and (root / "run" / "a.md").read_bytes() == b"a"
    assert not (tmp_path / "copy" / f"{CORPUS}.metadata").exists()
    fake.abandon = True
    assert type(fake.push(REMOTE, files)) is TransportAbandoned
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_transport.py -q`
Expected: FAIL, collection error `No module named 'beliefs.transport'`.

- [ ] **Step 3: Write `python/src/beliefs/transport.py`**

```python
"""The transport seam (publish-act-remote design §3.1, decision 1): the caller's
adapter moves bytes and reads the remote back, and the act — never the seam —
decides "verified complete" by comparing the remote's enumeration with its own
listing. Plain standard library over the export root; nothing of `atoms`."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination

__all__ = ["LISTING_DOMAIN", "Transport", "TransportAbandoned", "listing_identity", "local_listing", "transport_files"]

LISTING_DOMAIN = "science.publish-transport-listing.v1"


@dataclass(frozen=True)
class TransportAbandoned:
    """This attempt's upload will never complete (decision 4): a terminal answer,
    unlike an exception, which means "try again"."""

    detail: str


class Transport(Protocol):
    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None:
        """Upload every named file, idempotently: a retry converges on the same remote content."""
        ...

    def listing(self, destination: Destination, corpus_id: str) -> Mapping[str, str]:
        """Every remote file named `<corpus_id>.head-artifact.v1` or under `<corpus_id>/`,
        mapped to the SHA-256 hex of its remote bytes: what the remote holds, not what was asked."""
        ...


def transport_files(container: Path, corpus_id: str) -> dict[str, Path]:
    """Every regular file under `<container>/<corpus_id>`, named
    `<corpus_id>/<posix path relative to the root>`, and the sibling, named
    `<corpus_id>.head-artifact.v1`. The `.metadata` sibling is the engine's and is
    never named. A symlink or any other non-regular entry refuses."""
    root = Path(container) / corpus_id
    if root.is_symlink() or not root.is_dir():
        raise MalformedRecord(f"{root}: a transported root is a directory")
    files: dict[str, Path] = {}
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(dirnames)
        here = Path(directory)
        for name in (*dirnames, *filenames):
            if (here / name).is_symlink():
                raise MalformedRecord(f"{here / name}: a transported root holds no symlink")
        for name in sorted(filenames):
            path = here / name
            if not path.is_file():
                raise MalformedRecord(f"{path}: a transported root holds only regular files")
            files[f"{corpus_id}/{path.relative_to(root).as_posix()}"] = path
    sibling = Path(container) / f"{corpus_id}.head-artifact.v1"
    if sibling.is_symlink() or not sibling.is_file():
        raise MalformedRecord(f"{sibling}: the sibling is a regular file")
    files[sibling.name] = sibling
    return files


def local_listing(files: Mapping[str, Path]) -> dict[str, str]:
    """Each name mapped to the SHA-256 hex of its local bytes."""
    return {name: sha256(Path(path).read_bytes()).hexdigest() for name, path in sorted(files.items())}


def listing_identity(listing: Mapping[str, str]) -> str:
    """The `transported` outcome's `listing`: a digest of the verified listing alone."""
    return v1.digest(LISTING_DOMAIN, dict(sorted(listing.items())))
```

- [ ] **Step 4: Write `python/tests/transport_fake.py`**

```python
"""A directory-backed `Transport` for the remote publish tests
(publish-act-remote design §11.2): `https://remote.test/<name>` is the
directory `<base>/<name>`, and each transported name is a file under it. A
test double; it never ships."""

from __future__ import annotations

import shutil
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path

from beliefs.intents.publish import Destination
from beliefs.transport import TransportAbandoned

_PREFIX = "https://remote.test/"


class TransportFault(Exception):
    """A transient transport failure: the act propagates it and the attempt stays unfinished."""


class DirectoryTransport:
    def __init__(self, base: Path, *, fail_on_push: int | None = None, fail_after_files: int | None = None) -> None:
        self.base = Path(base)
        self.pushes = 0
        self.abandon = False
        self.fail_on_push = fail_on_push  # raise at the start of this push call (1-based)
        self.fail_after_files = fail_after_files  # raise after uploading this many files, on any push
        self.after_push: Callable[[Path], None] | None = None  # a fault applied to the remote after a push

    def remote_dir(self, destination: Destination) -> Path:
        if destination.type != "remote" or not destination.locator.startswith(_PREFIX):
            raise ValueError(f"the fake serves {_PREFIX}…, not {destination.locator!r}")
        return self.base / destination.locator.removeprefix(_PREFIX)

    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None:
        self.pushes += 1
        if self.abandon:
            return TransportAbandoned("the fake abandons")
        if self.fail_on_push == self.pushes:
            raise TransportFault(f"push {self.pushes} fails")
        target = self.remote_dir(destination)
        for uploaded, (name, path) in enumerate(sorted(files.items())):
            if self.fail_after_files is not None and uploaded == self.fail_after_files:
                raise TransportFault(f"push {self.pushes} fails after {uploaded} files")
            remote = target / name
            remote.parent.mkdir(parents=True, exist_ok=True)
            remote.write_bytes(Path(path).read_bytes())
        if self.after_push is not None:
            self.after_push(target)
        return None

    def listing(self, destination: Destination, corpus_id: str) -> dict[str, str]:
        target = self.remote_dir(destination)
        listed: dict[str, str] = {}
        for path in sorted(target.rglob("*")) if target.is_dir() else ():
            name = path.relative_to(target).as_posix()
            if path.is_file() and (name == f"{corpus_id}.head-artifact.v1" or name.startswith(f"{corpus_id}/")):
                listed[name] = sha256(path.read_bytes()).hexdigest()
        return listed

    def materialize(self, destination: Destination, corpus_id: str, into: Path) -> tuple[Path, bytes]:
        """A recipient's raw copy (decision 10): the root's files without any
        `.metadata` sibling, so it reads `METADATA_LESS`, and the sibling's bytes."""
        target = self.remote_dir(destination)
        into.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target / corpus_id, into / corpus_id)
        return into / corpus_id, (target / f"{corpus_id}.head-artifact.v1").read_bytes()
```

- [ ] **Step 5: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_transport.py -q`
Expected: `11 passed`. Then `uv run --frozen ruff check src/beliefs/transport.py tests/transport_fake.py tests/test_transport.py && uv run --frozen pyright src/beliefs/transport.py`.

If `test_equivalent_remote_spellings_are_one_destination` fails, `url_locator` does not fold the case of the scheme and host. That is a finding about Review Focus 1, not a test to relax. Keep the `REMOTE` assertion, move the mixed-case one into a note on `beliefs-3ce305`, and file an idea against `url_locator` naming the two spellings.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 1's id> "transport seam, naming, listings, directory fake"
tasks check && git add python/src/beliefs/transport.py python/tests/transport_fake.py python/tests/test_transport.py tasks
git commit -m "feat(publish): the transport seam and its directory fake — cut 42"
```

---

### Task 2: The transport entry and the remote lifecycle

**Files:**
- Modify: `python/src/beliefs/report.py` (the lifecycle values after `RevealRefused`; `Outcome`; `Entry`; the four tables; `_LIFECYCLE_SUCCESS`; `publish_sequence_error`; `_LIFECYCLE_OUTCOMES`; `_LIFECYCLE_ENTRY_TYPES`), `python/src/beliefs/stored.py` (`_REPORT_ENTRY_OUTCOMES`, and the lifecycle-kind tuple in `_valid_report_entry`)
- Test: `python/tests/test_report.py`

**Interfaces:**
- Produces: `Transported(corpus_id, listing)`, `TransportIncomplete(corpus_id, marker, reason)`, `TRANSPORT_INCOMPLETE_REASONS = ("abandoned", "listing-mismatch", "export-damaged")`, `PublicationTransportEntry(subject, outcome)`, and the entry kind `"publication-transport"` with the outcome types `"transported"` and `"transport-incomplete"`.

- [ ] **Step 1: Write the failing tests**, appended to `python/tests/test_report.py`:

```python
# --- publish-act-remote §5.1: the transport entry and the remote lifecycle ------

from beliefs.errors import MalformedRecord as _Malformed
from beliefs.report import (
    BindingBound as _Bound,
    Exported as _Exported,
    PublicationBindingEntry as _Binding,
    PublicationExportEntry as _Export,
    PublicationRevealEntry as _Reveal,
    PublicationStagingEntry as _Staging,
    PublicationTransportEntry,
    Revealed as _Revealed,
    RevealRefused as _RevealRefused,
    Staged as _Staged,
    StagingCorrupt as _StagingCorrupt,
    Transported,
    TransportIncomplete,
    _entry_facet,
    publish_entries_from_facet,
    publish_sequence_error,
)

_S = "coord:" + "a" * 32 + "/" + "d" * 32
_STAGE, _EXPORT, _REVEAL = _Staging(_S, _Staged("1" * 32, 2)), _Export(_S, _Exported("1" * 32, "f" * 64)), _Reveal(_S, _Revealed("1" * 32))
_MOVED = PublicationTransportEntry(_S, Transported("1" * 32, "e" * 64))
_BIND = _Binding(_S, _Bound("c" * 32, "1" * 32, "a" * 32))


def _incomplete(reason: str) -> PublicationTransportEntry:
    return PublicationTransportEntry(_S, TransportIncomplete("1" * 32, "a" * 32, reason))


@pytest.mark.parametrize(
    "sequence",
    [
        (_STAGE, _EXPORT, _REVEAL, _MOVED, _BIND),
        (_STAGE, _EXPORT, _REVEAL, _incomplete("abandoned")),
        (_STAGE, _EXPORT, _REVEAL, _incomplete("listing-mismatch")),
        (_STAGE, _EXPORT, _REVEAL, _incomplete("export-damaged")),
    ],
    ids=["bound", "abandoned", "listing-mismatch", "export-damaged"],
)
def test_the_remote_lifecycle_is_admitted_and_round_trips(sequence):
    assert publish_sequence_error(sequence) is None
    assert publish_entries_from_facet([_entry_facet(entry) for entry in sequence]) == sequence


@pytest.mark.parametrize(
    "sequence",
    [
        (_STAGE, _EXPORT, _MOVED),                                      # transport before reveal
        (_STAGE, _EXPORT, _Reveal(_S, _RevealRefused("1" * 32, "refuted")), _MOVED),  # transport after a refusal
        (_STAGE, _EXPORT, _REVEAL, _incomplete("abandoned"), _BIND),    # a binding after transport-incomplete
        (_STAGE, _EXPORT, _REVEAL, _MOVED),                             # a successful transport is not an ending
        (_MOVED, _BIND),                                                # a transport alone
    ],
    ids=["before-reveal", "after-refusal", "bind-after-incomplete", "transport-ends", "transport-alone"],
)
def test_malformed_remote_sequences_are_refused(sequence):
    assert publish_sequence_error(sequence) is not None


def test_every_local_sequence_is_still_admitted():
    corrupt = _Staging(_S, _StagingCorrupt("1" * 32, "extra", ("dataset:x",)))
    for sequence in ((_STAGE, _EXPORT, _REVEAL, _BIND), (_BIND,), (corrupt,), (_STAGE, _EXPORT, _Reveal(_S, _RevealRefused("1" * 32, "refuted")))):
        assert publish_sequence_error(sequence) is None


@pytest.mark.parametrize(
    "build",
    [
        lambda: Transported("1" * 32, "E" * 64),
        lambda: Transported("1" * 31, "e" * 64),
        lambda: TransportIncomplete("1" * 32, "a" * 32, "timed-out"),
        lambda: TransportIncomplete("1" * 32, "a" * 31, "abandoned"),
    ],
    ids=["listing-upper", "short-corpus", "reason-outside", "short-marker"],
)
def test_the_transport_outcomes_refuse_malformed_fields(build):
    with pytest.raises(_Malformed):
        build()


def test_the_stored_mirror_accepts_both_transport_outcomes():
    from beliefs.stored import _valid_report_entry

    assert _valid_report_entry(_entry_facet(_MOVED)) and _valid_report_entry(_entry_facet(_incomplete("export-damaged")))
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_report.py -q -k "remote or transport or local_sequence"`
Expected: FAIL at import, `cannot import name 'PublicationTransportEntry'`.

- [ ] **Step 3: Implement.** In `report.py`, after `REVEAL_REFUSED_VERDICTS`:

```python
TRANSPORT_INCOMPLETE_REASONS = ("abandoned", "listing-mismatch", "export-damaged")
```

After `RevealRefused`:

```python
@sealed
@final
@dataclass(frozen=True)
class Transported:
    corpus_id: str
    listing: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "transported corpus id")
        if type(self.listing) is not str or _HEX64.fullmatch(self.listing) is None:
            raise MalformedRecord("a transported listing identity is 64 lowercase hex")


@sealed
@final
@dataclass(frozen=True)
class TransportIncomplete:
    """A terminal refusal that carries its orphan (publish-act-remote decision 4)."""

    corpus_id: str
    marker: str
    reason: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "transport-incomplete corpus id")
        _require_hex32(self.marker, "transport-incomplete marker")
        if self.reason not in TRANSPORT_INCOMPLETE_REASONS:
            raise MalformedRecord(f"transport-incomplete reason {self.reason!r} is outside {TRANSPORT_INCOMPLETE_REASONS}")
```

Add `| Transported | TransportIncomplete` to the end of `Outcome`. After `PublicationRevealEntry`:

```python
@sealed
@final
@dataclass(frozen=True)
class PublicationTransportEntry:
    subject: str
    outcome: Transported | TransportIncomplete

    def __post_init__(self) -> None:
        _require_str(self.subject, "publication transport entry subject")
        _require_outcome(self, self.outcome)
```

Add `| PublicationTransportEntry` to `Entry`. Add one row to each table:
- `_ALLOWED_OUTCOMES`: `PublicationTransportEntry: (Transported, TransportIncomplete),`
- `_ENTRY_KINDS`: `PublicationTransportEntry: "publication-transport",`
- `_OUTCOME_TYPES`: `Transported: "transported",` and `TransportIncomplete: "transport-incomplete",`

Replace the lifecycle constants and `publish_sequence_error`:

```python
_LIFECYCLE_ENTRIES = (PublicationStagingEntry, PublicationExportEntry, PublicationRevealEntry)
_REMOTE_LIFECYCLE = (*_LIFECYCLE_ENTRIES, PublicationTransportEntry)
_LIFECYCLE_SUCCESS = {
    PublicationStagingEntry: Staged,
    PublicationExportEntry: Exported,
    PublicationRevealEntry: Revealed,
    PublicationTransportEntry: Transported,
}


def publish_sequence_error(sequence: object) -> str | None:
    """`None` iff `sequence` is a publish report's sequence (publish-act-local §7,
    publish-act-remote §5.1): a request refusal alone; a prefix of the local
    lifecycle (staging, export, reveal) or of the remote one (… then transport),
    each entry but the last succeeding and the last refusing; a whole lifecycle,
    every entry succeeding, then the binding; or the binding alone (cut 39's
    door, called bare)."""
    if type(sequence) is not tuple or not sequence or any(type(e) not in _ENTRY_KINDS for e in sequence):
        return "a publish report carries a non-empty tuple of entries"
    if len({e.subject for e in sequence}) != 1:
        return "every entry of a publish report names the one binding address"
    kinds = tuple(type(e) for e in sequence)
    if kinds == (PublicationRequestEntry,):
        return None
    if kinds[-1] is PublicationBindingEntry:
        if kinds[:-1] not in ((), _LIFECYCLE_ENTRIES, _REMOTE_LIFECYCLE):
            return "a binding entry follows the whole lifecycle or nothing"
        if any(type(e.outcome) is not _LIFECYCLE_SUCCESS[type(e)] for e in sequence[:-1]):
            return "a binding follows a lifecycle that succeeded at every step"
        return None
    if kinds != _REMOTE_LIFECYCLE[: len(kinds)]:
        return "lifecycle entries run staging, export, reveal, transport, in that order"
    if any(type(e.outcome) is not _LIFECYCLE_SUCCESS[type(e)] for e in sequence[:-1]):
        return "only the last lifecycle entry refuses"
    if type(sequence[-1].outcome) is _LIFECYCLE_SUCCESS[kinds[-1]]:
        return "a lifecycle sequence ends at a refusal or at the binding"
    return None
```

Add `"publication-transport": {"transported": Transported, "transport-incomplete": TransportIncomplete},` to `_LIFECYCLE_OUTCOMES`, and `"publication-transport": PublicationTransportEntry,` to `_LIFECYCLE_ENTRY_TYPES`.

In `stored.py`, add `"publication-transport": {"transported": (), "transport-incomplete": ()},` after the `publication-reveal` row of `_REPORT_ENTRY_OUTCOMES`, and add `"publication-transport"` to the kind tuple in `_valid_report_entry` that routes to `report_values.lifecycle_outcome_from_facet` (`grep -n '"publication-reveal")' src/beliefs/stored.py`).

If an existing test asserts the old message "lifecycle entries run staging, export, reveal, in that order", update its expected text: `grep -rn "reveal, in that order" tests`.

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_report.py tests/test_stored.py tests/test_publication_doors.py tests/test_arm_staleness.py -q`
Expected: PASS, with no stale arm.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 2's id> "publication-transport entry, transported / transport-incomplete, remote lifecycle"
tasks check && git add python/src/beliefs/report.py python/src/beliefs/stored.py python/tests/test_report.py tasks
git commit -m "feat(report): the transport entry and the remote publish lifecycle — cut 42"
```

---

### Task 3: The fold's orphan, the transport rule, and unfinished attempts

**Files:**
- Modify: `python/src/beliefs/publication_doors.py` (`PreBinding`, `_reports_at`, `marker_tips_at`, `_refuse_publication`'s docstring, the new `_orphan_of` and `unfinished_attempts`, `__all__`), `python/src/beliefs/errors.py` (`PublicationRefused(tokens=)`)
- Test: `python/tests/test_publication_doors.py`

**Interfaces:**
- Consumes: Task 2's `PublicationTransportEntry` and `TransportIncomplete`.
- Produces:
  - `PreBinding(outcome: str, orphan: tuple[str, str] | None = None)`;
  - `unfinished_attempts(writer: CorpusWriter, view: CoordinationAddress, destination: Destination, seam: MomentSeam) -> tuple[str, ...]`;
  - `PublicationRefused(reason, *, tips=(), refs=(), corpus_ids=(), field="", tokens=())`.

- [ ] **Step 1: Write the failing tests**, appended to `python/tests/test_publication_doors.py`:

```python
# --- publish-act-remote §5.2: the transport entry in the fold ------------------

from beliefs.coordination import ChainBound
from beliefs.publication_doors import PreBinding, _reports_at, unfinished_attempts
from beliefs.report import (
    Exported,
    PublicationExportEntry,
    PublicationRevealEntry,
    PublicationStagingEntry,
    PublicationTransportEntry,
    Revealed,
    Staged,
    Transported,
    TransportIncomplete,
)

REMOTE = Destination.remote("https://remote.test/pub")


def _lifecycle_to_reveal():
    s = _subject()
    return (
        PublicationStagingEntry(s, Staged("1" * 32, 2)),
        PublicationExportEntry(s, Exported("1" * 32, "f" * 64)),
        PublicationRevealEntry(s, Revealed("1" * 32)),
    )


def _transported_bound(marker):
    s = _subject()
    return (*_lifecycle_to_reveal(), PublicationTransportEntry(s, Transported("1" * 32, "e" * 64)),
            PublicationBindingEntry(s, BindingBound("c" * 32, "1" * 32, marker)))


def _incomplete(marker):
    return (*_lifecycle_to_reveal(), PublicationTransportEntry(_subject(), TransportIncomplete("1" * 32, marker, "abandoned")))


def _remote_refused(marker):
    s = _subject()
    return (*_lifecycle_to_reveal(), PublicationTransportEntry(s, Transported("1" * 32, "e" * 64)),
            PublicationBindingEntry(s, BindingEvidenceRefused("1" * 32, marker, True, "mounts-changed")))


def _remote_chain(tmp_path, rows, *, destination=REMOTE, unfulfilled=()):
    """One written root. Per row `(build, carried)`: a publish intent to
    `destination` carrying `carried` as its marker tips, and a committed
    fulfilment whose report holds `build(marker)`; the k-th marker is "ab"[k] * 32.
    Then one bare intent per `(token, view, destination)` in `unfulfilled`."""
    from beliefs.boundary import _mint_publish_refusal

    root = (tmp_path / "written").resolve()
    (root / "act-report").mkdir(parents=True)
    entries = [genesis_entry(b"g", label="remote-genesis")]
    for k, (build, carried) in enumerate(rows):
        value = intent(event_token=str(k) * 32, binding_tips=(), marker_tips=tuple(carried), destination=destination)
        opened = IntentEntryView(digest=digest(f"remote-intent-{k}"), payload=encode_publish_intent(value))
        body = build("ab"[k] * 32)
        times = {"observer": value.actor, "instrument": "beliefs.publish", "opened_at": value.at, "closed_at": value.at}
        if type(body[-1]) is PublicationBindingEntry:
            report = boundary._mint_publish_report(value, entry=body[-1], lifecycle=body[:-1], **times)
        else:
            report = _mint_publish_refusal(value, entries=body, **times)
        node = stored.act_report_node(report)
        path = path_for_node_id(node.id)
        data = node_to_markdown(node).encode("utf-8")
        (root / path).write_bytes(data)
        created = RegisteredEntryView(
            digest=digest(f"remote-reg-{k}"), txid=f"remote-{k}", initial=((path, ABSENT),), final=((path, file_state(data)),),
            fulfills=opened.digest,
        )
        entries += [opened, created, settlement(digest(f"remote-set-{k}"), created.digest, f"remote-{k}", committed=True)]
    for n, (token, view, target) in enumerate(unfulfilled):
        bare = intent(event_token=token, binding_tips=(), marker_tips=(), destination=target, view=view)
        entries.append(IntentEntryView(digest=digest(f"remote-bare-{n}"), payload=encode_publish_intent(bare)))
    return root, chain(*entries)


def _only(root, view, destination=REMOTE):
    bound = ChainBound(root, "9" * 32, view, len(view.entries) - 1, True)
    ((_, outcome),) = list(_reports_at(bound, VIEW, destination, seam_over({root: view})))
    return outcome


def test_a_transport_entry_under_a_local_intent_is_malformed(tmp_path):
    root, view = _remote_chain(tmp_path, [(_incomplete, ())], destination=HERE)
    outcome = _only(root, view, HERE)
    assert type(outcome) is PositionRefused and outcome.reason == "revision-malformed"


def test_only_transport_incomplete_sets_the_pre_binding_orphan(tmp_path):
    root, view = _remote_chain(tmp_path, [(_incomplete, ())])
    assert _only(root, view) == PreBinding("transport-incomplete", ("1" * 32, "a" * 32))
    other = tmp_path / "other"
    other.mkdir()
    root, view = _remote_chain(other, [(_staging_corrupt, ())])
    assert _only(root, view) == PreBinding("staging-corrupt")


A, B = ("1" * 32, "a" * 32), ("1" * 32, "b" * 32)


@pytest.mark.parametrize(
    "rows, expected",
    [
        ([(_staging_corrupt, ())], set()),                    # PreBinding, orphan None: skipped
        ([(_incomplete, ())], {A}),                           # PreBinding, orphan set: an orphan
        ([(_incomplete, ()), (_incomplete, (A,))], {A, B}),   # ... that retires nothing its intent named
        ([(_remote_refused, ())], {A}),                       # a remotely revealed step-8 refusal (cut 39)
        ([(_incomplete, ()), (_remote_refused, (A,))], {B}),  # a shared refusal retires what it named
        ([(_incomplete, ()), (_transported_bound, (A,))], set()),  # a bound publish retires what it named
    ],
    ids=["pre-binding", "incomplete", "incomplete-retires-nothing", "remote-refusal", "shared-refusal-retires", "bound-retires"],
)
def test_the_remote_orphan_fold(tmp_path, rows, expected):
    root, view = _remote_chain(tmp_path, rows)
    folded = marker_tips_at(
        {root: "9" * 32}, VIEW, REMOTE, written=root, position=view.tip, anchors=(), seam=seam_over({root: view}), binding_tips=()
    )
    assert type(folded) is tuple and set(folded) == expected


def test_unfinished_attempts_list_only_unfulfilled_intents_for_the_pair(tmp_path):
    root, view = _remote_chain(tmp_path, [(_incomplete, ())], unfulfilled=[("7" * 32, VIEW, REMOTE), ("6" * 32, VIEW, REMOTE)])
    assert unfinished_attempts(_reader_over(root), VIEW, REMOTE, seam_over({root: view})) == ("6" * 32, "7" * 32)


def test_unfinished_attempts_are_per_view_and_destination(tmp_path):
    """Review Focus 4: another view's, or another destination's, unfinished intent is not listed."""
    other_view = CoordinationAddress("a" * 32, "e" * 32, "c" * 32)
    root, view = _remote_chain(
        tmp_path, [], unfulfilled=[("7" * 32, other_view, REMOTE), ("6" * 32, VIEW, Destination.remote("https://remote.test/other"))]
    )
    assert unfinished_attempts(_reader_over(root), VIEW, REMOTE, seam_over({root: view})) == ()


def test_unfinished_attempts_refuse_a_chain_that_is_not_well_formed(tmp_path):
    root = (tmp_path / "written").resolve()
    root.mkdir()
    with pytest.raises(MalformedRecord):
        unfinished_attempts(_reader_over(root), VIEW, REMOTE, fake_seam(inspect_written=lambda _root: AbsentView()))


def test_publication_refused_carries_its_blocking_tokens():
    refused = PublicationRefused("publish-unfinished", tokens=("1" * 32, "2" * 32))
    assert refused.tokens == ("1" * 32, "2" * 32) and "1" * 32 in str(refused)
```

The `fake_seam` call reuses `test_standing_at`'s helper. Read its signature first (`grep -n "def fake_seam" -A 12 tests/test_standing_at.py`). If it takes no `inspect_written` keyword, build the absent view the way `test_an_unreadable_chain_refuses_before_the_intent` does (line 337).

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_publication_doors.py -q -k "remote or transport or unfinished or blocking"`
Expected: FAIL at import, `cannot import name 'unfinished_attempts'`.

- [ ] **Step 3: Implement.** In `errors.py`, `PublicationRefused.__init__`:

```python
    def __init__(
        self,
        reason: str,
        *,
        tips: tuple[str, ...] = (),
        refs: tuple[str, ...] = (),
        corpus_ids: tuple[str, ...] = (),
        field: str = "",
        tokens: tuple[str, ...] = (),
    ) -> None:
        detail = ", ".join(part for part in (",".join(refs), ",".join(corpus_ids), field, ",".join(tokens)) if part)
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.tips = tips
        self.refs = refs
        self.corpus_ids = corpus_ids
        self.field = field
        self.tokens = tokens
```

In `publication_doors.py`:
- import `PublicationTransportEntry` and `TransportIncomplete` from `beliefs.report`;
- add `"unfinished_attempts"` to `__all__`.

`PreBinding`:

```python
@final
@dataclass(frozen=True)
class PreBinding:
    """A publish report that ends before its binding entry (publish-act-local §7).
    It binds no marker. Only a `transport-incomplete` one carries an orphan
    (publish-act-remote §5.2): a marker possibly shared, which retires nothing."""

    outcome: str  # the last entry's outcome type
    orphan: tuple[str, str] | None = None


def _orphan_of(entry: Entry) -> tuple[str, str] | None:
    """§5.2 rule 2: `(corpus_id, marker)` when the last entry is `transport-incomplete`."""
    if type(entry.outcome) is TransportIncomplete:
        return (entry.outcome.corpus_id, entry.outcome.marker)
    return None
```

In `_reports_at`, between the `publish_entries_from_facet` try-block and the pinned `if type(entries[-1]) …` block:

```python
        if intent.destination.type == "local" and any(type(e) is PublicationTransportEntry for e in entries):
            # §5.2 rule 1: a local attempt never transports
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: {paths[0]}: a transport entry under a local intent")
            continue
```

and change the pinned block's second line only after its `PreBinding(` prefix, so that the pinned `        if type(entries[-1]) is not PublicationBindingEntry:\n            yield intent, PreBinding(` stays byte-exact:

```python
        if type(entries[-1]) is not PublicationBindingEntry:
            yield intent, PreBinding(str(facet["entries"][-1]["outcome"]["type"]), _orphan_of(entries[-1]))
            continue
```

In `marker_tips_at`, replace the `PreBinding` skip:

```python
            if type(outcome) is PreBinding:
                if outcome.orphan is not None:
                    orphans.add(outcome.orphan)  # possibly shared: an orphan that retires nothing (decision 3)
                continue  # otherwise refused before its binding: no marker bound, nothing retired
```

Change `_refuse_publication`'s docstring sentence "Nothing was revealed remotely, so it carries no orphan fields." to "Only a `transport-incomplete` entry carries orphan fields (publish-act-remote §5.1)."

Add after `attempt_reading`:

```python
def unfinished_attempts(
    writer: CorpusWriter, view: CoordinationAddress, destination: Destination, seam: MomentSeam
) -> tuple[str, ...]:
    """The tokens of every publish intent for `(view, destination)` on the written
    chain with no committed fulfilling registration, ascending (publish-act-remote
    §4.1). It reads chain entries only, never reports."""
    written = Path(writer.root).resolve()
    chain_view = seam.inspect_written(written)
    if type(chain_view) is not WellFormedView:
        raise MalformedRecord(f"{written}: the written chain is not well formed")
    committed = {e.registration for e in chain_view.entries if type(e) is SettledEntryView and e.committed}
    fulfilled = {
        e.fulfills
        for e in chain_view.entries
        if type(e) is RegisteredEntryView and e.fulfills is not None and e.digest in committed
    }
    tokens: list[str] = []
    for entry in chain_view.entries:
        if type(entry) is not IntentEntryView or entry.digest in fulfilled:
            continue
        try:
            intent = decode_publish_intent(entry.payload)
        except MalformedRecord:
            continue  # another shape's intent
        if intent.view.unpinned() == view.unpinned() and intent.destination == destination:
            tokens.append(intent.event_token)
    return tuple(sorted(tokens))
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_publication_doors.py tests/test_errors.py tests/test_arm_staleness.py -q`
Expected: PASS (drop `tests/test_errors.py` if it does not exist), with no stale arm.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 3's id> "PreBinding orphan, the transport rule, unfinished_attempts, PublicationRefused(tokens=)"
tasks check && git add python/src/beliefs/publication_doors.py python/src/beliefs/errors.py python/tests/test_publication_doors.py tasks
git commit -m "feat(publish): the fold reads transport-incomplete as an orphan; unfinished attempts — cut 42"
```

---

### Task 4: The mark codec and step 0's remote destination

**Files:**
- Modify: `python/src/beliefs/publish_request.py` (`require_usable`; the new `MARK_DOMAIN`, `TransportMark`, `encode_mark`, `decode_mark`), `python/src/beliefs/publish.py` (`publish`'s `require_usable` line)
- Test: `python/tests/test_publish_request.py`

**Interfaces:**
- Produces:
  - `require_usable(operations_root, destination, *, forbidden) -> tuple[Path, Destination]`;
  - `TransportMark(event_token, destination, corpus_id, marker, artifact, records)`;
  - `encode_mark(mark) -> bytes` and `decode_mark(data) -> TransportMark`, which raises `MalformedRecord`.

- [ ] **Step 1: Write the failing tests.** In `python/tests/test_publish_request.py`, change the two `require_usable` success assertions (lines 123 and 125) to expect `(ops.resolve(), Destination.local(str(dest.resolve())))`, then append:

```python
# --- publish-act-remote §4.1, §4.2 ---------------------------------------------

from dataclasses import replace as _replace

from beliefs.publish_request import TransportMark, decode_mark, encode_mark

REMOTE = Destination.remote("https://remote.test/pub")


def _mark(**changes) -> TransportMark:
    values = {"event_token": "d" * 32, "destination": REMOTE, "corpus_id": "1" * 32, "marker": "2" * 32, "artifact": "3" * 64, "records": 2}
    values.update(changes)
    return TransportMark(**values)


def test_a_remote_destination_is_returned_as_given(tmp_path):
    ops = tmp_path / "ops"
    ops.mkdir()
    assert require_usable(ops, REMOTE, forbidden=()) == (ops.resolve(), REMOTE)


def test_a_remote_destination_still_checks_the_operations_root(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for bad in (tmp_path / "missing", corpus):
        with pytest.raises(PublicationRefused) as caught:
            require_usable(bad, REMOTE, forbidden=(corpus,))
        assert caught.value.reason == "operations-root-unusable"


def test_the_mark_round_trips_canonically():
    mark = _mark()
    assert decode_mark(encode_mark(mark)) == mark


@pytest.mark.parametrize(
    "change",
    [
        {"destination": Destination.local("/srv/published")},
        {"event_token": "D" * 32},
        {"corpus_id": "1" * 31},
        {"marker": "x" * 32},
        {"artifact": "3" * 63},
        {"records": 0},
        {"records": True},
    ],
    ids=["local", "token", "corpus", "marker", "artifact", "records-zero", "records-bool"],
)
def test_a_malformed_mark_is_refused(change):
    with pytest.raises(MalformedRecord):
        _mark(**change)


@pytest.mark.parametrize(
    "tamper",
    [
        lambda d: {**d, "extra": 1},
        lambda d: {k: v for k, v in d.items() if k != "records"},
        lambda d: {**d, "domain": "science.publish-request.v1"},
        lambda d: {**d, "records": "2"},
    ],
    ids=["extra-field", "missing-field", "wrong-domain", "records-text"],
)
def test_a_mark_that_is_not_its_closed_shape_does_not_decode(tamper):
    from beliefs.identity import v1

    value = v1.decode(encode_mark(_mark()))
    with pytest.raises(MalformedRecord):
        decode_mark(v1.encode(tamper(value)))


def test_a_mark_that_is_not_canonical_does_not_decode():
    with pytest.raises(MalformedRecord):
        decode_mark(encode_mark(_mark()) + b" ")
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_publish_request.py -q`
Expected: FAIL at import, `cannot import name 'TransportMark'`.

- [ ] **Step 3: Implement.** In `publish_request.py`, replace `require_usable`:

```python
def require_usable(operations_root: Path, destination: Destination, *, forbidden: Sequence[Path]) -> tuple[Path, Destination]:
    """The resolved operations root and the destination the intent freezes
    (publish-act-local §4.1 item 7; publish-act-remote §4.1): the operations root
    is an existing directory outside every mounted corpus root and the world root
    (`forbidden`). A local destination is an existing directory, resolved, neither
    it nor the operations root inside the other or inside `forbidden`. A remote
    destination's locator is a canonical URL and is returned as given."""
    closed = tuple(Path(path).resolve() for path in forbidden)
    ops = Path(operations_root)
    if not ops.is_absolute() or not ops.is_dir() or any(_inside(ops.resolve(), path) for path in closed):
        raise PublicationRefused("operations-root-unusable")
    ops = ops.resolve()
    if destination.type == "remote":
        return ops, destination
    target = Path(destination.locator)
    if not target.is_dir():
        raise PublicationRefused("destination-unusable")
    target = target.resolve()
    if _inside(target, ops) or _inside(ops, target) or any(_inside(target, path) for path in closed):
        if _inside(ops, target) and not _inside(target, ops):
            raise PublicationRefused("operations-root-unusable")
        raise PublicationRefused("destination-unusable")
    return ops, Destination.local(str(target))
```

Append the mark codec:

```python
MARK_DOMAIN = "science.publish-transport.v1"
_MARK_FIELDS = frozenset({"domain", "event_token", "destination", "corpus_id", "marker", "artifact", "records"})


@dataclass(frozen=True)
class TransportMark:
    """The durable record that a remote reveal may have begun (publish-act-remote
    §4.2, decision 2): written create-only after step 6 and before the first `push`."""

    event_token: str
    destination: Destination
    corpus_id: str
    marker: str
    artifact: str
    records: int

    def __post_init__(self) -> None:
        _hex(self.event_token, _HEX32, "a mark's event token")
        if type(self.destination) is not Destination or self.destination.type != "remote":
            raise MalformedRecord("a transport mark names a remote destination")
        _hex(self.corpus_id, _HEX32, "a mark's corpus id")
        _hex(self.marker, _HEX32, "a mark's marker")
        _hex(self.artifact, _HEX64, "a mark's artifact identity")
        if type(self.records) is not int or self.records < 1:
            raise MalformedRecord("a mark's record count is a positive exact int")

    def projection(self) -> dict[str, object]:
        return {
            "domain": MARK_DOMAIN,
            "event_token": self.event_token,
            "destination": self.destination.projection(),
            "corpus_id": self.corpus_id,
            "marker": self.marker,
            "artifact": self.artifact,
            "records": self.records,
        }


def encode_mark(mark: TransportMark) -> bytes:
    return v1.encode(mark.projection())


def decode_mark(data: bytes) -> TransportMark:
    """Strictly: every field present and no other, under its domain, canonical bytes."""
    value = _decoded(data, "a transport mark")
    if set(value) != _MARK_FIELDS or value["domain"] != MARK_DOMAIN:
        raise MalformedRecord("a transport mark carries exactly its closed field set under its domain")
    try:
        mark = TransportMark(
            event_token=value["event_token"],
            destination=Destination.from_projection(value["destination"]),
            corpus_id=value["corpus_id"],
            marker=value["marker"],
            artifact=value["artifact"],
            records=value["records"],
        )
    except (TypeError, ValueError) as caught:
        raise MalformedRecord(f"a transport mark field is malformed: {caught}") from caught
    if encode_mark(mark) != data:
        raise MalformedRecord("a transport mark is not its canonical encoding")
    return mark
```

In `publish.py`, replace the two lines

```python
    operations_root, resolved_destination = require_usable(operations_root, destination, forbidden=forbidden)
    # spec §4.1 item 7: the resolved path is the destination the intent and the request freeze
    destination = Destination.local(str(resolved_destination))
```

with

```python
    # local §4.1 item 7, remote §4.1: the returned destination is the one the intent and the request freeze
    operations_root, destination = require_usable(operations_root, destination, forbidden=forbidden)
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_publish_request.py tests/test_publish.py tests/test_arm_staleness.py -q`
Expected: PASS, with no stale arm.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 4's id> "transport mark codec; require_usable returns the frozen destination"
tasks check && git add python/src/beliefs/publish_request.py python/src/beliefs/publish.py python/tests/test_publish_request.py tasks
git commit -m "feat(publish): the transport mark codec and step 0's remote destination — cut 42"
```

---
### Task 5: The remote act — `beliefs/publish.py` and `root.evaluate_copy`

**Files:**
- Modify: `python/src/beliefs/publish.py`, `python/src/beliefs/root.py` (after `restore_root`)
- Test: `python/tests/test_publish.py` (portable), `python/tests/test_publish_remote_engine.py` (certified: `evaluate_copy`)

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces:
  - `publish(…, transport: Transport | None = None)` and `resume_publish(…, transport: Transport | None = None)`;
  - `PublishUnresolved.reason`, which may now be `"transport-mark-corrupt"`;
  - `PublishRefused.outcome`, which may now be `"transport-incomplete"`;
  - the named step functions `_mark`, `_push` and `_verify`, which the acceptance module crashes;
  - `root.evaluate_copy(dest_root: Path, subject: CorpusSubject | StoreSubject, observers: ObserverSet) -> LogReport`.

- [ ] **Step 1: Write the failing portable tests**, appended to `python/tests/test_publish.py`:

```python
# --- publish-act-remote §3.2, §4.3: the seam guards and step 7 ------------------

import os
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, cast

from authority import ACTOR
from transport_fake import DirectoryTransport

from beliefs import publish as act
from beliefs.errors import ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publish_request import TransportMark
from beliefs.report import Transported, TransportIncomplete
from beliefs.transport import listing_identity, local_listing, transport_files
from beliefs.world.anchors import CorpusSubject, HeadArtifact, head_artifact_bytes

REMOTE = Destination.remote("https://remote.test/pub")
CID, TOKEN = "1" * 32, "d" * 32


def _writer(tmp_path):
    from coordination_fixtures import coordination_profile
    from nodes.core.write_plan import DefaultExecutor

    from beliefs.corpus import CorpusWriter

    root = tmp_path / "written"
    root.mkdir()
    return CorpusWriter(
        root, DefaultExecutor, authority=scoped_authority(RequiredCapabilities.publishes(), ACTOR),
        profile=coordination_profile(None, version=2),
    )


def _call_publish(writer, destination, transport):
    none = cast(Any, None)
    return act.publish(
        writer, none, none, view=none, destination=destination, operations_root=none, staging_profile=none,
        clock=none, seam=none, transport=transport,
    )


def test_a_remote_destination_without_a_transport_refuses_first(tmp_path):
    with pytest.raises(ValidationRefused, match="needs a transport"):
        _call_publish(_writer(tmp_path), REMOTE, None)


def test_a_local_destination_with_a_transport_refuses_first(tmp_path):
    with pytest.raises(ValidationRefused, match="takes no transport"):
        _call_publish(_writer(tmp_path), Destination.local(str(tmp_path)), DirectoryTransport(tmp_path / "remote"))


@pytest.mark.parametrize("destination, transport", [(REMOTE, None), ("local", "fake")], ids=["remote-without", "local-with"])
def test_resume_applies_the_seam_rule_to_the_intents_destination(tmp_path, monkeypatch, destination, transport):
    target = Destination.local(str(tmp_path)) if destination == "local" else destination
    opened = SimpleNamespace(intent=SimpleNamespace(destination=target, actor=ACTOR, event_token=TOKEN))
    monkeypatch.setattr(act, "attempt_reading", lambda *_: SimpleNamespace(opened=opened, reading="unfinished", outcome=None))
    none = cast(Any, None)
    with pytest.raises(ValidationRefused):
        act.resume_publish(
            _writer(tmp_path), none, event_token=TOKEN, operations_root=tmp_path, staging_profile=none, clock=none, seam=none,
            transport=DirectoryTransport(tmp_path / "remote") if transport == "fake" else None,
        )


def _remote(tmp_path, monkeypatch, verdict="validated", fake=None):
    """A `_Remote` over a hand-built export container and a mark agreeing with it;
    the evaluation is stubbed, so step 7's own logic runs without the engine."""
    op = tmp_path / "op"
    root = op / "export" / CID
    (root / "run").mkdir(parents=True)
    (root / "run" / "a.md").write_bytes(b"a")
    sibling = head_artifact_bytes(HeadArtifact(CorpusSubject(CID), "a" * 64, "b" * 64))
    (op / "export" / f"{CID}.head-artifact.v1").write_bytes(sibling)
    monkeypatch.setattr(act, "evaluate_copy", lambda *_args: verdict)
    fake = fake or DirectoryTransport(tmp_path / "remote")
    none = cast(Any, None)
    opened = cast(Any, SimpleNamespace(intent=SimpleNamespace(destination=REMOTE, event_token=TOKEN)))
    remote = act._Remote(none, none, opened, op, none, none, None, fake)
    mark = TransportMark(TOKEN, REMOTE, CID, "2" * 32, sha256(sibling).hexdigest(), 1)
    return remote, mark, fake


def test_a_verified_transport_answers_its_listing_identity(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    expected = local_listing(transport_files(remote.op / "export", CID))
    assert act._transport(remote, mark) == Transported(CID, listing_identity(expected)) and fake.pushes == 1


def test_an_export_the_evaluation_refuses_is_export_damaged_and_never_pushed(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch, verdict="refuted")
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0


def test_an_unreadable_export_file_is_export_damaged_and_never_pushed(tmp_path, monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    path = remote.op / "export" / CID / "run" / "a.md"
    path.chmod(0)
    try:
        assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0
    finally:
        path.chmod(0o644)


def test_bytes_changed_during_the_evaluation_are_export_damaged(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)

    def changing(*_args):
        (remote.op / "export" / CID / "run" / "a.md").write_bytes(b"changed")
        return "validated"

    monkeypatch.setattr(act, "evaluate_copy", changing)
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0


def test_an_abandoning_seam_is_abandoned(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    fake.abandon = True
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "abandoned")


class _Lying(DirectoryTransport):
    def __init__(self, base, lie):
        super().__init__(base)
        self.lie = lie

    def listing(self, destination, corpus_id):
        return self.lie(super().listing(destination, corpus_id))


@pytest.mark.parametrize(
    "lie",
    [
        lambda listed: {name: digest.upper() for name, digest in listed.items()},
        lambda listed: {name: digest for name, digest in listed.items() if not name.endswith(".head-artifact.v1")},
    ],
    ids=["upper-case-digests", "sibling-omitted"],
)
def test_a_listing_that_is_not_exact_is_listing_mismatch(tmp_path, monkeypatch, lie):
    """Review Focus 2: anything but an exact listing is refused, never taken as verified."""
    remote, mark, _ = _remote(tmp_path, monkeypatch, fake=_Lying(tmp_path / "remote", lie))
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "listing-mismatch")
```

`head_artifact_bytes` is the encoder that `decode_head_artifact` inverts. If `anchors` names it otherwise, find it with `grep -n "^def head_artifact" src/beliefs/world/anchors.py`.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_publish.py -q -k "transport or seam or listing or export or abandon"`
Expected: FAIL, with `publish() got an unexpected keyword argument 'transport'` and `module 'beliefs.publish' has no attribute '_Remote'`.

- [ ] **Step 3: `root.evaluate_copy`.** After `restore_root` in `root.py`:

```python
def evaluate_copy(dest_root: Path, subject: CorpusSubject | StoreSubject, observers: ObserverSet) -> str:
    """`restore_root`'s evaluation of a copy, granting nothing (publish-act-remote
    §4.3): the check a recipient's restore runs, run by the publisher over its own
    retained export before every upload. Writes nothing; takes no authority.

    Answers the evaluator's outcome, or `"unreadable"` when the copy cannot be
    read to be judged: a file the process cannot open, or the engine refusing
    the chain as state. The engine's types are named here and nowhere above."""
    if type(subject) not in {CorpusSubject, StoreSubject}:
        raise TypeError("a copy is evaluated for a corpus or store subject")
    try:
        return _restore_root(dest_root, subject, observers, seam=_log_seam(), grant=_grant_nothing).outcome
    except (OSError, ChainStateInvalid, TransactionHalted, PreconditionRefused):
        return "unreadable"


def _grant_nothing(_root: Path) -> None:
    """The evaluation's grant: none. Admission stays `restore_root`'s."""


def export_chain_head(root: Path) -> tuple[str, str] | None:
    """`chain_head_reader()`'s `(genesis, head)` for a retained export, or `None`
    when the engine refuses its chain as state (publish-act-remote §4.2): a
    damaged chain is a mark that names no export, never an exception out of the act."""
    try:
        return _chain_head(root)
    except (OSError, ChainStateInvalid, TransactionHalted, PreconditionRefused):
        return None
```

`PreconditionRefused` covers more than one fact (the `UNREGISTERED_ROOT` note in `root.py`). Here every one of them means the retained export's chain cannot be read, which is the mark naming no readable export, so it answers `None` and the resume answers `transport-mark-corrupt`.

Both `except` tuples grow by any further type Task 0 printed (`EVALUATE_UNREADABLE`, `EVALUATE_UNDECODABLE`, `CHAIN_HEAD_DAMAGED`), and by nothing else.

If Task 0 chose `audit_log`, `evaluate_copy`'s `_restore_root` call is instead `audit_log(WorldConfig(<a scratch world root under the export's container>, "0" * 32, (dest_root,)), subject, dest_root, observers, actor="beliefs.publish").outcome`, and the docstring says why.

Append to `python/tests/test_publish_remote_engine.py`:

```python
def test_evaluate_copy_is_the_no_grant_evaluation(exported):
    from beliefs.root import evaluate_copy

    export, corpus_id, observers, _, records = exported
    assert evaluate_copy(export, CorpusSubject(corpus_id), observers) == "validated"
    writable(export)
    (export / path_for_node_id(records[1].id)).write_bytes(b"\x00\xffnot a record")
    assert evaluate_copy(export, CorpusSubject(corpus_id), observers) != "validated"
    (export / path_for_node_id(records[1].id)).unlink()
    assert evaluate_copy(export, CorpusSubject(corpus_id), observers) != "validated"


def test_export_chain_head_answers_none_for_a_damaged_chain(exported):
    from beliefs.root import export_chain_head

    export, *_ = exported
    assert export_chain_head(export) == chain_head_reader()(export)
    writable(export)
    victim = next(p for p in sorted((export / ".#~chain").rglob("*")) if p.is_file())
    victim.write_bytes(b"garbage")
    assert export_chain_head(export) is None
    shutil.rmtree(export / ".#~chain")
    assert export_chain_head(export) is None
```

- [ ] **Step 4: The act.** In `publish.py`:

**Imports.** Add these to the existing groups:

```python
from collections.abc import Callable, Mapping
from nodes.core.errors import CollisionError, NodesError, PlacementError
from nodes.core.frontmatter import node_from_bytes, node_from_markdown, node_to_markdown
from nodes.core.paths import path_for_node_id
from beliefs.errors import CreateOnlyCollision, MalformedRecord, PublicationRefused, ScienceError, ValidationRefused
from beliefs.publication import (  # add to the existing list
    marker_address,
    marker_consistent,
    publication_content_malformed,
)
from beliefs.publication_doors import (  # add to the existing list
    unfinished_attempts,
)
from beliefs.publish_request import (  # add to the existing list
    TransportMark,
    decode_mark,
    encode_mark,
)
from beliefs.report import (  # add to the existing list
    PublicationTransportEntry,
    TransportIncomplete,
    Transported,
)
from beliefs.root import (  # add to the existing list
    evaluate_copy,
    export_chain_head,
)
from beliefs.transport import Transport, TransportAbandoned, listing_identity, local_listing, transport_files
from beliefs.world.anchors import CorpusSubject, decode_head_artifact
```

Remove `Destination`'s import if it becomes unused. `publish()` no longer builds one after Task 4, but `_require_transport` takes it as a type, so it stays.

**Outcome comment.** `PublishUnresolved.reason`'s comment becomes `# "no-request" | "indeterminate" | "binding-without-report" | "transport-mark-corrupt"`.

**`_Attempt`** gains a last field, `transport: Transport | None`, and a method:

```python
    def remote(self) -> _Remote:
        """Steps 7–9's view of this attempt (decision 5)."""
        assert self.transport is not None
        return _Remote(self.writer, self.resolver, self.opened, self.op, self.clock, self.seam, self.port, self.transport)
```

Add after `_Population`:

```python
@dataclass(frozen=True)
class _Remote:
    """Steps 7–9 of a remote attempt (remote decision 5): the mark, never the
    request or the snapshot."""

    writer: CorpusWriter
    resolver: CoordinationResolver
    opened: OpenedPublication
    op: Path
    clock: Callable[[], str]
    seam: MomentSeam
    port: OperationPort | None
    transport: Transport

    @property
    def token(self) -> str:
        return self.opened.intent.event_token

    @property
    def subject(self) -> str:
        return str(binding_address(self.opened.intent.view, self.opened.intent.destination))


def _require_transport(destination: Destination, transport: Transport | None) -> None:
    """Remote §3.2: a remote destination needs a transport and a local one takes none."""
    if destination.type == "remote" and transport is None:
        raise ValidationRefused("a remote destination needs a transport")
    if destination.type == "local" and transport is not None:
        raise ValidationRefused("a local destination takes no transport")
```

**`publish`.**
- Add the keyword `transport: Transport | None = None` after `port`.
- Replace `if destination.type != "local": raise ValidationRefused("remote destinations arrive in cut 42")` with `_require_transport(destination, transport)`.
- After the `require_usable` line, insert:

```python
    if destination.type == "remote":
        # remote §4.1, decision 6: a stranded attempt that may have shared its marker blocks the pair
        blocking = tuple(token for token in unfinished_attempts(writer, view, destination, seam) if (_op_dir(operations_root, token) / "transport.v1").is_file())
        if blocking:
            raise PublicationRefused("publish-unfinished", tokens=blocking)
```
- Pass `transport` as `_Attempt`'s last argument.

**Export paths.** Each gets a remote branch before its pinned local line:

```python
def _export_root(a: _Attempt, corpus_id: str) -> Path:
    if a.request.destination.type == "remote":
        return _remote_export(a.op, corpus_id)  # remote decision 7
    return Path(a.request.destination.locator) / corpus_id


def _sibling(a: _Attempt, corpus_id: str) -> Path:
    if a.request.destination.type == "remote":
        return _remote_sibling(a.op, corpus_id)
    return Path(a.request.destination.locator) / f"{corpus_id}.head-artifact.v1"


def _remote_export(op: Path, corpus_id: str) -> Path:
    return op / "export" / corpus_id


def _remote_sibling(op: Path, corpus_id: str) -> Path:
    return op / "export" / f"{corpus_id}.head-artifact.v1"
```

**`_write_sibling`.** Add `    ensure_directory(sibling.parent)` right after `sibling = _sibling(a, corpus_id)`, since the remote container is created here. A local destination exists already, so the call does nothing there.

**`_bind` and `_refused`** take either attempt shape:

```python
def _bind(a: _Attempt | _Remote, corpus_id: str, artifact_identity: str, entries: tuple[Entry, ...], *, remote: bool = False):
    """Step 8: the binding door, carrying the lifecycle entries. A remote reveal
    refused here is an orphan (remote §4.4)."""
    return _bind_publication(
        a.writer, a.resolver, a.opened, corpus_id=corpus_id, marker=marker_uid(a.token), artifact=artifact_identity,
        remotely_revealed=remote, clock=a.clock, seam=a.seam, port=a.port,
        lifecycle=entries,
    )
```

and `def _refused(a: _Attempt | _Remote, entries: tuple[Entry, ...]) -> PublishRefused:`, with an unchanged body.

**`_run`.** Insert between `entries.append(PublicationRevealEntry(a.subject, Revealed(corpus_id)))` and `outcome = _bind(...)`:

```python
    if a.request.destination.type == "remote":
        return _transport_and_bind(a.remote(), _mark(a, corpus_id, artifact_identity), tuple(entries))
```

**Steps 7–9**, added after `_run`:

```python
# --- the remote steps (remote §4.2–§4.4) ------------------------------------------


def _mark(a: _Attempt, corpus_id: str, artifact_identity: str) -> TransportMark:
    """The durable record that a remote reveal may begin (decision 2): create-only,
    after step 6 validates and before the first `push`."""
    mark = TransportMark(a.token, a.request.destination, corpus_id, marker_uid(a.token), artifact_identity, len(a.snapshot.records))
    write_create_only(a.op / "transport.v1", encode_mark(mark))
    return mark


def _push(r: _Remote, files: Mapping[str, Path]) -> TransportAbandoned | None:
    """Step 7's upload through the seam: idempotent, reinvoked whole on every retry (§14 item 5)."""
    return r.transport.push(r.opened.intent.destination, files)


def _verify(r: _Remote, corpus_id: str) -> dict[str, str]:
    """Step 7's read-back: the remote's enumeration of the publication's whole namespace."""
    return dict(r.transport.listing(r.opened.intent.destination, corpus_id))


def _listing_or_none(files: Mapping[str, Path]) -> dict[str, str] | None:
    try:
        return local_listing(files)
    except OSError:
        return None  # a file the act cannot read is damage (planning note)


def _evaluate_export(r: _Remote, mark: TransportMark) -> str:
    """§4.3 step 2: the recipient's evaluation of the retained export against its
    own sibling, granting nothing; `"unreadable"` when it cannot be judged."""
    try:
        observers = ObserverSet((ArtifactCarrier.from_bytes(_remote_sibling(r.op, mark.corpus_id).read_bytes()),))
    except (OSError, ScienceError):
        return "unreadable"  # a sibling gone or undecodable since the mark: damage, like any other
    return evaluate_copy(_remote_export(r.op, mark.corpus_id), CorpusSubject(mark.corpus_id), observers)


def _export_damaged(r: _Remote, mark: TransportMark) -> bool:
    """The one place the export's content is judged, on a fresh run and on a resume."""
    return _evaluate_export(r, mark) != "validated"


def _transport(r: _Remote, mark: TransportMark) -> Transported | TransportIncomplete:
    """Step 7 (§4.3): upload exactly the bytes the evaluation judged, then verify
    by the remote's own listing. The act, not the seam, decides."""
    damaged = TransportIncomplete(mark.corpus_id, mark.marker, "export-damaged")
    files = transport_files(r.op / "export", mark.corpus_id)
    before = _listing_or_none(files)
    if before is None or _export_damaged(r, mark):
        return damaged
    expected = _listing_or_none(files)
    if expected is None or expected != before:
        return damaged
    if type(_push(r, files)) is TransportAbandoned:
        return TransportIncomplete(mark.corpus_id, mark.marker, "abandoned")
    listing = _verify(r, mark.corpus_id)
    if listing != expected:
        return TransportIncomplete(mark.corpus_id, mark.marker, "listing-mismatch")
    return Transported(mark.corpus_id, listing_identity(expected))


def _transport_and_bind(r: _Remote, mark: TransportMark, entries: tuple[Entry, ...]) -> PublishOutcome:
    """Steps 7, 8 and 9 from the mark. An incomplete transport writes its report
    alone and carries its orphan (decision 4)."""
    transported = _transport(r, mark)
    if type(transported) is TransportIncomplete:
        return _refused(r, (*entries, PublicationTransportEntry(r.subject, transported)))
    assert type(transported) is Transported
    entries = (*entries, PublicationTransportEntry(r.subject, transported))
    outcome = _bind(r, mark.corpus_id, mark.artifact, entries, remote=True)
    if outcome.binding is None:
        return PublishRefused(r.token, outcome_type(outcome.report.entries[-1].outcome))
    _discard(r.op)
    return Published(r.token, mark.corpus_id, mark.marker, outcome.binding.uid, mark.artifact)


def _marker_path(r: _Remote, mark: TransportMark) -> Path:
    """The export's marker file, by name: its id follows from the intent and the mark's uid."""
    address = marker_address(r.opened.intent.view, r.opened.intent.destination)
    return _remote_export(r.op, mark.corpus_id) / path_for_node_id(f"{MARKER_KIND}:{address.project}.{address.local}.{mark.marker}")


def _export_agrees(r: _Remote, mark: TransportMark) -> bool:
    """§4.2 as identity only (planning note): the export's manifest names the
    mark's corpus, the sibling is the mark's artifact and names that corpus and
    the export's chain head, and the export holds one `publication` file, the
    mark's marker by name. No record's content is read here, so a damaged
    selected record reaches the evaluation and closes as `export-damaged`."""
    export, sibling = _remote_export(r.op, mark.corpus_id), _remote_sibling(r.op, mark.corpus_id)
    try:
        if not _serviceable(export) or load_manifest(export).corpus_id != mark.corpus_id:
            return False
        data = sibling.read_bytes()
        if sha256(data).hexdigest() != mark.artifact:
            return False
        artifact = decode_head_artifact(data)
    except (OSError, ValueError, ScienceError):  # file I/O, the artifact decoder, the manifest
        return False
    head = export_chain_head(export)
    if head is None or artifact.subject != CorpusSubject(mark.corpus_id) or (artifact.genesis, artifact.head) != head:
        return False
    marker = _marker_path(r, mark)
    kind_directory = export / marker.relative_to(export).parts[0]
    held = sorted(path for path in kind_directory.rglob("*") if path.is_file()) if kind_directory.is_dir() else []
    return held == [marker]


def _mark_corrupt(r: _Remote, mark: TransportMark) -> bool:
    """§4.2: the mark agrees with its intent, then with its export's identity."""
    intent = r.opened.intent
    if mark.event_token != intent.event_token or mark.destination != intent.destination or mark.marker != marker_uid(intent.event_token):
        return True
    return not _export_agrees(r, mark)


def _marker_agrees(r: _Remote, mark: TransportMark) -> bool:
    """After the export evaluated `validated`: its marker is well formed and
    consistent, is the mark's, and selects `mark.records` records."""
    try:
        node = node_from_bytes(_marker_path(r, mark).read_bytes())
    except (OSError, NodesError):
        return False
    if node.kind != MARKER_KIND or publication_content_malformed(node) or not marker_consistent(node) or node.uid != mark.marker:
        return False
    return len(node.facets[stored.COORDINATION_FACET]["selection"]) == mark.records


def _resume_from_mark(r: _Remote) -> PublishOutcome:
    """Decision 5: steps 7–9 from the mark alone. Identity first (a failure is
    `transport-mark-corrupt`); then the export's content (a failure closes the
    attempt `export-damaged` with its orphan, pushing nothing); then the marker's
    content, trusted only once the evaluation validated it."""
    try:
        mark = decode_mark((r.op / "transport.v1").read_bytes())
    except MalformedRecord:
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    if _mark_corrupt(r, mark):
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    entries = (
        PublicationStagingEntry(r.subject, Staged(mark.corpus_id, mark.records)),
        PublicationExportEntry(r.subject, Exported(mark.corpus_id, mark.artifact)),
        PublicationRevealEntry(r.subject, Revealed(mark.corpus_id)),
    )
    if _export_damaged(r, mark):
        return _refused(r, (*entries, PublicationTransportEntry(r.subject, TransportIncomplete(mark.corpus_id, mark.marker, "export-damaged"))))
    if not _marker_agrees(r, mark):
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    return _transport_and_bind(r, mark, entries)
```

`_marker_path` builds the marker id the way `_binding_present` builds the binding id. The kind directory is the first component of the marker's own path under the export, so the `rglob` over it finds every `publication` file however `nodes` nests ids.

**`resume_publish`.**
- Add the keyword `transport: Transport | None = None` after `port`.
- After the actor check, insert `    _require_transport(reading.opened.intent.destination, transport)`.
- Between the `binding-without-report` branch and the `no-request` branch, insert:

```python
    if (op / "transport.v1").is_file():
        assert transport is not None  # the seam rule above: a mark exists only for a remote intent
        return _resume_from_mark(_Remote(writer, resolver, reading.opened, op, clock, seam, port, transport))
```
- Pass `transport` as `_Attempt`'s last argument on the request path.

`pending_publishes` does not change.

- [ ] **Step 5: Run to verify they pass**

```bash
cd python && uv run --frozen pytest tests/test_publish.py tests/test_publish_request.py tests/test_publication_doors.py tests/test_arm_staleness.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py -q
uv run --frozen pytest tests/test_publish_remote_engine.py -q
uv run --frozen pytest tests/acceptance/test_publish_act_acceptance.py -q
uv run --frozen ruff check src tests && uv run --frozen pyright
```
Expected: every run passes, with no stale arm. Cut 40's acceptance module is the regression check for the local act. If `test_capability_boundary.py` or the permit inventories flag `evaluate_copy`, follow the Global Constraints' first bullet.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 5's id> "the remote act: mark, step 7 with the export evaluation, resume from the mark, publish-unfinished"
tasks check && git add python/src/beliefs/publish.py python/src/beliefs/root.py python/tests/test_publish.py python/tests/test_publish_remote_engine.py tasks
git commit -m "feat(publish): the remote act — mark, transport, verification, resume — cut 42"
```

---
### Task 6: The recipient's tip reading — `publication_tip`

**Files:**
- Modify: `python/src/beliefs/publication_arrival.py`, `python/src/beliefs/errors.py` (`PublicationReadingRefused`)
- Test: `python/tests/test_publication_arrival.py`

**Interfaces:**
- Produces:
  - `require_publication_layout(records: tuple[Node, ...]) -> None`, which raises `PublicationArrivalRefused`;
  - `publication_tip(roots: tuple[Path, ...], view: CoordinationAddress, destination: Destination) -> CurrentPublication | DivergentPublication | None`;
  - `CurrentPublication(corpus_id, marker)` and `DivergentPublication(tips: tuple[tuple[str, str], ...])`;
  - `PublicationReadingRefused(reason, corpus_id: str | None, refs=())`, a `WriteRefused`.

- [ ] **Step 1: Write the failing tests**, appended to `python/tests/test_publication_arrival.py`:

```python
# --- publish-act-remote §7.1: the tip reading ---------------------------------

import os
from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id

from beliefs.coordination import CoordinationAddress
from beliefs.errors import PublicationReadingRefused
from beliefs.intents.publish import Destination
from beliefs.publication import marker_uid
from beliefs.publication_arrival import CurrentPublication, DivergentPublication, publication_tip
from beliefs.world import load_manifest

REMOTE = Destination.remote("https://remote.test/pub")
VIEW = CoordinationAddress("a" * 32, "b" * 32, "c" * 32)
_PROFILE = coordination_profile(None, version=2)


def _root(tmp_path: Path, name: str) -> CorpusWriter:
    writer = CorpusWriter(tmp_path / name, lambda root: DefaultExecutor(root), authority=FULL, profile=_PROFILE)
    writer.adopt_manifest(profile=pins_for(_PROFILE))
    return writer


def _publish_into(writer: CorpusWriter, token: str, *, carried=(), records=("r",), destination=REMOTE):
    """Stage the selected records and the marker of `token`'s publish, carrying `carried` as its marker tips."""
    nodes = [stored.run_node(name, title=name, spec="s", produces=[]) for name in records]
    for node in nodes:
        writer._stage_record(node_to_markdown(node))
    value = intent(event_token=token, marker_tips=tuple(carried), destination=destination)
    writer._stage_marker(marker_record(value, world_id="d" * 32, epoch="f" * 64, selection=tuple(sorted(n.id for n in nodes))))
    return writer.root, load_manifest(writer.root).corpus_id, marker_uid(token)


def _held(tmp_path, name, token, **kwargs):
    return _publish_into(_root(tmp_path, name), token, **kwargs)


def test_no_marker_at_the_address_reads_none(tmp_path):
    assert publication_tip((), VIEW, REMOTE) is None
    root, _, _ = _held(tmp_path, "elsewhere", "1" * 32, destination=Destination.remote("https://remote.test/other"))
    assert publication_tip((root,), VIEW, REMOTE) is None


def test_one_marker_is_current(tmp_path):
    root, corpus_id, marker = _held(tmp_path, "a", "1" * 32)
    assert publication_tip((root,), VIEW, REMOTE) == CurrentPublication(corpus_id, marker)


def test_two_siblings_are_divergent_ascending(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    b, cb, mb = _held(tmp_path, "b", "2" * 32)
    assert publication_tip((b, a), VIEW, REMOTE) == DivergentPublication(tuple(sorted([(ca, ma), (cb, mb)])))


def test_publications_sharing_selected_records_are_read_side_by_side(tmp_path):
    """Decision 9's premise: one record in two held roots does not stop the reading."""
    a, ca, ma = _held(tmp_path, "a", "1" * 32, records=("r", "s"))
    b, cb, mb = _held(tmp_path, "b", "2" * 32, carried=((ca, ma),), records=("r", "s"))
    assert publication_tip((a, b), VIEW, REMOTE) == CurrentPublication(cb, mb)


def test_an_orphan_with_a_successor_reads_the_successor(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    b, cb, mb = _held(tmp_path, "b", "2" * 32, carried=((ca, ma),))
    assert publication_tip((a, b), VIEW, REMOTE) == CurrentPublication(cb, mb)


def test_a_missing_intermediate_is_divergent(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    c, cc, mc = _held(tmp_path, "c", "3" * 32, carried=(("9" * 32, marker_uid("2" * 32)),))  # C supersedes B only
    assert publication_tip((a, c), VIEW, REMOTE) == DivergentPublication(tuple(sorted([(ca, ma), (cc, mc)])))


def test_one_marker_uid_in_two_corpora_is_marker_duplicated(tmp_path):
    a, _, _ = _held(tmp_path, "a", "1" * 32)
    b, _, _ = _held(tmp_path, "b", "1" * 32)
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((a, b), VIEW, REMOTE)
    assert caught.value.reason == "marker-duplicated" and caught.value.corpus_id is None


def test_a_supersession_cycle_refuses(tmp_path):
    first, second = _root(tmp_path, "a"), _root(tmp_path, "b")
    ca, cb = first.corpus_id, second.corpus_id
    a, _, _ = _publish_into(first, "1" * 32, carried=((cb, marker_uid("2" * 32)),))
    b, _, _ = _publish_into(second, "2" * 32, carried=((ca, marker_uid("1" * 32)),))
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((a, b), VIEW, REMOTE)
    assert caught.value.reason == "supersession-cycle"


_R = stored.run_node("r", title="r", spec="s", produces=[])


def _two_markers(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, marker_record(intent(event_token="9" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,)))


def _beyond_selection(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, stored.run_node("s", title="s", spec="s", produces=[]))


def _binding(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, binding_record(intent(destination=REMOTE), corpus_id="1" * 32, marker="2" * 32, artifact="3" * 64))


def _malformed(writer):
    writer._stage_record(node_to_markdown(_R))
    node = marker_record(intent(event_token="1" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,))
    node.facets[stored.COORDINATION_FACET]["selection"] = ["not an id"]
    raw_add(writer.root, node)


def _inconsistent(writer):
    writer._stage_record(node_to_markdown(_R))
    node = marker_record(intent(event_token="1" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,))
    node.facets[stored.COORDINATION_FACET]["event_token"] = "8" * 32
    raw_add(writer.root, node)


@pytest.mark.parametrize(
    "build, reason",
    [
        (_two_markers, "marker-duplicated"),
        (_beyond_selection, "selection-mismatch"),
        (_binding, "binding-present"),
        (_malformed, "marker-malformed"),
        (_inconsistent, "marker-inconsistent"),
    ],
    ids=["two-markers", "beyond-selection", "binding", "malformed", "inconsistent"],
)
def test_the_reading_refuses_what_arrival_would_refuse(tmp_path, monkeypatch, build, reason):
    writer = _root(tmp_path, "held")
    build(writer)
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((writer.root,), VIEW, REMOTE)
    assert caught.value.reason == reason and caught.value.corpus_id == writer.corpus_id
    monkeypatch.setattr(publication_arrival, "admit_arrival", lambda *args, **kwargs: ("record", "report"))
    with pytest.raises(PublicationArrivalRefused) as arrival:
        admit_publication("world", writer.root, "observers")
    assert arrival.value.reason == reason


@pytest.mark.parametrize("damage", ["unreadable", "undecodable"])
@pytest.mark.parametrize("holds_marker", [True, False], ids=["marker-root", "markerless-root"])
def test_a_damaged_root_refuses_capture_damaged(tmp_path, damage, holds_marker):
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    writer = _root(tmp_path, "held")
    if holds_marker:
        _publish_into(writer, "1" * 32)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    raw_add(writer.root, extra)
    path = writer.root / path_for_node_id(extra.id)
    if damage == "unreadable":
        path.chmod(0)
    else:
        path.write_bytes(b"\x00\xffnot a record")
    try:
        with pytest.raises(PublicationReadingRefused) as caught:
            publication_tip((writer.root,), VIEW, REMOTE)
        assert caught.value.reason == "capture-damaged" and caught.value.corpus_id == writer.corpus_id
    finally:
        path.chmod(0o644)


def test_a_root_named_twice_is_a_value_error(tmp_path):
    """Review Focus 5: by path and through a symlink."""
    root, _, _ = _held(tmp_path, "a", "1" * 32)
    os.symlink(root, tmp_path / "link")
    with pytest.raises(ValueError):
        publication_tip((root, tmp_path / "link"), VIEW, REMOTE)
    with pytest.raises(TypeError):
        publication_tip([root], VIEW, REMOTE)  # type: ignore[arg-type]
```

`raw_add(writer.root, node)` places a record at its mapped path, bypassing every door (`coordination_fixtures.raw_add`). `_malformed` and `_inconsistent` stage one record and a raw marker selecting it: the marker factory refuses an empty selection, so the damage is applied after construction. The layout check runs, and fails, before any address filter (planning note). `DefaultExecutor` is imported in this module already, and so are `binding_record`, `marker_record`, `raw_add`, `intent` and `coordination_profile`.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_publication_arrival.py -q`
Expected: FAIL at import, `cannot import name 'CurrentPublication'`.

- [ ] **Step 3: Implement.** In `errors.py`, after `PublicationArrivalRefused`:

```python
class PublicationReadingRefused(WriteRefused):
    """A recipient's tip reading refused (publish-act-remote design §7.1): a held
    root whose layout arrival would refuse, one the store cannot read whole, or a
    reading that is not one corpus's (`corpus_id` None). A read refusal, like
    `SelectionRefused`."""

    def __init__(self, reason: str, corpus_id: str | None, refs: tuple[str, ...] = ()) -> None:
        where = f" in {corpus_id}" if corpus_id is not None else ""
        super().__init__(f"{reason}{where}: {', '.join(refs)}" if refs else f"{reason}{where}")
        self.reason = reason
        self.corpus_id = corpus_id
        self.refs = refs
```

Rewrite `publication_arrival.py`:

```python
"""Marker-required arrival (publish-act-local design §10; layer design §6.3): a
published corpus is admitted only through its marker, checked before any write,
then through cut 8's arrival act. The recipient's tip reading
(publish-act-remote §7.1) applies the same layout rule to each held root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nodes.core.errors import CollisionError, PlacementError
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.corpus import ReadView
from beliefs.errors import PublicationArrivalRefused, PublicationReadingRefused
from beliefs.intents.publish import Destination
from beliefs.publication import BINDING_KIND, MARKER_KIND, marker_address, marker_consistent, publication_content_malformed
from beliefs.root import admit_arrival
from beliefs.world import ReplicaOf, load_manifest

__all__ = ["CurrentPublication", "DivergentPublication", "admit_publication", "publication_tip", "require_publication_layout"]

_CAPTURE_DAMAGE = (OSError, NodesValidationError, PlacementError, CollisionError)
"""The store's refusals to read a root whole (planning note): an unreadable file,
undecodable bytes, a record off its mapped path, a duplicate uid."""


@dataclass(frozen=True)
class CurrentPublication:
    corpus_id: str
    marker: str


@dataclass(frozen=True)
class DivergentPublication:
    """§6.1's `divergent-publication`: a lawful sibling state, a value and not an exception."""

    tips: tuple[tuple[str, str], ...]


def require_publication_layout(records: tuple[Node, ...]) -> None:
    """Refuse a root with no marker, two markers, a malformed or inconsistent
    marker, a binding, or records other than the marker's selection."""
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
        first = min(set(held) ^ set(selection))
        raise PublicationArrivalRefused("selection-mismatch", refs=(first,))


def admit_publication(world, root: Path, observers):
    """The layout rule before `admit_arrival` writes anything; then admit the root
    as a replica of itself."""
    root = Path(root).resolve()
    require_publication_layout(tuple(ReadView.opened_at(root).iter_stored()))
    return admit_arrival(world, root, ReplicaOf(load_manifest(root).corpus_id), observers)


def _held_records(root: Path, corpus_id: str) -> tuple[Node, ...]:
    """§7.1 step 0: one root's records, read whole. A file the store cannot read
    or decode refuses; a report-mode read would drop it and pass the layout check."""
    try:
        return tuple(ReadView.opened_at(root).iter_stored())
    except _CAPTURE_DAMAGE as caught:
        raise PublicationReadingRefused("capture-damaged", corpus_id, ()) from caught


def publication_tip(
    roots: tuple[Path, ...], view: CoordinationAddress, destination: Destination
) -> CurrentPublication | DivergentPublication | None:
    """The current publication of `view` at `destination` among the held roots,
    each read alone (§7.1, decision 9): the family's one tip rule over the
    markers at `marker_address(view, destination)`, with no world index."""
    if type(roots) is not tuple or any(not isinstance(root, Path) for root in roots):
        raise TypeError("publication_tip reads an exact tuple of held corpus roots")
    resolved = tuple(root.resolve() for root in roots)
    if len(set(resolved)) != len(resolved):
        raise ValueError("a held root is named twice")
    address = marker_address(view.unpinned(), destination)
    held: list[tuple[str, Node]] = []
    seen: set[str] = set()
    for root in resolved:
        corpus_id = load_manifest(root).corpus_id
        records = _held_records(root, corpus_id)
        if not any(node.kind == MARKER_KIND for node in records):
            continue
        try:
            require_publication_layout(records)
        except PublicationArrivalRefused as refused:
            raise PublicationReadingRefused(refused.reason, corpus_id, refused.refs) from refused
        (marker,) = (node for node in records if node.kind == MARKER_KIND)
        if coordination_revision(marker).address != address:
            continue
        if marker.uid in seen:
            raise PublicationReadingRefused("marker-duplicated", None, (marker.uid,))
        seen.add(marker.uid)
        held.append((corpus_id, marker))
    if not held:
        return None
    present = {(corpus_id, marker.uid) for corpus_id, marker in held}
    superseded = {
        (str(pair[0]), str(pair[1]))
        for _, marker in held
        for pair in marker.facets[stored.COORDINATION_FACET]["supersedes_markers"]
    }
    tips = tuple(sorted(present - superseded))
    if not tips:
        raise PublicationReadingRefused("supersession-cycle", None, tuple(sorted(uid for _, uid in present)))
    if len(tips) == 1:
        return CurrentPublication(*tips[0])
    return DivergentPublication(tips)
```

The two pinned `admit_publication` lines keep their spelling and indentation inside `require_publication_layout`. Check with `grep -c '    if not markers:' src/beliefs/publication_arrival.py` and `grep -c '    if held != selection:' src/beliefs/publication_arrival.py`, each expected `1`.

- [ ] **Step 4: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_publication_arrival.py tests/test_arm_staleness.py -q && uv run --frozen pyright src/beliefs/publication_arrival.py`
Expected: PASS, with no stale arm.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 6's id> "require_publication_layout, publication_tip over held roots, PublicationReadingRefused"
tasks check && git add python/src/beliefs/publication_arrival.py python/src/beliefs/errors.py python/tests/test_publication_arrival.py tasks
git commit -m "feat(publish): the recipient's tip reading over held roots — cut 42"
```

---
### Task 7: The acceptance module — `test_publish_remote_acceptance.py`

**Files:**
- Create: `python/tests/acceptance/test_publish_remote_acceptance.py`

**Interfaces:**
- Consumes:
  - cut 40's fixture and helpers, imported from `test_publish_act_acceptance`: `source`, `run`, `fresh_writer`, `token_of_last_intent`, `chain_tip`, `_ops_tree`, `_publish_reports`, `_binding_files`, `Clock`, `Crash`, `crash`, `AUTHORITY`, `SETUP` and `V2`;
  - Tasks 1–6.
- Produces: the fourteen unit functions named in Task 8's `UNIT_CHECKS`.

- [ ] **Step 1: Write the module**

```python
"""Conformance cut 42 — the publish act, remote (publish-act-remote design §11.2).
Fourteen declaration units over real roots on the certified volume, each run
under exactly the publication permit, over cut 40's fixture with a
directory-backed transport at `https://remote.test/pub`.

Crashes are injected at step boundaries by monkeypatching the act's named step
functions (cut 40's, plus `_mark`, `_push`, `_verify`); a fresh `resume_publish`
then reads only disk."""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import replace
from itertools import count
from pathlib import Path

import pytest
from coordination_fixtures import raw_add
from nodes.core.paths import path_for_node_id
from test_publish_act_acceptance import (  # noqa: F401 — `source` is a fixture
    SETUP,
    V2,
    Clock,
    Crash,
    _binding_files,
    _ops_tree,
    _publish_reports,
    chain_tip,
    crash,
    fresh_writer,
    run,
    source,
    token_of_last_intent,
)
from test_world_receipts import hold_shipped
from transport_fake import DirectoryTransport, TransportFault

from beliefs import publish as act
from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.errors import AddressMapConflict, PublicationArrivalRefused, PublicationReadingRefused, PublicationRefused
from beliefs.intents.publish import Destination
from beliefs.publication import MARKER_KIND, marker_uid
from beliefs.publication_arrival import CurrentPublication, DivergentPublication, admit_publication, publication_tip
from beliefs.publication_doors import attempt_reading
from beliefs.publish import Published, PublishRefused, PublishUnresolved, resume_publish
from beliefs.publish_request import decode_mark, encode_mark
from beliefs.root import LifecycleState, init_world_root, moment_seam, open_world, read_lifecycle_state, restore_root
from beliefs.world import WorldConfig, epoch
from beliefs.world.anchors import CorpusSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet

REMOTE = Destination.remote("https://remote.test/pub")
_counter = count()


@pytest.fixture()
def remote(source):
    """Cut 40's source world, publishing to the fake remote."""
    (source.base / "remote").mkdir()
    source.transport = DirectoryTransport(source.base / "remote")
    source.destination = REMOTE
    return source


def publish_remote(s, **changes):
    return run(s, transport=s.transport, **changes)


def resume_remote(s, token: str, transport=None):
    return resume_publish(
        fresh_writer(s), s.resolver, event_token=token, operations_root=s.ops, staging_profile=V2,
        clock=Clock(), seam=moment_seam(), transport=transport or s.transport,
    )


def op_dir(s, token: str) -> Path:
    return s.ops / "publish" / token


def mark_of(s, token: str):
    return decode_mark((op_dir(s, token) / "transport.v1").read_bytes())


def export_of(s, token: str, corpus_id: str) -> Path:
    return op_dir(s, token) / "export" / corpus_id


def marker_node(root: Path):
    (marker,) = [n for n in ReadView.opened_at(root).iter_stored() if n.kind == MARKER_KIND]
    return marker


def supersedes(s, outcome: Published) -> set[tuple[str, str]]:
    """The published marker's `supersedes_markers`, read from its retained export root."""
    facet = marker_node(export_of(s, outcome.event_token, outcome.corpus_id)).facets[stored.COORDINATION_FACET]
    return {(str(c), str(m)) for c, m in facet["supersedes_markers"]}


def writable(root: Path) -> None:
    """Lift write permission on a root's tree (Task 0's DAMAGE_WRITABLE)."""
    for path in (root, *root.rglob("*")):
        if not path.is_symlink():
            os.chmod(path, stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)


def kinds(report) -> list[str]:
    return [e["kind"] for e in report["entries"]]


REMOTE_LIFECYCLE = ["publication-staging", "publication-export", "publication-reveal", "publication-transport"]


def recipient_copy(s, outcome: Published) -> tuple[Path, ObserverSet]:
    """A recipient's restored raw copy of a remote publication (decision 10)."""
    into = s.base / f"recipient-copy-{next(_counter)}"
    s.roots.append(into / outcome.corpus_id)
    root, sibling = s.transport.materialize(REMOTE, outcome.corpus_id, into)
    observers = ObserverSet((ArtifactCarrier.from_bytes(sibling),))
    assert restore_root(root, CorpusSubject(outcome.corpus_id), observers, authority=SETUP).outcome == "validated"
    return root, observers


def recipient_world(s, roots: tuple[Path, ...]):
    world_root = s.base / f"recipient-{next(_counter)}"
    s.roots.append(world_root)
    config = WorldConfig(world_root, "c" * 32, roots)
    init_world_root(config, authority=SETUP)
    return open_world(config, authority=SETUP)


# --- Y11 ------------------------------------------------------------------------


@pytest.mark.parametrize("fault", ["altered", "extra"])
def test_y11_a_a_listing_that_disagrees_is_transport_incomplete_durably(remote, fault):
    """Y11-a: a file altered, or an extra file added, at the remote after `push` → listing-mismatch."""

    def after_push(target: Path) -> None:
        (corpus_dir,) = [p for p in target.iterdir() if p.is_dir()]
        if fault == "altered":
            victim = next(p for p in sorted(corpus_dir.rglob("*")) if p.is_file())
            victim.write_bytes(victim.read_bytes() + b"\n")
        else:
            (corpus_dir / "extra").write_bytes(b"extra")

    remote.transport.after_push = after_push
    outcome = publish_remote(remote)
    assert outcome == PublishRefused(outcome.event_token, "transport-incomplete")
    (report,) = _publish_reports(remote, outcome.event_token)
    assert kinds(report) == REMOTE_LIFECYCLE and report["entries"][-1]["outcome"]["reason"] == "listing-mismatch"
    assert _binding_files(remote) == []
    reading = attempt_reading(fresh_writer(remote), outcome.event_token, moment_seam())
    assert reading is not None and reading.reading == "closed"


# --- Y12 ------------------------------------------------------------------------


def test_y12_a_a_crash_inside_push_leaves_the_mark_and_blocks_the_next_publish_durably(remote):
    """Y12-a: the mark is on disk before the first byte leaves."""
    remote.transport.fail_after_files = 1
    with pytest.raises(TransportFault):
        publish_remote(remote)
    token = token_of_last_intent(remote)
    assert (op_dir(remote, token) / "transport.v1").is_file()
    remote.transport.fail_after_files = None
    tip, ops = chain_tip(remote), _ops_tree(remote)
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.reason == "publish-unfinished" and refused.value.tokens == (token,)
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


def test_y12_b_a_resume_after_the_mark_never_rereads_staging_durably(remote, monkeypatch):
    """Y12-b: an extra record raw-written into staging after the mark is never seen."""
    crash(monkeypatch, "_verify", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    raw_add(op_dir(remote, token) / "staging", stored.run_node("zz", title="zz", spec="s", produces=[]))
    staged: list[str] = []
    original = CorpusWriter._stage_record
    monkeypatch.setattr(CorpusWriter, "_stage_record", lambda self, text: staged.append(text) or original(self, text))
    outcome = resume_remote(remote, token)
    assert type(outcome) is Published and staged == []


@pytest.mark.parametrize("field", ["corpus_id", "artifact"])
def test_y12_c_a_mark_disagreeing_with_its_export_fails_closed_durably(remote, monkeypatch, field):
    """Y12-c: a mark rewritten with another corpus_id or artifact → transport-mark-corrupt, nothing written."""
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    path = op_dir(remote, token) / "transport.v1"
    path.write_bytes(encode_mark(replace(mark_of(remote, token), **{field: "7" * (32 if field == "corpus_id" else 64)})))
    tip, ops = chain_tip(remote), _ops_tree(remote)
    assert resume_remote(remote, token) == PublishUnresolved(token, "transport-mark-corrupt")
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


# --- Y13 ------------------------------------------------------------------------


def test_y13_a_an_abandoned_transport_is_an_orphan_the_next_publish_supersedes_durably(remote):
    """Y13-a: the fake abandons; the next publish binds and its marker supersedes the abandoned pair."""
    remote.transport.abandon = True
    abandoned = publish_remote(remote)
    assert abandoned == PublishRefused(abandoned.event_token, "transport-incomplete")
    pair = (mark_of(remote, abandoned.event_token).corpus_id, marker_uid(abandoned.event_token))
    remote.transport.abandon = False
    bound = publish_remote(remote)
    assert type(bound) is Published and pair in supersedes(remote, bound)


def test_y13_b_an_orphan_named_by_an_abandoned_attempt_is_not_retired_durably(remote):
    """Y13-b: O abandons; T, naming O, abandons; N supersedes both."""
    remote.transport.abandon = True
    o = publish_remote(remote)
    t = publish_remote(remote)
    o_pair = (mark_of(remote, o.event_token).corpus_id, marker_uid(o.event_token))
    t_pair = (mark_of(remote, t.event_token).corpus_id, marker_uid(t.event_token))
    reading = attempt_reading(fresh_writer(remote), t.event_token, moment_seam())
    assert reading is not None and o_pair in reading.opened.intent.marker_tips
    remote.transport.abandon = False
    n = publish_remote(remote)
    assert type(n) is Published and {o_pair, t_pair} <= supersedes(remote, n)


@pytest.mark.parametrize("damage", ["deleted", "altered", "unreadable", "undecodable"])
def test_y13_c_an_export_damaged_after_the_mark_closes_as_an_orphan_durably(remote, monkeypatch, damage):
    """Y13-c: a selected record deleted from, altered in, made unreadable in or
    replaced by undecodable bytes in the serviceable export after the mark → the
    resume refuses `export-damaged` without pushing (never `transport-mark-corrupt`),
    and the next publish supersedes the orphan."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    mark = mark_of(remote, token)
    export = export_of(remote, token, mark.corpus_id)
    selected = marker_node(export).facets[stored.COORDINATION_FACET]["selection"][0]
    writable(export)
    record = export / path_for_node_id(selected)
    if damage == "deleted":
        record.unlink()
    elif damage == "altered":
        data = record.read_bytes()
        record.write_bytes(data[:-2] + bytes([data[-2] ^ 1]) + data[-1:])  # one byte flipped inside the content
    elif damage == "unreadable":
        record.chmod(0)
    else:
        record.write_bytes(b"\x00\xffnot a record")
    pushes = remote.transport.pushes
    assert resume_remote(remote, token) == PublishRefused(token, "transport-incomplete")
    assert remote.transport.pushes == pushes
    (report,) = _publish_reports(remote, token)
    assert kinds(report) == REMOTE_LIFECYCLE and report["entries"][-1]["outcome"]["reason"] == "export-damaged"
    after = publish_remote(remote)
    assert type(after) is Published and (mark.corpus_id, marker_uid(token)) in supersedes(remote, after)


# --- Y14 ------------------------------------------------------------------------


def test_y14_a_a_stranded_marked_attempt_blocks_until_resumed_durably(remote, monkeypatch):
    """Y14-a (Ruling 12): step 8 raises before any effect after a verified
    transport; the next publish refuses until the attempt is resumed."""
    crash(monkeypatch, "_bind", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    reading = attempt_reading(fresh_writer(remote), token, moment_seam())
    assert reading is not None and reading.reading == "unfinished"
    tip, ops = chain_tip(remote), _ops_tree(remote)
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.reason == "publish-unfinished" and refused.value.tokens == (token,)
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops
    resumed = resume_remote(remote, token)
    assert type(resumed) is Published
    after = publish_remote(remote)
    assert type(after) is Published and (resumed.corpus_id, resumed.marker) in supersedes(remote, after)


def test_y14_b_an_attempt_without_a_mark_never_blocks_durably(remote, monkeypatch):
    """Y14-b: a request and no mark → the next publish binds."""
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    stranded = token_of_last_intent(remote)
    assert (op_dir(remote, stranded) / "request.v1").is_file() and not (op_dir(remote, stranded) / "transport.v1").exists()
    assert type(publish_remote(remote)) is Published


# --- Y15 ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "step, before",
    [("_mark", False), ("_push", True), ("_push", False), ("_verify", True), ("_verify", False), ("_bind", True)],
    ids=["after-mark", "before-push", "after-push", "before-verify", "after-verify", "before-bind"],
)
def test_y15_a_a_crash_at_every_remote_step_resumes_to_one_binding_and_one_report_durably(remote, monkeypatch, step, before):
    """Y15-a: crash, resume → Published; one binding, one report of the whole
    remote lifecycle; step 9 keeps the export root, the mark, the request and the snapshot."""
    crash(monkeypatch, step, before=before)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    outcome = resume_remote(remote, token)
    assert type(outcome) is Published
    (report,) = _publish_reports(remote, token)
    assert kinds(report) == [*REMOTE_LIFECYCLE, "publication-binding"]
    assert len(_binding_files(remote)) == 1
    op = op_dir(remote, token)
    assert read_lifecycle_state(export_of(remote, token, outcome.corpus_id)) is LifecycleState.READ_ONLY_SERVICEABLE
    assert all((op / name).is_file() for name in ("transport.v1", "request.v1", "selection.v1"))
    assert not (op / "staging").exists() and not (op / "world").exists()


def test_y15_b_a_remote_step_8_refusal_is_an_orphan_the_next_publish_names_durably(remote):
    """Y15-b: cut 39's W17-p-a race through the act. P binds; A's port runs a whole
    remote publish B, superseding P, inside `append_intent` after A's tip read;
    A transports, then refuses `predecessor-not-standing` with `remotely_revealed`."""
    p = publish_remote(remote)
    assert type(p) is Published
    inner = remote.writer._operation_port
    superseding: list[object] = []

    class SecondWriter:
        def append_intent(self, payload):
            if not superseding:
                superseding.append(publish_remote(remote))  # B supersedes P before A's intent lands
            return inner.append_intent(payload)

        def __getattr__(self, name):
            return getattr(inner, name)

    a = publish_remote(remote, port=SecondWriter())
    (b,) = superseding
    assert type(b) is Published
    assert a == PublishRefused(a.event_token, "predecessor-not-standing")
    reading = attempt_reading(fresh_writer(remote), a.event_token, moment_seam())
    assert reading is not None and reading.opened.intent.binding_tips == (p.binding,)
    (report,) = _publish_reports(remote, a.event_token)
    last = report["entries"][-1]["outcome"]
    assert last["remotely_revealed"] is True and last["tips"] == [b.binding]
    a_pair = (mark_of(remote, a.event_token).corpus_id, marker_uid(a.event_token))
    after = publish_remote(remote)
    assert type(after) is Published
    reading = attempt_reading(fresh_writer(remote), after.event_token, moment_seam())
    assert reading is not None and a_pair in reading.opened.intent.marker_tips


# --- Y16 ------------------------------------------------------------------------


def test_y16_a_a_recipient_restores_admits_and_reads_the_current_publication_durably(remote):
    """Y16-a: materialize, restore against the transported artifact, admit, read the tip;
    the same copy missing one file restores to a non-validated verdict and is refused."""
    outcome = publish_remote(remote)
    assert type(outcome) is Published
    root, observers = recipient_copy(remote, outcome)
    admit_publication(recipient_world(remote, (root,)), root, observers)
    assert publication_tip((root,), remote.view, REMOTE) == CurrentPublication(outcome.corpus_id, outcome.marker)
    into = remote.base / f"recipient-partial-{next(_counter)}"
    remote.roots.append(into / outcome.corpus_id)
    partial, sibling = remote.transport.materialize(REMOTE, outcome.corpus_id, into)
    selected = marker_node(partial).facets[stored.COORDINATION_FACET]["selection"][0]
    writable(partial)
    (partial / path_for_node_id(selected)).unlink()
    verdict = restore_root(partial, CorpusSubject(outcome.corpus_id), ObserverSet((ArtifactCarrier.from_bytes(sibling),)), authority=SETUP)
    assert verdict.outcome != "validated"
    with pytest.raises(PublicationArrivalRefused):
        admit_publication(recipient_world(remote, (partial,)), partial, observers)


def test_y16_b_sibling_publications_are_divergent_until_one_supersedes_both_durably(remote, monkeypatch):
    """Y16-b: A crashed before its mark, B bound, A resumed and bound as a sibling.
    Both select the same records; the recipient's epoch refuses duplicate-location,
    and `publication_tip` reads them side by side as divergent until C."""
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    a_token = token_of_last_intent(remote)
    b = publish_remote(remote)
    a = resume_remote(remote, a_token)
    assert type(a) is Published and type(b) is Published
    (a_root, a_obs), (b_root, b_obs) = recipient_copy(remote, a), recipient_copy(remote, b)
    world = recipient_world(remote, (a_root, b_root))
    admit_publication(world, a_root, a_obs)
    admit_publication(world, b_root, b_obs)
    with pytest.raises(AddressMapConflict) as conflict:
        epoch.build_epoch(world, coverage=frozenset({a.corpus_id, b.corpus_id}), bindings=hold_shipped(world))
    assert conflict.value.args[0].code == "duplicate-location"
    divergent = publication_tip((a_root, b_root), remote.view, REMOTE)
    assert divergent == DivergentPublication(tuple(sorted([(a.corpus_id, a.marker), (b.corpus_id, b.marker)])))
    c = publish_remote(remote)
    assert type(c) is Published and {(a.corpus_id, a.marker), (b.corpus_id, b.marker)} <= supersedes(remote, c)
    c_root, _ = recipient_copy(remote, c)
    assert publication_tip((a_root, b_root, c_root), remote.view, REMOTE) == CurrentPublication(c.corpus_id, c.marker)


def test_y16_c_a_held_root_with_an_unreadable_record_file_refuses_capture_damaged_durably(remote):
    """Y16-c (the round-3 reviewer's probe): an unreadable extra record file in a
    held root refuses `capture-damaged`, and arrival of the same bytes refuses too."""
    if os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    outcome = publish_remote(remote)
    assert type(outcome) is Published
    root, observers = recipient_copy(remote, outcome)
    admit_publication(recipient_world(remote, (root,)), root, observers)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    writable(root)
    raw_add(root, extra)
    path = root / path_for_node_id(extra.id)
    path.chmod(0)
    try:
        with pytest.raises(PublicationReadingRefused) as refused:
            publication_tip((root,), remote.view, REMOTE)
        assert refused.value.reason == "capture-damaged" and refused.value.corpus_id == outcome.corpus_id
        with pytest.raises(PermissionError):
            admit_publication(recipient_world(remote, (root,)), root, observers)
    finally:
        path.chmod(0o644)


# --- beyond the units -------------------------------------------------------------


@pytest.mark.parametrize("check", ["serviceable", "sibling", "chain", "chain-deleted", "marker"])
def test_each_export_check_failing_alone_is_transport_mark_corrupt_durably(remote, monkeypatch, check):
    """§11.1: each of §4.2's checks failing alone → transport-mark-corrupt, nothing written.
    The marker case is the content check, which runs after the evaluation validates."""
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    if check == "serviceable":
        monkeypatch.setattr(act, "read_serviceable", lambda _root: False)
    elif check == "sibling":
        real = act.decode_head_artifact
        monkeypatch.setattr(act, "decode_head_artifact", lambda data: replace(real(data), head="0" * 64))
    elif check == "chain":
        monkeypatch.setattr(act, "export_chain_head", lambda _root: None)
    elif check == "chain-deleted":
        export = export_of(remote, token, mark_of(remote, token).corpus_id)
        writable(export)
        shutil.rmtree(export / ".#~chain")  # Task 0's CHAIN_DIR
    else:
        path = op_dir(remote, token) / "transport.v1"
        mark = mark_of(remote, token)
        path.write_bytes(encode_mark(replace(mark, records=mark.records + 1)))
    tip, ops = chain_tip(remote), _ops_tree(remote)
    assert resume_remote(remote, token) == PublishUnresolved(token, "transport-mark-corrupt")
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


def test_a_push_that_always_raises_writes_nothing_and_keeps_blocking_durably(remote):
    """Review Focus 3: a remote that raises on every push never closes the attempt;
    each resume propagates, writes nothing, and the pair stays blocked."""
    remote.transport.fail_after_files = 0
    with pytest.raises(TransportFault):
        publish_remote(remote)
    token = token_of_last_intent(remote)
    tip = chain_tip(remote)
    for _ in range(2):
        with pytest.raises(TransportFault):
            resume_remote(remote, token)
        assert chain_tip(remote) == tip and _publish_reports(remote, token) == []
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.tokens == (token,)


def test_a_transport_incomplete_attempt_is_never_resumed_durably(remote):
    """§6's last row: closed by transport-incomplete → PublishRefused, and nothing is pushed again."""
    remote.transport.abandon = True
    abandoned = publish_remote(remote)
    remote.transport.abandon = False
    pushes, tip = remote.transport.pushes, chain_tip(remote)
    assert resume_remote(remote, abandoned.event_token) == PublishRefused(abandoned.event_token, "transport-incomplete")
    assert remote.transport.pushes == pushes and chain_tip(remote) == tip
```

Notes for the implementer:
- `remote.view` is the source fixture's view address (`s.view`). `publication_tip` unpins it.
- `AddressMapConflict` carries its `Finding` as `args[0]` (`world/derive.py`). If `build_epoch` wraps the conflict in another refusal, assert that refusal and its `duplicate-location` code instead: the premise is the code, not the type.
- The `SecondWriter` port is used only for A's own calls. B's nested publish runs on the same writer with `port=None`, as W17-p-a's nested `publish(pair)` does.

- [ ] **Step 2: Run the module**

```bash
cd ~/d/beliefs/.worktrees/publish/python && cd "$(pwd -P)"
uv run --frozen pytest tests/acceptance/test_publish_remote_acceptance.py -q 2>&1 | tail -5
uv run --frozen pytest tests/acceptance/test_publish_remote_acceptance.py --collect-only -q | tail -1
```
Expected: `31 passed` (one or two skips when run as root), and a collection count of 31: the units' 24 cases plus the three extra tests' 7. The frozen cut document is never edited after Task 0; its digest is Task 8's pin. If the collected count differs from §4's, the results record §3 states both numbers and why they differ.

If `admit_publication` over Y16-a's unrestored partial copy raises something other than `PublicationArrivalRefused` (for example if `ReadView` refuses a copy restore did not grant), assert that type instead and record it in the spec's §17. The unit's claim is that the copy is refused, not which door refuses it.

A unit that fails for its own reason is a finding: fix the source, not the assertion. A unit that cannot see its behaviour (a vacuous pass) is rehomed at this step and recorded in the spec's §17, never dropped.

- [ ] **Step 3: Commit**

```bash
tasks done <Task 7's id> "acceptance module: 14 units, 31 cases"
tasks check && git add python/tests/acceptance/test_publish_remote_acceptance.py tasks
git commit -m "test(cut42): the remote publish acceptance module — Y11–Y16"
```

---
### Task 8: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut42.py`, `python/tests/acceptance/n2_arms_cut42.py` (cut 41's shim with `41` → `42`), `python/tests/acceptance/test_n2_cut42.py`, `python/tools/cut42_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit, digest and `CHAIN_DIR`; Task 7's test names.
- Produces: `CUT42_ARMS` (14), `DECLARATION_UNITS` (14), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS` and `PHASE_MODULES`.

- [ ] **Step 1: The declaration.** Write `python/tests/n2_arms_cut42.py` on cut 41's shape (`sed -n 1,60p tests/n2_arms_cut41.py`). Its arms span several modules, so `_arm` takes the module:

```python
"""Frozen cut-42 declaration: fourteen units, fourteen sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Y11-a", "Y12-a", "Y12-b", "Y12-c", "Y13-a", "Y13-b", "Y13-c",
    "Y14-a", "Y14-b", "Y15-a", "Y15-b", "Y16-a", "Y16-b", "Y16-c",
)
_MODULE = "acceptance/test_publish_remote_acceptance.py"
UNIT_CHECKS = {
    "Y11-a": f"{_MODULE}::test_y11_a_a_listing_that_disagrees_is_transport_incomplete_durably",
    "Y12-a": f"{_MODULE}::test_y12_a_a_crash_inside_push_leaves_the_mark_and_blocks_the_next_publish_durably",
    "Y12-b": f"{_MODULE}::test_y12_b_a_resume_after_the_mark_never_rereads_staging_durably",
    "Y12-c": f"{_MODULE}::test_y12_c_a_mark_disagreeing_with_its_export_fails_closed_durably",
    "Y13-a": f"{_MODULE}::test_y13_a_an_abandoned_transport_is_an_orphan_the_next_publish_supersedes_durably",
    "Y13-b": f"{_MODULE}::test_y13_b_an_orphan_named_by_an_abandoned_attempt_is_not_retired_durably",
    "Y13-c": f"{_MODULE}::test_y13_c_an_export_damaged_after_the_mark_closes_as_an_orphan_durably",
    "Y14-a": f"{_MODULE}::test_y14_a_a_stranded_marked_attempt_blocks_until_resumed_durably",
    "Y14-b": f"{_MODULE}::test_y14_b_an_attempt_without_a_mark_never_blocks_durably",
    "Y15-a": f"{_MODULE}::test_y15_a_a_crash_at_every_remote_step_resumes_to_one_binding_and_one_report_durably",
    "Y15-b": f"{_MODULE}::test_y15_b_a_remote_step_8_refusal_is_an_orphan_the_next_publish_names_durably",
    "Y16-a": f"{_MODULE}::test_y16_a_a_recipient_restores_admits_and_reads_the_current_publication_durably",
    "Y16-b": f"{_MODULE}::test_y16_b_sibling_publications_are_divergent_until_one_supersedes_both_durably",
    "Y16-c": f"{_MODULE}::test_y16_c_a_held_root_with_an_unreadable_record_file_refuses_capture_damaged_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-42 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )
```

The arms follow, one `_arm(...)` each, in `DECLARATION_UNITS` order inside `CUT42_ARMS = (…)`. Copy every `before` from the tree after Task 7 and check it with `source.count(before) == 1`. Each `after` must parse: run each sabotaged text through `ast.parse` via `n2_arms.py`'s sabotage helper before pinning.

| arm | module | before | after |
|---|---|---|---|
| Y11-a | `publish.py` | `    if listing != expected:` | `    if {name: listing.get(name) for name in expected} != expected:` |
| Y12-a | `publish.py` | `    write_create_only(a.op / "transport.v1", encode_mark(mark))` | `    pass` |
| Y12-b | `publish.py` | `    if (op / "transport.v1").is_file():` | `    if False:` |
| Y12-c | `publish.py` | `    return not _export_agrees(r, mark)` | `    return False` |
| Y13-a | `publication_doors.py` | `        return (entry.outcome.corpus_id, entry.outcome.marker)` | `        return None` |
| Y13-b | `publication_doors.py` | `                    orphans.add(outcome.orphan)  # possibly shared: an orphan that retires nothing (decision 3)` | `                    orphans.add(outcome.orphan)\n                    retired.update(intent.marker_tips)` |
| Y13-c | `publish.py` | `    return _evaluate_export(r, mark) != "validated"` | `    return False` |
| Y14-a | `publish.py` | `        if blocking:\n            raise PublicationRefused("publish-unfinished", tokens=blocking)` | `        if False:\n            raise PublicationRefused("publish-unfinished", tokens=blocking)` |
| Y14-b | `publish.py` | `        blocking = tuple(token for token in unfinished_attempts(writer, view, destination, seam) if (_op_dir(operations_root, token) / "transport.v1").is_file())` | `        blocking = tuple(unfinished_attempts(writer, view, destination, seam))` |
| Y15-a | `publish.py` | `    entries = (*entries, PublicationTransportEntry(r.subject, transported))` | `    entries = entries` |
| Y15-b | `publish.py` | `        remotely_revealed=remote, clock=a.clock, seam=a.seam, port=a.port,` | `        remotely_revealed=False, clock=a.clock, seam=a.seam, port=a.port,` |
| Y16-a | `transport.py` | `        dirnames[:] = sorted(dirnames)` | `        dirnames[:] = sorted(name for name in dirnames if name != "<CHAIN_DIR>")`, with Task 0's name |
| Y16-b | `publication_arrival.py` | `    return DivergentPublication(tips)` | `    return CurrentPublication(*tips[0])` |
| Y16-c | `publication_arrival.py` | `        raise PublicationReadingRefused("capture-damaged", corpus_id, ()) from caught` | `        return ()` |

Each arm's `asserts` text is its spec §10 row clause, in one sentence. Two arms are spelled for the one-edit form, as the spec's planning note records: Y12-a and Y16-c.

- [ ] **Step 2: The guard.** Copy `python/tests/acceptance/test_n2_cut41.py` to `python/tests/acceptance/test_n2_cut42.py`, then:
- import `CUT41_ARMS` and add it to `PRIOR_ARMS`;
- add `"python/tests/n2_arms_cut41.py": "<sha>"` to `FROZEN_PRIOR_CUT_FILES` (`git log -1 --format=%h -- python/tests/n2_arms_cut41.py`);
- set `FROZEN_CUT` to the cut-42 document, and `CUT42_FREEZE_COMMIT` and `CUT42_FROZEN_SHA256` from Task 0 Step 6;
- set `FROZEN_DECLARATION = "python/tests/n2_arms_cut42.py"` and its SHA-256;
- make the inventory test assert 14 units and 14 arms;
- make the freeze test assert `"**14 arms, 14 declaration units**" in current` and `'("cut41_acceptance.py",)' in current`.

The guard holds no `_LIVE_SABOTAGES` table: this lane moves no prior arm's pinned line (the Global Constraints). If `test_arm_staleness.py` reports one anyway, restore the line's spelling in the source. Never re-target a prior arm to fit this lane's code.

- [ ] **Step 3: The runner.** Write `python/tools/cut42_acceptance.py` as cut 41's, with:
- `cut=42`;
- `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut42"`;
- `PREFIX_RUNNERS = ("cut41_acceptance.py",)`;
- `PHASE_MODULES = ("test_publish_remote_acceptance.py", "test_n2_cut42.py")`;
- `declared_accounting` asserting `rows == {"Y11", "Y12", "Y13", "Y14", "Y15", "Y16"}` and `(arms, units) == (14, 14)`;
- on success, `print("guarantee rows exercised: 6 (6 newly closed: Y11, Y12, Y13, Y14, Y15, Y16)", flush=True)`.

- [ ] **Step 4: The recent-cut row.** In `test_recent_cut_acceptance.py`:
- add `import cut42_acceptance as cut42`;
- add `(cut42, 42, (14, 14, 6))` with id `"cut42"`;
- add:

```python
    if cut == 42:
        assert "guarantee rows exercised: 6 (6 newly closed: Y11, Y12, Y13, Y14, Y15, Y16)" in output
```

- [ ] **Step 5: Guard green, then the cut, harness-tracked**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
```

Then launch the runner with the Bash tool, `run_in_background: true`:

```bash
cd ~/d/beliefs/.worktrees/publish/python && cd "$(pwd -P)" && export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30 && set -o pipefail && uv run --frozen python tools/cut42_acceptance.py 2>&1 | tee ~/d/beliefs/.work/acceptance/cut42-runner.log
```

The harness starts the next turn when it exits. If the session must end first, the end-of-turn report names the background task and says that its log is the evidence. If the harness kills the run at its background cap (exit 144 and a truncated log; seen 2026-09-20 under an older harness), do not detach it. Run `tasks park <Task 8's id> "cut 42 runner killed at the background cap after <m> min; needs a harness-tracked way to run it" --reason environment`, and tell the user.

Read the log at exit. The expected tail has:
- three `[cut42 phase n/3]` lines;
- `declared arms: 14 (= 14 declaration units; 6 guarantee rows)`;
- the rows-exercised line;
- exit 0, with every arm `sound` and every check `resolved`.

A `stale` verdict means a `before` no longer matches: fix the declaration, never the source. A `vacuous` arm means its check passed under the sabotage. Rehome the check, or reshape the sabotage so that its check sees it, and record either change in the spec's §17.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 8's id> "N2 declarations, guard, runner, recent-cut row; cut 42 ran green"
tasks check && git add python/tests/n2_arms_cut42.py python/tests/acceptance/n2_arms_cut42.py python/tests/acceptance/test_n2_cut42.py python/tools/cut42_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut42): N2 declarations, guard, runner and the recent-cut row — Y11–Y16"
```

---

### Task 9: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §21)

- [ ] **Step 1: Run.**
  1. `export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30`, then `test -f "$SCIENCE_MM30_ROOT/state.json"`, and copy that file to the scratchpad.
  2. From `python/`, run `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight`, which must say `ok`. On a host-load refusal, run `tasks park <Task 9's id> "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`.
  3. Run `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`.
  4. `grep -n 'publish\|publication\|transport' python/tools/reproduction/*.py` shows what the driver reaches. Expected: nothing of this slice.

- [ ] **Step 2: Append §21** on §20's shape:
- §21.1, what changed: the remote publish act, the transport seam, the recipient's tip reading, none of them reached by the driver.
- §21.2, what the re-run reached: the same `NoBelief` payload, `rederived_equal: true`, and `state.json` byte-identical (the diff and both SHA-256s).
- §21.3, what it does not claim: mm30 publishes nothing.

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
tasks done <Task 9's id> "reproduction re-run under cut 42; nothing moves"
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under the remote publish act; nothing moves"
```

---

### Task 10: The results record, the re-rank, and the amendments

**Files:**
- Create: `docs/plans/<date>-conformance-cut-42-results.md`
- Modify:
  - the cut document (`**Status:**` only) and the spec (`**Status:**`);
  - the ledger, the roadmap, and `python/tools/roadmap_status.py`;
  - the layer design, the act-report design, the publication-records design, and `docs/designs/2026-09-22-publication-design.md` (status line);
  - `docs/plans/2026-09-23-conformance-cut-39-results.md` (a citing note only, below its frozen body);
  - `docs/guide/contracts-and-adoption.md`, `docs/guide/open-questions.md` and `README.md`;
  - tasks.

- [ ] **Step 1: The results record**, on cut 41's shape (`docs/plans/2026-09-25-conformance-cut-41-results.md`):
- **§1, what ran:** the runner's summary lines verbatim, and the per-unit table.
- **§2, accounting:** 14 arms, 14 units, 6 rows; Y11–Y16 closed; **210 of 237**.
- **§3, evidence:**
  - the spec's planning notes (§17), and every deviation from this plan;
  - the seven engine verdicts and `CHAIN_DIR`;
  - both permit inventories checked in both directions, with no new entry point;
  - the stale-arm probe clean, with every prior pinned line untouched;
  - Task 7's collected count, compared with the cut document's §4.
- **§4, the reproduction:** §21.
- **§5, `## Remaining boundary`:**
  - `publish` is discharged in full;
  - L1 stays under `persistence-cut`;
  - the spec's §13 items stay open: a recipient retiring a superseded corpus, a missing intermediate, and a recipient's world index over overlapping publications (`beliefs-81367e`).
- **§6, main integration:** filled at merge.
- **§7, execution rulings.**

- [ ] **Step 2: `roadmap_status.py`.** Add `42: ("conformance-cut-42-results §2", "Y11, Y12, Y13, Y14, Y15, Y16", ""),` after the cut-41 entry, then regenerate Appendix A. Expected: `Closed 210 of 237; open 27.`

- [ ] **Step 3: Ledger and roadmap.**
  - **Ledger `Current state`:** a built bullet for the remote publish act and the recipient's tip reading; Y11–Y16 closed; the totals. `publish` leaves `Current state` in the same commit that closes `beliefs-1a5157` (Task 11).
  - **Roadmap, rewritten whole:**
    - `**Ranked at:** cut 42`;
    - a `**Cut 42 (<date>) discharges the publish act, remote, and closes the boundary**` paragraph. It is the third and last slice of `publish`, off the path, and it re-ranks nothing on the path;
    - the `world-read` lane row: no open boundary, `publish` discharged at cuts 39, 40 and 42;
    - the boundary index without `publish`, and the next off-path row, `contract-cut` (spec §12);
    - the accounting paragraph and one reproduction sentence;
    - Appendix A pasted and Appendix B updated.
  - If `main` has gained another lane's results record since the freeze (`beliefs-fe7149`'s cut, say), rebase this commit onto it and re-rank against the higher-numbered record (roadmap rule 2).

- [ ] **Step 4: Amendments** (spec §12):
  - **Layer design §6.1.** Add dated notes, `> **Amended <date> (publish act, remote, conformance cut 42 — \`2026-09-26-publish-act-remote-design.md\`):**`, at the sentences they qualify: the remote export root (decision 7); step 7's seam, mark and `transport-incomplete` (decisions 1, 2, 4); step 8's orphans and the asymmetry (decision 3); the recovery table's split on the mark (§6); step 0's `publish-unfinished` (decision 6); step 9 keeping the export root (decision 8). **§6.3** gets `publication_tip` and `divergent-publication` (§7).
  - **Act-report design §2 and §6 item 3:** the transport entry and the remote lifecycle.
  - **Publication-records design §6:** a note on the fold's `PreBinding` orphan and `unfinished_attempts`.
  - **Cut 39 results §3.3:** Ruling 12 closed at cut 42, as a citing note below the frozen body.
  - **`docs/guide/open-questions.md`:** the spec's §13 items 1–3, the third citing `beliefs-81367e`.
  - **`2026-09-22-publication-design.md` status:** "Y11–Y16 closed at cut 42".

- [ ] **Step 5: Status lines, guide, README, tasks.**
  - The cut document's Status: `discharged <date> on the certified volume; results: …`.
  - The spec's Status: `discharged at conformance cut 42 on <date>; results: …`.
  - README: "through **cut 42**", its row's wording, and "The latest discharged boundary is cut 42".
  - The guide's cut-42 line as discharged.

```bash
tasks done <Task 10's id> "results record, re-rank at cut 42, amendments"
tasks check && git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut42): results record, re-rank at cut 42, Y11–Y16 closed"
```

---

### Task 11: Final review, gate, merge

- [ ] **Step 1: Whole-branch review.** Run `superpowers:requesting-code-review` over `git diff main...HEAD`, against the Global Constraints' decisions, the Review Focus lines and the cut document's §5. Land each fix as its own commit and record it in the results record §3.

- [ ] **Step 2: The gate, harness-tracked.** Launch with the Bash tool, `run_in_background: true`:

```bash
cd ~/d/beliefs/.worktrees/publish && cd "$(pwd -P)" && export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30 && set -o pipefail && just gate 2>&1 | tee ~/d/beliefs/.work/acceptance/cut42-gate.log
```

Read the log at exit. Expected: the pytest summary line with zero failures (memory `pytest-count-claims-need-the-summary-line`), and the TypeScript suite green.

- [ ] **Step 3: Close and merge**

```bash
tasks done <Task 11's id> "final review, gate green, merged"
tasks done beliefs-3ce305 "cut 42 discharged: Y11–Y16 — the remote publish act, orphans, publish-unfinished and publication_tip"
tasks done beliefs-1a5157 "publish discharged at cuts 39, 40 and 42: records, the local act, the remote act"
tasks check && git add docs tasks && git commit -m "chore(tasks): close beliefs-3ce305 and the publish lane — cut 42 discharged"
cd ~/d/beliefs && git merge --no-ff design/publish -m "merge: the publish act, remote — conformance cut 42"
```

Before the merge, `publish` leaves the ledger's `Current state` in the lane-close commit. Fill the results record's §6 in a `docs(cut42): record merged-main verification` commit on `main`. The lane is finished, so the worktree goes:
1. check that no host pointer resolves into it (`readlink -f ~/bin/* ~/.local/bin/* 2>/dev/null | grep -F .worktrees/publish` is empty);
2. `git worktree unlock .worktrees/publish`;
3. `git worktree remove .worktrees/publish`.

The execution rulings are already in the committed results record §7 (memory `execution-ledgers-are-durable-artifacts`).

---

## Self-review

**Spec coverage.**

| Spec section | Where it is built |
|---|---|
| §1 | the file map; Task 0's cut document |
| §2 decision 1 | Task 1 (seam), Task 5 (`_transport` compares) |
| §2 decision 2 | Task 5 (`_mark` before `_push`), Y12-a |
| §2 decision 3 | Task 3 (fold), Y13-b |
| §2 decision 4 | Tasks 2 and 5, Y11-a, Y13-a, Y13-c |
| §2 decision 5 | Task 5 (`_Remote`, `_resume_from_mark`, the export evaluation), Y12-b, Y12-c, Y13-c |
| §2 decision 6 | Tasks 3 and 5, Y14-a, Y14-b |
| §2 decision 7 | Task 5 (`_export_root`, `_sibling`) |
| §2 decision 8 | Task 5 (`_discard(r.op)`), Y15-a |
| §2 decision 9 | Task 6, Y16-b |
| §2 decision 10 | Task 1 (`materialize`), Y16-a |
| §3.1 | Task 1 |
| §3.2 | Task 5 (`_require_transport`, the removed cut-42 refusal) |
| §4.1 | Tasks 3, 4, 5 |
| §4.2 | Task 4 (codec), Task 5 (`_mark_corrupt`, `_export_agrees`), the extra three-check test in Task 7 |
| §4.3 | Task 5 (`_transport`, `_evaluate_export`, `evaluate_copy`), Task 0 (probes) |
| §4.4 and §4.5 | Task 5 (`_transport_and_bind`, `resume_publish`), Y15-a |
| §5.1 | Task 2 |
| §5.2 | Task 3 |
| §6 | Task 5; Y12-c, Y13-c, Y15-a, and the never-resumed test in Task 7 |
| §7.1 | Task 6, Y16-b, Y16-c |
| §7.2 | Task 7's `recipient_copy`, Y16-a |
| §8 | the Global Constraints' pinned lines, and cut 40's acceptance module rerun in Task 5 |
| §9 | the file map |
| §10 | Tasks 0 (bank) and 10 (close) |
| §11.1 | Tasks 1–6 |
| §11.2 | Task 7 |
| §11.3 and §11.4 | Task 8 |
| §12 | Task 10 |
| §13 | Task 10 (open questions; `beliefs-81367e`) |
| §14 | the cut document §7 and the results record §5 |
| §15 | Task 0 Step 5 (children), Task 11 (closing both tasks) |

**Placeholders.** Four places defer an exact spelling to the tree by instruction, each with the grep or file that settles it:
- `CHAIN_DIR` in Y16-a's `after`, from Task 0's printed top level;
- the `fake_seam` keyword in Task 3's absent-chain test, from `test_standing_at.py`;
- `head_artifact_bytes`'s name in Task 5's unit tests, from `anchors.py`;
- the `evaluate_copy` body if Task 0 chose `audit_log`.

**Type consistency.**
- **Seam:** `Transport.push(destination, files) -> TransportAbandoned | None`; `Transport.listing(destination, corpus_id) -> Mapping[str, str]`; `transport_files(container, corpus_id) -> dict[str, Path]`; `local_listing(files) -> dict[str, str]`; `listing_identity(listing) -> str`.
- **Report:** `Transported(corpus_id, listing)`; `TransportIncomplete(corpus_id, marker, reason)`; `PublicationTransportEntry(subject, outcome)`; kind `publication-transport`; types `transported` and `transport-incomplete`.
- **Fold:** `PreBinding(outcome, orphan=None)`; `unfinished_attempts(writer, view, destination, seam) -> tuple[str, ...]`.
- **Codec:** `TransportMark(event_token, destination, corpus_id, marker, artifact, records)`; `encode_mark`; `decode_mark`; `require_usable(...) -> tuple[Path, Destination]`.
- **Act:**
  - `publish(…, port=None, transport=None)` and `resume_publish(…, port=None, transport=None)`;
  - `_Remote(writer, resolver, opened, op, clock, seam, port, transport)`;
  - `_mark(a, corpus_id, artifact_identity) -> TransportMark`, `_push(r, files)`, `_verify(r, corpus_id)`;
  - `_transport(r, mark) -> Transported | TransportIncomplete`, `_transport_and_bind(r, mark, entries)`, `_resume_from_mark(r)`;
  - `_export_damaged(r, mark) -> bool`, `_export_agrees(r, mark) -> bool` (identity), `_marker_agrees(r, mark) -> bool` (content, after the evaluation);
  - `PublishUnresolved(event_token, "transport-mark-corrupt")`.
- **Root:** `evaluate_copy(dest_root, subject, observers) -> str` (the outcome, or `"unreadable"`); `export_chain_head(root) -> tuple[str, str] | None`.
- **Recipient:** `require_publication_layout(records) -> None`; `publication_tip(roots, view, destination)`; `CurrentPublication(corpus_id, marker)`; `DivergentPublication(tips)`; `PublicationReadingRefused(reason, corpus_id, refs=())`.
- **Errors:** `PublicationRefused(…, tokens=())`.
- **Spec names the plan renames**, each in the planning note: `publication_layout_refusal` → `require_publication_layout`; the spec's `(read: WorldView, …)` signature had already become `roots` at round 3.

**Review Focus.** Each of the five lines has a test in its owning task: Task 1 (1), Task 5 (2), Task 7 (3), Task 3 (4) and Task 6 (5).

## Plan review log

- 2026-09-27 — drafted from the spec approved at `e353c2d`. Found at planning and recorded in the spec's §17 (Task 0 Step 5):
  - the export evaluation is `evaluate_copy`, restore's evaluation without its grant, since `audit_log` needs a configured root;
  - an unreadable export file is `export-damaged`;
  - the layout rule is `require_publication_layout`, which keeps cut 40's Y10 pins;
  - the layout check runs before the address filter;
  - the four capture-damage types, two of them probed;
  - `require_usable` returns the destination;
  - the mark codec's home;
  - `_Remote`;
  - `tokens` on `PublicationRefused`;
  - `publish-unfinished` for remote destinations only;
  - the one-edit sabotages for Y12-a and Y16-c.

  Before anything relies on it, Task 0 pins that the evaluation validates an intact serviceable export, refuses one with a selected record deleted or altered, and writes nothing, and that the chain head reads a serviceable root. This keeps the user's round-3 condition that the chosen call be proven against both damages.
- 2026-09-27 — user review of the plan, round 1, two findings, both confirmed by the reviewer's probe against a real restored export; both taken:
  1. **A damaged selected record stranded the destination.** `_export_agrees` decoded every exported record, so an unreadable or undecodable selected record answered `transport-mark-corrupt` before step 7 could close it `export-damaged`. §4.2's checks are now identity only: the manifest, the sibling's hash, subject and chain head, and the one `publication` file by name. The export's content is judged by the evaluation, once on a resume and again before `push`. The marker's shape and selection count are read only after the evaluation validates (`_marker_agrees`). Y13-c now damages a selected record four ways (deleted, altered, unreadable, undecodable), and Task 0 probes the evaluation over the last two.
  2. **Corruption could escape as an exception.** The chain head raises `ChainStateInvalid` over a damaged chain, and a marker without `selection` raised `KeyError`. `root.py` now translates both engine types: `export_chain_head` answers `None`, and `evaluate_copy` answers `"unreadable"`. Task 0 prints the types, so each `except` names exactly what the engine raises. The marker's shape is checked (`publication_content_malformed`, `marker_consistent`) before its facet is read. The export-check test gains a `chain` case.

  Also from the review: long runs are harness-tracked (`run_in_background`), not detached. The Global Constraints and Tasks 8 and 11 changed accordingly.
- 2026-09-27 — user review of the plan, round 2: P1 resolved. One P2 finding, confirmed by the reviewer's probe, taken: **a missing chain escaped recovery.** Deleting `.#~chain`, or making it unreadable, raises `PreconditionRefused` from the chain head, which `export_chain_head` did not catch, so the resume raised instead of answering `transport-mark-corrupt`. Both `root.py` translations now catch `PreconditionRefused` (and `OSError`). Task 0 probes a deleted and an unreadable chain directory, and the evaluation over a deleted one. The export-check acceptance test gains a real `chain-deleted` case (31 cases).
