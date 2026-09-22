# Conformance cut 38 — results

**Cut:** `../designs/2026-09-22-conformance-cut-38.md`
**Freeze:** `21ef347a0a7dbfd4acabeb996d17663384892dfa`; SHA-256 `4b06f8fe9d310bfde6766c7b9328575d0cc758d299f54ec493b783cf1214efc6`
**Declaration:** `python/tests/n2_arms_cut38.py`; SHA-256 `b3953f933ba06782d91153e447e3ee8dc1c50c7d97bfd71cd1a7dfa90eed380b`
**Subject:** the act-report remainder — the `audit` and `re-check` operations, and every supplied operation port bound to its writer
**Design:** `../superpowers/specs/2026-09-22-act-report-remainder-design.md`
**Plan:** `../superpowers/plans/2026-09-22-act-report-remainder.md`
**Discharged:** 2026-09-22 on `design/act-report-remainder`, through `b4d71dd`; reproduction recorded at `c723680`
**Runner:** `python/tools/cut38_acceptance.py`

## 1. What ran

The certified runner ran from the worktree `act-report-remainder`'s
`python/`, reached by its canonical path rather than through the
`.worktrees` symlink (§7), with its cut roots on the main checkout's
certified volume. The worktree's own volume is uncertified. Cut 38 chains **cut 37's** runner
(`PREFIX_RUNNERS = ("cut37_acceptance.py",)`), which retains the complete
live prefix back through cut 17's nineteen phases; cut 37's own chained
summary appears in the log ahead of cut 38's, confirming the prefix ran.
Cut 8 remains cited-not-run; cut 38 reads no cut-8 arm, re-targets no
prior declaration and repairs no prior guard.

The runner's two final lines, verbatim from the main checkout's
`.work/acceptance/cut38-runner.log`, are:

```text
declared arms: 14 (= 12 declaration units; 3 guarantee rows)
guarantee rows exercised: 3 (1 newly closed: T2; T5 and T6 re-read for the new kinds; T7 partial under cross-root-publication)
```

Its own phases were:

```text
[cut38 phase 2/3] test_act_report_remainder_acceptance.py
21 passed in 32.51s
[cut38 phase 3/3] test_n2_cut38.py
10 passed in 32.13s
```

The runner's exit status was not literally captured — the reaping wrapper
`detached.sh` does not persist its wrapped command's `$?` (§7, and the
filed follow-up). Exit 0 is established from the log instead: the
rows-exercised line above is printed only inside the runner's
`if result == 0:` branch, all three phases completed, and the full log has
zero `FAILED`, `ERROR` or `Traceback` matches across sixty clean pytest
summaries.

Every prefix phase passed. Every one of the twelve live checks resolved
and passed without sabotage; all fourteen mutations scored **sound**. No
unit was stale, vacuous, mixed or uncollected — `test_n2_cut38.py`'s ten
tests are where those verdicts are asserted, and they passed. T2-g homes
three arms; every other unit homes one. Each check below is in
`python/tests/acceptance/test_act_report_remainder_acceptance.py`:

