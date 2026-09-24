# Conformance cut 40 — the publish act, local

**Status:** discharged 2026-09-24 on the certified volume; results: ../plans/2026-09-24-conformance-cut-40-results.md
**Design:** `../superpowers/specs/2026-09-23-publish-act-local-design.md`, approved 2026-09-23 at `8cd59d3` after one user review; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-23-publish-act-local.md`.
**Numbered after** cut 39 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 40 or above at freeze.

## 1. What this cut is

Cut 39 built the two points where a publish writes its source root: the
step-0 intent door (`_open_publication`) and the step-8 binding door
(`_bind_publication`), both in `publication_doors.py` with no public route.
This cut reads the act that runs between and around them, for a **local
destination**, a directory the publisher controls: a function a caller
holding the publication permit invokes to publish a view, resume an attempt
that crashed at any local step, and hand a second world a published corpus
it admits only through a door that requires the marker.

A reading of the tree on 2026-09-23 found six things the act needs and the
kernel lacked: a retry cannot re-resolve the selection once a contributing
corpus moves (`corpus-drifted`); no closure rule exists; no door writes a
selected record into staging unchanged; no durable create-only write exists
outside a root; the layer design's local export root is the destination
itself, so a second publication would collide with the first; and no arrival
door requires a marker. The slice supplies each: the selection is
snapshotted at step 0 into `selection.v1`, written create-only before
`request.v1`, and every later step reads only the snapshot; a closure rule
with the composite amendment; the staging doors `_stage_record` and
`_stage_marker`; `durable.py`'s create-only write; `<destination>/<corpus_id>`
beside its `.head-artifact.v1` sibling; and `admit_publication`. The act
authorizes against one permit, `RequiredCapabilities.publishes()`, writes one
terminal report per attempt carrying its lifecycle entries in step order,
and resumes by reinvoking each lifecycle operation and trusting its
predicate.

Remote destinations are split out to cut 41 (spec §2 decision 1): the
transport seam and step 7, the remote reveal and its orphans (cut 39's
Ruling 12 included), the recovery table's remote rows, and the recipient's
`divergent-publication`. `publish` refuses a remote destination with
`ValidationRefused("remote destinations arrive in cut 41")`.

Y5–Y10 open and close. The cut is **off the path**: the success criterion
publishes nothing.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/durable.py` (new), `errors.py`, `report.py`,
  `stored.py`, `boundary.py`, `publication_doors.py`, `permit.py`,
  `publish_request.py` (new), `corpus.py`, `publish.py` (new) and
  `publication_arrival.py` (new);
- the test modules `python/tests/test_publish_engine_order.py`,
  `test_durable.py`, `test_report.py`, `test_publication_doors.py`,
  `test_permit.py`, `test_publish_request.py`, `test_corpus_write.py`,
  `test_permit_boundary.py`, `test_permit_entry_points.py`,
  `test_publish.py` and `test_publication_arrival.py`;
- `python/tests/acceptance/test_publish_act_acceptance.py`,
  `python/tests/n2_arms_cut40.py`,
  `python/tests/acceptance/n2_arms_cut40.py`,
  `python/tests/acceptance/test_n2_cut40.py`,
  `python/tools/cut40_acceptance.py`,
  `python/tests/test_recent_cut_acceptance.py`;
- this cut, the Y table's owner (`2026-09-22-publication-design.md`), the
  ledger, roadmap, guide, README and `python/tests/test_designs_corpus.py`.

Frozen declarations and cut bodies through cut 39 remain byte-exact.

## 3. Selection

Fifteen declaration units are selected and single-homed here, against six
rows. The quoted row text is byte-exact from
`2026-09-22-publication-design.md` (Y5–Y10) at freeze.

```markdown
| **Y5** | every step-0 refusal — `view-revised`, `selection-incomplete`, `empty-selection`, `closure-incomplete` (a composite's missing member included), `pins-disagree`, `coordination-unpinned`, `destination-unusable`, `operations-root-unusable`, and `evaluate_query`'s own — writes nothing: no intent, no file under the operations root |
| **Y6** | a retry never selects differently: population reads only the snapshot the request's digest names, written create-only before the request; a corpus that drifts after step 0 does not strand the retry; a request or snapshot that disagrees with its intent is `request-corrupt`, reported, terminal |
| **Y7** | staging resumes only from a true prefix; a hole, an extra, a byte mismatch or an unequal marker is `staging-corrupt`, reported, terminal; population is complete iff the marker is byte-equal to the factory's |
| **Y8** | the local reveal is `restore_root`'s grant on `<destination>/<corpus_id>` against the create-only sibling; a colliding sibling or a non-`validated` verdict is reported and binds nothing; a second publication to the same destination lands beside the first |
| **Y9** | a crash after any local step resumes exactly to one binding and one report; done iff this attempt's binding exists and the intent is `closed`; `indeterminate` and binding-without-report fail closed with nothing written; the terminal report carries the lifecycle entries in step order, and the next publish's step-0 fold reads every such report, successful or refused |
| **Y10** | a published corpus is admitted in a second world only through `admit_publication`, which refuses before any write a root with no marker, two markers, a malformed or inconsistent marker, a binding, or records other than the marker's selection |
```

