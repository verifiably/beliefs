---
id: beliefs-638318
title: Design weighted-belief semantics
status: idea
priority: 4
size: l
created: 2026-08-31T00:38:28Z
updated: 2026-09-16T10:02:59Z
depends: [beliefs-59f846]
tags: [migration, design, belief]
---

Outcome: Beliefs gains an approved successor-policy design for unequal evidence weights over the commensuration keys estimand typing supplies.

Acceptance evidence: Decide which study-design or precision evidence may affect weights and whether constants are global or domain-scoped; specify identity, receipts, failure behavior, and S6(h) over `commensurable` and `co_scoped` (estimand-typing design §7.3, §11); produce an implementation plan only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `weighted-belief`; `docs/designs/2026-08-05-belief-policy-design.md`; `docs/designs/2026-09-12-estimand-typing-design.md`; and `docs/guide/open-questions.md` Weighted belief.

Uncertainty: The key domain is supplied — the estimand, applicability, estimate and uncertainty are typed and `commensurable`/`co_scoped` are exposed and total since cut 31 — and `science.belief.v1` reads none of it. What blocks this is its own design: which weights a design key and a precision term license, and where any constants live.

## Notes

- 2026-09-12T20:32:08Z (design/estimand-typing): 2026-09-12: the estimand-typing design (beliefs-59f846) answers the ρO3 estimand half this task is blocked on; once it lands, this task's blocker becomes its own successor-policy design over the commensuration key (design §7.3, §11).
- 2026-09-16T10:02:59Z (main): 2026-09-16 doc review: beliefs-59f846 closed at cut 31, so the dependency is met and the body's 'estimand compatibility and an owner are unresolved' was stale; rewritten to name the successor-policy design as the only blocker, matching the roadmap's tier-3 row and the open-questions entry.