| declaration unit | check | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|
| T2-e | `test_t2e_an_audit_closes_through_exactly_one_report_after_its_intent_and_the_evaluator_ran_between_durably` | resolved | sound | T2 closes |
| T2-f | `test_t2f_a_recheck_closes_through_one_report_and_its_operation_intent_precedes_every_holdings_intent_durably` | resolved | sound | T2 closes |
| T2-g (g1, g2, g3) | `test_t2g_root_selection_no_port_a_refused_append_and_a_foreign_store_begin_no_act_for_both_kinds_durably` | resolved | sound, sound, sound | T2 closes |
| T2-h | `test_t2h_each_kind_submits_exactly_one_fulfilling_execution_and_a_second_is_refused_durably` | resolved | sound | T2 closes |
| T2-i | `test_t2i_a_port_bound_to_another_root_is_refused_by_both_kinds_before_any_intent_durably` | resolved | sound | T2 closes |
| T2-j | `test_t2j_late_inputs_refuse_the_recheck_before_the_operation_intent_with_no_holdings_intent_and_no_read_durably` | resolved | sound | T2 closes |
| T5-d | `test_t5d_an_inconclusive_recheck_location_spells_untested_or_failed_by_whether_the_read_began_durably` | resolved | sound | T5 re-read for the re-check kind |
| T6-d | `test_t6d_cite_resolves_each_finding_in_evaluator_order_and_a_permutation_moves_the_identity_durably` | resolved | sound | T6 re-read for the audit kind |
| T6-e | `test_t6e_findings_differing_only_in_message_mint_equal_entries_and_one_identity_under_a_fixed_envelope_durably` | resolved | sound | T6 re-read for the audit kind |
| BI-1 | `test_bi1_the_evaluator_modules_define_no_write_entry_point_and_reach_no_primitive_durably` | resolved | sound | boundary invariant |
| BI-2 | `test_bi2_the_evaluators_read_runs_under_the_root_lock_after_the_intent_so_a_raced_write_lands_after_the_report_durably` | resolved | sound | boundary invariant |
| BI-3 | `test_bi3_the_session_routes_write_one_act_line_per_committed_transaction_and_name_the_session_actor_durably` | resolved | sound | boundary invariant |

T2-g and T2-j are each parametrized four ways, so the twelve unit
functions and three plain tests collect as the phase's **21 tests**.

The unit work that preceded the cut run passed on the certified tuple as
each task landed. Task 1's port binding: its six new tests, then **225
passed** over the focused capability and permit set, **526 passed** over
the wider regression set, and **15 passed** over the staleness and
frozen-declaration guards. Task 2's audit operation: **13 passed** in its
new module and **656 passed** combined with the permit, capability and
entry-point inventories. Task 3's re-check operation: **96 passed** in its
new module and **532 passed** over the three inventory modules. Task 4's
session routes: a RED run of `4 failed, 1 passed, 20 deselected` before
the routes existed, then **70 passed**, **532 passed** over the
inventories, and **25 passed** after the review fix. Task 5's acceptance
module: **21 passed** pristine, and 21 again under `-W error`. Task 6's
guards: **27 passed**, with the cut-38 fast loop at `9 passed, 1
deselected`. Pyright reported `0 errors, 0 warnings, 0 informations` and
Ruff `All checks passed!` at every code task. `tasks check` reported zero
errors at every task. No capability waiver or skip was used for the
discharge; `VERIFIABLY_UNCERTIFIED_HOST` was never set. The full
repository integration gate belongs to §6.

The new recent-cut entry is `(cut38, 38, (14, 12, 3))` and asserts the
guarantee-rows-exercised line above. That interface check mocks
subprocess execution; the actual chained run is the discharge evidence.

## 2. Accounting

**T2 closes in full.** Twelve declaration units comprise six against T2,
one against T5, two against T6 and three boundary invariants. The `audit`
operation (`beliefs/audit_operation.py`, `audit`) fixes the observer root
as the writer's own, checks port, authority and metadata before anything,
appends one `audit` intent, runs `audit_corpus` over the writer's own view
under the caller's hold and the root lock, and closes through one
act-report carrying one `subject-evaluation` entry per finding in the
evaluator's order; a clean audit's report has no entries. The `re-check`
operation (`beliefs/holdings/recheck.py`, `recheck_locations`) validates
every location, the store genesis, the observer, the instrument and every
standing set before the intent, appends one `re-check` intent, runs the
per-location `recheck` act as built with nothing held across the acts, and
closes through one report carrying one locator entry per location. A
supplied operation port is bound to its writer's root, authority and
profile or refused with `PortMismatch` before any intent. With these,
**every operation kind but `corpus-write` — reportless by design — opens
through a boundary and closes through exactly one terminal record: the `run`
where one is minted, the act-report otherwise.**

