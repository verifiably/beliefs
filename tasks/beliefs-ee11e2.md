---
id: beliefs-ee11e2
title: Eight N2 arms were already stale before the verification-publication slice
status: todo
priority: 2
size: s
created: 2026-09-07T09:30:47Z
updated: 2026-09-07T09:30:47Z
depends: []
tags: [conformance]
---

A scan of every n2_arms_cut{4,5,6,7,16}.py arm touching spec.py/stored.py/corpus.py/audit.py (97 arms) found 8 already stale at 041c7b6, before that slice made any change — rows S7 x2, S8 x2, R19, and T2 x2 plus C2. The T2 and C2 rows live in n2_arms_cut3.py:897,907 and n2_arms_cut5.py:151,161,174,268 and pin lines in boundary.py, root.py and unrelated corpus.py/stored.py logic (operation-port fulfillment, retraction validation).

Independently, three CUT5_ARMS sabotages were confirmed stale at 74a5938, 331c534 and da6bab8 alike: T2 (post-intent refusal), T2 (intent-append failure) and C2 (actor, event attribution).

tests/test_n2.py is green at 38 passed regardless, so whatever audit surfaces these is not the one the portable suite runs — which is itself worth understanding, since it means arm staleness can accumulate invisibly between cut discharges.

A stale arm proves nothing under its sabotage. Fix the arm to match the landed source, never the source.
