# Conformance cut 19 — the writer session

**Status:** Frozen 2026-09-05, before implementation. Not yet discharged.

**Sources:** `2026-09-05-writer-session-design.md` §2–§8, in particular §3
(the session and its ledger), §4 (the `corpus-write` operation and the
commit seam), §5 (the scoped writer), §6 (reconciliation) and §7 (the `J`
table), and the frozen `J` rows quoted below.

## 1. What this cut is

Cut 19 is the frozen acceptance boundary for the writer session: the attended
session and its fixed actor, the append-then-fsync session ledger and its
claim protocol, the invocation-bound scoped writer whose effective permit is
exactly its requirement, every session-mediated ordinary write as one
`corpus-write` operation intent fulfilled by its registration, the
unresolved-root discipline that settles before every prepare, and
reconciliation over ledgers and chains. The selection was frozen before
implementation, after six review rounds of the design.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. The `J` table is new, so no prior evidence exists and every
row is selected in full.

## 2. The boundary

In scope:

- `beliefs.session`: `open_attended_session` with its refusals (one corpus
  root, adopted, registered, well-formed chain; the optional coordination
  profile), the session identity and actor, `scoped(required,
  invocation_id)`, `claim_invocation`, `close_invocation`,
  `invocation_acts`, `close`, and the `LedgerFailed` terminal state;
- the ledger file: its five line kinds, canonical encoding, write-flush-fsync
  order before the index update, the reader, torn tails and malformed lines;
- `CorpusWriter.operations` and its seven methods, the shared prepare
  helpers, the single commit seam and its order — require, prepare,
  preflight, intent, fulfilling execution, rebuild — `PlanRefused`, and the
  `unresolved` flag with `_locked()` settlement on every path, `import_bundle`,
  `adopt_manifest` and the relocation acts included;
- `OperationPort.preflight`, `execute_fulfilling`'s registration-digest
  return, and the durable factory's `recover(root)`;
- the `corpus-write` operation kind and its qualification by the fulfilling
  registration in both reductions;
- `session.reconcile` over `ChainView`s and `LedgerEvidence`, its finding
  codes, and `root.reconcile_sessions` under the corpus operation lock
  through detached inspection;
- the static write inventory's 37th row.

Out of scope:

- the dispatcher, renderer, cursors and every surface (`science`);
- run, holdings and import acts through the scoped writer;
- multi-corpus write targeting;
- the run-session constructor, the actor sandbox and the endpoint handle;
- `publish`;
- reads that recover (`read_view` between a failure and the next write);
- cross-process coherence beyond the single-writer deployment obligation.

## 3. Selection

### J1 — closes

```markdown
| **J1** | Every session-mediated ordinary write is exactly one `corpus-write` intent under the session actor followed by exactly one committed registration fulfilling it; the intent qualification reads `matched` and completion reads `closed`; a refused write — permit, family, plan shape, or record ceiling — appends nothing of its own: the chain head after the refusal equals the head after settlement, where settlement may have appended the engine's recovery entries for a *prior* operation and never an intent or registration of the refused one; and every refusal an ordinary method makes, its operation twin makes | Through a real attended session over a registered root, for each of the seven scoped methods: assert the chain grew by one intent (decoded kind `corpus-write`, actor `session:<id>`) and one registration whose `fulfills` is that intent's digest; run `qualify_chain` and `completion` and assert `matched`/`closed`, `delete` included, whose registration publishes no record. Refuse each method under a permit lacking the kind, with a malformed record under the full permit, with a record over `RECORD_CEILING`, and — for `add` — with a retraction and with an act-report; assert the head equals the head read after `_settle` (taken by a settled, non-writing probe before the refused call), that no intent decodes to the refused call's kind and token, and, for the retraction, that the refusal equals `add`'s own; repeat one refusal on a root left unresolved by a prior failed submission and assert the head moved only by recovery's settlement of that prior work. **Negative:** the same seven through the ordinary `CorpusWriter` methods append no intent |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_session_acceptance.py` for the seven scoped writes, the qualification and completion readings and the head equality after settlement; `test_operation_writes.py` for the refusal-before-intent arms — permit, malformed record, record ceiling, retraction and act-report through `add` — over the in-memory executor and a synthetic-digest port.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J2 — closes

