---
id: beliefs-24b42b
title: Reconcile divergent identifier-correction histories at consolidate
status: todo
priority: 3
size: m
complexity: high
created: 2026-09-11T11:42:27Z
updated: 2026-09-12T16:26:55Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
---

Slice 2b makes consolidate refuse two source replicas whose identifier maps or correction histories differ (HistoryDisagreement). Reconciling them — which history survives, how tokens merge, whether the union of held addresses is the redirect set — needs its own design (slice 2b section 7).

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Slice 2b section 7 and relocation._reconcile intentionally refuse unequal identifier maps/histories. Choosing survivor history, token reconciliation and redirect-set semantics is the task itself and remains undesigned.
