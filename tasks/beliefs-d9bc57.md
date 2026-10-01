---
id: beliefs-d9bc57
title: "Acceptance predicate on gather: counts(corpus_id, address) before retraction folding, policy in the context (science commons §9)"
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-10-01T02:21:10Z
updated: 2026-10-01T02:21:10Z
depends: []
tags: [belief]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
---

Requirement from science's commons design §9: belief must count a record only when the reader's acceptance policy says so, and the filter must apply to assessments, verifications and correction records before any of their effects and before any pool-level rule (retraction standing and the identity collapse included). Science hands a view, not records, and gather takes the retraction enumeration from the view and folds standing before any assessment is decoded, so the filter must be kernel-side: a predicate counts(corpus_id, address) supplied to gather and consulted before standing is folded, plus the caller's policy statement carried into the reproducibility context so the answer explains both the evidence considered and how it was selected. node_corpus already attributes nodes to corpora; the world and pin state are what the predicate encapsulates. Needed by milestone 1a.
