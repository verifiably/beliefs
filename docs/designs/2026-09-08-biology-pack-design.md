# The biology pack and the cross-contract slot — design (the `domain-boundary` slice, part 2)

**Date:** 2026-09-08
**Status:** designed 2026-09-08 in a brainstorming session of five sectioned
reviews, each approved as presented (scope and the two contracts; the
cross-contract slot rule; the domain-facet read; contract locations and the
measurement; guarantees, the cut sketch, limitations and open questions).
Conformance cut 22 is not yet frozen; the freeze is a separate document
written after this design's review clears (§8). Not implemented.
**Scope:** the second of two slices on the `domain` lane, anchored on the
mm30 reproduction record's measured floor (`2026-09-05-mm30-reproduction.md`
§5 question 1 and §6 step 2), the facet-contracts design's read-ledger
question (`2026-09-05-facet-contracts-design.md` §5.6, §14), and the
roadmap's slice-2 row (`docs/plans/2026-08-29-implementation-roadmap.md`,
`domain-boundary`). The slice ships the first domain contract the package
carries, a corpus-local contract for mm30, the kernel rule that lets the two
compose, and the first derivation-side read of a domain facet. It reproduces
the measured floor and closes D6. Task `beliefs-1ce152`, parent
`beliefs-bc3aff`.
**Sources:** the domain extension boundary design (`2026-08-04-domain-extension-boundary-design.md`,
"D"), the formal model and claim calculus design
(`2026-08-04-formal-model-and-claim-calculus-design.md`, "M"), the facet
contracts design ("F"), conformance cuts 2 and 20, the belief policy design
(`2026-08-05-belief-policy-design.md`, "P"), the user and autonomy layer
design (`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`
§4.3 and sub-project 3), and the exercise vocabularies under
`python/tools/vocabularies/`.

---

## 1. Problem

The reproduction typed its one proposition under the exercise's *unsorted*
vocabulary, whose single sort admits every kind prefix mm30 recorded, and it
measured what the *modal-sorted* vocabulary says to the same target:

> `ArgumentSortMismatch: slot 1 of 'mm30/affects' is declared 'mm30/concept';
> 'protein:PHF19' is of sort 'mm30/protein'. Inside the model these are
> different types, so this is not a rejected value but a term with no slot
> to occupy.`

That refusal is the floor this slice must clear, and the record states it
exactly: one operator, `affects`, with a concept→protein argument pair; two
referents, `concept:disease-stage` and `protein:PHF19`; the `causal` layer and
`positive` polarity. The modal rule assigns `affects` two `concept` slots
because 208 of its 224 uses are concept→concept, and by that rule it refuses
the ten concept→protein records, one of which is the dogfood.

Three facts in the tree shape the answer.

1. **An operator has one signature.** M §6.2: `ArgSort(op) : Fin(arity(op))
   → Sort`, one sort per slot, and `Referent(s)` is a type — a term of the
   wrong sort has no slot to occupy. There is no overloading, no subsort,
   and no slot admitting two sorts. So "how a biology operator admits more
   than one argument shape" has one model-conforming answer: it does not;
   each shape is an operator.
