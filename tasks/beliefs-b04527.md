---
id: beliefs-b04527
title: "Idea: let the retraction-enumeration v2 rule refuse a uid held at two addresses itself"
status: shelved
priority: 3
created: 2026-10-28T19:56:52Z
updated: 2026-10-29T00:10:16Z
depends: []
tags: [world, conformance]
source: beliefs-918fd2
agent: claude-code/claude-fable-5-1
origin: agent
---

Cut 48's review (minor 6): rules_v1/retraction_v2.py lets the last record win for live_of[uid]; at build derive.address_map refuses uid-corruption first, but validate_receipt reruns the rule over a recapture without the map, so a uid-corrupted drift validates as refuted rather than naming corruption (as v1 does today). A third ValueError in the rule would complete its two-inputs-are-not-worlds docstring. Caveat that makes this an idea rather than a fix: the rule's bytes are its implementation identity, so the change is a new bundle (or a v2.1 implementation installed beside the current one) and every v2-bound receipt keeps validating only while the old pair stays held; scope it with the rules-store clauses R23 retains.

## Notes

- 2026-10-28T19:56:52Z (add): created
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:10:13Z (main): shelved: Revisit when a receipt consumer needs explicit uid-corruption diagnostics, or a successor retraction rule is already being designed; preserve the existing implementation pair for old receipts and decide new-bundle retention before changing rule bytes.
- 2026-10-29T00:10:16Z (main): scope: shelved; checked main db96252, rules_v1/retraction_v2.py live_of assignment, read._rebuilt_receipt exact-pair lookup and RuleNonconformant handling, and cut-48 final review minor 6. The extra corruption refusal is a diagnostic extension with rule-identity cost, not an established false-validation defect. The source review says same as v1 today; the body phrase as v1 does today must not be read as evidence that v1 names corruption. New work is deferred rather than silently mutating a receipt-bound implementation. Wake: Revisit when a receipt consumer needs explicit uid-corruption diagnostics, or a successor retraction rule is already being designed; preserve the existing implementation pair for old receipts and decide new-bundle retention before changing rule bytes.; origin: filing inferred in claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae, toolu_01GN8drvw7m6xFHZJ5SfSQcb at transcript line 5554, matching sourced add and id-only pipeline result with no captured reuse warning; user at line 5550 asked whether follow-ups should be created, but the specific asks came from agent review/limitations, so agent retained. No origin_session names an older request.
  provenance: {"harness_session":"codex:01a184fa-66da-7722-b909-7ed94114de05","harness_session_source":"CODEX_THREAD_ID"}
