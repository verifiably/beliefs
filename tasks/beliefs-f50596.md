---
id: beliefs-f50596
title: "Publication marker: per-record attribution entries for carried records (science commons §4.8, §7.1)"
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-10-01T02:21:10Z
updated: 2026-10-01T02:21:10Z
depends: []
tags: [publication]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
---

Requirement from science's commons design (science docs/specs/2026-09-30-science-commons-design.md §4.8, §7.1): for every selected record the publisher's world holds in an adopted (ReplicaOf) corpus rather than a corpus it wrote, the marker carries (record address, origin corpus_id, origin marker uid); the origin is the adopted corpus's own marker unless that marker already carries the record, in which case the earlier entry is copied forward. Content frozen with the selection snapshot, never identity; inputs are the epoch's address map, the registry's ReplicaOf provenance, and each adopted corpus's marker facet. Field name, encoding and where in the act the inputs are read are the kernel's. Needed by science commons milestone 1a.
