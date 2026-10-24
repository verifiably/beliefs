---
id: beliefs-9bf498
title: Inventory where belief computation discards information in the data
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-24T01:04:06Z
updated: 2026-10-24T01:04:06Z
depends: []
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: at each step from a run's output to a belief value, what information does the kernel hold, and what does the value then ignore? Start from [ref:policy] §3 and §8 and [ref:estimand], then read belief.py, lineage.py and policy.py. Known candidates to confirm or refute, each with the design line or code that causes it: unit weight (sample size, design, precision); the verdict collapsing a typed estimate and uncertainty into supported/refuted/inconclusive; inconclusive excluded, so a well-powered null is not evidence of absence (lim. 2); applicability unread (lim. 3); dependence binary, so partial overlap counts like full duplication and not-certified counts like shared-source; a dependent assessment dropped from the selection rather than down-weighted; a dependent contradiction can neutralise but never overturn (lim. 4); no declared prior or plausibility; each claim aggregated alone, with no propagation across related claims or composites. For each item, record what is held, what is discarded, whether discarding it is deliberate (and why), and a concrete case where the value misleads. Output: [ref:inventory]. No proposals beyond naming what a fix would need.

## References

- policy (input, required, kind=spec): docs/designs/2026-08-05-belief-policy-design.md — v1 rule, §3 rationale, §8 limitations
- estimand (input, kind=spec): docs/designs/2026-09-12-estimand-typing-design.md — what each assessment now carries in typed form
- inventory (output, kind=report): docs/notes/belief-information-loss-report.md — the inventory
