# Composite claims — the kind that places kernel §11's `inquiry`, `patch-definition` and `structural-chain`

**Status:** design, drafted 2026-09-12; under review, not frozen. Task
`beliefs-4bcf88` carries this spec. Implements nothing yet: the roadmap's
concurrency rule 6 keeps at most two kernel lanes open while the success
criterion is unmet, and this design is off the path (§11). It is written now
for the same reason the estimand-typing design was: it adds a world kind and
a relation signature to the base contract, and the contract cut freezes after
the last oracle-amending lane merges. Deciding the shape before that freeze
costs one design; deciding after it costs a successor contract.

**Answers.** Kernel §11's first open question — whether `inquiry`,
`patch-definition` and `structural-chain` are "one kernel-adjacent
model/patch kind or a view over the kernel" — and kernel §4.4's *open,
unplaced deliberately* row for those three. The models assessment of
2026-09-12 named a "model as structure" as the one sense of *model* that
belongs in `beliefs`; this is its design. **Leaves.** `search` (kernel §11,
the coverage record); the non-empirical route (kernel §11); the eleven K
records and the higher-order moratorium (cut 1 §2.4); estimand typing
(`2026-09-12-estimand-typing-design.md`, on the `design/estimand-typing`
branch), which this design reads but does not amend.

**Amends when it lands:** kernel §4.1 (a relation signature is added and
`supersedes` is widened to the new kind), §4.3 and §4.4 (the accounting: the
open row empties and the kernel counts fourteen), §11 (the first question
closes); formal model §2.1 (a fourteenth `Rec` row), §2.2 (a signature row)
and §8.2 (the amendment record); coordination-and-view-kinds §5.1 (the
literal relation list, by a versioned coordination-contract amendment);
user-layer §6.1 (the publish closure names members); both copies of
`CONTRACT.yaml`; the mm30 corpus-local contract, by a successor; the guide's
foundations page, glossary and `open-questions.md`; the ledger's `Current
state` table and the roadmap, at a results record.

## 1. What this design is

Nothing in `beliefs` represents the structure a causal analysis is drawn
against. The kernel keeps three senses of *model* apart and places two of
them: the estimator is the spec's `method` and its product is the
assessment's estimate; the generator is a run, and a fitted model is only
ever a `reads` input. The third — a causal DAG, a PGM skeleton, the
predecessor's `h00` working model — is "structured sets of propositions plus
assumptions" that kernel §11 left unplaced "rather than dissolved by
accident", because `h00` made patches load-bearing.

The predecessor's eight surveyed corpora show what the thing is in practice
and what it is not:

| predecessor kind | records in the eight corpora | what it carried |
|---|---|---|
| `inquiry` | 24 (23 in mm30, 1 in natural-systems) | a scoped work program: a target hypothesis, an estimand line, a purpose, a status, and a causal DAG **as `dot` prose in the body** |
| `patch-definition` | 3 (post-acute-infection) | a focal target, a derived-membership policy (`local-closure-v1`, `max_depth`), excludes, and an authored `inquiry:` block whose `flow_edges` are `causes` triples over **concept referents**, optionally backed by `proposition:` refs |
| `structural-chain` | 0 | an ordered chain of two or more entity refs whose verdicts a `chain-audit` carried |

Three facts follow. The DAG's edges were drawn between referents, not
propositions, so a curated edge and the propositions bearing on it were two
records with an optional link; the two-axis evidence model the predecessor
rated highly (`edge_status`, `identification`) was therefore **authored per
edge**, with the documented regret that a default of `observational` "converts
missing curation into a positive evidentiary claim". The membership half of a
patch was *derived* by a policy, and the structure half was *authored*; the
two lived in one record. And the chain kind was never used.

In `beliefs` an edge of a causal DAG is already a first-class object: a
typed claim `affects(X, Y)` on the causal layer, with a proposition record,
a semantic identity, assessments and a computed belief. What has no record is
the **structure**: which referents form the node set, which claims are its
edges, and — the assertion that makes a DAG a model rather than a list — that
**no other direct edge holds among those nodes**. This design gives that
assertion a kind, `composite`, whose belief is derived from its members'
and never authored, and rules where the rest of `inquiry` and
`patch-definition` go.

## 2. Decisions

1. **A world kind, not a view.** A composite asserts something about the
   world — these variables relate this way, and among them no other direct
   relation holds — and can be wrong. World §3 puts "what is true or done"
   in the world and "what is planned or organised" in coordination; a
   hypothesis view organises propositions, a composite asserts a structure
   over them. The kind therefore takes a world address, is content-identified,
   is shared across projects by address (`h00`'s "all projects live in one
   world"), and is publishable. §12 records why a view kind was rejected.

2. **Belief-inert by construction, like `coreference-attestation`.** `assesses`
   keeps its one target kind. A composite is never a belief input, never a
   member of the belief input closure (G3), and never an eligibility subject.
   Its reading (§6) is a pure function over its members' beliefs, stored
   nowhere. This is what keeps the moratorium untouched: the composite is a
   *record* related to propositions by an edge, not a *claim* whose argument
   is a claim.

3. **Members are propositions, named by claim identity; edges are derived
   from the members' typed claims.** Every member is a directed edge, read
   off its claim's operator and layer under a domain declaration (§3.3);
   polarity is the edge's **sign** and never its presence — a negative
   `affects(X, Y)` is an inhibitory arrow, exactly as the reproduction's
   `positive_level_for` reads negative polarity as predicting the lower
   level. Nothing about a member is authored on the composite beyond its
   identity. The two-axis labels the
   predecessor authored per edge become derived columns of the reading: the
   replication axis is the member's belief, the identification axis is the
   identification class its admitted assessments carry once estimand typing
   lands (§6.2). No default exists for either, so an uncurated edge reports
   `NoBelief` and an empty identification set — never `observational`.

4. **The node set is explicit and closed.** A composite declares its nodes
   as `(sort, term)` pairs. Every member's arguments must lie in the node
   set; a node may carry no member. The absence of an edge between two
   declared nodes is the composite's assertion, which is why the set is
   declared rather than inferred from the members: inferring it would make
   "no other edge" vacuous.

5. **One shape now — `dag` — under a versioned kernel grammar.** The base
   contract declares `composite_grammar` with a closed `shapes` set holding
   `dag`. A partially directed graph, an undirected factor graph, or a cyclic
   structure is a later grammar version (§3.4), exactly as qualifier
   structure is versioned; none is a separate kind.

6. **Assumptions are members or nothing.** A DAG's assumptions are of three
   kinds and each already has a home: an absent edge is implied by the node
   set (decision 4) and by nothing else — evidence *against* an edge is a
   member whose belief is negative, and an explicit absence claim is
   unrepresentable at this grammar version (limitation 14) rather than
   smuggled in through polarity; a confounding assumption is an absent edge
   to or from a declared node; an estimand-level assumption (positivity,
   consistency, no interference) is the spec's `assumptions` under the
   estimand design. A structural-layer
   claim that a DAG relies on — `is-proxy-for`, `part-of` — is a proposition
   with its own belief and is refused as a member of the `dag` shape in this
   grammar version (§3.4), not folded in as prose. No prose assumption field
   exists: an assumption the grammar cannot type is work (formal model §6.6),
   not a record.

7. **The direction of an edge is declared by the domain, per operator.** The
   kernel does not assume slot 0 is the cause: `binds(A, B)` is symmetric and
   `affects(X, Y)` is not. A domain contract's `edges:` table names, per
   operator, which slot is the cause and which the effect (§3.3); an
   undeclared operator is refused as a member. The declaration is a
   claim-vocabulary declaration under formal model §8.3's succession rules.

8. **A composite is immutable and succeeds by `supersedes`.** The formal
   model's signature is `* ──supersedes──▶ *` (same-kind succession); the
   base contract narrowed it to propositions because nothing else needed it.
   The signature widens to `composite` and gains a declared `same_kind`
   rule (§3.1) that the shared write path and the audit enforce for every
   route in — `add`, `supersede` and import alike — so widening the kind
   lists cannot open a cross-kind edge; an identity-unchanged successor is
   refused as it is for propositions. No new revision family.

9. **The reading refuses on an unresolved member and reports a superseded
   one.** The coordination-and-view-kinds design pins that evaluation over an
   address that does not resolve "refuse[s] naming it — never denote[s] the
   empty set"; the reading follows it. A superseded member is a resolved
   record with a successor, so its row reports the succession and the
   author's remedy is a successor composite (§6.3).

10. **`structural-chain` dissolves with no successor; `patch-definition`
    splits; `inquiry` decomposes.** §7 rules each, from the survey's counts:
    a chain is a path in a composite and no corpus ever minted one; a patch's
    authored half is a composite and its derived half is a view query; an
    inquiry's DAG is a composite, its estimand is the typed spec's, its target
    is a view, and its status and decisions are coordination records.

11. **Corpus recreation, never migration.** The base contract changes shape;
    an existing corpus audits as `profile-mismatch: base` and is recreated,
    as the estimand design ruled for the same transition (its decision 10).
    No composite exists before this lane, so no pre-grammar composite can.

12. **The lane opens after `estimand-typing` merges.** Both amend the same
    base-contract, profile and reproduction surfaces, and the reading's
    identification column reads the typed estimand. Sequencing the lanes
    replaces a merge conflict with a dependency (§11).

## 3. The kind, the grammar and the declaration

### 3.1 The base contract

A fourteenth world kind and one relation signature; `supersedes` widens.

```yaml
composite_grammar:
  version: 1
  shapes: [dag]