2. **mm30's concept terms are corpus-local.** The 285 records under mm30's
   `entities/concepts/` are names like `1q-gain`, `bortezomib-regimen` and
   `disease-stage`, which no public ontology binds. A `concept` sort can be
   bound honestly only to that list, held as a dataset by content identity
   (D §5's preferred form). Its protein terms are the 27 HGNC symbols the
   corpus uses.
3. **A slot names a sort of its own contract, and a binding is for life.**
   `parse_domain_contract` refuses `arg_sorts[i]` that is "not a sort this
   contract declares", and the succession rules (D §12, M §8.3) put a sort's
   vocabulary binding inside its canonical schema projection, so a sort
   bound to mm30's list today is bound to it under that identifier forever.

Put together: the operator the dogfood needs has a corpus-local slot and a
biology slot, it cannot live in a contract that owns only one of the two,
and the shared pack must not own the corpus-local one. That is the design's
centre: a **cross-contract slot rule** (§4) under which a corpus-local
contract may name a shipped pack's sort, never the reverse.

Beside the floor sits the arm slice 1 left open. `consulted_contracts` takes
a `facets_read` ledger that every derivation passes empty (F §5.6, F §9 item
3), so D6's facet arm — *derive belief over an assessment reading
`biology/gene-axis`, bump the biology contract, assert the digest moves* —
has never run against a reader. The ledger "must eventually come from the
readers' own execution … never from a caller". This slice ships that reader
(§5).

## 2. Decisions

Each was put to review as a question and ruled as stated.

1. **Scope is the minimum that clears the floor.** The operator vocabulary
   and the sorts a concept→protein `affects` needs; the GO, HP, EFO and
   MONDO bindings named by the layer design's sub-project 3 stay unmeasured,
   where cut 20 left them (§9). The alternative of designing all four
   bindings now was declined as a larger lane that still has to settle the
   shape question first.
2. **One operator per argument shape.** mm30's `affects` was four relations
   under one English word; each predicate-by-kind-pair the corpus recorded
   is one operator, declared by the contract that owns its sorts (§3.3).
   Rejected: one coarse sort per slot, which is the unsorted plan under a
   new name and would need one vocabulary spanning proteins and disease
   stages, which none does; and a kernel amendment giving slots sort-sets or
   a sort lattice, which reopens M §6.2's "different types" ruling and the
   operator schema projection that enters claim identity — a separate
   kernel lane if ever wanted, not this slice.
3. **Sorts split by vocabulary, and slots may cross contracts.** Biology
   owns `molecular-entity` (HGNC, exact release); mm30's corpus-local
   contract owns `concept` (its held list) and every operator with a concept
   slot, naming `biology/molecular-entity` in the cross-typed ones.
   Rejected: one corpus-local contract carrying both sorts, which makes
   `mm30/molecular-entity` and `biology/molecular-entity` different types
   forever; and the pack binding `concept` to one corpus's list, which
   succession makes permanent.
4. **The slice carries the pack and D6's facet arm; D1's `nodes` negative
   stays deferred.** The negative runs in another repository's suite; under
   the rule that any unrun arm is partial it is not claimed here (§7).
5. **The first domain-facet read is generic, reported, and never weighed.**
   `gather` reads every declared domain facet on each observed dataset it
   holds, re-validates it, fills the ledger from that execution, and digests
   the rows; the verdict is untouched, on P6's `applicability` precedent.
   Rejected: a biology-specific reader with a verdict effect, which needs P
   §open question 4 (whether a domain may extend `NoBeliefReason`) answered
   and puts domain code in the kernel; and a ledger read off the assessment's
   own declaration, which is the caller-selected digest F §5.6 refused.
6. **Operator names follow one mechanical rule** (§3.4). Nothing is named
   per operator, for the reason the modal file gave: a computed rule cannot
   be adjusted operator by operator until the yield improves.
7. **The closure member is always present.** `observed_facets` enters the
   projection empty or not; a projection whose shape depends on content is
   the fault M9 guards `π_claim` against. The one-time movement of every
   existing digest is accepted and stated (§5.4, §9).
8. **The pack lives at `domains/biology/`**, the location the layer design
   named, with a packaged byte-identical copy on the base contract's pattern
   (§6.1). The alternative, `contracts/biology/` beside `science`, was
   offered and declined.

## 3. The two contracts

### 3.1 The measured shapes

Over mm30's 307 structured propositions (`subject`, `predicate`, `object`
present), the predicate-by-kind-pair tally is:

