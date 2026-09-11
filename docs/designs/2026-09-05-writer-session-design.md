# Writer session — design (the `writer-session` slice)

**Date:** 2026-09-05
**Status:** designed and reviewed six times on 2026-09-05 (the first review's
seven findings became §2 items 10–14, the second's four items 15–18, the
third's two items 19–20; the fourth, fifth and sixth rewrote items 19 and 21
and aligned the `J` rows); **conformance cut 19 frozen 2026-09-05**
(`2026-09-05-conformance-cut-19.md`), before implementation; **implemented
through `8723fac`, discharged 2026-09-05**; conformance cut 19 froze at
`5cc2153` and its 11 units passed through 43 arms. Results:
`../plans/2026-09-05-conformance-cut-19-results.md`.
**Scope:** the `beliefs` half of the command framework's write boundary beyond
permits — the user and autonomy layer design
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §5.2
and §8 item 2, as the `science` repository's command-framework design §5
pins it: `open_attended_session` and the fresh session identity that fixes
the actor; `WriterSession.scoped(required, invocation_id)` returning a writer bound to
one invocation whose effective permit is exactly the requirement; the session ledger
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

> **Amended 2026-09-10** (world resolution slice 2): an eighth seam, `attest_coreference`, joins on the same rule — refusals first, one commit seam, the `act` line after the commit. J1's "seven" is frozen text and stays; cut 24's results record states the eighth is covered there.

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
   be submitted. A refused write appends nothing of its own — no intent, no
   registration — so the head after the refusal equals the head after
   settlement (decision 19), which may carry the engine's recovery entries
   for a prior operation and nothing of the refused one. This is the
   write-permits design §6's rule for every intent-opening family, stated
   with the one qualification settlement adds.

   > **Amended 2026-09-10** (world resolution slice 2): an eighth seam, `attest_coreference`, joins on the same rule — refusals first, one commit seam, the `act` line after the commit. J1's "seven" is frozen text and stays; cut 24's results record states the eighth is covered there.

3. **One commit seam.** All seven operation methods route through one
   private definition that calls the two primitives in order — intent, then
   fulfilling execution — and reads the registration digest back. The static
   inventory grows by exactly that definition (§4.4).

   > **Amended 2026-09-10** (world resolution slice 2): an eighth seam, `attest_coreference`, joins on the same rule — refusals first, one commit seam, the `act` line after the commit. J1's "seven" is frozen text and stays; cut 24's results record states the eighth is covered there.

4. **A scoped writer is a real writer bound to the requirement and to one
   invocation.** `scoped(required, invocation_id)` constructs a fresh
   `CorpusWriter` and durable port under `Authority(required.permit,
   session actor)` and binds the facade to the invocation id. The kernel
   entry points themselves refuse an overreaching act; the facade's only
   check is that its invocation is the open one. The session holds no
   writer, so no act ever runs under the ceiling (command-framework §4.2).
5. **Exactly one corpus root, adopted and registered.** `open_attended_session`
   refuses a config naming zero or several corpus roots, a root whose
   manifest does not load, and a root whose chain detached inspection does
   not find well-formed. The contract's `ScopedWriter` mirrors one
   `CorpusWriter`, and choosing a target silently would be a decision the
   world-resolution lane owns; initialization and adoption are launcher- and
   operator-time acts (command-framework §4.4), never something an endpoint
   performs by opening.
6. **The ledger is a JSON-lines file, appended and fsynced per line.** Its
   `act` line carries the intent digest beside the registration digest — an
   additive field the contract does not forbid — so reconciliation joins
   ledger to chain without inference.
7. **Protocol violations are hard errors, refusals are refusals, and an
   abandoned invocation is neither.** A close naming anything but the
   current invocation, or an act by a writer whose invocation is not the
   current one, raises `SessionProtocolError` before any effect; the
   dispatcher's lock makes both unreachable, and reaching one is a bug. An
   invocation the dispatcher never closes — an internal error escaped its
   pipeline — simply stays open: the next fresh claim proceeds and becomes
   current, a retry of the abandoned id is `ClaimOpen` (the contract's
   `outcome-unknown`), and reconciliation names every open invocation as a
   candidate for an uncovered entry. A session is never locked by a bug in
   one command.
8. **Reconciliation is one pure function over one coherent snapshot.** Open
   and the audit surface call the same classification over parsed ledgers
   and chain entry views, both read under the corpus operation lock through
   non-mutating inspection; the composition root supplies the reader. It
   writes nothing — not even recovery — mints nothing, and never refuses
   open: every ledger state, absent and malformed included, is a finding.
9. **The `session` lane opens.** Its shared surface touches the mutation lane
   at `corpus.py` and the acquisition lane at `report.py`; both are named in
   §10 under concurrency rule 3.
10. **Every check that needs no engine state runs before the intent.** The
    port exposes `preflight(plan)` — plan shape, reserved leaves, the record
    ceiling — and the commit seam calls it after the family's refusals and
    before `append_intent`. What remains after the intent is the engine's
    own precondition and durability judgment, and a failure there is the
    crash window, classified by reconciliation, never a refusal.
11. **The act line is written under the lock the commit held.** The scoped
    writer takes the root's operation lock, commits, appends `act`, and
    releases; reconciliation reads chain and ledgers under the same lock.
    Between those two, no committed registration lacks its line.
12. **Two contract additions, both change requests.** `scoped` gains a
    positional `invocation_id`, and `open_attended_session` gains an optional
    `coordination` keyword taking a `ProfileSpec`. Each is filed against the
    `science` plan's Task 12 *Consumes* block before either side codes (§10).
13. **The operation seams share the ordinary methods' refusal bodies,
    literally.** Each prepare helper is the ordinary method's own refusal
    sequence factored out and called by both; no operation seam runs a
    preflight the ordinary method does not.
14. **An unreadable ledger is crash evidence.** A session directory with no
    ledger, an empty ledger, a torn or malformed one: each is a finding, and
    the intents of such a session classify toward `outcome-unknown`, never
    toward foreign.
15. **Every refusal the scoped writer raises is a `WriteRefused`.** The
    preflight's `PlanRefusedError` — a `nodes` error the dispatcher's pinned
    handler does not catch — is raised by the commit seam as `PlanRefused`,
    a `WriteRefused` subclass, so an oversized record closes its invocation
    with a refusal envelope. `ExecutionError` is deliberately *not*
    normalized: after submission the write may be durable, the invocation
    stays open, and `outcome-unknown` is the truthful answer.
16. **"No record" is promised only before submission.** A failure after
    `execute_fulfilling` is called — the engine's own, the registration
    readback, the ledger append — leaves a state that is unknown until
    inspected; J2 says so, and reconciliation classifies it.
17. **Pending is evidence in its own right.** Reconciliation takes the whole
    `WellFormedView`, and a staged registration the view reports only in
    `pending` is a finding without an invented intent association.
18. **The corpus id and chain are read at open, once.** An unadopted or
    unregistered root refuses at open (decision 5); every `act` line carries
    the id read then.
19. **A root is unresolved from process start and from every submission
    until its in-memory state is known to match disk.** The root's shared
    state carries `unresolved`, initialized **true** — a fresh process has no
    knowledge of what a dead one left, and open accepts a well-formed chain
    with pending work — set true immediately before any write is submitted
    on any path, and cleared only when the state update that follows a
    successful write completes: `Corpus.add` returning on the ordinary path,
    `_reconstruct` returning on the operation path. Every acquisition of the
    root's operation lock goes through one `_locked()` context manager that
    settles first — recover through the root's bound capability, rebuild,
    clear — before any state-dependent read on any path: the seven ordinary
    methods, `_commit`, `import_bundle`, `adopt_manifest`, and the
    two-root relocation acts that enter both writers' locks. While
    settlement fails, no prepare runs. **Recovery is a capability of the
    executor factory, not of any writer's port**: the durable factory
    `root.durable_executor_factory()` returns carries `recover(root)`, the
    root state binds it at creation from the factory every writer over that
    root must share, and settlement recovers through it whether or not the
    settling writer holds an operation port. A portless
    `CorpusWriter(root, durable_executor_factory(), …)` therefore recovers
    exactly as `open_corpus`'s writer does; the in-memory `DefaultExecutor`
    carries no `recover`, and a root opened with it has nothing to recover.