kinds:
  composite:
    domain: science.composite.v1
    facets:
      composite: { required: true, covered: true }
      display: { required: false, covered: false }

relations:
  composes:   { group: world,     sources: [composite],              targets: [proposition] }
  supersedes: { group: lifecycle, sources: [proposition, composite], targets: [proposition, composite], same_kind: true }

facets:
  composite: { shape: reader, reader: stored.composite_value }
```

`composite_grammar` is a kernel-owned closed set, as `claim_grammar` and the
estimand design's `estimand_grammar` are: a shape is a thing the kernel
*does* — for `dag`, derive directed edges and refuse a cycle — so it cannot
be a domain's to declare. The base contract's closed field set gains the key;
both parsers refuse an unknown shape or a missing grammar. `display` is the
proposition's uncovered prose facet, reused unchanged: a label and a
rationale are content, never structure, and a hash covering them would
refuse an editorial fix.

`same_kind: true` is a new relation field, admissible only where `sources`
and `targets` are equal sets and refused at parse otherwise, in both
implementations. It states what the formal model's `* ──supersedes──▶ *
(same-kind succession)` already means: an instance's endpoints must be
records of one kind. Listing both kinds as sources and targets without it
would admit `composite ──supersedes──▶ proposition` and its reverse
through any path that does not call `supersede` — explicit import writes
records the adapter did not author — and a composite could then appear in a
proposition's supersession state, which admission reads. The rule is
therefore enforced where every incoming record passes: the shared
`_refuse` path, as a **new** check — the write path performs no relation
endpoint-kind check today (limitation 17) — placed **not** behind the
`document_validated` shortcut import takes (`supersedes-cross-kind`, a
`SignatureRefused` lineage), and again under audit for a raw-written record
(§4.3). The adapter's `supersede` keeps its
own cross-kind refusal (`FamilyKindUnsupported`) as the earlier, clearer
message; it is not the guard.

`assesses` is untouched. `composes` is a world-group relation whose only
effect is membership; it enters no closure, confers no eligibility and is
read by exactly two things — the reading (§6) and the audit (§4.3). Its row
in the formal model's §2.2 effects table reads: *membership of a composite;
the reading and the audit, never belief*.

### 3.2 The facet — `science.composite.v1`

```text
CompositeFacet =
  grammar   : "science.composite.v1"
  shape     : Shape                          -- from composite_grammar.shapes
  nodes     : sorted set of Node             -- non-empty
  members   : sorted set of ClaimIdentity    -- may be empty

Node          = (sort : NamespacedSort, term : TermIdentifier)
ClaimIdentity = I_claim of the member proposition (formal model §6.5)
```

`nodes` and `members` are canonical sets: sorted under
`science.identity.v1`'s ordering, distinct, and refused as duplicates rather
than deduplicated — a document listing one node twice is malformed, not
tidied. A composite with nodes and no members is legal and asserts that no
direct relation holds among its nodes. An empty node set is refused: a
structure over nothing asserts nothing.

The facet stores the members' **claim identities** — `I_claim`, the digest
of the claim projection (formal model §6.5), which is what a proposition's
world identity is. A proposition record also carries a `semantic-identity`
stamp, a digest of the same projection under the record's own domain; the
two are different digests of one thing, and the facet, the boundary (§4.2)
and the audit (§4.3) compare `I_claim`, never the stamp. The
`composes` relation instances store the members' **corpus refs**. This is
the assessment's two-namespace shape (`open-questions.md`, "the
assessment's `proposition` spelling"), adopted deliberately rather than by
accident: the identity-bearing facet must be world-portable — two corpora
composing the same claims hold one composite — while resolution, traversal
and the audit need a ref that resolves here. §4.2 requires the two to agree
at the boundary and §4.3 re-checks the agreement under audit, exactly as the
estimand design requires the spec's target ref and the estimand's claim to
agree.

### 3.3 The domain declaration — `edges:`

A domain contract declares which of its operators form an edge and in which
direction:

```yaml
edges:
  affects-concept-concept:            { cause: 0, effect: 1 }
  affects-concept-molecular-entity:   { cause: 0, effect: 1 }
  affects-molecular-entity-concept:   { cause: 0, effect: 1 }
  regulates-concept-concept:          { cause: 0, effect: 1 }
  regulates-concept-molecular-entity: { cause: 0, effect: 1 }
  regulates-molecular-entity-concept: { cause: 0, effect: 1 }
  induces-state-concept-concept:      { cause: 0, effect: 1 }
