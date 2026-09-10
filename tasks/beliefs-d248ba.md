---
id: beliefs-d248ba
title: Deliver world resolution and packaging remainder
status: todo
priority: 2
size: xl
owner: design/world-resolution
created: 2026-08-31T00:38:27Z
updated: 2026-09-10T20:26:52Z
depends: []
tags: [migration, world-read, resolution]
spec: docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md
plan: docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md
---

Outcome: Beliefs resolves the world read side across corpora, including views, coreference, snapshot clauses, and the packaging/import/audit ride-along.

Acceptance evidence: Freeze a world-read cut; implement resolution states and cross-corpus queries against the landed write boundary and index; exercise omission, divergence, coverage, snapshot, packaging, and audit negatives; discharge every roadmap row assigned to `world-resolution` and `packaging-remainder`; update current status; and pass all gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `world-resolution` and `packaging-remainder`; `docs/designs/2026-08-02-world-addressing-design.md`; `docs/designs/2026-08-08-world-address-ruling.md`; and `docs/designs/2026-08-03-world-index-packaging-design.md`.

Remaining work: Slices 1 and 2 are discharged at cuts 23 and 24, merged through 7d69341. The remaining serial chain is beliefs-b7994b (slice 2b, normalized source addressing), beliefs-46847c (slice 3, snapshots/import/audit and packaging), then beliefs-0e523a (slice 4, view evaluation). W8b's measured build defect is repaired by beliefs-fda0e5; selecting and discharging W8b remains open. The parent outcome is not complete.

## Notes

- 2026-09-09T09:53:03Z (design/world-resolution): Slice split agreed 2026-09-09: 1 world read view + cross-corpus traversal (this spec), 2 coreference-attestation kind, 3 snapshot import/audit/diagnostic callers + relabels, 4 view evaluation. Approach A: a sealed sibling WorldReadView beside ReadView, bound to an explicit epoch, consumers widened to the union. Review tightened four points: published producers consulted for absent carriers; absence carries corpus_id into LineageSnapshot.not_present and its projection; not_present is a third digested availability state in build_snapshot with overlap refused; evaluation seam names gather, run_value, facet-read routing and check_verification, broader audit to slice 3.
- 2026-09-09T11:18:48Z (design/world-resolution): Plan reviewed 2026-09-09 (eight findings, resolved): W8b measured broken at build and dropped from cut 23's selection (7 closed of 8 read; the view refuses uid ambiguity at open); absent roots checked before the walk; evaluation absence covers assessment runs, every input role and the lineage snapshot; derived attribution reaches evaluate; dataclass default via default_factory; four N2 arms retargeted; three fixtures corrected; discharge through just check/test.
- 2026-09-09T11:59:42Z (design/world-resolution): took over session 88aa735c-590d-4eda-8d25-0fcf60bef434 (owner design/world-resolution, host titan, pid 1720691, worktree /mnt/ssd/Dropbox/beliefs/.worktrees/world-resolution, since 2026-09-09T09:17:51Z, age 9711s, stale: pid 1720691 is gone)
- 2026-09-09T11:59:42Z (design/world-resolution): User authorized takeover from closed Claude session; claimed by Codex /root, pid 2130612; executing slice 1 with per-task implementation and review.
- 2026-09-09T12:07:35Z (design/world-resolution): cut 23 frozen at d62c0dc, sha256 c4873f96fbe6cbbb2925a99a449abe4883e10341592b0c2d363485513bf3eb96; frozen §§2–7 sha256 678e30c3a50863a17df680a8357512194dabd4c617a388a08713562303484276
- 2026-09-09T16:05:31Z (design/world-resolution): Slice 1 discharged at cut 23; slices 2–4 filed as beliefs-113561 (coreference including W15), beliefs-46847c (snapshots/import/audit and packaging), beliefs-0e523a (view evaluation), in serial dependency order. Parent remains open; returning todo and releasing controller claim at slice handoff; beliefs-fda0e5 stays open.
- 2026-09-09T17:32:47Z (main): Slice 1 merged into main at 6eb0b93. Final review fixes verified by 511 certified tests; merged-main just gate passed 4218 Python and 142 TypeScript tests with zero task errors or warnings. Slices 2-4 and the W8b build defect remain open; claim remains released.
