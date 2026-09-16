# Formal model and claim calculus — design

**Status:** **Banked 2026-08-05**, after review rounds across every section
(§2–§4 three, §5 one, §6 one, §7 two, §8 two, §9 three). The banking commit
applies §8.7's amendment set across the corpus: kernel §4.1/§5/§8/§11 with G3,
G7 and limitation 4; computation §7.1 (R5 unchanged); world §4.3, W4 and §10;
correction §3, §4 and C10; the normative contract §4; the domain extension
boundary §5, §6, §8, §12 with D3, D6 and limitation 2; plus the ledger and the
README. Two consequential edits fall outside §8.7's table and are recorded here:
**world §4.1** and **substrate §4.2** each restated the proposition-identity
basis in passing, and both would otherwise have kept describing an identity over
prose (ρA1, ρA2).

**Inherits:** the epistemic kernel (**G1–G9** since 2026-08-09, §4.1's signatures and semantic
identity, §8.7's recorded-history limit, limitation 4's predicate vocabulary),
substrate consolidation (S1–S9, S9 added 2026-09-13), world addressing (**W1–W16** since 2026-08-08),
computation and
reproducibility (R1–R23), correction lifecycle (C1–C10), world-index packaging
(X1–X12), normative contract (N1–N10), tamper-evident log (L1–L13), domain
extension boundary (D1–D10).

**Constraints:** M₀ transcribes and cites; it never rules. Every entry carries
its banked citation, and a claim with no citation is a gap, recorded as one.
M\* revises only inside the claim neighbourhood, and every revision names the
guarantees it preserves, amends, or invalidates.

**Banking obligations — recorded before drafting, discharged 2026-08-05.**
**M1–M13** are in the normative contract's exact oracle inventory (its §4) and in
ledger artifact 7's inventory; the ledger carries artifact 9 and an order-of-work
item 8; the README's count and table are updated. Both the L-table and the
N-table reached that inventory late — L omitted at its own banking, N only when a
later design noticed 5b §5 requires every oracle table in the suite — and this
note existed so M would not repeat it.

## 1. Why

Nine banked designs decide what the system means. They decide it in prose,
across roughly a hundred guarantee rows, and the properties those rows test are
never named as properties. Two consequences follow.

The first is that **completeness cannot be checked**. G3's belief-input closure
is the clearest case: the kernel's own text records that four of its members
"were live holes in earlier revisions, and none is reached by mutating a
member's value." Each was found by a reviewer noticing. Nothing in the method
distinguishes a closure that is complete from one whose next hole has not yet
been noticed.

The second is that **part of one family was never formalized**. The system's
labels are not homogeneous — `verdict` is a result codomain, `scope` a derived
label, `identification_strength` an ordered measure, `predicate` and
`claim_layer` semantic vocabulary — and they need different contracts, not one.
Sorted that way (§2.9 (c)), the codomains and derived labels are adequately
ruled. **The ordered measures lack their orders, and the semantic vocabulary
lacks term identity, an extension rule, and an owner** — while `predicate`,
`polarity` and `claim_layer` are three of the five inputs to proposition
semantic identity. Kernel limitation 4 records the visible corner: "The
predicate vocabulary is currently 9 terms; real claims will not fit cleanly."

This document is a two-ended refinement loop, not a transcription:

```text
intended epistemic behavior ──▶ candidate reference model (M*)
             ▲                          │
             │                          ▼
banked designs + guarantees (M₀) ◀── refinement / counterexamples
```

Neither end is authoritative. The intent constrains what the system should
mean; the banked designs carry commitments and hard-won edge cases. Where the
two cannot be connected, we have found either a design defect or an
underspecified goal.

Three columns stay conceptually separate throughout:

| layer | purpose |
|---|---|
| **M₀** — extracted model | what the banked designs currently rule |
| **M\*** — candidate model | the smallest system satisfying the intended guarantees |
| **ρ : M₀ → M\*** — refinement map | what is preserved, collapsed, renamed, or exposed as inconsistent |

**M₀ is wide and shallow; M\* is narrow and deep.** M₀ models the entire banked
system at interface depth — formal signatures and a dependency graph, not a
restatement of payload fields or mutation tests, for which the existing
documents remain the detailed source. M\* formalizes the claim neighbourhood
deeply. ρ is initially local to that neighbourhood, and M\* expands only when
another design question requires it.

## 2. M₀ — the formal inventory

> **M₀ is a snapshot, not a current description.** It transcribes the banked
> corpus **as it stood on 2026-08-04**, before this design's banking commit
> applied §8.2. Where §8 amends something, M₀ deliberately keeps the *old*
> reading — a proposition's identity over a normalized `statement` (§2.1), D3's
> "three unresolved states" (§5.2) — because ρ is a map **from** that state and
> rewriting its source would erase what changed. Read §8 for what the corpus says
> now. This is the one part of the document that is stale by design, and it is
> the reason §1's constraint reads *"M₀ transcribes and cites; it never rules."*

Every player gets a compact entry: **construction** (authored, derived, or
external), **identities** (the canonical projections πᵢ its commitments are
taken over — plural, see below), **lifecycle** (the legal transitions),
**reads / produces**, **readings affected**, **inertness** (the observational
equivalences under which it does not move), and **banked citations**.

**The object universe is many-sorted; the state space is not the universe.**

```text
U  =  Rec  ⊎  Proj  ⊎  Ext  ⊎  Art  ⊎  Con  ⊎  Cfg  ⊎  Sub
      │        │        │       │       │       │       └─ subrecord artifacts
      │        │        │       │       │       └───────── corpus / world configuration
      │        │        │       │       └───────────────── contracts and rules
      │        │        │       └───────────────────────── held artifacts (bytes)
      │        │        └───────────────────────────────── external referents
      │        └─────────────────────────────────────────── project-scoped records
      └──────────────────────────────────────────────────── world records

ω ∈ Ω  =  ⟨ population ⊆ U,  relation instances,  derived maps,  configuration ⟩
```

A **configuration** `ω` is a finite population of objects drawn from `U`,
together with the relation instances among them, the derived maps standing over
them, and the corpus/world configuration they are addressed under. `U` is what
exists as a kind of thing; `Ω` is what the system is in at a moment. Conflating
them is what made the first draft treat `Ω` as a disjoint union.

**Identities are plural per player.** One player bears several commitments that
move independently, and D2 is the proof: adding a `biology/gene-axis` facet to a
dataset node leaves the **dataset address** unchanged while moving that node's
**content identity** and, through it, the **corpus-state identity**. An entry
whose identity column held one value could not express D2, so the column holds a
set.

**The sorts are not a partition of concerns.** A `dataset` is a world record
*and* names held bytes; an `assessment` is a record, a derivation, and the
subject of several identities. The sorts partition the *carrier*; the axes above
cut across it, which is why each entry carries all seven fields independently.

### 2.1 `Rec` — world records (the thirteen kernel kinds)

Each row's **identities** cell lists every commitment the player bears. All thirteen
additionally bear a **node-content identity** (moved by any facet or field
change) and contribute to their corpus's **corpus-state identity**; those two are
stated once here rather than repeated in every row.
*(Extended 2026-08-10: `holdings-observation` joined — the verified-holdings
record design §2, §8.)*
*(Extended 2026-08-11: `act-report` joined — the act-report design §2, §7.)*

| player | construction | identities (πᵢ) | lifecycle | reads / produces | affects | inert under | banked |
|---|---|---|---|---|---|---|---|
| `proposition` | authored | **semantic identity** — normalized `statement` + `(subject, predicate, object, polarity, claim_layer)`, immutable for the life of the node; **world address** derived from it | mint → semantic edit **mints a successor** linked by `supersedes`; display edits are ordinary revisions | reads nothing; target of `assesses`, `asserts\|denies\|hypothesizes`, `targets` | belief (closure member 2) | `title` overwrite; location; ~~alias~~ *(alias dropped 2026-08-08 — no label is stored, so there is no alias dimension to be inert in; world address ruling §4)* | kernel §4.1; **G7**; world §3, §4.2 |
| `source-assertion` | authored or extracted, attributed | **content identity over `(source identity, anchored span, stance, proposition identity)`** — the proposition hash alone would collapse forty assertions of P into one node and destroy the discourse counts | authored; `anchored_in` a source span. **Correction/continuity lifecycle unstated** — gap §2.9 (a) | reads `source`; produces nothing derived | none — belief-inert **by type** | everything in belief | world **§4.2**; kernel §4.1, §6; **G1**, **G6** |
| `assessment` | **derived** — an immutable derived output with no revision path | **`(analysis-spec identity, run identity, proposition identity)`** — a key over the derivation's inputs, not a content hash. `rule_bindings` reaches it through `run` | minted by derivation; never revised; standing subtractable by `retraction` | reads spec, run, proposition; produces the **assessment facet** | belief (member 1); admission | location; ~~alias~~ *(alias dropped 2026-08-08 — no label is stored, so there is no alias dimension to be inert in; world address ruling §4)*; availability-with-copy-held | world §4.2; kernel §4.2.1, §5.1; comp §5.1; **G2b**, **G2c** |
| `analysis-spec` | authored, frozen pre-run | **content identity**, frozen; immutable by construction | authored → **frozen**. The freeze also resolves `rule_bindings`, refusing on ambiguity | declares inputs, parameters, nondeterminism contract, interpretation and equivalence rules; `targets` a proposition | eligibility via **G2a**; belief transitively via assessment identity | — | world §4.2; comp §4.2a; 5b §6; **G2a** |
| `run` | executed through the boundary | **content identity of the execution closure — recipe + result + occurrence**; the occurrence's minted **event token** is what keeps two identical executions distinct. Moves when **any** closure member changes | begin is **refused** without an already-frozen spec identity, which is recorded first; recipe frozen pre-execution; result and occurrence recorded after | reads datasets by role (`observes`, `reads`, `transforms`), code, environment, workflow definition, parameters, `rule_bindings`; produces outputs manifest and a **nested** boundary receipt | eligibility (≥1 `observes`); belief transitively | availability **in this checkout** while a controlled copy remains held | world **§4.2**; comp §4.1, §4.2, §7.1; **R2**, **R5**; kernel **G2a** |
| `verification` | **derived** comparison of two runs, immutable | content identity over **(ordered run identities, equivalence-rule identity, comparison-report identity, scope-derivation rule identity, scope, verdict)** — the report's digest is what makes two differently-evidenced verifications two nodes | immutable; superseded by a later verification naming the failure it supersedes; **or** cleared by a standing retraction | reads two runs, the frozen equivalence rule; produces admission input | admission (fail-closed); belief (member 3) | location; ~~alias~~ *(alias dropped 2026-08-08 — no label is stored, so there is no alias dimension to be inert in; world address ruling §4)* | world **§4.2**; kernel §3.3; comp §7.3, §7.3b; **G8**, **R4**, **C6** |
| `dataset` | authored (acquired) or derived (`produces`) | **content identity** over the **dataset basis projection** — every declared resource's digest as `<algorithm>:<hex>`, deduplicated, sorted, newline-joined and hashed; *restated 2026-08-09: this cell said "manifest/content hash", which named no canonical derivation and so let the fold go unruled — the projection excludes names, sizes, order and repetition (admission ramp §6.2; world §4.2; **R23** as amended)*. Provider identifiers and accessions are **authority-identifier fields**, never the basis — *restated 2026-08-08: they were called aliases, and there is no alias; `programme` and `release` are fields carrying authority identifiers, rendered through the pinned snapshot (world address ruling §4.1, §6)* | produced by a run; carries a stamped descendant-side **lineage basis**, tagged `single(route) \| conflict([route])` | read by runs under a role; carries facets, incl. `empirical-observation` | eligibility (held-ness + facet); belief (members 4, 5) | availability in this checkout **while a controlled copy remains held**; facet addition leaves the **address** unchanged (**D2**) | world §4.2; kernel §2.2, §4.1; comp §5.2, §7.1; **R5**, **D2** |
| `source` | authored record in a corpus | **normalized external identifier** — DOI, PMID, ISBN, accession. A work's identity is issued by the world, not computed by us | authored; `member_of` a dataset (the corpus **is** a dataset) | read by extraction | none directly — only through `source-assertion` | everything in belief | world **§4.2**; kernel §4.1, §4.3 |
| `retraction` | authored, attributed, immutable | world address; **its identity covers its target's identity** — banked as what makes cycles unconstructible, an argument **ρA9 replaces** | additive: the target stays byte-identical and resolvable. A counter-retraction removes **one** retraction from standing | reads its target; produces a standing subtraction | standing → admission → belief (member 6) | location; ~~alias~~ *(alias dropped 2026-08-08 — no label is stored, so there is no alias dimension to be inert in; world address ruling §4)* | correction §3, §4; **C1**, **C6**, **C10** |
| `instrument-certification` | **content-derived**, no event token — a derived demonstration on the `verification` precedent | content identity over **(contract identity, discriminated subject, implementation content identity, witness evaluations)**; the rule identity inside carries the fixture-set identity | re-deriving unchanged is **idempotent**; a byte-identical re-mint of a retracted certification **stays retracted**. Withdrawal is by **retraction**, corrected by **counter-retraction**; under a **successor cut it is a different record**, so recertification-after-amendment is a new act, never a toggle | certifies executable instruments, never authored lineage claims | rule-binding resolution; verification scope evidence | — | 5b §7.1, §7.2; world §4.2; N-table |
| `coreference-attestation` | authored, attributed, immutable — added 2026-08-08 (`2026-08-08-world-address-ruling.md` §5.1) | content identity over (**sorted endpoint pair**, **stance**, **actor**, **grounds**, **minted event token**) — the `retraction` shape; sorting makes `{A,B}` one identity regardless of authoring order | additive. A negative attestation **offsets** the pair's derived balance rather than retracting the positive one; both records stand. `retraction` is unused unless individual-attestation invalidation becomes necessary | reads its two endpoints; produces a **derived** balance — `Σ stance` over distinct `(endpoints, stance, actor, grounds)`, the event token deliberately outside the key so duplicate submissions preserve provenance without manufacturing weight | **none** — closure is a query-layer operation and rewrites no stored reference, identity or belief input (§5.3 there) | everything in belief; attester class, which carries **unit weight** for human and agent alike | world §4.2; **W15** |
| `holdings-observation` | minted by an act — a pure dereference or a managed mutation recording its captured post-state (holdings design §3) — under whatever orchestration (acquisition, audit, a move, deletion) runs it; added 2026-08-10 | content identity over the §2 facet under `science.holdings-observation.v1` — location, outcome, `expected`, observer, instrument, minted **event token**, `observed_at`, `supersedes` as a deduplicated sorted reference sequence | append-only; revised by **supersession only** — a later record names its predecessors; never expired by age | reads the bytes it dereferenced; produces the active/blocked sets and coverage projection the dataset admission state derives from | admission (heldness under a declared coverage) → belief transitively | `observed_at` (recorded, never read by a derivation); location of the *record*; everything in belief | holdings design §2–§5; **H1–H4** |
| `act-report` | minted only by the boundary — the terminal record of one opened operation (`acquisition`, `audit`, `import`, `re-check`, or a run attempt that minted no `run`), or the pre-intent refusal record of a run request rejected before an operation can open (act-report design §2–§3); added 2026-08-11 | content identity over the whole facet under `science.act-report.v1` — operation kind, the report occurrence's minted **event token**, actor, observer, instrument, timestamps, and `entries` as a canonical sequence, order identity-bearing | immutable; **never superseded**, retained — no ordinary API edits, supersedes, or deletes one | records member acts and their outcomes in per-kind native vocabularies; a finding is citable as **(act-report ref, entry index)** | nothing — inert by type: no eligibility predicate, no admission derivation, no belief closure member, no coverage projection | everything in belief; `opened_at`/`closed_at` (recorded, never read by a derivation); referenced products retain their own semantics | act-report design §2–§5; **T1–T8** |

### 2.2 Relation signatures and relation instances

Relations are not a sort of object; they are the edges of a configuration. Two
things must be inventoried separately, because they bear different disciplines.

A **relation signature** is a closed predicate over kinds, owned by `science` and
never redefined by a domain. The kernel's signatures:

```text
SourceAssertion ──asserts | denies | hypothesizes──▶ Proposition
Assessment  ──assesses──▶ Proposition          (the only belief-bearing edge)
AnalysisSpec──targets────▶ Proposition
Assessment  ──produced_by──▶ Run
Verification──verifies───▶ Assessment          (also ──replays──▶ Run ×2)
Run         ──executes───▶ AnalysisSpec
Run         ──observes───▶ Dataset             (empirical-observation facet required)
Run         ──reads──────▶ Dataset             (confers no eligibility, in any quantity)
Run         ──transforms─▶ Dataset             (lineage input; confers no eligibility)
Run         ──produces───▶ Dataset
SourceAssertion──anchored_in──▶ Source         (span-level)
Source      ──member_of──▶ Dataset             (the corpus is a dataset)
*           ──supersedes──▶ *                  (same-kind succession)
Retraction  ──retracts─────▶ EligibleTarget    ┐ adopted as-is into the normative
Retraction  ──grounded-in──▶ Ground            ├ relation vocabulary at the first
Retraction  ──succeeded-by─▶ Record            ┘ cut (5b §7.7, closing 5a §9)
```

**The three adopted names are hyphenated, and all three originate from
`Retraction`.** Both points are load-bearing: predicate matching is exact string
equality, so `grounded_in` is simply a different predicate from `grounded-in`
and would match nothing; and typing the latter two from `*` would let any record
ground or succeed anything, which 5a's fields do not permit — `grounds` and
`successor` are fields *of a retraction*.

`derived_from` is a **view** over `produces ∘ transforms` and is never a stored
edge — a distinction M₀ must keep, because a view has no instance identity.

**A relation instance has no identity of its own.** It is a stored occurrence
*embedded in* the source node, and it is committed by that node's content
identity — which is why editing an edge moves the node, and through it the
corpus-state identity, with no separate edge commitment anywhere. Predicate
matching on instances is **exact string equality** over a free string, a
different object from the proposition's `predicate` field (§2.9 (d)).

The tuple `(source live id, position, predicate, unresolved target)` is *not*
that identity: it is the shape of an **unresolved traversal entry** (substrate
§5) — what an adapter reports when a step fails to resolve. Its first two
components exist so a finding can say **whose** edge dangled, since
`(predicate, target)` alone deduplicates `X ─cites→ M` with `Y ─cites→ M`;
entries are totally ordered by `(source id, position)`. The first draft
transcribed a diagnostic shape as an identity.

**Effects are indexed by signature, not by "relation instance".** The signatures
carry different dependencies, and a single row for all of them would be the
roster this system's doctrine forbids:

| signature | what it affects | banked |
|---|---|---|
| `assesses` | the **only** belief-bearing edge; gates aggregation entirely | kernel §4.1; **G1** |
| `observes` | eligibility — at least one is required, and it demands the `empirical-observation` facet | kernel §4.1; **G6** |
| `reads`, `transforms` | confer **no** eligibility in any quantity; `transforms` feeds lineage | kernel §4.1; comp §5.2 |
| `produces` | lineage and the producer sets — belief member 5 | comp §5.2; kernel §5.1 |
| `verifies`, `replays` | admission; belief member 3 | kernel §3.3 |
| `executes`, `targets` | assessment identity's spec and proposition components | world §4.2 |
| `member_of` | corpus membership; discourse counts, never belief | kernel §4.3, §6 |
| `anchored_in` | part of `source-assertion`'s identity basis (the span) | world §4.2 |
| `supersedes` | active/superseded state → admission | kernel §3.3 |
| `retracts` | standing → admission → belief member 6 | correction §4; 5b §7.7 |
| `grounded-in` | the recorded evidence a retraction rests on; a groundless subtraction is **unspellable** | correction §5; **C2**; 5b §7.7 |
| `succeeded-by` | **nothing** — optional and informational, "a pointer for reviewers and diagnostics, **never an implicit redirect**"; nothing resolves through a retraction to its successor | correction §3; 5b §7.7 |

| player | construction | identities | banked |
|---|---|---|---|
| relation signature | authored, in the science base contract | contract identity of the declaring contract; a domain never redefines one | kernel §4.1; D §3.2, §8 |
| relation instance | authored | **none of its own** — committed by the source node's content identity. The stored ref and its **resolution** are recorded separately, which is what makes a deletion visible | substrate §5; kernel §5.1 |

### 2.3 `Sub` — identity-bearing artifacts that are not nodes

Four artifacts carry commitments, enter identities, and are **not** nodes. They
were absent from the first draft, which is why the inventory could not express
what a comparison report does.

| player | construction | identity | why not a node | banked |
|---|---|---|---|---|
| **boundary receipt** | constructed by the boundary | receipt identity; **nested inside the run**, never a node | a receipt names its inputs and holds none of them | comp §4.2, §4.4b; world §5 |
| **comparison report** | derived | **comparison-report identity** — a member of `verification`'s basis. Embeds boundary receipts, conformance results and certification evidence **inline** | the evidence must make two differently-evidenced verifications two nodes; a reference would let it drift | comp §7.3b; 5b §6, §7.6; world §4.2 |
| **lineage basis** | stamped descendant-side at production | tagged `single(route) \| conflict([route])`, the **tag inside the digest** | a durable descendant-side record, not an edge, so deleting the producing run leaves the loss **detectable** | comp §5.2; kernel §5.1 |
| **facet** | authored or derived, per contract | canonical facet digest; keyed to its carrier in belief member 1 | facets stay facets until the promotion trigger — no API retracts, supersedes, or attributes one | D §4, **D10**; kernel §5.1 |

### 2.4 `Proj` — project-scoped records

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| views — `hypothesis`, `question`, `theme`, `topic` | derived | project-scoped **name over a world query** | nothing in belief | world §3 |
| coordination — `task`, `decision` | authored | project-scoped; two projects may both hold a `t068` and always could | nothing in belief | world §3 |
| `note` | authored | project-scoped; **belief-inert prose** | nothing | world §3, §4.2, §4.3; kernel §4.3 |

These need no world identity, so they need no migration. That is a banked
consequence, not an omission.

### 2.5 `Ext` — external referents

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| `term` | **external** | the ontology's own identifier; scope **external** | read as a `reads` input, which confers **no** eligibility in any quantity | world §3; kernel §4.1, §4.3; **G6** |

**`term` is the only sort member living outside the world's identity space**,
and proposition `subject`/`object` are today bare strings that do not reference
it. Gap §2.9 (b).

### 2.6 `Art` — held artifacts

| player | identity | notes | banked |
|---|---|---|---|
| dataset bytes | content identity | **held** = the exact bytes can be produced on demand. Held-ness is a *world* property; availability is a *checkout* property | kernel §2.2; comp §7.1 |
| code bundle | `code_identity` over the content-addressed bundle | recipe member | comp §4.2, §4.4 |
| environment artifacts | `environment_identity` over the manifest of held artifacts | recipe member | comp §4.2, §4.5 |
| workflow definition | `workflow_definition_identity` over the snapshot | recipe member; declared pre-execution | comp §4.2, §6 |
| rule fixtures | **fixture-set identity** | half of rule identity | 5b §6 |

