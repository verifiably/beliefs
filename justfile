# Front door for tests. Full suite: `just test`. Gates: `just check` (seconds: lint,
# typecheck, task records) and `just gate` (check plus the suite). `just test-fast` is
# the documented fast local loop; `just test-one <runner args>` is the focused loop.
# CI carries the full suite for origin/main; other pushes keep the complete local gate.
#
# Every recipe runs through the vendored timing wrapper tools/tt and the shared hygiene
# check tools/ops-check (source of truth: ops bin/tt and ops bin/ops-check), so each run
# is recorded and every project checks the same things first. Design:
# ops docs/specs/2026-09-04-test-ci-audit-design.md.
#
# The git hooks in .githooks/ are installed (core.hooksPath); AGENTS.md says what each
# costs. What is left of the audit is step 4, the after-week comparison (beliefs-f253a1).

set quiet
set positional-arguments

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
py_fast_cmd := "(cd python && uv run --frozen pytest -n auto --dist=loadgroup --ignore=tests/test_n2.py)"
py_test_cmd := py_fast_cmd + " && (cd python && uv run --frozen pytest tests/test_n2.py)"
py_check_cmd := "(cd python && uv run --frozen ruff check . && uv run --frozen ruff format --check . && uv run --frozen pyright)"

# `npm ci` is installation, not a gate, so it stays out of the gate recipes and lives in
# `setup` below. `npx --no-install` so that a missing install fails here and says so,
# instead of silently fetching vitest from the network mid-test-run.
ts_fast_cmd := "(cd ts && npx --no-install vitest run --changed --passWithNoTests)"
ts_test_cmd := "(cd ts && npm test)"
ts_check_cmd := "(cd ts && npm run typecheck && npm run check)"

fast_cmd := py_fast_cmd + " && " + ts_fast_cmd
test_cmd := py_test_cmd + " && " + ts_test_cmd
# Focused pytest selection, relative to python/. Override one_cmd for Vitest (AGENTS.md).
one_cmd := "cd python && uv run --frozen pytest"
hygiene_cmd := "python3 tools/ops-check"
check_cmd := hygiene_cmd + " && " + py_check_cmd + " && " + ts_check_cmd + " && tasks check"

# Only agent guidance and task records take the docs-only path. README.md and docs/
# are read by conformance tests, so the template's broader allowlist is unsafe here.
docs_paths := "AGENTS.md tasks/*.md"
docs_check_cmd := hygiene_cmd + " && tasks check"

# ci.yml runs both complete package suites on main pushes and on PRs. PR-only refs
# cannot shorten a push gate; only origin/main is covered by the push trigger.
ci_suite_refs := "refs/heads/main"
ci_remote := "origin"

# Fixed fast set (act design form 3): all non-N2 Python tests plus all TS tests.
# Vitest's unbased --changed selection sees no committed push changes in a clean tree.
push_fast_cmd := py_fast_cmd + " && " + ts_test_cmd

# What a fresh checkout or worktree needs before the gates can run. ts/ has no
# node_modules of its own until `npm ci`; the python side needs nothing, because `uv run
# --frozen` creates the venv and installs the locked dependencies (pyright included) on
# first use. No gitignored inputs: the suite reads only tracked fixtures. Idempotent.
# npm ci replaces node_modules; restore its local Dropbox ignore attribute afterward.
setup_cmd := "(cd ts && npm ci && attr -s com.dropbox.ignored -V 1 node_modules)"

# beliefs-92e6fe measured the parallel fast loop at 164s against the serial gate's
# 868s and pinned pytest-xdist rather than adopting coverage-based selection.
# Scoped fixture consumers share a file or class group; other tests schedule separately.
# An empty vitest selection is a result, not a failure.
#
# `test`, `test-fast` and the pre-push hook run under ops' `host-budget run`, which sizes
# them to this host's CPU budget: `-n auto` reads PYTEST_XDIST_AUTO_NUM_WORKERS, and
# N2's pool reads OPS_WORKERS and refuses to run without it (ops
# docs/specs/2026-09-24-host-budget-design.md). `tt` stays outside so it times the run.
#
# The documented fast local loop: xdist with N2 excluded, plus the affected TS tests.
test-fast:
    {{tt}} test-fast -- host-budget run -- sh -c '{{fast_cmd}}'

# One path, path::test, or -k expression; argument boundaries reach the runner intact.
test-one +args:
    {{tt}} test-one -- host-budget run -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"

