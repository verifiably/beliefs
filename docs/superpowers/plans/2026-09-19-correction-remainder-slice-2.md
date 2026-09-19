# Correction Remainder Slice 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the retraction a `snapshot` target arm naming a producer subject, read that subject's standing live from its covered corpora at import, audit, query and the evaluator's world read, and discharge C8 and C9 at conformance cut 34, closing the correction lifecycle.

**Architecture:** `stored.py` gains `SnapshotTarget` and the third arm's controlled shape; `corpus.py` gains the writer's `snapshot_resolver` port (resolution needs the world's retained epochs) and the one live fold `snapshot_standing`, which validates every retraction in a snapshot's history chain before trusting it; `world/read.validate_receipt` decides `retracted` for the producer receipt **before** availability (the retraction write itself moves the covered corpus's state, so any later check is unreachable); `import_epoch` refuses `retracted-snapshot` and `unreadable-standing`; `world/audit.py` and `audit.py` report through one `reported_receipt` helper; `WorldReadView.snapshot_standing()` folds the live captured records and `gather` refuses `ProducerSnapshotRetracted`, refuses damage, answers absence, and hands the bound snapshot's live history into the closure so a counter-retracted snapshot digests differently from a never-retracted one. Cut 34 freezes before code and discharges on the certified volume.

**Tech Stack:** Python 3.11+ (`uv run --frozen` from `python/`), pytest, `nodes.core`, the N2 harness (`python/tests/test_n2.py`, `n2_arms.py`, `arm_staleness.py`), `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-19-correction-remainder-slice-2-design.md` (approved for planning 2026-09-19 at `435e254` after three reviews, review log §17).

## Global Constraints

- **Baseline is `main` at `1958ec5`** (spec header). Work in the worktree `.worktrees/correction-remainder` (branch `design/correction-remainder`); every path below is relative to the repository root, and paths shown to the user carry the worktree prefix. Exports for a worktree on `WORK_ROOT`: `SCIENCE_MM30_ROOT` and every `SCIENCE_CUT*_ROOT` name the **main checkout's** `.work/…` (memory `worktree-on-work-root-needs-cut-root-exports`; ~190 `CapabilityUnavailable` failures are a missing export, not a regression).
- Frozen declarations (`n2_arms_cut*.py`) and frozen cut bodies (§§2–7 of every cut document) stay byte-exact; a pinned line a refactor moves is re-targeted in the live guard, never in the frozen file (spec §11.5). Cut 33's pinned `target_ref = target["ref"] if target["arm"] == "node" else target["dataset"]` line in `evaluation.py` stays verbatim inside the node/route branch.
- Snapshot standing is **live** and **per covered corpus, then union** (decisions 1, 3, §5); `retracted` is decided **before** availability (decision 4); a history chain member is validated with the write boundary's checks before it is folded (§5); an absent covered corpus answers `unavailable-corpus-absent`, a damaged one refuses `CorpusDamaged` (decision 7); the bound snapshot's live history enters `found` and the trace (decision 8); the scope loop never takes a snapshot arm (decision 8); `subject_kind` is closed to `("producer",)` (decision 2); no `retracts` or `succeeded-by` edge for the arm (decision 9).
- `derive.RECEIPT_OUTCOMES` and `audit.SNAPSHOT_STATES` each gain `"retracted"` **last**; `ReceiptOutcome.validated` is unchanged; no derivation rule or implementation identity moves (decision 11 — Task 4 verifies by validating a pre-slice epoch); both `CONTRACT.yaml` copies are unchanged and their identities equal before and after (§12 — Task 1 verifies).
- `science.belief.v1`'s answers over every existing fixture are unchanged; P1–P9 green at every commit.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row(s) or invariant(s) it serves.

---

## File map

| File | Responsibility |
| --- | --- |
| `python/src/beliefs/errors.py` | `ProducerSnapshotRetracted`; `EpochImportRefused.reason` gains `"retracted-snapshot"`, `"unreadable-standing"` (Task 1) |
| `python/src/beliefs/stored.py` | `SnapshotTarget`, `RETRACTION_TARGET_ARMS`, `SNAPSHOT_SUBJECT_KINDS`, `retraction_node`'s third arm with no `retracts`/`succeeded-by` edge (Task 1) |
| `python/src/beliefs/corpus.py` | `_validated_retraction_target` and `CorpusWriter._validated_retraction` accept the arm (Task 1); `SnapshotResolver`, `CorpusWriter(snapshot_resolver=)`, `_resolve_retraction_target`'s eligibility-only snapshot branch, `_resolve_snapshot_target`, the `retract` and import call sites, `standing_in_local_view`/`corpus_check` docstrings (Task 2); `SnapshotStanding`, `snapshot_standing` (Task 3) |
| `python/src/beliefs/world/epoch.py` | `_retraction_target` keys the arm by identity (Task 1); `_member_for` moves here; `RetainedSnapshots` (Task 2) |
| `python/src/beliefs/session/__init__.py` | `open_session(snapshot_resolver=)` hands the port to the writer factory (Task 2) |
| `python/src/beliefs/world/derive.py` | `RECEIPT_OUTCOMES` gains `"retracted"` (Task 4) |
| `python/src/beliefs/world/read.py` | `_snapshot_standing`, the phase in `validate_receipt`, `reported_receipt`; `_member_for` re-exported (Task 4) |
| `python/src/beliefs/world/importing.py` | the two new refusals (Task 4) |
| `python/src/beliefs/world/audit.py` | `SNAPSHOT_STATES`, `_reduce`, `reported_receipt` in both reports (Task 4) |
| `python/src/beliefs/audit.py` | `_world_findings`: `reported_receipt`; snapshot-arm resolution over `captured_records` (Task 4) |
| `python/src/beliefs/world/view.py` | `WorldReadView.snapshot_standing()` (Task 5) |
| `python/src/beliefs/evaluation.py` | `gather`'s world block and the four arm-dependent sites (Task 5) |
| `python/tests/test_snapshot_retraction.py` (new), `test_world_standing.py`, `test_world_epoch_audit.py`, `test_world_import_epoch.py`, `test_world_audit.py`, `test_local_standing.py` | unit coverage (Tasks 1–5) |
| `python/tests/acceptance/test_snapshot_retraction_acceptance.py`, `python/tests/n2_arms_cut34.py`, `python/tests/acceptance/n2_arms_cut34.py`, `python/tests/acceptance/test_n2_cut34.py`, `python/tools/cut34_acceptance.py` | the seventeen declaration units, the sabotages, the guard, the runner (Task 7) |
| `docs/designs/2026-09-19-conformance-cut-34.md`, `docs/plans/2026-09-19-conformance-cut-34-results.md`, the ledger, the roadmap, the guide, `README.md`, the correction-lifecycle and world-index slice-2 designs (dated notes), the reproduction record §13 | freeze, discharge, amendments (Tasks 0, 6, 8) |

---

### Task 0: Freeze cut 34 and file the tasks

**Files:**
- Create: `docs/designs/2026-09-19-conformance-cut-34.md`
- Modify: `README.md` (the design table gains the cut-34 row, status "frozen"; "Every conformance cut through **cut 33**" stays until discharge), `docs/guide/contracts-and-adoption.md` (`sources` gains the cut document; after the cut-33 line: "Cut 34 is frozen and not yet discharged: correction-remainder slice 2, the snapshot target (C8, C9; `../designs/2026-09-19-conformance-cut-34.md`)")
- Tasks: filed at the planning commit (Step 3); `tasks start` the Task-0 step child

**Interfaces:**
- Produces: `CUT34_FREEZE_COMMIT` and `CUT34_FROZEN_SHA256`, pinned by Task 7's guard; the step-child ids every later commit closes.

- [ ] **Step 1: Confirm the baseline and the lane**

Run `git -C /mnt/ssd/Dropbox/beliefs log --oneline -1`; `main` is at `1958ec5` or a descendant touching none of `stored.py`, `corpus.py`, `evaluation.py`, `world/{derive,epoch,read,view,audit,importing}.py`, `audit.py`, `session/__init__.py`. If it moved, `git merge --ff-only main` in the worktree (or rebase), re-read spec §1's baseline claims against the tree and record any drift in spec §17. `tasks prime` inside the worktree: `beliefs-aa27da` and `beliefs-d79ca4` are `doing`, owned by this branch; the roadmap's lane table shows `mutation` as the only open kernel lane.

- [ ] **Step 2: Claim the cut number**

`git worktree list`, then for each worktree `ls <wt>/docs/designs/*conformance-cut-3[4-9]*.md` and `for b in $(git branch --format='%(refname:short)'); do git ls-tree -r --name-only $b docs/designs | grep -i 'cut-3[4-9]'; done`. Nothing may match (spec §11.4 scanned 2026-09-19; re-scan now). If something does, the number is the next unclaimed one and every `34` below moves with it. The highest discharged runner is `python/tools/cut33_acceptance.py`.

- [ ] **Step 3: The tasks are filed**

Filed at the planning commit so `tasks check` links every heading: `beliefs-d79ca4` carries the spec and this plan; its step children are `beliefs-e60614` (Task 0), `beliefs-f568c9` (1), `beliefs-44343a` (2), `beliefs-5f65eb` (3), `beliefs-a5d72a` (4), `beliefs-e2f187` (5), `beliefs-fbd67f` (6), `beliefs-fa1b95` (7), `beliefs-dd8b91` (8). Each `<taskN-id>` below is the id in this list.

`tasks start <step>` before each task; `tasks done <step> "<what landed>"` in its commit.

- [ ] **Step 4: Write and freeze the cut document**

`docs/designs/2026-09-19-conformance-cut-34.md` on cut 33's shape (`docs/designs/2026-09-16-conformance-cut-33.md`): `**Status:**` "frozen 2026-09-19, before implementation; C8 and C9 are open"; §1 what this cut is (spec §1 condensed; the slice design cited by its `docs/superpowers/specs/` path); §2 the boundary — the file map's surfaces; §3 selection — the seventeen units, single-homed:

| unit | row | what it reads |
|---|---|---|
| C8-a | C8 | `import_epoch` of a carrier whose producer subject is retracted → `retracted-snapshot`, no directory |
| C8-b | C8 | `audit_epochs`: the producer receipt `retracted`, the verdict `retracted`, no finding names it |
| C8-c | C8 | `snapshot_state(S)` `retracted`; `snapshot_state(S')` `unchecked` (receipt `unresolvable`); `checked` for `S'` only between build and retraction |
| C8-d | C8 | mount negative: `World.admit` writes nothing under `epochs/`, validates nothing |
| C9-a | C9 | narrowing: `gather` bound to the old epoch refuses `ProducerSnapshotRetracted` |
| C9-b | C9 | bound to the new: proceeds, digest moves, `closure()["producer_snapshot"] == S'` |
| C9-c | C9 | old members and receipts byte-identical across the retraction |
| C9-d | C9 | nothing resolves through the retraction to its successor (two mismatch negatives) |
| BI-1 | — | a snapshot retraction outside the target's coverage is refused at authoring; inside is admitted |
| BI-2 | — | a writer without the port refuses the arm |
| BI-3 | — | `retracted` precedes availability (the moved state does not hide it) |
| BI-4 | — | a counter-retraction restores: not retracted, `gather` proceeds, nothing stored on the target |
| BI-5 | — | an older snapshot's retraction is out of the closure |
| BI-6 | — | the raw-write disposition: `audit_world` reports `retraction-target-invalid` from `captured_records`; `corpus_check` reports nothing |
| BI-7 | — | history is in the digest: counter-retracted ≠ never-retracted; `found` carries the pair |
| BI-8 | — | an unreadable counter-retraction refuses rather than restores, at `gather`, import and the reports (which still return) |
| BI-9 | — | a rebuild restores nothing and duplicates nothing |

§4 accounting — "**17 declaration units**, eight against rows and nine boundary invariants; C8 closes, C9 closes; the boundary closes"; §5 N2 and acceptance obligations — spec §11.3's table; `PREFIX_RUNNERS = ("cut33_acceptance.py",)`; §6 second reader — the two things to check: that C9-a/C9-b read through `gather` with the identity supplied by the caller (no test-side selection of the epoch), and that BI-7's two digests differ over the *same* epoch; §7 limitations — spec §14 restated. Then `cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green (the newest *results* record is cut 33's, so a frozen 34 passes).

```bash
tasks done beliefs-e60614 "cut 34 frozen"
git add docs/designs/2026-09-19-conformance-cut-34.md README.md docs/guide/contracts-and-adoption.md tasks
git commit -m "docs(cut): freeze conformance cut 34, correction-remainder slice 2"
git rev-parse HEAD                                          # CUT34_FREEZE_COMMIT
sha256sum docs/designs/2026-09-19-conformance-cut-34.md     # CUT34_FROZEN_SHA256
```

---

### Task 1: Errors, the stored shape, the arm's validation, the discovery key

**Files:**
- Modify: `python/src/beliefs/errors.py:125-137` (`EpochImportRefused.reason`), after `:1160` (`ProducerSnapshotRetracted`)
- Modify: `python/src/beliefs/stored.py:975-987` (targets), `:1225-1300` (`retraction_node`)
- Modify: `python/src/beliefs/corpus.py:1100-1113` (`_validated_retraction_target`), `:2960-2996` (`CorpusWriter._validated_retraction`)
- Modify: `python/src/beliefs/world/epoch.py:1254-1266` (`_retraction_target`)
- Test: `python/tests/test_snapshot_retraction.py` (new)

**Interfaces:**
- Produces: `stored.SnapshotTarget(subject_kind: str, subject_identity: str)`; `stored.RETRACTION_TARGET_ARMS = ("node", "route", "snapshot")`; `stored.SNAPSHOT_SUBJECT_KINDS = ("producer",)`; `errors.ProducerSnapshotRetracted(identity: str)`; `EpochImportRefused.reason` literal widened. Tasks 2–5 and 7 consume all of these.

- [ ] **Step 1: The failing tests**

```python
# python/tests/test_snapshot_retraction.py
"""The snapshot target arm (correction-remainder slice 2)."""
from __future__ import annotations

import pytest
from authority import ACTOR
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import CorpusWriter, _validated_retraction_target
from beliefs.errors import MalformedRecord

S = "a" * 64
S2 = "b" * 64


def snapshot_retraction(identity: str = S, *, successor: str | None = None, token: str = "t1"):
    return stored.retraction_node(
        title=token,
        target=stored.SnapshotTarget("producer", identity),
        reason="authored-error",
        rationale="the snapshot's coverage was too wide",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
        successor=successor,
    )


class TestTheStoredShape:
    def test_the_facet_carries_the_arm_and_no_target_edge(self):
        node = snapshot_retraction(successor=S2)
        facet = node.facets[stored.RETRACTION_FACET]
        assert facet["target"] == {"arm": "snapshot", "subject_kind": "producer", "subject_identity": S}
        assert facet["successor"] == S2
        predicates = {r.predicate for r in node.relations}
        assert predicates == {stored.GROUNDED_IN}

    def test_the_identity_moves_with_the_subject_and_the_successor(self):
        assert snapshot_retraction().id != snapshot_retraction(S2).id
        assert snapshot_retraction().id != snapshot_retraction(successor=S2).id

    @pytest.mark.parametrize("kind", ["retraction-enumeration", "certification-enumeration", "coreference-reduction", ""])
    def test_only_the_producer_kind_constructs(self, kind):
        with pytest.raises(MalformedRecord):
            stored.retraction_node(
                title="t", target=stored.SnapshotTarget(kind, S), reason="authored-error", rationale="r",
                grounds=("verification:v1",), actor=ACTOR, event_token="t",
            )

    @pytest.mark.parametrize("identity", ["a" * 63, "A" * 64, "g" * 64, ""])
    def test_the_identity_is_sixty_four_lower_hex(self, identity):
        with pytest.raises(MalformedRecord):
            stored.retraction_node(
                title="t", target=stored.SnapshotTarget("producer", identity), reason="authored-error",
                rationale="r", grounds=("verification:v1",), actor=ACTOR, event_token="t",
            )

    def test_the_arm_set_is_named_once(self):
        assert stored.RETRACTION_TARGET_ARMS == ("node", "route", "snapshot")
        assert stored.SNAPSHOT_SUBJECT_KINDS == ("producer",)


class TestTheValidatedTarget:
    def test_the_arm_validates_and_the_controlled_shape_holds(self):
        node = snapshot_retraction()
        assert _validated_retraction_target(node)["arm"] == "snapshot"
        assert CorpusWriter._validated_retraction(node)["target"]["subject_identity"] == S

    def test_an_extra_or_missing_field_is_malformed(self):
        node = snapshot_retraction()
        node.facets[stored.RETRACTION_FACET]["target"]["ref"] = "x"
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)
        node = snapshot_retraction()
        del node.facets[stored.RETRACTION_FACET]["target"]["subject_kind"]
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)

    def test_a_retracts_edge_fails_the_controlled_shape(self):
        node = snapshot_retraction()
        node.relations.append(Relation(source=node.id, predicate=stored.RETRACTS, target=f"producer-snapshot:{S}"))
        stored.stamp_semantic_identity(node)
        with pytest.raises(MalformedRecord):
            CorpusWriter._validated_retraction(node)


