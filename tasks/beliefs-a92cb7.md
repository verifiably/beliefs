---
id: beliefs-a92cb7
title: "Curate beliefs public docs: distill the first-pass retained documents into a small set of polished reference docs and move the rest to records"
status: todo
priority: 0
size: l
complexity: high
process: planned
created: 2026-11-02T00:59:55Z
updated: 2026-11-02T01:00:00Z
depends: [ops-550b90]
tags: [docs]
source: ops-9a11f4
agent: claude-code/claude-opus-5-5
origin: user
---

User 2026-11-01 (session 9f8562e0, approving the beliefs records migration's retained set under ops-550b90): "retained set approved, but a task should be created to do a follow up pass clean and distill the 76 remaining records into a much smaller set of polished documents (ops-9a11f4)".

Reading (agent's, open to correction): the documents that remain in the beliefs code tree after the migration are the 290 of the retained set (attachment retained-set-beliefs-v5.txt on ops-550b90: docs/designs 89, docs/plans 128, docs/superpowers/specs 38, docs/superpowers/plans 33, docs/notes 4); the 76 named in that list are the working documents that move to the records directory with the 750 task files. This task takes the in-tree set; if the user meant the 76 moved documents, re-scope.

Goal, per ops-9a11f4: retained sets are temporary first-pass concessions. Distill the retained historical designs, cuts, results records, slice specs and plans into a much smaller set of polished, current reference documents (README, the contributor guide and typed reference docs under document types v1), move every remaining historical/working file out to records, and update everything that cites them: code comments, guides, tests that open documents by path (test_designs_corpus, test_check_guide, acceptance FROZEN_CUT constants), cut runners and cited_not_run pins.

Constraints to design around: AGENTS.md's frozen-conformance-cut rules (frozen bodies preserved, superseded by citation) and the cut-acceptance machinery that reads frozen documents by tree path; records-migrate's retained-set closure (version 5, citation rule 2) decides what can leave once citers change. Pilot and receipt: lore-666ce3 (records lore/docs/notes/2026-10-26-reference-docs-migration-receipt.md); sibling piece crew-6d51c5; type standard ops-ebff8f.

## Notes

- 2026-11-02T00:59:55Z (add): created
  provenance: {"harness_session":"claude-code:9f8562e0-f49d-4fa9-8f28-0333a41aa940","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"user"}
