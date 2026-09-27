# Conformance cut 42 — results

**Cut:** `../designs/2026-09-27-conformance-cut-42.md`
**Freeze:** `a2a73748269358c4e407e64451b3df8e22970d7c`; SHA-256 `5887bb87dc30d7451c3302651d546aa941cea70be6e99b7223fbd537d45faf35`
**Declaration:** `python/tests/n2_arms_cut42.py`; SHA-256 `ba1bfb07fec063c2eccac6b351267e177afc13151be8ac37f7a3aa21a0523503`
**Subject:** the remote publish act, its durable transport mark, verified upload, terminal orphans, resumption, and the recipient's current or divergent publication reading
**Design:** `../superpowers/specs/2026-09-26-publish-act-remote-design.md`
**Plan:** `../superpowers/plans/2026-09-27-publish-act-remote.md`
**Discharged:** 2026-09-27 on `design/publish`, implementation through `f625e21`; reproduction recorded at `ee07bf6`
**Runner:** `python/tools/cut42_acceptance.py`

## 1. What ran

The runner ran from `.worktrees/publish/python` through `host-budget run --
uv run --frozen python tools/cut42_acceptance.py`, with `SCIENCE_MM30_ROOT`
on the main checkout's certified volume. Its tracked foreground command
exited 0. The log is `.work/acceptance/cut42-runner.log` in the main checkout.
Cut 42 chains cut 41 (`PREFIX_RUNNERS = ("cut41_acceptance.py",)`), retaining
the full historical live prefix; cut 8 remains cited-not-run. Every prefix
phase passed. The log contains 68 completed pytest phases and 1078 passing
test invocations, including inherited repetitions; reported pytest phase
time totals 3187.99 seconds. No full-run refusal, abort or retry occurred.

The cut's own phase summaries and accounting lines, verbatim:

```text
[cut42 phase 2/3] test_publish_remote_acceptance.py
31 passed in 213.68s (0:03:33)
[cut42 phase 3/3] test_n2_cut42.py
10 passed in 84.87s (0:01:24)
declared arms: 14 (= 14 declaration units; 6 guarantee rows)
guarantee rows exercised: 6 (6 newly closed: Y11, Y12, Y13, Y14, Y15, Y16)
```

The guard's passing baseline assertion establishes every named check as
resolved; its audit assertion establishes all fourteen mutations as sound.
No arm is stale, vacuous, unresolved or uncollected. Each unit below homes
one arm, with no co-citation. Checks are in
`python/tests/acceptance/test_publish_remote_acceptance.py`.

| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| Y11-a | `test_y11_a_a_listing_that_disagrees_is_transport_incomplete_durably` | `publish.py` | resolved | sound | Y11 closes |
| Y12-a | `test_y12_a_a_crash_inside_push_leaves_the_mark_and_blocks_the_next_publish_durably` | `publish.py` | resolved | sound | Y12 closes |
| Y12-b | `test_y12_b_a_resume_after_the_mark_never_rereads_staging_durably` | `publish.py` | resolved | sound | Y12 closes |
| Y12-c | `test_y12_c_a_mark_disagreeing_with_its_export_fails_closed_durably` | `publish.py` | resolved | sound | Y12 closes |
| Y13-a | `test_y13_a_an_abandoned_transport_is_an_orphan_the_next_publish_supersedes_durably` | `publication_doors.py` | resolved | sound | Y13 closes |
| Y13-b | `test_y13_b_an_orphan_named_by_an_abandoned_attempt_is_not_retired_durably` | `publication_doors.py` | resolved | sound | Y13 closes |
| Y13-c | `test_y13_c_an_export_damaged_after_the_mark_closes_as_an_orphan_durably` | `publish.py` | resolved | sound | Y13 closes |
| Y14-a | `test_y14_a_a_stranded_marked_attempt_blocks_until_resumed_durably` | `publish.py` | resolved | sound | Y14 closes |
| Y14-b | `test_y14_b_an_attempt_without_a_mark_never_blocks_durably` | `publish.py` | resolved | sound | Y14 closes |
| Y15-a | `test_y15_a_a_crash_at_every_remote_step_resumes_to_one_binding_and_one_report_durably` | `publish.py` | resolved | sound | Y15 closes |
| Y15-b | `test_y15_b_a_remote_step_8_refusal_is_an_orphan_the_next_publish_names_durably` | `publish.py` | resolved | sound | Y15 closes |
| Y16-a | `test_y16_a_a_recipient_restores_admits_and_reads_the_current_publication_durably` | `transport.py` | resolved | sound | Y16 closes |
| Y16-b | `test_y16_b_sibling_publications_are_divergent_until_one_supersedes_both_durably` | `publication_arrival.py` | resolved | sound | Y16 closes |
| Y16-c | `test_y16_c_a_held_root_with_an_unreadable_record_file_refuses_capture_damaged_durably` | `publication_arrival.py` | resolved | sound | Y16 closes |

