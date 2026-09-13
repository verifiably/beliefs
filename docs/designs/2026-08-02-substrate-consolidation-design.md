# Substrate consolidation — design

**Date:** 2026-08-02
**Status:** design, approved in session
**Scope:** sub-problem 2 of 7 in the system redesign
**Depends on:** [`2026-08-02-epistemic-kernel-design.md`](2026-08-02-epistemic-kernel-design.md)

## 1. Why

The kernel design left three contracts open, and each turned out to be a question
about what the substrate can express rather than about epistemics:

- the **empirical-observation facet** and its eligibility predicate,
- **semantic-identity immutability** for propositions,
- **lineage-derived independence**.

This document answers those three, and fixes the boundary between Science,
`nodes` (the logical entity/relation kernel) and `atoms` (the durable
atomic filesystem effect engine).

### 1.1 The layering is articulated and entirely unwired

```
domain profile     science                    ← 151,645 LOC, 595 modules
logical substrate  nodes   (Node, Relation, shapes, indexes)
physical substrate atoms   (durable atomic filesystem effects)
```

Both `nodes` and `atoms` name Science as their consumer in their own
architecture docs. Measured state:

- `science` imports neither.
- **`nodes` does not reference `atoms` either** — its dependencies are `pydantic`
  and `pyyaml`.
- **`atoms` can execute certified effects.** A7 landed 2026-08-14 with the chain
  and effect/recovery executor; A8 landed 2026-08-17 with physical certification
  and an exact production allowlist. Science has not adopted it at the composition
  root.

So adopting `nodes` buys **no durability today**, and `nodes` §7 leaves the hole
explicitly: *"Single-writer assumption. Nothing coordinates concurrent mutation of
one corpus."* That is the seam `atoms` exists to fill, and neither end is
connected.

## 2. The boundary ruling — split by nature

| Gap | Owner | Reason |
|---|---|---|
| (a) cross-node eligibility predicate | **Science** | scientific policy over multiple kernel kinds |
| (b) semantic immutability | **Science** | proposition-specific revision semantics |
| (c) relation closure | ~~**`nodes`**~~ → **Science's world layer** | **withdrawn** (§3): both consumers turned out to be world-crossing, and one of them no longer walks relations at all |
| durability / concurrency | **`atoms`, later** | neither `nodes` nor Science invents a temporary transaction engine |

The rejected alternatives, recorded so they are not re-proposed:

- **Science owns all three** — duplicates a general graph primitive and risks
  Python/TypeScript divergence.
- **`nodes` owns all three** — contaminates a structural kernel with scientific
  policy, and *still* cannot enforce history against hand edits.
- **Defer-and-promote** — a sound general rule, and the one this design should have
  applied to (c). The argument against it was that relation closure "has already
  proven general through the existing membership analogue", which is a claim about
  the *shape* of the operation and says nothing about where its callers live. §3
  records what that cost.

Every addition to `nodes` costs a Python implementation, a TypeScript
implementation, conformance fixtures, and a `STANDARD.md` version bump. That cost
is the reason the line sits where it does — and it is the reason (c) comes back out
once its callers are known.

## 3. Gap (c) — relation closure, withdrawn from `nodes`

> **Amended by sub-problem 4 round 19.** These two operations were specified for
> `nodes` and are **not added there**. Both stated consumers moved out from under
> them, and the operations cannot serve either one where it now lives:
>
> - **`derived_from` closure for independence** no longer walks relations at all.
>   Sub-problem 4 §5.2 makes lineage a **facet** — the stamped lineage basis — so a
>   primitive whose contract is defined over stored `Relation` objects cannot reach
>   it. §5 below said in as many words "walk the basis via `transitive_outbound`",
>   which was unimplementable against the signature two sections above it.
> - **`supersedes` chains** are relations, but world §5 requires them to cross
>   corpora, and these operations are **corpus-local**: to corpus A, a relation
>   targeting a node in corpus B is dangling, and `dangling-skipping` would silently
>   truncate the chain.
>
> So the primitive had **no caller it could serve end to end**, and §2's own pricing
> argument — a Python implementation, a TypeScript implementation, conformance
> fixtures and a `STANDARD.md` bump per addition — is decisive against paying for it.
> This is what "defer and promote" existed to prevent, and the argument that
> overrode it reasoned about the operation's *generality* rather than its *callers'
> location*. A primitive is justified by who can call it, not by how clean it looks.
>
> **What survives is the contract, relocated and split.** Science's world layer
> performs both closures with **one algorithm over two adjacency adapters**, above
> `nodes`' existing **one-hop** `outbound()` / `inbound()` plus the world resolver.
> Every behavioural semantic survives, including start-exclusion, which substrate §5
> step 1 depends on. What does *not* survive is the claim that one *edge* contract
> covers both callers: `supersedes` has a predicate and a `directed` flag, a lineage
> step has neither, and a contract stating clauses that are category errors for half
> its callers is one contract in name only.

