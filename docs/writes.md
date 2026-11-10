# Writes

Type: protocol; document types 1. Currently unversioned. This document describes
how a write reaches a corpus: the authority a writer is bound to, an ordinary write,
the attended writer session and its ledger, operations and their act reports,
verification and publication. It then covers what is refused and how an
interrupted write recovers. The records being written are described in
[records.md](records.md), and the contracts that type them in
[contracts.md](contracts.md).

## Participants

- **Caller.** A library user, or the `science` layer acting for a person or an
  agent. A caller never supplies an actor on a call.
- **Authority.** A write permit together with an actor, bound once when a writer
  is constructed.
- **Writer.** A `CorpusWriter`, bound to one corpus root, one authority and one
  compiled profile.
- **Engine.** The certified `atoms` engine. `beliefs.root` is the only module that
  imports it, and every write to a corpus root goes through it.
- **Session.** A `WriterSession`, which writes one corpus root and records every
  step in its ledger.
- **Recipient.** A world that admits a published corpus.

## Authority and permits

A `WritePermit` has two closed sets: the record kinds a holder may write, and the
act families it may perform. The families are `corpus-write`, `run`, `holdings`,
`registry`, `epoch`, `lifecycle` and `publish`. An `Authority` binds a permit to an
actor, which must be a non-empty string that `science.identity.v1` can encode.

Every write entry point calls `authority.require(family, kinds)` before its first
effect. If the family or any kind falls outside the permit, the call raises
`PermitExceeded` and writes nothing. A kind outside the kernel and coordination
inventory is admitted only by an `ungoverned` permit, and only for `corpus-write`.
`WritePermit.full()` is the full permit. The read door, `open_world_read`, binds
the empty permit, so every act through it is refused.

## Opening a corpus

