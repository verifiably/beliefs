---
id: beliefs-0e523a
title: "World resolution slice 4: world view evaluation"
status: todo
priority: 2
size: l
complexity: high
created: 2026-09-09T15:26:54Z
updated: 2026-09-12T16:26:55Z
depends: [beliefs-46847c]
parent: beliefs-d248ba
tags: [world-read]
---

Design and freeze W7 view evaluation over the completed world resolver, following docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md section 1 and docs/plans/2026-08-29-implementation-roadmap.md. Preserve explicit epoch binding and deterministic query semantics. At discharge audit all world-resolution and packaging-remainder labels, including W8 and W8b conformance selection; beliefs-fda0e5 repaired the measured W8b build defect, but did not select the row; close the parent only when every retained obligation is proved or explicitly assigned to remaining work.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: W7 still needs its view-evaluation design over explicit epochs and deterministic query semantics, followed by a complete W8/W8b and packaging accounting. The landed world reader does not settle that evaluator or the remaining conformance selection.
