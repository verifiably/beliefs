---
title: Claims and belief
status: living
created: 2026-08-08
updated: 2026-09-16
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
  - ../designs/2026-08-05-review-disposition-and-conformance-cut-1.md
  - ../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md
  - ../designs/2026-08-07-multi-corpus-typing-exercise.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-09-conformance-cut-2.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../designs/2026-09-05-mm30-reproduction.md
  - ../designs/2026-09-12-estimand-typing-design.md
  - ../designs/2026-09-12-composite-claims-design.md
  - ../designs/2026-09-15-conformance-cut-31.md
  - ../designs/2026-09-16-conformance-cut-32.md
---

# Claims and belief

## TL;DR

A proposition is an immutable typed claim; empirical belief is a policy-bound
value computed only from eligible, directional assessments with demonstrated
independence—not from literature assertions or stored “current belief.”

## Why it matters

Free-text propositions make scope changes invisible and leave every consumer to
guess whether two sentences mean the same thing. Flat evidence scores also let
literature, duplicated analyses, or unavailable inputs become plausible-looking
belief. The redesign gives claim structure, eligibility, independence, and the
belief evaluator separate, explicit jobs.

## Key ideas

### A claim is typed by its operator

Choosing an `Operator` determines:

- the number and sort of its argument referents;
- which qualifier dimensions and restriction sorts it permits;
- whether polarity is meaningful;
- which claim layers it may inhabit.

Runtime contracts supply those declarations. The only route from a wire value
to an opaque `Claim` performs the profile-dependent checks once; downstream
code receives a value that has already been checked. An untypeable span creates
a typing-work item and no proposition—there is no placeholder operator or
degraded claim.

The supported qualifier fragment is intentionally flat: one restriction per
dimension with a quantifier. Disjunction, ranges, multiple restrictions on one
dimension, modality, and other unruled grammar are refused rather than hidden
in prose.

### Structure, not prose, determines identity

Claim identity hashes the canonical projection of the operator, sorted bound
arguments, qualifiers, polarity, and layer under `science.identity.v1`.
Rendered prose, `title`, and an optional authored `display_statement` are
identity-inert. A semantic edit therefore mints a new proposition linked by
`supersedes`; old assessments remain attached to the exact claim they assessed.

Contract releases do not enter claim identity. They do enter a belief's input
closure when their meanings were consulted, so an editorial contract successor
can leave the claim stable while moving the belief digest.

### Vocabulary is owned and earned

The Science base contract owns the closed claim grammar and kernel tags. Domain
contracts issue namespaced operators, sorts, dimensions, and vocabulary
bindings; they cannot redefine kernel relations or base tags.

A field reaches the base profile only when separately evolved corpora agree on
its vocabulary, exercise its declared values, and—decisively—some rule,
projection, invariant, or computation reads it. Agreement and exercise are
necessary, never sufficient. A divergent or readerless field does not
automatically become a domain vocabulary; it waits until a domain reader needs
it.

The base profile requires claim capability, not claim instances. A corpus with
no claims and no activated operator contracts can conform; if it records a
claim, that claim must type.

### Assessments are the only empirical route

An assessment is an immutable output derived from an analysis spec, run, and
proposition. It carries a scientific outcome (`supported`, `refuted`, or
`inconclusive`), the estimand copied from the frozen spec, applicability, and
the interpretation rule that produced the outcome.

It becomes eligible only when its run observes at least one held empirical
dataset, all run inputs are held, and an active clean-environment verification
admits it. Reproduction is an admission gate, not a strength score.

### The estimand is typed, and so is what the rule returns

Four belief-bearing fields were prose until cut 31
([design](../designs/2026-09-12-estimand-typing-design.md),
[cut](../designs/2026-09-15-conformance-cut-31.md)). What is typed is the
**structure** an estimand has; every vocabulary that fills it stays a domain
contract's.

- **Estimand.** Built against the typed claim it answers, never from the wire,
  and carrying that claim's identity. It names a contrast on one of the
  operator's argument slots — two levels, or a quantity with an additive
  increment — a measured quantity on a declared scale, a reference the estimate
  is read against, and a control structure: one identification term and an
  unordered set of conditioning members. The base contract owns the closed
  shape (`science.estimand.v1`: the contrast kinds, the scales, the uncertainty
  kinds); a domain contract declares, per operator, which sorts each member
  draws on. An estimand outside its claim's operator declaration is not
  constructible, and a fragment the grammar cannot express — three levels, a
  second measure, an attenuation pair — is **refused** rather than flattened.
