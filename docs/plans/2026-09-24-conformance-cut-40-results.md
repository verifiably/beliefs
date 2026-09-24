# Conformance cut 40 — results

**Cut:** `../designs/2026-09-24-conformance-cut-40.md`
**Freeze:** `34e553714d27f36d6131c4ea336b61a4f829cdcb`; SHA-256 `4d3afb537df9a127e5d7ce6f473a2bbb098a4ee26a71f66b78955968a090f0ec`
**Declaration:** `python/tests/n2_arms_cut40.py`; SHA-256 `d24688e4642594b21aa7998163dc3d38245d30dc099c81dcbbad72f3e7c17d03`
**Subject:** the publish act for a local destination — step-0 selection, refusals and the selection snapshot, the request record and its durable create-only write, staging through two dedicated writer doors, head export, the local reveal at `<destination>/<corpus_id>`, the terminal report with its lifecycle entries in step order, resumption by reinvocation, and the marker-required arrival door
**Design:** `../superpowers/specs/2026-09-23-publish-act-local-design.md`
**Plan:** `../superpowers/plans/2026-09-23-publish-act-local.md`
**Discharged:** 2026-09-24 on `design/publish`, through `567edbf`; reproduction recorded at `06244b3`
**Runner:** `python/tools/cut40_acceptance.py`

## 1. What ran

The certified runner ran from the worktree `publish`'s `python/`, reached by
its canonical path rather than through the `.worktrees` symlink, at head
`567edbf`, with every `SCIENCE_CUT*_ROOT` and `SCIENCE_MM30_ROOT` export
spelled through the resolved main checkout, so its cut roots sat on the main
checkout's certified volume. Cut 40 chains **cut 39's** runner
(`PREFIX_RUNNERS = ("cut39_acceptance.py",)`), which retains the complete
live prefix back through cut 17's nineteen phases; cut 39's own chained
summary appears in the log ahead of cut 40's, confirming the prefix ran.
Cut 8 remains cited-not-run.

The runner's two final lines, verbatim from the main checkout's
`.work/acceptance/cut40-runner.log`, are:

```text
declared arms: 15 (= 15 declaration units; 6 guarantee rows)
guarantee rows exercised: 6 (6 newly closed: Y5, Y6, Y7, Y8, Y9, Y10)
```

Its own phases were:

```text
[cut40 phase 2/3] test_publish_act_acceptance.py
34 passed in 207.55s (0:03:27)
[cut40 phase 3/3] test_n2_cut40.py
10 passed in 116.97s (0:01:56)
```

The exit status was captured this time: the log's last line is
`RUNNER EXIT 0`, written by the reaping wrapper after the runner returned.
The full log has zero `FAILED`, `ERROR` or `Traceback` matches across
sixty-four clean pytest summaries. The wrapper exited and its process group
is gone.

This is the second run. The first, at `0f490bd`, failed in the prefix chain:
cut 19's N2 guard scored its J2i arm vacuous. The cause lies on `main`, not
this lane (§3.1), and the repair is `567edbf`.

Every prefix phase passed. Every one of the fifteen live checks resolved and
passed without sabotage; all fifteen mutations scored **sound**. No unit was
stale, vacuous, mixed or uncollected — `test_n2_cut40.py`'s ten tests are
where those verdicts are asserted, and they passed. Every unit homes exactly
one arm. Each check below is in
`python/tests/acceptance/test_publish_act_acceptance.py`:

| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| Y5-a | `test_y5_a_every_step_0_refusal_writes_nothing_durably` (9 cases) | `publish_request.py` | resolved | sound | Y5 closes |
| Y5-b | `test_y5_b_a_view_revised_between_evaluation_and_lock_refuses_durably` | `publication_doors.py` | resolved | sound | Y5 closes |
| Y6-a | `test_y6_a_the_selection_is_fixed_before_the_intent_…_durably` | `publish.py` | resolved | sound | Y6 closes |
| Y6-b | `test_y6_b_a_rewritten_snapshot_is_request_corrupt_durably` | `publish.py` | resolved | sound | Y6 closes |
| Y7-a | `test_y7_a_a_crash_after_k_staged_records_resumes_at_k_plus_one_durably` | `publish.py` | resolved | sound | Y7 closes |
| Y7-b | `test_y7_b_an_extra_staged_record_is_staging_corrupt_…_durably` | `publish.py` | resolved | sound | Y7 closes |
| Y8-a | `test_y8_a_a_publication_lands_at_its_corpus_id_…_durably` | `publish.py` | resolved | sound | Y8 closes |
| Y8-b | `test_y8_b_a_colliding_sibling_is_export_collision_…_durably` | `publish.py` | resolved | sound | Y8 closes |
| Y9-a | `test_y9_a_a_crash_at_every_local_step_resumes_…_durably` (8 boundaries) | `publish.py` | resolved | sound | Y9 closes |
| Y9-b | `test_y9_b_a_binding_beside_an_unfinished_intent_is_unresolved_durably` | `publish.py` | resolved | sound | Y9 closes |
| Y9-c | `test_y9_c_pending_lists_crashed_attempts_only_durably` | `publish.py` | resolved | sound | Y9 closes |
| Y9-d | `test_y9_d_a_crash_inside_step_9_is_finished_by_the_resume_durably` | `publish.py` | resolved | sound | Y9 closes |
| Y9-e | `test_y9_e_the_next_publish_reads_success_and_pre_binding_reports_durably` | `publication_doors.py` | resolved | sound | Y9 closes |
| Y10-a | `test_y10_a_a_second_world_admits_a_publication_…_durably` | `publication_arrival.py` | resolved | sound | Y10 closes |
| Y10-b | `test_y10_b_a_verified_root_with_records_beyond_its_selection_…_durably` | `publication_arrival.py` | resolved | sound | Y10 closes |

The check names are abbreviated where they exceed a table cell; the
declaration's `UNIT_CHECKS` cites each in full. Y5-a is parametrized over
nine step-0 refusals: `empty-selection`, `closure-incomplete`,
`pins-disagree`, `coordination-unpinned`, `selection-incomplete`,
`destination-unusable`, `operations-root-unusable`, `profile-disagrees` and
`evaluate_query`'s own `corpus-drifted`. `view-revised` is Y5-b's. Y9-a is
parametrized over eight step boundaries: before and after `_initialize`,
after `_populate`, `_admit_and_export`, `_write_sibling`, `_replicate` and
`_restore`, and before `_bind`. The phase's **34 tests** are those seventeen
cases, Y9-a's lost-sibling test
(`test_y9_a_a_lost_sibling_after_replication_is_rewritten_byte_identically_durably`),
the thirteen other unit functions, and the three Review Focus tests that are
not declaration units: `test_two_attempts_do_not_share_directories`,
`test_a_foreign_root_at_the_export_path_binds_nothing_durably` and
`test_resume_refuses_another_actor_and_another_profile_writing_nothing`.
This is the count the cut's §4 froze.

Each task's unit work passed on the certified tuple as it landed. Task 0's
engine probes: **7 passed** in `test_publish_engine_order.py`, with cut 39's
guards and the frozen-guard module green. Task 1's create-only write: **10
passed** in `test_durable.py`. Task 2's report amendment: **200 passed** over
the report, doors, stored and inertness modules, with no stale arm. Task 3's
permit: **642 passed** over the permit and boundary modules. Task 5's doors:
**717 passed** over the permit inventories, the capability boundary, the
staleness probe, `test_corpus_write.py` and `test_publication_doors.py`.
Task 6's act: **579 passed** with the boundaries, then **457 passed** after
its fix round, plus a throwaway certified-volume smoke (5 passed) that was
not committed. Task 7's arrival: **7 passed** in its module. Task 8's
acceptance module: **34 passed**. Task 9's guards: **29 passed** over the
recent-cut, staleness and frozen-guard modules, and the cut-40 fast loop at
`8 passed, 2 deselected`. Every arm was sensitivity-checked by hand one at a
time before the cut ran. `just test-fast` rose from **5536 passed, 1
skipped** at Task 2 to **5623** at Task 7. Pyright reported `0 errors` and
Ruff `All checks passed!` on every changed file at every code task, and
`tasks check` reported zero errors. No capability waiver or skip was used for
the discharge; `VERIFIABLY_UNCERTIFIED_HOST` was never set. The full
repository integration gate belongs to §6.

The new recent-cut entry is `(cut40, 40, (15, 15, 6))` and asserts the
guarantee-rows-exercised line above. That interface check mocks subprocess
execution; the actual chained run is the discharge evidence.

## 2. Accounting

**The frozen accounting, every verdict holding.** All of Task 0's engine
probes hold (§3.2), so no arm relies on a refused fact and none is declared
unrun. That gives **15 arms, 15 declaration units, 6 rows**, recent-cut row
`(15, 15, 6)`, and a phase of 34 passes. No row is read in part.