**The T table stays partial on T7 alone**, on its cross-root case, owned
by `cross-root-publication` (`beliefs-256f17`, tier 3). Cut 38 reads no
T7 arm and changes nothing about cross-root publication. T1, T3, T4, T5,
T6 and T8 are unchanged: T3 and T4, already closed, are exercised for the
new kinds by two plain acceptance tests that declare no unit and claim no
row; T5 and T6 are re-read for the instance the new kinds give them and
were already full.

`act-report-remainder` leaves the ledger's table and the roadmap's
boundary index in this record's commit. The global corpus is **188 of 216
guarantee rows closed, 28 open**, up one from cut 37's 187. The accounting
entry `38: ("conformance-cut-38-results §2", "T2", "")` in
`python/tools/roadmap_status.py` produces Appendix A; no row is reopened
or read in part at cut 38. The seventh off-path lane under roadmap rule 6
re-ranks nothing on the dogfood path: the first belief audits nothing it
must report and re-checks no holding.

Both `CONTRACT.yaml` copies and the TypeScript tree are unchanged.
`root.py` remains the one `atoms` importer: neither new module imports
`atoms` or names an engine type, and both reach the log only through
`CorpusWriter._append_operation_intent`,
`CorpusWriter._publish_operation_report` and `holdings/boundary.py`'s
`recheck`, all inventoried callers. **The write inventories were checked
in both directions.** Neither wrapper calls a write primitive directly, so
`WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and the `CASES`
inventory in `test_permit_entry_points.py` are unchanged and neither file
appears in the branch diff; and BI-1 asserts the other direction on the
certified tuple — `audit.py` and `world/audit.py` define no
`WRITE_ENTRY_POINTS` member and reach no write primitive, read through
`test_permit_boundary.py`'s own `primitive_callers`. No evaluator, act,
contract or stored codec changed: the `subject-evaluation` entry kind with
its `evaluation-finding` outcome and the `pure-look` entry kind with its
three outcomes have been spellable, storable and decodable since the
act-report slice landed. No oracle is amended, so `contract-cut` gains
nothing to freeze.

## 3. Evidence

### 3.1 Frozen evidence and corrections

Cut 38's body remains byte-exact to its freeze: `git diff` over
`docs/designs/2026-09-22-conformance-cut-38.md` between `21ef347` and
`b4d71dd`, the head the cut ran at, is empty; this record's own commit then
changes the `**Status:**` line and nothing else. Its
declaration remains at the SHA-256 above. No prior frozen declaration or
cut body differs from the pre-lane tree, and the staleness probe
re-targets nothing: cut 37's live guard stays chained as the highest live
runner, and every arm this lane declares lands on a line this lane wrote.

**Two corrections this record carries, both from spec decision 1 and the
cut document's §2.** The parent task record (`beliefs-86b150`) and the
prior ledger row named `audit.py`, `world/audit.py` and
`holdings/boundary.py` as surfaces the wrappers **land on**. They are
**consumed**, not edited: the two operations are new modules, and the
branch diff touches none of those three files. The cut document froze the
corrected wording ("consumed and not edited") and the task record carries
the correction as a note. Second, the ledger row's *unblocks* column read
"the T table in full"; it is corrected to **"the T table in full but for
T7's cross-root case"**, which is what closing T2 achieves and what the
spec §1 states. Neither correction changes a declared width, a unit or an
arm.

**A third correction, from the final whole-branch review.** The frozen cut
document's §1 says every operation kind opens through a boundary and closes
through exactly one act-report, and counts `run-attempt` among the six kinds
that already do; the current-facing statements this lane wrote carried the
same unqualified phrasing. `run-attempt` closes through the **`run`** where
one is minted — the boundary publishes the run's own plan as the fulfilling
record — and through an act-report only on the refusal path. T2's own row
states the rule the lane should have used: "the `run` where one is minted,
the act-report otherwise". Every current-facing statement of the claim on
this branch is qualified in those terms; the frozen §1 stays byte-exact and
is **superseded by citation here**. The correction changes no declared
width, no unit and no arm: T2's positive arm already reads a post-intent
attempt that mints no run, and negative (b) already reads the minted run.

### 3.2 Deviations and read-at-freeze choices

The cut froze before its new source sites existed, so every sabotage
`before` block was read from the implemented tree after Tasks 1–5 rather
than from the plan's illustrative text. Three arms — T2-f, T2-g3 and T2-j
— carry `before` spans wider than the plan's literal prose bound, because
a sabotage is one contiguous replacement and each of those rows' `after`
moves a line past an anchor outside the stated bound. Each span occurs
exactly once; the review re-derived each of those three as the minimal
contiguous span that makes its `after` expressible, checked all fourteen
arms for module, span and occurrence count, and proved by line-multiset
diff that T2-e, T2-g3 and T2-j are pure reorderings that delete no guard. Structural masking is impossible
regardless: the N2 harness copies the package per arm and applies exactly
one.

Task-level deviations, each gate-forced and each reviewed:

- **Task 2** did not add `LocatorEntry` to `boundary.py`'s `beliefs.report`
  import block when the plan said to, because Ruff's F401 flags it unused
  until its consumer exists. Task 3 added it with `_mint_recheck_report`.
- **Task 3**'s new test module gained pyright-forced scaffolding types and
  three `assert isinstance(..., PublishedObservation)` narrowings; the
  review confirmed all three are assertions, not `if` guards, so none can
  skip a check. `ruff --fix` reformatted the import blocks and renamed two
  unused unpacks; the numbered step comments the arms pin survived.
- **Task 4** widened a stale closed-set enumeration of `ScopedWriter`'s
  public methods from 15 to 17 names — a widening of an `==`, not a
  loosening — and first landed a `# type: ignore[union-attr]` in place of
  an assertion, corrected at `a60f82d` (§3.3).