### 2.7 `Con` — contracts and rules

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| **science base contract** | authored, normative **SSOT** | contract identity | belief **unconditionally** — exactly one per semantic derivation; interpreting `assessment`, `dataset` or `assesses` *is* consulting it | D §8, §8.1; **D6**, **D7** |
| **domain contract** | authored, namespaced | contract identity | belief **conditionally** — each contract whose namespaced facets the derivation actually reads. Activated-but-unread domains stay out | D §3.3, §8; **D6** |
| `ProfileSpec` | **compiled** from the contracts | derived | the sole compiled runtime profile; **not** authoritative | D §6; substrate §12 (closed) |
| `KindSpec` | compiled from `ProfileSpec` | derived | input to `Registry.register()` | D §6 |
| **rule** | authored + fixtures | **rule identity = `(symbol, fixture-set identity)`** | binding frozen into `rule_bindings` at freeze; **refused** on ambiguity or an un-held / fixture-failing name | 5b §6; comp §4.2 |
| equivalence rule | declared in the spec, frozen with it | versioned rule id | `(original result, replay result) → passed \| failed \| inconclusive` | comp §7.2 |
| boundary policy | recipe member | names the **scope-derivation rule identity** | governs enforcement; scope is derived, never authored | comp §4.2, §4.4b; 5b §6; **R4** |
| **belief policy** | authored + fixtures | **`PolicyBinding = (policy rule identity, implementation content identity)`** (amended 2026-08-05, belief-policy §2.2 — M₀ transcribed it as *"belief policy version \| authored \| version"*, which this table's own **rule** row above already contradicted: every other fixture-bound rule carries an exact binding, and the one whose output *is* the belief carried a bare version string) | the aggregation rule itself (closure member 7), bound to the implementation that ran it; supplied as a **required argument** per computation | kernel §5.1; belief-policy §2.2, §2.3 |
| normative contract **cut** | derived | cut identity over normative rows + executable case identities — **never** the digest the cut produces | discovery from explicit cut + epoch | 5b §4, §5, §9 |

### 2.8 `Cfg` — corpus and world configuration

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| corpus manifest | authored | `manifest_version: 2`; `corpus_id`, `profile` (one `science_contract` + a `domains` **mapping**), optional `forked_from` | pins the profile a corpus runs under | D §7; packaging §6; world §5 |
| **corpus-state identity** | derived | the **complete canonical manifest projection** + sorted node identities, under `science.identity.v1` | receipt material; **never** a belief-digest member | world §5 (amended 2026-08-04); D §8.1 |
| `corpus_id` | minted, opaque | stable identity; **never** a path, directory name, or project | admission refuses a duplicate | world §5; packaging §4; **X5** |
| admission record | authored | registry record | `known := admission record exists`; `live := known ∧ ¬terminal event`; `present := configuration resolves exactly one corpus carrying the id`. `retired` / `departed` are **terminal** | packaging §4; **X4**, **X6**, **X7** |
| world index (four maps; **membership** changed 2026-08-08 — alias out, coreference in) | **derived** | packaging identity | derived, never authoritative; carries the producers map, retraction enumeration, and certification inventory | world §5; packaging; **W8a** |
| **producer snapshot** | derived | **semantic identity** = producers map + the stable `corpus_id`s of covered corpora | a **required argument** to belief with no default, no implicit "latest", no stored selector — any of those would make belief follow the checkout | kernel §5.1; world §5 |
| log heads / anchors | appended | per-engine-root hash chains at a reserved in-corpus path | subject-bound anchors; five-step verification under an explicit selected subject | L-design; **L1–L13** |

### 2.9 Gaps found while transcribing

Recorded here rather than repaired; repair is ρ's job and only inside the claim
neighbourhood.

**(a) `source-assertion` has an identity basis but no correction lifecycle.**
World §4.2 rules the basis — a hash over `(source identity, anchored span,
stance, proposition identity)` — so the first draft's claim that it had none was
wrong. The gap is downstream of that: because the span and the stance are *in*
the basis, an extraction rerun that shifts either **produces a different node**,
and nothing states whether the earlier one is superseded, retracted, or left
standing beside its replacement. Since extraction is a fallible computation with
a measured 25–40% field-level disagreement rate (kernel limitation 3), a corpus
re-extracted twice yields two populations of assertion nodes with no declared
relation between them, and the discourse counts §6 of the kernel computes are
counts over that population.

**(b) `subject` and `object` are bare strings while `term` exists.** The
referent side of every claim is unbound, and `term` is scoped *external*, so
binding it means proposition semantic identity would depend on an identifier
minted outside the world. This is the first thing M\* must resolve.

**(c) The label family is heterogeneous, and only two of its four classes are
defective.** The first draft's blanket claim — that the family has no
construction method and no identity discipline — is false, and the correction
matters because it changes what M\* owes.

| class | members | construction | verdict |
|---|---|---|---|
| **result codomain** | `verdict`, resolution outcome (`not-present` / `not-available` / `unknown`), standing | ruled: `verdict` is the equivalence rule's codomain (comp §7.2); the three resolution outcomes are ruled distinct and non-collapsible (D §5); standing is defined by recursion (correction §4) | **adequate** |
| **derived label** | `scope`, divergence state | ruled: `scope` is **derived** from how two runs' recipes relate, never authored, with `not-certified` as the floor (comp §7.3, **R4**); divergence is computed, never authored (**G5**) | **adequate as construction** |
| **ordered measure** | `identification_strength`; `scope` wherever it is *compared* rather than matched | **defective** — no order is defined. `identification_strength`'s own definition places five values on a continuum and one (`analogical`) off it, so it is not totally ordered; and admission tests `scope` for equality with `clean-environment`, so nothing yet needs an order the design does not supply | **defective** |
| **semantic vocabulary** | `predicate`, `claim_layer`; `polarity` as currently coupled | **defective** — no term identity, no extension rule, no owner, and three of these feed proposition semantic identity. `polarity`'s admissible values are gated by a hard-coded three-element roster over `predicate` | **defective** |

So the finding is not "the labels are unformalized" but: **result codomains and
derived labels have adequate contracts; ordered measures lack their orders; and
semantic vocabulary lacks everything.** M\* owes the last two.

**(d) `predicate` names two unrelated objects.** The relation instance's
`predicate` is a free string matched by exact equality (substrate §5); the
proposition's `predicate` is a semantic-vocabulary term inside an identity hash.
They share a word, a field name, and nothing else. M\* must not let the term
contract leak onto edges.

## 3. M₀ — the system-wide model

### 3.1 Commitments

Every identity in §2 has the same form:

```text
Iᵢ(x)  =  H( tagᵢ ‖ encode(πᵢ(x)) )
```

with `encode` the canonical encoding fixed by `science.identity.v1`, and `tagᵢ`
a domain separator. The property claimed is **not** mathematical injectivity of
`H`: it is that `encode ∘ πᵢ` is injective **on admissible values**, and that
`H` is domain-separated and collision-resistant. Every guarantee row that reads
"assert the digest changes" is a claim about `πᵢ` composed with a
collision-resistance assumption, and M₀ states it that way.

### 3.2 Transitions

Refusal is a **value**, so the transition is a function into a sum, not a
relation between configurations:

```text
Dom(step)  ⊆  Ω_valid × Action                         (§3.3 defines Ω_valid)

step   : Dom(step)  →  Ω_valid  +  Refused
audit  : Ω          →  Validated(ω ∈ Ω_valid)  +  Findings
```

**`audit` is not a `step`, and typing it as one was a contradiction.** `step`
accepts only `Ω_valid`, while `audit`'s entire purpose is to inspect a
configuration whose validity is *unknown* — including one a raw write pushed
outside `Ω_valid`. So `audit` takes all of `Ω`, returns either a validation that
the configuration is in `Ω_valid` or the findings explaining why it is not, and
**mints nothing** (5b §7.6): it is read-only, it produces no `ω′`, and it never
repairs. Detection stays split from correction.
*(Amended 2026-08-11, the act-report design §4: the type is unchanged and the
evaluator still mints nothing — the `audit` operation's inert act-report is
published by the boundary wrapper that ran the evaluator, under the wrapper's
own operation intent.)*

A relation `ω →ᵃ ω′` cannot simultaneously make refusal a value, because a
refused act has no `ω′` to relate to — the first draft wrote both and meant only
this one. `Refused` carries the reason; nothing in `Ω` records that an act was
attempted unless a record makes it so, which is §8.7's territory.

**`step` lands in `Ω_valid` wherever it is defined,** which is a preservation
claim and not a repair claim: a sanctioned action applied to a valid
configuration yields a valid one or refuses. It does not say a sanctioned action
can rescue an invalid configuration, and it says nothing about states reached
another way.

**`Dom(step)` is a subset, and the subset is not an evasion.** Writing
`step : Ω_valid × Action → Ω_valid + Refused` would claim that **every**
sanctioned action on a valid configuration has a defined result — and **ρO5 says
one class does not**. The excluded class has to be named precisely, because the
obvious phrasing excludes too much:

> **Excluded from `Dom(step)`:** a `merge` that would change some retraction's
> **exact target tuple**, and therefore that retraction's content identity.
>
> **Amended 2026-08-08 — the excluded class is now empty** (`2026-08-08-world-address-ruling.md` §5.3,
> §5.4). Structural merge is **retired**. Its two successors move no target
> tuple: `consolidate` requires **one canonical address** and performs **no
> redirect and no inbound rewrite**, and coreference is an **additive
> attestation** whose closure expands queries and rewrites no stored reference.
> A **rename** under world §4.4 does not move one either — nothing rewrites the
> retraction's stored tuple, and the old address keeps resolving through
> `deprecated_ids` (W5a). So no sanctioned action can change a retraction's exact
> target tuple, `Dom(step)` is **total over `Ω_valid × Action`**, and **ρO5
> closes** — *by its subject being retired, not by its cascade being ruled*. Raw
> writes are unaffected: they were never `step`s.
>
> The paragraphs below are kept as the record of why the exclusion existed.

**Not** every merge involving a retraction target. Consolidating two
**equal-basis replicas** of one retraction — world §4.3's `duplicate location`,
*one identity, two corpora* — changes physical multiplicity and nothing else: no
target tuple moves, no content identity changes, and a counter-retraction naming
that retraction still names the same identity afterwards. There is no cascade to
bound, so that merge is squarely **inside** `Dom(step)`, and ρA10 requires it to
succeed. Excluding it would have made ρA10 and `Dom(step)` contradict each
other — ρA10 saying the consolidation must succeed while the transition type
said it had no defined result.

What is excluded is the case with a real cascade: a merge that rewrites some
retraction's target, re-minting it and everything naming it (limitation 11).
Those pairs have no ruled outcome today — not a preserved state, not a refusal,
an *open question*.

The distinction matters because `Refused` is a **value the system produces**
about a case the design has ruled on. Folding an unruled case into it would
report a design gap as a runtime decision — the system saying "no" where in fact
no one has said anything. Design-undefined behaviour is not runtime refusal, and
`Dom(step)` is where the difference is written down. Closing ρO5 is exactly the
act of enlarging `Dom(step)` to cover those pairs.

**Raw mutation is not a `step`.** Writing bytes past the boundary is not an
`Action` and has no transition here — that is what makes it *raw*. It can
produce a configuration outside `Ω_valid`, and the model's answer is not a
wider `step` but **audit**: audit establishes that a configuration is valid, or
emits findings naming why it is not. The readings are never invoked on a
configuration whose validity has not been established (§3.3).

| transition | precondition | banked |
|---|---|---|
| `write` | kind and facet validation under the compiled profile | substrate §6; D §6 |
| `freeze` (spec) | resolves `rule_bindings` to exactly one held conforming implementation; **refuses** on ambiguity or a fixture-failing name | 5b §6 |
| `begin` (run) | for **assessment runs**: **refuses** without an already-frozen spec identity, and records it before any other observation; a `dataset-production` run carries no spec and opens the **operation intent** instead *(amended 2026-08-11, the act-report design §3.2)* | kernel **G2a** |
| `derive` | mints assessments, verifications, index maps. Divergence is **computed, never authored** | kernel **G5**; **W8a** |
| `supersede` | a later record naming what it supersedes | kernel §3.3, §4.1 |
| `retract` / `counter-retract` | additive; target stays byte-identical and resolvable | correction §4; **C1** |
| `admit` (corpus) | **refuses** a `corpus_id` already admitted | packaging §4; **X5**, **X7** |
| `retire` / `depart` | **terminal** — no API returns a corpus to `live` | packaging §4; **X6** |
| `move` | changes location only | world **W5** |
| `import` | admits a bundle; validates **the bundle together with the resolved world context**, and refuses one admitting no topological order (ρA9) | correction §3; **M3** |
| ~~`merge`~~ | ~~authored coreference; **every reachable inbound reference is rewritten**, which is why it — unlike `write` — can redirect an existing edge (ρA10)~~ — **retired 2026-08-08** (`2026-08-08-world-address-ruling.md` §5) | world §4; **W4** |
| `consolidate` | **requires one canonical address**; unions outgoing relations, preserves divergent lineage bases, selects `uid` continuity. **No redirect, no inbound rewrite** — added 2026-08-08 | ruling §5.4; **W16** |
| `attest-coreference` | mints a `coreference-attestation`: additive, attributed, unit-weighted, endpoints typed. Changes **no** existing record; the pair's balance is derived and the closure it activates is a **query-layer** expansion — added 2026-08-08 | ruling §5.1–§5.3; **W15** |

`import` and `merge` were absent from the first draft's inventory and were both
load-bearing under ρA9 and ρA10 — `import` because it is the one path admitting
records with no history, `merge` because it was the one path that *rewrote* edges
rather than adding them. **Since 2026-08-08 no transition rewrites an edge**
(`2026-08-08-world-address-ruling.md`): `import` alone carries the ρA9 obligation, and `merge`'s
successors are additive. That is one fewer route to reason about, not one fewer
check — `import` still validates acyclicity over the bundle union the resolved
world context, and **M3** still owns that oracle. `audit` has left this table: it is not an
`Action` and appears in the signature above instead.

**These are not a group action.** Terminal transitions are noninvertible,
refusals make several partial, and admission refuses duplicates. M₀ therefore
takes **observational equivalence per reading** as the primitive and derives the
quotient intuition from it, rather than assuming algebraic structure the system
does not have.

### 3.3 The four readings

```text
Ω_valid    =  { ω ∈ Ω | ω is structurally well-formed  ∧
                        retraction_graph(ω) is a DAG }        (§8, ρA9)

standing   : Ω_valid × Target       → { standing, subtracted }
admission  : Ω_valid × Assessment   → Adm
eligible   : Ω_valid × AssessesEdge → Bool
B          : Ω_valid × Q            → Belief  +  NotAvailable  +  Refused
```

**The readings are defined over `Ω_valid`, not over all of `Ω`.** `Ω` is any
finite configuration, and **three** paths can change the retraction graph: a
boundary `write`, an `import`, and a **raw write** that bypasses both. *(Four
until 2026-08-08, when `merge` retired — `2026-08-08-world-address-ruling.md` §5. Its successors add
records and edges but rewrite none, so neither can close a cycle by redirection;
**W15** asserts exactly that for coreference and **W16** for `consolidate`.)* The
first two are `step`s and produce only `Ω_valid`, and since the ρO5 exclusion is
now empty they do so **everywhere `step` is defined, which is everywhere**
(§3.2, ρA9, ρA10). A raw write can produce a configuration whose
retraction graph has a cycle, and over such a configuration `standing` has no
terminating definition at all.

**Two conditions, not one.** Acyclicity alone is too weak to carry totality: a
raw-written configuration can be perfectly acyclic and still structurally
malformed — a relation instance whose target does not resolve, a record whose
stored identity disagrees with its payload, a required member absent. Declaring
the readings total over an acyclic-but-malformed configuration would be the same
overclaim in a smaller place. So `Ω_valid` carries **both** conjuncts:
structural well-formedness, which is what the write boundary and every identity
recomputation already enforce, **and** acyclicity of the retraction graph, which
is ρA9's addition. Only the second is new here; the first was assumed
throughout and never written down.

Restricting the domain is the honest repair, and it is cheaper than the
alternative. The alternative is to make `standing` total over `Ω` by giving it a
`malformed` arm — which forces every reading to carry cycle detection, forces
every caller to handle an arm that only a bypass can produce, and makes the
readings responsible for a condition the boundary already prevents. Instead:
**audit classifies a raw cycle as malformed before any standing or belief
evaluation**, on exactly the terms the model already uses for every other
raw-write defect. A configuration outside `Ω_valid` is not a state whose belief
is unknown; it is a corpus with a detected integrity fault.

`B` is **total** into that sum. `B(ω,q)↓` is written throughout for *"lands in
the `Belief` arm"* — not for definedness in the partial-function sense. The
distinction matters in §4.3: a `def` dependency does not make `B` undefined, it
routes the result to `NotAvailable`, which is a value the caller receives and can
act on rather than an absence.

`Target` is **not** all of `Rec`. Retraction targets are the eligible node and
route targets only: a retraction naming a note, or a proposition, is
**unspellable through the boundary** (**C10**). Typing `standing` over `Rec`
would make ill-formed targets expressible and then require a validator to
reject them — defensive where the type should refuse.

**`admission`** is an explicit reduction, and the unordered codomain it reduces
into must be defined before it can be named:

```text
Adm  =  { not-admitted,  invalidated,  admitted }        an unordered three-element set

admission(ω, a)  =  let V = active verifications of a in ω               (§3.3 lifecycle)
                    if  ∃v ∈ V.  verdict(v) = failed           → invalidated      (1)
                    if  ∃v ∈ V.  verdict(v) = passed
                        ∧ scope(v) = clean-environment          → admitted        (2)
                    otherwise                                   → not-admitted
```

**`Adm` carries no order**, and the first draft's `not-admitted < invalidated <
admitted` had no banked justification — it is neither an information order (an
invalidated assessment is not "more informative" than an unadmitted one) nor a
permissiveness order. What the lifecycle rules is a **precedence between
clauses**: clause (1) is tested before clause (2), which is the whole content of
"a passing sibling never clears an active failure" (**G2c**). `failed` is
absorbing as a **reduction rule**, not as a lattice fact.

The reduction is over the **fixed set of active verifications**, so it is a
function of that set and nothing wider; it is *not* monotone over record-set
inclusion once retractions and counter-retractions exist, and M₀ claims only the
narrower statement.

**`standing`** is defined by structural recursion, not as a least fixpoint: an
input's standing is subtracted iff at least one **standing** retraction targets
it, and the operator is **antitone** through that negation. What makes the
recursion well-founded is banked as *a retraction's identity covers its target's
identity, so a cycle would require two records each containing the other's
digest* (correction §4) — transcribed here as M₀ states it, and **replaced by
ρA9**, which finds that argument invalid and substitutes the retraction graph's
**acyclicity invariant** over `Ω_valid`. Either way the recursion is unique and
structural, not Knaster–Tarski.

**`eligible`** is kernel §4.1's predicate: the assessment's run has at least one
`observes` input, all inputs are held, and the assessment is `admitted`. `reads`
inputs never confer eligibility, in any quantity.

**`B`**'s codomain has three arms, and the latter two are banked, not invented:
removing the corpus holding the records yields *"belief **not computable
here**"*, which is a computability state and not a belief that happens to be
unchanged — "reporting an unchanged belief in that situation would assert a
recomputation nobody performed" (comp §7.1).

**Superseded 2026-08-05 by belief-policy §4. The signature above stands as M₀'s
transcription and is not rewritten**, per §2's rule that M₀ records the banked
system as it was. The middle arm is now **`NoBelief(reason)`**, not
`NotAvailable`:

```text
B : Ω_valid × Q → Belief(value, belief_input_digest, policy_binding)
                + NoBelief(NoBeliefReason)
                + Refused(reason)

NoBeliefReason = Unavailable(PolicyUnheld | FixturesUnheld
                            | InputUnheld | CorpusAbsent)
               | NoEligibleAssessment
               | NoDirectionalOutcome
```

The arity is unchanged — three arms, with reasons as discriminants inside one of
them — so §3.4's laws and every row keyed on the `Belief` arm survive
untouched. What the widening fixes is that `NotAvailable` is **computational**
here, exactly as this section says, while an empty eligible set is a computation
that **succeeded** and found nothing. Filing the second under the first collapses
semantic absence into local unavailability: one is repaired by mounting a corpus,
the other by doing science. `NoEligibleAssessment` is deliberately named for what
is computable and **not** `Unassessed`, because nothing distinguishes *not yet
assessed* from *outside the empirical route* — `ClaimLayer` cannot decide it,
since `eligible` above reads the run's `observes` edge and not the claim.

### 3.4 Laws

| law | statement | tested by |
|---|---|---|
| **well-definedness** | each reading is a *function* of the configuration — one value, no ambient input | **G3** (recompute from the named closure alone; assert identity) |
| **order-independence** | `status : 𝒫(RegistryRecord) → RegistryStatus` — registry status is a function of the record **set**, so no arrival order can appear in it | **X6** — *"assert every status is invariant under record arrival order"*, the implementation oracle for that typing |
| **observational invariance** | `ω ∼_B ω′ ⟹ B(ω,q) = B(ω′,q)`. Declared inert dimensions: location, ~~alias~~, display fields, availability-with-a-copy-held — *alias dropped 2026-08-08 (`2026-08-08-world-address-ruling.md` §4): a label is rendered on read and never stored, so there is no alias dimension to be inert in. The cited rows are unaffected — **W5** and **D2** carry no alias arm, and kernel **G3**'s alias mutation is deleted without replacement* | **W5**, **R5**, **G7** (converse half), **D2** |
| **commitment sensitivity** | a change to a declared semantic projection changes the encoded commitment, up to negligible collision probability | **G3**, **L4**, **D5** |
| **well-founded recursion** | `standing` terminates on every `ω ∈ Ω_valid` | argued correction §4 by content-address containment — an argument **ρA9 invalidates and replaces** with the retraction graph's **acyclicity invariant**; **no banked row tests it directly** (C5 tests chain-not-toggle and sibling-awareness), which is why **M3** exists |
| **fail-closure** | `admission` reduces into an **unordered** three-element codomain under **failure-first precedence** | **G2c**, **G8**, **C6** |
| **declared limit** | a *negative* row: the system provably **cannot** detect something, tested so the positive half is not over-read | **G4**, **G2a**, **G8** negatives; §8.7 |

**Order-independence is a typing, not an equation.**

```text
status : 𝒫(RegistryRecord) → RegistryStatus
```

Writing it as `status(R) = status(R′) whenever R = R′` would be reflexivity, not
a law — it holds of every function whatsoever. The content is entirely in the
**domain**: `status` takes a *set*, so there is no place in its input for an
arrival order to sit, and independence follows from the type. X6 is the
implementation oracle for that typing, varying arrival order and asserting the
statuses agree.

M₀ claims nothing wider. In particular it does **not** claim `reduce(h) =
reduce(perm(h))` over whole configurations: that would assert equality of the
entire state under reordering, which nothing banked guarantees and which
occurrence-bearing records visibly violate — a `run` carries a minted event
token and `started_at`, so two histories differing in order do not produce equal
configurations even when they produce equal statuses. A system-wide history law
would need histories modeled, which M₀ does not do and does not yet need.

**Well-foundedness is argued in prose and tested by no row.** It is what makes
`standing` a definition rather than a description. Correction §4 argues it by
content-address containment — an argument **ρA9 finds invalid and replaces**
with the retraction graph's acyclicity — but either way no banked row tests
termination: C5 tests chain-not-toggle and sibling-awareness, which is behaviour
*given* that the recursion terminates. **M3** is that row, and finding the gap
took only the act of naming the laws separately from the rows.

The **declared-limit** class is why the taxonomy needs seven entries rather than
six. G4's row does not assert a property of the system; it asserts that
discarding a failed replay attempt is undetectable, and tests that the system
cannot detect it. Classified as well-definedness or invariance it would be
misfiled; dropped, §8.7's recorded-history limit would lose its carrier.

Note that packaging §4's phrase *"every predicate is monotone in the record
set"* is doing the work of **order-independence**, not monotonicity. `live :=
known ∧ ¬terminal-event` is anti-monotone — adding a record removes `live` — and
the conclusion the sentence draws (two registry copies with the same records
agree regardless of arrival order) follows from each predicate being a *function
of the record set*, which is what M₀ states.

## 4. The typed dependency graph and the factorization check

### 4.1 Two graphs, and only one is well-founded

The **type-level** dependency graph is *not* a DAG: `standing` depends on
`standing`, and `verification` supersession depends on `verification`. Recursion
at the type level is normal and carries no obligation.

A **concrete derivation's instance graph** is well-founded exactly where the
banked rules force it — the retraction graph being the clearest case, banked as
content-address containment (§3.3) and carried under ρA9 by the acyclicity
invariant that C10's resolvable-target rule maintains. M₀ therefore records the well-foundedness
*argument* per recursive edge, not a blanket acyclicity claim. An edge with
recursion at the type level and no banked argument at the instance level is a
gap; none was found in the four readings.

### 4.2 One dependency relation is three

A single `Dep₀` conflates three edges that answer different questions, and the
first draft's check was unsound for exactly that reason — it compared a mixed
edge set against a digest and concluded about belief.

```text
x →ˢᵉᵐ r     semantic read   — x's value participates in computing r's value
x →ᵇⁱⁿᵈ r    binding         — x's identity is committed in r's projection
x →ᵈᵉᶠ r     arm selection   — x's state determines which arm of r's codomain is reached
```

**`def` selects an arm; it does not withhold a value.** Every reading here is
total — `B` always answers, and `NotAvailable` is one of its answers. The first
draft called this edge "definedness … whether `r` is defined at all," which
contradicts `B`'s totality two sections earlier. What a `def` edge decides is
whether the reading lands in its **primary computable arm**.

They are independent: an input can be `sem` without being committed (read but
uncommitted — the defect class G3 exists to forbid), committed without being
`sem`, and `def` without either.

**The law is factorization, not edge-set inclusion.** `sem ⊆ bind` is not
well-typed: a semantic value is almost never committed *as the same object*.
Dataset bytes participate semantically; what is committed is their content
identity. An inclusion between a set of value-dependencies and a set of
identity-members compares two different kinds of thing. The statement that does
type is:

```text
D_B   =  { (ω,q)  |  B(ω,q) ∈ Belief }        the belief arm's preimage

κ_B   :  D_B  →  CommittedProjection          the complete canonical committed projection
B|D_B =  B̄ ∘ κ_B                              factorization
I(B)  =  H( tag_B ‖ encode(κ_B(ω,q)) )  =  belief_input_digest,  for (ω,q) ∈ D_B
```

`κ_B` is typed over **`D_B`, not `Ω × Q`**. Outside the belief arm there is no
claim that the projection can be computed at all — that is precisely what
`NotAvailable` reports — so defining the digest there would assert a computation
nobody performed. The factorization is a statement about `B` restricted to
`D_B`, and every claim below is scoped to it.

Equivalently: **equal committed projections must yield equal beliefs.** That is
what G3's "recompute from the named closure alone; assert identity" asserts, and
it fails exactly when some `sem` dependency is not determined by `κ_B`.
Collision resistance is what connects `κ_B` to the digest — the factorization is
the property; the digest is its representation.

**Commitment sensitivity is a separate law, not the converse of this one**:
changing an admissible semantic dependency must change `κ_B`. Factorization
alone is satisfied by a constant projection; sensitivity alone is satisfied by a
projection that commits noise. G3's row tests both halves, which is why its
mutation battery has a positive and a negative arm.

The `sem` / `bind` / `def` vocabulary remains useful as **diagnostic shorthand**
for classifying an edge — but only once the projection mapping each `sem`
dependency to its committed representative is written down, which §2's entries
do not yet carry.

**The economy law is withdrawn.** The draft's `bind ⊆ sem ∪ def` would forbid
**intentional structural commitments**, which this system deliberately makes:
the assessment identity binds a facet *to its derivation*, defeating the
permutation attack even when two derivations yield byte-identical facet values;
a coverage declaration binds the meaning of an **absence**. Neither changes the
belief value nor its definedness, and both are necessary. Rather than invent a
fourth edge type to rescue the formula, M₀ drops it — §5's classification does
not need it.

**The bound, stated plainly: an edge omitted from both the declarations and the
closure is invisible to this check.** It is a consistency check between two
declarations, not a proof about executed code — a derivation that reads an input
nobody declared satisfies every check here. Closing that gap needs a different
instrument, recorded as an M obligation: an **undeclared-read oracle** that
instruments a derivation to read an input it did not declare and requires
conformance to fail.

### 4.3 Running the factorization check on `B`

The projection `κ_B` is G3's eight members (kernel §5.1). The semantic
dependencies are what §2's entries read, transitively. The middle column names
the **committed representative** of each — the identity or projection through
which the value reaches `κ_B`, since almost none of them is committed as itself.

| semantic dependency of `B` | committed member of `κ_B` it is represented by | factors |
|---|---|---|
| assessment facet values, keyed to their carrier | 1 — keyed assessment facets | ✅ |
| what is believed | 2 — proposition semantic identities | ✅ |
| active verifications `(scope, verdict, supersession state)` → admission | 3 | ✅ |
| `observes` bytes | 4 — `observes` content identities | ✅ |
| ancestry → independence | 5 — lineage snapshot | ✅ |
| retractions + coverage declaration → standing | 6 — retraction enumeration | ✅ |
| the aggregation rule | 7 — policy binding (`belief policy version` until 2026-08-05) | ✅ |
| consulted contracts → interpretation | 8 — profile contracts | ✅ |

Every verified semantic dependency of `B` factors through `κ_B`.

**Two further dependencies sit deliberately outside that table**, and the
findings below are about exactly why. Neither is an established semantic
dependency: one is bound without being shown semantic, the other's edge type is
undecided. Listing either as a row would let an unproven claim inherit a ✅, and
the first draft did precisely that.

The first draft additionally claimed minimality, on the grounds that each of the
eight members is reached by some declared dependency. That argument compared the
wrong objects — it ran before `sem`, `bind` and `def` were distinguished at all —
and the law it was aiming at is withdrawn as unsound (§4.2). Nothing replaces it
here.

**Finding (a) — a complete binding path that nothing declares.** A run's
non-`observes` inputs *do* move the digest, by three hops no design states
together: `inputs` is a recipe member carrying `(role, dataset address, content
identity, exclusion certification?)` for **every** role (comp §4.2); a run's
identity moves when any closure member changes (**R2**); an assessment's identity
is `(spec, run, proposition)`, and member 1 keys facets by assessment identity
(kernel §5.1).

**What this establishes is a binding path, not a semantic one.** Swapping the
ontology a run read moves `κ_B`. It does *not* show that the swap changes belief
— the stored result and the assessment facet could be byte-identical — and no
argument here is entitled to that stronger claim. Over-binding is the safe
direction, and it is what the recipe buys.

The binding is nonetheless **fragile**: it rests entirely on that recipe member
being role-partitioned rather than `observes`-only, and nothing near G3 says so.
Narrowing it — a local, reasonable-looking edit — would drop those inputs out of
`κ_B` without touching G3's row, its mutation test, or any text mentioning
belief. Candidate M-row, stated at its true strength: *every run input enters the
execution recipe and therefore the assessment's carrier identity.*

**Finding (b) — a genuine choice point, not a transcription.** Held-ness is a
dependency of `B`; the question the first draft never asked is **which edge type
it is**, and the two answers are incompatible.

First, a scope correction: kernel §4.1's predicate requires that **all** inputs
are held, not only `observes` ones. Destroying the last held copy of an ontology
a run `reads` therefore has the same standing as destroying an `observes`
dataset. The first draft scoped this to `observes` and was wrong.

| reading | consequence |
|---|---|
| held-ness is a **`sem`** edge — losing it yields a *different belief value* | **factorization fails**: two configurations differing only in whether the last copy survives share `κ_B`, and therefore share a `belief_input_digest`, while yielding different beliefs. That is a G3 violation, not a qualifier on G3 |
| held-ness is a **`def`** edge — losing it routes the result to `NotAvailable` | factorization survives, and the guarantee reads: **whenever `B` lands in the `Belief` arm, `κ_B` determines it**. `NotAvailable` is the honest answer — a computability state, not a belief that happens to be unchanged |

The first draft chose neither and wrote "G3's completeness is relative to the
locally computable dependencies of `B`". **That formulation is withdrawn.**
Locality is a property of a *holder*, not of the dependency relation; letting it
qualify the relation means the same system has different dependencies at
different checkouts, which makes the model unstable exactly where it must not be.

**Recommendation for ρ: `def`. The mechanism stays open.** Adopting `def` is a
revision, not a transcription — comp §7.1's second row currently reads `sem`,
*"eligibility fails and admission **changes**"* — so ρ must carry that amendment
explicitly, with the guarantees it touches named.

The first draft went further and recommended making loss of the last held copy a
**recorded act**, so that held-ness became an ordinary committed member. That
recommendation is **withdrawn as premature**, for two reasons:

- A local deletion act proves only that *one copy* disappeared. "No copy
  survives anywhere" is a world-wide **negative** fact, and recording it needs
  coverage, authority and discovery semantics — the same machinery the retraction
  enumeration needed, and none of it is designed.
- Routing to `NotAvailable` does not by itself make the case computable. Comp
  §7.1 is explicit that computing it requires a **separately published
  belief-input snapshot** carrying kernel §5.1's members, which the world index
  deliberately does not contain. Choosing `def` decides what the *answer* is; it
  does not supply the ability to compute which answer applies.

So §4 records the choice and leaves the mechanism to §8.

### 4.4 The other three readings

Reported on the same typed basis. `def` columns are stated because two of these
readings are where definedness actually enters.

| reading | factors through its commitment | `def` edges | note |
|---|---|---|---|
| `standing` | ✅ retractions, counter-retractions, coverage declaration | the target must be an eligible target (**C10**) | recursion well-founded — by content-address containment as banked, by the retraction graph's **acyclicity over `Ω_valid`** under ρA9 |
| `admission` | ✅ active verifications only | none | the fixed active set is the whole dependency |
| `eligible` | n/a — `eligible` has no commitment of its own | **held-ness of every input** — finding (b) enters here | this is the reading finding (b) is *about*; `B` inherits it |

## 5. Guarantee classification

### 5.1 Method

**117 rows** across nine frozen tables: G (11), S (9), W (19), R (23), C (10),
X (12), N (10), L (13), D (10). *(Corrected 2026-08-09. These read 113 rows and
W (16): the world address ruling added **W14–W16** to §5.2 on 2026-08-08 and left
the totals behind, and W's count had never included **W5a, W8a and W8b**, which
§5.2 classifies individually. The admission ramp's **G9** is the fourth new row
and the occasion for the recount, not its cause.)*
*(Extended 2026-08-10: the verified-holdings record design banked **H (4)** —
the classified inventory is now **121 rows** across ten tables and **150
assertions**. The assertion count moves with H's arms; the classification is
per assertion, as ever.)*
*(Extended 2026-08-11: the act-report design banked **T (8)** — the classified
inventory is now **129 rows** across eleven tables and **180 assertions**. The
assertion count moves with T's arms; the classification is per assertion, as
ever.)*

Classification is **per assertion, not per row** — 117 rows, 135 assertions — and a row may carry several
labels: many rows state a property in a positive arm and pin its limit in a
negative arm, and those are different classes. **No id is renamed, renumbered or
merged.** This section mints nothing — it labels what is already banked.

§3.4's labels are abbreviated **WD** (well-definedness), **OI**
(order-independence), **OInv** (observational invariance), **CS** (commitment
sensitivity), **WF** (well-founded recursion), **FC** (fail-closure), **DL**
(declared limit). Labels marked **†** are *proposed* in §5.4, not yet part of the
taxonomy; they are used here so the classification is complete and reviewable
rather than half-blank.

### 5.2 The classification

**G — epistemic kernel**

| id | assertions | classes |
|---|---|---|
| G1 | belief output byte-identical under a maximal source-assertion / the `assesses` edge is refused | OInv / RF† |
| G2a | the boundary refuses an unfrozen spec / it records that identity **first** / post-hoc attachment is undetectable | RF† / EO† / **DL** |
| G2b | unheld or unhashed input refused | RF† |
| G2c | admission only at `clean-environment, passed`; a passing sibling never clears a failure | **FC** |
| G3 | recompute from the named closure alone → identity / mutate each member → digest moves, incl. permutation and scope / move an entity → digest unmoved — *the alias-edit arm was **deleted without replacement** 2026-08-08; location alone carries OInv here, and an authority-release bump is not a substitute because under **D6** a consulted release may legitimately move the digest (world address ruling §8)* | **WD** / **CS** / **OInv** |
| G4 | an unreferenced successor to a recorded failure is refused / discarding the attempt is undetectable | RF† / **DL** |
| G5 | divergence is computed; no authored kind exists | CA† + US† |
| G6 | `reads` inputs confer no eligibility in any quantity or QA state | **OInv** |
| G7 | a semantic edit mints a new identity, prior bindings hold, old belief unmoved / a `title` overwrite mints nothing | **CS** + **OInv** / **OInv** |
| G8 | a failing verification invalidates and forces recomputation; cleared only by resolution or standing retraction / deleting it restores admission | **FC** / **DL** |
| G9 | a recorded content identity with no bytes is minted and reads `declared`, never `held` / bytes whose digest disagrees do not promote, and the state is derived rather than stored / matching bytes held anywhere, in or out of the repository, promote alike / the path-exists predicate fails **G9** while G2b, R5 and R10 pass (added 2026-08-09) | **FC** / **CS** + **FC** / **OInv** / **DL** |

**S — substrate consolidation**

| id | assertions | classes |
|---|---|---|
| S1 | closure matches membership-traversal semantics; `directed` not reinterpreted | PC† |
| S1a | the lineage closure shares the algorithm, not the edge semantics | PC† |
| S2 | a semantic edit through the write API mints a new proposition | **CS** |
| S3 | a stale semantic hash is rejected on import / editing fields **and** hash passes | RF† / **DL** |
| S4 | no rename path is reachable from the semantic-change branch | US† |
| S5 | incomplete lineage never certifies independence / the deletion guarantee is scoped | EB† / **DL** |
| S6 | only certified independence confers multiplicity | EB† |
| S7 | eligibility is enforced at both boundaries, including raw writes | PC† |
| S8 | no module outside the write API holds a mutable handle (static) | US† |
| S9 | an audit judges a damaged corpus: construction faults are findings, the remainder is audited, no state identity is claimed | RF† + PC† |

**W — world addressing**

| id | assertions | classes |
|---|---|---|
| W1 | distinct bases never become one node | **CS** |
| W2 | a shared basis establishes coreference mechanically | **WD** |
| W3 | creating a world entity without its basis is refused | RF† |
| W4 | ~~a merge is authored; content is never derived by precedence~~ → **a coreference claim is attributed and additive, and never collapses the graph** — *restated 2026-08-08 (`2026-08-08-world-address-ruling.md` §9); the equal-basis arm re-homes to **W16**, the distinct-basis retraction refusal to **W15**'s cycle arm* | RF† + CA† |
| W5 | a move changes only location — `uid`, identity, belief unmoved | **OInv** |
| W5a | a basis change is ruled by case, never by default | ED† |
| W6 | the four resolution states never collapse | ED† |
| W7 | views see the whole world, not a directory | *unclassified — direct requirement* |
| W8 | no conflict is resolved by precedence | RF† |
| W8a | all **four** index maps are derived, never authoritative — *membership changed 2026-08-08: alias out, coreference in* | CA† |
| W8b | `uid` uniqueness is enforced; its two violations are distinguished | **CS** + ED† |
| W9 | an ambiguous **search term** refuses and names its candidates — *restated 2026-08-08; the subject was a stored alias, and there is no longer one* | RF† |
| W10 | cross-corpus edges are ordinary, not dangling | **OInv** |
| W11 | a world entity is never addressed by a coordination address, or the reverse | US† |
| W12 | renaming a project does not break coordination references | **OInv** |
| W13 | corpus identity is minted, opaque, stable / state identity is over content | **OInv** / **CS** |
| W14 | the address scheme adds unambiguity **by construction** — the only stored values participating in lookup are **canonical addresses, live and retired**, and no presentation value does; labels are rendered, never resolved against | US† + **OInv** |
| W15 | a coreference balance is derived over **typed** endpoints and a **declared coverage**, unmoved by **exact** duplicates and attester-symmetric; closure rewrites nothing, and an unestablished coverage refuses rather than reading as inactive | RF† + **CS** + **OInv** + US† + **FC** |
| W16 | `consolidate` repairs storage and asserts nothing about identity; it preserves a shared `uid` or selects one of two distinct ones, and never mints | RF† + **OInv** |

**R — computation and reproducibility**

| id | assertions | classes |
|---|---|---|
| R1 | an incomplete closure is refused; no `run` node is minted | RF† |
| R2 | the address moves on every closure member; the recipe holds nothing post-execution | **CS** |
| R3 | two executions of one recipe are two runs | **CS** |
| R4 | scope is derived, never authored; it rests on evidence | CA† + RF† |
| R5 | belief does not depend on availability in this checkout | **OInv** |
| R6 | un-replayability creates no verification and moves no state | **OInv** |
| R7 | the two run shapes are structurally exclusive | RF† |
| R8 | the equivalence rule cannot be chosen after outputs are seen | **CS** |
| R9 | `inconclusive` never collapses into `passed` or `failed` | ED† + EB† |
| R10 | runs begin at the most upstream held form | RF† |
| R11 | dataset-production replay is bitwise; forking identity does not cancel the verdict | RF† + **CS** |
| R12 | the boundary refuses a run naming no frozen spec / the bound is pinned | RF† / **DL** |
| R13 | `code_identity` captures what ran, not what was committed | **CS** |
| R14 | identity canonicalization is **injective** and domain-separated | **CS** |
| R15 | execution is confined to the closure it declared | RF† |
| R16 | non-conformance blocks scope, not just reporting | EB† |
| R17 | a recipe cannot disagree with its spec; seeds are pre-declared | RF† |
| R18 | scope evidence is embedded and identity-bearing | **CS** |
| R19 | derivation is validated at import and audit / neither mounting nor a raw write is an epistemic event | CA† / **DL** |
| R20 | the nondeterminism contract cannot contradict itself; stream totality reaches both records | RF† + ED† |
| R21 | a recipe says what to execute, portably | *unclassified — direct requirement* |
| R22 | the assessment facet is derived through the ordinary API | US† + CA† |
| R23 | a produced dataset, its ancestry and its durable basis are minted by the boundary | CA† |

**C — correction lifecycle**

| id | assertions | classes |
|---|---|---|
| C1 | the target is byte-identical, addressed and resolvable after retraction | **OInv** |
| C2 | attribution, reason and ground are required at the boundary | RF† |
| C3 | the digest covers the enumeration, never exact corpus states | **CS** + **OInv** |
| C4 | subtraction is direction-free — support and refutation subtract identically | **OInv** |
| C5 | chain, not toggle; standing is sibling-aware | **WF** + **CS** |
| C6 | verification retraction recomputes admission fail-closed | **FC** |
| C7 | retiring both routes yields `not-certified`, never a silent selection | EB† |
| C8 | a retracted snapshot is refused where recomputation already happens | RF† |
| C9 | narrowing is succession plus retraction, never mutation behind an identity | **CS** |
| C10 | ineligible or ill-formed targets are unspellable | US† |

**X — world-index packaging**

| id | assertions | classes |
|---|---|---|
| X1 | a published epoch is immutable; members are never individually deleted | US† |
| X2 | publication is crash-atomic; `current` survives a persistence cut | DU† |
| X3 | belief never reads `current` | RF† |
| X4 | the registry is append-only through every API / the negative bound | US† / **DL** |
| X5 | a duplicate `corpus_id` is refused at admission and detected at build | RF† |
| X6 | terminal states are terminal / every status is invariant under arrival order | US† / **OI** |
| X7 | admission is the cross-root commit point | RF† |
| X8 | every epoch answer is bound-stamped; an unstamped answer is unspellable | US† |
| X9 | maps and anchored head members share one coherent state view per corpus | DU† |
| X10 | receipts resolve rule bindings against the epoch | **CS** |
| X11 | GC's two hard rules hold; severed references are named | RF† |
| X12 | the maps are complete over coverage, and their receipts can refute | ED† + **CS** |

**N — normative contract**

| id | assertions | classes |
|---|---|---|
| N1 | contract succession retains every id and names its predecessor | **CS** |
| N2 | **every oracle row can fail** — a row that passes under sabotage is itself defective | OF† |
| N3 | the fixture set is the normative half of rule identity; derivations name their exact binding | **CS** |
| N4 | certification is recomputable; recomputation detects disagreement, not authorship | **WD** + CA† |
| N5 | certification binds contract, rule **and** implementation | **CS** |
| N6 | witness coverage is total per instrument, in both directions | ED† |
| N7 | uncertified degrades and never blocks; standing is discovered from explicit inputs | EB† |
| N8 | certification retraction is prospective, not transitive | EB† |
| N9 | no falsification evaluator or execution path exists | US† |
| N10 | every legacy check appears in exactly one disposition class | ED† |

**L — tamper-evident log**

| id | assertions | classes |
|---|---|---|
| L1 | registration precedes application; no unregistered cooperative path | EO† + US† |
| L2 | settlement gates every absence test | EB† |
| L3 | valid-prefix truncation refutes; interior damage is `malformed` | ED† |
| L4 | chain removal refutes against any surviving anchor, bound to its subject | **CS** |
| L5 | the unanchored tail is the pinned residue | **DL** |
| L6 | the genesis baseline reaches pre-log history — once anchored | **DL** |
| L7 | intent claims are exactly as wide as stated | EB† |
| L8 | cross-chain order exists only through world-ancestry-ordered cuts | EO† + **DL** |
| L9 | anchor evaluation is total over the observer set, never best-reachable | ED† |
| L10 | a fork is a new chain; a replica is the same chain | **CS** |
| L11 | the world chain is anchored only by export | RF† |
| L12 | one state vocabulary; every typed state class round-trips | ED† |
| L13 | **logged is not permitted** — a removal is in the timeline *and* verification still fails | **DL** |

**D — domain extension boundary**

| id | assertions | classes |
|---|---|---|
| D1 | `nodes` assigns no domain semantics | US† |
| D2 | the dataset address is unchanged under facet addition; node and corpus identity move | **OInv** + **CS** |
| D3 | a bare namespace is refused; the three unresolved states stay distinct | RF† + ED† |
| D4 | `ProfileSpec` is the only per-kind source; `KindSpec` is compiled | US† + CA† |
| D5 | reformatting `corpus.yaml` does not move the identity; content does | **OInv** + **CS** |
| D6 | consulted contracts enter belief; activated-but-unconsulted ones do not | **CS** + **OInv** |
| D7 | W5 survives unamended; contract agreement holds across a derivation | **OInv** + PC† |
| D8 | domain contributions compose; same-namespace collisions refuse | RF† + **WD** |
| D9 | a practice declaring a vocabulary or schema is refused | RF† |
| D10 | no API retracts, supersedes or attributes an individual facet payload | US† |

**H — verified holdings record** *(added 2026-08-10, the verified-holdings record design §6)*

| id | assertions | classes |
|---|---|---|
| H1 | a holdings observation is minted only by an act that dereferenced and **established** its outcome — back-filling `found` from a directory listing or a source stream's digest is unmintable / a hash outside the consistent-read boundary established no stable state, and raw concurrent mutation stays the out-of-band bound / `absent` is established by a post-delete look that answered, never inferred from a return code | RF† / RF† + **DL** / **FC** |
| H2 | active-ness is walked per location over a checked DAG, never ordered by `observed_at` / disagreeing heads block the location rather than any outcome winning / acyclicity is validated on every walk / an unmatched or qualification-unresolved mutating intent leaves its location unsettled, blocking as itself / every agreeing head stays active under coalescence / an algorithm-mixed `found` pair blocks as `incommensurable`, forced into neither box | **OInv** / **FC** / **WF** / **WD** + **FC** / **CS** / **FC** |
| H3 | "whatever is checked out" is not a coverage — enumeration is by declared stable identity / a receipt the bound rule over the named inputs does not reproduce is `refuted`, an absent input `unresolvable`, a receipt naming corpora-not-states `malformed` / the log chain heads are coherently captured, committed inputs, never read ambiently | RF† / **WD** + **FC** / **WD** |
| H4 | an act records every outcome it established or **fails** — never a transient report and a dropped record / an inconclusive attempt reports through its own channel and never mints `absent` / a mutating act runs inside its intent–fulfillment ordering or fails | **FC** / RF† / EO† |

**T — act-report** *(added 2026-08-11, the act-report design §5)*

| id | assertions | classes |
|---|---|---|
| T1 | no construction path authors an act-report — boundary-minted only, no API takes report fields as input / an imported report enters structurally validated but not operation-authenticated, attributed and inert, with no validation state written / a raw-written self-consistent report is undetected on read, and an audit detects it only with the tamper log implemented and a valid anchored observer set | CA† + US† / **DL** / **DL** |
| T2 | one started operation carries one intent and exactly one qualifying terminal — the `run` where one is minted, the act-report otherwise / a post-intent attempt minting no run closes through exactly one qualifying act-report / a second fulfilling registration on one intent is malformed / a root-selection or intent-append failure means no act began and no record was minted — an in-memory `event_token` carried by no intent and no record is not a mint / a pre-intent missing-spec refusal publishes an unfulfilling report that fulfills nothing, a crash there leaving no trace / a complete non-conforming execution mints a `run`, never an act-report / a dataset-production attempt opens the operation intent, the assessment-run intent unspellable without a `spec_identity` | **WD** + **CS** / **WD** / ED† / **FC** + EO† / **DL** + **FC** / ED† / US† |
| T3 | an unmatched intent reads unfinished / an unreadable fulfillment pointer reads indeterminate, never collapsed into unfinished / a fulfilled intent reads closed / no status field is spellable on any record — report, intent payload, or run / deleting a published report moves its operation closed → indeterminate, not unfinished | **WD** / **WD** + **FC** / **WD** / US† / **CS** |
| T4 | adding and removing reports and entries leaves the belief digest, admission, eligibility and the coverage projection byte-unchanged / an unfinished operation blocks nothing — a location with no unmatched holdings intent projects normally while its operation's intent stands unmatched / deleting an observation a report references has exactly the record-layer consequences, the report unchanged and conferring no protection | **OInv** / **OInv** / **OInv** + **DL** |
| T5 | `byte-locator-untested` is unspellable on a managed-mutation, record-import, or subject-evaluation entry / it is refused on a locator act whose request began — `retrieval-failed`'s territory / a preflight refusal and a deliberate post-stop skip both spell it, with distinct reasons / no entry outcome constructs an observation — reports reference products and never mint them | US† / RF† / ED† / US† |
| T6 | permuting two entries moves the report identity — order is identity-bearing / an (act-report ref, entry index) citation resolves to exactly one entry, an out-of-range index refused at the citing site / deleting the cited report leaves the verification unchanged and still valid, its embedded content intact — the R18 arm | **CS** / **WD** + RF† / **OInv** |
| T7 | a successful acquisition's provenance reference and act-report publish in one registered transaction in one root, the split attempt refused, never half-ordered / mutating the report moves the dataset's record bytes — its node-content identity — and the corpus-state identity, while the dataset **address** is byte-unchanged (the §6.2 basis excludes provenance) | RF† + EO† / **CS** + **OInv** |
| T8 | two operations with equal actors, timestamps and entries but distinct operation `event_token`s are two report identities / mutating each facet member in turn moves the identity every time / no ordinary API edits, supersedes, or deletes a report | **CS** / **CS** / US† |

### 5.3 What the existing taxonomy covers

The 113 rows contain **128 assertions**, since a row may state a property in a
positive arm and pin its limit in a negative one.

> **This tally is a measurement at 2026-08-05 and stays at its date**, under the
> disposition record's §5.4 discipline. **W14–W16** were added 2026-08-08
> (`2026-08-08-world-address-ruling.md`), taking the corpus to 116 rows; W15 additionally carries
> **FC**, which would move that row of the table. Neither the row count nor the
> per-label counts below have been re-measured, and restating them from
> arithmetic rather than from a recount is exactly the drift this document warns
> about elsewhere. The *conclusion* — the taxonomy reaches under half of what the
> corpus asserts — is unaffected in direction by three rows.

| label | rows | assertions |
|---|---|---|
| **CS** commitment sensitivity | 26 | 26 |
| **OInv** observational invariance | 17 | 18 |
| **DL** declared limit | 12 | 12 |
| **WD** well-definedness | 4 | 4 |
| **FC** fail-closure | 3 | 3 |
| **OI** order-independence | 1 | 1 |
| **WF** well-founded recursion | 1 | 1 |

**Both units, stated separately, because they measure different things:**

- **54 of 113 rows** contain at least one §3.4 label; **59 contain none.** This
  is a *row-level lower bound* on the gap — a row counts as covered when any one
  of its assertions is covered, so rows like G1 and G2a count as covered while
  part of their content lies outside the taxonomy.
- **59 of 128 assertions** carry a §3.4 label; **69 do not.** This is the
  coverage figure the classification is per-assertion in order to produce.

The taxonomy reaches **under half** of what the corpus asserts, and the half it
misses is not a scatter.

### 5.4 The residue, and why it exists

The 69 uncovered assertions are not miscellaneous. They are **covered by nine
recurring classes** — a cover, not a partition: the class counts sum well above
the assertion count because one assertion can carry several labels, and the
classes were derived to describe the residue rather than to divide it.

There is a structural reason the taxonomy missed all of them: **§3.4 derived its
laws from the four readings.** `standing`, `admission`, `eligible` and `B` are
functions of a configuration, so every law derived from them is a law about
*values in a state*. Roughly half of what the banked tables guarantee is about
**`step` instead** — what the system will accept, in which order, and what
cannot be expressed at all. A taxonomy built from the readings could not reach
them, and the gap is exactly as wide as that omission predicts.

| label | statement | rows |
|---|---|---|
| **RF†** refusal | `step` returns `Refused` on a stated precondition; nothing is written | 28 |
| **US†** unspellability | the act has no representation at all — tested statically, not by attempting it | 15 |
| **ED†** exhaustive discrimination | a fixed outcome set, no member collapsing into another, no unclassified residue | 12 |
| **EB†** evidence-bounded inference | a strong outcome requires a witness: `strong(r) ⟹ ∃e. Witness(e, r)` | 9 |
| **CA†** construction authority | each value has a **closed set of permitted constructors** — authored, derived, compiled, or boundary-minted — and no other path constructs it | 9 |
| **PC†** path coherence | two sanctioned paths from equivalent inputs must agree; the square commutes | 4 |
| **EO†** effect ordering | one effect durably precedes another within a single act | 3 |
| **DU†** durable atomicity | crash-atomic and survives a persistence cut (gated on composition-root adoption) | 2 |
| **OF†** oracle falsifiability | every oracle row must be capable of failing; one that passes under sabotage is defective | 1 |

**RF and US must stay distinct.** Refusal is a runtime answer — the act was
expressible, the boundary declined it. Unspellability is a type-level absence:
G5's "assert no such kind exists", S8's static assertion, N9's "no evaluator
exists", D10's "no API". The designs use both deliberately, and collapsing them
would lose the difference between a guard and a design that needs no guard —
the difference the house rule *explicit over defensive* turns on.

**CA† replaces the first draft's "derivation, not authorship", which was
backwards on its own evidence.** W4 required a merge to be **authored** and
forbade deriving content by precedence — *and as restated 2026-08-08 it requires
an attestation to be **attributed**, which is the same closed-constructor point
with the attester class no longer restricted*; classifying it as "derived, no authored
path" reversed it. What the rows share is not that authorship is absent but that
the **permitted constructor set is closed and named**: authored for W4, derived
for W8a and R4, compiled for D4, boundary-minted for R22 and R23. Stated that
way each row keeps its meaning.

**EB† is the largest unnamed principle in the corpus, and it is wider than a
default.** Comp §7.1 names its missing-value special case once — *"a failure to
look is not a finding of absence"* — and counts three appearances across
`t077`'s determinism test, world §5.1's `not-present` ≠ `unknown`, and its own
availability rule. But several of the nine rows are about **bounded inference**
rather than a default for an absent value: certification cannot be inferred
(N7), retraction effects do not propagate transitively (N8), and an intent claim
cannot widen beyond what it stated (L7). The unifying form is that a strong
reading requires a witness; the witness and the strength relation stay
reading-specific.

**PC† is path coherence, and only four rows earn it.** The first draft called it
"agreement" and stretched it over six. Defined properly — two sanctioned paths
from equivalent inputs must agree, as a commuting square — it fits S1 and S1a
(two closure algorithms), S7 (two enforcement boundaries), and D7 (contract
agreement across a derivation). W7 and R21 do not, and are reclassified in §5.5.

### 5.5 Assertions that classify as nothing

**Two rows, deliberately left unclassified:**

- **W7** — *views see the whole world, not a directory.* This names a view's
  scope. It is a direct functional requirement, not an instance of a reusable
  law, and forcing it into PC† required reading "two agreeing paths" into a row
  that states none.
- **R21** — *a recipe says what to execute, and says it portably.* Portability
  is promised; two-engine equality is not textually asserted. It would earn PC†
  only if the banked row were amended to say so, which §5 has no authority to do.

**Leaving them unclassified is the correct result, not a shortfall.** A
guarantee corpus is entitled to contain direct requirements that are not
instances of any law, and a taxonomy that absorbs every row is one that has
stopped discriminating. C4, by contrast, was genuinely misfiled: `standing`
never reads whether its target supports or refutes, so subtraction being
direction-free *is* observational invariance of that reading, and the first
draft's singleton "uniformity" class is withdrawn.

The remaining honest caveat: the nine classes of §5.4 were derived **from** the
residue, so their coverage of it is not independent evidence. What can be said
is that the residue was coherent — nine recurring classes, no class of size
zero, and only two rows left over.

### 5.6 What this changes

**§3.4's law table is incomplete, and structurally so.** M₀ states laws for the
readings and none for `step`. Refusal, unspellability, construction authority,
effect ordering and durable atomicity are properties of the transition function,
and nothing in §3 currently expresses them.

**Two of the classes are meta-level and do not belong in a system-law table.**
`OF†` constrains the **oracle suite** — that every row can fail — not `Ω`,
`step`, or any reading. `DL` is likewise documentary: it records what the system
cannot detect. Both are **assurance laws**, and grouping them with the others
would put a claim about the tests beside claims about the system.

The vocabulary §8 should draw on, stabilized:

| group | labels |
|---|---|
| **transition / type laws** | RF, US, CA, EO, DU |
| **state laws** (readings) | WD, OI, OInv, CS, WF, FC |
| **result laws** | ED, EB |
| **relational law** | PC |
| **assurance laws** | OF, DL |
| — | *plus unclassified direct requirements, explicitly permitted* |

**§5 freezes none of this.** The nine proposed labels keep their † marks until
adoption is decided; what §5 establishes is that ρ needs a vocabulary of roughly
this shape to state what M\* preserves or amends, and that manufacturing one
class per residue shape is not that vocabulary.

## 6. M\* — the typed claim calculus

This is the first section that **revises**. Everything above transcribes and
cites; what follows proposes, and §8 records what each proposal preserves,
amends or invalidates.

### 6.1 `Operator`, not `predicate`

Inside the calculus the relation term is an **`Operator`**. §2.9 (d) recorded
that `predicate` already names two unrelated objects — a relation instance's
free-string edge label, matched by exact equality, and the proposition's
vocabulary term inside an identity hash — and §4.1 of the kernel uses it in a
third sense, for a closed signature as opposed to a roster. A formal notation
that inherits a three-way overload starts by making its own statements
ambiguous.

`Operator` is therefore the name throughout M\*. `predicate` survives in M₀ for
relation instances, where it is what the substrate actually calls the field.

### 6.2 The type

```text
Claim  =  Σ (op : Operator).  Args(op) × Qualifiers(op) × Polarity(op) × Layer(op)
```

A claim is a **dependent sum**: choosing the operator determines the *types* of
everything else. The four indexed families are supplied by the operator's term
contract (§7).

Two levels have to stay distinct, and the first draft of this section collapsed
them. What a contract *declares* is a **schema**; what a claim *carries* is an
**inhabitant** of the type that schema induces. Writing `Args(op)` for both is
what made "wrong-sorted arguments are unconstructible" a slogan rather than a
consequence.

**Arguments.**

```text
arity(op)    :  ℕ                                          declared
ArgSort(op)  :  Fin(arity(op)) → Sort                      declared, one sort per slot

Args(op)     =  ∏ (i : Fin(arity(op))).  Referent(ArgSort(op, i))      induced
```

`Args(op)` is a **dependent product over slots**, and `Referent(s)` is the type
of bound referents of sort `s` — a `term` identifier drawn from the vocabulary
that sort declares (§2.9 (b) recorded that today they are bare strings). A slot
of the wrong sort is not a rejected value: `Referent(gene)` and
`Referent(phenotype)` are different types, so no term of one inhabits the other.
A slot that cannot be bound at all cannot be filled, which is what §6.6 is
about. Arity is declared per operator because it is not universally 2 —
`subtype-of` and `binds` do not take the same number or the same kinds of thing.

**Qualifiers.**

```text
Dims(op)             :  a finite set of dimension identifiers        declared
RestrictionSort(op)  :  Dims(op) → Sort                              declared, per dimension

Qualifiers(op)       =  the qualifier structure over ⟨Dims(op), RestrictionSort(op)⟩   induced
```

`Dims(op)` is the set of dimensions **permitted** for this operator — a
population restriction is meaningless for a structural operator — and
`RestrictionSort(op)(d)` fixes what a restriction on `d` may be bound to, so a
restriction is sorted exactly as an argument is. §6.4 defines the structure
itself, and states which fragment of it this pass inhabits.

**Polarity and layer.**

```text
signApt(op)  :  Bool                                       declared
Polarity(op) =  { positive, negative, unsigned }   if signApt(op)
             =  1                                  otherwise — the unit type

Layers(op)   :  a non-empty finite set of layer identifiers          declared
Layer(op)    =  that set, as a type                                  induced
```

Sign-aptness is a property of the operator, not of a central roster (§6.3).
`Layers(op)` is non-empty by construction — an operator admitting no layer would
make `Claim` uninhabited at that operator — and it is often a singleton:
`subtype-of` is structural and nothing else.

### 6.3 Unconstructibility inside the model; refusal at the boundary

The current model pairs a flat `Predicate` enum with a flat `Polarity` enum and
a **hard-coded three-element roster**, `SIGN_MEANINGFUL_PREDICATES`, consulted
by a validator that raises when the pair disagrees. That is a roster wearing a
predicate's clothes — the exact shape substrate §4.2.1 names and rejects, that
computation §1.3 records as already retired elsewhere, and that kernel §4.1
states as doctrine: *"A class is a roster — every new kind must be remembered
into it, so it has a hole by construction. A signature is a predicate."*

Under the dependent sum the invalid combination is unspellable:

```text
Polarity(op)  =  { positive, negative, unsigned }     when the contract declares op sign-apt
Polarity(op)  =  1                                    otherwise — the unit type
```

For a sign-less operator the polarity slot has **exactly one inhabitant**, so no
value can be wrong there and no `not_applicable` sentinel is needed. The
`SIGN_MEANINGFUL_PREDICATES` frozenset is **retired**, not relocated: sign-aptness
becomes a field of each operator's own contract, which is also what makes the
vocabulary extensible — a new operator declares its own sign-aptness instead of
requiring an edit to a central set.

The same argument disposes of the other two validators by construction: an
inadmissible layer is not a rejected value but an uninhabited type, and an
argument of the wrong sort has no slot to occupy.

This is *explicit over defensive* applied to the type rather than the guard, and
inside the model it classifies as **US†** — the invalid combination is
unspellable, not refused.

**How much of that is static depends on where the contract comes from.** The
dependent sum above is the specification. In an implementation whose operators
arrive through a runtime-loaded `ProfileSpec`, neither Python nor TypeScript can
vary a constructor's static signature by a runtime value without a
code-generation layer this design does not propose. What is statically
enforceable is that `Claim` is **opaque** and its **only** constructor is the
validated one, with no coercion from the wire type (**M13**); the
profile-dependent checks then happen once, at decode (**M11**). The guarantee
that survives is the one worth having — the check occurs at exactly one place
and downstream code never re-validates — and claiming more would put a
type-system property in a design that cannot deliver it.

> **What *"opaque"* has to mean, concretely — settled 2026-08-06, while building
> it.** *"No public field-wise constructor"* is necessary and is not sufficient.
> A validated constructor is worth exactly what `isinstance` is worth, and three
> further things were each independently enough to put an unchecked object
> downstream of the boundary while still satisfying `isinstance(x, Claim)`:
>
> | hole | what it admits |
> |---|---|
> | the type is **subclassable** | a subclass defines its own `__init__`, mints anything, and every reader that trusts a `Claim` unconditionally is wrong — with no line of the checked type edited |
> | the **value types** the claim holds check nothing | a referent whose `term` is an integer reaches a minted claim, because `term` is the one position in `π_claim` that **nothing downstream checks**: membership is decode's, against a snapshot |
> | qualifiers are **structurally** typed | any object exposing the right two attributes is stored inside a claim and trusted as one |
>
> So the requirement is: seal the type against subclassing **and every
> user-defined value type whose invariant the claim trusts** — it is a
> `Referent`'s own check that makes a claim's contents identifiers, so sealing
> only the claim leaves the invariant reachable one level down. The scope is that
> trust relation and not "everything the claim holds": a claim also holds strings
> and tuples, and nothing here is a claim about the language's own types. Then
> check by type, not by shape. Static `final` states the rule for a checker and
> enforces nothing at run time, which is the wrong half: the code that would
> subclass is exactly the code not being type checked.
>
> What remains reachable is `object.__new__` and direct attribute writes, which
> is the same act as the hand-edited file in the third row of the table below —
> the boundary was bypassed, not defeated — and it belongs to the audit surface
> for the same reason.
>
> **The three holes above are Python's list, and the second implementation had a
> fourth — recorded 2026-08-06, on building `ts/`.** The rows above are stated in
> terms of *"the type is subclassable"* and *"the value types check nothing"*,
> which is the right shape, but their remedy is not portable: it assumes that a
> value satisfying a type check went through that type's constructor. **In
> JavaScript it did not have to.** `instanceof` walks the prototype chain, and a
> derived constructor may `return` an object *instead of* calling `super`:
>
> ```ts
> class Rogue extends Referent {
>   constructor() { return Object.create(new.target.prototype); }   // no validation ran
> }
> ```
>
> The result satisfies `x instanceof Referent`, and a claim built from two of
> them projected integers where identifiers belong. Two more followed from the
> same assumption: `readonly` and `ReadonlyMap` are erased at run time, so a
> caller could delete a qualifier from a claim it was holding and **move that
> claim's identity**; and a structurally typed `ProfileSpec` could be
> hand-authored, so a claim could be typed against operators, sorts and layers no
> contract declares — the normative SSOT bypassed with the type checker satisfied.
>
> So the requirement generalizes: **the check must be that the constructor ran,
> not that the shape matches.** Each checked type carries a private-field brand,
> installed by its own constructor and readable only inside its own class body,
> and every validation asks the brand. Sealing against subclassing remains
> necessary and is no longer sufficient — a subclass can still be *declared*, and
> `Object.create(Subclass.prototype)` never calls a constructor at all.
>
> The asymmetry is worth stating rather than smoothing over. In Python
> `isinstance` is forgeable only through `object.__new__`, which is the raw-write
> row; in TypeScript the forge needs no unusual call, so the brand is
> load-bearing and `readonly` is the decoration. A guarantee stated as
> *"the type is opaque"* does not survive translation on its own — what survives
> is *"a value of this type was checked"*, and each language has to be asked
> separately how that can be faked.
>
> **A brand is worth what its minting function checks, and the chain runs to the
> authored document — recorded 2026-08-06, one round later.** Closing the three
> rows above did not end the forgery; it moved it one link up. `ProfileSpec`
> became branded, so a claim could no longer be typed against a hand-authored
> profile — but `compileProfile` still accepted structurally typed **contracts**,
> so a pair of object literals compiled to an entirely genuine `ProfileSpec`,
> brand and all, resolving an operator and a layer no document declares. The
> brand certified that a function had run. That was true, and worth nothing.
>
> Two properties of that finding decided how the rest of the work was done:
>
> * **Both implementations had it, and agreed.** The forged claim's digest was
>   identical on the two sides. A parity fixture compares implementations against
>   each other and would have reported perfect agreement about a claim neither
>   contract declares — so **M10 cannot witness this class of defect at all**, and
>   nothing in the parity apparatus should be read as if it could.
> * **The remedies were language-specific and the hole was not.** In TypeScript
>   the forgery is an object literal; in Python it is a public dataclass
>   constructor. Asking only the language that reported it would have left the
>   other open.
>
> So the rule is stated as a chain rather than a property of any one type: **each
> link certifies the link below it, and trust begins at the authored document.**
> Concretely — the parsers are the only route to a contract, `compileProfile`
> refuses a contract no parser produced, `buildClaim` refuses a profile
> `compileProfile` did not return, and `π_claim` refuses a claim `buildClaim` did
> not mint. A link that certifies only *"some function ran"* is not a link.
>
> The same round corrected the sentence above. `Object.freeze` was called
> decoration on the strength of the claim's scalar fields; it is load-bearing
> wherever a **collection** is held, and shallowly so. A compiled profile held its
> operators in a `Map` — `ReadonlyMap` again — and an argument sort in a plain
> array inside a frozen object, and rewriting either re-typed an operator that was
> otherwise entirely real, for every claim built afterwards. Immutability has to
> reach the leaves, and in Python it already did: `MappingProxyType` over private
> copies, with tuples throughout, which is why only the provenance half of this
> finding applied there.
>
> **Provenance is necessary and is not sufficient — recorded 2026-08-06, the
> round after.** With every link brand-checked, a hole remained that no brand
> could have caught, because **nothing in it was forged**. A domain contract's
> layer selections are validated exactly once, at parse time, against the base
> contract handed to the parser; the compiled operator then carries them as facts
> that nothing revalidates. So a domain parsed under one base and compiled under
> another — both documents real, both parsers correct, every brand intact —
> produces a claim standing on a layer the base in force does not declare.
>
> The general statement, which outranks the instance: **authenticating each input
> separately says nothing about whether the inputs belong together.** The rule has
> two conditions, and both must hold before it applies. An artifact is in scope
> when
>
> 1. its **validity is conditional** on a particular upstream artifact — some
>    check it passed was taken against that one and is not retaken; and
> 2. it **may later be recombined independently** — it can arrive somewhere
>    holding a different partner than the one it was checked against.
>
> Where both hold, the boundary that recombines them must **either verify a
> recorded dependency or revalidate the relation**. Recording is the cheaper of
> the two and is what a compiled profile does here; revalidating is available
> whenever the boundary still has what it needs to redo the check, and is the
> better answer when the relation is narrow.
>
> Both conditions are load-bearing, and the earlier phrasing of this rule — *"a
> stage that consumes an earlier stage's output creates a dependency"* — was
> wrong for want of them. Not every staged transformation needs provenance. A
> stage that revalidates everything it depends on has no conditional validity to
> carry; one whose output is never separable from its input cannot be recombined,
> so there is no second pairing to get wrong. Demanding a recorded dependency at
> every seam would put a tag on artifacts that cannot be mismatched, which buys
> nothing and obscures the seams that can.
>
> A domain contract meets both: its layers were checked against one base and the
> compiled operator carries them unrechecked, and it is handed to `compile_profile`
> separately from any base. So it records, and compilation refuses a mismatch —
> `ContractMismatch`, deliberately a different error from `UnparsedContract`,
> because a reader who sees them as one will look for a forgery that does not
> exist. **Decode is the next boundary owing the question**, and it is owed
> per-artifact rather than wholesale: a `BindingCheckReceipt` is conditional on
> the `ResolutionSnapshot` its outcomes were taken against and can travel apart
> from it, so it is in scope; a `WireClaim` is checked from scratch at decode
> against whatever profile and snapshot are in force, so it is not.
>
> Two smaller corrections from the same round, both worth their space because
> they are habits rather than incidents:
>
> * **A parser must authenticate its own dependencies.** `parse_domain_contract`
>   took a base contract and a predecessor and trusted both by shape — so its
>   layer check was worth whatever the base it was handed was worth, and its
>   succession check was compared against a predecessor written to pass. The rule
>   applied to a module's callers applies to the module.
> * **Fixing the language a defect is reported in leaves the other open.** The
>   TypeScript profile has been brand-checked at `buildClaim` since it became a
>   class; the Python one was never checked at all, and a duck exposing
>   `operator` and `claim_grammar` typed a claim against declarations of its own
>   choosing. Every finding in this block has now appeared in both languages,
>   usually wearing different clothes.
>
> **What a token achieves in Python is less than what a brand achieves in
> TypeScript, and the difference is the language's.** `#minted` cannot be
> installed from outside its class body — a forgery is impossible, not merely
> inconvenient. Python has no module privacy, so `object.__new__` plus
> `object.__setattr__` reproduces any private constructor in two lines. The mint
> tokens on `_parsed` and `_compiled` therefore remove an **ordinary** route — a
> method that merely looked internal, reachable by a caller with no intent to
> forge anything — and leave the raw write exactly where §6.3's third row already
> put it, on the audit surface. Stating that plainly is the point: the distinction
> worth keeping is between a hole and a documented limit, and a design that
> claimed unforgeable provenance in Python would have neither.
>
> **Added 2026-08-06, from the two defects reported against the snapshot and the
> wire value. Both are about a boundary's *inputs* rather than its provenance,
> which is why the round above did not reach them.**
>
> **A record type standing in for a sum must refuse the inhabitants the sum does
> not have — and the reason is identity, not tidiness.** `VocabularyBinding` is
> D §5's *held dataset* **or** *namespace with a release*, written as three
> optional fields. Its projection drops the namespace on the dataset arm, which is
> correct there and catastrophic off it: a value carrying both arms projects as
> the dataset alone, so two bindings that **differ** — distinct keys, resolved
> against different vocabularies — encode identically. Everything downstream that
> takes an identity **through** that projection then stops being determined by its
> contents. Two things do: a snapshot's identity, which is taken over an order the
> encoded binding decides, so the same snapshot took two identities depending on
> the order its bindings were supplied; and a **contract's content identity**,
> which is what `ContractMismatch` compares — two different contracts could have
> shared one. The general rule: wherever an identity is taken over a projection,
> that projection must be **injective**, and the only place injectivity can be
> established is the constructor of the type being projected. A reader cannot
> check it — by the time the reader has two colliding values it has already lost
> the distinction. Note also what closing it needed: enforcing the sum at
> construction is worth nothing against a subclass that overrides `projection`, so
> the type is **sealed** for the same reason `Claim` is — and it is the one
> declaration type here that callers construct directly, which is what puts it in
> `isinstance`'s reach at all.
>
> **A refusing arm must be closed over its own input space.** `decodeClaim` refuses
> a malformed wire value by raising a `DecodeError`; on a wire qualifier whose
> *field name* was not a string, the field arithmetic raised a raw `TypeError`
> instead, out of `sorted` or out of the `join` that builds the message. A caller
> holding the boundary's refusing arm gets a crash rather than a refusal — on
> exactly the input the boundary exists to refuse — and the sum type's `Refused`
> is a claim about the whole input space or it is not a claim. The instructive
> part is that the guard was not a new idea: both contract loaders check mapping
> keys **before** their field arithmetic, for this reason. **A boundary written
> later reimplemented the neighbourhood without the neighbourhood's guard**, and
> nothing pointed that out, because the two are in different modules and the
> shared discipline lives in neither. This is the one finding in this block with
> **no twin in the other language**, and the asymmetry is structural rather than
> accidental: JavaScript object keys are strings by construction, so `Object.keys`
> cannot hand a comparison two types. Python dictionary keys can be anything
> hashable, which is why every mapping arriving from outside needs its keys
> checked before they are sorted, joined, or compared.
>
> The same input-space question, asked of the snapshot, produced the other half:
> `build_snapshot` accepted non-string members. A `Referent` cannot carry one, so
> the snapshot held a member no claim could ever name — and `resolve` then answered
> `not-member`, the single **refusing** outcome and positive evidence that a
> vocabulary was read and lacks the term, about a vocabulary that had been handed
> it. §7.2 exists to stop an absence of evidence being reported as evidence of
> absence; this is the same confusion arriving from the other side, and its victim
> is a well-formed claim. Where two boundaries admit the same kind of value, their
> predicates have to agree, and the agreement is worth a test in **both**
> directions.
>
> **Same round, second report: injectivity is not only about shape, and the fix
> that suggests itself is the one the fixture was built to catch.** Two
> identifiers differing only in Unicode normalization are two Python strings and
> one encoded identifier, because `science.identity.v1` normalizes to NFC **at
> encode time**. So the sum enforcement above closed the shape collision and left
> the text collision open: two `VocabularyBinding`s with NFC-equivalent namespaces
> are distinct keys with one encoding, and a snapshot again took two identities.
> The obvious repair — canonicalize identifiers where they enter — is **wrong**,
> and wrong in an instructive way. The `affects-decomposed-referent` parity row
> exists to catch an implementation that normalizes at parse time rather than at
> encode time; an implementation that canonicalized or refused a decomposed
> referent would *be* that implementation, and would have failed its own fixture.
> The safeguard caught it here, which is the first time in this build a banked
> artifact overruled a fix in progress.
>
> What the layers actually want is different rules, each for a stated reason:
>
> | layer | rule | why |
> |---|---|---|
> | claim | **preserve** what the author wrote | §7.3 identifiers are authored, and encode-time normalization is a deliberate, fixture-pinned property |
> | contract, snapshot | **require** canonical form | not π_claim positions; they are inputs to projections identities are taken over, and D5's *"refused at load"* is already this layer's discipline |
> | comparison | **normalize** the query | membership must be decided under the same equivalence as `I_claim`, or a vocabulary reports `not-member` for a term it holds |
>
> Both halves of the third row are needed. Storing canonically without normalizing
> the query refuses a legitimately decomposed claim term; normalizing the query
> without storing canonically lets one vocabulary hold two members the projection
> cannot tell apart. **The general rule: where a value is stored and later
> compared, storage and comparison must agree about which equivalence they mean,
> and neither may be left implicit in a language's `==`.**
>
> The third defect of the round is the plainest and is the third instance of one
> pattern: `build_snapshot` accepted a bare string as a vocabulary, since `str`
> satisfies `Iterable[str]` — so `{binding: "EX:gene"}` builds a vocabulary of six
> characters and the term it was written to declare present resolves `not-member`.
> `decodeClaim` already refuses a bare string where it wants a sequence of terms,
> for exactly this reason, and the contract loaders already check mapping keys.
> Three times now a boundary written later has been missing a guard an existing
> boundary carries. The guards are not hard to find; **nothing points at them**,
> because each lives in the module that needed it and the discipline lives in
> none. That is an argument for the sabotage harness to be structural (N2) rather
> than a list of remembered cases.

**But the model is not the only thing that produces claims.** Serialized YAML,
imported records, a restored corpus and a raw write can all *express* a
combination the type cannot hold. Unconstructibility eliminates the internal
guard; it does not eliminate the boundary. The two are different laws at
different places, and collapsing them would leave the actual entry points
unruled.

```text
decodeClaim  :  WireClaim × ProfileSpec × ResolutionSnapshot
                ──▶  (Claim × BindingCheckReceipt) + Refused
```

Decoding is where sign-aptness, arity, argument sorts, permitted dimensions,
restriction sorts and admissible layers are **checked against the profile**,
because only there does an untyped external value meet the contract that types
it. `ProfileSpec` is the second parameter for the reason D4 makes it the sole
compiled per-kind source: the operator contracts a decode consults are compiled
profile contracts, not a roster the decoder carries. The third parameter and the
receipt are §7.2's — referent membership depends on vocabulary availability,
which is in neither of the first two, and without them the decode would not be a
function of its arguments.

The split is therefore:

| where | law | what it means |
|---|---|---|
| the typed constructor, inside the model | **US†** | there is no ill-typed `Claim` value to guard against; internal code may trust a `Claim` unconditionally |
| `decodeClaim`, on every import, deserialization and restore | **RF†** | an ill-formed wire claim is refused as a value, and nothing is minted |
| a raw write that bypasses the boundary | neither | it produces an **audit finding**, on the same terms as every other bypass in the system |

The third row is the honest one. A hand-edited file on disk can hold bytes that
no constructor and no decode would produce; that case is detected, not
prevented, and it belongs to the audit surface rather than to the type. What the
dependent sum buys is that *once decoded*, no downstream reader needs to
re-check — the check happens exactly once, at the one place an external value
enters.

### 6.4 Qualifiers — kernel structure, domain terms

This is where the founding example lives. Kernel §4.1 exists because editing
*"X affects Y in adults"* into *"X affects Y in all humans"* must not be a
revision — and *"in adults"* is not a subject, an object, a polarity or a layer.
Under a bare 5-tuple with `statement` demoted, both claims have identical typed
values and one identity, and **the exact failure the kernel was built to prevent
becomes invisible**. The qualifier is therefore not an optional enrichment; it
is what makes the typed form admissible at all.

**`Qualifiers(op)` is a typed structure, and this pass inhabits one fragment of
it.** The temptation is to declare the structure to *be* a dimension-keyed map
and move on. That would be a quiet commitment to a logic, because a map has no
quantifier scope and no order:

```text
∀ population. ∃ condition. P      ≠      ∃ condition. ∀ population. P
```

A map also permits at most one restriction per dimension, so a claim restricted
to two populations, or to a range, has no representation. Those are real
expressive limits, and the honest move is to name them as the boundary of this
pass rather than to let a convenient encoding decide the logic by default.

So the kernel rules three things about the structure and defers the fourth:

1. it is a **canonical, inspectable typed term** — not an opaque string, and not
   a rendering of one (§6.7);
2. every restriction is a **bound referent, never prose**, sorted by
   `RestrictionSort(op)`;
3. every restriction carries an **explicit quantifier**, kernel-owned and
   closed: `{ generic, universal, existential }`;
4. its **grammar is versioned**, and a later revision may extend it to express
   scope order and composition without invalidating terms already written under
   the earlier grammar.

The fragment this pass inhabits — call it the **flat fragment** — is exactly the
dimension-keyed map: each permitted dimension carries at most one
`⟨quantifier, restriction⟩`, and dimensions are mutually independent, so scope
order is not merely unrepresented but **irrelevant** within the fragment.

```text
QualifiersFlat(op)  =  a finite partial map,  d : Dims(op)  ↦  ⟨ quantifier, Referent(RestrictionSort(op, d)) ⟩
```

Anything richer — a scoped alternation, a disjunction of restrictions, a
quantitative range — is **refused at `decodeClaim`** (§6.3) rather than
flattened into the map. Flattening is the failure mode to avoid: it would
produce a well-typed claim that means something other than the span it came
from, which is the scope-widening failure kernel §4.1 exists to prevent,
committed by the encoding instead of by an editor.

**The kernel owns the structure; domains own what fills it.** Which dimensions
exist — `population`, `condition`, `regime`, `time-scale` — is domain
vocabulary, declared per operator by its contract, along with each dimension's
restriction sort. That split is D3 applied one level up, and it is what keeps
`Claim` from silently becoming a biology type: a qualifier structure designed
around populations would breach the domain boundary inside the kernel's most
load-bearing object.

Under this structure the founding example separates mechanically. Kernel §4.1's
edit is *"X affects Y in adults"* → *"X affects Y in all humans"*, and the two
differ in both slots the qualifier provides:

```text
c_adults  = ⟨ affects, [X, Y], { population ↦ ⟨generic,   term:adults⟩ }, positive, causal ⟩
c_humans  = ⟨ affects, [X, Y], { population ↦ ⟨universal, term:humans⟩ }, positive, causal ⟩

π_claim(c_adults)  ≠  π_claim(c_humans)
```

*"in adults"* is a generic claim about a population; *"in all humans"* is
universal over one — so the quantifiers differ, and the restriction identifiers
differ independently of them. Either difference alone separates the identities:
holding the quantifier fixed, `term:adults ≠ term:humans` still forks, which is
the case that matters, since the widening a reviewer would miss is usually a
restriction swap and not a visible *"all"*.

Two identities, a `supersedes` link, and every prior assessment still bound to
the claim it actually assessed — with no prose anywhere in the projection.

### 6.5 The canonical projection, and why `statement` leaves identity

**Every position in the projection is an identifier.** A symbol is what a term
is *called*; an identifier is what it *is*. The distinction is the whole content
of the binding rule already settled for vocabulary (D6, D §8): **claim identity
binds the term identifier, and the consulted vocabulary contract enters
`belief_input_digest`.** Putting the contract release into claim identity would
fork every claim on every ontology release; leaving the contract out of belief
entirely would let a reinterpretation of a term move a belief silently. The
projection carries identifiers, and the release travels the other channel.

```text
π_claim(c)  =  ⟨ operator      — the operator's term identifier,
                 args          — by slot index, each a bound referent identifier,
                 qualifiers    — sorted by dimension identifier, each
                                 ⟨ quantifier tag, restriction referent identifier ⟩,
                 polarity      — the polarity tag, always emitted; the
                                 sign-inapt tag when Polarity(op) = 1 (§7.5),
                 layer ⟩       — the layer term identifier

I_claim(c)  =  H( tag_claim ‖ encode(π_claim(c)) )        under science.identity.v1
```

> **`tag_claim` is `science.claim.v1`, and its version is the projection's —
> settled 2026-08-06, while building it.** The line above names `tag_claim`
> without saying what it is or what moves it, and three candidates were live: the
> corpus version, the claim grammar's `version` field, and the projection's own
> shape. The first two are wrong for the same reason, and it is M8's: a grammar
> bump or a corpus bump would fork every claim ever written, which is what §6.5
> exists to prevent one paragraph up.
>
> So the domain moves when **π_claim's shape** moves, and nothing else moves it.
> A `science.claim.v2` projection can then never collide with a v1 one — the
> guarantee `science.identity.v1`'s domain separation is for — and §6.4 rule 4's
> promise becomes mechanical rather than aspirational: when a later qualifier
> grammar adds scope order, claims already written in the flat fragment keep the
> identities they were written with, because their projection's shape did not
> change. The grammar version stays in the base contract, where it governs what
> may be *authored*, and stays out of what a claim is *named*.

Five positions, five kinds of name, and none of them prose:

| position | what enters the hash | owned by |
|---|---|---|
| operator | the operator's **term identifier** | a domain contract, always (§7.1) |
| argument, per slot | the **referent identifier**, in the sort's vocabulary | a domain contract |
| qualifier key | the **dimension identifier** | a domain contract |
| qualifier restriction | the **referent identifier**, in the dimension's restriction sort | a domain contract |
| quantifier | a **canonical kernel tag** from the closed set | the kernel |
| polarity | a **canonical kernel tag** from the closed set | the kernel |
| layer | the **layer term identifier** | the base contract |

The two kernel-owned positions are tags rather than contract-issued identifiers
because their sets are closed and kernel-owned. Their canonical encodings are
pinned by the base contract (§7.1) — a tag that is stable in prose but unstable
in bytes would fork identities across implementations — and changing one is the
severe case §7.4 row 5 records.

`I_claim` therefore names an identity that survives an ontology release, and
`belief_input_digest` — not `I_claim` — is what moves when the contract behind
one of those identifiers is reinterpreted. §7 defines the contracts these
identifiers are issued by.

**`statement` is excluded from identity**, which is precisely the move kernel
§4.1 already made for `title`, with §4.1's own argument carrying it the last
step: *"A field cannot be both hand-editable prose and an identity input."* Once
the typed form is normative, `statement` is in exactly the position `title` was.

But "a derived gloss, freely overridable" was still one field with two
construction authorities — the defect CA† names, committed in the sentence that
was supposed to fix it. It splits in two:

| | `render(Claim)` | `display_statement` |
|---|---|---|
| produced by | a **deterministic function** `render(Claim, Locale)` of the typed form, the consulted vocabulary, and an **explicit** locale — never an ambient one. *Generalized 2026-08-08 to every kind, per **value** rather than per kind: an **authority identifier** renders as `preferred_label(identifier, pinned_authority_release)`; a **record** renders from immutable content, recursively rendering any authority identifiers it holds* | **authored** ~~by a human~~ *— attributed to an attester, human or agent, with no class privileged (2026-08-08)* |
| stored | **no** — computed on read | yes, optional, may be absent |
| authority | derived | authored |
| in `π_claim` | no | no |
| in belief or matching | no | no |

Both are identity-inert; neither is ever read by identity, belief, standing or
estimand matching. Making `render` unstored is what keeps it honest: a stored
rendering is a cache that can disagree with what it renders, and a disagreement
between the gloss and the claim is exactly the confusion this section removes.
An authored `display_statement` is then an ordinary annotation with one
authority and no derived counterpart to drift from — a reader may prefer it, and
nothing downstream may consult it.

Three consequences worth stating.

**Kernel §11's normalization question largely dissolves.** It asks whether
whitespace, casing, term-synonym resolution and numeric formatting participate
in the hash, and frames the dilemma: *"too loose and a scope change slips
through as a revision; too tight and every typo forks the identity."* With no
prose in the projection there is no whitespace, casing or typo to rule on. What
remains is canonicalization of **typed values**, which `science.identity.v1`
already supplies, plus the separate question of whether two *referent terms* are
synonyms — which belongs to vocabulary binding (D §5), not to claim identity.

**The residual natural-language problem moves to extraction, where the system
already accounts for it.** Kernel §4.2 frames extraction as one-sided and
bounded — *"does this span assert P?"* — and limitation 3 already treats it as a
fallible computation with a measured 25–40% field-level disagreement rate. That
is the right home for linguistic ambiguity: a computation with an error rate,
not an immutable identity.

**Limitation 5 becomes stateable.** The estimand-match residue — extraction
records an estimand but nothing forces it to *match* the claim — is a relation
between two typed objects only once the claim is typed. `match(claim_type,
estimand_type)` is a predicate that can be written; over prose it could never be
more than a human judgment.

### 6.6 Untypeable spans produce work, not records

An extracted span that cannot be typed — no operator fits, or an argument cannot
be bound to a referent — **mints nothing**. The boundary refuses (**RF†**), and
the span becomes an ordinary typing-work item in the project-scoped tier (§2.4),
which needs no new kind and no fallback record.

The refusal propagates, and the reason is structural: `source-assertion`'s
identity basis **contains the proposition identity** (world §4.2), and when
typing refuses there is no proposition identity for the extraction path to
carry. So no constructor and no `decodeClaim` path admits untyped prose into the
record set as an assertion, and a raw write that fabricates one is an audit
finding, on the terms §6.3 already set out.

**Stated at the width it holds.** This is an end-to-end property of the
extraction path — refusal upstream means nothing is minted downstream — and
**not** a general claim that a source-assertion naming an unresolved proposition
identity is unconstructible. World addressing tolerates unresolved references;
forbidding them would be a deliberate amendment to source-assertion resolution,
which §8 does not make. M12 is scoped to match.

**The cost, stated plainly.** Coverage of the literature becomes gated by the
operator vocabulary's expressiveness. Kernel limitation 4 already says real
claims will not fit nine terms cleanly; under this design an unfitting claim is
not degraded, it is **queued**. That makes the vocabulary's extension rule
load-bearing for *throughput*, not only for correctness.

**This queue is a new operational consequence, not a banked precedent.** Kernel
limitation 1's ranked work queue is *widely-asserted-but-unassessed
propositions* — claims that exist, carry assertions, and lack assessments. An
untypeable span has no proposition at all and therefore cannot appear in that
row. Reusing the project-scoped `task` tier to hold it is sensible and needs no
new kind, but it introduces a **second** backlog with a different membership
condition and a different owner: the first is answered by running an analysis,
the second only by extending a vocabulary. §11 records it as such; nothing in
the kernel currently sizes it.

### 6.7 What is preserved for entailment, without defining it

Once a qualifier carries an explicit quantifier over a bound restriction
referent, `c_adults` and `c_humans` **retain the typed information a future
entailment relation would need**, and may become comparable under it. That is
the claim §6 makes, and it is weaker than the one the first draft made.

The first draft said the two were "ordered by entailment." They are not, and
`term:adults ⊆ term:humans` does not establish it. At least three things stand
between restriction inclusion and claim entailment:

| | why inclusion is not enough |
|---|---|
| operator variance | an operator need not be monotone in a restriction, and none has yet declared a variance |
| quantifier semantics | `generic` is not `universal` weakened — a generic claim tolerates exceptions, so it neither implies nor is implied by the universal over the same referent |
| ontology subsumption | `term:adults ⊆ term:humans` is a fact of a vocabulary contract at a release, not of the identifiers, and D6 deliberately keeps the release out of claim identity |

There is also a substantive reason to distrust the intuition rather than merely
its formalization: a statistical effect can **reverse** across a subpopulation,
so a claim true of adults may be false of humans, and a relation that concluded
otherwise from inclusion alone would be unsound about the world, not just
underspecified.

**§6 therefore does not define it.** Defining subsumption would pull ontology
reasoning, quantifier interaction, operator variance and partial orders over
restriction domains into a section whose job is the identity of a single claim.

What §6 *does* is keep such a relation **definable later**, which is a
requirement on the encoding and rules three of them out:

| ruled out | why |
|---|---|
| an opaque canonical string for the whole qualifier structure | nothing can be compared inside it |
| pre-normalizing restrictions to a most-general form | destroys the distinction being preserved |
| folding qualifiers into the operator identifier (`affects-in-adults`) | multiplies terms and loses the factorization the structure provides |

The estimand-match residue of limitation 5 is **related to** this relation and
not assumed to be the same one. `match(claim_type, estimand_type)` asks whether
a study's estimand answers a claim; entailment asks whether one claim follows
from another. They plainly share machinery — both compare typed restrictions
under a vocabulary — but whether one is definable from the other is an open
question, not a shortcut §6 may take.

Both are recorded in §11 as required-future with their motivation, so that a
later design inherits the constraint rather than rediscovering it.

## 7. M\* — term contracts and referent typing

§6 wrote `Operator`, `Sort`, `Dims` and `Layers` as though something issued
them. §7 says what does. It answers D §12's last open question directly — *"whether
the predicate vocabulary becomes a domain contract like any other"* — and it
closes the two halves of kernel limitation 4 that the nine-term roster left
open: **who owns the vocabulary, and by what rule it extends**.

A third half the roster never had is opened rather than closed. Once arguments
and restrictions are bound referents instead of strings, binding them acquires
a lifecycle, and §7.2 finds that lifecycle unspellable under the banked
correction rules. §7 takes the diagnostic fork deliberately and says so; the
claim being made is narrower than "limitation 4 is closed."

### 7.1 The contract split

The vocabulary is a contract like any other, but it does not sit in **one**
contract, because §6.4's D3-one-level-up ruling already divides it. The split
follows the existing base/domain line exactly:

| declared by | what it owns | why there |
|---|---|---|
| the **`science` base contract** | the claim grammar version; the closed quantifier tag set; the closed polarity tag set; the layer vocabulary; the canonical byte encoding of every kernel tag | these are the kernel-owned structure of `Claim` — the parts §6.4 refuses to let a domain choose |
| a **domain contract** | operator identifiers and their declarations; dimension identifiers; sort identifiers and their vocabulary bindings | `affects` is a claim *about* biology; the kernel has no opinion on which relations exist |

**Operators are domain-issued without exception**, and the base contract may not
issue one. The rule stays uniform for two reasons: a base-issued operator would
have the kernel opining on which relations exist, which is the boundary §6.4
draws; and because the base contract is unconditionally consulted, a base-issued
operator would sit outside the closure walk that every other operator goes
through, giving one class of operator a different belief rule for no reason.
Domain-neutral relations — `subtype-of` and its kin — belong to a
general-purpose domain contract, since nothing requires a "domain" to be a
natural science. §6.5's table said "a domain (or the base) contract"; that
hedge is withdrawn.

**D6's asymmetry survives; D6's trigger set does not.** The unconditional-base /
conditional-domain rule is exactly right and is inherited unchanged. But D6
computes domain participation by walking a derivation's closure and collecting
**the namespace of every facet it reads**, and claims introduce trigger kinds
that walk does not have: a contract can now be reached through an operator
identifier, a dimension identifier, a sort identifier, or a referent identifier
in a bound vocabulary — none of which is a facet key. A walk that collected only
facet namespaces would omit the contract declaring `affects` from a belief
derived over a claim at `affects`, and it would fail **open**, exactly as D
limitation 2 warns.

So the amendment is stated, not glossed:

> **Amendment to D6 (for §8 and D6's oracle).** The consulted set includes every
> contract reached through a **claim schema** — the contract declaring the
> operator, each dimension, each argument and restriction sort, and the
> vocabulary binding each sort resolves through — in addition to every contract
> reached through a facet namespace.

> **Amended 2026-09-16 — a third trigger, and a fourth declaration class**
> (`2026-09-12-estimand-typing-design.md`, discharged at conformance cut 31).
> A domain contract gains an `estimands:` table: one entry per operator it
> declares, naming the sorts that operator's levels, measures, identifications
> and conditioning members draw on. It is a declaration class like the three
> above — succession-governed under **M6 unamended**, entering
> `_declarations()` as `estimand:<operator>`, and leaving the operator's own
> `schema_projection()` byte-identical when an entry is added, so a successor
> that adds one for an operator that had none is **accepted**.
>
> **D6's trigger set widens again, for the reason it widened before.** An
> estimand reaches contracts a claim-schema walk does not: the contract
> declaring the `estimands:` entry, and the contract declaring each sort its
> contrast levels, measured quantity, identification term and conditioning
> members resolve through. A derivation over an assessment carrying a typed
> estimand therefore consults those too, and bumping one moves
> `belief_input_digest` while bumping an activated contract the estimand does
> not reach leaves it unchanged. D6's **asymmetry is inherited unchanged**; a
> walk that collected only facet and claim-schema namespaces would fail
> **open**, exactly as D limitation 2 warns and exactly as the claim-schema
> amendment above was written to prevent. Typing an estimand under a sort
> pinned by no corpus is a `ContractDisagreement`, not a silent omission.

With that, the reach is what §7.1 wants and no wider: a derivation interpreting
a claim consults the contract declaring its operator, so a biology contract bump
still leaves beliefs over chemistry claims undisturbed.

```yaml
# science base contract — the kernel-owned structure
claim_grammar:
  version: 1
  quantifiers: [generic, universal, existential]
  polarities:  [positive, negative, unsigned]
  sign_inapt_tag: inapt          # the unit inhabitant; see §7.5
  layers:      [causal, structural, statistical, methodological]
```

```yaml
# a domain contract — biology
sorts:
  molecular-entity:
    vocabulary: {namespace: HGNC, release: "2026-05-01"}
  phenotype:
    vocabulary: dataset:<content-identity>
  condition:
    vocabulary: {namespace: MONDO, release: "2026-07-01"}
  population-group:
    vocabulary: <population vocabulary — none selected; see §11>

dimensions:
  population: {restriction_sort: population-group}
  condition:  {restriction_sort: condition}

operators:
  affects:
    arity: 2
    arg_sorts: [molecular-entity, phenotype]
    sign_apt: true
    layers: [causal]
    dimensions: [population, condition]
```

> **Ruled 2026-08-06, while building it — a tag's canonical bytes are its
> symbol.** §8 asks this contract to fix *"the closed sets and their bytes, not
> their spelling"*, and §7.4 row 5 warns against *"an implementation choosing a
> different serialization for a tag"*. Read as two requirements they conflict;
> read as one they do not, and the one is: **the bytes must not be an
> implementation's decision**. So the contract declares the encoding rule
> alongside the symbols —
>
> ```yaml
> claim_grammar:
>   version: 1
>   tag_encoding: science.identity.v1   # a tag's bytes are its symbol, as a string
> ```
>
> — and a loader presented with any other `tag_encoding` **refuses**, rather than
> encoding the tags under a rule the contract did not name.
>
> **The alternative was considered and rejected.** Giving each tag a second,
> independent encoding beside its symbol would let a tag be *renamed* without
> re-minting the claim population. It buys renaming across a closed set of ten
> kernel tags, which nothing needs, and it costs every tag a second name that
> something must hold in correspondence — a cache that can disagree with what it
> names, which is the defect §6.5 removed from `render` and D §6 removed from
> `KIND_DESCRIPTORS`. §7.3 already pairs *authored and stable* with *enters claim
> identity*, and a tag symbol is exactly that; row 5 then prices a change to one
> as severe, which is the intended answer rather than a cost to engineer around.

The `population-group` binding is a **placeholder, not a proposal**. No
population vocabulary has been selected, and none of the obvious candidates is
one — MONDO is a disease ontology, and appears above bound to `condition`, which
is what it is for. As written that contract would be **refused at load** under D
§5, since a binding is exact or absent; it stands here to show that the sort
mechanism does not supply the vocabularies, and §11 records the selection as
open. It is also the concrete form of §6.6's cost: a claim qualified by
population is untypeable until some contract binds a population vocabulary.

Every field of the operator declaration is one of §6.2's declared schemas, and
nothing else is: `arity`, `arg_sorts`, `sign_apt`, `layers`, `dimensions` are
exactly `arity(op)`, `ArgSort(op)`, `signApt(op)`, `Layers(op)`, `Dims(op)`.
`RestrictionSort(op)` is resolved through the dimension declarations rather than
restated per operator, so two operators sharing `population` cannot disagree
about what a population restriction is bound to.

> **Consequence made explicit 2026-08-06, while implementing §8.3's succession
> check.** §6.2 types `Dims(op)` and `Layers(op)` as **finite sets** and
> `ArgSort(op)` as a function on `Fin(arity(op))`. A canonical schema projection
> must therefore treat them differently: `arg_sorts` is **ordered**, while
> `layers` and `dimensions` are **sorted** into a canonical set representation.
>
> This is not cosmetic, and the first implementation had it wrong. Holding a
> declared *set* in the order its author happened to type it makes reordering one
> line of YAML compare as a **different canonical schema projection** — so §8.3
> refuses it as a redefinition, on a change that changed nothing, at the one
> place in the corpus that can least afford a false positive. The converse holds
> and is why the two cannot be canonicalized alike: swapping `arg_sorts` says
> something genuinely different about the world, and must be refused.

The **layer set is base-owned but per-operator restricted** — `layers: [causal]`
selects from the base vocabulary and may not extend it. A domain that could mint
a layer would be redefining what kind of thing a claim is, which is the boundary
§6.4 draws.

### 7.2 Sorts and referent typing

A sort is a name bound to a vocabulary, and D §5 already rules how that binding
is written: a held ontology dataset by content identity, or a namespace with an
explicit release. A bare namespace is refused. §7 changes nothing about the
**form** of a binding — it uses the binding as the definition of `Referent` —
but it does refine the **outcomes** of resolving through one, below:

```text
Referent(s)  =  the terms of the vocabulary that sort s binds
```

**Binding a referent is not the same as resolving one.** This matters more for
claims than for facets, because a claim may legitimately name an ontology term
in a corpus that does not hold that ontology's bytes.

#### `unknown` cannot carry the decision, and D3 must be amended

The first draft of this section refused on D §5's `unknown`, treating it as
positive evidence that a term is not in its vocabulary. It is not.
D §5 defines `unknown` as a **disjunction**: the term is outside the bound
vocabulary, *or* the binding's namespace was never consulted. Refusing on it
would refuse a perfectly good identifier whenever a namespace went unconsulted —
and, worse, would report "not in the vocabulary" on evidence that no one looked.
That is the same error §7.2 was written to avoid, committed by the decoder.

The outcome set lacks the discriminator, so §7 **refines it**, which is a real
amendment to D §5 and to D3's oracle rather than a reading of them:

| outcome | when | replaces |
|---|---|---|
| `member` | the vocabulary was read and the term is in it | part of D §5's implicit success |
| `not-member` | the vocabulary **was read** and the term is **not** in it | half of `unknown` |
| `not-consulted` | the binding's namespace was never consulted — nothing was looked at | the other half of `unknown` |
| `not-present` | the bound dataset has a world address the consulted index records, but its corpus is absent | unchanged (world §5.1) |
| `not-available` | the dataset is identified but its bytes are not held here | unchanged |

`not-present` and `not-available` are carried over verbatim, so D3's
three-outcomes-stay-distinct test survives; what changes is that `unknown`
splits, and the two halves have opposite evidential force. `not-member` is a
finding; `not-consulted` is the absence of one.

> **Amendment to D §5 and D3 (for §8).** The term-resolution outcome is
> `member | not-member | not-consulted | not-present | not-available`. D3's
> oracle gains an arm asserting `not-member` and `not-consulted` are never
> collapsed, on the same terms it already asserts for `not-present` and
> `not-available`.

With the discriminator in place the decode rule is statable:

| outcome | `decodeClaim` | why |
|---|---|---|
| `member` | accept, check **performed and passed** | |
| `not-member` | **refuse** | positive evidence of a bad binding; admitting it would put an unbindable identifier into an immutable identity |
| `not-consulted`, `not-present`, `not-available` | accept, check **not performed** | all three are well-formed states, not errors; refusing would make claim typing require holding every bound ontology |

*"A failure to look is not a finding of absence"* appears nine times across five
banked documents; the bottom row is its **dual** — a failure to look is not a
finding of presence either. An unchecked binding must never be recorded,
reported, or later read as a checked one.

#### The decode interface needs an input and an output it did not have

§6.3 wrote `decodeClaim : WireClaim × ProfileSpec → Claim + Refused`. Both ends
are short. The decision depends on **vocabulary availability**, which is in
neither parameter, so as written the function is not a function — two holders
could decode identical inputs differently through ambient state, and which one
was right would be unanswerable. And "record the check as not performed" has no
carrier in the result type, so the record has nowhere to go.

```text
decodeClaim :  WireClaim × ProfileSpec × ResolutionSnapshot
               ──▶  (Claim × BindingCheckReceipt) + Refused
```

**`ResolutionSnapshot`** is the identified, content-derived state of vocabulary
availability the decode resolved against. Making it an explicit parameter is
what restores determinism: same three inputs, same outcome, anywhere, which is
the property §3.4's well-definedness law asks of every reading.

**`BindingCheckReceipt`** records, per referent position, which of the five
outcomes was obtained and under which snapshot identity. It is **not** in claim
identity: a corpus that happens to hold an ontology must not mint different
identities from one that does not, which would make `I_claim` depend on what
bytes are lying around — precisely what §6.5's identifier discipline exists to
prevent. It is emitted on the accepting arm only; the refusing arm produces no
claim and therefore no receipt.

> **Built 2026-08-06, and two things the interface did not say.**
>
> **The receipt also carries the claim identity**, which is beyond this section's
> letter. Without it a receipt is a set of position labels — `argument:0`,
> `restriction:testing/population` — with nothing saying whose positions they
> were, and a diagnostic that cannot be attached to its subject is not much of
> one. It is also what makes the receipt's own dependency legible: the claim
> identity fixes the operator, and §7.3 forbids redefining an operator's
> `arg_sorts` under its own identifier, so the positions cannot be silently
> reinterpreted. That argument has exactly one hole and it is already open — a
> parallel `genesis` in the same namespace is compared against nothing (§8.3,
> ρC1).
>
> **Decode maps the polarity position back to the unit inhabitant.** §7.5 always
> emits the position, so `sign_inapt_tag` is on the wire for an operator whose
> `Polarity(op)` is the unit type — and §6.3 says an author supplies nothing
> there. The boundary therefore has to *translate*, not forward: the tag on the
> wire becomes "there is nothing to supply" inside, while `build_claim` still
> refuses the same tag from an author. Recorded because forwarding it unmapped
> passed every arm-by-arm test written at the time; what caught it was decoding
> M10's frozen vector, where the sign-inapt row round-trips or the digests do not
> match.

It **reuses the boundary receipt's envelope, and is not the banked artifact.**
The first draft said "§2.3 already lists that as one of the four non-node
identity-bearers, so this needs no new kind." That was wrong on three counts
that matter. §2.3's boundary receipt is **nested inside a run** (comp §4.2,
§4.4b): it has no independent carrier, no lookup path by which a later process
could find it, and no `supersedes` lifecycle of its own. This receipt is
produced while decoding a claim rather than inside a run, and the use it was
introduced for — a later process finding it and recording that the check has now
been performed — needs exactly the independent carrier, lookup path and
succession the banked receipt lacks. Shared envelope, different artifact
contract, and the difference is what the next subsection has to resolve.

#### The correction path is unspellable under C, and §7 takes the diagnostic fork

The first draft said re-resolution to `not-member` becomes an audit finding and
"a human retracts." Nothing in the banked corpus permits that sentence. Four
independent rules block it:

| rule | consequence here |
|---|---|
| eligible targets are exactly the records whose standing a computed view reads — two arms, `node` and `route` (C §4) | a non-node receipt is in neither arm |
| propositions are **explicitly not retraction-eligible**; their lifecycle is `supersedes` (C §4) | the claim itself cannot be the target |
| audit mints nothing (5b §7.6) | detection cannot produce the correction |
| `supersedes` does not apply independently to a nested receipt | the receipt cannot be superseded in place |

So the correction, spelled out under the banked rules, would have to be some
combination of minting a corrected successor proposition, retracting the
**assessments and semantic snapshots** that carry the belief consequences, and
resolving the still-open `source-assertion` correction lifecycle (§2.9 (a)).
That is a lifecycle design, not a clause.

There are two clean options, and they are genuinely different designs:

1. **Binding checks stay diagnostic.** The receipt is a decode-time diagnostic
   with no independent addressing, no discovery path, and no succession. A
   `not-member` re-resolution is reported to a human, who decides what to do
   using the existing lifecycles. Persistence and correction remain **open**.
2. **Binding checks are promoted** to independently addressed records, with
   identity, a discovery path, succession, standing, and declared belief and
   eligibility consequences.

**§7 takes option 1, and says why option 2 is not available cheaply.** The
requirement that produced the question — needing independent supersession and
correction — *is* D's promotion trigger, the same one that decides when an
interpretation facet must become an interpretation node. Calling option 2 "no
new kind" would evade the design's own boundary, in the very document that
spent §6.4 defending that boundary. Option 2 is a kind with an eligibility
analysis, and this design's scope rule (§1) says M\* expands only when another
design question requires it.

**Therefore §7 does not close the referent-binding half of limitation 4.** It
narrows it: the ownership half is closed (§7.3), the term-identity and extension
half is closed (§7.3, §7.3a), and referent binding now has a defined check with
five honest outcomes and a decode boundary that cannot silently fabricate one.
What remains open is everything after the check — persistence, discovery,
succession, and the correction path for a claim found to name a term its
vocabulary does not contain. §11 records it, and records the promotion trigger
as the condition under which option 2 becomes the answer.

Two smaller questions go to §11 alongside it: when re-resolution runs at all,
and whether an unchecked claim may be assessed before its check is performed.

### 7.3 Term identity, and the extension rule

Kernel limitation 4's real content is not that nine terms are too few. It is
that a term has **no identity discipline**: nothing says what it means for two
uses of `affects` to be the same operator, and nothing says what may change
about `affects` without changing the claims already written with it.

Two identities, deliberately different in kind:

```text
operator term identifier   authored, stable, namespaced      enters claim identity
contract identity          content-derived, moves on edit    enters belief_input_digest
```

That pairing is what makes the first matrix row (§7.4) true. Making the term
identifier content-derived would fork every claim on every editorial change to a
contract; making the contract identity authored would let a reinterpretation
hide. Each is derived the way its job requires.

**The extension rule, in three cases.**

| operation | permitted | effect on existing claims |
|---|---|---|
| **issue** a new operator, dimension, or sort identifier | yes, freely — additive | none; no existing claim mentions it |
| **retire** an identifier | yes | existing claims keep their identity and stay readable; the **authoring constructor** may not select a retired identifier (§7.3a) |
| **redefine** an identifier — change `arity`, `arg_sorts`, `sign_apt`, `layers`, or `dimensions` | **no; refused at contract load** — but only **within a declared succession**, since a parallel `genesis` in the same namespace is compared against nothing (§8.3, ρC1) | would silently change what already-written claims mean |

The third row is the load-bearing one, and it is the guarantee tables' own
discipline — *extend, never renumber* — applied to vocabulary instead of to
guarantee ids. The reason is not aesthetic. Suppose `affects` flipped
`sign_apt` from `false` to `true`. Every stored claim at `affects` was
constructed with the unit polarity; after the flip the operator admits three
polarities, and a claim's meaning has changed underneath an identity that did
not move. Retiring `affects` and issuing `affects-directional` costs one
identifier and keeps every prior assertion bound to what it actually asserted —
the same trade kernel §4.1 made for propositions, one level up.

A change that is **purely editorial** — a description, a comment, an example —
moves the contract identity and therefore `belief_input_digest`, but touches no
declared schema and so needs no new identifier. That is D limitation 1's drift
case, inherited unchanged and not improved on here.

> **Corrected 2026-08-06, while building it — the list overstates by one item.**
> A **comment** does not move the contract identity, because contract identity is
> derived over the **canonical projection** and a comment does not survive
> parsing into one. Nor should it: D5 requires that reformatting — *"whitespace,
> key order, quoting style"* — leave an identity unchanged, and an identity taken
> over raw bytes to catch comments would make every one of those significant. A
> comment is on the formatting side of that line. Descriptions and examples are
> *fields*, survive into the projection, and move the identity exactly as this
> paragraph says.

**Who owns a term** is then simply: the contract whose namespace issues it. That
is the answer to the "no owner" half of limitation 4, and it is the same answer
D gives for facets, which is the point — the predicate vocabulary is not a
special case needing its own governance.

### 7.3a What retirement and redefinition actually require

The two rules above are stated as though `decodeClaim` enforces them. It cannot
enforce either, and saying so precisely changes what has to be built.

**Retirement is not a decode-time property.** `decodeClaim` sees wire bytes. It
cannot tell whether those bytes are a claim being authored now or a historical
claim being restored from a backup, re-imported from an export, or replayed from
the mutation log — and the two must behave differently, or retiring an
identifier would make every corpus holding a prior claim un-restorable. Refusing
at decode would corrupt exactly the history retirement exists to preserve.

The enforceable split:

| path | rule |
|---|---|
| the typed **authoring** constructor | **cannot select a retired identifier** — it is not offered, on the same US† terms as every other unconstructible combination. *"Identifier"* is every claim-vocabulary identifier the authoring act reaches, not only the operator's own: see below |
| **decode / import / restore** | accepts a retired identifier and types the claim against the **frozen retired declaration** |

Retirement therefore lives in authoring, not in validation, which is also the
only place it can live without a way to distinguish new bytes from old.

> **Which identifiers the authoring rule reaches — settled 2026-08-06, while
> building it.** Reading *"cannot select a retired identifier"* as the operator's
> own flag leaves an operator **offered whose slots cannot be filled**, so the
> refusal lands when the author tries to bind a referent — one step past the
> boundary this section draws. The rule reaches every identifier the authoring
> act touches, and §6.2's own typing decides how far:
>
> | retired | effect on authoring | why |
> |---|---|---|
> | the **operator** | withdrawn | directly |
> | an **argument sort** | the operator is **withdrawn** | every slot of `Fin(arity(op))` must be filled, and `Referent(s)` for a retired `s` offers nothing to fill it with |
> | a **permitted dimension** | that dimension alone is withdrawn; the operator remains authorable | `Dims(op)` is the set of dimensions **permitted**, not required |
> | a dimension's **restriction sort** | that dimension is withdrawn | a restriction is sorted exactly as an argument is, so nothing remains selectable on it |
>
> **Decode is untouched by all four.** A retired identifier stays fully
> resolvable, and a historical claim is typed against the frozen retired
> declaration exactly as this section requires — the asymmetry is the point, and
> widening the authoring rule must not narrow the decode one.
>
> **The rows are ordered, and a withdrawn operator has no dimensions to offer.**
> Row three narrows an *authorable* operator's selection; it is not an
> independent question. So asking which dimensions may be selected on an operator
> withdrawn by row one or row two must **refuse**, not answer *"none"* — an empty
> selection is already the honest answer for a live operator that permits no
> dimensions at all (`subtype-of` is one), and returning it for a withdrawn
> operator collapses two different facts, which is §7.5's `inapt`/`unsigned`
> collapse committed one position over. It would also let an author assemble most
> of a claim before the boundary refused it, which is the failure the table above
> was written to fix.

**That requires tombstones.** Typing a historical claim against a retired
operator means the declaration must still be readable, so a successor contract
**retains the retired declaration immutably**, marked retired, rather than
deleting it. A contract that drops a retired declaration is refused at load: it
would render an existing claim population untypeable, which is the same defect
as redefinition arriving by another route.

**And redefinition detection requires predecessor-aware validation.** "Refused
at contract load" compares a contract against something, and a content-derived
identity does not by itself say what it succeeds. So a contract **declares its
predecessor contract identity**, and load-time validation is a two-contract
check: every **claim-vocabulary** identifier present in both must have an
identical **canonical schema projection** — meaning-bearing fields, not bytes,
so editorial edits stay free — and every such identifier in the predecessor must
still be present, live or tombstoned. A contract with no predecessor declares
itself `genesis`. Without the declared predecessor there is nothing to diff against,
and "never redefine" is an honour system.

This lands squarely on D §12's open **domain contract versioning policy**
question, and it constrains the answer: whatever that policy becomes, it must
carry a predecessor link and a tombstone-retention rule, because the vocabulary
extension rule is unenforceable without both. §8 records the constraint; §11
records that the policy itself is still open.

### 7.4 What moves, and what does not

The rows this section exists to pin — five, with the fourth split, because
missing and ambiguous refuse at **different boundaries**:

| # | change | claim identity | `belief_input_digest` |
|---|---|---|---|
| 1 | same term identifiers; consulted contract release changes | **unchanged** | **moves** |
| 2 | an operator / dimension / layer / referent identifier differs | **a different claim** | moves transitively |
| 3 | an activated but **unconsulted** contract changes | unchanged | **unchanged** |
| 4a | a required contract is **missing** from the profile | **decode refused** | none produced |
| 4b | contracts **conflict across corpora** a derivation spans | unaffected — each claim already decoded | none produced; **derivation refused** |
| 5 | a kernel tag's byte encoding changes | moves — **requires an explicit standard amendment** | moves |

Row by row, with the citation each rests on.

**Row 1 is the whole point of §6.5's identifier discipline.** An ontology
release, a corrected description, a new operator added elsewhere in the same
contract — all move the content-derived contract identity, and D6 puts that in
the digest. None of them touches an identifier already in `π_claim`. Beliefs
are re-derivable and known to be affected; claims do not fork.

**Row 2 is a mint, not a mutation**, and the wording matters for the same reason
it mattered in §6.7. A claim identity never "moves" — it is immutable by
construction. What the row says is that two claims differing in any identifier
position are **different claims** with different identities, and any belief over
the new one is a different belief. "Transitively" is exact: the digest moves
because its claim-side input moved, not by a second rule.

**Row 3 is D6's conditional arm, whose *rule* is unamended and whose *triggers*
are not.** A domain activated in a manifest but never interpreted still
contributes nothing — that half is inherited exactly. But §7.1 amends what
counts as reaching a contract, adding claim-schema triggers to facet
namespaces, so the walk this row depends on is a **wider** walk than D6's
oracle currently tests. D limitation 2 already warns that an under-collecting
walk fails *open*; §7 does not fix that, and should say the uncomfortable part:
**§7 enlarges the surface D limitation 2 can get wrong**, and the widened walk
needs its own oracle arm (§8).

**Row 4 was one row and is two, because the two failures refuse in different
places.** Collapsing them made `decodeClaim` look responsible for a condition it
cannot see.

*4a, missing,* is local and static: a claim names an operator whose declaring
contract is not in the profile at all. The check is inside a single
`ProfileSpec`, so `decodeClaim` refuses and nothing is minted.

*4b, conflict,* is D7's case, and it is **not** a decode failure. Each corpus in
the closure may be individually valid and internally consistent; every claim in
each may have decoded successfully long ago. What is inconsistent is the
*combination* — a closure spanning corpora that pin different identities for one
namespace — and that is only visible when a derivation assembles the closure.
So D7's refusal fires at **derivation/belief construction**, where D already
puts it, never resolved by recency and never merged.

The shared result is that no belief is produced. Nothing partial is minted, and
there is no arm in which an unresolved contract yields a claim carrying a
resolution to be settled later.

**Row 5 is the severe one and should read that way.** The kernel tags are
canonical bytes inside `science.identity.v1`. Changing an encoding re-identifies
**every claim in every corpus** — it is not a migration, it is a re-minting of
the entire claim population. It therefore requires an explicit amendment to the
identity standard, on the same terms as any other encoding change, and it is
listed here precisely so that it can never be done incidentally by an
implementation choosing a different serialization for a tag. This is also why
§6.5's note stands: a tag stable in prose and unstable in bytes forks identities
across implementations, so the base contract pins the bytes, not the spelling.

### 7.5 Corrections §7 forces on §6

Three, of which the first is §7.2's and is recorded there: `decodeClaim` gains
`ResolutionSnapshot` and returns a `BindingCheckReceipt`, because §6.3's
signature made the decode depend on state it did not take and produce a record
it could not carry. The remaining two:

**The projection's shape must not depend on the contract.** §6.5 wrote the
polarity position as *"absent when `Polarity(op) = 1`"*. That makes the arity of
`π_claim` a function of a contract field, so a `sign_apt` flip would re-project
existing claims even though nothing about them changed. §7.3 refuses such a flip
outright, but a projection whose shape is contract-dependent is fragile in a way
the rule alone does not fix — it means the correctness of an immutable identity
rests on a contract never being edited a certain way.

So the position is **always present**, carrying the base contract's
`sign_inapt_tag` for the unit inhabitant:

```text
polarity  ∈  { positive, negative, unsigned, inapt }        always emitted
```

`inapt` and `unsigned` are different facts and must not be collapsed: `unsigned`
says the operator has a sign and this claim does not assert one; `inapt` says
the operator has no sign to assert. With this, `π_claim`'s shape is determined
entirely by the claim's own content — operator, one entry per argument slot, one
entry per present dimension, polarity, layer — and no contract edit can
re-project a stored claim.

**`ProfileSpec` resolves; contracts authorize.** D §6 already separates the two
roles, and §7 must not blur them: the contracts are the normative SSOT, and
`ProfileSpec` is the sole compiled runtime profile. `decodeClaim` takes
`ProfileSpec` as its second parameter (§6.3) because that is the resolved,
merged, validated form the check needs — but **`ProfileSpec`'s own identity
never appears in `π_claim` or in the consulted set.** What enters
`belief_input_digest` is the set of **contract** identities (D6), not the
compiled artifact's.

The reason is `KIND_DESCRIPTORS`' defect one level up. If a compiled artifact
were an identity authority, recompiling — a different merge order, a compiler
version, a validated-but-reordered output — could change claim identity with no
contract edit anywhere. D closed substrate §12 by retiring the second per-kind
source of truth; §7 declines to create one for vocabulary.

## 8. ρ — the refinement map

§1's constraint was that no revision may masquerade as a transcription. §8 is
where that is enforced: every M\* proposal is placed against the banked prose it
touches, the oracle that would have to change, and the guarantee classes it
preserves, amends, or invalidates.

### 8.1 Three dispositions, kept apart

| disposition | what it means | what banking it costs |
|---|---|---|
| **amendment** (ρA) | banked prose is wrong, incomplete, or ill-typed under M\*, and must change | edit the design text **and** its oracle row |
| **constraint** (ρC) | a banked **open question** stays open, but its answer is now bounded | edit the open question to record the bound; no oracle changes yet |
| **open mechanism** (ρO) | M\* names a requirement and does **not** supply the mechanism | nothing is banked but the record that it is open |

The three are separated because they fail differently when confused. An
amendment recorded as a constraint leaves a false oracle in place. A constraint
recorded as an amendment claims a question is closed that no one has answered.
An open mechanism recorded as either claims a mechanism exists.

The binding check is the case that forced the distinction, and it appears under
**two** dispositions on purpose: the diagnostic check is adopted (§8.5), while
its persistence and epistemic effect are ρO1. Nothing in §8 may read as though ρ
settled the second.

### 8.2 Amendments

**ρA1 — Proposition semantic identity becomes typed claim identity.**

| | |
|---|---|
| banked prose | kernel §4.1's Rule: *"A proposition carries a **semantic identity**: a hash over its normalized `statement` plus its factored fields (`subject`, `predicate`, `object`, `polarity`, `claim_layer`)."* |
| replaced by | `I_claim(c) = H(tag_claim ‖ encode(π_claim(c)))` over the typed projection (§6.5) |
| oracle | **G7**. Its positive arm — *"Edit a proposition's scope in place; assert a new semantic identity is minted, that prior assessments still bind the old one"* — is preserved **verbatim** and still passes. Its converse arm, *"overwrite `title` alone and assert *no* mint"*, gains a parallel `statement` arm |
| preserved | **CS** — the property G7 actually tests, that a semantic edit forks identity and cannot retarget evidence. **WD**. The `supersedes` lifecycle. The node-invariant framing (no new addressing layer) |
| amended | the identity **basis**: prose leaves; `qualifiers` enters; `subject`/`object` become sorted bound referents; `predicate` becomes `operator` |
| invalidated | *"normalized `statement`"* as an identity input, and with it kernel §11's **semantic-identity normalization** open question insofar as it concerns prose — whitespace, casing and numeric formatting have nothing to normalize once no prose is in the projection. Term-synonym resolution survives, relocated to vocabulary binding (D §5) |

This is the largest single amendment in the document, and its safety rests on
G7's positive arm being *strengthened* rather than weakened: under M₀ a
scope-widening edit forks identity only if the prose changed enough to move the
hash, which is exactly the "too loose" horn kernel §11 names. Under ρA1 it forks
whenever a typed field differs, and prose cannot mask it.

**ρA2 — `statement` splits into a derived rendering and an authored annotation.**

| | |
|---|---|
| banked prose | kernel §4.1's `title` split and its stated reason, *"A field cannot be both hand-editable prose and an identity input."* |
| becomes | unstored `render(Claim)`, plus optional authored `display_statement`; both identity-inert (§6.5) |
| oracle | **G7**'s converse arm, extended as in ρA1 |
| preserved | the doctrine itself, applied one field further. **CA†** — each value keeps a single construction authority |
| amended | one field with two authorities becomes two fields with one each |
| invalidated | §6.5's own first draft, *"a derived gloss, freely overridable"* — an M\* internal correction, not a banked claim |

**ρA3 — `subject` and `object` become sorted bound referents.**

| | |
|---|---|
| banked prose | kernel §4.1's factored-field list, where `subject` and `object` are unqualified; §2.9 (b) records them as bare strings while `term` is an external scoped entity (world §3) |
| becomes | `Args(op) = ∏ᵢ Referent(ArgSort(op,i))` (§6.2), each slot a term identifier in a bound vocabulary |
| oracle | **none banked** — no row tests that an argument is a resolvable referent. This is a gap, and it is a candidate **M** row (§9) |
| preserved | world §3's scoped-external `term`; D §5's binding forms |
| amended | the field's type |
| invalidated | nothing banked; the M₀ state was under-specified rather than wrong |

**ρA4 — Qualification enters the identity basis as typed structure.**

| | |
|---|---|
| banked prose | kernel §4.1's factored-field list, which has no qualifier slot — while §4.1's own founding example turns on *"in adults"* versus *"in all humans"* |
| becomes | `Qualifiers(op)`, kernel-owned structure over domain-owned dimensions, flat fragment this pass (§6.4) |
| oracle | **none banked**; candidate **M** row (§9), and the sharpest one, since G7's positive arm currently passes only because prose carries the qualifier |
| preserved | G7's intent |
| amended | the basis gains a member |
| invalidated | nothing banked. The defect it closes is latent, not recorded: under ρA1 alone — prose demoted, no qualifier slot — the two claims of §4.1's own example would collapse to **one identity** |

ρA4 is why ρA1 cannot be banked without it. Demoting prose while leaving the
factored fields as they are would institutionalize the exact failure kernel §4.1
exists to prevent.

**ρA5 — `predicate` becomes `Operator`, owned by a domain contract.**

| | |
|---|---|
| banked prose | kernel limitation 4, *"The predicate vocabulary is currently 9 terms; real claims will not fit cleanly"* — no owner, no extension rule; and D §12's open question, *"Whether the predicate vocabulary becomes a domain contract like any other"* |
| becomes | operators declared by domain contracts, always (§7.1); term identity, issue/retire/never-redefine (§7.3) |
| oracle | **D4 is unchanged and does not cover this.** D4 governs the sole authored **per-kind** source and `KindSpec` compilation; a claim schema is not a per-kind artifact and an operator roster is not a `KindSpec`. Two new oracles are required, both **M** rows (§9): that no second authored operator artifact exists beside the contracts, and that retirement/redefinition behaves as §7.3 says |
| preserved | **D4** exactly as written, at its existing scope; D §6's contracts-are-normative / `ProfileSpec`-is-compiled **split** (§7.5); **US†** for the sign-aptness roster's retirement |
| amended | limitation 4's "no owner, no extension rule" is answered; D §12's question is **closed** — yes, a domain contract like any other. Separately, **D §6's compiled-registry prose widens**: `ProfileSpec` now compiles claim schemas alongside the `KindSpec` set, so *"any further per-kind artifact is compiled from it"* is no longer a complete description of what it compiles |
| invalidated | the closed nine-term enum as the vocabulary's shape |

The first draft of this row said D4 *"is preserved and now covers more."* That
was normative scope acquired without editing either the prose or the oracle — the
same move §8 exists to prevent. D4's reach is unchanged; the new obligations are
new rows.

**ρA6 — D6's consulted-set trigger widens to claim schemas.**

| | |
|---|---|
| banked prose | D §8: *"walk the derivation's closure, collect the namespace of every facet it reads, and resolve each namespace to a contract identity by §8.1"* |
| becomes | that, **plus** every contract reached through a claim schema — operator, dimension, argument and restriction sorts, and each sort's vocabulary binding (§7.1) |
| oracle | **D6** gains a claim-schema arm: derive belief over an assessment reading a claim at `affects`, bump the contract declaring `affects` while touching no facet, and assert `belief_input_digest` **moves**. **D limitation 2**'s under-collecting-walk warning widens with it |
| preserved | D6's **asymmetry** — unconditional base, conditional domain — entirely. D7. W5. The negative arm (bump an unconsulted domain, digest unchanged) |
| amended | the trigger set only |
| invalidated | nothing. The facet-namespace rule stays correct; it is now **insufficient alone**, which is a different fault from being wrong |

The failure mode this closes fails **open**, which is why it is an amendment and
not a note: a facet-only walk omits the contract declaring an operator from a
belief derived over a claim at that operator, and the omission is invisible in
every test that uses facets.

**ρA7 — Term resolution refines from three outcomes to five.**

| | |
|---|---|
| banked prose | D §5's table row: *"`unknown` — the term is **outside the bound vocabulary** altogether, or the binding's namespace was never consulted"* |
| becomes | `member \| not-member \| not-consulted \| not-present \| not-available` (§7.2) |
| oracle | **D3**, whose statement *"the three unresolved states stay distinct"* becomes **five-way exhaustive discrimination** over two groups that must not be mixed: two **resolved membership results**, `member` and `not-member`, and three **results of a check not performed**, `not-consulted`, `not-present` and `not-available`. `not-member` is a resolved finding, not an unresolved state, and describing it as one would reproduce the very collapse the refinement exists to undo. D3 gains an arm asserting no member of the five collapses into another |
| preserved | `not-present` and `not-available` **verbatim**, so D3's existing arms pass unchanged; *"a binding is well-formed in all cases, no error is raised, and no fallback to another release occurs"*; **ED†** |
| amended | `unknown` splits into a finding and the absence of one |
| invalidated | any reading of banked `unknown` as evidence of **non-membership** — the reading §7.2's first draft made, and the one that would let a decoder report "not in the vocabulary" on the strength of nobody having looked |

**ρA8 — Held-ness is a `def` dependency, and G3 is stated over the `Belief` arm.**

| | |
|---|---|
| banked prose | computation §7.1's three-case table, row 2: *"the **last held copy** of an `observes` input destroyed → the input is no longer **held**; eligibility fails and admission **changes**"*; and G3's unrestricted statement that a belief state names its complete transitive input closure |
| becomes | held-ness typed as a **`def`** edge — it selects which arm of `B`'s codomain is reached, not the value within the `Belief` arm (§4.3 finding (b)) |
| oracle | **R5** — all three arms, including negative (a) *"destroy the last held copy … assert eligibility fails and admission changes"*, are preserved **unchanged and still pass**. **G3**'s phrasing gains the arm restriction: whenever `B` lands in the `Belief` arm, `κ_B` determines it |
| preserved | R5 verbatim; comp §7.1's three cases and its *"a failure to look is not a finding of absence"* framing; **DL**; the factorization law of §3.4 |
| amended | G3's scope, from all of `B`'s codomain to its `Belief` arm |
| invalidated | the reading under which held-ness is a `sem` edge. That reading is not merely inelegant: two configurations differing only in whether the last copy survives would share `κ_B` and therefore one `belief_input_digest` while yielding different beliefs — a **G3 violation**, not a qualifier on G3 |

The mechanism that would make the `NotAvailable` case *recorded* rather than
merely correct is **not** supplied here; that is ρO2.

**ρA9 — `standing`'s well-foundedness argument is replaced.**

| | |
|---|---|
| banked prose | correction §4: *"The recursion is well-founded: a retraction's identity covers its target's identity, so a cycle would require two records each containing the other's digest — **unconstructible**."* |
| why it fails | it is not a well-foundedness proof. Both identities are **fixed-width digests**, so "covers" establishes no containment order and nothing decreases along a chain. And collision resistance is not a proof that a cycle of digests has no solution — it is a statement about the difficulty of finding one. The banked argument is computational intuition wearing a structural argument's clothes |
| replaced by | an **acyclicity invariant on the retraction graph**. Over each finite evaluated world state, orient every retraction edge `target → retraction`; the admissible states are `Ω_valid`, those in which that graph is a **DAG** (§3.3). A topological rank then exists as a **theorem**, `standing` follows strictly increasing topological rank through a finite DAG, and the recursion terminates |
| oracle | **M3**, whose sabotage moves off the identity projection and onto the acyclicity invariant. **C10** (eligible, resolvable target) is preserved and becomes load-bearing for termination, which it was not previously credited with |
| preserved | the **property** — `standing` terminates, and the antitone operator is a unique structural recursion rather than a fixpoint (§3.3). C5's chain-not-toggle and sibling cases. **WF** |
| amended | the argument, and C §4's sentence carrying it; correction §3's import/audit contract gains the graph-validation obligation; the readings' domain becomes `Ω_valid` (§3.3) |
| invalidated | *"a cycle would require two records each containing the other's digest — unconstructible"* as a proof of anything |

**Why the invariant holds without anyone maintaining a counter.** Three
sanctioned paths change a state, and each preserves the invariant for a
different reason. A fourth — a raw write bypassing all of them — preserves
nothing, which is why §3.3 restricts the readings to `Ω_valid` rather than
claiming the invariant is universal.

| how a record arrives | why the DAG survives |
|---|---|
| an ordinary **write** | C10 already requires the retraction's target to **already resolve**. A record that existed before the retraction cannot name it, so the new edge points from an existing node to a newly added one and closes no cycle. The invariant is preserved by construction, not by a check |
| an **import** | a bundle carries records with no admission history, so the import validates **the bundle together with the resolved world context** for acyclicity, and refuses a bundle for which no topological order exists. Without this arm the argument holds for locally authored corpora and fails silently for imported ones — the shape of failure §8 exists to surface |
| ~~a **merge**~~ → a **`consolidate`** or an **`attest-coreference`** | ~~**ρA10**: distinct-basis retractions cannot be curator-merged, so no merge redirects one retraction's edge onto another act. Equal-basis replicas consolidate, which changes location and not the graph, and stays inside `Dom(step)`.~~ **Restated 2026-08-08** (`2026-08-08-world-address-ruling.md` §5): merge is retired, and **neither successor redirects an edge**. `consolidate` requires one canonical address, so it changes physical multiplicity and not the graph — the ρA10 arm that mattered, preserved under a name that cannot be read as an identity claim. `attest-coreference` is additive and its closure is a **query-layer** expansion that rewrites no stored reference, so a coreferenced pair of retractions closes no cycle either (**W15**'s negative arm). The row's conclusion is unchanged and its argument is now shorter: no sanctioned act redirects, so only `write` and `import` need arguments at all |
| a **raw write** | nothing is preserved, because nothing checked. A raw-written cycle produces `ω ∉ Ω_valid`, which **audit** classifies as malformed **before** any standing or belief evaluation — the same disposition every other raw-write defect gets. It is not a state whose belief is unknown; it is a corpus with a detected integrity fault |

