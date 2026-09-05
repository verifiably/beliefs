# Writer Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An attended `beliefs` writer session with a fixed actor, an append-then-fsync ledger and claim protocol, an invocation-bound scoped writer whose permit is exactly its requirement, every session write as one `corpus-write` intent fulfilled by its registration, settlement of an unresolved root before every prepare, and reconciliation of ledgers against chains — conformance cut 19, rows J1–J11.

**Architecture:** `report.py` and `intents/reduce.py` gain the `corpus-write` operation kind and the rule that a committed fulfilling registration qualifies it. `runrecord.py`'s port protocol gains `preflight` and a registration-digest return from `execute_fulfilling`; `root.py`'s durable factory carries `recover(root)`. `corpus.py` gains one `_locked()` context manager that settles an `unresolved` root before any prepare, an `OperationWrites` facade over seven prepare helpers, and one commit seam (`_commit`) that is the inventory's 37th primitive caller. A new `beliefs/session/` package holds the ledger (`ledger.py`), the session and scoped writer (`writer.py`), the pure reconciliation (`reconcile.py`), and the two compositions `open_attended_session` and `reconcile_sessions` (`__init__.py`). Durable acceptance, N2 arms and a runner discharge cut 19 on the certified volume.

**Tech Stack:** Python 3.11+ under `uv` (`python/`), pytest, ruff, pyright basic; the `atoms` engine on a certified volume for acceptance; git for freeze pins.

**Spec:** `docs/designs/2026-09-05-writer-session-design.md` (reviewed six times; §7 the J table, §9 the cut) and `docs/designs/2026-09-05-conformance-cut-19.md` (frozen at `5cc2153`). Task 1 adds the design's §13, the implementation amendment, before any code.

## Global Constraints

- Work in the worktree `.worktrees/writer-session` on branch `feat/writer-session`. Every command below runs from `python/` inside that worktree unless it says otherwise.
- Gates before every commit: `uv run --frozen pytest -q -p no:cacheprovider`, `uv run --frozen ruff check .`, `uv run --frozen pyright` — all clean. The pytest summary line is the count claim; never pipe the run through `tail` without `set -o pipefail`.
- **Frozen text stays frozen.** Never edit §7 or §9 of the design, nor §2–§7 of the cut record. Amendments go in the design's §13 (Task 1) and §10.
- **The permit check is one bare statement** (write-permits design §5): in `OperationWrites._commit` the first statement with any effect is `self._writer.authority.require("corpus-write", (kind,))` at the top level of the body. No prepare, preflight, primitive call or byte mutation may precede it.
- **No `actor` parameter** on any public or private definition in `session/`, on `OperationWrites`, or on any new definition in `corpus.py`. The actor is `Authority.actor`, always.
- **`session/` imports no engine name.** `session/ledger.py`, `writer.py` and `reconcile.py` import nothing from `atoms` and nothing from `beliefs.root`; only `session/__init__.py` (the composition) imports `beliefs.root`. `root.py` never imports `beliefs.session`.
- **Pinned sabotage blocks must keep matching exactly once.** After every task that edits `src/beliefs`, run the staleness probe and compare with the baseline Task 1 records:

```bash
uv run --frozen python - <<'PY'
import importlib, sys
from pathlib import Path
sys.path[:0] = ["tests", "tests/acceptance"]
import beliefs
package = Path(beliefs.__file__).resolve().parent
stale = []
for cut in (3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18):
    arms = getattr(importlib.import_module(f"n2_arms_cut{cut}"), f"CUT{cut}_ARMS")
    for arm in arms:
        n = (package / arm.sabotage.module).read_text(encoding="utf-8").count(arm.sabotage.before)
        if n != 1:
            stale.append((cut, arm.row, arm.sabotage.module, n))
print("stale:", stale)
PY
```

  Any arm that goes stale in a task must be listed in that task's commit message and in the design's §13 with the reason; a stale arm that no task explains is a defect.
- Test helper for a full authority: `tests/authority.py` exports `FULL`, `ACTOR`, `narrowed(...)`, `lacking(...)`. No test builds a `WritePermit` literal except through it or `RequiredCapabilities`.
- **Durable tests** live under `tests/acceptance/` and run on the certified volume beside the checkout (`SCIENCE_CUT4_ROOT` or the repository-relative default); `/tmp` and the scratch volume fail the durability allowlist. A `CapabilityUnavailable` block is a fail-closed result: recertify or report the tuple, never skip.
- Task records: every task names its own child id in its first and last steps — `tasks start <id>` before its first edit and `tasks done <id> "<what landed>"` staged into its final commit; `tasks check` before every commit. The children form a dependency chain (Task N depends on Task N−1). Never edit `tasks/*.md` by hand.
- Commit messages are conventional commits with no AI attribution trailer.

---

## File map

| file | responsibility |
|---|---|
| `python/src/beliefs/errors.py` | `PlanRefused(WriteRefused)`, `OperationPortMissing(WriteRefused)`, `SessionRefused`, `SessionClosed`, `SessionProtocolError`, `SessionLedgerFailed`, `LedgerMalformed` |
| `python/src/beliefs/report.py` | `OPERATION_KINDS` gains `corpus-write`; `completion` reads a `corpus-write` intent `CLOSED` on a token-matching registration |
| `python/src/beliefs/intents/reduce.py` | `_qualify_one` matches a `corpus-write` intent on a committed fulfilling registration, records or none |
| `python/src/beliefs/runrecord.py` | `OperationPort.preflight(plan)`; `execute_fulfilling(plan, fulfills) -> str` |
| `python/src/beliefs/root.py` | `plan_preflight`, `DurableOperationPort.preflight`, the registration readback, `_DurableExecutorFactory.recover`, `durable_operation_port`, `log_seam` |
| `python/src/beliefs/corpus.py` | `_RootState.unresolved`/`recover`, `_locked`, `_settle`, `_submitting`, the seven prepare helpers, `OperationWrites`, `_commit`, `OperationCommit` |
| `python/src/beliefs/relocation.py` | the two-root acts enter `writer._locked()` |
| `python/src/beliefs/session/ledger.py` (new) | line encoding, `LedgerWriter`, `LedgerReader`, `ActLine`, `InvocationRecord`, `LedgerEvidence` |
| `python/src/beliefs/session/writer.py` (new) | `WriterSession`, `ScopedWriter`, the `Claim` union, `KernelRefusalValue` |
| `python/src/beliefs/session/reconcile.py` (new) | `reconcile(ledgers, chains) -> tuple[Finding, ...]` |
| `python/src/beliefs/session/__init__.py` (new) | `open_attended_session`, `reconcile_sessions`, the contract's re-exports |
| `python/tests/test_permit_boundary.py` | the inventory's 37th row |
| `python/tests/test_operation_writes.py`, `test_session_ledger.py`, `test_session_writer.py`, `test_session_reconcile.py` (new) | the portable arms |
| `python/tests/acceptance/test_session_acceptance.py` (new) | the durable arms |
| `python/tests/acceptance/n2_arms_cut19.py`, `test_n2_cut19.py`, `python/tools/cut19_acceptance.py` (new) | N2 and the runner |

---

### Task 1: The implementation amendment (§13), the science change requests, and the task records

**Files:**
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (append §13 after §12)
- Modify (science repo): `/mnt/ssd/Dropbox/science/docs/plans/2026-08-31-command-framework.md` (Task 12 *Consumes* block), `/mnt/ssd/Dropbox/science/docs/specs/2026-08-31-command-framework-design.md` (§4.2, §5.1)
- Tasks: children of `beliefs-afbbff`

**Interfaces:**
- Produces: the amendment every later task cites; the science-side contract text both repositories code against; one task child per `### Task N:` heading of this plan.

- [ ] **Step 1: Record the staleness baseline**

Run the probe from Global Constraints on the untouched branch and paste its `stale:` line into §13 item 5 below (it is expected to be `stale: []`; if it is not, the baseline is whatever it prints, verbatim).

- [ ] **Step 2: Append §13 to the design**

Append after §12, verbatim except the baseline line:

```markdown
## 13. Implementation amendment — 2026-09-05

Rulings made at plan time, before any code, that the frozen text does not
decide. None changes a `J` row or the cut's §2–§7.

1. **Where the compositions live.** `open_attended_session` and
   `reconcile_sessions` are defined in `beliefs/session/__init__.py`, which
   imports `beliefs.root`; `root.py` does not import `beliefs.session`. §6
   names `root.reconcile_sessions`; the exported name is
   `beliefs.session.reconcile_sessions`, and the behavior is §6's exactly.
   `root.py` gains three small public seams the composition needs:
   `durable_operation_port(root, authority)` (the port `open_corpus`
   already builds), `log_seam()` (the production `LogSeam`), and
   `plan_preflight(plan)` (§4.3 step 3's two checks as one function).
2. **`WriterSession` is constructible from parts.** Its constructor takes
   the session identity, actor, world id, corpus root, corpus id, operations
   root, an open `LedgerWriter`, a `writer_factory(authority) ->
   CorpusWriter`, and the reconciliation findings. `open_attended_session`
   supplies the durable parts; the portable suite supplies an in-memory
   writer factory over a synthetic-digest port. No test constructs a session
   by any other route.
3. **Recovery is `read_chain`, gated by the lifecycle state.** The durable
   factory's `recover(root)` first reads the root's lifecycle state; when it
   is not `writable` it returns without reading the chain, leaving the
   engine's own registration refusal to the write itself — so
   `test_a_write_against_an_unregistered_root_refuses`' `(index, applied) ==
   (None, 0)` and its `__cause__` are unchanged. When it is writable,
   `read_chain` resolves recovery under the project lock; every engine
   exception maps to `ExecutionError(index=None, applied=None)`.
4. **The pending-registration fixture is a halting backend.** J2's
   continuation arm leaves a real staged, unsettled transaction by wrapping
   the engine backend in a delegate that raises `OSError` at its first
   publish-phase call (`exchange`, `transfer_noclobber` or `link_anchor`)
   after at least one `write`; the port under test is constructed over that
   backend, and the factory's `recover` — over the real backend — is what
   settles it. The arm asserts the registration is pending under detached
   inspection before recovery and gone after.
5. **Staleness baseline at plan time:** `stale: []`.
6. **Finding order.** §6's "corpus id, then chain position, then code" is
   implemented as an internal sort key `(corpus_id, position, code, ref)`
   that the returned `Finding` values do not carry; two runs over equal
   inputs return equal tuples, which is what J8 asserts.
7. **The corpus-write branch in `completion`.** A `Registration` whose
   `intent_token` equals a `corpus-write` intent's token reads `CLOSED`
   without consulting `held`; `INDETERMINATE` is unreachable for that kind,
   because nothing about the pointer bears on the reading.
```

- [ ] **Step 3: File the science change requests**

In `/mnt/ssd/Dropbox/science/docs/plans/2026-08-31-command-framework.md`, Task 12's *Consumes* block, replace the `scoped` and `open_attended_session` bullets and append two notes:

```markdown
  - `beliefs.session.open_attended_session(world_config, operations_root, *, coordination: ProfileSpec | None = None) -> WriterSession` — **changed 2026-09-05 by the beliefs writer-session design §3.1, decision 12**: the launcher supplies the compiled coordination profile for coordination-class commands; without it those commands refuse `CoordinationUnavailable` at the act
  - `WriterSession.scoped(required, invocation_id) -> ScopedWriter` — **changed 2026-09-05 by the beliefs writer-session design §5, decision 12**: the writer is bound to the invocation id the dispatcher has already minted, and acts only while that invocation is the current one (raises `PermitExceeded` when the requirement exceeds the session permit — the declaration-time refusal)
  - **Note (2026-09-05):** `tests/helpers/world.py` calls `open_corpus(corpus_root)` and `world.admit(..., actor="fixture")` without an `Authority`; beliefs cut 17 removed both forms. Fix before Step 2 can run.
  - **Note (2026-09-05):** a `delete`-class command, if ever declared, renders an empty canonical report — its `act` line carries no minted identities (beliefs writer-session design §8 item 8).
```

In `_invoke_write`, the plan's `writer = self._session.scoped(self._required(decl))` becomes `writer = self._session.scoped(self._required(decl), iid)`; make that one edit in the fenced code so the plan and the contract agree.

In `docs/specs/2026-08-31-command-framework-design.md` §4.2, after "`WriterSession.scoped(required)`, which either returns an **invocation-scoped writer** or a structured refusal (§6.3)", add:

```markdown
**Amended 2026-09-05 (`beliefs` writer-session design §5).** `scoped` takes
the invocation id as its second argument — `scoped(required, invocation_id)`
— and the writer it returns acts only while that invocation is the session's
current one. A writer scoped before the claim and outside the dispatcher's
lock cannot otherwise be told from another invocation's, and a writer
retained across invocations would carry its own permit into a later one.
```

And in §5.1 after the `open_attended_session` bullet:

```markdown
  **Amended 2026-09-05 (`beliefs` writer-session design §3.1).** The
  constructor takes an optional keyword `coordination`, the compiled
  `ProfileSpec` for the corpus; without it coordination-class commands refuse
  `CoordinationUnavailable` at the act. The launcher's configuration therefore
  names the contract documents the profile compiles from.
```

Commit in the science repo:

```bash
cd /mnt/ssd/Dropbox/science && git add docs && git commit -m "docs(command-framework): take the beliefs writer-session change requests

scoped(required, invocation_id) binds the writer to its invocation;
open_attended_session takes the coordination profile by keyword; two notes
on the fixture helpers and the empty delete report."
```

- [ ] **Step 4: Confirm the task children**

The twelve children (one per `### Task N:` heading, chained by dependency) were created when this plan was banked. From the worktree root, `tasks tree beliefs-afbbff --pretty` lists them; `tasks ready` offers exactly the first. `tasks start` it if Step 1 has not already.

- [ ] **Step 5: Gates and commit**

Run the three gates (the design-corpus guard reads the design; §13 must not break the row inventory), then:

```bash
git add docs/designs/2026-09-05-writer-session-design.md docs/plans/2026-09-05-writer-session.md tasks/
tasks done <task-1-id> "§13 banked; science change requests filed; 12 task children chained"
git add tasks/
git commit -m "docs(session): bank the implementation amendment and file the science change requests"
```

---

### Task 2: The `corpus-write` operation kind, its qualification, and the new error types

**Files:**
- Modify: `python/src/beliefs/report.py` (`OPERATION_KINDS`, `completion`)
- Modify: `python/src/beliefs/intents/reduce.py` (`_qualify_one`)
- Modify: `python/src/beliefs/errors.py` (seven new classes)
- Test: `python/tests/test_report.py`, `python/tests/test_intent_reduce.py`, `python/tests/test_errors_session.py` (new)

**Interfaces:**
- Produces: `report.OPERATION_KINDS` containing `"corpus-write"`; `OperationIntent("corpus-write", token, actor)` constructs; `completion(intent, registrations, held)` returns `CLOSED` for a `corpus-write` intent with a token-matching registration; `_qualify_one` returns `IntentQualification(digest, "operation", "matched", registration_digest)` for a committed fulfilling registration of a `corpus-write` intent regardless of record paths; `errors.PlanRefused`, `errors.OperationPortMissing` (both `WriteRefused`), `errors.SessionRefused`, `errors.SessionClosed`, `errors.SessionProtocolError`, `errors.SessionLedgerFailed`, `errors.LedgerMalformed` (all `ScienceError`).

- [ ] **Step 1: `tasks start <task-2-id>`**

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_report.py`:

```python
# --- corpus-write (writer-session design §4.1) --------------------------------
def test_corpus_write_is_an_operation_kind_and_constructs_an_intent():
    assert "corpus-write" in report_values.OPERATION_KINDS
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    assert intent.kind == "corpus-write"


def test_a_corpus_write_intent_reads_closed_on_a_token_matching_registration_whatever_it_points_at():
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    registrations = (Registration(intent_token="tok-9", pointer="proposition/p1.md"),)
    assert completion(intent, registrations, held={}) == CLOSED
    assert completion(intent, registrations, held={"proposition/p1.md": object()}) == CLOSED


def test_a_corpus_write_intent_with_no_registration_reads_unfinished():
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    assert completion(intent, registrations=(), held={}) == UNFINISHED
    assert completion(intent, (Registration(intent_token="other", pointer="x"),), held={}) == UNFINISHED
```

Append to `tests/test_intent_reduce.py`:

```python
def _corpus_write_intent(digest: str = "i" * 64) -> IntentEntryView:
    payload = v1.encode({"kind": "corpus-write", "event_token": "tok-9", "actor": "session:" + "a" * 32})
    return IntentEntryView(digest=digest, payload=payload)


def _registration(digest: str, fulfills: str, final=()) -> RegisteredEntryView:
    return RegisteredEntryView(digest=digest, txid="t1", initial=(), final=tuple(final), fulfills=fulfills)


def _settled(digest: str, registration: str, committed: bool) -> SettledEntryView:
    return SettledEntryView(digest=digest, txid="t1", registration=registration, committed=committed)


def _facts(state):
    return (("kind", "file"),) if state == "file" else (("kind", "absent"),)


def test_a_corpus_write_intent_is_matched_by_its_committed_registration_with_no_record_inspected():
    entries = (
        _corpus_write_intent(),
        _registration("r" * 64, "i" * 64, final=(("proposition/p1.md", "file"),)),
        _settled("s" * 64, "r" * 64, True),
    )
    rows, findings = qualify_chain(entries, records={}, state_facts=_facts)
    assert rows == (IntentQualification("i" * 64, "operation", "matched", "r" * 64),)
    assert findings == ()


def test_a_corpus_write_deletion_registration_with_an_empty_surface_still_matches():
    entries = (_corpus_write_intent(), _registration("r" * 64, "i" * 64), _settled("s" * 64, "r" * 64, True))
    rows, findings = qualify_chain(entries, records={}, state_facts=_facts)
    assert rows[0].state == "matched" and findings == ()


def test_a_rolled_back_corpus_write_registration_is_an_attempt_without_recorded_outcome():
    entries = (_corpus_write_intent(), _registration("r" * 64, "i" * 64), _settled("s" * 64, "r" * 64, False))
    rows, findings = qualify_chain(entries, records={}, state_facts=_facts)
    assert rows[0].state == "attempt-without-recorded-outcome"
    assert {f.code for f in findings} == {"intent-attempt-without-recorded-outcome", "intent-fulfillment-non-qualifying"}


def test_an_unsettled_corpus_write_registration_is_unresolvable():
    entries = (_corpus_write_intent(), _registration("r" * 64, "i" * 64))
    rows, _ = qualify_chain(entries, records={}, state_facts=_facts)
    assert rows[0].state == "unresolvable"


def test_every_other_operation_kind_still_needs_a_token_bearing_report():
    payload = v1.encode({"kind": "audit", "event_token": "tok-9", "actor": "session:" + "a" * 32})
    entries = (
        IntentEntryView(digest="i" * 64, payload=payload),
        _registration("r" * 64, "i" * 64, final=(("proposition/p1.md", "file"),)),
        _settled("s" * 64, "r" * 64, True),
    )
    rows, _ = qualify_chain(entries, records={}, state_facts=_facts)
    assert rows[0].state != "matched"
```

Check the attribute name of `IntentQualification`'s third field (`state` or similar) in `reduce.py` and use it verbatim.

Create `tests/test_errors_session.py`:

```python
from beliefs.errors import (
    LedgerMalformed,
    OperationPortMissing,
    PlanRefused,
    ScienceError,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
    SessionRefused,
    WriteRefused,
)


def test_the_session_errors_have_their_designed_bases():
    assert issubclass(PlanRefused, WriteRefused)
    assert issubclass(OperationPortMissing, WriteRefused)
    for hard in (SessionRefused, SessionClosed, SessionProtocolError, SessionLedgerFailed, LedgerMalformed):
        assert issubclass(hard, ScienceError) and not issubclass(hard, WriteRefused)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_report.py tests/test_intent_reduce.py tests/test_errors_session.py -q -p no:cacheprovider`
Expected: FAIL — `MalformedRecord` on the intent construction, `ImportError` on the errors.

- [ ] **Step 4: Implement**

`report.py`:

```python
OPERATION_KINDS = ("acquisition", "audit", "consolidate", "corpus-write", "import", "move", "re-check", "run-attempt")
```

and in `completion`, after the argument validation and before the `decoded = ...` line:

```python
    if type(intent) is OperationIntent and intent.kind == "corpus-write":
        # Writer-session design §4.1: the registration is the fulfillment;
        # nothing about its pointer bears on the reading (§13 item 7).
        return CLOSED if any(r.intent_token == intent.event_token for r in registrations) else UNFINISHED
```

`intents/reduce.py`, at the top of `_qualify_one`'s body:

```python
    value = intent.value
    if intent.shape == "operation" and isinstance(value, OperationIntent) and value.kind == "corpus-write":
        return _qualify_corpus_write(intent, registrations, settlement)
