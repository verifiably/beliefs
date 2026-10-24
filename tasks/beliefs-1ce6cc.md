---
id: beliefs-1ce6cc
title: "Cut-40 final-review follow-ups: polish deferred at merge"
status: todo
priority: 3
size: m
complexity: mid
process: direct
created: 2026-09-24T15:41:32Z
updated: 2026-10-24T11:24:04Z
depends: []
tags: [publication, hygiene]
---

Why: Finish the cut-40 review's remaining publication boundary and test polish without reopening Y5–Y10 or changing the certified engine behavior.

Established at main 2437c71 (2026-10-24):
- The findings below were checked against current publish.py, publish_request.py, publication_doors.py, publication_arrival.py, corpus.py, durable.py, root.py and their unit/acceptance tests.
- The raw record-read exception from admit_publication is already owned by beliefs-059c90 (P2, direct). That task's correction establishes that load_manifest already raises typed ManifestMissing / ManifestMalformed. Do not duplicate it or normalize the manifest API incidentally.
- PUBLISHING_COORDINATION now names versions (1, 2, 3), including the attribution-aware V3_PIN and snapshot checks. The original (1, 2) observation is stale. Retain the explicit supported-release policy; automatically authorizing future shipped releases is outside this polish task.
- root.py::replicate_export deliberately propagates RootOperationMismatch for a foreign occupant. Cut-40 results §3.2 and test_publish_engine_order.py / acceptance/test_publish_act_acceptance.py record and assert that behavior. Retain it; wrapping it would change a certified boundary, not merely tidy it.
- The remote slice was delivered as cut 42, not cut 41. test_the_remote_orphan_fold already covers transport-incomplete-retires-nothing, but does not include a later ordinary staging-corrupt refusal carrying an existing orphan. Keep that narrower regression case.

Done: Address these remaining items using the existing local/remote publish contracts:
1. A closed report ending bound with no binding present returns PublishUnresolved, not PublishRefused("bound"); prove the fail-closed row writes nothing and amend the current recovery table in [ref:local] §9 to distinguish a recorded refusal from an inconsistent bound report.
2. _initialize follows the specified adopt_manifest / ManifestAlreadyPresent path, checks the held pins on retry, and has a pins-foreign regression test.
3. Reuse one binding-id calculation for _binding_present and _published_from_disk without changing identity.
4. decode_request rejects non-string science_contract pins and domain names/values as MalformedRecord before they reach later code.
5. Type admit_publication's world/observers seam using the established arrival interfaces, without taking over beliefs-059c90.
6. write_create_only removes its own temporary after a failed write/fsync, and treats the target name literally when finding leftovers. Test write and fsync failure plus glob-metacharacter names; preserve create-only collision behavior, complete writes and directory fsync obligations.
7. Type closure_missing's get/resolve view seam using the smallest existing interface or Protocol.
8. _refuse_publication rejects every entry whose subject differs from the intent's binding address before any durable effect.
9. _stage_record checks its permit before parsing untrusted text; test denied authority with malformed input while retaining kind-specific authorization and normal record validation.
10. _open_publication rejects an unpinned expected_view as MalformedRecord before any effect; keep the existing optional argument's cut-39 behavior.
11. For an unfinished request, compare the caller's staging profile with decoded request pins before snapshot validation can durably close it request-corrupt. A wrong-profile retry must leave the attempt untouched; a matching profile must retain the existing corrupt-snapshot refusal behavior. Keep finished and marked remote resume paths intact.
12. Add the ordinary pre-binding-refusal-after-existing-orphan case to the remote fold tests, proving the orphan survives.

Where to look: [ref:results] preserves the source findings and engine verdict; [ref:local] specifies request pins, initialization, report subjects and resume; [ref:remote] owns transport and orphan behavior. Primary checks: python/tests/test_publish.py, test_publish_request.py, test_publication_doors.py, test_publication_arrival.py, test_durable.py and the permit inventories; acceptance/test_publish_act_acceptance.py and test_publish_remote_acceptance.py cover the integrated paths. Check current session callers and publication attribution tests before changing shared resume code.

Verification: demonstrate each behavioral correction with a focused regression via just test-one; run just test-fast before commit and just check as required. Keep root.py the sole Atoms importer, both write inventories closed and live frozen-arm anchors valid. Run affected capability acceptance paths when the fast suite does not cover the changed behavior; preserve historical declarations/results and apply the frozen-guard doctrine to live machinery. This scope pass ran no runtime tests.

Process: direct; m/mid. Existing designs settle the outcome and verification; the work spans several bounded boundary cases. Priority stays 3. No new design task, release-discovery abstraction or replication-error API change is needed.

## Original capture (historical; dispositions above narrow the work)

Minors the cut-40 whole-branch review (design/publish) deferred at merge. Each is a polish item; none reopens a Y5–Y10 row.

- A `bound` report with an absent binding should read PublishUnresolved rather than PublishRefused("bound").
- A `pins-foreign` unit test for `publish._initialize`; and `_initialize` should catch ManifestAlreadyPresent instead of testing for `corpus.yaml`.
- One helper for the binding id: publish.py builds it twice.
- `decode_request` accepts non-string pins.
- `publication_arrival`'s world and observers parameters are untyped.
- durable.py leaves a stray `.tmp` on a failed write, and its glob pattern is unescaped.
- `PUBLISHING_COORDINATION` hard-codes versions (1, 2).
- `closure_missing`'s view parameter is untyped (a Protocol).
- `_refuse_publication` should refuse entries whose subject is not the intent's binding address.
- `_stage_record` parses before the permit check, so a raw nodes/YAML exception escapes on bad text.
- An unpinned `expected_view` should refuse MalformedRecord.
- Resume should check the request's pins before the snapshot checks (it writes `request-corrupt` first today).
- `admit_publication` lets a raw nodes parse exception escape on a corrupted record file (the repository-wide `iter_stored` pattern).
- A test that a pre-binding report retires no existing orphan (cut 41).
- Consider wrapping RootOperationMismatch as a typed WriteRefused in root.py's `replicate_export`.

Source: docs/plans/2026-09-24-conformance-cut-40-results.md §3.3 and the final-review fix wave (65bfe1d).

## References

- results (input, required, kind=report): docs/plans/2026-09-24-conformance-cut-40-results.md — original findings and certified replication verdict
- local (input, required, kind=spec): docs/superpowers/specs/2026-09-23-publish-act-local-design.md — request, initialization, report and recovery contract
- remote (input, required, kind=spec): docs/superpowers/specs/2026-09-26-publish-act-remote-design.md — transport-mark recovery and orphan rules

## Notes

- 2026-09-25T10:59:17Z (design/live-query): The remote slice this body calls cut 41 was renumbered to planned cut 42 on 2026-09-25 (live view-query evaluation froze as cut 41, beliefs-cc0aea).
- 2026-10-24T11:24:04Z (main): scope: rescoped; checked against main 2437c71 and cut40 results/local and remote designs; retained twelve bounded follow-ups, assigned the duplicate admission error solely to beliefs-059c90, updated the supported-version observation to (1,2,3), retained certified RootOperationMismatch propagation, and narrowed the missing orphan regression; preserved all original source material; priority 3, m/mid/direct under existing contracts with an explicit recovery-table clarification
