# Beliefs test execution policy adoption

Status: proposed for user review. Task: beliefs-067a8d. This document authorizes no
implementation, workflow publication, push or policy-off activation. The
implementation plan follows user approval of this frozen design.

## Intent and authority

The ask behind this work comes from the session that filed ops-8bfa85
(codex:01a1874f-c2d8-7320-ae81-7114e37e343f, whose human turns nodes-6fde14's
origin note records): reduce development-host contention
and repeated broad verification, keep focused tests during implementation, and
move routine regression suites to hosted CI. The user approved the shared design
and plan there. An agent filed this adoption task, so every project-specific choice
below is the designer's call, open to correction at review. None of them adds a
human decision.

Shared authority is ops-8bfa85's approved design
(`docs/specs/2026-10-29-test-execution-policy-design.md` in ops, revision
`1ce9abe`) and its implementation plan, read through `tasks doc`. The ops pilot
(ops-68729d) is done, with accepted hosted evidence before and after activation.
lore-fdbe86 has delivered the policy-aware instructions. nodes-6fde14 is the
closest completed adoption: it has the same two-package layout and is reused
here wherever beliefs does not differ.

This is development infrastructure. It changes no kernel behaviour, frozen cut,
conformance oracle, contract or guarantee row. The two plan obligations in
AGENTS.md (the `root.py` atoms-import boundary and the recent-cut acceptance row)
cover discharged conformance cuts. No cut is discharged here, so neither applies.

## Current evidence (2026-10-31)

- `tools/tt` is version 9. It already validates the checkout-local policy,
  protects the focused and hygiene targets, records skips with null outcomes, and
  refuses a hosted skip without explicit force. The task body's version-7
  observation is stale. No `.tt.toml` exists, so automatic broad execution is enabled.
- `test-fast` runs the non-N2 Python suite under xdist with `loadgroup` plus
  Vitest `--changed`. `test` adds standalone N2 and the full TypeScript suite.
  `test-one +args` forwards argv intact to `one_cmd`, and an override serves Vitest.
  `test`, `test-fast`, `test-one` and both push recipes run under
  `host-budget run`, which supplies the `OPS_WORKERS` that N2 requires.
- `check`, `hook-pre-commit` and both push recipes embed one opaque
  `check_cmd`: ops-check, ops-docs check, Ruff check, Ruff format check, Pyright,
  tsc, Biome and `tasks check`. `hook-pre-commit-docs` runs hygiene and
  `tasks check` only. `push_fast_cmd` (non-N2 Python plus the full TypeScript
  suite) differs from `test-fast`. `ci_remote = "origin"` and
  `ci_suite_refs = "refs/heads/main"`.
- `python/tests/test_front_door.py` pins the hook routing and the `test-one`
  forwarding. Its fixtures inherit `os.environ` and run `git init` with the
  host's Git configuration. Both conflict with the current subprocess and Git
  fixture rules, so the change that touches these tests rebuilds them.
- CI (`.github/workflows/ci.yml`) runs only on `main` pushes and on every PR.
  It runs Python 3.11/3.13 and Node 20/24 on `ubuntu-latest` with pinned
  actions. The Python job checks out the public `verifiably/atoms` and
  `verifiably/nodes` at their default branches as editable sibling sources,
  fetches beliefs with full depth for the conformance guards, sets
  `OPS_WORKERS=4`, `PYTEST_XDIST_AUTO_NUM_WORKERS=4` and
  `VERIFIABLY_UNCERTIFIED_HOST=1`, and runs `just ci-python`. It has no explicit
  force, no concurrency group, no manual dispatch and no job timeout.
- Hosted run 41077923374 (main, 2026-10-30), from its logs: in each Python job,
  the non-N2 phase reported 6026 passed and 328 skipped; N2 reported 46 passed.
  Each TypeScript job reported 155 passed in 7 files. Job wall times: Python 3.11
  14.5 min, Python 3.13 8.2 min, each TypeScript job 0.3 min. Recent main runs
  took 10.7–15.1 min. The log's `-q` output does not give skip reasons. How many
  of the 328 skips are `CapabilityUnavailable` conversions is unmeasured.
- `tests/acceptance` is excluded from every pytest route by `addopts` and runs
  only through the cut runners. This adoption leaves it unchanged; it is not a
  new omission.