The unit table is spec §14.2's as amended by the spec's 2026-09-23 planning
note (§18), the assertion column verbatim:

| unit | row | assertion |
|---|---|---|
| Y5-a | Y5 | each pre-intent refusal leaves the chain's tip and the operations root byte-unchanged |
| Y5-b | Y5 | a view revised between evaluation and lock refuses `view-revised`; nothing is appended |
| Y6-a | Y6 | a record added to a contributing corpus after the intent is appended and before the snapshot is written, so the world drifts and re-evaluation refuses `corpus-drifted`; a crash before step 1; `resume_publish` publishes the step-0 selection byte for byte |
| Y6-b | Y6 | the snapshot rewritten with other bytes → `request-corrupt` report, closed, no binding |
| Y7-a | Y7 | a crash after *k* staged records → resume writes *k + 1* … once each (counting `_stage_record` calls on the resume) |
| Y7-b | Y7 | an extra record raw-written into staging → `staging-corrupt` naming it, report alone, staging retained |
| Y8-a | Y8 | a published root is read-only-serviceable at `<destination>/<corpus_id>` with the sibling beside it; a second publish of the same view lands beside it, and its marker supersedes the first's |
| Y8-b | Y8 | a pre-existing sibling with other bytes → `export-collision`, no binding |
| Y9-a | Y9 | for each step boundary 1–6 and 8, crash then resume → `Published`, exactly one binding revision and one report, the report's entries in step order |
| Y9-b | Y9 | a binding revision raw-written beside an unfinished intent → `PublishUnresolved("binding-without-report")`, nothing written |
| Y9-c | Y9 | `pending_publishes` lists a crashed attempt and omits a done one and a requestless intent; the requestless intent resumes to `PublishUnresolved("no-request")` |
| Y9-d | Y9 | done then a crash inside step 9 → resume discards staging and answers `Published` |
| Y9-e | Y9 | a successful publish followed by a second publish of the same view to the same destination: the second's intent carries the first's marker in `marker_tips` and binds; separately, a `staging-corrupt` refusal followed by a fresh publish: the fresh intent's `marker_tips` omits the refused attempt, and it binds |
| Y10-a | Y10 | a second world admits the published root through `admit_publication`, and its epoch sees the selection; a plain replica with no marker is refused `marker-absent` |
| Y10-b | Y10 | a root built through the staging doors with one record beyond its marker's selection, exported, replicated and restored against its own artifact, so its chain verifies → `admit_publication` refuses `selection-mismatch`, and the recipient's registry is unchanged |

Review Focus tests the plan adds beside the units — two attempts never share
directories, a foreign root at the export path binds nothing, a resume under
another actor or another staging profile writes nothing, and Y9-a's lost
sibling rewritten byte-identically — live in the same module and are not
declaration units.

## 4. Accounting

Task 0's engine probes (§5) all hold, so no arm is unrun: **15 arms, 15
declaration units**, six rows; Y5–Y10 open and close; recent-cut row
`(15, 15, 6)`; Task 8 passes 34; 193 of 226 → 199 of 226.

Task 8's 34 are Y5-a's nine parametrized refusal cases, Y9-a's eight step
boundaries, Y9-a's lost-sibling test, thirteen other unit functions, and the
three Review Focus and finding tests (`test_two_attempts_do_not_share_directories`,
`test_a_foreign_root_at_the_export_path_binds_nothing_durably`,
`test_resume_refuses_another_actor_and_another_profile_writing_nothing`).

## 5. N2 and acceptance obligations

