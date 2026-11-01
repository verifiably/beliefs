# Beliefs test execution policy adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split beliefs' gates into protected hygiene and broad children under tt policy, widen hosted CI with durable coverage evidence, and activate `automatic_broad = false` only after accepted hosted evidence and explicit approval.

**Architecture:** The justfile gains `check-hygiene`, `check-code`, `test-push` and `test-full`, and the hooks compose them as nested `just` calls so each child gets its own tt decision. The pre-push hook adopts ops' policy warning. `ci.yml` widens to every branch, forces tt at job scope and uploads JUnit plus a module inventory. Fixture-checkout tests with stub executables prove every route without running a real suite.

**Tech Stack:** just, POSIX sh, Python 3.11+ (pytest, PyYAML), vendored `tools/tt` v9, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-31-test-execution-policy-design.md`, accepted at `68fa37f`. Spec-review ledgers (rounds 1 to 6) are attached to beliefs-067a8d. This plan folds in round 4's three minors and round 6's five (marked `[r4 Mn]`, `[r6 Mn]`).

## Global Constraints

- Command strings, test selection and argument forwarding stay unchanged, except that `ci-python` and `ci-typescript` add JUnit output. `tools/tt` is not edited.
- `host-budget` stays inside tt's child command. A policy skip launches neither `host-budget` nor its children.
- No new dependency, selector engine or second workflow.
- Policy text at activation, exactly:
  ```toml
  automatic_broad = false
  broad_targets = ["test", "test-fast", "test-push", "check-code", "ci-python", "ci-typescript"]
  ```
- No `.tt.toml` reaches the registered main checkout before Task 9 Step 1. The design branch carries the unintegrated activation commit from Task 8 Step 5 (plan round 1 Ruling I1), and the worktree runs under policy-off from then on. Tests never disable the real checkout's policy; every policy case uses a fixture checkout.
- `ci_suite_refs` stays `refs/heads/main` until the activation commit (Task 8 Step 5), which sets `refs/heads/*`.
- Every test subprocess gets an environment built key by key: `PATH`, a temporary `HOME`, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM=1`, fake `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, and each variable the case needs. `TT_FORCE` and `GITHUB_ACTIONS` are absent unless a case sets them. Each fixture asserts its `git rev-parse --show-toplevel` and `--absolute-git-dir` before its first write. No case runs a recipe with `cwd` at the repository root.
- Workflow keeps both matrices (Python 3.11/3.13, Node 20/24), the pinned actions, frozen installs, the atoms and nodes sibling checkouts at their default branches, `fetch-depth: 0`, `OPS_WORKERS=4`, `PYTEST_XDIST_AUTO_NUM_WORKERS=4` and `VERIFIABLY_UNCERTIFIED_HOST=1`.
- Exact enabled-floor note: `policy: enabled at <RFC3339-UTC> revision <full-sha>`.
- External gates: every push, workflow run and account write needs explicit user approval at that moment. The publication approval (Task 7) covers pushing the policy-enabled revision only. Activation needs a separate approval on the activation packet (Task 8). The ops pilot's approval does not transfer.
- GitHub reads and writes use `GH_TOKEN=$(gh auth token --user khughitt) gh …`. Conventional commits, no AI attribution.
- AGENTS.md's two conformance-cut obligations (the `root.py` atoms importer, the recent-cut acceptance row) do not apply: no cut is discharged here.
- Every `just test`, `test-fast` and `test-one` run starts from the physical worktree path (`cd "$(pwd -P)"`), never through the `.worktrees` symlink, whose spelling makes atoms' `open_root` fail with `ELOOP`. The `.worktrees/…` spelling is for paths shown to the user.
- Task records commit wherever the tasks CLI runs. Until Task 7's merge, task commands run in the worktree. From the merge on, they run in the main checkout, where they add only `tasks/*.md` commits after the integrated revision. Every push names its approved commit by refspec (`git push origin <approved-sha>:refs/heads/main`), so no later record commit rides along unapproved. Every packet lists what that push publishes, `git log --oneline origin/main..<sha>` and `git diff --stat origin/main <sha>`, so no earlier unpushed commit rides along unnamed.
- Policy is absent (enabled) in the worktree through Tasks 2 to 8 Step 4. Each task works RED to GREEN through `just test-one`, runs `just test-fast` before committing, and lets the hooks run. A skipped suite is never green evidence.

## Review Focus

1. A push whose stdin has a deletion line, a malformed line or a trailing blank line: the split hook must still route by every line and forward the bytes unchanged (Task 4 test).
2. Git's hook variables (`GIT_DIR`, `GIT_WORK_TREE`) leaking into the nested `just` children, which would let a child test write into the real repository (Task 4 test).
3. An evidence directory whose path contains spaces: both JUnit paths and the inventory must still be written there (Task 5 test).
4. No `.tt.toml` at all: every hook still runs every child, in order, with reason `default`. This is the state Tasks 2 to 8 run in and the state after any lost policy file (Task 3 test).
5. A forced run whose broad child fails: `TT_FORCE=1 just gate` and `just test-full` must exit nonzero with the child's failure recorded, never reported as a pass (Task 3 tests).

---

### Task 1: Execution Setup and baseline

**Files:**
- Modify: `docs/superpowers/specs/2026-10-31-test-execution-policy-design.md:3-5` (status line only)

- [ ] **Step 1: Recheck shared delivery state.** Run `tasks show ops-8bfa85`, `tasks show ops-68729d`, `tasks show lore-fdbe86`, `tasks show ops-56aab7` and `python3 tools/tt --version` or the version line in `tools/tt`. Expected: ops-68729d and lore-fdbe86 done, ops-56aab7 open, tt version 9. Note any change on beliefs-067a8d. A change to the shared contract stops the work for a spec revision.
- [ ] **Step 2: Run the baseline** from the physical worktree path through the harness's background mechanism with a 30-minute timeout, teeing to the task scratch directory:
  `PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-rfEs" just test 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-067a8d/baseline.log"`, with `set -o pipefail`. Note the scratch directory's creation on the task (host, path, purpose, owner) when it is first made.
  Expected: exit 0, three summary lines (non-N2 about 6,300 or more passed, since the hosted run collected 6,354; N2 46 passed; Vitest 155 passed).
- [ ] **Step 3: Record the baseline** as a task note: the command, the three counts, failures (expected none), and every `SKIPPED` line of both pytest phases verbatim. Attach `baseline.log`. These SKIPPED lines are the local skip-reason baseline Task 8 compares against.
- [ ] **Step 4: Update the spec's status line** [r6 M5] to: revised after spec rounds 1 (`60b6487`), 2 (`e2927dd`) and 3 (`2cee097`); round 4 accepted `5237cb7`; round 5 (codex/gpt-6.1-sol, relayed by the user, who asked for its two revisions before implementation planning) revised it; round 6 accepted `68fa37f`. Claim no approval beyond what the task record holds. Keep the sentence that the document authorizes no publication, push or activation.
- [ ] **Step 5: Commit** `docs(spec): record test policy design review history`.

### Task 2: Isolated route fixture and ported front-door cases

**Files:**
- Create: `python/tests/route_fixtures.py`
- Modify: `python/tests/test_front_door.py` (rewritten)

**Interfaces:**
- Produces, in `route_fixtures.py`:
  - `ROOT: Path`, the repository root.
  - `BROAD: list[str] = ["test", "test-fast", "test-push", "check-code", "ci-python", "ci-typescript"]` [r4 M1].
  - `class Checkout` with `__init__(self, tmp: Path)`; `root: Path`; `env: dict[str, str]`; `run(self, *args: str, stdin: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]`; `just(self, *args: str) -> CompletedProcess[str]`; `policy(self, enabled: bool = False, targets: list[str] = BROAD) -> None` (writes the fixture `.tt.toml`); `events(self) -> list[list]` (each `[name, args, cwd, GIT_DIR]`); `rows(self) -> list[dict]` (the fixture tt log); `set_suite_refs(self, value: str) -> None` (rewrites the fixture justfile's `ci_suite_refs := "…"` line); `capture_hook_recipe(self) -> None` (installs `bin/just` that delegates `--evaluate` to the real binary and otherwise writes `$1` to `chosen` and stdin to `refs.actual`).
  - No shared pytest fixture: each test constructs `Checkout(tmp_path)` directly, as nodes' `test_ci_evidence.py` does. Importing a fixture only to name it as a parameter trips Ruff F401/F811.

Fixture contents, per the nodes pattern and [r4 M1]:
- The checkout root is `tmp / "checkout"`, so sibling repositories at `../../atoms` from `<root>/python` land at `tmp/atoms` inside the test's own temporary directory.
- Directories `python/`, `ts/`, `tools/`, `.githooks/`, `bin/`, `home/`, `evidence/`; copies of `justfile`, `tools/tt`, `.githooks/pre-commit`, `.githooks/pre-push`.
- `git init` under the key-by-key env; top-level and git-dir assertions before any write.
- Env keys: `PATH` (`<root>/bin`, the real `just`'s directory, `/usr/bin`, `/bin`), `HOME`, `GIT_CONFIG_GLOBAL=<root>/home/gitconfig`, `GIT_CONFIG_NOSYSTEM=1`, fake author and committer, `FIXTURE_ROOT`, `EVENTS=<root>/events.jsonl`, `TT_LOG=<root>/runs.jsonl`, `BELIEFS_CI_EVIDENCE_DIR=<root>/evidence` (absolute), `PYTEST_XDIST_AUTO_NUM_WORKERS=1`.
- Python-source stubs on `bin/`: `uv`, `npm`, `npx`, `tasks`, `ssh`; Python-source `tools/ops-check` and `tools/ops-docs` (run as `python3 tools/…`). Each appends `[name, argv[1:], cwd, GIT_DIR]` to `EVENTS` and exits 7 when `FAIL_STEP` equals its name. `tasks` answers any argv other than `["check"]` with the fixture project JSON (`{"project": {"root": <root>, "prefix": "fixture", "linked": false}}`) without logging or honouring `FAIL_STEP`. `ssh -G` prints `serveraliveinterval $SSH_INTERVAL` (default 60).
- `bin/host-budget` stub: logs, refuses (exit 1) unless argv starts `run --`, then execs the rest [r4 M1].

- [ ] **Step 1: Write `route_fixtures.py`** with the interface above.
- [ ] **Step 2: Rewrite `test_front_door.py`** on the fixture, with these cases:
  - `test_staged_paths_choose_the_gate` (same five parametrized paths and recipes as today), run as `sh .githooks/pre-commit` in the fixture after `capture_hook_recipe()`; assert `chosen`.
  - `test_push_refs_choose_the_gate`: `set_suite_refs` per case, independent of the live value. Cases: `("refs/heads/main", "origin", ("main",), "hook-pre-push-fast")`, `("refs/heads/main", "origin", ("feature",), "hook-pre-push")`, `("refs/heads/main", "origin", ("main", "feature"), "hook-pre-push")`, `("refs/heads/main", "backup", ("main",), "hook-pre-push")`, `("refs/heads/main", "origin", (), "hook-pre-push")`, `("refs/heads/*", "origin", ("feature/x",), "hook-pre-push-fast")`, `("refs/heads/*", "backup", ("main",), "hook-pre-push")`. Assert `chosen` and that `refs.actual` equals stdin byte for byte.
  - `test_one_preserves_arguments_and_records_the_run` [r4 M2]: in the fixture, `just --set one_cmd "python3 <runner.py>" test-one` with the same six arguments as today; assert the runner's argv, the row's `(target, tests) == ("test-one", 1)`, a `host-budget` event with `run --`, and that zero arguments exit nonzero.
- [ ] **Step 3: Run** `just test-one tests/test_front_door.py`. Expected: all pass against today's justfile and hooks. These cases pin existing behaviour.
- [ ] **Step 4: Prove isolation** by running the same command with `TT_FORCE=1 GITHUB_ACTIONS=true` exported in the outer shell. Expected: identical pass count.
- [ ] **Step 5:** `just test-fast`, then commit `test(front-door): run hook and focused routes in an isolated fixture checkout`.

### Task 3: Recipe split under policy

**Files:**
- Modify: `justfile` (recipes `check`, `gate`, `hook-pre-commit`, `hook-pre-push`, `hook-pre-push-fast`; new `check-hygiene`, `check-code`, `test-push`, `test-full`; variables `check_hygiene_cmd`, `check_code_cmd`)
- Test: `python/tests/test_front_door.py`

**Interfaces:**
- Consumes: `Checkout`, `BROAD` (Task 2).
- Produces: recipes with these tt targets and bodies:
  - `check_hygiene_cmd := hygiene_cmd + " && tasks check"`; `docs_check_cmd` becomes an alias of it or is replaced by it.
  - `check_code_cmd := py_check_cmd + " && " + ts_check_cmd`; `check_cmd` is removed.
  - `check-hygiene`: `{{tt}} check-hygiene -- sh -c '{{check_hygiene_cmd}}'`.
  - `check-code`: `{{tt}} check-code -- sh -c '{{check_code_cmd}}'`.
  - `test-push`: `{{tt}} test-push -- host-budget run -- sh -c '{{push_fast_cmd}}'`.
  - `test-full`: `TT_FORCE=1 just test` (untimed).
  - `check`: lines `just check-hygiene`, `just check-code` (untimed). `gate`: lines `just check`, `just test` (untimed).
  - `hook-pre-commit`: `{{tt}} hook-pre-commit -- sh -c '{{check_hygiene_cmd}}'`, then `just check-code`.
  - `hook-pre-commit-docs`: `{{tt}} hook-pre-commit-docs -- sh -c '{{check_hygiene_cmd}}'`.
  - `hook-pre-push`: hygiene under its own target, then `just check-code`, then `just test`.
  - `hook-pre-push-fast`: hygiene under its own target, then `just check-code`, then `just test-push`.

- [ ] **Step 1: Write the failing tests** in `test_front_door.py`:
  - `test_policy_off_keeps_hygiene_and_skips_broad_children[recipe]` for `hook-pre-commit`, `hook-pre-push`, `hook-pre-push-fast`, `check`, under `policy()`: exit 0; event names exactly `["ops-check", "ops-docs", "tasks"]` (no `uv`, `npm`, `npx`, `host-budget`); skipped-row targets `{"check-code"}` for `hook-pre-commit` and `check`, `{"check-code", "test"}` for `hook-pre-push`, `{"check-code", "test-push"}` for `hook-pre-push-fast`; every skipped row has `exit`, `tests`, `selection` and `slowest` all `None`.
  - `test_failure_stops_later_steps`: with no policy and `FAIL_STEP=ops-check`, each hook exits nonzero with events `["ops-check"]` only (a started `check-code` would log `uv`), and the rows are exactly one hook-target row with `exit == 7`. With no policy and `FAIL_STEP=uv`, `hook-pre-push` and `hook-pre-push-fast` exit nonzero, record a `check-code` row with exit 7, and log no `host-budget` event (the test child never started).
  - `test_enabled_hooks_run_every_child_in_order[recipe]` (Review Focus 4), no `.tt.toml`: `hook-pre-push` events are `ops-check, ops-docs, tasks, uv, uv, uv, npm, npm, host-budget, uv, uv, npm`; `hook-pre-push-fast` ends `host-budget, uv, npm`; `hook-pre-commit` is the first eight. Rows: the hook target and `check-code`, plus `test` (`hook-pre-push`) or `test-push` (`hook-pre-push-fast`), each `execution == "ran"`, reason `default`.
  - `test_test_full_records_one_forced_test_row`: under `policy()`, success gives exactly one row, `target == "test"`, reason `forced`. With `FAIL_STEP=uv` it exits nonzero, one row, `exit == 7` (Review Focus 5).
  - `test_forced_gate_records_three_forced_rows` [r6 M1]: under `policy()` with `TT_FORCE=1`, `just gate` exits 0 and the rows are exactly `check-hygiene`, `check-code`, `test` in that order, each `execution == "ran"` and `execution_reason == "forced"`, with no `check` or `gate` row. With `FAIL_STEP=npm` it exits nonzero and the failing row has `exit == 7` (Review Focus 5).
  - `test_hosted_refuses_missing_force[target]` for `ci-python`, `ci-typescript`: under `policy()` with `GITHUB_ACTIONS=true`, exit nonzero, `"TT_FORCE=1"` in stderr, no events, no rows. Then with `TT_FORCE=1` and `FAIL_STEP=uv` (Python) or `npm` (TypeScript), exit nonzero and the last row has `exit == 7`.
  - `test_nested_hosted_refuses_missing_force`: append `nested:` with body `{{tt}} outer -- just ci-python` to the fixture justfile. Under `policy()` with `GITHUB_ACTIONS=true`, `just nested` exits nonzero with `"TT_FORCE=1"` in stderr and no events, and the rows are only the `outer` row, `execution == "ran"`, nonzero exit. With `TT_FORCE=1` and `FAIL_STEP=uv`, the last row has `exit == 7`.
  - `test_focused_route_runs_under_policy_off`: under `policy()`, `test-one` records `execution == "ran"` (extend the Task 2 forwarding case or add one).
- [ ] **Step 2: Run** `just test-one tests/test_front_door.py`. Expected: the split, ordering, `test-full` and forced-gate cases fail (unknown recipes `check-code`, `test-push`, `test-full`; hook rows still single-target). The hosted-refusal, nested and focused-route cases already pass on tt v9; they pin existing behaviour.
- [ ] **Step 3: Implement the recipe split** in `justfile` as the Interfaces block says. Keep the comments above each recipe accurate to the new composition. Comment and guide prose beyond that waits for Tasks 5 and 6.
- [ ] **Step 4: Run** `just test-one tests/test_front_door.py`. Expected: all pass.
- [ ] **Step 5:** `just test-fast`, then commit `feat(justfile): split hooks into protected hygiene and broad children`. The pre-commit hook now runs the split recipe, which is a live check of it.

### Task 4: Pre-push policy warning

**Files:**
- Modify: `.githooks/pre-push` (insert after the Git local-variable clearing, before the final `exec`)
- Test: `python/tests/test_front_door.py`

**Interfaces:**
- Consumes: `Checkout.capture_hook_recipe`, `set_suite_refs`, `policy` (Task 2).
- Produces: on the full route only, the ops template block (as in nodes' `.githooks/pre-push`): evaluate `just --evaluate tt`, load the last word as a module with `importlib.machinery.SourceFileLoader`, call `execution_decision('test', read_policy(cwd), os.environ)`. On `skipped`, write to stderr exactly `pre-push: local test skipped by policy; remote full-suite coverage is not declared for this push. Use TT_FORCE=1 for deliberate local verification.` On `ValueError`, `OSError`, `IndexError` or `AttributeError`, write `pre-push: cannot inspect test execution policy: <error>` and exit 2.

- [ ] **Step 1: Write the failing tests:**
  - `test_uncovered_push_warns_only_under_policy_off`: `backup` remote, one `refs/heads/main` line. Under `policy()`: exit 0, `chosen == "hook-pre-push"`, the warning in stderr. With no policy: no warning. Under `policy()` on a covered `origin` main push: `hook-pre-push-fast` and no warning. With `TT_FORCE=1` under `policy()`: no warning.
  - `test_unreadable_policy_refuses_push`: fixture `.tt.toml` with `automatic_broad = "no"`, `backup` remote: exit 2, the `cannot inspect` message, and no `chosen` file.
  - `test_push_validates_every_ref_and_preserves_bytes` (Review Focus 1), with `set_suite_refs("refs/heads/*")`: a malformed line, a trailing blank line, and a mixed `refs/heads/main` plus `refs/tags/other` push all choose `hook-pre-push`; a deletion-only line (all-zero local oid) chooses `hook-pre-push-fast`; empty `ci_suite_refs` chooses `hook-pre-push`. `refs.actual` equals stdin in every case.
  - `test_hook_clears_git_local_environment` (Review Focus 2): `GIT_DIR` and `GIT_WORK_TREE` set in the fixture env, real recipes (no `capture_hook_recipe`), `policy()`: every non-`ssh` event's `GIT_DIR` is `None`.
  - `test_missing_keepalive_refuses_before_the_gate`: with `capture_hook_recipe()` installed, `SSH_INTERVAL=0`, URL `git@example.invalid:repo`: exit 1, no `chosen`, one `ssh -G example.invalid` event.
- [ ] **Step 2: Run** `just test-one tests/test_front_door.py -k "warns or unreadable"`. Expected: those two fail (no warning, no refusal). The other three pin existing behaviour and pass.
- [ ] **Step 3: Insert the template block** into `.githooks/pre-push` and update the hook's header comment to say the recipe now composes hygiene and broad children and that the warning names uncovered policy-off pushes.
- [ ] **Step 4: Run** `just test-one tests/test_front_door.py`. Expected: all pass.
- [ ] **Step 5:** `just test-fast`, then commit `feat(hooks): warn when policy skips an uncovered push suite`.

### Task 5: Widened workflow with durable coverage evidence

**Files:**
- Modify: `justfile` (`ci-python`, `ci-typescript`, new `ci_evidence_cmd`; the comment above `ci_suite_refs`)
- Modify: `.github/workflows/ci.yml`
- Modify: `AGENTS.md` (the Remote CI bullet only) [r4 M3]
- Create: `python/tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: `Checkout`, `BROAD`, `ROOT` (Task 2).
- Produces:
  - `ci_evidence_cmd`: fails with exit 2 unless `BELIEFS_CI_EVIDENCE_DIR` is set and absolute.
  - `ci-python`: `{{tt}} ci-python -- sh -c '{{ci_evidence_cmd}}; <non-N2 phase> --junitxml="$BELIEFS_CI_EVIDENCE_DIR/pytest.xml" && <N2 phase> --junitxml="$BELIEFS_CI_EVIDENCE_DIR/pytest-n2.xml" && {{py_check_cmd}}'`. Each phase is today's command string with only the `--junitxml` argument added.
  - `ci-typescript`: `{{tt}} ci-typescript -- sh -c '{{ci_evidence_cmd}}; (cd ts && npm test -- --reporter=default --reporter=junit --outputFile.junit="$BELIEFS_CI_EVIDENCE_DIR/vitest.xml") && {{ts_check_cmd}}'`.
  - In `ci.yml`, for each job: steps named `Prepare coverage evidence` and `Require coverage evidence`, and an `actions/upload-artifact` step pinned to `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`.
  - Test-module helpers: `workflow() -> dict`, `triggers(doc) -> dict` (reads `doc[True]` or `doc["on"]`, failing when neither exists), `github_covers(ref_glob: str, branches: list[str]) -> bool`.

Workflow contents:
- `on`: `push` with `branches: ["**"]` and no `paths`, `paths-ignore` or `tags`; `pull_request`; `workflow_dispatch`.
- Top-level `concurrency: {group: "${{ github.workflow }}-${{ github.ref }}", cancel-in-progress: true}`.
- Each job: `if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository`, `env.TT_FORCE: "1"`. `timeout-minutes` is 30 for python and 10 for typescript.
- Python `Prepare coverage evidence` (working directory `beliefs/python`): creates `$RUNNER_TEMP/beliefs-python-coverage`, appends `BELIEFS_CI_EVIDENCE_DIR=<dir>` to `$GITHUB_ENV`, and writes `module-inventory.txt`. The inventory holds `beliefs <git rev-parse HEAD>`, `atoms <git -C ../../atoms rev-parse HEAD>`, `nodes <git -C ../../nodes rev-parse HEAD>`, the eligible modules (tracked `tests/**` files whose basename matches `test_*.py` or `*_test.py`, excluding `tests/acceptance/**`), then `pyproject.toml`. TypeScript does the same in `beliefs/ts` with `beliefs-typescript-coverage`, the beliefs revision, `tests/*.test.ts` and `package.json`.
- `Require coverage evidence`, `if: always()`: `test -s` on `pytest.xml`, `pytest-n2.xml` and `module-inventory.txt` (Python), or on `vitest.xml` and `module-inventory.txt` (TypeScript).
- Upload, `if: always()`: `name: python-${{ matrix.python-version }}-coverage` or `typescript-${{ matrix.node-version }}-coverage`, `path: ${{ env.BELIEFS_CI_EVIDENCE_DIR }}`, `retention-days: 30`, `if-no-files-found: error`.

- [ ] **Step 1: Write the failing tests** in `test_ci_workflow.py`:
  - `test_ci_requires_absolute_evidence_path[target][path]`: the target is `ci-python` or `ci-typescript`; the path is unset or `relative/path`. Expect a nonzero exit and no events.
  - `test_pytest_junit_persists_both_phases_and_skip_reasons` [r6 M3, pytest] (Review Focus 3). The fixture's `bin/uv` execs `sys.executable -m pytest` with the arguments after `run --frozen pytest`. The fixture's `python/tests/` holds:
    - `test_some.py`, with one passing test and one test whose body calls `pytest.skip("certified tuple unavailable on this host: fixture")`, the runtime shape `conftest.py` produces;
    - `test_n2.py`, with one passing test.

    The evidence directory is `<root>/evidence with spaces`. Run `just --set py_check_cmd true ci-python` and expect exit 0. `pytest.xml` has the two `test_some` cases, and its skip message starts with `certified tuple unavailable on this host:`. `pytest-n2.xml` has the `test_n2` case. Rerunning with `py_check_cmd false` exits nonzero and leaves both XML files in place.
  - `test_vitest_reporter_arguments` [r6 M3, Vitest wiring]: with `ts_check_cmd` set to `true`, the logged `npm` argv is exactly `["test", "--", "--reporter=default", "--reporter=junit", "--outputFile.junit=<dir>/vitest.xml"]`.
  - `test_triggers_concurrency_and_jobs`: trigger keys exactly `push`, `pull_request` and `workflow_dispatch`; `push` equal to `{"branches": ["**"]}`; the concurrency values above. For each job: the `if` string, `TT_FORCE == "1"` and the timeout. The matrices are unchanged. The python job keeps `OPS_WORKERS`, `PYTEST_XDIST_AUTO_NUM_WORKERS`, the `VERIFIABLY_UNCERTIFIED_HOST: "1"` step env, checkouts of `verifiably/atoms` and `verifiably/nodes`, and `fetch-depth: 0` on beliefs.
  - `test_required_evidence_check_fails_when_a_file_is_missing[job][file]`: for each required file of each job, run the `Require coverage evidence` script under `sh -eu` in a fixture directory missing only that file and expect nonzero; with all files present, expect zero. Also check the upload step's `if`, `name`, `path`, `retention-days` and `if-no-files-found`.
  - `test_inventory_lists_eligible_modules_and_siblings[job]`. Commit to the fixture:
    - `tests/test_a b.py`, `tests/test_n2.py`, `tests/acceptance/test_c.py`, `tests/conftest.py` and `tests/x_fixtures.py` (Python);
    - `tests/a.test.ts` and `tests/helper.ts` (TypeScript).

    Copy the live `python/pyproject.toml` or `ts/package.json` into the fixture package, since the prepare step writes the manifest under `sh -eu`. For Python, create sibling `atoms` and `nodes` git repositories at the paths `../../atoms` and `../../nodes` resolve to. Their fixtures obey the same isolation and top-level assertions. Run the prepare script with `RUNNER_TEMP` and `GITHUB_ENV` pointing into the fixture. The exported directory lies under `RUNNER_TEMP`. The inventory lists `tests/test_a b.py` and `tests/test_n2.py` (or `tests/a.test.ts`) and none of the excluded files. For Python it also carries the `atoms` and `nodes` lines with the sibling HEADs.
  - `test_github_covers_semantics`: `github_covers("refs/heads/*", ["**"])` is true; `("refs/heads/*", ["*"])` is false; `("refs/heads/main", ["main"])` and `("refs/heads/main", ["**"])` are true; `("refs/heads/main", ["dev"])` is false. `("refs/heads/release/*", ["**"])` raises `ValueError`, because that shape is unspecified.
  - `test_live_suite_refs_are_covered_by_push_branches`: every whitespace-separated glob in the live justfile's `ci_suite_refs` value (read by regex from `ROOT / "justfile"`, not by running `just`) satisfies `github_covers` against the live `push.branches`.
  - `test_broad_targets_name_tt_targets`: every `BROAD` entry appears in the live justfile as a recipe body `{{tt}} <name> --`. When `ROOT / ".tt.toml"` exists, its `broad_targets` equals `BROAD` and passes the same check.
- [ ] **Step 2: Run** `just test-one tests/test_ci_workflow.py`. Expected: everything fails except the `github_covers` semantics, the coverage of `refs/heads/main` by today's `[main]` trigger and the broad-target names. The evidence path, reporters, triggers and steps are all missing.
- [ ] **Step 3: Implement** `ci_evidence_cmd` and the two CI recipes, and make the `ci.yml` changes. In the same commit [r4 M3]:
  - rewrite the justfile comment above `ci_suite_refs`: CI triggers on every branch, the hook's covered refs are `ci_suite_refs`, and those stay `refs/heads/main` until activation widens them;
  - rewrite AGENTS.md's Remote CI bullet to the widened triggers, the fork-only PR condition, cancellation, job-scope `TT_FORCE=1`, and the 30-day JUnit plus inventory artifacts. Keep the cost sentence.
- [ ] **Step 4: Run** `just test-one tests/test_ci_workflow.py tests/test_front_door.py`. Expected: all pass.
- [ ] **Step 5: Validate the Vitest evidence path** [r6 M3] with a focused probe that is not committed, through the documented TypeScript focused route. In a directory under the task scratch, write `pass.test.ts` and `skip.test.ts` that import nothing and use globals (`it(...)`, `it.skip(...)`). Run `just --set one_cmd "cd ts && npx --no-install vitest run" test-one --root <dir> --globals --reporter=default --reporter=junit --outputFile.junit=<dir>/vitest.xml`. Expected: a recorded `test-one` row, and XML with two testcases, one with `<skipped`. Attach the XML to the task with a caption, and note the probe as the Vitest executed-plus-skipped validation.
- [ ] **Step 6:** `just test-fast`, then commit `ci: run every branch with forced tt and durable coverage evidence`.

### Task 6: Guides

**Files:**
- Modify: `AGENTS.md` (Gates section)
- Modify: `justfile` (header comment)
- Modify: `python/README.md` (Gates paragraph)
- Modify: `.githooks/pre-commit` (header comment)

- [ ] **Step 1: Rewrite AGENTS.md Gates.** Keep it within the ops-docs budget; `python3 tools/ops-docs check` enforces it. State-independent where possible:
  - **Policy.** It comes from `.tt.toml` at the Git top level, read by `tools/tt`. If the file is absent, policy is enabled. The broad targets it lists skip under `automatic_broad = false`, unless `TT_FORCE=1` is set.
  - **Routes.** `check-hygiene` and `test-one` are protected. `check-code`, `test`, `test-fast` and `test-push` are broad. `check` and `gate` compose them. Describe what each hook runs.
  - **Evidence.** `just test-full` is suite evidence: its forced `test` row. `TT_FORCE=1 just gate` is full-gate evidence [r6 M2]: the consecutive `check-hygiene`, `check-code` and `test` rows of one invocation, with the same `rev`, `dirty` and `content`, each `execution: ran`. Under policy-off that needs `TT_FORCE=1`, and an unforced enabled run is equally valid. A skip or a hook completion is never evidence.
  - **Certified host.** List the certified-host routes from the spec's section of that name, word for word in substance, and keep the duty to report the exact mismatch.
  - **Timing series.** Hook targets now time hygiene only. `check` is untimed. `check-hygiene`, `check-code` and `test-push` are new series.
  - **Current state.** Any line that must state the current policy or covered refs states the pre-activation state: policy enabled, `refs/heads/main`.
- [ ] **Step 2: Rewrite the justfile header** and `python/README.md`'s `check` sentence to match. `check` is now `check-hygiene` plus `check-code`, and the gate is no longer one recorded run. Rewrite `.githooks/pre-commit`'s header state-independently: its claim that skipped checks "still run at the next code commit, at push, and in CI" becomes "run where policy allows, and in CI".
- [ ] **Step 3: List the state lines.** Note on beliefs-067a8d every line written in Tasks 5 and 6 that states the current policy or covered refs, by file and quoted text. Task 9 edits exactly those lines.
- [ ] **Step 4: Run** `just test-one tests/test_designs_corpus.py tests/test_check_guide.py tests/test_front_door.py` and `python3 tools/ops-docs check`. Expected: pass.
- [ ] **Step 5:** `just test-fast`, then commit `docs: describe the split gates, policy and certified-host routes`.

### Task 7: Final review, integration and publication

- [ ] **Step 1: Final whole-branch review.** Dispatch a fresh read-only reviewer on `main..design/067a8d-test-policy`, using this plan and the spec at their frozen revisions. Save the returned report as `final-review-report.md` in the plan workspace, with the reviewer's identity. Record the `review: impl round 1 — …` note before acting. Then run corrective rounds as the global Decisions rule says. Defer Minors to the ledger as `minor (deferred)`.
- [ ] **Step 2: Integrate** into local main from the main checkout: `git merge --no-ff design/067a8d-test-policy`. The personal profile allows a local merge of a reviewed branch. From here on, task commands run in the main checkout: move the claim there first with `tasks start beliefs-067a8d`. Record on beliefs-067a8d exactly `policy: enabled at <merge commit time, RFC3339 UTC> revision <merge full sha>`. That note starts the split-hook timing series.
- [ ] **Step 3: Prepare the publication packet** as a task attachment `publication-packet.md`, holding:
  - the exact commit to push (the Step 2 merge SHA), the refspec `<merge-sha>:refs/heads/main`, a statement that the `tasks/*.md` record commits made after it stay local until a later approved push, everything the push publishes (`git log --oneline origin/main..<merge-sha>` and `git diff --stat origin/main <merge-sha>`, which today include unpushed commits such as the ops-check v16 and tt v9 vendoring), the `ci.yml` diff, and the delivery revisions (ops design `469140a`, tt v9);
  - the runner class (`ubuntu-latest`, standard) and the timeouts (30 and 10 minutes);
  - the visibility of beliefs, atoms and nodes, rechecked now with `gh api repos/verifiably/<repo> --jq .visibility`;
  - the organization's Actions spending-limit state, if readable without a write. Otherwise, the explicit deviation from the task body;
  - the hosted-acceptance criteria. The per-job counts, module inventory, capability-omission list, wholly skipped modules and sibling revisions are marked pending, with run 41077923374's counts given for reference and their limits stated;
  - the rollback route.
- [ ] **Step 4: Ask for publication approval.** Park beliefs-067a8d with `--waiting-on user --reason approval`. The park text names the packet and states that approval covers only `git push origin <merge-sha>:refs/heads/main`.
- [ ] **Step 5:** After approval, confirm `git log --oneline origin/main..<merge-sha>` still matches the packet (origin may have moved; a mismatch means a new packet), then `git push origin <merge-sha>:refs/heads/main` and note the push and the run ID. Hosted acceptance is judged on that SHA's run.

### Task 8: Hosted acceptance and the activation packet

- [ ] **Step 1: Wait** for the run's completion with `gh run watch <id>`, in the background with a 45-minute timeout. A cancelled run is unverified: rerun it with `gh workflow run` only on a new approval.
- [ ] **Step 2: Download the artifacts** into `$WORK_ROOT/beliefs/beliefs-067a8d/hosted-1/` with `gh run download <id>`. Note the directory.
- [ ] **Step 3: Assess each matrix job** with a scratch script kept in that directory, not committed. It reads the XML with `xml.etree` and checks each item of the spec's Hosted acceptance:
  - a nonzero executed count in each phase;
  - no failures or errors;
  - every inventory module present in its expected XML (`test_n2.py` in `pytest-n2.xml`), with absent modules listed;
  - the capability omissions, by test ID: skips whose message starts with `certified tuple unavailable on this host:`;
  - the other skips grouped by reason and compared with Task 1's baseline SKIPPED reasons, with new reasons listed;
  - wholly skipped modules [r6 M4];
  - the sibling revisions from the inventory.

  Attach the script and its output (`hosted-1-assessment.txt`) to beliefs-067a8d.
- [ ] **Step 4: Settle the result.** Any failing criterion leaves policy on. Its fix is a new policy-enabled change, reviewed, and pushed only on a fresh approval like Task 7's. Repeat Steps 1 to 3 on that run.
- [ ] **Step 5: Build the activation commit, unintegrated.** This follows plan round 1 Ruling I1's reading of spec step 7: the packet names the exact commit, and approval authorizes integrating it into the registered main checkout. In the worktree, on `design/067a8d-test-policy` (whose own Git top level is separate, so the registered main checkout's policy is untouched):
  - write `.tt.toml` with the exact policy text;
  - set `ci_suite_refs` to `refs/heads/*`;
  - refresh Task 6 Step 3's state-line list against the tree with `git grep -n -e "refs/heads/main" -e "origin/main" -e "policy enabled" -e "policy is enabled" -- AGENTS.md justfile python/README.md .githooks`, note the additions, and edit the union.

  Before committing, run its focused checks from the physical path, since its own hooks skip `check-code` and `test-push`: `just test-one tests/test_front_door.py tests/test_ci_workflow.py tests/test_designs_corpus.py tests/test_check_guide.py`, plus `TT_FORCE=1 just check-code`. The live `.tt.toml` branch of `test_broad_targets_name_tt_targets` and the `refs/heads/*` coverage case now run. Expected: pass. Commit `chore(policy): activate tt policy-off with remote suite coverage`. Its SHA is the activation commit.
- [ ] **Step 6: Prepare the activation packet** (`activation-packet.md`, attached). It holds:
  - the publication packet's pending items, populated from the run;
  - a verdict for each acceptance criterion;
  - visibility and runner class, rechecked;
  - the capability-omission list, which becomes the guidance list for focused certified runs;
  - the exact activation commit (Step 5's SHA) and its diff, and the integration it authorizes: a `--no-ff` merge of exactly that commit into main, pushed by refspec as the merge SHA. Between the published merge and that merge, main may gain only `tasks/*.md` record commits; list them;
  - the latency and halt reinventory (`tasks list --tag test-latency`, `tasks list --tag halt`);
  - the rollback route.
- [ ] **Step 7: Ask for activation approval.** Park beliefs-067a8d with `--waiting-on user --reason approval`, naming the packet and the activation SHA. Approval there covers integrating and pushing that commit only. On refusal, reset the worktree branch to its pre-activation tip (the commit is unpushed and unmerged) and note it. On requested changes, rebuild the commit and present a new packet naming the new SHA.

### Task 9: Activation and post-activation verification

- [ ] **Step 1: Integrate** after approval: from the main checkout, first require `git diff --name-only <published-merge-sha> HEAD` to list only `tasks/*.md` files. Anything else (another lane merged meanwhile) stops the step: rebuild the activation commit if needed and present a new activation packet. Then `git merge --no-ff <activation-sha>`. Confirm that the merge's diff from main's previous tip equals the activation commit's diff, then `git push origin <merge-sha>:refs/heads/main`. Note the merge SHA, its time and the run ID.
- [ ] **Step 2: Verify from the registered main checkout**, recording each result on beliefs-067a8d:
  - `just test-one tests/test_front_door.py -k test_full` passes and records a `test-one` row with `execution: ran`. This covers the forced-failure fixture through `test-one`;
  - the activation push's hooks recorded `check-code` and `test-push` as `skipped`, with null `exit`, `tests`, `selection` and `slowest`. Read this from the shared tt log, identifying the push's rows as the `hook-pre-push-fast`, `check-code` and `test-push` rows whose `rev` is the pushed merge SHA (Task 8 Step 5's own pre-commit row also shows a skipped `check-code`);
  - the activation push's hosted run meets the Task 8 criteria. Rerun the Task 8 Step 3 script into `hosted-2/` and attach its output.
- [ ] **Step 3: Record the activation** on beliefs-067a8d:
  - the activation revision and time;
  - the latency reinventory (none known);
  - a note on ops-39bff6, a closed record, with the beliefs status;
  - a link to ops-56aab7, the regret review on 2026-11-28, in a note on both tasks rather than a duplicate.

  Attach the downloaded artifacts or their derived counts under the retained-item rules, since the artifacts expire before that review.
- [ ] **Step 4: Close out:**
  - run `tt-report`;
  - account for the retained items (the worktree, `$WORK_ROOT/beliefs/beliefs-067a8d/`, the plan workspace ledgers);
  - remove the worktree by the global removal checks;
  - run `tasks done beliefs-067a8d` with the done note, recording the focused scope, the mandatory checks, the skipped broad work and the remote evidence as separate items.

Rollback, if needed: set `automatic_broad = true` and `ci_suite_refs := "refs/heads/main"`, and update the same guide lines. Then record `policy: enabled at <landed RFC3339-UTC> revision <full-sha>` on beliefs-067a8d. Publishing the rollback is gated like any push.
