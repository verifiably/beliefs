---
id: beliefs-18b03d
title: "Worked example: a detector assessment against the estimand-typing draft"
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: design/estimand-typing
created: 2026-09-13T03:04:59Z
updated: 2026-09-15T16:38:08Z
started: 2026-09-15T16:30:54Z
completed: 2026-09-15T16:38:08Z
depends: []
tags: [natural-systems, belief]
source: natural-systems-v2 docs/specs/2026-09-12-natural-systems-v2-framing.md §4
model: claude-fable-5-1
---

From the natural-systems v2 framing draft §4 and §6 q5, against docs/superpowers/specs/2026-09-12-estimand-typing-design.md on the estimand-typing worktree (task beliefs-59f846 there). Write one detector's estimand: the statistic as measure, a levels contrast with the surrogate family as baseline and the observed series as comparison, on a declared scale. Test whether it inhabits the §3.3 fragment as drafted. Known frictions to settle, not assume: reference is a Decimal the spec freezes before the run, so a null expectation estimated from surrogates during execution does not fit that slot and a fixed-zero reference with the surrogate ensemble consumed inside the interpretation rule may; a surrogate null distribution is not the estimate's sampling distribution, so whether it can fill uncertainty is a separate question; the §3.3 no-time-index boundary when the resolution coordinate is a lag or scale; how a surrogate, a derived dataset, enters the run value. Output: the example and a finding on the draft, filed before the contract cut freezes. No stack extension is requested from this task; multi-product workflows is explicitly not an ask.

## Notes

- 2026-09-13T09:07:07Z (main): Framing draft moved to the natural-systems-v2 repository; goal re-homed as ns-a0e6ab
- 2026-09-15T16:26:47Z (main): Process direct: the natural-systems pilot design §7 fixes the exact target — delta(D,Q) = T(D) - E_Q[T(Q(D))] for fixed-lag CO_trev_1_num, identity observation against a phase-randomized surrogate procedure, additive scale, reference 0, MC standard error sd(T_surr)/sqrt(B) conditional on D — and names what to test: contrast referents, fixed reference, the home for lag and observation scope, surrogate lineage, the meaning of standard-error; the estimand draft's §3.2, §3.3 and §6 are the oracle. No design choice is open; the output is a prose mapping plus a finding.
- 2026-09-15T16:26:47Z (main): Sequencing 2026-09-15: this must land before estimand-typing Task 0 Step 3 (beliefs-705507), which git-mv's the draft into docs/designs and freezes it; a finding after that is a supersede-by-citation amendment. The pilot's demand for an API test against build_estimand (not a prose mapping) is split out as a lane step after Task 4 and before Task 11 on branch design/estimand-typing; this task stays the pre-freeze prose mapping and finding. Pilot source: natural-systems docs/specs/2026-09-13-time-series-pilot-design.md §7, which pinned draft head bf15848; the branch has moved since, so read the current head.
- 2026-09-15T16:38:08Z (design/estimand-typing): Worked the pilot's surrogate contrast (delta(D,Q) for fixed-lag CO_trev_1_num against Fourier phase randomization) against the draft: it inhabits the fragment as drafted, no member added, widened or re-sorted. Appendix A of the estimand-typing spec carries the encoding (levels contrast on a procedure slot, identity vs phase-randomized; lag in the measure term; reference 0 as the contrast's null value; MC standard error admitted because the estimand is over the held series; surrogates are run output bytes, not datasets, so lineage standing is not reached; synthetic controls refuse EligibilityUnmet and stay runs without assessments). Four clarifying amendments taken: §3.2 reference, §3.3 time-index, §6 standard-error randomness, limitation 12. API half is beliefs-e48279.
