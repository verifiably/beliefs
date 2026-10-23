# Session doors and ledger evidence for the publish and sharing acts — design

**Status:** approved for planning 2026-10-23 (review round 2); revised 2026-10-22 after
round 1 (the door entry checks, the evidence binding, and the guarded port's record
order) and 2026-10-23 for round 2's three minor corrections (the exception contract,
the restore door's subject, the fallback test's observation).
**Task:** `beliefs-f24fe9`.
**Requested by:** science's commons design
(`science docs/specs/2026-09-30-science-commons-design.md` §5, §7.4, §11), the command
framework's §3.3 and §4.4 amendments of 2026-10-01, and science's milestone 1a plan
(`science docs/plans/2026-10-22-science-commons-1a.md`, Tasks 4, 6, 7 and 8, whose
Interfaces blocks name the kernel names they assume).
**Amends:** the writer-session design (`docs/designs/2026-09-05-writer-session-design.md`
§3.2, §3.5, §5), the session-routes design (`docs/designs/2026-09-09-session-routes-design.md`
§4, the ledgered port), the publication-records design
(`docs/superpowers/specs/2026-09-22-publication-records-design.md` decision 7, the kernel
requirements), and the publish-act-local design
(`docs/superpowers/specs/2026-09-23-publish-act-local-design.md` §4.1, step 0's order).

## 1. Problem

Science's commons milestone 1a needs four things of the kernel's session surface that it
does not have.

1. **A requirement for the `sharing` write class.** The framework's §3.3 amendment maps
   `sharing` to the `lifecycle` and `registry` act families and no record kinds. Today
   `RequiredCapabilities.__post_init__` admits only command-reachable families, plus the
   one publication permit `publishes()` mints, so no requirement can name those two
   families and `scoped()` can never hand out a writer that holds them.
2. **Doors and evidence for the sharing acts.** `adopt` runs `restore_root` over a
   fetched copy and `admit_publication` over the session's world. Both are kernel acts
   that write outside any corpus chain, so the ledger has no line for them, and the
   framework's §4.4 condition for reaching a chain-less family is that its evidence is
   defined first: the pin the act wrote (corpus id, marker uid, head artifact identity,
   the marker's world id, pin source, location fetched from, verification verdict, and
   the transition made). Science's registry is rebuilt from exactly those lines.
3. **A door for the publish act.** `beliefs.publish.publish` and `resume_publish` take a
   raw `CorpusWriter` and write through its own operation port, so a publish run by a
   command reaches no session ledger: its binding revision and act report commit with
   no `act` line, and reconciliation would report them as uncovered registrations.
   Step 8 also commits through `execute_fulfilling_guarded`, which the ledgered port
   refuses today.
4. **A publication preview.** Science's `publish` dry run must show exactly what the act
   would freeze — the pinned view, the selection, the derived pins, the attribution
   entries — and cannot be allowed to disagree with it. Today that computation is the
   first half of `publish`'s step 0, inline, with no name a reader can call.

## 2. Decisions

1. **`RequiredCapabilities.sharing()` is a second kernel requirement.** Its permit is
   `WritePermit(frozenset(), frozenset({"lifecycle", "registry"}))`: no kinds, two
   families. It is minted the way `publishes()` is — under the construction route's
   context variable, as a member of `KERNEL_REQUIREMENTS`, which becomes a two-element
   set — so an ordinary declaration that names either family, or that compiles to this
   exact permit, still refuses. `COMMAND_REACHABLE_FAMILIES` is unchanged.
   *Rejected:* adding `lifecycle` and `registry` to the command-reachable set. Every
   declaration could then name them, and `for_kinds` would admit routes that write with
   no chain evidence.

2. **One new ledger line kind, `sharing`, carries the pin.** Its fields are exactly the
   evidence the framework's §4.4 amendment defines, plus the invocation and a timestamp:
   `invocation`, `corpus`, `marker`, `artifact`, `world`, `view`, `source`, `location`,
   `verdict`, `transition`, `at`. These are the field names science's `SharingLine`
   protocol already declares (its branch `commons-1a`, `python/src/science/sharing.py`).
   The transitions are the closed set `bound`, `fetched`, `admitted`, `mounted`,
   `retired`. There is no `inspected`: inspection is `evaluate_copy`, which writes
   nothing and takes no authority, so it leaves no line. `view` is the marker's
   `published_from.view`, which is `str(intent.view)`: any `VIEW_KINDS` address
   (project, question, hypothesis, topic, theme) pinned to the revision the publish
   resolved, so the line admits a pinned address with or without a subordinate part
   and refuses an unpinned one.
   *Rejected:* an `act` line with empty records for a sharing act. An `act` line names a
   chain registration, and reconciliation matches it against a chain; a sharing act has
   no registration to match, and the line would be reported as unverified.

3. **A sharing line is appended by the invocation that made the transition, under the
   session lock, after the act.** The two act doors (decision 5) run the kernel act and
   then append the line; `record_sharing` appends a line for a transition that has no
   kernel act. Every sharing line names the current invocation, as `select` does, and an
   invocation may hold any number of them in order. The index learns a line only after
   its append returns, and a failed append is §3.2's terminal `LedgerFailed` state.
   *Rejected:* appending the line before the act, as an intent. The ledger would then
   claim a transition that may not have happened, and the §7.1 comparison for this
   class (ledger-versus-registry) would read the claim as a discrepancy on every crash.

4. **The act doors determine `verdict` and `transition`; `record_sharing` takes them.**
   `SharingEvidence` is the seven pin facts a caller knows before any act: `corpus`,
   `marker`, `artifact`, `world`, `view`, `source`, `location`. `restore_root` ledgers
   `fetched` with the restore report's `outcome` as the verdict, whatever that outcome
   is; `admit_publication` ledgers `admitted` with the arrival report's `outcome`.
   `record_sharing(evidence, *, transition, verdict)` admits only `bound` and `mounted`:
   `fetched` and `admitted` are act-backed and come only from their doors, and
   `retired` is backed by `World.retire`, whose door is milestone 1b's (§8).

   **Which facts a door verifies, and which it takes on attestation.** The two act
   doors bind the evidence to the root they act on before any effect, and refuse
   `SharingEvidenceDisagrees(field, claimed, found)` (a `WriteRefused`) on the first
   disagreement, in this order:
   - `corpus` equals the subject's corpus id (`restore_root`) and the root's manifest
     corpus id (both doors; the copy's `corpus.yaml` is readable before any grant);
   - `artifact` equals the sha256 of the canonical bytes of one carrier in `observers`
     whose decoded head artifact's subject is `CorpusSubject(corpus)` — the identity
     the binding and the transport mark already record (`ArtifactCarrier.data` retains
     the bytes);
   - `marker`, `world` and `view` equal the root's own marker: the door reads the root's
     records, requires the publication layout (`require_publication_layout`, which
     `admit_publication` already runs and which the restore door now runs first,
     refusing `PublicationArrivalRefused` before the act when the layout is wrong),
     and compares the marker's `uid` and its `published_from` `world_id` and `view`.
   `source` and `location` are the caller's attestations: the kernel holds no record
   of where bytes came from or which binding sourced them. A `record_sharing` line
   (`bound`, `mounted`) is attestation in every field; its truth is science's
   ledger-versus-registry comparison to establish (decision 11).
   *Rejected:* taking the evidence on trust in the act doors. Well-formed evidence
   naming publication B beside publication A's root would admit A and ledger B, and
   replay would rebuild a pin the act never established. *Also rejected:* verifying
   `marker`, `world` and `view` only after a validated restore. A disagreement found
   after the grant would leave a transition with no line.
   *Rejected:* one evidence value carrying all nine fields into every door. A caller
   cannot know an act's verdict before the act, and a door that overwrote a supplied
   verdict would be defensive where it should be explicit.

5. **Two sharing doors on `ScopedWriter`, under the scoped authority.**
   `restore_root(copy, subject, observers, *, evidence)` runs `beliefs.root.restore_root`
   with the scoped writer's authority. `admit_publication(root, observers, *, evidence)`
   opens the session's world under the scoped authority and runs
   `beliefs.publication_arrival.admit_publication` over it, so the admission record
   carries the session actor. Each door requires its family of the scoped authority
   first — `lifecycle` for `restore_root`, `registry` for `admit_publication` — before
   any effect: the acts' own checks sit after verification (`restore_root` requires at
   its grant, which a refusing evaluation never reaches; `admit_arrival` requires at
   the admission core, after the layout and chain checks), so without the door's own
   check a writer scoped to less would ledger a refusing verdict, or fail a layout
   check, in place of `PermitExceeded`. Each door's order is: the session lock;
   liveness and currency (`SessionProtocolError` for a stale, abandoned or closed
   writer, before any read of the copy); the family check; the evidence binding of
   decision 4; the act; the line; release. Both hold the session lock across the act
   and the line, exactly as `_act` does, so a close or re-claim cannot fall between a
   committed transition and its line. The lock order stays session, then the act's own locks (the copy's root, the
   world root); nothing takes either before the session lock.
   *Rejected:* a door that takes a caller-opened `World`. The caller holds no authority
   to open one with, and a `World` opened under another authority would stamp another
   actor on the admission record.