| arm | module | sabotage | check |
|---|---|---|---|
| Y5-a | `publish_request.py` | the closure reads relation targets only | Y5-a |
| Y5-b | `publication_doors.py` | `_open_publication` ignores `expected_view` | Y5-b |
| Y6-a | `publish.py` | the act re-evaluates the selection after the intent instead of keeping the step-0 evaluation | Y6-a |
| Y6-b | `publish.py` | the retry skips the snapshot's identity check against the request and the intent | Y6-b |
| Y7-a | `publish.py` | the classifier restarts population from record 1 | Y7-a |
| Y7-b | `publish.py` | the classifier ignores records outside the snapshot | Y7-b |
| Y8-a | `publish.py` | the export root is the destination directory itself | Y8-a |
| Y8-b | `publish.py` | the sibling write overwrites instead of creating | Y8-b |
| Y9-a | `publish.py` | step 8's report omits the lifecycle entries | Y9-a |
| Y9-b | `publish.py` | the classifier treats binding-present-unfinished as done | Y9-b |
| Y9-c | `publish.py` | `pending_publishes` drops the `unfinished` filter | Y9-c |
| Y9-d | `publish.py` | the done branch of `resume_publish` skips step 9 | Y9-d |
| Y9-e | `publication_doors.py` | `_reports_at` keeps cut 39's exactly-one-binding-entry rule | Y9-e |
| Y10-a | `publication_arrival.py` | `admit_publication` drops the marker count, so a root with no marker is not refused | Y10-a |
| Y10-b | `publication_arrival.py` | the selection check tests membership one way only | Y10-b |

That makes **15 arms over 15 units**, one each. Both directions are
required: the check passes on the real tree and fails under sabotage.

Task 0's probes (`python/tests/test_publish_engine_order.py`, on the
certified volume) pin, from beliefs' side, the engine facts the act's
resumption relies on (spec §2 decision 8, §9):

- `INIT_RETRY = "holds"`: `init_corpus_root` and `init_world_root`,
  reinvoked over an initialized staging corpus and world, change nothing and
  raise nothing, and the world still opens;
- `ADMIT_RETRY = "holds"`: the same fresh adoption, reinvoked, returns a
  record naming the same corpus;
- `EXPORT_STABLE = "holds"`: `export_head_artifact` is a pure function of
  the chain, byte-equal across calls;
- `REPLICATE_RETRY = "holds"`: a completed replication retried exactly
  returns the same operation id and leaves the replica
  read-only-unserviceable;
- `REPLICATE_AFTER_RESTORE = "holds"`: a replication retried exactly after
  its copy was restored returns the same operation id and leaves the copy
  read-only-serviceable, which the resume after a crash past step 6
  reinvokes;
- `READ_SERVICEABLE = "holds"`: restore against the exported artifact
  answers `validated`, and a `ReadView` opens the serviceable copy;
- `FOREIGN_REPLICA = atoms.coordinator.lifecycle.RootOperationMismatch`:
  another corpus's replica at the export path refuses this replication with
  that exception, so a foreign occupant is never adopted as this attempt's
  copy (spec §16 item 6). Task 8's foreign-occupant test asserts exactly
  this type.

The runner uses `PREFIX_RUNNERS = ("cut39_acceptance.py",)` and carries
`PHASE_MODULES = ("test_publish_act_acceptance.py", "test_n2_cut40.py")`.

## 6. Second reader

Check that every arm publishes under exactly `publishes()`
(`scoped_authority(RequiredCapabilities.publishes(), ACTOR)`), with only the
fixtures built under setup authority; that Y6-a's drift happens after the
intent is appended and before the snapshot is written; that Y7-a counts
`_stage_record` calls on the resume; that Y9-a's crashes discard in-memory
state (a fresh `open_corpus`) before `resume_publish`; and that Y10-b's root
verifies its chain, so the refusal is the marker check's.

## 7. Limitations

1. **Crashes are exceptions at step boundaries.** They are not kills at
   engine stages or power cuts, which belong to `persistence-cut`
   (`beliefs-3ea822`). The arms prove the classifier and the reinvocation
   order, not the engine's own crash atomicity, which its cuts own.
2. **The durable create-only write rests on the host's POSIX `fsync` and
   `link`.** It is not an `atoms` root, and the kernel does not check the
   operations root's volume against the allowlist.
3. **Step 9 removes staging with `rmtree`,** outside any `atoms` operation.
   The roots are private and throwaway.
4. **`publish` has no public route.** `science` reaches it by its own design.
5. **Remote destinations are refused until cut 41.**
6. **A foreign root occupying `<destination>/<corpus_id>` leaves the attempt
   unfinished.** `replicate_root` refuses it, and the kernel does not
   classify engine refusals outside `root.py`, so no terminal report is
   written. The attempt stays listed by `pending_publishes` until an operator
   clears the path.
