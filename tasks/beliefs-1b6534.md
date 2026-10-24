---
id: beliefs-1b6534
title: test_n2_cut5.py carries 15 pre-existing failures from four older causes
status: dropped
priority: 3
size: m
complexity: mid
created: 2026-09-07T09:30:47Z
updated: 2026-10-24T11:12:40Z
closed: 2026-10-24T11:12:40Z
depends: []
parent: beliefs-199aeb
tags: [conformance]
---

tests/acceptance/test_n2_cut5.py fails 15 of 34 on main today, and did so identically at 74a5938 — none of it caused by the verification-publication slice, which fixed only its run-key spelling at line 143.

Four distinct causes, all older API surfaces:
- TypeError: CorpusWriter.import_bundle() got an unexpected keyword argument 'actor' (x5)
- beliefs.errors.ActorMismatch: the retraction names actor 'cut5', not the bound 'test-actor' (x5, corpus.py:1814)
- CoordinationKindUnsupported: 'note' enters through the coordination family door (corpus.py:2245)
- ValueError: actor must be a non-empty string (permit.py:72)
The remaining 3 are the arm-audit tests reporting those plus three stale sabotages.

Cut 5 feeds cuts 7-13 via tools/cut5_acceptance.py:45,66, so this debt has to be paid before any cut-5-citing chain runs green. Note pyproject.toml:42's addopts ignores tests/acceptance, so the portable suite never sees any of it.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-conformance-readiness-brief.md — frozen-cut disposition evidence

## Notes

- 2026-09-12T16:26:55Z (main): Complexity mid: The obsolete actor/import and coordination call sites are identified and still visible in cut 5. Repair is bounded, but stale sabotage handling and downstream acceptance-chain validation must preserve frozen evidence.
- 2026-09-16T10:03:27Z (main): 2026-09-16 doc review: the live certified chain (cut31 → cut30 → … → cut17, whose 19 phases start at test_n2_cut6.py) does not run cut 5, so this debt is invisible to every current discharge; it blocks only a re-run of cuts 5–13's own runners (cut7_acceptance.py still lists cut5_acceptance.py as a prefix). Still worth paying before beliefs-5aad8c's acceptance half, which needs those runners exercisable.
- 2026-10-24T11:06:15Z (main): scope: drop; at main a7ce8ff, cut 5 is explicitly cited-not-run in the registry and refused collection by acceptance conftest; retained original fifteen-failure report and todo status; brief: docs/notes/2026-10-24-conformance-readiness-brief.md; proposal: drop this API-repair task because 8b7fbc3 deliberately restored its frozen evidence and c153ac2 ruled old runner signatures historical; beliefs-5aad8c's dependent frozen-runner premise needs its own later re-scope
- 2026-10-24T11:12:40Z (main): dropped
  provenance: {"harness_session":"codex:01a16d90-ccf8-7d22-b11f-6f5a19dd8da9","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-24T11:12:40Z (main): User approved the proposed drop: cut 5 is cited-not-run historical evidence under 8b7fbc3 and c153ac2; retain the frozen record rather than repair it for current APIs.
  provenance: {"harness_session":"codex:01a16d90-ccf8-7d22-b11f-6f5a19dd8da9","harness_session_source":"CODEX_THREAD_ID"}
