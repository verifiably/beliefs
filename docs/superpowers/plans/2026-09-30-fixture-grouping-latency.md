# Fixture Grouping Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the unchanged non-N2 fast selection to a `tt` median of at most 90 seconds while retaining the complete certified gate under 300 seconds.

**Architecture:** Mark tests that use module- or class-scoped fixtures using pytest's full static fixture closure, then let pytest-xdist `loadgroup` keep those consumers on one worker. Leave other tests as separate scheduling units. Admit the scheduler only after an instrumented 16-worker pilot beats the worksteal baseline for total worker time, recorded wall time, and scoped-fixture setup; then run repeated fast and full gates and the incident's post-commit verification.

**Tech Stack:** Python 3.13 on the certified host, pytest 9, pytest-xdist 3.8.0, just, `host-budget`, `tools/tt`, `tt-latency`.

**Spec:** [Fast-suite fixture grouping](../specs/2026-09-30-fixture-grouping-latency-design.md)

## Global Constraints

- Work in `.worktrees/test-fast-remedy`, the existing locked worktree for `beliefs-04d696`. Run commands there. This plan is written from the main checkout's path convention; file references below include the worktree prefix where shown outside command blocks.
- Preserve every existing selected test, assertion, skip, certified-host capability check, frozen conformance-cut body, and the two independent environment captures. Keep N2 in its separate serial Python phase and TypeScript selection unchanged.
- The justfile's `py_fast_cmd` feeds `test-fast`, the non-N2 phase of `test`, and the pre-push fast gate. Change that one command; do not add a dependency or a second scheduler setting.
- `host-budget run` must grant 16 xdist workers during comparable performance runs. Capture host load and audio state; do not overlap measured runs with other long recorded runs. Use `just test-one` for focused pytest checks, `just test-fast` before the implementation commit, and `just check` before closing the task.
- `tt` times include host-budget, `uv run`, and TypeScript startup. The fixed all-durations worksteal baselines are 1,209.7 reported worker-seconds and 93.925 seconds in `tt`; the plain `tt` baseline is 93.984 seconds. The fast limit is 90 seconds, the full-gate limit is 300 seconds.
- `tt-latency verify` requires three successful, uncontended `test-fast` runs started strictly after the remedy commit timestamp. The incident currently names one host; verify separately on every host named in any later breach note. Include its output in `tasks done`.

## Review Focus

- A function fixture hides a module fixture in its transitive closure: Task 1's temporary collection probe checks `names_closure`, and the permanent assertions exercise the real `pair` and `minted` fixtures.
- A fixture is overridden closer to a test: Task 1 reads the last applicable `FixtureDef` in `name2fixturedefs`; the temporary probe checks both a function-scoped override and module-over-class precedence.
- A dynamic `request.getfixturevalue("production_pair")` is invisible to static closure discovery: Task 1 makes the existing evaluation test request it directly and checks the resulting file group.
- A test without scoped fixtures is pulled into a whole-file group by accident: Task 1 checks an unmarked test beside replay's grouped tests and a session-only contract test.
- Xdist rewrites node IDs before this hook adds markers, so `loadgroup` ignores them: Task 1 gives the hook `tryfirst=True`, then runs real pair consumers with `-n 2 --dist=loadgroup -vv --durations=0` and confirms one worker and one setup.

---

### Task 1: Implement grouping and run the instrumented pilot

**Files:**

- Modify: `.worktrees/test-fast-remedy/python/tests/conftest.py` (collection hook)
- Modify: `.worktrees/test-fast-remedy/python/tests/test_replay.py`, `.worktrees/test-fast-remedy/python/tests/test_boundary.py`, `.worktrees/test-fast-remedy/python/tests/test_typing_exercise.py`, `.worktrees/test-fast-remedy/python/tests/test_base_contract.py`, `.worktrees/test-fast-remedy/python/tests/test_evaluation.py` (assertions in existing tests; no new test IDs)
- Modify: `.worktrees/test-fast-remedy/justfile` (`py_fast_cmd` and scheduler comment)
- Temporary, then remove: `.worktrees/test-fast-remedy/python/tests/test_scope_group_probe.py`
- Evidence: `beliefs-04d696` via `tasks note`; ignored `.work/fixture-grouping/` logs

**Interfaces:**

