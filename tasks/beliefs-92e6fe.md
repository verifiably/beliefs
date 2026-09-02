---
id: beliefs-92e6fe
title: Add a measured opt-in fast Python test loop
status: todo
priority: 2
size: s
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T10:38:27Z
depends: [beliefs-5b28c5, beliefs-aa2d4f]
tags: [performance, testing, tooling]
---

Why: after the duplicate capture and N2 worker fixes, developers still need an explicit fast local loop while the exhaustive gate remains authoritative.

Change: first document the zero-dependency deterministic loop, including --ignore=tests/test_n2.py for ordinary code iteration because N2 audits contract content, plus pytest node ids, -k, --lf, and --ff. Re-benchmark after the two prerequisite fixes. Only then benchmark pytest-xdist on a multicore host, pinning N2 to one worker so its internal 24 subprocess workers are not multiplied. Trial coverage-based changed-test selection only if the native loop remains insufficient.

Done when: one documented opt-in command materially improves local iteration; full pytest remains the required CI/conformance gate; N2 still runs in required verification; no probabilistic omission is used.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Reordered behind the capture and N2 fixes; native deterministic selection is the first implementation.
