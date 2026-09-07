# Conformance cut 19 — discharge results

**Date:** 2026-09-05
**Subject:** the writer session (`../designs/2026-09-05-writer-session-design.md`
§3, §4, §5, §6 and §7, as its §13 implementation amendment rules them),
measured against the frozen cut at `5cc2153`
(`../designs/2026-09-05-conformance-cut-19.md`).

This cut froze as **cut 19** and is discharged as cut 19: no lower-numbered cut
was undischarged at the freeze, so concurrency rule 5 imposed no serialization
and no renumbering applies. The frozen §§2–7 are byte-identical to `5cc2153`;
`tests/acceptance/test_n2_cut19.py` pins them by digest and asserts §4's
accounting sentences and §5's `("cut18_acceptance.py",)`. The selection, the 11
declaration units and the accounting are the frozen ones.

**The discharge tree** is the code as committed at `8723fac` — the branch's
last code commit, carrying every implementation and test commit of the eleven
tasks. The discharge commit that adds this record does not know its own id.

**The runner** is `tools/cut19_acceptance.py`: `PREFIX_RUNNERS =
("cut18_acceptance.py",)` and `PHASE_MODULES = ("test_session_acceptance.py",
"test_n2_cut19.py")`, with its default durable work root beside the checkout
(`python/../.cut19-acceptance`, on the same volume as the repository).

**The prefix runner's result: the chain stops in phase 1 and this record does
not claim a clean end-to-end run.** `tools/cut18_acceptance.py` fails on two
freeze-**ancestry** pin tests — `test_n2_cut17.py::test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact`
and `test_n2_cut18.py::test_the_freeze_commit_and_sections_two_through_seven_are_pinned`
— because the four commits those modules pin (`a0f2302`, `398491d`, `2071be0`,
`e9e592a`) are no longer ancestors of any branch after a history rewrite. The
failure is a property of the repository's history, not of this branch: it
reproduces identically on `main` (`779fa7a`) and predates the fork point. It is
filed as `beliefs-faf658`, which belongs to the owning cuts' lane, and cuts 17
and 18 are not edited here. Run **scoped**, every N2 arm audit of cuts 17 and
18 passes: 13 passed, 2 failed, the two being exactly those ancestry pins. Both
cut-19 phases were therefore run directly, and §4 says what to re-run once the
pins are repaired.

**The certified tuple** was accepted by the runner's own probe through
`init_corpus_root` under a full authority; no capability refusal or tuple
mismatch banner was emitted.

## 1. What ran

All Python commands ran from `python/`.

### 1.1 The runner, and where it stops

`uv run --frozen python tools/cut19_acceptance.py`

```text
[cut19 phase 1/3] cut18_acceptance.py
[cut18 phase 1/3] cut17_acceptance.py
[cut17 phase 1/19] test_n2_cut6.py
23 passed in 10.95s
... 17 further cut-17 phases, every one green ...
[cut17 phase 19/19] test_n2_cut17.py
.....F..                                                                 [100%]
E           AssertionError: assert 1 == 0
E            +  where 1 = CompletedProcess(args=['git', ..., 'merge-base',
E                '--is-ancestor', 'a0f2302', 'HEAD'], returncode=1).returncode
tests/acceptance/test_n2_cut17.py:111: AssertionError
FAILED tests/acceptance/test_n2_cut17.py::test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact
1 failed, 7 passed in 14.52s
$ echo $?
1
```

The eighteen phases before it are green — the cut-6, -7, -9, -11, -12, -13,
-14, -15 and -16 N2 audits and the intent-boundary, successor-admission,
confinement, coordination, cut-15 lineage, relocation, permit-acceptance,
permit-boundary and permit-entry-point acceptance modules. The stop is the
nineteenth, and it is an ancestry assertion, not an arm. Scoped to the two
modules that carry those assertions:

`uv run --frozen pytest tests/acceptance/test_n2_cut17.py tests/acceptance/test_n2_cut18.py -p no:cacheprovider`

```text
FAILED tests/acceptance/test_n2_cut17.py::test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact
FAILED tests/acceptance/test_n2_cut18.py::test_the_freeze_commit_and_sections_two_through_seven_are_pinned
2 failed, 13 passed in 38.30s
```

Every N2 *arm* audit of cuts 17 and 18 passes; the two failures are the
freeze-ancestry pins and nothing else.

### 1.2 The two cut-19 phases, run directly

`uv run --frozen pytest tests/acceptance/test_session_acceptance.py tests/acceptance/test_n2_cut19.py -p no:cacheprovider`