```

and the new function beside it:

```python
def _qualify_corpus_write(
    intent: shapes.DecodedIntent,
    registrations: list[RegisteredEntryView],
    settlement: Mapping[str, bool],
) -> tuple[IntentQualification, tuple[Finding, ...]]:
    """Writer-session design §4.1: a committed registration fulfilling a
    `corpus-write` intent qualifies it, whatever it publishes — one record, a
    replacement, or nothing for a deletion. Records are not inspected."""
    unresolved = False
    rolled_back: list[str] = []
    for registration in registrations:
        committed = settlement.get(registration.digest)
        if committed is None:
            unresolved = True
        elif committed:
            return IntentQualification(intent.digest, intent.shape, "matched", registration.digest), ()
        else:
            rolled_back.append(registration.digest)
    if unresolved:
        return IntentQualification(intent.digest, intent.shape, "unresolvable", None), ()
    findings = [
        Finding(
            severity="warning",
            code="intent-attempt-without-recorded-outcome",
            ref=intent.digest,
            detail="",
            message="a durable intent whose every pointer fully resolves and none qualifies",
        ),
        *(
            Finding(
                severity="warning",
                code="intent-fulfillment-non-qualifying",
                ref=digest,
                detail=f"intent={intent.digest} reason=no-record",
                message="a committed fulfillment that does not qualify its intent",
            )
            for digest in rolled_back
        ),
    ]
    return IntentQualification(intent.digest, intent.shape, "attempt-without-recorded-outcome", None), tuple(findings)
```

Import `OperationIntent` from `beliefs.report` in `reduce.py` (it is already imported in `shapes.py`).

`errors.py`, after `ActorMismatch`:

```python
class PlanRefused(WriteRefused):
    """The operation seam's preflight refused the plan — shape, a reserved
    leaf, or the record ceiling — before any intent (writer-session design
    §4.3 step 3). Wraps the executor layer's `PlanRefusedError` so the
    dispatcher's one refusal handler sees a `WriteRefused`."""


class OperationPortMissing(WriteRefused):
    """An operation write was asked of a writer constructed without an
    operation port (writer-session design §4.2)."""


class SessionRefused(ScienceError):
    """`open_attended_session` refused its configuration (writer-session
    design §3.1): not exactly one corpus root, no manifest, or no well-formed
    chain."""


class SessionClosed(ScienceError):
    """A method was called on a session after `close()` (design §3.4)."""


class SessionProtocolError(ScienceError):
    """A close naming anything but the current invocation, or an act by a
    writer whose invocation is not current (design §3.3, §5). Unreachable
    through the dispatcher's lock; reaching it is a bug, never an outcome."""


class SessionLedgerFailed(ScienceError):
    """A ledger `write`, `flush` or `fsync` failed; the session is terminal
    and appends nothing further (design §3.2, decision 20)."""


class LedgerMalformed(ScienceError):
    """The ledger reader refused a line (design §3.5)."""
```

- [ ] **Step 5: Run the tests and the gates**

Run: `uv run --frozen pytest tests/test_report.py tests/test_intent_reduce.py tests/test_errors_session.py tests/test_deletion.py -q -p no:cacheprovider` — PASS. Then the three gates and the staleness probe (cut 11's arm quotes `OPERATION_KINDS` in `shapes.py`, which this task does not touch; the probe must equal the baseline).

- [ ] **Step 6: Commit**

```bash
tasks done <task-2-id> "corpus-write operation kind, registration-qualified in both reductions; session error types"
git add python/src/beliefs/report.py python/src/beliefs/intents/reduce.py python/src/beliefs/errors.py python/tests tasks/
git commit -m "feat(report): add the corpus-write operation kind qualified by its registration"
```

---

### Task 3: The port's `preflight`, the registration-digest return, and factory-owned recovery

**Files:**
- Modify: `python/src/beliefs/runrecord.py:89-100` (`OperationPort`)
- Modify: `python/src/beliefs/root.py` (`plan_preflight`, `DurableOperationPort`, `_DurableExecutorFactory`, `durable_operation_port`, `log_seam`)
- Modify: every test port (`tests/test_corpus_write.py:83,120,136`, `tests/test_relocation_recovery.py:245`, `tests/test_operation_port.py:62`, `tests/test_permit_entry_points.py:286`, `tests/test_boundary.py:114`, `tests/test_run_persistence.py:102,131`, `tests/acceptance/test_intent_boundary_acceptance.py:183`, `tests/fixtures_cut3.py:446`, `tests/test_import_bundle.py:51,731,752`)
- Test: `python/tests/test_operation_port.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `OperationPort.preflight(plan: WritePlan) -> None`; `OperationPort.execute_fulfilling(plan, fulfills) -> str` (the registration digest); `root.plan_preflight(plan) -> None`; `root.durable_operation_port(root: Path, authority: Authority) -> DurableOperationPort`; `root.log_seam() -> LogSeam`; `root.durable_executor_factory()` returns a `_DurableExecutorFactory` instance carrying `recover(root: Path) -> None`.

- [ ] **Step 1: `tasks start <task-3-id>`**

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_operation_port.py` inside a new class:

```python
class TestPreflightReadbackAndRecovery:
    def test_preflight_refuses_an_over_ceiling_plan_before_any_engine_call(self, tmp_path):
        port = _registered_port(tmp_path / "r")
        big = CreateOp("proposition/big.md", b"x" * (RECORD_CEILING + 1))
        with pytest.raises(PlanRefusedError):
            port.preflight([big])
        assert _registrations(tmp_path / "r") == []

    def test_preflight_refuses_a_reserved_leaf(self, tmp_path):
        port = _registered_port(tmp_path / "r")
        with pytest.raises(PlanRefusedError):
            port.preflight([CreateOp(".#~stage/x.md", b"x")])

    def test_execute_fulfilling_returns_the_registration_digest_the_chain_holds(self, tmp_path):
        root = tmp_path / "r"
        port = _registered_port(root)
        intent = port.append_intent(PAYLOAD)
        digest = port.execute_fulfilling([CreateOp("proposition/p1.md", b"---\nid: proposition:p1\n---\n")], intent)
        (registration,) = _registrations(root)
        assert digest == registration.digest and registration.fulfills == intent

    def test_the_durable_factory_carries_recover_and_the_default_executor_does_not(self):
        from nodes.core.write_plan import DefaultExecutor

        factory = durable_executor_factory()
        assert callable(getattr(factory, "recover", None))
        assert getattr(DefaultExecutor, "recover", None) is None
        assert durable_executor_factory() is factory

    def test_recover_on_an_unregistered_root_returns_without_reading_a_chain(self, tmp_path):
        durable_executor_factory().recover(tmp_path / "never-registered")  # no exception

    def test_recover_on_a_registered_root_reads_the_chain(self, tmp_path):
        root = tmp_path / "r"
        _registered_port(root)
        durable_executor_factory().recover(root)  # resolves recovery; nothing to settle here
        assert _registrations(root) == []
```

Add the imports the class needs: `from nodes.core.errors import PlanRefusedError`, `from beliefs.root import durable_executor_factory`, `CreateOp` from `nodes.core.write_plan`. Also add to `FakePort`:

```python
    def preflight(self, plan: WritePlan) -> None:
        pass
```

and make its `execute_fulfilling` return `"r" * 64`.

- [ ] **Step 3: Run to verify failure**

Run: `uv run --frozen pytest tests/test_operation_port.py -q -p no:cacheprovider` — FAIL with `AttributeError: preflight` and a `None` digest.

- [ ] **Step 4: Implement**

`runrecord.py`, the protocol:

```python
class OperationPort(Protocol):
    @property
    def authority(self) -> Authority: ...

    def append_intent(self, payload: bytes) -> str: ...

    def preflight(self, plan: WritePlan) -> None:
        """The state-free checks the engine would make — plan shape, reserved
        leaves, the record ceiling — raised before any intent (writer-session
        design §4.3 step 3)."""
        ...

    def execute(self, plan: WritePlan) -> None: ...

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        """Commit the plan fulfilling `fulfills` and return the digest of the
        registration it committed, read from the chain itself (design §4.4)."""
        ...
```

`root.py`:

```python
def plan_preflight(plan: WritePlan) -> None:
    """Writer-session design §4.3 step 3: the two checks that need no engine state."""
    _refuse_malformed(plan)
    _refuse_over_ceiling(plan)
```

In `DurableOperationPort`:

```python
    def preflight(self, plan: WritePlan) -> None:
        plan_preflight(plan)

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        with _operation_lock_for(self.root):
            self._execute_fulfilling(plan, fulfills)
            return _registration_for(self.root, self._backend, self._storage, self._metadata_root, fulfills)
```

and beside it:

```python
def _registration_for(root: Path, backend: Backend, storage: StorageProfile, metadata_root: Path, fulfills: str) -> str:
    """The digest of the one registration fulfilling `fulfills`, read back from
    the chain (design §4.4): digests come from the chain itself, as anchor
    carriage already reads them, and the executor's outcome stays discarded."""
    try:
        view = read_chain(backend, str(root), str(metadata_root), storage)
    except Exception as caught:  # noqa: BLE001 - every engine shape maps to the seam's one failure type
        raise ExecutionError(f"registration readback failed: {caught}", index=None, applied=None) from caught
    matches = [digest for digest, entry in view.entries if type(entry) is RegisteredEntry and entry.fulfills == fulfills]
    if len(matches) != 1:
        raise ExecutionError(
            f"expected exactly one registration fulfilling {fulfills}, found {len(matches)}", index=None, applied=None
        )
    return matches[0]
```

Replace the module-level factory:

```python
class _DurableExecutorFactory:
    """The stable root-taking factory the write API is built with, carrying the
    root's recovery capability (writer-session design decision 19)."""

    def __call__(self, root: Path) -> DurableExecutor:
        return _durable_executor(root)

    def recover(self, root: Path) -> None:
        """Resolve the engine's recovery for `root` (§13 item 3): a no-op on a
        root that is not writable — the write itself refuses registration —
        else `read_chain`, which resolves recovery under the project lock."""
        target = Path(root)
        try:
            state = read_lifecycle_state(target)
        except Exception:  # noqa: BLE001 - not a registered root: nothing to recover, and the write itself refuses
            return
        if state is not LifecycleState.WRITABLE:
            return
        try:
            read_chain(_PRODUCTION_BACKEND, str(target), str(metadata_root_for(target)), PRODUCTION_STORAGE)
        except Exception as caught:  # noqa: BLE001 - one seam failure type
            raise ExecutionError(f"recovery failed: {caught}", index=None, applied=None) from caught


_DURABLE_EXECUTOR_FACTORY = _DurableExecutorFactory()


def durable_executor_factory() -> _DurableExecutorFactory:
    """The stable root-taking factory the write API is built with."""
    return _DURABLE_EXECUTOR_FACTORY
```

`recover` returns on any lifecycle-read failure and on any non-writable state because an unregistered root has nothing to recover and its write refuses registration itself; `test_a_write_against_an_unregistered_root_refuses` pins that refusal's shape and must pass unchanged in Step 5.

Add the two public seams:

```python
def durable_operation_port(root: Path, authority: Authority) -> DurableOperationPort:
    """The port `open_corpus` binds, exposed for the session composition (§13 item 1)."""
    resolved = Path(root).resolve()
    return DurableOperationPort(
        resolved,
        backend=_PRODUCTION_BACKEND,
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(resolved),
        authority=authority,
    )


def log_seam() -> LogSeam:
    """The production log seam, exposed for the session composition (§13 item 1)."""
    return _LOG_SEAM
```

and make `open_corpus` call `durable_operation_port(root, authority)` instead of building the port inline.

Update every test port listed in **Files**: add `def preflight(self, plan): pass` (or `plan_preflight(plan)` where the port is durable-shaped) and make `execute_fulfilling` return a 64-hex string (`"r" * 64` or a counter-derived digest). The holdings seam's `_store_publish_fulfilling` and `_publish_operation_report`'s call ignore the return; no change there.

- [ ] **Step 5: Run the tests and the gates**

Run the whole suite: `uv run --frozen pytest -q -p no:cacheprovider`. `test_a_write_against_an_unregistered_root_refuses` and `test_capability_boundary.py` must pass unchanged (`read_chain` is named only in `root.py`). Then ruff, pyright, the staleness probe.

- [ ] **Step 6: Commit**

```bash
tasks done <task-3-id> "port preflight, registration-digest return, factory recover(root), durable_operation_port and log_seam"
git add python/src/beliefs/runrecord.py python/src/beliefs/root.py python/tests tasks/
git commit -m "feat(root): give the operation port a preflight and a registration readback, and the durable factory recovery"
```

---

### Task 4: The unresolved root — `_locked`, `_settle`, `_submitting`

**Files:**
- Modify: `python/src/beliefs/corpus.py:383-390` (`_RootState`), `:451-466` (`_root_state_for`), every `with self._operation:` (lines 1169, 1192, 1266, 1301, 1475, 1565, 1636, 1690, 1735 at HEAD), `_add_locked`, `_replace_locked`, `_delete_locked`, `adopt_manifest`, `_publish_operation_report`, `import_bundle`'s payload execute
- Modify: `python/src/beliefs/relocation.py:43`
- Test: `python/tests/test_corpus_write.py`, `python/tests/test_relocation.py`

**Interfaces:**
- Consumes: `executor_factory.recover` (Task 3).
- Produces: `_RootState.unresolved: bool` (initially `True`), `_RootState.recover: Callable[[Path], None] | None`; `CorpusWriter._locked()` (context manager: acquire, settle, yield), `CorpusWriter._settle()`, `CorpusWriter._submitting()` (context manager bracketing every write submission).

- [ ] **Step 1: `tasks start <task-4-id>`**

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_corpus_write.py`:

```python
class TestTheUnresolvedRoot:
    """Writer-session design §4.3 'Settlement before every state-dependent read'."""

    def test_a_fresh_root_state_is_unresolved_and_the_first_write_settles_it(self, tmp_path):
        from beliefs.corpus import _root_state_for

        writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL)
        state = _root_state_for(tmp_path, DefaultExecutor)
        assert state.unresolved is True and state.recover is None
        writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        assert state.unresolved is False

    def test_the_root_state_binds_the_factory_recover(self, tmp_path):
        from beliefs.corpus import _root_state_for

        calls = []

        class Factory:
            def __call__(self, root):
                return DefaultExecutor(root)

            def recover(self, root):
                calls.append(root)

        factory = Factory()
        writer = CorpusWriter(tmp_path, factory, authority=FULL)
        assert _root_state_for(tmp_path, factory).recover is factory.recover
        writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        assert calls == [tmp_path.resolve()]  # settled once, before the first prepare

    def test_a_failed_submission_leaves_the_root_unresolved_and_the_next_write_recovers_first(self, tmp_path):
        from beliefs.corpus import _root_state_for

        events = []

        class Halting(DefaultExecutor):
            fail = False

            def execute(self, plan):
                if Halting.fail:
                    Halting.fail = False
                    raise ExecutionError("halted", index=0, applied=0)
                events.append("execute")
                return super().execute(plan)

        class Factory:
            def __call__(self, root):
                return Halting(root)

            def recover(self, root):
                events.append("recover")

        factory = Factory()
        writer = CorpusWriter(tmp_path, factory, authority=FULL)
        writer.add(stored.proposition_node("p0", title="p0", claim={"operator": "affects"}))
        events.clear()
        Halting.fail = True
        with pytest.raises(ExecutionError):
            writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        assert _root_state_for(tmp_path, factory).unresolved is True
        writer.add(stored.proposition_node("p2", title="p2", claim={"operator": "affects"}))
        assert events == ["recover", "execute"]
        assert _root_state_for(tmp_path, factory).unresolved is False

    def test_a_failed_recovery_keeps_the_root_unresolved_and_blocks_the_prepare(self, tmp_path):
        from beliefs.corpus import _root_state_for

        class Factory:
            def __call__(self, root):
                return DefaultExecutor(root)

            def recover(self, root):
                raise ExecutionError("engine down", index=None, applied=None)

        factory = Factory()
        writer = CorpusWriter(tmp_path, factory, authority=FULL)
        with pytest.raises(ExecutionError, match="engine down"):
            writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        assert _root_state_for(tmp_path, factory).unresolved is True
        assert not (tmp_path / "proposition").exists()

    def test_no_bare_lock_acquisition_remains_outside_locked(self):
        import ast, inspect
        from beliefs import corpus as module

        tree = ast.parse(inspect.getsource(module))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    expression = item.context_expr
                    if isinstance(expression, ast.Attribute) and expression.attr == "_operation":
                        offenders.append(node.lineno)
        # `_locked` itself holds the one permitted `with self._operation`.
        assert len(offenders) == 1, offenders
```

The last test asserts exactly one bare acquisition remains — inside `_locked`. Note: the `Factory` class carrying `recover` must be a distinct object per test because `_root_state_for` keys on the factory identity per root; `tmp_path` differs per test, so it is.

- [ ] **Step 3: Run to verify failure**

Run: `uv run --frozen pytest tests/test_corpus_write.py -q -p no:cacheprovider -k Unresolved` — FAIL (`unresolved` attribute missing; many bare acquisitions).

- [ ] **Step 4: Implement**

`_RootState`:

```python
@dataclass
class _RootState:
    lock: OperationLock
    corpus: Corpus
    view: ReadView
    executor_factory: Callable[[Path], WritePlanExecutor]
    recover: Callable[[Path], None] | None
    unresolved: bool = True
    """Writer-session design decision 19: true at process start and from every
    submission until the in-memory state is known to match disk."""
```

`_root_state_for`: `state = _RootState(lock, corpus, ReadView(corpus), executor_factory, getattr(executor_factory, "recover", None))`.

`CorpusWriter`:

```python
    @contextmanager
    def _locked(self) -> Iterator[None]:
        """Acquire the root's operation lock and settle an unresolved root before
        any state-dependent read (writer-session design §4.3)."""
        with self._operation:
            self._settle()
            yield

    def _settle(self) -> None:
        state = self._state
        if not state.unresolved:
            return
        if state.recover is not None:
            state.recover(state.corpus.store.root)
        self._reconstruct()
        state.unresolved = False

    @contextmanager
    def _submitting(self) -> Iterator[None]:
        """Bracket one submission: unresolved from before the write until the
        in-memory update after it completes; a failure inside leaves it set."""
        self._state.unresolved = True
        yield
        self._state.unresolved = False
```

Then, mechanically: every `with self._operation:` in `CorpusWriter` becomes `with self._locked():`; every `return self._corpus.add(x)` in a family body becomes

```python
            with self._submitting():
                return self._corpus.add(x)
```

(`add`, `_add_locked`, `_replace_locked`, `retract`, `supersede`, `revise`, `mint_coordination`, `revise_coordination`); `_delete_locked`'s `self._corpus.executor.execute(...)` + `self._reconstruct()` and `adopt_manifest`'s executor call and `import_bundle`'s `self._corpus.executor.execute(payload); self._reconstruct()` and `_publish_operation_report`'s `execute_fulfilling(...); self._reconstruct()` are each wrapped in `with self._submitting():`. In `relocation.py:43`, `stack.enter_context(roots[key]._operation)` becomes `stack.enter_context(roots[key]._locked())`.

Add `from contextlib import contextmanager` and `Iterator` to `corpus.py`'s imports.

- [ ] **Step 5: Run the whole suite and the gates**

`uv run --frozen pytest -q -p no:cacheprovider`; ruff; pyright; the staleness probe. Pinned arms that quote `with self._operation:` in `corpus.py` (check cuts 14–18) will go stale: for each, record the arm in this task's commit message and in design §13 as a new dated item ("the acquisition moved into `_locked`; the arm's `before` no longer occurs"), and do **not** edit the frozen arms module — the discharge of cut 19 cites them (Task 12).

- [ ] **Step 6: Commit**

```bash
tasks done <task-4-id> "unresolved root state, _locked settlement on every path, _submitting bracket"
git add python/src/beliefs/corpus.py python/src/beliefs/relocation.py python/tests docs/designs/2026-09-05-writer-session-design.md tasks/
git commit -m "feat(corpus): settle an unresolved root before every prepare"
```

---

### Task 5: The operation seams — prepare helpers, `OperationWrites`, `_commit`, and the inventory row

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`CorpusWriter.add/retract/supersede/revise/delete/mint_coordination/revise_coordination`, new `_prepare_*`, `OperationCommit`, `OperationWrites`, `CorpusWriter.operations`)
- Modify: `python/tests/test_permit_boundary.py:53-70` (`WRITE_ENTRY_POINTS`)
- Test: `python/tests/test_operation_writes.py` (new)

**Interfaces:**
- Consumes: `OperationPort.preflight`, `execute_fulfilling -> str` (Task 3); `_locked`, `_submitting` (Task 4); `PlanRefused`, `OperationPortMissing` (Task 2).
- Produces: `corpus.OperationCommit(record: Node | None, event_token: str, intent_digest: str, entry_digest: str)`; `CorpusWriter.operations -> OperationWrites` with `add(node)`, `retract(record)`, `supersede(successor, *, of)`, `revise(node)`, `delete(ref)`, `mint_coordination(kind, *, project=None, content)`, `revise_coordination(kind, address, *, predecessors, content)`, each returning `OperationCommit`; `OperationWrites._commit(kind, prepare)` the inventoried definition; `CorpusWriter._prepare_add(node) -> Node`, `_prepare_retract(record) -> Node`, `_prepare_supersede(successor, of) -> Node`, `_prepare_revise(node) -> Node`, `_prepare_delete(ref) -> Node`, `_prepare_mint_coordination(kind, project, content) -> Node`, `_prepare_revise_coordination(kind, address, predecessors, content) -> Node`.

