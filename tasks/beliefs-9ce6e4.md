---
id: beliefs-9ce6e4
title: Assessment eligibility and evidence gathering across mounted corpora
status: done
priority: 2
size: m
complexity: high
process: planned
owner: cross-mount-eligibility
created: 2026-09-30T16:04:32Z
updated: 2026-10-01T20:50:46Z
started: 2026-10-01T09:35:48Z
completed: 2026-10-01T20:50:46Z
depends: []
tags: [session]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-10-01-mount-citations-design.md
plan: docs/superpowers/plans/2026-10-01-mount-citations.md
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
- 2026-10-01T10:29:56Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:29:56Z (cross-mount-eligibility): review: spec round 2 — verdict: revise; findings: P1 3, P2 1; reviewer: unknown (pasted by the user)
- 2026-10-01T10:32:58Z (cross-mount-eligibility): Round 2 disposition: all four accepted; validity over the mount view (session producers), citation view default for _refuse_facets on every caller and session producers in both _ImportView overlays, audit producers include published_producers with producers-incomplete for unmapped datasets, decision 3 now writer-profile decoding plus CitationContractMismatch on differing shared-namespace pins (J16d arms it)
- 2026-10-01T10:32:58Z (cross-mount-eligibility): parked (waiting on user, review): Round 3 review of .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md (§12 lists round 1-2 dispositions); on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:39:27Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:39:27Z (cross-mount-eligibility): review: spec round 3 — verdict: revise; findings: P1 1, P2 1; reviewer: unknown (pasted by the user)
- 2026-10-01T10:40:59Z (cross-mount-eligibility): Round 3 disposition: both accepted; acquisition_view judges bearer/validity over the session both directions (produces targets resolve into mounts, producers union) while overlays stay local; retrieval reports explicitly local to their dataset (validity_refusal gains reports=); decision 3 restated as policy; limitation 7 records per-corpus bearer findings
- 2026-10-01T10:40:59Z (cross-mount-eligibility): parked (waiting on user, review): Round 4 review of .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md (§12 lists rounds 1-3); on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:52:01Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T10:52:01Z (cross-mount-eligibility): review: spec round 4 — verdict: revise; findings: P2 2, P3 1; reviewer: unknown (pasted by the user)
- 2026-10-01T10:53:41Z (cross-mount-eligibility): Round 4 disposition: all three accepted; acquisition_view(base, local=) with reports=local on _refuse_facets paths and reports=holder in eligibility; J16h retargeted to bypass acquisition_view on revise; J16 import expects ImportRefused caused by AcquisitionBoundaryRefused; J16l added
- 2026-10-01T10:53:42Z (cross-mount-eligibility): parked (waiting on user, review): Round 5 review of .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md (§12 lists rounds 1-4); on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T11:02:17Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T11:02:17Z (cross-mount-eligibility): review: spec round 5 — verdict: revise; findings: P1 1, P2 1, P3 1; reviewer: unknown (pasted by the user)
- 2026-10-01T11:03:08Z (cross-mount-eligibility): Round 5 disposition: all three accepted; eligibility on _ImportView paths resolves through the overlay and judges validity with session producers (J16 imported-assessment case, J16m); J16h passes local to both judgments; plain write names AcquisitionBoundaryRefused
- 2026-10-01T11:03:08Z (cross-mount-eligibility): parked (waiting on user, review): Round 6 review of .worktrees/cross-mount-eligibility/docs/superpowers/specs/2026-10-01-mount-citations-design.md (§12 lists rounds 1-5); on accept: close beliefs-724941 citing decision 2, file the science §4 task, then writing-plans for cut 44
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T11:06:58Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T11:06:58Z (cross-mount-eligibility): review: spec round 6 — verdict: accept; findings: none; reviewer: unknown (pasted by the user)
- 2026-10-01T11:07:28Z (cross-mount-eligibility): Spec approved at round 6. beliefs-724941 closed (decision 2). Science consumer task sci-dc0381 filed; sci-13050a and sci-0d00d2 depend on it and on this task.
- 2026-10-01T11:28:12Z (cross-mount-eligibility): Plan drafted: docs/superpowers/plans/2026-10-01-mount-citations.md (Tasks 0-10, cut 44, 24 arms/24 units/6 rows). Planning found B4 (cut 22) promises nothing refuses for an unheld observed dataset in a corpus-local gather; J21 supersedes that clause by citation (spec §13), B4b and F4 re-targeted. mm30 pins shipped biology (24bcec43), so decision 3 passes for a shipped-pack working corpus.
- 2026-10-01T11:28:41Z (cross-mount-eligibility): parked (waiting on user, review): Plan review of .worktrees/cross-mount-eligibility/docs/superpowers/plans/2026-10-01-mount-citations.md (and spec §13's B4 supersession) plus execution-method choice; on accept: Task 0 (freeze cut 44), file the step children
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:02:54Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:02:54Z (cross-mount-eligibility): User decisions 2026-10-01: keep J21 and supersede B4's absent-dataset clause by citation, frozen record preserved; execution is sequential subagent-driven with a fresh review after each task.
- 2026-10-01T12:02:54Z (cross-mount-eligibility): review: plan round 1 — verdict: revise; findings: P1 1, P2 5, P3 1; reviewer: unknown (pasted by the user)
- 2026-10-01T12:06:41Z (cross-mount-eligibility): Plan round 1 disposition: all seven accepted (c0ed4f9): canonical-id malformedness, per-dataset producers-incomplete, J17 cites through an assessment, testing-capable fixtures, explicit gather args, J20 durable against a one-corpus baseline, test-one front door.
- 2026-10-01T12:06:41Z (cross-mount-eligibility): parked (waiting on user, review): Plan round 2 review of .worktrees/cross-mount-eligibility/docs/superpowers/plans/2026-10-01-mount-citations.md (revisions at c0ed4f9); on accept: Task 0 (freeze cut 44, file step children), then sequential subagent-driven execution with a fresh review per task
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:26:10Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:26:10Z (cross-mount-eligibility): review: plan round 2 — verdict: revise; findings: P2 3; reviewer: unknown (pasted by the user)
- 2026-10-01T12:27:14Z (cross-mount-eligibility): Plan round 2 disposition: all three accepted; incompleteness only when the dataset would otherwise pass (validity_refusal with known producers), J20 pins read once before removal, J20 lineage asserts producers/not_present before and after removal.
- 2026-10-01T12:27:14Z (cross-mount-eligibility): parked (waiting on user, review): Plan round 3 review of .worktrees/cross-mount-eligibility/docs/superpowers/plans/2026-10-01-mount-citations.md; on accept: Task 0 (freeze cut 44, file step children), then sequential subagent-driven execution with a fresh review per task
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:44:22Z (cross-mount-eligibility): resumed
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T12:44:22Z (cross-mount-eligibility): review: plan round 3 — verdict: accept; findings: none; reviewer: human
- 2026-10-01T20:50:46Z (cross-mount-eligibility): done
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T20:50:46Z (cross-mount-eligibility): cut 44 discharged: citations over read mounts, session-wide acquisition invariants, eligibility classes in both checks, corpus-local reads refuse unheld inputs and runs
  provenance: {"harness_session":"claude-code:ba7ce184-780b-4707-a2f5-de54e91daee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
