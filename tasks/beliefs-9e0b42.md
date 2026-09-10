---
id: beliefs-9e0b42
title: One-command mm30 driver run so the step order lives in one place
status: idea
priority: 2
created: 2026-09-10T22:01:42Z
updated: 2026-09-10T22:01:42Z
depends: []
tags: [reproduction]
---

The ten-step order (preflight, world, concepts, select_target, analysis_inputs, type_target, hold, spec, run, belief, close, rederive) is spelled out separately in three plan docs and fixed only by each module's docstring; the 2026-09-10 rebuild retyped it as a shell loop. A justfile recipe taking SCIENCE_MM30_ROOT would make 'reproduces unaided' literally one command. The design declares the scripts throwaway, so scope this as a recipe, not a promoted surface.