20. **Ledger I/O failure ends the session.** A failed `write`, `flush` or
    `fsync` leaves bytes whose durability the index cannot vouch for; the
    session becomes `LedgerFailed`, appends nothing further — not even
    `session-close` — and every method raises `SessionLedgerFailed`. The
    file is preserved exactly as the failure left it, and the reader's torn
    tail is its evidence. A handler's error is not a ledger failure and
    leaves the session usable (decision 7).

## 3. The session — `beliefs/session/`

A package of three modules — `ledger` (lines, writer, reader), `writer` (the
session and the scoped writer), `reconcile` (classification) — whose
`__init__` exports exactly the contract's names: `open_attended_session`,
`WriterSession`, `ScopedWriter`, `Claim`, `ClaimFresh`, `ClaimDone`,
`ClaimOpen`, `ClaimMismatch`, `ActLine`, `InvocationRecord`, `LedgerReader`,
`open_ledger_reader`, `KernelRefusalValue`, and `reconcile`.

### 3.1 Opening and identity

```python
def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    coordination: ProfileSpec | None = None,
) -> WriterSession: ...
```

`world_config` must be an exact `WorldConfig`; `operations_root` a `Path`.
The config must name exactly one corpus root; that root's manifest must
load (`ManifestMissing` and `ManifestMalformed` are re-raised as
`SessionRefused`, a `ScienceError`, with the cause attached), and its
corpus id is read once and carried on every `act` line; and detached
inspection of the root's chain must yield a `WellFormedView` — an
`AbsentView` (never registered) or a `MalformedView` refuses open naming
the view, because a session over a root the audit would refute is a session
whose every act line would be unverifiable. Adoption and registration are
`init_corpus_root` and `adopt_manifest`, launcher- and operator-time acts;
an endpoint opens over their result. Nothing else is checked at open.

`coordination` is the compiled `ProfileSpec` the launcher holds for the
corpus. When supplied, open constructs `CoordinationResolver({root:
profile})`, which validates the manifest's pins against the profile
(`ContractMismatch` propagates), and every scoped writer receives that
resolver. When absent, scoped writers have none and the two coordination
methods refuse `CoordinationUnavailable` exactly as an unmounted
`CorpusWriter` does today; `RequiredCapabilities.coordination()` still
passes `scoped`, and the refusal is at the act. A `ProfileSpec` compiles only
from parsed contract documents, which neither `WorldConfig` nor the manifest
can reconstruct, so the launcher supplies it or coordination is not
reachable — stated in §8 and filed against `science` in §10.

Open mints the session id as `secrets.token_hex(16)` — 32 lowercase hex,
the identifier bound of command-framework §6.2 — and fixes the actor as
`session:<session-id>`. In order: create `<operations root>/sessions/<id>/`
(parents included) and fsync the parent; create `ledger.v1`, write
`session-open`, fsync; then run `reconcile` (§6) over every *other* session
directory under the same operations root against the configured corpus
root, and expose the result as `session.findings`. A crash anywhere in that
sequence leaves a directory §6 classifies (`session-ledger-missing`,
`session-ledger-empty`); nothing it leaves can refuse a later open. The
session's permit is `WritePermit.full()`, held as a ceiling only: the
session constructs no `CorpusWriter`.

`WriterSession` exposes `session_id`, `actor`, `operations_root`,
`findings`, and the methods of §3.3–§3.4 and §5. It has no `permit`
attribute the contract names; the ceiling is internal.

### 3.2 The ledger

One JSON object per line: `json.dumps(obj, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)`, UTF-8, newline-terminated.
Every append is `write`, `flush`, `os.fsync` on the file descriptor, **and
only then** the in-memory index update, before the appending call returns;
the session directory is fsynced once at creation. If any of the three
steps raises, the session enters the `LedgerFailed` state (decision 20):
the exception is re-raised as `SessionLedgerFailed` carrying the cause, the
index is not updated, the file descriptor is closed without further writes,
and every later method — `scoped`, `claim_invocation`, `close_invocation`,
`invocation_acts`, and `close` itself — raises `SessionLedgerFailed`. Nothing
is ever appended after a partial line, so a torn tail stays a tail; and no
in-memory claim ever outruns the bytes that prove it. The `line` key
discriminates:

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
| nothing for the id | `ClaimFresh()` | appends `invocation-open`; the id becomes the current invocation |
| open and close, same command and digest | `ClaimDone(outcome)` | none; `outcome` is the persisted mapping, whole |
| open (either state), different command *or* digest | `ClaimMismatch()` | none |
| open without close, same command and digest | `ClaimOpen()` | none |

The most recently claimed fresh invocation is the **current** invocation.
A fresh claim while another is still open is permitted: the earlier one is
abandoned — an internal error escaped the dispatcher's pipeline before its
close — and stays open in the ledger, where a retry of its id meets
`ClaimOpen` and reconciliation names it (§6). `close_invocation` accepts
only the current invocation's id — anything else is `SessionProtocolError` —
and validates the outcome strictly before appending: exactly one key, `done` mapping to a list of
two-string pairs or `refusal` mapping to an object with string `code` and
`message` and a JSON-object `data`; otherwise `ValueError`, nothing appended,
the invocation still open. After the append the session has no current
invocation; earlier abandoned ones remain open. `invocation_acts` returns the `act` lines the index holds for the
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
`world_id`, `closed` (whether `session-close` was read),
`open_invocations` (the ids of every `invocation-open` with no
`invocation-close`, in ledger order — several when invocations were
abandoned, §3.3; empty when none), `acts()` (every `ActLine`),
`invocations()`, and
`invocation(id) -> InvocationRecord | None` carrying `invocation`, `command`,
`input_digest`, `acts` and `outcome` (`None` while open). A missing file is
`FileNotFoundError`, not a malformed ledger; an empty file is
`LedgerMalformed` (no `session-open`). Direct callers — `science`'s write
continuation — see those exceptions; reconciliation (§6) turns each into a
finding and never raises on ledger state.

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
`None` for `delete`. To keep the two paths from drifting, each ordinary
method's refusal body — everything between its `require` and its
`_corpus.add` (or executor call) — moves into a prepare helper that both
paths call: `_prepare_add(node)`, `_prepare_retract(record) -> Node`,
`_prepare_supersede(successor, of) -> Node`, `_prepare_revise(node) -> Node`,
`_prepare_delete(ref) -> Node`, `_prepare_mint_coordination(...) -> Node`,
`_prepare_revise_coordination(...) -> Node`. `_prepare_add` is `add`'s own
sequence — `_refuse_family_kinds(node)` with no admitted kind, `_refuse`,
`_refuse_foreign_closure_actor` — and **not** `_preflight_add_locked`, whose
`admitted_kind=node.kind` exists for the relocation families and admits a
retraction that `add` refuses and `retract` would judge for actor and
target (decision 13). The ordinary methods become `require`, lock, prepare,
write, exactly as today in effect; the static inventory is unchanged by the
factoring because no prepare helper calls a primitive.

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
3. `operation_port.preflight(plan)` — every check the engine would make that
   needs no engine state: `nodes`' `validate_plan`, the reserved-leaf rule,
   and the record ceiling (`root._refuse_malformed` and
   `_refuse_over_ceiling`, exposed through the port). The port's
   `PlanRefusedError` is raised here as `PlanRefused`, a `WriteRefused`
   (decision 15); the chain is untouched.
4. Append the intent: `OperationIntent("corpus-write",
   secrets.token_hex(16), authority.actor)` encoded as
   `v1.encode({"kind", "event_token", "actor"})`, through
   `operation_port.append_intent`. The existing `_append_operation_intent`
   is not reused: it requires the `act-report` kind because every operation
   used to end in a report. This seam requires the kind being written, which
   is what lets a requirement of just `proposition` commit.
