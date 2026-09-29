# Focused checks and N2 audit reliability

## Problem

Five testing ideas concern catching invalid audit evidence and boundary regressions
within the focused development loop. Goal: `beliefs-287026`. The remaining decision
is whether a cheap collection preflight can detect stale N2 replacements before a
later conformance run discovers them.

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

Lean: retain the syntax task and measure option 2 before creating implementation
work. Module import alone does not establish pytest collection; collection alone
does not establish that a sabotage exercises its intended guarantee.

## Unanswered questions

- Which preflight catches the documented collection failure, and at what pilot
  cost? The agent executing `beliefs-aa9f88` answers with three bounded cases.
- Should the result join the syntax task, inform the existing N2-only audit
  proposal, or remain deferred? That agent recommends from the pilot; a later
  scope pass determines implementation work.
- What caused the transient failure? Unknown; reopen only on recurrence with
  captured output, command, source revision and host/certification state.

## Proposed decomposition

- `beliefs-aa9f88`: bounded preflight research; completion writes a finding note
  on waiting idea `beliefs-89542c` and updates this brief in the same commit.
- `beliefs-89542c`: **briefed**, remains an idea pending that result.
- `beliefs-7ab5c4`: **scoped**, P3/s/mid/direct; fail on missing or ambiguous
  portable override targets while retaining legitimate repeated rows.
- `beliefs-95f461`: **scoped**, P3/xs/low/direct; document the four-module boundary
  check command through existing `test-one` and verify it.
- `beliefs-872a2a`: **proposed drop**, covered by `beliefs-d4dc85` at `7fd039f`;
  its status stays idea until disposition.
- `beliefs-15946f`: **shelved** until the world-view acceptance failure recurs
  with captured diagnostics. Preserve the original observation.

No implementation or new audit gate is authorized by this brief.
