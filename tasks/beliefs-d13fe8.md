---
id: beliefs-d13fe8
title: Deliver URL acquisition and act-report coverage
status: todo
priority: 2
size: l
complexity: high
created: 2026-08-31T00:38:27Z
updated: 2026-09-12T16:26:55Z
depends: []
tags: [migration, acquisition, act-report]
---

Outcome: Beliefs acquires datasets through canonical URL locators under the banked network discipline and closes the act-report remainder with the new acquisition operation surface.

Acceptance evidence: Design and freeze the acquisition cut; implement canonicalization, network and redirect policy, provenance, refusal reporting, and same-root behavior; cover H4, G9, R10, T5, T7's same-root case and T1/T2/T4 with deterministic tests; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `url-retrieval` and `act-report-remainder`; `docs/designs/2026-08-10-verified-holdings-record-design.md`; and `docs/designs/2026-08-11-act-report-design.md`.

Uncertainty: Canonicalization and network discipline are banked, but the concrete retrieval cut and supported transport behavior are not planned.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Holdings sections 2-3 bank URL canonicalization and network discipline, and act-report section 4 fixes same-root provenance/report publication. The concrete acquisition cut must still compose redirect/address validation, bounded retrieval, refusals and atomic publication; no transport implementation plan settles those interactions.
