---
id: beliefs-97075f
title: "ResultManifest keeps declared-target order in memory but sorts when stored, so equivalence reads failed for identical outputs"
status: done
priority: 1
size: s
complexity: mid
process: direct
owner: fix/manifest-order
created: 2026-09-23T18:49:35Z
updated: 2026-09-24T02:24:04Z
started: 2026-09-24T02:13:16Z
completed: 2026-09-24T02:24:04Z
depends: []
tags: [verification]
model: "claude-opus-5-5[1m]"
agent: claude-code/claude-opus-5-5
---

Observed 2026-09-23 (science belief-path Task 9, sci-5fe8fc): a RunMinted's in-memory run.result is ResultManifest(outputs=(('outputs/stats.tsv', …), ('outputs/outcome.txt', …))) in the workflow's target order, while decode_run_closure of the stored run yields the same pairs sorted. replay.CONTENT_EQUALITY (_manifest_equality: original == replayed, tuple equality) therefore answers 'failed' when a stored original is compared with a fresh replay whose targets are not in sorted order, though every digest agrees; build_verification mints verdict 'failed'. An audit that re-derives from the two stored runs computes 'passed' and disagrees with the stored verdict. The reproduction driver compared two in-memory closures in one order and never saw it. Expected: ResultManifest canonicalizes (sorts) outputs at construction, or the equivalence compares canonical forms; a test builds a manifest in unsorted order and asserts it equals its stored round trip. Science builds its verification from both stored forms meanwhile.

## Notes

- 2026-09-24T02:13:06Z (main): process direct: the task names the fix (canonical order at construction) and the round-trip test
- 2026-09-24T02:13:16Z (fix/manifest-order): started
  provenance: {"harness_session":"claude-code:99a95437-3bde-4503-a0dd-5f5a57cd7bd2","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T02:13:16Z (fix/manifest-order): claimed by claude-code opus-5-5, pid 3181057
- 2026-09-24T02:24:04Z (fix/manifest-order): done
  provenance: {"harness_session":"claude-code:99a95437-3bde-4503-a0dd-5f5a57cd7bd2","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T02:24:04Z (fix/manifest-order): ResultManifest sorts its outputs at construction, so a declared-order manifest equals its stored round trip and CONTENT_EQUALITY passes; test_runrecord pins it
  provenance: {"harness_session":"claude-code:99a95437-3bde-4503-a0dd-5f5a57cd7bd2","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
