---
id: beliefs-ad68df
title: Certified-tuple tests fail in worktrees on WORK_ROOT storage
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-09-25T01:21:27Z
updated: 2026-09-25T01:21:27Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
---

A worktree under .worktrees/ lives on WORK_ROOT (/mnt/ssd3 on titan), whose ext4 options are not on atoms' flush-honoring-disk.v1 allowlist. conftest's certified work dir defaults to REPO_ROOT/.lifecycle-wrappers-test, so just test-fast in such a worktree fails ~216 tests and 33 errors with CapabilityUnavailable, and acceptance fixtures that use repo-relative roots fail too. Workaround used 2026-09-24 (beliefs-1af3fd): SCIENCE_CUT13_ROOT=<main checkout>/.lifecycle-wrappers-test for the portable suite, then acceptance rerun from main after the merge. Decide the fix: either just setup or the recipes point the certified root at a certified volume, or the allowlist admits the WORK_ROOT volume after it is certified. Acceptance roots need the same override.
