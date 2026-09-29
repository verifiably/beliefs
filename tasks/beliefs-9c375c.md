---
id: beliefs-9c375c
title: Establish the relation-endpoint enforcement matrix
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-29T22:42:52Z
updated: 2026-09-29T22:42:52Z
depends: []
parent: beliefs-d58675
tags: [domain]
source: docs/notes/2026-09-29-domain-contract-backlog-brief.md
agent: codex
---

Question: Which declared relation endpoint constraints are enforced today, and what is the smallest consistent policy for unresolved and cross-corpus endpoints?
Where to start: python/src/beliefs/corpus.py shared refusal path and import validation; python/src/beliefs/audit.py; python/src/beliefs/profile.py; contracts/science/CONTRACT.yaml; python/tests/test_composite_boundary.py and test_facet_seams.py; docs/designs/2026-09-05-facet-contracts-design.md sections 9 and 14; the scope brief.
Bound: Inventory each declared relation against add/revise, import, relocation and audit; trace their common seams. Reproduce one representative wrong-kind edge and one unresolved or cross-corpus target using existing fixtures through just test-one. Do not implement a generic validator or change contract policy.
Expected result: Record a behavior matrix with source/test references, actual refusal or finding outcomes, and a recommended enforcement layer and missing-target policy on this task and in the brief. Distinguish observation from proposed semantics; name any decision needing the contract-cut design. Done when the two probes are recorded and every declared signature is accounted for.
Ideas it wakes: On completion, run tasks note beliefs-e803cc with the finding in the same commit as the result; this readmits the idea to scoping.
