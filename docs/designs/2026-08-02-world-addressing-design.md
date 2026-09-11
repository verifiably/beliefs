# World and addressing — design

**Date:** 2026-08-02
**Status:** design
**Scope:** sub-problem 3 of 7 in the system redesign
**Depends on:** [`2026-08-02-epistemic-kernel-design.md`](2026-08-02-epistemic-kernel-design.md),
[`2026-08-02-substrate-consolidation-design.md`](2026-08-02-substrate-consolidation-design.md)

## 1. Why

`meta/entities/hypotheses/0007-working-model.md` already rules this, and says so
in the model's own voice: *"all projects live in one world, and a project is
sub-structure … A cross-project reference is thus a same-world reference crossing
a sub-structure boundary, not a foreign reference needing a bridge."* It then
records the opposite as shipped behaviour and calls it *"a known limitation, not
the model's stance."* `t068` tracks the gap, and names it as the single primitive
that `t015` (freshness propagation), `t018` (typed blockers) and `t043`
(cross-project blockers) each separately defer.

So the stance is settled and the mechanism is missing. This document supplies the
mechanism. What follows is what measurement adds to the ruling.

### 1.1 Identity is not world-unique, and collisions are ambiguous

Across the three projects with entity trees (mm30, health/meta, science/meta):
**3,358 distinct `kind:slug` ids, 5 of which collide across projects.** (A sixth
scan hit, `entities:research-question`, is an artifact of deriving the kind from
the parent directory — both files sit at `entities/research-question.md`, at the
tree root rather than in a kind directory. It is not an entity and is excluded.)

The five split, and the split is the whole problem:

| colliding id | mm30 / science-meta | health/meta | same referent? |
|---|---|---|---|
| `paper:Chen2023` | scRNA-seq tumor programs (`10.1186/s13578-023-00971-2`) | mitochondrial dynamics in health and disease | **no** |
| `paper:Liu2020` | joint mixed sparse graphical models | robustness in multilayer biological networks | **no** |
| `paper:Shi2025` | NPM1/CXCR4 bortezomib resistance (`10.1080/16078454.2025.2565956`) | cross-tissue multicellular coordination in cancer | **no** |
| `dataset:depmap` | "DepMap" | "Cancer Dependency Map (DepMap)" | same programme, **neither names a release** |
| `dataset:tcga` | "TCGA — Pan-Cancer Cohort" | "The Cancer Genome Atlas (TCGA)" | same programme, **neither names a release** |

Same grammar, and **the id cannot tell you which**. A citekey is a nominal
handle: `Chen2023` names an author-year, and author-years are not unique. This is
the kernel's proposition ruling arriving at a second kind — a nominal identifier
cannot carry identity, because it is stable under changes of referent and
unstable under changes of nothing.

The dataset rows are the more interesting half, and they are **not** a
merge-two-into-one case. Neither record pins a release; health's own record says
so in a note: *"DepMap bulk release files are publicly downloadable … reproducible
analyses should pin the exact quarterly release."* Two descriptive stubs naming
the same programme do not denote the same *data*, and a merge would assert they
did. §4.2 rules on what they are instead.

### 1.2 The URI layer already conflates; only context keeps it apart

`graph/io.py:44` mints entity URIs as:

```python
PROJECT_NS[f"{kind}/{slug.lower()}"]      # PROJECT_NS = http://example.org/project/
```

**No project component.** mm30's `paper:Chen2023` and health's `paper:Chen2023`
produce the *identical* URI. What separates them is not identity but **quad
context**: `graph/composite.py:30` files each project's triples into a named graph
keyed `cancer://<project-id>`. Separation is by convention of storage, and any
query over the union sees one node where there are two papers.

Two unrelated URI schemes are live at once — `http://example.org/project/` for
entities and `cancer://` for projects — the first a placeholder, the second a
leftover of the toolkit's origin as a cancer-specific tool. Neither is a world
namespace, and no code path assigns one.

### 1.3 The collision hazard is observed, not projected

`fb-2026-07-11-018`: promoting science-meta's `Liu2025` minted canonical
`paper:Liu2025`, which **shadowed** natural-systems' `Liu2025` (a GNN paper) and
multiple-myeloma's `Liu2025` (single-cell 3D genomes) — *"the OTHER projects'
local same-keyed paper stops resolving."* Three different papers, one id, silent
capture. Marked addressed: a collision check was added **to the promotion path**.
The measurement in §1.1 is what that fix leaves behind — `Chen2023` and `Liu2020`
still collide today, harmlessly, because nothing yet puts them in one space.

Fixing the writer that creates a collision does not fix an identity scheme that
permits one. That is the difference between this document and `fb-2026-07-11-018`.

### 1.4 The bridge has a measured cost, and views leak through it

The commons promotion/overlay machinery — the current answer to "the same thing
appears in two projects" — measures **≈4,500 lines**: `promote.py` 2,246,
`overlay.py` 669, `promote_dataset.py` 547, `identity_resolve.py` 399,
`promote_types.py` 322, `promote_render.py` 308. **39 modules** mention overlays.

And it is not containable. `fb-2026-07-30-019` (open): the topic-coverage
instrument globs `entities/topics/*.md` and `entities/papers/*.md`, so it is
**blind to every commons-promoted entity** — while `science refs check`,
`science graph audit` and `graph.trig` all resolve them correctly. The report is
worth quoting because it is the shape of the defect, not an instance: every
consumer must remember that an entity may live somewhere else, and one that
forgets produces a clean-looking wrong answer. `fb-2026-07-18-006` (deferred) is
the same class — commons ref resolution that is *indentation-sensitive*.

A federation bridge is a fact that every reader must know. A single space is a
fact no reader needs to know.

## 2. The ruling — one world, and a project is a view

> **One addressable space.** There is exactly one world. Every world entity has
> one identity in it, independent of which project surfaced it, which repository
> stores it, and which projects reference it. A reference is a reference; there
> is no cross-project reference *category*.
>
> **A project is a view plus local coordination.** It selects from the world,
> and it owns work state about that selection. It does not own the entities.

### 2.1 The stored address is derived from identity, not from the handle

A first draft of this design kept `kind:slug` as the stored reference form while
allowing two `paper:Chen2023` nodes to coexist. That is incoherent: the stored
ref is then ambiguous *by construction*, and an `id-collision` finding does not
help — a finding reports a problem, it does not tell an existing binding which
node it meant.

> **Rule.** A world entity's **stored address** is `kind:<basis-digest>`, derived
> from its identity basis (§4.2) and world-unique. Every stored reference —
> relation endpoints, membership, facet refs — uses it. The human handle
> (`Chen2023`) survives as an **alias** carried on the node, and aliases are
> explicitly **not** unique.

This stays inside the `nodes` id grammar (`STANDARD.md` §3: slug matches
`^[A-Za-z0-9][A-Za-z0-9:_.-]*$`), so no substrate change is needed to hold it.

Human-typed handles remain the authoring surface — nobody writes a digest in
`related:`. They are **input**, resolved through an alias index at authoring
time, and an alias matching more than one world entity is a **refusal** naming
the candidates, never a guess. That is the fourth resolution state in §5.1.

> **Where aliases live.** A **Science-profile facet** persisted on the node —
> the existing substrate primitive, requiring no `nodes` change (`STANDARD.md`
> §2.3: named typed payloads with schemas enforced by invariants). The world
> index **derives** an `alias → [world address]` multimap from those facets and
> is a cache, never a second source of truth.

Three alternatives are rejected. **Adding aliases to `nodes`** buys a Python
implementation, a TypeScript implementation, fixtures and a standard bump for
something a facet already expresses. **Storing them only in the world index**
makes the index authoritative for content that belongs on the node, so a corpus
would no longer be self-describing. **Reusing `deprecated_ids`** is the subtlest
error and the one worth naming: it is rename *history*, and `nodes` requires a
deprecated id not to collide with a live one — precisely the uniqueness
constraint aliases must not have.

The two forms divide cleanly: **the address is what the system stores, the handle
is what a human types**, and the second is allowed to be ambiguous precisely
because it is never the thing stored. Stored refs hold addresses; resolution binds
an address to the `uid` that carries continuity (§4.1).

> **Amended 2026-08-08 — the stored alias is retired**
> (`2026-08-08-world-address-ruling.md` §4). The address rule above stands and is
> upheld; **the alias half does not**. A label is now **computed on read** —
> `preferred_label(identifier, pinned_authority_release)` for an authority
> identifier, kind-specific rendering from immutable record content otherwise —
> and is **never stored as world content**. The alias facet, the world index's
> `alias → [world address]` map, and the alias arm of `ambiguous` all retire with
> it. Search terms are authority-provided synonyms resolved against a **pinned
> snapshot, never a live lookup**; a term matching two identifiers is still a
> refusal naming candidates (W9, restated), but the ambiguity is now a
> reproducible property of the pinned snapshot rather than of accumulated
> authoring.
>
> **The three rejected alternatives above share a premise, and it is the defect.**
> All three ask *where an alias lives*; none asks **whether one is stored at all**.
> That is the same omission F9 charges against §4 — rejecting the adjacent
> alternatives while never reaching the one that dissolves the question — recurring
> one level down, and it is recorded here rather than quietly repaired.
>
> The sentence that survives all of it is the last one: **the address is what the
> system stores, the handle is what a human types.** Retiring the stored alias is
> that sentence taken literally.

### 2.2 What `t068` asked, and what closes it

`t068` asks for a cross-project *entity* reference syntax. Under §2 that category
is gone: a world entity is addressed by §2.1's world address, unqualified,
because the reference crosses nothing. `pan-disease::task:t071` is not the answer
for entities.

But `t068` exists to unblock `t018` (typed blockers) and `t043` (cross-project
blockers), and those are about **tasks** — which §3 keeps project-scoped. One
world makes project a *grouping level*; it does not erase scope for records that
are project-owned. So `t068` needs both halves, and §6.1 supplies the second.

**Rejected alternatives**, recorded so they are not re-proposed:

- **Keep per-project corpora and improve the bridge.** This is the status quo, and
  §1.4 prices it: ~4,500 lines, 39 modules that must remember, and a live open
  defect where a consumer forgot. Each fix is per-consumer, so the class stays
  open indefinitely.
- **Make the project part of the identity** (`project:kind:slug` as the stored
  id). This is the tempting one, and it fails on a property the kernel already
  fixed: identity would then change when an entity moves between projects, or
  when a project is renamed — a *nominal* change silently retargeting every
  reference bound to it. It also makes "the same paper in two projects" formally
  two entities, which is the defect, promoted to a rule.
- **Globally rename to guarantee uniqueness.** Treats the symptom. Uniqueness
  achieved by convention decays exactly as citekeys did, and nothing prevents the
  next `Chen2024`.

## 3. What is in the world, and what is not

Not every record is a world fact, and the kernel's decomposition already draws
the line — this document only names it as an addressing rule.

| tier | kinds | identity | scope |
|---|---|---|---|
| **World** | the 8 kernel kinds (§4.2): `proposition`, `source-assertion`, `assessment`, `analysis-spec`, `run`, `verification`, `dataset`, `source` — 10 since 2026-08-03, adding `retraction` (correction-lifecycle §3) and `instrument-certification` (normative-contract §7.2); **11 since 2026-08-08**, adding `coreference-attestation` (world address ruling §5.1) | world-unique address, derived (§4) | one space |
| **Views** | `hypothesis`, `question`, `theme`, `topic` | project-scoped name over a world query | per project |
| **Coordination** | `task`, `decision` | project-scoped | per project |
| **Notes** | `note` — belief-inert prose, including curation stubs (§4.2) and project commentary on a world entity (§4.3) | project-scoped | per project |
| **Referents** | `term` | the ontology's own identifier | external |

The world contains what is **true or done**: claims, sources, data, executions,
and their verifications. It does not contain what is **planned or organised** —
tasks, decisions, and the saved views that group things for a human purpose.

Two consequences worth stating, because both are load-bearing:

- **Coordination needs no world identity, so it needs no migration.** Two projects
  may both have a `t068`; they are different tasks and always were. This removes
  the largest and least interesting part of the corpus from the problem.
- **A view is defined over the world but evaluated in a project.** Sharing a
  view *definition* is ordinary reuse; it does not make the view a world fact.
  A topic is a saved query, not a thing that exists.

## 4. Identity in one world

### 4.1 A nominal id cannot be a canonical address

§1.1 is the general case of the kernel's proposition rule. The kernel required a
proposition's identity to be a hash over the claim's own structure — since
2026-08-05, over its typed projection, and before that over a normalized
statement plus factored fields (kernel §4.1) — because a nominal title was
editable without consequence. `paper:Chen2023` fails
the same test from the other direction: it is *stable* while its referent
changes, so two referents can wear it at once.

> **Rule.** A world entity's **canonical address** is derived from a
> **kind-declared identity basis**, never from its file path, its directory, or
> its slug. The `nodes` `id` *is* that address (§2.1); ~~the former slug survives
> as a non-unique alias~~ — *retired 2026-08-08 (`2026-08-08-world-address-ruling.md` §4): no slug
> survives as stored content; a label is rendered on read, and a search term is an
> authority-provided synonym rather than a persisted one.*

**Two things are being named here, and conflating them caused a contradiction
between this section and §4.4.** Keep them apart:

| | what it is | how it moves |
|---|---|---|
| **entity continuity** | the `nodes` `uid` — what resolution binds an address to | a **persisting entity keeps its `uid`**, across rename and across ~~merge~~ **`consolidate`** *(2026-08-08)*. `consolidate` **preserves a shared input `uid`, or selects one of two distinct ones** *(2026-08-09)*; a distinct removed `uid` ceases to be live. If the inputs already share a `uid` (the duplicate-location case, §4.1 below), nothing is retired |
| **canonical address** | the current basis-derived `id`, and what a stored ref holds | **changes** when the basis is corrected (§4.4) or the entity is merged (§4.3) |

Saying "identity is derived from the basis" collapses both and makes §4.4's
address correction read as a change of identity, which it is not. What the basis
determines is the *address*. Continuity is `uid`, it is opaque, and no basis
change touches it — which is exactly why a corrected DOI disturbs nothing bound
to the entity.

#### `uid` uniqueness is a Science invariant, not an inherited one

Promoting `uid` to world continuity asks more of it than `nodes` promises.
`STANDARD.md` §3 requires a **corpus** to reject a duplicate `uid`; it says
nothing across corpora, and cannot, since a corpus does not know the others
exist. So the world-level rule is Science's to state and enforce:

| observation | meaning |
|---|---|
| one `uid`, **different** canonical addresses | **corruption** — two entities were assigned one continuity anchor, and no authored act produces this |
| **one canonical address**, two records — one corpus or two, `uid`s **shared or distinct** | a **duplicate-location** migration state (§5), resolved by **`consolidate`** — *the operation was merge, retired 2026-08-08 (`2026-08-08-world-address-ruling.md` §5.4). **Corrected 2026-08-09:** this row read "one `uid`, same canonical address, two corpora". Equal bases give an equal address and **not** an equal `uid`, which is opaque and minted per authoring act, so the `uid` conjunct excluded the ordinary case — two corpora that independently authored one source from one DOI* |

The distinction matters because the two look alike in a naive scan and have
opposite handling: the second is expected during migration and repaired by an
ordinary authored **`consolidate`**; the first means something upstream is broken
and no repair is safe until it is understood — and `consolidate` is unavailable
there by construction, since it **requires** one canonical address.

**`consolidate` preserves a shared `uid` and otherwise selects one; it never mints.**
Where the inputs share a `uid` it survives untouched. Where they carry **distinct**
`uid`s the survivor keeps **one input** `uid`, the other ceases to be live, and **no
third `uid` is created**. *(Restated 2026-08-08, `2026-08-08-world-address-ruling.md` §5.4; the
operation was merge. The two-case split was added 2026-08-09 — the single "selects"
rule silently assumed the shared-`uid` case was the only one.)*

The objection to a third `uid` is not that bindings would break — they would not.
Stored refs hold *addresses*, never `uid`s (`STANDARD.md` §3), so every prior
reference resolves through §4.3's redirects regardless of which `uid` sits behind
them. The objection is that minting a third **discards both continuity anchors
for nothing**: two entities that existed and were reasoned about become a third
that never did, and anything holding a `uid` — indexes, caches, external records
of what was assessed — is invalidated to no purpose.

### 4.2 The basis, ruled per kind

A basis assigned by *category* rather than per kind produced three defects in the
first draft, so each of the eight kernel kinds is ruled individually. The ninth,
`retraction`, arrived after banking and is ruled the same way in the
correction-lifecycle design §3: a world kind with a content-derived basis over
target, reason, grounds, actor, and a minted event token. The tenth,
`instrument-certification` (normative-contract design §7.1–§7.2, 2026-08-03),
is ruled in the table below. The eleventh, `coreference-attestation`
(`2026-08-08-world-address-ruling.md` §5.1), is ruled on the `retraction`
precedent and appears in the table below.

