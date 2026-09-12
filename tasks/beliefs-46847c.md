---
id: beliefs-46847c
title: "World resolution slice 3: snapshots, import, audit and diagnostics"
status: todo
priority: 2
size: l
created: 2026-09-09T15:26:44Z
updated: 2026-09-12T12:17:05Z
depends: [beliefs-113561, beliefs-b7994b]
parent: beliefs-d248ba
tags: [world-read]
---

Design and freeze slice 3 from docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md section 1 and cut 23 sections 2-3. Widen snapshot import, audit and diagnostic callers; discharge R23 snapshot, cross-corpus divergence and explicit-import clauses, X5 relabel, W13 remaining clauses, and W8a import/audit packaging arms. Keep R23 rules-store clauses with contract-cut and retain any unselected W8 remainder explicitly. Coordinate beliefs-fda0e5 for W8b, without treating the world-view open refusal as build conformance.

## Notes

- 2026-09-10T15:55:37Z (world-resolution): from slice 2 (spec §13 item 3): whether the world-scale audit should report an attestation over a deleted endpoint, beside the drift question slice 1 filed
- 2026-09-10T20:26:52Z (main): Cut-24 curation: source addressing slice 2b precedes slice 3 under the roadmap’s serial delivery order; the dependency now records that order.
- 2026-09-12T12:17:05Z (main): nodes 2.0 (nodes main b0c37b8, 5ff3c78) landed 2026-09-12: Corpus(root, mode="collecting") excludes damaged, misplaced and colliding files and reports them through check() as parse-error / path-mismatch / uid-collision / id-collision / path-collision findings. The audit callers this slice widens still open strict and report the first fault as CorpusStateMalformed; opening the audited root in collecting mode is the nodes-remainder ledger row's 'audits over damaged corpora', now buildable and owned by no boundary — select it here or record why not.