**One algorithm, two adjacency adapters.** The relocated traversal serves two callers
whose *edges* have nothing in common — `supersedes` is a stored `Relation` with a
predicate and a `directed` flag; a lineage step is a **facet** with neither — so a
single contract covering both would have to state clauses that are meaningless for
half its callers. What they share is the **walk**, and that is where the sharing stops:

```text
closure(start, adjacency) -> { reached: [live id], unresolved: [step] }

adjacency := relation_adjacency(predicate, direction)   # supersedes, and any relation
           | lineage_adjacency                          # the stamped basis, sub-problem 4 §5.2
```

**The result is structured, and the previous revision's `[live id]` could not satisfy
its own contract.** The algorithm promises to *report* a step whose target does not
resolve, and §5's step 2 must tell an absent **ancestor** from an absent **producing
run** — none of which survives a return type carrying only the ids that did resolve.
The old paragraph justifying the narrow shape said the caller could recover the
information from `dangling()`, and that argument had two premises, both now false: it
was written for a **kernel** primitive, and `dangling()` is **relations-only**, so it
cannot see a facet-valued lineage reference at all. For the lineage adapter there is no
second source of truth, so the traversal is the only place the information exists.

`unresolved` carries the step as the adapter saw it, and every entry names **where it
was stored**:

| adapter | entry |
|---|---|
| relation | the **source node's live id**, the **position** of the relation in that node's stored list, the predicate, and the unresolved target |
| lineage | the **dataset**, the route, and **which position** in the route failed |

**The relation entry's first two components were missing**, and the previous revision
carried `(predicate, target)` alone. That shape cannot say *whose* edge dangled: `X
─cites→ M` and `Y ─cites→ M` produce one identical entry, so a finding has no source ref
to report, two defects deduplicate into one, and the ordering has no tie-break — three
consequences of a single omission. Entries are ordered by `(source id, position)` for
the relation adapter and by `(dataset, route, position)` for the lineage adapter, both
total, because a stored position is unique within its node. The lineage shape already
named its dataset, which is why the asymmetry was easy to miss: one adapter had been
given the attribution rule and the other had not.

Callers that do not care read `reached` and ignore it; §5 is not one of them.

The **algorithm's** contract, matching membership traversal (`STANDARD.md` §7) so there
is one traversal behaviour rather than two:

- cycle-safe
- uid-deduplicated
- start-excluding (even when a cycle makes the start reachable from itself)
- skips a step whose target does not resolve and **returns it in `unresolved`** rather
  than raising — at the world layer, "does not resolve" means unresolvable **in the
  world**, not merely outside the starting corpus, which is the whole reason the
  traversal moved
- returns `reached` as sorted live ids (Unicode code-point order), and `unresolved`
  sorted by the adapter's own key above — `(source id, position)` or
  `(dataset, route, position)` — both of which are total, so the order is determined
  rather than left to insertion
- raises `RefError` only when the *input* ref does not resolve

The **relation adapter's** semantics, which must be pinned because leaving them to
implementation guarantees Python/TypeScript divergence:

- **Predicate matching is exact string equality.** `predicate` is "a free string
  — never enforced by the kernel" (§2.2); no prefixing, namespacing, or hierarchy
  is introduced by the closure.
- **`directed` is not reinterpreted.** The adapter repeatedly applies `nodes`'
  existing one-hop semantics: the outbound direction follows source-position
  relations, the inbound direction target-position ones, exactly as `outbound` /
  `inbound` already do. An undirected relation (`directed: false`) is therefore
  followed in its **stored** orientation only. Making closure the one operation
  that walks undirected edges both ways would give two different readings of
  `directed` — the closure's and `outbound`'s.
- Unresolvable targets are surfaced by `dangling()` / `Corpus.check` at the corpus
  layer and by the world-aware check above it.

The **lineage adapter's** semantics, which the clauses above do not touch:

- The step is the stamped **lineage basis**, read as node content. There is no
  predicate to match and no `directed` to honour, and asking for either is a category
  error rather than a default.
- The basis is **tagged** (sub-problem 4 §5.2): `single(route)` yields that route's
  ancestor refs; `conflict([route])` yields **every** route's refs, all resolved for
  reporting, and certifies nothing.
- A basis entry that does not resolve is reported per §5's step 2, which distinguishes
  an absent **ancestor** from an absent **producing run** — a distinction the relation
  adapter has no vocabulary for.

**Two fixtures, not one.** The relation fixture covers a chain, a diamond, a cycle, an
unrelated predicate, a deprecated ref, a dangling target, and an **undirected
relation** — the last asserting it is reached from its stored source and *not* from its
stored target. The lineage fixture covers a chain, a diamond, a cycle, a `single` basis,
a `conflict` basis, an unresolvable ancestor and an unresolvable producing run. Both add
a chain **crossing corpora**, asserting the full closure rather than truncation at the
corpus edge. A previous revision folded these into one shared fixture, which would have
asserted predicate and `directed` behaviour against edges that have neither.

**The narrow return shape is retired**, and its reasoning is worth keeping as a
correction rather than deleting. It read: widening would complicate a clean primitive
for one caller's benefit, and `nodes` already exposes unresolved targets through
`outbound()` / `dangling()`. Both halves were true of a **kernel relation** primitive
and neither survived the move. The traversal is no longer in the kernel, so "keep the
primitive clean" is an argument about a thing that no longer exists; and `dangling()`
is relations-only, so for a facet-valued lineage step the alternative source of truth
was never there. A contract that *promises* to report something must **return** it —
the policy still lives in Science (§5), but the evidence has to reach it.

## 4. Gap (b) — semantic identity, in Science

### 4.1 Why `nodes` cannot do it

A per-node invariant can assert `stored_hash == hash(current fields)`. That passes
when both are edited together. Immutability *across time* requires prior state,
and `nodes` retains none — `version` is a bare integer with no history and no
revision store.

**And the obvious shortcut is a trap.** Making the semantic hash the node id would
turn a semantic change into a `rename` — but §3 specifies that rename "rewrites
every position holding `old_id` — in the renamed node and in every referrer."
Rename preserves reference integrity *by retargeting*, which is precisely what the
kernel forbids. `nodes.rename` must never be used on a proposition for a semantic
change.

### 4.2 The rule

Semantic changes pass through **Science's write API**, which compares against the
persisted proposition:

| comparison | action |
|---|---|
| same semantic identity | ordinary non-semantic update |
| changed semantic identity | **mint a new proposition** + `supersedes` edge to the old |

Non-semantic markdown — body prose, formatting, `title`, and the authored
`display_statement` — remains hand-editable. Only the semantic fields are
governed, and the kernel design §4.1 moves the claim itself out of prose
entirely: today `title` *is* the statement, hand-editable and author-owned, so
"title remains hand-editable" and "the claim is immutable" cannot both hold
without that split. *(Amended 2026-08-05, formal model ρA1/ρA2: kernel §4.1
first split the claim into a canonical `statement` field; it now carries the
claim as a **typed projection** and keeps no identity-bearing prose field at all,
so the governed set is the typed fields and the hand-editable set is every prose
field.)*

### 4.2.1 Which writers are trusted — a rule, not a migration finding

Left open, this decays into per-caller judgement calls, and a single writer
classified as trusted because migrating it was inconvenient reopens the hole.

> **Rule.** Every **Science-owned canonical writer** MUST write through the API —
> the annotation pipeline, entity creation, promotion, and agent-authored edits
> alike. Every other write — manual file edits, third-party tools, external
> repos — is an **untrusted import**, subject to the §4.3 stale-hash check on
> read and to the §6.2 corpus check.

Trust follows from *what a writer is*, not from what it costs to migrate. The
implementation plan inventories the callers and sequences their migration; it
does not get to reclassify one.

**Enforced as a capability boundary, not a scan.** "Discover the writers and
check them" is a roster wearing a predicate's clothes — a new writer reaching the
filesystem through an unrecognized primitive is simply not discovered, and the
scan reports clean. The enforceable statement is about *who holds the handle*:

> The write API is the **only** holder of a mutable corpus handle. Every other
> module receives a read-only view. Constructing or receiving a mutable `Corpus`
> outside that module is a static violation.

This is checkable by AST, and it is complete over the paths that go through
`nodes` at all — which is the whole of Science's own code, since Science does not
otherwise know the on-disk format.

