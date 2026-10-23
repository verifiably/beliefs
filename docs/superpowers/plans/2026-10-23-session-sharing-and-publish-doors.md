# Session Sharing and Publish Doors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the kernel's writer session a `sharing` requirement, a `sharing` ledger line with two act doors and one attestation door, a publish door that ledgers the write-root records, and a publication preview that publish itself calls.

**Architecture:** Every addition sits inside the existing session package and the permit module, over the ledger's existing append-then-fsync path. The two sharing doors wrap `root.restore_root` and `publication_arrival.admit_publication` under the scoped authority, binding the caller's evidence to the root before the act. The publish door composes `beliefs.publish` with the session's ledgered operation port, which learns the guarded commit, and step 0's intent is appended under the session's hold. The preview is step 0 up to the intent, factored out and called by publish.

**Tech Stack:** Python 3.11+, pytest (`just test-one`, `just test-fast`), ruff, pyright; the certified volume for real-root tests (`certified_work`).

**Spec:** `docs/superpowers/specs/2026-10-22-session-sharing-and-publish-doors-design.md` (approved for planning 2026-10-23 at `f2d75d6`).

**Revision:** 2026-10-23, after plan review round 1 (unrestored admission, the durable composition proof, the `J7b` and `Y6-a` probe migrations, the stale-writer fixtures, Review Focus 4, the guarded-publication assertions, the fixture's `resolver`).

## Global Constraints

- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
  This slice discharges no cut (spec decision 13), so no row is added; the
  obligation is carried so a later amendment that adds a cut sees it.
- The session package imports the acts through `beliefs.root` (`open_world`, `restore_root`, `moment_seam`) and `beliefs.publication_arrival`; never `atoms`.
- Exact types everywhere, as the package does: `type(x) is T`, sealed final frozen dataclasses for line values, `TypeError` for a wrong type and `ValueError` for a wrong value.
- The frozen cut-19 sabotage strings in `session/ledger.py` and `session/writer.py` (`tests/acceptance/n2_arms_cut19.py`) must not move: they pin `_act`'s body, `close_invocation`'s body, `scoped()`'s `permit_covers` line and the ledger's `os.fsync` / `self._failed = True` / `except OSError` lines. Add beside them; `just test-one tests/test_arm_staleness.py` after every task that touches those files.
- Refusal reasons, fields and messages of `beliefs.publish` do not change; only `profile-disagrees` moves behind the attribution refusals (spec decision 10).
- Tests use the test front door: `just test-one <args>` while working, `just test-fast` before each commit. Real-root tests take `certified_work`; a `CapabilityUnavailable` there is a failure on the certified host, never a skip.
- Science's field names are fixed by its `SharingLine` protocol (`commons-1a`, `python/src/science/sharing.py`): `invocation, corpus, marker, artifact, world, view, source, location, verdict, transition, at`.
- Conventional commits, no attribution trailers. Each task ends with `just test-fast` green and one commit.

## Review Focus

1. An observer set whose first carrier is another corpus's artifact and whose second is the publication's: the artifact binding must search every carrier, not the first. Test in Task 5.
2. `admit_publication` over a metadata-less copy that was never restored: detached verification admits it (`test_arrival_modes.py:175`), so the door ledgers `admitted` and the restore-first order is science's; a copy whose chain the verification refutes propagates `ArrivalRefused` with no line and no admission. Both tested in Task 5.
3. A guard that raises inside the ledgered guarded commit: the exception propagates, nothing committed, nothing ledgered, the invocation stays current. Test in Task 4.
4. A publish through the door whose `operations_root` lies inside a mounted root: `operations-root-unusable` from the act, after the entry checks and the world open, with no intent appended and no act line. (The world is opened before the act checks the root, so no promise about recovery holds here; the entry refusals of Task 7 — stale, closed, insufficient permit — are the ones that open no world.) Test in Task 7.
5. A view that is a subordinate address (a `question` under a project) through the preview, the publish door and the sharing line: the marker's view round-trips into the evidence and the line without refusal. Tests in Tasks 2, 6 and 7.

---

## File structure

- Modify `python/src/beliefs/permit.py` — `_SHARING_PERMIT`, `RequiredCapabilities.sharing()`, `KERNEL_REQUIREMENTS`.
- Modify `python/src/beliefs/session/ledger.py` — `TRANSITIONS`, `SharingEvidence`, `SharingLine`, `InvocationRecord.sharing`, `LedgerReader.sharing()`, the `sharing` line's validation and protocol rules.
- Modify `python/src/beliefs/session/writer.py` — `WriterSession.world_config`, `_record_sharing`, `invocation_sharing`; `ScopedWriter.record_sharing`, `restore_root`, `admit_publication`, `publish`, `resume_publish`.
- Modify `python/src/beliefs/session/routes.py` — `LedgeredPort.execute_fulfilling_guarded`.
- Modify `python/src/beliefs/session/__init__.py` — exports; `open_attended_session` passes `world_config`.
- Modify `python/src/beliefs/runrecord.py` — `GuardedCommit`, the protocol's return type.
- Modify `python/src/beliefs/root.py` — `DurableOperationPort.execute_fulfilling_guarded` returns `GuardedCommit`.
- Modify `python/src/beliefs/publication_doors.py`, `python/src/beliefs/boundary.py` — read `.reason`.
- Modify `python/src/beliefs/publish.py` — `require_publishes`, `hold`, `PublicationPreview`, `publication_preview`.
- Modify `python/src/beliefs/errors.py` — `SharingEvidenceDisagrees`.
- Create `python/tests/session_doors_fixture.py` — the published-source and recipient fixtures shared by Tasks 5–7.
- Create `python/tests/test_session_sharing_doors.py`, `python/tests/test_session_publish_door.py`.
- Modify tests: `test_permit.py`, `test_session_ledger.py`, `test_session_writer.py`, `test_session_routes.py`, `test_publish.py`, the ten port doubles, `test_permit_boundary.py`.
- Modify docs: writer-session design, session-routes design, publish-act-local design, the adoption ledger.

---

### Task 1: `RequiredCapabilities.sharing()`

**Files:**
- Modify: `python/src/beliefs/permit.py:140-150` (`_PUBLICATION_PERMIT`, `KERNEL_REQUIREMENTS`), `:239-242` (`publishes`)
- Test: `python/tests/test_permit.py:244-250`

**Interfaces:**
- Produces: `RequiredCapabilities.sharing() -> RequiredCapabilities` whose `.permit == WritePermit(frozenset(), frozenset({"lifecycle", "registry"}))`; `KERNEL_REQUIREMENTS == frozenset({_PUBLICATION_PERMIT, _SHARING_PERMIT})`.

- [ ] **Step 1: Write the failing tests** in `test_permit.py`

```python
def test_sharing_constructs_exactly_the_second_kernel_requirement():
    required = RequiredCapabilities.sharing()
    assert required.permit == WritePermit(frozenset(), frozenset({"lifecycle", "registry"}))
    assert KERNEL_REQUIREMENTS == frozenset({RequiredCapabilities.publishes().permit, required.permit})
    authority = scoped_authority(required, "sharer")
    authority.require("lifecycle"); authority.require("registry")
    with pytest.raises(PermitExceeded): authority.require("corpus-write")

@pytest.mark.parametrize("build", [
    lambda: RequiredCapabilities(WritePermit(frozenset(), frozenset({"lifecycle", "registry"}))),
    lambda: RequiredCapabilities(WritePermit(frozenset(), frozenset({"lifecycle"}))),
    lambda: RequiredCapabilities(WritePermit(frozenset({"task"}), frozenset({"lifecycle", "registry", "corpus-write"}))),
], ids=["exact", "lifecycle-alone", "widened"])
def test_every_ordinary_route_naming_lifecycle_or_registry_still_refuses(build):
    with pytest.raises(ValueError, match="a requirement names only command-reachable families"): build()
```

Change `test_publishes_constructs_exactly_the_kernel_requirement` so its `KERNEL_REQUIREMENTS` assertion names both permits.

- [ ] **Step 2: Run to verify failure**: `just test-one tests/test_permit.py -k "sharing or kernel_requirement"` — FAIL: `sharing` undefined.
- [ ] **Step 3: Implement** `_SHARING_PERMIT = WritePermit(frozenset(), frozenset({"lifecycle", "registry"}))`, add it to `KERNEL_REQUIREMENTS`, and `sharing()` decorated with `_mints_the_kernel_requirement` beside `publishes()`. Update the `KERNEL_REQUIREMENTS` docstring: two closed exceptions, decision 7 and this design's decision 1.
- [ ] **Step 4: Run** `just test-one tests/test_permit.py tests/test_permit_boundary.py` — PASS.
- [ ] **Step 5: `just test-fast`; commit** `feat(permit): the sharing kernel requirement over lifecycle and registry`.

---

### Task 2: The `sharing` ledger line

**Files:**
- Modify: `python/src/beliefs/session/ledger.py:44` (`LINE_KINDS`), `:136-160` (line values, `InvocationRecord`), `:195-247` (`_validated_line`), `:249-334` (`LedgerReader`), `:336-404` (`_parse`); `python/src/beliefs/session/__init__.py` (exports)
- Test: `python/tests/test_session_ledger.py`

**Interfaces:**
- Produces: `TRANSITIONS = ("bound", "fetched", "admitted", "mounted", "retired")`; `SharingEvidence(corpus, marker, artifact, world, view, source, location)` (sealed, final, frozen; `__post_init__` validates forms: `corpus`/`world`/`marker` 32 lowercase hex via `require_hex`, `artifact` 64 hex, `view` parses as `CoordinationAddress` with `revision` set, `source` an exact `str` (may be empty), `location` a non-empty `str`); `SharingLine(invocation, corpus, marker, artifact, world, view, source, location, verdict, transition, at)` (sealed, final, frozen); `require_sharing_view(value, what) -> CoordinationAddress`; `InvocationRecord.sharing: tuple[SharingLine, ...]`; `LedgerReader.sharing() -> tuple[SharingLine, ...]`; `_validated_line` accepts `sharing`; `_parse` holds it to the current invocation.

- [ ] **Step 1: Write the failing tests** in `test_session_ledger.py`. Add a builder beside `select`:

```python
VIEW = f"coord:{'1'*32}@{'2'*32}"
SUBORDINATE = f"coord:{'1'*32}/{'3'*32}@{'2'*32}"
def sharing(name, **changes):
    line = {"line": "sharing", "invocation": name, "corpus": CORPUS, "marker": "5"*32, "artifact": "6"*64,
            "world": WORLD, "view": VIEW, "source": "provider:https://remote.test/a", "location": "https://remote.test/a",
            "verdict": "validated", "transition": "fetched", "at": AT}
    line.update(changes); return line
```

Tests:

```python
def test_sharing_lines_round_trip_in_ledger_order_per_invocation_and_overall(tmp_path):
    # open A; sharing A bound; sharing A fetched (view=SUBORDINATE); sharing A admitted; close A; open B; sharing B mounted
    assert [l.transition for l in reader.invocation("A").sharing] == ["bound", "fetched", "admitted"]
    assert reader.invocation("A").sharing[1].view == SUBORDINATE
    assert [l.transition for l in reader.sharing()] == ["bound", "fetched", "admitted", "mounted"]
    assert reader.invocation("B").sharing[0] == SharingLine("B", CORPUS, "5"*32, "6"*64, WORLD, VIEW, "provider:https://remote.test/a", "https://remote.test/a", "validated", "mounted", AT)

@pytest.mark.parametrize(("bad", "message"), [
    (sharing("A", extra=1), "carries exactly"), ({k: v for k, v in sharing("A").items() if k != "verdict"}, "carries exactly"),
    (sharing("A", corpus="5"*31), "corpus id"), (sharing("A", artifact="6"*63), "artifact"), (sharing("A", marker="x"*32), "marker"),
    (sharing("A", world="7"*33), "world id"), (sharing("A", view=f"coord:{'1'*32}"), "pinned"), (sharing("A", view="not-an-address"), "view"),
    (sharing("A", location=""), "location"), (sharing("A", verdict=""), "verdict"), (sharing("A", transition="inspected"), "transition"),
    (sharing("A", source=3), "source"), (sharing("A", at=""), "at"),
])
def test_a_malformed_sharing_line_is_refused_naming_its_number(tmp_path, bad, message): ...  # LedgerMalformed, "line 3"

@pytest.mark.parametrize(("raw", "message"), [
    ([open_line(), sharing("A")], "never opened"),
    ([open_line(), invocation_open("A"), invocation_close("A"), sharing("A")], "not the current invocation"),
    ([open_line(), invocation_open("A"), invocation_open("B"), sharing("A")], "not the current invocation"),
    ([open_line(), invocation_open("A"), invocation_close("A"), {"line": "session-close", "at": AT}, sharing("A")], "no line follows session-close"),
])
def test_a_sharing_line_the_writer_cannot_produce_is_refused(tmp_path, raw, message): ...

def test_a_pre_amendment_session_open_still_parses_with_sharing_lines(tmp_path): ...   # open_line() without project + sharing
def test_sharing_evidence_validates_each_field(): ...   # SharingEvidence(...) raises ValueError per field; TypeError for a non-str source; a SUBORDINATE view constructs
def test_line_kinds_gains_sharing(): assert LINE_KINDS[-1] == "sharing"
```

- [ ] **Step 2: Run**: `just test-one tests/test_session_ledger.py -k sharing` — FAIL (unknown line kind).
- [ ] **Step 3: Implement** in `ledger.py`: `TRANSITIONS`; `require_sharing_view` (parse via `CoordinationAddress.parse`; `revision is None` → `ValueError(f"{what} must be a view address pinned to a revision")`); `SharingEvidence` and `SharingLine`; the `sharing` entry in the expected-keys map and its field checks in `_validated_line` (reuse `require_hex`, `_require_str`; `transition not in TRANSITIONS` → `ValueError`); in `_parse`, a `sharing` branch mirroring `select`'s currency check without the once-per-invocation rule; in `LedgerReader.__init__`, collect `sharing` lines per invocation and in order; `InvocationRecord.sharing` as the last field; `LedgerReader.sharing()`. Export `SharingEvidence`, `SharingLine`, `TRANSITIONS` from `beliefs.session`.
- [ ] **Step 4: Run** `just test-one tests/test_session_ledger.py tests/test_session_reconcile.py tests/test_arm_staleness.py` — PASS.
- [ ] **Step 5: `just test-fast`; commit** `feat(session): the sharing ledger line and its reader`.

---

### Task 3: The session records sharing lines; `record_sharing`; `world_config`

**Files:**
- Modify: `python/src/beliefs/session/writer.py:107-112` (`_Invocation`), `:142-200` (`__init__`), `:273-316` (`invocation_*`), `:362-380` (`ScopedWriter`); `python/src/beliefs/session/__init__.py:177-192` (`open_attended_session` passes `world_config=world_config`)
- Test: `python/tests/test_session_writer.py`

**Interfaces:**
- Consumes: Task 1's `sharing()`; Task 2's `SharingEvidence`, `SharingLine`, `TRANSITIONS`, `utc_now`.
- Produces: `WriterSession.__init__(..., world_config: WorldConfig | None = None)` (when given, `type(world_config) is WorldConfig` else `TypeError`; `world_config.world_id != world_id` → `ValueError`), stored as `self.world_config`; `WriterSession._record_sharing(invocation: str, evidence: SharingEvidence, *, transition: str, verdict: str) -> SharingLine` (under `self._lock`: `_require_live`, `_require_current(invocation)`, `transition in TRANSITIONS` else `ValueError`, `verdict` non-empty `str` else `ValueError`, append `{"line": "sharing", ...,"at": utc_now()}`, then `self._index[invocation].sharing.append(line)`); `WriterSession.invocation_sharing(invocation_id) -> tuple[SharingLine, ...]`; `ScopedWriter.record_sharing(evidence, *, transition, verdict) -> SharingLine` (`self._authority.require("lifecycle")`, `.require("registry")`, `transition not in ("bound", "mounted")` → `ValueError("record_sharing admits bound and mounted; fetched and admitted come from their doors, retired from World.retire's")`, then `_record_sharing`); `_Invocation.sharing: list[SharingLine]`.

- [ ] **Step 1: Write the failing tests** in `test_session_writer.py` (use `make_session`; add `world_config` handling to `make_session` as a keyword that passes through):

```python
SHARING = RequiredCapabilities.sharing()
EVIDENCE = SharingEvidence(CORPUS, "5"*32, "6"*64, WORLD, f"coord:{'1'*32}@{'2'*32}", "provider:https://r/a", "https://r/a")

def test_record_sharing_appends_and_the_index_learns_it_before_return(tmp_path):
    session, _ = make_session(tmp_path); session.claim_invocation("A", "bind", DIGEST)
    line = session.scoped(SHARING, "A").record_sharing(EVIDENCE, transition="bound", verdict="validated")
    assert session.invocation_sharing("A") == (line,) and line.transition == "bound" and line.invocation == "A"
    session.close_invocation("A", {"done": []}); session.close()
    assert open_ledger_reader(session.operations_root, SESSION).invocation("A").sharing == (line,)

@pytest.mark.parametrize("transition", ["fetched", "admitted", "retired", "inspected"])
def test_record_sharing_refuses_act_backed_and_unknown_transitions(tmp_path, transition): ...  # ValueError, invocation_sharing("A") == ()

def test_record_sharing_requires_the_sharing_families(tmp_path):
    # scoped(RequiredCapabilities.coordination(), "A") → PermitExceeded naming "lifecycle"; nothing appended
def test_record_sharing_under_the_publication_permit_is_admitted(tmp_path): ...  # publishes() holds both families: subset semantics
def test_record_sharing_is_held_to_the_current_invocation(tmp_path): ...  # retained writer after close → SessionProtocolError; closed session → SessionClosed
@pytest.mark.parametrize("fault", ["write", "flush", "fsync"])
def test_a_failed_sharing_append_leaves_the_index_unchanged_and_ends_the_session(tmp_path, monkeypatch, fault):
    # mirror test_a_failed_select_append_...: SessionLedgerFailed; session._index["A"].sharing == []; every later method raises SessionLedgerFailed; file bytes unchanged after the fault
def test_world_config_must_agree_with_world_id(tmp_path): ...  # mismatching id → ValueError; a non-WorldConfig → TypeError
def test_an_attended_session_holds_its_world_config(tmp_path, monkeypatch, base_contract): ...  # via _stub_durable_seams; session.world_config == config
```

Update `test_the_scoped_writer_exposes_the_seventeen_methods_...` to add `record_sharing` (rename the test as the count grows; Tasks 5 and 7 add theirs).

- [ ] **Step 2: Run**: `just test-one tests/test_session_writer.py -k "sharing or world_config"` — FAIL.
- [ ] **Step 3: Implement** per the Interfaces block. Keep `_act`, `close_invocation` and `scoped` bodies untouched (pinned).
- [ ] **Step 4: Run** `just test-one tests/test_session_writer.py tests/test_session_ledger.py tests/test_arm_staleness.py` — PASS.
- [ ] **Step 5: `just test-fast`; commit** `feat(session): record_sharing, invocation_sharing and the session's world configuration`.

---

### Task 4: `GuardedCommit` and the ledgered guarded commit

**Files:**
- Modify: `python/src/beliefs/runrecord.py:95-131` (`OperationPort`), `python/src/beliefs/root.py:1086-1093`, `python/src/beliefs/session/routes.py:77-85`, `python/src/beliefs/publication_doors.py:420-424`, `python/src/beliefs/boundary.py:1132-1135`
- Modify test doubles: `python/tests/test_corpus_write.py:106,164,188`, `test_import_bundle.py:65`, `test_operation_writes.py:88`, `test_relocation_recovery.py:258`, `test_operation_port.py:76`, `fixtures_cut3.py:508`, `test_permit_entry_points.py:365`, `acceptance/test_publication_records_acceptance.py:642`, `acceptance/test_act_report_remainder_acceptance.py:121`, `acceptance/test_url_retrieval_acceptance.py:677`
- Modify: `python/tests/test_permit_boundary.py:56-58` (route exemptions gain `session/routes.py:LedgeredPort.execute_fulfilling_guarded`)
- Test: `python/tests/test_session_routes.py:117-125` (replace), new tests; `python/tests/test_operation_port.py`

**Interfaces:**
- Produces: `runrecord.GuardedCommit(entry: str, reason: str | None)` (sealed, final, frozen); `OperationPort.execute_fulfilling_guarded(plan, fulfills, *, guard, fallback) -> GuardedCommit`; `DurableOperationPort.execute_fulfilling_guarded` returns `GuardedCommit(_registration_for(...), reason)`; `LedgeredPort.execute_fulfilling_guarded` under `session._lock`: `_require_current`, `records = plan_records(plan)`, wrapped fallback `lambda reason: remember(plan_records(fb := fallback(reason)), fb)`, `commit = inner.execute_fulfilling_guarded(...)`, `_record_committed(invocation, intent=fulfills, entry=commit.entry, records=<primary or remembered>)`, return `commit`.

- [ ] **Step 1: Write the failing tests** in `test_session_routes.py` (replace `test_execute_and_the_guarded_form_are_refused_before_the_inner_port` by an `execute`-only refusal test):

```python
def test_the_guarded_form_ledgers_the_primary_plan_when_the_guard_passes(tmp_path):
    commit = port.execute_fulfilling_guarded(_plan(node), fulfills, guard=lambda _v: None, fallback=lambda _r: ())
    assert commit.reason is None and (act.intent, act.entry, act.record_ids) == (fulfills, commit.entry, ((node.uid, node.id),))
def test_the_guarded_form_ledgers_the_fallback_plan_when_the_guard_refuses(tmp_path):
    # guard returns "stale"; fallback returns _plan(other); the act line carries other's (uid, id) and commit.reason == "stale"
def test_a_non_create_primary_plan_is_refused_before_the_inner_port(tmp_path): ...  # DeleteOp → SessionProtocolError("creates only"); inner.calls == []
def test_a_non_create_fallback_plan_is_refused_before_it_commits(tmp_path):
    # guard returns "r"; fallback returns [DeleteOp(...)]; SessionProtocolError; inner.calls has no execute_fulfilling; no act line; invocation still current
def test_a_raising_guard_commits_and_ledgers_nothing(tmp_path): ...  # guard raises RuntimeError; propagates; no act; session.current_invocation == "A"
def test_a_production_run_through_the_session_port_commits_and_ledgers(tmp_path):
    # run_production(tmp_path, port=port) over fixtures_cut3; the ledger's acts match the port's fulfilling commits; reconcile reports nothing (as the assessment-run test does)
def test_execute_is_refused_before_the_inner_port(tmp_path): ...
```

In `test_operation_port.py`, assert `durable_port(...).execute_fulfilling_guarded(...)` returns a `GuardedCommit` whose `entry` equals the chain's registration digest for `fulfills` on both branches (`certified_work`).

The composition proof the spec's §6 and decision 13 require — `LedgeredPort` **over the durable port**, on real roots — goes in `test_session_routes.py` too, each test taking `certified_work` and a helper `durable_session(work) -> tuple[WriterSession, ScopedWriter, OperationPort]` that runs `init_corpus_root`, `open_corpus(...).adopt_manifest(profile=pins_for(BASE))`, `init_world_root(WorldConfig(work/"world", "e"*32, (root,)))`, `open_attended_session(config, work/"ops", write_root=root, profile=BASE, mounts={root: BASE})`, claims `"A"`, scopes `RUNS`, and returns `writer.operation_port()`:

```python
def test_the_ledgered_guarded_commit_over_the_durable_port_ledgers_the_primary_plan(certified_work):
    commit = port.execute_fulfilling_guarded(_plan(node), fulfills, guard=lambda _v: None, fallback=lambda _r: ())
    registered = [e for e in log_seam().inspect_detached(root).entries if type(e) is RegisteredEntryView and e.fulfills == fulfills]
    assert [e.digest for e in registered] == [commit.entry] and commit.reason is None
    (act,) = session.invocation_acts("A"); assert (act.entry, act.intent, act.record_ids) == (commit.entry, fulfills, ((node.uid, node.id),))
def test_the_ledgered_guarded_commit_over_the_durable_port_ledgers_the_fallback_plan(certified_work):
    # guard returns "stale"; fallback returns _plan(other); the one registration fulfilling `fulfills` is commit.entry; the act carries other's pair; the file for `other` exists and `node`'s does not
def test_an_invalid_fallback_over_the_durable_port_commits_registers_and_ledgers_nothing(certified_work):
    # fallback returns [DeleteOp(...)]; SessionProtocolError; no RegisteredEntryView fulfills `fulfills`; no file for either record; invocation_acts("A") == (); the invocation stays current
```

Two existing assertions migrate: `test_guarded_publication.py:26-37` read the bare value from `OperationRecorder` and now read `.reason` (`commit.reason is None`, `commit.reason == "acquisition-boundary"`).

Cut 11's live probe `J7b` (`tests/acceptance/test_n2_cut11.py:39-47`, in its `_LIVE_SABOTAGES`) anchors on the three `boundary.py:1132-1134` lines this task changes. Re-target its `before` to the formatted text after the change (the call now ends `).reason`), keep its `after` (`port.execute(plan)` then `reason = None`), and leave the frozen declaration `n2_arms_cut11.py` untouched. Verify both halves: `just test-one tests/test_arm_staleness.py` (the `before` matches exactly once), and the arm's own behaviour by running `audit(arm, workspace)` from `test_n2.py` for that one arm (from `python/`, with `tests/` and `tests/acceptance/` on `sys.path`, under `host-budget run --`), expecting the finding `test_every_arm_fails_under_its_own_sabotage` asserts for a live arm.

- [ ] **Step 2: Run**: `just test-one tests/test_session_routes.py tests/test_operation_port.py -k guarded` — FAIL.
- [ ] **Step 3: Implement**: `GuardedCommit` and the protocol in `runrecord.py`; `root.py` returns it; `routes.py` per the Interfaces block (drop the `SessionProtocolError("... guarded ...")`); `publication_doors.py` `reason = operation_port.execute_fulfilling_guarded(...).reason`; `boundary.py:1132` likewise; every double returns `GuardedCommit(self.execute_fulfilling(...)/synthetic digest, reason)`; `test_permit_boundary.py` route exemptions gain the ledgered guarded form; `test_guarded_publication.py`'s two assertions and cut 11's `J7b` live matcher as Step 1 says.
- [ ] **Step 4: Run** `just test-one tests/test_session_routes.py tests/test_operation_port.py tests/test_guarded_publication.py tests/test_publication_doors.py tests/test_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_corpus_write.py tests/test_import_bundle.py tests/test_relocation_recovery.py tests/test_arm_staleness.py` — PASS; the one-arm `J7b` audit as Step 1 says; `just check` (pyright sees the protocol change).
- [ ] **Step 5: `just test-fast`; commit** `feat(session): the ledgered port commits the guarded form and returns GuardedCommit`.

---

### Task 5: The sharing act doors with evidence binding

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `PortMismatch`, `:1570`), `python/src/beliefs/session/writer.py` (`ScopedWriter`)
- Create: `python/tests/session_doors_fixture.py`, `python/tests/test_session_sharing_doors.py`
- Test: `python/tests/test_session_writer.py` (method set)

