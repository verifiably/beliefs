---
id: beliefs-3ea822
title: Certify publication persistence
status: todo
priority: 3
size: l
complexity: high
created: 2026-08-31T00:38:28Z
updated: 2026-09-12T16:26:55Z
depends: [atoms-f5779f]
tags: [migration, cross-repo, durability]
---

Outcome: Beliefs closes X2 with persistence-cut certification that exercises its real publication path through the Atoms durability boundary.

Acceptance evidence: Consume the Atoms harness delivered by `atoms-f5779f`; extend the Beliefs-side composition test across each X2 stage without a duplicate transaction authority; record reproducible zero-violation evidence or fail closed; discharge X2; update current status; and pass both affected repositories' complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `persistence-cut`; cut 7's X2 accounting; and Atoms task `atoms-f5779f`.

Uncertainty: The current publication path exists, but its cross-repository persistence-cut harness and certified hardware scope do not.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Cut 7 explicitly leaves X2 power-fail evidence open and atoms-f5779f still has no cross-repository harness design or certified hardware scope. Composing consumer publication stages with the sole Atoms recovery authority requires substantial design and certification judgment.