Before the complete runner, the Task 8 pilot checked that all fourteen
source strings occurred once, every mutated module parsed, and Y11-a
resolved at baseline and scored sound under sabotage. Its temporary copies
were removed. The recent-cut row is `(cut42, 42, (14, 14, 6))`, including
the guarantee-rows-exercised line; that interface test mocks subprocesses,
while the chained runner above is the discharge evidence.

## 2. Accounting

**14 arms, 14 declaration units, 6 guarantee rows. Y11–Y16 close in full.**
Every frozen arm held, so none is rehomed and no cut supplement is needed.

- **Y11:** the act verifies the remote namespace's complete listing and bytes.
- **Y12:** the durable mark precedes upload, binds to the export and sibling,
  and makes resumption independent of staging and the request.
- **Y13:** incomplete transport and damaged export close as standing orphans;
  those orphans retire none of the prior marker tips.
- **Y14:** marked unfinished attempts block another publication at step 0;
  an unmarked attempt does not block.
- **Y15:** remote step boundaries resume to one binding and one ordered report;
  a remotely revealed step-8 refusal becomes an orphan.
- **Y16:** recipients restore, admit and read current or divergent tips from
  held roots, refusing damaged captures and missing intermediates.

The corpus is **210 of 237 guarantee rows closed, 27 open**, up six from
cut 42's freeze at **204 of 237**. No row reopens. The accounting entry
`42: ("conformance-cut-42-results §2", "Y11, Y12, Y13, Y14, Y15, Y16", "")`
in `python/tools/roadmap_status.py` generates Appendix A with
`Closed 210 of 237; open 27.` The Y table is closed in full across cuts 39,
40 and 42. This third and last `publish` slice is off the path and re-ranks
nothing on the path; `contract-cut` becomes the first off-path boundary.

## 3. Evidence

### 3.1 Frozen evidence and boundaries

The cut's body is preserved byte-exact to the freeze; this results change
edits its `**Status:**` line only. The declaration retains the SHA-256 above.
The frozen guard pins every prior declaration; the stale-arm probe is clean,
with every prior pinned line untouched. No prior arm was retargeted.

Task 7 collected **31 acceptance cases**, exactly the cut's §4 count:
24 parametrized cases from fourteen named units and seven additional cases.
The complete runner confirms 31 passes. No accounting correction is needed.

`root.py` remains the one `atoms` importer. Its `evaluate_copy` uses the
recipient restore evaluation with a no-op grant and returns an outcome
string; engine exceptions are translated there, including
`LogEvidenceRefused` for an unreadable record. `export_chain_head` returns
`None` when the engine refuses the export's chain. `transport_files` scans
the complete root, including chain files, and the head-artifact sibling;
`.metadata` stays outside the transport. `publication_tip` and
`admit_publication` share `require_publication_layout` in
`publication_arrival.py`.

