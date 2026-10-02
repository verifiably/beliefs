# Belief acceptance before evidence and correction effects

**Date:** 2026-10-02  
**Status:** implemented and discharged at cut 45 on 2026-10-02; results: `../../plans/2026-10-02-conformance-cut-45-results.md`
**Review:** spec round 3 accepted revision `dc41764`; reviewer `claude-code/claude-opus-5-5`, forwarded by the user. Three nonblocking planning items are carried into the implementation plan.
**Task:** `beliefs-d9bc57`  
**Boundary:** `belief-acceptance`, discharged in the `world-read` lane
**Workspace (historical; removed after integration 2026-10-02):** .worktrees/acceptance-filter, branch `feat/acceptance-filter`
**Measured against:** main `676e2f8`; the worktree starts at `f5a8ac2`, which adds only the task claim  
**Cut:** 45, frozen at `4bec463` after the spec and implementation-plan reviews

## 1. Intent and scope

The user chose acceptance filtering, then publication attribution, then the
bounded N2 collection-preflight pilot. This is the first task's design.

Science commons milestone 1a needs installation B to hold, cite and reproduce
A's records without counting A's evidence until B accepts its provenance.
The same rule must apply to assessments, verifications and corrections before
they have any effect. The answer must state how evidence was selected.

The upstream requirement is Science's approved commons design, §9 and §11
(`science docs/specs/2026-09-30-science-commons-design.md`, task `sci-fe8522`);
`sci-13050a` depends on this task and `beliefs-f50596`. The latter supplies
publication attribution; it is not needed to prove this kernel mechanism
with supplied predicates. Science owns the provenance-world rules, accepted
worlds, publication bindings and pin authentication. Beliefs owns the timing
of selection and its effect on derivation.

Success means an excluded assessment cannot enter belief or poison an accepted
identity-equal assessment; an excluded verification cannot invalidate evidence
or suppress an accepted failure; and an excluded correction cannot change node,
route or snapshot standing. The selection statement and exclusions are available
to the consumer without claiming that the kernel authenticated the statement.

No Science implementation, publication-marker change, new trust store,
retraction-rule version, transport change or unrelated refactor is included.

## 2. Observed implementation

`evaluation.gather` is the shared corpus-backed resolver. Its world branch
first checks damage, absence and producer-snapshot standing. It then reads
the epoch's retraction enumeration, resolves the correction targets, folds
standing and subtracts node targets or retires routes. Only afterwards does
it select assessments and verifications by their relation edges.

`WorldReadView.snapshot_standing()` folds **all current captured records**
from the covered corpora, including post-epoch corrections not present in the
address map. Its cached answer is currently independent of a reader's policy.
Adding a filter only to the assessment loop would therefore be too late.

`belief.evaluate_traced` subsequently collapses assessment identities and
refuses facet-disagreeing twins before admission. The twins can have different
stored addresses (`assessment:<slug>`) while carrying one derived assessment
identity. The filter must use the stored address and run before this collapse.

`SuppliedContext` currently carries lineage, producer-snapshot identity,
attribution and pins. The three answer types carry no selection context.
`build_closure` digests the selected evidence, correction enumeration and
aggregation binding, but no acceptance statement.

The world address map is singular and refuses duplicate canonical locations.
That capture-integrity rule precedes this task and remains unconditional.
The identity-twin acceptance case uses distinct stored addresses; it does not
waive duplicate-location or uid-corruption checks.

Baseline: `just setup` succeeded; `just test-one tests/test_evaluation.py
tests/test_world_view.py tests/test_snapshot_retraction.py` passed, 119 tests
in 38.89 seconds on this host. No product code has changed.

## 3. Chosen approach and alternatives

**Choose one caller-supplied predicate paired with an immutable statement.**
Apply it in the existing gather and standing paths, then pass the selected
records to the existing pure evaluator. Reuse captured records, attribution,
canonical identity encoding and retraction folding.

