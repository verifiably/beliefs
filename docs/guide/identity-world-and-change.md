---
title: Identity, world, and change
status: living
created: 2026-08-08
updated: 2026-09-26
sources:
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-08-world-address-ruling.md
  - ../designs/2026-08-03-correction-lifecycle-design.md
  - ../designs/2026-08-03-world-index-packaging-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-20-world-registry-design.md
  - ../designs/2026-08-20-conformance-cut-6.md
  - ../designs/2026-08-20-world-index-slice-2-design.md
  - ../designs/2026-08-20-conformance-cut-7.md
  - ../designs/2026-08-22-log-verification-design.md
  - ../designs/2026-08-22-conformance-cut-8.md
  - ../designs/2026-08-23-world-index-root-lifecycle-design.md
  - ../designs/2026-08-23-conformance-cut-9.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../designs/2026-08-24-conformance-cut-10.md
  - ../designs/2026-09-14-conformance-cut-28.md
  - ../designs/2026-09-14-conformance-cut-29.md
  - ../designs/2026-09-15-conformance-cut-30.md
  - ../designs/2026-08-26-world-index-intent-boundary-design.md
  - ../designs/2026-08-27-conformance-cut-11.md
  - ../designs/2026-09-09-conformance-cut-23.md
  - ../designs/2026-09-10-conformance-cut-24.md
  - ../designs/2026-09-10-conformance-cut-25.md
  - ../designs/2026-09-13-conformance-cut-27.md
  - ../designs/2026-09-24-live-query-evaluation-design.md
  - ../superpowers/specs/2026-09-21-event-level-l8-design.md
  - ../superpowers/specs/2026-09-21-l13-preimage-design.md
---

# Identity, world, and change

## In brief

Every record has an identity computed from what it means, not from where it is
stored or what it is called. All collections of records together form one
**world**; to answer a question across them, the system builds an **epoch** — a
frozen, published index of exactly which collections, in which states, it
covers — and every answer names its epoch, or for a live read, the states it
captured. Records are never edited
in place: a better version **supersedes** the old one and a withdrawal
**retracts** it, both as new records. Each collection keeps a hash-linked log of
its changes, so an unrecorded deletion or a rewrite can be detected as long as
someone outside
kept a copy of the log's head.

- **Meaning, address, name, continuity, and location are five separate
  things.** Moving a file or renaming a label never changes an identity.
- **One world; projects are views.** A project selects part of the world; it is
  not a separate universe.
- **Answers are pinned.** A world read names its epoch, or for attention reads,
  the exact states it captured. There is no silent "latest".
- **Corrections add, never erase.** A record's standing is calculated from the
  retractions that target it, not stored as a flag.
- **Tampering is detectable, within limits.** An outside observer's copy of the
  log head exposes truncation or rewriting; losing every copy cannot be detected
  from nothing.

## Why it matters

A content hash alone cannot say whether two records mean the same thing, where
one is stored, or whether a corrected record continues an earlier scientific
object. Likewise, overwriting or deleting a disputed result erases the evidence
needed to understand later conclusions. The redesign assigns each concern an
explicit mechanism and makes every answer name the world state against which it
was computed.

## Key ideas

### There is one world; projects are views

The world is the union of admitted corpora and world-level records. A project
selects and coordinates part of that world but does not create a separate
epistemic universe. Cross-corpus questions therefore resolve through an
explicit world index rather than by searching whichever checkout happens to be
open.

A corpus has an opaque, durable `corpus_id` and a canonical manifest. Its state
identity commits to the whole manifest and the sorted identities of its nodes.
Changing a profile, adding a node, or changing a node identity produces a new
corpus-state identity; the durable corpus identity remains.

### Identity is not one field

The model keeps five ideas separate:

| Concept | Meaning |
|---|---|
| Semantic or content identity | The digest of the kind-specific meaning-bearing basis. |
| Canonical address | The stored lookup key, `kind:<basis-digest>`. |
| `uid` continuity | Which historical scientific object this record continues. |
| Label | A human-facing name, computed on read and never stored. |
| Location | Where bytes happen to be held. It is identity-inert. |

