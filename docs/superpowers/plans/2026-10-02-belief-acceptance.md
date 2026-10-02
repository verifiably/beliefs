# Belief acceptance — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply a supplied acceptance predicate before assessment, verification
and correction effects; return its selection statement and deterministic
exclusions; discharge G10–G13 in the successor conformance cut.

**Architecture:** Extend the existing gather and standing functions. One private
selection object belongs to one invocation and owns the decision cache and
completion report. Ordinary corrections use mapped records and inventoried
facets; snapshot standing uses the full capture. The pure evaluator receives
selected records and the completed context. Only the statement extends closure
identity. No facade, trust registry or new runtime dependency.

**Tech Stack:** Python 3.11+, frozen dataclasses, `science.identity.v1`, existing
pytest fixtures, the N2 mutation harness and the certified acceptance runner.

**Spec:** `docs/superpowers/specs/2026-10-02-belief-acceptance-design.md`, accepted
at `dc41764` in spec review round 3. Read it before implementation. The review's
three remaining items are addressed here: refusal parity in G12-l, representative
early/late errors in G13-c/d, and an appended task attribution correction.

**Status:** approved for execution after the two P2 corrections from plan review
round 1; corrections incorporated below. Execute natively
with `superpowers:executing-plans` after approval: these tasks share gather state
and fold interfaces, so per-task agent handoffs would add coordination overhead.

## Global Constraints

- Reuse `.worktrees/acceptance-filter`, branch `feat/acceptance-filter`, locked
  on WORK_ROOT storage. Baseline is `dc41764`; main product baseline is `676e2f8`.
  `just setup` already passed. Paths shown to the user include the worktree prefix.
  Run commands from the canonical worktree path (`pwd -P`), avoiding pytest's
  ELOOP through the `.worktrees` symlink in open_root.
- Proposed cut number is **45**, following cut 44. Task 0 rechecks branches and
  worktrees before freezing; a newly occupied number requires an explicit plan
  amendment, not overwriting another cut. Freeze before changing product code.
- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  This lane adds no write entry point. Task 6 verifies both inventories.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
  Task 6 owns `(cut45, 45, (34, 34, 4))` and its G10–G13 line.
- **Accounting:** 34 arms, 34 declaration units, four new guarantee rows.
  G10 has six units, G11 six, G12 twelve and G13 ten. Each table row below is
  one unit and one arm. Other regressions are required checks, not extra units.
- Preserve old frozen cuts and canonical declaration files byte for byte.
  Live overrides: cut 18's **M1** verification membership uses
  verification_targets instead of visited (Task 3), and cut 33's **C3-b** local
  enumeration call gains counts (Task 2). Cut 33's **BI-5** receipt comparison
  gains indentation under the unrestricted branch (Task 2 finding; same check
  and assertion). Preserve their assertions and checks.
  `tests/test_arm_staleness.py` must remain green. Any other stale arm requires
  identifying its owner and amending this retarget list before proceeding;
  never silently weaken a check or edit its frozen body.
- `acceptance=None` preserves unrestricted selection, reasons, admission and
  closure bytes. Accept-all preserves values, admission **and refusal behavior**;
  its statement intentionally changes the digest. A parity failure is a blocking
  finding to investigate before discharge, not permission to declare a stricter
  contract. Do not remove either filtered comparison to make a test pass.
- Preserve binding, damage, absence, epoch packaging and capture integrity checks.
  Acceptance is never a repair or fallback. Call the predicate for every candidate,
  including irrelevant records, because Science §9.4 requires every exclusion.
- Singleton holders apply only to commons milestone 1a. Do not implement overlap;
  `beliefs-81367e` must revisit the predicate over all holders for milestone 1b.
- Run focused checks through `just test-one`; run `just test-fast` before each
  implementation commit and this plan commit. Run `tasks check` with zero errors;
  report warnings. Full suites follow repository hooks/CI, not each edit.
- Use conventional commits without attribution. Keep task changes on this branch
  through the CLI. Commit the accepted spec and this plan in the lane. No push,
  PR, host-pointer change or deployment is authorized by this plan.
- Long checks use harness-tracked `exec_command` sessions and bounded
  `write_stdin` waits; no detached jobs. Acceptance writes go to the main
  checkout's `.work/acceptance/cut45`, since the worktree storage is uncertified.
  Capability refusals are failures with the exact tuple recorded. Before the
  complete chain, run Task 7's bounded pilot through its verdict.

## Review Focus

1. **A failure names a rejected twin's stored address.** The accepted assessment
   must still fail admission. G11-d/e/f in Task 3 distinguish structural targets,
   accepted identities and correction scope.
2. **An unrelated exclusion hides a corrupt receipt.** G12-h/i in Task 2 prove
   local-vs-world comparison remains unconditional and receipt comparison is
   waived only by excluded transitive in-corpus counters.
3. **Drift contributes an alias to the wrong resolver.** G12-g/l in Tasks 2/5
   distinguish mapped ordinary folds from full-capture snapshot folds and pin
   accept-all refusal parity.
4. **Rejected malformed snapshot records are validated too early or cached history
   leaks across policies.** G12-e/k and G13-i in Tasks 2/4 pin pre-validation
   filtering, filtered history and invocation-owned decisions.
