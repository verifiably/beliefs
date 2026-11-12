# Front door for tests. Full suite: `just test`. Gates: `just check` (hygiene, then lint
# and typecheck) and `just gate` (check plus the suite). `just test-fast` is the
# documented fast local loop; `just test-one <runner args>` is the focused loop.
# A `.tt.toml` (absent: enabled) may skip the broad targets; `just test-full` and
# `TT_FORCE=1 just gate` are the deliberate suite and full-gate routes (AGENTS.md).
# CI runs the full suites on every branch push; the push hook treats ci_suite_refs as
# covered, and other pushes take the full local route, which tt policy may skip.
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
# `pyright` takes no path argument, deliberately: docs/development.md records that naming a
# path narrows the check and hides diagnostics outside it, which is how tests/ drifted
# once already. The gate is the whole project or it is not the gate.
py_fast_cmd := "(cd python && uv run --frozen pytest -n auto --dist=loadgroup)"
py_test_cmd := py_fast_cmd
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
hygiene_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && python3 python/tools/check_doc_links.py && (cd python && uv run --frozen python tools/check_shipped_contracts.py)"
# The always-run checks (protected under tt policy) and the code checks (broad).
check_hygiene_cmd := hygiene_cmd + " && tasks check"
check_code_cmd := py_check_cmd + " && " + ts_check_cmd

# Agent guidance, the README and the public documents under docs/ take the docs-only
# path: no test reads them, so a commit that changes only them cannot change a result.
# The match is fnmatch, so the `*` also spans subdirectories.
docs_paths := "AGENTS.md README.md docs/*.md"

# The refs whose pushes the hook treats as covered by CI's complete package suites.
# ci.yml runs them on every branch push (test_ci_workflow.py checks that it covers
# each glob here), so every branch push to origin is covered; tags and other remotes
# take the full route, whose suite tt policy may skip with a warning.
ci_suite_refs := "refs/heads/*"
ci_remote := "origin"

# Fixed fast set (ops test-ci-act design, form 3): all Python tests plus all TS tests.
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
# `test`, `test-fast`, `test-push` and `test-one` run under ops' `host-budget run`, which sizes
# them to this host's CPU budget: `-n auto` reads PYTEST_XDIST_AUTO_NUM_WORKERS (ops
# docs/specs/2026-09-24-host-budget-design.md). `tt` stays outside so it times the run.
#
# The documented fast local loop: xdist over the Python tests, plus the affected TS tests.
test-fast:
    {{tt}} test-fast -- host-budget run -- sh -c '{{fast_cmd}}'

# Every real-engine acceptance module, each in its own process (about 25 minutes). Not a
# broad target: tt policy never skips it. BELIEFS_ACCEPTANCE_ROOT overrides the work root.
# It takes no arguments; a focused run is `just test-one tests/acceptance/<module>.py`.
test-acceptance:
    {{tt}} test-acceptance -- host-budget run -- sh -c 'cd python && uv run --frozen python tools/acceptance_runner.py'

# One path, path::test, or -k expression; argument boundaries reach the runner intact.
test-one +args:
    {{tt}} test-one -- host-budget run -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"

# The full suite, both packages.
test:
    {{tt}} test -- host-budget run -- sh -c '{{test_cmd}}'

# Deliberate suite evidence: `test` forced past tt policy. Untimed; tt records the
# inner `test` row with reason `forced`. It runs no hygiene, lint or typecheck.
test-full:
    TT_FORCE=1 just test

# The fixed push set (all Python tests plus all TS tests), its own recorded target.
test-push:
    {{tt}} test-push -- host-budget run -- sh -c '{{push_fast_cmd}}'

# Always runs: the shared hygiene checks, the document link check and the task-record check.
check-hygiene:
    {{tt}} check-hygiene -- sh -c '{{check_hygiene_cmd}}'

# Lint, format and typecheck for both packages.
check-code:
    {{tt}} check-code -- sh -c '{{check_code_cmd}}'

# Untimed: each child records its own row.
check:
    just check-hygiene
    just check-code

