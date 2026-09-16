# Correction remainder, slice 1 — standing reaches the evaluator

**Date:** 2026-09-16
**Status:** draft, under review
**Boundary:** `correction-remainder` (`beliefs-aa27da`), the mutation lane's only open boundary; slice 1 of 2
**Lane:** `mutation`, worktree `.worktrees/correction-remainder`
**Sources:** `../../designs/2026-08-03-correction-lifecycle-design.md` (§3, §4, §6, §7a, C3, C7, C10),
`../../designs/2026-08-19-family-adapters-design.md` (§3.3, §4.3, §7.2),
`../../designs/2026-08-19-conformance-cut-5.md` (the C3, C7 and C10 splits),
`../../designs/2026-08-02-world-addressing-design.md` (§5, the enumeration and the receipt split),
`../../designs/2026-08-20-world-index-slice-2-design.md` (§7.4–§7.6),
`../../designs/2026-09-03-world-changing-families-design.md` (`move`, cut 16),
`../../designs/2026-09-12-composite-claims-design.md` (limitation 16),
`../../plans/2026-09-16-conformance-cut-32-results.md` (§3.4 Important 3; the boundary's inherited findings),
`../../plans/2026-08-29-implementation-roadmap.md` (tier 1 row 1, Appendix B, concurrency rules)
**Measured against:** `main` at `25ab84c`

## 1. What this slice is

The baseline below describes `main` at `25ab84c` before implementation.

The correction lifecycle's carrier landed at cut 5: the `retraction` kind with
its two target arms, the write boundary's eligibility and resolution checks
(`CorpusWriter._resolve_retraction_target`), the corpus-local standing fold
(`corpus.standing_in_local_view`, sibling-aware, cycle-refusing), and the
corpus check's `retraction-target-invalid` and `retraction-cycle` findings.
Cut 7 gave the world index a **retraction enumeration** — every retraction
address with its per-corpus resolution, `upheld` or `overturned`, under the
epoch's coverage declaration — and a retraction-discovery map beside it. The
belief input closure has carried a `RetractionEnumeration` member since cut 5
(`closure.py`), and the evaluator declares every found retraction as a read
(`EvaluationInputs.declared_refs`).

What no cut built is the subtraction. `evaluation.gather` reads every stored
assessment and every stored verification for a proposition whether or not a
standing retraction names it; `belief.evaluate` and `verification.lifecycle_state`
never consult a retraction; and the enumeration in the closure is a
**caller-supplied** member of `SuppliedContext` — the reproduction driver
supplies `found=()` — so the digest records whatever the caller declared
rather than what the corpus holds. Cut 5's C4, C5 and C6 checks filter the
records *inside the test* with `standing_in_local_view` and then call
`evaluate`; `verification.py`'s module docstring records the amended G8
definition's retraction clause as "deferred with the C group"; cut 32's
results record states the consequence for the composite reading: "an
assessment a standing retraction names contributes a term exactly as it
contributes to belief" (limitation 16 there). Route retirement (C7) has no
evaluator: `lineage.py` walks every stored route, and nothing reads a
`route`-arm retraction after the write boundary admits it.

This slice makes standing a property of the read. The enumeration is
**derived** from the view the evaluator reads — the bound epoch's member for a
world read, the corpus's own fold for a corpus-local read — never supplied;
every found retraction is dereferenced through the same view and the
standing fold is recomputed over what it names; a node-arm target of a
standing retraction leaves the read set before it is decoded; a route-arm
target retires its route, and the lineage walk certifies over the survivors.
Coverage and relocation then behave as C3 states — because the enumeration
carries its coverage and nothing about a state identity — and the audit
reports the refused shapes a raw write can produce (C10).

Rows read: **C7** in full; **C3**'s two deferred clauses, closing the row;
**C10**'s audit arm, leaving the row partial on its `instrument-certification`
arm, which `contract-cut` owns. The amended G8 clause lands as a boundary
invariant rather than a row: G8 closed at cut 5 on its positive retraction
arms and Appendix B lists no remainder for it, so the docstring's bound is
discharged and no row moves. Slice 2 takes C8 and C9 (§12).

## 2. Decisions

1. **The enumeration is derived at the read, never supplied.**
   `SuppliedContext` loses `retractions`. A world read takes the enumeration
   the bound epoch published (`retraction-enumeration`, §7.6's projection); a
   corpus-local read computes it from the corpus with coverage
   `(corpus_id,)`. A member the caller could set to empty is a member the
   caller could use to declare retractions away, and the digest would then
   certify the declaration rather than the corpus. Rejected: keeping it
   supplied and checking it against the view — the check would need the
   derived value anyway, and a member that must equal a derived value is a
   derived value with a redundant argument.
2. **The producer snapshot identity stays supplied, and a world read checks
   it.** It has no local derivation (a corpus-local read has no epoch), so it
   stays the caller's declaration; a world read refuses a supplied identity
   that is not the bound epoch's (`ProducerSnapshotMismatch`). Slice 2 adds
   the retracted case.
3. **Standing is recomputed by the evaluator over what it dereferences, and
   must agree with what the enumeration recorded.** Every found retraction —
   upheld or overturned — is read through the view, its target resolved, the
   graph folded with the one shared fold (§3.2), and the result compared with
   the enumeration's resolutions; disagreement refuses. The epoch's resolution
   is computed per corpus at capture (`epoch._standing_retractions`); a
   `move` that separates a counter-retraction from the retraction it counters
   makes the two folds differ, and a digest whose recorded resolution the
   evaluator did not use would be a digest describing another evaluation.
   Rejected: trusting `upheld` alone — cheaper, and silently wrong in exactly
   that case.
4. **A retraction the evaluator cannot read refuses the evaluation.** A found
   retraction whose facet does not parse, whose target does not resolve
   exactly, whose target's content identity does not match, or whose route is
   absent from the stamped basis makes standing undecidable for every input
   it might name; the evaluator refuses (`RetractionUnreadable`) rather than
   guess. The audit is where the record is reported (`retraction-target-invalid`,
   already emitted); `delete` (cut 18) is the remedy. Precedent:
   `test_local_standing.py::test_stale_retraction_refuses_the_whole_evaluation`.
5. **Subtraction is read-set removal, before decoding.** An assessment or
   verification a standing retraction names is skipped where `gather`
   iterates — a lookup, not a value handed out — so it is neither traced nor
   declared, and the closure's assessment and verification members simply
   lack it. `belief.evaluate`, `admission`, `verification.active` and
   `lifecycle_state` are unchanged. The amended G8 definition therefore
   composes as: first the read set loses every retracted verification, then
   `active` is computed over what remains — so a retracted *resolution* no
   longer supersedes the failure it named, and the failure stands again. That
   is the fail-closed reading §7a intends ("retracting a false failing
   verification restores admission iff a standing passing one remains"); the
   other reading, in which a retracted superseder keeps clearing a failure,
   is the one the design forbids. Rejected: threading a subtracted set into
   `lifecycle_state` — the composite reading and every other caller of the
   admission function would need the set too, and the design's own words are
   "leaves the read set".
6. **Route retirement is applied to the supplied lineage snapshot by the
   evaluator, and projected.** `LineageSnapshot` gains `retired` (dataset →
   sorted retired route identities); the supplied snapshot carries it empty
   and `gather` fills it from the fold; the stored basis is untouched and the
   walk computes an **effective** tag over surviving routes — one survivor
   certifies over that route, two or more stay `conflict`, none is
   `lineage-incomplete` and therefore `not-certified`, never silently single.
   `retired` is a projected member of every dataset's basis, so a retirement
   moves the digest. Rejected: retiring inside `corpus.lineage_snapshot` —
   it is also the audit's and the verifier's snapshot, and their reading of a
   stamped basis is not this slice's question.
7. **A route's identity is the `identity` its stamped basis records.** The
   write boundary already refuses a `route` arm naming an identity the basis
   lacks; a route without one cannot be named and is never retired.
   `lineage.Route` gains `identity: str | None`, read from the stored route
   and used only for matching — the route projection is unchanged.
8. **One fold.** `epoch._standing_retractions` and `standing_in_local_view`
   each carry a copy of the graph fold; this slice names it once
   (`corpus.retraction_standing`) and both call it. The local one-at-a-time
   reading keeps its name and its target validation.
9. **Cross-corpus targets stay refused at the write boundary.** Family
   adapters §4.3's bound stands; this slice widens no write. The world read
   resolves a target through the epoch's address map, so a retraction and
   its target separated by `move` still read; only the counter-retraction
   split of decision 3 refuses, and it is named in §11.
10. **The four src-touching follow-ups ride.** `beliefs-0521da`,
    `beliefs-1dd03f`, `beliefs-010c6e` and `beliefs-b1245d` each say "lands
    with the next cut that re-runs the certified chain"; this is that cut.
    `beliefs-010c6e` (filter assessments by their `assesses` edge before
    decoding) lands in the same loop this slice rewrites. They are plan
    tasks, not rows, and add no declaration.

## 3. The enumeration, derived

### 3.1 Surfaces

`closure.RetractionEnumeration` is unchanged: `found` is sorted
`(ref, resolution)` pairs, `coverage` sorted corpus ids, both projected into
the digest as today.

**World read.** `WorldReadView` is opened over an epoch and already carries
its producers map; it gains the epoch's retraction enumeration and producer
snapshot identity, parsed once at `open_world_view` from the published
members (`derive.retraction_enumeration` over the enumeration document; the
producer receipt carrier's `subject_identity` for the snapshot) and exposed as `retraction_enumeration() -> RetractionEnumeration` and
`producer_snapshot_identity() -> str`. Nothing about the open changes:
the same lock, the same barrier, the same captures.

**Corpus-local read.** `ReadView` gains `corpus_id` (the manifest's, through
`world.load_manifest(root)`; a corpus without a readable manifest cannot
declare coverage and the read refuses with the loader's own refusal,
unchanged). `corpus.local_retraction_enumeration(view) ->
RetractionEnumeration` enumerates every stored retraction, validates its facet
(`_validated_retraction_facet`, as capture does), folds standing (§3.2) and
returns `found = sorted((id, "upheld" | "overturned"))`,
`coverage = (view.corpus_id,)`. A world address and a corpus-local id are the
same string (`epoch._captured_records` sets `address=node.id`), so the two
enumerations agree in their keys.

**`SuppliedContext`** keeps `snapshot`, `producer_snapshot_identity`,
`node_corpus`, `pins`; `retractions` is removed. `belief.SuppliedContext`
and every constructor site (tests, the reproduction driver's `context()`)
change together.

### 3.2 The fold

```python
def retraction_standing(
    view: ReadView | WorldReadView, facets: Mapping[str, Mapping[str, object]]
) -> Mapping[str, bool]
```

`facets` maps retraction id → validated retraction facet. Node-arm targets
are resolved through `view.resolve(target["ref"])` and grouped; the graph is
`target → sorted retractions`; `_acyclic_postorder` orders it, refusing a
cycle with `RetractionCycleMalformed`; `standing[t] = not any(standing[r]
for r in graph[t])`. The mapping answers for every vertex — every target and
every retraction — and a retraction no other retraction names is standing.
`epoch._standing_retractions` becomes a call to it over the capture's
`ReadView`; `standing_in_local_view` builds `facets` with target validation
first (as today) and reads one answer from it. Behaviour of both callers is
unchanged; the arms of cut 5 and cut 7 that pin them are re-run at the cut
(§8.5).

## 4. Standing at the read — `evaluation.gather`

`gather` gains one step before it reads a single assessment, and applies
its result in three places.

**Dereference and fold.** With `enumeration` from §3.1:

```
facets = {}
for ref, recorded in enumeration.found:
    node = view.get(ref)                                   # traced as ("retraction", ref)
    facets[ref] = CorpusWriter._validated_retraction(node)
    CorpusWriter._resolve_retraction_target(node, view)    # exact resolution, content identity, route presence
standing = retraction_standing(view, facets)
```

A `MalformedRecord`, `RetractionTargetIneligible` or
`RetractionTargetUnresolvable` raised for a found ref is re-raised as
`RetractionUnreadable(ref, cause)` (decision 4). Then, for every found ref,
`("upheld" if standing[ref] else "overturned") == recorded` or the evaluation
refuses with `RetractionResolutionDisagreement` naming the ref and both
resolutions (decision 3). Every found retraction is traced: the evaluator
read it, and `declared_refs` already declares each one.

From the upheld retractions: `subtracted = {target["resolved"] for node
arms}` and `retired = {target["resolved"]: {route_identity, ...} for route
arms}`. The target's `resolved` member is exact by the resolution check
above, so it is a live id.

**Assessments.** In the assessment loop, after the kind test and the
`assesses`-edge filter `beliefs-010c6e` adds, and before
`stored.assessment_value` is called: `if node.id in subtracted: continue`.
The record is not decoded, not traced, not attributed, not declared.

**Verifications.** In the verification loop, before `stored.verification_value`:
`if node.id in subtracted: continue`. `lifecycle_state` then runs over the
standing verifications only; a superseder that was retracted no longer
appears in `supersedes`, so `active` recovers what it named.

**The lineage snapshot.** `context.snapshot.retired` must be empty — a caller
may not pre-retire, for the reason `node_corpus` must be supplied empty on a
world read — and `gather` returns `EvaluationInputs.snapshot =
lineage.retire(context.snapshot, retired)`, which copies the snapshot with
`retired` restricted to datasets that carry a basis (a route arm resolving
to a dataset outside the walk retires nothing the walk reads and is still a
projected member). The rest of `gather` — runs, observed facets, the claim,
`consulted` — reads the filtered assessment set as today.

**Datasets and runs** are not eligible targets (design §4); the loops that
read them are unchanged.

**`EvaluationInputs`** is built with `retractions=enumeration` and
`producer_snapshot_identity=context.producer_snapshot_identity`, the latter
refused on a world read when it differs from
`view.producer_snapshot_identity()` (`ProducerSnapshotMismatch`, decision 2).
`declared_refs` and `closure()` are unchanged in shape.

**The composite reading** (`composite.read_composite`) calls
`evaluate_over_traced` per member and takes its admission from the same
`EvaluationInputs`; it inherits the subtraction with no change of its own.
Limitation 16 of the composite-claims design is discharged by this slice
and that design gains a dated note saying so (§9).

## 5. Route retirement — `lineage.py`

- `Route` gains `identity: str | None`, filled by `corpus.lineage_snapshot`
  from the stored route's `identity` key (`None` when absent). It is not a
  member of `_route_projection`.
- `LineageSnapshot` gains `retired: Mapping[str, tuple[str, ...]]`, default
  empty, frozen like the other maps; each value sorted and distinct
  (`MalformedSnapshot` otherwise).
- `retire(snapshot, retired) -> LineageSnapshot` copies with `retired` set.
- `effective_routes(snapshot, dataset) -> tuple[Route, ...]` is the basis's
  routes minus those whose `identity` is in `retired[dataset]`;
  `effective_tag(snapshot, dataset)` is `"conflict"` for two or more,
  `"single"` for one, `"retired"` for none. A stored `conflict` with one
  survivor is effectively single; a stored `single` whose route is retired is
  effectively retired.
- `_closure` decides on the effective tag: `"conflict"` → `lineage-divergent`
  on the tag alone; `"retired"` → `lineage-incomplete`, and the walk does
  not continue through that dataset; `"single"` → walk the survivor's
  resolved ancestor and run `divergence_state`.
- `divergence_state` is defined against the effective single route:
  `BasisTagMismatch` when the effective tag is not `"single"`, and the
  comparison runs against the surviving route.
- `snapshot_projection` adds, per dataset, `"retired": [...]` (always present,
  sorted) beside `tag` and `routes`, and the `divergence` entry becomes
  `"divergent"` for effective `conflict`, `"incomplete"` for effective
  `retired`, else `divergence_state`. Every existing digest moves by the new
  key; the reproduction re-run records the transition (§10).
- `certify` is unchanged; it reads the walk.

C7's three clauses follow: retire one of two conflicting routes → the
effective basis is single over the survivor and, complete and undiverged,
certifies; retire both → `lineage-incomplete` → `not-certified`; the stored
`lineage-basis` facet is never written by `retract` (it writes one record)
and the test asserts the dataset's bytes and content identity before and
after.

## 6. Coverage and relocation — C3's deferred clauses

Both follow from §3 and need no code beyond it; they are stated here because
they are frozen text and the cut selects them.

**Uncovered corpus.** A world read enumerates retractions from the bound
epoch, and the epoch captured its declared coverage and nothing else. A
standing retraction held in a registered corpus the epoch does not cover is
not in `found`, subtracts nothing, and moves no digest; the coverage
declaration is a digest member (`closure.py`, unchanged), so widening
coverage to that corpus and rebuilding moves the digest even before the
retraction is applied. The fixture is two corpora holding **replicas** of one
assessment (equal content identity, equal address): the retraction is
written in the uncovered corpus against its replica; the covered corpus's
replica is read unretracted. After the widening rebuild the retraction is
found, its target resolves through the world address map to the one address
both replicas share, and the covered replica leaves the read set.

**Corpus move.** `move` (cut 16) relocates a record between corpora, changing
both corpus-state identities and neither the record's address nor any
content identity. Moving the retraction's *target* from covered corpus A to
covered corpus B and rebuilding: `found` is the same pairs (the retraction's
address and its per-corpus resolution are unchanged), `coverage` is the
same ids, the target resolves in B through the address map, and the digest
is unchanged; the new epoch's receipts record B's and A's new states. Moving
the *retraction* instead reads the same way. What is not exercised — the
counter-retraction split — is §11's limitation and decision 3's refusal, and
the test for the refusal is in §8.1.

## 7. The audit — C10's audit arm

`corpus_check` already emits `retraction-target-invalid` when
`_resolve_retraction_target` refuses a stored retraction, and `audit_corpus`
(through `corpus_check`) and `audit_world` (through `_record_findings` over
the captured check view) both surface it. The arm is declared and tested, not
built: raw-write, past the boundary, a retraction naming a `note`, a
`proposition`, a `run`, and one naming a route absent from its dataset's
stamped basis; assert each is reported by `audit_corpus` and by `audit_world`
with that code and the offending record's ref. The ineligible-kind refusal
text and the absent-route text are the boundary's own, unchanged.

The positive `instrument-certification` eligibility arm stays with
`contract-cut`: the kind has no stored definition
(`CONTRACT.yaml` declares it empty), and eligibility of a kind that cannot be
minted is that cut's question.

## 8. Testing and the cut

### 8.1 Unit

`python/tests/test_standing_read.py` (new):

- a corpus-local `gather` over a corpus with a retracted supporting
  assessment: the assessment is absent from `EvaluationInputs.assessments`,
  from `read_trace`, from `declared_refs()`; the retraction is present in
  `read_trace` and `retractions.found` carries `(ref, "upheld")`;
- counter-retract it: the assessment returns, `found` carries both refs with
  `overturned` and `upheld`, and the three closure digests are pairwise
  distinct (C5's shape, now through `gather`);
- a retracted **failing** verification whose target assessment has a standing
  clean-environment pass: `admission` over the gathered inputs is
  `admitted`; retract the pass instead: `not-admitted`; a retracted
  **resolution** (a verification that superseded a failure): the failure is
  active again and admission is `invalidated`;
- `SuppliedContext(retractions=...)` is a `TypeError` (the member is gone);
  a supplied `LineageSnapshot` with non-empty `retired` refuses;
- a found retraction whose target ref was raw-edited to a missing record →
  `RetractionUnreadable`; one whose stored `content_identity` was raw-edited
  → `RetractionUnreadable`; a raw-written retraction facet missing `grounds`
  → `RetractionUnreadable` (the cause is the boundary's own message);
- `local_retraction_enumeration` over a corpus with no retractions is
  `found=()`, `coverage=(corpus_id,)`; over a manifest-less corpus root
  refuses.

`python/tests/test_lineage.py` (extended):

- `Basis` construction is unchanged; `effective_tag` over a `conflict` with
  one retired route is `single`, with both retired is `retired`; over a
  `single` with its route retired is `retired`;
- `certify` over a two-route conflict: `not-certified` with
  `lineage-divergent`; retire one → `independent` (disjoint fixture) and no
  finding; retire both → `not-certified` with `lineage-incomplete` and no
  `lineage-divergent`;
- `divergence_state` runs against the survivor: a producer whose transforms
  match the retired route and differ from the survivor's is `divergent`;
- `snapshot_projection` carries `retired` per dataset and the digest of a
  snapshot with one retired route differs from the same snapshot with none;
- `retire` refuses an unsorted or duplicated identity tuple.

`python/tests/test_world_standing.py` (new, world fixture):

- a world read over an epoch whose covered corpus holds a retracted
  assessment: `gather` subtracts it; the enumeration is the epoch's member,
  byte for byte the same `found` pairs as `derive.retraction_enumeration`
  parses; `SuppliedContext.producer_snapshot_identity` equal to the epoch's
  passes and any other string refuses `ProducerSnapshotMismatch`;
- C3 uncovered: the replica fixture of §6, digest unchanged, coverage in the
  projection, digest moved by the widening rebuild;
- C3 move: the target moved between covered corpora, digest unchanged,
  receipt states changed;
- the split: retraction R in A targeting X in A, counter-retraction C in A
  targeting R, then `move` C to B and rebuild — the epoch records R `upheld`
  and C `upheld`; `gather` folds R `overturned` and refuses
  `RetractionResolutionDisagreement` naming R;
- a corpus-local read of the same corpus before the move folds R
  `overturned`, and the world read before the move agrees.

`python/tests/test_retract.py` (extended): a retraction of a stamped route
leaves the dataset's bytes and `stored_semantic_hash` unchanged (C7's
preservation clause, asserted at the write).

`python/tests/test_composite_reading.py` (extended): a member whose only
supporting assessment is retracted reads `no-belief` for that member through
`read_composite` with no test-side filtering.

`python/tests/test_local_standing.py`, `test_world_build.py`: unchanged in
assertion; `standing_in_local_view` and `_standing_retractions` now call the
shared fold and the existing tests pin that nothing moved.

### 8.2 Acceptance

`python/tests/acceptance/test_correction_acceptance.py` (new), on the
certified tuple through the durable writer, one check per selected clause:

- **C7-a** conflict of two routes, retire one through `retract` (route arm),
  `evaluate_over` certifies over the survivor (the `Belief` carries
  `independent` where the fixture's roots are disjoint);
- **C7-b** retire the second: `not-certified`, finding `lineage-incomplete`;
- **C7-c** the dataset's stored basis facet is byte-identical throughout, and
  the retraction operation writes exactly one record;
- **C3-a** uncovered-corpus replica: digest unchanged; widening moves it
  (§6);
- **C3-b** in-coverage move: digest unchanged, receipts record the new
  states;
- **C10-a** the four raw-written refused shapes, reported by `audit_corpus`
  and `audit_world` as `retraction-target-invalid`;
- **BI-1** node standing subtracts at the read: retract a supporting
  assessment, `evaluate_over` moves from the baseline through the same rule
  (no test-side filter);
- **BI-2** the amended G8 clause: the three verification cases of §8.1
  through `evaluate_over` and `admission`;
- **BI-3** the enumeration is the view's: a `SuppliedContext` cannot carry
  one, and a world read's closure carries the epoch's member;
- **BI-4** an unreadable found retraction refuses (`RetractionUnreadable`);
- **BI-5** a resolution disagreement refuses.

### 8.3 N2 sabotages

`python/tests/n2_arms_cut33.py`, one `Arm` per clause above; every `before`
string occurs exactly once in its module at freeze, and a mutated module is
`ast.parse`d (cut 31's guard, lifted into the shared audit by
`beliefs-1b0827` if it lands first, else carried per-cut as cut 31 did).

| arm | module | sabotage | check |
|---|---|---|---|
| C7-a | `lineage.py` | `effective_routes` returns `basis.routes` (ignores `retired`) | acceptance C7-a |
| C7-b | `lineage.py` | the `"retired"` branch in `_closure` appends nothing | acceptance C7-b |
| C7-c | `adapter.py` | `retract` also rewrites the target dataset's `lineage-basis` facet dropping the retired route | acceptance C7-c |
| C3-a | `closure.py` | `"coverage": list(retractions.coverage)` → `"coverage": []` | acceptance C3-a (the widening half fails) |
| C3-b | `evaluation.py` | the world enumeration's `coverage` is replaced by `f"{id}@{state}"` pairs from `view.stamp()` | acceptance C3-b |
| C10-a | `corpus.py` | the `retraction-target-invalid` `Finding` append is removed | acceptance C10-a |
| BI-1 | `evaluation.py` | `if node.id in subtracted: continue` (assessments) → `if False: continue` | acceptance BI-1 |
| BI-2 | `evaluation.py` | the same line in the verification loop | acceptance BI-2 |
| BI-3 | `evaluation.py` | `enumeration` replaced by `RetractionEnumeration((), enumeration.coverage)` | acceptance BI-3 |
| BI-4 | `evaluation.py` | the `except` that raises `RetractionUnreadable` swallows and `continue`s | acceptance BI-4 |
| BI-5 | `evaluation.py` | the disagreement comparison → `if False:` | acceptance BI-5 |

### 8.4 The cut

Conformance cut **33**, claimed at freeze (rule 1); no other worktree or
branch holds a cut-33 document at 2026-09-16 (scanned: `main`,
`design/correction-remainder`, `.worktrees/audio-baseline`). The runner
`python/tools/cut33_acceptance.py` names `cut32_acceptance` in
`PREFIX_RUNNERS` (rule 5) and carries
`PHASE_MODULES = ("test_correction_acceptance.py", "test_n2_cut33.py")`.
Declaration units: C7-a, C7-b, C7-c, C3-a, C3-b, C10-a, and BI-1–BI-5 —
eleven, six against rows and five boundary invariants. Frozen by dated
commit after review clears; invalidated frozen evidence is pinned and cited,
never edited.

### 8.5 Frozen evidence and live tests

Cut 5's `_STANDING_DISABLED` sabotage pins
`return standing.get(view.resolve(ref) or ref, True)` in `corpus.py`; the
refactor of §3.2 keeps that line verbatim in `standing_in_local_view` (it
reads the shared fold's answer) so the pinned string still occurs once. Cut
7's arms over `epoch._standing_retractions` are checked the same way before
the freeze; a pinned line the refactor moves is re-targeted in the live
guard, and the frozen cut document is not edited; the staleness probe's
baseline is the tree's own output at freeze, never an asserted `stale: []`.

The reproduction re-runs under this slice (§10) and every digest it pins
moves with the `retired` key; the record's transition section states that.

## 9. Shared files, under roadmap concurrency rule 3

`errors.py` (`RetractionUnreadable`, `RetractionResolutionDisagreement`,
`ProducerSnapshotMismatch`), `python/tests/test_designs_corpus.py`, the
ledger, the roadmap and the guide index, as every lane. Beyond those this
slice rewrites `evaluation.py`, `belief.py` (`SuppliedContext`), `closure.py`
(no change in shape; named because C3-a's sabotage lands there), `corpus.py`
(the fold, `local_retraction_enumeration`, `ReadView.corpus_id`,
`lineage_snapshot`'s route identity), `lineage.py`, `verification.py`
(docstring only), `world/view.py`, `world/epoch.py` (the fold call),
`composite.py` and `audit.py` (riders), `estimand.py`/`decode.py`/`spec.py`
(rider `beliefs-1dd03f`), the reproduction driver's `belief.py`, and the
composite-claims design (a dated note under its limitation 16). No lane is
open beside this one; the surfaces are named so the next lane's design can
name them back.

## 10. The reproduction

Step 8 and step 10a of the reproduction driver build `SuppliedContext`
without `retractions`; the corpus-local enumeration is derived (the mm30
corpus holds no retraction, so `found=()` and `coverage=(corpus_id,)`, now
computed rather than declared). The re-run reaches the same evaluator answer
over the same data; every pinned closure digest moves by the `retired` key
and the derived coverage, and §12 of `../../designs/2026-09-05-mm30-reproduction.md`
records the transition as §10 and §11 did for cuts 31 and 32. The cut-32
corpus state is moved aside to `.work/reproduction/mm30.cut32`, never
deleted.

## 11. Limitations and open questions this slice files

1. **The epoch's resolution is per corpus.** `epoch._standing_retractions`
   folds each corpus alone, so a counter-retraction `move`d away from the
   retraction it counters is `upheld` in its new corpus and the retraction it
   counters is `upheld` in the old one. The evaluator refuses that state
   (decision 3) rather than compute a wrong standing. The remedy is a
   world-wide fold at **derivation** rather than capture — a new version of
   the `retraction-enumeration` rule, its fixtures and its receipt identity —
   which is slice 2's or `contract-cut`'s to schedule; filed as an idea at
   the cut.
2. **An unreadable retraction anywhere in coverage refuses every evaluation
   over that epoch.** Fail-closed by decision 4; the audit names the record,
   `delete` removes it, a rebuild publishes over the corrected corpus. A
   narrower refusal (only when the unreadable retraction could name this
   closure) would need the target it cannot read.
3. **Cross-corpus retraction targets are still refused at the write.** The
   world read resolves them; the write boundary does not mint them. Family
   adapters §4.3's bound; no row.
4. **Routes without a stored `identity` cannot be retired.** The stamped
   basis's route identity is authored by whatever mints the basis; the
   kernel's `production.StampedBasis` mints none. C10's absent-route refusal
   already covers the write; the read follows it.
5. **The audit's and the verifier's lineage reading ignores retirement.**
   `corpus.lineage_snapshot` still returns `retired` empty, and
   `check_lineage_basis` and `world/verify.py` read the stored basis as
   today. Retirement is a belief-input fact in this slice; whether an audit
   should report a certification that retirement would change is filed as
   an idea.
6. **The instrument-certification eligibility arm of C10** stays with
   `contract-cut` (§7).
7. **The snapshot target** — C8, C9 — is slice 2 (§12).

## 12. Slice 2, stated so the split is visible

Slice 2 gives the retraction a third target arm, **`snapshot`**, naming an
epoch subject by kind (`producer`) and subject identity, resolvable at
authoring iff a retained epoch carries it; `retracted` joins the receipt
outcomes (`derive.RECEIPT_OUTCOMES`) and the snapshot-state reduction;
`import_epoch` refuses a carrier whose producer snapshot is retracted before
any write; `audit_epochs` and `snapshot_state` report `retracted`; a
computation whose supplied `producer_snapshot_identity` is retracted refuses
(the check decision 2 places); narrowing is `build_epoch` under the narrower
coverage then `retract` naming the old identity with `successor` the new
one; and the mount negative is asserted against the managed holdings root.
Rows C8 and C9; the boundary closes with it. A stored `producer-snapshot`
corpus kind is rejected there for the reason §1 gives: the epoch is the
derivation boundary world §5 requires, and a second representation of the
same derived input would be an authored one with a hash on it.

## 13. Task linkage

`beliefs-aa27da` is the boundary and carries `--spec
correction-remainder-slice-1` for this document; the implementation plan
attaches to a slice-1 child task, whose `### Task N:` headings become its
step children with explicit complexity and `--process direct`. The four
riders (`beliefs-0521da`, `beliefs-1dd03f`, `beliefs-010c6e`,
`beliefs-b1245d`) are reparented under the slice-1 task and closed by the
commits that land them. Slice 2 is a second child task, filed at this
slice's freeze with §12 as its body. The idea tasks of §11 items 1 and 5 are
filed at the cut.

## 14. Review log

- 2026-09-16 — drafted against `main` at `25ab84c`; not yet reviewed.