**The rank is derived and never stored, which is the point.** An earlier draft of
ρA9 proposed an **admission rank** carried by the mutation log's sequence. That
formulation does not survive contact with the object it orders: a `retraction`
is a **world** kind and may target a record in **another corpus**, while the
mutation log's sequence is **per root** (L). There is no global clock to compare
across roots, so a corpus-local counter cannot order a cross-corpus edge at all
— the very edges most in need of ordering.

The graph formulation needs none of that. Acyclicity is a property of the
evaluated state, the topological rank is a consequence rather than a stored
field, and no cross-corpus clock, global log sequence, or shared counter is
required anywhere.

**The rank is derived per evaluation, so there is nothing to store.** An earlier
draft argued that storing one would enlarge W13/D §5's closed corpus-state
basis. That is not established — as a node field a rank would be content and
would enter identity legitimately, and as a derived cache it could sit outside
identity entirely — so the claim is withdrawn rather than defended.

The objections that do hold are simpler, and they are objections to an
**authoritative** rank rather than to any representation of one: it would be
**admission-order dependent**, so two corpora holding identical records could
disagree; **noncanonical**, since many topological orders satisfy the same DAG;
**evaluation-context dependent**, since a cross-corpus edge's position depends
on which corpora the evaluation spans; and **unnecessary**, since the DAG
invariant already yields termination without anyone naming an order. M3's
negative arm pins the consequence that matters: re-admitting the same records in
a different order changes no identity and no digest.