- With the profile account, the GitHub API reports `verifiably/beliefs` as public
  with admin access. Under current GitHub documentation, standard hosted runners
  are free for public repositories, so the private allowance and no-paid-overage
  setting do not apply while the repository stays public on standard runners.
  Visibility and runner class are rechecked at activation. No billing setting changes.
- No open task in this project is tagged `test-latency` or `halt`. This is
  reinventoried at activation.

Local executed runs in this host's shared tt log, read with ops `tt-report`
(`--project beliefs --since 2026-10-01 --all`, read 2026-10-31):

| Target | Runs | Median s | p90 s |
| --- | ---: | ---: | ---: |
| hook-pre-commit | 232 | 32.3 | 40.6 |
| check | 82 | 34.9 | 57.9 |
| test-fast | 134 | 90.3 | 168.2 |
| test | 18 | 266.6 | 381.1 |
| hook-pre-push-fast | 15 | 135.3 | 181.8 |
| hook-pre-commit-docs | 586 | 1.9 | 2.5 |
| test-one | 491 | 7.6 | 56.3 |

These are invocation wall times under mixed host load. They are not uncontended
measurements or projected savings. Hygiene and focused runs remain after adoption,
so the actual saving has to be measured afterwards.

## Approaches

1. **Adopt tt policy at the existing command boundaries, keep both matrices and
   the sibling checkouts, extend the existing workflow (selected).** This follows
   the shared contract and the nodes adoption. It adds one broad push child for
   beliefs' distinct `push_fast_cmd`.
2. **Keep Ruff and Pyright on the always-run path (rejected).** Pre-commit cost
   is mostly Pyright, and leaving it local would preserve most of the per-commit
   wait. The shared contract classifies lint and typecheck as broad. The cost
   is stated under the tradeoffs below.
3. **Drop the Python 3.11 job, or N2 from CI, to shorten hosted time
   (rejected).** That removes established coverage, and public hosted compute is
   free. Reducing N2's cost stays with beliefs-f64cf1.

## Command contract

Command strings, test selection, `host-budget` wrapping and argument forwarding
stay unchanged, with one exception: the CI routes add persistent JUnit output,
specified below. Every executed check still goes through the vendored
`tools/tt`, which this change does not edit.

| Route | Classification | Contract |
| --- | --- | --- |
| `test-one +args` | protected | Unchanged: `one_cmd` and the Vitest override, argv intact, under `host-budget run`; at least one argument. |
| `test-fast` | broad | Unchanged `fast_cmd` under `host-budget run`. |
| `test-push` | broad | New: the existing `push_fast_cmd` under `host-budget run`, recorded under its own target. |
| `test` | broad | Unchanged `test_cmd` (non-N2, N2, TypeScript) under `host-budget run`. |
| `test-full` | protected | New untimed alias `TT_FORCE=1 just test`. Only the inner `test` row is recorded, with reason `forced`. |
| `check-hygiene` | protected | New: ops-check, ops-docs check, `tasks check`. Always runs. |
| `check-code` | broad | New: the existing `py_check_cmd` then `ts_check_cmd` (Ruff check, Ruff format check, Pyright, tsc, Biome). |
| `check` | untimed alias | `just check-hygiene` then `just check-code`, as sequential recipe lines. |
| `gate` | untimed alias | `just check` then `just test`. |
| `setup` | protected | Unchanged. |
| `hook-pre-commit` | protected | Times hygiene once under its own target, then runs `just check-code`. |
| `hook-pre-commit-docs` | protected | Unchanged hygiene path, now the same command as `check-hygiene`. |
| `hook-pre-push` | protected | Times hygiene once, then `just check-code`, then `just test`. |
| `hook-pre-push-fast` | protected | Times hygiene once, then `just check-code`, then `just test-push`. |
| `ci-python`, `ci-typescript` | broad | The complete package suite and checks, as now, plus JUnit evidence. They are broad so that a hosted invocation missing `TT_FORCE=1` refuses instead of passing as a skip. |
| `mm30-recreate`, cut runners | untouched | Outside tt's broad list. They measure and audit; they are not regression gates. |

`host-budget` stays inside tt's child command, so a policy skip launches neither
`host-budget` nor its children and holds no budget slot. Sequential recipe lines
stop at the first failure, as `&&` does now.

After accepted hosted verification and explicit activation approval, commit:

```toml
automatic_broad = false
broad_targets = ["test", "test-fast", "test-push", "check-code", "ci-python", "ci-typescript"]
```

