# Relocation cut implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `move` and `consolidate` — the two-root world-changing operations — and discharge the relocation cut, closing G3 and D7 and reading W5 in full.

**Architecture:** A new `beliefs.relocation` module composes two `CorpusWriter`s rather than subclassing one, because an operation over two corpus roots cannot honestly be a method on an object bound to one. Each operation acquires both per-root operation locks in sorted resolved-path order, validates every precondition under them, then runs a fixed sequence of one-transaction steps: intent per root, data per root, fulfilling report per root. `move` is destination-first, so its only partial state is a duplicate location — which is exactly what `consolidate` repairs, and the reason the two ship together.

**Tech Stack:** Python 3.12+, `nodes` core (`Node`, `CreateOp`/`ReplaceOp`/`DeleteOp`, `DefaultExecutor`), the certified `atoms` engine behind `beliefs.root`, pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-09-03-world-changing-families-design.md` — read it alongside this plan. Every task below argues from a numbered section of it.

## Global Constraints

- **The cut is frozen before its code exists.** Task 1 lands the frozen cut document; no implementation task may add, remove, or reword a selected arm afterwards. A post-freeze discovery is recorded as a dated deviation in the results record, never as an edit to the frozen text.
- **Discharge runs on the certified volume**, which is the repository's own volume. `/tmp`, `/dev/shm` and the scratch volume all fail the durability allowlist; the acceptance work directory lives beside the checkout.
- **Run the suite with the project venv.** System `python` lacks `beliefs`. Use `uv run --project python pytest` (or the project venv directly) from the repository root.
- **Do not pass `-q` to pytest.** `python/pyproject.toml` already sets `addopts = "-q --ignore=tests/acceptance"`; doubling it suppresses the summary line, and any claim about test counts must quote that line. Never pipe pytest through `tail` without `set -o pipefail` — it fakes exit 0.
- **Conventional commits, and no AI-attribution trailer or footer** in any commit message, PR, or comment.
- **Merge `--no-ff`** at the end, preserving history.
- **One worktree for the lane**, `.worktrees/consolidate-family`, on branch `design/consolidate-family`.
- **Every mutation is an `atoms` effect** executed by the certified engine under the per-root operation lock — no Science-side transaction, saved plan, or authentication layer.
- **Files shared with other lanes**, per roadmap concurrency rule 3: `python/src/beliefs/errors.py`, `python/tests/test_designs_corpus.py`, the adoption ledger, the implementation roadmap, the guide index, plus `world/registry.py`, `world/verify.py`, `report.py`, `corpus.py`, `stored.py`, `decode.py`. A later merge resolves toward the earlier one.

## File Structure

| file | responsibility | task |
|---|---|---|
| `docs/designs/2026-09-03-world-changing-families-design.md` | the design, promoted from `specs/` at banking | 1 |
| `docs/designs/2026-09-03-conformance-cut-N.md` | the frozen relocation cut: boundary, selection, accounting, N2 obligations | 1 |
| `python/src/beliefs/report.py` | `RecordMutationEntry`, `Moved`, `Consolidated`, the two new operation kinds | 2 |
| `python/src/beliefs/errors.py` | the relocation refusal vocabulary | 3 |
| `python/src/beliefs/corpus.py` | `_add_locked`, `_delete_locked`, `_replace_locked`; re-resolution in `retract`/`supersede`; the rewritten concurrency docstring | 4, 5 |
| `python/src/beliefs/relocation.py` | `move`, `consolidate`, the ordered lock acquisition, the contract-agreement predicate | 6, 7, 8 |
| `python/tests/test_report.py` | the report schema and qualification arms | 2 |
| `python/tests/test_relocation.py` | the operations' unit and refusal arms | 6, 7, 8 |
| `python/tests/test_relocation_rows.py` | the guarantee-row arms: W5, W16, G3, D7, C3, R23, M3, T2, T8 | 7, 8 |
| `python/tests/test_relocation_recovery.py` | §3.5's crash prefixes and the recovery table | 9 |
| `python/tests/n2_arms_cutN.py` | the cut's N2 declaration inventory | 10 |
| `python/tools/cutN_acceptance.py` | the acceptance runner, with cut 15's as prefix | 10 |
| `docs/plans/2026-09-03-conformance-cut-N-results.md` | the discharge record | 11 |

`N` is the cut number, claimed at freeze in Task 1. Substitute it everywhere.

---

### Task 1: Bank the design and freeze the relocation cut

**Files:**
- Create: `docs/designs/2026-09-03-world-changing-families-design.md` (git mv from `docs/superpowers/specs/`)
- Create: `docs/designs/2026-09-03-conformance-cut-N.md`
- Modify: `docs/designs/2026-08-19-family-adapters-design.md` (§5.3 amendment)
- Modify: `docs/designs/2026-08-11-act-report-design.md` (§2, §2.1, §2.2 amendment)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`consolidate-family` row note)
- Modify: `README.md` (design count, table, date)
- Modify: `python/tests/test_designs_corpus.py` (`_COUNT_WORDS` if the new count has no spelling)

**Interfaces:**
- Consumes: nothing.
- Produces: the frozen arm inventory every later task tests against; the cut number `N`.

- [ ] **Step 1: Claim the cut number**

Run: `ls docs/plans/ | grep -o 'conformance-cut-[0-9]*' | sort -t- -k3 -n | tail -1`

The newest discharged cut is 15. This cut takes **16** unless another lane froze first — check `docs/designs/` for a `conformance-cut-16` document before claiming it. Roadmap rule 1: the number is claimed at freeze, in freeze order, and a lane that discharges first does not renumber.

- [ ] **Step 2: Promote the design**

```bash
git mv docs/superpowers/specs/2026-09-03-world-changing-families-design.md \
       docs/designs/2026-09-03-world-changing-families-design.md
```

Then edit its status header to read:

```markdown
**Status:** Banked 2026-09-03. Relocation cut frozen as conformance cut 16;
the deletion cut is not yet frozen.
```

Fix the two relative links in the header — from `docs/designs/` they become
`../plans/2026-08-29-implementation-roadmap.md` and
`2026-08-19-family-adapters-design.md`.

- [ ] **Step 3: Write the three dated amendments**

In `2026-08-19-family-adapters-design.md`, replace §5.3's body with:

```markdown
### 5.3 Create-only target predicates

*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §3.6: the
monotonicity argument below is retired. Consolidate and move now exist, so a
target that resolved under the lock **can** be made missing. Its replacement:
`retract` and `supersede` re-resolve their target under the lock immediately
before plan construction and refuse if it no longer resolves; each distinct
resolved root is locked exactly once, in sorted order; and the surviving hazard
is crash, whose prefixes that design enumerates.)*