```text
................................                                         [100%]
32 passed in 51.43s
```

The 32 checks are the 25 of `test_session_acceptance.py` and the 7 of
`test_n2_cut19.py` — the runner's phase-2 and phase-3 modules, unchanged, on
the certified volume beside the checkout under their repository-relative
default work root rather than the runner's temporary one. The audit module
reports the frozen accounting it pins: **43 declared arms over
11 declaration units, 11 guarantee rows read full/closed, 0 partial and 0
re-reads**, every arm's verdict `sound`.

### 1.3 Certified host facts

- backend `linux`, revision `linux-4`, storage profile
  `flush-honoring-disk.v1`;
- kernel `7.2.2-arch1-1`;
- ext4 normalized options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`,
  `ro_compat=0x46b`; and
- certification record
  `atoms/docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json` at
  Atoms commit `0b382a9`.

### 1.4 Repository evidence at the discharge head

- `uv run --frozen pytest -p no:cacheprovider` — **3640 passed in 856.14s (0:14:16)**;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**;
- `uv run --frozen python tools/check_guide.py` — clean; and
- `tasks check` — zero errors and zero warnings.

The staleness probe of the plan's Global Constraints prints the Task 1
baseline (design §13 item 5) byte for byte after every task of this cut,
discharge included: 24 entries, all of them pre-existing invalidated evidence
from cuts 5, 6, 8 and 10, and none from cuts 17 or 18.

## 2. Accounting and disposition

Cut 19 reads eleven guarantee rows: **11 full/closed** (J1–J11), 0 partial, 0
closed-row re-reads. It selects no row of any other table and closes none. The
frozen inventory is **11 declaration units**, one grouped unit per row; the
executable declarations expand them into **43 unique one-mutation sabotage
arms** over **38 distinct checks** — J1×8, J2×10, J3×3, J4×1, J5×3, J6×3,
J7×3, J8×7, J9×2, J10×1, J11×2 — mutating `corpus.py` (18), `session/writer.py`
(11), `session/reconcile.py` (4), `session/__init__.py` (4),
`session/ledger.py` (3), `report.py` (1), `intents/reduce.py` (1) and
`root.py` (1). Every arm audited **sound**: none vacuous, mixed, uncollected or
stale. `CO_CITED` is empty — no check of cuts 3–18 is reclaimed.

- **J1 — closes.** Each of the seven scoped methods over a real attended
  session on a registered root grows the chain by exactly one `corpus-write`
  intent under actor `session:<id>` and one committed registration whose
  `fulfills` is that intent's digest; `qualify_chain` reads `matched` and
  `completion` reads `closed`, `delete` included, whose registration publishes
  no record. Every refusal — permit, family, malformed record, record ceiling,
  a retraction through `add`, an act-report through `add` — appends nothing of
  its own, and the head after the refusal equals the head a settled non-writing
  probe read after `_settle`; on a root left unresolved by a prior failed
  submission the head moves only by that prior work's settlement. The
  **Negative** holds: the same seven through the ordinary `CorpusWriter` append
  no intent.
  *(`acceptance/test_session_acceptance.py::test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration`,
  `::test_j1_refusals_append_nothing_of_their_own`,
  `::test_j1_coordination_writes_commit_as_operations`,
  `::test_j1_a_refusal_on_a_root_left_unresolved_moves_the_head_only_by_settlement`;
  `test_operation_writes.py::test_add_commits_as_preflight_intent_then_fulfilling_execution`,
  `::test_the_ordinary_path_appends_no_intent_and_the_scope_is_never_left_bound`,
  `::test_delete_commits_a_delete_op_and_carries_no_record`,
  `::test_revise_commits_a_replace_op`,
  `::test_retract_and_supersede_commit_through_their_ordinary_bodies`,
  `::test_a_permit_refusal_appends_nothing`,
  `::test_the_twin_refuses_exactly_as_the_ordinary_method_and_appends_nothing`,
  `::test_an_over_ceiling_record_is_plan_refused_before_the_intent`,
  `::test_supersede_of_a_missing_target_refuses_before_the_intent`,
  `::test_a_writer_without_a_port_refuses_every_operation_before_any_refusal`.)*
- **J2 — closes.** Intent precedes effect and the promise is bounded by
  submission. A fault before submission leaves one intent, no registration, no
  record file and one `session-outcome-unknown`; a faulted registration
  readback and a faulted `_reconstruct` each leave the record durable, the
  registration committed, no `act` line, `unresolved` still set and the view
  *not* rebuilt, and the next write on that root settles first and sees the
  record; a faulted ledger append after the commit raises `SessionLedgerFailed`
  with the registration committed and uncovered; a faulted ledger fsync after a
  complete `act` line ends the session. A raced precondition is an
  `ExecutionError` and reconciliation, not the test, says whether a
  registration stands. The fresh-process arm leaves a staged, unsettled
  transaction in one interpreter and asserts the next process's first scoped
  write recovers before its prepare; the library and mixed-handle arms settle
  first through `import_bundle`, a relocation `move`, and a portless durable
  `CorpusWriter`; a failed recovery refuses the next write before any prepare.
  The **Negative** holds: a faulted `append_intent` leaves nothing to
  reconcile, and a preflight `PlanRefused` appends no intent.
  *(`acceptance/test_session_acceptance.py::test_j2_a_failure_before_submission_leaves_an_intent_and_no_record`,
  `::test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed`,
  `::test_j2_a_post_commit_rebuild_failure_on_delete_leaves_the_root_unresolved`,
  `::test_j2_a_post_commit_index_failure_on_add_leaves_the_root_unresolved`,
  `::test_j2_a_ledger_write_failure_after_commit_leaves_the_registration_uncovered`,
  `::test_j2_a_ledger_fsync_failure_after_a_complete_act_line_ends_the_session`,
  `::test_j2_a_raced_precondition_is_an_execution_error`,
  `::test_j2_the_halting_backends_skip_count_names_the_records_publish`,
  `::test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare`,
  `::test_j2_a_fresh_process_settles_before_its_first_prepare`,
  `::test_j2_library_and_mixed_handles_settle_first`,
  `::test_j2_a_failed_recovery_refuses_the_write_before_any_prepare`;
  `test_corpus_write.py::TestTheUnresolvedRoot`;
  `test_operation_writes.py::test_a_post_submission_failure_on_the_twin_is_an_execution_error`.)*
- **J3 — closes.** The scoped writer's effective permit is exactly the
  requirement: an act outside it is `PermitExceeded` raised by the kernel entry
  point under a full-permit session with nothing written, and `scoped` refuses
  an uncovered requirement before any writer exists. `PermitExceeded.capability`
  carries the *requirement's* summary at the act and the *ceiling's* at
  `scoped`. The **Negative** holds: the same acts under a requirement that
  names them are minted.
  *(`acceptance/test_session_acceptance.py::test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session`;
  `test_session_writer.py::test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists`,
  `::test_the_act_time_refusal_comes_from_the_kernel_with_the_requirements_summary`,
  `::test_scoped_type_checks_its_arguments`;
  `test_operation_writes.py::test_the_requirement_is_the_effective_permit_at_the_act`,
  `::test_the_twin_judges_the_permit_before_it_settles`.)*
- **J4 — closes.** Every intent a session write appends decodes to actor
  `session:<id>`; no public signature on `WriterSession`, `ScopedWriter` or
  `OperationWrites` takes an `actor`; a retraction whose facet names another
  actor is `ActorMismatch` with nothing appended, and the same retraction under
  the session actor is minted.
  *(`acceptance/test_session_acceptance.py::test_j4_every_intent_carries_the_session_actor`;
  `test_operation_writes.py::test_every_intent_carries_the_bound_actor_and_no_seam_takes_one`,
  `::test_a_retraction_naming_another_actor_is_actor_mismatch_with_nothing_appended`,
  `::test_the_two_intent_producers_emit_one_encoding`.)*
- **J5 — closes.** After each scoped write the ledger's last `act` line carries
  the registration digest `read_chain` reports for that intent and the exact
  minted identities (`[]` for `delete`); a wrapped `os.fsync` is observed once
  per line and the file has grown before the method returns; a second thread
  observes the root's operation lock held from before the commit until after
  the append. The **Negative** is J8's: a fabricated `entry` is what
  `session-act-unverified` catches.
  *(`acceptance/test_session_acceptance.py::test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock`;
  `test_session_writer.py::test_the_session_lock_spans_the_act_so_no_claim_interleaves_with_a_commit`,
  `::test_delete_ledgers_an_empty_record_list`.)*
- **J6 — closes.** The claim protocol runs the whole §3.3 table — `ClaimFresh`,
  `ClaimDone` (a `done` and a refusal envelope both replayed whole and detached
  from every caller), `ClaimMismatch` on a changed digest and on a changed
  command, `ClaimOpen` — with every returned value one of the four sealed
  classes; an abandoned invocation stays open and never blocks a later fresh
  claim; `close_invocation` of an abandoned id is `SessionProtocolError`; a
  malformed outcome is refused with the invocation still current. The
  **Negative** holds: eight threads claiming one fresh id under a lock see one
  `ClaimFresh` and then seven `ClaimDone`, and an over-ceiling record through
  the scoped writer is `PlanRefused` and closes its invocation with a refusal
  envelope.
  *(`test_session_writer.py::test_the_claim_table`,
  `::test_a_refusal_outcome_replays_whole_and_detached_from_every_caller`,
  `::test_an_abandoned_invocation_stays_open_and_never_blocks_a_fresh_claim`,
  `::test_a_malformed_outcome_is_refused_and_the_invocation_stays_current`,
  `::test_claims_are_validated`,
  `::test_eight_threads_claiming_one_fresh_id_under_a_lock_see_one_fresh`,
  `::test_an_over_ceiling_record_through_the_scoped_writer_is_plan_refused`.)*
- **J7 — closes.** Every ledger line is appended and fsynced before its call
  returns and before the index records it; the encoding is canonical JSON lines
  in `sort_keys` order with no whitespace; a truncated ledger reports
  `torn_tail` with every complete line read, a corrupted interior line is
  `LedgerMalformed` naming its number, and a first line that is not
  `session-open` is `LedgerMalformed`. A faulted `write` after part of a line
  ends the writer with the file's bytes exactly the partial line and every
  later call `SessionLedgerFailed`; a short write without an exception and a
  failed `fsync` after a complete line do the same, and the claim the line
  would have recorded is absent from the index. The **Negative** holds: a valid
  ledger round-trips to the same `InvocationRecord`s the index holds, and a
  handler's `WriteRefused` leaves the session usable.
  *(`test_session_ledger.py::test_lines_are_canonical_json_one_per_line`,
  `::test_each_append_is_fsynced_once_and_lands_before_return`,
  `::test_the_reader_round_trips_every_line`,
  `::test_open_invocations_lists_every_unclosed_one_in_order`,
  `::test_a_torn_tail_is_reported_and_every_complete_line_is_read`,
  `::test_a_malformed_interior_line_is_refused_naming_its_number`,
  `::test_a_first_line_that_is_not_session_open_is_malformed`,
  `::test_a_line_the_writer_protocol_cannot_produce_is_refused_naming_its_number`,
  `::test_an_empty_or_missing_ledger_is_not_malformed_to_the_reader_but_is_evidence`,
  `::test_a_partial_write_ends_the_writer_and_preserves_the_bytes`,
  `::test_a_short_write_without_an_exception_ends_the_writer`,
  `::test_a_failed_fsync_ends_the_writer`,
  `::test_validated_outcome_accepts_the_two_shapes_and_nothing_else`;
  `test_session_writer.py::test_a_ledger_failure_ends_the_session`.)*
- **J8 — closes.** Every intent, chain and ledger state §6 tables — the
  detached `pending`-only registration included — yields exactly one finding
  with the tabled code, severity and ref over stand-in views and evidence, and
  the results are deterministic and ordered by corpus, then chain position,
  then code. Over the real root, `reconcile_sessions` before and after a
  crashed session equals `session.findings` of a session opened over the same
  root, and the corpus root, its metadata sibling and the operations root hash
  equal before and after — with an unsettled registration present, which
  registered inspection would have resolved. The interleaving arm blocks a
  scoped write inside its commit on a second thread and asserts no
  `session-entry-foreign` and that the write is either absent from both reads
  or covered. The **Negative** holds: a fully covered session yields no
  finding, an ordinary library write is never classified, and a session
  directory with no ledger yields `session-ledger-missing` without refusing
  open.
  *(`test_session_reconcile.py` — all seventeen checks;
  `acceptance/test_session_acceptance.py::test_j8_reconciliation_over_the_real_root`,
  `::test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write`,
  `::test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold`.)*
- **J9 — closes.** Open writes `session-open` with the actor, world id and
  permit summary; `close` appends `session-close` once and is idempotent; every
  later call is `SessionClosed`; and a config with zero or two corpus roots, a
  missing root, an existing but unadopted root, a registered root with no
  manifest, or an adopted root whose chain directory is removed refuses at open
  with no `sessions/` entry created. The **Negative** holds: a session left with
  an open invocation at `close` writes `session-close` after it and the reader
  reports it in `open_invocations` and `closed` both.
  *(`acceptance/test_session_acceptance.py::test_j9_lifecycle_and_the_refusing_configurations`;
  `test_session_writer.py::test_close_is_idempotent_and_every_later_call_is_session_closed`.)*
- **J10 — closes.** One node written through a scoped writer and the same node
  through `open_corpus` on a twin root give byte-equal record files, equal
  `corpus_check` findings and equal record inventories; a session `delete` and
  a raw `unlink` of the twin leave equal read views. The **Negative** holds: the
  two *chains* differ — the session root holds the intent and the fulfilling
  registration — and that is the whole of the difference.
  *(`acceptance/test_session_acceptance.py::test_j10_a_session_write_is_indistinguishable_on_ordinary_read`.)*
- **J11 — closes.** A scoped writer acts only while its invocation is current:
  before the claim, after the close, under another current invocation, and
  after abandonment it refuses `SessionProtocolError` with the head unchanged
  and no `act` line; it carries the requirement it was scoped with, not the
  ceiling. The **Negative** holds: two writers scoped for one id under one claim
  both act, and every act ledgers under that id.
  *(`acceptance/test_session_acceptance.py::test_j11_a_writer_is_bound_to_one_invocation_durably`;
  `test_session_writer.py::test_a_scoped_writer_acts_only_under_its_own_current_invocation`,
  `::test_two_writers_scoped_for_one_id_both_act_under_that_id`,
  `::test_the_scoped_writer_exposes_only_the_seven_methods_and_its_invocation`.)*

T3 (completion derived, never stored) is re-read informally by J1's
`completion` assertions and is not counted, exactly as the frozen §4 says. T2
is untouched: a `corpus-write` operation mints no act-report, so it contributes
no act-report arm.

## 3. Corrections and deviations

Every item is dated 2026-09-05 and none changes the frozen selection, the
eleven rows, their checks or the 11 units. §§2–7 of the cut document are
byte-identical to the freeze at `5cc2153`; the only edit to it in this
discharge is its status line.

**The prefix runner cannot complete on this repository's history, and this
record does not claim it did.** The freeze's §5 item 3 names
`cut18_acceptance.py` as this runner's prefix, and the implementation plan
required the aggregate run to exit 0. It stops in phase 1 on two freeze-**ancestry** assertions of cuts 17 and 18:
`test_n2_cut17.py` pins `a0f2302` and `398491d`, `test_n2_cut18.py` pins
`2071be0` and `e9e592a`, and none of the four is an ancestor of any branch
after a history rewrite that predates this lane's fork point. The same two
tests fail on `main` (`779fa7a`). Run scoped, the two modules give **13 passed,
2 failed** — every N2 *arm audit* of cuts 17 and 18 passes, and the two
failures are exactly the ancestry pins. The defect is filed as task
`beliefs-faf658` against the owning cuts' lane; cuts 17 and 18 and their
records are not edited here, and §4 states what to re-run once the pins are
repaired. Cut 19's own two phases were run directly with the runner's own
module list, on the same certified volume.

**Four rulings were added to the design's §13 during implementation.**

- **Item 17 — the scoped authority is minted in `permit.py`.** §5 writes the
  scoped writer's authority as `Authority(required.permit, self.actor)` at the
  session, but E6's static arm admits an `Authority(...)` construction in
  `permit.py` and nowhere else. `permit.py` therefore gains
  `scoped_authority(required, actor)`, which type-checks the requirement and
  returns exactly §5's value; `WriterSession.scoped` calls it, no `session/`
  definition takes an actor, and the static arm is unweakened.
- **Item 18 — the scoped act holds the session lock, then the root lock.**
  Holding the session lock only across the currency check left a race:
  `_act` held the root lock alone while `claim_invocation` and
  `close_invocation` hold the session lock alone, so another thread could move
  the current invocation between the durable commit and the ledger append — a
  committed registration with no `act` line in a session that stays live, which
  §5 sanctions only for a crash or a ledger I/O failure. `_act` now takes the
  session lock first and holds it across the currency check, `perform()` and
  the `act` line, taking the raw root lock inside it; the re-check in
  `_record_act` becomes an invariant (`ScienceError`, never
  `SessionProtocolError`). Session lock, then root lock, everywhere.
- **Item 19 — a `CapabilityUnavailable` lifecycle read defers to the write's
  own refusal.** `_DurableExecutorFactory.recover` catches
  `CapabilityUnavailable` from the lifecycle read and returns without reading
  the chain, exactly as for a successful non-`WRITABLE` read: the refusal is
  the engine's own judgment that the root is not writable, and the write will
  refuse with the identical cause. This was a Task 3 regression, caught by
  `tests/acceptance/test_durable_families.py::test_import_on_an_uncertified_tuple_refuses`
  — whose frozen `(index, applied) == (None, 0)` shape a settling hold would
  otherwise have moved one step earlier — and fixed at `8994575`. Every other
  lifecycle-read exception still maps to `ExecutionError(index=None,
  applied=None)` with the flag left set.
- **Item 4's in-place paragraph — the traced publish sequence.**
  `PUBLISH_CALLS_BEFORE_RECORD` is **6**, established by a `TracingBackend`
  over one `execute_fulfilling` rather than by the plan's estimate. Two facts
  the trace settled: the engine answers a failed publish by rolling the
  transaction back *in band*, and the rollback unlinks the record's staging
  file on its way out — so the staged bytes that survive the halt are the
  **chain's** (`<root>/.#~chain/.#~stage`), not the record's. The count also
  holds only over a kind directory that already exists, so every arm writes a
  record of the same kind before it arms, and the acceptance suite re-derives
  both shapes through `TracingBackend`
  (`::test_j2_the_halting_backends_skip_count_names_the_records_publish`).

