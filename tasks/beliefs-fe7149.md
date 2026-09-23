---
id: beliefs-fe7149
title: "Attended session: one write root, N mounted read corpora, coordination resolution over all"
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-23T11:40:35Z
updated: 2026-09-23T11:40:35Z
depends: []
tags: [session]
agent: claude-code/claude-fable-5-1
---

open_attended_session refuses unless corpus_roots names exactly one root (session/__init__.py) and its CoordinationResolver mounts only that root, while the read side already opens one view per configured root. The science projects design (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §3.1) needs a session that writes to one corpus and reads every configured one: a write root named separately from the read set; each mounted corpus read under the profile its own manifest pins (mm30 pins the mm30 corpus-local contract; a working corpus pins base + biology + coordination); coordination tip resolution over every mounted corpus, which coordination-and-view-kinds §6.3 already states as world-wide. Prerequisite of the second-project milestone (§9.2). The kernel owns how a mounted corpus's profile is compiled and cached; science adds write_root beside corpus_roots when this lands.