5. **An early error exposes partial exclusions, or a late error loses completed
   ones.** G13-c/d/e in Task 4 pin the completion boundary, reason preservation
   and deterministic empty incomplete reports.

## File map

All paths here are repository-relative; user-facing paths add the worktree prefix.

| Files | Responsibility / task |
|---|---|
| `docs/designs/2026-10-02-conformance-cut-45.md` (new), `docs/designs/2026-08-02-epistemic-kernel-design.md`, `docs/designs/2026-08-03-correction-lifecycle-design.md`, `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md`, `python/tests/test_designs_corpus.py` | Bank G10–G13, acceptance scope and frozen obligations (0) |
| `README.md`, `docs/guide/contracts-and-adoption.md`, `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, spec status, task records | Current accounting and commons prerequisite; discharge status (0/7) |
| `python/src/beliefs/belief.py`, `python/tests/test_belief.py`, `python/tests/test_acceptance.py` (new) | Public value types, pure guard and context propagation (1) |
| `python/src/beliefs/evaluation.py`, `corpus.py`, `world/view.py` under the same package; `python/tests/test_acceptance.py`, `test_world_standing.py`, `test_snapshot_retraction.py` | Private selection state, correction membership and folds (2) |
| `python/src/beliefs/evaluation.py`, `python/tests/test_acceptance.py`, `test_evaluation.py`, `test_world_view.py` | Evidence filtering and twin verification membership (3) |
| `python/src/beliefs/evaluation.py`, `belief.py`, `closure.py`; `python/tests/test_acceptance.py`, `test_closure.py`, `test_evaluation.py` | Completion reporting, wrapper behavior and closure statement (4) |
| `python/tests/acceptance/test_n2_cut33.py`, `python/tests/acceptance/test_n2_cut18.py` | C3-b and M1 live retargets; frozen declarations untouched (2/3) |
| `python/tests/test_acceptance.py`, `python/tests/acceptance/test_belief_acceptance.py` (new) | Full regression matrix and durable acceptance (5) |
| `python/tests/n2_arms_cut45.py`, `python/tests/acceptance/n2_arms_cut45.py`, `python/tests/acceptance/test_n2_cut45.py`, `python/tools/cut45_acceptance.py` (new), `python/tests/test_recent_cut_acceptance.py` | Frozen declaration, guard, successor runner and inventory (6) |
| `docs/plans/2026-10-02-conformance-cut-45-results.md` (new), `docs/guide/open-questions.md` if its active commons claim changes | Certified evidence and final disposition (7) |

## Declared arms and checks

Every check is `test_acceptance.py::test_<unit with hyphen replaced by underscore>`,
with the suffix shown below. Thus G10-a names
`test_acceptance.py::test_g10_a_all_assessments_rejected` (lowercase guarantee id).
The table names the mutation's responsible branch; Tasks 1–4 fix its implementation
seam. Task 6 records exact unique source replacements after those seams exist.
The assertions are frozen in Task 0; changing one requires a disposition.

| Unit | Test suffix / decisive assertion | Independent mutation target |
|---|---|---|
| G10-a | `all_assessments_rejected`: NoBelief/no-eligible-assessment, empty reached set | Bypass assessment selection |
| G10-b | `contradictory_twin`: rejected disagreeing twin inert; both accepted refuse | Bypass assessment selection before collapse |
| G10-c | `malformed_assessment`: rejected malformed facet never decoded | Move assessment decode ahead of selection |
| G10-d | `canonical_holder`: callback receives holding corpus and live address, including alias inputs | Pass a deprecated assessment address |
| G10-e | `manifest_preflight`: missing/malformed manifest raises before iteration/resolution/callback | Skip filtered local manifest preflight |
| G10-f | `accepted_attribution`: rejected holder never joins identity attribution | Attribute a rejected twin |
| G11-a | `rejected_failure`: accepted evidence remains admitted | Bypass verification selection for a failure |
| G11-b | `rejected_pass`: no accepted pass means no admission | Bypass verification selection for a pass |
| G11-c | `rejected_superseder`: rejected later pass cannot clear accepted failure | Include rejected superseding verification |
| G11-d | `failure_names_rejected_twin`: accepted failing edge to rejected twin invalidates accepted identical assessment | Populate verification targets from accepted assessments only |
| G11-e | `pass_names_rejected_twin`: accepted passing edge to rejected twin admits accepted identical assessment | Test verifies membership against visited |
| G11-f | `edge_scope`: rejected-only identity admits nothing; correction of rejected twin stays out of closure | Union verification targets into correction scope |
| G12-a | `node_retraction`: rejected node correction cannot subtract evidence | Bypass ordinary retraction selection |
| G12-b | `route_retraction`: rejected route correction cannot retire lineage | Retire a rejected route target |
| G12-c | `counter_retraction`: rejected counter cannot restore its accepted target | Include rejected counters in facets |
| G12-d | `changed_chain_receipt`: excluded reachable counter permits changed resolution; multi-hop C_c(r) is honored | Require receipt comparison despite excluded transitive counter |
| G12-e | `malformed_snapshot_candidate`: rejected malformed record outside chain cannot poison fold | Validate snapshot facet before selection |
| G12-f | `accepted_snapshot_chain`: accepted malformed chain still raises RetractionUnreadable | Omit accepted chain-member validation |
| G12-g | `mapped_oracle`: post-epoch record/alias does not enter ordinary local oracle | Use full captured resolver for L_c |
| G12-h | `split_with_exclusion`: split-corpus local/world disagreement still refuses with unrelated exclusion | Skip L_c-vs-W comparison |
| G12-i | `unchanged_receipt`: unrelated exclusion cannot hide corrupt surviving receipt | Disable all receipt checks on any exclusion |
| G12-j | `snapshot_root`: rejected post-epoch snapshot root is inert | Use unrestricted snapshot fold |
| G12-k | `snapshot_history`: only surviving filtered chain/history enters closure and trace | Reuse unfiltered cached history |
| G12-l | `accept_all_refusal_parity`: same refusal/absence/admission outcomes as unrestricted | Omit filtered receipt-fidelity check |
| G13-a | `policy_validation`: exact bool, callable, nonempty exact str and v1 encoding; exception propagates | Coerce result with bool instead of rejecting |
| G13-b | `complete_report`: every irrelevant exclusion appears once, sorted | Apply relation matching before predicate |
| G13-c | `early_error`: caught pre-completion error reports empty incomplete exclusions under both scan orders | Expose decisions while incomplete |
| G13-d | `late_error`: caught late consulted error retains completed exclusions and original reason | Reset report in exception handler |
| G13-e | `late_absence`: supplied lineage snapshot not_present yields unavailable-corpus-absent with complete report | Mark every absence incomplete |
| G13-f | `supplied_context`: forged gather context raises before reads even without policy | Remove supplied-acceptance guard |
| G13-g | `pure_incomplete`: pure refusal after binding guard and before consulted walk; wrapper bad-binding refusal carries empty incomplete report before reads | Remove pure incomplete guard |
| G13-h | `closure_statement`: statement changes digest; unrelated exclusion does not; both closure paths agree | Omit acceptance_policy from projection |
| G13-i | `two_policies`: same view, different calls, no decision/snapshot cache leakage | Return unrestricted snapshot cache on filtered call |
| G13-j | `capture_integrity`: damaged/absent coverage cannot be hidden by reject-all | Return rejected-pool answer before coverage checks |

## Task 0: Freeze the successor cut and bank the guarantees

**Consumes:** approved spec and plan, current roadmap and cut-44 accounting.
**Produces:** immutable cut-45 obligation document, G10–G13 banked as open,
freeze commit/hash and task children for Tasks 0–7 under `beliefs-d9bc57`.

- [ ] Run `tasks prime` in this worktree. Scan local/remote branches with
  `git for-each-ref` and `git ls-tree -r --name-only <ref> docs/designs` for cuts
  45 or later, and check each path in `git worktree list` for uncommitted freezes.
  Expected: cut 44 is highest; only this plan proposes 45.
- [ ] Copy G10–G13 from spec §7 into the kernel table. Amend G3/G8 and kernel §5.1
  to distinguish selected evidence, opaque statement and explanatory exclusions.
  Amend correction-standing prose to name both filtered resolvers; add the four
  rows to the formal-model coverage inventory and `GUARANTEE_TABLES["G"]`.
- [ ] Write `docs/designs/2026-10-02-conformance-cut-45.md` using cut 44's seven
  headings: What this cut is; The boundary; Selection; Accounting; N2 and
  acceptance obligations; Second reader; Limitations. Include a frozen header
  with spec/plan paths, this complete arm/check table and accounting `(34,34,4)`.
  Prefix is `("cut44_acceptance.py",)`; phases are
  `("test_belief_acceptance.py", "test_n2_cut45.py")`. Task 5 declares eight
  durable test functions. Include both resolver definitions, refusal parity and
  the M1/C3-b live retargets in the N2 obligations section.
- [ ] Run `cd python && uv run --frozen python tools/roadmap_status.py` to derive
  totals. Current 220/247 becomes 220/251 at freeze, 224/251 only after discharge
  (unless another verified change intervenes). Update README, guide, ledger and
  roadmap together. Reopen `world-read` for `belief-acceptance`; distinguish the
  commons workflow from the completed historical dogfood criterion. Retain its
  evidence, and retain the contract-freeze ordering behind oracle amendments.
- [ ] Register task children using `tasks add --parent beliefs-d9bc57 --plan
  belief-acceptance --step '<exact Task heading>'`, with direct process and the
  executing agent. Add sequential dependencies with `tasks dep`; start Task 0.
  Update the spec status to approved/frozen cut 45. Record freeze evidence in notes.
- [ ] Run `just test-one tests/test_designs_corpus.py tests/test_check_guide.py`,
  `just test-fast`, `tasks check`, then commit `docs(cut): freeze belief acceptance
  guarantees for cut 45`. Record `git rev-parse HEAD` and `sha256sum` of the cut.

## Task 1: Define acceptance values and the pure evaluator boundary

**Files:** `belief.py`, `test_belief.py`, new `test_acceptance.py`.
**Produces:** `AcceptancePolicy(counts: Callable[[str,str],bool], statement: str)`;
`AcceptanceContext(statement: str, excluded: tuple[tuple[str,str],...],
complete: bool)`; optional `acceptance` fields defaulting to None on
SuppliedContext/Belief/NoBelief/Refused. Export both new types from `belief.__all__`.

- [ ] RED: add `test_acceptance_value_validation` and G13-g using
  `test_belief.scenario` for the pure path.
  Constructor checks cover noncallable, empty/non-string statement and lone
  surrogate. Add the G13-a callback test in Task 2 when its caller seam exists;
  do not commit a failing future test. Assert incomplete/nonempty exclusions raises the
  exact specified MalformedRecord reason. Use this pure guard test:

  ```python
  kwargs = scenario()
  selection = AcceptanceContext("pinned policy", (), False)
  kwargs["context"] = replace(kwargs["context"], acceptance=selection)
  def unexpected_consulted(**_kwargs):
      pytest.fail("incomplete selection reached consulted_contracts")
  monkeypatch.setattr("beliefs.belief.consulted_contracts", unexpected_consulted)
  answer, admission = evaluate_traced(**kwargs)
  assert answer == Refused("acceptance-selection-incomplete", acceptance=selection)
  assert admission == NotReached()
  answer, admission = evaluate_traced(**scenario(
      context=kwargs["context"], binding=object(),
  ))
  assert isinstance(answer, Refused)
  assert answer.reason.startswith("binding-not-exact")
  assert answer.acceptance == selection and admission == NotReached()
  ```

- [ ] Run `just test-one tests/test_acceptance.py -k 'value_validation or
  pure_incomplete'`; verify failure is the missing contract, not a fixture error.
