# Publication packet — beliefs-067a8d (Task 7)

Approval asked: push exactly `d6dab00165bf520bb61215e309d2847af90c0978` to origin main, with
`git push origin d6dab00165bf520bb61215e309d2847af90c0978:refs/heads/main`. This publishes the
policy-enabled split and the widened workflow. It does not activate policy-off: no `.tt.toml`
is in this revision and `ci_suite_refs` stays `refs/heads/main`. Activation needs a separate
approval on the activation packet after this push's hosted run is assessed.

## What the push publishes

origin/main is `49c39ab` (fetched just now). `origin/main..d6dab00` is 83 commits: 63 are
`chore(tasks)` record commits, the other 20 are listed below. Record commits made in the main
checkout after `d6dab00` (this packet's attachment, the park) stay local until a later approved push.

```
d6dab00 merge: adopt tt test execution policy split and widened CI (beliefs-067a8d)
70385c4 test(ci): pin the full suite to the two package suites CI carries
c929e95 test(ci): pin CI suite selection to the local suites
79098f3 docs: describe the split gates, policy and certified-host routes
9589483 ci: run every branch with forced tt and durable coverage evidence
27ffe19 feat(hooks): warn when policy skips an uncovered push suite
e97b70c feat(justfile): split hooks into protected hygiene and broad children
0a85a27 test(front-door): run hook and focused routes in an isolated fixture checkout
5b8b881 docs(spec): record test policy design review history
b2ead49 docs(plan): fold plan review round 3 minors
0d142f8 docs(plan): bound published commits and separate branch and main policy state
ab1f9a6 docs(plan): pin approved push commits, physical-path runs and fixture details
224c799 docs(plan): plan the beliefs test execution policy adoption
68fa37f docs(spec): separate gate evidence and the publication packet in test policy design
5237cb7 docs(spec): address spec round 3 for test policy adoption
2cee097 docs(spec): address spec round 2 for test policy adoption
e2927dd docs(spec): address spec round 1 for test policy adoption
60b6487 docs(spec): design beliefs test execution policy adoption
b77990d chore(tools): vendor tt version 9
405f249 chore(tools): vendor ops-check version 16
```

The two vendoring commits (405f249 ops-check v16, b77990d tt v9) predate this task's work and were unpushed on main.

```
 .githooks/pre-commit                               |   3 +-
 .githooks/pre-push                                 |  33 +-
 .github/workflows/ci.yml                           |  75 +++-
 AGENTS.md                                          |  12 +-
 .../plans/2026-11-01-test-execution-policy.md      | 280 ++++++++++++
 .../2026-10-31-test-execution-policy-design.md     | 484 +++++++++++++++++++++
 justfile                                           |  85 +++-
 python/README.md                                   |  10 +-
 python/tests/route_fixtures.py                     | 162 +++++++
 python/tests/test_ci_workflow.py                   | 252 +++++++++++
 python/tests/test_front_door.py                    | 339 ++++++++++++---
 tools/ops-check                                    | 276 ++++++++++--
 tools/tt                                           |  13 +-
 13 files changed, 1888 insertions(+), 136 deletions(-)
tasks/:  29 files changed, 744 insertions(+), 4 deletions(-)
```

## Delivery revisions

- Shared authority: ops design `docs/specs/2026-10-29-test-execution-policy-design.md` at `469140a`; vendored `tools/tt` version 9.
- Adoption spec `docs/superpowers/specs/2026-10-31-test-execution-policy-design.md` (accepted `68fa37f`), plan `docs/superpowers/plans/2026-11-01-test-execution-policy.md` (accepted `0d142f8`, minors folded `b2ead49`).
- Final review: round 1 with fixes (Important 1 fixed in `c929e95`), corrective re-reviews accepted (`70385c4`). Four minor (deferred) items in the attached execution-ledger.md.

## Runner, timeouts, visibility, billing (rechecked 2026-11-01)

- Runner class: `ubuntu-latest`, standard hosted Linux. Timeouts: Python jobs 30 min (slowest observed run 15.1 min), TypeScript jobs 10 min.
- Visibility: verifiably/beliefs public, verifiably/atoms public, verifiably/nodes public (default branch main for each). `main` has no branch protection.
- Billing: standard runners are free for public repositories. The organization's Actions budget reads `budget_amount: 0`, `prevent_further_usage: true` (alerts to khughitt), so paid overage is blocked. October usage for beliefs: 597 Linux minutes, net $0.00 (fully discounted). No billing setting was changed.

## What the new workflow runs

- Triggers: push on every branch (`branches: ["**"]`), pull_request (fork PRs only, by job condition), workflow_dispatch. Concurrency `${{ github.workflow }}-${{ github.ref }}` with cancel-in-progress.
- Job env `TT_FORCE: "1"`; both matrices and the atoms/nodes sibling checkouts unchanged; `VERIFIABLY_UNCERTIFIED_HOST=1` on `just ci-python` as before.
- Evidence: per job, a module inventory (beliefs, atoms and nodes revisions; eligible modules; manifest) and JUnit (`pytest.xml`, `pytest-n2.xml`, `vitest.xml`), checked by an always-run step and uploaded as 30-day artifacts.

## Hosted acceptance criteria (assessed on this push's run, Task 8)

Per matrix job: nonzero executed count in each phase (non-N2, N2, Vitest); no failed or errored test; every eligible module present in its expected XML; every skip reasoned, with capability skips (`certified tuple unavailable on this host:`) listed by test ID and the rest matched against the local baseline (one skip: `tests/test_composite.py:190`); wholly skipped modules listed; sibling revisions recorded.

Pending until that run exists: per-job counts, module inventory, capability-omission list, wholly skipped modules, sibling revisions.

For reference only, run 41077923374 (main, 2026-10-30, old workflow): non-N2 6026 passed / 328 skipped, N2 46 passed, TypeScript 155 passed in 7 files; job times 14.5 / 8.2 / 0.3 min. Its limits: `-q` output gives no skip reasons, and it has no module inventory and no sibling revisions.

## Other state

- beliefs-0f5112 (halt, test-latency, filed 2026-11-01T10:00:05Z): titan test-fast median 91.312 s over the 90 s limit. This push does not change it; activation would retire that obligation (test-fast becomes a broad target) and lift only its timing halt.
- The local pre-push hook for this push takes the covered route (`hook-pre-push-fast`, policy enabled): hygiene, check-code, then test-push run locally first.

## Rollback

The workflow change reverts with `git revert -m 1 d6dab00` and an approved push. Policy is not activated, so there is no policy rollback at this stage.
