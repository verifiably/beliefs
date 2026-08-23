# Tamper-evident mutation log — design

**Status:** Banked 2026-08-03, after eleven review rounds; the banking commit
applies the amendment set below across kernel, comp, repro, packaging, the
`atoms` design (its repo), and the ledger. Closes ledger artifact 5 at the design
level. `atoms` A7 landed the engine half on 2026-08-14 and A8 landed durability
certification on 2026-08-17.
**Science's half landed 2026-08-23** as world-index slice 3
(`2026-08-22-log-verification-design.md`), discharging conformance cut 8
(`2026-08-22-conformance-cut-8.md`; results at
`../plans/2026-08-22-conformance-cut-8-results.md`) on branch
`design/log-verification`, whose `--no-ff` merge is the one remaining act.
What that closes, exactly: the **detectability** of three of kernel §8.7's
four recorded-mutation consequences — deleting a failing verification (G8),
hand-editing a proposition's semantic fields with its stored hash, and
deleting a retraction record (5a's standing subtraction) — each now a
registered-surface removal or rewrite that replay refutes against a
surviving anchor, with the removal itself named in a policy finding. **G4
does not close**: discarding a failed replay attempt is an
intent-qualification question, and qualification is unevaluated in every
report this slice produces. Chronology's strengthening stays
boundary-mediated, as banked; G2a/R12's out-of-band negative and packaging
limitation 2 stand unchanged, and the derived-answer negatives of G4 and G8
(a deleted record stops invalidating) are a separate fact this design never
claimed to change. §10's rows carry their own dispositions: L3, L5, L9, L11
and L12 read in full, L1/L2/L4/L7/L8/L10/L13 in part, and **L6 not at all**
(see its row).
**Inherits:** kernel §8.7 (the contract — pre-mutation durable registration
**and** detectable removal, stricter than crash recovery — and its five
consequences); repro §9 and its 2026-08-03 amendment (the shared facility, one
capability with five consumers; anchor placement before any registration API;
`register_run_intent` as this facility's consumer, not the facility); packaging
§4 (the reserved log-head records), §12 (shape, cadence, and write-through cost
left to this design), and limitation 1 (the unanchored registry); `atoms` §15
(future obligation: terminal records and preimage blobs as natural witnesses,
consumer tag + frozen-intent digest already persisted, preimage GC as explicit
consumer policy); 5a limitation 1 (deleting a correction silently restores
standing — the fifth consequence, stated on arrival).
**Constraints:** the guarantee tables extend, never renumber: this design
adds its own table (**L**) and, where a banked rule must change (kernel G2a,
comp §3.3/R12, packaging §5/§5.1/§5.2/X9), amends in place under the retained
identifier. Nothing here re-states closure of §8.7, and the
claim is four-of-five: at implementation, with L1–L13 passing, the log closes
the **four recorded-mutation consequences** (G4, G8, semantic identity, 5a's
standing subtraction) and **strengthens chronology for boundary-mediated
executions only** — G2a/R12's out-of-band chronology negative remains
(limitation 5). None of it closes when this document banks. No interim logger
is designed: registration exists exactly where the `atoms` executor runs.
*(Amended 2026-08-23: at the actual implementation the claim realized is
**three**-of-five, not four. G4's closure was conditioned on the whole of
L1–L13 passing, and intent qualification — L7's reduction — is not built
here; it waits on the intent-boundary slice. The other three closed as
stated. The four-of-five figure remains the design's claim for the
completed capability, not a claim about the tree.)*

**Banking amendment set** (to apply across the corpus in the banking commit):
kernel §8.7 gains "designed 2026-08-03 (`2026-08-03-tamper-evident-log-design.md`);
the four recorded-mutation consequences close at implementation, and the
G2a-ordering row strengthens for **boundary-mediated** executions only —
out-of-band chronology remains open (its limitation 5)"; kernel **G2a**'s
"the strong claim needs the §9 mutation log" narrows the same way, keeping its
out-of-band negative; comp **§3.3**'s bound and **R12** gain the same
boundary-mediated qualification wherever they defer the strong chronology
claim to this log; repro §9's amendment gains the same pointer and the
note that `register_run_intent` is superseded by the intent entry correlated by
`event_token` (§3 here); packaging is amended in eight places — §3's fixed
world-root layout gains the world chain's reserved log path **and the
configuration contract gains the `world_id` field with its lifecycle** —
fresh initialization mints it, replica/restore and cold bootstrap over an
existing chain preserve the genesis `world_id`, and a configuration/genesis
mismatch refuses rather than silently re-minting (§3 here), §4's "(reserved)"
log-head bullet becomes a ruled record type (shape and cadence per §5 here),
§5's exact epoch inventory gains the head members, §5.1's build contract gains
coherent head capture (each corpus head under that corpus's lock hold; the
build-start world head under the world root's own write lock), §5.2 classifies
heads as packaging members — never semantic identities, never belief inputs —
and X9 extends to head/state coherence (the captured head and the receipts'
corpus-state identity describe one view); packaging §12's log-head open
question closes and limitation 1 points here; `atoms` §15 (in the `atoms`
repo) gains the enumerated engine obligations of §9 here. The ledger's
artifact-5 row advances to design-banked.

## 1. Why, and what "detectable" quantifies over

Kernel §8.7 is the one architectural limitation every belief-bearing guarantee
leans on: everything the kernel promises holds only over what remains
*recorded*. Its contract is stricter than crash recovery — a recovery journal
that can itself be deleted closes nothing — and it names five consequences of
the one missing capability: a discarded failed replay (G4), a deleted failing
verification (G8), a coordinated fields-plus-hash edit (semantic identity), a
spec frozen after an out-of-band execution (§3.3), and a deleted retraction
silently restoring standing (5a). Repro §9 sized the facility: a **general
tamper-evident mutation log** — every mutation durably registered **before** it
is applied, in a sequence whose **removal is detectable** — and warned by name
against sizing it as a run registry, which would close one consequence while
believing it had closed five.

**Detection is quantified over surviving observers.** A hash chain makes
history append-only *relative to a head someone else holds*. Anyone holding a
later anchored head — the registry, a published epoch, a replica, an archived
export — can refute truncation at import or audit. Nobody holding anything can
detect the destruction of a world and every observer of it. This design states
that bound in §11 rather than papering over it, and it distinguishes the two
anchor classes precisely (§5): what anchors a corpus chain lives outside the
corpus but inside the world root; what anchors the **world** chain lives only
outside the world root entirely.

**A `refuted` outcome is a completeness verdict, not a malice verdict.** It
means "this chain is not a complete history against these anchors." An honest
restore from an old backup and a deliberate truncation are observationally
identical; classification tells them apart by evidence never, by provenance
sometimes, and the finding says which question it answered.

## 2. Framing rulings

1. **Registration is an engine facility.** The `atoms` executor writes the log
   inside its transaction path; the only cooperative write path to a registered
   root *is* the executor, so no science-layer code can mutate a registered
   root without producing an entry. Raw writes remain raw — §6 states what the
   log does and does not catch there.
2. **The chain travels with the root; its anchors survive it.** Each engine
   root carries its chain at a reserved path (the second consumer of `nodes`'
   reserved-path contract, after `corpus.yaml`), so copy, sync, and restore
   carry a corpus's mutation history with the corpus. Anchors live outside the
   chain's own deletable set: registry log-head records and epoch head members
   for corpus chains; **exported** epochs or head artifacts — held by a
   replica, archive, or consumer outside the world root — for the world chain.
   An epoch stored only inside the world root is not an external observer of
   that root.
3. **Anchor cadence is the epoch build plus an explicit anchor act** — never
   per-transaction write-through. Corpus writes never touch the world root;
   the unanchored tail is bounded by anchor cadence, the same temporal shape
   as the index's staleness contract (packaging §5.4, 5a limitation 6), one
   story rather than two.
4. **The log is append-only forever and carries digests, never bytes.**
   Entries hold typed state fingerprints; `atoms`' preimage blobs hold bytes,
   and their GC stays explicit consumer policy (`atoms` §7.5, §15) —
   collecting blobs shrinks forensic depth, never detection.
5. **No interim logger.** Pre-adoption writes are covered by the existing
   stated limitations, which this design closes on arrival rather than
   shimming. The clean-start implementation adopts `atoms` at the composition
   root from day one, so the first cooperative write of the new system is a
   logged write.

## 3. The chain

One chain per engine root: every corpus, the world root itself, and a managed
payload store — so registry appends and epoch publications are logged
mutations, which is what closes packaging limitation 1 when the
implementation lands *(amended 2026-08-10, the verified-holdings record
design §8)*. One content-named
file per entry; **order comes from linkage, never from filenames** (the
registry's own no-ordering rule): each entry's identity is the digest over
`(previous-entry digest | genesis, entry class, payload)`. The entry set of a
root is **one genesis-connected linear sequence**: every entry reachable from
the genesis, **at most one successor per entry, exactly one tip**. A sibling
branch or an orphan file is malformed (§6), never a silently ignored fork —
"latest entry" is well-defined by exactly this invariant, and tail
replacement remains L5's residue.

**Genesis** is minted at root registration, as a discriminated union:

- `corpus(corpus_id, forked_from?)` — `forked_from`, present iff the root was
  created by a fork act, names the **parent genesis identity and the parent
  head digest at the fork**, paralleling the manifest's `forked_from` (packaging
  §6). A **fork mints a new genesis**: parent and fork are separate chains with
  separate anchors, never one chain with incomparable heads. A **replica or
  restore carries the chain unchanged** — same genesis, same comparability.
- `world(world_id)` — the world id minted fresh at world-root
  initialization, parallel to `corpus_id` minting, and recorded in
  installation configuration. Replica, restore, and cold bootstrap over an
  existing chain **preserve** the genesis `world_id`; a
  configuration/genesis mismatch **refuses** rather than silently
  re-minting.
- `store(store_id, forked_from?)` — the store id minted at store
  initialization, carried in the store's genesis record. Replica and
  restore **preserve** the genesis `store_id` verbatim; a
  configuration/genesis mismatch **refuses** rather than silently
  re-minting, exactly as `world(world_id)` does. `forked_from` is present
  **iff** a writable copy was minted by the fork act: a replica is a
  read-only carrier, never a writable twin, so a writable fork is always a
  new genesis — the corpus-fork precedent applied to stores (the
  verified-holdings record design §2) *(amended 2026-08-10, the
  verified-holdings record design §8)*.

*(Amended 2026-08-23, the log-verification design §1.2 — the genesis-subject
amendment.)* The corpus arm's **`corpus_id` is not carried in the genesis
payload**. `science.corpus-root.v1` is a constant payload and both Science
root initializers register an empty surface, so **every currently
constructible non-fork corpus chain has the byte-identical genesis entry and
the identical genesis digest**; a future fork genesis is the ruled exception
and may carry `forked_from`. This is the banked slice-1 ruling — an adopted
identity binds through a later chain entry, never by rewriting genesis — and
it is the authority, so this arm is amended rather than retrofitted. The
consequence for §5 and §6: **corpus anchor comparison is scoped by
`(selected subject, genesis_digest)`, never genesis alone**. Subject
filtering happens first, then genesis and ancestry evaluation, and the
presented manifest is a separate policy check against the selected subject.
The `world` and `store` arms are unaffected — their payloads carry
`world_id` and `store_id`.

All three arms commit a **baseline**: the sorted typed path/state fingerprints of
the root's **registered surface** at registration. The baseline is what brings a
pre-log surface into history — the registry deliberately arrives before this
log (packaging limitation 1), and without a committed baseline, deleting an
admission record or a verification that predates log activation would remain
invisible forever. Refusing nonempty adoption would have been simpler and
cannot handle the already-populated world root.

*(Amended 2026-08-23, the log-verification design §1.3 — the empty-baseline
amendment.)* Both Science initializers register `()` as the surface, so
**every genesis baseline that exists is empty**, and genesis-form validation
therefore **requires an empty baseline: a non-empty baseline is malformed**,
classified at step 1 before any anchor judgment. The paragraph above states
what a populated baseline would be *for*; no Science path mints one today.
The consequence for the guarantee table is L6's, recorded in its own row:
both of that row's arms are presently unconstructible, and conformance cut 8
reads the row not at all. Lifting this is a future registration-surface
design act, not a test fixture's liberty.

**The registered surface is one projection, used three times.** A root's
registered surface is every path its declared layout claims — node records and
declared reserved files (`corpus.yaml`; for the world root: the registry,
epochs, and rules store) — **excluding engine bookkeeping**: the reserved log
path and the engine's own metadata. The genesis baseline fingerprints this
projection, every transaction's initial/final fingerprints are stated over it,
and §6's replay compares its accumulated state against exactly it — one
projection, never three ad-hoc ones, so the log can neither refute itself over
its own appends nor be blind to what it claims to witness. A **raw-created
record at a claimed layout path is inside the surface**: replay refutes a disk
surface carrying a path the timeline never produced, which is the detection
R19's negative (e) and substrate §4.3 defer to this design. An undeclared
foreign path is outside the surface and outside this design (limitation 3) —
a walk-hazard and validation question, not history. For a **managed payload
store**, the projection instantiates the same rule: every path in the
store's payload namespace, excluding engine bookkeeping — the reserved log
path and the engine's own metadata — **never** "the paths acts happen to
mutate," which no registration-time baseline could state. A raw-created
payload file is **inside** the surface under this projection, exactly as a
raw-created record is, and replay refutes it *(amended 2026-08-10, the
verified-holdings record design §8)*.

**Three entry classes:**

- **`registered`** — engine-written, made durable **before** the transaction
  applies, and **durably bound to its transaction in both directions**, in the
  pinned order: durable `PREPARED` record → durable `registered` entry
  carrying the **transaction id** → transaction record durably storing that
  entry's digest → first apply. Recovery correlates entry and transaction
  exactly — never by guessing among identical intents — and is **idempotent
  by transaction id**: a crash between entry durability and the digest store
  appends no second registration, and at most one `registered` entry per
  transaction id is structural (§6). Payload: the
  transaction id, the transaction's frozen-intent digest and consumer tag
  (both already persisted by the spec, `atoms` §5.1), the complete typed
  initial/final path-state fingerprints of the registered surface the frozen
  transaction touches — `atoms`' own state vocabulary, covering absence,
  directory state, symlink targets, and modes; **no second summary model** —
  and an optional `fulfills` member naming an intent entry digest (below).
- **`settled(committed | rolled-back)`** — engine-written, and a
  **completion barrier**, in the pinned order: durable terminal decision →
  durable settlement append (referencing the `registered` entry's digest and
  its transaction id, which must match) → transaction record durably binding
  the settlement digest — **that binding is the acknowledgement** → consumer
  **terminal-outcome** return and lease release → terminal-record GC. Both
  arms sit behind the barrier: a normally completed **and** a normally
  rolled-back transaction are settled **before** the consumer learns
  of the outcome: the copy-before-settlement window exists only around a
  crash.
  The append is **idempotent by transaction id**, recovery backfills a
  missing binding from the unique settlement, and **exactly one settlement
  per registration** is a structural invariant (§6). A `registered` entry
  with no settlement is **pending**, and pending participates in no absence
  test. Only `committed` transitions enter the replay of §6.
- **`intent`** — consumer-authored acts with no mutation behind them. Two
  consumers are named today. The **assessment-run intent** —
  `dataset-production` recipes carry no `spec_identity` to name (comp §4.2),
  and neither G4 nor §3.3 concerns them — is written by the execution
  boundary **before** execution starts, under a barrier and in one chosen
  place. The boundary **freezes the destination corpus first** — operational
  placement, never
  run identity — then: acquire that root's existing `atoms` lease → durably
  append the intent and advance the chain → return the intent digest and
  release → only then start execution. The run's publication is required
  through that **same root**, which is what keeps `fulfills`' ancestor rule
  satisfiable: a cross-root publication is **refused**, and placement cannot
  be selected after observing results. Payload: spec identity, the
  boundary-minted **`event_token`** (repro §4.2 — reused, not a second
  attempt id), and the actor. The run's
  publishing transaction correlates by carrying the intent entry digest in
  `fulfills`. An intent is **unmatched** only under §6's reduction — no
  pointers at all, or every pointer fully resolved and non-qualifying;
  unresolved evidence proves nothing — and an unmatched intent proves
  exactly "**a boundary-mediated attempt with no recorded outcome**" — crash,
  cancellation, and discarded failure are indistinguishable, and the claim is
  stated at that width. That is still what closes G4's invisibility: once the
  head is anchored, the attempt cannot be silently discarded. A **qualifying
  fulfillment** is a committed **run-publication** registration whose
  published run matches the intent's spec identity and `event_token` —
  pointer ancestry alone proves nothing, since any committed transaction
  could carry `fulfills`. The **boundary constructs the link from its own
  intent** — no caller-selected `fulfills` argument exists — and `atoms`
  carries it opaquely; whatever pointers point at an intent, matching runs
  only through §6's reduction — a non-qualifying pointer never matches, and
  an unreadable one leaves qualification unresolved rather than unmatched.

  The **holdings intent** is appended by every store-dereferencing act —
  mutating or re-check — before it acts (the verified-holdings record design
  §3); payload: canonical location, act kind, the boundary-minted
  `event_token` — reused, never a second attempt id — and the actor
  *(amended 2026-08-10, the verified-holdings record design §8)*.

  The **operation intent** is the union's third consumer — one per boundary
  operation (the act-report design §3): `acquisition`, `audit`, `import`,
  `re-check`, or `run-attempt` for a `dataset-production` run, which carries
  no `spec_identity` and is therefore outside the assessment-run intent.
  Payload: the operation kind, the boundary-minted **`event_token`** — the
  report occurrence's own, reused by no member act — and the actor. The
  boundary **freezes the observer-corpus root first**, then appends the
  intent under that root's lease **before any member act begins**; if the
  root selection or the append fails, **no act begins and no record is
  minted**. Assessment runs keep opening the assessment-run intent as
  built, and a run request refused pre-intent (no frozen `spec_identity`)
  opens nothing *(amended 2026-08-11, the act-report design §3)*.

Appending the reserved log path itself is **engine bookkeeping**, not a logged
mutation — no recursive entry is required or permitted. Raw alteration of the
log path **within the anchored prefix** is caught by anchor evaluation (§6) —
interior damage is malformed, prefix truncation refuted. A structurally valid
raw append or replacement **beyond the maximal anchor** passes both checks and
may even be anchored later: it is L5's undetectable residue, which is why
every "an entry proves an act" claim in this design — an intent proving a
boundary-mediated attempt included — holds under the **cooperative-write
assumption** and no further.

A crash between registration and apply leaves a pending entry; on a **live**
root, `atoms` recovery resolves the transaction from its terminal record and
appends the settlement. On a **copied** root the transaction metadata did not
travel (`atoms` §7): a pending registration there is **unresolvable — never
inferred from disk state** — and import/adoption **refuses further mutation**
on that root until settlement evidence arrives from the origin or the root is
recopied. To keep settlement always appendable, **terminal-record GC is gated
on the settlement entry being durably appended and bound into the transaction
record** (§9).

## 4. The five consequences, witnessed

The general rule is §6's timeline replay; these rows are its named witnesses,
kept because kernel §8.7 enumerates them:

| kernel §8.7 consequence | witness |
|---|---|
| **G4** — discarded failed replay | intent entry, `event_token`-bearing, **unmatched under §6's reduction** — no pointers, or only fully resolved non-qualifiers: attempt-without-recorded-outcome, and discarding it after anchoring is truncation |
| **G8** — deleted failing verification | committed creation in the replayed timeline; record absent from the disk surface with no committed removal transition → refuted |
| **semantic identity** — fields-plus-hash edit | disk state disagrees with the replayed final surface at the local head → refuted |
| **§3.3** — spec predates run | the **committed** spec-freeze transition and the assessment-run intent entry ordered exactly within one chain — a rolled-back registration proves no spec existed; across chains only by ordered epoch cuts (§7), else unordered — never "spec predates run" by default. **Boundary-mediated executions only**: an out-of-band execution emits no intent, and a later cooperative import is witnessed at import time — the log proves when the record entered recorded history, never when the execution occurred (limitation 5) |
| **5a** — deleted retraction | same shape as G8: committed creation, no committed removal, absent record → refuted |

## 5. Anchoring and head capture

A **head** is the digest of a chain's latest entry. Anchors are per-genesis:
a fork's chain is anchored under its own genesis, and heads under different
geneses are never compared.

**Corpus heads** are captured at epoch build during that corpus's existing
lock hold, so head capture inherits X9's coherence — the head and the
corpus-state identity in the receipts describe one view. They land in two
carriers:

- **Epoch head members** — sorted, **subject-bound** triples
  `(corpus(corpus_id) | world(world_id), genesis identity, head digest)` for
  the covered corpora, plus the **world-chain head as of build start**;
  members of the epoch, covered by its packaging identity. The publication transaction
  then extends the world chain: an epoch cannot contain the entry that
  publishes it, and does not need to — the next observer does. **Members
  stay `corpus | world`**: an epoch is built over corpora, which a store is
  not, so a store subject in an epoch stays unconstructible *(amended
  2026-08-10, the verified-holdings record design §8)*.
- **Registry log-head records** — the ruled form of packaging §4's reserved
  slot: content-named, unordered, immutable; payload `(subject:
  corpus(corpus_id) | store(store_id), genesis identity, head digest,
  authored origin: build(epoch packaging identity) | anchor-act(actor))`.
  **Corpus or store subjects, never world**: a registry record cannot
  anchor the world chain — the registry lives inside the world root, and a
  store root is not it, so admitting a `world` subject here would let the
  world self-anchor (§2, L11); the L11 concern stays confined to the
  `world` subject *(amended 2026-08-10, the verified-holdings record design
  §8)*. The `world(world_id)` arm lives in every epoch's head members and
  in exported head artifacts; whether an epoch may serve as a **world**
  anchor is a carrier question (§6) — only through the externally
  supplied, exported route, never named from inside the root it would anchor.
  Unordered suffices: anchored heads of one genesis are totally ordered by
  chain ancestry, so "maximal anchor" is computed from linkage, never from
  record order — the registry's monotone-status discipline, unchanged.

**Every carrier is subject-bound** so an anchor identifies the root it
anchors even when the chain is wholly absent — exactly the L4 case, where no
genesis payload survives to say whose history is missing, and where, with
several anchored corpora, nothing else could associate an opaque genesis
digest with the arriving corpus. The **selected subject is the sole anchor
filter** (§6): a corpus anchor binds by `corpus_id`, the world's by
`world_id` — which must itself survive outside the chain, recorded in
installation configuration at world-root initialization and carried by every
exported head artifact. The presented manifest or configuration never
associates, admits, or discards an anchor; it is compared separately against
the genesis subject (§6). *(Amended 2026-08-23, the log-verification design
§1.2: for a corpus the comparison scope is the **pair** `(selected subject,
genesis_digest)`, because the corpus genesis is identity-free and every
constructible non-fork corpus chain shares one genesis digest — subject
filtering first, then genesis and ancestry. Nothing about the filter itself
changes; what changes is that genesis alone can no longer distinguish two
corpora.)*

**The explicit anchor act** writes registry log-head records for named
corpora and stores alike, outside any build *(amended 2026-08-10, the
verified-holdings record design §8)*. It reads chain heads only — no
corpus-state identity, no scan — so it is cheap enough to run before a sync,
before a GC act, or on demand to shrink the unanchored tail. For the **world
chain**, anchoring *is*
export: copying an epoch, or a compact head artifact, to a holder outside the
world root. No local act can anchor the world chain to itself.

## 6. Verification — observer sets, precedence, replay

Log verification runs at the boundaries that already recompute — **import**
(corpus arrival, before adoption) and **audit** (an explicit act over a live
root). It takes an **explicit observer set**: which anchor carriers to
consult — the registry, named epochs, supplied exported artifacts — following
5b's explicit-selection precedent. The finding records that bound. Verification
**mints nothing** (the 5b detection/correction split): findings only, and
correction stays with each record kind's own explicit constructor acts.

**Outcomes are exactly `validated | refuted | unresolvable | malformed`.**
Everything else — the maximal anchored head (`anchored-through`), the
unanchored-tail extent, the pending set, unmatched intents, the observer-set
bound, policy findings — is a **report field**, never a fifth outcome.

**Fixed evaluation precedence**, so no state earns two outcomes:

1. **Structure** — present chains only: a **wholly absent chain bypasses
   this step** (there is nothing to traverse) and proceeds directly to
   anchor evaluation, where any surviving anchor refutes it (L4) and an
   empty observer set is unresolvable. Undecodable entry; broken linkage; a
   **sibling branch** (two entries naming one predecessor) or an entry
   unreachable from the genesis (§3's linearity invariant); a
   settlement whose registration is not an ancestor or whose transaction id
   differs from its registration's; **two settlements for one registration**;
   **two registrations for one transaction id**; a `fulfills` naming an
   intent that is missing or not an ancestor; **two committed registrations
   fulfilling one intent** → **malformed**. Stops here; a malformed chain is
   never also refuted — interior deletion or rewrite breaks linkage and
   lands here, while truncation to a valid prefix is step 2's refutation.
2. **Anchors.** The verification **subject `S` is an explicit input** — the
   act names which corpus, world, or store it verifies, and the finding
   records it *(amended 2026-08-10, the verified-holdings record design
   §8)*. `S` is the **sole anchor filter**: the presented manifest or
   configuration never associates, admits, or discards an anchor. An anchor
   is **accepted** into evaluation by structure and by naming `S`, with
   possession as the trust root; carrier eligibility is §5's — a registry
   log-head record (**corpus or store subjects**, a `world` subject on a
   registry record is never an anchor, §5/L11) *(amended 2026-08-10, the
   verified-holdings record design §8)*; a head member read from an
   epoch that validates against its packaging identity, where for a
   **corpus** subject a named local epoch serves and for the **world**
   subject only the externally supplied, exported carrier route, never named
   from inside the root under verification (§5, L11); an exported head
   artifact that decodes and names `S`. Nothing is searched for —
   verification trusts exactly what the caller possesses and supplies, and
   the finding records the set. A forged-but-well-formed registry record is
   a raw world-root mutation: its integrity is the **world** chain's
   question, grounding at that chain's exported observers, and the finding
   names which anchor refuted, so a poisoned audit is diagnosable rather
   than silent. Then, for every accepted `S`-bound anchor:
   - chain **wholly absent** → **refuted** — removal (L4);
   - chain present under a **different genesis** → **refuted** —
     replacement: the anchored history was rewritten, not extended — prefix
     rewriting, never L5's tail residue, and never a mere non-match
     *(amended 2026-08-23, the log-verification design §1.2: this bullet
     fires for **world** subjects and for future fork geneses. For a corpus
     subject it is presently unreachable — the genesis is identity-free, so
     a replacement chain under the same `corpus_id` carries the **same**
     genesis digest and a fabricated distinct corpus genesis is malformed at
     genesis-form validation before any anchor judgment. Corpus-chain
     replacement is refuted through **anchored-head unreachability** in the
     bullet below instead: same verdict, stated mechanism)*;
   - **matching genesis** → into ancestry evaluation: **all** such anchors
     must be reachable in the chain by ancestry and mutually comparable —
     an unreachable anchored head or an incomparable pair → **refuted**; a
     reachable old anchor never hides a missing newer one, and "best
     reachable" is not a selection rule.

   An empty set of `S`-bound anchors → **unresolvable** relative to that
   observer set (reported as unanchored-from-genesis where the root is
   genuinely fresh) — never a claim that no anchor exists anywhere — and
   **replay is not reached**: a verdict against no anchor would be a verdict
   against nothing. The presented manifest `corpus_id` or configured
   `world_id` is compared **separately** against the present chain's genesis
   subject: a disagreement is a **subject-mismatch finding** plus §3's
   refusal where its lifecycle rule applies, and replay refutes a manifest
   edit since `corpus.yaml` is registered surface — the comparison never
   filters anchors. *(Amended 2026-08-23, the log-verification design
   §1.2/§6.3: at an import boundary the disagreement is a **refusal even
   when the chain verdict is `validated`** — a cooperatively logged
   `corpus.yaml` identity rewrite replays consistently, so replay alone is
   not the guard. At an explicit audit it stays a finding, since auditing a
   root whose identity is in dispute is the point. Step 1 also gained the
   genesis-**form** check, which runs before anchors: an undecodable or
   wrong-form genesis payload, or a non-empty baseline, is malformed, while
   a valid world genesis naming a **different** `world_id` is this
   subject-mismatch case and never malformed.)*
3. **Pending.** A pending registration whose transaction metadata is live
   resolves through recovery first; a pending registration **without** live
   transaction metadata — the copied root of §3 — → **unresolvable**, and
   replay is not reached: settlement is never inferred from disk state,
   whether or not the transaction's effects were applied before the copy.
4. **Replay.** From the genesis baseline, in chain order over **committed**
   registrations only: verify each entry's initial fingerprints against the
   accumulated registered surface, apply its final fingerprints; a
   rolled-back registration is no transition. Any initial-state disagreement,
   and any disagreement — **in either direction** — between the accumulated
   surface at the local head and the disk's registered surface → **refuted**:
   a path the timeline never produced is a disagreement, which is how a
   raw-created in-surface record is caught (§3). This is the general rule
   §4's rows instantiate — replacements, moves, and repeated paths are
   handled because the whole timeline is replayed, not pattern-matched.
5. Otherwise **validated**, with the report fields above. A consistent rewrite
   of the tail beyond the maximal anchor survives replay undetected — that is
   L5's pinned residue, bounded by anchor cadence.

Pending registrations classify per §3: resolvable on a live root through
recovery; **unresolvable** on a copied root, with further mutation refused.
Intent qualification reduces explicitly, and is **report-field status, never
the chain verdict**: any qualifying pointer → **matched**; no qualifier but
any pointer whose published run cannot be read → qualification
**unresolvable** — decayed bytes are not evidence of no outcome, and no
unmatched finding is emitted; only when every pointer fully resolves and
none qualifies (§3 — a non-run-publication transaction, another spec,
another `event_token`, no run created) → the attempt-without-recorded-outcome
finding, with each non-qualifying `fulfills` named in its own finding.

A **holdings intent**'s qualifying fulfillment is the same reduction, read at
its own shape: a committed registration publishing a holdings observation
for the intent's canonical location, carrying the intent's `event_token` — a
non-qualifying pointer never matches, and an unresolved one proves nothing,
exactly as above. The `fulfills` construction rule is restated, not relaxed,
for this consumer too: the boundary constructs the link from its own
holdings intent, never from a caller-supplied path *(amended 2026-08-10, the
verified-holdings record design §8)*.

An **operation intent**'s qualifying fulfillment reads at its own shape,
under the same reduction: for a non-run operation, a committed
registration publishing the **act-report** carrying the intent's
`event_token`; for a `dataset-production` operation, the minted `run` or,
when none is minted, that act-report. The **assessment-run intent's
qualification widens** to the same alternatives — the `run` as built, or
an act-report of kind `run-attempt` carrying the intent's token, for a
post-intent attempt that minted no run; a pre-intent refusal publishes an
*unfulfilling* report and fulfills nothing. The `fulfills` construction
rule is restated, not relaxed, for this consumer too: the boundary
constructs the link from its own operation intent, never from a
caller-supplied path *(amended 2026-08-11, the act-report design §3)*.

## 7. Ordering across chains

Within one chain, order is exact ancestry. Across chains, order exists only
through **ordered epoch cuts**, and cuts are ordered by **world-chain
ancestry, never sequence numbers** (packaging §5.1's decoration stays
decoration): epoch E2 orders after E1 **iff** E2's embedded build-start world
head descends from E1's settled publication entry. Two cuts not so related
are unordered.

An event `a` in chain A precedes an event `b` in chain B only when ordered
cuts establish it — an earlier cut whose captured A-head contains `a` and
whose captured B-head excludes `b`, and a later cut containing `b`. Both
events first appearing in one cut, or either root outside a cut's coverage,
is **unordered** — a single epoch cannot order its own contents, and per-corpus
captures within one build are serial but not mutually ordered, so the earlier
cut's build window is the residual uncertainty. §3.3's cross-corpus claim is
stated at exactly this granularity; "unknown" is a legal answer and the
default one.

## 8. Occurrence is not authorization

The log renders mutations **visible**; it does not render them **legitimate**.
Two separate judgments, never merged:

- **logged vs unlogged** — this design's axis. Unlogged cooperative mutation
  is unconstructible (L1); unlogged raw mutation is caught by replay against
  an anchored history (§6) or remains the stated raw-write residue.
- **permitted vs prohibited** — the consumer contract's axis. A **logged**
  removal of a failing verification is still a violation of the kernel's
  immutability rules; it is merely no longer hidden, and verification emits a
  policy finding naming it.

Consequences, stated so no deletion is accidentally blessed: corpus retirement
is a registry **status event** — an append, not a deletion. Preimage-blob GC
is host-local `atoms` housekeeping outside every registered root — not a
registered-root mutation, not logged, and not detection-relevant (§2.4).
Whole-epoch GC **is** a logged world-root mutation, and the GC act's report
keeps exactly packaging §9's shape; it cannot name — and this design does not
pretend it can name — externally held anchors, whose continued existence is
unknowable without a holder protocol (§12).

## 9. The `atoms` seam — obligations by repo

**`atoms`** (its deferred-obligation ledger, amended at banking; all inside
A7's executor path, implemented 2026-08-14):

1. `registered` entry written and durable **before** apply, inside the
   transaction path, in the pinned order: durable `PREPARED` → durable
   `registered` carrying the transaction id → the transaction record durably
   storing the entry digest → first apply. No entry, no apply; no digest in
   the transaction record, no entry recovery must guess at. Registration
   recovery is idempotent by transaction id — never a second entry.
2. `settled` as a **completion barrier**, in the pinned order: durable
   terminal decision → durable settlement append → transaction record
   durably binding the settlement digest → consumer **terminal-outcome**
   return and lease release, for **both** arms — rollback as much as commit.
   Idempotent by transaction id; recovery appends the settlement and
   backfills the binding when it resolves a transaction.
3. Genesis-with-baseline minted at root registration, all three arms of
   §3's union.
4. The `intent` entry API — the append serialized through the root's
   existing lease and **durably acknowledged before return**, so no
   cooperative race can mint a sibling branch — and the `fulfills` member
   carried opaquely into the transaction's `registered` entry.
5. **Terminal-record GC gated on the settlement entry being durably appended
   and bound into the transaction record** — the binding is the
   acknowledgement, and what keeps the gate checkable after a crash.
6. Log-path appends are engine bookkeeping — excluded from recursive
   registration, included in no transaction surface.

**science** (world layer and boundary): head capture under the build lock;
epoch head members; registry log-head records and the anchor act; head/epoch
export as the world-chain anchor; import/audit classification per §6; the
execution boundary freezing the destination corpus, writing assessment-run
intents there under the lease barrier (§3) **before** execution, publishing
through that same root, and constructing `fulfills` **from its own intent**
for the publishing transaction — never from a caller argument; and the
boundary writing holdings intents and constructing their `fulfills`, on the
`atoms` intent API as built (the verified-holdings record design §3)
*(amended 2026-08-10, the verified-holdings record design §8)*. The
boundary also writes **operation intents** — the observer-corpus root
frozen before the append, the append durable before any member act — and
constructs their `fulfills` for the closing terminal record (the
act-report, or the run where one is minted), on the same `atoms` intent
API as built. An `audit` operation's intent is the **boundary
wrapper's**, never the read-only evaluator's — the evaluator appends
nothing *(amended 2026-08-11, the act-report design §3, §4)*.

The **log's** `atoms` machinery changes nothing here, though `atoms` is not
wholly unchanged: the verified-holdings record design's read command, its
mutating-command post-state capture, its replica, restore, and fork
commands under the fail-closed writer state, and the payload-store root
kind are separate, named adoption obligations — that design's §7 item 7,
recorded against the adoption ledger's artifact 4 row *(amended 2026-08-10,
the verified-holdings record design §8)*.

## 10. Guarantees

New table, prefix **L**, certified by mutation per the estimator doctrine.
**Every row is [Plan B]-gated**: the tests run against the certified
`atoms`-backed executor after composition-root adoption; until
then kernel §8.7 stands
unchanged as the honest limitation. The positive arms of rows exercising
replay (L2, L5, L6, L13) presume an observer set carrying at least one valid
anchor — §6's step 2 passes; anchor-free and malformed classification belong
to L9 and step 1.

| # | guarantee | mutation test |
|---|---|---|
| L1 | Registration precedes application, with no unregistered cooperative path | kill the executor between entry durability and apply at every stage → entry present, pending; recovery settles it and the surface matches the settlement; crash after entry durability but **before** the transaction record stores the entry digest → recovery appends **no second registration** (idempotent by transaction id); cut persistence at **every** stage of the settlement sequence, for **both terminal arms** — a normally committing and a normally rolling-back transaction alike → recovery converges on exactly one registration and one settlement, backfills the transaction record's settlement binding, and **neither terminal outcome is returned, nor the lease released, before the settlement is durable**; attempt any cooperative mutation path that skips registration → unspellable |
| L2 | Settlement gates every absence test | under an anchored observer set: roll back a registered creation → the record's absence is **not** refuted (no transition); commit a creation, then raw-delete the record → refuted at replay; append two settlements for one registration → **malformed** at step 1; a pending entry on a **live** root settles through recovery; the same entry on a **copied** root (no metadata) → **unresolvable at step 3**, whether the copy caught the transaction **before apply** (record absent) or **after apply** (record present) — never refuted as a disk mismatch, never inferred from disk — and further mutation on that root is refused |
| L3 | Valid-prefix truncation refutes; interior damage is malformed | anchor, then truncate the chain to a valid prefix behind the anchored head → **refuted** at step 2, and the finding names the unreachable anchored head; delete or rewrite an **interior** entry → broken linkage, **malformed** at step 1; raw-append a **sibling branch** beside a retained original, or an **orphan** entry → **malformed** at step 1 (§3's linearity invariant — one genesis-connected sequence, one tip), never a silently ignored fork — never silently validated in any arm |
| L4 | Chain removal refutes against any surviving anchor, bound to its subject | delete the chain while a registry log-head record (or supplied exported head) is in the observer set → refuted — the "detectable journal removal" clause of kernel §8.7, discharged; with **two anchored corpora** and one arriving chainless → the subject binding associates the surviving anchor with the arriving corpus's `corpus_id` and refutes exactly it, never the sibling — an anchor is never matched to a root by elimination or by opaque genesis digest alone; raw re-mint an anchored corpus's manifest (`corpus.yaml` A → B) with the chain present → verify selecting **A**; A-bound anchors remain admitted by the selected subject, the manifest mismatch is reported separately, and replay **refutes** the edit — never `unresolvable` by subject disqualification; an edited configuration `world_id` against a present world chain → subject-mismatch finding **and operation refusal** (§3's lifecycle rule) — configuration is not registered surface, so replay cannot refute it, and the chain verdict derives independently of the presented configuration; replace an anchored corpus's chain with a **self-consistent different genesis** under the same `corpus_id`, verify selecting that subject → **refuted**, never empty-set `unresolvable` — a selected-subject anchor naming another genesis is replacement evidence, not a non-match; export a **W1** head, rewrite the local world subject and genesis to **W2**, verify explicitly selecting **W1** → refuted as removal/replacement, while selecting **W2** is a separate-world audit, never a verdict about W1; delete an anchored corpus A's chain **and** re-mint its `corpus.yaml` as B, then verify explicitly selecting **A** with A's anchor supplied → **refuted** as removal — the selected subject associates the anchor, and the presented manifest never discards it into empty-set `unresolvable`; delete or replace a store's chain while its store-subject registry record is in the observer set → **refuted**, the subject binding associating the anchor by `store_id`, never by elimination *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2 — mechanism, not verdict: the corpus genesis is identity-free, so the "self-consistent **different** genesis under the same `corpus_id`" arm is not currently constructible — a fabricated distinct corpus genesis is malformed at genesis-form validation before any anchor judgment. Corpus-chain **replacement** is refuted through anchored-head unreachability under the same constant genesis instead, which is the arm conformance cut 8 reads; the different-genesis refutation is read for **world** subjects and defers, with L10's fork arms, for a future fork genesis)* |
| L5 | The unanchored tail is the pinned residue | rewrite the tail beyond the maximal anchor into a self-consistent alternative **and rewrite the affected registered surface to match** → validated, undetected; assert the report's unanchored-tail extent covers it — the bound is anchor cadence, and the negative is the claim |
| L6 | The genesis baseline reaches pre-log history — once anchored | register over a populated root, anchor, then delete a baseline-covered pre-log record → refuted at replay; **negative:** with **no surviving anchor for the selected subject**, rewrite genesis, baseline, and chain consistently to omit the record → unresolvable at best, undetected — the baseline is load-bearing only under an anchor, and one surviving selected-subject anchor turns the same rewrite into a refutation (L4) *(amended 2026-08-23, the log-verification design §1.3 — **both arms are presently unconstructible**: every genesis baseline is empty, no Science path mints a populated one, and genesis-form validation refuses a non-empty baseline as malformed, so the positive arm has no starting state; the anchor-free negative needs the same populated-baseline start for the omission to be the **baseline's** claim, and under empty baselines it collapses into the anchor-free rewrite residue already homed in L5. Conformance cut 8 reads this row **not at all** — reading it would certify nothing the amendment leaves standing. Lifting the amendment is a registration-surface design act, and the row is then read by that act's own cut)* |
| L7 | Intent claims are exactly as wide as stated | assessment-run intent with **no pointers at all, or every `fulfills` pointer fully resolved and non-qualifying** — §6's exact reduction, never a collapse of an unresolved candidate → attempt-without-recorded-outcome finding, never a refutation; excise the intent entry after anchoring → **malformed** (interior linkage break) or, via truncation to a valid prefix, **refuted** — never silent; a second committed registration fulfilling the same intent, or a `fulfills` naming a missing or non-ancestor intent → **malformed**; mutate the fulfillment itself — a wrong-purpose committed transaction carrying `fulfills = I`, a run publication under another spec, another `event_token`, or a publication creating no run → each **fails qualification** (§3), the intent stays attempt-without-recorded-outcome, and the non-qualifying `fulfills` is named in a finding; make a **genuine** published run's bytes unresolvable → qualification **unresolvable**, and **no** unmatched finding is emitted (§6's reduction); kill between the intent's durable append and execution start → intent present, no execution — attempt-without-recorded-outcome, exactly as stated; race two cooperative intent appends on one root → serialized by the root lease, one linear chain, never a sibling branch (L3); attempt to publish the run through a root other than the intent's → **refused**, placement froze before execution; assert no caller-supplied `fulfills` path exists at the boundary; **negative:** crash, cancellation, and discarded failure are indistinguishable by construction; the guarantee quantifies over **both** intent kinds — instantiated for the holdings shape, a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between a holdings intent's append and its mutation reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-10, the verified-holdings record design §8)*; the guarantee now quantifies over the **operation intent** too — instantiated for its shape, a report carrying another operation's token, a report of the wrong kind, a run publication for a non-run operation, or a registration publishing no terminal record each **fails qualification** (a second fulfilling registration on one intent stays the chain's **malformed**, classified before qualification — T2's arm), and a kill between the operation intent's append and its first act reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-11, the act-report design §3)* |
| L8 | Cross-chain order exists only through world-ancestry-ordered cuts | committed spec-freeze transition in E1's captured head, intent absent from E1, intent in E2, E2's build-start world head descending from E1's publication entry → ordered; both events first appearing in one cut → unordered, and "spec predates run" is not emitted; assert epoch sequence numbers are read by nothing |
| L9 | Anchor evaluation is total over the observer set, never best-reachable | observer set holding an old reachable anchor and a newer anchored head absent from the chain → refuted, never validated-through-the-old; two mutually incomparable anchored heads for one genesis → refuted; empty set → unresolvable with the observer bound recorded; assert `anchored-through` and the observer set appear as report fields, and that malformed structure stops evaluation before any anchor judgment |
| L10 | A fork is a new chain; a replica is the same chain | fork act → fresh genesis carrying `(parent genesis, parent head)` and its own baseline; assert parent and fork anchors are never compared; replica/restore → same genesis, chain carried unchanged, comparability intact; a copy presenting the parent genesis under a fresh `corpus_id` manifest without a fork-genesis → its chain refuses to verify under the new identity (genesis names the parent `corpus_id`); the **store instantiation** (the verified-holdings record design §2) — replica act → same genesis, chain carried unchanged, the copy stamped read-only in engine bookkeeping, the stamp durable **before** the copy is exposable; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation on any root **not granted writability** → refused, the fork act the only exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2/§6.2 — mechanism, not verdict: the copy presenting the parent genesis under a fresh `corpus_id` manifest **cannot** be caught by a genesis-payload comparison, since a corpus genesis names no `corpus_id`. The arrival act is the mechanism instead — `admit_arrival` selects `S = Corpus(provenance.parent_corpus_id)`, because the chain a replica carries is its parent's, and the fresh manifest then refuses `SubjectMismatch`: its chain refuses to verify under the new identity, exactly the frozen claim. This is the one arm of this row conformance cut 8 reads; every fork, replica-construction, restore and store arm still waits on ledger row 4)* |
| L11 | The world chain is anchored only by export | present an epoch stored inside the world root as the world chain's anchor → not accepted into the observer set, while the **same** epoch supplied for a **corpus** subject is accepted — eligibility is carrier-specific, not a property of the epoch; a registry log-head record carrying a `world` subject → unconstructible through the anchor act and never accepted as an anchor; coordinated truncation of world chain, registry, and in-root epochs with no exported holder → undetected (**negative**, the surviving-observer bound); the same truncation with one exported epoch supplied → refuted |
| L12 | One state vocabulary, and the log path is bookkeeping | each typed state class — absence, directory, symlink target, mode — round-trips through registration fingerprints and replay; assert no second summary model exists; appending the log is not recursively registered; raw-edit the log path **within the anchored prefix** → caught at step 1 (interior damage, malformed) or step 2 (prefix truncation, refuted); **negative:** a structurally valid raw append beyond the maximal anchor — most sharply a forged intent — passes steps 1 and 2 and may later be anchored: L5's residue, and why every entry-proves-an-act claim holds only under the cooperative-write assumption (§3) |
| L13 | Logged is not permitted | log-visible removal of a **verification** via a cooperative act → the removal is in the timeline **and** verification emits the policy finding naming the deleted record; assert the finding classifies it as removal of a *failing* verification only where the historical content resolves — a held copy or surviving preimage bytes — since entries retain state digests, not verdicts; with the preimage GC'd and no copy held, the deletion is still detected and the semantic classification is honestly absent; assert corpus retirement appends a status event and deletes nothing; assert preimage-blob GC appears in no chain |

## 11. Limitations

1. **The unanchored tail is rewritable.** Bounded by anchor cadence; the
   anchor act exists to shrink it on demand (L5 pins the negative).
2. **Detection has a surviving-observer bound.** The world chain is unanchored
   until something leaves the root; destruction of a world and every observer
   of it is undetectable, and `refuted` is a completeness verdict, not a
   malice verdict — an honest old backup and a truncation are observationally
   identical (§1).
3. **Outside the registered surface, raw creation is not this design's
   catch.** Inside it, replay refutes a path the timeline never produced
   (§3, §6) — the detection R19's negative (e) and substrate §4.3 defer to
   this design, discharged at implementation. An **undeclared foreign path**
   is outside the surface: a walk-hazard and validation question, unchanged
   here.
4. **Cross-chain order is partial.** Ordered cuts or nothing; the earlier
   cut's build window is the residual uncertainty (§7).
5. **Attempt visibility and chronology are boundary-mediated claims.**
   Crash, cancellation, and discarded failure behind an unmatched intent are
   indistinguishable; G4's upgrade is from *invisible* to
   *visible-unresolved*, and covers boundary-mediated attempts only. The
   same bound holds for §3.3's chronology: an out-of-band execution emits no
   intent entry, and cooperatively importing its self-consistent record logs
   the **import** — the log proves when a record entered recorded history,
   never when an unwitnessed execution occurred. Raw attachment is caught as
   an unlogged surface mutation (§6); cooperative import of the out-of-band
   past is the residue.
6. **The end-to-end capability is gated on composition-root adoption.**
   A7's engine half and A8's certified production tuple are implemented; the Science half is not.
   Until then, kernel §8.7 and packaging limitations 1–2 stand exactly as
   written.
7. **Pending on a copied root may never resolve.** Settlement evidence lives
   with the origin; the refusal state (§3) is the honest floor, and recopying
   is the remedy.
8. **No holder protocol.** Which exported anchors exist, and whether they
   survive, is unknowable locally; epoch GC cannot account for external
   holders (§8), and anchor distribution waits with §12.

## 12. Open questions

- **Entry serialization and the head-artifact format.** Identity runs over
  prescribed digests, so any canonical serialization serves; choosing one is
  an implementation-plan decision, beside packaging's map-format question.
- **Verification cost at scale.** Full-timeline replay at mm30 scale is
  subject to the ledger's measurement gate before any optimization — a Merkle
  overlay is the known upgrade path and is not built speculatively.
- **Anchor distribution and a holder protocol.** Which observers hold exported
  heads, and whether holders attest continuity, waits for a second
  installation to exist — the rules-store distribution question's twin.
