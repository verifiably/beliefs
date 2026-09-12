---
id: beliefs-59f846
title: "Type the estimand, applicability, estimate and uncertainty"
status: todo
priority: 3
size: l
complexity: high
created: 2026-09-12T20:31:58Z
updated: 2026-09-12T21:06:08Z
depends: []
tags: [design, belief, contract]
spec: docs/superpowers/specs/2026-09-12-estimand-typing-design.md
---

Outcome: beliefs owns ρO3's estimand half. The base contract declares a kernel-owned estimand grammar (science.estimand.v1), a domain contract declares per-operator estimand sorts in an estimands: table, the frozen spec carries a typed estimand and a qualifier-map applicability, and the interpretation rule returns decimal estimates and typed uncertainty on the spec's declared scale and reference. Structural match is checked at the write boundary and under audit; a commensuration predicate is exposed and unread by science.belief.v1.

Acceptance evidence: the design spec docs/superpowers/specs/2026-09-12-estimand-typing-design.md reviewed and frozen; table Q (Q1–Q10) discharged at a conformance cut; the mm30 reproduction re-typed under a successor corpus-local contract with a dated addendum to its record; beliefs-638318 unblocked on this and reblocked on its own successor-policy design.

Sources: docs/guide/open-questions.md (Entailment and estimand match; Weighted belief); docs/designs/2026-08-05-belief-policy-design.md §3.2, §5, §9; docs/designs/2026-08-05-review-disposition-and-conformance-cut-1.md §8 question 4; the 2026-09-12 models assessment.

Uncertainty: off the dogfood path; opens a lane only under roadmap concurrency rule 6, and must merge before the contract cut freezes.

## Notes

- 2026-09-12T20:32:08Z (design/estimand-typing): Drafted the design spec in the estimand-typing worktree (.worktrees/estimand-typing, branch design/estimand-typing); under review, not frozen.
- 2026-09-12T20:32:52Z (design/estimand-typing): parked (waiting on user, review): Review the design spec docs/superpowers/specs/2026-09-12-estimand-typing-design.md; on approval invoke writing-plans for the implementation plan (lane opens only under roadmap rule 6)
- 2026-09-12T20:46:25Z (design/estimand-typing): 2026-09-12: first review's four findings taken (claim identity in the estimand; increment on continuous contrasts; applicability relocation rule; standard-error kind). Spec revised at 8c80aea; still parked for review.
- 2026-09-12T21:06:08Z (design/estimand-typing): 2026-09-12: second review's two findings taken: the boundary and audit require both claim-identity and operator equality on a stored estimand (Q6 gains the inconsistent-pair arm); applicability retyping admits only declared dimensions or an observes restatement and refuses the rest, so the reproduction re-authors a revise successor whose scope equality is a recorded judgment (limitations 9, 10). Still parked for review.