> **The rule this table instances, stated generally (2026-08-08).** Every
> addressable world entity has the basis declared for its kind: an **intrinsic**
> basis, or an identifier from an **accepted authority**. A missing basis makes
> the record a project-scoped **curation note**, not a weakened world entity —
> and, added with the ruling, **a curation note cannot be the target of a
> semantic reference**, since belief-inertness constrains what a note may do to
> belief but not what may point at one. The missing-basis rule below was stated
> for `source` and `dataset` only; generalizing it is what makes this table a
> rule rather than a list.

| kind | basis | why not otherwise |
|---|---|---|
| `proposition` | kernel §4.1 semantic hash | already ruled |
| `source-assertion` | hash over **(source identity, anchored span, stance, proposition identity)** | the proposition hash alone would make every paper's assertion of P *the same node*, collapsing the discourse counts §6 of the kernel is built to compute — one assertion where the corpus holds forty |
| `source` | external identifier — DOI, PMID, ISBN, accession — normalized *— normalized per scheme and selected by fixed precedence doi > pmid > isbn > accession, addressed as the domain digest under `science.source-address.v1` (2026-09-10, slice 2b §3)* | a work's identity is issued by the world, not computed by us |
| `dataset` | **content identity** — the **dataset basis projection** over the declared resources' digests: deduplicated, sorted, `\n`-joined, digested (*projection ruled 2026-08-09, `2026-08-09-admission-ramp-design.md` §6.2; the row previously read "manifest/content hash", which named no canonical derivation and so gave two implementations two addresses*) | a provider identifier names a *programme*, not data — §1.1's DepMap rows are exactly this confusion. Provider identifiers and accessions are ~~**aliases**~~ **authority-identifier fields** (`programme`, `release`) carried in the record, not the basis — *amended 2026-08-08 with the alias's retirement; the three levels (programme, release, held bytes) are distinct fields and a normalizer may never collapse them* |
| `analysis-spec` | content identity | frozen pre-run by the kernel; immutable by construction |
| `run` | content identity of the execution closure — specified by sub-problem 4 §4.1 as **recipe + result + occurrence** | immutable by construction; the occurrence's minted event token is what keeps two identical executions distinct |
| `verification` | content identity over (**ordered** run identities, equivalence-rule identity, **comparison-report identity**, **scope-derivation rule identity**, scope, verdict) — **extended** by sub-problem 4 §7.3b | kernel §3.3 states it is immutable; scope depends on evidence outside both runs, and that evidence is carried **inline in the comparison report** — including, since 2026-08-03 (normative-contract §6, §7.6), the exact `(rule identity, implementation content identity)` binding each executed rule ran under and the semantic certification-discovery evidence — so the report's digest is what makes two differently-evidenced verifications two nodes |
| `assessment` | **(analysis-spec identity, run identity, proposition identity)** | a **key over the derivation's inputs**: sub-problem 4 §5.1 gives the facet one constructor taking the run ref alone, so the triple is exactly what determines every field. The first draft's rationale — preserving "assessment revisions" from a content hash — is **retired with the revision concept** (§5.1 there); the basis is unchanged and now justified by the derivation rather than by a lifecycle that cannot occur. The exact rule binding is inside the triple already: `rule_bindings` is a recipe member (sub-problem 4 §4.2, amended 2026-08-03, 5b §6), so it reaches this basis through `run` |
| `instrument-certification` | content identity over (**contract identity**, the **discriminated subject** — `equivalence` \| `interpretation` \| `scope-derivation` over a rule binding, or `falsification` over (spec identity, interpretation binding) — the **implementation content identity**, and the **witness evaluations**) — added 2026-08-03, normative-contract design §7.1–§7.2 | a derived demonstration on the `verification` precedent: identical content is identical identity, re-derivation is idempotent, and **no event token** — a retracted certification re-minted byte-identical stays retracted, and under a successor cut it is a different record; the rule identity contains the fixture-set identity, one spelling only (5b §6) |
| `coreference-attestation` | content identity over (**sorted endpoint pair**, **stance**, **actor**, **grounds**, **minted event token**) — added 2026-08-08, world address ruling §5.1 | the `retraction` precedent exactly. Sorting the pair makes `{A, B}` one identity regardless of authoring order; the event token keeps two genuinely distinct attestation *events* distinct, as the occurrence token does for `run`. The token is deliberately **outside** the balance's deduplication key (§5.2 there), so repeated identical submissions preserve provenance without manufacturing weight |
| `holdings-observation` | content identity of the §2 canonical facet under **`science.holdings-observation.v1`** — every field participating, the minted **event token** among them on the `retraction` shape's precedent, `supersedes` hashing as its deduplicated sequence sorted by canonical reference bytes — added 2026-08-10, verified-holdings record design §2 | the `coreference-attestation` precedent: the event token keeps two genuinely distinct observation *events* distinct however the clock reads; the sorted `supersedes` encoding gives one predecessor set one identity, since `science.identity.v1` refuses sets |
| `act-report` | content identity of the whole canonical facet under **`science.act-report.v1`** — every field participating: the operation kind, the report occurrence's minted **event token**, actor, observer, instrument, `opened_at`/`closed_at`, and `entries` as a **canonical sequence**, order identity-bearing — added 2026-08-11, act-report design §2.3 | the `run` occurrence precedent: the event token keeps two operations with equal actors, timestamps and entries distinct (T8); the ordered `entries` encoding makes a permutation a different report (T6), because a finding is cited as **(act-report ref, entry index)** and position must therefore be identity-bearing |

Two of these correct claims the first draft made against the kernel rather than
from it. `source-assertion` sharing the proposition's hash would have destroyed
the divergence machinery; `assessment` as content-addressed contradicts the
revision concept the belief digest depends on. The pattern in both is the same —
a category applied to a kind whose contract says otherwise.

