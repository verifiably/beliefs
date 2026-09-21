---
id: beliefs-08ff74
title: Scrub machine layout from tracked files and commit ops-check 5
status: done
priority: 2
size: m
complexity: low
process: direct
owner: main
created: 2026-09-21T13:05:41Z
updated: 2026-09-21T21:14:13Z
started: 2026-09-21T21:09:59Z
completed: 2026-09-21T21:14:13Z
depends: []
tags: []
source: ops-0c42b9
model: "claude-opus-5[1m]"
agent: "claude-code/claude-opus-5[1m]"
---

ops-check 5 (ops ops-0c42b9) fails on this machine's layout in any tracked file: the home directory, the hostname, WORK_ROOT, a registered checkout or its parent, the banned tracker host. tools/ops-check is already updated in the working tree but uncommitted, because the pre-commit hook refuses every commit here until these findings are gone. Per file: rewrite the path or hostname neutrally; drop the file when it is captured scratch that does not belong in the repository; or, for evidence that must stay verbatim, list its path prefix under layout_allowed in a root .ops-check.toml. Commit tools/ops-check in the same change.

Findings (52 lines in 25 files):
- docs/designs/2026-09-05-mm30-reproduction.md: the hostname, the parent of a registered checkout
- docs/plans/2026-09-05-writer-session.md: a registered checkout
- docs/plans/2026-09-08-conformance-cut-22-run/check.log: a registered checkout, the home directory
- docs/plans/2026-09-08-conformance-cut-22-run/test.log: a registered checkout, the home directory
- docs/plans/2026-09-08-mm30-reproduction-slice2-run/state.json: a registered checkout, the parent of a registered checkout
- docs/plans/2026-09-09-conformance-cut-23-run/main-gate.log: a registered checkout
- docs/plans/2026-09-09-conformance-cut-23-run/test-first-failed.log: a registered checkout
- docs/plans/2026-09-09-conformance-cut-23-run/test.log: a registered checkout
- docs/plans/2026-09-10-conformance-cut-24-run/capture-lift-cleanup-warning.log: a registered checkout
- docs/plans/2026-09-10-conformance-cut-24-run/main-gate.log: a registered checkout
- docs/plans/2026-09-10-conformance-cut-24-run/test.log: a registered checkout
- docs/plans/2026-09-10-mm30-reproduction-rebuild-run/state.json: a registered checkout, the parent of a registered checkout
- docs/plans/2026-09-10-mm30-reproduction-rebuild-run/target.yaml: the parent of a registered checkout
- docs/plans/2026-09-13-conformance-cut-27-run/main-gate.log: a registered checkout
- docs/plans/2026-09-13-conformance-cut-27-run/test.log: a registered checkout
- docs/plans/2026-09-14-conformance-cut-28-run/main-gate.log: a registered checkout
- docs/plans/2026-09-15-conformance-cut-31-run/test.log: WORK_ROOT
- docs/superpowers/plans/2026-08-28-current-state-documentation-curation.md: a registered checkout
- docs/superpowers/plans/2026-09-05-facet-contracts.md: the home directory, the parent of a registered checkout
- docs/superpowers/plans/2026-09-06-verification-publication.md: the home directory, the parent of a registered checkout
- docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md: a registered checkout
- docs/superpowers/plans/2026-09-15-world-resolution-slice-6.md: a registered checkout
- docs/superpowers/plans/2026-09-16-correction-remainder-slice-1.md: WORK_ROOT, a registered checkout
- docs/superpowers/plans/2026-09-19-correction-remainder-slice-2.md: a registered checkout
- docs/superpowers/plans/2026-09-20-url-retrieval.md: a registered checkout

## Notes

- 2026-09-21T16:28:14Z (main): cut 36's merge (eebf6d0) adds files the version-5 rule flags beyond the 13:05 findings list: docs/superpowers/plans/2026-09-21-event-level-l8.md, docs/plans/2026-09-21-event-level-l8-execution-ledger.md, docs/designs/2026-09-05-mm30-reproduction.md §15 (the §13/§14 predecessor path), docs/plans/2026-09-21-conformance-cut-36-results.md; rerun the check for the current list.
- 2026-09-21T21:09:59Z (main): started
  provenance: {"harness_session":"claude-code:6819244b-2358-447b-8b92-1c2457c77557","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-21T21:14:13Z (main): done
  provenance: {"harness_session":"claude-code:6819244b-2358-447b-8b92-1c2457c77557","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-21T21:14:13Z (main): ops-check 5 committed; eight run-capture directories allowed via root .ops-check.toml (evidence linked from results docs), eleven design/plan docs rewritten to ~/d/ and $WORK_ROOT forms, the hostname in the mm30 design neutralized
  provenance: {"harness_session":"claude-code:6819244b-2358-447b-8b92-1c2457c77557","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
