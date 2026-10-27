# Owned replica publication implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Inline execution is recommended because the four tasks share one preparation path and conformance declaration; a fresh reviewer checks the finished branch before integration.

**Goal:** Publish an explicitly declared own, markerless replica without changing
its corpus identity or weakening attribution for adopted publications.

**Architecture:** Add `own_corpora` to existing preparation, publish and scoped
publish calls. Validate the declaration once, check full captured content, and
exclude eligible declared holders from the existing replica-origin calculation.
Persist only the existing frozen result; recovery and wire formats stay unchanged.

**Tech Stack:** Python 3.11+, pytest, existing durable fixtures, N2 and acceptance
runner. No dependency, public type, registry record or TypeScript change.

**Spec:** `docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md`,
revision `deb8d99`, after review of `338c71f` and the user's fix-then-plan instruction.
Read both artifacts. **Status:** accepted at `69577b6`; implementation and
conformance completed. [Results](../../plans/2026-10-27-conformance-cut-47-results.md)
record exact evidence and execution rulings. Final review, task closure and local
integration are recorded on beliefs-7c612b; the final handoff step below stays
unmarked in this frozen review revision until those actions occur.

## Global Constraints

- Reuse `.worktrees/7c612b-replica-publication`, branch
  `design/7c612b-replica-publication`. Setup and the full execution baseline passed; results record the counts. Use physical cwd for tests, but show the user paths
  prefixed with this worktree directory. Do not touch main's existing lockfile edit.
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
- Task 4 owns the proposed `(cut47, 47, (9, 9, 2))` row. Recheck branches and
  worktrees before Task 1 freezes cut 47. If occupied, amend this plan and all
  dependent names before freezing; do not silently reuse a number.
- `own_corpora: frozenset[str] = frozenset()` is keyword-only on all three
  public doors. Exact types; reuse `publication._HEX32.fullmatch` for IDs.
  No coercion, guessed ownership or caller-supplied attribution triples.
- Selected holder admission checks precede declared-own marker checks, which
  precede existing replica checks. Earlier selection, closure and pin errors
  keep their precedence. Malformed declarations fail at preview entry, before
  publication intent or operations-root writes; scoped world recovery can precede it.
- A marker in **any** captured node vetoes a selected holder's declaration,
  even for Fresh/ForkOf, malformed markers, or unmapped coordination records.
  Captured absence is not evidence of authorship; the declaration is a claim.
- No new format, contract release, world-config field, permit or session option.
  Empty defaults and saved v2/v3 attempts preserve behavior. `resume_publish`
  takes no declaration. Preserve all registry provenance and corpus IDs.
- Freeze the cut document before product edits. Preserve prior frozen documents,
  canonical declarations and their tests' assertions; live mutation retargets
  go in the owning guard with a recorded reason and a proved kill.
- `just test-one` is the test front door; `just test-fast` precedes implementation
  commits. Portable and acceptance modules run separately to avoid conftest
  shadowing. Full baseline: `just test`, once at execution Setup, record counts.
  Hooks run checks; explicit acceptance is required because fast excludes it.
- Durable fixtures and the successor runner use the certified volume through
  `checkout.MAIN_CHECKOUT`, not the storage-backed worktree. Report exact
  capability refusal; do not turn it into a skip. No live corpus is a fixture.
- New test subprocesses receive an environment built key by key, with temporary
  HOME, required PATH and explicit variables. Git reads use `GIT_CONFIG_NOSYSTEM=1`
  and a temporary `GIT_CONFIG_GLOBAL`; do not copy the inherited environment.
- Record lifecycle, review and retained-item evidence with tasks. No push or
  live-world mutation is authorized. Reviewed local integration follows the
  personal-profile rule; science integration is separately tracked by sci-9a7ce2.

## Review Focus

1. A marker is captured but absent from the index/selection: Task 2 must still veto ownership.
2. An unknown selected holder is declared own: Task 2 must refuse admission before inspecting markers.
3. A v2 writer declares all local sources but also selects a real publication: Task 2 must name only the remaining replica and preserve pin precedence.
4. A scoped caller is stale or under-permitted and supplies malformed ownership: Task 3 must retain currency/permit rejection before opening the world.
5. A resumed attempt has no source world or ownership configuration: Task 3 must use frozen records/origins for local and remote recovery, including mark-only recovery.

## File map and declaration

All paths in this document are repository-relative; user-facing paths add the worktree prefix.

