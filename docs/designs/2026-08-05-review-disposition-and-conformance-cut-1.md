# External review disposition, and conformance cut 1

**Status.** Draft 2026-08-05; **cut 1's slice was built and merged 2026-08-07**
(`f81d3a3`), and §5's dated subsections record what building it found — the
freeze below is unamended. Disposes of an external review of the eleven banked
designs. Sizes formal-model **limitation 4** against the mm30 corpus under a
stated manual protocol (§2). Freezes **conformance cut 1** (§5) *before* any
implementation. Amends nothing in the banked corpus — every finding that would
amend lands as a disposition row naming its target, and the three proposed cuts
are docketed for re-litigation (§4), not decided here.

---

> **Status amendment 2026-08-17.** `atoms` A8 landed; the live prerequisite
> descriptions below now name composition-root adoption alone. This changes no
> frozen selection. Original prerequisite text, preserved verbatim:
>
> - Every L row remains gated on unbuilt `atoms` A8 and composition-root
>   adoption. A7's engine half landed 2026-08-14, but no Science L row moves, so
>   nothing is unblocked by deciding this sooner and nothing is lost by deciding
>   it later.
>
> | tamper log | L1–L13 | 13 | `atoms` A8, composition-root adoption (and §4.2) |

## 1. Method and standing

The review arrived as prose. This document keeps only what was checked, and
records what the check found — including where it found the review understated
or mis-measured its own case.

**What was verified against the tree.**

