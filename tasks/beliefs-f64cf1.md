---
id: beliefs-f64cf1
title: "Attribute and reduce N2 audit cost, now the largest share of the full gate and CI"
status: todo
priority: 2
size: m
complexity: mid
process: planned
created: 2026-09-26T19:29:52Z
updated: 2026-09-26T19:29:52Z
depends: []
tags: [testing]
source: beliefs-9b248a
agent: claude-code/claude-opus-5-5
---

Why: after beliefs-9b248a, standalone N2 (tests/test_n2.py, 46 tests) is the largest single cost in both gates. Locally at host-budget 16 it took 193 s pre-memo / 173.88 s post-memo of a ~236 s full gate, using ~2,514 CPU-seconds (2026-09-26 measurement, /usr/bin/time user+sys). In CI at 4 workers (run 36264706736) N2 took 514–538 s of each ~13–14 min Python job, against ~240–253 s for the whole non-N2 phase; it also runs once per matrix Python version. The fast-loop median sits at 87.17 s against its 90 s target, so the full gate is where headroom remains.

Change: first attribute N2's CPU per arm and per check (subprocess start, closure capture, pipeline runs, copy setup) with a pilot on a few arms before any full sweep. Then propose bounded reductions that keep every declared arm audited and every sabotage applied to its own copy. Separately evaluate a CI-only restructuring (N2 as its own job running concurrently with the non-N2 phase, or on one Python version) — that is layout, not a cost reduction, and must not weaken the certified local gate.

Done when: N2's cost is attributed, retained reductions are measured end to end on the certified host, and the full gate and CI timings are recorded; no arm, check or capability-dependent result is dropped.