Missing policy means enabled. Malformed policy is an error, even under force. A
skip is a decision. It never counts as a passing suite or a performance sample.

Three timing series change meaning. Hook targets now measure the hygiene portion
only. `check` stops being timed. `check-hygiene`, `check-code` and `test-push`
start new series. None of them is compared with, or spliced onto, the historical
whole-hook or `check` medians in the table above.

### Pre-push coverage routing

Adopt ops `templates/githooks/pre-push`'s policy warning. On the full route under
policy-off, the hook loads the configured tt module and asks
`execution_decision('test', read_policy(cwd), environ)`. If that returns
`skipped`, it warns that no remote suite coverage is declared for this push and
names `TT_FORCE=1`. If the policy cannot be read, it exits 2. It has no TOML
parser of its own. Keep input validation, deletion handling, byte-preserving ref
forwarding, the SSH keepalive refusal and Git local-variable clearing.

`ci_suite_refs` becomes `refs/heads/*` only in the activation commit, after the
widened workflow is published and its hosted run is accepted. Until then it stays
`refs/heads/main`, which the current workflow already covers. Beliefs has no
release workflow and pushes no tags, so no tag pattern is declared.

## Hosted verification

Extend the existing `ci.yml`. Do not add a second workflow.

- Triggers: `push` on branches `["**"]` with no path filters, `pull_request`,
  and `workflow_dispatch`. Each job has the condition
  `github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository`,
  so a same-repository PR launches no duplicate suite jobs and a fork PR still runs.
- Concurrency: `group: ${{ github.workflow }}-${{ github.ref }}`,
  `cancel-in-progress: true`. A cancelled revision is unverified, not passed.
- `TT_FORCE: "1"` at job scope in both jobs, so nested wrapper processes inherit it.
- Keep both matrices, the pinned actions, the frozen installs, the atoms and nodes
  sibling checkouts at their default branches, `fetch-depth: 0`, both worker
  variables and `VERIFIABLY_UNCERTIFIED_HOST=1`.
- `timeout-minutes: 30` on the Python jobs, about twice the slowest observed run.
  10 on the TypeScript jobs. Both bounds appear in the activation packet.

### Durable coverage evidence

This follows the nodes design. A shell step creates an evidence directory under
`RUNNER_TEMP` and exports `BELIEFS_CI_EVIDENCE_DIR`. `ci-python` and
`ci-typescript` require that variable to be an absolute path and fail early
otherwise. The pytest non-N2 phase writes `pytest.xml` and the N2 phase writes
`pytest-n2.xml`, both through `--junitxml`. Vitest adds the default and junit
reporters with an explicit junit output file. The local `test`, `test-fast`,
`test-push` and `test-one` commands keep their current flags.

A pre-run step writes a module inventory: revision, tracked test files and the
package manifest. An always-run step then requires the expected XML and inventory
files, and a pinned `upload-artifact` step uploads them with a per-package,
per-version name, 30-day retention and `if-no-files-found: error`. A failed suite
keeps its failure status even when the upload succeeds.

From the downloaded artifacts, activation records per matrix job: executed,
passed, failed and skipped counts per phase; skipped tests grouped by reported
reason, with `CapabilityUnavailable` conversions counted separately; wholly
skipped modules; and any eligible module absent from JUnit. An absent module with
no explanation blocks acceptance. Before the full hosted run, the plan validates
the evidence path on one executed case and one skipped case in each runner,
including the missing-artifact case.

## Certified-host coverage under policy-off

A green hosted run is evidence about the portable tests and never about the
capability-dependent ones (AGENTS.md, Gates). Today the local full gate is what
runs those tests on the certified tuple. With `test` skipped by policy, that
routine local run stops, and the shared design accepts the gap explicitly.

Policy-off leaves these routes for certified evidence. Guidance names each one:

- **Focused.** A change that touches capability-dependent behaviour (the
  `root.py` atoms boundary, durability, publication persistence, or any test
  that can raise `CapabilityUnavailable`) runs the relevant tests with
  `just test-one` on the certified tuple, where that exception still fails.
- **Deliberate full.** `just test-full` (or `TT_FORCE=1 just test`) runs every
  local phase, N2 included. It is used when the change warrants the whole
  certified suite, and when a record must cite a full local gate.
