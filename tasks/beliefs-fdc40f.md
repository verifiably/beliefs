---
id: beliefs-fdc40f
title: "Acceptance runner chain nests prefix runs: path depth grows one run dir per cut and hits SQLite's 512-char path limit"
status: done
priority: 1
size: s
complexity: mid
process: direct
owner: fix/fdc40f-chain-depth
created: 2026-10-01T15:11:16Z
updated: 2026-10-01T21:31:29Z
started: 2026-10-01T21:18:00Z
completed: 2026-10-01T21:31:29Z
depends: []
tags: [conformance, testing]
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

tools/acceptance_runner.py passes each prefix runner SCIENCE_CUT{cut-1}_ROOT=<this run dir>, so cut N's chain nests N-4 run-XXXXXXXX dirs. Cut 44's chain puts cut 17's test_permit_entry_points needs_volume cases ~405 chars deep and atoms' SQLite-WAL certification refuses (CapabilityUnavailable: parent connection failed / unable to open database file). Reproduced: 27 levels under a canonical base fails, 20 passes. Cut 43 passed one level shallower. Workaround used for cut 44: SCIENCE_CUT44_ROOT=<main>/.work/c44 (13 chars shorter = cut 43's depth). Fix: give prefix runners a sibling run under the top work dir (constant depth), or a short per-chain base; every later cut depends on it.

## Notes

- 2026-10-01T21:18:00Z (fix/fdc40f-chain-depth): started
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T21:18:00Z (fix/fdc40f-chain-depth): claimed by claude-code subagent, pid 3801267
- 2026-10-01T21:28:39Z (fix/fdc40f-chain-depth): design: constant depth — acceptance_runner passes each prefix runner SCIENCE_CUT{cut-1}_ROOT=<its own work dir>, so every acceptance_runner-based run (cuts 23-44+) is a sibling run-XXXXXXXX under the top work dir. No consumer reads the nesting: each runner reads only its own *_ROOT, probes and removes its own run. Rejected per-chain short base: still nests, only delays the limit. Frozen runners 17-22 still nest, but their depth is fixed (6 levels to cut 17), not growing with later cuts.
- 2026-10-01T21:31:29Z (fix/fdc40f-chain-depth): done
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T21:31:29Z (fix/fdc40f-chain-depth): acceptance_runner hands each prefix runner its work dir, so chained runs are siblings at constant depth; cut 17's permit entry points pass at the new 6-level depth
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