| predicate | subject → object | count |
|---|---|---|
| affects | concept → concept | 208 |
| affects | concept → protein | 10 |
| affects | protein → concept | 5 |
| affects | protein → protein | 1 |
| associates_with | concept → concept | 46 |
| associates_with | protein → protein | 3 |
| associates_with | protein → concept | 1 |
| binds | concept → concept | 1 |
| induces_state | concept → concept | 12 |
| is_proxy_for | concept → concept | 5 |
| part_of | protein → concept | 3 |
| part_of | concept → concept | 1 |
| regulates | concept → protein | 5 |
| regulates | concept → concept | 2 |
| regulates | protein → protein | 1 |
| regulates | protein → concept | 1 |
| subtype_of | concept → concept | 2 |

Seventeen shapes over eight predicates. Every shape with at least one record
is an operator; the contract does not pre-declare shapes the corpus never
recorded. `binds` between two `concept` terms is kept as measured — the
modal file's remark that the operator's own meaning objects is a finding
about the corpus, and this design does not correct a corpus by typing it.

### 3.2 The biology pack — `biology`

Declares what is biology's regardless of corpus.

```yaml
contract:
  contract: biology
  version: 1
  lineage: genesis

  sorts:
    molecular-entity:
      vocabulary: { namespace: HGNC, release: "<archive date>" }

  dimensions: {}

  operators:
    affects-molecular-entity-molecular-entity:
      arity: 2
      arg_sorts: [molecular-entity, molecular-entity]
      sign_apt: true
      layers: [causal, structural, statistical]
      dimensions: []
    associates-with-molecular-entity-molecular-entity:
      arity: 2
      arg_sorts: [molecular-entity, molecular-entity]
      sign_apt: true
      layers: [statistical, causal]
      dimensions: []
    regulates-molecular-entity-molecular-entity:
      arity: 2
      arg_sorts: [molecular-entity, molecular-entity]
      sign_apt: true
      layers: [causal]
      dimensions: []

  facets:
    gene-axis:
      attaches_to: [dataset]
      fields:
        axis: { type: string, required: true }
        namespace: { type: string, required: true }
```

- **`molecular-entity`** is the formal model's own example sort (M §7, the
  biology contract sketch), bound to HGNC because mm30's protein terms are
  HGNC symbols and the sketch already binds it so. The release is the most
  recent HGNC archive date on or before this design's date, spelled as that
  archive date; the exact string is fixed in the implementation plan when
  the file is authored, and once authored it is the sort's binding for the
  life of the identifier. No HGNC release is held in this slice, so
  resolution answers `not-consulted`, which D3 lets mint.
