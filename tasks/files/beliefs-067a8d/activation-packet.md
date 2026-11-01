# Activation packet — beliefs-067a8d (Task 8)

Approval asked: integrate and push the activation commit
`48d9891eb10986694a686b66dc7b859f3e965d00` (on `design/067a8d-test-policy`, unmerged). From the
main checkout: first require `git diff --name-only d6dab00 HEAD` to list only `tasks/*.md`
(otherwise stop and present a new packet), record `git log --oneline d6dab00..HEAD`, then
`git merge --no-ff 48d9891` and `git push origin <merge-sha>:refs/heads/main`. Nothing commits in
main between the merge and its push. After that push the registered main checkout runs with
`automatic_broad = false`.

## The activation commit

```
48d9891eb10986694a686b66dc7b859f3e965d00
chore(policy): activate tt policy-off with remote suite coverage

 .tt.toml  | 2 ++
 AGENTS.md | 4 ++--
 justfile  | 8 ++++----
 3 files changed, 8 insertions(+), 6 deletions(-)
```

```diff
diff --git a/.tt.toml b/.tt.toml
new file mode 100644
index 0000000..c8bc728
--- /dev/null
+++ b/.tt.toml
@@ -0,0 +1,2 @@
+automatic_broad = false
+broad_targets = ["test", "test-fast", "test-push", "check-code", "ci-python", "ci-typescript"]
diff --git a/AGENTS.md b/AGENTS.md
index 193fc61..33026c3 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -13,9 +13,9 @@ Member of the verifiably family (https://github.com/verifiably/docs/blob/main/ov
 ## Gates
 
 - From the repository root, run `just check` (`check-hygiene`: ops-check, ops-docs check, `tasks check`; then `check-code`: ruff check, ruff format --check, pyright, tsc, biome) and `just test` (parallel Python tests outside N2, standalone N2, then the TypeScript suite). `just gate` runs both. Every check and suite runs through the vendored timing wrapper `tools/tt`, so every run is recorded (ops `docs/specs/2026-09-04-test-ci-audit-design.md`); `check` and `gate` are untimed compositions whose children record their own rows. Freeze pins on Python files hold modulo formatting (frozen guard doctrine §8), so formatting covers every file; `.git-blame-ignore-revs` lists both reformats.
-- Test execution policy comes from `.tt.toml` at the Git top level, validated by `tools/tt` (ops `docs/specs/2026-10-29-test-execution-policy-design.md`; adoption: `docs/superpowers/specs/2026-10-31-test-execution-policy-design.md`). If the file is absent, policy is enabled and every target runs. With `automatic_broad = false`, the broad targets it lists (`test`, `test-fast`, `test-push`, `check-code`, `ci-python`, `ci-typescript`) are recorded as skipped instead of run, unless `TT_FORCE=1` is set; `test-one`, `test-full`, `check-hygiene`, `setup` and the hooks are protected and always run. A skip is a decision, never a pass or a timing sample. This checkout has no `.tt.toml` yet, so policy is enabled.
+- Test execution policy comes from `.tt.toml` at the Git top level, validated by `tools/tt` (ops `docs/specs/2026-10-29-test-execution-policy-design.md`; adoption: `docs/superpowers/specs/2026-10-31-test-execution-policy-design.md`). If the file is absent, policy is enabled and every target runs. With `automatic_broad = false`, the broad targets it lists (`test`, `test-fast`, `test-push`, `check-code`, `ci-python`, `ci-typescript`) are recorded as skipped instead of run, unless `TT_FORCE=1` is set; `test-one`, `test-full`, `check-hygiene`, `setup` and the hooks are protected and always run. A skip is a decision, never a pass or a timing sample. This checkout's `.tt.toml` sets `automatic_broad = false`, so those broad targets skip locally and hosted CI carries them on every branch push.
 - Focused Python runs: `just test-one tests/test_file.py`, `just test-one tests/test_file.py::test_name`, or `just test-one -k "a and b"` (paths relative to `python/`). Focused TypeScript runs: `just --set one_cmd "cd ts && npx --no-install vitest run" test-one <filename-filter> -t "<test-name>"` (filters relative to `ts/`). Arguments reach the runner intact; at least one is required. N2 can be selected with `just test-one tests/test_n2.py`; the recipe runs under `host-budget run`, which supplies its required `OPS_WORKERS`. `just setup` installs the TypeScript dependencies (`npm ci`, which is installation, not a gate); the Python side needs none, since `uv run --frozen` builds the locked environment on first use.
-- `just test-fast` runs all non-N2 Python tests in parallel plus the affected TypeScript tests. The non-N2 phase uses `loadgroup`: module/class fixture consumers share file/class groups, while other tests schedule separately. N2 is the slow standalone phase of `just test`. The push hook treats a push to `origin` whose every ref matches `ci_suite_refs` (now `refs/heads/main`) as covered by CI's complete package suites; every other push keeps the complete local gate. Hand-run full suites are costly here: the historical serial gate took about 18 min, and the baseline week (beliefs-f253a1) found hand-run full suites costing 2.4x the pre-push hook itself.
+- `just test-fast` runs all non-N2 Python tests in parallel plus the affected TypeScript tests. The non-N2 phase uses `loadgroup`: module/class fixture consumers share file/class groups, while other tests schedule separately. N2 is the slow standalone phase of `just test`. The push hook treats a push to `origin` whose every ref matches `ci_suite_refs` (now `refs/heads/*`, every branch) as covered by CI's complete package suites; any other push (another remote, or a tag) takes the full local route, whose suite policy skips with a warning. Hand-run full suites are costly here: the historical serial gate took about 18 min, and the baseline week (beliefs-f253a1) found hand-run full suites costing 2.4x the pre-push hook itself.
 - Deliberate verification: `just test-full` forces `test` and is suite evidence, its forced `test` row; it runs no hygiene, lint or typecheck. `TT_FORCE=1 just gate` is full-gate evidence: the consecutive `check-hygiene`, `check-code` and `test` rows of one invocation, with the same `rev`, `dirty` and `content`, each `execution: ran`. Unforced rows under enabled policy are equally valid; under policy-off the broad rows need `TT_FORCE=1`. A results record or freeze names which of the two it cites. A policy skip or a hook completion is never evidence that a suite or gate passed.
 - The git hooks in `.githooks/` run `just hook-pre-commit` at pre-commit: hygiene, timed under the hook's target, then `just check-code`. Only commits whose every staged path matches `AGENTS.md` or `tasks/*.md` run `just hook-pre-commit-docs` instead (hygiene only, well under a second); renames count on both sides and failed classification runs the full check. README.md and docs/ are test inputs and excluded from this allowlist. At pre-push, `just hook-pre-push-fast` runs hygiene, `just check-code` and `just test-push` (all non-N2 Python tests and the full TypeScript suite) when CI covers every pushed ref on `origin`; `just hook-pre-push` runs hygiene, `just check-code` and `just test` otherwise, and warns when policy skips that suite with no remote coverage declared. Since this split, hook targets time hygiene only, `check` is untimed, and `check-hygiene`, `check-code` and `test-push` are new series; none is compared with the earlier whole-hook or `check` medians. On a fresh clone run `git config core.hooksPath .githooks` once.
 - Remote CI: `.github/workflows/ci.yml` runs `just ci-python` (Python 3.11 and 3.13) and `just ci-typescript` (Node 20 and 24) on every branch push, on manual dispatch, and on fork pull requests (a same-repository PR's branch push already ran). A newer push to a ref cancels the older run, which leaves that revision unverified. The jobs set `TT_FORCE=1`, so tt policy never skips them, and upload JUnit plus a module inventory (with the atoms and nodes revisions) as 30-day artifacts. It runs the recipes rather than `just gate` because the `tasks` binary is not on a runner. It costs nothing: verifiably/beliefs is public, and standard GitHub-hosted runners are free in public repositories on every plan, drawing on no private-repo minute allowance. Larger, GPU and macOS runners are billed even on public repos, so CI stays on standard Linux.
diff --git a/justfile b/justfile
index cec7128..be069df 100644
--- a/justfile
+++ b/justfile
@@ -4,7 +4,7 @@
 # A `.tt.toml` (absent: enabled) may skip the broad targets; `just test-full` and
 # `TT_FORCE=1 just gate` are the deliberate suite and full-gate routes (AGENTS.md).
 # CI runs the full suites on every branch push; the push hook treats ci_suite_refs as
-# covered, and other pushes keep the complete local gate.
+# covered, and other pushes take the full local route, which tt policy may skip.
 #
 # Every recipe runs through the vendored timing wrapper tools/tt and the shared hygiene
 # check tools/ops-check (source of truth: ops bin/tt and ops bin/ops-check), so each run
@@ -56,9 +56,9 @@ docs_paths := "AGENTS.md tasks/*.md"
 
 # The refs whose pushes the hook treats as covered by CI's complete package suites.
 # ci.yml runs them on every branch push (test_ci_workflow.py checks that it covers
-# each glob here); this declaration stays refs/heads/main until tt policy-off
-# activation widens it, so until then other pushes keep the complete local gate.
-ci_suite_refs := "refs/heads/main"
+# each glob here), so every branch push to origin is covered; tags and other remotes
+# take the full route, whose suite tt policy may skip with a warning.
+ci_suite_refs := "refs/heads/*"
 ci_remote := "origin"
 
 # Fixed fast set (act design form 3): all non-N2 Python tests plus all TS tests.
```

Focus checks run before it was committed (its own pre-commit hook skipped check-code by
policy, as designed): `just test-one tests/test_front_door.py tests/test_ci_workflow.py
tests/test_designs_corpus.py tests/test_check_guide.py` -> 84 passed (includes the live
`.tt.toml` broad-targets check and the `refs/heads/*` coverage check); `TT_FORCE=1 just
check-code` -> ruff, format, pyright, tsc, biome clean (row: check-code ran forced exit 0);
`ops-docs check` ok.

## Main since the published push

`d6dab00..main` holds 16 commits, all `chore(tasks)` record commits; `git diff --name-only
d6dab00 main` lists only `tasks/` paths. The merge would publish those record commits
with the activation commit. Further record commits (this packet's attachment, the park) will
be listed again at Task 9 Step 1 before merging.

## Hosted acceptance of the published revision (run 41298875513, d6dab00, success)

| Job | Phase | Cases | Executed | Skipped | Failed/errors | Modules |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| python 3.11 | non-N2 | 6404 | 6076 | 328 | 0 | 204/204 present |
| python 3.11 | N2 | 46 | 46 | 0 | 0 | 1/1 present |
| python 3.13 | non-N2 | 6404 | 6076 | 328 | 0 | 204/204 present |
| python 3.13 | N2 | 46 | 46 | 0 | 0 | 1/1 present |
| typescript 20 | Vitest | 155 | 155 | 0 | 0 | 7/7 present |
| typescript 24 | Vitest | 155 | 155 | 0 | 0 | 7/7 present |

Criterion verdicts, every job: nonzero executed count in each phase — met; no failed or
errored test — met; every eligible module present in its expected XML — met; every skip
reasoned — met: 327 capability omissions (`certified tuple unavailable on this host:`),
identical lists in both Python jobs, plus 1 non-capability skip matching the local baseline
(`tests/test_composite.py:190`, "the fixture's affects admits causal only; …"); no new skip
reason; TypeScript has no skips.

Local baseline for comparison (Task 1, certified tuple): non-N2 6353 passed + 1 skipped = 6354
at that revision (6404 cases now after the new route and CI tests), N2 46, Vitest 155.

Wholly skipped modules (capability-dependent): tests/test_holdings_windows.py,
tests/test_publication_engine_order.py, tests/test_publish_engine_order.py,
tests/test_publish_remote_engine.py.

Sibling revisions under test: atoms 935535a7275eeaa9d5ea9189b0b2163c021d4a95, nodes
ce159f2694c3149416f3d7e24ac0fedad5f4253d.

Job times: python 3.11 14.6 min, python 3.13 10.0 min, typescript 0.2-0.4 min (timeouts 30/10).

Capability-omission list: the 327 test IDs are in the attached `hosted-1-assessment.txt`
(largest modules: test_succession 43, test_permit_entry_points 41,
test_session_sharing_doors 38, test_holdings_boundary 37, test_session_publish_door 22,
test_holdings_acquire 21). This is the list AGENTS.md points certified-host focused runs at.

## Rechecked now

Visibility: verifiably/beliefs, atoms, nodes public. Runner: ubuntu-latest standard. Billing:
Actions budget $0 with prevent_further_usage (read earlier today, unchanged setting).

## Latency and halt reinventory

- beliefs-0f5112 (halt, test-latency; titan test-fast median 91.312 s > 90 s), parked by another
  session waiting on the user's choice of A/B/C. test-fast is in broad_targets, so once this
  activation lands on main the titan/test-fast obligation is retired (not applicable, never
  met). At Task 9 this task notes that retirement on beliefs-0f5112 with the landed policy
  revision and removes only its `halt` tag, leaving the incident's remaining scope to its
  owner and the user's A/B/C choice. Its options A (keep improving test-fast) and B (close as
  policy-retired) are compatible with activating now; option C (fix test-fast under enabled
  policy first, then rebuild this packet) would mean holding this activation.
- No other open test-latency or halt task.

## Deferred items

Four minor (deferred) final-review items (two route tests that could be sharper, two stale
"hook prices the whole hook" comments, an untested spaced Vitest path) are in the attached
execution-ledger.md; none changes behaviour.

## After activation (Task 9)

Verify from the main checkout: `just test-one tests/test_front_door.py -k test_full` records
`ran`; the activation push's `hook-pre-push-fast`, `check-code`, `test-push` rows (rev = short
merge SHA) show check-code and test-push `skipped` with null outcomes; the activation push's
hosted run meets the same criteria (assessed into hosted-2/). Then notes on ops-39bff6 and
ops-56aab7 (regret review 2026-11-28), artifacts or derived counts attached, close-out.

## Rollback

Set `automatic_broad = true` and `ci_suite_refs := "refs/heads/main"`, update the same guide
lines, commit, and push on approval; record `policy: enabled at <landed RFC3339-UTC> revision
<full-sha>` on beliefs-067a8d. The widened workflow may stay.