- [ ] Implement frozen types using current sealed/final dataclass conventions.
  Share statement validation privately: `type(text) is str and text != ""`,
  then `v1.encode(text)` without swallowing IdentityError. Policy requires
  `callable(counts)`; context normalizes sorted unique pairs and refuses nonempty
  incomplete exclusions. Retain exact statement text; do not parse it as policy.
- [ ] Place incomplete refusal immediately after pure step 1. Propagate context
  on every pure answer with one boundary projection using `dataclasses.replace`
  around the existing computation; keep the current body and N2 source anchors.
  No mutable module state or callback inside the pure evaluator. Preserve public
  signatures except the agreed optional context/answer fields.
- [ ] GREEN: `just test-one tests/test_belief.py tests/test_acceptance.py`;
  only Task 1's tests exist at this point. Run fast/check,
  close the child via CLI and commit `feat(belief): define acceptance context`.

## Task 2: Filter corrections using invocation-owned decisions

**Files:** `evaluation.py`, `corpus.py`, `world/view.py`, standing/snapshot tests
and `test_acceptance.py`.
**Consumes:** Task 1's value types, existing carried enumeration and packaged map.
**Produces:**

- Private `_AcceptanceSelection(policy: AcceptancePolicy | None)`, with
  `counts(corpus_id: str, address: str) -> bool`, `finish() -> None`, and
  `policy: AcceptancePolicy | None`, `report: AcceptanceContext | None`.
  Report is initially None for unrestricted calls,
  otherwise incomplete with empty exclusions. Its cache is a fresh
  `dict[tuple[str,str],bool]` per invocation. `finish` publishes rejected pairs.
