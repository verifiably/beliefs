# Conformance cut 44 — results

**Cut:** `../designs/2026-10-01-conformance-cut-44.md`
**Freeze:** `ce4d138`; SHA-256 `48679ee46e5e2195e1c820a39b9e0e661caa1eee47fdd219029da60ce7f1bb40`
**Declaration:** `python/tests/n2_arms_cut44.py`; SHA-256 `73f9847285753a425f15e05b581346b2128dda861a7a776c2892f64f205828ef`
**Subject:** citations into mounted corpora at the write boundary, eligibility the checks cannot decide, the world audit over its capture, and belief over the two-installation split
**Design:** `../superpowers/specs/2026-10-01-mount-citations-design.md`
**Plan:** `../superpowers/plans/2026-10-01-mount-citations.md`
**Discharged:** 2026-10-01 on `cross-mount-eligibility`, implementation through `912005b`; reproduction at `48aaa2f`, its §26 corrected at `4761862`
**Runner:** `python/tools/cut44_acceptance.py`

## 1. What ran

The cut runner needed four attempts. Only the fourth ran to its verdict; the retained
log, main `.work/acceptance/cut44-runner.log`, is that attempt's; the earlier three
are recorded here.

1. **Refused: `OPS_WORKERS` unset.** The plan's command omitted `host-budget run --`,
   so the prefix chain refused in cut 6's N2 phase before any of cut 44's own phases
   ran. The command below is the corrected one, the same wrapper the justfile's test
   recipes use.
2. **Failed in cut 17's phase.** `test_permit_entry_points` reported its 8
   `needs_volume` cases as `CapabilityUnavailable`: the SQLite-WAL parent connection
   failed with "unable to open database file". `tools/acceptance_runner.py` nests each
   prefix run under its parent's run directory, and cut 44's chain is one level deeper
   than cut 43's, which pushed the deepest SQLite path past 512 characters. This was
   reproduced: 27 nesting levels fail at the canonical base and 20 pass. It is not a
   cut-44 code defect. The workaround is `SCIENCE_CUT44_ROOT=<main>/.work/c44`, 13
   characters shorter, which restores cut 43's proven depth on the certified volume
   (`.work/` is gitignored). The structural fix is filed as `beliefs-fdc40f` (P1).
3. **Failed in cut 23's phase.** The tail of
   `test_world_view_acceptance.py::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably`
   evaluated corpus-locally over a corpus whose run observes a dataset another corpus
   holds, and asserted B4's silent drop. J21 now refuses that read. This was an
   unforeseen reach of the approved B4 supersession; §3 records the rewrite.
4. **Green, exit 0.** The final invocation, run from `python/` in the canonical
   worktree path:

```text
SCIENCE_MM30_ROOT=<main>/.work/reproduction/mm30 SCIENCE_CUT44_ROOT=<main>/.work/c44 host-budget run -- uv run --frozen python tools/cut44_acceptance.py
```

The runner chains cut 43 (`PREFIX_RUNNERS = ("cut43_acceptance.py",)`), retaining the
historical live prefix; cut 8 remains cited-not-run. All **72 pytest phases and 1126
passing invocations** passed, including inherited repetitions, with no failure, skip
or error line. Reported pytest times total **5537.81 seconds**. Attempt 4 started
after `912005b` and the log's last write followed it by about 94 minutes, which
bounds the elapsed time.

```text
[cut44 phase 2/3] test_mount_citations_acceptance.py
10 passed in 30.34s
[cut44 phase 3/3] test_n2_cut44.py
10 passed in 30.26s
declared arms: 24 (= 24 declaration units; 6 guarantee rows)
guarantee rows exercised: 6 (6 newly closed: J16, J17, J18, J19, J20, J21)
```

The guard resolves every baseline and finds every mutation sound: no stale, vacuous,
unresolved or uncollected arm. `CO_CITED` holds two shared checks: J16-a with J16-b, and
J21-a with cut 22's B4b (§3). Portable checks live under `python/tests/`; the module
named in each row's first cell is repeated by `::` rows below it.

| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| J16-a | `test_mount_citations.py::test_an_assessment_over_a_mount_dataset_and_proposition_is_written` | `corpus.py` | resolved | sound | J16 closes |
| J16-b | the same check (co-cited) | `corpus.py` | resolved | sound | J16 closes |
| J16-c | `::test_a_verification_of_a_mount_assessment_is_written` | `corpus.py` | resolved | sound | J16 closes |
| J16-d | `::test_a_citation_across_differing_identities_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-e | `test_session_writer.py::test_the_session_writer_cites_its_read_mounts` | `session/__init__.py` | resolved | sound | J16 closes |
| J16-f | `test_mount_citations.py::test_an_assessment_over_a_dataset_a_third_mount_produces_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-g | `test_session_writer.py::test_a_symlinked_write_root_mount_key_is_filtered_after_normalization` | `session/__init__.py` | resolved | sound | J16 closes |
| J16-h | `test_mount_citations.py::test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-i | `::test_an_acquired_dataset_a_mount_run_produces_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-j | `::test_an_imported_run_producing_a_mount_observation_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-k | `::test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-l | `::test_an_assessment_over_a_raw_split_dataset_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J16-m | `::test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses` | `corpus.py` | resolved | sound | J16 closes |
| J17-a | `::test_a_ref_held_twice_refuses_duplicate_location_naming_both` | `corpus.py` | resolved | sound | J17 closes |
| J17-b | `::test_a_held_read_mount_lock_refuses_build_contended` | `corpus.py` | resolved | sound | J17 closes |
| J18-a | `test_read_side.py::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved` | `corpus.py` | resolved | sound | J18 closes |
| J18-b | `test_read_side.py::test_one_held_invalid_and_one_unheld_dataset_is_unresolved` | `corpus.py` | resolved | sound | J18 closes |
| J19-a | `test_world_audit.py::test_j19_a_supported_cross_corpus_citation_has_no_finding` | `audit.py` | resolved | sound | J19 closes |
| J19-b | `::test_j19_b_an_absent_holder_is_unresolved` | `audit.py` | resolved | sound | J19 closes |
| J19-c | `::test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier` | `audit.py` | resolved | sound | J19 closes |
| J19-d | `::test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues` | `audit.py` | resolved | sound | J19 closes |
| J19-e | `::test_j19_e_an_absent_producer_keeps_the_dataset_produced` | `audit.py` | resolved | sound | J19 closes |
| J20-a | `test_world_view.py::test_j20_the_two_installation_split_evaluates_as_one_corpus` | `evaluation.py` | resolved | sound | J20 closes |
| J21-a | `test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather` | `evaluation.py` | resolved | sound | J21 closes |

The recent-cut row is `(cut44, 44, (24, 24, 6))`, including the rows-exercised line;
that interface test mocks subprocesses, while the full chain supplies discharge evidence.
The ten durable cases in `python/tests/acceptance/test_mount_citations_acceptance.py`
match frozen §4's count.

## 2. Accounting

**24 arms, 24 declaration units, 6 guarantee rows. J16–J21 close.** Every declared arm
ran sound. Every sub-case the rows name is exercised by a unit or durable test, except
J19's `excluded:<scope>` cause, which §3 lists as unexercised.

- **J16:** a session's write boundary resolves citations over the write root and every
  read mount, reads each cited record in its holding corpus under the writer's profile,
  refuses a citation across differing identities of one namespace, and judges producers
  over the whole session on every path, in both directions. The write lands in the write
  root alone.
- **J17:** a citation two session corpora resolve refuses `duplicate-location` naming
  both, and a read mount whose operation lock is held refuses `BuildContended`, each
  before any effect.
- **J18:** `corpus_check` reports eligibility resting on references the corpus does not
  hold as an `eligibility-unresolved` warning; locally decided failures stay
  `eligibility-unmet` errors, with S7's finding line byte-exact.
- **J19:** `audit_world` judges eligibility over its capture through a total citation
  reader: supported, unmapped, and unresolved by an absent, damaged or malformed holder,
  and the audit continues. The excluded-holder cause is not exercised (§3).
- **J20:** belief over a world read gathers, admits and evaluates the two-installation
  split with the one-corpus answer.
- **J21:** a corpus-local belief read refuses an input the corpus does not hold. It
  supersedes B4's absent-dataset clause, cited (§3).

The corpus is **220 of 247 guarantee rows closed, 27 open**, up six from the frozen
tree's 214 of 247. No row reopens. The entry
`44: ("conformance-cut-44-results §2", "J16, J17, J18, J19, J20, J21", "")` in
`python/tools/roadmap_status.py` generates Appendix A with `Closed 220 of 247; open 27.`
The J table is closed across cuts 19, 43 and 44. `mount-citations` closes, tier 1
**on the path**, the second-project milestone's last kernel prerequisite.

## 3. Evidence

The frozen cut body is byte-exact; this change edits only its status line, which sits
above the pinned §§2–7. The declaration keeps the hash above. `WRITE_ENTRY_POINTS` in
`test_permit_boundary.py` and `CASES` in `test_permit_entry_points.py` are unchanged and
closed in both directions; the capability-boundary inventory is unchanged too. This
slice adds no write primitive or entry point, and `root.py` remains the one `atoms`
importer: `MountCitations` reaches the capture hold through `_operation_lock_for`.

**Re-targets.** Two foreseen live pins moved, each in its live guard's
`_LIVE_SABOTAGES` table, and no frozen declaration module was edited:

- cut 20's F4 (`test_n2_cut20.py`, at `ce68292`) follows
  `reason = validity_refusal(...)` from `eligibility_refusal` into `eligibility_outcome`
  with the same mutation, reading the facet directly;
- cut 22's B4b (`test_n2_cut22.py`, at `d45244c`) takes J21-a's mutation, removing the
  `InputOutsideCorpus` refusal. B4b's check keeps its frozen node id; its body asserts
  J21's refusal, with a docstring naming the supersession.

**B4's absent-dataset clause is superseded by J21**, cited as cut 43 cited J9's two-root
clause as superseded by J12. B4's guarantee row ("only held datasets are read") said
that `gather` over an absent observed dataset leaves it out and "nothing refuses"; a
corpus-local read now refuses it. B4's other clauses stand: every read is validated, and
only held datasets are read. The biology-pack design's §7 now carries a line naming J21
as the clause's successor.

**The supersession reached one durable test the spec did not foresee.** The tail of
cut 23's
`test_world_view_acceptance.py::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably`
asserted the silent drop. At `912005b` only that tail was rewritten: `gather` raises
`InputOutsideCorpus` naming the run and its dataset, and `evaluate_over` returns
`Refused("input-outside-corpus: …")`. Cut 23's R19b, R19c and R19e observables sit in
the unchanged part of the test, and its name is unchanged. A sweep of the ten
acceptance modules that seed corpus-local reads found no other assertion of the drop.
The portable suite cannot see `tests/acceptance`, which is why the cut runner found it.

**Independent evidence.** J21-a shares both its mutation and its check with cut 22's
re-targeted B4b. The frozen §5 says the two "differ in their check"; they do not, and
`test_n2_cut22.py`'s comment now says they share both. Cut 44 therefore has **23
independent sabotage arms**. J21's arm is B4b's; its independent evidence is its unit
tests and durable case (`test_j21_a_local_read_of_the_split_refuses_durably`).

**J16-c's check was reshaped under its frozen id.** On the first N2 run the arm was
vacuous: its check wrote a report-less verification, which never reads the view
(cut 18's R2), so `view=self._view` changed nothing. The check body now writes a
published, report-carrying verification over a mount assessment, so the view decides
it. The frozen mutation and check id are unchanged (`cac773c`).

**J20's equality.** The durable case compares the value, policy binding and admission,
and the closure projection, between the split world and the same records in one
corpus. It excludes `belief_input_digest` and, from the closure, `producer_snapshot` and
the retraction `coverage`: those name the world's epoch and its corpus ids by
construction, against `producer-snapshot-1` and the single corpus id. Every other closure
member is equal. Attribution is asserted as assessment and run → W, the observed
datasets → M, and the proposition's corpus via `corpus_of`, because `gather` attributes
only assessments, runs and datasets (decision 10). The lineage snapshot reaches M's
dataset, and the absent-carrier negative is `NoBelief("unavailable-corpus-absent")`.

**J21 was extended to the run after the cut ran.** The final whole-branch review found
that a corpus-local read of an assessment whose run the corpus does not hold, the shape
a mounted session writes when it assesses over a read mount's run, raised `KeyError`:
`gather` skipped the run and `evaluate` indexed it. Decision 9 now reaches the run
(spec §13): `gather` raises `InputOutsideCorpus` naming the run, and `evaluate_over`
returns `Refused("input-outside-corpus: …")`. Unit tests cover it
(`test_domain_facet_read.py::test_an_assessment_whose_run_the_corpus_does_not_hold_refuses`
and `test_mount_citations.py::test_a_corpus_local_read_of_an_assessment_over_a_mount_run_refuses`),
but no declared N2 arm does: cut 44's declaration is frozen at 24 arms, and this
refusal is not one of them.

**Row sub-cases the final review found unexercised.** The final whole-branch review
found six sub-cases of J16, J17 and J19 that no test reached while this record said the
rows closed "in full". Five now have portable tests:

- J17, the address held by W and a read mount:
  `test_mount_citations.py::test_a_citation_held_by_the_write_root_and_a_mount_refuses_naming_both`
  (the write root's own corpus id in the `duplicate-location` finding, W unchanged);
- J19-d, W's other records and M's readable remainder still audited beside M's damage:
  `test_world_audit.py::test_j19_d_the_audit_still_judges_w_and_ms_readable_remainder`;
- J19's stale stamp, M's own `semantic-hash-stale` finding beside the eligibility one:
  `test_world_audit.py::test_j19_a_malformed_held_record_is_unresolved`;
- J16's raw-written split retrieval, the dataset in W and its report only in M, with
  `corpus_check(W)` and `audit_world` each reporting `facet-retrieval-unresolved` on it
  and nothing else:
  `test_world_audit.py::test_j16_a_split_retrieval_report_is_unresolved_in_the_check_and_the_audit_alike`;
- J16's negative through a session with `mounts=None`, which refuses the citation into
  another root with today's `EligibilityUnmet`:
  `test_session_writer.py::test_a_session_with_no_mounts_refuses_a_citation_into_another_root`.

None of these is a declared N2 arm. **Unexercised:** J19's `excluded:<scope>` cause.
No test reaches it, and `audit_world` appears unable to produce it as a citation cause.
`_manifest_findings` yields only scope `base`, `domains` or `none`, so `malformed` never
occurs. Scope `base` arises in two ways, and neither reaches it. If the audit's profile
requires a non-shipped base, every corpus is excluded, the citing one too, so no
eligibility is judged. If a manifest pins a non-shipped base, the corpus is damaged
(`base-pin`) and skipped before the exclusion. The reader's `excluded` branch therefore
stands untested, and §2 no longer claims it.

**A cut-31 cited test was narrowed.** Task 4 narrowed
`test_world_audit.py::test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues`.
The old last-per-reference map hid a pre-existing `derivation-malformed` behind an
`eligibility-unresolved` that the two-pass audit correctly no longer reports. Cut 31's
pre-grammar guarantee, which it and mm30 §10 cite the test for, is still asserted, more
strictly.

The spec's §13 notes are realized, and Task 9 adds the rest:

- **At planning:** the B4 supersession and the two foreseen re-targets above;
  `eligibility_refusal` keeps its string return over a new `eligibility_outcome`; mm30
  can be cited from a shipped-pack working corpus, since its `biology` pin is the shipped
  identity; `producers-incomplete` is judged per dataset and the scan continues; and the
  portable fixtures use `profile_with()` and `profile_with("other")`.
- **At Task 5:** J20 compares value, policy binding and admission, not
  `belief_input_digest`; no portable test relied on the silent drop beyond B4b's check.
- **At Task 7:** J16-c's reshape, and the cut-23 tail above.
- **At Task 9:** the durable module realizes §8.2's M, M2 and M3 as `profile_with()`
  (M and M3) and `biology("other")` (M2), for portability, so no durable case covers a
  namespace M pins and W lacks; J20's "the others → M" is checked for the proposition
  through `corpus_of`; and §3.2 drifted in three places (the session passes `()`, not
  `None`; `acquisition_view` was built as `MountCitations.overlay(base)` returning
  `_SessionOverlay`; and `eligibility_outcome`'s docstring restores the rationale that
  `reads` inputs never confer eligibility, still true of the code).

## 4. The reproduction

`../designs/2026-09-05-mm30-reproduction.md` §26 (`4761862`) records Task 8's re-run from
`5ac7447`. Preflight printed `ok` and `reproduction.rederive` ran in a fresh process.
The answer is unchanged, `NoBelief(no-directional-outcome)` with `"equal": true`, not an
`input-outside-corpus` refusal. Steps 10b and 10c agree. The before copy and rewritten
`state.json` are byte-identical (`cmp` exit 0, empty full diff), both SHA-256
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`. The verdict step was
not run, per §25.1. The driver opens no session and mounts no corpus, so this is
compatibility evidence: J21 does not move mm30's answer because every input its run
reads is held. mm30's manifest pins the shipped `biology` identity (`24bcec43…`), so a
working corpus on the shipped pack can cite it. The mounted measurement is science's
`sci-0d00d2`, after `sci-dc0381`.

