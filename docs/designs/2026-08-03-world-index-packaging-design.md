# World-index packaging — design

**Status:** Banked 2026-08-03. Second design after sub-problem 5a (adoption ledger
§3); banked with in-place amendments to world §5's map inventory, W8a, W13's
negative, world limitation 9, and world §10's first two questions (closed).
Amended 2026-08-03 in eight places (§3, §4, §5, §5.1, §5.2, X9, §12,
limitation 1) at the tamper-evident log design's banking
(`2026-08-03-tamper-evident-log-design.md`).
**Inherits:** world §5 (the index maps — four at this design's banking and four
since, with **membership changed 2026-08-08**: the alias map retired with the
stored alias and the **coreference** map arrived, `2026-08-08-world-address-ruling.md` §4.3 and
§5.5 — producer snapshot, corpus manifest, derivation receipts), §5.1 (`not-present` vs `unknown`), §10 (the packaging
question, with receipts and rule-holding folded in); repro §9's amendment (anchor
placement — the index is the natural carrier); 5a §4 (the retraction map, a fourth
derived member) and limitation 6 (discovery is enumeration-bounded, temporal half
deferred here); the ledger's artifact-1 consumer list.
**Constraints:** the guarantee tables G/S/W/R/C stay frozen — this design adds its
own table (X) and, where a banked rule must change (W13's re-minting negative and
world limitation 9, §4), amends in place under the same identifier, never
renumbering. Nothing here is tamper evidence (§11.1); the
registry is the head carrier for the mutation log (repro §9; record shape ruled
2026-08-03, §4), and that log keeps its own design.

## 1. Why

The world index is the largest unbuilt artifact in the redesign and was, until
now, the least specified: world §5 defines *what* it holds and §10 admits it never
said where it lives, who writes it, or what a consumer may assume about its
freshness. Meanwhile every adjacent design has been depositing requirements on it:
`not-present` resolution for absent corpora (world §5.1), receipt checkability and
rule-holding (world §5), ~~merge inbound hygiene~~ and `corpus_id` uniqueness
refusal (world §4.3, §5) — *merge inbound hygiene lapsed 2026-08-08: structural
merge is retired and `consolidate` rewrites no inbound reference, so the index
carries no hygiene obligation for it*, §9 anchor carriage (repro §9, amendment 2026-08-03), and the
retraction map with 5a's temporal discovery bound explicitly deferred to "whatever
staleness semantics the packaging design settles" (5a limitation 6). This design
pays those IOUs: it rules the artifact's home, its write discipline, and its
staleness contract, and it settles the two questions world §10 folded into the
same package — the corpus manifest's contents and where receipts and enumeration
rules are held.

## 2. Framing rulings

Three rulings, made before the structure and constraining all of it:

1. **Single live host.** One machine holds the live world at a time. Every other
   copy is a replica or a cold arrival: a world root arriving by copy without
   engine metadata is a normal cold bootstrap, and one arriving *with* another
   host's metadata is a restored-backup classification case (`atoms` §7, and the
   ledger's cold-arrivals invariant). Concurrent multi-host publication is out of
   scope and *named* as such (§11.4) — this is a stated assumption, not an
   enforced invariant.
2. **Split discipline.** The index has two authority classes and they get two
   update disciplines. The **registry** (§4) is authoritative and write-through:
   corpus lifecycle events are registry events, and the acts that need it refuse
   if they cannot reach it. The **derived maps** (§5) change only at an explicit,
   identity-stamped build; their staleness is visible, never silent.
3. **Full scope.** The corpus manifest and the receipt/rule-holding questions are
   settled here, not deferred again — they share one failure story (what survives
   when a corpus is absent), and every consumer in the ledger's artifact-1 row
   needs all three answered together.

## 3. The world root

One installation-level directory — the **world root** — named by installation
configuration, outside every corpus. It is not a corpus: no `nodes` tooling reads
it, its layout is this design's contract, and nothing about its path enters any
identity. That last clause is W5 applied one level up: the root is *where* the
world's records sit, never *what* they are, so moving or renaming it is an
operational act with no epistemic content.

Layout, fixed:

