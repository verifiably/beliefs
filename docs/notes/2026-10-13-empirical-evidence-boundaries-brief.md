# Observation and source assertion evidence boundaries

## Problem

Four ideas concern the boundary between empirical evidence and attributed
claims: annotation datasets (`beliefs-91bce7`), observation-first analysis
(`beliefs-8b26dc`), the missing stored source-assertion reader
(`beliefs-a1a767`), and fitted-model input roles (`beliefs-72b6f6`, added
2026-10-24). Establish concrete admission cases before choosing a new
annotation representation; design the stored source-assertion path separately.
The user's rule recorded in `sun-08c8ea` is a constraint: predictions about
observations are not themselves primary observations of the world.

## Current behaviour and evidence

Static evidence checked at main `31f8ad9`, 2026-10-13:

- **Heldness is insufficient.** `python/src/beliefs/acquisition.py`
  `validity_refusal` requires a valid empirical-observation declaration,
  no producer or lineage basis, and a valid acquisition report when named.
  `corpus.py`'s eligibility walk requires at least one valid `observes`
  input. `admission.py` additionally checks all inputs' heldness and admitted
  verification. `python/tests/test_acquisition.py` covers the bearer
  exclusions and the existential eligibility rule.
- **Observational nature remains authored.** The
  [kernel design's limitation 8 and September 7 amendment](../designs/2026-08-02-epistemic-kernel-design.md)
  explicitly do not prove that acquired material is observational. The
  [facet contract](../designs/2026-09-05-facet-contracts-design.md) specifies
  `locator`, `attested_by`, and optional `retrieval`, without an annotation
  classification. External labels declared as acquisition data therefore
  raise a different question from a known produced dataset, which already
  cannot carry empirical standing. This pass did not reproduce a complete
  annotation-to-belief execution.
- **Source assertions have a value path but no dedicated stored codec.**
  `record.SourceAssertion` restricts signs to asserts, denies and hypothesizes;
  `test_records.py` and `test_belief.py` cover G1's refusal and inertness
  (introduced at `d1fd379`). The canonical and packaged science contracts
  name `stored.source_assertion_value`, still absent from `stored.py` along
  with a dedicated builder. `contract/facets.py` validates the reader label
  as text; `facets.validate_payload` skips reader-shaped facets. These labels
  are not a runtime dispatcher. `evaluation.py` supplies an empty source
  assertion tuple. The gap was explicitly deferred in
  [world-resolution slice 2b](../superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md).
- **Nothing consumes stored source assertions yet.** On 2026-10-14 a search
  of the science, multiple-myeloma, sun and lit sources for `source-assertion`,
  `source_assertion` and `SourceAssertion` found no caller that mints or reads
  one. The stored path's urgency therefore rests on the contract's dangling
  reader label and on the annotation question below, not on a consumer.
- **Annotations and source assertions may share a representation.**
  `beliefs-91bce7` calls an annotation the same kind of thing as a source
  assertion in data form: an attributed claim with an annotator. Whether an
  annotation record can be a source assertion over a dataset or source span is
  open, and its answer constrains the stored projection.
- **Observation-first remains a direction.** The
  [guide's open questions](../guide/open-questions.md) asks how characterization
  reaches belief. Existing specs freeze before execution; they do not prove
  that the author had never seen the data.

Fitted-model rerun, 2026-10-24 at main `6c9bd9b`; static reads, no runtime probe:

- **Generic refusals and an oracle already exist.** `acquisition.py`'s
  `validity_refusal` rejects empirical standing for a dataset with a lineage
  basis or a known producer; `bearer_refusal` prevents the produced/facet pair
  at writes. These landed in `1d9d235`. Facet-contract rows F2 and F4 are
  frozen at cut 20. `python/tests/acceptance/test_facet_acceptance.py`'s
  `test_f4_eligibility_reads_the_validity_predicate` covers a lineage-bearing
  observed dataset; `python/tests/n2_arms_cut20.py` defines F4's validity-to-
  presence sabotage. This pass did not execute that arm or verify its live
  mutation still applies. The historical models-context report's "no oracle
  row or code found" does not account for this generic protection.
- **Eligibility is not a per-input role prohibition.**
  `corpus.py:eligibility_outcome` accepts an assessment when any observed
  dataset passes validity. The same F4 test adds a valid observed dataset
  beside the lineage-bearing one and expects eligibility. A model-specific
  "never observes" guarantee is stronger than the existing refusal of
  empirical standing and cannot be added as a mechanical restatement of F4.
- **Content identity supplies no model classification.** `RunInput` holds a
  role and a `DatasetDeclaration`; no fitted-model discriminator was found
  in those types or the base input contract. `production.mint_dataset` and
  `runrecord.publication_plan` preserve production provenance for the
  dataset-production route, but do not classify bytes as a fitted model.
  Kernel limitation 8 still excludes proving that an acquired declaration
  is truthful or its contents observational. The composite design's section 1
  says fitted models are only `reads`; it supplies no matching classifier.

## Constraints

Preserve G1/G6, acquisition bearer checks, recorded attempts, and frozen cuts.
Reproducibility does not turn an annotator's prediction into an observation.
Conversely, neither annotations supplied as `reads` nor a mixed dataset can
be judged merely by checking whether one valid observed input exists.

Do not equate the formal model's nine optional classification labels with a
new annotation dataset type. Do not infer that all computed outputs should
be forbidden: characterize their role and target first. Methodological
claims about an annotator remain an open policy question, not an exception
approved by this scope pass.

Preserve F4's existential rule while researching fitted-model roles. A stronger
role ban needs an explicit semantic decision and reviewed successor guarantees;
do not impose it on every produced dataset or infer a model type from a filename.

Existing owners remain: endpoint enforcement research `beliefs-9c375c`,
contract cut `beliefs-eacbe2`, lineage standing `beliefs-8ecbb5`, and weighted
belief `beliefs-638318`. The last two remain shelved under their existing wake
conditions. No duplicate endpoint research or weighting project is needed.

## Alternatives

1. **Work from explicit cases, then design the smallest boundary (lean).**
   Separate primary measurements, external predictions, mixed datasets and
   run-produced characterization; use existing workflow objects where they fit.
   Give stored source assertions their own reviewed representation, designed
   after the worked cases say whether annotations reuse it.
2. **Introduce an annotation kind or provenance facet immediately.** It can
   express attribution, but cannot by itself settle mixed data, `reads`
   influence, truthful declarations, or propositions about annotators.
3. **Keep annotation treatment solely in consumer guidance.** Useful now,
   but insufficient if the requirement is kernel-enforced exclusion.

For fitted models, reuse the worked-case research first (lean), rather than
adding a model-specific refusal or a generic ban on produced `observes` targets
now. It must separate existing non-eligibility, authoring guidance and any
stronger role rule before choosing an oracle amendment.

For the stored source-assertion path alone:

- **Design it after the worked cases (lean).** The case matrix may show that
  annotations need the same attributed-claim projection; designing first risks
  reopening it. With no consumer, waiting costs nothing.
- **Correct the contract and shelve the design.** Remove the dangling
  `stored.source_assertion_value` label, or mark the reader unimplemented, and
  wake the design when a consumer must mint source assertions. Cheaper, but it
  amends both contract copies ahead of `beliefs-eacbe2`, and it would be
  premature if the annotation design turns out to need the projection.
- **Design it now, independently.** Rejected: no consumer forces it, and it
  could fix a projection before the annotation cases are known.

## Unanswered questions

- Does "fitted models only as reads" mean refusing an input role even beside
  valid observations, or denying empirical standing to the model itself?
  `beliefs-1d023a` maps a known produced model alone, beside valid observations,
  as `reads`, and externally acquired without recorded production, within its
  existing workflow and probe bound. It recommends whether a reviewed semantic
  design is needed and names the limits of any proposed classifier.
- Which annotation cases pass each current gate, and what treatment satisfies
  the user's rule? What is the first unsupported step in a
  characterize-then-formulate workflow? `beliefs-1d023a` answers with one
  worked workflow and at most three focused probes.
- What stored projection carries a source span, attribution, proposition and
  sign while preserving inertness, identity and source correction?
  Can an annotation record be a source assertion over a dataset or source
  span? `beliefs-1d023a` answers the second question as part of its case
  matrix; `beliefs-595a53` owns the reviewed design, informed by both
  `beliefs-1d023a` and `beliefs-9c375c`.
- Does observation-first need a kernel change, and does it actually require
  unequal weights or inherited standing? Decide from the worked case rather
  than making either shelved design an automatic prerequisite.

## Proposed decomposition

Goal `beliefs-9396cf` groups all four ideas, preserving their original material
and sources.

- `beliefs-72b6f6`: **briefed**, depends on the existing `beliefs-1d023a`
  (P2, medium, mid complexity, direct research). Add fitted-model variants to
  its existing produced/characterization cases; retain the limit of three
  focused probes. Its result updates this brief and wakes this idea with
  `tasks note beliefs-72b6f6 --no-reviewed "<finding>"` before merging.
  No duplicate research, new model kind or implementation task is filed.

- `beliefs-91bce7` and `beliefs-8b26dc`: **briefed**, both depend on
  `beliefs-1d023a` (P2, medium, mid complexity, direct research). Its result
  updates this brief and wakes both with `tasks note <id> --no-reviewed`
  before the result's branch merges.
- `beliefs-a1a767`: **briefed**, depends on `beliefs-595a53` (P3, medium,
  high complexity, planned design). That task depends on `beliefs-1d023a` and
  on the existing endpoint matrix `beliefs-9c375c` (P3); its reviewed handoff
  wakes this idea with `--no-reviewed` before merging. Spec and plan reviews
  precede any implementation. It was lowered from P2 on 2026-10-14 because no
  consumer needs stored source assertions yet, which also matches the P3
  endpoint matrix it waits on. Raise it if `beliefs-1d023a` finds that
  annotations need the projection.
