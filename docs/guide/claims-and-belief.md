---
title: Claims and belief
status: living
created: 2026-08-08
updated: 2026-08-29
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

Independence is derived from complete dataset-lineage closures. It is
three-valued—`independent`, `shared-source`, or `not-certified`—and pairwise, so
it cannot be represented honestly as fixed groups. Belief aggregation instead
builds a dependency graph and selects a maximum set of pairwise demonstrably
independent directional assessments. Dependent opposing assessments may reduce
a result toward the prior but cannot manufacture corroboration or cross the
prior.

### A belief is a reproducible view

A belief computation receives an exact
`PolicyBinding = (policy rule identity, implementation content identity)` as a
required argument. There is no default or implicit “latest” policy.

`science.belief.v1` returns an unbounded integer: a signed balance of unit-weight
directional assessments after the dependency and contestation rules. It is not
an odds, probability, confidence score, or stored record. Uniform weighting is
a declared limit: estimands and uncertainty lack the typed reference and
commensuration contract needed for study-design or precision weights.

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
Verified holdings are a governed stored kind — recorded per location by
intent-bearing acts and projected under a declared coverage — so an
observation's admission input is a system record rather than a supplied
argument. The survey and typing exercise remain hand-run measurements, not
conformance oracles. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-08-29)
states what remains.

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
- [External-review typing limits](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#2-the-typing-measurement)
