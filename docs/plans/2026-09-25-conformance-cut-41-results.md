# Conformance cut 41 — results

**Cut:** `../designs/2026-09-25-conformance-cut-41.md`
**Freeze:** `e8d47f2e576e8c96a67e0898667acbeddd3dc6b2`; SHA-256 `6e5374104758ebfc3c612166134397cbdb5d9946ff53afb8d99c949af16d2987`
**Declaration:** `python/tests/n2_arms_cut41.py`; SHA-256 `2437a3345c145d0e60a2122efc4d6538f028b513c9a008ec19061baafbf46f14`
**Subject:** live view-query evaluation — `evaluate_live_query(world, query) -> LiveSelection` over every corpus the registry admits with no terminal status, each present corpus captured inside its own operation-lock hold, damage and world-record conflicts refused with publish's classification, and the result stamped by the per-corpus states read inside each hold, never an epoch identity
**Design:** `../designs/2026-09-24-live-query-evaluation-design.md`
**Plan:** `../superpowers/plans/2026-09-24-live-query-evaluation.md`
**Discharged:** 2026-09-25 on `design/live-query`, through `235af2d`; reproduction recorded at `cb474eb`
**Runner:** `python/tools/cut41_acceptance.py`

## 1. What ran

The certified runner ran from the worktree `live-query`'s `python/`,
reached by its canonical path rather than through the `.worktrees` symlink,
at head `235af2d`, with every `SCIENCE_CUT*_ROOT` (cuts 4 to 41) and
`SCIENCE_MM30_ROOT` export spelled through the resolved main checkout, so its
cut roots sat on the main checkout's certified volume. Cut 41 chains **cut
40's** runner (`PREFIX_RUNNERS = ("cut40_acceptance.py",)`), which retains
the complete live prefix back through cut 17's nineteen phases; cut 40's own
chained summary appears in the log ahead of cut 41's, confirming the prefix
ran. Cut 8 remains cited-not-run.

The runner's two final lines, verbatim from the main checkout's
`.work/acceptance/cut41-runner.log`, are:

```text
declared arms: 12 (= 12 declaration units; 5 guarantee rows)
guarantee rows exercised: 5 (5 newly closed: Z1, Z2, Z3, Z4, Z5)
```

Its own phases were:

```text
[cut41 phase 2/3] test_live_selection_acceptance.py
19 passed in 36.01s
[cut41 phase 3/3] test_n2_cut41.py
10 passed in 10.31s
```

The log's last line is `RUNNER EXIT 0`, written by the reaping wrapper after
the runner returned. The full log has zero `FAILED`, `ERROR` or `Traceback`
matches across sixty-six clean pytest summaries. The wrapper exited and left
no process behind. This was the first and only full run.

Every prefix phase passed. Every one of the twelve live checks resolved and
passed without sabotage; all twelve mutations scored **sound**. No unit was
stale, vacuous, mixed or uncollected — `test_n2_cut41.py`'s ten tests are
where those verdicts are asserted, and they passed. Every unit homes exactly
one arm, every arm's sabotage lands in `world/live.py`, and no check is
co-cited. Each check below is in
`python/tests/acceptance/test_live_selection_acceptance.py`:

| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| Z1-a | `test_z1_a_every_present_admitted_corpus_is_captured_and_stamped_durably` | `world/live.py` | resolved | sound | Z1 closes |
| Z1-b | `test_z1_b_a_terminal_corpus_is_never_covered_durably` | `world/live.py` | resolved | sound | Z1 closes |
| Z1-c | `test_z1_c_an_absent_corpus_is_listed_and_its_addresses_are_unknown_durably` | `world/live.py` | resolved | sound | Z1 closes |
| Z1-d | `test_z1_d_coverage_is_the_registry_not_an_epoch_durably` | `world/live.py` | resolved | sound | Z1 closes |
| Z2-a | `test_z2_a_a_state_moving_inside_the_hold_discards_the_evaluation_durably` | `world/live.py` | resolved | sound | Z2 closes |
| Z2-b | `test_z2_b_state_reads_and_enumeration_run_inside_the_corpus_hold_durably` | `world/live.py` | resolved | sound | Z2 closes |
| Z3-a | `test_z3_a_the_stamp_names_the_states_the_selection_was_denoted_over_durably` | `world/live.py` | resolved | sound | Z3 closes |
| Z4-a | `test_z4_a_a_malformed_corpus_refuses_and_is_never_omitted_durably` | `world/live.py` | resolved | sound | Z4 closes |
| Z4-b | `test_z4_b_a_disagreeing_base_pin_refuses_durably` | `world/live.py` | resolved | sound | Z4 closes |
| Z5-a | `test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably` | `world/live.py` | resolved | sound | Z5 closes |
| Z5-b | `test_z5_b_uid_corruption_outranks_duplicate_location_durably` | `world/live.py` | resolved | sound | Z5 closes |
| Z5-c | `test_z5_c_a_uid_shared_with_a_record_outside_the_map_refuses_after_the_map_durably` | `world/live.py` | resolved | sound | Z5 closes |