5. `operation_port.execute_fulfilling(plan, intent_digest)`, which now
   **returns the registration digest** (§4.4). What the engine judges here —
   the path preconditions the prepare step read under this same lock, and
   durability — fails as `ExecutionError`, never as a refusal; so does the
   readback of the registration digest, which runs after the commit is
   durable.
6. `_reconstruct()` — the view is rebuilt as import rebuilds it today —
   and only if it returns is `unresolved` cleared. The flag was set true
   immediately before step 5; if step 5 raised, or step 6 raised, it stays
   set and the exception propagates (decision 19). The files on disk may
   include a staged effect the engine's recovery will roll back, and
   indexing them would let the next prepare accept, say, a retraction
   target that recovery then removes before the retraction commits; a
   committed write whose rebuild failed leaves a stale index the same rule
   protects.
7. Return the commit.

**Settlement before every state-dependent read.** `CorpusWriter` gains one
context manager, `_locked()`, and every `with self._operation:` in
`corpus.py` becomes `with self._locked():`; `relocation.py`'s two-root acts
enter `writer._locked()` for each writer instead of the bare lock. On entry
it acquires the root's operation lock and then, while `unresolved` is set,
runs `_settle()`: `state.recover()` when the root state carries a recovery
capability, then `_reconstruct()`, then clear. The capability is read once,
at root-state creation, from the executor factory —
`getattr(executor_factory, "recover", None)` — and never from a writer: a
durable root's factory always carries it, so a portless writer sharing the
state cannot clear the flag without recovering (decision 19), and an
in-memory root's factory never does, so there is nothing to call. Settlement therefore precedes the first
prepare in a fresh process (the flag starts true), after a failed
submission on any path, after a committed write whose rebuild failed, and
before `import_bundle` validates a member against the index or a relocation
act calls `_preflight_add_locked`, `_preflight_replace_locked`, `_add_locked`,
`_replace_locked` or `_delete_locked` — none of which reads before its
caller has entered `_locked()`. When recovery or rebuild fails the flag stays
set and `ExecutionError` propagates, so no prepare runs against unresolved
state. On the ordinary paths the bracket is the same: `unresolved` is set
true before `_corpus.add` or `_corpus.executor.execute` and cleared after
the call returns with the index updated; a failure inside leaves it set.
`recover(root)` is `read_chain` under the engine's project lock — the call
`_chain_head` already makes, which "resolves recovery before it projects" —
and it is not a write primitive: recovery is the engine's own consistency
act, exactly as the audit's registered inspection runs it today, and the
static inventory is unchanged by it. A static arm holds the rule: no bare
`with self._operation` remains outside `_locked`, and every `_corpus.add`,
`executor.execute`, `execute` and `execute_fulfilling` call site in
`corpus.py` sits inside the bracket. The cost is one chain read on a root's
first write per process and after each failure. Reads through `read_view`
between a failure and the next write see the files as the failure left
them, as they do today for any failed write (§8 item 11).

Steps 1–3 are refusals and leave nothing. Step 3 raises `PlanRefused`, a
`WriteRefused` subclass wrapping the preflight's `PlanRefusedError`
(decision 15), so the dispatcher's pinned handler closes the invocation
with a refusal envelope; the ordinary methods keep raising the `nodes` type
as today. After step 4 the state depends on where the failure fell: a
failure before submission is attempted — `append_intent` returned and
`execute_fulfilling` was never entered, or raised before the engine took the
plan — leaves an unfulfilled intent and no record; a failure **after
submission** — the engine's own, the readback, or the crash — leaves a
registration that may be committed and a record that may be durable, and
nothing in this seam can say which (decision 16). Both surface as
`ExecutionError` from this seam — the scoped writer's ledger append, one
step later, surfaces as `SessionLedgerFailed` (§5) — and all are the crash
window of command-framework §5.3, which §6 classifies from the chain, not
from the exception. Steps 2 and 3 before step 4 are decisions 2 and 10, and
they are what make J1's "a refused write appends nothing of its own" hold
for every one of the seven: the head after a refusal equals the head after
settlement.

### 4.4 The port and the inventory

`OperationPort` gains `preflight(plan) -> None`, the state-free checks of
§4.3 step 3, implemented once in `root.py` and called by both the durable
port and, unchanged in effect, the executor it constructs; a test port
implements it with the same two functions. `OperationPort.execute_fulfilling(plan, fulfills) -> str` returns the digest
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

> **Amended 2026-09-10** (world resolution slice 2): an eighth seam, `attest_coreference`, joins on the same rule — refusals first, one commit seam, the `act` line after the commit. J1's "seven" is frozen text and stays; cut 24's results record states the eighth is covered there.

> **Amended 2026-09-10 (slice 2b):** the session-mediated writes number
> **nine** — `correct_identifier` joins them as an ordinary `corpus-write`,
> one intent and one registration, minting no act-report
> ([slice 2b design](../superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md) §6).

## 5. The scoped writer

```python
def scoped(self, required: RequiredCapabilities, invocation_id: str) -> ScopedWriter: ...
```

`required` must be an exact `RequiredCapabilities` (`TypeError` otherwise);
`invocation_id` is validated against §3.3's grammar. `scoped` judges
`permit_covers(ceiling, required)`; on failure it raises
`PermitExceeded(PermitFact(...), ceiling.summary())` naming the first
missing family in sorted order, else the first missing kind in sorted
order — the declaration-time refusal, before any writer exists. On success
it constructs `CorpusWriter(root, durable_executor_factory(),
authority=Authority(required.permit, self.actor), operation_port=
DurableOperationPort(root, ..., authority=<the same>),
coordination_resolver=<the session's, or None>)` — `open_corpus`'s body under
the narrowed authority — and wraps it in a `ScopedWriter` bound to
`invocation_id`. The root-state registry makes every writer over one root
share one lock and one corpus state, so the cost is two small value objects
per invocation. `scoped` records nothing in the ledger and needs no claim to
have happened: the dispatcher calls it before `claim_invocation` with the id
it has already minted (command-framework §6.1 step 3, §6.2), and the binding
is what the claim later opens.

`ScopedWriter` exposes the seven methods of §4.2 with the ordinary
signatures and the ordinary return types (`Node`, or `None` for `delete`).
Each one, under the root's operation lock (the very one `_commit` nests
in — the lock is re-entrant per thread):

1. asks the session for the current invocation and requires it to equal the
   writer's own — none current, another current, the writer's abandoned or
   closed: `SessionProtocolError`, before any effect. A writer is therefore usable
   during exactly one invocation and never again, and a writer retained past
   its invocation cannot act under a later one's identity with its own
   permit (decision 4);
2. calls the writer's operation twin, which performs the kernel's own
   `require` (the act-time refusal — `PermitExceeded` from the entry point,
   under a full-permit session, when the handler exceeds its declaration);
3. appends the `act` line from the returned commit — invocation, the
   writer's `corpus_id`, `entry_digest`, `intent_digest`, and `[(uid, id)]`
   of the record or `[]` — still under the lock;
4. releases the lock and returns the record.

Step 3 runs after the commit, before the method returns, and before the
lock releases, so a write the handler observes is a write the ledger holds
(J5) and a reconciliation reading under the same lock never sees a committed
registration without its line (decision 11). A crash between 2 and 3 is the
window §6 names. Refusals propagate as raised, and every one is a `WriteRefused`:
`PermitExceeded`, the family refusals, and `PlanRefused` from the preflight.
`ExecutionError` propagates as raised too, and is not a refusal: the
dispatcher's pinned handler lets it escape as an internal error, the
invocation stays open, and a retry meets `outcome-unknown` — which is the
truthful state after a failure past submission (decision 16). The ledger
append in step 3 is the last such failure point: a crash between the commit
and the line leaves a covered-in-truth, uncovered-in-evidence registration
that §6 names, and a ledger I/O failure there raises `SessionLedgerFailed`,
ends the session (decision 20), and leaves the same registration for §6. `KernelRefusalValue(value)` — an
`Exception` exposing `.value`, whose wrapped value exposes `.reason` — is
defined and exported for the contract's one normalization path. **None of
the seven methods returns a value-style refusal, so this slice never raises
it**; the run and holdings mirrors that would are out of scope (§8).

