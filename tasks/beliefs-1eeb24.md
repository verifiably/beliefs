---
id: beliefs-1eeb24
title: Measure content-identity cost across world reads and policy folds
status: todo
priority: 3
size: m
complexity: mid
process: direct
created: 2026-10-28T19:56:58Z
updated: 2026-10-29T00:10:22Z
depends: []
tags: [world]
source: beliefs-918fd2
agent: claude-code/claude-fable-5-1
origin: agent
---

Question: After cut 48 and 345d2d4, what is the end-to-end cost of content identity in open_world_view, evaluate_live_query and gather with a policy at 10,000 and 100,000 records, without overlap and with equal-content overlap; does evidence justify designing a per-corpus content index keyed by corpus state identity?

Where to start: world/view.py open_world_view, world/live.py _address_map, corpus.py _merged_capture and evaluation.py gather. Use python/tests/acceptance/test_overlapping_publications_acceptance.py for valid typed worlds and holder-policy cases, and test_snapshot_retraction.py::test_the_merge_digests_only_addresses_several_holders_claim for the digest boundary. Read [ref:overlap] for exact equality and holder semantics and [ref:review] for the original cost observation. Main db96252 includes 345d2d4: snapshot folding hashes only multiply-held addresses; view opening and live mapping still compute content identities. The review's approximately 274 microseconds/node is historical local microbenchmark evidence, not a measured end-to-end cost or a portable threshold.

Bound: One reproducible measurement pass covering the three entry points at both requested sizes and overlap conditions. State unique-record and total-holder-copy counts, record shape, overlap fraction, policy and query. First run a small pilot through fixture creation, all entry points, correctness checks, timing and verdict; inspect it before the larger run. Keep fixture construction outside timed calls, report repeated timings and memory plus host/runtime/commit/load and cache conditions, and account for observer overhead. Preserve existing semantics and rule identities; no cache implementation or invalidation design in this task. The project currently declares no shared-resource need vocabulary: do not invent --need quiet; follow the host-load/quiet-run workflow if an uncontended window is required.

Expected result: Attach the reproducible driver, raw measurements and a short result to this task; distinguish measured end-to-end time from attributed digest cost, verify unchanged result/holder-policy behavior, and recommend either no cache work or a separately reviewed cache design with the evidence and remaining uncertainty. Run project test recipes appropriate to any committed measurement code. Priority 3, size m, complexity mid, process direct: the output is bounded evidence and a recommendation, not an architectural implementation.

Ideas it wakes: None currently depend on this measurement. Record the finding here; if later waiting ideas are added, record the finding on each with tasks note <id> --no-reviewed before the result branch merges.

## Original capture (preserved)

Cut 48's limitation 8 is 'no cost measurement'. The review measured content_identity at about 274 microseconds per node on this host; open_world_view and live._address_map digest every captured record, and the merged snapshot fold now digests only addresses several holders claim (345d2d4). Measure open_world_view, evaluate_live_query and gather with a policy over a world of 10,000 and 100,000 records with and without overlap, and decide whether a cached per-corpus content index (keyed by corpus state identity) is worth its invalidation rules.

## References

- overlap (input, required, kind=spec): docs/superpowers/specs/2026-10-28-overlapping-publications-design.md — equality and holder semantics
- review (input, required, kind=review): tasks/files/beliefs-918fd2/final-review-round-1-report.md — historical cost observation and scope limits

## Notes

- 2026-10-28T19:56:58Z (add): created
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T00:10:22Z (main): scope: scoped; main db96252 contains 345d2d4 and its digest-boundary regression test. Established the three entry points, 10k/100k equal-overlap matrix, small end-to-end pilot, correctness checks and evidence-only deliverables; no cache implementation authorized. Searched open content-identity, benchmark and performance work across related projects; no overlapping measurement task found. Reused this record and existing spec/review instead of adding a brief or research duplicate. P3/m/mid/direct; original capture preserved. origin: filing inferred in claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae, toolu_01GN8drvw7m6xFHZJ5SfSQcb at transcript line 5554, matching sourced add and id-only pipeline result with no captured reuse warning; user at line 5550 asked whether follow-ups should be created, but the specific asks came from agent review/limitations, so agent retained. No origin_session names an older request.
  provenance: {"harness_session":"codex:01a184fa-66da-7722-b909-7ed94114de05","harness_session_source":"CODEX_THREAD_ID"}
