# The ledgered retirement door for an adopted publication — design

**Status:** approved by the user at revision 3, `578a014` (round 3, 2026-10-29, verdict
accept, no findings; reviewer `codex/gpt-6-astra`). Not yet implemented: beliefs-a989fb
builds the door (§6). Revision 2 (`f72802f`) had the user's
forwarded review (round 2, verdict revise: Important 1, Minor 1; reviewer
`codex/gpt-6-astra`), which supported every decision and corrected two of §5's test
expectations: a failed append can leave a complete line on disk (decision 6 and §5's
recovery test now say what the file holds per fault), and the departed refusal keeps its
existing record (§5's no-effect refusals). Revision 1 (`56089e6`) had a builder check
(round 1: one delivery question, four inaccurate claims about the code; reviewer
`claude-code`), all resolved: §3 decisions 3–5 and §5 correct the claims, §6 answers the
question.
**Task:** beliefs-c0d952 (child of beliefs-182296); its implementation idea beliefs-a989fb
waits on it, and science's milestone 1b tail (sci-9104fb Tasks 13–15) waits on that.
**Brief:** `../../notes/2026-10-24-publication-session-follow-ups-brief.md`.
**Requested by:** science's milestone 1b design
(`science docs/specs/2026-10-28-science-commons-1b-design.md` §5.7, the paragraph beginning
"A predecessor that is required stays `mounted`") and plan
(`science docs/plans/2026-10-28-science-commons-1b.md`, Task 13), which state the
requirement on this door rather than a mechanism.
**Amends:** the session sharing and publish doors design
(`2026-10-22-session-sharing-and-publish-doors-design.md`, decision 4's last sentence and
§8's second bullet, which defer `retired` to "World.retire's door").
**Baseline:** beliefs main `95ead8d`; science main `2546bdd`.

## 1. Problem

The sharing design's ledger carries five transitions — `bound`, `fetched`, `admitted`,
`mounted`, `retired` — and gives four of them a route: `restore_root` ledgers `fetched`,
`admit_publication` ledgers `admitted`, and `record_sharing` ledgers `bound` and
`mounted`. `retired` has none. `record_sharing` refuses it by design (decision 4: a
transition backed by a kernel act comes only from that act's door), and the act,
`World.retire`, is reachable only by a caller who holds a `World` opened under registry
authority, which a command never does. Science's milestone 1b retires an unrequired
predecessor publication after its successor's chain resolves, and it cannot do so.

Three facts in the code shape the door.

1. **A retry after a ledger failure is always another actor's.** A failed append leaves the
   session terminal (`SessionLedgerFailed` on every later call, writer-session design
   §3.2), so the only session that can re-ledger a retirement whose line was lost is a new
   one, whose actor is `session:<new id>`. `World._terminal` puts the actor in the
   candidate status record's digest (`status_digest` over `corpus_id`, `status`, `actor`),
   finds no record with that digest, finds the corpus's existing status, and refuses
   `StatusTerminal`. The different-actor retry the task asks about is therefore not an
   edge case: it is the only recovery path there is.
2. **A same-actor repeat is silent.** `World._terminal` returns the existing record when
   the candidate's digest matches one, so a second `World.retire` by the same session
   cannot be told from the first by its return value. A door that ledgered whatever the
   act returned would record a second retirement the act did not make.
3. **The registry records nothing about a publication but its corpus id.** An admission
   record holds the manifest, the provenance and the actor; a status record holds the
   corpus id, the status and the actor. The marker uid, the head artifact identity and
   the marker's `published_from` world and view exist only in the publication's root and
   in the carrier its arrival was verified against. A door that takes only a corpus id
   can bind only the corpus id.

## 2. Approaches

**A. The door takes the root and observers the admission door takes, and binds the
evidence exactly as it does (chosen).** `retire(root, observers, *, evidence)` runs the
existing `_bind_sharing_evidence(root, evidence, observers, subject=None)` before any
effect, so every pin fact the `retired` line carries except the two attestations
(`source`, `location`) is checked against the publication it names, with the same
refusals in the same order as `admitted`. Cost: retirement needs the publication's copy
and its head artifact on hand. Science keeps both for every adopted pin
(`SharingRegistry.root_for` and `head_artifact_for`, read by its `adopt` today), and its
1b design keeps a retired pin's copy, which supplies the links of longer chains.

**B. The door takes a corpus id and binds only that (rejected).** This is science's
assumed signature. The other five evidence facts would be attestation, as in
`record_sharing`. The sharing design's decision 4 rejected exactly this for act doors:
evidence naming publication B beside an act on publication A would ledger B's pin, and
science's `apply_line` creates a pin from the first line it folds for a corpus, so a
replay into an empty registry would rebuild a pin the act never touched. Retirement is
irreversible, which makes a wrong line worse here, not better.

**C. A corpus id, with the marker, world and view bound against the session's configured
carrier root (rejected).** This binds three facts without a root argument, but leaves
the artifact unbound (no configured root holds the carrier bytes), and it makes the door
depend on science mounting the corpus it retires. The reconcile path is exactly the case
where science's mounts and the kernel's registry disagree.

## 3. Decisions

1. **One door, `ScopedWriter.retire(root, observers, *, evidence) -> SharingLine`.** It
   retires `evidence.corpus` in the session's world under the scoped authority and ledgers
   one `retired` sharing line for the current invocation. The status record it writes
   carries the session actor, as the admission record `admit_publication` writes does
   (sharing design decision 6). *Rejected:* a `depart` door alongside. Science reports a
   `departed` status as a Finding and never departs a corpus itself (1b design §5.7
   step 1); a second door would be scope with no caller.

2. **The order, every step before any effect.** Each step refuses with the exception the
   existing doors already use for that condition:
   1. argument types, before the session lock: `_require_door_arguments(root, observers,
      evidence)` (`TypeError`);
   2. the session lock; liveness and currency (`SessionLedgerFailed`, `SessionClosed`,
      `SessionProtocolError`) before any read of the root;
   3. `self._authority.require("registry")` (`PermitExceeded`) — `World._terminal`'s own
      family, checked first so a writer scoped to less refuses here rather than after
      the binding;
   4. the session's world configuration (`SessionProtocolError`, as `admit_publication`);
   5. the evidence binding, `_bind_sharing_evidence(root, evidence, observers,
      subject=None)`: `SharingEvidenceDisagrees` on `corpus`, `artifact`, `marker`,
      `world`, `view` in that order, `PublicationReadingRefused("capture-damaged")`, or
      `PublicationArrivalRefused` from the layout check;
   6. the world, opened under the scoped authority (`open_world(config,
      authority=self._authority)`), and its registry read: no admission of
      `evidence.corpus` refuses `StatusTargetUnknown`; an admission whose provenance is
      not `ReplicaOf(evidence.corpus)` also refuses `StatusTargetUnknown`, naming the
      provenance it found;
   7. the corpus's terminal status: `departed` refuses `StatusTerminal`, naming
      `departed`;
   8. the act, or its absence (decision 3);
   9. the line; release.

   *My call, step 6's provenance check.* `admit_publication` admits a publication as
   `ReplicaOf` itself and no other sharing route admits anything, so a corpus admitted
   `Fresh` or `ForkOf` is not the sharing class's to retire, even when its root has the
   publication layout. The check uses the existing exception rather than a new one:
   to this door such a corpus names no known target. *Rejected:* letting it through.
   Retirement is irreversible, and a sharing invocation has no business ending a corpus
   it did not adopt.

3. **The door reads the status before acting, and the verdict says which happened.** At
   step 8, with the registry read at step 6:
   - no terminal status for the corpus: the door calls `World.retire(evidence.corpus)`
     and the line's verdict is `retired`;
   - a `retired` status by **any** actor, this session's included: the door makes no
     act and the line's verdict is `already-retired`;
   - `World.retire` raising `StatusTerminal` (another session in this process retired or
     departed the corpus between step 6's read and the act — two sessions over one world
     root share its per-process world lock, `_world_state_for`, but not a session lock):
     the door re-reads the registry; a `retired` status gives verdict `already-retired`,
     a `departed` status re-raises. Writers in other processes are outside this rule:
     the world lock is a `threading.Lock`, and deployment stays single-writer across
     processes (world-index slice 2 design, "Cross-process writers").

   The two verdicts are the evidence that tells a retirement from its recovery. Every
   other field of the two lines is identical, and `transition` is `retired` in both,
   because what the line records — this invocation established that the corpus has
   left the live span, and recorded it — is true of both. *Rejected:* refusing a
   different actor's status. Fact 1 makes that the only recovery path, so refusing it
   would leave a committed retirement permanently unledgered and science's pin
   `mounted` over a corpus the kernel no longer counts as live, which is the state
   science's reconcile exists to repair. *Rejected:* ledgering `retired` with the act's
   return value and no pre-read. Fact 2 makes a same-session repeat indistinguishable
   from the first retirement. *Rejected:* amending `World._terminal` to accept any
   actor's identical status. The registry's actor rule is the world-resolution cuts'
   and needs no change for this door; the door's read-then-act is the whole fix.

4. **The status record is evidenced by the line's `corpus`, with no new field.** A world
   holds at most one terminal status per corpus (`World._terminal` refuses a second under
   its world lock, and the single-writer deployment rule covers other processes), so
   `corpus` names the status record uniquely, and its actor and digest are one
   `World.registry()` read away. The `sharing` line keeps its eleven fields, `TRANSITIONS`
   is unchanged, and every ledger written before this door parses as before. Science's
   ledger-versus-registry comparison (sharing design decision 11) matches a `retired`
   line, of either verdict, against the corpus's `retired` status record. *Rejected:* a
   twelfth field carrying the status digest or its actor. It would version the line for
   a fact the registry already answers exactly.

5. **The session lock is held from step 2 through the line**, as `admit_publication`
   holds it, so no close or re-claim can fall between a committed status and its line.
   The lock order stays session, then the world lock inside `World.retire`; the
   binding reads the root through `load_manifest` and `ReadView.opened_at` and takes no
   lock, and nothing takes the world lock before the session lock.

6. **A ledger failure after the status commits is terminal and is recovered by the next
   session's call.** The `retired` append can fail at the write, the flush or the fsync
   after `World.retire` has made its status durable. The ledger's discipline applies
   unchanged: the call raises `SessionLedgerFailed`, the in-memory index does not learn
   the line, and the session is terminal. The registry keeps the status. The ledger file
   is not rolled back: `LedgerWriter` writes through an unbuffered handle before its
   flush and fsync and never truncates, so a short write leaves a torn tail
   (`LedgerReader.torn_tail`), while a flush or fsync failure leaves the complete
   `retired` line (verdict `retired`) readable on disk though never acknowledged. This
   design does not change that append contract. Any later session that calls the door
   with the same root, observers and evidence reaches decision 3's second branch and
   ledgers `already-retired` with no second status record, so the ledgers may then hold
   both the first session's `retired` line and the successor's `already-retired` line for
   one status record. Every reader must accept that: science's `apply_line` folds both to
   the pin's `retired` state idempotently, and its ledger-versus-registry comparison
   matches any number of `retired` lines, of either verdict, against the corpus's one
   `retired` status record. A crash at the
   same point leaves the same state and is recovered the same way. That later call is
   science's reconcile step (1b design §5.7, step 1), which calls the door for every
   `mounted` pin whose kernel status is known and not live and is `retired`.

7. **`record_sharing` keeps refusing `retired`.** Decision 4 of the sharing design makes
   an act-backed transition the door's alone, and that holds now that the act has a door.
   The refusal's message names `ScopedWriter.retire` instead of "World.retire's" door.
   *My call:* the sharing design's §8 reads "`record_sharing` admits `retired` only once
   that door exists", which could be read as admitting it after this change. Its
   decision 4 is the operative rule, and an attested `retired` line would be the one
   transition science could ledger without the kernel having retired anything.

8. **No conformance cut.** The door is a composition of a registry act whose behaviour
   is unchanged (`World._terminal`, under the world-resolution cuts) and the ledger's
   existing append path, which the sharing design's tests already fault at write, flush
   and fsync. It adds a recovery rule (decision 3) and a verdict vocabulary, and no
   persistence path. This is the sharing design's decision 13 reasoning, and it holds
   for the same reason. No frozen guarantee row changes, so nothing is superseded.
   AGENTS.md's two cut obligations bind only a cut. The permit inventories are a
   standing obligation (decision 9).

9. **The inventories stay closed.** The door calls `World.retire`, not a write primitive,
   so it joins neither `WRITE_ENTRY_POINTS` (`test_permit_boundary.py`) nor
   `test_permit_entry_points.py`'s `CASES`. `World._terminal` already has its `Case`, as
   `admit_publication` relies on the arrival's. The door does not import `atoms`, and
   `root.py` stays the one importer. The builder confirms the inventories pass unchanged
   and amends them only if a test proves the door is in scope.

## 4. The API

```python
# beliefs/session/writer.py
class ScopedWriter:
    def retire(self, root: Path, observers: ObserverSet, *, evidence: SharingEvidence) -> SharingLine: ...
```

Its verdict is `retired` or `already-retired`, and its transition is always `retired`.
The `SharingLine` it returns is the one appended. There are no new errors, and no new
ledger fields or line kinds. The `ScopedWriter` class docstring's inventory gains the
door.

## 5. Testing

The tests go in `tests/test_session_sharing_doors.py` beside the admission door's, over
the same `certified_work` fixtures, run through `just test-one`.

- **Retirement.** An admitted publication is retired through the door: the line's
  fields equal the evidence, with verdict `retired` and transition `retired`;
  `World.status` reports it known and not live; the registry holds exactly one status
  record for it, whose actor is the session's; `invocation_sharing` holds the line.
- **Ordering and no-effect refusals**, each asserting that the registry's status records
  are unchanged by the call (none in every case but the departed one, which keeps its
  `departed` record and gains no `retired` record) and that the ledger gains no
  `sharing` line: a stale or closed writer refuses before the
  root is read (proved with `refuse_any_read`, which patches `_bind_sharing_evidence` to
  raise, as `test_stale_and_closed_writers_refuse_before_reading_the_copy` does); a writer scoped without `registry` refuses `PermitExceeded` before the binding;
  a session with no world configuration refuses `SessionProtocolError`; each evidence
  field disagreeing refuses naming that field (parametrized as the existing doors'
  test is); a corpus not admitted refuses `StatusTargetUnknown`; a publication root
  admitted `Fresh` through `World.admit` refuses `StatusTargetUnknown`; a departed corpus
  refuses `StatusTerminal`.
- **Repeat in one session.** A second call in a later invocation of the same session
  ledgers `already-retired`, and the registry still holds one status record.
- **Recovery after a ledger failure**, one case each for a fault at the write, the
  flush and the fsync of the `retired` append, parametrized and faulted as
  `test_session_writer.py`'s
  `test_a_failed_sharing_append_leaves_the_index_unchanged_and_ends_the_session` faults
  `session._ledger._file`, with one difference: `World.retire` runs inside the call,
  so each fault is armed for the ledger's file alone (a `write` or `flush` patched on
  the handle, and `os.fsync` patched to fail only for the ledger file's descriptor),
  never globally. In every case the call raises `SessionLedgerFailed`, the in-memory
  index holds no `retired` line (`session._index[...].sharing` is unchanged), every
  later session method raises `SessionLedgerFailed`, and the registry holds the status
  under the first session's actor. The first session's ledger file then differs by
  fault, and the test asserts each: after the short write, `open_ledger_reader` reports
  `torn_tail` and no complete `retired` line; after the flush or fsync fault, the file
  holds the complete `retired` line with verdict `retired`, which the reader returns. A
  second session over the same world then calls the door with the same arguments: it
  ledgers `already-retired`, the registry still holds one status record whose actor is
  the first session's, and `read_ledger_evidence` over the second session's ledger
  returns the line. In the flush and fsync cases both ledgers' lines read back together,
  one `retired` and one `already-retired` for the one status record.
- **The race branch.** `World.retire` is patched to write another actor's `retired`
  status and then run the original, which raises `StatusTerminal`: the door ledgers
  `already-retired`. The same patch writing `departed` instead re-raises
  `StatusTerminal` and appends nothing.
- **`record_sharing`** still refuses `retired` with `ValueError`, and its message names
  the door.
- **Lock order.** A close attempted from another thread while the door is inside
  `World.retire` (the only lock the door takes below the session lock is the world
  lock there) waits on the session lock and completes after the line, traced with
  `TracingLock` as `test_session_routes.py`'s
  `test_close_waits_while_append_intent_holds_the_session_lock` traces the intent
  append. No existing sharing-door test holds this for `admitted`; this one is new.
- **Inventories.** `test_permit_boundary.py`, `test_permit_entry_points.py` and
  `test_capability_boundary.py` pass unchanged.

## 6. What changes elsewhere

**Delivery** (my call). This design's branch carries the design, the brief's record of
its decision and the wake note, and nothing that says the door exists. The door is
built by beliefs-a989fb in its own lane and worktree once this design merges: that task
is scoped `direct` against this design, so no further plan document is needed unless its
scoping finds a design gap. Every claim that the door exists lands with the code, in
the change that makes the old claim stale:

- **The sharing design** gets a dated amendment section naming this door against
  decision 4's last sentence and §8's second bullet. Its body is unchanged.
- **The adoption ledger** gets one line under the session work naming this door and
  design.
- **The guide's open questions** (`docs/guide/open-questions.md`, "Retiring a
  superseded publication at the recipient") drop the entry, or narrow it to science's
  policy, since the kernel's operation then exists.

This design's branch carries the rest:

- **The brief** records this design's decision and the implementation handoff, as the
  task requires.
- **beliefs-a989fb** is woken before this branch merges with
  `tasks note beliefs-a989fb --no-reviewed "<finding>"`. The finding names the signature,
  the two verdicts and the recovery rule, and leaves the idea ready to scope as a
  `direct` implementation task against this design.
**Science** changes in its own repository, by its own change, not on this branch. Task
13's Interfaces change as follows, and the plan's constraints already require revising
them against this design before the task starts:

  - The door takes `(root, observers, *, evidence)`. `adopt` passes `root_for(cid)`
    and the observer set it builds from `head_artifact_for(cid)`, as it does for
    admission.
  - Idempotency holds across actors. Science's reconcile needs no Finding path for a
    different actor's status, though it keeps one for a refusal.
  - A `departed` corpus refuses `StatusTerminal`, which science already filters out
    before calling.
  - The verdict is `retired` or `already-retired`. `apply_line` folds both to the pin's
    `retired` state and reads neither.

## 7. Left to the builder

- Whether the pre-read at step 6 reuses the `World.registry()` result for step 7, or
  calls `World.status` as well. Either is correct: the race branch covers the window
  between the read and the act, whichever read is used.
- The exact refusal messages, which name the corpus and, for step 6's provenance
  refusal, the provenance found.
- Whether `retire` shares a private helper with `admit_publication` for steps 2–5. The
  two doors run the same steps in the same order.