- `local_retraction_enumeration(view, *, counts: Callable[[str,str],bool] |
  None = None)` and `snapshot_standing(views, subject_kind="producer", *,
  counts: Callable[[str,str],bool] | None = None)`; existing callers unchanged.
- `WorldReadView.snapshot_standing(*, counts=...)` forwards filtered calls without
  reading/writing its unrestricted cache. `_mapped_view(corpus_id)` returns a
  restricted `_CapturedCheckView`; `_retraction_discovery` retains immutable
  `Mapping[str,tuple[str,...]]` from the packaged map, with written target keys.
- `_CapturedCheckView(records, *, addresses: Mapping[str,str] | None = None)`:
  when addresses is supplied, use exactly that resolver map. Default behavior
  still includes all supplied records' live/deprecated ids for snapshot folding.

- [ ] RED: implement G12-a through k in `test_acceptance.py`, reusing
  `split_evaluation_world`, `world_kwargs`, `profile_with`, `writer_at`,
  `support_in`, `retracts`, `snapshot_retraction`, `broken_counter`, `publish`
  and `hold_shipped`. Raw malformed records use `fixtures_cut4.raw_write`,
  then a fresh view; never mutate an already-open capture and claim it reread.
  G12-d has a multi-hop chain whose excluded counter is not directly adjacent.
  G12-g uses a real post-epoch alias to show that the full captured resolver
  sees aliases absent from the epoch-mapped resolver. Corpus admission refuses
  live/deprecated collisions before capture; characterize that live-id precedence
  with a synthetic `_CapturedCheckView` pair rather than weakening admission.
  Precompute snapshot standing and supply it during gather, then assert ordinary
  folding makes no calls to the full captured resolver. Switching L_c to
  `_captured_views[c]` must fail this assertion.
- [ ] For G12-i reuse `test_world_receipts.repackage`: edit a surviving receipt
  resolution **and** its subject identity coherently so opening passes packaging
  and carried-enumeration checks. Reject an unrelated correction. Evaluation must
  raise RetractionResolutionDisagreement for the corrupted surviving ref.
  G12-h relocates a counter as `TestTheSplit` does; reject an unrelated record.