**Two rulings on landed behavior the frozen text does not decide.**

- **The ledger reader refuses protocol-impossible line sequences as
  `LedgerMalformed`** (Task 6). §3.2's five typed lines admit sequences the
  writer can never produce — an `act` before any `claim`, a `claim` for an id
  already closed, a line after `session-close`. The reader refuses them by
  number rather than returning them as evidence, on the same fail-closed rule
  as a malformed line; `test_a_line_the_writer_protocol_cannot_produce_is_refused_naming_its_number`
  is the arm. J7's "refuses a malformed line and reports a torn tail" is read
  at that width.
- **`reconcile_sessions` returns `(*extra, *reconcile(...))`** (Task 8), with
  the `sessions/` listing taken under the root lock and `session-act-unverified`
  raised only against a `WellFormedView`. Unadopted-root and unreadable-ledger
  findings lead; `reconcile`'s own order — corpus, then chain position, then
  code — is preserved behind them, so the deterministic-order arm reads the
  landed function and not a re-sorted copy. An `act` line naming a corpus whose
  chain is absent or malformed is *not* classified unverified, because that
  chain is not truth to classify against.

**Three N2 departures from the freeze's §5 item 4 arm list, and one check
split.**

- **The freeze's `J-inv` is not constructible in this harness.** §5 item 4 asks
  for a sabotage of `test_permit_boundary.py`'s inventory row. The N2 harness
  copies only `src/beliefs` into its workspace and mutates there, so no arm can
  mutate a test module, and no prior cut has one either. The guarantee is
  broken from the source side instead.
