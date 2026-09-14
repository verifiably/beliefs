---
id: beliefs-48214e
title: Dataset addresses derived from the content identity
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: design/world-resolution-slice-5
created: 2026-09-11T11:42:27Z
updated: 2026-09-14T22:45:20Z
started: 2026-09-14T22:06:20Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
spec: docs/superpowers/specs/2026-09-14-world-resolution-slice-5-design.md
plan: docs/superpowers/plans/2026-09-14-world-resolution-slice-5.md
---

dataset_node takes an authored slug while dataset_address is computed and never checked against the id; 189 dataset_node sites measured 2026-09-10. The choice between dataset:sha256: as the address and a digest domain is this design's. Filed by slice 2b (docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md section 12).

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Slice 2b section 12 deliberately leaves the dataset address domain/basis decision open. stored.dataset_node still accepts an authored slug while dataset_address derives content identity; enforcing agreement affects identity and existing references, not just the measured builder sites.
- 2026-09-14T22:06:16Z (main): Process planned: slice 2b §12 leaves the address domain/basis choice (dataset:sha256: vs a digest domain) open and enforcing id/address agreement touches identity and existing references; opened as world-resolution slice 5 under rule 6 — no kernel lane open after cut 28 and this is the world-read lane's head
- 2026-09-14T22:18:44Z (design/world-resolution-slice-5): Slice 5 spec drafted 2026-09-14: keep dataset:sha256:<fold> as ruled (domain digest rejected), builder drops the slug, boundary adds DatasetAddressDisagreement in _refuse_dataset_basis clause 2; no seam or history; cut 29 re-reads W2/W3/W8 dataset arms, closes nothing; migration measured at 217 test sites, 768 literals, 52 title-only raw-corpus sites; cut 7 INTERPOSED_WRITE needs a dated live adapter
- 2026-09-14T22:18:54Z (design/world-resolution-slice-5): parked (waiting on user, review): User reviews docs/superpowers/specs/2026-09-14-world-resolution-slice-5-design.md; on approval, write the implementation plan (writing-plans) in this worktree
- 2026-09-14T22:26:49Z (design/world-resolution-slice-5): Spec review 1 (2026-09-14): consolidate must validate both dataset inputs before _reconcile (loser's declaration was discarded unexamined); boundary BasisMissing tests migrate to governed_node so the builder refusal cannot satisfy them. Both taken in the spec §12.