def test_the_discovery_map_keys_the_arm_by_identity():
    from beliefs.world.epoch import _retraction_target

    assert _retraction_target(snapshot_retraction().facets[stored.RETRACTION_FACET]) == S
```

If `stored.stamp_semantic_identity` does not exist under that name, use the helper `test_world_view_acceptance.py:328` uses (`grep -n "stamp_semantic_identity" python/tests/acceptance/test_world_view_acceptance.py`).

- [ ] **Step 2: Run to verify failure**

`cd python && uv run --frozen pytest tests/test_snapshot_retraction.py -q` — fails with `AttributeError: ... SnapshotTarget`.

- [ ] **Step 3: Errors**

`errors.py`: widen the literal at `:130` to
`Literal["malformed-carrier", "foreign-world", "malformed-receipt", "refuted-receipt", "retracted-snapshot", "unreadable-standing"]`. After `ProducerSnapshotMismatch`:

```python
class ProducerSnapshotRetracted(RecordError):
    """A world read was handed the bound epoch's producer-snapshot identity,
    and a standing snapshot-arm retraction in a covered corpus names it
    (correction-remainder slice 2, decision 6). The computation is refused,
    not performed; nothing enters a closure."""

    def __init__(self, identity: str) -> None:
        super().__init__(f"the supplied producer snapshot {identity!r} is retracted in its covered corpora")
        self.identity = identity
```

- [ ] **Step 4: The stored shape**

`stored.py` after `RouteTarget`:

```python
@dataclass(frozen=True)
class SnapshotTarget:
    """An epoch subject named by kind and identity (slice 2 §3). The snapshot
    has no stored record, so neither arm above can name it."""

    subject_kind: str
    subject_identity: str


RETRACTION_TARGET_ARMS: tuple[str, ...] = ("node", "route", "snapshot")
SNAPSHOT_SUBJECT_KINDS: tuple[str, ...] = ("producer",)
_LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")
```

(`import re` at the top if absent.) In `retraction_node`, widen the annotation to `NodeTarget | RouteTarget | SnapshotTarget` and replace the `else: raise` with:

```python
    elif isinstance(target, SnapshotTarget):
        if target.subject_kind not in SNAPSHOT_SUBJECT_KINDS:
            raise MalformedRecord(f"a snapshot target's subject kind is one of {SNAPSHOT_SUBJECT_KINDS}")
        if type(target.subject_identity) is not str or not _LOWER_HEX_64.fullmatch(target.subject_identity):
            raise MalformedRecord("a snapshot target's subject identity is 64 lower-hex characters")
        target_mapping = {
            "arm": "snapshot",
            "subject_kind": target.subject_kind,
            "subject_identity": target.subject_identity,
        }
        target_ref = None
    else:
        raise MalformedRecord("a retraction target arm is NodeTarget, RouteTarget or SnapshotTarget")
```

and the relations block:

```python
    relations = [] if target_ref is None else [Relation(source=node_id, predicate=RETRACTS, target=target_ref)]
    relations.extend(Relation(source=node_id, predicate=GROUNDED_IN, target=ground) for ground in grounds_list)
    if successor is not None and target_ref is not None:
        relations.append(Relation(source=node_id, predicate=SUCCEEDED_BY, target=successor))
```

- [ ] **Step 5: The validation**

`corpus.py:1100-1113`:

```python
def _validated_retraction_target(record: Node) -> dict:
    facet = record.facets.get(stored.RETRACTION_FACET)
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{record.id}: malformed retraction facet")
    target = facet.get("target")
    if not isinstance(target, dict) or target.get("arm") not in stored.RETRACTION_TARGET_ARMS:
        raise MalformedRecord(f"{record.id}: malformed retraction target arm")
    target_fields = {
        "node": {"arm", "ref", "resolved", "content_identity"},
        "route": {"arm", "dataset", "resolved", "content_identity", "route_identity"},
        "snapshot": {"arm", "subject_kind", "subject_identity"},
    }[target["arm"]]
    if set(target) != target_fields or not all(type(target[field]) is str and target[field] for field in target):
        raise MalformedRecord(f"{record.id}: malformed retraction target")
    if target["arm"] == "snapshot":
        if target["subject_kind"] not in stored.SNAPSHOT_SUBJECT_KINDS:
            raise MalformedRecord(f"{record.id}: malformed retraction target: subject kind outside the closed set")
        if not stored._LOWER_HEX_64.fullmatch(target["subject_identity"]):
            raise MalformedRecord(f"{record.id}: malformed retraction target: subject identity is not 64 lower hex")
    return target
```

`CorpusWriter._validated_retraction` (`:2975-2984`): widen `target_value`'s annotation to `stored.NodeTarget | stored.RouteTarget | stored.SnapshotTarget` and make the branch three-way:

```python
        if target["arm"] == "node":
            target_value = stored.NodeTarget(target["ref"], target["resolved"], target["content_identity"])
        elif target["arm"] == "route":
            target_value = stored.RouteTarget(
                target["dataset"], target["resolved"], target["content_identity"], target["route_identity"]
            )
        else:
            target_value = stored.SnapshotTarget(target["subject_kind"], target["subject_identity"])
```

`epoch._retraction_target`:

```python
    target = cast(Mapping[str, str], facet["target"])
    if target["arm"] == "node":
        return target["ref"]
    if target["arm"] == "route":
        return target["route_identity"]
    return target["subject_identity"]
```

and extend the docstring with one sentence: "A snapshot-arm retraction names a subject identity, disjoint from every ref and every route identity by namespace, so the key is the identity itself (slice 2 §6)."

- [ ] **Step 6: Run, then the contract-identity check**

`uv run --frozen pytest tests/test_snapshot_retraction.py tests/test_retract.py tests/test_local_standing.py tests/test_world_build.py -q` green. Then the §12 claim: `git stash -q && uv run --frozen python -c "from beliefs.profile import *; ..."` is not needed — the contract identity is the file's digest; run `sha256sum contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml` and confirm both equal their values at `1958ec5` (`git show 1958ec5:contracts/science/CONTRACT.yaml | sha256sum`). Record the two digests in the commit message.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-f568c9 "SnapshotTarget, the third arm's controlled shape and validation, the discovery key"
git add python/src/beliefs/errors.py python/src/beliefs/stored.py python/src/beliefs/corpus.py python/src/beliefs/world/epoch.py python/tests/test_snapshot_retraction.py tasks
git commit -m "feat(correction): the snapshot target arm — stored shape and validation (C8, C9)"
```

