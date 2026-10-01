---
id: beliefs-e02ef3
title: Measure audit_world's second record pass and per-write mount opening at mm30 scale
status: idea
priority: 2
created: 2026-10-01T18:25:11Z
updated: 2026-10-01T18:25:11Z
depends: []
tags: [performance]
agent: claude-code/claude-opus-5-5
---

From cut 44's final whole-branch review (mount-citations). Two costs the lane added are unmeasured. (1) audit_world (python/src/beliefs/audit.py) now runs _record_findings twice per eligible corpus: once without the eligibility arm, then again with a _CapturedCitations reader so eligibility sees every corpus's malformedness set; the second pass re-checks every record only to keep its ELIGIBILITY_CODES findings. (2) A citing write in a session with read mounts opens a fresh ReadView of every read mount inside its capture hold (MountCitations._read_mount, corpus.py), indexing each mount whole, on every citing write (spec §10 limitation 1). Measure both on the mm30 replica: audit_world wall time over an epoch covering mm30 and a working corpus, before and after the two-pass split, and the per-write latency of an assessment citing mm30 from a mounted session. If either is material, the remedies to weigh are an eligibility-only second pass (no full _record_findings), and a mount view cache keyed by a cheap state witness, which does not exist yet. Done when both numbers are recorded and any remedy is filed or ruled unneeded.
