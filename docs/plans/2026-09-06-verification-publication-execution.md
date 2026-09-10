# Verification-publication execution record

**Date:** 2026-09-06
**Subject:** the subagent-driven execution of `docs/superpowers/plans/2026-09-06-verification-publication.md`
(spec `docs/designs/2026-09-06-verification-publication-design.md`, frozen cut
`docs/designs/2026-09-06-conformance-cut-21.md`, frozen at `41c9920`, digest
`eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5`), branch
`feat/verification-publication`, worktree `.worktrees/verification-publication`,
start `3969e05`.

This is the durable record of every ruling the controlling session made while
executing the plan, banked to a tracked path because the session's own
`.superpowers/sdd/2026-09-06-verification-publication/progress.md` ledger sits
under a git-ignored directory and is deleted with the worktree. A previous
slice in this repo (`writer-session`, cut 19) lost its rulings this exact way;
its ledger was later recovered and landed at
`docs/plans/2026-09-05-writer-session-execution-ledger.md`, whose convention
this record follows. The code history is the record of what landed; this
document is the record of *why*, and of what remains open.

## 1. What landed, and what did not

The plan has twelve tasks. **Tasks 0–11 landed** in this session, each behind
its own implementer/reviewer pass (and, where findings warranted, one or more
fix rounds), ending in a final whole-branch review and one fix wave. **Task
12 — the cut-21 discharge — was not executed.** Its step 1 requires the
`domain` lane's cut 20 to be discharged and merged into `main` before this
branch merges; at the time of execution `main` carried no cut-20 design, no
cut-20 results record, and no `python/tools/cut20_acceptance.py`, and the
`domain` lane's branch (`feat/domain-boundary`, tip `1d9d235`) was itself
undischarged. Task 12's step 8 also merges this branch into `main` — an
outward side effect the session declined to take unasked. **Nothing in this
record claims or implies conformance cut 21 is discharged.** The plan's own
Task 11 status line already says so: "cut 21 undischarged, awaiting the
domain lane's cut 20."

`docs/plans/2026-09-06-conformance-cut-21-results.md` — the discharge results
record — does not exist and must not be created until Task 12 runs.

## 2. Rulings, in order

Each ruling below is exactly as made during execution: what was decided, why,
and what it costs if the decision turns out wrong. Two of the controller's
own rulings (P6, P8) were later found wrong by the final whole-branch review
and corrected — see §4.

**Global rulings, made during preflight:**

- **P1 — the per-commit lint gate.** Reads as "adds no new diagnostic beyond
  the BASE baseline", not "reports zero". BASE (`3969e05`, measured from
  `python/`) carried 6 ruff diagnostics (5× I001 in
  `tests/test_reproduction_driver.py`, 1× C408 in
  `tools/reproduction/run.py:67`) and 9 pyright errors (all in
  `tests/test_reproduction_driver.py`: 5× `reportMissingImports` on
  `reproduction*` since `tools/` is not on pyright's path, 1×
  `reportArgumentType`, 2× `reportOptionalMemberAccess`). Fixing the pyright
  class would mean adding `tools` to pyright's `extraPaths`, newly
  type-checking all of `tools/` — real scope creep this slice does not own.
  *Cost if wrong:* 6 ruff + 9 pyright pre-existing diagnostics stay on the
  branch; visible in one command, cheap to clear separately.

- **P2 — sanctioned forward references.** Tasks 0–4 may commit while
  `tests/verification_fixtures.py` carries pyright "unknown import symbol" /
  "not a known attribute" diagnostics naming *only* the forward references
  the plan schedules for later tasks (`beliefs.stored.local_id` → T1,
  `beliefs.verify._basis`/`_restore_report` → T2,
  `beliefs.verify.publication_node` → T3,
  `beliefs.errors.VerificationTargetMismatch` → T5), since the plan mandates
  the fixture module land at Task 0 with these as lazy imports. Every one had
  to be gone by Task 5's commit. *Cost if wrong:* a handful of intermediate
  commits are not pyright-clean; the branch merges as a unit, so no reader of
  `main` ever sees an intermediate state.