Rejected: wrapping a read view with a generic filtered facade. Filtering
iteration alone leaves snapshot standing unfiltered; filtering resolution
also would hide the runs, datasets and targets needed to evaluate accepted
records. It introduces a second resolution contract at a sealed boundary.

Rejected: putting the commons trust algorithm in Beliefs. Beliefs lacks the
reader's accepted-world and authenticated-pin state. A kernel trust registry
would duplicate Science's policy and couple this task to publication attribution.

## 4. Public contract

### 4.1 Predicate and statement

Add a frozen `AcceptancePolicy` value beside the belief context types:

```python
AcceptancePolicy(
    counts: Callable[[str, str], bool],
    statement: str,
)
```

The callable receives `(corpus_id, canonical_stored_address)`. The address is
the record's live `node.id`, not an assessment identity, uid or deprecated
spelling. The constructor requires a callable, otherwise
`MalformedRecord("acceptance-predicate-not-callable")`. The result must be exactly
a `bool`; another return type raises `MalformedRecord("acceptance-result-not-bool")`.
Exceptions fail the call and never turn into acceptance or an unrestricted retry.

The statement must be an exact, nonempty `str`, otherwise the constructor raises
`MalformedRecord("acceptance-statement-not-text")`. Its encoding check is that
`v1.encode(statement)` succeeds; an encoding failure propagates the original
`IdentityError` subclass, including `LoneSurrogate`, without replacement text.
Science supplies its canonical policy document as that text, including the
verifier set, relevant pin sources and provenance information it needs to
explain exclusions. The kernel keeps this text unchanged and includes it in
the filtered closure. It does not interpret world ids, pins or trust branches.
Text is used because it is already immutable and the kernel does not need a
new policy schema or recursive freezing mechanism.

The caller must bind both fields to the same immutable policy/pin snapshot.
The kernel cannot prove a callable implements its statement, just as it cannot
authenticate other supplied execution evidence by description alone. A shared
statement with a stateful or dishonest callable is outside this guarantee.

`gather`, `evaluate_over` and `evaluate_over_traced` gain an optional keyword
`acceptance: AcceptancePolicy | None = None`; their private shared path forwards
it. `None` means the existing unrestricted selection. No settings lookup,
environment default, implicit accepted-world list or fallback supplies a policy.

### 4.2 Returned context

Add a frozen `AcceptanceContext` with:

- `statement: str`, the exact policy statement;
- `excluded: tuple[tuple[str, str], ...]`, sorted unique corpus/address pairs;
- `complete: bool`, whether all acceptance candidate scans and filtered standing
  folds finished. Completion does not assert that dependency reads or contract
  interpretation succeeded.

`EvaluationInputs` gains `acceptance: AcceptanceContext | None`. `SuppliedContext`
gains the same optional field so `_evaluate_over_inputs` can forward the computed
selection to the pure evaluator with its existing `replace` operation. `Belief`,
`NoBelief` and `Refused` gain the same optional field. Unrestricted calls leave
it unset and preserve their present results.

`gather` rejects any non-`None` incoming `context.acceptance`, with or without
an `AcceptancePolicy`, by raising `MalformedRecord("supplied-acceptance-context")`
before record iteration, resolution, standing or predicate invocation. It is
an output of this resolver, like world-derived `node_corpus`, never permission
to claim a selection ran. Only after gathering does `_evaluate_over_inputs`
copy the resolver's context into the context passed to the pure evaluator.

For a filtered call that completes gathering, every rejected evidence or
correction record encountered in the selection domain is listed, including
irrelevant evidence records. Science joins each corpus/address pair to the
origin information bound in its statement when rendering the upstream
world-attributed exclusion report. Holding corpora are not presented as
authenticated provenance worlds.

