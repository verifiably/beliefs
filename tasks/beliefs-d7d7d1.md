---
id: beliefs-d7d7d1
title: "Publication records: coordination amendment, publish intent and the intent-position rule (cut 39)"
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: design/publish
created: 2026-09-22T22:08:29Z
updated: 2026-09-23T16:43:16Z
started: 2026-09-22T22:08:29Z
depends: []
parent: beliefs-1a5157
tags: [publication, coordination]
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-09-22-publication-records-design.md
plan: docs/superpowers/plans/2026-09-22-publication-records.md
---

Slice 1 of publish: ship coordination contract v1+v2 (publication, publication-binding, composite/composes), deterministic marker/binding factories, the science.publish-intent.v1 intent with anchors, standing_at over registration moments, the step-0 intent door and step-8 binding door, the act-report publish kind. Closes W17 and Y1-Y4. Spec: docs/superpowers/specs/2026-09-22-publication-records-design.md

## Notes

- 2026-09-22T22:08:29Z (design/publish): started
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T22:19:16Z (design/publish): First independent review: 12 findings, all folded in at e7d9c31 (moment seam 4 answers, orphan fields on every refusal, separate marker address, predecessor-not-standing as single-writer detection, sabotage per unit, permit/WRITE_ENTRY_POINTS gaps).
- 2026-09-22T22:19:16Z (design/publish): parked (waiting on user, review): User reviews docs/superpowers/specs/2026-09-22-publication-records-design.md in .worktrees/publish; on approval write the plan (writing-plans), freezing cut 39's unit list in Task 0.
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T22:46:33Z (design/publish): User review: #1/#3 already fixed at e7d9c31; #2 (presence from chain inventory, bytes required, history-violated, re-read classification) and #4 (marker carries destination) taken at e7fb05d. W17-p-f needs a durable rollback; Task 0 finds one or W17 reports partial.
- 2026-09-22T22:55:00Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T22:55:00Z (design/publish): Spec approved by user after re-review (601e22f); writing the plan.
- 2026-09-22T23:39:54Z (design/publish): Plan written (dd8b275), reviewed once (15 findings, all applied at acac917).
- 2026-09-22T23:39:54Z (design/publish): parked (waiting on user, review): User reviews docs/superpowers/plans/2026-09-22-publication-records.md; on approval execute Task 0 (beliefs-ff3c13) via subagent-driven development.
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T01:04:11Z (design/publish): User plan review: 5 findings applied at 72f0f55 (creation requires ABSENT->file, history-violated for rewrite; orphan fold qualifies reports, report-unqualified; stored outcome via constructors; selection ids via NodeId.parse; W17-p-c before fixed). Accounting (14,13,5).
- 2026-09-23T01:15:52Z (design/publish): User plan review 2 applied at da5f559: validate-before-sort (tips, Anchor, decoder), stored-path tests re-identified with control and rule messages, conditional accounting table frozen by Task 0's REPLACE_UNREGISTERED and ROLLBACK_MEANS.
- 2026-09-23T08:45:49Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T08:45:49Z (design/publish): User approved the plan after review 3 (fix at 192ae53); executing via subagent-driven development, controller claude-code session 9a178026.
- 2026-09-23T09:11:43Z (design/publish): Cut 39 frozen: ROLLBACK_MEANS=patched create effect; REPLACE_UNREGISTERED=accepted; RETRY_AFTER_ROLLBACK=same intent; accounting row 14/13/5, W17 closes, Task 7 passes 16; chains cut 38.
- 2026-09-23T09:19:33Z (design/publish): Cut 39 re-frozen after review fix round 1: CUT39_FREEZE_COMMIT=8e81e1ac72ac9838bc863d07b93e2cdbfa31ad8c, CUT39_FROZEN_SHA256=b92c7a2052e97d2ccc75fbb7fbb07b5d53d90ecc99904be666c61d9dd9dd7a43 (supersedes 15fd610); verdicts and row 14/13/5 unchanged.
- 2026-09-23T16:43:16Z (design/publish): parked (waiting on user): Waits on the held merge (beliefs-fc5063); then close with the cut 39 discharge line.
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
