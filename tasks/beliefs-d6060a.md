---
id: beliefs-d6060a
title: "Map claims, assessments and composites onto probabilistic and causal graphical models"
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-24T01:04:11Z
updated: 2026-10-24T01:04:11Z
depends: []
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: how does the kernel's model (typed propositions with causal/statistical/structural layers and polarity; assessments with typed estimands, identification and applicability; dag composites over claims) relate to probabilistic and causal graphical models as used in scientific practice? Cover: whether a causal proposition reads as an edge in a causal DAG and an assessment as evidence about that edge under its identification strategy; what the data-fusion and transportability literature (combining heterogeneous experimental and observational sources, Bareinboim and Pearl) says about the applicability gap; what inference across related claims a graphical model would allow that per-claim aggregation cannot ([ref:composites] says a composite is never a claim and a path's standing is its rows); and what a model-based belief would require of records the kernel does not hold today. Output: [ref:graphical], with each correspondence marked as exact, partial or absent.

## References

- composites (input, required, kind=spec): docs/designs/2026-09-12-composite-claims-design.md — dag composites and derived standing
- estimand (input, required, kind=spec): docs/designs/2026-09-12-estimand-typing-design.md — control.identification and applicability
- graphical (output, kind=report): docs/notes/graphical-model-mapping-report.md — the mapping
