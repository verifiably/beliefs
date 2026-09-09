---
title: Identity, world, and change
status: living
created: 2026-08-08
updated: 2026-09-05
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
  - ../designs/2026-08-26-world-index-intent-boundary-design.md
  - ../designs/2026-08-27-conformance-cut-11.md
---

# Identity, world, and change

## TL;DR

Science treats identity, location, human names, and historical continuity as
different things; corrections add immutable records, indexes derive named views,
and anchored mutation chains make some removals detectable without pretending
that history is impossible to destroy.

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
only inside its stated coverage and state.

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
transaction. Whether the removed record was a *failing verification* resolves
only where the caller supplies historical bytes, and even then by the path the
held copy claims rather than by digest.

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

The world side runs end to end at the registry level: the authoritative world
root, corpus manifests and corpus-state identity, and the append-only registry
with lifecycle status and configured presence; epoch publication with its four
derived maps, fixture-bound receipts, bounded reads and whole-epoch GC; the
mutation log's anchor carriage and its verification — the log-head record and
head artifact, the explicit anchor act, the four-outcome evaluator, replay with
its removal policy pass, the audit and replica-arrival boundaries, the
genesis↔mirror agreement check, and the ordered-cuts predicate; the root
lifecycle and store substrate — the fail-closed writer state, the lifecycle
commands, `restore_root`, the fork acts with act-derived `forked_from`, and
genesis-bound store subjects; and verified store-side holdings with their
intent-bearing acts. Global resolution remains designed, and the address ruling
still governs the eventual derived views: labels are computed on read,
coreference is graded rather than merged, and storage duplication changes no
address. What the log still owes — event-level L8 and the L13 preimage resolver
— is listed with its owners in the
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-08).

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
