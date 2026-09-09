# Session routes, store identity and reference rules — design (the belief-path seams)

**Date:** 2026-09-09
**Status:** designed 2026-09-09 in a brainstorming session of four sectioned
reviews, each approved as presented (store identity and the session; the
ledgered port and seam; reference rules, replay and errors; testing and
documents), after three rulings: the reproduction driver maps its
identities onto the kernel implementations rather than keeping copies; rule
identities carry the kernel's scope; the store root is optional on the
session. Not yet implemented.
**Scope:** the three kernel seams the science belief-path design depends on
(science `docs/specs/2026-09-09-belief-path-commands-design.md` §6.1, §6.2,
§5): the public store identity reader (`beliefs-2d9a55`), the run and
holdings routes on the invocation-scoped writer (`beliefs-5fe2e3`), and the
reference rule implementations keyed by rule identity (`beliefs-e5ab34`).
Builds on the writer session (`2026-09-05-writer-session-design.md`), the
write permits (`2026-09-04-write-permits-design.md`) and the holdings
boundary. Science's `sci-66b26d` depends on all three.

## 1. What the surface needs and why the kernel has to give it

A science command runs one invocation of one attended session. It holds a
`ScopedWriter`, whose seven methods are the corpus-write family, and a read
context; it never sees a permit or an `Authority` (command framework §4.2).
The belief path needs two more act families from that position:

- **`run`.** `execute_assessment_run` and `replay` take an `OperationPort`.
  The port binds an `Authority` and the durable root; a command has neither.
- **`holdings`.** `write` and `delete` take an `ActContext`, which binds an
  `Authority`, a store root, a seam and a profile. Same position.

Permit reach is not the gap. A declaration that routes `run` and
`act-report` to `run` yields the `run` family; `holdings-observation` yields
`holdings`; both are command-reachable and the session ceiling covers them.
The gap is a seam: nothing on the scoped writer hands out a port or a
context bound to the invocation's scoped authority, and nothing would ledger
what they commit. The session's ledger is the account of what an invocation
did (writer-session design §3); a run or an observation committed past it
would be an act the ledger cannot see, and science's write audit, which
rebuilds the canonical report from the ledger's `act` lines, would see
nothing.

Two smaller needs sit beside it. The read context must know a store root's
identity without opening a session, to build the resolution snapshot and to
match held paths of the form `store:<id>:<relative>`; the kernel holds that
read as a private function. And the surface's `spec` command resolves rule
identities to implementations the kernel ships, so `freeze` binds them and
the audit recomputes against the same code; today the only such
implementations live in the mm30 reproduction driver, an instrument.

## 2. Store identity (`beliefs-2d9a55`)

```python
def store_identity(store_root: Path) -> str | None: ...
```

`beliefs.root.store_identity` is the public name of the existing
`_read_existing_store_genesis`: a detached inspection of the root's chain,
with no metadata root, no recovery and no writes, that returns the id the
store genesis carries. It returns `None` when the root has no chain, the
chain is not well formed, or the first entry is not a store genesis. A
genesis whose payload is malformed still raises `CorpusRootRefused`, as it
does today. `init_store_root` calls the public name; the private one is
removed.

Detached inspection is the point, not a convenience: a store may be arriving
or interrupted, and the read context must never run recovery on a root it
only reads (science plan Task 3).

## 3. The session's store and the scoped writer (`beliefs-5fe2e3`)

### 3.1 Opening with a store

```python
def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    profile: ProfileSpec,
    coordination: ProfileSpec | None = None,
    store_root: Path | None = None,
) -> WriterSession: ...
```

When `store_root` is given, the opener reads `store_identity(store_root)`
before any ledger file exists and refuses with `SessionRefused` when it is
`None`; a misconfigured store fails before a `session-open` line is written.
`WriterSession` carries `store_root`, `store_id`, `profile` and the holdings
seam beside its writer factory. All four are optional on the constructor so
the portable tests that build a session from parts keep working, and the
opener supplies the production seam (`holdings_seam()`).

