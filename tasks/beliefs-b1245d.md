---
id: beliefs-b1245d
title: "composite.py tidy: duplicated loops, the tautological projection tests, the first-absent-member unchecked"
status: done
priority: 4
size: s
complexity: low
process: direct
owner: design/correction-remainder
created: 2026-09-16T22:38:37Z
updated: 2026-09-17T08:44:44Z
started: 2026-09-17T08:31:50Z
completed: 2026-09-17T08:44:44Z
depends: []
parent: beliefs-dc4e56
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
agent: claude-code/claude-fable-5-1
---

Residuals recorded at cut 32's results record §7 and left unfiled there: the relations-count/order check inlined in both audit.check_composite and corpus._refuse_composite (fold into one helper beside classify); the node-outcome loop duplicated between build_composite and read_composite with differing refusal text; the four NotReached arms (fixtures-unheld, fixture failure, gather exceptions, corpus-absent) asserted only through the answer; the tautological first-projection tests in test_belief.py and test_evaluation.py needing a comment that P1–P9 carry the proof; check_composite returning _unchecked on the first absent-corpus member so a dangling sibling is reported only once that corpus is present; _refuse_cycle's recursion; the unconditional skip in test_composite.py; audit.py's function-scope _absence_of import. Every U8 before string in n2_arms_cut32.py must still occur exactly once, so re-target the live guard where a pinned line moves.

## Notes

- 2026-09-17T08:31:50Z (design/correction-remainder): claimed by Codex task5, pid 787
- 2026-09-17T08:44:44Z (design/correction-remainder): RED first-absent/dangling-sibling world test failed with no finding; GREEN focused composite integration passed. U6-b live guard retargeted corpus.py -> composite.py and sabotage verdict sound. Certified test-fast: 4956 passed, 1 skipped on 2026-09-17.
- 2026-09-17T08:44:44Z (design/correction-remainder): Consolidated composite checks/outcomes, made cycle refusal iterative, preserved sibling auditing past absent corpora, and pinned NotReached arms