**Y5–Y10 open and close at this cut.**

- **Y5:** every step-0 refusal writes nothing, neither an intent nor a file
  under the operations root. That covers `view-revised` under the lock, and
  `evaluate_query`'s own refusal and each of the act's before it.
- **Y6:** the selection is snapshotted at step 0, before the intent, into
  `selection.v1`. That file is written create-only before `request.v1`, and
  population reads only it. A corpus that drifts after the intent does not
  strand the retry. A snapshot that disagrees with its request or intent is
  `request-corrupt`: reported and terminal.
- **Y7:** staging resumes from its true prefix. A hole, an extra, a byte
  mismatch or an unequal marker is `staging-corrupt`: reported alone, with
  staging retained.
- **Y8:** the local reveal is `restore_root`'s grant on
  `<destination>/<corpus_id>` against the create-only sibling. A second
  publication lands beside the first, and a colliding sibling is
  `export-collision` and binds nothing.
- **Y9:** a crash at every local step boundary resumes to exactly one binding
  and one report. Done means this attempt's binding exists and the intent is
  `closed`. A binding beside an unfinished intent fails closed with nothing
  written. The report carries its lifecycle entries in step order, and the
  next publish's step-0 fold reads every such report, whether it succeeded or
  was refused before the binding.
- **Y10:** a published corpus enters a second world only through
  `admit_publication`, which refuses before any write a root with no marker
  or with records other than the marker's selection.

The global corpus is **199 of 226 guarantee rows closed, 27 open**, up six
from cut 39's 193 of 226. The Y table's six new rows were banked at the
freeze and never selected until now. The accounting entry
`40: ("conformance-cut-40-results §2", "Y5, Y6, Y7, Y8, Y9, Y10", "")` in
`python/tools/roadmap_status.py` produces the roadmap's Appendix A, whose
totals line reads `Closed 199 of 226; open 27.`; no row is reopened. This is
the ninth off-path lane under roadmap rule 6, and it re-ranks nothing on the
dogfood path: the first belief publishes nothing.

`root.py` remains the one `atoms` importer. `publish.py`,
`publish_request.py`, `durable.py` and `publication_arrival.py` import
nothing of `atoms`. `publish.py` reaches the lifecycle only through
`root.py`'s wrappers. It gained two thin seams, `replicate_export` and
`read_serviceable`, because only `root.py` may name `replicate_root` and
`read_lifecycle_state`.

**The write inventories were checked in both directions.** Three new callers
of write primitives joined `WRITE_ENTRY_POINTS` in `test_permit_boundary.py`,
and each gained a `Case` in `test_permit_entry_points.py`'s `CASES`:

- `"corpus.py:CorpusWriter._stage_record": "corpus-write"`, since
  `self._corpus.add` is a primitive;
- `"corpus.py:CorpusWriter._stage_marker": "publish"`;
- `"publication_doors.py:_refuse_publication": "publish"`, which calls
  `execute_fulfilling`.

`test_the_inventory_is_closed_in_both_directions` and
`test_the_cases_cover_the_inventory_exactly` pass. `test_capability_boundary.py`'s
`RAW_WRITE_ALLOWLIST` gained `durable.py` `{unlink}` (Task 1: the create-only
write is plain POSIX outside every root, spec §4.4) and `publish.py`
`{rmtree}` (Task 6: step 9's discard of the private staging roots, spec §8).

The act-report oracle gains four entry kinds and the ordered-sequence rule;
the coordination contract is unchanged. The base contract, both base
`CONTRACT.yaml` copies and the TypeScript tree are unchanged.

## 3. Evidence

### 3.1 Frozen evidence and corrections

Cut 40's body remains byte-exact to its freeze. `git diff` over
`docs/designs/2026-09-24-conformance-cut-40.md` between `34e5537` and
`567edbf`, the head the cut ran at, is empty, and its §§2–7 hash to the
frozen SHA-256 above. This record's own commit changes the `**Status:**`
line and nothing else, as cut 39's did. The declaration remains at its
SHA-256, which the guard pins as `CUT40_DECLARATION_SHA256`, as cut 39's
does. No prior frozen declaration or cut body differs from the pre-lane
tree: the branch diff over `n2_arms_cut*.py` and the cut documents names
only cut 40's own.

**Cut 39's pinned lines untouched.** Cut 39's live arms pin seven lines in
`publication_doors.py` and `revise_coordination`'s seven-line guard block in
`corpus.py`. Tasks 2, 3, 5 and 6 each ended with `tests/test_arm_staleness.py`
green, and each pinned line occurs exactly once in its module. The
stale-arm probe was clean at every task. No prior arm was re-targeted.

**The J2i repair: cut 19's arm, vacuous since `main`'s `70ff54e`.** Run 1
failed at `test_n2_cut19.py::test_every_arm_fails_under_its_own_sabotage`:
J2i's two checks in `test_session_acceptance.py` kept passing under its
sabotage. The frozen arm removes the seam's
`self._state.unresolved = True` in `corpus.py`'s `_RoutedExecutor`.

- **Root cause, proven by bisection:** `main`'s `70ff54e` (`beliefs-40e593`,
  "port commits mark the root's shared writer state unresolved"). It made
  `DurableOperationPort` in `root.py` call `mark_root_unresolved` on the same
  process-wide state in `append_intent` and both execute paths. The
  guarantee then had two holders, and a single-site sabotage of one could not
  fail a check that runs through both.
