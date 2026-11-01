# Spec round 3 (scoped re-review) — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only Claude Code subagent dispatched by the controller).
Revision reviewed: beliefs 2cee097 (diff e2927dd..2cee097 read in full).
Verdict: revise. Round-2 findings: 9 of 10 addressed correctly; M5's prescribed mechanism does not work (N1). New: Important 1, Minor 4.

Read at 2cee097: justfile, .githooks/pre-commit, .githooks/pre-push, .github/workflows/ci.yml, python/pyproject.toml, python/tests/test_front_door.py, conftest.py, test_n2.py (child env), the explicit skip sites in python/tests, and tools/tt (RUNNERS/parse_tests, read_policy, execution_decision, project_of, shared_log, main). Context: ops templates/githooks/pre-push (415de02), ops bin/host-budget (env passing), the ops design file log (469140a is head), and the nodes adoption's justfile and python/tests/test_development_routes.py. Probes: installed pytest 9.1.1's getreportopt and _REPORTCHARS_DEFAULT; a scratch justfile testing whether --set reaches nested just; this host's PYTEST_ADDOPTS.

## 1. Round-2 findings

- I-A skip-reason baseline: addressed. Correct for counting: tt's pytest seen/count regexes require line start or "=+ " before "<n> <word>… in <secs>s"; SKIPPED [n] path:line: reason lines do not match, and no explicit skip reason in python/tests contains such text. PYTEST_ADDOPTS reaches pytest (tt runs the child with {**env, …}; host-budget execs with {**os.environ, **job_environment}). N2 arm children build their env key by key without PYTEST_ADDOPTS, so the arms are unaffected. Skip reasons are static strings comparable with hosted JUnit message. Two unstated side effects: Minor 1.
- I-B post-activation verification: addressed and correct. Field names match tt (execution; exit, tests, selection, slowest, and also content, None on skip). read_policy runs before the decision even for a protected target, so a test-one ran row also proves the main checkout's .tt.toml validates. After widening, the activation push from main takes hook-pre-push-fast, so test-push (not test) is the right child to check.
- I-C stale guide claims: addressed and correct; one remaining ambiguity, Minor 3.
- M1 ops revision: addressed; 469140a is the head of the ops design.
- M2 tools/tt copied for every routing case: addressed and correct. The template's warning block is gated only on recipe = hook-pre-push, loads shlex.split(just --evaluate tt)[-1] (tools/tt relative to cwd), and turns OSError into exit 2, so without the copy every full-route case fails under check=True.
- M3 GitHub glob semantics: addressed and correct (* does not cross /, ** does; fnmatch crosses). One edge case unspecified: Minor 4.
- M4 key-by-key env for every subprocess: addressed; covers both inline calls in test_one_preserves_arguments_and_records_the_run. Nit: the runner sets GITHUB_ACTIONS, not the job.
- M5 failure short-circuit with marker children: cases added, but the prescribed mechanism does not work for this recipe structure (N1).
- M6 broad_targets names test: correct intent, no protection when it matters (Minor 2).
- M7 hook-pre-push named: addressed and correct (check_cmd && test_cmd; 0 runs in October).

## 2. New findings

### Important

N1. just --set markers do not reach the nested recipes the command contract creates. (Step 3, "Exercise real recipes with just --set marker commands in place of their children"; Command contract table.) The new recipes are nested just calls: hook-pre-commit (hygiene, then just check-code), hook-pre-push (hygiene, just check-code, just test), hook-pre-push-fast (hygiene, just check-code, just test-push), check (just check-hygiene, just check-code), test-full (TT_FORCE=1 just test). --set applies only to the just process it is given to; a recipe line running just <child> starts a fresh process that evaluates the real variables. Probe under just 1.59.0: cmd := "echo real", outer: runs sh -c '{{cmd}}' then just child; just --set cmd "echo marker" outer printed marker then real.

Failures for the cases step 3 now requires:
- "A failing check-code stops test-push" via just --set py_check_cmd false … hook-pre-push-fast: the nested just check-code runs the real py_check_cmd. In a hook_repo-style tmp fixture it fails only because there is no python/ directory, so the test is green for the wrong reason.
- "test-full … propagates failure" run with cwd=ROOT (as the current test_one case does): the nested TT_FORCE=1 just test runs the real suite, which includes test_front_door.py, which runs test-full again: unbounded recursion, the fork-bomb shape test_n2.py's guard exists to prevent. In a tmp fixture it fails fast, again for the wrong reason.
- Enabled-policy cases expecting broad children to run hit the same split: they recurse into the suite or pass vacuously.

