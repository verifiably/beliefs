---
id: beliefs-354eae
title: Give derive.address_map's retired-address collision a typed refusal instead of ValueError
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-25T13:10:53Z
updated: 2026-10-28T19:47:58Z
depends: []
tags: [world]
agent: claude-code
---

Why: A retired/deprecated address that another record claims as its live address reaches derive.address_map's final singularity check and raises a bare ValueError. Cut 41's final review reproduced that error over the same states through epoch publication and evaluate_live_query. Both paths still call the same derivation code at main 96066b6, so fix the shared boundary once.

Established: python/src/beliefs/world/derive.py::address_map first checks canonical uid-corruption, then canonical duplicate-location via AddressMapConflict, and only afterward folds live and deprecated addresses into the singular map. The last fold still raises ValueError for an already-held address. python/tests/test_world_derive.py::TestAddressMap.test_a_deprecated_entry_may_not_shadow_a_live_address explicitly expects that ValueError for a same-corpus fixture. The production callers are world/epoch.py::_derived_members and world/live.py::_address_map; world/read.py's similarly named helper reads a published map and is not this derivation.

Done: Replace only the retired-address singularity refusal in derive.address_map with the existing ResolutionRefused type, preserving diagnostic address and both (corpus_id, uid) claims. Use that existing typed refusal rather than add an error class or relabel this as a canonical duplicate-location that offers consolidate. Keep uid-corruption precedence, canonical duplicate-location findings and their existing error types/messages unchanged. Do not choose a carrier by precedence, silently drop the retired alias, catch the error only in live.py, or alter frozen cut-41 targets. Epoch publication and live query must surface the same typed refusal for the same captured states. The original decision-7 agreement requirement is [ref:live-design]; [ref:cut41-results] §3.3 records this exact deferred finding, and [ref:world-addresses] §5 requires the map to remain singular.

Verification: Update the existing direct derivation regression and cover a retired/live cross-corpus collision in both input orders, plus retired/retired ambiguity if the same branch handles it. Verify live-query and epoch-publication propagation and confirm no epoch or current pointer is published on refusal. Keep the existing uid-corruption-before-duplicate-location cases passing. Run affected tests through just test-one (test_world_derive.py, test_live_selection.py and the relevant epoch/acceptance tests), then just test-fast before committing. Preserve frozen evidence under [ref:freeze-doctrine]; capability-dependent checks need the certified tuple and must name a refusal rather than imply coverage. This scope pass used source/test inspection, not a fresh runtime reproduction.

Where: python/src/beliefs/world/derive.py::address_map, beliefs/errors.py's existing ResolutionRefused, python/tests/test_world_derive.py::TestAddressMap, python/tests/test_live_selection.py, and the epoch publication tests/acceptance fixtures reached through world/epoch.py. Preserve the original review note below.

## References

- live-design (input, required, kind=spec): docs/designs/2026-09-24-live-query-evaluation-design.md — current live-query guarantees and original duplication ruling
- cut41-results (context, kind=report): docs/plans/2026-09-25-conformance-cut-41-results.md — original deferred review findings
- freeze-doctrine (input, required, kind=spec): docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md — retarget live machinery and preserve historical evidence
- world-addresses (input, required, kind=spec): docs/designs/2026-08-02-world-addressing-design.md — singular address-map and conflict rules

## Notes

- 2026-09-25T13:11:06Z (main): From beliefs-cc0aea's final review (2026-09-25): when one record's deprecated id equals another record's live address in a different corpus, derive.address_map raises a plain ValueError rather than a typed refusal. publish (and so evaluate_live_query, bound to publish's address-map behaviour by the live-query design's decision 7) surfaces it untyped. Fix it in derive, not in world/live.py (cut 41's frozen arm targets). A scratch probe during the review reproduced it over the same states for both paths.
- 2026-10-24T11:16:04Z (main): scope: rescoped; at main 96066b6, confirmed derive.address_map's final retired-alias fold and existing regression still raise/expect ValueError; chose existing ResolutionRefused at that shared boundary, preserving canonical AddressMapConflict precedence and both callers; retained P3/s/mid, set direct, added same/cross-corpus and no-publication checks; no fresh runtime reproduction or new brief
- 2026-10-28T19:47:58Z (design/918fd2-overlapping-publications): absorbed by cut 48 (beliefs-918fd2), spec §4.2 rule 3: derive.address_map's deprecated-key collision now refuses the typed ResolutionRefused (and the merged snapshot fold's DeprecatedKeyCollision subclass carries the finding); pinned by test_w19_d_deprecated_key_entry; closed with the cut