- [ ] **Step 1: `tasks start <task-5-id>`**

- [ ] **Step 2: Write the failing tests**

Create `tests/test_operation_writes.py`:

```python
"""The operation seams (writer-session design §4.2–§4.4): J1's refusal-before-
intent arms, J3's act-time permit refusal, J4's actor rule — portably, over the
in-memory executor and a port returning synthetic registration digests."""

from __future__ import annotations

import inspect
from typing import ClassVar

import pytest
from authority import ACTOR, FULL, narrowed
from fixtures_cut6 import PINS
from nodes.core.errors import PlanRefusedError
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DefaultExecutor, DeleteOp, ReplaceOp, WritePlan
from test_deletion import retraction_for

from beliefs import stored
from beliefs.corpus import CorpusWriter, OperationCommit, OperationWrites
from beliefs.errors import (
    ActorMismatch,
    OperationPortMissing,
    PermitExceeded,
    PermitFact,
    PlanRefused,
    RelocationTargetMissing,
    WriteRefused,
)
from beliefs.identity import v1
from beliefs.intents.shapes import decode_intent
from beliefs.permit import Authority, WritePermit
from beliefs.report import OperationIntent
from beliefs.world.records import RECORD_CEILING


def proposition(slug: str, operator: str = "affects") -> Node:
    return stored.proposition_node(slug, title=slug, claim={"operator": operator})


class RecordingPort:
    """A port that appends nothing durable but records the two primitive calls
    in order and returns synthetic digests, so a test can assert what the seam
    did and in what order."""

    def __init__(self, authority: Authority, *, fail_preflight: bool = False) -> None:
        self.authority = authority
        self.calls: list[tuple[str, object]] = []
        self.fail_preflight = fail_preflight
        self._counter = 0

    def _digest(self, tag: str) -> str:
        self._counter += 1
        return (tag * 64)[:60] + f"{self._counter:04d}"

    def append_intent(self, payload: bytes) -> str:
        digest = self._digest("1")
        self.calls.append(("append_intent", payload))
        return digest

    def preflight(self, plan: WritePlan) -> None:
        self.calls.append(("preflight", tuple(plan)))
        if self.fail_preflight:
            raise PlanRefusedError("preflight refused by the test port")
        for op in plan:
            content = getattr(op, "content", None)
            if isinstance(content, bytes) and len(content) > RECORD_CEILING:
                raise PlanRefusedError("over the record ceiling")

    def execute(self, plan: WritePlan) -> None:
        self.calls.append(("execute", tuple(plan)))

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        self.calls.append(("execute_fulfilling", (tuple(plan), fulfills)))
        DefaultExecutor(self.root).execute(list(plan))  # apply so the rebuilt view sees the record
        return self._digest("2")


def writer_over(tmp_path, authority: Authority = FULL, **port_kwargs) -> tuple[CorpusWriter, RecordingPort]:
    port = RecordingPort(authority, **port_kwargs)
    port.root = tmp_path
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=authority, operation_port=port)
    return writer, port


def intents_of(port: RecordingPort) -> list[OperationIntent]:
    decoded = [decode_intent("d" * 64, payload) for kind, payload in port.calls if kind == "append_intent"]
    return [d.value for d in decoded]


# --- J1: one intent, one fulfilling execution, in order --------------------------
def test_add_commits_as_intent_then_fulfilling_execution_and_returns_the_commit(tmp_path):
    writer, port = writer_over(tmp_path)
    commit = writer.operations.add(proposition("p1"))
    assert type(commit) is OperationCommit and commit.record is not None and commit.record.id == "proposition:p1"
    kinds = [kind for kind, _ in port.calls]
    assert kinds == ["preflight", "append_intent", "execute_fulfilling"]
    (intent,) = intents_of(port)
    assert intent == OperationIntent("corpus-write", commit.event_token, ACTOR)
    _, (plan, fulfills) = port.calls[2]
    assert fulfills == commit.intent_digest and type(plan[0]) is CreateOp
    assert writer.read_view.get("proposition:p1").id == "proposition:p1"


def test_delete_commits_a_delete_op_and_carries_no_record(tmp_path):
    writer, port = writer_over(tmp_path)
    writer.add(proposition("p1"))
    port.calls.clear()
    commit = writer.operations.delete("proposition:p1")
    assert commit.record is None
    _, (plan, _) = port.calls[-1]
    assert type(plan[0]) is DeleteOp


def test_revise_commits_a_replace_op(tmp_path):
    writer, port = writer_over(tmp_path)
    node = writer.add(proposition("p1"))
    port.calls.clear()
    revised = node.model_copy(update={"title": "renamed"})
    commit = writer.operations.revise(revised)
    _, (plan, _) = port.calls[-1]
    assert type(plan[0]) is ReplaceOp and commit.record is not None


# --- J1: every refusal precedes the intent -------------------------------------
@pytest.mark.parametrize(
    "authority, kind",
    [
        (narrowed(kinds=("source",), families=("corpus-write",)), "proposition"),
        (narrowed(kinds=("proposition",), families=("run",)), "proposition"),
    ],
)
def test_a_permit_refusal_appends_nothing(tmp_path, authority, kind):
    writer, port = writer_over(tmp_path, authority)
    with pytest.raises(PermitExceeded):
        writer.operations.add(proposition("p1"))
    assert port.calls == []


def test_a_malformed_record_is_refused_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    with pytest.raises(WriteRefused):
        writer.operations.add(proposition("p1").model_copy(update={"kind": "act-report"}))
    assert not any(kind == "append_intent" for kind, _ in port.calls)


def test_the_operation_add_refuses_a_retraction_exactly_as_add_does(tmp_path):
    writer, port = writer_over(tmp_path)
    target = writer.add(proposition("p1"))
    retraction = retraction_for(target, "proposition:p1")
    with pytest.raises(WriteRefused) as ordinary:
        writer.add(retraction)
    with pytest.raises(WriteRefused) as operation:
        writer.operations.add(retraction)
    assert type(operation.value) is type(ordinary.value) and str(operation.value) == str(ordinary.value)
    assert not any(kind == "append_intent" for kind, _ in port.calls)


def test_an_over_ceiling_record_is_plan_refused_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    huge = proposition("p1").model_copy(update={"body": "x" * (RECORD_CEILING + 1)})
    with pytest.raises(PlanRefused) as caught:
        writer.operations.add(huge)
    assert isinstance(caught.value.__cause__, PlanRefusedError)
    assert [kind for kind, _ in port.calls] == ["preflight"]


def test_a_writer_without_a_port_refuses_every_operation_before_any_refusal(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=narrowed())
    with pytest.raises(OperationPortMissing):
        writer.operations.add(proposition("p1"))


# --- J3: the act-time refusal comes from the kernel entry point ------------------
def test_the_requirement_is_the_effective_permit_at_the_act(tmp_path):
    writer, port = writer_over(tmp_path, narrowed(kinds=("proposition",), families=("corpus-write",)))
    writer.operations.add(proposition("p1"))
    with pytest.raises(PermitExceeded) as caught:
        writer.operations.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s1"}))
    assert caught.value.requirement == PermitFact("kind", "source")
    assert caught.value.capability.kinds == ("proposition",)


# --- J4: the actor is the bound one ----------------------------------------------
def test_every_intent_carries_the_bound_actor_and_no_seam_takes_one(tmp_path):
    writer, port = writer_over(tmp_path, Authority(WritePermit.full(), "session:" + "a" * 32))
    writer.operations.add(proposition("p1"))
    assert intents_of(port)[0].actor == "session:" + "a" * 32
    for name, member in inspect.getmembers(OperationWrites, inspect.isfunction):
        assert "actor" not in inspect.signature(member).parameters, name


def test_a_retraction_naming_another_actor_is_actor_mismatch_with_nothing_appended(tmp_path):
    writer, port = writer_over(tmp_path)
    target = writer.add(proposition("p1"))
    foreign = retraction_for(target, "proposition:p1")
    foreign.facets[stored.RETRACTION_FACET] = {**foreign.facets[stored.RETRACTION_FACET], "actor": "someone-else"}
    port.calls.clear()
    with pytest.raises(ActorMismatch):
        writer.operations.retract(foreign)
    assert port.calls == []
    assert writer.operations.retract(retraction_for(target, "proposition:p1")).record is not None


def test_supersede_of_a_missing_target_refuses_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    with pytest.raises(RelocationTargetMissing):
        writer.operations.supersede(proposition("p2", "inhibits"), of="proposition:gone")
    assert port.calls == []
```