```markdown
| **J2** | Intent precedes effect, and the promise is bounded by submission: a failure after the intent and before the plan is submitted leaves an unfulfilled intent and no record; a failure after submission leaves the invocation's outcome unknown until inspected, and two consequences follow separately: root consistency — a failure of the engine, the readback, or the rebuild leaves the root unresolved until settled, while a ledger-append failure, which follows a completed rebuild, does not — and invocation outcome — the seam's failures surface as `ExecutionError` and the ledger append's as `SessionLedgerFailed`, never as a refusal, and reconciliation classifies the intent and any registration it finds by §6's table (`session-outcome-unknown` for a committed or absent registration under the open invocation, `session-entry-pending` for an unsettled one) from the chain, not the exception | Fault `execute_fulfilling` before it submits; assert `ExecutionError`, one intent, no registration, no record file, one `session-outcome-unknown` on the intent digest. Fault the registration readback after the commit; assert `ExecutionError`, the record durable, the registration committed, no `act` line, `unresolved` still set (the view **not** rebuilt), and one `session-outcome-unknown` on the registration digest; then assert the next write on that root settles first and sees the record. Fault `_reconstruct` after a successful commit and assert the same flag state and the same settlement on the next write. Fault the ledger append after the commit; assert `SessionLedgerFailed`, the record durable, the registration committed, no `act` line, and one `session-outcome-unknown` on the registration digest. **Fresh process:** leave a root with a staged, unsettled transaction, open a session over it in a new process (the chain is well-formed with pending work), and assert the first scoped write runs recovery and rebuilds before its prepare — the staged file is gone before the prepare reads. **Library writer and the other paths:** commit a session `delete` whose readback fails, then through an `open_corpus` writer over the same root run `import_bundle` with a member deriving from the deleted record and a relocation `move` of it; assert each settled first and refused against the rebuilt index, never validated against the stale one. **Mixed handles:** after a failed session submission that leaves a staged file, construct `CorpusWriter(root, durable_executor_factory(), authority=FULL)` with no operation port over the same root and `add` a record; assert recovery ran (the staged file is gone, the chain shows the rollback) before its prepare and that the flag cleared only then; assert the root state's `recover` is the durable factory's and that a `DefaultExecutor` root's is `None`. **Continuation after unresolved effects:** fault the engine after it has staged the record file but before commit; assert `ExecutionError` and `unresolved`; then, through the same session, `retract` a retraction naming that record — assert recovery ran first (the staged file is gone, the chain shows the rollback), the view was rebuilt, and the retraction is refused `RelocationTargetMissing`, never committed; then a fresh `add` succeeds and clears the flag. Fault recovery itself and assert the flag stays set and the next write raises `ExecutionError` before any prepare. Raw-write the target path between prepare and execute so the engine's precondition fails; assert `ExecutionError` and that reconciliation, not the test, says whether a registration stands. **Negative:** fault `append_intent` itself and assert no intent and no record — nothing to reconcile; `PlanRefused` from preflight appends no intent |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_session_acceptance.py`: the pre-submission fault, the readback fault, the rebuild fault, the ledger-append fault, the raced precondition, the fresh-process case (a staged transaction left by one process and the first scoped write of another), the library-writer continuation through `import_bundle` and `move`, and the mixed-handle continuation through a portless durable writer.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J3 — closes

```markdown
| **J3** | The scoped writer's effective permit is exactly the requirement: an act outside it is `PermitExceeded` raised by the kernel entry point under a full-permit session with nothing written, and `scoped` refuses an uncovered requirement before any writer exists | `scoped(for_kinds({"proposition"}, {}))` then `add(source)` → `PermitExceeded(("kind", "source"))`, head unchanged, no `act` line; `scoped(coordination())` then `add(proposition)` → refused on `proposition`; a requirement covered by the ceiling under a session whose ceiling is narrowed in test → `PermitExceeded` from `scoped`, `_root_state_for` untouched. **Negative:** the same acts under a requirement that names them are minted, and `PermitExceeded.capability` is the *requirement's* summary at the act and the *ceiling's* at `scoped` |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_operation_writes.py` and `test_session_writer.py` over the in-memory executor: act-time `PermitExceeded` from the entry point under a full-permit session, `scoped`'s declaration-time refusal under a test-narrowed ceiling, and the `capability` field's two summaries.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J4 — closes

