---
id: beliefs-8060d0
title: "Evidence aggregation beyond the unit-weight count: research the long-term direction"
status: todo
priority: 2
created: 2026-10-24T01:04:04Z
updated: 2026-10-24T01:45:39Z
depends: []
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Why: science.belief.v1 is a signed count of independent directional assessments at unit weight, chosen deliberately as the smallest uncalibrated surface (belief-policy design §3, §8). It discards signal: a 1,000-patient and a 10-patient study count the same, effect size and precision are not read, inconclusive results move nothing, and partial dependence is treated as full. The successor design (beliefs-638318, shelved until a real belief needs unequal weights) would be easier to write well from research done ahead of it. Raised by the user 2026-10-23 after a guided tour of beliefs (vdocs-9ca77b).

Start from [ref:context]. The 2026-09-12 models work already settled the frame and built two foundations: model as structure (dag composites, cut 32), estimator (typed estimand, estimate and uncertainty, cut 31) and generator (runs); a single model layer was rejected; composites are belief-inert and read as rows. This research builds on that and does not re-open it. Its job is the parts left open: aggregation over the typed quantities, what graphical-model practice offers the composite's deferred limitations, and which of the pieces handed to science should be built there.

Pieces: the inventory of where signal is discarded first; then prior art and the graphical-model gaps; then one synthesis that recommends a direction. Research only: no kernel change and no successor policy design here. Related: beliefs-638318 (weighted-belief design), beliefs-8b26dc (observation-first direction), beliefs-a91959 (independent confirmation vs secondary analysis), beliefs-6cd85f (participant-overlap evidence), beliefs-9e1f60 (higher-order moratorium), and the science-side ideas filed 2026-10-23 for composites on the daily surface.

## References

- context (input, required, kind=report): files:models-context-report.md — what 2026-09-12 settled, what science was handed, what is deferred, proto lessons

## Notes

- 2026-10-24T01:44:53Z (main): attached: models-context-report.md (6246 bytes): What 2026-09-12 settled, what was handed to science and never filed, what is deferred, and proto-science's lessons
