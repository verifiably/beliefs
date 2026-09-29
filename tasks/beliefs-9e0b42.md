---
id: beliefs-9e0b42
title: One-command mm30 driver run so the step order lives in one place
status: idea
priority: 2
created: 2026-09-10T22:01:42Z
updated: 2026-09-29T23:16:01Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
---

The ten-step order (preflight, world, concepts, select_target, analysis_inputs, type_target, hold, spec, run, belief, close, rederive) is spelled out separately in three plan docs and fixed only by each module's docstring; the 2026-09-10 rebuild retyped it as a shell loop. A justfile recipe taking SCIENCE_MM30_ROOT would make 'reproduces unaided' literally one command. The design declares the scripts throwaway, so scope this as a recipe, not a promoted surface.

## Scoping context (2026-09-29)

The current driver also has compose and two fresh-process read calls. world.main refuses an existing work root; rederive requires the preserved cut-22 state; several steps record defects but return zero. A shell loop needs a precise input and terminal-verdict contract before it can promise reproduction. Keep this an idea pending a bounded invocation inventory. Handoff: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md

## Notes

- 2026-09-29T22:59:41Z (main): scope: briefed; current sequence and success verdict need an invocation inventory; research beliefs-b9c3ea; brief: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
- 2026-09-29T23:16:01Z (research/beliefs-b9c3ea): finding (beliefs-b9c3ea, 2026-09-29): a recipe alone cannot report truthfully. Five steps (belief, rederive, close, compose's receipt check, read --again) record a defect and exit zero, and rederive needs the cut-22 archive at <work dir>.cut22, which a fresh directory lacks. Scope as: a just recipe over the design §13/§14 order with analysis_inputs restored, a read-only verdict step over state.json and findings.jsonl, and an environment override for paths.PRIOR. Body's ten-step order is stale. Inventory: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md, Recipe inventory