Both permit inventories were checked in both directions:
`WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and `CASES` in
`test_permit_entry_points.py` remain unchanged. The remote act uses existing
`_refuse_publication` and `_bind_publication` entries; the durable mark is
outside every corpus. There is no new write primitive or permit entry point.

### 3.2 Engine facts

Task 0's certified probe passed all seven required verdicts:

| probe | verdict |
|---|---|
| `EXPORT_LAYOUT` | holds |
| `CHAIN_HEAD_SERVICEABLE` | holds |
| `EVALUATE_INTACT` | holds |
| `EVALUATE_DELETED` | holds |
| `EVALUATE_ALTERED` | holds |
| `EVALUATE_WRITES_NOTHING` | holds |
| `DAMAGE_WRITABLE` | holds |

`CHAIN_DIR = .#~chain`; the probed top level was
`['.#~chain', 'corpus.yaml', 'run']`. Additional observations:
`EVALUATE_UNREADABLE` raises `beliefs.errors.LogEvidenceRefused`;
`EVALUATE_UNDECODABLE` answers `refuted`; damaged chain-head reads raise
`atoms.chain.errors.ChainStateInvalid`; deleted or unreadable chain-head
reads raise `atoms.core.errors.PreconditionRefused`; evaluating with the
chain deleted answers `refuted`. All translations stay in `root.py`.
No alternate `audit_log` probe was required.

### 3.3 Planning notes and deviations

The approved spec's §17 planning notes were implemented as follows (the
notes are retained here to keep the discharge evidence self-contained):


- 2026-09-27 — at planning (plan `../superpowers/plans/2026-09-27-publish-act-remote.md`):
  - **The export evaluation is `root.evaluate_copy(dest_root, subject,
    observers) -> str`**: `_restore_root`'s outcome with a grant that does
    nothing, the recipient's own evaluation, or `"unreadable"` when the copy
    cannot be read to be judged (`OSError`, `LogEvidenceRefused` from an
    unreadable record, or the engine refusing its chain as state, translated
    inside `root.py`). Task 0 pinned that it validates an
    intact serviceable export, refuses one with a selected record deleted,
    altered, unreadable or undecodable, and writes nothing. `audit_log` was
    not chosen: it requires the target to be a configured corpus root, and an
    export root is in no world.
  - **§4.2's checks are identity only; the marker's content waits for the
    evaluation** (plan review, round 1). Before anything else, the resume
    checks the mark against its intent, the export's manifest, the sibling's
    SHA-256, subject and chain head (`root.export_chain_head`, which answers
    `None` for a chain the engine refuses as state), and the export's one
    `publication` file by its path. It reads no record's content. It then
    evaluates the export. A failed evaluation closes the attempt
    `transport-incomplete` (`export-damaged`) with its orphan, so a damaged
    selected record never strands the destination as `transport-mark-corrupt`.
    Only after `validated` does it read the marker file and check its shape
    (`publication_content_malformed`, `marker_consistent`), its uid and its
    selection count. A disagreement there is `transport-mark-corrupt`. Step 7
    evaluates again before `push`, binding the uploaded bytes to the judged
    ones. A resume therefore evaluates twice, and a fresh run once.
  - **An `OSError` while reading an export file for either listing is
    `export-damaged`** (§4.3 steps 1 and 3). The listings read every byte, and
    a file the act cannot read is damage the evaluation would also find.
  - **`publication_layout_refusal` is spelled `require_publication_layout(records)
    -> None`**, which raises `PublicationArrivalRefused`. Raising keeps cut
    40's Y10-a and Y10-b pins byte-exact. `publication_tip` catches it and
    raises `PublicationReadingRefused` with the same reason and refs.
  - **The layout check runs on every held root that holds any `publication`
    record**, before the address filter. The address of a malformed marker
    cannot be read, so a root whose only marker is malformed refuses the
    reading rather than being skipped as "another view's".
  - **`capture-damaged` catches exactly the store's four read refusals**:
    `OSError` (an unreadable file answers `PermissionError`, probed),
    `nodes`' `ValidationError` (undecodable bytes, probed), `PlacementError`
    and `CollisionError`. These are `_population`'s three plus `OSError`.
  - **`PublicationReadingRefused(reason, corpus_id, refs=())`**, where
    `corpus_id` is `None` for the two readings that are not one corpus's:
    `supersession-cycle`, and `marker-duplicated` across corpora.
  - **`require_usable` returns the frozen `Destination`** in place of a path:
    the resolved local directory, or the remote destination as given.
  - **The mark codec lives in `publish_request.py`** beside the snapshot and
    request codecs: `TransportMark`, `encode_mark`, `decode_mark`, and
    `MARK_DOMAIN = "science.publish-transport.v1"`.
  - **Steps 7–9 run over `_Remote`**, which holds the writer, the resolver,
    the opened intent, the operations directory, the clock, the seam, the
    port and the transport, and never the request or the snapshot
    (decision 5). A fresh run builds it from `_Attempt.remote()`.
  - **`PublicationRefused` gains `tokens`**, the blocking tokens in
    ascending order.
  - **`PreBinding.orphan` defaults to `None`**, so every existing
    construction and comparison stands.
  - **`publish-unfinished` runs for a remote destination only.** A local
    destination can hold no mark (§4.1), and not reading its chain keeps cut
    40's step-0 refusal order untouched.
  - **The listing identity** is `v1.digest("science.publish-transport-listing.v1",
    <expected listing as a mapping>)`, 64 lowercase hex.
  - **Crashes are injected by monkeypatching the act's named step functions**,
    cut 40's plus `_mark`, `_push` and `_verify`.
  - **Two sabotages are spelled for one-edit form:**
    - Y12-a deletes the mark's write. For a crash inside `push`, that is
      indistinguishable from a mark written after `push` returns.
    - Y16-c reads a damaged root as holding nothing. That is what a
      report-mode capture does to the one unreadable file, over a root
      whose only other content the check does not need.