**ρA10 — Distinct-basis retractions cannot be curator-merged.**

ρA9's write arm proves that an ordinary write adds only an `existing → new`
edge. **Merge is not an ordinary write**, and the proof does not reach it: W4
requires that on a merge *"every reachable inbound reference is rewritten"*, so
merge **redirects existing edges** rather than adding one.

That is enough to build a cycle out of two valid states. Take `T → S → R` — `S`
retracts `T`, `R` retracts `S` — and merge `T` into `R`. Rewriting `S`'s inbound
reference retargets it at `R`, and the graph now holds `R ↔ S`. World §4's merge
rule permits this today: bases that disagree may still be merged when *"a
curator asserts the identification and the assertion is stored with its
rationale."*

| | |
|---|---|
| banked prose | world §4's merge rule — specifically the **curator-assertion** arm — together with W4's *"every reachable inbound reference is rewritten"* |
| becomes | two retractions may be merged **only** when their bases are equal. A **curator-asserted merge of distinct-basis retractions is refused**; an equal-basis replica consolidates mechanically, exactly as world §4.3's `duplicate location` state prescribes |
| oracle | **W4** gains the distinct-basis refusal arm; **M3** gains both arms — the refusal and the permitted consolidation |
| preserved | W4 entirely for every other kind, and its redirect-set and `uid` arms; world §4.3's `duplicate location` handling — *"one identity, two corpora … resolved by an authored merge"*; C5's sibling semantics |
| amended | the curator-assertion arm's eligible-record set |
| invalidated | the reading under which **any** two records may be merged given a curator assertion |

