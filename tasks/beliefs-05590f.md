---
id: beliefs-05590f
title: "Declarations, guard, runner, the recent-cut row; run the cut"
status: doing
priority: 2
complexity: mid
process: direct
owner: design/live-query
created: 2026-09-25T02:24:58Z
updated: 2026-09-25T12:01:13Z
started: 2026-09-25T11:55:21Z
depends: [beliefs-b5adc3]
parent: beliefs-cc0aea
tags: []
agent: claude-code/claude-opus-5-5
plan: docs/superpowers/plans/2026-09-24-live-query-evaluation.md
step: "Task 5: Declarations, guard, runner, the recent-cut row; run the cut"
---

## Notes

- 2026-09-25T11:55:21Z (design/live-query): started
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T12:01:13Z (design/live-query): Guard green: uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q -> 30 passed. Pilot green under the Global Constraints acceptance exports: uv run --frozen pytest tests/acceptance/test_live_selection_acceptance.py tests/acceptance/test_n2_cut41.py -q -> 29 passed in 45.15s. Every arm sound (test_every_arm_fails_under_its_own_sabotage), every live check resolved (test_every_live_check_resolves_and_passes_without_sabotage). No rehoming needed. Detached cut41_acceptance.py run not launched; that is the controller's step.