**What it does not cover, stated rather than papered over:** a module that
bypasses `nodes` entirely and writes bytes to a corpus path with a raw
filesystem call. Nothing static distinguishes that from writing any other file.
Such a write is an untrusted import **by definition**, and it is **subject to**
§4.3's stale-hash rejection and §6.2's corpus check — which is not the same as
being caught. A raw write that produces a *valid* node passes both: the hash
agrees with the fields because the writer computed it, and the corpus check finds
nothing structurally wrong, because nothing is. That is the **recorded-history
completeness** limitation (§4.3, kernel §8.7) reappearing at the write boundary
rather than a second hole — the system compares a state against itself and has no
record of what preceded it.

S8 is bounded to the capability, and its negative test says so.

### 4.3 The bound, stated not patched

A direct edit to semantic fields on disk is an **untrusted import**, not a
guaranteed mutation. Science can detect a *stale* hash (stored ≠ computed) and
reject the node. It **cannot** detect an edit that changes the fields and the
stored hash together.

That is one consequence of the **recorded-history completeness** limitation named
in the kernel design §8.7, alongside G4 and G8 — one missing substrate capability,
three consequences. Its eventual owner is `atoms`, under a contract stricter than
crash recovery: **pre-mutation durable registration and detectable journal
removal**. A recovery journal that can itself be deleted is not tamper evidence.

## 5. Lineage and independence certification, in Science

**Orientation is fixed:**

```text
descendant ──derived_from──▶ ancestor
```

This is load-bearing, not stylistic: with the claim on the descendant, deleting an
ancestor leaves a **detectable dangling reference** on the surviving node. The
reverse orientation would make ancestor deletion invisible.

> **Amended by sub-problem 4 §5.2 — the orientation survives, its carrier does
> not.** `derived_from` is no longer a stored edge: it is a **view** over the runs'
> `produces ∘ transforms`, which removes the last authored route to ancestry. A view
> has nothing on disk to go stale, and that is a loss as well as a gain — deleting
> the **producing run** removes both composed edges at once, so the descendant
> resolves to no ancestry at all and reads as a **root**, which is the one direction
> this section must never fail in. What is durable instead is the **lineage basis**
> stamped on the produced dataset by the boundary: the producing run ref and the
> sorted content identities of its `transforms` inputs, minted with the dataset and
> not editable through any ordinary API. The basis is a descendant-side record, so the
> argument above holds word for word with "edge" replaced by "basis entry"; the walk
> below reads the **basis**, and the view is descriptive only.
>
> **The basis is tagged** — `single(route) | conflict([route], ≥2, sorted)`. The
> boundary mints only `single`; `conflict` arises solely from **`consolidate`** of two
> records at one content address whose routes disagree *(the operation was world §4.3's
> merge, retired 2026-08-08; the equal-basis arm it names is now `consolidate` —
> `2026-08-08-world-address-ruling.md` §5.4)*.
>
> **Independence reads the basis, not the view**, because the view unions every
> producing run while the durable record attests **one** route for a boundary-minted
> dataset — so a route the view supplied could be deleted without dangling anything,
> and the deletion would *buy* independence. A producing run whose inputs differ from a
> `single` basis is instead a **divergent derivation** and forces `not-certified`;
> sub-problem 4 §5.2 carries the argument and §11.14 the residue.

**Procedure.** For each `observes` dataset of the assessments being compared, walk
the **lineage basis** transitively **at the world layer** under §3's contract — each
ancestor's own basis supplying the next step, resolved through the world resolver over
`nodes`' one-hop operations. Not `transitive_outbound`: an earlier revision of this
section named it, and that primitive is defined over stored `Relation` objects while
the basis is a **facet**, so the walk it prescribed could not be written. §3 records
the withdrawal. Then:

1. **The inspected set is `{observed root} ∪ closure`** — the root included
   explicitly, because §3's traversal is **start-excluding**. A root whose *own*
   ancestor has been deleted reaches nothing: the closure is empty, and inspecting
   only "reached datasets" would inspect nothing and certify a dataset whose
   immediate parent is gone. The most direct form of the failure this rule exists to
   catch is the one that escapes it.
2. If any dataset **in the inspected set** carries a `conflict` basis → emit
   `lineage-divergent` and issue **no independence certificate**. This is decided on
   the **tag alone**, before any comparison: a `conflict` records two derivations of
   one content identity that the system has no rule for choosing between, which is the
   condition step 3 exists to detect, already established. Every route is still
   **resolved**, so step 2b can report what is missing as well as what disagrees, but
   nothing about the outcome depends on the result.