- **P3 — Task 12 is not executed this session.** Blocked on its own
  precondition (cut 20 undischarged, unmerged) and on a stop-condition action
  (the branch merge). Tasks 0–11 land; Task 12 is reported deferred with its
  precondition named. *Cost if wrong:* the slice is banked but undischarged —
  exactly the state the plan's own Task 11 status line already declares.

- **P4 — how P1 composes with the plan's literal gate text.** Where a task
  step says `ruff check . && pyright → clean`, P1's reading applies. Where a
  step says the full `pytest` run passes, that is literal from Task 1 step 8
  onward — the only sanctioned red before that is
  `test_verification_identity.py`.

- **P5 — prior-cut N2 arms moved by this slice's edits.** When an edit makes
  a *prior* cut's N2 arm `stale`, the arm's `before`/`after` is updated to the
  landed source — never the source rewritten to match the arm. A `mixed`
  finding (a check still passes under its sabotage) is the opposite case:
  strengthen the check, never the arm. Both cases are named explicitly in
  every task report. *Cost if wrong:* a prior cut's sabotage stops proving
  its check, invisible until that cut's runner re-runs — contained by always
  naming the moved arm.

**Task 1 rulings:**

- `beliefs.assess.run_record` (`assess.py:99`) returned `RunValue(ref=…)`
  *bare* while `corpus.run_value` returns it *typed*, and Task 1 made `admit`
  compare the typed form. The implementer had instead patched the *test* call
  site to paper over the mismatch — against fail-early/no-silent-fallbacks.
  **Sent back:** `assess.run_record` spells the typed ref; the test
  workaround reverts. *Cost if wrong:* a one-line kernel change whose only
  callers are tests and `fixtures_cut3`; the suite would say so immediately
  if some caller wanted the bare form.
- The residual pyright `reportArgumentType` at `verification_fixtures.py:229`
  was a genuine new diagnostic, not a sanctioned forward reference — folded
  into the fix round with a narrow `# type: ignore`, no coercion (M11
  forbids repairing a malformed member by coercion).
- A fix-round edit to `python/tests/acceptance/test_n2_cut5.py` was
  **reverted**. That module is frozen, cited-not-run evidence
  (`pyproject.toml` excludes it from pyright with a stated reason; later cuts
  pin `n2_arms_cut5.py` by sha; no gate this slice must pass ever executes
  it). Editing frozen evidence to satisfy a run no gate performs is exactly
  what the freeze rule forbids. *Cost if wrong:* cut 5's module keeps a call
  spelling that would fail if ever run again — a documented consequence of
  the freeze, owned by whoever unfreezes it. (A sibling edit to
  `test_confinement_acceptance.py`, neither sha-pinned nor pyright-excluded,
  stood.)

**Task 2 rulings:**

- **P6 — the arm re-pin stands; the byte-freeze on `n2_arms_cut3.py` gives.**
  `n2_arms_cut3.py` pins verbatim `verify.py` source strings *and* is itself
  frozen byte-for-byte by cuts 15–19's `FROZEN_PRIOR_CUT_FILES`. Once this
  slice edits a pinned `verify.py` line, both cannot hold; P5 says the arm
  re-pin is correct. Repo precedent: `test_n2_cut11.py:46` records
  `n2_arms_cut3.py` deliberately absent after Task 4 of an earlier slice
  rebased an arm, carried unpinned through cuts 12–13 before cuts 15–19
  re-pinned it. **This ruling was later corrected by the final review — see
  §4, I1.** Two consequences were carried forward at the time: Task 10 must
  pin `n2_arms_cut3.py` (and, after Task 6 extended this ruling,
  `n2_arms_cut5.py` too) in cut 21's `FROZEN_PRIOR_CUT_FILES` at this slice's
  own re-pin commit, not at the plan's literal `5a02ca2`/cut-19 table; Task 12
  must record in the results record that cuts 15–19's pin no longer holds,
  and why.
