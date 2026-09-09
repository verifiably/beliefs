---
id: beliefs-ee11e2
title: Eight N2 arms were already stale before the verification-publication slice
status: done
priority: 2
size: s
owner: hygiene/n2-arms
created: 2026-09-07T09:30:47Z
updated: 2026-09-09T09:03:25Z
depends: []
tags: [conformance]
---

A scan of every n2_arms_cut{4,5,6,7,16}.py arm touching spec.py/stored.py/corpus.py/audit.py (97 arms) found 8 already stale at 041c7b6, before that slice made any change — rows S7 x2, S8 x2, R19, and T2 x2 plus C2. The T2 and C2 rows live in n2_arms_cut3.py:897,907 and n2_arms_cut5.py:151,161,174,268 and pin lines in boundary.py, root.py and unrelated corpus.py/stored.py logic (operation-port fulfillment, retraction validation).

Independently, three CUT5_ARMS sabotages were confirmed stale at 74a5938, 331c534 and da6bab8 alike: T2 (post-intent refusal), T2 (intent-append failure) and C2 (actor, event attribution).

tests/test_n2.py is green at 38 passed regardless, so whatever audit surfaces these is not the one the portable suite runs — which is itself worth understanding, since it means arm staleness can accumulate invisibly between cut discharges.

A stale arm proves nothing under its sabotage. Fix the arm to match the landed source, never the source.

## Notes

- 2026-09-09T09:03:25Z (hygiene/n2-arms): Measured 2026-09-09 on 7d06e27: the eight arms (S7 x3, S8 x3, R19 in cut 4; G7 x2, M5, T2 x2, C2 in cut 5) plus four in cut 8 and two in cut 10 all live in cited-not-run declarations, which the frozen-guard doctrine rules evidence, never repaired. Every live guard is already clean: cuts 11, 14, 16, 17 and 18 re-target stale rows in a _LIVE_SABOTAGES table and audit the re-targeted tuple, cut 6 audits its pinned historical tree; 704 arms, zero stale. The audit that surfaces staleness is each guard's own test_no_sabotage_has_gone_stale under tests/acceptance, which addopts ignores - that is why the portable suite could not see it.
- 2026-09-09T09:03:25Z (hygiene/n2-arms): tests/arm_staleness.py + tests/test_arm_staleness.py measure staleness in the portable suite: every arm a live guard audits applies exactly once against the tree it pins, every declared arm the tree has outgrown is a row the guard re-targets, and cited-not-run guards' stale arms are recorded per entry in cited_not_run.py (stale_arms) and held to exactly. Doctrine §7 amended. No arm changed: the tree was already clean under its re-targeting tables.