**Why equal-basis consolidation must survive.** An earlier draft of this row
excluded retractions from merge outright, on the argument that two retraction
records are never two recordings of one act. That conflates **semantic identity**
with **physical multiplicity**: world §4.3 records `duplicate location` — *one
identity, two corpora* — as a real migration state resolved by an authored merge,
and a retraction replicated across two corpora is exactly that. Refusing it
would leave a banked state with no resolution. What must be refused is the
curator asserting that two **different** acts are one, which is where a cycle can
be built and where the event token says the acts are distinct by construction.

**What ρA10 does not close.** The cascade is wider than the cycle, and this row
does not reach it — see **ρO5**.

> **Amended 2026-08-08** (`2026-08-08-world-address-ruling.md` §5). **ρA10's subject is retired**, and its
> conclusion survives a fortiori. Structural merge no longer exists, so a
> curator-asserted merge of distinct-basis retractions is not refused — it is
> **unspellable**, which is strictly stronger than the refusal this row banked.
> Distinct-basis records are now related only by an **additive attestation** that
> rewrites nothing. The positive arm is preserved and renamed: equal-basis
> replica consolidation is **`consolidate`** (ruling §5.4, **W16**), which
> requires one canonical address and so cannot move a target tuple by
> construction rather than by rule.
>
> **What does not change.** The DAG invariant still needs checking. Retiring
> merge closes one *route* to a cycle; it does not make the invariant
> unconstructible. `import` still validates acyclicity over the bundle union the
> resolved world context (ρA9), **M3** still owns that oracle, and a raw-written
> cycle is still auditable corruption. The ruling records this correction in its
> own §5.3, against a draft that overclaimed it.