- **Conformance records.** A results record or freeze that cites a full-gate run
  cites a forced run with its recorded target and reason. A policy skip or a hook
  completion is never evidence that a suite passed. Cut runners and
  `tests/acceptance` are unchanged.

The AGENTS.md sentence "Run the Python suite on the certified kernel and volume
tuple or report the exact mismatch" is rewritten to these routes. The
`CapabilityUnavailable` fail-closed semantics are unchanged.

## Tradeoffs proposed for approval

- Routine Ruff, format, Pyright, tsc and Biome failures can go unnoticed until the
  next push's completed CI run. Freeze pins hold modulo formatting, so a format
  failure cannot invalidate a pin, but it can fail CI after the fact.
  `just check-code` (forced when policy-off) stays available for deliberate use.
- Regressions in unrelated non-N2 tests and in N2 surface remotely, after the
  push. Local work does not block on missing CI, and a cancelled, queued or
  failed run leaves its revision unverified.
- Capability-dependent regressions outside the focused tests a change runs are
  caught only by a later deliberate `test-full` on the certified host.

## Verification and activation sequence

1. After design approval, write and freeze the implementation plan for user
   review. Policy stays enabled through preparation and the first hosted run.
2. Execution Setup checks the shared delivery state again, then runs `just test`
   as the full baseline from the hydrated worktree and records its test counts
   and failures.
3. Implement the recipe split, the hook warning and the workflow, each RED to
   GREEN through `just test-one`. Rebuild `test_front_door.py`'s fixtures with
   key-by-key environments, a temporary `HOME`, `GIT_CONFIG_GLOBAL` and
   `GIT_CONFIG_NOSYSTEM`, and assert each fixture's top level and git-dir before
   its first write. Using isolated fixture policy files, prove that: hygiene
   survives policy-off; a skipped child never spawns and logs a null outcome;
   `test-one` still forwards argv; `test-full` records exactly one forced `test`
   row and propagates failure; a hosted missing-force call refuses directly and
   nested; the uncovered-push warning fires only under policy-off. Workflow
   contract tests pin the triggers, the fork-only PR condition, the concurrency
   key, job-scope force, timeouts, sibling checkouts and evidence upload. Never
   disable the real checkout's policy to test adoption.
4. Update AGENTS.md's Gates section, the justfile's header comments and any
   README text that names these commands: policy source, focused route, force
   command, CI refs, certified-host routes and the timing-series discontinuity.
   README.md and docs/ are test inputs, so the plan runs the tests that read them.
5. Present the reviewed implementation and an activation packet: the exact
   commit and refs, the workflow diff, delivery revisions, runner class and
   timeouts, public status and billing applicability, the per-job test, skip and
   module inventory, and rollback. Obtain explicit approval before any push,
   workflow run or account write. The ops pilot's approval does not transfer.
6. Push only the approved policy-enabled revision and inspect the completed hosted
   results. With coverage accepted and explicit conditional approval, commit
   `.tt.toml` and the `ci_suite_refs` widening, integrate them, push the
   activation, and inspect that run's forced execution too. If hosted setup
   fails, policy stays on.
7. When the hook split integrates, record exactly
   `policy: enabled at <RFC3339-UTC> revision <full-sha>`. At activation, record
   the actual revision and time, reinventory latency incidents (none are known),
   report status to ops-39bff6, and link the shared regret review ops-56aab7
   (deferred to 2026-11-28) rather than filing a duplicate.

Rollback sets `automatic_broad = true`, restores the documented local cadence,
records the same enabled-floor note with the rollback's actual landed timestamp
and SHA, and reports the remote state. Publishing a rollback is externally gated
too.

## Builder freedom and limits

The builder chooses small just and shell details, fixture placement, evidence
file names within this contract, and attachment names. No new dependency,
selector engine or second workflow is needed. Changing the binary policy,
removing a focused check, dropping a matrix entry or a sibling checkout, or
claiming certified coverage from a hosted run needs a new decision.

Sources: the current justfile, `.githooks/`, `ci.yml`, `python/pyproject.toml`,
`python/tests/uncertified_host.py` and `test_front_door.py`; hosted run
41077923374's logs; `tt-report`; the ops-8bfa85 design and plan; the ops-68729d
completion; the nodes-6fde14 design and its adopted justfile, hook and workflow;
ops `templates/githooks/pre-push`;
[GitHub billing](https://docs.github.com/en/actions/concepts/billing-and-usage) and
[concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency).