`ScopedWriter` exposes `invocation_id` and nothing else beyond the seven
methods: no `close`, no `permit`, no way to reach the `WriterSession` or the
underlying `CorpusWriter`. The handler holds the facade and nothing behind
it.

## 6. Reconciliation

```python
def reconcile(ledgers: Sequence[LedgerEvidence], chains: Mapping[str, ChainView]) -> tuple[Finding, ...]: ...
```

`LedgerEvidence` is what the composition read for one session directory:
its `session_id` (the directory name) and one of `LedgerReader`,
`LedgerMissing`, `LedgerEmpty`, or `LedgerUnreadable(error)` — a
sealed union, so an unreadable ledger is an input, never an exception
(decision 14). `chains` maps corpus id to the detached `ChainView` read for it. An
`AbsentView` or `MalformedView` yields one finding — `session-chain-absent`
or `session-chain-malformed` (error, the defect as detail) — and classifies
nothing for that corpus: there is no truth to compare against. For a
`WellFormedView` the function decodes every `IntentEntryView` in `entries`
with `intents.shapes.decode_intent` and keeps operation intents whose actor
has the form `session:<32 hex>`; registrations are joined by `fulfills`, and
a registration's settlement decides `committed`; a registration in
`entries` with no settlement is **pending**. The view's own `pending`
pairs — a transaction id and a registration digest nothing settles, which
in detached mode may name a staged registration **absent from `entries`**
(decision 17) — are reported as `session-chain-pending` (warning, ref the
registration digest, detail the transaction id) with no session or intent
named, because the view provides none; a pending pair whose digest *is* in
`entries` is classified through the intent it fulfills, below. For every
kept intent, exactly one classification:

| state | finding (`code`, severity) | `ref` / `detail` |
|---|---|---|
| a committed registration fulfills it and an `act` line of that session names the registration digest | none | — |
| a committed registration fulfills it, no `act` line names it, and that session's ledger has one or more open invocations **or is not readable** | `session-outcome-unknown`, warning | the registration digest / `session=… invocations=[…] intent=…` — every open invocation, since the ledger cannot say which one it was |
| a committed registration fulfills it, no `act` line names it, ledger readable with no open invocation | `session-entry-foreign`, error | the registration digest / `session=… intent=…` |
| a pending registration fulfills it | `session-entry-pending`, warning | the registration digest / `session=… intent=…` |
| no registration fulfills it, open invocation(s) or unreadable ledger | `session-outcome-unknown`, warning | the intent digest / `session=… invocations=[…]` |
| no registration fulfills it, ledger readable with no open invocation | `session-intent-unclaimed`, error | the intent digest / `session=…` |
| the actor's session has no directory under this operations root | `session-unknown`, error | the intent digest / `actor=…` |

And over the ledgers themselves: an `act` line whose `entry` no chain holds
as a committed registration is `session-act-unverified` (error; chains are
truth); a readable ledger with no `session-close` is `session-unclosed`
(warning); a torn tail is `ledger-torn-tail` (warning); a directory with no
`ledger.v1` is `session-ledger-missing` (warning); an empty ledger is
`session-ledger-empty` (warning); a ledger the reader refuses is
`session-ledger-malformed` (error, the reader's message as detail). Findings
use `corpus.Finding` and sort by corpus id, then chain position, then code,
so two runs over the same inputs are byte-equal (J8). A rolled-back
registration is no registration.

The production composition is `root.reconcile_sessions(config,
operations_root) -> tuple[Finding, ...]`. For each configured corpus root it
takes the root's operation lock (the log seam's `corpus_lock`, the very lock
the writers hold), and under it reads the chain through the seam's
**`inspect_detached`** — a read-only scan that runs no recovery and appends
nothing; the registered inspection's `resolve` can append a settlement, and
reconciliation writes nothing — then reads every session directory under
`<operations root>/sessions/` into a `LedgerEvidence`, then releases. Under
the lock no in-process writer commits or appends an `act` line (decision
11), so the chain and the ledgers are one snapshot: an invocation that
opens, commits and closes around the read is either wholly before it (covered)
or wholly after it (absent from both), never `foreign`. Cross-process
writers remain the single-writer deployment obligation. A pending
registration under detached inspection is what the next write's recovery
will settle; it is reported, not adjudicated. The root is mapped to the
corpus id its manifest carries — a root with no manifest is
`session-corpus-unadopted` (error) and is not read — and `reconcile` is
called with the `ChainView` whole. `open_attended_session`
calls the same function with the new session's own directory excluded; the
audit surface is the function itself. Neither writes, recovers, or mints.

## 7. Guarantees

The `J` table. Rows are frozen; ids are never renumbered.

