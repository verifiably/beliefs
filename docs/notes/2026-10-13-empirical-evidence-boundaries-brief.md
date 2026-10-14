# Observation and source assertion evidence boundaries

## Problem

Three ideas concern the boundary between empirical evidence and attributed
claims: annotation datasets (`beliefs-91bce7`), observation-first analysis
(`beliefs-8b26dc`), and the missing stored source-assertion reader
(`beliefs-a1a767`). Establish concrete admission cases before choosing a new
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
- **Observation-first remains a direction.** The
  [guide's open questions](../guide/open-questions.md) asks how characterization
  reaches belief. Existing specs freeze before execution; they do not prove
  that the author had never seen the data.

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

Existing owners remain: endpoint enforcement research `beliefs-9c375c`,
contract cut `beliefs-eacbe2`, lineage standing `beliefs-8ecbb5`, and weighted
belief `beliefs-638318`. The last two remain shelved under their existing wake
conditions. No duplicate endpoint research or weighting project is needed.

## Alternatives

1. **Work from explicit cases, then design the smallest boundary (lean).**
   Separate primary measurements, external predictions, mixed datasets and
   run-produced characterization; use existing workflow objects where they fit.
   Give stored source assertions their own reviewed representation.
2. **Introduce an annotation kind or provenance facet immediately.** It can
   express attribution, but cannot by itself settle mixed data, `reads`
   influence, truthful declarations, or propositions about annotators.
3. **Keep annotation treatment solely in consumer guidance.** Useful now,
   but insufficient if the requirement is kernel-enforced exclusion.

## Unanswered questions

- Which annotation cases pass each current gate, and what treatment satisfies
  the user's rule? What is the first unsupported step in a
  characterize-then-formulate workflow? `beliefs-1d023a` answers with one
  worked workflow and at most three focused probes.
- What stored projection carries a source span, attribution, proposition and
  sign while preserving inertness, identity and source correction?
  `beliefs-595a53` owns the reviewed design, informed by `beliefs-9c375c`.
- Does observation-first need a kernel change, and does it actually require
  unequal weights or inherited standing? Decide from the worked case rather
  than making either shelved design an automatic prerequisite.

## Proposed decomposition

Goal `beliefs-9396cf` groups all three ideas, preserving their bodies and sources.

- `beliefs-91bce7` and `beliefs-8b26dc`: **briefed**, both depend on
  `beliefs-1d023a` (P2, medium, mid complexity, direct research). Its result
  updates this brief and wakes both with `tasks note <id> --no-reviewed`
  before the result's branch merges.
- `beliefs-a1a767`: **briefed**, depends on `beliefs-595a53` (P2, medium,
  high complexity, planned design). That task depends on the existing
  endpoint matrix `beliefs-9c375c`; its reviewed handoff wakes this idea
  with `--no-reviewed` before merging. Spec and plan reviews precede any
  implementation.
