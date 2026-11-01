# Corrective round 2 re-review — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only subagent). Scope: commit 70385c4 (test_cmd composition assertion), fix for the round-1 re-review Minor re-graded Important.
Verdict: accept. Critical 0, Important 0, Minor 0. Ran just test-one tests/test_ci_workflow.py: 18 passed.

The new assertion (test_ci_workflow.py:248) pins test_cmd exactly to py_test_cmd + " && " + ts_test_cmd; with c929e95's assertions the chain test_cmd -> ci_py_test_cmd/ci_ts_test_cmd is pinned at the variable level, only reporting flags stripped.

Checked and fine: the test recipe body is pinned indirectly by test_enabled_hooks_run_every_child_in_order's exact tool-event list (host-budget, uv, uv, npm); an argv-only edit typed inline in the recipe body would bypass the variables and is not a realistic path (optional future fix: assert event argv there). ci-typescript body pinned by test_vitest_reporter_arguments' exact argv and cwd; ci-python body pinned by the real-pytest JUnit test requiring both phases (same inline-argv caveat). host-budget run sets only worker-count variables; sh -c wrapping and quoting identical on both sides; ts/package.json test script is `vitest run`; addopts and testpaths shared; no conftest selects on CI or GITHUB_ACTIONS; VERIFIABLY_UNCERTIFIED_HOST=1 changes evidence, not selection, and is pinned. No new issue.
