# Conformance cut 37 — the L13 preimage resolver

**Status:** frozen 2026-09-21, before implementation; L13 is open
**Design:** `../superpowers/specs/2026-09-21-l13-preimage-design.md`, approved for implementation planning 2026-09-21 at `c3565d4` after one review; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-21-l13-preimage.md`.
**Numbered after** cut 36 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 37–39 at freeze; cut 36 is the highest discharged runner.

## 1. What this cut is

Cut 8 read L13 in five units and left it partial for the resolver deferral
and R16's weakened path match. Both were overtaken by landed work:
`state_facts` yields the removed digest and `atoms-38887b` delivered
`read_preimage`. This cut builds the digest match for both channels, the
surviving-preimage arm through one seam callable reached only by the audit,
the stated absence finding and the corruption refusal. L13 closes in full;
row 5 stays partial for L1's persistence arms under `persistence-cut`.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/world/verify.py`, `root.py`, `errors.py`;
- `python/tests/test_world_log_replay.py`, `test_world_log_audit.py`,
  `test_world_log_codecs.py`, `cited_not_run.py`;
- `python/tests/acceptance/test_l13_preimage_acceptance.py`,
  `python/tests/n2_arms_cut37.py`,
  `python/tests/acceptance/n2_arms_cut37.py`,
  `python/tests/acceptance/test_n2_cut37.py`,
  `python/tools/cut37_acceptance.py`;
- this cut, the ledger, roadmap, guide, README, the log design's L13 marker,
  the log-verification design's §5.3 note and §10 item 4 closure.

Frozen declarations and cut bodies through cut 36 remain byte-exact; cut 8's
`L13u1[38]`, `L13u2[39]` and `L13u3[40]` go stale by this cut's own edits
and are recorded, never repaired.

## 3. Selection

Eleven declaration units are selected and single-homed here. The quoted row
text is byte-exact from the named design at freeze.

```markdown
| L13 | Logged is not permitted | log-visible removal of a **verification** via a cooperative act → the removal is in the timeline **and** verification emits the policy finding naming the deleted record; assert the finding classifies it as removal of a *failing* verification only where the historical content resolves — a held copy or surviving preimage bytes — since entries retain state digests, not verdicts; with the preimage GC'd and no copy held, the deletion is still detected and the semantic classification is honestly absent; assert corpus retirement appends a status event and deletes nothing; assert preimage-blob GC appears in no chain |
```

| unit | row | what it reads |
|---|---|---|
| L13-a | L13 | a cooperatively logged removal of a failing verification is in the replayed timeline (`validated`, no disagreement) **and** draws `record-removed` naming the path and the removing `txid`, unchanged in code, severity, ref, detail and message — cut 8's L13u1 superseded by this unit |
| L13-b | L13 | the surviving preimage on the writable root: with no `history`, the removal classifies `failing-verification-removed` at `error`, `source=preimage`, the digest equal to `sha256` of the record's bytes before removal, the message naming the removed bytes and never a held copy — the resolver deferral closed |
| L13-c | L13 | digest, not path: `history` holding a hand-rendered copy of the same record (same id, verdict `passed`) is named nowhere — on the writable root the preimage classifies `verdict=failed`, and on the restored read-only copy the removal reads `removal-unclassified` naming the removed digest only — R16's weakened match reversed in the direction it said it could misclassify |
| L13-d | L13 | no local history: the restored `read-only-serviceable` copy audits to `record-removed` and `removal-unclassified preimage=refused`, the message carrying the engine's lifecycle refusal; the detached arrival of a raw copy reports `preimage=not-consulted`; with the removed bytes held under their digest, both classify `failing-verification-removed source=held-copy` — the row's "GC'd and no copy held" arm read at the width the design states (no collector exists; absence is constructible on non-writable roots only) |
| L13-e | L13 | corrupt local history: the indexed preimage leaf under the metadata root **unlinked** (a truncated leaf is caught earlier, by the registered inspection's own store checks, as raw `MetadataStoreInvalid` — not this cut's translation) → the audit refuses `LogEvidenceRefused` with `phase == "preimage"` and `engine_error == "MetadataStoreInvalid"`, no report, every project file byte-identical |
| L13-f | L13 | not a verification: a removed `discussion` record classifies `removal-classified kind=discussion source=preimage` at `warning`; the unreadable-facet, not-a-record and `digest=none` (symlink pre-state) arms are declared at the unit level over fabricated views (`test_world_log_replay.py`), with the declaration stating that width |
| L13-g | L13 | relabel: corpus retirement appends a status event and deletes nothing — cut 8's L13u4 cited (`../plans/2026-08-22-conformance-cut-8-results.md`); one durable check — a real world retires an admitted corpus, the registry gains one record, no registry file is removed, and the world chain's committed removals are empty |
| L13-h | L13 | relabel: preimage-blob GC appears in no chain — cut 8's L13u5 cited, a taxonomy fact over the closed entry-class union; one durable check — after an audit that resolved a preimage, the corpus chain's entries and tip are byte-identical to the pre-audit inspection (a read appends nothing) |
| BI-1 | — | the reads are made inside the audit's hold, after the inspection and both captures, one per committed removal with a file pre-state, with the chain's `txid`, `path` and `byte_len`; arrival and restore make none |
| BI-2 | — | a read mutates nothing: every file under the audited root and its metadata sibling's `blobs/` tree is byte-identical across the audit, and `read_preimage` appears in no `WRITE_ENTRY_POINTS` row |
| BI-3 | — | the re-hash: a seam returning bytes that hash to another digest for the removal refuses `PreimageMismatch` before any finding, over a real chain with every other seam callable the production one |