- An Important review finding — the certification/citation restore path in
  `_restore_report` was never exercised by a passing test — was **fixed now,
  not deferred**. Traced forward: no later task closes the gap (Task 4's own
  certified-verification test recomputes with the *decoded* certification, so
  a field swap on restore would produce the same swapped object on both sides
  of the comparison and the audit would stay clean). A field swap in a sealed
  value type's restore path shipping undetected, in a slice whose whole claim
  is that a stored verification restores faithfully, is not acceptable; the
  plan's own Step 1 test list simply omitted the case, and the plan does not
  get to grade its own coverage. Fix: one round-trip test in `test_verify.py`
  over a certified *and* cited verification, asserting field-wise plus
  `decoded.basis() == verification.basis()`. *Cost if wrong:* one extra test.

**Task 6 ruling (P6 extended):**

- A *second* pinned arms file moved: `n2_arms_cut5.py`'s R20 arm, re-pinned
  under P5 to match a rewritten `_refuse_r20_contradiction` body. Consequence
  measured precisely: `n2_arms_cut3.py` is pinned by cuts 15–19;
  `n2_arms_cut5.py` is pinned by cuts 7–19 (thirteen cuts). Task 10 must
  re-pin **both** files at this slice's commits in cut 21's
  `FROZEN_PRIOR_CUT_FILES`; Task 12 must date both substitutions. Contained
  at the time: nothing in Tasks 0–11 runs the prefix chain that would hit the
  stale pins. (Also: an Important review finding this round was a
  **report-accuracy correction, not a code defect** — the implementer had
  misattributed 8 pre-existing stale N2 arms to the wrong files; the reviewer
  located the correct rows, and this record carries the corrected locations
  rather than spending a fix round on prose in a file that gets deleted with
  the workspace — see §5.)

**Task 7 rulings:**

- **P7 (load-bearing plan defect).** Design decision 17 permits two
  assessment records to carry one identity, and Task 5's
  `VerificationTargetMismatch` accepts a twin as a valid `verifies` target.
  But `belief.py`'s directional-vertex construction keyed strictly by
  identity, and `AggregationInput.__post_init__` refuses duplicate-identity
  vertices (and self-edges) — so a corpus containing a twin assessment could
  not form a belief at all, exactly what the plan's own Task 7 test exercised.
  **Decision:** the aggregation checks are correct and stay; the gap is a
  missing dedupe. Dedupe by identity when the vertex set is built, first
  occurrence wins (deterministic — proven later by the reviewer to follow
  file-path sort order, not insertion or set-iteration order), so the belief
  input stays deterministic. This widens the slice by one file
  (`belief.py`) not in the plan's list; the alternative (narrowing or
  dropping the plan's own test) would ship decision 17 half-implemented. *Cost
  if wrong:* one trivially revertible dedupe; if twins were meant never to be
  gathered together at all, the fix belongs in `gather` instead.
