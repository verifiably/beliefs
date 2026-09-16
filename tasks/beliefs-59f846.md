---
id: beliefs-59f846
title: "Type the estimand, applicability, estimate and uncertainty"
status: done
priority: 3
size: l
complexity: high
process: planned
owner: design/estimand-typing
created: 2026-09-12T20:31:58Z
updated: 2026-09-16T06:57:07Z
started: 2026-09-15T16:45:12Z
completed: 2026-09-16T06:57:07Z
depends: []
tags: [design, belief, contract]
model: claude-fable-5-1
spec: docs/designs/2026-09-12-estimand-typing-design.md
plan: docs/superpowers/plans/2026-09-12-estimand-typing.md
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
- 2026-09-12T21:10:57Z (design/estimand-typing): 2026-09-12: third review's two findings taken: the transition is recreation not migration (decision 10: grammar member on the spec projection, named pre-grammar refusals and audit codes, no revise or supersedes across the shape change; Q10 restores from disk in a fresh process); co_scoped added beside commensurable over applicability maps, Q9 carries the same-claim different-scope counterexample. Still parked for review.
- 2026-09-12T21:46:21Z (design/estimand-typing): parked (waiting on user, review): Review the implementation plan docs/superpowers/plans/2026-09-12-estimand-typing.md; on approval, Tasks 1-5 may start in this worktree, Tasks 6-12 wait for the lane under roadmap rule 6
- 2026-09-12T22:33:24Z (design/estimand-typing): 2026-09-12: plan review's eleven findings taken (Task 0 opens the lane and freezes the cut first; factory-built refusal fixtures; stored referents require explicit valid sorts; numerical invariants at every AssessmentValue construction; AssessmentRef keeps spec and identity for successor admission; decode failures translate to MalformedRecord at the readers; the prior corpus audits as profile-mismatch: base; lists prepare before adoption and the belief step is in the sequence; integer slots; the estimator refuses non-finite input; Q8 isolated through a contract only the estimand reaches). Still parked for plan review.
- 2026-09-12T23:02:59Z (design/estimand-typing): 2026-09-12: plan review round 2 taken: stored routes refuse a bare-term referent (stored=True on the stored decoders and applicability), check_assessment takes the profile and both callers pass it, the estimand decoder's text checks raise MalformedWireEstimand.
- 2026-09-12T23:50:22Z (design/estimand-typing): parked (waiting on agent, dependency): Plan cleared 2026-09-12; execution waits on Task 0's lane admission (beliefs-705507, blocked on beliefs-46847c)
- 2026-09-15T16:27:04Z (design/estimand-typing): 2026-09-15: natural-systems v2 framing §4 and pilot design §7 checked against this lane. No spec change is known yet; the pilot's target (fixed reference 0, additive, surrogate-vs-identity levels contrast, MC standard error conditional on D, lag inside the measure term) is meant to inhabit §3.2/§3.3/§6 as drafted, and 18b03d tests that pre-freeze. Two order constraints added: 18b03d before Task 0 Step 3; beliefs-e48279 (API test) after Task 4, before Task 11. Watch §6's standard-error meaning: the pilot's SE is Monte-Carlo error of E_Q, not sampling error over trajectories, and §6 fixes one meaning per kind.
- 2026-09-15T16:45:12Z (design/estimand-typing): lane admitted under rule 6, 2026-09-15 after cut 30: open kernel lanes none (doing holds only the CI audit, a non-lane task; composite-claim is parked on this lane's merge); on-path state: tier 1 has no on-path boundary, world-resolution discharged at cut 30, so an off-path lane may open. Cut number scan across worktrees: highest claimed 30; this cut is 31, chained after cut30_acceptance.py (rule 5). Baseline: main at 5127dcfa52d85ec2f6f2b2cc6af507d0a1e1eafe.
- 2026-09-15T16:45:12Z (design/estimand-typing): Process planned: the spec (three reviews) and plan (two reviews) cleared 2026-09-12; execution follows the plan's Tasks 0-12.
- 2026-09-15T16:45:35Z (design/estimand-typing): cut 31 frozen at c2a2211c2d9a0889a59e7892dcb71f2008e20e46, sha256 3cd4409dd08d5b121d3f62bfaaa00e3d553335d6a54e7657471c70677854d93f (docs/designs/2026-09-15-conformance-cut-31.md); Task 11's guard pins both
- 2026-09-16T06:57:07Z (design/estimand-typing): Estimand typing landed on design/estimand-typing: cut 31 frozen at c2a2211 and discharged (Q1–Q10 closed; 163 of 206 rows); the base contract owns science.estimand.v1, domain contracts declare estimands:, specs carry a typed estimand and applicability, rules return decimal estimates and typed uncertainty, structural match holds at the boundary and under audit, commensurable/co_scoped exposed and unread by v1; the mm30 corpus recreated under the successor contract with the belief re-derived equal in a fresh process; the natural-systems worked example and API test admitted as drafted; results record 2026-09-16-conformance-cut-31-results.md; weighted-belief re-blocked on the successor policy design; follow-ups beliefs-1dd03f, beliefs-0521da, beliefs-1b0827. Awaits the --no-ff merge into main.
