# Conformance cut 33 — results

**Cut:** `../designs/2026-09-16-conformance-cut-33.md`
**Freeze:** `23f8a213737ae053c2a7715779e033c5802e20df`; SHA-256 `636b9b253507ad7f5eb4bfcdce560b7efe708f0b690bfc027415b7c16301a9b6`
**Declaration:** `python/tests/n2_arms_cut33.py`; SHA-256 `abf0e8289065634c4d355e080b716fbfeb4d7c2f276c0411b01a48bc11c7569d`
**Subject:** correction-remainder slice 1 — standing reaches the evaluator at the read
**Design:** `../superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md`
**Plan:** `../superpowers/plans/2026-09-16-correction-remainder-slice-1.md`
**Discharged:** 2026-09-17 on `design/correction-remainder`, through `d4d6432`
**Runner:** `python/tools/cut33_acceptance.py`

## 1. What ran

The certified runner exported cut roots 4–33 to the certified cut-33 root and
the reproduction root to the retained mm30 corpus, then ran the complete prefix
through cut 32 followed by cut 33. It exited **0**. Its final declaration line,
verbatim, was:

```text
declared arms: 11 (= 11 declaration units; 11 guarantee rows)
```

The runner's last phrase is its inherited accounting label. The eleven items
are declaration units: C7-a, C7-b, C7-c, C3-a, C3-b, C10-a and BI-1–BI-5.
Five are boundary-invariant units rather than guarantee rows. At row level this
cut closes C7 and C3 and reads only C10's audit arm; C10 remains partial.

Cut 33's own phases passed:

```text
[cut33 phase 2/3] test_correction_acceptance.py
11 passed in 54.25s
[cut33 phase 3/3] test_n2_cut33.py
10 passed in 24.57s
```

All earlier live acceptance phases through cut 32 passed. The five cut-33
source files were byte-identical before and after the chain. The later explicit
argument correction in the C10 test helper fixed Ruff B008 without changing
production, prior tests, declarations or frozen pins. The controller therefore
retained the successful unchanged-prefix evidence and required the final cut-33
acceptance and guard plus the full repository gate. That final focused run was:

```text
21 passed in 79.09s (0:01:19)
```

The final full gate ran after that helper correction and after the two-line
empty-CUT10 test-precondition correction described in §3.2. It exited **0**.
The two test summary lines were:

```text
4997 passed, 1 skipped in 1135.85s (0:18:55)
```

```text
      Tests  155 passed (155)
```

All static checks passed: Ruff, Pyright with zero errors and warnings,
TypeScript typecheck, Biome, and `tasks check` with zero errors and warnings.
The one Python skip is intentional and is not a capability waiver:
`tests/test_composite.py:119`, where the testing fixture admits only the causal
layer and the deferred layer arm is exercised by the biology fixture in
`test_composite_boundary`. Seven TypeScript files passed. No capability refusal
or waiver occurred.

The eleven baselines all reported **resolved**, and every corresponding
mutation reported **sound**. No unit was stale, vacuous, mixed or uncollected.

| declaration unit | baseline | mutation | guarantee-row effect |
|---|---|---|---|
| C7-a | resolved | sound | C7 closes |
| C7-b | resolved | sound | C7 closes |
| C7-c | resolved | sound | C7 closes |
| C3-a | resolved | sound | C3 closes |
| C3-b | resolved | sound | C3 closes |
| C10-a | resolved | sound | C10 audit arm read; row stays partial |
| BI-1 | resolved | sound | boundary invariant |
| BI-2 | resolved | sound | boundary invariant |
| BI-3 | resolved | sound | boundary invariant |
| BI-4 | resolved | sound | boundary invariant |
| BI-5 | resolved | sound | boundary invariant |

**Staleness evidence.** The pre-implementation probe measured the repository's
existing state rather than assuming zero drift: 28 cut-5 arms had seven stale
pins (G7[2], G7[4], M5[5], T2[10], T2[11], C1[17], C2[18]), while all 48 cut-7
arms were current. Task 1 restored the exact seven cut-5 source spellings after
formatting moved them. Later live guards followed measured implementation
movement: cut 16 R23c, cut 18 W16 and M1, cut 23 S5e, cut 32 U4-a and U6-b. No
frozen declaration changed. Task 7 required no new retarget, and the final
staleness/freeze check passed 16 tests in 3.32 seconds alongside the fallback
regression.