6. **The session holds its world configuration.** `WriterSession.__init__` gains
   `world_config: WorldConfig | None = None`; `open_attended_session` passes the one it
   validates. When given, its `world_id` must equal the `world_id` argument. The
   publish and admit doors open a `World` from it per call, under the scoped authority;
   a session opened without one refuses those doors with `SessionProtocolError`, as the
   holdings route refuses without a store.
   *Rejected:* opening the world once at session open and sharing it. A `World` binds
   one authority, and each invocation's authority is narrowed from its own requirement.

7. **The publish door runs the existing act with the session's parts.**
   `ScopedWriter.publish(*, view, destination, operations_root, staging_profile,
   transport=None)` and `resume_publish(*, event_token, operations_root,
   staging_profile, transport=None)` call `beliefs.publish.publish` and `resume_publish`
   with the scoped `CorpusWriter`, the session's coordination resolver (a session
   without one refuses `CoordinationUnavailable`), a `World` opened under the scoped
   authority (decision 6), this invocation's ledgered operation port, the ledger's UTC
   clock, the production moment seam, and the caller's transport. The acts' own permit
   checks run unchanged. Before delegating, each door takes the session lock and
   requires liveness and currency, then requires the publication permit of the scoped
   authority — `publish.require_publishes(authority)`, the act's own check made public
   — and only then opens the world, because `open_world` resolves recovery on the
   world root before the act's check would run; the lock is released before the act
   runs. A stale writer therefore refuses `SessionProtocolError` before it can touch
   the operations root, and `resume_publish` in particular cannot reach
   `transport.push` (which `_resume_from_mark` runs before any port call) or discard a
   completed attempt's operation directory (which the closed-and-bound path does
   without the port) under an invocation that is no longer current. What remains is
   the window every route has between a check and its next ledgered write: an
   invocation closed by another thread after the entry check and before the port is
   reached is refused at the port, after any upload that step 7 made in between, and
   the attempt stays `unfinished` with its mark, exactly as a crash there would leave
   it. The door ledgers what reaches the write root
   through the port — the refusal report, or the binding revision with its report — as
   `act` lines, and nothing from the staging root, the export, or the publication
   corpus: those are not the session's corpus, and science's ledger-rebuilt report
   reads the binding from the configured roots.
   *Rejected:* a door that re-implements the act's steps. There is one publish act, and
   cuts 39, 40, 42 and 46 discharged it.