- **`J1h` renames the seam in `corpus.py`** (`commit_fulfilling` →
  `commit_fulfilment`, call site and `def` in one replacement) so the static
  inventory's 37th row names a definition the tree lacks and an uninventoried
  primitive caller appears; `test_permit_boundary.py::test_the_inventory_is_closed_in_both_directions`
  catches it. It is homed under **J1**, not as a twelfth unit, because
  `DECLARATION_UNITS` is exactly the eleven `J` rows.
- **`J8f` as landed proves a hold exists across the chain and ledger reads, not
  that the ledger read is inside it.** The arm the plan wrote — dedent the
  ledger read out of the `ExitStack` — audits **vacuous**: the test's only
  timing lever is a wait inside the patched `inspect_detached`, so a ledger read
  moved just past the stack still wins the race against the unblocked writer's
  durable commit. The landed arm drops `stack.enter_context(...)` so no root
  lock is held across the reads at all, and both interleaving arms catch it.
  The residue is a gap in
  `test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold`, not in
  `reconcile_sessions`: the code holds the lock across both reads; the check
  cannot yet distinguish a ledger read that escapes it. A stronger arm needs a
  second patch point between the two reads.
- **One check was split in two.**
  `test_j2_a_ledger_failure_after_commit_ends_the_session` does not exist as
  one check: J2's clause is read by
  `test_j2_a_ledger_write_failure_after_commit_leaves_the_registration_uncovered`
  and the fsync half by
  `test_j2_a_ledger_fsync_failure_after_a_complete_act_line_ends_the_session`.
  Both are cited; no clause is lost.