## 2. Accounting

The cut carries **11 declaration units** and **11 one-mutation arms**. Six units
exercise clauses of three guarantee rows and five exercise read-boundary
invariants. C7 closes in full, C3 closes in full, and C10 stays partial only on
its `instrument-certification` eligibility arm, owned by `contract-cut`.

The global corpus is **175 of 216 guarantee rows closed, 41 open**. This is a
two-row increase from cut 32's 173: C7 and C3 close. C10 does not add a closed
row. `python/tools/roadmap_status.py` carries the cut-33 accounting and produces
the roadmap's Appendix A with C8 and C9 never selected and C10 part at cut 33.

The cut changes no grammar, kind or relation. `contract-cut` gains no dependency
from this slice. The base contract exact-set rider makes the already declared
sets executable as closed sets; it is an implementation correction, not a new
contract oracle.

## 3. Evidence

No prior frozen declaration or cut body changed. Cut 33's §§2–7 remain
byte-exact to the freeze object; only its status line changes at discharge.
The cut-33 declaration remains byte-exact at its pinned SHA-256. Historical
evidence in prior results records and the reproduction record is unchanged.

### 3.1 Corrections carried by the cut document

The frozen cut required no post-freeze supplement. Its selected units, homing,
second-reader challenge and limitations stand as written. Implementation
corrections and reviewed plan deviations are recorded here instead of rewriting
the frozen body.

### 3.2 Deviations from the plan, all reviewed and taken

- **Execution claims use 2026-09-17.** The design and plan filenames retain
  2026-09-16, but freeze and discharge happened on 2026-09-17.
- **Exact exceptions and direct receipt replacement replaced illustrative
  recipes.** Manifest absence expects `ManifestMissing`, and known receipt
  carriers use direct dataclass replacement. The boundary failures are more
  specific without widening behavior.
- **The supplied snapshot bounds the route scope.** The implementation follows
  the plan's explicit `snapshot.bases` algorithm; it does not infer a wider
  inspected world from the design's shorthand.
- **Fixture prerequisites were made real.** Task 1 seeds the referenced spec and
  run nodes; C7 supplies a real observed empirical ancestor; C3-b moves the
  destination's dataset, run and proposition prerequisites before the measured
  baseline; alternate histories share one logical corpus id while retaining
  real manifest writes.
- **New edge-first membership replaced invalid historical characterizations.**
  A divergent `assesses` edge no longer selects the assessment for the other
  proposition. Composite malformed-edge/pre-grammar tests and the live M1
  sabotage now exercise the actual membership path. Frozen declarations stay
  untouched.
- **Unreadable found references are one error boundary.** The absence probe and
  stale-index `nodes.RefError` lookup sit inside the `RetractionUnreadable`
  boundary, preserving the original cause. The required malformed BI-4 shapes
  still refuse during enumeration; a found-but-unindexed reference makes the
  declared gather sabotage non-vacuous.
- **The reproduction reused the existing corpus.** The answer is `NoBelief`, so
  there is no pinned digest to move and no successful contract requiring a
  recreated corpus. The explicit predecessor recorded by §11 was used after the
  host-dependent default path refused.
- **Two final test-only corrections were disclosed and rechecked.** Ruff B008
  rejected a function call in the C10 helper's default argument; the helper now
  takes that reference explicitly at the same callers. The first serial full
  suite then found that the empty-CUT10 fallback test left CUT12 and CUT13
  configured, so it had not established the repository-fallback precondition.
  The test now clears those two variables. Before that change the full suite
  reported **1 failed, 4996 passed, 1 skipped in 1125.09s**; the isolated RED was
  one failure in 0.07 seconds. The two-line fix changed no fixture policy or
  production selection, had no live or frozen pin, passed the focused fallback,
  staleness and freeze set (**16 passed in 3.32s**), and the final full gate then
  produced the green result in §1.

### 3.3 Limitations found at review

1. The epoch folds standing per corpus. A counter-retraction moved away from
   what it counters can leave both records upheld in separate corpora; the
   evaluator refuses the disagreement rather than computing the wrong standing.
   A world-wide fold at derivation remains open as `beliefs-c800ef`.
