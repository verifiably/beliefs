---
title: Foundations
status: living
created: 2026-08-08
updated: 2026-09-26
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
  - ../designs/2026-09-20-conformance-cut-35.md
  - ../designs/2026-08-31-coordination-and-view-kinds-design.md
  - ../designs/2026-09-12-composite-claims-design.md
  - ../superpowers/specs/2026-09-22-publication-records-design.md
  - ../plans/2026-09-23-conformance-cut-39-results.md
  - ../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md
  - ../designs/2026-09-24-live-query-evaluation-design.md
---

# Foundations

## In brief

At the centre of the kernel is one rule: **only an analysis of data we actually
hold, shown to give the same result when run again from scratch, can count as
evidence about the world.**
Everything else is arranged to protect that rule. There is a small, fixed set of
record kinds, and only one of them — the assessment — has a path into belief.
Contracts say what each record may contain, and the system refuses anything that
does not fit rather than trying to fix it.

- **One route to belief.** An assessment of a claim, backed by a verified re-run
  over held data. Papers, notes, and tasks have no route.
- **"Held" means we can produce the exact bytes.** A dataset we can only name,
  not produce, is *declared* and never counts.
- **Fourteen kernel record kinds, no more.** Beliefs, indexes, projects, and
  tasks are views or coordination records, not kernel kinds.
- **Each rule lives where its nature puts it.** Storage knows nothing about
  science; the kernel knows the scientific rules; domains add vocabulary.
- **Refuse, don't repair.** A sanctioned action produces a valid state or a
  refusal; audit reports writes that went around it.

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
world record minted by an act that dereferenced and hashed, at a `store`
location or, since cut 35, a canonical `url` — matches its
declared digest. The record is superseded, never expired; no age or clock
participates in the derivation. The executable derivation and its receipt are
specified by the [store-side holdings design](../designs/2026-08-24-world-index-holdings-design.md);
the `url` arm and the `acquisition` operation that mints a dataset from it by
the [url-retrieval cut](../designs/2026-09-20-conformance-cut-35.md).

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

### The fourteen world-record kinds

The formal inventory contains fourteen kernel kinds:

| Group | Kinds | Purpose |
|---|---|---|
| Epistemic | `proposition`, `source-assertion`, `assessment`, `composite` | Represent a typed claim, what a source said about it, and a run-derived result that may bear on it; and, as a `composite`, the **structure** a set of claims is drawn against — an explicit closed node set of `(sort, term)` pairs and members that are propositions named by claim identity, each read as a signed directed edge. Under the one shape, `dag`, the *absence* of an edge between two declared nodes is the record's assertion. A composite is belief-inert: its reading is derived, never stored, and never an input to belief. |
| Computation | `analysis-spec`, `run`, `verification` | Predeclare an analysis, capture one complete execution, and compare two executions immutably. |
| Materials | `dataset`, `source`, `holdings-observation` | Hold data or a literature corpus, and identify works within a corpus; and record, act-by-act, what was found at each held location. |
| Change and conformance | `retraction`, `instrument-certification` | Subtract standing without deletion, by one of three target arms — a node, an embedded route, or (since cut 34) a producer semantic snapshot — and demonstrate that an executable instrument conforms to a contract. |
| Identity | `coreference-attestation` | Record, with attribution, that two differently-identified records are believed to name one thing — a graded claim, not a merge. |
| Operations | `act-report` | Record, inertly, one boundary operation's member acts and their outcomes — the terminal record of an opened operation, or the refusal record of a run request rejected before one can open. |

Computed beliefs, world indexes, hypotheses, questions, tasks, and other views
are not additional kernel kinds. A view has no independent authority: it is a
function of named records and configuration. A **composite** is the one thing on
that line that *is* a kind, and the reason is what it authors rather than
derives: a query cannot hold a closed node set, and it cannot assert that no
other direct edge holds among those nodes. Everything a composite makes
available beyond that — its reading, its exogenous and outcome nodes, any
neighbourhood around it — stays derived
([composite claims](../designs/2026-09-12-composite-claims-design.md),
[cut 32](../designs/2026-09-16-conformance-cut-32.md)).

