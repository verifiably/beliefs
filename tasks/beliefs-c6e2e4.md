---
id: beliefs-c6e2e4
title: "Establish whether a proposition-only corpus's namespace refuses a world read, and what each fix changes"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-09T11:13:41Z
updated: 2026-10-09T11:13:41Z
depends: []
parent: beliefs-7e341d
tags: [world-read]
source: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
agent: claude-code/claude-opus-5-5
---

Question: Does a world read where corpus M holds only the proposition, whose claim uses a namespace only M pins, refuse ContractDisagreement at consulted_contracts, and would passing the proposition's corpus separately (option 1) or attributing it in node_corpus (option 2) change the reproducibility context identity of any existing world-read derivation?
Where to start: python/src/beliefs/consulted.py consulted_contracts; evaluation.py's world-read node_corpus attribution; test_world_view.py's split_evaluation_world and the J20 test; mount-citations design decision 10 and §13 (J20 note); the brief docs/notes/2026-10-09-mount-citations-follow-ups-brief.md.
Bound: One failing world-read test over that shape (a test-local contract only M pins) and a comparison of context identities for J20's split under both options; no product-code change.
Expected result: Record whether it refuses, the identity effect of each option, and a recommendation on this task and in the brief's Alternatives.
Ideas it wakes: On completion, run tasks note on beliefs-d69102 with the finding, in the same commit as this result.