| Files | Responsibility |
|---|---|
| `docs/designs/2026-10-27-conformance-cut-47.md` (new), publication/formal-model tables, `python/tools/roadmap_status.py`, README, adoption ledger, roadmap | Freeze and later discharge Y5/Y17 amendments (Tasks 1/4) |
| `python/src/beliefs/publish.py` | Validate and consume ownership; forward from publish to preview (Task 2) |
| `python/tests/test_owned_replica_publication.py` (new), `test_publication_attribution.py` | New declared tests and small backward-compatible fixture/signature updates (Task 2) |
| `python/src/beliefs/session/writer.py`, `python/tests/test_session_publish_door.py` | Scoped forwarding and unchanged preflight (Task 3) |
| `python/tests/acceptance/test_owned_replica_publication_acceptance.py` (new) | Real replica arrival, publication and recovery (Task 3) |
| `python/tests/n2_arms_cut47.py`, acceptance shim and `test_n2_cut47.py`, `python/tools/cut47_acceptance.py` (new), `test_recent_cut_acceptance.py` | Mutation proof, historical pins and runner accounting (Task 4) |
| `python/tests/acceptance/test_n2_cut46.py` and, only if needed, `test_n2_cut40.py` | Live retargets preserving earlier assertions (Tasks 2/4) |
| `docs/plans/2026-10-27-conformance-cut-47-results.md` (new) | Actual results, review dispositions and limits (Task 4) |

Nine units, nine arms, two existing guarantee rows reopened; no new guarantee IDs.
The exact check is `test_owned_replica_publication.py::test_<unit>_<suffix>`
with lowercase unit and underscore, except Y17-w, which lives in
`test_session_publish_door.py`. Parameter cases stay within one unit. No prior
check node is reclaimed or co-cited. Additional durable tests do not enlarge counts.

| Unit | Suffix / decisive behavior | Independent mutation responsibility |
|---|---|---|
| Y5-f | `declaration_validation`: exact frozenset/string/hex shape; unused malformed IDs still fail at preview entry | Bypass the ownership validator call |
| Y17-q | `owned_replica`: declared markerless replica returns None/v2 or ()/v3 with its admission unchanged | Keep declared holders in the replica set |
| Y17-r | `explicit_scope`: empty declaration retains refusal; an unselected declaration cannot exempt a selected holder | Treat a nonempty declaration as applying to every holder |
| Y17-s | `captured_marker_veto`: any marker in full capture vetoes every provenance class | Suppress marker-present rejection |
| Y17-t | `refusal_order`: all admissions first, then sorted declared-holder marker errors, then ordinary replicas | Move marker validation ahead of the complete admission pass |
| Y17-u | `mixed_origins`: omit owned records only, forward remaining source triples unchanged | Suppress carried entries whenever any own holder contributes |
| Y17-v | `preview_matches_freeze`: public preview and publish snapshot agree on texts, pins and None/tuple origins | Drop the declaration at publish-to-preview forwarding |
| Y17-w | `scoped_ownership`: scoped publish forwards the exact frozenset, with existing preflight intact | Drop declaration forwarding in ScopedWriter.publish |
| Y17-x | `frozen_owned_marker`: local/remote reconstruction preserves None/empty own-only formats with source reads trapped | Invent a carried entry for an owned selected record during reconstruction |

Each arm must fail at its named assertion, not a collection, syntax or unrelated
guard error. Pre-intent refusal also has a separate uncounted regression test;
its declaration forwarding is mutation-tested by Y17-v. Task 4 fixes exact
before/after anchors against the finished implementation without weakening these obligations.

### Task 1: Freeze the owned-replica amendment

**Files:** new cut document; `docs/designs/2026-09-22-publication-design.md`,
`docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md`,
`python/tools/roadmap_status.py`, `README.md`,
`docs/designs/2026-08-03-redesign-adoption-ledger.md`,
`docs/plans/2026-08-29-implementation-roadmap.md`.

**Interfaces:** Consumes spec `deb8d99` and this reviewed plan. Produces frozen
cut-47 obligations, nine unit names and reopened Y5/Y17; no product behavior yet.

- [x] At execution Setup, refresh the task claim and trial arm, inspect worktree
  status and installed hooks, and run the full `just test` baseline before code
  changes. Record the command, passed/failed/skipped counts and capability limits.
  Setup already succeeded; rerun it only if dependency state needs hydration.
- [x] Inspect `git for-each-ref`, `git worktree list`, and tracked/untracked cut
  documents in those worktrees. The planning inspection found cut 46 highest.
  Confirm 47 is unused before creating it.