The store is optional because a session that only mints propositions has no
use for one, and the kernel's own acceptance rigs open sessions with no
store. A route that needs it and finds none is a protocol error (§3.3), not
a refusal of the invocation.

### 3.2 The scoped authority reaches the facade

`WriterSession.scoped` mints the scoped authority as today
(`scoped_authority(required, self.actor)`) and hands it to the
`ScopedWriter` explicitly, beside the corpus writer. The facade needs it for
the two routes, and today it is reachable only through the corpus writer's
private fields. No new `Authority(...)` construction appears; the permit
module's static test stands.

### 3.3 Four members on the facade

```python
class ScopedWriter:
    @property
    def actor(self) -> str: ...            # the session actor
    @property
    def store_id(self) -> str: ...         # SessionProtocolError without a store
    def operation_port(self) -> OperationPort: ...
    def holdings_context(self, *, instrument: str) -> ActContext: ...
```

`actor` is the session actor, which is also the scoped authority's actor,
so the `observer` a command passes to a boundary and the `actor` the
boundary stamps agree.

`operation_port()` returns the ledgered port of §4 over the durable port
bound to this invocation's scoped authority.

`holdings_context(instrument=…)` returns an `ActContext` with observer root
= the session's corpus root, store root = the session's, observer = the
actor, instrument as given, authority = the scoped authority, profile = the
session's, seam = the ledgered seam of §4. Without a store it raises
`SessionProtocolError`. The seven existing methods do not change.

The boundaries keep their own `authority.require` calls, so an invocation
whose declared capabilities do not cover a route is refused by the kernel
with `PermitExceeded` before an intent is appended, exactly as an
under-permitted `add` is.

## 4. The ledgered routes (`beliefs-5fe2e3`)

One new module, `beliefs/session/routes.py`, holds two thin wrappers that
share one recording helper. Neither changes what the boundaries do; each
lets the session hear what they commit.

### 4.1 `LedgeredPort`

An `OperationPort` over the invocation's durable port.

- `profile`, `authority`, `preflight`: delegate.
- `append_intent(payload)`: requires the invocation to be current, then
  delegates.
- `execute_fulfilling(plan, fulfills)`: under the session lock, requires
  currency, delegates, and records an act from `fulfills` (the intent
  digest), the entry digest the durable port returns, and the records of
  the plan (§4.3). The lock order is the one `ScopedWriter._act` uses,
  session then operation, and nothing is held while a workflow runs: the
  boundary reaches the port only before the run (the intent) and after it
  (the publication).
- `execute(plan)`: refused with `SessionProtocolError`. A session route
  commits only fulfilling writes; an unfulfilling commit would be an act
  with no intent for the ledger to name.
- `execute_fulfilling_guarded(...)`: refused with `SessionProtocolError`.
  The durable form returns the guard's reason, not an entry digest, so the
  act could not be ledgered faithfully. No command declares a production
  run; when one does, the guarded path is extended to return both and this
  refusal is lifted (§9).

### 4.2 `LedgeredSeam`

A `StoreActSeam` whose `publish_fulfilling(root, plan, intent)` requires
currency under the session lock, delegates, and records an act from the
intent digest, the entry digest and the plan's records. Every other field
passes through to the production seam unchanged.

For this, `StoreActSeam.publish_fulfilling` changes type from
`Callable[[Path, WritePlan, str], None]` to `Callable[[Path, WritePlan, str],
str]`, and `_store_publish_fulfilling` returns the registration's entry
digest, computed the way `DurableOperationPort.execute_fulfilling` already
computes it. The holdings acts ignore the return value, so nothing else in
the boundary moves.

### 4.3 Records from a plan

