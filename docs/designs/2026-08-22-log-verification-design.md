# Log verification and anchoring — design (world-index slice 3)

**Status:** Banked 2026-08-23, promoted here from
`docs/superpowers/specs/` at the discharge of conformance cut 8 (results:
`../plans/2026-08-22-conformance-cut-8-results.md`), with §5.3 and §7
amended first from the execution rulings — a promoted design must not bank
a claim the code contradicts. Implements the
Science half of the tamper-evident mutation log (ledger row 5): the ruled
registry log-head record, the exported head artifact, the explicit anchor
act, the §6 evaluator behind an audit act and a `ReplicaOf` arrival act,
the world genesis↔mirror agreement check, and the ordered-cuts predicate.
**Inherits:** `2026-08-03-tamper-evident-log-design.md` (the authority this
slice implements; cited below as *log design*); packaging §4/§5.1/§5.2;
`2026-08-20-world-registry-design.md` (the registry record grammar and the
identity-free corpus genesis ruling); `2026-08-20-world-index-slice-2-design.md`
(the epoch anchors, `read_chain`, and the callback seam);
`2026-08-10-verified-holdings-record-design.md` (store subjects and the
supplied-store-anchor route this slice's codecs must not exclude).
**Amended at banking, 2026-08-23** (all applied in the banking change): the
log design's §3/§5/§6 genesis-subject clauses and the affected L4/L10 arm
mechanisms (§1.2 here); its L6 pre-log-history arm's constructibility
(§1.3); the world-registry design's admission algorithm (`World.admit`'s
`ReplicaOf` refusal now precedes the known-id refusal, superseding cut 6's
X5 replica clause); ledger rows 4 and 5; kernel §8.7's status line (three
of the four recorded-mutation consequences closed at this slice's
discharge; G4 waits on the intent boundary).

## 1. Scope and the two dated amendments

### 1.1 In and out

**Built here (Science):** the registry log-head record and its codec; the
exported head artifact, its codec, and its locked producer
`export_head_artifact`; `anchor_heads` (the explicit anchor act); the one read-only log evaluator implementing the log design §6's
four-step precedence; `audit_log` (the audit boundary); `admit_arrival`
(the import boundary) plus `World.admit`'s `ReplicaOf` refusal; the
registered-surface projection and replay, with the replay policy pass; the
world genesis↔mirror agreement check (discharging the dated slice-1/2
deferral — reading was impossible then, `read_chain` exists now); and
`epochs_ordered`, the ordered-cuts predicate.

**Built here (atoms, behind its own design gate — §8):** `inspect_chain`,
the batch path-state capture command, and the shared post-recovery pending
gate.

**Deferred, each with an owner (§10):** intent qualification and G4's
closure (the intent-boundary slice); store-subject behavior, fork, replica,
and restore (row 4); the preimage-backed L13 classification (the atoms
blob-read seam, named in §10); event-level L8 (this design's own successor
work); verification-cost optimization (measurement-gated).

### 1.2 The genesis-subject amendment

