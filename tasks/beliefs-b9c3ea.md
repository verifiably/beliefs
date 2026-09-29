---
id: beliefs-b9c3ea
title: Establish the inputs and verdict for one-command mm30 recreation
status: done
priority: 3
size: s
complexity: mid
process: direct
owner: research/beliefs-b9c3ea
created: 2026-09-29T22:59:41Z
updated: 2026-09-29T23:16:01Z
started: 2026-09-29T23:11:22Z
completed: 2026-09-29T23:16:01Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
source: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
model: claude-fable-5-1
agent: codex
---

Question: What exact ordered invocations, external inputs and final assertions let a small recipe truthfully report that current mm30 recreation succeeded?
Where to start: python/tools/reproduction/{preflight,world,rederive,compose,read,findings,paths}.py, the remaining driver entry points, docs/designs/2026-09-05-mm30-reproduction.md §§10–11 and docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md §4. See docs/notes/2026-09-29-reproduction-audit-backlog-brief.md.
Bound: Trace the existing entry points and their state inputs/outputs once; compare fresh recreation with the documented read-in-place checks. Include the cut-22 and cut-31 archive requirements, compose and read --again, and steps that return zero after recording a defect. Inspect existing tests; do not run confinement, recreate or mutate the preserved corpus, build a runner framework, or implement the recipe.
Expected result: Record one exact proposed recipe sequence, required pre-existing artifacts and a minimal terminal-verdict check, with unavailable inputs named. Recommend whether a recipe alone suffices; update this task and the brief. Keep relocation as a separate operation. Account for the transition step owned by beliefs-0c1cc9 without duplicating it.
Ideas it wakes: On completion, run tasks note on beliefs-9e0b42 with the finding, in the same commit as this result.

## Notes

- 2026-09-29T23:11:22Z (research/beliefs-b9c3ea): started
  provenance: {"harness_session":"claude-code:786b5be4-402f-41ae-9587-17839b760c79","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-29T23:11:22Z (research/beliefs-b9c3ea): claimed by claude-code/claude-fable-5-1, harness pid 2351564; process direct in .worktrees/beliefs-b9c3ea
- 2026-09-29T23:16:01Z (research/beliefs-b9c3ea): result recorded in the brief's Recipe inventory section: 19-invocation sequence, six pre-existing inputs with their state on this host, per-step exit-code table, run-invariant verdict. Not run: preflight, any driver step, a linked prior archive. beliefs-0c1cc9's transition step is a named slot in the sequence, not duplicated
- 2026-09-29T23:16:01Z (research/beliefs-b9c3ea): done
  provenance: {"harness_session":"claude-code:786b5be4-402f-41ae-9587-17839b760c79","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-29T23:16:01Z (research/beliefs-b9c3ea): Inventoried the mm30 recreation recipe: sequence, inputs, exit-code gaps and a run-invariant verdict; a recipe needs a verdict step and a prior-archive override
  provenance: {"harness_session":"claude-code:786b5be4-402f-41ae-9587-17839b760c79","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
