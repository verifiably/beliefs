# Computation and reproducibility — design

**Date:** 2026-08-02
**Status:** design
**Scope:** sub-problem 4 of 7 in the system redesign
**Depends on:** [`2026-08-02-epistemic-kernel-design.md`](2026-08-02-epistemic-kernel-design.md),
[`2026-08-02-substrate-consolidation-design.md`](2026-08-02-substrate-consolidation-design.md),
[`2026-08-02-world-addressing-design.md`](2026-08-02-world-addressing-design.md)

## 1. Why

The kernel's invariant — *only an assessment successfully reproduced from primary
observations we possess may affect empirical belief* — rests on three objects it
names but does not specify: the **run**, its **closure**, and the **analysis
spec** whose hash must precede it. This document specifies them, and rules on
what happens to the machinery already built for a weaker version of the same
contract.

### 1.1 The contract is complete, enforceable, and governs nothing

`t077` (the analysis-run reproducibility contract, shipped `beeff218`) is a
finished piece of work: a tri-state fingerprint model, a frozen obligation table
with an import-time reconciliation gate, graph-phase run resolution, and a
determinism test forbidding disk probes from reaching the obligation logic. It is
the closest thing the current system has to this design.

Measured across every Science project on this machine:

| record | count | state |
|---|---|---|
| `workflow-run` | **15** | **0 carry a `fingerprint`; 0 carry an `execution` declaration** |
| `workflow` / `workflow-step` / `method` | 20 / **0** / 78 | — |
| `dataset` | 1,036 | 15 name a `workflow_run`; 5 recipe-only; 1 `produced_by`-only; **1,015 no provenance at all** |
| `evidence-line` | 1,065 | 624 empirical; 907 carry `dataset_usage`; **0 carry `run_refs`** |
| `pre-registration` | 209 | prose documents: no typed entity, no hash, no edge to any run |
| `proposition` / `paper` | 824 / 2,332 | — |

The method-representation umbrella design recorded, on 2026-07-09, that there
were **zero** `workflow` / `workflow-run` / `workflow-step` / `method` entities
anywhere, and concluded that `t077` "shipped an enforceable contract over an
empty population." That measurement is now stale in its numbers and stronger in
its point. The population is 15 runs, **none of which satisfies the contract**,
under 624 empirical evidence lines that resolve to zero fingerprinted runs.

> **The admissible-assessment count today is zero.** This design is not migrating
> a working mechanism. It is specifying one for the first time, and the absence of
> a population is what makes every ruling below cheap.

### 1.2 The spec has no representation, so the ordering guarantee has no subject

Kernel §3.1 puts the analysis-spec hash first in the closure, and G2a requires it
to predate the run — **refusal, not downgrade**, when it does not. Nothing in the
shipped model can hold it. `RunFingerprint` has no spec field; its nearest
analogue, `parameters_digest` over `config_snapshot`, is parameters, not target,
estimand, interpretation rule or equivalence rule. The 209 pre-registrations are
prose documents governed by section checks (`validate/checks/prereg.py`), with no
identity and no edge to a run.

So G2a currently has no subject. §3 gives it one.

A second consequence follows immediately and is worth taking now: `seed_policy`
is observed on the run, while the equivalence rule is pre-declared in the spec.
A run declaring `stochastic-unseeded` under a spec declaring bitwise equivalence
is a contradiction **detectable before execution**. Today neither half is
representable, so nothing can see it. §3.1a puts both halves in one frozen facet
and settles which contradictions are refused by the type and which stay checks.

### 1.3 What was reused, and what was retired

The audit that opened this sub-problem kept ten mechanisms from `t077` and
retired four. Recorded here so the plan does not re-derive either list.

**Kept.** The declaration/observation split (`RunDeclaration` vs
`RunFingerprint`, from `t093`) — a human authors what is asserted, the tool
writes what is observed, validate re-checks agreement. The frozen versioned
obligation table with an import-time reconciliation gate, which is the
"predicate, not roster" pattern already implemented. The rule that **obligation
is never a function of what validate can observe on disk**, pinned by the
determinism test — *identical verdict with the run's data files present and
absent* — which is world §5.1's `not-present` ≠ `unknown` proved a layer down,
before that design existed. "Code is not a run; recipe is not a run." The
requirement that a manifest entry carry a content-identifying field and fail loud
on a bare path, because "a bare path is stable across content changes." The
content-freeze rule of `validate/checks/prereg_vehicles.py`. And, from
`audit/fingerprint.py`, **two** mechanisms that generalize: **domain-prefixed
digests** — `sha256(domain + "\n" + canonical bytes)` — and **rejection of
post-normalization key collisions**, which `normalize_identity_qualifiers`
already performs.

That module's strict *value* contract does **not** generalize, and its
**recursive null pruning is actively wrong for identity** — it makes
`{"x": null}` and `{}` the same bytes. §4.3 states what must be built instead.
This corrects a claim made in the audit that opened this sub-problem, and a
second one made in the first revision of this document.

**Retired**, each for a reason stated where it arises: the tri-state
`FingerprintComponent` as persisted run state (§2), `ExecutorKind.COMMONS` and
`CaptureOrigin` (§2.3), `step_seeds` keyed by authored `workflow-step` refs (§6),
and the entire dataset-walk run-resolution apparatus (§12).

## 2. The ruling — a run is a complete closure, or it is not a run

> **Rule.** A persisted `run` carries a **complete, held, content-identified
> closure**. No component may be `unknown` or `attested`. A record that cannot
> supply every member of its closure is **not a weaker run** — it is not a run.

This is world §4.2 applied to the kind that design already assigned a basis:
*"`run` — content identity of the execution closure."* A closure containing an
`unknown` component has no content to identify, and an `attested` value is
supplied by a party we do not trust, which would make a run's **address** partly
chosen by someone else. The same rule already refuses a `source` with no
identifier and a `dataset` with **no content identity** *(narrowed 2026-08-09,
admission ramp §6.4; this read "holding no content", which conflated identity
with holding)*; nothing new is being invented.

**`unknown` is a refusal result, not persisted state.** The tri-state discipline
may survive at the import/capture boundary, where a capture that fails to observe
a component must say so in order to refuse — but it does not reach the stored
record. What is stored is what was observed, entire.

**"Held" binds every member, including the ones that look like metadata.** The
word is easy to read as applying only to data inputs, and §4.4 and §4.5 are where
it bites hardest: a code bundle that omits an untracked file, or an environment
named by a lockfile rather than held as artifacts, produces a record that looks
complete and is not. Both are refusals under this rule, not degradations of it.

### 2.1 "Captured" does not mean "executed in this checkout"

The rule is about closure completeness, not about who ran it.

> A complete run published by another corpus **remains a run**, provided its
> closure and artifacts are held and resolvable. Locality of execution is not an
> identity property and confers nothing.

This matters because the obvious reading of "we ran it ourselves" would make
belief depend on which repository a computation happened in, and one world (§8)
has no such category.

### 2.2 What an incomplete external report is instead

A paper's methods section, a collaborator's description of what they ran, a
commons record whose closure was never captured: these are claims about what
someone did. The kernel already types them — **a source assertion, or a note.**
They are not runs, they produce no assessment, and they are not degraded runs
sitting in a lower tier.

This intentionally loses the ability to call an incomplete imported record a
"run". It loses **no admissible evidence**, because such a record could never
have produced an admissible assessment under the kernel's eligibility predicate,
and it avoids carrying a second, weaker run concept whose only function would be
to look like the first one in listings.

### 2.3 Two enum casualties

`ExecutorKind.COMMONS` and `CaptureOrigin` exist to model a *producing* project
capturing facts and a *consuming* project importing a verified copy —
`origin_project`, `origin_run_ref`, `source_digest`, `capture_policy`. Under one
world there is no copy: a commons run is a run in another corpus, reached by the
world resolver, and world §9 already retires promotion because "one space has
nothing to promote to." With no copy there is no origin to record, and no second
policy version to track — the record's own policy version says what it was
authored under.

`ExecutorKind` therefore does not survive as a three-way key. What remains of the
distinction it drew is §2's binary, and that binary is not a field: **we observed
the execution, or the record is not a run.**

`ArtifactLocality` goes the same way for the same reason. It keyed obligations on
whether artifacts were Science-managed or external; under §2 every closure member
is held and content-identified, so there is one obligation and nothing to key.

## 3. The analysis spec is the pre-registration

> **Rule.** The structured `analysis-spec` is **primary, and it is the
> pre-registration.** There is no second authoritative record of what was planned.

### 3.1 The normative facet

The spec's typed facet is normative — validated, hashed, and the thing every rule
below refers to:

| field | content |
|---|---|
| `target` | the proposition this spec assesses |
| `estimand` | what quantity is being estimated, at what scope |
| `method` | the analytical procedure — what is done to the inputs to produce the estimand |
| `assumptions` | the conditions under which the method licenses the estimand |
| `falsification` | what result would count against `target`, declared before the result exists |
| `input_roles` | which datasets are `observes`, which are `reads` (kernel §4.1) |
| `applicability` | the scope the estimand licenses, which may be narrower than the proposition (§3.1b) |
| `interpretation_rule` | a **versioned rule identity** mapping the run's result to an outcome payload (§3.1b) |
| `equivalence_rule` | when two executions' outputs count as the same result (§7.2) |
| `parameters` | the declared parameter set |
| `nondeterminism_contract` | a **discriminated union** — `deterministic`, `seeded` (carrying a complete seed plan), or `stochastic-unseeded` (carrying a rationale) — §3.1a |

**`method`, `assumptions` and `falsification` are separate fields because the kernel
says they are separate things.** Kernel §4.4 absorbs `method`, `assumption` and
`falsification` into `analysis-spec` "as fields/refs", and kernel §11 adds that they
"are not semantically identical to each other and should not be collapsed into one
field by default." An earlier revision of this table carried none of them, and since
§3.1 also rules the Markdown body non-authoritative, they had **nowhere to live**:
the kernel had assigned three kinds to a home that did not admit them.

Each may be an inline field or a **ref to a content-addressed artifact**, and both
representations **participate in identity** — a ref hashes as its content address,
without dereferencing. Saying the choice "does not affect spec identity" would have
been wrong twice: switching a field to a ref changes the canonical facet bytes and so
mints a successor spec, which is correct and should be visible; and hashing a ref by
*dereferencing* it would make spec identity depend on whether the artifact is
resolvable here, which is the availability-dependent identity R5 and world §4.2 both
refuse. A ref's content address is the whole of what identity sees.

`plan`, `pre-registration` and `spec` from that same kernel row need no fields —
they are names for **the spec itself**, not parts of it. That is the whole row
accounted for, which is the accounting discipline kernel §4.4 uses on the 50 kinds.

Certification of `falsification` — whether a declared falsifier could actually fire,
the estimator doctrine's question — is **not** settled here and belongs with
sub-problem 5's conformance oracles, next to the identical open question about
`equivalence_rule` (§11.4).

**The seed plan is normative spec content, not a runtime choice.** An earlier
revision left the derivation *rule* to the spec and the *root seed* to the recipe,
which reopened the hole §4.2a was written to close one level down: an author could
execute under a dozen root seeds, keep the one whose result they liked, and replay
that winner cleanly forever. Every replay would agree, every scope would derive
`clean-environment`, and the selection would be invisible because it happened before
the recipe that any replay reconstructs. A root seed chosen after seeing outcomes is
tolerance shopping wearing a different hat, and it is answered the same way: the
seed is declared in the frozen spec or it is not the run's seed.

Changing a root seed therefore mints a **successor spec** under §3.2's rule, and the
runs executed under the original stay attached to it — so seed selection becomes
visible in the same way tolerance selection is. It is bounded by the same limit: a
recorded attempt is only visible if it was recorded, which is kernel **G4** and
needs §9's mutation log. Root-seed shopping is not a new defect; making the seed
normative is what moves it under an existing guard instead of leaving it outside
every one.

### 3.1a The nondeterminism contract is one discriminated union

Making the spec authoritative and projecting it into the recipe (§4.2a) closes
disagreement **between** the two records. It does nothing about a contradiction
**inside** the spec, and projection is faithful: it reproduces the contradiction
into the recipe rather than catching it.

An earlier revision carried `nondeterminism_contract` and `seed_plan` as independent
fields, which spells all of these:

| spellable, and incoherent | why |
|---|---|
| `deterministic` **plus** a seed plan | seeds that govern nothing, or a determinism claim that is false |
| `stochastic-unseeded` **plus** a seed plan | the contract disclaims what the plan supplies |
| `seeded` **with no** seed plan | a seeding discipline with no seed |
| multiple roots, **no rule selecting one** | a job's seed is not determined; the derivation has no `stream_root` |

> **Rule.** `nondeterminism_contract` is a **discriminated union** with exactly three
> variants:
>
> - **`deterministic`** — carries nothing. The run claims no RNG dependence at all.
> - **`seeded`** — carries a **complete seed plan**: the derivation rule identity, the
>   **logical stream identities** the analysis uses, the root seeds, and a **total**
>   mapping from every declared logical stream to exactly one root. If a stream can
>   exist that no root covers, the plan is incomplete and the spec is refused. The
>   derivation is `seed = f(stream_root, semantic_job_key, stream_key)` (§6.2), where
>   `stream_key` is a **logical** stream identity.
>
>   A logical stream is named for **the role randomness plays in the analysis** —
>   `model-initialization`, `resample-draws`, `train-test-split` — never for the
>   library that provides it. `numpy-rng` and `torch-rng` were the first examples
>   written here and were wrong for the same reason rule names were: a
>   reimplementation in a different framework draws the same *analytical* randomness
>   from a different library, and a spec naming the library disagrees with it. Library
>   names are as much implementation topology as rule names, one layer down and easier
>   to miss.
> - **`stochastic-unseeded`** — carries a **rationale** and nothing else. It is a
>   valid, honest declaration; it simply cannot support a bitwise `equivalence_rule`.
>
> A spec whose union is inhabited by no variant, or by one whose payload is
> incomplete, is **not a spec** and cannot be frozen.

Totality is the part worth stating explicitly. "Multiple roots" is not refused —
multi-stream generators are ordinary — but a set of roots with no rule assigning
streams to them leaves the derivation with an ambiguous root argument, which is the
seed plan failing at the same place the round before last failed: a derivation rule
is only as determined as its inputs.

**Declaring streams in the plan obliges the occurrence to record them**, which is
§6.2's business and is where the first version of this rule stopped short. A plan may
say `model-initialization` and `resample-draws` draw from different roots while the
realized seeds are keyed by job alone — one job, two streams, one slot. §6.2 closes that with the nested keying;
the two halves of stream totality have to land in both records or neither.

**The per-job obligation is real, and it does not belong in the spec.** The
distinction that took three revisions to get right: the spec **does** hold one global
set of logical streams — the equality check above needs it — but a global set must
not become a **per-job obligation**. A previous revision made exactly that mistake,
requiring *every* job to have realized every declared stream: for a workflow where
family A initializes a model and family B resamples, the honest record
`{A: [model-initialization], B: [resample-draws]}` makes **both families
non-conforming**, and the only conforming record is the false one — every job
claiming randomness it never drew. A conformance rule whose sole satisfying record is
a lie is worse than no rule: it does not merely fail to catch the omission §6.2 was
closing, it *requires* the fabrication.

The next revision fixed that by declaring streams **per semantic job family** — and
put the declaration in the frozen spec, which is worse in a way that is easy to miss
because the field looked like it belonged there. **A job family is a workflow rule or
process name: implementation topology.** The spec is the record that must survive
being implemented twice, and §7.3's `independent-implementation` row requires the
**same `spec_identity`** with a different `code_identity`. A reimplementation that
splits one rule into three, or names them differently — which is what an independent
implementation *does* — would disagree with the spec's family names, requiring a
successor spec, and could then never be compared under that row at all. **The scope
row becomes unreachable for every seeded spec**, which is the design refuting its own
strongest verification class by way of a field name.

> **Rule.** The spec declares **logical streams**, their roots, and the derivation
> rule. The **content-addressed workflow-definition snapshot** (§6) declares, per
> semantic job family, **which logical streams that family uses**. The execution
> boundary checks **set equality against the recipe**:
>
> ```
> union(family streams over the workflow definition) == recipe.seed_plan.logical_streams
> ```
>
> and refuses the run otherwise.

**The right-hand side is the recipe, not the spec.** Writing it against the spec made
the rule undefined for the shape that does not have one: `dataset-production` runs
carry no `spec_identity` (§4.2, §5.2) and author their seed plan directly, so a rule
comparing against "spec logical streams" has no right-hand side for them — it would
either refuse every seeded dataset-production run or, more likely, be quietly skipped
for the shape it cannot evaluate. Naming the recipe covers both: for `assessment`
runs projection (§4.2a) guarantees the recipe's plan **is** the spec's, so the check
is identical in force, and for `dataset-production` it reaches the authored plan
directly. **When a rule must hold for both shapes, state it over the member both
shapes carry** — a lesson §5's whole structure already encodes, applied here one rule
too late.

**Equality, not containment.** The first version of this rule checked only that every
family stream maps to a declared logical stream — one direction, and the harmless
one. The other direction is where the failure lives: a plan declares
`resample-draws`, no family claims it, and the workflow **conforms** while the
analysis silently does not resample. Every downstream record agrees: the boundary
passes, the occurrence records every stream any family declared, conformance passes,
and a replay reproduces the same omission perfectly and derives `clean-environment`.
A declared source of randomness that no implementation touches is a **pre-registered
step that did not happen**, and a containment check reads it as full compliance. It
is the coarse-declaration failure of the previous revision inverted — there the
obligation was wider than the work, here the work is narrower than the obligation —
and set equality is the only form that catches both.

The seam falls where the two records already differ in kind: the spec says *what the
analysis is*, including which sources of randomness it depends on and what seeds
them; the workflow definition says *how this implementation is decomposed*, including
which of those streams each piece touches. Two independent implementations of one
spec then have different workflow-definition identities and the same
`spec_identity` — which is exactly the shape §7.3's row is looking for — while seed
shopping stays closed, because the roots never leave the spec.

Nothing new is introduced to hold this. `workflow_definition_identity` is already a
recipe member, already content-addressed, and already differs between implementations
by construction. And the obligation still lands per family, so the conformance rule
of §6.2 is unchanged in force: `f` is keyed by job *and* stream, so the obligation is
indexed the same way the derivation is. A declaration coarser than the thing it
constrains cannot constrain it — and one **finer-grained than the record it sits in**
drags implementation detail into an identity that must not carry it.

**This supplies the pre-execution consistency rule §1.2 promised.** That section
observed that a run declaring `stochastic-unseeded` under a spec declaring bitwise
equivalence is a contradiction *detectable before execution*, and noted that today
neither half is representable. Both halves are now in one frozen record, so the
check is a **freeze-time** rule over a single facet rather than a cross-record
reconciliation. The four rows above are refused by the **type** and need no check at
all; the §1.2 case — `stochastic-unseeded` alongside a bitwise `equivalence_rule` —
remains spellable, because it is a contradiction across two fields rather than within
one, and is therefore a freeze-time **check** over the frozen facet. Nothing about it
reaches execution: an unfreezable spec produces no run.

The spec's **Markdown body may explain these fields**. It may not contradict them
and it is never the authority for them. A publishable pre-registration document is
a **rendering** — a content-addressed run artifact in the kernel's §4.3 sense —
not a second record.

Draft prose that has not been frozen is a **note** or a coordination artifact. It
is not a spec, and nothing may execute against it.

### 3.1b The interpretation rule, and where `applicability` lives

§5.1 gives the assessment a constructor that "applies the frozen
`interpretation_rule`" and "copies `applicability` from the spec". Neither was
buildable as written: `applicability` was not a spec field at all — kernel §4.2.1
lists it on the *assessment*, and this table did not carry it — and
`interpretation_rule` was a prose description of a mapping with no signature, no
output shape and no failure semantics. **A constructor whose inputs do not exist is
not a constructor**, and the previous revision closed the authorship hole while
leaving the mechanism that replaces authorship undefined.

> **Rule.** `interpretation_rule` is a **versioned rule identity**, frozen with the
> spec, denoting an evaluator with the signature
>
> ```
> (execution result) → { outcome, estimate?, uncertainty? }
> ```
>
> where `outcome ∈ supported | refuted | inconclusive`, and `estimate` /
> `uncertainty` are present exactly when the rule yields them. It reads the
> **boundary-built result manifest** (§4.2d) and nothing else — not the recipe, not
> the occurrence, not the corpus. A `v2` rule identity is **disjoint** from its `v1`,
> as with every other versioned rule here.

**Evaluator failure produces no assessment — it is not `inconclusive`.** This is the
opposite ruling to §7.2's, and the asymmetry is the point. There, an equivalence rule
that cannot read its artifacts returns `inconclusive` because a *verification* is a
record about two runs and "could not tell" is an honest thing for it to say. Here,
`outcome: inconclusive` is a **scientific claim** — the analysis ran and did not
resolve the question — and a reader crash, an unparseable output or a missing rule
implementation says nothing scientific whatever. Mapping machinery failure onto a
scientific outcome would put the estimator doctrine's exact defect at the last step:
a check that cannot fail, because every failure has a verdict waiting for it. The
run stands, complete and verifiable; **no assessment is produced**, and the reason is
recorded as a finding.

**A rule identity must be bound to an evaluator, or it names nothing.** The identity
is a symbol; the facet is what an implementation of that symbol produces. If two
installations implement `median-difference/v1` differently, one frozen spec and one
immutable run derive **different assessments** — and under the `(spec, run,
proposition)` basis those two facets collide at **one address**, which is the worst
available form of the failure: not two records disagreeing, one record whose content
depends on where it was computed.

> **Rule.** A rule identity binds to behaviour by one of two routes, and a spec
> naming a rule that has neither is refused:
>
> - a **held, content-addressed implementation**, resolved like any other closure
>   content (§4.4); or
> - a **normative registry entry with conformance fixtures** — declared inputs and
>   required outputs — that any implementation must satisfy.
>
> Either way, **a semantic change mints a new identity**. `v2` is disjoint from `v1`,
> and an implementation that fails its fixtures is not that rule.

This applies verbatim to the **equivalence rule** (§7.2), which has carried a
versioned identity since the first draft with the same gap underneath it: versioning
a symbol is not versioning behaviour. Certifying that a rule *could fire* — the
estimator-doctrine question §11.4 already parks for equivalence rules and
falsifiers — belongs beside this in sub-problem 5, and is a different question from
binding the symbol, which is settled here.

**`applicability` becomes a spec field**, joining `estimand` as something declared
before execution and copied by the constructor. It has to be pre-declared for the
same reason the equivalence rule does: choosing after seeing the result which
population a finding applies to is scope-narrowing after the fact, and it is the
cheapest possible way to rescue a null. Kernel §4.2.1 keeps listing it on the
assessment — that is the copy, not a second authority, exactly as with `estimand`.

### 3.2 Freezing and revision

A complete spec is **minted frozen**, before execution. Its identity is the
content hash over the normative facet under `science.identity.v1` (§4.3).
Semantic revision follows the kernel's
proposition rule exactly: an edit that changes the facet **mints a successor**
with a `supersedes` edge; an edit to the explanatory body does not.

Kernel §3.2's tolerance-shopping guard lands here: a spec whose replay failed is
recorded **superseded-after-failure**, and its successor must reference it. The
limitation the kernel states about that guard — it exposes shopping only when the
failed attempt was retained — is unchanged and is not weakened by anything below.

### 3.3 A content hash proves content equality, not chronology

This is the load-bearing warning of the whole design, and it must not be softened
anywhere downstream.

Content addressing establishes that two things are the same thing. It establishes
**nothing about when either came into existence**. A spec hash computed today over
a facet authored today is byte-identical to one that would have been computed a
year ago, and no author-supplied date distinguishes them.