The spec's own justification ("Real children would run suites inside the suite") describes exactly what its mechanism produces for every nested recipe.

Fix: prescribe the nodes pattern (nodes/python/tests/test_development_routes.py): a fixture checkout copying justfile, tools/tt and .githooks/pre-push; stub executables (uv, npm, tasks, host-budget, ssh) on the key-by-key PATH plus stub tools/ops-check and tools/ops-docs; an events log; and an env var such as FAIL_STEP selecting the failing step. Env vars, unlike --set, reach nested just. Assertions read events and tt rows (hygiene-only under policy-off; one forced test row with exit 7 for test-full). --set stays acceptable for single-level recipes (the existing test-one forwarding case); the routing tests keep the stub just that delegates --evaluate to the real binary.

### Minor

1. PYTEST_ADDOPTS=-rs replaces two things the spec calls unchanged (step 2). (a) This host exports PYTEST_ADDOPTS="-o tmp_path_retention_policy=failed" (from ~/.zshenv, present in the agent shell); conftest.py's _forget_temporary_roots docstring names it as routine-run configuration. Assigning -rs drops it, so the baseline runs under default retention (all, 3 sessions), keeping every tmp_path under TMPDIR (/mnt/ssd3/tmp) and no longer exercising routine runs' path-reuse behaviour. (b) -r replaces pytest's default fE (pytest 9.1.1 _REPORTCHARS_DEFAULT = "fE"), so short-summary FAILED/ERROR lines disappear; failures remain countable from the summary line and the FAILURES section. Fix: PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-rfEs" just test, and say the host's value is preserved.
2. The broad_targets test protects nothing when it matters (Pre-push coverage routing, third contract test). It checks the live .tt.toml "when the file exists", so it passes vacuously at every commit before activation, including its own RED→GREEN. The one commit that adds .tt.toml (activation) runs only test-one tests/test_front_door.py and "the workflow contract test" (singular, though there are several), and under policy-off its hooks skip everything broad, so a typo surfaces only in the post-push hosted run. Fail-safe (the target keeps running), but give the test a fixture case so it can fail before activation, and put it in test_front_door.py or name it in the activation commit's focused list. That list should also name any test that reads a README or docs/ line the activation commit edits. The sentence "Under policy-off the activation commit's own hooks skip…" has merged into this paragraph; it belongs with the routing tests.
3. Trigger vs declared coverage in step 4's pre-activation text. After step 3, ci.yml triggers on ["**"] while ci_suite_refs stays refs/heads/main. "Covered refs: refs/heads/main" is right; "CI runs on main pushes" (the current justfile comment above ci_suite_refs, "only origin/main is covered by the push trigger", and AGENTS.md's Remote CI line) is stale from step 3 onward. Say step 4 describes the widened trigger and the main-only hook declaration as two separate facts.
4. The coverage relation is incomplete (line 196ff). "refs/heads/<name> requires <name> or **" is stricter than GitHub (* matches a slash-free name): harmless, conservative. Any other glob shape (refs/heads/release/*) is undefined. Say any other ci_suite_refs shape fails the test until its GitHub equivalent is specified.

## Checked and fine

-rs lines never reach tt's pytest regex, so the tests count is unaffected. The variable reaches pytest through tt and host-budget. test_frozen_guards' collect-only child inherits -rs harmlessly. Skip reasons in python/tests are static and comparable with hosted JUnit messages; locally on the certified host none is expected to fire except under root or without git. tt's key-by-key needs are covered by the spec's environment (TT_LOG or a temporary HOME for the log; tasks optional; owner from branch). I-B's fields and route match tt and the hook's routing. The ops template matches M2's description. 469140a is current. Rollback keeps the round-1 cadence and adds the guide-update line. No contradiction with round-1 resolutions; Certified-host, Tradeoffs and table stay consistent ("all four skip" means their suite children skip, as round 2 worded it).
