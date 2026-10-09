---
id: beliefs-c6e2e4
title: "Establish whether a proposition-only corpus's namespace refuses a world read, and what each fix changes"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-09T11:13:41Z
updated: 2026-10-09T13:48:15Z
depends: []
parent: beliefs-7e341d
tags: [world-read]
source: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
agent: claude-code/claude-opus-5-5
---

Question: Does a world read where corpus M holds only the proposition, whose claim uses a namespace only M pins, refuse ContractDisagreement at consulted_contracts? It must be checked at both walks: gather (python/src/beliefs/evaluation.py:610) and the pure evaluator, which recomputes the consulted contracts from context.node_corpus (python/src/beliefs/belief.py:368). Under option 1 (pass the proposition's corpus separately, which must reach both walks and so enters the belief context) and option 2 (attribute it in node_corpus), what happens when M pins no version of the namespace, and when M's pin disagrees with an evidence corpus's pin? Does either option change the reproducibility context identity of any existing world-read derivation?
Where to start: python/src/beliefs/consulted.py consulted_contracts; evaluation.py's world-read node_corpus attribution and its consulted_contracts call (:610); belief.py's evaluator walk (:368) and the BeliefContext fields it reads; test_world_view.py's split_evaluation_world and the J20 test; mount-citations design decision 10 and §13 (J20 note); the brief docs/notes/2026-10-09-mount-citations-follow-ups-brief.md (option 1 now names both walks).
Bound: World-read tests over that shape with a test-local contract only M pins: refusal at each walk; the missing-pin and disagreeing-pin cases under each option; a comparison of context identities for J20's split under both options. No product-code change.
Expected result: Record, per walk and per pin case, whether it refuses, the identity effect of each option, and a recommendation, on this task and in the brief's Alternatives.
Ideas it wakes: On completion, run tasks note on beliefs-d69102 with the finding, in the same commit as this result.

## Notes

- 2026-10-09T13:48:14Z (main): Widened 2026-10-09 after a review of the brief: option 1 must reach both consulted_contracts walks (gather at evaluation.py:610 and the evaluator's recomputation from context.node_corpus at belief.py:368), and the comparison now covers missing and disagreeing proposition pins as well as context identities
