---
id: beliefs-4bcf88
title: "Composite claims: the kind that places kernel §11's inquiry, patch-definition and structural-chain"
status: todo
priority: 2
size: l
complexity: high
created: 2026-09-13T00:35:00Z
updated: 2026-09-13T01:11:40Z
depends: []
tags: [design]
spec: docs/superpowers/specs/2026-09-12-composite-claims-design.md
---

The second spec from the 2026-09-12 models assessment. A structure (a causal DAG, the predecessor's h00 working model, inquiry DAGs and patch-definitions) is a set of propositions over a declared node set with derived, never authored, belief. Kernel §11 left inquiry / patch-definition / structural-chain unplaced; this design places them. Off the path; before the contract-cut freeze; after estimand-typing.

## Notes

- 2026-09-13T00:41:23Z (design/composite-claim): parked (waiting on user, review): Spec drafted; review it, then write the implementation plan
- 2026-09-13T01:05:00Z (design/composite-claim): Spec review 1: four findings (negative polarity kept as a sign; reading names every evaluator input; supersedes same_kind on the shared path and under audit; build_composite takes a ResolutionSnapshot and returns a receipt), all taken
- 2026-09-13T01:11:40Z (design/composite-claim): Spec review 2: four findings (reading goes through evaluate_over; identification follows current admission via a traced wrapper; U3 split form vs vocabulary; node receipt on CompositeReading), all taken; same_kind stays declarative