# Untimed. `TT_FORCE=1 just gate` is the full-gate evidence route.
gate:
    just check
    just test

# A gate that fails before `just setup` is an unhydrated tree, not a bug. Recorded like
# the gates, because setup that recurs is a cost.
#
# Make this checkout runnable: once right after `git worktree add`, again after a dependency change.
setup:
    {{tt}} setup -- sh -c '{{setup_cmd}}'

# Hook targets time their hygiene only, so the report can cost the hook itself.
#
# Each hook times its hygiene under its own target, then runs the broad children as
# nested recipes, so tt decides each child separately and a failure stops the rest.
#
# The pre-commit hook: hygiene, then the code checks.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'
    just check-code

# What the pre-commit hook runs when every staged path matches docs_paths.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{check_hygiene_cmd}}'

# The full push gate: hygiene, the code checks, then the full suite.
hook-pre-push:
    {{tt}} hook-pre-push -- sh -c '{{check_hygiene_cmd}}'
    just check-code
    just test

# Every pushed ref is covered by CI's full suite: hygiene, the code checks, then the fixed push set.
hook-pre-push-fast:
    {{tt}} hook-pre-push-fast -- sh -c '{{check_hygiene_cmd}}'
    just check-code
    just test-push

# CI keeps a two-job matrix (Python 3.11/3.13, Node 20/24); each job runs the recipe for
# its package, so the whole job is one recorded number. These run exactly what `test` and
# `check` run for that package. `tasks check` is not in them: the tasks binary is not on
# a runner, which is why CI runs these rather than `just gate` (ops test-ci-audit design §4.6).
# A runner has no host-budget, so ci.yml sets the xdist worker variable.
#
# Each also writes JUnit into BELIEFS_CI_EVIDENCE_DIR, which ci.yml uploads; the
# reporting flags select nothing, so the suites are py_test_cmd's and ts_test_cmd's.
ci_evidence_cmd := "case \"${BELIEFS_CI_EVIDENCE_DIR:?set BELIEFS_CI_EVIDENCE_DIR}\" in /*) ;; *) echo \"CI evidence path must be absolute\" >&2; exit 2;; esac"
ci_py_test_cmd := "(cd python && uv run --frozen pytest -n auto --dist=loadgroup --junitxml=\"$BELIEFS_CI_EVIDENCE_DIR/pytest.xml\")"
ci_ts_test_cmd := "(cd ts && npm test -- --reporter=default --reporter=junit --outputFile.junit=\"$BELIEFS_CI_EVIDENCE_DIR/vitest.xml\")"

# The Python job: the pytest suite, then ruff and pyright.
ci-python:
    {{tt}} ci-python -- sh -c '{{ci_evidence_cmd}} && {{ci_py_test_cmd}} && {{py_check_cmd}}'

# The TypeScript job: the suite, then tsc and biome.
ci-typescript:
    {{tt}} ci-typescript -- sh -c '{{ci_evidence_cmd}} && {{ci_ts_test_cmd}} && {{ts_check_cmd}}'

# The full legacy route remains separately owned and cannot run under the current pack.
mm30-recreate work predecessor cut22="" cut31="":
    #!/usr/bin/env bash
    echo 'mm30-recreate: unsupported legacy composite/cut route; beliefs-6f039b owns restoration. Use mm30-phf19 for the selected RNA demonstration.' >&2
    exit 2

# One explicitly declared gene RNA engineering demonstration; no ranking or old cuts.
mm30-phf19 work predecessor hgnc ensembl declaration="python/tools/reproduction/phf19-inputs.json":
    #!/usr/bin/env bash
    set -euo pipefail
    work=$1
    predecessor=$(realpath -e "$2")
    hgnc=$(realpath -e "$3")
    ensembl=$(realpath -e "$4")
    declaration=$(realpath -e "$5")
    cd python
    PYTHONPATH=tools uv run --frozen python -m reproduction.phf19 "$work" "$predecessor" "$hgnc" "$ensembl" --declaration "$declaration"
