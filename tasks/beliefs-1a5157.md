---
id: beliefs-1a5157
title: Implement the Beliefs publish act and governed records
status: doing
priority: 2
size: xl
complexity: high
process: planned
owner: design/publish
created: 2026-08-31T00:38:28Z
updated: 2026-09-23T11:39:55Z
started: 2026-09-22T21:54:25Z
depends: [beliefs-b34652, beliefs-1f7400]
tags: [migration, publication, coordination]
---


Outcome: Beliefs publishes an immutable selected view through a recoverable governed act, with publication marker and binding revisions, exact retry, terminal reporting, and recipient admission refusal.

Acceptance evidence: After coordination/view delivery and the world-read lane, bank the coordination-contract and act-report amendments; implement request fixation, staging, exact-prefix recovery, head export, replication, restore, reveal, atomic source binding/report, orphan repair semantics, and marker-required arrival; test every recovery-table state and destination refusal; and pass the complete gates before any real publish runs.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §§4.1 and 6 and §8 item 5; `docs/designs/2026-08-11-act-report-design.md`; and the root-lifecycle and log-verification designs.

Uncertainty: Destination-specific remote transport remains for Science, while this task owns only the Beliefs act and records. Coordination/view delivery is complete at cut 14 (beliefs-1f7400); the world-read lane discharged its last boundary at cut 38, which moved publish to tier 1 off the path as that lane's head. W17’s publication-binding intent-position arm belongs here.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: The user/autonomy design section 6 fixes the recovery protocol, but implementing exact-prefix resumption, intent-position binding, source reports, reveal/orphan handling and recipient refusal crosses interacting durability and governance boundaries. Contract amendments and a concrete cut remain.
- 2026-09-22T21:54:25Z (main): Process planned: xl/high, crosses durability and governance boundaries and needs contract amendments plus a slice design, plan and conformance cut; body refreshed for cut 38.
- 2026-09-22T21:54:25Z (main): started
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T21:54:25Z (main): claimed by claude-code/claude-opus-5-5, pid 1928635
- 2026-09-22T22:08:29Z (design/publish): Split into two slices: beliefs-d7d7d1 (records/evidence, cut 39) and beliefs-328507 (the act, cut 40).
- 2026-09-22T22:19:16Z (design/publish): parked (waiting on user, review): Slice 1 (beliefs-d7d7d1) spec awaiting user review; slice 2 (beliefs-328507) follows its discharge.
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T22:55:00Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T23:39:54Z (design/publish): parked (waiting on user, review): Slice 1 plan awaiting user review.
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T08:45:49Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T11:39:55Z (main): From the science projects design (science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §8): (1) whether dataset holdings travel is a property of the destination kind, not the selection: private directory and git remote carry records only, a Zenodo deposit carries holdings, a commons inbox defers to the commons world's policy; each destination kind should state it. (2) Deferral recorded: the coordination trail (question, hypothesis, decision) is not selectable by any view (view_query.py rejects non-world kinds and coord: addresses), so publishing it needs a publish-contract amendment; not requested now.
