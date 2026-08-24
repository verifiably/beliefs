---
title: Foundations
status: living
created: 2026-08-08
updated: 2026-08-24
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-20-world-registry-design.md
  - ../designs/2026-08-20-conformance-cut-6.md
  - ../plans/2026-08-20-conformance-cut-6-results.md
---

# Foundations

## TL;DR

Science makes empirical belief a derived reading over a small typed kernel:
only reproduced assessments of held observations can enter it, and contracts
make invalid routes unconstructible at the boundary.

## Why it matters

The predecessor encoded scientific policy mostly as prose and after-the-fact
checks. The redesign moves the important distinctions into record types,
relation signatures, identities, and explicit inputs. Invalid states should be
refused before they become plausible records; raw writes remain detectable by
audit rather than silently repaired.

## Key ideas

### The epistemic invariant

**Only an assessment successfully reproduced from primary observations we
possess may affect empirical belief** (G1). A paper measures what someone wrote,
not the world, so a literature-derived `source-assertion` has no belief-bearing
edge. Literature remains useful for orientation, extraction, and corpus QA.

An artifact is **held** when its exact bytes can be produced on demand and named
by content identity. Held does not mean raw, public, inside Git, or present in
this checkout. A normalized or access-controlled dataset can be held; an
accession alone is not. Since 2026-08-10, heldness is derived: an artifact is
held under a declared coverage when an active **holdings observation** — a
world record minted by an act that dereferenced and hashed — matches its
declared digest. The record is superseded, never expired; no age or clock
participates in the derivation.

A dataset that records **which bytes it is** without those bytes being in hand is
**declared**: a real world entity, addressable and referenceable, and never
belief-eligible. Declared is the gap named rather than the gate weakened. A
dataset leaves it only when **every resource its declaration names** has an
observation whose digest matches what the record already claimed — never by
declaring, and never by a file merely being present (G9). A dataset's content
identity is that declaration, projected canonically: the declared digests,
deduplicated, sorted and digested, which is also its address.

The system guarantees representational eligibility and execution replay. It
does not guarantee honest observations, valid instruments, appropriate models,
or a correct match between estimand and claim.

### Closed routes, inert by default

Belief reads the closed relation `Assessment ─assesses→ Proposition`; it does
not inspect a growing roster of “evidence-like” record kinds. Run inputs are
role-typed:

- `observes` names held data with an empirical-observation facet and can confer
  eligibility;
- `reads` names corpora, ontologies, references, or configuration and never
  confers eligibility;
- `transforms` and `produces` carry dataset lineage without becoming evidence
  by themselves.

This makes inertness the default. Adding a record kind or domain facet does not
accidentally create a new route to belief.

### The thirteen world-record kinds

The formal inventory contains thirteen kernel kinds:

| Group | Kinds | Purpose |
|---|---|---|
| Epistemic | `proposition`, `source-assertion`, `assessment` | Represent a typed claim, what a source said about it, and a run-derived result that may bear on it. |
| Computation | `analysis-spec`, `run`, `verification` | Predeclare an analysis, capture one complete execution, and compare two executions immutably. |
| Materials | `dataset`, `source`, `holdings-observation` | Hold data or a literature corpus, and identify works within a corpus; and record, act-by-act, what was found at each held location. |
| Change and conformance | `retraction`, `instrument-certification` | Subtract standing without deletion and demonstrate that an executable instrument conforms to a contract. |
| Identity | `coreference-attestation` | Record, with attribution, that two differently-identified records are believed to name one thing — a graded claim, not a merge. |
| Operations | `act-report` | Record, inertly, one boundary operation's member acts and their outcomes — the terminal record of an opened operation, or the refusal record of a run request rejected before one can open. |

Computed beliefs, world indexes, hypotheses, questions, tasks, and other views
are not additional kernel kinds. A view has no independent authority: it is a
function of named records and configuration.

### Ownership follows the nature of the rule