- [ ] Run `just test-one tests/test_acceptance.py -k g12` and observe the expected
  missing-seam failures. Add the shared private `_gather(..., selection)`;
  public gather creates state, while the wrapper can later pass its own state.
  Add optional `acceptance` keywords on public gather/evaluate-over functions
  and forward them; do not expose the state in a public signature.
- [ ] Implement exact-result caching and fail-closed callback behavior:

  ```python
  key = (corpus_id, address)
  if key not in self._decisions:
      result = self.policy.counts(corpus_id, address)
      if type(result) is not bool:
          raise MalformedRecord("acceptance-result-not-bool")
      self._decisions[key] = result
  return self._decisions[key]
  ```

  The unrestricted branch returns True before accessing policy.counts; callback
  exceptions propagate. Filter local retractions before facet validation. Load
  the local manifest once, after context guards and before scans, when filtered.
- [ ] Snapshot fold calls `counts(corpus_id,node.id)` before
  `_validated_retraction_facet`, fold or chain validation. Full captured
  resolvers remain in use. Forward the same cached callback into all folds;
  duplicate visits decide once. Preserve snapshot binding and carrier guards.
  The ordinary enumeration call in `_gather` becomes:

  ```python
  counts = None if selection.policy is None else selection.counts
  enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view, counts=counts)
  ```

  In cut 33's `_LIVE_SABOTAGES`, retarget C3-b to that exact new enumeration
  line. Its after-text keeps the line and appends the original world coverage
  corruption `(f"{c}@{s}" for c,s in view.stamp.coverage)`. Keep C3-b's existing
  relocation check and assertion. Frozen `n2_arms_cut33.py` stays unchanged.
- [ ] Retain the already parsed packaged `retraction-discovery-map.yaml` from
  `published.documents`, validating its targets/retractions shape with EpochMalformed
  on malformed data. No live rediscovery and no decoding rejected current facets.
  Construct mapped addresses from `_recorded` entries whose holder matches c
  and whose uid is in `_held[c]`; map them to held `node.id`. Use only these
  addresses and records for `_mapped_view(c)`.
  Its resolver construction is:

  ```python
  records = tuple(self._held[corpus_id].values())
  addresses = {
      ref: self._held[corpus_id][uid].id
      for ref, (holder, uid) in self._recorded.items()
      if holder == corpus_id and uid in self._held[corpus_id]
  }
  return _CapturedCheckView(records, addresses=addresses)
  ```
- [ ] Ordinary inventoried correction order is `_absence_of(view,ref)`, then
  `view.resolve(ref)`/holder, then counts on the canonical address, then get and
  validation for survivors. A present nonresolving ref remains RetractionUnreadable.
  Build F_c from surviving inventory only. Compute L_c on `_mapped_view(c)`;
  compute W on the world union. Compare L_c(r) vs W(r) for **every** survivor.
- [ ] Build the original per-corpus counter adjacency from the retained map:
  restricted-resolve each written target and listed correction; retain edges
  only when both endpoints are inventoried retractions in c. Walk reachable
  counters with a visited set. Compare receipt(r) to L_c(r) unless at least one
  reachable counter was rejected. An exclusion of r, of an unrelated correction,
  or of a post-epoch candidate is never a global waiver. Use W resolutions for
  subtraction, route retirement and scoped enumeration.
- [ ] GREEN: run `just test-one tests/test_acceptance.py -k g12`, then
  `just test-one tests/test_world_standing.py tests/test_snapshot_retraction.py
  tests/test_local_standing.py tests/test_arm_staleness.py`. Complete G13-a's
  callback checks. Fast/check, child done, commit
  `feat(evaluation): filter correction standing before validation`.

## Task 3: Select evidence while preserving rejected-twin edges

**Files:** `evaluation.py`, `test_acceptance.py`, evaluation/world regression tests.
**Consumes:** selection cache and filtered standing from Task 2.
**Produces:** accepted semantic inputs with separate structural
`verification_targets: set[str]` and accepted `visited: set[str]`.

- [ ] RED: implement G10-a through f and G11-a through f. Reuse
  `test_evaluation._fixture(tmp_path, PROPOSITION_REF)` and `fixtures_cut4.reopen`.
  Create identity twins with distinct stored addresses and the same spec/run/
  proposition; change outcome only for the contradictory-facet test. Derive the
  verification identity from the accepted assessment. Set the verifies edge to
  rejected twin B, accept A and the verification. Test both passed and failed.
  Remove other passing verifications when proving a rejected pass cannot admit.
  G11-f adds a correction of B and asserts it is absent from scoped.found.
- [ ] Run `just test-one tests/test_acceptance.py -k 'g10 or g11'`. Install read
  sentinels on assessment/verification decoders for rejected malformed tests;
  assert neither decoder nor attribution/trace contains rejected records.
- [ ] Iterate world evidence using `_mapped_records()` for `(cid,node)` before
  identity collapse; use the preflight cid for local evidence. Call counts before
  relation selection so irrelevant records enter the report. For assessments:

  ```python
  accepted = selection.counts(corpus_id, node.id)
  # Determine assesses-edge membership without decoding facets.
  if edge_matches:
      verification_targets.add(node.id)
  if not accepted or not edge_matches:
      continue
  visited.add(node.id)
  # Existing subtraction, decoding, trace and attribution follow here.
  ```

  `edge_matches` uses existing resolved proposition membership. Include rejected
  structural targets; decode only accepted, unretracted matching assessments.