- **Task 5** corrected the plan's import block, which Ruff rejects
  (ruling, §7), dropped an unused local and a stale `noqa`, narrowed a
  `pytest.raises(Exception)` to `pytest.raises(CitationRefused)`, and
  replaced a `dict(...)` call with a literal. This tree's Ruff preset is
  wider than `pyproject.toml` suggests — B017, C408, I001, F841 and RUF100
  are all enabled — which is worth knowing when a future plan spells test
  code verbatim.
- **Task 7**'s first commit was rejected by the pre-commit documentation
  hook for a literal absolute host path in the §17 draft; the addendum was
  re-spelled descriptively, as §16 does, and committed clean.
- **Task 1** added `root` at eight sites rather than the five fakes the
  plan named: two local `Port` classes in `test_corpus_write.py` that
  pyright flagged, and `LedgeredPort`, which is not a fake at all but
  production code in `session/routes.py`. The review confirmed both extra
  test edits were pyright-forced, not scope creep.

**One departure from the spec's own wording.** Spec decision 12 says the
reproduction exercises neither operation, and the §17 draft transcribed it
as "exercised only by `test_act_report_remainder_acceptance.py`". That is
false of the whole suite — `test_audit_operation.py`,
`test_holdings_recheck.py` and `test_session_routes.py` all call the
operations directly. The sentence was narrowed to what was actually
grepped (§7). Decision 12's substance is untouched: the *reproduction*
reaches neither operation.

**Final review.** Recorded at §6 when the whole-branch review and the
repository gate run.

### 3.3 Review findings and limitations

Every task was reviewed against the spec before the next began. Three
findings were Important, fixed in two commits:

- Task 4's `# type: ignore[union-attr]` at `test_session_routes.py`
  stood in for an assertion. It was replaced at `a60f82d` by
  `assert isinstance(outcome.entries[0].outcome, PublishedObservation)`
  immediately before the dereference. The implementer deviated from the
  finding's literal suggested import and was right to: see §7's name
  collision.
- The reproduction §17's "exercised only by" sentence, and a key-order
  question on its quoted `NoBelief` payload, fixed at `c723680`. The
  second was handed back as a question rather than normalized away, and
  the answer was traced to source: `state.save` writes with
  `sort_keys=True` while `rederive` prints the same dataclass in
  field-declaration order. Same payload, two transcriptions — not a
  serialization discrepancy, and so not a reproduction finding.