```text
<world-root>/
  registry/   append-only lifecycle records          (§4)
  epochs/     immutable index publications           (§5)
  rules/      held enumeration-rule implementations  (§7)
  log/        the world root's own mutation-log chain (tamper-evident-log §3)
```

**Amended 2026-08-03** (`2026-08-03-tamper-evident-log-design.md` §3): the
layout gains the world chain's reserved log path, and the installation
configuration gains a **`world_id`** field with a fixed lifecycle — fresh
initialization mints it; replica, restore, and cold bootstrap over an existing
chain **preserve the genesis `world_id`**; a configuration/genesis mismatch
**refuses** rather than silently re-minting. The configuration is not
registered surface: the log design's verification reports a mismatch as a
finding and refuses operation, while the chain verdict derives independently.

## 4. The registry — the authoritative core

The registry is the part of the index that is **not rebuildable from the
corpora**, which is precisely why it exists as its own class. Two consumers force
that: `corpus_id` uniqueness refusal needs a record of every id **ever admitted**,
not merely those currently visible — reusing a retired id would make every old
coverage declaration and receipt naming it ambiguous — and repro §9's anchor must
survive exactly the deletions it exists to catch, so it cannot live in anything a
rebuild recomputes.

**Records.** Append-only, attributed, immutable; one file per event,
content-named. Three record types:

- **admission** — the `corpus_id`, a copy of the manifest facts at admission, and
  the authored provenance: `fresh`, `replica-of`, or `fork-of` (with the parent
  id and, for a fork, the corpus-state identity at the fork).
- **status event** — `retired` or `departed`, both **terminal**.
- **log-head records** for the mutation log — **ruled 2026-08-03** by the
  tamper-evident log design (its §5), which owns shape and cadence: the subject
  is a **corpus only** — `(corpus_id, genesis identity, head digest)` plus the
  authored origin, `build` (carrying the epoch packaging identity) or
  `anchor-act` (carrying the actor). A `world` subject is unconstructible here:
  a registry record anchoring the world chain would live inside the world
  root's own deletable set (log design L11). Like every registry record the
  files are unordered; anchored heads order by chain ancestry, never by
  arrival.

**Status is computed, monotonically, without event ordering.** Content-named
files carry no order, so no status may depend on one. The model:

```text
known   := an admission record exists
live    := known, and no terminal status event exists
present := installation configuration resolves exactly one corpus carrying the id
```

`retired` and `departed` are terminal: no API returns a corpus to `live`, and a
replacement replica carrying an already-admitted id is `present` again without
any new admission — replication changes where a corpus is reachable, never
whether it was admitted. Because every predicate is monotone in the record set,
two registry copies that hold the same records agree on every status regardless
of arrival order.

**Admission is the cross-root commit point.** A manifest written into a corpus
makes an *unregistered corpus* — a local fact. The corpus is in the world iff its
admission record exists; admission **refuses** a `corpus_id` that is already
known (unless the act is the authored replica declaration, which mints no new
admission), and an epoch build refuses a coverage declaration naming an
unadmitted corpus. The one raw-write escape — two corpora placed on disk carrying
one id with no admission act — is caught at build, as world §5 already rules.

**No purge, ever.** The registry grows monotonically and "live" is a computed
status, not a row deletion. A world that admitted and retired a corpus is forever
distinguishable from one that never admitted it — the 5a digest-is-the-memory
shape, one layer down.

**The registry amends banked W13, and says so.** W13's negative asserted that raw
re-minting a `corpus_id` is undetectable *because no surviving record names the
old id* — and the admission record is now exactly such a record. The bound splits:
a **manifest-only** re-mint is detected at the next build (the presented id has no
admission, X7, while the registry names the original); the **coordinated** act —
re-mint the manifest and raw-**forge** an admission for the new id, optionally
also deleting the old one — remains undetectable until the log lands
(limitation 1). The fork mimicry requires **retaining** the old admission: a
legitimate fork keeps its parent's admission, so a registry missing it is unlike
a fork. Deleting an admission **alone** is a distinct undetectable registry-loss
case that evades nothing — the re-minted id stays unadmitted and X7 still
refuses. W13's negative and world limitation 9 are amended in place under their
identifiers, in the world document, as part of this design's adoption.

