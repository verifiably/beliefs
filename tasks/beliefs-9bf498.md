---
id: beliefs-9bf498
title: Inventory where belief computation discards information in the data
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-24T01:04:06Z
updated: 2026-10-24T10:05:25Z
depends: []
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: at each step from a run's output to a belief value, what information does the kernel hold, and what does the value then ignore? Start from [ref:policy] §3 and §8 and [ref:estimand], then read belief.py, lineage.py, policy.py and composite.py. The goal's attachment models-context-report.md lists what 2026-09-12 settled; treat those as decisions, not findings. Known candidates to confirm or refute, each with the design line or code that causes it: unit weight (sample size, design, precision); the verdict collapsing a typed estimate and uncertainty into supported/refuted/inconclusive; inconclusive excluded, so a well-powered null is not evidence of absence (lim. 2); applicability unread (lim. 3); commensurable and co_scoped computed but read by nothing; dependence binary, so partial overlap counts like full duplication and not-certified counts like shared-source; a dependent assessment dropped from the selection rather than down-weighted; a dependent contradiction can neutralise but never overturn (lim. 4); no declared prior or plausibility; each claim aggregated alone, with composites reading rows and nothing propagated across them. For each item, record what is held, what is discarded, whether discarding it is deliberate (and why), and a concrete case where the value misleads. Proto-science's failure modes (attachment §4) are a check on each fix's cost: metadata that authors leave at defaults separates nothing. Output: [ref:inventory]. No proposals beyond naming what a fix would need.

Where to start: [ref:brief] supplies the two concrete confirmation/overlap cases and the current acceptance seam. Read python/src/beliefs/evaluation.py:_AcceptanceSelection and belief.py:AcceptancePolicy as well as the existing inventory inputs.

Bound: Keep the existing static information-loss inventory. For these cases, trace the acceptance callback's address-only interface and all-rejected answer, and the distinct-root/no-basis example in python/tests/test_lineage.py. Distinguish selection exposure from dataset ancestry; identify evidence absent from the snapshot. Do not fetch or validate the external program's full roster, invent its current certification result, or implement a feature.

Expected result: Preserve the full inventory requested above in [ref:inventory]. Add what current acceptance can express, what remains external, and what participant-overlap evidence the current lineage projection lacks. Mark the protocol/roster evidence unavailable in this checkout, and identify the inputs a later recommendation needs. Update [ref:brief] with findings; leave ownership and design recommendations to beliefs-5e66ba.

Ideas it wakes: On completion, run `tasks note beliefs-a91959 --no-reviewed "<finding>"` and `tasks note beliefs-6cd85f --no-reviewed "<finding>"` before this result's branch merges.

## References

- policy (input, required, kind=spec): docs/designs/2026-08-05-belief-policy-design.md — v1 rule, §3 rationale, §8 limitations
- estimand (input, kind=spec): docs/designs/2026-09-12-estimand-typing-design.md — what each assessment now carries in typed form
- inventory (output, kind=report): docs/notes/belief-information-loss-report.md — the inventory
- brief (input, required, kind=brief): docs/notes/2026-10-24-confirmation-independence-brief.md — concrete selection and participant-overlap cases for the inventory
