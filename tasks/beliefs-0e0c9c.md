---
id: beliefs-0e0c9c
title: Make the reproduction driver's imports resolvable so pyright is green
status: done
priority: 2
size: xs
owner: main
created: 2026-09-07T12:40:40Z
updated: 2026-09-07T12:42:04Z
depends: []
parent: beliefs-d84799
tags: [testing]
---

The cheap half of beliefs-d84799. pyright cannot see python/tools/, so tests/test_reproduction_driver.py's 'from reproduction import ...' is unresolvable and the standing twelve-error baseline is entirely that file.

Add extraPaths = ["tools"] to [tool.pyright] so imports resolve without putting tools/ in include (measured: 12 errors to 3). The three that remain are real: _assoc() uses importlib.util.spec_from_file_location, whose ModuleSpec | None and Loader | None both need narrowing before module_from_spec and exec_module.

That takes pyright to zero, which makes 'pyright is clean' a meaningful gate again and turns just check green for the first time, unblocking both the git hooks and beliefs-e7b186. Type-checking tools/ itself stays with the parent.

## Notes

- 2026-09-07T12:42:04Z (main): extraPaths = ["tools"] plus one assertion narrowing spec and spec.loader in _assoc(). pyright is at 0 errors, and just check exits 0 for the first time. Hooks and beliefs-e7b186 are unblocked; type-checking tools/ (42 errors, not the 1600 the parent estimated) stays with beliefs-d84799.
