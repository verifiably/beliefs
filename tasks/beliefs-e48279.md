---
id: beliefs-e48279
title: The pilot's surrogate-contrast estimand through build_estimand
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-09-15T16:27:04Z
updated: 2026-09-15T16:27:04Z
depends: [beliefs-c54ed5]
parent: beliefs-59f846
tags: [natural-systems, belief]
source: natural-systems docs/specs/2026-09-13-time-series-pilot-design.md §7
agent: claude-code/claude-fable-5-1
---

The API half of beliefs-18b03d, which the pilot design §7 requires ('a prose mapping is not a passing API test'). After Task 4 builds beliefs/estimand.py: a fixture domain contract with a natural-systems estimands: row (a measure sort holding the fixed-lag trev statistic with lag in the term, a level sort with identity observation and the phase-randomized surrogate procedure), then build_estimand and the AssessmentValue constructor over delta(D,Q) = T(D) - E_Q[T(Q(D))], additive, reference 0, standard-error sd(T_surr)/sqrt(B). Asserts admission and that the refusals 18b03d predicted refuse. Unit test only, no new kernel surface, no acceptance row: a finding here before Task 11 is a plan amendment, after it a citation. Lands before Task 11.