8. **The ledgered port learns the guarded commit.** `OperationPort.execute_fulfilling_guarded`
   returns `GuardedCommit(entry: str, reason: str | None)`: the registration digest read
   back from the chain, as `execute_fulfilling` already reads it, and the guard's reason
   when the fallback plan committed. `LedgeredPort` implements it under the session
   lock: currency; the primary plan's records read and validated by `plan_records`
   before delegation, as `execute_fulfilling` does; the inner commit with the fallback
   wrapped so that the records of the plan it returns are read and validated before
   the plan reaches the durable port; then one `act` line carrying the records of
   whichever plan committed. A plan the route refuses (a non-create operation,
   record bytes that do not parse) is refused before any commit on either branch,
   never after it.
   The two production callers read `.reason` where they read the bare value:
   `_bind_publication`, and `execute_production_run` (`boundary.py`, the acquisition
   guard). The second is a consequence this design accepts: a production run through a
   session's operation port, which the ledgered port refused until now, commits and
   ledgers its records like the assessment run already does, and §6 holds it to that
   with one test. Every test double that implements the port (ten, under `tests/` and
   `tests/acceptance/`) returns the new value. `execute` stays refused: a session route
   commits only fulfilling writes.
   *Rejected:* keeping the bare `str | None` return and reading the digest back inside
   the ledgered port. The port holds no chain reader. *Also rejected:* implementing the
   guarded form for the binding door alone and keeping it refused for the production
   run. The port cannot tell its callers apart without a flag no caller should carry,
   and a route that commits chain-registered records under the session lock is what
   the ledger exists to record.