## 5. Remaining boundary

None for `mount-citations`: J16–J21 are discharged, with the one unexercised J19 cause
§3 lists. Spec §10's limitations remain:

1. Read mounts are opened per citing write; there is no state-keyed cache.
2. Duplicates refuse, including identical ones, until `beliefs-81367e`.
3. A read mount mid-write blocks every citing write in the session, with an immediate
   `BuildContended` naming the read mount. Its converse, added at the final review
   (spec §13): a writer in the same process on a mounted root, arriving while a citing
   write holds that mount's capture, refuses `BuildHold` at once, worded as an epoch
   build's capture because the operation lock does not name its holder
   (`test_mount_citations.py::test_a_writer_on_a_mount_a_citing_write_holds_refuses_build_hold`).
4. There is no live multi-corpus belief read; belief over mounts is a world read at an
   epoch.
5. Mutation targets stay in the write root.
6. Retrieval reports stay with their datasets; a split dataset and report refuses
   everywhere.
7. There is no world-wide bearer finding; `facet-bearer-produced` stays per corpus.

Two follow-ups are filed:

- `beliefs-fdc40f` (priority 1): the acceptance runner's nested run directories push the
  deepest SQLite path past the platform limit one cut deeper than cut 43. Cut 44 ran
  with `SCIENCE_CUT44_ROOT` shortened; cut 45 hits the limit again unless this lands.
