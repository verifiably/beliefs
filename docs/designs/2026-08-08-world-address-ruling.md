# World address — the §4.1 ruling

**Status:** Ruled 2026-08-08. Closes **F9** and re-litigation docket **§4.1**
(`2026-08-05-review-disposition-and-conformance-cut-1.md`). Upholds basis-derived
addressing, and rules four things the docket's binary could not reach: a
generalized basis rule, derived labels in place of stored aliases, coreference as
a graded claim in place of structural merge, and an eleventh kernel kind to carry
it. **Un-couples F10**, which the docket folded into this ruling on a coupling
that does not hold, and returns it to the docket as its own item.

Amends **ten other design documents, five guide pages, the README and one guard**:
world addressing §2.1, §3, §4.2–§4.4, §5, §5.1, §7, §8, §9, §10; kernel §4.4,
§5.1 and **G3**; formal model §1, §2.1, §3.2–§3.4, §6.5, **ρA10**, **ρO5**,
**M3**, its W coverage map and limitation 11; correction lifecycle; computation
and reproducibility; substrate consolidation; world-index packaging; the
normative contract; the domain-extension boundary; the adoption ledger; the
README; five contributor-guide pages; and the corpus guard's `W` table. Adds
**W14–W16**, taking the frozen corpus to **138 rows** across eleven tables, and
the kernel to **eleven kinds**. **Closes ρO5** — by retiring merge, not by ruling
its cascade — and both of world §10's open questions.

**Corrected 2026-08-09** on review, in two passes. **First**, in six places: §2's kind table omitted
`source-assertion` (nine of ten, not eight); the retired alias and merge
machinery was still normative across eight documents; the W inventory stopped at
W13 where it is counted at W16; **W15** lacked endpoint typing and overclaimed
its duplication key; **W14** forbade a string rather than a lookup path; and §4
called new machinery a reuse.

**Second**, in three more. §5.2's balance summed over an unspecified universe
while no published map could supply one, so **§5.5 is added**: the epoch gains a
**coreference map** — the alias map's replacement, leaving the count at four —
publishing each pair's *reduced* balance under a declared coverage, and a **third
edge state, `indeterminate`**, derived per query rather than stored, which
refuses rather than defaulting to inactive.
Packaging's receipt contract and **X9, X10, X12** extend to it, so the map is not
published without the completeness evidence those rows exist to require.
**W14** contradicted the address map, which resolves every stored
`deprecated_ids` entry; it now permits canonical addresses live and retired, and
forbids presentation values. **`consolidate`**'s `uid` rule assumed the inputs
shared one — equal bases give an equal *address*, not an equal `uid` — so
duplicate location is redefined by the address and the `uid` rule splits in two.
The full site list, and what is deliberately *not* amended, is §8.

---

## 1. What this rules, and what it does not

Docket §4.1 asks whether a world entity's stored address should be derived from
its identity basis, or should stay a nominal `kind:slug` made unique at the write
boundary with the basis demoted to a coreference check.

This document answers that question, and then answers a larger one the docket did
not pose, because the honest answer to the first is *"neither side's framing
survives contact with §4.2."*

**Not ruled here.** Docket §4.2 (tamper log versus git) and §4.3 (normative
contract strata) are untouched. §4.2 is explicitly free to defer — every L row is
gated on composition-root adoption regardless. §4.3's substance is already settled by its own
table; what remains there is execution.

---

## 2. The docket asked the wrong question

> **The binary is a category error, and the corpus has already named this one.**
> World §4.2 opens: *"A basis assigned by category rather than per kind produced
> three defects in the first draft, so each of the eight kernel kinds is ruled
> individually."* §4.1's binary is that same move, one level up — a scheme
> assigned to the world rather than to its kinds.

Applied per kind, the alternative does not have a subject. Of the ten world
kinds, **nine have no human-typed slug to promote into an address**, and
`source` is the sole exception:

| kind | basis | is there a slug to promote? |
|---|---|---|
| `proposition` | `I_claim` (kernel §4.1, typed since 2026-08-05) | no — and it is built and frozen in cut 1 |
| `source-assertion` | content identity over (source identity, anchored span, stance, proposition identity) | no |
| `run` | content identity of the execution closure | no |
| `verification` | content identity over the ordered closure | no |
| `analysis-spec` | content identity, frozen pre-run | no |
| `assessment` | key over (spec, run, proposition) | no |
| `instrument-certification` | content identity over the certification closure | no |
| `retraction` | content-derived over target, reason, grounds, actor, event token | no |
| `dataset` | content identity | no — provider identifiers name a *programme* |
| `source` | normalized external identifier | **yes** — the citekey |
| *(handles generally)* | — | only on `source`, and on `dataset`'s provider fields |

To run the alternative on the first nine you would have to **mint** nominal
slugs for kinds that have none, purely to have something for boundary uniqueness
to enforce over. That is not a simplification; it is a second identity system
laid beside a sufficient one.

And the collision evidence sits entirely in the last two rows. §1.3's three
`paper:` pairs — `Chen2023`, `Liu2020`, `Shi2025` — are `source` handles. §1.1's
two dataset rows are provider programmes. The docket's strongest empirical case
applies to exactly the kinds this ruling handles by **not storing handles at
all** (§4).

> **The review's surviving point, kept.** F9's sharpest observation is not
> defeated by the above and is adopted: **W1** and **W2** test that the basis was
> *chosen and encoded correctly*, which follows from `encode ∘ πᵢ` being injective
> on admissible values together with domain separation and collision resistance.
> They do not test what the *address scheme* adds beyond that. **W14** is added to
> close it (§10).

**Verdict.** Basis-derived addressing is upheld. F9 is closed.