9. **Step 0's intent is appended under the caller's hold.** `publish` gains
   `hold: Callable[[], AbstractContextManager[object]] | None = None`, as `acquire`,
   `audit` and `recheck` have, and runs `_open_publication` inside it. The door passes
   the session's `_closing_hold`, so the intent's root lock is taken under the session
   lock — the one order every route takes — and not the other way round, which a
   ledgered `append_intent` inside `writer._operation` would otherwise produce. Steps
   1–9 take no hold: their write-root commits go through the ledgered port, which takes
   the session lock first and the root lock inside it, and the transport step holds no
   session lock at all (publish-act-remote decision 15's reasoning).
   *Rejected:* holding the session lock across the whole act. A remote publish uploads
   inside it.

10. **`publication_preview` is step 0 up to the intent, and `publish` calls it.**
    `beliefs.publish.publication_preview(world, resolver, view, *, own_pins) ->
    PublicationPreview` resolves the view, evaluates the selection at the current
    epoch, checks closure, derives the pins, computes the attribution entries, renders
    the records and asserts the snapshot rule (`_require_snapshot_records`), raising
    exactly the `PublicationRefused` reasons `publish` raises there today, in the order
    it raises them — `view-unresolved`, `divergent-view`, `selection-incomplete`,
    `empty-selection`, `closure-incomplete`, `pins-disagree` (from `derive_pins`),
    `attribution-holder-unregistered`, `attribution-contract-unpinned`,
    `attribution-source-invalid` — and `MalformedRecord` where a record fails the
    snapshot rule. It writes nothing and needs no authority: the read door's `World`
    suffices. `publish` keeps its own prior checks (the permit, the transport rule,
    `require_usable`, `publish-unfinished`), then calls the preview, then refuses
    `profile-disagrees` against the preview's pins, then opens the intent with the
    preview's pinned view as `expected_view` and freezes the preview's records and
    attributions into the snapshot and request. One ordering changes, deliberately:
    `profile-disagrees`, a check on the caller's staging profile that no dry run holds,
    today precedes the attribution refusals and the snapshot rule, and now follows
    them. No reason, field or message changes, and no test pins the old precedence. A
    dry run therefore raises the refusal the act would raise, or shows the facts the
    act would freeze.
    *Rejected:* a preview that returns `closure_missing` as data instead of refusing.
    The act refuses `closure-incomplete` naming the refs, and a preview that reported
    the same state as a success would disagree with it. The refusal's `refs` carry the
    missing addresses to the dry run's report.

11. **Reconciliation ignores `sharing` lines, and the kernel adds no registry comparison.**
    A sharing line names no chain registration, so `reconcile.py` skips it as it skips
    `select`. The §7.1 comparison for this class is ledger-versus-registry; the kernel
    exposes its two sides — `LedgerReader.sharing()` and the world's `status` and
    `registry()` — and the comparison is the framework's write-audit rule (framework
    §7.4), which science owns.
    *Rejected:* a kernel `audit_sharing` over every session ledger. The sharing registry
    the lines rebuild is science's artifact; the kernel would be auditing a file it
    does not define.

12. **Resuming a publish still requires the intent's actor.** The local design's
    decision 9 stands: `resume_publish` refuses under any other actor. Under a service
    the actor is `session:<id>`, so a remote attempt stranded after its transport mark
    by a session that never resumes it leaves its `(view, destination)` pair refusing
    `publish-unfinished` from every later session. This design does not amend that;
    science states the limitation (its Task 6), and a successor-actor resume is filed as
    follow-up work (§8).
    *Rejected:* admitting any actor of the same world. Cut 40 froze the actor rule and
    the report's observer; amending it is its own design against those rows.

13. **No conformance cut.** Decisions 1–11 are typed amendments inside the session and
    permit modules over the ledger's existing persistence path, plus a composition of
    acts already discharged by cuts 39, 40, 42 and 46. Ordinary unit tests hold them,
    on the conditions in §6: the sharing append is faulted at the write, the flush and
    the fsync, each fault leaving the index unchanged and the session terminal; the
    guarded ledgered commit is proven for both plan branches against the chain; and one
    end-to-end local publish through the door, over real roots, shows the ledger's act
    lines equal to the write root's committed registrations.
    *Rejected:* a cut. It would cost a lane, an N2 runner and a results record for line
    kinds and doors that add no new persistence path.

## 3. The ledger line

