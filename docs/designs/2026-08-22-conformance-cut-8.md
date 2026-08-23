# Conformance cut 8 — log verification and anchoring

**Status:** Frozen 2026-08-22 at `117f37e`; second reader discharged
2026-08-22 (§7.1), its five findings and one spec-side stale claim closed
before freeze. **Discharged 2026-08-23** on branch `design/log-verification`
— results, with the evidence and the per-unit dispositions, at
`../plans/2026-08-22-conformance-cut-8-results.md`; the execution rulings at
`../plans/2026-08-22-log-verification-ledger.md`. Nothing below this header
changed at discharge. Three notes a reader needs and this frozen text cannot
carry. The specification cited in **Sources** was promoted in the banking
change and now lives at `2026-08-22-log-verification-design.md`, so the path
quoted there is pre-promotion. 51 of the 53 declaration units are
certified in full, the other two — L7u1 and L2u5 — partial, for reasons the
results record states. And **§7's byte-exactness charge now needs a stated
comparison basis**: the banking change amended the source L table in place,
so §3.1's quotations of **L4 and L10** are no longer byte-exact against the
live `2026-08-03-tamper-evident-log-design.md`. All twelve remain byte-exact
against that table **as of this cut's freeze commit `117f37e`**, which is the
basis to compare against; the two amendments are dated in the source rows,
move no disposition, and are ruled in the execution ledger (R39). No
mechanical guard enforces the pairing — this header is it.

**Sources:** `2026-08-20-conformance-cut-7.md` (rule and practice
inheritances); the log-verification specification
`docs/superpowers/specs/2026-08-22-log-verification-design.md` (cited as
*spec*); and the frozen L rows of
`2026-08-03-tamper-evident-log-design.md` §10, quoted verbatim below.

## 1. What this cut is

Cut 8 is the frozen acceptance boundary for world-index slice 3: the
registry log-head record and its codec, the exported head artifact and its
producer, the explicit anchor act, the one read-only log evaluator with its
four-step precedence, the audit act, the `ReplicaOf` arrival act, the world
genesis↔mirror agreement check, the ordered-cuts predicate, and the four
atoms seam obligations as consumed through `science.root`.

The selection rule is cut 5's rule, unchanged: a clause is selected only
when its source mutation and every named check run entirely inside §2. A
row with any unrun arm is **partial** — never "full" on an argument for why
an arm should not count (the error always runs toward overstating
coverage). Three practice inheritances: **labeled declarations** for
post-freeze arms and spec-minted obligations outside the frozen rows
(§3.3); **single-homing** for every cross-referenced assertion — each lives
in exactly one row's declarations and is cited, never re-declared,
elsewhere; and verbatim row quotation, byte-exact against the source table.

One principle is stated here because this cut is the first to need it
systemically: **engine-interior productions are certified in atoms; this
cut certifies the evaluator over fabricated states.** Where a row's
mutation runs inside the `atoms` transaction path — a kill between
registration stages, a genuine mid-transaction rollback — the producing
half is A7/A8's certified territory, and this cut's arm runs the evaluator
against a raw-fabricated chain carrying the resulting state. Every
fabricated chain must pass `inspect_chain` as well-formed **unless the
arm's point is the defect** (§6 makes this a declaration-time check), so a
fabrication can never smuggle in the malformation it claims not to have.

## 2. The boundary

**Mutation surface:** the Science modules this slice adds or amends —
`science/world/anchors.py`, `science/world/verify.py`, and the touched
surfaces of `science/world/registry.py`, `science/world/epoch.py`,
`science/world/read.py`, and `science/root.py` — plus, as **certified
engine**, the merged atoms seam (`inspect_chain`, the batch capture
command, the shared pending gate, `read_chain`): its interior is certified
by the atoms suite and is not this cut's mutation surface, exactly as the
executor was for cuts 4–7.

**Checks:** pytest nodes under `python/tests/`, and the cut-8 acceptance
run. Durable arms live on the repository's own volume, never `/tmp`, the
scratch volume, or `/dev/shm`. Count claims quote pytest's own summary
line under `pipefail`.

