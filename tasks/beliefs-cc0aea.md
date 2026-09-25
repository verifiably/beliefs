---
id: beliefs-cc0aea
title: "Live, unpublished view-query evaluation for attention reads"
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-24T10:43:33Z
updated: 2026-09-24T10:43:33Z
depends: []
tags: [world-read, coordination]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S1
agent: claude-code/claude-opus-5-5
---

Requested by science's coordination command set design (docs/specs/2026-09-24-coordination-command-set-design.md §8 S1, decision 3). evaluate_query denotes a ViewQuery only over a WorldReadView at a published epoch and refuses corpus-drifted once any corpus moves past it (coordination-and-view-kinds §6.2), and no science command may publish an epoch (framework §4.4). A project's next would therefore refuse after the first write until an operator republished. Requirement: denote a ViewQuery over the mounted corpora's current captured state without building or publishing an epoch, returning a selection whose stamp names the capture rather than any epoch identity, so no consumer can mistake it for an epoch-bound answer. Publish and every epoch-bound read are unchanged. Rationale: the queue is attention, not belief input — §6.2's own argument for live coordination resolution ('no packaging step mediates seeing your own task edit') covers seeing your own new proposition in your project's queue. Function vs view type is the kernel's call. Blocks science's project-scoped next.