Both wrappers derive the act's `[uid, id]` pairs from the plan itself: each
`CreateOp`'s bytes are read back through `node_from_markdown`, the reader
the corpus and the boundary already use, and the node's `uid` and `id` are
the pair. A plan carrying any other op kind is refused with
`SessionProtocolError`; the run publication plan, the act-report plan and
the holdings observation plan are creates only.

`WriterSession._record_act` splits in two: the existing commit-shaped entry
stays for the seven corpus-write methods, and a general one takes
`(invocation, *, intent, entry, records)`. Both write the same ledger line
and append the same `ActLine`, so the ledger schema, `reconcile_sessions`
and science's audit are untouched. An act line for a run names the run
record; for a refused run, the act-report; for a holdings write, the
observation.

## 5. Reference rules (`beliefs-e5ab34`)

A new module, `beliefs/rules.py`, importable without constructing anything:

```python
OUTCOME_FILE = "outputs/outcome.txt"
OUTCOME_FILE_RULE = "beliefs/outcome-file/v1"
CONTENT_IDENTITY_RULE = "beliefs/content-identity-equality/v1"
OUTCOME_FILE_V1: RuleImplementation          # identity "impl-outcome-file-1"
REFERENCE_RULES: Mapping[str, RuleImplementation | EquivalenceImplementation]
```

`OUTCOME_FILE_V1` is the driver's interpretation rule moved into the kernel:
it maps the manifest's digest for `OUTCOME_FILE`, one of the three digests
of the canonical lines `supported`, `refuted`, `inconclusive` (each with a
trailing newline), to `{"outcome": …}`. A manifest without the file, or with
another digest, raises; `implementation_conforms` treats a raise as
non-conformance, and `freeze` refuses to bind it. It carries three fixtures,
one per outcome.

`REFERENCE_RULES` maps `OUTCOME_FILE_RULE` to `OUTCOME_FILE_V1` and
`CONTENT_IDENTITY_RULE` to `beliefs.replay.CONTENT_EQUALITY`, which keeps
its `impl-eq-1` identity and gains two manifest fixtures, equal and
unequal, so it is no longer conformant by vacuity.

### 5.1 Rule identities carry the author's scope

A rule identity is digested into every spec identity that binds it, so it
is permanent. The shape is `<scope>/<rule>/v<N>`: the scope names the
author, the version is the contract's, not the code's. A new digest scheme
for the outcome file would be `beliefs/outcome-file/v2`; a faster
implementation of the same contract is a new `impl-…` identity under the
same rule. The kernel's scope is `beliefs`. The reproduction driver took
`mm30-reproduction`; an operator's rules, when the kernel gives them a home,
take the operator's.

### 5.2 The driver maps onto the kernel

`python/tools/reproduction/spec.py` deletes its evaluator and its
equivalence lambda. Its `held_rules()` maps its existing identities,
`mm30-reproduction/outcome-file/v1` and the bare
`content-identity-equality/v1`, to `OUTCOME_FILE_V1` and `CONTENT_EQUALITY`.
The record's frozen spec identity is unchanged, because `freeze` digests
`(rule identity, implementation identity)` pairs and both pairs are the
pairs the record carries. The driver's design-gap finding (its rule sees
digests, not bytes) is unchanged in substance and now describes the kernel
rule too.

## 6. Replay over a closure

`replay(original: RunMinted | RunClosure, …)` reads only the closure's
recipe (boundary policy, identity, shape, inputs, parameters,
nondeterminism). The union and one line selecting `original.run` for a
minted result are the change. The surface verifies from a stored run
record's closure and never holds the minted result.

## 7. Errors

No new exception class. Everything a route can refuse is an existing one:

| Condition | Raised by | Class |
| --- | --- | --- |
| declared capabilities do not cover the route | the boundary's `require` | `PermitExceeded` |
| the invocation is not current | the ledgered port or seam | `SessionProtocolError` |
| `execute` or the guarded form on a ledgered port | the ledgered port | `SessionProtocolError` |
| a plan with a non-create op | the recording helper | `SessionProtocolError` |
| `store_id` or `holdings_context` on a store-less session | the facade | `SessionProtocolError` |
| a store root without a genesis at open | the opener | `SessionRefused` |
| a malformed store genesis | `store_identity` | `CorpusRootRefused` |
| a locator naming another store | the holdings boundary | `StoreIdMismatch` |