**ρO5 (open mechanism) — merge versus immutable exact targets.**

W4's inbound rewrite and content-derived identity are in tension for **any**
merge that would **rewrite some retraction's exact target tuple** — not only for
merges of retractions. Merge assessment `A` into `A′` while `S` retracts `A`: W4
rewrites `S`'s target, `S`'s content changes, and therefore `S`'s **identity**
changes — so `S` is re-minted. Any `R` targeting `S` then names a stale identity
and is re-minted in turn, and the cascade runs as far as the retraction chain
reaches.

**The tension needs a target tuple to move.** Consolidating equal-basis replicas
of a retraction does not move one — same identity, two corpora — so no
re-minting occurs and no counter-retraction is disturbed. That case is exempt
from ρO5 and defined by ρA10 (§3.2).

This is not a claim-neighbourhood question and §8 does not answer it. The
candidate resolutions are visibly different designs — retractions could name
targets through a stable handle rather than a content identity; merge could be
refused whenever it would change a retraction's exact target tuple; or the
cascade could be defined and made an explicit, recorded consequence of
merging. Each trades
something real, and choosing among them belongs with a world-addressing
question, not here.

**What is recorded now** is that ρA10 closes the *cycle* case and leaves the
*cascade* open, so no reader takes the merge/identity interaction as settled.
Formally, ρO5 **names the portion of `Ω_valid × Action` excluded from
`Dom(step)`** (§3.2): a merge that would change some retraction's **exact target
tuple**, and hence its content identity, has no ruled outcome — a gap in the
design rather than a refusal by the system. **Identity-preserving replica
consolidation is explicitly exempt** and stays inside `Dom(step)`, since it moves
no target tuple and starts no cascade. §10 and §11 carry it.