---

## 3. The generalized basis rule

World §4.2 rules the basis per kind and states the missing-basis rule only for
`source` and `dataset`. It generalizes, and stating it generally is what makes
the per-kind table a rule rather than a list.

> **Rule (2026-08-08).** Every addressable world entity has the basis declared
> for its kind: an **intrinsic** basis, or an identifier from an **accepted
> authority**. If that basis is missing, the record is a project-scoped
> **curation note** — not a weakened world entity.

Two clauses carry over unchanged from §4.2 and now bind all thirteen kinds
(eleven at this ruling; `holdings-observation` joined 2026-08-10,
`act-report` 2026-08-11): the refusal
and the note are **two operations**, never a silent coercion; and **no
fallback basis is derived at any point**, because a fabricated identity is
indistinguishable from a real one everywhere downstream.

One clause is **new**, and it closes a back door §4.2 left open:

> **A curation note cannot be the target of a semantic reference.** Notes are
> belief-inert prose, which constrains what a note can *do* to belief but not
> what may *point at* one. Without this clause an unbased record is reachable
> anyway — through a relation endpoint, a facet ref, or a view — which is the
> refusal being routed around rather than enforced.

**Where an accepted identifier does not exist**, the sequence is: retain the
record as a project-scoped curation note; prevent semantic references to it;
batch it into the migration queue; and mint a **governed local identifier** only
if recurring real cases prove external-only coverage insufficient. The local
identifier is deliberately not designed here — the trigger is recorded so the
option is not lost, and nothing is built for a case that has not occurred.

---

## 4. Labels are derived, never stored

> **Rule.** The stored reference is the **canonical identifier**. A **label** is
> computed on read and is never stored as world content. **Search terms** are
> authority-provided synonyms. A label never becomes a persistent world alias.

**The *shape* is banked; the *machinery* is not.** The formal model already banks
this split for `proposition`, separating `render(Claim, Locale)` — *"a
deterministic function of the typed form, the consulted vocabulary, and an
explicit locale — never an ambient one"*, **not stored, computed on read** — from
`display_statement`, authored, optional and identity-inert. This ruling
generalizes that split from one kind to every value.

What it reuses from cut 1 is the **pinning discipline** of the
`VocabularyBinding` + `ResolutionSnapshot` pair — an explicit binding, a snapshot
resolved once and named thereafter, and D3's arms testing that discipline. It
does **not** reuse the snapshot's payload: `ResolutionSnapshot` as shipped holds
**term membership only** — per binding, whether the vocabulary was readable and
the sorted set of terms it contained. It carries no preferred labels and no
synonyms, which are exactly the two things a label renderer and an
ambiguous-search refusal need. Supplying them is **new machinery**, and it is
ledger artifact 11 (limitation 5). Nothing here is a repackaging of something
already built.

### 4.1 The renderer is per value, not per kind

An earlier draft of this ruling stated two *kind* families and was wrong:
`dataset` is intrinsically addressed by content identity, and only its
`programme` / `release` fields carry authority identifiers. The rule is over
values:

| value | renderer |
|---|---|
| an **authority identifier** | `preferred_label(identifier, pinned_authority_release)` |
| a **record** | kind-specific rendering from immutable record content, **recursively rendering any authority identifiers it holds** |

> **Amended 2026-09-10 (slice 2b):** for `source` the renderer reads `stored.source_basis` — the selected `(scheme, value)` — and nothing else.

`source` is the pure first case — its basis *is* an authority identifier.
`dataset` is the second, holding authority identifiers in its fields.
`proposition` is the second and is the worked example already banked, consulting
vocabulary for its term labels only.

### 4.2 Resolution is against a pinned snapshot

Authority resolution uses a **pinned local snapshot, never a live network
lookup**. Builds stay reproducible, and an authority update becomes an explicit
amendment rather than a silent retroactive change. This is the ruling world §4.2
already makes for vocabulary, applied to labels.

**What CI can decide from a pinned snapshot:** two records carrying the same
canonical identifier; a non-canonical spelling; an identifier in the wrong
namespace or for the wrong kind; a label differing from the authority's preferred
label; an authority's explicit equivalence or replacement declaration; a record
missing its required identifier.

**What CI cannot decide:** that "DepMap" and "Cancer Dependency Map" denote one
thing. That is establishable only if both resolve to one identifier, or the
pinned authority lists one as a synonym of the other. Inference from strings
alone is refused.

**Fuzzy matching is candidate generation, never a decision.** A fuzzy label match
enters the review queue; authority evidence normalizes **form only**; missing
evidence leaves the record unresolved. Fuzzy matching never decides identity.

### 4.3 What this deletes

