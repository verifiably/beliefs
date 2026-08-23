# Conformance cut 9 — root lifecycle and the store substrate

**Status:** Drafted 2026-08-23; awaiting the second reader (§7); **freezes
before any implementation** (spec §8 step 3). The L6 source row was amended
with the fork-baseline lift before this draft, so §3.1's quotation carries
the lifted ruling.

**Sources:** `2026-08-22-conformance-cut-8.md` (rule and practice
inheritances); the root-lifecycle specification
`docs/superpowers/specs/2026-08-23-world-index-root-lifecycle-design.md`
(cited as *spec*); the frozen L rows of
`2026-08-03-tamper-evident-log-design.md` §10 as amended through the
2026-08-23 fork-baseline lift, quoted verbatim below; and **W13** of
`2026-08-02-world-addressing-design.md`, quoted verbatim below.

## 1. What this cut is

Cut 9 is the frozen acceptance boundary for world-index slice 4: the
fail-closed writer state as consumed through `science.root`; the four
atoms lifecycle seam obligations (`replicate_root`, `fork_root`,
`grant_read_serviceability`, `read_lifecycle_state`); store subjects
through the anchor act, the head-artifact producer, and the evaluator;
`restore_root`; the fork acts with act-minted manifests; and fork-of
admission.

The selection rule is cut 5's rule, unchanged: a clause is selected only
when its source mutation and every named check run entirely inside §2. A
row with any unrun arm is **partial** — never "full" on an argument for
why an arm should not count. The three practice inheritances stand:
labeled declarations (§3.3), single-homing, and verbatim row quotation,
byte-exact against the source tables as of this cut's freeze commit.

Cut 8's engine-interior principle applies systemically here: **durability
orders and kill windows inside the lifecycle commands are atoms-certified
productions; this cut certifies Science's orchestration, the evaluator,
and the lifecycle-state readings over the resulting states** — fabricated
where the production is engine-interior, and every fabricated chain or
bookkeeping state passes `inspect_chain` (or presents exactly its one
intended defect or lifecycle delta, asserted at declaration time).

## 2. The boundary

**Mutation surface:** the Science modules this slice adds or amends —
`science/root.py` (`init_store_root`, the lifecycle wrappers,
`restore_root`, the fork acts, lifecycle-state consumption),
`science/world/anchors.py`, `science/world/verify.py`, and the touched
surfaces of `science/world/registry.py` (fork-of admission) — plus, as
**certified engine**, the merged atoms lifecycle seam (the three mutating
commands and the state query) beside the standing four commands: their
interiors are certified by the atoms suite and are not this cut's
mutation surface, exactly as for cuts 4–8.

**Checks:** pytest nodes under `python/tests/`, and the cut-9 acceptance
run. Durable arms live on the repository's own volume, never `/tmp`, the
scratch volume, or `/dev/shm`. Count claims quote pytest's own summary
line under `pipefail`.

**The raw-write license:** sabotage and fixture construction may
raw-author chain entry files, engine bookkeeping (including fabricated
pre-lifecycle vintages and binding deltas), registry records, manifests,
head artifacts, and configuration. Detection claims quantify over
cooperative writes; the license is the sabotage construction's, bounded
by §1's well-formedness obligation.

## 3. The rows

### 3.1 Rows read, quoted verbatim, with dispositions

| L4 | Chain removal refutes against any surviving anchor, bound to its subject | delete the chain while a registry log-head record (or supplied exported head) is in the observer set → refuted — the "detectable journal removal" clause of kernel §8.7, discharged; with **two anchored corpora** and one arriving chainless → the subject binding associates the surviving anchor with the arriving corpus's `corpus_id` and refutes exactly it, never the sibling — an anchor is never matched to a root by elimination or by opaque genesis digest alone; raw re-mint an anchored corpus's manifest (`corpus.yaml` A → B) with the chain present → verify selecting **A**; A-bound anchors remain admitted by the selected subject, the manifest mismatch is reported separately, and replay **refutes** the edit — never `unresolvable` by subject disqualification; an edited configuration `world_id` against a present world chain → subject-mismatch finding **and operation refusal** (§3's lifecycle rule) — configuration is not registered surface, so replay cannot refute it, and the chain verdict derives independently of the presented configuration; replace an anchored corpus's chain with a **self-consistent different genesis** under the same `corpus_id`, verify selecting that subject → **refuted**, never empty-set `unresolvable` — a selected-subject anchor naming another genesis is replacement evidence, not a non-match; export a **W1** head, rewrite the local world subject and genesis to **W2**, verify explicitly selecting **W1** → refuted as removal/replacement, while selecting **W2** is a separate-world audit, never a verdict about W1; delete an anchored corpus A's chain **and** re-mint its `corpus.yaml` as B, then verify explicitly selecting **A** with A's anchor supplied → **refuted** as removal — the selected subject associates the anchor, and the presented manifest never discards it into empty-set `unresolvable`; delete or replace a store's chain while its store-subject registry record is in the observer set → **refuted**, the subject binding associating the anchor by `store_id`, never by elimination *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2 — mechanism, not verdict: the corpus genesis is identity-free, so the "self-consistent **different** genesis under the same `corpus_id`" arm is not currently constructible — a fabricated distinct corpus genesis is malformed at genesis-form validation before any anchor judgment. Corpus-chain **replacement** is refuted through anchored-head unreachability under the same constant genesis instead, which is the arm conformance cut 8 reads; the different-genesis refutation is read for **world** subjects and defers, with L10's fork arms, for a future fork genesis)* |