> **ρO5 is CLOSED, 2026-08-08** (`2026-08-08-world-address-ruling.md` §5.3, §5.4). This row named the
> question as belonging *"with a world-addressing question, not here"*, and the
> world address ruling answered it — by taking a fourth route the three candidate
> resolutions did not list. It did not pick stable target handles, refuse
> tuple-changing merges, or define the cascade. It **retired the operation**.
>
> With merge gone, no sanctioned action rewrites an inbound reference:
> `consolidate` requires one canonical address and performs no redirect;
> coreference closure expands queries and rewrites nothing; and a §4.4 rename
> leaves every stored target tuple byte-identical, resolving the old address
> through `deprecated_ids`. The tuple-changing pairs this row excluded from
> `Dom(step)` therefore have **no members**, `Dom(step)` is total, and the
> cascade has no way to start.
>
> **Stated precisely, because the distinction is the same one §5.3 of the ruling
> insists on:** the cascade is not *bounded*, it is *unreachable through
> sanctioned actions*. A raw write can still leave a retraction naming a target
> that no longer resolves; that is auditable corruption, was never a `step`, and
> is unaffected by this closure. No new oracle is owed — **W15** and **W16**
> assert the no-rewrite property directly, and **M3**'s merge arms restate onto
> them.

### 8.3 Contract succession — an adopted rule and a bound, not one thing

§7.3a does two different things in one passage, and filing them together would
have ρA5 promising enforceable retirement while ρC1 said no oracle exists. They
split the way the binding check does.

**Adopted (§8.5, with M rows) — the succession rules M\* actually asserts.**
These are normative now, not deferred:

| rule | why |
|---|---|
| a contract declares **`genesis`** or **`successor(<predecessor contract identity>)`** | a first release has no predecessor; requiring one unconditionally would make no contract loadable at all |
| for **claim-vocabulary declarations only** — operators, dimensions, sorts — every identifier present in both a contract and its predecessor must have an **identical canonical schema projection** | this is *never redefine* made checkable. It compares the **meaning-bearing** fields, not bytes: a description, comment or example may change freely, which is what M6's editorial arm requires |
| retired claim-vocabulary declarations are **retained immutably as tombstones** | historical claims are typed against them (§7.3a) |
| **retirement is one-way** — a successor may retire an identifier and may never un-retire one (added 2026-08-06) | see below |
| a violation of any of the above is **refused at contract load** | RF†, at load, not at claim decode |

> **The fifth rule was missing, and was found while implementing the other
> four** (2026-08-06). The gap is a direct consequence of a decision the rules
> above force. `retired` **must** sit outside the canonical schema projection —
> inside it, the act of retiring an identifier would compare as a redefinition
> of that identifier and be refused, which would forbid the one operation §7.3a
> requires to be available. But outside it, the schema comparison cannot see
> `retired` at all, and the presence check only asks whether a declaration is
> still *there*. A successor flipping `retired: true` back to `false` therefore
> satisfied every one of the four rules above.
>
> **Why that is not merely untidy.** §7.3a puts retirement in **authoring** —
> the typed constructor cannot select a retired identifier — so the retired set
> is what decides whether a claim was authorable at the time it was written. If
> that set can shrink, it is no longer reconstructible from any point in the
> lineage, and two contracts in one lineage disagree about whether an existing
> claim was legitimately authored, with the later one silently winning. That is
> a change to what already-written records mean, which is what redefinition
> *is* — arriving through the status field instead of the schema field.
>
> So the rule belongs **beside** the schema comparison, not inside it. Omitting
> the field is the same act as writing `false`, since the default is `false`,
> and both are refused. A tombstone also remains subject to the schema
> comparison: retirement freezes a declaration, it does not exempt it.

**The scope restriction is deliberate.** These rules govern claim vocabulary and
nothing else. Facet contracts keep whatever succession discipline D §12
eventually settles on; an unscoped "every identifier" would have this design
quietly deciding facet versioning while §8.3's own constraint says that stays
open.

**`genesis` is an escape hatch, and the honest ruling is to say so.** Nothing
above stops an author from publishing a *second* contract under the same
namespace that also declares `genesis`, reusing an operator identifier with a
different schema and never being compared against anything. The rules enforce
immutability **within a declared lineage**, not across a namespace.

Closing that would require one of two mechanisms this design does not supply:
validating a corpus's **pin transition** against its prior pin, so a namespace
cannot silently jump lineages; or a **namespace/lineage authority** that says
which contract legitimately succeeds which. Both are governance, not typing.
**The parallel-genesis case is added to D §12** as part of ρC1, and M6 is worded
to the guarantee that actually holds.

**ρC1 (constraint) — the broader versioning policy stays open.**

| | |
|---|---|
| banked open question | D §12: *"Domain contract versioning policy. What constitutes a breaking change to a facet contract, and whether contract identity being content-derived is sufficient or a declared compatibility range is also needed."* |
| constraint | the policy must be **compatible with** the four adopted rules above; it may not, for instance, permit a successor to drop a claim-vocabulary declaration or to reuse such an identifier under a different canonical schema projection |
| what stays open | what counts as a breaking change to a **facet** contract, whether a declared compatibility range is needed, how ranges interact with 5b's versioning rules, and the **parallel-genesis** case — whether preventing a same-namespace lineage fork needs pin-transition validation or a namespace authority. None of that is settled here |
| status | **open.** ρC1 bounds the answer; it does not supply one |

D §12's own framing — whether content-derived identity is *sufficient* — is
answered in one direction only: it is not sufficient for vocabulary, because a
content-derived identity says what a contract *is* and never what it *succeeds*.

### 8.4 Open mechanisms

Named requirements with no mechanism. Each is a record that something is
missing, not a design.

**ρO1 — Binding-check persistence and epistemic effect.** §7.2 adopts the
diagnostic check (§8.5) and leaves open: whether the receipt persists at all,
how it would be discovered, how it would be superseded, and what corrects a
claim later found `not-member`. The banked correction rules make the obvious
path unspellable — C §4's eligible-target set is two arms and a non-node receipt
is in neither, propositions are not retraction-eligible, and 5b §7.6's audit
mints nothing — so the answer is either a lifecycle design or promotion to an
independently addressed record, which is **D's own promotion trigger** and
therefore a new kind with its own eligibility analysis. Also open: whether an
unchecked claim may be assessed, and when re-resolution runs. **ρ does not
settle any of this**, and no row in §8.2 depends on it.

**ρO2 — The held-ness mechanism.** ρA8 decides what the *answer* is when the
last held copy is destroyed. It does not make the case **recorded**: nothing
observes the destruction, so `NotAvailable` is reached by a check failing rather
than by an act being committed. §4.3 withdrew the recorded-loss repair as
premature, and it stays withdrawn.

**ρO3 — Entailment and estimand match.** §6.7 preserves the typed information a
future entailment relation would need and defines nothing. Kernel limitation 5's
estimand match becomes **stateable** as `match(claim_type, estimand_type)` and
is not stated. The two are related and not assumed identical.

> **Amended 2026-09-16 — the estimand half is answered; the entailment half is
> not** (`2026-09-12-estimand-typing-design.md`, discharged at conformance cut
> 31). `match(claim_type, estimand_type)` is now **stated and checked**, and the
> answer to this row's own question is that estimand compatibility is **not**
> derived from entailment: an estimand is built against a typed `Claim` and
> carries its identity, so the match is the structural agreement of the
> estimand's claim and operator with the target record's — refused at the write
> boundary, refused at explicit import, and contradicted under audit. Beside it,
> `commensurable` and `co_scoped` relate two **estimands** to each other, both
> total and decidable, neither read by `science.belief.v1`. The match is
> **structural**: that the measured quantity operationalizes the claim's
> argument stays authored, which is kernel limitation 5's surviving residue.
>
> The **entailment half is untouched**. §6.7 still defines no order over claims,
> so evidence still cannot be said to bear from one claim to another, and none
> of the above supplies it: two estimands over two claims at one operator are
> **not** commensurable, by construction. Belief aggregation across related
> claims remains this row's open question.

**~~ρO5~~ — Merge versus immutable exact targets. CLOSED 2026-08-08.** Stated in
full at ρA10: a merge that would change a retraction's **exact target tuple**
re-minted that retraction under W4's inbound rewrite, cascading through every
record that named it. This row said the question *belonged with world
addressing*, and `2026-08-08-world-address-ruling.md` ruled it — by **retiring merge** rather than by
choosing among the three candidate resolutions. No sanctioned action now rewrites
an inbound reference, so the excluded class is empty, `Dom(step)` is total, and
the cascade is unreachable through sanctioned actions. See ρA10's amendment for
what this does **not** buy: the DAG invariant is still checked at import (**M3**),
and a raw write is still auditable corruption.

**ρO4 — A population vocabulary.** §7.1's `population-group` sort has no
binding, and the contract as written would be refused at load under D §5. Until
one is selected, a population-qualified claim is untypeable — the concrete form
of §6.6's cost.

### 8.5 Adopted with no banked counterpart

M\* additions that amend nothing because M₀ has no corresponding claim. They
still enter §9 as candidate guarantees.

| adopted | classes | note |
|---|---|---|
| the dependent-sum `Claim` and its schema/inhabitant split (§6.2) | **US†** | no M₀ type to amend |
| `decodeClaim : WireClaim × ProfileSpec × ResolutionSnapshot → (Claim × BindingCheckReceipt) + Refused` (§6.3, §7.2) | **RF†**, **WD** | the boundary M₀ never stated; `ResolutionSnapshot` is what makes it a function of its arguments |
| the **diagnostic** binding check and its five outcomes | **ED†** | adopted; persistence and effect are ρO1 |
| unconstructible sign-inapt polarity; `SIGN_MEANINGFUL_PREDICATES` retired | **US†** | the roster is proto-science implementation, not banked prose |
| untypeable spans mint nothing; refusal upstream means the extraction path receives **no proposition identity** and mints no source-assertion | **RF†** | an **end-to-end** property of that path. World §4.2's identity basis is preserved, not amended, and this is **not** a general claim that an unresolved proposition identity is unconstructible (§6.6, M12) |
| the polarity position is always emitted (§7.5) | **CS** | keeps `π_claim`'s shape independent of any contract field |
| contract succession for claim vocabulary: `genesis`/`successor`, identical canonical schema projections across a succession, immutable tombstones, refusal at load (§8.3) | **RF†**, **CA†** | adopted now; only the **broader** versioning policy is ρC1 |
| retirement is enforced in the authoring constructor, never at decode (§7.3a) | **US†** | decode and restore must accept retired identifiers or history becomes un-restorable |

### 8.6 Preserved untouched — the negative list

Worth stating explicitly, because a claim-neighbourhood revision of this size
invites the assumption that more moved than did.

| preserved | why it is worth saying |
|---|---|
| world §4.2's identity bases, including `source-assertion`'s | §6.6's refusal is a **consequence** of that basis, not a change to it |
| C §4's eligible-target set — still exactly `node` and `route` | §7.2 explicitly declines to extend it |
| 5b §7.6, audit mints nothing | ρO1's open path must not be read as licensing an automatic retraction |
| D7 and W5 | ρA6 widens a walk; it does not touch agreement or location-invariance |
| kernel limitation 1's ranked queue | untypeable spans are a **second** backlog with a different membership condition, not an extension of that row (§6.6) |
| the nine banked guarantee tables' ids | no id is renumbered; every change above is an edit to a row's text or a new arm |

### 8.7 What banking this costs

**Design prose and oracles.**

| artifact | edit |
|---|---|
| kernel §4.1 | the Rule is restated over the typed projection (ρA1); the `title` split gains its `statement` case (ρA2); the **migration** rule becomes a **reproduction** rule under ledger §0 — `title` copies into `display_statement`, the claim is constructed afresh through the ordinary boundary, and a failure yields a typing-work item and **no proposition** |
| kernel §11 | the semantic-identity normalization question is closed for prose, narrowed to term synonyms (ρA1) |
| kernel limitation 4 | answered — owner and extension rule (ρA5); the referent-binding half is **re-recorded as open** (ρO1), not deleted |
| kernel G7, G3 | G7 gains a `statement` converse arm; G3's statement gains the `Belief`-arm restriction (ρA1, ρA8) |
| computation §7.1, R5 | §7.1's row 2 gains its `def` typing; R5's arms are unchanged (ρA8) |
| D §5, D3 | the outcome set refines to five; D3 gains a five-way non-collapsing arm (ρA7) |
| D §6 | the compiled-registry prose widens: `ProfileSpec` compiles claim schemas alongside the `KindSpec` set (ρA5) |
| D §8, D6, D limitation 2 | the trigger set widens; D6 gains a claim-schema arm (ρA6) |
| world §4, W4 | the curator-assertion arm refuses **distinct-basis** retraction merges; W4 gains that arm, and equal-basis consolidation is preserved (ρA10). *Superseded 2026-08-08 (`2026-08-08-world-address-ruling.md`): merge is retired, so the refusal becomes unspellability and the preserved consolidation becomes `consolidate`; W4 is restated and the two arms re-home to W15 and W16* |
| correction §§3–4 | §4's well-foundedness rationale is replaced by the **acyclicity invariant**, and C10 gains its termination role; **§3's import/audit contract** gains the graph-validation obligation — validate the bundle **union the resolved world context**, and classify a raw cycle as malformed (ρA9). **M3** owns the new oracle; C10's existing test is not widened |
| D §12 | the predicate-vocabulary question is closed (ρA5); the versioning question records ρC1's bound, including the **parallel-genesis** case |
| **M1–M13** | §9's rows, plus the §1 banking obligations already recorded |

**Two edits this table missed, found by the banking drift sweep.** Neither is a
new ruling; both are places where a *third* document restated an amended rule in
passing and would otherwise have kept asserting the old one. **World §4.1** cites
the kernel's proposition rule as motivation for its own addressing rule, quoting
the statement-plus-factored-fields basis; **substrate §4.2** describes kernel
§4.1 as moving the claim "out of `title` into a canonical `statement` field",
which ρA2 supersedes. A table built from the amendments alone will systematically
miss this class, because the drift lives wherever a rule is *cited*, not where it
is stated — the reason the sweep runs over the whole corpus and not over the
amendment list.

**Implementation authorities M\* introduces.** Editing design prose does not
make two implementations hash a typed claim identically, and none of these
exists today. Each needs a named home before M\* is buildable. **All four were
sited 2026-08-06**, at the start of the conformance cut 1 slice; the homes below
are where they are being built, and none is yet complete:

| authority | what it must fix | home |
|---|---|---|
| the **claim grammar** and the **canonical byte encoding of every kernel tag** — quantifiers, polarities including `sign_inapt_tag`, and the layer vocabulary | the closed sets and their bytes, not their spelling (§7.1, §7.4 row 5) | the `science` **base contract**, which is why it is a contract and not a constant — sited at `science/contracts/science/` (D §9, amended 2026-08-06) |
| **`π_claim`'s canonical projection** and its domain-separation tag `tag_claim` | field order, encoding of each position, and the tag itself, as a first-class member of the identity standard | **`science.identity.v1`** (computation §4.3's value contract), extended — a new tag, not a new encoding. Implemented in **both** trees, since this is the one shared encoding |
| **`ProfileSpec` compilation of claim schemas** | that operator, dimension and sort declarations merge and validate into the compiled profile on the same terms as `KindSpec`, with no second authored artifact | D §6's compiled-registry path, widened as above — Python only, since compilation is not a shared encoding and no parity obligation reaches it |
| a shared **Python/TypeScript parity fixture for claim identity** | that one typed claim projects to identical bytes and hashes identically in both implementations | `science/fixtures/`, at the repository root and owned by neither implementation (D §9, amended 2026-08-06). **Built and frozen 2026-08-06** — `fixtures/claim-identity-v1.json`, eleven rows, generated by `python/tools/…`, reviewed, and consumed by **both** halves; the eleven rows reproduced byte-identically in TypeScript on the first run |

The parity fixture is the one that would otherwise be discovered late. `nodes`
already imposes no facet-key grammar and both implementations accept arbitrary
string keys — D §6 pinned that freedom with a fixture rather than trusting it,
and a typed claim projection has strictly more ways to disagree: slot order,
map key sorting, tag bytes, and the absent-versus-unit distinction §7.5 exists
to remove.

> **What the fixture had to carry, settled 2026-08-06 on building it.** Three
> decisions, each one a way the artifact could have looked complete and asserted
> less than M10 asks.
>
> **Every row carries the claim's components, not only its expected projection.**
> Both implementations build *and project* from the parts. A fixture keyed on the
> projection alone would pin `science.identity.v1` — the shared *encoding* — while
> bypassing `π_claim` entirely, which is most of what this row is for: slot order
> and map-key sorting are encoding properties, but the absent-versus-unit
> distinction, the argument position emitting `term` and not `sort`, and the
> constructor supplying the unit inhabitant are all projection properties, and
> none of them would be exercised.
>
> **The artifact is stored pure-ASCII**, with every non-ASCII referent held as a
> `\uXXXX` escape. The vector deliberately contains a composed non-ASCII
> identifier and a decomposed one, and `science.identity.v1` normalizes to NFC
> **at encode time** — so one row's projection holds the decomposed form while its
> canonical bytes hold the composed one, which is exactly the divergence a second
> implementation produces by normalizing at parse time or not at all. Stored
> literally, an editor, merge tool or transfer that normalized the file would
> silently delete that assertion — the fixture committing the very bug it exists
> to catch.
>
> **Declared limit (DL).** The vector cannot exercise §4.3's amended
> code-point-versus-UTF-16 key ordering. `π_claim`'s only contract-issued keys are
> dimension identifiers, and the contract grammar restricts those to
> `[a-z][a-z0-9-]*`, so no conforming contract can issue a key above U+FFFF. That
> rule is covered by each language's own `identity.v1` unit tests and is **not**
> claimed here; a fixture that appeared to cover it would be worse than one that
> says it does not.
>
> **A second obligation this uncovered, and it is owed.** `π_claim` uses strings,
> arrays and string-keyed objects, so the claim fixture pins the value contract
> only over those. `science.identity.v1`'s **numeric arms have no cross-language
> fixture at all** — integers, decimals, the one spelling of zero, the refusal of
> binary floats, the escape table, and the astral key ordering are each tested
> twice and compared never. D §6's precedent is one parity fixture per shared
> *encoding*, and `identity.v1` is a different shared encoding from `π_claim`, so
> a values-level fixture is the second one that precedent asks for. It is **not**
> in cut 1 — §5.1 selects one fixture and the stop rule holds — and it should be
> the first thing added after it. The divergence risk is concrete: the two
> implementations spell the numeric refusal differently, Python refusing `float`
> and TypeScript refusing `number`, and nothing currently compares what they
> accept.
>
> **Demonstrated, not argued (2026-08-06).** N2's harness carries an arm whose
> sabotage changes how `science.identity.v1` writes a backslash. It **passes the
> claim fixture**: no row's values carry a backslash or a quote, so the vector
> compares the two implementations over tags, slots and keys, and over escaping
> compares nothing. Only Python's own `identity.v1` unit test catches it, and the
> TypeScript half would go on agreeing with a Python that had changed. The arm is
> kept, worded as what it actually asserts, so the gap has a row that states it.

> **Correction 2026-08-06 — the cited precedent does not exist.** This section's
> home column read *"alongside D §6's **existing** namespaced-facet-key parity
> fixture, which is the precedent for exactly one such fixture per shared
> encoding."* Measured against the trees, that is wrong twice, and this
> document's own §8.7 names the class: drift lives wherever a rule is *cited*
> rather than where it is stated.
>
> - **Not existing.** D §6 calls it *"the one shared parity fixture this design
>   **adds**"*, and D1–D10 await implementation. Nothing was there to sit
>   alongside.
> - **Not namespaced.** `nodes/fixtures/gene_phf19.{canonical.json, py-emit.md,
>   ts-emit.md}` is a genuine cross-language emit fixture, and D1 describes it
>   accurately as example payload. But its only facet key is `bio-axes` — a
>   hyphenated **flat** key. It pins nothing about `biology/gene-axis`.
>
> What survives is weaker and still useful: `gene_phf19` is a precedent for the
> **form** — one canonical artifact with a per-language emission beside it — but
> not for the encoding. **The claim parity fixture is therefore the corpus's
> first typed parity fixture, not its second**, and it has no shape to inherit.
> The consequence is a real cost rather than a bookkeeping note: its coverage
> has to be argued from M10's own text (*"vector coverage asserted complete"*)
> instead of extended from a fixture that already made those choices. D §6's
> namespaced-facet-key fixture remains outstanding and is **not** in cut 1 —
> D4 is fully deferred (disposition record §5.2).

## 9. Guarantees (M1–M13)

Thirteen rows. Six come from obligations this document raised before §8 — three
from the closure check and the laws (§3.4, §4.3), three from ρ cells that read
*"no banked oracle"*. The rest come from §8.5's adopted items, which amend
nothing and are therefore tested by nothing unless M tests them.

**M does not duplicate an amended banked row.** Term-resolution discrimination
belongs to **D3**, which ρA7 already extends to the five outcomes; an M row
restating it would create a second oracle for one property and a second place
to keep in step. What M adds instead is the part D3 does not reach — that an
accepting decode's receipt is **complete** — and that lives in M4.

**The discipline is §5's OF†, applied to M itself: every row must be capable of
failing.** So each row below names a **sabotage** — a specific mutation that
must break it. A row whose sabotage still passes is defective and is the first
thing to fix, not a row that can be left in place because it is green.

Ids are frozen on banking and extended, never renumbered — the same rule the
nine banked tables use.