The first is a refusal of the invocation; the science dispatcher already
normalises it. The `SessionProtocolError` rows are programming errors on
the caller's side and surface as such.

## 8. Guarantees and their tests

Three layers on existing rigs.

**Portable, from parts** (`test_session_writer.py`'s `make_session` with the
recording port and a fake seam):

1. `actor` equals the session actor.
2. `store_id` and `holdings_context()` raise `SessionProtocolError` on a
   session built without a store.
3. `operation_port().execute_fulfilling(plan, fulfills)` ledgers one act
   whose `intent` is `fulfills`, whose `entry` is what the port returned,
   and whose records are the pairs parsed from the plan.
4. `execute` and `execute_fulfilling_guarded` raise `SessionProtocolError`
   and reach the inner port not at all.
5. A plan with a non-create op is refused before the inner port is reached.
6. After the invocation closes, `append_intent` and `execute_fulfilling`
   raise `SessionProtocolError`.
7. The ledgered seam's `publish_fulfilling` ledgers a holdings act the same
   way, and its other fields are the inner seam's.
8. A permit narrowed below `run` or `holdings` is refused by the boundary
   with `PermitExceeded` before any intent is appended (the recording port
   saw no `append_intent`).

**Durable** (`acceptance/test_session_acceptance.py`'s rig):

9. Opening with an initialised store root exposes its `store_id` through a
   scoped writer; opening on a root without a genesis raises
   `SessionRefused` and leaves no ledger directory.
10. One holdings `write` through `holdings_context` publishes an
    observation whose act line's entry digest is the chain entry that
    carries it.
11. One run publication through `operation_port()` from a fixture closure
    (`publication_plan`) is ledgered the same way.
12. `reconcile_sessions` over a session holding both lines reports no
    finding beyond what a proposition-only session reports.

**Rules and replay:**

13. Every entry of `REFERENCE_RULES` conforms to its fixtures, and its key
    is a `beliefs/…/v1` identity.
14. The driver's `frozen().identity` equals the value the 2026-09-05
    reproduction record carries, pinned as a literal.
15. `replay` over `minted.run` returns what `replay` over `minted` returns.

**Store identity:**

16. A fresh `init_store_root` round-trips through `store_identity`; an
    empty directory and a corpus root return `None`; a malformed genesis
    raises `CorpusRootRefused`.

## 9. Limitations and open questions

- **Production runs.** The guarded execution path is outside this seam
  (§4.1). Lifting it means the durable guarded form returning the entry
  digest beside the reason; a one-line change to its callers when a command
  needs it.
- **One store per session.** The session binds one store root. A world
  with several stores needs either several sessions or a locator-keyed
  context; neither is asked for.
- **Records by re-reading.** Deriving pairs by parsing the plan's bytes is
  a read of what the boundary is about to write, not a second source of
  truth: the bytes are the node. If a future plan carries something other
  than nodes, the helper refuses rather than guesses.
- **Rule identities in the record.** The mm30 record keeps
  `mm30-reproduction/outcome-file/v1`; a spec frozen through the surface
  under `beliefs/outcome-file/v1` has a different identity, which the
  science design already accounts for (§8.3 there).

## 10. Task mapping

- `beliefs-2d9a55` — §2. Size xs. First: science's read context depends on
  it alone.
- `beliefs-5fe2e3` — §3, §4, §6. Size m.
- `beliefs-e5ab34` — §5. Size s. Independent of the other two.

The plan (`../plans/2026-09-09-session-routes.md`) attaches one step per
section to these tasks. The adoption ledger gains its row when the work
lands.