2b. If any dataset **in the inspected set** carries a **basis entry that does not
   resolve** — an absent ancestor, *or* an absent producing run, in **any** route —
   **or** the lineage contains a cycle → emit `lineage-incomplete` and issue **no
   independence certificate**. A basis entry naming a deleted run is the case a
   purely derived view cannot see, and it is why the basis is stored.
3. If any dataset **in the inspected set** carries a `single(route)` basis and has a
   producing run whose `transforms` inputs differ from that route → emit
   `lineage-divergent` and issue **no independence certificate**. This is the route the
   basis cannot carry, refused rather than assumed either way. The comparison is
   defined **only** against `single`: "differs from the basis" has no meaning against a
   set of routes, and an earlier revision of this section stated it as though it did.
4. Only **complete, undiverged, disjoint** ancestor closures certify independence.

**A `conflict` short-circuits, and that ordering is deliberate.** Placing it before the
resolution and comparison steps keeps every later rule defined over a `single` route,
which is the only shape they were ever written for. It also means a conflicted dataset
is refused for the reason it actually has — two irreconcilable derivations — rather than
for whichever downstream check happened to trip on a set where a tuple was expected.

**A resolvable basis whose run is gone is still incomplete**, even when some *other*
surviving run produces the same dataset by another route. The basis attests one
derivation; a second producer is a different derivation of identical bytes, not
evidence that the first one's inputs are still known. Reading it as a substitute
would let the deletion of the route an assessment actually used be repaired by an
unrelated route's existence. The failure direction is the same one this whole
section takes: uncertified costs corroboration.

**Step 3 is undetectable once its evidence is gone, and that is a limit rather than a
mechanism.** A divergent producer is a node like any other, and no surviving node holds
a reference to it — recording one on the dataset would mean appending to a node that
may be immutable or foreign, which is what sub-problem 4 §5.2 declined. So deleting the
divergent run *restores* the certificate, and afterwards the corpus is
**indistinguishable from one in which that run never existed**.

A previous revision called that "change detection, not loss detection", which
overclaimed by one step: belief is a **computed view** (kernel §6), so no prior digest
is durably retained anywhere for the new one to differ *from*. G3 guarantees that two
**available** states hash differently; it retains neither. This is therefore the same
undetectable-history limit as G4 and G8's deletion negatives — §4.3's recorded-history
limitation reaching the one place the descendant-side trick cannot — and closing it
needs §4.3's owner, not a stronger sentence here.

**Three states, and the third is the point:**

| state | meaning |
|---|---|
| `independent` | complete closures demonstrated disjoint |
| `shared-source` | common ancestry **demonstrated** |
| `not-certified` | independence **not demonstrated** — computed, never authored |

`not-certified` is **not** a synonym for `shared-source`. Labelling an incomplete
closure "shared-source" would assert demonstrated common ancestry from an absence
of information — the unknown-as-verdict error the kernel exists to remove.

In aggregation, the distinction costs nothing to carry: the kernel §4.2.1
dependency graph draws an edge for every pair that is not certified
`independent`, so `shared-source` and `not-certified` are equally non-corroborating
without either being restated as the other. The two states differ in what a
curator can act on — a demonstrated shared source is a fact about the data, an
uncertified pair is a gap in the lineage that may still be closable.

### 5.1 Test split

| layer | test |
|---|---|
| world layer | an unresolvable step is skipped by the closure and **returned in `unresolved`**, with a relation step naming its **source id and stored position** as well as its predicate and target, and a lineage step naming its dataset, route and failing position. **Attribution:** give **two** nodes a dangling relation under **one** predicate to **one** target; assert **two** entries distinguished by source id, that neither is deduplicated away, and that the order is determined by `(source id, position)` rather than by traversal order. **Negative:** assert `dangling()` alone cannot recover the lineage case, which is why the return shape carries it |
| Science | a **`conflict`** basis yields `lineage-divergent` on the **tag alone** (step 2), before resolution or comparison; assert every route is still resolved for reporting, and that no producer comparison is attempted against it |
| Science | deleting an **ancestor named by a basis** changes the lineage snapshot, invalidates independence certification, changes `belief_input_digest`, and **cannot increase belief strength** — the guarantee holds because the basis is a durable record on the surviving descendant, and it is scoped to that case |
| Science | deleting a **divergent producer** (step 3) **restores** the certificate and **can** increase belief strength; assert the resulting state is indistinguishable from one where that run never existed. The negative half of the row above, and it must be asserted rather than implied — a deletion guarantee stated without its scope will be read as the absolute claim an earlier draft made here |
| Science | **deleting the observed root's immediate parent** — the closure is empty and the root itself carries the dangling edge — still yields `lineage-incomplete` (pins step 1) |