| # | Guarantee | Mutation test |
|---|---|---|
| **J1** | Every session-mediated ordinary write is exactly one `corpus-write` intent under the session actor followed by exactly one committed registration fulfilling it; the intent qualification reads `matched` and completion reads `closed`; a refused write — permit, family, plan shape, or record ceiling — appends nothing of its own: the chain head after the refusal equals the head after settlement, where settlement may have appended the engine's recovery entries for a *prior* operation and never an intent or registration of the refused one; and every refusal an ordinary method makes, its operation twin makes | Through a real attended session over a registered root, for each of the seven scoped methods: assert the chain grew by one intent (decoded kind `corpus-write`, actor `session:<id>`) and one registration whose `fulfills` is that intent's digest; run `qualify_chain` and `completion` and assert `matched`/`closed`, `delete` included, whose registration publishes no record. Refuse each method under a permit lacking the kind, with a malformed record under the full permit, with a record over `RECORD_CEILING`, and — for `add` — with a retraction and with an act-report; assert the head equals the head read after `_settle` (taken by a settled, non-writing probe before the refused call), that no intent decodes to the refused call's kind and token, and, for the retraction, that the refusal equals `add`'s own; repeat one refusal on a root left unresolved by a prior failed submission and assert the head moved only by recovery's settlement of that prior work. **Negative:** the same seven through the ordinary `CorpusWriter` methods append no intent |
| **J2** | Intent precedes effect, and the promise is bounded by submission: a failure after the intent and before the plan is submitted leaves an unfulfilled intent and no record; a failure after submission leaves the invocation's outcome unknown until inspected, and two consequences follow separately: root consistency — a failure of the engine, the readback, or the rebuild leaves the root unresolved until settled, while a ledger-append failure, which follows a completed rebuild, does not — and invocation outcome — the seam's failures surface as `ExecutionError` and the ledger append's as `SessionLedgerFailed`, never as a refusal, and reconciliation classifies the intent and any registration it finds by §6's table (`session-outcome-unknown` for a committed or absent registration under the open invocation, `session-entry-pending` for an unsettled one) from the chain, not the exception | Fault `execute_fulfilling` before it submits; assert `ExecutionError`, one intent, no registration, no record file, one `session-outcome-unknown` on the intent digest. Fault the registration readback after the commit; assert `ExecutionError`, the record durable, the registration committed, no `act` line, `unresolved` still set (the view **not** rebuilt), and one `session-outcome-unknown` on the registration digest; then assert the next write on that root settles first and sees the record. Fault `_reconstruct` after a successful commit and assert the same flag state and the same settlement on the next write. Fault the ledger append after the commit; assert `SessionLedgerFailed`, the record durable, the registration committed, no `act` line, and one `session-outcome-unknown` on the registration digest. **Fresh process:** leave a root with a staged, unsettled transaction, open a session over it in a new process (the chain is well-formed with pending work), and assert the first scoped write runs recovery and rebuilds before its prepare — the staged file is gone before the prepare reads. **Library writer and the other paths:** commit a session `delete` whose readback fails, then through an `open_corpus` writer over the same root run `import_bundle` with a member deriving from the deleted record and a relocation `move` of it; assert each settled first and refused against the rebuilt index, never validated against the stale one. **Mixed handles:** after a failed session submission that leaves a staged file, construct `CorpusWriter(root, durable_executor_factory(), authority=FULL)` with no operation port over the same root and `add` a record; assert recovery ran (the staged file is gone, the chain shows the rollback) before its prepare and that the flag cleared only then; assert the root state's `recover` is the durable factory's and that a `DefaultExecutor` root's is `None`. **Continuation after unresolved effects:** fault the engine after it has staged the record file but before commit; assert `ExecutionError` and `unresolved`; then, through the same session, `retract` a retraction naming that record — assert recovery ran first (the staged file is gone, the chain shows the rollback), the view was rebuilt, and the retraction is refused `RelocationTargetMissing`, never committed; then a fresh `add` succeeds and clears the flag. Fault recovery itself and assert the flag stays set and the next write raises `ExecutionError` before any prepare. Raw-write the target path between prepare and execute so the engine's precondition fails; assert `ExecutionError` and that reconciliation, not the test, says whether a registration stands. **Negative:** fault `append_intent` itself and assert no intent and no record — nothing to reconcile; `PlanRefused` from preflight appends no intent |
| **J3** | The scoped writer's effective permit is exactly the requirement: an act outside it is `PermitExceeded` raised by the kernel entry point under a full-permit session with nothing written, and `scoped` refuses an uncovered requirement before any writer exists | `scoped(for_kinds({"proposition"}, {}))` then `add(source)` → `PermitExceeded(("kind", "source"))`, head unchanged, no `act` line; `scoped(coordination())` then `add(proposition)` → refused on `proposition`; a requirement covered by the ceiling under a session whose ceiling is narrowed in test → `PermitExceeded` from `scoped`, `_root_state_for` untouched. **Negative:** the same acts under a requirement that names them are minted, and `PermitExceeded.capability` is the *requirement's* summary at the act and the *ceiling's* at `scoped` |
| **J4** | The actor is session-fixed: every intent a session write appends carries `session:<id>`, no session or scoped method accepts an actor, and a retraction whose facet names another actor is `ActorMismatch` with nothing written | Decode every intent after a run of scoped writes and assert the actor; inspect every public signature on `WriterSession`, `ScopedWriter` and `OperationWrites` for an `actor` parameter and assert none; `retract` a retraction naming `someone-else` → `ActorMismatch`, head unchanged. **Negative:** the same retraction with the session actor is minted |
| **J5** | Every `act` line carries the registration digest the chain holds and the exact minted identities, and is durable before the write returns and before the root's operation lock releases | After each scoped write, read the ledger back and assert the last `act` line's `entry` equals the registration digest `read_chain` reports for the intent and its `records` equal `[(node.uid, node.id)]` (or `[]` for delete); assert the file's byte length grew before the method returned (a wrapped `os.fsync` observed once per line); observe the lock from a second thread and assert it is held from before the commit until after the append. **Negative:** an `act` line written with a fabricated `entry` is what `session-act-unverified` catches (J8) |
| **J6** | The claim protocol is exhaustive and fail-closed: the four outcomes of §3.3 exactly, a `ClaimDone` outcome replayed whole (refusal envelope included), an abandoned invocation left open and never blocking a later fresh claim, and every protocol violation a hard error with nothing appended | Drive the table: fresh → open line; same id, same command and digest after close → `ClaimDone` with the identical persisted mapping, for a `done` and for a `refusal` outcome; different digest → `ClaimMismatch`; different command → `ClaimMismatch`; open without close → `ClaimOpen`; a second fresh id while one is open → `ClaimFresh`, the earlier still open, the new one current; `close_invocation` of the abandoned id → `SessionProtocolError`; `close_invocation` of the current id → closed; a malformed outcome → `ValueError`, invocation still current. Assert the returned value's type is one of the four sealed classes in every case. **Negative:** eight threads claiming one fresh id under an external lock see one `ClaimFresh` and, after close, seven `ClaimDone`; an oversized record through the scoped writer is `PlanRefused`, a `WriteRefused`, and its invocation closes with a refusal envelope rather than staying open |
| **J7** | Every ledger line is appended and fsynced before its call returns and before the index records it, the encoding is canonical JSON lines, the reader refuses a malformed line and reports a torn tail, and a ledger I/O failure ends the session with the file preserved as the failure left it | Wrap `os.fsync` and assert one call per line for every line kind; parse each line with a strict decoder and assert `sort_keys` order and no whitespace; truncate a ledger mid-line → `torn_tail` true and every complete line read; corrupt a middle line → `LedgerMalformed` naming its number; a first line that is not `session-open` → `LedgerMalformed`. Fault `write` after part of a line → `SessionLedgerFailed`, the index unchanged, the next `claim_invocation` and `close` → `SessionLedgerFailed`, the file's bytes exactly the partial line, the reader reporting a torn tail with every earlier line intact; fault `fsync` after a complete line → the same, and the claim the line would have recorded is absent from the index. **Negative:** a valid ledger round-trips through the reader to the same `InvocationRecord`s the session's index holds; a handler's `WriteRefused` leaves the session usable |
| **J8** | Reconciliation classifies every actor-matching chain entry into exactly one of §6's codes, reports ledger claims the chain lacks and every unreadable ledger state, writes nothing — recovery included — and yields byte-equal results at open and through the audit surface over one lock-coherent snapshot | Build every intent, chain and ledger state §6 tables — the detached `pending`-only registration included — over stand-in views and ledger evidence and assert one finding each with the tabled code, severity and ref; run `root.reconcile_sessions` over the real root before and after a crashed session (a ledger with open invocation and a chain with its uncovered entry) and assert the findings equal `session.findings` of a session opened over the same root; hash the corpus root, its metadata sibling and the operations root before and after and assert equality, including with an unsettled registration present (which registered inspection would have resolved). **Interleaving:** start a scoped write on a second thread that blocks inside the commit, run reconciliation, release; assert no `session-entry-foreign` and that the write is either absent from both reads or covered. **Negative:** a fully covered session yields no finding, and an ordinary library write — no session actor — is never classified; a session directory with no ledger yields `session-ledger-missing` and does not refuse open |
| **J9** | Lifecycle: open writes `session-open` with the actor, world id and permit summary; `close` appends `session-close` once and is idempotent; every later call is `SessionClosed`; a config without exactly one corpus root, a root with no manifest, or a root whose chain is absent or malformed refuses at open with no directory created | Open and assert the first line; close twice and assert one `session-close`; call each method → `SessionClosed`; open over configs with zero and two corpus roots, a missing root, an existing but unadopted root, a registered root with no manifest, and an adopted root whose chain directory is removed → `SessionRefused`, no `sessions/` entry. **Negative:** a session left with an open invocation at `close` writes `session-close` after it, and the reader reports it in `open_invocations` and `closed` both |
| **J11** | A scoped writer is bound to one invocation: it acts only while that invocation is the current one, refuses with `SessionProtocolError` and nothing written before it is claimed, after it is closed or abandoned, and under any other current invocation, and carries the requirement it was scoped with, not the ceiling | `scoped(req, "A")`; act before claiming A → `SessionProtocolError`, head unchanged; claim A fresh, act → minted; close A; act again → `SessionProtocolError`; `scoped(narrower, "B")`, claim B fresh; act with A's writer → `SessionProtocolError`, head unchanged, no `act` line under B; act with B's writer → minted under B; abandon B (no close), claim C fresh; act with B's writer → `SessionProtocolError`. **Negative:** two writers scoped for the same id under one claim both act, and every act ledgers under that id |
| **J10** | A session-written record is indistinguishable on ordinary read from a library write of the same node: same bytes, same path, no additional record, and the corpus view differs only by the record itself | Write one node through a scoped writer and the same node through `open_corpus` on a twin root; assert byte-equal record files, equal `corpus_check` findings, and equal record inventories. Session-`delete` a record and raw-`unlink` its twin; assert the two read views are equal. **Negative:** the two *chains* differ — the session root holds the intent and the fulfilling registration — which is the whole of the difference |

## 8. Limitations

