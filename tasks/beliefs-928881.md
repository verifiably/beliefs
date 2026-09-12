---
id: beliefs-928881
title: Close D1 through the cross-repository domain-boundary negative
status: todo
priority: 2
size: m
complexity: mid
created: 2026-09-10T20:26:23Z
updated: 2026-09-12T16:28:17Z
depends: []
tags: [cross-repo, conformance]
---

Outcome: close the sole remaining domain-boundary clause, D1’s negative that adds a domain-aware code path to nodes and proves the independent conformance check refuses it. The Beliefs domain slices are already discharged at cuts 20 and 22; this is not another domain implementation slice.

Acceptance: agree the Nodes-local design gate and cross-repository mutation harness with its owner; freeze the D1 selection before implementation; exercise the negative against the real Nodes package; retain runnable refusal evidence; discharge the cut on the required tuple and update the ledger and roadmap. Do not add a production domain-aware path to Nodes. Keep nodes-ce28b8’s broader Nodes 2.0 contract work separate.

Sources: docs/plans/2026-09-08-conformance-cut-22-results.md sections 2 and 5; docs/designs/2026-08-04-domain-extension-boundary-design.md D1; docs/plans/2026-08-29-implementation-roadmap.md domain-boundary. The Nodes-local gate remains unapproved; begin with that coordination and design.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity mid: The draft in .worktrees/d1-cross-repo-negative/docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md now specifies namespace invariance, two mutations, installed-package resolution and shared portable N2 inventory. Review, Nodes documentation gate and cut freeze remain; harness integration is bounded by that design. Existing review park is unchanged.
- 2026-09-12T16:28:17Z (main): Complexity evidence correction: the spec header and shared review park lag the worktree. Read its linked implementation plan and task records; history through d3d4c07 in .worktrees/d1-cross-repo-negative already contains the Nodes gate, invariance check, harness and freeze. The remaining discharge task beliefs-af9fd8 is already mid: certified acceptance-chain validation and evidence/status reconciliation remain bounded work. The mid rating stands. On merge retain the worktree task metadata and notes alongside this rating; no worktree edits or ownership takeover here.
