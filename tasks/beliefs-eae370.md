---
id: beliefs-eae370
title: The doors and the orphan fold — `beliefs/publication_doors.py`
status: done
priority: 2
complexity: high
process: direct
owner: design/publish
created: 2026-09-22T23:12:05Z
updated: 2026-09-23T11:40:19Z
started: 2026-09-23T11:17:33Z
completed: 2026-09-23T11:40:19Z
depends: [beliefs-ec5974]
parent: beliefs-d7d7d1
tags: []
agent: claude-code/claude-opus-5-5
plan: docs/superpowers/plans/2026-09-22-publication-records.md
step: "Task 6: The doors and the orphan fold — `beliefs/publication_doors.py`"
---

## Notes

- 2026-09-23T11:17:33Z (design/publish): started
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T11:40:01Z (design/publish): Ruling 6 (controller): LogEvidenceRefused is a beliefs.errors type, so publication_doors.py catches it directly (no atoms import). Step 0 lets it propagate (nothing revealed or written). Step 8: _judge (called only by the guard) catches it around both readings and returns PositionRefused('chain-malformed'), so the guard records evidence-refused/chain-malformed with corpus_id, marker and remotely_revealed; EVIDENCE_REFUSAL_REASONS not widened. The catch sits in _judge because W17-p-a's frozen before pins the guard's first line at 8-space indent (a try in the guard would break its after). Pinned by test_an_engine_refusal_to_inspect_at_step_0_propagates_before_the_intent and test_an_engine_refusal_to_inspect_at_step_8_is_an_evidence_refusal_that_keeps_the_orphan[written|other].
- 2026-09-23T11:40:01Z (design/publish): Adaptations to the brief: (1) cut 35's live arm T2-c pins the _append_operation_intent operation-intent line, so payload= takes its own early-return branch and the digest-shape check moved to _checked_intent_digest (unpinned); (2) the entry-point Case probes _publication_probe = (_corpus_probe, chain length) instead of _corpus_probe alone, since a durable write shows in the chain; (3) the portable step-8 tests use an advancing clock and a post-intent sibling so Y2-a and W17-p-b are observable portably. All seven frozen publication_doors.py befores occur once; each after parses and fails the portable module.
- 2026-09-23T11:40:19Z (design/publish): done
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T11:40:19Z (design/publish): publication_doors.py: step-0 intent door, step-8 binding door through execute_fulfilling_guarded, the orphan fold; PublicationRefused; _append_operation_intent(payload=); _bind_publication inventoried with a Case; Ruling 6 pinned
  provenance: {"harness_session":"claude-code:9a178026-a9d1-42aa-8035-08fc78013fed","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
