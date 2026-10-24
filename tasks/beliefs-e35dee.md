---
id: beliefs-e35dee
title: "A main commit can make a frozen N2 arm vacuous, unseen until the next cut's chained run"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-09-24T16:14:31Z
updated: 2026-10-24T11:06:07Z
depends: []
parent: beliefs-199aeb
tags: [conformance, testing]
source: docs/plans/2026-09-24-conformance-cut-40-results.md §3.1
agent: claude-code/claude-opus-5-5
---

Question: What affordable pre-merge runtime net detects a live frozen N2 arm becoming vacuous after an ordinary kernel change?

Where to start: [ref:brief] distinguishes live guards from historical evidence and bounds this recommendation; [ref:testing-brief] retains the completed collection-preflight pilot. Read docs/plans/2026-09-24-conformance-cut-40-results.md §3.1, python/tests/test_n2.py (baseline, audit, PORTABLE_ARMS), python/tests/frozen_guards.py's newest-runner inventory, the live cut-19 J2i guard, and the existing cost task beliefs-f64cf1.

Established: main commit 70ff54e (beliefs-40e593) added a second mark_root_unresolved to the durable port, so J2i's single-site sabotage no longer failed its checks. The next cut's chained run discovered it a day later and required a bisect and repair on the cut-40 branch (567edbf, beliefs-50067c). At inspected main a7ce8ff, the ordinary suite still excludes tests/acceptance; portable N2 audits cuts 1–3 and 26, not every live acceptance guard. The origin/main push route omits standalone N2 because CI carries it; other pushes retain the full local suite. Neither route supplies the full live acceptance audit. CI's explicit uncertified-host mode skips only unavailable capabilities. beliefs-aa9f88's 2026-10-02 pilot detects uncollected replacements but proves neither runtime sensitivity nor absence of vacuity.

Bound: First pilot a healthy control and one copied-package reproduction of J2i-style vacuity through baseline and sabotage verdicts. Measure incremental live-N2-only cost before considering a full inventory sweep; coordinate common per-arm attribution with beliefs-f64cf1. Compare a recipe auditing only the newest runner's live N2 phases plus a source-change pre-merge rule against running the latest complete chained runner. Exclude cited-not-run guards. Do not add a gate, weaken existing coverage, edit frozen evidence, or perform a long run without an end-to-end pilot and the required host window.

Expected result: Record commands, source revision, certification/capability state, selected live inventory, detection verdicts and measured elapsed cost here and in [ref:brief]. Recommend a net and its trigger with explicit limits; distinguish portable, collection-only and runtime evidence. Correctness requires the healthy control to remain sound and the reproduced loss of sensitivity to be detected as vacuous, never as an import/collection failure. Any rollout needing design remains subsequent planned work.

Ideas it wakes: None directly. Coordinate findings with beliefs-f64cf1 and update [ref:brief]; beliefs-89542c already waits on that existing cost task, so do not create a duplicate research task or wait edge.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-conformance-readiness-brief.md — current prerequisites, evidence limits and remaining decisions
- testing-brief (input, required, kind=brief): docs/notes/2026-09-29-testing-backlog-brief.md — completed collection pilot and existing N2 cost work

## Notes

- 2026-10-02T16:52:50Z (research/n2-preflight-pilot): coordination from beliefs-aa9f88: named-check collection detects reproduced uncollected D8a replacement, but neither import nor collection establishes mutation soundness or vacuity; full runtime audit remains required. No overlap with this task's runtime question.
