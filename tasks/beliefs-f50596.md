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
updated: 2026-10-02T13:11:42Z
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
