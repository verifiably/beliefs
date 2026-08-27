---
title: Open questions
status: living
created: 2026-08-08
updated: 2026-08-27
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-correction-lifecycle-design.md
  - ../designs/2026-08-03-world-index-packaging-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
  - ../designs/2026-08-05-review-disposition-and-conformance-cut-1.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-09-conformance-cut-2.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-11-conformance-cut-3.md
  - ../designs/2026-08-17-conformance-cut-4.md
  - ../designs/2026-08-18-composition-root-adapter-design.md
  - ../designs/2026-08-19-family-adapters-design.md
  - ../designs/2026-08-19-conformance-cut-5.md
  - ../designs/2026-08-20-world-registry-design.md
  - ../designs/2026-08-20-conformance-cut-6.md
  - ../designs/2026-08-20-world-index-slice-2-design.md
  - ../designs/2026-08-20-conformance-cut-7.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../designs/2026-08-24-conformance-cut-10.md
  - ../designs/2026-08-27-conformance-cut-11.md
  - ../plans/2026-08-20-conformance-cut-6-results.md
  - ../plans/2026-08-24-conformance-cut-10-results.md
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
- **Empirical-observation facet.** What demonstrates an acquisition boundary,
  rather than merely asserting that a dataset is observational? This contract is
  the hinge of empirical eligibility. ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Kernel-adjacent structures.** Are inquiries, patch definitions, structural
  chains, and coverage searches new kinds or derived views over existing kinds?
  ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Science profile distribution.** Does the downstream profile live inside
  the `science` distribution or in its own package? The durability composition
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
  `science.identity.v1`, or on its own.
  ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))

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
  parallel `genesis` contracts in one namespace, domain distribution, and
  Python/TypeScript parity policy remain open. ([domain questions](../designs/2026-08-04-domain-extension-boundary-design.md#12-open-questions))
- **Normative artifact shape.** Whether a contract cut becomes a world node and
  how legacy checks pass the adoption gate remain decisions for the first full
  contract cut. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **Certifying the instruments that already exist.** An immutable spec cannot
  acquire the witnesses its falsification declaration lacks, so retroactive
  certification is unspellable and existing instruments certify only through a
  successor spec. Open is the cadence: sweep, mint on next authored use, or
  never. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **Cut 10 is discharged; part of cut 3's deferred boundary stays open.** Cut 3
  was frozen 2026-08-11 at the run boundary,
  taking run capture — the seam the verified-holdings record (2026-08-10)
  and the act-report design (2026-08-11) finished designing. Its §5
  deferred the persistence seam (the holdings store, H1–H4, T7, the tamper
  log), world persistence, and the `nodes` contract deltas, noting that the
  first cut to cross a persistence boundary would take several of those
  groups at once — whether as one cut or two, not ruled there. The cut-4
  `nodes` write-plan/executor seam dependency was frozen and satisfied
  2026-08-17, its failure-attribution amendment landed 2026-08-18, and the
  Science composition-root adapter design banked that day. Cut 4 is drawn
  against the certified
  `atoms` engine adopted at Science's composition root, add-only,
  corpus-write minting alone, with no L row selected because registration
  is engine-supplied. Cut 6 lands the authoritative world root, manifest,
  corpus-state identity, registry, lifecycle, and presence core. Cut 7 froze
  the epoch build, four maps and receipts, rules store, bounded reads,
  GC, and anchor carrier, and discharged all 48 declarations on the certified
  tuple; anchor verification was outside it. Cut 8 closed that: it froze
  2026-08-22 over the L table, reading five rows in full and seven in part with
  L6 unread, and discharged all 53 declarations on the certified tuple on
  2026-08-23 — the anchor act, the one four-outcome evaluator, replay, the
  audit and replica-arrival boundaries, and the genesis↔mirror check. Cut 9
  froze and discharged 2026-08-23: the root lifecycle and store substrate —
  the fail-closed writer state and lifecycle commands, `restore_root`, the
  fork acts, genesis-bound store subjects, and lifecycle-aware arrival modes —
  reading one row in full and four in part with L6 read for the first time
  under the fork-baseline lift, all 30 declarations on the certified tuple.
  Cuts 4–9 are implemented, discharged, and merged on `main` — cut 9's
  `--no-ff` integration commit is `7a9fec8`, 2026-08-24. Cut 10 froze
  2026-08-24 and discharged verified store-side holdings on 2026-08-25 — the
  governed observation kind, intent-bearing acts, mechanical coverage,
  fixture-bound reduction and receipt, and dataset admission adapter — with
  20 selected + 11 labeled declarations. Its `--no-ff` merge landed on local
  `main` as `35be6ff` on 2026-08-25 and has not been pushed.
  What the tamper-log group still owes is named
  and owned: general intent qualification (the intent-boundary slice, in
  design), G4 (**split 2026-08-27 to its own successor-admission
  slice** — the intent-boundary spec §5 carries the transfer), the
  preimage-backed classification of a removed verification, and
  event-level cross-chain order.
  L10's fork/replica/restore and store arms closed with cut 9; its two deferred
  holdings-read arms and L7's holdings-shaped qualification/boundary arms
  closed with cut 10. The store substrate's holdings prerequisite is complete,
  including the atoms read command and returned final-state evidence at remote
  atoms `main` `038513f`.
  The separately deferred consolidate/move/deletion cut no longer waits on the
  world index.
  ([conformance cut 3](../designs/2026-08-11-conformance-cut-3.md),
  [its deferrals](../designs/2026-08-11-conformance-cut-3.md#5-step-3--fully-deferred-rows-grouped-by-unblocking-subsystem),
  [conformance cut 4](../designs/2026-08-17-conformance-cut-4.md),
  [composition-root adapter design](../designs/2026-08-18-composition-root-adapter-design.md),
  [conformance cut 5](../designs/2026-08-19-conformance-cut-5.md),
  [cut 5 results](../plans/2026-08-19-conformance-cut-5-results.md),
  [conformance cut 6](../designs/2026-08-20-conformance-cut-6.md),
  [cut 6 results](../plans/2026-08-20-conformance-cut-6-results.md),
  [epoch-carrier design](../designs/2026-08-20-world-index-slice-2-design.md),
  [conformance cut 7](../designs/2026-08-20-conformance-cut-7.md),
  [cut 7 results](../plans/2026-08-20-conformance-cut-7-results.md),
  [log-verification design](../designs/2026-08-22-log-verification-design.md),
  [conformance cut 8](../designs/2026-08-22-conformance-cut-8.md),
  [cut 8 results](../plans/2026-08-22-conformance-cut-8-results.md),
  [root-lifecycle design](../designs/2026-08-23-world-index-root-lifecycle-design.md),
  [conformance cut 9](../designs/2026-08-23-conformance-cut-9.md),
  [cut 9 results](../plans/2026-08-23-conformance-cut-9-results.md),
  [holdings design](../designs/2026-08-24-world-index-holdings-design.md),
  [conformance cut 10](../designs/2026-08-24-conformance-cut-10.md),
  [cut 10 results](../plans/2026-08-24-conformance-cut-10-results.md),
  [conformance cut 11](../designs/2026-08-27-conformance-cut-11.md))
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
  audit scheduling and liveness, kernel sub-problem 6. Science-side anchor
  carriage and a durable-log consumer are **no longer among them**: carriage
  landed with cut 7 and the consumer — the explicit anchor act, the evaluator,
  and the audit and arrival boundaries — with cut 8 on 2026-08-23.
  ([act-report design](../designs/2026-08-11-act-report-design.md),
  [what stays open](../designs/2026-08-11-act-report-design.md#6-what-this-unblocks-and-what-stays-open))