### 3.2 Rows not read

**L1** is not read; its persistence arms are `persistence-cut`'s
(`beliefs-3ea822`, cut 36 results §2). L13 is read in full.

## 4. Accounting

**11 declaration units**, eight against L13 and three boundary invariants;
L13 closes; row 5 stays partial for L1 alone. 186 of 216 → 187 of 216.

## 5. N2 and acceptance obligations

| arm | module | sabotage | check |
|---|---|---|---|
| L13-a | `world/verify.py` | `replay` emits no removal findings | L13-a |
| L13-b1 | `world/verify.py` | `removed_digest` answers `None` for every state (no digest, ever) | L13-b |
| L13-b2 | `world/verify.py` | `_read_preimages` passes `max_bytes=0` | L13-b |
| L13-c | `world/verify.py` | any held copy classifies (the digest lookup becomes "is anything held") | L13-c |
| L13-d1 | `world/verify.py` | the engine's refusal is reported as `not-consulted` | L13-d |
| L13-d2 | `world/verify.py` | `_admit_arrival` reads preimages | L13-d |
| L13-d3 | `world/verify.py` | absence goes silent (`removal-unclassified` dropped) | L13-d |
| L13-e | `root.py` | `MetadataStoreInvalid` downgraded to `PreimageUnavailable` | L13-e |
| L13-d4 | `root.py` | `PreconditionRefused` upgraded to `LogEvidenceRefused` (availability upgraded to a refusal is caught where availability is asserted) | L13-d |
| L13-f | `world/verify.py` | every decoded record is read as a verification | L13-f |
| L13-g | `world/registry.py` | retirement stops being append-only (cut 8's `_RETIREMENT_DELETES` site, re-run under this guard) | L13-g |
| L13-h | `world/logmodel.py` | an entry class acquires a `preimage_gc` member (cut 8's `_INTENT_ENTRY_RECORDS_GC` site, re-run under this guard) | L13-h |
| BI-1 | `world/verify.py` | the reads move outside the hold | BI-1 |
| BI-2 | `world/verify.py` | `_read_preimages` writes a marker file into the root | BI-2 |
| BI-3 | `world/verify.py` | the re-hash is skipped | BI-3 |

That makes **15 arms over 11 units** (L13-b homes two, L13-d four; every
other unit one). Both directions are required: the check passes on the real
tree and fails under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut36_acceptance.py",)` and carries
`PHASE_MODULES = ("test_l13_preimage_acceptance.py", "test_n2_cut37.py")`.

## 6. Second reader

Check that L13-c's hand-rendered copy really claims the removed path (same
id) and really differs in digest; that L13-d's restored copy is
`read-only-serviceable` (registered inspection) and the arrival's copy
`metadata-less` (detached); that L13-e unlinks the leaf the store indexes
under the removed digest (`blobs/sha256/<hex>`) and not some other file, and
that the registered inspection still passes over the missing leaf so the
refusal is the reader's; that BI-1 observes the writer hold through
`BuildContended` on the real operation lock and not a stub; that BI-3's
stand-in replaces `read_preimage` only.

## 7. Limitations

1. No read-only preimage arm (spec §12.1).
2. No collector, so no GC arm on a writable root (§12.2).
3. No consumer (§12.3).
