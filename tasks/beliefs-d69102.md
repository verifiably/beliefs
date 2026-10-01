---
id: beliefs-d69102
title: "World read: consulted contracts ignore a corpus that holds only the proposition"
status: idea
priority: 2
created: 2026-10-01T17:35:30Z
updated: 2026-10-01T17:35:30Z
depends: []
tags: [world-read]
agent: claude-code/claude-opus-5-5
---

consulted_contracts (python/src/beliefs/consulted.py:59) takes its corpora only from closure nodes that node_corpus attributes. Gather attributes only assessments, runs and datasets (mount citations spec decision 10), so a corpus holding only the proposition contributes no pins. A world read where corpus M holds only the proposition, whose claim uses a namespace only M pins, would therefore raise ContractDisagreement ("namespace ... is consulted but pinned by no corpus") at consulted.py:121. This predates the mount-citations lane: found in cut 44's Task 6 review. Cut 44's durable J20 case uses profile_with()/biology("other") fixtures and covers no M-only namespace (spec §13). Next: write a world-read test over that shape and decide whether the proposition's corpus joins the consulted set.