**The staleness baseline is unchanged through discharge.** Cuts 5, 6, 8 and 10
carry twenty-four pre-existing stale arms — invalidated evidence, cited and not
run, recorded verbatim in the design's §13 item 5. Cuts 17 and 18, the two the
prefix runner executes, contribute none. The probe printed that exact line
after every one of the twelve tasks, discharge included.

**Clauses unreachable on the certified volume are discharged portably.** Four
clauses of the frozen rows are read by portable checks rather than durable
ones, because what they assert happens before or beside any durable effect:
J3's `scoped`-time refusal
(`tests/test_session_writer.py::test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists`),
J5's **Negative** and J8's **Negatives**
(`tests/test_session_reconcile.py`), and J7's race arm
(`tests/test_session_writer.py::test_the_session_lock_spans_the_act_so_no_claim_interleaves_with_a_commit`).
The frozen §3 selects each of these rows "with the portable arms beside it", so
this is the selection's own shape and not a narrowing.

**The re-rank and the ledger row.** The roadmap ranks tier 1 by distance to the
mm30 dogfood success criterion (its method design §4.0, amended 2026-09-05),
not by breadth; this discharge re-ranks under that method and changes only what
cut 19 closed. `writer-session` leaves the boundary index, the tier-1 table and
the lane table, and `verification-publication` — already next behind it in the
same `write-path` lane — becomes that lane's open boundary and tier 1's first
on the path. The ledger's `writer-session` row is **removed** rather than
edited: a boundary the table lists is one still open, and a frozen-and-now-
discharged cut belongs in the `Current state` prose and in this record. No
other row moves, in either document.