- 2026-09-27 — Task 7 acceptance execution: Y16-b reads the epoch refusal
  through `AddressMapConflict.finding.code`, the existing typed interface.
  The plan assumed `args[0]` held the `Finding`; it holds the formatted error
  message. The required `duplicate-location` code and the sibling-publication
  assertions are unchanged.


Additional execution adjustments:

- Task 0 merged main at `16a00f5` before freezing, as the plan required;
  the merged baseline passed `just test-fast` (5709 passed, 1 skipped).
- Task 1 review found that `os.walk` silently skipped an unreadable
  directory. Its `onerror` now raises; a regression check covers the refusal.
- Task 2's isolated fast suite passed after a concurrent replay failure;
  review found no diff-linked cause.
- Task 5 enumerates before a fresh mark, then translates post-mark
  `OSError` and `MalformedRecord` during enumeration to `export-damaged`.
  It follows the concrete `str` signature for `evaluate_copy` despite the
  brief's introductory `LogReport` annotation.
- Task 6's event-token mutation is `marker-malformed`: the existing shared
  classifier checks uid/event-token agreement before consistency. The test
  expectation was corrected without changing that classifier.
- Task 7's Y16-b uses `AddressMapConflict.finding.code`; `args[0]` is text.
- Task 8 copied actual source spellings for Y13-b (the orphan comment has
  no decision-3 suffix) and Y16-c (the exception constructor has two
  arguments). Both planned sabotage behaviors are preserved; no prior
  declaration or production source changed to fit them. The focused guard
  run found these differences, and they were corrected before the pilot.
- Task 10 checked main (`026f208`): no later lane results record has landed,
  so no higher-numbered re-rank is required. The ledger retains discharged
  `publish` integration status in prose until Task 11 closes `beliefs-1a5157`.
  The open-boundary row leaves with the roadmap row: the existing equality
  guard requires their boundary sets to agree. This is a documentation
  placement adjustment to the plan, not a test waiver.

### 3.4 Final whole-branch review fixes

Review at `e8964e2` found two issues. A nonregular or dangling
`transport.v1` was treated as absent by `is_file()`: another publish could
start, and a resume could close on a corrupt request without recording an
orphan. Resume also followed a symlink to a regular mark and let unreadable
mark errors escape. Adjacent `lstat()` checks now keep nonregular marks
blocking and answer `PublishUnresolved("transport-mark-corrupt")` before
reading the request; mark read errors receive the same unresolved verdict.
The original step-0 and resume sabotage anchors remain byte-exact.

Five additional regression cases cover a directory, dangling symlink,
symlink to a valid mark, unreadable file, and FIFO, each after a partial
upload and with a corrupt request. They assert blocking, unresolved resume,
an unfinished attempt, an unchanged chain tip, and no report. All five
failed before the fix and pass afterward. These supplement the frozen
31-case evidence above; no frozen declaration or cut body changed.

The second finding was a `capture-damaged` message missing the caught store
error required by spec §7.1. `PublicationReadingRefused.__str__` now includes
its explicit cause for that reason, preserving the constructor, `refs`, and
Y16-c's raise anchor. Four unreadable/undecodable capture assertions failed
before this change and pass afterward.

