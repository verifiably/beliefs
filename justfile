# Front door for tests. Full suite: `just test`. Gates: `just check` (seconds: lint,
# typecheck, task records) and `just gate` (check plus the suite). `just test-fast` is
# the documented fast local loop; the inner-loop rule itself lands in step 3 of the
# audit, after a baseline week, so no guidance points at it yet.
#
# Every recipe runs through the vendored timing wrapper tools/tt and the shared hygiene
# check tools/ops-check (source of truth: ops bin/tt and ops bin/ops-check), so each run
# is recorded and every project checks the same things first. Design:
# ops docs/specs/2026-09-04-test-ci-audit-design.md.
#
# The git hooks in .githooks/ are installed (core.hooksPath); AGENTS.md says what each
# costs. What is left of audit step 3 is the inner-loop guidance (beliefs-f253a1).

tt := "python3 tools/tt"

# Two packages, so each command is written once per package and the whole-repo commands
# below are composed from them. Recipes and hooks all run these, so none of them can
# drift from the others. Each is a subshell: `cd` must not leak to the next.
#
# `pytest` is bare on purpose. pyproject's addopts already carries `-q`; the documented
# `uv run --frozen pytest -q` is therefore a second `-q`, i.e. `-qq`, which drops the
# summary line the wrapper counts tests from.
#
# `pyright` takes no path argument, deliberately: python/README.md records that naming a
# path narrows the check and hides diagnostics outside it, which is how tests/ drifted
# once already. The gate is the whole project or it is not the gate.
py_fast_cmd := "(cd python && uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py)"
py_test_cmd := "(cd python && uv run --frozen pytest)"
py_check_cmd := "(cd python && uv run --frozen ruff check . && uv run --frozen pyright)"

# `npm ci` is installation, not a gate, so it stays out of the gate recipes and lives in
# `setup` below. `npx --no-install` so that a missing install fails here and says so,
# instead of silently fetching vitest from the network mid-test-run.
ts_fast_cmd := "(cd ts && npx --no-install vitest run --changed --passWithNoTests)"
ts_test_cmd := "(cd ts && npm test)"
ts_check_cmd := "(cd ts && npm run typecheck && npm run check)"

fast_cmd := py_fast_cmd + " && " + ts_fast_cmd
test_cmd := py_test_cmd + " && " + ts_test_cmd
hygiene_cmd := "python3 tools/ops-check"
check_cmd := hygiene_cmd + " && " + py_check_cmd + " && " + ts_check_cmd + " && tasks check"

# The checks a commit pays when it stages nothing under python/ or ts/: ruff, pyright,
# tsc and biome read only those two trees, so such a commit cannot change their verdict,
# and the pre-commit hook runs this instead (see .githooks/pre-commit). Composed from the
# same pieces as check_cmd so the two cannot drift. Baseline 2026-09-12: 76 of 196
# commits (39 percent) were docs- or tasks-only and each paid the 20s gate, pyright 92
# percent of it (beliefs-f253a1).
docs_check_cmd := hygiene_cmd + " && tasks check"

# What a fresh checkout or worktree needs before the gates can run. ts/ has no
# node_modules of its own until `npm ci`; the python side needs nothing, because `uv run
# --frozen` creates the venv and installs the locked dependencies (pyright included) on
# first use. No gitignored inputs: the suite reads only tracked fixtures. Idempotent.
# npm ci replaces node_modules; restore its local Dropbox ignore attribute afterward.
setup_cmd := "(cd ts && npm ci && attr -s com.dropbox.ignored -V 1 node_modules)"

# beliefs-92e6fe measured this at 164s against the serial gate's 868s and pinned
# pytest-xdist rather than adopting coverage-based selection; --dist=loadfile keeps every
# N2 test on one worker so its own 24 subprocess workers are not multiplied. An empty
# vitest selection is a result, not a failure.
#
# The documented fast local loop: xdist with N2 excluded, plus the affected TS tests.
test-fast:
    {{tt}} test-fast -- sh -c '{{fast_cmd}}'

# The serial pytest run is the required conformance gate.
#
# The full suite, both packages.
test:
    {{tt}} test -- sh -c '{{test_cmd}}'

# Seconds, not minutes: lint, typecheck, and the task-record check.
check:
    {{tt}} check -- sh -c '{{check_cmd}}'

gate: check test

# A gate that fails before `just setup` is an unhydrated tree, not a bug. Recorded like
# the gates, because setup that recurs is a cost.
#
# Make this checkout runnable: once right after `git worktree add`, again after a dependency change.
setup:
    {{tt}} setup -- sh -c '{{setup_cmd}}'

# Priced separately from the runs people ask for, so the report can cost the hook itself.
#
# What a pre-commit hook will run once the gate is green: `check`'s command.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_cmd}}'

# What the pre-commit hook runs when nothing under python/ or ts/ is staged: the checks that read what it touched.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

# What a pre-push hook will run: `gate`'s commands, under one hook target.
hook-pre-push:
    {{tt}} hook-pre-push -- sh -c '{{check_cmd}} && {{test_cmd}}'

# CI keeps a two-job matrix (Python 3.11/3.13, Node 20/24); each job runs the recipe for
# its package, so the whole job is one recorded number. These run exactly what `test` and
# `check` run for that package. `tasks check` is not in them: the tasks binary is not on
# a runner, which is why CI runs these rather than `just gate` (design section 4.6).
# The serial pytest run is deliberate — python/README.md makes it the required CI,
# conformance and completion gate, so CI does not use the xdist fast loop.
#
# The Python job: the serial suite, then ruff and pyright.
ci-python:
    {{tt}} ci-python -- sh -c '{{py_test_cmd}} && {{py_check_cmd}}'

# The TypeScript job: the suite, then tsc and biome.
ci-typescript:
    {{tt}} ci-typescript -- sh -c '{{ts_test_cmd}} && {{ts_check_cmd}}'