**The merge is not part of this discharge commit.** The commit that adds this
record lands on `feat/writer-session`; the `--no-ff` merge into `main` and the
post-merge gate run follow separately.

## 4. Reproduction prerequisites, and what this run does not claim

**To reproduce this discharge** you need: this repository at the discharge
commit; `atoms` at `0b382a9` or later, resolved as an editable path dependency,
carrying `docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json`; and a
volume matching the §1.3 tuple beside the checkout — `/tmp` and any scratch
volume fail the durability allowlist, and a `CapabilityUnavailable` block is a
fail-closed result, never a skip. Run `uv run --frozen pytest
tests/acceptance/test_session_acceptance.py tests/acceptance/test_n2_cut19.py
-p no:cacheprovider` from `python/`.

**What to re-run when the freeze pins are repaired.** Once `beliefs-faf658`
re-pins cuts 17's and 18's freeze-ancestry commits to the surviving history,
`uv run --frozen python tools/cut19_acceptance.py` must be run **end to end**
and must exit 0. Until then this record claims the two cut-19 phases and the
scoped prefix result, and nothing more.

**Nothing here closes a row of another table.** The `J` table is new and every
other row stands exactly as cut 18 left it: S5 partial on its cross-corpus
reach, R23 on its producer-snapshot, coverage, cross-corpus-divergence,
explicit-import and rules-store clauses, R19 on cross-corpus recomputation,
R22 on the unresolvable-interpretation-rule refusal, M3 on its coreference arm
and its banked concrete-cycle limitation, C3 on its coverage clauses, T2 on its
other operation-family clauses, and L13 on the preimage resolver.

