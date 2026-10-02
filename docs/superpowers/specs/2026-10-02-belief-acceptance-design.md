# Belief acceptance before evidence and correction effects

**Date:** 2026-10-02  
**Status:** proposed; written-spec review pending; no implementation authorized by this artifact yet  
**Task:** `beliefs-d9bc57`  
**Boundary:** `belief-acceptance`, proposed in the `world-read` lane  
**Workspace:** `.worktrees/acceptance-filter`, branch `feat/acceptance-filter`  
**Measured against:** main `676e2f8`; the worktree starts at `f5a8ac2`, which adds only the task claim  
**Cut:** numbered at freeze after the spec and implementation-plan reviews; no cut is frozen here

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
spelling. The result must be exactly a `bool`; another return type is malformed.
Exceptions fail the call and never turn into acceptance or an unrestricted retry.

The statement is nonempty text, validated by `science.identity.v1` encoding.
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
- `complete: bool`, whether gathering finished successfully.

`EvaluationInputs` gains `acceptance: AcceptanceContext | None`. `SuppliedContext`
gains the same optional field so `_evaluate_over_inputs` can forward the computed
selection to the pure evaluator with its existing `replace` operation. `Belief`,
`NoBelief` and `Refused` gain the same optional field. Unrestricted calls leave
it unset and preserve their present results.

For a filtered call that completes gathering, every rejected evidence or
correction record encountered in the selection domain is listed, including
irrelevant evidence records. Science joins each corpus/address pair to the
origin information bound in its statement when rendering the upstream
world-attributed exclusion report. Holding corpora are not presented as
authenticated provenance worlds.

A returned refusal before gathering completes carries the statement with
`complete=False`; it must not present an empty exclusion list as a completed
selection. Existing raised kernel errors still raise. A pure evaluator may
consume a complete context with already selected `Records`; it does not have
corpus/address information sufficient to run the predicate itself. An
incomplete acceptance context cannot produce a `Belief`.

Completeness means all candidate scans and filtered folds finished, not merely
that `gather` returned. Its early absent-input route returns an incomplete
context, and `unavailable-corpus-absent` carries that context without pretending
selection finished. Exclusions already observed may be reported; an exception
path that cannot return them reports the statement and `complete=False`.

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
the stored address. An explicit policy on a manifest-less local corpus cannot
invent a corpus identity and fails at that boundary.

Each gather call caches decisions by `(corpus_id, address)` and invokes the
predicate at most once for a candidate in that call. The same decision is
used by snapshot standing, ordinary corrections and evidence selection.
No decision is cached on a shared view or across calls. Changing policy and
re-evaluating the same view must change selection immediately.

### 5.2 Evidence

Reject an assessment or verification before decoding its facet, adding its
identity or address to the visited sets, recording a semantic read, or
applying relation-based selection. Rejected malformed evidence therefore
does not poison the accepted pool; accepted malformed evidence still refuses
under the existing checks.

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
candidate inventory for mapped corrections; node/route effects are applied
here, and snapshot effects are judged by the live fold of §5.4. It is not replaced
with caller-supplied refs, and post-epoch ordinary corrections do not enter it.
Filter candidates before resolving or validating their contents. Resolve and
validate surviving corrections' targets with the existing view. A target may
be looked up to establish an accepted correction's integrity without being
accepted evidence or becoming a standing graph vertex.

Filtering can legitimately change a surviving retraction from `overturned` to
`upheld`. Comparing that filtered result directly to the unfiltered receipt
would reject the intended behavior. For an evaluation with excluded receipt
candidates, derive per-corpus resolutions over the surviving inventoried facets
using the captured per-corpus resolution data, then compare those with the
world-wide fold before applying effects. Both folds use exactly the same
acceptance decisions. Scope and digest the resulting filtered resolutions.

If no inventoried correction was excluded, retain the comparison with the original
receipted resolutions. In particular, an explicit accept-all policy must not
hide an existing `RetractionResolutionDisagreement`. Excluding a post-epoch
snapshot-chain record outside the carried inventory does not disable this check;
that record participates only in the live snapshot fold of §5.4.

The per-corpus versus world-wide disagreement remains a refusal even when a
policy filters some unrelated correction. This is the existing split-corpus
limitation (`beliefs-c800ef`, research task `beliefs-ae33ff`), not permission to
change the shipped derivation rule or its receipt identity. Epoch publication,
audit and import continue to use their existing unfiltered semantics.

### 5.4 Snapshot corrections

Allow the snapshot-standing helper to receive an optional decision callable
that takes corpus id and canonical stored address. Filter correction vertices
before any fold and before chain-member validation, including counter-retractions
that reach a snapshot-arm root.

`WorldReadView.snapshot_standing` forwards that callable over the same **full
captured records** it uses now. A filtered fold is computed for that evaluation
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
| G11 | Verification acceptance precedes lifecycle and supersession | Rejected failure cannot invalidate; rejected pass cannot admit; rejected superseder cannot clear an accepted failure; accepted failure plus accepted resolution retains the existing lifecycle |
| G12 | Correction acceptance precedes every standing effect | Rejected node and route retractions are inert; rejected counter cannot restore; filtered resolution changes are legitimate; snapshot root/counter and post-epoch snapshot cases are filtered; accepted malformed chain refuses; split-corpus disagreement still refuses |
| G13 | Policy and selection are reproducible and reported | Complete policy/exclusions on Belief and NoBelief and on post-gather Refused; pre-gather returned refusal is marked incomplete; policy mutation moves filtered digest; unrelated exclusion changes report but not digest; gather and pure-evaluation closures agree |

Additional regression obligations: unrestricted closure bytes and answer shapes;
accept-all value/admission parity; same captured view under two policies with no
cross-call decision leakage; exact-bool return enforcement and raising predicate;
unconditional damaged/absent-world behavior; dependencies in excluded-evidence
corpora remain usable; no rejected-corpus attribution leaks into an accepted pool.

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
plan fixes exact files and counts after review. No new runtime dependency is needed.

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
