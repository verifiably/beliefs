---
id: beliefs-e02ef3
title: Measure audit_world's second record pass and per-write mount opening at mm30 scale
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-01T18:25:11Z
updated: 2026-10-09T11:14:11Z
depends: []
parent: beliefs-7e341d
tags: [performance]
agent: claude-code/claude-opus-5-5
---

Why: two costs cut 44 (mount-citations) added are unmeasured. (1) audit_world (python/src/beliefs/audit.py) runs _record_findings twice per eligible corpus: once without the eligibility arm, then again with a _CapturedCitations reader so eligibility sees every corpus's malformedness set; the second pass re-checks every record only to keep its ELIGIBILITY_CODES findings. (2) A citing write in a session with read mounts opens a fresh ReadView of every read mount inside its capture hold (MountCitations._read_mount, corpus.py), indexing each mount whole, on every citing write (spec §10 limitation 1). From cut 44's final whole-branch review.

Approach: measure both on the mm30 replica: audit_world wall time over an epoch covering mm30 and a working corpus, before and after the two-pass split, and the per-write latency of an assessment citing mm30 from a mounted session. If either is material, weigh an eligibility-only second pass (no full _record_findings), and a mount view cache keyed by a cheap state witness, which does not exist yet; beliefs-655c10 asks for the same witness for coordination drift.

Done when: both numbers are recorded on this task and in the brief, and any remedy is filed or ruled unneeded.

Where: audit.py audit_world; corpus.py MountCitations._read_mount; docs/superpowers/specs/2026-10-01-mount-citations-design.md §10; brief docs/notes/2026-10-09-mount-citations-follow-ups-brief.md.

## Notes

- 2026-10-09T11:14:09Z (main): scope: scoped; measurement with a defined done, set todo P3 s/mid/direct under goal beliefs-7e341d, linked the state-witness overlap with beliefs-655c10; brief: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
