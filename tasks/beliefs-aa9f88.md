---
id: beliefs-aa9f88
title: Determine whether a collection preflight catches stale N2 replacements affordably
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: research/n2-preflight-pilot
created: 2026-09-29T22:33:07Z
updated: 2026-10-02T16:55:27Z
started: 2026-10-02T16:48:02Z
completed: 2026-10-02T16:55:26Z
depends: []
parent: beliefs-287026
tags: [testing]
source: docs/notes/2026-09-29-testing-backlog-brief.md
agent: codex
---

Question: Can a bounded preflight detect syntactically valid stale sabotages that break test collection, beyond the ast.parse check already owned by beliefs-1b0827?

Where to start: docs/notes/2026-09-29-testing-backlog-brief.md; python/tests/arm_staleness.py::stale_arms; python/tests/test_n2.py::_sabotage, _run_check and audit; python/tests/acceptance/test_n2_cut20.py's D8a override; docs/plans/2026-09-16-conformance-cut-32-results.md §3.2–3.3; beliefs-1b0827, beliefs-e35dee and beliefs-f64cf1.

Bound: In an isolated worktree, compare parse-only, module import, and collection of the arm's named checks on one healthy control, one syntax-breaking mutation, and the documented D8a stale-after case (or a faithful minimal reproduction if historical dependencies prevent replay). Use copied packages, never live source mutation. Run through just test-one and record capability/environment limits. No full-arm sweep, implementation rollout, new gate or benchmark campaign.

Expected result: Record which probes distinguish each case, elapsed cost for this pilot, limitations of import versus pytest collection, and a recommendation with acceptance criteria on this task and in the brief. Coordinate with the existing syntax, vacuity and cost tasks rather than duplicate them. This is a measurement and recommendation task, not a promise that collection proves sabotage correctness.

Ideas it wakes: On completion, run tasks note beliefs-89542c with the finding in the same commit as the result; update the brief so a later scope pass can reconsider the idea.

## Notes

- 2026-10-02T16:48:02Z (research/n2-preflight-pilot): started
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T16:48:02Z (research/n2-preflight-pilot): claimed by codex/gpt-6.1, pid3565319; process direct; isolated .worktrees/n2-preflight-pilot on research/n2-preflight-pilot, base3a59054. Scope is exactly three copied-package cases times parse/import/named-check collection, through just test-one; no rollout or full-arm sweep.
- 2026-10-02T16:52:50Z (research/n2-preflight-pilot): pilot: nine just test-one probes, copied packages only,13.96s total incl first-use uv hydration. Valid D8a replacement parse/import/collect exits0/0/0, collection one test; syntax1/1/4; syntactically valid missing-edges replacement0/0/4, collection MalformedContract edges through acceptance conftest/profiles. Wall collection1.074-2.371s; module import misses this fixture-dependent failure. Original package hashes unchanged; no full sweep, runtime durability or rollout.
- 2026-10-02T16:52:50Z (research/n2-preflight-pilot): recommendation: retain parse in beliefs-1b0827; inform beliefs-f64cf1 N2 cost/placement with named-check collection; do not add always-on gate from three cases. Accept only copied resolution/all named checks collected; exit4/zero collection refuses invalid audit input, never sound. Keep full audits for vacuity/runtime and benchmark broader cost only within existing cost task. Updated source brief with environment, exact cases, commands and acceptance criteria.
- 2026-10-02T16:55:26Z (research/n2-preflight-pilot): verification: focused designs/guide23 passed in1.14s; just check0errors/0warnings; fast6080 passed/1 existing skip in87.02s, no affected TypeScript tests; taskscheck clean. Original source hashes unchanged, all nine probe outputs inspected through collection verdicts. Task-start multi-worktree uncommitted warning resolved by claim commit7414bc2.
- 2026-10-02T16:55:26Z (research/n2-preflight-pilot): done
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T16:55:26Z (research/n2-preflight-pilot): Completed bounded nine-probe pilot: collection detects valid stale D8a omitted-edges replacement missed by parse/import;1.074-2.371s per process,13.96s incl hydration; brief and existing syntax/vacuity/cost/idea notes updated, no gate rollout.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
