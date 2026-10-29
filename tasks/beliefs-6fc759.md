---
id: beliefs-6fc759
title: Resolve existing tilde-layout findings before checker rollout
status: doing
priority: 2
size: m
complexity: mid
process: direct
owner: fix/beliefs-6fc759
created: 2026-10-22T19:06:28Z
updated: 2026-10-29T20:52:31Z
started: 2026-10-29T20:26:25Z
depends: []
tags: []
source: ops-295f8d
agent: codex
---

Why: the final candidate from ops-295f8d reports existing home-relative machine-layout paths that the current checker misses. Resolve these before the stricter vendored copy arrives, so unrelated commits are not blocked. These are scanner findings to classify, not an instruction to discard historical documents.

Done: inspect each listed file in context. Replace accidental checkout/storage paths in shared docs, examples or fixtures with repository-relative paths, project-role references or portable URLs as appropriate. For intentional host configuration, use only the narrow existing layout_allowed mechanism where this repository is host configuration by design; do not exempt ordinary docs wholesale. Preserve historical evidence, attachments and every spec/plan review ledger; follow the task attachment CLI and retention rules instead of editing attached artifacts by hand. If a runtime-path correction needs an unsettled public contract, change that piece to planned before implementation. Run the project-declared checks and the reviewed candidate checker by explicit path, then record every listed file disposition and the clean verdict on this task. Do not repoint shared launchers, vendor the checker, publish, push or activate global guidance in this task.

Where: the current project guide/profile, listed tracked files, existing layout_allowed, and ops-295f8d for candidate branch/path and canonical report. The full sweep reached 36 registered repositories with no unavailable roots; counts here are capped scanner records, not an estimate of all occurrences. No source snippets are copied.

Reported files:
- docs/designs/2026-08-18-composition-root-adapter-design.md: first reported line 19; 2 reported finding(s)
- docs/designs/2026-09-05-mm30-reproduction.md: first reported line 0; 11 reported finding(s)
- docs/plans/2026-09-05-writer-session.md: first reported line 79; 3 reported finding(s)
- docs/plans/2026-09-23-publication-records-execution-ledger.md: first reported line 38; 3 reported finding(s)
- docs/plans/2026-10-01-mount-citations-execution-ledger.md: first reported line 107; 1 reported finding(s)
- docs/superpowers/plans/2026-08-19-family-adapters.md: first reported line 99; 2 reported finding(s)
- docs/superpowers/plans/2026-08-23-root-lifecycle.md: first reported line 23; 3 reported finding(s)
- docs/superpowers/plans/2026-08-28-current-state-documentation-curation.md: first reported line 39; 1 reported finding(s)
- docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md: first reported line 72; 2 reported finding(s)
- docs/superpowers/plans/2026-09-15-world-resolution-slice-6.md: first reported line 56; 4 reported finding(s)
- docs/superpowers/plans/2026-09-16-correction-remainder-slice-1.md: first reported line 61; 3 reported finding(s)
- docs/superpowers/plans/2026-09-19-correction-remainder-slice-2.md: first reported line 58; 3 reported finding(s)
- docs/superpowers/plans/2026-09-20-url-retrieval.md: first reported line 72; 3 reported finding(s)
- docs/superpowers/plans/2026-09-21-event-level-l8.md: first reported line 0; 12 reported finding(s)
- docs/superpowers/plans/2026-09-21-l13-preimage.md: first reported line 0; 11 reported finding(s)
- docs/superpowers/plans/2026-09-22-act-report-remainder.md: first reported line 0; 11 reported finding(s)
- docs/superpowers/plans/2026-09-22-publication-records.md: first reported line 0; 11 reported finding(s)
- docs/superpowers/plans/2026-09-23-publish-act-local.md: first reported line 0; 11 reported finding(s)
- docs/superpowers/plans/2026-09-24-live-query-evaluation.md: first reported line 0; 11 reported finding(s)
- docs/superpowers/plans/2026-09-27-publish-act-remote.md: first reported line 22; 8 reported finding(s)
- docs/superpowers/plans/2026-09-27-session-mounts.md: first reported line 47; 6 reported finding(s)
- docs/superpowers/plans/2026-10-01-mount-citations.md: first reported line 75; 5 reported finding(s)