---

### Task 2: The write boundary — the resolver port, `RetainedSnapshots`, the session

**Files:**
- Modify: `python/src/beliefs/corpus.py:1694-1730` (`CorpusWriter.__init__`), `:2801-2848` (`_resolve_retraction_target`), `:2314-2325` (the `retract` call site), `:2733-2738` (the import call site), `:996-1010` (`standing_in_local_view` docstring), `:1297` (`corpus_check` docstring)
- Modify: `python/src/beliefs/world/epoch.py` (after `_retained_identities_locked`, `:1752`): `_member_for`, `RetainedSnapshots`
- Modify: `python/src/beliefs/world/read.py:343-354` (`_member_for` becomes a re-export)
- Modify: `python/src/beliefs/session/__init__.py:120-129` (`open_session` and the factory)
- Test: `python/tests/test_snapshot_retraction.py` (extended), `python/tests/test_local_standing.py` (one test)

**Interfaces:**
- Consumes: `SnapshotTarget`, `RETRACTION_TARGET_ARMS`, `SNAPSHOT_SUBJECT_KINDS` (Task 1).
- Produces: `corpus.SnapshotResolver` (Protocol: `retained(subject_kind: str) -> Mapping[str, tuple[str, ...]]`); `CorpusWriter(..., snapshot_resolver: SnapshotResolver | None = None)`; `CorpusWriter._resolve_snapshot_target(record: Node, corpus_id: str) -> None`; `epoch.RetainedSnapshots(world)`; `epoch._member_for(kind) -> str`; `open_session(..., snapshot_resolver=None)`. Tasks 3, 4, 5, 7 consume.

- [ ] **Step 1: The failing tests**

Append to `test_snapshot_retraction.py`:

```python
from pathlib import Path
from types import MappingProxyType

from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder
from test_world_build import ALPHA, BETA
from test_world_receipts import hold_shipped, publish, published_world

from beliefs.errors import RetractionTargetIneligible, RetractionTargetUnresolvable, ValidationRefused
from beliefs.world import registry
from beliefs.world.epoch import RetainedSnapshots


class StubResolver:
    def __init__(self, retained):
        self._retained = retained

    def retained(self, subject_kind):
        assert subject_kind == "producer"
        return MappingProxyType(dict(self._retained))


def writer_at(root: Path, profile=BASE, *, resolver=None) -> CorpusWriter:
    """A manifest-bearing writer (ReadView.corpus_id reads one)."""
    from authority import FULL

    writer = CorpusWriter(
        root, DefaultExecutor, authority=FULL, profile=profile,
        operation_port=OperationRecorder(root, authority=FULL, profile=profile), snapshot_resolver=resolver,
    )
    writer.adopt_manifest(profile=pins_for(profile))
    return writer


class TestTheWriteBoundary:
    def test_a_writer_without_the_port_refuses_the_arm(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        with pytest.raises(RetractionTargetUnresolvable, match="reaches none"):
            writer.operations.retract(snapshot_retraction())

    def test_an_unretained_identity_refuses(self, tmp_path):
        writer = writer_at(tmp_path / "c", resolver=StubResolver({}))
        with pytest.raises(RetractionTargetUnresolvable, match="no retained epoch carries"):
            writer.operations.retract(snapshot_retraction())

    def test_a_corpus_outside_the_coverage_refuses_naming_it(self, tmp_path):
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: ("0" * 32,)}))
        with pytest.raises(RetractionTargetUnresolvable, match=f"corpus {writer.corpus_id} is outside the coverage"):
            writer.operations.retract(snapshot_retraction())

    def test_a_successor_must_be_retained_and_not_the_target(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        cid = writer.corpus_id
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,)}))
        with pytest.raises(RetractionTargetUnresolvable, match="successor"):
            writer.operations.retract(snapshot_retraction(successor=S2))
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,), S2: (cid,)}))
        with pytest.raises(ValidationRefused, match="not its target"):
            writer.operations.retract(snapshot_retraction(successor=S))

    def test_the_happy_path_writes_one_record(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        cid = writer.corpus_id
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,), S2: (cid,)}))
        before = len(list(writer.read_view.iter_stored()))
        minted = writer.operations.retract(snapshot_retraction(successor=S2))
        assert minted.kind == "retraction"
        assert len(list(writer.read_view.iter_stored())) == before + 1

    def test_a_snapshot_kind_outside_the_closed_set_is_ineligible_everywhere(self, tmp_path):
        node = snapshot_retraction()
        node.facets[stored.RETRACTION_FACET]["target"]["subject_kind"] = "coreference-reduction"
        # shape validation refuses first; the eligibility refusal is reached through the static method
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)


class TestRetainedSnapshots:
    def test_two_epochs_of_different_coverage_answer_with_their_coverage(self, tmp_path):
        world, bindings, _roots, wide = published_world(tmp_path, (ALPHA, BETA))
        narrow = publish(world, (ALPHA,), bindings)
        retained = RetainedSnapshots(world).retained("producer")
        wide_id = wide.receipts["producer-receipt.yaml"].subject_identity
        narrow_id = narrow.receipts["producer-receipt.yaml"].subject_identity
        assert wide_id != narrow_id
        assert retained[wide_id] == tuple(sorted((ALPHA, BETA)))
        assert retained[narrow_id] == (ALPHA,)

    def test_a_world_with_no_epochs_answers_empty_and_an_unknown_kind_refuses(self, tmp_path):
        from test_world_receipts import sample_corpora, world_over

        world = world_over(tmp_path, sample_corpora(tmp_path, (ALPHA,)))
        assert dict(RetainedSnapshots(world).retained("producer")) == {}
        with pytest.raises(ValueError):
            RetainedSnapshots(world).retained("weather")
```

And in `test_local_standing.py`, one test (find its `seed`/writer helpers at the top of that module and use them):

```python
def test_a_snapshot_arm_retraction_is_a_vertex_and_never_refuses_the_local_read(tmp_path):
    """slice 2 §4: standing_in_local_view has no world and must not refuse for lack of one."""
    from test_snapshot_retraction import S, snapshot_retraction
    from fixtures_cut4 import raw_write

    view, target = seeded_view_and_target(tmp_path)   # whatever this module's fixture is named; the pattern of test_stale_retraction_refuses_the_whole_evaluation
    raw_write(view_root(view), snapshot_retraction())
    fresh = ReadView.opened_at(view_root(view))
    assert standing_in_local_view(fresh, target.id) is True
```

Adapt the two helper names to what `test_local_standing.py` actually provides (`grep -n "^def " python/tests/test_local_standing.py`); the assertion is the contract.

- [ ] **Step 2: Run to verify failure**

`uv run --frozen pytest tests/test_snapshot_retraction.py tests/test_local_standing.py -q` — `TypeError: unexpected keyword 'snapshot_resolver'`, `ImportError: RetainedSnapshots`.

- [ ] **Step 3: `_member_for` moves; `RetainedSnapshots`**

`epoch.py`, after `_retained_identities_locked`:

```python
def _member_for(kind: str) -> str:
    """The §6.1 member the named receipt kind is written to.

    A kind outside §7.5's four is a caller error and refuses here: inventing a
    fifth outcome for it would answer a question the specification does not
    ask. Lives here rather than in `read` because `read` imports this module.
    """
    for member, declared in RECEIPT_KINDS.items():
        if declared == kind:
            return member
    raise ValueError(f"{kind!r} is not one of the four receipt kinds {sorted(RECEIPT_KINDS.values())}")


class RetainedSnapshots:
    """The writer's snapshot resolver over one world's retained epochs
    (slice 2 §4). One scan under the barrier; the mapping is built outside it."""

    def __init__(self, world: registry.World) -> None:
        self._world = world

    def retained(self, subject_kind: str) -> Mapping[str, tuple[str, ...]]:
        member = _member_for(subject_kind)
        with registry._locked_barrier(self._world) as world_root:
            carriers = _retained_receipt_bindings_locked(world_root)
        retained: dict[str, tuple[str, ...]] = {}
        for carrier in carriers:
            if carrier.member != member or carrier.subject_identity is None or carrier.corpus_states is None:
                continue  # a receipt-contract fault is the audit's to report, not a name to resolve against
            coverage = tuple(sorted(corpus_id for corpus_id, _state in carrier.corpus_states))
            if carrier.subject_identity in retained and retained[carrier.subject_identity] != coverage:
                raise EpochMalformed(
                    f"{carrier.packaging_identity}: subject {carrier.subject_identity} is retained under two "
                    "coverages; the identity digests the coverage, so one of the carriers is not what it claims"
                )
            retained[carrier.subject_identity] = coverage
        return MappingProxyType(retained)
```

`read.py:343-354` becomes `_member_for = epoch._member_for` with a one-line comment ("moved to `epoch` for `RetainedSnapshots`; every `read._member_for` caller is unchanged"). `world/audit.py:107` calls `read._member_for` — unchanged.

- [ ] **Step 4: The port and the writer's resolution**

`corpus.py`, near `CoordinationResolver`'s import or the module's protocols:

```python
class SnapshotResolver(Protocol):
    """What a writer needs to resolve a snapshot-arm target (slice 2 §4): the
    world's retained subjects of one kind, each with its covered corpus ids."""

    def retained(self, subject_kind: str) -> Mapping[str, tuple[str, ...]]: ...
```