**Interfaces:**
- Consumes: Tasks 2–3; `beliefs.root.restore_root`, `open_world`, `read_lifecycle_state`, `LifecycleState`; `beliefs.publication_arrival.admit_publication`, `require_publication_layout`; `beliefs.world.anchors.CorpusSubject`, `decode_head_artifact`; `beliefs.world.verify.ObserverSet`, `ArtifactCarrier`; `beliefs.corpus.ReadView`; `beliefs.world.load_manifest`; `beliefs.publication.MARKER_KIND`; `stored.COORDINATION_FACET`.
- Produces: `errors.SharingEvidenceDisagrees(WriteRefused)` with `field`, `claimed`, `found` attributes and message `f"sharing evidence {field} is {claimed!r}; the root holds {found!r}"`; `ScopedWriter.restore_root(copy: Path, subject: CorpusSubject, observers: ObserverSet, *, evidence: SharingEvidence) -> SharingLine`; `ScopedWriter.admit_publication(root: Path, observers: ObserverSet, *, evidence: SharingEvidence) -> SharingLine`; a module-private `_bind_sharing_evidence(root: Path, evidence: SharingEvidence, observers: ObserverSet, *, subject: CorpusSubject | None) -> None` in `writer.py` that checks, in order: `subject.corpus_id == evidence.corpus` (field `corpus`, when a subject is given), `load_manifest(root).corpus_id == evidence.corpus` (`corpus`), one carrier with `sha256(carrier.data).hexdigest() == evidence.artifact` and `decode_head_artifact(carrier.data).subject == CorpusSubject(evidence.corpus)` (`artifact`; `found` is the comma-joined identities of the carriers whose subject matched, or `"none"`), then `records = tuple(ReadView.opened_at(root).iter_stored())`, `require_publication_layout(records)`, the marker's `uid == evidence.marker` (`marker`), `published_from["world_id"] == evidence.world` (`world`), `CoordinationAddress.parse(published_from["view"]) == CoordinationAddress.parse(evidence.view)` (`view`).
- Fixture module `session_doors_fixture.py`: `published_source(work: Path) -> SimpleNamespace` — mirrors the cut-40 `source` fixture inside `work` (alpha corpus of `topic_nodes()` records under `BASE`; a written root under `coordination_profile(None, version=2)` holding a `project` whose query is `KINDS`; `WorldConfig(world_root, "e"*32, (alpha, written))`; both admitted `Fresh()`; epoch built with `hold_shipped`; `ops`, `dest`) returning `config, alpha, written, profile (V2), mounts {alpha: BASE, written: V2}, resolver (CoordinationResolver({alpha: BASE, written: V2}))`, `view, ops, dest, destination`; `publish_locally(s) -> Published` running `beliefs.publish.publish` with `open_corpus(written, authority=scoped_authority(RequiredCapabilities.publishes(), ACTOR), ...)` as the cut-40 `run` does; `metadata_less_copy(s, published, into: Path) -> tuple[Path, bytes]` — `shutil.copytree(dest / corpus_id, into)` and the sibling `dest / f"{corpus_id}.head-artifact.v1"` bytes; `recipient_session(work, *, required) -> tuple[WriterSession, ScopedWriter]` — one fresh corpus under `BASE` as write root, `WorldConfig(work/"rworld", "f"*32, (root,))` initialised and admitted, `open_attended_session(config, ops, write_root=root, profile=BASE, mounts={root: BASE})`, invocation `"A"` claimed, `scoped(required, "A")`; `evidence_for(published, sibling: bytes, s) -> SharingEvidence` reading the marker from the export (`corpus`, `marker`, `world == "e"*32`, `view == published_from.view`, `artifact == sha256(sibling)`, `source "provider:https://remote.test/a"`, `location "https://remote.test/a"`).