- **P8 (corrects P7).** P7's premise — "two records with one identity ARE the
  same assessment" — assumed facet agreement, which nothing enforced.
  `AssessmentValue.identity()` digests only `(spec, run, proposition)`;
  `outcome`, `interpretation_rule` and the optionals live in
  `facet_digest()` as free parameters with no cross-check on the write path.
  So a corpus could hold two identity-equal records that *disagree*. Before
  P7 that raised `MalformedRecord` (loud, for the wrong reason); after P7
  both cases silently succeeded and the belief reflected whichever record the
  corpus file sort happened to put first — a silent-fallback regression P7
  itself introduced. **Decision:** keep the dedupe, add the missing guard —
  compare `facet_digest()` on an identity collision; equal collapses
  (decision 17's genuine twin), unequal raises `MalformedRecord` naming the
  identity and both record ids. *Cost if wrong:* a corpus that today forms a
  belief over disagreeing twins would start refusing — the intended
  direction, and loud rather than silent. **This ruling was itself found to
  have a hole by the final review — see §4, C2.** Notably, the plan's own
  agreeing-twin test turned out not to build a facet-agreeing twin at all (it
  omitted the optionals); it had been silently relying on the first-wins pick
  P8 removes, and widening it into a genuine twin was direct evidence P8 was
  the right call.

**Task 8 rulings:**

- Review finding 1 (`confinement_fixtures.py` loading `conftest.py` by
  importlib path, to dodge a `sys.modules['conftest']` name collision with
  `tests/acceptance/conftest.py`) was **upheld and sent back**. The diagnosis
  was proven, but the implementer had rejected the lighter fix — moving the
  four shared constants into a plain module both scopes import normally — on
  a factually wrong basis (claiming it would require tracing every fixture
  caller; it would not, since re-importing a name into a module's namespace
  is indistinguishable from defining it locally). The chosen fix left a
  hidden double-execution dependency in a shared fixture module the whole
  portable suite imports. Fixed by extracting `confinement_constants.py`.
- Review finding 2 (`_fresh_process` used `check=True`, dropping the child's
  stderr on failure) was **fixed rather than deferred**, even though it was
  plan-mandated text: the plan's own Step 1 told the implementer to mirror
  `test_session_acceptance.py`, whose own fresh-process arm uses
  `check=False` plus an explicit stderr assertion. These are the durable
  arms whose failures are hardest to diagnose; local convention beats the
  plan's literal text here. *Cost if wrong:* three lines in a test helper.

**Task 9 rulings:**

- Pyright rose 9 → 11, then 11 → 12 across this task, and both rises were
  **accepted**. Verified from `python/`: every new error is
  `reportMissingImports` on `reproduction*` in
  `tests/test_reproduction_driver.py`, the same class as the 9 pre-existing,
  forced by the plan's own test code importing `reproduction` while `tools/`
  stays off pyright's path (verified out of scope: adding it produced 1625
  errors elsewhere). New baseline for Tasks 10–11: ruff 6, pyright 12.
- Findings 1–2 from Task 9's review were **code fixes, sent back**:
  `close.evidence_for`'s new `RuntimeError` on a stored spec that fails to
  restore had no test proving it could fail (against N2); and a local
  variable shadowed a module-level `findings` import — harmless today, a live
  footgun for the next edit. Findings 3–4 were **report-accuracy
  corrections, not code changes**: the implementer's cited precedent for a
  manual `target.yaml` patch (see §5, the mm30 driver residual) was only
  loosely analogous, not a real precedent, and the report had to stop framing
  a genuine driver gap as sanctioned; a "permanently dead code" claim about
  two `belief.py` checks was unsupported and withdrawn.

**Task 10 ruling:**

- **P6 discharged concretely.** `n2_arms_cut3.py` and `n2_arms_cut5.py` are
  pinned in cut 21's `FROZEN_PRIOR_CUT_FILES` at `1e92471` — verified as the
  true last-touch commit for both — rather than omitted (cut 11's precedent
  for an earlier slice). Pinning keeps the freeze meaningful for cut 21
  forward instead of leaving those two files unguarded the way cuts 12–13
  once were.

**Task 11 ruling:**

- Both Important review findings were **fixed rather than deferred**: the
  glossary's new `Published verification` entry carried no source citation
  while every sibling entry does, breaking the file's own convention in the
  document a reader consults first; and the guide's substituted sentence read
  as self-contradictory ("what is not built here … is implemented …") and had
  dropped the original clause's link to the design. *Cost if wrong:* two
  sentences in guide docs, trivially revertible.

**Post-final-review ruling:**