Things in the world — a gene, a cell line, a disease, a measured outcome — are
not kernel kinds either. They are **term referents**, named by the ontology's
own identifier (a sort's controlled vocabulary or an accession), and a claim
reaches them by reference, never by owning a record for them. The
predecessor's `concept`, `construct`, `variable` and `outcome` kinds have no
successor by design
([kernel §4.3](../designs/2026-08-02-epistemic-kernel-design.md#43-outside-the-kernel),
[§4.4](../designs/2026-08-02-epistemic-kernel-design.md#44-complete-accounting-of-the-50-core-kinds)):
prose *about* a referent — what a gene is, why a variable was chosen — lives
in belief-inert note records attached to the referent, and a domain pack
supplies vocabulary and sorts, not a `concept` kind.

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
small, closed selector grammar, deliberately not a query engine. It is
evaluated either at a named epoch (`evaluate_query`, cut 28) or live over the
corpora's current state for attention reads such as a work queue
(`evaluate_live_query`, cut 41); see
[reading the world](identity-world-and-change.md#reading-the-world-at-an-epoch-or-live).
The [coordination-and-view-kinds
design](../designs/2026-08-31-coordination-and-view-kinds-design.md)
specifies all of this and is implemented through conformance cut 14.

The coordination contract's version 2 adds two more coordination kinds,
`publication` and `publication-binding`, which record a published view and bind
a view and destination to what was published. Only the publish act mints them
([publication-records design](../superpowers/specs/2026-09-22-publication-records-design.md);
[cut 39 results](../plans/2026-09-23-conformance-cut-39-results.md)); see
[publishing a view](writes-operations-and-publication.md#publishing-a-view).

### Ownership follows the nature of the rule

| Owner | Owns |
|---|---|
| `nodes` | Generic entity/relation storage, relation closure, traversal, and mechanism. It knows no scientific semantics. |
| `beliefs` | Kernel kinds, closed relation signatures, identity rules, eligibility, belief policy, and cross-node scientific invariants — this repository (named `science` until 2026-08-30; the designs' "Science" names the whole stack). |
| `domains` | Namespaced sorts, operators, dimensions, facets, and vocabulary bindings. A domain may extend interpretation, not redefine kernel relations. |
| `practices` | Procedures and workflows that use the model without owning scientific vocabulary. |
| `atoms` | Durable atomic filesystem effects, including the pre-mutation registration boundary. |

Domain and practice packs live inside this repository: domains under
`python/src/beliefs/domains/`, where the biology pack is the first shipped one,
and practices as `PRACTICE.yaml` documents that `beliefs.contract.practice`
parses, with no pack shipped yet. `nodes` and `atoms` are their own
repositories. Two layers sit above the kernel,
each its own repository: `science`, the daily surface of commands people and
agents use, and `autonomy`, which runs that surface unattended. Neither owns a
record kind or any storage: every durable thing they produce is a governed
record written through a `beliefs` writer
([layer design §3](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md#3-repositories-and-names)).

Only one module, `beliefs/root.py`, imports `atoms`: the composition root binds
the certified engine and hands every other module a seam. The rule is tested
(`test_capability_boundary.py`).

Composition happens at the kernel's boundary. There is no compatibility layer with
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
- [Writes, operations, and publication](writes-operations-and-publication.md)
  describes the permit-bound doors every write goes through.

## Current state

- **Built:** the fourteen kernel kinds with typed construction and identity; the
  derived admission state, the assessment admission gate, and
  `science.belief.v1` under an exact binding; the mutation log's anchoring and
  verification and successor admission, which close kernel §8.7's
  recorded-mutation consequences; facet contracts and the empirical-observation
  payload (cut 20); views and coordination records (cut 14) with both query
  evaluators; bound authority at every write entry point (cut 17); and the
  writer session, its routes, and session selection
  ([writer-session design](../designs/2026-09-05-writer-session-design.md),
  [session routes](../designs/2026-09-09-session-routes-design.md)).
- **Above the kernel:** the `science` daily surface has its command framework
  and belief-path commands and part of its coordination commands; `autonomy` is
  not started; salvage has no design.

The [adoption ledger's current-state
summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
is the complete statement of what is built and what remains.

## Open edges

See [Foundations](open-questions.md#foundations) in the consolidated question
list for the unresolved non-empirical route, the kernel-adjacent structures, Science profile distribution, and why
pre-run fixation is not pre-registration. The empirical-observation facet's
payload contract is implemented and discharged at cut 20, as specified by the
[facet-contracts design](../designs/2026-09-05-facet-contracts-design.md#6-the-empirical-observation-contract).

## References

- [Epistemic kernel: invariant, structure, and G1–G9](../designs/2026-08-02-epistemic-kernel-design.md#2-the-invariant)
- [Substrate consolidation: S1–S9 and ownership](../designs/2026-08-02-substrate-consolidation-design.md#2-the-boundary-ruling--split-by-nature)
- [Write permits: authority at every write entry point, E1–E8](../designs/2026-09-04-write-permits-design.md#7-guarantees)
- [Facet contracts: declarations, the compiled registry, the bearer invariant, F1–F8](../designs/2026-09-05-facet-contracts-design.md#8-guarantees)
- [Writer session: the session ledger, the scoped writer, and `corpus-write` as an operation, J1–J11](../designs/2026-09-05-writer-session-design.md#7-guarantees)
- [Session routes: store identity, ledgered run and holdings routes, and reference rules](../designs/2026-09-09-session-routes-design.md)
- [Domain extension: D1–D10 and profile compilation](../designs/2026-08-04-domain-extension-boundary-design.md#3-the-ownership-split)
- [Formal model: the fourteen kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-fourteen-kernel-kinds)
- [Adoption ledger: clean-start ruling](../designs/2026-08-03-redesign-adoption-ledger.md#0-the-clean-start-ruling-2026-08-04)
