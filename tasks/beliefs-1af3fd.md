---
id: beliefs-1af3fd
title: "CoordinationResolver: public enumeration of standing tips by kind"
status: done
priority: 2
size: s
complexity: low
process: direct
owner: feat/resolver-enumeration
created: 2026-09-24T10:43:33Z
updated: 2026-09-25T01:11:54Z
started: 2026-09-25T00:53:30Z
completed: 2026-09-25T01:11:54Z
depends: []
tags: [coordination]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S3
model: "claude-opus-5-5[1m]"
agent: claude-code/claude-opus-5-5
---

Requested by science's coordination command set design (§8 S3). The resolver resolves addresses only; enumeration is the private _revisions(). Requirement: a public method returning every address of a given kind, optionally within one project, each with its resolution (the tip's Node, or CoordinationRefused divergent-view with its tips), over exactly the resolver's mounts. Names stay content the kernel never consults (§3.3): science matches names over the enumeration. Needed for project-select by name, projects and project-show; the mount set is the authority on visibility and becomes multi-corpus with beliefs-fe7149, so a surface-side scan would have to track it.

## Notes

- 2026-09-25T00:53:30Z (feat/resolver-enumeration): started
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T00:53:30Z (feat/resolver-enumeration): claimed by claude-code/claude-opus-5-5, pid 707902; process direct, worktree .worktrees/resolver-enumeration
- 2026-09-25T01:11:54Z (feat/resolver-enumeration): worktree on WORK_ROOT (/mnt/ssd3) fails the durability allowlist: capability tests need SCIENCE_CUT13_ROOT on the main volume; acceptance roots stay repo-relative, so acceptance verified from main after merge
- 2026-09-25T01:11:54Z (feat/resolver-enumeration): done
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T01:11:54Z (feat/resolver-enumeration): CoordinationResolver.standing(kind, project=None): every address of a kind over the mounts, each with resolve()'s value; mixed-kind address raises MalformedRecord
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