```

`edges:` is a new top-level key of the domain contract, beside `sorts`,
`dimensions`, `operators` and the estimand design's `estimands:`. Each row
names an operator **of the same contract**, and two distinct slots within
its arity; `EdgeDecl(operator, cause, effect)` is refused at parse for an
unknown operator, an out-of-range or repeated slot, or an operator whose
`layers` do not include `causal`. The row's key in `_declarations()` is
`edge:<operator>`, so formal model §8.3's succession rules cover it
unamended: never redefined, retired one way, tombstoned. An operator with no
row forms no edge; `binds-concept-concept` and `associates-with-*` are
deliberately absent from mm30's table because neither has a cause slot.

Compile (`ProfileSpec.edges`, keyed by namespaced operator) resolves each row
against the compiled operator and refuses a mismatch; a contract may not
declare an edge for another namespace's operator, since a direction is part
of what the operator means and only its owner may say it. The consulted walk
(D6) treats an `edges:` row as it treats an `estimands:` row: a domain
contract whose row the reading or the boundary read is a consulted contract.
Nothing about belief consults it — the reading is not belief — so the belief
input closure is unmoved by the declaration's presence, absence or content.

### 3.4 The `dag` shape — what a member contributes, and what refuses

Under `shape: dag`, each member's typed claim is read (its operator, layer,
polarity and arguments) and classified:

| the member's claim | contributes | condition |
|---|---|---|
| operator has an `edges:` row; layer `causal`; any polarity — `positive`, `negative`, `unsigned`, or the operator is sign-inapt | a directed edge `cause → effect`, carrying the polarity as its sign | both endpoint nodes are in the node set |
| operator has no `edges:` row | **refused** — `composite-member-undeclared`, naming the operator | |
| layer is not `causal` | **refused** — `composite-member-layer`, naming the layer and the fragment | |
| an argument's `(sort, term)` is not a declared node | **refused** — `composite-member-outside-nodes`, naming the argument | |
| the edge set has a cycle | **refused** — `composite-cyclic`, naming one cycle | |

Polarity never decides presence. A negative-polarity member is an
inhibitory edge, so a cycle through it is a cycle and the check runs over
every member; reading `negative` as "no edge" would turn an inhibitory
relationship into no relationship and let such a cycle escape. The DAG's
only absences are the ordered pairs of declared nodes that no member
covers, and they are implied, never authored. Two members forming the same edge — `affects(X, Y)` and `regulates(X, Y)` —
are two claims about one arrow and both stand; the edge set is a set of
ordered pairs. A member's qualifiers are carried, reported by the reading,
and not interpreted: two members on one pair restricted to different
populations are two claims about the same arrow at this grammar version
(limitation 3). A structural-layer member (`is-proxy-for`, `part-of`) is
refused with the fragment named, not silently kept as a non-edge: the
measurement relation a DAG relies on is the estimand design's
`measure.quantity` and a later composite grammar's, and keeping it here
untyped would be the predecessor's `claim_refs` again. Every refusal above
is a `CompositeError` with a stable code, raised at construction and again
at the boundary; none is a warning.

A later grammar version adds shapes — `pag` for partially directed edges,
`undirected` for factor-graph skeletons, `cyclic` for feedback — each with
its own classification table. A shape's arrival is a base-contract
successor, never a domain's choice.

## 4. Construction, the boundary and the audit

### 4.1 `build_composite`

```text
build_composite(profile, view, *, shape, nodes, members, snapshot, slug)
    → (Composite, CompositeReceipt)

CompositeReceipt = (composite identity, snapshot identity,
                    one TermOutcome per node position `node:<index>`)
