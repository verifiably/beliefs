# Writer session — design (the `writer-session` slice)

**Date:** 2026-09-05
**Status:** designed; conformance cut 19 freezes after review, before
implementation.
**Scope:** the `beliefs` half of the command framework's write boundary beyond
permits — the user and autonomy layer design
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §5.2
and §8 item 2, as the `science` repository's command-framework design §5
pins it: `open_attended_session` and the fresh session identity that fixes
the actor; `WriterSession.scoped(required)` returning an invocation-scoped
writer whose effective permit is exactly the requirement; the session ledger
at `<operations root>/sessions/<session-id>/ledger.v1` with its five typed
lines and the claim protocol over them; every session-mediated ordinary
corpus write performed as one `corpus-write` operation intent under the
session actor followed by one committed registration fulfilling it; the
versioned act-report amendment adding that operation kind and the rule that
qualifies it; and reconciliation — chains are truth, the ledger is
evidence — run at open and through the audit surface. No store change, no
`atoms` or `nodes` change, no new record kind, one dated amendment to the
act-report design.
**Inherits:** the layer design §5.2 (the endpoint supplies the permit and
sets every intent's actor from the session; the ledger is the evidence the
closing check compares against the chains) and the `science` command-framework
design §4.2, §5.1–§5.3, §6.1–§6.3 and §7.3–§7.4 (the contract: constructor and
method names, the ledger's line kinds and their fields, the claim outcomes,
the refusal envelope, what write continuation re-renders). Where those
documents decide a point this one cites it. The write-permits design
(`2026-09-04-write-permits-design.md`) owns `WritePermit`, `Authority`,
`RequiredCapabilities`, `permit_covers`, `PermitExceeded` and the static
entry-point inventory this document extends by one definition; the act-report
design (`2026-08-11-act-report-design.md`) §3 owns the operation intent and
the completion discipline this document amends; the family-adapters design
(`2026-08-19-family-adapters-design.md`) and the world-changing-families
design (`2026-09-03-world-changing-families-design.md`) own the seven write
families the operation seams mirror; the log-verification design
(`2026-08-22-log-verification-design.md`) owns the chain views reconciliation
reads.
**Out of scope:** the dispatcher, renderer, cursors and every surface
(`science`'s Task 12 and 13); run, holdings and import acts through the
scoped writer (§8); multi-corpus write targeting (§8); the run-session
constructor and its tiers, the actor sandbox and the endpoint handle
(sub-project 6); `publish` (sub-project 5); any `science` code.

**Sources, read at design time:** `python/src/beliefs/corpus.py`, `root.py`,
`report.py`, `runrecord.py`, `permit.py`, `errors.py`, `intents/shapes.py`,
`intents/reduce.py`, `intents/evidence.py`, `world/logmodel.py`,
`world/verify.py`, `world/registry.py`, `holdings/boundary.py`;
`python/tests/test_permit_boundary.py`, `tests/authority.py`,
`tests/conftest.py`; the `science` repository's
`docs/specs/2026-08-31-command-framework-design.md` §4–§7 and its plan's
Task 12 in full — the *Consumes* block that names the values this document
exports, and the tests that exercise them.

---

## 1. Problem

Write permits made the write boundary exist: every entry point binds an
`Authority` and refuses before its first effect. Nothing yet *holds* one on
behalf of a person's endpoint. There is no session identity, so no actor a
command's intent can carry that is not a string some caller spelled; no
ledger, so a crashed process leaves no evidence of what it claimed to write;
no invocation-scoped writer, so a handler that exceeds its declaration could
only be refused if the endpoint itself narrowed the writer, which is the
declaration-trusting arrangement the layer design rejects.

The ordinary corpus route compounds this. `CorpusWriter.add`, `retract`,
`supersede`, `revise`, `delete` and the two coordination writes publish
records that fulfill no intent. A chain therefore holds the record and the
registration that committed it, and nothing that says who asked. The run and
holdings routes already append actor-bearing intents; the ordinary route —
the one every daily command will use — does not, so the interval-membership
test of the layer design §7.1 and the crash reconciliation of the
command-framework design §5.3 could never name an ordinary session write.

Until this lands, `science`'s Task 12 cannot open a session and no shipped
command writes.

## 2. Decisions

1. **The registration is the fulfillment.** A `corpus-write` intent is
   qualified by a committed registration whose `fulfills` names the intent
   digest, whatever that registration publishes — one record, a replacement,
   or nothing at all for a deletion. Binding is by the intent digest, which
   already covers kind, token and actor. No `corpus-write` act-report is ever
   minted: a session-written record is byte-for-byte what a library write of
   the same node produces, and cut 18's managed-versus-raw reading of a
   deletion is untouched (§11).
2. **Every refusal precedes the intent.** The seven operation seams run the
   ordinary refusals first and append the intent only for a write that will
   be submitted. A refused write leaves the chain head unchanged, as the
   write-permits design §6 already rules for every intent-opening family.
3. **One commit seam.** All seven operation methods route through one
   private definition that calls the two primitives in order — intent, then
   fulfilling execution — and reads the registration digest back. The static
   inventory grows by exactly that definition (§4.4).
4. **A scoped writer is a real writer bound to the requirement.** `scoped`
   constructs a fresh `CorpusWriter` and durable port under
   `Authority(required.permit, session actor)`. The kernel entry points
   themselves refuse an overreaching act; the facade adds no check of its
   own. The session holds no writer, so no act ever runs under the ceiling
   (command-framework §4.2).
5. **Exactly one corpus root.** `open_attended_session` refuses a config
   naming zero or several corpus roots. The contract's `ScopedWriter` mirrors
   one `CorpusWriter`, and choosing a target silently would be a decision
   the world-resolution lane owns.
6. **The ledger is a JSON-lines file, appended and fsynced per line.** Its
   `act` line carries the intent digest beside the registration digest — an
   additive field the contract does not forbid — so reconciliation joins
   ledger to chain without inference.
7. **Protocol violations are hard errors, refusals are refusals.** A fresh
   claim while another invocation is open, a close naming anything but the
   open invocation, an act with no open invocation: each raises
   `SessionProtocolError` before any effect. The dispatcher's lock makes
   them unreachable; reaching one is a bug, never a recorded outcome.
8. **Reconciliation is one pure function.** Open and the audit surface call
   the same classification over parsed ledgers and chain entry views; the
   composition root supplies the chain reader. It writes nothing and mints
   nothing, and findings never refuse open.
9. **The `session` lane opens.** Its shared surface touches the mutation lane
   at `corpus.py` and the acquisition lane at `report.py`; both are named in
   §10 under concurrency rule 3.

## 3. The session — `beliefs/session/`

A package of three modules — `ledger` (lines, writer, reader), `writer` (the
session and the scoped writer), `reconcile` (classification) — whose
`__init__` exports exactly the contract's names: `open_attended_session`,
`WriterSession`, `ScopedWriter`, `Claim`, `ClaimFresh`, `ClaimDone`,
`ClaimOpen`, `ClaimMismatch`, `ActLine`, `InvocationRecord`, `LedgerReader`,
`open_ledger_reader`, `KernelRefusalValue`, and `reconcile`.

### 3.1 Opening and identity

```python
def open_attended_session(world_config: WorldConfig, operations_root: Path) -> WriterSession: ...
```

`world_config` must be an exact `WorldConfig`; `operations_root` a `Path`.
The config must name exactly one corpus root, and that root must be an
existing directory; otherwise `SessionRefused`, a `ScienceError`. Nothing
else is checked at open — an unregistered or unadopted corpus refuses at its
first write through the engine, exactly as `open_corpus` does today.

Open mints the session id as `secrets.token_hex(16)` — 32 lowercase hex,
the identifier bound of command-framework §6.2 — and fixes the actor as
`session:<session-id>`. It creates `<operations root>/sessions/<id>/`
(parents included), opens `ledger.v1` for append, writes `session-open`, then
runs `reconcile` over every *other* session directory under the same
operations root against the configured corpus root (§6) and exposes the
result as `session.findings`. The session's permit is `WritePermit.full()`,
held as a ceiling only: the session constructs no `CorpusWriter`.

`WriterSession` exposes `session_id`, `actor`, `operations_root`,
`findings`, and the methods of §3.3–§3.4 and §5. It has no `permit`
attribute the contract names; the ceiling is internal.

### 3.2 The ledger

One JSON object per line: `json.dumps(obj, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)`, UTF-8, newline-terminated.
Every append is `write`, `flush`, `os.fsync` on the file descriptor before
the appending call returns; the session directory is fsynced once at
creation. The `line` key discriminates:

| `line` | fields |
|---|---|
| `session-open` | `session` (32 hex), `actor`, `world` (the config's world id), `permit` (`{kinds, act_families, ungoverned}`, the `PermitSummary` as plain data), `at` |
| `invocation-open` | `invocation`, `command`, `input_digest` (64 lowercase hex), `at` |
| `act` | `invocation`, `corpus` (the manifest's corpus id), `entry` (the registration digest, 64 hex), `intent` (the intent digest, 64 hex), `records` (a list of `[uid, id]` pairs, in minting order — one pair for every family but `delete`, whose list is empty) |
| `invocation-close` | `invocation`, `outcome` — `{"done": [[uid, id], …]}` or `{"refusal": {"code", "message", "data"}}` |
| `session-close` | `at` |

`at` is UTC `%Y-%m-%dT%H:%M:%SZ`, the timestamp form every other record in
the corpus uses. Reads leave no line: the writer has no line kind for them,
which is how the contract's "write evidence, not a query store" is held on
this side.

### 3.3 Claims and the invocation lifecycle

```python
def claim_invocation(self, invocation_id: str, command: str, input_digest: str) -> Claim: ...
def close_invocation(self, invocation_id: str, outcome: Mapping[str, object]) -> None: ...
def invocation_acts(self, invocation_id: str) -> tuple[ActLine, ...]: ...
```

Arguments are validated before anything else: `invocation_id` against
`^[A-Za-z0-9_-]{1,64}$`, `command` a non-empty exact `str`, `input_digest`
64 lowercase hex; a violation is `ValueError`. The session keeps an in-memory
index of its own ledger — it is the file's only writer for its lifetime, so
the index is authoritative. `claim_invocation` judges the id under the
session's internal lock and returns one member of the closed union:

| the index holds | returns | side effect |
|---|---|---|
| nothing for the id | `ClaimFresh()` | appends `invocation-open`; the id becomes the open invocation |
| open and close, same command and digest | `ClaimDone(outcome)` | none; `outcome` is the persisted mapping, whole |
| open (either state), different command *or* digest | `ClaimMismatch()` | none |
| open without close, same command and digest | `ClaimOpen()` | none |

A fresh claim while another invocation is already open raises
`SessionProtocolError`. `close_invocation` accepts only the open invocation's
id — anything else is `SessionProtocolError` — and validates the outcome
strictly before appending: exactly one key, `done` mapping to a list of
two-string pairs or `refusal` mapping to an object with string `code` and
`message` and a JSON-object `data`; otherwise `ValueError`, nothing appended,
the invocation still open. After the append the session has no open
invocation. `invocation_acts` returns the `act` lines the index holds for the
id, in ledger order, as `ActLine(invocation, corpus, entry, intent,
record_ids)` with `record_ids: tuple[tuple[str, str], ...]`; an unknown id
returns `()`.

The four claim types are sealed, final, frozen dataclasses; `Claim` is
their union alias. Nothing else is ever returned.

### 3.4 Closing

`close()` appends `session-close` once and closes the file; a second call
returns without effect. Every other method on a closed session — `scoped`,
`claim_invocation`, `close_invocation`, `invocation_acts` — raises
`SessionClosed`. An invocation still open at `close()` is left open in the
ledger: the line records what was done, and §6 classifies what it left.

### 3.5 The reader

```python
def open_ledger_reader(operations_root: Path, session_id: str) -> LedgerReader: ...
```

Parses `<operations root>/sessions/<session-id>/ledger.v1` in full. A line
that is not a JSON object, lacks `line`, names an unknown line kind, or fails
its kind's field validation raises `LedgerMalformed` naming the line number;
a first line that is not `session-open` is malformed. A final byte sequence
with no terminating newline is a **torn tail**: the reader records it
(`reader.torn_tail: bool`) and does not refuse, because it is the crash
evidence §6 exists to surface. The reader exposes `session_id`, `actor`,
`world_id`, `closed` (whether `session-close` was read), `open_invocation`
(the id of an `invocation-open` with no `invocation-close`, or `None`),
`acts()` (every `ActLine`), `invocations()`, and
`invocation(id) -> InvocationRecord | None` carrying `invocation`, `command`,
`input_digest`, `acts` and `outcome` (`None` while open). A missing file is
`FileNotFoundError`, not a malformed ledger.

## 4. The kernel amendment — `corpus-write`

### 4.1 The operation kind and its qualification

`OPERATION_KINDS` gains `corpus-write`, so `OperationIntent("corpus-write",
token, actor)` constructs and `decode_intent` recognizes it through the
existing operation branch. `_mint_report` accepts the kind too, because the
tuple is shared; no boundary mints such a report, and a `corpus-write`
act-report arriving through explicit import is stored verbatim as
provenance like any other member.

The qualification rule is new, and it is stated once in the act-report
design's §3 as a dated amendment: **a `corpus-write` intent is qualified by
a committed registration fulfilling it, whatever it publishes.** Both
reductions implement it in one place each:

- `intents.reduce._qualify_one`: for a decoded operation intent of kind
  `corpus-write`, a committed registration whose `fulfills` is the intent
  digest is `matched` before any record is inspected; record paths are not
  consulted and an empty final surface is not `no-record`.
- `report.completion`: a `Registration` whose `intent_token` equals a
  `corpus-write` intent's token reads `CLOSED` whether or not its pointer
  resolves in `held`.

`shapes.mismatch` is unchanged: no evidence value qualifies or disqualifies
a `corpus-write` intent, so a `corpus-write` intent whose registration
publishes an act-report is still `matched` by the registration, never by the
report. Every other operation kind keeps the report-carrying-the-token rule.

### 4.2 The operation seams on `CorpusWriter`

`CorpusWriter.operations` returns an `OperationWrites` facade over the same
writer, with seven methods whose signatures equal their ordinary twins':

| method | mirrors | kind required | plan |
|---|---|---|---|
| `add(node)` | `add` | `node.kind` | `CreateOp`, or `ReplaceOp` with the manifest's expected digest when the uid is live — the choice `nodes`' `Corpus.add` makes |
| `retract(record)` | `retract` | `retraction` | `CreateOp` |
| `supersede(successor, *, of)` | `supersede` | `proposition` | `CreateOp` of the adapter-completed candidate |
| `revise(node)` | `revise` | `proposition` | `ReplaceOp` with the manifest's expected digest |
| `delete(ref)` | `delete` | the resolved record's kind | `DeleteOp` with the held content's digest |
| `mint_coordination(kind, *, project, content)` | `mint_coordination` | `kind` | `CreateOp` |
| `revise_coordination(kind, address, *, predecessors, content)` | `revise_coordination` | `kind` | `CreateOp` |

Each returns an `OperationCommit(record: Node | None, event_token,
intent_digest, entry_digest)` — `record` is the minted or replacing node,
`None` for `delete`. To keep the two paths from drifting, the refusal
bodies of `retract`, `supersede`, `revise`, `mint_coordination` and
`revise_coordination` move into shared prepare helpers
(`_prepare_retract(record) -> Node`, `_prepare_supersede(successor, of) ->
Node`, `_prepare_revise(node) -> Node`, `_prepare_mint_coordination(...) ->
Node`, `_prepare_revise_coordination(...) -> Node`) that run every existing
refusal and return the candidate to write; `add` and `delete` already have
`_preflight_add_locked`, `_preflight_replace_locked` and the excluded-kind
check. The ordinary methods keep calling `nodes`' `Corpus.add` (or the
executor for `delete`) after their prepare helper, exactly as today.

An `OperationWrites` requires an operation port; a writer constructed without
one refuses every operation method with `ImportRefused`'s sibling
`OperationPortMissing` (a `WriteRefused`), before any refusal of the write
itself.

### 4.3 The commit seam and its order

The one new primitive caller is `OperationWrites._commit(kind, prepare)`.
Under the root's operation lock, in this order and no other:

1. `authority.require("corpus-write", (kind,))` — the permit refusal, first.
2. `prepare()` — the family's refusals, returning the candidate node (or
   `None` for delete) and its plan. Any refusal propagates; the chain is
   untouched.
3. Append the intent: `OperationIntent("corpus-write",
   secrets.token_hex(16), authority.actor)` encoded as
   `v1.encode({"kind", "event_token", "actor"})`, through
   `operation_port.append_intent`. The existing `_append_operation_intent`
   is not reused: it requires the `act-report` kind because every operation
   used to end in a report. This seam requires the kind being written, which
   is what lets a requirement of just `proposition` commit.
4. `operation_port.execute_fulfilling(plan, intent_digest)`, which now
   **returns the registration digest** (§4.4).
5. `_reconstruct()` — the view is rebuilt as import rebuilds it today.
6. Return the commit.

A failure at step 3 leaves nothing; a failure between steps 3 and 4 — the
crash window of command-framework §5.3 — leaves an unfulfilled intent under
the session actor and no record, which §6 classifies. Step 2 before step 3
is decision 2, and it is what makes J1's "a refused write leaves the chain
head unchanged" hold for every one of the seven.

### 4.4 The port and the inventory

`OperationPort.execute_fulfilling(plan, fulfills) -> str` returns the digest
of the registration it committed. `DurableOperationPort` reads it back from
the chain under the lock it already holds: `read_chain` after submission,
the one `RegisteredEntryView` whose `fulfills` equals the intent digest, or
`ExecutionError` if there is not exactly one — digests come from the chain
itself, as anchor carriage already reads them, and the executor's
`TransactionOutcome` stays discarded. Every test port implements the return;
the existing callers (`_publish_operation_report`, the run boundary's two
sites, the holdings seam's `publish_fulfilling`) ignore it.

The static inventory of the write-permits design §4.2 gains one row:
`OperationWrites._commit`, family `corpus-write`, kinds required: the kind
passed in — judged, like every row, from what the definition emits. The
seven operation methods call no primitive and are not inventoried; `_commit`
requires unconditionally at the top of its body before its `append_intent`
(§5 arm 2 of that design). No definition gains an `actor` parameter.
`test_permit_boundary.py`'s `WRITE_ENTRY_POINTS` holds 37 definitions.

## 5. The scoped writer

```python
def scoped(self, required: RequiredCapabilities) -> ScopedWriter: ...
```

`required` must be an exact `RequiredCapabilities` (`TypeError` otherwise).
`scoped` judges `permit_covers(ceiling, required)`; on failure it raises
`PermitExceeded(PermitFact(...), ceiling.summary())` naming the first
missing family in sorted order, else the first missing kind in sorted
order — the declaration-time refusal, before any writer exists. On success
it constructs `CorpusWriter(root, durable_executor_factory(),
authority=Authority(required.permit, self.actor), operation_port=
DurableOperationPort(root, ..., authority=<the same>))` — `open_corpus`'s
body under the narrowed authority — and wraps it. The root-state registry
makes every writer over one root share one lock and one corpus state, so
the cost is two small value objects per invocation.

`ScopedWriter` exposes the seven methods of §4.2 with the ordinary
signatures and the ordinary return types (`Node`, or `None` for `delete`).
Each one:

1. asks the session for the open invocation — none is
   `SessionProtocolError`, before any effect, which also covers a writer
   kept past its invocation's close;
2. calls the writer's operation twin, which performs the kernel's own
   `require` (the act-time refusal — `PermitExceeded` from the entry point,
   under a full-permit session, when the handler exceeds its declaration);
3. appends the `act` line from the returned commit — invocation, the
   writer's `corpus_id`, `entry_digest`, `intent_digest`, and `[(uid, id)]`
   of the record or `[]`;
4. returns the record.

Step 3 runs after the commit and before the method returns, so a write the
handler observes is a write the ledger holds (J5); a crash between 2 and 3
is the window §6 names. Refusals propagate as raised: `PermitExceeded` and
every other `WriteRefused` from the kernel, `ExecutionError` from the
engine. `KernelRefusalValue(value)` — an `Exception` exposing `.value`,
whose wrapped value exposes `.reason` — is defined and exported for the
contract's one normalization path. **None of the seven methods returns a
value-style refusal, so this slice never raises it**; the run and holdings
mirrors that would are out of scope (§8).

`ScopedWriter` has no `close`, no `permit`, and no way to reach the
`WriterSession` or the underlying `CorpusWriter`; the handler holds the
facade and nothing behind it.

## 6. Reconciliation

```python
def reconcile(ledgers: Sequence[LedgerReader], chains: Mapping[str, tuple[EntryView, ...]]) -> tuple[Finding, ...]: ...
```

`chains` maps corpus id to the chain's entry views in chain order. For each
corpus, the function decodes every `IntentEntryView` with
`intents.shapes.decode_intent` and keeps operation intents whose actor has
the form `session:<32 hex>`; registrations are joined by `fulfills`, and a
registration's settlement decides `committed`. For every kept intent,
exactly one classification:

| state | finding (`code`, severity) | `ref` / `detail` |
|---|---|---|
| a committed registration fulfills it and some `act` line of that session names the registration digest | none | — |
| a committed registration fulfills it, no `act` line names it, and that session's ledger has an open invocation | `session-outcome-unknown`, warning | the registration digest / `session=… invocation=… intent=…` |
| a committed registration fulfills it, no `act` line names it, no open invocation | `session-entry-foreign`, error | the registration digest / `session=… intent=…` |
| no registration fulfills it, open invocation | `session-outcome-unknown`, warning | the intent digest / `session=… invocation=…` |
| no registration fulfills it, no open invocation | `session-intent-unclaimed`, error | the intent digest / `session=…` |
| the actor's session has no ledger under this operations root | `session-unknown`, error | the intent digest / `actor=…` |

And over the ledgers themselves: an `act` line whose `entry` no chain holds
as a committed registration is `session-act-unverified` (error; chains are
truth); a ledger with no `session-close` is `session-unclosed` (warning); a
torn tail is `ledger-torn-tail` (warning). Findings use `corpus.Finding` and
sort by corpus id, then chain position, then code, so two runs over the same
inputs are byte-equal (J8). A rolled-back registration is no registration.

The production composition is `root.reconcile_sessions(config,
operations_root) -> tuple[Finding, ...]`: it opens a `LedgerReader` for every
directory under `<operations root>/sessions/`, reads each configured corpus
root's chain through the log seam's `inspect_registered` (the same call the
audit takes, recovery resolved, pending refused), maps the root to its
manifest's corpus id, and calls `reconcile`. `open_attended_session` calls
the same function with the new session's own directory excluded; the audit
surface is the function itself. Neither writes, mints, or takes the corpus
operation lock — a chain read is what the audit already does beside a live
writer.

## 7. Guarantees

The `J` table. Rows are frozen; ids are never renumbered.

| # | Guarantee | Mutation test |
|---|---|---|
| **J1** | Every session-mediated ordinary write is exactly one `corpus-write` intent under the session actor followed by exactly one committed registration fulfilling it; the intent qualification reads `matched` and completion reads `closed`; a refused write — permit, family, or engine — leaves the chain head unchanged | Through a real attended session over a registered root, for each of the seven scoped methods: assert the chain grew by one intent (decoded kind `corpus-write`, actor `session:<id>`) and one registration whose `fulfills` is that intent's digest; run `qualify_chain` and `completion` and assert `matched`/`closed`, `delete` included, whose registration publishes no record. Refuse each method under a permit lacking the kind, and with a malformed record under the full permit; assert the head is byte-identical. **Negative:** the same seven through the ordinary `CorpusWriter` methods append no intent |
| **J2** | Intent precedes effect: a failure after the intent and before execution leaves an unfulfilled intent and no record, and reconciliation names it `session-outcome-unknown` under the open invocation | Fault the port's `execute_fulfilling` after `append_intent`; assert one intent, no registration, no record file; assert `reconcile` yields exactly one `session-outcome-unknown` naming the invocation and the intent digest. **Negative:** fault `append_intent` itself and assert no intent and no record — nothing to reconcile |
| **J3** | The scoped writer's effective permit is exactly the requirement: an act outside it is `PermitExceeded` raised by the kernel entry point under a full-permit session with nothing written, and `scoped` refuses an uncovered requirement before any writer exists | `scoped(for_kinds({"proposition"}, {}))` then `add(source)` → `PermitExceeded(("kind", "source"))`, head unchanged, no `act` line; `scoped(coordination())` then `add(proposition)` → refused on `proposition`; a requirement covered by the ceiling under a session whose ceiling is narrowed in test → `PermitExceeded` from `scoped`, `_root_state_for` untouched. **Negative:** the same acts under a requirement that names them are minted, and `PermitExceeded.capability` is the *requirement's* summary at the act and the *ceiling's* at `scoped` |
| **J4** | The actor is session-fixed: every intent a session write appends carries `session:<id>`, no session or scoped method accepts an actor, and a retraction whose facet names another actor is `ActorMismatch` with nothing written | Decode every intent after a run of scoped writes and assert the actor; inspect every public signature on `WriterSession`, `ScopedWriter` and `OperationWrites` for an `actor` parameter and assert none; `retract` a retraction naming `someone-else` → `ActorMismatch`, head unchanged. **Negative:** the same retraction with the session actor is minted |
| **J5** | Every `act` line carries the registration digest the chain holds and the exact minted identities, and is durable before the write returns | After each scoped write, read the ledger back and assert the last `act` line's `entry` equals the registration digest `read_chain` reports for the intent and its `records` equal `[(node.uid, node.id)]` (or `[]` for delete); assert the file's byte length grew before the method returned (a wrapped `os.fsync` observed once per line). **Negative:** an `act` line written with a fabricated `entry` is what `session-act-unverified` catches (J8) |
| **J6** | The claim protocol is exhaustive and fail-closed: the four outcomes of §3.3 exactly, a `ClaimDone` outcome replayed whole (refusal envelope included), and every protocol violation a hard error with nothing appended | Drive the table: fresh → open line; same id, same command and digest after close → `ClaimDone` with the identical persisted mapping, for a `done` and for a `refusal` outcome; different digest → `ClaimMismatch`; different command → `ClaimMismatch`; open without close → `ClaimOpen`; a second fresh id while one is open → `SessionProtocolError`; `close_invocation` of a non-open id → `SessionProtocolError`; a malformed outcome → `ValueError`, invocation still open. Assert the returned value's type is one of the four sealed classes in every case. **Negative:** eight threads claiming one fresh id under an external lock see one `ClaimFresh` and, after close, seven `ClaimDone` |
| **J7** | Every ledger line is appended and fsynced before its call returns, the encoding is canonical JSON lines, and the reader refuses a malformed line and reports a torn tail | Wrap `os.fsync` and assert one call per line for every line kind; parse each line with a strict decoder and assert `sort_keys` order and no whitespace; truncate a ledger mid-line → `torn_tail` true and every complete line read; corrupt a middle line → `LedgerMalformed` naming its number; a first line that is not `session-open` → `LedgerMalformed`. **Negative:** a valid ledger round-trips through the reader to the same `InvocationRecord`s the session's index holds |
| **J8** | Reconciliation classifies every actor-matching chain entry into exactly one of §6's codes, reports ledger claims the chain lacks, writes nothing, and yields byte-equal results at open and through the audit surface | Build the six intent states of §6 and the three ledger states over stand-in chains and assert one finding each with the tabled code, severity and ref; run `root.reconcile_sessions` over the real root before and after a crashed session (a ledger with open invocation and a chain with its uncovered entry) and assert the findings equal `session.findings` of a session opened over the same root; hash the corpus root and the operations root before and after and assert equality. **Negative:** a fully covered session yields no finding, and an ordinary library write — no session actor — is never classified |
| **J9** | Lifecycle: open writes `session-open` with the actor, world id and permit summary; `close` appends `session-close` once and is idempotent; every later call is `SessionClosed`; a config without exactly one corpus root refuses at open with no directory created | Open and assert the first line; close twice and assert one `session-close`; call each method → `SessionClosed`; open over configs with zero and two corpus roots and over a missing root → `SessionRefused`, no `sessions/` entry. **Negative:** a session left with an open invocation at `close` writes `session-close` after it, and the reader reports `open_invocation` and `closed` both |
| **J10** | A session-written record is indistinguishable on ordinary read from a library write of the same node: same bytes, same path, no additional record, and the corpus view differs only by the record itself | Write one node through a scoped writer and the same node through `open_corpus` on a twin root; assert byte-equal record files, equal `corpus_check` findings, and equal record inventories. Session-`delete` a record and raw-`unlink` its twin; assert the two read views are equal. **Negative:** the two *chains* differ — the session root holds the intent and the fulfilling registration — which is the whole of the difference |

## 8. Limitations

1. **One corpus root.** A `WorldConfig` naming several refuses at open. The
   world-resolution lane owns cross-corpus targeting; when it lands, the
   scoped writer's selection is a contract change made against both
   documents first.
2. **Run, holdings and import are library-only.** `RequiredCapabilities`
   can name the `run` and `holdings` families and `scoped` will honor a
   covered requirement, but the facade offers no method under either. A
   command that needs one is a follow-up whose first obligation is the
   `act` line it writes for an act that already carries its own intent —
   and `KernelRefusalValue` is unraised until then.
3. **Deduplication is session-scoped.** A retry against a new session is
   not deduplicated; the crashed session's ledger and the `session-outcome-
   unknown` finding are the operator's diagnostic (command-framework §6.2).
4. **Every operation commit rebuilds the view.** `_reconstruct` after the
   fulfilling execution is what import pays today; incremental maintenance
   of the `nodes` index through the port is not attempted here.
5. **The ledger's durability is a file fsync.** It sits outside every corpus
   and outside the engine's certified path; the A8 certification does not
   cover it. What the chain holds is truth precisely because the ledger's
   durability is weaker.
6. **Two ledgered sessions over one operations root are not refused.** A
   sibling live session shows as `session-unclosed`; single-writer
   deployment across processes remains the stated obligation it is for
   every writer.
7. **A `delete` renders nothing.** Its `act` line has no identities, so the
   contract's canonical ledger-rebuilt report for a delete is empty. That is
   correct and stated, not repaired.
8. **The `corpus-write` intent is not permit-narrowed by route.** A
   requirement of `for_kinds({"run"}, {"run": "corpus-write"})` commits a
   `run` record through `add` as an ordinary write, as the route says; the
   `run` family's own intent is the run boundary's.

## 9. Conformance cut 19

Cut 18 is discharged (`../plans/2026-09-04-conformance-cut-18-results.md`)
and no other cut is frozen in any worktree; this cut takes 19 and names
`cut18_acceptance.py` as its prefix runner.

### 9.1 Selection

Every row of §7 in full: J1–J10. Ten rows, ten selected units, carried by
the arms §9.3 declares. No row of another table is selected: the slice adds
guarantees and closes none. T3 (completion derived, never stored) is
re-read, not selected: `completion` gains a branch and remains a derived
reading.

### 9.2 Where the arms live

**Portable suite** (no host prerequisite): `test_session_ledger.py` — J6
and J7 over a temporary directory with a wrapped `os.fsync`;
`test_session_reconcile.py` — J8's classification over stand-in chains and
ledgers; `test_operation_writes.py` — J1's refusal-before-intent, J3 and J4
over the in-memory executor and a test port returning synthetic
registration digests; `test_intent_reduce.py` and `test_records.py` gaining
the `corpus-write` qualification branch of §4.1; `test_permit_boundary.py`
gaining `OperationWrites._commit` and its offender and satisfied
counterparts.

**Durable suite**, on the certified volume beside the checkout:
`acceptance/test_session_acceptance.py` — J1, J2, J5, J9 and J10 through
`open_attended_session` over a registered, adopted root with the real
`DurableOperationPort`; J8 through `root.reconcile_sessions` over the same
root after a faulted write.

### 9.3 N2

`acceptance/n2_arms_cut19.py` declares one lettered arm per selected unit
with its sabotage in `session/ledger.py` (drop the `fsync`; write the outcome
code only; accept a claim while one is open), `session/writer.py` (skip the
`act` line; bind the scoped writer to the ceiling instead of the
requirement; let `scoped` return without judging coverage), `corpus.py`
(move `_commit`'s `require` after `append_intent`; append the intent before
`prepare`; reuse `_append_operation_intent`), `report.py` and
`intents/reduce.py` (drop the `corpus-write` branch; qualify on `no-record`
for every kind), `session/reconcile.py` (adopt an uncovered entry as
covered; classify an open-invocation entry as foreign), and
`test_permit_boundary.py`'s inventory (drop the `_commit` row).
`test_n2_cut19.py` audits them by the cut-12 pattern, and
`tools/cut19_acceptance.py` runs `PREFIX_RUNNERS = ("cut18_acceptance.py",)`
then its phase modules.

## 10. What changes elsewhere

- **Implementation surface.** Adds `session/__init__.py`, `session/ledger.py`,
  `session/writer.py`, `session/reconcile.py`; rewrites `corpus.py`
  (`OperationWrites`, the prepare helpers, `_commit`), `report.py`
  (`OPERATION_KINDS`, `completion`), `runrecord.py` (`execute_fulfilling`'s
  return), `root.py` (`DurableOperationPort.execute_fulfilling`,
  `reconcile_sessions`), `intents/reduce.py` (`_qualify_one`), `errors.py`
  (`SessionRefused`, `SessionClosed`, `SessionProtocolError`,
  `LedgerMalformed`, `OperationPortMissing`); and every test port's
  `execute_fulfilling`.
- **The `session` lane.** The roadmap's lane table gains `session` with
  `writer-session` as its one boundary and a shared surface of `session/`,
  `corpus.py`, `report.py`, `runrecord.py`, `root.py`, `intents/reduce.py`
  and `errors.py`. Under concurrency rule 3 it names `corpus.py` (the
  mutation lane's `correction-remainder`) and `report.py` (the acquisition
  lane's `act-report-remainder`) as files it rewrites; the later merge
  resolves toward the earlier one.
- **The ledger's `Current state`** records the implementation in its summary
  when the cut discharges; the roadmap's boundary index, tier-1 table and
  lane table gain `writer-session` at freeze and drop it at discharge.
- **The guarantee inventory.** `GUARANTEE_TABLES` gains `J` with ten rows
  and `TABLE_OWNERS` names this document; the README's design table gains
  this document and the cut, and moves to fifteen frozen tables and the new
  row total.
- **The guide** — `foundations.md` drops "its writer session … not yet
  implemented" at discharge and cites this document; the glossary gains
  *writer session*, *session ledger* and *scoped writer*.
- **Dated amendment notes**, frozen cut text untouched: the act-report
  design §3 (the `corpus-write` operation kind and its qualification by the
  registration; the operation-kind tuple now has eight members); the
  write-permits design §4.2 (the inventory's 37th row) and §8 item 5 (the
  ledger and session now exist); the world-changing-families design §3.1
  (a session-mediated `delete` appends an intent and a fulfilling
  registration with an empty surface; it still mints no report).
- **`test_capability_boundary.py`** gains `DurableOperationPort`'s
  post-submission `read_chain` call at its one new site; no raw write is
  added.
- **The `science` repository** consumes exactly the names its plan's Task 12
  *Consumes* block pins; this document adds none and changes none. Two
  notes go back as change requests against that plan, not this contract:
  its fixture helpers still call `open_corpus(corpus_root)` and
  `world.admit(..., actor="fixture")` without an `Authority`, which cut 17
  removed; and a `delete`-class command, if one is ever declared, renders
  an empty canonical report (§8 item 7).

## 11. Alternatives rejected

- **A `corpus-write` act-report closing every session write.** In-corpus
  attribution and a token-bearing terminal record, at the cost of a second
  record per write, an act-report namespace that grows with every daily
  command, and a session `delete` that mints a live record — the exact
  thing cut 18 ruled out so that a managed deletion reads like a raw one.
  The contract's own words are the registration: "publishes the record
  through the existing fulfilling execution path."
- **A routed executor with a `fulfills` slot and a facade-side permit
  check.** Less code, but the act runs on a full-permit writer with the
  check beside it rather than in it, the router becomes an inventoried
  primitive caller with a hollow `require`, and the plan-to-intent binding
  lives in mutable state.
- **A ledger without kernel change** — intents appended by the session and
  records written through ordinary `add`. Two unlinked entries; no
  qualification; the intent claims nothing the chain confirms.
- **Per-corpus selection on the scoped writer.** A contract change made
  unilaterally, for a lane that has not designed the read side of a
  multi-corpus world.
- **Returning the executor's `TransactionOutcome` through the port.** The
  digest is available there, but every other digest the package trusts is
  read from the chain, and reading it back costs one validated read under a
  lock already held.
- **Refusing open when a prior session is unclosed.** It would make a crash
  a lockout. The finding is the contract's chosen surface for the person.

## 12. Verification

The repository gates, from `python/`: `uv run --frozen pytest`,
`uv run --frozen ruff check .`, `uv run --frozen pyright`; from `ts/`:
`npm ci`, `npm test`, `npm run typecheck`, `npm run check` — the TypeScript
package is untouched and its gates are the proof. The cut is discharged by
`tools/cut19_acceptance.py` on the certified volume beside the checkout, and
its results record lands with the ledger and roadmap re-rank in one commit
under concurrency rule 2. `science`'s Task 12 suite is the external check
that the contract's names resolve; it runs there, against a `beliefs` at the
discharge commit, and is not a gate here.
