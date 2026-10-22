---
id: beliefs-6fc759
title: Resolve existing tilde-layout findings before checker rollout
status: todo
priority: 2
size: m
complexity: mid
process: direct
created: 2026-10-22T19:06:28Z
updated: 2026-10-22T19:06:28Z
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