**The raw-write license:** sabotage and fixture construction may
raw-author chain entry files, registry records, epochs, head artifacts,
manifests, and configuration. Detection claims quantify over cooperative
writes; the license is the sabotage construction's, bounded by §1's
well-formedness obligation.

## 3. The rows

### 3.1 Rows read, quoted verbatim, with dispositions

| L1 | Registration precedes application, with no unregistered cooperative path | kill the executor between entry durability and apply at every stage → entry present, pending; recovery settles it and the surface matches the settlement; crash after entry durability but **before** the transaction record stores the entry digest → recovery appends **no second registration** (idempotent by transaction id); cut persistence at **every** stage of the settlement sequence, for **both terminal arms** — a normally committing and a normally rolling-back transaction alike → recovery converges on exactly one registration and one settlement, backfills the transaction record's settlement binding, and **neither terminal outcome is returned, nor the lease released, before the settlement is durable**; attempt any cooperative mutation path that skips registration → unspellable |

- **Partial.** Selected (1 unit): the unspellability arm — no cooperative
  mutation path skips registration, asserted over the composition surface
  (`science.root` is the only atoms importer; every **registered-surface
  mutation** flows through `run_transaction`, while genesis registration
  and intent append are protocol entries rather than application
  mutations). Deferred, engine-certified: every
  kill-at-stage and settlement-persistence arm — those run inside the
  transaction path and are A7/A8's certified productions; Science holds no
  persistence-cut harness (the cut-7 X2 gap, named, not argued around).

| L2 | Settlement gates every absence test | under an anchored observer set: roll back a registered creation → the record's absence is **not** refuted (no transition); commit a creation, then raw-delete the record → refuted at replay; append two settlements for one registration → **malformed** at step 1; a pending entry on a **live** root settles through recovery; the same entry on a **copied** root (no metadata) → **unresolvable at step 3**, whether the copy caught the transaction **before apply** (record absent) or **after apply** (record present) — never refuted as a disk mismatch, never inferred from disk — and further mutation on that root is refused |