Limitations found or confirmed at review, none of which reopens T2:

1. **No world-scope audit operation** (spec §12.1). The audit is
   corpus-scoped because a `subject-evaluation` entry has no corpus
   member. Filed as an idea (§7).
2. **No scheduler**: the act-report design §4's sub-problem 6 stays
   excluded (spec §12.2).
3. **The audit report does not spell the corpus-state identity it
   judged**; the intent's chain position names it under decision 4 (spec
   §12.3).
4. **A re-check location's `detail` is dropped** from the entry; the
   holdings intent and the seam's own view keep it where they keep it
   today (spec §12.4). `result.detail` appears nowhere in `recheck.py`.
5. **The reproduction exercises neither operation** (spec §12.5, §4).

Narrower limitations the reviews recorded across Tasks 1–7, so this record
does not overclaim:

- The shared `closed()` helper the acceptance module inherits from cut 35
  proves that a fulfilling registration exists and that the report
  qualifies, but does not read the chain's final-state path back to the
  report. **This record's "closes through one report" and "`closed`" are
  scoped to that**: the tie between the chain's final state and the report
  is made by T2-h alone.
- BI-2's sabotage releases the caller's hold as well as the root lock,
  because they are one `with` statement, while the frozen §5 row names
  only the root lock. Inseparable without splitting the statement.
- T2-e's sabotage leaves a `# 4. Act:` comment trailing below the
  relocated append, describing nothing — unavoidable if the arm is to stay
  a pure line-multiset move.
- BI-1's evaluator loop lacks the `seen == evaluators` guard its wrapper
  loop has. Not vacuous today — both modules exist and resolve as
  expected — but asymmetric.
- The re-check's unit-level "reads nothing" is proven for `read_path`
  only; the foreign-store arm's refusal does follow an effect-free store
  genesis read the test cannot see. T2-j proves the acceptance-level claim
  from the seam's own `read_path` counter.
- The re-check's unit lock test proves nothing is held across the acts and
  that the hold brackets the close, but not that the close takes
  `writer._operation`; the sibling audit test pins that with an in-close
  probe, this one has none.
- `recheck.py`'s `zip(..., strict=True)` has no reachable failure mode,
  and `dict(standing)` raises an uncaught `TypeError` rather than
  `RecheckRefused` if `standing` is not a Mapping — its values are handled
  correctly, its container type is not.
- T6-e's check compares the two live reports' own identities, which the
  frozen row says are "not compared". The comparison is labelled and
  true — the identities differ, as T8 requires — but it is literally the
  excluded comparison.
- T2-g's `wrong-root` arm checks that the foreign writer has no act-report
  but not that the foreign root's chain is unchanged, as T2-i does.
- The audit's unit-level pre-intent parametrization omits a
  mismatched-authority or mismatched-profile port, an empty observer, an
  unencodable instrument and an unencodable actor; authority and profile
  have a second home in Task 1's own tests, and the acceptance units read
  the rest.
- Four port-shaped doubles still lack `root` — `_Port` in
  `test_permit_entry_points.py`, `KilledAfterAppend` in
  `test_run_persistence.py` and `CancelledBeforePublication` in
  `acceptance/test_intent_boundary_acceptance.py`. None is passed as
  `port=` to a primitive, so pyright is clean today; a future caller that
  passes one would have to add it.
- `fixtures_cut3.py`'s `MemoryPort.root` is a relative placeholder
  resolving against the process cwd — harmless while that port is only
  ever a writer's own, and never compared by `_require_bound_port`.
- The port refusal messages for authority and profile name neither side,
  unlike the root message beside them.
- The port binding has no test for a same-root-different-spelling port
  (which would prove `resolve()` earns its place), an equal-but-distinct
  `Authority`, or a port-less writer handed a valid supplied port.
- `audit_operation.py`'s `_now()` duplicates `holdings/acquire.py`'s byte
  for byte, deliberately, to avoid a cross-wrapper import. Hoist it if a
  third operation module arrives.