The Science tests are the ones that matter, and what they assert together is narrower
than an earlier summary claimed. **Deleting anything a basis names** — an ancestor at
any depth, including depth one, or the producing run itself — can only cost belief,
because the surviving descendant still holds the reference and the loss is visible.
**Deleting a divergent producer can buy belief**, because nothing holds a reference to
it; that is the row above and §11.14 there, not an exception to be read past. The
sentence that stood here said the tests prove deletion can never buy belief, which
contradicts the row printed directly above it — a summary written before step 3 existed
and left in place when its own table stopped supporting it.

## 6. Gap (a) — cross-node eligibility, in Science

### 6.1 Why `nodes` cannot do it

`validate(node)` runs invariants on **one node** (§6). The eligibility predicate
spans four: assessment → run → `observes` → dataset → facet. `Corpus.check` is
corpus-wide but its code list is **closed** — seven structural codes — and a kind
invariant surfaces only as `invariant-violated` with `detail: ""`, because
"invariants are opaque callables and cannot be attributed to a facet."

The **facet itself is native** to `nodes`: an optional `empirical-observation`
facet on the `dataset` kind, with a payload schema rejecting unknown keys (§2.3).
Only the cross-node predicate is Science's.

**Corrected 2026-08-04** (`2026-08-04-domain-extension-boundary-design.md` §3.4):
the facet is **not** native to `nodes`; it belongs to the **`science` base
profile**, and the payload schema travels with it. The placement above
contradicted this document's own governing argument — §2's rule that scientific
policy in a structural kernel "contaminates" it. Two independent reasons settle
it: `dataset` is itself a Science kernel kind (kernel §4.2), and
acquisition-boundary semantics are scientific policy whose honesty is explicitly
outside the guarantee (kernel limitation 8). Nothing about the facet is
structural. The cross-node predicate remains Science's, as stated; what changes
is that the facet is Science's too, so §6.1's argument now reads without an
exception.

### 6.2 Enforcement — both boundaries

1. **Write boundary** — Science's write API refuses to create an inadmissible
   `assesses` edge.
2. **Profile-level corpus check** — because files are canonical and hand-editable,
   a node can bypass the write boundary. This mirrors `nodes` §8's own reasoning
   for providing a reporting check at all.

**Reuse the envelope, not the codes.** Science findings adopt `nodes`' finding
contract — `{severity, code, ref, detail, message}`, normative ordering by
`(ref, code, detail)`, `message` explicitly non-normative and never used for
ordering or parity — with a **Science-owned code namespace**
(`lineage-incomplete`, `eligibility-unmet`, `semantic-hash-stale`, …).

**No generic predicate-plugin framework is added to `nodes`.**

That envelope is also the answer to a standing complaint: `fb-2026-08-01-006`
reports one unreadable task store surfacing as ~16 peer errors, 15 of them "check
could not run" — a report that looks like sixteen problems and conceals that most
validation was disabled. A normative severity/code/ordering contract with a
non-normative message is what makes that distinction expressible.

## 7. Durability — deferred to composition-root adoption

`atoms` owns durability and concurrency. A8 certified a production configuration
on 2026-08-17. Until Science adopts the composition root:

- the profile claims **single-writer operation** and **no crash-safe multi-file
  durability**, matching `nodes` §7 and §13 exactly;
- **no interim Science transaction layer is built.** A temporary engine would be
  machinery destined for deletion, which is the failure mode this redesign exists
  to end.

`nodes`' current write path is a **validation** boundary, not a durability one:
§7 `add` guarantees "any failure MUST precede the disk write" for one file, and §3
rename prepares rewrites in memory then commits write-new-then-delete-old. That is
best-effort ordering, not journaling.

## 8. Scale — an adoption gate, not a backend decision

`nodes` §13 targets "personal-corpus scale (order of 10⁴–10⁵ nodes), not bulk
graph workloads," with in-memory indexes and brute-force cosine.

