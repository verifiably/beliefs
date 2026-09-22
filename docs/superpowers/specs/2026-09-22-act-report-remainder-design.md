# The act-report remainder — the `audit` and `re-check` operations

**Slice of:** `2026-08-11-act-report-design.md` §3.1 and §4 (the boundary
wrapper over the read-only audit evaluator and over holdings re-checks)
**Boundary:** `act-report-remainder` — T2's `audit` and `re-check` operation
kinds (`../../designs/2026-08-03-redesign-adoption-ledger.md`, Current state)
**Task:** `beliefs-86b150`
**Lane:** `world-read`, its head since cut 36 (roadmap §Lanes)
**Cut:** 38, off the path (roadmap tier 1, off-path row 1)
**Status:** discharged at conformance cut 38 on 2026-09-22; results: ../../plans/2026-09-22-conformance-cut-38-results.md

## 1. What this slice is

The act-report design names a closed enum of operation kinds and requires
that every one of them open through a boundary that appends one operation
intent before any act and closes through exactly one act-report (§3.1,
guarantee T2). Six of the eight kinds open that way today: `import` (cut 3),
`move` and `consolidate` (cut 16), `run-attempt` (cut 3), `corpus-write`
(cut 19, registration-qualified and reportless by design) and `acquisition`
(cut 35). Two do not: **`audit`** — the evaluator `audit_corpus` runs
read-only and its findings are returned to the caller and recorded nowhere
— and **`re-check`** — `holdings/boundary.py`'s `recheck` is a single
per-location act with a holdings intent of its own grain, and no operation
groups a set of re-checks under one terminal record. Cut 35 discharged T2
for `acquisition` and left it partial on exactly these two kinds
(`../../designs/2026-09-20-conformance-cut-35.md` §7 item 7).

This slice builds the two wrappers and closes T2. The T table is then full
but for T7's cross-root case, which the ledger assigns to
`cross-root-publication` (tier 3) and which this slice does not touch.
It changes no evaluator, no act, no contract and no stored codec: the
`subject-evaluation` entry kind with its `evaluation-finding` outcome and the
`pure-look` entry kind with its three outcomes have been spellable, storable
and decodable since the act-report slice landed (`report.py`, `stored.py` line 874); what is
missing is the operation that mints them. No oracle is amended, so
`contract-cut` gains nothing to freeze.

It is **off the path**: the first belief audits nothing it must report, and
mm30's holdings are five `store` observations no driver step re-checks.
Roadmap rule 6 admits it as the seventh off-path lane, and no other kernel
lane is open.

## 2. Decisions

Each decision names what it rejects. The reader checks the code against the
decision, not the prose around it.

1. **Two new modules, not two grown files.** The audit operation lands in
   `beliefs/audit_operation.py` and the re-check operation in
   `beliefs/holdings/recheck.py`. `audit.py` stays the evaluator and
   `holdings/boundary.py` stays the per-act boundary; neither is edited. The
   task record and ledger row say the wrappers *land on* `audit.py`,
   `world/audit.py` and `holdings/boundary.py`; they *consume* those
   surfaces, and the results record corrects the wording. **Rejected:**
   adding the wrapper to `audit.py`. The design's sentence "the evaluator
   acquires no write" (§4) is then checkable by module: `audit.py` and
   `world/audit.py` define no member of `WRITE_ENTRY_POINTS` and reach no
   write primitive, which BI-1 asserts statically with
   `test_permit_boundary.py`'s own helpers.

2. **The audit's subject is the observer corpus.** The `audit` operation
   runs `audit_corpus` over the writer's own read view — the corpus the
   report publishes in — after the intent. **Rejected:** wrapping
   `audit_world` at a published epoch. A `subject-evaluation` entry carries
   a bare subject; a world audit's findings are grouped per corpus, and a
   corpus-level finding's ref is a corpus id, not a record ref. The shape
   that would carry a world audit is §2.2's 2026-09-03 amendment — one intent
   and one report *per touched root* under one `event_token` — and choosing
   whether an audit at an epoch is such a composite operation, or one report
   in one root whose entries name their corpus, is a design question this
   slice files (§13) and does not settle. **Also rejected:** a wrapper
   parametrized by an evaluator callable. The evaluator surface is the
   contract; a callable parameter would let any read report as an audit.

