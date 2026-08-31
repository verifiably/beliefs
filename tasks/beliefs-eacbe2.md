---
id: beliefs-eacbe2
title: Deliver the first full contract cut
status: todo
priority: 2
size: xl
created: 2026-08-31T00:38:28Z
updated: 2026-08-31T23:36:24Z
depends: [beliefs-73be28, beliefs-d13fe8, beliefs-b34652, beliefs-bc3aff, beliefs-aa27da, beliefs-a7df71, beliefs-3ea822, nodes-ce28b8]
tags: [migration, contract, conformance]
---

Outcome: Beliefs freezes and implements the first full successor contract after every oracle-amending lane, including certification cadence, conformance-package split, rules-store resolution, and legacy-check disposition.

Acceptance evidence: Wait for the execution (`beliefs-73be28`), acquisition (`beliefs-d13fe8`), mutation (`beliefs-aa27da`), world-read (`beliefs-b34652`), domain (`beliefs-bc3aff`), L13 (`beliefs-a7df71`), and persistence (`beliefs-3ea822`) endpoints, plus the resolved Nodes producer `nodes-ce28b8` (`nodes-remainder`); design the successor identities and governance decisions; freeze before implementation; discharge N1–N10, P1 and the assigned certification/resolver/rules-store arms; update the authority artifacts and roadmap; and pass all Python, TypeScript, corpus, and parity gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `contract-cut` and join rule; `docs/designs/2026-08-03-normative-contract-design.md`; and `docs/guide/open-questions.md` Contracts and adoption.

Uncertainty: The roadmap fixes the join point, but successor identities, certification cadence, normative artifact shape, and legacy-check ruling need their design cycle. The Nodes producer `nodes-ce28b8` is resolved but unfinished and remains a blocker.
