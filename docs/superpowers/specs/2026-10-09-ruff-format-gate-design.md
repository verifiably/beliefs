# ruff format in the gate — reformat once, enforce, keep N2 honest

**Date:** 2026-10-09
**Task:** `beliefs-a555d6` (follow-up `beliefs-ea5ec7` retires the exclude this adds)
**Measured against:** `main` at `9e3c67a`, ruff 0.16.1 (pinned by `python/uv.lock`)
**Doctrine:** `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`

This is hygiene, not a cut: it closes no guarantee row, adds no adoption-ledger row, and
adds no `test_recent_cut_acceptance.py` row. It touches the N2 machinery only through
the mechanisms the doctrine already provides.

## 1. Decision

The gate runs `ruff check` but not `ruff format`, so formatting drifts silently. The
user chose on 2026-10-09 to **reformat once and enforce** (option c). Rejected by the
user: keeping format out of the gate (a), and a ratchet whose exclude list holds every
drifted file (b).

## 2. What a reformat does today

Measured on a scratch reformat in this worktree, then discarded:

- `ruff format --check .` from `python/` reports 347 of 566 files drifted.
- **Freeze pins.** The 43 guard modules carry 942 pins on 57 targets, 53 of them under
  `python/`, all `.py`. 52 exist; `python/tests/n2_arms_cut25.py` is an
  already-falsified pin on a removed file. Formatting any of the 52 would falsify the
  pins on it.
- **Cited-not-run evidence without a pin.** Cut 4's guard (`test_n2_cut4.py`), its
  declaration (`n2_arms_cut4.py`) and its runner (`cut4_acceptance.py`) are
  cited-not-run evidence that doctrine §2 says is "never edited", but no pin names
  them. The surfaces of cuts 5, 8 and 10 are all pinned already.
- **Scalar declaration pins.** Outside the `FROZEN_*` tables, 21 guards (cuts 26–46)
  name their own arm declaration as a module-level `FROZEN_DECLARATION` path and pin it
  with a scalar `CUTN_DECLARATION_SHA256` (byte identity); cuts 27–30 also carry a
  `CUTN_DECLARATION_COMMIT`. `frozen_guards.pins_in` reads only the tables, so it misses them. All
  but one are table-pinned by a later cut as well. The exception is
  `python/tests/n2_arms_cut46.py`, the newest: formatting it changes its SHA-256 and
  fails `test_the_declaration_is_byte_exact_against_its_pinned_digest`. (Spec review,
  round 1, found this.) The scalar `CUTN_FROZEN_SHA256` constants hash Markdown cut
  documents at their freeze commits, which formatting cannot reach.
- With those 56 files excluded, `ruff format` rewrites 313 files (70 under `src/`). Every
  table pin holds. The live guards' static tests, i.e. all of them except the mutation
  audits and the live-check runs, pass 289 of the 290 selected, in under 3 minutes.
  The one failure is cut 14's `test_no_cut14_arm_is_vacuous_mixed_uncollected_or_stale`,
  an audit test the pilot's selection let through; it fails on the stale arms §3.3
  repairs. The static tests are where every scalar pin is enforced.
- **N2 arms.** 70 arms that live guards audit go stale, across 28 of the 38 live guards
  that audit the working tree (cut 6 audits a pinned historical tree and is unaffected):
  cut 46 has 7, cuts 11, 16 and 19 have 5 each, cuts 14, 28, 31, 32 and 35 have 4 each,
  and so on. 60 of them are declared arms no re-target covers yet; the other 10 are
  already re-targeted rows whose re-targeted text moved. Three arms of the cited guard
  for cut 10 newly go stale (`H1u1[0]`, `H2u1[3]`, `L7u1[16]`). The portable arms
  (`test_n2.PORTABLE_ARMS`) are unaffected.
- **Suppression comments.** The formatter moves five trailing suppressions off the line
  they suppress: two `# noqa: RUF022` (so `ruff check` fails) and three
  `# type: ignore[...]` (so pyright reports 3 errors), in `tests/verification_fixtures.py`,
  `tests/test_estimand.py`, `tests/test_profile_agreement.py` and
  `tests/acceptance/test_dataset_address_acceptance.py`.
- **Nothing else.** Apart from the three arm-staleness tests, `just test-fast` is green
  on the reformatted tree (6077 passed).

## 3. Design

### 3.1 The format exclude

`python/pyproject.toml` gains `[tool.ruff.format] exclude`, listing the paths, relative
to `python/`, of the **protected set**:

- every existing `python/` target of a freeze pin in any guard module
  (`frozen_guards.pins_in` over `frozen_guards.guard_modules`);
- every guard module's `FROZEN_DECLARATION`, the scalar declaration pin. This is read
  statically with `frozen_guards._module_constants`, made public as `module_constants`,
  the way `pins_in` reads tables;