Measured markdown files (a **proxy** for node count, not node count):

| corpus | files |
|---|---|
| mm30 | 10,647 |
| health | 2,799 |
| science-commons | 416 |
| meta | 343 |

Roughly 14–15k aggregate. **That is inside the stated range, not beyond it**, and
no current measurement establishes a capacity failure.

**Ruling:** representative-world benchmarks are an **adoption gate** — run them,
publish the numbers, and re-check when sub-problem 3 aggregates corpora into one
world. Do **not** build a different backend until measurements show the current
one failing. Building for a projected ceiling that measurement has not
demonstrated is how the present system acquired its alternatives.

## 9. What Science stops owning

The candidate replacement surface, measured:

| Science module(s) | lines | replaced by |
|---|---|---|
| `entities.py` | 1,923 | `nodes` Node / Corpus |
| `graph/store/` (15 submodules) | 4,764 | `nodes` Corpus + indexes (partly; belief stays) |
| `model/` frontmatter, identity, ids, entities | 1,930 | `nodes` §4 format + §3 identity |
| `entity_identity`, `entity_scan`, `entity_kinds`, `entity_profiles`, `addressing`, `entity_reservation`, `entity_migrations` | 874 | `nodes` registry + id grammar |

≈ **9,500 lines** of directly-overlapping surface, before counting their tests.
This is a scoping estimate for the implementation plan, not a promise: belief,
policy, and the domain profile itself stay in Science, and some of `graph/store/`
is belief machinery rather than storage.

## 10. Guarantees and tests

| # | Guarantee | Layer | Test |
|---|---|---|---|
| **S1** | Relation closure matches membership-traversal semantics, and does not reinterpret `directed` | **Science's world layer** (§3, withdrawn from `nodes`) | the **relation** fixture: chain, diamond, cycle, unrelated predicate, deprecated ref, dangling target, and an **undirected relation** reached from its stored source but not its stored target — plus a chain **crossing corpora**, asserting the full closure rather than truncation at the corpus edge. **Negative:** assert `nodes` exposes **no** transitive operation, so the contract has one implementation rather than a kernel one that no caller can reach |
| **S1a** | The lineage closure walks a facet, and shares the algorithm rather than the edge semantics | Science's world layer | the **lineage** fixture: chain, diamond, cycle, cross-corpus chain, a `single` basis, a `conflict` basis yielding **every** route and certifying nothing, an unresolvable **ancestor**, and an unresolvable **producing run** — the last two distinguished, which the relation adapter cannot express. **Negative:** assert the lineage adapter accepts **no** predicate and **no** direction argument, so the relation clauses cannot be applied to it by default; and assert one algorithm serves both, so cycle-safety and start-exclusion are certified once |
| **S2** | A semantic edit through the write API mints a new proposition | Science | edit scope via API; assert new node, `supersedes` edge, prior refs unmoved |
| **S3** | A stale semantic hash is rejected on import | Science | hand-edit fields only; assert refusal. **Negative:** edit fields *and* hash; assert it passes undetected, pinning §4.3 |
| **S4** | `nodes.rename` is never used for a semantic change | Science | assert no rename path is reachable from the semantic-change branch |
| **S5** | Incomplete lineage never certifies independence, and the deletion guarantee is scoped | Science | delete an **ancestor named by a basis**; assert `lineage-incomplete`, `not-certified`, changed `belief_input_digest`, and no belief increase. **Negative:** delete a **divergent producer** (step 3) and assert the certificate is **restored**, belief **can** increase, and the state is indistinguishable from one where that run never existed — the absolute form of this row was written before step 3 existed |
| **S6** | Only certified independence confers multiplicity | Science | the kernel §4.2.1 dependency graph: (a) the `A={x}, B={x,y}, C={y}` case — assert multiplicity **2**, i.e. neither a partition nor components; (b) B disagreeing with A and C still **contests**, so non-selection is not exclusion; (c) an assessment certified independent of nothing raises neither multiplicity nor displacement when **added** — addition only, since deletion falls under §3.2; (d) **clique** — every singleton is maximum, so assert the added vertex may be selected yet displacement still cannot rise; (e) **non-amplification** — duplicate a dependent contrary assessment N times and assert the **epistemic output** is identical while `belief_input_digest` **changes**, since the added nodes are inputs (a byte-identical belief record would contradict G3); (f) the `A={x1,x2}, C={y1,y2}` vs `B={x1,y1}, D={x2,y2}` case — two independent objections contest twice, both candidate selections land at the prior, and the uid tie-break does **not** decide the sign; (g) contestation on a neutral result, and one that would cross the prior, both clamp; (h) **regression** — supports `A={x}`, `C={y}` with a strong dispute `B={x,y}`, then add a weak universal dispute `D={x,y}`: assert contestation still resolves to `B`, so belief does not rise (the contrary selection inherits the outer objective, not its own). **Amended 2026-08-05 (belief-policy §3.3): this arm is a named acceptance condition for the first successor policy admitting unequal weights, and is not assertable against `science.belief.v1`**, whose unit weight makes `B` and `D` interchangeable so the case cannot be constructed. It is recorded as a forward obligation rather than run vacuously, since an oracle that cannot be sabotaged and fail does not meet N2; what binds v1 today is belief-policy **P5**, which asserts unequal weights are **unspellable** |
| **S7** | Eligibility is enforced at both boundaries | Science | write a file directly that **violates eligibility** (an `assesses` edge whose run has no `observes` input); assert the corpus check reports `eligibility-unmet`. A raw write producing a *valid* node is intentionally unreported — that is §4.2.1's stated bound, not a gap in S7 |
| **S8** | Only the write API holds a mutable corpus handle (§4.2.1) | Science | static: assert no module outside the write API constructs or receives a mutable `Corpus`. **Negative:** write a corpus file with a raw filesystem call and assert S8 does *not* fire — the limit is pinned, and §4.3 + §6.2 then **validate** it, subject to the recorded-history limitation |
| **S9** | An audit judges a damaged corpus rather than refusing it — construction faults are findings, the remainder is audited, and no state identity is claimed *(added 2026-09-13, world resolution slice 3 §7)* | Science | damage a covered corpus one way at a time — an unparsable file, a misplaced file, two files sharing a `uid`, two files claiming one id — and assert the world audit reports the matching construction finding (`parse-error`, `path-mismatch`, `uid-collision`, `id-collision`), audits the remainder, records `corpus-damaged`, makes no drift comparison, and that every read of a mapped address in that corpus refuses with `CorpusDamaged`; assert the receipt evaluator answers `unresolvable` for a receipt naming it. **Negative:** the default open still refuses with `CorpusStateMalformed`; a state identity is never computed over a collected remainder |