Two rows deliberately stay apart. **M2** (every run input reaches the
assessment's carrier identity) and **M3** (`standing` terminates) were both
raised by §4, but they have nothing in common operationally: M2's sabotage
attaches an input outside the declared role partitions, M3's writes a retraction
against an unresolvable target and imports a bundle with no topological order. Sharing a row would let one
pass on the other's evidence.

| id | guarantee | how it is tested |
|---|---|---|
| **M1** | **Every read that crosses the instrumented resolver is inside the declared closure** | Instrument the resolver so each value read through it is recorded at read time; assert the recorded read-set is contained in the declared closure, for a corpus exercising every closure member. **Sabotage:** add a code path that reads one value outside the closure **through the resolver** — a facet, a contract, a producer set — changing nothing else, and assert the check **fails**. **Scope, and it is a real one (DL):** the row is bounded by the resolver. A read that never crosses it — a module-level constant, an environment lookup, a cached global, a file opened directly — is invisible and passes, so M1 does **not** assert that every undeclared read is detected (limitation 1). Strengthening it to that claim requires an exhaustive capability or sandbox boundary, which this design does not propose. **Why the bounded row is still worth having:** G3's own text records four closure members that "were live holes in earlier revisions," each found by a reviewer noticing. M1 converts the ordinary case from noticing to checking, and names precisely the case it leaves to noticing |
| **M2** | **Every run input reaches the assessment's carrier identity** | Take an assessment; for each input of its run, **replace that input with a newly minted dataset carrying a different content identity** — inputs are immutable and content-addressed, so the mutation is a substitution, not an edit — and assert the assessment identity **moves** every time. **Sabotage:** attach an input to the run that no declared role partition covers, and assert the attempt is **refused**, not silently ignored. §4.3 finding (a) established that the current path is three hops (the recipe's role-partitioned `inputs` → R2 → assessment identity) and is a **binding** path, not a proven semantic one; this row pins the binding so the fragility is tested rather than argued |
| **M3** | **`standing` terminates, because the retraction graph is a DAG** | **Termination itself, on valid states:** evaluate `standing` over retraction chains of increasing depth, including counter-retractions and several standing retractions of one target, and assert termination and a stable value. Without this arm a looping implementation passes while its validator is perfectly correct. **The validator, exercised directly** — the only arm that can certify the check exists: hand it an abstract two-cycle and assert a **cycle-specific** result carrying a **witness** (the offending edge set), not a generic failure. Case-split the cycle across the boundary that matters — both records in the **bundle**, and one record in the bundle closing a cycle through the **resolved world context** — and assert import invokes the validator on the **union**, never on the bundle alone. **That import consumes the result:** force a cycle verdict for an otherwise entirely valid bundle and assert the import **refuses with no write**; an importer that calls the validator and ignores its witness must fail this arm. **Ordinary writes:** attempt a retraction whose target does not already resolve and assert refusal (C10), which is what makes a write incapable of closing a cycle. **Merge's two arms, restated onto its successors 2026-08-08 (`2026-08-08-world-address-ruling.md` §5; ρA10):** the distinct-basis arm becomes **unspellable rather than refused** — assert **no operation exists** that merges two distinct-basis retractions, which is stronger than the refusal this arm banked, and assert instead that a `coreference-attestation` over them leaves both retraction records **byte-unchanged** and closes **no cycle** (**W15**). The equal-basis arm keeps its shape under its new name: `consolidate` two **equal-basis** replicas of one retraction held in two corpora **while a counter-retraction `R` already targets it**, and assert it **succeeds**, that the retraction's content identity is **unchanged**, and that `R` is **not rewritten and not re-minted** — now true by construction, since `consolidate` requires one canonical address and performs no inbound rewrite (**W16**). World §4.3's `duplicate location` state has no other resolution. **Raw writes:** a cyclic configuration is classified **malformed by audit before any standing or belief evaluation** — assert no reading is invoked on it (§3.3, `Ω_valid`). **Explicitly not the test:** refusing a hand-written cyclic *pair* certifies nothing. Each retraction's content-derived address already includes its target identity, so such a pair fails **identity recomputation** on its own, and a generic "import refused" passes whether or not any acyclicity validation exists. That fixture is circular evidence, and an earlier draft of this row used it. **Negative:** no topological rank is stored anywhere; re-evaluate the same state after admitting records in a different order and assert every identity and `belief_input_digest` is unchanged |
| **M4** | **Every argument and restriction is a typed referent; resolved non-membership refuses, and an unperformed check stays explicit** | Decode a claim whose argument term **is** in the sort's bound vocabulary with that vocabulary readable → accepted, outcome `member`. **Sabotage:** decode one whose term is **not** in a readable vocabulary → **refused**, nothing minted. **Negative — availability is not membership:** make the vocabulary unreadable and decode the same bad term → **accepted**, outcome `not-available`, and assert the two accepting receipts are distinguishable. **Receipt completeness:** on every accepting decode, assert the receipt carries **exactly one outcome per referent position** — no position missing, none duplicated — plus the **`ResolutionSnapshot` identity** it resolved against. **Static:** assert a bare string cannot occupy an argument slot at all. **Snapshot inputs, added 2026-08-06 on a reported defect:** a receipt's outcomes are worth exactly what the snapshot's contents are, so assert the snapshot **refuses what it cannot resolve honestly** — a key that is not a `VocabularyBinding` (matched by value against the sort declarations, so a lookalike matches none and every term under it reports `not-consulted`), and a member that is not a term identifier (which no `Referent` can carry, so `resolve` answers `not-member` about a vocabulary that was handed the term). Assert the member predicate is **the same one `Referent` applies**, in both directions, and that a bare string is refused where a collection of terms is wanted. **Canonical equivalence:** assert a member stored non-canonically is **refused**, that a **decomposed** claim term resolves `member` against the composed member it names, and that the two spellings give one claim identity — membership and `I_claim` must decide under the same equivalence. **Sabotage in both directions**, since each half is silently survivable alone: compare the raw query, and normalize the stored side instead of the query. **Negative, and the one that protects a banked decision:** assert the claim layer does **not** canonicalize — a `Referent` may hold a decomposed term, because M10's `affects-decomposed-referent` row exists to catch an implementation that normalizes at parse time. **Scope:** the five outcomes' mutual distinctness is **D3**'s, as amended by ρA7, not this row's |
| **M5** | **Qualification participates in claim identity** | Two claims differing **only** in a restriction identifier → different `I_claim`; differing **only** in quantifier tag → different; one carrying a dimension the other omits → different. Then the founding case end to end: mint kernel §4.1's *"in adults"* claim, assess it, "edit" to *"in all humans"*, and assert a **new** identity, the prior assessment still bound to the old one, and a `supersedes` link. **Sabotage:** drop the qualifier map from `π_claim` and assert the founding case **collapses to one identity** — the row's whole point. **Negative:** re-serialize the qualifier map with keys in a different order and assert the identity is **unchanged** |
| **M6** | **Operators are issued, retired, and never redefined within a declared succession** | A successor contract changing `arity`, `arg_sorts`, `sign_apt`, `layers` or `dimensions` under an existing identifier → **refused at contract load**. A successor **dropping** a retired declaration → refused. A successor **adding** a new operator → accepted; assert existing **claim identities are unchanged**, and assert **consulted belief digests move**, because the contract identity moved and D6 puts it in the digest. Adding is additive for identity and never for belief, and a row claiming "no existing claim affected" without that second arm would be false. **Retirement, both paths:** assert the authoring constructor **cannot select** a retired identifier (statically), and that decode/restore of a historical claim at that identifier **succeeds** against the frozen declaration. **Sabotage:** flip `sign_apt` on a live operator and assert load fails; remove the declared predecessor link and assert the redefinition check is **unable to run** rather than silently passing. **Negative:** a purely editorial change is accepted, moves the contract identity, and needs no new identifier. **Declared limit (DL):** a second contract in the same namespace declaring `genesis` and reusing an identifier under a different schema is **not** caught — assert that it loads, and that the gap is the parallel-genesis case recorded in D §12, not a defect in this row |
| **M7** | **No second authored operator artifact exists** | Assert operator, dimension and sort declarations exist **only** in profile contracts, and every runtime form is compiled from `ProfileSpec`. **Sabotage:** add a hand-authored operator roster beside the contracts and assert it is **refused or unreachable** — never consulted as a parallel source. **Negative:** a grep for operator names is **not** the test and would fail against a conforming tree. The test is a pair of mutations: change a contract's **semantic schema** — an operator's dimension set, say — and assert the compiled schema changes with **no code change**; change only a **description** and assert the compiled schema is **unchanged** while the contract identity moves. D4 does not cover this — it governs per-kind sources, and a claim schema is not a per-kind artifact |
| **M8** | **Claim identity is independent of contract release and of compilation** | Bump a consulted contract editorially and assert `I_claim` is **unchanged** while `belief_input_digest` **moves** (§7.4 row 1). Recompile `ProfileSpec` — different merge order, different compiler build — and assert `I_claim` is unchanged and `ProfileSpec`'s identity appears in **neither** `π_claim` nor the consulted set. **Sabotage:** fold the contract release into `π_claim` and assert an ontology release now forks every claim, which is the failure this row forbids. **Negative:** bump an **activated but unconsulted** contract and assert both `I_claim` and the digest are unchanged (§7.4 row 3) |
| **M9** | **`π_claim`'s shape depends on the claim, never on a contract field** | Project a claim at a **sign-inapt** operator; assert the polarity position is **present**, carrying `sign_inapt_tag`. Assert `inapt` and `unsigned` are **distinct byte sequences in the encoding**, asserted **directly against the base contract** rather than inferred from two claim digests — the two tags necessarily occur under **different operators**, so differing digests would prove only that the operators differ. **Sabotage:** omit the position for sign-inapt operators and assert the digest changes — the defect §7.5 corrects, in which a `sign_apt` edit would re-project stored claims. **Negative:** combined with **M6**, an edit that would re-project a stored claim must be **unreachable**, not merely untried |
| **M10** | **Two implementations hash a typed claim identically, over every closed tag** | One shared fixture artifact holding a **vector** of minimal claims, chosen so that **every** closed kernel tag appears at least once — each polarity (`positive`, `negative`, `unsigned`, `inapt`), each quantifier, each layer in the base vocabulary — plus one claim exercising multi-slot args, several qualifier dimensions and a non-ASCII referent identifier. Assert byte-identical projections and equal digests in **both** Python and TypeScript for **every** entry, and assert the vector's tag coverage is **complete against the base contract**, so adding a tag to the grammar forces a vector entry rather than silently going untested. **Sabotage:** change one implementation's map-key sort, slot order, or **a single tag's bytes**, and assert the fixture fails — under a one-claim fixture, changing an unused tag would pass. Follows D §6's precedent of exactly one parity fixture per shared encoding. **What it cannot witness, recorded 2026-08-06 after finding one:** parity compares the implementations against each other, so a defect *both* share is invisible to it — a forged-contract hole present in both produced identical digests for a claim no contract declares, and this row reported agreement. Provenance is M13's, not this row's |
| **M11** | **`decodeClaim` is a function of its arguments, and refuses rather than repairs** | Same `⟨WireClaim, ProfileSpec, ResolutionSnapshot⟩` decoded twice, in different processes and different checkouts → **identical** result. Then each ill-formed input in turn — a sign on a sign-inapt operator, wrong arity, an undeclared dimension, an inadmissible layer, a missing required contract — → **`Refused`**, with **nothing minted** in every case. **Sabotage:** make availability ambient rather than a parameter and assert two holders now decode the same bytes differently. **Negative:** a raw-written malformed claim is an **audit finding**, not a silent accept and not a decode failure — the boundary was bypassed, not defeated |
| **M12** | **An untypeable span mints nothing** | **End to end, which is the only form this row can take.** Present a span no operator fits; assert claim typing **refuses**, and assert the extraction path therefore receives **no proposition identity** and mints **no source-assertion** — the span surfaces as a project-scoped typing-work item instead. **Sabotage:** add a fallback that mints a proposition at a placeholder operator; separately, one that mints a source-assertion against a synthesized proposition identity. Assert both fail. **Negative:** the work item must **not** appear in kernel limitation 1's unassessed queue — different membership condition, different owner (§6.6). **Scope:** this row does **not** assert that a source-assertion naming an unresolved proposition identity is unconstructible in general. World addressing tolerates unresolved references, and forbidding them would be a deliberate amendment to source-assertion resolution, which ρ does not make |
| **M13** | **`Claim` is opaque, and the only route to one is the validated constructor** | Assert `Claim` cannot be built from ambient data: no public field-wise constructor, no cast or coercion from `WireClaim`, no dict/object-literal path. Assert **no function downstream of the boundary accepts a `WireClaim`** — the wire type is confined to the decode module. **Sabotage:** export a raw constructor, or widen one downstream signature from `Claim` to `WireClaim`, and assert the check fails. **Scope, stated because the first draft overreached:** profile-dependent validity — sign-aptness, arity, argument sorts, permitted dimensions, admissible layers — is **runtime** and belongs to **M11**. Operators arrive through `ProfileSpec`, and no Python or TypeScript implementation can vary a constructor's static signature by a runtime value without a code-generation layer this design does not propose. What survives statically is the consequence that actually matters: the check happens **once**, at one place, and downstream code needs no defensive revalidation. **Extended 2026-08-06, twice, on building it:** the guarantee is *"a value of this type was checked"*, and it is a **chain** — assert that `π_claim` refuses a claim its validated constructor did not mint, that the constructor refuses a profile the compiler did not return, and that the compiler refuses a contract no parser produced, each by an unforgeable brand rather than by shape. **Sabotage each link separately, and each link's brand against a prototype-only forgery**, since a plain object literal fails `instanceof` too and a test built only from one cannot tell the two checks apart — that vacuous test was written three times here. Assert also that everything a profile or contract holds is immutable **to the leaves**: rewriting one argument sort inside a compiled operator re-types an operator that is otherwise entirely real. **And assert what no brand can reach:** that two *genuine* artifacts which were never typed against one another are refused where they meet — a domain contract parsed under one base contract and compiled under another, which needs no forgery and passes every provenance check there is. This last obligation is **scoped, not universal**: it falls on an artifact whose validity is conditional on a particular upstream artifact *and* which can later be recombined independently, and it is discharged by verifying a recorded dependency **or** by revalidating the relation |

### 9.1 What M does not cover

| not covered | why |
|---|---|
| binding-check persistence, discovery, succession, and the correction path for a claim later found `not-member` | ρO1. **D3** (as amended by ρA7) owns outcome discrimination and **M4** owns receipt completeness; both stop at the decode boundary |
| whether an unchecked claim may be assessed | ρO1 |
| the recording mechanism for destruction of a last held copy | ρO2. M has no row, because ρA8 decides the *answer* and not the mechanism |
| entailment, subsumption, and estimand match | ρO3. §6.7 preserves the encoding's capacity to express them and defines no relation, so there is nothing to test |
| ~~the merge/immutable-target cascade beyond the cycle case~~ | ~~ρO5.~~ **Closed 2026-08-08** (`2026-08-08-world-address-ruling.md`): merge is retired, so the cascade has no sanctioned route to start. M3's two arms restate onto `consolidate` and `attest-coreference`, and **W15**/**W16** assert the no-rewrite property directly |
| that a population-qualified claim can be typed at all | ρO4. No population vocabulary is bound, so the case is currently untypeable by construction |
| that an operator's declared schema faithfully describes the relation it names | authored, not checked — the same class as D limitation 4 and kernel limitation 8's acquisition boundary. M6 tests that a declaration cannot **change**; nothing tests that it was right |

**Two rows are load-bearing beyond their own statement.** M1 is the only row
that attacks the method rather than a property: every other row here, and in the
nine banked tables, tests something a person thought to test. And M13 is what
keeps the boundary a boundary — if `Claim` stops being opaque, or one downstream
signature widens to the wire type, then M11's single check stops being the only
check and every reader has a reason to re-validate defensively.

## 10. Limitations

1. **M1 is bounded by its read-interception boundary, and says so.** M1 asserts
   containment for reads that cross the instrumented resolver — not for every
   read. A direct ambient read — a module-level constant, an environment lookup,
   a cached global, a file opened outside the resolver — never reaches the
   instrumentation and passes. The failure is **open**, and it has the same shape
   as D limitation 2's under-collecting walk, one level up. Closing it needs an
   exhaustive capability or sandbox boundary; until then, M1 converts the
   ordinary case from noticing to checking and leaves the ambient case to
   noticing. The scope is written into M1's own text rather than left to this
   list, because a limitation cannot rescue an oracle that fails its own
   sabotage.
2. **An operator's declared schema is authored, not checked.** M6 tests that a
   declaration cannot change; nothing tests that it was right in the first
   place. Whether `affects` really takes a molecular entity and a phenotype, and
   really admits a population dimension, is a human judgment recorded in a
   contract — the same class as D limitation 4 and kernel limitation 8's
   acquisition boundary.
3. **The flat qualifier fragment is narrow, and the narrowness is a throughput
   cost.** Scoped alternation, disjunctive restrictions, more than one
   restriction per dimension, and quantitative ranges are all unrepresentable
   and therefore refused (§6.4). Combined with §6.6, a claim the fragment cannot
   express is queued rather than degraded — correct, and paid for in coverage.
   The grammar is versioned so this can be widened, but nothing here estimates
   how much of the real literature the fragment reaches.
4. **The untypeable-span backlog is unsized.** §6.6 establishes that it exists,
   is distinct from kernel limitation 1's unassessed queue, and is discharged
   only by extending a vocabulary. Nothing measures how large it would be.
5. **M\* is deep only in the claim neighbourhood.** §1's scope ruling was wide
   M₀ / narrow M\*, so this document can detect a defect in claim typing and
   cannot detect one in, say, verification scope derivation. Absence of findings
   outside the neighbourhood is absence of *looking*, which is the same
   principle this system applies everywhere else, turned on itself.
6. **§5's classification freezes nothing.** The nine proposed † labels are an
   overlapping cover, not a partition, and their adoption is undecided (§11).
   Until adopted they are an analytical instrument, and citing them — as §6–§9
   do — is provisional.
7. **The held-ness answer is decided; the mechanism is not.** ρA8 types
   held-ness as `def`, so destroying the last held copy routes to
   `NotAvailable`. Nothing *records* the destruction: the state is reached by a
   check failing rather than by an act being committed, so the system can report
   the honest answer without being able to say when or why it changed (ρO2).
8. **Extraction stays fallible, and the typed form relocates the problem rather
   than removing it.** §6.5 moves linguistic ambiguity out of identity and into
   extraction, where kernel limitation 3 already records a measured 25–40%
   field-level disagreement rate. A typed claim is exactly as trustworthy as the
   typing act that produced it, and that act is a computation with an error rate.
9. **One cross-implementation check.** M10 is the only row that compares Python
   and TypeScript. Everything else in M is single-implementation, so a divergence
   anywhere outside claim projection is invisible to this table — deliberate, on
   D §6's one-fixture-per-shared-encoding precedent, but a real limit.
10. **A kernel-tag re-encoding re-mints every claim.** §7.4 row 5 is an accepted
    severe cost, not a mitigated one. There is no migration path that preserves
    identities across a tag byte change, because the identities *are* the bytes.
11. ~~**Merge and content-derived identity are in unresolved tension.**~~ ρA10
    closed the case where a merge can build a retraction cycle; the wider
    cascade stayed open as ρO5.

    > **Retired 2026-08-08** (`2026-08-08-world-address-ruling.md` §5). The tension had exactly one
    > source — an operation that rewrote inbound references — and that operation
    > is retired. `consolidate` requires one canonical address and rewrites
    > nothing inbound; coreference is additive and its closure is a query-layer
    > expansion. No sanctioned action moves a retraction's exact target tuple, so
    > `Dom(step)` is total and ρO5 closes (§3.2).
    >
    > **What replaces it is narrower and belongs to the world layer**, not here:
    > two addresses persist for one work permanently, with no operation that
    > reduces them (world limitation 3a). That is a cost of the trade, not a
    > tension in the model.
12. **No domain exists**, and this limitation narrows twice (*updated
    2026-08-08*). It read *"nothing here is implemented, and every mechanism in
    §6–§9 is unexercised."* Conformance cut 1 landed 2026-08-07 and built
    **M4, M7, M9, M10, M11 and M13 whole**, plus the selected arms of **M5, M6
    and M8** — the claim grammar, `π_claim`/`tag_claim`, decode, opacity and
    cross-language parity —
    so §6 and §7 are exercised where the cut reached and **M1, M2, M3 and M12
    remain unbuilt** (disposition record §5.2, §5.3). What is unchanged is the
    domain half: the operator contract in §7.1 is still illustrative, its
    `population-group` binding would still be refused at load, and the contract
    that *is* loaded — `fixtures/contracts/testing.yaml` — is deliberately not a
    real domain. This is D limitation 5's position, inherited and now narrowed
    the same way: the rulings are what this design commits to, not the shapes of
    the files.
13. **ρ is applied, and four of its rows are now the only record of what the
    corpus used to say.** §8's amendments landed in the 2026-08-05 banking
    commit, so §8.2 is no longer a proposal — but that inverts the reading
    hazard rather than removing it. Two banked *arguments* were found **invalid**
    and replaced, not merely extended: correction §4's digest-containment
    well-foundedness proof (ρA9) and `unknown` as evidence of non-membership
    (ρA7). Both replacements are stated at their sites with the withdrawn text
    quoted, because a reader encountering only the new text has no way to know an
    argument was retired rather than refined. The same applies to kernel §4.1's
    identity basis (ρA1) and world §4.3's curator-assertion arm (ρA10). What is
    **not** banked is anything in §8.4: ρO1–ρO5 name requirements with no
    mechanism, and their homes — kernel limitation 4, world §10, D §12 — record
    them as open.

## 11. Open questions

**Carried from ρ, with their motivation.**

- **Binding-check persistence and epistemic effect (ρO1).** Whether the receipt
  persists at all; how it is discovered; how it is superseded; what corrects a
  claim later found `not-member`; and whether an unchecked claim may be assessed
  before its check is performed. The banked correction rules make the obvious
  path unspellable (§7.2), so the answer is either a lifecycle design or
  promotion to an independently addressed record. **The trigger is already
  defined**: needing independent supersession and correction is D's own
  promotion condition, so the day a binding check needs to be corrected rather
  than merely reported is the day option 2 becomes the answer.
- **The held-ness recording mechanism (ρO2).** What, if anything, records the
  destruction of a last held copy. §4.3 withdrew the recorded-loss repair as
  premature; it stays withdrawn, and limitation 7 is its residue.
- **Claim entailment and subsumption (ρO3).** §6.7 keeps the encoding capable of
  expressing it and defines nothing. The motivation is concrete and worth
  recording so a later design does not have to rediscover it: **belief
  aggregation across related claims** needs it — without an order, a corpus
  holding a claim about adults and a claim about humans has two unrelated belief
  states and no way to say whether the evidence could bear on both. **Necessary,
  not sufficient:** an entailment relation supplies the structure and does not by
  itself license transferring evidence from one claim to the other; that
  additionally requires estimand and evidence compatibility, which is a separate
  question below. The three barriers are named in §6.7, and the
  population-reversal case is why the intuition itself, not merely its
  formalization, must be distrusted.
- **Estimand match (ρO3).** Kernel limitation 5's residue becomes stateable as
  `match(claim_type, estimand_type)` once claims are typed. Whether it is
  definable *from* entailment, or is a related but independent relation, is
  open — §6.7 declines to assume the former.
- **A population vocabulary (ρO4).** None is selected, and none of the obvious
  ontologies is one. Until a contract binds one, a population-qualified claim is
  untypeable — which makes this the first concrete instance of limitation 3's
  cost rather than a detail.
- **Domain contract versioning policy (ρC1).** D §12's question, now bounded:
  whatever it becomes must be compatible with §8.3's four adopted succession
  rules. What counts as a breaking change to a **facet** contract, and whether a
  declared compatibility range is needed, stays open and should be settled with
  5b's versioning rules.

**Raised by this document and not resolved in it.**

- **Adoption of the nine † labels.** §5 deliberately freezes nothing. Adopting
  them means committing the banked tables to a vocabulary; not adopting them
  means §6–§9's classifications are annotations. The decision is cheap now and
  expensive after the labels appear in oracle prose.
- **What triggers the next M\* expansion.** §1 rules that M\* widens only when
  another design question requires it. The two nearest candidates are
  verification scope derivation (whose laws §5 shows are transition laws the
  reading-based taxonomy structurally misses) and the assessment/estimand
  neighbourhood, which ρO3 already reaches into.
- **Quantitative restrictions.** The likely first extension to the qualifier
  grammar — *"in adults over 65"*, *"at doses above X"* — and the one that
  breaks the flat fragment's single-referent-per-dimension shape rather than
  merely stretching it. Worth designing deliberately rather than as a patch,
  because a quantitative restriction is where a bound referent stops being an
  ontology term.
- **Where domain-neutral operators live.** §7.1 rules that operators are
  domain-issued without exception and that `subtype-of` and its kin belong to a
  general-purpose domain contract. **What is open is only its namespace,
  ownership and distribution.** Whatever it is called, it remains an **ordinary,
  conditionally consulted domain contract** — it does not become base-adjacent,
  does not acquire unconditional membership in the consulted set, and does not
  get to issue anything the base contract owns. Treating it as "distinguished"
  in any stronger sense would reopen §7.1's uniform rule through the back door,
  which is precisely why that rule is uniform.
- **The layer vocabulary's actual contents** — *no longer illustrative, and the
  admission rule now exists* (updated 2026-08-08). `contracts/science/CONTRACT.yaml`
  declares `layers: [causal, structural, statistical, methodological]`, so the set
  is authored data in the base contract rather than an example in this section,
  and editing it re-identifies every claim (§7.4 row 5). What stays open is what
  *belongs* in it — and that question now has a procedure rather than a taste:
  the corpus survey's **2.6** (agreement and exercise across the eight surveyed
  corpora, then the reader clause) is what admits a value, and it has already
  refused one. `mechanistic_narrative` failed on exercise — all 13 records
  carrying it are unstructured, so the layer would admit zero claims — and the
  kernel's §4.2 `mechanism` row was corrected rather than the set widened to make
  it true (typing exercise §5.2, kernel §4.2 as amended 2026-08-07).
  **This is not kernel §11's non-empirical question, and the two must not be
  merged:** a non-empirical proposition is blocked by the
  `observes` eligibility rule, which reads the assessment's run and not the
  claim's layer, so no layer vocabulary can make one assessable. Adding a layer
  changes what a claim can *say*; a second route — proof, derivation, simulation,
  with its own eligibility predicate and guarantees — is what would change what
  belief can *reach*. That route stays kernel §11's, unamended here.
- **Which locales `render` supports.** The **interface is settled here**:
  `render(Claim, Locale) → String`, with the locale an explicit parameter. An
  ambient locale would make the function non-deterministic in its arguments —
  the same defect `decodeClaim` had before `ResolutionSnapshot` became a
  parameter (§7.2) — and that is a defect whether or not the output is stored.
  What stays open is only which locales exist and who supplies their
  vocabulary strings.