## 5. Epochs — the derived publications

An explicit **build** enumerates a declared coverage — a set of admitted, live
`corpus_id`s — and publishes one immutable **epoch** holding the **four** maps
(address, producers, retraction, coreference — *the fourth was **alias** until
2026-08-08, when it retired with the stored alias and the **coreference** map took
its place: sorted endpoint pair → reduced balance and distinct-key count, world
address ruling §4.3 and §5.5*), the producer snapshot with its
derivation receipts, the **retraction-map derivation receipt**, and — added at
5b's banking (normative-contract §7.6) — the **certification-enumeration
receipt** (§7), and — added 2026-08-08 with the coreference map (world address
ruling §5.5) — the **coreference-reduction receipt** (§7), and — added at the
tamper-evident log design's banking
(its §5) — the **anchored head members**: sorted
`(subject, genesis identity, head digest)` triples, one per covered corpus
chain, plus the **build-start world-chain head**. Nothing else writes into
`epochs/`.

### 5.1 The build contract — coherent enumeration first, publication second

The build is a computation and the publication is a transaction, in that order —
`atoms`' own rule ("the transaction is the publish, not the computation") applied
to the artifact that will one day ride its transactions.

**Coherent enumeration.** Every map in one epoch is derived from **one recorded
state view per covered corpus**, shared across all four maps and the snapshot.
The load-bearing mechanism is the **lock, not the check**: the build acquires
each covered corpus's **existing per-corpus write lock** and holds it for the
entirety of that corpus's capture — state identity, then enumeration — one
corpus at a time, releasing before the next. No multi-root transaction and no
world-wide freeze: coverage is captured serially, and each corpus's view is
coherent because no cooperating writer can interleave with a held lock. The
pre/post identity pair alone could not carry this claim — a corpus can move
`A → B → A` while a scan reads mixed files, and the final identity still equals
the initial one — so the post-capture recompute is retained strictly as a check
against **noncooperating (raw) drift**: a mismatch discards the capture and
retries or refuses; it never publishes; and a raw ABA writer defeats it, which
is the standard raw-write bound, stated in X9's negative. A mixed epoch —
producers from one state of a corpus, retractions from another — is therefore
unconstructible through cooperating writers (X9). Contention resolves by
**refusal in both directions, never by waiting**: a build reaching a corpus
whose lock an active writer holds refuses, and an API write reaching a corpus
whose lock the build holds is refused — no queueing on either side, so neither
party can stall the other invisibly.

**Coherent head capture** (added 2026-08-03, tamper-evident log design §5):
each covered corpus's chain head is captured **within the same lock hold** as
that corpus's state identity — one view per corpus, head and state together
(X9) — and the **build-start world-chain head** is read under the world root's
**own** write lock, never inferred from registry records.

**Publication.** The epoch is written create-only and never edited. A single
**current pointer** selects the default publication; swapping it is the only
mutation in `epochs/`, and both its durability and the swap's crash-atomicity
are gated on the `atoms` executor (§8, limitation 2). A
sequence number may decorate epoch directories for operator convenience — it is
**operational decoration, not contract**; content identity plus `current`
supply everything the contract needs.

### 5.2 Three identities, kept apart

An epoch touches three identity classes, and conflating any two of them re-opens
defects the banked designs closed:

- **The producer snapshot's semantic identity** (world §5) — the only semantic
  map/snapshot **identity** that is a belief input, unchanged by this design;
  the retraction projection (next bullet) is also a closure input, entering as
  a projection rather than an identity. Two epochs built over unchanged corpora
  carry the **same** snapshot identity, and an exact no-op rebuild — same states,
  same rule — re-derives the **identical receipt** too (receipt identity is a
  function of snapshot, states, and rule); state or rule changes may mint another
  receipt while leaving belief unchanged. Rebuilds move belief only when the
  enumeration really did change.
