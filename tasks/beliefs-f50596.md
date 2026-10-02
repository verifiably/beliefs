---
id: beliefs-f50596
title: "Publication marker: per-record attribution entries for carried records (science commons §4.8, §7.1)"
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: feat/publication-attribution
created: 2026-10-01T02:21:10Z
updated: 2026-10-02T13:58:25Z
started: 2026-10-02T12:47:02Z
depends: []
tags: [publication]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
---

Requirement from science's commons design (science docs/specs/2026-09-30-science-commons-design.md §4.8, §7.1): for every selected record the publisher's world holds in an adopted (ReplicaOf) corpus rather than a corpus it wrote, the marker carries (record address, origin corpus_id, origin marker uid); the origin is the adopted corpus's own marker unless that marker already carries the record, in which case the earlier entry is copied forward. Content frozen with the selection snapshot, never identity; inputs are the epoch's address map, the registry's ReplicaOf provenance, and each adopted corpus's marker facet. Field name, encoding and where in the act the inputs are read are the kernel's. Needed by science commons milestone 1a.

## Notes

- 2026-10-02T12:47:02Z (feat/publication-attribution): started
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T12:47:02Z (feat/publication-attribution): claimed by codex, harness daemon pid 11248; architectural design only in .worktrees/publication-attribution, branch feat/publication-attribution, stacked on acceptance discharge d466f5f. just setup passed. Main advanced independently by a vendored tooling update only. User order remains attribution next, then beliefs-aa9f88; written spec/plan gates remain.
- 2026-10-02T12:48:47Z (feat/publication-attribution): Verified end-to-end: evaluate_query ignores unmapped coordination/prose records when captured and published states agree; an adopted publication marker therefore needs no world-read drift change. Existing captured_records holds its marker. Coordination succession freezes existing top-level fields, so the proposed extension is published_from.attributions under a shipped v3 pin, with origin inputs frozen before intent and marker uid/address unchanged.
- 2026-10-02T13:11:16Z (feat/publication-attribution): Trial arm checked after the new instruction arrived: not enrolled, no trial for beliefs. Spec self-review completed: no placeholders; scope remains one publication slice; pinned checks use one private pure release predicate after shape/layout validation; corrected remote ordering to preserve identity, content and count checks before the release check. No implementation or plan has started.
- 2026-10-02T13:11:41Z (feat/publication-attribution): Written spec ready for user review: docs/superpowers/specs/2026-10-02-publication-attribution-design.md. Focused document guards passed, 23 tests in 1.02s; tasks check and git diff --check passed with no task warnings. The only changes are this proposed spec and task-record evidence; publication implementation and its plan remain gated on the written review.
- 2026-10-02T13:11:41Z (feat/publication-attribution): parked (waiting on user, review): User reviews .worktrees/publication-attribution/docs/superpowers/specs/2026-10-02-publication-attribution-design.md; after approval Codex resumes this worktree and writes the implementation plan.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T13:30:56Z (feat/publication-attribution): review: spec round 1 — verdict: revise; findings: P1 1, P2 2, P3 4; reviewer: claude-code/claude-opus-5-5
- 2026-10-02T13:30:57Z (feat/publication-attribution): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T13:33:12Z (feat/publication-attribution): Spec round 1 decisions: name the v2 carried-selection refusal and test its sorted ids plus earlier v2/v3 coordination disagreement; enable v3 only on new roots, compatible with Science commons §§11–12 without adding a re-pin act; refuse markerless ReplicaOf holdings rather than invent a carrier origin. Added missing-holder and first-invalid-holder checks. Verified P3 race correction: retirement retains admissions, so the second scan still supplies provenance; a genuinely missing admission fails closed. Every new publish scans, including v2 own-only; retries never scan. Legacy v2 missing origins remain unreconstructable, and coordination.tips_at is deliberately shape-only. Author accepts corrected spec under the reviewer/user fix-then-plan disposition; proceed to planning, no implementation.
- 2026-10-02T13:58:24Z (feat/publication-attribution): claimed by codex, harness daemon pid 11248; resumed in the existing locked .worktrees/publication-attribution worktree. Revised spec committed at dcc8a53, author-approved under the round-1 fix-then-plan disposition. Draft plan covers Tasks 0–7, 36 distinct units (Y5 3, Y17 16, Y18 17), ten durable functions, pre-change v2 byte fixtures, and the live cut-40 Y6-a retarget. Self-review checked spec coverage, signatures, failure precedence, actual baseline verdict resolved, and rule bindings vs profile activation. Focused document guards passed: 23 tests in 0.96s. No freeze, product change, task children, implementation agent or pilot has started.
- 2026-10-02T13:58:24Z (feat/publication-attribution): parked (waiting on user, review): User reviews .worktrees/publication-attribution/docs/superpowers/plans/2026-10-02-publication-attribution.md; after approval Codex resumes native execution here, rechecks cut numbering and begins Task 0.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