- [ ] **Step 1: Write the fixture module and the failing tests** in `test_session_sharing_doors.py` (every test takes `certified_work`):

```python
def test_restore_root_grants_read_serviceability_and_ledgers_fetched_validated(certified_work):
    line = writer.restore_root(copy, CorpusSubject(cid), observers, evidence=evidence)
    assert read_lifecycle_state(copy) is LifecycleState.READ_ONLY_SERVICEABLE
    assert (line.transition, line.verdict, line.corpus) == ("fetched", "validated", cid) and session.invocation_sharing("A") == (line,)
def test_restore_root_of_a_disagreeing_copy_ledgers_the_refusing_verdict_and_grants_nothing(certified_work):
    # sibling bytes of another publication (publish twice to two destinations) → evidence.artifact from the wrong sibling disagrees → first fix: build evidence from the right sibling but corrupt one record's bytes in the copy → verdict != "validated", state not serviceable, line present
def test_admit_publication_admits_a_replica_under_the_session_actor_and_ledgers_admitted(certified_work):
    # restore first, then admit; registry().admissions has cid with ReplicaOf(cid) and actor == session.actor; line.transition == "admitted"; line.verdict == "validated"
def test_admit_publication_of_an_unrestored_metadata_less_copy_admits_through_detached_verification(certified_work):
    # no restore_root first; the act verifies detached (test_arrival_modes.py:175) and admits; line "admitted"; the copy's lifecycle state is still METADATA_LESS   # Review Focus 2
def test_admit_publication_of_a_refuted_chain_propagates_the_arrival_refusal_and_appends_nothing(certified_work):
    # after a validated restore, rewrite one selected record's body in the copy to another canonical text (the layout still holds); ArrivalRefused propagates from admit_publication; registry unchanged; invocation_sharing("A") == ()   # Review Focus 2
def test_a_copy_without_its_marker_refuses_the_layout_before_either_act(certified_work):
    # delete the marker file in the copy → PublicationArrivalRefused("marker-absent") from restore_root AND from admit_publication; state unchanged; no line
@pytest.mark.parametrize("field", ["corpus", "artifact", "marker", "world", "view"])
def test_mismatched_evidence_refuses_naming_the_field_before_the_act(certified_work, field):
    # replace(evidence, **{field: <another well-formed value>}); SharingEvidenceDisagrees with .field == field, for both doors; copy unserviceable; registry unchanged; invocation_sharing("A") == ()
def test_the_artifact_binding_searches_every_carrier(certified_work):
    # ObserverSet((other_publication_carrier, right_carrier)) → restore_root succeeds   # Review Focus 1
def test_the_doors_require_their_family_first(certified_work): ...  # coordination()-scoped writer: PermitExceeded naming lifecycle / registry; nothing read (copy untouched), no line
def test_stale_and_closed_writers_refuse_before_reading_the_copy(certified_work): ...  # SessionProtocolError after close_invocation; SessionClosed after session.close()
def test_a_store_subject_is_a_type_error(certified_work): ...
def test_a_session_without_a_world_configuration_refuses_admit_publication(tmp_path): ...  # make_session: SessionProtocolError
```

