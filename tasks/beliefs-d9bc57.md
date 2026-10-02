---
id: beliefs-d9bc57
title: "Acceptance predicate on gather: counts(corpus_id, address) before retraction folding, policy in the context (science commons §9)"
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: main
created: 2026-10-01T02:21:10Z
updated: 2026-10-02T08:09:26Z
started: 2026-10-02T08:09:25Z
depends: []
tags: [belief]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
---

Requirement from science's commons design §9: belief must count a record only when the reader's acceptance policy says so, and the filter must apply to assessments, verifications and correction records before any of their effects and before any pool-level rule (retraction standing and the identity collapse included). Science hands a view, not records, and gather takes the retraction enumeration from the view and folds standing before any assessment is decoded, so the filter must be kernel-side: a predicate counts(corpus_id, address) supplied to gather and consulted before standing is folded, plus the caller's policy statement carried into the reproducibility context so the answer explains both the evidence considered and how it was selected. node_corpus already attributes nodes to corpora; the world and pin state are what the predicate encapsulates. Needed by milestone 1a.

## Notes

- 2026-10-02T08:09:25Z (main): started
  provenance: {"harness_session":"codex:01a0fba6-b334-7252-a61e-7aedd3e230bb","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-02T08:09:25Z (main): Scope confirmed: acceptance filtering first, publication attribution second, N2 preflight pilot third; planned design and implementation-plan review gates retained.
