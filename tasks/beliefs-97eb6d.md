---
id: beliefs-97eb6d
title: Clear the six ruff errors so just check can reach exit 0
status: done
priority: 2
size: xs
owner: main
created: 2026-09-07T11:55:34Z
updated: 2026-09-07T12:14:43Z
depends: []
tags: [testing]
---

`uv run --frozen ruff check .` exits 1 on main with six errors, and because check_cmd is `&&`-chained and ruff runs first, it short-circuits the whole gate in 0.06s — the pyright errors behind it are never even reached.

Five are auto-fixable in python/tests/test_reproduction_driver.py: two I001 (unsorted import blocks, at lines 16 and 146) and three RUF100 (`# noqa: E402` directives that are unused because E402 is not enabled). The sixth is a manual C408 in python/tools/reproduction/run.py:67 (`dict()` call to rewrite as a literal).

Checked while measuring beliefs-f253a1: the I001 reordering is safe. All three imports at line 16 sit after the `sys.path.insert` on line 14, so sorting among them does not move anything above the path setup.

This plus beliefs-d84799 (the twelve pyright errors) is what unblocks installing the git hooks. Neither alone does: hook-pre-commit runs the whole check_cmd. Until then the recorded `check` timing is time-to-first-failure, not the gate's cost.

## Notes

- 2026-09-07T12:14:43Z (main): ruff is clean: five auto-fixed (two I001 import blocks, three unused noqa: E402) plus one C408 dict() rewritten as a literal by hand. just check now runs the whole chain and records 18.5s instead of 0.044s, so the baseline week prices the real gate; it still exits 1 at pyright's twelve errors (beliefs-d84799).
