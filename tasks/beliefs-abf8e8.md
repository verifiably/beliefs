---
id: beliefs-abf8e8
title: Split contracts/coordination and domains out of beliefs
status: shelved
priority: 2
created: 2026-08-31T10:04:46Z
updated: 2026-10-09T13:57:56Z
depends: []
tags: []
---

Projected, not observed: ledger §5 splits a distribution only on an observed second consumer or a different constraint regime. The coordination contract churns with the user layer while the kernel must not (the agent-surface argument), and domain packs want their own owners and cadence — so these are the expected first split-outs. Prerequisite already banked: sub-project 1 versions the coordination contract independently of the base, so the split stays a move, not a rewrite. Scope this only when a second consumer actually appears.

## Notes

- 2026-10-09T11:37:51Z (main): shelved: Wake when the coordination contract or a domain pack gains an observed second consumer: tasks records realizing coordination task (alternative 3 of the coordination-outside-the-kernel brief), or a domain pack owned outside beliefs (natural-systems' first pack, beliefs-f484a7)
- 2026-10-09T11:37:51Z (main): scope: shelved; ledger §5 and user/autonomy §3.2 split only on an observed second consumer, and none exists: science is the coordination contract's one consumer, domains/ holds biology alone, natural-systems defers its pack route (ns-437ab5); parented under goal beliefs-614364; wake condition recorded by shelve; brief: docs/notes/2026-10-09-coordination-outside-the-kernel-brief.md
- 2026-10-09T13:48:25Z (main): shelved: Wake when another component itself consumes the coordination contract (not through science), or a distinct constraint regime is documented that justifies a separate distribution, such as a domain pack whose owner and release cadence differ from beliefs'. Science delegating its task writes to the tasks CLI is not a second consumer: tasks never reads the contract.
- 2026-10-09T13:48:25Z (main): Wake condition corrected 2026-10-09 after a review of the brief: the earlier wake named tasks realizing coordination task as a second consumer, but tasks never reads the contract, so science stays its one consumer; the wake now needs a component that itself consumes the contract, or a documented constraint regime
- 2026-10-09T13:57:55Z (main): Detached from goal beliefs-614364 when it closed on 2026-10-09 (decided: two systems); stays shelved with its wake condition; brief: docs/notes/2026-10-09-coordination-outside-the-kernel-brief.md
