---
id: beliefs-7ab5c4
title: Guard portable N2 overrides against missing or ambiguous arm targets
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-16T20:09:36Z
updated: 2026-09-29T22:34:00Z
depends: []
parent: beliefs-287026
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

Why: portable N2 overrides currently select arms by row alone. At main 7fd039f, _LIVE_SABOTAGES is a literal with one P9 entry, not a dict comprehension over the union. P9 occurs once in the portable declarations today; repeated rows elsewhere are intentional, including within a cut. The risk is a future override silently applying to several arms or to none.

Done:
- Before applying the portable override table, require each override row to select exactly one declared portable arm; fail with the row and match count for zero or multiple targets.
- Preserve the complete arm tuple, including legitimate repeated rows without overrides. Do not assert global row uniqueness or compare table size with all arms.
- Add a small regression covering a missing target, duplicate target, and unchanged non-target arms; retain today's P9 behavior.
- Inspect analogous live-guard tables for the same ambiguity; record findings, preserving intentional per-row multi-arm overrides and all frozen declarations.
- Verify through just test-one with the focused selector, test_arm_staleness.py and test_frozen_guards.py, then just test-fast. Run the affected portable N2 check through just test-one tests/test_n2.py with a focused selector because test-fast omits that module.

Where to look: python/tests/test_n2.py (_LIVE_SABOTAGES and PORTABLE_ARMS), python/tests/n2_arms.py, n2_arms_cut2.py, n2_arms_cut3.py, n2_arms_cut26.py; docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md. The override was introduced at 6b392e8.

Original capture (retained; the current-code correction above supersedes its proposed count assertion):
python/tests/test_n2.py builds its live re-target table as a dict keyed by arm.row over the union of several cuts' arm tuples. Row labels are unique within a cut's declaration, not across cuts, so two arms from different cuts sharing a label collapse silently: the second overwrites the first and the lost arm is simply never re-targeted, with no failure anywhere. A one-line assert that len(_LIVE_SABOTAGES) equals the number of entries built would catch it. The same shape is mirrored in the acceptance guards' own tables.

## Notes

- 2026-09-29T22:34:00Z (main): scope: scoped; corrected the dict-collapse premise from current code; todo P3/s/mid/direct for zero-or-multiple portable override targets, preserving legitimate repeated rows and original capture; brief: docs/notes/2026-09-29-testing-backlog-brief.md