S3's negative half follows the G4/G8 pattern: the limit is asserted, so it cannot
be read as the strong claim.

## 11. Limitations

1. **No Science durability until composition-root adoption.**
   Single-writer, no crash-safe multi-file commit. Stated, not mitigated.
2. **Recorded-history completeness** (kernel §8.7) — a coordinated
   fields-plus-hash edit is undetectable.
3. **Scale is unbenchmarked.** The range is stated by `nodes` and the corpora are
   inside it; neither fact is a measurement of this workload.
4. **TypeScript parity is a standing cost** on anything pushed into `nodes`. Only
   §3's two operations are proposed, deliberately.

## 12. Open questions

- **Where the profile lives.** `nodes` expects domain profiles in downstream
  repos; whether the Science profile is a package inside `science/` or its own
  distribution affects how `science-commons` and external consumers pin it.
- ~~**Registry vs `KIND_DESCRIPTORS`.**~~ **CLOSED 2026-08-04**
  (`2026-08-04-domain-extension-boundary-design.md` §6) — and closed by
  **retiring the descriptors**, not by choosing a direction: picking a winner
  leaves the loser as a derived duplicate that can drift, which is the defect
  itself. The declarative contracts — the `science` base contract plus the
  activated domain contracts — are the **normative SSOT**; `ProfileSpec` is the
  **sole compiled runtime profile**; `KindSpec` is a further compiled product.
  `KIND_DESCRIPTORS` gains no successor, and under the clean-start ruling
  (ledger §0) it is not carried over, so nothing is deprecated and no
  compatibility layer appears. Note the pricing consequence: because
  contributions merge *upstream* of `Registry.register()`, `nodes` gains
  nothing — a zero runtime and contract delta, with one added parity fixture.
- ~~**`atoms` consumption order.**~~ **CLOSED 2026-08-14.** Science's Python
  composition root combines `nodes` and `atoms`; portable `nodes` does not
  depend on the Python-only, filesystem-specific engine. `atoms` authority
  §12.2 and the adoption ledger artifact 4 own that route. A7 supplies the
  transaction interface and A8 supplies the certified production tuple;
  composition-root adoption remains the production gate.
