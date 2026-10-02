---
id: beliefs-f50596
title: "Publication marker: per-record attribution entries for carried records (science commons §4.8, §7.1)"
status: done
priority: 2
size: m
complexity: high
process: planned
owner: feat/publication-attribution
created: 2026-10-01T02:21:10Z
updated: 2026-10-02T17:29:49Z
started: 2026-10-02T12:47:02Z
completed: 2026-10-02T16:43:23Z
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
- 2026-10-02T14:22:09Z (feat/publication-attribution): review: spec round 2 — verdict: accept; findings: none; reviewer: claude-code/claude-opus-5-5
- 2026-10-02T14:22:09Z (feat/publication-attribution): review: plan round 1 — verdict: accept; findings: P3 3; reviewer: claude-code/claude-opus-5-5
- 2026-10-02T14:22:10Z (feat/publication-attribution): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T14:23:31Z (feat/publication-attribution): Author approves spec dcc8a53 and plan 47a2260 after spec round 2 and plan round 1 acceptance. Native execution resumed; cut recheck finds maximum 45 across refs and all three worktrees, successor 46 available. Pre-change byte fixtures: marker beef9590baed6442330e4c85e4c673cc974a2feb41d3738ae48c39e4d6e38a07; selection a475656c573635014fe8cd8d9ee4df977ace92a8bf7fbe3547421e7d2de02182.
- 2026-10-02T14:29:38Z (feat/publication-attribution): Freeze 5981ae6; v2 fixture bytes committed unchanged. Task 0 passes 23 docs, 5994 fast tests with 1 existing skip; tasks check zero warnings.
- 2026-10-02T15:32:05Z (feat/publication-attribution): review: impl round 1 — verdict: revise; findings: P2 1; reviewer: codex/gpt-6-astra
- 2026-10-02T15:47:32Z (feat/publication-attribution): review: impl round 2 — verdict: accept; findings: P3 1; reviewer: codex/gpt-6-astra
- 2026-10-02T15:57:33Z (feat/publication-attribution): claimed by codex, pid 3565319; Task7 remains doing until repaired-source successor and final documentation checks complete. Scoped correction review accepted; no Critical/Important remains.
- 2026-10-02T16:41:56Z (feat/publication-attribution): cut46 evidence: complete repaired-source successor at 454fc55 passed 76 phases/1172 invocations without skips in 3808.561s; all36 mutations sound, durable14/14. Results docs/plans/2026-10-02-conformance-cut-46-results.md; Y5 amendment reclosed, Y17/Y18 closed; 226/253 closed, 27 open.
- 2026-10-02T16:43:23Z (feat/publication-attribution): done
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T16:43:23Z (feat/publication-attribution): Publication attribution discharged at cut46: explicit v3 new roots, frozen/forwarded origins and pinned release refusals; full certified successor1172 passes/all36 sound;226/253 rows closed.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T16:46:22Z (main): integration: personal-main merge prepared cleanly; all16 tested source/declaration hashes unchanged and independent ops-check6 retained. Static check0errors/0warnings. Pre-commit merged fast run6079 passed/1 existing skip/1 pin-guard failure: frozen_guards.holds compares committed HEAD (old main lacks cut45 declaration), while staged/live declaration exactly matches d466f5f SHA e845aff4e54eb74e88b561e77aa9fd6be4afe6246851b87fd95ee78e95e4d94b. Commit merge then rerun against merged HEAD; no source or guard change.
- 2026-10-02T16:52:50Z (research/n2-preflight-pilot): integration verified: local merge3a59054 now passes committed-HEAD pin guard1/1 in3.58s and full fast6080 passed/1 existing skip in106.03s; merged static0errors/0warnings. Earlier pre-commit pin failure was HEAD-vs-staged-state only; no code/guard changed. Main source hashes equal certified successor inputs; no external write.
- 2026-10-02T17:25:29Z (research/n2-preflight-pilot): cleanup: fully merged publication worktree removed after integration3a59054; branch retained; tt-report harvested, no host pointers or unmerged changes. Certified runner logs remain in main .work/acceptance.
- 2026-10-02T17:26:11Z (research/n2-preflight-pilot): cleanup status correction: the preceding cleanup note describes the prepared outcome; worktree removal is pending final document checks and commit. Its clean/merged/pointer checks and timing harvest are complete.
- 2026-10-02T17:29:49Z (main): cleanup complete: git worktree removal succeeded; only main remains registered. Publication branch is fully merged and retained; certified successor logs preserved.
