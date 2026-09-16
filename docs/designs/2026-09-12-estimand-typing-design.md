# Estimand typing — the owner of ρO3's estimand half

**Status:** frozen 2026-09-15 at conformance cut 31
(`2026-09-15-conformance-cut-31.md`), after three spec reviews, a plan
review and a second-domain worked example (§15, Appendix A); implementation
follows on `design/estimand-typing`. Task `beliefs-59f846` carries this
spec; `beliefs-638318` (weighted belief) depends on it. The lane opened
under the roadmap's concurrency rule 6 once cut 30 left tier 1 with no
on-path boundary; this design is off the path (§11). It was written before
the lane could open because it amends the base contract
and the operator declaration, and the contract cut freezes after the last
oracle-amending lane merges; deciding the shape before that freeze costs one
design, deciding after it costs a successor contract.
**Discharged 2026-09-16 at cut 31**, Q1–Q10 closed in full; results
`../plans/2026-09-16-conformance-cut-31-results.md`. The boundary entered the
ledger's `Current state` and the roadmap's boundary index at that record and
closed in the same commit (§11).

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
   view — instead of being uncomputable. A prose applicability retypes only
   along declared dimensions or by dropping a restatement of an `observes`
   dataset; every other clause refuses. A spec re-authored under the grammar
   is a new spec in a recreated corpus, with no successor link to the prose
   one and no certified scope equality (§4, decision 10).
3. **Estimate, uncertainty and reference are decimals on one declared scale**
   (§6). The reference is the spec's; the scale is the estimand's; the rule
   returns `Decimal`s that the constructor checks against both, and each
   uncertainty kind has one fixed meaning — a central interval at a level,
   or the estimate's standard error on the scale's additive form. A float, a
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
   estimand is built against the typed claim it answers, carries that claim's
   identity, and cannot be built outside the claim's operator declaration
   (§7.1); the write boundary then checks the spec's estimand names both the
   claim identity and the operator its *target record* carries (§7.2), which
   construction cannot see and which a stored record carries as two
   independent members.
   Whether the measured quantity actually
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
9. **One inhabited fragment, and anything richer refuses.** A two-level
   contrast, or a continuous one with a named quantity and increment, on one
   slot; one measured quantity; one reference; one
   identification; one flat conditioning set. Multi-arm contrasts,
   interactions, an attenuation across two conditioning sets, time-varying
   estimands and censoring specifics are refused at construction with the
   fragment named, never flattened into the fragment (§3.3). Flattening is the
   scope-widening failure kernel §4.1 exists to prevent, committed by an
   encoding.
10. **A corpus is recreated under the new base contract, never migrated,
    and a pre-grammar record is refused by name.** The spec facet and the
    assessment facet take canonical typed projections, and every spec facet
    projection now carries the grammar it was frozen under
    (`estimand_grammar: science.estimand.v1`). A stored projection with no
    grammar member is a **pre-grammar** record: `restore` and
    `analysis_spec_value` refuse it with `UnfreezableSpec("pre-grammar
    spec")`, `assessment_value` refuses a prose-fielded facet with
    `MalformedRecord("pre-grammar assessment")`, the audit reports each
    under its own code (`spec-pre-grammar`, `assessment-pre-grammar`) and
    never as `derivation-malformed` in a corpus pinned to the successor base
    — a corpus still pinned to a pre-grammar base audits as
    `profile-mismatch: base` before any record is read, the existing rule,
    preserved — and **no reader coerces prose into a
    typed member**. There is no `revise` across the shape change, because
    `revise` copies members from a restored original and a pre-grammar spec
    does not restore; there is no `supersedes` edge either, since a
    successor edge asserts a semantic edit of a record the successor's
    corpus does not hold. The transition is the one the corpus already
    made at cut 22 for the claim identity: the driver **recreates** the
    reproduction corpus from the predecessor's records under the new
    contracts, the prior corpus state survives in history, and the addendum
    cites the prose spec's identity as text. Exactly one frozen spec and one
    assessment exist today, both the reproduction's. Belief input digests
    move for every corpus, as verification-publication decision 12 already
    made them. Rejected: a coercing reader that types a prose estimand on
    the way in (it would mint an estimand nobody authored, under a claim
    nobody checked); a `PreGrammarSpec` arm that restores and is inert
    (every consumer of `FrozenSpec` would grow a branch for a record no
    corpus needs to hold).
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
  uncertainty_kinds: [interval, standard-error]
```

Three closed sets, all **structural**: each member is defined by an operation
the kernel performs, not by a label the kernel carries. A `levels` contrast
requires two bound levels and a `continuous` one forbids them; an `additive`
scale compares estimate to reference by difference and a `multiplicative` one
by ratio, so the sign constraints in §6 differ; an `interval` carries two
bounds and a level, a `standard-error` one non-negative width on the scale's
additive form, each with the single meaning §6 fixes. That is the test
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
Estimand(c)   =  { claim      : I_claim(c) — the identity of the target claim the estimand answers
                 , operator   : the term identifier of op(c)
                 , contrast   : Contrast(op)
                 , measure    : { quantity : Referent(MeasureSort(op)),  scale : additive | multiplicative }
                 , reference  : Decimal                          -- finite; > 0 when multiplicative
                 , control    : { identification : Referent(IdentificationSort(op))
                                , conditioning   : a set of Referent(ConditioningSort(op)), possibly empty } }

Contrast(op)  =  { slot : Fin(arity(op)), kind : levels
                 , baseline : Referent(LevelSort(op, slot)), comparison : Referent(LevelSort(op, slot)) }   -- distinct
              |  { slot : Fin(arity(op)), kind : continuous
                 , quantity : Referent(MeasureSort(op)), increment : Decimal }                            -- increment > 0

Applicability(op)  =  QualifiersFlat(op)          -- formal model §6.4, unchanged
```