**Dataset, specifically** *(split 2026-08-09, admission ramp §2.2 and §6.4;
this paragraph previously read "content identity means a dataset entity denotes
data we hold")*. Content identity means a dataset entity **says which bytes it
is**. That is a different property from holding those bytes, and the two are
separated here deliberately: a content-addressed dataset whose bytes are not in
hand has a basis, is a world dataset, and is refused at the *eligibility* gate by
kernel `G2b` — not at this one. Reading the two as one made that state
unreachable by construction, which is the defect the narrowing repairs.

A descriptive stub naming a programme with no release pinned — both §1.1 dataset
rows — fails the narrowed test too, and for the original reason: nothing in it
says which bytes, so there is no content identity to record and §4.2's
unavailable rule applies. It is not a world dataset yet. Health's own note
already says why.

**Kinds whose basis is unavailable — the record is not that kind yet.** A source
with no DOI; a dataset stub with no content identity. Calling such a record a
project-scoped `source` does not work: §2.1 gives world kinds a basis-derived
address, and it has no basis, so it would be a kernel kind with **no legal
address in either form**.

> **Rule.** Creating a `source` or `dataset` without its basis is **refused** at
> the write boundary. What may be authored instead — as a separate, explicit act
> — is a **project-scoped `note`**: a curation stub recording what is known and
> what is missing. **Supplying the basis mints the world entity**, and the note
> is what it was minted from.

The refusal and the note are deliberately two operations. Silently accepting a
`source` and storing it as a note would be a kind coercion — the author asked for
one thing and the system persisted another, which is the class of implicit
behaviour this redesign exists to remove.

"Without its basis" for a `source` means **no accepted external identifier at
all** — not merely no DOI. A PMID, ISBN or accession is a basis; §4.2 lists them
as alternatives, not as fallbacks.

This is stricter than it first sounds, and it is the same move the kernel makes
with eligibility: a thing is not admitted in a weakened form, it is simply not
yet the thing. §1.1's two dataset rows are notes about the DepMap and TCGA
programmes, and they become datasets when a release is pinned and held.

No fallback identity is derived at any point, because a fabricated identity is
indistinguishable from a real one everywhere downstream.

> **This is a refusal, not a degradation.** The alternative — deriving a basis
> from title and year when no identifier exists — would mint exactly the
> collisions of §1.1 under a longer name.

### 4.3 Merge is a claim, and claims are recorded

> **Amended 2026-08-08 — structural merge is retired**
> (`2026-08-08-world-address-ruling.md` §5). This section's *premise* is upheld and
> its *mechanism* is withdrawn. Coreference remains a claim, recorded and
> attributed; it no longer collapses the graph.
>
> - **Same-basis coreference** is unchanged and stays mechanical (W2).
> - **Different-basis coreference** becomes a `coreference-attestation` (§4.2) —
>   attributed, additive, carrying a signed stance, with a **derived** balance.
>   Both records stand, both addresses persist, and **no address retires and no
>   inbound reference is rewritten**. A positive standing balance activates a
>   semantic coreference edge; zero or negative does not.
> - **Closure is a query-layer operation.** It never rewrites a stored reference,
>   an identity, or a belief input — retraction targets, `π_claim` positions,
>   `belief_input_digest` members and every content-identity basis read **exact
>   addresses**. This is what stops coreferenced retractions from recreating the
>   cycle merge could close, and what keeps `dataset` coreference out of belief.
> - **The duplicate-location exit** — one identity in two corpora, which this
>   section resolved by an authored merge — moves to **`consolidate`** (ruling
>   §5.4): one canonical address required, content and location reconciled,
>   outgoing relations unioned, divergent lineage bases preserved, **no redirect
>   and no inbound rewrite**. Naming it separately is the point: it is a storage
>   repair, not an identity claim, and the single word "merge" was hiding the
>   difference.
> - **"Curator assertion" is retired as a term of art.** An attestation is
>   **attributed to an attester**, and no attester class is privileged: human and
>   agent attestations carry equal unit weight. That unit weight is **this
>   ruling's own default**, not an inheritance — the belief policy is the
>   precedent, and its **ρO3** blocker governs *study-design* weighting inside
>   belief, which an attester balance is outside of (ruling §5.3). The default is
>   chosen for the same reason ρO3 exists: reliability is to be *measured* — a
>   `meta/` question — never assumed by category.
>
> **Limitation 3 retires with the mechanism**: "merge is recorded, not reversible"
> described an operation that no longer exists.

Two records of one paper carrying the same normalized DOI should become one node;
`paper:Chen2023` × 2 must not, because their DOIs differ. Under §4.2 the *bases*
answer both — but only where the bases are present, and today they frequently are
not.

(The §1.1 DepMap rows are **not** an example of this: under §4.2 they hold no
content, so they are notes, and there is nothing to merge. An earlier draft used
them here on the strength of a shared provider identifier, which the
content-identity ruling removed.)

> **Rule** (amended 2026-08-05 — formal model ρA10). Merging two records into one
> world entity is an authored, recorded act with a basis: either **both bases
> agree** (coreference is established mechanically), or a curator asserts the
> identification and the assertion is stored with its rationale. An unrecorded
> merge is not available. **The curator-assertion arm does not reach
> `retraction`s.** Two retractions may be merged **only** when their bases are
> equal; a curator-asserted merge of **distinct-basis** retractions is
> **refused**.

**Why retractions are the one exception.** Merge rewrites every reachable inbound
reference (W4), so it **redirects** existing edges rather than adding one — and
that is enough to build a cycle out of two valid states. Take `T → S → R`, where
`S` retracts `T` and `R` retracts `S`, and merge `T` into `R`: rewriting `S`'s
inbound reference retargets it at `R`, and the graph now holds `R ↔ S`.
Correction's `standing` recursion follows exactly those edges, and its
termination rests on the retraction graph being **acyclic** (correction §4, as
amended 2026-08-05). A curator asserting that two **different** retraction acts
are one is the single sanctioned operation that can close such a cycle — and it
is an assertion the event token already contradicts, since distinct acts are
distinct by construction.

**Equal-basis consolidation must survive, and does.** Two *replicas* of one
retraction held in two corpora are §5's `duplicate location` state — one
identity, two corpora — for which an authored merge is the only prescribed
resolution; refusing them would leave a banked state with nowhere to go.
Consolidating replicas changes location and not the graph: no target tuple moves,
no identity is re-minted, and a counter-retraction already targeting that
retraction is untouched. An earlier draft of this amendment excluded retractions
from merge outright, which conflated **semantic identity** with **physical
multiplicity**.

**What this rule does not settle.** It closes the *cycle* case only. A merge of
any two records that would rewrite some retraction's **exact target tuple** —
merging assessment `A` into `A′` while `S` retracts `A`, say — changes `S`'s
content and therefore its content-derived identity, re-minting `S` and cascading
through every record that names it. That tension between W4's inbound rewrite and
content-derived identity has **no ruled outcome**, and is recorded as open in §10
(formal model ρO5).

**An equal basis — hence an equal canonical address — establishes coreference; it
does not decide whose content survives.** Two records of the same source carry different bodies, different
facets, and different relations, and the basis says nothing about any of them.
Mechanical field-level merging would need a precedence rule — first corpus,
longest field, most recent — and §5 rejects precedence for exactly the reason it
would apply here: it is a silent answer to a question with more than one right
answer.

> **Rule.** A merge **produces one file in one corpus**. Which corpus holds it,
> and which content survives field by field, are part of the authored act.
> Relations are then handled by **two distinct operations**:
>
> 1. **Outgoing** — the two nodes' own relations are **unioned** onto the
>    survivor.
> 2. **Redirect** — the survivor's `deprecated_ids` becomes
>
>    ```text
>    (every input node's live address ∪ every input node's deprecated addresses)
>      −  the survivor's own live address
>    ```
>
>    and world resolution consults it. This happens at merge time and does not
>    depend on any referrer being present.
> 3. **Inbound** — every reference held by a third party to any retired address is
>    **rewritten** to the survivor's address, wherever that referrer is reachable.

**"Which content survives field by field" cannot govern a derived field, and one
now exists.** Sub-problem 4 §5.2 stamps a **lineage basis** on every produced
dataset and calls it derived, non-editable and never authored — while a dataset's
address is its **content identity**, so two corpora can hold the same address for
byte-identical output produced independently, with **different bases**. Generic field
selection would then let a curator pick which route is authoritative for
independence: an authored ancestry, arrived at by a route that never touches the
authoring API, and worth the most precisely when the losing basis's producing run has
also gone. Every guard §5.2 built — derived from the recipe, frozen, no ordinary API
path — sits on the minting side of the record and none of them is looking here.

> **Rule.** A merge **never selects between lineage bases**. If the inputs' routes
> differ, the survivor's basis becomes `conflict([both routes], sorted, distinct)` —
> the tagged shape sub-problem 4 §5.2 defines, which requires **at least two distinct
> routes** — and the dataset is **`lineage-divergent`** (substrate §5 step 2):
> independence over it is `not-certified`. Equal routes merge to the one `single` and
> nothing is recorded. A merge may **widen** `single` to `conflict`, and merging two
> `conflict`s **unions** their routes; it may never **select or drop** a route, which
> is what keeps §5.2's route-preservation true through this path.
>
> **The conflict is permanent under this design.** No operation here resolves it: the
> correction lifecycle that would — retiring a route shown to be wrong — does not exist
> and is handed to sub-problem 5 alongside retraction. A curator merging two disagreeing
> records is recording a fact, not opening a workflow, and should be told so.
>
> **Designed 2026-08-03** (`2026-08-03-correction-lifecycle-design.md`, its `route`
> target arm and C7). The permanence is **under this design** and no further: a
> retraction retires a route, the stored basis facet stays byte-unchanged, and the
> **effective** tag is computed over unretired routes — one survivor certifies over
> that route, several stay `conflict`, zero is `not-certified` and never a silent
> `single`. Retirement composes after merge-widening. Nothing above changes: this
> design still offers no such operation, and until C1–C10 are implemented none
> exists to call.

Preserving the conflict beats refusing the merge, because refusing leaves two nodes
at one address — the duplicate-location state §4.3 says must be resolved — and it
beats selecting, because two independent derivations of one content identity are
exactly what step 3 exists to refuse. It also makes this the **one** form of
divergence that is durable: the conflicting bases are stored on the surviving
descendant, so unlike a divergent producer (sub-problem 4 §11.14) it does not vanish
when a run is deleted. A curator who believes one basis is wrong has the ordinary
route — say so with a record — and not the silent one.

The set expression is not pedantry; a draft that said "both retired addresses"
was wrong three ways. **One input address usually survives** as the survivor's
live address, and `nodes` forbids a live id from also being deprecated
(`STANDARD.md` §3 rejects a node claiming a live id or another node's active
deprecated id). **Equal-basis duplicates share one address** — §2.1 derives the
address from the basis, so the mechanical merge case has one address between the
two nodes, not two. And **the removed node carries its own history**: its
`deprecated_ids` are addresses that already resolved to it, and dropping them on
merge breaks references the merge was supposed to preserve.

**The redirect is what makes the merge safe; the rewrite is hygiene.** An earlier
draft had only the rewrite, which left a referrer in an unavailable corpus
pointing at an address that no longer resolved — a merge whose correctness
depended on how much of the world happened to be checked out. With the redirect
recorded on the survivor, the old address keeps resolving whether or not the
referrer was ever visited, and the rewrite becomes an optimization that shortens
the path.

**`deprecated_ids` is the right home, and this is what it is for.** A retired
canonical address was unique and its successor is unambiguous, which is exactly
the shape `nodes` requires — a deprecated id must not collide with a live one
(`STANDARD.md` §3), and resolution already falls through to the deprecated map
after the live one. That constraint is why §2.1 keeps *aliases* out of it: a
human handle is deliberately non-unique. Two mechanisms, and the distinguishing
question is whether the string was ever a unique address.

**No redirect chain is ever formed.** `deprecated_ids` is a flat list and every
entry indexes directly to the live `uid` (`STANDARD.md` §3: resolution is O(1)
through the live map then the deprecated map). The set rule above preserves that
by construction — it accumulates addresses onto one node rather than pointing one
retired address at another — so resolution stays single-hop no matter how many
merges and corrections an entity has been through.

These are not one operation, and an earlier draft ran them together — unioning
relations, then justifying it by inbound-reference preservation, which a union of
outgoing edges does not achieve. Outgoing edges live on the merged nodes and move
with them; inbound edges live in *other* corpora entirely and are untouched by
anything done to the survivor. Missing the second leaves every referrer pointing
at an address that no longer resolves, which is the one outcome that loses
information no later step can recover.

The rewrite is `nodes`' rename mechanics applied across corpora
(`STANDARD.md` §3 rewrites "every position holding `old_id` … in every
referrer"), which is precisely why it needs the world-level reverse index of §5:
corpus-local rename cannot see referrers it does not contain.

Post-migration the invariant is **one identity, one file, one location**, enforced
at the write boundary: an attempt to create a second entity with an existing
identity is refused, exactly as `nodes` already refuses a duplicate id or uid
(`STANDARD.md` §3, `CollisionError`). Two records sharing an identity is therefore
a *migration state*, not a steady state, which is what keeps the world index's map
singular (§5).

**What replaces an overlay.** Today a project's local commentary on a shared
record lives in an overlay file. Under one world there is one node, and
project-specific commentary is a **note** — belief-inert prose, project-scoped by
§3 — that references it. The commentary does not need to be part of the entity,
and making it so is what created the overlay machinery.

Merging is destructive to references in a way splitting is not: if two things were
wrongly merged, every assessment bound to the merged node now bears on a
conflation, and no record says which. That asymmetry is why the recorded form is
required and the mechanical form is preferred.

### 4.4 When a basis changes

A basis is not immutable — a DOI is corrected, a dataset is re-held. Three cases,
and they are genuinely different:

| case | ruling |
|---|---|
| **dataset re-held with a different manifest** | **always a new dataset entity.** Retargeting prior assessments would violate content identity: the assessments observed the old bytes, and saying they observed the new ones is false |
| **corrected external identifier, same referent** | a recorded **address correction**: `uid` is preserved, the node is renamed to the corrected basis-derived address, and the old address is retained in `deprecated_ids` |
| **genuinely different version or work** | a new entity, linked to the old. Prior references stay bound to what they referenced |

The middle case is the one worth stating explicitly, because §2.1's rule read
literally would make a corrected DOI a *different entity*. It is not: a
correction says the earlier address was wrong, not that two works exist. `uid`
survives — which `nodes` guarantees across rename (`STANDARD.md` §3: "`uid` never
changes; a stale ref still resolves through `deprecated_ids`") — so nothing bound
to the entity is disturbed.

Distinguishing the second case from the third is a **curation judgement**, not a
derivation: only a person can say whether a new identifier corrects the old one or
names a different work. The system's job is to refuse to guess, and to record
which was asserted.

This is the same mechanism §4.3's merge needs, arrived at from the other
direction: rename plus `deprecated_ids` plus preserved `uid`. One redirect
mechanism serves both, which is why neither needs a bespoke one.

> **Amended 2026-08-08** (`2026-08-08-world-address-ruling.md` §5). Two changes,
> and the second sharpens a distinction this section blurred.
>
> **"Only a person can say" is withdrawn.** The judgement is not a derivation —
> that part stands — but requiring a *human* to make it privileges an attester
> class by category, which the corpus refuses elsewhere on the same grounds it
> refuses unjustified evidence weights. The belief policy is the **precedent**
> here and not the authority: its ρO3 blocker is about weighting by study design
> *inside belief*, and an attester balance is outside belief entirely. What the
> system requires is that the judgement be
> **attributed to an attester** and recorded. Human and agent attesters carry
> equal weight; reliability is a `meta/` question to be measured, not assumed.
>
> **The middle case splits, and the split is cleaner than the old second/third
> boundary.** The question is not "correction or new work" but *how many
> identifiers legitimately exist*:
>
> | case | ruling |
> |---|---|
> | **the basis was mis-transcribed** — one identifier ever, recorded wrongly | unchanged: a **rename**. `uid` preserved, node renamed to the corrected address, old address retained in `deprecated_ids`. No coreference is involved because there is only one work *and* only one identifier |
> | **the authority replaced or corrected the identifier** — two identifiers legitimately exist | a **`coreference-attestation`** (§4.2). Both records stand, both addresses persist, nothing is renamed and nothing retires |
> | **the record gains an identifier that always existed** (enrichment) — one record, one work | a **rename** iff the selected basis changes; old address retained. An attestation needs two records (slice 2b §6.4) |
> | **genuinely different version or work** | unchanged: a new entity, linked to the old |
>
> The old table put the first two in one row and made the boundary turn on a
> judgement about *works*. It turns on a fact about *identifiers*, which an
> authority snapshot can often settle — and where it cannot, the attestation
> records who said so.

## 5. Storage is not identity

One addressable space does **not** mean one directory, one repository, or one
`nodes` corpus. Projects keep their own repositories, their own git history, and
their own remotes; the commons keeps its role as a store.

This must be stated as a rule because `nodes` forecloses the naive reading:
`STANDARD.md` §4.1 fixes corpus layout at `<root>/<kind>/<slug>.md` — **one
root** — and requires that a corpus walk **skip symlinks**. So a single corpus
cannot be assembled out of several repositories by linking them together. The
options are real and few.

| option | verdict |
|---|---|
| `nodes` gains multi-root corpora | rejected — see below |
| Science composes N corpora behind a world index | **chosen** |
| the world is physically one repository | rejected — discards per-project git history, remotes, and access boundaries for a problem that is not about storage |

**Why not multi-root in `nodes`.** Sub-problem 2's boundary test asks whether the
capability is domain-free. Walking several roots is; but *which* root a node lives
in, *which* roots a given actor can see, and *what happens* when two roots claim
one id are all policy — project membership, permissions, and curation. A
multi-root `nodes` would have to answer the policy questions to be useful, and
each answer costs a Python implementation, a TypeScript implementation,
conformance fixtures, and a `STANDARD.md` bump. The two operations of §3 in that
design were priced deliberately; this would be a much larger one buying a policy
decision Science has to make anyway.

> **The world index.** Science holds **four maps** (two at this design's banking;
> a third and fourth from 2026-08-03 with the producers and retraction maps, 5a
> §4; **membership changed 2026-08-08** — the alias map retired with the stored
> alias and the **coreference** map arrived in its place, world address ruling
> §4.3 and §5.5, leaving the count at four), not one — and they do not share an
> identity:
>
> | map | shape | multiplicity |
> |---|---|---|
> | **address** | live address **and** every `deprecated_ids` entry → `(corpus, uid)` | singular, by the §4.3 invariant and `nodes`' non-collision rule |
> | ~~**alias**~~ | ~~alias → `[canonical address]`~~ | **retired 2026-08-08** — labels are rendered on read, never stored, so no corpus content derives this map (world address ruling §4.3) |
> | **producers** | dataset address → `[run address]`, every run holding a `produces` edge to it | multi-valued; §5.3 gives a reproduced dataset at least two |
> | **retraction** | target identity → `[retraction address]` (correction-lifecycle §4) | multi-valued; event tokens permit several retractions of one target |
> | **coreference** | sorted endpoint pair → `(derived balance, distinct-key count)` — added 2026-08-08 (world address ruling §5.5) | singular per pair. Published **reduced**, not as pointers: the address map carries no content, so an attestation in an absent corpus would otherwise be known to exist and unreadable for its stance. The **edge state is not stored** — `active | inactive | indeterminate` depends on the world a query spans and on whether the receipt resolves now, neither of which an immutable epoch can know, so it is derived per query on the `standing` precedent. **Not** a belief input — coreference is outside belief by that ruling's §5.3 — so it carries no semantic identity and is absent from `belief_input_digest` |
>
> All four are **derived** from corpus state and none is authoritative for it. The
> **producer snapshot** — the producers map together with its coverage declaration —
> carries its own **semantic identity**, separate from the other maps and from the
> derivation receipts that name it, and that identity is a belief input (below); the
> **retraction enumeration** — found refs, resolutions, and coverage declaration
> (correction-lifecycle §6) — is the other closure input, entering as its prescribed
> projection rather than as a map identity; and the **certification-inventory
> projection** (amended 2026-08-03, normative-contract §7.6) — the epoch-wide
> by-kind `instrument-certification` enumeration as sorted refs under the
> coverage, location-free and resolution-free — is the third semantic
> projection, the comparison report's receipt-covered core.

~~The address/alias split is forced, not stylistic.~~ An earlier draft put addresses and
aliases in one map, which cannot hold: an alias deliberately names several entities, so
folding it into a map whose singularity is a load-bearing invariant would either
break the invariant or silently discard candidates.

> **Superseded 2026-08-08** (`2026-08-08-world-address-ruling.md` §4.3). There is no alias map, so
> there is no split to force. **The argument survives one level out**, and is
> stronger there: a **search term** may name several entities, so search resolves
> to addresses and only addresses resolve to locations. The ambiguity stays
> confined to the step where an attester can answer it, and the refusal that used
> to guard the alias map now guards **search** (**W9**, restated).

**Retired addresses must be in the published index, not only in the corpus.**
This is the §5.1 requirement applied to §4.3's redirect: the index is what an
actor consults when a corpus is *absent*, so an index carrying only live
addresses would report a retired address as `unknown` — "no such thing" — when
the truth is `not-present`. The redirect would then hold only while the survivor's
corpus happened to be checked out, which is exactly the conditional correctness
§4.3 exists to remove.

The address, producers, retraction and coreference maps are **derived** from the corpora — the
index publishes what the nodes say, and is never the authority for it. *(This read
"the address and alias maps … like aliases (§2.1)" until 2026-08-08; the alias map
retired with the stored alias, `2026-08-08-world-address-ruling.md` §4.3.)*

**The producer snapshot, the retraction enumeration, and the
certification-inventory projection are what make the index an epistemic
artifact rather than a packaging convenience — and they are the only parts of
it that are** (amended 2026-08-03, with the fourth map; amended again at 5b's
banking with the certification-inventory projection, normative-contract §7.6).

> **The producer snapshot** = the **producers** map plus a **coverage declaration**:
> the set of corpora the snapshot was built over, named by their **stable corpus
> identities** — which corpora were consulted, not what state they were in.
>
> That pair carries the **semantic snapshot identity**, and it alone is a **belief
> input** named by kernel §5.1's digest. The address, retraction and coreference
> maps are not in it *(nor was the alias map, which retired 2026-08-08)*.
>
> **Separately**, and **outside** the belief identity, a **derivation receipt** records
> the **exact corpus-state identities** the enumeration was built from — identities, not
> the states themselves — together with the **identity of the enumeration rule** that
> read them. It is its own record pointing at the snapshot rather than a field of it
> (below), it is checkable only if it is **structurally sound** against the snapshot it
> names — otherwise it is `malformed` and is not evidence — and then only while a corpus
> still **stands at** a state it names and that rule is still **held** (both below), and
> nothing reads it to decide belief.

Both halves name a **stable corpus identity**, which nothing in this design had defined:

> **The corpus manifest.** Every corpus in the world carries a **manifest** at a fixed
> path in its root, and the field that matters here is `corpus_id` — an **opaque
> identifier minted once**, when the corpus is created, from a random 128-bit value. It
> is **never derived** from the directory name, the path, the repository URL, a remote,
> or a project name, and **no ordinary API re-mints it**. Moving the corpus, renaming
> its directory, restoring it from a backup or mounting it elsewhere leaves it
> unchanged. That is the stable corpus identity the coverage declaration names.
>
> **Uniqueness is a world invariant**, like §4.1's `uid` rule and enforced the same way:
> two corpora in one world holding one `corpus_id` is **corruption**, refused at index
> build and not a merge question.
>
> **Copying is two different acts, and the copy cannot tell you which:**
>
> | act | meaning | `corpus_id` |
> |---|---|---|
> | **replica** | the same corpus, reachable at a second location — a mirror, a restored backup, a re-clone; at most one is live in a world | **retained** |
> | **fork** | a new corpus that starts from this one's content and will diverge | **freshly minted** |
>
> The two are byte-identical at the moment of copying, so the distinction is **authored
> at the copy**, not inferred. Failing to declare a fork is caught only when both
> corpora are live in one world, by the uniqueness invariant above.
>
> **Node content identity** is the `science.identity.v1` digest, under its own domain
> kind, of `nodes`' **normative canonical JSON projection** of the whole node
> (`STANDARD.md` §11.1): `id`, `uid`, `kind`, `title`, `body`, `metadata`, **`relations`
> normalized in document order**, **`facets`**, and `deprecated_ids`. The complete node,
> not a chosen subset.
>
> **The exact corpus-state identity is derived, not stored:** the `science.identity.v1`
> digest, under its own domain kind, of the **complete canonical manifest projection**
> together with the sorted `(uid, node content identity)` pairs of every node in the
> corpus.

**Amendment (2026-08-04) — the manifest projection joins the state identity**
(`2026-08-04-domain-extension-boundary-design.md` §7). The first member was
`corpus_id` alone. It is now the `science.identity.v1` canonical form of the
**whole closed manifest**, which subsumes `corpus_id` and brings the manifest's
`profile` block — the pinned `science_contract` and domain contract identities —
inside the digest. Hashing a chosen subset instead would recreate limitation 9
for every field the manifest is later permitted to grow. Because the member is a
*canonical projection* of the parsed manifest, formatting is inert: whitespace,
key order, and quoting style vanish at parse, and only a semantic change moves
the identity.

**Amendment (2026-08-03) — the projection must be a shipped contract, and whole-node is
deliberate.** `STANDARD.md` §11.1's projection is today implemented only as `nodes`'
*test helpers* (`python/tests/_canonical.py` and its TS twin): unimportable, unversioned,
with no stability clause in `nodes`' §12 change policy. Both identities above therefore
rest on an artifact no consumer can call. Adoption requires `nodes` to ship the
projection as public API in both languages, versioned independently of the spec version,
with a stated stability guarantee — recorded as a nodes-side obligation in `nodes`'
`2026-08-03-nodes-under-the-system-redesign-design.md` §2.1. And to foreclose a
misreading found in review: the content identity is deliberately **whole-node** — it
moves on an address correction or a `metadata` touch *(and on an alias edit, until the
stored alias retired 2026-08-08 — `2026-08-08-world-address-ruling.md` §4.3)*, because the
recorded state changed — and it is *not* the semantic identity (kernel §4.1) and not any
kind's address basis (ruled per kind in §4.2), each of which digests its own declared
subset.

**Opacity is forced by W5, one level down from where W5 is usually applied.** An
identity derived from where the corpus sits *is* a location, so a move would change
every coverage declaration naming it and, through the semantic identity, the belief
digest — the violation this section has now committed twice by other routes. An identity
derived from a human-chosen label is editable, so a rename would be an epistemic event.
A minted opaque value is the only form that survives both operations, and surviving them
is the entire reason the manifest exists rather than the corpus being named by its root.

**"Never re-minted" was the ordinary-API claim wearing an absolute's clothes**, which is
the same overreach §5.2 of sub-problem 4 corrected for lineage routes one round ago.
Raw-edit the manifest, then regenerate the snapshot and its receipt consistently, and
recomputation has nothing to object to: every state identity is internally consistent
with the corpus as it now stands, and no surviving record says the corpus was ever called
anything else.

**Amendment (2026-08-03, packaging design §4) — a surviving record now exists, and it
splits this bound in two.** The packaging design's registry keeps an append-only
admission record naming every `corpus_id` ever admitted, outside every corpus. A
**manifest-only** re-mint is therefore **detected**: the edited corpus presents an id
with no admission record and is refused at index build (packaging X7), while the
registry still names the original. What remains undetectable is the **coordinated**
act — re-mint the manifest *and* raw-**forge** an admission for the new id,
optionally also deleting the old one. The fork mimicry requires **retaining** the
old admission, since a legitimate fork keeps its parent's; deleting an admission
**alone** is a distinct undetectable registry-loss case that evades nothing — the
re-minted id stays unadmitted and the build still refuses. That residue is what
waits for §9's log. W13's negative and limitation 9 are amended in place
accordingly.

**The "an older receipt still resolves" escape does not work, and the reasoning that
produced it inverted its own mechanism.** `corpus_id` is *inside* every corpus-state
identity, so re-minting `A → B` guarantees that the edited corpus resolves **none** of
the old `A`-based states — the receipts naming them become **unresolvable**, which
§5 has just finished ruling establishes nothing. If some older replica does still resolve
them, what it validates is corpus `A`; nothing whatever ties the new `B` to it, and the
pair `A`-replica-plus-`B`-corpus is **byte-for-byte the shape of a legitimate fork**, which
is an authored act this design explicitly permits. Putting the id inside the state
identity is what makes the tamper invisible rather than what catches it: the edit does not
break a check, it moves the corpus outside the reach of every check that named it. This is
G4/G8/S3's undetectable-history limit — softened, since the 2026-08-03 amendment above,
by exactly one partial detection: the registry catches the manifest-only case, and W13
asserts both that detection and the coordinated residue that survives it.

**Replica and fork have to be named because "re-clone keeps the id" and "a copy needs a
fresh one" both sounded like rules and contradicted each other.** They are the two ends
of one authored decision, and the decision is not computable from the bytes — which puts
it in the same class as §4.3's merge assertion and sub-problem 4's code-lineage claim:
attributed, recorded, and checked only by the invariant that catches the failure after
the fact.

**A project identity will not serve, and the two are not interchangeable.** §6 makes
storage one field of `science.yaml`: several projects may contribute to one corpus, and
a project may change which corpus it writes to. So a project identity is neither
one-to-one with a corpus nor stable under the operations a corpus identity must survive
— and using it would put a coordination fact inside a belief input, which §3 separates
world content from coordination content precisely to prevent.

**The projection is the whole node, and the citation this rule first carried was wrong.**
An earlier phrasing pointed at substrate §4.2 for "the per-node content identity the
stale-hash check already requires", and §4.2 supplies no such thing: it governs
**proposition semantic identity**, which is deliberately scoped to the semantic fields of
one kind. A corpus-state identity built on that would be blind to exactly the change this
mechanism exists to catch — **a run's `produces` relation is not part of any node's
identity basis** (§4.2 here), so adding, removing or retargeting one moves the producers
map while every world address, and every semantic identity, stands still. Digesting the
canonical projection is what makes the state identity see it, and it is why the
projection must be the **complete** node rather than an identity-bearing subset:
the producers map is derived from relations, so relations have to be inside the state
the receipt names.

`nodes` §11.1 is also the right source rather than a Science-local canonicalization: it
is the projection **cross-language node equality is already defined over**, with
conformance fixtures behind it, so a Python and a TypeScript implementation cannot
disagree about what a corpus state is. Field order and normalization come from the
standard; Science adds only the domain-separated digest.

**Document order is inside the identity, and that is a deliberate false positive.**
Reordering a node's relations changes nothing semantically and still moves the state
identity, so a receipt naming the old state stops matching. That costs an audit its
evidence (below) and never costs belief, because the state identity is not a belief
input — the alternative, sorting relations before digesting, would silently accept a
projection `nodes` itself does not treat as equal, and cross-language equality is worth
more here than tolerance of a cosmetic edit.

**The state identity is over node content, not over the filesystem and not over git.** A
git commit is unavailable where a corpus is not a repository, and wrong where it is
available: it moves on untracked files and misses uncommitted ones, which is the same
defect sub-problem 4 §4.2's `code_identity` argument makes about capturing what ran. A
tree hash over the directory would fold in file names, ordering and non-node files, so
reformatting a file or renaming it inside the corpus would read as a state change the
producers map cannot see. Digesting `(uid, content identity)` pairs makes "the state the
enumeration was built from" mean exactly the state the enumeration **read**.

> **The derivation receipt is its own record.** It is an **immutable record directed at
> the semantic snapshot**, carrying that snapshot's identity; for each covered corpus,
> the exact corpus-state identity the enumeration was built from; and the
> **`producer_snapshot_rule_identity`** — the versioned identity of the enumeration rule
> that produced the map. Its own identity is
> `(snapshot identity, sorted (corpus_id, corpus-state identity) pairs, rule identity)`.
>
> The rule identity is bound the way sub-problem 4 §3.1b binds an `interpretation_rule`:
> it names a **held implementation or a registry entry with fixtures**, and an
> implementation that fails those fixtures **is not that rule**. Validation rebuilds
> using the rule the receipt names — **not** whatever this installation would run today.
> A reference that is **not a fixture-bound rule identity at all** — a bare version string
> — is a **structural** defect and makes the receipt `malformed` below, never
> `unresolvable`: nothing could arrive that would let it resolve.
>
> **A held implementation does not change in place.** The identity is over its content,
> so new bytes are a **different rule** with a different identity; installing one leaves
> the old rule untouched and every receipt naming it still validating. A receipt goes
> **unresolvable** when its rule is **no longer held here** — the same thing an absent
> corpus state does, and a different event from an upgrade.
>
> **The rule identity is in the receipt and not in the snapshot.** The snapshot's
> semantic identity is over *what was enumerated*, so two rules that produce the same map
> over the same coverage are the same belief input — as they should be, since belief
> reads the enumeration and not the program that wrote it.
>
> **Several receipts may name one snapshot**, and that is the ordinary case rather than
> an anomaly. Belief names **none** of them.

**Without the rule identity, a receipt is refutable by a software upgrade.** Validation
compares a stored map against one rebuilt *now*, so with no rule pinned, if the
enumeration's implementation or profile changes — a widened notion of what counts as a producing edge, a different
treatment of retired addresses — the same stored, previously validating receipt starts
**refuting** its snapshot, by neither of the two routes §5 names and with nothing in the
corpus having changed. Worse, two installations running different versions **disagree at
the same instant** about whether one record is a false derivation, which makes the
outcome a fact about the reader rather than about the record. Pinning the rule inside the
receipt's own identity turns an upgrade into what it actually is: a **new derivation**,
which produces a **new receipt** beside the old one, and a new snapshot only if the map
or coverage really did change. Nothing retroactively refutes.

**Upgrading and un-holding are different events, and an earlier test conflated them.**
Because the rule is content-addressed, installing a newer enumeration alongside the old
one changes nothing about existing receipts — their rule is still held, so they still
validate, and the world now simply holds two rules. What makes a receipt unresolvable is
**ceasing to hold** the one it names, which is a deliberate act of dropping an
implementation, not a consequence of adopting a better one. Reading "the rule changed" as
"the old rule is gone" is the same category error as reading a corpus's *new* state as
the loss of its old one — in both cases the receipt's evidence survives exactly as long
as the thing it names is still around.

**A version string alone would not have done it**, which is why the binding runs through
fixtures. "Rule `v3`" that two implementations interpret differently reproduces the
disagreement one level down, and sub-problem 4 already ruled on this shape for
interpretation rules: an implementation failing the rule's fixtures **is not that rule**.
This is the fifth consumer of that discipline and the first outside sub-problem 4.

**Logical separation was not enough, and the previous revision had only that.** Saying
the receipt "sits alongside" the snapshot leaves it a **field** of one artifact — and
W5's own case then breaks the artifact. Move a dataset between two covered corpora: the
producers map, the covered-corpus set and therefore the semantic identity are all
unchanged, while both corpus states move. Re-derive, and there are two receipts for one
unchanged snapshot identity, which inside a single artifact means either two byte-images
at one identity or a **mutable** receipt sitting in a record whose immutability the whole
completeness argument rests on. Two records with two identities makes the ordinary case
ordinary, and it is the shape the split should have taken when the identities were split.

**Splitting the identity is required, not tidiness — and it took two cuts.** An earlier
revision made "the index's identity — maps and coverage together" the belief input,
which contradicts W5 directly: moving an entity between corpora changes the address map,
and W5 requires a move to leave `belief_input_digest` **unchanged**, because location is
not evidence. *(Editing an alias would have done the same through the alias map, until
both retired 2026-08-08 — `2026-08-08-world-address-ruling.md` §4.3. The argument never needed the
second example.)* A single index
identity makes every rename and every file move an epistemic event, which is the
opposite of what §4.4 and §5.1 spent their arguments establishing.

**Removing the address map did not finish the job**, because the fix for completeness
put location straight back in by another door. A move rewrites both the source and
destination corpora, so **both corpus-state identities change** — and with exact states
inside the coverage declaration, the snapshot identity moves on a move that leaves the
producers map untouched. The same W5 violation, arrived at from the audit requirement
instead of from the packaging one. That is the second time in three rounds that a
completeness mechanism has smuggled a location fact into an epistemic identity, and the
tell is the same both times: **the thing you need for recomputation is not the thing
belief reads.**

So the cut runs between them. Belief reads *what was enumerated* and *over which
corpora* — both stable under a move. Audit needs *which bytes it was built from* —
which is not stable under a move, and does not belong in a digest that must be. **Two
records with two identities**, and only one of them is a belief input; an earlier
phrasing here said "two records, one artifact", which is the version the receipt's own
multiplicity then broke.

**And a snapshot that is merely hashed is not evidence that it is complete.** Take a
valid snapshot, delete the entry for a divergent `R2`, keep the coverage declaration
untouched, and hash the result: it is internally consistent, it certifies independence,
and its identity faithfully names the fabricated answer. Hashing detects **change**, and
the property belief needs here is **completeness** — the two are not the same claim, and
the earlier text used one word for both.

> **Rule.** The producer snapshot is **derived**, and carries the derivation discipline
> sub-problem 4 §7.3c defines for verification: it is **recomputed and compared** at
> **explicit import** and under **audit**, and a mismatch refuses the import before any
> write. It is **never validated on read** — that would make belief depend on the
> checkout, which R5 forbids — so a snapshot written straight into place stands until
> an audit runs, exactly as a raw-written verification does.
>
> **A receipt names its inputs; it holds none of them.** Define the predicate once, and
> refer to *this* everywhere the word appears:
>
> ```text
> resolvable(receipt, availability) :=
>       the receipt's producer_snapshot_rule_identity resolves to a rule held here
>   ∧   ∀ (corpus_id, state_id) in the receipt:
>           the corpus available here under corpus_id recomputes to state_id
> ```
>
> The quantifier is **per pair**: each covered corpus must itself stand at the state the
> receipt records **for that `corpus_id`**. One corpus cannot satisfy another's entry, and
> a receipt over five corpora needs all five.
>
> **Well-formedness comes first, and it is a different outcome.** Before availability is
> consulted at all:
>
> ```text
> well_formed(receipt, snapshot) :=
>       keys(receipt.states) == snapshot.coverage      (as sets, no duplicates)
>   ∧   receipt.snapshot_identity == snapshot's identity
>   ∧   ∀ (corpus_id, value) in receipt.states:
>           value is a syntactically valid exact corpus-state identity
>   ∧   receipt.producer_snapshot_rule_identity is a syntactically valid
>           fixture-bound rule identity
> ```
>
> **`well_formed` asks whether these are identities at all; `resolvable` asks whether
> they are held here.** That cut is what keeps a structural defect from hiding behind a
> transient one. A **bare version string** in place of a rule identity is not a rule that
> happens to be unavailable — it names nothing that could ever be held, so it is
> **malformed**, and reporting it `unresolvable` would have invited its owner to install
> the missing rule. Likewise a state value naming a **corpus** rather than an exact
> corpus-state identity: no arrival makes it checkable. Neither judgement consults
> availability, and both are decidable with no corpus present.
>
> A receipt with a **missing**, **extra** or **duplicate** corpus entry, a wrong snapshot
> identity, a state value that is not a state identity, or a rule reference that is not a
> rule identity is **malformed**. It is **unrecomputable in principle** — alongside the
> no-receipt case — and it is never `unresolvable`. `resolvable` is evaluated only for a
> well-formed receipt.
>
> Validation of a resolvable receipt rebuilds the producers map from **those corpora,
> under that rule**, and compares it to the snapshot's map byte for byte. An
> **unresolvable** receipt establishes **nothing** — not completeness, and not its
> absence — whichever conjunct failed.
>
> A snapshot **no receipt names**, and one whose receipt is **not `well_formed`**, are
> both **refused at import**. An unresolvable receipt is a different outcome: import
> **proceeds**, an **import finding** records that the derivation was not checked,
> **nothing is written onto either record**, and an audit checks it if the receipt
> becomes `resolvable` — by its states arriving, its rule being installed, or both.

**A receipt is a hash, not an archive, and the previous phrasing traded on the
difference.** "Recomputation replays against exact corpus states" reads as though the
states were held; nothing in this design holds them. Once a covered corpus moves from
`C0` to `C1`, keeping `hash(C0)` does not let anyone rebuild the map as it stood at `C0`
— the bytes are gone, and a digest of absent bytes is a name, not a copy. So the contract
narrows to what the mechanism can do: **a receipt is checkable exactly while it is
`resolvable`** — every covered corpus standing at *its own* recorded state, and the named
rule still held here. That makes completeness evidence **time-bounded** rather than permanent, and makes
re-deriving a snapshot as its corpora change the way you keep the evidence alive
(limitation 10). The alternative — binding
each state to a held, hash-verifying corpus archive — buys permanence at the price of a
full corpus copy per receipt, and this design does not ask for it.

**`resolvable` alone would have validated a snapshot against a corpus set the forger
chose.** The predicate quantifies over the pairs *in the receipt*, so for a snapshot
declaring coverage `{A, B}`, a receipt naming only `A` resolves whenever `A` is present,
rebuilds from `A` alone, and reproduces a producers map that quietly omitted every
producer living in `B` — a completeness check passing on the strength of a set the record
under scrutiny got to pick. The coverage declaration is the snapshot's claim about what
was consulted; the receipt has to be a claim about **that same set**, or it is checking a
different question. Hence `well_formed` runs first and is a **refusal**: a receipt that
does not cover the coverage is not weak evidence, it is a malformed record.

This also keeps the two failure kinds from blurring, which the previous revision had
begun to do. **Malformed** is a property of the record — permanent, visible without any
corpus, refusable at import. **Unresolvable** is a property of *here and now* — it says
nothing about the record and everything about the checkout. Letting a coverage mismatch
report as `unresolvable` would have filed a forgery under "come back when you have more
corpora."

**But "refused at import" is not a place a state can live, and the previous revision put
malformedness only there.** §11.11's raw-write case is explicit that the filesystem is
reachable past every boundary — it is the reason `contradicted` had to be given a
population two revisions ago — so a malformed receipt *will* be found sitting in a corpus,
and the evaluator that finds it returned only `validated` / `refuted` / `unresolvable`
while the rule above said malformed is never `unresolvable`. That is not a lenient
outcome, it is **no outcome**: an audit meeting a raw-written malformed receipt had
nothing defined to return. So malformedness is a **structural result of the evaluator**,
computed before availability is consulted at all, and the import refusal is one **caller's
reaction** to it rather than the whole of its existence. The pattern is the one the
`contradicted` round already established and this revision re-learned one member down:
**a condition enforced only at a boundary needs a state for the records that got in
around it.**

Refusal and unresolvability have to stay separate outcomes because separability (§5.1)
and recomputation pull in opposite directions: the index must be consumable **without**
the corpora it names, while checking a receipt requires exactly those corpora, at exactly
those states. The cut is §5.1's own distinction carried into derivation — a record that
**cannot be checked here** is not a record that **cannot be checked** — and it is
sub-problem 4 §7.3c's existing rule rather than a new one: an import whose inputs do not
resolve proceeds and emits a finding, and writes no validation state onto the record.

> **Validation is per `(snapshot, receipt)` pair**, never global to a snapshot, and it is
> **evaluated now, never stored**: **malformed** (not `well_formed` — evaluated first,
> without consulting availability), **validated** (`well_formed` and `resolvable`, and the
> rebuild reproduces the map), **refuted** (`well_formed` and `resolvable`, and it does
> not), **unresolvable** (`well_formed` but not `resolvable` — whichever conjunct failed, a
> state or the rule).
>
> A receipt that is **refuted at import** is **refused before any write** — it is a false
> record about a derivation, the same case as §7.3c's fabricated verification.
>
> **A stored receipt can still evaluate to `refuted` later**, and by exactly two routes:
> it was **unresolvable when imported** and what it was missing — **the corpus states,
> the named rule, or both** — became available afterwards; or it was **raw-written** past
> the import boundary. Import refuses what it can refute *at the time it runs*; it makes
> no claim about what a stored receipt will evaluate to next year.
>
> **One evaluator, three callers.** `evaluate(snapshot, receipt)` runs `well_formed`
> **first** and returns `malformed` without consulting anything; otherwise it is
> **read-only**, not pure: it consults the **availability context** — which corpora are
> here, at which states, and which rules are held — then rebuilds, compares, and returns
> `validated` / `refuted` / `unresolvable`, **writing nothing**. Only the structural
> outcome is a function of `(snapshot, receipt)` alone; the other three are a function of
> `(snapshot, receipt, availability)`, so **determinism is guaranteed within one
> availability context** and across nothing else. Its callers are:
>
> | caller | effect |
> |---|---|
> | **explicit import** | **effectful boundary** — a `malformed` or `refuted` result refuses the import before any write |
> | **audit** | **effectful boundary** — evaluates stored pairs on demand, **reports every `malformed` pair as its own finding**, reports the snapshot state below, and is where a correction is published |
> | **diagnostic query** | **read-only** — reports the same result and writes nothing |
>
> There are therefore **two effectful validation boundaries and one diagnostic caller**,
> over one evaluator. Nothing else evaluates: **mounting a corpus makes an evaluation
> possible and does not perform one**, no result is stored on any record, and belief
> consults none of them.
>
> A snapshot's state is what a caller **computes from its receipts as they evaluate at
> that moment**. **The reduction runs over its `well_formed` receipts only** — a
> `malformed` receipt is not weak evidence about the snapshot, it is not evidence, and it
> is reported on its own rather than folded into a snapshot state. Over that domain the
> three cases are total:
>
> | state | condition |
> |---|---|
> | **checked** | at least one well-formed receipt is **`resolvable`** now and its rebuild reproduces the map |
> | **contradicted** | **no** well-formed receipt is `resolvable`-and-reproducing, and at least one is **`resolvable`** now and does **not** reproduce it |
> | **unchecked** | **no** well-formed receipt is `resolvable` now — because none is well-formed, or for want of a state, of the rule, or of both |
>
> A refuted or unresolvable receipt therefore cannot condemn a snapshot that another
> receipt validates, and a snapshot whose corpora have all moved on becomes **unchecked**
> — never contradicted, and never retroactively invalidated.
>
> A snapshot whose receipts are **all malformed** therefore reduces to **unchecked**,
> exactly as one with no receipt at all does — which is the right answer, since a
> malformed receipt establishes neither completeness nor its absence — but the audit
> **additionally emits a malformed finding per pair**, because the two roads to
> `unchecked` are not the same problem. Unchecked-for-want-of-a-corpus is a property of
> this checkout and clears when the corpus arrives; unchecked-because-malformed is a
> defect in a stored record that no arrival will ever clear. Collapsing them would file a
> permanent defect under "come back later" a second time, one level up.

**"Becomes refuted" needed an operation to become it in.** The previous revision said a
receipt evaluates to `refuted` once its corpora arrive, while the rule two paragraphs up
says validation runs at import and under audit and **never on read** — and a mount is
neither. Written that way, the state changed by itself, which is exactly the read-time
validation R5 forbids wearing a passive verb. The sequence is **mount, then audit**: the
mount changes what an audit *would* find, and the audit is what finds it.

**Calling the evaluator "pure" was wrong, and the mistake mattered because the whole
design turns on it.** With identical arguments it returns `unresolvable` before a corpus
or a rule arrives and `validated` or `refuted` after — availability was a hidden input,
and a hidden input that varies by checkout is precisely what R5 is about. Naming it makes
the guarantee statable: **read-only** (it writes nothing, which is what "never validated
on read" needs) and **deterministic within one availability context** (which is what "two
installations agree" needs, and all it can mean). The earlier wording claimed a stronger
property that the mount-then-audit transition, four paragraphs up, falsifies by design.

**And "exactly two operations" was the wrong count, stated one paragraph before a third
was introduced.** The diagnostic query evaluates receipts too; calling it something else
did not make it not one. What is actually two is the number of **effectful** boundaries —
the places an evaluation can refuse a write or publish a correction — and the way to say
that without miscounting is to name the **evaluator** once and list its callers, which is
what the rule above now does. One shared evaluator with three callers is also the honest
implementation shape: three separate validation paths would drift, and drift here means
two operations disagreeing about whether a record is false — a disagreement no
availability context could excuse.

The diagnostic caller is not a hole in "never validated on read". It is an explicit act,
it writes nothing, and no belief computation consults it. What is forbidden is validation
happening **because a corpus was loaded**, since that would make a record's standing
depend on an actor's checkout.

**The first route has two halves because unresolvability does**, and an earlier phrasing
named only the corpora. Once the rule identity joined the receipt, "unresolvable" covered
a second missing input — so a receipt can enter unresolvable for want of its **rule**,
sit there while every corpus it names is present, and evaluate to `refuted` the moment
that rule is installed and an audit runs. The route is the same shape either way: what
was missing arrives. Adding a member to a record widened a state defined over that
record, and the lifecycle written before the member existed did not notice.

**Naming those two routes is what makes `contradicted` reachable at all.** If import
refused every refuted receipt *and* refusal were the only filter, no stored receipt could
ever refute anything and the state would be dead on arrival — a valid-state rule that
excludes its own population, the defect the `conflict` variant was given a lifecycle to
avoid. Import is a **boundary check at a moment**, not a standing invariant over the
corpus, and the same is true of §7.3c's verification import; saying so is what keeps the
three states describing something that can happen.

**Both quantifiers were wrong in the previous revision, in opposite directions.**
"A snapshot keeps whatever validation it had" is unstatable, because **no validation
state is stored anywhere**: validation is a computation over receipts and the present
availability context — corpora *and* held rules, per `resolvable` — so there is no past
result to keep. And "every resolvable receipt is refuted" is
**vacuously true when none resolve**, which would have marked a snapshot *contradicted* on
the strength of evidence the paragraph above says establishes nothing. The table replaces
both: `checked` and `contradicted` each require something to hold **now**, and the vacuous
case falls to `unchecked` where it belongs.

Making validation universal instead would let one stale or forged receipt condemn a
snapshot with a perfectly good one; making it global to the snapshot would attach a
per-derivation result to the wrong record entirely, since which states a rebuild used is a
fact about the receipt.

> **The snapshot is a required argument to belief computation.** Its semantic identity is
> a kernel §5.1 digest member, so a computation that did not name one has no digest to
> compute; there is no default, no implicit "latest", and no "whichever is mounted".
> **This is the whole of the mechanism** — belief is a computed view (kernel §6), and a
> view's arguments are supplied at the call.
>
> **An audit that refutes a snapshot derives the correct one from the available corpora
> and publishes it with its own receipt.** A **later computation names the corrected
> snapshot**, and its digest differs because a different argument was passed. The audit
> **mutates nothing**: it writes a new snapshot and a new receipt, and changes no belief
> by itself.

**"Selection moves to it" named a mover that does not exist**, and the previous revision
wrote it as though some stored pointer were being updated. Nothing in this design holds
such a pointer, and inventing one would have created a mutable belief-input selector —
the same defect as a mutable receipt, one level up. G3 already supplies everything
needed: pass the snapshot identity, get that snapshot's belief.

**If a project wants a standing choice, that belongs in the view, not here.** §6 makes a
project a **view plus coordination**, which is exactly the layer where "the snapshot this
project computes against" is a durable, authored, renameable setting with a lifecycle —
and keeping it there preserves §3's separation, since a standing preference is a
coordination fact and the identity it names is a world one. This design does not specify
that setting; it specifies that belief takes the identity as an argument, so any such
setting is a convenience over an explicit call rather than a hidden input to it.

**What none of this supplies is a retraction, and the gap is the same one three times.**
The refuted snapshot is still a well-formed record at its own identity; nothing here
retires it, so a computation that names it still computes the false value. That is
sub-problem 4 §11.13's missing retraction reached from a third direction — after the
divergent producer and the conflicted lineage basis — and it goes to sub-problem 5 with
them. Until it exists, the honest claim about receipts is bounded: a validated receipt
makes a snapshot's completeness **checkable now**, and a refutation makes a **correction
publishable**; neither makes the wrong answer unusable.

That makes the producer snapshot the **fourth** consumer of the same discipline, beside
verification derivation, the assessment facet and the result manifest. The pattern is
now explicit enough to state as a rule for sub-problem 5: **a derived belief input needs
a derivation boundary, or it is an authored one with a hash on it.**

Sub-problem 4 §5.2 certifies a dataset's lineage only if **no producing run
disagrees** with its stamped basis, which makes "every run that produces `D`" a
question belief must answer. It is a **reverse** adjacency question, and the index's
forward maps answer *where does this address live*, never *what points at it*. Producers of `D` live in corpora that need not contain `D` and need not be
checked out, so without publication the answer silently shrinks to whatever is
locally present — a divergent producer in an absent corpus simply is not seen, the
dataset reads undiverged, and independence is certified from an enumeration nobody
bounded. **Belief would then depend on what is checked out**, which is exactly what
R5 forbids and what §5.1 introduced `not-present` to prevent for forward references.

The coverage declaration is what converts an unbounded question into an answerable
one. Certification is **relative to declared coverage**: a producer inside coverage
whose corpus is absent resolves to `not-present` and is a computability state, not a
silent omission; a producer in a corpus **outside** coverage is outside the guarantee,
and sub-problem 4 §11.15 records that rather than pretending the enumeration is
absolute. Two different coverages are two different belief inputs, which is why the
identity rather than the content enters the digest — and why that identity is the
snapshot's, not the index's.

This settles what §5.1 below leaves as a packaging question. An index that must be
publishable so `not-present` is representable is a convenience; an index whose
identity enters `belief_input_digest` is part of the epistemic record, and its
completeness contract is load-bearing. It also gives the §13 "publishable
belief-input snapshot" question a concrete first member.

**It is not a thin map, and the first draft's claim that it "adds nothing the
corpus indexes already provide" is false.** `nodes` indexes are corpus-local in
exactly the way that matters here: a relation from a node in corpus A to a node in
corpus B is, to corpus A, a **dangling** target — `STANDARD.md` §7 says inbound /
outbound / dangling are relations-only and uid-based within the corpus. Under one
world that relation is not dangling; it is ordinary. So the world layer must
supply:

| capability | why the corpus cannot |
|---|---|
| world resolver | address → corpus, before any corpus can be asked |
| world adjacency / reverse index | inbound edges to a node live in corpora that do not contain it |
| world-aware dangling check | corpus-local `dangling()` reports every cross-corpus edge as broken |
| world traversal | relation and basis closures cross corpora; a corpus-local walk truncates at the corpus edge |

That last row is a live cross-document consequence, not a note. Substrate §5
certifies independence by walking dataset lineage and emitting `lineage-incomplete`
when it meets an unresolvable reference. Run corpus-locally against a
world whose lineage crosses corpora, it would emit `lineage-incomplete` for every
cross-corpus ancestor — refusing to certify independence that is actually
demonstrable. The failure is *conservative*, so it costs belief rather than
inventing it, but it is wrong, and it means **lineage closure must run at the
world layer**, over the composed adjacency, not against a single corpus.

**That consequence has since been paid in full, and it landed on the substrate.**
Substrate §3 specified `transitive_outbound` / `transitive_inbound` in `nodes` to
serve two callers — lineage closure and `supersedes` chains — and this row says both
are world-crossing, so neither could use a corpus-local primitive end to end. Sub-
problem 4 §5.2 then made lineage a **facet** rather than a relation, which the
primitive's signature cannot address at all. The operations are **withdrawn from
`nodes`** and their contract is owned here: the world layer walks both closures over
`nodes`' one-hop `outbound()` / `inbound()` plus this resolver, under substrate §3's
semantics unchanged. This table stopped being a list of capabilities the world layer
adds and became the argument for where the traversal lives.

`graph/composite.py` is therefore **replaced, not deleted**: its function —
assembling a queryable whole from parts — is exactly what the world layer does.
What disappears is its premise, that the parts are separate worlds needing named
graphs to keep them apart.

**Three conflicts, and only one of them is a collision.** The measured §1.1
condition — two corpora claiming one `id` for different things — is not
expressible once the stored address is basis-derived (§2.1), so the old
`id-collision` finding has no referent. What replaces it are three distinct
states with three distinct handlings:

| conflict | meaning | handling |
|---|---|---|
| **duplicate location** | **one canonical address, two records** — one corpus or two, `uid`s shared or distinct *(2026-08-09: read "one identity, two corpora", which the `uid` reading made too narrow)* | the §4.3 migration state: reported, resolved by ~~an authored merge~~ **`consolidate`** *(2026-08-08 — merge retired; `consolidate` repairs storage and asserts nothing about identity, so no address retires and no inbound reference is rewritten)*, refused at the write boundary thereafter |
| **ambiguous ~~alias~~ search term** | one **search term**, several identities | ordinary and expected; refused *at authoring* with candidates named, never a finding against the corpus. *(2026-08-08: the term resolves against the **pinned authority snapshot**, not against stored aliases, so the ambiguity is reproducible across installations holding that snapshot rather than an artifact of accumulated authoring.)* |
| **address conflict** | one derived address, disagreeing bases | a digest or corruption failure, not a curation question — the basis derivation is deterministic, so this cannot arise from ordinary authoring |

**None is resolved by precedence.** No first-wins, no project priority, no
recency: a precedence rule is a silent answer to a question that has more than one
right answer depending on facts the rule cannot see. That holds for all three,
and it is the property W8 tests.

The five measured collisions of §1.1 are, under this model, **five ambiguous
search terms** *("aliases" until 2026-08-08, `2026-08-08-world-address-ruling.md` §4.3)* — the
least severe of the three. Three resolve to distinct world
entities that happen to share a citekey, which is ordinary; two are notes with no
world identity at all. The measurement motivated the design and none of it
survives as a corpus-level defect, which is the intended outcome.

### 5.1 Availability is not existence

`t068` asks what happens when the target project is not locally available. Under
one world the question sharpens: a reference is not foreign, so failing to resolve
it is not a category, it is a **state**.

| state | meaning | applies to |
|---|---|---|
| `resolved` | the address is in the world index and its corpus is present | address, alias |
| `not-present` | the address is in the world index; its corpus is not in this checkout | address, alias |
| `unknown` | the address is in neither map of the world index | address, alias |
| `ambiguous` | the **alias** matches more than one world entity | alias only |

`not-present` and `unknown` are different findings and must not collapse into one
"broken reference." Collapsing them is the error `fb-2026-07-27-010` records
elsewhere in the toolkit — reading a failure to look as a finding of absence.

`ambiguous` arises only on the handle path (§2.1) and is a **refusal listing the
candidates**, never a selection. A stored world address cannot reach this state,
which is the point of having two forms: the ambiguity is caught where a human can
still answer it, rather than resolved silently where nobody is looking.

> **Amended 2026-08-08 — three resolution states, not four**
> (`2026-08-08-world-address-ruling.md` §4.3). With the stored alias retired, the
> `applies to` column reads **address** on every surviving row, and `ambiguous`
> leaves the table: it was the alias-only row, and there is no alias.
>
> The refusal it named **survives, relocated**. A **search term** matching more
> than one identifier in the pinned authority snapshot is still a refusal listing
> candidates, never a selection — but it is a **search-time** outcome, not a
> reference-resolution state, because a search term is never stored and so never
> resolved. W9 is restated on that basis.
>
> The paragraph above keeps its force under the new spelling: the ambiguity is
> still caught where it can be answered rather than resolved silently. What
> changes is that it is now a reproducible property of a pinned snapshot rather
> than of what previous authors happened to type.

This requires the world index to be **separable from the content it indexes**: it
must be publishable and consumable without the corpora it names, or `not-present`
is unrepresentable. That is a genuine new artifact, and it is the one piece of
this design with no current analogue.

**And separability is now the smaller half of why it must be published.** §5's third
map carries a **belief input** — kernel §5.1 digests the producer snapshot's **semantic**
identity, covered-corpus identities included, while the address map, the retraction
map, the coreference map and the derivation receipt all stay out of it so that moving
a file remains epistemically silent (W5) *(the alias map was in this list until it
retired 2026-08-08; the coreference map joined it — outside the digest — the same
day, world address ruling §5.5)*. An unpublished snapshot does not merely cost a resolution state; it leaves
an enumeration belief depends on unbounded and unrecorded. The artifact's contract
therefore includes **what it covers** (in the identity) and **which corpus states it was
built from, under which enumeration rule** (in a separate receipt record, of which one
snapshot may have several), not only what it maps.

The receipt is also why publication and availability are different questions here. A
consumer without the corpora can hold the snapshot, resolve `not-present`, and compute
belief from the semantic identity; what it cannot do is *check* the derivation, and §5's
import rule says so in as many words rather than leaving the two requirements to collide
in an implementation.

## 6. What a project becomes

`science.yaml` survives, with its contents re-typed rather than replaced:

- **the view** — the world selection this project works on;
- **coordination** — its tasks and decisions, project-scoped by §3;
- **storage** — which corpus this project contributes to the world index;
- **peers** — retired. Peers exist to name *other projects whose entities I might
  reference*; under one world there is no such category. What survives is
  *availability*: which corpora this checkout can see, which is a property of the
  checkout, not a declared relationship between projects.

### 6.1 Coordination addressing — the other half of `t068`

Tasks and decisions stay project-scoped (§3), so they need a scope in their
address. Dropping the qualified form entirely would leave `t018` and `t043` — the
tasks `t068` exists to unblock — with no way to name a blocker in another project.

> **Rule.** A coordination address is **(project identity, local id)**. Local ids
> stay project-unique only; two projects may both hold `t068` and they are
> different tasks. The world address form (§2.1) is for world entities and is
> never used for coordination; the qualified form is for coordination and is
> never used for world entities.

**Projects therefore need durable identity of their own**, and by the same
argument as §4.1: a project id derived from its *name* would break every
coordination reference when a project is renamed — a nominal change silently
retargeting bindings, which is the defect this design exists to remove. A project
carries an opaque durable identity; its name is an alias.

Two address forms, and which one applies is determined by the kind, not by the
author. That is the answer to `t068`: not one grammar, but a ruling about which
records have world identity and which have scope — with the grammar following
from it.

`addressing.py`'s `<project>:<artifact>` grammar is therefore **not** deleted
outright (§9): its entity use has no referent under one world, and its
coordination use survives, corrected to bind project identity rather than the
project name. *Discharged 2026-08-31 by supersession rather than correction:
no such module exists in this repository — the grammar survived only in
design prose — and the coordination-and-view-kinds design
(`2026-08-31-coordination-and-view-kinds-design.md`)
defines the `coord:` address form fresh, adding rows W17 and W18 below.*

**A project is not a permission boundary in this design.** Anything a project can
see, it can reference. Access control over parts of the world is not addressed
here and is not implied by the view (§8).

## 7. Guarantees, and how each is tested

Certified by mutation, per the kernel's §5 discipline.

| # | Guarantee | Mutation test |
|---|---|---|
| **W1** | Distinct bases never become one node | Load all three colliding `paper:` pairs (`Chen2023`, `Liu2020`, `Shi2025`); assert **six nodes and six distinct world addresses — two per pair** — and that no handle lookup silently picks one |
| **W2** | A shared basis establishes coreference mechanically | Two records of one source carrying the same normalized DOI; assert one identity, no curator assertion required |
| **W3** | Creating a world entity without its basis is refused (dataset arm narrowed 2026-08-09, admission ramp §6.4) | Attempt to create a `source` with **no accepted external identifier** (no DOI, PMID, ISBN or accession), and a `dataset` with **no content identity** — the §1.1 DepMap case, a programme named with no release pinned, which says which *work* but never which bytes; assert both are **refused** — not silently coerced to notes. Author the curation note as a separate explicit act, then supply the basis and assert the world entity is minted from it. **Negative:** assert no title-and-year fallback exists to be reached. **Negative — identity is not holding, and this is the narrowing:** create a `dataset` whose content identity is recorded and whose bytes are **not held anywhere**; assert it is **minted**, not refused — it is `declared` under the admission ramp, addressable and referenceable, and `G2b` is what refuses it as an assessment input. An implementation refusing it here re-admits the fusion the arm was narrowed to remove, and makes the ramp's state unreachable |
| **W4** | A merge is authored, and never derives content by precedence | Merge two records whose bases disagree; assert refusal. Merge with a curator assertion; assert the rationale is stored, the survivor's **outgoing** relations are the union of both, **every retired address resolves to the survivor**, every reachable inbound reference is rewritten, and **no** field-level precedence rule was applied. **Redirect set:** give the removed node a pre-existing deprecated address, merge, and assert that **both pre-merge live addresses and every inherited deprecated address** resolve to the survivor, while the survivor's own live address is **not** in its `deprecated_ids`. **`uid`:** assert the survivor keeps one input `uid` and that **no third `uid` was minted**. **Absent referrer:** hold one referrer's corpus out of the checkout, merge, and assert its untouched old address still resolves — the redirect, not the rewrite, is what carries it. **Absent survivor:** publish the index, remove the *survivor's* corpus, and assert a retired address reports `not-present`, never `unknown`. **Derived fields are not selectable:** merge two dataset records at one content address carrying **different lineage bases** (sub-problem 4 §5.2); assert **both** survive, that no field-selection path offers a choice between them, that the dataset becomes `lineage-divergent` and independence over it `not-certified`, and that the conflict **still stands after deleting either producing run** — pinning that field-by-field authorship governs authored content only, and that this is the one durable form of a divergence whose other form (§11.14 there) is not. **Retractions, both arms (added 2026-08-05 — formal model ρA10):** attempt a curator-asserted merge of two **distinct-basis** retractions and assert **refusal** — merge redirects inbound references, so this is the one sanctioned act that can close a cycle in the retraction graph; then consolidate two **equal-basis** replicas of one retraction held in two corpora **while a counter-retraction `R` already targets it**, and assert the merge **succeeds**, that the retraction's content identity is **unchanged**, and that `R` is **not rewritten and not re-minted** — §5's `duplicate location` state has no other resolution **Amended 2026-08-08 — structural merge is retired** (`2026-08-08-world-address-ruling.md` §5). The row's premise stands and its mechanism is withdrawn; the arms re-home rather than disappear. Assert **no operation retires an address on coreference grounds**. The **equal-basis consolidation** arm and the **lineage-divergence** arm (both survive, no field-selection path, `lineage-divergent`, conflict standing after either producing run is deleted) move to **W16**, whose union rule now carries them; the **distinct-basis retraction refusal** moves to **W15**'s cycle arm, where it becomes an assertion that no cycle is constructible rather than that one is refused. Every remaining arm — redirect sets, absent referrer, absent survivor, `uid` non-minting — described merge and retires with it |
| **W5** | Moving an entity between corpora changes only its location | Move a `source` from one corpus to another; assert its **`uid` unchanged**, its **canonical address unchanged**, no entry added to `deprecated_ids`, every inbound reference unchanged, and `belief_input_digest` unchanged. Then move a **dataset** that appears in the producers map, and assert `belief_input_digest` is **still** unchanged even though the address map and **both corpus-state identities** moved, so that re-deriving now mints a **new receipt** naming the same snapshot — this row is what two successive revisions of §5's snapshot identity violated, once through the address map and once through exact coverage states, so it is asserted against a member of the producer enumeration and not only against an unrelated `source` |
| **W5a** | A basis change is ruled by case, never by default (§4.4) | Re-hold a dataset with a different manifest and assert a **new** entity with prior assessments still bound to the old. Correct a source's identifier and assert **one** entity: `uid` preserved, address renamed, old address resolving through `deprecated_ids`. **Negative:** assert the system does not choose between correction and new-work on its own |
| **W6** | The four resolution states never collapse | Resolve a ref whose corpus is absent, one that does not exist, and an alias matching two entities; assert three distinct findings. **Negative:** assert removing a corpus from the checkout does **not** convert its ids to `unknown` **Amended 2026-08-08:** **three** states, not four — `ambiguous` leaves with the stored alias (§5.1). Resolve a ref whose corpus is absent and one that does not exist; assert two distinct findings. The ambiguous-term refusal is now **W9**'s, at search time |
| **W7** | Views see the whole world, not a directory | Evaluate a topic view over an entity stored in another corpus; assert it is found — the `fb-2026-07-30-019` defect, pinned as a test rather than fixed per-consumer |
| **W8** | No conflict is resolved by precedence | Exercise all three §5 conflicts — duplicate location, ambiguous **search term**, address conflict; assert each gets its own handling and that **none** applies precedence: not project order, not checkout order, not recency. **Amended 2026-08-08** (world address ruling §4.3, §5.4): the second conflict's subject is a search term resolved against the **pinned authority snapshot**, not a stored alias, and the first is handled by **`consolidate`**, not by merge. The row's claim is unchanged — three conflicts, three handlings, no precedence — and only the two names move |
| **W8a** | All **four** index maps are derived, never authoritative — and the producers map, retraction enumeration, coreference reduction, and certification inventory carry their own scope (amended 2026-08-03, packaging §5 / 5a §4 / 5b §7.6; **amended 2026-08-08**, world address ruling §4.3 and §5.5 — the *membership* changed and the count did not: the alias-map arm is **deleted without replacement**, since a map derived from nothing has nothing to reconstruct, and a **coreference** arm replaces it) | Delete the world index and rebuild it from the corpora alone; assert the **address**, **producers**, **retraction** and **coreference** maps all reconstruct identically. **Added 2026-08-08 — the coreference reduction carries its own completeness evidence, on the retraction map's precedent:** omit an in-coverage `coreference-attestation` and repackage into an internally consistent epoch; assert validation of the **coreference-map derivation receipt** — rebuilding with its fixture-bound rule against corpora at its named states — **refutes** it. **And assert the coverage arm, which is this map's whole hazard:** build over a **narrower** corpus set and assert a pair's published balance may differ, that the **coverage declaration** differs, and — unlike the producers map — that `belief_input_digest` is **unchanged**, since coreference is outside belief (that ruling's §5.3). Then edit each map in the index only; assert the rebuild discards every edit. **Amended 2026-08-03 — the retraction map carries its own completeness evidence:** omit an in-coverage retraction and repackage into an internally consistent epoch; assert validation of the **retraction-map derivation receipt** — rebuilding with its fixture-bound rule against corpora at its named states — **refutes** it (packaging §7, X12). **Amended again at 5b's banking — so does the certification inventory:** omit an in-coverage `instrument-certification` from the address map and repackage; assert validation of the **certification-enumeration receipt** — same contract, same rebuild — **refutes** it (normative-contract §7.6, packaging §7, X12). **Coverage is part of the answer, not of the plumbing:** build the index over a **narrower** corpus set with every included corpus byte-identical, and assert (a) the producers map is smaller, (b) the **coverage declaration** differs, and (c) kernel §5.1's `belief_input_digest` **differs** — pinning that an enumeration is bounded by what it consulted and that two coverages are two belief inputs. **Negative — the receipt is beside the identity, not in it:** move an entity between two covered corpora so **both** corpus-state identities change while the producers map and the covered-corpus set do not; assert the **semantic** snapshot identity and `belief_input_digest` are **unchanged**, and that re-deriving mints a **new receipt** at a different receipt identity while the earlier receipt is left intact — W5 holds through the completeness mechanism as well as through the address map. **And the receipt is still required:** import a snapshot with no receipt and assert it is refused as unrecomputable. **Well-formedness before availability:** for a snapshot declaring coverage `{A, B}`, hand import a receipt naming **only `A`** with `A` present and standing at its recorded state; assert it is **refused as malformed** — and specifically that it is **not** evaluated against availability, **not** `unresolvable`, and above all **not `validated`**, which is what a rebuild from `A` alone would have returned for a map omitting every producer in `B`. Repeat with an **extra** corpus outside coverage, a **duplicate** `corpus_id`, and a receipt whose snapshot identity names a different snapshot; assert each is refused. **The values must be identities, not merely present:** hand import a receipt whose state value names a **corpus** rather than an exact corpus-state identity, and one whose rule reference is a **bare version string** with no fixture binding; assert **`malformed`** for both — specifically **not `unresolvable`**, since no corpus mount and no rule installation could ever make either checkable, and an `unresolvable` verdict would have told their author to go find the missing input. Then assert the contrast that fixes the boundary between the two predicates: a **syntactically valid** state identity and a **syntactically valid** rule identity that are simply **not held here** are `unresolvable`, not malformed — *is it an identity* belongs to `well_formed`, *is it held* belongs to `resolvable`. **Negative:** assert every malformedness above is decided **with no corpus present at all** and with **no rule held**, pinning that malformedness is a property of the record while unresolvability is a property of the checkout. **Malformed is an evaluator outcome, not only an import refusal:** **raw-write** a malformed receipt past the import boundary (§11.11), then run an **audit**; assert the evaluator returns **`malformed`** — not `unresolvable`, not `refuted`, and not `validated` — that the audit emits a **malformed finding naming that pair**, and that the same result comes back from the **diagnostic query**, which writes nothing. Assert the snapshot reduction **excludes** it: with that receipt alone, the snapshot is **`unchecked`** and **not `contradicted`**, so a forged record cannot condemn a snapshot; place a **validating** receipt beside it and assert the snapshot is **`checked`**, with the malformed finding **still emitted**. **Negative — the two roads to `unchecked` are distinguishable:** assert an audit over an all-malformed snapshot and one over a snapshot whose corpora are merely absent both report `unchecked`, but that only the first carries malformed findings — pinning that a permanent record defect is not filed as a transient checkout condition. **The rule identity is in the receipt, and its three transitions are distinct:** validate a receipt under an audit, then **(i) install a newer enumeration rule beside the old one** — assert the old receipt **still validates**, since its named implementation is still held and a content-addressed implementation never changes in place; **(ii) stop holding the old rule** — assert the receipt is now **unresolvable**, and **never refuted**, since nothing in any corpus changed; **(iii) re-derive under the new rule** — assert a **new receipt** at a new receipt identity, the old receipt untouched, and a **new snapshot only if the map or coverage differ**, with the semantic identity and `belief_input_digest` **unchanged** when they do not. Assert a rule identity naming an implementation that **fails its fixtures** is not that rule — a `resolvable` failure, since the reference is well formed and the world simply holds no such rule — while a bare version string is **`malformed`**, per the case above. **Two installations agree, with the precondition stated:** assert two installations in the **same availability context** — both resolving the same rule and the same per-corpus states — reach the **same** outcome for one receipt; assert one lacking the rule returns **`unresolvable`**, which is agreement about what it can establish rather than a contradicting verdict. **Negative — unavailable is not malformed:** import a snapshot whose receipt names exact states whose **corpora are absent from this checkout**; assert the import **proceeds**, that an **import finding** records the unchecked derivation, and that **no validation state is written onto either record**. Assert the malformedness refusals above are still refusals under exactly that condition, pinning that "cannot be checked here" and "cannot be checked" are different findings. **The availability transition, which is what must not move belief:** compute belief **naming that snapshot**, then **mount the corpora** and assert the digest and admission are **unchanged** — mounting is not an argument. Assert a computation naming a **different** snapshot **does** produce a different digest, since the identity is itself a belief input; assert the identity is a **required argument** with no default, so a computation naming none has no digest to produce, and that **no implicit "latest" and no stored selector** exists to be reached. Assert an **audit writes only a new snapshot and a new receipt** and by itself changes **no** belief. **A receipt is checkable only against a state that still exists:** validate a receipt under an **audit**, then change a covered corpus so it stands at a **new** state; audit again and assert the receipt is now **unresolvable** rather than refuted, and the snapshot **`unchecked`**. **The quantifier is per corpus:** build a receipt over **two** corpora, move **one** of them to a new state and leave the other untouched; assert the receipt is **unresolvable**, that the still-standing corpus does **not** satisfy the moved one's entry, and that restoring the moved corpus to its recorded state makes the receipt resolvable again. Assert the same for the rule conjunct, so all three ways of failing `resolvable` are covered — asserting specifically that **no stored validation survives**, since the state is an audit-time diagnostic that is evaluated and never written. Assert that a computation naming that **same snapshot identity** yields the **same digest and admission** across the whole transition, and that re-deriving mints a snapshot and receipt that are checkable again. **The evaluating operation is named:** assert **mounting a corpus performs no validation** — no finding, no record mutated, no validation result written — and that the **audit** is what evaluates. Assert import, audit and the diagnostic query all call **one read-only evaluator**, that only the first two are effectful (refusing a write; publishing a correction), and that the diagnostic query **writes nothing and feeds no belief computation**. **Negative:** assert no fourth path evaluates a receipt, and that the three callers **evaluating in the same availability context** return the same result, since they share the function rather than reimplementing it. **Then assert the limit:** the evaluator is **not pure** — assert the *same* `(snapshot, receipt)` returns `unresolvable` before a needed corpus or rule is available and `validated`/`refuted` after, so agreement is guaranteed **within** an availability context and across nothing else. **Per-pair validation and its quantifiers:** first assert the import boundary — hand it a receipt that is **resolvable and refuted right now** and assert it is **refused before any write**, with no file afterwards. Then build the state a refusal cannot produce, by the route §5 names: import a second receipt **while its corpus is absent**, so it enters unresolvable with a finding, then **mount that corpus and run an audit**, which is what evaluates it to **refuted**. **Then the other half of that route:** import a third receipt whose corpora are all present but whose **named rule is not held here**; assert it enters **unresolvable** with a finding rather than being refused, then **install that rule and audit**, and assert it now evaluates — to **refuted** where the rebuild disagrees, **validated** where it agrees. Assert the rule's arrival — which does of course change what is held, since holding the implementation is the point — **mutates neither the snapshot nor the receipt**, writes **no validation result** anywhere, and changes **no** belief; only the subsequent audit may publish a correction. Exactly as the corpus mount does not. With a validating receipt also present, assert the snapshot is **`checked`** and that the refuted outcome attaches to the **pair**, not to the snapshot. Now make the validating receipt unresolvable while the refuting one still resolves, and assert **`contradicted`**; then make **none** resolve and assert **`unchecked`**, **not** contradicted — the vacuous case, which an "every resolvable receipt is refuted" rule would have gotten backwards. Assert the three states are **total and mutually exclusive over the well-formed receipts**, and that adding a malformed receipt to any of the three leaves the state unchanged while adding one finding. **Negative — the boundary is a moment, not an invariant:** assert no rule requires every stored receipt to be non-refuting, that raw-writing a refuting receipt is likewise not refused, and that both are caught only when something evaluates them — otherwise `contradicted` would be a state with no reachable population. As the limit, assert a contradicted snapshot is **not retired** and can still be named by a computation (limitation 11). **Negative — one snapshot, several receipts:** re-derive after a change that leaves the producers map and coverage untouched; assert a **second receipt** at a **different receipt identity** naming the **same** snapshot identity, that neither receipt is overwritten, and that no belief digest moves — pinning that the receipt is its own record and not a mutable field of the snapshot. **Negative — absent is not empty:** hold out a corpus **inside** coverage that holds a producing run, and assert that producer reports **`not-present`** and the dataset does **not** read as undiverged; contrast with a producer outside coverage, which is unsuspected and is sub-problem 4 §11.15's stated limit rather than a detection. **Read 2026-09-10 (cut 24, slice 2 design §5):** the coreference coverage arm's "`belief_input_digest` is unchanged" clause is unsatisfiable as stated — `coverage` is a member of the producer snapshot's projection (`derive.ProducerSnapshot.projection`), so narrowing the corpus set moves the digest, which is this row's own producers clause (c). The arm is read as the digest-boundary claim it can carry: over one coverage, two epochs whose coreference maps differ carry one digest. |
| **W8b** | World `uid` uniqueness is enforced, and its two violations are distinguished | Place one `uid` under two different canonical addresses; assert **corruption**, and assert **no repair operation is offered** — *amended 2026-08-08: the operation this arm declined to offer was merge, which is retired; `consolidate` must be declined here for the same reason and a stronger one, since it **requires** one canonical address (ruling §5.4)*. Place two records at **one** canonical address in two corpora and assert a **duplicate-location** finding resolvable by **`consolidate`** — *amended 2026-08-08, same ruling; this is the equal-basis case and is storage repair, never an identity claim*. **Run it twice** *(added 2026-08-09)*: once with the two records **sharing** a `uid` and once with **distinct** `uid`s, and assert the finding is the same in both. Equal bases give an equal address and not an equal `uid`, so a check keyed on `uid` equality would miss the ordinary case entirely. **Negative:** assert a single corpus's own `nodes` check reports neither — the invariant is Science's, and no corpus can see it |
| **W9** | An ambiguous alias refuses and names its candidates | Author `related: [paper:Chen2023]` in a world holding two; assert refusal listing both world addresses, and assert **no** binding was written **Restated 2026-08-08:** the subject is an ambiguous **search term**, not a stored alias. Search a term the **pinned authority snapshot** maps to two identifiers; assert refusal listing both, and that **no binding was written**. **Negative:** assert the ambiguity is a property of the pinned snapshot — reproducible across two installations holding it — and not of accumulated authoring |
| **W10** | Cross-corpus edges are ordinary, not dangling | Place a lineage chain spanning two corpora — as `produces` / `transforms` edges on runs, since sub-problem 4 §5.2 makes `derived_from` a **view** composed from them — and assert the world traversal returns the full closure and emits **no** `lineage-incomplete`. Assert the same for a **lineage basis** whose producing run lives in the other corpus. **Negative:** assert the corpus-local closure *does* report both — pinning why lineage must run at the world layer, and that composing the relation raised the number of references that must resolve rather than lowering it |
| **W11** | A world entity is never addressed by a coordination address, or the reverse | Attempt a qualified `(project, id)` reference to a `source`, and a world address for a task; assert both refused by kind |
| **W12** | Renaming a project does not break coordination references | Rename a project; assert every `(project identity, local id)` reference still resolves, and that the old name survives only as an alias |
| **W13** | A corpus identity is minted, opaque and stable; its state identity is over content (§5) | Move a corpus's root directory, rename it, re-clone it and mount it at a second path; assert `corpus_id` is **unchanged** in every case, and that the coverage declaration naming it — and therefore `belief_input_digest` — is unchanged with it. Assert `corpus_id` is **not** derived from the path, directory name, remote URL or project name: change each and assert no effect; and assert **no ordinary API re-mints** it for an existing corpus. **Negative — amended 2026-08-03 (packaging §4): the immutability is the API's; manifest-only re-minting is detected, coordinated forgery is not.** Raw-edit the manifest's `corpus_id`, regenerate the snapshot and receipt consistently, and assert the next index build **refuses** — the presented id has no admission record while the registry still names the original (packaging X7). Then perform the **coordinated** act: raw-forge an admission for the new id while **retaining** the old id's admission — as a legitimate fork's registry would read — and assert **nothing detects it**: every state identity is self-consistent and the registry is well-formed. Under that retained-admission variant, assert the case that *looks* like a detection is not one: keep an **older replica** still resolving the pre-edit states, and assert every receipt naming them is **unresolvable against the edited corpus** (its states all moved with the id), that resolving them against the replica validates **the replica**, that **no assertion ties the new id to the old**, and that the resulting pair is **indistinguishable from a declared fork**. **Separately**, raw-delete an admission record alone and assert both halves: nothing detects the loss, **and** it evades nothing — the re-minted id is still unadmitted and the build still refuses (packaging X7). Assert no finding is emitted for any undetected case — G4/G8/S3's undetectable-history limit, one partial detection deep, needing §9's log for the rest. **Uniqueness:** place two corpora carrying one `corpus_id` in one world and assert the index build reports **corruption** and offers **no merge** — the W8b handling, not the duplicate-location one. **Replica vs fork:** restore a corpus from a backup and mount it in place of the original; assert the id is **retained** and every coverage declaration naming it still resolves. Then copy a corpus as a **fork**; assert a fresh id is minted, that the declaration is **authored** rather than inferred from the bytes, and that an undeclared fork is caught **only** when both corpora are live in one world. **State identity is content, not filesystem:** change a node's content and assert the corpus-state identity moves; **add, remove and retarget a `produces` relation** and assert it moves each time, **while the run's world address and every semantic identity stand still** — the case a subset-based content identity would have missed and the producers map is derived from. Then reformat a non-node file **other than the manifest**, rename a node's **file** without changing its `uid` or content identity, and touch every mtime, and assert the state identity is **unchanged**. **Amended 2026-08-04 (domain-extension-boundary §7): the manifest splits three ways** — reformat `corpus.yaml` (whitespace, key order, quoting) or reorder its `domains` mapping and assert the state identity is **unchanged**, since the member is a canonical projection of the parsed manifest; change any manifest field **semantically** — a pinned `science_contract` or domain contract identity, `corpus_id`, fork provenance — and assert it **moves**; and assert an unknown field, a duplicate `domains` key, or a malformed contract identity is **refused at load** rather than digested. Assert the identity is computed over `nodes`' **canonical JSON projection** (`STANDARD.md` §11.1) including `relations` and `facets`, and that **reordering a node's relations does move it** — the deliberate false positive, since cross-language equality is defined over document order. **Negative — not git:** compute the state identity for a corpus that is **not a repository** and assert it exists; then, in one that is, modify an **untracked** node file and assert the state identity **moves** while `HEAD` does not, and commit with no content change and assert it does **not** move. **Negative — a project identity is not a corpus identity:** point two projects at one corpus and assert one `corpus_id`; repoint a project to another corpus and assert **no** corpus identity changed |
| **W14** | The address scheme adds what the basis alone does not: a stored reference is unambiguous **by construction**, because **the only stored values participating in reference lookup are canonical addresses — the live one and its retired predecessors** — and **no presentation value participates** (added 2026-08-08; the *canonical identifier* phrasing was corrected 2026-08-09, having contradicted §5's address map, which resolves every stored `deprecated_ids` entry) | Author a reference to a record whose label collides with another's; assert the stored ref holds a **canonical address**, and that resolution consults **no presentation field** — no alias facet, no handle field, no rendered label. **The permitted set, asserted positively:** rename a record under §4.4's mis-transcribed-basis case and assert its **retired** address still resolves through the address map (**W5a**). A retired address is a canonical address that stopped being live — singular, derived from a declared basis, and the thing the rename's redirect is made of; forbidding it would break §4.4. Render one record under two locales; assert **two labels, one address, no stored difference, and no identity movement**. **Recursive rendering:** render a `dataset` and assert its `programme` and `release` fields render through the **pinned snapshot** while the dataset itself renders from immutable content — the renderer is per **value**, not per kind. **Sabotage:** add a stored field that resolution would consult **by label** → **refused**, since a lookup-bearing label field is an alias by another name. **The boundary, asserted rather than assumed:** author a `display_statement` **byte-identical to the rendered label** and assert it is **accepted** and resolves **nothing** — `display_statement` is authored, stored, identity-inert and lookup-inert (formal model §6.5), so a coincidence of strings is not an alias. The guarantee is about *participation in lookup*, never about which strings may appear in authored content. **Negative — this is not W1/W2, and neither implies the other** *(restated 2026-08-09: the arm read "mutate only the label", and there is no stored label to mutate)*: admit a presentation field into lookup while leaving every basis fixed and correctly encoded, and assert **W14 fails while W1/W2 pass**; then corrupt an encoding while admitting no presentation field, and assert the converse. W14 tests the *scheme*, W1/W2 test the *encoding* — the distinction F9 correctly observed they conflated. **Negative — not an authority-release invariance claim:** assert this row says nothing about whether bumping a consulted release moves `belief_input_digest`; under D6 it legitimately may |
| **W15** | A coreference balance is derived over **typed** endpoints, is unmoved by **exact** duplicate submissions, privileges no attester class, and its closure rewrites nothing (added 2026-08-08) | **Endpoint typing is four refusals:** assert refusal for a pair naming **one address twice**, for a pair of **different kinds** (`dataset` and `source` is a category error, not a coreference claim), for an endpoint that **does not resolve**, and for an endpoint that is a **curation note** — §3 of the ruling forbids a semantic reference to one, and an attestation is a semantic reference. Then post `+1` from a human actor and `+1` from an agent actor over one pair; assert balance **2** and an **active** edge, then **swap the two actors** and assert nothing changes — the symmetry *is* the assertion. Post a `-1`; assert balance **1**, the edge still active, and **both prior records still present** — a negative attestation **offsets**, it does not retract. Post a second `-1` from a distinct actor; assert balance **0** and the edge **inactive**, with every record retained. **Exact duplication cannot manufacture weight:** over a **fresh** pair standing at `0`, submit the same `(endpoints, stance, actor, grounds)` ten times under ten distinct event tokens; assert the **first** moves the balance `0 → 1` and the **remaining nine move it not at all**, while **ten records exist** — provenance is preserved, weight is not, because the token is outside the deduplication key. *(Stated as first-versus-rest 2026-08-09: the arm previously ran on from the balance-`0` sequence above and read "unchanged at 1", which contradicted its own setup and would also have been satisfied by an implementation that recorded nothing.)* **And assert the limit of that claim, so it is not read as more:** resubmit from the **same actor** with **different `grounds`**; assert the balance **does move**. The key defeats exact duplication only; it is not a per-attester cap, and no reduction over distinct rationales is claimed or built (ruling §5.2). **Closure does not rewrite:** with an active edge between `A` and `B`, assert a retraction targeting `A` still names `A` **exactly**, that `π_claim`, `belief_input_digest` and every content-identity basis are **byte-unchanged**, and that only **query expansion** observes the edge. **Coverage and the missing attestation (added 2026-08-08, ruling §5.5):** build an epoch over coverage `{A, B}` where `B` holds the only `-1` on a pair standing at `+2` in `A`; assert the published balance is **1** and the edge **active**. Rebuild with `B` **outside coverage** and assert the balance is **2** — a different answer under a different declared scope, and not an error. Then query a world spanning `{A, B}` while naming the narrower epoch and assert **`indeterminate`, refusing and naming the uncovered corpus** — specifically **not** `active` and above all **not** `inactive`, which is `fb-2026-07-27-010`'s error of reading a failure to look as a finding of absence. Assert the same for **no epoch named** and for a coreference map whose derivation receipt is **`unresolvable`**, **`refuted`** or **`malformed`** — all three, since every outcome other than `validated` leaves the balance unestablished, and `malformed` most of all: no mount and no rule installation could ever make it checkable (packaging **X10** for `unresolvable` and `malformed`; **X12** for `refuted`, the outcome only a rebuild against the named corpora produces). **Negative — absent is not empty:** an attestation whose corpus is **inside coverage but unmounted** still contributes, because the map publishes the **reduction** and not pointers a reader would have to resolve. **Negative — the cycle route stays shut:** activate coreference between two retractions and assert **no cycle is constructible through closure**; assert that this does **not** discharge the DAG invariant, which **M3**'s import validation over the bundle union the resolved world context still owns, and that a raw-written cycle remains auditable corruption |
| **W16** | `consolidate` repairs storage and asserts nothing about identity (added 2026-08-08) | Hold **one canonical address** in two corpora; `consolidate`; assert **one canonical address**, outgoing relations **unioned**, **no redirect written**, **no inbound reference rewritten**, and **no `deprecated_ids` entry created** — no address retired, so nothing needs one. **`uid`, both cases** *(added 2026-08-09: equal basis gives an equal address, and does **not** give an equal `uid`)*: with inputs **sharing** a `uid` — a stamped corpus that was copied — assert it is **preserved**; with inputs carrying **distinct** `uid`s — independent authoring of the same source from the same DOI, which is the ordinary case — assert **one input `uid` survives**, the other ceases to be live, and **no third is minted**. **Divergent lineage survives consolidation:** consolidate two dataset records at one content address carrying **different lineage bases**; assert **both** survive, that no field-selection path offers a choice between them, that the dataset is `lineage-divergent` with independence over it `not-certified`, and that the conflict **still stands after deleting either producing run** — the W4 arm, re-homed. **Negative:** attempt `consolidate` on two records at **different** canonical addresses and assert **refusal** — that is a coreference question and `consolidate` must not answer it. **Negative, which is W8b's first arm:** one `uid` under two **different** canonical addresses is **corruption**; assert `consolidate` is not offered, and that it refuses on its **one-address precondition** rather than on a corruption check. **Negative:** assert `consolidate` writes no `coreference-attestation` and moves no balance |
| **W17** | A coordination address has one standing tip, or resolution refuses naming every tip (added 2026-08-31, coordination-and-view-kinds design) | **Genesis and immutability:** mint a coordination record's first revision and assert it names zero predecessors; edit it and assert a **new whole revision** superseding the first, with the predecessor set stored as **adapter-authored** `supersedes` relations — an author-written one refuses. Assert `add`, `revise`, `supersede` and `retract` all **refuse coordination kinds** — `note` included, whose unscoped predecessor-era use is retired by succession banked in cut 14 (its §9.2, cut 9's citation mechanism: the entire cut-5 surface stays byte-identical and is cited rather than run, its discharge standing as its frozen results record) — that `import_bundle` **refuses a bundle carrying a coordination kind, naming the member** (an imported revision would bypass every family judgment), and that the family door refuses world kinds — no other door, in any direction; assert the **pre-plan already-minted guard** holds at the new door, keyed on the per-revision stored identity, so a replayed genesis refuses rather than silently replacing. **The general rule:** under the written root's lock, supersede a predecessor and then attempt a revision naming it; assert `PredecessorNotStanding` judged **at commit** through the coordination resolver over its explicit corpus set. **Continuity before standing:** attempt a revision whose named predecessor is a standing tip of **another kind**, and one whose named predecessor is a standing tip of **another address**; assert both raise `PredecessorMismatch` — supersession never retargets what or where a record is, even across two standing tips. **The sibling state:** mint sibling successors of one tip in **two corpora**, resolve over a set containing both, and assert `Refused(divergent-view)` **naming every tip** — then reverse the corpus-set order and assert the identical refusal, pinning that no recency, arrival, or iteration order chooses. **Repair:** mint one revision superseding **all** named tips — the multi-predecessor arity's one job — and assert the address resolves again, with every sibling retained immutable and superseded. **The intent-position rule:** judge admission as a **pure function of a constructed chain prefix** ending at an operation intent: a predecessor already superseded at that position refuses; a predecessor superseded **between** intent and commit admits, and the result is **two standing tips** — the sibling state lawfully reached, repaired the same way. Its operational instance (`publish`'s `publication-binding`) is sub-project 5's cut. **Negative — zero tips is corruption:** raw-write a `supersedes` cycle and assert an **audit finding naming the cycle**, that resolution reports no tip, and that **no repair is offered** — no sanctioned door can produce the state. **Negative — a record that cannot state its address claims none:** raw-write a coordination node failing the dedicated `coordination_facet_malformed` validator (the one function the mint door, the audit and the resolver share); assert the audit emits a **malformed finding naming it**, that the resolver **excludes** it from tip computation so the address still resolves to its standing tip, and that nothing repairs or deletes it — vandalism cannot flip a tip, and exclusion is not repair. **Negative — a subordinate needs its project:** attempt a `(project identity, local id)` mint under a project identity with no resolvable record, and under one whose record is divergent; assert both refuse, the second naming the project's tips |
| **W18** | Coordination minting is authorized by the pinned coordination contract, and the tier is world-inert (added 2026-08-31, coordination-and-view-kinds design) | **Authorization:** attempt a coordination mint in a corpus whose manifest pins **no** coordination contract; assert refusal — no pin, no mints. Pin version 1 and attempt a kind only a later amendment declares; assert refusal — an earlier version's pin authorizes nothing an amendment added. **Query admission is the malformed/unresolvable split at the mint boundary:** a view revision whose query fails the grammar, or names a kind, closure relation or version outside the pinned contract's **literal query vocabulary**, **refuses at mint**; a **well-formed** query whose anchor does not resolve in this checkout is **accepted** — well-formedness is a property of the record, resolvability of the checkout and epoch, and evaluation (the `world-read` lane's) is what refuses the latter, never by denoting the empty set. **The vocabulary's honesty is checked at compile:** a contract whose query vocabulary names a kind or relation the kernel inventories do not know refuses at `compile_profile`; and an editorial or lineage-only contract edit moves the contract identity while `compiled_identity` stands still, where a kind-schema edit moves both — the M7 split, held at this contract too. **World-inertness:** mint coordination records, package an epoch, and assert they appear in **no** world-index map — address, producers, retraction, coreference — and that `belief_input_digest` is **byte-unchanged** by their existence; assert no coordination kind declares a belief-bearing edge and that the consulted-contracts computation never names the coordination contract, whose declarations contain no operator to consult. **Negative — the namespace is reserved:** parse a domain contract claiming the `coordination` namespace and assert refusal, where the `science` reservation is already enforced |

**Current W17 disposition — discharged 2026-09-02.** The row above remains the
frozen guarantee. Cut 14 implements and selects its ordinary revision-family
clauses, but not the intent-position arm: the current chain surface carries
fingerprints rather than the coordination bytes needed to derive standing tips,
and a multi-corpus tip set is not a function of the source chain alone. The
coordination-and-view-kinds design §11.6 leaves that evidence with `publish`,
its first operational consumer; W17 therefore remains partial only on that
clause.

W1/W2 are the same mechanism observed on the two halves of §1.1, which is why
both are needed: a rule that only ever merges and a rule that only ever splits
each pass one of them. W10's negative half is the same pattern applied to the
substrate boundary — it asserts the corpus-local behaviour that would be wrong,
so nobody later "optimizes" the world traversal back into a corpus call.

## 8. Limitations

1. **The world layer is a new component, not a new file.** §5 requires a
   resolver, a cross-corpus adjacency and reverse index, a world-aware dangling
   check, and world traversal — because every `nodes` index is corpus-local.
   §5.1's `not-present` additionally requires the index to be publishable
   separately from the corpora it names. Nothing in `nodes` or `atoms` supplies
   any of this, and it is the largest thing this design asks to be built.
2. **Bases are frequently absent today.** §4.2 makes those records
   project-scoped **notes**, from which world entities are minted once a basis is
   supplied. The world therefore starts smaller than the corpus and grows as
   identifiers arrive. This is the intended direction but it is not free, and a
   note is not a weaker entity — it is not an entity.
3. ~~**Merge is recorded, not reversible.**~~ §4.3 requires a rationale; it does
   not supply an unmerge that restores prior references, and a wrong merge is
   discovered downstream of everything bound to it.

   > **Retired 2026-08-08** (`2026-08-08-world-address-ruling.md` §5). This
   > limitation described an operation that no longer exists: structural merge is
   > retired, coreference is a graded claim that collapses nothing, and a
   > mistaken attestation is answered by an offsetting one with both records
   > retained. **Three limitations replace it**, and they are the honest price of
   > the trade:
   >
   > 3a. **Two addresses persist for one work, permanently.** No operation reduces
   > them. Query-layer searches expand over active coreference closure; the
   > records never merge.
   >
   > 3b. **Attester reliability is unmeasured.** Unit weight is the honest default,
   > not a finding that attesters are equally reliable. Until the `meta/`
   > programme exists, a coordinated set of low-quality attestations outweighs a
   > single careful one and nothing detects it.
   >
   > 3c. **`consolidate` selects continuity.** Where two copies disagree on
   > content it reconciles, and reconciliation is a judgement recorded rather than
   > derived — the standing merge had, narrowed to storage repair.
4. **No access control.** §6 states that a project is not a permission boundary.
   A world in which every reader sees everything is the assumption; multi-actor
   corpora would need a boundary this design does not have.
5. **Single-writer still holds** (substrate §7). One world does not add
   concurrency; it enlarges what a single writer is writing to.
6. **Coordination gets an address, not a model.** §6.1 supplies the
   `(project identity, local id)` form that `t018` and `t043` need to *name* a
   blocker in another project. What a cross-project blocker *means* — how it
   propagates, what it blocks, how staleness crosses the boundary — is a
   coordination-semantics question this design does not answer.
7. **`consolidate` carries relations but not conflicts.** *(Restated 2026-08-08,
   world address ruling §5.4; the subject was merge, which is retired.)*
   `consolidate` unions the two records' outgoing relations. Two records
   asserting *contradictory* outgoing relations both survive that union, and
   reconciling them is left to curation. The limitation is unchanged in
   substance — a union is not a reconciliation — and it is now the whole of it,
   since the inbound-rewrite half named in limitation 8 no longer exists.
8. ~~**Inbound rewrite is eventual; resolution is not.**~~ §4.3's rewrite reaches
   only corpora the checkout can see, so a merge is not atomic over a world
   larger than the checkout.

   > **Retired 2026-08-08** (`2026-08-08-world-address-ruling.md` §5.3, §5.4).
   > **There is no inbound rewrite.** Structural merge is retired; `consolidate`
   > performs **no redirect and no inbound rewrite** because no address retires;
   > and coreference closure is a query-layer expansion that rewrites no stored
   > reference. The eventual-consistency hazard this limitation described has no
   > operation left to arise from.
   >
   > **The `deprecated_ids` residue survives, narrowed, as 8a.** A **rename**
   > under §4.4's mis-transcribed-basis case still appends to `deprecated_ids`,
   > resolution stays single-hop because the list is flat, and the list's
   > *length* on a long-lived entity is still unbounded. No pruning rule is
   > specified, deliberately: pruning discards the redirects that make a rename
   > safe, and no measurement yet shows the list mattering. What is *gone* is the
   > merge route that inherited whole redirect sets at once, which was the only
   > way the list grew faster than one entry per correction.
9. **The corpus manifest is a second new artifact, and adopting it is a minting
   event.** §5's `corpus_id` must exist before any coverage declaration can name a
   corpus, so every corpus that exists today acquires one by an explicit act — and
   that act is the one place a duplicate can be created, by copying a corpus after
   it has been stamped. Uniqueness is enforced at index build (W13), which detects
   the duplicate but cannot say which copy was the original. The manifest also gives
   a corpus content that is **not** a node, and **nothing here checks it**. Putting
   `corpus_id` inside every corpus-state identity does not make an edit to it
   detectable — it makes the edited corpus resolve **none** of the states that named
   it, so every receipt reaching for it reads as **unresolvable**, which §5 rules
   establishes nothing; and an old replica that still resolves them validates the
   *old* corpus while nothing ties the new one to it, a pair indistinguishable from a
   declared fork. *(Amended 2026-08-03, packaging §4:)* the registry's surviving
   admission record now catches the **manifest-only** re-mint at index build;
   **coordinated** re-minting — manifest plus a raw-forged admission for the new
   id, the old admission retained as fork mimicry requires, optionally also
   deleted as a separate registry-loss act — remains undetectable without §9's
   log. *(Amended 2026-08-04, domain-extension-boundary §7:)* the clause that
   "any further field the manifest grows is outside every check in this design"
   **no longer holds**: the corpus-state identity is now taken over the complete
   canonical manifest projection, so every manifest field — present or later
   permitted — is inside it. The surviving residue is narrower and unchanged in
   kind: a **coordinated** re-mint that rewrites the manifest and forges the
   registry consistently still moves every state identity together and remains
   undetectable without §9's log.
10. **A receipt's evidence decays, because a receipt is a name and not an archive.**
    §5's validation rebuilds the producers map from corpora that **still stand at**
    the states the receipt identifies, **under the rule it names**. Once a covered
    corpus moves on the bytes are gone; once the named rule is no longer held here,
    the derivation cannot be reproduced either. Both make the receipt
    **unresolvable** — it establishes neither completeness nor its absence. So a snapshot's completeness evidence is
    **time-bounded**, and keeping it alive means re-deriving snapshot and receipt as
    corpora change; nothing here forces that to happen, which puts it beside
    sub-problem 4 §11.11's audit-cadence question in sub-problem 6. Holding a
    hash-verifying corpus archive per receipt would make the evidence permanent, at
    the price of a full corpus copy each time, and this design does not ask for it.
11. **A contradicted snapshot is not retired.** §5 makes an audit's correction
    publishable — derive the right snapshot and receipt it, so a later computation can
    name the corrected one — but the refuted snapshot remains a well-formed record at
    its own identity, and a computation that names it still computes the false value. This is sub-problem 4
    §11.13's missing **retraction** reached from a third direction, after the
    divergent producer and the conflicted lineage basis, and it goes to sub-problem 5
    with them. The bounded claim in the meantime: a validated receipt makes
    completeness **checkable** and a refutation makes a correction **publishable**;
    neither makes the wrong answer unusable.

    **Designed 2026-08-03** (`2026-08-03-correction-lifecycle-design.md`; its §4
    semantic-snapshot instantiation and C8). A semantic snapshot is a `node`-arm
    retraction target: a retracted snapshot is refused at import and reported as
    `retracted` — a fifth evaluator outcome beside
    `malformed`/`validated`/`refuted`/`unresolvable` — at the three sites that
    already recompute. The bound narrows rather than disappearing, and 5a says so
    itself: enforcement is at import, audit and query, so a raw reader can still
    compute from the bytes. Until C1–C10 are implemented this limitation stands
    exactly as written.

## 9. What stops being needed

| surface | lines | why |
|---|---|---|
| `commons/promote.py` + `promote_dataset.py` + `promote_types.py` + `promote_render.py` | 3,423 | promotion is the bridge; one space has nothing to promote *to* |
| `commons/overlay.py` | 669 | an overlay is a project's local extension of a canonical record — under one world, one node carries both |
| `commons/identity_resolve.py` | 399 | superseded by §4's bases and the world index |
| `peers.py` + `peers_cli.py` + `peers_validate.py` | 645 | §6 retires peers |

≈ **5,136 lines**, plus the overlay awareness spread across 39 modules. As in the
substrate design this is a **scoping estimate, not a promise**: `commons/`
also holds `dataset_lifecycle`, `datapackage`, `variant` and `contigs`, which are
data-model work and stay.

**Two surfaces are replaced rather than removed, and the difference matters for
the plan:**

- `graph/composite.py` (135) — its premise goes, its function does not. §5's
  world layer is what assembles a queryable whole, and it is a larger component
  than the one it replaces, not a smaller one.
- `addressing.py` (85) — its entity grammar has no referent under one world; its
  project-qualified grammar survives for coordination (§6.1), rebound to project
  identity rather than project name.

Netting these out, this design **removes** ~5,136 lines and **builds** the world
layer of §5. It is not a reduction in total machinery, and presenting it as one
would be the same error as calling the world index a thin map.

> **Amended 2026-08-08 — machinery this design proposed and will now not build**
> (`2026-08-08-world-address-ruling.md`). The table above lists *predecessor*
> surfaces; these are this design's own, cancelled before implementation and
> recorded here so the world layer's scope is not over-estimated from the banked
> text: the **alias facet** and its schema; the world index's **alias map**; the
> **`ambiguous`** resolution state on the reference path; and **structural
> merge** — the redirect-set, inbound rewrite, absent-referrer and
> `uid`-selection machinery of §4.3, of which only `consolidate`'s much smaller
> storage repair survives.
>
> Against that, the ruling **adds** an eleventh kind, a derived balance, a
> query-layer closure, a **fourth index map** taking the alias map's place
> (coreference — reduction rule, derivation receipt and a place in the build's
> coherent enumeration, ruling §5.5), and a pinned-authority renderer whose
> snapshot artifact is itself undesigned (§10 there, limitation 5). *(Corrected
> 2026-08-09: an earlier version of this note claimed the map count fell from
> four to three. It does not — the membership changed and the count did not, and
> the coreference map is real work the alias map's retirement does not pay for.)*
> The net is **not** quantified, and this design's own warning against presenting
> a rebuild as a reduction applies to its amendments too.

The relevant number is not the line count. It is that **39 modules currently have
to remember that an entity might live elsewhere**, and one of them —
`fb-2026-07-30-019` — forgot, silently, in a coverage instrument whose whole
purpose is to report what is missing.

## 10. Open questions

- ~~**Where the world index lives, and who writes it.**~~ **CLOSED** by the
  world-index packaging design (2026-08-03): a world root outside every corpus
  holding an append-only registry, immutable epoch publications, and a held-rules
  store; explicit builds under per-corpus write locks publish epochs, derivation
  receipts live in the epoch beside the artifacts they name, and "held" is
  membership in the rules store.
- ~~**Where the corpus manifest lives, and what else is in it.**~~ **CLOSED** by
  the packaging design §6: `corpus.yaml` at the corpus root, reserved under
  `nodes`' reserved-path contract; fields are the manifest version, `corpus_id`,
  and optional fork provenance — nothing else, deliberately. *(Amended
  2026-08-04, domain-extension-boundary §7:)* the field set gains a `profile`
  block — one `science_contract` and a namespace-to-contract mapping of domains
  — and the "nothing else" reasoning is **superseded**, not overruled: it held
  because manifest fields sat outside every check, and §5 now takes the
  corpus-state identity over the complete canonical manifest projection. The
  shape stays **closed**: unknown fields, duplicate keys, and malformed
  contract identities are refused at load.
- ~~**The `source` basis when identifiers disagree.**~~ **CLOSED 2026-08-08**
  (`2026-08-08-world-address-ruling.md` §5). A paper with a preprint DOI and a journal DOI is one work
  with two issued identifiers, and §4.2 makes it two world entities. This
  question offered two answers — a *set* of identifiers with an equivalence rule,
  or a primary with aliases — and the ruling takes **neither**: one accepted
  identifier per record, both records standing, and the belief that they name one
  work carried by a **`coreference-attestation`** whose balance is derived. The
  "primary with aliases" branch dies with the stored alias (§4.3 here); the "set"
  branch would make identity depend on how many identifiers had been discovered,
  so a record's address would move when a second identifier arrived. **The cost
  is explicit and accepted:** two addresses persist for one work permanently
  (limitation 3a).
- ~~**Whether `run` and `assessment` need world identity at all.**~~ **CLOSED** by
  sub-problem 4 §8: both do, and collaboration is not the deciding dependency.
  `verification` is a world kind referencing two runs, so runs cross corpora by the
  kernel's own structure; `verification ──verifies──▶ assessment` carries
  assessments across by the same argument; and G3's belief digest already names
  `observes` dataset content identities that cross corpora.
- ~~**Merge versus a retraction's immutable exact target**~~ (opened 2026-08-05 —
  formal model ρO5; **CLOSED 2026-08-08**, `2026-08-08-world-address-ruling.md` §5.3, §5.4 —
  *by retiring merge, which is a fourth route none of the three candidate
  resolutions below listed*. No sanctioned action rewrites an inbound reference:
  `consolidate` requires one canonical address and performs no redirect,
  coreference closure expands queries and rewrites nothing, and a §4.4 rename
  leaves every stored target tuple byte-identical. The excluded portion of
  `Dom(step)` is therefore empty. **What this does not buy:** the DAG invariant
  is still checked at import, **M3** still owns that oracle, and a raw-written
  cycle is still auditable corruption — one route closes, the invariant still
  needs checking). W4 required that *every reachable inbound reference is
  rewritten* on a merge, while a `retraction`'s identity is derived from content
  that **includes its exact target tuple**. The two cannot both hold: merging
  assessment `A` into `A′` while `S` retracts `A` rewrites `S`'s target, changes
  `S`'s content, and therefore **re-mints `S`** — after which any `R` targeting
  `S` names a stale identity and is re-minted in turn, cascading as far as the
  retraction chain reaches. §4.3's ρA10 amendment closes the *cycle* case and not
  this one, and identity-preserving replica consolidation is exempt because it
  moves no target tuple. The candidate resolutions are visibly different designs
  — retractions naming targets through a **stable handle** rather than a content
  identity; **refusing** any merge that would change a retraction's exact target
  tuple; or **defining the cascade** and making it an explicit, recorded
  consequence of merging — and each trades something real. Until one is chosen,
  such merges have **no ruled outcome**: this is a gap in the design, not a
  refusal the system performs.

**No question in this section remains open** — both closed 2026-08-08, and the
open surface moved to the ruling's own §11 (which authorities are accepted and
who decides; whether a coreference balance belongs in any audit; the `meta/`
reliability programme; and F10, returned to the docket). Migration order is not
among the open set: §4.2 populates the world
incrementally as bases arrive, and whether that runs per kind, per project, or per
basis is an implementation-plan decision, not a design one.
