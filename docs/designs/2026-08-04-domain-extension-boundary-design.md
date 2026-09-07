# Domain extension boundary — design

**Status:** Banked 2026-08-04, after two review rounds; the banking commit
applies the amendment set below across world, packaging, kernel, substrate, the
normative contract, and the ledger. Rules where domain-specific material
lives across `nodes`, `science`, and downstream domains; closes substrate §12's
kind-SSOT question; and organizes the `science` repository so that a later
decomposition into distributable packs is a move, not a rewrite. No domain
exists yet: this design rules the **boundary** and the **organization**, and
deliberately builds no domain-pack machinery (ledger §5's materialization rule).
**Amended 2026-08-05** by the formal model and claim calculus design: §5's
resolution outcomes refine from three to **five** and D3 with them (ρA7); §6's
compiled-registry inventory widens — `ProfileSpec` compiles **claim schemas**
alongside `KindSpec`s, with D4's scope unchanged (ρA5); §8's consulted-set walk
gains every contract reached through a **claim schema**, and D6 gains that arm,
as does limitation 2 (ρA6); §12's predicate-vocabulary question **closes** —
yes, a domain contract like any other — and its versioning question records a
bound plus the parallel-genesis case (ρA5, ρC1).
**Amended 2026-08-07** by the corpus survey (eight corpora, 6,860 records): §2
gains **2.6**, making cross-corpus **agreement** and **exercise** necessary for a
base-profile vocabulary and a **reader** the clause that admits it; and **2.7**,
ruling one navigation-only `see-also` edge with no epistemic effect in place of a
second relation taxonomy, with the source→claim connection staying the existing
`source-assertion` record projected as an edge. It adds no guarantee row: 2.6's
first two clauses are a **review rule**, because the corpora they rest on are
outside this repository (corpus survey §7). 2.6's reader clause is testable here
and belongs to 5b's contract cut — as a **named** per-field check flipped by a
value perturbation, not as "removal breaks a test," which schema completeness
alone would satisfy. 2.7's no-epistemic-effect rows are **owed** with the edge
surface, which does not exist yet.
**Inherits:** substrate §2 (split by nature; the pricing argument;
defer-and-promote), §4.1/§6.1 (the arity-and-history test), §12 (the
`KIND_DESCRIPTORS`-versus-`KindSpec` open question, closed here); kernel §4.2
(the thirteen kernel kinds — ten until 2026-08-08, eleven until 2026-08-10, twelve until 2026-08-11), §4.2.1/§5.1 (the G3 belief-input closure), §4.3
(Referents — `term`, external), limitation 4 (the predicate vocabulary);
world §4.2 (per-kind identity bases; `dataset` is content identity), §5
(corpus-state identity), limitation 9 (the manifest is not a node and nothing
checks it); packaging §6 (the manifest's closed field set); normative-contract
5b §7 (rule binding frozen at freeze, receipt naming the executed
implementation); ledger §5 (record the seam, materialize later).
**Constraints:** the guarantee tables extend, never renumber. This design adds
its own table (**D**) and, where a banked rule must change (world §5, W13,
limitation 9; packaging §6; kernel §5.1; substrate §6.1/§12), amends in place
under the retained identifier.

**Banking amendment set** (to apply across the corpus in the banking commit):
world **§5**'s corpus-state identity is redefined over the **complete canonical
manifest projection plus** the sorted node identities; world **W13**'s
non-node-file clause splits three ways (manifest formatting-only → unchanged;
manifest semantic change → moves; other non-node file → unchanged); world
**limitation 9** narrows to the residue that survives; packaging **§6**'s
"nothing else, deliberately" closure is **superseded** by the `profile` block;
kernel **§5.1**'s G3 closure gains a member — **every profile contract the
derivation consults**: exactly one `science_contract` **unconditionally**, plus
each domain contract whose namespaced facets are actually read;
**W5 is preserved unamended** by §8.1's agreement and move-refusal rules;
substrate **§12**'s kind-SSOT question **closes** by retiring
`KIND_DESCRIPTORS` in favour of a single compiled `ProfileSpec`; substrate
**§6.1**'s
placement of the `empirical-observation` facet as native to `nodes` is
**corrected** to the `science` profile (§3.4 here); the **normative-contract**
design's exact oracle inventory (its §4) gains **D1–D10** — and, correcting
omissions, **L1–L13**, which the §9 banking never carried there, and **N1–N10**,
its own table, which its §5 requires in the suite. The ledger
gains this design in §1's artifact table and §3's order of work, and its
artifact-7 oracle inventory gains **L1–L13** and **D1–D10** for the same reason.

## 1. Why

Two problems, one boundary.

**The observed problem.** `proto-science` accumulated domain-specific material
without a rule for where it goes. Its `skills/` tree carries fourteen sibling
groups that conflate three different things: field domains (`bio/` → genomics,
transcriptomics, proteomics), methods (`statistics`, `ml`, `study-design`,
`literature`), and system concerns (`epistemics`, `meta`, `data-management`,
`writing`). Fifty-three generated artifacts sit inside the same tree as
hand-authored source. Entity kinds are minted dynamically as project-local
(`layer/local`) with no declared vocabulary anywhere. And the one piece of real
domain machinery — bio identity: gene crosswalks, assembly registry, cytoband,
liftover — is embedded imperatively in the tool because there was nowhere
better to put it. Nothing here is wrong locally; there is simply no rule, so
each addition picked its own home.

**The unruled problem.** The banked designs are, on inspection, almost entirely
**silent** on domain modeling — and the silence is verified rather than
assumed. "Ontology" and "controlled vocabulary" do not appear at all in the
substrate or computation designs; they appear once in world (§3's tier table,
placing `term` external) and only as `reads` inputs in the kernel. There is no
schema registry, no per-corpus typing, no plugin framework, and no
generic-versus-domain boundary stated anywhere. Two consequences follow. First,
this design is answering an open question rather than overturning a ruling —
substrate §12 says outright that the kernel's kind descriptors and `nodes`'
`KindSpec` registry are two registries where "one must derive from the other,
and which direction is unresolved." Second, the absence is already producing
drift: substrate §6.1 places the `empirical-observation` facet and its payload
schema *native to `nodes`*, while the same document's governing argument is
that scientific policy in a structural kernel "contaminates" it. That facet is
the hinge the entire eligibility predicate turns on. The boundary is already
blurred at exactly the point this design exists to rule.

## 2. Framing rulings

**2.1 Identity answers *which bytes*; interpretation answers *what they mean*.**
These are different questions and stay separate mechanisms. A dataset's basis is
content identity (world §4.2) and remains so; nothing in this design puts a
type, shape, format, or schema into an address. What the bytes *mean* — that
this file is a matrix whose rows are genes in a named vocabulary — is a
separate, **checkable** claim carried alongside. The separation is what keeps
replay's bitwise comparison sound while making interpretation falsifiable.

**2.2 Domain content never enters `nodes`; mechanism may.** `nodes` may hold
the facility for declaring, composing, and validating facets. It may not hold
biology, a controlled vocabulary, or an ontology binding. The reasons are the
substrate design's own: every addition to `nodes` costs a Python
implementation, a TypeScript implementation, conformance fixtures, and a
`STANDARD.md` bump (§2); "a primitive is justified by who can call it, not by
how clean it looks" (§2); and *defer-and-promote* is the stated default.
Domain facets have exactly one class of caller. They start above, and this
design promotes nothing.

**2.3 Interpretation is a facet while it is mechanically checkable metadata.**
A facet is the right carrier precisely as long as the claim can be validated
against bytes by a checker. The **promotion trigger** is explicit: when
interpretations need *independent authorship*, *competing alternatives*, or
*retraction*, they become interpretation **nodes**, because those three
operations are defined over records, not payloads — retraction in particular is
a record-level act (5a). Until one of the three is actually needed, promoting
early buys a node kind and its lifecycle for nothing.

**2.4 A vocabulary binding is exact or it is absent.** A bare name — "HGNC" —
is not a binding, because the referent drifts underneath it. A binding names
either a defined namespace *release*, or, preferably, the content identity of a
**held ontology dataset**. Whether that dataset resolves locally is a separate
question with a legitimate `not-present` answer (world §5.1's vocabulary),
which keeps domains installable without carrying gigabytes.

**2.5 Contracts govern corpus states; nodes carry no creation stamps.** "This
body of records was authored under biology 0.3" is recorded once, for the
corpus, as the contract its **current state** must validate against — not
stamped on every node. A per-node creation stamp is an unfalsifiable claim
about the past; a corpus-level pin is checkable now and fails loudly. The
temporal record that a stamp would duplicate already exists, with its own
stated bound: the mutation log registers **boundary-mediated** changes, and
`corpus.yaml` is inside its registered surface, so a raw edit is *detectable*
by replay rather than registered — subject to that design's anchor limitations
(its L5 unanchored-tail residue and the surviving-observer bound). Receipts
independently name the exact implementation that executed a check. A per-node
stamp would duplicate both while inheriting the same bound, since a stamp is
itself raw-editable.

**2.6 Cross-corpus agreement and demonstrated exercise are *necessary* for a
base-profile vocabulary; a reader is what admits it** (added 2026-08-07 — corpus
survey §4). Across at least **two** corpora with **separately evolved histories**
carrying at least 20 records each, a field proposed for the `science` base profile
must show:

- **agreement** — the corpora's value sets are **identical or nested**, where
  nested means every pair is comparable by inclusion. A **divergent** family, two
  corpora each carrying a term the other lacks, is refused; it is two
  vocabularies sharing a name.
- **exercise** — at least **two** distinct values occur across those corpora, and
  every value the contract declares occurs in at least one. A value occurring
  nowhere is dropped before admission.
- **a reader** — some rule, projection, invariant or computation in this system
  consumes the field. This is the **final** test and the one that admits.
  Agreement and exercise establish only that a field *could* be carrying
  information, never that anything reads it.

A field failing exercise is not admitted at all. A field failing agreement is
**out of the base profile** — and that is *all* divergence establishes. It does
not route the field into a **domain pack**: a domain contract costs ownership,
succession and a schema (§3), and every field the survey found divergent has no
reader either, so automatic routing would buy a contract for a vocabulary nobody
reads. A field enters a domain when a **domain** reader wants it, and is promoted
to the base when corpora agree *and* a base reader wants it.

A field passing agreement and exercise but having no reader **waits**, named,
until its reader exists — the survey's `strength` is the case: nested across four
corpora, discriminating in three, and still out of the base profile because belief
policy v1 weights every assessment at 1 and weighting is blocked on ρO3. Waiting
is the same state a divergent readerless field is in; the reader clause admits at
every level, not only the base.

**Separately evolved, not independent.** The corpora behind this rule share one
author and one predecessor system, so "independent" is a standard its own evidence
fails. The requirement is that the corpora's vocabulary choices were made in
separate projects, at separate times, with neither's frontmatter copied from the
other's. Under that weaker criterion agreement is weak evidence and disagreement
is strong, which is why the agreement clause is written as a refusal.

The unit is the **corpus**, not the record count. Two corpora at 20 records beat
one corpus at 2,000, because the failure guarded against is a project inventing
its own term, and that failure is invisible inside any single project. The
survey's `priority` is the case — two corpora, the same concept,
`high`/`medium`/`low` against `P1`/`P2`/`P3`, **zero** shared values, and each
corpus looking entirely reasonable alone. Its `scope`, `provisional` and
`pre_registered` are the other case: perfect agreement across two corpora on
**one value each**, over 307–317 records.

Exercise is measured **across** the corpora rather than within each, because a
corpus that happens to hold no negative claims is not evidence that `polarity` is
unreal.

**Every clause here was forced by a measurement that contradicted a draft.** The
first draft admitted on *discrimination* — top value below 90% in two corpora —
and against eight corpora it rejected `stance`, the one vocabulary in the survey
that never drifted, while admitting `status`, which shares 4 values of 20. Rarity
is not uninformativeness, and variety is not agreement. The reader clause was
added after agreement and exercise alone admitted a field nothing consumes
(corpus survey §4.1).

This remains weaker than *"this field is meaningful"*: two corpora can agree,
exercise a vocabulary, have a reader, and both use it wrongly. And it is a
**review rule**, not a guarantee, for the reason corpus-survey §7 gives — the
corpora are outside this repository, so no oracle can rest on them.

The reader clause is the exception, and what it owes is narrower than it first
looks. *Removing the field breaks some test* is **not** the oracle: schema
completeness, fixture coverage and a pinned contract digest all fail on the
**declaration**, while a reader consumes a **value**. Under N2, admission owes a
**named** check per declared field plus a fixture perturbation that changes the
field's value and flips that check's result, identity or refusal. `stance`,
`claim_layer` and `polarity` have such checks; `strength` has none, which is why
it waits.

The harder half, stated with it: **admission checks a state, not a permanent
verdict.** No field is added in order to be constant or to mean two things, so a
field found divergent or collapsed reports either that its distinctions were
never real or that authorship stopped making them. Both deserve an answer, and
neither is reachable without re-measuring.

**2.7 One navigation-only edge, and no second relation taxonomy** (added
2026-08-07 — corpus survey §9.1). Across eight corpora the untyped `related` edge
carried **62–84%** of every link while typed relations went unadopted and kept
multiplying — 56 detected link-bearing fields, 3 of them universal. The ruling is
therefore **not** a better taxonomy. There is **one** explicitly navigation-only
edge, **`see-also`**, carrying no inference, no closure traversal, no symmetry and
**no epistemic effect**: it cannot move belief, cannot alter an independent set,
and cannot appear in a G3 closure. A precise relation is added only when a reader
or an invariant uses it — 2.6's consumer test, applied to edges.

The attributed source→claim connection is **not** a new primitive. It is the
existing **`source-assertion`** record projected as an edge; it already carries
source, anchored span, stance and claim identity, and G1 already rules it out of
belief aggregation by type. An edge kind beside it would duplicate an existing
record and re-open the firewall G1 closes.

## 3. The ownership split

```text
nodes       facet / registry composition mechanics
science     kernel kinds and cross-node scientific policy
domains     namespaced facet contracts, schemas, validators, vocabulary adapters
practices   procedural guidance only — no vocabulary, no schema

        active domain contracts + science base profile
                            ↓
                   derived nodes Registry
```

### 3.1 `nodes` — mechanism only

`nodes` keeps what it already has: `Node`, `Relation`, `ShapeSpec`, `KindSpec`,
`Registry` with facet composition and invariant validation, indexes, and the
canonical projection. It gains **nothing** from this design (§6). It learns
about no domain, no ontology, and no vocabulary.

### 3.2 `science` — kernel kinds and cross-node policy

`science` owns the thirteen kernel kinds (kernel §4.2; ten until 2026-08-08, eleven until 2026-08-10, twelve until 2026-08-11), the relation signatures that
close belief, the eligibility predicate, and every judgment spanning more than
one node — the arity-and-history test from substrate §4.1/§6.1 is unchanged.
It also owns the **base profile**: the facet contracts that are scientific
rather than domain-specific.

### 3.3 `domains` — namespaced facet contracts

A domain owns a **namespaced facet contract**: the facet's key namespace, its
payload schema, its validators, and its vocabulary adapters. A domain never
defines a kernel kind and never redefines a relation signature; it contributes
facets to kinds that already exist.

### 3.4 The `empirical-observation` correction

Substrate §6.1 rules the `empirical-observation` facet and its payload schema
"native to `nodes`." Under §2.2 that placement is wrong, and this design
corrects it in place: the facet belongs to the **`science` base profile**. It
is the hinge of the eligibility predicate (kernel §4.1) — a declared acquisition
boundary is scientific policy in the most direct sense, and its honesty is
explicitly outside the guarantee (kernel limitation 8). Nothing about it is
structural. The correction costs `nodes` nothing and removes the one existing
counterexample to the boundary this design draws.

**Confirmed on review, 2026-08-04**, on an independent argument: `dataset` is
itself a Science kernel kind, and acquisition-boundary semantics are scientific
policy, so leaving either in domain-free `nodes` would contradict `nodes`'
own ownership contract. The correction does not rest on §2.2 alone.

### 3.5 `practices` — procedure without vocabulary

A practice (statistics, causal modeling, study design) carries **skills and
procedural guidance only**. The distinguishing test is mechanical: a domain
brings a vocabulary binding, a practice does not. If a practice acquires one,
it was a domain.

## 4. Interpretation as facet conjunction

There is no `BioDataFrame` kind and no `BioDataFrame` class. There is a node of
kind `dataset` carrying independently validated facets:

```yaml
kind: dataset
facets:
  tabular:
    orientation: wide
  biology/gene-axis:
    axis: rows
    vocabulary: dataset:<content-identity>
```

Each facet validates on its own terms; their conjunction is the "type." This is
composition rather than inheritance, and it means a domain adds expressiveness
by contributing a facet contract rather than by subclassing anything.

**What this does to identity, precisely.** A dataset's address is its content
identity, so adding or correcting an interpretation **does not mint a different
dataset** — the bytes did not change. But whole-node identity covers `facets`
(world §5, over `nodes`' canonical projection), so the same act **does** move
node content identity and therefore corpus state. That is the desired
asymmetry: the data is the same data, and the corpus knows something changed.

**No per-node domain list.** A node states which domain semantics it uses by
the **namespace of the facets it carries**. A redundant `domains:` field on
each node would restate what the facet keys already say, and would be a second
place to go stale.

## 5. Vocabulary binding

A domain's vocabulary adapter declares what it binds to. Two forms, in
preference order:

```yaml
# preferred — a held ontology dataset, by content identity
vocabulary: dataset:<content-identity>

# acceptable — a defined namespace release
vocabulary:
  namespace: MONDO
  release: "2026-07-01"
```

A bare namespace with no release is **refused**: it is the drift §2.4 exists to
prevent.

**Resolution is separate from binding, and its outcomes are five distinct
things in two groups that must never be mixed** — a distinction worth keeping
precise, because world §5.1's vocabulary is narrower than it is tempting to
assume:

| outcome | group | when |
|---|---|---|
| `member` | **resolved** | the vocabulary was read, and the term **is** in it |
| `not-member` | **resolved** | the vocabulary was read, and the term is **not** in it |
| `not-present` | **check not performed** | the bound ontology **dataset has a world address** that the consulted index records, but the corpus holding it is absent — world §5.1's case exactly, and only this case |
| `not-available` | **check not performed** | the dataset is identified but its **bytes are not held here**, so terms cannot be read — an artifact-availability fact, not an addressing one |
| `not-consulted` | **check not performed** | the binding's namespace was **never consulted** — nothing was ever indexed to be absent |

A binding is well-formed in all five cases; none is an error, and none may
silently fall back to a different release. **Only `not-member` refuses.** The
grouping carries the weight: the resolved pair reports what the vocabulary
*says*, the not-performed trio reports that nobody looked, and nothing anywhere
may read the second group as evidence about membership. Collapsing
`not-available` into `not-present` would report an unindexed artifact as though
the index had spoken about it.

> **Amended 2026-08-05** (formal model ρA7). This table previously had **three**
> rows, and its third was a **disjunction**: `unknown` meant *"the term is
> outside the bound vocabulary altogether, **or** the binding's namespace was
> never consulted."* Those are two incompatible facts under one token — one a
> finding, the other the absence of one — and only the first can carry a
> refusal. Under the old table a decoder reporting "not in the vocabulary" could
> be doing so on the strength of nobody having looked. The split adds `member`
> and `not-member` and renames the residue `not-consulted`; **`not-present` and
> `not-available` are unchanged**, so D3's existing arms pass verbatim.

This also keeps ontologies exactly where the kernel already put them: `reads`
inputs that confer no eligibility (kernel §4.1), and `term` entities identified
by the ontology's own identifier, scoped external (world §3).

## 6. The compiled registry — closing substrate §12

Substrate §12 asks which of `science_model.profiles`' `KIND_DESCRIPTORS` and
`nodes`' `KindSpec` registry derives from the other. The question is closed by
**retiring the descriptors**, not by choosing a direction: two per-kind
sources of truth are the defect, and picking a winner leaves the loser as a
derived duplicate that can drift.

There is **one** normative source — the **profile source**: the declarative
`science` base contract together with the activated domain contracts. Every
per-kind artifact is compiled from it.

```text
science base contract  ─┐   (normative SSOT)
                        ├─▶  ProfileSpec  ─┬─▶  KindSpec set ─▶ Registry.register()
active domain contracts ┘   (compiled)     ├─▶  claim schemas   (added 2026-08-05)
                                           └─▶  any further per-kind artifact
```

> **Widened 2026-08-05** (formal model ρA5, M7). `ProfileSpec` compiles more
> than per-kind artifacts. It also compiles **claim schemas** — the operator,
> dimension and sort declarations a domain contract issues — which are **not
> per-kind artifacts**: an operator roster is not a `KindSpec` and belongs to no
> kind. So *"any further per-kind artifact is compiled from it"* is no longer a
> complete description of what `ProfileSpec` compiles, and the sentence is
> widened rather than corrected: the rule was right, its inventory was short.
> **D4's scope is unchanged** — it governs the sole authored per-kind source and
> `KindSpec` compilation, and it does not reach claim schemas. That there is no
> second authored operator artifact beside the contracts is a separate
> obligation with its own oracle, the formal model's **M7**.

> **Two consequences made explicit 2026-08-06, while building the compiled
> path.** Both were implicit in §6 and neither survived a first implementation.
>
> **`ProfileSpec` is compiled, never authored — and that has to be enforced, not
> stated.** A profile a caller can construct field-wise *is* a second authored
> per-kind source, arriving through the constructor instead of through a file;
> a profile whose mappings can be mutated after compilation carries a compiled
> identity describing a profile that no longer exists. Both are
> `KIND_DESCRIPTORS`' drift with the two sources inside one object. The
> compiled artifact therefore exposes no public constructor and hands out
> read-only views.
>
> **Activated is not consulted.** D6's conditional arm already says an
> activated-but-unconsulted contract contributes nothing to
> `belief_input_digest`, but a compiled profile that carries one undifferentiated
> map of contract identities invites a consumer to take all of them — which
> moves a belief because an unrelated domain was switched on, the exact case
> D6's negative arm tests. The unconditional base identity and the conditional
> domain bindings are therefore **separate members**, and the map of activated
> domains is a **resolution table**: what a claim's identifiers may be resolved
> against, not what any derivation consulted.

The two roles are distinct and should not both be called "authoritative": the
**contracts are the normative SSOT** — what a reviewer reads, what a version
names, what an amendment edits — while **`ProfileSpec` is the sole compiled
runtime profile**, the merged and validated in-memory form nothing authors by
hand. `KindSpec` is a further **compiled runtime product** derived from it.
`KIND_DESCRIPTORS` does not survive as a parallel
per-kind SSOT — under the clean-start ruling (ledger §0) it is not carried over
at all, so nothing is deprecated and no compatibility layer is created; the
descriptor concept simply has no successor. Any future artifact needing per-kind
information is compiled from `ProfileSpec` on the same terms, never authored
beside it.

**This is why the `nodes` delta is zero.** `Registry.register()` refuses a
duplicate kind name, and one `KindSpec` owns a kind's complete allowed-facet
set — so `Registry` as it stands cannot accept two contributors for one kind.
The compiled-product framing makes that irrelevant: merging happens *upstream*
of `register()`, and `Registry` only ever sees one fully-composed spec per
kind. No new `nodes` capability, no `STANDARD.md` bump, no TypeScript parity
cost — the strongest available position under substrate §2's pricing argument.

Facet-key namespacing needs no feature either: `STANDARD.md` imposes no
facet-key grammar and both implementations accept arbitrary string keys, so
`biology/gene-axis` survives the current canonical projection unchanged. The
only implementation obligation is **one shared parity fixture** pinning a
namespaced facet key through both projections, so the freedom stays deliberate
rather than incidental.

## 7. Corpus activation — the manifest profile

The corpus manifest pins the normative contract under which its facets and
kinds are legal:

```yaml
manifest_version: 2
corpus_id: ...
profile:
  science_contract: science:<contract-identity>
  domains:                        # a mapping, not a list
    biology: biology:<contract-identity>
forked_from: ...                  # optional, unchanged
```

**`domains` is a namespace-to-contract mapping, deliberately not a list.** A
list leaves two things undefined that a digest cannot tolerate: whether the same
namespace may appear twice, and whether order is significant. A mapping makes
duplicate namespaces unrepresentable rather than merely forbidden, and makes
ordering a non-question. The manifest is a **closed** shape: an unknown field,
a duplicate key, or a namespace whose contract identity is malformed is
**refused** at load, never ignored.

**The projection is defined through the existing canonical encoding.** The
manifest projection is the `science.identity.v1` canonical form (computation
§4.3's value contract — NFC strings, sorted object keys, type-preserving) of
the parsed manifest, taken over the **complete** closed field set. Defining it
through the existing encoding rather than a new one is what makes D5's
formatting-inert arm true by construction: YAML whitespace, key order, and
quoting style vanish at parse, so only a semantic change moves the digest.

**Why the manifest and not a node.** A singleton activation node would
technically enter corpus identity, but it would introduce bootstrap ordering
rules, singleton semantics, and a new category of control node — all to
preserve a manifest closure this design is free to correct deliberately.
Correcting the closure is the smaller change and the honest one.

**The amendment is two-part, and one part without the other reproduces the
defect.** Adding `profile` while leaving corpus-state identity defined over
`corpus_id` plus node identities would place the pin *outside* every check —
exactly world limitation 9's residue. So:

1. Packaging §6's closed field set is **superseded** to admit `profile`.
2. World §5's corpus-state identity is redefined over the **complete canonical
   manifest projection** together with the sorted node identities.

The projection covers the **whole closed manifest**, not selected fields.
Hashing a chosen subset would recreate limitation 9 for every field the
manifest is later allowed to grow.

## 8. What enters identity, and what enters belief

This is the load-bearing chain, and each level answers a different question:

```text
each corpus manifest pins its profile contracts
        ↓
corpus-state identity includes the canonical manifest projection
        ↓
each semantic derivation includes every profile contract it actually interprets
        ↓
the receipt additionally names the exact implementation executed
```

**Why the third level is mandatory.** Corpus-state identities live in receipts,
not in belief (world §5). If the chain stopped at level two, biology 0.4 could
reinterpret `gene-axis` without changing facet bytes, without changing
assessment bytes, and without moving `belief_input_digest` — two different
beliefs behind one digest, which is precisely what kernel §5.1's G3 guarantee
forbids. So **kernel §5.1's closure gains a member**: every profile contract the
derivation actually interprets, alongside the existing belief-policy member —
`belief policy version` when this was written, and the exact **policy binding**
since 2026-08-05 (kernel §5.1, belief-policy §2.2) — which is the exact
precedent: a versioned rule entering the computed view as an input rather than
being stamped on records.

**The `science` base contract is unconditional; domain contracts are
conditional.** These are not the same rule, and collapsing them reopens the
defect.

`science_contract` governs the kernel kinds, the relation signatures that close
belief, the eligibility predicate, the **outcome-to-sign semantics** (added
2026-08-05, belief-policy §2.1 — `supported ↦ +1`, `refuted ↦ −1`,
`inconclusive ↦ 0`, which is base meaning and deliberately **not** a belief
policy's to choose, since a policy able to map outcomes to signs is a policy able
to reverse them), and the unnamespaced base-profile facets. A
Science semantic derivation therefore consults it **always** — interpreting
`assessment`, `dataset`, or a relation signature *is* consulting it, whether or
not the closure happens to read a base-profile facet. Making its membership
conditional on a facet read would let a successor contract reinterpret
`assesses` or the eligibility predicate itself without moving G3, which is the
original defect at a still more load-bearing place than §3.4's
`empirical-observation`.

So the consulted set is a set of **contract identities** built by two different
rules:

- **Exactly one `science_contract`, always.** Every Science semantic derivation
  includes it unconditionally. There is no closure walk that can omit it and no
  derivation that does not consult it.
- **Each domain contract, only if actually read.** A domain activated in a
  manifest but never interpreted does **not** enter the digest. Membership is
  computed rather than declared: walk the derivation's closure, collect the
  namespace of every facet it reads, **and every contract reached through a
  claim schema** — the operator, its dimensions, its argument and restriction
  sorts, and each sort's vocabulary binding — then resolve each to a contract
  identity by §8.1.

Belief therefore moves when the base contract moves, and when a domain contract
it actually used moves — not when an unrelated domain is upgraded.

> **The trigger set widens 2026-08-05** (formal model ρA6). D6's **asymmetry** —
> unconditional base, conditional domain — is untouched, and so is the
> facet-namespace rule: what changes is that facets are no longer the only route
> by which a derivation reaches a contract. A claim reaches its contract through
> its **operator**, and through the sorts and dimensions that operator declares;
> none of those is a facet key, so a facet-only walk omits the contract
> declaring `affects` from a belief derived over a claim at `affects`. Like
> limitation 2's under-collecting walk, this failure is **invisible in every
> test that uses facets** and fails **open**. The prior rule is not wrong — it is
> **insufficient alone**, which is a different fault and the reason this is an
> amendment rather than a note.

### 8.1 Cross-corpus agreement, and why W5 survives

A derivation's closure can span corpora, so "the manifest" is not well defined
without a rule — and the obvious reading breaks a banked guarantee. **W5
requires that moving an entity between corpora changes only its location**, and
asserts specifically that moving a dataset in the producers map leaves
`belief_input_digest` unchanged *even though both corpus-state identities
moved*. If corpus A pinned `biology@0.3` and corpus B pinned `biology@0.4`,
then moving a dataset from A to B would change the consulted contract and move
belief — a pure relocation with an epistemic consequence. W5's own note records
that two successive revisions of the snapshot identity already violated this
row; this would have been the third.

**The rule, which removes the possibility rather than trading it off:**

1. **Resolution.** A facet namespace resolves to the contract identity pinned by
   the manifest of the corpus holding the node the facet sits on. The
   `science_contract` resolves the same way, per corpus.
2. **Agreement.** Across one derivation's closure, every consulted namespace
   must resolve to **exactly one** contract identity. Two corpora in one closure
   pinning different identities for one namespace is **refused**, not merged,
   not preferred-by-recency, and never silently resolved. **`science_contract`
   agreement is required unconditionally** — every corpus in the closure must
   pin the same one, whether or not any base-profile facet is read, since §8
   makes the base contract an unconditional member.
3. **Move and consolidate.** Moving a node — or bringing two replicas of one
   node together under `consolidate` — into a corpus whose profile pins a
   **different** identity for any namespace the node's facets use is **refused**
   at the write boundary. *(This read "move and merge" until 2026-08-08;
   structural merge retired and the surviving equal-basis operation is
   `consolidate` — `2026-08-08-world-address-ruling.md` §5.4. A coreference attestation is not a
   relocation and does not reach this rule: it moves no node between corpora.)* For a **Science node**, the receiving
   corpus must pin the same `science_contract` regardless of which facets the
   node carries — a node with no domain facets at all is still governed by the
   base contract, so relocation across base-contract identities is refused too.

Rule 3 is what makes rule 2 satisfiable in practice and what preserves W5
exactly: a *permitted* move never crosses a contract boundary, so a permitted
move never changes the consulted set, so `belief_input_digest` is unchanged —
W5 holds unamended. What was previously an invisible digest change becomes a
visible refusal at the moment of the move. Upgrading a domain across a world is
therefore a deliberate, coordinated act over the corpora that share the
namespace, not a per-corpus drift that surfaces later as a belief anomaly.

**Level four is the existing normative-binding pattern**, not a new one: the
manifest pins *meaning*, and a check receipt names the exact implementation
that executed — the same split 5b makes between a rule's identity and the
implementation that ran it.

## 9. Organization in the `science` repository

```text
science/
  python/               # kernel kinds, cross-node policy, the compiler
    src/science/
    tests/
  ts/                   # the shared-encoding path only; see below
    src/
    tests/
  fixtures/             # cross-language parity corpus, owned by neither
    contracts/          # the synthetic domain contract the corpus is built from
  contracts/
    science/            # the science base contract (formal model §7.1)
  domains/
    biology/
      DOMAIN.yaml       # contract identity, version, namespace
      schema/           # facet contracts
      vocab/            # vocabulary adapters and bindings
      skills/
  practices/
    statistics/
      PRACTICE.yaml
      skills/
  docs/
```

> **Amended 2026-08-06, at the cut 1 slice.** The tree above replaces a
> single-language `src/science/ … docs/ tests/` layout, which predates the
> cross-language obligation the formal model's **M10** introduced and could not
> hold two implementations of one encoding. Three changes, and the reason for
> each:
>
> - **`python/` and `ts/` beside each other, mirroring `nodes`.** Science is
>   Python-primary — substrate §11 puts the composition root there, and formal
>   model limitation 9 records M10 as the **only** cross-implementation row, so
>   `ts/` carries the shared-encoding path (`science.identity.v1` and
>   `π_claim`) and not a second system. That asymmetry is recorded here in
>   prose rather than encoded as directory depth, because depth would have to be
>   restated every time the shared surface grows.
> - **`fixtures/` at the root, owned by neither language.** A parity corpus that
>   lives inside one implementation's tree is that implementation's fixture with
>   a second reader, which is the arrangement it exists to prevent. `nodes`
>   already does this.
> - **`contracts/science/` is new.** §6 names the base contract as the normative
>   SSOT and §7.1 gives it a shape, but no banked document sited it. It is
>   authored data, never a constant compiled into either implementation — *"which
>   is why it is a contract and not a constant"* (formal model §8).
>
> `tests/` moves inside each implementation because a test tree at the root of a
> two-language repository has to answer which language it tests on every file.

Three organizing rules, each aimed at a specific failure observed in
`proto-science`:

- **Generated artifacts never live in a source tree.** The 53 `science-*`
  generated skills are build output and belong in a build directory, not beside
  hand-authored material where the two become indistinguishable.
- **External provenance is retained.** `sources.yaml`'s per-source title,
  authors, license, upstream ref, and last-checked date is a genuinely good
  mechanism and survives, scoped per domain or practice rather than globally.
- **`aspects/` folds into `practices/`.** Causal modeling, computational
  analysis, hypothesis testing, and software development are methods, not
  fields; keeping a second parallel taxonomy is how the first one drifted.

Per ledger §5, these are **directories now**. A domain becomes a distribution
when there is an observed second consumer, and the layout is chosen so that
promotion is a move rather than a rewrite.

## 10. Guarantees, and how each is tested

New table, prefix **D**, certified by mutation per the estimator doctrine.
Rows D5, D6 and D7 depend on the banking amendment set (header) having landed;
until then the banked closures stand and those rows are pending, not failing.
D7's first arm is W5's own assertion, restated here because this design is
what must not break it.

| # | guarantee | mutation test |
|---|---|---|
| D1 | `nodes` assigns no domain semantics | assert `nodes` ships **no domain contract, schema, validator, or vocabulary adapter**, and that **no `nodes` API accepts** a domain, contract, or vocabulary argument; assert every domain-flavoured string in the `nodes` tree is **opaque** — its normative fixtures already carry `bio-axes` and `HGNC:7296` (`fixtures/gene_phf19.*`) purely as example payload the kernel never interprets, and that is **conforming, not a violation**; **negative:** add a `nodes` code path that reads a facet key's namespace and behaves differently for `biology/` → refused, since assigning meaning to a namespace is exactly what this row forbids. A grep for domain *names* is **not** the test and would fail against a conforming tree |
| D2 | Interpretation is separable from identity | add a `biology/gene-axis` facet to a dataset node and assert the **dataset address is unchanged** (bytes did not move) while **node content identity and corpus-state identity both move**; correct the facet's payload and assert the same asymmetry again; **negative:** change the bytes and assert a **different dataset** is minted with no facet involvement |
| D3 | A vocabulary binding is exact or refused, and its **five** resolution outcomes stay distinct across two groups (amended 2026-08-05 — formal model ρA7) | bind `vocabulary: {namespace: MONDO}` with no release → **refused** at contract load; bind a namespace+release and a held-dataset content identity → both **accepted**; then assert the outcomes are **not collapsed** (§5): index the bound dataset's world address but make its corpus absent → **`not-present`**; identify the dataset but hold none of its bytes here → **`not-available`**, never reported as `not-present`; never consult the binding's namespace → **`not-consulted`**; read a **readable** vocabulary and query a term in it → **`member`**, and one outside it → **`not-member`**. **Five-way non-collapsing:** assert no member of the five is reported as any other, and specifically that no *check-not-performed* outcome (`not-present`, `not-available`, `not-consulted`) is ever reported as `not-member` — the collapse the old three-state `unknown` permitted, and the one that would let a decoder refuse a good term because nobody looked. Assert **only `not-member` refuses**. In every case assert the binding remains **well-formed**, no error is raised, and **no fallback to another release** occurs |
| D4 | `ProfileSpec` is the only per-kind source; `KindSpec` is compiled | have `science` and a domain both contribute facets to `dataset`; assert exactly **one** `KindSpec` is registered for it carrying the union, that `Registry.register()` is called **once** per kind, and that no duplicate-registration error is reachable; mutate a domain contract and assert the compiled spec changes with **no `nodes` code change**; assert **no second authored per-kind artifact exists** — nothing plays `KIND_DESCRIPTORS`' old role beside `ProfileSpec`, and any further per-kind artifact is compiled from it; assert a namespaced facet key round-trips **identically** through the Python and TypeScript canonical projections (the one shared parity fixture this design adds) |
| D5 | The manifest pin is inside corpus-state identity, over a canonical projection | reformat `corpus.yaml` — whitespace, key order, quoting style — and assert corpus-state identity is **unchanged**; **reorder the `domains` mapping** and assert it is **unchanged** (ordering is inert by construction, since the projection sorts object keys); change a pinned contract identity and assert it **moves**; change any other non-node file and assert it is **unchanged**; assert the digest covers the **complete** canonical projection by adding a new permitted field and confirming it participates without a further amendment; **refusals:** an unknown field, a duplicate `domains` key, and a malformed contract identity are each **refused at load**, never ignored and never digested |
| D6 | Every consulted profile contract enters belief; activated-but-unconsulted ones do not — **through facets and through claim schemas alike** (claim-schema arm added 2026-08-05, formal model ρA6) | **the claim-schema arm:** derive belief over an assessment reading a claim at the operator `affects`, bump the contract **declaring** `affects` while touching **no facet**, and assert `belief_input_digest` **moves** — a walk collecting only facet namespaces reaches no operator and would miss this entirely; then derive belief over an assessment reading `biology/gene-axis`, bump the biology contract, and assert `belief_input_digest` **moves**; activate an unrelated domain and bump *it*, and assert the digest is **unchanged**; **the base-contract arm:** bump the **`science` base contract** in a way that reinterprets the **unnamespaced** `empirical-observation` facet (§3.4) and assert the digest **moves** — a consulted-set rule collecting only *domain* namespaces would miss exactly this, at the eligibility hinge; **the unconditional arm:** take a derivation whose closure reads **no base-profile facet at all**, bump the base contract so it reinterprets a **kernel kind or a relation signature** (`assessment`, `dataset`, `assesses`), and assert the digest **still moves** — membership of `science_contract` is unconditional, so no facet-triggered walk may be able to omit it; **negative — the defect this closes:** reinterpret a facet, kind, or signature in a successor contract without changing any facet byte or assessment byte and assert the digest **still moves**, so two beliefs can never share one digest |
| D7 | Contract agreement holds across a derivation, and W5 survives unamended | **W5 preservation:** move a dataset that appears in the producers map between two corpora pinning the **same** contract identities and assert `belief_input_digest` is **unchanged** even though both corpus-state identities moved — the row two prior snapshot-identity revisions violated; **agreement:** construct a closure spanning corpora pinning **different** identities for one namespace and assert the derivation is **refused**, never merged, never resolved by recency; **move refusal:** attempt to move a node whose facets use `biology/` into a corpus pinning a different `biology` identity and assert the **write boundary refuses**, so the belief-moving case is unreachable by relocation rather than tolerated; **the base-contract arms:** construct a closure spanning corpora that agree on every domain namespace but pin **different `science_contract`s** and assert the derivation is **refused** even though no base-profile facet is read; and attempt to move a Science node carrying **no domain facets whatsoever** into a corpus pinning a different `science_contract` and assert the move is **refused** — base-contract agreement is not conditional on facet content |
| D8 | Domain contributions compose without collision | two domains contributing same-named facets in **different** namespaces → both compose; two contributions to one namespaced facet key → **refused** at compile, never last-writer-wins; a domain attempting to define a **kernel kind** or a relation signature → **refused** |
| D9 | Practices carry no vocabulary | a `PRACTICE.yaml` declaring a vocabulary binding or a facet schema → **refused**; assert a practice contributes **nothing** to the compiled registry and therefore can never move `belief_input_digest` |
| D10 | Facets stay facets until the promotion trigger | assert no API retracts, supersedes, or attributes an individual facet payload — the three operations that define the trigger are **unspellable** over facets; assert correcting an interpretation is an ordinary node revision leaving no record of the prior claim, and that this is the stated cost (limitation 3) of not yet promoting |

## 11. Limitations

1. **Meaning can drift inside a validating revision.** A contract revision may
   change what a facet *means* while every stored payload still validates. The
   change is visible at corpus granularity — contract identity is
   content-derived, so the pin moves, corpus state moves, and every consulted
   derivation's digest moves (D6) — but it is **not adjudicated per node**.
   Nothing says which nodes' meanings actually changed. This is the same shape
   as the kernel's semantic-identity hazard and is stated, not closed.
2. **"Consulted" must be computed, and the computation is load-bearing.** D6's
   guarantee is only as good as the closure walk that collects facet
   namespaces **and claim-schema references** (widened 2026-08-05 — formal model
   ρA6). An under-collecting walk silently omits a contract from the
   digest, which is exactly the defect §8 exists to prevent — and it would fail
   *open*, not closed. The **unnamespaced** base-profile facets are one sharp
   case: a walk keyed on the presence of a namespace separator would drop the
   `science` base contract entirely while looking correct on every domain facet,
   which is why §8 states the empty namespace explicitly. **Claim schemas are a
   second, and they are worse**, because the omitted contract is reached by no
   facet at all: an operator, its dimensions, its sorts and their vocabulary
   bindings are all outside the facet-key space, so a facet-complete walk can be
   claim-blind while every facet test passes. This needs its own
   conformance oracle when 5b's contract cut lands.
3. **Correcting an interpretation leaves no record of the prior claim.** While
   interpretations are facets, a corrected payload is an ordinary revision: the
   previous interpretation is simply gone from the node. It is recoverable only
   from the mutation log, and only to the extent that log reaches — a
   boundary-mediated correction is registered, while a raw edit is detectable
   at replay rather than recorded, under that design's anchor limitations. So
   "recoverable from the log" is a qualified claim, not a guarantee. That is
   the accepted cost of not promoting early (§2.3), and the first time it bites
   is the promotion trigger firing.
4. **Domain contract authorship is unverified.** That a contract's schema
   faithfully describes its field is authored, not checked — the same class as
   kernel limitation 8's acquisition boundary.
5. **No domain exists yet**, and the limitation narrows rather than holding
   whole (*updated 2026-08-08*). Cut 1 and the typing exercise now exercise
   contract load, `genesis`/`successor` lineage, operator and sort declaration,
   and vocabulary binding — through `fixtures/contracts/testing.yaml` and the
   four plans under `tools/vocabularies/`. Every one of those is **deliberately
   not a real domain**: shipping `domains/biology/DOMAIN.yaml` is a design act,
   and §7.1's own biology example would be refused at load because no population
   vocabulary has been selected (§11, open). So what stays unexercised is
   **ownership, succession and activation** — a contract with an owner, a
   corpus manifest pinning it, and a second version of it. The first real domain
   is expected to move details, and the boundary rulings (§2) are what this
   design commits to — not the file layout.
6. **The domain/practice line is a judgment at the margin.** The vocabulary
   test (§3.5) is mechanical, but whether a body of expertise *should* carry a
   vocabulary is not, and misfiling is cheap to fix only before consumers pin
   it.

## 12. Open questions

- **Domain contract versioning policy** — **still open, now bounded**
  (2026-08-05, formal model ρC1). What constitutes a breaking change to
  a facet contract, and whether contract identity being content-derived is
  sufficient or a declared compatibility range is also needed. Interacts with
  5b's versioning rules and should be settled with them.

  **The bound.** Whatever policy is chosen must be **compatible with** four
  rules the formal model adopts for **claim vocabulary only** — operators,
  dimensions and sorts, not facets: every contract declares either **`genesis`**
  or **`successor(<predecessor contract identity>)`**; every claim-vocabulary
  identifier present in both a contract and its declared predecessor must carry
  an **identical canonical schema projection**, which compares meaning-bearing
  fields and lets a description, comment or example change freely; **retired**
  claim-vocabulary declarations are retained immutably as **tombstones**,
  because historical claims are typed against them; and a violation of any of
  these is **refused at contract load**, not at claim decode. So the policy may
  not permit a successor to drop a claim-vocabulary declaration, nor to reuse
  such an identifier under a different canonical schema projection.
  D §12's own framing — whether content-derived identity is *sufficient* — is
  answered in one direction only: **not for vocabulary**, because a
  content-derived identity says what a contract *is* and never what it
  *succeeds*.

  **What stays open, including one case the bound does not cover.** Breaking
  changes to **facet** contracts; whether a declared compatibility range is
  needed; how ranges interact with 5b's versioning rules; and the
  **parallel-genesis** case — nothing above stops an author publishing a
  *second* contract in the same namespace that also declares `genesis`, reusing
  an operator identifier under a different schema and never being compared
  against anything. The rules enforce immutability **within a declared
  lineage**, not across a namespace. Closing that needs either validation of a
  corpus's **pin transition** against its prior pin, or a **namespace/lineage
  authority** saying which contract legitimately succeeds which. Both are
  governance rather than typing, and neither is designed. The formal model's
  **M6** asserts the gap rather than concealing it: it tests that such a
  contract **loads**, and names this bullet as its home.
- **Parity for domains.** Whether a domain must ship Python and TypeScript
  validators or may be Python-first with parity declared per contract. The
  declarative form makes parity cheap but does not make it automatic.
- **Distribution.** Where domain contracts are published once they leave the
  repository, and whether a domain is ultimately a package, a corpus, or both.
  Ledger §5's split test governs, and nothing forces the answer yet.
- ~~**The predicate vocabulary.**~~ **CLOSED 2026-08-05** by the formal model
  and claim calculus design (ρA5): **yes — a domain contract like any other.**
  `predicate` becomes **`operator`**, declared by a domain contract without
  exception, carrying arity, argument sorts, permitted qualifier dimensions,
  sign-aptness and admissible layers; term identity, issue-and-retire, and
  *never redefine* follow the succession rules bounded above. The closed
  nine-term enum is retired, and **no second authored operator roster** may
  exist beside the contracts (M7). What that design does **not** close is the
  referent-binding half of kernel limitation 4 — the persistence, discovery,
  supersession and correction path for a claim's binding check — which is
  re-recorded as open there (its ρO1) rather than deleted.

> **Amended 2026-09-07** (facet-contracts design §3.4, §5, §6, §7.2).
> Section 3.4's payload schema travels with the facet — now literally, as the
> base contract's `facets:` entry. Section 6's compiled inventory includes
> kinds, relations, and facets. Section 12's parity question is answered for
> domain contracts: TypeScript parses their declarations with the same
> structural refusals, while payload validation remains Python-primary and
> sited with compilation. Distribution remains open.

> **Current implementation status, 2026-09-07.** Slice 1, the facet-contracts
> design dated 2026-09-05, is implemented and discharged as frozen conformance
> cut 20. Slice 2, the biology pack, remains open; cut 21 is a separate,
> undischarged verification-publication cut.
