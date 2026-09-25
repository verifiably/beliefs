---
id: beliefs-1ce6cc
title: "Cut-40 final-review follow-ups: polish deferred at merge"
status: todo
priority: 3
created: 2026-09-24T15:41:32Z
updated: 2026-09-25T10:59:17Z
depends: []
tags: [publication, hygiene]
---

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

## Notes

- 2026-09-25T10:59:17Z (design/live-query): The remote slice this body calls cut 41 was renumbered to planned cut 42 on 2026-09-25 (live view-query evaluation froze as cut 41, beliefs-cc0aea).