2. An unreadable retraction anywhere in coverage refuses every evaluation over
   that epoch. An absent retraction produces `unavailable-corpus-absent`. A
   narrower refusal would require reading the target that is unreadable.
3. Cross-corpus retraction targets remain refused at the write boundary even
   though the world read can resolve them.
4. A route without a stored identity cannot be retired.
5. Corpus audit reads the stored lineage basis and ignores retirement; whether
   it should report a retirement-sensitive certification is open as
   `beliefs-2d5ada`.
6. C10's `instrument-certification` eligibility arm stays with `contract-cut`.
7. The semantic-snapshot target, C8 and C9, stays with slice 2,
   `beliefs-d79ca4`.

The host's default work-root and predecessor paths remain host-dependent; the
certified runner and reproduction preflight use explicit existing roots. A
Pyright upgrade advisory appeared during the lane, but analysis was clean and
no dependency upgrade was requested. Neither is a behavioral remainder.

## 4. Reproduction measurement

The reproduction record's §12 ran `reproduction.rederive` on 2026-09-17 in a
fresh process against the existing cut-32 corpus. No contract succeeded, so the
corpus was neither recreated nor moved aside; the earlier retained corpora were
untouched.

The driver no longer supplies `SuppliedContext.retractions`. The evaluator
derives the full fold and then the input-scoped enumeration. This corpus holds
no retraction, so both were `found=()` with coverage containing the measured
corpus id `8b5d0c802677ee445e2b9d91ebf5d6a7`, byte-equal to the enumeration the
driver formerly supplied.

The fresh answer was
`NoBelief(reason="no-directional-outcome")`, equal to the recorded answer.
`NoBelief` carries no `belief_input_digest`, so there is no digest transition to
claim. State hash, top-level inventory and the 65-file corpus count were
unchanged. The measurement establishes supplied-to-derived equality for the
empty enumeration; it does not claim how an mm30 retraction or an epoch would
behave.

## 5. Remaining boundary

`correction-remainder` remains open for **C8 and C9** in slice 2,
`beliefs-d79ca4`: the snapshot target, `retracted` receipt/snapshot outcomes,
import and audit refusals, supplied producer-snapshot refusal, coverage
narrowing by successor snapshot plus retraction, and the mount negative.

**C10** remains partial on the `instrument-certification` eligibility arm,
owned by `contract-cut`. Its raw-written audit arm is complete here.

Two reviewed questions remain as ideas rather than hidden limitations:
`beliefs-c800ef` owns a world-wide standing fold at derivation, and
`beliefs-2d5ada` owns the question of retirement-sensitive certification in
audit. Neither changes the C8/C9 slice-2 scope.

## 6. Main integration

**Pending controller review and local merge.** The branch has not been merged
or pushed. After the controller's final whole-branch review, the reviewed plan
requires a local `--no-ff` merge to `main`, `just gate` on the merged tree, and
a follow-up commit recording the merge revision and merged-main verification
here. No merge commit or merged-main gate result is claimed by this record yet.

## 7. Execution rulings

Every `Ruling:` entry from the execution ledger, in chronological order:

- **Use actual execution dates for new freeze/discharge claims, retaining
  established document filenames.** Status headers are historical claims and
  execution is 2026-09-17. Cost if wrong: date text only.
- **Match manifest absence with `ManifestMissing` rather than the plan recipe's
  broad `Exception`; use direct dataclass replacement for known receipt
  carriers.** Exact failures make these checks meaningful. Cost if wrong: test
  adjustment.
- **Follow the explicit §4 scope algorithm over `snapshot.bases`, as the plan
  specifies.** Decision 10's inspected-set phrasing describes that supplied
  snapshot scope and avoids silently changing the reviewed closure contract.
  Cost if wrong: tighter route locality needs follow-up.
- **Record the reproduction correction in spec §14 and preserve the existing
  corpus.** The measured answer is `NoBelief` and carries no pinned digest.
  Cost if wrong: reproduction measurement would need repeating.
- **Close each step task in its implementation commit before closing the slice
  parent in Task 8.** The tasks CLI enforces children complete first.
  Cost if wrong: task bookkeeping correction.