A returned answer before that completion boundary carries
`AcceptanceContext(statement, excluded=(), complete=False)`. Incomplete contexts
**always** have `excluded=()`; their constructor refuses a nonempty list with
`MalformedRecord("incomplete-acceptance-exclusions")`. Partially observed decisions
are not returned, so incomplete reports do not vary with scan order. The statement
uses the same validation as `AcceptancePolicy`. The corpus-backed wrapper's
binding-exactness guard still runs first and carries this incomplete context
on its returned refusal.

The completion boundary is after all evidence/correction candidate scans and
filtered standing folds, when the verification scan and correction scoping have
finished, before the claim lookup and late `consulted_contracts` walk. Public
`gather` and `_evaluate_over_inputs` share a private gather implementation with
invocation-owned state: the decision cache and the completed context. This lets
the wrapper preserve completion on a caught late error without rerunning the
predicate or attaching new fields to existing exception types. Public `gather`
continues to raise its existing errors; the state is not a new public argument.

| Outcome site | Acceptance context on a returned answer |
|---|---|
| Corpus-backed binding guard, caught error before the completion boundary, or `_absent_inputs` early return before evidence scans finish | Incomplete; `excluded=()` |
| `ContractDisagreement`, `ContractMismatch`, `FacetPayloadRefused` or `FacetUndeclared` raised by the late `consulted_contracts` walk and caught by the wrapper | Complete; full sorted exclusions; existing refusal reason |
| Other existing caught errors after the completion boundary, including a caught claim-decoding error | Complete; full sorted exclusions; existing refusal reason |
| Absence discovered by `absences(snapshot)` from a supplied lineage snapshot, or defensively in the run/dependency loop or claim lookup, with all candidate scans and folds subsequently completed | Complete; full sorted exclusions; `NoBelief("unavailable-corpus-absent", ...)` and `NotReached()` |
| Pure-evaluator Belief, NoBelief or Refused after a completed gather | Complete; full sorted exclusions |

An error not already caught by the wrapper still raises. If another refusal
occurs before a late absence answer can be produced, the existing refusal order
wins; the table does not turn an exception into an absence answer.

For world reads, genuinely absent covered corpora are caught by the initial
`view.absent()` preflight. Later run/claim absence branches are defensive;
`LineageSnapshot.not_present` supplies a reachable late absence without changing
the captured view. The wrapper creates its invocation state before its binding
guard so that refusal can carry the initial empty incomplete report without reads.

A pure evaluator may consume a complete context with already selected `Records`;
it lacks corpus/address information sufficient to run the predicate itself.
With a valid aggregation binding and `context.acceptance.complete=False`,
`evaluate_traced` returns
`(Refused("acceptance-selection-incomplete", acceptance=context.acceptance), NotReached())`
immediately after step 1's binding-exactness guard, before step 2's consulted
walk or any record-pool reads. An inexact binding retains precedence and its
existing refusal reason, with the supplied acceptance context unchanged.
`evaluate` remains the first projection of this path.

The filtered corpus-backed path is the guaranteed selector. Direct construction
of `Records` or `AcceptanceContext` remains supplied input, not kernel evidence
that filtering ran. No extra trusted wrapper or capability token is introduced.

## 5. Selection and reading order

### 5.1 The selection domain

Acceptance applies to stored `assessment`, `verification` and `retraction`
records. Superseding verifications and counter-retractions are covered by their
record kinds. Source assertions are already belief-inert.

Runs, analysis specs, propositions, datasets and profile contracts remain
readable dependencies of accepted evidence. Their presence is not an endorsement
of their author's assessments. The predicate is not a general read-access gate.
For example, an accepted verification can check an accepted assessment whose
run observes a dataset held in a corpus contributing no accepted assessments.

For a world view, obtain the holding corpus together with each record from the
existing located capture (`WorldReadView._mapped_records`), before attribution
is collapsed to derived identities. For a local view, use `view.corpus_id` and
the stored address. For an explicit policy on a local view, preflight
`view.corpus_id` immediately after the context guards and before any record
iteration, reference resolution, standing, dependency reads or predicate call.
A missing manifest raises `ManifestMissing` from `load_manifest`; a malformed
manifest raises `ManifestMalformed`. The required manifest read itself is the
preflight, not an evidence read. Neither error invents a corpus identity.

