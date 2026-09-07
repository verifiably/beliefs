---
id: beliefs-1b6534
title: test_n2_cut5.py carries 15 pre-existing failures from four older causes
status: todo
priority: 3
size: m
created: 2026-09-07T09:30:47Z
updated: 2026-09-07T09:30:47Z
depends: []
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