- Consumes: pytest's `item._fixtureinfo.names_closure`, `name2fixturedefs[name][-1].scope`, and xdist's `xdist_group` mark. These fixture-info members are private pytest API; real consumer tests pin their behavior at the installed version.
- Produces: `pytest_collection_modifyitems(items)` that marks a module fixture consumer with its file node ID, a class-only consumer with its class node ID, and no other item. The hook runs before xdist's collection hook. `py_fast_cmd` uses `--dist=loadgroup` with the existing `-n auto --ignore=tests/test_n2.py`.

- [ ] **Step 1: Start the first child and refresh the baseline.** Run `tasks start beliefs-5cc080` and record `git rev-parse HEAD` as the pre-pilot revision for a possible rollback. Run `host-budget show` and `host-load --section session`; require 16 granted workers and no competing long run. Make `.work/fixture-grouping/`, then run `PYTEST_ADDOPTS='--durations=0' just test-fast > .work/fixture-grouping/worksteal.log 2>&1`. Read its final verdict, `tt` record, aggregate worker-seconds, each scoped-fixture file's setup rows, and top ten files by worker time. The fixed design baselines remain the admission thresholds; this fresh run identifies changes in host load or suite inventory before an experiment. Diagnose any baseline failure before changing code.

- [ ] **Step 2: Write failing checks in existing tests.** In `test_replay.py::test_a_replay_runs_in_a_fresh_scratch_root_with_an_equal_recipe`, add `request` and assert `request.node.get_closest_marker("xdist_group").args == ("tests/test_replay.py",)`. In `test_boundary.py::test_the_boundary_mints_a_run_over_the_held_fixture`, assert the group is `tests/test_boundary.py`. In `test_typing_exercise.py::TestTypeRecord::test_a_well_formed_record_types`, assert the group is `tests/test_typing_exercise.py::TestTypeRecord`. In `test_replay.py::test_definition_agreement_is_none` and `test_base_contract.py::TestTheShippedContract::test_it_loads`, add `request` and assert that the group marker is absent. Keep all existing assertions. The two negative cases cover function-only and session-plus-function fixture closure.

```python
# In the replay pair consumer; use the corresponding expected group above
# in the minted and typed consumers. Keep their existing behavior assertions.
mark = request.node.get_closest_marker("xdist_group")
assert mark is not None and mark.args == ("tests/test_replay.py",)

# Add to the existing function-only and session-fixture consumers.
assert request.node.get_closest_marker("xdist_group") is None
```

- [ ] **Step 3: Expose the one dynamic module fixture as a static dependency.** In `test_evaluation.py::test_v7_gather_never_selects_a_production_verification`, replace `request.getfixturevalue("production_pair")` with a direct `production_pair` parameter and pass it to `_production_verification`. Add `request` only to assert group `tests/test_evaluation.py`. The fixture is already imported into this module, and the test requests it unconditionally, so the produced verification is unchanged. This makes its module scope visible in `names_closure`.

```diff
-def test_v7_gather_never_selects_a_production_verification(request, tmp_path):
+def test_v7_gather_never_selects_a_production_verification(production_pair, request, tmp_path):
     from domain_facet_fixtures import over_kwargs
     from test_relocation import _writer
     from test_verify import _production_verification
 
     from beliefs.verify import publication_node
 
-    production = _production_verification(request.getfixturevalue("production_pair"))
+    mark = request.node.get_closest_marker("xdist_group")
+    assert mark is not None and mark.args == ("tests/test_evaluation.py",)
+    production = _production_verification(production_pair)
```

- [ ] **Step 4: Confirm red before implementing.** Run `just test-one tests/test_typing_exercise.py::TestTypeRecord::test_a_well_formed_record_types`. It must fail because no `xdist_group` mark exists yet, after the typed fixture succeeds. If it fails for another reason, diagnose that reason before proceeding.

- [ ] **Step 5: Add the collection hook in `python/tests/conftest.py`.** Add this near the existing pytest hooks; keep marker addition unconditional so a focused `test-one` run without xdist checks it too:

