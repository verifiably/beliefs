# Epistemic kernel — design

**Date:** 2026-08-02
**Status:** design, approved in session. **Amended 2026-08-07** — §4.2's
`mechanism` row cited `claim_layer: mechanistic_narrative` as an existing home
for it; that value was ruled **not admitted** to the base layer set by the
typing exercise, and the row is corrected in place. The absorption stands; the
route does not.
**Scope:** sub-problem 1 of 7 in the system redesign (see §10)

## 1. Why

Science grew organically. It now carries 151,645 LOC across 595 modules, 907 test
modules, 63 validation check modules registering 89 checks, 51 CLI groups, 50 core
entity kinds (21 epistemic) and 23 relation kinds. It imports neither `atoms` (durable atomic filesystem
effects) nor `nodes` (the entity/relation kernel) — both of which name
Science as their consumer in their own architecture docs.

The complexity is a symptom. The cause is that **the project's stance is written
as prose and enforced as after-the-fact checks over a schema that permits the
violation.**

The stance, from `docs/user-guide/big-picture.md`:

> Literature claims are *hints*, not facts. Belief updates from our own
> analyses, not from what a paper concluded.

The implementation instead gives literature an evidence type, a finding grade,
and a ceiling. A ceiling is a permission: it says *this may bear on belief, just
not too much*. The gap is not theoretical. In
`science_tool/annotation/cross_paper_evidence.py`:

```
:88-91   lit_assertion_uri()  ->  PROJECT_NS["evidence-line/lit-assertion/<sha256>"]
:71-84   "asserted"     -> (SUPPORTS,  PROXY_SUPPORT,         MODERATE)
         "negated"      -> (DISPUTES,  PROXY_SUPPORT,         MODERATE)
         "hypothesized" -> (SUPPORTS,  BACKGROUND_CONSTRAINT, WEAK)
:69,:125 INDEPENDENT stamped unconditionally on every emitted line
:160     _belief_for_units -> aggregate_belief(collect_evidence_units(...))
```

A paper's speech act is not converted into an evidence line downstream — it **is**
one, by URI construction, and it runs through the identical aggregation path as
empirical evidence with independence assumed. `EvidenceStrength.MODERATE` for
"a paper said so" is the creed inverted in a lookup table.

What that costs, from the open feedback corpus (62 items, 2026-07-18 → 2026-08-01):

- `fb-2026-07-28-002` — a **fabricated** citation (real authors, real topic,
  well-formed DOI, no such article) backed a `Strong / literature_evidence`
  finding for four months, with a task built on it.
