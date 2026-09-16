---
id: beliefs-638318
title: Design weighted-belief semantics
status: idea
priority: 4
size: l
created: 2026-08-31T00:38:28Z
updated: 2026-09-12T20:32:08Z
depends: [beliefs-59f846]
tags: [migration, design, belief]
---

Outcome: Beliefs gains an approved successor-policy design for unequal evidence weights grounded in estimand typing rather than unowned constants.

Acceptance evidence: Assign estimand-typing ownership; decide which study-design or precision evidence may affect weights and whether constants are global or domain-scoped; specify identity, receipts, failure behavior, and S6(h); produce an implementation plan only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `weighted-belief`; `docs/designs/2026-08-05-belief-policy-design.md`; and `docs/guide/open-questions.md` Weighted belief.

Uncertainty: Estimand compatibility and an owner are unresolved, so implementation status is not yet justified.

## Notes

- 2026-09-12T20:32:08Z (design/estimand-typing): 2026-09-12: the estimand-typing design (beliefs-59f846) answers the ρO3 estimand half this task is blocked on; once it lands, this task's blocker becomes its own successor-policy design over the commensuration key (design §7.3, §11).
