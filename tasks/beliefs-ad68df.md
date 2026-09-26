---
id: beliefs-ad68df
title: Certified-tuple tests fail in worktrees on WORK_ROOT storage
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: main
created: 2026-09-25T01:21:27Z
updated: 2026-09-26T08:07:28Z
started: 2026-09-26T08:07:28Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
---

A worktree under .worktrees/ lives on WORK_ROOT (/mnt/ssd3 on titan), whose ext4 options are not on atoms' flush-honoring-disk.v1 allowlist. conftest's certified work dir defaults to REPO_ROOT/.lifecycle-wrappers-test, so just test-fast in such a worktree fails ~216 tests and 33 errors with CapabilityUnavailable, and acceptance fixtures that use repo-relative roots fail too. Workaround used 2026-09-24 (beliefs-1af3fd): SCIENCE_CUT13_ROOT=<main checkout>/.lifecycle-wrappers-test for the portable suite, then acceptance rerun from main after the merge. Decide the fix: either just setup or the recipes point the certified root at a certified volume, or the allowlist admits the WORK_ROOT volume after it is certified. Acceptance roots need the same override.

## Notes

- 2026-09-25T10:00:51Z (main): 2026-09-25: the N2 harness (test_n2.py::_run_check) forwards only SCIENCE_CUT4-10_ROOT and SCIENCE_MM30_ROOT to each check's child pytest, so SCIENCE_CUT13_ROOT does not reach guard children: cut 38's baseline failed 11 checks in a WORK_ROOT worktree on unchanged code. Exporting SCIENCE_CUT10_ROOT=<main>/.lifecycle-wrappers-test (read first by tests/conftest.py) plus SCIENCE_CUT4_ROOT=<main>/.cut4-acceptance made the cut 19 and 38 guards pass (17 tests, 42 s). The fix should cover guard children too.
- 2026-09-26T08:07:28Z (main): started
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-26T08:07:28Z (main): claimed by claude-code opus-5-5, pid 438313; fix in-repo: point certified roots (conftest + N2 guard children) at the main checkout's volume
