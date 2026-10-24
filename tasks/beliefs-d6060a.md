---
id: beliefs-d6060a
title: "What graphical-model practice offers the composite's deferred limits, and where each piece would live"
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-24T01:04:11Z
updated: 2026-10-24T01:45:41Z
depends: []
parent: beliefs-8060d0
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Question: the structure sense of model is settled and built ([ref:composites]: dag composites, belief-inert, read as rows; [ref:estimand]: identification and conditioning typed on the estimand). Do not re-derive that mapping. Instead, for each part the composite design defers, say what probabilistic and causal graphical-model practice offers and what it would need: adjustment sets, d-separation, Markov and faithfulness semantics (limitation 8, no owner); latent nodes and later shapes such as PAGs (limitations 4-6); relations between composites such as sub-structure, refinement and agreement (limitation 9); whether a belief policy may read composite structure (limitation 1); and claims about a composite as a whole (fit, discovery posteriors), which sit on the unbuilt non-empirical route (KER §11). Draw on the data-fusion and transportability literature (Bareinboim and Pearl) for applicability. For each piece, recommend where it lives: a beliefs reading over rows, a science command or tool, or the non-empirical route. Proto-science lessons in the goal's attachment models-context-report.md §4 apply: its exporters bit-rotted without a round trip, adjustment sets were hand-derived wrongly in all three projects, and the t034 rule that a graph never strengthens belief by assertion is worth keeping. Output: [ref:graphical].

## References

- composites (input, required, kind=spec): docs/designs/2026-09-12-composite-claims-design.md — dag composites and derived standing
- estimand (input, required, kind=spec): docs/designs/2026-09-12-estimand-typing-design.md — control.identification and applicability
- graphical (output, kind=report): docs/notes/graphical-model-mapping-report.md — the mapping