- **P9 (the P6/I1 residual — see §4).** Cuts 7–13's pin tables are **not**
  fixed in this branch; this is surfaced to the human rather than chased
  further. The final fix wave found the true scope was 13 pin tables, not the
  5 originally dispatched for; it fixed 14–19 (14 was forced, since the fix
  wave's own C1 edit to `test_n2_cut5.py` moved a file cut 14 pins by
  content). Cuts 7, 8, 9, 11, 12, 13 each need a one-line re-pin; **cut 10 is
  structurally blocked** (see §5). *Reasoning:* the pin breakage is an
  unavoidable consequence of doing this slice at all — the rule is fix the
  arm, never the source — and nothing in this branch needs those tables green
  today: the portable suite is green, and cut 21's own chain cannot run
  regardless while cut 20 does not exist. Chasing a 13-table cascade into
  other lanes' frozen cut records, with one node that cannot be fixed without
  breaking a newer cut's content pin, is a bigger decision than this slice's
  remit and turns on how the maintainer wants frozen evidence handled. *Cost
  if wrong:* the discharge task inherits six mechanical re-pins plus one
  genuine design question, all named here rather than discovered cold.

## 3. Per-task outcomes

Every task's review cleared (with fix rounds where findings warranted) before
the next task began.

| Task | Commits | Review |
|---|---|---|
| 0 — shared verification fixtures | `3969e05..2fbb83d` | clean |
| 1 — one spelling for the assessment's run member | `2fbb83d..7f99bfa` (`b047b77`, `7f99bfa`) | clean after 1 fix round |
| 2 — the stored verification's reader | `7f99bfa..7771484` (`21d98fa`, `6b325e5`, `7771484`) | clean after 1 fix round |
| 3 — the publication projection | `7771484..9e91689` | clean |
| 4 — scope, rule, scope rule and report recomputed | `9e91689..2eced2d` | clean |
| 5 — forgery refused before the intent | `2eced2d..041c7b6` | clean |
| 6 — the stored analysis-spec builder and reader | `041c7b6..1e92471` | clean |
| 7 — admission over records read back (belief moves with the record) | `1e92471..4c3830d` (`69eb235`, `4c3830d`) | clean after 2 fix rounds |
| 8 — verification publication through an attended session (V1, V2, V3, V5) | `4c3830d..d4a23de` (`bf2458e`, `d4a23de`) | clean after 1 fix round |
| 9 — the reproduction driver publishes and reads 10b from the corpus | `d4a23de..f2aefd5` (`392643f`, `f2aefd5`) | clean after 1 fix round |
| 10 — N2 arms, the cut-21 audit and the runner | `f2aefd5..804cfac` | clean |
| 11 — bank the implementation (status, dated notes, guide, glossary) | `804cfac..331c534` (`66fe3c2`, `331c534`) | clean after 1 fix round |
| 12 — discharge after cut 20 merges | **not executed** — see §1, Ruling P3 | — |

## 4. Final whole-branch review and fix wave

Dispatched over the whole branch diff, merge-base `74a5938..331c534`, in six
passes, proving every finding with a probe rather than arguing it. It
returned **2 Critical, 5 Important**, and it demonstrated that two of the
controller's own rulings were wrong.

- **C1 — three durable acceptance modules were broken** by Task 1's
  `AssessmentValue.run` bare / `RunValue.ref` typed contract change, invisible
  to the 3737-pass portable measurement because `pyproject.toml` sets
  `addopts = "-q --ignore=tests/acceptance"`. Task 1's call-site sweep had
  stopped at `python/tests/`, fixing only the one acceptance file that
  happened to get run. Broken: `tests/acceptance/test_deletion_acceptance.py`
  (three asserts, inside cut 21's chain via cut 18's `PHASE_MODULES`),
  `tests/acceptance/test_durable_records.py` (a frozen check cited by
  `n2_arms_cut4.py`), `tests/acceptance/test_n2_cut5.py`.
- **C2 — Ruling P8's guard had a hole**, reproduced directly: the dedupe+guard
  ran over `directional`, which `belief.py` had *already* filtered to
  non-zero `OUTCOME_SIGNS`. An identity-equal pair disagreeing *across* that
  directional boundary — `supported` vs `inconclusive` — never reached the
  guard at all. The controller's own P8 test had only exercised
  supported/refuted, which is exactly why the hole survived. Fix: move the
  guard before the directional filter.
