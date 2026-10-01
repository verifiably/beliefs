---
id: beliefs-fdc40f
title: "Acceptance runner chain nests prefix runs: path depth grows one run dir per cut and hits SQLite's 512-char path limit"
status: todo
priority: 1
size: s
complexity: mid
process: direct
created: 2026-10-01T15:11:16Z
updated: 2026-10-01T15:11:22Z
depends: []
tags: [conformance, testing]
agent: claude-code/claude-opus-5-5
---

tools/acceptance_runner.py passes each prefix runner SCIENCE_CUT{cut-1}_ROOT=<this run dir>, so cut N's chain nests N-4 run-XXXXXXXX dirs. Cut 44's chain puts cut 17's test_permit_entry_points needs_volume cases ~405 chars deep and atoms' SQLite-WAL certification refuses (CapabilityUnavailable: parent connection failed / unable to open database file). Reproduced: 27 levels under a canonical base fails, 20 passes. Cut 43 passed one level shallower. Workaround used for cut 44: SCIENCE_CUT44_ROOT=<main>/.work/c44 (13 chars shorter = cut 43's depth). Fix: give prefix runners a sibling run under the top work dir (constant depth), or a short per-chain base; every later cut depends on it.
