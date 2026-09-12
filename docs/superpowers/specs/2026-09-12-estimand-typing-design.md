# Estimand typing — the owner of ρO3's estimand half

**Status:** design, drafted 2026-09-12; under review, not frozen. Task
`beliefs-59f846` carries this spec; `beliefs-638318` (weighted belief) depends
on it. Implements nothing yet: the roadmap's concurrency rule 6 keeps at most
two kernel lanes open while the success criterion is unmet, and this design
is off the path (§11). It is written now because it amends the base contract
and the operator declaration, and the contract cut freezes after the last
oracle-amending lane merges; deciding the shape before that freeze costs one
design, deciding after it costs a successor contract.

**Answers.** ρO3's *estimand* half — kernel limitation 5's residue, belief
policy §3.2's "typed reference and commensuration contract that no artifact
yet owns", belief policy §9 questions 2 and 3, and the review disposition's
open question 4 (where an adjustment set belongs). **Leaves.** ρO3's
*entailment* half (formal model §6.7), quantifier-directed gating (belief
policy §5), the eleven K records and every higher-order claim (cut 1 §2.4),
and the non-empirical route (kernel §11).

**Amends when it lands:** kernel §4.2.1 (the assessment facet table) and
limitation 5; computation §3.1 (the spec facet), §3.1b (the rule's output
types) and §5.1 (the constructor); formal model §7.1 (a domain contract gains
a declaration class) and D6's trigger set (a second amendment, beside §7.1's);
belief policy §3.2 and §5; review disposition §8 question 4; facet contracts
§3.2 (two reader rows narrowed); both copies of `CONTRACT.yaml`;
`domains/biology/DOMAIN.yaml` and the mm30 corpus-local contract, each by a
successor; the guide's claims page and glossary; `open-questions.md`; the
ledger's `Current state` table and the roadmap, at a results record.

## 1. What this design is

Four belief-bearing fields are prose. `estimand`, `applicability`, `estimate`
and `uncertainty` are `str` on the spec draft and the assessment value
(`python/src/beliefs/spec.py`, `record.py`), the stored reader coerces them
with `str` and drops non-strings (`stored.assessment_value`), and the
interpretation rule may return any string for the two it yields
(`assess.build_assessment`). Kernel §4.2.1 describes the estimand as
"population, outcome definition, endpoint type, control structure" and
`record.py`'s docstring says the untyping is deliberate: "typing them is ρO3's
open neighbourhood, not this module's to claim." This design claims it.

Three readers are blocked on the same absence, and each is already named:

| reader | what it needs | where it is blocked |
|---|---|---|
| a weighted successor belief policy (S6 arm (h)) | a study-design key, and a precision term made dimensionless against a **typed reference** | belief policy §3.2: "`estimand` has no type … a design-weight table has no key domain"; limitation 1 |
| estimand match (kernel limitation 5) | `match(claim_type, estimand_type)`, stateable once both are typed | formal model ρO3, §11: "stateable … and is not stated" |
| applicability comparison (belief policy §5) | `applicability` as a qualifier map so canonical equality applies | "It is not a qualifier map, so map equality does not apply to it" |

A fourth is waiting on the ruling rather than the type: the vocabulary survey
admitted `strength` on agreement and exercise and held it out of the base
profile because "weighting is blocked on ρO3, not on this ruling" (survey §4).

The predecessor shows the cost of typing this wrongly. Its `QuantitativeResult`
declared a Bayesian posterior summary only, so six mm30 evidence lines carrying
`attenuation_fraction`, `hazard_ratio`, `p_value`, `confidence_interval` and
`adjusted_for` were "dropped in silence … carried in frontmatter where nothing
read them" (finding F11; the mm30 records still say so in their bodies). A
fixed statistical shape in the kernel is that failure again. The design
therefore types the **structure** an estimand has — what varies, what is
measured, against what null, under what control — and puts every vocabulary
that fills it in a domain contract, which is the D3 split kernel §6.4 already
applies one level up to qualifiers.

**Rows it intends to close.** None of the existing guarantee rows. It files a
new table, **Q** (§8), and answers the design question `weighted-belief` is
blocked on; S6 (h) itself stays that boundary's, since the successor policy is
its own design.

**Rows it does not touch.** P1–P9 are preserved verbatim: v1 still reads no
magnitude-bearing field (P6) and unequal weights stay unspellable under it
(P5). R22's constructor rule is preserved and narrowed. M1–M13 are untouched;
in particular M6 governs the new declaration class without amendment (§5.3).

## 2. Decisions

