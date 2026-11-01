---
id: beliefs-ef55af
title: "Execution setup, focused baseline, and byte-keyed AST caching"
status: done
priority: 0
size: s
complexity: low
process: direct
owner: perf/0f5112-test-latency
created: 2026-11-01T13:22:04Z
updated: 2026-11-01T15:55:39Z
started: 2026-11-01T15:47:22Z
completed: 2026-11-01T15:55:39Z
closed: 2026-11-01T15:55:39Z
depends: []
parent: beliefs-0f5112
tags: []
model: claude-opus-5-5
origin: agent
plan: docs/superpowers/plans/2026-11-01-test-fast-latency.md
step: "Task 1: Execution setup, focused baseline, and byte-keyed AST caching"
---

## Notes

- 2026-11-01T13:22:04Z (add): created
  provenance: {"origin":"agent"}
- 2026-11-01T15:47:22Z (perf/0f5112-test-latency): started
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T15:55:39Z (perf/0f5112-test-latency): done
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T15:55:39Z (perf/0f5112-test-latency): Task 1 landed at 4f6c6e1: byte-keyed lru_cache(256) _parsed_bytes behind parsed(), hoisted per-module name sets in the two scan tests, spec status updated. RED (NameError) -> GREEN; just test-one tests/test_capability_boundary.py tests/acceptance/test_durable_corpus.py 470 passed in 8.71 s; just check-hygiene exit 0 (pre-existing unlinked_step warnings only). Broad check-code skipped by policy at commit; forced check-code runs in Task 3 Step 4.
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