- [ ] **Step 2: Run**: `just test-one tests/test_session_sharing_doors.py` — FAIL (no door).
- [ ] **Step 3: Implement** `SharingEvidenceDisagrees`; `_bind_sharing_evidence`; the two doors in this order: `with self._session._lock:` → `self._session._require_current(self._invocation)` (which runs `_require_live`) → `self._authority.require("lifecycle" | "registry")` → `type(subject) is CorpusSubject` else `TypeError` (restore only) → `_bind_sharing_evidence` → the act (`restore_root(copy, subject, observers, authority=self._authority)`; or `open_world(self._session.world_config, authority=self._authority)` then `admit_publication(world, root, observers)`, a `None` world configuration raising `SessionProtocolError("this session was opened with no world configuration; the admit and publish doors have no world")`) → `self._session._record_sharing(self._invocation, evidence, transition="fetched" | "admitted", verdict=report.outcome)`. Add both to the facade's public-method test.
- [ ] **Step 4: Run** `just test-one tests/test_session_sharing_doors.py tests/test_session_writer.py tests/test_errors_session.py tests/test_capability_boundary.py tests/test_permit_boundary.py` — PASS.
- [ ] **Step 5: `just test-fast`; commit** `feat(session): restore_root and admit_publication doors binding their sharing evidence`.

