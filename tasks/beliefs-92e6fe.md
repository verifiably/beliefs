---
id: beliefs-92e6fe
title: Add a measured opt-in fast Python test loop
status: done
priority: 2
size: s
owner: perf/test-optimization
created: 2026-09-02T03:41:06Z
updated: 2026-09-04T12:48:29Z
depends: [beliefs-5b28c5, beliefs-aa2d4f]
tags: [performance, testing, tooling]
---

Why: after the duplicate capture and N2 worker fixes, developers still need an explicit fast local loop while the exhaustive gate remains authoritative.

Change: first document the zero-dependency deterministic loop, including --ignore=tests/test_n2.py for ordinary code iteration because N2 audits contract content, plus pytest node ids, -k, --lf, and --ff. Re-benchmark after the two prerequisite fixes. Only then benchmark pytest-xdist on a multicore host, pinning N2 to one worker so its internal 24 subprocess workers are not multiplied. Trial coverage-based changed-test selection only if the native loop remains insufficient.

Done when: one documented opt-in command materially improves local iteration; full pytest remains the required CI/conformance gate; N2 still runs in required verification; no probabilistic omission is used.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Reordered behind the capture and N2 fixes; native deterministic selection is the first implementation.
- 2026-09-04T11:49:47Z (perf/test-optimization): Reusing the completed N2 worker commit; measuring native deterministic selection before deciding whether any dependency earns its cost.
- 2026-09-04T12:28:53Z (perf/test-optimization): Fresh-cache measurements on 16-core/32-thread host: serial full 3216 in 868.15s; serial without N2 3178 in 703.03s; xdist -n8 loadfile full 3216 in 223.34s; xdist without N2 3178 in 164.25s. Pinned pytest-xdist; skipped probabilistic coverage selection.
- 2026-09-04T12:48:29Z (perf/test-optimization): Documented a deterministic 156.10s xdist loop, preserved the serial gate and N2 verification, and pinned pytest-xdist without probabilistic selection.
