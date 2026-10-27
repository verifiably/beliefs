---
id: beliefs-23f259
title: Isolate N2 child test homes from host Git hooks
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-27T17:54:02Z
updated: 2026-10-27T17:54:02Z
depends: [beliefs-7c612b]
tags: []
source: beliefs-7c612b
agent: codex
origin: agent
---

Observed while running cut47 at feaf73b: the complete successor stopped in cut6 with 22 passes and two baseline failures, both test_git_is_not_an_identity_member. test_n2._run_check constructs a restricted environment but retains Path.home(), so historical and live scratch Git commits read host global hook configuration. No ownership-publication code caused this. Running with an empty task-owned HOME/XDG_CONFIG_HOME and disabled global/system Git configuration passed both Git baselines; with chain-equivalent certified roots, the full cut6 guard passed all 24 checks. Keep that runtime isolation for the current publication task. This follow-up should give N2 children a test-owned temporary home and explicit isolated Git configuration, preserve required cache/certified-root forwarding and all historical source/assertion pins, and prove the regression with a harmless sentinel host hook plus live/historical baselines. Do not alter host Git config, weaken checks, or treat a historical baseline failure as a sound mutation. Raw failure and successful isolated probe evidence are tracked on beliefs-7c612b; inspect before choosing the final repair scope.

## Notes

- 2026-10-27T17:54:02Z (add): created
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
