---
id: beliefs-ff2529
title: "Realize the coordination task kind through the tasks CLI: a commands-as-tools seam, not a second task system"
status: idea
priority: 2
created: 2026-09-16T21:45:25Z
updated: 2026-09-16T21:45:25Z
depends: []
tags: [coordination, contract]
agent: "claude-code/claude-opus-5[1m]"
---

The user/autonomy design (docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md) mints task/decision/note as coordination kinds (§4.1: attributed acts, governed, never belief inputs; §4.4: the queue is derived, what persists is the choice). The tasks CLI (khughitt/tasks) already is that: one markdown record per task, derived ready queue, start as the recorded choice, notes as attributed acts, a claim store for liveness, JSON as its only interface, and a protocol twenty projects run daily. Proposal: a versioned amendment to the coordination contract under which a coordination task is realized by a tasks record — science's coordination writes shell out to tasks (the §7.4 commands-as-tools seam, as autonomy already treats science), the corpus-write adapter records the act with the task id, and tasks never learns beliefs exists (the rule quick-add imposed between tasks and mindful). Not: minting task content in the corpus a second time; not: teaching tasks any science kind — cross-references are opaque refs tasks stores and never interprets (as source is today). Open: what the act record carries (id, revision, checkout), whether decision and note follow (tasks note is close; decision is not a tasks concept), and where the derived queue lives when autonomy's priority function (§7.3) ranks it — tasks next with a pluggable priority is the candidate. Related: tasks-96b215 (can science index a tasks record as a node by format alone); beliefs-abf8e8 (splitting contracts/coordination out). Scope after the current contract cut (beliefs-eacbe2) and the publish act (beliefs-1a5157); the seam is a user-layer concern, not a kernel one. From a design conversation in ai on 2026-09-16.