Every kind declares its own identity basis. Presentation fields, cache state,
filesystem paths, and rendered labels do not enter that basis. A genuinely different
scientific object receives a new identity and an explicit relationship to what
came before. A correction to identity-bearing metadata can change the canonical
address while preserving `uid` continuity and deprecating the old address.

### The world index is a named, covered view

The world root holds an authoritative registry for corpus admission and
terminal status. Derived immutable epochs index an explicit set of corpus
states and world-level records through four maps:

- canonical address to one record;
- input record to its producers;
- target record to its retractions;
- endpoint pair to its coreference balance.

An epoch's packaging identity commits to its coverage and derived contents. A
mutable “current epoch” pointer is an operational convenience only: belief
binds to an explicit producer-snapshot identity, while epoch read answers carry
the packaging identity and coverage they came from. An older epoch may answer
only inside its stated coverage and state. Retracting the current epoch's
snapshot with no successor makes every world read bound to `current_epoch`
refuse until a new epoch is built — intended: `current_epoch` silently
skipping a retracted epoch is the implicit resolution the narrowing
guarantee's negative forbids. The same snapshot retraction makes every
receipt covering the writing corpus `unresolvable` until a fresh epoch is
built, the successor's included, since the retracting write moves that
corpus's state.

Open a cross-corpus read with `open_world_view(world, published_epoch)`. It
captures each present corpus against that explicit epoch's address map before
serving any answer. `WorldReadView` follows the same adjacencies across corpus
boundaries; a plain `ReadView` truncates at its corpus edge.

### Reading the world: at an epoch or live

A view's query can be evaluated two ways, and the difference is deliberate.

- **At an epoch** — `evaluate_query` over a `WorldReadView`. The answer is bound
  to a published epoch and refuses `corpus-drifted` once a covered corpus moves
  past it. Belief inputs and publication read this way, because their answers
  must be reproducible.
- **Live** — `evaluate_live_query(world, query)`. The answer covers every
  corpus the registry admits with no terminal status, captures each one inside
  its own hold, and refuses a damaged corpus rather than omitting it. It returns
  a `LiveSelection` stamped by the corpus states it captured, never by an epoch,
  so no consumer can mistake it for an epoch-bound answer. A work queue reads
  this way, so a user sees their own new record without anyone publishing an
  epoch first (Z1–Z5, cut 41;
  [live-query design](../designs/2026-09-24-live-query-evaluation-design.md)).

### Correction is additive

Records are immutable. **Supersession** says that a replacement continues or
updates an earlier object. **Retraction** subtracts the target's standing at
read time without changing the target. Retractions identify their exact target,
actor, grounds, and authority; their graph must be acyclic across the local
corpus and imported world context.

A retraction can itself be countered by another retraction. Readers calculate
standing from the active graph rather than trusting a mutable status bit. The
enumerated retraction closure and its digest enter derived answers so that
changing the visible correction history changes the answer identity.

### Mutation history is detectable relative to observers

Each corpus and the world root has a reserved, hash-linked mutation chain.
Boundary operations append durable stages:

- `registered` before a transaction is applied;
- `settled(committed|rolled-back)` when it completes;
- `intent` before a boundary-mediated destructive attempt.

Log entries retain identities and digests, not copies of deleted bytes. Heads
are anchored outside their own deletable set: corpus heads can be observed by
the world registry or an epoch, while the world head needs an external export.
Verification reports `validated`, `refuted`, `unresolvable`, or `malformed`
against an explicit observer set.

That verifier is now built. One read-only evaluator judges a root's chain in
four steps — structure, anchors, pending, replay — and both the audit act and
the verified replica-arrival act call it rather than reimplementing it. Replay
walks the registered surface from the genesis baseline and compares in both
directions, so a record the timeline never produced is a disagreement, and a
removal inside that surface emits a finding naming the path and the removing
transaction. Whether the removed record was a *failing verification* is decided
by matching the removed state's digest against a held copy or surviving preimage
bytes; where neither survives, the finding says so (`removal-unclassified`)
rather than guessing (L13, cut 37).

