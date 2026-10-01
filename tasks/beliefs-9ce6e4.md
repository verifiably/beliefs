---
id: beliefs-9ce6e4
title: Assessment eligibility and evidence gathering across mounted corpora
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: cross-mount-eligibility
created: 2026-09-30T16:04:32Z
updated: 2026-10-01T10:18:34Z
started: 2026-10-01T09:35:48Z
depends: []
tags: [session]
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-10-01-mount-citations-design.md
---

An attended session writes one root and mounts N read corpora (cut 43). A run in the write root may observe a dataset whose record a read mount declares — a dataset's id derives from its content, so it is one world record and cannot be declared again in the write root without a duplicate-location that refuses every live selection. The run boundary accepts it (it needs only the address and a held path), but CorpusWriter._refuse_ineligible reads eligibility_refusal through the writer's own view, so the assessment over that run refuses EligibilityUnmet; gather/admission likewise read the proposition's own corpus. Needed: eligibility at the assess write, and evidence gathering and admission, resolving an observed dataset's declaration over the session's mounts. Science's coordination part 3 (sci-923d3a) keeps write-command dataset inputs in the write root and refuses a read mount's dataset by name until this lands; science's second-project milestone (sci-0d00d2) needs it to assess a working-corpus proposition over mm30 data.

## Notes

- 2026-09-30T16:04:32Z (main): concerns: beliefs-fe7149 extension — cross-corpus dataset inputs at assessment and admission, found in science's part 3 plan review round 2
- 2026-10-01T09:35:48Z (cross-mount-eligibility): started
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T09:35:48Z (cross-mount-eligibility): claimed by claude-code/claude-opus-5-5, pid 17260; brainstorming with beliefs-724941's scope question folded in (decided in this design, not after it)
- 2026-10-01T09:46:12Z (cross-mount-eligibility): Spec drafted: docs/superpowers/specs/2026-10-01-mount-citations-design.md (cut 44, rows J16-J21). Decision 2 answers beliefs-724941: one mount view covers eligibility, assesses target, estimand target, verification target, composite members; compared runs are caller-supplied RunClosure values.
- 2026-10-01T09:46:53Z (cross-mount-eligibility): parked (waiting on user, review): User (or a dispatched reviewer) reviews .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md; on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:15:02Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:15:02Z (cross-mount-eligibility): review: spec round 1 — verdict: revise; findings: P1 3, P2 2; reviewer: unknown (pasted by the user)
- 2026-10-01T10:18:27Z (cross-mount-eligibility): Round 1 disposition: all five accepted; producers union over session (3a), captured-only total world reader with unreadable class (8), eligibility reads base content only so audit_world keeps one profile (3), normalized mounted mapping (3.2); J16d witness is a mount-only claim operator in the estimand-target check
- 2026-10-01T10:18:34Z (cross-mount-eligibility): parked (waiting on user, review): Round 2 review of .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md (revisions at 9e5dcc1, §12 lists the round 1 dispositions); on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