1. **One corpus root.** A `WorldConfig` naming several refuses at open. The
   world-resolution lane owns cross-corpus targeting; when it lands, the
   scoped writer's selection is a contract change made against both
   documents first.
2. **Coordination is reachable only when the launcher supplies the
   profile.** `open_attended_session` takes a compiled `ProfileSpec` by
   keyword; without it, `mint_coordination` and `revise_coordination` refuse
   `CoordinationUnavailable` at the act. Compiling one needs the contract
   documents, which live outside every corpus; the `science` launcher's
   configuration is where they are named (§10).
3. **Run, holdings and import are library-only.** `RequiredCapabilities`
   can name the `run` and `holdings` families and `scoped` will honor a
   covered requirement, but the facade offers no method under either. A
   command that needs one is a follow-up whose first obligation is the
   `act` line it writes for an act that already carries its own intent —
   and `KernelRefusalValue` is unraised until then.
4. **Deduplication is session-scoped.** A retry against a new session is
   not deduplicated; the crashed session's ledger and the `session-outcome-
   unknown` finding are the operator's diagnostic (command-framework §6.2).
5. **Every operation commit rebuilds the view.** `_reconstruct` after the
   fulfilling execution is what import pays today; incremental maintenance
   of the `nodes` index through the port is not attempted here.
6. **The ledger's durability is a file fsync.** It sits outside every corpus
   and outside the engine's certified path; the A8 certification does not
   cover it. What the chain holds is truth precisely because the ledger's
   durability is weaker.
7. **Two ledgered sessions over one operations root are not refused.** A
   sibling live session shows as `session-unclosed`; single-writer
   deployment across processes remains the stated obligation it is for
   every writer.
8. **A `delete` renders nothing.** Its `act` line has no identities, so the
   contract's canonical ledger-rebuilt report for a delete is empty. That is
   correct and stated, not repaired.
9. **Reconciliation's snapshot is in-process coherent.** The corpus
   operation lock closes the race against in-process writers; a second
   endpoint process over the same corpus is outside it, as it is for every
   writer. Detached inspection reports a pending registration rather than
   settling it; the next write's recovery settles it.
10. **The `corpus-write` intent is not permit-narrowed by route.** A
    requirement of `for_kinds({"run"}, {"run": "corpus-write"})` commits a
    `run` record through `add` as an ordinary write, as the route says; the
    `run` family's own intent is the run boundary's.
11. **Reads after a failed submission see unresolved files until the next
    write.** `unresolved` gates writes, not `read_view`; a read between
    the failure and the next write may see a staged effect recovery will
    remove, exactly as it does today for a failed ordinary write. Making
    reads recover is the world-read lane's question, not this slice's.
## 9. Conformance cut 19

Cut 18 is discharged (`../plans/2026-09-04-conformance-cut-18-results.md`)
and no other cut is frozen in any worktree; this cut takes 19 and names
`cut18_acceptance.py` as its prefix runner.

### 9.1 Selection

Every row of §7 in full: J1–J11. Eleven rows, eleven selected units, carried by
the arms §9.3 declares. No row of another table is selected: the slice adds
guarantees and closes none. T3 (completion derived, never stored) is
re-read, not selected: `completion` gains a branch and remains a derived
reading.

### 9.2 Where the arms live

**Portable suite** (no host prerequisite): `test_session_ledger.py` — J6
and J7 over a temporary directory with a wrapped `os.fsync`;
`test_session_reconcile.py` — J8's classification over stand-in chains and
ledgers; `test_operation_writes.py` — J1's refusal-before-intent (the retraction and
ceiling arms included), J3, J4 and J11 over the in-memory executor and a
test port returning synthetic registration digests; `test_intent_reduce.py` and `test_records.py` gaining
the `corpus-write` qualification branch of §4.1; `test_permit_boundary.py`
gaining `OperationWrites._commit` and its offender and satisfied
counterparts.

**Durable suite**, on the certified volume beside the checkout:
`acceptance/test_session_acceptance.py` — J1, J2, J5, J9, J10 and J11
through `open_attended_session` over a registered, adopted root with the
real `DurableOperationPort`, the coordination arms under a supplied profile;
J8 through `root.reconcile_sessions` over the same root after a faulted
write, with the interleaving and the unsettled-registration arms.

### 9.3 N2

`acceptance/n2_arms_cut19.py` declares one lettered arm per selected unit
with its sabotage in `session/ledger.py` (drop the `fsync`; write the outcome
code only; accept a claim while one is open), `session/writer.py` (skip the
`act` line; append it after releasing the lock; bind the scoped writer to
the ceiling instead of the requirement; let `scoped` return without judging
coverage; let a writer act under any open invocation), `corpus.py` (move
`_commit`'s `require` after `append_intent`; append the intent before
`prepare`; reuse `_append_operation_intent`; call `preflight` after the
intent; build `_prepare_add` on `_preflight_add_locked`), `report.py` and
`intents/reduce.py` (drop the `corpus-write` branch; qualify on `no-record`
for every kind), `session/reconcile.py` (adopt an uncovered entry as
covered; classify an open-invocation entry as foreign; classify an
unreadable ledger's entries as foreign; settle a pending registration),
`root.py` (read the chain through `inspect_registered`; read ledgers
outside the lock; raise on a missing ledger; open over a root with no
manifest), `session/writer.py` again (let a fresh claim raise while one is
open; let `_commit` raise the `nodes` type from preflight; rebuild the view after a failed submission; initialize `unresolved` false;
clear it before `_reconstruct` returns; read `recover` from the writer's
port instead of the factory; drop `recover` from the durable factory; leave one `with self._operation`
outside `_locked`; enter the bare lock in `relocation.py`; append a ledger
line after a failed one; update the index before the fsync),
`session/reconcile.py` again (drop the view's
`pending` pairs; attach a `pending` pair to an intent), and
`test_permit_boundary.py`'s inventory (drop the `_commit` row).
`test_n2_cut19.py` audits them by the cut-12 pattern, and
`tools/cut19_acceptance.py` runs `PREFIX_RUNNERS = ("cut18_acceptance.py",)`
then its phase modules.

## 10. What changes elsewhere

- **Implementation surface.** Adds `session/__init__.py`, `session/ledger.py`,
  `session/writer.py`, `session/reconcile.py`; rewrites `corpus.py`
  (`OperationWrites`, the prepare helpers, `_commit`, `_locked` and the
  `unresolved` bracket on every write), `relocation.py` (entering
  `_locked()` for each root), `report.py`
  (`OPERATION_KINDS`, `completion`), `runrecord.py` (`preflight` and
  `execute_fulfilling`'s return), `root.py`
  (`DurableOperationPort.preflight` and `execute_fulfilling`,
  `reconcile_sessions`), `intents/reduce.py` (`_qualify_one`), `errors.py`
  (`SessionRefused`, `SessionClosed`, `SessionProtocolError`,
  `LedgerMalformed`, `SessionLedgerFailed`, `OperationPortMissing`,
  `PlanRefused`); `root.py`'s `durable_executor_factory()` returns a stable
  callable object carrying `recover(root)`, and `corpus.py`'s `_RootState`
  binds it at creation; and every test port's
  `execute_fulfilling`.
- **The `session` lane.** The roadmap's lane table gains `session` with
  `writer-session` as its one boundary and a shared surface of `session/`,
  `corpus.py`, `relocation.py`, `report.py`, `runrecord.py`, `root.py`,
  `intents/reduce.py` and `errors.py`. Under concurrency rule 3 it names `corpus.py` (the
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
- **The `science` repository.** Two contract changes go back as change
  requests against its plan's Task 12 *Consumes* block and its design
  §4.2 and §5.1, made before either side codes on (decision 12):
  `WriterSession.scoped(required, invocation_id)` — the dispatcher passes
  the `iid` it has already minted, and the writer is bound to it, which is
  the only sound answer to a writer retained across invocations; and
  `open_attended_session(world_config, operations_root, *,
  coordination=None)` — the launcher supplies the compiled `ProfileSpec` for
  coordination-class commands, so its configuration must name the contract
  documents. Two notes accompany them: the fixture helpers still call
  `open_corpus(corpus_root)` and `world.admit(..., actor="fixture")` without
  an `Authority`, which cut 17 removed; and a `delete`-class command, if one
  is ever declared, renders an empty canonical report (§8 item 8). Every
  other name is consumed exactly as pinned.

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
- **Binding a scoped writer at its first act, or to "whatever invocation is
  open".** Both let a writer scoped for one invocation act under a later
  one with its own permit — a permit escalation across commands by a
  handler that keeps a reference — and no session-side inference can tell
  the writers apart, because `scoped` runs before the claim and outside the
  dispatcher's lock. The id is known to the caller at that point; passing it
  is the change request.
- **Compiling the coordination profile inside the session.** The manifest
  pins name contract identities, not documents; `beliefs` ships no
  document registry and the corpus holds none. Inventing a lookup here would
  be a second configuration surface beside the launcher's.
- **Registered inspection for reconciliation.** It runs recovery, which can
  append a settlement — a write from a surface that promises none, and one
  that J8's byte-equality would have to exempt. Pending is reported instead
  and settled by the next write.
- **Normalizing `ExecutionError` into a refusal.** It would close an
  invocation `refusal` whose write may be durable, and a retry would then
  re-execute into exactly the uncertainty command-framework §6.2 forbids.
  The open invocation *is* the record of that uncertainty.
- **Refusing a fresh claim while one is open.** Sound only if no exception
  ever escapes the dispatcher's pipeline; the first internal error would
  lock the session until restart, and the ledger already expresses "open,
  never closed" without help.
- **Deferring adoption and registration to the first write.** Reconciliation
  at open needs the corpus id and the chain; an endpoint that opened over
  nothing would carry `act` lines no audit could verify.
- **Recovery through the operation port.** A writer without a port shares
  the root state with one that has it, and would clear the flag after a
  rebuild that recovered nothing — the original bug, one handle over. The
  factory is what every writer over a root must share, so the capability
  lives there.
- **A recovery flag set only by the failing seam.** It dies with the
  process, misses a rebuild that fails after a successful commit, and
  covers only the paths that know to set it; the state the flag tracks is
  "does the index match the disk", which is unknown at process start and
  after every submission until the update completes, so that is when it is
  set.
- **Rebuilding the view in a `finally` after a failed submission.** It
  indexes whatever the failure left, staged effects included, and the next
  prepare trusts the index; recovery then moves the files under a decision
  already made. Gating writes on recovery costs one chain read after a
  failure that should be rare.
- **Continuing to append after a ledger I/O failure.** A partial line
  followed by a complete one is malformed interior content the reader must
  refuse, where a partial tail alone is evidence it can report; and an index
  that recorded a claim whose fsync failed would replay an outcome the disk
  may not hold.
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
   the session identity (from which it derives the actor — no constructor
   or method anywhere takes an actor, J4), world id, corpus root, corpus
   id, operations root, an open `LedgerWriter`, a `writer_factory(authority)
   -> CorpusWriter`, and an optional ceiling for the portable suite. `open_attended_session`
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

   **The traced sequence (cut 19, Task 10).** `TracingBackend` over one
   `execute_fulfilling` on a registered root records these publish-phase calls,
   in order: four from the engine's own volume certification probe (`exchange`,
   `transfer_noclobber`, `transfer_noclobber`, `link_anchor` — the probe runs
   once per submission and deletes its `certify.db` after), then the record
   payload's blob publish, then the **registration** leaf's
   `.#~stage` → `<digest>` publish, then the **record's** own
   `.#~<txid>.op-0.staging` → `<slug>.md` publish, then the settlement's
   `.#~stage` → `<digest>`. `PUBLISH_CALLS_BEFORE_RECORD` is therefore **6**:
   the halt lands on the seventh call, after the registration is durable and
   before the record's path exists. Two facts the trace settled that the plan
   text did not anticipate: (a) the engine answers a failed publish by rolling
   the transaction back *in band*, and a rollback that succeeds appends the
   settlement — so the fixture's window stays open for the whole fulfilling
   execution and closes in the port's `finally`, which is what leaves the
   registration durable and unsettled; and (b) the rollback unlinks the
   record's staging file on its way out, so the staged bytes that survive the
   halt are the chain's (`<root>/.#~chain/.#~stage`, a file), not the record's.
   And (c) the count holds only over a kind directory that already exists: a
   transaction that must create `<kind>/` publishes the directory one call
   *before* the record, so every arm writes a record of the same kind before it
   arms, and the acceptance suite re-derives both shapes through
   `TracingBackend`.
