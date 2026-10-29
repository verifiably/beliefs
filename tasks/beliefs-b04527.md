---
id: beliefs-b04527
title: "Idea: let the retraction-enumeration v2 rule refuse a uid held at two addresses itself"
status: shelved
priority: 3
created: 2026-10-28T19:56:52Z
updated: 2026-10-29T00:10:13Z
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
