# Relocation cut implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `move` and `consolidate` — the two-root world-changing operations — and discharge the relocation cut, closing G3 and D7 and reading W5 in full.

**Architecture:** A new `beliefs.relocation` module composes two `CorpusWriter`s rather than subclassing one, because an operation over two corpus roots cannot honestly be a method on an object bound to one. Each operation acquires both per-root operation locks in sorted resolved-path order, validates every precondition under them, then runs a fixed sequence of one-transaction steps: intent per root, data per root, fulfilling report per root. `move` is destination-first, so its only partial state is a duplicate location — which is exactly what `consolidate` repairs, and the reason the two ship together.

**Tech Stack:** Python 3.12+, `nodes` core (`Node`, `Relation`, `CreateOp`/`ReplaceOp`/`DeleteOp`, `DefaultExecutor`), the certified `atoms` engine behind `beliefs.root`, pytest, ruff, pyright, `uv`.

**Spec:** `docs/superpowers/specs/2026-09-03-world-changing-families-design.md` — read it alongside this plan. Every task below argues from a numbered section of it.

**Task record:** `beliefs-676a2c` ("Deliver consolidate, move, and managed deletion"). Run `tasks start beliefs-676a2c` before Task 1 and `tasks note` at each checkpoint.

## Global Constraints

- **The cut is frozen before its code exists.** Task 1 lands the frozen cut document; no implementation task may add, remove, or reword a selected arm afterwards. A post-freeze discovery is a dated deviation in the results record, never an edit to the frozen text.
- **Gates, from `AGENTS.md`.** From `python/`: `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen pyright`. From `ts/`: `npm ci`, `npm test`, `npm run typecheck`, `npm run check`. Before completion: `tasks check`, zero errors, every warning reported — registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental.
- **Always `--frozen`.** Never let a test run resolve new dependencies.
- **Do not pass `-q` to pytest.** `python/pyproject.toml` already sets `addopts = "-q --ignore=tests/acceptance"`; doubling it hides the summary line, and any claim about test counts must quote that line. Never pipe pytest through `tail` without `set -o pipefail` — it fakes exit 0.
- **Discharge runs on the certified volume**, which is the repository's own. `/tmp`, `/dev/shm` and the scratch volume all fail the durability allowlist; the acceptance work directory lives beside the checkout.
- **Conventional commits, and no AI-attribution trailer or footer** in any commit message, PR, or comment.
- **One worktree for the lane**, `.worktrees/consolidate-family`, on branch `design/consolidate-family`. `main` is checked out at the repository root, so the final merge runs **from the root, not from this worktree** — `git checkout main` here will fail.
- **Every mutation is an `atoms` effect** executed by the certified engine under the per-root operation lock.
- **Files shared with other lanes**, per roadmap concurrency rule 3: `errors.py`, `test_designs_corpus.py`, the adoption ledger, the roadmap, the guide index, plus `world/registry.py`, `world/verify.py`, `report.py`, `stored.py`, `boundary.py`, `corpus.py`. A later merge resolves toward the earlier one.

## Interfaces verified against the tree

Do not re-derive these; they were inspected while writing this plan.

| fact | consequence |
|---|---|
| `DeleteOp(path, expected_digest)`, `ReplaceOp(path, content, expected_digest)`, `CreateOp(path, content)` | a delete needs a digest |
| `rules.member_content_digest(content) -> str` is a **bare 64-hex** sha256, no `sha256:` prefix | never write `sha256:…` for a plan digest |
| no `expected_digest` appears anywhere in `corpus.py`; `revise` replaces via `self._corpus.add(node)` | `_replace_locked` takes no digest — the substrate reads it pre-plan |
| `CorpusWriter.add` body is `_refuse_family_kinds(node)`, `_refuse(node)`, `self._corpus.add(node)` | `_add_locked` mirrors exactly that, minus the lock acquisition |
| `_refuse(node, *, document_validated=False, view=None)` centralises already-minted, basis, eligibility, display-facet, validity, governed-stamp, rendering and collision | never hand-roll a subset |
| `ReadView.get` propagates `nodes`' `RefError` for an absent ref | catch `RefError`, not `KeyError` |
| `Relation` is **unhashable**; `Node.relations` is `list[Relation]`, `Node.deprecated_ids` is `list[str]` | no `set()` over relations, and updates must stay lists |
| `stored.stamp_semantic_identity(node)` restamps; `SEMANTIC_IDENTITY_FACET` is covered | any covered-facet change must restamp |
| `stored._REPORT_ENTRY_OUTCOMES` and `_valid_report_entry` are a closed stored grammar | a new entry kind and its `corpus` field must be added there too |
| `test_inertness.py::test_t1_the_constructor_is_reachable_only_from_the_boundary` asserts `_mint_report` callers are exactly `["boundary.py", "report.py"]` | the mint helper lives in `boundary.py`, as `_mint_import_report` does |
| `coordination.COORDINATION_KINDS = ("project","question","hypothesis","topic","theme","task","decision","note")` | there is no `"coordination-revision"` kind |

## File Structure

| file | responsibility | task |
|---|---|---|
| `docs/designs/2026-09-03-world-changing-families-design.md` | the design, promoted from `specs/` | 1 |
| `docs/designs/2026-09-03-conformance-cut-N.md` | the frozen relocation cut | 1 |
| `python/src/beliefs/report.py` | `RecordMutationEntry`, `Moved`, `Consolidated`, the two operation kinds | 2 |
| `python/src/beliefs/stored.py` | the stored report-entry grammar; `union_lineage_bases` | 2, 9 |
| `python/src/beliefs/errors.py` | the relocation refusal vocabulary | 3 |
| `python/src/beliefs/corpus.py` | the three lock-held seams; re-resolution; the rewritten docstring | 4, 8 |
| `python/src/beliefs/boundary.py` | `_mint_relocation_report` | 6 |
| `python/src/beliefs/relocation.py` | `move`, `consolidate`, locks, predicates | 5, 7, 9 |
| `python/tests/test_relocation.py` | operation and refusal arms | 3, 5, 7, 9 |
| `python/tests/test_relocation_rows.py` | W5, W16, G3, D7, C3, R23, M3, T2, T8 | 7, 9 |
| `python/tests/test_relocation_recovery.py` | §3.5's prefixes and recovery table | 10 |
| `python/tests/acceptance/test_relocation_acceptance.py` | the durable arms, on the certified engine | 11 |
| `python/tests/n2_arms_cutN.py`, `python/tests/acceptance/test_n2_cutN.py` | the N2 declaration inventory | 11 |
| `python/tools/cutN_acceptance.py` | the runner, with cut 15's as prefix | 11 |
| `docs/plans/2026-09-03-conformance-cut-N-results.md` | the discharge record | 12 |

`N` is the cut number, claimed at freeze in Task 1. Substitute it everywhere.

---

### Task 1: Bank the design and freeze the relocation cut