- [ ] Verification order: counts, structural edge resolving into
  verification_targets, accepted verification_ids bookkeeping, subtraction,
  decode, `_verification_selected(value, ids)`. Identity matching remains as
  today. Scope remains `visited | verification_ids | set(snapshot.bases)`;
  verification_targets never participates. Surviving dependency reads remain
  unfiltered, even when their corpus has excluded evidence.
- [ ] Retarget M1 in cut 18's `_LIVE_SABOTAGES`: its existing before-text changes
  only `in visited` to `in verification_targets`. Preserve the existing
  membership/decode block and after-text that widens both edge membership and
  `_verification_selected`, while leaving the new acceptance check in place.
  Its unrestricted containment check must still fail under this sabotage;
  canonical `n2_arms_cut18.py` stays byte-exact.
- [ ] GREEN: `just test-one tests/test_acceptance.py -k 'g10 or g11'`, then
  `just test-one tests/test_evaluation.py tests/test_world_view.py
  tests/test_arm_staleness.py`. Fast/check, child done, commit
  `feat(evaluation): select evidence before semantic reads`.

## Task 4: Complete deterministic reports and extend closure identity

**Files:** `evaluation.py`, `belief.py`, `closure.py`, acceptance/closure tests.
**Consumes:** `_gather` selection state and filtered history.
**Produces:** optional EvaluationInputs.acceptance; optional keyword
`build_closure(..., acceptance_statement: str | None = None)`;
all corpus-backed outcomes carry the correct report.

- [ ] RED: implement G13-b through j plus G12-k's full digest/trace assertions.
  Use actual excluded unrelated nodes for report tests. G13-c injects
  `FacetUndeclared("early sentinel")` at accepted assessment decoding, after one
  rejected record was visited; reverse the candidate order and assert byte-equal
  incomplete reports with excluded=(). G13-d injects
  `ContractDisagreement("late sentinel")` at evaluation.consulted_contracts,
  after scans/folds; assert original refusal reason, complete exclusions and no
  repeated predicate calls. These are representative boundary errors, not an
  exhaustive exception taxonomy. Existing contract tests retain real mismatch
  coverage; the sentinels isolate timing here.
- [ ] G13-e supplies a LineageSnapshot with a reachable `not_present` entry in
  its context; `absences(snapshot)` discovers it after the runs loop. Assert the
  late absence answer after completed scans without monkeypatches. Run/claim
  late-absence branches are defensive for world reads: view.absent already
  catches genuinely absent covered corpora before selection.
  Separately make a real covered BETA carrier absent and assert incomplete
  report; G13-j proves reject-all cannot hide that absence or damaged coverage.
  Neither may become no-eligible-assessment.
- [ ] G13-f supplies a hand-built complete context to gather, with and without a
  policy, and installs failing iteration/resolve/fold/callback sentinels. Expect
  MalformedRecord("supplied-acceptance-context") before all those reads.
- [ ] Run `just test-one tests/test_acceptance.py -k g13`. Reject incoming
  context.acceptance at the existing gather guard site. Wrapper binding guard
  stays first. `_evaluate_over_inputs` creates one state **before** that guard,
  so its initial report is AcceptanceContext(statement, (), False). Add the
  wrapper bad-binding case to G13-g using a read sentinel; assert Refused retains
  that incomplete report with NotReached. Unrestricted bad binding keeps None.
  Valid binding then calls `_gather`
  directly. Every existing caught exception projects `selection.report` onto
  its existing answer; do not add new catches or rerun the predicate.
- [ ] Call `selection.finish()` after verification scanning and correction scoping,
  before claim lookup/consulted_contracts. Early `_absent_inputs` uses incomplete
  report; completed runs/dependency or claim absence preserves complete report.
  Forward inputs.acceptance into `replace(context, ...)` for pure evaluation.
- [ ] `finish` constructs `AcceptanceContext(statement, sorted rejected cache
  keys, True)`. Before finishing, report remains `(statement, (), False)`.
  Populate EvaluationInputs.acceptance with that report; its closure forwards
  only `.statement`. The pure closure uses the same optional statement.
  The completion method's filtered branch is:

  ```python
  self.report = AcceptanceContext(
      statement=self.policy.statement,
      excluded=tuple(sorted(key for key, accepted in self._decisions.items()
                            if not accepted)),
      complete=True,
  )
  ```

  Unrestricted finish leaves report=None. `_gather` consumes the same state
  object passed by the wrapper, so the wrapper reads this report after a caught
  late error even when no EvaluationInputs was returned.
- [ ] Add the projection member only for supplied text:

  ```python
  if acceptance_statement is not None:
      projection["acceptance_policy"] = acceptance_statement
  ```

  Do not hash excluded pairs, completeness, callable or object identity. Use
  filtered SnapshotStanding.history when building scoped.found and its trace.
  G13-h compares `inputs.closure().digest()` with the Belief digest, changes only
  statement, and adds an irrelevant exclusion under unchanged statement.