1. **Ownership is split four ways, and each artifact owns exactly one thing.**
   The **base contract** owns the estimand's structure and its closed
   structural tags (`science.estimand.v1`, §3). A **domain contract** owns the
   sorts that fill it, declared per operator in a new `estimands:` table (§5).
   The **frozen spec** owns the inhabitant — which slot varies, which quantity
   is measured, the null, the identification, the conditioning set — and the
   applicability map. The **interpretation rule** owns the estimate's value and
   its uncertainty, on the scale the spec declared, and nothing else. Belief
   policy §3.2 asked which of the operator, the estimand and the rule should
   supply the reference; the answer is that the operator's contract supplies
   the *types*, the spec supplies the *reference*, and the rule supplies
   *values*. Rejected: an operator declaring the whole estimand type (a domain
   would then own kernel structure, the boundary D8 draws); the rule declaring
   its output type (a rule sees a result manifest and nothing else, and a
   change of null would then be a rule version, conflating two identities);
   kernel-declared vocabularies (the survey ruled `identification_strength`
   **divergent** across corpora and out of the base profile, and no corpus ever
   carried a measure or scale field, so admission rule 2.6 has nothing to
   admit).
2. **`applicability` is a qualifier map**, the claim grammar's flat fragment
   over the target operator's dimensions (§4). Canonical equality against the
   proposition's own qualifiers becomes decidable. **No mismatch finding is
   emitted**: P6's last clause stands, quantifier-directed gating still needs
   term subsumption the domain boundary declines to supply, and refusing on
   mismatch stays rejected on kernel §4.2.1's grounds. What this buys is that
   the comparison exists to be read — by a successor policy, or by a `science`
   view — instead of being uncomputable.