- `beliefs-d69102` (idea): `consulted_contracts` (`python/src/beliefs/consulted.py`)
  takes its corpora only from attributed nodes, so a world read where the mounted corpus
  holds only the proposition, whose claim uses a namespace only that corpus pins, would
  raise `ContractDisagreement` ("pinned by no corpus"). This predates the lane; it was
  found in Task 6's review, and no durable case covers that shape.

The second-project milestone has not been measured. Its kernel prerequisites are now
closed; it waits on science's `sci-dc0381`. The `write-path` lane closes again;
`contract-cut` stays first off the path.

## 6. Main integration

Pending: Task 10 runs the whole-branch review and `just gate`, then merges
`cross-mount-eligibility` into `main` and fills this section.

## 7. Execution rulings

Each ruling is followed by its cost if wrong.

- **Task 1:** J16-j's one-line `before` occurs twice in `corpus.py`, in `resolve` and
  `get`. Task 7 spells it as the two-line, unique `resolve` body with a matching
  two-line `after`, and J16-i as its two-line `for` loop. No code changed; the plan
  already said to spell them from the tree where unique. *Cost if wrong:* J16-j stale or
  ambiguous, caught by `test_arm_staleness` at Task 7.
- **Task 2:** the implementer's concern that `boundary.acquisition_guard` judges the
  write root only needs no action. A session's operation port is a `LedgeredPort` whose
  `execute_fulfilling_guarded` raises `SessionProtocolError`, and the unattended writer
  has no read mounts (decision 6). *Cost if wrong:* an unattended publication with
  mounts could miss a mount producer; no such path exists today.