The **alias facet** on nodes, the **alias map** (one of the world index's four),
and the alias arm of the `ambiguous` resolution state. World §2.1 rejected three
alternatives for *where aliases live* — adding them to `nodes`, storing them only
in the index, reusing `deprecated_ids` — and never considered **not storing
them**. That is the identical defect F9 charges against §4, recurring one level
down, and it is recorded here rather than quietly repaired.

---

## 5. Coreference is a graded claim

**Same-basis coreference is unchanged and stays mechanical** — W2, *"a shared
basis establishes coreference mechanically … no curator assertion required."*
Nothing below touches it.

**Different-basis coreference** — a corrected identifier, an authority
`replacedBy`, "these two records are one work" — is where an attester enters, and
where structural merge used to fire.

> **Rule.** Different-basis coreference is an **attributed, additive attestation
> carrying a signed stance**. The pair's balance is **derived**. Nothing
> collapses: both records stand, both addresses persist, and no reference is
> retired or rewritten. **Structural merge is retired.**

### 5.1 `coreference-attestation` — the eleventh kernel kind

```text
coreference-attestation
  endpoints    sorted canonical pair — two DISTINCT exact addresses of the SAME kind
  stance       +1 | -1
  actor
  grounds
  event_token
```

**Basis:** content-derived over (endpoints, stance, actor, grounds, event token)
— the `retraction` shape exactly, which world §4.2 records as *"a content-derived
basis over target, reason, grounds, actor, and a minted event token."*

Sorting the endpoint pair makes `{A, B}` one identity regardless of authoring
order. The event token keeps two genuinely distinct attestation *events* distinct,
as the occurrence token does for `run`.

**The endpoints are typed, and the typing is a refusal.** Both must be exact
canonical addresses that resolve; they must be **distinct**, since a pair naming
one address twice is a claim with no content; and they must be of the **same
kind**, since "this `dataset` is that `source`" is not a coreference claim but a
category error. An unbased **curation note** is not an admissible endpoint either
— §3's clause forbids a semantic reference to one, and an attestation is a
semantic reference. Each of the four is a refusal at the boundary, not a warning.

**Rejected realizations, recorded so they are not re-proposed:**

- **Extending relation instances.** An edge cannot carry attribution, grounds, a
  stance and a derived balance. Giving it those makes it a node with worse
  ergonomics.
- **Reusing `source-assertion`.** Its stance is about a *proposition*, and its
  role-typing is what keeps literature→belief unspellable — the corpus's first
  must-survive item. Overloading it trades a structural guarantee for a saved
  kind.
- **A generic attestation framework.** Larger than the thing it would generalize,
  with exactly one instance. YAGNI.

All three are larger changes than the eleventh kind.

### 5.2 Balance is derived, and exact duplicates cannot manufacture it

```text
balance(A, B | coverage) = Σ stance over distinct (endpoints, stance, actor, grounds)
                           taken over attestations in the declared coverage
```

The event token preserves event provenance and is deliberately **outside** the
deduplication key.

**The sum is over a declared coverage, never over "whatever is checked out".**
An attestation is an ordinary world record and may live in any corpus, so a
balance computed from the local checkout is a derived enumeration nobody bounded
— the exact defect world §5's coverage declaration exists to prevent, and the
reason §7 here keeps that apparatus. The universe is therefore **explicit and
part of the answer**: §5.5 publishes the map, and a balance whose coverage cannot
be established is not a balance. A positive standing balance over an established
coverage activates the semantic coreference edge; **zero or negative does not**;
and **unestablished coverage is a third outcome, not a default to inactive**.

**What the key does and does not buy.** It defeats exactly one thing: the same
attester submitting the **same stance on the same grounds** repeatedly, whether
by a retry, a re-import, or an attempt to stack weight. It is **not** a general
reduction. An attester who varies `grounds` — a second citation, a reworded
rationale, a different line of evidence — mints another distinct unit and moves
the balance, and this is deliberate rather than a gap: two genuinely different
reasons from one attester *are* more evidence than one, and a rule that collapsed
them would need to decide when two rationales are the same rationale, which is
the string-inference §4.2 refuses. The honest statement of the guarantee is
therefore **"exact duplicates do not add weight"**, not "one attester counts
once". Stronger reduction — per-attester capping, grounds equivalence classes —
is a **policy** question that belongs with the reliability programme (§11.3), and
nothing here builds it.

**Unit weight is this ruling's default, and it is new.** Every attestation counts
±1; a human attester and an agent attester carry identical weight; the record
carries `actor` so reliability becomes *measurable* rather than assumed. The
belief policy is the **precedent, not the authority**: `science.belief.v1` fixes
`V = ℤ` with unit weight so a value is a signed evidence balance and never odds,
and there weighting by study design or precision is blocked on **ρO3**. ρO3 is
about study-design weighting inside belief. It says nothing about weighting
attesters, which is outside belief entirely by §5.3 — so this default is
**chosen here**, and it could be changed here without touching ρO3. It is chosen
for the same reason: privileging a class by category before the data exists is
arm-waving, and the honest move is to make the data collectable first.

**A negative attestation offsets; it does not retract.** Both records stand and
both remain recorded. `retraction` enters only if invalidating an *individual*
attestation ever becomes necessary — the trigger is recorded, the machinery is
not built.

### 5.3 Closure is a query-layer operation

> **Rule.** Coreference closure **never rewrites a stored reference, an identity,
> or a belief input.** Retraction targets, `π_claim` positions,
> `belief_input_digest` members and every content-identity basis read **exact
> addresses**, always. Closure expands **queries**.

This is load-bearing in two directions.

**It preserves the property retiring merge was meant to buy.** Retraction targets
stay exact-address references. If closure rewrote them, coreferencing two
retractions would recreate exactly the cycle structural merge could close — the
hazard W4 refuses today — through a new route.

**It keeps coreference out of belief.** A `dataset` coreference could otherwise
reach `belief_input_digest` through lineage and the producers map. Under the rule
it cannot, because belief reads exact addresses.

**This closes ρO5, and the mechanism matters.** The formal model's ρO5 — *merge
versus immutable exact targets* — recorded that a merge rewriting a retraction's
exact target tuple re-mints that retraction and cascades through everything
naming it, and that the choice among its three candidate resolutions *"belongs
with a world-addressing question, not here."* This is that question, and the
answer is a **fourth** route none of the three listed: retire the operation. With
no inbound rewrite anywhere — `consolidate` requires one canonical address,
closure expands queries, and a §4.4 rename leaves every stored target tuple
byte-identical — the pairs ρO5 excluded from `Dom(step)` have **no members**, so
`Dom(step)` is total and the cascade has no way to start. Formal model
limitation 11 retires with it.

> **Correction to an earlier draft of this ruling, recorded in place.** A draft
> claimed that retiring merge upgrades the retraction graph's acyclicity from
> **RF†** to **US†**. That is an overclaim. Retiring merge makes the
> *merge-created cycle route* unspellable; it does not make the DAG invariant
> unconstructible. Bundle import still validates acyclicity over the bundle
> **union the resolved world context** and refuses one admitting no topological
> order (ρA9), **M3** still owns that oracle, and a raw write remains auditable
> corruption. One route closes. The invariant still needs checking.

### 5.4 `consolidate` — the duplicate-location exit

Retiring merge would otherwise leave §5's `duplicate location` state with no
resolution, since world §5 records its only exit as *"resolved by an authored
merge."*

> **Duplicate location is defined by the address, not by the `uid`.** Two records
> at **one canonical address** — in one corpus or two. An earlier draft of this
> section said *"same basis, same address, same `uid`"* and was wrong on the last
> conjunct: `uid` is opaque and minted per authoring act, so two corpora that
> independently authored the same source from the same DOI hold one address and
> **two** `uid`s. That is the ordinary case, and defining the state by `uid`
> equality would have excluded it from the only operation that repairs it.
> Equal basis gives equal address; it does not give equal `uid`.

> **`consolidate`.** Requires **one canonical address**. Reconciles content and
> location. **Unions outgoing relations** and **preserves divergent lineage
> bases**. Performs **no redirect and no inbound rewrite** — no address retires,
> so nothing needs rewriting.
>
> **`uid`, both cases, one rule: never mint.** Where the inputs **share** a `uid`
> — a stamped corpus that was copied — it is **preserved**. Where they carry
> **distinct** `uid`s — independent authoring — `consolidate` **selects one input
> `uid`**; the other ceases to be live; **no third `uid` is created**. Selection
> is a recorded judgement, which is limitation 4's whole content.

**This does not weaken W8b, and the two arms stay distinguishable.** One `uid`
under **two different** canonical addresses is still **corruption** — two entities
were given one continuity anchor, no authored act produces it, and `consolidate`
is unavailable there by construction because it requires one address. Two `uid`s
under **one** canonical address is duplicate location and is repairable. The
asymmetry is right: an address is derived from a declared basis and equal bases
*must* collide, while a `uid` is opaque and equal `uid`s can only come from an
act that assigned them.

W4's equal-basis arm already described an operation of this shape without naming
it: *"the merge succeeds, the retraction's content identity is unchanged, and `R`
is not rewritten and not re-minted."* Naming it separates a storage repair from
an identity claim, which is the distinction the single word "merge" was hiding.

### 5.5 The coreference map, and what a query may conclude without it

§5.2's balance is an enumeration over records that may live anywhere, and §5.3
puts its consumption at the query layer. Neither states **where the enumeration
comes from**, and without that the balance is unusable in exactly the situation
the world layer exists for: a federated corpus set, partially checked out.

**The address map cannot supply it.** It resolves an address to `(corpus, uid)`
and carries no content, so knowing an attestation *exists* tells a reader nothing
about its `stance`, `actor` or `grounds` while its corpus is absent. Pointers are
not enough; the enumeration has to be published **reduced**.

> **Rule.** An epoch publishes a **coreference map** as a derived map beside
> address, producers and retraction: **sorted endpoint pair → (derived balance,
> distinct-key count)**, reduced at build under the epoch's **declared
> coverage**, with its own **derivation receipt** on the
> retraction-map precedent — that contract, and **X9**, **X10** and **X12**, are
> extended to it in this ruling's commit (packaging §7). It is **derived, never
> authoritative** (**W8a**), and it is **not a belief input** — §5.3 keeps
> coreference out of belief, so unlike the producer snapshot it carries no
> semantic identity and is absent from `belief_input_digest`.
>
> **The map stores the reduction and never the edge state.** An epoch is
> immutable, and the state below is a function of two things an epoch cannot
> know: which corpora the *querying* world spans, and whether the receipt
> resolves *now*. Publishing a state would freeze an answer that keeps changing
> under a fixed artifact — a stored value that can disagree with what it
> summarizes, which is the same defect §4 refuses for labels and world §5
> refuses for validation outcomes ("*the state is an audit-time diagnostic that
> is evaluated and never written*"). The epoch publishes what is fixed at build;
> the state is **derived per query**, like `standing` and like belief itself.

**The map's membership replaces the alias map's; the count is unchanged.** The
index held four maps before this ruling and holds four after — the alias map
retires (§4.3) and the coreference map arrives, in the same document. Nothing
here reopens the ordinal that correction lifecycle §4 used for the retraction
map; the maps are named, not numbered.

> **Rule — three edge states, derived at query time, and the third is not a
> default.** Given a named epoch and the world a query spans, an edge is
> **`active`** (published balance > 0 over an established coverage),
> **`inactive`** (balance ≤ 0 over an established coverage), or
> **`indeterminate`**: no epoch is named, the named epoch's coverage does not
> include a corpus the query's world spans, or the coreference map's derivation
> receipt is anything other than `validated` — `malformed`, `unresolvable` or
> `refuted` alike, on world §5's existing lattice. **Query expansion over an
> `indeterminate` edge refuses**, naming what it could not establish. It
> **never** silently reads as `inactive`.
>
> Two of the three inputs are query-time by construction — the spanned world and
> the receipt's current resolvability — which is why the state cannot be a stored
> field. One epoch answers `active` to a query over the corpora it covers and
> `indeterminate` to a query over a wider world, from the same immutable bytes.

That last clause is the whole point of the rule. Defaulting an unestablished
balance to `inactive` reads a **failure to look** as a **finding of absence** —
`fb-2026-07-27-010`, which world §5.1 already pins as the error separating
`not-present` from `unknown`. A coreference balance is the same shape of
enumeration as the producers map and inherits the same discipline: *an
enumeration is only as good as its stated scope, and the scope has to be part of
the record.*

**Two coverages are two answers, and that is correct rather than a defect.** A
balance over a narrower coverage may be smaller, and an edge active under one
epoch may be inactive under another. Since the balance is outside belief, this
moves no digest — the property W8a's coverage arm asserts for the producers map,
here with the belief consequence absent.

*(Read 2026-09-10: the producers-map property is that the digest **moves** with coverage; the coreference map's property is that it contributes nothing to the digest, asserted on one coverage — cut 24.)*

---

## 6. Programme and release are identifiers, not entities

A held dataset carries `programme` and `release` as **authority identifiers in
its own record**. Searching "DepMap" resolves against the pinned snapshot to an
identifier, not to a node. The only node is the held dataset.

```text
programme        authority identifier   (a field)
release/version  authority identifier   (a field, when the authority issues one)
held dataset     content identity       (the entity)
```

**The three levels must never be collapsed by a normalizer.** "Cancer Dependency
Map", "DepMap 24Q4" and a downloaded matrix are not interchangeable — this is
§1.1's observed confusion, and world §4.2 already refuses it (*"a provider
identifier names a programme, not data"*). Keeping the levels as distinct fields
is what makes the refusal structural instead of a check.

**What this costs:** a claim *about* a release — "24Q4 supersedes 23Q2" — is not
expressible, because a release is not an entity. Accepted. Promoting the levels
to entities would cost a twelfth and thirteenth kind for a capability nothing
currently needs.

---

## 7. F10 is un-coupled and returns to the docket

The docket folds F10 — *"world §5's receipt apparatus is 42% of the document and
its evidence expires"* — into F9, with the disposition *"its fate follows the
address ruling."*

**It does not follow.** §5's bulk is the producer snapshot, the coverage
declaration, the derivation receipt, the
`malformed` / `unresolvable` / `validated` / `refuted` evaluation lattice, and the
`checked` / `unchecked` / `contradicted` snapshot reduction. Those exist because:

1. corpora **federate**, so a corpus can be absent;
2. the producers map is a **belief input** — kernel §5.1 digests the producer
   snapshot's semantic identity;
3. a **derived enumeration needs completeness evidence**, or a snapshot that is
   merely hashed proves nothing about what it omitted.

All three hold identically under any address scheme. What *is* downstream of the
address scheme is the alias map, the alias arm of `ambiguous`, and W9 — and §4
deletes those on grounds that have nothing to do with receipts.

> **Disposition.** F10 is **not closed by this ruling** and is **not folded into
> F9**. It returns to the docket as its own item, with its question restated
> fairly: *is a receipt apparatus whose evidence expires on the next commit worth
> 42% of the world design?* That is live. It is not this question, and answering
> this one told us nothing about it.

The docket's cost list for F9 is corrected in the same move: it priced
basis-derived addressing at the address/alias duality, the alias map, the fourth
resolution state, W9, §4.4's rename machinery **and §5's receipt apparatus**. The
last item was never F9's to pay.

---

## 8. What this amends

| site | amendment |
|---|---|
| world §2.1 | the alias facet and the alias map retire; the fourth rejected alternative — not storing handles — is recorded; §2.1's rule that "the former slug survives as a non-unique alias" retires with it |
| world §3 | tier table gains `coreference-attestation` |
| world §4.2 | basis table gains `coreference-attestation`; the missing-basis rule generalizes (§3 here); `dataset`'s provider identifiers stop being "aliases" and become authority-identifier **fields** |
| world §4.3 | structural merge retires; §5.4's `consolidate` takes its duplicate-location role; "curator assertion" → attester |
| world §4.4 | the middle case **splits**, and the boundary moves from a judgement about *works* to a fact about *identifiers*: a **mis-transcribed** basis is still a rename with `uid` preserved and the old address in `deprecated_ids`; an **authority replacement** is a coreference attestation; a genuinely different work is unchanged. *"Only a person can say"* is withdrawn here |
| world §5, §5.1 | the index's map **membership** changes and its count does not: the **alias** map retires and the **coreference** map arrives (§5.5 here), so four stay four. The map table, "Science holds four maps", "all four are derived", the address/alias split argument (which survives one level out, over **search terms**), the derivation sentence and the belief-input exclusion list all follow; `ambiguous` leaves the resolution table and the refusal relocates to search time |
| world §3 (`uid`), §5 conflicts | `duplicate location` is repaired by `consolidate`, not merge, and is **redefined by the address** rather than by `uid` equality: two records at one canonical address, in one corpus or two, `uid`s shared or distinct. The `uid` rule is **not** preserved verbatim — it **splits**: preserve a shared input `uid`, select one of two distinct ones, never mint a third. The continuity row and the conflicts table follow, and **W8b**'s second arm runs both cases |
| world §5 (elsewhere) | the reverse-adjacency argument stops naming the alias map; §1.1's five collisions become ambiguous **search terms**; the whole-node content-identity sentence and the split-identity argument drop their alias-edit examples |
| world §10 | **both** open questions close — the `source` basis when identifiers disagree (answered by attestation, which is neither branch the question offered) and merge versus a retraction's immutable exact target (**ρO5**, closed by retirement). The section's closing sentence is rewritten: no question in it remains open |
| world §5 conflicts | `duplicate location` exits via `consolidate`; "ambiguous alias" → "ambiguous search term" |
| world §7 | W4, W6, W8, W8a, W8b, W9 restated; **W14–W16** added |
| world §8 | limitation 3 retires and **3a–3c** replace it; limitation 7 restates onto `consolidate`; limitation 8 **retires** — there is no inbound rewrite — leaving **8a**, the `deprecated_ids` growth residue that a rename still produces |
| world §9 | records the machinery this design proposed and will now **not** build, so the world layer's scope is not over-estimated from the banked text |
| kernel §4.4 | kind inventory and totals: ten → eleven |
| kernel **G3** | the alias mutation is **deleted without replacement** — location already tests OInv, G7 tests display invariance, and an authority-release bump is **not** a substitute because a consulted release may legitimately move the digest under **D6** |
| kernel §5.1 | the producer-snapshot argument stops leaning on "an alias edit would do the same"; it never needed the second example |
| formal model §2.1 | heading count, and the player table gains a `coreference-attestation` row |
| formal model §3.4 | observational invariance drops **alias** from its declared inert dimensions — there is no stored alias to be inert in. The rows it cites are untouched |
| formal model §6.5 | the `render` row generalizes to a per-**value** renderer; "authored **by a human**" → attributed |
| formal model W map | W4, W8a, W9, W14, W15, W16 restated; W14–W16 added, W15 gaining **FC** |
| formal model §5.3 | the 113-row / 128-assertion tally is marked as a **measurement at its date** rather than restated by arithmetic — three rows and one label moved under it, and it has not been re-measured |
| formal model §1 | the inherited world inventory → **W1–W16** |
| formal model §2.1 (rows) | four players drop **alias** from their inert dimensions; `dataset`'s provider identifiers become authority-identifier **fields** |
| formal model §3.2, §3.3 | the transition inventory retires `merge` and gains **`consolidate`** and **`attest-coreference`**; the `Dom(step)` exclusion becomes **empty**, so `Dom(step)` is total; the retraction graph's mutating paths go four → three |
| formal model **ρA10** | its subject retires: distinct-basis retraction merge is now **unspellable** rather than refused, which is stronger; the equal-basis arm survives as `consolidate`. The DAG invariant still needs checking — **M3** still owns it |
| formal model **ρO5** | **CLOSED** — by retiring the operation, a fourth route none of its three candidate resolutions listed. Its §10 summary, §9.1 not-covered row and **limitation 11** retire with it |
| formal model **M3** | the two merge arms restate onto `consolidate` and `attest-coreference`; the distinct-basis arm becomes an unspellability assertion |
| formal model §8.5 table | the ρA10 adoption row records its own supersession |
| correction lifecycle §2, §4 | the operation table's `merge` row becomes `consolidate` and gains the coreference distinction; ρA9's merge arm restates onto both successors; the retraction map's **ordinal is dropped** — it was "a fourth derived map" counting the alias map, and with alias out and coreference in the index still holds four, so the maps are named rather than numbered; "merge-widening" becomes "consolidation-widening" |
| computation §5.2, §7.3, §11 | `conflict` arises from **`consolidate`**, not merge, in all five places the operation is named; the `aliases, not the basis` sentence becomes authority-identifier fields; the world §8.3 citation is repointed at limitation 3c |
| substrate §5 | the lineage-basis note names `consolidate` |
| packaging §0, §5, §5.1, **§7** | the epoch's four maps change membership — alias out, coreference in — and the coherent-enumeration view is shared across all four; **merge inbound hygiene lapses** as a requirement on the index; and §7's receipt contract gains a **fourth receipt**, the coreference reduction, on the retraction-map contract member for member, with the two ways it differs from its siblings stated — no semantic identity and no belief input, and a failed validation that makes covered edges `indeterminate` rather than only reporting a finding |
| packaging **X9, X10, X12** | the three receipt rows extend to the coreference reduction: X9's identical-states arm covers four receipts; X10 gains the `indeterminate`-and-refuse consequence on the two outcomes it owns, **`unresolvable` and `malformed`** — the latter would otherwise have no consequence anywhere; and X12 gains an omitted-attestation arm, a **wrong-balance** arm and, since only a rebuild can produce one, the **`refuted`** arm with the same consequence, so the reduction is checked and not only its membership. The three non-`validated` outcomes are covered once each across the two rows, not twice |
| normative contract §3 | the contract's operation inventory: `merge` → `consolidate` + coreference attestation |
| domain boundary §8.1 | "move and merge" → "move and consolidate", with a note that an attestation is not a relocation and does not reach the rule |
| domain boundary §1, §5 | "the ten kernel kinds" ×2 → eleven |
| normative contract §4 | the frozen-row count 135 → **138**, and the **exact current inventory** extends to **W1–W16** — without this the count guard passes while the contract excludes the rows it counts |
| adoption ledger | **artifact 11** (the pinned authority snapshot, owed and undesigned); a §0 note carrying the kind count, the merge retirement and the F9/F10 disposition; artifact 1's map list and its merge-hygiene requirement; artifact 7's oracle inventory → W1–W16; §3's ρO5 pointer; §4's **concurrent-merge interleaving gate lapses** — there is no cross-corpus referrer rewrite left to interleave |
| README | the design table gains this document, and the world row drops "aliases" and reads W1–W16; the frozen-row count → 138 |
| guide `foundations.md` | the kind inventory gains `coreference-attestation`; heading, count and one inbound anchor follow |
| guide `identity-world-and-change.md` | `sources`; "Current state" gains the ruling; the W-range reference → W1–W16; the identity table's **Alias** row becomes **Label**; the four index maps keep their count and change membership — alias out, coreference in; the open-edges sentence drops merge continuity |
| guide `glossary.md` | **Alias** is deleted; **Label** and **Coreference attestation** are added; `UID` stops citing merge |
| guide `open-questions.md` | the two closed world questions are replaced by the ruling's three open ones |
| guide `contracts-and-adoption.md` | the frozen-row count → 138 |
| `python/tests/test_designs_corpus.py` | `GUARANTEE_TABLES["W"]` extends to W16, so the range and count guards see the new rows |

**Not amended, deliberately:**

- **W1, W2, W5, D2, M3**, and every G (but for G3), S, L, R, C, N and P row.
  **X is no longer among them:** **X9, X10 and X12** extend to the coreference
  reduction's receipt (§5.5), because a map published under a coverage without a
  receipt is the completeness gap those three rows exist to close. X1–X8 and X11
  are untouched.
  W5 and D2 carry **no alias arm** — the formal model's invariance row cited them
  for the *dimension*, which is what changes, not for a test that mentions it.
- **Correction lifecycle §3.** `retraction`'s basis is the *model* for the new
  kind, which cites it; nothing in correction lifecycle changes. Its import
  acyclicity obligation is explicitly **unchanged** (§5.3).
- **Computation §, and normative contract §7.2**, which call
  `instrument-certification` the *tenth* kernel kind. It still is. Only the
  **total** moved, and only where a total is stated.
- **The disposition record's own measurements** (§1's "126 rows across ten frozen
  tables", W 16), which are dated evidence and stay at their date under §5.4's
  discipline. Cut 1's denominator of 126 is likewise frozen and untouched.

---

## 9. Guarantees, and how each is tested

Certified by mutation, per the kernel's §5 discipline. Three rows are added; three
are rewritten.

| # | Guarantee | Mutation test |
|---|---|---|
| **W14** | The address scheme adds a property the basis alone does not: a stored reference is unambiguous **by construction**, because **the only stored values that participate in reference lookup are canonical addresses — the live one and its retired predecessors**. No presentation value participates. Labels are rendered, never resolved against, and rendering is locale-explicit | Author a reference to a record whose label collides with another's; assert the stored ref holds a **canonical address**, and that resolution consults **no presentation field** — no alias facet, no handle field, no rendered label. **The permitted set, asserted positively so the rule is not read as narrower than it is:** rename a record under §4.4's mis-transcribed-basis case and assert the **retired** address in `deprecated_ids` still resolves through the address map (**W5a**, world §5). Retired addresses are canonical addresses that stopped being live; they are not aliases, they are singular, and forbidding them would break the redirect the rename depends on. Render the same record under two locales; assert **two labels, one address, no stored difference, and no identity movement**. **Recursive rendering:** render a `dataset` and assert its `programme` / `release` fields render through the pinned snapshot while the dataset itself renders from content. **Sabotage:** add a stored field that resolution would consult **by label** → the corpus must refuse it, since a lookup-bearing label field is an alias by another name. **The boundary, stated as an arm:** author a `display_statement` whose text is **byte-identical to the rendered label** and assert it is **accepted** — an authored, identity-inert, lookup-inert string may coincide with a rendering, and the guarantee is about *participation in lookup*, never about which strings may occur in authored content. Then assert that string resolves **nothing**. **Negative — this is not W1/W2, and the two are independent:** admit a presentation field into lookup while leaving every basis fixed and correctly encoded; assert **W14 fails and W1/W2 still pass**. Then corrupt an encoding while admitting no presentation field; assert the converse. Neither row implies the other |
| **W15** | A coreference balance is derived over typed endpoints and a **declared coverage**, is unmoved by **exact** duplicate submissions, and privileges no attester class; closure rewrites nothing, and an unestablished coverage refuses rather than reading as inactive | **Endpoint typing, four refusals:** assert refusal for a pair naming one address twice, for a pair of **different kinds**, for an endpoint that does not resolve, and for an endpoint that is a **curation note** (§3). **Balance:** post `+1` from a human actor and `+1` from an agent actor over one valid pair; assert balance `2` and an **active** edge, and assert **swapping the two actors changes nothing** — the symmetry is the assertion. Post a `-1`; assert balance `1`, the edge still active, and **both prior records still present**. Post a second `-1` from a distinct actor; assert balance `0` and the edge **inactive**, with every record retained. **Exact duplicates:** over a **fresh** pair at balance `0`, submit the same `(endpoints, stance, actor, grounds)` ten times under ten distinct event tokens; assert the **first** submission moves the balance `0 → 1` and the **remaining nine move it not at all**, while **ten distinct records exist** — provenance is kept, weight is not manufactured. Stating it as the first-versus-rest transition is the point: "unchanged" alone would be satisfied by an implementation that recorded nothing. **The stated limit of that, asserted as such:** resubmit from the **same actor** with **different `grounds`** and assert the balance **does move** — the key defeats exact duplication only, and per-attester capping is not claimed (§5.2). **Closure does not rewrite:** with an active edge between `A` and `B`, assert a retraction targeting `A` still names `A` exactly, that `π_claim`, `belief_input_digest` and every content-identity basis are **byte-unchanged**, and that only **query expansion** observes the edge. **Missing attestation, which is the arm the map exists for (§5.5):** build an epoch over coverage `{A, B}` where `B` holds the only `-1` on a pair standing at `+2` in `A`; assert the published balance is `1` and the edge **active**. Then hold `B` **out of coverage**, rebuild, and assert the balance is `2` — a different answer under a different declared scope, and **not** an error. Now query against a world spanning `{A, B}` while naming the narrower epoch, and assert **`indeterminate` and a refusal naming the uncovered corpus** — specifically **not** `active`, and above all **not** `inactive`, which is what reading a failure to look as a finding of absence would produce. Assert the same for **no epoch named**, and for a coreference map whose derivation receipt is **`unresolvable`**, **`refuted`** or **`malformed`** — all three, `malformed` included; packaging carries them split by what produces each, **X10** for `unresolvable` and `malformed` and **X12** for `refuted`, which only a rebuild against the named corpora can produce. **Negative — absent is not empty:** assert an attestation whose corpus is merely **unmounted but inside coverage** still contributes, because the map was reduced at build; pinning that the map publishes the *reduction*, not pointers a reader would have to resolve. **Negative — the cycle route stays shut:** activate coreference between two retractions and assert **no cycle is constructible**, and that M3's import validation is still what refuses a raw one |
| **W16** | `consolidate` repairs storage and asserts nothing about identity | Hold **one canonical address** in two corpora; `consolidate`; assert **one canonical address**, outgoing relations **unioned**, divergent lineage bases **both preserved**, **no redirect written**, and **no inbound reference rewritten**. **`uid`, both cases, since equal basis does not imply equal `uid`:** with inputs **sharing** a `uid`, assert it is **preserved**; with inputs carrying **distinct** `uid`s — the independent-authoring case, and the common one — assert **one input `uid` survives**, the other ceases to be live, and **no third `uid` is minted**. **Negative:** attempt `consolidate` on two records at **different** canonical addresses and assert **refusal** — that is a coreference question and `consolidate` must not answer it. **Negative, and it is W8b's first arm:** one `uid` under two **different** canonical addresses is **corruption**; assert `consolidate` is not offered, refusing on the one-address precondition rather than on a corruption check. **Negative:** assert no `deprecated_ids` entry is created, since no address retired |
| **W4** | *(rewritten)* A coreference claim is attributed and additive, and never collapses the graph | Assert no operation retires an address on coreference grounds. Its equal-basis consolidation arm moves to **W16**; its distinct-basis retraction refusal moves to **W15**'s cycle arm; its lineage-divergence arm — *"both survive, no field-selection path offers a choice, the dataset becomes `lineage-divergent`"* — moves to **W16**, where the union rule now carries it |
| **W6** | *(rewritten)* Three resolution states never collapse | `not-present`, `unknown`, `resolved` remain distinct; `ambiguous` is no longer among them. **Negative:** assert removing a corpus does not convert its ids to `unknown` — unchanged |
| **W9** | *(rewritten)* An ambiguous **search term** refuses and names its candidates | Search a term the pinned snapshot maps to two identifiers; assert refusal listing both, and that **no binding was written**. **Negative:** assert the ambiguity is a property of the **pinned snapshot**, reproducible across installations holding that snapshot — not of accumulated authoring |

---

## 10. Limitations

1. **An eleventh kernel kind is spent.** Adding a kind is a cross-corpus
   amendment — the same cost F8 records for removing one. Priced at §8 and judged
   worth paying only because all three cheaper realizations (§5.1) are larger
   changes in disguise.
2. **Two addresses persist for one work, permanently.** There is no longer an
   operation that reduces them. Query-layer searches expand over **`active`**
   coreference closure, refuse over an **`indeterminate`** edge (§5.5), and the
   underlying records never merge.
3. **Attester reliability is unmeasured.** Unit weight is the honest default, not
   a finding that attesters are equally reliable. The `meta/` data collection that
   would inform per-source priors does not exist and is not opened here. Until it
   does, a coordinated set of low-quality attestations outweighs a single careful
   one, and nothing detects that.
4. **`consolidate` selects continuity.** Where two copies disagree on content it
   reconciles, and where they carry distinct `uid`s it selects one. Both are
   judgements recorded rather than derived — the same standing merge had,
   narrowed to storage repair. Nothing computable says which of two opaque
   continuity anchors is the right survivor.
5. **The pinned authority snapshot is a new dependency with no design.** Which
   authorities are accepted, how a snapshot is pinned, versioned, distributed and
   bumped, and whether a bump is an amendment act — none of that is ruled here.
   §4.2 states the discipline; the artifact is owed.
6. **A claim about a release is not expressible** (§6). Accepted.
7. **A coreference balance is bounded by coverage, so two epochs can disagree**
   (§5.5). This is the producers map's property without the belief consequence:
   the disagreement moves no digest, but a reader who does not look at the
   coverage declaration will read one epoch's `inactive` as a settled fact. The
   `indeterminate` state and its refusal are what keep the *unestablished* case
   honest; they do nothing about a narrower coverage that is established and
   simply smaller.
8. **The coreference map is real work the alias map's retirement does not pay
   for.** The count is unchanged; the build is not. Its reduction rule, its
   derivation receipt and its place in the build's coherent enumeration are
   **designed** — packaging §5, §7, X9, X10 and X12 carry them on the
   retraction-map contract, amended in this ruling's commit — and **unimplemented**,
   like every other X row. What is *not* designed is the reduction rule's own
   fixture set, which arrives with the first contract cut (**N1**) as every
   enumeration rule's does.

---

## 11. Open questions

1. **Which authorities are accepted, and who decides.** Limitation 5's artifact.
   The vocabulary-admission design (2026-08-07) is the nearest precedent and may
   be the right home rather than a new document.
2. **Does a coreference balance belong in any audit?** It is outside belief by
   §5.3, but an active edge with balance `1` and a contested history is a
   different epistemic object from one with balance `12` and none. Nothing
   currently surfaces the difference.
3. **The `meta/` reliability programme.** Collecting attester-agreement data is a
   research question the system should be able to answer about itself, and
   `instrument-certification` is the adjacent mechanism. Not opened.
4. **F10**, returned to the docket (§7).
