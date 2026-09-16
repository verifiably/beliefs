---
id: beliefs-6776d3
title: No U7 arm exercises check_composite through audit_world's _recompute dispatch
status: idea
priority: 2
created: 2026-09-16T20:09:29Z
updated: 2026-09-16T20:09:29Z
depends: []
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

Cut 32 Task 5 wired check_composite into both of audit.py's per-kind dispatches — audit_corpus's loop and audit_world's _recompute — so the world audit reaches it (design §4.3, not repeating the gap estimand typing's limitation 14 records for check_spec_target). Every U7 acceptance arm reaches it through audit_corpus or by calling check_composite directly; none goes through audit_world, and test_u7's comment claims the dispatch it does not exercise. One world-audit arm over a damaged composite in a captured world corpus would hold the wiring the design asked for.
