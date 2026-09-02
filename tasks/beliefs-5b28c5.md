---
id: beliefs-5b28c5
title: Reuse captured closure in tests that do not exercise capture
status: todo
priority: 1
size: m
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T03:41:06Z
depends: []
tags: [performance, testing, confinement]
---

Why: many 7-24s tests repeatedly execute assessment, production, or replay; each boundary run recaptures the Python/runtime closure even when the assertion is unrelated to capture.

Change: add the smallest test fixture/seam that captures one immutable closure and reuses it only in tests whose subject is downstream run behavior. Leave closure, freshness, and production-capture tests on the real path.

Done when: identify and document the real-capture test set; preserve those tests unchanged in meaning; record three before/after timings for the affected modules and the full suite; run the Python repository gates.