The corpus genesis is deliberately identity-free: `science.corpus-root.v1`
is a constant payload and both Science root initializers register an empty
surface, so **every corpus chain has the byte-identical genesis entry and
the identical genesis digest** — every *currently constructible* non-fork
corpus chain, that is; a future fork genesis is the ruled exception. That
is a banked slice-1 ruling ("an adopted
identity binds through a later chain entry, never by rewriting genesis"),
and it is the authority; the log design's §3 `corpus(corpus_id,
forked_from?)` arm is amended rather than retrofitted. The amendment,
applied to the log design's §3/§5/§6 and the affected L4/L10 arms at
banking:

> Corpus anchor comparison is scoped by `(selected subject, genesis_digest)`,
> never genesis alone. Subject filtering happens first, then genesis and
> ancestry evaluation. Corpus genesis carries no child `corpus_id`; a future
> fork genesis may carry `forked_from`. The presented manifest is a separate
> policy check against the selected subject.

Consequences, restated per clause: corpus-chain **replacement** under the
constant genesis is caught by anchored-head unreachability (step 2's
ancestry rule), not genesis mismatch — same verdict, stated mechanism. The
genesis-mismatch refutation arm fires for world subjects and for future
fork geneses. **Subject mismatch is a lifecycle-boundary refusal even when
the chain verdict is `validated`**: a cooperatively logged `corpus.yaml`
identity rewrite replays consistently, so replay alone is not the guard.
The world subject keeps the genesis comparison as designed — its payload
carries `world_id`.

### 1.3 The empty-baseline amendment

Both initializers register `()` as the surface, so every existing genesis
baseline is empty. Genesis-form validation (§4.2) therefore **requires an
empty baseline; a non-empty baseline is malformed**. The log design's
pre-log-history arm (L6: register over a populated root, baseline brings it
into history) is presently unconstructible — no Science path mints a
populated baseline — and its anchor-free negative needs the same
populated-baseline start for the omission to be the baseline's claim, so
**L6 is wholly unread** by cut 8 (§9). Lifting the amendment is a future
registration-surface design act, not a test fixture's liberty.

## 2. The atoms seam — `inspect_chain`, capture, and the pending gate

Three APIs, four obligations (§8 adds the merge-and-disclosure duty), one
design document in the atoms repository, reviewed there before any Science
implementation task starts (§8, §11). Science consumes all three
through `science.root`-injected callbacks; `science.root` stays the only
module importing `atoms`.

### 2.1 `inspect_chain`

A public coordinator command that never raises on structural damage;
protocol misuse still raises, and `ChainStateInvalid` remains the refusal
of the write path's reads. Result is a closed union:

- **`WellFormedChain(genesis_digest, entries, tip, pending)`** — the
  linearized sequence over the already-public `Entry` union, plus
  `pending`: the registrations with no settlement, by transaction id and
  entry digest. In detached mode a staged, non-durable registration that
  links the tip joins `pending`; **detached pending digests need not occur
  in `entries`** — staged evidence errs toward refusal (ruled at the atoms
  gate, 2026-08-22).
- **`MalformedChain(defect)`** — **one deterministic defect**, the first in
  the validator's fixed traversal order, naming the offending digest or
  leaf. The taxonomy: foreign leaf; name/bytes mismatch; undecodable entry;
  zero or multiple genesis; missing predecessor; sibling branch; cycle;
  orphan history; settlement without ancestor registration; settlement /
  registration transaction-id mismatch; duplicate settlement; duplicate
  registration per transaction id; `fulfills` naming a missing,
  non-ancestor, or non-intent entry; duplicate committed fulfillment of one
  intent. The settlement and `fulfills` invariants live here because they
  are facts about atoms's own entry classes and linkage: atoms carries
  `fulfills`' *meaning* opaquely, but its referent's ancestry is chain
  structure.
- **`AbsentChain()`** — **no durable chain claim**: the chain directory
  absent, or present and empty with no contradictory live metadata (a live
  transaction record over an empty chain is the engine's own chain/store
  contradiction and keeps raising). The evaluator's absent-chain bypass is
  a typed input, never an exception, and arrival treats either absent form
  as chainless.

The fixed staging leaf is engine bookkeeping, **never a foreign-leaf
defect when it is a readable, no-follow regular staging file**, in both
modes; anything else occupying the reserved name is a foreign leaf (ruled
at the atoms gate, 2026-08-22).

**Two modes, explicit in the signature.** *Registered mode* serves a live
root, in the pinned order: acquire the project lock → structural inspection
→ a malformed chain **returns** `MalformedChain` (recovery never runs over
damage) → a well-formed chain runs recovery → inspect again and return.
This reorders the existing lease choreography, whose `resolve()` runs
before the lease yields; the atoms design gate owns the refactor, under one
typed validation core shared with the raising paths so the defect taxonomy
cannot fork. *Detached mode* serves an arriving root: a read-only directory
scan, no metadata required, no recovery, pending honestly unresolved. The
import boundary consumes detached mode; audit consumes registered mode.

### 2.2 The batch capture command

A public command over `(backend, root, paths)` returning atoms `PathState`s
for exactly the named paths — absence, file content, directory, symlink
target, and mode, the engine's own vocabulary. The private `_capture_path`
stays private: its signature leaks the audited backend and root descriptor.
This is what makes L12's "no second summary model" a mechanism: Science
never fingerprints a path with code of its own.

### 2.3 The shared pending gate

One post-recovery check, shared by `register_root`'s existing-chain arm,
`append_intent`, and `run_transaction`: an unsettled registration surviving
recovery refuses the command with `PendingUnresolved`. Today
`register_root` accepts a matching genesis over a traveled chain without
recapturing the populated surface, and the mutators never look — so the
log design §3's "further mutation refused" on a copied root has no
authority. After the gate, it has one, and L2's refusal arm and this
design's arrival refusal (§6.2) both cite it.

## 3. The log-head record, the head artifact, and the anchor act

### 3.1 The registry log-head record

Stored beside admission and status records under the registry's existing
grammar, discriminated by `record_kind: log-head`; content-named by its
digest under the minted domain **`science.log-head.v1`** over the canonical
projection of its payload. Payload, exactly the log design §5's ruled form:

```
subject:  corpus(corpus_id) | store(store_id)
genesis:  <genesis entry digest>
head:     <head entry digest>
origin:   build(epoch packaging identity) | anchor-act(actor)
```

The store arm is decodable and constructible in the codec, and nothing
this slice ships can reach it: the anchor act's corpus-only signature makes
a store unspellable there, and the evaluator's subject refusal (§4.1) is
the one place a store can be named at all. The content-named record
contract is final on arrival, and the holdings slice (row 4) fills in
behavior without changing an anchored record's form. A `world` subject is
not in the union at all: unconstructible, per the log design §5/L11.
Records are immutable and unordered; "maximal anchor" is computed by chain
ancestry, never record order.

**Idempotency is the rules-store discipline, verbatim:** under the world
lock, an existing record file with byte-identical content is skipped as
success and submits no transaction; a same-name file with different bytes
refuses as a collision, never an overwrite.

### 3.2 The exported head artifact

A standalone file under the minted domain **`science.head-artifact.v1`**,
canonical bytes via `science.identity.v1` encoding. Payload: `(subject:
corpus(corpus_id) | world(world_id) | store(store_id), genesis identity,
head digest)`. The world arm carries `world_id` because the id must survive
outside the chain; the store arm exists because the holdings authority
already admits a supplied exported head as a store anchor — **its writer is
row 4's**; this slice writes corpus and world artifacts only. *(Landed
2026-08-23: the root-lifecycle slice extended `export_head_artifact` to the
store subject under the same binding rule —
`2026-08-23-world-index-root-lifecycle-design.md` §5.)*

The producer is `export_head_artifact(world, subject)` — `subject:
Corpus(corpus_id) | World(world_id)` — which, under the world lock (and
the corpus's operation lock for a corpus subject), reads the chain tip
via `read_chain` and returns the canonical artifact bytes. **The subject
binds, never decorates:** a `World(world_id)` subject must agree with the
configuration and the genesis payload — a mismatch refuses, so `World(W2)`
can never be encoded over W1's chain — and a corpus subject resolves to
exactly one configured carrier under the anchor act's rule (§3.3),
refusing otherwise. No `actor` parameter: the ruled artifact has no member
to record one and the function writes nothing. Storing the bytes with an
external holder is the holder's job, never this function's: export *is*
the return of the value. Export of an epoch
copy or a head artifact to a holder outside the world root is what anchors
the world chain; no local act can (log design §5, L11).

### 3.3 The anchor act

`anchor_heads(world, corpus_ids, *, actor)` — under the world lock, for
each named corpus: resolve the corpus to **exactly one configured carrier
root** (an unknown `corpus_id` refuses `AnchorSubjectUnknown`; a known
corpus with no resolvable carrier, or more than one, refuses
`AnchorTargetUnresolvable` — resolution failure is never silent narrowing);
read the chain tip via the injected `read_chain` callback — chain
validation only, **no registered-surface scan**, no corpus-state identity;
then submit one WritePlan of `CreateOp`s for the new records under §3.1's
idempotency rule. **Terminal corpora may be anchored** — ruled here:
anchoring immediately before retirement or departure cleanup is a
legitimate, indeed archetypal, use of the act. Epoch builds keep writing
their head members as slice 2 built them, and the build's registry-record
half (origin `build`) joins the epoch publication plan.

## 4. The evaluator

### 4.1 Signature and report

One read-only function is the entire judgment surface — audit and arrival
both call it, and no third path evaluates (asserted by a labeled
declaration). Inputs: the **subject** `S` — `Corpus(corpus_id) |
World(world_id) | Store(store_id)`, the store arm refused with
`StoreSubjectUnsupported` (this union is the one API that can spell a
store, so the refusal lives here and only here; the anchor act's
corpus-only signature makes stores unspellable there and carries no such
error); the **inspection result** (§2.1's union); the **explicit observer
set**; disk access for replay (§5); and the optional typed `history`
input (§5.3). Nothing is searched for.

The observer set is a typed collection of three carrier arms:

- registry log-head records;
- epoch head members, each carrying a **provenance discriminator**:
  `named-local` (an epoch read from the world root under verification) or
  `supplied-export` (an exported copy in the caller's possession);
- head artifacts.

Every carrier must validate before evaluation — an epoch against its
packaging identity, an artifact by its codec, a record by its grammar; a
supplied carrier that fails refuses the act with `ObserverCarrierInvalid`,
never a silently narrowed set. Carrier eligibility per subject: a corpus
subject accepts all three arms with either provenance; the **world**
subject accepts only `supplied-export` epoch members and artifacts —
identical epoch bytes, different eligibility, which is exactly L11's point
— and a `world` subject on a registry record is unconstructible (§3.1).

Output: one frozen report — outcome `validated | refuted | unresolvable |
malformed`; `anchored_through` (the maximal anchored head); the
unanchored-tail extent; the pending set; the **intent inventory, marked
unevaluated** (the qualification deferral stated in the report itself);
the observer bound with per-carrier provenance; and findings. No error
doubles as an outcome; no outcome doubles as an error.

### 4.2 Precedence

Exactly four steps, so no state earns two outcomes:

1. **Structure.** `MalformedChain` → **malformed**, stop, the defect named.
   `AbsentChain` → skip to step 2. For a present well-formed chain,
   **genesis-form validation runs now, before anchors**: the genesis
   payload must decode under the Science form for `S`'s kind
   (`science.corpus-root.v1` constant; `science.world-root.v1` with
   `world_id`) and the baseline must be empty (§1.3) — an undecodable or
   wrong-form payload or a non-empty baseline → **malformed**. A valid
   world genesis naming a **different** `world_id` is the separate
   subject-mismatch case (§6.3), never malformed.
2. **Anchors.** Filter the accepted carriers by `S` first — the sole
   filter; the presented manifest or configuration never admits or
   discards an anchor. Then, per `S`-bound anchor: chain wholly absent →
   **refuted** (removal); anchor genesis ≠ chain genesis → **refuted**
   (replacement — world subjects and future fork geneses; §1.2);
   anchored head unreachable by chain ancestry, or two anchors mutually
   incomparable → **refuted**; a reachable old anchor never hides a
   missing newer one. All reachable → continue. Empty `S`-bound set →
   **unresolvable**, replay not reached, reported as
   unanchored-from-genesis where the chain is genuinely fresh.
3. **Pending.** Registered-mode inspection has already run recovery, so a
   surviving pending registration is evidence-starved by construction; in
   either mode, any pending at this step → **unresolvable**, replay not
   reached, never inferred from disk.
4. **Replay** (§5). Any disagreement → **refuted**. Otherwise
   **validated**, with L5's unanchored-tail residue stated in the report.

## 5. Replay and the one projection

### 5.1 The registered-surface projection

One Science function, instantiated per root kind — the log design §3's
"one projection, used three times":

- **corpus:** every claimed node-layout path plus `corpus.yaml`, excluding
  `.nodes-index`, the reserved log path, and engine bookkeeping;
- **world root:** the exact registry, epoch, and rules-store grammars plus
  `world.yaml`, with the same exclusions.

Enumeration never follows symlinks. States cover the full atoms
vocabulary — files, directories, symlink targets, modes — captured through
§2.2's public command, never a Science reimplementation.

### 5.2 Replay

From the genesis baseline, in chain order, over **committed**
registrations only: verify each entry's initial fingerprints against the
accumulated surface, apply its finals; a rolled-back registration is no
transition. Refuted on any initial-state disagreement, and on any
disagreement **in either direction** between the accumulated surface at
the local head and the scanned disk surface. The comparison runs over the
**union** of replay-known paths and disk-discovered claimed paths, an
unknown replay state reading as `ABSENT` — a path the timeline never
produced is a disagreement, which is how a raw-created in-surface record
is caught.

### 5.3 The policy pass

Logged is not permitted (log design §8). During replay, every committed
transition that removes a claimed record path emits a **removal finding**
naming the path and the removing transaction. Classifying the removed
record — a *verification*, and a *failing* one — resolves only through
**supplied historical bytes** in this slice: the evaluator and both
boundaries accept a typed optional input, `history: Mapping[content-hash,
bytes]`, whose keys are atoms's exact content-hash form —
`sha256:<64 lowercase hex>`. A malformed key, or a key whose bytes do not
hash to it, **refuses the act** — corrupt evidence is never silently
ignored. A held copy resolves by **the path its own identity claims**, and
every classified finding **names the digest the copy was filed under**; two
copies claiming one path resolve nothing. The
preimage-store resolver is a named atoms seam (§10) and until it
exists the classification without a held copy is honestly absent, exactly
as L13's own arm words it. That L13 arm is **partial, stated** — and
partial for **two** reasons, not one.

> **Amended 2026-08-23 (execution ruling R16).** This clause first read
> "a held copy resolves iff its digest matches the recorded state". That is
> not implementable through the frozen §2 seam: a chain entry retains a
> path *state*, states are opaque above the composition root, and `LogSeam`
> exposes no state→digest accessor — checked against the seam's surface,
> not assumed. The landed pass decodes the held bytes, derives the corpus
> path the copy's identity claims, matches the removed path, and names the
> digest the copy was filed under. **This is a second, distinct partiality
> of L13**, beyond §10.4's resolver deferral: the deferral says the
> classification is absent when no copy is held; this says the *match
> predicate itself* is weakened when one is. A single held copy of a
> different version of the same record can misclassify a removal in either
> direction, so every finding message is scoped to what the evidence
> supports — it speaks about the held copy, never about the removed bytes.
> Stating both reasons wherever the first is stated is part of the
> amendment. The digest match returns with the preimage resolver.

## 6. The two boundaries and the mismatch rule

### 6.1 Audit

`audit_log(config, subject, target_root, observer_set, *, actor,
history=None)` — the evaluator plus a report and **nothing else**:
verification mints nothing, and the operation-intent obligation on the
audit wrapper is deferred, dated, with the intent consumers. The act takes
the **world configuration/context**, not an opened `World` (it needs the
configured root set and any `named-local` epochs, and the **world audit
must remain callable when ordinary `open_world` refuses** a
genesis/configuration mismatch — auditing a broken world is the point),
and an **explicit target root**: for a corpus subject, the root under
audit, which must be one of the configured corpus roots and is **never
associated to `S` by reading its manifest** — the configuration holds an
unassociated root tuple and ordinary resolution associates by manifest,
so a manifest-based lookup could not locate the root whose `corpus.yaml`
was rewritten to another id, which is the exact mismatch the audit must
report. For a world subject the target is the configured world root.
The act holds the subject's operation lock across inspection and surface
capture — for a corpus through a **lock-only lookup** (splitting lock
acquisition out of `_root_state_for`, which today constructs and parses a
full `Corpus`; audit must remain possible over damaged node bytes), for
the world root under the world lock — so the verdict and the surface it
judged are one view.

### 6.2 Arrival

`World.admit` refuses `ReplicaOf` provenance with
**`ReplicaAdmissionRequiresVerification`** — a distinct error, since bare
`admit` holds no verdict to report. The verified route is:

`admit_arrival(world, corpus_root, provenance: ReplicaOf, observer_set, *,
actor, history=None)` — the manifest is **loaded internally** under the
arriving root's lock, never supplied (a supplied manifest could disagree
with the bytes the lock protects), and the verification subject is
selected from the provenance: `S = Corpus(provenance.parent_corpus_id)` —
the traveled chain is the parent's chain, and its anchors bind by the
parent's id. The act holds that lock across manifest reading, detached
inspection, surface capture, and the admission transaction, in the
existing world→corpus lock order, so the admitted bytes cannot change
after their verdict; it commits through **one shared admission core** with
`World.admit`, never a second registration path. Outcomes:

- **refuted / malformed** → `ArrivalRefused`, carrying the **complete
  report** plus a closed cause (`refuted | malformed | chainless |
  pending`), the remedy named.
- **unresolvable, empty observer set** → admissible **only** for a
  `WellFormedChain` with **zero pending**: an arrival at a fresh world
  must be possible, and the unanchored bound is recorded. `AbsentChain`
  with empty observers is **refused** (`chainless`): a `ReplicaOf` that
  did not carry its chain is not an unanchored arrival.
- **unresolvable, pending** → `ArrivalRefused` (`pending`) — a dated
  narrowing of the log design §3's "adopt but refuse further mutation":
  the registry's status vocabulary is monotone (`retired | departed`,
  nothing liftable), and §2.3's engine gate is the standing write-refusal
  authority. Remedy: settlement evidence from the origin, or recopy.
- **validated** → admission proceeds. `admit_arrival` returns the
  `AdmissionRecord` and the verification report **side by side**; the
  observer bound is never discarded and never enters admission identity —
  admission identity is not amended by this design.

The refusal cause derives from the **report's fields**, not from which
precedence step produced the outcome: a pending chain with an empty
observer set is `unresolvable` at step 2 (unanchored), but its nonempty
pending set still refuses arrival with cause `pending` — the causes rank
`malformed` > `refuted` > `pending` > `chainless`, and admissibility
requires none of them.

### 6.3 Subject mismatch and the world mirror

A loaded manifest whose `corpus_id` differs from the selected `S` is a
**lifecycle-boundary refusal** (`SubjectMismatch`) at arrival, even when
the chain verdict is `validated` (§1.2); at audit it is a finding, and it
never filters anchors. The refusal mechanics, pinned: at arrival, the
**report-based refusals outrank `SubjectMismatch`** — a chain that is
malformed, refuted, pending, or chainless refuses on that cause first —
and `SubjectMismatch` is then checked **before** the admission transaction,
so no mismatched subject is ever admitted. The **world genesis↔mirror
agreement check** discharges the dated slice-1/2 deferral, split across
the two surfaces by the detection/refusal rule: **ordinary `open_world`
checks genesis/configuration/mirror agreement and refuses** on a mismatch
(the log design §3's lifecycle refusal, now enforced at the surface every
consumer crosses), while the **world audit reports it** as the
subject-mismatch finding — the audit must stay usable on exactly the
worlds `open_world` refuses (§6.1). The genesis payload's `world_id` is
read through `read_chain` in both.

### 6.4 Engine refusals at the boundaries

Three engine states escape the never-raises envelope by design: a
chain-vs-record contradiction that `resolve` raises (`ChainStateInvalid` —
not a chain-structural fact, so it gets no taxonomy row); a halted
transaction (`TransactionHalted`); and a capture refusal on an
unrepresentable entry at a modeled path (`PreconditionRefused`). The
boundary contract for all three, ruled at the atoms gate (2026-08-22):
the **root-owned seam adapters translate exactly those exceptions** into
one Science error,

```
LogEvidenceRefused(phase: "inspect" | "capture",
                   engine_error: "ChainStateInvalid" | "TransactionHalted"
                                 | "PreconditionRefused",
                   detail: str)