| claim | verdict | measured |
|---|---|---|
| the corpus is specification with no execution | **true of `science` only**, and true until 2026-08-07 | 11,953 lines across eleven designs + README; no source, no test, no build manifest. `nodes` is released (0.1.1, dual-language, parity-tested) and `atoms` is real through A5b, so the *lower* end is not spec-only. *(The verdict expired by being acted on: cut 1's slice landed 2026-08-07 and `science` now carries source, tests and a build manifest. `atoms` is through A6 as of 2026-08-08. The row is kept at its date — it is the measurement that motivated the slice.)* |
| 126 guarantee rows across ten frozen tables | **exact** | G 10, S 9, W 16, R 23, C 10, X 12, N 10, L 13, D 10, M 13 = 126 |
| mm30 propositions are bimodal, most machine-generated | **understated** | 307 of 334 (92%) are three-token stubs, not "five in six" |
| the stub predicate set is a small closed enum | **true** | eight terms: `affects` 224, `associates_with` 50, `induces_state` 12, `regulates` 9, `is_proxy_for` 5, `part_of` 4, `subtype_of` 2, `binds` 1 |
| datasets carry almost no content hash | **understated** | 0 of 259 mm30 datasets carry a content-hash field; 3 mention `sha256` anywhere. Hashing exists almost entirely on `papers` (40 files) |
| the corpus makes no outward citation | **true** | one `Merkle`, three `canonical JSON`, nothing else. Every other apparent hit was a substring of *case* / *causal* |
| belief aggregation is undesigned **and unlisted** | **true** | `belief policy version` occurs four times corpus-wide, always as closure member 7 or "a policy constant". No document defines the function; no open-questions list names it |
| compound guarantee rows defeat localization | **true** | W8a is 1,877 words in one table cell; R23 ~1,560 |

**Two schema facts the review did not reach, and which are sharper than its
title-level argument.**

> **(a) The typed layer and the science are disjoint record sets.** Across all
> 334 mm30 propositions, `subject` / `predicate` / `object` / `polarity` appear
> on **exactly the 307 stubs**. The 27 authored propositions carry none of those
> fields — only `claim_layer` and prose. The existing structured representation
> is not *mostly* stubs; it is *only* stubs.

> **(b) No record anywhere carries a qualifier.** Zero qualifier-shaped fields
> in 334 records. Kernel §4.1's founding example — *"in adults"* versus *"in all
> humans"* — has **no instance** in the corpus it was designed from.
> `Qualifiers(op)` is entirely greenfield, so §6.4's flat-fragment ruling has
> never met a real restriction.

**What is not adopted from the review.** Its corpus counts (700 propositions,
863 evidence lines, 451 datasets) do not reconcile with measurement (334, 396,
260 for mm30; ~472 datasets tree-wide). Nothing downstream changes, but its
figures are not cited anywhere in this document — including its "18 of 451",
which makes the content-addressability case **weaker** than the truth.

---

## 2. The typing measurement

### 2.1 What this measures, and what it does not

> **Scope rule.** §2 sizes formal-model **limitation 4** — the untypeable-span
> backlog — for all 27 authored mm30 records, under the protocol below. It does
> **not** close formal-model limitation 3, and it does **not** touch kernel
> limitation 3. Limitation 3's extraction error is the gap between a span and
> the claim a reader takes from it; this exercise *is* an instance of that
> error, performed by one reader with the answer in view. The vertical slice
> (§5) must replace judgment with an executable constructor before any coverage
> number here is treated as a property of the system rather than of the
> exercise.
>
> **Amended 2026-08-07.** The constructor exists, was run over these 27 records,
> and **reaches 0 of them** — they carry no `subject`, `predicate` or `object`,
> and `build_claim` reads front matter
> (`2026-08-07-multi-corpus-typing-exercise.md` §4). So the condition above is
> **not satisfiable by any constructor**: the distance between this section's 6
> and the constructor's 0 *is* limitation 3's extraction error, which the scope
> rule already said §2 does not close. Both figures below therefore remain
> hand-computed and remain non-quotable, on the grounds already stated. What the
> slice did measure is the **307 structured** mm30 propositions this section
> never examined — a different population, not a validation of this one.

**Protocol, stated so the result is reproducible and its assumptions are
attackable.**

1. Population: all 27 mm30 propositions lacking `subject`/`predicate`/`object`
   — the complete authored set, not a sample.
2. Input: the record's `title` and front matter. `measurement_model` prose was
   **not** used: a real `decodeClaim` never sees it, and the target is what a
   constructor could reach from what is recorded as the claim.
3. **Counterfactual vocabulary.** ρO4 records that no population vocabulary is
   bound, so under today's contracts *every* record is untypeable by
   construction and the measurement would be trivially 0/27. Each record is
   therefore typed **as if** the terms and operators it needs were bound with
   plausible sorts. **V is recorded on every record where vocabulary is a
   blocker**, including records that also carry Γ (0002, 0013). The count that
   drives a verdict is the derived **V-only** figure — records where vocabulary
   is the *sole* remaining blocker — reported separately in §2.3.
4. One reader, no second pass, no adjudication. Each verdict is a judgment call
   and is recorded per record in §2.2 so it can be disputed individually.

### 2.2 Per-record worksheet

Verdicts: **T** types in the flat fragment given bound vocabulary · **T-split**
types after decomposition · **R** refused.

Blockers: **V** missing vocabulary · **Γ** missing claim grammar · **A**
non-atomic record · **K** wrong epistemic kind.

| # | record (short) | attempted typed claim | blockers | verdict | destination |
|---|---|---|---|---|---|
| 0001 | MGUS→SMM epigenomically active but transcriptomically weak | two claims, one per assay channel, each with a gradable magnitude | A, Γ | R | decompose; then §3 F-Γ-quant |
| 0002 | PHF19 retains prognostic signal beyond gain(1q) dosage | `has-prognostic-signal(PHF19)` adjusted for a covariate set | Γ, V | R | §4 grammar: set-valued restriction |
| 0003 | strongest current H1 mechanism is the PHF19/PRC2–IFN arm | superlative over an implicit candidate set | Γ, K | R | re-home as a **decision**; §2.3 |
| 0004 | gain(1q)± strata have materially different rankings | comparison across two values of one dimension, magnitude-qualified | Γ | R | grammar: two restrictions on one dimension; quantitative |
| 0005 | H2 is best read as convergent endpoints via divergent programs | interpretive predication over two claim-shaped operands | A, K | R | re-home as an **interpretation** (D §6 facet conjunction) |
| 0006 | longitudinal gain(1q) acquisition supports a causal role | `supports(evidence, claim)` — second argument is a claim | K | R | re-home as an **assessment** (`assesses` edge) |
| 0007 | ribosome–E2F1 bridge best read as a cell-state composition link | interpretive predication | K | R | re-home as an **interpretation** |
| 0008 | t174 per-cell coupling collapses under the adjustment panel | `coupling-attenuates(X,Y)` under a two-element adjuster set | Γ, K | R | grammar: adjustment set; and §2.3 |
| 0009 | composition adjusters do not absorb the bulk association | negated `absorbs(adjusters, association)` | Γ, K | R | grammar + re-home |
| 0010 | t202 shows the null baseline depends strongly on matching | `shows-that(analysis, claim)` + magnitude | Γ, K | R | re-home as an **assessment** |
| 0011 | t174/t202 narrow the explanation but do not adjudicate | two meta-claims about evidential state | A, K | R | re-home as a **verification result** |
| 0012 | the migrated t174/t202 representation preserves the verdict | a claim about this record system, not about the world | K | R | re-home as an **audit/verification** finding |
| 0013 | lineage, especially t(11;14), conditions rankings beyond gain(1q) | `conditions(lineage, ranking)` + focus operator + adjuster | Γ, V | R | grammar: adjustment set; focus has no slot |
| 0014 | transient Polycomb perturbation is **sufficient** to induce transition | modal `sufficient-for(X, Y)` | Γ | R | grammar: modality |
| 0015 | attractor occupancy; durable escape **requires** multi-target flattening | two claims, second modal and contrastive | A, Γ | R | decompose; grammar: modality |
| 0016 | HD is a multi-trisomy architecture that conditions H2 beyond binary HD | two claims + comparative baseline | A, Γ | R | decompose; grammar: comparative baseline |
| 0017 | the gain(1q)− ribosome program is a subtype-specific vulnerability | `confers-vulnerability(program)`, population ↦ ⟨generic, gain1q-neg⟩ | V | **T** | vocabulary work only |
| 0018 | bulk state-space geometry is not reproducible across MM30 cohorts | arity-1 `reproducible-across`, negative, population ↦ ⟨universal, mm30-cohorts⟩ | V | **T** | vocabulary work only |
| 0019 | PC-maturity composition is the **dominant** nuisance axis | superlative over an implicit set | Γ | R | grammar: superlative |
| 0020 | the ribosome program is prognostic but not drug-exploitable | two claims of opposite polarity | A | **T-split** | decomposition rule only |
| 0021 | the Mulligan signature replicates only partially and sign-unstably | quantitative partiality + polarity asserted to be *unstable* | Γ, K | R | polarity is one tag; re-home as **verification** |
| 0022 | dominated by an erythroid axis, **not** proliferation **or** purity | superlative + disjunction of negated restrictions | Γ | R | §6.4's own named refusal |
| 0023 | top OS survival genes are not materially inflated by winner's curse | negated magnitude over a selection-defined subject | Γ, K | R | grammar: threshold; re-home as **verification** |
| 0024 | NPM1 marker ploidy-robust; HD elevates but is decoupled | three claims + an adjustment | A, Γ | R | decompose; grammar: adjustment |
| 0025 | bulk IRE1/UPR conflates enzymatic and nonenzymatic dependencies | arity-3 `conflates(measure, X, Y)`, population ↦ MM | V | **T** | vocabulary work only |
| 0026 | focal and whole-arm gain(1q) are distinct prognostic entities in MM | arity-2 `distinct-from`, population ↦ ⟨generic, MM⟩ | V | **T** | vocabulary work only |
| 0027 | germline DNA-repair axis operates orthogonally to somatic drivers | arity-2 `orthogonal-to`, population ↦ ⟨generic, MM⟩ | V | **T** | vocabulary work only |

### 2.3 Aggregates — an overlapping cover, not a partition

> **The blocker columns are a cover.** A record may carry two or three blockers
> and is counted under each. The column totals therefore **exceed 27 and do not
> sum to it**, and no percentage may be computed by dividing one column by the
> total. The only partition in this section is the verdict column.

| verdict | n |
|---|---|
| **T** — types given bound vocabulary | 5 |
| **T-split** — types after decomposition | 1 |
| **R** — refused | 21 |

> **"6 of 27" is a reproduction yield, not claim-calculus coverage, and it is
> not final.** The 27 are records *labelled* propositions by the legacy system.
> Re-homing one onto another kernel kind **removes it from the proposition
> denominator**; it does not thereby become a successfully typed claim, and it
> is not a failure of the calculus either. Reporting 6/27 as "coverage"
> conflates two different measurements, and an earlier draft did exactly that.

Two figures, reported separately, with different denominators and different
pending inputs:

| figure | denominator | value | pending on |
|---|---|---|---|
| **reproduction yield** — legacy records that reproduce as at least one well-formed record of the new system | all **27** legacy proposition-labelled records | **6 determined-successful**, 10 blocked on grammar, **11 undetermined** | the §2.4 re-homing adjudication. Until it runs, no single fraction is honest — the yield is *6 of 27 with 11 undetermined*, never 22% |
| **expressiveness** — typed-claim coverage among records judged actually to be propositions | **16**, if all 11 **K** records re-home | **6 of 16 (38%)**, provisional | both the §2.4 adjudication and open question 4 |

**Open question 4 can move this figure, and the records it would move are
named.** If an adjustment set defaults to the `analysis-spec` rather than to the
claim, then **0002** plausibly becomes **T** (leaving only vocabulary), and
**0016** and **0024** become **T-split** (leaving only non-atomicity). **0008**
and **0009** stay blocked as **K**, and **0013** stays refused on its focus
operator. So the expressiveness figure is bounded below by 6/16 and could reach
9/16 on that adjudication alone — which is why neither number is quotable until
open question 4 is settled.

| blocker class | records | n |
|---|---|---|
| **Γ** missing claim grammar | 0001, 0002, 0003, 0004, 0008, 0009, 0010, 0013, 0014, 0015, 0016, 0019, 0021, 0022, 0023, 0024 | 16 |
| **K** wrong epistemic kind | 0003, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0021, 0023 | 11 |
| **A** non-atomic record | 0001, 0005, 0011, 0015, 0016, 0020, 0024 | 7 |
| **V** missing vocabulary | 0002, 0013, 0017, 0018, 0025, 0026, 0027 | 7 |

Derived, and the figure the verdict column rests on: **V-only** — vocabulary is
the sole blocker — is 0017, 0018, 0025, 0026, 0027, **5 records**. 0002 and 0013
carry V *and* Γ and are not reachable by vocabulary work alone.

**Within Γ, by frequency among the 16 Γ records.** These are frequencies, not
unblocking counts: the cover overlaps, so closing one gap does not release the
records that carry a second Γ cause as well.

| grammar gap | n | status in the banked design |
|---|---|---|
| adjustment / covariate set (a set-valued restriction, no dimension for it) | 6 | **unnamed** — §6.4 defers quantitative restrictions and refuses disjunction, but never names this case |
| quantitative or magnitude restriction | 5 | §6.4 defers |
| superlative / comparative over an implicit set | 4 | unspellable; unnamed |
| modality — necessity, sufficiency | 2 | no slot; unnamed |
| disjunction of restrictions | 1 | §6.4 refuses explicitly |
| two restrictions on one dimension | 1 | the map permits one |
| polarity asserted to be *unstable* | 1 | polarity is a single tag |

**Three findings follow that the review did not reach.**

1. **The largest grammar gap is the adjustment set, and no banked document names
   it.** Six records refuse because a claim's restriction is a *set* of
   covariates conditioned on. The review led with quantitative restrictions;
   they rank second.
2. **Non-atomicity is the cheapest large win.** Seven records refuse partly or
   wholly because one file holds two or three claims. That is a write-boundary
   rule — one record, one claim — not a grammar extension, and it costs nothing
   in `Claim`.
3. **Second-order records are the second-largest class and must not be answered
   in `Claim`.** See §2.4.

### 2.4 The eleven **K** records — a classification, and a moratorium

Kernel §11 names non-empirical claims as the largest open question. §2.2 shows
the case is not a corner: eleven of 27 authored records are, in whole or in
part, claims *about* claims, analyses, or the record system. Under the ten
kernel kinds they are not one thing:

| proposed home | records | why |
|---|---|---|
| **assessment** — evidence bearing on a proposition, the `assesses` edge | 0006, 0009, 0010 | *"supports"*, *"shows that"*, *"do not absorb"* each report a derivation's bearing on a claim. This is the belief-bearing edge, already typed |
| **verification** — comparison of two runs under a frozen equivalence rule | 0011, 0021, 0023 | replication, sign-stability, winner's-curse inflation are verdicts over analyses, not statements about myeloma |
| **interpretation** — D §6's facet conjunction, promotable on the trigger | 0005, 0007 | *"is best read as"* is precisely the competing-alternatives case D's promotion trigger exists for |
| **decision / current best explanation** | 0003 | a superlative over a candidate set is a standing choice, revised as candidates change |
| **audit finding** — about this record system | 0012 | not a world claim at all |
| **unresolved** | 0008 | reads as an assessment, but its subject is an adjusted association the grammar cannot name; blocked behind the adjustment-set decision |

> **Moratorium (proposed ruling).** **`Claim` is not extended with a
> higher-order argument until this classification is settled.** The scope is
> exactly that: an `operator` whose argument is another claim. Other grammar
> extensions — the adjustment set, quantitative restrictions, modality — are
> not covered by this moratorium and are free to proceed on their own merits.
>
> **The objection, stated correctly.** A claim-valued argument does *not*
> break §6.5's "every position is an identifier" rule: a claim identity is an
> identifier, and `I_claim` would sit in the slot perfectly well. Nor does it
> import retraction or standing — **C10 refuses a retraction naming a
> proposition**, so a proposition's lifecycle is `supersedes` and nothing else.
> An earlier draft of this blockquote claimed both, and both were wrong.
>
> The actual boundary change is that `Args` widens from **external referents**
> to **internal record identities**. A referent is a term drawn from a bound
> vocabulary: it resolves through the vocabulary contract, and §7's five
> outcomes are the whole of its resolution story. A proposition identity
> resolves through the **world**, and carries **supersession** — so an argument
> slot holding one inherits record resolution and a successor chain, and a
> claim's arguments stop being inert with respect to anything but vocabulary.
>
> **And it collapses a discourse edge into claim semantics.** *"X supports Y"*
> is today spelled by an **edge** — `assesses` from an assessment, or
> `asserts | denies | hypothesizes` from a source-assertion. Those edges are
> what let forty assertions of one proposition stay forty nodes (§2.1's
> source-assertion row) and what keep the belief-bearing edge the only
> belief-bearing edge. Re-spelling the relation inside `Claim` puts it where no
> edge discipline reaches it. Eleven records is a strong pull toward exactly
> that. If most re-home onto existing kinds, the pull disappears; if a residue
> survives, *that* residue — not the whole class — is the case for the
> extension.

---

## 3. Dispositions

Verdicts: **accept** · **accept-mod** (accepted with a stated modification) ·
**re-litigate** (docketed to §4, no verdict here) · **reject** · **defer**.

| # | finding | verdict | disposition and landing site |
|---|---|---|---|
| F1 | the claim calculus types the stubs and refuses the science | **accept** | measured in §2 and sharpened: the typed fields exist *only* on stubs (§1 (a)). Sizes formal-model limitation 4; does **not** close limitation 3 (§2.1) |
| F2 | content-addressability is empty on day one and no ramp is designed | **accept** | 0 of 259 mm30 datasets carry a content hash, so kernel §2.2's *held* predicate and the eligibility gate admit nothing. New obligation: **the admission ramp** — how a corpus goes from zero held inputs to a usable admitted set. No banked document owns it |
| F3 | belief aggregation has no design and is on no open-questions list | **accept, narrowed — now designed** | the largest hole. The prior, the belief scale, the displacement metric and "the policy's ordinary rule" are all cited as versioned constants that nothing defines. **Designed 2026-08-05** (`2026-08-05-belief-policy-design.md`, P1–P9). The row as written was **too broad**, and the correction is recorded rather than quietly dropped: kernel §4.2.1 designs the aggregation *structure* in depth — dependency graph, maximum-independent-set selection under a three-stage lexicographic objective, contestation as one clamped move inheriting the outer objective, exact-only selection, the addition property — and substrate S6 already carries eight test arms over it. What had no design was every **scalar** that structure is parameterized by, plus the identity pinning them. This closes the prerequisite §5.5 names; **cut 1 is unchanged and still computes no belief** |
| F4 | sub-problem 6 is undesigned and four documents defer load-bearing questions into it | **accept** | including audit liveness (computation §11: *"nothing here forces an audit ever to run"*) — the universal backstop for every raw-write hole — and kernel §6's divergence table, which the kernel calls the main capability it adds. Recorded as the largest **structural** deferral; not opened in this pass |
| F5 | non-empirical claims have no route to belief | **accept, elevated** | §2.4 shows it is 11 of 27, not a corner case. Elevated from kernel §11 open question to a **blocking prerequisite for a higher-order argument extension** — and for that alone. It does not gate the adjustment set, quantitative restrictions, or modality, which are ordinary grammar questions (§2.4) |
| F6 | estimand match is unclosed | **accept as a known deferral** | kernel limitation 5 already names it as the largest survivor of the ten-item scope cluster. Recording it as a *finding* overstates novelty; it stays open, unamended |
| F7 | shelve the tamper-evident log | **re-litigate** | §4.2. The Dropbox observation is the review's sharpest hit and is accepted as a **hazard** (F17); "shelve L" does not follow from it |
| F8 | drop the normative contract's superstructure, keep the oracle tables | **re-litigate** | §4.3, split into parity machinery (deferrable) and SSOT/succession/identity/inventory (not). Note that retiring `instrument-certification` would remove a **tenth kernel kind** cited across several documents — a cross-corpus amendment, not a cut |
| F9 | world addressing's basis-derived address is unjustified | **re-litigate** | §4.1. Verified: §4 rejects three alternatives and never considers the adjacent one |
| F10 | world §5's receipt apparatus is 42% of the document and its evidence expires | **re-litigate, folded into F9** | limitations 10 and 11 concede expiry-on-next-commit and inability-to-invalidate. Its fate follows the address ruling |
| F11 | compound guarantee rows defeat localization | **accept** | W8a is 1,877 words in one cell. **Splitting is id-stable but requires a contract amendment** — not free, as an earlier draft of this row claimed. Normative contract §3: *"Extending a table appends; amending a row's meaning mints a successor contract identity under the retained id … renumbering is unspellable."* Appending the new rows does **not** split the compound one; narrowing the original is an amendment to its meaning, so a split costs a successor contract identity plus updates to the exact oracle inventory (5b §4), the ledger's artifact-7 inventory, and the owning design's own obligations. §5.2 found **five** rows compound enough that cut 1 can reach part of each — M5, M6, M8, D3, N2 — not the one this document first assumed, and not the eight a second draft claimed before D4, D6 and M12 were withdrawn from the cut entirely. Cut 1 works around the five by selecting arms, which is why it does not pay that cost now; the amendment is the cheaper fix only if the pattern recurs at cut 2 |
| F12 | revision archaeology triples reading cost | **accept-mod** | the review blurs two things. The **withdrawal blockquote stays at its site** — that discipline is what caught the migration-rule defect before the last push. The **narrative history** moves to a per-document appendix |
| F13 | not one outward citation in 11,953 lines | **accept** | verified. A reader cannot distinguish deliberate divergence from ignorance. Each document gains a short related-work note naming what it re-derives and where it diverges: in-toto/SLSA, Certificate Transparency, Sigstore/Rekor, W3C PROV, RFC 8785 |
| F14 | both ends of the attack are specification | **accept-mod** | true of `science` (11,953 lines, no code). False of the stack: `nodes` is released and parity-tested, `atoms` is real through A5b |
| F15 | the review's corpus counts | **reject** | do not reconcile with measurement; not cited (§1) |
| F16 | build the vertical slice next | **accept, sequenced** | correct, but **cut 1 freezes first** (§5) — otherwise the cut becomes a post-hoc list of what happened to pass — and the slice **stops at the last fully designed seam** (§5.5) |
| F17 | the real threat is two hosts publishing into synced world roots | **accept as hazard; reject minting a design** | packaging limitation 4 concedes it, and this repository is synced. But a detector presumes multiple live writers. **Decide the writer model first.** If single-writer, the smaller and stronger rule is operational prevention — one writer, and no synchronized live Git metadata — not a detector. Recorded as a decision owed, not a design opened |

---

## 4. Re-litigation docket

Each item gets a written head-to-head against the alternative its document never
considered. **No verdicts here.** The docket exists so the option is preserved
rather than lost, and so each comparison is argued on terms fair to both sides.

### 4.1 World address — basis-derived versus `kind:slug` with boundary uniqueness

The unconsidered alternative: keep nominal `kind:slug` addresses, enforce
uniqueness at the write boundary, and use the identity basis as a **coreference
check** rather than as the address.

Fair framing requires stating what each side actually buys.

- The alternative is not weaker by assumption. §5 **already** enforces "one
  identity, one file, one location … refused at the write boundary", so the
  enforcement point exists either way.
- The review's phrasing — that W1 and W2 restate *"a hash is injective"* —
  **repeats an overclaim the corpus has already retired** and must not be used
  as the docket's framing. Formal model §3.4 states the property exactly: what
  is claimed is not mathematical injectivity of `H`, but that `encode ∘ πᵢ` is
  **injective on admissible values** and that `H` is **domain-separated and
  collision-resistant**. Correction §4 withdrew a well-foundedness argument for
  precisely this confusion.
- Restated on those terms the observation survives, and is still the review's
  strongest: **W1** (distinct bases never become one node) and **W2** (a shared
  basis establishes coreference mechanically) follow from the encoding's
  injectivity on admissible bases together with collision resistance. They test
  that the basis was chosen and encoded correctly — which is real — but they do
  not test anything the *address scheme* adds beyond it, which is what the
  docket has to price.
- **But the loss is real and must be priced.** Under basis-derived addressing,
  two records with the same basis are **unconstructible** (US†). Under the
  alternative they are **detected and refused** (RF†) — a strictly weaker law,
  and one that can be bypassed by a raw write in exactly the way §6.3's third
  row describes. The question is whether that downgrade is worth the address /
  alias duality, the alias map, the fourth resolution state, W9, §4.4's
  rename-on-DOI-correction machinery, and §5's receipt apparatus (F10).

### 4.2 Tamper-evident log — versus `world root = git repo, anchor = push`

The log design re-derives git's object model closely enough that the null
hypothesis had to be weighed and was not: entry digest over `(predecessor,
payload)`, linkage-not-filename ordering, genesis, fork-versus-replica, anchors
as pushed refs, the unanchored tail as unpushed commits.

Fairness constraints on the comparison:

- **A git push is an anchor only against an immutable or protection-enforced
  external ref.** An ordinary mutable remote is not an anchor: force-push
  rewrites history, so the null hypothesis must be stated as "push to a
  *protected* ref", and the operational cost of that protection is part of its
  price.
- The log's own **limitation 2** concedes that on a single host with no external
  holders, destruction of a world and every observer of it is undetectable — so
  in the deployment that will exist for years it degrades toward what git and
  backups already provide.
- Against that, git offers no **subject-bound** anchor across corpora, no intent
  entries, and no carrier for the registry log-head the packaging design
  reserved. Those are the properties the comparison has to defeat, not the hash
  chain itself.
- Every L row remains gated on composition-root adoption. A7's engine half
  landed 2026-08-14 and A8 landed 2026-08-17, but no Science L row moves, so
  nothing is unblocked by deciding this sooner and nothing is lost by deciding
  it later.

### 4.3 Normative contract — parity machinery versus what survives one implementation

The document's own **limitation 5** concedes: *"One implementation makes
conformance a self-check."* The docket must split the design rather than accept
or reject it whole.

| stratum | contents | provisional reading |
|---|---|---|
| **coordination / parity** | exact-K certification, `instrument-certification` as a tenth kernel kind, §7's existential audit apparatus, and the conformance framing that treats agreement between implementations as the evidence | machinery for keeping *independent implementations* honest. Deferrable while there is one |
| **still needed regardless** | the single source of truth for rules; **cut identity** and **contract succession**; **rule identity** = (symbol, fixture-set identity); and the **oracle inventory** | these hold for one implementation as much as for five |

**A correction to the review's split, which this document initially repeated.**
Cut identities and successor chains do **not** belong in the deferrable
stratum. A cut is the versioned set of rules a derivation speaks for; with one
implementation you still need to say *which cut* a result was produced under and
how a rule's meaning changed between cuts, or an amendment becomes
indistinguishable from a correction. Placing them below while placing "contract
succession" above was self-contradictory — they are the same mechanism. Both are
now in the surviving stratum, and the oracle inventory is what §5 selects from.

Note the coupling F8 records: `instrument-certification` is one of the ten
kernel kinds and is cited in the formal model's §2.1 inventory, in world §4.2,
and in the N table. Deferring its *machinery* is cheap; removing the *kind* is a
cross-corpus amendment.

---

## 5. Conformance cut 1 — frozen prospectively

> **Why prospectively.** A cut drawn after implementation is a list of what
> happened to pass. This cut is frozen **before** any code exists, so a row that
> fails is a failure and not a redefinition.

### 5.1 Step 1 — the boundaries the slice crosses

The slice is `Claim`, `π_claim`, `I_claim`, `decodeClaim`, the base operator
contract, and the cross-language parity fixture. It crosses exactly three
boundaries:

1. **the typed constructor** — the only route to a `Claim`;
2. **`decodeClaim`** — where an external value meets the contract that types it;
3. **contract load and compilation** — where `ProfileSpec` yields claim schemas.

It crosses **no** persistence boundary. Construction and canonical serialization
are in scope; writing a record into a corpus is not, because that seam runs
through the substrate write API and world addressing, neither of which is built.

### 5.2 Step 2 — the unit of selection is an assertion arm, not a row

> **Withdrawn.** An earlier draft of this section selected **twelve whole rows
> plus one conditional**, and reported *"12 selected + 1 conditional + 113
> deferred = 126, every banked row accounted for in exactly one place."* **That
> accounting was not semantically valid** and is withdrawn. Several selected
> rows carry arms the declared slice boundary (§5.1) explicitly excludes: M5's
> founding case requires proposition minting, assessment binding and
> `supersedes`; M6 and M8 each require a `belief_input_digest` assertion; D3's
> `not-present` and `not-available` arms require world availability; D4's first
> arm requires facet composition and `KindSpec` registration. D6 was therefore
> **not** the only compound row, and treating whole rows as atomic made the cut
> claim coverage the slice cannot deliver.

**The rule that replaces it.** Cut 1 is defined over **exact assertion arms**. A
banked row may be **partly selected and partly deferred**; no row is split in
the banked corpus to make this work, and no selected arm may depend on a
boundary §5.1 excludes. Every banked row is classified into exactly one of three
states.

**Three rows were selected in the first corrected draft and are withdrawn from
the cut entirely**, because "partly selected" was itself being used to smuggle
past the boundary:

| row | why no arm survives |
|---|---|
| **D6** | it has **no identity arm**. Every D6 assertion is about `belief_input_digest` — the claim-schema arm, the base-contract arm, the unconditional arm and the negative arm alike. The clause selected as D6's — *"a consulted claim schema does not enter `I_claim`"* — is **M8's** assertion, misattributed. D6 is fully deferred |
| **D4** | its mutations concern **facet** compilation, `KindSpec` registration and namespaced **facet** projection — not claim-schema compilation. Claim-schema compilation is **M7**'s, which is why M7 exists (its own text: *"D4 does not cover this — it governs per-kind sources, and a claim schema is not a per-kind artifact"*). Selecting D4 double-counted M7 |
| **M12** | its banked text states the form is not optional: *"**End to end, which is the only form this row can take.**"* Selecting the no-mint prefix while deferring the work-item arm contradicts the row's own condition. The row needs extraction, proposition and source-assertion construction, and the typing-work queue |

**Fully selected — every arm is inside the slice's boundaries (6 rows).**

| row | what the slice must demonstrate | its sabotage |
|---|---|---|
| **M4** | every argument and restriction is a typed referent; only `not-member` refuses; an unperformed check stays explicit; the receipt carries exactly one outcome per referent position plus the `ResolutionSnapshot` identity | decode a term absent from a **readable** vocabulary → refused, nothing minted |
| **M7** | no second authored operator artifact exists; semantic-schema edits recompile, description edits do not | add a hand-authored operator roster beside the contracts → refused or unreachable |
| **M9** | `π_claim`'s shape depends on the claim, never on a contract field; `inapt` and `unsigned` are distinct bytes **against the base contract** | omit the polarity position for sign-inapt operators → the digest changes |
| **M10** | two implementations hash a claim identically over **every** closed tag, with vector coverage asserted complete | change one implementation's map-key sort, slot order, or a single tag's bytes → fixture fails |
| **M11** | `decodeClaim` is a function of its arguments and refuses rather than repairs, for each ill-formed input in turn | make availability ambient rather than a parameter → two holders decode the same bytes differently |
| **M13** | `Claim` is opaque; the validated constructor is the only route; no downstream signature accepts `WireClaim` | export a raw constructor, or widen one downstream signature → must fail |

**Partly selected — the arm split, stated exactly (5 rows).**

| row | arms **in** cut 1 | arms **deferred**, and on what |
|---|---|---|
| **M5** | restriction identifier alone forks `I_claim`; quantifier tag alone forks; a present-versus-absent dimension forks; sabotage (drop the qualifier map → the founding pair collapses to one identity); negative (re-serialize map keys in another order → unchanged) | the founding case **end to end** — mint, assess, edit, assert a new identity with the prior assessment still bound and a `supersedes` link. Needs minting, assessment binding and succession: **persistence + belief** |
| **M6** | a successor changing `arity`, `arg_sorts`, `sign_apt`, `layers` or `dimensions` under an existing id → refused at load; a successor dropping a retired declaration → refused; an additive successor → accepted with **claim identities unchanged**; retirement both paths; sabotage (flip `sign_apt`; remove the predecessor link); negative (editorial change accepted, contract identity moves); the parallel-genesis **DL** | *"consulted belief digests move"* on an additive successor. Needs **belief** |
| **M8** | recompile `ProfileSpec` under a different merge order and compiler build → `I_claim` **unchanged**, and `ProfileSpec`'s identity absent from `π_claim`; sabotage (fold the contract release into `π_claim` → an ontology release forks every claim) | the `belief_input_digest` half of the editorial-bump arm; the negative arm's digest half (activated-but-unconsulted); **and the "absent from the consulted set" clause**, which needs the consulted-contract machinery the slice does not build. Needs **belief** |
| **D3** | `vocabulary` with no release → refused at contract load; a readable vocabulary yields `member` and `not-member`; an unconsulted namespace yields `not-consulted`; **only `not-member` refuses**; the binding stays well-formed with **no fallback to another release** | `not-present` (world address indexed, corpus absent) and `not-available` (dataset identified, no bytes held). Needs **world availability and holding**. *Note:* M4's local analogue — an unreadable vocabulary yielding `not-available` — **is** selected; the two are not the same test, and this cut does not let one stand in for the other |
| **N2** | **every oracle row can fail**, applied to cut 1's own selected arms: sabotage each selected arm and assert its check fails; construct an arm that passes under its own sabotage and assert it is reported as **malformed contract content** | the same doctrine over the rows cut 1 does not select |

**N2 belongs here, and its inclusion is the point.** Its trigger is *the first
executable suite*, which is what cut 1 is — not a second implementation. A cut
whose own rows were exempt from the discipline they encode would be the first
thing this corpus should refuse.

**N2 as built (2026-08-06).** Forty-two arms across the ten other selected rows,
each declared as data: the row, what the arm asserts, a source mutation that makes
it false, and the **exact tests** that must fail under it. The harness applies each
mutation to a copy of the package and runs that arm's checks in a subprocess, so
nothing touches the working tree.

Four details were not obvious before building it, and each came from the harness
reporting on its own table:

* **Naming the checks is the whole difference.** Three sessions of hand-run
  matrices asserted only that *the suite* went red, which cannot see an arm whose
  mutation breaks something unrelated while its own check stays green. Ten of the
  first forty arms were defective on the first audit — five vacuous, five stale.
* **Staleness is a distinct finding, and the one that will actually happen.** A
  sabotage that no longer matches the code applies nothing, so the checks pass and
  the arm scores healthy. It is the same false report as vacuity, reached by a
  route that opens as the code moves under a table nobody re-reads. Both are
  reported as malformed contract content.
* **The unsabotaged direction is load-bearing.** A check that does not pass
  against the real package asserts nothing about what a sabotage does to it,
  because it was already red. So every declared check is also run without the
  sabotage and must resolve and pass.
* **The verdict has to be taken over the unit the arm names, and only exit code 1
  is a verdict.** Both halves were wrong in the first build and are recorded here
  because neither is visible from a green suite. An arm's checks run in **one
  `pytest` invocation per check**: a single invocation carrying several node ids
  reports one exit code, so a failing check covers for a passing one, and three
  real arms in this table were sitting exactly that way — the M4 bare-string arm,
  the M8 contract-identity arm, and the M10 tag-bytes arm each carried a check
  that passed under their own sabotage. And *"exited non-zero"* is not *"the check
  failed"*: `pytest` exits **4** when it cannot collect the node id, so a renamed
  check, or a sabotage coarse enough to break the module's syntax, scored as a
  failing check while demonstrating only that unimportable code does not import.
  `uncollected` is now its own finding.
* **The unit is a test function, and splitting the invocation does not by itself
  say so.** The first fix required a check to *look like* a node id, which a
  **class** node also does — and a class node is one invocation over every method
  it holds, so the aggregation returns through the check rather than the runner.
  Measured: `test_decode.py::TestM4TypedReferentsAndTheReceipt` under M4's first
  sabotage scores `sound`, with one method failing and the rest passing behind
  the class-level exit code. The rule is therefore the unit and not the
  punctuation. It stops at **parametrization**, deliberately: the parameters of
  one test function are its data rather than separate assertions, so a check that
  fails on some rows of a vector and passes on others is a check that failed.

The three arms are worth naming individually, because each was repaired
differently and none of the repairs was *"fix the mutation"*:

* **M4** was asserting two properties held at two places — *a bare string cannot
  occupy a slot* (the constructor) and *the sort travels with the value* (the
  boundary) — and no single sabotage can make both false. Split into two arms.
* **M8**'s `test_no_contract_identity_reaches_the_bytes` looks for the profile's
  own digests, computed at run time, and **no source mutation confined to
  `projection.py` can put one in the bytes**. It guards the prohibition from the
  value side and no arm can make it fail; the arm now names the signature test,
  which the class's own docstring already identified as the one with force.
* **M10**'s sabotage changed backslash escaping, which the claim parity fixture
  does not cover — the finding recorded against the owed values-level fixture in
  the formal model design. The tag-bytes arm now renames one closed-vocabulary
  polarity tag, which the fixture *must* see because coverage of the closed sets
  is asserted by the arm beside it; the escaping sabotage is kept as its own arm,
  worded as what it actually asserts.

Two of the original ten defects were of the same kind as M8's: the arms were
pointed at checks the suite's own docstrings already record as **unable to fail**
(`science.identity.v1` sorts object keys at encode time, so no iteration order
inside the compiler can reach an identity). Those notes had been written honestly
and then not consulted when the arm table was drawn up. The harness is what
connected them.

N2's second clause is discharged by five arms defective **by construction** —
vacuous, stale, mixed (one check fails, one passes), uncollected, and a class
node — which the harness must report rather than pass. The harness itself is
sabotaged fifteen ways.

One of those fifteen is a rule the build learned the hard way. A check that
resolves to a whole module rather than one test — the empty string, a bare
directory, or the harness file itself — collects `testpaths`, including the
harness, whose every arm invokes `pytest` again. That is not a weak arm but a
**fork bomb**, so it is refused twice: `audit` refuses an arm that names no check
and reports it as a finding, and the runner refuses a check that is not a node id
outside this file. Each guard is what makes the other survivable. The
demonstration was involuntary the first time: the harness's own first sabotage
script mutated `tests/` in place and restored in a `finally`, and a `SIGKILL`
during the runaway left two sabotages on disk — the exact practice the harness
replaces, committed by the tool auditing it. The second time was deliberate and
contained: disabling the runner's guard was run inside a bounded `systemd-run`
scope, where it detonated as predicted rather than reporting anything, so a
terminating variant — a guard narrowed to refuse only the empty check — is what
demonstrates the property cleanly.

**Why six-plus-five and not the ~25 the review proposed.** Selection is by
boundary crossed, arm by arm. A row the slice cannot exercise is not
strengthened by being listed, and a row listed whole while half of it is
unreachable is worse than an honest omission.

**Explicitly considered and fully deferred**, with the reason:

| row | why no arm is in cut 1 |
|---|---|
| **M1** | requires an instrumented resolver; the slice has none |
| **M2**, **M3** | runs, run inputs, retraction graphs — none exist in the slice |
| **G7** | its converse arm is *implied* by M5's and M8's selected arms but is not the same assertion, and its positive arm needs the mint path. Implication is not selection |
| **S2**, **S3**, **S8** | the substrate write API and the import path are not crossed |
| **G3**, **D6** and all belief rows | the slice computes no belief (§5.5) |
| **D4** | facet composition and `KindSpec` registration; its claim-adjacent content is M7's |
| **M12** | end-to-end by its own banked condition |

### 5.3 Step 3 — fully deferred rows, grouped by untouched subsystem

115 of 126 rows have **no** arm in cut 1. Grouping is by the subsystem the slice
does not build, so each group has a single unblocking event. The N group is
split, because its rows do **not** share a trigger.

| group | rows | n | unblocked by |
|---|---|---|---|
| tamper log | L1–L13 | 13 | composition-root adoption (and §4.2) |
| computation & runs | R1–R23 | 23 | the run boundary |
| world addressing | W1–W13, W5a, W8a–b | 16 | the world index (and §4.1) |
| packaging | X1–X12 | 12 | world export |
| correction lifecycle | C1–C10 | 10 | retraction records |
| normative contract — **contract cut** | N1, N3 | 2 | the **first contract cut**: succession retaining ids, and rule identity = (symbol, fixture-set identity). Not a second implementation |
| normative contract — **certification** | N4–N9 | 6 | instrument certification and the parity machinery (§4.3) |
| normative contract — **legacy adoption** | N10 | 1 | the **adoption gate** over the legacy suite. Independent of implementations entirely |
| kernel & belief | G1–G8 (incl. G2a–c) | 10 | the belief policy design (F3) |
| substrate | S1–S8, S1a | 9 | the write API |
| domain boundary, not crossed | D1, D2, D4, D5, D6, D7, D8, D9, D10 | 9 | facets, manifests, practices, and belief for D6 |
| formal model, not crossed | M1, M2, M3, M12 | 4 | resolver, runs, retractions, and the extraction path for M12 |

**Accounting.** 6 fully selected + 5 partly selected + 115 fully deferred = 126.
Every banked row is classified into exactly one of the three states. **No count
of "arms" is offered as a denominator**: the banked rows do not enumerate their
arms formally, so the arm splits in §5.2 are *this document's reading* of each
row's test cell, and a different reader could draw a boundary one clause earlier
or later (limitation 7).

### 5.4 Steps 4 and 5 — freeze and amendment discipline

> **Freeze.** This cut is frozen on the date in the status header, before any
> implementation exists. **Results are recorded separately**, never by editing
> the selection. If the cut must change, the original selection is **preserved
> verbatim** alongside the amendment, with the reason stated — the same
> discipline the banked corpus applies to withdrawn arguments.

### 5.5 Where the slice stops

> **Stop rule.** The slice stops at the **last fully designed seam**. Typed
> claim construction, canonical projection, identity, decode and cross-language
> parity are fully designed and can run now. **If the slice would compute a
> belief, the belief-policy design (F3) is a prerequisite** and the slice must
> stop short of it. Proposition and source-assertion *construction* is inside
> the seam; belief, admission and eligibility are outside it.

**The prerequisite is discharged, and the stop rule stands unchanged**
(2026-08-05, `2026-08-05-belief-policy-design.md`). The rule is preserved
verbatim above per §5.4's discipline. Discharging it does **not** move the seam:
cut 1's selection is exactly what it was, it still computes no belief, and P1–P9
are acceptance criteria for a later slice rather than rows added to this cut. A
future slice that does compute belief now has a designed seam to stop at, which
is the only thing that changed.

---

## 6. What must survive any cut

Recorded because §4 puts three documents at risk of deletion, and these must not
travel with them.

1. **A paper is not a measurement of the world; it is a measurement of what
   someone wrote** — enforced by role-typing inputs (`observes` versus `reads`)
   so that literature→belief has **no edge that spells it**, rather than a flag
   that checks it. Structural, and grounded in observed failures.
2. **Negative tests that assert the system cannot detect something.** The
   discipline that produces declared limits (DL) instead of overclaims.
3. **Kernel §2.1's explicit guaranteeable / not-guaranteeable split.**
4. **Independence as a maximum independent set**, with the counterexamples that
   kill both connected-components and the greedy fallback.
5. **Every check must be able to fail** — §5's OF†, and the per-row sabotage it
   forces. Kept even if §4.3 defers everything else in the normative contract.
6. **Withdrawn arguments quoted at their site** (F12), which is what caught the
   migration-rule defect.

---

## 7. Limitations

1. **§2 is one reader's judgment.** No second pass, no adjudication. Its
   verdicts are recorded per record so each can be disputed individually, but
   the aggregate inherits every individual error.
2. **§2 assumes vocabulary that does not exist** (ρO4). Under today's contracts
   nothing types at all; both §2.3 figures are counterfactual on bound
   vocabulary and must be labelled as such wherever they are cited. Neither is
   quotable until the §2.4 re-homing and open question 4 are settled — the
   reproduction yield has 11 undetermined records, and expressiveness ranges
   from 6/16 to 9/16 on the adjustment-set adjudication alone.
3. **§2 measures 27 records from one domain.** It sizes limitation 4 for the
   mm30 authored set and for nothing else. It is not an estimate of the
   literature, and formal-model limitation 3 stands unamended.
4. **The blocker classification is a cover, not a partition** (§2.3), and the
   assignment of a record to **K** rather than **Γ** is sometimes a choice
   between two defensible readings — 0008 is recorded as unresolved for exactly
   this reason.
5. **§4 decides nothing.** Three documents totalling ~2,800 lines remain in an
   undecided state until the docket is worked, and the corpus meanwhile
   describes a system whose address scheme may not survive.
6. **§5's cut is drawn against a slice that does not exist.** If the slice's
   boundaries turn out differently, the cut is amended under §5.4 — and every
   such amendment is evidence that prospective cutting is harder than it looks.

   **Resolved 2026-08-07, and the answer needs its own caveat.** The slice was
   built and merged (`f81d3a3`) and the cut required **no** §5.4 amendment: the
   eleven rows selected prospectively are the eleven the slice exercises, six
   whole and five in part. That is one clean run on a slice whose boundary the
   same author drew — weaker evidence for prospective cutting than a clean run
   looks, for exactly the reason limitation 8 gives. What building it *did* find
   is recorded in §5's dated subsections and its N2 account, never by editing the
   selection.
7. **The arm splits in §5.2 are an interpretation of the banked rows, not a
   property of them.** No banked table enumerates its assertion arms formally,
   so where one arm ends and the next begins is this document's reading of a
   prose test cell. A different reader could draw a boundary one clause earlier
   and change which half of M6 or D3 is selectable. This is why §5.3 offers no
   arm count as a denominator, and it is the strongest argument for F11's
   splitting: a split row makes the boundary a banked fact instead of a
   reading. **That argument now has a price attached** — a split is an
   amendment minting a successor contract identity (F11) — so the trade is a
   real one, between paying it once and carrying an interpretive boundary
   through every future cut.
8. **§5.2 has now been corrected twice, in the same direction both times.** The
   first draft claimed whole-row coverage the declared boundary could not
   deliver. The second kept D4, D6 and M12 as "partly selected" — using the arm
   split to smuggle past the boundary rather than to respect it — when D6 has
   no identity arm at all, D4's content belongs to M7, and M12's banked text
   forbids a partial form. Both withdrawals are recorded in place rather than
   edited away. **The pattern is the finding:** every error ran toward a larger
   cut, and each was caught by review rather than by the selection method
   itself. A cut drawn by its author against rows the author also reads is not
   self-checking, which is an argument for F11's splitting and for a second
   reader on cut 2.

---

## 8. Open questions

1. **The writer model** (F17). Is more than one live writer supported? Until
   this is answered, neither a sync-corruption detector nor the operational rule
   that would replace it can be specified.
2. **The admission ramp** (F2). How does a corpus with zero content-addressed
   inputs reach a usable admitted set? Nothing owns this.
3. **Where the eleven K records land** (§2.4). Until settled, `Claim` is not
   extended.
4. **Where an adjustment set belongs.** Six records turn on it and no banked
   document names the case. The three candidate homes are **not mutually
   exclusive**, and an earlier draft's claim that conditioning makes it *"a
   different claim"* is **withdrawn as false in general**: different valid
   adjustment sets can identify the same estimand and support the same claim.

   Two axes decide placement, and they are independent:

   - **semantic target** — does conditioning change *what quantity is
     estimated*, or the claim's truth conditions?
   - **identification method** — *which covariates* were used to identify or
     estimate that target?

   `analysis-spec` already separates `estimand`, `method`, `assumptions` and
   `parameters`, so the default placement follows:

   | case | home |
   |---|---|
   | the set only identifies or estimates the **same** target | `analysis-spec.method` / `assumptions` / `parameters` |
   | conditioning defines a **different** target quantity | `estimand` |
   | the source explicitly asserts the relationship **conditional on** that set | **also** represented in the typed claim's qualification |

   The third row is why the homes overlap: the same covariate set can appear in
   an `analysis-spec` and in a claim qualifier without contradiction, because
   they answer different questions. Settling this is a prerequisite for
   quoting either figure in §2.3, and it interacts with the estimand-match
   deferral (F6), which is where a wrong answer would surface.

   > **Answered 2026-09-16** (`2026-09-12-estimand-typing-design.md`,
   > discharged at conformance cut 31). The default placement above is adopted
   > as written, with the three homes made concrete and the two axes kept
   > independent.
   >
   > - A set that only **identifies or estimates the same target** stays in
   >   `method` / `assumptions` / `parameters`, as prose or a ref. The typed
   >   estimand takes nothing from it.
   > - A set that **defines a different target quantity** is typed, and it has
   >   its own member: the estimand's `control` carries one `identification`
   >   term and an unordered set of `conditioning` members, each sorted by the
   >   operator's `estimands:` declaration. Duplicates are refused; reordering
   >   does not move the spec's identity, because the set is unordered and its
   >   canonical projection says so.
   > - A source **asserting the relationship conditional on** that set is the
   >   claim's qualification, and that row is **not** settled here: the
   >   qualifier home for "conditional on" stays a grammar question (design
   >   §13 limitation 5), so this third home remains as banked.
   >
   > The split is what makes the first two decidable rather than a matter of
   > taste: `commensurable` is equality on every estimand member **except**
   > `control.identification`, so two analyses that identify one quantity
   > differently are commensurable, and two that condition into different
   > quantities are not. That is the same distinction this question drew, now
   > computed. The earlier draft's withdrawn claim — that conditioning makes it
   > *"a different claim"* — stays withdrawn: conditioning moves the estimand,
   > not the claim.
5. **Sub-problem 6** (F4) — audit liveness and the divergence table remain the
   corpus's largest structural deferral.