1. `init_corpus_root(root, authority=...)` requires `lifecycle` and
   [registers](glossary.md#registration) the root with the engine. A root must be
   registered explicitly; a write against an unregistered root is refused.
2. `open_corpus(root, authority=..., profile=...)` returns a writer. The profile's
   base contract must be the one the runtime ships. The root does not need a
   manifest yet.
3. `writer.adopt_manifest(profile=pins)` requires `lifecycle` and writes
   `corpus.yaml` with a fresh corpus id. It refuses when a manifest is already
   present, or when the pins it is given disagree with the writer's profile.

## An ordinary write

`add`, `supersede`, `revise`, `retract`, `attest_coreference`,
`correct_identifier`, `delete`, `mint_coordination` and `revise_coordination` are
ordinary writes. Each runs these steps in order, except `delete` (below):

1. Require the permit for the act's family and kind.
2. Take the root's lock, check that the manifest pins agree with the profile, and
   recover the root if an earlier write left it unresolved.
3. Run the refusals: the kinds this door does not admit, the facet, identity,
   eligibility and signature checks in [records.md](records.md), lossless
   rendering, and collision with an existing record.
4. Build one `nodes` write plan and submit it as one engine transaction. The
   transaction applies completely or not at all.

A kind with its own door is refused through `add`. Holdings observations, act
reports and publication records have no ordinary door at all. `delete` removes one
record's file. It takes the lock, checks the pins and resolves its target first,
then requires the permit on the target's kind, then refuses act reports, holdings
observations, coordination kinds, exposure events and reservation assignments
(`DeletionKindExcluded`).

## Writer sessions

The `science` layer writes through a session:

1. `open_attended_session(world_config, operations_root, write_root=..., profile=...)`
   opens one. `write_root` must be one of the world's configured corpus roots, and
   `mounts`, when given, must name every configured root exactly once. The corpus
   must have a manifest whose pins agree with the profile, and its
   [chain](glossary.md#roots-log) must be well-formed. The session's actor is
   `session:<32 hex>`, derived from a fresh session id. The session writes
   `session-open` to its ledger and reconciles the other sessions' ledgers.
2. `claim_invocation(id, command, input_digest)` writes `invocation-open` for a new
   id and returns `ClaimFresh`. For an id it has seen, it returns `ClaimDone` (with
   the recorded outcome), `ClaimOpen` or `ClaimMismatch`, and writes nothing.
3. `scoped(required, id)` returns a `ScopedWriter` whose permit is exactly
   `required`, as long as the session's ceiling covers it; otherwise it raises
   `PermitExceeded`.
4. Each write through the scoped writer first checks that the invocation is the
   current one. It then appends a `corpus-write` operation intent, commits the
   write as the transaction that fulfils that intent, and writes an `act` line that
   names the intent, the [registration](glossary.md#registration) and the records
   written. A holdings act through the session (`holdings_context`) also writes one
   `act` line for every store transaction it commits: a `write`, `delete` or `move`,
   and each object a `tree-write` creates (the tree file included).
5. `close_invocation(id, outcome)` writes `invocation-close`, and `close()` writes
   `session-close`.

The ledger is the append-only file `<operations_root>/sessions/<id>/ledger.v1`.
Every line is written, flushed and fsynced before the call that wrote it returns.

An `act` line carries `invocation`, `corpus`, `entry`, `intent` and `records`.
`corpus` is the id of the chain the entry is on: the corpus id for a corpus write,
and the store id (the store genesis's `store_id`) for a store transaction. For a
store transaction, `entry` is the store registration's digest as the engine
returned it, `intent` is the holdings act's intent on the corpus chain (for a move,
the move-source intent; for a tree-write, its one intent on every create), and
`records` is empty. The session holds its lock, then the store root's operation
lock, across the store call and its `act` line; holdings takes the corpus root's
operation lock only around an intent append or a publication, so a writer holds one
operation lock at a time.

## Citations across mounts

A session with read mounts writes only to its write root, but a record may cite
records in any mount. Citations include an assessment's run and its datasets, a
spec's target, a verification's assessment and a composite's members. Each mount
is opened inside that mount's [capture hold](glossary.md#capture-hold), which never
waits. A write that changes a record (`supersede`, `revise`, `delete`) resolves
that record in the write root only.

## Operations

An operation is an act made of several member acts. Its kind is one of `acquisition`,
`audit`, `consolidate`, `corpus-write`, `import`, `move`, `publish`, `re-check` and
`run-attempt`. An operation proceeds in three steps:

1. Append an intent to [the root's log](glossary.md#roots-log), before any member
   act. The intent is `{kind, event_token, actor}`, and its actor must be the
   writer's.
2. Perform the member acts.
3. Close by registering one terminal record that fulfils the intent. That record is
   the operation's act report, or a run closure for a run.

`publish` opens with its own intent, `science.publish-intent.v1`. A `corpus-write`
is closed by its own registration and writes no act report. An `acquisition` mints
its dataset and its act report in the same transaction.

Completion is read from the log and never stored:

- `closed`: a registration carrying the intent's token points to a
  [held](glossary.md#held) record of the matching shape;
- `indeterminate`: a matching registration's record is not held here;
- `unfinished`: neither.

### Sealing an acquisition

`seal_acquisition(ctx, writer, request, *, standing=None, unsettled=frozenset())`
(`holdings/seal.py`) is the second `acquisition` operation; its session route is
`ScopedWriter.seal_acquisition(request, *, instrument, standing=None, unsettled=frozenset())`.
A program fetches or imports a set of files into a work area and writes its
[acquisition log](records.md#acquisition-logs); the seal verifies both and holds the
set as one tree dataset. The `SealRequest` gives the dataset's `title`, `locator` and
optional `domain_facets`, as an acquisition request does, the `tree_name` of its one
resource, `members` (the file for each tree path), the `log` file, `origin`,
`fetched_by` and, for an import, `source_journals` (each a name and a file). The seal
runs these steps:

1. Check, before any effect. A missing permit (`holdings` for `holdings-observation`,
   `corpus-write` for `dataset` and `act-report`) raises `PermitExceeded`. Every other
   check raises `AcquisitionRefused` and writes nothing, except that an argument that is
   not a `SealRequest` raises `MalformedRecord` and a failed read of the store's genesis
   raises the engine's refusal:
   - the writer's root is the context's observer root, and an operation port exists;
   - every file of the work area lies outside the corpus and store roots;
   - the log parses and is its own canonical rendering, and its header's `origin` and
     `fetched_by` equal the request's;
   - the request's source journals are the header's, by name and in order, and each
     file has the digest the header gives it;
   - the tree of the log's `fetched` lines is non-empty, its paths are exactly the
     request's members, and each member file, hashed one at a time, has its line's
     digest and size;
   - each `standing` entry at a location the seal writes holds only observations of
     that location, and the dataset's shape is valid.
2. Append the `acquisition` intent.
3. Re-check each location the seal writes that `unsettled` names (the log's, a source
   journal's or the store-tree location). The seal keeps a head map, one entry per
   location, seeded from `standing`. A re-check runs with that location's heads, and the
   `found` or `absent` it publishes replaces them; every later act at that location
   supersedes it. An inconclusive re-check raises `AcquisitionRefused`: the seal writes
   nothing more and leaves the intent unfinished.
4. Write the log into the store at `<hex>/acquisition-log.jsonl`, and each
   source journal at `<hex>/<name>`, each with an ordinary holdings `write`. `<hex>` is
   the sha256 hex of the file's own bytes, with no set or tree component, so different
   bytes never share a path, no seal replaces bytes an earlier report binds, and sealing
   the same bytes again writes the same bytes to the same path.
5. Write the tree with the `tree-write` act
   ([records.md](records.md#datasets-sources-and-holdings)).
6. Close in one transaction, under `acquire`'s lock order. It mints the dataset, unless
   its address is already held, with `empirical-observation` set to
   `{locator, attested_by: actor, retrieval: <report id>}`, and the act report. The
   report's entries are a `managed-mutation` for the log and for each source journal,
   one for the store-tree location, the `acquisition-set` entry, and a
   `declaration-pin` when the dataset is minted.

The act context's `instrument` is the sealing tool: the act report and every
observation the seal mints carry it. `fetched_by`, who fetched the bytes, appears only in
the log header and the `acquisition-set` entry.

`standing` and `unsettled` are the caller's, keyed by canonical location and taken from
one holdings reduction: `standing` the current heads at each location the seal writes,
`unsettled` the locations that reduction blocks as unsettled. Entries at other locations
are ignored. That they are complete and current is the caller's precondition, which the
seal does not establish. A head left out stays unsuperseded beside the seal's new
observation, so an `absent` left there reads as contested beside the new `found`. An
unsettled location left out stays blocked, since a later matched write does not clear an
unmatched write intent.

An interrupted seal leaves its intent unfinished and only whole objects in the store.
Sealing the same set again, with `standing` and `unsettled` from a fresh reduction,
repairs it: step 3 re-checks the interrupted locations, the log and journals are written
with the same bytes, objects are create-only and reused only when they match, and a held
address is not minted again. Two different sets of identical bytes give one dataset and
two act reports, each naming its own log. No step scans the stored records once per
member.

## Verification

A verification compares two runs and is published through an ordinary `add`:

1. `build_verification(original, replayed, specs=..., held_rules=...,
   contract_identity=..., epoch=...)` takes two run closures. Both must be
   assessment runs or both dataset-production runs; a mixed pair is refused
   (`MixedShapes`). It returns an `AssessmentVerification` or a
   `DatasetProductionVerification`, carrying the comparison report, the scope and
   the verdict.
2. `publication_node(derived, assessment_ref=...)` builds the record. An
   assessment verification requires the corpus reference of its assessment, which
   becomes the `verifies` edge. A dataset-production verification takes none.
3. `writer.add(record)`, or a scoped writer's `add`, decodes the record, checks
   that its id recomputes from its fields, and checks its `verifies` target; see
   [records.md](records.md#verifications).

## Publication

`publish(writer, resolver, world, view=..., destination=..., operations_root=...,
staging_profile=..., clock=..., seam=...)` shares what a saved view selects; see
the function's signature for its optional arguments. It runs these steps:

1. Require the publish, `corpus-write`, `lifecycle` and `registry` families.
2. Resolve the view and evaluate it at the current [epoch](glossary.md#epoch).
   The publish is refused if the selection is incomplete (`selection-incomplete`),
   if it is empty (`empty-selection`), or if a selected record depends on one left
   out (`closure-incomplete`). Closure follows world relations, and a selected
   reservation assignment's `supersedes` edge as well, so a published successor
   carries its predecessor chain; other kinds' `supersedes` edges stay outside it.
3. Append the publish intent. Then write `selection.v1` and `request.v1`
   create-only under `<operations_root>/publish/<token>/`.
4. Stage the selected records, together with one `publication` marker, in a fresh
   corpus. Export it and reveal it at the destination. For a remote destination,
   transport it.
5. Write a `publication-binding` in the source corpus, and discard the operation
   directory.

The result is `Published`, `PublishRefused` or `PublishUnresolved`. Every publish
mints a new corpus. `admit_publication` admits one on the recipient's side only
when it holds exactly one consistent marker, holds no binding, and holds exactly the
records the marker's selection names.

## Failure

**Refusals.** A refusal is raised before any effect, and nothing is written. The
main ones are:

- `PermitExceeded`: the permit does not cover the act;
- `ContractMismatch`: the manifest pins disagree with the profile;
- `WriteRefused` and its subclasses (`ValidationRefused`, `EligibilityUnmet`,
  `CollisionRefused`, `RecordAlreadyMinted`, `ActorMismatch`, and `ReservationRefused`,
  whose `code` names the exposure or reservation check that failed; see
  [records.md](records.md#write-rules)): the record fails a
  check;
- `SignatureRefused`: a relation breaks an enforced signature;
- `SessionRefused`: a session cannot open;
- `PublicationRefused`: a publish is refused before its intent, and the exception
  names the reason.

Two further refusals concern read mounts. A read mount whose operation lock is held
refuses a citing write with `BuildContended`; the write does not queue, and the
caller retries. A citation held by several corpora with different content is
refused with `AddressMapConflict`.

**Engine failures.** Engine failures surface as `ExecutionError`. When
`applied == 0`, the engine refused before changing anything. This covers an
unregistered root, a failed precondition and `CapabilityUnavailable`, which is
preserved as the cause. `CapabilityUnavailable` means the host's kernel and volume
are not a tuple `atoms` certifies, and no write can happen there until they are.
When `applied` is `None`, the engine could not prove that the disk is back in its
state before the plan.

**Interruption and recovery.** A root is unresolved when a process first opens it,
and a writer marks it unresolved again before each submission. The first write on
an unresolved root asks the engine to recover it, which settles any transaction a
crash or an `applied=None` failure left open. The writer then rebuilds its index
before reading anything. An interrupted operation reads as `unfinished` from its
intent. An interrupted publish resumes with `resume_publish(event_token=...)`
under the same actor, and `pending_publishes` lists the unfinished ones.

**Sessions.** A failed ledger append makes the session terminal
(`SessionLedgerFailed`). So does a store call through a session that raises
anything other than `StoreWriteRefused` for its arguments (a malformed path, an
`objects/` path, a create outside `objects/sha256/`), which is refused before
anything reaches the engine and leaves the session live. The engine registers a
store transaction before it applies its effects, and an effect that meets drift
rolls back, settles the registration as not committed and raises a routine refusal.
A refusal therefore does not prove that nothing registered, and no `act` line can
describe a rolled-back registration, so the ledger is marked failed before the
exception propagates. What the act then raises depends on the act: `write` still
reports a routine engine refusal as `StoreWriteRefused`, after the ledger has
failed; `delete` and `move` raise the engine's error itself; a `tree-write` raises
`SessionLedgerFailed`, because the failed session refuses the read of the object
that follows a refused create, so its read-again tolerance applies only outside a
session. The failed ledger cannot close its invocation or the session.
This ends attended sessions too, on any such failure: an engine refusal caused by a
write outside the session, and also a missing source for a `delete` or `move`,
which fails before anything is submitted. A write from an invocation that is not
the current one raises `SessionProtocolError`. When a session opens, `reconcile_sessions` compares
every other session's ledger with the chains. It reports findings such as
`session-unclosed`, `session-intent-unclaimed` and `session-act-unverified`.

**Gaps.** Reconciliation reports, but it writes nothing and recovers nothing. A
contended or refused write is not retried automatically; the caller retries it.