- [x] Write the cut using cut 46's seven-section form. Copy this declaration,
  the precise refusal order, v2/v3 results, and spec §1's answer to decision 8.
  Freeze `PREFIX_RUNNERS = ("cut46_acceptance.py",)` and
  `PHASE_MODULES = ("test_owned_replica_publication_acceptance.py", "test_n2_cut47.py")`.
  State **9 arms, 9 declaration units, two exercised rows**: Y5 and Y17,
  both amendments reclosed, no newly closed rows. The document is frozen now;
  executable sabotage declarations are pinned when Task 4 creates them.
- [x] Amend the two current-facing Y17 copies and add a dated Y5 amendment;
  distinguish declared own markerless replicas from carried replicas. Preserve
  the cut-46 quotation and decision's historical text. Set
  `REOPENED["Y5"] = ("conformance-cut-47 §3", 47)` and likewise Y17.
  Run `cd python && uv run --frozen python tools/roadmap_status.py` to derive
  totals: with unchanged prior accounting, 224/253 closed at freeze and
  226/253 after discharge. Do not claim discharge yet. Update current ledger,
  roadmap and README claims together, keeping the science integration pending.
- [x] Run `just test-one tests/test_designs_corpus.py tests/test_check_guide.py`,
  then `just test-fast` and `tasks check`. Commit
  `docs(cut): freeze owned-replica publication amendment`; record commit and
  document SHA-256. Freeze work is documentation/accounting, not new test logic.

### Task 2: Implement explicit ownership in publication preparation

**Files:** `python/src/beliefs/publish.py`; new portable test module;
`python/tests/test_publication_attribution.py`; live cut-46 mutation guard.

**Interfaces:** Produces keyword-only `own_corpora: frozenset[str] = frozenset()`
on `publication_preview(...) -> PublicationPreview` and `publish(...) -> PublishOutcome`.
Add the same optional keyword to `_selected_attributions(...) -> tuple[tuple[str, str, str], ...] | None`.
Consumes `publication._HEX32` and existing capture, registry and snapshot types.

- [x] Write Y5-f and Y17-q/r/s/t/u/v/x in the new module using
  `capture_fixture`, `wrapper_fixture`, `frozen_attempt`, `pin` and `Prepared`
  from `test_publication_attribution`. Allow `wrapper_fixture.run` to accept
  `own_corpora=frozenset()` and pass it to the real publish function; return
  its existing resolver/view from the fixture so preview uses the same values.
  Preserve old default tests. These are fixture extensions, not product wrappers.

  Add `test_ownership_refusals_before_intent` for the unchanged-file/intent
  assertions below (additional evidence, not another declaration unit).
  Pin these assertions, with release cases named `v2`/`v3`:

  ```python
  assert origins == (None if version == 2 else ())  # declared markerless holder
  assert world.registry() == before_registry       # no provenance rewrite
  assert (caught.value.reason, caught.value.corpus_ids, caught.value.refs,
          caught.value.field) == (
      "attribution-own-source-invalid", (cid,), ("run:a",), "marker-present")
  assert snapshot.records == preview.records
  assert snapshot.attributions == preview.attributions
  assert list(ops.iterdir()) == []                  # pre-intent refusal case
  assert "intent" not in calls
  ```

  Y5-f rejects list/set/None and non-exact-string members with TypeError,
  and uppercase, 31/33-character, newline-suffixed IDs with ValueError;
  include an invalid **unselected** ID. Trap resolver/epoch access so validation
  precedes preparation. Y17-r includes a valid unknown unselected ID with no
  effect. Y17-s uses a marker in `captures[cid]` absent from selected IDs and
  the mock address map, with normal and malformed marker content across
  Fresh/ForkOf/ReplicaOf. Y17-t combines a later missing admission with an earlier
  marked holder, then reverses registry order and proves sorted marker errors
  beat v2 carried refusal/v3 invalid-source errors. Y17-u owns one markerless
  holder beside a publication with an earlier origin; assert exact remaining
  entries and v2 remaining-corpus refusal. Y17-x traps source/registry reads
  around `_expected_marker` with frozen None and () formats and both destinations.
- [x] Run `just test-one tests/test_owned_replica_publication.py`; require
  failures for the absent ownership behavior, not broken fixtures/imports.
  Unchanged recovery regression assertions may already pass; record them as
  regressions, not manufactured RED evidence.
- [x] At `publication_preview` entry validate exact container/member types and
  `_HEX32.fullmatch`. Add no generic validator library. Pass the value into
  `_selected_attributions`. After its complete admission pass, scan sorted
  selected declared holders' `captured_records`, refuse any MARKER_KIND with
  the specified fields, then exclude them from `replicas`. Leave the remaining
  v2/v3 code intact. Thread the argument from `publish` into this same preview.
  Do not modify `_expected_marker`, snapshot encoding, resume or registry code.
