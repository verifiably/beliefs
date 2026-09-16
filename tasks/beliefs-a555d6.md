---
id: beliefs-a555d6
title: ruff format is not in the gate; 11 reproduction-lane files drift from it
status: idea
priority: 2
created: 2026-09-10T22:01:42Z
updated: 2026-09-16T10:03:27Z
depends: []
tags: [hygiene]
---

Seen 2026-09-10 while closing beliefs-efc32d: the pre-commit gate runs ruff check only, and ruff format --check over python/tools/reproduction and tests/test_reproduction_driver.py lists 11 files it would reformat (line-length wrapping). Decide whether format joins the gate (one reformat commit, then enforced) or stays out; the current state is silent drift.

## Notes

- 2026-09-16T10:03:27Z (main): 2026-09-16 doc review: 'ruff format --check .' from python/ now reports 273 files would be reformatted, 159 already formatted — the drift is repo-wide, not 11 reproduction-lane files. Scoping this means deciding format's place in the gate over the whole tree, and the one reformat commit would touch frozen-cut test modules, which is a supersession by citation, not an edit.
