---
id: beliefs-b9c3ea
title: Establish the inputs and verdict for one-command mm30 recreation
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-29T22:59:41Z
updated: 2026-09-29T22:59:41Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
source: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
agent: codex
---

Question: What exact ordered invocations, external inputs and final assertions let a small recipe truthfully report that current mm30 recreation succeeded?
Where to start: python/tools/reproduction/{preflight,world,rederive,compose,read,findings,paths}.py, the remaining driver entry points, docs/designs/2026-09-05-mm30-reproduction.md §§10–11 and docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md §4. See docs/notes/2026-09-29-reproduction-audit-backlog-brief.md.
Bound: Trace the existing entry points and their state inputs/outputs once; compare fresh recreation with the documented read-in-place checks. Include the cut-22 and cut-31 archive requirements, compose and read --again, and steps that return zero after recording a defect. Inspect existing tests; do not run confinement, recreate or mutate the preserved corpus, build a runner framework, or implement the recipe.
Expected result: Record one exact proposed recipe sequence, required pre-existing artifacts and a minimal terminal-verdict check, with unavailable inputs named. Recommend whether a recipe alone suffices; update this task and the brief. Keep relocation as a separate operation. Account for the transition step owned by beliefs-0c1cc9 without duplicating it.
Ideas it wakes: On completion, run tasks note on beliefs-9e0b42 with the finding, in the same commit as this result.
