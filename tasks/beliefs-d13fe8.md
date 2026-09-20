---
id: beliefs-d13fe8
title: Deliver URL acquisition and act-report coverage
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-08-31T00:38:27Z
updated: 2026-09-20T01:29:35Z
depends: []
tags: [migration, acquisition, act-report]
---

Outcome: Beliefs acquires datasets through canonical URL locators under the banked network discipline and closes the act-report remainder with the new acquisition operation surface.

Acceptance evidence: Design and freeze the acquisition cut; implement canonicalization, network and redirect policy, provenance, refusal reporting, and same-root behavior; cover H4, G9, R10, T5, T7's same-root case and T1/T2/T4 with deterministic tests; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `url-retrieval` and `act-report-remainder`; `docs/designs/2026-08-10-verified-holdings-record-design.md`; and `docs/designs/2026-08-11-act-report-design.md`.

Uncertainty: Canonicalization and network discipline are banked, but the concrete retrieval cut and supported transport behavior are not planned.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Holdings sections 2-3 bank URL canonicalization and network discipline, and act-report section 4 fixes same-root provenance/report publication. The concrete acquisition cut must still compose redirect/address validation, bounded retrieval, refusals and atomic publication; no transport implementation plan settles those interactions.
- 2026-09-15T16:26:47Z (main): 2026-09-15: natural-systems v2 is a real consumer once its Dryad pilot sample is drawn (ns-006fda; framing §4: the survey corpus is random acquisition from repositories). A second corpus is the measurement the roadmap says may re-rank tier 1; until the pilot runs, url-retrieval stays off-path row 2 in breadth order.
- 2026-09-20T01:29:35Z (main): 2026-09-19: process planned — holdings §2–§3 bank canonicalization and network discipline but no transport plan settles how redirect/address validation, bounded retrieval, refusals and atomic publication compose; the lane opens as off-path row 1 after cut 34 (rule 6: no on-path lane, none open), carrying act-report-remainder (T1, T2, T4) as the ride-along; slice design → freeze cut 35 → plan → implement, in .worktrees/url-retrieval
