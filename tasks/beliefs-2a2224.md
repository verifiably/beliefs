---
id: beliefs-2a2224
title: Establish the reserved-path manifest-safety remainder after S9
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-14T01:27:08Z
updated: 2026-10-14T01:27:08Z
depends: []
parent: beliefs-03d483
tags: [world-read]
source: docs/notes/2026-10-13-world-capture-safety-brief.md
agent: codex
---

Question: What reserved-path manifest-safety obligation remains in beliefs after S9, and should it receive a conformance boundary, ride along with an existing boundary, or be banked as a limitation?

Where to start: docs/notes/2026-10-13-world-capture-safety-brief.md; docs/superpowers/specs/2026-09-13-world-resolution-slice-3-design.md section 11.2 (root-level non-node files are not walk hazards); docs/designs/2026-08-02-substrate-consolidation-design.md S9; world-addressing design section 5; python/src/beliefs/world/registry.py corpus_state_identity, world/epoch.py _capture, corpus.py _collecting_view, and tests/test_manifest.py plus tests/test_world_view.py TestReportMode.

Bound: Produce a small obligation-to-code/test matrix for reserved non-node paths, malformed manifests, the four S9 construction findings, and path-collision. Distinguish already discharged behavior from unowned obligations and behavior that belongs solely to nodes. Trace each relevant consumer, reusing existing fixtures for a focused check only where static evidence cannot settle reachability. Do not broaden S9, implement a witness, change frozen cuts, or repair upstream code. If a nodes defect is suspected, check its issues, PRs, branches, and changelog before reproducing or patching it.

Expected result: Record a supported disposition on this task and in the brief: a named owning boundary/next task with an observable acceptance condition, or evidence for banking/dropping the original idea. Cite the exact behavior and tests instead of equating the ledger's old wording with a missing implementation.

Ideas it wakes: Before this result's branch merges, run tasks note beliefs-85df0f --no-reviewed "<finding and recommended disposition>".
