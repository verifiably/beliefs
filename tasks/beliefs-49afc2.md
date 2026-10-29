---
id: beliefs-49afc2
title: "A renamed record beside its predecessor publication: a supersession-aware address map"
status: shelved
priority: 2
created: 2026-10-28T13:14:47Z
updated: 2026-10-29T00:09:20Z
depends: []
tags: [world, publication]
source: docs/superpowers/specs/2026-10-28-overlapping-publications-design.md
agent: claude-code/claude-fable-5-1
origin: agent
---

From the overlapping-publications design (beliefs-918fd2, §4.1 and §10 item 2): a record renamed under a redirect (new live address, old address in deprecated_ids, same uid) held beside its predecessor publication refuses uid-corruption, one uid under two canonical addresses, so a successor publication carrying the renamed record cannot be mounted beside the dependency-kept predecessor. Science's adopt refuses it before admission (commons §10.5 exit, the §8 checklist). The lift is a map that recognises 'holder B's deprecated id is holder A's live address for the same uid' as a revision lineage rather than corruption, resolving the old address to the newer record without picking by holder order. Needs its own design: it touches W8b's first arm (uid-corruption offers no repair) and the retired-address fold.

## Notes

- 2026-10-28T13:14:47Z (add): created
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:09:16Z (main): shelved: Revisit when a concrete consumer needs to adopt a renamed successor while retaining its predecessor, or the user prioritizes relaxing W8b; then design lineage proof, ambiguous/forked renames and retired-address resolution together. Current cut-48 admission refusal remains intentional.
- 2026-10-29T00:09:20Z (main): scope: shelved; checked main db96252, derive.address_map and approved overlapping-publications spec sections 4.1, 4.2 and 10.2: renamed predecessors still refuse uid-corruption; the spec explicitly calls the lift not promised. Preserve the eventual possibility without scheduling a new conformance design absent a consumer need. Science admission is a required consumer contract, not verified shipped behavior in this pass. Wake: Revisit when a concrete consumer needs to adopt a renamed successor while retaining its predecessor, or the user prioritizes relaxing W8b; then design lineage proof, ambiguous/forked renames and retired-address resolution together. Current cut-48 admission refusal remains intentional.; origin: filing matched in claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae, toolu_01XhmPq1NMxiwRSdjGXzLSRv (transcript lines 1329/1339), full created result at 2026-10-28T13:14:47Z. User said Looks good! Let us draft the plan (line 1306); specific follow-up came from agent spec section 10.2, so agent retained. No origin_session names an older request.
  provenance: {"harness_session":"codex:01a184fa-66da-7722-b909-7ed94114de05","harness_session_source":"CODEX_THREAD_ID"}