- [x] Adjust test spies forwarding `_selected_attributions` in
  `test_publication_attribution.py` and
  `acceptance/test_publication_attribution_acceptance.py` to accept/forward the
  optional keyword. Existing default assertions must still pass.
  Update live cut-46 sabotage overrides for Y17-a/g/i where filtering, call
  signature and admission adjacency changed. Preserve canonical declaration,
  assertions and check IDs. Inspect Y17-j/k/l and cut-40 Y6-a for incidental
  staleness; change only a demonstrated stale anchor, with a ledger disposition.
- [x] Run new and existing portable attribution/session-preview tests through
  `just test-one`; run cut-46's anchor/importability guard separately through
  `just test-one tests/acceptance/test_n2_cut46.py -k 'each_arm_targets'`.
  Record each changed legacy arm for Task 4's full kill proof. Then
  `just test-fast`, `tasks check`, and commit
  `feat(publication): allow declared own markerless replicas`.

### Task 3: Carry ownership through the session and durable lifecycle

**Files:** `python/src/beliefs/session/writer.py`,
`python/tests/test_session_publish_door.py`, new durable acceptance module.

**Interfaces:** Adds the same keyword-only `own_corpora` default to
`ScopedWriter.publish(...) -> PublishOutcome`, forwarded unchanged to Task 2's
public publish. `resume_publish`, constructors and ledger formats stay exact.

- [x] Write `test_y17_w_scoped_ownership`: a spy on the act sees the exact
  frozenset object; existing malformed/closed/stale/under-permitted session
  cases trap `open_world` and prove their earlier error wins even when the
  declaration is malformed. Use the existing `publishing_session` and door
  helpers, closing sessions in finally blocks. Run it through `just test-one`
  and observe absent parameter/forwarding behavior before the one forwarding edit.
- [x] Add the argument and forwarding only. Run
  `just test-one tests/test_session_publish_door.py` to GREEN, retaining the
  existing binding/report and recovery checks. No new primitive: verify the
  unchanged permit inventories rather than adding duplicate entries.
- [x] Build the durable fixture from the existing attribution acceptance
  module's `source`, `world_at`, `build`, `context_at`, `saved_marker`, `resume`
  and `unavailable` helpers. Replicate a real unpublished source root, export
  its head, restore against that observer, and `admit_arrival(..., ReplicaOf(cid), ...)`.
  Require `validated` and identical source/destination corpus IDs. Do not
  fake a Fresh admission. In the destination world create/admit a separate
  write root, include both roots in WorldConfig/mounts, mint a project selecting
  the replica's world records, then build the epoch. The source fixture remains
  untouched. Use unique roots, fixture cleanup and existing fake transport.
- [x] Add five end-to-end functions (parameter cases are additional evidence):
  `test_owned_replica_preview_and_publish` (v2/v3),
  `test_owned_replica_refusal_preserves_intent_and_ops` (no declaration,
  marker-present, missing admission and closure/pin failure),
  `test_owned_replica_scoped_publish` (v2),
  `test_owned_replica_local_resume` (v2/v3), and
  `test_owned_replica_remote_mark_only_resume` (v3).
  Assert full preview/snapshot equality, same contributing corpus identity,
  unchanged admission digest/provenance, and exactly one binding and success
  report. For a marker-bearing case use a genuine publication arrival; for
  out-of-band damage use the existing damage fixture and assert its earlier
  refusal, not marker-absent ownership. Session success also asserts its act
  ledger names the resulting binding/report.
- [x] For local retry, crash after request/snapshot persistence, save expected
  marker bytes, remove the source copy and trap preparation/registry access;
  resume with no declaration and assert exact marker content. For remote retry,
  crash after transport mark persistence, remove request/snapshot and source
  inputs using the existing mark-only test pattern, then resume with the fake
  transport; assert preserved marker and single binding/report. Restore patches
  before independent postconditions that legitimately read fixtures.
- [x] Run portable tests and
  `just test-one tests/acceptance/test_owned_replica_publication_acceptance.py`
  separately, then existing attribution acceptance regressions. Also run
  `just test-one tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py`.
  Record actual counts and capability tuple; then `just test-fast`, `tasks check`
  and commit `feat(session): publish declared own replicas through scoped calls`.

### Task 4: Prove the amendment and discharge cut 47

**Files:** new declaration, shim, N2 guard and runner from the file map;
`python/tests/test_recent_cut_acceptance.py`; affected live legacy guards;
roadmap accounting, current docs and new results record.

