# Focused checks and N2 audit reliability

## Problem

Five testing ideas concern catching invalid audit evidence and boundary regressions
within the focused development loop. Goal: `beliefs-287026`. The bounded pilot
below establishes that named-check collection detects the
reported stale replacement. The remaining decision is where that preflight belongs
and what cost it adds across the existing N2 inventory.

## Current behaviour and evidence

Inspected main at `7fd039f` on 2026-09-29; this pass did not run the test suites.

- `python/tests/arm_staleness.py::stale_arms` counts matches of `before`; it does
  not validate substituted source. Cut 32's results (§3.2–3.3) record cut 20's
  syntactically valid D8a replacement breaking fixture import after the domain
  parser gained `edges`. The N2 audit already rejects uncollected checks; the gap
  is earlier detection, not an audit treating collection errors as success.
- `python/tests/test_n2.py` has one explicit P9 override, introduced at `6b392e8`.
  It applies that override by row over a tuple; it does not construct a dict from
  all arms. Static inspection finds one P9 declaration across the four portable
  declaration modules. Repeated rows are legitimate, even within one cut. The
  captured count-assert suggestion is therefore unsuitable; guard the number of
  targets of each portable override instead.
- `7fd039f` / `beliefs-d4dc85` supplied timed `just test-one` with a documented
  Vitest command override. It also accepts multiple Python module paths. The
  TypeScript missing-recipe idea is covered; boundary selection needs guidance,
  not another recipe. Cut 35's execution ledger records the missed Task 4
  boundary regression and its fix at `b065711`.
- Cut 34's results record one transient world-view acceptance failure followed
  by three passing runs. The idea has no later recurrence note; cause is unknown.

## Constraints

Preserve frozen declarations and historical cut bodies under the frozen guard
doctrine (`docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`).
Respect historical source pins, installed `nodes` arms, and certified-host limits.
Use copied packages for sabotage, and the timed test front door for checks.

`beliefs-1b0827` already owns shared syntax validation. `beliefs-e35dee` owns the
broader vacuity-detection question, and `beliefs-f64cf1` owns N2 cost and
placement (`beliefs-d3882f` was dropped into it on 2026-09-29). Do not duplicate
them or change full-gate coverage here.

## Alternatives

1. **Parse substituted source only.** Cheap and already scoped in `beliefs-1b0827`,
   but cannot establish that a syntactically valid replacement still collects.
2. **Import or collect selected sabotaged checks.** Could detect the D8a failure
   earlier; import context, fixture loading and cost need a bounded comparison.
3. **Rely on full sabotage audits.** Stronger evidence, with cost and placement
   already tracked by the existing N2 tasks.

Recommendation after the bounded pilot: retain parse validation in `beliefs-1b0827`
and take named-check collection into `beliefs-f64cf1`'s N2 cost/placement decision.
Direct module import adds no detection for the reproduced D8a case. Do not add an
always-on collection gate from this small sample. Collection does not establish
that a sabotage exercises its intended guarantee; `beliefs-e35dee` retains that
separate vacuity question.

## Unanswered questions

- Collection caught the documented failure; parse and direct import missed it.
  This pilot measured 1.07–2.37 seconds per collection process, not inventory-wide
  or steady-state cost. A later scope pass uses this evidence to decide whether
  to extend the N2-only proposal; no rollout is included here.
- What caused the transient failure? Unknown; reopen only on recurrence with
  captured output, command, source revision and host/certification state.

## Proposed decomposition

- `beliefs-aa9f88`: **completed** bounded preflight research; findings below and
  on `beliefs-89542c` enter the same result commit.
- `beliefs-89542c`: **briefed**, remains an idea ready for a later scope pass
  using the measured collection result.
- `beliefs-7ab5c4`: **scoped**, P3/s/mid/direct; fail on missing or ambiguous
  portable override targets while retaining legitimate repeated rows.
- `beliefs-95f461`: **scoped**, P3/xs/low/direct; document the four-module boundary
  check command through existing `test-one` and verify it.
- `beliefs-872a2a`: **proposed drop**, covered by `beliefs-d4dc85` at `7fd039f`;
  its status stays idea until disposition.
- `beliefs-15946f`: **shelved** until the world-view acceptance failure recurs
  with captured diagnostics. Preserve the original observation.

No implementation or new audit gate is authorized by this brief.

## Bounded preflight pilot — 2026-10-02

`beliefs-aa9f88` compared exactly three copied-package mutations and three
probes, in `.worktrees/n2-preflight-pilot`, based on integrated main `3a59054`
and claim commit `7414bc2`. The nine sequential calls took **13.96 seconds**
including copy preparation, process launch and first-use dependency hydration.
No full-arm sweep, gate rollout, or durability test was run. All original package
file hashes matched afterward; frozen declarations and live source were untouched.