- [ ] Update the exact signature/field inventory test in `test_evaluation.py`
  to map `acceptance` context to `acceptance_statement` explicitly; preserve its
  existing required-field inventory. Do not compare an arbitrary first-N slice
  to all parameters once the optional projection input is added.
- [ ] GREEN: `just test-one tests/test_acceptance.py tests/test_closure.py
  tests/test_evaluation.py tests/test_belief.py tests/test_arm_staleness.py`.
  Fast/check, child done, commit
  `feat(belief): report acceptance and bind its statement to closure`.

## Task 5: Finish refusal parity and durable acceptance

**Files:** `test_acceptance.py`, new `acceptance/test_belief_acceptance.py`.
**Consumes:** complete public API and Task 0's frozen assertions.
**Produces:** full portable regression matrix and eight durable test functions.

- [ ] RED: G12-l evaluates each fixture twice through evaluate_over_traced:
  unrestricted and AcceptancePolicy(lambda _c,_r: True, "accept all"). Compare
  answer type, refusal reason/detail or exception type/ref, and admission; compare
  Belief value/binding while allowing the declared statement's digest difference.
  Never catch Exception broadly or treat a fixture setup failure as parity.
  Cases: clean world; legitimate same-corpus counter chain; split counter;
  coherently corrupt receipt; accepted malformed snapshot chain; post-epoch
  ordinary drift alias; post-epoch snapshot root/counter; covered-corpus absence;
  bad aggregation binding. Keep existing packaging failures unconditional.
- [ ] Example clean parity check using existing fixtures:

  ```python
  world, _roots, published = split_evaluation_world(tmp_path, beta_refs=())
  view = open_world_view(world, published)
  kwargs = over_kwargs(world_kwargs(view, profile_with()))
  before, before_admission = evaluate_over_traced(view, "proposition:p", **kwargs)
  after, after_admission = evaluate_over_traced(
      view, "proposition:p", **kwargs,
      acceptance=AcceptancePolicy(lambda _c, _r: True, "accept all"),
  )
  assert isinstance(before, Belief) and isinstance(after, Belief)
  assert (after.value, after.policy_binding, after_admission) == (
      before.value, before.policy_binding, before_admission,
  )
  ```

- [ ] Add non-declared regression tests for unrestricted projection bytes and
  None answer fields; rejected malformed verification and ordinary correction;
  canonical enumeration aliases; raising callback without retry; selected
  dependencies in an excluded-evidence corpus; callback once per key despite
  fold reuse; duplicate-location opening still refuses. Use existing baseline
  assertions/fixtures, no production abstraction solely for test construction.
- [ ] Run `just test-one tests/test_acceptance.py`. Investigate any parity
  discrepancy against capture-time vs mapped-only resolution before proceeding;
  an intended stricter behavior requires spec amendment and review.
- [ ] Write eight durable checks using actual writers/registered roots under
  the acceptance work_directory, following cut 44's `_adopt`/teardown pattern:
  `test_assessment_twins`, `test_verification_twin_edges`,
  `test_node_and_route_corrections`, `test_counter_and_receipt_fidelity`,
  `test_snapshot_filter_and_history`, `test_completed_and_incomplete_reports`,
  `test_statement_and_two_policies`, `test_accept_all_refusal_parity`.
  Use add/retract/publish/open for honest records. Only adversarial malformed or
  forged-receipt subcases use raw fixtures/repackage, and label them. Keep durable
  writer evidence distinct from portable OperationRecorder/raw-write evidence.
- [ ] GREEN: portable `just test-one tests/test_acceptance.py`. Run the durable
  module on the certified work_directory in Task 7's pilot; no skipped capability
  result counts as discharge. Fast/check, child done, commit
  `test(belief): cover acceptance parity and durable selection`.

## Task 6: Declare N2, wire the runner and close inventories

**Files:** new canonical declaration/re-export/guard/runner; recent-cut inventory.
**Consumes:** freeze commit/hash, exact stable selection seams, 34 named checks.
**Produces:** CUT45_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of, CO_CITED;
runner accounting `(34,34,4)`, frozen declaration hash and prior pins.

- [ ] RED: add the recent-cut parametrization/import/guarantee line before the
  new runner exists, then `just test-one tests/test_recent_cut_acceptance.py`.
  Failure must identify the missing runner, not change historical expectations.
- [ ] In `python/tests/n2_arms_cut45.py`, declare each table row explicitly as
  Arm/Sabotage with its named test. Pin before/after source text that matches
  exactly once. G12-l's corrupt-receipt case must fail when its filtered fidelity
  branch is omitted; G13-c/d mutate their report seam separately. Independent
  G11-d/e/f mutations target the two membership sets and correction scope.
  Record multiple checks in one arm only when each independently fails under
  that same sabotage. Re-export the one canonical table as cut 44 does.
- [ ] Adapt cut 44's guard using its full prior-cut pins plus cut 44, add the new
  freeze/declaration hashes, exact arm/unit sets, one-check-function validation,
  source staleness and N2 findings. Do not derive obligations from implementation
  branches. Add `test_pilot_arms_fail_under_sabotage` selecting exactly
  G10-a/G11-d/G12-i/G13-d with the existing baseline/audit helpers; require
  normal checks to pass and sabotaged checks to fail assertions, not collection.
  It must not depend on the all-arm findings fixture. Task 7 runs this bounded
  pilot before the full new-arm audit or the chained runner.