- **Applicability.** A qualifier map over the target operator's declared
  dimensions, sorted exactly as a claim's qualifiers are, so
  `applicability == claim.qualifiers` is decidable in both directions. The
  empty map is admitted. A scope clause the operator declares no dimension for
  is refused at authoring, not coerced.
- **Estimate and uncertainty.** The interpretation rule returns a decimal
  estimate and typed uncertainty — an interval with a level, or a dispersion —
  on the **spec's** declared scale and reference, and nothing else. A float, a
  string, an interval that does not contain the estimate, a level outside
  `(0, 1)`, a negative standard error, or an attempt to move the scale or
  reference produces **no assessment** and a finding naming the violation. It
  never produces `inconclusive`, which is a scientific claim.

Structural match is checked where it can be: a spec whose estimand was built
against a claim other than the one its target record carries is refused at the
write boundary and at explicit import, and a raw-written mismatch is caught
under audit. That the measured quantity actually operationalizes the claim's
argument stays **authored** — the check is structural and does not pretend
otherwise.

Two predicates, `commensurable` and `co_scoped`, are exposed from
`beliefs.estimand`. Both are total and decidable; `science.belief.v1` reads
neither. Two specs on one claim with identical estimands and different
applicability maps are commensurable and not co-scoped, which is the
distinction a weighted successor policy will need and which this design
supplies without spending.

A record minted before the grammar is **refused under its own name and audited
under its own code**, never coerced: the transition is recreation, not
migration. The mm30 reproduction recreated its corpus, re-authored its spec,
and re-derived its belief from disk in a fresh process to the same value
(`../designs/2026-09-05-mm30-reproduction.md` §10).

Independence is derived from complete dataset-lineage closures. It is
three-valued—`independent`, `shared-source`, or `not-certified`—and pairwise, so
it cannot be represented honestly as fixed groups. Belief aggregation instead
builds a dependency graph and selects a maximum set of pairwise demonstrably
independent directional assessments. Dependent opposing assessments may reduce
a result toward the prior but cannot manufacture corroboration or cross the
prior.

### Composites: a structure over claims, and never a claim

A **composite** is the record for the structure a set of claims is drawn
against — a causal DAG, an inquiry's spine, the authored half of a patch
definition — added at cut 32
([design](../designs/2026-09-12-composite-claims-design.md),
[cut](../designs/2026-09-16-conformance-cut-32.md)).

**What one asserts.** Three things, all authored: a closed node set of
`(sort, term)` pairs; members that are propositions, named by claim identity
and read as signed directed edges under the domain contract's per-operator
declaration of which argument slot is the cause and which the effect; and,
under the one shape `dag`, that **no other direct edge holds among those
nodes**. That absence is what makes it a model rather than a list, and it is
why a saved query could not do this job. An edge's polarity is its *sign*, not
its presence: an inhibitory member is an edge like any other, and a cycle
through one refuses like any other cycle.

**How it is read.** Its reading is derived and stored nowhere: one row per
member, carrying that member's belief and the sorted set of identification
terms from the assessments the evaluator admitted for it. Every row's belief is
**the evaluator's own answer** for that member under the same arguments — the
reading calls the traced evaluator rather than re-deriving anything — so
withholding the policy implementation reads `NoBelief("unavailable-policy-unheld")`
and a member nothing assesses reads `NoBelief` with an empty set. A reading is
a pure function of its named arguments: two processes given equal arguments
agree byte for byte.

**It is never a belief input.** `assesses` keeps its one target kind, so an
assessment cannot name a composite; minting, superseding or deleting one leaves
every proposition's belief input digest byte-identical; and a claim *about* a
composite — that this DAG fits the data, a causal-discovery posterior over
structures — is model-conditional and has no empirical route, exactly as
before. A composite is amended by succession, never in place: a change to what
it asserts mints a successor linked by `supersedes`.

### A belief is a reproducible view

A belief computation receives an exact
`PolicyBinding = (policy rule identity, implementation content identity)` as a
required argument. There is no default or implicit “latest” policy.

`science.belief.v1` returns an unbounded integer: a signed balance of unit-weight
directional assessments after the dependency and contestation rules. It is not
an odds, probability, confidence score, or stored record. Uniform weighting is
still a declared limit, but since cut 31 it is no longer for want of a typed
reference: the estimand, its applicability, the estimate and the uncertainty
are typed, and `commensurable` and `co_scoped` give a weight table a key
domain. What is open is the **policy** — which weights, and whether its
constants are global or domain-scoped — and that is the successor belief
policy's to design. v1 reads none of it.

The answer has three top-level forms:

| Answer | Meaning |
|---|---|
| `Belief(value, belief_input_digest, policy_binding)` | The complete named closure was available and produced a value. A balanced directional set may legitimately yield `0`. |
| `NoBelief(reason)` | Computation cannot run here (`Unavailable`), found no eligible assessment, or found only non-directional outcomes. |
| `Refused(reason)` | The request or binding is malformed, contradictory, or fails its conformance fixtures. |

`NoEligibleAssessment` is not `Unavailable`: the first is a successful
computation that found no empirical basis; the second means required material is
not held here. Likewise, an empty selection never publishes `Belief(0)`, because
absence of evidence must not masquerade as a balanced result.

## What the corpus measurements established

The survey measured eight predecessor corpora containing 6,860 records. It
found a small shared vocabulary spine, substantial project-specific drift, and
that 307 of the 337 structured propositions were in mm30. These corpora share an
author and predecessor, so agreement is weak evidence; disagreement is the
stronger signal.

The later typing exercise used four configurations:

- A fitted, unsorted mm30 plan typed all **307 of 307** structured propositions.
  This demonstrates reach under fitted vocabulary, not independent validation.
- A modal-sorted mm30 plan typed **282 of 307**; **25** refused with
  `ArgumentSortMismatch`. The sorting rule was computed rather than
  independently chosen, and another rule can produce another 25. The refusal
  count survives the vocabulary-fitting objection but remains conditional on
  that rule.
- Post-acute-infection recorded no typed claim in 45 proposition-labelled
  records, and natural-systems recorded none in 5. The calculus was therefore
  exercised against one corpus, not three.
- No surveyed corpus recorded a qualifier, so the qualifier grammar remains
  unexercised by corpus data.

The admission pass added no base vocabulary. In particular,
`mechanistic_narrative` was not admitted as a base layer: all 13 records carrying
it were unstructured, so adding the layer would type no claim. Revisit only when
a corpus records a structured proposition carrying it.

## How it connects

- [Foundations](foundations.md) defines the closed `assesses` route and the
  contract/profile boundary.
- [Computation and reproducibility](computation-and-reproducibility.md) defines
  the run and verification needed for assessment eligibility.
- [Identity, world, and change](identity-world-and-change.md) explains semantic
  succession, standing, and the world inputs named by the belief digest.
- [Contracts and adoption](contracts-and-adoption.md) explains guarantees M1–M13,
  P1–P9, and the implemented conformance cut.

## Current state

Typed claim construction, profile compilation, canonical projection, identity,
decode, and Python/TypeScript parity are implemented. So is the belief seam:
the derived admission state, the assessment admission gate, the belief-input
closure digest, and `science.belief.v1` computed under an exact binding, with
the belief policy's P1–P9 and the admission ramp's G9 in cut 2's selection.
Since cut 33, retraction standing reaches that evaluator at the read:
assessments and verifications targeted by standing retractions leave its input
set, and standing route retractions retire lineage routes before certification.
Verified holdings are a governed stored kind — recorded per location by
intent-bearing acts and projected under a declared coverage — so an
observation's admission input is a system record rather than a supplied
argument. The survey and typing exercise remain hand-run measurements, not
conformance oracles. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
states what remains. The estimand, applicability, estimate and uncertainty are
typed as of cut 31, with the two commensuration predicates exposed and unread.
The `composite` kind is built as of cut 32: structures are recorded, read
through the traced evaluator, and inert to belief.

## Open edges

See [Claims and belief](open-questions.md#claims-and-belief) for the unresolved
binding-check lifecycle, entailment and estimand match, qualifier grammar,
vocabulary gaps, higher-order records, weighted belief, what records the loss of
a last held copy, and whether the nine † labels are adopted.

## References

- [Kernel G1–G9 and assessment aggregation](../designs/2026-08-02-epistemic-kernel-design.md#421-the-assessment-facet)
- [Typed claim calculus and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#6-m--the-typed-claim-calculus)
- [Domain contracts and D1–D10](../designs/2026-08-04-domain-extension-boundary-design.md#3-the-ownership-split)
- [Belief policy and P1–P9](../designs/2026-08-05-belief-policy-design.md#2-what-a-belief-policy-is)
- [Eight-corpus vocabulary survey](../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md#3-what-the-corpora-show)
- [Multi-corpus typing measurement](../designs/2026-08-07-multi-corpus-typing-exercise.md#3-results)
- [The mm30 reproduction measurement](../designs/2026-09-05-mm30-reproduction.md#3-the-path)
- [External-review typing limits](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#2-the-typing-measurement)