- **Compare Task 1 staleness with measured pre-existing drift, not the plan's
  expected zero.** Successor live guards determine current evidence; the
  baseline already has seven stale cut-5 pins. Cost if wrong: guard evidence
  must be revisited before discharge.
- **Task 1 seeds prerequisite spec/run nodes using existing `test_retract`
  fixtures.** The plan assessment builder references `run:r1`, which the
  adopted empty corpus lacks, and changing profile cannot fix missing
  references. Cost if wrong: fixture setup adjustment. RED confirmed missing
  `RETRACTION_OVERTURNED` before source implementation.
- **Preserve the existing validator's generic malformed-retraction-facet
  message and change the illustrative grounds-substring assertion to that
  actual message; do not expand validator scope.** The spec requires the
  boundary's own cause and the generic validator message is already stable.
  Cost if wrong: missing-field diagnostics remain generic. Fix round 1 base
  `5fb3152`.
- **Task 4 replaces the malformed divergent-`assesses` fixture's old
  containment-violation expectation with edge-selection behavior.** Reviewed
  edge-first membership necessarily stops selecting an assessment whose edge
  names another proposition. Cost if wrong: historical characterization
  changes; valid-input P1–P9 remain protected. Carry live guard implications
  into the task.
- **Move C3-b target destination prerequisites before the compared baseline,
  then compare only target relocation.** Real move enforces destination
  run/dataset eligibility and digest invariance needs identical
  producer/contract inputs. Cost if wrong: relocation fixture requires further
  alignment.
- **Update composite malformed-edge/unrelated pre-grammar characterizations and
  live M1 sabotage for the new edge prefilter.** The reviewed membership filter
  intentionally prevents those old reads, so sabotage must bypass membership
  too. Cost if wrong: affected historical characterization or live arm needs
  revisiting; frozen declarations remain untouched.
- **Alternate-history digest fixtures use the same logical corpus id via a
  scoped replacement of `beliefs.corpus.secrets` during `adopt_manifest`,
  following existing coordination acceptance tests.** Derived coverage now
  exposes independently random ids, while coverage must remain in the digest;
  replacing the module reference avoids altering engine nonce generation.
  Cost if wrong: comparison fixture identities need revisiting; real manifest writes
  remain exercised.
- **Put the found-ref absence probe inside the unreadability boundary and
  include the specific nodes `RefError` lookup failure.** Decision 4 requires
  every found-but-unreadable ref to identify `RetractionUnreadable`, overriding
  the narrower illustrative plan catch. Cost if wrong: error classification
  changes on damaged or stale views; the original cause must remain intact.
- **Set `MM30_PREDECESSOR` to the existing predecessor location recorded by
  reproduction §11 after the default location refused as absent.** This
  preserves the same measured predecessor and certified-root check without
  recreating data. Cost if wrong: reproduction evidence must be rerun against
  the correct predecessor.
- **Add the found-but-unindexed real retraction case to BI-4 alongside the three
  required malformed shapes.** Those shapes refuse during local enumeration
  before the declared gather catch, so the extra case is needed to make its
  sabotage non-vacuous. Cost if wrong: BI-4 fixture or sabotage needs retargeting
  before discharge.
- **Give C7 run-a an additional real observed empirical ancestor alongside the
  conflicted derived dataset.** Controlled admission requires empirical
  observation, which the derived dataset itself cannot carry; both route
  ancestors remain held and assessment B disjoint. Cost if wrong: the fixture
  could mask the retirement effect, so assert actual full-root certification
  and `BELIEF_V1` 1→2 as well as surviving route projection.
- **After making the C10 test helper's ref argument explicit, retain the
  successful unchanged-prefix chain evidence and rerun final cut-33
  acceptance/guard plus the full hook.** Production, prior tests and frozen
  pins are unchanged, so repeating the 38-minute prefix adds no coverage.
  Cost if wrong: prefix evidence would need rerunning if the test-only correction
  affects it.
- **Make the empty-CUT10 fallback test clear CUT12 and CUT13 with
  `monkeypatch.delenv`.** `conftest` intentionally checks those configured
  alternatives before repository fallback, and all-root certified exports
  exposed an incomplete test precondition. Cost if wrong: fallback behavior
  coverage could narrow; fixture and capability policy remain unchanged and the
  final full gate must pass.