> **G2a as narrowed here.** The system guarantees that a run's closure names
> exactly one frozen spec identity, and that semantic revision of a spec mints a
> successor. It does **not** guarantee that the spec was frozen before execution
> began. Ordering holds only over what the execution boundary **recorded**, and
> the boundary's own record is rewritable.

A run started **through** the execution boundary (§4.4b) does acquire a recorded
ordering, because the boundary observes the spec identity before it observes
anything else. A run performed out of band and attached afterwards presents a
history that is complete, consistent, and indistinguishable from the first.

This is not a new defect. It is the **fourth consequence** of the single missing
substrate capability the kernel names in §8.7 — alongside G4 (discarding a failed
replay), G8 (deleting a failing verification), and semantic-identity enforcement
(a coordinated fields-plus-hash edit). One capability, four consequences when this
design banked; the correction-lifecycle design added the fifth on 2026-08-03
(deleting a retraction record, its limitation 1).
Closing it requires **pre-mutation durable registration and detectable journal
removal** (§9), and nothing short of that.

The log is designed (`2026-08-03-tamper-evident-log-design.md`), and its reach
here is exactly the boundary-mediated qualification: at implementation, a run
started **through** the boundary acquires a durably appended intent entry before
execution begins, so its recorded ordering gains a removal-detectable witness.
The out-of-band case is untouched — a run performed outside the boundary
appends nothing, and the strong chronology claim is **not** restored by the log
(its limitation 5).

R12 pins the limit as a test, so no reader over-reads the guarantee.

### 3.4 The 209 existing pre-registrations

They are **salvage inputs**. Curating one may produce a spec; that spec **cannot
retroactively satisfy pre-declaration for an earlier run**, and may only govern a
later rerun. Sub-problem 4 defines that boundary; sub-problem 7 performs the
salvage.

`validate/checks/prereg_vehicles.py`'s rule — freeze the vehicle by **content**,
never by path — is absorbed into `input_roles`, where a declared input is a
dataset address and therefore content-identified by construction. The
`fb-2026-07-11-024` failure it was written for (a "frozen" vehicle that was a
gitignored build product, regenerated and destroyed by the registered refresh)
becomes unspellable rather than checked.

## 4. The closure

### 4.1 Three parts, and the boundaries between them are load-bearing

A run's closure has **three** parts. Two is one too few, and the missing boundary
is the one that makes tolerance-based replay expressible at all:

| part | content | role |
|---|---|---|
| **execution recipe** | everything a replay must reconstruct | what **scope** compares |
| **execution result** | the actual output manifest | what **verdict** compares |
| **execution occurrence** | a boundary-minted event token, plus runtime observations | what makes this execution *this one* |

The run's **address** covers all three. **Scope compares recipes; verdict compares
results.** They never touch.

**Why the result must be outside the recipe.** Kernel §3.1 permits an equivalence
rule with a declared numeric tolerance, so a legitimate clean reproduction may
produce *different output bytes*. If the output manifest sat in the part that
replay must reconstruct, that run's recipe would already differ before the
tolerance could be evaluated — and the reproduction would be disqualified by the
very difference the rule exists to forgive. Any tolerance looser than bitwise
would be unreachable in practice while appearing to be supported.

**Why the occurrence needs an explicit token.** `started_at + actor + host` does
not guarantee two executions have distinct addresses: the same actor can start two
runs on one host within the same timestamp granularity, and a coincidence there
would silently collapse two events into one node. The execution boundary therefore
**mints a random event token** per execution. It is not derived from anything, and
it is the only member of the closure that is neither observed nor declared.

Without this split a deterministic pipeline run twice would have identical content
and therefore one address, and kernel §3.3's verification — which references *two*
runs — could not be constructed. With it, a deterministic replay is exactly **two
runs with equal recipe identity and distinct occurrences.**

This refines world §4.2's "content identity of the execution closure" rather than
contradicting it: the basis is over the whole closure record, of which the result
and the occurrence are members.

### 4.2 Members

**The recipe contains nothing that only exists after execution.** This is not a
stylistic ordering — a member observed during the run makes two identical
executions differ, and §7.3 compares recipes to derive scope, so a post-execution
member in the recipe puts `clean-environment` out of reach before the equivalence
evaluator ever runs. An earlier revision placed the engine-native execution trace
and the realized seeds here and had exactly that defect, with transient job ids
inside an identity.

**Execution recipe** — frozen inputs to execution, complete before it starts:

| member | content | notes |
|---|---|---|
| `shape` | `assessment` \| `dataset-production` | §5; discriminates which members are obligatory |
| `spec_identity` | the frozen spec hash | obligatory for `assessment`; absent for `dataset-production` |
| `code_identity` | digest over the **content-addressed code bundle** | §4.4 |
| `environment_identity` | digest over the **manifest of held environment artifacts** | §4.5 |
| `workflow_definition_identity` | digest over the workflow-definition snapshot | §6 |
| `invocation` | the **bundle-relative entrypoint**, the requested **engine targets**, **bindings** to the members supplying engine configuration, and **boundary-relative declared outputs** | §4.2b, §4.2c; a definition is not an invocation, and this member holds **no values another member already holds** |
| `inputs` | role-partitioned manifest of `(role, dataset address, content identity, exclusion certification?)` | §4.6; **projected from the spec** for `assessment` runs (§4.2a); the certification is inline on `reads` entries (§5.2) |
| `parameters` | the parameter set | ″ |
| `nondeterminism_contract` | the discriminated union of §3.1a, **with its payload** — the complete seed plan in the `seeded` variant | ″ — declared, never observed; **projected whole**, roots included, for `assessment` runs (§4.2a) |
| `boundary_policy` | the enforcement policy the run executes under; **names the scope-derivation rule identity** (amended 2026-08-03, 5b §6) | §4.4b |
| `rule_bindings` | the resolved `(rule identity → implementation content identity)` pair for every rule the run's downstream derivations execute — the spec's interpretation and equivalence rules, the boundary policy's scope-derivation rule | added 2026-08-03 (5b §6); resolved at freeze — determined with one conforming implementation held, explicitly named by the freeze act with several, **refused** on ambiguity or an un-held/fixture-failing name; downstream constructors read it and accept no selection argument |

**Execution result:** `outputs` — a manifest of `(logical name, content identity)`,
**constructed by the boundary from `invocation`'s declared outputs** (§4.2d), never
supplied.

**Execution occurrence:** `event_token` (minted, random), `started_at`, `actor`,
`host_realization`, the **raw execution trace**, the **realized seeds** keyed
`[semantic job key][stream key]` (§6.2), and the **boundary receipt** (§4.4b)
recording what the boundary constructed and enforced.

**Trace conformance is not an identity input — but it is not merely a diagnostic
either.** After execution the realized seeds are checked against the seed plan and
the trace against the workflow definition. A mismatch never changes the recipe to
match what happened; that would let the record follow the run instead of governing
it.

But leaving it at "a finding" was a hole. A **non-conforming** execution is precisely
one the recipe did **not** govern, and if scope derivation does not consult that,
two runs with equal recipes, qualifying receipts and equivalent outputs can reach
`clean-environment, passed` while their realized seeds violate the declared plan, or
their executed jobs fall outside the trace their targets imply (§6.2). §7.3 therefore requires conformance of **both**
executions, and the conformance result travels in the comparison report — which is
already a member of the verification basis (§7.3b).

So conformance sits in exactly one place in identity: not in the run's recipe, and
not nowhere.

### 4.2a For `assessment` runs, the recipe is projected from the spec

The spec declares inputs, parameters and a nondeterminism contract. The recipe
carries the same three. Nothing above requires them to **agree**, and an earlier
revision simply did not ask — so a spec could declare `dataset:A` and
`alpha = 0.05` while its run used `dataset:B` and `alpha = 0.5`, and two identical
replays of that run would reach `clean-environment, passed` and admit it.
Pre-declaration would be decoration.

> **Rule.** For a run of `assessment` shape, the boundary **constructs**
> `inputs`, `parameters` and the `nondeterminism_contract` **with whatever payload
> its variant carries — the complete seed plan, root seeds included** — **directly
> from the frozen spec**. There is no caller-supplied path to those members and no
> override.
>
> **`rule_bindings` resolves at the same freeze, likewise boundary-performed**
> (added 2026-08-03, 5b §6): the spec and the boundary policy name rule
> identities only, and the boundary resolves each to exactly one held
> implementation content identity — determined with one conforming
> implementation held, an explicit freeze-act selection with several, refusal
> on ambiguity or an un-held or fixture-failing name. Nothing observable exists
> yet to shop, which is the point of resolving here.

Projecting the derivation rule while leaving the root seed to the caller was the
first version of this rule, and it left the same defect one level down: the rule
`seed = f(stream_root, semantic_job_key, stream_key)` is only as pre-declared as its
roots. §3.1a
now carries the roots inside the contract, so there is no seed-shaped member left
outside the projection — which is the point of folding the plan into the union
rather than projecting two fields side by side.

Checking equality after the fact was the alternative and is weaker: it needs the
check to exist, to run, and to be reachable on every path. Projection makes
disagreement **unspellable** rather than detected, which is the discipline the
kernel applies to literature and this document applies to `unknown` components.

`dataset-production` recipes are authored directly, because there is no spec to
project from — which is also why §5.2 gives that shape a fixed equivalence rule
rather than a declared one. The two facts have the same cause.

Obligation is a pure function of `shape`, and the import-time reconciliation gate
survives from `t077` with its key changed: a member added without an obligation for
every shape fails at import. What the table no longer encodes is **policy** — under
§2 there is only completeness, so it states which members each shape must carry and
nothing else.

### 4.2b A definition is not an invocation

Every member above says what was *available* to the execution. None of them said what
was **asked for**, and a replay reconstructs from the recipe alone — so an earlier
revision's recipe could not be executed.

The counterexample is one Snakefile with targets `analysis` and `report`. Two runs
building different targets share every recipe member the previous table listed:
same bundle, same environment, same definition snapshot, same inputs, same
parameters, same contract, same policy. They have **equal recipe identities** while
having done different work, so §7.3 reads them as two executions of one recipe and
can derive `clean-environment` from a comparison of unrelated outputs. And a replay
boundary handed such a recipe has nothing to invoke: `snakemake` with no target is a
different request than either.

> **Rule.** `invocation` is a recipe member, frozen before execution, and it is
> **structural**: the **bundle-relative entrypoint**, the **engine targets
> requested**, and **bindings** naming which recipe members supply the engine's
> configuration. It carries **no values of its own** for anything another member
> already holds. Options that affect only scheduling and not the computation (worker
> counts, resource hints) are excluded and named as excluded, so the member does not
> turn a `-j 8` into a different recipe.
>
> The boundary **renders** the engine's configuration — config files, `--config`
> flags, environment, CLI arguments — from `inputs`, `parameters` and the seed plan.
> A caller cannot supply that rendering, and `invocation` cannot restate what it
> renders from.

**Structural, because a free-form option list is a second parameter channel.** The
first version of this member accepted "the execution options that change what runs",
which is every `--config` flag an engine takes — so a recipe could hold
`parameters = {alpha: 0.05}`, projected faithfully from the frozen spec under §4.2a,
alongside `invocation: --config alpha=0.5`. The engine reads the flag. Every replay
reproduces `0.5`, derives `clean-environment`, and admits an assessment whose spec
declared something else.

That is §4.2a's own defect reintroduced by the member added to fix a different one:
projection makes disagreement with the spec unspellable **through the members it
projects**, and an option list is a door beside them. Rendering rather than accepting
is the same move projection made — the authoritative value has exactly one path to
the engine, and no second spelling exists to disagree with it. R17 tests this route
alongside the original one, because "no caller-supplied path to those members" is a
claim about *all* paths, and it was true of the ones I had enumerated.

### 4.2c Output locations are boundary-relative, and the host mapping is an observation

§4.4b confined writes to "the declared output locations" — a set no recipe member
named until now, so the rule quantified over nothing and the receipt attested a
boundary the closure could not describe. But putting the locations in the recipe as
**caller-supplied host paths** trades that for two worse problems.

**A declared location grants its own authority.** The confinement allowlist is built
from the declaration, so declaring `/etc` puts `/etc` inside the allowlist. The rule
would then check that writes stay within a set the writer chose, which is not a
constraint. This is the same shape as an authored `scope` (§7.3): a field whose value
decides whether the field's own guard is satisfied.

**An absolute path makes recipe identity machine-specific.** `/data/scratch/run-17`
is a fact about one host. Two runs of "the same recipe" on different machines then
have different recipe identities and can never reach `clean-environment` — the scope
this design cares most about, defeated by a mount point.

> **Rule.** Declared outputs are **logical names or boundary-relative paths beneath a
> boundary-owned output root**. Absolute paths are refused, and so is any traversal
> that escapes the root. The mapping from that root to a host location is chosen by
> the **boundary**, recorded in the **receipt** as an occurrence observation
> (§4.1), and is **not a recipe member**.

The split follows §4.1's rule exactly: what a replay must reconstruct is *that
outputs go to the run's output root*, which is portable; *where that root was mounted
this time* is what makes this execution this one. Reading it the other way is how the
first version put a hostname-shaped fact into an identity, which is the defect R4's
negative (a) already pins one section over.

This is the `code_identity` correction repeated at the level above it. There, "the
executed code tree" named nothing until §4.4 defined a bundle; here, "the execution"
named nothing until the request itself was a member. **A closure that cannot be
executed is not complete**, whatever §2 says about its members being present — which
makes this a §2 failure that survived nine reviews because every member in the table
was individually well-defined.

### 4.2d The result manifest is derived from the declaration, not reported

Declaring the outputs (§4.2c) and recording the outputs (§4.1) were, until now, two
independent acts. The recipe says which outputs the run produces; the result carries
`(logical name, content identity)` pairs; and nothing tied the second to the first.
That gap is directly admission-bearing, because the verdict compares **results**
(§4.1) — so whoever writes the manifest chooses what the equivalence rule sees.

Three spellings, all previously available:

| manipulation | effect |
|---|---|
| **omit** a declared output | an unfavourable artifact never reaches the evaluator; the comparison passes on what remains |
| bind a logical name to **different content** | the name says `estimates`, the digest is of something else |
| add an **undeclared** entry | the manifest describes work the recipe never asked for |

Each survives every guarantee already in place: the recipe is intact, the receipt is
intact, conformance passes, and the two runs compare cleanly. This is the §7.3c
defect one record over — a derived value trusted while its inputs were free — and it
is the fourth time that shape has appeared. The fix is the same one, applied here.

> **Rule.** The **boundary alone** constructs the result manifest. After target
> satisfaction it **content-addresses every declared final output** and emits exactly
> those entries. A declared output that is **missing**, a **duplicate** logical name,
> an **undeclared** entry, or a digest that does not match the bytes on disk means
> **no run is minted**. There is no supplied-manifest path.
>
> **Intermediates are not results.** Temporary and scratch files beneath the output
> root are not content-addressed and do not enter the manifest; only the outputs
> `invocation` declares as final do. The confinement rule (§4.4b) still governs where
> they may be written.

The intermediates exclusion matters for more than tidiness: sweeping the whole output
root into the manifest would make the result depend on an engine's scratch-file
behaviour, so a replay that cleaned up differently would differ before its tolerance
was evaluated — §4.1's original defect, re-entering through a directory listing.

**Refusal, not non-conformance, and the two are not interchangeable.** An earlier
phrasing said such a manifest "refuses the run or makes it non-conforming", which
offered a choice §2 does not leave open: a run with a missing or unverifiable output
has an **incomplete closure**, and §2 says that is not a weaker run, it is not a run.
Minting one and marking it non-conforming would put an incomplete closure in the
world and rely on a downstream reader to discount it.

The two states divide cleanly, and the division is worth stating because this
document has now needed it three times:

| condition | outcome |
|---|---|
| the closure cannot be completed — missing output, duplicate name, undeclared entry, digest mismatch | **no run is minted** (§2) |
| the closure is complete, and the execution violated it — realized seeds contradict the seed plan, executed jobs fall outside the trace their targets imply | **non-conforming run**, `not-certified` scope (§7.3) |

**Non-conformance is reserved for complete executions that disobeyed their recipe.**
It is a statement about behaviour, and it needs a run to be a statement about. A
hand-written record that never went through the boundary is neither of these — it is
an untrusted import, governed by §7.3c's explicit-import and audit limitation, and no
rule here changes that.

### 4.3 Canonicalization is new machinery, not an existing contract

An earlier draft claimed `science_model/audit/fingerprint.py` already supplies a
strict value contract — floats, nulls and nested objects refused. **That is wrong,
and the error matters because six identity bases were about to be built on it.**

The strictness lives in `normalize_identity_value`, which governs *finding
qualifiers only*. The generic serializer `canonical_json` accepts floats and nested
objects and prunes nulls recursively. Measured directly:

```
canonical_json({"float": 1.25, "nested": {"x": 1}})  ->  b'{"float":1.25,"nested":{"x":1}}'
canonical_json({"f": 0.1 + 0.2})                     ->  b'{"f":0.30000000000000004}'
```

A basis built on that would let a run's address depend on binary float formatting —
platform-sensitive, and exactly the failure the finding module refuses for its own
identities.

**A contract that is merely strict is not enough — it must be injective.** Four
collisions had to be closed, and **two of them were introduced by the fixes for the
others** — which is why the rule below is stated as an encoding that preserves
*type*, not merely value:

| collision | introduced by |
|---|---|
| binary float bytes are platform-dependent | the original `canonical_json` claim |
| decimal `0.5` ≡ string `"0.5"` | rendering decimals *as strings* to fix the float |
| `{"x": null}` ≡ `{}` | carrying over `canonical_json`'s recursive null pruning |
| integer `1` ≡ decimal `1.0` | stripping trailing zeros to canonicalize the decimal |

Each fix was locally right and collapsed a distinction one level over. A value's
**type must survive its encoding**, and every rule below is that one requirement.

> **What must be built: `science.identity.v1`,** a generic, versioned canonical-value
> contract that is **injective** and **domain-separated per kind**.
>
> - **Values:** NFC strings, booleans, integers, decimals, arrays, and objects whose
>   keys are NFC-normalized and sorted by code point.
> - **Decimals are typed, and encode as canonical JSON *numbers* that always retain a
>   fractional part** — no exponent, no trailing zeros beyond the first fractional
>   digit, one spelling of zero: `1.00` → `1.0`, `1.500` → `1.5`, `0.0` → `0.0`. An
>   **integer never contains a point**, so integer `1` encodes as `1` and decimal
>   `1.0` as `1.0`. A decimal shares an encoding with neither a string nor an integer.
>   **Binary floats are refused at the boundary**; the caller supplies a decimal and
>   owns the rounding, so scientific values never inherit an accidental IEEE
>   spelling. **Non-finite decimals — `NaN`, `Infinity`, `-Infinity`, and the
>   signalling forms — are refused outright**, since JSON has no encoding for them
>   and every substitute is a collision: a bare token collides with a string, `null`
>   is already refused, and mapping them onto a sentinel number collides with that
>   number. `NaN ≠ NaN` also makes them unusable as identity content on their own
>   terms.
> - **Nulls are refused, not pruned.** Pruning is what makes `{"x": null}` and `{}`
>   identical, and an absent member must differ from a member that is present and
>   empty. An absent field is simply absent.
> - **Post-normalization key collisions are rejected**, not silently merged —
>   `normalize_identity_qualifiers` already does this and is the precedent.
> - **Digest** = `sha256(domain + "\n" + canonical bytes)`, with a **per-kind domain**
>   (`science.run.v1`, `science.spec.v1`, `science.dataset.v1`, …) so identical
>   payloads under different kinds cannot collide.
> - **Versioned, and v2 domains are disjoint from v1 by construction.**