- **Task 3:** J18's tests are module-level functions, because the frozen cut document
  names their checks with no class segment and the brief's code is module-level. A
  pre-review fix (`0c6dacf`) moved them. *Cost if wrong:* one extra move commit.
- **Task 4:** the narrowing of the cited cut-31 test
  `test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues`
  stands (§3). The old last-per-reference map hid a pre-existing `derivation-malformed`
  behind an `eligibility-unresolved` this task correctly removes; cut 31 and mm30 §10
  cite the test for the two pre-grammar codes, still asserted more strictly. *Cost if
  wrong:* a masked defect in the derivation on `assessment:a-p` goes unexamined.
- **Task 5:** the implementer's spec §13 note stands: J20 compares value, policy binding
  and admission, not `belief_input_digest`, which names epoch and corpus ids by
  construction. The spec's J20 row never required digest equality. *Cost if wrong:* one
  note to reword.
- **Task 5:** Task 6's durable J20 additionally asserts closure-projection equality
  minus `producer_snapshot` and retraction `coverage`, plus the full row (assessment and
  run → W; proposition and both datasets → M; lineage; the negative), and durable J21
  asserts the assessment. This makes §13's "every other closure member is equal" a
  tested claim. *Cost if wrong:* one extra assertion to drop.
- **Task 6:** the spec's §8.2 and J16 row describe M pinning a namespace W lacks and M2
  on fixture version 2, while the acceptance module uses `profile_with()` and
  `biology("other")`. A §13 note records the fixture choice, beside a note that J20's
  "the others → M" is checked for the proposition through `corpus_of` (both landed at
  Task 9, §3). *Cost if wrong:* no durable case covers a namespace only M pins.