- `fb-2026-07-28-003` — two paper entities already carried the correct marker
  ("LLM-derived orientation note; not evidence eligible until checked against the
  source") as free text in one field, so nothing propagated it and three sibling
  entities were written without it.
- Ten items (`fb-2026-07-18-009` … `fb-2026-07-19-014`) are one failure class:
  a claim stated at a broader scope than its source licenses — wrong denominator
  flipping a verdict, non-commensurable estimands fused into "convergence", a
  subgroup split read as effect modification at p_interaction = 0.27, an
  `[UNVERIFIED]` hedge dropped in propagation. All were prose norms asking an
  agent to remember restrictions the schema never made anything carry.

This document specifies the kernel that makes those states unspellable rather
than checked.

## 2. The invariant

> **Only an assessment successfully reproduced from primary observations we
> possess may affect empirical belief.**

There is no rule banning literature. The ban falls out of a typing discipline:

> **A paper is not a measurement of the world. It is a measurement of what
> someone wrote.**

A computation over a literature corpus therefore produces claims about the
corpus, never about nature. Literature → world-belief is not rejected by a
check; there is no edge that spells it.

### 2.1 What this does and does not guarantee

Stated once, and load-bearing for every later section:

**Guaranteeable:** representational eligibility, and execution replay.

**Not guaranteeable:** that observations are honest, that measurements are valid,
that models are appropriate, or that an estimand matches the claim it is used
for. These remain visible scientific uncertainties, addressed by QA, sensitivity
analysis, pre-declared interpretation rules, and independent replication over
independent data.

Any later document that uses the word "guarantee" must land on the first list.

### 2.2 "Held" / "we possess"

An input is **held** when we can produce its exact bytes on demand and identify
them by content hash. Held is about *possession and addressability*, not about
being raw and not about location:

- A normalized expression matrix we store is held. A GEO accession number is not.
- Access-controlled data we have and can re-read is held, even though we may not
  redistribute it.
- Data outside the repository is held if content-addressed and retrievable.
  **Git-tracking is not the eligibility mechanism** — content addressing is. This
  is deliberate: `fb-2026-07-25-014` records 46 of 56 pre-registrations frozen on
  gitignored outputs, unsatisfiable because the current check requires
  git-tracking of multi-GB and access-controlled vehicles.

Eligibility asks whether we hold the inputs and the complete processing closure
from the most upstream form we hold — never whether the data is raw.

## 3. Reproduction is an eligibility gate, not a ceiling

Reproduction state is **admission**, not strength. Mixing them repeats the
`STANCE_EMIT` error with a different input, and it was already ruled out — the
`t077` run-reproducibility contract design (`meta/doc/plans/2026-07-09-...`)
records it as an explicit non-goal:

> "A missing run is **absent required structure**, not a weak epistemic verdict;
> belief must not silently cap or exclude it, because that turns a malformed
> empirical line into a plausible-looking downstream result."

| Execution state | Epistemic consequence |
|---|---|
| Closure captured, not replayed | Run artifact only. **No assessment.** |
| Same-environment rerun | Self-consistency diagnostic. **No assessment.** |
| Clean replay from captured closure | Assessment becomes belief-eligible |
| Independent implementation, same data | Verifies the assessment. Not new evidence. |
| Independent data | New evidence unit, new independence group |

A single cleanly reproduced assessment remains a single assessment. It does not
become `well_supported` by virtue of being reproduced. Conversely an unreplayed
result contributes nothing — not `fragile`, nothing.

### 3.1 Definition

> **Successfully reproduced** means a second, full execution in a fresh
> environment reconstructed solely from the captured closure, using the exact
> held inputs, with no undeclared dependencies, whose outputs satisfy a
> predeclared equivalence rule.

The **closure** comprises: analysis-spec hash, code, environment, parameters,
held-input hashes, seed / nondeterminism contract, and output manifest.

Exact output hashes are preferred. Legitimate numeric nondeterminism uses a
versioned tolerance **declared in the spec before execution**, which the
spec-hash-predates-run rule (§5, G2a) already protects.

A seeded-subsample smoke test proves the machinery can execute. It does not
reproduce the assessment and cannot confer eligibility.

### 3.2 Spec supersession after failed replay

The pre-declaration guarantee is decorative without this.

If a replay fails, an author can revise the tolerance, obtain a *new* spec hash,
and that hash still predates *its* run. The rule is satisfied; tolerance shopping
is invisible; only the winner is durable.

Therefore: **a spec whose replay failed is recorded as superseded-after-failure,
and its successor must reference it.**

**But this is weaker than it first reads, and the weakness is stated, not
patched.** The rule only exposes shopping when the failed attempt was *retained*.
An author who discards the failure outright, then runs a fresh spec, presents a
history that is complete, consistent, and passing. No hash and no author-supplied
date can distinguish that from a first-attempt success, because the evidence of
the discarded attempt never existed durably.

> **Guarantee as narrowed: lineage among recorded attempts.** The system
> guarantees that *recorded* failed attempts cannot be silently orphaned. It does
> **not** guarantee that all attempts were recorded.

Strengthening it to the full claim requires every attempt to be registered
durably *before* execution, in an append-only sequence the author cannot rewrite.
`atoms` — a write-ahead journaling engine — is the natural home for such a
registry. A7's chain and effect/recovery executor landed 2026-08-14, including
the engine half of pre-mutation registration; A8's durability certification
landed 2026-08-17. Science still owes composition-root adoption, anchor carriage,
and verification, so this is
not yet a present Science capability. `atoms`' authority design §15 recorded the
obligation — including that its recovery journal alone is not the registry —
and the A7 implementation discharges the engine half. Recorded here so that a
later document does not quietly assume the stronger end-to-end guarantee.

This is the §2.1 discipline applied to my own rule: the strong version is not on
the guaranteeable list, so it is not claimed.

### 3.3 Verification is an artifact, not a state

Successful reproduction requires **two** executions, but the structure named only
`Run` — leaving nowhere to name the original run, the replay run, the comparator,
the observed difference, or the attempt itself. A bare `verification-failed` flag
on the assessment cannot carry any of that, and says nothing about what happens
to belief already computed.

> A **verification** is an immutable node referencing the original run, the
> replay run, the **equivalence-rule hash** taken from the frozen spec, the
> observed differences, and a `(scope, verdict)` pair.
>
> `scope` ∈ `same-environment` | `clean-environment` | `independent-implementation`
>            | `not-certified`
> `verdict` ∈ `passed` | `failed` | `inconclusive`

**Amended by sub-problem 4** (`2026-08-02-computation-reproducibility-design.md`
§7.3, §5.3, §7.3b), which specifies the run closure this node compares:

- `scope` is **derived** from how the two runs' execution recipes relate, never
  authored — an authored scope is a field an author can raise into admission.
- `not-certified` is the fourth value and admits nothing: it is what a pair of runs
  earns when the evidence for a stronger scope is absent, exactly as substrate §5
  refuses to read an absent lineage as demonstrated common ancestry.
- Verification has **two shapes**. The assessment shape carries `verifies →
  assessment` and controls admission; the **dataset-production** shape references
  two runs, uses the built-in `dataset-content-equality/v1` rule, carries no
  `verifies` edge and gates nothing.
- The node's **comparison report carries the evidence its scope rests on** —
  boundary receipts, conformance results, and any code-lineage certification —
  **inline**, so that two verifications resting on different evidence are two
  different nodes. It is *not* a reference: no *code-lineage* `certification` kind
  exists to point at (amended 2026-08-03 — the tenth kind,
  `instrument-certification`, certifies executable instruments, never authored
  lineage claims; normative-contract §7.2, §7.5),
  and a receipt is nested inside a run rather than being a node, so the dangling
  edge an earlier revision promised here cannot be constructed. Withdrawal of a
  certification is answered by a **superseding verification**, per §3.3's
  immutability.

**It is a kernel kind, not a loose artifact.** `nodes` relations target node refs,
and every ref is a `kind:slug` node id (`STANDARD.md` §2.2, §3), so a
`verified_by` relation cannot point at something that is not a node. Storing
verifications in a facet on the assessment was the alternative and is worse here:
G8 requires *later* verifications to accrue against an existing assessment, so a
facet would mean mutating the assessment each time — and sub-problem 4 §5.1 makes
the assessment an **immutable derived output** with no revision path at all, so a
mutating facet is not merely awkward but unspellable. The conclusion is unchanged
and now stronger: verification is the **eighth kernel kind**, operational.

#### Lifecycle — one model, fail-closed

The assessment has no verification field. Its verification state is **derived**
from the verifications pointing at it:

| Verifications present | Assessment state |
|---|---|
| none | **not admitted** — no assessment participates in belief |
| any active `failed` | **invalidated** — fail-closed, regardless of passing siblings |
| ≥1 active `passed` at `clean-environment` scope, no active `failed` | **admitted** |
| no active `failed` and no active `clean-environment, passed` | **not admitted** |

The final row is written as a **complement**, not as a list of cases. An earlier
version enumerated "only `same-environment` and/or `inconclusive`", which left
`(independent-implementation, passed)` and `(not-certified, passed)` matching **no
row at all** — a lifecycle table with holes in exactly the states a reviewer would
reach for. Stated as a complement it is total by construction, and it stays total
when sub-problem 4 adds a fourth scope value.

"Active" (amended 2026-08-03, correction-lifecycle design §7a): not superseded by
a later verification that explicitly references it, **and not targeted by a
standing retraction** (correction-lifecycle §4). **While it is recorded**, a
failing verification is cleared only by a **resolution** — a subsequent
verification naming the failure it supersedes — **or by a standing retraction**,
both addressed, attributed acts; and never by adding a passing sibling.
Precedence remains explicit supersession, now joined by explicit subtraction.

A newly active `failed` verification **forces belief recomputation** for every
proposition its assessment touched.

**Deletion is not covered by this rule.** A verification owns its
`verifies → assessment` edge, so removing the verification node leaves no
dangling reference on the assessment, and a passing sibling then suffices for
admission. Immutability of a node's *contents* does not make the node
*undeletable* under `nodes`. Deleting a recorded failure therefore falls under
§3.2's undetectable-history limitation, identically to discarding a failed replay
attempt — same defect, same missing mechanism, same honest bound.

The Science profile SHOULD refuse verification deletion through its ordinary API
as an accidental-damage guard. That is hygiene, not tamper evidence, and it must
not be described as the latter until the append-only registry of §3.2 exists.

#### Reconciling the `t078` vocabulary

`t078`'s tokens are not a competing enum; they are a derived reading of
`(scope, verdict)`, which is why both can be kept without ambiguity:

| `t078` token | derivation |
|---|---|
| `unverified` | no verification node exists |
| `self-consistent` | `(same-environment, passed)` |
| `independently-reproduced` | `(clean-environment, passed)` or `(independent-implementation, passed)` — note that only the **first** admits; the second classifies |
| `failed` | any active `(·, failed)` |

**The `t078` vocabulary is a partial projection, not a total one.**
`not-certified` has **no** token: nothing in that four-value set names "a replay
happened and the evidence for any stronger scope is absent." Reading the absence of
a token as `unverified` would be wrong — a verification exists — which is why the
lifecycle table above, not this vocabulary, is what decides admission.

Only `clean-environment, passed` admits. `self-consistent` is a diagnostic and
confers nothing, which is the §3 table restated at the vocabulary level.

## 4. Structure

```text
literature corpus ──▶ source assertion ──asserts/denies/hypothesizes──▶ proposition
   (a dataset, but a          │                                          ▲  (semantic
    `reads` input only)       └── no path to belief                      │   identity)
                                  (no such edge exists)                  │
                                                                         │
held observations ──observes──▶ run ──▶ assessment ──────────────────────┘
  (empirical-observation           ▲         ▲              assesses
   facet + acquisition             │         │
   boundary)                       │     verification  (node, §3.3: 2 runs +
                                   │      ──verifies──▶  rule hash + scope +
  corpora / ontologies ──reads─────┘                      verdict)
  (never confer eligibility)       │
                                   └── executes ──▶ analysis spec
                                                     (frozen pre-run:
                                                      target · estimand ·
                                                      interpretation rule ·
                                                      equivalence rule)
                                                                         │
                                                                         ▼
                                                                 empirical belief
                                                                    (computed)
```

### 4.1 The guarantee lives in closed relation signatures

Not in an entity class. A class is a **roster** — every new kind must be
remembered into it, so it has a hole by construction. A signature is a
**predicate**.

```text
SourceAssertion ──asserts | denies | hypothesizes──▶ Proposition
Assessment ─────────────assesses──────────────────▶ Proposition
```

**Only `assesses` is consumed by belief aggregation.** Nothing else requires an
inert class or a per-kind flag. Inertness is the default; belief-bearing is the
declared exception, and it is declared exactly once.

Closure relations:

```text
Assessment  ──produced_by──▶ Run
Assessment  ◀──verifies─── Verification     (§3.3; also ──replays──▶ Run ×2)
Run         ──executes────▶ AnalysisSpec
Run         ──observes────▶ Dataset   (empirical-observation facet required)
Run         ──transforms──▶ Dataset   (dataset-production lineage input; confers no eligibility)
Run         ──produces────▶ Dataset   (dataset-production output; `derived_from` is a view over
                                       produces ∘ transforms, never a stored edge. The produced
                                       dataset carries a stamped **lineage basis** — a durable
                                       descendant-side record, not an edge — so that deleting the
                                       run leaves the loss detectable; sub-problem 4 §5.2)
Run         ──reads───────▶ Dataset   (corpus, ontology, reference, simulator config)
AnalysisSpec──targets─────▶ Proposition
SourceAssertion──anchored_in──▶ Source     (span-level)
Source      ──member_of───▶ Dataset        (the corpus is a dataset)
```

#### Input roles are what close the signature

A single `consumes` edge does **not** close it. Because a literature corpus is a
dataset, `Run ──consumes──▶ Dataset` would satisfy every signature for:

```text
literature-corpus Dataset ◀──consumes── Run ──▶ Assessment ──assesses──▶ world Proposition
```

— reinstating literature → world-belief through the input side, which is the
exact route §2 exists to forbid. Therefore inputs are **role-typed**:

- **`observes`** — a held dataset carrying an **empirical-observation facet**:
  a measurement of the world, with a declared acquisition boundary.
- **`reads`** — everything else a run legitimately needs: literature corpora,
  ontologies and term catalogs, reference graphs, simulator configuration,
  parameter files.

> **Eligibility predicate.** An `assesses` edge is admissible only if its
> assessment's run has **at least one `observes` input**, all inputs are held
> (§2.2), and the assessment is in the **admitted** verification state (§3.3).
> `reads` inputs never confer eligibility, in any quantity.

This also dissolves the "primary observations" tension: eligibility rests on the
empirical-observation *facet* and its declared acquisition boundary, not on the
data being raw. A normalized matrix with a declared boundary is an `observes`
input; a corpus of paper full texts is not, however well-processed.

#### Proposition identity must be semantic, not nominal

One canonical proposition identity is only safe if that identity is **immutable
under semantic change**. `nodes` does not supply this: `uid` is "immutable,
corpus-unique … survives renames" and is "the join key and identity anchor"
(`STANDARD.md` §2.1, §3), and relations bind `uid`. `metadata.version` exists but
nothing binds it.

So editing *"X affects Y in adults"* into *"X affects Y in all humans"* keeps the
same `uid` and silently retargets every source assertion and every assessment
already bound to it — institutionalizing precisely the scope-widening failure
this kernel exists to prevent (`fb-2026-07-18-009`, `fb-2026-07-19-009`).

> **Rule** (amended 2026-08-05 — formal model §6, ρA1/ρA3/ρA4). A proposition
> **is** a typed claim, and carries a **semantic identity**:
> `I_claim(c) = H(tag_claim ‖ encode(π_claim(c)))` — a hash over the claim's
> canonical projection, which is its **operator**, its **sorted bound argument
> referents**, its **qualifiers**, its **polarity**, and its **claim layer**. No
> prose participates. That hash is **immutable for the life of the node**. Any
> edit that would change it instead **mints a new proposition node — new `uid`,
> new id — linked to the old by `supersedes`**. Edits that do not change it
> (typography, formatting, body prose, the display gloss) are ordinary
> revisions.

The prior basis was *"a hash over its normalized `statement` plus its factored
fields (`subject`, `predicate`, `object`, `polarity`, `claim_layer`)."* Four
things changed, and each is load-bearing: prose **left** the basis; `qualifiers`
**entered** it, because §4.1's own founding example turns on *"in adults"*
versus *"in all humans"* and without a qualifier slot the two would collapse to
one identity; `subject` and `object` became **sorted referents bound to a
vocabulary** rather than bare strings; and `predicate` became **`operator`**,
issued by a domain contract rather than drawn from a closed nine-term enum
(limitation 4). The projection's field order, per-position encoding and the
`tag_claim` domain-separation tag are fixed by `science.identity.v1`; the closed
kernel tags — quantifiers, polarities, layers — are fixed by the `science` base
contract.

This **strengthens** the guarantee G7 tests rather than weakening it. Under the
prior basis a scope-widening edit forked identity only if the prose changed
enough to move the hash — the "too loose" horn §11 named. Under the typed
projection it forks whenever a typed field differs, and prose cannot mask it.

Relations keep binding the node ref / `uid`, exactly as `nodes` specifies. No
parallel reference scheme is introduced: because a semantic change produces a
*different node*, ordinary `nodes` references preserve every prior binding for
free, and old assessments continue to point at the proposition they actually
assessed. The immutability is a **node invariant**, not a new addressing layer.

##### Prose is not identity — and after 2026-08-05, prose is not a field either

"Normalized statement" above needs a home, and today it does not have one. The
current promotion path *derives* the proposition title from `subject predicate
object` and then hands ownership to the author — `title` sits in
`CREATE_ONLY_KEYS`, and the module comments call titles "durable authored
source" whose value "wins" on update
(`dag/entity_frontmatter.py:76-99`). So `title` currently **is** the statement,
edited freely, with no identity consequence.

That cannot survive alongside a semantic hash. A field cannot be both
hand-editable prose and an identity input.

> **Rule** (amended 2026-08-05 — formal model §6.5, ρA2). The doctrine above
> applies one field further: `statement` too cannot be both hand-editable prose
> and an identity input, so it is **not stored as an identity-bearing field at
> all**. Prose appears in two places, each with **exactly one construction
> authority**: an **unstored `render(Claim, Locale)`**, derived from the typed
> projection and never authored; and an optional authored **`display_statement`**,
> never derived. Both are **identity-inert**. `title` remains **display only** —
> defaulting to the rendering, freely overridable, and never an input to
> identity, belief, or matching.

The prior rule made `statement` "a semantic field: covered by the hash,
immutable for the life of the node, and writable only through the
mint-a-successor path." That was the right instinct applied to the wrong
carrier: it is the *claim*, not a sentence about it, that must be immutable.
With the typed projection carrying identity, a prose field covered by the hash
buys nothing and costs the normalization problem §11 records.

**One rendering, one authored gloss, and neither is identity.** `render` takes a
locale so that a claim can be shown in more than one language without any of
them being privileged; nothing downstream of identity may consume its output as
a key.

This is the one substantive change to the proposition record. **For new writes it
is mechanical**: the typed claim is constructed at mint, the rendering follows
from it, the author's override — the thing `CREATE_ONLY_KEYS` exists to preserve
— keeps living on `title` and `display_statement`, where editing it is harmless,
and what changes is that editing the *claim* is no longer indistinguishable from
editing its *label*.

**There is no mechanical migration, and the clean start is why.** An existing
record may carry an author-overridden title, incomplete factored fields, or both,
and in those cases the original derived title is **unrecoverable** — the override
destroyed it, which is exactly the defect being fixed, observed after the fact.
The adoption ledger's §0 settles what follows: records are **reproduced under
this system, never migrated into it**, because a migrated record is a
provenance-weak assertion of precisely the kind these guarantees exist to
exclude.

> **Reproduction rule** (replaces the migration rule, 2026-08-05 — ρA1, ρA2,
> ledger §0). A legacy record contributes **two independent things, with no
> derivation between them**. Its `title` is copied verbatim into
> `display_statement`, which is identity-inert and asserts nothing. Its claim is
> **constructed afresh through the ordinary authoring boundary** — the same typed
> constructor every new claim passes — from the sources, not from the old
> record's fields. Where that construction does not succeed, the result is a
> **typing-work item and no proposition**: nothing is minted, no typed field is
> inferred from prose, and no record enters the system in a degraded state.

**Why the rule is not a test applied to the old record.** A draft of this
amendment made it one — *"mark the record suspect where its factored fields do
not type as a claim"* — and that was wrong twice. It is **not stricter** than the
rule it replaced: a record whose fields type perfectly while its *title*
contradicts them passes the type check and failed the old prose comparison, so
the two conditions are **incomparable**, not ordered. And it is **not
checkable**: deciding whether a title carries a qualifier the fields omit means
interpreting prose, which is the extraction problem (limitation 3), not a type
check. Under the reproduction rule neither question arises, because nothing is
being converted. The old fields are **evidence a human reads**, with the same
standing as the source itself, and the typed claim's only construction authority
is the boundary.

This is the "treat all as suspect until verified and re-situated" disposition
(sub-problem 7) at its sharpest. The legacy record stays readable and
inspectable against its own sources, and it certifies nothing — not because it
was flagged, but because it never became a proposition in this system at all.

### 4.2 The kernel

Eight kinds. Three carry epistemic semantics; five provide operational closure.

| kind | role | absorbs |
|---|---|---|
| **proposition** | the one canonical truth-apt statement | `mechanism` — **but not by the route this row first gave**; see below |
| **source-assertion** | a source asserted / denied / hypothesized it | — |
| **assessment** | run-derived result bearing on a proposition (facet in §4.2.1) | `evidence-line`, `finding`, `observation` |
| **analysis-spec** | target, estimand, eligible inputs, interpretation rule, equivalence rule — frozen pre-run | `pre-registration`, `plan`, `spec` (as fields/refs, not as identity) |
| **run** | one execution closure (carries no verdict — see `verification`) | `workflow-run`, `transformation`; `workflow`/`workflow-step` become *imported* DAG structure |
| **verification** | immutable comparison of two runs: `(scope, verdict)` + equivalence-rule hash + differences (§3.3) | — (new) |
| **dataset** | held data + manifest + QA — **including a literature corpus** | `data-package`, `research-package` |
| **source** | a paper / book / talk as a record in a corpus | `paper`, `article`, `book`, `talk`, `prose-source` |

> **Amended 2026-08-07: `mechanism`'s absorption route is withdrawn.** This row
> said `mechanism` was *"already expressible as `claim_layer:
> mechanistic_narrative`."* It is not. `mechanistic_narrative` is a value of the
> **predecessor** system's layer enum; the `science` base contract's layer set is
> the closed `[causal, structural, statistical, methodological]`, and the typing
> exercise ruled the value **not admitted** to it — all 13 records carrying it,
> across two corpora, are unstructured, so the layer would admit zero claims
> (`2026-08-07-multi-corpus-typing-exercise.md` §5.2, survey §9.3).
>
> The absorption itself is **not** withdrawn: `mechanism` is still not a kind,
> and the two mm30 records that motivated this row — 0014 and 0015 — were
> independently adjudicated as propositions **blocked on modality**, which is a
> grammar gap (§6.4) and not a missing kind. What is withdrawn is the claim that
> a home for them already exists. It does not, and the layer is not where it will
> be. This is the ordinary case of a banked row citing a vocabulary that later
> failed admission, and the fix is to say so rather than to widen the layer set
> to make the sentence true.

There is **one proposition identity**, not a world/discourse pair. Papers assert
it; reproduced analyses assess it. This is what removes the alignment problem: no
two-sided join between separately-produced claim sets, so no manufactured
divergence. Referent binding survives only as a *one-sided* extraction question
("does this span assert P?"), which is bounded and measurable against a labeled
sample.

`source-assertion` is **not** extraction-only. Human curation is legitimate when
anchored to a source span and attributed. Authorship affects extraction
reliability; it never affects world-belief eligibility.

Because a literature corpus is a dataset, citation verification (`science bib
verify`, per `fb-2026-07-28-002`) is **data QA on that dataset**, reusing the
same machinery as structural QA on an experimental one.

**It must not feed the empirical-belief ceiling.** A literature corpus is only
ever a `reads` input, so its QA verdict gates *discourse measurements* — the
counts, coverage and recall of §6 — and nothing else. Routing corpus QA into the
empirical ceiling would reconnect literature to world-belief through the QA back
door, the same defect as an unrolled `consumes` edge.

### 4.2.1 The assessment facet

Belief cannot be recomputed from assessments that carry no contract, so the
minimal facet is normative, not illustrative:

| field | contract |
|---|---|
| `proposition` | the **semantic identity** assessed (§4.1) |
| `outcome` | `supported` \| `refuted` \| `inconclusive` — **scientific outcomes only**; verification state is never an outcome, it is derived from the verification nodes (§3.3) |
| `estimate` | the quantity, where the interpretation rule yields one |
| `uncertainty` | interval / dispersion, on the estimate's own scale |
| `estimand` | population, outcome definition, endpoint type, control structure — copied from the frozen spec, never re-authored here |
| `applicability` | the scope the estimand licenses, which may be narrower than the proposition |
| `interpretation_rule` | ref to the frozen rule in the spec that mapped the run's output to `outcome` |

**Independence is derived, never authored.** It is computed from upstream dataset
lineage: two assessments are independent when their `observes` inputs have
**complete and disjoint** ancestor closures. This is the direct fix for the
original defect — `cross_paper_evidence.py:69,125` stamps
`IndependenceTag.INDEPENDENT` as an unconditional module constant. An authored
independence tag is an assertion about the world wearing the costume of metadata.

Independence is **three-valued**, and the third value is the point:

| state | meaning |
|---|---|
| `independent` | complete lineage closures demonstrated **disjoint** |
| `shared-source` | common ancestry **demonstrated** |
| `not-certified` | independence **not demonstrated** — a computed state, never authored |

`not-certified` is not a synonym for `shared-source`. Calling an incomplete
closure "shared-source" would assert demonstrated common ancestry from an absence
of information — the same unknown-as-verdict error this kernel exists to remove
(cf. `fb-2026-07-19-011`: absence of evidence is indeterminate, never a fail).

**Independence is pairwise, and pairwise relations do not partition.** This is
not a detail of presentation — it kills any rule that builds groups directly out
of pair states. Three assessments with ancestor sets `A={x}`, `B={x,y}`,
`C={y}`: A–B share `x`, B–C share `y`, A–C are demonstrably disjoint. A partition
would have to place A with B, B with C, and A apart from C. No partition does
that, and every one of the three facts is *demonstrated* — the counterexample
needs no `not-certified` pair at all.

> **Model.** Aggregation reads a **dependency graph**, not cells. Vertices are
> all **directional** assessments on the proposition, **both directions
> together**. An undirected edge joins every pair that is **not certified
> `independent`**.

**"Directional" was added 2026-08-05** (belief-policy §3.4). `outcome` has three
values and this section reasons only about two of them; an `inconclusive`
assessment has no direction, so it can neither corroborate nor oppose. Admitting
it as a zero-weight vertex would be strictly worse than excluding it, because
selection below is **cardinality-first**: a vertex contributing nothing can
enlarge a maximum independent set and thereby displace a *contributing*
assessment from the winning selection, moving the value through a channel with
no evidential content. The exclusion is about the **value** only — an
inconclusive assessment's keyed facet remains a G3 closure member, so adding one
moves the digest (belief-policy P8).

**The outcome-to-sign mapping is not the policy's to choose.** `supported ↦ +1`,
`refuted ↦ −1`, `inconclusive ↦ 0` belongs to base outcome semantics and to the
`science_contract`'s meaning-bearing content (domain-extension §8), because a
policy permitted to map those to signs is a policy permitted to reverse them,
and reinterpreting an outcome is not aggregating it.

Two consequences fall out rather than being legislated:

- **`not-certified` needs no special case.** The edge is the default; only a
  certificate removes one. "Independence not demonstrated" and "dependence
  demonstrated" both leave the edge in place, and they differ only in what the
  finding says and what a curator can do about it. Every rule the previous
  formulation needed to state about uncertified assessments is now a property of
  a graph with more edges in it.
- **The graph spans directions.** Shared ancestry between a supporting and a
  disputing assessment is a demonstrated fact; partitioning per direction, as an
  earlier version of this section did, would discard it.

> **Selection.** Corroboration multiplicity is a **maximum set of pairwise
> non-adjacent vertices** — the demonstrably-independent assessments, taken as
> large as the certificates allow.

**Not connected components**, though they are simpler and look more conservative.
Components are contagious: one assessment uncertified against everything joins
every component into one, erasing independence that was actually demonstrated. In
the example above, components give 1 where the certificates support 2. That is
the same defect from the other side — it lets adding a sloppy assessment destroy
established belief, which is a manipulation vector, not a safety margin.
Conservatism that can be *induced* is not conservatism.

The conditions that force `not-certified`, and their `lineage-incomplete`
finding, are specified in the substrate design.

#### How the graph controls belief — there are no cells

Assigning every assessment to some cell, with dependent pairs forced to share
one, **rebuilds connected components under another name**: on `A—B—C` the A–B
edge and the B–C edge drag all three into one cell, yielding multiplicity 1
against the selection's 2. A rule that partitions is a rule that partitions. The
cell vocabulary is therefore gone, not repaired, and the policy reads the graph
through two separate channels:

> **Corroboration** comes only from a **selection** — a set of pairwise
> non-adjacent vertices. Its members are demonstrably independent of one another,
> which is exactly the licence to multiply.
>
> **Contestation** comes from **every** assessment, selected or not. A
> non-selected assessment contributes no corroboration in any direction; if its
> outcome opposes the selection's net direction it moves the result **toward**
> the prior, under the reduction below.

Non-selection is therefore not exclusion. `B` in the example above corroborates
nothing — it is a third probe of ground already covered by `A` and `C` — but if
it disagrees with them, that disagreement is not erased by its dependence. This
is the asymmetry the whole section turns on, applied one level down: dependence
may cost belief, never buy it.

**Contestation needs its own non-amplification rule, or it becomes the back door.**
"Every assessment contests" without a reduction lets a hundred dependent copies
of one contrary result depress belief a hundred times — corroboration by
duplication, arriving through the channel built to be immune to it. The channel
that grants no multiplicity must not confer it by subtraction either.

**But `max` over the contrary assessments is not the answer**, and the argument
for it does not survive contact with the graph. It ran: every non-selected
assessment is adjacent to something *selected*, so it adds nothing new. True —
and it says nothing about whether non-selected assessments are independent **of
each other**. They routinely are:

```text
supports   A = {x1, x2}      C = {y1, y2}
disputes   B = {x1, y1}      D = {x2, y2}
```

Every lineage here is complete and every pair is certified. `A—C` disjoint,
`B—D` disjoint, and each support–dispute pair overlaps. The only maximum
selections are `{A,C}` and `{B,D}`. Under `max`, whichever wins receives a single
unit of contestation from a genuinely two-fold independent objection, the two
candidates come out equal and opposite, and **the uid tie-break decides whether
the proposition is supported or refuted**. A lexicographic tiebreaker choosing
the sign of a belief is not a rounding error.

> **Reduction.** Contestation is a **single clamped move toward the prior**:
>
> - its magnitude is computed over the **contrary subgraph** — the non-selected
>   assessments opposing the selection's net direction, carrying their existing
>   dependency edges — by the **same exact maximum-independent-set enumerator**,
>   combined by the policy's ordinary rule. Dependent duplicates collapse
>   (a duplicate is adjacent to its original, so only one is selected);
>   independently corroborated objections combine;
> - among the maximum-cardinality contrary selections, take the one minimizing
>   **the outer candidate's final displacement** — *not* the contrary selection's
>   own displacement (see below);
> - it is **clamped at the prior**: contestation never crosses it, never flips
>   the result's direction, and does nothing when displacement is already zero.

One mechanism now serves both channels, which is the point: independence governs
multiplicity wherever multiplicity arises, and there is no second theory of
evidence hiding on the contrary side. On the example above, either candidate
selection meets two independent objections, both land at the prior, and the
tie-break no longer touches the sign.

**Reusing the enumerator is right; reusing its objective is not.** Stage (2)
minimizes *the selection's own* displacement, which on the contrary side selects
the **weakest** objection — and that is exploitable:

```text
supports  A = {x}      C = {y}          independent
disputes  B = {x, y}   strong
          D = {x, y}   weak, adjacent to everything
```

`{A,C}` is the unique maximum selection. The contrary subgraph `{B,D}` is a
clique, so cardinality ties at one, and a standalone displacement-minimizer picks
weak `D` over strong `B`. Contestation drops and **belief rises on the addition
of a disputing assessment** — violating the addition property, through the very
channel added to uphold it.

So the objective is inherited from the outer problem, not from the sub-problem:
both levels minimize **the same quantity, the final displacement**. The nesting
was the bug, not the reuse.

That also fixes what stage (2) evaluates: **the policy's complete result,
contestation included**. Scoring candidates on corroboration alone is what let
the sign hang on a uid comparison. There is no circularity — each outer candidate
determines its own net direction and contrary subgraph, its contrary selection is
resolved against that candidate's final result, and the candidates are then
compared.

> **Limitation — dependent contradiction can only neutralize, never overturn.**
> Selection is cardinality-first, so **strength never rescues a contrary
> assessment into the selection**: in `A—B—C`, two weak supporting assessments
> `{A,C}` beat one arbitrarily strong refuting `B`, every time. `B` can drive
> belief to the prior and no further.

This is a real cost, stated rather than hidden, and the alternative is worse:
letting a strong enough dependent assessment cross the prior would let evidence
that shares its opponent's lineage *assert* the opposite conclusion, which is the
thing the clamp exists to prevent. The route to overturning a proposition is an
**independent** refutation — the correct scientific answer, and one imposed by
**aggregation**, not by the eligibility gate. The gate (§4.1) asks only for held
observations and admitted verification; it has no view on independence at all.
Two mechanisms, two jobs: eligibility decides what may bear on belief,
aggregation decides what corroborates.

> **Choice of selection.** Lexicographic: (1) **maximum cardinality** — take as
> much demonstrated independence as the certificates support; (2) among those,
> **minimize displacement from the prior**; (3) canonical tie-break, by sorted
> member uid.

Maximizing first is what stops the minimization from choosing the empty
selection, whose displacement is trivially zero. The objective is joint and total,
so it has no ordering dependence, and stage (2) is stated against the policy's
own output, so it stays correct when the policy changes.

**The prior is a policy constant, and may not be the previous belief.** Both the
prior and the displacement metric are declared, versioned members of the belief
policy: a fixed neutral state and a distance on the belief scale. Reading "the
prior" from the last materialized belief would make identical closures yield
different results by history — and G3 forbids it *structurally*, because
recomputing it would require a digest member that does not exist. Because both
are policy constants, the **policy binding** already covers them in §5.1; no new
digest member is needed.

**All four of this section's policy citations are now defined** (added
2026-08-05, `2026-08-05-belief-policy-design.md`). The belief scale, the prior,
the displacement metric and "the policy's ordinary rule" were cited here as
declared, versioned members of a policy that did not exist. A policy now
declares a carrier `V`, a `prior ∈ V`, a `distance`, and the evaluator
`aggregate` — and the **identity fixture-binds `aggregate` end to end**, not a
decomposition of it, precisely because the selection, contestation, clamp,
candidate ordering and tie-break specified in this section all change belief: an
identity covering only the numeric primitives would let the behaviour above move
without any identity moving. `science.belief.v1` instantiates `V = ℤ` with unit
weight per directional assessment, so a belief value is a **signed evidence
balance** and never odds or a probability. It carries no weighting by study
design or precision, and that is a blocked term rather than a deferred one:
`estimand` is untyped and `uncertainty` is on the estimate's own scale, so no
dimensionless magnitude is computable without the typed reference and
commensuration contract ρO3 leaves open.

Minimizing *displacement* rather than the signed value is what makes the rule
symmetric: a confidently refuted proposition is a confident state too, so
uncertainty must not manufacture confidence at either pole.

"Attach to the greatest-weight cell" is retired with the cells. Any comparable
shortcut in the current log-odds policy is an optimization, valid only until the
policy changes, and is verified by an exhaustive oracle that enumerates every
selection on small graphs and asserts the shortcut picks the same one.

#### Exact only — no approximate selection

Maximum independent set is NP-hard in general and trivial at this scale (a
proposition's assessments number in the single digits). **The selection is
computed exactly, always.** No vertex bound, no greedy fallback, no `exact |
lower-bound` marker.

Two earlier answers are both rejected, and the second is the instructive one:

- **Refusing above a bound** converts a working belief state into an availability
  failure that anyone able to add assessments can trigger.
- **A greedy fallback** was justified here on the grounds that greedy can only
  understate multiplicity — which is true, and does not imply what it was used to
  imply. **A lower bound on cardinality is not a lower bound on belief.** Greedy
  picks a *different* selection, not a smaller version of the same one, and a
  different selection can be more one-sided.

  `a=support`, `b=support`, `c=dispute`, with the single edge `b—c`. The exact
  candidates `{a,b}` and `{a,c}` tie on cardinality, so stage (2) takes the
  balanced `{a,c}`. Add a later-sorting universal vertex to cross the bound and
  greedy takes `{a,b}` — the one-sided set. Contestation from `c` may reduce that
  result but is not guaranteed to reach the exact one. **Belief rises**, which is
  precisely what the fallback was introduced to make impossible.

This is the substrate design §8 discipline applied to compute rather than
storage: do not build a second mechanism for a ceiling no measurement has
demonstrated. If a real corpus ever produces a graph where exactness costs too
much, the replacement must be shown to preserve the belief-direction asymmetry —
the property greedy silently broke, and the reason a cardinality argument is not
enough on its own.

#### What the model guarantees against an added assessment

> **Property.** **Adding** an assessment certified independent of nothing can
> never **increase** multiplicity, and can never **increase** displacement.

**Addition only.** The symmetric claim about removal is false, and by the
mechanism the model is built on: a contrary universal assessment lowers
displacement through contestation, so deleting it *restores* the higher
displacement. That is not a defect — it is §3.2's deletion limit showing up on
schedule, and it is why the guarantees about deletion live there rather than
here. Stated as a two-way property it would be a false claim about tamper
resistance, which is the error G8 was narrowed for.

The multiplicity half holds because such a vertex is adjacent to every other, so
it enlarges no set of pairwise non-adjacent vertices and removes no edge among
the rest.

The second half needs a different argument, because the obvious one is false.
Such a vertex does **not** always sit outside the maximum selection: when the
graph is a clique the independence number is 1, every singleton is a maximum
selection, and the new vertex is a legitimate candidate. But stage (2) then
chooses among those singletons by **minimizing displacement**, so a newly
admissible candidate can only be taken when it displaces *less*. Displacement
falls or holds; it cannot rise. The guarantee survives; the non-membership
reasoning does not, and a clique case belongs in the tests to keep it honest.

`applicability` is where the estimand-match residue (§8.5) will eventually be
attacked: it is recorded here, and comparing it against the proposition's own
scope is the check this kernel makes *possible* but does not yet specify.

**Amended 2026-08-05 (belief-policy §5) — the blocker is now named, and it is
upstream of this kernel.** No belief policy reads `applicability` for value, and
none can yet emit a mismatch: `applicability` is untyped prose, not a qualifier
map, so the canonical map equality M5 pins does not apply to it, and ρO3 defines
no applicability-match predicate. The rule that would be *right* — narrower
evidence refutes a universal claim but cannot corroborate it, and the reverse for
an existential one — needs **term subsumption**, which domain-extension declines
to supply by design and which the formal model marks `scope` **"defective — no
order is defined"** for. Refusing on mismatch is separately rejected: it would
convert a working belief state into an availability failure anyone able to add an
assessment could trigger, which is the shape this section refuses above.

### 4.3 Outside the kernel

**Views** — `hypothesis` (a thin saved view over propositions: membership/query,
composition rule, scope, rationale; belief entirely derived), `theme`/`topic`,
`question`. `nodes` `docs/STANDARD.md` supplies no saved-view primitive
(§2 data model, §5 shapes, §9 derived indexes — no view concept), so a small
`hypothesis` entity is justified rather than a kernel omission.

**Content-addressed run artifacts** — `synthesis`, `report`, `validation-report`,
`chain-audit`, `curation-sweep`. They keep identity and provenance as artifacts;
they stop being epistemic entities. (Verification is **not** one of these — it is
a kernel kind, §3.3.)

**Notes** — belief-inert prose. A former `interpretation` resolves to exactly one
of: an inert note; a proposition; or the predeclared interpretation rule that
generated an assessment.

**Referents** — `term`, from `science_model/ontologies` (absorbs `concept`,
`construct`, `variable`, `outcome`).

**Coordination** — `task`, `decision`.

### 4.4 Complete accounting of the 50 core kinds

Listing a mapping invites the same hole this design argues against, so the
accounting is exhaustive rather than illustrative. Every current core kind
appears exactly once.

| Destination | Kinds |
|---|---|
| **Kernel (8; 10 since 2026-08-03; 11 since 2026-08-08; 12 since 2026-08-10; 13 since 2026-08-11)** | `proposition`, `source-assertion`*, `assessment`, `analysis-spec`*, `run`*, `verification`*, `dataset`, `source`* — plus `retraction` (correction-lifecycle), `instrument-certification` (normative-contract 5b §7.2), and `coreference-attestation` (world address ruling §5.1), then `holdings-observation` (verified-holdings record design §2, 2026-08-10) and `act-report` (act-report design §2, 2026-08-11), which absorb nothing |
| Absorbed into `assessment` | `evidence-line`, `finding`, `observation` |
| Absorbed into `proposition` | `mechanism` |
| Absorbed into `analysis-spec` (as fields/refs, not identity — see §11) | `pre-registration`, `plan`, `spec`, `method`, `assumption`, `falsification` |
| Absorbed into `run` | `workflow-run`, `transformation`; `workflow`, `workflow-step` become imported DAG structure; `code-file` is closure content, not an entity |
| Absorbed into `dataset` | `data-package`, `research-package` |
| Absorbed into `source` | `paper`, `article`, `book`, `talk`, `prose-source` |
| → **dataset provenance** (acquisition, not analysis) | `experiment` |
| **Views** | `hypothesis`, `question` (absorbs `research-question`), `theme`, `topic` |
| **Content-addressed run artifacts** | `synthesis`, `report`, `validation-report`, `chain-audit`, `curation-sweep`, `claim-registry` |
| **Notes** (belief-inert prose) | `interpretation`, `discussion`, `story` |
| **Referents** (`science_model/ontologies`) | `concept`, `construct`, `variable`, `outcome` |
| **Coordination** | `task`, `decision` |
| **Open — unplaced deliberately (§11)** | `inquiry`, `patch-definition`, `structural-chain`, `search` |
| **Deleted, no successor** | `unknown` |

`*` = new or renamed kind.

Totals: 50 current core kinds accounted for; 4 views, 6 artifacts, 3 notes,
4 referents, 2 coordination, 4 open, 1 deleted, the remainder absorbed. The
kernel is 8 kinds — 9 since `retraction` (correction-lifecycle design,
2026-08-03), 10 since `instrument-certification` (normative-contract design
5b §7.2, 2026-08-03), 11 since `coreference-attestation`
(`2026-08-08-world-address-ruling.md` §5.1) — each of which like `verification`
absorbs nothing — so the 50 map onto 7 of the original 8.

## 5. Guarantees, and how each is tested

Certified by **mutation**: break what the guard guards and watch it fail. A guard
that has never been observed failing is uncertified.

| # | Guarantee | Mutation test |
|---|---|---|
| **G1** | A source assertion cannot enter belief aggregation, by type | Author a source-assertion with every field maximal; assert belief output is byte-identical. Then attempt to author an `assesses` edge from it; assert refusal. |
| **G2a** | **Execution-boundary ordering.** The boundary refuses to begin a run that does not name an already-frozen analysis-spec identity, and records that identity before any other observation | Attempt to begin a run naming no frozen spec, and one naming a spec frozen mid-execution; assert both are **refused**, not downgraded. **Also assert the negative:** perform a run out of band, freeze a spec afterwards and attach it, and confirm the ordering is **undetectable** — G2a is a guarantee about what the boundary will start, never a proof about what happened outside it |
| **G2b** | An assessment requires held, content-hashed inputs | Point a run at an unheld or unhashed input; assert refusal |
| **G2c** | An assessment is admitted only in the **admitted** verification state | Walk every row of the §3.3 lifecycle table; assert admission only for `clean-environment, passed` with no active `failed`. Assert a passing sibling does **not** clear an active failure |
| **G3** | **Whenever a belief is produced**, that belief state names its **complete transitive input closure** (below), as one digest (arm restriction added 2026-08-05 — formal model ρA8) | Recompute from the named closure alone; assert identity. Then mutate **each** closure member in turn — including ones the old G3 omitted — and assert the digest changes every time. **Structure, not only content:** a member that is a *set* must be tested for what the set's own structure carries — **permute** the keyed facets across assessments and assert the digest changes, and **delete** a producing run so a lineage basis entry stops resolving and assert the same. **Reads, not descriptions:** **add** a second producing run to a dataset already in the closure, changing nothing else, and assert the digest changes — the divergence test reads the producer set, so the producer set is a closure member. **Scope, not only contents:** enumerate the producer sets from a snapshot covering **fewer corpora**, with every present corpus identical, and assert the digest changes — an enumeration is bounded by what it consulted. **Negative — location is not evidence:** move an entity between corpora; assert the digest is **unchanged** (world W5), pinning that the member is the **producer snapshot** and not the world index that carries it. *(The alias arm was deleted 2026-08-08 with the alias itself — labels are rendered, never stored, so there is nothing to edit. Not replaced: location already tests OInv here, G7 tests display invariance, and an authority-release bump is **not** a substitute, since a consulted release may legitimately move the digest under D6.)* All four were live holes in earlier revisions, and none is reached by mutating a member's value |
| **G4** | A **recorded** failed replay cannot be silently orphaned (narrowed — §3.2) | Attempt an unreferenced successor to a recorded failure; assert refusal. **Also assert the negative:** discard the failed attempt entirely and confirm the system *cannot* detect it — the test pins the limit so no reader over-reads G4 |
| **G5** | Divergence is computed, never authored | Attempt to author a divergence record; assert no such kind exists |
| **G6** | `reads` inputs never confer eligibility | Build a run whose only inputs are a literature corpus and an ontology; assert no assessment is admissible regardless of quantity or QA state |
| **G7** | A semantic edit to a proposition cannot retarget existing evidence | Edit a proposition's scope in place; assert a new semantic identity is minted, that prior assessments still bind the old one, and that belief on the old identity is unchanged. **Also assert the converse, in both prose forms** (second form added 2026-08-05, ρA1/ρA2): overwrite `title` alone, and separately overwrite `display_statement` alone, and assert in each case *no* mint, no new node, and an unchanged digest — pinning that the split of §4.1 is real in both directions and that display edits stay free. The positive arm is unchanged and **strengthens** under the typed projection: it forked identity only when prose moved the hash, and now forks whenever a typed field differs |
| **G8** | A later failing verification forces recomputation and, **while recorded**, clears only by explicit resolution **or a standing retraction** (bounded — §3.3, amended by correction-lifecycle §7a) | Attach a failing verification to an admitted assessment; assert invalidation and recomputation of every touched proposition. Assert it is **not** cleared by recency or by a passing sibling, **and is cleared by a standing retraction** (correction-lifecycle C6). **Also assert the negative:** delete the failing verification and confirm the assessment returns to admitted — pinning that deletion is §3.2's undetectable-history limit, not a tamper-evidence claim |
| **G9** | A dataset reaches **held** only when **every** resource its declaration names has a byte observation matching the digest recorded for it — declaration does not promote, presence does not promote, a proper subset does not promote (added 2026-08-09, admission ramp §6.3) | **Declaration does not promote:** author a dataset carrying a content identity and no bytes; assert it is **minted** as a world entity (world W3, as narrowed), that it reads **`declared`**, and that G2b refuses it as an assessment input. Assert **no API accepts an authored `held`** and that the state is **derived, never stored** — nothing on the record changes when bytes arrive or leave. **Presence does not promote:** supply bytes whose digest **differs** from the recorded digest for that resource; assert the dataset stays `declared`, that the mismatch is **reported as a mismatch** and not as a failure to retrieve, and that no path promotes on the strength of the bytes existing. **A proper subset does not promote:** over a dataset declaring **three** resources, supply matching bytes for **two** and assert it is still `declared`; supply the third and assert `held`. Then remove one and assert it returns to `declared`. An implementation quantifying **existentially** passes every other arm of this row and fails here, which is the arm's whole job — the declaration is the identity (admission ramp §6.2), so heldness is quantified over the same declaration. **Negative — location is not the discriminator:** hold matching bytes **outside the repository**, content-addressed and retrievable, and assert **`held`** all the same (§2.2), so the row is never read as requiring local storage; then make them unreachable *here* while a controlled copy remains held and assert R5's answer is unchanged. **Negative — absence in one coverage is not absence:** assert that observing no matching bytes across a **declared coverage** yields *no matching observation in that coverage* and **not** `unheld` — the `fb-2026-07-27-010` error the coreference ruling refused, reached from the holding side. **Negative — this row is about the upward transition only:** assert it says nothing about *losing* heldness, which is R5's negative (a). **Sabotage, asserted for independence:** install *the declared path exists* as the promotion predicate; assert **G9 fails while G2b, R5 and R10 all pass** — G2b consumes heldness rather than establishing it, R5 tests the downward transition, and R10 refuses a URL-valued input without saying what acquisition must verify, so an unverified promotion is invisible to every one of them |

Each row must be a failing test before it is a passing one. G4's negative half is
deliberate: a guarantee whose limit is untested will be read as the strong claim.

**G9 (added 2026-08-09) is the first row appended to this table since it was
frozen, and it exists because nothing here established heldness.** §2.2 defines
*held*; G2b **consumes** it. An implementation that promoted a dataset on the
strength of a declared path existing would pass every other row in this corpus
while voiding content-addressing entirely, which is the independently
sabotage-able property the admission ramp's §6.3 requires before a row is added.
Its companion amendment is world W3's dataset arm, narrowed the same day so that
a content-addressed dataset whose bytes are unheld is a world entity at all.

**G3's arm restriction (added 2026-08-05, formal model ρA8) narrows the
statement and preserves every test.** Asking for a belief has three possible
answers, not one: a belief, *not available*, or a refusal. The closure digest
determines the **first**; whether that arm is reached at all is decided by
eligibility and by whether the inputs are still **held** — and held-ness is not a
closure member, because it selects the answer's *shape* rather than its *value*.
Stated without the restriction, G3 was falsifiable by a case it never intended to
cover: two configurations differing only in whether the last held copy of an
`observes` input survives share one `belief_input_digest` while yielding
different answers. That is not a qualifier on G3 — under the unrestricted
phrasing it is a G3 violation. R5 already tests the held-ness case, unchanged,
and no G3 arm moves.

**The three answers are now a type** (added 2026-08-05, belief-policy §4):
`Belief(value, belief_input_digest, policy_binding) | NoBelief(reason) |
Refused(reason)`. Three top-level arms, as this section already required;
reasons are discriminants **within** an arm and never a fourth answer. The
digest accompanies the `Belief` arm alone, which is what ρA8's restriction
above amounts to once the arms are named. Two boundaries that were previously
unstated are fixed there and are easy to get backwards: an empty eligible set is
**`NoBelief(NoEligibleAssessment)`** and not an unavailability, because the
computation succeeded and found nothing rather than failing to run; and a
policy implementation that **fails its fixtures refuses**, unlike W8a's
unresolvable reading, because an exact binding names the implementation and no
installation can repair a binding that is false.

**G2a is a guarantee about the execution boundary, not about chronology, and
sub-problem 4 is where that surfaced.** A content hash proves content **equality,
not chronology**: a spec hash computed today is byte-identical to one that would
have been computed a year ago. So "requires a hash predating the run" is not
something any hash can establish, and phrasing it that way while its own negative
test proves post-hoc attachment undetectable was a contradiction inside one row.

What *is* enforceable is stated above: the boundary will not **begin** a run without
an already-frozen spec identity, and it records that identity first. Ordering
therefore holds over what the boundary recorded, and the boundary's record is itself
rewritable. The strong claim requires the tamper-evident mutation log of §8.7
(designed 2026-08-03, `2026-08-03-tamper-evident-log-design.md`), and is listed
there rather than asserted here. That log strengthens the claim for
**boundary-mediated** executions only — an intent entry durably appended before
execution begins — so the negative in G2a's row stands unchanged: a run
performed out of band never passes the boundary, and freezing a spec afterwards
remains undetectable.

### 5.1 The belief input closure (G3)

Naming assessments is not sufficient. Admission depends on verification state,
and independence is derived from dataset lineage — both of which can change while
the named assessment set stays fixed, so the same set could yield different
belief. G3 therefore pins the **transitive semantic closure**, reduced to a single
`belief_input_digest` over:

| member | why it must be in the digest |
|---|---|
| **keyed assessment facets** — sorted `(assessment identity, canonical facet digest)` pairs | the facet values belief reads, **bound to the assessment that carries them**. **Amended twice by sub-problem 4 §5.1.** It first said "assessment revisions" while the facet was authored; a correction replaced that with bare *identities*, which lost the property the word "revisions" was carrying — an assessment's identity is `(spec, run, proposition)`, so a raw-written record whose `outcome` reads `supported` where the derivation yields `refuted` occupies the same address and produced the **same digest as the correct belief state**. The second correction, to bare facet **digests**, fixed that and lost the other half: a bag of digests is **permutation-invariant**, so exchanging the facets of two assessments — one supporting, one disputing, with different runs, lineage and independence roles — leaves the digest unmoved while moving belief. Neither the key nor the value is sufficient alone; the digest covers the **pairing**. Canonicalized under `science.identity.v1` (sub-problem 4 §4.3), which is what makes "sorted pairs" a determined byte string rather than a convention. No revision lifecycle returns — the facet is derived and immutable |
| proposition semantic identities | what is being believed (§4.1) |
| **active verification nodes** `(scope, verdict, supersession state)` | determines admission; changes without touching the assessment |
| **`observes` dataset content identities** | the actual bytes assessed |
| **dataset lineage snapshot** (defined below) | independence is derived from ancestry, which is mutable |
| **retraction enumeration per closure member** — the found retraction refs, their resolutions, and the coverage declaration the enumeration ran under (added 2026-08-03, correction-lifecycle §6) | standing is computed at read time, so a corpus with a standing retraction and one without must hash differently; the exact corpus states the enumeration ran at are receipt material, never digest members (world §5's semantic-snapshot/receipt split) |
| **policy binding** — `(policy rule identity, implementation content identity)` (amended 2026-08-05, belief-policy §2.2) | the aggregation rule, bound to the exact implementation that ran it. It read *"belief policy version — the aggregation rule"* while the policy was undesigned, which left the member that determines the **value** as the last bare version string in this table: 5b §6 rules that finite fixtures cannot force two conforming implementations to agree outside those fixtures, so two of them could produce different values behind one digest — repro §3.1b's *"versioning a symbol is not versioning behaviour"*, applied to the one rule whose output **is** the belief. World W8a already returns `malformed` for a rule reference that is a bare version string with no fixture binding. The binding is a **required argument** to the computation, with no default and no implicit "latest", for the reason the producer-snapshot member states: any of those would make belief follow the checkout |
| **consulted profile contracts** — exactly one `science_contract` **unconditionally**, plus each domain contract whose namespaced facets the derivation actually reads (added 2026-08-04, domain-extension-boundary §8) | the rules by which the derivation *interprets* what it read. A successor contract can reinterpret a facet, a kernel kind, or a relation signature without changing one byte of facet or assessment content; without this member the same digest would stand for two different beliefs, which is what this table exists to forbid. The base contract is unconditional because interpreting `assessment`, `dataset`, or `assesses` **is** consulting it — a facet-triggered rule would miss exactly the load-bearing case. Activated-but-unread domains stay out: belief moves when the rules it used move. Cross-corpus closures must agree on every consulted identity, which is what preserves W5 (domain-extension-boundary §8.1) |

A belief state that cannot be recomputed byte-identically from **the closure this
digest names** is a defect, not a drift. It read *"from its digest alone"* until
2026-08-05; a digest is a hash and nothing is recomputable from one, and G3's own
test arm always said the recomputation runs *"from the named closure alone"*. The
looser phrasing was found while designing the belief policy, whose P7 makes the
same claim about the evaluator (belief-policy §7).

**Keying is also what puts run identity in the digest at all.** An assessment
identity is `(spec, run, proposition)`, so the first member now carries the run
address of every assessment on the proposition — and a run's address moves with
its recipe (sub-problem 4 §4.2, R2). Anything frozen into a recipe is therefore in
G3's reach, which is what sub-problem 4 §5.2's inline exclusion certification
relies on: withdraw or add a certification and the recipe, the run, the assessment
identity and this digest all move, **even when the facet values are byte-identical**.
Under facet digests alone that claim was simply false — there was no run or
assessment identity anywhere in the digest to carry it.

**The lineage snapshot is content, not a gesture.** "Ancestry" is too abstract to
satisfy that requirement, and the abstraction hides a live failure: deleting an
ancestor changes how a reference *resolves* without changing what is *stored on
disk*. A digest over stored records alone would be identical before and after, and
independence would silently stop being recomputable. The snapshot is therefore:

| component | content |
|---|---|
| observed roots | the `observes` dataset refs themselves, sorted — **including** roots whose own basis names nothing |
| lineage basis tuples | for every dataset in the inspected set, its stamped **lineage basis** (sub-problem 4 §5.2) — a tagged `single(route) \| conflict([route])`, with the **tag inside the digest**, each route contributing `(dataset uid, stored producing-run ref, resolved run uid or null, stored ancestor ref, resolved ancestor uid or null)` and a `conflict`'s routes sorted |
| **producer sets** | for every dataset in the inspected set, the sorted refs of **every** run holding a `produces` edge to it, each with its resolution — the input to the `lineage-divergent` test |
| **divergence states** | the derived per-dataset outcome of that test |
| **producer-snapshot identity** | the **semantic** identity of the world §5 producer snapshot **this computation was given** — the identity is a **required argument** to the computation, with no default, no implicit "latest" and no stored selector, since any of those would make belief follow the checkout: the **producers map plus the stable identities of the covered corpora** — each the corpus's minted opaque `corpus_id` (world §5), never its path, directory name or project. *Not* the world index as a whole, and *not* the snapshot's derivation receipt, which is a separate record: the exact corpus-state identities it was built from live outside this digest, because both change on a move that W5 requires to be epistemically silent |

The **stored ref and its resolution are both recorded, and separately**. That
pair is what makes a deletion visible in the digest: the stored ref is unchanged,
the resolution flips to `null`, the digest moves, and the belief state is
correctly invalidated. Recording either alone loses the deletion.

**It is now recorded for the run as well as the ancestor, and that is the newer
half.** Sub-problem 4 §5.2 makes `derived_from` a **view** over the runs'
`produces ∘ transforms`, and a view has nothing on disk to go stale: deleting the
producing run removes both edges at once, leaving a dataset that resolves to *no*
ancestry and reads as a root — buying disjointness rather than losing it. The
stamped basis is the durable descendant-side record that survives the run's
deletion, and this snapshot digests its resolution, so the deletion moves the digest
in exactly the way an ancestor's deletion already did.

**The last two members exist because the snapshot must digest what aggregation
reads, not what the design finds most natural to name.** A first version of this
table digested the basis alone while independence *also* consulted every other run
producing the dataset — to decide whether the basis is divergent. Adding a second
producer therefore changed ancestry, and potentially belief, while no assessment
identity, observed content or verification state moved: the digest stayed identical
across a real change in belief inputs, which is precisely what G3 forbids. The rule
that generalizes it: **enumerate the reads of the aggregation function, then digest
that set** — a member is in the closure because something reads it, never because it
is the tidiest description of the lineage.

**The last member is there because a set can be incomplete as well as wrong.** The
producer set is a **reverse** adjacency question — which runs point at this dataset —
and the answer depends on how much of the world was consulted: producers live in
corpora that need not contain the dataset and need not be present. Digesting the set
without the snapshot it came from would give the same digest to an enumeration over one
corpus and over forty, and independence certified from the smaller one is certified
from an unbounded absence. So the **producer snapshot's** identity, including its
coverage declaration, is a belief input, and world §5's index stops being a publication
convenience: an enumeration is only as good as its stated scope, and the scope has to
be part of the record.

**The producer snapshot, and not the world index.** A first version of this member
named the index entire — address map, alias map and coverage together — which
contradicts world W5 outright: moving an entity between corpora changes the address
map, and W5 requires a move to leave this digest **unchanged**, because location is not
evidence. *(The alias map retired 2026-08-08 with the stored alias, `2026-08-08-world-address-ruling.md`
§4.3; the argument stands on the address map alone, and one fewer map is one fewer way
to reach it.)* The rule the slip broke is one this design
states elsewhere in its own words: **a digest member is the thing that is read, not the
artifact it arrived in.** Belief reads the producer enumeration and its scope; it does
not read where anything is filed.

Nor does hashing the snapshot make it complete. An identity over a map with an entry
deleted faithfully names the smaller map, and the belief that certifies independence
from it is wrong in a way no digest can see. Completeness comes from the snapshot being
**recomputable** — world §5 binds it to a **derivation receipt**, a separate immutable
record directed at the snapshot carrying the exact corpus-state identities **and the
identity of the enumeration rule that read them**, and to the same import/audit
discipline as the assessment facet and the verification, so "this is what the corpora
say" is checkable rather than asserted. The rule is in the receipt and not in this digest
for the same reason the states are not: belief reads **what was enumerated**, so two
rules producing one map over one coverage are one belief input. **Checkable is not permanent:** a
receipt **names** its inputs rather than holding them, so it can be validated only while
it is `resolvable` in world §5's sense — **each** covered corpus standing at its own
recorded state, and the enumeration rule still held — asked only of a receipt that is
**`well_formed`** against the snapshot it is directed at, since a receipt covering a
smaller set than the snapshot declared would certify completeness over a set it chose
itself. And a refuted snapshot is corrected
by **publishing a right
one that a later computation names** — not by retiring the wrong one, and not by moving
any stored selector, since the snapshot identity is an **argument** to this digest rather
than a setting (world limitations 10 and 11). G3's
contract is that equal digests mean equal belief inputs; it was never a contract that
the inputs are true.

**And the receipt stays out of this digest**, which is the other half of the same
lesson. Exact corpus-state identities are what an audit rebuilds against — **while
corpora still stand at them** — and they move whenever a file moves, so folding them in
would restore the W5 violation the paragraph above just removed, by the door marked *completeness* instead of the one marked *packaging*. A
member is chosen by what the aggregation **reads**; recomputability is a property the
member must **have**, and the two are not satisfied by the same bytes.

## 6. Divergence

Belief and divergence are **computed views, not entities**.

Divergence compares aggregated source assertions against aggregated assessments
on the same proposition.

**The discourse axis is quantitative.** For a proposition it is a tuple —
`(n_assert, n_deny, n_hypothesize, coverage, recall)` — never a magnitude and
never a single categorical label. Real corpora routinely contain both assertions
and denials, so any collapse to "the corpus asserts P" is a classification, and a
classification needs a declared rule.

> Any categorical reading of the discourse axis is produced by a **versioned,
> declared classification rule** with an explicit **mixed** outcome. The word
> *consensus* may not be used unless that rule's criterion is stated. Absent a
> declared rule, only the tuple is reported.

Under such a rule the surface is:

|  | corpus: predominantly asserts | corpus: **mixed** | corpus: not observed | corpus: predominantly denies |
|---|---|---|---|---|
| **assessed: supported** | corroborated | ★ we side with one camp | ★ candidate novel | ★★ we say yes, they say no |
| **unassessed** | *untested community claim — the default, and most of the graph* | open controversy | unknown | untested |
| **assessed: refuted** | ★★ they say yes, we say no | ★ we side with one camp | negative result | corroborated (negative) |

The starred cells are the product: where robust data and community claims part
company. Making them a computed surface rather than something a human notices is
the main capability this kernel adds that the current system cannot express.

The **mixed** column is not a rounding artifact to be eliminated — an unassessed
proposition with a genuinely split corpus is the highest-value entry in the work
queue of §8.1.

**"Not observed in corpus" is not "silent."** Both the novelty and the
disagreement cells require a **declared corpus coverage** (source, query, date
bound) and a **measured extraction recall** against a labeled sample. Without
both, an empty cell means "we didn't look," and a novelty claim is unearned.

Discourse aggregation yields **counts and coverage, never belief**: "14 of 17
papers in the declared corpus assert P; extraction recall 0.82" is a measurement.
Assigning it a magnitude would rebuild `STANCE_EMIT` by other means.

## 7. Deletions

- **`EvidenceType` entirely** — `{empirical_data, benchmark, simulation,
  literature, expert_judgment, negative_result}`. Every value is either a
  forbidden route (`literature`, `expert_judgment` → source assertion or note),
  implied by the route (`empirical_data`), an input role (`simulation`,
  `benchmark`), or an outcome (`negative_result`). Nothing remains. This is the
  vocabulary that made the original category error expressible.
- **`STANCE_EMIT`, `emit_literature_evidence`, `_belief_for_units`**, the
  unconditional independence tag, and the `evidence-line/` URI stem in
  `cross_paper_evidence.py`. The scanner, source resolution and dedup
  (`scan_literature_assertions`, `collapse_assertions`) are kept; the module
  becomes `source_assertions`.
- **`authored_only_ceiling`** as a permission for expert judgment.
- The `literature_evidence` finding grade.

Simulation needs no evidence-type loophole. But note what the eligibility
predicate (§4.1) implies, because it is stricter than "not about nature
directly": a pure simulation run has **no `observes` input**, so it cannot
satisfy the predicate at all.

> **Ruling for this kernel: simulation produces run artifacts and no assessment.**
> It bears on nothing until a derivation route exists.

Claims about a simulator, an algorithm, or a model-conditional world are
therefore in exactly the same position as mathematical and structural claims —
they need the second, non-empirical route left open in §11, and they do not get a
partial one here. A simulation that *is* compared against held observations is a
different case: that run has an `observes` input and is admissible on the
ordinary terms.

## 8. Limitations

1. **Throughput is bounded by reanalysis capacity.** Belief is sparse by
   construction and the unassessed row stays wide. The system must therefore be
   useful while almost entirely unassessed: the daily surface cannot be belief.
   The discourse side carries that load — widely-asserted-but-unassessed
   propositions are the ranked work queue (divergence-in-waiting).
2. **We reproduce the analysis, never the acquisition.** GEO series and
   access-controlled cohorts cannot be re-measured. Eligibility is possession +
   closure of the *analysis*; acquisition lives in dataset provenance. Stated
   explicitly so "reproduced" is not read as "re-measured".
3. **Extraction is a fallible computation.** Discourse claims rest on extraction
   that is re-runnable but not correct. meta `t030` D4 measured two
   verbatim-identical blind passes disagreeing on **25–40% of rubric-ambiguous
   fields**, with systematic pass-1-higher drift. Extraction reliability needs
   its own accounting.
4. **One-sided referent binding is still hard** (amended 2026-08-05 — formal
   model ρA5, ρO1). The **vocabulary half is answered.** Predicates become
   **operators**, declared by a domain contract like any other vocabulary, with
   term identity, an issue-and-retire rule, and *never redefine* enforced at
   contract load against a declared predecessor (formal model §7.1, §7.3, §7.3a;
   M6, M7). The closed nine-term enum is retired, and no second authored
   operator roster may exist beside the contracts.
   **The binding half stays open, and is now stated precisely** rather than
   impressionistically. Decoding a claim resolves each argument against its
   sort's bound vocabulary and yields one of five outcomes (D §5 as amended);
   what is unsettled is whether that check's receipt **persists**, how it would
   be discovered or superseded, whether an unchecked claim may be assessed, and
   what corrects a claim later found `not-member` (formal model ρO1). The banked
   correction rules make the obvious path unspellable — C §4's eligible-target
   set is exactly `node` and `route`, a proposition is not retraction-eligible,
   and 5b §7.6's audit mints nothing — so the answer is either a lifecycle
   design or promotion to an independently addressed record, which is a new kind
   with its own eligibility analysis. It is recorded as open here rather than
   deleted.
5. **The estimand-match residue is not solved here.** Making extraction a
   provenanced computation forces an estimand to be *recorded*. It does not force
   it to *match* the claim it is used for. That is the largest surviving piece of
   the ten-item scope cluster and it needs its own treatment.

   **Amended 2026-08-05 (belief-policy §5) — unchanged in substance, and its
   blocker is now named.** The residue is not waiting on effort. It is waiting on
   a **typed reference and a commensuration contract** that no artifact yet owns:
   `estimand` appears in this document exactly once, as prose, with no value set
   declared for any of its four components, and `applicability` is prose too.
   Which artifact should supply them — the claim operator, the estimand, or the
   interpretation rule — is ρO3's neighbourhood, and a typed endpoint alone would
   not settle it, since a noninferiority margin is not determined by an endpoint.
   The same gap is what forces `science.belief.v1` to weight every directional
   assessment equally, so this limitation and belief-policy limitation 1 are one
   limitation reached from two directions.
6. **"Data doesn't lie" has practical limits** beyond fabrication — QA failures,
   batch effects, analytic degrees of freedom. This is why pre-declared
   interpretation rules and estimator certification must survive the rebuild
   rather than be simplified away.
7. **Recorded-history completeness** (cited here and in the companion designs as
   **§8.7**) — one named architectural limitation, not three local caveats. Every
   guarantee in this kernel that depends on the past holds only over what remains
   *recorded*:

   | consequence | undetectable action |
   |---|---|
   | **G4** (§3.2) | discarding a failed replay attempt |
   | **G8** (§3.3) | deleting a failing verification |
   | **semantic-identity enforcement** (§4.1) | hand-editing a proposition's semantic fields *and* its stored hash together |
   | **G2a ordering** (§5; sub-problem 4 §3.3) | freezing a spec *after* an out-of-band execution and attaching it |
   | **standing subtraction** (correction-lifecycle §4) | deleting a retraction record, silently restoring its target's standing |

   These are **five** consequences of one missing substrate capability, not five
   separate defects. A node's content-immutability does not make it undeletable, a
   write-boundary rule cannot see a state it was never shown, and a content hash
   proves equality rather than chronology. The fourth row was added by sub-problem
   4, which found the ordering claim resting on nothing enforceable; the fifth by
   the correction-lifecycle design (5a), which states it on arrival (its
   limitation 1) rather than claiming to close anything here.

   Its eventual owner is `atoms`. But the requirement is **stricter than
   crash recovery**, and must be stated as such before that wiring is designed: an
   ordinary recovery journal is not automatically tamper evidence, because the
   journal itself can be removed. Closing this limitation requires both
   **pre-mutation durable registration** and **detectable journal removal**.
   Whichever design takes it on inherits that contract, not merely "use the
   journal." Its first question is anchor placement: removal detection needs an
   anchor outside the deletable set, and the separately-publishable world index is
   the natural carrier (reproducibility §9, amendment of 2026-08-03).

   **Designed 2026-08-03** (`2026-08-03-tamper-evident-log-design.md`): the four
   recorded-mutation consequences — G4, G8, semantic identity, and 5a's standing
   subtraction — close at implementation, with that design's L1–L13 passing
   against the `atoms`-backed executor; the **G2a-ordering row strengthens for
   boundary-mediated executions only**, and out-of-band chronology remains open
   (its limitation 5).

   **Three of the four closed 2026-08-23**, at the discharge of conformance
   cut 8 by world-index slice 3 (`2026-08-22-log-verification-design.md`;
   results at `../plans/2026-08-22-conformance-cut-8-results.md`), merged
   into `main` on 2026-08-23 with `--no-ff` (`10cc84b`). **G8**, **semantic
   identity** and **5a's standing subtraction** are each a removal or rewrite
   inside the registered surface, and the log's replay refutes each against a
   surviving anchor — the removal itself additionally named in a policy finding,
   with the *failing*-verification classification resolving only where the
   caller supplies the historical bytes. **G4 has not closed**: discarding a
   failed replay attempt is an intent-qualification question, qualification is
   marked unevaluated in every report that slice produces, and it waits on the
   intent-boundary slice. **The G2a-ordering row is unchanged** — its
   strengthening stays boundary-mediated, exactly as banked, and the
   out-of-band negative stands. Detection is quantified over surviving
   observers throughout: destruction of a root together with every anchor
   holding it is not detectable from nothing.

   The three closures are about **detectability**, which is what this
   limitation is about. The separate derived-answer negatives — a deleted
   failing verification stops invalidating, a discarded replay stops being
   consulted — are facts about how belief is computed from what remains, and
   neither this limitation nor that design ever claimed to change them.

   G4 and G8 each carry a negative test pinning the current limit so neither is
   read as the strong claim; semantic-identity enforcement carries the same bound
   in the substrate design.
8. **The acquisition boundary is authored.** Eligibility rests on a dataset's
   empirical-observation facet and its declared boundary (§4.1). Whether that
   declaration is honest is outside the guarantee — the same class of limit as
   (2), and the reason dataset QA stays load-bearing.

## 9. Backlog consequences

- **`t080`** ("reproduction verdict as a belief ceiling — mirror the dataset-QA
  ceiling") — premise rejected by §3. Reproduction is admission, not a ceiling.
- **`t078`** — its verdict tokens `(unverified, self-consistent,
  independently-reproduced, failed)` survive, but **as a derived reading of the
  verification node's `(scope, verdict)`**, not as a stored enum (§3.3). Their
  belief ceiling does not survive. Its open tolerance question is resolved by
  §3.1 (predeclared equivalence rule, fixed by spec hash); its seeded-subsample
  question is resolved by demotion to a machinery smoke test.
- **`t016`** (derived qualitative standing) and **`t085`** (norm-to-check
  conversion) should be re-read against §4.1: several norms become unspellable
  rather than checked.

## 10. Not in scope — the remaining six sub-problems

This document is sub-problem 1. Each of the following gets its own design.

> **Where they stand** (*added 2026-08-08; the ledger is the authority, this is a
> pointer*). Sub-problems 2, 3 and 4 banked 2026-08-02, and 5 banked 2026-08-03 —
> split into **5a**, the correction lifecycle, and **5b**, the normative contract
> and its oracles, in that order and for the reasons the ledger's §2 records.
> **Sub-problems 6 and 7 are undesigned**, and 6 — the agentic surface, carrying
> audit liveness and the divergence table — is the corpus's largest structural
> deferral (disposition record, open question 5). **Seven later designs have no
> number in this list at all** and carry a guarantee table each — world-index
> packaging (X), the mutation log (L), the domain-extension boundary (D), the
> formal model and claim calculus (M), the belief policy (P), the
> verified-holdings record (H) *(amended 2026-08-10, the verified-holdings
> record design §8)*, and the act-report (T) *(amended 2026-08-11, the
> act-report design §7)*. Six numbered sub-problems plus those seven is where
> the thirteen frozen tables come from; the list below was never the whole
> roadmap.

2. **Substrate consolidation** — Science as a `nodes` profile over `atoms`.
3. **World & addressing** — one addressable space; project = view. `h00` already
   rules that "all projects live in one world" and records the current split as a
   known limitation; `t068` tracks the gap.
4. **Computation & reproducibility** — content-addressing primary; workflow DAGs
   imported, not authored.
5. **Guarantees & verification** — a versioned normative contract with
   conformance oracles (the `nodes` `STANDARD.md` §11–§12 shape) in place of the
   predecessor's 63 check modules.
6. **Agentic surface** — human+agent and autonomous curation; the ratchet
   (`t101`).
7. **Salvage** — pipelines, notes, bibliographies and results survive; all
   suspect until re-situated.

## 11. Open questions

- **`inquiry` / `patch-definition` / `structural-chain`** are unplaced. They are
  structured sets of propositions plus assumptions, so they are either one
  kernel-adjacent "model/patch" kind or a view over the kernel. `h00` makes
  patches load-bearing; they are left unplaced rather than dissolved by accident.
- **`search`** is the candidate home for the declared corpus-coverage record §6
  requires.
- **Non-empirical propositions — now the single largest open question**, because
  §7 rules that pure simulation also lands here. The invariant governs *empirical*
  belief; `ClaimLayer` carries `structural_claim`; math, derivation, algorithm and
  model-conditional claims have no `observes` input and so cannot produce an
  assessment at all. They need a second route (proof / derivation / simulation)
  designed on the same terms — its own eligibility predicate and its own
  guarantees — or an explicit ruling that they stay outside belief entirely.
  Leaving this open is a deliberate choice, not an omission: a partial route
  bolted onto the empirical one is how `EvidenceType` acquired `simulation` and
  `expert_judgment` in the first place.
- **`plan`, `method`, `assumption`, `falsification`** become fields or referenced
  artifacts inside the analysis spec, but are not semantically identical to each
  other and should not be collapsed into one field by default.
- **Formal pre-registration.** Science can guarantee pre-*run* fixation. Claiming
  something is *pre-registered* additionally requires evidence it preceded data
  access — ideally an external timestamp. The two must not be conflated in the
  user-facing vocabulary.
- **The empirical-observation facet** (§4.1) needs its own contract: what
  declares an acquisition boundary, and what distinguishes a dataset that carries
  the facet from one that merely claims it. This is the hinge the whole
  eligibility predicate turns on, so it cannot stay informal for long.
- **Semantic-identity normalization** (§4.1) — **closed for prose 2026-08-05**
  (formal model ρA1), **narrowed to term synonyms**. The hash no longer covers a
  statement, so whitespace, casing and numeric formatting have nothing to
  normalize, and the too-loose/too-tight dilemma dissolves for them: a typo
  cannot fork an identity because a typo cannot reach one. What survives is
  **term-synonym resolution** — two argument referents naming the same entity
  under different ontology identifiers project differently and so hash
  differently. That question is **relocated, not answered**: it is a
  vocabulary-binding question (D §5), where it is open.
- **Independence from dataset lineage** (§4.2.1) requires dataset provenance to
  record ancestry deeply enough to find common ancestors. Whether current dataset
  provenance can support that is unverified, and it is a dependency on
  sub-problem 4.
- **The discourse classification rule** (§6) — who declares it, where it is
  versioned, and whether one rule serves all propositions or it is per-view.
