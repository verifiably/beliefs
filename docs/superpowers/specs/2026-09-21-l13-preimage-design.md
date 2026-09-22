# L13 preimage resolver — digest-matched classification of a removed verification

**Date:** 2026-09-21
**Status:** draft, for review before the cut freezes
**Boundary:** `l13-preimage` (`beliefs-a7df71`), tier 1 off the path, row 1 after cut 36
**Lane:** `cross-repo`, worktree `.worktrees/l13-preimage`
**Sources:** `../../designs/2026-08-03-tamper-evident-log-design.md` (§2 ruling 4, §8, §9, L13),
`../../designs/2026-08-22-log-verification-design.md` (§5.3 and its R16 amendment, §6.1, §6.2, §6.4, §10 item 4),
`../../designs/2026-08-22-conformance-cut-8.md` (§3.1's L13 disposition, five units),
`../../designs/2026-08-27-conformance-cut-11.md` (label 1: `history` as L13's caller-held input),
`../../designs/2026-09-13-conformance-cut-27.md` (§3's relabel shape),
`../../designs/2026-08-03-redesign-adoption-ledger.md` (`l13-preimage` row; row 5),
`../../plans/2026-08-29-implementation-roadmap.md` (tier 1 off the path row 1, `cross-repo` lane, concurrency rules),
`atoms` `docs/plans/2026-09-11-public-preimage-read-design.md` (`read_preimage`, its §1.1 consumer check, §5, §7)
**Measured against:** `main` at `e9e3457`

## 1. What this slice is

The baseline below describes `main` at `e9e3457` before implementation.

L13 says that a log-visible removal of a verification is in the timeline
**and** draws a policy finding naming the deleted record, and that the
finding classifies the removal as a *failing* verification's **only where
the historical content resolves — a held copy or surviving preimage
bytes** — because entries retain state digests, not verdicts. Cut 8 read it
in five units and left it partial for two reasons the log-verification
design states side by side (§5.3, amended 2026-08-23 by R16):

1. **The resolver deferral.** Classification resolves only through the
   caller's `history: Mapping[content-hash, bytes]`; the surviving-preimage
   arm waited on a named `atoms` seam.
2. **The weakened match.** Even with a copy held, the match is by the
   corpus path the copy's own identity claims, not by the removed state's
   digest, because "`LogSeam` exposes no state→digest accessor". A single
   held copy of another version of the same record can misclassify a
   removal in either direction, so every finding message speaks about the
   held copy and never about the removed bytes.

Both reasons have since been overtaken by landed work, which is why this
slice needs no engine change:

- **The seam landed** on 2026-09-11 (`atoms-38887b`): `read_preimage(backend,
  project_root, metadata_root, storage, txid, path, *, max_bytes) -> bytes`
  returns the owned, twice-verified bytes of one regular-file initial state
  of a settled transaction, selected by transaction id and registered path,
  on a **writable** root through the existing recovery lease; every other
  lifecycle state refuses `PreconditionRefused` before the writable suffix,
  corruption raises `MetadataStoreInvalid`, and a chain/record contradiction
  raises `ChainStateInvalid`. Its §1.1 established that no engine-produced
  replica carries local transaction records or preimage blobs, and that
  nothing leaves the writable state, so the surviving-bytes arm is served on
  the writable source root and nowhere else.
- **The accessor landed** with the intent-boundary slice: `LogSeam.state_facts`
  (`root._state_facts`, the engine's `state_to_json`) renders an opaque path
  state as its closed fact vocabulary — for a file, `content_hash` (64 hex),
  `mode` and `byte_len`. A removal's declared pre-state therefore *does*
  yield the digest R16 could not reach, and the digest match is
  implementable today in the policy pass, independently of the seam.

Two facts measured on the tree bound the arms this slice can construct
(both checked on 2026-09-21 against the certified volume with a throwaway
script, not kept):

- On a writable root, `read_preimage` for a committed removal returns the
  removed bytes, and `state_facts` on the removed entry's declared pre-state
  yields the same `content_hash`.
- A raw copy of a registered root **cannot** be registered writable
  (`register_root` refuses: "matching genesis has no local initialization
  operation"), and `replicate_root` yields `read-only-unserviceable`. No
  engine-produced root is ever *writable with unretained history*, and no
  `atoms` command collects blobs or transaction records (its ledger #28).
  So the row's "preimage GC'd and no copy held" arm is constructible on
  exactly the roots the engine retains no history for — the non-writable
  ones — and this slice declares it at that width rather than arguing it
  full.

This slice builds the **digest match** for both channels, the
**surviving-preimage arm** through one new seam callable reached only by
the audit, the **absence finding** that states why nothing resolved, and
the refusal envelope for corrupt local history. It closes L13 in full and
builds no consumer.

## 2. Decisions

1. **The removed state's digest is the key, and both channels resolve by
   it.** For every committed removal the policy pass renders the declared
   pre-state through `state_facts`; a `file` state yields
   `sha256:<content_hash>`. A held copy resolves iff `history` carries that
   exact key — the key *is* the digest, and `validate_history` has already
   proved the bytes hash to it. A preimage read resolves iff the engine's
   bytes re-hash to it. Path is consulted by neither channel. A copy of
   another version claiming the removed path resolves nothing, which
   reverses R16's second partiality: every classification now speaks about
   **the removed bytes**, and the finding messages say so.
2. **The source root is the audited root and nothing else.** `_audit_log`'s
   target root is explicit and never associated by manifest (§6.1); the
   preimage read is made against that root, under the same hold as the
   inspection that declared the removal. No search for "the world's writable
   root for this corpus" is made: it would associate by id, take a second
   corpus lock under the first, and answer a question the held-copy channel
   already answers — a replica's removal is classified by auditing the
   source root, whose chain is the same chain, or by passing the bytes as
   `history`. No Science-side operator helper to fetch preimages for
   `history` is built: it has no consumer.
3. **The preimage arm is the audit's; arrival and restore consult none.**
   `_admit_arrival` refuses a writable root before it inspects anything
   (§6.2), so every read it could make would be refused by construction;
   the restore core evaluates a root that is not writable by definition.
   Both evaluate with `preimages` empty and their absence finding says
   `preimage=not-consulted`. In the audit the reads happen **inside the
   hold, after the inspection and both captures**, one per committed
   removal the inspected view declares, and the evaluator stays pure over
   values.
4. **Beliefs holds no lifecycle model of its own for this.** The audit does
   not gate the read on `seam.lifecycle_state`; it asks the engine, and the
   engine's `PreconditionRefused` — a non-writable root, a non-file
   pre-state, history not retained — is the reason the absence finding
   records. A second rule here ("only writable roots retain preimages")
   would silently outlive any later engine change.
5. **The request is derived from the chain, never from the caller.**
   `txid` and `path` are the removing registration's; `max_bytes` is the
   declared pre-state's `byte_len`, so the budget is exactly the chain's own
   claim and an over-budget refusal is impossible for a consistent root. A
   pre-state that is not a `file` (a symlink removed at a record path)
   yields no digest, is not read, and the absence finding says
   `digest=none`.
6. **Corruption refuses the act; unavailability is a finding.**
   `MetadataStoreInvalid`, `ChainStateInvalid` and `TransactionHalted` from
   the read become `LogEvidenceRefused("preimage", …)`: no report, exactly
   as a corrupt `history` refuses under `validate_history` and as the
   inspect and capture phases refuse under §6.4. The Beliefs-side re-hash
   of returned bytes against the declared digest disagreeing is
   `PreimageMismatch`, a refusal in its own right: two evidence sources
   the act reads under one hold contradict each other. `PreconditionRefused`
   is the one engine refusal that is *evidence about availability* rather
   than about integrity, and it produces the absence finding with the
   engine's words.
7. **Absence is stated, not silent.** A committed removal nothing resolves
   draws `removal-unclassified` beside `record-removed`, naming the digest
   the resolution would have needed and whether the preimage was consulted
   and what the engine said. The finding itself states that no held copy
   under that digest was supplied — a copy under it would have classified —
   and copies supplied under other digests are not counted: they support no
   removal, and counting them would mislead a reader about which one they
   support. Cut 8's L13u3 read "honestly absent" as *no classification
   finding*; this slice reads it as *a finding that says the classification
   is absent and why*, so an operator can tell a root that retains no
   history from a caller who held no copy. `record-removed` itself is
   unchanged.
8. **Precedence between the two channels is nominal.** Two byte strings
   with one SHA-256 are one byte string, so the channels cannot disagree; the
   preimage is named as `source` when it resolved and the held copy
   otherwise. A held copy is still validated at entry and a preimage is
   still re-hashed, so the finding's digest is always one the act checked.
9. **The seam callable is the composition root's, and the evaluator never
   sees an engine type.** `LogSeam` gains `read_preimage`, wired in
   `root.py` — the one `atoms` importer — with an unwired default that
   raises, as `state_facts` and `lifecycle_state` have. `replay` gains
   `state_facts` as a **required** parameter (a replay that could not render
   the digest would silently regress to no classification) and `preimages`
   as the audit's evidence. `read_preimage` is a read, so `WRITE_ENTRY_POINTS`
   and `CASES` are unchanged (AGENTS.md, Cut plans).
10. **L13 closes in full; row 5 stays partial for L1's persistence arms
    only.** Cut 37 selects its own units for every clause the digest match
    or the preimage arm touches and cites cut 8's frozen evidence for the
    two it does not (retirement appends and deletes nothing; preimage-blob
    GC appears in no chain — a taxonomy fact over the closed entry-class
    union, at the width cut 8 declared). `l13-preimage` leaves the ledger's
    `Current state` table and the roadmap's boundary index in the results
    commit; the `cross-repo` lane keeps `persistence-cut`.

## 3. The evidence model — `world/verify.py`

### 3.1 Committed removals

```python
@dataclass(frozen=True, slots=True)
class Removal:
    txid: str
    path: str
    state: object          # the declared pre-state, opaque

def committed_removals(view: WellFormedView, absent_state: object) -> tuple[Removal, ...]
```

In chain order over committed registrations only (the settlement naming
the registration is committed), a removal is a `final` pair whose state is
`absent_state` and whose **declared** `initial` state for that path is not —
the transition's own claim about itself, read exactly as today's policy
pass reads it, never the accumulated surface. `replay`'s policy pass
iterates this function's result rather than recomputing the predicate, so
the audit and the evaluator name one set of removals.

### 3.2 The removed digest

```python
def removed_digest(state: object, state_facts: StateFacts) -> str | None
```

`state_facts(state)` rendered to a mapping; `kind == "file"` yields
`f"sha256:{content_hash}"`, any other kind `None`. `byte_len` is read
beside it for the request budget (decision 5). This is the only place the
policy pass touches a state's facts, and it touches them through the
seam's codec — no second summary model.

### 3.3 Preimage evidence

```python
@dataclass(frozen=True, slots=True)
class PreimageRead:
    payload: bytes

@dataclass(frozen=True, slots=True)
class PreimageUnavailable:
    reason: str            # the engine's PreconditionRefused text

PreimageEvidence: TypeAlias = PreimageRead | PreimageUnavailable
Preimages: TypeAlias = Mapping[tuple[str, str], PreimageEvidence]   # (txid, path)
```

`replay(view, disk, absent_state, history, *, state_facts, preimages)`
validates `history` as today and, for each removal, resolves in this
order:

1. `digest = removed_digest(removal.state, state_facts)`; `None` →
   unclassified, `digest=none`.
2. `preimages.get((txid, path))`: a `PreimageRead` whose payload hashes to
   `digest` → resolved, `source=preimage`; one that does not →
   `PreimageMismatch` (decision 6); a `PreimageUnavailable` → the reason is
   carried to step 4; absent → `not-consulted`.
3. `history.get(digest)` → resolved, `source=held-copy`.
4. Nothing resolved → `removal-unclassified`.

The pass decodes resolved bytes as today (`node_from_markdown`, the
verification facet's verdict where the kind is `verification`), and
`_HeldRecord`/`_held_records`' path index is deleted with the path match.

### 3.4 Findings

Every committed removal draws `record-removed` exactly as today
(`warning`, `ref=path`, `detail="txid=<txid>"`). It then draws exactly one
of the following, `ref=path` in every case:

| code | severity | detail | when |
|---|---|---|---|
| `failing-verification-removed` | `error` | `txid=<t> digest=<d> source=<preimage\|held-copy>` | the removed bytes decode as a verification carrying verdict `failed` |
| `removal-classified` | `warning` | `txid=<t> digest=<d> source=<s> kind=<k> verdict=<v>` | a verification carrying another verdict |
| `removal-classified` | `warning` | `… kind=verification verdict=unreadable` | a verification whose facet does not validate |
| `removal-classified` | `warning` | `… kind=<k>` | a record of another kind |
| `removal-classified` | `warning` | `… kind=none` | bytes that are not a Science record (`NodesError`, `ValueError`, `YAMLError` at decode) |
| `removal-unclassified` | `warning` | `txid=<t> digest=<d\|none> preimage=<refused\|not-consulted>` | nothing resolved: no preimage bytes and no held copy under `<d>` |

Messages speak about **the removed bytes** ("the removed record's bytes,
resolved by digest, …"); the phrase "a held copy filed under this digest
claims the removed path" leaves the module. The `removal-unclassified`
message carries the engine's reason verbatim when `preimage=refused`, so
the detail grammar stays `key=value` tokens and the free text stays in the
message, which is normative for nothing. `preimage=resolved` never
appears on an unclassified removal — a resolved read classifies — and the
detail carries no `held=` token: the finding's existence is the statement
that `history` held nothing under the removed digest, and copies under
other digests are unrelated evidence (decision 7).

## 4. The seam — `LogSeam.read_preimage` and `root.py`

```python
read_preimage: Callable[[Path, str, str, int], PreimageEvidence] = _unwired_read_preimage
```

`(root, txid, path, max_bytes)`. The composition root wires it to the
engine:

```python
def _read_preimage(root: Path, txid: str, path: str, max_bytes: int) -> PreimageEvidence:
    try:
        payload = read_preimage(_PRODUCTION_BACKEND, str(root), str(metadata_root_for(root)),
                                PRODUCTION_STORAGE, txid, path, max_bytes=max_bytes)
    except PreconditionRefused as caught:
        return PreimageUnavailable(str(caught))
    except MetadataStoreInvalid as caught:
        raise LogEvidenceRefused("preimage", "MetadataStoreInvalid", str(caught)) from caught
    except ChainStateInvalid as caught:
        raise LogEvidenceRefused("preimage", "ChainStateInvalid", str(caught)) from caught
    except TransactionHalted as caught:
        raise LogEvidenceRefused("preimage", "TransactionHalted", str(caught)) from caught
    return PreimageRead(payload)
```

Exactly these four are caught; `ProtocolError` and setup errors keep their
own contracts, as `_inspect_escapes` rules. The engine's own argument
grammar cannot refuse here — `txid` and `path` come off a validated chain
entry — and if it ever did, the `PreconditionRefused` reads as an
unavailability with the engine's words, visible in the finding.

The lease the engine takes is the project lock the audit's registered
inspection already took and released under the same Science operation
lock; recovery has already run, so lease entry recovers nothing. On a
non-writable root the engine refuses before the writable suffix and
touches no metadata.

## 5. The audit — `_audit_log`

Inside `_subject_hold`, after `_assemble_evaluation_inputs` returns the
view, the disk surface, the records and the presented identity:

```python
preimages = _read_preimages(seam, root, view) if type(view) is WellFormedView else {}
```

`_read_preimages` iterates `committed_removals(view, seam.absent_state)`,
computes each removal's digest and `byte_len` through `seam.state_facts`,
skips a removal with no digest, and calls `seam.read_preimage(root, txid,
path, byte_len)` for the rest, in chain order, collecting
`{(txid, path): evidence}`. A `LogEvidenceRefused` propagates untranslated:
the act refused to judge (§6.4). Evaluation runs outside the hold as
today, with `preimages` passed through `evaluate_log` to `replay`.

A malformed or absent view reads no preimage: the evaluator stops at step
1 or step 2 and replay is not reached. A pending chain (step 3) also never
reaches replay; the reads are made anyway because the pending set is a
fact of the view the act has not yet judged, and reading a settled
transaction's history on a root with an unrelated pending registration is
admitted by the engine ("unrelated pending registrations do not impose a
new whole-chain write gate", atoms §5). This keeps the hold's contents a
function of the view alone.

`_admit_arrival` and the restore core pass no `preimages`. Their
signatures, holds, orders and refusals are unchanged.

## 6. Errors — `errors.py`

- `LogEvidenceRefused` widens its two literals: `phase` gains `"preimage"`,
  `engine_error` gains `"MetadataStoreInvalid"`. Its docstring's "three
  engine states" becomes four phases' worth, stated per phase; the
  refusal-not-judgment contract is unchanged.
- `PreimageMismatch(ScienceError)` — the bytes the engine returned for
  `(txid, path)` do not hash to the digest the inspected chain declares for
  that removal. Raised by `replay`, before any finding for that removal is
  produced; a refusal to judge, never an outcome and never an arrival
  cause.

## 7. What does not change

- `history`'s shape, its key form, `validate_history`, and its refusal at
  entry of the evaluator and of both boundaries (cut 11 label 1; D9).
- `record-removed`: code, severity, ref, detail and message.
- `evaluate_log`'s four steps and their precedence; `replay`'s divergence
  rule and head comparison; `_arrival_cause`.
- `_admit_arrival`'s and the restore core's contracts.
- The engine: no `atoms` change, and no read-only preimage arm (limitation
  1).
- Both `CONTRACT.yaml` copies and their identities. No TypeScript changes.
- `science.belief.v1`'s answers over every fixture; P1–P9.
- The reproduction: cut 37 reads the mm30 corpus in place and re-derives
  the same answer; the corpus removes nothing, so no removal finding is
  drawn and the preimage arm is exercised only by the acceptance module.

## 8. Shared files, under roadmap concurrency rule 3

`errors.py`, `python/tests/test_designs_corpus.py`, the ledger, the roadmap
and the guide index are rewritten by every lane. This slice also rewrites
`world/verify.py` and `root.py`, both in the `world-read` lane's column,
and `test_world_log_replay.py`, `test_world_log_audit.py` and
`tests/cited_not_run.py`. No other lane is open; if `act-report-remainder`
(`beliefs-86b150`, the `world-read` head) opens beside this one, its
design names `world/verify.py` and `root.py` and the later merge resolves
toward the earlier.

## 9. Testing and the cut

### 9.1 Unit — `test_world_log_replay.py`, `test_world_log_audit.py`

`test_world_log_replay.py`, over the fabricated `removed_record` chain and
the production `state_facts`:

- `committed_removals`: one removal per committed absent-final; a
  rolled-back removal and a pending one are none; a replacement is none;
  chain order.
- `removed_digest`: a file state → `sha256:<hex>` equal to the state's
  `content_hash`; a symlink or directory state → `None`, and a removal
  with such a pre-state draws `removal-unclassified digest=none` with no
  read attempted (§9.2 case 5's unit-level arm).
- the held copy resolves by digest: the copy of the removed bytes →
  `failing-verification-removed` with `source=held-copy` and the removed
  digest; a copy of **another version** of the same record (same id, other
  verdict) → `removal-unclassified`, the other-version copy named
  nowhere; two copies, one
  matching → classified from the matching one alone (the R16 reversal, in
  both directions).
- the preimage resolves: `PreimageRead` of the removed bytes →
  `source=preimage`; `PreimageRead` of other bytes → `PreimageMismatch`
  before any finding; `PreimageUnavailable` → `preimage=refused` and the
  reason in the message; the pair absent → `preimage=not-consulted`.
- both present → one classification, `source=preimage`.
- the classification table (§3.4): failed, passed, unreadable facet,
  another kind, not a record — each from a preimage and from a held copy.
- `record-removed` unchanged: code, severity, detail, message.
- the existing cut-8 checks (`L13u1`–`L13u3`, `D9`) rewritten to the new
  contract and kept under their names, since `n2_arms_cut8.py` names them
  and is cited-not-run (§9.5).

`test_world_log_audit.py` gains a class for the audit over injected seams
(the existing `Inspections`/`Captures` doubles plus a recording
`read_preimage`):

- the read is made for every committed removal, in chain order, with the
  chain's `txid`, `path` and `byte_len`, **inside the hold** (the existing
  lock-probe pattern) and after the captures;
- no read for a malformed or absent view; reads for a pending view; no read
  for a removal whose pre-state is not a file;
- `LogEvidenceRefused("preimage", …)` propagates untranslated and no
  report is produced;
- arrival and restore make no read (the recording seam sees none);
- the composition-root wrapper's exception mapping (§4): each of the four
  engine exceptions injected in place of `read_preimage`, and
  `ProtocolError` passing through.

### 9.2 Acceptance — `test_l13_preimage_acceptance.py` (new)

Real roots on the certified volume, through `root` only:
`init_corpus_root`, `open_corpus`, a failing verification added and then
removed with `CorpusWriter.delete`, the audit anchored at the root's own
tip as `test_deletion_acceptance.py`'s `_audit_log` does. Cases:

1. **The surviving preimage.** Audit the writable root with no `history` →
   `validated`, findings `record-removed` then
   `failing-verification-removed` at `error`, `source=preimage`, the
   digest equal to `sha256` of the record's rendered bytes before removal.
2. **Digest, not path.** `history` holds a hand-rendered copy of the
   **same record** — same id, so the same claimed path — with verdict
   `passed`, never stored. On the writable root the removal classifies
   from the preimage (`source=preimage`, `verdict=failed`) and the copy is
   not named; on the restored copy (case 3's) the same `history` yields
   `removal-unclassified` naming the removed digest only — a copy of
   another version of the record resolves nothing and is named nowhere, in
   the direction R16 said it could misclassify.
3. **No local history.** `replicate_root` then `restore_root` the source
   after case 1 (`read-only-serviceable`; registered inspection), and admit
   a raw copy through `admit_arrival` (detached): the audit of the restored
   copy → `record-removed` and `removal-unclassified preimage=refused`,
   the message carrying the engine's lifecycle refusal; the
   arrival's report → `preimage=not-consulted`. With `history` holding the
   removed bytes, both classify `source=held-copy`.
4. **Corrupt local history.** On a writable root after a removal, unlink
   the indexed preimage leaf under the metadata root (`blobs/sha256/<hex>`);
   the audit → `LogEvidenceRefused` with `phase == "preimage"` and
   `engine_error == "MetadataStoreInvalid"`, no report; the root's project
   files are untouched. A *truncated* leaf is not this case: the registered
   inspection's own store checks find it first and raise the engine's raw
   `MetadataStoreInvalid` before any read (plan review, 2026-09-21), so only
   the missing leaf reaches the reader's translation.
5. **Not a verification.** Delete a record of another kind `delete`
   admits (cut 18's fixtures delete assessments and producers) →
   `removal-classified kind=<kind>` at `warning`, `source=preimage`. The
   `digest=none` arm (a symlink pre-state) has no engine production
   through the corpus writer and is declared at the unit level over a
   fabricated view (§9.1), with the declaration stating that width.
6. **The write inventory is closed.** `read_preimage` appears in no
   `WRITE_ENTRY_POINTS` row and the audit still calls no write primitive
   (the permit-boundary tests unchanged and green).
7. **Relabels.** Retirement appends a status event and deletes nothing;
   preimage-blob GC appears in no chain — each one check citing cut 8's
   L13u4 and L13u5 by unit and re-running that unit's live check under cut
   37's own guard (cut 27's shape).

Every classified finding asserts `ref`, `severity`, the full `detail`
token set and that its message names the removed bytes, never a held
copy.

### 9.3 N2 sabotages — `n2_arms_cut37.py`

One sabotage per declaration unit, each named to a real source site with a
`before` occurring exactly once in its module:

- `removed_digest` returns the path instead of the digest (the path match
  returns);
- `replay` resolves a held copy by the path its identity claims when no
  digest matches (R16's fallback);
- `replay` accepts a `PreimageRead` without re-hashing (the mismatch
  becomes a classification);
- `replay` maps `PreimageUnavailable` to a classification from any held
  copy (absence stops being honest);
- `replay` drops `removal-unclassified` (absence goes silent);
- `_read_preimages` skips the read for a removal whose settlement is
  pending-adjacent, or reads outside the hold (the lock probe catches it);
- `_read_preimages` passes `max_bytes=0`;
- `root._read_preimage` maps `MetadataStoreInvalid` to
  `PreimageUnavailable` (corruption downgraded to absence);
- `root._read_preimage` maps `PreconditionRefused` to `LogEvidenceRefused`
  (absence upgraded to a refusal);
- `committed_removals` counts a rolled-back removal;
- `_admit_arrival` passes preimages (the recording seam sees a read);
- an L13u4 and an L13u5 sabotage each re-run one prior clause's site (the
  relabels' live guard).

The staleness gate is `test_arm_staleness.py`'s: zero stale live arms
after any `_LIVE_SABOTAGES` re-targeting. Cited-not-run guards keep their
historical staleness recorded in `cited_not_run.py`, never repaired.

### 9.4 The cut

Conformance cut 37, `docs/designs/2026-09-21-conformance-cut-37.md`, frozen
before implementation after this spec's review. Rows: **L13** in full —
cut 8's L13u1–L13u3 **superseded** by cut 37's own units (the removal
finding re-read, the classification re-read under the digest match, the
absence re-read as the stated finding), its L13u4 and L13u5 **cited** to
its standing record and relabelled (decision 10), never re-run, since
`test_n2_cut8.py` is cited-not-run by ruling R15. Runner
`cut37_acceptance.py` chains **cut 36's** runner in `PREFIX_RUNNERS` — the
live certified chain continues, never re-roots — with phase modules
`test_l13_preimage_acceptance.py` and `test_n2_cut37.py`.
`test_recent_cut_acceptance.py` gains the cut-37 row with its accounting
triple and guarantee-rows-exercised line (AGENTS.md, Cut plans).

### 9.5 Frozen evidence and live tests

Every frozen declaration stays byte-exact. `n2_arms_cut8.py`'s
`_NO_CLASSIFICATION` and `_CLASSIFIES_ANY_COPY` pin `resolved =
held.get(path)`, which this slice deletes; both arms go stale and, because
cut 8 is cited-not-run, that staleness is **recorded** in
`cited_not_run.py`'s `stale_arms` with the moving commit — never
re-targeted, never repaired. `_NO_REMOVAL_FINDING` pins the
`findings.extend(_removal_findings(...))` line; if the refactor moves it,
the same rule applies. No live guard (cuts 17–36) sabotages
`world/verify.py`'s policy pass; after the implementation task, run
`cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py -q`
and record or re-target whatever moved. The cut-18 durable check
`test_g8_c6_raw_removal_refutes_and_managed_delete_validates` asserts the
managed arm's codes `["record-removed", "failing-verification-removed"]`
and severities; under this slice the writable root resolves the preimage
first and the held copy second, so the assertion holds unchanged.

## 10. Documentation amendments

- The log-verification design §5.3 gains a dated note beneath its R16
  amendment: the digest match built through `state_facts`, the
  surviving-preimage arm built through `read_preimage`, both partialities
  closed at cut 37; §10 item 4 closes.
- The log design's L13 row gains a closure marker naming cut 37 and the
  width statement of §1 (absence constructible on non-writable roots; no
  collector exists).
- The ledger's `Current state` table drops `l13-preimage`; row 5's
  remainder becomes L1's persistence arms alone (`persistence-cut`); the
  roadmap re-ranks at cut 37 (off-path row 1 discharged, every later row
  renumbers up; the `cross-repo` lane keeps `persistence-cut`; Appendix A
  and B rows for L13); the guide's contracts-and-adoption page and
  `README.md` state the count (187 of 216 closed, 29 open).
- The atoms design's §1.1 sentence "Beliefs' L13 task remains open until
  its consumer behavior is implemented and verified" is answered by a
  note on `atoms-38887b` (a `tasks note`, no `atoms` document edit).

## 11. Task linkage

- `beliefs-a7df71` is this slice's task; this spec attaches with
  `tasks edit --spec`.
- Plan steps become children of `beliefs-a7df71` with `--plan` and
  `--step`, each `--complexity` and `--process direct`.
- `beliefs-86b150` (`act-report-remainder`) gains a note naming the
  shared-surface overlap on `world/verify.py` and `root.py` (§8).

## 12. Limitations and open questions this slice files

1. **No read-only preimage arm.** A replica or restored copy retains no
   local transaction records or blobs by engine construction, and the
   `atoms` design (§1.1) declines a read-only historical-store API. The
   held-copy channel is the route for such roots; the audit of the writable
   source root is the other. Stated in the results record; not an open
   question, since nothing in the row needs it.
2. **No collector, so no GC arm.** "Preimage GC'd" has no engine
   production; the row's absence arm is read on non-writable roots. When
   `atoms` adds a collector (its ledger #28 gates it on the settlement
   binding), the writable-root absence case becomes constructible and is
   read by that change's own cut.
3. **No consumer.** Comp §3.3's contradiction findings and the corpus
   read do not consult the classification; `failing-verification-removed`
   remains a log-audit finding. A consumer is the owning lane's, when a
   boundary needs it.

## 13. Review log

- **2026-09-21, spec review (one P2, taken):** `held=present` was defined
  three ways — a copy under another digest (§3.4), absent for another
  version of the record (§9.1), present for the same case (§9.2). Presence
  is now defined by the exact removed digest, which makes the token
  unreachable on an unclassified removal, so it is dropped: the finding
  states that nothing was held under the removed digest, and unrelated
  copies are not counted (decision 7, §3.4, §9.1, §9.2 cases 2–3). Digest
  matching, the `atoms` exception mapping and the frozen-evidence handling
  were confirmed against the code.
- **2026-09-21, plan review (one correction to §9.2):** case 4 unlinks the
  leaf rather than truncating it — the registered inspection raises raw
  `MetadataStoreInvalid` over a truncated leaf before the reader runs
  (reproduced on the certified volume by the reviewer).