```python
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        info = getattr(item, "_fixtureinfo", None)
        if info is None:
            continue
        scopes = {
            definitions[-1].scope
            for name in info.names_closure
            if (definitions := info.name2fixturedefs.get(name))
        }
        if "module" in scopes:
            group = item.nodeid.split("::", 1)[0]
        elif "class" in scopes:
            group = item.nodeid.rsplit("::", 1)[0]
        else:
            continue
        item.add_marker(pytest.mark.xdist_group(group))
```

  `names_closure` includes dependencies of function-scoped fixtures. The last definition is pytest's closest applicable override. The module branch wins when both scopes are present. Stable file/class node IDs give every worker the same group name. Xdist 3.8 appends the group to node IDs during its own collection hook, which is why `tryfirst=True` matters.

- [ ] **Step 6: Check real consumers and a temporary closure probe.** Run one focused `just test-one` command selecting all six edited checks; all must pass. Create a temporary `test_scope_group_probe.py` under `python/tests` with the following fixture cases, run `just test-one tests/test_scope_group_probe.py`, then remove the temporary file before the full pilot. This checks transitive closure and precedence absent from the permanent suite without adding a selected test to the fast gate.

```python
import pytest

@pytest.fixture(scope="module")
def module_value():
    return 1

@pytest.fixture(scope="class")
def class_value():
    return 2

@pytest.fixture(scope="session")
def session_value():
    return 3

@pytest.fixture
def indirect(module_value):
    return module_value

def test_indirect(indirect, request):
    assert request.node.get_closest_marker("xdist_group").args == ("tests/test_scope_group_probe.py",)

class TestScopes:
    def test_both(self, indirect, class_value, request):
        assert request.node.get_closest_marker("xdist_group").args == ("tests/test_scope_group_probe.py",)

    def test_class_only(self, class_value, request):
        assert request.node.get_closest_marker("xdist_group").args == ("tests/test_scope_group_probe.py::TestScopes",)

def test_session_only(session_value, request):
    assert request.node.get_closest_marker("xdist_group") is None

@pytest.fixture(scope="module")
def overridden():
    return "module"

class TestOverride:
    @pytest.fixture
    def overridden(self):
        return "function"

    def test_closest_definition_wins(self, overridden, request):
        assert overridden == "function"
        assert request.node.get_closest_marker("xdist_group") is None
```

- [ ] **Step 7: Switch the shared scheduler and run the smallest xdist verdict.** Change only `py_fast_cmd` to `--dist=loadgroup`; update the justfile comment describing `worksteal`. Run the following through the test front door, then read worker IDs and setup output: both pair consumers must run on one worker with one `pair` setup; the minted consumer must carry its own file group; the function-only test remains unmarked. Record the verdict before the complete pilot.

```sh
just test-one -n 2 --dist=loadgroup -vv --durations=0 \
  tests/test_replay.py::test_a_replay_runs_in_a_fresh_scratch_root_with_an_equal_recipe \
  tests/test_replay.py::test_r4_equal_recipes_without_a_receipt_derive_same_environment \
  tests/test_boundary.py::test_the_boundary_mints_a_run_over_the_held_fixture \
  tests/test_replay.py::test_definition_agreement_is_none
```

- [ ] **Step 8: Run one instrumented, complete 16-worker pilot.** With comparable low host load, run `PYTEST_ADDOPTS='--durations=0' just test-fast > .work/fixture-grouping/loadgroup.log 2>&1`. Parse every `setup`, `call`, and `teardown` duration row by file, print total reported worker-seconds, setup row count and seconds for every scoped-fixture file, and the top ten files by total worker time for both `worksteal.log` and `loadgroup.log`. Read the newest matching `test-fast` record in `~/.local/share/ops/runs.jsonl` for `tt` wall time and test count. This attributes a miss even if the other scoped fixtures explain only part of the old unmarked-loadgroup cost; one-at-a-time dispatch and worker-local cache locality remain possible costs.