The singular address map and uid uniqueness give this slice one holding corpus
per stored address. That implements Science §9.2's **any holding corpus** rule
for milestone 1a, where the holding set is a singleton. Distinct stored addresses
can still carry one assessment identity and get independent acceptance decisions.
Overlapping publications at milestone 1b (`beliefs-81367e`) must revisit this
contract: the predicate must be tried for every holding corpus before collapsing
an address, or an equivalent union must be computed. Choosing the first carrier
would not implement §9.2. This slice leaves the current duplicate-location refusal
in place and claims no overlap support.

Each gather call caches decisions by `(corpus_id, address)` and invokes the
predicate at most once for a candidate in that call. The same decision is
used by snapshot standing, ordinary corrections and evidence selection.
No decision is cached on a shared view or across calls. Changing policy and
re-evaluating the same view must change selection immediately.

Science §9.4 requires every excluded record, which justifies invoking the
predicate for every mapped assessment and verification and every correction
candidate, including the full captured correction set used by snapshot standing.
The cost is linear in that inventory even for a query matching little evidence.
Relation-based selection must not move ahead of the predicate to omit irrelevant
exclusions. Structural edge bookkeeping after a decision is allowed as §5.2
states; excluded facets are still not decoded.

### 5.2 Evidence

Decide acceptance before decoding an assessment or verification facet,
recording a semantic read, or selecting the semantic evidence pool. Rejected
malformed evidence therefore does not poison that pool; accepted malformed
evidence still refuses under the existing checks.

Assessment addresses have two different bookkeeping roles:

- `verification_targets`: every assessment whose structural `assesses` edge
  matches this proposition after reference resolution, whether accepted or
  rejected. Populate this set after its acceptance decision, without decoding
  rejected facets or claiming their identities.
- `visited`: only acceptance-surviving assessments whose edge matches, including
  those removed by a standing retraction as in the existing resolver. Rejected
  addresses never enter this set, attribution, semantic read trace or correction
  scope.

After a verification's own acceptance decision, its `verifies` edge qualifies
it for facet decoding if the resolved target belongs to `verification_targets`.
Then `_verification_selected(value, ids)` selects its declared assessment identity
against the accepted gathered identities exactly as now. Therefore an accepted
failure or pass naming rejected twin B's stored address still applies to accepted
twin A carrying the same identity. A verification of a rejected-only identity
does not enter the evidence pool. Rejected assessment facets are never read to
establish either case.

Keep the existing edge-qualified verification-address bookkeeping for accepted
verification records, including those subsequently removed by a standing
retraction; rejected verification addresses never enter `verification_ids`.
`verification_targets` is never unioned into
`scope = visited | verification_ids | set(snapshot.bases)`. In particular, a
correction targeting rejected twin B does not enter solely because B made an
accepted verification's edge eligible for identity matching. Predicate rejection
does not delete the structural address needed to locate that accepted verification.

The evaluator and `verification.active` see only surviving records. An excluded
superseder cannot remove an accepted failing verification. Identity-equal
assessments collapse only after rejected copies have left the pool, and two
accepted facet-disagreeing twins still refuse.

Derive `node_corpus` and consulted-contract membership from the records and
dependencies actually read. A rejected assessment does not contribute its
corpus's pins to an otherwise nonempty accepted evidence closure. The existing
base-contract walk for an empty pool is retained; this task does not waive
profile interpretation or root validation.

### 5.3 Ordinary corrections and recorded resolutions

For local reads, allow `local_retraction_enumeration` to use the gather decision
callable before validating correction facets or folding standing. The retained
facets form the correction graph; a rejected counter-retraction is absent from
that graph and cannot restore its target.