- [ ] Wire `cut45_acceptance.py` through existing run_acceptance: default
  MAIN_CHECKOUT/.work/acceptance/cut45, prefix cut44, two phase modules from
  Task 0. declared_accounting checks exact 34/34 and G10/G11/G12/G13 rows.
  Success prints `guarantee rows exercised: 4 (4 newly closed: G10, G11, G12, G13)`.
  Add recent-cut row `(cut45, 45, (34, 34, 4))` and that line assertion.
- [ ] Run Task 7's bounded pilot now before the full mutation audit.
  Record its verdict with the current source/declaration hashes;
  Task 7 reuses that evidence if those hashes are unchanged.
- [ ] GREEN: `just test-one tests/test_recent_cut_acceptance.py
  tests/test_arm_staleness.py tests/test_capability_boundary.py
  tests/test_permit_boundary.py tests/test_permit_entry_points.py`; then the
  static new guard checks through `just test-one tests/acceptance/test_n2_cut45.py
  -k 'inventory or unique or source_site or pinned or byte_exact or prior or
  row_parser'`. Full mutation findings run in Task 7 after its pilot; do not
  claim nonvacuity from the static checks. Fast/check, child done,
  commit `test(cut): declare belief acceptance arms and successor runner`.

## Task 7: Discharge, review and report the lane

**Files:** new results record, current status/accounting documents and task records.
**Consumes:** implemented checks and runner; all frozen obligations unchanged.
**Produces:** certified acceptance evidence, final review disposition and lane state.

- [ ] Verify the bounded pilot recorded in Task 6 still matches source/declaration
  hashes; rerun only if changes invalidated it. The pilot has eight new durable
  checks and four new
  N2 arms, one per G10–G13, through the normal test front door on the certified
  main-checkout `.work/acceptance/cut45` root. Read all verdicts, timing and tuple.
  This pilot exercises writer/capture/evaluation, all new guarantees and mutation
  refusal. Analyze any refusal or partial output before changing environment.
  With `cut45_work` set to the main checkout's absolute
  `.work/acceptance/cut45` directory, run:

  ```bash
  SCIENCE_CUT4_ROOT="$cut45_work" just test-one tests/acceptance/test_belief_acceptance.py
  SCIENCE_CUT4_ROOT="$cut45_work" just test-one tests/acceptance/test_n2_cut45.py::test_pilot_arms_fail_under_sabotage
  ```

  The new guard uses `test_n2.workers()` for bounded pools, rather than copying
  cut 44's hard-coded eight workers. The fast suite ignores tests/acceptance;
  explicit test-one paths and the runner collect the guard. This pilot orders
  the extended mutation audit and does not
  create a second acceptance mode.
- [ ] Run the complete successor runner through the recorded front door:

  ```bash
  just --set one_cmd "cd python && uv run --frozen python tools/cut45_acceptance.py" test-one -q
  ```

  Track the process through the harness until it exits; log its output and
  phase results under main-checkout `.work/acceptance/cut45`. This chains cut 44
  and proves all 34 new arms. A missing capability is a named failure, never a
  waived guarantee. Portable CI has no authority to discharge the durable arms.
- [ ] Write results with spec/plan/freeze hashes, environment tuple, command,
  arm/unit/row counts, eight acceptance cases, parity matrix and measured times.
  Update current-facing docs to close only G10–G13 and belief-acceptance; retain
  historical cut evidence and all other open limitations. Recompute roadmap
  totals with its status tool; verify expected 224/251 against the live inventory.
- [ ] Obtain implementation review via the requesting-code-review workflow;
  record its round/verdict/model in the exact task-note format and resolve all
  blocking findings. Never attribute a forwarded model review to the messenger.
- [ ] Run `just test-fast`, `tasks check` and required hook checks after the final
  change. Re-run the affected acceptance phase only if revisions changed its
  behavior or pins. Review git diff/status, verify no task-owned processes or
  host pointers remain, and close the task with evidence in the same commit.
- [ ] Commit `docs(cut): record belief acceptance discharge`. Report the branch,
  exact passing checks and integration status. Leave remote publication behind
  explicit user authorization; preserve the worktree until integration.
  Next task is beliefs-f50596, then beliefs-aa9f88; each keeps its own gates.

## Inline review checklist for this plan

- [x] All spec §7 decisive checks map to a declared unit or named regression.
- [x] Constructor errors, callback types, completion boundary and both resolvers
  agree across the spec, interface list, tasks and mutations.
- [x] Counts are 6 + 6 + 12 + 10 = 34; four guarantee rows; eight durable functions.
- [x] Refusal parity includes corrupt receipt, split corpus and drift cases.
- [x] No implementation starts before plan approval; no discharge is claimed from
  the current 119-test design baseline or portable fast suite.

Execution dispositions: Tasks 2–4 share one commit and one fast gate. Besides M1/C3-b, retarget the live BI-5 receipt anchor in cut 33, R19e absent-answer anchor in cut 23, and portable G1 closure-signature anchor. Canonical declarations and frozen cut bodies remain unchanged.