The phase's **19 tests** are the twelve unit functions and the seven other
tests the design's §6.2 names and the cut's §3 leaves outside the
declaration: live after a write
(`test_live_after_a_write_selects_what_the_old_epoch_refuses_durably`), the
qualified agreement with an epoch and its counter-case
(`test_live_and_epoch_agree_over_identical_coverage_every_corpus_present_and_equal_states_durably`,
`test_equal_states_alone_do_not_make_the_two_agree_durably`), damage naming
every offender, coordination records never selected and never mapped, two
carriers of one corpus refusing, and no writes.

Each task's unit work passed on the certified tuple as it landed. Task 1's
shared core: the selection, view, staleness and boundary modules green, and
slice 4's acceptance module (`test_world_selection_acceptance.py`) **25
passed** unmodified. Task 2's types: **3 passed** in `test_live_selection.py`.
Task 3's entry point: **10 passed** in that module, then **12** after its fix
round's two message-agreement tests. Task 4's acceptance module: **19
passed** on the certified volume under `-W error`. Task 5's guards: **30
passed** over the recent-cut, staleness and frozen-guard modules, and a pilot
of the cut's two phase modules at **29 passed**, every arm sound and every
check resolved. `just test-fast` rose from **5682 passed, 1 skipped** at Task
0 to **5701** at Task 4. Pyright reported `0 errors` and Ruff `All checks
passed!` at every code task, and `tasks check` reported zero errors. No
capability waiver or skip was used for the discharge;
`VERIFIABLY_UNCERTIFIED_HOST` was never set.

The new recent-cut entry is `(cut41, 41, (12, 12, 5))` and asserts the
guarantee-rows-exercised line above. That interface check mocks subprocess
execution; the actual chained run is the discharge evidence.

## 2. Accounting

**The frozen accounting, every verdict holding.** Every arm the freeze
audited on paper held under the executable audit, so none was rehomed and
the cut document carries no §8 supplement. That gives **12 arms, 12
declaration units, 5 rows**, recent-cut row `(12, 12, 5)`, and a phase of 19
passes. No row is read in part.

**Z1–Z5 open and close at this cut.**

- **Z1:** coverage is the registry's live admitted set, read under the world
  barrier, never an epoch's. A retired corpus whose carrier is still
  configured is never covered, an admitted corpus with no carrier is listed
  in `absent` and makes the selection incomplete, and a world that has never
  published evaluates.
- **Z2:** each corpus's two state reads, its open and its one enumeration run
  inside its own `capture()` hold, serially in sorted order. A state that
  moves inside the hold raises `CaptureDrift` and discards the evaluation, and
  a writer holding the corpus's lock refuses it `BuildContended`.
- **Z3:** the stamp is built from the in-hold states and never re-read, so a
  record written after a corpus's hold releases is neither selected nor named
  by the stamp.
- **Z4:** a present corpus that fails construction or whose base pin
  disagrees refuses `corpus-damaged` naming it, after every corpus is tried;
  it is never omitted from a returned selection.
- **Z5:** the address map is publish's own `derive.address_map` over world
  kinds, so `uid-corruption` outranks `duplicate-location` exactly as at
  publish; the scoped W8b check runs only after the map and covers only
  records outside it.

The global corpus is **204 of 231 guarantee rows closed, 27 open**, up five
from the **199 of 231** of cut 41's freeze, which banked Z1–Z5 open onto cut
40's **199 of 226**. The Z table's five rows were banked at the freeze and
never selected until now. The accounting entry
`41: ("conformance-cut-41-results §2", "Z1, Z2, Z3, Z4, Z5", "")` in
`python/tools/roadmap_status.py` produces the roadmap's Appendix A, whose
totals line reads `Closed 204 of 231; open 27.`; no row is reopened.

`live-query` enters the ledger's `Current state` and the roadmap's boundary
index at this discharge and closes in this same commit, so neither table
carries an open row for it; the roadmap's lane table carries the closed
`live-query` lane. This is the **tenth** off-path lane opened under rule 6,
and it **re-ranks nothing on the path**: a live selection is attention, never
belief input, so the first belief reads none.