- **I1 — Ruling P6's consequence was live, not deferred, as claimed.** Five
  prior cuts' freeze pins fail *today* (two verified by direct run), and cut
  21's chain does reach all five via cut 17's `PHASE_MODULES` — the
  controller's belief that nothing in Tasks 0–11 exercises the chain was
  wrong for the freeze-pin tests specifically. House remedy already
  established by this repo's own merge-base commit `74a5938`
  ("re-pin cuts 17 and 18 to the rewritten twins…"): re-pin the affected
  tables and add dated citation amendments.
- **I2** — `admission.py`'s run-mismatch message printed one side bare and
  the other typed, producing a misleading message in exactly the debugging
  situation this slice exists to serve.
- **I3** — `test_inertness.py`'s `admitted_scenario()` no longer admitted
  (same bare/typed shape as C1); a frozen guarantee row's arm still passed,
  but only because both sides of its assertion were now the same refusal —
  vacuous.
- **I4** — `belief.py`'s new P8 raise made `evaluate` partial against its own
  precedent (a sibling cross-corpus contradiction returns `Refused(...)`
  rather than raising); should return `Refused` too, keeping the function
  total.
- **I5** — `tools/cut21_acceptance.py` is entirely unexercised: see §5.

Also corrected in the same review: the controller's claim that cut 21's
prefix chain terminates at cut 14 was wrong (it terminates at cut 17), and its
belief that `test_n2_cut5.py` was never executed by any gate was wrong (it is,
by `tools/cut5_acceptance.py`, which feeds cuts 7–13) — the Task 1 `test_n2_cut5.py`
revert ruling rested on both facts and neither held, though the file was left
correctly frozen regardless per the freeze rule.

The final review also triaged the deferred minors accumulated across all
twelve tasks: none blocked merge; one (a `facet["report"] = None` vs
absent-key parametrize gap from Task 2) was promoted into the fix wave, and
three cheap one-liners were folded in alongside it.

