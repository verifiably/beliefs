---
id: beliefs-7c612b
title: A relocated replica of the world's own corpus is refused as a foreign publication
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: design/7c612b-replica-publication
created: 2026-10-27T12:47:43Z
updated: 2026-10-27T16:52:17Z
started: 2026-10-27T14:38:26Z
depends: []
tags: [publication]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
spec: docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md
plan: docs/superpowers/plans/2026-10-27-owned-replica-publication.md
---

science's publish-preview of a view over the mm30 corpus, relocated into the user's world and admitted replica-of, refused kernel-refused attribution-contract-unpinned naming corpus 8b5d0c80 (under coordination v3 it would demand a publication marker the relocation does not carry). The publish act has no notion of a replica the same person relocated, so no view over that corpus can be published. Evidence: science docs/records/2026-10-26-second-project-milestone.md §4 R4, §5 F12 (design-gap).

## Notes

- 2026-10-27T12:47:43Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-27T14:38:26Z (main): started
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T14:39:13Z (design/7c612b-replica-publication): resumed
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T14:40:29Z (design/7c612b-replica-publication): Planned path in .worktrees/7c612b-replica-publication (design/7c612b-replica-publication); just setup succeeded. Full-suite baseline deferred to execution Setup per the planned-work rule. Source intent recovered from sci-0d00d2 and Claude sessions 74a061f4-8320-41fa-a2a3-a3ce105dd286 and 8b479072-91d3-4b9c-b77c-d178525b6574: user accepted the milestone measurement, reviewer required attribution discrepancy filing, agent filed F12. Cut 46 decision 8 explicitly refuses markerless restored own corpora; changing that is a design amendment, not a missing branch in an existing guarantee.
- 2026-10-27T14:42:47Z (design/7c612b-replica-publication): Scope discovery: science commons spec section 9, amendment 2026-10-22 Deviation 6, and python/src/science/acceptance.py already treat hand-configured markerless roots as Own, excluding sharing-registry roots. Recommended design is an explicit own-corpus declaration at publication preparation, independently guarded against captured publication markers, rather than a new registry provenance type or forced fork. This is the agent recommendation, not recorded user approval. Science publish and preview wiring is required for the milestone; sci-775e90 owns the eventual live rerun.
- 2026-10-27T14:48:01Z (design/7c612b-replica-publication): retained: {"host":"titan","kind":"worktree","path":".worktrees/7c612b-replica-publication","state":"kept","verification":"verified","purpose":"Frozen ownership-declaration design and subsequent reviewed implementation; builder check is running against 338c71f","next_owner":"task:beliefs-7c612b","cleanup_trigger":"After the approved implementation is integrated, inspect evidence and run the required worktree-removal checks"}
- 2026-10-27T14:48:47Z (design/7c612b-replica-publication): review: spec round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6-astra
- 2026-10-27T14:48:50Z (design/7c612b-replica-publication): attached: builder-check-report.md (412 bytes): Read-only builder check of frozen design 338c71f; reviewer codex/gpt-6-astra
- 2026-10-27T14:48:52Z (design/7c612b-replica-publication): retained: {"host":"titan","kind":"worktree","path":".worktrees/7c612b-replica-publication","state":"kept","verification":"verified","purpose":"Design 338c71f awaits user review; builder check accepted with no findings and is attached as builder-check-report.md; pre-commit checks and tasks check passed; no code changes or baseline tests yet","next_owner":"task:beliefs-7c612b","cleanup_trigger":"After the approved implementation is integrated, inspect evidence and run the required worktree-removal checks"}
- 2026-10-27T14:48:55Z (design/7c612b-replica-publication): parked (waiting on user, review): User reviews beliefs commit 338c71f:docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md in .worktrees/7c612b-replica-publication. After acceptance, agent resumes here, records the user review, drafts the implementation plan with writing-plans, and files the science consumer integration dependency for sci-775e90; implementation waits for plan review.
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T15:46:07Z (design/7c612b-replica-publication): resumed
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T15:46:11Z (design/7c612b-replica-publication): review: spec round 2 — verdict: revise; findings: Important 1, Minor 5; reviewer: claude-code/claude-opus-5-5
- 2026-10-27T15:50:11Z (design/7c612b-replica-publication): Spec revised at deb8d99 after round 2: I1 and M1-M5 accepted and addressed. User instructed fix-then-plan; proceeding to the implementation plan without inventing a separate acceptance review round. Science consumer integration is sci-9a7ce2, dependent on this kernel task; sci-775e90 now depends on both. No science implementation or live changes performed.
- 2026-10-27T15:58:04Z (design/7c612b-replica-publication): attached: spec-round-2-report.md (5475 bytes): Full relayed spec round 2 review of frozen 338c71f; reviewer claude-code/claude-opus-5-5
- 2026-10-27T15:58:06Z (design/7c612b-replica-publication): attached: design-review-ledger.md (3191 bytes): Controller rulings I1 and M1-M5, revised spec deb8d99, consumer handoff and plan self-review
- 2026-10-27T16:01:06Z (design/7c612b-replica-publication): review: plan round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6-astra
- 2026-10-27T16:01:08Z (design/7c612b-replica-publication): Controller self-review of frozen plan 69577b6 (not user approval): spec coverage, step clarity, type consistency, review-focus tests and proportion checked; no outstanding findings. Plan SHA-256 9bcec8c8325374ae94a289b33969c143def52f904f3679b198e8507cb8b61815. Revised spec deb8d99 SHA-256 720261f5edd22248a3d8441bdff16b7296db25d6168164c5c1b5ad119c455fb4. Four sequential children: beliefs-ecb75f, beliefs-991a0f, beliefs-eab322, beliefs-b367fd. First step is blocked on user plan review. Both documentation commits passed full pre-commit checks; no test-suite baseline or implementation has run.
- 2026-10-27T16:01:11Z (design/7c612b-replica-publication): retained: {"host":"titan","kind":"worktree","path":".worktrees/7c612b-replica-publication","state":"kept","verification":"verified","purpose":"Revised spec deb8d99 and implementation plan 69577b6; waiting for user plan review, then unblock beliefs-ecb75f and run execution Setup baseline","next_owner":"task:beliefs-7c612b","cleanup_trigger":"After approved implementation is reviewed and integrated, inspect attached review evidence and perform required worktree-removal checks"}
- 2026-10-27T16:01:29Z (design/7c612b-replica-publication): retained: {"host":"titan","kind":"evidence","path":"$WORK_ROOT/beliefs/.worktrees/7c612b-replica-publication/.superpowers/sdd/7c612b","state":"kept","verification":"verified","purpose":"Full spec round 2 report and I1/M1-M5 controller rulings; bytes verified equal to task attachments spec-round-2-report.md and design-review-ledger.md","next_owner":"task:beliefs-7c612b","cleanup_trigger":"At worktree removal after reviewed integration, verify attachments and ensure every ledger ruling reached the final report before disposing of these duplicate workspace copies","manifest":"$WORK_ROOT/beliefs/.worktrees/7c612b-replica-publication/.superpowers/sdd/7c612b/manifest.json","sha256":"c73ad8e0f93701ab5c57b82896ab6c8f6e319fb8ba113fad753fdde0f04fb84b"}
- 2026-10-27T16:01:32Z (design/7c612b-replica-publication): parked (waiting on user, review): User reviews beliefs commit 69577b6:docs/superpowers/plans/2026-10-27-owned-replica-publication.md, implementing revised spec deb8d99, in .worktrees/7c612b-replica-publication. On acceptance, agent records the review, unblocks and starts beliefs-ecb75f, runs trial-arm and the deferred just test baseline, then executes the four steps inline with final independent review. No implementation is running.
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-27T16:52:17Z (design/7c612b-replica-publication): resumed
  provenance: {"harness_session":"codex:01a17dcb-2a5d-7101-9aa7-305b6690786c","harness_session_source":"CODEX_THREAD_ID"}