- **The three operators** are the protein→protein shapes. Sign-aptness and
  admitted layers are read off the corpus's own predicate usage exactly as
  the exercise did (the modal file's per-operator `layers`), not chosen.
- **`gene-axis`** is the facet D §4 sketched and D2, D6 and the tests
  already name. `axis` says which axis of the dataset's tabular form carries
  molecular entities (`rows` for the dogfood's TPM matrix), `namespace` says
  under which identifier namespace (`HGNC`). Both are `string` under F
  §3.4's grammar; no nesting, no default. A domain facet is optional and
  never covered (F §3.3).

The pack declares no `kinds:` or `relations:` (refused at load, F §3.3) and
no dimensions.

### 3.3 The corpus-local contract — `mm30`

Declares what is one corpus's.

```yaml
contract:
  contract: mm30
  version: 1
  lineage: genesis

  sorts:
    concept:
      vocabulary: dataset:sha256:<content identity of the held concept list>

  dimensions: {}

  operators:
    affects-concept-concept:
      arity: 2
      arg_sorts: [concept, concept]
      ...
    affects-concept-molecular-entity:
      arity: 2
      arg_sorts: [concept, biology/molecular-entity]
      sign_apt: true
      layers: [causal, structural, statistical]
      dimensions: []
    affects-molecular-entity-concept:
      arity: 2
      arg_sorts: [biology/molecular-entity, concept]
      ...
    # … the remaining eleven shapes with a concept slot, one entry each
```

Fourteen operators: every shape in §3.1 with at least one `concept` slot.
Eight are concept→concept and name only `concept`. Six are mixed —
`affects` c→p and p→c, `associates_with` p→c, `part_of` p→c, `regulates`
c→p and p→c — and name `biology/molecular-entity` in the protein slot under
§4's rule. The remaining three shapes in §3.1 are protein→protein and live
in the pack (§3.2); 8 + 6 + 3 = 17.

**The partition rule.** An operator is declared by the contract that owns
its most specific sort: a corpus-local sort if any slot has one, else the
pack. A corpus-local contract may reference the pack; the pack cannot
reference a corpus-local contract, not by a rule but because it is compiled
in corpora that hold no such contract, and the compile refuses an
unresolved reference (§4.3). The consequence is stated once: **the biology
pack's operator vocabulary is three operators**, and the roadmap row that
put "mm30's operator vocabulary" in the pack is corrected (§10).

### 3.4 Operator names

One rule, applied to every operator in both contracts:

```text
<predicate>-<subject sort>-<object sort>
```

with the predicate's underscores as hyphens (the identifier grammar is
`[a-z][a-z0-9-]*`) and each sort by its **local** name — `concept`,
`molecular-entity` — never its namespace. The dogfood's operator is
`mm30/affects-concept-molecular-entity`. The names are long and uniform on
purpose; a shorter name for the modal shape would be a per-operator choice.

### 3.5 The plan map

The exercise's `plan:` section maps a corpus predicate to one operator. It
now maps a **predicate and kind pair** to an operator, and a kind prefix to a
**namespaced** sort:

```yaml
plan:
  operators:
    - { predicate: affects, subject: concept, object: concept, operator: affects-concept-concept }
    - { predicate: affects, subject: concept, object: protein, operator: affects-concept-molecular-entity }
    # … one row per shape in §3.1, seventeen in all; a shape with no row refuses
  sorts:
    concept: concept
    protein: biology/molecular-entity
  layers:     { causal_effect: causal, structural_claim: structural, empirical_regularity: statistical }
  polarities: { positive: positive, negative: negative, unsigned: unsigned, not_applicable: null }
```

`subject` and `object` are the corpus's kind prefixes; `sorts` maps each to
its sort. A record whose predicate and kind pair has no row is refused by
the tool, never typed under a nearest row.

The typing tools (`type_corpus_claims.py`, the reproduction's `type_target`)
resolve through the named contract's `term` for a local sort and pass a
namespaced one through, exactly as the compile does (§4.3). The plan is a
heritage mapping from a corpus's spelling to operator terms, not an operator
roster; M7's "no second authored operator artifact" is respected because
every runtime form is still compiled from `ProfileSpec`, and the plan can
name nothing the contracts do not declare.

## 4. The cross-contract slot rule

### 4.1 Grammar

Wherever a contract names a sort — an operator's `arg_sorts` and a
dimension's `restriction_sort` — the value is one of:

- a **bare name**, `[a-z][a-z0-9-]*`, a sort this contract declares; or
- a **namespaced reference**, `<namespace>/<name>`, a sort another compiled
  contract declares.

Both sites take both forms through one resolver. Two spellings are refused
at parse: a reference to the contract's own namespace (`mm30/concept` inside
`mm30`), since the bare name is the only spelling of a local sort; and a
reference into `science`, since the base declares no claim vocabulary.

### 4.2 Parse

`parse_domain_contract` keeps its check for bare names ("not a sort this
contract declares") and stops there for namespaced ones: it records the
reference and defers resolution. The contract's `claim_vocabulary()`
projection — what enters content identity and the succession comparison —
carries the sort name **as written**, so a namespaced reference is a string
like any other to both.

### 4.3 Compile

`compile_profile` already walks every contract's sorts into one map keyed by
term identifier before it compiles operators. The change is ordering and a
refusal: sorts and dimensions of every contract are compiled first,
operators and dimensions' restriction sorts second, and the resolver that
today is `contract.term(local)` becomes

```text
resolve(contract, name) = name                      if name contains "/"
                        = f"{contract.namespace}/{name}"   otherwise
```

followed by a lookup in the compiled sort map. A reference the map lacks
refuses the compile with the reference and the **missing namespace** named
(`MalformedContract`, prefix-stable), so a corpus compiling `mm30` without
`biology` learns which contract it did not supply. A reference to a retired
sort follows M §7.3a's existing row: the operator is withdrawn.

`CompiledOperator` and `CompiledDimension` are unchanged in shape. Their
`arg_sorts` and `restriction_sort` already hold term identifiers; the
`contract` field stays the declaring contract's namespace.

### 4.4 The consulted walk

D §8 states the rule the code never needed: a claim reaches "the operator,
its dimensions, its argument and restriction sorts, and each sort's
vocabulary binding". `consulted_contracts` adds, per claim, the operator's
contract, then the `contract` of each compiled argument sort, then of each
compiled dimension and its restriction sort. For a same-contract operator
the set is what it was, so cut 2's D6 claim-schema arm is unaffected. For
the dogfood's claim it is `{science, mm30, biology}`.

The negative needs no new code. A corpus that types such a claim and pins no
`biology` contract refuses through the walk's existing arm — "namespace
`biology` is consulted but pinned by no corpus" — and the reproduction
records that refusal once on purpose (§6.5).

### 4.5 Identity

- `π_claim` carries term identifiers already (M §6.5); a cross-typed claim's
  projection is what a same-contract one would be. `I_claim` is unaffected
  (M8).
- A contract's content identity takes the operator schema projection over
  the names as written (§4.2). `mm30`'s identity does **not** include
  `biology`'s: a biology bump moves belief through the consulted set, never
  through `mm30`'s identity. That is D6's asymmetry, and it is why the walk
  must reach the sort's contract (§4.4).
- Succession (M6) compares the written names; a successor rewriting a
  namespaced slot is a changed `arg_sorts` and is refused as today.

### 4.6 TypeScript

Cut 20 gave the TypeScript parser the same structural refusals as Python
for domain declarations; today it refuses `arg_sorts` that "is not a
declared sort". It gains the same two forms and the same two parse-time
refusals (own-namespace, `science`), and its profile compile gains the same
unresolved-reference refusal. Payload validation stays Python-primary (F
§7.2); this slice changes nothing there.

## 5. The domain-facet read

### 5.1 The reader, in `gather`

`gather` is the one place a derivation reads a corpus, and the closure
already digests, as `observes`, the address of every `observes` input of
every matched assessment's run. For each such address the reader now:

1. fetches the dataset node when `view.holds(address)`; an observed dataset
   the view does not hold is digested by address as today and reads
   nothing;
2. reads every **namespaced** facet key present on the node that the
   compiled profile declares as attaching to `dataset`;
3. re-validates each payload through `facets.validate_payload` against the
   compiled schema — the same validator the writer ran, run again under the
   profile the derivation holds;
4. mints one `FacetRead(address, key, payload_digest)` per facet, the digest
   taken under `science.identity.v1` over the payload mapping, as
   `AssessmentValue.facet_digest` takes its own.

Unnamespaced facets are not this reader's: `empirical-observation` and the
other base facets keep their readers and their seams. The read is traced at
the `("dataset", address)` ref the trace already carries, so M1's
containment is unchanged: the ref was declared, and now it is actually read.

### 5.2 `FacetRead`

Sealed, final, frozen, and **without a field-wise constructor** — the
`__init__` raises, as `Claim`'s does, and the reader's minting classmethod
is the only route in. A ledger therefore cannot be authored by a caller and
handed to the walk; F §5.6's "never from a caller" becomes a property of the
type. The class carries `address`, `key`, `payload_digest`, and a
`projection()` of the three in that order.

### 5.3 `Records`, and the walk

`Records` gains `observed_facets: tuple[FacetRead, ...]`, sorted, and
`gather` fills it. Two consumers:

- **`consulted_contracts`** derives `facets_read` from the rows, keyed by
  address. The `closure_nodes` it receives from `evaluate` grow to include
  the observed addresses, which are closure members already, so the
  existing "not a closure node" arm now guards a `FacetRead` naming an
  address no matched run observes. `node_corpus` need not map dataset
  addresses; the corpora selection skips unmapped nodes as it does today.
- **`build_closure`** takes the rows as a new argument (§5.4).

`evaluate`'s own `facets_read={}` and `gather`'s go away; there is one
source, the reader, and one carrier, `Records`.

### 5.4 The closure member

The projection gains `"observed_facets": [[address, key, digest], …]`,
sorted, **always present** (decision 7). Consequences, all stated:

- A payload byte change on an observed, held dataset moves
  `belief_input_digest` with every other member fixed. This is new; D6's
  row did not claim it and §7 files it as B5.
- Every existing belief digest moves once when this lands. The reproduction's
  step 10a re-derive will not reproduce the digest recorded on 2026-09-05,
  and the record is amended to say why (§10).

Nothing about the verdict changes. `science.belief.v1` weighs `outcome`
alone; a domain payload is reported and digested exactly as `applicability`
is under P6.

### 5.5 Refusals

- A declared facet whose payload fails re-validation refuses the derivation:
  `Refused("facet-payload-refused: <facet>, <field>, <reason>")`, wrapping
  `FacetPayloadRefused`. A payload the writer accepted under an earlier
  contract that the current profile rejects is a real disagreement, not
  noise to drop.
- A namespaced key on the node that the profile does not declare refuses:
  `Refused("facet-undeclared: <key>")`. The profile the derivation runs
  under is stale against the corpus.
- A `FacetRead` whose address is not an observed dataset is malformed at
  the walk (existing arm).
- An observed dataset not held reads nothing and refuses nothing.

Every message is prefix-stable.

### 5.6 What D6's facet arm measures

On the dogfood: the GSE179929 node carries `biology/gene-axis` (§6.4); the
read fills the ledger; a biology contract bump with payload and every
assessment byte fixed moves the digest; an unrelated activated domain's bump
leaves it unchanged; a payload byte change moves it. The first three are D6
as written; the fourth is B5.

## 6. Location, packaging, and the measurement

### 6.1 The pack

The normative file is `domains/biology/CONTRACT.yaml` at the repository
root. A build-time copy at `python/src/beliefs/domains/biology/CONTRACT.yaml`
is held byte-identical by a test, as the base copy is (F §9 item 5), and
`shipped_domain_contract("biology")` in `profile.py` parses it once per
process beside `shipped_base_contract`, with `base=shipped_base_contract()`
and `predecessor=None`. Distribution beyond the package stays open (D §12,
F §9 item 6): a caller still names the contracts it compiles, and the writer
verifies pins rather than locating documents.

### 6.2 The corpus-local contract

`mm30.yaml` under `python/tools/reproduction/`, where the placeholder
`mm30-reproduction.yaml` sits. The kernel treats a corpus-local contract and
a shipped one identically; the difference is who ships it. The two exercise
vocabularies under `python/tools/vocabularies/` stay as the heritage
artifacts they are; the reproduction's `vocabulary.py` compiles the base, the
pack and `mm30.yaml` into one profile.

### 6.3 The held concept vocabulary

The reproduction writes the 285 canonical identifiers of mm30's concept
records (`concept:<slug>`, the `id` of each record under
`entities/concepts/`) as one UTF-8 text resource, one identifier per line,
sorted by code point, terminated by a newline; holds it in the store under
its digest; and mints its dataset record, whose content address is the
`dataset:sha256:…` the `concept` sort binds. Every member must satisfy
`not_a_canonical_identifier` (resolution.py), which the tool checks before
holding, since a non-canonical member is refused at snapshot construction.

The kernel defines **no vocabulary file format** and reads no vocabulary
bytes; `build_snapshot(readable={binding: terms})` is built by the caller
from what it read, as today. The reproduction reads the held bytes back and
supplies them, so the first `member` outcome a derivation sees is measured
by the tool, not by the kernel. §12 files the kernel-side reader.

### 6.4 The reproduction re-run

The reproduction is this slice's measurement, run through its existing
driver with three amendments:

- **Step 2** types the target under the compiled profile of the base, the
  pack and `mm30.yaml`. The operator is
  `mm30/affects-concept-molecular-entity`; slot 0 resolves `member` against
  the held list; slot 1 is `biology/molecular-entity`, `not-consulted`. The
  claim identity differs from the recorded `5e702bc43fdf51d3…`, the expected
  consequence of a different operator term, and is recorded as such. The
  corpus typing tool is also run over all 307 propositions under the
  seventeen operators, which is the cost of the sort discipline the modal
  file was written to measure and could not.
- **Step 3** stamps `biology/gene-axis: {axis: rows, namespace: HGNC}` on the
  GSE179929 dataset node, validated at write by cut 20's seam.
- **Step 10** derives belief with the reader live and records the digest
  movement §5.4 predicts as a finding, not a regression.

### 6.5 Pins

`CorpusPins.domains` carries both `mm30` and `biology`. Before pinning both
the reproduction types the claim with `mm30` alone pinned and records the
walk's refusal, once, as the measured negative for §4.4.

## 7. Guarantees

The slice's own rows, prefixed B, each with a sabotage naming the check it
fails:

| id | guarantee | test | sabotage |
|---|---|---|---|
| **B1** | A slot sort resolves or refuses, at the right stage | bare name undeclared → refused at parse; `mm30/concept` inside `mm30` → refused at parse; `science/x` → refused at parse; `biology/molecular-entity` compiled with `biology` → resolves to that term; compiled without it → refused at compile with `biology` named; `restriction_sort` takes both forms identically | the resolver namespacing a namespaced name twice → the resolution test fails |
| **B2** | The consulted walk reaches every sort's contract | the dogfood claim consults `{science, mm30, biology}`; a same-contract operator's set is unchanged from cut 2; a corpus pinning `mm30` only → `ContractDisagreement` naming `biology` | the walk adding the operator's contract alone → the dogfood set lacks `biology`, the test fails |
| **B3** | `FacetRead` is minted by the reader only | no public field-wise constructor, no cast from a mapping; the only route is the reader's classmethod over a validated payload | a field-wise constructor added → the opacity test fails |
| **B4** | Every read is validated | a declared facet failing its schema → `Refused("facet-payload-refused…")`; an undeclared namespaced key → `Refused("facet-undeclared…")`; an unheld observed dataset → no read, no refusal | the reader skipping re-validation → the malformed-payload test passes a bad payload, the refusal test fails |
| **B5** | Observed facets enter the digest | payload byte change, every other member fixed → digest moves; the member is present and empty when nothing was read | the closure omitting the member → the byte-change test fails |
| **B6** | The pack ships byte-identical, and TypeScript refuses what Python refuses | packaged copy equals `domains/biology/CONTRACT.yaml`; the TypeScript parser refuses own-namespace and `science` references and an unresolved reference at compile | the copy edited → the identity test fails; TypeScript accepting `mm30/concept` inside `mm30` → the parity refusal test fails |

Rows elsewhere:

- **D6 closes.** Its facet arm and the negative's domain-facet instantiation
  run on the dogfood shape (§5.6); B5 adds the payload-byte arm as new.
- **M8 gains an arm.** An editorial `biology` bump leaves
  `I_claim` unchanged and moves `belief_input_digest`, now through a sort's
  contract rather than the operator's.
- **M6 re-runs** unchanged over a successor that rewrites a namespaced slot.
- **M7 is respected** explicitly (§3.5).
- **D1 stays partial.** Its "add a `nodes` code path" negative runs in
  `nodes`'s suite; deferred again with that reason.
- **D3 is not reopened.** The held concept list gives the first live
  `member` outcome, but D3 closed at cut 2 over a synthetic readable
  vocabulary and this measurement adds no arm to it.

## 8. Conformance cut 22

Sketch; the freeze is a separate document written after this design's
review clears, numbered after cut 21 and serialized after cut 21's
discharge, which landed 2026-09-08 (`03471da`). Selected in full: B1–B6,
D6, the M8 sort-contract arm, the M6 re-run. In part: D1, unchanged.
N2 arms sabotage, each with a named check that fails (§7). Discharged on the
certified tuple, with the reproduction's re-run (§6.4) as the measurement
rather than an arm: its findings are filed to the reproduction record, and
a refusal there is a finding through the owning lane, never a workaround.

## 9. Limitations

1. **GO, HP, EFO and MONDO stay unmeasured.** The pack binds one namespace.
2. **HGNC is bound but unconsulted.** No release is held; `molecular-entity`
   resolves `not-consulted`, which mints.
3. **The reader reports and never weighs.** A domain payload changes the
   digest, not the verdict (P6).
4. **The vocabulary line format is the caller's.** `member` on the concept
   list is measured in the reproduction, not by the kernel (§6.3).
5. **Every existing belief digest moves once** (§5.4).
6. **The pack's operator roster is three protein→protein relations shaped
   by one corpus**; 14 of mm30's 17 operators are corpus-local (§3.3).
7. **D1's `nodes` negative is deferred** (§7).
8. **Parallel genesis is unchanged** (D §12): nothing stops a second
   `biology` contract declaring `genesis`.
9. **TypeScript validates no payload** (F §9 item 10), unchanged.
10. **An observed dataset not held reads nothing**, so a derivation over an
    unheld dataset consults no domain through facets, and the digest cannot
    tell "no facet" from "not held" — the `observes` address is the same
    either way.

## 10. What changes elsewhere

- **Roadmap** `domain-boundary` row: "the biology pack — GO, HP, EFO and
  MONDO bindings and mm30's operator vocabulary" becomes the pack as §3.2
  declares it, with the corpus-local contract named and the four bindings
  deferred; D6 moves to closes-at-cut-22; D1's row entry unchanged.
- **Layer design sub-project 3**: same correction, by amendment note.
- **Parent design D §12**: the predicate-vocabulary bullet gains a note that
  an operator's slot may name another contract's sort under §4's rule; the
  "distribution" bullet notes the packaged pack as the first shipped domain
  contract, distribution itself still open.
- **Facet-contracts design** F §5.6 and F §14: the read-ledger question is
  answered here; F §9 items 3 and 6 are amended by citation.
- **The reproduction record** `2026-09-05-mm30-reproduction.md`: question 1
  gains a measured answer for the sort discipline (§6.4); §6 gains the
  re-run's findings; step 10a's digest is annotated as moved by §5.4.
- **Task `beliefs-1ce152`** gets this document as its spec; the parent
  `beliefs-bc3aff`'s acceptance line is corrected to the pack as declared.

## 11. Alternatives rejected

Recorded in §2; in one line each: one coarse sort (the unsorted plan
renamed); sort-sets or a lattice (a formal-model amendment); one corpus-local
contract with duplicated sorts (two protein types forever); the pack binding
`concept` (permanent by succession); a biology reader with a verdict effect
(needs P question 4); the ledger off the assessment's declaration (the
caller-selected digest); `observed_facets` omitted when empty
(content-dependent shape); the pack under `contracts/` (declined on
review).

## 12. Open questions this design files

- **A kernel-side vocabulary dataset reader**, so that `member` against a
  held vocabulary is kernel-measured and the line format is a contract
  rather than a tool's convention. Claims and resolution.
- **Whether a domain may weigh** — P §open question 4, unchanged; the first
  reader that wants a verdict effect reopens it.
- **The retire-and-reissue path** when a concept gains an ontology binding
  and its operators should move from a corpus-local contract into the pack:
  a successor retires the corpus-local operator and the pack issues one;
  what the corpus's existing claims then are is the referent-binding
  question M ρO1 already holds.
- **Distribution**, unchanged (D §12).
- **The HGNC release selection rule** beyond this slice's "most recent
  archive on or before the design date" — whether a pack successor may move
  the release at all, given succession makes the binding part of the sort's
  schema projection. If it may not, a release change is a new sort.