```

The constructor takes the compiled profile, a read view, the shape, the node
set as `(sort, term)` pairs, the members as **corpus refs** of propositions,
and a `ResolutionSnapshot` — a required argument with no default and no
ambient fallback, for the reason `decode_claim` takes one: which
vocabularies are readable is an input, and two holders resolving the same
nodes through ambient state could disagree with nothing to say which was
right. For each member ref it resolves the record in `view`, refuses a
non-proposition (`composite-member-kind`), restores the record's typed
claim through the stored claim projection, and classifies it under §3.4.
For each node it requires the sort to be one the profile declares, the term
to be a well-formed identifier, and then resolves the term against the
sort's bound vocabulary under `snapshot`, with D3's five outcomes: `member`
admits; `not-member` **refuses** (`composite-node-not-member`, naming the
node); `not-consulted`, `not-present` and `not-available` admit, because a
check not performed is not a finding. Every outcome is written to the
receipt at the node's position in the sorted set, so a caller can tell a
node whose vocabulary was consulted and holds it from one whose vocabulary
was never opened. This matters most for an **isolated node** — one no
member's claim names — since no claim decode ever resolves it and the
composite's own resolution is its only one; U3 holds an isolated node
against a consulted vocabulary that excludes it (refuses) and against one
the snapshot did not consult (admits, `not-consulted` in the receipt).

It returns a frozen `Composite` value carrying the facet (§3.2), the derived
edge set with signs, and the members' refs beside their identities, and
the receipt beside it.

The constructor is the only route to a `Composite`: a hand-built value has
no `_checked` mark and `stored.composite_node` refuses it, the estimand
design's opaque-value pattern. `composite_node(value, *, title)` writes the
covered facet and one `composes` relation per member; the adapter's ordinary
`add` mints it under the `corpus-write` permit for `composite`, which
`permit.KIND_ACTS` gains.

### 4.2 The write boundary

`_refuse_composite(node, view)` runs inside `_refuse` for every incoming
`composite` — `add`, `supersede`, and import alike — and trusts nothing the
constructor did:

1. the facet decodes (`stored.composite_value`): grammar tag, a shape in
   the profile's `composite_grammar`, canonical non-empty `nodes` whose
   sorts the profile declares and whose terms are well-formed identifiers,
   canonical `members`; anything else is `facet-payload-malformed`. The
   boundary and the audit check **form only** and never vocabulary
   membership: like a stored claim's referents, a node's membership "is
   deferred to decode against a snapshot", and the writer holds none — the
   constructor (§4.1) and the reading (§6.1) are where membership is
   resolved, each under the snapshot its caller names;
2. the relation set is exactly one `composes` per member, in facet order,
   and nothing else authored under that predicate
   (`composite-relations-mismatch`);
3. every `composes` target resolves in this corpus to a proposition whose
   semantic identity equals the facet's member identity at the same
   position (`composite-member-mismatch`, or `composite-member-unresolvable`
   when it does not resolve);
4. §3.4's classification, re-derived from the resolved records, refuses as
   the constructor does.

A member held in another corpus is refused, not admitted unchecked, until
`world-resolution`'s read side resolves it (limitation 2, the estimand
design's limitation 2 verbatim). A superseded member is admitted: the
boundary checks resolution and identity, and succession is the reading's to
report.

### 4.3 The audit

`audit_corpus` gains a `composite` arm, `check_composite(view, node, *,
profile)`, that re-runs §4.2's steps 1–4 over the stored record and reports:

| code | when |
|---|---|
| `composite-member-unresolvable` | a `composes` target no longer resolves — a deletion or a move left the composite dangling (world-changing families §3.1: no referential check at delete, so this is where the loss is seen) |
| `composite-member-mismatch` | the resolved proposition's semantic identity differs from the facet's — a raw edit to either record |
| `composite-relations-mismatch` | the facet and the relation set disagree in count or order |
| `composite-malformed` | §3.4 refuses over the resolved records — a domain contract successor retired an `edges:` row the composite relies on, or a member's stored claim no longer classifies |
| `supersedes-cross-kind` | a stored `supersedes` instance, on any record, whose endpoints are of different kinds — a raw write, since the shared path refuses it |

A finding here is a contradiction, not malformedness: the record is well
formed, and it is read again by every later arm. The audit reads the
profile, since classification needs `edges:`; a corpus audited under a
profile with no `composite_grammar` is `profile-mismatch: base` before this
arm runs (decision 11).

## 5. Identity, lifecycle and the world

**Identity.** Content identity under `science.composite.v1` over the covered
facet — kind, `grammar`, `shape`, sorted `nodes`, sorted `members` — the
proposition's semantic-hash discipline, stamped at mint and recomputed by
`corpus_check`. Two composites over the same nodes and members in any
authoring order are one identity; adding a node with no member changes it,
because the implied absence set changed. Neither the display facet nor the local
slug enters it. The world address derives from the identity as every
semantic-identity kind's does (world §4.2).

**Lifecycle.** Immutable. A changed structure is a successor minted through
`supersede(successor, of=predecessor)`, which the widened signature admits
for a `composite` predecessor and successor of the same kind; a
cross-kind pair is `FamilyKindUnsupported`, an identity-unchanged successor
is `SupersedeIdentityUnchanged`, and the relation is authored by the adapter
as it is for propositions. `superseded_by` reports a composite's successors
through the same inbound closure. Nothing admits on a composite's
supersession state; the reading reports it.

**Deletion, move, consolidate.** The three families treat a composite as an
ordinary world record. A deleted member leaves the composite dangling and
the audit names it (§4.3); a moved member re-resolves under the destination
root as every relation target does.

**The index and views.** `composes` is traversed by the index's
predicate-generic adjacency (`RelationAdjacency`) with no new map. The
coordination contract's literal relation list (coordination-and-view-kinds
§5.1) does not carry `composes`, so at version 1 a `closure` predicate from a
composite anchor is not writable; a view selects a composite's members by
`addresses` today and by `closure` once the list is amended — a versioned
coordination-contract successor that can ride with the `publication`
amendment sub-project 5 banks, or stand alone. The kind is a world kind, so a
`kinds: [composite]` predicate is admissible from the day the base contract
declares it (`view_query` checks `stored.WORLD_KINDS`, which is derived).

**Publication.** A selected composite whose member is outside the selection
makes the publish `Refused(closure-incomplete)` with the member listed, the
rule user-layer §6.1 already states for an assessment whose run closure
names an unselected dataset; the definition of a record's closure there
gains the sentence "a composite's closure is its members".

**No belief input.** Minting, superseding or deleting a composite leaves
every proposition's belief input digest byte-identical; the closure's
projection (`closure.py`) does not mention the kind, and U4 holds it there.

## 6. The reading

### 6.1 What it is

```text
read_composite(view, ref, *,
               context      : SuppliedContext,
               availability : Availability,
               resolution   : ResolutionSnapshot,
               binding      : PolicyBinding,
               profile      : ProfileSpec) → CompositeReading

CompositeReading =
  composite   : ref, identity, shape, nodes
  standing    : active | superseded(successors)
  nodes       : one TermOutcome per node position, under `resolution`  -- §4.1's receipt, re-taken
  rows        : one MemberRow per member, in facet order              -- empty for a memberless composite

MemberRow =
  member      : ClaimIdentity, corpus ref
  role        : edge(cause, effect, sign)
  claim       : operator, args, qualifiers, polarity, layer   -- as restored
  resolution  : active | superseded(successors)
  belief      : Belief | NoBelief | Refused                   -- the evaluator's own answer
  identification : sorted set of identification terms | not-reached   -- §6.2
```

The node receipt sits on the reading, not on a row: a composite with nodes
and no members is legal (§3.2), has no rows, and still has nodes whose
resolution under this reading's snapshot is the reading's finding to
expose.

The reading is a pure function of exactly the arguments above — the
composite record as `view` serves it at the epoch, the supplied context
(lineage snapshot, producer snapshot, retraction enumeration, corpus
pins), what is held here (`Availability`: byte observations, policy
implementations, fixtures), the vocabulary resolution snapshot, the policy
binding and the profile — and of nothing ambient. It stores nothing and is
not a belief. Per member it obtains the evaluator's answer **through
`evaluation.evaluate_over`'s sequence and never by calling `gather` and
`evaluate` itself**: the wrapper's binding guard, its translation of
gather-time contract and facet errors into `Refused`, its
`NoBelief("unavailable-corpus-absent")` for inputs recorded in absent
corpora, and its corpus attribution of the gathered records are the
evaluator's behaviour, and a reading that re-sequenced them would let a
missing run reach `evaluate` as a missing dictionary entry where the
wrapper answers `NoBelief`. `belief` in a row is therefore **equal** to
what `evaluate_over(view, member, availability=, context=, profile=,
resolution=, binding=)` returns for that member, and U8 asserts the
equality rather than a shape: withholding the bound implementation makes
the row `NoBelief("unavailable-policy-unheld")`, withholding a dataset's
observation makes it `NoBelief` with the evaluator's own reason, and
neither changes without the reading's arguments changing. Nothing is
summed, weighted or combined across rows. The two-axis lesson is kept as
two columns per row, each with no default: an edge nobody has assessed
reports `NoBelief` and `{}`; a refused evaluation reports `Refused` with
its reason, never a neutral value.

A summary — how many edges carry a computed belief, how many an
interventional identification, the predecessor's ladder level — is
presentation over rows and belongs to the `science` surface. `beliefs`
returns rows.

### 6.2 The identification column

Once estimand typing lands, each admitted assessment of a member carries a
typed estimand whose `control.identification` is a term of the domain's
identification sort; the column is the sorted set of those terms over the
assessments **the evaluator admitted for that member** — the admission the
`belief` column rests on, not a second derivation — read through
`stored.analysis_spec_value` with the reading's profile.

*How the reading obtains that set.* The evaluator's step 5 — collapsing
the record pool onto identities and gating it through `admit` — is
factored into one function, `belief.admitted(records, availability,
context, profile)`, that `evaluate` calls exactly once and whose result it
carries forward; and `evaluation.evaluate_over` is restated as the first
projection of `evaluation.evaluate_over_traced`, which runs the identical
guard, gather, absent-corpus and translation sequence and returns
`(answer, admission)` where

```text
admission = not-reached                    -- the answer was given before step 5:
                                           --   Refused, or NoBelief("unavailable-policy-unheld"),
                                           --   NoBelief("unavailable-corpus-absent"), a fixture failure
          | reached(admitted identities)   -- step 5 ran; the set may be empty