| `line` | fields |
|---|---|
| `sharing` | `invocation`; `corpus` (32 hex); `marker` (32 hex, `publication.marker_uid`'s form); `artifact` (64 hex, the head artifact's sha256); `world` (32 hex, the world id the marker claims); `view` (the marker's `published_from.view`: a view address pinned to its revision, `coord:<project>[/<local>]@<revision>`); `source` (a string the kernel does not interpret; may be empty); `location` (non-empty string); `verdict` (non-empty string); `transition` (one of `bound`, `fetched`, `admitted`, `mounted`, `retired`); `at` (UTC `%Y-%m-%dT%H:%M:%SZ`) |

Validation, in `_validated_line`: the key set is exactly the eleven above; each field
holds its form; `view` parses as a `CoordinationAddress` with `revision` set, `local`
set or not (decision 2). Protocol rules,
in `_parse`, beside the `select` rules: a `sharing` line names the invocation current at
its line (never opened, closed, abandoned by a later open, or no current invocation
each refuse), and no `sharing` follows `session-close`. There is no limit per
invocation. Violations raise `LedgerMalformed` naming the line, the whole ledger is
refused, and `read_ledger_evidence` reports it as `LedgerUnreadable`.

`LINE_KINDS` gains `sharing`. The `act`, `invocation-open`, `invocation-close`,
`select`, `session-open` and `session-close` shapes do not change, so ledgers written
before this amendment parse as before.

## 4. The API

### 4.1 Permits — `beliefs/permit.py`

```python
@classmethod
@_mints_the_kernel_requirement
def sharing(cls) -> RequiredCapabilities: ...   # WritePermit(frozenset(), {"lifecycle", "registry"})
```

`_SHARING_PERMIT` joins `_PUBLICATION_PERMIT` in `KERNEL_REQUIREMENTS`. `permit_covers`
is unchanged: the full ceiling covers it, and a ceiling lacking either family refuses
at `scoped()` naming the first missing family in sorted order (`lifecycle`).

### 4.2 Evidence and lines — `beliefs/session/ledger.py`

```python
TRANSITIONS = ("bound", "fetched", "admitted", "mounted", "retired")

@sealed @final @dataclass(frozen=True)
class SharingEvidence:
    corpus: str; marker: str; artifact: str; world: str; view: str; source: str; location: str
    # __post_init__ validates each field's form as §3 does

@sealed @final @dataclass(frozen=True)
class SharingLine:
    invocation: str; corpus: str; marker: str; artifact: str; world: str; view: str
    source: str; location: str; verdict: str; transition: str; at: str
```

`InvocationRecord` gains `sharing: tuple[SharingLine, ...]`. `LedgerReader.sharing()`
returns every sharing line in ledger order across invocations; `reader.invocation(id).sharing`
answers science's replay per invocation. Both are exported from `beliefs.session`.

### 4.3 The session — `beliefs/session/writer.py`

```python
WriterSession.__init__(..., world_config: WorldConfig | None = None)
def invocation_sharing(self, invocation_id: str) -> tuple[SharingLine, ...]
def _record_sharing(self, invocation: str, evidence: SharingEvidence, *, transition: str, verdict: str) -> SharingLine
```

`_record_sharing` runs under the session lock: liveness, currency (`SessionProtocolError`
when `invocation` is not current), the append with the ledger's discipline, then the
index. `invocation_sharing` requires a live session, as `invocation_acts` does.

The exception contract every door and route already holds is unchanged: a
non-current invocation (abandoned, closed, or another's) is `SessionProtocolError`; a
closed session is `SessionClosed`; a session whose ledger failed is
`SessionLedgerFailed`. The new doors raise the same three from the same conditions.

### 4.4 The scoped writer — `beliefs/session/writer.py`

```python
def record_sharing(self, evidence: SharingEvidence, *, transition: str, verdict: str) -> SharingLine
def restore_root(self, copy: Path, subject: CorpusSubject, observers: ObserverSet,
                 *, evidence: SharingEvidence) -> SharingLine
def admit_publication(self, root: Path, observers: ObserverSet, *, evidence: SharingEvidence) -> SharingLine
def publish(self, *, view: CoordinationAddress, destination: Destination, operations_root: Path,
            staging_profile: ProfileSpec, transport: Transport | None = None) -> PublishOutcome
def resume_publish(self, *, event_token: str, operations_root: Path, staging_profile: ProfileSpec,
                   transport: Transport | None = None) -> PublishOutcome
```

- `record_sharing` requires both `lifecycle` and `registry` of the scoped authority
  before appending (the sharing class's two families; a writer scoped to less raises
  `PermitExceeded` naming the first missing family), and refuses a `transition` outside
  `bound` and `mounted` with `ValueError`. It appends under the session lock and
  returns the line.
- `restore_root` and `admit_publication` take the session lock, check liveness and
  currency, require their family, bind the evidence (decision 4), run the act, append
  the line and return it. `restore_root` takes a `CorpusSubject` only and refuses any
  other subject type with `TypeError` before any check: the evidence binding needs a
  corpus id, a corpus manifest and a publication marker, which a store has none of.
  The kernel's `restore_root` keeps its store arm for callers outside the session. `restore_root`'s verdict is the report's
  `outcome`; the copy's lifecycle state, not the line, is what says whether the root
  is serviceable. `admit_publication`'s verdict is the arrival report's `outcome`; a
  refusal raised by the layout check or by verified arrival propagates and appends
  nothing, because no transition was made. `admit_publication` opens the session's
  world under the scoped authority (decision 6).
- `publish` and `resume_publish` check liveness, currency and the publication permit
  under the session lock, open the world, release the lock, and compose the act as
  decision 7 says, returning its outcome unchanged. Their other refusals are the
  act's own. `beliefs.publish.require_publishes(authority: Authority)` is the public
  form of today's `_require_publishes(writer)`, which the act keeps calling.

`pending_publishes` keeps its `CorpusWriter` parameter: it reads the written chain and
the operations root and writes nothing, so a reader that holds no permit opens a corpus
under `scoped_authority(RequiredCapabilities.none(), actor)` and calls it.

### 4.5 Errors — `beliefs/errors.py`

```python
class SharingEvidenceDisagrees(WriteRefused):
    field: str      # corpus | artifact | marker | world | view
    claimed: str    # the evidence's value
    found: str      # the root's, the subject's or the carrier's value
```

Raised by the two act doors before any effect (decision 4). `SessionProtocolError`,
`PermitExceeded`, `PublicationArrivalRefused` and the acts' own refusals keep their
meanings.

### 4.6 The routes — `beliefs/session/routes.py`, `beliefs/runrecord.py`

```python
@sealed @final @dataclass(frozen=True)
class GuardedCommit:
    entry: str            # the registration digest, read back from the chain
    reason: str | None    # the guard's reason when the fallback plan committed

OperationPort.execute_fulfilling_guarded(...) -> GuardedCommit
```

`DurableOperationPort` reads the digest back with `_registration_for` as
`execute_fulfilling` does. `LedgeredPort.execute_fulfilling_guarded` holds the session
lock, checks currency, runs the inner guarded commit with the fallback wrapped, and
ledgers one `act` line with `intent=fulfills`, `entry=commit.entry`, and the records of
the plan that committed. `_bind_publication` adapts to the new return value. Every test
double that implements the port follows the protocol.

### 4.7 The act — `beliefs/publish.py`

```python
@dataclass(frozen=True)
class PublicationPreview:
    view: CoordinationAddress            # pinned to the revision the selection was evaluated against
    epoch: str                           # the published epoch's packaging identity
    world_id: str
    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    pins: CorpusPins                     # the derived pins the staging profile must hold
    attributions: tuple[tuple[str, str, str], ...] | None   # None under a v2 coordination pin
    records: tuple[tuple[str, str], ...] # (address, canonical text) in selection order

def publication_preview(world: World, resolver: CoordinationResolver, view: CoordinationAddress,
                        *, own_pins: CorpusPins) -> PublicationPreview

def publish(..., hold: Callable[[], AbstractContextManager[object]] | None = None) -> PublishOutcome
```

`publish`'s step 0 becomes: the permit, the transport rule, `require_usable`, the
`publish-unfinished` check, `publication_preview(world, resolver, view,
own_pins=load_manifest(writer.root).profile)`, `profile-disagrees` against
`preview.pins`, then `_open_publication` under `hold` with `expected_view=preview.view`,
and the snapshot and request built from the preview. No refusal reason or message
changes, and only `profile-disagrees` moves (decision 10); `test_publication_attribution.py`'s fixtures, which patch
`current_epoch`, `open_world_view` and `evaluate_query` on the module, keep working
because the preview reads those names from the same module.

## 5. What does not change

- The seven corpus-write methods, the run, holdings, acquisition, audit and re-check
  routes, and their lock discipline.
- The `act`, `select` and session line shapes; reconciliation's reading of them; the
  frozen cut-19 sabotage strings pinned into `session/ledger.py` and
  `session/writer.py` (`n2_arms_cut19.py`): the new code is added beside them, and
  `test_arm_staleness.py` holds that no pinned block moved.
- `publish`'s steps 1–9, `resume_publish`'s readings, the request, snapshot and mark
  formats, and every refusal the acts raise.
- `World.retire`: no door this slice (§8).
- Science's write classes: the kernel does not know them. The framework maps `sharing`
  to `RequiredCapabilities.sharing()` and `publishes` to `publishes()` on its side.

## 6. Testing

In `test_permit.py`, `test_session_ledger.py`, `test_session_writer.py`,
`test_session_routes.py`, `test_publish.py` and one new end-to-end module:

- **Permit.** `sharing()` constructs with exactly the two families and no kinds;
  `KERNEL_REQUIREMENTS` holds exactly the two kernel permits; a direct
  `RequiredCapabilities(WritePermit(frozenset(), {"lifecycle", "registry"}))` and a
  `for_kinds` route that would compile to it refuse; `scoped(sharing(), id)` under a
  full ceiling yields a writer whose authority requires `lifecycle` and `registry`
  without error and refuses `corpus-write`; a ceiling without `registry` refuses at
  `scoped` naming it.
- **Line shape, reader side.** Each of these raw ledgers raises `LedgerMalformed`
  naming the line: a `sharing` with a missing or extra key; each field in a wrong form
  (a 31-hex corpus, a 63-hex artifact, an unpinned `view`, an empty
  `location`, an unknown `transition`); a `sharing` naming an unopened, a closed, an
  abandoned, or no current invocation; a `sharing` after `session-close`. A ledger with
  three sharing lines in one invocation (one naming a subordinate pinned view) and
  one in another round-trips through
  `reader.sharing()` and `reader.invocation(id).sharing` in ledger order.
- **Writer side.** `record_sharing` appends and the index reads it back through
  `invocation_sharing` before the method returns; `fetched`, `admitted` and `retired`
  refuse `ValueError` and append nothing; a writer scoped to `coordination()` refuses
  `PermitExceeded` naming `lifecycle`; a writer whose invocation is not current refuses
  `SessionProtocolError` and appends nothing.
- **Append failure.** The `sharing` append is faulted at `write` (a short write), at
  `flush` and at `os.fsync`, one case each: the call raises `SessionLedgerFailed`; the
  invocation's index entry holds no sharing line (asserted on the index); every later
  method raises `SessionLedgerFailed`; nothing after the fault reaches the file.
- **The sharing doors, over real roots on the certified volume.** A publication
  exported by the existing local publish fixture is copied without its metadata
  sibling; `restore_root` through a sharing-scoped writer grants read serviceability
  (`read_lifecycle_state`) and ledgers `fetched` with verdict `validated`; a copy whose
  artifact disagrees ledgers `fetched` with the report's refusing outcome and grants
  nothing. `admit_publication` through the same writer admits the restored copy into
  the session's world as `ReplicaOf` with the session actor on the admission record,
  and ledgers `admitted`; a copy missing its marker raises `PublicationArrivalRefused`
  from either door before the act, and appends nothing. A writer scoped to
  `coordination()` refuses both doors `PermitExceeded` before any effect; a writer
  whose invocation is not current refuses `SessionProtocolError`, and one whose
  session is closed refuses `SessionClosed`, before reading the copy; a
  `StoreSubject` refuses `TypeError`. Mismatched
  evidence, one case per verified field — a corpus naming another publication's root,
  an artifact that is no carrier's identity, a marker uid, world id or view that is
  not the root's marker's — refuses `SharingEvidenceDisagrees` naming the field,
  before the act: the copy stays unserviceable, the world's registry is unchanged,
  and no line is appended. A session opened without a world configuration
  refuses `admit_publication` with `SessionProtocolError`.
- **The guarded ledgered commit.** Through `LedgeredPort` over a durable port: a guard
  returning `None` commits the plan and ledgers its records with the committed
  registration's digest; a guard returning a reason commits the fallback and ledgers
  the fallback's records with that registration's digest; `GuardedCommit.reason`
  carries the reason; a non-current invocation refuses before the inner port is
  reached; a primary plan holding a `DeleteOp` refuses `SessionProtocolError` before
  the inner port is called; a fallback plan holding one refuses `SessionProtocolError`
  from inside the delegated guarded call, after the guard ran and before the fallback
  plan reaches the durable port — asserted as no commit, no registration fulfilling
  the intent on the chain, and no ledger line. `execute` still refuses. A production run through the session's port
  (`execute_production_run` with the acquisition guard, over the cut-3 fixtures
  `test_session_routes.py` already uses for the assessment run) commits and ledgers
  its records, and reconciliation reports no finding. Every port double under
  `tests/` and `tests/acceptance/` returns `GuardedCommit`, and
  `test_operation_port.py`'s protocol checks hold the durable port to it.
- **The publish door, end to end.** Over the cut-40 fixture's shape, opened as an
  attended session whose write root is one of the configured roots: a local publish
  through `ScopedWriter.publish` returns `Published`, the ledger holds one `act` line
  whose `intent` is the publish intent's digest, whose `entry` is the committed
  registration's digest and whose records are the binding and the report, and
  `reconcile_sessions` reports no finding for the session. A refused publish (an
  export collision) ledgers one `act` line for the refusal report. `resume_publish`
  through a second invocation of the same session, after a crash injected at a step
  boundary, binds and ledgers under that invocation. A writer retained after its
  invocation closed refuses `SessionProtocolError`, and one from a closed session
  refuses `SessionClosed`, on both doors: a transport spy records no `push`, and the operation directory's files
  (the request, the snapshot, a transport mark) are byte-for-byte unchanged, a
  completed attempt's directory included. A writer scoped to `coordination()`
  refuses `PermitExceeded` with nothing written, no line, and no recovery resolved on
  the world root (the world is not opened). A
  session with no coordination resolver refuses `CoordinationUnavailable`.
- **The preview.** `publication_preview` over the same fixture returns the pinned view,
  the epoch identity, the selection, the derived pins, `None` attributions under v2 and
  the entries under v3, and records equal to the snapshot a subsequent `publish`
  freezes; each refusal of §2 decision 10 raises from the preview with the same reason
  and fields `publish` raised before this change (the existing `test_publish*` and
  attribution tests hold the order).
- **Arm staleness.** `test_arm_staleness.py` stays green.
- **The inventories.** `test_permit_boundary.py`'s entry-point inventory and
  `test_permit_entry_points.py`'s cases stay closed in both directions; the ledgered
  guarded form joins the route exemptions beside `execute_fulfilling`.

## 7. What changes elsewhere

- The writer-session design gets a dated amendment section: the `sharing` row, the
  evidence value, §4's signatures, and decisions 3–7; the session-routes design a note
  on the guarded ledgered commit; the publish-act-local design a note on `hold` and
  the preview.
- The adoption ledger gets a line under the session work naming this amendment.
- Science's milestone 1a plan adapts its assumed names and one ordering: `restore` is
  `restore_root`, and it requires the publication layout before the act, so the
  layout refusal its Task 8 places after the restore (step 7) now arrives from the
  restore door with no pin written;
  `SharingEvidence` carries seven fields and `record_sharing` takes `transition` and
  `verdict` as keywords; `publication_preview` takes `own_pins` and raises
  `closure-incomplete` rather than returning `closure_missing`; `pending_publishes`
  needs a corpus opened under `RequiredCapabilities.none()`.

## 8. Follow-up work filed

- A successor-actor resume for a publish stranded by a session that will never
  resume it (decision 12), as its own design against cut 40's actor rows:
  `beliefs-b427db`.
- The `retired` transition's door, `World.retire` under the scoped authority, for
  science's milestone 1b; `record_sharing` admits `retired` only once that door exists:
  `beliefs-a989fb`.
- The existing follow-up from the selection design: the reader holds `act` and
  `invocation-close` to the writer's currency rule.

## Amendment — 2026-10-23 (execution)

Three points were settled while building; the body above is unchanged.

- **§4.6's readback (R6).** The durable port's guarded readback is
  `root.py`'s `_committed_registration_for`, not `_registration_for`: it returns the
  one registration fulfilling the intent whose settlement committed, requiring
  exactly one (`ExecutionError` otherwise). The engine refuses a second committed
  fulfilment of one intent, so this is exact and fails early where "latest" would
  pick an uncommitted registration if settlement lagged. `execute_fulfilling` is
  unchanged.
- **Decision 5's parameter name (R10).** The restore door is
  `restore_root(root, subject, observers, *, evidence)`: `copy` is a byte-mutation
  name the capability boundary's raw-write scan rejects. Science's Interfaces adapt.
  The subject `TypeError` and argument-type checks run before the session lock, and
  `admit_publication` refuses a missing world configuration before the evidence
  binding (both before any effect).
- **Decision 7's resume door (R16).** `resume_publish`'s door opens the session's
  world, which the act's `resume_publish` does not use, so it needs a world
  configuration. Decision 7's guarantee is at entry only: a writer stale at door
  entry refuses before any effect; an invocation closed by another thread after
  entry is the accepted window.