3. **One entry per finding, in the evaluator's order, and a clean audit
   closes with no entries.** Each `Finding` the evaluator returns becomes
   one `SubjectEvaluationEntry(subject=finding.ref,
   outcome=EvaluationFinding(payload))`, in the order `audit_corpus` returns
   them (its `sort_key` order, deterministic). The payload is the v1
   canonical encoding of `{"severity", "code", "detail"}`, decoded as
   UTF-8; **`message` is excluded**, because `Finding`'s own docstring makes
   it normative for nothing, and a report's identity must not move when a
   message is reworded. An audit that finds nothing closes through a report
   whose `entries` is empty: the report is the evidence that the audit ran
   over that state and returned nothing, and T6's citations are of
   findings. **Rejected:** an entry per evaluated subject with a
   "validated" outcome. T5 reserves each kind's outcome vocabulary and
   `subject-evaluation` has one outcome, the finding; adding a second is an
   amendment the row does not need. **Rejected:** carrying `message`.

4. **The audit runs under the root lock from intent to report.** The whole
   operation — checks, intent append, evaluator read, close — runs inside
   the caller's hold (the session lock, when routed through a session) and
   then the writer's `_operation` hold, in that order, exactly as
   `import_bundle` does. The evaluator issues no request and takes no lease,
   so nothing the acquisition's decision 15 protects against applies, and
   holding the lock buys the one thing the report cannot spell: the corpus
   state the evaluator judged is exactly the state at the intent's chain
   position, because no write can land between the two. **Rejected:** the
   acquisition's take-at-close shape, whose reason does not apply here, and
   which would leave the report's subject state unnamed.

5. **The re-check operation is a set of independent store re-checks with
   no cooperative stop.** The request is a non-empty tuple of
   `StoreLocator` values with unique canonical spellings, all naming the
   bound store. Per location, in request order, the operation runs
   `holdings/boundary.py`'s `recheck` — the act as built, with its own
   holdings intent and its own published observation — and records one
   `LocatorEntry(subject=location.canonical(), outcome, instrument_inputs=())`:
   `PublishedObservation(ref)` for a published observation,
   `ByteLocatorUntested(reason)` for a `byte-locator-untested` attempt and
   `RetrievalFailed(reason)` for a `retrieval-failed` one, the attempt's
   `reason` only — its `detail` may carry a path or a message and enters no
   record. A store read has no bounds, so `instrument_inputs` is empty. An
   inconclusive location does not stop the rest: the close mints nothing
   that depends on any location, which is the whole reason the acquisition
   stops (its decision 10). **Rejected:** the acquisition's stop. **Rejected:**
   a stop on a `StoreIdMismatch`, which cannot occur after the pre-intent
   check in §4 step 1 moves the store-genesis comparison before the intent
   (decision 14 moves the rest of the act's late checks there too).

6. **The re-check's acts run outside the root lock; only its close takes
   it.** `recheck` takes the corpus lock itself for its intent append and
   its publish; the operation holds nothing across the acts and takes the
   caller's hold and then `_operation` at the close, rebuilding the view
   before any published ref resolves — `acquire`'s shape, for `acquire`'s
   reason.

7. **Both operations open exactly as §3.1 orders.** Every check that can
   refuse runs before the intent (root, port and its binding, authority,
   request validity, store genesis, observer and instrument, `standing`); the intent is appended before the first act; a refusal
   at any check or a failure of the append leaves no read, no holdings
   intent, no observation and no record; the close publishes the report as
   one registered transaction fulfilling the intent from the boundary's own
   `intent_digest`. Any failure after the intent and before the close
   propagates and leaves the operation **unfinished** (§3.3, first row);
   neither wrapper catches on the operation's behalf. **Rejected:** the
   import's catch-and-publish-a-refusal-report, whose reason (a bundle
   judged malformed after its intent) has no analogue here: the audit
   evaluator reports and never raises, and a re-check act's inconclusive
   outcome is an entry, not a failure.