**T2 gains no arm.** A `corpus-write` operation mints no act-report; its
completion is read from the fulfilling registration alone.

The frozen §7 limitations stand, unchanged by this run: one corpus root, so
multi-corpus targeting is `world-resolution`'s; coordination needs the
launcher's profile; run, holdings and import stay library-only through this
session and `KernelRefusalValue` is unraised until a mirror exists;
deduplication is session-scoped; the ledger's durability is a file fsync,
outside the certified path; two ledgered sessions over one operations root are
not refused; a `delete` renders nothing; reconciliation's snapshot is
in-process coherent, and pending is reported rather than settled; and reads
after a failed submission see unresolved files until the next write. Design
§13 item 15 narrows the "every operation commit rebuilds the view" limitation:
a session `add`, `retract`, `supersede`, `revise` or coordination write updates
the index incrementally, exactly as the library path does; `delete` still
rebuilds.

Two residues are named rather than closed: **`J8f`'s check gap** above, and
**`J1h`'s source-side-only proof** — a deletion of the `WRITE_ENTRY_POINTS`
row from `tests/test_permit_boundary.py` itself is caught by no cut-19 arm,
because the harness cannot sabotage a test module.

## 5. Implementation commits

| commit | subject |
|---|---|
| `6b215eb` | docs(session): bank the writer-session design |
| `5cc2153` | docs(designs): freeze conformance cut 19 for the writer session |
| `7386093` | docs(session): bank the implementation amendment and file the science change requests |
| `7381e28` | feat(report): add the corpus-write operation kind qualified by its registration |
| `cdf2a63` | feat(root): give the operation port a preflight and a registration readback, and the durable factory recovery |
| `cc3e5a3` | feat(corpus): settle an unresolved root before every write body through the existing hold |
| `5951f35` | feat(corpus): commit an operation write as a corpus-write intent and its fulfillment through the routed executor |
| `9cffbcc` | refactor(corpus): give the operation intent one wire encoding both producers append |
| `26c2e45` | feat(session): add the append-then-fsync session ledger and its reader |
| `9c75761` | fix(session): refuse ledger lines the writer protocol cannot produce |
| `1a49a38` | feat(session): add the attended writer session and the invocation-bound scoped writer |
| `dbe9180` | fix(session): hold the session lock across a scoped act so no claim interleaves with its commit |
| `c73c203` | feat(session): reconcile session ledgers against chains |
| `ad7dfd0` | fix(session): keep reconcile's order, list sessions under the lock, and classify no act against a chain that is not truth |
| `f8eb249` | test(session): add the durable acceptance arms for J1, J3, J4, J5, J9, J10 and J11 |
| `8994575` | fix(root): defer to the write's own refusal on an uncertified tuple's lifecycle read |
| `663a2db` | test(session): read the act lines back from the ledger and pin the body's refusal |
| `d6c031d` | test(session): add the durable acceptance arms for J2 and J8 |
| `88763ca` | test(session): fault the ledger write itself and close the one-hold arm's vacuity |
| `8723fac` | test(cut19): add the N2 arms, the freeze-pinning audit and the acceptance runner |
| `af99233` | chore(tasks): file the cut 17/18 freeze-ancestry pin defect found by the cut 19 runner |

