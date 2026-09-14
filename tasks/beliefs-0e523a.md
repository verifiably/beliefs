---
id: beliefs-0e523a
title: "World resolution slice 4: world view evaluation"
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: design/world-resolution-slice-4
created: 2026-09-09T15:26:54Z
updated: 2026-09-14T03:26:43Z
started: 2026-09-14T03:10:08Z
depends: [beliefs-46847c]
parent: beliefs-d248ba
tags: [world-read]
spec: docs/superpowers/specs/2026-09-13-world-resolution-slice-4-design.md
---

Design and freeze W7 view evaluation over the completed world resolver, following docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md section 1 and docs/plans/2026-08-29-implementation-roadmap.md. Preserve explicit epoch binding and deterministic query semantics. At discharge audit all world-resolution and packaging-remainder labels, including W8 and W8b conformance selection; beliefs-fda0e5 repaired the measured W8b build defect, but did not select the row; close the parent only when every retained obligation is proved or explicitly assigned to remaining work.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: W7 still needs its view-evaluation design over explicit epochs and deterministic query semantics, followed by a complete W8/W8b and packaging accounting. The landed world reader does not settle that evaluator or the remaining conformance selection.
- 2026-09-13T17:05:26Z (design/world-resolution-slice-3): from slice 3: W8 and W8b remain retained and unselected; audit both labels at slice 4's discharge (slice 3 design §11 item 3)
- 2026-09-14T03:09:34Z (main): Process planned: W7 view evaluation is an undesigned slice; it needs a slice design and freeze like slices 1-3 (cuts 23/24/25/27). Rule-6 reading 2026-09-13: slice 3 merged at cut 27, no kernel lane open, this is the on-path head, so it opens; estimand-typing and composite-claim stay parked off-path.
- 2026-09-14T03:26:43Z (design/world-resolution-slice-4): Design drafted 2026-09-13: evaluate_query over WorldReadView (world/selection.py), W7 selected, W8 part (search-term arm deferred to authority-labels, re-homed at discharge), W8b selected over existing code, W14 stays tier 3; cut 28 claimed at freeze