8. **Two session routes, mirroring `acquire`.** `ScopedWriter.audit` and
   `ScopedWriter.recheck` route through `operation_port()` (the ledgered
   port, so the report's registration writes an `act` line) and
   `_closing_hold` (the session lock taken before the root lock, currency
   re-checked on entry). `recheck` also routes through `holdings_context`
   for the ledgered store seam, so every member act is ledgered. The audit
   route needs no store and refuses nothing a store-less session cannot
   supply. The observer of a session-routed report is the session actor,
   as `holdings_context` already binds it.

9. **Two kind-checked minting helpers in `boundary.py`.**
   `_mint_audit_report` refuses any entry that is not a
   `SubjectEvaluationEntry`, and `_mint_recheck_report` any that is not a
   `LocatorEntry`, beside the kind check on the intent that
   `_mint_acquisition_report` already makes. The per-kind entry check is
   what each helper adds; `_mint_report` stays the one constructor.
   **Rejected:** one generic `_mint_operation_report` — it would drop the
   only check the helpers exist to make.

10. **Two refusal errors, `AuditRefused` and `RecheckRefused`**, both under
    `WriteRefused` beside `AcquisitionRefused`, raised only by the
    pre-intent checks. Malformed request values raise `MalformedRecord` at
    construction, as `AcquisitionRequest` does.

11. **`root.py` stays the one `atoms` importer, and the inventories do not
    grow.** Neither module imports `atoms` or names an engine type; both
    reach the log only through `CorpusWriter._append_operation_intent`,
    `CorpusWriter._publish_operation_report` and `holdings/boundary.py`'s
    `recheck`, which are the inventoried callers. Neither wrapper calls a
    write primitive directly, so neither joins `WRITE_ENTRY_POINTS` or
    `test_permit_entry_points.py`'s `CASES` — the same standing
    `holdings/acquire.py:acquire` has. The plan's Global Constraints carry
    both obligations verbatim, and the results record states that the
    inventories were checked and found closed in both directions.

12. **The reproduction reads in place.** Step 9 of the mm30 driver
    (`tools/reproduction/close.py`) audits through the bare evaluator by its
    own contract — "Writes nothing" — and stays so; routing it through the
    wrapper would mint a report into the reproduction corpus, a change to the
    measured artifact that the reproduction lane does not make from a kernel
    lane (roadmap rule 6). Cut 38 re-runs the driver in place, appends §17 to
    the reproduction record with the same answer and `state.json`
    byte-identical, and states that the two operations are exercised only by
    the acceptance module. A driver step that audits through the wrapper is
    filed as an idea (§13).

13. **A port override is bound to the writer's root, authority and profile,
    and the primitives check it.** `OperationPort` gains a `root: Path`
    property — `DurableOperationPort` already carries `root` as an attribute
    and `LedgeredPort` forwards its inner port's — and
    `CorpusWriter._append_operation_intent` and
    `CorpusWriter._publish_operation_report` refuse (`ActorMismatch`'s
    sibling, `PortMismatch`, under `WriteRefused`) a `port` whose `root`
    does not resolve to `self.root`, whose `authority` is not equal to
    `self.authority` (a frozen dataclass; `root.py` hands both the same
    object), or whose `profile.compiled_identity` is not `self.profile`'s,
    before appending or executing anything. Without it, root B's port with root A's writer audits A while
    the intent and report land in B — the observer-corpus rule (decision 2)
    and the chain-position claim (decision 4) both fail silently. The check
    lives in the two primitives so `acquire` and every later operation get
    it, not only these two; the review found the gap here, and cut 35's
    acquisition shares it. Twenty-one test fakes that implement the protocol
    gain a `root` (the pyright count from the spike on 2026-09-22), each
    set to the writer's root they already serve. **Rejected:** checking
    `authority` and `profile` only, which the protocol already exposes — the
    root is the claim that matters and the protocol has to carry it.
    **Rejected:** verifying by effect after the append (reconstruct, look
    for the intent in the writer's chain), which leaves an orphan intent in
    the foreign root.

14. **The re-check validates every input the acts would refuse late,
    before the operation intent.** `holdings_observation` rejects an empty
    or non-encodable `observer` or `instrument` and a predecessor whose
    canonical location is not the observation's — at construction, after
    `recheck`'s holdings intent and store read. `ActContext` checks neither
    field. So the operation's step 1 checks `ctx.observer` and
    `ctx.instrument` by the observation's own rule (non-empty, encodes as
    identity text) and, for every requested location, that each member of
    its `standing` set is a `HoldingsObservation` at that canonical
    location; a `standing` key naming no requested location is refused too,
    since it can only be a caller's mistake. Any of these refuses with
    `RecheckRefused` and no intent of either grain exists. The audit has no
    analogue: it constructs no observation, and its metadata check is
    already pre-intent (§3 step 1). The per-act `recheck` keeps its late
    checks; they are unreachable from the operation.

## 3. The audit operation — `beliefs/audit_operation.py`

```python
@sealed @final @dataclass(frozen=True)
class AuditOutcome:
    report: ActReport
    report_ref: str                 # the stored node id, "act-report:<identity>"
    findings: tuple[Finding, ...]   # exactly what audit_corpus returned, in its order
    entries: tuple[SubjectEvaluationEntry, ...]  # one per finding, same order

def audit(
    writer: CorpusWriter,
    *,
    observer: str,
    instrument: str,
    evidence: DerivationEvidence,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> AuditOutcome
```

The actor is `writer.authority.actor`; no actor is supplied per call
(act-report design §3, 2026-09-04 amendment). The profile is
`writer.profile`. `evidence` is supplied, never ambient (M11, as
`import_bundle` states it).

Steps, in this order and no other:

1. **Checks, before any effect.** `writer.authority.require("corpus-write",
   ("act-report",))`. `evidence` is a `DerivationEvidence` or
   `MalformedRecord`. `observer` and `instrument` are non-empty strings and,
   with the actor, canonically encodable, or `AuditRefused` (the import's
   check, for the import's reason: a report that cannot be stored must be
   refused before it has an intent to fulfil). A `port` of `None` with a
   writer whose `_operation_port` is `None` is `AuditRefused("this corpus
   has no operation port; audit is a boundary operation")`; a supplied port
   is bound to this writer or `writer._require_bound_port(port)` refuses
   it (decision 13) — the same helper the primitives call, invoked here so
   the refusal is pre-hold; there is one comparison, not two.
2. **Enter the hold.** `hold()` if given, then `writer._operation`. Every
   later step runs inside both.
3. **Open.** `OperationIntent("audit", secrets.token_hex(16), actor)`,
   `opened_at` stamped, `intent_digest = writer._append_operation_intent(...)`.
   `_append_operation_intent` itself re-checks pins and authority; a refusal
   there leaves no intent and the operation never opens.
4. **Act.** `writer._reconstruct()`, then `findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)`.
   The reconstruct is what makes the read see the intent's chain position
   as the current head; `audit_corpus` raises nothing it documents, and
   anything it does raise propagates, unfinished.
5. **Close.** `closed_at` stamped; entries built per decision 3;
   `report = boundary._mint_audit_report(intent, observer=..., instrument=...,
   opened_at=..., closed_at=..., entries=entries)`;
   `writer._publish_operation_report(report, intent_digest, port=port)`,
   which re-checks pins and authority, executes the one fulfilling
   transaction and reconstructs. Return `AuditOutcome`.

The payload builder is one private function,
`_finding_payload(finding) -> str`, returning
`v1.encode({"severity": ..., "code": ..., "detail": ...}).decode("utf-8")`.
A `LoneSurrogate` raised by `v1.encode` on a finding's detail propagates:
the finding exists, the report cannot carry it, and the operation is
unfinished rather than misreported. (No evaluator finding today carries a
detail the canonical encoder refuses; the branch is stated so the reader
knows it was not overlooked.)

## 4. The re-check operation — `beliefs/holdings/recheck.py`

```python
@sealed @final @dataclass(frozen=True)
class RecheckOutcome:
    report: ActReport
    report_ref: str
    entries: tuple[LocatorEntry, ...]           # one per location, request order
    results: tuple[ActResult, ...]              # recheck's own results, same order

def recheck_locations(
    ctx: ActContext,
    writer: CorpusWriter,
    locations: tuple[StoreLocator, ...],
    *,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> RecheckOutcome
```

`standing` maps a canonical location to the observations the new one
supersedes, as `acquire` takes it. Steps:

1. **Checks, before any effect.** `locations` is a non-empty tuple of
   `StoreLocator` values (`MalformedRecord` otherwise) with unique canonical
   spellings (`RecheckRefused`). `ctx.authority.require("holdings",
   ("holdings-observation",))` and `ctx.authority.require("corpus-write",
   ("act-report",))`. `writer.root` resolves to `ctx.observer_root` or
   `RecheckRefused` (one root). Port present or `RecheckRefused`. The bound
   store's genesis is read once through `ctx.seam.store_genesis` and every
   location's `store_id` must equal it, or `RecheckRefused` naming the first
   that does not — the comparison `recheck` makes after its read, moved
   before the intent so that no location can refuse mid-operation.
   `ctx.observer` and `ctx.instrument` are non-empty and encode as identity
   text, and every `standing` entry is a `HoldingsObservation` at a
   requested canonical location, or `RecheckRefused` (decision 14). A
   supplied port is bound to this writer, by
   `writer._require_bound_port(port)` (decision 13).
2. **Open.** `OperationIntent("re-check", token, ctx.actor)`, `opened_at`,
   `intent_digest = writer._append_operation_intent(...)`.
3. **Acts, in request order, nothing held across them.** For each
   location, `result = recheck(ctx, location, standing=standing.get(canonical, ()))`.
   A `PublishedObservation` records
   `LocatorEntry(canonical, PublishedObservation(f"holdings-observation:{result.record.identity()}"))`;
   an `InconclusiveAttempt` records `ByteLocatorUntested(result.reason)` or
   `RetrievalFailed(result.reason)` by its `report` value. Any exception
   propagates: the operation is unfinished, and the location's own
   holdings intent stays whatever the act left it.
4. **Close.** `closed_at`; `hold()` then `writer._operation`;
   `writer._reconstruct()`; every published ref must resolve in
   `writer.read_view` or `RecheckRefused` ("the report would reference an
   observation no act published" — `acquire`'s check, for `acquire`'s
   reason: the act published through the holdings seam past this writer's
   cached index); `report = boundary._mint_recheck_report(...)`;
   `writer._publish_operation_report(report, intent_digest, port=port)`.

`recheck`'s three inconclusive branches map exactly: `ReadNotAttemptedView`
→ `byte-locator-untested` (no read began: T5's territory for the untested
spelling); `ReadUnestablishedView` and a non-regular final state →
`retrieval-failed` (an attempt began). `recheck` does not change.

## 5. The session routes — `session/writer.py`

```python
def audit(self, *, instrument: str, evidence: DerivationEvidence) -> AuditOutcome:
    return run_audit(self._writer, observer=self._session.actor, instrument=instrument,
                     evidence=evidence, port=self.operation_port(), hold=self._closing_hold)

def recheck(self, locations, *, instrument: str, standing=None) -> RecheckOutcome:
    ctx = self.holdings_context(instrument=instrument)
    return recheck_locations(ctx, self._writer, locations, standing=standing,
                             port=self.operation_port(), hold=self._closing_hold)
```

Both are invocation-scoped like `acquire`; `_closing_hold` takes the
session lock before the root lock and re-checks currency, and the ledgered
port's `execute_fulfilling` re-enters the same `RLock`. For the audit the
hold spans the whole operation (decision 4), so the session lock is held
across the evaluator read — a read of the writer's own index, no I/O
outside the root — and the docstring says so. A store-less session can
`audit` and cannot `recheck` (`holdings_context` refuses, as today).

## 6. `boundary.py`, `errors.py`, `runrecord.py`, `corpus.py`

- `_mint_audit_report(intent, *, observer, instrument, opened_at, closed_at, entries)`:
  `intent.kind == "audit"` and every entry a `SubjectEvaluationEntry`, or
  `MalformedRecord`.
- `_mint_recheck_report(...)`: `intent.kind == "re-check"` and every entry a
  `LocatorEntry`, or `MalformedRecord`.
- `AuditRefused(WriteRefused)`, `RecheckRefused(WriteRefused)` and
  `PortMismatch(WriteRefused)`, beside `AcquisitionRefused` and
  `ActorMismatch`, with `errors.py`'s catalogue entries and `test_errors_*`
  parity where the existing refusals have it.
- `runrecord.py`: `OperationPort.root`. `session/routes.py`:
  `LedgeredPort.root` forwards. `corpus.py`: the two primitives' binding
  check (decision 13), one private `_require_bound_port` shared by both
  primitives and called by both wrappers' preflights — the one place the
  comparison is spelled.

## 7. What does not change

`audit.py`, `world/audit.py`, `holdings/boundary.py`, `report.py`,
`stored.py`, both `CONTRACT.yaml` copies, the TypeScript parity artifact,
`intents/shapes.py`, `completion`, and the reproduction driver. The
operation-kind enum stays at eight. `_append_operation_intent` and
`_publish_operation_report` change only by the binding check of decision
13, ahead of every effect. No design guarantee outside T2 changes its
evidence; T5 and T6 are read by the acceptance module where the new kinds
give them a new instance, and T3 and T4 by plain acceptance tests that
declare no unit (§9.2).

## 8. Shared files, under roadmap concurrency rule 3

Rewritten by every lane and therefore by this one: `errors.py`, the ledger,
the roadmap, `docs/guide/open-questions.md` (the act-report paragraph's
"what remains unbuilt" sentence), `python/tests/test_designs_corpus.py` where
the new spec, plan and cut documents register. Named beyond those:
`session/writer.py`, `session/routes.py`, `boundary.py`, `corpus.py` and
`runrecord.py` (the first four in the `acquisition` lane's column, which
closed at cut 35, `corpus.py` in this lane's own, and none in an open
lane's), the test modules whose port fakes gain `root` (§9.1), `README.md`
(the cut count). No file in `world/verify.py` or `root.py` — cut 37's rewrites —
is touched, so the shared-surface note on `beliefs-86b150` resolves with
nothing to resolve toward. No other lane is open.

## 9. Testing and the cut

### 9.1 Unit — `test_audit_operation.py`, `test_holdings_recheck.py` (new), `test_session_writer.py`, `test_operation_port.py`, `test_corpus_write.py`

Portable, over a fake operation port (the `RefusingPort` / recording-port
shape `test_holdings_acquire.py` uses) and a certified-tuple-free writer:

- the happy path: one intent appended, the evaluator invoked after the
  append returns (a recording port and a monkeypatched `audit_corpus` share
  one event list), one report published fulfilling that intent, `completion`
  reads `closed`; entries equal the findings mapped per decision 3, in
  order; a clean corpus yields an empty `entries`;
- `_finding_payload` excludes `message`: two findings equal but for
  `message` give equal entries, and one report identity under a fixed
  envelope through `_mint_audit_report`; two findings differing in
  `detail` give two entries;
- every pre-intent refusal (no port, a port bound to another root,
  authority or profile, actor/observer/instrument unencodable, authority
  lacking `act-report`, evidence of the wrong type) appends nothing,
  invokes the evaluator zero times, publishes nothing;
- an evaluator exception after the intent propagates, the intent stays
  unmatched, `completion` reads `unfinished`;
- the hold enters before the root lock and spans the evaluator call;
- re-check: N locations → one operation intent, then N holdings intents and
  their observations in chain order, then the report; entries per decision
  5; an inconclusive location is an entry with `reason` only and the
  operation still closes; duplicate spellings, a foreign `store_id`, a
  writer on another root, a port-less writer, a foreign-root port, an empty
  or non-encodable observer or instrument, a `standing` predecessor at
  another location and a `standing` key naming no requested location each
  refuse pre-intent with no intent of either grain appended; a `standing`
  head is superseded by the new observation; the close rebuilds the view
  before resolving; a published ref the view cannot resolve refuses at the
  close;
- `_mint_audit_report` and `_mint_recheck_report` refuse the wrong intent
  kind and the wrong entry kind;
- the primitives: `_append_operation_intent` and
  `_publish_operation_report` refuse a port whose root, authority or
  profile is not the writer's, before any effect on either root
  (`test_corpus_write.py`); `LedgeredPort.root` is its inner port's
  (`test_operation_port.py` or `test_session_routes.py`, whichever holds
  the port's forwarding tests today); the fakes in the modules the spike
  named gain `root`;
- the session routes ledger an `act` line per committed transaction and
  refuse after the invocation closes.

### 9.2 Acceptance — `test_act_report_remainder_acceptance.py` (new)

On the certified tuple, one arm per declaration unit, each ending
`_durably`. Twelve units over three guarantee rows (T2, T5, T6) and three
boundary invariants:

| unit | row | assertion |
|---|---|---|
| T2-e | T2 | audit to success: one intent, one qualifying report, `closed`; the intent's chain position precedes the report's registration and the evaluator ran between the two |
| T2-f | T2 | re-check to success over two locations: one operation intent, two holdings intents each fulfilled by its observation, one report, `closed`; the operation intent precedes every holdings intent in the chain |
| T2-g | T2 | root selection (another root's writer), a port-less writer, a refusing port and a foreign store each begin no act for both kinds: no read, no holdings intent, no observation, no record — the audit, which selects no root and names no store, reads the port-less writer under those two arms |
| T2-h | T2 | an audit and a re-check each submit **exactly one** fulfilling execution (a counting port over the durable one records every `execute_fulfilling` call); a second `execute_fulfilling` on the audit intent by the test is refused by the coordinator, and a raw second fulfilment reads `MalformedView` `duplicate-fulfillment` (cut 35's T2-d, for the new kind, with the count added because a swallowed second close is invisible to the other two assertions) |
| T2-i | T2 | a port bound to another root, with the writer's authority and profile, is refused by both operations before any intent: both roots' chains are unchanged |
| T2-j | T2 | an empty instrument, a non-encodable observer, a predecessor at another location and a `standing` key for an unrequested location each refuse the re-check before the operation intent, with no holdings intent appended and no store read (the seam records zero reads) |
| T5-d | T5 | an inconclusive re-check location spells `byte-locator-untested` for a not-attempted read and `retrieval-failed` for an unestablished one, reasons distinct, and neither outcome constructs an observation |
| T6-d | T6 | `cite(report, i)` resolves the i-th finding in the evaluator's order; permuting two entries moves the identity; index out of range refuses |
| T6-e | T6 | two audits over corpora whose findings differ only in `message` return equal `entries` tuples, and `_mint_audit_report` over each tuple under one fixed envelope (one intent value, one `opened_at`/`closed_at`, one observer and instrument) yields one identity; two whose findings differ in `detail` return unequal entries and two identities. The live reports' own identities differ regardless — T8, distinct tokens — and are not compared |
| BI-1 | — | `audit.py` and `world/audit.py` define no `WRITE_ENTRY_POINTS` member and reach no write primitive; the wrappers reach the log only through inventoried callers |
| BI-2 | — | the audit's evaluator read runs under the root lock after the intent: a write raced against an open audit lands after the report's registration |
| BI-3 | — | the session routes: an audit and a re-check through `ScopedWriter` each write one `act` line per committed transaction, and the report's observer is the session actor |

Plain acceptance tests, declaring no unit and claiming no row (T3's and
T4's rules, both already closed, read where the new kinds give them an
instance): deleting the published audit report moves its operation
`closed → indeterminate`, never unfinished; over a fixed observation set,
with both reports present, then one, then none, then an unmatched audit
intent, the holdings reducer outputs and the corpus's audit findings never
move and nothing blocks; and over a belief-bearing corpus the two reports
leave the answer, its `belief_input_digest` and its traced admission
byte-unchanged, added and removed.

### 9.3 N2 sabotages — `n2_arms_cut38.py`

Every declaration unit carries at least one sabotage the unit's check must
catch; fourteen arms over twelve units:

| arm | unit | sabotage |
|---|---|---|
| T2-e | T2-e | the evaluator read moved before the intent append |
| T2-f | T2-f | the operation intent appended after the first `recheck` act |
| T2-g1 | T2-g | the re-check's one-root check dropped, so the wrong-root arm appends the operation intent in one root and then runs a member act in the other |
| T2-g2 | T2-g | the append failure caught and the acts proceeding |
| T2-g3 | T2-g | the store-genesis check moved after the intent |
| T2-h | T2-h | the close publishing twice under one intent, swallowing the refusal — caught by the submission count, not by the coordinator's refusal |
| T2-i | T2-i | `_require_bound_port`'s root comparison removed — the one helper both primitives and both preflights call, so no second check survives it |
| T2-j | T2-j | the observer/instrument/`standing` validation moved after the intent |
| T5-d | T5-d | an inconclusive location dropped from the entries |
| T6-d | T6-d | the entries built in reverse evaluator order |
| T6-e | T6-e | `message` admitted into the payload |
| BI-1 | BI-1 | a write-primitive attribute call inserted into `audit_corpus` |
| BI-2 | BI-2 | the root lock released before the evaluator call |
| BI-3 | BI-3 | the session route bypassing `operation_port()` for the writer's raw port |

Declared accounting: 14 arms, 12 units, 3 rows. The staleness probe
re-targets nothing: cut 37's live guard stays chained as the highest live
runner.

### 9.4 The cut

`docs/designs/2026-09-22-conformance-cut-38.md` frozen after review;
`tools/cut38_acceptance.py` with `PREFIX_RUNNERS = ("cut37_acceptance.py",)`
and `PHASE_MODULES = ("test_act_report_remainder_acceptance.py",
"test_n2_cut38.py")`; the `test_recent_cut_acceptance.py` row with the
declared arm, unit and guarantee-row counts and the runner's
guarantee-rows-exercised line; the results record
`docs/superpowers/plans/2026-09-22-conformance-cut-38-results.md`. The
acceptance roots sit under the main checkout's `.work/acceptance/cut38`.

### 9.5 Frozen evidence and live tests

The cut doc's arm table is the frozen body; the acceptance and N2 modules
are live. A finding after the freeze is recorded in the results record and
the cut doc is superseded by citation, never edited.

## 10. Documentation amendments

- Act-report design §3.1: an "Amended 2026-09-22 (cut 38)" note beside cut
  35's, stating the two operations as built and that every kind but
  `corpus-write` now opens through a boundary and closes through exactly one
  terminal record — the `run` where one is minted, the act-report otherwise.
- Ledger: T2 closes; `act-report-remainder` leaves `Current state`; the T
  table reads full but for T7's cross-root case, which stays with
  `cross-root-publication`; the row's "unblocks: the T table in full" is
  corrected to say so.
- Roadmap: re-ranked at cut 38; `act-report-remainder` leaves the index and
  off-path row 1; `publish` moves from tier 2 to tier 1 off the path (its
  world-read prerequisite is discharged; the criterion needs no publish),
  and the `world-read` lane's head becomes `publish`.
- `docs/guide/open-questions.md`: the act-report paragraph's "what remains
  unbuilt" sentence becomes a statement that the enum is built through, and
  the world-scope audit question (§13) is filed under contracts and
  adoption.
- Reproduction record §17.
- `README.md` cut count.

## 11. Task linkage

`beliefs-86b150` carries the spec (`--spec act-report-remainder`) and the
plan; the plan's `### Task N:` headings become its children, each rated and
processed explicitly. The results record closes the task in the commit that
adds it.

## 12. Limitations

1. **No world-scope audit operation.** Decision 2; filed (§13).
2. **No scheduler.** Act-report design §4's sub-problem 6 stays excluded.
3. **The audit report does not spell the corpus-state identity it judged**;
   the intent's chain position names it under decision 4. A report member
   for it is an amendment nobody has asked for.
4. **A re-check location's `detail` is dropped** from the entry; the
   holdings intent and the seam's own view keep it where they keep it today.
5. **The reproduction does not exercise either operation** (decision 12).

## 13. Open questions this slice files

- *Idea:* a world-scope audit operation — one report per touched root under
  one token (§2.2's composite shape), or one report whose entries name
  their corpus; either is an act-report design amendment.
- *Idea:* a reproduction driver step that audits through the wrapper and
  keeps the report in the measured corpus.

## 14. Review log

- 2026-09-22 — drafted.
- 2026-09-22 — first review, four findings, all taken: a port override is
  now bound to the writer's root, authority and profile and checked in the
  primitives (decision 13, `OperationPort.root`); the re-check validates
  observer, instrument and every `standing` set before the operation intent
  (decision 14); the mutation mapping is complete — every unit has a
  sabotage, T2-i, T2-j and T6-e added, T3-e and T4-e demoted to plain tests
  (§9); the T table stays open on T7's cross-root case (§1, §10).
- 2026-09-22 — second review, three findings on test definitions, all
  taken: T6-e compares entries and mints under a fixed envelope, since T8
  separates two live reports by token; the port-binding comparison is
  spelled once in `_require_bound_port`, which both preflights call, so
  T2-i's sabotage kills every check; T2-h counts fulfilling submissions,
  since a swallowed second close leaves one fulfilment.
- 2026-09-22 — at planning: T2-g gains the foreign-store arm, so T2-g3's
  sabotage (the store-genesis check moved after the intent) has a check
  that sees it; the plan's self-review found the gap.
- 2026-09-22 — at planning, second review: T2-g1's sabotage becomes the
  dropped one-root check, since removing the wrapper's port check alone
  still refuses before any act (the primitive's own binding check catches
  it) and would be detected only by the exception type; the plan's
  declaration table and this one now agree, which is what Task 0 freezes
  from. T3's and T4's plain tests are stated in §9.2 below: T4 snapshots
  with both reports present before deleting either, and reads the belief
  answer, its digest and its traced admission over a belief-bearing
  corpus, not only the holdings projection.