```sh
PYTEST_ADDOPTS='--durations=0' just test-fast > .work/fixture-grouping/loadgroup.log 2>&1
python3 - <<'PY'
import collections
import json
import pathlib
import re

scoped = {
    'test_arm_staleness.py', 'test_assess.py', 'test_boundary.py',
    'test_closure_capture.py', 'test_frozen_guards.py', 'test_intent_reduce.py',
    'test_production.py', 'test_replay.py', 'test_typing_exercise.py', 'test_verify.py',
    'test_evaluation.py',  # imported production_pair is now a static dependency
}
for label in ('worksteal', 'loadgroup'):
    totals = collections.defaultdict(float)
    setup = collections.defaultdict(lambda: [0, 0.0])
    for line in pathlib.Path(f'.work/fixture-grouping/{label}.log').read_text().splitlines():
        match = re.match(r'^([0-9.]+)s (setup|call|teardown)\s+tests/([^:]+)::', line)
        if not match:
            continue
        seconds, phase, name = float(match[1]), match[2], match[3]
        totals[name] += seconds
        if phase == 'setup':
            setup[name][0] += 1
            setup[name][1] += seconds
    print(label, 'reported worker-seconds', round(sum(totals.values()), 1))
    print('top files', sorted(totals.items(), key=lambda pair: -pair[1])[:10])
    for name in sorted(scoped):
        print(name, 'setup rows/time', setup[name], 'file worker-seconds', round(totals[name], 1))

records = [json.loads(line) for line in (pathlib.Path.home() / '.local/share/ops/runs.jsonl').open()]
pilot = next(row for row in reversed(records) if row.get('project') == 'beliefs'
             and row.get('target') == 'test-fast' and '--dist=loadgroup' in row.get('command', ''))
print('pilot tt', {key: pilot.get(key) for key in ('at', 'seconds', 'exit', 'tests', 'rev', 'dirty')})
PY
```

- [ ] **Step 9: Apply the pilot gate and commit an accepted pilot.** Continue only if the same existing Python tests and one skip pass, reported worker time is **below 1,209.7 seconds**, instrumented `tt` time is **at most 93.925 seconds**, and no scoped-fixture file gains duplicate setup compared with worksteal. Compare each file's setup seconds and the top ten file totals as well. In `test_evaluation.py`, making `production_pair` a direct parameter moves its one fixture execution from pytest's call phase into setup; compare its combined call-plus-setup time and confirm one execution rather than treating the new setup row as duplication. `test_verify.py` has one file group containing both `pair` and `production_pair`, expected to be the longest group at roughly 30 seconds. If load makes the comparison inconclusive, repeat the pilot once. If it still misses, restore the hook, justfile, and test edits together, note the top-file attribution on `beliefs-04d696`, and stop this plan for a revised measured remedy. Do not run the repeated sweep on a failed pilot. If it passes, run `just check`, record the metrics in `tasks note beliefs-04d696`, close `beliefs-5cc080` with the pilot result, run `tasks check`, and commit the hook, tests, scheduler, and task records as `perf(beliefs): pilot scoped fixture grouping`.

### Task 2: Prove the fast and full gates, then commit the remedy

**Files:**

- Modify: `.worktrees/test-fast-remedy/AGENTS.md`, `.worktrees/test-fast-remedy/python/README.md`, and `.worktrees/test-fast-remedy/justfile` (current scheduler description; retain the dated 2026-09-26 measurements as history)
- Commit: the accepted Task 1 hook, test, and scheduler edits with these current-facing docs
- Evidence: `beliefs-04d696` via `tasks note`

**Interfaces:**

- Consumes: Task 1's accepted `loadgroup` command and the unchanged N2/TypeScript phases.
- Produces: a committed remedy with `just check` green, three warm pre-commit-of-this-step `test-fast` verdicts whose median `tt` time is at most 90 seconds, and a complete certified `just test` verdict at most 300 seconds. The pilot code commit precedes them, but they are not used for incident verification; the final accepted remedy commit is this task's documentation-and-result commit.

- [ ] **Step 1: Start the second child and run the repeated fast sweep.** After `beliefs-5cc080` is done, run `tasks start beliefs-2605cc`. Run three non-overlapping `just test-fast` verdicts with the same 16-worker host budget and low competing load. Record each `tt` time, test count, skip count, and host load in `tasks note beliefs-04d696`. The median of the three `tt` times must be at most 90 seconds. These runs occur before the final accepted remedy commit and will not be used for `tt-latency verify`. If the median misses under comparable load, attribute the top files, restore the Task 1 code/test/justfile paths from the recorded pre-pilot revision, record and commit that rollback, and leave the P0 open for a revised remedy. Do not continue to the full gate.

- [ ] **Step 2: Run the complete certified gate once.** Run `just test` in the worktree, without overlapping a fast run. Require both Python phases and the TypeScript suite to pass within 300 seconds; confirm the non-N2 phase still excludes `test_n2.py` and the separate N2 phase receives the full `OPS_WORKERS` allowance. If the result is close to 300 seconds or materially unlike the earlier 235–237-second full gates, repeat once and attribute the difference before continuing. If the scheduler causes a confirmed failure or a sustained budget miss, roll back the Task 1 paths together as in Step 1 and keep the incident open.