3. **Estimate, uncertainty and reference are decimals on one declared scale**
   (§6). The reference is the spec's; the scale is the estimand's; the rule
   returns `Decimal`s that the constructor checks against both. A float, a
   string, an interval that excludes its estimate, or a rule output that
   restates the reference is a machinery failure and produces a finding, never
   an assessment (computation §3.1b's rule, unchanged).
4. **The conditioning set that defines the target lives on the estimand; the
   set that only identifies it stays in `method`.** This settles the default
   placement cut 1 §8 question 4 left open, mechanically: a covariate set
   appears in `estimand.control.conditioning` when conditioning on it changes
   what quantity is estimated, and in `method` (prose or ref, unchanged here)
   when it only identifies the same quantity. The third home the ruling
   named — a claim asserted *conditional on* a set, in the claim's own
   qualification — is a grammar extension this design does not make; the
   flat fragment still refuses set-valued restrictions.
5. **Structural match is checked; semantic match stays a limitation.** An
   estimand is built against one operator's declaration and cannot be built
   outside it (§7.1); the write boundary then checks the spec's estimand was
   built against the *target proposition's* operator (§7.2), which
   construction cannot see. Whether the measured quantity actually
   operationalizes the claim's argument — kernel §2.1's "that an estimand
   matches the claim it is used for" — is not guaranteeable and is not
   claimed.
6. **Commensuration is a total, decidable predicate that v1 does not read**
   (§7.3). Two admitted estimands are commensurable when they agree on
   everything but identification. It is the key domain the weighted successor
   lacked; defining the weights is that successor's design.
7. **`estimands:` is a claim-vocabulary declaration class.** It enters the
   contract's succession comparison under §8.3's existing four rules: a
   successor may add a declaration for an operator that had none, may never
   change or drop one, and retires it with its operator. No fifth rule is
   needed, and no operator's own schema projection changes, so M6 holds
   unamended and the 307 typed mm30 propositions keep their identities by
   construction (M8).
8. **The consulted walk reaches the estimand's contracts.** D6's trigger set
   gains estimand schemas beside claim schemas and facet namespaces (§5.4).
9. **One inhabited fragment, and anything richer refuses.** A two-level or
   continuous contrast on one slot; one measured quantity; one reference; one
   identification; one flat conditioning set. Multi-arm contrasts,
   interactions, an attenuation across two conditioning sets, time-varying
   estimands and censoring specifics are refused at construction with the
   fragment named, never flattened into the fragment (§3.3). Flattening is the
   scope-widening failure kernel §4.1 exists to prevent, committed by an
   encoding.
10. **Every existing spec and assessment re-identifies.** The spec facet and
    the assessment facet take canonical typed projections, so their identities
    and digests move. Exactly one frozen spec and one assessment exist, both
    the reproduction's, and §9 says what the reproduction re-runs. Belief
    input digests move for every corpus, as verification-publication decision
    12 already made them.
11. **No new kind, relation, facet key, intent, operation kind or write
    class.** Analysis specs and assessments are minted through the writer as
    today; the permit, the session ledger and the root lock are untouched.

## 3. The grammar — `science.estimand.v1`

### 3.1 The base contract

```yaml
# contracts/science/CONTRACT.yaml — beside claim_grammar
estimand_grammar:
  version: 1
  tag_encoding: science.identity.v1
  contrast_kinds: [levels, continuous]
  scales: [additive, multiplicative]
  uncertainty_kinds: [interval, dispersion]
```

Three closed sets, all **structural**: each member is defined by an operation
the kernel performs, not by a label the kernel carries. A `levels` contrast
requires two bound levels and a `continuous` one forbids them; an `additive`
scale compares estimate to reference by difference and a `multiplicative` one
by ratio, so the sign constraints in §6 differ; an `interval` carries bounds
and a level, a `dispersion` a single non-negative width. That is the test
that keeps them out of the survey's admission rule: quantifiers were admitted
as logic on the same ground. A label the kernel never operates on —
identification class, measured quantity — is vocabulary, and goes to a
domain (§5). `tag_encoding` is declared for the reason §7.1 declares it for
claims: a tag's bytes are its symbol, and a loader presented with any other
encoding refuses. A base contract lacking `estimand_grammar` is refused at
load; a domain contract declaring one is refused at load (D8's kernel-kind
arm, applied to a grammar).

### 3.2 The type

```text
Estimand(op)  =  { operator   : the term identifier of op
                 , contrast   : Contrast(op)
                 , measure    : { quantity : Referent(MeasureSort(op)),  scale : additive | multiplicative }
                 , reference  : Decimal                          -- finite; > 0 when multiplicative
                 , control    : { identification : Referent(IdentificationSort(op))
                                , conditioning   : a set of Referent(ConditioningSort(op)), possibly empty } }

Contrast(op)  =  { slot : Fin(arity(op)), kind : levels
                 , baseline : Referent(LevelSort(op, slot)), comparison : Referent(LevelSort(op, slot)) }   -- distinct
              |  { slot : Fin(arity(op)), kind : continuous }

Applicability(op)  =  QualifiersFlat(op)          -- formal model §6.4, unchanged
```

Like `Claim`, an `Estimand` is a dependent sum: choosing the operator fixes
the sorts of every referent through the operator's `estimands:` declaration
(§5.1), and a referent of the wrong sort has no slot to occupy. `operator`
travels with the value for the reason `Referent.sort` does: a bare structure
carries nothing to compare against at the boundary (§7.2).

`baseline` and `comparison` are named, not a sorted pair, because direction is
part of the quantity: "PD against NDMM" and "NDMM against PD" are two
estimands with opposite signs, and collapsing them would let two studies
with opposite conventions read as one key (§7.3). The kernel does not flip
one into the other; a successor policy may define a flip, and this design
defines none.

**Canonical projection.** `operator`; `contrast` as `{slot, kind}` plus
`{baseline, comparison}` when `kind` is `levels`, each referent as
`{sort, term}`; `measure`; `reference` as identity v1's canonical decimal
text; `control` with `conditioning` **sorted by `(sort, term)`**, since it is
a set. Two conditioning orders are one estimand; two level assignments are
two. The projection is a member of the spec's facet projection and of the
assessment's facet digest (§9); it has no digest of its own, because nothing
addresses an estimand apart from the spec that froze it.

### 3.3 The inhabited fragment, and what refuses

The fragment above is the whole of v1. `build_estimand` (§7.1) refuses, with
the fragment named in the reason:

- a contrast over more than one slot, or more than two levels — interactions
  and multi-arm designs;
- a second measure, or a second reference — a ratio of two estimands, which
  is what mm30's `attenuation_fraction` is (an adjusted and an unadjusted
  association compared), and what its record 0008 turns on; that comparison
  is a claim *about* two estimands and stays with the K records;
- a reference that is a function rather than a number — a noninferiority
  margin expressed as a rule; belief policy §3.2 already notes a margin is
  not determined by an endpoint, and v1 carries the margin as the number it
  resolves to, in the spec, declared before the run;
- any time index, censoring rule or repeated-measures structure — carried in
  `method` and `assumptions` as today.

Each is a real expressive limit, recorded as the boundary of this pass.

## 4. Applicability

`applicability` becomes `QualifiersFlat(op)` over the target operator's
declared dimensions, built by the claim module's own qualifier construction:
an undeclared dimension, a second restriction on one dimension, an unbound
restriction referent or a quantifier outside the base set refuses exactly as
it does for a claim. The empty map is admitted and means the estimand
licenses the whole scope the proposition states.

It stays a spec field beside `estimand`, not a member of it. Kernel §4.2.1's
table separates the two, P6 tests them separately, and they vary
independently: one estimand can be licensed for two scopes by two specs.
Folding one into the other would reshape a frozen row's arms to save one
field.