For world reads, the epoch's carried enumeration remains the authenticated
candidate inventory for mapped corrections; node/route effects are applied here,
and snapshot effects are judged by the live fold of §5.4. It is not replaced with
caller-supplied refs, and post-epoch ordinary corrections do not enter it.

For each enumerated ref, the order is:

1. `_absence_of(view, ref)` first. A recorded-but-absent corpus is an absence,
   before any predicate can exclude the record; damage propagates its refusal.
2. `canonical = view.resolve(ref)` and `corpus_id = view.corpus_of(ref)`.
   Resolve only the address here, without calling `get` or validating its facet.
   If a present enumerated ref does not resolve, raise
   `RetractionUnreadable(ref, ...)` with the existing missing-ref error as cause.
3. Consult the cached decision for `(corpus_id, canonical)`; a deprecated
   enumeration spelling therefore never reaches the predicate.
4. Only for a survivor, fetch and validate the correction and resolve/check its
   target. Target absence retains the existing absence answer. A target lookup
   can establish an accepted correction's integrity without accepting that target
   as evidence or making it a standing graph vertex.

There is **no stored per-corpus resolution datum**. For a filtered evaluation,
compute the local comparison oracle explicitly:

- `M_c` is the record set `view._held[c]`: present epoch-mapped records only.
  It excludes unmapped records from `view._captured_views[c]`.
- Its resolver returns the held node's canonical `id` only when
  `view._recorded[ref] == (c, uid)` and `uid` is held in `M_c`; otherwise `None`.
  Build the existing `_CapturedCheckView` over those mapped nodes with that
  restricted reference table. Do not add new redirects from drift records or
  from current `deprecated_ids` absent from the epoch's address map.
- `F_c` contains only validated, acceptance-surviving facets from the carried
  inventory whose records belong to corpus `c`, keyed by canonical address.
  It contains no post-epoch correction and no rejected correction facet.
- `L_c = retraction_standing(M_c_resolver, F_c)` is the filtered per-corpus fold.
  `W = retraction_standing(view, union(F_c))` is the filtered world-wide fold.
  Compare `L_c[ref]` with `W[ref]` for **every** surviving inventoried correction.
  A difference raises `RetractionResolutionDisagreement`; exclusions elsewhere
  never disable this split-corpus check. Apply effects and scope resolutions from
  `W` only after these comparisons pass.

Filtering can legitimately change a survivor from `overturned` to `upheld`, so
receipt fidelity is checked **per surviving ref**, not disabled globally:

- Preserve the packaged `retraction-discovery-map.yaml` with the opened view.
  Its `{target, retractions}` entries describe the original inventoried targets;
  this is existing epoch data, not new resolution metadata or a new rule version.
  Derive its in-corpus counter graph using the restricted resolver above. An
  entry contributes `r -> k` when a listed correction `k` and the resolved
  `target = r` are both inventoried corrections held in corpus `c`.
- For each surviving ref `r`, let `C_c(r)` be the inventoried corrections reachable
  from `r` along these target-to-counter edges. This includes rejected
  counters, without reading or validating their current facets. Traverse with a
  visited-ref set; this dependency query does not validate rejected records.
  Cycles in a surviving standing fold retain `RetractionCycleMalformed`.
- If `C_c(r)` contains no excluded record, compare the receipt's resolution for
  `r` with `L_c[r]` and raise `RetractionResolutionDisagreement` on a mismatch.
  A rejected correction outside this set cannot suppress the check. If it does
  contain an excluded record, omit **only that ref's** receipt comparison, since
  a filtered resolution may legitimately differ; the `L_c` versus `W` comparison
  still runs. Normalize receipt refs through the same resolver for these lookups.

This preserves all receipt comparisons for accept-all, and catches a corrupt
resolution for an unaffected survivor even when another chain has exclusions.
An excluded post-epoch snapshot-chain record is outside the original inventory
and cannot disable these receipt checks. `open_world_view`'s existing packaging
and carried-enumeration validation still run before any selection.