# The complete Python gate: parallel non-N2 tests, then N2 alone with its full
# OPS_WORKERS pool. Both summaries are counted by tt as one recorded run.
#
# The full suite, both packages.
test:
    {{tt}} test -- host-budget run -- sh -c '{{test_cmd}}'

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

# What the pre-commit hook runs when every staged path matches docs_paths.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

# What a pre-push hook will run: `gate`'s commands, under one hook target.
hook-pre-push:
    {{tt}} hook-pre-push -- host-budget run -- sh -c '{{check_cmd}} && {{test_cmd}}'

# Every pushed ref is covered by CI's full suite: checks and the fixed fast set.
hook-pre-push-fast:
    {{tt}} hook-pre-push-fast -- host-budget run -- sh -c '{{check_cmd}} && {{push_fast_cmd}}'

# CI keeps a two-job matrix (Python 3.11/3.13, Node 20/24); each job runs the recipe for
# its package, so the whole job is one recorded number. These run exactly what `test` and
# `check` run for that package. `tasks check` is not in them: the tasks binary is not on
# a runner, which is why CI runs these rather than `just gate` (design section 4.6).
# A runner has no host-budget, so ci.yml sets both worker variables for the
# parallel first phase and the standalone N2 pool.
#
# The Python job: both pytest phases, then ruff and pyright.
ci-python:
    {{tt}} ci-python -- sh -c '{{py_test_cmd}} && {{py_check_cmd}}'

# The TypeScript job: the suite, then tsc and biome.
ci-typescript:
    {{tt}} ci-typescript -- sh -c '{{ts_test_cmd}} && {{ts_check_cmd}}'

# The mm30 recreation in one command (beliefs-9e0b42): the reproduction design's §13 and
# §14 sequence into a fresh work directory, one process per step, stopping at the first
# non-zero exit, then the read-only verdict and the tracked Snakefile check. Five steps
# record a defect and still exit zero, so the verdict, not the exit codes, says whether it
# reproduced (docs/notes/2026-09-29-reproduction-audit-backlog-brief.md, Recipe
# inventory). Not part of any gate, and it deletes nothing. The cut-22 and cut-31
# archives default to the fixture's siblings under the main checkout's .work/reproduction/.
#
# Recreate the mm30 corpus into WORK, a fresh absolute canonical path, from PREDECESSOR.
mm30-recreate work predecessor cut22="" cut31="":
    #!/usr/bin/env bash
    set -euo pipefail
    work=$1 predecessor=$2
    fixtures="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.work/reproduction"
    cut22=${3:-$fixtures/mm30.cut22} cut31=${4:-$fixtures/mm30.cut31}
    snakefile=python/tools/reproduction/analysis/workflow/Snakefile
    refuse() { echo "mm30-recreate: $*" >&2; exit 2; }
    [[ $work == /* && $(realpath -m "$work") == "$work" ]] || refuse "the work directory must be absolute and canonical: $work"
    [[ ! -e $work ]] || refuse "the work directory already exists; the verdict is defined over a fresh one: $work"
    [[ -d $predecessor ]] || refuse "no predecessor root at $predecessor"
    for archive in "$cut22" "$cut31"; do
        for required in corpus/corpus.yaml state.json; do
            [[ -f $archive/$required ]] || refuse "the archive $archive has no $required"
        done
    done
    git diff --quiet -- "$snakefile" || refuse "$snakefile differs from HEAD before the run"
    export PYTHONPATH=tools SCIENCE_MM30_ROOT=$work MM30_PREDECESSOR=$predecessor MM30_CUT22_ARCHIVE=$cut22
    steps=(preflight world select_target analysis_inputs "lists prepare" concepts "lists mint" type_target hold spec run belief rederive close compose read "read --again" "transition --archive $cut31")
    cd python
    for step in "${steps[@]}"; do
        echo "== $step"
        started=$SECONDS
        # shellcheck disable=SC2086 # a step is a module and its arguments
        uv run --frozen python -m reproduction.$step || { status=$?; echo "mm30-recreate: stopped at '$step' (exit $status)" >&2; exit $status; }
        echo "== $step: $((SECONDS - started)) s"
    done
    echo "== verdict"
    status=0
    uv run --frozen python -m reproduction.verdict || status=$?
    cd ..
    git diff --quiet -- "$snakefile" || { echo "FAIL tree: $snakefile differs from HEAD after the run"; status=1; }
    echo "mm30-recreate: $SECONDS s wall, exit $status, into $work"
    exit $status
