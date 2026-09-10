---
id: beliefs-a555d6
title: ruff format is not in the gate; 11 reproduction-lane files drift from it
status: idea
priority: 2
created: 2026-09-10T22:01:42Z
updated: 2026-09-10T22:01:42Z
depends: []
tags: [hygiene]
---

Seen 2026-09-10 while closing beliefs-efc32d: the pre-commit gate runs ruff check only, and ruff format --check over python/tools/reproduction and tests/test_reproduction_driver.py lists 11 files it would reformat (line-length wrapping). Decide whether format joins the gate (one reformat commit, then enforced) or stays out; the current state is silent drift.