The per-corpus versus world-wide disagreement remains a refusal even when a
policy filters some unrelated correction. This is the existing split-corpus
limitation (`beliefs-c800ef`, research task `beliefs-ae33ff`), not permission to
change the shipped derivation rule or its receipt identity. Epoch publication,
audit and import continue to use their existing unfiltered semantics.

### 5.4 Snapshot corrections

Allow the snapshot-standing helper to receive an optional decision callable
that takes corpus id and canonical stored address. Filter correction vertices
before `_validated_retraction_facet`, any standing fold and chain-member
validation, including counter-retractions that reach a snapshot-arm root. A
rejected malformed retraction outside any snapshot chain is also skipped before
facet validation and cannot raise `RetractionUnreadable` from this fold.

`WorldReadView.snapshot_standing` forwards that callable over the same **full
captured records and full captured resolvers** it uses now (`_captured_views`).
This deliberately differs from the mapped-only ordinary comparison oracle in
§5.3: snapshot standing is live and must see post-epoch records. A filtered fold
is computed for that evaluation
and never stored in the view's policy-independent cache. The unrestricted cache
and its callers retain their present semantics.

This preserves the live-read obligation: post-epoch snapshot retractions and
their counters are subject to the predicate even though they have no epoch-map
entry. An excluded snapshot retraction cannot trigger `ProducerSnapshotRetracted`;
an excluded counter cannot restore an accepted snapshot retraction. Accepted
malformed chain members still refuse.

Epoch binding, damaged-carrier checks, absence, capture drift checks and uid/address
integrity remain unconditional. Acceptance selects evidence; it does not repair
or authorize reading a damaged world. A policy cannot conceal a missing covered
carrier by returning false for records the kernel cannot inspect.

## 6. Closure and recomputation

Extend `build_closure` with an optional acceptance-statement argument. When
present, include it as the `acceptance_policy` member. Forward the same statement
from `EvaluationInputs.closure` and from `belief.evaluate_traced`; both paths must
produce the same digest. An unrestricted call omits this member and keeps the
existing projection, rather than manufacturing a policy statement nobody supplied.

The selected assessments, verifications and scoped correction resolutions remain
the existing closure members. The statement distinguishes otherwise identical
selected evidence under different declared acceptance policies. The callable,
its object identity, and invocation order are not identity inputs.

For a filtered world evaluation, `history` is taken from the **filtered**
`SnapshotStanding.history` for the bound producer snapshot and is the history
unioned into `scoped.found`. Neither the cached unrestricted history nor the
receipt's unfiltered snapshot resolutions are substituted. Rejected chain members
are absent from this history and its read trace; changed surviving resolutions
enter the digest. This is true for post-epoch snapshot corrections too.

The global exclusion report is returned explanation, not a digest member.
An unrelated excluded assessment's appearance must not perturb a belief over
an unchanged proposition. Excluded facet values are never decoded just to hash
them. A changed policy statement does move the filtered digest; admitted-input
changes continue to move the existing members. This distinction is explicit in
the kernel §5.1 amendment.

Filtering affects retraction standing at evaluation; it does not mutate the
producer snapshot, epoch coverage, lineage capture or any record. The existing
route-retirement operation is applied only for accepted standing route retractions.

## 7. Guarantees and decisive checks

At freeze, append G10–G13 to the epistemic kernel's guarantee table and its
formal-model coverage inventory. Existing rows keep their ids and frozen cuts
keep their bodies. G3, G8 and correction-standing prose gain explicit acceptance
scope; unrestricted behavior retains the existing interpretation.