- **The retraction enumeration** (5a §6) — enters kernel §5.1's closure as the
  prescribed projection: found refs, resolutions, and the coverage declaration.
  **Not the epoch identity**, and the exact corpus states stay in receipts.
  The **certification-inventory projection** (added at 5b's banking,
  normative-contract §7.6) is the third semantic member: the epoch-wide
  by-kind `instrument-certification` enumeration as sorted refs under the
  coverage — location-free, resolution-free — the comparison report's
  receipt-covered core. Like the others, never the epoch identity.
- **The epoch's packaging identity** — a content identity over the epoch's
  members. It names the *publication* for receipts, GC acts, and operations, and
  it is **never a belief input and never a shared semantic identity of the
  maps**: the maps deliberately do not share one (world §5), and packaging them
  together must not manufacture one. The **anchored head members** (added
  2026-08-03, tamper-evident log design §5) sit in this class: packaging
  members that enter the packaging identity, **never semantic identities and
  never belief inputs** — an epoch anchors chains without chains entering
  belief.

### 5.3 `current` is operational, and belief never reads it

**`current` selects the default operational publication only.** Resolution
convenience — "look something up" — may follow it. A belief computation may
**not**: it receives an explicit producer-snapshot identity (world §5's
explicit-selection rule), and every epoch remains readable by its packaging
identity for as long as it exists. "Compute belief against current" is
unspellable through the API (X3): it would be implicit-latest selection, the
exact thing world §5 rejected for snapshots, arriving through a side door.

### 5.4 The staleness contract

Every answer an epoch gives is **bound-stamped**: it carries the epoch's
packaging identity and coverage declaration, so what a consumer learns is always
"as of this publication, over these corpora." This is where 5a's limitation 6
lands: a retraction-map answer is epoch-bounded, a retraction minted after the
epoch's build is invisible until a later build, and the remedy is a rebuild.

Stated with the honesty the bound deserves: **the bound is visible; actual
staleness may be unknown.** The epoch names the states it read; nothing bounds
what has happened to the corpora since, and no consumer may treat "recent epoch"
as "fresh world."

**`not-present` vs `unknown`, scoped.** With every corpus absent, an address
recorded in the epoch resolves `not-present` — the §5.1 requirement this
artifact exists to meet, covering retired addresses through the §4.3 redirect.
An address **outside the epoch's coverage** is legitimately `unknown`: the epoch
never saw the corpus that could have recorded it, and claiming `not-present`
there would convert a coverage bound into a world fact.

## 6. The corpus manifest

A reserved file, `corpus.yaml`, at the corpus root — the **first consumer of
`nodes`' reserved-path contract** (nodes redesign design §2), which is what makes
a root-level non-node file a declared part of the layout rather than a walk
hazard. Fields, deliberately minimal:

```yaml
manifest_version: 2
corpus_id: <opaque 128-bit value, lowercase hex, minted once>
profile:                # added 2026-08-04; see the amendment below
  science_contract: science:<contract-identity>
  domains:              # a mapping, never a list
    biology: biology:<contract-identity>
forked_from:            # optional; present iff this corpus was forked
  corpus_id: <parent id>
  corpus_state: <exact corpus-state identity at the fork>
```

**Amendment (2026-08-04) — the `profile` block, and why the old closure could
not simply be widened** (`2026-08-04-domain-extension-boundary-design.md` §7).
This section previously read "Nothing else," on the reasoning that every
additional field is a place for a location or a human label to sneak back into
an identity's neighborhood (world limitation 9). That reasoning is **superseded
rather than overruled**: it was sound precisely *because* manifest fields sat
outside every check, and world §5 has now been amended so the corpus-state
identity is taken over the **complete canonical manifest projection**. A field
in the manifest is no longer unchecked, so the objection no longer applies —
and the two amendments must land together, since `profile` inside an unchecked
manifest would reproduce exactly the defect limitation 9 named.

The `profile` block pins the normative contracts under which this corpus's
kinds and facets are legal: exactly one `science_contract`, and a
**namespace-to-contract mapping** of domains. A mapping rather than a list makes
duplicate namespaces unrepresentable and ordering a non-question. The manifest
stays a **closed** shape: an unknown field, a duplicate key, or a malformed
contract identity is **refused at load**, never ignored.

