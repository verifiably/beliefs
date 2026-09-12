---
id: beliefs-48214e
title: Dataset addresses derived from the content identity
status: todo
priority: 2
size: l
complexity: high
created: 2026-09-11T11:42:27Z
updated: 2026-09-12T16:26:55Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
---

dataset_node takes an authored slug while dataset_address is computed and never checked against the id; 189 dataset_node sites measured 2026-09-10. The choice between dataset:sha256: as the address and a digest domain is this design's. Filed by slice 2b (docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md section 12).

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Slice 2b section 12 deliberately leaves the dataset address domain/basis decision open. stored.dataset_node still accepts an authored slug while dataset_address derives content identity; enforcing agreement affects identity and existing references, not just the measured builder sites.
