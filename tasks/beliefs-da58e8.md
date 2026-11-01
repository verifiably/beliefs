---
id: beliefs-da58e8
title: Certified directory helper and module-scoped session-door fixtures
status: done
priority: 0
size: m
complexity: mid
process: direct
owner: perf/0f5112-test-latency
created: 2026-11-01T13:22:07Z
updated: 2026-11-01T16:02:14Z
started: 2026-11-01T15:55:42Z
completed: 2026-11-01T16:02:14Z
closed: 2026-11-01T16:02:14Z
depends: [beliefs-ef55af]
parent: beliefs-0f5112
tags: []
model: claude-opus-5-5
origin: agent
plan: docs/superpowers/plans/2026-11-01-test-fast-latency.md
step: "Task 2: Certified directory helper and module-scoped session-door fixtures"
---

## Notes

- 2026-11-01T13:22:07Z (add): created
  provenance: {"origin":"agent"}
- 2026-11-01T15:55:42Z (perf/0f5112-test-latency): started
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T16:02:14Z (perf/0f5112-test-latency): done
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T16:02:14Z (perf/0f5112-test-latency): Task 2 landed at 7c48364: certified_work_dir() try/finally helper with certified_work, certified_module_work, certified_work_factory fixtures; module-scoped exported_publication in test_session_sharing_doors.py (25 functions/38 items copy only the metadata-less export); readonly_source + scoped_source for the 8 non-mutating publish-door items. RED->GREEN on both new tests. Focused: 67 passed (sharing+publish+fixture_grouping); acceptance callers 24 passed; sharing doors alone 41 passed in 13.18 s (was 175 s worker time); VERIFIABLY_UNCERTIFIED_HOST=1 on tmpfs: 6 passed, 60 skipped, all certified-tuple reasons, rmdir of base clean; check-hygiene exit 0.
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
