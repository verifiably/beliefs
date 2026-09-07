---
id: beliefs-5aad8c
title: Consolidate work roots under a single .work/ instead of the project root
status: todo
priority: 3
size: m
created: 2026-09-07T09:48:53Z
updated: 2026-09-07T09:49:14Z
depends: [beliefs-1b6534]
tags: [testing]
---

Thirteen git-ignored work-root directories sit at the project root (.cut4/5/6/7/8/9/19-acceptance, .cut14-merge-cache, .lifecycle-wrappers-test, .mm30-reproduction, .mm30-reproduction-cut21), against five genuine hidden dirs (.git, .worktrees, .claude, .agents, .codex). They drown the real ones.

Proposal: one hidden root, e.g.
  .work/acceptance/cut21/        was .cut21-acceptance/
  .work/reproduction/mm30-cut21/ was .mm30-reproduction-cut21/
  .work/merge-cache/cut14/       was .cut14-merge-cache/
One .gitignore line (.work/), and it absorbs the non-cut variants a bare ./acceptance/ would not. Prefer hidden over a visible ./cuts or ./acceptance: these are ignored scratch, and a visible root entry is more intrusive to someone browsing the repo, not less.

DURABILITY IS NOT AN OBSTACLE. The allowlist is a volume certification held in atoms, not a path rule — root.py:271: 'Science holds no tuple data, no allowlist and no override: admitting a new volume configuration is an atoms certification amendment.' A subdirectory is the same device (verified: repo root, .cut19-acceptance and .worktrees all report device 66306), so the certification is untouched.

Scope: 17 runners each carry one line, DEFAULT_WORK = PYTHON_ROOT.parent / '.cutN-acceptance'; plus python/tests/acceptance/conftest.py's SCIENCE_CUT4_ROOT default; plus tools/reproduction's mm30 default; plus .gitignore. SCIENCE_CUT*_ROOT already overrides, so hosts are unaffected.

ADOPT FORWARD, NEVER MIGRATE THE FROZEN RECORDS. Of 25 docs naming these paths, 11 are conformance results records (cuts 7-19). Those state the work root a past run actually used; rewriting them would make them assert something false about the past, which the repo's own rule forbids (invalidated frozen evidence is pinned and cited, never edited). Leave every results record alone. Old .gitignore lines can be pruned once nothing cites them.

Verification is the hard part, not the edit: proving a runner still works means re-running its chain, and most chains cannot run today (cut 20 absent; cut 5 carries 15 pre-existing failures, beliefs-1b6534). Do this when a chain can be exercised, not blind.