**Files:**
- Create: `docs/designs/2026-09-03-world-changing-families-design.md` (git mv from `docs/superpowers/specs/`)
- Create: `docs/designs/2026-09-03-conformance-cut-N.md`
- Modify: `docs/designs/2026-08-19-family-adapters-design.md` (§5.3)
- Modify: `docs/designs/2026-08-11-act-report-design.md` (§2, §2.1, §2.2)
- Modify: `docs/designs/2026-08-03-correction-lifecycle-design.md` (C1)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `README.md`, `python/tests/test_designs_corpus.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the frozen arm inventory every later task tests against; the cut number `N`.

- [ ] **Step 1: Claim the cut number**

Run: `ls docs/designs/ docs/plans/ | grep -o 'conformance-cut-[0-9]*' | sort -t- -k3 -n | tail -1`

Cut 15 is the newest discharged. Take **16** unless another lane has already frozen a 16. Roadmap rule 1: the number is claimed at freeze, in freeze order, and a lane that discharges first does not renumber.

- [ ] **Step 2: Promote the design**

```bash
git mv docs/superpowers/specs/2026-09-03-world-changing-families-design.md \
       docs/designs/2026-09-03-world-changing-families-design.md
```

Set its status to `**Status:** Banked 2026-09-03. Relocation cut frozen as conformance cut 16; the deletion cut is not yet frozen.` and fix the two header links — from `docs/designs/` they become `../plans/2026-08-29-implementation-roadmap.md` and `2026-08-19-family-adapters-design.md`.

- [ ] **Step 3: Amend the family-adapters design (§5.3)**

Replace §5.3's body with:

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

- [ ] **Step 4: Amend the act-report design (five clauses)**

Append after §2.2's outcome list:

```markdown
*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §2.4, five
clauses. **Operation kinds** gain `consolidate` and `move`. **Act kinds** gain
`record-mutation`. **Subject:** a `record-mutation` entry's subject is a record
ref together with the corpus it is read from or written to — a bare ref cannot
name a side of a two-root operation. **Outcomes:** `record-mutation` takes
`moved` or `consolidated`, and nothing is borrowed from another kind;
`consolidated` carries `retired_uids`, a sequence that is **empty** where the
inputs shared a `uid` and nothing retired. **Composite root-local operations:**
an operation may span two corpus roots under one `event_token` and one
`opened_at`/`closed_at`, minting one intent and one terminal report **per
touched root**; T2 is read root-locally over such an operation.)*
```

- [ ] **Step 5: Amend the correction-lifecycle design (C1)**

This amendment is **required in this banking change** — design §10 names it, and the deletion cut's C1 re-read has nothing to re-read against without it. Append to C1's row, or immediately beneath the guarantee table:

```markdown
*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §2.2: C1 is
a claim about the **retraction family** — retraction is additive, and the
retraction operation never edits, removes, or re-addresses its target. It is not
a claim that no operation anywhere can remove a record; the world-changing
families' `delete` does, and is refused by no referential check. Cut 5's reading
of C1 stands as a reading of the pre-amendment text and is not edited; the
deletion cut re-reads C1 against this narrowing.)*
```

- [ ] **Step 6: Write the frozen cut document**

Create `docs/designs/2026-09-03-conformance-cut-16.md` following `docs/designs/2026-08-19-conformance-cut-5.md`: §1 what this cut is, §2 the boundary (in/out of scope), §3 the selection with each source row quoted verbatim in a fenced block followed by **Selected** / **Prior, not selected again** / **Deferred** bullets, §4 accounting, §5 N2 and acceptance obligations, §6 the second reader, §7 limitations.

§2's out-of-scope list names: `delete` and every deletion arm; the audit; cross-corpus record reads through the world resolver; the rules store; `world-resolution`'s snapshot, coverage and divergence clauses; the M1 resolver and the claim restore seam.

§3 selects, from design §6.1: W5 (full), W16 (part), G3, D7, C3's move clause, R23's two move clauses and its consolidate clauses, M3's replica arm, T2's per-kind arms for `move` and `consolidate` read root-locally, T8's re-read against both. Plus two boundary-invariant arms: §3.6's re-resolution refusal after a real `move`, and sorted dedup acquisition over a same-root pair.

**D7's cell must state that both refusals are exercised through the public `move` and `consolidate` entry points**, not only against the predicate — a helper-level test would survive deleting the call from the operation.

§7 carries design §8's relocation limitations verbatim: same-corpus duplicate location unrepaired; `consolidate` two-way only; ordered acquisition in-process only; an operation interrupted after its second data transaction cannot be completed.

- [ ] **Step 7: Update the guard inputs**

Run: `ls docs/designs/*.md | wc -l`

Update `README.md`'s design count, table and date; extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` if the new count has no spelling.

- [ ] **Step 8: Run the guard**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py
```
Expected: PASS. Quote the summary line.

- [ ] **Step 9: Commit**

```bash
git add docs README.md python/tests/test_designs_corpus.py
git commit -m "docs(mutation): bank the world-changing families and freeze cut 16"
```

---

### Task 2: The act-report record-mutation grammar, in memory and in storage

The acquisition lane's integration point: it lands first among the code tasks and touches nothing else.

**Files:**
- Modify: `python/src/beliefs/report.py`, `python/src/beliefs/stored.py`
- Test: `python/tests/test_report.py`, `python/tests/test_stored_act_report.py`

**Interfaces:**
- Produces:
  - `report.Moved(source_corpus: str, destination_corpus: str, ref: str)`
  - `report.Consolidated(kept_corpus: str, kept_ref: str, other_corpus: str, other_ref: str, retired_uids: tuple[str, ...], rationale: str)`
  - `report.RecordMutationEntry(subject: str, corpus: str, outcome: Moved | Consolidated)`
  - `report.OPERATION_KINDS` extended with `"consolidate"` and `"move"`
  - `stored.act_report_node` accepting and round-tripping a `record-mutation` entry

- [ ] **Step 1: Write the failing in-memory tests**

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
    assert facet["outcome"] == {
        "type": "moved",
        "source_corpus": "corpus-a",
        "destination_corpus": "corpus-b",
        "ref": "dataset:d1",
    }


def test_record_mutation_entry_refuses_a_locator_outcome():
    # T5's reservation: byte-locator-untested is unspellable here.
    with pytest.raises(OutcomeRefused):
        report.RecordMutationEntry(
            subject="dataset:d1",
            corpus="corpus-a",
            outcome=report.ByteLocatorUntested(reason="preflight-refused"),
        )


def test_consolidated_retires_nothing_when_the_uid_was_shared():
    facet = report._outcome_facet(
        report.Consolidated(
            kept_corpus="corpus-a", kept_ref="source:s1",
            other_corpus="corpus-b", other_ref="source:s1",
            retired_uids=(), rationale="a copied corpus; one uid throughout",
        )
    )
    assert facet["retired_uids"] == []


def test_consolidated_records_the_retired_uid_and_the_judgement():
    facet = report._outcome_facet(
        report.Consolidated(
            kept_corpus="corpus-a", kept_ref="source:s1",
            other_corpus="corpus-b", other_ref="source:s1",
            retired_uids=("u-2",), rationale="corpus-a holds the authored record",
        )
    )
    assert facet["type"] == "consolidated"
    assert facet["retired_uids"] == ["u-2"]
    assert facet["rationale"] == "corpus-a holds the authored record"


def test_the_two_relocation_operation_kinds_are_admitted():
    assert "move" in report.OPERATION_KINDS
    assert "consolidate" in report.OPERATION_KINDS
    assert "delete" not in report.OPERATION_KINDS
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_report.py -k "record_mutation or consolidated or relocation_operation"
```
Expected: FAIL with `AttributeError: module 'beliefs.report' has no attribute 'RecordMutationEntry'`

- [ ] **Step 3: Implement the in-memory grammar**

In `report.py`, beside `RunRefusal`:

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
    retired_uids: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("kept corpus", self.kept_corpus),
            ("kept ref", self.kept_ref),
            ("other corpus", self.other_corpus),
            ("other ref", self.other_ref),
            ("rationale", self.rationale),
        ):
            _require_str(value, f"consolidated {name}")
        _require_strings(self.retired_uids, "consolidated retired uids")
```

Every field is a string or a flat tuple of strings on purpose: `_outcome_facet`
converts only a top-level tuple to a list, so a nested tuple would not encode.
`retired_uids` is empty in the shared-`uid` arm (design §4).

Beside `RunAttemptEntry`:

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

Extend, as literal members of the existing declarations rather than as
assignments after them: `OPERATION_KINDS` to `("acquisition", "audit",
"consolidate", "import", "move", "re-check", "run-attempt")`; the `Outcome` and
`Entry` aliases; `_ALLOWED_OUTCOMES[RecordMutationEntry] = (Moved,
Consolidated)`; `_ENTRY_KINDS[RecordMutationEntry] = "record-mutation"`;
`_OUTCOME_TYPES[Moved] = "moved"` and `_OUTCOME_TYPES[Consolidated] =
"consolidated"`. Add the three new names to `__all__`, sorted.

Extend `_entry_facet`:

```python
    if type(entry) is RecordMutationEntry:
        row["corpus"] = entry.corpus
```

- [ ] **Step 4: Write the failing stored round-trip test**

`stored.py` carries the **closed storage grammar** and currently rejects both the new kind and its extra field. Add to `python/tests/test_stored_act_report.py`, mirroring its existing per-entry cases:

```python
def test_a_record_mutation_report_round_trips():
    report_value = _mint(  # the module's existing minting helper
        operation="move",
        entries=(
            report.RecordMutationEntry(
                subject="dataset:d1",
                corpus="corpus-a",
                outcome=report.Moved(source_corpus="corpus-a", destination_corpus="corpus-b", ref="dataset:d1"),
            ),
        ),
    )
    node = stored.act_report_node(report_value)
    assert stored.act_report(node) == report_value


def test_a_record_mutation_entry_missing_its_corpus_is_malformed():
    node = stored.act_report_node(_mint(operation="move", entries=(_record_mutation_entry(),)))
    del node.facets[stored.ACT_REPORT_FACET]["entries"][0]["corpus"]
    with pytest.raises(MalformedRecord):
        stored.act_report(node)


def test_a_record_mutation_entry_refuses_a_foreign_outcome_type():
    node = stored.act_report_node(_mint(operation="move", entries=(_record_mutation_entry(),)))
    node.facets[stored.ACT_REPORT_FACET]["entries"][0]["outcome"]["type"] = "published-observation"
    with pytest.raises(MalformedRecord):
        stored.act_report(node)
```

Use the module's own facet constant and minting helper names — read the file first and match them.

- [ ] **Step 5: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_stored_act_report.py -k record_mutation
```
Expected: FAIL — `_valid_report_entry` rejects the unknown kind.

- [ ] **Step 6: Extend the stored grammar**

In `stored.py`, add to `_REPORT_ENTRY_OUTCOMES`:

```python
    "record-mutation": {
        "moved": ("source_corpus", "destination_corpus", "ref"),
        "consolidated": (
            "kept_corpus", "kept_ref", "other_corpus", "other_ref", "retired_uids", "rationale",
        ),
    },
```

and admit the extra field in `_valid_report_entry`:

```python
    expected_entry_fields = {
        "kind",
        "subject",
        "outcome",
        *(("instrument_inputs",) if kind == "pure-look" else ()),
        *(("corpus",) if kind == "record-mutation" else ()),
    }
```

Add a `type(entry.get("corpus")) is not str` check for that kind, beside the existing `subject` check, and validate `retired_uids` as a list of strings the way `record-import`'s `refs` is validated.

- [ ] **Step 7: Run the report and stored suites**

```bash
cd python && uv run --frozen pytest tests/test_report.py tests/test_stored_act_report.py tests/test_inertness.py
```
Expected: PASS. `test_inertness.py` is included deliberately: it holds T1's confinement and T4's inertness, and this is the change most likely to disturb them.

- [ ] **Step 8: Commit**

```bash
git add python/src/beliefs/report.py python/src/beliefs/stored.py python/tests/
git commit -m "feat(report): add the record-mutation entry, in memory and in storage"
```

---

### Task 3: The relocation refusal vocabulary

**Files:**
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_relocation.py` (create)

**Interfaces:**
- Produces: `RelocationRefused`, `SameRootRefused`, `AddressDisagreement`, `DuplicateLocation`, `ContractPinDisagreement`, `RelocationKindExcluded`, `RelocationTargetMissing` — all `WriteRefused` subclasses.

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
    RelocationTargetMissing,
    SameRootRefused,
    WriteRefused,
)


def test_every_relocation_refusal_is_a_write_refusal():
    for error in (
        RelocationRefused, SameRootRefused, AddressDisagreement, DuplicateLocation,
        ContractPinDisagreement, RelocationKindExcluded, RelocationTargetMissing,
    ):
        assert issubclass(error, WriteRefused)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py
```
Expected: FAIL with `ImportError: cannot import name 'AddressDisagreement'`

- [ ] **Step 3: Implement the vocabulary**

Add to `errors.py` after `ReviseOutsideAllowlist`:

```python
class RelocationRefused(WriteRefused):
    """A two-root world-changing operation refused before any transaction.

    Every relocation refusal is one of these: the operation decides in
    Science's vocabulary under both locks, before an engine lease exists.
    """


class SameRootRefused(RelocationRefused):
    """Both positions resolved to one corpus root.

    `move` has nowhere to move to, and `consolidate`'s scope is two readable
    corpora — a single corpus holding two live records at one canonical address
    needs a recovery scanner this design does not build.
    """


class AddressDisagreement(RelocationRefused):
    """`consolidate` was given two different canonical addresses.

    That is a coreference question and `consolidate` must not answer it. It is
    also why `consolidate` is unavailable for one `uid` under two addresses —
    W8b's corruption case, refused on this precondition rather than by a
    corruption check.
    """


class DuplicateLocation(RelocationRefused):
    """`move`'s destination already holds a record at that canonical address.

    Repairing that is `consolidate`'s job, not `move`'s — and it is also the
    state a `move` interrupted after its destination create leaves behind.
    """


class ContractPinDisagreement(RelocationRefused):
    """The receiving corpus does not pin what the relocated node needs (D7).

    Raised for a differing `science_contract`, a differing identity for a
    namespace the node's facets use, and for a namespace the receiving corpus
    pins nothing for — agreement requires exactly one identity, so a missing pin
    is a disagreement and not a permission.
    """


class RelocationKindExcluded(RelocationRefused):
    """The record's kind is excluded from every world-changing operation.

    Act-reports (T8), coordination records, and holdings observations.
    """


class RelocationTargetMissing(RelocationRefused):
    """A create-only family's target stopped resolving under the lock.

    The replacement for family-adapters §5.3's monotonicity argument: consolidate
    and move can remove a record another operation resolved, so `retract` and
    `supersede` re-read their target and refuse rather than assume.
    """
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py
```
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
- Produces, all private and all assuming the caller already holds the root's lock:
  - `CorpusWriter._add_locked(node: Node) -> Node`
  - `CorpusWriter._delete_locked(ref: str) -> None`
  - `CorpusWriter._replace_locked(node: Node) -> Node`

None takes an intent digest. Each runs through the ordinary write path, which fulfills nothing; only the report transaction calls `execute_fulfilling`. Handing a digest to a data transaction would register it as the operation's first fulfillment and leave the report as a forbidden second — the state T2's *"attempt a second fulfilling registration on one intent"* arm refuses.

- [ ] **Step 1: Write the failing tests**

Add to `python/tests/test_corpus_write.py`:

```python
def test_add_locked_applies_every_ordinary_create_check(writer):
    """It mirrors `add`, so `_refuse_already_minted` still bites."""
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with writer._operation:
        with pytest.raises(RecordAlreadyMinted):
            writer._add_locked(node)


def test_replace_locked_rewrites_at_the_same_uid_and_id(writer):
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    revised = node.model_copy(update={"title": "A paper, consolidated"})
    with writer._operation:
        result = writer._replace_locked(revised)
    assert (result.uid, result.id) == (node.uid, node.id)
    assert writer.read_view.get(node.id).title == "A paper, consolidated"


def test_replace_locked_refuses_a_node_that_is_not_already_minted(writer):
    absent = stored.source_node("s2", title="Another", identifiers={"doi": "10.1/xyz"})
    with writer._operation:
        with pytest.raises(WriteRefused):
            writer._replace_locked(absent)


def test_delete_locked_removes_the_record_and_checks_no_references(writer):
    target = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    # An inbound reference exists and must NOT prevent removal.
    writer.add(stored.assessment_node(...))  # copy the module's assessment fixture, assessing p1
    with writer._operation:
        writer._delete_locked(target.id)
    with pytest.raises(RefError):
        writer.read_view.get(target.id)
```

Import `RefError` from wherever `nodes` exports it — check `nodes.core.errors` first; `ReadView.get` propagates it for an absent ref, and it is **not** `KeyError`.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_corpus_write.py -k locked
```
Expected: FAIL with `AttributeError: 'CorpusWriter' object has no attribute '_add_locked'`

- [ ] **Step 3: Implement the seams**

`add`'s body is exactly `_refuse_family_kinds(node)`, `_refuse(node)`, `self._corpus.add(node)` inside `with self._operation:`. `_add_locked` is that body without the acquisition — do not hand-roll a subset of `_refuse`, which already centralises already-minted, basis, eligibility, display-facet, validity, governed-stamp, rendering and collision.

```python
    def _add_locked(self, node: Node) -> Node:
        """`add`'s body, with the lock already held by a composing operation.

        A re-entry point, not a relaxation: every ordinary create check runs,
        `_refuse_already_minted` included.
        """
        self._refuse_family_kinds(node)
        self._refuse(node)
        return self._corpus.add(node)

    def _replace_locked(self, node: Node) -> Node:
        """Rewrite an existing `(uid, id)`, with the lock already held.

        `Corpus.add` selects `ReplaceOp` for a pair that already exists and
        takes its `expected_digest` from the pre-plan read of the current file
        — the same mechanism `revise` uses, and the reason no digest is a
        parameter here. A race refuses through family-adapters §5.2's mapping.

        Distinct from `add`, whose `_refuse_already_minted` guard stays intact,
        and from `revise`, whose allowlist is display prose only.
        """
        existing = self._corpus.index.by_uid.get(node.uid)
        if existing is None or existing.id != node.id:
            raise RevisionTargetMissing(f"{node.id}: exact uid and id do not identify a local node")
        self._refuse_family_kinds(node)
        self._refuse_invalid(node)
        self._refuse_governed_stamp(node)
        self._refuse_rendering(node)
        return self._corpus.add(node)

    def _delete_locked(self, ref: str) -> None:
        """Remove one record's file, with the lock already held.

        No referential check: inbound references do not prevent removal, nothing
        enumerates them, and the existence of such records is not a refusal
        condition. Deletion is a storage operation, not an epistemic one.
        """
        node = self._view.get(ref)
        content = node_to_markdown(node).encode("utf-8")
        self._corpus.executor.execute(
            [DeleteOp(path=self._relative_path(node), expected_digest=member_content_digest(content))]
        )
        self._reconstruct()
```

`DeleteOp` takes `(path, expected_digest)` and the digest is the **bare
64-character** `member_content_digest` of the record's rendered bytes — never a
`sha256:`-prefixed identity. Import `DeleteOp` from `nodes.core.write_plan` and
`member_content_digest` from `beliefs.world.rules`; if that import would create a
cycle, move the four-line helper into a shared module and update both callers in
this same commit.

`_replace_locked` deliberately does not call the full `_refuse`, because
`_refuse_already_minted` and `_refuse_collision` would reject the very pair it
targets. It runs every other check individually. If `_refuse` grows a keyword
that skips those two, prefer that.

- [ ] **Step 4: Run to verify they pass**

```bash
cd python && uv run --frozen pytest tests/test_corpus_write.py
```
Expected: PASS, whole file — the existing add, revise, retract and import arms must not move.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/corpus.py python/tests/test_corpus_write.py
git commit -m "feat(corpus): add the lock-held add, replace and delete seams"
```

---

### Task 5: Ordered acquisition and the relocation predicates

**Files:**
- Create: `python/src/beliefs/relocation.py`
- Test: `python/tests/test_relocation.py`

**Interfaces:**
- Produces: `relocation._both_locks(a, b)`, `_refuse_same_root(a, b)`, `_refuse_excluded_kind(node)`, `_refuse_contract_disagreement(node, source, destination)`, `relocation.EXCLUDED_KINDS`.

- [ ] **Step 1: Write the failing tests**

```python
def test_both_locks_acquires_one_distinct_root_once(tmp_path):
    writer = CorpusWriter(tmp_path, Recorder)
    twin = CorpusWriter(tmp_path, Recorder)   # same root, second handle
    with relocation._both_locks(writer, twin):
        pass                                   # must not hang


def test_both_locks_is_order_independent(tmp_path):
    a = CorpusWriter(tmp_path / "a", Recorder)
    b = CorpusWriter(tmp_path / "b", Recorder)
    with relocation._both_locks(a, b):
        pass
    with relocation._both_locks(b, a):
        pass


def test_the_excluded_kinds_are_reports_coordination_records_and_observations():
    assert "act-report" in relocation.EXCLUDED_KINDS
    assert "holdings-observation" in relocation.EXCLUDED_KINDS
    for kind in coordination.COORDINATION_KINDS:
        assert kind in relocation.EXCLUDED_KINDS
```

The third test is the correction that matters: there is **no** `"coordination-revision"` stored kind. The closed set is `coordination.COORDINATION_KINDS` — `project`, `question`, `hypothesis`, `topic`, `theme`, `task`, `decision`, `note` — and it must be reused, never restated.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'beliefs.relocation'`

- [ ] **Step 3: Implement the module's foundation**

```python
"""The two-root world-changing operations: `move` and `consolidate`.

This module **composes** two `CorpusWriter`s and subclasses neither: an
operation over two corpus roots cannot honestly be a method on an object bound
to one. `atoms` §12.2 keys an engine root on a corpus root, so two corpora are
two chains and two operation ports — these operations are never one
transaction, and the design's §3.5 enumerates every durable prefix instead of
pretending otherwise.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path

from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import COORDINATION_KINDS
from beliefs.corpus import CorpusWriter
from beliefs.errors import ContractPinDisagreement, RelocationKindExcluded, SameRootRefused

EXCLUDED_KINDS = ("act-report", "holdings-observation", *COORDINATION_KINDS)


@contextmanager
def _both_locks(first: CorpusWriter, second: CorpusWriter):
    """Both roots' operation locks, each distinct root once, in sorted order.

    Sorting makes two opposing relocations deadlock-free. Deduplicating on the
    resolved path is the rule; the lock's per-thread reentrancy makes an
    accidental second acquisition harmless rather than load-bearing.
    """
    roots = {str(Path(writer.root).resolve()): writer for writer in (first, second)}
    with ExitStack() as stack:
        for key in sorted(roots):
            stack.enter_context(roots[key]._operation)
        yield
```

Then `_refuse_same_root`, `_refuse_excluded_kind` and
`_refuse_contract_disagreement` as the design's §3.0 and §5 state them:
`science_contract` equality first, then, for every namespace the node's facets
use, the receiving corpus must resolve to **exactly one** identity equal to the
source's — a **missing** pin refuses, because agreement requires one identity and
"not different" is too weak.

- [ ] **Step 4: Add the accessors this needs, if absent**

`CorpusWriter.root`, `CorpusWriter.corpus_id`, `CorpusWriter.manifest_pins()`, and a `stored` helper returning a node's used facet namespaces. Check each before writing it; add the missing ones as thin accessors with their own unit tests in this same commit.

- [ ] **Step 5: Run to verify they pass**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/relocation.py python/src/beliefs/corpus.py python/src/beliefs/stored.py python/tests/test_relocation.py
git commit -m "feat(relocation): add ordered acquisition and the relocation predicates"
```

---

### Task 6: The boundary-owned relocation report mint

`_mint_report` is private and `test_inertness.py::test_t1_the_constructor_is_reachable_only_from_the_boundary` asserts its callers are exactly `["boundary.py", "report.py"]`. Calling it from `corpus.py` or `relocation.py` breaks T1. The legal route is the one `import_bundle` already uses: a mint helper in `boundary.py`, called through a thin `CorpusWriter` method.

**Files:**
- Modify: `python/src/beliefs/boundary.py`, `python/src/beliefs/corpus.py`
- Test: `python/tests/test_inertness.py`, `python/tests/test_boundary.py`

**Interfaces:**
- Produces:
  - `boundary._mint_relocation_report(intent, *, subject, corpus, observer, instrument, opened_at, closed_at, outcome) -> ActReport`
  - `CorpusWriter._append_operation_intent(kind: str, token: str, actor: str) -> str`
  - `CorpusWriter._publish_operation_report(...) -> ActReport`

- [ ] **Step 1: Write the failing tests**

```python
def test_t1_still_confines_the_constructor_after_the_relocation_mint():
    src = Path(beliefs.__file__).parent
    callers = [path.name for path in src.rglob("*.py") if "_mint_report" in path.read_text(encoding="utf-8")]
    assert sorted(callers) == ["boundary.py", "report.py"]


def test_the_relocation_mint_refuses_a_foreign_intent_kind():
    with pytest.raises(MalformedRecord):
        boundary._mint_relocation_report(
            OperationIntent("import", "t" * 32, "actor"),
            subject="dataset:d1", corpus="corpus-a", observer="o", instrument="i",
            opened_at="2026-09-03T10:00:00Z", closed_at="2026-09-03T10:00:01Z",
            outcome=report.Moved(source_corpus="corpus-a", destination_corpus="corpus-b", ref="dataset:d1"),
        )
```

The second mirrors `_mint_import_report`'s own `intent.kind != "import"` guard.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_inertness.py tests/test_boundary.py -k relocation
```
Expected: FAIL with `AttributeError: module 'beliefs.boundary' has no attribute '_mint_relocation_report'`

- [ ] **Step 3: Implement the mint and the two writer helpers**

In `boundary.py`, beside `_mint_import_report`:

```python
def _mint_relocation_report(
    intent: OperationIntent,
    *,
    subject: str,
    corpus: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    outcome: Moved | Consolidated,
) -> ActReport:
    if type(intent) is not OperationIntent or intent.kind not in ("move", "consolidate"):
        raise MalformedRecord("a relocation report requires a move or consolidate operation intent")
    return _mint_report(
        operation=intent.kind,
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=(RecordMutationEntry(subject=subject, corpus=corpus, outcome=outcome),),
    )
```

In `corpus.py`, factor `import_bundle`'s existing intent-append and
fulfilling-publish steps into two reusable methods so there is one such path and
not two — `_append_operation_intent(kind, token, actor)` returning the validated
64-hex digest, and `_publish_operation_report(...)` which builds the node with
`stored.act_report_node`, executes it with `execute_fulfilling`, and
`_reconstruct()`s. `import_bundle` must then call them and keep every existing
test green.

`_publish_operation_report` is the **only** caller of `execute_fulfilling` on
this path; the Task 4 seams use ordinary execution.

- [ ] **Step 4: Run to verify they pass**

```bash
cd python && uv run --frozen pytest tests/test_inertness.py tests/test_boundary.py tests/test_corpus_write.py
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/boundary.py python/src/beliefs/corpus.py python/tests/
git commit -m "feat(boundary): mint relocation act-reports from the boundary"
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
    with pytest.raises(RefError):
        source_writer.read_view.get(node.id)


def test_move_refuses_an_occupied_destination(source_writer, destination_writer):
    node = source_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    destination_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with pytest.raises(DuplicateLocation):
        relocation.move(source_writer, destination_writer, node.id, actor="a", observer="o",
                        instrument="i", opened_at="2026-09-03T10:00:00Z", closed_at="2026-09-03T10:00:01Z")


def test_move_refuses_a_same_root_pair(writer):
    node = writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    with pytest.raises(SameRootRefused):
        relocation.move(writer, writer, node.id, actor="a", observer="o", instrument="i",
                        opened_at="2026-09-03T10:00:00Z", closed_at="2026-09-03T10:00:01Z")


def test_move_mints_one_report_per_root_under_one_token(source_writer, destination_writer):
    node = source_writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"}))
    _, destination_report, source_report = relocation.move(...)
    assert destination_report.event_token == source_report.event_token   # one operation
    assert destination_report.operation == source_report.operation == "move"
    assert destination_report.opened_at == source_report.opened_at
    assert destination_report.identity() != source_report.identity()     # different entries
```

- [ ] **Step 2: Write the failing row tests**

Create `python/tests/test_relocation_rows.py` covering the frozen selection. Every D7 arm goes through the **public** `relocation.move`, not the predicate — a helper-level test would survive deleting the call from the operation:

```python
def test_w5_a_move_changes_only_location(...):
    """uid, canonical address, deprecated_ids, inbound references and the
    belief digest all unchanged."""

def test_w5_a_producers_map_member_moves_without_moving_the_digest(...):
    """Move a dataset that appears in the producers map; the digest is
    unchanged though the address map and BOTH corpus-state identities moved,
    and re-deriving mints a new receipt naming the same snapshot."""

def test_g3_location_is_not_a_closure_member(...):
    """G3's negative: the member is the producer snapshot, not the index."""

def test_d7_a_permitted_move_preserves_w5(...):
def test_d7_move_refuses_a_domain_facet_across_identities(...):
    with pytest.raises(ContractPinDisagreement):
        relocation.move(source_writer, other_biology_writer, node.id, ...)
def test_d7_move_refuses_a_base_contract_for_a_facetless_node(...):
def test_d7_move_refuses_a_missing_pin(...):

def test_c3_an_in_coverage_move_leaves_the_digest_and_moves_the_receipt(...):
def test_r23_location_is_not_evidence(...):
def test_r23_the_receipt_is_not_a_belief_input(...):
def test_t2_a_move_is_one_intent_and_one_report_in_each_root(...):
def test_t8_move_refuses_an_act_report_subject(...):
```

Build fixtures from `fixtures_cut6.PINS` and `closure_fixtures.py`; the producers-map and receipt arms need a published epoch, so follow `test_epoch.py`'s construction.

- [ ] **Step 3: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py tests/test_relocation_rows.py
```
Expected: FAIL with `AttributeError: module 'beliefs.relocation' has no attribute 'move'`

- [ ] **Step 4: Implement `move`**

Destination-first, with the §3.5 order: both locks, every precondition, destination intent, source intent, destination create, source delete, destination report, source report. One `secrets.token_hex(16)` token shared by both roots; `opened_at`/`closed_at` passed identically to both. Preconditions in the design's order: distinct roots, `ref` resolves in the source, kind not excluded, contract agreement, destination unoccupied.

- [ ] **Step 5: Run to verify they pass, then the full suite**

```bash
cd python && uv run --frozen pytest tests/test_relocation.py tests/test_relocation_rows.py
cd python && uv run --frozen pytest
```
Expected: PASS. Quote the summary line.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/relocation.py python/tests/
git commit -m "feat(relocation): add the destination-first cross-corpus move"
```

---

### Task 8: The replacement concurrency ruling

This follows `move` deliberately. The frozen arm is *a target **moved away***, and only a real `move` produces that state — deleting the target directly would test a state the current code already refuses, and would not demonstrate under-lock re-resolution at all.

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`retract`, `supersede`, the `CorpusWriter` docstring)
- Test: `python/tests/test_relocation_rows.py`

**Interfaces:**
- Consumes: `relocation.move`.
- Produces: `retract` and `supersede` raise `RelocationTargetMissing` for a target that stopped resolving.

- [ ] **Step 1: Write the failing tests**

```python
def test_retract_refuses_a_target_moved_away(source_writer, destination_writer):
    """§3.6 clause 1, through the operation that creates the state."""
    target = source_writer.add(stored.assessment_node(...))
    record = stored.retraction_node("r1", target=stored.NodeTarget(target.id, target.id, ...), ...)
    relocation.move(source_writer, destination_writer, target.id, actor="a", observer="o",
                    instrument="i", opened_at="...", closed_at="...")
    with pytest.raises(RelocationTargetMissing):
        source_writer.retract(record)


def test_supersede_refuses_a_predecessor_moved_away(source_writer, destination_writer):
    predecessor = source_writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    successor = stored.proposition_node("p2", title="p2", claim={"operator": "inhibits"})
    relocation.move(source_writer, destination_writer, predecessor.id, actor="a", observer="o",
                    instrument="i", opened_at="...", closed_at="...")
    with pytest.raises(RelocationTargetMissing):
        source_writer.supersede(successor, of=predecessor.id)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_relocation_rows.py -k moved_away
```
Expected: FAIL — a different error type, or none.

- [ ] **Step 3: Implement re-resolution and rewrite the docstring**

In both `retract` and `supersede`, inside the existing `with self._operation:` and immediately before plan construction, re-read the target and refuse:

```python
        try:
            self._view.get(target_ref)
        except RefError as caught:
            raise RelocationTargetMissing(
                f"{target_ref}: the target no longer resolves in this corpus; a concurrent move "
                "or deletion removed it (world-changing families §3.6)"
            ) from caught
```

`ReadView.get` propagates `nodes`' `RefError`, not `KeyError`. Use each method's own target — the retraction's resolved target, and `of` for supersede.

Replace the `CorpusWriter` docstring's closing paragraph:

```python
    **The world-changing families exist, so no target is monotone.** Consolidate
    and move can remove a record another operation resolved, so `retract` and
    `supersede` re-resolve their target under this lock immediately before plan
    construction and refuse if it has gone (world-changing families §3.6). The
    collision predicates remain what they were: two planners can each pass
    `assert_addable` for one uid under different ids, so the single-planner
    restriction stands — in-process this lock, cross-process a stated deployment
    obligation whose violation is detected loudly.
```

- [ ] **Step 4: Run to verify they pass, then the full suite**

```bash
cd python && uv run --frozen pytest tests/test_relocation_rows.py
cd python && uv run --frozen pytest
```
Expected: PASS. Quote the summary line.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/corpus.py python/tests/test_relocation_rows.py
git commit -m "fix(corpus): re-resolve create-only targets under the lock"
```

---

### Task 9: `consolidate` and the tagged-basis reconciliation

**Files:**
- Modify: `python/src/beliefs/relocation.py`, `python/src/beliefs/stored.py`
- Test: `python/tests/test_relocation.py`, `python/tests/test_relocation_rows.py`, `python/tests/test_stored.py`

**Interfaces:**
- Produces:
  - `relocation.consolidate(keep, other, *, rationale, actor, observer, instrument, opened_at, closed_at) -> tuple[Node, ActReport, ActReport]`, where `keep` and `other` are each `tuple[CorpusWriter, str]`; the kept root's report is first
  - `stored.union_lineage_bases(survivor: Node, loser: Node) -> dict[str, dict]`

- [ ] **Step 1: Write the failing reconciliation tests**

Add to `python/tests/test_stored.py`:

```python
def test_union_lineage_bases_keeps_a_single_tag_for_equal_bases(): ...
def test_union_lineage_bases_makes_a_sorted_conflict_for_differing_routes(): ...
def test_union_lineage_bases_unions_two_conflicts(): ...
def test_a_conflict_with_fewer_than_two_routes_is_unconstructible(): ...
```

- [ ] **Step 2: Write the failing operation and row tests**

```python
def test_consolidate_unions_relations_and_preserves_both_bases(...):
    """W16: one address survives, outgoing relations unioned, divergent lineage
    bases both preserved, no redirect, no inbound rewrite, no deprecated_ids
    entry, no coreference-attestation, no balance moved."""

def test_consolidate_preserves_a_shared_uid_and_retires_nothing(...):
    """And the report's `retired_uids` is empty — the arm a mandatory single
    retired uid could not state truthfully."""

def test_consolidate_selects_one_of_two_distinct_uids_and_mints_no_third(...):
def test_consolidate_refuses_two_different_addresses(...):
def test_consolidate_is_not_offered_for_one_uid_under_two_addresses(...):
    """W8b's first arm: assert the error is AddressDisagreement — it refuses on
    the one-address precondition, not on a corruption check."""
def test_consolidate_refuses_a_same_root_pair(...):
def test_consolidate_refuses_an_excluded_kind_on_either_input(...):
    """T8: two replicated act-reports at one address must not be consolidable."""

def test_d7_consolidate_refuses_a_domain_facet_across_identities(...):
def test_d7_consolidate_refuses_a_base_contract_for_a_facetless_node(...):
def test_d7_consolidate_refuses_a_missing_pin(...):
    """The frozen D7 cell requires these through public `consolidate`."""

def test_m3_consolidating_equal_basis_retraction_replicas_leaves_the_counter_retraction(...):
    """Consolidate two equal-basis replicas of one retraction held in two
    corpora while a counter-retraction R targets it; it succeeds, the
    retraction's content identity is unchanged, and R is neither rewritten nor
    re-minted."""

def test_the_survivor_is_readable_after_consolidation(...):
    """The restamp arm: a covered-facet union with a stale semantic-identity
    stamp makes the survivor unreadable — `ReadView.get` refuses
    `semantic-hash-stale`. Read the survivor back through the view."""

def test_consolidate_is_idempotent_over_an_already_unioned_survivor(...):
def test_t2_a_consolidate_is_one_intent_and_one_report_in_each_root(...):
```

- [ ] **Step 3: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_stored.py tests/test_relocation.py tests/test_relocation_rows.py -k "consolidate or union_lineage or m3"
```
Expected: FAIL with `AttributeError: module 'beliefs.stored' has no attribute 'union_lineage_bases'`

- [ ] **Step 4: Implement the reconciliation**

Three interface facts govern this and were each verified: `Relation` is **unhashable**, so no `set()`; `Node.relations` is `list[Relation]` and `deprecated_ids` is `list[str]`, so updates must stay lists or lossless rendering fails; and the lineage basis is a **covered** facet, so a union leaves the survivor's semantic-identity stamp stale and `ReadView.get` will refuse it as `semantic-hash-stale` on the very next read.

```python
def _relation_key(relation: Relation) -> tuple[str, str, str]:
    """A canonical, hashable key for deduplication. `Relation` is unhashable,
    so equality is taken over its three identifying fields."""
    return (relation.source, relation.predicate, relation.target)


def _reconcile(survivor: Node, loser: Node) -> Node:
    """`keep`'s whole authored record, carrying `keep`'s uid, with the unions.

    Order-independent and idempotent: reconciling an already-unioned survivor
    with the same loser returns an equal node, which is what makes a re-run the
    recovery for the design's §3.5 prefixes 1–4.
    """
    merged: dict[tuple[str, str, str], Relation] = {}
    for relation in [*survivor.relations, *loser.relations]:
        merged.setdefault(_relation_key(relation), relation)
    relations = [merged[key] for key in sorted(merged)]
    deprecated = sorted({*survivor.deprecated_ids, *loser.deprecated_ids})
    facets = stored.union_lineage_bases(survivor, loser)
    unstamped = survivor.model_copy(
        update={"relations": relations, "deprecated_ids": deprecated, "facets": facets}
    )
    return stored.stamp_semantic_identity(unstamped)
```

The restamp is not optional: without it the survivor carries a stamp for its
pre-union facets and becomes unreadable through the ordinary view.

Then `consolidate` itself, in the §3.5 order: both locks; preconditions (distinct
roots, both resolve, neither excluded, one canonical address, contract
agreement); `keep` intent; other intent; `_replace_locked(merged)`;
`_delete_locked(other_ref)`; `keep` report; other report. `retired_uids` is `()`
when the inputs shared a `uid` and `(loser.uid,)` when they differed.

- [ ] **Step 5: Run to verify they pass, then the full suite**

```bash
cd python && uv run --frozen pytest tests/test_stored.py tests/test_relocation.py tests/test_relocation_rows.py
cd python && uv run --frozen pytest
```
Expected: PASS. Quote the summary line.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/relocation.py python/src/beliefs/stored.py python/tests/
git commit -m "feat(relocation): add consolidate, the duplicate-location exit"
```

---

### Task 10: The crash prefixes and the recovery table

**Files:**
- Test: `python/tests/test_relocation_recovery.py` (create)

**Interfaces:**
- Consumes: `move`, `consolidate`, the seams.
- Produces: nothing importable — this task is evidence for design §3.5.

- [ ] **Step 1: Write the failing tests**

Drive each prefix by monkeypatching a seam to run and then raise a module-local `_Stop`, so the durable step genuinely lands before the operation aborts. Do **not** add fault injection to `relocation.py`; production code must not carry a test seam.

```python
@pytest.mark.parametrize(
    "stop_after",
    ["destination-intent", "source-intent", "destination-create", "source-delete", "destination-report"],
)
def test_move_prefixes_are_exactly_the_enumerated_states(stop_after, ...):
    """§3.5's move table, row by row."""

def test_a_move_interrupted_at_the_destination_create_is_a_duplicate_location(...):
    """And re-running `move` now refuses at precondition 5 — correct, because
    the state is no longer a move's pre-state."""
    with pytest.raises(DuplicateLocation):
        relocation.move(source_writer, destination_writer, ref, ...)

def test_that_duplicate_location_is_repaired_by_consolidate(...):
    """The recovery table's `move` step-4 row."""

def test_a_move_interrupted_after_the_source_delete_cannot_be_completed(...):
    """Data final; re-running refuses because the source no longer holds the
    record; the intents stay unmatched and read `unfinished` under T3."""

def test_consolidate_prefixes_two_to_four_are_repaired_by_re_running(...):
def test_consolidate_after_the_other_delete_cannot_be_completed(...):
    """Re-running refuses: `other` no longer resolves."""

def test_a_move_never_loses_the_record_at_any_prefix(...):
    """The argument for the two operations sharing a cut: at every prefix the
    record is readable in at least one corpus."""
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_relocation_recovery.py
```
Expected: FAIL — the module's helpers do not exist yet.

- [ ] **Step 3: Implement the fault-injection harness in the test module**

- [ ] **Step 4: Run to verify they pass**

```bash
cd python && uv run --frozen pytest tests/test_relocation_recovery.py
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/tests/test_relocation_recovery.py
git commit -m "test(relocation): pin every durable prefix and its recovery"
```

---

### Task 11: The durable arms, N2 declarations and the acceptance runner

**Files:**
- Create: `python/tests/acceptance/test_relocation_acceptance.py`, `python/tests/n2_arms_cut16.py`, `python/tests/acceptance/test_n2_cut16.py`, `python/tools/cut16_acceptance.py`

**Interfaces:**
- Consumes: every selected arm from Tasks 7–10.
- Produces: the discharge evidence Task 12 records.

- [ ] **Step 1: Write the durable acceptance module**

`python/tests/acceptance/test_relocation_acceptance.py` re-runs every selected arm against the **certified engine** rather than `DefaultExecutor`. The portable tests prove behaviour; only this module can support a discharge claim. Follow the construction in the acceptance module cut 15's runner names, using `init_corpus_root`/`open_corpus` against the runner's work directory. A selected durable arm **errors rather than skips** when the certified tuple is unavailable.

- [ ] **Step 2: Enumerate the N2 declarations**

`python/tests/n2_arms_cut16.py`, following `n2_arms_cut7.py`'s shape: one entry per selected arm from the frozen §3, each naming the test that runs it. The count must equal the frozen §4 accounting exactly — a mismatch is a freeze violation, recorded as a dated deviation, not silently reconciled.

- [ ] **Step 3: Write the runner**

`python/tools/cut16_acceptance.py`, modelled on `cut15_acceptance.py`:

```python
PREFIX_RUNNERS = ("cut15_acceptance.py",)
PHASE_MODULES = ("test_relocation_acceptance.py", "test_n2_cut16.py")
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut16-acceptance"
```

Cut 15 is the highest-numbered discharged cut, so it is the prefix (roadmap rule 5). The work directory sits beside the checkout because `/tmp`, `/dev/shm` and the scratch volume all fail the durability allowlist.

- [ ] **Step 4: Run the portable suite and the runner**

```bash
cd python && uv run --frozen pytest
cd python && uv run --frozen python tools/cut16_acceptance.py
```
Expected: PASS, then exit 0. If the runner exits with the probe's refusal code, the kernel has outrun the `atoms` A8 allowlist — a recertification matter (`atoms-recertify.timer`), not a regression here.

- [ ] **Step 5: Commit**

```bash
git add python/tests/ python/tools/cut16_acceptance.py
git commit -m "test(cut16): add the durable arms, N2 declarations and the acceptance runner"
```

---

### Task 12: Gates, discharge, re-rank, and merge

**Files:**
- Create: `docs/plans/2026-09-03-conformance-cut-16-results.md`, `docs/plans/2026-09-03-relocation-rulings-ledger.md`
- Modify: the adoption ledger's `Current state`, the roadmap

- [ ] **Step 1: Run every gate**

```bash
cd python && uv run --frozen pytest
cd python && uv run --frozen ruff check .
cd python && uv run --frozen pyright
cd ts && npm ci && npm test && npm run typecheck && npm run check
```
Expected: all pass. Quote pytest's summary line. Fix anything that fails before continuing — a discharge over a red gate is not a discharge.

- [ ] **Step 2: Write the results record**

Follow `docs/plans/2026-09-01-conformance-cut-15-results.md`: §1 what ran and where (the exact commit, the certified tuple, the runner invocation), §2 the selected rows with each one's full/part reading, §3 corrections and deviations, §4 what this run does not claim.

§4 must state plainly: no deletion arm ran; W16 is part, its remaining arm belonging to the deletion cut; T2 and R23 stay part; nothing here closes L13; removal classification is not exercised; the M1 resolver and the claim restore seam do not exist yet, so M11 and M13 are untouched by this cut.

- [ ] **Step 3: Commit the rulings ledger**

Every ruling made during implementation goes in `docs/plans/2026-09-03-relocation-rulings-ledger.md`, committed to that tracked path **before the worktree is removed**. Slice 2 lost R1–R15 by leaving its ledger in a worktree.

- [ ] **Step 4: Re-rank**

Add the cut's bullet to the ledger's `Current state`. Rewrite the roadmap whole: `Ranked at` becomes cut 16, `consolidate-family` keeps its remaining rows, and Appendices A and B are regenerated.

```bash
cd python && uv run --frozen python tools/roadmap_status.py
cd python && uv run --frozen pytest tests/test_designs_corpus.py
```
Expected: PASS — `test_the_roadmap_and_ledger_name_the_same_boundaries` holds `Ranked at` to the newest results record.

- [ ] **Step 5: Close the task record and check**

```bash
tasks note beliefs-676a2c "Relocation cut discharged; deletion cut remains."
tasks check
```
Expected: zero errors. Report every warning; registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental.

- [ ] **Step 6: Commit and merge from the repository root**

`main` is checked out at the root, so `git checkout main` **inside this worktree will fail**. Commit here, then merge there.

```bash
git add docs
git commit -m "docs(mutation): discharge conformance cut 16 and re-rank the roadmap"

cd /mnt/ssd/Dropbox/beliefs        # the root worktree, where main is checked out
git merge --no-ff design/consolidate-family
```

- [ ] **Step 7: Draft the deletion cut's plan**

Its arm inventory depends on what this results record discharged — W16's remainder and T2's reading in particular. Re-read design §6.2 and §6.3 against the record, then write `docs/superpowers/plans/<date>-deletion-cut.md`.

---

## Self-Review

**Spec coverage.** §1 → Task 1. §2.1 → Tasks 1, 8. §2.2 → **Task 1 Step 5** (the C1 amendment lands in this banking change; only the *re-read* is the deletion cut's). §2.3's relocation half → Tasks 7, 9. §2.4 → Tasks 1, 2. §2.5 → the deletion cut, correctly absent. §3.0 → Task 5. §3.1 → the deletion cut. §3.2 → Task 7. §3.3 → Task 9. §3.4 → Tasks 4, 6. §3.5 → Task 10. §3.6 → Task 8. §4 → Tasks 2, 6. §5 → Task 5, exercised publicly in Tasks 7 and 9. §6.1 → Tasks 7, 9. §6.2, §6.3 → the deletion cut. §7 → the deletion cut. §8's relocation limitations → Task 1 Step 6. §9 → Global Constraints. §10 → Task 1. §11 → rationale, no task.

**Accepted gap.** R23's consolidate clauses include *the conflict survives deleting either producing run*, which cannot run without `delete`. Task 9 covers the constructible half; the frozen cut marks R23 part and names the deletion cut for the rest.

**Type consistency.** `_add_locked(node)`, `_delete_locked(ref)`, `_replace_locked(node)` — no intent digest, no expected-digest parameter, consistent across Tasks 4, 7, 9. `Moved`/`Consolidated`/`RecordMutationEntry` field names match between Task 2's implementation, Task 2's stored grammar, Task 6's mint, and Tasks 7 and 9's construction; `retired_uids` is a tuple everywhere. `_both_locks`, `_refuse_same_root`, `_refuse_excluded_kind`, `_refuse_contract_disagreement` are defined in Task 5 and used under those names in Tasks 7 and 9.

**Design corrections this review forced**, both applied to the spec before this plan was rewritten: §3.4's `_replace_locked` no longer takes an `expected_digest` — the substrate reads it pre-plan, as `revise` demonstrates — and §4's `retired_uid` became `retired_uids`, a sequence that is empty in the shared-`uid` arm, which a mandatory single field could not state truthfully.

**Accessors to verify before use, not assume:** `CorpusWriter.root`, `.corpus_id`, `.manifest_pins()`, `_relative_path`, a `stored` facet-namespace helper, and `member_content_digest`'s import path. Tasks 4 and 5 each say to check and to add the missing ones with unit tests in the same commit.
