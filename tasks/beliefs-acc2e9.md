---
id: beliefs-acc2e9
title: Deliver coordination and view kinds
status: todo
priority: 2
size: xl
created: 2026-08-31T00:38:28Z
updated: 2026-08-31T00:38:28Z
depends: [beliefs-c88566]
tags: [migration, mutation, coordination]
---

Outcome: Beliefs implements governed view and coordination kinds, opaque project identity, `(project, local id)` addressing, and the revision/tip rules that close W11, W12, and W13's two-project negative.

Acceptance evidence: Begin only after `beliefs-c88566` approves the dedicated design; freeze the resulting mutation-lane cut; compile the independently versioned coordination contract into `ProfileSpec`; implement factories, address and predecessor checks, divergence refusal, and guarantee-row tests; update foundations, the open question, adoption ledger, and roadmap; and pass all gates.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §§4.1–4.2 and §8 item 1; `docs/plans/2026-08-29-implementation-roadmap.md` `coordination-addressing`; and existing task `beliefs-c88566`.

Uncertainty: The approved umbrella design fixes the outcome, but `beliefs-c88566` still owns the dedicated design decisions, including the closed view-query language.
