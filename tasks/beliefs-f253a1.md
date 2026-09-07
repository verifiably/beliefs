---
id: beliefs-f253a1
title: Test + CI iteration cost audit
status: doing
priority: 2
size: m
owner: test-ci-audit
created: 2026-09-04T21:44:54Z
updated: 2026-09-07T11:17:52Z
depends: [ops-31f038]
tags: [testing]
---

Piece of ops-65837b (the cross-project audit in the ops hub). 1. Measure: full-suite wall time, and roughly how often agent full-suite runs fail here. 2. Add a fast or affected-only test target for the inner loop and point AGENTS.md at it; keep the full suite for commit and CI. 3. Use a quiet reporter so test output does not flood agent context. 4. Fix suite hygiene: sleeps, real network, unshared fixtures. Record the before and after numbers in a note on this task.

## Notes

- 2026-09-05T02:38:40Z (main): design: ops docs/specs/2026-09-04-test-ci-audit-design.md; follow §5: (1) justfile + vendored tools/tt, route existing hooks, CI, and documented test commands through it, verify a line lands under each agent; (2) after a week of runs, add a note reading 'baseline <date>: <tt-report --project numbers>'; (3) gates to §4.6, AGENTS.md line, hygiene; (4) close with before/after numbers
- 2026-09-07T11:17:52Z (test-ci-audit): step 1 wired 2026-09-07: justfile (two packages composed into fast/test/check, plus gate and both hook targets), vendored tools/tt version 2, .tt/ gitignored, AGENTS.md and python/README.md repointed at the recipes. No CI here to route. Verified in the shared log ~/.local/share/ops/runs.jsonl: three test-fast lines, agent claude / null (by hand) / codex, all exit 0, 3701 tests, 168.5-216.1s; no fallback .tt/ log, so this sandbox reaches the shared log.
- 2026-09-07T11:17:52Z (test-ci-audit): Hooks deliberately NOT installed, the one part of step 1 left undone: just check fails on main. ruff 6 errors and pyright 12, all in the mm30 reproduction lane (tests/test_reproduction_driver.py, tools/reproduction/run.py; cf. beliefs-d84799, beliefs-efc32d), reproduced in the main checkout too. A pre-commit hook running hook-pre-commit would block every commit. Hooks land with the 4.6 gate move in step 3, once the gate is green; the recipes are already there and core.hooksPath is one command.
- 2026-09-07T11:17:52Z (test-ci-audit): Two recipe details worth keeping: pytest is bare, not the documented -q, because addopts already carries -q and a second one is -qq, which drops the summary line tt counts tests from; pyright keeps no path argument per python/README.md, since naming a path hides diagnostics outside it. npm ci stays out of the recipes as installation, and ts_fast_cmd uses npx --no-install so a fresh worktree without ts/node_modules fails loudly instead of fetching vitest mid-run.
- 2026-09-07T11:17:52Z (test-ci-audit): ops spec 4.5 assigned beliefs pytest --testmon, but beliefs-92e6fe had already measured and rejected coverage-based selection on 2026-09-04, pinning pytest-xdist; testmon is not a dependency. Corrected that row in ops docs/specs/2026-09-04-test-ci-audit-design.md in the same change; test-fast runs the project's own documented loop.