5. **Staleness baseline at plan time.** The probe of the plan's Global
   Constraints (with its existence guard) prints, on the untouched tree:
   `stale: [(5, 'T2', 'corpus.py', 0), (5, 'T2', 'corpus.py', 0), (5, 'C2', 'stored.py', 0), (6, 'X4', 'world.py', 'missing'), (6, 'X4', 'world.py', 'missing'), (6, 'X5', 'world.py', 'missing'), (6, 'X6', 'world.py', 'missing'), (6, 'X6', 'world.py', 'missing'), (6, 'X6', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'W13', 'world.py', 'missing'), (6, 'labeled:admission-idempotency', 'world.py', 'missing'), (6, 'labeled:status-idempotency', 'world.py', 'missing'), (6, 'labeled:duplicate-carrier', 'world.py', 'missing'), (8, 'L2u5', 'root.py', 0), (8, 'L12u5', 'world/verify.py', 0), (8, 'D6', 'world/verify.py', 0), (8, 'D10', 'world/verify.py', 0), (10, 'H4u1', 'holdings/boundary.py', 0), (10, 'J8', 'holdings/boundary.py', 0)]`.
   Every entry is pre-existing invalidated evidence from cuts 5, 6, 8 and 10,
   cited and not run; cuts 17 and 18, which cut 19's prefix runner executes,
   contribute none.
6. **Finding order.** §6's "corpus id, then chain position, then code" is
   implemented as an internal sort key `(corpus_id, position, code, ref)`
   that the returned `Finding` values do not carry; two runs over equal
   inputs return equal tuples, which is what J8 asserts.
7. **The corpus-write branch in `completion`.** A `Registration` whose
   `intent_token` equals a `corpus-write` intent's token reads `CLOSED`
   without consulting `held`; `INDETERMINATE` is unreachable for that kind,
   because nothing about the pointer bears on the reading.
8. **The constructor writes `session-open`.** `WriterSession.__init__`
   appends the line; the composition writes nothing before it, and
   reconciliation runs after construction.
9. **The commit is routed through the root's executor; the ordinary bodies
   are the one refusal implementation.** Decision 13's prepare helpers and
   §11's rejection of "a routed executor" are revisited together, on review
   of the plan: factoring the ordinary bodies collides with the pinned
   sabotage strings of cuts 5, 16, 17 and 18 (`E1c`, `E1r`, `C1`, `S4`,
   `G2c`, the boundary re-resolution arms), which cut 19's prefix runner
   executes; and §11's two objections no longer hold — the scoped writer is
   per-invocation, so no act runs under the ceiling, and the `require` in
   the routed seam is real, judged on the kinds the plan emits. So:
   `OperationWrites.<method>` calls `CorpusWriter.<method>` unchanged, inside
   a fulfilling scope; the root's wrapped executor routes that scope's one
   submission to `_RoutedExecutor.commit_fulfilling`, which is the commit
   seam of §4.3 — require, preflight, intent, fulfilling execution — and
   the inventory's 37th row. "Every refusal an ordinary method makes, its
   twin makes" (J1) holds by construction. §4.2's helper table and §4.4's
   row name are superseded by this item; the cut record's §8 cites it.
10. **The raw operation lock stays non-settling.** `_operation_lock_for(root)`
    returns the bare `OperationLock` as today; reconciliation, the scoped
    writer's act hold, and every engine-side acquisition take it without
    triggering recovery. `CorpusWriter._operation` becomes a `_SettlingHold`
    around that lock: enter acquires, then settles an unresolved root; a
    settlement failure releases the lock and propagates. Every existing
    `with self._operation:` — `relocation.py`'s `enter_context(writer._operation)`
    included — therefore settles with no text change, and `relocation.py` is
    not rewritten.