`root.py` remains the one `atoms` importer; `world/live.py` and
`world/selection.py` import nothing of `atoms`. The live path calls no write
primitive, so `WRITE_ENTRY_POINTS` in `test_permit_boundary.py`, the `CASES`
of `test_permit_entry_points.py` and `test_capability_boundary.py`'s
`RAW_WRITE_ALLOWLIST` are unchanged, and the three modules passed at Tasks 1
and 3. No error class is added. The base contract, the coordination contract,
both `CONTRACT.yaml` copies and the TypeScript tree are unchanged, so
`contract-cut` gains no dependency.

## 3. Evidence

### 3.1 Frozen evidence

Cut 41's body remains byte-exact to its freeze. `git diff` over
`docs/designs/2026-09-25-conformance-cut-41.md` between `e8d47f2` and
`235af2d`, the head the cut ran at, is empty, and the freeze commit's file
hashes to the frozen SHA-256 above; the guard compares §§2–7 against it. This
record's own commit changes the `**Status:**` line and nothing else, as cut
40's did. The declaration remains at its SHA-256, which the guard pins as
`CUT41_DECLARATION_SHA256`. No prior frozen declaration or cut body differs
from the pre-lane tree: the branch diff over `n2_arms_cut*.py` and the cut
documents names only cut 41's own.

**The shared denotation stays cut 28's.** Decision 9 moved the clause loop,
`_denote`, `_require_located`, `_classify` and the adjacencies into a private
core, `_denoted`, typed over a private `_QueryableView` protocol. Every one
of cut 28's W7-a to W7-o spellings in `world/selection.py` (and W7-p in
`decode.py`) still occurs exactly once, as do its W8 and W8b arms in
`world/derive.py` and `relocation.py`. Cut 23's and cut 27's pinned lines in
`world/view.py` (`locate`, `get`, `inbound`, `open_world_view`) and cut 4's
`RelationAdjacency(self._view, stored.TRANSFORMS, "outbound")` in
`corpus.py` are untouched: Task 1 added `LocatedState`,
`WorldReadView._located_state` and the `RelationView` protocol beside them.
`tests/test_arm_staleness.py` was green at every code task, and the
stale-arm probe was clean. No prior arm was re-targeted, and no cut-41 arm
touches `world/selection.py`.

**The count the cut froze.** The frozen §4 and §5 give 12 arms over 12
units, one each; the §3 paragraph names the module's seven other tests.
Task 4's module collected 19, so no superseding note is needed.

### 3.2 The planning notes, the pre-flight rulings and the deviations

**The planning notes the design carries (§8, "at planning").** Every one
landed as written:

- Table Z's owner is the design, moved into `docs/designs/` at the freeze.
- `LocatedState` lives in `world/view.py`, beside
  `WorldReadView._located_state`, because `selection.py` already imports
  `view.py`.
- `RelationAdjacency` is typed over the structural `RelationView` protocol
  in `corpus.py`, which `ReadView`, `WorldReadView` and the live capture all
  satisfy.
- The live capture is private (`live._LiveCapture`), and `_denoted` returns
  a private `_Denotation`.
- The refusals keep their exception types; no error class is added.
- `live.py` repeats `open_world_view`'s coverage block, capture loop, W8b
  message and inbound-edge construction, and keeps `_capture`'s two `except`
  branches and `_address_map`'s per-corpus filter separate, so that cut
  41's arms have single-site targets and cut 23's and cut 27's `view.py`
  pins do not move.
- `evaluate_live_query` checks `type(world) is registry.World` and
  `isinstance(query, ViewQuery)`, as `evaluate_query` does.
- Z1-d's and Z3-a's sabotages are stated as implemented.
- The twelve arms were audited on paper at the freeze and held under the
  executable audit (§2).

**The pre-flight rulings.** A pre-flight scan of the plan before Task 1 (19
pair rows, 9 task rows, a scratch run of Tasks 1–3 and a portable mirror of
Task 4 with all twelve arms sound) found no Critical finding, six Important
and eighteen Minor. The rulings, applied to the plan and design at
`4fb5ad6`:

- **I1:** the freeze commit stages `publish.py`, whose remote-refusal text
  the cut-42 relabel edits.
- **I2:** `main` was merged into `design/live-query` at `ce8e46e` before the
  freeze, so the baseline carries `main`'s task notes and the
  session-selection merge (disjoint files) and Step 6's merge does not
  conflict.
- **I3:** Task 4 runs ruff and fixes its lint by `_` prefixes on unused
  unpacked names and one merged `with`; no assertion is touched.
- **I4 and M8:** `live.py`'s repetition of `open_world_view` and its
  single-site structures are kept, recorded in the design's §8, with
  de-duplication out of this cut.