- **Task 6:** file a follow-up for `consulted_contracts`, which takes corpora only from
  attributed nodes, so a world read where M holds only the proposition with an M-only
  namespace would raise `ContractDisagreement` ("pinned by no corpus"). Filed as
  `beliefs-d69102` (§5); it predates the lane. *Cost if wrong:* a real mixed-namespace
  world read refuses.
- **Task 7:** J16-c keeps its frozen mutation and check id; its check body was reshaped
  to write a published, report-carrying verification over the mount assessment (§3).
  The cut document names the check id, not its body. *Cost if wrong:* one more check
  rewrite.
- **Task 7:** J21-a joins J16-a and J16-b in `CO_CITED`, since its check is also B4b's
  live re-target check. *Cost if wrong:* the guard expects 23 distinct checks instead
  of 24.
- **Task 7:** attempt 1 refused on `OPS_WORKERS`; the rerun is
  `host-budget run -- uv run --frozen python tools/cut44_acceptance.py`, as the
  justfile's test recipes run, and §1 records the corrected command. *Cost if wrong:*
  none; environment only.
- **Task 7:** J21-a duplicates B4b's re-target in both mutation and check, so the frozen
  prose "differ in their check" is false. The frozen body is not edited;
  `test_n2_cut22.py`'s current-facing comment was corrected, and §3 states 23
  independent arms. *Cost if wrong:* coverage overstated by one arm.
- **Task 7:** attempt 2's path-length failure is worked around with
  `SCIENCE_CUT44_ROOT=<main>/.work/c44` (13 characters shorter, cut 43's proven depth,
  gitignored and on the certified volume) and filed as `beliefs-fdc40f` (§1, §5).
  *Cost if wrong:* cut 45 hits the limit again unless `beliefs-fdc40f` lands.
- **Task 7:** the cut-23 tail asserted B4's absent-dataset clause, which the user
  approved J21 superseding. **The rewritten test,
  `test_world_view_acceptance.py::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably`,
  is the cited check for cut 23's R19b, R19c and R19e arms**
  (`python/tests/acceptance/n2_arms_cut23.py:227,237,267`), **and its body was
  edited** at `912005b`. Only the tail changed, to assert J21's refusal (`gather` raises
  `InputOutsideCorpus` naming the run and its dataset; `evaluate_over` returns
  `Refused("input-outside-corpus: …")`); the test keeps its name, and the R19b, R19c and
  R19e observables sit in the unchanged part. The acceptance modules were swept for other
  corpus-local reads over unheld inputs before attempt 4 (§3). *Cost if wrong:* a frozen
  cut-23 claim is edited where it should have been pinned.
- **Task 9:** the cut-44 document's `**Status:**` line is edited, and only that line.
  Cut 43's results commit did the same, and
  `test_the_newest_cut_document_says_it_is_discharged` requires it; the guard pins
  §§2–7, which stay byte-exact. *Cost if wrong:* a frozen-document edit the user would
  rather have avoided.
- **Task 9:** Task 10 commits the lane's execution ledger to
  `docs/plans/2026-10-01-mount-citations-execution-ledger.md` before the worktree is
  removed, since the working copy is gitignored. *Cost if wrong:* none.
- Deferred review observations are minor and none blocks discharge. The notable ones are
  an `assert` on a mutable profile in `audit.py`, a second-pass audit cost per corpus that
  a dogfood should measure, and observes-loop filtering in `evaluation.py` that no live
  arm guards after B4b's re-target.
