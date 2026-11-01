# Spec round 4 (scoped re-review) — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only Claude Code subagent dispatched by the controller).
Revision reviewed: beliefs 5237cb7 (diff 2cee097..5237cb7 read in full).
Verdict: accept. Critical 0, Important 0, Minor 3. All five round-3 findings addressed; PYTEST_ADDOPTS form correct.

Read at 5237cb7: justfile (all recipes and command variables), .githooks/pre-push, .githooks/pre-commit, .github/workflows/ci.yml, python/tests/test_front_door.py, python/pyproject.toml (addopts), tools/tt (project_of, _git, read_policy, execution_decision, owner_of, shared_log, run, main). Precedent: nodes python/tests/test_development_routes.py at 13b572d.

## 1. Round-3 findings

N1 (--set does not reach nested just): addressed. Both claims are correct: --set does not reach nested just, and environment variables do (just passes its environment to recipe shells, tt passes {**env, TT_JUNIT_DIR} to its child, and a pass-through host-budget stub execs with it, so FAIL_STEP and TT_FORCE reach every level). The cwd=ROOT ban closes the recursion and wrong-reason-green paths from round 3.

External commands each Command-contract recipe would invoke after the split:
- check-hygiene / hook-pre-commit-docs: python3 tools/ops-check, python3 tools/ops-docs check, tasks check
- check-code: uv (ruff check, ruff format check, pyright), npm run typecheck, npm run check
- test-fast: host-budget, uv, npx --no-install vitest
- test, test-push: host-budget, uv, npm test
- test-one: host-budget, uv
- test-full: real nested just
- ci-python / ci-typescript: uv / npm
- pre-push hook: ssh -G (only for URLs with a host), just --evaluate, python3, git rev-parse
- tt itself: git, and tasks where <cwd> --json whenever no tasks/.config.toml is found above the cwd

The stub names (uv, npm, npx, tasks, host-budget, ssh, plus ops-check/ops-docs) are sufficient. Real just, python3 (/usr/bin/python3 has tomllib on host and on ubuntu-latest's 3.12), git, sh and coreutils/awk stay real; nodes' PATH (stub bin, which just's directory, /usr/bin:/bin) provides them. attr is reached only by setup, which step 3 does not exercise. Two stub behaviours and three fixture details are missing (Minor 1).

Minor 1 (PYTEST_ADDOPTS): addressed and correct. "${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-rfEs" behaves identically in bash and zsh: -o tmp_path_retention_policy=failed -rfEs on this host, -rfEs when unset or empty. pytest shlex-splits it to -o, tmp_path_retention_policy=failed, -rfEs; -rfEs parses as -r fEs (pytest 9's default fE plus s). pyproject addopts (-q --ignore=tests/acceptance) has no conflicting -r. FAILED/SKIPPED lines start with their keyword, so tt's summary regex (line start or "=+ ") cannot match them; the test count is unchanged. The command string is unchanged, so tt's recorded command is unaffected.

Minor 2 (broad_targets test): addressed. The fixture-policy arm can fail before activation. The live arm guards activation: the activation commit runs just test-one over test_front_door.py beforehand, with the uncommitted .tt.toml present in the working tree, and test-one is protected, so the live arm runs. The misplaced sentence now has its own paragraph. Nit: say the fixture policy carries the exact list in the TOML block, or "can fail before activation" may test only the checker, not the list.

Minor 3 (trigger vs declared coverage): addressed. Step 4 states the two as separate facts and names the justfile comment (lines 53–54) and AGENTS.md's Remote CI line (19). The general rule ("Any line that has to state…") also covers justfile line 4 and AGENTS.md line 17, which still hold as declared-coverage statements. Timing nit: Minor 3 below.

Minor 4 (other ci_suite_refs shapes): addressed and correct; undefined shapes fail the coverage test, the conservative direction.

## 2. New findings

Critical: none.

Important: none. The diff does not break the accepted round-1/round-2 resolutions. The Pre-push coverage routing text (hook_repo copies tools/tt; routing cases declare their own ci_suite_refs) agrees with the new step-3 fixture; fixture placement is the builder's.

### Minor

1. Step 3's stub description is literally wrong for tasks and host-budget, and omits three fixture details. ("Each stub appends to an events log and fails when an environment variable such as FAIL_STEP names it.")
   - tasks: tt's project_of runs `tasks where <cwd> --json` on every tt call unless a tasks/.config.toml is found above the cwd. A log-and-exit stub prints nothing, tt calls fail("cannot tell which project …"), and every recipe exits 1 before its child. Nodes' stub answers non-check calls with the fixture's project JSON and returns before both the events log and the FAIL_STEP test. If an implementer adds the JSON answer but still applies FAIL_STEP to where, a FAIL_STEP=tasks case for "a failing hygiene step stops check-code" passes for the wrong reason (tt fails before hygiene runs).
   - host-budget: every timed test recipe runs under host-budget run -- sh -c …; a log-and-exit stub never runs the child. Nodes has no host-budget stub, so the nodes pattern does not supply this. The pass-through form is already in beliefs (test_front_door.py:81: `[ "$1" = run ] && [ "$2" = -- ] || exit 1; shift 2; exec "$@"`).
   - Fixture details: the fixture must contain python/ and ts/ (every package command starts with cd python or cd ts; nodes creates both); the ops-check/ops-docs stubs run as python3 tools/…, so they must be Python source; the key-by-key env needs an absolute BELIEFS_CI_EVIDENCE_DIR for the forced ci-python/ci-typescript cases, or the spec's fail-early rule turns the expected exit 7 into an evidence-path refusal (nodes sets NODES_CI_EVIDENCE_DIR).
   Most of these fail loudly at RED (success cases go red), hence Minor; FAIL_STEP=tasks is the one silent case. Fix: host-budget stub checks run -- and execs the rest; tasks where answers the fixture's project JSON without logging or failing (or give the fixture a tasks/.config.toml with a prefix); the fixture has python/ and ts/, Python-source ops-check/ops-docs stubs, and an absolute BELIEFS_CI_EVIDENCE_DIR.
2. Internal contradiction on cwd=ROOT (step 3). "None runs with cwd at the repository root" sits next to "--set stays acceptable for single-level recipes such as the existing test-one forwarding case", which runs with cwd=ROOT (test_front_door.py:90, :96). It does not recurse, but the sentences pull opposite ways. Fix: the test-one forwarding case moves into the fixture checkout and keeps --set one_cmd (the single-level route works there).
3. Stale-claim window between steps 3 and 4. Widening the trigger in step 3 makes the justfile comment at lines 53–54 ("on main pushes … only origin/main is covered by the push trigger") and AGENTS.md's Remote CI line stale; step 4 corrects them in a later change, but the repository rule asks for the correction "in the same change that makes them stale". Nothing is pushed between the steps, so the cost is small. Fix: the commit that widens ci.yml's trigger also rewrites those two lines, or state that the rule is read at branch level for this lane.

## Checked and fine

Real just is found on the hosted runner (setup-just puts it on PATH, so shutil.which sees it), and key-by-key PATH keeps /usr/bin/python3. A temporary HOME with no XDG_DATA_HOME keeps tt's shared log inside the fixture, so TT_LOG is optional. The template's warning block finds tools/tt through real just --evaluate tt in the fixture. The ssh stub matters only for host URLs; the beliefs routing cases use https and never reach it. The nested hosted-refusal case can follow nodes' appended nested: recipe. test-full = TT_FORCE=1 just test yields exactly one forced test row through the pass-through host-budget stub.
