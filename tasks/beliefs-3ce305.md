---
id: beliefs-3ce305
title: "The publish act, remote: transport seam, remote reveal and orphans, divergent-publication (cut 42)"
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: design/publish
created: 2026-09-24T02:36:23Z
updated: 2026-09-26T08:59:01Z
started: 2026-09-26T08:38:03Z
depends: [beliefs-328507]
parent: beliefs-1a5157
tags: [publication]
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-09-26-publish-act-remote-design.md
---

Third slice of publish, split from beliefs-328507 by the user on 2026-09-23. Owns layer design §6.1 step 7 (transport as an injected seam, verified complete or not complete), the remote reveal and the orphans it creates, cut 39's Ruling 12 (an exception before any effect at step 8 leaves the intent unfinished rather than orphaned, so a remotely revealed marker must be recovered from the unfinished intent; leading candidate: step 0 refuses while an earlier publish to the same view and destination is unfinished and has a request record), the recovery table's remote rows, and the recipient's divergent-publication. Designed after cut 40 discharges.

## Notes

- 2026-09-25T10:06:03Z (main): Renumbered cut 41 → 42 on 2026-09-25 by the user's decision: live view-query evaluation (beliefs-cc0aea) freezes as cut 41, prefixing cut 40. Living docs on main still say cut 41 for this slice until beliefs-cc0aea's freeze commit relabels them (its plan, Task 0 Step 1); do not freeze this slice as 41.
- 2026-09-25T10:39:08Z (design/live-query): renumbered cut 41 → 42 on 2026-09-25: live view-query evaluation froze as cut 41 (beliefs-cc0aea), by the user's decision of 2026-09-25
- 2026-09-26T08:38:03Z (main): started
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-26T08:38:03Z (main): claimed by claude-code opus-5-5, pid 438313; brainstorming the cut-42 spec in .worktrees/publish
- 2026-09-26T08:47:20Z (design/publish): spec drafted: docs/superpowers/specs/2026-09-26-publish-act-remote-design.md (Y11-Y16, 12 arms); awaiting user review
- 2026-09-26T08:47:27Z (design/publish): parked (waiting on user, review): user reviews docs/superpowers/specs/2026-09-26-publish-act-remote-design.md in .worktrees/publish; on approval, the agent writes the cut-42 plan (writing-plans) there
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-26T08:59:01Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:3615b71e-88b4-402a-972d-ae857c1808d4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-26T08:59:01Z (design/publish): spec review round 1: four findings verified against code (orphan scenario unreachable at intent position; mark not checked against export; listing blind to extras; tip reading lacks corpus-level layout checks); revising
