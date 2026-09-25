---
id: beliefs-1af3fd
title: "CoordinationResolver: public enumeration of standing tips by kind"
status: todo
priority: 2
size: s
complexity: low
process: direct
created: 2026-09-24T10:43:33Z
updated: 2026-09-24T10:43:33Z
depends: []
tags: [coordination]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S3
agent: claude-code/claude-opus-5-5
---

Requested by science's coordination command set design (§8 S3). The resolver resolves addresses only; enumeration is the private _revisions(). Requirement: a public method returning every address of a given kind, optionally within one project, each with its resolution (the tip's Node, or CoordinationRefused divergent-view with its tips), over exactly the resolver's mounts. Names stay content the kernel never consults (§3.3): science matches names over the enumeration. Needed for project-select by name, projects and project-show; the mount set is the authority on visibility and becomes multi-corpus with beliefs-fe7149, so a surface-side scan would have to track it.
