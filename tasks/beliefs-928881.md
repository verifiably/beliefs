---
id: beliefs-928881
title: Close D1 through the cross-repository domain-boundary negative
status: doing
priority: 2
size: m
owner: design/d1-cross-repo-negative
created: 2026-09-10T20:26:23Z
updated: 2026-09-12T14:09:34Z
started: 2026-09-12T13:29:49Z
depends: []
tags: [cross-repo, conformance]
spec: docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md
plan: docs/superpowers/plans/2026-09-12-d1-cross-repository-negative.md
---

Outcome: close the sole remaining domain-boundary clause, D1’s negative that adds a domain-aware code path to nodes and proves the independent conformance check refuses it. The Beliefs domain slices are already discharged at cuts 20 and 22; this is not another domain implementation slice.

Acceptance: agree the Nodes-local design gate and cross-repository mutation harness with its owner; freeze the D1 selection before implementation; exercise the negative against the real Nodes package; retain runnable refusal evidence; discharge the cut on the required tuple and update the ledger and roadmap. Do not add a production domain-aware path to Nodes. Keep nodes-ce28b8’s broader Nodes 2.0 contract work separate.

Sources: docs/plans/2026-09-08-conformance-cut-22-results.md sections 2 and 5; docs/designs/2026-08-04-domain-extension-boundary-design.md D1; docs/plans/2026-08-29-implementation-roadmap.md domain-boundary. The Nodes-local gate remains unapproved; begin with that coordination and design.

## Notes

- 2026-09-12T13:34:45Z (design/d1-cross-repo-negative): 2026-09-12: design spec drafted at docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md in .worktrees/d1-cross-repo-negative (branch design/d1-cross-repo-negative). Key finding: no existing check would refuse a domain-aware nodes path — signature inspection cannot see a branch on a string — so the design adds a namespace-renaming invariance check over the installed nodes, extends N2 Sabotage with a package field so a sabotage can land in a copy of nodes, and asks nodes for a STANDARD 2.3 opacity sentence plus a seam 8 row, no nodes code. Cut 26 (highest across branches is 25).
- 2026-09-12T13:34:51Z (design/d1-cross-repo-negative): parked (waiting on user, review): review the design spec at .worktrees/d1-cross-repo-negative/docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md; on approval: file the nodes task (STANDARD 2.3 sentence + seam 8 row), then write cut 26's design and the implementation plan
