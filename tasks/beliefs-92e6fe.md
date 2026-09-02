---
id: beliefs-92e6fe
title: Add a measured opt-in fast Python test loop
status: todo
priority: 2
size: s
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T03:41:06Z
depends: []
tags: [performance, testing, tooling]
---

Why: the exhaustive Python gate takes roughly 15:49-20:31 while collection takes about 1.23s. Developers already have native node, -k, --lf, and --ff selection but no documented project fast loop.

Change: document a zero-dependency focused workflow first. On a multicore host, benchmark pytest-xdist without weakening the default gate. Separately trial coverage-based changed-test selection for local use only and keep it only if recall checks and median savings justify the dependency.

Done when: one documented opt-in command provides a materially faster local loop; full pytest remains the required CI/conformance gate; benchmark method and limitations are recorded; no probabilistic omission is used for required verification.