The superseded argument, preserved: supersede and retract are create-only.
Within cut 5's slice, a target that resolved under the lock cannot be made
missing by another supported mutation, because no family deletes or moves it.
```

In `2026-08-11-act-report-design.md`, add after §2.2's outcome list:

```markdown
*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §2.4, five
clauses. **Operation kinds** gain `consolidate` and `move`. **Act kinds** gain
`record-mutation`. **Subject:** a `record-mutation` entry's subject is a record
ref together with the corpus it is read from or written to — a bare ref cannot
name a side of a two-root operation. **Outcomes:** `record-mutation` takes
`moved` or `consolidated`, and nothing is borrowed from another kind.
**Composite root-local operations:** an operation may span two corpus roots
under one `event_token` and one `opened_at`/`closed_at`, minting one intent and
one terminal report **per touched root**; T2 is read root-locally over such an
operation — each root sees exactly one intent and exactly one fulfillment.)*
```

In the ledger's `consolidate-family` row, append to the last cell:

```markdown
**Designed and frozen 2026-09-03** (`../designs/2026-09-03-world-changing-families-design.md`):
the boundary splits across two freezes. Cut 16 is the relocation cut (`move`,
`consolidate`); the deletion cut follows with `delete` and the ride-alongs.
```

- [ ] **Step 4: Write the frozen cut document**

Create `docs/designs/2026-09-03-conformance-cut-16.md`, following the structure of `docs/designs/2026-08-19-conformance-cut-5.md`: §1 what this cut is, §2 the boundary (in scope / out of scope), §3 the selection with each source row quoted verbatim in a fenced block followed by **Selected** / **Prior, not selected again** / **Deferred** bullets, §4 accounting, §5 N2 and acceptance obligations, §6 the second reader, §7 limitations.

§2's out-of-scope list must name: `delete` and every deletion arm; the audit; the world resolver's cross-corpus record reads; the rules store; `world-resolution`'s snapshot, coverage and divergence clauses.

§3 selects, from the design's §6.1 table: W5 (full), W16 (part), G3, D7, C3's move clause, R23's two move clauses and its consolidate clauses, M3's replica arm, T2's per-kind arms for `move` and `consolidate` read root-locally, T8's re-read against both operations. Plus the two boundary-invariant arms: §3.6's re-resolution refusal, and sorted dedup acquisition over a same-root pair.

§7's limitations must carry, verbatim from design §8: same-corpus duplicate location is not repaired; `consolidate` is two-way only; ordered acquisition is in-process only; an operation interrupted after its second data transaction cannot be completed.

- [ ] **Step 5: Update the design-corpus guard inputs**

Run: `ls docs/designs/*.md | wc -l`

Update `README.md`'s design count, its table of designs (add both new documents), and its date. If the new count has no spelling in `_COUNT_WORDS`, add one in `python/tests/test_designs_corpus.py`.

- [ ] **Step 6: Run the design-corpus guard**

Run: `uv run --project python pytest tests/test_designs_corpus.py`
Expected: PASS, with the summary line quoted in the commit message body.

- [ ] **Step 7: Commit**

```bash
git add docs README.md python/tests/test_designs_corpus.py
git commit -m "docs(mutation): bank the world-changing families and freeze cut 16"
```

---

### Task 2: Act-report schema for record mutations

This is the acquisition lane's integration point. It lands first among the code tasks and changes nothing else, so that lane can build on a settled `report.py`.

**Files:**
- Modify: `python/src/beliefs/report.py`
- Test: `python/tests/test_report.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `report.Moved(source_corpus: str, destination_corpus: str, ref: str)`
  - `report.Consolidated(kept_corpus: str, kept_ref: str, other_corpus: str, other_ref: str, retired_uid: str, rationale: str)`
  - `report.RecordMutationEntry(subject: str, corpus: str, outcome: Moved | Consolidated)` — `subject` is the record ref, `corpus` the side this entry speaks for
  - `report.OPERATION_KINDS` extended with `"consolidate"` and `"move"`

- [ ] **Step 1: Write the failing tests**

Add to `python/tests/test_report.py`:

```python
def test_record_mutation_entry_projects_its_corpus_and_outcome():
    entry = report.RecordMutationEntry(
        subject="dataset:d1",
        corpus="corpus-a",
        outcome=report.Moved(source_corpus="corpus-a", destination_corpus="corpus-b", ref="dataset:d1"),
    )
    facet = report._entry_facet(entry)
    assert facet["kind"] == "record-mutation"
    assert facet["subject"] == "dataset:d1"
    assert facet["corpus"] == "corpus-a"
    assert facet["outcome"]["type"] == "moved"
    assert facet["outcome"]["destination_corpus"] == "corpus-b"


def test_record_mutation_entry_refuses_a_locator_outcome():
    # T5's reservation: byte-locator-untested is unspellable here.
    with pytest.raises(OutcomeRefused):
        report.RecordMutationEntry(
            subject="dataset:d1",
            corpus="corpus-a",
            outcome=report.ByteLocatorUntested(reason="preflight-refused"),
        )


def test_consolidated_records_the_judgement():
    outcome = report.Consolidated(
        kept_corpus="corpus-a",
        kept_ref="source:s1",
        other_corpus="corpus-b",
        other_ref="source:s1",
        retired_uid="u-2",
        rationale="corpus-a holds the authored record",
    )
    facet = report._outcome_facet(outcome)
    assert facet["type"] == "consolidated"
    assert facet["retired_uid"] == "u-2"
    assert facet["rationale"] == "corpus-a holds the authored record"


def test_the_two_relocation_operation_kinds_are_admitted():
    assert "move" in report.OPERATION_KINDS
    assert "consolidate" in report.OPERATION_KINDS
    assert "delete" not in report.OPERATION_KINDS
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --project python pytest tests/test_report.py -k "record_mutation or consolidated or relocation_operation"`
Expected: FAIL with `AttributeError: module 'beliefs.report' has no attribute 'RecordMutationEntry'`

- [ ] **Step 3: Implement the schema**

In `python/src/beliefs/report.py`, add the two outcome values beside `RunRefusal`:

```python
@sealed
@final
@dataclass(frozen=True)
class Moved:
    source_corpus: str
    destination_corpus: str
    ref: str

    def __post_init__(self) -> None:
        _require_str(self.source_corpus, "moved source corpus")
        _require_str(self.destination_corpus, "moved destination corpus")
        _require_str(self.ref, "moved ref")


@sealed
@final
@dataclass(frozen=True)
class Consolidated:
    kept_corpus: str
    kept_ref: str
    other_corpus: str
    other_ref: str
    retired_uid: str
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("kept corpus", self.kept_corpus),
            ("kept ref", self.kept_ref),
            ("other corpus", self.other_corpus),
            ("other ref", self.other_ref),
            ("retired uid", self.retired_uid),
            ("rationale", self.rationale),
        ):
            _require_str(value, f"consolidated {name}")
```

Every field is a plain string on purpose: `_outcome_facet` converts only a
top-level tuple to a list, so a nested tuple would not encode. Exactly two
inputs also matches the design's two-way scope (§3.3).

Add the entry type beside `RunAttemptEntry`:

```python
@sealed
@final
@dataclass(frozen=True)
class RecordMutationEntry:
    subject: str
    corpus: str
    outcome: Moved | Consolidated

    def __post_init__(self) -> None:
        _require_str(self.subject, "record mutation entry subject")
        _require_str(self.corpus, "record mutation entry corpus")
        _require_outcome(self, self.outcome)
```

Extend the five tables:

```python
OPERATION_KINDS = ("acquisition", "audit", "consolidate", "import", "move", "re-check", "run-attempt")

Outcome: TypeAlias = (
    PublishedObservation | ByteLocatorUntested | RetrievalFailed | EvaluationFinding
    | ImportedRecords | PinnedDeclaration | RunRefusal | Moved | Consolidated
)

Entry: TypeAlias = (
    LocatorEntry | ManagedMutationEntry | DeclarationPinEntry
    | SubjectEvaluationEntry | RecordImportEntry | RunAttemptEntry | RecordMutationEntry
)

_ALLOWED_OUTCOMES[RecordMutationEntry] = (Moved, Consolidated)
_ENTRY_KINDS[RecordMutationEntry] = "record-mutation"
_OUTCOME_TYPES[Moved] = "moved"
_OUTCOME_TYPES[Consolidated] = "consolidated"
```

(Write those four as literal entries inside the existing dict literals rather than as assignments after them — match the surrounding style.)

Extend `_entry_facet` to carry the corpus:

```python
def _entry_facet(entry: Entry) -> dict[str, object]:
    row: dict[str, object] = {
        "kind": _ENTRY_KINDS[type(entry)],
        "subject": entry.subject,
        "outcome": _outcome_facet(entry.outcome),
    }
    if type(entry) is LocatorEntry:
        row["instrument_inputs"] = [list(pair) for pair in entry.instrument_inputs]
    if type(entry) is RecordMutationEntry:
        row["corpus"] = entry.corpus
    return row
```

Add `"Consolidated"`, `"Moved"` and `"RecordMutationEntry"` to `__all__`, keeping it sorted.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --project python pytest tests/test_report.py`
Expected: PASS, whole file.

- [ ] **Step 5: Run the qualification tests**

Run: `uv run --project python pytest tests/test_report.py tests/test_stored_act_report.py`
Expected: PASS. These cover report identity over the whole facet, entry-order identity-bearingness (T6), and three-valued completion (T3) — the arms the acquisition lane will build on. If `test_stored_act_report.py` round-trips reports through storage, add a `RecordMutationEntry` case there mirroring its existing per-entry cases.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/report.py python/tests/test_report.py python/tests/test_stored_act_report.py
git commit -m "feat(report): add the record-mutation entry and the two relocation operation kinds"
```

---

### Task 3: The relocation refusal vocabulary

**Files:**
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_relocation.py` (create)

**Interfaces:**
- Consumes: `errors.WriteRefused`.
- Produces: `RelocationRefused`, `DuplicateLocation`, `AddressDisagreement`, `ContractPinDisagreement`, `SameRootRefused`, `RelocationKindExcluded` — all subclasses of `WriteRefused`.

- [ ] **Step 1: Write the failing test**

Create `python/tests/test_relocation.py`:

```python
"""The two-root world-changing operations: move and consolidate.

Portable: `relocation` takes its writers as arguments, so these run against
`DefaultExecutor` behind the test recorder. What they cannot claim is cut-16
discharge — that runs on the certified engine, under the acceptance runner.
"""

from __future__ import annotations

import pytest

from beliefs.errors import (
    AddressDisagreement,
    ContractPinDisagreement,
    DuplicateLocation,
    RelocationKindExcluded,
    RelocationRefused,
    SameRootRefused,
    WriteRefused,
)


def test_every_relocation_refusal_is_a_write_refusal():
    for error in (
        RelocationRefused,
        DuplicateLocation,
        AddressDisagreement,
        ContractPinDisagreement,
        SameRootRefused,
        RelocationKindExcluded,
    ):
        assert issubclass(error, WriteRefused)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run --project python pytest tests/test_relocation.py`
Expected: FAIL with `ImportError: cannot import name 'AddressDisagreement'`

- [ ] **Step 3: Implement the vocabulary**

Add to `python/src/beliefs/errors.py`, after `ReviseOutsideAllowlist`:

```python
class RelocationRefused(WriteRefused):
    """A two-root world-changing operation refused before any transaction.

    Every relocation refusal is one of these: the operation decides in
    Science's vocabulary under both locks, before an engine lease exists.
    """


class SameRootRefused(RelocationRefused):
    """Both positions resolved to one corpus root.

    `move` has nowhere to move to, and `consolidate`'s scope is two readable
    corpora — a single corpus holding two live records at one canonical
    address needs a recovery scanner this design does not build.
    """


class AddressDisagreement(RelocationRefused):
    """`consolidate` was given two different canonical addresses.

    That is a coreference question and `consolidate` must not answer it. It is
    also the precondition that makes `consolidate` unavailable for one `uid`
    under two addresses — W8b's corruption case, refused here rather than by a
    corruption check.
    """


class DuplicateLocation(RelocationRefused):
    """`move`'s destination already holds a record at that canonical address.

    Repairing that is `consolidate`'s job, not `move`'s.
    """


class ContractPinDisagreement(RelocationRefused):
    """The receiving corpus does not pin what the relocated node needs (D7).

    Raised for a differing `science_contract`, a differing identity for a
    namespace the node's facets use, and for a namespace the receiving corpus
    pins nothing for — agreement requires exactly one identity, so a missing
    pin is a disagreement and not a permission.
    """


class RelocationKindExcluded(RelocationRefused):
    """The record's kind is excluded from every world-changing operation.

    Act-reports (T8), coordination revision records, and holdings observations.
    """
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run --project python pytest tests/test_relocation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/errors.py python/tests/test_relocation.py
git commit -m "feat(errors): add the relocation refusal vocabulary"
```

---

### Task 4: The lock-held mutation seams

**Files:**
- Modify: `python/src/beliefs/corpus.py`
- Test: `python/tests/test_corpus_write.py`

**Interfaces:**
- Consumes: `CorpusWriter._operation`, `CorpusWriter._corpus`, `CorpusWriter._view`.
- Produces, all private to the package and all assuming the caller already holds the root's lock:
  - `CorpusWriter._add_locked(node: Node) -> Node`
  - `CorpusWriter._delete_locked(ref: str) -> None`
  - `CorpusWriter._replace_locked(node: Node, expected_digest: str) -> Node`

None of the three takes an intent digest. Each executes through the operation port's ordinary `execute`, which fulfills nothing; only the report transaction calls `execute_fulfilling`. Handing a digest to a data transaction would register it as the operation's first fulfillment and leave the report as a forbidden second — the state T2's *"attempt a second fulfilling registration on one intent"* arm refuses.

- [ ] **Step 1: Write the failing tests**

Add to `python/tests/test_corpus_write.py`:

```python
def test_replace_locked_refuses_a_stale_expected_digest(writer, tmp_path):
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with writer._operation:
        with pytest.raises(WriteRefused, match="expected digest"):
            writer._replace_locked(node, expected_digest="sha256:" + "00" * 32)


def test_replace_locked_rewrites_at_the_same_uid_and_id(writer):
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    current = writer._current_digest(node.id)
    revised = node.model_copy(update={"title": "A paper, consolidated"})
    with writer._operation:
        result = writer._replace_locked(revised, expected_digest=current)
    assert (result.uid, result.id) == (node.uid, node.id)
    assert writer.read_view.get(node.id).title == "A paper, consolidated"


def test_delete_locked_removes_the_record_and_checks_nothing_else(writer):
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with writer._operation:
        writer._delete_locked(node.id)
    assert node.id not in writer.read_view
```

Adapt the membership assertion to `ReadView`'s actual API — if it has no
`__contains__`, assert `pytest.raises` on `writer.read_view.get(node.id)`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --project python pytest tests/test_corpus_write.py -k locked`
Expected: FAIL with `AttributeError: 'CorpusWriter' object has no attribute '_replace_locked'`

- [ ] **Step 3: Implement the seams**

In `python/src/beliefs/corpus.py`, add to `CorpusWriter`:

```python
    def _current_digest(self, ref: str) -> str:
        """The stored digest of `ref` as it stands, read under the lock.

        `_replace_locked`'s precondition is taken from this immediately before
        plan construction, so a raced file refuses rather than being clobbered.
        """
        return self._corpus.store.digest_of(self._relative_path(self._view.get(ref)))

    def _add_locked(self, node: Node) -> Node:
        """`add`'s body, with the lock already held by a composing operation.

        Every ordinary create check still runs, `_refuse_already_minted`
        included: this seam is a re-entry point, not a relaxation.
        """
        self._refuse_family_kinds(node)
        self._refuse_invalid(node)
        self._refuse_already_minted(node)
        self._refuse_missing_basis(node)
        self._refuse_rendering(node)
        return self._corpus.add(node)

    def _delete_locked(self, ref: str) -> None:
        """Remove one record's file, with the lock already held.

        No referential check: inbound references do not prevent removal, and
        nothing enumerates them. Deletion is a storage operation.
        """
        node = self._view.get(ref)
        self._corpus.executor.execute([DeleteOp(self._relative_path(node))])
        self._reconstruct()

    def _replace_locked(self, node: Node, expected_digest: str) -> Node:
        """Rewrite an existing `(uid, id)`, with the lock already held.

        A distinct path from `add`, whose `_refuse_already_minted` guard stays
        intact, and from `revise`, whose allowlist is display prose only. The
        expected digest is read under this same lock immediately before the
        plan; a mismatch refuses with nothing applied.
        """
        existing = self._corpus.index.by_uid.get(node.uid)
        if existing is None or existing.id != node.id:
            raise RevisionTargetMissing(f"{node.id}: exact uid and id do not identify a local node")
        if self._current_digest(node.id) != expected_digest:
            raise WriteRefused(f"{node.id}: expected digest does not match the stored record")
        self._refuse_invalid(node)
        self._refuse_rendering(node)
        return self._corpus.add(node)
```

Import `DeleteOp` from `nodes.core.write_plan` at the top of the module if it is not already imported.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --project python pytest tests/test_corpus_write.py`
Expected: PASS, whole file — the existing add/revise/retract arms must not move.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/corpus.py python/tests/test_corpus_write.py
git commit -m "feat(corpus): add the lock-held add, delete and replace seams"
```

---

### Task 5: The replacement concurrency ruling

**Files:**
- Modify: `python/src/beliefs/corpus.py:1071-1097` (the `CorpusWriter` docstring), `retract`, `supersede`
- Test: `python/tests/test_corpus_write.py`

**Interfaces:**
- Consumes: Task 4's seams.
- Produces: `retract` and `supersede` refuse a target that stopped resolving; the docstring no longer claims monotonicity.

- [ ] **Step 1: Write the failing tests**

```python
def test_retract_re_resolves_its_target_under_the_lock(writer, monkeypatch):
    """§3.6 clause 1: create-only targets are no longer monotone."""
    target = writer.add(stored.assessment_node(...))  # copy the module's existing assessment fixture
    record = stored.retraction_node(
        "r1",
        target=stored.NodeTarget(target.id, target.id, "sha256:" + "cd" * 32),
        ...,  # copy the module's existing retraction fixture arguments
    )
    with writer._operation:
        writer._delete_locked(target.id)
    with pytest.raises(WriteRefused, match="no longer resolves"):
        writer.retract(record)


def test_supersede_re_resolves_its_predecessor_under_the_lock(writer):
    predecessor = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    successor = stored.proposition_node("p2", title="p2", claim={"operator": "inhibits"})
    with writer._operation:
        writer._delete_locked(predecessor.id)
    with pytest.raises(WriteRefused, match="no longer resolves"):
        writer.supersede(successor, of=predecessor.id)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --project python pytest tests/test_corpus_write.py -k re_resolves`
Expected: FAIL — the current code raises a different error, or none.

- [ ] **Step 3: Implement re-resolution and rewrite the docstring**

In `retract` and `supersede`, immediately before plan construction and inside the existing `with self._operation:` block, re-read the target:

```python
        try:
            self._view.get(target_ref)
        except KeyError as caught:
            raise RelocationRefused(
                f"{target_ref}: the target no longer resolves in this corpus; "
                "a concurrent move or deletion removed it (world-changing families §3.6)"
            ) from caught
```

Use each method's own name for `target_ref` — the retraction's resolved target, and `of` for supersede. Match `KeyError` to whatever `ReadView.get` actually raises.

Replace the `CorpusWriter` docstring's last paragraph:

```python
    **The world-changing families exist, so no target is monotone.** Consolidate
    and move can remove a record another operation resolved, so `retract` and
    `supersede` re-resolve their target under this lock immediately before plan
    construction and refuse if it has gone (world-changing families §3.6). The
    collision predicates remain what they were: two planners can each pass
    `assert_addable` for one uid under different ids, so the single-planner
    restriction stands — in-process this lock, cross-process a stated
    deployment obligation whose violation is detected loudly.
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --project python pytest tests/test_corpus_write.py`
Expected: PASS, whole file.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/corpus.py python/tests/test_corpus_write.py
git commit -m "fix(corpus): re-resolve create-only targets under the lock"
```

---

### Task 6: Ordered acquisition and the contract-agreement predicate

**Files:**
- Create: `python/src/beliefs/relocation.py`
- Test: `python/tests/test_relocation.py`

**Interfaces:**
- Produces:
  - `relocation._both_locks(a: CorpusWriter, b: CorpusWriter) -> ContextManager[None]` — acquires each distinct resolved root once, in sorted path order
  - `relocation._refuse_contract_disagreement(node: Node, source: CorpusWriter, destination: CorpusWriter) -> None`
  - `relocation._refuse_excluded_kind(node: Node) -> None`

- [ ] **Step 1: Write the failing tests**

```python
def test_both_locks_acquires_one_distinct_root_once(tmp_path):
    writer = CorpusWriter(tmp_path, Recorder)
    twin = CorpusWriter(tmp_path, Recorder)   # same root, second handle
    with relocation._both_locks(writer, twin):
        pass  # reentrancy makes this safe; the point is that it does not hang


def test_both_locks_is_order_independent(tmp_path):
    a = CorpusWriter(tmp_path / "a", Recorder)
    b = CorpusWriter(tmp_path / "b", Recorder)
    with relocation._both_locks(a, b):
        pass
    with relocation._both_locks(b, a):
        pass


def test_relocation_refuses_a_differing_science_contract(...):
    """D7 rule 3, base contract: a node with no domain facets at all."""
    with pytest.raises(ContractPinDisagreement, match="science_contract"):
        relocation._refuse_contract_disagreement(plain_node, source, destination_with_other_base)


def test_relocation_refuses_a_differing_domain_identity(...):
    with pytest.raises(ContractPinDisagreement, match="biology"):
        relocation._refuse_contract_disagreement(biology_node, source, destination_with_other_biology)


def test_relocation_refuses_a_missing_pin(...):
    """Agreement requires exactly one identity; pinning nothing is not permission."""
    with pytest.raises(ContractPinDisagreement, match="pins no identity"):
        relocation._refuse_contract_disagreement(biology_node, source, destination_pinning_nothing)


def test_relocation_refuses_an_act_report(...):
    with pytest.raises(RelocationKindExcluded, match="act-report"):
        relocation._refuse_excluded_kind(act_report_node)
```

Build the corpora with `fixtures_cut6.PINS` as the base and a second pin map that differs — follow how `test_consulted.py` constructs disagreeing pins.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --project python pytest tests/test_relocation.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'beliefs.relocation'`

- [ ] **Step 3: Implement the module's foundation**

```python
"""The two-root world-changing operations: `move` and `consolidate`.

This module **composes** two `CorpusWriter`s and subclasses neither: an
operation over two corpus roots cannot honestly be a method on an object bound
to one. `atoms` §12.2 keys an engine root on a corpus root, so two corpora are
two chains and two operation ports — these operations are never one
transaction, and §3.5 of the design enumerates every durable prefix instead of
pretending otherwise.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path

from nodes.core.node import Node

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import ContractPinDisagreement, RelocationKindExcluded, SameRootRefused

EXCLUDED_KINDS = ("act-report", "coordination-revision", "holdings-observation")


@contextmanager
def _both_locks(first: CorpusWriter, second: CorpusWriter):
    """Both roots' operation locks, each distinct root once, in sorted order.

    Sorting is what makes two opposing relocations deadlock-free. Deduplicating
    on the resolved path is the rule; the lock's per-thread reentrancy makes an
    accidental second acquisition harmless rather than load-bearing.
    """
    roots = {str(Path(w.root).resolve()): w for w in (first, second)}
    with ExitStack() as stack:
        for key in sorted(roots):
            stack.enter_context(roots[key]._operation)
        yield


def _refuse_same_root(first: CorpusWriter, second: CorpusWriter) -> None:
    if Path(first.root).resolve() == Path(second.root).resolve():
        raise SameRootRefused(
            "a relocation needs two distinct corpus roots; repairing one corpus holding two live "
            "records at one canonical address needs a recovery scanner this design does not build"
        )


def _refuse_excluded_kind(node: Node) -> None:
    if node.kind in EXCLUDED_KINDS:
        raise RelocationKindExcluded(
            f"{node.id}: {node.kind} is excluded from every world-changing operation"
        )


def _refuse_contract_disagreement(
    node: Node, source: CorpusWriter, destination: CorpusWriter
) -> None:
    """D7 rule 3, for `move` and `consolidate` alike.

    Agreement requires each consulted namespace to resolve to **exactly one**
    identity, so a receiving corpus that pins nothing for a namespace the node
    uses disagrees — "not different" is too weak a test.
    """
    source_pins = source.manifest_pins()
    destination_pins = destination.manifest_pins()
    if source_pins.science_contract != destination_pins.science_contract:
        raise ContractPinDisagreement(
            f"{node.id}: the receiving corpus pins science_contract "
            f"{destination_pins.science_contract!r}, not {source_pins.science_contract!r}; "
            "base-contract agreement is not conditional on facet content"
        )
    for namespace in stored.facet_namespaces(node):
        theirs = destination_pins.domains.get(namespace)
        if theirs is None:
            raise ContractPinDisagreement(
                f"{node.id}: the receiving corpus pins no identity for {namespace!r}, "
                "and agreement requires exactly one"
            )
        if theirs != source_pins.domains[namespace]:
            raise ContractPinDisagreement(
                f"{node.id}: the receiving corpus pins {theirs!r} for {namespace!r}, "
                f"not {source_pins.domains[namespace]!r}"
            )
```

`CorpusWriter.root` and `CorpusWriter.manifest_pins()` may not exist yet — if not, add them as thin accessors over `self._state` and `world.load_manifest(self.root).profile` in the same commit. `stored.facet_namespaces(node)` likewise: if there is no such helper, add one returning the sorted namespace prefixes of the node's facet keys, and unit-test it.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --project python pytest tests/test_relocation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/relocation.py python/src/beliefs/corpus.py python/src/beliefs/stored.py python/tests/test_relocation.py
git commit -m "feat(relocation): add ordered acquisition and the contract-agreement predicate"
```

---

### Task 7: `move`

**Files:**
- Modify: `python/src/beliefs/relocation.py`
- Test: `python/tests/test_relocation.py`, `python/tests/test_relocation_rows.py` (create)

**Interfaces:**
- Produces: `relocation.move(source, destination, ref, *, actor, observer, instrument, opened_at, closed_at) -> tuple[Node, ActReport, ActReport]` — destination report first.

- [ ] **Step 1: Write the failing operation tests**

```python
def test_move_relocates_without_touching_identity(source_writer, destination_writer):
    node = source_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    moved, destination_report, source_report = relocation.move(
        source_writer, destination_writer, node.id,
        actor="a", observer="o", instrument="i",
        opened_at="2026-09-03T10:00:00Z", closed_at="2026-09-03T10:00:01Z",
    )
    assert (moved.uid, moved.id) == (node.uid, node.id)
    assert moved.deprecated_ids == node.deprecated_ids
    assert destination_writer.read_view.get(node.id).uid == node.uid
    with pytest.raises(KeyError):
        source_writer.read_view.get(node.id)


def test_move_refuses_an_occupied_destination(source_writer, destination_writer):
    node = source_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    destination_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with pytest.raises(DuplicateLocation):
        relocation.move(source_writer, destination_writer, node.id, actor="a", observer="o",
                        instrument="i", opened_at="...", closed_at="...")


def test_move_mints_one_report_per_root_under_one_token(source_writer, destination_writer):
    node = source_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    _, destination_report, source_report = relocation.move(...)
    assert destination_report.event_token == source_report.event_token
    assert destination_report.operation == source_report.operation == "move"
    assert destination_report.opened_at == source_report.opened_at
    assert destination_report.identity() != source_report.identity()   # different entries
```

- [ ] **Step 2: Write the failing row tests**

Create `python/tests/test_relocation_rows.py` with the cut's selected arms:

```python
def test_w5_a_move_changes_only_location(...):
    """W5: uid, canonical address, deprecated_ids, inbound references and the
    belief digest all unchanged."""


def test_w5_a_producers_map_member_moves_without_moving_the_digest(...):
    """W5's second half: move a dataset that appears in the producers map;
    assert belief_input_digest unchanged though the address map and BOTH
    corpus-state identities moved, and that re-deriving mints a new receipt
    naming the same snapshot."""


def test_g3_location_is_not_a_closure_member(...):
    """G3's negative: move an entity between corpora; the digest is unchanged,
    pinning the member as the producer snapshot and not the index carrying it."""


def test_d7_a_permitted_move_preserves_w5(...):
def test_d7_refuses_a_domain_facet_move_across_identities(...):
def test_d7_refuses_a_base_contract_move_for_a_facetless_node(...):
def test_d7_refuses_a_missing_pin(...):


def test_c3_an_in_coverage_move_leaves_the_digest_and_moves_the_receipt(...):
    """C3's move clause: content identities unchanged → digest unchanged, and
    the receipt records the new corpus states."""


def test_r23_location_is_not_evidence(...):
def test_r23_the_receipt_is_not_a_belief_input(...):
    """Both covered corpus-state identities change, the producers map does
    not, and the belief digest is unchanged."""


def test_t2_a_move_is_one_intent_and_one_report_in_each_root(...):
    """T2 read root-locally over a composite operation."""


def test_t8_move_refuses_an_act_report_subject(...):
```

Write each body against the fixtures in `fixtures_cut6.py` and `closure_fixtures.py`; the producers-map and receipt arms need a published epoch, so follow `test_epoch.py`'s construction.

- [ ] **Step 3: Run to verify they fail**

Run: `uv run --project python pytest tests/test_relocation.py tests/test_relocation_rows.py`
Expected: FAIL with `AttributeError: module 'beliefs.relocation' has no attribute 'move'`

- [ ] **Step 4: Implement `move`**

```python
def move(source: CorpusWriter, destination: CorpusWriter, ref: str, *,
         actor: str, observer: str, instrument: str,
         opened_at: str, closed_at: str) -> tuple[Node, ActReport, ActReport]:
    """Relocate one record between corpora, destination-first.

    Order is load-bearing: a crash after the destination create and before the
    source delete leaves one canonical address in two corpora — world §5's
    `duplicate location`, whose designed exit is `consolidate`. A move
    therefore loses nothing at any interruption point.
    """
    token = secrets.token_hex(16)
    with _both_locks(source, destination):
        _refuse_same_root(source, destination)
        node = source.read_view.get(ref)
        _refuse_excluded_kind(node)
        _refuse_contract_disagreement(node, source, destination)
        _refuse_occupied_destination(node, destination)

        destination_intent = destination._append_operation_intent("move", token, actor)
        source_intent = source._append_operation_intent("move", token, actor)

        moved = destination._add_locked(node)
        source._delete_locked(ref)

        outcome = Moved(
            source_corpus=source.corpus_id,
            destination_corpus=destination.corpus_id,
            ref=ref,
        )
        destination_report = destination._publish_operation_report(
            "move", token, destination_intent, actor=actor, observer=observer, instrument=instrument,
            opened_at=opened_at, closed_at=closed_at,
            entries=(RecordMutationEntry(subject=ref, corpus=destination.corpus_id, outcome=outcome),),
        )
        source_report = source._publish_operation_report(
            "move", token, source_intent, actor=actor, observer=observer, instrument=instrument,
            opened_at=opened_at, closed_at=closed_at,
            entries=(RecordMutationEntry(subject=ref, corpus=source.corpus_id, outcome=outcome),),
        )
    return moved, destination_report, source_report
```

Add the two `CorpusWriter` helpers this needs, factored out of `import_bundle`'s existing body so there is one intent/report path and not two:

```python
    def _append_operation_intent(self, kind: str, token: str, actor: str) -> str:
        """Append one operation intent and return its digest."""

    def _publish_operation_report(self, kind, token, intent_digest, *, actor, observer,
                                  instrument, opened_at, closed_at, entries) -> ActReport:
        """Mint the terminal report and execute it as the intent's one fulfillment."""
```

`_publish_operation_report` is the **only** caller of `execute_fulfilling` on this path; `_add_locked` and `_delete_locked` use ordinary `execute`.

- [ ] **Step 5: Run to verify they pass**

Run: `uv run --project python pytest tests/test_relocation.py tests/test_relocation_rows.py`
Expected: PASS

- [ ] **Step 6: Run the whole suite**

Run: `uv run --project python pytest`
Expected: PASS. Quote the summary line.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/relocation.py python/src/beliefs/corpus.py python/tests/
git commit -m "feat(relocation): add the destination-first cross-corpus move"
```

---

### Task 8: `consolidate`

**Files:**
- Modify: `python/src/beliefs/relocation.py`
- Test: `python/tests/test_relocation.py`, `python/tests/test_relocation_rows.py`

**Interfaces:**
- Produces: `relocation.consolidate(keep, other, *, rationale, actor, observer, instrument, opened_at, closed_at) -> tuple[Node, ActReport, ActReport]`, where `keep` and `other` are each `tuple[CorpusWriter, str]`. The kept root's report is first.

- [ ] **Step 1: Write the failing tests**

```python
def test_consolidate_unions_relations_and_preserves_both_bases(...):
    """W16: one address survives, outgoing relations unioned, divergent lineage
    bases both preserved, no redirect, no inbound rewrite, no deprecated_ids
    entry, no coreference-attestation, no balance moved."""


def test_consolidate_preserves_a_shared_uid(...):
def test_consolidate_selects_one_of_two_distinct_uids_and_mints_no_third(...):
def test_consolidate_refuses_two_different_addresses(...):
    with pytest.raises(AddressDisagreement):
        ...
def test_consolidate_is_not_offered_for_one_uid_under_two_addresses(...):
    """W8b's first arm: it refuses on the one-address precondition, not on a
    corruption check — assert the error type is AddressDisagreement."""
def test_consolidate_refuses_a_same_root_pair(...):
    with pytest.raises(SameRootRefused):
        ...
def test_consolidate_refuses_an_excluded_kind_on_either_input(...):
    """T8: two replicated act-reports at one address must not be consolidable,
    which would remove one through an ordinary API."""


def test_m3_consolidating_equal_basis_retraction_replicas_leaves_the_counter_retraction(...):
    """M3's replica arm: consolidate two equal-basis replicas of one retraction
    held in two corpora while a counter-retraction R already targets it; assert
    it succeeds, the retraction's content identity is unchanged, and R is
    neither rewritten nor re-minted."""


def test_consolidate_is_idempotent_over_an_already_unioned_survivor(...):
    """§3.3: the union is order-independent and idempotent, which is what makes
    a re-run over prefixes 1–4 safe."""


def test_t2_a_consolidate_is_one_intent_and_one_report_in_each_root(...):
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --project python pytest tests/test_relocation.py tests/test_relocation_rows.py -k consolidate or m3`
Expected: FAIL with `AttributeError: module 'beliefs.relocation' has no attribute 'consolidate'`

- [ ] **Step 3: Implement `consolidate`**

```python
def consolidate(keep: tuple[CorpusWriter, str], other: tuple[CorpusWriter, str], *,
                rationale: str, actor: str, observer: str, instrument: str,
                opened_at: str, closed_at: str) -> tuple[Node, ActReport, ActReport]:
    """Repair a duplicate location: two records at one canonical address, in
    two corpora.

    Requires one canonical address. Unions outgoing relations, preserves
    divergent lineage bases, writes no redirect and rewrites no inbound
    reference — no address retires, so nothing needs one. Never mints a `uid`:
    a shared one is preserved, and of two distinct ones `keep`'s survives.
    """
    keep_writer, keep_ref = keep
    other_writer, other_ref = other
    token = secrets.token_hex(16)
    with _both_locks(keep_writer, other_writer):
        _refuse_same_root(keep_writer, other_writer)
        survivor = keep_writer.read_view.get(keep_ref)
        loser = other_writer.read_view.get(other_ref)
        _refuse_excluded_kind(survivor)
        _refuse_excluded_kind(loser)
        _refuse_address_disagreement(survivor, loser)
        _refuse_contract_disagreement(loser, other_writer, keep_writer)

        merged = _reconcile(survivor, loser)
        expected = keep_writer._current_digest(keep_ref)

        keep_intent = keep_writer._append_operation_intent("consolidate", token, actor)
        other_intent = other_writer._append_operation_intent("consolidate", token, actor)

        result = keep_writer._replace_locked(merged, expected_digest=expected)
        other_writer._delete_locked(other_ref)
        ...  # reports, exactly as `move` publishes them, with a Consolidated outcome
    return result, keep_report, other_report
```

`_reconcile` is the reconciliation rule, and must be order-independent and idempotent:

```python
def _reconcile(survivor: Node, loser: Node) -> Node:
    """`keep`'s whole authored record, carrying `keep`'s uid, with the unions.

    Order-independent and idempotent: consolidating an already-unioned survivor
    with the same loser returns an equal node, which is what makes a re-run the
    recovery for §3.5's prefixes 1–4.
    """
    relations = tuple(sorted(set(survivor.relations) | set(loser.relations)))
    deprecated = tuple(sorted(set(survivor.deprecated_ids) | set(loser.deprecated_ids)))
    facets = stored.union_lineage_bases(survivor, loser)
    return survivor.model_copy(update={"relations": relations, "deprecated_ids": deprecated, "facets": facets})
```

`stored.union_lineage_bases` produces the tagged basis: two equal bases stay `single`; two differing bases become `conflict([both], sorted)`; two `conflict`s union their routes; and a `conflict` with fewer than two distinct routes is unconstructible. Add it to `stored.py` with its own unit tests in `python/tests/test_stored.py` in this same task.

`_refuse_address_disagreement` compares the two records' canonical addresses and raises `AddressDisagreement` when they differ — which is also what makes `consolidate` unavailable for one `uid` under two addresses, refusing on the precondition rather than on a corruption check.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --project python pytest tests/test_relocation.py tests/test_relocation_rows.py tests/test_stored.py`
Expected: PASS

- [ ] **Step 5: Run the whole suite**

Run: `uv run --project python pytest`
Expected: PASS. Quote the summary line.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/relocation.py python/src/beliefs/stored.py python/tests/
git commit -m "feat(relocation): add consolidate, the duplicate-location exit"
```

---

### Task 9: The crash prefixes and the recovery table

**Files:**
- Test: `python/tests/test_relocation_recovery.py` (create)

**Interfaces:**
- Consumes: `move`, `consolidate`, and the seams.
- Produces: nothing importable — this task is evidence for design §3.5.

- [ ] **Step 1: Write the failing tests**

Drive each prefix by raising from a monkeypatched seam, then assert the observable state and the recovery:

```python
@pytest.mark.parametrize("stop_after", ["destination-intent", "source-intent", "destination-create", "source-delete", "destination-report"])
def test_move_prefixes_are_exactly_the_enumerated_states(stop_after, ...):
    """§3.5's move table: every durable prefix, and no other."""


def test_a_move_interrupted_at_the_destination_create_is_a_duplicate_location(...):
    """And `move` itself now refuses — precondition 5 — which is correct: the
    state is no longer a move's pre-state."""
    with pytest.raises(DuplicateLocation):
        relocation.move(source_writer, destination_writer, ref, ...)


def test_that_duplicate_location_is_repaired_by_consolidate(...):
    """The recovery table's `move` step-4 row."""


def test_a_move_interrupted_after_the_source_delete_leaves_unfinished_intents(...):
    """Data final; nothing completes it. Assert the operation reads `unfinished`
    under T3's three-valued completion, and that re-running `move` refuses
    because the source no longer holds the record."""


def test_consolidate_prefixes_1_to_4_are_repaired_by_re_running(...):
def test_consolidate_after_the_other_delete_leaves_unfinished_intents(...):
    """Re-running now refuses: `other` no longer resolves."""


def test_a_move_never_loses_the_record_at_any_prefix(...):
    """The argument for the two operations sharing a cut: at every prefix the
    record is readable in at least one corpus."""
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --project python pytest tests/test_relocation_recovery.py`
Expected: FAIL — the file's helpers do not exist yet.

- [ ] **Step 3: Implement the harness**

Add a `stop_after` fault-injection helper local to the test module — monkeypatch the named seam to raise a sentinel `_Stop` exception after the real call, so the durable prefix is genuinely reached before the operation aborts. Do not add fault injection to `relocation.py` itself: production code must not carry a test seam.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --project python pytest tests/test_relocation_recovery.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/tests/test_relocation_recovery.py
git commit -m "test(relocation): pin every durable prefix and its recovery"
```

---

### Task 10: N2 declarations and the acceptance runner

**Files:**
- Create: `python/tests/n2_arms_cut16.py`, `python/tests/acceptance/test_n2_cut16.py`, `python/tools/cut16_acceptance.py`
- Test: the runner itself

**Interfaces:**
- Consumes: every selected arm from Tasks 7–9.
- Produces: the discharge evidence Task 11 records.

- [ ] **Step 1: Enumerate the declarations**

Create `python/tests/n2_arms_cut16.py` following `n2_arms_cut7.py`'s shape: one entry per selected arm from the frozen cut's §3, each naming the test that runs it. The count here must equal the frozen §4 accounting exactly — a mismatch is a freeze violation, not a bookkeeping slip, and is recorded as a dated deviation.

- [ ] **Step 2: Write the acceptance runner**

Create `python/tools/cut16_acceptance.py` modelled on `cut15_acceptance.py`:

```python
PREFIX_RUNNERS = ("cut15_acceptance.py",)
PHASE_MODULES = ("test_relocation_acceptance.py", "test_n2_cut16.py")
```

Cut 15 is the highest-numbered discharged cut, so it is the prefix (roadmap rule 5). The work directory defaults beside the checkout — `PYTHON_ROOT.parent / ".cut16-acceptance"` — because `/tmp`, `/dev/shm` and the scratch volume all fail the durability allowlist.

- [ ] **Step 3: Run the portable suite**

Run: `uv run --project python pytest`
Expected: PASS. Quote the summary line.

- [ ] **Step 4: Run the acceptance runner on the certified volume**

Run: `uv run --project python python tools/cut16_acceptance.py`
Expected: exit 0. If it exits with the probe's refusal code, the kernel has outrun the `atoms` A8 allowlist — that is a recertification matter (`atoms-recertify.timer`), not a regression in this work.

- [ ] **Step 5: Commit**

```bash
git add python/tests/n2_arms_cut16.py python/tests/acceptance/ python/tools/cut16_acceptance.py
git commit -m "test(cut16): declare the N2 arms and add the acceptance runner"
```

---

### Task 11: Discharge, re-rank, and merge

**Files:**
- Create: `docs/plans/2026-09-03-conformance-cut-16-results.md`
- Create: `docs/plans/2026-09-03-relocation-rulings-ledger.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md` (rewritten whole)

**Interfaces:**
- Consumes: Task 10's discharge evidence.
- Produces: the re-ranked roadmap the next lane reads.

- [ ] **Step 1: Write the results record**

Follow `docs/plans/2026-09-01-conformance-cut-15-results.md`: §1 what ran and where (the exact commit, the certified tuple, the runner invocation), §2 the selected rows with each one's full/part reading, §3 corrections and deviations, §4 what this run does not claim.

§4 must state plainly: no deletion arm ran; W16 is part, its remaining arm belonging to the deletion cut; T2 and R23 stay part; nothing here closes L13, and removal classification is not exercised at all.

- [ ] **Step 2: Commit the rulings ledger**

Any ruling made during implementation goes in `docs/plans/2026-09-03-relocation-rulings-ledger.md`, committed to that tracked path **before the worktree is removed**. Slice 2 lost R1–R15 by leaving its ledger in a worktree.

- [ ] **Step 3: Rewrite the ledger's Current state and re-rank the roadmap**

Add the relocation cut's bullet to the ledger's implemented list. Rewrite the roadmap whole: `Ranked at` becomes cut 16, `consolidate-family` stays in the boundary index with its remaining rows, and Appendix A and B are regenerated.

Run: `uv run --project python python tools/roadmap_status.py`

- [ ] **Step 4: Run the guard**

Run: `uv run --project python pytest tests/test_designs_corpus.py`
Expected: PASS — `test_the_roadmap_and_ledger_name_the_same_boundaries` holds `Ranked at` to the newest results record.

- [ ] **Step 5: Commit and merge**

```bash
git add docs
git commit -m "docs(mutation): discharge conformance cut 16 and re-rank the roadmap"
git checkout main
git merge --no-ff design/consolidate-family
```

- [ ] **Step 6: Draft the deletion cut's plan**

The deletion cut's arm inventory depends on what this results record actually discharged — W16's remainder and T2's reading in particular. Re-read the spec's §6.2 and §6.3 against it, then write `docs/superpowers/plans/<date>-deletion-cut.md`.

---

## Self-Review

**Spec coverage.** §1 → Task 1. §2.1 → Task 5 (ruling) and Task 1 (amendment). §2.2, §2.5 → the deletion cut, correctly absent here. §2.3's relocation half → Tasks 7, 8. §2.4 → Tasks 1, 2. §3.0 → Task 6. §3.1 → the deletion cut. §3.2 → Task 7. §3.3 → Task 8. §3.4 → Task 4. §3.5 → Task 9. §3.6 → Task 5. §4 → Task 2. §5 → Task 6. §6.1 → Tasks 7, 8. §6.2, §6.3 → the deletion cut. §7 → the deletion cut. §8's relocation limitations → Task 1's §7. §9 → Global Constraints. §10 → Task 1. §11 → no task; it is rationale.

**Gap accepted deliberately:** design §6.1 lists R23's consolidate clauses over the tagged basis, whose deletion-dependent arm (*the conflict survives deleting either producing run*) cannot run here. Task 8 covers the constructible half; the frozen cut must mark R23 part and name the deletion cut for the rest.

**Type consistency.** `_add_locked(node)`, `_delete_locked(ref)`, `_replace_locked(node, expected_digest)` — no intent digest, consistent across Tasks 4, 7, 8. `Moved`/`Consolidated`/`RecordMutationEntry` field names match between Task 2's implementation and Tasks 7–8's construction. `_both_locks`, `_refuse_same_root`, `_refuse_excluded_kind`, `_refuse_contract_disagreement` are defined in Task 6 and used under those exact names in Tasks 7 and 8.

**Unverified helpers, flagged rather than assumed:** `CorpusWriter.root`, `CorpusWriter.corpus_id`, `CorpusWriter.manifest_pins()`, `CorpusWriter._relative_path`, `stored.facet_namespaces`, `stored.union_lineage_bases`, and `Corpus.store.digest_of`. Tasks 4, 6 and 8 each say to add the ones that turn out not to exist, with unit tests, in the same commit.