Like `Claim`, an `Estimand` is a dependent sum, and it is indexed by the
**claim**, not merely by the operator: the claim's operator fixes the sorts
of every referent through the operator's `estimands:` declaration (§5.1), so
a referent of the wrong sort has no slot to occupy, and the claim's identity
enters the value so that the estimand says *which* proposition it answers.
An estimand of "PD against NDMM expression" at `affects-concept-molecular-
entity` is a different quantity for PHF19 and for EZH2, and the operator
alone cannot tell them apart; the bound arguments can, and `I_claim` is
their canonical carrier (M5, M8). `operator` is stored beside it so that a
decoder holding a profile and no view can still validate sorts (§7.2).

A `continuous` contrast names the **quantity by which the slot varies** and
the **increment** the estimate is per. "Per one unit" and "per ten units"
of the same quantity are two estimands, as are "per unit of TPM" and "per
unit of log₂ TPM". The convention is fixed once: the increment is
**additive on the quantity as named**, so a multiplicative step — per
doubling, per ten-fold — is expressed by naming a log-scaled quantity and an
additive increment on it, never by a second scale tag on the contrast.

`baseline` and `comparison` are named, not a sorted pair, because direction is
part of the quantity: "PD against NDMM" and "NDMM against PD" are two
estimands with opposite signs, and collapsing them would let two studies
with opposite conventions read as one key (§7.3). The kernel does not flip
one into the other; a successor policy may define a flip, and this design
defines none.

`reference` is the value the **contrast** takes when the claim is false —
zero on an additive scale for "no difference", one on a multiplicative
scale, a noninferiority margin as the number it resolves to — and never the
value of a level. The baseline level's value is something the run
computes; a null expectation estimated from data during execution (a
surrogate ensemble's mean, a permutation distribution's centre) is the
baseline level, consumed inside the rule, and has no claim on this slot
(Appendix A). The reference is data-independent by the order of events,
not by its type: the spec freezes before the run that is bound to it.

**Canonical projection.** `claim`; `operator`; `contrast` as `{slot, kind}`
plus `{baseline, comparison}` when `kind` is `levels` and `{quantity,
increment}` when it is `continuous`, each referent as `{sort, term}` and the
increment as canonical decimal text; `measure`; `reference` as identity v1's canonical decimal
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
- any time index, censoring rule or repeated-measures structure — a
  **design's** time structure, carried in `method` and `assumptions` as
  today. A statistic's own parameters — a lag, a scale, an embedding
  dimension — are not this: they are members of the measured quantity's
  term, as "log₂ TPM" is a term and "TPM" another (Appendix A).

Each is a real expressive limit, recorded as the boundary of this pass.

## 4. Applicability

`applicability` becomes `QualifiersFlat(op)` over the target operator's
declared dimensions, built by the claim module's own qualifier construction:
an undeclared dimension, a second restriction on one dimension, an unbound
restriction referent or a quantifier outside the base set refuses exactly as
it does for a claim. The empty map is admitted and means the estimand adds
no restriction, along the operator's declared dimensions, beyond the ones the
proposition already carries.

**What applicability is, and what it is not.** It restricts along the
operator's **declared dimensions only**, because that is the one structure
canonical equality can compare. Exactly one other thing a prose
"applicability" habitually carries has a typed home already: the **dataset**
— "samples of gse179929" — is the run's `observes` input, stamped in the
closure and read by lineage and independence, and restating it in a
qualifier would carry the same fact twice. Nothing else does. In particular
the `observes` set names *which datasets* were read and not *which rows* the
analysis kept, so a sample selection — adults only, first-relapse only, rows
with a finite value — is **not** carried by it, and the inline exclusion
certification (computation §5.2) is a different thing again: it removes a
`reads` input from the lineage closure and says nothing about rows.