Events on different chains can also be ordered, within what the anchors can
witness. An event is `(corpus_id, entry_digest)`; `root.event_order` answers
`a-precedes-b`, `b-precedes-a`, or `unordered`, and says `unordered` when the
available captures cannot tell (L8, cut 36).

This is deliberately bounded. A surviving anchor can expose truncation or
rewriting; destruction of a root and every observer cannot be detected from
nothing. An entry proves that an operation occurred through the boundary, not
that the operation was scientifically or administratively authorized.

## How it connects

- [Foundations](foundations.md) defines immutable records, ownership, and the
  transition/refusal boundary.
- [Claims and belief](claims-and-belief.md) uses semantic succession, standing,
  and an explicit world epoch in belief input closure.
- [Computation and reproducibility](computation-and-reproducibility.md) gives
  runs event identity and uses the mutation boundary to strengthen chronology.
- [Contracts and adoption](contracts-and-adoption.md) distinguishes these
  frozen guarantees from the smaller implemented conformance cut.

## Current state

- **World registry and epochs** (cuts 6–7): the authoritative world root,
  corpus manifests and corpus-state identity, the append-only registry with
  lifecycle status and presence, epoch publication with its four derived maps
  and receipts, bounded reads, and whole-epoch GC.
- **Root lifecycle and holdings** (cuts 9–10): the fail-closed writer state,
  lifecycle commands, `restore_root`, fork acts, and verified store-side
  holdings.
- **Reading across corpora** (cuts 23, 27, 28, 41): the explicit-epoch world
  read view, epoch import and audit, a world audit that reports a damaged corpus
  rather than refusing it, epoch-bound view-query evaluation, and live
  evaluation.
- **Addresses and coreference** (cuts 24, 25, 29, 30): graded coreference
  attestation and its balance; source and dataset addresses derived from their
  identifiers and content; attributed identifier correction; and `consolidate`
  reconciling divergent correction histories.
- **Correction** (cuts 4–5, 18, 33–34): supersede, revise, retract and import
  through the write boundary; managed deletion; retraction standing reaching the
  belief evaluator; and retraction of a producer's semantic snapshot.
- **The mutation log** (cuts 8, 36, 37): anchoring, the four-outcome
  verifier with replay, the event-level ordering relation, and digest-matched
  classification of removed records.
- **Not built:** rendered labels and the ambiguous-search refusal, which wait on
  the pinned authority snapshot (W8's remaining conflict, W9, W14); and L1's
  kill-at-stage and settlement-persistence arms and X2's persistence arm, which
  wait on the `atoms` certification of the publication path.

The address ruling governs the derived views: labels are computed on read,
coreference is graded rather than merged, and storage duplication changes no
address. Owners for everything not built are in the
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16).

## Open edges

See [Identity, world, and change](open-questions.md#identity-world-and-change)
for unresolved questions about which external authorities are accepted, whether a
coreference balance belongs in any audit, attester reliability, authority, epoch
retention, observer loss, whether a dataset's own standing is retractable, and
what chain verification costs at scale.

## References

- [World addressing guarantees W1–W16](../designs/2026-08-02-world-addressing-design.md#7-guarantees-and-how-each-is-tested)
- [The address ruling, and what it retired](../designs/2026-08-08-world-address-ruling.md#5-coreference-is-a-graded-claim)
- [Correction guarantees C1–C10](../designs/2026-08-03-correction-lifecycle-design.md#7-guarantees)
- [World-index guarantees X1–X12](../designs/2026-08-03-world-index-packaging-design.md#10-guarantees)
- [Mutation-log guarantees L1–L13](../designs/2026-08-03-tamper-evident-log-design.md#10-guarantees)
- [The log evaluator, its precedence, and its two boundaries](../designs/2026-08-22-log-verification-design.md#4-the-evaluator)
- [Per-kind world identity bases](../designs/2026-08-02-world-addressing-design.md#42-the-basis-ruled-per-kind)