```markdown
| **J4** | The actor is session-fixed: every intent a session write appends carries `session:<id>`, no session or scoped method accepts an actor, and a retraction whose facet names another actor is `ActorMismatch` with nothing written | Decode every intent after a run of scoped writes and assert the actor; inspect every public signature on `WriterSession`, `ScopedWriter` and `OperationWrites` for an `actor` parameter and assert none; `retract` a retraction naming `someone-else` → `ActorMismatch`, head unchanged. **Negative:** the same retraction with the session actor is minted |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_operation_writes.py`: decoded intent actors, the signature inspection over `WriterSession`, `ScopedWriter` and `OperationWrites`, and the retraction `ActorMismatch` arm.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J5 — closes

```markdown
| **J5** | Every `act` line carries the registration digest the chain holds and the exact minted identities, and is durable before the write returns and before the root's operation lock releases | After each scoped write, read the ledger back and assert the last `act` line's `entry` equals the registration digest `read_chain` reports for the intent and its `records` equal `[(node.uid, node.id)]` (or `[]` for delete); assert the file's byte length grew before the method returned (a wrapped `os.fsync` observed once per line); observe the lock from a second thread and assert it is held from before the commit until after the append. **Negative:** an `act` line written with a fabricated `entry` is what `session-act-unverified` catches (J8) |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_session_acceptance.py`: the `act` line read back against `read_chain`'s registration digest, the fsync observation per line, and the lock observed held from before the commit to after the append.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J6 — closes

```markdown
| **J6** | The claim protocol is exhaustive and fail-closed: the four outcomes of §3.3 exactly, a `ClaimDone` outcome replayed whole (refusal envelope included), an abandoned invocation left open and never blocking a later fresh claim, and every protocol violation a hard error with nothing appended | Drive the table: fresh → open line; same id, same command and digest after close → `ClaimDone` with the identical persisted mapping, for a `done` and for a `refusal` outcome; different digest → `ClaimMismatch`; different command → `ClaimMismatch`; open without close → `ClaimOpen`; a second fresh id while one is open → `ClaimFresh`, the earlier still open, the new one current; `close_invocation` of the abandoned id → `SessionProtocolError`; `close_invocation` of the current id → closed; a malformed outcome → `ValueError`, invocation still current. Assert the returned value's type is one of the four sealed classes in every case. **Negative:** eight threads claiming one fresh id under an external lock see one `ClaimFresh` and, after close, seven `ClaimDone`; an oversized record through the scoped writer is `PlanRefused`, a `WriteRefused`, and its invocation closes with a refusal envelope rather than staying open |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_session_ledger.py` over a temporary directory: the claim table, the abandoned-invocation continuation, the protocol errors, the malformed outcome, the eight-thread claim, and the `PlanRefused` closing envelope.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J7 — closes

```markdown
| **J7** | Every ledger line is appended and fsynced before its call returns and before the index records it, the encoding is canonical JSON lines, the reader refuses a malformed line and reports a torn tail, and a ledger I/O failure ends the session with the file preserved as the failure left it | Wrap `os.fsync` and assert one call per line for every line kind; parse each line with a strict decoder and assert `sort_keys` order and no whitespace; truncate a ledger mid-line → `torn_tail` true and every complete line read; corrupt a middle line → `LedgerMalformed` naming its number; a first line that is not `session-open` → `LedgerMalformed`. Fault `write` after part of a line → `SessionLedgerFailed`, the index unchanged, the next `claim_invocation` and `close` → `SessionLedgerFailed`, the file's bytes exactly the partial line, the reader reporting a torn tail with every earlier line intact; fault `fsync` after a complete line → the same, and the claim the line would have recorded is absent from the index. **Negative:** a valid ledger round-trips through the reader to the same `InvocationRecord`s the session's index holds; a handler's `WriteRefused` leaves the session usable |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_session_ledger.py` with a wrapped `os.fsync` and faulted `write`: canonical encoding, the torn tail, the malformed interior line, the partial-write and failed-fsync terminal states with their preserved bytes.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J8 — closes

