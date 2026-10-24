---
id: beliefs-eacbe2
title: Deliver the first full contract cut
status: todo
priority: 2
size: xl
complexity: high
process: planned
created: 2026-08-31T00:38:28Z
updated: 2026-10-24T11:05:57Z
depends: [beliefs-73be28, beliefs-d13fe8, beliefs-b34652, beliefs-bc3aff, beliefs-aa27da, beliefs-a7df71, beliefs-3ea822, nodes-ce28b8, beliefs-928881, beliefs-1a5157, beliefs-59f846, beliefs-4bcf88]
parent: beliefs-199aeb
tags: [migration, contract, conformance]
---

Outcome: Beliefs freezes and implements the first full successor contract after every oracle-amending lane, including certification cadence, conformance-package split, rules-store resolution, and legacy-check disposition.

Acceptance evidence: At inspected main a7ce8ff on 2026-10-24, eleven of twelve recorded endpoints are done: execution (beliefs-73be28), acquisition (beliefs-d13fe8), world-read (beliefs-b34652), domain (beliefs-bc3aff), mutation (beliefs-aa27da), L13 (beliefs-a7df71), Nodes 2.0 (nodes-ce28b8), D1 (beliefs-928881), publish (beliefs-1a5157), estimand typing (beliefs-59f846), and composite claims (beliefs-4bcf88). Only persistence (beliefs-3ea822, itself waiting on atoms-f5779f) remains open in that recorded set. Preserve these edges as provenance, not eleven unfinished blockers.

First refresh the join against current code, the adoption ledger, the roadmap's off-path/concurrency rules and any later oracle-amending work; [ref:brief] identifies why the old dependency list alone cannot authorize a freeze. The session envelope and empirical-boundary work are examples to inspect, not newly adjudicated prerequisites in this pass. Once the operation set settles and prerequisites are satisfied, review the successor-contract design and implementation plan; freeze before implementation; discharge N1–N10, P1, R22's resolver arm, R23's rules-store clauses, W8a's instrument-certification arm, X12 and C10's certification arms; update the authority artifacts and roadmap; and pass all Python, TypeScript, corpus, and parity gates. Preserve frozen conformance evidence and include the repository's capability/permit and recent-cut acceptance obligations in the plan.

Sources: docs/plans/2026-08-29-implementation-roadmap.md contract-cut and join rule; docs/designs/2026-08-03-redesign-adoption-ledger.md remaining-boundary table; docs/designs/2026-08-03-normative-contract-design.md; docs/guide/open-questions.md Contracts and adoption; and [ref:brief] for this prerequisite refresh.

Uncertainty: The roadmap fixes the join point, not successor identities, certification cadence, normative artifact shape, rules-store/resolver realization or legacy-check disposition. Those still need the design cycle. The old body described the estimand grammar (cut 31) as the base contract's one post-freeze amendment; composite grammar, the composite kind, composes and supersedes same_kind followed at cut 32, and subsequent oracle changes must be inventoried before freezing. Closed historical lane endpoints do not establish that today's operation set has settled.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-conformance-readiness-brief.md — current prerequisites, evidence limits and remaining decisions

## Notes

- 2026-09-10T20:26:52Z (main): Curation restores D1 and publish as blockers: domain slice completion left D1 open, and publish amends the coordination contract, W17 and act-report oracles before the final contract freezes.
- 2026-09-12T16:26:55Z (main): Complexity high: The roadmap fixes the join point, not successor contract identities, certification cadence, normative package shape or legacy-check disposition. Those architecture/governance decisions remain after the oracle-amending lanes; Nodes 2.0 landing alone does not settle them.
- 2026-09-16T10:02:59Z (main): 2026-09-16 doc review: body no longer calls nodes-ce28b8 an unfinished blocker — it closed 2026-09-12 (nodes b0c37b8) and the ledger already says the join no longer waits on nodes. Six open endpoints remain: d13fe8, aa27da, b34652, a7df71, 3ea822, 1a5157.
- 2026-10-24T11:05:57Z (main): scope: rescoped; at main a7ce8ff, eleven recorded endpoint dependencies are done and only persistence remains open; retained P2/xl/high, chose planned, and required a fresh join/oracle inventory before successor design and freeze; brief: docs/notes/2026-10-24-conformance-readiness-brief.md
