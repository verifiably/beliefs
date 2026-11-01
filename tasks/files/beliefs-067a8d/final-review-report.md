# Final whole-branch review, round 1 — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only Claude Code subagent, model opus specified by the controller).
Range: 0b40c74..79098f3 on design/067a8d-test-policy (code excluding tasks/).
Verdict: with fixes. Critical 0, Important 1, Minor 4.

## Strengths

- Recipe split matches the spec's Command contract line for line (check-hygiene, check-code, test-push, test-full; untimed check and gate; hooks time hygiene under their own hook-* target then nested just children; host-budget inside tt's child), same composition as nodes.
- Pre-push warning block byte-identical to the nodes/ops template (diffed), placed after unset $git_local_vars, full route only, exit 2 on malformed policy. Routing, deletion handling, byte-preserving forwarding and keepalive refusal untouched.
- route_fixtures.Checkout: every tool a stub, env key by key (GIT_CONFIG_GLOBAL, GIT_CONFIG_NOSYSTEM, fake identity, no TT_FORCE/GITHUB_ACTIONS), init_repo asserts toplevel and git-dir before any write including siblings. tt rows asserted directly (reasons default/forced, skip-row nulls).
- Workflow tests execute the real Prepare/Require run: scripts against fixtures; trigger lookup cannot pass vacuously; github_covers follows the spec's GitHub-glob rule.
- Pytest JUnit test drives real pytest through the uv stub into a spaced evidence path, checks skip messages and that XML survives a failing static check.
- Workflow details correct for ubuntu-latest: ../../atoms from beliefs/python resolves; no bash/dash-specific constructs; upload pin matches nodes; TT_FORCE at job scope.
- Docs follow the spec in substance, including the exact-mismatch duty.
- Ran `just test-one tests/test_front_door.py tests/test_ci_workflow.py` from the physical path: 60 passed in 13.58s; worktree clean afterwards.

## Important

1. justfile:170-171 — no test pins CI suite selection to the local suite (Task 5 Ruling accepted it). ci_py_test_cmd and ci_ts_test_cmd are hand-copied from py_fast_cmd + N2 and ts_test_cmd with JUnit flags added. test_vitest_reporter_arguments pins CI's own argv and test_pytest_junit pins its behaviour, but nothing compares CI's command with the local one. A later edit to py_fast_cmd, py_test_cmd or ts_test_cmd (a new --ignore, a third phase, a marker) silently changes what CI runs relative to just test. The Global Constraint "test selection stays unchanged except JUnit" is enforced only by hand; after activation hosted CI is the only routine full-suite route, so the fast push route and the policy-off argument rest on CI running exactly test's suite; drift would be silent loss of coverage. Fix: in a Checkout, `just --evaluate ci_py_test_cmd` and `py_test_cmd`, strip the --junitxml tokens with a regex and assert equality; same for ci_ts_test_cmd vs ts_test_cmd stripping ` -- --reporter=default --reporter=junit --outputFile.junit="…"`.

## Minor

1. test_front_door.py:271 — the deletion case does not test what Review Focus 1 targets: the deleted ref refs/heads/gone matches refs/heads/* anyway, so it passes whether or not deletions are set aside (removing the `pushed = …` filter leaves it green). Hook behaviour is correct and unchanged; the weak case comes from the plan's Task 4 text. Fix: add a covered main push plus a deletion of refs/tags/old with coverage refs/heads/main, expecting hook-pre-push-fast.
2. test_front_door.py:287-295 — the git-local-variable test never observes a nested child (Review Focus 2): under policy() check-code and test skip, so the only stub events come from the first-line hygiene process, and the stub records GIT_DIR only. The property holds structurally (all children inherit the cleaned `exec just` environment); the plan specified policy(). Fix: run with no policy so nested children log events; record GIT_WORK_TREE too and assert both None for non-ssh events.
3. .githooks/pre-push:2 and justfile:134 — stale comments: "The push gate, recorded under its own target so the report can price the hook" and "Hook targets time their hygiene only, so the report can cost the hook itself" — the hook target now times hygiene only and the hook's full cost is that row plus the child rows. Fix: reword ("the hook target records its hygiene; each child records its own row, so the hook's cost is their sum").
4. test_ci_workflow.py:113 — the Vitest JUnit path with spaces is untested (Review Focus 3 partial): pytest paths and the inventory are tested with spaces, the Vitest argv test uses the default `evidence` dir. Fix: point BELIEFS_CI_EVIDENCE_DIR at a spaced dir and assert one intact --outputFile.junit element. Low practical risk (RUNNER_TEMP has no spaces on GitHub).

## Declined to judge

- Pre-commit hook does not clear git-local vars before just (pre-existing; its route builds no fixture repos).
- Nested just children do not inherit --set/--justfile overrides (spec mandates nested calls; no documented override reaches a composed recipe).
- `if: always()` on Require/upload runs on cancelled runs too (nodes precedent; harmless).
- cancel-in-progress can leave intermediate main commits unverified (spec states it).
- Same-repo PRs show skipped python/typescript checks, interacting with any branch protection (none declared; spec chose the condition).
- Vitest JUnit skips carry no message (Task 5 Ruling; 0 TS skips; acceptance-time matter).
- Pre-existing tests passing {**os.environ} to subprocesses (config_probe.py:43, test_boundary.py:519, test_adapter.py:310, test_world_rules.py:490), outside this diff.
- Action SHA pins not verified upstream (no network); match nodes.
- Hosted run's actual outcome belongs to Tasks 7-9.
- Warning block silently skips when `just --evaluate tt` fails (template behaviour; the following exec just fails anyway).
- "biome, tsc" vs "tsc, biome" ordering in python/README.md and AGENTS.md (pre-existing nit).
- Task 1 and Task 3 Rulings accepted as ruled.

## Recommendations

- Fix Important 1 before Task 7 integration.
- Fold Minors 1, 2, 4 into the same test pass so Review Focus 1-3 become regression-catching checks.
- In Task 8 Step 5, refresh the two stale comments from Minor 3 alongside the state-line grep.

## Assessment

Ready to merge: with fixes. Tasks 1-6 implement the spec faithfully, the hosted workflow should run on ubuntu-latest as written, and the 60 focused tests pass; the one Important gap is unpinned CI-vs-local suite selection, which matters because policy-off makes hosted CI the sole routine full-suite evidence.
