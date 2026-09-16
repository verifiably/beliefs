---
id: beliefs-0c1cc9
title: No committed check reads the reproduction's cut-31-corpus transition measurement
status: idea
priority: 2
created: 2026-09-16T20:09:21Z
updated: 2026-09-16T20:09:21Z
depends: []
tags: [conformance, reproduction]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

The mm30 reproduction record's §11.5 measurement — the cut-31 corpus state audited read-only under the successor profile, returning exactly 'profile-mismatch: base' and reading no record — was taken by a one-shot script that is not in the tree, and its result is saved as state.cut31_corpus_state in the recreated corpus. Nothing committed reads that key: the driver has no step for it and no acceptance arm asserts it, so decision 11's transition arm is a recorded measurement with no way to re-run it. Give the driver a step (as rederive.prior_state already is for the cut-22 state) or an acceptance arm that reads the key, so the next recreation measures the transition rather than restating it.