> **Amended 2026-08-06, while implementing it.** *"Canonical JSON"* above does
> not determine the bytes, and two of the choices it leaves open are exactly the
> kind that fork an identity silently across implementations. Both are now
> pinned, and neither was discoverable from the prose:
>
> - **String escaping is exact.** `"` → `\"`, `\` → `\\`, and the five C0
>   controls with a short form (`\b \t \n \f \r`) take it; every other C0
>   control takes `\u00xx` with **lowercase** hex. Nothing else is escaped —
>   **non-ASCII is emitted as literal UTF-8** and `/` is never escaped. Both of
>   those are *optional* in JSON, and Python and JavaScript take opposite
>   defaults, so leaving them optional means two conforming implementations
>   producing different bytes for one value. **Unpaired surrogates are refused**:
>   they have no UTF-8 encoding, and a JavaScript string can hold one.
> - **Object keys sort by code point, never by UTF-16 code unit.** The two orders
>   disagree above U+FFFF — `U+FF03` precedes `U+1F600` by code point but follows
>   it by code unit, because the astral character's first unit is `D83D` — and
>   **JavaScript's default `Array.prototype.sort` uses the code-unit order**.
>   "Sorted by code point" was already the stated rule; what is new is that it is
>   a *hazard* rather than a description, and the TypeScript implementation has
>   to sort explicitly rather than by default.
>
> A third rule is a consequence rather than a choice, recorded because a reader
> will ask: the digest separator is a newline, so the **domain grammar must
> exclude newlines** or a crafted domain could forge the separator and let one
> payload digest as another. The grammar is checked — `science.<kind>.v<n>`,
> lowercase, positive version — which also delivers the disjointness the last
> bullet above asserts, rather than leaving it to convention.

A tagged encoding (`{"$dec": "0.5"}`) would also be injective and is **rejected**:
it needs a reserved key namespace, and reserving `$` means every caller's key space
acquires a rule that only the identity layer knows about.

`finding_fingerprint` is the precedent for the domain prefix, for disjoint
versioning, and for key-collision rejection; the value contract above is new work.

**Injectivity cannot come from the discriminator.** `shape` disambiguates
*top-level* members only, so it says nothing about a null nested three levels down.
The encoding has to carry the distinction on its own, at every depth — which is why
refusing nulls replaced pruning them rather than sitting beside it.

**Six bases depend on this.** World §4.2 assigns content-derived bases to `dataset`,
`analysis-spec`, `run`, `verification`, `assessment` and `source-assertion` and
specifies canonicalization for none of them. This is that missing piece, and building
it once is what stops six kinds acquiring six answers to what "the same content" is.

### 4.4 `code_identity` is a captured bundle, not a tree we hope we digested

Removing `code_dirty` is correct **only if** the system defines and snapshots every
relevant byte. "The executed code tree" names no such thing: nothing today decides
which files are in it, and a run could claim a complete closure while omitting a
dynamically imported local module.

> **Rule.** `code_identity` is the digest over a **content-addressed code bundle**
> built from declared `code_roots` and captured by the execution boundary **before
> execution begins**. Uncommitted and untracked files inside `code_roots` are
> bundled — that is the point. Local runtime imports must resolve **inside that
> bundle or inside the held environment**; anything else is a refusal, not a
> silently missing member.

With the bundle defined, `code_sha` + `code_dirty` genuinely dissolves: the digest
covers what ran, dirty or clean, and the git commit — when the tree is clean —
survives as a convenience annotation that is **not** part of identity. This is
`t077`'s reasoning one step further: it made `""` unrepresentable; this makes "the
identity might not describe the artifact" unrepresentable.

R13 tests the capture, not the field: change an **untracked** file inside
`code_roots` and `code_identity` must move.

### 4.4b Capturing the closure is not enough — execution must be confined to it

A bundle captured before execution says what the boundary *saw*. It does not say
what the process *used*. Two gaps sit between those, and both leave the recorded
identity unchanged while the result changes:

- **mutation after capture** — the bundle is digested, then a file under
  `code_roots` is edited before or during the run;
- **undeclared reads** — the process imports a module, opens a data file, reads an
  environment variable, or fetches a URL that no closure member names.

The clean-environment receipt as first written proves *reconstruction* and says
nothing about either. A run could then be perfectly identified, perfectly held, and
governed by none of it.

> **Rule.** The execution boundary **executes from the captured bundle**, inside an
> environment confined to: the captured code bundle, the held environment artifacts,
> the declared inputs, and the **boundary-owned output root** that `invocation`'s
> declared outputs sit beneath (§4.2c). Reads outside that set fail; they are not warned about. The confinement in force is named by a versioned
> **`boundary_policy`**, which is a recipe member (§4.2) and is **bound into the
> receipt** (§7.3).

Making the policy a named record rather than a boolean is what keeps this honest.
Confinement is platform-dependent — filesystem namespacing and network denial are
implementable, total isolation is not universally so — so a policy **declares which
capabilities it provides**, and §7.3a evaluates scope over that set rather than over
a version ordering that does not exist. A run executed under a policy providing
fewer capabilities is still a run; it simply cannot reach `clean-environment`.

R15 tests both gaps by mutation: edit a bundled file after capture, and attempt an
undeclared file read and network fetch.

### 4.5 `environment_identity` is held content, not a recipe for content

A lockfile is a **recipe for an environment, not the environment**. Admitting one as
a closure member would contradict §2 by the design's own principle — the same
distinction as "recipe is not a run", one layer down. Packages get yanked, indexes
rotate, and a closure whose environment member cannot be reconstituted is not
complete; it merely looks complete.

> **Rule.** `environment_identity` digests a **manifest of held environment
> artifacts**, held on the same terms as every other closure member (§2, §4.7).

Resolved package blobs, an OCI image's layers, or a Nix-style closure all satisfy
it. **Containers are not mandatory** — the contract is holding, and the
implementations are interchangeable. A bare lockfile digest satisfies nothing and is
refused.

### 4.6 Inputs are role-partitioned, or eligibility is undecidable

`t077`'s single `input_manifest_digest` is role-blind. The kernel's eligibility
predicate turns on the run having **at least one `observes` input**, and G3's
belief digest names *`observes` dataset content identities* specifically. Neither
question can be answered from one undifferentiated digest.

So the input manifest is partitioned by role, with the `observes` partition
digested separately. That partition digest is the G3 member; the whole-manifest
digest is a closure member. Cheap to state now, expensive to retrofit after the
belief digest is built on it.

**The roles are per shape, and both shapes need the partition for the same reason.**
An `assessment` run partitions into `observes` and `reads`, which decides
eligibility. A `dataset-production` run partitions into **lineage-bearing** and
**auxiliary**, which decides what the produced dataset's stamped **lineage basis**
contains (§5.2) — and that basis is what substrate §5 walks to certify
independence, which kernel §4.2.1 turns into a corroboration multiplier. Different
roles, one mechanism, and in both cases a role-blind manifest leaves a
belief-bearing question unanswerable.

### 4.7 Runs begin at the most upstream held form

> **Rule.** Every input to a run is a **held dataset**. A computation whose input
> is not held — a URL, an accession, an instrument — is **acquisition**, recorded
> as dataset provenance, and is never a run.

This draws the acquisition line exactly where kernel §2.2 already draws it:
*"eligibility asks whether we hold the inputs and the complete processing closure
from the most upstream form we hold."* The most upstream held form is the
boundary; everything above it is provenance on the dataset, including its declared
acquisition boundary.

A download script that fetches a GEO series and lands files is therefore not a run.
But "not a run" must not mean "not recorded": the fetch has a real execution
record, and discarding it would lose provenance the kernel's acquisition boundary
depends on.

> **Acquisition provenance record.** A dataset whose bytes were fetched or produced
> outside the held boundary carries: the fetch procedure's **code identity** and
> **environment identity**, its **parameters**, the **locator** (URL, accession,
> instrument), the **retrieval observation** (when, by whom, what the source
> reported), the **resulting content identity**, and — added 2026-08-11 (the
> act-report design §4) — a **reference to the acquiring operation's act-report**:
> operational detail and references, never a second acquisition-provenance object. The
> existing fields remain authoritative, and for a successful acquisition the reference
> and the report publish in the **same registered transaction, in the same root**
> (T7); cross-root publication is refused.

This is deliberately most of a recipe, and deliberately not one. It preserves the
useful execution record without asserting that the acquisition is reproducible —
re-running it next year may return different bytes, because the *source* changed
and no closure of ours governs that. Kernel limitation 2, restated where it bites.

No ninth kernel kind is added: this is provenance on the `dataset`, which is where
kernel §4.4 already routes `experiment`.

## 5. Two run shapes, one kind

The kernel needs runs that produce assessments and runs that produce data. These
are **not** two kinds and the second is **not** an "acquisition run" — the kernel
is explicit that acquisition is not reproduced, so naming a reproducible thing
after it would be wrong.

### 5.1 `assessment` shape

Executes an `analysis-spec`, consumes role-typed inputs with at least one
`observes`, and **may** produce an assessment. Admission still requires the
verification state of kernel §3.3; producing an assessment is permission to be
assessed, not admission.

```text
Run(assessment) ──executes──▶ AnalysisSpec ──targets──▶ Proposition
Run(assessment) ──observes──▶ Dataset        (≥1, required)
Run(assessment) ──reads─────▶ Dataset        (any number)
Assessment ─────produced_by─▶ Run(assessment)
```

**The relation is not the payload.** The diagram places an assessment against a run
and says nothing about where its **fields** come from, and kernel §4.2.1 makes those
fields belief-bearing: `outcome`, `estimate`, `uncertainty`, `estimand`,
`applicability`, `interpretation_rule`. The kernel calls the assessment run-derived;
no constructor made it so. An author could therefore pair a run whose result refutes
the proposition with `outcome: supported`, let a clean verification admit it, and G3
would faithfully hash the fabricated facet — the belief digest is only as honest as
the fields it digests.

This is the §4.2d defect one relation downstream: §4.2d secured the manifest the
verdict compares, and the assessment is what the verdict *admits*. Securing the input
to a derivation and leaving its output free closes nothing.

**What a constructor guarantees, stated once for §5.1 and §5.2 both.** It governs the
**ordinary API** — every path Science offers — and, as §7.3c established for
verification, that is not the whole world: a raw filesystem write producing a
valid-looking node bypasses it entirely. So the guarantee is the same shape here.
Explicit import recomputes the facet from the run and refuses a mismatch; a
hand-written file that crossed no import is caught only under **audit**; and reading
validates nothing, because read-time validation would move admission on what is
mounted and cost R5. R22 and R23 say "no such parameter exists" about the API and
carry negatives for the bypass, rather than claiming a fabricated facet is
*unreachable* — which an earlier phrasing did, and which is false for the same reason
it was false for the comparison report.

> **Rule.** There is **one constructor** for an `assessment`, and its only argument
> is the **run ref**. It resolves the run's frozen spec, applies that spec's
> **`interpretation_rule`** to the **boundary-built result manifest** (§4.2d), and
> derives the whole facet: `outcome` from the rule, `estimate` and `uncertainty`
> where the rule yields them, `proposition` from the spec's `target`, `estimand` and
> `applicability` copied from the spec, and `interpretation_rule` as a ref to the
> frozen rule that ran. **There are no facet arguments.**

Every field then traces to something already frozen or already derived, and the two
fields kernel §4.2.1 marks "copied from the frozen spec, never re-authored here" are
copied by the constructor rather than by a convention a writer is asked to honour.

`applicability` deserves its own note because it is the one field that might look
authored: it is a property of the **estimand**, which the spec froze before
execution, so narrowing it after seeing the result would be the interpretation-rule
version of tolerance shopping. §3.1b therefore makes it a spec field, and if a run's
applicability turns out to be wrong, the answer is a successor spec and a new run,
exactly as with any other pre-declared field.

**An assessment therefore has no revisions, and the concept is retired.** Every field
is a function of `(frozen spec, immutable run result)` and both inputs are immutable
by construction — so there is no edit that changes a facet and leaves the same
assessment. Correcting an interpretation rule mints a successor spec; correcting
`applicability` mints a successor spec; a re-run mints a new run. Each produces a
**different assessment**, not a new revision of one.

This contradicts two banked claims that were written before the constructor existed,
and §14 records both. Kernel §5.1's belief digest names "**assessment revisions**" as
a member, and world §4.2 chose a `(spec, run, proposition)` basis over a content hash
with the reasoning that content addressing "would mint a new entity per revision and
there would be no revisions to name". Both are correct *given* an authored facet.
With a derived one they describe a lifecycle that cannot occur, and a digest member
naming a state nothing can enter is worse than redundant — it reads as a guarantee
that mutation is being tracked.

> **Ruling.** An `assessment` is an **immutable derived output**. The world basis
> stays `(spec, run, proposition)`, now justified as a **key over the derivation's
> inputs** rather than as a workaround for revisions, and **G3 digests sorted
> `(assessment identity, facet digest)` pairs** — the values *bound to* the identity,
> neither alone. Facets change only by a different assessment existing.

The basis survives the change unaltered, which is worth noticing rather than
glossing: the triple was already exactly the arguments the constructor takes. Its
*rationale* was wrong while its *content* was right — the same shape as §7.3b's
embedded evidence, where the mechanism was sound and the argument for it was not.

**Retiring the lifecycle nearly retired the property it carried.** A first version of
this ruling replaced G3's "assessment revisions" with bare **assessment identities**,
which is exactly wrong in the case the constructor cannot reach. R22's negative (c)
concedes that a raw-written assessment bypasses the API and is caught only under
audit; such a record occupies the address `(spec, run, proposition)` — the address is
a key over inputs, and the forger keeps the inputs — while carrying `supported` where
the derivation yields `refuted`. Under identity-only hashing the fabricated and the
correct belief states produce **the same digest**, and a later audit correcting the
facet would change belief without changing it either. G3's whole contract is that
equal digests mean equal belief.

So the member takes in the **values**, and the word "revisions" turns out to have
been standing in for them. Deleting a concept is safe only after checking what else
was leaning on it, which is what this document has now had to do twice — the other
being §7.3b's basis member that became redundant rather than wrong.

**And the correction over-corrected: a bag of facet digests is permutation-invariant.**
Hashing the values and dropping the identity fixes the forged-value case and opens a
second one, because a multiset does not record *which assessment carried which
facet*. Take two assessments on one proposition — one `supported` from a run over
one lineage, one `refuted` from a run over another — and **exchange their facets**.
Every digest in the bag is unchanged, the multiset is unchanged, and the belief
digest is unchanged. What changed is which evidence group supports the proposition
and which disputes it, and since kernel §4.2.1 weights corroboration by the
independence of the assessments doing the corroborating, the two states can aggregate
differently. Both halves are needed, and neither is sufficient:

| member shape | forged value | exchanged facets |
|---|---|---|
| assessment identities | **invisible** | invisible |
| facet digests | visible | **invisible** |
| `(identity, facet digest)` pairs, sorted | visible | visible |

That is the same defect twice in a row, in opposite directions — first the key
without the value, then the value without the key — and the general form is worth
stating: **a digest over a set loses everything the set's own structure carried.**
Pairing is how a set-valued member keeps it. Sorting and canonicalization come from
`science.identity.v1` (§4.3), so "sorted pairs" denotes one byte string rather than
an implementation habit.

**Why not content-address the assessment instead**, which would give the forgery a
different address outright: it lets the corpus hold two assessments claiming the same
`(spec, run, proposition)`, with no rule saying which one belief reads. The triple
keeps exactly one node per derivation, so there is nothing to disambiguate, and the
keyed member makes any divergence from the canonical derivation move the belief
digest. What that buys is **change detection, not truth detection** — G3 says belief
inputs differ, and only an audit says which one is right. Those are different claims
and the design should not blur them.

Keying does one more thing the bare form could not: it is the **only** place run
identity enters G3 at all, which is what §5.2's inline exclusion certification needs
in order to be reachable by the belief digest. That dependency is recorded there.

R22 tests it.

### 5.2 `dataset-production` shape

Transforms from a declared held boundary and produces a dataset. **Targets no
proposition and admits no assessment.** It names no spec, because it declares no
estimand and no interpretation rule — there is nothing to interpret.

```text
Run(dataset-production) ──transforms──▶ Dataset   (lineage-bearing, ≥1, held §4.7)
Run(dataset-production) ──reads───────▶ Dataset   (auxiliary, any number)
Run(dataset-production) ──produces────▶ Dataset   (exactly one, §5.2)

