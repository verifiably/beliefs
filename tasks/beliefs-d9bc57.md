---
id: beliefs-d9bc57
title: "Acceptance predicate on gather: counts(corpus_id, address) before retraction folding, policy in the context (science commons §9)"
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: feat/acceptance-filter
created: 2026-10-01T02:21:10Z
updated: 2026-10-02T10:12:18Z
started: 2026-10-02T08:09:25Z
depends: []
tags: [belief]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
spec: docs/superpowers/specs/2026-10-02-belief-acceptance-design.md
---

Requirement from science's commons design §9: belief must count a record only when the reader's acceptance policy says so, and the filter must apply to assessments, verifications and correction records before any of their effects and before any pool-level rule (retraction standing and the identity collapse included). Science hands a view, not records, and gather takes the retraction enumeration from the view and folds standing before any assessment is decoded, so the filter must be kernel-side: a predicate counts(corpus_id, address) supplied to gather and consulted before standing is folded, plus the caller's policy statement carried into the reproducibility context so the answer explains both the evidence considered and how it was selected. node_corpus already attributes nodes to corpora; the world and pin state are what the predicate encapsulates. Needed by milestone 1a.

## Notes

- 2026-10-02T08:09:25Z (main): started
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T08:09:25Z (main): Scope confirmed: acceptance filtering first, publication attribution second, N2 preflight pilot third; planned design and implementation-plan review gates retained.
- 2026-10-02T08:09:48Z (feat/acceptance-filter): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T08:09:48Z (feat/acceptance-filter): claimed by codex, harness thread owns claim; workspace .worktrees/acceptance-filter, branch feat/acceptance-filter
- 2026-10-02T08:10:20Z (feat/acceptance-filter): claimed by codex, pid 3565319; investigating gather, world capture, retraction folds and closure identity before drafting spec
- 2026-10-02T08:15:55Z (feat/acceptance-filter): Baseline: just setup passed; just test-one tests/test_evaluation.py tests/test_world_view.py tests/test_snapshot_retraction.py passed (119 tests, 38.89 s). Design must filter snapshot chains as well as ordinary retractions, preserve the split-corpus refusal, and keep epoch/capture integrity checks unconditional.
- 2026-10-02T08:15:55Z (feat/acceptance-filter): Design choices: pair counts with an immutable caller policy statement; filter only evidence and correction records, keep dependency reads; capture per-corpus/address exclusions; retain unrestricted call behavior; do not introduce a filtered-view wrapper or a kernel trust registry.
- 2026-10-02T08:20:54Z (feat/acceptance-filter): review: spec round 1 — verdict: revise; findings: P2 2; reviewer: codex (self-review)
- 2026-10-02T08:20:54Z (feat/acceptance-filter): Self-review fixes: define completeness for early absent-input returns; distinguish filtered receipt candidates from snapshot-only current capture records when deciding whether recorded resolutions can be compared unchanged.
- 2026-10-02T08:22:50Z (feat/acceptance-filter): Spec self-review findings resolved inline: early absent-input returns explicitly remain incomplete, and snapshot-only post-epoch exclusions do not disable the receipted correction-resolution check. No product code changed.
- 2026-10-02T08:22:50Z (feat/acceptance-filter): Verification: just test-fast passed (5946 passed, 1 skipped; Python phase 117.45 s; no affected TypeScript tests). Focused baseline: 119 passed. Written design ready for user review; implementation plan follows accepted spec.
- 2026-10-02T08:22:50Z (feat/acceptance-filter): parked (waiting on user, review): User reviews .worktrees/acceptance-filter/docs/superpowers/specs/2026-10-02-belief-acceptance-design.md; after acceptance Codex resumes this worktree and drafts the implementation plan, then requests its review before freeze and implementation.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T09:15:16Z (feat/acceptance-filter): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T09:15:16Z (feat/acceptance-filter): review: spec round 2 — verdict: revise; findings: P1 2, P2 7, P3 4; reviewer: human
- 2026-10-02T09:15:16Z (feat/acceptance-filter): Review scope: verification edge membership for rejected identity twins; exact mapped per-corpus resolver and filtered facets; per-ref receipt fidelity; pre-facet snapshot filtering; supplied-context guard and pure-evaluator refusal; deterministic completion; overlap milestone limit; filtered snapshot history; canonicalization, manifest and encoding errors, exhaustive predicate cost.
- 2026-10-02T09:27:06Z (feat/acceptance-filter): Round 2 disposition: all findings accepted. Spec now separates verification-target edge membership from accepted correction scope; defines mapped-only per-corpus resolvers and surviving inventoried facets; retains receipt checks per unaffected transitive counter set using the existing packaged discovery map; filters snapshot facets before validation; rejects supplied acceptance context; defines refusal order, deterministic empty incomplete reports and late completion; names the singleton/1b contract limit, filtered history and exact preflight errors/cost.
- 2026-10-02T09:29:44Z (feat/acceptance-filter): Revision verification: just test-one tests/test_designs_corpus.py passed (15 tests, 0.82 s); just test-fast passed (5946 passed, 1 skipped; Python phase 84.25 s; no affected TypeScript tests); git diff --check and tasks check clean. These verify the documentation change against the existing implementation; acceptance behavior remains proposed.
- 2026-10-02T09:29:44Z (feat/acceptance-filter): parked (waiting on user, review): User re-reviews revised .worktrees/acceptance-filter/docs/superpowers/specs/2026-10-02-belief-acceptance-design.md against round 2 findings; after acceptance Codex resumes this worktree and writes the implementation plan for its review before freeze or product changes.
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T09:39:48Z (feat/acceptance-filter): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T09:39:48Z (feat/acceptance-filter): attribution correction: spec round 2 reviewer was claude-code/claude-opus-5-5, forwarded by the user; the earlier human attribution was incorrect.
- 2026-10-02T09:39:49Z (feat/acceptance-filter): review: spec round 3 — verdict: accept; findings: P3 3; reviewer: claude-code/claude-opus-5-5
- 2026-10-02T09:41:12Z (feat/acceptance-filter): claimed by codex/gpt-6, planning in existing acceptance-filter worktree; spec accepted at dc41764. Plan includes refusal parity and representative early/late caught errors; product implementation remains behind plan review.
- 2026-10-02T09:57:04Z (feat/acceptance-filter): Plan drafted: 8 tasks, 34 arms/units across G10–G13, 8 durable checks. Accept-all refusal parity and representative early/late caught errors are explicit; M1/C3-b live retargets preserve frozen declarations. Inline coverage/type/count audit passed. Verification: 23 focused document checks passed; just test-fast 5946 passed, 1 skipped in 85.28s; no affected TypeScript tests; tasks check clean.
- 2026-10-02T09:57:04Z (feat/acceptance-filter): parked (waiting on user, review): User reviews .worktrees/acceptance-filter/docs/superpowers/plans/2026-10-02-belief-acceptance.md; after acceptance Codex freezes cut 45 and executes the plan natively
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T10:05:52Z (feat/acceptance-filter): resumed
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T10:05:52Z (feat/acceptance-filter): review: plan round 1 — verdict: revise; findings: P2 2, P3 5; reviewer: claude-code/claude-opus-5-5
- 2026-10-02T10:07:00Z (feat/acceptance-filter): Ruling: plan round 1 corrections are adopted and execution approved under the user instruction to freeze/start without another review round. G13-e uses reachable supplied lineage not_present; wrapper state precedes binding guard. P3 corrections: explicit acceptance collection only, real cut headings, reliable live-id/alias drift fixture, canonical cwd. Product code still untouched before freeze.
- 2026-10-02T10:12:18Z (feat/acceptance-filter): claimed by codex/gpt-6, pid 3565319; executing corrected plan natively. Freeze scan shows no competing cut 45; roadmap inventory 220/251 with G10–G13 banked open.