The retraction mutation in `test_a_retraction_naming_another_actor...` does not recompute the semantic stamp; the assertion the row needs is `ActorMismatch`, which `retract` raises **before** stamp validation (it checks the facet's actor first), so a mutated facet without a fresh stamp is sufficient — confirm by reading `_prepare_retract`'s order after the factoring. The ceiling check is the durable executor's, so no ordinary-path ceiling test runs over `DefaultExecutor`; J1's durable arm (Task 9) covers it.

- [ ] **Step 3: Run to verify failure**

Run: `uv run --frozen pytest tests/test_operation_writes.py -q -p no:cacheprovider` — FAIL with `AttributeError: operations`.

- [ ] **Step 4: Implement**

Factor the prepare helpers out of the ordinary methods (decision 13). Each ordinary method becomes require, `_locked`, prepare, `_submitting` write:

```python
    def add(self, node: Node) -> Node:
        self._authority.require("corpus-write", (node.kind,))
        with self._locked():
            self._prepare_add(node)
            with self._submitting():
                return self._corpus.add(node)

    def _prepare_add(self, node: Node) -> None:
        """`add`'s own refusals — and not `_preflight_add_locked`, whose
        admitted kind exists for the relocation families (design §4.2)."""
        self._refuse_family_kinds(node)
        self._refuse(node)
        self._refuse_foreign_closure_actor(node)
```

`retract`: move everything between `with self._locked():` and `return self._corpus.add(record)` into `_prepare_retract(self, record: Node) -> Node` returning `record`; `supersede` → `_prepare_supersede(self, successor, of) -> Node` returning `candidate`; `revise` → `_prepare_revise(self, node) -> Node` returning `node`; `delete` → `_prepare_delete(self, ref) -> Node` (resolve under the lock, `require` on the resolved kind, `_refuse_excluded_kind`, return the node) with `delete` itself then calling `_delete_locked(node.id)`; `mint_coordination` → `_prepare_mint_coordination(self, kind, project, content) -> Node`; `revise_coordination` → `_prepare_revise_coordination(self, kind, address, predecessors, content) -> Node`. The ordinary bodies keep their behavior exactly; the tests of cut 5, 14, 16, 18 are the proof.

The facade and the seam:

```python
@sealed
@final
@dataclass(frozen=True)
class OperationCommit:
    """What one operation write committed (writer-session design §4.2)."""

    record: Node | None
    event_token: str
    intent_digest: str
    entry_digest: str


class OperationWrites:
    """The seven session-mediated writes, each one `corpus-write` intent
    followed by one fulfilling registration (writer-session design §4.2–§4.3).
    Obtained through `CorpusWriter.operations`; never constructed elsewhere."""

    def __init__(self, writer: CorpusWriter) -> None:
        self._writer = writer

    def add(self, node: Node) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            writer._prepare_add(node)
            return node, [writer._create_or_replace_op(node)]

        return self._commit(node.kind, prepare)

    def retract(self, record: Node) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            prepared = writer._prepare_retract(record)
            return prepared, [writer._create_op(prepared)]

        return self._commit("retraction", prepare)

    def supersede(self, successor: Node, *, of: str) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            candidate = writer._prepare_supersede(successor, of)
            return candidate, [writer._create_op(candidate)]

        return self._commit("proposition", prepare)

    def revise(self, node: Node) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            prepared = writer._prepare_revise(node)
            return prepared, [writer._replace_op(prepared)]

        return self._commit("proposition", prepare)

    def delete(self, ref: str) -> OperationCommit:
        writer = self._writer
        with writer._locked():
            kind = writer._prepare_delete(ref).kind  # resolves or refuses DeletionTargetMissing; the require needs the kind

            def prepare() -> tuple[None, WritePlan]:
                prepared = writer._prepare_delete(ref)  # re-read under the same (re-entrant) lock
                return None, [writer._delete_op(prepared)]

            return self._commit(kind, prepare)

    def mint_coordination(self, kind: str, *, project: CoordinationAddress | None = None, content: Mapping[str, object]) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            candidate = writer._prepare_mint_coordination(kind, project, content)
            return candidate, [writer._create_op(candidate)]

        return self._commit(kind, prepare)

    def revise_coordination(self, kind: str, address: CoordinationAddress, *, predecessors: Sequence[str], content: Mapping[str, object]) -> OperationCommit:
        writer = self._writer

        def prepare() -> tuple[Node, WritePlan]:
            candidate = writer._prepare_revise_coordination(kind, address, predecessors, content)
            return candidate, [writer._create_op(candidate)]

        return self._commit(kind, prepare)

    def _commit(self, kind: str, prepare: Callable[[], tuple[Node | None, WritePlan]]) -> OperationCommit:
        """The one primitive caller (design §4.3): require, prepare, preflight,
        intent, fulfilling execution, rebuild — in that order and no other."""
        self._writer.authority.require("corpus-write", (kind,))
        writer = self._writer
        port = writer._operation_port
        if port is None:
            raise OperationPortMissing("this corpus has no operation port; operation writes are session-mediated")
        with writer._locked():
            record, plan = prepare()
            try:
                port.preflight(plan)
            except PlanRefusedError as caught:
                raise PlanRefused(str(caught)) from caught
            token = secrets.token_hex(16)
            intent = OperationIntent("corpus-write", token, writer.authority.actor)
            intent_digest = port.append_intent(
                v1.encode({"kind": intent.kind, "event_token": intent.event_token, "actor": intent.actor})
            )
            with writer._submitting():
                entry_digest = port.execute_fulfilling(plan, intent_digest)
                writer._reconstruct()
            return OperationCommit(record, token, intent_digest, entry_digest)
```

`delete` resolves once under the lock to learn the kind the `require` needs and again inside `prepare`; both reads happen under one hold of the re-entrant lock, so nothing can remove the target between them, and `_prepare_delete` is where `DeletionTargetMissing` is raised in both paths. Add on `CorpusWriter`:

```python
    @property
    def operations(self) -> OperationWrites:
        return OperationWrites(self)

    def _create_or_replace_op(self, record: Node) -> CreateOp | ReplaceOp:
        """The choice `nodes`' `Corpus.add` makes: a live uid replaces."""
        path = self._relative_path(record)
        if record.uid in self._corpus.index.by_uid:
            return ReplaceOp(path=path, content=node_to_markdown(record).encode("utf-8"), expected_digest=self._corpus.manifest[path].sha256)
        return CreateOp(path=path, content=node_to_markdown(record).encode("utf-8"))

    def _replace_op(self, record: Node) -> ReplaceOp:
        path = self._relative_path(record)
        return ReplaceOp(path=path, content=node_to_markdown(record).encode("utf-8"), expected_digest=self._corpus.manifest[path].sha256)

    def _delete_op(self, record: Node) -> DeleteOp:
        from beliefs.world.rules import member_content_digest

        return DeleteOp(path=self._relative_path(record), expected_digest=member_content_digest(node_to_markdown(record).encode("utf-8")))
```

`_prepare_delete` must call `self._authority.require("corpus-write", (node.kind,))` after resolving, exactly as `delete` does today, so `delete`'s inventory row keeps its `require`; `_delete_locked` is unchanged.

`test_permit_boundary.py`: add `"corpus.py:OperationWrites._commit": "corpus-write"` to `WRITE_ENTRY_POINTS`. The static arm 2 requires the `require` to be the first statement — it is. Arm 1 will report `OperationWrites._commit` as a caller of `append_intent` and `execute_fulfilling`; the row satisfies it. Confirm the inventory count is 37.

- [ ] **Step 5: Run the tests and the gates**

`uv run --frozen pytest tests/test_operation_writes.py tests/test_permit_boundary.py tests/test_corpus_write.py tests/test_deletion.py tests/test_coordination_write.py tests/test_relocation.py -q -p no:cacheprovider`, then the whole suite, ruff, pyright, the staleness probe (record any newly stale arm as in Task 4).

- [ ] **Step 6: Commit**

```bash
tasks done <task-5-id> "OperationWrites with seven prepare helpers and one commit seam; PlanRefused; inventory row 37"
git add python/src/beliefs/corpus.py python/tests tasks/
git commit -m "feat(corpus): add the operation seams that commit a write as a corpus-write intent and its fulfillment"
```

---

### Task 6: The ledger — `session/ledger.py`

**Files:**
- Create: `python/src/beliefs/session/__init__.py` (empty for now; Task 7 fills it), `python/src/beliefs/session/ledger.py`
- Test: `python/tests/test_session_ledger.py` (new)

**Interfaces:**
- Consumes: `errors.SessionLedgerFailed`, `errors.LedgerMalformed` (Task 2).
- Produces (`beliefs.session.ledger`): `LINE_KINDS`, `encode_line(obj: Mapping) -> bytes`, `utc_now() -> str`, `ledger_path(operations_root, session_id) -> Path`; `ActLine(invocation, corpus, entry, intent, record_ids)`; `InvocationRecord(invocation, command, input_digest, acts, outcome)`; `LedgerWriter(path)` with `.append(line: Mapping) -> None`, `.failed: bool`, `.close() -> None`; `LedgerReader` with `.session_id`, `.actor`, `.world_id`, `.closed`, `.torn_tail`, `.open_invocations: tuple[str, ...]`, `.acts() -> tuple[ActLine, ...]`, `.invocations() -> tuple[InvocationRecord, ...]`, `.invocation(id) -> InvocationRecord | None`; `open_ledger_reader(operations_root, session_id) -> LedgerReader`; `LedgerMissing(session_id)`, `LedgerEmpty(session_id)`, `LedgerUnreadable(session_id, error)`; `LedgerEvidence = LedgerReader | LedgerMissing | LedgerEmpty | LedgerUnreadable`; `read_ledger_evidence(operations_root, session_id) -> LedgerEvidence`; validation helpers `require_invocation_id(value) -> str`, `require_hex(value, width, what) -> str`, `validated_outcome(outcome) -> dict`.

- [ ] **Step 1: `tasks start <task-6-id>`**

- [ ] **Step 2: Write the failing tests**

Create `tests/test_session_ledger.py`:

```python
"""J7 (and the ledger halves of J6): canonical lines, fsync before index, the
reader's refusals, the torn tail, and the terminal LedgerFailed state."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.session.ledger import (
    LINE_KINDS,
    ActLine,
    LedgerEmpty,
    LedgerMissing,
    LedgerReader,
    LedgerUnreadable,
    LedgerWriter,
    encode_line,
    ledger_path,
    open_ledger_reader,
    read_ledger_evidence,
    validated_outcome,
)

SESSION = "a" * 32
ACTOR = f"session:{SESSION}"
WORLD = "b" * 32
DIGEST = "c" * 64
ENTRY = "d" * 64
INTENT = "e" * 64
AT = "2026-09-05T12:00:00Z"


def open_line():
    return {"line": "session-open", "session": SESSION, "actor": ACTOR, "world": WORLD,
            "permit": {"kinds": ["proposition"], "act_families": ["corpus-write"], "ungoverned": False}, "at": AT}


def lines():
    return [
        open_line(),
        {"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT},
        {"line": "act", "invocation": "A", "corpus": WORLD, "entry": ENTRY, "intent": INTENT, "records": [["u1", "proposition:p1"]]},
        {"line": "invocation-close", "invocation": "A", "outcome": {"done": [["u1", "proposition:p1"]]}},
        {"line": "session-close", "at": AT},
    ]


@pytest.fixture()
def fsyncs(monkeypatch):
    calls = []
    real = os.fsync

    def counting(fd):
        calls.append(fd)
        return real(fd)

    monkeypatch.setattr(os, "fsync", counting)
    return calls


def test_lines_are_canonical_json_one_per_line():
    encoded = encode_line({"z": 1, "a": [1, 2], "line": "act"})
    assert encoded == b'{"a":[1,2],"line":"act","z":1}\n'
    assert set(LINE_KINDS) == {"session-open", "invocation-open", "act", "invocation-close", "session-close"}


def test_each_append_is_fsynced_once_and_lands_before_return(tmp_path, fsyncs):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for index, line in enumerate(lines(), start=1):
        writer.append(line)
        assert len(fsyncs) == index
        assert path.read_bytes().endswith(encode_line(line))
    writer.close()


def test_the_reader_round_trips_every_line(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for line in lines():
        writer.append(line)
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert (reader.session_id, reader.actor, reader.world_id, reader.closed, reader.torn_tail) == (SESSION, ACTOR, WORLD, True, False)
    assert reader.open_invocations == ()
    (record,) = reader.invocations()
    assert record.command == "mint" and record.input_digest == DIGEST
    assert record.acts == (ActLine("A", WORLD, ENTRY, INTENT, (("u1", "proposition:p1"),)),)
    assert record.outcome == {"done": [["u1", "proposition:p1"]]}
    assert reader.invocation("A") is record and reader.invocation("Z") is None


def test_open_invocations_lists_every_unclosed_one_in_order(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())
    for name in ("A", "B", "C"):
        writer.append({"line": "invocation-open", "invocation": name, "command": "mint", "input_digest": DIGEST, "at": AT})
    writer.append({"line": "invocation-close", "invocation": "B", "outcome": {"refusal": {"code": "x", "message": "m", "data": {}}}})
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.open_invocations == ("A", "C") and reader.closed is False


def test_a_torn_tail_is_reported_and_every_complete_line_is_read(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for line in lines()[:3]:
        writer.append(line)
    writer.close()
    with path.open("ab") as handle:
        handle.write(b'{"line":"invocation-close","invoc')
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True and len(reader.acts()) == 1 and reader.open_invocations == ("A",)


@pytest.mark.parametrize(
    "bad, message",
    [
        (b"not json\n", "line 2"),
        (b'{"line":"unknown-kind"}\n', "line 2"),
        (b'{"line":"act","invocation":"A","corpus":"x","entry":"short","intent":"' + b"e" * 64 + b'","records":[]}\n', "line 2"),
    ],
)
def test_a_malformed_interior_line_is_refused_naming_its_number(tmp_path, bad, message):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(encode_line(open_line()) + bad + encode_line({"line": "session-close", "at": AT}))
    with pytest.raises(LedgerMalformed, match=message):
        open_ledger_reader(tmp_path, SESSION)


def test_a_first_line_that_is_not_session_open_is_malformed(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(encode_line({"line": "session-close", "at": AT}))
    with pytest.raises(LedgerMalformed, match="line 1"):
        open_ledger_reader(tmp_path, SESSION)


def test_an_empty_or_missing_ledger_is_not_malformed_to_the_reader_but_is_evidence(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_ledger_reader(tmp_path, SESSION)
    assert read_ledger_evidence(tmp_path, SESSION) == LedgerMissing(SESSION)
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    with pytest.raises(LedgerMalformed):
        open_ledger_reader(tmp_path, SESSION)
    assert read_ledger_evidence(tmp_path, SESSION) == LedgerEmpty(SESSION)
    path.write_bytes(b"garbage\n")
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is LedgerUnreadable and evidence.session_id == SESSION and "line 1" in evidence.error


def test_a_partial_write_ends_the_writer_and_preserves_the_bytes(tmp_path, monkeypatch):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())
    before = path.read_bytes()
    partial = encode_line(lines()[1])[:17]

    def failing_write(data):
        writer._file.buffer.write(partial) if hasattr(writer._file, "buffer") else None
        raise OSError("disk gone")

    monkeypatch.setattr(writer, "_write", failing_write)
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[1])
    assert writer.failed is True
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[2])
    assert path.read_bytes() == before + partial
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True and reader.open_invocations == ()


def test_a_failed_fsync_ends_the_writer(tmp_path, monkeypatch):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())

    def failing(fd):
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", failing)
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[1])
    assert writer.failed is True


def test_validated_outcome_accepts_the_two_shapes_and_nothing_else():
    assert validated_outcome({"done": [["u", "proposition:p"]]}) == {"done": [["u", "proposition:p"]]}
    assert validated_outcome({"refusal": {"code": "c", "message": "m", "data": {"k": 1}}})["refusal"]["code"] == "c"
    for bad in ({}, {"done": [], "refusal": {}}, {"done": [["u"]]}, {"refusal": {"code": 1, "message": "m", "data": {}}}, {"refusal": {"code": "c", "message": "m", "data": []}}, {"other": 1}):
        with pytest.raises(ValueError):
            validated_outcome(bad)
```

The `_write` seam in `test_a_partial_write_ends_the_writer...`: give `LedgerWriter` a private `_write(data: bytes) -> None` that does the raw write, so the test can replace it to simulate a partial write; the test's replacement writes the partial bytes through the underlying binary file and raises. Keep the file handle binary (`open(path, "ab", buffering=0)`), and drop the `hasattr(..., "buffer")` branch — write `writer._file.write(partial)` directly.

- [ ] **Step 3: Run to verify failure**

Run: `uv run --frozen pytest tests/test_session_ledger.py -q -p no:cacheprovider` — FAIL with `ModuleNotFoundError: beliefs.session`.

- [ ] **Step 4: Implement `session/ledger.py`**

```python
"""The session ledger (writer-session design §3.2, §3.5): canonical JSON lines,
appended and fsynced before the index learns them; a reader that refuses a
malformed line and reports a torn tail; and the evidence union reconciliation
takes when a ledger is missing, empty, or unreadable."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeAlias, final

from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.sealed import sealed

__all__ = [
    "LINE_KINDS",
    "ActLine",
    "InvocationRecord",
    "LedgerEmpty",
    "LedgerEvidence",
    "LedgerMissing",
    "LedgerReader",
    "LedgerUnreadable",
    "LedgerWriter",
    "encode_line",
    "ledger_path",
    "open_ledger_reader",
    "read_ledger_evidence",
    "require_hex",
    "require_invocation_id",
    "utc_now",
    "validated_outcome",
]

LINE_KINDS = ("session-open", "invocation-open", "act", "invocation-close", "session-close")
LEDGER_FILE = "ledger.v1"
_INVOCATION = re.compile(r"[A-Za-z0-9_-]{1,64}")
_HEX = "0123456789abcdef"


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def encode_line(line: Mapping[str, object]) -> bytes:
    return (json.dumps(line, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def ledger_path(operations_root: Path, session_id: str) -> Path:
    return Path(operations_root) / "sessions" / session_id / LEDGER_FILE


def require_invocation_id(value: object) -> str:
    if type(value) is not str or _INVOCATION.fullmatch(value) is None:
        raise ValueError(f"invocation id must match [A-Za-z0-9_-]{{1,64}}: {value!r}")
    return value


def require_hex(value: object, width: int, what: str) -> str:
    if type(value) is not str or len(value) != width or any(c not in _HEX for c in value):
        raise ValueError(f"{what} must be {width} lowercase hexadecimal characters")
    return value


def _require_str(value: object, what: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{what} must be a non-empty string")
    return value


def _pairs(value: object, what: str) -> tuple[tuple[str, str], ...]:
    if type(value) is not list or any(
        type(pair) is not list or len(pair) != 2 or any(type(m) is not str or not m for m in pair) for pair in value
    ):
        raise ValueError(f"{what} must be a list of [uid, id] string pairs")
    return tuple((pair[0], pair[1]) for pair in value)


def validated_outcome(outcome: object) -> dict[str, object]:
    """§3.3: exactly `{"done": pairs}` or `{"refusal": {code, message, data}}`."""
    if not isinstance(outcome, Mapping) or len(outcome) != 1:
        raise ValueError("an outcome carries exactly one key, done or refusal")
    if "done" in outcome:
        return {"done": [list(pair) for pair in _pairs(outcome["done"], "a done outcome")]}
    if "refusal" in outcome:
        refusal = outcome["refusal"]
        if not isinstance(refusal, Mapping) or set(refusal) != {"code", "message", "data"}:
            raise ValueError("a refusal outcome carries exactly code, message and data")
        _require_str(refusal["code"], "refusal code")
        if type(refusal["message"]) is not str:
            raise ValueError("refusal message must be a string")
        if not isinstance(refusal["data"], Mapping):
            raise ValueError("refusal data must be a JSON object")
        return {"refusal": {"code": refusal["code"], "message": refusal["message"], "data": dict(refusal["data"])}}
    raise ValueError("an outcome is done or refusal")


@sealed
@final
@dataclass(frozen=True)
class ActLine:
    invocation: str
    corpus: str
    entry: str
    intent: str
    record_ids: tuple[tuple[str, str], ...]


@sealed
@final
@dataclass(frozen=True)
class InvocationRecord:
    invocation: str
    command: str
    input_digest: str
    acts: tuple[ActLine, ...]
    outcome: Mapping[str, object] | None


class LedgerWriter:
    """Append-only; every line is written, flushed and fsynced before the call
    returns, and a failure anywhere in that sequence is terminal (§3.2)."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._file = open(self._path, "ab", buffering=0)  # noqa: SIM115 - held for the session's lifetime
        self._failed = False

    @property
    def failed(self) -> bool:
        return self._failed

    def _write(self, data: bytes) -> None:
        self._file.write(data)

    def append(self, line: Mapping[str, object]) -> None:
        if self._failed:
            raise SessionLedgerFailed("the session ledger failed earlier; nothing further is appended")
        data = encode_line(_validated_line(line, line_number=None))
        try:
            self._write(data)
            self._file.flush()
            os.fsync(self._file.fileno())
        except OSError as caught:
            self._failed = True
            try:
                self._file.close()
            except OSError:
                pass
            raise SessionLedgerFailed(f"ledger append failed: {caught}") from caught

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()


def _validated_line(line: Mapping[str, object], *, line_number: int | None) -> dict[str, object]:
    where = f"line {line_number}" if line_number is not None else "an appended line"
    try:
        if not isinstance(line, Mapping):
            raise ValueError("a ledger line is a JSON object")
        kind = line.get("line")
        if kind not in LINE_KINDS:
            raise ValueError(f"unknown line kind {kind!r}")
        expected = {
            "session-open": {"line", "session", "actor", "world", "permit", "at"},
            "invocation-open": {"line", "invocation", "command", "input_digest", "at"},
            "act": {"line", "invocation", "corpus", "entry", "intent", "records"},
            "invocation-close": {"line", "invocation", "outcome"},
            "session-close": {"line", "at"},
        }[kind]
        if set(line) != expected:
            raise ValueError(f"{kind} carries exactly {sorted(expected)}")
        if kind == "session-open":
            require_hex(line["session"], 32, "session id")
            _require_str(line["actor"], "actor")
            require_hex(line["world"], 32, "world id")
            permit = line["permit"]
            if not isinstance(permit, Mapping) or set(permit) != {"kinds", "act_families", "ungoverned"}:
                raise ValueError("permit summary carries kinds, act_families and ungoverned")
            _require_str(line["at"], "at")
        elif kind == "invocation-open":
            require_invocation_id(line["invocation"])
            _require_str(line["command"], "command")
            require_hex(line["input_digest"], 64, "input digest")
            _require_str(line["at"], "at")
        elif kind == "act":
            require_invocation_id(line["invocation"])
            require_hex(line["corpus"], 32, "corpus id")
            require_hex(line["entry"], 64, "entry digest")
            require_hex(line["intent"], 64, "intent digest")
            _pairs(line["records"], "act records")
        elif kind == "invocation-close":
            require_invocation_id(line["invocation"])
            validated_outcome(line["outcome"])
        else:
            _require_str(line["at"], "at")
    except ValueError as caught:
        raise LedgerMalformed(f"{where}: {caught}") from caught
    return dict(line)


class LedgerReader:
    """One ledger, parsed in full (§3.5)."""

    def __init__(self, session_id: str, lines: list[dict[str, object]], torn_tail: bool) -> None:
        self.session_id = session_id
        self.torn_tail = torn_tail
        head = lines[0]
        self.actor = str(head["actor"])
        self.world_id = str(head["world"])
        self.closed = any(line["line"] == "session-close" for line in lines)
        self._records: dict[str, InvocationRecord] = {}
        self._order: list[str] = []
        acts: dict[str, list[ActLine]] = {}
        for line in lines[1:]:
            kind = line["line"]
            if kind == "invocation-open":
                invocation = str(line["invocation"])
                self._order.append(invocation)
                self._records[invocation] = InvocationRecord(invocation, str(line["command"]), str(line["input_digest"]), (), None)
                acts[invocation] = []
            elif kind == "act":
                invocation = str(line["invocation"])
                acts.setdefault(invocation, []).append(
                    ActLine(invocation, str(line["corpus"]), str(line["entry"]), str(line["intent"]), _pairs(line["records"], "act records"))
                )
            elif kind == "invocation-close":
                invocation = str(line["invocation"])
                current = self._records.get(invocation)
                if current is not None:
                    self._records[invocation] = InvocationRecord(invocation, current.command, current.input_digest, (), validated_outcome(line["outcome"]))
        for invocation, record in list(self._records.items()):
            self._records[invocation] = InvocationRecord(invocation, record.command, record.input_digest, tuple(acts.get(invocation, ())), record.outcome)
        self._stray_acts = tuple(act for invocation, found in acts.items() if invocation not in self._records for act in found)

    @property
    def open_invocations(self) -> tuple[str, ...]:
        return tuple(i for i in self._order if self._records[i].outcome is None)

    def acts(self) -> tuple[ActLine, ...]:
        return tuple(act for i in self._order for act in self._records[i].acts) + self._stray_acts

    def invocations(self) -> tuple[InvocationRecord, ...]:
        return tuple(self._records[i] for i in self._order)

    def invocation(self, invocation_id: str) -> InvocationRecord | None:
        return self._records.get(invocation_id)


def _parse(session_id: str, raw: bytes) -> LedgerReader:
    if not raw:
        raise LedgerMalformed("line 1: the ledger is empty; no session-open")
    torn_tail = not raw.endswith(b"\n")
    chunks = raw.split(b"\n")[:-1]  # the last chunk is empty after a newline, or the torn tail
    lines: list[dict[str, object]] = []
    for number, chunk in enumerate(chunks, start=1):
        try:
            parsed = json.loads(chunk.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as caught:
            raise LedgerMalformed(f"line {number}: not a JSON object: {caught}") from caught
        lines.append(_validated_line(parsed, line_number=number))
    if not lines:
        raise LedgerMalformed("line 1: the ledger is empty; no session-open")
    if lines[0]["line"] != "session-open":
        raise LedgerMalformed("line 1: the first line is not session-open")
    return LedgerReader(session_id, lines, torn_tail)


def open_ledger_reader(operations_root: Path, session_id: str) -> LedgerReader:
    return _parse(session_id, ledger_path(operations_root, session_id).read_bytes())


@sealed
@final
@dataclass(frozen=True)
class LedgerMissing:
    session_id: str


@sealed
@final
@dataclass(frozen=True)
class LedgerEmpty:
    session_id: str


@sealed
@final
@dataclass(frozen=True)
class LedgerUnreadable:
    session_id: str
    error: str


LedgerEvidence: TypeAlias = LedgerReader | LedgerMissing | LedgerEmpty | LedgerUnreadable


def read_ledger_evidence(operations_root: Path, session_id: str) -> LedgerEvidence:
    """Reconciliation's input (§6, decision 14): never raises on ledger state."""
    path = ledger_path(operations_root, session_id)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return LedgerMissing(session_id)
    if not raw:
        return LedgerEmpty(session_id)
    try:
        return _parse(session_id, raw)
    except LedgerMalformed as caught:
        return LedgerUnreadable(session_id, str(caught))
```

Create `session/__init__.py` with only a module docstring for now.

- [ ] **Step 5: Run the tests and gates**

`uv run --frozen pytest tests/test_session_ledger.py -q -p no:cacheprovider`, then the three gates. `test_capability_boundary.py` must still pass: the new module imports only stdlib and `beliefs.errors`/`beliefs.sealed`.

- [ ] **Step 6: Commit**

```bash
tasks done <task-6-id> "session ledger: canonical lines, fsync-before-index writer, refusing reader, evidence union"
git add python/src/beliefs/session python/tests/test_session_ledger.py tasks/
git commit -m "feat(session): add the append-then-fsync session ledger and its reader"
```

---

### Task 7: The session and the scoped writer — `session/writer.py`, the composition's `open_attended_session`

**Files:**
- Create: `python/src/beliefs/session/writer.py`
- Modify: `python/src/beliefs/session/__init__.py` (`open_attended_session` and the re-exports; `reconcile_sessions` arrives in Task 8 — until then open runs no reconciliation and `findings` is `()`)
- Test: `python/tests/test_session_writer.py` (new)

**Interfaces:**
- Consumes: Task 6's ledger; `CorpusWriter.operations`, `OperationCommit` (Task 5); `permit_covers`, `Authority`, `WritePermit`, `RequiredCapabilities`, `PermitExceeded`, `PermitFact` (permit.py, errors.py); `root.durable_operation_port`, `root.log_seam`, `root.durable_executor_factory` (Task 3); `CoordinationResolver`, `_operation_lock_for` (corpus.py).
- Produces (`beliefs.session.writer`): `ClaimFresh`, `ClaimDone(outcome)`, `ClaimOpen`, `ClaimMismatch`, `Claim`; `KernelRefusalValue(value)` with `.value`; `WriterSession(*, session_id, actor, world_id, corpus_root, corpus_id, operations_root, ledger, writer_factory, findings=())` with `.session_id`, `.actor`, `.operations_root`, `.findings`, `.current_invocation`, `.scoped(required, invocation_id) -> ScopedWriter`, `.claim_invocation(id, command, digest) -> Claim`, `.close_invocation(id, outcome) -> None`, `.invocation_acts(id) -> tuple[ActLine, ...]`, `.close() -> None`; `ScopedWriter` with `.invocation_id` and the seven methods. (`beliefs.session`): `open_attended_session(world_config, operations_root, *, coordination=None) -> WriterSession` and re-exports of everything the contract names.

- [ ] **Step 1: `tasks start <task-7-id>`**

- [ ] **Step 2: Write the failing tests**

Create `tests/test_session_writer.py`:

```python
"""J3, J6 and J11 portably: a WriterSession built from parts over the in-memory
executor and a synthetic-digest port (design §13 item 2)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from authority import FULL
from nodes.core.write_plan import DefaultExecutor
from test_operation_writes import RecordingPort, proposition

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import PermitExceeded, PermitFact, PlanRefused, SessionClosed, SessionLedgerFailed, SessionProtocolError
from beliefs.permit import Authority, RequiredCapabilities, WritePermit
from beliefs.session import (
    ClaimDone,
    ClaimFresh,
    ClaimMismatch,
    ClaimOpen,
    KernelRefusalValue,
    ScopedWriter,
    WriterSession,
    open_ledger_reader,
)
from beliefs.session.ledger import LedgerWriter, ledger_path
from beliefs.world.records import RECORD_CEILING

SESSION = "a" * 32
WORLD = "b" * 32
CORPUS = "c" * 32
DIGEST = "d" * 64


def make_session(tmp_path: Path, ceiling: WritePermit = WritePermit.full()) -> tuple[WriterSession, list[RecordingPort]]:
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    operations_root = tmp_path / "ops"
    path = ledger_path(operations_root, SESSION)
    path.parent.mkdir(parents=True)
    ports: list[RecordingPort] = []

    def writer_factory(authority: Authority) -> CorpusWriter:
        port = RecordingPort(authority)
        port.root = corpus_root
        ports.append(port)
        return CorpusWriter(corpus_root, DefaultExecutor, authority=authority, operation_port=port)

    ledger = LedgerWriter(path)
    session = WriterSession(
        session_id=SESSION, actor=f"session:{SESSION}", world_id=WORLD, corpus_root=corpus_root, corpus_id=CORPUS,
        operations_root=operations_root, ledger=ledger, writer_factory=writer_factory, ceiling=ceiling,
    )
    return session, ports


PROPOSITIONS = RequiredCapabilities.for_kinds({"proposition"}, {})


# --- J6: the claim table ---------------------------------------------------------
def test_the_claim_table(tmp_path):
    session, _ = make_session(tmp_path)
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimFresh
    assert session.current_invocation == "A"
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimOpen
    assert type(session.claim_invocation("A", "mint", "e" * 64)) is ClaimMismatch
    assert type(session.claim_invocation("A", "other", DIGEST)) is ClaimMismatch
    session.close_invocation("A", {"done": [["u1", "proposition:p1"]]})
    done = session.claim_invocation("A", "mint", DIGEST)
    assert type(done) is ClaimDone and done.outcome == {"done": [["u1", "proposition:p1"]]}
    assert type(session.claim_invocation("A", "mint", "e" * 64)) is ClaimMismatch
    assert session.current_invocation is None


def test_a_refusal_outcome_replays_whole(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("F", "over", DIGEST)
    envelope = {"refusal": {"code": "permit-exceeded", "message": "kind source", "data": {"requirement": "kind source"}}}
    session.close_invocation("F", envelope)
    assert session.claim_invocation("F", "over", DIGEST).outcome == envelope


def test_an_abandoned_invocation_stays_open_and_never_blocks_a_fresh_claim(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    assert type(session.claim_invocation("B", "mint", DIGEST)) is ClaimFresh
    assert session.current_invocation == "B"
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimOpen
    with pytest.raises(SessionProtocolError):
        session.close_invocation("A", {"done": []})
    session.close_invocation("B", {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert reader.open_invocations == ("A",)


def test_a_malformed_outcome_is_refused_and_the_invocation_stays_current(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(ValueError):
        session.close_invocation("A", {"done": [["u"]]})
    assert session.current_invocation == "A"


def test_claims_are_validated(tmp_path):
    session, _ = make_session(tmp_path)
    for bad in [("bad id!", "mint", DIGEST), ("A", "", DIGEST), ("A", "mint", "short")]:
        with pytest.raises(ValueError):
            session.claim_invocation(*bad)


def test_eight_threads_claiming_one_fresh_id_under_a_lock_see_one_fresh(tmp_path):
    session, _ = make_session(tmp_path)
    lock = threading.Lock()
    results = []

    def go():
        with lock:
            claim = session.claim_invocation("C", "mint", DIGEST)
            if type(claim) is ClaimFresh:
                session.close_invocation("C", {"done": []})
            results.append(type(claim))

    threads = [threading.Thread(target=go) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(ClaimFresh) == 1 and results.count(ClaimDone) == 7


# --- J3: scoped is a real writer bound to the requirement -----------------------
def test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists(tmp_path):
    session, ports = make_session(tmp_path, ceiling=WritePermit(frozenset({"source"}), frozenset({"corpus-write"})))
    with pytest.raises(PermitExceeded) as caught:
        session.scoped(PROPOSITIONS, "A")
    assert caught.value.requirement == PermitFact("kind", "proposition")
    assert caught.value.capability.kinds == ("source",)
    assert ports == []


def test_the_act_time_refusal_comes_from_the_kernel_with_the_requirements_summary(tmp_path):
    session, _ = make_session(tmp_path)
    writer = session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(PermitExceeded) as caught:
        writer.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s1"}))
    assert caught.value.capability.kinds == ("proposition",)
    assert session.invocation_acts("A") == ()


def test_scoped_type_checks_its_arguments(tmp_path):
    session, _ = make_session(tmp_path)
    with pytest.raises(TypeError):
        session.scoped(WritePermit.full(), "A")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        session.scoped(PROPOSITIONS, "not valid!")


# --- J11: bound to one invocation -----------------------------------------------
def test_a_scoped_writer_acts_only_under_its_own_current_invocation(tmp_path):
    session, _ = make_session(tmp_path)
    a = session.scoped(PROPOSITIONS, "A")
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p0"))
    session.claim_invocation("A", "mint", DIGEST)
    node = a.add(proposition("p1"))
    assert node.id == "proposition:p1"
    (act,) = session.invocation_acts("A")
    assert act.record_ids == ((node.uid, node.id),) and act.corpus == CORPUS
    session.close_invocation("A", {"done": [[node.uid, node.id]]})
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p2"))
    b = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "B")
    session.claim_invocation("B", "mint", DIGEST)
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p3"))
    assert session.invocation_acts("B") == ()
    assert b.add(proposition("p3")).id == "proposition:p3"
    session.claim_invocation("C", "mint", DIGEST)  # B abandoned
    with pytest.raises(SessionProtocolError):
        b.add(proposition("p4"))


def test_two_writers_scoped_for_one_id_both_act_under_that_id(tmp_path):
    session, _ = make_session(tmp_path)
    one, two = session.scoped(PROPOSITIONS, "A"), session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    one.add(proposition("p1"))
    two.add(proposition("p2"))
    assert [act.invocation for act in session.invocation_acts("A")] == ["A", "A"]


def test_delete_ledgers_an_empty_record_list(tmp_path):
    session, _ = make_session(tmp_path)
    w = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "A")
    session.claim_invocation("A", "mint", DIGEST)
    w.add(proposition("p1"))
    assert w.delete("proposition:p1") is None
    assert session.invocation_acts("A")[-1].record_ids == ()


def test_the_scoped_writer_exposes_only_the_seven_methods_and_its_invocation(tmp_path):
    public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
    assert public == {"add", "retract", "supersede", "revise", "delete", "mint_coordination", "revise_coordination", "invocation_id"}


# --- refusal shapes -----------------------------------------------------------------
def test_an_over_ceiling_record_through_the_scoped_writer_is_plan_refused(tmp_path):
    session, _ = make_session(tmp_path)
    w = session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(PlanRefused):
        w.add(proposition("p1").model_copy(update={"body": "x" * (RECORD_CEILING + 1)}))
    assert session.invocation_acts("A") == ()


def test_kernel_refusal_value_wraps_a_value_and_exposes_it():
    class Refusal:
        reason = "recipe-mismatch"

    value = Refusal()
    caught = KernelRefusalValue(value)
    assert caught.value is value and "recipe-mismatch" in str(caught)


# --- J9 lifecycle, portable half -----------------------------------------------------
def test_close_is_idempotent_and_every_later_call_is_session_closed(tmp_path):
    session, _ = make_session(tmp_path)
    session.close()
    session.close()
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert reader.closed is True
    for call in (
        lambda: session.scoped(PROPOSITIONS, "A"),
        lambda: session.claim_invocation("A", "mint", DIGEST),
        lambda: session.close_invocation("A", {"done": []}),
        lambda: session.invocation_acts("A"),
    ):
        with pytest.raises(SessionClosed):
            call()


def test_a_ledger_failure_ends_the_session(tmp_path, monkeypatch):
    import os

    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    monkeypatch.setattr(os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("gone")))
    with pytest.raises(SessionLedgerFailed):
        session.close_invocation("A", {"done": []})
    monkeypatch.undo()
    for call in (
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.scoped(PROPOSITIONS, "B"),
        lambda: session.invocation_acts("A"),
        session.close,
    ):
        with pytest.raises(SessionLedgerFailed):
            call()
    assert session.current_invocation == "A"  # the index never learned the close
```

The session's `session-open` line must be written by the caller of the constructor in production (`open_attended_session`); for the portable tests the constructor writes it itself when the ledger is empty — decide once: **the constructor writes `session-open`**, and `open_attended_session` therefore does not. Record this in §13 as item 8.

- [ ] **Step 3: Run to verify failure**

`uv run --frozen pytest tests/test_session_writer.py -q -p no:cacheprovider` — FAIL with `ImportError`.

- [ ] **Step 4: Implement `session/writer.py`**

```python
"""The attended writer session and its invocation-bound scoped writer
(writer-session design §3, §5)."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, final

from nodes.core.node import Node

from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CorpusWriter, Finding, OperationCommit, _operation_lock_for
from beliefs.errors import PermitExceeded, PermitFact, SessionClosed, SessionLedgerFailed, SessionProtocolError
from beliefs.permit import Authority, RequiredCapabilities, WritePermit, permit_covers
from beliefs.sealed import sealed
from beliefs.session.ledger import (
    ActLine,
    LedgerWriter,
    require_hex,
    require_invocation_id,
    utc_now,
    validated_outcome,
)

__all__ = [
    "Claim",
    "ClaimDone",
    "ClaimFresh",
    "ClaimMismatch",
    "ClaimOpen",
    "KernelRefusalValue",
    "ScopedWriter",
    "WriterSession",
]


@sealed
@final
@dataclass(frozen=True)
class ClaimFresh:
    pass


@sealed
@final
@dataclass(frozen=True)
class ClaimDone:
    outcome: Mapping[str, object]


@sealed
@final
@dataclass(frozen=True)
class ClaimOpen:
    pass


@sealed
@final
@dataclass(frozen=True)
class ClaimMismatch:
    pass


Claim: TypeAlias = ClaimFresh | ClaimDone | ClaimOpen | ClaimMismatch


class KernelRefusalValue(Exception):
    """A value-style kernel refusal carried as an exception so the dispatcher has
    one normalization path (design §5). Unraised by this slice's seven methods."""

    def __init__(self, value: object) -> None:
        super().__init__(str(getattr(value, "reason", repr(value))))
        self.value = value


@dataclass
class _Invocation:
    command: str
    input_digest: str
    acts: list[ActLine]
    outcome: Mapping[str, object] | None


class WriterSession:
    """The trusted server-side object (design §3.1). Holds the ceiling, the
    ledger and the index; constructs no writer of its own."""

    def __init__(
        self,
        *,
        session_id: str,
        actor: str,
        world_id: str,
        corpus_root: Path,
        corpus_id: str,
        operations_root: Path,
        ledger: LedgerWriter,
        writer_factory: Callable[[Authority], CorpusWriter],
        findings: tuple[Finding, ...] = (),
        ceiling: WritePermit | None = None,
    ) -> None:
        self.session_id = require_hex(session_id, 32, "session id")
        self.actor = actor
        self.world_id = require_hex(world_id, 32, "world id")
        self.corpus_root = Path(corpus_root)
        self.corpus_id = require_hex(corpus_id, 32, "corpus id")
        self.operations_root = Path(operations_root)
        self.findings = findings
        self._ledger = ledger
        self._writer_factory = writer_factory
        self._ceiling = WritePermit.full() if ceiling is None else ceiling
        self._lock = threading.Lock()
        self._index: dict[str, _Invocation] = {}
        self._current: str | None = None
        self._closed = False
        self._ledger.append(
            {
                "line": "session-open",
                "session": self.session_id,
                "actor": self.actor,
                "world": self.world_id,
                "permit": {
                    "kinds": list(self._ceiling.summary().kinds),
                    "act_families": list(self._ceiling.summary().act_families),
                    "ungoverned": self._ceiling.ungoverned,
                },
                "at": utc_now(),
            }
        )

    # --- liveness -------------------------------------------------------------
    def _require_live(self) -> None:
        if self._ledger.failed:
            raise SessionLedgerFailed("the session ledger failed; this session is terminal")
        if self._closed:
            raise SessionClosed("the session is closed")

    @property
    def current_invocation(self) -> str | None:
        return self._current

    # --- the scoped writer -----------------------------------------------------
    def scoped(self, required: RequiredCapabilities, invocation_id: str) -> ScopedWriter:
        if type(required) is not RequiredCapabilities:
            raise TypeError("scoped judges a RequiredCapabilities")
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
        if not permit_covers(self._ceiling, required):
            summary = self._ceiling.summary()
            missing_family = sorted(required.permit.act_families - self._ceiling.act_families)
            if missing_family:
                raise PermitExceeded(PermitFact("family", missing_family[0]), summary)
            missing_kind = sorted(required.permit.kinds - self._ceiling.kinds)
            raise PermitExceeded(PermitFact("kind", missing_kind[0]), summary)
        writer = self._writer_factory(Authority(required.permit, self.actor))
        return ScopedWriter(self, writer, invocation)

    # --- claims ------------------------------------------------------------------
    def claim_invocation(self, invocation_id: str, command: str, input_digest: str) -> Claim:
        invocation = require_invocation_id(invocation_id)
        if type(command) is not str or not command:
            raise ValueError("command must be a non-empty string")
        digest = require_hex(input_digest, 64, "input digest")
        with self._lock:
            self._require_live()
            entry = self._index.get(invocation)
            if entry is None:
                self._ledger.append(
                    {"line": "invocation-open", "invocation": invocation, "command": command, "input_digest": digest, "at": utc_now()}
                )
                self._index[invocation] = _Invocation(command, digest, [], None)
                self._current = invocation
                return ClaimFresh()
            if entry.command != command or entry.input_digest != digest:
                return ClaimMismatch()
            if entry.outcome is None:
                return ClaimOpen()
            return ClaimDone(entry.outcome)

    def close_invocation(self, invocation_id: str, outcome: Mapping[str, object]) -> None:
        invocation = require_invocation_id(invocation_id)
        validated = validated_outcome(outcome)
        with self._lock:
            self._require_live()
            if invocation != self._current:
                raise SessionProtocolError(f"{invocation} is not the current invocation ({self._current})")
            self._ledger.append({"line": "invocation-close", "invocation": invocation, "outcome": validated})
            self._index[invocation].outcome = validated
            self._current = None

    def invocation_acts(self, invocation_id: str) -> tuple[ActLine, ...]:
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
            entry = self._index.get(invocation)
            return () if entry is None else tuple(entry.acts)

    def _require_current(self, invocation: str) -> None:
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise SessionProtocolError(f"writer bound to {invocation} cannot act; current invocation is {self._current}")

    def _record_act(self, invocation: str, commit: OperationCommit) -> None:
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise SessionProtocolError(f"invocation {invocation} is no longer current")
            records = [] if commit.record is None else [[commit.record.uid, commit.record.id]]
            self._ledger.append(
                {
                    "line": "act",
                    "invocation": invocation,
                    "corpus": self.corpus_id,
                    "entry": commit.entry_digest,
                    "intent": commit.intent_digest,
                    "records": records,
                }
            )
            self._index[invocation].acts.append(
                ActLine(invocation, self.corpus_id, commit.entry_digest, commit.intent_digest, tuple((r[0], r[1]) for r in records))
            )

    # --- close -----------------------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            if self._ledger.failed:
                raise SessionLedgerFailed("the session ledger failed; this session is terminal")
            if self._closed:
                return
            self._ledger.append({"line": "session-close", "at": utc_now()})
            self._closed = True
            self._ledger.close()


class ScopedWriter:
    """The facade a handler holds (design §5): seven methods, one invocation."""

    __slots__ = ("_invocation", "_session", "_writer")

    def __init__(self, session: WriterSession, writer: CorpusWriter, invocation_id: str) -> None:
        self._session = session
        self._writer = writer
        self._invocation = invocation_id

    @property
    def invocation_id(self) -> str:
        return self._invocation

    def _act(self, perform: Callable[[], OperationCommit]) -> Node | None:
        with _operation_lock_for(self._writer.root):
            self._session._require_current(self._invocation)
            commit = perform()
            self._session._record_act(self._invocation, commit)
            return commit.record

    def add(self, node: Node) -> Node:
        record = self._act(lambda: self._writer.operations.add(node))
        assert record is not None
        return record

    def retract(self, record: Node) -> Node:
        minted = self._act(lambda: self._writer.operations.retract(record))
        assert minted is not None
        return minted

    def supersede(self, successor: Node, *, of: str) -> Node:
        minted = self._act(lambda: self._writer.operations.supersede(successor, of=of))
        assert minted is not None
        return minted

    def revise(self, node: Node) -> Node:
        minted = self._act(lambda: self._writer.operations.revise(node))
        assert minted is not None
        return minted

    def delete(self, ref: str) -> None:
        self._act(lambda: self._writer.operations.delete(ref))

    def mint_coordination(self, kind: str, *, project: CoordinationAddress | None = None, content: Mapping[str, object]) -> Node:
        minted = self._act(lambda: self._writer.operations.mint_coordination(kind, project=project, content=content))
        assert minted is not None
        return minted

    def revise_coordination(self, kind: str, address: CoordinationAddress, *, predecessors: Sequence[str], content: Mapping[str, object]) -> Node:
        minted = self._act(lambda: self._writer.operations.revise_coordination(kind, address, predecessors=predecessors, content=content))
        assert minted is not None
        return minted
```

Note the test `test_a_ledger_failure_ends_the_session` monkeypatches `os.fsync` module-wide; the ledger's `append` catches `OSError`. The `_operation_lock_for(self._writer.root)` in `_act` is the same lock object `_commit` nests in (re-entrant per thread), so the `act` line is appended before the lock releases (decision 11).

`session/__init__.py`:

```python
"""The writer session (writer-session design): the contract's names, and the
two compositions over `beliefs.root`."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import ManifestMalformed, ManifestMissing, SessionRefused
from beliefs.permit import Authority
from beliefs.profile import ProfileSpec
from beliefs.root import durable_executor_factory, durable_operation_port, log_seam
from beliefs.session.ledger import (
    ActLine,
    InvocationRecord,
    LedgerReader,
    LedgerWriter,
    ledger_path,
    open_ledger_reader,
)
from beliefs.session.writer import (
    Claim,
    ClaimDone,
    ClaimFresh,
    ClaimMismatch,
    ClaimOpen,
    KernelRefusalValue,
    ScopedWriter,
    WriterSession,
)
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.logmodel import WellFormedView

__all__ = [
    "ActLine", "Claim", "ClaimDone", "ClaimFresh", "ClaimMismatch", "ClaimOpen", "InvocationRecord",
    "KernelRefusalValue", "LedgerReader", "ScopedWriter", "WriterSession", "open_attended_session",
    "open_ledger_reader", "reconcile_sessions",
]


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def open_attended_session(
    world_config: WorldConfig, operations_root: Path, *, coordination: ProfileSpec | None = None
) -> WriterSession:
    """The interactive constructor (design §3.1): full permit by construction."""
    if type(world_config) is not WorldConfig:
        raise TypeError("open_attended_session takes an exact WorldConfig")
    if not isinstance(operations_root, Path):
        raise TypeError("operations_root must be a Path")
    if coordination is not None and not isinstance(coordination, ProfileSpec):
        raise TypeError("coordination must be a compiled ProfileSpec")
    if len(world_config.corpus_roots) != 1:
        raise SessionRefused(f"a session needs exactly one corpus root; the config names {len(world_config.corpus_roots)}")
    (root,) = world_config.corpus_roots
    try:
        corpus_id = load_manifest(root).corpus_id
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"{root}: the corpus is not adopted: {caught}") from caught
    view = log_seam().inspect_detached(root)
    if type(view) is not WellFormedView:
        raise SessionRefused(f"{root}: the chain is {type(view).__name__}; a session opens over a registered, well-formed root")
    resolver = CoordinationResolver({root: coordination}) if coordination is not None else None

    session_id = secrets.token_hex(16)
    path = ledger_path(operations_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=False)
    _fsync_directory(path.parent.parent)
    ledger = LedgerWriter(path)

    def writer_factory(authority: Authority) -> CorpusWriter:
        return CorpusWriter(
            root,
            durable_executor_factory(),
            authority=authority,
            operation_port=durable_operation_port(root, authority),
            coordination_resolver=resolver,
        )

    session = WriterSession(
        session_id=session_id,
        actor=f"session:{session_id}",
        world_id=world_config.world_id,
        corpus_root=root,
        corpus_id=corpus_id,
        operations_root=operations_root,
        ledger=ledger,
        writer_factory=writer_factory,
    )
    # §3.1: session-open is written (by the constructor) before reconciliation runs.
    session.findings = reconcile_sessions(world_config, operations_root, exclude=session_id)
    return session


def reconcile_sessions(world_config: WorldConfig, operations_root: Path, *, exclude: str | None = None):
    """Task 8 supplies the body; until then, no prior session is read."""
    return ()
```

`WriterSession.__init__` writes `session-open` (§13 item 8, added by this task: "the constructor writes `session-open`; the composition writes nothing before it"), so `open_attended_session` constructs the session first and assigns `findings` after reconciliation. `findings` is a plain attribute.

- [ ] **Step 5: Run the tests and gates**

`uv run --frozen pytest tests/test_session_writer.py tests/test_session_ledger.py -q -p no:cacheprovider`; whole suite; ruff; pyright; `test_capability_boundary.py` (only `session/__init__.py` imports `beliefs.root`).

- [ ] **Step 6: Commit**

```bash
tasks done <task-7-id> "WriterSession and ScopedWriter; claim protocol; open_attended_session composition"
git add python/src/beliefs/session python/tests/test_session_writer.py docs/designs/2026-09-05-writer-session-design.md tasks/
git commit -m "feat(session): add the attended writer session and the invocation-bound scoped writer"
```

---

### Task 8: Reconciliation — `session/reconcile.py` and `reconcile_sessions`

**Files:**
- Create: `python/src/beliefs/session/reconcile.py`
- Modify: `python/src/beliefs/session/__init__.py` (`reconcile_sessions` body; export `reconcile`)
- Test: `python/tests/test_session_reconcile.py` (new)

**Interfaces:**
- Consumes: `LedgerEvidence`, `read_ledger_evidence` (Task 6); `ChainView` types (`world/logmodel.py`); `decode_intent` (`intents/shapes.py`); `Finding` (`corpus.py`); `log_seam().inspect_detached`, `_operation_lock_for`, `load_manifest`.
- Produces: `beliefs.session.reconcile.reconcile(ledgers: Sequence[LedgerEvidence], chains: Mapping[str, ChainView]) -> tuple[Finding, ...]`; `beliefs.session.reconcile_sessions(world_config, operations_root, *, exclude=None) -> tuple[Finding, ...]`; the finding codes of design §6.

- [ ] **Step 1: `tasks start <task-8-id>`**

- [ ] **Step 2: Write the failing tests**

Create `tests/test_session_reconcile.py`:

```python
"""J8 portably: every intent, chain and ledger state of design §6 over stand-in
views and ledger evidence."""

from __future__ import annotations

import pytest

from beliefs.identity import v1
from beliefs.session.ledger import LedgerEmpty, LedgerMissing, LedgerReader, LedgerUnreadable, encode_line
from beliefs.session.ledger import _parse as parse_ledger
from beliefs.session.reconcile import reconcile
from beliefs.world.logmodel import (
    AbsentView,
    DefectView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

S1 = "1" * 32
CORPUS = "c" * 32
AT = "2026-09-05T12:00:00Z"


def intent(digest: str, session: str = S1, kind: str = "corpus-write") -> IntentEntryView:
    return IntentEntryView(digest=digest, payload=v1.encode({"kind": kind, "event_token": "tok-" + digest[:4], "actor": f"session:{session}"}))


def registration(digest: str, fulfills: str) -> RegisteredEntryView:
    return RegisteredEntryView(digest=digest, txid="t" + digest[:4], initial=(), final=(), fulfills=fulfills)


def settled(registration_digest: str, committed: bool) -> SettledEntryView:
    return SettledEntryView(digest="s" + registration_digest[1:], txid="t", registration=registration_digest, committed=committed)


def genesis() -> GenesisEntryView:
    return GenesisEntryView(digest="g" * 64, payload=b"", baseline=())


def view(*entries, pending=()) -> WellFormedView:
    return WellFormedView(genesis=genesis(), entries=(genesis(), *entries), tip=entries[-1].digest if entries else "g" * 64, pending=tuple(pending))


def ledger(session: str = S1, *, opens=(), closes=(), acts=(), closed=True) -> LedgerReader:
    lines = [{"line": "session-open", "session": session, "actor": f"session:{session}", "world": "w" * 32,
              "permit": {"kinds": [], "act_families": [], "ungoverned": True}, "at": AT}]
    for invocation in opens:
        lines.append({"line": "invocation-open", "invocation": invocation, "command": "mint", "input_digest": "d" * 64, "at": AT})
    for invocation, entry, intent_digest in acts:
        lines.append({"line": "act", "invocation": invocation, "corpus": CORPUS, "entry": entry, "intent": intent_digest, "records": []})
    for invocation in closes:
        lines.append({"line": "invocation-close", "invocation": invocation, "outcome": {"done": []}})
    if closed:
        lines.append({"line": "session-close", "at": AT})
    return parse_ledger(session, b"".join(encode_line(line) for line in lines))


def codes(findings):
    return [(f.code, f.severity, f.ref) for f in findings]


I, R = "i" * 64, "r" * 64


def test_a_covered_registration_yields_nothing():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains) == ()


def test_uncovered_committed_registration_under_an_open_invocation_is_outcome_unknown():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    findings = reconcile([ledger(opens=("A", "B"), closes=("B",), closed=False)], chains)
    assert ("session-outcome-unknown", "warning", R) in codes(findings)
    unknown = next(f for f in findings if f.code == "session-outcome-unknown")
    assert "invocations=['A']" in unknown.detail and f"intent={I}" in unknown.detail
    assert ("session-unclosed", "warning", S1) in codes(findings)


def test_uncovered_committed_registration_with_no_open_invocation_is_foreign():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    assert codes(reconcile([ledger()], chains)) == [("session-entry-foreign", "error", R)]


def test_an_unsettled_registration_is_pending():
    chains = {CORPUS: view(intent(I), registration(R, I))}
    assert codes(reconcile([ledger()], chains)) == [("session-entry-pending", "warning", R)]


def test_a_rolled_back_registration_is_no_registration():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, False))}
    assert codes(reconcile([ledger()], chains)) == [("session-intent-unclaimed", "error", I)]


def test_an_intent_with_no_registration_under_an_open_invocation_is_outcome_unknown():
    chains = {CORPUS: view(intent(I))}
    assert codes(reconcile([ledger(opens=("A",), closed=False)], chains))[0] == ("session-outcome-unknown", "warning", I)


def test_an_unknown_session_actor_is_reported():
    chains = {CORPUS: view(intent(I, session="9" * 32))}
    assert codes(reconcile([ledger()], chains)) == [("session-unknown", "error", I)]


def test_an_ordinary_actor_is_never_classified():
    payload = v1.encode({"kind": "corpus-write", "event_token": "t", "actor": "test-actor"})
    chains = {CORPUS: view(IntentEntryView(digest=I, payload=payload))}
    assert reconcile([ledger()], chains) == ()


@pytest.mark.parametrize("evidence, code, severity", [
    (LedgerMissing(S1), "session-ledger-missing", "warning"),
    (LedgerEmpty(S1), "session-ledger-empty", "warning"),
    (LedgerUnreadable(S1, "line 3: bad"), "session-ledger-malformed", "error"),
])
def test_unreadable_ledgers_are_findings_and_their_intents_read_outcome_unknown(evidence, code, severity):
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    found = codes(reconcile([evidence], chains))
    assert (code, severity, S1) in found and ("session-outcome-unknown", "warning", R) in found


def test_a_torn_tail_is_reported():
    torn = parse_ledger(S1, encode_line({"line": "session-open", "session": S1, "actor": f"session:{S1}", "world": "w" * 32,
                                          "permit": {"kinds": [], "act_families": [], "ungoverned": True}, "at": AT}) + b'{"line":"inv')
    assert ("ledger-torn-tail", "warning", S1) in codes(reconcile([torn], {CORPUS: view()}))


def test_an_act_line_the_chain_does_not_hold_is_unverified():
    chains = {CORPUS: view(intent(I))}
    findings = reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains)
    assert ("session-act-unverified", "error", R) in codes(findings)


def test_the_views_pending_pairs_absent_from_entries_are_reported_without_an_intent():
    staged = "e" * 64
    chains = {CORPUS: view(intent(I), pending=(("txid-1", staged),))}
    found = reconcile([ledger()], chains)
    pending = next(f for f in found if f.code == "session-chain-pending")
    assert pending.ref == staged and "txid-1" in pending.detail and "intent" not in pending.detail


def test_absent_and_malformed_views_classify_nothing():
    found = reconcile([ledger()], {CORPUS: AbsentView(), "d" * 32: MalformedView(DefectView(kind="foreign-leaf", subject="x", detail="y"))})
    assert codes(found) == [("session-chain-absent", "error", CORPUS), ("session-chain-malformed", "error", "d" * 32)]


def test_results_are_deterministic():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True), intent("j" * 64))}
    ledgers = [ledger(opens=("A",), closed=False), LedgerMissing("2" * 32)]
    assert reconcile(ledgers, chains) == reconcile(list(reversed(ledgers)), dict(chains))
```

Confirm the `DefectView` constructor's field names in `logmodel.py` and the finding for a malformed view uses the defect's `kind` and `detail`.

- [ ] **Step 3: Run to verify failure**

`uv run --frozen pytest tests/test_session_reconcile.py -q -p no:cacheprovider` — FAIL with `ImportError`.

- [ ] **Step 4: Implement `session/reconcile.py`**

```python
"""Reconciliation (writer-session design §6): chains are truth, the ledger is
evidence. A pure classification over ledger evidence and detached chain views;
it writes nothing, recovers nothing, and never raises on ledger state."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from beliefs.corpus import Finding
from beliefs.intents import shapes
from beliefs.report import OperationIntent
from beliefs.session.ledger import LedgerEmpty, LedgerEvidence, LedgerMissing, LedgerReader, LedgerUnreadable
from beliefs.world.logmodel import (
    AbsentView,
    ChainView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

__all__ = ["reconcile"]

_SESSION_ACTOR = re.compile(r"session:([0-9a-f]{32})")


def _finding(severity: str, code: str, ref: str, detail: str, message: str) -> Finding:
    return Finding(severity=severity, code=code, ref=ref, detail=detail, message=message)


def reconcile(ledgers: Sequence[LedgerEvidence], chains: Mapping[str, ChainView]) -> tuple[Finding, ...]:
    by_session: dict[str, LedgerEvidence] = {evidence.session_id: evidence for evidence in ledgers}
    keyed: list[tuple[tuple[str, int, str, str], Finding]] = []

    # --- ledger-level evidence ---------------------------------------------------
    for evidence in ledgers:
        sid = evidence.session_id
        if type(evidence) is LedgerMissing:
            keyed.append((("", 0, "session-ledger-missing", sid), _finding("warning", "session-ledger-missing", sid, "", "a session directory with no ledger file: creation was interrupted")))
        elif type(evidence) is LedgerEmpty:
            keyed.append((("", 0, "session-ledger-empty", sid), _finding("warning", "session-ledger-empty", sid, "", "an empty ledger: the session-open line never landed")))
        elif type(evidence) is LedgerUnreadable:
            keyed.append((("", 0, "session-ledger-malformed", sid), _finding("error", "session-ledger-malformed", sid, evidence.error, "the ledger reader refused this ledger")))
        else:
            assert type(evidence) is LedgerReader
            if not evidence.closed:
                keyed.append((("", 0, "session-unclosed", sid), _finding("warning", "session-unclosed", sid, f"open_invocations={list(evidence.open_invocations)}", "a ledger with no session-close")))
            if evidence.torn_tail:
                keyed.append((("", 0, "ledger-torn-tail", sid), _finding("warning", "ledger-torn-tail", sid, "", "the ledger ends mid-line: the last append was interrupted")))

    committed_everywhere: set[str] = set()

    # --- per corpus -------------------------------------------------------------------
    for corpus_id in sorted(chains):
        view = chains[corpus_id]
        if type(view) is AbsentView:
            keyed.append(((corpus_id, 0, "session-chain-absent", corpus_id), _finding("error", "session-chain-absent", corpus_id, "", "no durable chain to compare against")))
            continue
        if type(view) is MalformedView:
            defect = view.defect
            keyed.append(((corpus_id, 0, "session-chain-malformed", corpus_id), _finding("error", "session-chain-malformed", corpus_id, f"{defect.kind}: {defect.detail}", "the chain is malformed; nothing is classified")))
            continue
        assert type(view) is WellFormedView
        entries = view.entries
        settlement = {entry.registration: entry.committed for entry in entries if type(entry) is SettledEntryView}
        by_fulfills: dict[str, list[RegisteredEntryView]] = {}
        for entry in entries:
            if type(entry) is RegisteredEntryView and entry.fulfills is not None:
                by_fulfills.setdefault(entry.fulfills, []).append(entry)
        digests = {entry.digest for entry in entries}
        committed_everywhere |= {digest for digest, committed in settlement.items() if committed}

        for txid, staged in view.pending:
            if staged not in digests:
                keyed.append(((corpus_id, len(entries), "session-chain-pending", staged), _finding("warning", "session-chain-pending", staged, f"txid={txid}", "a staged registration the detached view reports outside its entries; the next write's recovery settles it")))

        for position, entry in enumerate(entries):
            if type(entry) is not IntentEntryView:
                continue
            decoded = shapes.decode_intent(entry.digest, entry.payload)
            if type(decoded) is not shapes.DecodedIntent or not isinstance(decoded.value, OperationIntent):
                continue
            match = _SESSION_ACTOR.fullmatch(decoded.value.actor)
            if match is None:
                continue
            sid = match.group(1)
            evidence = by_session.get(sid)
            if evidence is None:
                keyed.append(((corpus_id, position, "session-unknown", entry.digest), _finding("error", "session-unknown", entry.digest, f"actor={decoded.value.actor}", "an intent by a session with no ledger under this operations root")))
                continue
            readable = type(evidence) is LedgerReader
            open_invocations = list(evidence.open_invocations) if readable else []
            unknown = (not readable) or bool(open_invocations)
            acts = {act.entry for act in evidence.acts()} if readable else set()
            registrations = by_fulfills.get(entry.digest, [])
            committed = [r for r in registrations if settlement.get(r.digest) is True]
            pending = [r for r in registrations if settlement.get(r.digest) is None]
            if committed:
                for r in committed:
                    if r.digest in acts:
                        continue
                    if unknown:
                        keyed.append(((corpus_id, position, "session-outcome-unknown", r.digest), _finding("warning", "session-outcome-unknown", r.digest, f"session={sid} invocations={open_invocations} intent={entry.digest}", "a committed session write no act line covers, under an open invocation or an unreadable ledger")))
                    else:
                        keyed.append(((corpus_id, position, "session-entry-foreign", r.digest), _finding("error", "session-entry-foreign", r.digest, f"session={sid} intent={entry.digest}", "a committed session write no act line covers and no open invocation explains")))
            elif pending:
                for r in pending:
                    keyed.append(((corpus_id, position, "session-entry-pending", r.digest), _finding("warning", "session-entry-pending", r.digest, f"session={sid} intent={entry.digest}", "an unsettled registration fulfilling a session intent; reported, not adjudicated")))
            elif unknown:
                keyed.append(((corpus_id, position, "session-outcome-unknown", entry.digest), _finding("warning", "session-outcome-unknown", entry.digest, f"session={sid} invocations={open_invocations}", "a session intent with no registration, under an open invocation or an unreadable ledger")))
            else:
                keyed.append(((corpus_id, position, "session-intent-unclaimed", entry.digest), _finding("error", "session-intent-unclaimed", entry.digest, f"session={sid}", "a session intent no registration fulfills and no open invocation explains")))

    # --- ledger claims the chains lack -------------------------------------------------
    for evidence in ledgers:
        if type(evidence) is not LedgerReader:
            continue
        for act in evidence.acts():
            if act.entry not in committed_everywhere:
                keyed.append(((act.corpus, 1 << 30, "session-act-unverified", act.entry), _finding("error", "session-act-unverified", act.entry, f"session={evidence.session_id} invocation={act.invocation}", "an act line naming a registration no chain holds as committed; chains are truth")))

    keyed.sort(key=lambda pair: pair[0])
    return tuple(finding for _, finding in keyed)
```

`reconcile_sessions` in `session/__init__.py`:

```python
def reconcile_sessions(world_config: WorldConfig, operations_root: Path, *, exclude: str | None = None) -> tuple[Finding, ...]:
    """The audit surface (design §6): one lock-coherent snapshot per root, read
    through detached inspection; writes nothing and recovers nothing."""
    sessions = Path(operations_root) / "sessions"
    ids = sorted(p.name for p in sessions.iterdir() if p.is_dir() and p.name != exclude) if sessions.is_dir() else []
    chains: dict[str, ChainView] = {}
    extra: list[Finding] = []
    roots = sorted(world_config.corpus_roots)
    with ExitStack() as stack:
        for root in roots:
            stack.enter_context(_operation_lock_for(root))
        for root in roots:
            try:
                corpus_id = load_manifest(root).corpus_id
            except (ManifestMissing, ManifestMalformed) as caught:
                extra.append(Finding(severity="error", code="session-corpus-unadopted", ref=str(root), detail=str(caught), message="a configured corpus root with no readable manifest is not reconciled"))
                continue
            chains[corpus_id] = log_seam().inspect_detached(root)
        ledgers = tuple(read_ledger_evidence(operations_root, sid) for sid in ids)
    return tuple(sorted((*extra, *reconcile(ledgers, chains)), key=lambda f: (f.code, f.ref, f.detail)))
```

Import `ExitStack` from `contextlib`, `_operation_lock_for` and `Finding` from `beliefs.corpus`, `ChainView` from `beliefs.world.logmodel`, `read_ledger_evidence` from the ledger module, and `reconcile` from `beliefs.session.reconcile`; add `reconcile` to `__all__`.

- [ ] **Step 5: Run the tests and gates**

`uv run --frozen pytest tests/test_session_reconcile.py tests/test_session_writer.py -q -p no:cacheprovider`; whole suite; ruff; pyright; `test_capability_boundary.py`.

- [ ] **Step 6: Commit**

```bash
tasks done <task-8-id> "reconcile over ledger evidence and detached chain views; reconcile_sessions under the corpus lock"
git add python/src/beliefs/session python/tests/test_session_reconcile.py tasks/
git commit -m "feat(session): reconcile session ledgers against chains"
```

---

### Task 9: The durable acceptance suite — J1, J3, J4, J5, J9, J10, J11 over real roots

**Files:**
- Create: `python/tests/acceptance/test_session_acceptance.py`
- Test: the same file

**Interfaces:**
- Consumes: `open_attended_session`, `reconcile_sessions`, `WriterSession`, `ScopedWriter` (Tasks 7–8); `init_corpus_root`, `open_corpus`, `log_seam`, `durable_executor_factory` (root.py); `PINS` (`fixtures_cut6`); `durable_root`, `work_directory` fixtures (`acceptance/conftest.py`); `read_chain` through `log_seam().inspect_detached`.
- Produces: the test names the N2 arms of Task 11 cite — `test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration`, `test_j1_refusals_append_nothing_of_their_own`, `test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session`, `test_j4_every_intent_carries_the_session_actor`, `test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock`, `test_j9_lifecycle_and_the_refusing_configurations`, `test_j10_a_session_write_is_indistinguishable_on_ordinary_read`, `test_j11_a_writer_is_bound_to_one_invocation_durably`; a module-level `attended(work_directory, root, **kwargs)` helper.

- [ ] **Step 1: `tasks start <task-9-id>`**

- [ ] **Step 2: Write the tests**

Create `tests/acceptance/test_session_acceptance.py`:

```python
"""Cut 19's durable arms (design §9.2): the attended session over registered,
adopted roots on the certified volume, through the real DurableOperationPort."""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import threading
from pathlib import Path

import pytest
from authority import FULL
from fixtures_cut6 import PINS
from test_deletion import retraction_for
from test_durable_families import proposition

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import CorpusWriter, _operation_lock_for, corpus_check
from beliefs.errors import ActorMismatch, PermitExceeded, PermitFact, PlanRefused, SessionClosed, SessionProtocolError, SessionRefused
from beliefs.intents.reduce import qualify_chain
from beliefs.intents.shapes import decode_intent
from beliefs.permit import RequiredCapabilities
from beliefs.report import CLOSED, OperationIntent, Registration, completion
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.session import open_attended_session, open_ledger_reader, reconcile_sessions
from beliefs.session.ledger import ledger_path
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView
from beliefs.world.records import RECORD_CEILING

PROPOSITIONS = RequiredCapabilities.for_kinds({"proposition"}, {})
DIGEST = "d" * 64


def adopted(work_directory: Path, name: str) -> Path:
    root = work_directory / f"{name}-{secrets.token_hex(4)}"
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL).adopt_manifest(profile=PINS)
    return root


def config_for(work_directory: Path, root: Path) -> WorldConfig:
    return WorldConfig(work_directory / "world", secrets.token_hex(16), (root,))


def attended(work_directory: Path, root: Path, **kwargs):
    ops = work_directory / f"ops-{secrets.token_hex(4)}"
    return open_attended_session(config_for(work_directory, root), ops, **kwargs), ops


def chain(root: Path) -> WellFormedView:
    view = science_root.log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return view


def intents(root: Path):
    return [decode_intent(e.digest, e.payload).value for e in chain(root).entries if type(e) is IntentEntryView]


def registrations(root: Path):
    return [e for e in chain(root).entries if type(e) is RegisteredEntryView]


def tree_hash(*roots: Path) -> str:
    digest = hashlib.sha256()
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture()
def session_rig(work_directory):
    root = adopted(work_directory, "corpus")
    session, ops = attended(work_directory, root)
    try:
        yield session, root, ops
    finally:
        try:
            session.close()
        except Exception:  # noqa: BLE001 - a test may have ended the session
            pass
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)
        shutil.rmtree(ops, ignore_errors=True)


def fresh(session, invocation: str, required=PROPOSITIONS):
    writer = session.scoped(required, invocation)
    session.claim_invocation(invocation, "mint", DIGEST)
    return writer


# --- J1 ---------------------------------------------------------------------------
def test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration(session_rig):
    session, root, _ = session_rig
    before = len(chain(root).entries)
    w = fresh(session, "A")
    p1 = w.add(proposition("p1"))
    p2 = w.add(proposition("p2"))
    w.revise(p2.model_copy(update={"title": "renamed"}))
    w.supersede(proposition("p3", "inhibits"), of="proposition:p1")
    w.retract(retraction_for(p2, "proposition:p3"))
    w.delete("proposition:p3")
    entries = chain(root).entries[before:]
    kinds = [type(e).__name__ for e in entries]
    assert kinds == ["IntentEntryView", "RegisteredEntryView", "SettledEntryView"] * 6
    for intent_entry, registration, settlement in zip(entries[0::3], entries[1::3], entries[2::3]):
        decoded = decode_intent(intent_entry.digest, intent_entry.payload).value
        assert decoded.kind == "corpus-write" and decoded.actor == session.actor
        assert registration.fulfills == intent_entry.digest and settlement.committed
    rows, findings = qualify_chain(chain(root).entries, records={}, state_facts=science_root.log_seam().state_facts)
    assert {row.state for row in rows if row.shape == "operation"} == {"matched"}  # use IntentQualification's real field names
    for intent_entry in entries[0::3]:
        decoded = decode_intent(intent_entry.digest, intent_entry.payload).value
        registration = next(e for e in entries if type(e) is RegisteredEntryView and e.fulfills == intent_entry.digest)
        assert completion(decoded, (Registration(intent_token=decoded.event_token, pointer=registration.digest),), held={}) == CLOSED
    # Negative: the ordinary writer appends no intent.
    open_corpus(root, authority=FULL).add(proposition("plain"))
    assert type(chain(root).entries[-3]) is not IntentEntryView


def test_j1_refusals_append_nothing_of_their_own(session_rig):
    session, root, _ = session_rig
    settled_head = chain(root).tip  # the probe: a settled, non-writing read
    w = fresh(session, "A", RequiredCapabilities.for_kinds({"proposition"}, {}))
    refused = [
        (PermitExceeded, lambda: w.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s"}))),
        (PlanRefused, lambda: w.add(proposition("big").model_copy(update={"body": "x" * (RECORD_CEILING + 1)}))),
        (Exception, lambda: w.add(proposition("p1").model_copy(update={"kind": "act-report"}))),
    ]
    for exception, call in refused:
        with pytest.raises(exception):
            call()
        assert chain(root).tip == settled_head
    assert len(intents(root)) == 0  # no intent decodes to any refused call
    target = w.add(proposition("t"))
    w2 = fresh(session, "B")
    session_head = chain(root).tip
    with pytest.raises(Exception) as ordinary:
        open_corpus(root, authority=FULL).add(retraction_for(target, "proposition:t"))
    with pytest.raises(Exception) as operation:
        w2.add(retraction_for(target, "proposition:t"))
    assert type(operation.value) is type(ordinary.value)
    assert chain(root).tip == session_head


# --- J3 -----------------------------------------------------------------------------
def test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session(session_rig):
    session, root, _ = session_rig
    w = fresh(session, "A")
    with pytest.raises(PermitExceeded) as caught:
        w.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s"}))
    assert caught.value.requirement == PermitFact("kind", "source") and caught.value.capability.kinds == ("proposition",)
    assert session.invocation_acts("A") == ()
    with pytest.raises(PermitExceeded):
        fresh(session, "B", RequiredCapabilities.coordination()).add(proposition("p"))


# --- J4 -----------------------------------------------------------------------------
def test_j4_every_intent_carries_the_session_actor(session_rig):
    session, root, _ = session_rig
    w = fresh(session, "A")
    target = w.add(proposition("p1"))
    foreign = retraction_for(target, "proposition:p1")
    foreign.facets[stored.RETRACTION_FACET]["actor"] = "someone-else"
    head = chain(root).tip
    with pytest.raises(ActorMismatch):
        w.retract(foreign)
    assert chain(root).tip == head
    w.retract(retraction_for(target, "proposition:p1"))
    assert {i.actor for i in intents(root)} == {session.actor}


# --- J5 -----------------------------------------------------------------------------
def test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock(session_rig, monkeypatch):
    session, root, ops = session_rig
    ledger_file = ledger_path(ops, session.session_id)
    lock = _operation_lock_for(root)
    observed: dict[str, object] = {}
    real_record = session._record_act
    real_fsync = os.fsync

    def recording(invocation, commit):
        # The row's evidence: the append happens while this thread still holds the lock the commit held.
        observed["holder"] = (lock._holder, lock._writer_owner == threading.get_ident())
        observed["size_before"] = ledger_file.stat().st_size
        return real_record(invocation, commit)

    def counting(fd):
        observed.setdefault("fsyncs", []).append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(session, "_record_act", recording)
    monkeypatch.setattr(os, "fsync", counting)
    w = fresh(session, "A")
    node = w.add(proposition("p1"))
    assert observed["holder"] == ("writer", True)
    assert ledger_file.stat().st_size > observed["size_before"]
    (act,) = session.invocation_acts("A")
    registration = next(e for e in registrations(root) if e.fulfills == act.intent)
    assert act.entry == registration.digest and act.record_ids == ((node.uid, node.id),)
    assert ledger_file.read_bytes().endswith(b"\n")
    assert session._ledger._file.fileno() in observed["fsyncs"]
    w.delete("proposition:p1")
    assert session.invocation_acts("A")[-1].record_ids == ()
```

Continue the file:

```python
# --- J9 -----------------------------------------------------------------------------
def test_j9_lifecycle_and_the_refusing_configurations(work_directory):
    root = adopted(work_directory, "corpus")
    session, ops = attended(work_directory, root)
    reader = open_ledger_reader(ops, session.session_id)
    assert reader.actor == session.actor and reader.world_id and reader.closed is False
    session.claim_invocation("A", "mint", DIGEST)
    session.close()
    session.close()
    reader = open_ledger_reader(ops, session.session_id)
    assert reader.closed is True and reader.open_invocations == ("A",)
    for call in (lambda: session.scoped(PROPOSITIONS, "B"), lambda: session.claim_invocation("B", "mint", DIGEST), lambda: session.invocation_acts("A")):
        with pytest.raises(SessionClosed):
            call()
    # Refusing configurations, no sessions/ entry created.
    registered_no_manifest = work_directory / f"unadopted-{secrets.token_hex(4)}"
    init_corpus_root(registered_no_manifest, authority=FULL)
    plain = work_directory / f"plain-{secrets.token_hex(4)}"
    plain.mkdir()
    missing = work_directory / "missing"
    other = adopted(work_directory, "other")
    chainless = adopted(work_directory, "chainless")
    shutil.rmtree(chainless / ".#~chain")  # the chain lives under the root; removing it is AbsentView
    for description, roots in (
        ("zero roots", ()),
        ("two roots", (root, other)),
        ("missing root", (missing,)),
        ("existing, never registered", (plain,)),
        ("registered, no manifest", (registered_no_manifest,)),
    ):
        ops2 = work_directory / f"ops-{secrets.token_hex(4)}"
        with pytest.raises(SessionRefused):
            open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), roots), ops2)
        assert not (ops2 / "sessions").exists(), description
    ops3 = work_directory / f"ops-{secrets.token_hex(4)}"
    with pytest.raises(SessionRefused):
        open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), (chainless,)), ops3)
    assert not (ops3 / "sessions").exists()


# --- J10 ----------------------------------------------------------------------------
def test_j10_a_session_write_is_indistinguishable_on_ordinary_read(work_directory):
    twin_a = adopted(work_directory, "twin-a")
    twin_b = adopted(work_directory, "twin-b")
    session, ops = attended(work_directory, twin_a)
    node = proposition("p1")
    fresh(session, "A").add(node)
    open_corpus(twin_b, authority=FULL).add(node)
    a = {p.relative_to(twin_a).as_posix(): p.read_bytes() for p in twin_a.rglob("*.md")}
    b = {p.relative_to(twin_b).as_posix(): p.read_bytes() for p in twin_b.rglob("*.md")}
    assert a == b
    assert corpus_check(open_corpus(twin_a, authority=FULL).read_view) == corpus_check(open_corpus(twin_b, authority=FULL).read_view)
    fresh(session, "B").delete("proposition:p1")
    (twin_b / "proposition" / "p1.md").unlink()
    assert {p.name for p in twin_a.rglob("*.md")} == {p.name for p in twin_b.rglob("*.md")}
    # Negative: the chains differ by exactly what the session added — two intents, and the
    # delete's registration and settlement that a raw unlink never appends.
    assert len(chain(twin_a).entries) == len(chain(twin_b).entries) + 4
    session.close()


# --- J11 ----------------------------------------------------------------------------
def test_j11_a_writer_is_bound_to_one_invocation_durably(session_rig):
    session, root, _ = session_rig
    a = session.scoped(PROPOSITIONS, "A")
    head = chain(root).tip
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p0"))
    assert chain(root).tip == head
    session.claim_invocation("A", "mint", DIGEST)
    a.add(proposition("p1"))
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p2"))
    b = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "B")
    session.claim_invocation("B", "mint", DIGEST)
    head = chain(root).tip
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p3"))
    assert chain(root).tip == head and session.invocation_acts("B") == ()
    b.add(proposition("p3"))
    session.claim_invocation("C", "mint", DIGEST)
    with pytest.raises(SessionProtocolError):
        b.add(proposition("p4"))
```

`test_j1_each_scoped_write...` assumes the retraction of `p2` after its revision resolves; `retraction_for` reads the target's semantic stamp, which `revise` leaves unchanged. If the acceptance `conftest` lacks `work_directory`, use the same fixture name the permit acceptance module uses (check `tests/acceptance/conftest.py`).

- [ ] **Step 3: Run on the certified volume**

Run: `uv run --frozen pytest tests/acceptance/test_session_acceptance.py -q -p no:cacheprovider` from `python/` with the checkout's certified volume (the repository-relative default). Expected: PASS. A `CapabilityUnavailable` block means the kernel outran the certification, not a regression: recertify and rerun.

- [ ] **Step 4: Gates and commit**

```bash
tasks done <task-9-id> "durable acceptance: J1, J3, J4, J5, J9, J10, J11 over registered roots"
git add python/tests/acceptance/test_session_acceptance.py tasks/
git commit -m "test(session): add the durable acceptance arms for J1, J3, J4, J5, J9, J10 and J11"
```

---

### Task 10: The durable acceptance suite — J2's faults and J8's reconciliation

**Files:**
- Modify: `python/tests/acceptance/test_session_acceptance.py` (append)
- Create: `python/tests/acceptance/session_faults.py` (the halting backend and the child-process script)

**Interfaces:**
- Consumes: Task 9's helpers; `science_root._mapped_submit`, `science_root._registration_for`, `CorpusWriter._reconstruct`, `atoms.fs.platform.select_backend`, `DurableOperationPort`.
- Produces: `test_j2_a_failure_before_submission_leaves_an_intent_and_no_record`, `test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed`, `test_j2_a_rebuild_failure_leaves_the_root_unresolved`, `test_j2_a_ledger_failure_after_commit_ends_the_session`, `test_j2_a_raced_precondition_is_an_execution_error`, `test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare`, `test_j2_a_fresh_process_settles_before_its_first_prepare`, `test_j2_library_and_mixed_handles_settle_first`, `test_j8_reconciliation_over_the_real_root`, `test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write`; `session_faults.HaltingBackend`.

- [ ] **Step 1: `tasks start <task-10-id>`**

- [ ] **Step 2: Write the halting backend**

Create `tests/acceptance/session_faults.py`:

```python
"""Fault fixtures for J2 (design §13 item 4): a backend that halts at the first
publish-phase call, leaving a real staged, unsettled transaction."""

from __future__ import annotations

from atoms.fs.platform import select_backend

PUBLISH_PHASE = ("exchange", "transfer_noclobber", "link_anchor")


class HaltingBackend:
    """Delegates every engine call to the real backend; once `armed`, raises
    `OSError` at the first publish-phase call after at least one `write`, then
    disarms — one halt per arming."""

    def __init__(self) -> None:
        self._inner = select_backend()
        self.writes = 0
        self.armed = False
        self.halted = False

    def arm(self) -> None:
        self.writes = 0
        self.armed = True
        self.halted = False

    def __getattr__(self, name):
        target = getattr(self._inner, name)
        if name == "write":
            def counting(*args, **kwargs):
                self.writes += 1
                return target(*args, **kwargs)
            return counting
        if name in PUBLISH_PHASE:
            def halting(*args, **kwargs):
                if self.armed and self.writes and not self.halted:
                    self.halted = True
                    self.armed = False
                    raise OSError("halted by the J2 fixture before publish")
                return target(*args, **kwargs)
            return halting
        return target
```

If the engine's publish step turns out to use a different backend method, find it by tracing one committing transaction's backend calls (wrap every method, print names) and set `PUBLISH_PHASE` to the first call after the staging writes; the arm's assertion — a pending registration under detached inspection before recovery, gone after — is what the row requires.

- [ ] **Step 3: Write the tests**

Append to `test_session_acceptance.py`:

```python
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import DefaultExecutor
from session_faults import HaltingBackend

from beliefs.corpus import _root_state_for
from beliefs.errors import RelocationTargetMissing, SessionLedgerFailed
from beliefs.relocation import move
from beliefs.root import DurableOperationPort, PRODUCTION_STORAGE, durable_executor_factory


def state_of(root: Path):
    return _root_state_for(root.resolve(), durable_executor_factory())


# --- J2 -------------------------------------------------------------------------------
def test_j2_a_failure_before_submission_leaves_an_intent_and_no_record(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")

    def refuse(**kwargs):
        raise ExecutionError("no submission", index=None, applied=0)

    monkeypatch.setattr(science_root, "_mapped_submit", refuse)
    before = len(chain(root).entries)
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    entries = chain(root).entries[before:]
    assert [type(e).__name__ for e in entries] == ["IntentEntryView"]
    assert not (root / "proposition" / "p1.md").exists()
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    (unknown,) = [f for f in findings if f.code == "session-outcome-unknown"]
    assert unknown.ref == entries[0].digest and "invocations=['A']" in unknown.detail
    # Negative: a failure in append_intent leaves nothing.
    monkeypatch.setattr(DurableOperationPort, "append_intent", lambda self, payload: (_ for _ in ()).throw(ExecutionError("no intent", index=None, applied=0)))
    head = chain(root).tip
    with pytest.raises(ExecutionError):
        w.add(proposition("p2"))
    assert chain(root).tip == head


def test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")
    monkeypatch.setattr(science_root, "_registration_for", lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)))
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert (root / "proposition" / "p1.md").exists()
    (registration,) = [e for e in registrations(root) if e.fulfills is not None]
    assert state_of(root).unresolved is True
    assert session.invocation_acts("A") == ()
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert ("session-outcome-unknown", registration.digest) in [(f.code, f.ref) for f in findings]
    # The next write settles first and sees the record.
    w.add(proposition("p2"))
    assert state_of(root).unresolved is False
    assert open_corpus(root, authority=FULL).read_view.get("proposition:p1").id == "proposition:p1"


def test_j2_a_rebuild_failure_leaves_the_root_unresolved(session_rig, monkeypatch):
    session, root, _ = session_rig
    w = fresh(session, "A")
    original = CorpusWriter._reconstruct
    calls = {"n": 0}

    def failing(self):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ExecutionError("rebuild failed", index=None, applied=None)
        return original(self)

    monkeypatch.setattr(CorpusWriter, "_reconstruct", failing)
    with pytest.raises(ExecutionError, match="rebuild failed"):
        w.add(proposition("p1"))
    assert state_of(root).unresolved is True
    monkeypatch.undo()
    w.add(proposition("p2"))
    assert state_of(root).unresolved is False


def test_j2_a_ledger_failure_after_commit_ends_the_session(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")
    real = os.fsync
    ledger_fd = session._ledger._file.fileno()
    monkeypatch.setattr(os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("ledger fsync")) if fd == ledger_fd else real(fd))
    with pytest.raises(SessionLedgerFailed):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert (root / "proposition" / "p1.md").exists()
    assert state_of(root).unresolved is False  # the rebuild completed before the append
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    (registration,) = [e for e in registrations(root) if e.fulfills is not None]
    assert ("session-outcome-unknown", registration.digest) in [(f.code, f.ref) for f in findings]
    with pytest.raises(SessionLedgerFailed):
        session.claim_invocation("B", "mint", DIGEST)


def test_j2_a_raced_precondition_is_an_execution_error(session_rig, monkeypatch):
    session, root, _ = session_rig
    w = fresh(session, "A")
    real = science_root._mapped_submit

    def race(**kwargs):
        (root / "proposition").mkdir(exist_ok=True)
        (root / "proposition" / "p1.md").write_bytes(b"raw")
        return real(**kwargs)

    monkeypatch.setattr(science_root, "_mapped_submit", race)
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    (root / "proposition" / "p1.md").unlink()
    w.add(proposition("p2"))  # settles, then commits


def halting_session(work_directory: Path, root: Path):
    """A session whose scoped writers run over a halting backend; the factory's
    recovery runs over the real one."""
    from beliefs.session.writer import WriterSession
    from beliefs.session.ledger import LedgerWriter, ledger_path

    backend = HaltingBackend()
    ops = work_directory / f"ops-{secrets.token_hex(4)}"
    session_id = secrets.token_hex(16)
    path = ledger_path(ops, session_id)
    path.parent.mkdir(parents=True)

    def writer_factory(authority):
        port = DurableOperationPort(root, backend=backend, storage=PRODUCTION_STORAGE, metadata_root=metadata_root_for(root), authority=authority)
        return CorpusWriter(root, durable_executor_factory(), authority=authority, operation_port=port)

    session = WriterSession(session_id=session_id, actor=f"session:{session_id}", world_id="1" * 32, corpus_root=root,
                            corpus_id=load_manifest(root).corpus_id, operations_root=ops, ledger=LedgerWriter(path),
                            writer_factory=writer_factory)
    return session, backend, ops


def test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare(work_directory):
    root = adopted(work_directory, "halting")
    session, backend, _ = halting_session(work_directory, root)
    w = fresh(session, "A")
    w.add(proposition("t"))  # commits: the backend is not yet armed
    backend.arm()
    with pytest.raises(ExecutionError):
        w.add(proposition("staged"))
    assert backend.halted and state_of(root).unresolved is True
    view = chain(root)
    pending = [r for r in view.entries if type(r) is RegisteredEntryView and r.digest not in {s.registration for s in view.entries if type(s) is SettledEntryView}]
    assert pending or view.pending, "the halt must leave a pending registration"
    # Continuation through the same session: recovery first, then the prepare judges the settled state.
    session.close_invocation("A", {"done": []})
    w2 = fresh(session, "B")
    with pytest.raises(RelocationTargetMissing):
        w2.retract(retraction_for(proposition("staged"), "proposition:t"))
    assert not (root / "proposition" / "staged.md").exists()
    after = chain(root)
    assert not after.pending
    assert state_of(root).unresolved is False
    w2.add(proposition("fresh"))


def test_j2_a_fresh_process_settles_before_its_first_prepare(work_directory):
    import json
    import subprocess
    import sys

    root = adopted(work_directory, "cross-process")
    session, backend, ops = halting_session(work_directory, root)
    w = fresh(session, "A")
    w.add(proposition("t"))
    backend.arm()
    with pytest.raises(ExecutionError):
        w.add(proposition("staged"))
    assert chain(root).pending or any(
        type(e) is RegisteredEntryView and e.digest not in {s.registration for s in chain(root).entries if type(s) is SettledEntryView}
        for e in chain(root).entries
    ), "the halt must leave a pending registration for the child to settle"
    # The child opens over the SAME operations root, so it reads this session's unclosed ledger,
    # reports the pending registration at open, and settles it before its first prepare.
    script = f"""
import json, secrets
from pathlib import Path
from test_durable_families import proposition
from beliefs.permit import RequiredCapabilities
from beliefs.session import open_attended_session
from beliefs.world import WorldConfig
root = Path({str(root)!r})
session = open_attended_session(WorldConfig(root.parent / "w", secrets.token_hex(16), (root,)), Path({str(ops)!r}))
w = session.scoped(RequiredCapabilities.for_kinds({{"proposition"}}, {{}}), "A")
session.claim_invocation("A", "mint", "d" * 64)
w.add(proposition("after"))
from beliefs import root as science_root
view = science_root.log_seam().inspect_detached(root)
settled = {{s.registration for s in view.entries if type(s).__name__ == "SettledEntryView"}}
pending = [e.digest for e in view.entries if type(e).__name__ == "RegisteredEntryView" and e.digest not in settled] + [d for _, d in view.pending]
print(json.dumps({{"pending_after": pending, "findings": sorted({{f.code for f in session.findings}})}}))
session.close()
"""
    completed = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True,
                               env={**os.environ, "PYTHONPATH": os.pathsep.join([str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)])})
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["pending_after"] == []  # the child's first write settled it before its prepare
    assert "session-entry-pending" in result["findings"] and "session-unclosed" in result["findings"]


def test_j2_library_and_mixed_handles_settle_first(work_directory, monkeypatch):
    root = adopted(work_directory, "handles")
    session, _ = attended(work_directory, root)
    w = fresh(session, "A")
    target = w.add(proposition("t"))
    monkeypatch.setattr(science_root, "_registration_for", lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)))
    with pytest.raises(ExecutionError):
        w.delete("proposition:t")
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    order: list[str] = []
    real_settle = CorpusWriter._settle
    real_validate = CorpusWriter._validate_import_bundle
    real_preflight_add = CorpusWriter._preflight_add_locked
    monkeypatch.setattr(CorpusWriter, "_settle", lambda self: (order.append("settle"), real_settle(self))[1])
    monkeypatch.setattr(CorpusWriter, "_validate_import_bundle", lambda self, *a, **k: (order.append("validate"), real_validate(self, *a, **k))[1])
    monkeypatch.setattr(CorpusWriter, "_preflight_add_locked", lambda self, node: (order.append("preflight-add"), real_preflight_add(self, node))[1])
    library = open_corpus(root, authority=FULL)
    try:
        library.import_bundle([retraction_for(target, "proposition:t")], observer="o", instrument="i", opened_at="2026-09-05T00:00:00Z", closed_at="2026-09-05T00:00:01Z")
    except Exception:  # noqa: BLE001 - the outcome is not the claim; the order is
        pass
    assert order[:2] == ["settle", "validate"] and state_of(root).unresolved is False
    assert library.read_view.resolve("proposition:t") is None
    # Relocation: settlement precedes the locked preflight helpers.
    other = adopted(work_directory, "other")
    survivor = library.add(proposition("mover"))
    state_of(root).unresolved = True
    order.clear()
    try:
        move(library, open_corpus(other, authority=FULL), "proposition:mover")
    except Exception:  # noqa: BLE001
        pass
    assert order and order[0] == "settle" and ("preflight-add" not in order or order.index("preflight-add") > 0)
    # Mixed handle: a portless durable writer recovers through the factory's capability.
    state_of(root).unresolved = True
    portless = CorpusWriter(root, durable_executor_factory(), authority=FULL)
    assert state_of(root).recover is durable_executor_factory().recover
    portless.add(proposition("after"))
    assert state_of(root).unresolved is False
    never = work_directory / f"never-{secrets.token_hex(4)}"
    never.mkdir()
    assert _root_state_for(never, DefaultExecutor).recover is None
    session.close()


# --- J8 -------------------------------------------------------------------------------
def test_j8_reconciliation_over_the_real_root(work_directory, monkeypatch):
    root = adopted(work_directory, "reconcile")
    session, ops = attended(work_directory, root)
    fresh(session, "A").add(proposition("p1"))
    session.close_invocation("A", {"done": []})
    w = fresh(session, "B")
    monkeypatch.setattr(science_root, "_registration_for", lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)))
    with pytest.raises(ExecutionError):
        w.add(proposition("p2"))
    monkeypatch.undo()
    config = config_for(work_directory, root)
    before = tree_hash(root, metadata_root_for(root), ops)
    findings = reconcile_sessions(config, ops)
    assert tree_hash(root, metadata_root_for(root), ops) == before
    assert findings == reconcile_sessions(config, ops)
    codes = {f.code for f in findings}
    assert "session-outcome-unknown" in codes and "session-unclosed" in codes
    later, ops2 = attended(work_directory, root)  # a later endpoint over a *different* operations root
    assert {f.code for f in later.findings} == {"session-unknown"}  # this session's intents name a ledger it cannot see
    later.close()
    second = open_attended_session(config, ops)
    assert second.findings == reconcile_sessions(config, ops, exclude=second.session_id)
    second.close()
    # Byte equality with an unsettled registration present (registered inspection would have resolved it).
    halted_root = adopted(work_directory, "halted")
    halted, backend, halted_ops = halting_session(work_directory, halted_root)
    hw = fresh(halted, "A")
    hw.add(proposition("t"))
    backend.arm()
    with pytest.raises(ExecutionError):
        hw.add(proposition("staged"))
    before = tree_hash(halted_root, metadata_root_for(halted_root), halted_ops)
    found = reconcile_sessions(config_for(work_directory, halted_root), halted_ops)
    assert tree_hash(halted_root, metadata_root_for(halted_root), halted_ops) == before
    assert {"session-entry-pending", "session-unclosed"} <= {f.code for f in found}


def test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write(work_directory):
    root = adopted(work_directory, "interleave")
    session, ops = attended(work_directory, root)
    w = fresh(session, "A")
    config = config_for(work_directory, root)
    inside = threading.Event()
    release = threading.Event()
    original = CorpusWriter._reconstruct

    def blocking(self):
        inside.set()
        release.wait(timeout=10)
        return original(self)

    CorpusWriter._reconstruct = blocking
    try:
        thread = threading.Thread(target=lambda: w.add(proposition("p1")))
        thread.start()
        inside.wait(timeout=10)
        done = []
        reader = threading.Thread(target=lambda: done.append(reconcile_sessions(config, ops)))
        reader.start()
        reader.join(timeout=0.5)
        assert reader.is_alive(), "reconciliation must wait for the corpus lock"
        release.set()
        thread.join()
        reader.join()
    finally:
        CorpusWriter._reconstruct = original
    (findings,) = done
    assert not [f for f in findings if f.code == "session-entry-foreign"]
    session.close()
```

`move`'s signature is `relocation.move(source_writer, destination_writer, ref, ...)` at HEAD; check it and adjust the call in `test_j2_library_and_mixed_handles_settle_first`. The relocation assertion is only that `_settle` ran first; whether the move then succeeds or refuses is not the claim.

- [ ] **Step 4: Run on the certified volume**

`uv run --frozen pytest tests/acceptance/test_session_acceptance.py -q -p no:cacheprovider` — PASS. Where the halting backend's method choice is wrong, the continuation arm fails on "must leave a pending registration"; adjust `PUBLISH_PHASE` per Step 2's note and rerun.

- [ ] **Step 5: Gates and commit**

```bash
tasks done <task-10-id> "durable acceptance: J2's faults, the fresh-process and mixed-handle continuations, J8 over the real root and under an interleaved write"
git add python/tests/acceptance tasks/
git commit -m "test(session): add the durable acceptance arms for J2 and J8"
```

---

### Task 11: N2 arms, the audit test, and the cut 19 runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut19.py`, `python/tests/acceptance/test_n2_cut19.py`, `python/tools/cut19_acceptance.py`

**Interfaces:**
- Consumes: the check names of Tasks 9–10; `n2_arms.Arm`, `n2_arms.Sabotage`; `test_n2.audit`, `test_n2.baseline`; the frozen cut record `docs/designs/2026-09-05-conformance-cut-19.md` at `5cc2153`.
- Produces: `CUT19_ARMS`, `DECLARATION_UNITS` (the eleven `J` rows), `unit_of(row)`, `CO_CITED = ()`; `tools/cut19_acceptance.py` with `PREFIX_RUNNERS = ("cut18_acceptance.py",)` and `PHASE_MODULES = ("test_session_acceptance.py", "test_n2_cut19.py")`.

- [ ] **Step 1: `tasks start <task-11-id>`**

- [ ] **Step 2: Write the arms**

Create `tests/acceptance/n2_arms_cut19.py`. One grouped unit per row; lettered arms normalize through `unit_of`. Every `before` must occur exactly once in its module — take each from the landed source, not from this plan. The sabotages, by row (each `Arm(row=..., asserts=..., sabotage=Sabotage(module=..., before=..., after=...), checks=(...,))`):

```python
from n2_arms import Arm, Sabotage

_A = "acceptance/test_session_acceptance.py"
_J1 = f"{_A}::test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration"
_J1R = f"{_A}::test_j1_refusals_append_nothing_of_their_own"
_J2 = f"{_A}::test_j2_a_failure_before_submission_leaves_an_intent_and_no_record"
_J2R = f"{_A}::test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed"
_J2C = f"{_A}::test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare"
_J2L = f"{_A}::test_j2_a_ledger_failure_after_commit_ends_the_session"
_J3 = f"{_A}::test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session"
_J4 = f"{_A}::test_j4_every_intent_carries_the_session_actor"
_J5 = f"{_A}::test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock"
_J6 = "test_session_writer.py::test_the_claim_table"
_J6A = "test_session_writer.py::test_an_abandoned_invocation_stays_open_and_never_blocks_a_fresh_claim"
_J7 = "test_session_ledger.py::test_each_append_is_fsynced_once_and_lands_before_return"
_J7P = "test_session_ledger.py::test_a_partial_write_ends_the_writer_and_preserves_the_bytes"
_J8 = f"{_A}::test_j8_reconciliation_over_the_real_root"
_J8P = "test_session_reconcile.py::test_the_views_pending_pairs_absent_from_entries_are_reported_without_an_intent"
_J8F = "test_session_reconcile.py::test_uncovered_committed_registration_with_no_open_invocation_is_foreign"
_J8I = f"{_A}::test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write"
_J9 = f"{_A}::test_j9_lifecycle_and_the_refusing_configurations"
_J10 = f"{_A}::test_j10_a_session_write_is_indistinguishable_on_ordinary_read"
_J11 = f"{_A}::test_j11_a_writer_is_bound_to_one_invocation_durably"

DECLARATION_UNITS = tuple(f"J{n}" for n in range(1, 12))
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")
```

Then the arms, in this order, each `before` copied verbatim from the landed file:

| row | module | sabotage (`before` → `after`) | checks |
|---|---|---|---|
| J1a | `corpus.py` | in `_commit`: swap the `preflight` block and the `append_intent` block so the intent precedes the preflight | `_J1R` |
| J1b | `corpus.py` | in `_commit`: call `self._writer._append_operation_intent(...)` instead of the new intent append (requires `act-report`) | `_J1`, `_J3` |
| J1c | `corpus.py` | `_prepare_add`: replace `self._refuse_family_kinds(node)` with `self._preflight_add_locked(node)` | `_J1R` |
| J1d | `corpus.py` | in `_commit`: `raise PlanRefused(str(caught)) from caught` → `raise` (the nodes type escapes) | `_J1R`, `test_operation_writes.py::test_an_over_ceiling_record_is_plan_refused_before_the_intent` |
| J1e | `report.py` | drop `"corpus-write", ` from `OPERATION_KINDS` | `_J1` |
| J1f | `intents/reduce.py` | in `_qualify_one`: `value.kind == "corpus-write"` → `value.kind == "never"` | `_J1` |
| J2a | `corpus.py` | in `_commit`: move `writer._reconstruct()` out of the `_submitting` block into a `finally` | `_J2R` |
| J2b | `corpus.py` | `_RootState.unresolved: bool = True` → `= False` | `test_corpus_write.py::TestTheUnresolvedRoot::test_a_fresh_root_state_is_unresolved_and_the_first_write_settles_it` |
| J2c | `corpus.py` | `_settle`: remove the `state.recover(...)` call | `_J2C` |
| J2d | `corpus.py` | `_root_state_for`: `getattr(executor_factory, "recover", None)` → `None` | `_J2C`, `f"{_A}::test_j2_library_and_mixed_handles_settle_first"` |
| J2e | `root.py` | `_DurableExecutorFactory.recover`: body → `return` | `_J2C` |
| J3a | `session/writer.py` | `scoped`: `Authority(required.permit, self.actor)` → `Authority(self._ceiling, self.actor)` | `_J3` |
| J3b | `session/writer.py` | `scoped`: `if not permit_covers(self._ceiling, required):` → `if False:` | `test_session_writer.py::test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists` |
| J4 | `corpus.py` | in `_commit`: `OperationIntent("corpus-write", token, writer.authority.actor)` → `... "library")` | `_J4` |
| J5a | `session/writer.py` | `_act`: drop `self._session._record_act(self._invocation, commit)` | `_J5` |
| J5b | `session/writer.py` | `_act`: move `_record_act` after the `with _operation_lock_for(...)` block | `_J5` |
| J6a | `session/writer.py` | `claim_invocation`: `if entry.command != command or entry.input_digest != digest:` → `if False:` | `_J6` |
| J6b | `session/writer.py` | `claim_invocation`: insert a `SessionProtocolError` when `self._current is not None` before the fresh claim | `_J6A` |
| J6c | `session/writer.py` | `close_invocation`: `self._index[invocation].outcome = validated` → `= {"done": []}` | `test_session_writer.py::test_a_refusal_outcome_replays_whole` |
| J7a | `session/ledger.py` | `append`: drop `os.fsync(self._file.fileno())` | `_J7` |
| J7b | `session/ledger.py` | `append`: `self._failed = True` → `self._failed = False` | `_J7P` |
| J7c | `session/writer.py` | `close_invocation`: update the index before the `append` | `test_session_writer.py::test_a_ledger_failure_ends_the_session` |
| J8a | `session/reconcile.py` | `if r.digest in acts: continue` → `if True: continue` | `_J8F`, `_J8` |
| J8b | `session/reconcile.py` | `if unknown:` (registration branch) → `if False:` | `_J8` |
| J8c | `session/reconcile.py` | `unknown = (not readable) or bool(open_invocations)` → `unknown = bool(open_invocations)` | `test_session_reconcile.py::test_unreadable_ledgers_are_findings_and_their_intents_read_outcome_unknown` |
| J8d | `session/reconcile.py` | drop the `for txid, staged in view.pending:` block | `_J8P` |
| J8e | `session/__init__.py` | `inspect_detached(root)` → `inspect_registered(root)` | `_J8` (the byte-equality with an unsettled registration) |
| J8f | `session/__init__.py` | read `ledgers` after the `with ExitStack()` block | `_J8I` |
| J9a | `session/__init__.py` | `if len(world_config.corpus_roots) != 1:` → `if False:` | `_J9` |
| J9b | `session/__init__.py` | drop the `type(view) is not WellFormedView` refusal | `_J9` |
| J10 | `corpus.py` | `_create_or_replace_op`: append a second `CreateOp` of an act-report to the plan | `_J10` |
| J11a | `session/writer.py` | `_require_current`: `if self._current != invocation:` → `if self._current is None:` | `_J11` |
| J11b | `session/writer.py` | `_record_act`: `if self._current != invocation:` → `if False:` | `_J11` |
| J-inv | `tests/test_permit_boundary.py` | drop the `"corpus.py:OperationWrites._commit"` row | `test_permit_boundary.py::test_the_inventory_is_closed_in_both_directions` |

Where the table says "drop" or "move", spell the exact `before`/`after` strings from the file. The `J-inv` arm sabotages a test module, not the package: follow how `n2_arms_cut17.py` spells its inventory arm's `module` so `test_each_sabotage_names_one_real_source_site` resolves it.

- [ ] **Step 3: Write the audit test**

Create `tests/acceptance/test_n2_cut19.py` by copying `test_n2_cut18.py` and changing: the imports (`CUT18_ARMS` joins `PRIOR_ARMS`; `from n2_arms_cut19 import CO_CITED, CUT19_ARMS, DECLARATION_UNITS, unit_of`), `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-05-conformance-cut-19.md"`, `CUT19_FREEZE_COMMIT = "5cc2153"`, `CUT19_FROZEN_SHA256 = <sha256 of the file at that commit>` (compute with `git show 5cc2153:docs/designs/2026-09-05-conformance-cut-19.md | sha256sum`), `FROZEN_PRIOR_CUT_FILES` gaining `"python/tests/n2_arms_cut18.py": "<the commit that froze it>"`, the inventory test asserting `DECLARATION_UNITS == tuple(f"J{n}" for n in range(1, 12))` and `len == 11`, and the pin test comparing §2–§7 of the current file byte-exact to the freeze commit's (no renumbering substitutions — this cut was frozen once). Drop the renumbering machinery.

- [ ] **Step 4: Write the runner**

Create `tools/cut19_acceptance.py` from `cut18_acceptance.py` with: `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut19-acceptance"`, `SCIENCE_CUT19_ROOT`, `PREFIX_RUNNERS = ("cut18_acceptance.py",)`, `PHASE_MODULES = ("test_session_acceptance.py", "test_n2_cut19.py")`, the probe's actor `"cut19-probe"`, `range(4, 20)` in `cut_environment`, `SCIENCE_CUT18_ROOT` in `run_prefix`, `from n2_arms_cut19 import CUT19_ARMS, DECLARATION_UNITS`, and the two closing prints: `f"declared arms: {arms} (= {units} declaration units; 11 guarantee rows)"` and `"row accounting: 11 full/closed + 0 partial + 0 re-reads"`.

- [ ] **Step 5: Run**

`uv run --frozen pytest tests/acceptance/test_n2_cut19.py -q -p no:cacheprovider` (the audit applies every sabotage in a workspace copy; expect several minutes). Every arm must be `sound`; a `stale` arm means a `before` string does not occur exactly once — fix the string, never the source. Then `uv run --frozen python tools/cut19_acceptance.py` end to end on the certified volume.

- [ ] **Step 6: Gates and commit**

```bash
tasks done <task-11-id> "n2_arms_cut19 (11 units), test_n2_cut19 pinning 5cc2153, tools/cut19_acceptance.py with the cut 18 prefix"
git add python/tests/acceptance/n2_arms_cut19.py python/tests/acceptance/test_n2_cut19.py python/tools/cut19_acceptance.py tasks/
git commit -m "test(cut19): add the N2 arms, the freeze-pinning audit and the acceptance runner"
```

---

### Task 12: Discharge — results record, ledger, roadmap, README, guide, banked-design notes, task closure

**Files:**
- Create: `docs/plans/2026-09-05-conformance-cut-19-results.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (Current state), `docs/plans/2026-08-29-implementation-roadmap.md`, `README.md`, `docs/guide/foundations.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/glossary.md`, `docs/designs/2026-09-05-writer-session-design.md` (status), `docs/designs/2026-09-05-conformance-cut-19.md` (status line only), `docs/designs/2026-08-11-act-report-design.md`, `docs/designs/2026-09-04-write-permits-design.md`, `docs/designs/2026-09-03-world-changing-families-design.md` (dated amendment notes)

**Interfaces:**
- Consumes: the runner's output from Task 11.
- Produces: the record the roadmap guard reads as newest (`**Ranked at:** cut 19`); a `Remaining boundary` section the ledger guard reads.

- [ ] **Step 1: `tasks start <task-12-id>`**

- [ ] **Step 2: Run the discharge**

From `python/`: `uv run --frozen python tools/cut19_acceptance.py 2>&1 | tee ../docs/plans/cut19-run.log` (use `set -o pipefail`). It must exit 0 after running cut 18's runner as prefix. Record the kernel, volume tuple, commit, wall time, arm count and the two accounting lines.

- [ ] **Step 3: Write the results record**

`docs/plans/2026-09-05-conformance-cut-19-results.md`, in the shape of `2026-09-04-conformance-cut-18-results.md` (read it first): header with the discharge commit, the freeze commit `5cc2153`, the runner, the prefix runner's result, the certified tuple; §1 the eleven rows each `closed` with the tests that closed them; §2 the N2 accounting (arms, 11 units, all sound); §3 deviations dated (any §13 items added during implementation, any stale prior arm and its citation); §4 reproduction prerequisites; and a `## Remaining boundary` section naming, as guarantee-row labels, what stays open on the roadmap after this cut — at minimum the rows the tier-1 table still lists (C7, C8, C9, H4, G9, R10, T5, W1…, D1…, L8, N1…): copy the labels the cut-18 record's `Remaining boundary` names and drop none, since this cut closes no other table's rows. Delete `cut19-run.log` after quoting from it.

- [ ] **Step 4: Ledger, roadmap, README, guide**

- Ledger `Current state`: add a bullet after the managed-deletion one — "**The writer session** — the attended session and its fixed actor, the append-then-fsync ledger and claim protocol, the invocation-bound scoped writer under exactly its requirement, `corpus-write` as an operation intent fulfilled by its registration, unresolved-root settlement before every prepare, and reconciliation over ledgers and chains. J1–J11 close at cut 19; `science`'s Task 12 is unblocked." Change "Implemented through conformance cut 18" to 19; drop the `writer-session` row from the boundary table; update the closing paragraph to name the new record and "closes J1–J11 and leaves every other open row as cut 18 left it".
- Roadmap: `**Ranked at:** cut 19, against the ledger's Current state (2026-09-05)`; drop `writer-session` from the boundary index, the tier-1 table and the lane table (the `session` lane closes; say so in the head paragraph the way cut 17's did for `authority`); add a head paragraph "Cut 19 delivered the writer session: J1–J11 close …".
- README: "Every conformance cut through **cut 19**"; the status paragraph gains the writer session; the cut-19 design-table row's "not yet discharged" becomes "discharged 2026-09-05"; the "latest discharged boundary" sentence names cut 19 and its results; the "is frozen and not yet implemented" sentence is removed.
- Guide: `foundations.md` — the writer session is implemented (drop "not yet implemented"), bump `updated`; `contracts-and-adoption.md` — "The writer-session cut is discharged as cut 19: J1–J11 close" and the results record in `sources`; `glossary.md` — entries for *writer session*, *session ledger*, *scoped writer*, each citing the design. Run `uv run --frozen python tools/check_guide.py`.
- Design status: "implemented and discharged 2026-09-05 at `<commit>`; conformance cut 19 froze at `5cc2153` and its 11 units passed through N arms. Results: `../plans/2026-09-05-conformance-cut-19-results.md`." Cut record status: "Discharged 2026-09-05 (`../plans/2026-09-05-conformance-cut-19-results.md`)." — the status line only; §2–§7 stay byte-exact (the pin test enforces it).
- Dated amendment notes (a short `> **Amended 2026-09-05 (writer session):**` block, frozen text untouched): act-report design §3 (the `corpus-write` operation kind and its qualification by the registration; eight members); write-permits design §4.2 (the inventory's 37th row, `OperationWrites._commit`) and §8 item 5 (the ledger and session now exist); world-changing-families design §3.1 (a session-mediated `delete` appends an intent and a fulfilling registration with an empty surface; it still mints no report).

- [ ] **Step 5: Gates, guards, and the merge**

Run the three gates, `tools/check_guide.py`, and `tasks check`. Then:

```bash
tasks done <task-12-id> "cut 19 discharged; ledger, roadmap, README, guide and banked designs updated"
tasks done beliefs-afbbff "writer session delivered: J1-J11 closed at cut 19 (docs/plans/2026-09-05-conformance-cut-19-results.md)"
git add -A
git commit -m "docs(session): discharge conformance cut 19 and record the writer session as delivered"
```

Then, per the finishing-a-development-branch skill: merge `feat/writer-session` into `main` with `--no-ff` from the main checkout, re-run the gates on `main`, and remove the worktree only after the merge commit is on `main` (the ledger and results record are tracked files, so nothing is lost with the worktree).