| Owner | Owns |
|---|---|
| `nodes` | Generic entity/relation storage, relation closure, traversal, and mechanism. It knows no scientific semantics. |
| `science` | Kernel kinds, closed relation signatures, identity rules, eligibility, belief policy, and cross-node scientific invariants. |
| `domains` | Namespaced sorts, operators, dimensions, facets, and vocabulary bindings. A domain may extend interpretation, not redefine kernel relations. |
| `practices` | Procedures and workflows that use the model without owning scientific vocabulary. |
| `atoms` | Durable atomic filesystem effects, including the pre-mutation registration boundary. |

Composition happens at Science's boundary. There is no compatibility layer with
the predecessor: legacy material is reproduced through the ordinary typed
authoring path, not mechanically migrated or inferred from prose.

### Contracts compile into profiles

A corpus manifest selects exactly one Science base contract and a mapping of
domain contracts. Their content identities compile into a `ProfileSpec`, then
into per-kind runtime specifications. Compiled registries are derived products,
never parallel authorities.

Contracts carry meaning-bearing declarations; the corpus manifest pins which
ones apply. A domain facet can affect identity only where its contract says so,
and can affect belief only when the derivation actually reads it. Merely
activating a domain does not perturb an unrelated belief.

### Valid transitions refuse; audit detects bypasses

Sanctioned actions take a valid configuration to another valid configuration or
return `Refused`. They do not guess, repair, or downgrade malformed input. A raw
filesystem write is outside that transition boundary; audit may then report a
structural or integrity finding, but it mints nothing and performs no repair.

## How it connects

- [Claims and belief](claims-and-belief.md) specifies typed propositions,
  assessment eligibility, independence, and the belief-policy result.
- [Identity, world, and change](identity-world-and-change.md) explains content
  identity, corpus/world configuration, standing, and the mutation log.
- [Computation and reproducibility](computation-and-reproducibility.md) defines
  the run closure that makes an assessment eligible.
- [Contracts and adoption](contracts-and-adoption.md) explains frozen guarantees
  and which parts of these boundaries are executable today.

## Current state

The adoption ledger records nine landed slices. Cut 6 implements the
authoritative world root, manifest, corpus-state identity, and append-only
registry core; cut 7 adds epoch publication, the four derived maps and their
receipts, bounded reads, whole-epoch GC, and anchor carriage, merged into
`main` on 2026-08-22; cut 8 adds anchor **verification** — the anchor act, the
four-outcome log evaluator, replay with its removal policy pass, the audit and
replica-arrival boundaries, and the genesis↔mirror agreement check — discharged
2026-08-23 and merged into `main` the same day; cut 9 adds the **root
lifecycle and store substrate** — the fail-closed writer state, the lifecycle
commands, `restore_root`, the fork acts, and genesis-bound store subjects —
discharged 2026-08-23 and merged into `main` on 2026-08-24. Global resolution
remains designed, and so do the log slice's named deferrals: intent
qualification, the preimage-backed classification of a removed verification,
and event-level cross-chain order — the fork/replica/restore arms closed with
cut 9, and the store's holdings reads are the next slice's.

## Open edges

See [Foundations](open-questions.md#foundations) in the consolidated question
list for the unresolved non-empirical route, the empirical-observation facet
contract, the kernel-adjacent structures, Science profile distribution, and why
pre-run fixation is not pre-registration.

## References

- [Epistemic kernel: invariant, structure, and G1–G9](../designs/2026-08-02-epistemic-kernel-design.md#2-the-invariant)
- [Substrate consolidation: S1–S8 and ownership](../designs/2026-08-02-substrate-consolidation-design.md#2-the-boundary-ruling--split-by-nature)
- [Domain extension: D1–D10 and profile compilation](../designs/2026-08-04-domain-extension-boundary-design.md#3-the-ownership-split)
- [Formal model: the thirteen kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-thirteen-kernel-kinds)
- [Adoption ledger: clean-start ruling](../designs/2026-08-03-redesign-adoption-ledger.md#0-the-clean-start-ruling-2026-08-04)