- [ ] **Step 3: Update current-facing instructions.** Change the `worksteal` commands in `python/README.md` to `loadgroup` and explain in one sentence that tests using module/class fixtures receive file/class groups while other tests remain independently scheduled. Update `AGENTS.md`'s current gate wording with the new scheduler and measured result; preserve its dated 2026-09-26 figures as prior evidence. Keep the justfile's one scheduler definition and comment aligned. Do not edit historical plans or frozen acceptance records.

- [ ] **Step 4: Check and commit the accepted remedy.** Run `just check`, `tasks check`, `git diff --check`, and `git status --short`. Confirm the temporary probe is gone and no result log is staged. Run `just test-fast` again only if Step 3 changed executable behavior; documentation changes alone do not require a fourth pre-commit sweep. Close `beliefs-2605cc` with the measured fast and full result, then run `tasks check` again. Commit the current docs, measurement notes, and second child closure as `perf(beliefs): accept scoped fixture grouping`. This final accepted remedy commit is the timestamp anchor after review; do not amend it later to add the incident closure note.

### Task 3: Verify the incident after the commit and close the halt

**Files:**

- Modify through `tasks` only: `.worktrees/test-fast-remedy/tasks/beliefs-04d696.md`
- No additional product code changes

**Interfaces:**

- Consumes: Task 2's remedy commit and timestamp, the `tt-latency verify` rule in ops `latency.toml`, and the currently open halt task.
- Produces: three qualifying post-commit `test-fast` records per breached host, a successful `tt-latency verify` note, and a done incident containing the verify output. Branch integration follows this task.

- [ ] **Step 1: Start the third child and review before final verification.** After `beliefs-2605cc` is done, run `tasks start beliefs-d21024`. Run a whole-branch implementation review and fix findings first. If main moved, merge main into the worktree branch and resolve conflicts before the post-commit verification; rerun focused checks and the affected fast/full gate if code changed. The final remedy commit after any fix or merge is the timestamp anchor for the next steps.

- [ ] **Step 2: Record the final remedy timestamp.** Get its commit epoch with `git show -s --format=%ct HEAD` and format it as RFC 3339 UTC with `date -u -d "@<epoch>" +%Y-%m-%dT%H:%M:%SZ`. Use that exact timestamp for verification; its qualifying runs must start strictly later.

- [ ] **Step 3: Run three new qualifying fast verdicts.** On each host named by a `breach:` note, run `just test-fast` three times sequentially after the commit, with no overlapping `just test` or other long recorded run. Check each exit code and `tt` record; if a run is contended, make an additional uncontended run. The median of qualifying runs must be at most 90 seconds.

- [ ] **Step 4: Verify and close in hierarchy order.** Run `tt-latency verify beliefs-04d696 --after <UTC timestamp>` on each breached host. Require exit zero and capture its full output; `verify` also writes a `verified:` note. Close `beliefs-d21024` with the verification result, then run `tasks done beliefs-04d696 "<one-line result; include the flattened verify output>"`; the parent refuses to close while any child is open. Run `tasks check` with zero errors and resolve every non-environment warning. Commit both task records as `chore(beliefs): close verified test-latency incident`. If verification fails, keep the halt open and record the measured residual instead of closing it. If three or more qualifying post-commit runs confirm a median above 90 seconds, roll back the scheduler and grouping together and revise the remedy. This separate closure commit is required by the post-commit verification rule; it supersedes the usual same-commit task-close convention.

## Integration

After Task 3 is done, merge the verified branch into main using the repository's branch-finishing workflow. If main moves between verification and merge, merge its changes without altering the verified remedy tree; if code changes, rerun the affected gate and qualifying fast verification before integration. Before removing the worktree, run `tt-report`, check that no host pointer resolves into it, unlock it, and remove it with `git worktree remove`. Report the final commits and measured fast/full times.

## Plan self-check

- Task 1 covers all grouping, real fixture closure checks, scheduler ordering, and the whole-suite pilot before a sweep.
- Task 2 preserves the selection and full gate, updates current docs, and commits only after performance acceptance.
- Task 3 enforces the post-commit run count, uncontended condition, strict timestamp, and child-before-parent task closure. Integration follows the completed task.