- **I5:** the plan's test that the core denotes what `evaluate_query`
  selects is dropped, as true by construction after Task 1; core sharing is
  evidenced end to end by the qualified epoch agreement.
- **I6:** the agreement set is slice 4's default-fixture acceptance queries
  plus the plan's two extras, since the design's §6.2 says every slice 4
  query.
- **M1:** Task 4 adds the address-map half of the coordination-records test,
  which the design's §6.2 requires.
- **M3:** the design's Z1-d and Z3-a sabotage wording is amended to what
  Task 5 implements, so the frozen §5 and the table's owner agree.
- **M4:** `isinstance(query, ViewQuery)` is kept, mirroring
  `evaluate_query`.
- **M5, M7, M10, M11 and M12:** plan text only.

**Deviations from the plan and the design**, each reviewed:

- **Live after a write adds a dataset** where the design's §6.2 says a
  proposition. The live path treats every world kind identically, so the
  test observes the same guarantee; the final review judged it no fix.
- **Task 0:** a fix round relabelled the one remaining current "cut 41"
  reference to the remote slice, in the user and autonomy layer design's
  Status line, and corrected `beliefs-1ce6cc`'s body by a task note, since
  the tasks CLI has no body edit.
- **Task 3:** two portable tests were added in its fix round (`cc08484`),
  pinning `evaluate_live_query`'s unreadable-manifest and duplicate-carrier
  refusals to `open_world_view`'s messages by full string equality, so the
  repetition the design keeps cannot drift unnoticed. `live.py` did not
  change.
- **Task 4:**
  - The address-map probe (ruling M1) calls the private `live._capture`
    and `live._address_map` and asserts that no coordination address is
    mapped, behind a non-vacuity guard (the corpus is undamaged and its
    project record was captured). Its sensitivity was proven by hand:
    removing `_address_map`'s world-kind filter failed the probe while the
    two selection assertions still passed.
  - Seven names took `_` prefixes, not the brief's nine, because the probe
    uses two of them.
  - **No fixture fix was needed**: every durable fixture behaved as the plan
    predicted.
- **Task 5:** the declaration and the runner are byte-exact to the plan, and
  the guard differs from cut 40's only by the rename and the planned edits.
  Z5-a's arm is the every-record uid check before the map, in place of the
  scoped check after it, as the frozen §5 states.
- **Task 7's review needed no code fix.** Nothing changed on the branch
  between the review and this record except task records.

### 3.3 Review findings, the gate and limitations

Every task was reviewed against the design before the next began. Task 0's
review found the remaining remote-slice reference (fixed, §3.2); Task 3's
found the plan-mandated repetition (kept by ruling, messages pinned); Tasks
1, 2, 4, 5 and 6 were clean at their first review.

**The whole-branch review** ran over `7cf5d17..cb474eb` against the design's
decisions, the plan's Global Constraints and Review Focus, and the cut
document's §5 and §6. No Critical or Important findings. All five Review
Focus inputs hold and are pinned: a retired address resolves to its live
record through publish's map; nothing admitted evaluates to an empty,
complete selection; a coordination-only corpus is stamped and contributes
nothing; an unreadable manifest refuses and is never an absence; and a
repeated evaluation is identical, with only a written corpus's coverage pair
moving. The §6 second-reader checks hold. Five Minor findings:

1. A retired address in one corpus equal to another corpus's live address
   escapes `derive.address_map` as a bare `ValueError`. Publish raises the
   same error over the same states, and decision 7 binds the live path to
   publish's classification, so the fix belongs in `derive`: filed as
   `beliefs-354eae`.
2. `beliefs.world` does not re-export the live entry point beside
   `evaluate_query`; science imports it from `beliefs.world.live`.
3. The W8b message equality is not pinned; it belongs with the
   de-duplication, `beliefs-0e1acb`, which removes the repeated text.
4. Damage in an earlier corpus is reported as a later corpus's
   `CaptureDrift` or `BuildContended` when both occur. Every path returns
   nothing, so no corpus is silently omitted and decision 8 holds; the
   precedence is undocumented.
5. Z2-b's per-carrier kind-set assertion proves less than its comment says;
   the unit's soundness rests on its every-call holder assertion.

Minors 2, 4 and 5 move no arm target and are left as recorded here.
`beliefs-0e1acb` carries the Task 3 review's repetition finding.

**The gate.** `just gate` at `cb474eb` on the certified volume: ruff `All
checks passed!`; pyright `0 errors, 0 warnings, 0 informations`; `5743
passed, 1 skipped in 1283.58s (0:21:23)`; TypeScript `Test Files 7 passed
(7)`, `Tests 155 passed (155)`; `GATE EXIT 0` (log
`.work/acceptance/cut41-gate.log`). The only later branch commit before this
record, `2c13291`, closes task records and touches no code.