## Notes

- 2026-10-29T20:26:25Z (main): started
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:26:48Z (fix/beliefs-6fc759): resumed
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:51:50Z (fix/beliefs-6fc759): dispositions: reworded (202 occurrences in 19 files; ~/d/<project> -> <project checkout>, only path text changed; one prose mention -> 'the atoms checkout'): docs/designs/2026-08-18-composition-root-adapter-design.md:19,22; docs/plans/2026-09-05-writer-session.md:79,257,292; docs/superpowers/plans/2026-08-19-family-adapters.md:99,104; docs/superpowers/plans/2026-08-23-root-lifecycle.md:23,93,115; docs/superpowers/plans/2026-08-28-current-state-documentation-curation.md:39; docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md:72-73; docs/superpowers/plans/2026-09-15-world-resolution-slice-6.md:56,1004,1286,1331; docs/superpowers/plans/2026-09-16-correction-remainder-slice-1.md:61,1511,1596; docs/superpowers/plans/2026-09-19-correction-remainder-slice-2.md:58,1486,1563; docs/superpowers/plans/2026-09-20-url-retrieval.md:72,2831,2929; docs/superpowers/plans/2026-09-21-event-level-l8.md (17, global constraints and run/merge commands); docs/superpowers/plans/2026-09-21-l13-preimage.md (25, same pattern); docs/superpowers/plans/2026-09-22-act-report-remainder.md (25); docs/superpowers/plans/2026-09-22-publication-records.md (25); docs/superpowers/plans/2026-09-23-publish-act-local.md (23); docs/superpowers/plans/2026-09-24-live-query-evaluation.md (29); docs/superpowers/plans/2026-09-27-publish-act-remote.md (12); docs/superpowers/plans/2026-09-27-session-mounts.md (9); docs/superpowers/plans/2026-10-01-mount-citations.md (8). allowed (exact-file layout_allowed entries in .ops-check.toml): docs/designs/2026-09-05-mm30-reproduction.md:889-1895 (16 lines) — run record quoting each run's exact MM30_PREDECESSOR, the driver's declared default and the symlinked root spelling that hit ELOOP; docs/plans/2026-09-23-publication-records-execution-ledger.md:38,112 — ledger note and Ruling 10 whose subject is the home-relative spelling causing ELOOP; docs/plans/2026-10-01-mount-citations-execution-ledger.md:107 — deferred minor quoting the MM30 record's home-relative predecessor path.
- 2026-10-29T20:51:52Z (fix/beliefs-6fc759): verification: candidate rc=0 at 973c780 (uncapped scan of the same rule also 0, was 186 line-value findings / 127 capped); just check rc=0; baseline before changes: just test-fast 6353 passed 1 skipped, just test-one tests/test_n2.py 46 passed, ts npm test 155 passed (full just test exceeded the 590 s foreground timeout under host contention, so run in three phases); after changes: just test-fast 6353 passed 1 skipped (N2 reads no changed docs); git diff --check clean; inverse mapping of every changed line reproduces the original exactly.
- 2026-10-29T20:52:07Z (fix/beliefs-6fc759): retained: {"host":"titan","kind":"worktree","path":".worktrees/beliefs-6fc759","state":"kept","verification":"verified","purpose":"branch fix/beliefs-6fc759 at 973c780 (docs commit) awaiting controller review and integration","next_owner":"task:beliefs-6fc759","cleanup_trigger":"fix/beliefs-6fc759 merged into main"}
- 2026-10-29T20:52:10Z (fix/beliefs-6fc759): parked (waiting on agent): controller: review fix/beliefs-6fc759 at 5c06347 in .worktrees/beliefs-6fc759, then integrate
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:52:31Z (fix/beliefs-6fc759): parked (waiting on agent, review): controller: review fix/beliefs-6fc759 at 973c780 in .worktrees/beliefs-6fc759, then integrate
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
