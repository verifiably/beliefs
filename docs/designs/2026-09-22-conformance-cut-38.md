# Conformance cut 38 — the act-report remainder

**Status:** frozen 2026-09-22, before implementation; T2 is open
**Design:** `../superpowers/specs/2026-09-22-act-report-remainder-design.md`, approved for implementation planning 2026-09-22 at `f43e236` after two reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-22-act-report-remainder.md`.
**Numbered after** cut 37 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 38–39 at freeze; cut 37 is the highest discharged runner.

## 1. What this cut is

The act-report design requires every operation kind to open through a
boundary that appends one operation intent before any act and to close
through exactly one act-report. Six of the eight kinds open that way
today: `import`, `move`, `consolidate`, `run-attempt`, `corpus-write`
(registration-qualified and reportless by design) and `acquisition`. Two
have no boundary at all — `audit`, whose evaluator runs read-only and
whose findings are returned to the caller and recorded nowhere, and
`re-check`, whose per-location acts carry a holdings intent of their own
grain and are grouped by no operation. This cut builds the two
wrappers — the audit over the writer's own corpus under the root lock,
the re-check over independent store re-checks — binds every supplied
operation port to its writer, and closes T2. The T table is then full
but for T7's cross-root case, which stays with `cross-root-publication`.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/audit_operation.py` (new),
  `python/src/beliefs/holdings/recheck.py` (new), `boundary.py`,
  `corpus.py`, `runrecord.py`, `session/routes.py`,
  `session/writer.py`, `errors.py`;
- the test modules whose port fakes gain `root`;
  `python/tests/test_operation_port_binding.py`,
  `test_audit_operation.py`, `test_holdings_recheck.py`,
  `test_session_routes.py`;
- `python/tests/acceptance/test_act_report_remainder_acceptance.py`,
  `python/tests/n2_arms_cut38.py`,
  `python/tests/acceptance/n2_arms_cut38.py`,
  `python/tests/acceptance/test_n2_cut38.py`,
  `python/tools/cut38_acceptance.py`;
- this cut, the ledger, roadmap, guide, README, the act-report design's
  §3.1 amendment note.

`audit.py`, `world/audit.py` and `holdings/boundary.py` are consumed and
not edited. Frozen declarations and cut bodies through cut 37 remain
byte-exact; no prior live arm pins a line this cut moves.

## 3. Selection

Twelve declaration units are selected and single-homed here. The quoted
row text is byte-exact from `2026-08-11-act-report-design.md` at freeze.

```markdown
| **T2** | One started operation, one intent, one terminal record — and no act precedes the intent | Run each operation kind to success; assert exactly one qualifying fulfillment: the `run` where one is minted, the act-report otherwise. **Positive:** a post-intent attempt that mints no run closes through **exactly one** qualifying act-report. Attempt a second fulfilling registration on one intent → **malformed**, the log's rule as built. Make root selection fail, then the intent append fail; assert in each case **no act began** — no request issued, no lease taken, **no record minted** (an `event_token` generated in memory and carried by no intent and no record is not a mint). **Negative (a):** a missing-spec run request refuses **pre-intent**; assert a surviving boundary publishes an *unfulfilling* act-report, that it fulfills nothing, and that a crash there leaves no trace. **Negative (b):** a complete non-conforming execution mints a **run**, never an act-report. **Negative (c):** a dataset-production attempt opens the **operation intent** — assert the assessment-run intent cannot be spelled without a `spec_identity` |
```

| unit | row | what it reads |
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

### 3.2 Rows not read

**T7** is not read; its cross-root case is `cross-root-publication`'s
(`beliefs-256f17`, tier 3). **T3** and **T4** are already closed and are
exercised by two plain acceptance tests that declare no unit and claim
no row. **T1** and **T8** are not read. T2, T5 and T6 are read: T2 in
full, T5 and T6 for the instance the new kinds give them.

## 4. Accounting

**12 declaration units**, nine against T2, T5 and T6 and three boundary
invariants; T2 closes; the T table stays partial on T7 alone. 187 of 216
→ 188 of 216.

## 5. N2 and acceptance obligations

| arm | module | sabotage | check |
|---|---|---|---|
| T2-e | `audit_operation.py` | the evaluator read moved before the intent append | T2-e |
| T2-f | `holdings/recheck.py` | the operation intent appended after the first `recheck` act | T2-f |
| T2-g1 | `holdings/recheck.py` | the re-check's one-root check dropped, so the wrong-root arm appends the operation intent in one root and then runs a member act in the other | T2-g |
| T2-g2 | `audit_operation.py` | the append failure caught and the acts proceeding | T2-g |
| T2-g3 | `holdings/recheck.py` | the store-genesis check moved after the intent | T2-g |
| T2-h | `audit_operation.py` | the close publishing twice under one intent, swallowing the refusal — caught by the submission count, not by the coordinator's refusal | T2-h |
| T2-i | `corpus.py` | `_require_bound_port`'s root comparison removed — the one helper both primitives and both preflights call, so no second check survives it | T2-i |
| T2-j | `holdings/recheck.py` | the observer/instrument/`standing` validation moved after the intent | T2-j |
| T5-d | `holdings/recheck.py` | an inconclusive location dropped from the entries | T5-d |
| T6-d | `audit_operation.py` | the entries built in reverse evaluator order | T6-d |
| T6-e | `audit_operation.py` | `message` admitted into the payload | T6-e |
| BI-1 | `audit.py` | a write-primitive attribute call inserted into `audit_corpus` | BI-1 |
| BI-2 | `audit_operation.py` | the root lock released before the evaluator call | BI-2 |
| BI-3 | `session/writer.py` | the session route bypassing `operation_port()` for the writer's raw port | BI-3 |

That makes **14 arms over 12 units** (T2-g homes three; every other unit
one). Both directions are required: the check passes on the real tree
and fails under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut37_acceptance.py",)` and carries
`PHASE_MODULES = ("test_act_report_remainder_acceptance.py", "test_n2_cut38.py")`.

## 6. Second reader

Check that T2-e's ordering proof reads the evaluator's invocation from a
recording seam and the intent's position from the chain, not from
timestamps; that T2-i's foreign port carries the writer's own authority
and profile so only the root differs; that T2-j's "zero reads" is read
from the store seam's `read_path` counter and not inferred from the
chain; that T6-e's two entry tuples come from two evaluator returns that
differ in `message` alone, and that the fixed envelope is one
`OperationIntent` value reused for both mints; that BI-2's racing write
is a real `writer.add` on another thread that blocks on the root lock
(its registration lands after the report's); that BI-1's static
assertion uses `test_permit_boundary.py`'s own `primitive_callers` over
the two evaluator modules.

## 7. Limitations

1. **No world-scope audit operation** (spec §12.1); filed as an open
   question.
2. **No scheduler**: the act-report design §4's sub-problem 6 stays
   excluded (spec §12.2).
3. **The audit report does not spell the corpus-state identity it
   judged**; the intent's chain position names it (spec §12.3).
4. **A re-check location's `detail` is dropped** from the entry; the
   holdings intent and the seam's own view keep it where they keep it
   today (spec §12.4).
5. **The reproduction exercises neither operation** (spec §12.5).
