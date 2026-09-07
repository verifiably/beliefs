---
id: beliefs-d84799
title: "pyright does not type-check tools/, and the baseline hides it"
status: todo
priority: 3
size: m
created: 2026-09-07T09:31:01Z
updated: 2026-09-07T09:31:01Z
depends: []
tags: [testing]
---

python/pyproject.toml's [tool.pyright] include is ["src", "tests"], so python/tools/ is never type-checked. The visible consequence is that the 12-error pyright baseline is entirely 'Import "reproduction" could not be resolved' in tests/test_reproduction_driver.py — tests that import a package pyright cannot see.

Adding tools to extraPaths was measured during the verification-publication slice: it surfaces roughly 1600 errors across tools/, so it is a real project rather than a config toggle. It was deliberately not attempted there.

Two things worth separating: making tests/test_reproduction_driver.py's imports resolvable (which would clear the whole standing baseline and make 'pyright is clean' a meaningful gate again), and type-checking tools/ itself. The first may be much cheaper than the second.