---

### Task 6: `require_publishes`, `hold`, and `publication_preview`

**Files:**
- Modify: `python/src/beliefs/publish.py:213-218` (`_require_publishes`), `:290-383` (`publish`), `:837-895` (`resume_publish`)
- Test: `python/tests/test_publish.py`, `python/tests/test_publication_attribution.py` (unchanged, must stay green), new tests in `python/tests/test_session_publish_door.py` (preview section; uses Task 5's fixture)

**Interfaces:**
- Produces: `publish.require_publishes(authority: Authority) -> None` (the four `require` calls of today's `_require_publishes`, which becomes `require_publishes(writer.authority)`); `PublicationPreview(view, epoch, world_id, selected, contributing, pins, attributions, records)` (frozen dataclass; field types as spec §4.7); `publication_preview(world: World, resolver: CoordinationResolver, view: CoordinationAddress, *, own_pins: CorpusPins) -> PublicationPreview` — the body is today's `publish` lines `329-355` with `load_manifest(writer.root).profile` replaced by `own_pins`, returning the frozen facts; `publish(..., hold: Callable[[], AbstractContextManager[object]] | None = None)` whose step 0 is: `require_publishes(writer.authority)`, `_require_transport`, `require_usable`, the `publish-unfinished` block, `preview = publication_preview(world, resolver, view, own_pins=load_manifest(writer.root).profile)`, `if pins_of(staging_profile) != preview.pins: raise PublicationRefused("profile-disagrees")`, `records = preview.records` on its own line, `with (nullcontext() if hold is None else hold()): opened = _open_publication(..., expected_view=preview.view)`, `token = opened.intent.event_token`, snapshot `Snapshot(token, records, preview.attributions)`, request with `epoch=preview.epoch`, `world_id=preview.world_id`, `pins=preview.pins`. The local `records` name is deliberate: cut 40's live probe `Y6-a` sabotages the texts the snapshot freezes by reselecting them after the intent, and its `after` assigns that name. `__all__` gains `PublicationPreview`, `publication_preview`, `require_publishes`.

- [ ] **Step 1: Write the failing tests**. In `test_session_publish_door.py` (preview section, `certified_work`, Task 5's `published_source`):

```python
def test_the_preview_returns_what_publish_freezes(certified_work):
    s = published_source(certified_work); world = open_world_read(s.config)
    preview = publication_preview(world, s.resolver, s.view, own_pins=load_manifest(s.written).profile)
    published = publish_locally(s)
    snapshot = decode_snapshot((s.ops / "publish" / published.event_token / "selection.v1").read_bytes())
    request = decode_request((s.ops / "publish" / published.event_token / "request.v1").read_bytes())
    assert (snapshot.records, snapshot.attributions) == (preview.records, preview.attributions)
    assert (request.epoch, request.world_id, request.pins, request.view) == (preview.epoch, preview.world_id, preview.pins, preview.view)
def test_the_preview_of_a_subordinate_view_pins_it(certified_work): ...   # a question under the project; preview.view.local is not None and revision set   # Review Focus 5
def test_the_preview_refuses_as_publish_does(certified_work):  # an unresolvable view → "view-unresolved"; a project whose query selects nothing → "empty-selection"
def test_the_preview_needs_no_authority(certified_work): ...  # open_world_read suffices; nothing under ops / "publish"
```

In `test_publish.py`, add `test_profile_disagrees_follows_the_preview(monkeypatch)` with the attribution module's `wrapper_fixture` pattern: a `staging_profile` whose pins differ and an attribution refusal both present → the attribution refusal wins. And `test_require_publishes_is_the_acts_check()`: `require_publishes(scoped_authority(RequiredCapabilities.coordination(), "a"))` raises `PermitExceeded` naming `publish`.

- [ ] **Step 2: Run**: `just test-one tests/test_session_publish_door.py tests/test_publish.py -k "preview or require_publishes or follows"` — FAIL.
- [ ] **Step 3: Implement** per the Interfaces block. Keep every private step function name (`_initialize`, `_populate`, ... are monkeypatched by the acceptance tests).

Cut 40's live probe `Y6-a` (`tests/acceptance/test_n2_cut40.py:68-80`, in its `_LIVE_SABOTAGES`) anchors on `"    )\n    token = opened.intent.event_token\n"` and its `after` recomputes a local `records` from `query`, which step 0 no longer holds. Re-target it, leaving `n2_arms_cut40.py` frozen: `before` becomes the formatted `token = opened.intent.event_token` line (with the line that precedes it after the hold block), and `after` inserts, before that line, `records = tuple((address, node_to_markdown(open_world_view(world, current_epoch(world)).get(address))) for address in preview.selected)` — the same proof, the texts reselected after the intent from a fresh view, now from the preview's addresses. Verify as Task 4 does for `J7b`: `just test-one tests/test_arm_staleness.py`, and the one-arm `audit` under `host-budget run --`, expecting the live-arm finding.
- [ ] **Step 4: Run** `just test-one tests/test_publish.py tests/test_publication_attribution.py tests/test_publish_request.py tests/test_publish_intent.py tests/test_session_publish_door.py tests/test_permit_boundary.py tests/test_arm_staleness.py` — PASS; the one-arm `Y6-a` audit as Step 3 says. Then, because the acceptance modules are outside `addopts`, run `just test-one tests/acceptance/test_publish_act_acceptance.py tests/acceptance/test_publish_remote_acceptance.py tests/acceptance/test_publication_attribution_acceptance.py` once — PASS (they pin the act's refusals and crash points).
- [ ] **Step 5: `just test-fast`; commit** `feat(publish): publication_preview as step 0's one computation; hold at the intent; require_publishes`.

---

### Task 7: The publish door

**Files:**
- Modify: `python/src/beliefs/session/writer.py` (`ScopedWriter.publish`, `resume_publish`), `python/src/beliefs/session/__init__.py` (no new export needed)
- Test: `python/tests/test_session_publish_door.py` (door section), `python/tests/test_session_writer.py` (method set)

**Interfaces:**
- Consumes: Task 3's `world_config`, Task 4's ledgered guarded commit, Task 6's `require_publishes`, `hold`; `beliefs.root.open_world`, `moment_seam`; `beliefs.session.ledger.utc_now`; `beliefs.publish.publish`, `resume_publish`; `tests/transport_fake.DirectoryTransport`.
- Produces: `ScopedWriter.publish(*, view: CoordinationAddress, destination: Destination, operations_root: Path, staging_profile: ProfileSpec, transport: Transport | None = None) -> PublishOutcome`; `ScopedWriter.resume_publish(*, event_token: str, operations_root: Path, staging_profile: ProfileSpec, transport: Transport | None = None) -> PublishOutcome`. Both: `with self._session._lock:` → `_require_current` → `require_publishes(self._authority)` → `resolver = self._session._coordination_resolver` (`None` → `CoordinationUnavailable("this session has no coordination resolver; the publish door resolves the view through it")`) → `config = self._session.world_config` (`None` → `SessionProtocolError`, Task 5's message) → `world = open_world(config, authority=self._authority)`; then outside the lock, `publish(self._writer, resolver, world, view=..., destination=..., operations_root=..., staging_profile=..., clock=utc_now, seam=moment_seam(), port=self.operation_port(), transport=transport, hold=self._closing_hold)` / `resume_publish(self._writer, resolver, event_token=..., ..., port=self.operation_port(), transport=transport)`.

- [ ] **Step 1: Write the failing tests** (door section of `test_session_publish_door.py`; `certified_work`; a helper `publishing_session(s) -> tuple[WriterSession, ScopedWriter]` opening `open_attended_session(s.config, s.ops / "sessions-root", write_root=s.written, profile=s.profile, mounts=s.mounts)`, claiming `"A"` and scoping `RequiredCapabilities.publishes()`):

```python
def test_a_local_publish_through_the_door_ledgers_the_binding_and_report(certified_work):
    outcome = writer.publish(view=s.view, destination=s.destination, operations_root=s.ops, staging_profile=s.profile)
    assert type(outcome) is Published
    (act,) = session.invocation_acts("A")
    reading = attempt_reading(open_corpus(s.written, ...), outcome.event_token, moment_seam())
    assert act.intent == reading.opened.digest and {uid for uid, _ in act.record_ids} == {outcome.binding, <report uid read from the write root>}
    assert act.entry == <the registration digest fulfilling act.intent on the chain>
    session.close_invocation("A", {"done": [list(p) for p in act.record_ids]}); session.close()
    assert reconcile_sessions(s.config, s.ops / "sessions-root") == ()
def test_a_refused_publish_ledgers_the_refusal_report(certified_work): ...  # pre-create the sibling file → export-collision; one act with the report's (uid, id); outcome PublishRefused
def test_resume_in_a_second_invocation_ledgers_under_it(certified_work):
    # crash(monkeypatch, "_replicate", before=True) as the acceptance module does; publish → Crash; close A refused; claim B, scoped B; writer_b.resume_publish(event_token=token, ...) → Published; invocation_acts("B") holds the binding act
@pytest.mark.parametrize("left", ["marked", "bound-undiscarded"])
def test_a_stale_writer_refuses_before_any_effect_with_a_transport_spy(certified_work, monkeypatch, left):
    # remote destination with DirectoryTransport; through invocation A: `marked` = crash(monkeypatch, "_push", before=True) so the attempt is unfinished with its transport mark and nothing pushed; `bound-undiscarded` = crash(monkeypatch, "_discard", before=True) so the attempt is bound with staging and world still on disk; then monkeypatch.undo(), close_invocation("A", refusal), and the retained writer's .publish(...) and .resume_publish(event_token=token, ...) → SessionProtocolError; transport.pushes unchanged (0 for `marked`); every file under ops/publish byte-for-byte unchanged, staging and world still present for `bound-undiscarded`
@pytest.mark.parametrize("left", ["marked", "bound-undiscarded"])
def test_a_closed_session_writer_refuses_session_closed(certified_work, monkeypatch, left): ...  # the same two fixtures after session.close(); SessionClosed; same unchanged-state assertions
def test_a_coordination_scoped_writer_refuses_the_permit_before_the_world_is_opened(certified_work, monkeypatch):
    # monkeypatch beliefs.session.writer.open_world to raise AssertionError("opened"); PermitExceeded naming "publish"; no act
def test_a_session_without_a_resolver_refuses_coordination_unavailable(certified_work): ...  # mounts=None
def test_an_operations_root_inside_a_mount_is_unusable_from_the_act(certified_work): ...  # operations_root=s.alpha / "ops" → PublicationRefused("operations-root-unusable"); no act, no intent   # Review Focus 4
def test_a_subordinate_view_publishes_through_the_door(certified_work): ...   # Review Focus 5
```

Add `publish` and `resume_publish` to the facade's public-method test (now 22 names).

- [ ] **Step 2: Run**: `just test-one tests/test_session_publish_door.py -k "door or ledgers or refuses"` — FAIL.
- [ ] **Step 3: Implement** per the Interfaces block.
- [ ] **Step 4: Run** `just test-one tests/test_session_publish_door.py tests/test_session_writer.py tests/test_session_reconcile.py tests/test_capability_boundary.py tests/test_arm_staleness.py` — PASS; `just check`.
- [ ] **Step 5: `just test-fast`; commit** `feat(session): publish and resume_publish doors over the ledgered port`.

---

### Task 8: Documents

**Files:**
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (append `## Sharing and publish doors amendment — 2026-10-23` after line 1301), `docs/designs/2026-09-09-session-routes-design.md` (append a dated note after line 478), `docs/superpowers/specs/2026-09-23-publish-act-local-design.md` (append a dated note after line 875), `docs/designs/2026-08-03-redesign-adoption-ledger.md:152` (a bullet after the Session selection entry)

- [ ] **Step 1: Write the writer-session amendment**: the `sharing` row (spec §3), `SharingEvidence`/`SharingLine`, §4.3–4.4's signatures, decisions 3–7 and 12 in the style of the Selection amendment (`:1237-1267`).
- [ ] **Step 2: Write the session-routes note**: `LedgeredPort.execute_fulfilling_guarded` commits and ledgers both branches, records read before any commit, `GuardedCommit`; the production run through a session port is now reachable.
- [ ] **Step 3: Write the publish-act-local note**: `hold` at step 0's intent; `publication_preview` as step 0's one computation; `profile-disagrees` after the attribution refusals; `require_publishes`.
- [ ] **Step 4: Add the adoption-ledger bullet**: "**Session sharing and publish doors** — `RequiredCapabilities.sharing()`; the `sharing` ledger line with `restore_root`, `admit_publication` and `record_sharing` doors binding their evidence; `publish`/`resume_publish` doors over the ledgered port, which commits the guarded form; `publication_preview` ([design](../superpowers/specs/2026-10-22-session-sharing-and-publish-doors-design.md)). Built; no conformance cut."
- [ ] **Step 5: Run** `just check` (ops-docs check reads the docs) — PASS. Commit `docs(designs): amend the session, routes and publish designs for the sharing and publish doors`.

---

## Self-review

- **Spec coverage.** §2.1 → Task 1; §2.2–2.3, §3, §4.2 → Task 2; §2.3, §2.6, §4.3, `record_sharing` of §4.4 → Task 3; §2.8, §4.6 → Task 4; §2.4–2.5, §4.5, the act doors of §4.4 → Task 5; §2.9–2.10, §4.7 → Task 6; §2.7, §2.12 (unchanged behaviour, tested by the stale-writer and resume tests), the publish doors of §4.4 → Task 7; §2.11 (reconcile unchanged: Tasks 2 and 7 run `test_session_reconcile.py` and `reconcile_sessions`) → no code; §2.13's conditions → Tasks 3 (append faults), 4 (both branches over the durable port on certified roots), 7 (real-root publish); the two live probes the changes move (`J7b`, `Y6-a`) → Tasks 4 and 6, declarations frozen; §7 → Task 8; §8 → filed (`beliefs-b427db`, `beliefs-a989fb`).
- **Step scan.** Each test step names tests and assertions; each code step names the signature, file and the spec's values. The two algorithmic bodies spelled out are `_bind_sharing_evidence`'s check order and the doors' lock-then-check order, which the signatures do not determine.
- **Type consistency.** `SharingEvidence` has seven fields everywhere; `record_sharing(evidence, *, transition, verdict)`; `GuardedCommit(entry, reason)`; `publication_preview(..., own_pins=)`; `restore_root(copy, subject, observers, *, evidence)`; `admit_publication(root, observers, *, evidence)`.
- **Review Focus.** All five lines have tests in Tasks 2, 4, 5, 6 and 7.
- **Proportion.** The plan is shorter than the spec plus the code it describes; code appears as signatures, test names and assertions.
