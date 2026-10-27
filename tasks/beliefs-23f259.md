---
id: beliefs-23f259
title: Isolate N2 child test homes from host Git hooks
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-27T17:54:02Z
updated: 2026-10-27T18:28:43Z
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
- 2026-10-27T18:20:34Z (design/7c612b-replica-publication): retained: {"host": "titan", "kind": "evidence", "path": "$WORK_ROOT/beliefs/beliefs-7c612b/cut47-runner.json", "state": "kept", "verification": "verified", "purpose": "Raw successor metadata refused by attachment layout gate; preserve exact command/storage mapping for N2 isolation repair and comparison", "next_owner": "task:beliefs-23f259", "cleanup_trigger": "After N2 isolation repair, recheck attachment exemption or preserve raw evidence before cleanup", "sha256": "7fd8f264239a9cd1fd2f2addebcc3b6b4444a5b1ee97a2fef592b4a1d092a0df"}
- 2026-10-27T18:28:43Z (design/7c612b-replica-publication): retained: {"host": "titan", "kind": "scratch", "path": "$WORK_ROOT/beliefs/beliefs-7c612b", "state": "kept", "verification": "verified", "purpose": "Contains only exact raw successor metadata refused by attachment layout gate and its manifest; compare while repairing N2 child isolation", "next_owner": "task:beliefs-23f259", "cleanup_trigger": "After isolation repair, recheck shipped attachment exemption and preserve exact raw bytes before cleanup", "manifest": "$WORK_ROOT/beliefs/beliefs-7c612b/retained-manifest.json", "sha256": "8a7cb08e3bfbc8528c59661d5b0493adac38ff27ecea9cfb18889fdb8a7fcb39"}
