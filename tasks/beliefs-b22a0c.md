---
id: beliefs-b22a0c
title: corpus.py's import call site calls _validated_retraction twice
status: todo
priority: 4
size: xs
complexity: low
process: direct
created: 2026-09-19T18:52:24Z
updated: 2026-10-09T14:39:37Z
depends: []
tags: [hygiene, conformance]
---

Why: CorpusWriter._validate_import_bundle (python/src/beliefs/corpus.py ~L3274–3282) calls self._validated_retraction(record) once to validate a bundled retraction, then again only to read target.arm before calling _resolve_snapshot_target. The first call has been there since bf78f7a. The second came with 6090cf4 (snapshot targets, BI-1/BI-2) and follows the shape slice 2's Task 2 plan prescribed. It is not a defect, but each import validates every retraction twice, including the semantic-hash stamp check.

Done: bind facet = self._validated_retraction(record) once and branch on facet["target"]["arm"] == "snapshot". The refusal order stays the same: validate, resolve the target, then resolve the snapshot. No behaviour change.

Where to look / verification:
- No N2 arm pins these lines: a 2026-10-09 grep of tests/ and tests/acceptance/ for the call site and for _resolve_snapshot_target found none.
- test_arm_staleness stays at zero stale arms.
- Run just test-one tests/test_import_bundle.py tests/test_corpus_write.py tests/test_snapshot_retraction.py; test_corpus_write.py covers snapshot-arm import.
- Then run just test-fast.

## Notes

- 2026-10-09T14:39:36Z (main): scope: scoped; confirmed the double call at corpus.py ~L3277/3279 and that no N2 arm pins it; rewrote body; todo P4/xs/low/direct
