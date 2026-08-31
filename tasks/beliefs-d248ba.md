---
id: beliefs-d248ba
title: Deliver world resolution and packaging remainder
status: todo
priority: 2
size: xl
created: 2026-08-31T00:38:27Z
updated: 2026-08-31T00:38:27Z
depends: []
tags: [migration, world-read, resolution]
---

Outcome: Beliefs resolves the world read side across corpora, including views, coreference, snapshot clauses, and the packaging/import/audit ride-along.

Acceptance evidence: Freeze a world-read cut; implement resolution states and cross-corpus queries against the landed write boundary and index; exercise omission, divergence, coverage, snapshot, packaging, and audit negatives; discharge every roadmap row assigned to `world-resolution` and `packaging-remainder`; update current status; and pass all gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `world-resolution` and `packaging-remainder`; `docs/designs/2026-08-02-world-addressing-design.md`; `docs/designs/2026-08-08-world-address-ruling.md`; and `docs/designs/2026-08-03-world-index-packaging-design.md`.

Uncertainty: The required write and index prerequisites have landed, but the resolver cut and its public query shape are not yet planned.
