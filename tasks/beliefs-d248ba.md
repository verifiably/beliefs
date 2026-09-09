---
id: beliefs-d248ba
title: Deliver world resolution and packaging remainder
status: doing
priority: 2
size: xl
owner: design/world-resolution
created: 2026-08-31T00:38:27Z
updated: 2026-09-09T11:59:42Z
depends: []
tags: [migration, world-read, resolution]
spec: docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md
plan: docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md
---

Outcome: Beliefs resolves the world read side across corpora, including views, coreference, snapshot clauses, and the packaging/import/audit ride-along.

Acceptance evidence: Freeze a world-read cut; implement resolution states and cross-corpus queries against the landed write boundary and index; exercise omission, divergence, coverage, snapshot, packaging, and audit negatives; discharge every roadmap row assigned to `world-resolution` and `packaging-remainder`; update current status; and pass all gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `world-resolution` and `packaging-remainder`; `docs/designs/2026-08-02-world-addressing-design.md`; `docs/designs/2026-08-08-world-address-ruling.md`; and `docs/designs/2026-08-03-world-index-packaging-design.md`.

Uncertainty: The required write and index prerequisites have landed, but the resolver cut and its public query shape are not yet planned.

## Notes

- 2026-09-09T09:53:03Z (design/world-resolution): Slice split agreed 2026-09-09: 1 world read view + cross-corpus traversal (this spec), 2 coreference-attestation kind, 3 snapshot import/audit/diagnostic callers + relabels, 4 view evaluation. Approach A: a sealed sibling WorldReadView beside ReadView, bound to an explicit epoch, consumers widened to the union. Review tightened four points: published producers consulted for absent carriers; absence carries corpus_id into LineageSnapshot.not_present and its projection; not_present is a third digested availability state in build_snapshot with overlap refused; evaluation seam names gather, run_value, facet-read routing and check_verification, broader audit to slice 3.
- 2026-09-09T11:18:48Z (design/world-resolution): Plan reviewed 2026-09-09 (eight findings, resolved): W8b measured broken at build and dropped from cut 23's selection (7 closed of 8 read; the view refuses uid ambiguity at open); absent roots checked before the walk; evaluation absence covers assessment runs, every input role and the lineage snapshot; derived attribution reaches evaluate; dataclass default via default_factory; four N2 arms retargeted; three fixtures corrected; discharge through just check/test.
- 2026-09-09T11:59:42Z (design/world-resolution): took over session 88aa735c-590d-4eda-8d25-0fcf60bef434 (owner design/world-resolution, host titan, pid 1720691, worktree /mnt/ssd/Dropbox/beliefs/.worktrees/world-resolution, since 2026-09-09T09:17:51Z, age 9711s, stale: pid 1720691 is gone)
- 2026-09-09T11:59:42Z (design/world-resolution): User authorized takeover from closed Claude session; claimed by Codex /root, pid 2130612; executing slice 1 with per-task implementation and review.