**Fix wave** (one subagent, all findings): `205e5f7` (C1), `26cfcb1`
(C2 + I4), `1e9011a` (I2 + I3), `ee48f2e` (verify one-liners, the promoted V6
case, I5's docstring/log fixes), `da6bab8` (I1, partial — see Ruling P9).
Verified afterward: portable suite 3739 passed / 0 failed; `test_n2.py` 38
passed; `test_n2_cut21.py` 7 passed, 25 arms sound; cuts 14–19 freeze and pin
suites green; ruff 6; pyright 12; designs corpus 14.

A `git add -A` from the fix wave briefly landed a stray commit (`d0717f4`) on
`main` in the main checkout, not this worktree. It was caught and reset;
verified independently afterward — `main` HEAD is the pre-session value,
the tracked tree is pristine, and the stray commit is dangling and
unreferenced. Root cause: `.gitignore` covers `.mm30-reproduction/` but not
the `-cut21` work-root variant this session used, which is what let `-A`
sweep it up; only residue was an untracked directory beside the main
checkout, not repo content.

## 5. Residuals handed forward

**Freeze-pin work.** Cuts 14–19 are re-pinned to this slice's rewritten
`n2_arms_cut3.py`/`n2_arms_cut5.py` twins and are green. Cuts 7, 9, 11, 12,
13 each need a one-line re-pin to `1e92471`. **Cut 8 needs two lines** — one
of which (`test_n2_cut6.py` pinned at `RENAME_COMMIT = "5a02ca2"`,
`test_n2_cut8.py:104,113`) was already broken at the merge-base and is older
debt with its own, unrelated cause, not this slice's doing. **Cut 10 is
structurally blocked**: `test_n2_cut17.py:48-53`'s `FROZEN_CUT10_SHA256` pins
`test_n2_cut10.py` by content, so amending cut 10's own table to re-pin its
moved arms would break cut 17's cited-surface guarantee — a genuine design
question (how the maintainer wants that conflict resolved), not a mechanical
fix, and left for the discharge task per Ruling P9.

**`tools/cut21_acceptance.py` has never been observed executing.** Its
`PREFIX_RUNNERS = ("cut20_acceptance.py",)` names a runner that does not
exist in this tree. `main()` reaches that name, fails to find it, and
**returns 1 before `probe()`, `cut_environment()`, `run_prefix()` or
`declared_accounting()` ever run** — none of the runner's own control flow is
exercised. The cut-21 audit's "7 passed, 25 arms sound" result came from
running `tests/acceptance/test_n2_cut21.py` directly (per the plan's own Task
10 step 4, since "the runner refuses until cut 20 merges"), never through the
runner. This is now stated explicitly in
`docs/superpowers/plans/2026-09-06-verification-publication.md`.

**`tests/acceptance/test_n2_cut5.py` carries 15 pre-existing failures**, all
verified identical at the merge-base `74a5938` and none this slice's doing:
four older-slice causes (`import_bundle(actor=…)`, retraction actor binding,
`note` entering through the coordination family door, and `permit.py:72`'s
empty-actor path) plus three sabotages (T2 ×2, C2) stale at the merge-base
and still stale.

**The mm30 driver does not reproduce end to end unaided.** Task 9's step 7
re-run completed only after four analysis parameters (`value_row`,
`value_row_symbol`, `group_separator`, `positive_level`) were hand-supplied
into the generated `target.yaml` — values no driver step writes, taken
verbatim from the frozen 2026-09-05 record. The resulting 10b JSON proves
step 10b reads the stored report correctly *once target selection is
complete* — it is not evidence the driver reproduces end to end. The gap
belongs to `select_target.py`/`type_target.py`/`hold.py`, none in this
slice's scope, and is a finding for the reproduction lane.

**Closed 2026-09-10 (`beliefs-efc32d`).** A new driver step, `analysis_inputs.py` (step 2a), now derives those keys itself: the symbol from the proposition's protein term, the row through the crosswalk the dataset record's `identity_context` names, the levels from the held file's header, and the separator and level order from the driver's checked-in `analysis-inputs.yaml`, which the header must agree with. Rebuilt unaided into `.work/reproduction/mm30-rebuild`, `target.yaml` was identical to the frozen 2026-09-05 file, the spec froze to the same identity `86aaa1a8…`, and the full path reached `clean-environment`, `passed`, `Admitted` and an equal 10a/10b re-derivation; the ledger is `docs/plans/2026-09-10-mm30-reproduction-rebuild-run/`.

**Deferred minors the final review triaged as shippable** (non-exhaustive,
by task): Task 0 — a `# noqa: RUF022` on `verification_fixtures.py`'s
`__all__`. Task 1 — three added `# type: ignore` comments beyond the brief's
literal text (`stored.py:398`, `test_stored.py:127`, `test_admission.py:509`,
plus `verification_fixtures.py`), non-behavioral. Task 2 — a dead defensive
double-check in `decode_verification`, reproduced verbatim from the brief; no
test distinguishing `facet["report"] = None` from an absent key (the report's
parametrize case was later promoted and closed in the fix wave). Task 3 — two
disclosed test-file deviations avoiding a ruff/pyright conflict in the
brief's literal text. Task 4 — a lost `{node.id}:` message prefix
(plan-mandated, cosmetic); a reordering of two independent failure modes,
untested before and after. Task 5 — no structural concern, just line growth
in `corpus.py`. Task 6 — `spec.py`'s restore-side member handling spread
across four places with no single manifest. Task 7 — a comment
misattributing what the dedupe protects (reworded in the same round it was
found, not deferred). Task 8 — n/a (both findings fixed, see §2). Task 9 —
`DerivationEvidence` imported from two different paths across the touched
files, harmless but inconsistent. Task 10 — the cut document's own §5 item 4
miscounts its sabotages as "twenty-three" where the true count is 24 (+ V3's
own = 25 implemented); worth correcting in the plan source if reused. Task
11 — the adoption ledger's `verification-publication` row still lists the
boundary as unbuilt; correct today (cut 21 is undischarged) and belongs to
Task 12 step 7's re-rank, not this session.

**Pre-existing repo conditions surfaced, none this slice's doing:** 8 N2 arms
were already stale at the branch point (rows S7×2, S8×2, R19 in
`n2_arms_cut{3,4,6,7,16}.py`, and T2×2, C2 in `n2_arms_cut3.py:897,907` and
`n2_arms_cut5.py:151,161,174,268`) — `tests/test_n2.py` stays green at 38
passed regardless, so whatever audit surfaces these staleness findings is not
the one the portable suite runs. And `corpus.py:559`'s `_ROOT_STATES` map is
process-global, keyed by root path, and is never evicted — when pytest's
retention policy deletes a passing parametrized case's numbered directory and
hands a later case the same literal path, `_root_state_for` serves the stale
state instead of opening a fresh corpus. Task 4's `test_audit.py` fixture was
given a uuid-scoped path as a test-side mitigation; the underlying kernel
property is out of this slice's scope and makes every path-keyed test fixture
in the repo quietly order-dependent.

**Plan errors implementers had to correct**, all carried into the results
record for Task 12: `beliefs.corpus.open_corpus` does not exist — the real
name is `beliefs.root.open_corpus` (Task 8); `close.evidence()` must be
`close.evidence_for(view)`, else the in-process spec silently returns (Task
9); Task 9 step 7's for-loop step order was wrong — `type_target`/`hold` must
follow `world` per each module's own docstring; the brief's stated
ruff/pyright baselines were each off by one (Task 9); and the frozen cut
document's own §5 item 4 sabotage count is off by one (Task 10, see above).

## 6. Measured final gates

All from `python/`, at `da6bab8`:

| gate | result |
|---|---|
| `uv run --frozen pytest` (portable) | **3739 passed / 0 failed** |
| `uv run --frozen ruff check .` | **6** diagnostics, all pre-existing at BASE |
| `uv run --frozen pyright` | **12** errors, all pre-existing, all in `tests/test_reproduction_driver.py` |
| `tests/test_n2.py` | 38 passed |
| `tests/acceptance/test_n2_cut21.py` (direct, not through the runner) | 7 passed, all 25 arms sound |
| durable acceptance module (Task 8) | 4/4 |
| cuts 14–19 freeze and pin suites | green |

## 7. Citation amendment — 2026-09-07

This section amends the record after the freeze doctrine it left open was ruled. It
rewrites nothing above; where it corrects a ruling it is the current one.

**C1's edit to `python/tests/acceptance/test_n2_cut5.py` is reverted, and cut 14's
content pin over that module is restored** from `f744c34d…` to `df589285…`, the hash cut
14's own results record §3 published and still publishes. Cut 5's guard is cited, not
run; editing it to carry a contract change put the code at odds with the discharge record
it pins, and Task 1's ruling — which reverted exactly this edit, on exactly this ground —
was right. The two facts §4 records as having undercut that ruling (the chain terminating
at cut 17, and `cut5_acceptance.py` executing the module) do not bear on it: an older
runner is a frozen command for the tree it discharged on, not a live gate.

**Ruling P9's "structurally blocked" is resolved, and its premise corrected.** Cut 10's
table is not repaired and needs no repair: a cited-not-run guard's pins are historical
statements, so cut 17's `FROZEN_CUT10_SHA256` and cut 10's own falsified pin now coexist
by rule rather than by deadlock. Cuts 7, 9, 11, 12 and 13 — live, and re-pinned in the
facet-contracts landing — were the whole of the mechanical remainder. Cut 8's two pins,
like cut 10's one, stay as they are.

**Cut 21's chain was never blocked by any of this.** §4's correction stands: the chain
roots at cut 17, whose inventory contains neither cut 8's guard nor cut 10's.

The doctrine, the registry that records the three falsified pins, and the checks that
hold the tree to all of it are
`docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`.
