---
id: beliefs-a61cb4
title: "Cut 48 review minors: validate the address-map content at open, name the live address in the disagreement message, share RULE_INPUT_V2, drop audit's dead corpus_id, label no-capture, test the legacy damaged branch"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-28T19:56:48Z
updated: 2026-10-28T19:56:48Z
depends: []
tags: [world]
source: beliefs-918fd2
agent: claude-code/claude-fable-5-1
origin: agent
---

The eight deferred minors of cut 48's whole-branch review (the ledger attached to beliefs-918fd2 as execution-ledger.md; report final-review-round-1-report.md), none a defect: (1) epoch._check_addresses admits any non-empty content while read._address_map's AddressEntry requires 64 lower hex, so a malformed member raises a bare ValueError outside the EpochMalformed wrapper, and derive.address_map_projection would serialise a legacy content None; add _require_lower_hex at open and refuse None in the projection (unreachable through the kernel's own writes). (2) open_world_view's disagreement message names the first sorted key of the uid, which may be a deprecated id; name a present copy's node.id. (3) derive.py spells science.rule-input.v2 while rules exports RULE_INPUT_V2; share one constant or name the import reason. (4) audit.py's corpus_id = targets[0] is dead after the per-holder fan-out and survives only so W20-i's frozen after text parses; remove it and retarget W20-i in test_n2_cut48.py's _LIVE_SABOTAGES in the same change. (5) _CapturedCitations._holder labels a holder with no recorded cause and no readable view unreadable; no-capture says what happened. (6) _refuse_damaged's fail-closed branch for a legacy entry with one damaged and one captured holder has no direct test. The v2 rule's own uid-corruption refusal is a separate idea, since it changes the rule's bytes.

## Notes

- 2026-10-28T19:56:48Z (add): created
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