- **Partial (this cut reads 2 units; cut 8's seven stand certified there,
  cited never re-declared).** Selected: **(u1)** the store arm — delete or
  replace a store's chain while its store-subject registry record is in
  the observer set → refuted, the anchor associated by `store_id`, never
  by elimination; **(u2)** the fork-genesis mismatch arm, in the §1.2
  amendment's deferred reading now constructible — replace an anchored
  fork's chain with a self-consistent chain under a **different fork
  genesis** while both present the **same child corpus subject**, verify
  selecting that subject with the original anchor supplied → **refuted**
  as replacement, the genesis-mismatch mechanism firing for a corpus for
  the first time. Parent and child anchors are incomparable by policy and
  never reach this comparison — that assertion is homed in L10 and cited.

| L6 | The genesis baseline reaches pre-log history — once anchored | register over a populated root, anchor, then delete a baseline-covered pre-log record → refuted at replay; **negative:** with **no surviving anchor for the selected subject**, rewrite genesis, baseline, and chain consistently to omit the record → unresolvable at best, undetected — the baseline is load-bearing only under an anchor, and one surviving selected-subject anchor turns the same rewrite into a refutation (L4) *(amended 2026-08-23, the log-verification design §1.3 — **both arms are presently unconstructible**: every genesis baseline is empty, no Science path mints a populated one, and genesis-form validation refuses a non-empty baseline as malformed, so the positive arm has no starting state; the anchor-free negative needs the same populated-baseline start for the omission to be the **baseline's** claim, and under empty baselines it collapses into the anchor-free rewrite residue already homed in L5. Conformance cut 8 reads this row **not at all** — reading it would certify nothing the amendment leaves standing. Lifting the amendment is a registration-surface design act, and the row is then read by that act's own cut)* *(amended 2026-08-23, the root-lifecycle design — world-index slice 4, §5 — the lifting act: a **fork genesis** registers the destination surface after its overrides as its baseline — non-fork geneses still require an empty baseline, and `init_store_root` refuses a populated payload root — so a populated baseline is mintable by exactly one path, the fork act, and **both arms are constructible over a forked root**: register the fork over its copied, populated destination, anchor, then delete a baseline-covered pre-log member → **refuted** at replay; with no surviving anchor for the selected fork subject, rewrite genesis, baseline, and chain consistently to omit it → **unresolvable** at best — the baseline's claim, no longer collapsing into L5's residue, because the omitted member was the **baseline's** to state. Conformance cut 9 reads both arms)* |

- **Full.** Selected (2 units): **(u1)** the positive arm over a forked
  root — fork, anchor the fork's head, then delete a baseline-covered
  pre-log member → **refuted** at replay, with a declaration-time
  assertion that the deleted member is genuinely baseline-covered and
  pre-log (§5); **(u2)** the anchor-free negative — with no surviving
  anchor for the selected fork subject, rewrite genesis, baseline, and
  chain consistently to omit the member → **unresolvable** at best,
  asserted never validated and never refuted, the omission being the
  baseline's claim.

| L10 | A fork is a new chain; a replica is the same chain | fork act → fresh genesis carrying `(parent genesis, parent head)` and its own baseline; assert parent and fork anchors are never compared; replica/restore → same genesis, chain carried unchanged, comparability intact; a copy presenting the parent genesis under a fresh `corpus_id` manifest without a fork-genesis → its chain refuses to verify under the new identity (genesis names the parent `corpus_id`); the **store instantiation** (the verified-holdings record design §2) — replica act → same genesis, chain carried unchanged, the copy stamped read-only in engine bookkeeping, the stamp durable **before** the copy is exposable; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation on any root **not granted writability** → refused, the fork act the only exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2/§6.2 — mechanism, not verdict: the copy presenting the parent genesis under a fresh `corpus_id` manifest **cannot** be caught by a genesis-payload comparison, since a corpus genesis names no `corpus_id`. The arrival act is the mechanism instead — `admit_arrival` selects `S = Corpus(provenance.parent_corpus_id)`, because the chain a replica carries is its parent's, and the fresh manifest then refuses `SubjectMismatch`: its chain refuses to verify under the new identity, exactly the frozen claim. This is the one arm of this row conformance cut 8 reads; every fork, replica-construction, restore and store arm still waits on ledger row 4)* |

- **Partial.** The arrival-identity arm is cut 8's, cited never
  re-declared; the holdings-read consequence clauses defer, named below.
  Selected (12 units): **(u1)** fork act → fresh genesis carrying
  `(parent genesis, parent head)` and its own baseline, asserted against
  the fork's chain; **(u2)** parent and fork anchors are never compared —
  a parent anchor in a fork-subject observer set participates in no
  genesis or ancestry judgment; **(u3)** replica and restore → same
  genesis, chain carried unchanged, comparability intact; **(u4)** the
  replica's read-only stamp is durable before the copy is exposable —
  asserted over the command's post-states, the kill interior being the
  engine's certified production; **(u5)** a kill inside the stamp window
  → metadata-less, hence read-only, never a writable twin; **(u6)**
  cooperative mutation on any root not granted writability → refused;
  **(u7)** the fork's new genesis is durable before its writability
  grant, and a kill between them leaves a read-only root — pre-grant
  retry completes the grant (spec §4, label 4's discipline); **(u8)**
  copy any store tree without its engine metadata — replica or original
  alike — and cold-bootstrap it → read-only, every mutation refused, the
  stamp's loss failing closed; the **unresolvable-for-holdings-reads and
  dereference-minting clauses defer to the holdings slice** — no holdings
  read exists to refuse; **(u9)** restore two metadata-less copies of one
  `store_id` on two hosts → both enter service read-only, a write on
  either refused, the sole writable exit a fork under a new `store_id`;
  **(u10)** an interrupted copy carrying genesis and chain with payload
  files missing → the restore act's verification never returns
  `validated`, the verdict preserved, the root unserviceable — its
  dereference behavior again the holdings slice's; **(u11)** a restore
  presented with an empty store-anchored observer set → `unresolvable`,
  replay not reached, the root unserviceable; **(u12)** raw-written
  copies of one `store_id`: branches assembled in one root →
  sibling-malformed (L3's classification, cited); both divergent heads
  supplied as anchors in one observer set → refuted (L9, cited); the same
  two copies verified separately after their last common anchored head →
  each validates, the divergent tails L5's unanchored residue — the
  pinned surviving-observer negative, asserted as the claim.

| **W13** | A corpus identity is minted, opaque and stable; its state identity is over content (§5) | Move a corpus's root directory, rename it, re-clone it and mount it at a second path; assert `corpus_id` is **unchanged** in every case, and that the coverage declaration naming it — and therefore `belief_input_digest` — is unchanged with it. Assert `corpus_id` is **not** derived from the path, directory name, remote URL or project name: change each and assert no effect; and assert **no ordinary API re-mints** it for an existing corpus. **Negative — amended 2026-08-03 (packaging §4): the immutability is the API's; manifest-only re-minting is detected, coordinated forgery is not.** Raw-edit the manifest's `corpus_id`, regenerate the snapshot and receipt consistently, and assert the next index build **refuses** — the presented id has no admission record while the registry still names the original (packaging X7). Then perform the **coordinated** act: raw-forge an admission for the new id while **retaining** the old id's admission — as a legitimate fork's registry would read — and assert **nothing detects it**: every state identity is self-consistent and the registry is well-formed. Under that retained-admission variant, assert the case that *looks* like a detection is not one: keep an **older replica** still resolving the pre-edit states, and assert every receipt naming them is **unresolvable against the edited corpus** (its states all moved with the id), that resolving them against the replica validates **the replica**, that **no assertion ties the new id to the old**, and that the resulting pair is **indistinguishable from a declared fork**. **Separately**, raw-delete an admission record alone and assert both halves: nothing detects the loss, **and** it evades nothing — the re-minted id is still unadmitted and the build still refuses (packaging X7). Assert no finding is emitted for any undetected case — G4/G8/S3's undetectable-history limit, one partial detection deep, needing §9's log for the rest. **Uniqueness:** place two corpora carrying one `corpus_id` in one world and assert the index build reports **corruption** and offers **no merge** — the W8b handling, not the duplicate-location one. **Replica vs fork:** restore a corpus from a backup and mount it in place of the original; assert the id is **retained** and every coverage declaration naming it still resolves. Then copy a corpus as a **fork**; assert a fresh id is minted, that the declaration is **authored** rather than inferred from the bytes, and that an undeclared fork is caught **only** when both corpora are live in one world. **State identity is content, not filesystem:** change a node's content and assert the corpus-state identity moves; **add, remove and retarget a `produces` relation** and assert it moves each time, **while the run's world address and every semantic identity stand still** — the case a subset-based content identity would have missed and the producers map is derived from. Then reformat a non-node file **other than the manifest**, rename a node's **file** without changing its `uid` or content identity, and touch every mtime, and assert the state identity is **unchanged**. **Amended 2026-08-04 (domain-extension-boundary §7): the manifest splits three ways** — reformat `corpus.yaml` (whitespace, key order, quoting) or reorder its `domains` mapping and assert the state identity is **unchanged**, since the member is a canonical projection of the parsed manifest; change any manifest field **semantically** — a pinned `science_contract` or domain contract identity, `corpus_id`, fork provenance — and assert it **moves**; and assert an unknown field, a duplicate `domains` key, or a malformed contract identity is **refused at load** rather than digested. Assert the identity is computed over `nodes`' **canonical JSON projection** (`STANDARD.md` §11.1) including `relations` and `facets`, and that **reordering a node's relations does move it** — the deliberate false positive, since cross-language equality is defined over document order. **Negative — not git:** compute the state identity for a corpus that is **not a repository** and assert it exists; then, in one that is, modify an **untracked** node file and assert the state identity **moves** while `HEAD` does not, and commit with no content change and assert it does **not** move. **Negative — a project identity is not a corpus identity:** point two projects at one corpus and assert one `corpus_id`; repoint a project to another corpus and assert **no** corpus identity changed |

- **Partial (this cut reads the fork-constructor arm; the slice-1 and
  cut-6 units stand, cited never re-declared).** Selected (2 units):
  **(u1)** the fork act mints a fresh `corpus_id` — opaque, path- and
  name-independent, with no ordinary re-mint path, asserted over the act;
  **(u2)** the fork declaration is **authored by the act**: the child
  manifest's `forked_from` carries the parent's `corpus_id` and
  corpus-state identity, derived from the parent's genesis-verified root
  at its captured state, never inferred from bytes and never
  caller-supplied. The undeclared-fork detection bound is X5's and cut
  6's, cited.

### 3.2 Rows not read

Every other L row stands at its prior cut's certification; this cut reads
exactly the rows its slice's mutations move. No expected row fails
construction — the fork-baseline lift (§8 step 2 of the spec) landed
before this draft precisely so L6 would not.

### 3.3 Labeled declarations

Ten labeled declarations carry the spec's minted obligations outside the
frozen rows, declared as data beside the selected arms:

1. **The initialization-operation grant discipline** — `register_root`
   records a local initialization operation before genesis; the grant
   completes that operation; the retry matching the recorded operation —
   and only that retry — completes a crash-interrupted grant; the bare
   matching-existing-genesis arm never grants (spec §2).
2. **The root/host binding** — no grant honored without a matching
   binding; a mismatch reports `binding-mismatched` and conveys no grant;
   moving or renaming a writable root invalidates its grant, and no
   writable rebind operation exists (spec §2).
3. **The migration** — the operator-authorized success records the grant
   with a fresh binding; metadata-less roots and post-lifecycle binding
   mismatches never migrate; migration provenance is attested, not proven
   (spec §2).
4. **No-clobber and the operation identity** — both copy commands claim
   destination exclusivity durably at start; fork retry splits at the
   grant: pre-grant proves genesis, baseline, and destination tree;
   post-grant recognizes the operation identity and returns success
   without requiring the original snapshot (spec §4).
5. **The grant primitive is structural and idempotent** —
   `grant_read_serviceability` rechecks non-writability and current
   state only, returns success without another write on a matching
   read-only serviceable state, accepts no verdict or attestation, and
   atoms spells no `restore_root` (spec §4).
6. **The lifecycle union is closed at five** — `read_lifecycle_state`
   returns exactly writable, read-only serviceable, read-only
   unserviceable, metadata-less, or `binding-mismatched`; the mismatch is
   its own declared state, never the state the bookkeeping's bytes claim
   (spec §4).
7. **`restore_root` is one held boundary** — inspect → capture presented
   identity and surface → evaluate → subject-agreement gate → grant; a
   malformed view reaches `evaluate_log` and returns `malformed`; a
   `validated` report with subject mismatch does not grant; the subject
   binds by root kind — store by genesis `store_id`, corpus by manifest
   `corpus_id` with the genesis passing form validation only; restore
   never grants writability (spec §7.2).
8. **`admit_arrival` branches over the full union** — registered
   inspection on read-only serviceable; detached on read-only
   unserviceable, metadata-less, and binding-mismatched; **writable
   refuses**; a restored corpus arrival is serviceable before
   registered-mode arrival; the detached staging-leaf ruling untouched
   (spec §7.2).
9. **Store-subject resolution is the supplied root** — `anchor_heads` and
   `export_head_artifact` resolve a store by supplied root whose genesis
   must carry the subject's `store_id`, verified before head acceptance
   or registry mutation; a store audit holds one boundary across
   inspection, surface capture, and evaluation; no store-admission
   registry exists (spec §7.1).
10. **Genesis-form and baseline construction** — `init_store_root`
    refuses a populated payload root; a fork genesis's baseline is the
    destination surface after its overrides; non-fork geneses require an
    empty baseline (spec §3, §5) — the constructions L6's arms stand on,
    declared once here.

## 4. Accounting

Four rows read: **1 full** (L6) **+ 3 partial** (L4, L10, W13). Selected
units by row: L4 2, L6 2, L10 12, W13 2 — **18 selected + 10 labeled =
28 declaration units**.

## 5. N2 obligations

Beyond the standing N2 harness discipline, the declarations carry these
check-time obligations:

1. **Fabrication well-formedness** (§1): every fabricated chain or
   bookkeeping state passes `inspect_chain` — or presents exactly its one
   intended defect or lifecycle delta and no other — asserted at
   declaration time.
2. **L6 u1** asserts the deleted member is baseline-covered and pre-log —
   present in the fork genesis's baseline and absent from every
   post-genesis entry — before replay runs.
3. **L6 u2** asserts the rewrite differs byte-wise from the original,
   remains self-consistent (well-formed under inspection), and genuinely
   omits the member from genesis, baseline, and chain alike.
4. **L4 u2** asserts both chains present the same child corpus subject
   and that the two fork geneses genuinely differ, before verification.
5. **L10 u9** asserts both roots are metadata-less before their restores;
   a root retaining bookkeeping makes the arm vacuous.
6. **The migration arms** (label 3) assert the fabricated bookkeeping's
   pre-lifecycle vintage — no binding, no initialization operation —
   at declaration time.
7. **Binding-mismatch fabrications** (labels 2, 6) assert exactly the one
   binding delta — host or path, stated — and no other edit.
8. **Count claims** in the results record quote pytest's summary line
   under `pipefail`, never a collect-only count.

## 6. Freeze obligations

Three, named before the plan exists: the **L10 u10 incompleteness** must
be constructed by omitting payload files the chain's surface names —
never by chain damage — so the never-`validated` claim is completeness's,
not malformation's; the **L6 u1 deletion** must interpose no other
mutation between the anchor and the deletion (the deletion is the only
delta); and the **label-8 writable-refusal arm** must construct its
granted root through `register_root`'s own path, never through fabricated
bookkeeping — the refusal must fire on real grant state.

## 7. Second reader

The charge, unchanged from cut 8 §7: verify every quoted row byte-exact
against its source table; audit each selection against §2's boundary;
check single-homing across rows and labeled declarations; test each
partiality against the any-unrun-arm rule; verify the §4 accounting by
independent recount; and read §3.2 adversarially. Findings and their
dispositions are recorded here before freeze.

### 7.1 The run and its dispositions

*The second reader has not yet run. This section is completed, and the
cut freezes, only after its findings are dispositioned.*

## 8. Limitations

1. **No persistence-cut harness** (fourth cut running): every
   kill-at-stage and durability-order interior defers to the atoms
   certification; this cut reads the resulting states.
2. **Holdings-read consequences defer**: L10's u8 and u10 certify
   lifecycle state and mutation refusals; unresolvable-for-holdings-reads
   and dereference-minting behavior wait on the holdings slice, named in
   their units.
3. **Intent qualification remains entirely out.** The lifecycle acts
   append no intents — the store-dereferencing holdings intents arrive
   with the holdings slice.
4. **The evaluator is certified over fabricated states** for
   engine-interior productions, bounded by the well-formedness
   obligation; the atoms suite is the standing mitigation.
5. **Migration provenance is attested, not proven** (spec §2): the cut
   certifies the refusals and the authorized path's mechanics, never that
   an operator's attestation is true.
6. **The cut inherits the spec's rulings and the L6 lift as dated**; a
   future design moving either extends by a successor cut, never by
   editing this one.
