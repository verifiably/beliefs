---
id: beliefs-ae33ff
title: Determine the capture inputs a world-wide retraction fold needs
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-29T22:50:05Z
updated: 2026-09-29T22:50:05Z
depends: []
parent: beliefs-0c50ed
tags: [world-read]
source: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
agent: codex
---

Question: Can derivation recompute cross-corpus retraction standing from the current Capture.rule_input, or what minimum versioned input change is required?
Where to start: python/src/beliefs/world/epoch.py:_captured_records and _standing_retractions; world/derive.py:CapturedRetraction and Capture.rule_input; world/rules_v1/retraction.py; corpus.py:retraction_standing; tests/test_world_standing.py:TestTheSplit; correction-remainder slice 1 design §11.1 and slice 2 §14.2. Read docs/notes/2026-09-29-retraction-standing-backlog-brief.md and beliefs-eacbe2 before recommending ownership.
Bound: Trace the capture-to-rule-to-receipt-to-reader path and compare the information needed for node, route and snapshot targets, including deprecated references. Use the existing split-counterexample and at most one small local probe to distinguish input sufficiency from a schema change. No production change, new rule version, frozen-cut edit, or full conformance run.
Expected result: Record an input/identity impact inventory and a recommendation in this task and the brief: keep the fail-closed limitation, or hand a precisely bounded successor-rule design to contract-cut. Identify fixture and receipt obligations; unchanged output shape does not mean unchanged identity.
Ideas it wakes: On completion, run tasks note on beliefs-c800ef with the finding in the same commit as this result.
