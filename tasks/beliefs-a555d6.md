---
id: beliefs-a555d6
title: ruff format is not in the gate; 11 reproduction-lane files drift from it
status: idea
priority: 2
created: 2026-09-10T22:01:42Z
updated: 2026-10-09T14:39:37Z
depends: []
tags: [hygiene]
---

Seen 2026-09-10 while closing beliefs-efc32d: the pre-commit gate runs ruff check only (justfile py_check_cmd), and ruff format --check over python/tools/reproduction and tests/test_reproduction_driver.py listed 11 files it would reformat (line-length wrapping). Decide whether format joins the gate (one reformat commit, then enforced) or stays out; the current state is silent drift.

2026-09-16 doc review: 'ruff format --check .' from python/ reported 273 files would be reformatted, 159 already formatted. The drift is repo-wide, not 11 reproduction-lane files. Scoping this means deciding format's place in the gate over the whole tree, and the one reformat commit would touch frozen-cut test modules, which is a supersession by citation, not an edit.

Scope evidence 2026-10-09 (main at cb354e1):
- 347 files would be reformatted and 219 are already formatted: 70 in src, 180 in tests, 79 in tests/acceptance, 18 in tools. Line length is 120, from [tool.ruff] in python/pyproject.toml.
- N2 sabotages match exact source text. Formatting a scratch copy of src/beliefs and re-counting every declared beliefs arm: 1149 apply exactly once today, and 63 would stop applying (cut 46: 7, cut 19: 5, cuts 11/14/28/31/35: 4 each, ...). That means re-targets in many live guards' _LIVE_SABOTAGES, plus moved-pin records in cited_not_run.py for cited guards (cuts 9 and 10 are among them).
- Frozen declaration and guard modules are content-pinned (tests/frozen_guards.py), so they cannot be reformatted at all and would need a permanent exclude.

## Open questions

- Should ruff format be enforced at all? Options:
  (a) Keep it out of the gate and record why in AGENTS.md, then close this idea. N2's exact-text pins make reformatting src costly, and lint already runs.
  (b) Ratchet: enforce on files that are formatted today and on new files, via an exclude list of the 347 drifted paths.
  (c) Reformat everything once and re-target the 63 arms, keeping frozen modules excluded.
  Recommendation: (a). Formatting buys readability only, while (c) churns 63 conformance arms across many guards, and (b) leaves a 347-path exclude list that never shrinks on its own.

## Notes

- 2026-09-16T10:03:27Z (main): 2026-09-16 doc review: 'ruff format --check .' from python/ now reports 273 files would be reformatted, 159 already formatted — the drift is repo-wide, not 11 reproduction-lane files. Scoping this means deciding format's place in the gate over the whole tree, and the one reformat commit would touch frozen-cut test modules, which is a supersession by citation, not an edit.
- 2026-10-09T14:39:36Z (main): scope: question; measured 347/566 files drifted and 63 of 1149 applying N2 arms broken by an src reformat; options and recommendation (keep format out, record why) under Open questions