Dataset ──derived_from──▶ Dataset                 (a world-derived VIEW, not a stored edge,
                                                   and DESCRIPTIVE — independence reads the
                                                   dataset's stamped lineage basis, §5.2)
```

**The input role is `transforms`, and it is a third run-input relation.** An earlier
revision wrote `Run ──derived_from──▶ Dataset`, which overloads the **dataset-to-
dataset** lineage predicate substrate §5 walks — two different relations under one
name, one of whose ends is the wrong kind. It is also not in kernel §4.1's closed
signature list, which admits `observes` and `reads` for runs and nothing else, so the
edge was unspellable in the design it was written against. §4.1's whole argument is
that a signature is a predicate rather than a roster; quietly adding an edge shape
outside it is the roster failure from the inside.

`transforms` is therefore added to the kernel's closed signatures (§14), and it
**confers no eligibility** — only `observes` does, and only an `assessment`-shape run
carries it.

**The production edge points away from the run, and §5.3 is the proof.** Earlier
revisions wrote `Dataset ──produced_by──▶ Run`, mirroring the assessment's edge, and
that direction is refuted by this design's own **successful** replay case: §5.3 says
a `dataset-production` replay that reproduces its input bitwise yields **the same
dataset address** from **two distinct runs**. So the moment reproduction works — the
outcome the whole design is built to reach — a dataset has two producers. "One output
per run" does not give one run per dataset, and an earlier sentence here claimed it
did, reasoning about the wrong side of the relation.

The direction also decides what has to be mutated. `Dataset ──produced_by──▶ Run`
requires **editing an existing dataset node** to add an edge — a node that may be
immutable, may live in another corpus, and in the replay case already exists and is
not being minted. `Run ──produces──▶ Dataset` is emitted with the run, which is the
node actually being created, so nothing pre-existing is touched. That is the same
reasoning kernel §3.3 used to make verification its own kind rather than a facet on
the assessment: **put the edge on the node being minted.**

> **Rule.** `Run ──produces──▶ Dataset` is a kernel signature (§14), emitted by the
> boundary with the run. `Dataset ──derived_from──▶ Dataset` is **not stored**: it is
> a **world-derived view** — `D derived_from X` exactly when some run `produces D`
> and `transforms X`, excluding `X = D` — and it is **descriptive**. What independence
> reads is the dataset's stamped **lineage basis**, for the reason developed below.

Making lineage a view rather than a stored edge closes a class of drift: there is no
second copy to disagree with the runs, no authored ancestry to omit, and no way for
the graph to say a dataset came from somewhere no run touched. World §5 already
relocates lineage closure to the world layer over composed adjacency, so the walk
substrate §5 performs is unchanged in shape — it now composes over run-owned facts
instead of dataset-owned ones.

**But it does not cost nothing, and an earlier sentence here said it did.** A stored
`derived_from` edge is what substrate §5's orientation argument rests on: with the
edge on the **descendant**, deleting an ancestor leaves a dangling reference on the
surviving node, and that dangling reference is the whole detection mechanism.
Compose the relation out of `produces` and `transforms` and both edges live on the
**run** — so deleting the run removes the ancestry rather than breaking it. The
dataset survives, resolves to an empty closure, and reads as a **root**. Roots are
maximally independent, so the deletion does not cost corroboration; it *buys* it,
which is the direction nothing in this design is allowed to fail in. A purely derived
view cannot detect deletion, because detection needs a record of what was expected
and a view is only a record of what remains.

> **Rule.** The boundary stamps a **lineage basis** on the dataset it mints. A
> **route** is `(producing run ref, sorted content identities of that recipe's
> `transforms` inputs)`, and the basis is a **tagged shape** over routes:
>
> ```text
> basis := single(route) | conflict([route], sorted, distinct, len ≥ 2)
> ```
>
> The boundary mints only `single`. `conflict` arises from exactly one operation —
> **`consolidate`** of two records at one content address whose routes disagree — and
> that operation may only **widen**. *(the operation was world §4.3's **merge**, retired 2026-08-08; its equal-basis arm is now **`consolidate`**, which requires one canonical address — `2026-08-08-world-address-ruling.md` §5.4. This case was always the equal-basis one, so nothing about the lineage rule changes)* A `conflict` carrying fewer than two distinct
> routes is **unconstructible**: it would represent a conflict that never occurred, and
> a one-route `conflict` beside the corresponding `single` would be two spellings of
> one fact. **No ordinary API selects, replaces or removes a route**; "not editable" is
> a statement about routes, and widening adds one without touching any. There is no
> authoring path to either variant, so this is not the authored ancestry of the previous
> revision returning under a new name. It is the durable **descendant-side** claim
> substrate §5 requires; the view remains the resolution, and the basis is what makes
> non-resolution visible.
>
> **The limit, since the previous phrasing said "by any path":** the immutability above
> is a claim about **ordinary APIs**. A raw filesystem edit can rewrite a basis, drop a
> route from a `conflict`, or forge a `single`; no API guarantee reaches the filesystem,
> and the strong reading promised tamper evidence only §9's log can supply.
>
> **And "caught under audit" is itself too strong for one of those.** An audit
> recomputes against inputs that still exist. Consolidate `A` and `B` into `conflict([A, B])`,
> **delete `B`'s producing run**, then raw-write `single(A)` with a matching hash: the
> audit finds a well-formed basis whose one route resolves, and nothing surviving in the
> corpus says `B` was ever a route. **Route removal is detectable while the evidence it
> removed survives, and undetectable once it does not** — §11.11 and §11.14 composed,
> and §9's mutation log is the only thing that closes it.

**The tagged shape is what makes the consolidation rule expressible at all.** A previous
revision ruled that the operation keeps both bases while this section still defined *the*
basis as one immutable `(run, transforms)` tuple — so "both" had no representation,
`producer.transforms ≠ dataset.basis` had no meaning against two of them, and kernel
§5.1's tuple-shaped snapshot member could not hold the result. Ruling an outcome the
data model cannot express is the same defect as §3.1b's constructor naming fields that
did not exist, one document over. `single | conflict` is a discriminated union in
§3.1a's sense, canonicalized by `science.identity.v1` with the discriminator inside the
digest, so the two variants can never collide and a one-route `conflict` is not the
same bytes as a `single`.

The shape propagates rather than being unwrapped at each site:

| site | `single(route)` | `conflict(routes)` |
|---|---|---|
| traversal (substrate §5) | walk the route's ancestors | resolve **every** route's refs for reporting, and certify nothing |
| divergence test | compare each producer's `transforms` against the route | already divergent **on the tag**, checked before any comparison; "differs from the basis" is undefined against a set and is never evaluated |
| kernel §5.1 snapshot | the route's `(stored, resolved)` pairs | every route's pairs, sorted, under the `conflict` tag |
| independence | as certified by the walk | **`not-certified`** |

**A `conflict` has no resolution path, and saying "until resolved by evidence" implied
one that does not exist.** Nothing in this design retires a route, chooses between two,
or records that one has been shown wrong — that is the same missing machinery as
§11.13's retraction, reached from a different direction, and it is handed to
sub-problem 5 with it. Until then a conflicted dataset certifies nothing.
*(Amended 2026-08-03, `2026-08-03-correction-lifecycle-design.md` §4 and C7: the
route retirement this paragraph says does not exist now does. The word
"permanently" stood here and is withdrawn — retiring routes leaves the stored
basis byte-unchanged and computes the **effective** tag over the survivors, so
one survivor certifies over that route and zero is `not-certified`. Nothing in
**this** design retires a route, which is what the paragraph is really about, and
C1–C10 await implementation.)*

*(Amended 2026-08-19, `2026-08-19-conformance-cut-5.md`: cut 5 landed its
selected C1–C6 and C10 arms. The unselected clauses and C7–C9 remain deferred
to their named world-index, audit, and registry-compile dependencies.)*

**Why the conflict is kept rather than the consolidation refused**, which would be simpler and
was the obvious alternative: refusing leaves two records at one world address, which is
world §5's **duplicate-location** state — reported, refused at the write boundary, and
explicitly a migration state that must be resolvable. It also leaves every reference to
that address ambiguous, which §2.1 spends its argument preventing. So refusal trades a
dataset that certifies nothing for a *world* that cannot answer a reference, and the
second is worse. The cost is stated rather than hidden: this variant exists for a case
with zero measured instances, and its only outcome today is a permanent
`not-certified`.

Independence walks the basis transitively: each ancestor's own basis supplies the next
step. A basis entry that no longer resolves — an absent ancestor **or an absent
producing run** — is `lineage-incomplete` and certifies nothing. Kernel §5.1's lineage
snapshot digests the basis with the same `(stored ref, resolved uid or null)`
discipline it already used for edges, so the deletion moves the belief digest instead
of silently improving it.

**The dataset that already exists is not re-stamped**, which matters because §5.3's
successful replay produces one that does. The basis attests **one** derivation route,
recorded when the address was first minted; a second producing run adds a `produces`
edge and mutates nothing. That keeps the no-mutation property the edge direction was
chosen for, and it means the basis is deliberately **not** a complete account of every
route — only a durable one.

**A union over every producer and a single durable basis cannot both stand**, and a
previous revision of this section asserted them together. The rule it stated was that
`derived_from` is the union over all producing runs and that independence reads the
union. But the basis records exactly one route, so the union has routes behind it that
nothing durable holds. `R1` mints `D` from `A`, stamping `(R1, A)`. `R2` later produces
identical `D` from `B`, and the union adds `B`. **Delete `R2`:** every basis entry
still resolves, no reference dangles, and `B` simply leaves the closure — an assessment
over `D` can now be certified independent of one over `B`. The deletion **bought**
corroboration, which is the exact failure the basis was introduced to prevent, at a
route the basis never covered. Substrate §5's guarantee has to hold over **every route
independence reads**, and half a durable record satisfies it for none of them.

**Only one of the two can be repaired, and which one is forced rather than chosen.**
Deletion is detectable only where a **surviving node holds a reference to what was
deleted** — that is the whole content of substrate §5's orientation rule. After `R2`
is deleted the survivors are `D`, `A` and `B`; `A` and `B` know nothing of `D`, so the
only possible holder is `D`, and putting it there means **appending to a dataset node
that already exists** — the immutable, possibly-foreign node §5.2 chose the `produces`
direction specifically to avoid touching. So "make every route durable" is not
available at this cost, and the other option is:

> **Rule.** Independence reads the **basis and only the basis**. The `derived_from`
> view remains, as a **descriptive** relation over `produces ∘ transforms` — it is not
> belief-bearing, and no independence claim is computed from it. A producing run whose
> `transforms` set differs from the dataset's stamped basis is a **divergent
> derivation**: the walk emits `lineage-divergent` and independence over that dataset
> is **`not-certified`**. `D derived_from D` is **excluded** from the view: a run that
> transforms and produces one content identity contributes no edge.

The divergence rule is what stops "reads only the basis" from being the false-
independence hole the union was protecting against. A genuine second derivation of the
same bytes from a different ancestor **is** evidence that `D` and `B`-derived data
share content, and the basis cannot carry it — so the dataset stops certifying rather
than certifying from a record known to be partial. Not silently unioned, which was
undurable; not silently ignored, which would assert independence from an absence.

**The divergence test asks a reverse question, and reverse questions have a scope.**
"Every run producing `D`" is not answerable from the dataset: producing runs live in
corpora that need not contain it and need not be present, and world §5's index was
forward-only — address and alias, both answering *where does this live* *(dated to this
design's writing: the index held those two maps and nothing else. The **producers** map
this section goes on to require is itself the reverse map, and the **retraction** and
**coreference** maps added since are reverse too, so the index is no longer
forward-only — which is the argument's outcome, not a contradiction of it. The alias map
retired 2026-08-08, `2026-08-08-world-address-ruling.md` §4.3)*. Enumerated
against whatever happened to be checked out, the test silently shrinks: a divergent
producer in an absent corpus is not seen, `D` reads undiverged, and independence is
certified from an enumeration nobody bounded — belief depending on the checkout, which
R5 forbids. World §5 therefore publishes a **producer snapshot** — the producers map
plus a **coverage declaration** naming the covered corpora by **stable identity** — and
kernel §5.1 digests *that* pair, not the world index's identity and not the
**derivation receipt**, a separate record naming the exact corpus states the enumeration
was built from **and the identity of the enumeration rule that built it**. All three
exclusions serve one rule: belief reads **what was enumerated**, so a file move — which
rewrites two corpora, changing the address map and both corpus-state identities while
leaving the producers map untouched — must be epistemically silent (W5), and two rules
producing one map over one coverage must be one belief input. Certification is explicitly
**relative to declared coverage**, and two coverages are two belief inputs.

The snapshot is **derived**, and carries §7.3c's derivation discipline for the reason
that section established: an identity over a map with one entry deleted faithfully names
the smaller map, so hashing is change detection and the property needed here is
**completeness**. Recomputation against the named corpus states is what supplies it —
validated at explicit import and under audit, never on read. That makes it the fourth
consumer of the same discipline, beside verification derivation, the assessment facet
and the result manifest, and the fourth place a value called *derived* turned out to
need a boundary before anything downstream could rely on the word. §11.15 records what
coverage cannot reach even so.

**The exposure is confined, and worth stating rather than trusting.** For the case
that actually occurs — a **replay** — the second producer executes the same recipe,
so its `transforms` set *equals* the basis by construction, no divergence arises, and
§5.3's two-producers-one-dataset guarantee is untouched. Divergence needs byte-identical
output from a genuinely different ancestor set, which is exotic for real transforms and
has a measured population of zero. What it is **not** is impossible, and §11.14 records
what remains: deleting the divergent run restores certification, because no survivor
holds a reference to it, and afterwards nothing distinguishes that corpus from one in
which the run never existed. An earlier revision called this "change detection, not
loss detection" and claimed it was strictly better than the union — both wrong for the
same reason. Belief is a **computed view** (kernel §6), so no prior digest is retained
for the new one to differ from; G3 guarantees that two *available* states hash
differently and retains neither. It is the undetectable-history limit of G4 and G8,
stated as such.

There is **one** durable form of the same conflict, and it arrives by a different
route: **`consolidate`** of two records at one content address whose routes disagree
widens the survivor's basis to `conflict`. *(the operation was world §4.3's **merge**, retired 2026-08-08; its equal-basis arm is now **`consolidate`**, which requires one canonical address — `2026-08-08-world-address-ruling.md` §5.4. This case was always the equal-basis one, so nothing about the lineage rule changes)* That conflict is stored on the descendant, so
it does not evaporate when a run is deleted — the contrast is worth holding onto,
because it shows the limit above is about *where the record sits*, not about divergence
being inherently unrecordable.

Self-edges are excluded because an identity transform is legitimate — a repackaging
run that emits its input bitwise is a real thing — while `D derived_from D` is a
one-node cycle, and substrate §5 step 2 emits `lineage-incomplete` on any cycle. Left
in, the honest no-op would poison the closure of everything downstream of it. It is
also not divergent: a run whose `transforms` and `produces` name one identity adds no
ancestor the basis lacks. Cycles of length greater than one are **not** excluded: those
are genuine corruption and the existing finding is the correct response.

**Both of these edges were authored, and both are belief-bearing.** The diagram said
a dataset is produced by a run and `derived_from` other datasets without binding
either to anything the run actually did. Two consequences, and the second is worse:

- **A different dataset can claim the run.** Nothing tied the produced dataset's
  content identity to the run's result, so an entity whose bytes the run never
  emitted could carry the production edge and inherit its provenance.
- **An omitted ancestor buys false independence.** Kernel §4.2.1 derives
  independence from **complete and disjoint** ancestor closures, and substrate §5
  walks `derived_from` to certify it. A shared upstream dataset simply left out of
  the authored edges makes two assessments look independent when they are not —
  and independence is the multiplier on corroboration, so this inflates belief
  rather than merely mislabelling it.

> **Rule.** The **boundary mints the output dataset from the result manifest's single
> output entry** (§4.2d): the dataset's basis is **that entry's content identity**,
> and the run's `produces` edge is emitted with the run.
>
> *Amended 2026-08-09 (admission ramp §6.2).* The basis is still the content
> identity and nothing else, but the **address** is the dataset basis projection
> over it — deduplicated, sorted, `\n`-joined, digested — because an acquired
> dataset declaring the same bytes must take the same address, and a projection
> with a cardinality special case would not give it one. The paragraph below is
> why the projection excludes names, and is unaffected. The `transforms` partition
> is likewise taken from the recipe, not from an authored list, and dataset lineage
> follows as a view over the two. The ordinary API offers no path to attach either
> edge by hand.

**The dataset's basis is the output's content identity, not the manifest's digest.**
The manifest is `(logical name, content identity)` pairs, so digesting *it* would put
the **logical name** into the dataset's world identity: the same bytes emitted as
`matrix` in one run and `normalized_matrix` in another would mint two different world
datasets. World §4.2 rules a dataset's basis to be content identity precisely to keep
nominal handles out — provider identifiers and accessions are **authority-identifier
fields**, not the basis *(restated 2026-08-08: they were called aliases, and no alias is
stored — `2026-08-08-world-address-ruling.md` §4.1)*, and a logical output name is exactly such a handle. Wrapping it in a digest
does not launder it.

The manifest remains the **run result**, which is what §7.2's equivalence rule
compares and what §4.1 says the verdict reads. Two records, two purposes: the
manifest identifies *the execution's output*, the entry's content identity
identifies *the data*. This is only unambiguous because §5.2 bounds the shape to one
output; a multi-product rule would have to say which entry is the dataset, which is
part of why §13 leaves that open rather than guessing. Note what that bound does
**not** buy: one output per run gives one dataset per run, and says nothing about how
many runs produced a given dataset — §5.3 guarantees at least two whenever a replay
succeeds.

**Lineage-bearing versus auxiliary is a role distinction, and it belongs in
`inputs`.** §4.6 already partitions inputs by role for the assessment shape, where
`observes` and `reads` decide eligibility; the same mechanism decides here what
ancestry means. A dataset that contributes content to the output is
**lineage-bearing** and appears in the closure; a gene-name lookup table or a
plotting palette consulted along the way is **auxiliary** and does not. Deriving
lineage from *all* inputs would make every run that consults a reference file share
an ancestor with every other one, collapsing independence to nearly nothing —
conservative, but wrong in the way §7.3's `lineage-incomplete` is wrong, and just as
untrue.

The role is declared in the recipe before execution, which keeps it out of reach of
the result: an author who realises after seeing two results that a shared ancestor is
inconvenient cannot reclassify it without minting a different recipe, and hence a
different run.

**Pre-declaration stops shopping, not omission — and the derived edge is only as
honest as the classification it derives from.** Deriving `derived_from` from the
recipe closes the *authored-ancestry* hole and leaves the one behind it: classify a
shared **empirical** ancestor as `reads`, and the boundary faithfully omits the edge.
Two assessments then read as independent, and independence multiplies corroboration,
so belief goes **up** on a single mislabelled input. This is the sixth appearance of
the same pattern in this document, and the tell is now familiar enough to state as a
question: *what is the free input to the thing I just made derived?*

There is no computable rule separating "a reference table that contributes no
evidential content" from "an empirical dataset I would rather not share an ancestor
with". So it takes the same shape as §7.3's code-lineage independence — the other
place where nothing computable distinguishes the honest case from the convenient one:

> **Rule.** Excluding an input from the lineage closure requires an **exclusion
> certification carried inline on that `reads` entry** of the recipe's `inputs`
> member: a rationale and an attribution, frozen into **recipe identity** with
> everything else. An uncertified `reads` input leaves the closure **incomplete**,
> and independence over that closure is **`not-certified`** — never assumed.

**Inline, because there is nothing for it to be a reference to.** A first version
said "an authored, recorded certification" without saying where it lives, and the
kernel's kinds — eight then, ten now — include no *code-lineage* certification
kind (amended 2026-08-03: executable-instrument certification is the
`instrument-certification` kind, 5b §7.2; authored claims stay inline) — the same
discovery §7.3b made about code-lineage claims, and the same resolution: put the
content where it is used rather than inventing a new kind to point at. Carrying it on the input entry gets
three properties for free. It is **hashed**, because `inputs` is a recipe member. It
is **frozen**, so adding or withdrawing a certification mints a different **recipe** —
and therefore cannot alter the run that already exists, which is the same guard that
stops role reclassification. It mints no run by itself: a recipe is a description, and
only executing it produces one. That distinction is what limitation 13 turns on, and
it is stated here so the guard is not read as a correction path.
And it is **in G3's reach** — though only after the kernel §5.1 repair this round
forced. That claim was written while G3's first member was a bag of bare **facet
digests**, which contains no run identity and no assessment identity, so a
certification added or withdrawn without changing any facet **value** moved nothing
in the belief digest and the sentence was simply untrue. Keying the member by
assessment identity puts `(spec, run, proposition)` in the digest, the run address
moves with its recipe (R2), and the reach the sentence claimed now exists. The tell
is worth keeping: *a property claimed on behalf of another document is a claim about
that document's current text.*

Uncertified therefore costs corroboration rather than granting it, which is the
correct direction of failure and the one substrate §5's `lineage-incomplete` already
takes. It is a real cost: routine reference lookups now need certifying before two
runs that share one can be called independent.

**And the limit, stated rather than implied: this guarantees attribution, not
truth.** A false certification — an empirical dataset declared evidentially inert —
still omits the edge, still yields false independence, and still inflates belief. What
changes is that the claim is now *someone's*, recorded with a rationale, frozen into
an identity, and visible to review. That is the same bargain §7.3 strikes for
code-lineage independence and world §5.1's coreference attestation *(2026-08-09: as
above, `consolidate` records no claim and is the wrong comparand)*, and it is the best
available
where nothing computable decides the question. §11 records it as a limitation rather
than leaving it read as a fix.

**Freezing gave the certification durable attribution and left it with no way to be
withdrawn**, which is worse than the limitation above and is a different problem.
Editing the certification mints a different **recipe** — but a recipe is not a belief
input; only a **run** is, and only executing the new recipe mints one. Re-execution
therefore *adds* a corrected run beside the original, and the original, with its false
certification, remains an active belief input at its original address. A reviewer who
establishes that an exclusion was wrong can attribute it, and can do nothing else. So
review is not a correction path here, and the design should not be read as though
attribution implied one.

The gap is **not specific to certifications**, and that is the useful part of finding
it here. Nothing in this design retires *any* run or the assessment derived from it:
a run whose code is later found defective, whose environment is later found
mis-captured, or whose input is later found corrupt keeps contributing exactly as
much as it did on the day it was recorded. Assessments are immutable by construction
(§5.1), addresses are keys over inputs the correction does not change, and re-running
is additive. What the system lacks is a **retraction**: an attributed, immutable
record that removes a named **belief input** from the computation without editing it.

**"Removes a named run's assessment" was the wrong statement of it, and the case that
motivated the whole paragraph is the one it missed.** A `dataset-production` run
**has no assessment** (§5.2) — it targets no proposition — so a false exclusion
certification, which lives on exactly such a run, is untouched by an
assessment-shaped retraction. What a retraction names is whatever the belief
computation *reads*: an assessment, a production route, or a certification's effect on
a lineage closure. Naming the reachable output rather than the input under correction
is the same error as digesting the lineage the design finds tidiest instead of the
lineage aggregation reads (kernel §5.1), one layer up.

> **Requirement handed to sub-problem 5**, where certification and conformance
> already live (§13). **Delivered 2026-08-03**
> (`2026-08-03-correction-lifecycle-design.md`), with all five clauses below
> intact and one addition this section did not ask for: the eligibility contract
> is **procedural** — named target, attribution, typed reason, recorded grounds,
> symmetry — because nothing certifies a retraction true, so the system makes one
> expensive to issue invisibly instead. A retraction must be **additive** — a new node, never an edit,
> for kernel §3.3's reason; **attributed and rationale-bearing**, since like every
> other judgment here it is a claim rather than a computation; a **belief input**, so
> kernel §5.1's digest must cover it or a retracted and an unretracted corpus would
> hash alike; **structurally subtractive** — its only effect is that a named input is
> no longer read, with the belief then recomputed by the ordinary policy; and
> **itself eligibility-bearing**, since a subtractive operation is not a safe one.

**"Monotone downward" was wrong, and wrong in a way worth keeping visible.** An
earlier phrasing required a retraction to lower belief or leave it unchanged, on the
reasoning that anything able to raise belief is an authored-belief channel. But
belief aggregates support *and* dispute: retract a **refuting** assessment and support
goes **up**. So the constraint is unsatisfiable for half its legitimate uses, and a
retraction that refused to apply because the recomputed value rose would be refusing
to correct a false refutation.

The constraint belongs on the **operation**, not on its result: a retraction removes a
named input and nothing else, and the recomputation moves wherever the policy takes
it. That is a general slip — **constraining the output of an operation that should be
constrained in its form** — and it is the fifth distinct place in this document where
a rule was written about the wrong noun.

Making it structurally subtractive is what keeps it out of the authored-belief
channel, but it is not sufficient on its own, because "remove the evidence against my
claim" is a subtractive operation with an inflationary result. A retraction therefore
needs its own eligibility contract — who may issue one, against what standard, and
what makes it reviewable — which is why it belongs beside equivalence- and
interpretation-rule certification rather than being bolted onto this section.

Until that exists, the honest statement is the one §11 now carries: **a reviewed
false certification stays epistemically active.** Attribution is durable; correction
is not yet possible.

**One output per dataset-production run**, until multiple products are measured. A
single dataset or package keeps the run's `produces` edge unambiguous and the
equality rule in §5.3 bitwise over one address. Multi-product runs are a real pattern and are
deliberately not designed here — §13 records the question rather than a guess, and
the measured population is currently zero.

The two shapes are **structurally exclusive**, and R7 tests it: a run that names
no spec cannot stand under an `assesses` edge, and a run that produces an
assessment must name a spec carrying a target.

R23 tests the minting and the closure.

### 5.3 A dataset-production run declares no equivalence rule, and still verifies

The rule is fixed rather than absent. A dataset's basis is **content identity**
(world §4.2), so a replay either produces the same dataset address or it does not:
the comparison is bitwise, and **no tolerance is declarable**. Only assessment runs
declare an equivalence rule, because an assessment's output is a **claim**, and two
claims can agree while their bytes differ.

But a differing replay yields **two facts, not one**, and an earlier draft recorded
only the first:

1. it minted a **different dataset entity** — correct, and the identity consequence
   of content addressing;
2. it **failed to reproduce the original dataset** — a verification result, with
   nowhere to live if identity is said to have absorbed it.

**Identity does not erase verification.** Saying "a different dataset, therefore not
a failed reproduction" quietly converts a reproducibility failure into a naming
event, which is the same move as reading a failure to look as a finding of absence.

> **Rule.** `verification` (kernel §3.3) covers **both** run shapes.
> A **dataset-production verification** references two runs, carries the built-in
> equivalence rule `dataset-content-equality/v1`, and **never gates belief** — it
> carries no `verifies → assessment` edge because there is no assessment to admit.
> An **assessment verification** additionally points at an assessment and controls
> admission.

So a nondeterministic transform records both: a new dataset entity, *and* a
`failed` dataset-production verification against the original. Prior assessments
stay bound to the prior dataset, and no belief moves. R11 asserts all four.

What such a transform loses is not correctness but reproducibility, and its
`nondeterminism_contract` recipe member is where that was declared in advance.

## 6. Workflow DAGs are imported, not authored

### 6.1 Why

An authored DAG is a second description of an executable definition, and the two
drift. The evidence is already in the tree: `templates/workflow.md` declares a
`method:` field no model reads; `workflow-step`'s descriptor conflated definition
and execution until `t088` split it; its template minted the wrong id prefix; and
**zero** `workflow-step` entities exist to this day against 20 `workflow` records.

The kernel's ruling (§4.4) is that `workflow` and `workflow-step` become imported
DAG structure and `code-file` is closure content, not an entity. This design
supplies the import.

### 6.2 The definition is declared; the trace is observed; seeds key on neither

Three artifacts, and which side of execution each falls on decides everything:

| artifact | side | in identity? |
|---|---|---|
| **workflow definition** — Snakefile, Nextflow config, Makefile, notebook cell graph | declared, pre-execution | **recipe member** |
| **engine-native execution trace** — job ids, rule names, wildcards, per-job inputs and outputs | observed, post-execution | **occurrence member** |
| **normalized DAG** — nodes, edges, per-node code and declared nondeterminism | derived, after the fact | **never** |

Two earlier revisions each got one of these wrong, in opposite directions. The
first keyed realized seeds by *normalized-DAG* step identity while admitting the
normalized DAG is lossy for dynamic workflows — a derived structure carrying
identity. The second moved the keying to the *engine-native trace* and put the
trace in the recipe — which fixed the lossiness and broke something worse, because
a post-execution artifact containing transient job ids cannot sit in the part two
identical executions must share.

> **Rule.** Seeds are keyed by a **stable semantic job key** — the rule or process
> name plus its canonicalized wildcard binding — never by a transient engine job id,
> and **nested by stream key**: `realized_seeds[job_key][stream_key] = seed`. The
> recipe's `nondeterminism_contract`, in its **`seeded`** variant, carries the
> **seed plan**: the **logical streams**, the roots they map to, and a versioned
> **seed-derivation rule** with `seed = f(stream_root, semantic_job_key, stream_key)`
> (§3.1a), projected whole from the frozen spec for `assessment` runs (§4.2a). The
> **workflow-definition snapshot** carries the **per-family stream declaration**, and
> the boundary enforces `union(family streams) == recipe.seed_plan.logical_streams`
> (§3.1a). Realized seeds are **occurrence** members, and conformance **is a
> precondition on scope derivation** (§4.2, §7.3): it never rewrites the recipe, and
> a non-conforming execution derives `not-certified`.
>
> Conformance is checked at **two levels**, and a seeded run must pass both:
>
> - **per job** — each executed job is compared against **its own family's** declared
>   stream set. A job that realized a stream its family does not declare, or omitted
>   one it does, is non-conforming. A wildcard instance inherits its family's
>   declaration.
> - **over the occurrence** —
>   `union(realized stream keys) == recipe.seed_plan.logical_streams`. A declared
>   logical stream that no executed job realized is non-conforming, however well each
>   individual job matched its family.

**One key per job was one dimension short**, and the failure is quiet rather than
loud. A single job drawing `model-initialization` and `resample-draws` has two
streams and one job key, so a flat map has one slot for two seeds: one is dropped or
overwritten, and the record looks complete because every job key present in the trace
has a seed against it. Conformance would pass while half the run's nondeterminism
went unrecorded, and a replay reproducing only the recorded stream would derive
`clean-environment` honestly and wrongly. §3.1a's totality over streams has to appear
in both records or it constrains nothing — the plan can name two roots while the
occurrence has nowhere to put the second seed.

The nesting is not new machinery: shipped `RunFingerprint.step_seeds` is already
`dict[str, dict[str, int]]`, which is the same two-level shape one level off in what
the inner key means. This fixes the key semantics rather than the container.

**Definition coverage is not execution coverage**, which is why the second
conformance level exists. §3.1a's set equality is checked against the workflow
*definition*: it establishes that some family claims every declared stream. It says
nothing about whether that family ever **ran**. A definition can satisfy the equality
exactly while the family claiming `resample-draws` produces **zero jobs** — filtered
out by a conditional, unreached because its inputs were empty, or simply not on the
path to the requested target — and every per-job check is then vacuously satisfied,
because the jobs that would have been checked do not exist. Two runs reproduce the
omission identically and reach `clean-environment`.

This is the third time the same shape has appeared in this section: an obligation
declared in one record and unenforced in the next. The plan named streams the
occurrence could not key; the spec named streams the definition need not claim; the
definition claims streams the execution need not draw. Each fix pushed the gap one
record downstream, and the occurrence is where it stops, because the occurrence is
the last record — after it there is nothing left to be inconsistent with. **A
declaration is only binding at the last record that can contradict it.**

A derivation rule rather than an enumeration is what makes this work for dynamic
workflows, and the per-family declaration is what keeps that true at the stream level:
a checkpoint fan-out cannot be listed before execution, but every job it creates
belongs to a **family that was declared**, inherits that family's stream set, and has
a semantic key — so every seed it needs is determined and every stream it owes is
known, without anyone enumerating the instances. The lossy normalized DAG then keys
nothing and carries nothing, which is the only safe place for it.

**The workflow definition alone is not the execution trace**, and keeping the trace
out of identity is what lets that be true without cost.

**A target is not a requested job set, and conformance must not pretend otherwise.**
Adding `invocation` made the *request* reconstructible, and an earlier revision
promptly over-read that as making job-set divergence measurable against it. It is
not: this section has already said a checkpoint fan-out cannot be enumerated before
execution, so a target names an outcome and the engine decides which jobs reach it.
Comparing an executed job set against a "requested" one that was never enumerable is
a check with no left-hand side — the same error as the seed plan's, except that here
the missing enumeration is genuinely impossible rather than merely absent, which is
why the answer is to narrow the claim rather than to add a member.

> **Rule.** For a single run, job-set conformance asserts exactly two things: the
> **requested targets were satisfied**, and **every executed job belongs to the
> engine-derived trace** for those targets under the frozen definition. It does not
> assert that the job set matches a prior enumeration, because none exists.

**Job-set equality between two runs is not part of any verdict.** The previous
revision moved it out of conformance and handed it to §7 "as an equivalence rule over
the two occurrences" — which §7.2 cannot express: an equivalence rule is
`(original execution result, replay execution result) → passed | failed |
inconclusive`, and §4.1 is emphatic that it reads **results and never recipes or
occurrences**. That separation is load-bearing; it is what lets a declared tolerance
forgive differing bytes. Reassigning a job-set comparison to that evaluator asked it
to read a record it is defined not to see, which would have been discovered at
implementation time as an impossible signature, or — worse — closed by widening the
evaluator and losing the separation.

Relocating a problem is not solving it, and "some other section owns this" is the
form that error takes in a design document.

> **Rule.** Job-set differences between two runs are **comparison-report
> diagnostics**. They are recorded, they are visible, and they contribute to **no
> verdict and no scope**. No equivalence rule reads an occurrence.

Nothing is lost that was measured to be needed: no spec today asks the question, and
a data-dependent workflow makes it the wrong question anyway, since a replay over
different held inputs legitimately runs different jobs. If a measured use later
requires it, the honest form is an **occurrence-aware pairwise rule** with its own
signature, versioning and doctrine — not a quiet widening of the equivalence
evaluator. The report carries the difference in the meantime, which is exactly where
§7.3b already puts facts that inform a reader without gating admission.

`WorkflowRunEntity.workflow` and the `register-run` refusal built on it go with all
of this: a run does not name a workflow entity, it carries one.

### 6.3 "Which runs executed the same pipeline" is computed

Runs sharing a `workflow_definition_identity` are executions of the same definition.
That is a query, not an entity, and a project-scoped **view** (world §3) may name the
set. No `workflow` kind is required to express it.

`method` (78 records) resolves the same way as the kernel's §4.4 accounting says:
the scientific description is spec content, the stochasticity classification `t088`
put on it is a property of a step in the imported DAG, and what remains is a note.
The mapping is not mechanical and lands in sub-problem 7.

### 6.4 One schema, one adapter, no plugin framework

The engine question is measurable rather than arguable, so it was measured. Across
the projects holding `workflow-run` records:

| project | Snakemake files | Nextflow files |
|---|---|---|
| mm30 | 54 | 0 |
| natural-systems | 25 | 0 |
| protein-landscape | 14 | 0 |
| health/post-acute-infection | 1 | 0 |

**94 Snakemake files, zero Nextflow.** There is no measured second-engine
population, and Snakemake already exposes enough for a first execution-boundary
adapter: job-DAG output, D3 JSON, detailed summaries, workflow archives, and
provenance metadata.

> **Ruling.** One **minimal normalized schema**, one **Snakemake adapter** now, and
> **no plugin framework**. A second adapter is written when a second engine actually
> exists in a project, not in anticipation of one.

**Snakemake is not replaced.** The execution boundary wraps it — capturing the code
bundle and environment manifest before execution and the trace after — rather than
substituting a Science-owned runner for a tool the projects already run. This closes
the DAG open question the first draft left open.

## 7. Replay eligibility, equivalence, and verification

### 7.1 Replay eligibility is not an epistemic verdict

Three distinct things, routinely collapsed:

| | what it is | depends on |
|---|---|---|
| **closure completeness** | whether this is a run at all (§2) | the record |
| **replay eligibility** | whether a replay could be attempted here and now | what this checkout can resolve |
| **verification** | that a replay happened, and what it found (kernel §3.3) | what was recorded |

> **Rule.** A run whose artifacts are not resolvable in this checkout is **not**
> `unverified`, `failed`, or degraded. It is a run whose verification has not been
> attempted here. Replay eligibility never becomes a verdict.

This is the third appearance of one principle, and naming it once is why the three
documents agree: `t077`'s determinism test (identical verdict with data files
present and absent), world §5.1's `not-present` ≠ `unknown`, and this rule are the
same statement at three layers — **a failure to look is not a finding of absence.**

Its sharpest consequence is a guarantee in its own right — **and it must be stated
at exactly the scope on which it holds**, because the obvious wider form is false:

> **Belief does not depend on artifact availability *in this checkout*.** Making
> the bytes unreachable here — unmounting a volume, dropping a corpus from the
> working set — while **at least one controlled copy remains held** changes neither
> `belief_input_digest` nor any assessment's admission state.

The qualifier is load-bearing. **Destroying the last held copy is not an
availability event**: kernel §2.2 requires that we can produce the exact bytes on
demand, so an input with no surviving copy is no longer held, the eligibility
predicate fails, and admission **must** change. Availability is about reach;
holding is about existence, and only the first is free.

Without this, belief would flicker as data volumes are mounted and unmounted, and
G3's recomputability claim would be false in the ordinary case. R5 tests it.

**The wider claim — "belief does not depend on what is checked out" — does not
hold, and asserting it would be a computation from missing inputs.** Removing the
*corpus* removes the assessment, verification and dataset **facets** themselves,
and world §5.1's index maps addresses to locations; it does not carry facets. The
correct result is that belief is **not computable here** — `not-available` — which
is a computability state, not a belief that happens to be unchanged. Reporting an
unchanged belief in that situation would assert a recomputation nobody performed.

**Three** cases, and none of them may be run together:

| what was removed | result |
|---|---|
| artifact bytes **unreachable here**, a controlled copy still held | belief **unchanged**; replay eligibility `not-available` |
| the **last held copy** of an `observes` input destroyed | the input is no longer **held**; eligibility fails and admission **changes** — a **`def`** dependency (formal model §4.2, ρA8): held-ness selects *which answer you get*, not what the answer says |
| the **corpus holding the records** | belief **not computable here**; addresses still resolve to `not-present`, never `unknown` |

Making the second case computable would require a **separately published
belief-input snapshot** carrying the digest members of kernel §5.1 — which the
world index deliberately does not contain. §13 records it as open.

**The second row's dependency is typed, and the typing is what keeps G3 true**
(added 2026-08-05 — formal model §4.2, ρA8). The three edge kinds a belief
reading depends on are not interchangeable: a `sem` edge changes the belief's
**value** and must therefore be in the closure digest; a `def` edge selects
**which arm of the answer is reached at all**; a `bind` edge merely routes.
Held-ness is a `def` edge. Typing it as `sem` — the reading a casual glance
invites, since destroying a copy plainly changes the outcome — would make G3
**false**: two configurations differing only in whether the last copy survives
share one `belief_input_digest` while yielding different answers. Typing it as
`def` instead restricts G3 to its `Belief` arm, where the digest does determine
the value, and leaves R5's three arms exactly as banked. What is *not* supplied
by this typing is any mechanism making the destruction **recorded** — nothing
observes it, so the case is reached by a check failing rather than by an act
being committed (formal model ρO2).

Held-ness is a **world** property — the bytes exist somewhere we control and are
content-addressed — while availability is a **checkout** property. Kernel §2.2's
"we can produce its exact bytes on demand" is a claim about the world, not about
the working directory.

### 7.2 The equivalence rule and its evaluator

Nothing in the toolkit compares two runs' outputs today. `numeric_verification.py`
compares prose numeric claims against bound artifacts, which is adjacent and is
not it. `t078` is still `proposed`. This is net-new machinery.

> An **equivalence rule** is declared in the spec, frozen with it, and identified
> by a versioned rule id. It maps
> `(original execution result, replay execution result) → passed | failed | inconclusive`.

It reads **results** and never recipes (§4.1). That separation is what lets a
declared tolerance forgive differing output bytes without the differing bytes having
already disqualified the replay.

- The **default and strictest** form is content-identity equality over the output
  manifest. Anything weaker is a declared tolerance carrying a versioned rule id,
  and kernel §3.1 already requires it to be declared *before* execution.
- **`inconclusive` is a real verdict, never a silent pass or fail.** An output
  missing, an unreadable artifact, a reader error: the rule could not be
  evaluated, and saying so is the answer. This reuses `numeric_verification.py`'s
  discipline, where a resolver or reader error always becomes `error` and an
  opaque locator always becomes `unverifiable` — never a silent pass and never a
  hidden read.
- The evaluator is versioned like `belief_weights` and fingerprint v1, and a v2
  produces **disjoint** rule identities. §3.1b's binding rule applies here without
  change: the identity must resolve to a **held implementation** or to a **registry
  entry with conformance fixtures**, since versioning a symbol is not versioning
  behaviour and two installations disagreeing about `tolerance-1e-6/v1` would produce
  two verdicts from one comparison.

### 7.3 Verification scope is derived, not authored

Kernel §3.3 gives verification a `(scope, verdict)` pair. `verdict` comes from the
evaluator. `scope` is not authored — but neither can it be inferred from the crude
signals an earlier draft used. Two of the three rows were unsound:

- **A different host does not make an environment clean.** A fresh container on one
  host is a clean reconstruction; a pre-existing environment copied to a second host
  is not. Deriving `clean-environment` from host difference meant **changing a
  hostname could buy admission** — a machine-name field controlling belief.
- **Different code bytes do not make an independent implementation.** A comment edit
  changes `code_identity`. And sharing only the *proposition target* ignores the
  estimand, the parameters and the interpretation rule, so two runs answering
  different questions about one proposition would have counted as corroborating
  implementations.

The derivation therefore rests on evidence, not on difference:

**Both executions must have conformed to their recipes.** This precondition governs
every row below, and without it the whole table can be satisfied by runs that did
not do what they recorded (§4.2): equal recipes, qualifying receipts and equivalent
outputs say nothing about whether the realized seeds followed the declared seed plan,
whether the requested targets were satisfied, or whether the executed jobs belong to
the engine-derived trace (§6.2). A non-conforming execution yields **`not-certified`**
regardless of everything else, and the conformance result for both runs travels in
the comparison report (§7.3b).

| relation between the two runs | derived scope |
|---|---|
| equal recipe, no qualifying receipt | `same-environment` |
| equal recipe **and** a boundary receipt attesting a fresh environment instance reconstructed from that recipe **and** attesting the confinement capabilities §7.3a requires | `clean-environment` |
| **same `spec_identity`**, same `observes` input identities, different `code_identity`, **and** certified code-lineage independence | `independent-implementation` |
| either execution did not conform to its recipe, **any required certification subject without a standing certification** under the explicitly selected cut and epoch (amended 2026-08-03 — the per-shape required subject set, 5b §7.6), or anything else | **`not-certified`** |

`not-certified` is a real fourth state and admits nothing, exactly as substrate §5's
independence certification refuses to read an absence of information as a verdict.
The two are the same discipline applied to two different questions.

**The receipt is an observation, not an assertion, and it attests two things.** The
execution boundary records that it constructed a fresh environment instance from
the recipe **and** that execution was confined to the closure (§4.4b).
Reconstruction alone was the first version of this rule and was not enough: an
environment can be rebuilt correctly and then read a file nobody declared. Under §2
no attested component is admissible, so **a clean-environment verification requires
the replay to have run through the boundary.** A replay performed out of band can be
recorded and derives `same-environment` at best.

#### 7.3a Confinement qualifies by capability, not by version number

An earlier revision said the receipt's `boundary_policy` had to be "at or above" a
required version. **Version identifiers do not form a strength ordering.** `v3` may
drop a confinement `v2` had; two policies may be incomparable; and a rule that
compares them as if they were ranked is a roster pretending to be a predicate — the
thing kernel §4.1 rejects by name.

> **Rule.** A policy **qualifies** for `clean-environment` when the receipt attests
> that it provided every required **capability**:
>
> - execution proceeded **from the captured bundle**, not from a working tree;
> - filesystem reads and writes were **confined to the closure** — held code, held
>   environment, declared inputs, the boundary-owned output root;
> - **network access was denied**, or restricted to held, content-verified fetches.
>
> A `boundary_policy` names which capabilities it provides. Qualification is
> evaluated over that set, and a policy providing all of them qualifies whatever its
> version string says.

This keeps confinement graded without pretending it is ordered: a run under a policy
missing any capability is still a valid run, and simply cannot reach
`clean-environment`.

**Code-lineage independence is certified by an authored, recorded claim** with a
rationale — the same shape as world §5's **coreference attestation** *(2026-08-09: this
cited world §4.3's merge, and the 2026-08-08 sweep repointed it at `consolidate`, which
is wrong in the other direction — `consolidate` is a storage repair that asserts nothing
and carries no rationale. The attested claim with recorded grounds is the attestation,
`2026-08-08-world-address-ruling.md` §5.1)*, and for the same reason: nothing computable distinguishes an
independent reimplementation from a copy with the comments rewritten. Absent that claim the scope is `not-certified`, never
optimistically upgraded. §11 records the resulting soft spot honestly.

This keeps kernel §3.1's definition computable — *a second, full execution in a
fresh environment reconstructed solely from the captured closure* is a second run
with an equal **recipe** identity, a distinct **occurrence**, and a receipt proving
the reconstruction — while removing the two places where a difference was being read
as evidence.

Making scope derived rather than asserted matters because scope decides admission
(only `clean-environment, passed` admits). An authored scope is a field whose value
an author can raise; a derived one is not. R4 tests both halves.

#### 7.3b A verification must name the evidence its scope rests on

World §4.2 gives `verification` a basis over *(two run identities, equivalence-rule
hash, scope, verdict)*. That is **not sufficient**, and the reason is the same
mechanism §7.3 just introduced: scope now depends on records that live outside both
runs. A code-lineage certification turns `not-certified` into
`independent-implementation`, and under the old basis two *different* certifications
supporting the same pair of runs would produce **one** verification address —
collapsing two distinct claims — while deleting the certification would leave the
verification asserting a scope with nothing behind it and **no dangling reference**
to show for it.

> **The verification basis is:**
>
> - the **ordered** original and replay run identities
> - the equivalence-rule identity
> - the **comparison report / observed-differences** identity — which **carries the
>   scope evidence inline**: the qualifying boundary receipts, both executions'
>   conformance results, and the code-lineage certification where one is relied on
> - the **scope-derivation rule** identity
> - the derived **scope** and the **verdict**

Ordering matters because "A replays B" and "B replays A" are different claims.

**Scope evidence is not a separate basis member.** An earlier revision listed it
beside the comparison-report identity, which was correct while the evidence was
referenced and became redundant the moment it was embedded: the report is immutable
and content-identified, so its digest already moves when any embedded receipt,
conformance result or certification claim differs. Listing both would state one
requirement twice and invite an implementation to compute a digest over evidence the
report also digests — two answers to what the evidence is, which is the defect §4.3
is built to prevent.

**The scope evidence is embedded, not referenced — an earlier revision promised an
edge that cannot exist.** It claimed the verification holds a reference to a
code-lineage certification, so deleting the certification would leave a dangling
edge, by analogy with substrate §5's orientation rule. The analogy fails: that rule
works because *both* ends are nodes, and here neither end is. There is **no
*code-lineage* `certification` kind** in the kernel — ten kinds since 2026-08-03,
and its `instrument-certification` (5b §7.2) certifies executable instruments,
never authored lineage claims — and no relation signature for one,
and a **boundary receipt is nested inside a run**, not a node at all. The promised
dangling edge is unconstructible.

> **Resolution.** The **comparison report** carries, inline and canonically, the
> code-lineage certification claim and the identities of the receipts relied on. The
> report is immutable and content-identified, and its digest already participates in
> the verification basis.

Different certifications therefore still mint different verifications — the property
the edge was wanted for — and no ninth kernel kind is added to get it.

What is genuinely given up is stated rather than glossed: **the verification cannot
notice that a certification was later withdrawn**, because it holds the claim's
content rather than a live pointer. That is consistent with a verification being
immutable in the first place (kernel §3.3): the remedy for a certification found
false is a **superseding verification**, exactly as for any other correction, not a
silent revaluation of an existing one.

This **amends** world §4.2 rather than merely commenting on it; §14 records it with
the other amendments.

#### 7.3c The comparison report is derived too, or none of the above holds

§7.3 refuses an authored `scope`, and §7.3b moves the evidence scope trusts into the
comparison report. Neither said where the **report** comes from, and that omission
undoes both: refusing to let an author write `scope: clean-environment` accomplishes
nothing if the same author can write `conformed: true` and a qualifying receipt into
the report that scope is derived *from*. The guard would sit one field downstream of
the value it guards — a scope derived, faithfully, from fabricated inputs.

This is the same defect as §4.2a's, in the same shape: a derivation is only as
trustworthy as the provenance of its arguments. There, projection had to reach the
root seed; here it has to reach the report.

> **Rule.** There is **one constructor** for a `verification`. Its arguments are the
> **ordered run refs**, an **optional code-lineage certification**, an **optional
> report-position citation** — added 2026-08-11 (the act-report design §4): the cited
> finding's resolved content embeds inline in the comparison report with **(act-report
> ref, entry index)** as provenance, and the code-lineage certification remains the
> **only** authored claim input — and — added 2026-08-03 (5b §7.6) — the **explicitly
> selected contract identity and epoch** for certification discovery — nothing else.
> It resolves the equivalence-rule **identity** **from the original run's frozen spec**
> for `assessment` runs, or from the fixed `dataset-content-equality/v1` rule for
> `dataset-production` runs — and its **implementation from the original run's
> frozen `rule_bindings`** (amended 2026-08-03, 5b §6: the binding froze before
> execution, and no selection argument exists) — and refuses a pair of **mixed
> shapes**. It then
> **derives** the comparison report, the verdict and the scope. Every scope-bearing
> fact in the report — each execution's conformance result, each boundary receipt
> and the capabilities it attests — is **read from the runs**, never accepted as an
> argument.
>
> The **only** authored input is the **code-lineage certification**, which is
> authored by construction (§7.3: nothing computable separates a reimplementation
> from a rewrite) and is therefore recorded as an explicit claim with a rationale,
> attributed and visible as authored.

**The evaluator is not an argument either**, though an earlier revision made it one.
A caller-supplied evaluator is a caller-supplied `equivalence_rule` reached through a
different door: §7.2 and R8 exist to stop a rule being chosen after the outputs are
seen, and passing the evaluator in at verification time is exactly choosing it after
the outputs are seen. The rule is already frozen in the spec the original run was
projected from (§4.2a), so resolving it there is both available and the only
defensible source. Mixed shapes refuse because there is no honest answer: one side's
rule is authored and the other's is fixed.

The asymmetry is deliberate and is the design's usual line: what can be derived is
derived, what cannot be derived is authored **and labelled as such**. One authored
input that announces itself beats a report full of facts that look observed. §11.7
already carries that limitation; nothing else in the report may join it.

**A constructor governs writes through Science, and that is not the whole world.**
Substrate §4.2's capability boundary is complete over code that goes through `nodes`
— but it says so explicitly of raw filesystem writes that a bypassing write "is an
untrusted import **by definition**", and that such a write producing a *valid* node
"passes both" the stale-hash rejection and the corpus check, because the writer
computed the hash to agree with the fields it wrote. A hand-authored verification
file with a fabricated report, a chosen scope and verdict, and a self-consistent
address is exactly that case. Making derivation a property of the **constructor
only** would leave the entire guarantee resting on the assumption that the file was
written by the constructor — which is the assumption substrate §4.2 refuses to make
anywhere else.

> **Rule.** Derivation is validated by a **world-level predicate** that runs at two
> **explicit** moments and at no other:
>
> - **On explicit import** — an operation Science performs to bring a record into a
>   corpus. Validation happens **before the write**: if the derivation inputs
>   resolve, report, scope, verdict and address are recomputed from them plus the
>   embedded authored certification, and a mismatch **refuses the import** — the file
>   is never written, so nothing ever depended on it. If the inputs do not resolve,
>   the import proceeds and **emits an import finding** saying so.
> - **On audit** — an explicit operation a person or an agent invokes over records
>   already in the world. It recomputes whatever now resolves and **emits an audit
>   finding**; where a recomputation contradicts a stored verification, the finding
>   says so and the audit **mints nothing** (amended 2026-08-03, 5b §7.6: the
>   constructor requires an explicit cut and epoch the audit context need not have).
>   *(and 2026-08-11, the act-report design §4: the finding is recorded as an entry in
>   the boundary wrapper's inert act-report — the evaluator still mints nothing
>   epistemic)* The **superseding `verification`** carrying the correct derivation is
>   a separate, explicit constructor act naming its own selections, through the
>   ordinary lifecycle (kernel §3.3, §7.3b). The contradicted record is
>   superseded, not deleted, and the correction is an addressed, attributable
>   act — detection and correction, two acts.
>
> **Reading never validates and never changes admission**, and **no validation state
> is ever stored on the record.** Findings are the output; the verification is
> immutable and gains no `validated` field. The same applies to `analysis-spec`:
> §3.1a's contradiction is checked on freeze and on explicit import, and otherwise
> by audit.

**"On import" means the operation, not the discovery.** An earlier revision said
"on import" while also saying reading never validates, and those two are only
consistent if `import` names something an actor invokes. It does — and the case that
forces the distinction is the very one this section is about. A file written straight
into a corpus directory by `cp` **never crosses an import boundary at all**. If corpus
discovery counted as import, every reload would validate, which is the read-path rule
this section rejected last revision for contradicting R5. If it does not, then the
hand-written file R19 is aimed at is simply never checked at write time. The loader
cannot tell first discovery from the hundredth read, because telling them apart is a
history question and history is §9's.

So the honest split, stated rather than left to the reader:

> **Explicit Science imports validate before writing. Raw filesystem additions are
> undetectable until an audit runs.** Validation is a property of operations Science
> performs, not of files appearing in a directory.

That is narrower than "on import" sounded, and it is the same narrowing this section
has now made three times: the guard belongs to acts, not to states. It also settles
where "unvalidated" lives — **nowhere**. Marking a record unvalidated means writing to
it, and a verification is immutable (kernel §3.3); a mutable status field on an
immutable record would be a second source of truth about a node whose whole point is
that its content is its identity. The import and audit operations emit **findings**
instead, which are ordinary content-addressed run artifacts (kernel §4.3) and carry
no authority over the record they describe.

**Why world-level and not corpus-level.** An earlier revision called this a "corpus
invariant" and, in §14, "kind-level recomputation" — two names for a scope that is
neither. The predicate traverses verification → two runs → spec and results, and
world §4.2 puts all of those in **world identity**, so under one world they routinely
sit in different corpora. Run corpus-locally it would fail exactly the way world §5
says a corpus-local `dangling()` and a corpus-local closure fail: every cross-corpus
reference reads as broken, and the check would refuse valid verifications for being
distributed. It composes over the **world resolver**, like the lineage closure world
§5 already relocates for the same reason. That is the third time in this document a
rule has been written at the wrong scope, and the tell is the same each time: the
rule names entities whose identity is world-level. The fourth turned out to be in the
substrate — its §3 closure primitive, specified in `nodes` for two callers that both
turned out to live up here (§14).

**Why validation is bound to explicit acts, and R5 is what forces it.** Two earlier
revisions each got this wrong in opposite directions, and the second was harder to
see because it looked like the fix for the first.

The first said recomputation happens on import **and on every read**. Against R5 that
is a contradiction: a verification with a declared numeric tolerance is recorded
`passed`, its output arrays later become unreachable in this checkout while remaining
held elsewhere, and §7.2 correctly returns **`inconclusive`** for an evaluator that
cannot read its artifacts. A mandatory recompute must then either reject a
verification that was and remains sound — admission moving on what is mounted, which
R5 forbids — or quietly trust the stored report, which R19 forbids.

The second narrowed it to "recompute wherever the inputs resolve", which fixes
available → unavailable and **reintroduces the same defect in the other direction**.
A forged `passed` verification whose artifacts are absent stands recorded and admits;
mount the artifacts and the predicate fires, refuses it, and admission disappears. No
record changed. A directory got mounted. That is R5's exact prohibition with the
arrow reversed, and the reason the first fix did not catch it is that R19's negative
tested only the transition I had in mind — genuine, available → unavailable — and
never the forged, unavailable → available one. **A symmetric guarantee needs both
transitions tested, and the untested direction is the one the fix will break.**

Binding validation to **explicit import** and **audit** removes availability from the
causal path entirely. An explicit import is an act with a result: a mismatch means
the file is never written, so nothing ever depended on it. An audit is an act someone
performs: a mismatch mints a **superseding verification**, and admission changes
because a node was recorded — attributable, addressed, and visible in history — not
because a filesystem changed shape. Mounting a volume is not an epistemic event and
must not behave like one. This also reuses the correction machinery §7.3b already
established for a withdrawn code-lineage certification, rather than inventing a second
way to revise a verification.

The price is that a record which never crossed an import — a raw `cp` into a corpus
directory — gets no write-time check at all, and is caught only when an audit reaches
it. That is worse than the previous revision *sounded* and identical to what it
actually delivered, since a loader with no history cannot tell a first discovery from
a reread anyway. Saying so is the difference.

There is still no way to distinguish "recorded by the constructor" from "hand-written
to look like it" without a record of what preceded the current state, and that is
§9's mutation log, which does not exist yet. So the guarantee is stated at the
strength it actually has:

> **Bound.** Recomputation is **tamper detection at import and under audit, and
> nothing in between.** A self-consistent verification that has not been audited, or
> whose inputs do not resolve, is **not refused and not certified as sound** — it
> stands as recorded, covered by the **recorded-history completeness** limitation
> (substrate §4.3, kernel §8.7, §9 here). The constructor is **hygiene, not tamper
> evidence.**

**Unresolvable is not a verdict, and it is not non-admission either.** A previous
revision said an unrecomputable verification "admits nothing while in it", which
turns a fact about this checkout into an epistemic result — the identical defect R5's
negative (b) was added to pin, committed one section away from the guarantee that
pins it. If the derivation inputs cannot be resolved, belief that depends on this
verification is **not computable here**; it is not a belief that happens to have
changed, and admission does not silently drop. Corpus-gone and bytes-unreachable are
distinct cases and R5 already separates them; this section must not re-merge them.

What is genuinely gained is narrower than the previous revision claimed and still
worth having: in the ordinary case — the runs and their outputs are here, which is
the case for any verification produced by work done in this world — a forged
verification is no longer independent work. It requires forging the **runs**
underneath it, and a raw-written run whose internal hashes agree is still undetected
(substrate §4.3). Above that floor, nothing here is tamper evidence.

R19 tests **both transitions**, in both directions: a genuine verification going
available → unavailable must keep admitting, and a forged one going unavailable →
available must not lose admission until an **audit** records the superseding
verification that takes it away.

### 7.4 `t078` and `t080`, closed

`t080`'s belief ceiling is rejected by kernel §3 and nothing here revives it.
`t078`'s four tokens survive as a derived reading of `(scope, verdict)`:

| `t078` token | derivation |
|---|---|
| `unverified` | no verification node exists |
| `self-consistent` | `(same-environment, passed)` |
| `independently-reproduced` | `(clean-environment, passed)` or `(independent-implementation, passed)` |
| `failed` | any active `(·, failed)` |

Its open tolerance question is answered by §7.2; its seeded-subsample question by
demotion to a machinery smoke test that confers nothing (kernel §3.1). What this
design adds that `t078` lacked is the second run: a rerun is not a flag on the
original, it is a run with its own closure, and the comparison is a node.

## 8. Cross-corpus provenance, and world §10 Q3

World §10 left open whether `run` and `assessment` need world identity, and said
it "turns on the collaboration model and should be settled there." That dependency
is wrong, and the audit shows why: **the kernel forces both, without
collaboration.**

- `verification` is a world kind that references **two runs**. If runs were
  project-scoped, a verification could not name what it replayed once the two runs
  live in different corpora — and that is exactly the `independent-implementation`
  case the kernel defines.
- `verification ──verifies──▶ assessment` puts assessments in the world by the
  same argument.
- G3's belief digest names `observes` dataset content identities, which already
  cross corpora.

> **Ruling: both `run` and `assessment` are world kinds.** Collaboration makes the
> need visible sooner; it is not the deciding dependency. World §10 Q3 is closed.

Two consequences:

**Run addresses are globally unique without coordination**, because they are
derived from the closure (§4.1). No registry allocates them and no project owns a
namespace.

**Lineage closure runs at the world layer**, as world §5 already requires. A run's
`observes` inputs may be datasets in other corpora, and substrate §5's independence
certification walks `derived_from` from exactly those roots. Run corpus-locally it
would emit `lineage-incomplete` for every cross-corpus ancestor — conservative,
and wrong.

## 9. The `atoms` boundary

`atoms` completed A7 on 2026-08-14: durable transaction records, coherent
capture, and effect/recovery execution now exist. A8's persistence-cut exerciser
and durability certification landed 2026-08-17, admitting one exact production
tuple. This design is written so that **nothing in it waits on composition-root
adoption**, and so that what changes there is stated rather than assumed.

**Content addressing is not durability.** A hash-named artifact in an ordinary
directory is content addressing, available today, and it is what specs, datasets,
runs and outputs need. `atoms` is required for atomic multi-file commit and for
tamper evidence — different capabilities, and keeping them apart is what stops
this design stalling on composition-root adoption.

**What this design builds:** content identity for specs, datasets, runs and outputs
(`science.identity.v1`, §4.3); the execution boundary and its receipts; the code
bundle and held-environment capture; the equivalence evaluator; the Snakemake
execution-trace adapter (§6.4).

**No new artifact store is built.** Every guarantee above needs exactly
`{content identity, locator, hash-verifying resolver}`, and the repository already
has that shape: `commons/resolver.py` maps `(dataset id, logical path)` to a
filesystem path through a lookup chain with per-machine overrides, and **verifies
the sha256 against the datapackage hash on every call**. A dedicated
content-addressable store is warranted only when placement, deduplication or
retrieval measurements demand it — and no such measurement exists. Building one now
would repeat the pattern this redesign exists to end: machinery sized for a
projected ceiling rather than an observed one.

**What it deliberately does not build:** an append-only registry of execution
attempts. The temptation is specific and worth naming — such a registry would
upgrade kernel G4 from *recorded* attempts to *all* attempts, and would give §3.3
the pre-run ordering it cannot otherwise have. Building it here would produce
something that looks like tamper evidence without being it, because kernel §8.7's
contract is **stricter than crash recovery**: it requires pre-mutation durable
registration **and** detectable journal removal. A journal that can itself be
deleted closes nothing.

**The interface, stated so a later design inherits a contract rather than "use the
journal" — and stated at the right size.** An earlier revision named
`register_run_intent(spec identity, run intent, timestamp)` and claimed it closed
all of §8.7's consequences (then four, now five). **It does not.** Registering an
intent before execution can close §3.3's run chronology, and nothing about it can
detect the deletion of a verification node, a retraction record, or a coordinated
proposition fields-plus-hash edit — those are mutations of records that a
run-scoped registry never sees.

> **The shared facility is a general tamper-evident mutation log**: every mutation
> durably registered **before** it is applied, in a sequence whose **removal is
> detectable**. Registering run intent is *this design's consumer* of that facility,
> not the facility.

| consequence | what the log must witness |
|---|---|
| kernel **G4** — discarded failed replay | the attempt, registered before execution |
| kernel **G8** — deleted failing verification | the deletion, as a mutation |
| **semantic identity** — coordinated fields-plus-hash edit | the prior state, before the write |
| **§3.3** — spec-predates-run | the spec freeze and the run intent, in order |

One capability, four consumers. Sizing it as a run registry would have closed one
consequence and left the design believing it had closed four — which is the shape
of error this document has now made twice, and the reason it is written out here
rather than inferred later.

**Amendment (2026-08-03) — the first design question is anchor placement, not the
registration API.** Removal-detectability cannot come from where the log naturally
wants to live. `atoms`' transaction metadata is host-local and sync-ignored by
design, so it does not travel with a corpus that moves by copy or sync; a
per-corpus log file travels *with* the corpus — deletable alongside everything it
witnesses. Detecting removal requires an anchor **outside the deletable set**. The
world index is the natural carrier: world §5 already requires it to be publishable
and consumable without the corpora it names, so publishing each corpus's log
sequence head into it makes a truncated or removed log detectable at exactly the
boundaries that already recompute — import and audit. Whichever design takes §9 on
should begin there — where the anchor lives, and how staleness between anchor and
log is classified — before any registration API.

**Taken on 2026-08-03** (`2026-08-03-tamper-evident-log-design.md`): per-root
hash chains at a reserved in-corpus path, epoch-cadence anchoring through the
world index plus an explicit anchor act, and the surviving-observer bound stated
rather than papered over. `register_run_intent` is **superseded** by that
design's intent entry, correlated to its fulfilling run publication by the
boundary-minted `event_token` (§4.2 here) — the boundary appends the intent
durably before execution and constructs the fulfillment linkage itself, so no
caller-supplied correlation exists. The four recorded-mutation consequences
close at implementation; §3.3's chronology strengthens for boundary-mediated
executions only.

## 10. Guarantees, and how each is tested

Certified by mutation, per the kernel's §5 discipline: break what the guard guards
and watch it fail.

| # | Guarantee | Mutation test |
|---|---|---|
| **R1** | An incomplete closure is refused as a run | Omit `environment_identity`; assert refusal and that **no** `run` node is minted. Author the note or source-assertion as a **separate explicit act** (mirroring world W3), then supply the member and assert the run is minted from it. **Negative (a):** assert no `unknown`- or `attested`-valued component can be persisted on a run in any position. **Negative (b):** supply a bare **lockfile digest** as `environment_identity` and assert refusal — a recipe for an environment is not held environment content (§4.5) |
| **R2** | A run's address moves when any closure member changes, and the recipe holds nothing post-execution | Mutate **each** member of §4.2 in turn — every recipe member including `invocation`, each input partition, the result's `outputs`, and each occurrence member — and assert the address changes every time. **Negative:** execute one recipe twice and assert the two **recipe identities are equal** despite differing traces, job ids and realized seeds — pinning that no post-execution observation reaches the recipe, which is what keeps `clean-environment` reachable |
| **R3** | Two executions of one recipe are two runs | Execute the same recipe twice; assert **equal recipe identity, distinct addresses**, and that a verification can reference both. **Negative (a):** assert the two do **not** collapse to one node. **Negative (b):** force `started_at`, `actor` and `host_realization` to be identical across the two and assert the addresses are **still** distinct — pinning that the minted `event_token`, not the timestamp triple, is what separates them |
| **R4** | Verification scope is derived, and rests on evidence rather than difference | Attempt to author a `scope`; assert refusal. Walk every row of §7.3 including `not-certified`. **Negative (a):** change only the **hostname** between two runs of one recipe and assert the scope stays `same-environment` — no receipt, no `clean-environment`, so a machine name cannot buy admission. **Negative (b):** change only a **comment** in the code and assert `not-certified`, never `independent-implementation`. **Negative (c):** two runs sharing a proposition target but with **different `spec_identity`** assert `not-certified`. **Negative (d):** replay under a `boundary_policy` **missing a required capability** (§7.3a) and assert `same-environment`, never `clean-environment`; assert a policy providing every capability qualifies **whatever its version string**, and that two incomparable policies are not ranked |
| **R5** | Belief does not depend on **artifact availability in this checkout** | Make the artifact bytes unreachable here **while a controlled copy remains held**; assert `belief_input_digest` **unchanged**, admission **unchanged**, replay eligibility *not available* — never `unverified`, never `failed`. **Negative (a) — holding, not reach:** destroy the **last held copy** of an `observes` input and assert the input is no longer held, eligibility fails, and admission **changes**. **Negative (b) — computability, not belief:** remove the **corpus holding the records** and assert **`not-available`**, not an unchanged belief, which would be a recomputation from absent inputs |
| **R6** | Replay eligibility is not a verdict | Make a run un-replayable here; assert **no** verification node is created and **no** assessment state changes. Restore availability and assert the state is likewise unchanged until a replay actually runs |
| **R7** | The two run shapes are structurally exclusive | Give a `dataset-production` run an `assesses` descendant; assert refusal. Give an `assessment` run a spec with no `target`; assert refusal. Assert an `assessment` run with zero `observes` inputs admits nothing, at any quantity of `reads` |
| **R8** | The equivalence rule cannot be chosen after the outputs are seen | Run, observe a failing replay, edit the rule; assert a **new spec identity** is minted, that the original run's closure still names the **old** spec, that the successor references the superseded one, and that the failing verification **remains active** |
| **R9** | `inconclusive` never collapses into `passed` or `failed` | Make an output unreadable; assert `inconclusive`, and assert admission does **not** follow. Assert the same for a missing output and a reader error |
| **R10** | Runs begin at the most upstream held form | Attempt a run whose input is a URL or an accession rather than a held dataset; assert refusal and that the acquisition path records dataset provenance instead. **Negative:** assert no fallback synthesizes a dataset entity from the URL |
| **R11** | A dataset-production replay is bitwise, and forking identity does not cancel the verdict | Attempt to declare a tolerance on a `dataset-production` replay; assert refusal. Replay a nondeterministic transform and assert **all four**: a **different dataset entity** is minted; a **`failed`** dataset-production verification is recorded under `dataset-content-equality/v1`; the prior dataset's assessments stay bound to the prior dataset; and **no belief moves**. **Negative:** assert the dataset-production verification carries **no** `verifies → assessment` edge and gates nothing |
| **R12** | Spec-predates-run is bounded, and the bound is pinned | Assert the execution boundary refuses a run naming no frozen spec identity. **Then assert the negative:** freeze a spec *after* an out-of-band execution, attach it, and confirm the system **cannot** detect the ordering — pinning §3.3 so no reader takes content addressing for proof of pre-registration. With the §8.7 log implemented (`2026-08-03-tamper-evident-log-design.md`), the **boundary-mediated** arm strengthens — a boundary-started run's intent entry is a removal-detectable witness — while this out-of-band negative stands unchanged (its limitation 5) *(Amended 2026-08-11, the act-report design §3: cooperative no-run closure now exists — a post-intent attempt that minted no run may close through a qualifying act-report — and the formal claim is unchanged: the out-of-band negative stands, and an unmatched intent still proves exactly an attempt with no qualifying recorded outcome.)* |
| **R13** | `code_identity` captures what actually ran, not what was committed | Modify an **untracked** file inside `code_roots` and assert `code_identity` changes. Modify a tracked-but-uncommitted file and assert the same. **Negative:** attempt a run whose local import resolves **outside** the bundle and the held environment; assert refusal, not a silently absent member. This tests the capture, which mutating a stored digest does not |
| **R14** | Identity canonicalization is **injective** and domain-separated (§4.3) | Assert a binary float is **refused** in every position, including nested, and that `0.1 + 0.2` cannot enter an identity. Then walk all **four** collisions of §4.3: **(i)** the decimal `0.5` and the string `"0.5"` produce **different** bytes; **(ii)** `{"x": null}` is **refused**, and does not encode as `{}`; **(iii)** the integer `1` and the decimal `1.0` produce **different** bytes, and `1.00` and `1.0` produce the **same** bytes — a decimal always keeps a fractional digit and an integer never acquires one; **(iv)** two keys equal only after NFC normalization are **rejected**, not merged. Assert `NaN`, `Infinity` and `-Infinity` are **refused in every position**, not encoded, substituted or coerced. Assert two **different kinds** with byte-identical payloads produce different digests. **Negative:** assert a `v2` domain digest never equals its `v1` counterpart for the same payload |
| **R15** | Execution is confined to the closure it declared (§4.4b) | Capture the bundle, then **edit a bundled file before execution reads it**; assert the run fails rather than executing modified code under an unchanged `code_identity`. Attempt an **undeclared file read** and an **undeclared network fetch**; assert both fail closed. Assert the receipt names the capabilities actually in force. **Negative:** run under a policy providing fewer capabilities and assert the run is still valid but **cannot reach `clean-environment`** — confinement is graded, not pretended |
| **R16** | Non-conformance blocks scope, not just reporting (§4.2, §7.3, §6.2) | Execute two runs with equal recipes, qualifying receipts and **equivalent outputs**, but force one execution's **realized seeds to violate its seed plan**; assert the derived scope is **`not-certified`** and that **nothing is admitted**. Repeat with a job that is **not in the engine-derived trace** for the requested targets, and with a **requested target left unsatisfied** — the two things single-run job-set conformance actually asserts (§6.2). **Negative — no phantom enumeration:** assert a data-dependent replay that legitimately runs a **different job set** over different held inputs is **conforming**, that the difference appears in the **comparison report as a diagnostic**, and that it contributes to **no verdict and no scope**. Assert **no equivalence rule can read an occurrence** — the evaluator's signature is `(result, result)` (§7.2) and admits no job-set argument. **Multi-stream:** run a job whose **family declares two streams**, assert both seeds are recorded under `[job_key][stream_key]`, then omit one and assert **`not-certified`** — not a pass on the strength of the job key being present. Repeat with a realized stream that family does **not** declare. **Per-family:** run a workflow where family A declares `model-initialization` and family B declares `resample-draws`; assert the honest record `{A: [model-initialization], B: [resample-draws]}` **conforms**, and that a record claiming every stream for every job does **not** — pinning that conformance is evaluated against each job's own family and cannot be satisfied by over-claiming. Assert a wildcard instance is judged against its family's declaration. Assert the family declarations are read from the **workflow-definition snapshot**, not the spec, and that the boundary enforces **set equality against `recipe.seed_plan.logical_streams`** in both directions: a family stream with no matching logical stream is refused, **and** a declared logical stream that **no family claims** is refused. Assert this holds for a **`dataset-production`** run, which has no spec — pinning that the rule reads the recipe rather than a member that shape does not carry. **Execution coverage, not just definition coverage:** build a workflow that satisfies the definition equality but whose `resample-draws` family produces **zero jobs** — filtered out, or off the path to the requested target — and assert the run is **non-conforming** and the derived scope is **`not-certified`**, even though every executed job matched its own family vacuously. Assert the conformance result for **both** runs appears in the comparison report, and therefore in the verification's identity |
| **R17** | An assessment recipe cannot disagree with its spec, and its seeds are pre-declared (§3.1, §3.1a, §4.2a) | Attempt to supply `inputs`, `parameters`, or the `nondeterminism_contract` **or any part of its payload, root seeds included**, directly on an `assessment` run; assert **no such path exists** — the boundary projects all three from the frozen spec. **Then attempt the same values through `invocation`** (§4.2b): assert an engine option carrying a parameter value — `--config alpha=0.5` against a projected `alpha = 0.05` — **cannot be spelled**, that `invocation` holds bindings rather than values, and that the boundary **renders** the engine's configuration from the projected members. Pin that "no caller-supplied path" is a claim about **every** path, and that a free-form option list is one. Assert a spec declaring `dataset:A` and `alpha = 0.05` cannot produce a run over `dataset:B` at `alpha = 0.5` in any way, including through a replay. **Negative (a) — seed shopping:** attempt to execute one frozen spec under **several caller-supplied root seeds** and assert those executions **cannot occur at all** — the boundary refuses them rather than running them and overwriting the seed afterwards. Assert that changing a root requires a **successor spec** with its own identity, and that runs **recorded** under the original stay attached to it. **Then assert the limit:** an attempt that was deleted, or never recorded, is **undetectable** — this is kernel G4 and §9's mutation log, and R17 must not be read as promising more history than G4 provides. **Negative (b):** assert a `dataset-production` recipe **is** authored directly, seed plan included, since it has no spec to project from |
| **R18** | Scope evidence is embedded and identity-bearing (§7.3b) | Build two verifications over the **same pair of runs** relying on **different** code-lineage certifications; assert **two distinct verification addresses**. Assert the comparison report carries the certification claim, both conformance results, the relied-on receipt identities, and — since 2026-08-03 (5b §6) — the exact `(rule identity, implementation content identity)` binding each executed rule ran under, all **inline**, and that the verification basis names the **report** rather than that evidence a second time — one digest over the evidence, not two. **Negative:** delete the external certification record and assert the verification is **unchanged and still valid** — pinning that the promised dangling edge does not exist, and that withdrawal is handled by a **superseding verification** rather than by silent revaluation *(Amended 2026-08-11, the act-report design §4: a report-position citation embeds on this same discipline — resolved content inline, **(act-report ref, entry index)** as provenance — and deleting the cited report leaves the verification unchanged and still valid, T6's R18 arm.)* |
| **R19** | Verification derivation is validated at explicit import and under audit, and neither mounting nor a raw write is an epistemic event (§7.3c) | Assert the constructor's arguments are **ordered run refs, an optional certification, and the explicitly selected contract identity and epoch (5b §7.6), and nothing else**: attempt to pass a comparison report, a conformance result, a boundary receipt, an **equivalence-rule evaluator**, or an **implementation selection** and assert no such parameter exists. Assert the evaluator's **identity** is resolved from the **original run's frozen spec** and its **implementation** from the run's frozen `rule_bindings` (5b §6), and that a **mixed-shape** pair is refused. **Explicit import, inputs resolvable:** hand a `verification` with a fabricated report, a chosen `scope` and `verdict`, and an address computed to agree with them to the **import operation** — the untrusted-import case substrate §4.2 says passes stale-hash and corpus checks — and assert the import is **refused before any write**, and that no file exists afterwards. Assert an import whose inputs do **not** resolve **proceeds** and emits an **import finding**, and that **no validation state is written onto the verification** in either case — the record is immutable and gains no `validated` field. Assert the recomputation resolves **across corpora** through the world resolver, and that a verification whose runs live in a different corpus is **not** refused for that reason alone. Do the same for an `analysis-spec` whose `stochastic-unseeded` contract accompanies a bitwise `equivalence_rule`. **Both transitions, which is the point of this row:** **(a) genuine, available → unavailable** — record a `passed` verification under a declared **tolerance**, make its artifacts unreachable here while they remain **held elsewhere**, and assert it is **not refused**, admission is **unchanged**, and no `inconclusive` is recorded; **(b) forged, unavailable → available** — import a self-consistent forged verification whose artifacts do **not** resolve (so it enters unvalidated and admits), then **mount them**, and assert admission is **still unchanged** until an **audit** runs, that the audit emits the contradiction finding and **mints nothing** (amended 2026-08-03, 5b §7.6), that a separate explicit constructor act naming its own cut and epoch mints the **superseding verification** carrying the correct derivation, and that admission changes **because of that node**, never as a side effect of the mount or of the audit alone. Assert reading the record at any point in either transition validates nothing. **Negative (c) — availability is not an epistemic result:** assert an unvalidated verification is neither certified sound nor treated as non-admitting; where its inputs cannot be resolved anywhere in the world, assert belief is **not computable**, never a silently unchanged or lowered value. **Negative (d) — the import boundary is an operation, not a directory:** write the same forged verification straight into a corpus path with a raw filesystem call, bypassing the import operation entirely; assert it is **not** refused, that **reloading the corpus does not validate it** at any point, and that it is caught **only** when an audit runs — pinning that "validate on import" is a claim about Science's operations and never about files appearing on disk. **Negative (e):** assert a raw-written *run* whose internal hashes agree is **still** not detected, and that an unaudited self-consistent verification is **not** distinguishable from a genuine one — both are substrate §4.3's limitation and need §9's log; this test must not be read as closing either *(Amended 2026-08-11, the act-report design §4: the constructor's closed list gains one member — the optional report-position citation. Every other extra argument is still refused, deleting the cited report invalidates nothing, and the audit arm is unchanged: the evaluator mints nothing, its finding recorded as an entry in the boundary wrapper's inert act-report.)* |
| **R20** | The nondeterminism contract cannot contradict itself, and stream totality reaches both records (§3.1a, §6.2) | Attempt to freeze a spec that is `deterministic` **with** a seed plan, `stochastic-unseeded` **with** a seed plan, and `seeded` **without** one; assert each is **unspellable** — refused by the union, not by a validator. Attempt a `seeded` plan with multiple roots and **no total stream-to-root mapping**; assert refusal, since the derivation has no determined root argument. Assert `stochastic-unseeded` **is** freezable when it carries a rationale — an honest declaration is not an error. **Negative (a):** assert `stochastic-unseeded` alongside a **bitwise** `equivalence_rule` is caught at **freeze time** *and* on **import** (§7.3c), and assert this one is a **check** rather than a type refusal, since it spans two fields. **Negative (b) — totality reaches the occurrence:** declare two streams over two roots, then attempt to record realized seeds keyed by **job alone**; assert the occurrence **cannot represent it** and the run is refused, pinning that a plan naming two roots is not satisfiable by a record with one slot. **Negative (c) — the *obligation* is per family, though the *declaration* is global:** assert the spec **does** hold one global set of logical streams — that is correct and required for the equality check — while **no global per-job obligation is spellable**, so an honest record in which different families realize different streams **conforms**. Pin that no conformance rule here is satisfiable only by a job claiming streams it did not use. **Negative (d) — no topology in the spec:** assert the frozen spec names **logical streams only**, that **no workflow rule or process name can be spelled in it**, and that stream identities name **analytical roles** (`model-initialization`, `resample-draws`) rather than **libraries** — assert a spec built around `numpy-rng` and `torch-rng` fails review for the same reason a rule name would, since a reimplementation in another framework draws the same analytical randomness elsewhere. Then build two implementations of one spec with **different rule decompositions**, and assert both carry the **same `spec_identity`** and can be compared under `independent-implementation` — pinning that a family-named field in the spec would have made that scope row unreachable for every seeded spec |
| **R21** | A recipe says what to execute, and says it portably (§4.2b, §4.2c) | Take one workflow definition with two targets, `analysis` and `report`, and execute each; assert the two runs have **different recipe identities** — pinning that a shared bundle, environment, definition snapshot, inputs, parameters and contract do **not** make them executions of one recipe, and that §7.3 cannot read them as such. Assert a replay boundary given only the recipe **can invoke it**: the entrypoint, the targets and the bindings are all present, the boundary **renders** the engine's configuration from `inputs`, `parameters` and the seed plan, and no caller supplies any of it. **Result manifest (§4.2d):** assert the manifest is **constructed by the boundary** by content-addressing every declared final output, and that there is **no supplied-manifest path**; then assert each of a **missing** declared output, a **duplicate** logical name, an **undeclared** entry, and a digest disagreeing with the bytes on disk mints **no run at all** — not a run marked non-conforming. Assert **intermediates beneath the output root are excluded**, and that a replay leaving different scratch files therefore produces an **equal manifest**. **Negative (a):** vary a scheduling-only option (`-j 8` → `-j 2`) and assert the recipe identity is **unchanged** — the member records what runs, not how fast. **Negative (b) — outputs cannot grant their own authority (§4.2c):** attempt to declare an **absolute** output path, and a boundary-relative one containing traversal that escapes the output root; assert both are **refused**, so a caller cannot place a host location inside the confinement allowlist by naming it. Attempt a write outside the boundary-owned output root and assert it fails closed. **Negative (c) — the host mapping is not identity:** execute one recipe on two hosts whose output roots mount at **different absolute paths**; assert the **recipe identities are equal** and `clean-environment` stays reachable, and that each host's mapping appears only in its **receipt**. **Negative (d) — targets are not a job set:** assert `invocation` does **not** claim to enumerate the jobs a target implies, and that R16's single-run job-set conformance asserts only target satisfaction and trace membership (§6.2). **Negative (e) — the two failure states are distinct:** assert a **complete** closure whose realized seeds violate the plan **does** mint a run and is **non-conforming**, pinning that refusal is for closures that cannot be completed and non-conformance for executions that disobeyed a complete one. |
| **R22** | The assessment facet is derived from the run through the ordinary API (§3.1b, §5.1, kernel §4.2.1) | Assert the assessment constructor takes **only a run ref** — attempt to pass `outcome`, `estimate`, `uncertainty`, `estimand`, `applicability` or `interpretation_rule` and assert **no such parameter exists**. Run an analysis whose result the frozen `interpretation_rule` maps to **`refuted`**, and assert no API path produces an assessment carrying `supported`; assert the derived `outcome` changes only when the **result** or the **rule** changes. Assert `estimand` and `applicability` are **copied by the constructor** from the frozen spec, and that `proposition` comes from the spec's `target`. **Evaluator failure (§3.1b):** make the rule's evaluator fail — unreadable output, unparseable payload, missing rule implementation — and assert **no assessment is produced** and a finding is recorded; assert `inconclusive` is **not** produced, since it is a scientific outcome and machinery failure is not one. **Negative (a):** assert narrowing `applicability` after seeing the result requires a **successor spec and a new run**. **Negative (b) — no revisions, but the values are still hashed:** assert there is **no edit** that changes a facet and leaves the same assessment, and that the world basis `(spec, run, proposition)` is the constructor's own argument set. Then assert **G3 digests keyed facets** — sorted `(assessment identity, facet digest)` pairs — with **both** halves tested, since two consecutive revisions each dropped one: raw-write an assessment at the correct address carrying `supported` where the derivation yields `refuted` and assert the **belief digest differs** from the correct state's (which hashing identities alone would have missed); then **exchange the facets of two assessments** on one proposition, over different runs and different lineages, and assert the belief digest **differs** (which hashing a bag of facet digests alone would have missed, the multiset being unchanged). Assert the second state can aggregate to a different belief, so the digest is not merely being pedantic. Assert this is **change detection, not truth detection**. **Reach:** execute one recipe, then execute a second differing **only** by an inline exclusion certification (§5.2), so the two assessments carry **byte-identical facet values**; assert the belief digest differs. Assert that editing the certification alone changes **no** belief digest, because it mints a recipe and no run. **Rule binding (§3.1b):** assert a spec naming an `interpretation_rule` that resolves to neither a held implementation nor a registry entry with fixtures is **refused**, and that an implementation failing its fixtures **is not that rule**. **Negative (c) — the API is not the world:** hand-write an assessment file with a fabricated facet straight into a corpus path; assert it is **not** refused and **not** detected on read, that **explicit import** recomputes the facet from the run and **refuses** a mismatch, and that a raw-written one is caught **only under audit** — the §7.3c limitation, unchanged, and read-time validation would violate R5 |
| **R23** | A produced dataset, its ancestry and its durable basis are minted by the boundary (§5.2) | Assert the output dataset's address is the **dataset basis projection over the output manifest's content identities** — deduplicated, sorted, digested (admission ramp §6.2; *amended 2026-08-09, this read "the single output entry's content identity", which a uniform projection cannot return for a one-entry manifest without a cardinality special case inside an identity function*) — and that the run's **`produces`** edge is emitted with the run; attempt to attach `produces` naming a dataset the manifest did **not** emit, and assert the ordinary API offers no such path. Assert **no `produced_by` edge exists in either direction of the API** — the retired representation must not be reachable. **Negative (a) — no nominal handle in identity:** emit byte-identical output under two different **logical names** and assert **one** dataset address results — pinning that the address is not the manifest digest, which carries the name. Assert `derived_from` **resolves as a view** over `produces ∘ transforms`, is **not stored**, and is **not read by independence** — which walks the stamped basis — and that no authored ancestry list is accepted. **Negative (b) — the independence multiplier:** construct two runs sharing an upstream dataset and omit it from one's ancestry in a build that permits authoring; assert the omission **would** make the two assessments read as independent under kernel §4.2.1's disjoint-closure rule, then assert the derived form makes it unspellable. **Negative (c) — omission survives derivation:** classify a shared **empirical** input as auxiliary `reads` **without certification**; assert the closure is **incomplete** and independence is **`not-certified`**, never assumed — pinning that deriving the edge did not make the classification honest. Assert a **certified** exclusion does remove the input from the closure, that the certification is **inline on the `reads` entry** with a rationale and attribution, and that adding or withdrawing it **mints a different recipe** — then assert it mints **no run**, and that the original run is unchanged, until that recipe is **executed**. **Then assert both limits:** a *false* certification still omits the edge and still inflates belief — the guarantee is attribution, not truth; and after a corrected re-execution, assert the **original run and its false certification are still active belief inputs**, with no API path that retires either, pinning §11.13 rather than letting attribution be read as correction. **Replay cardinality:** replay a `dataset-production` run successfully and assert **one dataset address with two `produces` edges from two runs**; assert the lineage view composes over both, and that **no existing dataset node was mutated** to record either — including that the pre-existing dataset's **lineage basis is unchanged** and still names the first run. **Deletion, which the view alone cannot see:** stamp the basis, then **delete the producing run**; assert the dataset does **not** read as a root, that the unresolved basis entry emits **`lineage-incomplete`**, that independence over it is **`not-certified`**, and that kernel §5.1's belief digest **moves** — asserting the stored ref and its `null` resolution are recorded **separately**, since recording either alone loses the deletion. Assert the same for a deleted **ancestor**. Assert a *second* surviving run producing the same address by another route does **not** repair the first basis. **Negative (e) — divergence, not union and not silence:** have `R1` mint `D` from `A`, stamping the basis, then have `R2` produce byte-identical `D` from `B`. Assert independence over `D` becomes **`not-certified`** with a **`lineage-divergent`** finding — not silently unioned into ancestry, which the single basis cannot make durable, and not silently ignored, which would certify `D` independent of `B`-derived evidence while a derivation from `B` demonstrably exists. Assert kernel §5.1's belief digest **moves** when `R2` is added, pinning that the snapshot covers the **producer set** and not only the basis. **Coverage (§11.15):** enumerate producers from a **producer snapshot** whose coverage omits `R2`'s corpus and assert the digest **differs** from the full-coverage one even though every *present* corpus is identical; then make `R2`'s corpus absent **within** coverage and assert `not-present` rather than a silent undiverged reading. **Negative — location is not evidence:** move a dataset between corpora and edit an alias, and assert the belief digest is **unchanged** (world W5) — pinning that the member is the snapshot and not the whole index. **Derivation, not just hashing:** delete `R2`'s entry from a valid snapshot, leave its coverage and receipt intact, and hand it to **explicit import**; assert it is **refused** because rebuilding from the receipt's corpus states does not reproduce the map, that a snapshot carrying **no receipt** is refused as unrecomputable and that a receipt naming corpora rather than **exact states**, or naming a bare version string rather than a fixture-bound rule identity, evaluates to **`malformed`** — refused at import, and returned as `malformed` rather than `unresolvable` by an **audit** that meets one raw-written, since no arriving corpus or rule could ever make it checkable (world §5, W8a). Assert a snapshot whose receipts are **all malformed** is **`unchecked`**, never `contradicted`, with a malformed finding per pair. Assert a fabricated snapshot written straight into place is caught **only under audit** — never on read, which would violate R5. Assert the third case is **not** a refusal: a receipt naming exact states whose **corpora are absent here** imports with a **finding**, writes no validation state, and is checked by a later audit (world §5) — "cannot be checked here" is `not-present`, not `unknown`. Assert a receipt whose covered corpus has **moved to a new state** is likewise **unresolvable** rather than refuted, so a snapshot's completeness evidence is checkable only while the receipt is **`resolvable`** — **each** covered corpus at its own recorded state (world §5, limitation 10). **Two corpora:** make one of two covered corpora move while the other stands still, and assert the receipt is **unresolvable** — one corpus cannot satisfy the other's entry. **The rule is a receipt member too:** mutate the receipt's `producer_snapshot_rule_identity` and assert the **receipt identity moves** while the snapshot's semantic identity and the belief digest do **not**; then install a newer enumeration rule beside the old and assert the receipt **still validates**, stop holding the old rule and assert **`unresolvable`** rather than refuted, and assert a rule whose implementation fails its fixtures **is not that rule** (world W8a). **Negative — the receipt is not a belief input:** move a dataset between two covered corpora, so **both** corpus-state identities in the receipt change while the producers map does not; assert the belief digest is **unchanged**, pinning that exact states sit outside the semantic identity and that the completeness mechanism did not smuggle location back in. **Then assert the residue (§11.14):** delete `R2` and assert certification is **restored** and the resulting state is **indistinguishable** from one where `R2` never existed — no retained prior digest, since belief is a computed view; assert specifically that **no** test can distinguish them, rather than asserting a difference the design cannot deliver. **Merge and the tagged basis (world §4.3):** assert a boundary-minted basis is always **`single`**, and that the **only** transition to `conflict` is a merge of records whose routes differ. Merge two records at one content address with different routes; assert the survivor carries `conflict([both], sorted)`, that no field-selection path chooses between them and **no ordinary API removes a route**, that the dataset is `lineage-divergent` with independence `not-certified`, and — unlike the deletion case — that the conflict **survives** deleting either producing run. Assert merging two `conflict`s **unions** their routes. Assert the traversal over a `conflict` resolves **every** route's refs and certifies nothing, and that divergence is decided on the **tag** before any comparison — no `transforms`-versus-basis comparison is attempted against a set. **Valid state:** assert `conflict` with **fewer than two distinct routes is unconstructible**, so a conflict that never occurred cannot be spelled and there is one representation per fact. **Lifecycle:** assert **no** API resolves a conflict — none retires a route, chooses between two, or records one as wrong — so the state is permanent under this design (§11.13's missing correction lifecycle, reached from another direction). **Then assert two limits, which are not one limit:** a raw filesystem edit *can* drop a route or forge a `single`, and the API guarantee does not reach the filesystem (§11.11) — with `B`'s producing run still present, assert an **audit detects** the forged `single(A)`, since recomputation still has `B` to contradict it. **Then delete `B`'s producing run as well** and assert the audit reports **nothing**: every surviving route resolves and no record of `B` remains. Assert specifically that **no test distinguishes** that corpus from one in which the conflict never arose, rather than asserting a detection the design cannot deliver — the composite of §11.11 and §11.14, where R23 previously claimed a route's removal was always caught while the row above it said no path removes one. **Negative (f) — the replay case is not divergent:** replay `R1`'s recipe; assert the second producer's `transforms` set **equals** the basis, that **no** divergence is reported, and that independence stays certified — pinning that the divergence rule does not fire on the case §5.3 is built to reach. **Negative (g) — self-edges:** run an identity transform that transforms and produces one content identity; assert the run is **valid**, that **no** `D derived_from D` edge appears in the view, that the closure is **not** reported as cyclic, and that the run is **not** divergent — then assert a genuine two-node cycle **is** reported. **Negative (h):** assert an input's role is fixed in the recipe before execution, so reclassifying it mints a **different recipe**, and a different run only on execution; and assert a raw-written lineage basis is caught only under audit, as in R22 |

R12's negative half follows the G4/G8/S3 pattern exactly: a guarantee whose limit is
untested will be read as the strong claim. **R17's second negative is the same
pattern caught in this document's own text** — an earlier phrasing promised that
discarded attempts stay "visible", which is precisely the history G4 says cannot be
guaranteed. A guarantee's limit does not stop applying because the sentence
restating it is friendlier. R2, R3, R4, R5, R13, R14, R15, R18 and R19 each carry a
negative for a sharper reason — every one of them pins a place where an **earlier
revision of this document was wrong**, so the test exists to stop the wrong version
returning. Most of the negatives in this table are scar tissue, and that is the
intended reading.

R14's four collisions and R18's negative are worth reading together: two of R14's
were **introduced by the fixes for the other two**, and R18 pins a mechanism that
was promised, argued for by analogy, and turned out to be unconstructible. Both are
the same lesson — a repair is a change, and a change needs its own test.

R19 is the third variant and the sharpest, because it was wrong three revisions
running, twice in one direction and once in the other. R4 refuses an authored `scope`
and was read as closing the question; it closes one field. §7.3c then refused a
supplied report and was read as closing it again; a **constructor** governs writes
that go through it, and substrate §4.2 says in as many words that a raw filesystem
write is an untrusted import that a valid-looking node passes. So the guard moved to
recomputation — and **overshot**, because "recompute on every read" cannot coexist
with R5: a tolerant verification whose outputs are unreachable here would be rejected
for a fact about this checkout. Narrowing that to "wherever the inputs resolve" then
broke the opposite transition, and "on import" turned out to name a boundary a raw
`cp` never crosses. The guarantee that finally holds is narrower than any of them:
**explicit imports validate before writing, audits validate on demand, and nothing
else validates at all.**

Its two transitions and three negatives carry the whole cost. **The transitions are
one lesson**: the revision that narrowed recomputation to "wherever the inputs
resolve" fixed available → unavailable and broke unavailable → available, because the
test I wrote covered only the direction I was already thinking about. A guarantee
about a state change needs **both** directions tested, and the untested one is where
the next fix will land. **Negative (d) is the other**: the following revision said
"validated on import" while a raw `cp` into a corpus directory crosses no import at
all, so the test has to be written against the bypass rather than against the API —
the same lesson as R19's own history, one layer further out. Then (c) pins that
unresolvable is a computability state and never an epistemic one, and (e) pins that an
unaudited self-consistent verification is **indistinguishable** from a genuine one.
The constructor is hygiene; §9's log is the only tamper evidence in this design, and
it does not exist yet.

**R22 and R23 are the fourth and fifth variants, and together they are one lesson
about repairs.** R22's member was wrong three times in a row — the key without the
value, then the value without the key, now the pair — and each revision fixed the
case the previous one had just broken, because each was written against the specific
forgery in front of it rather than against the member's contract. R23's is the same
shape one relation away: making lineage a **view** removed the last authored route to
ancestry and, in the same stroke, removed the stored record substrate §5's deletion
detection was reading. Both repairs were correct about what they were aimed at and
silently traded away a property nobody had restated. The generalization is the one
worth carrying into sub-problem 5: **a repair is a substitution, and a substitution
must be checked against everything the replaced thing was doing** — not only against
the defect that prompted it. Both rows now carry the *old* case and the *new* one as
separate assertions, so a future revision that trades one for the other fails a test
instead of passing review.

**R23's own repair then needed the same treatment, one revision later.** Stamping the
basis made *one* route durable while the rule above it still handed independence a
**union** over every producer — so the guarantee held for the route the basis named
and for no other, and a second producer's deletion still bought corroboration without
dangling anything. A durable record and a wider consumer is not a partial fix; it is
the same defect with a smaller domain. The rule that comes out of it is worth stating
in the same breath as the substitution one: **a durability guarantee must span exactly
what reads it** — narrow the consumer to what is durable, or make durable everything
the consumer reads, and say which of the two you did.

## 11. Limitations

1. **Spec-predates-run is not proved by content addressing** (§3.3). The fourth
   consequence of the one missing substrate capability, and the largest surviving
   gap between what this design says and what it can enforce.
2. **The world starts with zero runs.** The 15 existing `workflow-run` records
   carry no closure and cannot acquire one retroactively; they are salvage. Until
   analyses are executed under the boundary, the admissible-assessment count stays
   at its current value, which is zero. This is the intended direction and it is
   not free.
3. **Held environment bytes still may not execute.** §4.5 requires the environment
   artifacts themselves to be held, which closes the yanked-package hole an earlier
   draft left open. What remains is narrower and real: held bytes can stop running
   on future kernels, hardware or drivers. A run can be completely identified,
   completely held, and permanently un-replayable — and no closure discipline
   reaches that.
4. **Equivalence rules and falsifiers are authored, and one loose enough to never
   fire is spellable.** The estimator doctrine applies — a check must be able to
   fail — and §3.1 now requires a `falsification` field without certifying that
   the declared falsifier *could* fire, exactly as `equivalence_rule` is required
   without certifying that it could fail. Both are the same open question and both
   belong with sub-problem 5's conformance oracles. Requiring the field is still
   worth doing: an uncertified declaration is checkable later, an absent one is
   not.
5. **Acquisition is not reproduced** (kernel limitation 2, restated at this
   layer). §4.7's held-form boundary is a floor, and whether the dataset's declared
   acquisition boundary is honest is outside every guarantee above.
6. **DAG normalization is lossy, and nothing identity-bearing depends on it.**
   Checkpoints, dynamic fan-out and notebook control flow can produce executed
   steps the normalized DAG does not represent. §6.2 is what makes this a mere
   presentation limitation: identity rests on the **declared definition snapshot**,
   seeds on a **derivation rule over semantic job keys** that covers jobs nobody
   could enumerate in advance, and the normalized form keys nothing.
7. **Code-lineage independence is an authored claim.** §7.3 certifies
   `independent-implementation` from a recorded claim with a rationale, because
   nothing computable separates a genuine reimplementation from a copy with the
   comments rewritten. It is the same class of limit as world limitation 3c's
   continuity selection under `consolidate` *(restated 2026-08-08; the citation was
   world §8's irreversible merge, a limitation that retired with the operation —
   `2026-08-08-world-address-ruling.md`)* and kernel §8.8's authored acquisition boundary. **It reaches
   classification, not admission** — only `clean-environment, passed` admits
   (kernel §3.3), and a false independence claim therefore mislabels corroboration
   rather than buying eligibility. `not-certified` is the default, so the failure
   mode is a false claim, never an inference.
8. **Run count grows without epistemic content.** Every execution is a node, and
   §5.3 means every nondeterministic transform mints a fresh dataset as well. No
   pruning rule is specified, deliberately — pruning would discard the closures
   verification depends on — but no measurement yet bounds the growth either.
9. **`method` and `pre-registration` mappings are not mechanical.** 78 and 209
   records respectively resolve to spec content or notes case by case, in
   sub-problem 7.
10. **Belief is not recomputable without the corpora** (§7.1). Artifact absence is
    survivable; record absence is not, and the world index carries addresses rather
    than facets. A published belief-input snapshot would close it and does not
    exist.
11. **An unaudited verification is not certified sound** (§7.3c). Recomputation is
    tamper detection at **explicit import** and under **audit**. A self-consistent
    hand-written verification that entered while its inputs did not resolve — or that
    was written straight into a corpus directory and so crossed no import at all —
    stands as recorded until someone audits it, and is indistinguishable from a
    genuine one until then. Making validation automatic on read — or on the inputs becoming
    resolvable — costs R5 in one direction or the other: belief would move because
    of what is mounted. So detection is bound to acts rather than to filesystem
    state, deliberately. It is the recorded-history limitation appearing at the
    verification boundary, alongside limitation 1, and §9's log is what would close
    both. **A corollary worth stating: audit cadence is now a real operational
    question** — nothing here forces an audit ever to run, and sub-problem 6's
    agentic surface is where that belongs. §5.1 and §5.2's constructors inherit this
    limitation exactly: they govern the API, not the filesystem.
12. **Auxiliary-input exclusion is an authored claim, and uncertified reads cost
    corroboration** (§5.2). Nothing computable separates a reference table carrying
    no evidential content from an empirical dataset an author would rather not share
    an ancestor with, so exclusion requires a certification, and an uncertified
    `reads` input leaves the lineage closure incomplete. The failure direction is
    deliberate — uncertified costs independence rather than granting it — but the
    cost is real: routine lookups need certifying before two runs sharing one can be
    called independent, and nothing here estimates how often that will bite. **The
    certification guarantees attribution, not truth**: a false one still omits the
    edge and still inflates belief; what it adds is a named claimant, a rationale and
    a frozen identity. Same class of limit as 7, one relation upstream.
13. **Nothing retires a run, so a reviewed false certification stays epistemically
    active** (§5.2). Freezing the certification into recipe identity makes withdrawal
    mint a different **recipe**, and a recipe is not a belief input — only a run is,
    and only executing the new recipe mints one. Re-execution is therefore additive:
    the corrected run joins the corpus and the original, with its false certification,
    keeps contributing at its original address. The gap is **general rather than
    certification-specific** — no run is retired when its code is later found
    defective, its environment mis-captured, or its input corrupt, because assessments
    are immutable by construction (§5.1) and their addresses are keys over inputs a
    correction does not change. What is missing is a **retraction**: additive,
    attributed, a belief input under kernel §5.1, **structurally subtractive** rather
    than monotone in the belief it produces — retracting a *refuting* assessment
    legitimately raises support — and carrying its own eligibility contract, since
    "remove the evidence against my claim" is subtractive and inflationary at once.
    §13 hands the mechanism to sub-problem 5. **Designed 2026-08-03**
    (`2026-08-03-correction-lifecycle-design.md`): the `retraction` kind is that
    mechanism, with the eligibility contract this limitation asks for. Two details
    of the answer differ from the ask and are worth carrying: the target is
    whatever a computation **reads**, so a *run* is not retraction-eligible — its
    readable products are (5a §4) — and a `dataset-production` run's false
    certification is subtracted through the **`route`** arm. Until C1–C10 are
    implemented this limitation stands as written: review produces attribution and
    no correction, and limitation 12 should be read with that attached.
14. **A divergent producer's deletion restores a certificate** (§5.2, substrate §5
    step 3). Independence reads the dataset's stamped lineage basis, and a producing
    run whose inputs differ from it forces `not-certified` rather than being unioned
    into ancestry — because only the basis is durable, and a union would hand
    independence routes that could be deleted without dangling anything. But the
    divergent run is itself deletable and **no survivor holds a reference to it**:
    recording one would mean appending to a dataset node that may be immutable or
    foreign, which §5.2 declined for the same reason it declined `produced_by`. So
    deleting the divergent run returns the dataset to certified, and the corpus is then
    **indistinguishable from one in which that run never existed**. An earlier
    revision called this "change detection, not loss detection", which overclaims:
    belief is a **computed view** (kernel §6), so no prior digest is durably retained
    anywhere for the new one to differ from — G3 guarantees that two *available* states
    hash differently and retains neither. So this is the plain undetectable-history
    limit of G4 and G8, and limitation 1 at the one place substrate §5's
    descendant-side trick cannot reach. The exposure is narrow: a replay's producer
    transforms the same inputs by construction, so divergence needs byte-identical
    output from a genuinely different ancestor set, whose measured population is zero.
    Narrow is not empty. The **`consolidate`** route to the same conflict (world §5.4) is
    durable **under ordinary APIs** and is not covered by this limitation — but the two
    limits **compose**, and the composite is weaker than either alone: raw-write
    `single(A)` over a `conflict([A, B])` **and** delete `B`'s producing run, and an
    audit sees a well-formed one-route basis with nothing left to contradict it. A
    route's removal is detectable only while the evidence it removed survives. That
    composite case belongs to limitation 11 rather than to this one, and §9's log closes
    it; the durability claim in §5.2 is scoped accordingly.
15. **Producer enumeration is bounded by declared coverage** (§5.2, world §5). The
    divergence test needs every run producing a dataset — a reverse adjacency question
    whose answer depends on how much of the world was consulted. World §5 publishes a
    **producer snapshot** — producers map plus covered-corpus identities, the corpora
    named by the opaque `corpus_id` of world §5's manifest, with the exact corpus states
    and the fixture-bound **enumeration rule identity** in a separate derivation receipt
    record — kernel §5.1 digests the semantic
    pair, and §7.3c's derivation discipline against the receipt makes it recomputable
    rather than merely hashed, so an absent corpus **inside** coverage yields
    `not-present` rather than a silent omission, and two coverages are two belief
    inputs. What none of that reaches is a producer in a corpus **outside** coverage: it
    is not merely unseen but unsuspected, and independence certified under that coverage
    is certified against a world nobody claimed was complete. Coverage converts an
    unbounded question into a bounded one; it does not answer it. And the snapshot
    inherits limitation 11 in full — a fabricated one written straight into place stands
    until an audit runs, because validating on read would make belief depend on the
    checkout. **And the audit's reach is bounded by time as well as by cadence:** world
    §5's receipt *names* its corpus states and its enumeration rule rather than holding
    either, so it is checkable only while it is **`resolvable`** in world §5's sense —
    **each** covered corpus standing at its own recorded state, and that rule still held
    here (world limitation 10). Resolvability is asked only of a **`well_formed`**
    receipt: one whose named corpora are exactly the declared coverage and whose members
    are identities rather than corpus names or version strings. A receipt failing that is
    **`malformed`** — refused at import, reported as its own audit finding when it was
    raw-written in, and never counted as evidence for or against a snapshot. And an audit
    that does refute a snapshot can publish a corrected one but cannot retire the wrong
    one (world limitation 11) — §11.13's retraction again, at a third site. Whether a
    coverage declaration can itself be made accountable — who may narrow one, and whether
    narrowing is visible — is sub-problem 5's, beside retraction eligibility.
    **Answered 2026-08-03** (5a §4, C9): narrowing is **snapshot succession plus
    retraction** rather than a separate target class, so it is visible because the
    retraction is a record and a §5.1 digest member; and *who may narrow* is
    answered by exposure — anyone who can write, attributably and reviewably — not
    by permission.

## 12. What stops being needed

| surface | lines | why |
|---|---|---|
| `graph/run_resolution.py` | 141 | the kernel names the run directly (`Assessment ──produced_by──▶ Run`); the dataset-walk existed only because an evidence line could not |
| `run_fingerprint_policy.py` | 210 | obligation keyed on executor × locality; §2 leaves one obligation and nothing to key |
| `validate/checks/workflow_runs.py` | 216 | fingerprint well-formedness against the retired table |
| `validate/checks/workflow_steps.py` | 158 | `workflow-step` is imported DAG structure (§6) |
| `seed_policy_derivation.py` | 143 | the recipe carries a seed **plan**; realized seeds are occurrence observations keyed by semantic job key |
| `datasets_stochasticity.py` + `_format.py` | 236 | stochasticity is a step property in the imported DAG |
| parts of `run_fingerprint.py` | of 241 | `FingerprintComponent` tri-state as stored state, `CaptureOrigin`, `ExecutorKind`, `ArtifactLocality` |

Plus, in the graph layer: `EvidenceLineEntity.run_refs` with its `sci:runRef`
materialization, and the `sci:derivationKind` / `sci:workflowRun` /
`sci:memberOfParent` triples added solely to make run resolution graph-decidable.

≈ **1,100 lines** of direct surface, before tests. As in the two preceding designs
this is a **scoping estimate, not a promise**, and it is dwarfed by what this design
**builds**: the spec kind and its freeze path, `science.identity.v1`, code-bundle
and held-environment capture, the Snakemake trace adapter, the equivalence
evaluator, and the execution boundary with its receipts. This is not a reduction in
machinery.

**Two deletions that would be wrong, recorded so the plan does not make them.**

`dependence_datasets_by_line` and the dataset lineage walk do **not** die.
Independence still walks `derived_from` from the run's `observes` inputs (substrate
§5), and the dataset-QA ceiling still uses the same traversal. What changes is what
it walks over — a **view** composed from `produces ∘ transforms`, checked against each
dataset's stamped **lineage basis** — and what dies is using that walk to *find the
run*.

`commons/resolver.py` does **not** die and is not replaced by a new store (§9). Its
`{content identity, locator, hash-verifying resolver}` shape is precisely what the
guarantees need, and it already verifies on every call.

## 13. Open questions

- **The empirical-observation facet contract** (kernel §11, still open). §4.6's
  role partition presumes a dataset either carries the facet or does not; what
  *declares* an acquisition boundary, and what distinguishes a dataset that
  carries the facet from one that merely claims it, is the hinge this design
  inherits and does not settle.
- **Whether anything ever collects garbage.** Content-addressed outputs and held
  environment artifacts accumulate; §11.8 declines to specify pruning because
  pruning discards what verification depends on. That is a position on verification
  and not yet a position on disk. **Where** they live is settled (§9: the existing
  resolver shape, no new store until measurements demand one).
- **A publishable belief-input snapshot** (§7.1, §11.10). Making belief recomputable
  without the corpora needs the kernel §5.1 digest members published separately from
  the content they name — the same shape as world §5.1's separable index, for
  different content. Whether the two are one artifact is **no longer purely a
  packaging question**: world §5's producers map and its coverage declaration are now
  a kernel §5.1 digest member, so one belief input already lives in the index. That is
  an argument for one artifact and not yet a decision.
- ~~**Equivalence-rule certification** (§11.4) hands to sub-problem 5.~~
  **CLOSED 2026-08-03** by `2026-08-03-normative-contract-design.md` §7:
  `instrument-certification` is the tenth kernel kind, and an instrument certifies
  by exhibiting witnesses that reach each declared outcome — which is exactly "a
  rule that cannot fail is a defect", made executable (N4–N9). Code-lineage
  independence (§11.7) went with it and came back **unchanged**: 5b limitation 3
  keeps it an authored attestation embedded in the comparison report, the one
  B-form survivor, because there is nothing executable to demonstrate.
- **The scope-derivation rule's version identity** (§7.3) participates in every
  verification address. Whether it is versioned with the belief policy, with
  `science.identity.v1`, or on its own is unresolved.
- ~~**Which binding route rule identities take** (§3.1b).~~ **CLOSED 2026-08-03**
  by `2026-08-03-normative-contract-design.md` §6, and by ruling the two routes
  **halves of one binding rather than alternatives**: a rule identity is
  `(symbol, fixture-set identity)` — the fixtures are the normative half and are
  contract content, so the "registry nobody maintains" is the contract itself —
  and a held implementation in the rules store is the operational half. The
  decision covers interpretation, equivalence and the scope-derivation rule at
  once, as this question asked.
- ~~**What retracts a run** (§5.2, §11.13), and it is the largest of these.~~
  **CLOSED 2026-08-03** by `2026-08-03-correction-lifecycle-design.md`, and the
  answer inverts the question: **nothing retracts a run.** One record kind carries
  all three instantiations with reasons as data (its §2), and the eligible targets
  are exactly the readable inputs — assessments, verifications, semantic snapshots,
  instrument certifications, and production routes. A run is not one; "a run
  happened", and its readable products are what a retraction names. Eligibility is
  answered **procedurally** — named target, attribution, typed reason, recorded
  grounds, and symmetry — never as a truth gate. The question as posed follows,
  preserved rather than edited away:

  Every correction mechanism this design has is a *minting* mechanism — a successor spec, a
  superseding verification, a corrected re-execution — and each of them adds a record
  beside the wrong one rather than removing the wrong one's contribution. That is
  correct for provenance and insufficient for belief: a run established to be
  defective keeps its assessment, and there is no path that says so. The requirement
  is fixed in §5.2 (additive, attributed, a kernel §5.1 digest member, structurally
  subtractive); the open parts are **what carries it** — one mechanism or one per
  reason, since a false exclusion certification, a defective implementation and a
  corrupt input are the same *shape* and may not deserve the same *record* — and **what
  makes one eligible**, which is the harder half: a retraction can raise belief by
  removing a refutation, so nothing about its form stops it being used as the
  authored-belief channel. It belongs with sub-problem 5 beside equivalence- and
  interpretation-rule certification, since all four are judgments about whether a
  recorded thing deserves the weight it has.
- **Multi-product `dataset-production` runs.** §5.2 bounds the shape to one dataset
  or package output, which keeps a run's `produces` edge unambiguous and §5.3's
  equality rule bitwise over one address. A run emitting several distinct products is a real
  pattern and the measured population today is **zero**, so the bound is a deliberate
  under-commitment rather than a claim that it cannot happen. What it would need is a
  rule for whether one differing product fails the whole replay or forks one address,
  and that is the sort of question §5.3 shows is easy to answer wrongly from the
  armchair.

Two questions the first draft left open are **closed** rather than carried: the DAG
import (§6.4 — one schema, one Snakemake adapter, no plugin framework) and
`environment_identity` (§4.5 — held artifacts, containers optional, a bare lockfile
refused).

## 14. Amendments to the banked designs

This sub-problem changes things **all three** earlier documents state — the substrate
included, which a previous revision of this section denied. They are listed here, and
applied there, rather than left as a divergence a later reader has to notice.

**Epistemic kernel (sub-problem 1):**

| § | was | becomes |
|---|---|---|
| §3.3 | `scope` ∈ `same-environment` \| `clean-environment` \| `independent-implementation` | a **fourth** value, `not-certified`, and scope is **derived** (§7.3), never authored |
| §3.3 | lifecycle row "only `same-environment` and/or `inconclusive`" | rewritten as a **complement** — no active failure and no active `clean-environment, passed` — so the table is total and stays total under the fourth scope value |
| §3.3 | the `t078` token table read as total | marked a **partial projection**: `not-certified` has no token, and admission is decided by the lifecycle table |
| §3.3 | verification always `verifies` an assessment | verification has **two shapes** (§5.3); the dataset-production shape carries no `verifies` edge and gates nothing |
| §5, G2a | "An assessment requires an analysis-spec hash predating its run" | restated as an **execution-boundary guarantee**: the boundary refuses to *begin* a run that does not name an already-frozen spec, and records it first. A hash cannot establish chronology, so the old phrasing contradicted its own negative test. The strong claim needs the §9 mutation log |
| §4.2.1 | the assessment facet is normative and run-derived; `estimand` "copied from the frozen spec, never re-authored here" | **given a constructor** (§5.1): one entry point taking the **run ref only**, deriving `outcome`, `estimate` and `uncertainty` by applying the frozen `interpretation_rule` to the boundary-built result, and copying `estimand`, `applicability` and `proposition` from the spec. "Run-derived" was a description with nothing enforcing it; the copy is now performed rather than requested |
| §4.2.1 | independence is derived from complete and disjoint `derived_from` ancestor closures | **the closure is now derived too, and it is the basis rather than the view** (§5.2): no ancestry is authored anywhere, independence walks each dataset's stamped **lineage basis**, and a producing run whose inputs differ from it is **divergent** and forces `not-certified`. Excluding a `reads` input requires an **inline exclusion certification** on that input entry — uncertified, the closure is incomplete and independence is **`not-certified`** |
| §4.1 | closed run signatures list `observes` and `reads`, and no dataset-to-run production edge | **widened by two** (§5.2): `Run ──transforms──▶ Dataset` (lineage input, **confers no eligibility**) and `Run ──produces──▶ Dataset`. `Dataset ──produced_by──▶ Run` was never in the closed list and is also **wrong in direction**: §5.3's successful replay gives one dataset two producing runs, and recording it on the dataset would mean mutating an existing, possibly remote node. `Dataset ──derived_from──▶ Dataset` becomes a **world-derived view** over `produces ∘ transforms`, excluding self-edges — not a stored edge, and **descriptive**: independence reads the produced dataset's stamped, non-editable **lineage basis**, which is a facet rather than a signature and so widens nothing further |
| §5.1 | the belief digest names "assessment revisions" | **keyed assessment facets** — sorted `(assessment identity, canonical facet digest)` pairs (§5.1 here). The revision *lifecycle* is retired because the facet is derived from immutable inputs, but the digest must still cover the **values** belief reads — a raw-written facet occupies the same `(spec, run, proposition)` address, so hashing the identity alone gives a fabricated and a correct belief state the same digest — **and** it must cover the pairing, since a bag of facet digests is permutation-invariant and exchanging two assessments' facets leaves it unmoved. Two corrections, in opposite directions; the pair is what holds |
| §5.1 | the lineage snapshot digests `derived_from` **relations** as `(source, predicate, stored target ref, resolved target uid or null)` | digests each inspected dataset's **lineage basis** (§5.2 here) as `(dataset uid, stored producing-run ref, resolved run uid or null, stored ancestor ref, resolved ancestor uid or null)`, **as a tagged `single(route) \| conflict([route])` with the tag inside the digest, plus the dataset's producer set, its divergence state, and the identity of the world §5 **producer snapshot** those producers were enumerated from** — producers map and coverage only, never the address or alias maps, which W5 requires to be belief-neutral. The stored-and-resolved discipline is unchanged and now applies to the **run** as well: with `derived_from` a view, deleting the producing run deletes the ancestry rather than breaking it, and a dataset that resolves to no ancestry reads as a **root**. The producer set is a member because the divergence test **reads** it — digesting the basis alone left adding a second producer invisible while it changed ancestry and belief |
| §4.4, §11 | `method`, `assumption`, `falsification` absorbed into `analysis-spec` "as fields/refs", not to be collapsed | **given the fields** (§3.1): `method`, `assumptions` and `falsification` are distinct members of the normative facet. The kernel assigned them a home; this supplies it, and since §3.1 rules the Markdown body non-authoritative they had nowhere else to go. `plan`, `pre-registration` and `spec` need no field — they name the spec itself |
| §8.7 | three consequences of the recorded-history capability | **four** — spec-predates-run joins G4, G8 and semantic identity |
| §9 | `t078`'s `independently-reproduced` covers `(independent-implementation, passed)` | it does, as a **classification**; the admission table is unchanged and only `clean-environment, passed` admits |

**World and addressing (sub-problem 3):**

| § | was | becomes |
|---|---|---|
| §4.2 | `run` basis = content identity of the execution closure | unchanged in principle; the closure is specified here as **recipe + result + occurrence** (§4.1) |
| §4.2 | `verification` basis = (two run identities, equivalence-rule hash, scope, verdict) | **extended** (§7.3b): ordered run identities, equivalence-rule identity, comparison-report identity, scope-derivation rule identity, scope, verdict. The scope evidence is **embedded in the comparison report** — since no `certification` kind exists to point at — and is therefore **not a separate basis member**: one digest over the evidence, not two |
| §4.2 | `assessment` basis is `(spec, run, proposition)` **because** a content hash would erase revisions | **same basis, retired rationale** (§5.1): the facet is derived, so there are no revisions; the triple stands as a **key over the constructor's own arguments** |
| §5 | the world index holds **two** maps, address and alias, both forward and both a publication convenience | **a third map, separately identified** (§5.2 here): `dataset address → [producing run addresses]`, published with a **coverage declaration** naming the covered corpora by **stable identity** — a `corpus_id` minted opaque and once, in the corpus manifest world §5 defines — plus a **derivation receipt**, a separate immutable record naming — not holding — the exact corpus-state **identities** it was built from and the **enumeration rule identity** that built it, fixture-bound so an upgrade is a new derivation rather than a retroactive refutation. The divergence test asks a **reverse** question that forward maps cannot answer, and enumerated against the local checkout it shrinks silently. The **semantic snapshot identity** — producers map plus covered-corpus identities, and **not** the address map, the alias map, or the receipt — is a kernel §5.1 belief input, so a corpus move stays epistemically silent (W5) while the enumeration's scope does not. The receipt is what §7.3c's derivation discipline rebuilds against at explicit import and under audit, since hashing a map is change detection and completeness is what belief needs — and only while the receipt is **`well_formed`** against the snapshot — covering exactly the declared coverage, with identities rather than corpus names or version strings as its members, a failure being **`malformed`** and never evidence — and **`resolvable`** — **each** covered corpus at its own recorded state and the named rule still held — so the evidence is time-bounded (world limitation 10) rather than replayable from held bytes. It stays outside the belief identity because exact states move whenever a file moves. Which snapshot a computation reads is an **argument** to it, never a stored selection |
| §4.3 | a merge's surviving content is chosen **field by field** as part of the authored act | **not for the lineage basis** (§5.2 here). Two corpora can hold one content address with different routes, and field selection would make the derived basis authorable by a route that touches no authoring API. The merge **widens** `single` to `conflict([both routes])` — the tagged shape §5.2 defines — the dataset becomes `lineage-divergent`, and no selection or removal is offered by any path |
| §10 Q3 | whether `run` and `assessment` need world identity is open | **closed** (§8): both do, forced by cross-corpus verification |
| §5 | world resolver, composed adjacency and world traversal are required for aliases, dangling checks and lineage closure | **two more consumers**, neither asking for a new capability. (a) §7.3c: verification-derivation validation traverses verification → runs → spec and results, all world-identified, so it runs on the composed resolver for the reason §5 already gives — a corpus-local check reads every cross-corpus reference as broken. (b) §5.2: lineage closure now composes `produces ∘ transforms` and resolves each dataset's **lineage basis**, so the traversal §5 already relocates to the world layer has **more** references to resolve there — a producing run and its input content identities, which may sit in a different corpus from the dataset. W10 covers both |

**Substrate consolidation (sub-problem 2):**

| § | was | becomes |
|---|---|---|
| §3 | `transitive_outbound` / `transitive_inbound` are added to `nodes`, serving "two kernel needs" — lineage closure and `supersedes` chains — under **one** contract | **withdrawn from `nodes`; the contract moves to Science's world layer and splits.** Neither caller could use a corpus-local primitive end to end (world §5 says both cross corpora), and §5.2 here made lineage a **facet**, which a signature over stored `Relation` objects cannot address at all. §2's own pricing argument — two implementations, fixtures, a `STANDARD.md` bump per addition — settles the relocation once the callers are known. The split follows for the same reason one layer down: **one algorithm, two adjacency adapters**. Predicate matching, `directed` and relation-level dangling belong to the *relation* adapter; a lineage step has no predicate and no direction, and the tagged basis is its own vocabulary. Behavioural semantics — cycle-safe, start-excluding, skip-and-report, sorted — stay shared, and the fixture becomes two. The **return shape widens** to `{reached, unresolved}`: a contract that promises to report an unresolvable step has to return it, and §3's argument for the narrow shape rested on `dangling()`, which is relations-only and cannot see a facet step |
| §5 | independence walks the **stored** `derived_from` edge, and the descendant-side orientation makes ancestor deletion detectable as a dangling edge | **the orientation survives; its carrier changes** (§5.2 here). The walk reads each dataset's stamped **lineage basis** transitively over composed adjacency; `derived_from` becomes a **descriptive view** over `produces ∘ transforms` that independence does not read. Step 2's trigger widens from "a dangling lineage edge" to "a basis entry that does not resolve — an absent ancestor **or an absent producing run**", because deleting the run is the case a view cannot see. A **step 3** is added: a producing run whose inputs differ from the basis is **divergent** and issues no certificate — the route the single durable basis cannot carry, refused rather than unioned in undurably or dropped silently |

**This is an amendment the previous revision explicitly denied would be needed**, and
the denial is worth leaving visible. It read: "no amendment, and specifically **not**
because its §5 orientation rule is reused here" — correct about §7.3b, which had just
concluded that the orientation *analogy* fails for scope evidence, since deletion is
detectable only when both ends are nodes and a certification is not a kind. That
argument still stands exactly as written. What it did not license was the inference
that substrate §5 was therefore untouched **by everything else in this document**:
one section later, §5.2 replaced the very edge §5 walks. A statement of the form "we
take nothing from X" is a claim about the whole document, and it was made from one
section's vantage.

The §3 row is the same lesson at the level of the substrate's own boundary ruling.
`nodes` was given the closure primitive because the operation *looked* domain-free and
symmetric with a membership closure already shipped — a judgment about the operation's
shape, made without asking where its two callers would run. Both ran here. **An
interface is justified by who can call it**, and "general-purpose" is not a
substitute for naming them.

The correct statement about §7.3b alone: embedding the scope evidence in the
comparison report needs **nothing from the substrate**. It is content inside an
immutable record, not a relation, so no `nodes` operation, no orientation rule and no
dangling-edge mechanism is involved.

What §7.3c **does** take from the substrate is §4.2's untrusted-import framing, used
as stated rather than amended: a raw write producing a valid-looking node passes the
stale-hash and corpus checks, so Science adds **recomputation above them** — and adds
it at the **world layer**, not inside `nodes`, because the predicate resolves a
verification's runs, spec and results, which world §4.2 places in world identity and
which therefore may sit in different corpora. That is the same relocation world §5
already performs for lineage closure, and for the same reason: a corpus-local check
reads every cross-corpus reference as broken. Nothing about what `nodes` guarantees
changes, and substrate §4.3's limitation is unchanged — restated in §7.3c and pinned
by R19's negative (d), which asserts that an unaudited self-consistent verification
stays indistinguishable from a genuine one. The recomputation is bound to **import
and audit**, not to reads, so it never turns a mount into an admission change in
either direction.

**World and addressing gains one obligation from this**, recorded in the table above:
the world resolver and composed traversal world §5 specifies are what §7.3c's
predicate runs on. It is a consumer of that capability, not a new requirement on it.

## 15. Workflow-surface amendments (2026-09-02)

These amendments landed with conformance cut 15. They narrow or widen the
specific statements below; the surrounding rules remain in force.

### 15.1 §6.2 job-set conformance has a prior enumeration except at checkpoints

Section 6.2's statement that no prior job enumeration exists is narrowed.
The boundary now performs a planning launch for every run and records its
non-checkpoint jobs. Single-run conformance requires every ordinary executed
job to belong to that planned set and requires every resolved target job to
execute. A checkpoint-expanded job still cannot be enumerated before the
checkpoint runs, so it is admitted by the workflow definition's explicit
`checkpoint_expanded_families` declaration and then checked by family.

The adjacent rule is unchanged: a job-set difference between two runs is a
comparison-report diagnostic and contributes to no verdict and no scope.

### 15.2 R16's definition/plan predicate has two dispositions

The equality between the workflow definition's union of family streams and
the recipe's logical streams remains a pre-effect boundary check. A mismatch
there is refused before planning or execution. The same predicate is now also
statable about a constructed or decoded closure; a mismatch found there is
`non-conforming`. This is a widening of R16's evidence surface, not a
replacement of its primary refusal disposition.

### 15.3 Versioned workflow and run-record shapes

The workflow definition is `science.workflow-definition.v2`, and a recipe
carrying its snapshot is `science.recipe.v2`. A receipt now composes planning
and execution launch attestations under `science.boundary-receipt.v3`
(minimal) or `.v4` (confined). The matching run domains are:

| recipe shape | receipt shape | run domain |
|---|---|---|
| v1 identity-only | boundary receipt v1 | `science.run.v1` |
| v1 identity-only | confined receipt v2 | `science.run.v2` |
| v2 snapshot | composed receipt v3 | `science.run.v3` |
| v2 snapshot | confined composed receipt v4 | `science.run.v4` |

Every recipe/receipt cross-pair outside this matrix is malformed. Existing
v1/v2 records decode and recompute untranslated; typed closure decode requires
the v2 snapshot and refuses to invent one for a v1 record.