## 4. Reproduction measurement

The reproduction record's §17
(`../designs/2026-09-05-mm30-reproduction.md`) records the run at
`b4d71dd`, committed at `963b860` and corrected at `c723680`.
`reproduction.rederive` read the established mm30 corpus in place; no
contract succeeded, so nothing was recreated or moved aside. The fresh
result was `NoBelief(reason="no-directional-outcome")`, with
`rederived_equal: true`. The complete `state.json` diff was empty; before
and after its SHA-256 was
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`, the
same digest §16.2 recorded.

The driver scan for the two new operations across
`python/tools/reproduction/*.py` is **empty**: no `audit_operation`,
`recheck_locations`, `ScopedWriter.audit` or `scoped.recheck` reference.
Step 9 still calls the bare evaluator by its own contract — its docstring
reads "Writes nothing" — so the driver mints no `audit` or `recheck`
report and re-checks no holding. Decision 12 holds: routing step 9 through
the wrapper would mint a report into the measured corpus, a change to the
artifact the reproduction lane does not make from a kernel lane. The
reproduction and design guards passed **50 tests** after §17 was added,
and 50 again after the review fix.

## 5. Remaining boundary

`act-report-remainder` closes in full at cut 38, and T2 with it: every
operation kind but `corpus-write`, reportless by design, now opens through
a boundary and closes through exactly one terminal record — the `run` where
one is minted, the act-report otherwise.

**T7** remains partial on its cross-root case — cross-root publication of
a dataset's provenance reference and its acquiring report, refused
today — owned by `cross-root-publication` (`beliefs-256f17`, tier 3). The
same-root case was read at cut 35. This cut reads no T7 arm.

**L1** remains partial on its persistence arms: kill the executor between
entry durability and apply at every stage; crash after entry durability
but before the transaction record stores the entry digest; cut persistence
at every stage of the settlement sequence for both terminal arms. These
belong to `persistence-cut` (`beliefs-3ea822`, tier 2), behind
`atoms-f5779f`, as cut 36 re-homed them. The unspellability arm stands
certified at cut 8. Cut 38 reads no L1 arm.

With `act-report-remainder` discharged, the `world-read` lane's head
becomes `publish`, which moves from tier 2 to tier 1 off the path: its
`world-read` prerequisite is discharged and the dogfood criterion needs no
publish. `contract-cut` remains the off-path join.

## 6. Main integration

*Filled at merge.* The whole-branch review, the detached repository gate
and the `--no-ff` merge into `main` belong to this section and are
recorded here in the `docs(cut38): record merged-main verification` commit
that follows the merge.

## 7. Execution rulings

- **The canonical worktree path, and why the plan's own recipes were
  re-spelled.** `atoms` opens roots with `openat2` under
  `RESOLVE_NO_SYMLINKS`, which refuses any symlinked path component, and
  this checkout's `.worktrees` is a symlink onto the work volume. Running
  pytest from the symlinked spelling produced `ELOOP` failures that read
  as real regressions; running the same module from the resolved spelling
  gave `22 passed`. Every pytest run in this lane therefore executes from
  the resolved worktree path, with every `SCIENCE_CUT*_ROOT` and
  `SCIENCE_MM30_ROOT` export spelled through a resolved main-checkout
  path. The plan's own Task 6 and Task 9 shell recipes carried the
  symlinked spelling and were re-spelled before dispatch. The exports are
  load-bearing rather than belt-and-braces: `cut37_acceptance.py`'s
  main-checkout inference resolves to the work volume when run from a
  worktree (the filed issue `beliefs-51ffdf`), so without them the runner
  would write its roots onto an uncertified volume and the durability
  allowlist would refuse. A separate, earlier symptom — about 190
  `CapabilityUnavailable` failures — was the *missing* root exports, not a
  regression either.
- **`PublishedObservation` is two classes, and the collision nearly landed
  two wrong assertions.** `beliefs.report.PublishedObservation` carries a
  `ref`; `beliefs.holdings.boundary.PublishedObservation` carries a
  `record`. `LocatorEntry.outcome` is typed with the first. A review
  finding on Task 4 suggested an import that would have bound the second,
  making a new assertion evaluate False for a genuinely published
  observation; the implementer deviated from the literal suggestion and
  was right to. The acceptance module hit the same hazard and avoids it by
  importing `PublishedObservation` from `beliefs.report` and importing
  `beliefs.holdings.boundary` for `ActContext` and `write` only.
- **§17's "exercised only by" sentence narrows away from spec decision
  12's literal wording.** The spec never checked the whole suite, so its
  "only" is loose prose, not a decision. An evidence record must be true:
  the sentence now says the acceptance module is where the
  certified-tuple guarantee rows are discharged, and names the unit and
  session-route tests that call the operations directly as outside the
  reproduction's evidence. The decision's substance — that the
  reproduction reaches neither operation — is unchanged and is what §17.1's
  empty grep proves.
- **The plan's Task 5 import block is a superset and is not
  byte-normative.** It mandated code that `ruff check .` — a repository
  gate — rejects. The implementer merged the two `beliefs.holdings.boundary`
  imports, ordered the block for Ruff, and deleted every name Ruff called
  unused. The spec mandates nothing about import spelling, so the gate
  wins; a name wrongly dropped would have errored at collection
  immediately. Task 5 also gained the pyright and Ruff commands every
  other code task carries, which its step had omitted.
- **The two refusal wordings the acceptance asserts** are the re-check's
  inconclusive reasons, and they are the attempt's own: a read that never
  began spells `ByteLocatorUntested("lease-refused")`, a read that began
  and did not establish spells `RetrievalFailed("io-error")`. The two
  outcomes are asserted distinct, and neither constructs an observation —
  the observation directory grows by exactly one file, the one conclusive
  location's. The refusal *types* the acceptance asserts are
  `PortMismatch` for a foreign-root port on both kinds, `RecheckRefused`
  for every late re-check input, `CitationRefused` for an out-of-range
  citation, and `ExecutionError` matching `already fulfills` for a second
  fulfilling submission, with a raw forged second fulfilment reading
  `MalformedView` `duplicate-fulfillment`.
- **The ledger-act counts BI-3 observed: four acts** — the audit's close,
  the write, the re-check act, and the re-check's close. That is one `act`
  line per committed transaction through `ScopedWriter`, and the audit
  contributes exactly one because it commits only its close: the audit
  writes nothing else. The count is asserted exactly, not as a lower
  bound, and the report observers are asserted equal to the session actor.
- **A commit subject's `; T2` suffix is a guarantee row, not a task
  number.** Task 3's reviewer read `feat(holdings): … ; T2` as a typo for
  T3. The plan's Global Constraints require every commit message to name
  the row or invariant it serves, and this cut closes row T2. Recorded so
  the misreading does not propagate.
- **The runner's exit code is inferred, not captured.** `detached.sh` does
  not persist its wrapped command's `$?`, so a cut has to establish exit 0
  from the log's contents (§1). Filed as an idea: the wrapper should echo
  `exit=$?`.
- **Every implementer ran in the foreground and committed before
  returning.** The first Task 1 dispatch parked on a background wait and
  ended its turn with the work uncommitted; it was resumed with a
  foreground-only instruction, and every later dispatch carried the rule.
  The one detached run this lane has made — Task 6's cut runner — went
  through the reaping wrapper and was polled from the foreground; its
  process group was confirmed gone and the session's scope left nothing
  running. The repository gate is the lane's other detached run; it has not
  run yet, and §6 records it.
- **The results record is `docs/plans/2026-09-22-conformance-cut-38-results.md`.**
  Spec §9.4 spells it under `docs/superpowers/plans/`; that is a typo, not
  a decision. Every prior results record lives in `docs/plans/`, the
  ledger's authority list cites that directory, and the cut document's and
  spec's status links are written relative to it.