11. **Fulfillment is scoped to one locked call, bound under the raw lock.**
    The executor belongs to the shared root state, so a per-invocation writer
    does not isolate it. `OperationWrites._run` takes the *raw* root lock,
    binds exactly the calling writer's authority and port into
    `_RootState.fulfilling` through `CorpusWriter._fulfilling()`, and then
    calls the ordinary method — whose own `require` runs first and whose own
    settling hold (re-entrant on the same lock) settles afterwards, exactly
    as for a library caller. Entering the settling hold before the ordinary
    method would recover, and could move bytes, before the permit was judged;
    the twin's refusal order is therefore the ordinary method's, by
    construction. `_fulfilling` rejects a nested scope (`ScienceError`) and
    clears the binding in `finally`; the scope admits exactly one submission
    and refuses a second (`ScienceError`). Both are hard errors: neither is
    reachable through the seven twins. The scope records two facts
    separately: `consumed` (its one submission attempt was taken, which
    guards a second) and `submitted` (the seam appended the intent, set after
    the preflight). Once `submitted`, any exception the ordinary method
    raises — the engine, the readback, the index update, the rebuild — is
    re-raised by `_run` as `ExecutionError` with the cause attached (J2's
    boundary); a refusal before it — the permit's, the body's, or the
    preflight's `PlanRefused` — propagates unchanged, and the library path's
    behavior is untouched.
12. **`unresolved` is set at every submission point and cleared only after the
    complete state update.** Set true: in `_RoutedExecutor.execute`'s
    ordinary branch before delegating (this covers `Corpus.add`,
    `_corpus.executor.execute`, and `adopt_manifest`'s factory-created
    executor, because `_RootState.executors` — the wrapped factory — is what
    `Corpus` and `adopt_manifest` construct from, and `_reconstruct` rebuilds
    with it, so the wrapper survives every rebuild); in
    `commit_fulfilling` after its preflight and before the intent; and by one
    explicit `self._state.unresolved = True` line before
    `_publish_operation_report`'s direct port submission. Cleared: only in
    `_SettlingHold.__exit__`, only on the outermost hold, only when the body
    exited without an exception — which is after `nodes`' index update, after
    `_reconstruct`, after the readback. A failure anywhere leaves it set. The
    run boundary's and the holdings acts' port submissions do not touch this
    writer's state and are not covered (§8 item 12).
13. **The permit guard stays a top-level statement in a dedicated method.**
    `_RoutedExecutor.commit_fulfilling(scope, plan)` begins with
    `scope.authority.require("corpus-write", _plan_kinds(plan))`, the kinds
    read from the plan's record paths (`<kind>/<slug>.md`), so the seam
    requires exactly what it emits. It is inventoried under
    `corpus.py:_RoutedExecutor.commit_fulfilling`. `_RoutedExecutor.execute`
    is the `WritePlanExecutor` the corpus holds — an *implementation* of the
    `execute` primitive, not a caller — and joins `test_permit_boundary.py`'s
    implementation-exclusion list by exact name, as the design's §4.3 rule
    for primitive implementations provides.
14. **Every frozen obligation is retained.** The `J` rows, their checks and
    the 11 units are unchanged; cut 19's §2 sentence naming "the shared
    prepare helpers" and §5 item 4's `_prepare_add`/`_locked` arms are
    superseded by citation in the cut record's dated §8, with §2–§7
    byte-identical to the freeze; cut 17's and cut 18's audits run unchanged
    as the prefix and every one of their strings matches exactly once.
15. **Limitation 5 narrows.** A session `add`, `retract`, `supersede`,
    `revise` or coordination write no longer rebuilds the view: `nodes`'
    `Corpus.add` updates the index incrementally after the routed executor
    returns, exactly as on the library path. `delete` rebuilds, as its
    ordinary body does today.
16. **The staleness baseline is unchanged throughout.** No task may leave a
    prior-cut arm stale; the executor route exists so that none does.
17. **The scoped authority is minted in `permit.py`.** §5 writes the scoped
    writer's authority as `Authority(required.permit, self.actor)` at the
    session. E6's static arm
    (`test_permit_boundary.py::test_authority_is_constructed_only_in_permit`)
    admits an `Authority(...)` construction in `permit.py` and nowhere else —
    the rule write-permits design §16 states as the reason `permit.READ_ONLY`
    lives there — and `beliefs/session/writer.py` is not `permit.py`. So
    `permit.py` gains `scoped_authority(required, actor) -> Authority`: it
    type-checks the requirement and returns `Authority(required.permit,
    actor)`, exactly §5's value with no widening, no default and no second
    permit source. `WriterSession.scoped` calls it with the actor it derives
    from the session id, so no `session/` definition takes an actor and the
    static arm is unweakened.
18. **The scoped act runs under the session lock; the lock order is session,
    then root.** `ScopedWriter._act` takes the session's lock first and holds it
    across the currency check, `perform()` and the `act` line, taking the raw
    `_operation_lock_for(root)` lock inside it. Holding the session lock only
    for the check left a window: `_act` held the root lock alone while
    `claim_invocation` and `close_invocation` hold the session lock alone, so
    another thread could move the current invocation between the durable commit
    and the ledger append — a committed registration with no `act` line in a
    session that stays live, which §5 sanctions only for a crash or a ledger
    I/O failure, both terminal. With the lock held for the whole act, the
    currency re-check in `_record_act` is an **invariant**, not a refusal: it
    raises `ScienceError`, never `SessionProtocolError`, because an operation
    whose registration is durable can no longer be refused. The session lock is
    a `threading.RLock` so the helpers `_act` calls may take it again;
    `claim_invocation` and `close_invocation` are unchanged, still taking it
    once. **Session lock, then root lock, everywhere** — claims and closes take
    the session lock alone, and nothing takes the root lock before the session
    lock, so the two orders never cross.
19. **A `CapabilityUnavailable` lifecycle read defers to the write's own
    refusal.** Item 3's "not writable" case is not only a successful read that
    resolves to a non-`WRITABLE` state: an uncertified tuple (a volume the
    engine's allowlist does not certify, e.g. a `tmpfs` with no barrier-option
    table) fails the lifecycle read itself with `CapabilityUnavailable`, and
    that failure is the engine's own judgment that the root is not writable —
    the write will refuse with the identical cause regardless of what recovery
    does. So `recover` catches `CapabilityUnavailable` from the lifecycle read
    and returns without reading the chain, the same as a successful
    non-`WRITABLE` read; this is what keeps
    `test_import_on_an_uncertified_tuple_refuses`'s frozen `(None, 0)` shape
    intact; a settling hold that instead mapped this case to
    `ExecutionError(index=None, applied=None)` at recovery would refuse with
    the right cause but the wrong `(index, applied)` shape, one step earlier
    than the write itself. Every other lifecycle-read exception is unchanged:
    it proves nothing about the root, so it still maps to
    `ExecutionError(index=None, applied=None)` and the flag stays set.

## Integration amendment — 2026-09-07

The facet-contracts integration requires `profile: ProfileSpec` as a keyword
on `open_attended_session`. The session passes this explicit compiled profile
to its writer and durable operation port. The optional `coordination` argument
continues to provide the coordination resolver; the writer's shared agreement
checks require that resolver and the held profile to agree. No default profile
is inferred from a manifest or from coordination. Downstream launchers must
supply the compiled profile when opening a session. This composes the session
write boundary with the facet-contracts pin gate; it changes no read API.

Revision retains the session's early candidate-kind permission check before
settlement, followed by authorization against the actual stored kind under
the lock. A forbidden candidate kind is refused before target resolution,
including a missing target; a permitted forged candidate kind never grants
authority over a forbidden stored kind. With full authority, changing a
dataset's kind still reaches the dataset revision allowlist refusal.
