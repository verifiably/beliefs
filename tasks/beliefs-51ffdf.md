---
id: beliefs-51ffdf
title: The reproduction and cut-32 runners resolve the main checkout through the worktree's real path
status: done
priority: 2
created: 2026-09-16T20:09:14Z
updated: 2026-09-26T08:17:48Z
completed: 2026-09-26T08:17:48Z
depends: []
tags: [conformance, reproduction]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
model: claude-opus-5-5
---

python/tools/reproduction/paths.py and python/tools/cut32_acceptance.py both derive the main checkout from the repository root's real path (the grandparent when the parent is named .worktrees). Where .worktrees/ is a symlink onto a separate work-root volume, the real path's grandparent is on that volume, not beside the main checkout, so the derived default work roots land somewhere the checkout does not own. Every cut 32 run therefore needed SCIENCE_CUT*_ROOT, SCIENCE_MM30_ROOT and MM30_PREDECESSOR exported by hand, and the reproduction's preflight refused once before they were. Resolve the main checkout from git's own worktree list (the first entry of 'git worktree list --porcelain') instead of from the path shape, and keep the exports as an override.

## Notes

- 2026-09-26T08:17:48Z (fix/worktree-certified-roots): done
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-26T08:17:48Z (fix/worktree-certified-roots): fixed by beliefs-ad68df: tools/checkout.py reads git's worktree link instead of the path shape; exports remain overrides
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
