---
id: beliefs-202076
title: Zero-cache single-walk closure cleanup in adapter.py
status: done
priority: 0
size: m
complexity: mid
process: direct
owner: perf/0f5112-test-latency
created: 2026-11-01T13:22:10Z
updated: 2026-11-01T16:15:52Z
started: 2026-11-01T16:02:17Z
completed: 2026-11-01T16:15:52Z
closed: 2026-11-01T16:15:52Z
depends: [beliefs-da58e8]
parent: beliefs-0f5112
tags: []
model: claude-opus-5-5
origin: agent
plan: docs/superpowers/plans/2026-11-01-test-fast-latency.md
step: "Task 3: Zero-cache single-walk closure cleanup in adapter.py"
---

## Notes

- 2026-11-01T13:22:10Z (add): created
  provenance: {"origin":"agent"}
- 2026-11-01T16:02:17Z (perf/0f5112-test-latency): started
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T16:15:52Z (perf/0f5112-test-latency): done
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T16:15:52Z (perf/0f5112-test-latency): Task 3 landed at 5de55eb (plus 3038992 style fix to Task 2's test for ruff SIM117/format): string-prefix root table, string-keyed parent realpath + single lstat, pruned os.scandir add_tree, low-allocation parent-resolved add_records, per-walk hashed-file ELF header retention; zero cross-walk state. 4 new tests (2 RED->GREEN, 2 pinning baseline behaviour). Focused 575 passed; N2 cut13 16 passed (K7a/b/c live kills); check-hygiene 0; TT_FORCE=1 check-code 0; Python 3.11.15 focused 633 passed; capture_closure parity exact vs 240a989 (sha256 18b10edf..., 8476 rows, 75 loader-map, 27 elves); single walk median 0.623 s vs 1.566 s baseline. Rulings in the plan ledger.
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