- for every guard in `cited_not_run.CITED_NOT_RUN`, its guard module, its declaration
  `n2_arms_cutN.py` (under `tests/` or `tests/acceptance/`), and its runner
  `tools/cutN_acceptance.py`, wherever each exists.

Today that is 56 paths. `ruff check` is unaffected, because the table is format-only.
`[tool.ruff]` also gains `force-exclude = true`. Without it, a path passed explicitly,
as an editor's format-on-save does, would be formatted despite the exclude.

A portable test in `python/tests/test_frozen_guards.py` holds the exclude list equal to
the protected set, computed live, in both directions. It also asserts that
`python/tests/n2_arms_cut46.py` is in the protected set, so the scalar arm of the
derivation cannot silently drop out. A new freeze that pins a file, whether by table or by
`FROZEN_DECLARATION`, or a new cited-not-run ruling, fails the test until the exclude
names the file. An exclude entry
that nothing protects any more fails it too. The test reads the table with `tomllib`. It
compares sets, so the order of the list in the file is free; the file keeps it sorted.

The exclude is temporary. `beliefs-ea5ec7` makes pins hold modulo formatting, then
removes the exclude and this test together.

### 3.2 The reformat commit

One commit contains `uv run --frozen ruff format .` from `python/`, with the exclude in
place, plus the five suppression comments moved back onto the lines they suppress. Those
moves are the only hand edits in the commit, and they are needed for `just check` to
pass at that commit. The commit is generated, never merged by hand: if `main` moves
before landing, rebase the commits before it and re-run the command.

`.git-blame-ignore-revs` is created at the repository root and names this commit's full
hash, with a comment line. GitHub reads the file by name. Its header says that local
blame needs `git config blame.ignoreRevsFile .git-blame-ignore-revs`.

### 3.3 Re-targeting the live arms

Each stale live arm is re-targeted **mechanically**, in a way that preserves what it
mutates. Let `S0` be the module's source at the commit before the reformat, `S1` its
formatted source, and `(b, a)` the arm's audited sabotage. Then:

1. `b` occurs exactly once in `S0`; otherwise the arm was already stale and the tool
   refuses it.
2. `T1 = ruff_format(S0.replace(b, a))`, run with the module's own path as
   `--stdin-filename`, so the project configuration applies.
3. `(b', a')` is the smallest line-aligned differing region between `S1` and `T1`,
   widened one line at a time on each side until `b'` occurs exactly once in `S1`.
4. The derivation is accepted only when `S1.replace(b', a') == T1`, byte for byte.

The mutated program the audit runs after the reformat is therefore exactly the
formatted form of the program the cut discharged against. The pilot derived all 70 arms
this way, with no refusal and no mismatch.

This lives in a committed tool, `python/tools/retarget_formatted_arms.py`, because a
ruff upgrade that changes the house style reproduces the same drift.

- `derive --base <commit>` prints, as JSON, one entry per stale audited arm of a live
  guard: guard, index, row, module, `before`, `after`. It exits non-zero if any arm
  fails a condition above.
- `verify --base <commit>` re-derives every entry and checks that each guard's audited
  arm at that index now carries exactly the derived sabotage. This catches transcription
  errors, which the staleness test cannot: a wrong `after` that still matches would pass
  there.

The tool's portable test covers its derivation on a synthetic module:

- a statement that the formatter re-wraps;
- an `after` that changes how the surrounding statement wraps;
- a sabotage whose `before` sits inside one line;
- the refusal when `b` is not unique in `S0`.

The derived entries go into each guard by the idiom it already uses:

- **A guard that already has `_LIVE_SABOTAGES`** gets a new entry or a replaced entry.
  Re-targeting is row-keyed, except in cut 7, which keys by `(row, index)` because row
  `X10` has four arms and only `X10[20]` moved.
- **A guard without the table** gains one in cut 16's row-keyed shape:
  `CUTN_ARMS = tuple(replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if … else arm for
  …)`. That is 13 guards: cuts 13, 28, 31, 34, 35, 37, 38, 39, 41, 42, 43, 45 and 46. The
  pilot found no multi-arm row among them.
- **Cut 21** declares `RETARGETED_ROWS = frozenset(_LIVE_SABOTAGES)`, so it follows the
  table without a separate edit.

Every new or replaced entry carries the guards' existing comment form: "Repository
reformat, <the date of commit 5>: `ruff format` re-wrapped the anchored lines; derived by
`tools/retarget_formatted_arms.py`, so this arm applied to the formatted source is
exactly the formatted declared sabotage." Where the entry replaces an earlier
re-target, the earlier comment stays and this line is appended.