```markdown
| **J8** | Reconciliation classifies every actor-matching chain entry into exactly one of §6's codes, reports ledger claims the chain lacks and every unreadable ledger state, writes nothing — recovery included — and yields byte-equal results at open and through the audit surface over one lock-coherent snapshot | Build every intent, chain and ledger state §6 tables — the detached `pending`-only registration included — over stand-in views and ledger evidence and assert one finding each with the tabled code, severity and ref; run `root.reconcile_sessions` over the real root before and after a crashed session (a ledger with open invocation and a chain with its uncovered entry) and assert the findings equal `session.findings` of a session opened over the same root; hash the corpus root, its metadata sibling and the operations root before and after and assert equality, including with an unsettled registration present (which registered inspection would have resolved). **Interleaving:** start a scoped write on a second thread that blocks inside the commit, run reconciliation, release; assert no `session-entry-foreign` and that the write is either absent from both reads or covered. **Negative:** a fully covered session yields no finding, and an ordinary library write — no session actor — is never classified; a session directory with no ledger yields `session-ledger-missing` and does not refuse open |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `test_session_reconcile.py` for every intent, chain and ledger state over stand-in views and evidence; `acceptance/test_session_acceptance.py` for `root.reconcile_sessions` over the real root — equality with `session.findings`, the byte-equality of corpus root, metadata sibling and operations root with an unsettled registration present, and the interleaving arm.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J9 — closes

```markdown
| **J9** | Lifecycle: open writes `session-open` with the actor, world id and permit summary; `close` appends `session-close` once and is idempotent; every later call is `SessionClosed`; a config without exactly one corpus root, a root with no manifest, or a root whose chain is absent or malformed refuses at open with no directory created | Open and assert the first line; close twice and assert one `session-close`; call each method → `SessionClosed`; open over configs with zero and two corpus roots, a missing root, an existing but unadopted root, a registered root with no manifest, and an adopted root whose chain directory is removed → `SessionRefused`, no `sessions/` entry. **Negative:** a session left with an open invocation at `close` writes `session-close` after it, and the reader reports it in `open_invocations` and `closed` both |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_session_acceptance.py`: the `session-open` line, idempotent close, `SessionClosed`, and the seven refusing configurations including the unadopted root and the removed chain directory.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J10 — closes

```markdown
| **J10** | A session-written record is indistinguishable on ordinary read from a library write of the same node: same bytes, same path, no additional record, and the corpus view differs only by the record itself | Write one node through a scoped writer and the same node through `open_corpus` on a twin root; assert byte-equal record files, equal `corpus_check` findings, and equal record inventories. Session-`delete` a record and raw-`unlink` its twin; assert the two read views are equal. **Negative:** the two *chains* differ — the session root holds the intent and the fulfilling registration — which is the whole of the difference |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_session_acceptance.py`: twin roots written through the scoped writer and `open_corpus`, byte-equal record files, equal `corpus_check` findings and inventories, and the session-`delete`/raw-`unlink` read equality.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.
### J11 — closes

```markdown
| **J11** | A scoped writer is bound to one invocation: it acts only while that invocation is the current one, refuses with `SessionProtocolError` and nothing written before it is claimed, after it is closed or abandoned, and under any other current invocation, and carries the requirement it was scoped with, not the ceiling | `scoped(req, "A")`; act before claiming A → `SessionProtocolError`, head unchanged; claim A fresh, act → minted; close A; act again → `SessionProtocolError`; `scoped(narrower, "B")`, claim B fresh; act with A's writer → `SessionProtocolError`, head unchanged, no `act` line under B; act with B's writer → minted under B; abandon B (no close), claim C fresh; act with B's writer → `SessionProtocolError`. **Negative:** two writers scoped for the same id under one claim both act, and every act ledgers under that id |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_session_writer.py` over the in-memory executor: the bind-before-claim, closed, other-invocation and abandoned-invocation refusals, and the two-writers-one-claim negative.
- **Prior, not selected again:** none. The `J` table is new at this cut.
- **Deferred:** none.

## 4. Accounting

Eleven guarantee rows are read, **11 full/closed** (J1–J11), 0 partial, 0
re-reads. No row of another table is selected; the slice adds guarantees and
closes none. T3 (completion derived, never stored) is re-read informally in
the design's §9.1 and is not counted here. The N2 inventory therefore has
**11 declaration units**, one grouped unit per row. A grouped unit may expand
into lettered sabotage arms, but it is counted once here and may not be
silently split or merged after the freeze.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 11 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior marked durable in §3 runs through the certified
   engine on the certified kernel and volume tuple, on the volume beside the
   checkout; its portable arms run beside it. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner `tools/cut19_acceptance.py` names
   `cut18_acceptance.py` as its prefix (`PREFIX_RUNNERS =
   ("cut18_acceptance.py",)`), then runs the session acceptance module and
   the cut-19 N2 audit. No lower-numbered cut is undischarged, so no
   serialization under concurrency rule 5 applies.