Retyping an existing spec therefore admits exactly two dispositions per
clause of its prose applicability — **typed** along a declared dimension, or
**dropped** as a restatement of an `observes` dataset — and **refuses** every
other clause, quoted, with no third home: not `assumptions`, not `method`,
because a scope restriction moved into prose is a scope restriction the typed
comparison can no longer see. A refused clause that restricts along a
scientific attribute asks the operator's successor to declare the dimension
(ρO4's population vocabulary is the obvious first). A refused clause the
author judges to be estimator behaviour rather than scope — how missing
values are handled — is **re-authored** as a new spec under the grammar, in
the recreated corpus decision 10 rules, with `method` stating the
behaviour; the new spec's scope is what its typed fields say, it carries no
`supersedes` edge to the prose one, and the design does **not** certify the
two equal in scope. The reproduction's clause is the second case and is
worked in §9.

**The limit this leaves, stated once.** The key (§7.3) and the match (§7.2)
see scope only through declared dimensions. Two specs over one dataset, one
of which keeps only adults by a rule written in `method`, carry identical
typed applicability and one commensuration key, and nothing here detects
it. The kernel cannot read prose; what it can do is refuse to *import* such
a clause from prose at retyping, which this section does, and make the
typed route the cheap one, which declaring the dimension is. Limitation 9
carries this.

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
Uncertainty  =  { kind : interval,       low : Decimal, high : Decimal, level : Decimal }   -- low ≤ estimate ≤ high; 0 < level < 1; low > 0 when multiplicative
             |  { kind : standard-error, value : Decimal }                                  -- value ≥ 0
```

Each kind has exactly one meaning, fixed here so that a successor policy
reads every rule's output the same way without knowing the rule:

- an **`interval`** is the two-sided central interval at coverage `level`
  around the estimate, on the estimate's own scale; whether it is a credible
  or a confidence interval is the rule's business and the kernel does not
  record it, since both are read by their width;
- a **`standard-error`** is the standard error **of the estimate** on the
  scale's **additive form**: on the estimate's own scale when the scale is
  `additive`, and on the natural logarithm of the estimate when it is
  `multiplicative` — the form in which a log hazard ratio or log odds ratio
  reports it. A dispersion of the *data* (a standard deviation, an
  interquartile range) is not an uncertainty of the estimate and has no
  kind here; a rule wanting to report one has `method` and its artifacts.
  The randomness a standard error is *over* is the randomness the estimand
  leaves open: for a quantity defined over a held dataset — a contrast of
  the series as held against a declared surrogate procedure applied to it
  — that is computational (Monte Carlo) randomness alone, and its Monte
  Carlo error is the estimate's standard error; a null distribution's own
  dispersion is a dispersion of generated data and has no kind (Appendix
  A). What a fresh sample would show is a different estimand's question.

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
build_estimand :  WireEstimand × Claim × ProfileSpec × ResolutionSnapshot
                  ──▶  (Estimand × BindingCheckReceipts) + Refused
```

The claim module's discipline, one artifact over. The estimand is built
against the **typed claim** it answers — the opaque `Claim` the author
already holds, since a spec's author typed or resolved its target before
freezing — and takes its `operator` and `claim` identity from it; a
`WireEstimand` carries neither. The snapshot is in the signature so two
holders cannot build identical bytes differently; every referent — both
levels or the contrasted quantity, the measured quantity, the
identification, each conditioning member — is resolved under D3's five
outcomes, and **only `not-member` refuses**; `not-consulted` mints and
emits a receipt, as it does for a claim (ρO1's persistence question is
unchanged and reaches one more producer). Refusals, each `Refused` with the
position named: the claim's operator declares no `estimands:` entry; `slot ∉
Fin(arity)`; `kind: levels` on a slot with no level sort; `kind: continuous`
with levels supplied, or without a quantity, or with an increment that is
not a finite `Decimal > 0`; one level, or two equal levels; a referent whose
sort is not the declared sort for its position; a duplicate conditioning
member; a tag outside a closed set; a `reference` that is not a finite
`Decimal`, or `≤ 0` under `multiplicative`; anything §3.3 names.

`build_applicability` is the claim module's qualifier construction over the
same operator, and refuses as §4 states.

### 7.2 The boundary — where the target is checked

Construction sees a claim; it cannot see the spec's `target`, which is a
corpus ref (`target: str`) that only a view resolves, and nothing at
construction proves the claim handed in is the one that ref names. The
check that the estimand answers the *record* the spec targets therefore
lives at the seams that hold a view:

| seam | check | on failure |
|---|---|---|
| `CorpusWriter._refuse` for an `analysis-spec` record — a new `_refuse_estimand_target_mismatch` beside `_refuse_r20_contradiction` | resolve `spec.target` in the writer's view; decode its claim; require **both** `spec.estimand.claim == I_claim(decoded)` **and** `spec.estimand.operator == decoded.operator`, and `spec.applicability` over `Dims(decoded.operator)`. At construction the identity entails the operator; a **stored** estimand carries the two as independent members with no claim preimage, so a record pairing the target's true hash with another operator and a payload correctly typed under it decodes cleanly, re-digests cleanly, and is caught only by the second equality | `ValidationRefused("estimand-target-mismatch")`; an unresolvable target is `ValidationRefused("estimand-target-unresolvable")` — cross-corpus targets are `world-resolution`'s read (§13) |
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
replay path and the driver's `rederive`). A projection lacking the
`estimand_grammar` member, or an assessment facet whose `estimand` is a
string, is a **pre-grammar** record and refuses under decision 10's named
reasons; the audit's spec and assessment checks report `spec-pre-grammar`
and `assessment-pre-grammar` as their own codes, so a recreated corpus that
somehow still holds one is told which record and why, and a reader never
repairs it.

### 7.3 Commensuration

```text
key(e)               =  π_estimand(e) with control.identification removed
commensurable(a, b)  =  key(a) == key(b)
```

Total over any two admitted estimands, decidable by projection equality, and
**unread by `science.belief.v1`** — P6 says v1 reads no magnitude-bearing
field, and this predicate reads them all. Because `claim` is in the
projection, two estimands are commensurable only when they answer **one
claim**: the same contrast and measure over PHF19 and over EZH2 are two keys,
as are the same over "in adults" and "in all humans", and no policy can pool
them by accident. That is the right grain, since aggregation is per
proposition (kernel §4.2.1) and the key is asked of assessments already
gathered under one. It is exposed from `beliefs.estimand`
so the successor policy has its key domain; whether non-commensurable inputs
to that policy refuse, exclude or answer `NoBelief` is the question belief
policy §2.1 deliberately declined to reserve an arm for, and it stays that
successor's.

Identification is the one member outside the key because it is the design
key a weight table reads: a longitudinal and an observational estimate of the
same quantity are the same quantity, weighted differently. Conditioning is
inside the key because a different conditioning set is a different quantity
(decision 4).

**Applicability is outside the estimand, so it is outside this key, and a
second predicate carries it:**

```text
co_scoped(a, b)  =  π_applicability(a) == π_applicability(b)      -- canonical map equality, M5's
```

Two specs on one claim with identical estimands and different typed
applicability maps — one licensed for `population ↦ ⟨generic, adults⟩`,
one for the empty map — are `commensurable` and **not** `co_scoped`. A
successor policy that pools on `commensurable` alone pools a subgroup with
the whole; the successor's design reads **both** predicates, and the rule
it adopts for estimands that are commensurable and not co-scoped —
exclude, refuse, or weight — is its own. `co_scoped` is exposed beside
`commensurable` from `beliefs.estimand` and, like it, is unread by v1.
Folding applicability into the estimand was rejected in §4 and stays
rejected; two predicates over two fields is the shape kernel §4.2.1's
table already has.

## 8. Guarantees — table Q

Certified by mutation per the estimator doctrine; every check must be able to
fail (N2). Rows are `Q1`–`Q10`; the table is owned here and registered in the
corpus inventory when the design moves to `docs/designs/` at freeze.

| # | guarantee | mutation test |
|---|---|---|
| **Q1** | The estimand's structure is kernel-owned and closed | A base contract lacking `estimand_grammar` → **refused** at load; a domain contract declaring `estimand_grammar`, `contrast_kinds`, `scales` or `uncertainty_kinds` → **refused** at load; a `tag_encoding` other than `science.identity.v1` → refused; `build_estimand` with `kind`, `scale` or an uncertainty `kind` outside its set → **refused**. **Sabotage:** widen a closed set in the implementation without editing the contract and assert the shipped base-contract fixture **fails** |
| **Q2** | `estimands:` is domain-issued, operator-bound and succession-governed | An entry keyed by an operator the contract does not declare → refused at load; an unresolved sort → refused at compile with the missing namespace named; an arity-0 operator → refused; a `level_sorts` index outside `Fin(arity)` or duplicated → refused. **Succession:** a successor adding an entry for an operator that had none → **accepted**, with the operator's own `schema_projection()` byte-identical (M6 unamended); changing any of the four members → `SuccessionViolation`; dropping an entry → `SuccessionViolation`; retiring the operator → the entry survives as a tombstone. **Negative:** reorder `level_sorts` keys and assert the contract's content identity and the projection are **unchanged** |
| **Q3** | An estimand is unconstructible outside its claim's operator declaration, and refuses rather than flattens | Each refusal in §7.1, one fixture each, asserting the position named; a wrong-sorted level, contrasted quantity, measured quantity, identification and conditioning member each **refused**; a continuous contrast with no quantity, or with an increment of `0`, negative, or a `float` → **refused**; `not-member` refuses and `not-consulted` **mints** with a receipt, and the five outcomes stay distinct (D3 preserved). **Fragment:** three levels, two slots, a second measure, an attenuation pair → each refused with the fragment named, and assert **no flattened estimand** is reachable. **Opacity:** `Estimand` has no public field-wise constructor (M13's shape), and `claim` and `operator` are taken from the `Claim` handed in, never from the wire |
| **Q4** | `applicability` is a qualifier map over the target operator's dimensions, comparable and unread | An undeclared dimension, two restrictions on one dimension, an unbound restriction → refused; the empty map admitted; `applicability == claim.qualifiers` computed by canonical projection equality and **decidable in both directions**. **P6 preserved verbatim:** change only `applicability`, assert belief value unchanged and digest moved, and assert **no mismatch finding exists** to be emitted |
| **Q5** | Estimate and uncertainty are typed on the spec's scale, and the rule cannot move the reference | A rule yielding a `float`, a `str`, an interval with `low > estimate` or `high < estimate`, `level ∉ (0, 1)`, a negative standard error, or an estimate `≤ 0` under `multiplicative` → **no assessment**, an `AssessmentFinding` naming the violation, and never `inconclusive`; a rule output carrying `reference` or `scale` → the same. **Negative:** a rule yielding nothing but `outcome` mints as today, and `mm30-reproduction/outcome-file/v1`'s identity is **unchanged** |
| **Q6** | Structural match is checked at the write boundary and under audit; semantic match is not claimed | A spec whose estimand was built against a claim other than the one its target record carries → `ValidationRefused("estimand-target-mismatch")` — **including** a claim at the **same operator** with different arguments, or the same arguments under different qualifiers; a target the writer's view cannot resolve → `ValidationRefused("estimand-target-unresolvable")`; explicit import refuses the same; a raw-written mismatching spec is **not** refused on read and is caught **only** under audit with `spec-target-contradicted`. **The inconsistent stored pair:** raw-write a spec whose estimand carries the target's **correct** claim identity beside a **different** declared operator, with contrast, measure and control correctly typed under that operator and the spec digest recomputed; assert it decodes without refusal, that explicit import **refuses** it and audit **contradicts** it on the operator equality alone, and — **sabotage** — that comparing claim identities only lets it through. **Negative:** a measured quantity of the right sort that does not in fact operationalize the claim's argument is **admitted** — the check is structural, and the row asserts it does not pretend otherwise |
| **Q7** | Every member enters identity, and only members do | Change **only** `claim`, `contrast.slot`, `kind`, `baseline`, `comparison`, `contrast.quantity`, `increment`, `measure.quantity`, `measure.scale`, `reference`, `control.identification`, one `conditioning` member, or one `applicability` entry: the spec identity **moves** each time; reorder `conditioning` → **unchanged**; `increment` `1` against `1.0` → **unchanged** (identity v1's canonical decimal text). On the assessment: change only `estimate`, only `uncertainty`, only `estimand`, only `applicability` → the facet digest **moves**, the belief value is **unchanged** (P6's four arms, now per member); G3's keyed-facet arms unchanged. **Negative:** an editorial change to a consulted contract leaves `I_claim` unchanged (M8) |
| **Q8** | The estimand's contracts are consulted | Derive belief over an assessment whose estimand binds a measure sort declared in contract `X`; bump `X` touching no facet, no operator and no claim → `belief_input_digest` **moves**; bump an activated contract the estimand does not reach → **unchanged**; type an estimand under a sort pinned by no corpus → `ContractDisagreement`. **Sabotage:** drop the estimand walk from `consulted_contracts` and assert the first arm **fails** |
| **Q9** | Commensuration is total, decidable, and unread by v1 | For any two admitted estimands the predicate returns a boolean, never raises; equal except `control.identification` → **commensurable**; differing in any other member → **not**; `baseline`/`comparison` swapped → **not**; the same contrast and measure over two claims at one operator (PHF19 and EZH2) → **not**; per-unit against per-ten-units of one quantity → **not**. **The scope counterexample:** two specs on **one** claim with **identical** estimands and **different** typed applicability maps (`population ↦ ⟨generic, adults⟩` against `{}`) → `commensurable` is **true** and `co_scoped` is **false**; assert both predicates are exposed, both are total, and neither is read by v1's evaluator (**sabotage:** make `co_scoped` raise and assert every P row still passes). **Sabotage:** make the predicate raise and assert every P row still passes — v1 never calls it; **P5** still holds: no API path produces unequal weights |
| **Q10** | The reproduction recreates its corpus, re-authors its spec, and re-derives from disk | The driver recreates the reproduction corpus under the successor contracts (decision 10); the record's estimand builds with every referent resolving `member` against the held lists; the prose applicability's second clause is **refused** at retyping (§4), and the typed spec is minted by `freeze` with no `supersedes`; steps 4–10b re-run; the belief re-derives to the **same value** under a **different digest**; the consulted set is unchanged. **Then, in a fresh process** holding nothing in memory: restore the frozen spec through `analysis_spec_value` and the assessment through `assessment_value` from the corpus on disk, re-derive the assessment from its run and the belief from its closure, and assert both equal what the driver's process derived — the recovered-from-the-corpus-alone reading the reproduction record §5 question 3 required of verification. **The transition:** present the **prior** corpus state's prose spec and assessment to the same readers under the successor profile and assert `UnfreezableSpec("pre-grammar spec")` and `MalformedRecord("pre-grammar assessment")`, and that no reader returns a typed value for either; assert `audit_corpus` over that state under the successor profile reports `profile-mismatch: base` and nothing else — its pinned base contract predates the grammar and does not parse under the successor, so the existing profile-disagreement rule fires before any record is read and is preserved. The codes `spec-pre-grammar` and `assessment-pre-grammar` are exercised on a corpus **pinned to the successor** holding a raw-written pre-grammar record, and assert **not** `derivation-malformed` there. **Not asserted:** that the new spec's scope equals the prose spec's — the addendum records the authored judgment and no row certifies it. **Measured, not asserted** (§9) |

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
  token in gse179929", types as: `claim: 780ace59…` (the pack-typed
  identity, biology pack §6.4); `operator:
  mm30/affects-concept-molecular-entity`; `contrast: {slot: 0, kind: levels,
  baseline: NDMM, comparison: PD}`; `measure: {quantity: <expression>,
  scale: additive}`; `reference: 0`; `control: {identification:
  <observational>, conditioning: ∅}`; `applicability: {}`. The driver's
  prose applicability, "samples of gse179929 whose ids carry a stage token
  and whose value is finite", is two clauses. The first restates the run's
  one `observes` input and is dropped under §4. The second is **refused**:
  the operator declares no dimension it could be typed along, and §4 gives
  it no other home. The reproduction therefore does not *retype* its spec;
  it **re-authors** one by `freeze` in the corpus the driver recreates under
  the successor contracts (decision 10), with applicability `{}` and a
  `method` that states how the estimator treats a sample with no finite
  value. The prose spec is not restored, not revised and not superseded:
  it lives in the prior corpus state, and the addendum cites its identity
  (`86aaa1a8…`) as text, as the biology pack's re-run cited the replaced
  claim identity. The new spec's scope is what its typed fields say. **It
  is not certified equal in scope to the prose spec**, and Q10 does not
  claim it; the addendum records the author's judgment that the refused
  clause described estimator behaviour, as a judgment. The 285-member
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
rule output; drop the operator equality from
`_refuse_estimand_target_mismatch`, keeping the claim-identity one (Q6's
stored-pair arm selects it); drop the claim-identity equality, keeping the
operator one; drop `check_spec_target` from the audit
loop; drop the estimand walk in `consulted_contracts`; put `identification`
into the commensuration key; drop `claim` from the projection; drop
`increment` from the projection; admit an increment of `0`; take `claim` from
the wire instead of the `Claim`; drop `estimand:` entries from
`_declarations()`; drop the `estimand_grammar` member from the spec
projection; coerce a string estimand to a typed one in `restore`; report a
pre-grammar spec as `derivation-malformed`. Each sabotage is
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
  lane, `estimand-typing`, only when no on-path lane is startable (rule 6).
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
- **Building the estimand against an operator alone**, the first draft's
  shape. Review found it loses the bound arguments, so two claims at one
  operator shared a commensuration key and passed the target check. The
  estimand is now built against the typed `Claim` (§7.1) and carries its
  identity. What is still **not** done is letting that identity replace the
  spec's `target` ref: the spec keeps the corpus ref, the boundary requires
  the two to agree (§7.2), and the two-namespace question of the
  assessment's `proposition` member (verification-publication §9) stays with
  the layer design's claim sub-project, undecided here.
- **A `dispersion` kind left to each rule's convention.** A successor
  policy would then need per-rule knowledge to read a width; §6 gives the
  kind one meaning instead and names it for it.
- **Deferring continuous contrasts** until an increment could be
  represented. The increment and the contrasted quantity cost two members
  (§3.2) and make the hazard-ratio shape mm30's records carry expressible
  now, so the fragment includes them.
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
3. **Direction is not normalized, and neither is the increment.** Two
   estimands with swapped levels, or with increments of one and ten units of
   one quantity, are not commensurable here; whether a successor policy may
   flip one or rescale the other is that policy's ruling. The kernel fixes
   only the convention — an increment is additive on the quantity as named
   (§3.2) — so that the two are at least distinguishable.
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
9. **Sample selection outside a declared dimension is invisible to both
   predicates** (§4, §7.3). Two specs over one dataset, one keeping only
   adults by a rule stated in `method`, share typed applicability, so they
   are `commensurable` and `co_scoped` alike. The design refuses to import
   such a clause from prose at retyping and cannot stop a new spec from
   stating one in prose. Declaring the dimension — a contract successor
   and, for populations, ρO4 — moves the selection into `applicability`,
   where `co_scoped` separates it; it does not move it into the
   commensuration key, and a successor policy that reads only
   `commensurable` still pools it.
10. **The reproduction's typed spec is a new spec in a recreated corpus,
    not a retyping and not a successor**; its scope equality with the prose
    spec is an authored judgment the addendum records and no row certifies
    (§9, Q10). The prose spec survives only in the prior corpus state.
11. **A pre-grammar record is refused, never read.** A corpus that holds
    one after the lane lands is a corpus that was not recreated; the audit
    names the record and the reason, and nothing repairs it (decision 10).
12. **The interval constraint reaches as far as containment.** `low ≤
    estimate ≤ high` refuses an interval that is not around the estimate —
    a null distribution's central band, in the case where the estimate
    lies outside it — and admits one that happens to contain it under a
    label that is false. What the interval is an interval *of* is the
    rule's honesty, as limitation 1 says semantic match is the author's
    (Appendix A.4).

## 14. Task linkage

`beliefs-59f846` carries this spec; the implementation plan's tasks become
its children. `beliefs-638318` (weighted belief) depends on it and keeps its
own design gate. `beliefs-eacbe2` (the contract cut) gains it as a
dependency when the lane opens. The composite-claim design that answers
kernel §11's unplaced `inquiry` / `patch-definition` / `structural-chain`
kinds is the second spec the 2026-09-12 session agreed to and is filed
separately; it does not depend on this one.

## 15. Review log

- 2026-09-12, drafted in session from the models assessment.
- 2026-09-12, first review, four findings, all taken: (1) the reproduction's
  prose applicability was silently widened to `{}` — §4 now rules where each
  clause of a prose applicability goes (declared dimensions, the `observes`
  set, or `assumptions`), refuses a clause that fits none, and §9 works the
  reproduction's; (2) a continuous contrast carried only its slot, so per-
  unit and per-ten-units shared a key — §3.2 adds the contrasted quantity
  and the increment, with the additive-on-the-named-quantity convention;
  (3) the key and the target check saw the operator and not the bound
  arguments — the estimand is now built against the typed `Claim` and
  carries `I_claim`, which enters the projection, the key and the boundary
  check; (4) `dispersion` had no precision meaning — renamed
  `standard-error` and given one (§6), with the interval's meaning fixed
  beside it.
- 2026-09-12, second review, two findings, both taken: (1) a stored
  estimand carries claim identity and operator as independent members with
  no preimage, so identity equality alone admits a record pairing the true
  hash with another operator — §7.2 now requires both equalities, Q6 gains
  the inconsistent-pair arm and §10.3 two sabotages; (2) the `observes` set
  names datasets, not rows, so relocating a sample-selection clause into
  `assumptions` hid a scope distinction from the key — §4 now admits only
  two dispositions (typed along a declared dimension, or dropped as a
  restatement of an `observes` dataset), refuses every other clause,
  names the residual blindness as limitation 9, and §9 and Q10 make the
  reproduction's typed spec a `revise` successor whose scope equality is
  recorded as a judgment and certified by no row.
- 2026-09-12, third review, two findings, both taken: (1) the `revise`
  successor had no construction route, since `revise` copies members from a
  restored original and a prose spec cannot restore once restoration is
  typed, and a retained prose spec would audit as malformed — decision 10
  now rules the transition as recreation, never migration: the spec
  projection carries its grammar, a pre-grammar spec or assessment refuses
  under a named reason and audits under its own code, no reader coerces,
  and the reproduction re-authors by `freeze` in a recreated corpus with no
  `supersedes`; Q10 restores spec and assessment from disk in a fresh
  process and exercises the pre-grammar refusals against the prior corpus
  state; (2) applicability sits outside the estimand and so outside the
  commensuration key, so two specs on one claim with identical estimands
  and different typed applicability compared as commensurable — §7.3 adds
  `co_scoped` over the applicability maps, rules that a successor policy
  reads both predicates, Q9 carries the exact counterexample, and
  limitation 9 no longer names a declared dimension as a fix for the key.
- 2026-09-12, plan review, one spec consequence: the prior reproduction
  corpus pins a base contract that predates the grammar and cannot parse
  under the successor, so its audit reports `profile-mismatch: base` and
  never reaches the pre-grammar codes — decision 10 and Q10 now say so, and
  the codes are exercised on a successor-pinned corpus holding a raw-written
  pre-grammar record.
- 2026-09-15, worked example from a second domain (`beliefs-18b03d`; the
  natural-systems pilot's surrogate contrast, Appendix A), four findings,
  all taken and none structural: (1) §3.2 says what `reference` is — the
  contrast's null value, never a level's, data-independent by the freeze
  preceding the run; (2) §3.3's time-index refusal names what it excludes,
  a design's time structure, and puts a statistic's own parameters in the
  measure term; (3) §6 says which randomness a standard error is over, so
  a Monte Carlo error over a held dataset is admitted and a null
  distribution's dispersion is not; (4) limitation 12 records the reach of
  the interval containment check. The fragment admits the pilot's target
  with no member added, widened or re-sorted. The API half of the example
  is `beliefs-e48279`, after Task 4.

## Appendix A — a second inhabitant: the natural-systems surrogate contrast

**What this is.** The worked example task `beliefs-18b03d` asked for, from
the natural-systems v2 framing §4 and the time-series pilot design §7
(`natural-systems` `docs/specs/2026-09-13-time-series-pilot-design.md`),
worked 2026-09-15 against this draft before its freeze. It is a prose
mapping and a reading of the constructor's refusals as §7.1 states them;
its API half — the same fixture through `build_estimand` and the
`AssessmentValue` constructor once they exist — is `beliefs-e48279`, after
Task 4 and before Task 11. Findings on the draft are in A.5 and were taken
in the revision that adds this appendix (§15).

### A.1 The target

The pilot's opening surrogate assessment, stated once by its design §7 and
copied here so the encoding can be checked against it:

```text
T      =  CO_trev_1_num — the normalized lag-one cubed-increment time-reversal statistic (pycatch22)
Q      =  Fourier phase randomization under its finite-window approximation: magnitudes, mean,
          length, real-valuedness, DC and (even lengths) Nyquist preserved; independent
          positive-frequency phases randomized under conjugate symmetry
delta(D,Q)  =  T(D) − E_Q[ T(Q(D)) ]                               -- over one held finite series D
estimate    =  T(D) − mean_b T(Q_b(D)),  b = 1..B,  B = 999
uncertainty =  sd_b T(Q_b(D)) / √B  — the Monte Carlo standard error of the second term, conditional on D
outcome     =  two-sided rank comparison, (1 + #{|T_b| ≥ |T(D)|}) / (B + 1), at 0.05
```

Additive scale, fixed reference zero. The design is explicit that the MC
standard error "is uncertainty in estimating Q's expectation, not a
confidence interval for a world's property, not the surrogate distribution
itself, and not the uncertainty from recording a different trajectory".

### A.2 The encoding

A corpus-local contract for the pilot, on the mm30 shape (§5.1, §9): four
held one-line-per-term lists, one operator, one `estimands:` entry. The
pack question — which of these the eventual `natural-systems` pack owns —
is that project's and changes nothing below.

```yaml
contract: natural-systems-pilot
version: 1
lineage: genesis
sorts:
  series-source:          { vocabulary: { namespace: ns-pilot-series,     release: "<sample date>" } }   # one term per held series: a pilot record and variable, or a construction
  observation-procedure:  { vocabulary: { namespace: ns-pilot-procedures, release: "<sample date>" } }   # identity, fourier-phase-randomized, aaft, …
  statistic:              { vocabulary: { namespace: ns-pilot-statistics, release: "<sample date>" } }   # co-trev-1-num, … — one term per statistic *and its parameters*
  identification:         { vocabulary: { namespace: ns-pilot-identification, release: "<sample date>" } }   # within-series-surrogate
dimensions: {}
operators:
  departs-from-series-source-observation-procedure:
    arity: 2
    arg_sorts: [series-source, observation-procedure]
    sign_apt: true
    layers: [statistical]
    dimensions: []
estimands:
  departs-from-series-source-observation-procedure:
    level_sorts: { "1": observation-procedure }
    measure_sort: statistic
    identification_sort: identification
    conditioning_sort: statistic        # exercised by nothing here; a conditioning member would be another statistic of the same series (A.6)
```

**The claim.** `departs-from-series-source-observation-procedure(⟨record⟩,
fourier-phase-randomized)`, polarity `unsigned` (the pilot's test is
two-sided), layer `statistical`, qualifiers `{}`. Read: *the series
⟨record⟩ departs from what Fourier phase randomization of it produces.* In
which quantity is the estimand's to say, exactly as mm30's claim says
"affects" and its estimand says "expression" (§9). A domain that wants the
statistic in the proposition adds a third argument of sort `statistic`;
the kernel is indifferent, and this example does not.

**The estimand**, member by member against §3.2:

| member | value | why it fits |
|---|---|---|
| `claim`, `operator` | `I_claim` of the claim above; the operator's term | taken from the typed `Claim` (§7.1) |
| `contrast` | `{slot: 1, kind: levels, baseline: fourier-phase-randomized, comparison: identity}` | slot 1 is the procedure argument, whose level sort is `observation-procedure`; `comparison − baseline` is `T(D) − E_Q[T]`, the pilot's sign. The identity procedure is a member of the same sort as the null: "observe D as held" is a procedure, and the contrast is between two procedures applied to one series |
| `measure` | `{quantity: co-trev-1-num, scale: additive}` | the lag, the increment power and the normalization are **members of the term**, as "log₂ TPM" is (§3.2); a second lag is a second term and a second estimand. `additive`, because the statistic is signed |
| `reference` | `0` | the value of the **contrast** when the claim is false. Not `E_Q[T]`: that is the baseline **level's** value, which the run computes. The framing's worry — a null expectation estimated during execution "does not fit that slot" — is answered by what the slot means, not by an extension. Frozen before the run because the run is bound to a frozen spec (computation guide) |
| `control.identification` | `within-series-surrogate` | corpus-local, as §13 limitation 4 says every identification vocabulary is today |
| `control.conditioning` | `∅` | the null's preserved properties (spectrum, mean, length, DC, Nyquist) are the **definition of the baseline term**, held in its list entry and stated in `method`; they are not covariates whose conditioning changes the quantity (decision 4) |

**Applicability** is `{}`: the operator declares no dimension, and the
series is the run's one `observes` input, which §4 drops as a restatement.
The pilot's burn-in and retained window are not a scope clause: a run that
windows D in `method` and a run that windows it differently share one key
(§4's stated limit, limitation 9). The alternative — producing the retained
window as its own dataset — meets A.4.

**Estimate and uncertainty** against §6: `estimate` is the `Decimal`
`T(D) − mean_b T_b` on the additive scale; `uncertainty` is
`{kind: standard-error, value: sd_b / √B}`. The kind is admitted **because
the estimand is `delta(D, Q)` over the held D**: with D fixed, the only
randomness the estimate has left is Monte Carlo, so the Monte Carlo error
*is* the standard error of the estimate, on the additive form. The surrogate
distribution itself — `sd_b`, or its quantiles — is a dispersion of
generated data and has no kind, which is §6's exclusion holding, not
bending. A statement about the *generating process* — what a fresh
trajectory would show — is a different claim (its slot-0 term names a
process, not a series), a different estimand, and an uncertainty nothing in
this example computes. `outcome` is `supported` when the rank rule rejects
and `inconclusive` otherwise; it is never `refuted`, since failing to reject
a departure is not evidence of the null (the pilot says so). The p-value has
no field and stays in the run's result bytes and the rule's own record —
the F11 hazard is the reason it has none, and the estimate and its standard
error are what the field carries instead.

### A.3 Where the surrogates enter the run, and what they are not

The execution recipe observes D, carries `B` and the surrogate scheme's
parameters as `parameters`, and declares `nondeterminism: Seeded` with a
seed plan; the occurrence records the realized seeds; the declared output
bytes are `T(D)` and the vector of `T(Q_b(D))` with their seeds. The
interpretation rule reads that result manifest and reduces it to
`{outcome, estimate, uncertainty}` — the reduction (mean, `sd/√B`, the rank
rule at 0.05) is interpretation, so it has a rule identity; the generation
is execution, so it has an occurrence. **No surrogate is a dataset.** None
is held, none carries a facet, none enters lineage, and the open question on
lineage-inherited empirical standing is not reached. It would be reached only
by a surrogate *bank* held once and observed by many runs, which the framing
does not ask for and this example does not encode.

### A.4 What refuses, and that it should

Read against §7.1 and §6; each is an arm the API test (`beliefs-e48279`)
asserts.

- **A surrogate family as one contrast** — identity against
  phase-randomized *and* AAFT — is three levels on one slot and refuses at
  the fragment (§3.3). One scheme per estimand; a family is several
  estimands on one claim, each with its own key. The framing's phrase "the
  surrogate family as baseline" names one member of it.
- **A lag range searched** as a `continuous` contrast over lag refuses: lag
  is no argument of the operator, so there is no slot for it
  (`slot ∉ Fin(arity)`). One estimand per `(statistic, lag)` term; the search
  is a multiple comparison in the rule and `method`, which is where the
  framing already puts it.
- **`reference: E_Q[T]`** is a finite `Decimal` and the constructor admits
  it. What makes it impossible as a *data-dependent* number is the order of
  events, not the type: the spec freezes before the run that would compute
  it. An author who runs first and freezes after is telling a lie the
  constructor cannot see; limitation 1's shape, and A.5's finding 1 says so.
- **The null's central interval as `uncertainty`** —
  `{kind: interval, low: q₀.₀₂₅(T_b) − mean_b, high: q₀.₉₇₅(T_b) − mean_b,
  level: 0.95}` on the contrast's scale — is caught by `low ≤ estimate ≤
  high` **exactly when the rank rule rejects**, since a rejecting estimate
  lies outside the null's central band by construction; when the rule does
  not reject, the interval contains the estimate and is admitted under a
  label that is false. The check does what a structural check can;
  limitation 12 records the rest.
- **A synthetic control series** — the pilot's seeded AR(1) arms, produced
  by a dataset-production run — cannot bear the `empirical-observation`
  facet (`acquisition.bearer_refusal`: a produced dataset is refused as a
  bearer), so an assessment run observing it refuses its `assesses` edge
  with `EligibilityUnmet` (S7). The calibration and power controls are runs
  with results and no assessment of any proposition — which is what the
  pilot design §7 says it wants ("the ordinary held-dataset result can exist
  before that typing question is settled") and is the non-empirical route
  question's territory, not this design's. The same rule means the **retained
  window**, if produced as its own dataset, cannot be observed by the
  assessment run either: the run observes the acquired series and windows
  in-run.

### A.5 Findings on the draft, all taken in this revision

1. §3.2 did not say what `reference` *is*, and the framing read it as a
   slot for the null's expected value. It now says: the contrast's value
   under the null, never a level's value, frozen before the run by the
   run's binding to a frozen spec.
2. §3.3's "any time index" read as excluding a statistic's own time
   parameter. It now says what it excludes — a design's time structure:
   repeated measures, censoring, survival time — and that a statistic's
   parameters (a lag, a scale, an embedding) are members of the measured
   quantity's term.
3. §6 fixed the standard error's meaning as "of the estimate" and left
   *over what randomness* to the reader. It now says: over the randomness
   the estimand leaves open, which for a quantity defined over a held
   dataset is computational randomness alone, and that a null
   distribution's own dispersion has no kind.
4. §6's interval constraint is a structural check with a stated reach: it
   refuses a null-band interval in the rejection case and admits it,
   mislabelled, otherwise. Limitation 12 records this.

No structural finding: the fragment admits the pilot's target as drafted,
with no member added, widened or re-sorted.

### A.6 What this example does not establish

- A **conditional** statistic — the pilot's partial correlation at lag one
  conditioned on the series' own lag — would put the conditioning term in
  `control.conditioning` under `conditioning_sort: statistic` (decision 4:
  it changes the quantity). Spellable; not worked.
- A **pairwise** or network claim between two series sources (the pilot's
  cross-correlation and PCMCI rows) is an arity-2 operator over
  `series-source` twice with a levels contrast on a procedure slot it must
  also declare — arity 3 — or a continuous contrast. Not worked; the
  "compare maxima, not the best lag" rule types as one statistic term
  (`ccf-max-abs`) and the arg-max lag as a claim about a different quantity,
  refused as a second measure (§3.3) and correctly so.
- A **process-level** claim — generalizing from the held series to its
  source — is a different claim with an uncertainty over trajectories that
  no surrogate scheme supplies. Not worked; A.2 names it as out of reach.
- A **held surrogate bank** reused across runs, and any derived dataset's
  empirical standing. Not asked; A.3.
- **Multi-product workflows.** Not asked (framing §4); nothing here needs
  one.