`CorpusWriter.__init__`: add `snapshot_resolver: SnapshotResolver | None = None,` after `coordination_resolver` and `self._snapshot_resolver = snapshot_resolver`. In `_resolve_retraction_target`, before the `route` fallthrough (after the node branch's `return`):

```python
        if target["arm"] == "snapshot":
            if target["subject_kind"] not in stored.SNAPSHOT_SUBJECT_KINDS:
                raise RetractionTargetIneligible(
                    f"{record.id}: snapshot subject kind is outside {stored.SNAPSHOT_SUBJECT_KINDS}"
                )
            return  # retained-epoch resolution is the writer's (_resolve_snapshot_target); a view has no world
```

New instance method after it:

```python
    def _resolve_snapshot_target(self, record: Node, corpus_id: str) -> None:
        """Slice 2 §4: a snapshot arm resolves iff a retained epoch carries the
        identity and this corpus is in that snapshot's coverage; a successor
        must be retained and must not be the target."""
        target = _validated_retraction_target(record)
        if target["arm"] != "snapshot":
            return
        if type(corpus_id) is not str:
            raise TypeError("a snapshot target is resolved against the writing corpus's id")
        if self._snapshot_resolver is None:
            raise RetractionTargetUnresolvable(
                f"{record.id}: a snapshot target needs the world's retained epochs, and this writer reaches none"
            )
        retained = self._snapshot_resolver.retained(target["subject_kind"])
        identity = target["subject_identity"]
        if identity not in retained:
            raise RetractionTargetUnresolvable(f"{record.id}: no retained epoch carries producer snapshot {identity}")
        if corpus_id not in retained[identity]:
            raise RetractionTargetUnresolvable(
                f"{record.id}: corpus {corpus_id} is outside the coverage of producer snapshot {identity}"
            )
        successor = record.facets[stored.RETRACTION_FACET].get("successor")
        if successor is not None:
            if successor == identity:
                raise ValidationRefused(f"{record.id}: a snapshot retraction's successor is not its target")
            if successor not in retained:
                raise RetractionTargetUnresolvable(
                    f"{record.id}: successor {successor} is not a retained producer snapshot"
                )
```

Call sites. In `retract` (`:2314-2325`), replace the `lookup_ref`/try block with:

```python
            target = facet["target"]
            if target["arm"] == "snapshot":
                self._resolve_retraction_target(record, self._view)
                self._resolve_snapshot_target(record, self.corpus_id)
            else:
                target_ref = target["resolved"]
                lookup_ref = target["ref"] if target["arm"] == "node" else target["dataset"]
                try:
                    self._resolve_retraction_target(record, self._view)
                except RetractionTargetUnresolvable:
                    if self._view.resolve(lookup_ref) is None:
                        try:
                            self._view.get(target_ref)
                        except RefError as caught:
                            raise RelocationTargetMissing(
                                f"{target_ref}: the target no longer resolves in this corpus; a concurrent move "
                                "or deletion removed it (world-changing families §3.6)"
                            ) from caught
                    raise
```

In the import path (`:2733-2738`) add `self._resolve_snapshot_target(record, self.corpus_id)` after `self._resolve_retraction_target(record, union)`, inside the same `try`.

Docstrings: `standing_in_local_view` — append "A snapshot-arm retraction is a vertex here: it names no node, and its retained-epoch resolution is the writer's and the world audit's (slice 2 §4)." `corpus_check` (`:1297`) — append "Snapshot-arm retractions are checked for shape and eligibility only; retained-ness needs the world and is `audit_world`'s (slice 2 §7.4)."

- [ ] **Step 5: The session**

`session/__init__.py`: `open_session` gains `snapshot_resolver: SnapshotResolver | None = None` (import the Protocol from `beliefs.corpus` under `TYPE_CHECKING` if the module keeps its imports lazy) and the factory passes `snapshot_resolver=snapshot_resolver`. Docstring line: "A world-bound caller passes `RetainedSnapshots(world)`; without it a session cannot author a snapshot-arm retraction."

- [ ] **Step 6: Run**

`uv run --frozen pytest tests/test_snapshot_retraction.py tests/test_local_standing.py tests/test_retract.py tests/test_import_bundle.py tests/test_world_receipts.py tests/test_session*.py -q` green; `just check` green.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-44343a "snapshot_resolver port, _resolve_snapshot_target, RetainedSnapshots, open_session(snapshot_resolver=)"
git add python/src/beliefs/corpus.py python/src/beliefs/world/epoch.py python/src/beliefs/world/read.py python/src/beliefs/session/__init__.py python/tests/test_snapshot_retraction.py python/tests/test_local_standing.py tasks
git commit -m "feat(correction): resolve a snapshot target at the write boundary through the world's retained epochs (BI-1, BI-2)"
```

---

### Task 3: The fold — `snapshot_standing` with chain validation

**Files:**
- Modify: `python/src/beliefs/corpus.py` (after `local_retraction_enumeration`, `:994`)
- Test: `python/tests/test_snapshot_retraction.py` (extended)

**Interfaces:**
- Consumes: `retraction_standing`, `_validated_retraction_facet`, `CorpusWriter._validated_retraction`, `CorpusWriter._resolve_retraction_target` (Tasks 1, 2).
- Produces: `corpus.SnapshotStanding(retracted: frozenset[str], history: Mapping[str, tuple[tuple[str, str], ...]])`; `corpus.snapshot_standing(views: Mapping[str, ReadView], subject_kind: str = "producer") -> SnapshotStanding`. Tasks 4, 5, 7 consume.

- [ ] **Step 1: The failing tests**

```python
from test_local_standing import retracts  # node-arm retraction of a target record, canonical

from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.corpus import ReadView, snapshot_standing
from beliefs.errors import RetractionUnreadable
from fixtures_cut4 import raw_write


def corpus_with(tmp_path, *nodes, resolver):
    writer = writer_at(tmp_path, resolver=resolver)
    minted = [writer.operations.retract(n) if n.kind == "retraction" else writer.add(n) for n in nodes]
    return writer, minted


class TestSnapshotStanding:
    def _resolver(self, writer_root):
        cid = writer_at(writer_root).corpus_id
        return StubResolver({S: (cid,), S2: (cid,)}), cid

    def test_no_retractions_is_empty(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        standing = snapshot_standing({writer.corpus_id: writer.read_view})
        assert standing.retracted == frozenset() and dict(standing.history) == {}

    def test_one_standing_retraction_names_its_identity_with_history(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == {S}
        assert standing.history[S] == ((r.id, RETRACTION_UPHELD),)

    def test_a_counter_retraction_restores_and_the_history_carries_both(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        c = writer.operations.retract(retracts(r, "counter"))
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == frozenset()
        assert standing.history[S] == tuple(sorted([(c.id, RETRACTION_UPHELD), (r.id, RETRACTION_OVERTURNED)]))
        cc = writer.operations.retract(retracts(c, "counter-counter"))
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == {S}
        assert len(standing.history[S]) == 3 and (cc.id, RETRACTION_UPHELD) in standing.history[S]

    def test_two_corpora_union(self, tmp_path):
        a = writer_at(tmp_path / "a"); b = writer_at(tmp_path / "b")
        ra = StubResolver({S: (a.corpus_id,)}); rb = StubResolver({S2: (b.corpus_id,)})
        a = writer_at(tmp_path / "a", resolver=ra); b = writer_at(tmp_path / "b", resolver=rb)
        a.operations.retract(snapshot_retraction(S)); b.operations.retract(snapshot_retraction(S2, token="t2"))
        standing = snapshot_standing({a.corpus_id: a.read_view, b.corpus_id: b.read_view})
        assert standing.retracted == {S, S2}

    def test_an_unreadable_facet_refuses(self, tmp_path):
        from test_local_standing import raw_retraction

        writer = writer_at(tmp_path / "c")
        raw_write(tmp_path / "c", raw_retraction("retraction:raw", "assessment:x"))
        with pytest.raises(RetractionUnreadable):
            snapshot_standing({writer.corpus_id: ReadView.opened_at(tmp_path / "c")})

    def test_a_broken_counter_retraction_refuses_rather_than_restores(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        broken = retracts(r, "counter")
        broken.facets[stored.RETRACTION_FACET]["target"]["content_identity"] = "0" * 64
        stored.stamp_semantic_identity(broken)           # canonical shape, wrong target identity
        raw_write(tmp_path / "c", broken)
        with pytest.raises(RetractionUnreadable) as caught:
            snapshot_standing({cid: ReadView.opened_at(tmp_path / "c")})
        assert caught.value.ref == broken.id

    def test_a_broken_retraction_outside_every_chain_raises_nothing(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        unrelated = retracts(r, "elsewhere")
        unrelated.facets[stored.RETRACTION_FACET]["target"] = {
            "arm": "node", "ref": "assessment:nobody", "resolved": "assessment:nobody", "content_identity": "0" * 64,
        }
        stored.stamp_semantic_identity(unrelated)
        raw_write(tmp_path / "c", unrelated)
        standing = snapshot_standing({cid: ReadView.opened_at(tmp_path / "c")})
        assert standing.retracted == {S}
```

The `retracts(r, "counter")` fixture computes the target's content identity from `r`; the broken variants overwrite it and restamp so the controlled-shape check passes and target resolution supplies the refusal (the recipe slice 1's Task 4 used).

- [ ] **Step 2: Run to verify failure**

`uv run --frozen pytest tests/test_snapshot_retraction.py -q -k SnapshotStanding` — `ImportError: snapshot_standing`.

- [ ] **Step 3: The fold**

`corpus.py`, after `local_retraction_enumeration`:

```python
@dataclass(frozen=True)
class SnapshotStanding:
    """Which subjects a live fold finds retracted, and each subject's history
    (slice 2 §5): every snapshot-arm retraction naming it and, transitively,
    every retraction naming one of those, each with its folded resolution."""

    retracted: frozenset[str]
    history: Mapping[str, tuple[tuple[str, str], ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "history", MappingProxyType(dict(self.history)))


def snapshot_standing(views: Mapping[str, ReadView], subject_kind: str = "producer") -> SnapshotStanding:
    """Fold snapshot standing live over the corpora a snapshot covers.

    Per corpus and then union: a counter-retraction lives beside the
    retraction it counters (cross-corpus node targets are refused at the
    write boundary). Every chain member is validated with the write
    boundary's own checks before it is trusted — `retraction_standing`
    resolves a ref and nothing else, and a raw-written counter-retraction
    with a wrong content identity would otherwise restore a retracted
    snapshot. Retractions outside every chain fold from their facet alone.
    """
    from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD

    retracted: set[str] = set()
    history: dict[str, dict[str, str]] = {}
    for corpus_id in sorted(views):
        view = views[corpus_id]
        nodes: dict[str, Node] = {}
        facets: dict[str, Mapping[str, object]] = {}
        for node in view.iter_stored():
            if node.kind != "retraction":
                continue
            try:
                facets[node.id] = _validated_retraction_facet(node)
            except ScienceError as caught:
                raise RetractionUnreadable(node.id, str(caught)) from caught
            nodes[node.id] = node
        standing = retraction_standing(view, facets)
        # chains: snapshot-arm roots of this kind, then every retraction whose resolved node target is a member
        roots = {
            ref for ref, facet in facets.items()
            if cast(Mapping[str, str], facet["target"])["arm"] == "snapshot"
            and cast(Mapping[str, str], facet["target"])["subject_kind"] == subject_kind
        }
        members: set[str] = set(roots)
        grew = True
        while grew:
            grew = False
            for ref, facet in facets.items():
                target = cast(Mapping[str, str], facet["target"])
                if ref in members or target["arm"] != "node":
                    continue
                if (view.resolve(target["ref"]) or target["ref"]) in members:
                    members.add(ref)
                    grew = True
        for ref in sorted(members):
            try:
                CorpusWriter._validated_retraction(nodes[ref])
                CorpusWriter._resolve_retraction_target(nodes[ref], view)
            except ScienceError as caught:
                raise RetractionUnreadable(ref, str(caught)) from caught
        for root in roots:
            identity = cast(Mapping[str, str], facets[root]["target"])["subject_identity"]
            if standing[root]:
                retracted.add(identity)
            chain = history.setdefault(identity, {})
            chain[root] = RETRACTION_UPHELD if standing[root] else RETRACTION_OVERTURNED
            frontier = {root}
            while frontier:
                nxt: set[str] = set()
                for ref in members - set(chain):
                    target = cast(Mapping[str, str], facets[ref]["target"])
                    if target["arm"] == "node" and (view.resolve(target["ref"]) or target["ref"]) in frontier:
                        chain[ref] = RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED
                        nxt.add(ref)
                frontier = nxt
    return SnapshotStanding(
        frozenset(retracted),
        {identity: tuple(sorted(chain.items())) for identity, chain in history.items()},
    )
```

`retraction_standing` skips non-node arms as subtractors and answers for every vertex, so `standing[root]` and `standing[ref]` are always present. The import of `RetractionUnreadable` and `ScienceError` already exists in `corpus.py` (used by `local_retraction_enumeration`).

- [ ] **Step 4: Run**

`uv run --frozen pytest tests/test_snapshot_retraction.py tests/test_local_standing.py -q` green; `just check`.

- [ ] **Step 5: Commit**

```bash
tasks done beliefs-5f65eb "snapshot_standing: per-corpus live fold with validated history chains"
git add python/src/beliefs/corpus.py python/tests/test_snapshot_retraction.py tasks
git commit -m "feat(correction): snapshot_standing folds a subject's live standing and validated history (BI-4, BI-7, BI-8)"
```

---

### Task 4: The recomputation sites — `validate_receipt`, import, the audits

**Files:**
- Modify: `python/src/beliefs/world/derive.py:120` (`RECEIPT_OUTCOMES`)
- Modify: `python/src/beliefs/world/read.py:219-340` (`validate_receipt`), new `_snapshot_standing`, `reported_receipt`
- Modify: `python/src/beliefs/world/importing.py:52-66`
- Modify: `python/src/beliefs/world/audit.py:14-45` (`SNAPSHOT_STATES`, `_reduce`), `:137-186` (both reports)
- Modify: `python/src/beliefs/audit.py:705-800` (`_world_findings`)
- Test: `python/tests/test_world_epoch_audit.py`, `test_world_import_epoch.py`, `test_world_audit.py` (extended)

**Interfaces:**
- Consumes: `snapshot_standing` (Task 3), `RetainedSnapshots`, `CorpusWriter._resolve_snapshot_target` (Task 2).
- Produces: `read.reported_receipt(world, published, kind) -> tuple[ReceiptOutcome, Finding | None]`; outcome `"retracted"`; state `"retracted"`; `EpochImportRefused` reasons `"retracted-snapshot"`, `"unreadable-standing"`; finding codes `retraction-unreadable`, and `retraction-target-invalid` from `audit_world` for the arm. Task 7 consumes.

- [ ] **Step 1: A shared world fixture for these tests**

Add to `python/tests/test_snapshot_retraction.py` (imported by the three test modules below):

```python
def retracted_world(tmp_path, *, counter=False):
    """A two-corpus world with one published epoch S, and S retracted by a
    session-shaped writer in ALPHA (covered). With counter=True the
    retraction is counter-retracted."""
    from test_world_receipts import corpora, hold_shipped, publish, world_over
    from test_world_build import sample_nodes, slug_for

    coverage = (ALPHA, BETA)
    roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    published = publish(world, coverage, bindings)
    identity = published.receipts["producer-receipt.yaml"].subject_identity
    writer = CorpusWriter(
        roots[ALPHA], DefaultExecutor, authority=FULL, profile=BASE,
        operation_port=OperationRecorder(roots[ALPHA], authority=FULL, profile=BASE),
        snapshot_resolver=RetainedSnapshots(world),
    )
    r = writer.operations.retract(snapshot_retraction(identity))
    c = writer.operations.retract(retracts(r, "counter")) if counter else None
    return world, roots, bindings, published, identity, writer, r, c
```

(`from authority import FULL` at the module top.) If `sample_nodes` corpora carry a profile that refuses `retract` for the actor, use `writer_at`'s manifest-adopting shape over the same root instead — the requirement is a writer over `roots[ALPHA]` holding the port.

- [ ] **Step 2: The failing tests**

`test_world_epoch_audit.py`:

```python
from test_snapshot_retraction import retracted_world
from beliefs.world import derive
from beliefs.world.audit import SNAPSHOT_STATES, audit_epochs, snapshot_state


def test_the_closed_sets_gain_retracted_last():
    assert derive.RECEIPT_OUTCOMES[-1] == "retracted" and SNAPSHOT_STATES[-1] == "retracted"
    assert derive.ReceiptOutcome("producer", "retracted", "x").validated is False


def test_a_retracted_subject_is_reported_and_is_not_a_finding(tmp_path):
    world, _roots, _b, published, identity, *_ = retracted_world(tmp_path)
    audit = audit_epochs(world)
    assert (published.packaging_identity, "producer", "retracted") in [(n, k, o.outcome) for n, k, o in audit.receipts]
    verdict = next(v for v in audit.snapshots if v.subject_identity == identity)
    assert verdict.state == "retracted"
    assert not any(f.ref == identity or f.code.startswith("snapshot") for f in audit.findings if "retract" in f.code)
    assert snapshot_state(world, "producer", identity).state == "retracted"


def test_retracted_precedes_availability(tmp_path):
    """BI-3: the retraction write moved ALPHA's state; a phase after availability would answer unresolvable."""
    from beliefs.world import read
    world, _roots, _b, published, *_ = retracted_world(tmp_path)
    assert read.validate_receipt(world, published, "producer").outcome == "retracted"
    assert read.validate_receipt(world, published, "retraction-enumeration").outcome == "unresolvable"


def test_a_counter_retraction_leaves_the_subject_unchecked_not_retracted(tmp_path):
    world, _roots, _b, _p, identity, *_ = retracted_world(tmp_path, counter=True)
    verdict = snapshot_state(world, "producer", identity)
    assert verdict.state == "unchecked"
    assert all(o.outcome == "unresolvable" for _n, o in verdict.receipts)


def test_an_unreadable_chain_is_an_unresolvable_outcome_and_a_finding_and_the_reports_return(tmp_path):
    from fixtures_cut4 import raw_write
    from test_local_standing import retracts
    from beliefs import stored
    world, roots, _b, published, identity, _w, r, _c = retracted_world(tmp_path)
    broken = retracts(r, "counter")
    broken.facets[stored.RETRACTION_FACET]["target"]["content_identity"] = "0" * 64
    stored.stamp_semantic_identity(broken)
    raw_write(roots[ALPHA], broken)
    audit = audit_epochs(world)
    assert [f.code for f in audit.findings if f.ref == broken.id] == ["retraction-unreadable"]
    verdict = snapshot_state(world, "producer", identity)
    assert verdict.state == "unchecked" and "cannot be decided" in verdict.receipts[0][1].detail
```

`test_world_import_epoch.py`:

```python
from test_snapshot_retraction import retracted_world


def test_a_retracted_producer_subject_refuses_before_any_write(tmp_path):
    world, _roots, _b, published, *_ = retracted_world(tmp_path)
    source = exported(published, tmp_path / "export")
    replica = world_over(tmp_path, _roots, name="replica"); hold_shipped(replica)
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(replica, source)
    assert caught.value.reason == "retracted-snapshot"
    assert [o.outcome for o in caught.value.outcomes] == ["retracted"]
    assert epochs_of(replica) == set()


def test_an_unreadable_standing_refuses_before_any_write(tmp_path):
    from fixtures_cut4 import raw_write
    from test_local_standing import retracts
    from beliefs import stored
    world, roots, _b, published, _i, _w, r, _c = retracted_world(tmp_path)
    broken = retracts(r, "counter")
    broken.facets[stored.RETRACTION_FACET]["target"]["content_identity"] = "0" * 64
    stored.stamp_semantic_identity(broken)
    raw_write(roots[ALPHA], broken)
    replica = world_over(tmp_path, roots, name="replica"); hold_shipped(replica)
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(replica, exported(published, tmp_path / "export"))
    assert caught.value.reason == "unreadable-standing" and epochs_of(replica) == set()
```

`test_world_audit.py`:

```python
def test_a_raw_written_snapshot_retraction_naming_nothing_retained_is_reported_from_captured_records(tmp_path):
    """BI-6: the epoch predates the raw write, so the record is unmapped; iter_stored would miss it."""
    from fixtures_cut4 import raw_write
    from test_snapshot_retraction import S, snapshot_retraction
    from test_world_receipts import published_world
    from beliefs.audit import NO_EVIDENCE, audit_world
    from beliefs.corpus import ReadView, corpus_check
    world, _b, roots, published = published_world(tmp_path, (ALPHA,))
    node = snapshot_retraction(S)                       # S is retained nowhere
    raw_write(roots[ALPHA], node)
    report = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert ("retraction-target-invalid", node.id) in [(f.code, f.ref) for f in report.findings]
    assert not [f for f in corpus_check(ReadView.opened_at(roots[ALPHA]), BASE) if f.ref == node.id]
```

Use this module's existing `codes`/`inventory` helpers and `WorldAudit`'s findings attribute name as they are (`grep -n "findings" python/tests/test_world_audit.py | head`).

- [ ] **Step 3: Run to verify failure**

`uv run --frozen pytest tests/test_world_epoch_audit.py tests/test_world_import_epoch.py tests/test_world_audit.py -q` — the new tests fail (`"retracted"` absent; `reason` mismatch; finding missing).

- [ ] **Step 4: `derive`, `read`**

`derive.py:120`: `RECEIPT_OUTCOMES: tuple[str, ...] = ("validated", "refuted", "unresolvable", "malformed", "retracted")`; docstring gains "`retracted` (slice 2 decision 4) is the producer receipt's only, decided before availability."

`read.py` — in `validate_receipt`, after the `fault` return and before `named_states`:

```python
    if kind == derive.BELIEF_INPUT_KIND:
        standing = _snapshot_standing(world, receipt)
        if standing is not None:
            return standing
```

New functions:

```python
def _snapshot_standing(world: registry.World, receipt: epoch._ReceiptCarrier) -> derive.ReceiptOutcome | None:
    """Slice 2 §7.1: the producer subject's live standing, decided before availability.

    Every named corpus is opened live and folded **inside its own capture
    hold** — `ReadView.iter_stored` reads the store lazily, so a fold after the
    hold would read outside it — and the per-corpus answers are unioned, which
    is the fold's own rule. The world lock is never held here. An absent or
    unreadable corpus returns ``None`` so the availability phase reports it in
    its own words. `RetractionUnreadable` propagates, as `CaptureDrift` does: a
    raw-written retraction the write boundary would have refused leaves no
    coherent standing to report on.
    """
    from beliefs.corpus import snapshot_standing

    identity = cast(str, receipt.subject_identity)
    retracted: set[str] = set()
    upheld: list[str] = []
    named: list[str] = []
    for corpus_id, _state in cast(Sequence[tuple[str, str]], receipt.corpus_states):
        try:
            carriers = registry._carrier_roots(world.config, corpus_id)
        except ManifestMalformed:
            return None
        if len(carriers) != 1:
            return None
        with _operation_lock_for(carriers[0]).capture():
            try:
                view = ReadView.opened_at(carriers[0])
                view._require_base_pin()
            except (CorpusStateMalformed, ContractMismatch):
                return None
            partial = snapshot_standing({corpus_id: view}, derive.BELIEF_INPUT_KIND)
        named.append(corpus_id)
        retracted |= partial.retracted
        upheld.extend(ref for ref, resolution in partial.history.get(identity, ()) if resolution == "upheld")
    if identity not in retracted:
        return None
    return derive.ReceiptOutcome(
        derive.BELIEF_INPUT_KIND,
        "retracted",
        f"retraction(s) {', '.join(sorted(upheld))} in {', '.join(sorted(named))} stand against this subject",
    )


def reported_receipt(
    world: registry.World, published: epoch.Epoch, kind: derive.ReceiptKind
) -> tuple[derive.ReceiptOutcome, Finding | None]:
    """`validate_receipt` for a report (slice 2 §7.3): an unreadable standing
    chain becomes an `unresolvable` outcome and a `retraction-unreadable`
    finding instead of an exception, so a raw write cannot stop a report."""
    try:
        return validate_receipt(world, published, kind), None
    except RetractionUnreadable as caught:
        outcome = derive.ReceiptOutcome(
            kind, "unresolvable", f"the standing of this subject cannot be decided: {caught}"
        )
        return outcome, Finding(
            "error",
            "retraction-unreadable",
            caught.ref,
            str(caught),
            f"{published.packaging_identity}: the {kind} subject's standing cannot be decided: {caught}",
        )
```

Imports: `Finding` from `beliefs.corpus` (already imported there? `read.py:90` imports `ReadView, _operation_lock_for` — add `Finding`), `CorpusStateMalformed`, `ContractMismatch`, `ManifestMalformed`, `RetractionUnreadable` from `beliefs.errors`. Add `"reported_receipt"` to `__all__` (`:122` region) and to `world/__init__.py`'s re-exports beside `validate_receipt`.

- [ ] **Step 5: Import**

`importing.py:52-56`:

```python
    kinds = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))
    outcomes: dict[derive.ReceiptKind, derive.ReceiptOutcome] = {}
    for kind in kinds:
        try:
            outcomes[kind] = read.validate_receipt(world, carrier, kind)
        except RetractionUnreadable as caught:
            raise EpochImportRefused(
                "unreadable-standing",
                f"{packaging_identity}: the {kind} subject's standing cannot be decided: {caught}",
            ) from caught
    decisions: tuple[
        tuple[Literal["malformed-receipt"], Literal["malformed"]]
        | tuple[Literal["retracted-snapshot"], Literal["retracted"]]
        | tuple[Literal["refuted-receipt"], Literal["refuted"]],
        ...,
    ] = (("malformed-receipt", "malformed"), ("retracted-snapshot", "retracted"), ("refuted-receipt", "refuted"))
```

- [ ] **Step 6: The audits**

`world/audit.py`: `SNAPSHOT_STATES = ("checked", "contradicted", "unchecked", "retracted")`, `SnapshotState = Literal[..., "retracted"]`; `_reduce` gains, first:

```python
    if any(outcome.outcome == "retracted" for outcome in outcomes):
        return "retracted"  # every receipt of a retracted subject is; stated first so a mixed case has a rule
```

`audit_epochs` (`:147-150`):

```python
            outcome, unreadable_finding = read.reported_receipt(world, opened[name], kind)
            outcomes.append((name, kind, outcome))
            for finding in (unreadable_finding, _receipt_finding(name, outcome)):
                if finding is not None:
                    findings.append(finding)
```

`snapshot_state` (`:175-178`): `(name, read.reported_receipt(world, opened[name], kind)[0])`.

`audit.py::_world_findings` (`:777`): `outcome, unreadable = reported_receipt(world, published, kind)` and append `unreadable` when not `None` (import `reported_receipt` beside `validate_receipt`; drop `validate_receipt` from the import if unused). Then, before the receipt loop, the snapshot-arm resolution (§7.4):

```python
    from beliefs.corpus import CorpusWriter, _validated_retraction_target
    from beliefs.world.epoch import RetainedSnapshots

    resolver = RetainedSnapshots(world)
    retained = resolver.retained("producer")
    for corpus_id, _state in published.coverage:
        if corpus_id in view.absent() or corpus_id in excluded:
            continue
        for node in view.captured_records(corpus_id):      # unmapped post-build records included (§7.4)
            if node.kind != "retraction":
                continue
            try:
                target = _validated_retraction_target(node)
            except ScienceError:
                continue  # shape faults are corpus_check's
            if target["arm"] != "snapshot":
                continue
            faults = []
            if target["subject_identity"] not in retained:
                faults.append(f"no retained epoch carries producer snapshot {target['subject_identity']}")
            elif corpus_id not in retained[target["subject_identity"]]:
                faults.append(f"corpus {corpus_id} is outside the coverage of producer snapshot {target['subject_identity']}")
            successor = node.facets[stored.RETRACTION_FACET].get("successor")
            if successor is not None and successor not in retained:
                faults.append(f"successor {successor} is not a retained producer snapshot")
            for fault in faults:
                findings.append(Finding("error", "retraction-target-invalid", node.id, "target", f"{node.id}: {fault}"))
```

- [ ] **Step 7: Run; the rule-identity check**

`uv run --frozen pytest tests/test_world_epoch_audit.py tests/test_world_import_epoch.py tests/test_world_audit.py tests/test_world_receipts.py tests/test_snapshot_retraction.py -q` green. Decision 11's check: over `published_world(tmp_path, (ALPHA,))` with nothing retracted, every receipt is still `validated` (`test_a_validated_carrier_is_admitted_without_a_pointer_or_a_log_head_record` covers it — confirm it is in the green run). `just check`.

- [ ] **Step 8: Commit**

```bash
tasks done beliefs-a5d72a "retracted before availability; import refuses retracted-snapshot and unreadable-standing; reports return through reported_receipt; audit_world resolves the arm over captured_records"
git add python/src/beliefs/world/derive.py python/src/beliefs/world/read.py python/src/beliefs/world/importing.py python/src/beliefs/world/audit.py python/src/beliefs/world/__init__.py python/src/beliefs/audit.py python/tests/test_world_epoch_audit.py python/tests/test_world_import_epoch.py python/tests/test_world_audit.py python/tests/test_snapshot_retraction.py tasks
git commit -m "feat(correction): a retracted producer snapshot is refused at import and reported by the audits (C8, BI-3, BI-6, BI-8)"
```

---

### Task 5: The evaluator — the world read's standing, history, damage and absence

**Files:**
- Modify: `python/src/beliefs/world/view.py:57-72` (fields), after `:161` (`snapshot_standing`)
- Modify: `python/src/beliefs/evaluation.py:268-300` (the world block and the standing loop), `:306-315` (subtraction), `:407-423` (scope and `scoped`)
- Test: `python/tests/test_world_standing.py` (extended)

**Interfaces:**
- Consumes: `snapshot_standing`, `SnapshotStanding` (Task 3); `ProducerSnapshotRetracted` (Task 1).
- Produces: `WorldReadView.snapshot_standing() -> SnapshotStanding`; `gather`'s refusals and the history in `EvaluationInputs.retractions.found`. Task 7 consumes.

- [ ] **Step 1: The failing tests**

Append to `test_world_standing.py` (its helpers `writer_at`, `evaluation`, `split_evaluation_world`, `world_kwargs`, `make_absent` are at the top):

```python
from test_snapshot_retraction import snapshot_retraction
from test_local_standing import retracts as counter_of
from beliefs.closure import RETRACTION_OVERTURNED
from beliefs.errors import CorpusDamaged, ProducerSnapshotRetracted, RetractionUnreadable
from beliefs.world.epoch import RetainedSnapshots


def _retract_snapshot(world, roots, published, profile, *, corpus=ALPHA):
    identity = published.receipts["producer-receipt.yaml"].subject_identity
    writer = writer_at(roots[corpus], profile)
    writer._snapshot_resolver = RetainedSnapshots(world)   # writer_at has no port parameter; bind it
    return identity, writer, writer.operations.retract(snapshot_retraction(identity))


class TestTheSnapshotTarget:
    def test_a_retracted_bound_snapshot_refuses(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _identity, _w, _r = _retract_snapshot(world, roots, published, profile)
        with pytest.raises(ProducerSnapshotRetracted):
            evaluation(world, published, profile)

    def test_a_counter_retraction_restores_and_the_history_is_in_the_digest(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _view, baseline, _answer = evaluation(world, published, profile)
        _identity, writer, r = _retract_snapshot(world, roots, published, profile)
        c = writer.operations.retract(counter_of(r, "counter"))
        view, inputs, _answer = evaluation(world, published, profile)
        assert (r.id, RETRACTION_OVERTURNED) in inputs.retractions.found and (c.id, RETRACTION_UPHELD) in inputs.retractions.found
        assert ("retraction", r.id) in inputs.read_trace and ("retraction", c.id) in inputs.read_trace
        assert inputs.closure().digest() != baseline.closure().digest()
        assert len({ref for ref, _ in inputs.retractions.found}) == len(inputs.retractions.found)

    def test_an_absent_covered_corpus_answers_absence_for_the_snapshot(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        identity = view.producer_snapshot_identity()
        assert (f"producer-snapshot:{identity}", BETA) in inputs.absent

    def test_a_damaged_covered_corpus_refuses_whatever_it_holds(self, tmp_path):
        from test_world_view import damage
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        damage(roots[BETA], "construction")
        view = open_world_view(world, published, on_damage="report")
        kwargs = world_kwargs(view, profile)
        with pytest.raises(CorpusDamaged) as caught:
            gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert caught.value.ref == f"producer-snapshot:{view.producer_snapshot_identity()}" and caught.value.corpus_id == BETA

    def test_a_rebuild_after_retraction_keeps_the_identity_and_still_refuses(self, tmp_path):
        from test_world_receipts import hold_shipped, publish
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        identity, writer, r = _retract_snapshot(world, roots, published, profile)
        rebuilt = publish(world, (ALPHA, BETA), hold_shipped(world))
        assert rebuilt.receipts["producer-receipt.yaml"].subject_identity == identity
        with pytest.raises(ProducerSnapshotRetracted):
            evaluation(world, rebuilt, profile)
        writer.operations.retract(counter_of(r, "counter"))
        rebuilt2 = publish(world, (ALPHA, BETA), hold_shipped(world))
        _v, over_rebuilt, _a = evaluation(world, rebuilt2, profile)
        _v, over_old, _a = evaluation(world, published, profile)
        assert over_rebuilt.retractions.found == over_old.retractions.found

    def test_an_older_snapshots_retraction_is_out_of_the_closure(self, tmp_path):
        from test_world_receipts import hold_shipped, publish
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _v, baseline, _a = evaluation(world, published, profile)
        narrow = publish(world, (ALPHA,), hold_shipped(world))          # a different identity
        old_identity = narrow.receipts["producer-receipt.yaml"].subject_identity
        writer = writer_at(roots[ALPHA], profile); writer._snapshot_resolver = RetainedSnapshots(world)
        writer.operations.retract(snapshot_retraction(old_identity))
        later = publish(world, (ALPHA, BETA), hold_shipped(world))       # captures that retraction
        _v, inputs, _a = evaluation(world, later, profile)
        assert inputs.retractions.found == baseline.retractions.found

    def test_a_broken_counter_retraction_refuses_the_read(self, tmp_path):
        from fixtures_cut4 import raw_write
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _identity, _writer, r = _retract_snapshot(world, roots, published, profile)
        broken = counter_of(r, "counter")
        broken.facets[stored.RETRACTION_FACET]["target"]["content_identity"] = "0" * 64
        stored.stamp_semantic_identity(broken)
        raw_write(roots[ALPHA], broken)
        with pytest.raises(RetractionUnreadable) as caught:
            evaluation(world, published, profile)
        assert caught.value.ref == broken.id
```

`profile_with` comes from `domain_facet_fixtures` (already imported by the module through `test_world_view`); `damage` is `test_world_view.damage(root, kind)`. If `writer_at` in this module cannot take a resolver, the `_snapshot_resolver` attribute binding above is the recipe — or extend `writer_at` with a `resolver=None` keyword; either is fine, the assertion is the contract.

- [ ] **Step 2: Run to verify failure**

`uv run --frozen pytest tests/test_world_standing.py -q -k TheSnapshotTarget` — `AttributeError: snapshot_standing`.

- [ ] **Step 3: The view**

`view.py`: add field `_snapshot_standing: SnapshotStanding | None` (import `SnapshotStanding, snapshot_standing` from `beliefs.corpus`), set `view._snapshot_standing = None` in `_opened`, and after `producer_snapshot_identity`:

```python
    def snapshot_standing(self) -> SnapshotStanding:
        """The live fold over the present covered corpora (slice 2 §8). Reads
        through the corpus views, not the epoch's address map: a post-build
        record has no epoch address, and `resolve` would answer None for a
        counter-retraction's target and break the fold."""
        if self._snapshot_standing is None:
            self._snapshot_standing = snapshot_standing(self._live)
        return self._snapshot_standing
```

- [ ] **Step 4: `gather`**

`evaluation.py`, the world block (`:271-274`) becomes:

```python
    absent: list[tuple[str, str]] = []
    history: tuple[tuple[str, str], ...] = ()
    if world:
        bound = view.producer_snapshot_identity()
        if context.producer_snapshot_identity != bound:
            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)
        for report in view.damaged():
            raise CorpusDamaged(f"producer-snapshot:{bound}", report.corpus_id, view.stamp)
        for corpus_id in view.absent():
            absent.append((f"producer-snapshot:{bound}", corpus_id))
        snapshot_standing = view.snapshot_standing()
        if not absent and bound in snapshot_standing.retracted:
            raise ProducerSnapshotRetracted(bound)
        history = snapshot_standing.history.get(bound, ())
```

and delete the later `absent: list[tuple[str, str]] = []` at `:278`. (`view.stamp` is a property on `WorldReadView` — `:116`.) In the standing loop, the target branch becomes:

```python
            target = cast(Mapping[str, str], facet["target"])
            if target["arm"] == "snapshot":
                facets[ref] = facet  # a vertex only: its one possible closure member is the bound snapshot, checked above
                continue
            target_ref = target["ref"] if target["arm"] == "node" else target["dataset"]
```

(the pinned cut-33 line stays verbatim.) The subtraction loop (`:311-315`):

```python
        if target["arm"] == "node":
            subtracted.add(target["resolved"])
        elif target["arm"] == "route":
            retired.setdefault(target["resolved"], set()).add(target["route_identity"])
        # a snapshot arm names no node and no route
```

The scope loop (`:415-418`):

```python
            target = cast(Mapping[str, str], facet["target"])
            key = None if target["arm"] == "snapshot" else target["resolved"]   # a snapshot arm is never in scope (decision 8)
            if key is not None and (key in scope or key in taken):
```

and `scoped`:

```python
    scoped = RetractionEnumeration(
        found=tuple(sorted({*((ref, recorded) for ref, recorded in enumeration.found if ref in taken), *history})),
        coverage=enumeration.coverage,
    )
```

Imports: `CorpusDamaged`, `ProducerSnapshotRetracted` from `beliefs.errors`. `grep -n 'target\["arm"\]\|target\["resolved"\]' python/src/beliefs/evaluation.py` must now list exactly the four sites of spec §8.

- [ ] **Step 5: Run**

`uv run --frozen pytest tests/test_world_standing.py tests/test_standing_read.py tests/test_world_view.py tests/test_evaluation.py tests/test_belief.py tests/test_composite_reading.py -q` green, then `just test-fast` green; `just check`.

- [ ] **Step 6: Commit**

```bash
tasks done beliefs-e2f187 "gather: refuses a retracted bound snapshot, refuses damage, answers absence, hands the live history into the closure; the arm at all four target sites"
git add python/src/beliefs/world/view.py python/src/beliefs/evaluation.py python/tests/test_world_standing.py tasks
git commit -m "feat(correction): the world read refuses a retracted producer snapshot and digests its history (C9, BI-4, BI-5, BI-7, BI-9)"
```

---

### Task 6: The reproduction re-runs

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §13)

**Interfaces:**
- Consumes: everything above. Produces: the transition measurement the results record cites.

- [ ] **Step 1: Run**

From `python/`, with `SCIENCE_MM30_ROOT=/mnt/ssd/Dropbox/beliefs/.work/reproduction/mm30` (the main checkout's, memory `worktree-on-work-root-needs-cut-root-exports`; the driver resolves the main checkout through the worktree's real path, `beliefs-51ffdf`): run the driver as cut 33's Task 6 did (`sed -n '/### Task 6/,/### Task 7/p' docs/superpowers/plans/2026-09-16-correction-remainder-slice-1.md` for the exact command and the `state.json` fields read). Nothing is recreated or moved aside: no contract succeeded; the retraction enumeration is derived as at cut 33 and mm30's corpus holds no snapshot-arm retraction.

- [ ] **Step 2: Record**

Append `## 13. Addendum — the snapshot target, 2026-09-19` to the record: the same evaluator answer as §12; `found=()` and coverage unchanged; the producer snapshot identity unchanged (decision 11: no rule identity moved); the one new arm exercised by the acceptance module only. If any pinned value differs, stop: that is a finding against decision 11 and the cut does not freeze its results until it is explained (spec §13).

```bash
tasks done beliefs-fbd67f "reproduction re-run: same answer, no digest moved"
git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under slice 2; nothing moves"
```

---

### Task 7: Acceptance, the N2 declaration, the guard and the runner

**Files:**
- Create: `python/tests/acceptance/test_snapshot_retraction_acceptance.py`, `python/tests/n2_arms_cut34.py`, `python/tests/acceptance/n2_arms_cut34.py` (the re-export shim on `acceptance/n2_arms_cut33.py`'s shape), `python/tests/acceptance/test_n2_cut34.py`, `python/tools/cut34_acceptance.py`

**Interfaces:**
- Consumes: the frozen cut document, `CUT34_FREEZE_COMMIT`, `CUT34_FROZEN_SHA256` (Task 0); every module above.
- Produces: C8-a–d, C9-a–d, BI-1–9 discharged on the certified volume.

- [ ] **Step 1: The acceptance module**

One test per unit over the durable world (`test_world_view_acceptance.durable_world` and `evaluation_world`, as `test_correction_acceptance.py` imports them; a session-shaped writer over the ALPHA root with `snapshot_resolver=RetainedSnapshots(world)`), named exactly as `UNIT_CHECKS` names it. Each is the Task 4/5 unit test re-composed over the durable roots:

- `test_c8a_import_of_a_retracted_producer_subject_refuses_before_any_write` — Task 4's import test; also `inventory(replica epochs/)` unchanged.
- `test_c8b_the_audit_reports_retracted_without_a_finding` — Task 4's audit test.
- `test_c8c_the_query_reports_retracted_and_the_successor_unchecked` — build `new` under `(ALPHA,)`; assert `snapshot_state(new) == "checked"` **before** the retraction; retract old with `successor=new`; assert old `retracted`, new `unchecked` with the receipt `unresolvable` and "no longer stands at the state" in its detail.
- `test_c8d_mounting_writes_nothing_and_validates_nothing` — a fresh corpus root holding a snapshot-arm retraction (raw-written, since it is unmounted) and the ALPHA root a retracted snapshot covers: `monkeypatch.setattr(read, "validate_receipt", counting)`; `world.admit(root, provenance=...)` for each (use the provenance `test_world_receipts.world_over` uses — `grep -n "provenance=" python/tests/test_world_receipts.py`); `inventory(world_root / "epochs")` byte-identical, `counting.calls == 0`.
- `test_c9a_a_computation_bound_to_the_old_snapshot_refuses` — Task 5's first test over the durable world with the narrowing route.
- `test_c9b_bound_to_the_new_snapshot_proceeds_and_the_digest_moves` — `gather` over `open_world_view(world, new)` with `S'`; `inputs.closure()["producer_snapshot"] == S'`; `answer.belief_input_digest != pre-narrowing digest over old` (gather old *before* retracting).
- `test_c9c_the_old_epoch_is_byte_unchanged` — `read.open_epoch(world, old.packaging_identity).members == old.members` and each `receipts[m].document` equal before and after; the retracted carrier's directory inventory identical.
- `test_c9d_nothing_resolves_through_the_retraction_to_its_successor` — the two `ProducerSnapshotMismatch` negatives of spec §9 step 4.
- `test_bi1_a_snapshot_retraction_outside_the_targets_coverage_is_refused_at_authoring` — narrow `new` covers ALPHA only; a writer over BETA with the port refuses `RetractionTargetUnresolvable` naming BETA when retracting `S'`; the same retraction through ALPHA's writer is admitted.
- `test_bi2_a_writer_without_the_port_refuses_the_arm`.
- `test_bi3_retracted_precedes_availability` — Task 4's `test_retracted_precedes_availability`.
- `test_bi4_a_counter_retraction_restores_the_snapshot` — `snapshot_state(S).state != "retracted"`; `gather` proceeds; `old.members` unchanged.
- `test_bi5_an_older_snapshots_retraction_is_out_of_the_closure` — Task 5's test.
- `test_bi6_a_raw_written_snapshot_retraction_is_reported_by_audit_world_from_captured_records` — Task 4's `test_world_audit` test, epoch built first.
- `test_bi7_history_is_in_the_digest` — Task 5's counter-retraction test: the pair in `found`, both in `read_trace`, digest differs from the never-retracted digest over the same epoch.
- `test_bi8_an_unreadable_counter_retraction_refuses_rather_than_restores` — `gather` → `RetractionUnreadable` naming it; `import_epoch` → `unreadable-standing`, no directory; `snapshot_state` verdict `unchecked` with "cannot be decided"; `audit_epochs` **and** `audit_world` return, each with exactly one `retraction-unreadable` finding naming it, and `audit_world`'s other findings equal the readable-chain run's.
- `test_bi9_a_rebuild_restores_nothing_and_duplicates_nothing` — Task 5's rebuild test.

- [ ] **Step 2: The declaration file**

`python/tests/n2_arms_cut34.py` on `n2_arms_cut33.py`'s shape: `DECLARATION_UNITS` = the seventeen; `UNIT_CHECKS` to `acceptance/test_snapshot_retraction_acceptance.py::<name>`; `CO_CITED = ()`; `unit_of`; `CUT34_ARMS` with `before` copied verbatim from the tree at freeze:

| unit | module | `before` (as Tasks 1–5 write it) | `after` |
|---|---|---|---|
| C8-a | `world/importing.py` | `("malformed-receipt", "malformed"), ("retracted-snapshot", "retracted"), ("refuted-receipt", "refuted"))` | `("malformed-receipt", "malformed"), ("refuted-receipt", "refuted"))` |
| C8-b | `world/audit.py` | `    if any(outcome.outcome == "retracted" for outcome in outcomes):` | `    if False:` |
| C8-c | `world/read.py` | `    if identity not in standing.retracted:\n        return None` | `    if True:\n        return None` |
| C8-d | `world/registry.py` | the last statement of `_locked_admit` before its `return` (read it at freeze) | the same, preceded by `from beliefs.world import read as _read; _read.validate_receipt(world, _read.current_epoch(world), "producer")` — if `_locked_admit` has no `world` in scope, sabotage `World.admit` instead: after `_locked_admit(...)` returns, call `read.validate_receipt(self, read.current_epoch(self), "producer")` |
| C9-a | `evaluation.py` | `            raise ProducerSnapshotRetracted(bound)` | `            pass` |
| C9-b | `closure.py` | `        "producer_snapshot": producer_snapshot_identity,` | `        "producer_snapshot": "",` |
| C9-c | `world/epoch.py` | `            retained[carrier.subject_identity] = coverage` | the same line followed by `            (self._world.config.world_root / "epochs" / carrier.packaging_identity / member).open("ab").write(b"\nretracted: true\n")` |
| C9-d | `evaluation.py` | `        if context.producer_snapshot_identity != bound:\n            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)` | `        if context.producer_snapshot_identity != bound and context.producer_snapshot_identity not in {r for h in view.snapshot_standing().history.values() for r, _ in h}:\n            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)` — and if that does not make C9-d's negative pass, the arm's `after` accepts the successor named by any standing snapshot retraction's facet (read it through `view.captured_records`); the check is that C9-d fails |
| BI-1 | `corpus.py` | `        if corpus_id not in retained[identity]:` | `        if False:` |
| BI-2 | `corpus.py` | `        if self._snapshot_resolver is None:\n            raise RetractionTargetUnresolvable(` | `        if self._snapshot_resolver is None:\n            return\n            raise RetractionTargetUnresolvable(` |
| BI-3 | `world/read.py` | `    if kind == derive.BELIEF_INPUT_KIND:\n        standing = _snapshot_standing(world, receipt)` | `    if False:\n        standing = _snapshot_standing(world, receipt)` (the retracted phase never runs; availability answers `unresolvable`) |
| BI-4 | `corpus.py` | `            if standing[root]:\n                retracted.add(identity)` | `            if True:\n                retracted.add(identity)` |
| BI-5 | `evaluation.py` | `            key = None if target["arm"] == "snapshot" else target["resolved"]` | `            key = f"producer-snapshot:{target['subject_identity']}" if target["arm"] == "snapshot" else target["resolved"]` plus `scope` gaining every retained identity — the two-line `after` names both edits, in the same module |
| BI-6 | `audit.py` | `        for node in view.captured_records(corpus_id):      # unmapped post-build records included (§7.4)` | `        for node in ():` |
| BI-7 | `evaluation.py` | `        found=tuple(sorted({*((ref, recorded) for ref, recorded in enumeration.found if ref in taken), *history})),` | `        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),` |
| BI-8 | `corpus.py` | `                CorpusWriter._resolve_retraction_target(nodes[ref], view)\n            except ScienceError as caught:\n                raise RetractionUnreadable(ref, str(caught)) from caught` | `                pass\n            except ScienceError as caught:\n                raise RetractionUnreadable(ref, str(caught)) from caught` |
| BI-9 | `evaluation.py` | the same `key = ...` line as BI-5 | `key = f"producer-snapshot:{target['subject_identity']}" ...` **and** `scope` gains `f"producer-snapshot:{bound}"` — distinct from BI-5's `after` (which adds every retained identity); BI-9's check is the rebuilt epoch's duplicated pair |

Every `before` must occur exactly once in its module and the mutated module must `ast.parse`; where a `before` collides with another arm's (BI-5 and BI-9 share a line), widen one of them with its preceding line so each is unique. `python/tests/acceptance/n2_arms_cut34.py` re-exports the five names.

- [ ] **Step 3: The guard and the runner**

`python/tests/acceptance/test_n2_cut34.py` on `test_n2_cut33.py`'s shape: `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-19-conformance-cut-34.md"`, `CUT34_FREEZE_COMMIT`, `CUT34_FROZEN_SHA256` (Task 0), `FROZEN_DECLARATION = "python/tests/n2_arms_cut34.py"` with `CUT34_DECLARATION_SHA256` pinned once final, `FROZEN_PRIOR_CUT_FILES` = cut 33's dict plus `"python/tests/n2_arms_cut33.py": "<git log -1 --format=%h -- python/tests/n2_arms_cut33.py>"`, `PRIOR_ARMS` extended with `CUT33_ARMS`, no `UNAUDITED_UNIT`, the inventory test asserting seventeen, the freeze-pin test asserting `"**17 declaration units**"` and `'("cut33_acceptance.py",)'`, `test_every_acceptance_test_the_arms_name_exists` over the new module, the staleness audit with the tree's baseline. `python/tools/cut34_acceptance.py` is `cut33_acceptance.py` with `33→34`, `PREFIX_RUNNERS = ("cut33_acceptance.py",)`, `PHASE_MODULES = ("test_snapshot_retraction_acceptance.py", "test_n2_cut34.py")`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut34"`, `declared_accounting` from `n2_arms_cut34`.

- [ ] **Step 4: Freeze the declaration, discharge, commit**

Pin `CUT34_DECLARATION_SHA256`; `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut34.py -q -k "not sabotage"`; then on the certified volume `SCIENCE_CUT34_ROOT=/mnt/ssd/Dropbox/beliefs/.work/acceptance/cut34 uv run --frozen python tools/cut34_acceptance.py` (the runner exports the prefix chain's roots itself), then `just hook-pre-push`. Record both summary lines. Every arm `sound`, the baseline `resolved`, no `stale`.

```bash
tasks check
tasks done beliefs-fa1b95 "cut 34 discharged on the certified volume: 17 units sound"
git add python/tests/acceptance python/tests/n2_arms_cut34.py python/tools/cut34_acceptance.py tasks
git commit -m "test(cut): discharge conformance cut 34 — C8, C9, BI-1..9"
```

---

### Task 8: Results record, ledger, roadmap, guide, amendments, closeout

**Files:**
- Create: `docs/plans/2026-09-19-conformance-cut-34-results.md`
- Modify: `docs/designs/2026-09-19-conformance-cut-34.md` (`**Status:**` only), the slice-2 spec (`**Status:**`), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`: `correction-remainder` leaves the open table; the summary names cut 34; the count), `docs/plans/2026-08-29-implementation-roadmap.md` (rewritten whole: `Ranked at: cut 34`; a `Cut 34 (2026-09-19)` paragraph; tier 1 off-path row 1 removed and the later rows renumbered; the lane table's `mutation` row "closed 2026-09-19 at cut 34"; Appendix A regenerated by `python/tools/roadmap_status.py`; Appendix B rows C8, C9 removed; the count), `docs/guide/contracts-and-adoption.md` (the cut-34 line as discharged; totals), `README.md` ("through **cut 34**"; the table row; "The latest discharged boundary is cut 34"), the guide's kinds table (retraction arms: three; `grep -rn "route arm\|route-arm" docs/guide/*.md`) and epoch outcomes/states (`grep -rn "unresolvable" docs/guide/*.md`), plus spec §14 items 4 and 5 as two sentences where `current_epoch` is described, `docs/designs/2026-08-03-correction-lifecycle-design.md` (dated notes under §3's target bullet and §4's "Eligible targets" and "Semantic snapshot": the third arm, decision 10; §14 items 1, 6 as limitations), `docs/designs/2026-08-20-world-index-slice-2-design.md` (a dated note at §7.5's outcome set and wherever the snapshot states are listed: `retracted`)
- Tasks: step children done as their commits land; `beliefs-d79ca4` and `beliefs-aa27da` at the results commit; ideas filed (spec §14 items 1 and 7); `beliefs-2d5ada` read and noted

- [ ] **Step 1: Status lines** — the cut document: "discharged 2026-09-19 on the certified volume; results: `../plans/2026-09-19-conformance-cut-34-results.md`"; the spec: "discharged at conformance cut 34 on 2026-09-19; results: `../../plans/2026-09-19-conformance-cut-34-results.md`".

- [ ] **Step 2: The results record** — on cut 33's shape: §1 what ran; §2 accounting (seventeen units; C8, C9 closed; the boundary closed; the global count); §3 evidence (corrections, deviations, limitations found); §4 the reproduction (§13 of the record); §5 `## Remaining boundary` — must name at least one row label: C10's `instrument-certification` arm (`contract-cut`) and the ideas filed; §6 main integration (filled at merge); §7 execution rulings.

- [ ] **Step 3: Ledger, roadmap, guide, README, the amendments** — as the Files block says. `cd python && uv run --frozen python tools/roadmap_status.py` for Appendix A; `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green.

- [ ] **Step 4: Tasks**

```bash
tasks add "A retraction's corpus can depart: standing neither restores nor confirms" --status idea --tag conformance --tag correction \
  -b "Slice 2 §14.1: gather answers NoBelief(unavailable-corpus-absent) and audit answers unresolvable when a covered corpus holding a snapshot retraction is absent; nothing re-admits the snapshot. Decide whether departure should be a registry-visible event the audit names."
tasks add "Should build_epoch refuse to publish a retracted producer identity?" --status idea --tag conformance --tag correction \
  -b "Slice 2 §14.7: a same-coverage rebuild republishes a retracted S, is retained and may become current; reads refuse and import refuses the same carrier, so the state is coherent but asymmetric. Refusing at build changes world-index §5.3's closed refusal surface."
tasks note beliefs-2d5ada "read at cut 34: unchanged by slice 2 (retirement is still a belief-input fact only); stays open"
tasks done beliefs-dd8b91 "results record, ledger, roadmap, guide, amendments"
tasks done beliefs-d79ca4 "slice 2 discharged at cut 34: the snapshot target; C8 and C9 closed; results docs/plans/2026-09-19-conformance-cut-34-results.md"
tasks done beliefs-aa27da "correction lifecycle complete: cuts 5, 33 and 34; C1–C9 closed, C10's certification arm with contract-cut"
tasks check
git add docs README.md tasks
git commit -m "docs(cut): discharge conformance cut 34; correction-remainder slice 2 closes C8 and C9 and the boundary"
```

- [ ] **Step 5: Merge** — from the main checkout: `git merge --no-ff design/correction-remainder -m "merge: correction remainder slice 2 — conformance cut 34"`, `just gate` on the merged tree, then record the merge commit in the results record's §6 (`docs(cut34): record merged-main verification`). The lane is closed: `git worktree unlock` then `git worktree remove .worktrees/correction-remainder` after the results record and every ledger under it are on `main` (memory `execution-ledgers-are-durable-artifacts`).

---

## Self-review

**Spec coverage.** Decision 1 → Tasks 3, 4 (`_snapshot_standing` before availability; the per-corpus fold), 5; decision 2 → Task 1 (`SNAPSHOT_SUBJECT_KINDS`, both validators); decision 3 → Task 2 (`_resolve_snapshot_target`'s coverage clause; the port); decision 4 → Task 4 (the phase's position; `retracted` producer-only); decision 5 → Task 4 (`_reduce`, no finding); decision 6 → Task 5 (`ProducerSnapshotRetracted`); decision 7 → Task 5 (damage refuses, absence answers) and Task 4 (fall-through to availability); decision 8 → Tasks 3 (history chains), 5 (the four sites, `scoped`); decision 9 → Task 1 (no edges; successor text) and Task 2 (successor checks); decision 10 → Task 8 (the dated notes); decision 11 → Tasks 1 (`_retraction_target`), 4 Step 7, 6. §3 → Task 1; §4 → Task 2; §5 → Task 3; §6 → Task 1; §7.1–7.3 → Task 4; §7.4 → Task 4 Step 6; §8 → Task 5; §9, §10 → Task 7 (C9, C8-d); §11.1 → Tasks 1–5; §11.2–11.4 → Task 7; §11.5 → Task 5 (the pinned line) and Task 7 Step 2; §12 → the file map and Task 1 Step 6; §13 → Task 6; §14 → Task 8; §15, §16 → Tasks 0, 8.

**Planning correction, recorded in spec §17.** Spec §7.1 says the views are collected, each hold released, and the fold run "outside every lock". `ReadView.iter_stored` reads the store lazily (`corpus.py:340`), so that fold would read outside the hold; Task 4 folds each corpus inside its own capture hold and unions the per-corpus answers — the fold's own per-corpus-then-union rule — and still holds the world lock nowhere. The same holds for `WorldReadView.snapshot_standing()` (Task 5): `_live` views are read after the open's holds are released, exactly as every other live read through `corpus_view` is today; the view's drift discipline (a state change under a later read is that read's `CaptureDrift`, not this fold's) is unchanged.

**Placeholder scan.** the step ids are filed and named in Task 0 Step 3; `<git log -1 …>` and "read it at freeze" in Task 7 name values read from the tree at that step, as slice 1's plan did. Task 2 Step 1's `seeded_view_and_target` names a helper to be read from `test_local_standing.py` — the assertion is fixed, the helper name is not.

**Type consistency.** `SnapshotTarget(subject_kind, subject_identity)` in Tasks 1, 2, 3, 5, 7; `snapshot_standing(views: Mapping[str, ReadView], subject_kind="producer") -> SnapshotStanding(retracted, history)` in Tasks 3, 4, 5, 7; `RetainedSnapshots(world).retained(kind) -> Mapping[str, tuple[str, ...]]` in Tasks 2, 4, 5, 7; `CorpusWriter(snapshot_resolver=)`, `_resolve_snapshot_target(record, corpus_id)` in Tasks 2, 4; `reported_receipt(world, published, kind) -> (ReceiptOutcome, Finding | None)` in Task 4 (three callers); `WorldReadView.snapshot_standing()` (method) in Tasks 5, 7; `ProducerSnapshotRetracted(identity)`, `CorpusDamaged(ref, corpus_id, stamp)` in Task 5; `EpochImportRefused.reason` literals in Tasks 1, 4, 7; the `producer-snapshot:{identity}` spelling in Tasks 5, 7 and `declared_refs()`.
