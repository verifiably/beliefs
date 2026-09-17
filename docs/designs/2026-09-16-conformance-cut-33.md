# Conformance cut 33 — correction remainder, slice 1

**Status:** discharged 2026-09-17 on the certified volume; results: `../plans/2026-09-16-conformance-cut-33-results.md`.
**Design:** `../superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md`, approved after four reviews; implementation in progress.
**Plan:** `../superpowers/plans/2026-09-16-correction-remainder-slice-1.md`.
**Numbered after** cut 32 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 33–39 at freeze; cut 32 is the highest discharged runner.

## 1. What this cut is

The baseline below describes `main` at `25ab84c` before implementation.

The correction carrier, write-boundary checks, local standing fold and audit
findings landed at cut 5; the world enumeration landed at cut 7; the closure
has carried a caller-supplied enumeration since cut 5. Standing still does not
reach the evaluator: assessments and verifications are read despite standing
retractions, routes are never retired during the lineage walk, and a caller can
supply an empty enumeration.

This cut makes standing a property of the read. The evaluator derives the
enumeration from its bound view, dereferences and refolds every found
retraction, refuses unreadability or disagreement, removes standing node-arm
targets before decoding, retires route-arm targets in the lineage walk, and
projects the input-scoped enumeration and effective snapshot into the closure.
It reads C7 in full, C3's two deferred coverage clauses, and C10's audit arm.
The amended G8 clause is a boundary invariant. Slice 2 owns C8 and C9.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/errors.py`, `closure.py`, `corpus.py`, `lineage.py`,
  `belief.py`, `evaluation.py`, `verification.py`, `composite.py`, `audit.py`,
  `contract/base.py`, `contract/decode.py`, `contract/estimand.py`,
  `world/epoch.py`, and `world/view.py`;
- `python/tools/reproduction/belief.py`;
- `python/tests/test_standing_read.py`, `test_world_standing.py`,
  `test_lineage.py`, `test_local_standing.py`, `test_world_view.py`,
  `test_retract.py`, `test_composite_reading.py`, `test_belief.py`,
  `test_evaluation.py`, `test_deletion_rows.py`,
  `test_reproduction_driver.py`, `verification_fixtures.py`,
  `domain_facet_fixtures.py`, and the named pre-existing acceptance modules;
- `python/tests/acceptance/test_correction_acceptance.py`,
  `python/tests/n2_arms_cut33.py`, its `acceptance/` re-export,
  `python/tests/acceptance/test_n2_cut33.py`, and
  `python/tools/cut33_acceptance.py`;
- this cut, its results record, the adoption ledger, roadmap, guide, README,
  composite-claims amendment and reproduction record.

Frozen declarations and cut bodies through cut 32 remain byte-exact.

## 3. Selection

Eleven declaration units are selected and single-homed here. The quoted row
text is byte-exact from correction lifecycle §7 at freeze.

### C7 — closes

```markdown
| C7 | Route retirement never selects silently | conflict of two routes: retire one → certifiable over the survivor; retire both → `not-certified`; assert stored basis facet unchanged throughout (route preservation) |
```

- **C7-a:** conflict of two routes, retire one → certifiable over the survivor.
- **C7-b:** retire both → `not-certified` with `lineage-incomplete`.
- **C7-c:** the stored basis facet is byte-unchanged throughout; `retract`
  writes one record.

### C3 — closes

```markdown
| C3 | The digest covers the retraction enumeration — refs, resolutions, and coverage declaration; never exact corpus states | retract an in-closure, in-coverage input → digest moves; input outside the closure → unchanged; **standing retraction in an uncovered corpus → digest unchanged, and the coverage declaration is itself a digest member — the bound is visible, not silent**; **in-coverage corpus move (content identities unchanged) → digest unchanged, receipt records the new states** |
```

- **C3-a:** a standing retraction in an uncovered corpus leaves the digest
  unchanged; the isolated closure check proves the coverage declaration is a
  digest member.
- **C3-b:** an in-coverage `move` leaves the digest unchanged and the receipts
  record the new states.

### C10 — stays partial

```markdown
| C10 | Ineligible or ill-formed targets are unspellable through the boundary — and, since 2026-08-05, this is also what makes an ordinary write incapable of closing a cycle in the retraction graph (§4; formal model ρA9, M3). **The test below is unchanged**; the row gains a role it always played, not an arm | retraction naming a note, a proposition, a run → refused; **a `route` arm naming a route absent from the named dataset's stamped basis → malformed**; a retraction naming an `instrument-certification` → **eligible** (added 2026-08-03, normative-contract §7.2 — its standing is read by scope derivation); raw-write each refused case and assert the audit reports it |
```

- **C10-a:** four raw-written refused shapes are reported by `audit_corpus`
  and `audit_world` as `retraction-target-invalid`.

The `instrument-certification` eligibility arm remains open for
`contract-cut`.

### Boundary invariants

- **BI-1:** node standing subtracts an assessment at the read.
- **BI-2:** the amended G8 clause: a retracted verification leaves the read
  set, in all three cases.
- **BI-3:** the enumeration is the view's and input-scoped, with matching and
  unrelated retractions present together.
- **BI-4:** an unreadable found retraction refuses.
- **BI-5:** a resolution disagreement refuses.

## 4. Accounting

**11 declaration units**, six against rows and five boundary invariants. C7
closes, C3 closes, and C10 stays part.

## 5. N2 and acceptance obligations

Acceptance has one arm per declaration unit. Each N2 sabotage has a byte-exact
`before` block copied from the tree in Task 7 and parsed after mutation.

| arm | module | sabotage | check |
|---|---|---|---|
| C7-a | `lineage.py` | `effective_routes` returns `basis.routes` (ignores `retired`) | acceptance C7-a |
| C7-b | `lineage.py` | the `"retired"` branch in `_closure` appends nothing | acceptance C7-b |
| C7-c | `corpus.py` | `CorpusWriter.retract` (line 2241 at baseline) also plans an update of the target dataset's `lineage-basis` facet dropping the retired route | acceptance C7-c |
| C3-a | `closure.py` | `"coverage": list(retractions.coverage)` → `"coverage": []` | acceptance C3-a (the isolated closure check fails) |
| C3-b | `evaluation.py` | the world enumeration's `coverage` is replaced by `f"{id}@{state}"` pairs from `view.stamp()` | acceptance C3-b |
| C10-a | `corpus.py` | the `retraction-target-invalid` `Finding` append is removed | acceptance C10-a |
| BI-1 | `evaluation.py` | `if node.id in subtracted: continue` (assessments) → `if False: continue` | acceptance BI-1 |
| BI-2 | `evaluation.py` | the same line in the verification loop | acceptance BI-2 |
| BI-3 | `evaluation.py` | the closure subset is replaced by every found retraction (decision 10's scoping dropped) | acceptance BI-3 (the unrelated-proposition half fails) |
| BI-4 | `evaluation.py` | the `except` that raises `RetractionUnreadable` swallows and `continue`s | acceptance BI-4 |
| BI-5 | `evaluation.py` | the disagreement comparison → `if False:` | acceptance BI-5 |

Both directions are required: the check passes on the real tree and fails
under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut32_acceptance.py",)` and the correction acceptance and
cut-33 N2 guard as its phase modules.

## 6. Second reader

Challenge the overstated-coverage attack. Verify that BI-1 and BI-2 exercise
`evaluate_over` without test-side filtering, and that C3-a's isolated closure
check changes only `retractions.coverage`.

## 7. Limitations

The epoch still resolves standing per corpus, so separating a
counter-retraction with `move` produces a disagreement that the evaluator
refuses; a world-wide derivation fold remains open. An unreadable retraction
anywhere in coverage refuses every evaluation over that epoch, while an absent
one yields `unavailable-corpus-absent`. Cross-corpus targets remain refused at
write. Routes without a stored identity cannot be retired. Corpus audit still
reads the stored basis without retirement. C10's `instrument-certification`
arm remains with `contract-cut`; C8 and C9 remain for slice 2.