Focused validation: 7 remote cases passed (the five regressions plus Y12-b
and Y14-b); 64 publish, arrival, and arm-staleness tests passed. Ruff and
Pyright passed; `tasks check` reported zero errors and zero warnings.
The cut 42 N2 guard passed all 10 tests in 87.82 seconds, including the
frozen declaration/body checks, baseline checks, and all fourteen sabotages.
Scoped re-review approved both fixes at `f697ba6`. The repository gate on
that head exited 0: 5815 Python tests passed with 1 skip, standalone N2
passed 46 tests, and TypeScript passed 155 tests in 7 files. All static
checks passed. The log is `.work/acceptance/cut42-gate.log` in the main
checkout. Main integration is recorded in §6.

## 4. The reproduction

`2026-09-05-mm30-reproduction.md` §21 records the certified preflight and
re-derive. The answer remains `NoBelief(no-directional-outcome)` and
`rederived_equal` remains true. `state.json` is byte identical, SHA-256
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`
before and after; `cmp` and `diff -u` both exited 0. The driver supplies no
remote destination or transport and reads no publication tip. This re-run
measures compatibility, not the remote guarantees: mm30 publishes nothing.

## 5. Remaining boundary

`publish` is discharged in full: publication records at cut 39, the local
act at cut 40 and the remote act at cut 42. L1 remains under
`persistence-cut`; exception injection at act step boundaries does not
certify kills inside transport or engine operations.

Spec §13's three recipient questions remain open: retiring a superseded
corpus through the registry lifecycle; acquiring a missing intermediate;
and a world index over overlapping publications (`beliefs-81367e`). They
are recorded in `../guide/open-questions.md`. The tip reading itself needs
no epoch; ordinary world reads still refuse `duplicate-location` for
shared selected records across held publications.

## 6. Main integration

Pending Task 11: whole-branch review, repository gate, lane-goal closure,
and main integration. Fill the merge and gate evidence here at integration.
No claim of a completed merge is made by this results record.

## 7. Execution rulings

- Preflight 2026-09-27: both worktrees clean; cut 42 unclaimed across local branches. `main` has Python changes since a38d6ff (five commits), so Task 0 must merge main and rerun `just test-fast` per Step 1. Ruling: perform that merge inside design/publish before freezing — the plan explicitly prescribes it; cost if wrong: integration conflicts or changed pin baseline require another fix.

- Task 5: Ruling: call transport_files before writing a fresh mark and translate post-mark enumeration OSError/MalformedRecord to export-damaged — spec §3.1 requires nonregular entries to refuse before mark, while §4.3 and planning note classify damaged export reads after mark; cost if wrong: an abnormal export may be classified as early refusal or terminal damage at the wrong boundary.

- Task 5: Ruling: root.evaluate_copy returns str as the concrete Step 3 and approved spec planning note require, despite the brief's introductory LogReport annotation — cost if wrong: a future caller expecting a LogReport needs the public signature corrected.

- Task 6: Ruling: the plan's `_inconsistent` fixture (mutated event_token) expects marker-inconsistent, but the existing shared publication_content_malformed classifier tests uid/event-token agreement first and returns marker-malformed; keep the classifier and correct that test expectation — cost if wrong: this case no longer exercises the marker-inconsistent branch, which may need a different reachable fixture later.

- Task 7: Ruling: Y16-b asserts AddressMapConflict.finding.code, not args[0].code as the plan says — the exception constructor stores the Finding on .finding and formats args[0] as a string; cost if wrong: the acceptance arm would target the wrong public detail, but still requires duplicate-location.

- **Task 8 source-spelling ruling:** use the implemented Y13-b orphan
  comment and Y16-c two-argument exception constructor as sabotage anchors;
  preserve the planned behavior and every prior pin (§3.3).
- **Task 10 closeout ruling:** record `publish` as discharged now, remove
  its roadmap boundary and the ledger's matching open-boundary row. Keep
  the integration status in Current state prose until Task 11 closes
  `beliefs-1a5157`. The plan's literal temporary row retention would fail
  the existing boundary-set equality guard; prose preserves its intended
  goal-close timing without weakening that guard.
