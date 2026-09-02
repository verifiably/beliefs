---
id: beliefs-e32746
title: Fix Python Pyright regressions after cut 13
status: done
priority: 1
size: xs
owner: fix/python-pyright
created: 2026-09-01T23:24:36Z
updated: 2026-09-01T23:56:18Z
depends: [beliefs-739255]
tags: [python, typing]
---

Restore the Python typecheck gate by narrowing cut-13 test fixtures and decoded projections without changing production contracts.

## Notes

- 2026-09-01T23:24:42Z (fix/python-pyright): Reproduced 31 Pyright errors; all arise from unnarrowed unions, optional confined fields, or decoded object values in five cut-13 test files.
- 2026-09-01T23:55:58Z (fix/python-pyright): Added explicit runtime narrowing in five tests; Pyright is clean, affected tests pass 88/88, and the full Python suite passes 2850/2850.
- 2026-09-01T23:56:18Z (fix/python-pyright): Narrowed cut-13 test values at runtime and restored a clean Python typecheck gate.