The cut's §7 limitations stand, and none reopens a row:

- Coherence is per corpus; there is no cross-corpus snapshot, as there is
  none in a build.
- An absent corpus's addresses are unknown to a live read, so
  `address-not-present` is never raised on this path.
- A live selection is attention, never belief input; belief reads and
  publication stay epoch-bound.

The design's §5 amendment to coordination §6.2 lands in the same commit as
this record, dated to the discharge.

## 4. Reproduction measurement

The reproduction record's §20
(`../designs/2026-09-05-mm30-reproduction.md`) records the run at `e198961`,
committed at `cb474eb`. `reproduction.rederive` read the established mm30
corpus in place; no contract succeeded, so nothing was recreated or moved
aside. The result was the same `NoBelief` payload, with
`rederived_equal: true`. The complete `state.json` was byte-identical, with
SHA-256 `1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`
before and after, the same digest §19 recorded. The driver reaches none of
this slice's surfaces: it mints no view query and calls neither
`evaluate_query` nor `evaluate_live_query`, so neither the live path nor the
shared denotation core is exercised.

## 5. Remaining boundary

`live-query` retains nothing: Z1–Z5 close in full, the cut's three
limitations are banked as limitations rather than work, and the boundary
leaves the ledger in the commit that entered it.

What stays open elsewhere, unchanged by this cut:

- `publish` stays open, in the ledger's table and the roadmap's boundary
  index, tier 1 off the path, with planned cut 42's remote slice
  (`beliefs-3ce305`): the transport seam, the remote reveal and its orphans,
  the recovery table's remote rows and the recipient's
  `divergent-publication`. It appends its own rows to the Y table. Cut 41
  touched `world/view.py` and `corpus.py`, which that lane's shared surface
  also lists; the overlap was named at the freeze under rule 3.
- **L1** remains partial on its persistence arms, owned by `persistence-cut`
  (`beliefs-3ea822`, tier 2) behind `atoms-f5779f`. Cut 41 reads no L1 arm.
- **T7** remains partial on its cross-root case, owned by
  `cross-root-publication` (`beliefs-256f17`, tier 3). Cut 41 reads no T7
  arm.

Two follow-ups filed from this lane's reviews are tasks, not boundaries:
`beliefs-354eae` (a typed refusal for a retired-address collision in
`derive.address_map`, shared with publish) and `beliefs-0e1acb` (sharing
`live.py`'s repeated coverage, capture, W8b and inbound code with
`open_world_view`, re-targeting cut 23's, cut 27's and cut 41's arms). The
consumer is science's part 2 (`sci-f95f8b`), which calls
`evaluate_live_query` for `next` under a selected project.

## 6. Main integration

Filled at merge: the merge into `main` and the verification on the merged
tree. The whole-branch review and the repository gate ran before this record
(§3.3).

## 7. Execution rulings

- **Ruling 1: the cut number (plan Task 0 Step 1).** At planning, cut 41 was
  unfrozen, reserved only in prose for the remote publish slice. The user
  decided on 2026-09-25 to freeze this cut as **cut 41**, prefixing cut 40,
  and to relabel the remote slice's current references to planned cut 42 in
  the freeze commit, leaving historical cut bodies byte-exact. The freeze
  scan found no cut-41-or-later document, results record or runner on any
  branch (`main`, `design/live-query`, `design/publish`, `origin/main`), and
  the pre-discharge rescan against `main` found none but this lane's own
  cut document. Cut 40 was discharged, so rule 5 added no wait.
- **Ruling 2: the pre-flight scan was delegated** to a fresh reviewer, which
  wrote its table to the lane's working notes; its rulings are in §3.2.
- **Ruling 3: `live.py`'s repetition is kept and its messages pinned** after
  Task 3's review, with the de-duplication filed as `beliefs-0e1acb`.
- **Ruling 4: `beliefs-1ce6cc` is corrected by a task note,** not a body
  edit, since the tasks CLI has none and task records change only through it.
- **Ruling 5: the chained runner is the controller's.** Task 5's implementer
  did Steps 1–4, the guard and a pilot, and committed; the controller
  launched the detached cut runner through the reaping wrapper as a tracked
  background job and read its log, since the chain re-runs cut 40's prefix
  for about half an hour. The gate ran as a tracked background job too.
- **Every implementer ran in the foreground and committed before
  returning.** Neither background run, the chained cut runner or the gate,
  left a process behind.