- **Partial.** Selected (5 units): the rolled-back registration whose
  record's absence is **not** refuted — over a fabricated well-formed
  chain, with a declaration-time assertion that the fabricated entry is
  genuinely `settled(rolled-back)` and the path genuinely absent (§1's
  principle; the engine's own rollback production is atoms-certified);
  committed creation then raw-delete → refuted at replay; two settlements
  for one registration → malformed at step 1; the copied-root pending
  entry → unresolvable at step 3 in **both** variants — copy caught before
  apply (record absent) and after apply (record present) — never refuted
  as a disk mismatch; and further mutation refused — the pending gate's
  `PendingUnresolved` from all three commands (`register_root`'s
  existing-chain arm, `append_intent`, `run_transaction`). Deferred: the
  live-root pending entry settling through recovery — constructing a
  pending entry with live terminal metadata requires the persistence-cut
  harness (the same named gap).

| L3 | Valid-prefix truncation refutes; interior damage is malformed | anchor, then truncate the chain to a valid prefix behind the anchored head → **refuted** at step 2, and the finding names the unreachable anchored head; delete or rewrite an **interior** entry → broken linkage, **malformed** at step 1; raw-append a **sibling branch** beside a retained original, or an **orphan** entry → **malformed** at step 1 (§3's linearity invariant — one genesis-connected sequence, one tip), never a silently ignored fork — never silently validated in any arm |

- **Full** (4 units): valid-prefix truncation behind the anchored head →
  refuted, the finding naming the unreachable anchored head; interior
  entry deletion or rewrite → malformed at step 1; a raw-appended sibling
  branch beside the retained original → malformed; an orphan entry →
  malformed. Every arm additionally asserts the chain is never silently
  validated.

| L4 | Chain removal refutes against any surviving anchor, bound to its subject | delete the chain while a registry log-head record (or supplied exported head) is in the observer set → refuted — the "detectable journal removal" clause of kernel §8.7, discharged; with **two anchored corpora** and one arriving chainless → the subject binding associates the surviving anchor with the arriving corpus's `corpus_id` and refutes exactly it, never the sibling — an anchor is never matched to a root by elimination or by opaque genesis digest alone; raw re-mint an anchored corpus's manifest (`corpus.yaml` A → B) with the chain present → verify selecting **A**; A-bound anchors remain admitted by the selected subject, the manifest mismatch is reported separately, and replay **refutes** the edit — never `unresolvable` by subject disqualification; an edited configuration `world_id` against a present world chain → subject-mismatch finding **and operation refusal** (§3's lifecycle rule) — configuration is not registered surface, so replay cannot refute it, and the chain verdict derives independently of the presented configuration; replace an anchored corpus's chain with a **self-consistent different genesis** under the same `corpus_id`, verify selecting that subject → **refuted**, never empty-set `unresolvable` — a selected-subject anchor naming another genesis is replacement evidence, not a non-match; export a **W1** head, rewrite the local world subject and genesis to **W2**, verify explicitly selecting **W1** → refuted as removal/replacement, while selecting **W2** is a separate-world audit, never a verdict about W1; delete an anchored corpus A's chain **and** re-mint its `corpus.yaml` as B, then verify explicitly selecting **A** with A's anchor supplied → **refuted** as removal — the selected subject associates the anchor, and the presented manifest never discards it into empty-set `unresolvable`; delete or replace a store's chain while its store-subject registry record is in the observer set → **refuted**, the subject binding associating the anchor by `store_id`, never by elimination *(amended 2026-08-10, the verified-holdings record design §8)* |

- **Partial.** Selected (7 units): chain deletion against a surviving
  registry log-head record → refuted — kernel §8.7's "detectable journal
  removal" clause, discharged; two anchored corpora with one arriving
  chainless → the subject binding refutes exactly the arriving one, never
  the sibling; the raw manifest re-mint (A → B) with the chain present,
  verified selecting A → A-bound anchors admitted, the manifest mismatch
  reported separately, replay refuting the edit; the edited configuration
  `world_id` → subject-mismatch finding **and** `open_world`'s operation
  refusal, the chain verdict derived independently; chain replacement by a
  **self-consistent alternative chain under the same constant genesis**
  and the same `corpus_id` → refuted through anchored-head unreachability
  — the spec §1.2 amendment's stated mechanism for corpus replacement,
  since a fabricated distinct genesis would be malformed at genesis-form
  validation before any anchor judgment; the distinct-genesis variant is
  the future fork arm's, deferred with L10's fork arms;
  the W1 head exported, the local world rewritten to W2, verification
  selecting W1 → refuted as removal/replacement, selecting W2 a separate
  audit; and chain deletion **plus** manifest re-mint as B, verified
  selecting A with A's anchor supplied → refuted as removal, never
  empty-set unresolvable. Deferred: the store-subject arm (row 4 owns
  store roots; spec §10.2).

| L5 | The unanchored tail is the pinned residue | rewrite the tail beyond the maximal anchor into a self-consistent alternative **and rewrite the affected registered surface to match** → validated, undetected; assert the report's unanchored-tail extent covers it — the bound is anchor cadence, and the negative is the claim |

- **Full** (2 units): the consistent tail-and-surface rewrite beyond the
  maximal anchor → validated, undetected — the pinned negative, with §6's
  nonvacuousness check that the rewrite genuinely altered entries beyond
  the maximal anchor; and the report's unanchored-tail extent covering the
  rewritten span.

| L7 | Intent claims are exactly as wide as stated | assessment-run intent with **no pointers at all, or every `fulfills` pointer fully resolved and non-qualifying** — §6's exact reduction, never a collapse of an unresolved candidate → attempt-without-recorded-outcome finding, never a refutation; excise the intent entry after anchoring → **malformed** (interior linkage break) or, via truncation to a valid prefix, **refuted** — never silent; a second committed registration fulfilling the same intent, or a `fulfills` naming a missing or non-ancestor intent → **malformed**; mutate the fulfillment itself — a wrong-purpose committed transaction carrying `fulfills = I`, a run publication under another spec, another `event_token`, or a publication creating no run → each **fails qualification** (§3), the intent stays attempt-without-recorded-outcome, and the non-qualifying `fulfills` is named in a finding; make a **genuine** published run's bytes unresolvable → qualification **unresolvable**, and **no** unmatched finding is emitted (§6's reduction); kill between the intent's durable append and execution start → intent present, no execution — attempt-without-recorded-outcome, exactly as stated; race two cooperative intent appends on one root → serialized by the root lease, one linear chain, never a sibling branch (L3); attempt to publish the run through a root other than the intent's → **refused**, placement froze before execution; assert no caller-supplied `fulfills` path exists at the boundary; **negative:** crash, cancellation, and discarded failure are indistinguishable by construction; the guarantee quantifies over **both** intent kinds — instantiated for the holdings shape, a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between a holdings intent's append and its mutation reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-10, the verified-holdings record design §8)*; the guarantee now quantifies over the **operation intent** too — instantiated for its shape, a report carrying another operation's token, a report of the wrong kind, a run publication for a non-run operation, or a registration publishing no terminal record each **fails qualification** (a second fulfilling registration on one intent stays the chain's **malformed**, classified before qualification — T2's arm), and a kill between the operation intent's append and its first act reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-11, the act-report design §3)* |

- **Partial**, a recorded refinement of spec §9's expectation (which
  anticipated wholly deferred; the spec states dispositions are fixed at
  this freeze). Selected (2 units), both chain-structural and fabricated:
  a `fulfills` naming a missing or non-ancestor intent → malformed; a
  second committed registration fulfilling one intent → malformed. These
  are `inspect_chain` taxonomy entries with no other certifying home —
  leaving them deferred would ship untested defect classes. Deferred,
  owner named (the intent-boundary slice): the entire qualification
  reduction and its findings, every boundary-side arm (placement freeze,
  no caller-supplied `fulfills`, kill windows), and both non-run intent
  shapes; the intent-excision arm is L3-shaped and stays homed in L3.

| L8 | Cross-chain order exists only through world-ancestry-ordered cuts | committed spec-freeze transition in E1's captured head, intent absent from E1, intent in E2, E2's build-start world head descending from E1's publication entry → ordered; both events first appearing in one cut → unordered, and "spec predates run" is not emitted; assert epoch sequence numbers are read by nothing |

- **Partial.** Selected (2 units): the ordered-cuts predicate — E2 orders
  after E1 **iff** E2's build-start world head descends from E1's settled
  publication entry, with a missing or rolled-back publication →
  unordered; and the negative that epoch sequence numbers are read by
  nothing. Deferred (this design's successor work, spec §10.7): the
  event-level relation — spec-freeze/intent presence and exclusion
  reasoning across captured corpus heads.

| L9 | Anchor evaluation is total over the observer set, never best-reachable | observer set holding an old reachable anchor and a newer anchored head absent from the chain → refuted, never validated-through-the-old; two mutually incomparable anchored heads for one genesis → refuted; empty set → unresolvable with the observer bound recorded; assert `anchored-through` and the observer set appear as report fields, and that malformed structure stops evaluation before any anchor judgment |

- **Full** (5 units): an old reachable anchor plus a newer anchored head
  absent from the chain → refuted, never validated-through-the-old; two
  mutually incomparable anchored heads for one genesis → refuted; the
  empty observer set → unresolvable with the observer bound recorded;
  `anchored-through` and the observer set present as report fields; and
  malformed structure stopping evaluation before any anchor judgment.

| L10 | A fork is a new chain; a replica is the same chain | fork act → fresh genesis carrying `(parent genesis, parent head)` and its own baseline; assert parent and fork anchors are never compared; replica/restore → same genesis, chain carried unchanged, comparability intact; a copy presenting the parent genesis under a fresh `corpus_id` manifest without a fork-genesis → its chain refuses to verify under the new identity (genesis names the parent `corpus_id`); the **store instantiation** (the verified-holdings record design §2) — replica act → same genesis, chain carried unchanged, the copy stamped read-only in engine bookkeeping, the stamp durable **before** the copy is exposable; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation on any root **not granted writability** → refused, the fork act the only exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative *(amended 2026-08-10, the verified-holdings record design §8)* |

- **Partial.** Selected (1 unit): the copy-presenting-the-parent-genesis
  arm, under the spec §1.2/§6.2 amendment's mechanism — `admit_arrival`
  selects `S = Corpus(provenance.parent_corpus_id)`, so a copy presented
  under a fresh `corpus_id` manifest without a fork genesis refuses with
  `SubjectMismatch`: the chain refuses to verify under the new identity,
  exactly the frozen claim, reached through the arrival act rather than a
  genesis-payload comparison. Deferred, owner named (row 4): every fork,
  replica-construction, restore, and store-instantiation arm.

| L11 | The world chain is anchored only by export | present an epoch stored inside the world root as the world chain's anchor → not accepted into the observer set, while the **same** epoch supplied for a **corpus** subject is accepted — eligibility is carrier-specific, not a property of the epoch; a registry log-head record carrying a `world` subject → unconstructible through the anchor act and never accepted as an anchor; coordinated truncation of world chain, registry, and in-root epochs with no exported holder → undetected (**negative**, the surviving-observer bound); the same truncation with one exported epoch supplied → refuted |

- **Full** (4 units): an epoch stored inside the world root, presented for
  the world subject → not accepted, while byte-identical epoch content
  supplied as an export is — and the **same** epoch accepted for a corpus
  subject, eligibility being carrier-specific (the provenance
  discriminator, spec §4.1); a registry log-head record with a `world`
  subject → unconstructible and never accepted; coordinated truncation of
  world chain, registry, and in-root epochs with no exported holder →
  undetected, the surviving-observer negative; the same truncation with
  one exported epoch supplied → refuted.

| L12 | One state vocabulary, and the log path is bookkeeping | each typed state class — absence, directory, symlink target, mode — round-trips through registration fingerprints and replay; assert no second summary model exists; appending the log is not recursively registered; raw-edit the log path **within the anchored prefix** → caught at step 1 (interior damage, malformed) or step 2 (prefix truncation, refuted); **negative:** a structurally valid raw append beyond the maximal anchor — most sharply a forged intent — passes steps 1 and 2 and may later be anchored: L5's residue, and why every entry-proves-an-act claim holds only under the cooperative-write assumption (§3) |

- **Full** (5 units): each typed state class — absence, directory, symlink
  target, mode — round-tripping through registration fingerprints and
  replay; no second summary model (Science fingerprints exclusively
  through the atoms capture command, asserted over the package surface);
  log-path appends not recursively registered; a raw edit of the log path
  within the anchored prefix → malformed (interior) or refuted (prefix
  truncation); and the negative — a structurally valid raw append beyond
  the maximal anchor, most sharply a forged intent, passing steps 1 and 2,
  L5's residue.

| L13 | Logged is not permitted | log-visible removal of a **verification** via a cooperative act → the removal is in the timeline **and** verification emits the policy finding naming the deleted record; assert the finding classifies it as removal of a *failing* verification only where the historical content resolves — a held copy or surviving preimage bytes — since entries retain state digests, not verdicts; with the preimage GC'd and no copy held, the deletion is still detected and the semantic classification is honestly absent; assert corpus retirement appends a status event and deletes nothing; assert preimage-blob GC appears in no chain |

- **Partial.** Selected (5 units): a cooperatively logged verification
  removal → present in the replayed timeline **and** the policy finding
  naming the deleted record; the *failing-verification* classification
  where supplied `history` bytes resolve, the finding naming the matched
  digest; the no-copy case → deletion still detected, semantic
  classification honestly absent; corpus retirement appending a status
  event and deleting nothing; and preimage-blob GC appearing in no chain —
  asserted as a taxonomy fact over the entry classes, with the declaration
  stating that width. Deferred, owner named (spec §10.4): the
  preimage-store-backed classification, waiting on the atoms blob-read
  seam.

### 3.2 The row not read

**L6** (the genesis baseline reaching pre-log history) is not read by this
cut: both arms fail construction under the spec §1.3 empty-baseline
amendment. The positive arm needs a populated baseline no Science path
mints and genesis-form validation rejects as malformed; the anchor-free
negative needs the same populated-baseline starting state for the omission
to be the **baseline's** claim — under empty baselines it collapses into
the anchor-free rewrite residue already homed in L5. Reading L6 would
certify nothing the amendment leaves standing; the row waits on the
registration-surface design act named in the spec's deferral ledger
(§10.6 there).

### 3.3 Labeled declarations

Ten labeled declarations carry the spec's minted obligations outside the
frozen rows; each is declared as data beside the selected arms, with the
same audit discipline:

1. **Genesis-form malformation** — an undecodable or wrong-form genesis
   payload, or a non-empty baseline, → malformed before anchor evaluation;
   a valid world genesis naming a different `world_id` is subject-mismatch,
   never malformed (spec §4.2, §1.3).
2. **Arrival cause precedence** — causes rank `malformed` > `refuted` >
   `pending` > `chainless`, derived from report fields, not precedence
   steps: a pending chain under an empty observer set is
   unresolvable-unanchored yet refuses with cause `pending`; `AbsentChain`
   with empty observers refuses `chainless` (spec §6.2).
3. **The bare-admit refusal and the shared core** — `World.admit` refuses
   `ReplicaOf` with `ReplicaAdmissionRequiresVerification`; `admit_arrival`
   commits through the same admission core, and the `AdmissionRecord`'s
   identity is byte-identical to a fixture admission of the same inputs —
   admission identity unamended (spec §6.2).
4. **Refusal ordering at arrival** — report-based refusals outrank the
   subject-mismatch refusal, and that refusal precedes the admission
   transaction; the underlying mismatch outcomes are homed in L4 (the
   audit finding and configuration refusal) and L10 (the arrival refusal)
   and are cited here, never re-declared (spec §6.3).
5. **The mirror branch and audit callability** — `open_world`'s
   `world.yaml` mirror-agreement check refuses on mismatch, and the world
   audit remains callable on exactly the worlds `open_world` refuses; the
   configuration-mismatch outcome itself is homed in L4 and cited (spec
   §6.1, §6.3).
6. **Store subjects are shape-only** — the log-head and head-artifact
   codecs round-trip the store arm; the evaluator refuses
   `StoreSubjectUnsupported`; the anchor act's signature cannot spell a
   store (spec §3.1, §10.2).
7. **Export binds the subject** — `export_head_artifact` refuses a
   `World(world_id)` disagreeing with configuration or genesis; a corpus
   subject resolves under the exactly-one-carrier rule; the function takes
   no actor and writes nothing; the returned bytes decode under
   `science.head-artifact.v1` (spec §3.2).
8. **Anchor-act refusals and idempotency** — `AnchorSubjectUnknown` for an
   unknown `corpus_id`; `AnchorTargetUnresolvable` for zero or multiple
   carriers; byte-identical re-anchoring is idempotent success submitting
   no transaction, a same-name different-bytes record a collision; terminal
   corpora are anchorable (spec §3.1, §3.3).
9. **History evidence is validated** — a malformed `history` key, or bytes
   not hashing to their key, refuses the act; keys are exactly
   `sha256:<64 lowercase hex>`; every classified finding names the matched
   digest (spec §5.3).
10. **One evaluator, one inspection contract** — audit and arrival share
    the one read-only evaluator and no third path evaluates; the staging
    leaf is never a foreign-leaf defect; `MalformedChain` carries one
    deterministic first defect; detached mode requires no metadata root
    (spec §2.1, §4.1, §6.1–§6.2).

## 4. Accounting

Twelve rows read: **5 full** (L3, L5, L9, L11, L12) **+ 7 partial** (L1,
L2, L4, L7, L8, L10, L13); L6 unread (§3.2). Selected units by row: L1 1,
L2 5, L3 4, L4 7, L5 2, L7 2, L8 2, L9 5, L10 1, L11 4, L12 5, L13 5 —
**43 selected + 10 labeled = 53 declaration units**.

## 5. N2 obligations

Beyond the standing N2 harness discipline (arms declared as data; `vacuous`,
`uncollected`, and `stale` reported as malformed contract content), the
declarations carry these check-time obligations:

1. **Fabrication well-formedness** (§1): every fabricated chain passes
   `inspect_chain` as well-formed, asserted at declaration time — except
   where the arm's point is the defect, in which case the declaration
   asserts exactly the one intended defect class and no other.
2. **L2's rollback arm** asserts the fabricated entry is
   `settled(rolled-back)` and the target path absent before evaluating —
   a refusal-before-registration or a missing settlement makes the arm
   vacuous.
3. **L5's rewrite arm** asserts the rewritten tail differs byte-wise from
   the original beyond the maximal anchor, and that at least one rewritten
   entry exists — an empty rewrite validates vacuously.
4. **L4's two-corpora arm** constructs two distinct corpus roots with
   distinct `corpus_id`s, both anchored, before removing one chain.
5. **L11's coordinated-truncation arm** asserts all three in-root carriers
   (world chain tail, registry records, in-root epochs) were actually
   truncated — a partial truncation refutes for the wrong reason.
6. **L12's round-trip arm** covers all four state classes; a subset pass
   is reported as malformed declaration content, not a pass.
7. **Count claims** in the results record quote pytest's summary line
   under `pipefail`, never a collect-only count.

## 6. Freeze obligations

Two, on the cut-7 precedent of naming them before the plan exists: the
**L4 manifest re-mint arm** must interpose no other mutation between the
re-mint and verification (the mismatch must be the only delta), checked at
declaration time; and the **L8 predicate arm's unordered case** must be
constructed from a genuinely rolled-back or absent publication entry,
asserted by entry class, never from two arbitrary epochs.

## 7. Second reader

The charge, unchanged from cut 7 §6: verify every quoted row byte-exact
against the source table; audit each selection against §2's boundary;
check single-homing across rows and labeled declarations; test each
partiality against the any-unrun-arm rule (no "full" by argument); verify
the §4 accounting by independent recount; and read §3.2's unread-row
justification adversarially. Findings and their dispositions are recorded
here before freeze.

### 7.1 The run and its dispositions

The reader ran 2026-08-22 and returned five findings, all closed at
`c5700ed` before freeze: the L4 different-genesis unit contradicted
genesis-form validation and was replaced by the same-genesis
alternative-chain unit refuted through ancestry; L6's selected negative
was vacuous under the §1.3 amendment and the row moved to unread (§3.2);
L10's unread justification failed adversarial review — the arrival act
constructs the frozen copy-under-a-fresh-manifest case — and the row moved
to partial with that one amended arm; labeled declarations 4 and 5
violated single-homing against L4 and L10 and were narrowed to ordering
and the mirror branch respectively; and L1's boundary wording overclaimed
`run_transaction` coverage and was corrected to registered-surface
mutations. A sixth, spec-side stale claim ("all of L10 wait on row 4",
spec §10.3) was corrected in the freeze change. Mechanical checks at
discharge: quoted rows byte-identical (L1–L5, L7–L13); independent
recount 43 selected across 12 rows plus 10 labels; corpus guard 12/12;
guide check exit 0; `git show --check` clean.

## 8. Limitations

1. **No persistence-cut harness.** Every kill-at-stage arm defers to
   atoms's certification; Science-side observation of mid-transaction
   states remains unconstructible (the cut-7 X2 gap, third cut running).
2. **The evaluator is certified over fabricated states** for
   engine-interior productions (§1). The fabrication license is bounded by
   the well-formedness obligation, but a systematic divergence between
   fabricated and engine-produced chains would evade this cut; the atoms
   suite is the standing mitigation.
3. **Intent qualification is entirely out** (L7's reduction); the cut's
   L7 units certify inspection taxonomy only.
4. **L10's fork, replica-construction, restore, and store arms have no
   certification here**; only its arrival-identity arm is read. **L6 is
   unread entirely** (§3.2).
5. **The cut inherits the spec's dated amendments** (§1.2, §1.3); if a
   future design lifts either, the affected declarations are extended by a
   successor cut, never edited here.
6. **The acceptance-node dependency** noted in cut 7's results (§8 there)
   applies unchanged: explicit node ids beating `--ignore` is undocumented
   pytest behavior the harness relies on.