| copied D8a case | ast.parse exit / wall seconds | direct module import exit / wall seconds | named-check collection exit / wall seconds |
|---|---|---|---|
| Current valid replacement | 0 / 4.935 | 0 / 0.861 | 0 / 2.371 |
| Unclosed _fields call | 1 / 0.789 | 1 / 0.804 | 4 / 1.074 |
| Valid replacement omitting edges | 0 / 0.767 | 0 / 0.820 | 4 / 1.441 |

The valid control uses the owning live guard's D8a replacement, not pristine
source: its parser intentionally accepts `kinds` and `relations`, while preserving
all current optional fields. It collected exactly the named test. The syntax
case replaces the same unique block with an unclosed `_fields(` call. The stale
case drops only `edges` from the valid replacement, retaining `estimands`; this
is a faithful current-tree reproduction of cut 32 §3.2–3.3, without unrelated
historical dependency changes.

The stale module imported from the copied package successfully. Collection
loaded acceptance conftest, then profiles.py and biology-fixture.yaml, and refused
`MalformedContract: unknown field(s) edges`. The syntax case refused `SyntaxError`
during collection. Both returned pytest/front-door exit **4**, meaning no named
check executed. These are invalid audit inputs, not successful sabotage kills.

Each case copied the existing beliefs package with `shutil.copytree`, excluding
bytecode caches; each replacement's before-block matched exactly once. Each probe
used a fresh process with `PYTHONPATH` pointing to that copy's parent. Parse used
`ast.parse` on copied contract/domain.py. Import used
`importlib.import_module("beliefs.contract.domain")` and asserted that its resolved
file was the copied module. Collection used exactly:

```text
just test-one --collect-only tests/acceptance/test_facet_acceptance.py::test_d8_contributions_compose_without_collision
```

Parse/import ran a temporary stdlib probe through the same timed front door:

```text
just --set one_cmd 'cd python && uv run --frozen python /tmp/beliefs-n2-preflight-probe.py' test-one parse COPY_PACKAGE
just --set one_cmd 'cd python && uv run --frozen python /tmp/beliefs-n2-preflight-probe.py' test-one import COPY_PACKAGE
```

The copied package cases, results.json and nine complete logs are retained under
.worktrees/n2-preflight-pilot/.work/n2-preflight-pilot. They are experiment inputs,
not new repository gates. The first parse invocation's 4.935-second wall time
includes creation of the locked Python environment and installation of 65 packages;
uv reported cross-filesystem hardlink fallback to copy. Its inner parse took
0.00676 seconds; the control's direct import took 0.05778 seconds internally.
Later parse/import front-door invocations took 0.767–0.861 seconds. Collection's
valid-control pytest phase itself took 0.29 seconds; the table includes the front
door and process overhead. These are nine single observations on a warm host,
not medians, a benchmark campaign or a prediction for all arms.

Environment: CPython **3.13.12**, kernel **7.2.2-arch1-1**; canonical worktree
on `/dev/sdb1`, ext4 `rw,noatime,data=ordered`. The front door supplied
`host-budget run`. Collection imported acceptance machinery but did not execute
its fixtures or probe the certified durability tuple. This evidence therefore
establishes collection behavior on this environment only. No capability refusal
was suppressed or converted into a skip.

The original domain module's input SHA-256 is
`1264485f63cfd44f126fd6c28fef302bae5f3e8db38888a3d586de9bf4b08707`;
the owning cut20 guard SHA-256 is
`de7d1bfee021d166f7197ba5063876e9c2ae6923ce1e556d09f292745a5aa3f0`.
The scope remains three cases and the arm's one named check.

Acceptance criteria for a later scoped preflight:

- Keep the existing exactly-one-before-site check and parse validation; syntax
  failure refuses the arm before a runtime audit.
- Collection resolves every declared named check against its sabotaged copy,
  preserving the audit's fixture/plugin/environment context. Zero collected
  tests, missing nodes, and collection/usage errors refuse as invalid or
  uncollected; they never count as sound or as an intended test failure.
- Demonstrate that the current D8a control collects, the syntax mutation is
  refused, and the valid stale-edges mutation passes parse/import but is refused
  during collection. Verify copied-package resolution and untouched source.
- Keep import alone out of the detection path: this pilot shows it misses the
  relevant fixture-dependent failure. Collection can still miss lazy imports,
  fixture setup failures, vacuity and incorrect runtime assertions; retain the
  full baseline/audit verdicts owned by the existing N2 and vacuity tasks.
- Measure incremental inventory cost and duplication with the existing audit in
  `beliefs-f64cf1` before deciding placement. This sample supports a focused
  preflight when an arm changes, not a universal cost bound or a new always-on
  fast-suite gate. `beliefs-89542c` remains an idea for that scope decision.
