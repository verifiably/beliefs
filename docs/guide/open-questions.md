---
title: Open questions
status: living
created: 2026-08-08
updated: 2026-09-05
sources:
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-09-05-mm30-reproduction.md
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-03-correction-lifecycle-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-03-world-index-packaging-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
  - ../designs/2026-08-05-review-disposition-and-conformance-cut-1.md
  - ../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md
  - ../designs/2026-08-08-world-address-ruling.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-17-conformance-cut-4.md
  - ../designs/2026-08-20-conformance-cut-6.md
  - ../designs/2026-08-20-world-index-slice-2-design.md
  - ../designs/2026-08-23-world-index-root-lifecycle-design.md
---

# Open questions

This page groups the material open edges that remain after later designs closed
or narrowed earlier questions. It is a navigation aid, not a new docket: follow
the cited source before deciding or implementing an item.

Two things are deliberately **not** here. A **limitation** — a bound the designs
state and accept, such as finite witnesses proving reachability rather than
correctness, or code-lineage independence staying an authored claim — is not a
design uncertainty and is not listed as one. Neither is **deferred
implementation**: a guarantee row awaiting code is work, not a question.

## Foundations

- **Non-empirical knowledge route.** Mathematical, algorithmic,
  model-conditional, proof, derivation, and simulation claims cannot satisfy the
  empirical `observes` route. Do they get a second eligibility and answer model,
  or remain outside computed belief? ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- ~~**Empirical-observation facet.** What demonstrates an acquisition boundary?~~
  **CLOSED 2026-09-05** by the
  [facet-contracts design §6](../designs/2026-09-05-facet-contracts-design.md#6-the-empirical-observation-contract).
- **Lineage-inherited empirical standing.** Should a derived dataset inherit
  empirical standing from observed ancestors, and what exact lineage proof
  would permit it? ([facet-contracts design §14](../designs/2026-09-05-facet-contracts-design.md#14-open-questions-this-design-files))
- **Kernel-adjacent structures.** Are inquiries, patch definitions, structural
  chains, and coverage searches new kinds or derived views over existing kinds?
  ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Science profile distribution.** Does the downstream profile live inside
  the `beliefs` distribution or in its own package? The durability composition
  route is closed: Science's Python composition root combines portable `nodes`
  with `atoms`; `nodes` does not adopt the Python-only engine.
  ([substrate question](../designs/2026-08-02-substrate-consolidation-design.md#12-open-questions))
- **Pre-run fixation is not pre-registration.** Science can guarantee that a
  spec was frozen before its run. Calling that *pre-registered* additionally
  claims it preceded data access, which needs external evidence. The two must
  not merge in the user-facing vocabulary.
  ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))

## Claims and belief

- **Binding-check lifecycle.** If vocabulary membership is checked separately,
  where is the receipt stored, how is it discovered or corrected, and may an
  unchecked claim be assessed? ([ρO1](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Entailment and estimand match.** Can evidence bear across related claims,
  and is estimand compatibility derived from claim entailment or governed by an
  independent typed relation? ([ρO3](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Qualifier grammar.** Quantitative restrictions, multiple restrictions,
  adjustment sets, modality, comparison, and disjunction remain outside the
  flat fragment. Adjustment placement depends separately on scientific target
  and identification method. ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions), [adjustment ruling](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#8-open-questions))
- **Which vocabulary a claim is typed under, and who names it.** The mm30
  reproduction typed its target under one of two pre-existing vocabularies
  because the other's sort discipline refused the target's concept→protein
  pair; a `claim` command must take the contract from the caller or the
  corpus manifest and never choose one to make a claim type. Where that
  binding lives — the manifest's domain pins, a session default, or an
  argument — is the layer design's sub-project 4 to decide.
  ([reproduction record](../designs/2026-09-05-mm30-reproduction.md#5-questions))
- **Vocabulary gaps.** A population vocabulary, term-synonym resolution, and
  the namespace and ownership of a general-purpose operator contract remain
  unsettled. The **layer** set is declared — `contracts/science/CONTRACT.yaml`
  fixes it and editing it re-identifies every claim — so what is open there is
  admission to it, under the survey's agreement-exercise-reader rule.
  ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions), [admission rule](../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md#4-ruling-admission-by-agreement-and-exercise))
- **Higher-order records.** Eleven authored mm30 records concern claims,
  analyses, decisions, or the record system. Their re-homing must be settled
  before claim arguments widen from external referents to internal records.
  ([review classification](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#24-the-eleven-k-records--a-classification-and-a-moratorium))
- **The assessment's `proposition` spelling.** The derived assessment value
  carries the spec's target and the stored facet the proposition record's
  corpus ref — two namespaces, excluded from the audit's comparison for that
  reason. The verification-publication design unifies the run member's
  spelling and leaves this one to the layer design's claim sub-project, which
  authors specs against typed claims.
  ([verification publication](../designs/2026-09-06-verification-publication-design.md#9-limitations))
- **Weighted belief.** Estimand typing needs an owner before study-design or
  precision weights can be compared; a successor must also decide whether any
  constants are global or domain-scoped. ([belief questions](../designs/2026-08-05-belief-policy-design.md#9-open-questions))
- **Losing the last held copy.** Nothing records the destruction of a final held
  artifact. The recorded-loss repair was withdrawn as premature and stays
  withdrawn, so the gap is a stated residue rather than an oversight.
  ([ρO2](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Whether the nine † labels are adopted.** The formal model froze none of
  them. Adopting commits the banked tables to a vocabulary; declining leaves the
  classifications as annotations. Cheap to decide now and expensive once the
  labels reach oracle prose.
  ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))

## Identity, world, and change

- **Which external authorities are accepted, and who decides.** Every rendered
  label and the ambiguous-search refusal resolve against a pinned local snapshot
  of an authority. How a snapshot is pinned, versioned, distributed and bumped —
  and whether a bump is an amendment act — is owed and undesigned.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Whether a coreference balance belongs in any audit.** A coreference edge is
  outside belief by construction, but an active edge standing at `1` with a
  contested history is a different object from one standing at `12` with none.
  Nothing currently surfaces the difference.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Attester reliability.** Every attestation carries unit weight, which is an
  honest default rather than a finding that attesters are equally reliable. The
  data collection that would inform per-source priors does not exist.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Authority and coordination.** The designs assume one writer and no access
  control; multi-writer semantics, authority to retract, and propagation of
  cross-project blockers still need concrete rules. The root lifecycle
  (2026-08-23) narrowed the accident half mechanically — a copy fails closed
  and two cooperative writers of one root are unconstructible, the sole
  writable exit a fork under a fresh identity — but who *may* write remains
  the open question. ([review writer question](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#8-open-questions),
  [root-lifecycle design](../designs/2026-08-23-world-index-root-lifecycle-design.md))
- **Storage and retention.** The epoch carrier now fixes closed YAML members
  and explicit whole-epoch GC, but retention policy, redirect growth, and log
  serialization still need measurements before pruning or format rules are
  chosen. ([index questions](../designs/2026-08-03-world-index-packaging-design.md#12-open-questions), [epoch carrier](../designs/2026-08-20-world-index-slice-2-design.md#9-whole-epoch-garbage-collection), [log questions](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))
- **Observer distribution.** Which independent holders keep world-log anchors,
  what continuity they attest, and what happens when the last observer is lost
  wait on a second installation. ([log question](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))
- **Whether a dataset's own standing is retractable.** An upstream withdrawal
  already grounds retractions of dependent assessments. Whether a dataset's
  empirical-observation standing can be retracted directly is deferred until a
  concrete case forces it — the eligible-target test admits it with no new
  mechanism if so. ([correction question](../designs/2026-08-03-correction-lifecycle-design.md#9-open-questions))
- **Chain verification cost.** Full-timeline replay at mm30 scale sits behind
  the ledger's measurement gate. A Merkle overlay is the known upgrade path and
  is deliberately not built on speculation.
  ([log question](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))
## Computation and reproducibility

- **Artifact lifetime.** Held code, environments, inputs, and outputs accumulate;
  pruning cannot silently destroy verification closure. A disk policy remains
  undesigned. ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **Multi-product workflows.** Dataset-production v1 emits one product. A later
  shape needs to say whether one differing product fails the whole replay or
  creates separately verifiable results. ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **A publishable belief-input snapshot.** Recomputing a belief without holding
  the corpora needs the digest's members published apart from the content they
  name. The world index already carries one such member, which argues for a
  single artifact — an argument, not yet a decision.
  ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **Where the scope-derivation rule is versioned.** That rule's identity enters
  every verification address, so it needs one: with the belief policy, with
  `science.identity.v1`, or on its own. A stored verification now carries the
  identity as its `scope_rule` member, so a versioning decision changes what
  new records write, never what stored ones mean.
  ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions),
  [verification publication](../designs/2026-09-06-verification-publication-design.md#14-open-questions-this-design-files))
- **Where an interpretation rule reads content.** `build_assessment` hands the
  frozen spec's interpretation rule a `ResultManifest` of output digests, not
  output bytes, so a rule that must read a number reads it through a canonical
  outcome file whose digest it maps. Whether the rule should instead receive
  the declared outputs' content — and through which held, digest-verified
  read — is undecided; the mm30 reproduction routed its verdict through a
  three-line outcome file to stay inside the seam.
  ([reproduction record](../designs/2026-09-05-mm30-reproduction.md#6-findings))

## Contracts and adoption

- **Recency and corroboration — the holdings record's residue.** The
  verified-holdings record design (2026-08-10) closed where verified
  holdings are recorded: a world record in the observer's corpus,
  per-location, act-minted, superseded never expired, projected under a
  declared coverage. What remains open is smaller: whether anything ever
  discounts an old observation — a possible recency-bearing **successor
  projection rule**, pinned in every derivation receipt with an explicit
  reference instant, and never a belief-policy parameter — and the
  partly-pinned rule's empirical corroboration, which the ramp holds as
  evidence-not-design.
  ([holdings design](../designs/2026-08-10-verified-holdings-record-design.md),
  [what stayed open](../designs/2026-08-10-verified-holdings-record-design.md#7-what-this-unblocks-and-what-stays-open))
- **Contract governance.** Facet-breaking changes, compatibility ranges,
  parallel `genesis` contracts in one namespace, and domain distribution remain
  open. ([domain questions](../designs/2026-08-04-domain-extension-boundary-design.md#12-open-questions))
- **Relation endpoint enforcement.** Should contract-declared endpoint kinds be
  enforced by `nodes`, by the compiled Science profile at every seam, or by a
  later registry boundary? ([facet-contracts design §14](../designs/2026-09-05-facet-contracts-design.md#14-open-questions-this-design-files))
- **Normative artifact shape.** Whether a contract cut becomes a world node and
  how legacy checks pass the adoption gate remain decisions for the first full
  contract cut. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **Certifying the instruments that already exist.** An immutable spec cannot
  acquire the witnesses its falsification declaration lacks, so retroactive
  certification is unspellable and existing instruments certify only through a
  successor spec. Open is the cadence: sweep, mint on next authored use, or
  never. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **The act-report's residue.** The act-report design (2026-08-11) closed
  the run boundary's report seam: the boundary-minted terminal record of
  an opened operation — or the pre-intent refusal record of a rejected
  run request — the operation intent's three-valued completion reading
  (unfinished, indeterminate, closed), and the durable home of a look's
  non-report. Four things stay open, deliberately: cross-root publication
  of a dataset's provenance reference and its acquiring report (refused
  today); a compaction protocol that must preserve intent-qualification
  resolvability and fulfillment evidence (the rule today is retain); new
  operation kinds (the enum is closed at five); the agentic surface —
  audit scheduling and liveness, kernel sub-problem 6.
  ([act-report design](../designs/2026-08-11-act-report-design.md),
  [what stays open](../designs/2026-08-11-act-report-design.md#6-what-this-unblocks-and-what-stays-open))
