---
id: beliefs-942b40
title: Re-pin cuts 7-13 to the rewritten cut-3 and cut-5 arms
status: done
priority: 1
size: s
created: 2026-09-07T09:29:37Z
updated: 2026-09-08T02:33:14Z
depends: []
tags: [conformance, write-path]
---

The verification-publication slice moved lines that cut 3's and cut 5's N2 arms pin verbatim, so those arms were rewritten against the landed source (fix the arm, never the source). Cuts 14-19 were re-pinned to 1e92471 and are green (965fe7f). Cuts 7-13 still pin python/tests/n2_arms_cut5.py at 4a7dc19dd08d and fail their FROZEN_PRIOR_CUT_FILES test today.

Cuts 7, 9, 11, 12, 13: one line each. Cuts 7-9 reach the pin through CUT6_SOURCE_COMMIT rather than an inline entry.

Cut 8 needs two lines: it also pins python/tests/acceptance/test_n2_cut6.py at RENAME_COMMIT = 5a02ca2 (test_n2_cut8.py:104,113), and that entry already failed at 74a5938 — older debt with its own cause, not from this slice.

Cut 10 is STRUCTURALLY BLOCKED and needs a ruling before it can be touched: test_n2_cut17.py:48-53's FROZEN_CUT10_SHA256 pins python/tests/acceptance/test_n2_cut10.py by content, so amending cut 10's own pin table breaks cut 17's cited-surface guarantee. The general question is worth answering once: an older cut's module being content-pinned by a newer cut means it can never be amended, and this will recur every time an arm file moves.

Cut 21's runner chain cannot go green until this is resolved. Precedent for the mechanical part is 74a5938. Reasoning in docs/plans/2026-09-06-verification-publication-execution.md (Ruling P9).

## Notes

- 2026-09-07T17:56:02Z (main): Facet-contract integration d5e203c and its local main landing include the live cut 7/9/11/12/13 guard migration; the actual cut20 aggregate now passes on main. Historical cut 8/10 are outside that live prefix and were not executed here; verify their remaining scope before changing frozen pins. This note does not close the historical remainder.
- 2026-09-08T02:33:14Z (feat/verification-publication): Resolved by the freeze doctrine (docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md, commit 8b7fbc3). Cuts 7, 9, 11, 12, 13 were live and were re-pinned in the facet-contracts landing. Cuts 8 and 10 are cited-not-run: their pin tables are historical statements, never repaired, so cut 10's collision with cut 17's FROZEN_CUT10_SHA256 dissolves rather than needing a ruling to break it. The three falsified pins are recorded in python/tests/cited_not_run.py. Cut 21's chain was never blocked by this - it roots at cut 17, whose inventory holds neither guard.