```

preserving the original as `__cause__`. It produces **no `LogReport`**, is
**not** `ArrivalRefused`, and sits **outside** the evaluator's precedence
and the arrival-cause ranking — the act refused to judge, it did not
judge. `ProtocolError` and unrelated setup errors keep their existing
contracts untranslated. Audit and arrival both carry tests for the
translation.

## 7. The ordered-cuts predicate

`epochs_ordered(config, e1, e2)` → `ordered | unordered`, over already
validated epochs and world chain: locate E1's **committed** publication
registration and its settlement in the world chain; E2 orders after E1
**iff** E2's build-start world head descends from that settlement by
ancestry. A missing or rolled-back E1 publication → `unordered`. Epoch
sequence numbers are read by nothing. This is the log design §7's
predicate **only** — the event-level relation (presence/exclusion
reasoning across both captured corpus heads) is deferred, and L8 is
**partial**.

> **Amended 2026-08-23 (execution ruling R33).** The signature first read
> `epochs_ordered(world, e1, e2)`. The predicate takes the world
> **configuration**, for the audit act's own reason (§6.1): it must answer
> on exactly the worlds `open_world` refuses, and `open_world` now reads
> the chain (§6.3). Three further rules landed in the docstring rather than
> as fallbacks: the descent **includes** the settlement entry, since a
> publication linearizes registration → settlement and the tip at the
> instant E1 commits *is* the settlement (R29); the publication moment is
> the **earliest committed** settlement of the registration creating
> `epochs/<e1>/anchors.yaml` (R30); and an absent or malformed world chain
> answers `unordered`, caller-input facts still refusing `EpochUnknown`
> (R31).

## 8. The atoms design gate

One design document in the atoms repository, its own review before any
Science implementation task — the `read_chain` choreography exactly. Its
obligations: §2.1's `inspect_chain` (both modes, the pinned registered
order, the staging-leaf ruling, one typed validation core under both the
inspecting and raising paths); §2.2's batch capture command; §2.3's shared
pending gate with `PendingUnresolved`; and the merge joining row 4's
recorded unpushed disclosure — pushing remains a prerequisite of any
integration expecting a fresh checkout to build.

## 9. Cut 8 — expected dispositions

Selected from the log design's L table; verbatim splicing and the
any-unrun-arm rule apply as in cuts 5–7. Expected shape, to be fixed at
the cut's own freeze — **the cut is now frozen and its own §3/§4 are the
authority; the two places this expectation was refined are noted below**:

- **In:** L3, L5, L9, L11, L12.
- **Partial:** L1 (the pending-gate and refusal arms here; the
  executor-interior kill arms are A7's, certified in atoms); L2
  (copied-root, rollback-absence, raw-delete, and duplicate-settlement
  arms in; the live-root recovery-settlement arm needs a persistence-cut
  harness Science does not have — the cut-7 X2 gap, named, not argued
  around); L4 (store arm and distinct-fork-genesis arm unrun; the amended
  corpus arms in); L8 (§7's predicate only); L10 (the arrival-identity arm
  in, under §1.2/§6.2's mechanism — `admit_arrival` refuses a fresh
  manifest over the parent's chain with `SubjectMismatch`; fork, replica,
  restore, and store arms deferred to row 4); L13 (removal findings in;
  failing-classification conditional on supplied bytes; preimage resolver
  deferred).
- **Deferred / unread:** L6 — both arms fail construction under §1.3:
  the pre-log arm needs a populated baseline no Science path mints and
  genesis-form validation rejects, and the anchor-free negative needs the
  same populated-baseline start for the omission to be the baseline's
  claim, collapsing otherwise into L5's homed residue; L7's remainder (its
  structural half is selected as chain-structural inspection arms;
  qualification with the intent boundary).

> **Refinements at the freeze, recorded 2026-08-23.** Two. **L7 is
> partial**, not deferred: its two chain-structural units are selected
> because they are `inspect_chain` taxonomy entries with no other
> certifying home, and the cut records that refinement in its own §3.1.
> **L4's different-genesis unit was replaced** — a fabricated distinct
> corpus genesis contradicts §4.2's genesis-form validation, so the
> same-genesis alternative-chain unit refuted through ancestry stands in
> its place, and the distinct-genesis variant defers with L10's fork arms.
> The cut's §7.1 records these and three other second-reader dispositions.
> Two of the 53 declared units are themselves **partial** at discharge —
> L7u1 (the non-ancestor `fulfills` spelling is directory-unconstructible)
> and L2u5 (`register_root`'s existing-chain arm has no Science mapping) —
> giving 51 full + 2 partial; the results record's §1.1 states both.

## 10. Limitations and the deferral ledger

1. **Intent qualification is unevaluated**, stated in every report; L7 and
   G4's closure wait on the intent-boundary slice.
2. **Store subjects are shape-only**: codecs closed and complete; the
   anchor act's signature makes a store unspellable and the evaluator
   refuses the one place it can be named; behavior and the store-artifact
   writer are row 4's. *(Closed 2026-08-23 — the root-lifecycle slice
   spelled the store subject through `anchor_heads`, the evaluator, and
   `export_head_artifact` under the genesis-binding rule; cut 9's V-labeled
   store units are the successor certification of cut 8's retired label 6:
   `2026-08-23-world-index-root-lifecycle-design.md` §5, results at
   `../plans/2026-08-23-conformance-cut-9-results.md`.)*
3. **Fork, replica, restore are unbuilt**; the distinct-fork-genesis
   refutation arm and L10's fork, replica-construction, restore, and
   store arms wait on row 4 — the arrival-identity arm is read by cut 8.
   *(Closed 2026-08-23 — `replicate_root`, `restore_root`, `fork_corpus`,
   and `fork_store` landed with the root-lifecycle slice on the atoms
   lifecycle commands, and cut 9 read L10's fork, replica, restore, and
   store arms plus the distinct-fork-genesis refutation:
   `2026-08-23-world-index-root-lifecycle-design.md` §6–§7.)*
4. **The L13 resolver is a named seam, not an orphan:** the public
   preimage/blob-read command joins the atoms obligation ledger at
   banking, and its Science consumption is recorded as row 5's named
   remainder. Row 5 stays **partial** while it and intent qualification
   are outstanding.
5. **The refuse-don't-arrest narrowing** (§6.2) is dated against the log
   design §3's letter.
6. **The empty-baseline amendment** (§1.3) leaves L6 wholly unread —
   the pre-log arm unconstructible and the anchor-free negative vacuous —
   until a registration-surface design act lifts it. *(Lifted 2026-08-23 —
   the root-lifecycle slice's fork-baseline rule populates the baseline
   for fork-form genesis exactly, `registered_surface_paths` projects the
   registered store namespace, and cut 9's L6 units read both arms:
   `2026-08-23-world-index-root-lifecycle-design.md` §5.)*
7. **Event-level cross-chain order** is deferred; §7's predicate is the
   whole of L8 built here.
8. **Verification cost** is measurement-gated; no Merkle overlay is built
   speculatively (log design §12).
9. **The holder protocol** remains open (log design §12); nothing here
   learns which exported anchors survive.

At this slice's discharge, **three of kernel §8.7's four recorded-mutation
consequences close** — G8, semantic identity, and 5a's standing
subtraction, all replay-witnessed; G4's closure waits on the intent
boundary, and chronology's strengthening stays boundary-mediated-only as
banked.

## 11. Choreography

1. This spec's review closes.
2. Conformance cut 8: authored, second-read, and **frozen before any
   implementation** (verbatim L-row splicing; the freeze discipline of
   cuts 5–7).
3. The implementation plan is written against the frozen cut.
4. Atoms design gate (§8), as the plan's opening tasks: design doc in the
   atoms repository → review → implement → merge on local atoms `main`,
   the new head joining row 4's recorded unpushed disclosure, pushing
   remaining a prerequisite of any fresh-checkout integration.
5. Science implementation against the merged seam.
6. Certified acceptance, results record, and banking: this document
   promotes to `docs/designs/`, the log design's amendments land (§1.2,
   §1.3), ledger rows 4 and 5 and kernel §8.7's status line are corrected
   in the same change, and the stale-claim grep runs over the user-facing
   docs.

**All six steps completed 2026-08-23** on branch `design/log-verification`,
merged to `main` the same day with `--no-ff` (integration commit `10cc84b`);
the atoms head `3aa5a76` was pushed to the `atoms` remote the same day,
closing §8's fresh-checkout prerequisite. The forty-four
execution rulings are in
`../plans/2026-08-22-log-verification-ledger.md`; the discharge is
`../plans/2026-08-22-conformance-cut-8-results.md`.