The discharge commit carries this record, the ledger's `Current state`, the
roadmap's re-rank, the README, the guide, the two status lines and the four
dated amendment notes; it does not know its own id.

## 6. Remaining boundary

`writer-session` closes with this discharge and leaves the ledger's boundary
table and the roadmap's ranking. Its lane, `write-path`, does not close: the
lane's next boundary is **`verification-publication`**, which becomes tier 1's
first on the path — durable publication of verification records, the
comparison report and scope recoverable from the corpus rather than from an
in-memory `AssessmentVerification`, carrying the optional `derivation` member
cut 18's ruling R2 added for exactly this writer. No new boundary is created,
and no row is re-homed.

Every other boundary stands as cut 18's record left it, and the remainders it
named are untouched by this cut:

- `world-resolution` keeps R19's cross-corpus recomputation, S5's cross-corpus
  reach, M3's coreference arm, and R23's producer-snapshot, coverage,
  cross-corpus-divergence and explicit-import clauses, together with W1, W2,
  W4, W5a, W6, W7, W8, W8b, W10, W15, W13 less its two-projects negative,
  W8a's coreference arms, S1, S1a, D3 and X12's coreference membership. M1 and
  M5 closed at cut 18 and are not reopened here.
- `contract-cut` keeps R22's unresolvable-interpretation-rule resolver arm,
  R23's rules-store clauses, N1–N10, N2's closing doctrine, P1's
  resolver-negative arm and the `instrument-certification` arms of W8a, X12 and
  C10. It is still the join.
- `correction-remainder` keeps C7, C8, C9, C3's coverage clauses and C10's
  audit arm; it is the mutation lane's only open boundary.
- `url-retrieval` keeps H4, G9, R10, T5 and T7's same-root case;
  `act-report-remainder`, which rides with it, keeps T1, T2 and T4 — `delete`
  and `corpus-write` each add no arm to T2.
- `domain-boundary` keeps D1, D2, D4, D5, D6, D8, D9, D10 and G5;
  `parity-fixture-2` rides with it.
- `event-level-l8` keeps L8, and `log-remainder`, which rides with it, keeps
  L1, L4 and L10's relabel.
- `packaging-remainder` keeps X5's relabel and W8a's import-boundary and audit
  arms; `l13-preimage` keeps L13, still a path match and not a byte match;
  `persistence-cut` keeps X2's persistence-cut arm; and `nodes-remainder`,
  which carries no guarantee row, is unmoved.
- Tier 3 is unmoved: `authority-labels` (W9, W14), `weighted-belief` (S6's arm
  h), `extraction-path` (M12) and `cross-root-publication` (T7's cross-root
  case).