With both sides typed, `applicability == claim.qualifiers` is canonical map
equality (M5's) and is decidable. Nothing in this design acts on the answer
(decision 2).

## 5. The declaration

### 5.1 A domain contract's `estimands:`

```yaml
# a corpus-local contract — mm30, successor of the cut-22 contract
estimands:
  affects-concept-molecular-entity:
    level_sorts: { "0": stage-level }      # slots admitting a `levels` contrast, by index
    measure_sort: measure
    identification_sort: identification
    conditioning_sort: concept
```

- The key names an operator **this contract declares**; a key naming any
  other operator is refused at load. The partition rule the biology pack
  states for operators (an operator lives with its most specific sort) puts
  the estimand declaration with the operator, and a pack cannot declare one
  for a corpus-local operator it has never seen.
- `level_sorts` maps slot indices, spelled as decimal strings so the
  canonical encoder accepts them as keys, to sorts. A slot absent from the
  map admits only a `continuous` contrast; a slot present admits either. An
  index outside `Fin(arity)` or a duplicate is refused.
- The three sorts resolve under the biology pack's resolver (§4.3 there):
  a local name is this contract's, `ns/name` is another's; an unresolved
  reference refuses the compile with the missing namespace named.
- An operator of arity 0 admits no declaration, since a contrast has no slot
  to name; a spec targeting a claim at such an operator is refused (§7.2).
- No `retired` field. Retiring the operator retires its declaration, which
  remains as a tombstone under §8.3's third rule.

### 5.2 Compilation

`compile_profile` compiles `estimands:` after operators and sorts, into
`CompiledEstimandDecl {operator term, level_sorts: {slot: sort term},
measure_sort, identification_sort, conditioning_sort, contract}`, keyed by
operator term in `ProfileSpec.estimands`. The projection enters
`compiled_identity`. TypeScript parses and compiles the same declaration
with the same refusals (contract §4.6 pattern); it validates no estimand
payload and hashes no spec, which stays Python-primary (F §7.2).

### 5.3 Succession

`DomainContract._declarations()` gains `estimand:<operator>` entries whose
schema projection is `{level_sorts sorted by key, measure_sort,
identification_sort, conditioning_sort}`. `check_succession` is not edited:
its existing comparison refuses a changed projection, its existing dropped
check refuses removal, and an added entry passes as any added declaration
does. The operator's own `schema_projection()` is byte-identical before and
after, which is what keeps M6's "changing `arity`, `arg_sorts`, `sign_apt`,
`layers` or `dimensions` … refused" true without amendment and lets the
biology and mm30 contracts gain declarations by successor rather than by a
second genesis.

### 5.4 The consulted walk — D6 amended a second time

§7.1 amended D6's trigger set from facet namespaces to facet namespaces plus
claim schemas. This design adds a third:

> The consulted set includes every contract reached through an **estimand
> schema** — the contract declaring the `estimands:` entry, and the contract
> of each of its sorts and each sort's vocabulary binding — for every
> assessment in the closure, in addition to every contract reached through a
> claim schema or a facet namespace.

`consulted_contracts` takes an `estimands: Mapping[str, Estimand]` beside
`claims`, keyed by assessment identity, and walks
`profile.estimands[e.operator]` and its four sorts exactly as it walks an
operator's argument sorts today. A corpus typing an estimand under a sort no
corpus pins refuses through the existing arm ("consulted but pinned by no
corpus"). The reproduction's set becomes `{science, mm30, biology}` still,
because its new sorts are corpus-local (§9).

## 6. Estimate and uncertainty

```text
Estimate     =  Decimal                                     -- finite; > 0 when the estimand's scale is multiplicative
Uncertainty  =  { kind : interval,   low : Decimal, high : Decimal, level : Decimal }   -- low ≤ estimate ≤ high; 0 < level < 1; low > 0 when multiplicative
             |  { kind : dispersion, value : Decimal }                                 -- value ≥ 0
```

The interpretation rule's signature keeps its shape,
`(execution result) → { outcome, estimate?, uncertainty? }`, and the
constructor now checks what the `?`s carry: `estimate` is a `Decimal` or
absent; `uncertainty` is one of the two shapes or absent; the constraints
above hold against the spec's `reference` and `measure.scale`; and the
output carries **no other key** — a rule that returns `reference` or `scale`
is restating what the spec froze, and is refused as a rule that lies. Every
violation is `evaluation-failed`, recorded as an `AssessmentFinding` on the
run, and never `inconclusive` (computation §3.1b, R22's evaluator-failure
arm). Identity v1 already refuses binary floats and non-finite decimals at
the boundary, so a rule returning a `float` fails at the digest if it slipped
the check, and the check exists so that it fails earlier with a reason.

`mm30-reproduction/outcome-file/v1` yields no estimate and no uncertainty;
its output already conforms and its identity does not move.

## 7. Match and commensuration

### 7.1 Construction — `build_estimand`

```text
build_estimand :  WireEstimand × CompiledOperator × ProfileSpec × ResolutionSnapshot
                  ──▶  (Estimand × BindingCheckReceipts) + Refused
```

The claim module's discipline, one artifact over. The snapshot is in the
signature so two holders cannot build identical bytes differently; every
referent — both levels, the quantity, the identification, each conditioning
member — is resolved under D3's five outcomes, and **only `not-member`
refuses**; `not-consulted` mints and emits a receipt, as it does for a
claim (ρO1's persistence question is unchanged and reaches one more
producer). Refusals, each `Refused` with the position named: the operator
declares no `estimands:` entry; `slot ∉ Fin(arity)`; `kind: levels` on a
slot with no level sort; `kind: continuous` with levels supplied; one level,
or two equal levels; a referent whose sort is not the declared sort for its
position; a duplicate conditioning member; a tag outside a closed set; a
`reference` that is not a finite `Decimal`, or `≤ 0` under `multiplicative`;
anything §3.3 names.

`build_applicability` is the claim module's qualifier construction over the
same operator, and refuses as §4 states.

### 7.2 The boundary — where the target is checked

Construction sees an operator; it cannot see the spec's target, which is a
corpus ref (`target: str`) that only a view resolves. The check that the
estimand was built against the *right* operator therefore lives at the
seams that hold a view:

| seam | check | on failure |
|---|---|---|
| `CorpusWriter._refuse` for an `analysis-spec` record — a new `_refuse_estimand_target_mismatch` beside `_refuse_r20_contradiction` | resolve `spec.target` in the writer's view; decode its claim; require `spec.estimand.operator == claim.operator` and `spec.applicability` over `Dims(claim.operator)` | `ValidationRefused("estimand-target-mismatch")`; an unresolvable target is `ValidationRefused("estimand-target-unresolvable")` — cross-corpus targets are `world-resolution`'s read (§13) |
| explicit import | the same check, over the import view | refused, never repaired |
| audit, a new `check_spec_target` beside `check_assessment` | the same comparison over the stored record | `Finding(code="spec-target-contradicted")`; a raw-written mismatching spec is not refused on read and is caught here only — §7.3c's limitation, unchanged in shape |
| `build_assessment` | none added — it consumes an admitted spec | — |

`FrozenSpec` decode (`restore`, `stored.analysis_spec_value`) rebuilds the
typed estimand and applicability through `decode.estimand_from_stored`,
which takes the profile as `claim_from_stored` does and enforces no
retirement, for the reason `decode_claim` gives: it cannot tell authoring
from restoration. `restore` and `analysis_spec_value` gain a `profile`
argument; every caller is enumerated in the implementation plan (measured:
`corpus._refuse_r20_contradiction`, `succession._decoded_evidence`, the
replay path and the driver's `rederive`).

### 7.3 Commensuration

```text
key(e)               =  π_estimand(e) with control.identification removed
commensurable(a, b)  =  key(a) == key(b)
```

Total over any two admitted estimands, decidable by projection equality, and
**unread by `science.belief.v1`** — P6 says v1 reads no magnitude-bearing
field, and this predicate reads four. It is exposed from `beliefs.estimand`
so the successor policy has its key domain; whether non-commensurable inputs
to that policy refuse, exclude or answer `NoBelief` is the question belief
policy §2.1 deliberately declined to reserve an arm for, and it stays that
successor's.

Identification is the one member outside the key because it is the design
key a weight table reads: a longitudinal and an observational estimate of the
same quantity are the same quantity, weighted differently. Conditioning is
inside the key because a different conditioning set is a different quantity
(decision 4).

## 8. Guarantees — table Q

Certified by mutation per the estimator doctrine; every check must be able to
fail (N2). Rows are `Q1`–`Q10`; the table is owned here and registered in the
corpus inventory when the design moves to `docs/designs/` at freeze.

| # | guarantee | mutation test |
|---|---|---|
| **Q1** | The estimand's structure is kernel-owned and closed | A base contract lacking `estimand_grammar` → **refused** at load; a domain contract declaring `estimand_grammar`, `contrast_kinds`, `scales` or `uncertainty_kinds` → **refused** at load; a `tag_encoding` other than `science.identity.v1` → refused; `build_estimand` with `kind`, `scale` or an uncertainty `kind` outside its set → **refused**. **Sabotage:** widen a closed set in the implementation without editing the contract and assert the shipped base-contract fixture **fails** |
| **Q2** | `estimands:` is domain-issued, operator-bound and succession-governed | An entry keyed by an operator the contract does not declare → refused at load; an unresolved sort → refused at compile with the missing namespace named; an arity-0 operator → refused; a `level_sorts` index outside `Fin(arity)` or duplicated → refused. **Succession:** a successor adding an entry for an operator that had none → **accepted**, with the operator's own `schema_projection()` byte-identical (M6 unamended); changing any of the four members → `SuccessionViolation`; dropping an entry → `SuccessionViolation`; retiring the operator → the entry survives as a tombstone. **Negative:** reorder `level_sorts` keys and assert the contract's content identity and the projection are **unchanged** |
| **Q3** | An estimand is unconstructible outside its operator's declaration, and refuses rather than flattens | Each refusal in §7.1, one fixture each, asserting the position named; a wrong-sorted level, quantity, identification and conditioning member each **refused**; `not-member` refuses and `not-consulted` **mints** with a receipt, and the five outcomes stay distinct (D3 preserved). **Fragment:** three levels, two slots, a second measure, an attenuation pair → each refused with the fragment named, and assert **no flattened estimand** is reachable. **Opacity:** `Estimand` has no public field-wise constructor (M13's shape) |
| **Q4** | `applicability` is a qualifier map over the target operator's dimensions, comparable and unread | An undeclared dimension, two restrictions on one dimension, an unbound restriction → refused; the empty map admitted; `applicability == claim.qualifiers` computed by canonical projection equality and **decidable in both directions**. **P6 preserved verbatim:** change only `applicability`, assert belief value unchanged and digest moved, and assert **no mismatch finding exists** to be emitted |
| **Q5** | Estimate and uncertainty are typed on the spec's scale, and the rule cannot move the reference | A rule yielding a `float`, a `str`, an interval with `low > estimate` or `high < estimate`, `level ∉ (0, 1)`, a negative dispersion, or an estimate `≤ 0` under `multiplicative` → **no assessment**, an `AssessmentFinding` naming the violation, and never `inconclusive`; a rule output carrying `reference` or `scale` → the same. **Negative:** a rule yielding nothing but `outcome` mints as today, and `mm30-reproduction/outcome-file/v1`'s identity is **unchanged** |
| **Q6** | Structural match is checked at the write boundary and under audit; semantic match is not claimed | A spec whose estimand was built against an operator other than its target's → `ValidationRefused("estimand-target-mismatch")`; a target the writer's view cannot resolve → `ValidationRefused("estimand-target-unresolvable")`; explicit import refuses the same; a raw-written mismatching spec is **not** refused on read and is caught **only** under audit with `spec-target-contradicted`. **Negative:** a quantity that names the wrong argument but the right sort is **admitted** — the check is structural, and the row asserts it does not pretend otherwise |
| **Q7** | Every member enters identity, and only members do | Change **only** `contrast.slot`, `kind`, `baseline`, `comparison`, `measure.quantity`, `measure.scale`, `reference`, `control.identification`, one `conditioning` member, or one `applicability` entry: the spec identity **moves** each time; reorder `conditioning` → **unchanged**. On the assessment: change only `estimate`, only `uncertainty`, only `estimand`, only `applicability` → the facet digest **moves**, the belief value is **unchanged** (P6's four arms, now per member); G3's keyed-facet arms unchanged. **Negative:** an editorial change to a consulted contract leaves `I_claim` unchanged (M8) |
| **Q8** | The estimand's contracts are consulted | Derive belief over an assessment whose estimand binds a measure sort declared in contract `X`; bump `X` touching no facet, no operator and no claim → `belief_input_digest` **moves**; bump an activated contract the estimand does not reach → **unchanged**; type an estimand under a sort pinned by no corpus → `ContractDisagreement`. **Sabotage:** drop the estimand walk from `consulted_contracts` and assert the first arm **fails** |
| **Q9** | Commensuration is total, decidable, and unread by v1 | For any two admitted estimands the predicate returns a boolean, never raises; equal except `control.identification` → **commensurable**; differing in any other member → **not**; `baseline`/`comparison` swapped → **not**. **Sabotage:** make the predicate raise and assert every P row still passes — v1 never calls it; **P5** still holds: no API path produces unequal weights |
| **Q10** | The reproduction re-types, re-identifies, and re-derives | Under mm30's successor contract the record's estimand builds with every referent resolving `member` against the held lists; the spec re-identifies; steps 4–10b re-run; the belief re-derives to the **same value** under a **different digest**; the consulted set is unchanged. **Measured, not asserted** (§9) |

## 9. Identity, digests, and the reproduction

- **Spec identity** (`_facet_projection`): `estimand` and `applicability`
  are canonical typed projections in place of strings. Every frozen spec
  re-identifies. One exists.
- **Assessment facet digest** (`AssessmentValue.facet_digest`): the four
  members are typed projections; `estimand` and `applicability` are now
  always present (the spec always has them), so the "absent optionals are
  omitted" rule applies to `estimate` and `uncertainty` only.
- **Contract identities**: the base contract moves (new grammar); `biology`
  and `mm30` move by successor. Claim identities do not move (M8).
- **Belief input digests** move for every corpus, through the base member
  and through the assessment facet.
- **The reproduction.** Its spec's estimand, today the prose "difference in
  PHF19 expression between PD and the other level of the sample-id stage
  token in gse179929", types as: `operator:
  mm30/affects-concept-molecular-entity`; `contrast: {slot: 0, kind: levels,
  baseline: NDMM, comparison: PD}`; `measure: {quantity: <expression>,
  scale: additive}`; `reference: 0`; `control: {identification:
  <observational>, conditioning: ∅}`; `applicability: {}`. The 285-member
  concept list holds `concept:disease-stage` and holds **no** `ndmm` or `pd`
  member (measured 2026-09-12), so the levels cannot bind under `concept`.
  The successor mm30 contract declares three corpus-local sorts —
  `stage-level`, `measure`, `identification` — each bound to a held one-line-
  per-term list exactly as the pack design §6.3 held the concept list; the
  identification list carries the predecessor's two-axis values
  (`interventional`, `longitudinal`, `observational`, `structural`) as its
  first exercise, with `none` deliberately absent, because an estimand with
  no identification does not freeze. What the lists cost, what refused, and
  whether `observational` is the honest class for a two-group comparison over
  paired samples the analysis did not pair, are recorded as a dated addendum
  to the reproduction record. The re-run reaches the evaluator's answer or
  files a finding through this lane.

## 10. Testing and the cut

### 10.1 Unit

`test_estimand.py` (construction, projection, commensuration, every refusal
in §7.1 and §3.3); `test_contract_domain.py` gains the `estimands:` parse and
succession arms; `test_profile.py` the compile arms; `test_spec.py` the typed
draft, freeze, restore and identity arms; `test_assess.py` the Q5 arms;
`test_records.py` the facet digest arms; `test_consulted.py` Q8; `ts/tests`
the parse and compile refusals in TypeScript.

### 10.2 Acceptance

`tests/acceptance/test_estimand_acceptance.py`: Q1–Q10 as acceptance units,
single-homed; Q10 is the reproduction re-run, executed by the driver against
the corpus on the certified volume and read from its addendum.

### 10.3 N2 sabotages

`n2_arms_cut<N>.py`, audited by `test_n2_cut<N>.py` on the cut 12 pattern,
staleness baseline taken from the tree. One arm per mechanism: drop the
closed-set membership check; admit an unknown grammar key; skip the
operator-declared check on an `estimands:` key; skip the `Fin(arity)` check;
skip the level-sort presence check; admit `not-member`; skip the duplicate-
conditioning check; admit a float reference; drop the sign check under
`multiplicative`; drop the dimension check in `build_applicability`; admit a
string estimate; drop `low ≤ estimate ≤ high`; drop the extra-key refusal on
rule output; drop the operator comparison in `_refuse_estimand_target_
mismatch`; drop `check_spec_target` from the audit loop; drop the estimand
walk in `consulted_contracts`; put `identification` into the commensuration
key; drop `estimand:` entries from `_declarations()`. Each sabotage is
validated against its site and its selecting checks before the accounting
freezes.

### 10.4 The cut

A cut number is claimed at freeze, not now (concurrency rule 1); the runner
names the highest-numbered acceptance runner discharged at that time in
`PREFIX_RUNNERS` (rule 5) and carries `PHASE_MODULES =
("test_estimand_acceptance.py", "test_n2_cut<N>.py")`. Declaration units
`Q1`–`Q10`. Frozen by dated commit after review clears; invalidated frozen
evidence is pinned and cited, never edited.

### 10.5 Shared files, under concurrency rule 3

`errors.py`, `test_designs_corpus.py`, the ledger, the roadmap and the guide
index, as every lane. Beyond those this lane rewrites `decode.py` (the
`mutation` lane's surface), `corpus.py` and `evaluation.py` (the
`world-read` lane's), and `stored.py`; the later merge resolves toward the
earlier one.

## 11. Roadmap and ledger placement

- A new boundary, **`estimand-typing`**, owner this design, rows Q1–Q10,
  enters the ledger's `Current state` table and the roadmap's boundary index
  at the results record that discharges its cut; until then this design is
  named only from `weighted-belief`'s *blocked on*.
- **Tier 1, off the path.** Its entry point is designed and nothing outside
  its own work must land first. The dogfood's first belief needs none of it:
  the reproduction reached a computed belief with prose fields. It opens a
  lane, `estimand`, only when no on-path lane is startable (rule 6).
- **Before the contract cut freezes.** It amends the base contract, the
  operator declaration class, the assessment facet and the D6 oracle; N1
  mints a successor identity for every oracle amended after the freeze, so
  `contract-cut` waits on this lane as it waits on every other
  oracle-amending lane, and `beliefs-eacbe2` gains the dependency.
- **`weighted-belief`** stays tier 3. Its blocker changes from "ρO3,
  estimand typing" to "the successor belief-policy design over §7.3's key",
  which is `beliefs-638318`'s own design, filed after this one lands.
- **`extraction-path`** is unaffected; §3.3's attenuation case joins the K
  records it already carries.

## 12. Alternatives rejected

- **One model layer** holding estimands, structures and generators together.
  Rejected in the session that filed this design: it re-merges the three
  senses of "model" the kernel keeps apart, and is how `EvidenceType`
  acquired `simulation` and `expert_judgment`.
- **A kernel-owned identification vocabulary.** The survey measured
  `identification_strength` divergent across separately evolved corpora and
  ruled it out of the base profile; overriding a banked measurement on no new
  evidence is exactly what the admission rule exists to refuse.
- **A fixed statistical result shape** (posterior mean and interval; or
  point, confidence interval and p-value). F11 is the record of the first;
  the second drops the Bayesian case symmetrically. The typed reference and
  scale carry both, and the interval's `level` carries a credible and a
  confidence interval alike without the kernel saying which it is.
- **Typing `method` and `assumptions` in the same pass.** They are three
  separate things kernel §11 refuses to collapse, and the estimand is the
  one with three named readers. They stay prose or ref, and decision 4 says
  which covariate sets stay there.
- **Folding `applicability` into the estimand.** §4.
- **Checking the target at construction** by giving `freeze` the target's
  `Claim`. It would decide the two-namespace question of the assessment's
  `proposition` member (verification-publication §9) as a side effect of a
  signature, which the layer design's claim sub-project owns. The boundary
  check (§7.2) costs one resolution and decides nothing it does not own.
- **Emitting a `scope-differs` note from the belief evaluator.** It amends
  P6's frozen arm for a report nobody reads yet; a `science` view can render
  the same comparison from the typed fields.

## 13. Limitations and open questions this design files

1. **Semantic match is not guaranteed** (kernel §2.1). The measured quantity
   is bound to a sort; that it operationalizes the claim's argument is
   authored. The predecessor's `measurement_model` (observed entity, latent
   construct, relation, failure modes) is the record of that authorship, and
   the survey holds it waiting for a reader; this design supplies the slot
   (`measure.quantity`) and no reader.
2. **The write boundary's target check is corpus-local.** A spec targeting a
   proposition held in another corpus is refused, not admitted unchecked,
   until `world-resolution`'s read side resolves it; filed against
   `beliefs-d248ba` as a caller.
3. **Direction is not normalized.** Two estimands with swapped levels are
   not commensurable here; whether a successor policy may flip one is that
   policy's ruling.
4. **Identification is authored and corpus-local.** Promotion of the
   identification vocabulary to a shared contract follows admission rule
   2.6 when a second corpus carries it; a general-purpose domain contract's
   namespace and ownership remain the formal model's open question.
5. **The claim-qualifier home for "conditional on"** stays a grammar
   question; quantitative restrictions likewise.
6. **Attenuation, model comparison and mediation** are higher-order and
   refused; the K moratorium is unchanged.
7. **TypeScript validates no estimand payload** and hashes no spec (F
   limitation 10, extended).
8. **`restore` and `analysis_spec_value` gain a `profile` argument**, a
   signature change across four measured callers; the plan enumerates them.

## 14. Task linkage

`beliefs-59f846` carries this spec; the implementation plan's tasks become
its children. `beliefs-638318` (weighted belief) depends on it and keeps its
own design gate. `beliefs-eacbe2` (the contract cut) gains it as a
dependency when the lane opens. The composite-claim design that answers
kernel §11's unplaced `inquiry` / `patch-definition` / `structural-chain`
kinds is the second spec the 2026-09-12 session agreed to and is filed
separately; it does not depend on this one.

## 15. Review log

- 2026-09-12, drafted in session from the models assessment; not yet
  reviewed.