```

**`NoBelief` does not imply an empty admitted set.** Two admitted
assessments that are both `inconclusive` yield
`NoBelief("no-directional-outcome")` with two admitted identities, and
their identification terms are the column's content; an empty selection
yields `NoBelief` with `reached(∅)`. Only an answer given before step 5
is `not-reached`, and the column then reads `not-reached` — never `{}`,
which would say admission found nothing when admission never ran. The
admitted set is also **not** the set the belief digest keys: the closure's
keyed-assessment-facets member covers every assessment on the proposition
that the caller's records hold, admitted or not (`closure.py`: membership
"computed from what the caller supplies as records"), while `admitted` is
admission's output over that pool. The trace returns the latter, and a
fixture with one admitted and one refused assessment pins that the two
sets differ. The reading calls the traced form once per member and reads
both columns from its result, so the two columns cannot rest on different
admissions; a fixture pins `evaluate_over(...) == evaluate_over_traced(...)[0]`
over every U8 case; and a second fixture wraps `belief.admitted` in a
trap that raises on a second call and reads a member, so "admission runs
once" is asserted directly rather than inferred from agreement.

*What that set is.* Admission today checks a run's inputs and the
verification state (G2b, G6, G2c); `verification.py` defers the
correction-lifecycle §7a clause that excludes the target of a standing
retraction to `correction-remainder`. The column follows admission **as it
is**: an assessment a standing retraction names contributes its term
exactly as it contributes to belief until that remainder lands, and when
it lands both columns move together through the one function
(limitation 16). An assessment admission refuses — a run mismatch, no
`observes` input, an unheld input, a failing verification state —
contributes no term.
It is the predecessor's `identification` axis derived instead of authored,
with `none` unspellable: a member with no admitted assessment has an empty
set, not a value. This is the one place the design depends on the estimand
lane's code, and it is why the lane opens after it (decision 12).

### 6.3 Resolution

A member that does not resolve at the epoch makes the reading **refuse**,
naming the member and the composite (`composite-member-unresolvable`) — the
same code the audit files, because it is the same defect seen from the
other side. A superseded member resolves; its row reports `superseded` with
the successor identities, its belief is still computed (the evaluator
already reads supersession state through admission), and the composite is
not amended: the author mints a successor composite naming the successor
proposition. The composite's own `standing` reports its successors the same
way.

## 7. Where the three unplaced kinds go

Kernel §4.4's accounting listed `inquiry`, `patch-definition`,
`structural-chain` and `search` as "open — unplaced deliberately". This
section places the first three; `search` stays open, since a coverage
record is not a structure.

### 7.1 `structural-chain` — dissolved, no successor

Zero records in the eight corpora. Its shape — an ordered chain of two or
more refs — is a path in a `dag` composite, and its verdicts (`chain-audit`:
*evidence for*, *evidence against*, *mixed*, *inconclusive*, with a Bayes
factor) were authored claims about a set of claims, which is the K-record
shape the moratorium holds. The derived reading replaces both: a path's
standing is its rows. Nothing is built for it and nothing waits on it.

### 7.2 `patch-definition` — split along the line it already had

Its authored half — the focal target, the `flow_edges`, the boundary roles —
is a composite: the `causes` triples over concept referents become
causal-layer propositions over declared nodes, and `BoundaryIn` /
`BoundaryOut` are the node set's exogenous and outcome nodes, which the
`dag` shape derives (a node with no incoming edge; a node with no outgoing
edge) rather than stores. Its derived half — `local-closure-v1` with
`max_depth`, `scope_set`, `excludes` — is a view: the coordination-and-view-
kinds design's `closure` predicate from an anchor over named relations is
the same derivation, and once `composes` enters the literal relation list a
neighbourhood around a composite is one clause. Two things do not carry
over: a depth bound (`max_depth`), which `science.view-query.v1` has no
predicate for and which arrives, if the pinch is real, as a v2 predicate by
the road §2.4 there names; and `excludes`, which is negation, deliberately
absent from the language (§2.5 there). Both are named in §13, not worked
around.

### 7.3 `inquiry` — decomposed into records that exist

An mm30 inquiry carries five things, and each has a home:

| what the inquiry carried | where it goes |
|---|---|
| the causal DAG, as `dot` prose | a `composite` over propositions minted for its edges |
| the estimand line ("PHF19 expression → overall survival, total and direct effects") | the typed estimand of the analysis specs that assess its edges (estimand design §3); *direct* versus *total* is `control.conditioning`, not structure |
| the target hypothesis and the question | `hypothesis` and `question` views whose queries name the composite and its members by `addresses` |
| status (`sketch` … `complete`), purpose, decisions, "next moves" | a `project`'s coordination records — `task`, `decision`, `note` with `about` naming the composite |
| transformations and validation refs | runs, and verifications over them |

Nothing is left that needs a kind. The mm30 corpus's 23 inquiries and the
predecessor's `h00` working model are heritage under `recreate-mm30-not-
migrate`: the reproduction lane composes the fragment it has evidence for
(§9), and the rest is recreated as propositions and composites when a
project needs them, never bulk-imported from `dot` bodies.

### 7.4 What this closes and what it does not

Kernel §11's first bullet closes. Kernel §4.4's open row loses three of its
four entries. The non-empirical route is **not** touched: a claim *about* a
composite — "this DAG is consistent with the data", a causal-discovery
posterior over structures, a model-fit statistic — is model-conditional and
has no assessment, exactly as before. A composite is a structure over
claims, never a claim, and its reading is never a belief.

## 8. Guarantees — table U

| row | guarantee | how it is tested |
|---|---|---|
| **U1** | The base contract declares `composite_grammar` and the `composite` kind; an unknown shape, a missing grammar, or a `composes` signature outside `composite → proposition` refuses at parse in both implementations | Python and TypeScript parse the shipped contract and refuse each mutation; the world-kind count is fourteen in both |
| **U2** | A domain `edges:` row names an own-namespace operator with `causal` among its layers and two distinct in-range slots; compile keys it by namespaced operator; succession never redefines a row | parse and compile refusals; a successor contract redefining `edge:<op>` refuses under §8.3's rule |
| **U3** | *Form and classification, at construction and at `add` alike:* refuse, with the named code, a member whose operator is undeclared, whose layer is not `causal`, whose argument is outside the node set, a cycle — including one through a negative-polarity member — a duplicate node or member, and an empty node set; admit a composite with nodes and no members, and a negative-polarity member as a signed edge. *Vocabulary, at construction and at reading only:* `build_composite` refuses an isolated node that a consulted vocabulary excludes (`composite-node-not-member`) and the reading refuses the same stored record under the same snapshot, while `add` admits it, checking form only (§4.2); under a snapshot that did not consult the vocabulary both admit it with `not-consulted` in the receipt | one fixture per row of §3.4's table, each asserted at construction and at `add`; the isolated-node fixture asserted at construction, at `add`, and at reading, under an excluding and an unconsulted snapshot |
| **U4** | Minting, superseding and deleting a composite leaves every proposition's belief input digest byte-identical, and `assesses` cannot target one | digest before and after each family operation; a hand-built assessment naming a composite refuses at the signature |
| **U5** | Identity is content identity over the covered facet: authoring order does not move it; a node with no member does; display prose does not | three pairs of records, hashed |
| **U6** | The boundary requires each `composes` target to resolve to a proposition whose semantic identity equals the facet's member at that position; a mismatch, a non-proposition and an unresolvable ref each refuse with their code | a stored composite with a swapped member, a dataset member, and a member ref that resolves nowhere |
| **U7** | The audit reports an unresolvable member, a mismatched member, a relation-set mismatch, and a composite that no longer classifies, as contradictions, not malformedness, and reads the record again in later arms | delete a member and audit; raw-edit a member's claim and audit; retire the `edges:` row by successor and audit |
| **U8** | The reading is a pure function of its named arguments — record, view at the epoch, supplied context, availability, resolution snapshot, binding, profile: two processes agree byte for byte under equal arguments; every row's `belief` **equals** `evaluate_over`'s answer for that member under the same arguments — so withholding the policy implementation reads `NoBelief("unavailable-policy-unheld")`, withholding a dataset observation reads the evaluator's own `NoBelief`, and a member whose inputs sit in an absent corpus reads `NoBelief("unavailable-corpus-absent")` — with the identification column drawn from the same traced admission — two admitted `inconclusive` assessments read `NoBelief("no-directional-outcome")` with both identification terms present, and an answer given before admission reads `not-reached`, never `{}`; a member with no admitted assessment reads `NoBelief` and `{}`; a superseded member reads its successors and a belief; an unresolvable member refuses the reading; a memberless composite reads no rows and a node receipt, with `not-consulted` for a node under an unconsulted vocabulary | the reproduction's composite read twice from persisted records (§9); a fixture composite with an assessed, an unassessed and a superseded member, read under full availability and under each withholding, each row compared with `evaluate_over` called directly; a two-inconclusive fixture; a one-admitted-one-refused fixture pinning the admitted set apart from the digest's keyed facets; a memberless two-node composite under an unconsulted snapshot |
| **U9** | `supersede` admits a same-kind composite successor, authors the relation, and refuses a cross-kind pair and an identity-unchanged successor; a `supersedes` instance with endpoints of different kinds refuses on the shared path for `add` and for `import_bundle` (`ImportRefused`, the member named), and a raw-written one audits as `supersedes-cross-kind`; both parsers refuse `same_kind` on a relation whose sources and targets differ | the three family calls; an import bundle carrying `composite ──supersedes──▶ proposition` and its reverse; a raw-written pair audited; a mutated contract parsed in Python and TypeScript |
| **U10** | The reproduction composes the `h1-prognosis` fragment from the recreated corpus and reads it in a fresh process: the assessed member carries the evaluator's belief and the unassessed one `NoBelief`, from persisted records, twice, byte-identical | §9's addendum, from persisted records |

## 9. The reproduction

The reproduction lane's sequence, as the estimand design leaves it, is
`world`, `select_target`, `lists prepare`, `concepts`, `lists mint`,
`type_target`, `hold`, `spec`, `run`, `belief`, `rederive`, `close`. This
design adds two steps after `belief`:

- **`compose`** — the successor mm30 contract gains an `edges:` table over
  its `affects-*`, `regulates-*` and `induces-state` operators, seven rows
  (§3.3's example is that table; `biology`'s successor gains one row, for
  `affects-molecular-entity-molecular-entity`). The driver mints a second
  proposition, `affects-molecular-entity-concept(PHF19, overall-survival)`
  at the causal layer, positive — the `h1-prognosis` inquiry's spine, and a
  claim the recreated corpus has no evidence for — then a composite
  `h1-prognosis-fragment` with nodes `{(mm30/concept, disease-stage),
  (biology/molecular-entity, PHF19), (mm30/concept, overall-survival)}` and
  members `{the reproduced target, the new proposition}`. The concept list
  holds `overall-survival` (measured 2026-09-12, `entities/concepts/`).
- **`read`** — the driver reads the composite under the reproduction's
  policy binding, supplied context, availability and resolution snapshot —
  the same four the `belief` step handed the evaluator — and records the
  node receipt and the rows: the target member `edge(disease-stage
  → PHF19)` with the belief the `belief` step computed and the
  identification set `{observational}` from its typed estimand; the spine
  member `edge(PHF19 → overall-survival)` with `NoBelief` and `{}`. The
  reading is taken twice, from persisted records in a fresh process, and the
  two byte strings are compared.

What the addendum records: the composite's identity, the rows, and the
author's judgment that the fragment is the inquiry's spine and not its
DAG — the inquiry's other nodes (gain(1q), EZH2, PRC2 retargeting,
proliferation score, the proxies) are not minted, because the corpus holds
no propositions for them and this lane does not author claims it has no
evidence for. That the `is-proxy-for` edges of the inquiry cannot be
members at this grammar version is recorded as the first exercise of
limitation 5, not worked around by typing them as `affects`.

## 10. Testing and the cut

### 10.1 Unit

`test_composite.py` (construction, classification, identity, the reading
over fixtures), `test_facet_declarations.py` and the TypeScript
`declarations.test.ts` (the fourteen-kind inventory and the grammar),
`test_domain_contract.py` (`edges:`), `test_permit.py` (the key set),
`test_coordination.py` (the inventory assertion), `test_audit.py` (the four
codes), `test_corpus_write.py` (`supersede` for composites).

### 10.2 Acceptance

`tests/acceptance/test_composite_acceptance.py` declares U1–U10 and holds
U8 and U10 against persisted records, in a fresh process, twice.

### 10.3 N2 sabotages

| arm | sabotage | caught by |
|---|---|---|
| U4 | `closure.py`'s projection gains the composites naming the proposition | the digest moves when a composite is minted |
| U4 | the base contract's `assesses` targets gain `composite` | the signature test and U1 |
| U6 | `_refuse_composite` skips step 3 | a swapped member is admitted |
| U9 | the same-kind check moves behind `document_validated` | the import arm admits a cross-kind edge |
| U8 | the reading maps an unresolvable member to `NoBelief` | U8's refusal arm |
| U8 | the reading defaults an empty identification set to `observational` | U8's `{}` arm |
| U8 | the reading builds its own `Availability` from the checkout instead of taking it | U8's withholding arms disagree with the evaluator's |
| U8 | the reading calls `gather` and `evaluate` directly, skipping the wrapper's absent-corpus arm | U8's absent-corpus row disagrees with `evaluate_over` |
| U8 | the identification column re-runs `admit` instead of reading the traced set | the trap on a second `belief.admitted` call raises during the reading — a pure function re-run over equal inputs agrees with itself, so agreement is not the assertion; the call is |
| U8 | the traced form maps every `NoBelief` to an empty admitted set | the two-inconclusive fixture loses its terms |
| U3 | classification accepts a `statistical`-layer member as an edge | the `associates-with` fixture |
| U3 | classification drops a negative-polarity member from the edge set | the signed-cycle fixture |

### 10.4 The cut

A cut number is claimed at freeze, not now (concurrency rule 1); the runner
names the highest-numbered acceptance runner discharged at that time in
`PREFIX_RUNNERS` (rule 5) and carries `PHASE_MODULES =
("test_composite_acceptance.py", "test_n2_cut<N>.py")`. Declaration units
U1–U10. Frozen by dated commit after review clears; invalidated frozen
evidence is pinned and cited, never edited.

### 10.5 Shared files, under concurrency rule 3

`errors.py`, `test_designs_corpus.py` (a new table letter moves the README's
"frozen tables" count), the ledger, the roadmap and the guide index, as every
lane. Beyond those this lane rewrites both `CONTRACT.yaml` copies,
`contract/base.py`, `contract/domain.py`, `contract.ts`, `profile.py`,
`stored.py`, `corpus.py` (`supersede`, `_refuse`), `audit.py`, `permit.py`
and the reproduction driver — every one of them a surface the
`estimand-typing` lane rewrites, which is why this lane opens after that one
merges rather than beside it.

## 11. Roadmap and ledger placement

- A new boundary, **`composite-claims`**, owner this design, rows U1–U10,
  enters the ledger's `Current state` table and the roadmap's boundary index
  at the results record that discharges its cut; until then this design is
  named from `open-questions.md`'s "Kernel-adjacent structures" entry.
- **Tier 1, off the path.** The dogfood's first belief needs no structure:
  the reproduction reached a computed belief over one proposition. It opens
  a lane, `composite-claims`, only when no on-path lane is startable (rule
  6), and **after `estimand-typing` merges** (decision 12).
- **Before the contract cut freezes.** It amends the base contract's kinds,
  relations and grammar; N1 mints a successor identity for every oracle
  amended after the freeze, so `contract-cut` waits on this lane as it waits
  on every other oracle-amending lane, and `beliefs-eacbe2` gains the
  dependency when the lane opens.
- **The coordination-contract amendment** (the literal relation list gaining
  `composes`) is sub-project 5's road, not this lane's; the lane files the
  row and does not wait on it.
- The estimand design's §14 sentence that the composite design "does not
  depend on this one" is true of the design and false of the lane; this
  document is the correction, and the estimand spec is not edited on its
  branch for it.

## 12. Alternatives rejected

- **A view kind in the coordination contract.** Cheapest: a `structure`
  view whose query enumerates member addresses. Rejected because a view
  carries no world address and asserts nothing — it "is a stored world
  query plus a label, never a container", and the absence of an edge cannot
  be a query result. It would also be per project, and `h00` rules that
  structures are shared.
- **No kind at all — render the DAG by query.** `kinds: [proposition]`
  intersected with `references-term` over a node list draws the same
  picture. Rejected because the node set is then nobody's assertion, the
  absence of an edge means nothing, and two projects cannot name the same
  structure or supersede it.
- **A higher-order claim** — `composes` as an operator whose arguments are
  claims. Rejected by the moratorium (cut 1 §2.4), and unnecessary: a
  relation between records carries everything a structure needs.
- **A kind named `model`, `structure` or `inquiry`.** `model` is the word the
  assessment showed names three things; `structure` collides with the
  `structural` claim layer, which a `dag` composite refuses; `inquiry` names
  the work program §7.3 decomposes. `composite` says what the record is.
- **An assumption role on members, or a prose `assumptions` field.**
  Decision 6: every assumption a DAG makes is a member, an absence the node
  set implies, or the spec's. A prose field is `claim_refs` again.
- **Negative polarity as an absence member.** The first draft's reading;
  review found it turns inhibition into no relationship and lets a signed
  cycle escape detection. Polarity is a sign (decision 3).
- **Authored per-edge labels** (`edge_status`, `identification`,
  `ladder_level`). The predecessor's documented regret; both are derived
  columns here and the ladder is presentation.
- **A scalar belief for the composite.** Summing member beliefs is
  meaningless over a DAG and would make a belief-bearing thing of a
  belief-inert kind; the reading returns rows.
- **Inferring the node set from the members.** Makes "no other edge"
  vacuous (decision 4).
- **Assuming slot 0 is the cause.** `binds` is symmetric; direction is the
  owner's declaration (decision 7).
- **Admitting structural-layer members now.** Proxies and part-of relations
  are what a DAG's measurement model needs, and typing them as non-edge
  members without a reading of what they contribute is the untyped bag the
  design refuses; they wait for a grammar version with a classification for
  them (limitation 5).
- **A new revision family for composites.** `supersedes` is already
  same-kind succession in the formal model; widening a signature is smaller
  than a door.
- **Migrating mm30's 23 inquiries.** `recreate-mm30-not-migrate`; `dot`
  bodies are heritage.

## 13. Limitations and open questions this design files

1. **Membership asserts directness only relative to the node set, and the
   member's belief is about the claim as stated.** `affects(X, Y)` assessed
   by an adjusted regression is a total or conditional effect under its
   typed estimand; the composite's edge says the relation is direct *among
   these nodes*. The reading reports the member's belief and the estimand's
   conditioning set side by side and does not claim the belief is about the
   direct edge. Whether a policy may read a composite's structure to select
   which assessments bear on an edge is a successor-policy question.
2. **Members are corpus-local at the boundary.** A member held in another
   corpus refuses until `world-resolution`'s read side lands (the estimand
   design's limitation 2, shared).
3. **Qualifier heterogeneity among members is not checked.** Two members on
   one ordered pair restricted to different populations are two claims
   about one arrow; the estimand design's `co_scoped` is the predicate a
   later grammar version would apply, and nothing applies it here.
4. **Cycles refuse.** Feedback is a later shape, not a malformed DAG with
   the check off.
5. **Structural-layer members refuse.** The `is-proxy-for` edges of every
   mm30 inquiry cannot be members at this grammar version.
6. **Latent nodes carry no marker.** The predecessor drew latent nodes
   dashed; here a latent variable is a node like any other, and whether it
   is measured is a fact about specs, not structure.
7. **No summary, no ladder.** Rows only; the `science` surface derives
   counts and levels.
8. **Faithfulness and the Markov condition are unstated.** The `dag` shape
   gives the absence set a meaning — no direct edge — and says nothing about
   d-separation or what the absence implies for distributions; a reader
   that wants adjustment sets from a composite is a later design over the
   rows and edges this one exposes.
9. **No relation between composites.** Sub-structure, refinement and
   agreement between two composites are definable over their edge sets and
   are not defined; the constraint formal model §6.7 states for entailment
   applies — the encoding keeps them definable.
10. **A depth-bounded neighbourhood and an exclusion list are not
    expressible** in `science.view-query.v1`; `patch-definition`'s derived
    half loses both until a v2 predicate (§7.2).
11. **TypeScript validates no composite payload**, only the grammar and the
    kind declaration (the estimand design's limitation 7, extended).
12. **`closure` from a composite anchor waits on the coordination-contract
    amendment** (§5).
13. **The identification column is empty until estimand typing lands**, and
    the lane is sequenced after it rather than shipping the column blank.
14. **An explicit absence claim is unrepresentable.** Polarity is a sign,
    and the grammar's closed polarity set has no "no effect" value; a
    finding of no effect is a refuted edge member, and a composite that
    wants to *assert* an absence beyond what its node set implies has no
    member to do it with at this grammar version. A separately declared
    absence meaning is a later grammar version's, if a corpus needs one.
15. **Node membership is resolved at construction and at reading, never at
    the boundary.** A stored composite whose node was `not-consulted` when
    built is well formed; whether its term is a member is the next
    reading's finding under that reading's snapshot.
16. **The identification column follows admission as it is.** Retraction
    filtering of admitted assessments is deferred by `verification.py` to
    `correction-remainder`; until it lands, an assessment a standing
    retraction names contributes a term as it contributes to belief. The
    column and the belief share one admission function, so they move
    together and never disagree.
17. **Relation endpoint kinds are not enforced at the write boundary.**
    The base contract's `sources` and `targets` are parsed and compiled and
    consulted by nothing on the shared refusal path — found while planning.
    `composes` endpoints are checked by the composite's own boundary step
    and `supersedes` by the same-kind rule; every other signature rests on
    the typed constructors and the audit. A general endpoint-kind check is
    filed in `open-questions.md` at the cut, not built here.

## 14. Task linkage

`beliefs-4bcf88` carries this spec; the implementation plan's tasks become
its children. The estimand-typing design (`beliefs-59f846`, on
`design/estimand-typing`) precedes this lane (decision 12).
`beliefs-eacbe2` (the contract cut) gains it as a dependency when the lane
opens. `search` and the non-empirical route stay where kernel §11 holds
them.

## 15. Review log

- 2026-09-12, drafted in session from the models assessment, after the
  estimand-typing spec cleared review.
- 2026-09-12, first review, four findings, all taken: (1) negative polarity
  was read as an absent edge, turning inhibition into no relationship and
  letting a signed cycle escape — polarity is now the edge's sign and never
  its presence (decisions 3 and 6, §3.4, limitation 14); (2) the reading
  promised determinism from four inputs while the evaluator needs supplied
  context, availability and a resolution snapshot — §6.1 names every
  argument, the identification column rests on the same admission, and U8
  gains the withholding arms; (3) widening `supersedes` to two kinds admitted
  cross-kind edges through import — the relation declares `same_kind`,
  enforced on the shared write path outside the `document_validated`
  shortcut and under audit, with an import arm in U9; (4) construction
  invoked the five resolution outcomes without a snapshot or a receipt —
  `build_composite` takes a `ResolutionSnapshot` and returns a receipt per
  node, isolated nodes are tested under consulted non-membership and an
  unconsulted vocabulary, and the boundary checks form only (limitation
  15).
- 2026-09-12, second review, four findings, all taken; `same_kind` stays
  declarative: (1) the reading re-sequenced `gather` and `evaluate`,
  bypassing `evaluate_over`'s absent-corpus arm, error translation and
  attribution, and U8 expected `Refused` for an unheld implementation where
  the evaluator answers `NoBelief("unavailable-policy-unheld")` — §6.1 now
  obtains each row through the wrapper's sequence and U8 asserts equality
  with `evaluate_over`'s answers; (2) the identification column promised a
  retraction exclusion admission does not perform — it follows the current
  admitted set, obtained once through `evaluate_over_traced` over a
  factored `belief.admitted`, with limitation 16; (3) U3 required `add` to
  refuse a vocabulary-excluded node the boundary cannot see — split into
  form-and-classification arms at construction and `add`, and vocabulary
  arms at construction and reading; (4) node outcomes lived on member rows
  and vanished for a memberless composite — the receipt sits on
  `CompositeReading`, with a memberless fixture in U8.
- 2026-09-12, third review, two findings, both taken: (1) the traced form
  discarded the admitted set on every `NoBelief` arm, though two admitted
  `inconclusive` assessments answer `NoBelief("no-directional-outcome")`
  with identities — the trace now returns `not-reached` or
  `reached(identities)`, the column reads `not-reached` rather than `{}`
  when admission never ran, and the admitted set is pinned apart from the
  digest's keyed facets; (2) the repeated-admission sabotage was caught by
  nothing, since a pure function re-run over equal inputs agrees with
  itself — replaced by a trap on a second `belief.admitted` call.
- 2026-09-12, cleared for implementation planning. Two corrections found
  while planning, recorded here: (1) §3.1 said the same-kind rule sits
  beside a relation-instance signature check the write path already
  performs; no such check exists — `RelationDecl` is read by nothing on the
  write path — so the rule is a new check and the general absence is
  limitation 17; (2) §3.2's "semantic identity" of a member is `I_claim`,
  not the record's `semantic-identity` stamp, and the boundary compares
  `I_claim`.