- **Bisection:** the guard passes at `38ae515` (`70ff54e`'s parent) and fails
  at `70ff54e`, at `b9cd8b6` (this lane's baseline) and at `0f490bd`.
- **Repair:** `567edbf` (`beliefs-50067c`) follows the cut 31 document §8.3
  precedent, where cut 22's `M8a` premise was restored additively. Both J2i
  checks in `test_session_acceptance.py` patch
  `science_root.mark_root_unresolved` to a no-op for the faulted add, so the
  seam's own mark is again the only thing that can set the state. The frozen
  declaration, the sabotaged source and `70ff54e`'s fix are untouched.
- **Consequence:** `main`'s cut-19 guard has been red since `70ff54e`, and the
  cut-40 merge carries the repair. The repair lands on this branch, not on
  `main` first (Ruling 12).

**The count the cut froze.** Task 0 wrote *n* = 34 into §4, counted from
Task 8's planned code (Ruling 2). Task 8's module collected 34, so no
superseding note is needed.

### 3.2 The planning notes, the engine verdicts and the deviations

**The planning notes the spec carries (§18, "at planning").** Every one
landed as written:

- The staging profile is the caller's: step 0 refuses `profile-disagrees`
  before the intent, and a resume under another profile writes nothing.
- `_stage_record` applies only the record-local refusals.
- `staging-corrupt` carries `refs`, a tuple of zero or one record ids.
- `PublishRefused` carries the last entry's outcome type, and the unresolved
  value is `PublishUnresolved`.
- The completion reading is `publication_doors.attempt_reading`, read by the
  fold's own rule.
- The binding's `artifact` is the SHA-256 of the sibling's bytes.
- `_bind_publication(lifecycle=())` and `_open_publication(expected_view=None)`
  keep cut 39's behaviour.
- Crashes are injected by monkeypatching the act's named step functions.
- Six arms are reshaped so that each check sees its sabotage (Y5-a, Y6-a,
  Y9-c, Y9-d, Y10-a, Y10-b).
- The destination and the operations root are resolved once, at entry.

**The engine verdicts.** Task 0's probes, in
`python/tests/test_publish_engine_order.py` on the certified volume, pin the
engine facts resumption relies on:

- `INIT_RETRY = "holds"`, `ADMIT_RETRY = "holds"`, `EXPORT_STABLE = "holds"`,
  `REPLICATE_RETRY = "holds"`, `REPLICATE_AFTER_RESTORE = "holds"` and
  `READ_SERVICEABLE = "holds"`: each lifecycle step, reinvoked, converges on
  this attempt's state, the export is a pure function of the chain, and a
  restored copy opens read-only.
- `FOREIGN_REPLICA = atoms.coordinator.lifecycle.RootOperationMismatch`:
  another corpus's replica at the export path, serviceable or not, refuses
  this replication with that exception. It is never adopted as this
  attempt's copy, and Task 8's foreign-occupant test asserts exactly that
  type.

The cut's §5 records all seven.

**Every "read at freeze" choice.** The cut froze before its code existed.
Each sabotage `before` was read from the tree after Task 8 and checked for
exactly one occurrence and an `after` that parses.

- Y6-a's `before` spans the records line, the snapshot-record assertion
  `_require_snapshot_records(read, records)` added at Task 6's fix round, and
  the `opened = _open_publication(...)` statement (Ruling 10). Its `after`
  re-evaluates the selection after the intent, over a fresh epoch.
- Y9-e's `after` restores cut 39's exactly-one-entry rule ahead of the
  sequence fold.

**Deviations from the plan**, each gate-forced or fail-early, and each
reviewed:

- **Task 1:** `ensure_directory` raises `FileExistsError` for a file in the
  way, not the plan's `NotADirectoryError`. `durable.py` joins
  `RAW_WRITE_ALLOWLIST` (Ruling 4).
- **Task 2:**
  - `report.__all__` is extended by `__all__ +=`, because cut 3's T1/T8 arms
    pin the list's tail.
  - `publish_sequence_error(sequence)` and `publish_entries_from_facet(rows)`
    are renamed from `entries`, because a T1 inertness test bans public
    `entries` parameters.
  - `PreBinding` is `@final`.
  - Review fix: a non-string stored outcome type or kind refuses
    `MalformedRecord` rather than raising `TypeError` (Ruling 5).
- **Task 3:** a second hard-coded permit assertion
  (`test_publishes_constructs_exactly_the_kernel_requirement`) was updated.
- **Task 4:**
  - The dataset fixtures use pinned-digest resources, since `resources=()`
    raises `BasisMissing`.
  - Review fix: the plan's `node.body != ""` canonicality check is removed,
    because bodies are hand-editable prose. The plan's `text + "\n"` "not
    canonical" case is the canonical rendering of another record, so it was
    replaced by a genuinely non-canonical mutation of the same id
    (Ruling 6).
- **Task 5:**
  - The same `+ "\n"` case was replaced, here with a quoted title.
  - The tests share one `DefaultExecutor` factory and use the module's
    existing `Doors` scaffold instead of a new `_pair`. They read
    `RecordingPort`'s `calls`.
- **Task 6:**
  - `root.py` gains the two seams above, and `publish.py`'s `rmtree` is
    allowlisted.
  - Review fixes (Ruling 9): the snapshot records are asserted before the
    intent, by the snapshot rule and by each text re-parsing equal to the
    captured record, where the plan built them after. A finished resume no
    longer reads `request.v1`.
- **Task 8:**
  - `pins-disagree` keeps the view's dataset-and-run query, because a
    dataset-only query hits `closure-incomplete` first.
  - `coordination-unpinned` asserts `PublicationRefused`, refused at step 0
    before the lock (spec §4.1), not the plan's `ValidationRefused`.
  - Y5-b pins the evaluated tip's uid.
  - Review fix: Y6-b rewrites a decodable snapshot, so that only the identity
    check refuses it. Its sensitivity is proven.
- **Task 9:**
  - The freeze test matches whitespace-normalised text, because the frozen §4
    wraps a phrase across a line.
  - Y6-a's `before` is spelled as above, and it re-evaluates the selection
    after the intent.
  - `CUT40_DECLARATION_SHA256` is added, as cut 39's guard does.
  - Y9-b's and Y10-a's sabotages were copied from the plan table and drift
    from the frozen §5 prose, but both remain sound kills. Y9-b's replaces
    the `binding-without-report` return with `pass`, so the classifier falls
    through past that state. Y10-a's disables the absent-marker refusal
    rather than the whole count.

**Fixes outside the task briefs**, each tested:

- `attempt_reading` raises `MalformedRecord` on a chain that is not
  well-formed and on two intents sharing a token (Ruling 8).
- `_stage_marker`'s display-facet and governed-stamp guards were deferred to
  the final-review fix wave (Ruling 7). Population byte-compares the marker
  to the factory's output before anything builds on it.

**Post-discharge fixes.** The whole-branch review after discharge at
`9428a31` found two findings, fixed in one dispatch at `65bfe1d` (Ruling
13). Neither edits the frozen declaration: every one of cut 40's fifteen
`before` lines still occurs exactly once in its module, cut 39's pinned
lines did not move, `test_arm_staleness.py` passes, and
`test_publish_act_acceptance.py` (34 passed) and `test_n2_cut40.py` (10
passed, sabotage audit included) re-ran green against the changed source.

- **`_stage_marker`'s guards, `65bfe1d`** — spec §5 requires the
  display-facet and governed-stamp guards on both staging doors, and only
  `_stage_record` ran them. `_stage_marker` now runs both beside
  `_refuse_facet_shapes`, under `_stage_record`'s message shape, and names
  the record by `node.id` (every caller passes the factory's `Node`). The
  marker's closed content rule and the facet-payload check refuse such a
  marker first, so the unit test asserts the refusal armed and, with those
  two disarmed, that the guard itself refuses
  (`test_stage_marker_runs_the_display_facet_and_governed_stamp_guards`).
- **A corrupt staging file, `65bfe1d`** — `_population` read the staging
  store through `iter_stored`, and a file `nodes` refuses to read raised a
  raw exception, so every resume raised, the attempt stayed `unfinished` and
  `pending_publishes` listed it for good. Probed: garbage, non-UTF-8 and
  malformed frontmatter raise `ValidationError`, a record off its mapped
  path `PlacementError`, a duplicate uid `CollisionError`; nothing raises
  `MalformedRecord`. Those three now return `StagingCorrupt(corpus_id,
  "bytes", ())`, naming no record since none can be read to name (Y7;
  `test_an_unreadable_staging_file_is_corrupt_bytes`).

The deferred minors in §3.3 and the review's other minors are filed as
`beliefs-1ce6cc` (priority 3).

### 3.3 Review findings and limitations

Every task was reviewed against the spec before the next began. Task 2's
review found the decoder's `TypeError` gap, Task 4's the canonicality check,
Task 6's the late snapshot assertion and the dead request decode, and Task
8's Y6-b insensitivity. Each was fixed in a round of its own and re-reviewed
clean.

The deferred minors, carried to the final review (§6) and filed after it as
`beliefs-1ce6cc`:

- `_refuse_publication` does not check that its entries' subject equals the
  intent's binding address.
- `_stage_record` parses before the permit check, so a raw `nodes`/YAML
  exception escapes on bad text.
- A resume writes a `request-corrupt` report before the staging-profile pins
  check when the request decodes but the snapshot is bad.
- `_initialize` tests for `corpus.yaml` instead of catching
  `ManifestAlreadyPresent`.
- `admit_publication` lets a raw `nodes` parse exception escape on a
  byte-corrupted record file, the repository-wide `iter_stored` pattern.
- `PUBLISHING_COORDINATION` hard-codes versions `(1, 2)`.

The spec's §16 limitations stand, and none reopens a row:

- Crashes are exceptions at step boundaries, not kills at engine stages.
- The create-only write rests on POSIX `fsync` and `link`.
- Step 9 uses `rmtree`.
- `publish` has no public route.
- Remote destinations refuse until cut 41.
- A foreign root at `<destination>/<corpus_id>` leaves the attempt
  unfinished and listed by `pending_publishes`.

The spec's §4.1 is amended in the same commit as this record. The code runs
the operations-root and destination checks first, once and resolved, and it
asserts the snapshot records before the intent.

## 4. Reproduction measurement

The reproduction record's §19
(`../designs/2026-09-05-mm30-reproduction.md`) records the run at `ab1b572`,
committed at `06244b3`. `reproduction.rederive` read the established mm30
corpus in place; no contract succeeded, so nothing was recreated or moved
aside. The result was the same `NoBelief` payload, with
`rederived_equal: true`. The complete `state.json` was byte-identical, with
SHA-256 `1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`
before and after, the same digest §18 recorded. The driver reaches none of
this slice's surfaces (`publish.py`, `publish_request.py`, `durable.py`, the
staging doors, `publication_arrival.py`): mm30's world publishes nothing.

## 5. Remaining boundary

`publish` stays open, in the ledger's table and the roadmap's boundary
index, tier 1 off the path. **Y5–Y10** are closed. What remains is cut 41,
the remote slice (`beliefs-3ce305`):

- the transport seam and layer design §6.1 step 7;
- the remote reveal and the orphans it creates;
- cut 39's Ruling 12: an exception before any effect at step 8 leaves the
  intent unfinished, not orphaned, so a remotely revealed marker must be
  recovered from the unfinished intent;
- the recovery table's remote rows;
- the recipient's `divergent-publication`.

It appends its own rows to the Y table.

**L1** remains partial on its persistence arms: kill the executor between
entry durability and apply at every stage; crash after entry durability but
before the transaction record stores the entry digest; cut persistence at
every stage of the settlement sequence for both terminal arms. These belong
to `persistence-cut` (`beliefs-3ea822`, tier 2), behind `atoms-f5779f`. Cut
40 reads no L1 arm.

One local recovery-table row is not exercised by this cut: a **bare
reservation** at the export root, left by a crash inside `replicate_root`
before it stamps. That state exists only between engine stages, so a crash
injected at the act's step boundaries cannot reach it. Its resumption,
`replicate_root`'s exact retry adopting the retained claim, is the engine's
predicate, and killing the process mid-replication is `persistence-cut`'s
harness. `REPLICATE_RETRY` pins the completed retry, not the bare one.

**T7** remains partial on its cross-root case, owned by
`cross-root-publication` (`beliefs-256f17`, tier 3). Cut 40 reads no T7 arm.

## 6. Main integration

Filled at merge: the whole-branch review, the repository gate on the exact
integrated head, and the merge into `main`.

## 7. Execution rulings

- **Ruling 1: Review Focus 4's test lives in Task 8.** The plan text was
  corrected at `2b4de49`: Task 6 Step 1 and the self-review both place it
  there, and it needs a real chain.
- **Ruling 2: Task 0 writes *n* = 34 into §4.** The count is Y5-a's 9, Y9-a's
  8, the lost-sibling test, 13 other unit functions, and the two-attempts,
  foreign-root and resume-refusal tests, counted from Task 8's code. Task 8
  must not edit the frozen document; a later mismatch would take a
  superseding note.
- **Ruling 3: Task 12's merge into `main` waits for the user.** The
  controller does not execute it without asking, since a merge is an
  outward-facing stop. The plan's other Task 12 steps, the final review and
  the gate, run.
- **Ruling 4: `durable.py` joins `RAW_WRITE_ALLOWLIST` in Task 1.** Spec
  §4.4 places the create-only write outside every root as plain POSIX, and
  no later task owns the entry.
- **Ruling 5: the decoder gap in Task 2 is fixed, not accepted.** The plan
  let a non-string outcome type or kind escape as `TypeError`. The spec's
  fail-closed rule makes malformed stored bytes `MalformedRecord`, as the
  sibling binding decoder already guards.
- **Ruling 6: the plan's "not canonical" snapshot case is wrong against spec
  §4.3.** `text + "\n"` is the canonical rendering of a different record
  (the same id, body `"\n"`). It is replaced with a truly non-canonical
  mutation, and the body check is dropped.
- **Ruling 7: `_stage_marker`'s missing guards go to the final-review fix
  wave.** The display-facet and governed-stamp guards are not a Task 5 loop.
  Population byte-compares the marker to the factory's output first, so
  nothing downstream builds on the gap.
  Resolved at `65bfe1d`: the fix wave added both guards (§3.2,
  post-discharge fixes).
- **Ruling 8: `attempt_reading` fails early.** It raises `MalformedRecord`
  on a chain that is not well-formed and on two intents sharing a token, and
  the act lets that propagate with nothing written. Spec §9's
  `indeterminate` covers a report the fold refuses, not a corrupt chain.
- **Ruling 9: Task 6's two plan-mandated Importants are fixed.** The
  snapshot records are validated before `_open_publication`, per spec §4.1
  item 8 and §4.3 and Y5's "a step-0 refusal writes nothing". The unused
  `request.v1` decode in resume's done branch is dropped.
- **Ruling 10: Y6-a's `before` spans the new validation.** It covers the
  records line, the validation statement and the `opened =
  _open_publication(...)` statement, since every `before` is copied from the
  tree after Task 8.
- **Ruling 11: the chained runner is the controller's.** Task 9's
  implementer did Steps 1–4 and the guard run and committed. The controller
  launched the detached cut runner through `detached.sh` and read its log,
  because subagents park on long waits and end uncommitted.
- **Ruling 12: the J2i repair lands on `design/publish`.** It is its own
  commit with its own filed and closed task (`beliefs-50067c`), not a
  commit on `main` first. Every code change goes through a worktree, and this
  lane's merge carries the repair to `main`. `main`'s cut-19 guard stays red
  until then, as it has been since `70ff54e`.
- **Ruling 13: one fix dispatch after the final review** for the marker
  door's guards and the corrupt staging file, then the cut-40 phase modules
  re-run (§3.2). The review's minors went to one follow-up task,
  `beliefs-1ce6cc`, not to this lane.
- **Every implementer ran in the foreground and committed before
  returning.** The lane's detached runs, both chained cut runners, went
  through the reaping wrapper, and each process group was confirmed gone.
  The repository gate has not run yet; §6 records it.
