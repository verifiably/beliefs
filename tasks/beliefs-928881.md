---
id: beliefs-928881
title: Close D1 through the cross-repository domain-boundary negative
status: todo
priority: 2
size: m
created: 2026-09-10T20:26:23Z
updated: 2026-09-10T20:26:23Z
depends: []
tags: [cross-repo, conformance]
---

Outcome: close the sole remaining domain-boundary clause, D1’s negative that adds a domain-aware code path to nodes and proves the independent conformance check refuses it. The Beliefs domain slices are already discharged at cuts 20 and 22; this is not another domain implementation slice.

Acceptance: agree the Nodes-local design gate and cross-repository mutation harness with its owner; freeze the D1 selection before implementation; exercise the negative against the real Nodes package; retain runnable refusal evidence; discharge the cut on the required tuple and update the ledger and roadmap. Do not add a production domain-aware path to Nodes. Keep nodes-ce28b8’s broader Nodes 2.0 contract work separate.

Sources: docs/plans/2026-09-08-conformance-cut-22-results.md sections 2 and 5; docs/designs/2026-08-04-domain-extension-boundary-design.md D1; docs/plans/2026-08-29-implementation-roadmap.md domain-boundary. The Nodes-local gate remains unapproved; begin with that coordination and design.