| Proposed row | Obligation | Decisive checks |
|---|---|---|
| G10 | Assessment acceptance precedes evidence reads and identity collapse | All-rejected yields `no-eligible-assessment`; excluded facet-disagreeing twin is inert; accepting both still refuses; excluded malformed assessment is not decoded; canonical address and corpus are passed to the predicate |
| G11 | Verification acceptance precedes lifecycle and supersession | Rejected failure cannot invalidate; rejected pass cannot admit; rejected superseder cannot clear an accepted failure; accepted failure or pass naming a rejected twin's stored address still applies to the accepted identical assessment; rejected-only identities admit nothing; twin edge bookkeeping does not widen correction scope |
| G12 | Correction acceptance precedes every standing effect | Rejected node and route retractions are inert; rejected counter cannot restore; filtered resolution changes are legitimate; rejected malformed snapshot-fold candidate is never facet-validated; accepted malformed chain refuses; mapped-only local oracle ignores drift-only aliases; split-corpus disagreement still refuses with unrelated exclusions; unchanged chains retain receipt-fidelity checks; filtered snapshot history alone enters the digest |
| G13 | Policy and selection are reproducible and reported | Complete policy/exclusions on completed selection outcomes, including late consulted-contract refusals and late dependency-absence answers; every incomplete answer has empty exclusions; supplied acceptance context fails before reads; pure incomplete context refuses after the binding guard and before the consulted walk; policy mutation moves filtered digest; unrelated exclusion changes report but not digest; gather and pure-evaluation closures agree |

Additional regression obligations: unrestricted closure bytes and answer shapes;
accept-all value/admission parity; same captured view under two policies with no
cross-call decision leakage; exact-bool return enforcement and raising predicate;
unconditional damaged/absent-world behavior; dependencies in excluded-evidence
corpora remain usable; no rejected-corpus attribution leaks into an accepted pool.
Also test enumeration aliases deliver canonical callback addresses; missing local
manifest fails with `ManifestMissing` before record reads; invalid statement
encoding preserves its `IdentityError`; irrelevant rejected records appear in a
complete report; and incomplete reports remain byte-identical under scan reordering.

The plan maps these checks to declared arms, selects independent sabotages and
records the declaration-unit and guarantee-row counts before implementation.
Each new guarantee has a mutation that bypasses its responsible selection or
reporting seam; the conformance cut is frozen before product code changes.

## 8. Surfaces, delivery and evidence

Expected shared surfaces are `belief.py`, `evaluation.py`, `closure.py`,
`corpus.py` and `world/view.py`; existing evaluation, belief, closure, world-view,
snapshot-retraction and standing tests; the new acceptance module and N2 declarations;
the runner and `test_recent_cut_acceptance.py`; and current-facing kernel,
correction, formal-model, ledger, roadmap and guide documents. The implementation
plan fixes exact files and counts after review, including the existing view's
retention of the packaged correction discovery map and the private shared gather
state for late error reporting. No new runtime dependency is needed.

The accepted design and plan open `belief-acceptance` in `world-read` as a
commons-milestone prerequisite. Current roadmap claims refer to the earlier
one-/two-project dogfood criterion, not this newly requested commons workflow.
The status update must make that distinction explicit and retain its historical
measurement evidence. The later publication-attribution task opens its own
boundary only through its own design and plan reviews. The contract freeze
remains behind oracle-amending work.

Delivery preserves the repository's cut process: prepare the plan; obtain its
review; freeze the successor cut; implement with focused checks; discharge on the
certified tuple; update row accounting and current-facing documents; and integrate
with the recorded acceptance evidence. Every new discharged runner has its row
in `test_recent_cut_acceptance.py`. `root.py` remains the only `atoms` importer,
and no new write entry point is needed for this read-only feature.

Focused verification uses `just test-one` for the affected test groups. Run
`just test-fast` before committing, `just check` via the installed pre-commit
hook, and the configured full pre-push/CI gates. The successor acceptance runner
supplies capability-dependent evidence on the certified tuple. Do not run a full
cut chain for this proposed spec or treat portable tests as discharge evidence.

After this task lands, proceed to `beliefs-f50596` (publication attribution), then
`beliefs-aa9f88` (the already scoped, bounded N2 preflight pilot). This order was
chosen by the user; the spec review does not authorize skipping any later task's
required artifact review.