Coordination facts still have their home in `science.yaml`, not here. Replica vs
fork stays an authored act, exactly as world §5 rules it: a fork declares
`forked_from` and mints a fresh id at copy time; a replica changes nothing; the
undeclared case is caught by the uniqueness invariant when both are live.

## 7. Receipts and the rules store

**Derivation receipts live in the epoch beside the artifacts they name.** Several
receipts per snapshot is the ordinary case (world §5), and an epoch is exactly
the "minted together" grouping that keeps them findable when the corpora are
not. Receipts for computations elsewhere in the system live with their runs;
this design homes only the index's own evidence.

**The retraction map gets its own derivation receipt, on the producer-receipt
contract.** 5a §6 puts the enumeration's exact states in receipt material, and
until now nothing defined the receipt that carries them — the epoch's packaging
identity cannot: omit an in-coverage retraction and repackage, and the new epoch
is internally consistent under a new packaging identity, proving nothing. The
receipt mirrors world §5's producer-receipt contract member for member: an
immutable record directed at the retraction enumeration, carrying the
enumeration's projection identity (found refs, resolutions, coverage — 5a §6's
closure member), the exact corpus-state identity per covered corpus, and a
**fixture-bound enumeration-rule binding** — the rule identity and, since 5b's
banking, the **implementation content identity that ran** (normative-contract
§6); its own identity is the digest over those three. Validation rebuilds the
map **using the exact binding the receipt names**
against corpora standing at the named states — an omitted in-coverage entry
**refutes**; an absent state or un-held rule is `unresolvable`; a bare version
string is `malformed` (world §5's outcomes, unchanged). Same coherent capture
feeds both receipts, so their per-corpus states are identical within one epoch
(X9).

**The certification-enumeration receipt joins at 5b's banking, on the same
contract** (normative-contract §7.6). Its subject is the
**certification-inventory projection** — the epoch-wide by-kind
`instrument-certification` enumeration as sorted refs under the coverage,
location-free and resolution-free, the comparison report's receipt-covered
core — with the exact corpus-state identity per covered corpus and the
fixture-bound enumeration-rule binding; the address-map sourcing and per-ref
corpus assignment are receipt material, never projection members. Validation
rebuilds the projection with the named binding against corpora at the named
states — an omitted in-coverage certification **refutes** (X12); an absent
state or un-held rule is `unresolvable`; a bare version string is `malformed`.
The same coherent capture feeds all three receipts, so per-corpus states are
identical within one epoch (X9).

**The coreference-reduction receipt joins 2026-08-08, on the same contract**
(`2026-08-08-world-address-ruling.md` §5.5). Its subject is the **coreference map** — sorted endpoint
pair → derived balance and distinct-key count, reduced under the coverage — the
**edge state is not a map member**, being a function of the querying world and of
the receipt's current resolvability, neither of which an immutable epoch knows — with the exact corpus-state identity per covered corpus and the
fixture-bound enumeration-rule binding. Validation rebuilds the reduction with
the named binding against corpora at the named states: an omitted in-coverage
`coreference-attestation`, or a balance that does not recompute, **refutes**
(X12); an absent state or un-held rule is `unresolvable`; a bare version string
is `malformed`. **Four receipts now, one capture** — per-corpus states stay
identical within an epoch (X9).

Two things distinguish this receipt from its three siblings, and both follow
from coreference sitting outside belief (that ruling's §5.3).

- **It carries no semantic identity and is not a belief input.** The producer
  snapshot's semantic identity exists because kernel §5.1 digests it; nothing
  digests a coreference balance, so the map is packaged evidence and nothing
  more. A build over a narrower coverage may publish a different balance and
  **must not** move `belief_input_digest`.
- **Any outcome other than `validated` has a reader-visible consequence the
  others lack.** A coreference receipt that is `refuted`, `unresolvable` **or
  `malformed`** makes every edge it covers **`indeterminate`**, and a query
  expanding over one **refuses** rather than reading the edge as inactive (that
  ruling's §5.5). All three, not two: `malformed` is the case a
  consequence-free reading would leave dangling, and it is the one where
  refusing matters most, since a receipt no corpus mount and no rule
  installation could ever make checkable is exactly what a forged record looks
  like. For the retraction and certification receipts a failed validation is a
  finding about the epoch; here it is also an answer the query layer must give.
  X10 carries the arm.

**The rules store holds what "held" means.** `rules/` stores enumeration-rule
implementations content-addressed, each with the fixtures that bind its
identity (world §5's fixture-bound rule contract). Clarified at 5b's banking
(normative-contract §6): the fixtures are **contract-normative content** — the
store holds implementations *and* fixture content, and binding runs through
the contract's fixture-set identity, which the rule identity contains. A rule is **held** iff
present here; **un-holding is an explicit removal act**, never a side effect of
installing a newer rule — two rules held at once is the ordinary upgrade state.
Receipt validation resolves the named rule identity against this store and
never against "whatever this installation would run today."

## 8. The `atoms` seam — and what the interim writer may not claim

The world root is one `atoms` engine root. An epoch publication is one
transaction on it — the epoch's files create-only, plus the pointer swap — and a
registry append is a smaller one. The transaction covers **only publication**:
enumeration and map derivation complete before it begins, per `atoms`' own
ruling that the transaction is the publish, not the computation. One
transaction, one root, holds — corpus writes and world-root writes are separate
sequences composed by the consumer, never one transaction.

**The interim writer is best-effort, and says so.** `atoms` A7 landed
2026-08-14 and A8's persistence-cut certification landed 2026-08-17, but the
Science composition root does not exist. The substrate design's ruling therefore
stands: no Science claim of crash-safe multi-file durability before adoption. Until then the
writer is plain create-then-pointer-replace —
same layout, same seam, honestly weaker, and the weakness is not confined to
partial epochs: after a durability failure (a persistence cut, not only a
process kill), `current` may still name the old epoch, may be **missing**, or
may name **incomplete content**. "Durable pointer" is itself a gated claim.
Every durability and crash-atomicity claim in §10 is **gated on composition-root
adoption** and stated as such; the layout is constrained now
so that swapping the executor
changes no consumer-visible contract (X-gating, §10; limitation 2).

## 9. Garbage collection — two hard rules, policy deferred

GC of old epochs is explicit consumer policy — nothing automatic, ever, because
an automatic retention policy would silently destroy historical evidence.
**Whole-epoch GC is the sole deletion operation**: no API deletes an individual
epoch member, and the mechanical fact that `atoms` today lacks recursive
directory deletion (so removal executes per path) does not license a per-member
operation. The policy itself can wait. Two rules are fixed now:

1. **A GC act cannot delete `current`.** Refused, structurally.
2. **Every epoch remains identity-addressable until explicitly deleted**, and a
   deletion act must **report what it severs**: the snapshots and receipts the
   deleted epoch carried, which may become unresolvable where no other epoch or
   replica holds them. Deletion is legal; silent evidence destruction is not.

## 10. Guarantees

New table, prefix **X**. Each row is certified by mutation, per the estimator
doctrine. Rows marked **[Plan B]** are gated: their mutation tests run against
the certified `atoms`-backed writer after composition-root adoption, and the interim
writer carries limitation 2 instead of the claim.

| # | guarantee | mutation test |
|---|---|---|
| X1 | A published epoch is immutable, and members are never deleted individually | no API edits or deletes an **individual** epoch member — whole-epoch GC (§9, X11) is the sole deletion operation; raw-edit a member → the epoch's packaging identity no longer matches at audit, reported |
| X2 | **[Plan B]** Publication is crash-atomic and `current` is durable: it never selects a partial epoch and survives a persistence cut | kill the writer at every stage of publication **and** cut persistence (power-fail simulation) at every stage; assert `current` resolves the **prior epoch when the cut precedes the commit decision's durability, and the new, complete epoch after it** — `atoms` recovery rolls a committed transaction forward, never back — and is never missing and never names incomplete content; pre-commit residue is detected and reported. **Interim negative:** the best-effort writer can leave a partial epoch, a missing `current`, or a `current` naming incomplete content after a persistence cut — asserted and reported, per limitation 2 |
| X3 | Belief never reads `current` | attempt a belief computation selecting "current" rather than an explicit snapshot identity → refused; assert every epoch remains readable by packaging identity while it exists |
| X4 | The registry is append-only through every API | assert no API mutates or deletes a registry record; attempt a purge → unspellable. **Negative (limitation 1):** raw deletion of an admission record is undetected until §9 lands |
| X5 | Duplicate `corpus_id` is refused at admission and detected at build | admit a known id → refused (replica declaration excepted, minting no admission); raw-place two corpora with one id, build → refused, reported |
| X6 | Status is monotone and terminal states are terminal | emit `retired`, attempt any act returning the corpus to live → unspellable; make an admitted, live corpus unreachable, then restore a replica carrying its id → `present` recomputes true with **no new admission record**; assert every status is invariant under record arrival order |
| X7 | Admission is the cross-root commit point | build a coverage naming a manifest-bearing but unadmitted corpus → refused; admit it → same build proceeds |
| X8 | Every epoch answer is bound-stamped | assert answers carry packaging identity + coverage declaration through every read API; an answer without them is unconstructible |
| X9 | An epoch's maps **and its anchored head members** share one coherent state view per corpus, held by the corpus write lock (head/state coherence added 2026-08-03, tamper-evident log design §5) | attempt an API write to a covered corpus while the build holds its lock → **refused**, never queued, never interleaved; start a capture on a corpus whose lock an active writer holds → build **refuses**, never waits; raw-mutate a covered corpus during capture → post-check discards, build retries/refuses; assert no published epoch's receipts name two states of one corpus, and that the producer, retraction, certification-enumeration, and coreference-reduction receipts (the third added at 5b's banking, the fourth 2026-08-08 with the coreference map — `2026-08-08-world-address-ruling.md` §5.5) name **identical** states per corpus; capture a corpus's chain head outside the lock hold that captured its state → **unconstructible** through the build, and assert each epoch head member and the receipts' corpus-state identity describe **one** view. **Negative (ABA, limitation 7):** raw-move a corpus `A → B → A` within one capture → pre/post identities match and nothing detects the mixed scan — the raw-write bound, which is why the lock, not the check, carries the guarantee |
| X10 | Receipts — producer, retraction-map, certification-enumeration (amended 2026-08-03 at 5b's banking) **and coreference-reduction** (amended 2026-08-08, `2026-08-08-world-address-ruling.md` §5.5) — resolve rule bindings against the held store only | for each receipt kind: un-hold its rule implementation → `unresolvable`, not `refuted`; install a newer rule beside it → still validates against the implementation it names, never revalidates against the newcomer (normative-contract §6); bare version string → `malformed` (world §5's contract, packaged). **For the coreference receipt, assert the extra consequence on the two outcomes this row owns — `unresolvable` and `malformed`:** un-hold its rule → `unresolvable`; raw-write a receipt naming a **bare version string** or a corpus rather than a corpus-state identity → `malformed`, decided with no corpus present and no rule held; and in **each** case assert the covered edges read **`indeterminate`** and a query expanding over one **refuses**. The third outcome, **`refuted`**, is reached only by rebuilding the reduction against the corpora the receipt names, so **X12 owns it** and asserts the same consequence there — this row does not restate that arm. The malformed arm is the one that would otherwise have no consequence anywhere — a permanently uncheckable receipt is the strongest reason to refuse, and reading it as `inactive` would let a forged record silently suppress an edge (that ruling's §5.5) |
| X11 | GC's two hard rules hold | GC act naming `current`'s epoch → refused; delete another epoch → act's report names the snapshots/receipts severed; before deletion the epoch resolves by identity |
| X12 | The retraction map, the certification inventory **and the coreference reduction** are complete over the epoch's coverage at its recorded states, and their receipts can refute an incomplete one (amended 2026-08-03 at 5b's banking; **coreference added 2026-08-08**, `2026-08-08-world-address-ruling.md` §5.5) | standing retraction in-coverage at build → in the map; out-of-coverage → absent, and the coverage declaration states the bound (5a C3's shape, at the artifact layer); an in-coverage `instrument-certification` at build → in the address map and the inventory projection. an in-coverage `coreference-attestation` at build → inside the pair's published balance; out-of-coverage → outside it, with the coverage declaration stating the bound. **The receipt is the completeness check, not the packaging hash:** for each receipted projection — retraction map, certification inventory, coreference reduction — omit an in-coverage entry and repackage into an internally consistent epoch → receipt validation, rebuilding with the named binding against corpora at the named states, **refutes** it; a corpus no longer standing at a named state → `unresolvable`, never a pass. **For coreference, assert the reduction is checked and not merely the membership:** leave every attestation in place and publish a **wrong balance** for a pair → the rebuild **refutes**. Then assert the belief boundary — a **refuted** coreference receipt moves **no** `belief_input_digest`, unlike the producer snapshot, and its consequence is that the covered edges read **`indeterminate`** |

## 11. Limitations

1. **The registry was unanchored until §9 landed** *(closed 2026-08-23; see the
   end of this item)*. As written: deleting an admission record —
   or a future head record — is undetectable. The anchor carrier arrives
   before the anchor; the bootstrap order is deliberate and stated on arrival
   (the §8.7 pattern), and closing it is the log design's job (repro §9), not
   this design's. **Designed 2026-08-03**
   (`2026-08-03-tamper-evident-log-design.md`): the world chain registers the
   registry as part of the world root's surface, exported heads anchor the
   world chain from outside, and the closure lands at implementation with its
   L1–L13. **Closed 2026-08-23** by world-index slice 3
   (`2026-08-22-log-verification-design.md`), discharging conformance cut 8:
   the registry lives inside the world root's registered surface, so deleting
   an admission or a log-head record is a removal replay refutes against a
   surviving anchor, and the explicit anchor act plus exported head artifacts
   supply anchors from outside the deletable set. Two bounds survive the
   closure and are not this limitation's: detection is quantified over
   **surviving observers** — a coordinated truncation with no exported holder
   is undetected, which is that design's own pinned negative — and a rewrite of
   the tail beyond the maximal anchor stays the unanchored residue, bounded by
   anchor cadence.
2. **Interim publication is neither crash-atomic nor durably pointed.** Until
   composition-root adoption, the writer is best-effort
   create-then-pointer-replace; after a
   durability failure `current` may still name the old epoch, may be missing, or
   may name incomplete content — not merely sit intact beside a partial epoch.
   X2 is gated; a partial epoch is detectable (X1's audit) and every cleanup is
   manual.
3. **The bound is visible; staleness is not measured.** An epoch names the
   states it read, nothing more. Nothing bounds corpus changes since the build,
   and no freshness claim is derivable from the epoch alone.
4. **Single live host is assumed, not enforced.** Two hosts publishing into
   synced world roots will corrupt each other in ways this design does not
   detect; the cold-arrival classification (§2) is the only cross-host story.
5. **Manifest honesty is authored.** An undeclared fork is caught only when both
   corpora are live in one world (X5); nothing verifies `forked_from` against
   history.
6. **GC policy is unwritten.** Only §9's two hard rules exist; what to retain,
   for whom, on what schedule is future consumer policy.
7. **A noncooperating ABA writer defeats coherent enumeration.** A raw writer
   moving a corpus `A → B → A` within one capture yields matching pre/post
   identities over a mixed scan, so a published epoch can carry an incoherent
   view of that corpus. The lock protects against cooperating writers only;
   X9's negative pins the residue.

## 12. Open questions

- **Log-head records.** **Closed 2026-08-03**: shape and cadence are ruled by
  `2026-08-03-tamper-evident-log-design.md` — subject-bound corpus-only records
  (its §5, and §4 here as amended), epoch-cadence anchoring plus the explicit
  anchor act, and **never per-transaction write-through** (its §2).
- **On-disk format of the maps.** Identity runs over prescribed projections, so
  any canonical serialization serves; choosing one (and its scale behavior at
  mm30, per the ledger's measurement gate) is an implementation-plan decision.
- **Rules-store distribution.** Single-host holding is ruled; whether rules are
  ever distributed between installations (and what "held here" means then) waits
  for a second installation to exist.
