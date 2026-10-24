---
id: beliefs-7edb06
title: Survey prior art in evidence aggregation against the kernel's constraints
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-24T01:04:09Z
updated: 2026-10-24T01:04:16Z
depends: [beliefs-9bf498]
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: what do established methods for combining evidence offer a successor belief policy, and which of them survive the kernel's constraints? Constraints to judge against (from [ref:policy]): every value carries a receipt over its exact inputs and a named policy binding; independence is derived from dataset lineage, not asserted; literature never bears on empirical belief; a value must not be rendered as a probability unless it is one; reproducible and deterministic. Families to cover, at least: fixed- and random-effects meta-analysis and inverse-variance weighting; Bayesian evidence synthesis and hierarchical models, including how priors are declared and audited; likelihood ratios and Bayes factors; e-values and their merging under arbitrary dependence (relevant to not-certified pairs); correlation-aware combination of dependent estimates; information-theoretic measures of the evidence an analysis carries and of the value of information for choosing the next analysis; graded-certainty frameworks such as GRADE; belief functions (Dempster-Shafer). For each: what it needs as input, which inventory item (beliefs inventory task, same goal) it would address, what it costs in assumptions, and whether it fits the receipt and determinism rules. Use quarry or lit for sources where they help; cite primary sources. Output: [ref:prior-art].

## References

- policy (context, kind=spec): docs/designs/2026-08-05-belief-policy-design.md — the constraints a successor must keep
- prior-art (output, kind=report): docs/notes/evidence-aggregation-prior-art-report.md — the survey