4. `acceptance/n2_arms_cut19.py` declares the sabotage arms of the design's
   §9.3: in `session/ledger.py` (drop the `fsync`; write the outcome code
   only; update the index before the fsync; append after a failed line), in
   `session/writer.py` (skip the `act` line; append it after releasing the
   lock; bind the scoped writer to the ceiling; let `scoped` return without
   judging coverage; let a writer act under any open invocation; let a fresh
   claim raise while one is open; let `_commit` raise the `nodes` type from
   preflight), in `corpus.py` (move `_commit`'s `require` after
   `append_intent`; append the intent before `prepare`; reuse
   `_append_operation_intent`; call `preflight` after the intent; build
   `_prepare_add` on `_preflight_add_locked`; rebuild the view after a
   failed submission; initialize `unresolved` false; clear it before
   `_reconstruct` returns; leave one `with self._operation` outside
   `_locked`; read `recover` from the writer's port), in `relocation.py`
   (enter the bare lock), in `root.py` (drop `recover` from the durable
   factory; read the chain through `inspect_registered`; read ledgers
   outside the lock; raise on a missing ledger; open over a root with no
   manifest), in `report.py` and `intents/reduce.py` (drop the
   `corpus-write` branch; qualify on `no-record` for every kind), in
   `session/reconcile.py` (adopt an uncovered entry as covered; classify an
   open-invocation entry as foreign; classify an unreadable ledger's entries
   as foreign; settle a pending registration; drop the view's `pending`
   pairs; attach a `pending` pair to an intent), and in
   `test_permit_boundary.py`'s inventory (drop the `_commit` row).
   `test_n2_cut19.py` audits them by the cut-12 pattern.
5. J5's and J7's fsync observations wrap `os.fsync` and count one call per
   line; a test that asserts only the file's final contents does not satisfy
   the cell.
6. J8's byte-equality hashes the corpus root, its metadata sibling and the
   operations root, and the interleaving arm blocks a real scoped write
   inside the commit on a second thread while reconciliation runs.
7. J2's fresh-process arm crosses a process boundary: the staged transaction
   is left by one interpreter and settled by another's first scoped write.
8. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against the
design's §7 table at the freeze commit; audit every selected clause against
§2; and force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- J1's head equality is against the head **after settlement**, and the
  assertion that no intent decodes to the refused call's kind and token is
  present — a bare "head unchanged" assertion that would fail on a root
  recovery just settled does not satisfy the cell;
- J2 distinguishes root consistency from invocation outcome, and its
  post-submission arms assert `unresolved` still set rather than a rebuilt
  view;
- J3's act-time refusal comes from the kernel entry point's own `require`,
  never from a check in the facade;
- J8's classification arms include the `pending`-only registration the
  detached view reports outside `entries`, with no intent attached;
- J11's abandoned-invocation arm follows a real unclosed invocation, not a
  simulated flag.

## 7. Limitations

Inherited from the design's §8, restated at the freeze:

- **One corpus root**; multi-corpus targeting is the world-resolution lane's.
- **Coordination needs the launcher's profile**; without it the two methods
  refuse at the act.
- **Run, holdings and import are library-only** through this session, and
  `KernelRefusalValue` is unraised until a mirror exists.
- **Deduplication is session-scoped.**
- **Every operation commit rebuilds the view.**
- **The ledger's durability is a file fsync**, outside the certified path.
- **Two ledgered sessions over one operations root are not refused.**
- **A `delete` renders nothing.**
- **Reconciliation's snapshot is in-process coherent**; pending is reported,
  not settled.
- **Reads after a failed submission see unresolved files until the next
  write.**

## 8. Mechanism amendment — 2026-09-05

Frozen at `5cc2153`. On review of the implementation plan the commit
mechanism changed (design §13 items 9–15): the ordinary write bodies are the
one refusal implementation and stay byte-identical, `CorpusWriter._operation`
settles an unresolved root around the raw lock, and the commit seam is
`_RoutedExecutor.commit_fulfilling`, reached by routing a fulfilling scope's
one submission through the root's wrapped executor. Three sentences of §2 and
one arm list in §5 name the superseded mechanism — "the shared prepare
helpers", "`_locked()` settlement", and §5 item 4's `_prepare_add` and
`_locked` sabotages — and are read as citing §13; the selection, the eleven
rows, their checks and the 11 units are unchanged, and §2–§7 are
byte-identical to the freeze. `n2_arms_cut19.py` declares the arms this
mechanism admits, listed in the plan's Task 11.