**Interfaces:** `CUT47_ARMS`, `DECLARATION_UNITS`, `UNIT_CHECKS`, `CO_CITED = ()`,
`unit_of(row: str) -> str`; `cut47_acceptance.declared_accounting() -> (9, 9, 2)`;
runner `main(argv: list[str]) -> int` chaining cut 46 before new durable/N2 modules.

- [x] Materialize the nine-unit table into `n2_arms_cut47.py`. Each mutation
  targets one unique source span and preserves parsing/importability; it must
  fail its named assertion against a passing normal check. Pin the completed
  declaration's content digest in its guard and commit them together, after
  which canonical declarations are frozen. Do not invent a future commit/hash
  or regenerate expectations silently after edits.
- [x] Add the acceptance shim and guard using cut 46's existing pattern, with
  `frozen_guards.content_pin_holds`/`commit_pin_holds` for Python sources.
  Pin Task 1's actual freeze commit/hash and §§2–7; preserve all earlier
  declaration pins and forbid reuse of their check node IDs. Verify exact
  9/9 inventory, one arm per unit, unique checks, unique matching source
  spans, AST parse after sabotage, passing baselines and sound kills. New git
  subprocess calls use the explicit isolated environment from Global Constraints.
- [x] Add a bounded `test_cut47_pilot` in the guard: run `baseline` and `audit`
  for Y17-s alone and assert `resolved`/`sound`. Run this and one local/remote
  durable case through `just test-one` before the extended successor chain.
  Separately run the complete new guard and legacy cut-46 guard so all new
  mutations and retargets are shown to kill their checks. Record the verdicts;
  a syntax/collection failure is not a kill.
- [x] Add `cut47_acceptance.py` using `run_acceptance`, defaulting to
  `MAIN_CHECKOUT / ".work" / "acceptance" / "cut47"`, with the prefix and
  phase tuple frozen in Task 1. Add import, parametrization, id and output
  assertion to `test_recent_cut_acceptance.py`:

  ```python
  (cut47, 47, (9, 9, 2))
  assert "guarantee rows exercised: 2 (0 newly closed; Y5 and Y17 amendments reclosed)" in output
  ```

  Run `just test-one tests/test_recent_cut_acceptance.py -k cut47` to prove
  command arguments, environment, cleanup and accounting before the real run.
- [x] Commit the declaration/runner and recorded checks after `just test-fast`
  and `tasks check`, then run the complete chain through the front door:
  `just --set one_cmd "cd python && uv run --frozen python tools/cut47_acceptance.py" test-one -q`.
  Use a harness-tracked process and retain command, counts, exit status and log
  evidence. On refusal or failure, inspect completed output before retrying;
  no skip or unrun arm permits discharge. Canonical multi-session evidence
  belongs under the task's persistent WORK_ROOT directory with retention notes.
- [x] Only after successful conformance, prepare the discharge record and add ACCOUNTING[47] naming
  the results §2 and full Y5/Y17, remove their REOPENED entries and regenerate
  live totals. Update current README, adoption ledger, roadmap, spec/plan status
  and results with exact evidence, limits, retarget rulings and consumer status.
  Preserve cut-46 history. Re-run affected documentation/runner tests and
  `just check`; do not repeat the full suite without a changed behavior or
  unresolved concern. Record the pending sci-9a7ce2 and sci-775e90 rollout.
- [ ] Request the final whole-branch read-only review under executing-plans;
  record it before acting. Fix/rule on Critical/Important findings in the
  prescribed corrective rounds, with a fresh scoped re-review. Keep every
  ruling and deferred minor in the ledger and final report. Review any final
  evidence/status edits as part of that branch review, not after approval.
  Close children on their branch, account for retained evidence, then close
  beliefs-7c612b and integrate locally only when review and required checks pass.
  No push. Recheck/attach ignored evidence, run `tt-report` and host-pointer
  checks before any worktree cleanup.

## Consumer handoff and self-review

sci-9a7ce2 depends on beliefs-7c612b and owns science's two call sites, comments,
documentation and classifier-precondition tests. sci-775e90 now depends on both
and retains the live milestone rerun. This plan does not enter another code
checkout or change live mounts to make the milestone appear fixed.

Self-review: spec §§1–2 are carried into Task 1's amendment rationale;
§§3–4 into Task 2's exact API, validation and refusal tests; §5 into Tasks 2/3's
frozen-format/retry checks; §6 into the filed consumer task and rerun dependency;
§7 into Tasks 2–4, the accounting row and required baseline; §8 into the scope
limits. All five Review Focus conditions have named tests. That was the pre-implementation self-review at plan freeze; execution evidence
and fixture adjustments are now recorded in the cut-47 results.