No declaration file and no `FROZEN_*` table is edited. With §3.1's scalar arm, every
canonical declaration is protected. What gets reformatted is the declaration plumbing:
`tests/n2_arms.py` (the `Arm` and `Sabotage` types) and the acceptance re-export shims,
such as `tests/acceptance/n2_arms_cut31.py`, whose content the guards check only by
substring. Formatting preserves the value of every string literal, so no declared arm
changes. Verification checks this (§5).

### 3.4 The cited-not-run arms

Cut 10's three newly stale arms are added to its `stale_arms` registry entry in
`python/tests/cited_not_run.py`, as a shared `MOVED_BY_REFORMAT` constant naming the
reformat commit. This follows the pattern of `MOVED_BY_WORKTREE_ROOT`. Nothing in cut 10's
surface is edited; the exclude keeps it byte-identical.

### 3.5 The gate

`py_check_cmd` in the justfile gains `&& uv run --frozen ruff format --check .`.
`ci-python` and `hook-pre-commit` both go through `py_check_cmd`, so CI and the commit
hook enforce it with no other edit. The AGENTS.md gate line ("`just check` (ruff,
pyright, …)") is updated to say ruff check and ruff format.

## 4. Commits and landing

On branch `chore/ruff-format-gate`, in order:

1. This spec and its plan.
2. The exclude and its test (§3.1). Green: format is not yet in the gate.
3. The tool and its test (§3.3).
4. The reformat (§3.2). `just check` passes. The arm-staleness tests are red at this
   commit, and only on the branch.
5. The re-targets (§3.3) and the cut-10 registry entry (§3.4), which name commit 4.
6. `.git-blame-ignore-revs`, the gate change, the AGENTS.md line, and `tasks done`.

The branch lands by `git merge --no-ff`, so no first-parent commit on `main` has stale
live arms. Before merging, re-confirm the task's precondition: every other branch is
fully merged into `main`, and no worktree besides this one holds unmerged kernel work.
On 2026-10-09 all four other branches were 0 ahead of `main`.

## 5. Verification

- `retarget_formatted_arms.py derive` and `verify` both exit 0 at commit 5, against
  commit 4's parent.
- For every guard module, `arm_staleness.declared_arms` is equal before and after
  commit 4, compared on `(row, module, before, after)` and `checks` for each arm.
  Formatting must not have changed any declaration's value.
- `broken_pins` over every guard is identical before and after commit 4. That includes
  the already-falsified pins the registry records.
- `tests/test_arm_staleness.py` and `tests/test_frozen_guards.py` are green, and so is
  `just test-fast`.
- `ruff format --check .` passes inside `just check`.
- **Static guard tests.** At commit 5, every live guard's tests pass, apart from its
  mutation audits and live-check runs. The command is `just test-one <live guard
  modules> -k "<selection>"`, with the module list and `-k` selection the plan fixes.
  Before the reformat this selection passed 290 tests in about 3 minutes. This is where
  every scalar pin is enforced, whatever its form. The portable pin test (§3.1) reads
  only the forms it knows, so this step is the backstop that catches the next unknown
  form.
- **Mutation pilot.** At commit 5, before the chain, run `just test-one
  tests/acceptance/test_n2_cut46.py`, the whole cut-46 guard. It takes every one of its
  36 arms through baseline, sabotage application, check execution and the `sound`
  verdict. 7 of those arms are re-targeted by this change, in a guard that gains its
  `_LIVE_SABOTAGES` table here. On 2026-10-09, before the reformat, it passed 13 tests in
  15 s. A failure stops the run there and is analysed before anything longer starts.
- **Audit soundness.** The newest runner's chain, `host-budget run -- uv run --frozen
  python tools/cut46_acceptance.py`, passes with every arm `sound`. It is run from
  `python/` on the certified host, through background Bash with `tee`. At cut 46 the
  chain reported about 3713 s of pytest time. It runs every live guard, which covers all
  28 affected ones, and it also runs the non-N2 acceptance modules the reformat touched,
  which the portable suite cannot see.
- `just gate` on the certified host, at the branch tip.

## 6. Rejected alternatives

- **`# fmt: off` / `# fmt: skip` around the 70 anchors in `src/`.** This would avoid
  re-targeting, but it puts test-machinery markers into kernel source permanently, and
  every future arm would want one.
- **Whitespace- or token-insensitive arm matching in `test_n2._sabotage`.** This would
  make arms indifferent to formatting, but the audit would then no longer apply what the
  discharged cut declared. It is a doctrine change with its own design, in the same
  family as `beliefs-ea5ec7`, and not this task's.
- **A one-shot scratch script for the re-targets.** The equivalence proof is the
  evidence for 70 arms, and the next ruff style change needs the same derivation, so the
  tool is committed with a test.
- **Formatting the cited-not-run cut-4 surface because no pin names it.** Doctrine §2
  makes cited bytes evidence whether or not a later cut pinned them.
