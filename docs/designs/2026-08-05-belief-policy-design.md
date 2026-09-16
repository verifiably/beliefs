# Belief policy — design

**Status:** Banked 2026-08-05, after six review rounds; the banking commit
applies the §6 amendment set across kernel, the formal model, domain extension,
substrate, the normative contract, the review-disposition record, the ledger and
the README. Discharges the prerequisite that the disposition record's F3 and
§5.5 stop rule place ahead of the vertical slice; it does **not** widen
conformance cut 1, which remains frozen and still computes no belief. P1–P9
await implementation.
**Inherits:** kernel §4.2.1 (the dependency-graph aggregation model, its
selection, contestation and clamping rules, and its four undefined policy
citations); kernel §5 and §5.1 (the three answers, and `belief policy version`
as a `belief_input_digest` member); repro §3.1b and 5b §6 (rule identity, and
the exact binding a derivation must carry); world W8a (`well_formed` versus
`resolvable`); formal model §3.3 (the projection codomain) and ρO3 (estimand
match, open).

## 1. Why

Kernel §4.2.1 designs how belief aggregates, in depth and with its
counterexamples worked. It does not say what a belief *is*.

Four of its terms are cited as declared, versioned members of "the belief
policy" and defined nowhere: **the belief scale**, **the displacement metric**,
**the prior**, and **"the policy's ordinary rule"** by which a selection
combines. A fifth is implied and never named — every argument in the section
about contestation turns on assessments of unequal **strength** ("weak `D` over
strong `B`"), and nothing says what strength is a function of. A sixth sits in
the digest: `belief policy version` is a `belief_input_digest` member whose
entire specification is the phrase *"the aggregation rule"*.

So the hole is not aggregation. It is every scalar aggregation is parameterized
by, plus the identity under which those scalars are pinned. This document
supplies them, in the smallest form the current facet can actually support, and
is explicit about which terms it cannot supply and why.

The measurement in the review-disposition record bounds the ambition. On the
corpus this system was designed from, **0 of 259 datasets carry a content
hash**, so nothing is eligible and no assessment exists. A belief policy cannot
be calibrated against data that is not there. Every constant here is therefore
**declared, not fitted**, and the design's response to that is to have as close
to zero constants as the problem allows.

## 2. What a belief policy is

### 2.1 The interface

A belief policy declares a carrier, a neutral element and a metric, and supplies
the evaluator:

```text
V         : carrier                     -- what a belief value is
prior     : V                           -- the fixed neutral state
distance  : V × V → ℝ≥0                 -- displacement
aggregate : AggregationInput → V        -- kernel §4.2.1, end to end
```

`prior` and `distance` are members because §4.2.1 already declares them to be —
*"Both the prior and the displacement metric are declared, versioned members of
the belief policy: a fixed neutral state and a distance on the belief scale."*
`V` is the carrier those two presuppose. `aggregate` is the behaviour.

**The identity binds `aggregate` end to end, not a decomposition of it.** The
tempting alternative is to expose the numeric operations — a sign function, a
strength function, a combination rule — and let the base contract own the fixed
orchestration. It fails on the same argument that made every other rule in this
corpus fixture-bound: §4.2.1's algorithm contains the independent-set selection,
the contestation reduction, the clamp, the candidate ordering and the tie-break,
and **a change to any of them changes belief**. If the policy identity covered
only the numeric primitives, behaviour could move without either identity
moving. The decomposition below is normative as description; the fixtures bind
the whole evaluator.

**Contribution and combination are internal.** An earlier draft exposed
`strength : AssessmentFacet → ℝ≥0 + Refused` at the interface, reserving the
refusal arm for the first policy able to read `estimate`. That is withdrawn.
Reserving it now would prematurely decide whether a future non-commensurable
input means a refusal, a `NoBelief`, or exclusion from the policy's domain —
three different answers — and it buys nothing, because closing ρO3 requires a
contract amendment regardless. The cost the reserved arm was meant to avoid
cannot be avoided by reserving it.

**`direction` is not policy-owned.** `supported`, `refuted` and `inconclusive`
already carry meanings fixed by kernel §4.2.1's facet table. A policy permitted
to map them to signs is a policy permitted to reverse them, and reinterpreting
an outcome is not aggregating it. The mapping `supported ↦ +1`, `refuted ↦ −1`,
`inconclusive ↦ 0` therefore belongs to base outcome semantics, and to the
`science_contract`'s meaning-bearing content under D §8.

### 2.2 Identity is an exact binding

```text
PolicyBinding = (policy rule identity, implementation content identity)
```

Not the rule identity alone. 5b §6 rules that finite fixtures cannot force two
conforming implementations to agree outside those fixtures, so every derivation
carries the exact implementation it used. A belief computation naming only
`science.belief.v1` would let two conforming implementations produce different
values behind one digest — the precise failure repro §3.1b names for evaluators:
*"versioning a symbol is not versioning behaviour."*

This replaces kernel §5.1's `belief policy version` member, which is the last
bare version string in the digest. World W8a already returns **`malformed`** for
a rule reference that is a bare version string with no fixture binding; the
member that determines the value itself should not be the one exception.

### 2.3 The binding is a required argument, and the policy is not corpus-pinned

The binding is supplied **to each computation**. No default, no implicit
"latest", no stored selector. This is the producer-snapshot ruling applied
without modification (world §5, kernel §5.1): *"the identity is a **required
argument** to the computation, with no default, no implicit 'latest' and no
stored selector, since any of those would make belief follow the checkout."*
Every word of that is true of the belief policy.

The policy therefore does **not** live in the `science_contract`. An earlier
draft argued this on the grounds that embedding would let an unrelated
base-contract amendment fork every belief digest. **That argument is void**, and
is recorded here rather than deleted: D §8 already makes exactly one
`science_contract` an unconditional digest member, so every base-contract
amendment forks every belief digest today. Embedding adds no such cost.

The reasons that do hold:

- a policy is an executable, fixture-bound rule, and the existing rule mechanism
  already fits it — no new artifact and no new lifecycle;
- policy selection is **per computation**, while a `science_contract` is
  **corpus-pinned**;
- embedding would make it impossible to evaluate one closure under two
  explicitly named policies without changing corpus configuration, which is
  most of what a versioned policy is for.

It is an ordinary rule identity resolved through the existing rules store. No
"record beside the contracts" is introduced.

## 3. `science.belief.v1`

```text
V₁        = ℤ
prior     = 0 ∈ ℤ
distance  = |a − b|

weight    = 1 for every directional eligible assessment
combine   = integer sum,  sum(∅) = 0
```

The value is a **signed evidence balance**: independent corroboration minus
effective contestation, after §4.2.1's reduction. One demonstrably independent
assessment is one unit.

### 3.1 Why the carrier is ℤ and not log-odds

An earlier draft chose log-odds on the reals, and the choice was made before
knowing what would populate the scale. Withdrawn. Under unit weight a value is a
signed count, and calling a signed count "log-odds" asserts that each
independent assessment multiplies the prior odds by exactly *e*. Nothing
supports that, and the assertion would be invisible to a reader who was told the
units were log-odds. **The value must not be rendered as odds or as a
probability.**

ℤ also removes a defect the real-valued draft carried: on `ℝ ∪ {±∞}` the
displacement `|a − b|` is partial at equal infinities, so the metric was not
total on its own carrier.

### 3.2 Why weight is uniform, and what that costs

Strength was to be a function of study design and precision — `estimand`
supplying a design key, `uncertainty` a precision term. Neither is computable.

**`estimand` has no type.** It appears once in the corpus, as prose: *"population,
outcome definition, endpoint type, control structure — copied from the frozen
spec, never re-authored here."* No value set is declared for any component, and
no design says who would declare one. A design-weight table has no key domain.

**A precision term needs a reference the facet does not supply.** `uncertainty`
is defined as *"interval / dispersion, **on the estimate's own scale**"*, so any
precision term must be made dimensionless before it can be compared across
estimands, and every dimensionless form needs to know what the estimate is
measured *against* — a null, a contrast, a margin. The current facet supplies no
typed reference and no commensuration contract. Which artifact should supply
them — the claim operator, the estimand, or the interpretation rule — is exactly
the neighbourhood ρO3 leaves open, and a noninferiority margin is not determined
by a typed endpoint alone. This design does not claim that territory: putting a
belief-determining vocabulary in the one document that must not own vocabulary
would repeat the error the domain-extension boundary exists to prevent.

So v1 weights every directional eligible assessment at 1. The cost is stated
plainly in limitation 1: a large, well-controlled study and a small uncontrolled
one contribute equally.

> **Amended 2026-09-16 — the blocker this section named is supplied, and v1
> still weights at 1** (`2026-09-12-estimand-typing-design.md`, discharged at
> conformance cut 31). Both sentences above are now false as statements about
> the artifacts, and true as statements about v1.
>
> **`estimand` has a type.** It is a typed opaque value built against the typed
> claim it answers — a contrast on one argument slot, a measured quantity on a
> declared scale, a reference, and a control structure of one identification
> term and a set of conditioning members — under a kernel-owned closed grammar,
> with each member's vocabulary declared by a domain contract per operator. A
> design-weight table has a key domain: `commensuration_key`, exposed through
> the total predicate `commensurable`, which is equality on every member except
> `control.identification` — the member a design weight would read.
>
> **The precision term has its reference.** `uncertainty` is typed as an
> interval with a level, or a dispersion with a standard error, on the scale
> and against the reference the **spec** declared, and the rule cannot move
> either. That is exactly the "what the estimate is measured against" this
> section said the facet did not supply.
>
> **What this does not do is write the successor.** `science.belief.v1` reads
> none of these fields and weights every directional eligible assessment at 1;
> the estimand-typing design's Q9 asserts that making either predicate raise
> leaves every P row passing, so v1's independence from them is measured, not
> claimed. Limitation 1 stands as written. What has changed is that the
> successor is now a **policy** question — which weights the key licenses, and
> §9 question 3's scope of its constants — rather than a typing one, and it is
> `weighted-belief`'s to design.

There is one compensation worth naming, because it is not merely consolation. A
count is **interpretable**. The units are not a fitted quantity standing in for
evidence; they are the number of demonstrably independent assessments, and the
document can say so without a warning attached.

### 3.3 §4.2.1's unequal-strength argument, and where it is now tested

§4.2.1 establishes that the contrary selection must inherit the outer objective,
using a case with a **strong** dispute `B` and a **weak** universal dispute `D`.
Under v1 that case cannot be constructed: `B` and `D` weigh the same.

The argument is not thereby invalid — it is a property of `aggregate` over
policies that assign unequal weights, not a property of v1. But it must not be
allowed to pass **vacuously**, which is the failure the disposition record's
limitation 8 was written about. Two separate things are therefore done, and
neither is a test-only policy registered as if it were production machinery:

- P5 asserts that unequal weights are **unspellable** under
  `science.belief.v1` — a claim about today, which can be sabotaged and fail
  today, as N2 requires of every oracle;
- substrate **S6(h)** carries the weak-`D`/strong-`B` case as a **named
  acceptance condition binding the first successor policy that admits unequal
  weights**. It is an obligation on a future artifact, not an assertion about
  the present one.

### 3.4 `inconclusive` is not a vertex

`direction(inconclusive) = 0`, and a zero-direction assessment is excluded from
both the selection graph and the contrary subgraph.

Admitting it as a zero-weight vertex would be worse than excluding it. Selection
is cardinality-first, so a zero-weight vertex **competes for cardinality**: it
can enlarge a maximum independent set it contributes nothing to, and thereby
displace a contributing assessment from the winning selection. That moves the
value through a channel with no evidential content.

Exclusion is a statement about the **value**, not about the record. An
inconclusive assessment remains a belief input: its keyed facet is in the G3
closure, so the digest moves when one is added (P8). Its outcome is read — to
decide the exclusion — so it is committed, not ignored.

### 3.5 No cap on the sum

Nothing saturates and nothing is clamped except at the prior, as §4.2.1 already
requires.

The reason is structural, not empirical: every evaluated state supplies a
**finite** set of assessments and v1 sums integers over a subset of them. An
earlier draft argued instead that a proposition's assessments number "in the
single digits" — an empirical claim about today's corpus, which is the kind of
claim that goes stale and is later found by a drift sweep.

Implementations use **unbounded integers**. A fixed-width implementation that
would overflow must **refuse**; saturating would publish a value the policy did
not compute.

## 4. What asking for a belief returns

```text
BeliefAnswer =
    Belief(value, belief_input_digest, policy_binding)
  | NoBelief(reason)
  | Refused(reason)

NoBeliefReason =
    Unavailable(PolicyUnheld | FixturesUnheld | InputUnheld | CorpusAbsent)
  | NoEligibleAssessment
  | NoDirectionalOutcome
```

Three top-level answers, as kernel §5 requires — *"a belief, *not available*, or
a refusal"*. Reasons are discriminants **within** an arm, never a fourth answer.

| condition | answer |
|---|---|
| binding not supplied, or only the rule identity supplied | `Refused` |
| binding structurally malformed — a bare version string, no implementation identity | `Refused` |
| named implementation **fails its fixtures** | `Refused` |
| consulted contracts disagree across corpora | `Refused` (D7, unchanged) |
| binding well-formed, implementation or fixtures **not held here** | `NoBelief(Unavailable(PolicyUnheld \| FixturesUnheld))` |
| corpus holding the records absent | `NoBelief(Unavailable(CorpusAbsent))` (R5) |
| unholding removes the **last** eligible directional assessment | `NoBelief(Unavailable(InputUnheld))` |
| no eligible assessments at all | `NoBelief(NoEligibleAssessment)` |
| eligible assessments exist, none directional | `NoBelief(NoDirectionalOutcome)` |
| otherwise | `Belief(...)` |

### 4.1 Why a fixture failure refuses rather than reporting unavailable

World W8a splits *is it an identity* (`well_formed`) from *is it held*
(`resolvable`), and rules that a rule identity naming an implementation which
fails its fixtures *"is not that rule"* — a `resolvable` failure, since the
reference is well formed and the world simply holds no such rule.

That reading does **not** transfer here, and an earlier draft applied it
unchanged. W8a's case is an identity that names a rule you must then go find. A
`PolicyBinding` names the implementation **explicitly**. If that exact content
identity fails the fixtures, the binding asserts something false, and installing
a conforming implementation beside it cannot make it true. Nothing repairs it,
so it is not a condition of this checkout.

### 4.2 Why `NoEligibleAssessment` is not `Unavailable`

`NotAvailable` in formal model §3.3 is **computational**: required material is
absent, so the projection cannot be computed. With no eligible assessments the
computation succeeds and discovers that no belief exists. Filing that under
`Unavailable` would collapse semantic absence into local unavailability — two
states a reader must be able to tell apart, since one is repaired by mounting a
corpus and the other by doing science.

**The reason is named for what is computable, not for what it probably means.**
An earlier draft called it `Unassessed`. Withdrawn: the system cannot determine
whether zero eligible assessments means *not yet assessed* or *outside the
empirical route entirely*, and `claim_layer` cannot decide it either, because
eligibility is a property of the run's `observes` edge rather than of the claim.
Banking `Unassessed` would freeze a knowingly false interpretation into a
guarantee table. `NoEligibleAssessment` states exactly what was established.

It and `NoDirectionalOutcome` are distinct: **fifty inconclusive assessments are
not an absence of assessment.**

### 4.3 Why the empty selection never publishes `Belief(0)`

`sum(∅) = 0` is the algebraic identity and is never a reportable answer. A
published `Belief(0)` for a proposition nobody has assessed would be
indistinguishable from a genuinely balanced one — absence of evidence returned
as a verdict, which is the error the kernel exists to remove (`fb-2026-07-19-011`:
absence of evidence is indeterminate, never a fail). A **balanced directional
set does** publish `Belief(0)`; that is a result.

This is the common case, not an edge one. Kernel limitation 1: belief is sparse
by construction and the unassessed row stays wide.

### 4.4 Partial unholding recomputes

`Unavailable(InputUnheld)` wins only when unholding removes the **last** eligible
directional assessment. Otherwise belief **recomputes from the survivors** — and
where the dropped assessment was refuting, the value **rises**. That is R5's
negative (a) and §4.2.1's addition-only property, both banked. A refusal here
would silently overrule a recomputation the corpus already specifies.

### 4.5 The answer is a value, not a record

Belief is a computed view (kernel §6). No belief node, no authoritative "current
belief" selector, and no prior value or digest is retained or accepted as input.
Caching may exist and must be observationally inert.

`belief_input_digest` accompanies the **`Belief`** arm only. This is exactly
ρA8's arm restriction: the closure digest determines the value, and whether that
arm is reached at all is decided by eligibility and by what is held. Diagnostics
may accompany any arm and never affect the value.

## 5. Applicability

v1 reads `applicability` for **reporting only**. It weights nothing, gates
nothing, and excludes nothing.

An earlier draft had the policy emit a `scope-mismatch` finding whenever
`applicability` differed from the proposition's scope, comparing them by the
canonical qualifier-map equality M5 pins. **That is not constructible**, and the
reason is worth recording: `applicability` is untyped prose — *"the scope the
estimand licenses, which may be narrower than the proposition"* — exactly like
`estimand`. It is not a qualifier map, so map equality does not apply to it, and
ρO3 defines no applicability-match predicate. The system cannot emit "mismatch"
because it cannot compute one.

Two stronger designs were considered and both are blocked upstream:

- **Quantifier-directed gating** — narrower-scope evidence can refute a
  universal claim but cannot corroborate it, and the reverse for an existential
  one — is the epistemically right rule and needs **term subsumption**. The
  domain-extension design declines to supply it as a deliberate commitment:
  *"'Ontology' and 'controlled vocabulary' do not appear at all"*, ontologies are
  `reads` inputs conferring no eligibility, and `term` is an external identifier
  with no declared hierarchy. The formal model independently marks `scope`
  **"defective — no order is defined"** wherever it is compared rather than
  matched.
- **Refusing on mismatch** is rejected on banked grounds even if a predicate
  existed: §4.2.1 refuses to convert a working belief state into *"an
  availability failure that anyone able to add assessments can trigger."*

Kernel limitation 5's residue is unchanged. What this design adds is its
**blocker, named**: the residue is not waiting on effort, it is waiting on a
typed reference and a commensuration contract that ρO3 leaves open.

> **Amended 2026-09-16 — `applicability` is typed, and v1 still reads none of
> it** (`2026-09-12-estimand-typing-design.md`, discharged at conformance cut
> 31). `applicability` is no longer untyped prose: it is a **qualifier map over
> the target operator's declared dimensions**, sorted exactly as a claim's
> qualifiers are, so the map equality M5 pins **does** apply to it and
> `applicability == claim.qualifiers` is decidable in both directions. The
> `scope-mismatch` finding this section withdrew as *not constructible* is
> therefore constructible now.
>
> **It is still not emitted, and the reason has changed.** It was blocked on
> computability; it is now declined on the banked ground this section already
> gives — P6 is frozen, v1 reads no magnitude-bearing field, and amending a
> frozen arm for a report nobody reads is not worth the amendment. A `science`
> view can render the same comparison from the typed fields. The
> estimand-typing design's Q4 asserts this directly: change only
> `applicability`, and the belief value is unchanged, the digest moves, and
> **no mismatch finding exists to be emitted**. `co_scoped` is exposed beside
> `commensurable` for whoever wants the comparison, and v1 calls neither.
>
> **Quantifier-directed gating is unchanged and still blocked.** It needs term
> subsumption, which nothing here supplies: no order over terms is defined, and
> a qualifier map's equality is not a subsumption relation. Kernel limitation
> 5's residue narrows to its semantic half — see the amendment there.

## 6. What this amends

Applied at banking, as one amendment set.

| site | change |
|---|---|
| kernel §5.1 | `belief policy version` → `policy_binding = (policy rule identity, implementation content identity)` |
| kernel §5, G3 | the three answers become `Belief \| NoBelief(reason) \| Refused(reason)`; the digest accompanies the `Belief` arm only |
| kernel §4.2.1 | the four undefined citations resolve to §2.1; `direction` fixed in base outcome semantics; `inconclusive` is not a vertex (§3.4) |
| kernel lim. 5 | applicability is read to report, never to weight; blocker named — no typed reference or commensuration contract, ρO3 |
| formal model §3.3 | codomain `Belief + NotAvailable + Refused` superseded by `Belief \| NoBelief \| Refused`. **M₀ is preserved as the historical snapshot and annotated**, never rewritten |
| domain-extension §8 | outcome→sign semantics added to the `science_contract`'s meaning-bearing content. **D6 unchanged** |
| substrate S6(h) | the weak-`D`/strong-`B` case becomes a named acceptance condition for the first weighted successor policy (§3.3) |
| 5b §4, ledger artifact 7 | the exact oracle inventories gain P1–P9, under `P` for the reason §7 gives |
| ledger §1, §3 | artifact 10 and order item 9 |
| disposition record | F3 marked designed **and narrowed**; §5.5's stop rule preserved verbatim with its prerequisite recorded as discharged. **Cut 1 stays frozen and still computes no belief** |
| README | design count and the table |

**One amendment outside the set, found while applying it.** Kernel §5.1 read
*"A belief state that cannot be recomputed byte-identically from its **digest
alone** is a defect, not a drift."* A digest is a hash and nothing is
recomputable from one; G3's own test arm always said the recomputation runs
*"from the named **closure** alone"*, so the section defining the digest and the
row testing it disagreed. Corrected to *"from the closure this digest names"*.
It is listed here rather than folded in silently because it is a change to
banked text that this design did not set out to make — the same defect P7 was
written to avoid in the evaluator's own guarantee.

**The successor identity is the contract's, not the row's.** Normative contract
§3: *"amending a row's meaning mints a successor contract identity under the
retained id."* G3 keeps its oracle id; the contract cut carrying the amended G3
gets the successor identity. The inventories move because **P1–P9 are added**,
not because any existing id changed.

## 7. Guarantees, and how each is tested

Table **P**. `B` is unavailable: the formal model already uses it for the belief
reading throughout M₀, and reusing it for oracle ids would recreate exactly the
overloading that document was written to remove.

| id | guarantee | test |
|---|---|---|
| **P1** | The belief evaluator accepts only an exact `PolicyBinding`; resolution happens before the call | Supply nothing → **refusal**; supply the rule identity alone → **refusal**. **Negative — this is a claim about the evaluator, not the resolver:** assert 5b §6's deterministic resolution of a single conforming held implementation is **unaffected**, and that the evaluator still refuses the identity that resolver would have accepted |
| **P2** | A named implementation failing its fixtures **refuses** | Bind an implementation that fails, assert **refusal**, not `NoBelief`. Then **install a conforming implementation beside it** and assert the original binding **still refuses** — the binding is false, not unresolved. **Negative:** a well-formed binding whose implementation is merely **not held** yields `NoBelief(Unavailable(PolicyUnheld))`, and holding it later makes the same binding compute |
| **P3** | The binding is a digest member | Change **only** the implementation content identity under one rule identity, with the closure otherwise byte-identical, and assert `belief_input_digest` **differs**. **Negative:** resolve the same binding in a different checkout and assert the digest is **unchanged** |
| **P4** | The absence states are distinguishable | A balanced directional set publishes **`Belief(0)`**; **no eligible assessments** publishes `NoBelief(NoEligibleAssessment)`; fifty eligible **inconclusive** assessments publish `NoBelief(NoDirectionalOutcome)` and specifically **not** `NoEligibleAssessment`. Assert all three are distinguishable from each other and that none is `Unavailable` |
| **P5** | Unequal weights are **unspellable** under `science.belief.v1` | Attempt to construct two eligible directional assessments contributing different magnitudes; assert no API path and no facet content produces one. **Sabotage:** give one assessment weight 2 in the implementation and assert the fixtures **fail** |
| **P6** | v1 reads no magnitude-bearing facet field | Change **only** `estimate`, **only** `uncertainty`, **only** `estimand`, and **only** `applicability`, in each case preserving `outcome`, eligibility and the dependency structure; assert the **value is unchanged** and the **digest moves** every time. Assert `applicability` may be **reported** and that **no mismatch finding exists** to be emitted |
| **P7** | Belief is a computed view | Assert **no** belief record and **no** authoritative current-belief selector is minted; assert the evaluator accepts **no** prior value and **no** prior digest as input; assert recomputation from the same committed projection under the same exact binding is **byte-identical**. Assert any cache is **observationally inert** — clearing it changes no answer |
| **P8** | An `inconclusive` assessment is value-inert but digest-committed | Add an **otherwise eligible** inconclusive assessment; assert the value is **unchanged** and `belief_input_digest` **changed**. **Negative — the exclusion is not a cardinality gift:** construct a graph where admitting it as a zero-weight vertex **would** enlarge the maximum selection and displace a contributing assessment, and assert the value is unmoved |
| **P9** | Unholding precedence | Unhold so the **last** eligible directional assessment is removed; assert `NoBelief(Unavailable(InputUnheld))`. Then **partial** unholding: assert belief **recomputes from the survivors**, and where the dropped assessment was **refuting**, assert the value **rises** — R5's negative (a), which a refusal here would contradict |

## 8. Limitations

1. **The value is a count, not a measure of evidential weight.** A large
   well-controlled study and a small uncontrolled one contribute equally.
   Blocked on a typed reference and a commensuration contract (§3.2, ρO3), not
   on effort.
2. **Inconclusive results are not evidence of absence.** Fifty of them read as
   none, for the value. They are distinguished from an absence of assessment in
   the answer (§4) and are digest-committed (P8), so the state is visible; it
   just does not move the number.
3. **Applicability is unread for value and has no mismatch predicate** (§5).
   Kernel limitation 5's residue stands unchanged.
4. **A dependent contradiction can neutralize, never overturn** — §4.2.1's own
   limitation, inherited unchanged. Selection is cardinality-first, so strength
   never rescues a contrary assessment into the selection, and under uniform
   weight there is no strength to do the rescuing anyway.
5. **Agreement holds within an availability context and across nothing else.**
   Two installations resolving the same binding and the same closure agree; one
   lacking the implementation returns `NoBelief(Unavailable(...))`, which is
   agreement about what it can establish rather than a contradicting value. Same
   non-purity W8a states for its evaluator.
6. **Nothing is calibrated, because there is nothing to calibrate against.** On
   the measured corpus every proposition returns `NoBelief(NoEligibleAssessment)`. The
   design's answer is to carry exactly one constant — unit weight — so the
   uncalibrated surface is as small as the problem permits.
7. **This design widens no cut.** Conformance cut 1 is frozen and still computes
   no belief; P1–P9 are acceptance criteria for a later slice.

## 9. Open questions

1. **Non-empirical propositions return the wrong absence.** Kernel §11 calls
   these the single largest open question: math, derivation, algorithm and
   model-conditional claims have no `observes` input and so cannot produce an
   assessment at all. Under §4 they return `NoBelief(NoEligibleAssessment)`,
   which is true but **deliberately collapses two states**: *not attempted* and
   *no applicable route*. §4.2 explains why the collapse is banked rather than
   resolved — nothing currently computes the distinction, and `claim_layer`
   cannot supply it because eligibility reads the run's `observes` edge. It is
   uncollapsed by whichever of these arrives first: the second route kernel §11
   asks for, supplying its own answer type, or a **route-applicability
   predicate**, after which `NoBeliefReason` can gain a discriminant that
   something is able to decide. Adding `OutsideEmpiricalRoute` now would mint a
   reason no computation could ever return.
2. **Where estimand typing lands.** ρO3's neighbourhood — a typed reference, a
   contrast, a commensuration contract — could be owned by the claim operator,
   the estimand, or the interpretation rule. Until it has an owner, no weighted
   successor policy can be written.

   > **Answered 2026-09-16** (`2026-09-12-estimand-typing-design.md`,
   > discharged at conformance cut 31). It lands in **three places, split by
   > who may own what**. The **kernel** (the base contract) owns the closed
   > *structure*: the grammar version, the contrast kinds, the scales and the
   > uncertainty kinds. A **domain contract** owns every *vocabulary* that
   > fills it, declared per operator in an `estimands:` table. The **spec**
   > carries the instance — the estimand built against its typed target claim,
   > and the applicability map over that claim's operator's dimensions — and
   > the **interpretation rule** owns none of it: it returns an estimate and an
   > uncertainty *within* the spec's declared scale and reference and may not
   > move either. A weighted successor policy can now be written; what it
   > reads is `commensuration_key` and the typed uncertainty, and question 3
   > below is what remains of this question.
3. **Scope of a weighted successor's constants.** Global, per-domain, or
   per-corpus. Per-corpus would make belief follow the checkout and is almost
   certainly wrong; per-domain interacts with D §8's contract-agreement rule.

   > **Amended 2026-09-16 — still open, and now the binding one**
   > (`2026-09-12-estimand-typing-design.md`, discharged at conformance cut
   > 31). Question 2's answer supplies the key domain and does **not** answer
   > this: whether a design weight over `control.identification`, or a
   > precision term over a typed uncertainty, is fixed globally or per domain
   > is a policy ruling no typing decides. It now blocks `weighted-belief`
   > alone, which is why the roadmap's *blocked on* for that boundary becomes
   > the successor belief-policy design over `commensurable` and `co_scoped`
   > rather than ρO3.
4. **Whether `NoBeliefReason` is extensible by a domain**, or closed at the
   kernel. Closed is the default here; question 1 is the first pressure on it.
