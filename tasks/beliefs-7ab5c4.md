---
id: beliefs-7ab5c4
title: "test_n2.py's _LIVE_SABOTAGES keys by arm.row, which is not unique across the unioned arm tuples"
status: idea
priority: 2
created: 2026-09-16T20:09:36Z
updated: 2026-09-16T20:09:36Z
depends: []
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

python/tests/test_n2.py builds its live re-target table as a dict keyed by arm.row over the union of several cuts' arm tuples. Row labels are unique within a cut's declaration, not across cuts, so two arms from different cuts sharing a label collapse silently: the second overwrites the first and the lost arm is simply never re-targeted, with no failure anywhere. A one-line assert that len(_LIVE_SABOTAGES) equals the number of entries built would catch it. The same shape is mirrored in the acceptance guards' own tables.
