---
id: beliefs-595a53
title: Design the stored source-assertion boundary from the evidence brief
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-10-14T01:34:45Z
updated: 2026-10-14T01:34:45Z
depends: [beliefs-9c375c]
parent: beliefs-9396cf
tags: [contract]
source: docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md
agent: codex
---

Why: contracts/science/CONTRACT.yaml names stored.source_assertion_value, but stored.py has neither that reader nor a dedicated builder. The in-memory record.SourceAssertion exists and enforces its closed signs; evaluation.gather supplies no source assertions. parse_facet_declarations checks the reader label is nonempty text and does not dispatch it, while validate_payload deliberately skips reader-shaped facets. The missing stored path is therefore not a contract-loading crash, nor proof that G1's value-level tests failed.

Outcome: Produce a reviewed design for the smallest complete stored source-assertion boundary, using docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md. Reconcile the in-memory value with kernel section 4.2's source-span anchoring and attribution, the base contract's anchored_in relation, and stored identity and facet validation. Decide where assertion signs/proposition references live, the exact projection and malformed-record behavior, and which reader/builder/write/import/audit paths must enforce it. Reuse beliefs-9c375c's endpoint matrix before deciding resolution and relation enforcement; do not turn the descriptive reader labels into a generic runtime dispatcher.

Done when: The design records accepted and rejected representations, named implementation surfaces, compatibility and identity consequences, and checks for round trip, malformed payloads, missing/incorrect source references, the forbidden assesses route, and unchanged belief under added source assertions. Check the source-correction alias case deferred by world-resolution slice 2b. Name the conformance owner and impacts on both the canonical and packaged contract and TypeScript parity. Preserve frozen cuts and G1's separation. Follow spec review then plan review before implementation; implementation itself is outside this task.

Where: python/src/beliefs/record.py, stored.py, contract/facets.py, facets.py, corpus.py, evaluation.py; contracts/science/CONTRACT.yaml and python/src/beliefs/contracts/science/CONTRACT.yaml; tests/test_records.py, test_belief.py, test_facet_validation.py; docs/designs/2026-08-02-epistemic-kernel-design.md; docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md. Specs belong in docs/superpowers/specs/.

Ideas it wakes: Before this result's branch merges, run tasks note beliefs-a1a767 --no-reviewed "<reviewed design and implementation handoff>".
