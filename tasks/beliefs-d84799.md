---
id: beliefs-d84799
title: "pyright does not type-check tools/, and the baseline hides it"
status: done
priority: 3
size: m
created: 2026-09-07T09:31:01Z
updated: 2026-09-09T09:17:06Z
depends: []
tags: [testing]
---

python/pyproject.toml's [tool.pyright] include is ["src", "tests"], so python/tools/ is never type-checked. The visible consequence is that the 12-error pyright baseline is entirely 'Import "reproduction" could not be resolved' in tests/test_reproduction_driver.py — tests that import a package pyright cannot see.

Adding tools to extraPaths was measured during the verification-publication slice: it surfaces roughly 1600 errors across tools/, so it is a real project rather than a config toggle. It was deliberately not attempted there.

Two things worth separating: making tests/test_reproduction_driver.py's imports resolvable (which would clear the whole standing baseline and make 'pyright is clean' a meaningful gate again), and type-checking tools/ itself. The first may be much cheaper than the second.

## Notes

- 2026-09-07T12:40:40Z (main): Measured 2026-09-07, both figures in the body are wrong: extraPaths = ["tools"] alone takes the baseline from 12 errors to 3 (all in tests/, none in tools/), and putting tools in include type-checks it for 42 errors, not roughly 1600. So type-checking tools/ is a bounded piece of work, not the project the body describes; the import-resolution half is a config line plus three assertions.
- 2026-09-07T18:27:25Z (main): Half landed with cut 20's merge (b818471): extraPaths = ["tools"] makes tools/ importable so test_reproduction_driver.py's imports resolve, without adding it to include — the cheap half this task hypothesised, and the pyproject comment now cites this task for the rest. Baseline is gone: measured on f2d5a14 from python/, pyright 0 errors and ruff all-passed, down from 12 and 6. Remaining work is deciding whether to type-check tools/ at all (~1600 errors when measured) or to keep importable-but-unchecked as the end state. Upshot: 'pyright/ruff clean' are meaningful gates again, so any new diagnostic is genuinely new.
- 2026-09-09T09:17:06Z (hygiene/n2-arms): Verdict: importable-but-unchecked is the end state. Measured 2026-09-09: checking tools/ gives 30 errors, 29 of them 'argument missing for authority' in the cut 4-16 runners, which are frozen commands of the trees they discharged on and are pinned by later guards (11 runner pins), so they cannot be repaired; the one live error, in the reproduction driver, is noted on beliefs-efc32d. The pyproject comment now states the verdict instead of citing this task.
