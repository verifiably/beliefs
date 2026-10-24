---
id: beliefs-1d023a
title: Map annotations and observation-first characterization onto empirical admission
status: todo
priority: 2
size: m
complexity: mid
process: direct
created: 2026-10-14T01:34:23Z
updated: 2026-10-24T10:17:06Z
depends: []
parent: beliefs-9396cf
tags: [design]
source: docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md
agent: codex
---

Question: Which annotation and observation-first characterization cases already fit the empirical admission route, and which require a new provenance or eligibility contract to enforce the user's rule that predictions about the world are not primary observations?

Where to start: docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md; source task sun-08c8ea; kernel design sections 4.1 and 8 limitation 8 plus its 2026-09-07 amendment; facet-contracts design sections 2, 6 and 14; python/src/beliefs/acquisition.py validity_refusal, corpus.py eligibility_refusal, admission.py admit, evaluation.py and tests/test_acquisition.py.

Bound: One synthetic worked workflow with measured values, external labels, and a deterministic characterization output. Map five cases: annotations alone with and without an empirical declaration; a mixed measurement/label dataset; a known produced dataset with lineage; annotations supplied as reads beside a valid observes input; and characterization generated inside a run versus acquired as a dataset. Distinguish current shape/provenance validation, heldness, clean-environment verification and the truth of the acquisition declaration. Record the current outcome and desired empirical-belief treatment for each case without claiming held bytes alone suffice. Use at most three focused fixture probes where code/tests leave the answer uncertain; run them through just test-one. Trace a characterize-then-formulate workflow onto existing specs, runs, datasets and assessments, and identify the first unsupported step. No new kind, policy, weighting scheme, catalog download, benchmark, or implementation. Do not treat methodological propositions about annotators as already authorized empirical evidence.

Within the existing produced/characterization cases, include a fitted-model output: as the sole observes input; beside valid primary observations; as reads beside valid observations; and externally acquired without recorded production. Start from [ref:brief]'s 2026-10-24 evidence: F2/F4 already deny known produced data empirical standing, but F4 remains existential, and the input types do not classify fitted models. Fit these variants into the same synthetic workflow and existing maximum of three focused fixture probes; do not begin a separate investigation or impose a role ban.

Expected result: Record the case matrix, probe commands/results, an example of characterization before a later fixed spec, and a recommendation for the smallest design boundary on this task and in the brief. Distinguish observations from proposed semantics. List the decisions a subsequent annotation design must settle (mixed data, attribution, reads influence, target type, classification updates, and truthful-declaration limits); state whether observation-first requires kernel changes or consumer orchestration. State whether an annotation record can be a source assertion over a dataset or source span (an attributed claim with its annotator), and record that answer on beliefs-595a53, whose stored source-assertion design waits on it. Link any overlap with beliefs-8ecbb5 and beliefs-638318 without waking them unless their concrete conditions hold. Also record whether the model-only-reads prose is satisfied by current standing rules, needs consumer authoring guidance, or requires a reviewed stronger input-role contract; name the classifier's limits for acquired model bytes and any change's effect on frozen F4. Do not equate known provenance with recognizing model contents.

Ideas it wakes: Before this result's branch merges, run tasks note beliefs-91bce7 --no-reviewed "<finding>" and tasks note beliefs-8b26dc --no-reviewed "<finding>". Also run tasks note beliefs-72b6f6 --no-reviewed "<finding>" before this result's branch merges.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md — admission case matrix and fitted-model role question
