---
title: Foundations
status: living
created: 2026-08-08
updated: 2026-09-05
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-09-04-write-permits-design.md
  - ../designs/2026-09-05-facet-contracts-design.md
  - ../designs/2026-09-05-writer-session-design.md
  - ../designs/2026-09-09-session-routes-design.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../designs/2026-08-31-coordination-and-view-kinds-design.md
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
participates in the derivation. The executable derivation and its receipt are
specified by the [store-side holdings design](../designs/2026-08-24-world-index-holdings-design.md).

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

### Views and coordination are governed, not kernel

Two further tiers of record exist without joining the kernel: **views**
(`project`, `question`, `hypothesis`, `topic`, `theme`) — each a stored world
query plus a label, never a container — and **coordination** records (`task`,
`decision`, `note`), which are attributed acts. Both are minted through the
corpus-write adapter, so they carry provenance, enter the log, and are captured
by epochs; but they are declared by a **coordination contract** compiled into
`ProfileSpec` and versioned independently of the base contract, not by the
kernel. They are never world facts — no world address, no world-index map
membership — and never belief inputs: no coordination kind declares a
belief-bearing edge, and the contract declares no operator the consulted set
could name.

Identity at this tier is coordination-scoped. A `project` carries an opaque
durable identity minted the way a `corpus_id` is, and every other record is
addressed `(project identity, local id)` — both halves opaque, with names and
handles as content that lookup never consults, so renaming breaks no
reference. Editing mints an immutable **revision** through a family that takes
one or more predecessor tips; an address resolves to its one standing tip or
refuses naming every tip, and divergence is repaired by one revision
superseding them all. The query a view stores is `science.view-query.v1` — a
small, closed selector grammar evaluated at a named epoch, deliberately not a
query engine. The [coordination-and-view-kinds
design](../designs/2026-08-31-coordination-and-view-kinds-design.md)
specifies all of this and is implemented through conformance cut 14. Its 2026-09-02
§11 amendment leaves W17's intent-position evidence with `publish`, the first
operation that can define an honest multi-root proof shape; cut 14 covers the
ordinary revision family and builds no caller-asserted substitute.

### Ownership follows the nature of the rule

| Owner | Owns |
|---|---|
| `nodes` | Generic entity/relation storage, relation closure, traversal, and mechanism. It knows no scientific semantics. |
| `beliefs` | Kernel kinds, closed relation signatures, identity rules, eligibility, belief policy, and cross-node scientific invariants — this repository (named `science` until 2026-08-30; the designs' "Science" names the whole stack). |
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

Base and domain contracts also declare facet payload schemas; profile
compilation merges those declarations into the per-kind runtime specifications.
The shipped Science base contract declares `empirical-observation`, including
its required `locator` and `attested_by` fields.

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

The kernel's typed records, admission and belief computation run: claim
construction and identity, the derived admission state, the assessment
admission gate, and `science.belief.v1` under an exact binding. Kernel §8.7's
recorded-mutation consequences now close through the mutation log's anchor
carriage and verification and cut 12's successor admission. Every write entry
point now receives a bound authority, checks its permit before effects, and
reads its actor from that authority. The agentic surface has an approved [user
and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md);
its writer session is implemented and discharged as conformance cut 19
([writer-session design](../designs/2026-09-05-writer-session-design.md)) — the
attended session, its session ledger and claim protocol, the invocation-bound
scoped writer, and reconciliation. Its [session routes](../designs/2026-09-09-session-routes-design.md)
add ledgered run and holdings access, the public store identity reader, and
kernel-scoped reference rules. Its daily surface and autonomy
sub-projects are not yet implemented; salvage remains undesigned. The [adoption ledger's current-state
summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-08)
is the complete statement of what is built and what remains.

## Open edges

See [Foundations](open-questions.md#foundations) in the consolidated question
list for the unresolved non-empirical route, the kernel-adjacent structures, Science profile distribution, and why
pre-run fixation is not pre-registration. The empirical-observation facet's
payload contract is implemented and discharged at cut 20, as specified by the
[facet-contracts design](../designs/2026-09-05-facet-contracts-design.md#6-the-empirical-observation-contract).

## References

- [Epistemic kernel: invariant, structure, and G1–G9](../designs/2026-08-02-epistemic-kernel-design.md#2-the-invariant)
- [Substrate consolidation: S1–S8 and ownership](../designs/2026-08-02-substrate-consolidation-design.md#2-the-boundary-ruling--split-by-nature)
- [Write permits: authority at every write entry point, E1–E8](../designs/2026-09-04-write-permits-design.md#7-guarantees)
- [Facet contracts: declarations, the compiled registry, the bearer invariant, F1–F8](../designs/2026-09-05-facet-contracts-design.md#8-guarantees)
- [Writer session: the session ledger, the scoped writer, and `corpus-write` as an operation, J1–J11](../designs/2026-09-05-writer-session-design.md#7-guarantees)
- [Session routes: store identity, ledgered run and holdings routes, and reference rules](../designs/2026-09-09-session-routes-design.md)
- [Domain extension: D1–D10 and profile compilation](../designs/2026-08-04-domain-extension-boundary-design.md#3-the-ownership-split)
- [Formal model: the thirteen kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-thirteen-kernel-kinds)
- [Adoption ledger: clean-start ruling](../designs/2026-08-03-redesign-adoption-ledger.md#0-the-clean-start-ruling-2026-08-04)
