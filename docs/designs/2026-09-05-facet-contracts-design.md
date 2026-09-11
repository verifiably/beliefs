# Facet contracts and the compiled kind registry — design (the `domain-boundary` slice, part 1)

**Date:** 2026-09-05
**Status:** designed 2026-09-05 in a brainstorming session of six sectioned
reviews, each revised on the reviewer's findings (the bearer invariant over
resulting corpus state, attestation on correction, stamp coverage kept apart
from consultation, the base-versus-domain mismatch stopping rule, guarded
publication under the operation lock, typed parity-fixture inputs, and the
oracle corrections in §8), then on a written review of the committed
document whose seven findings became §2 items 1, 2 and 6, §3.1's relation
groups and `display`, §3.7, §4.2's coverage order, §5.5's enumeration and
audit stop, and F2 and F4's added cases; then on the plan review of 2026-09-05, whose
thirteen findings amended §3.1 (prose kinds and `role`), §3.5 (no null in a
projection), §4.1 (the registry is private), §5.1 (the port holds the profile
and every port method rechecks), §5.2 (provenance mode threaded through import,
relocation and consolidation) and §7.1 (validated reads, never construction).
**Conformance cut 20 frozen 2026-09-06** (`2026-09-05-conformance-cut-20.md`), before implementation.
Implemented on the `domain-boundary` lane through the integration and cut-20
acceptance surface (2026-09-07); the certified aggregate passed and cut 20 is
discharged. Landed on `main` on 2026-09-07; biology slice 2 was subsequently
implemented and discharged at cut 22 on 2026-09-08.
**Scope:** the first of two slices on the `domain` lane, anchored on the
empirical-observation facet's payload contract, kernel §11's open question
and the mm30 reproduction record's first filed finding
(`2026-09-05-mm30-reproduction.md` §6 step 3, task `beliefs-d245a9`). The
slice builds the mechanism the contract needs and every D row deferred on
it since cut 3: facet declarations in the base and domain contracts, the
compiled per-kind registry (D4), Science-side payload validation at every
write seam, the bearer invariant, attestation binding, the shipped base
profile, the pin recheck under the operation lock, the consulted walk's facet
arm, the practice loader, and the second `science.identity.v1` parity
fixture. The second slice, the biology domain pack, rides this mechanism
unchanged and is designed separately.
**Inherits:** the domain-extension boundary design
(`2026-08-04-domain-extension-boundary-design.md`) §2–§8 (the ownership
split, interpretation as facet conjunction, the compiled registry, the
manifest profile, what enters identity and belief) and its D table; kernel
§4.1 (the eligibility predicate and the role-typed inputs), §2.2 (held) and
limitation 8; computation §4.7 (the acquisition boundary at the most upstream
held form, and the acquisition provenance record); the formal model
(`2026-08-04-formal-model-and-claim-calculus-design.md`) §6 and §8's
second-fixture obligation; the composition-root adapter design
(`2026-08-18-composition-root-adapter-design.md`) §5's stamp rules; the
family-adapters design (`2026-08-19-family-adapters-design.md`) for `revise`
and `supersede`; the write-permits design (`2026-09-04-write-permits-design.md`)
for `Authority`, `ActorMismatch` and the actor-binding rule; the act-report
design (`2026-08-11-act-report-design.md`) for the `acquisition` operation
kind and the unfulfilled-intent state; the world-registry design
(`2026-08-20-world-registry-design.md`) for the manifest and its pins. Where
those documents decide a point this one cites it.
**Out of scope:** the biology pack and every real vocabulary binding (slice
2); URL acquisition itself (`url-retrieval`) — F7's positive arm tests
reference acceptance over an imported report, not acquisition; lineage-inherited observation standing (§14); relation
endpoint enforcement at write (§9); migrating any reader-shaped facet to a
schema; contract distribution (D §12); any `science` code.

**Sources, read at design time:** `python/src/beliefs/stored.py`,
`corpus.py`, `profile.py`, `consulted.py`, `admission.py`, `dataset.py`,
`production.py`, `runrecord.py`, `boundary.py`, `root.py`, `permit.py`,
`relocation.py`, `audit.py`, `errors.py`, `contract/base.py`,
`contract/domain.py`, `contract/coordination.py`, `holdings/records.py`,
`holdings/adapter.py`, `world/registry.py`, `world/epoch.py`;
`contracts/science/CONTRACT.yaml`, `fixtures/contracts/testing.yaml`,
`fixtures/claim-identity-v1.json`; `ts/src/contract.ts`, `ts/src/profile.ts`,
`ts/README.md`, `ts/tests/identity-v1.test.ts`; the `nodes` package's
`core/registry.py`; `python/tests/test_designs_corpus.py`,
`tests/n2_arms_cut4.py`; `python/tools/reproduction/hold.py`,
`vocabulary.py`, `close.py`; the reproduction corpus's stored dataset and
holdings-observation records; the roadmap
(`../plans/2026-08-29-implementation-roadmap.md`) rows 3 and its lanes
table; tasks `beliefs-bc3aff` and `beliefs-d245a9`.

---

## 1. Problem

The empirical-observation facet is the hinge of eligibility and nothing
reads its payload. The reproduction record measured that directly: the
driver authored `{boundary: acquisition, source: dataset:gse179929,
asserted_by: mm30-reproduction}`, `is_empirical_observation` read presence
only, and the dataset was admitted. Nothing refuses a dataset that is not an
observation.

Underneath, the cause is structural, and it is why the finding belongs to
this lane. No contract declares any facet's schema: the base contract
declares the claim grammar and nothing else, and a domain contract declares
sorts, dimensions, operators and vocabulary bindings, never a facet. The
kernel's per-kind inventory — `WORLD_KINDS`, `WORLD_RELATIONS`,
`SEMANTIC_DOMAINS`, `COVERED_FACETS` — is authored in `stored.py`, which is
exactly the second authored per-kind source D4 retires; D §6 said "every
per-kind artifact is compiled from" the profile source, and `profile.py`'s
own docstring records that only the claim-schema half was built. The writer
validates the `nodes` document model and nothing more, sees a compiled
profile only through the optional coordination resolver, and checks no
kind's existence, so G5 is open too. Every D row deferred since cut 3 —
"facets, manifests, and the registry compile" — is deferred on this one
missing mechanism, and the roadmap's row 3 names the payload contract as
the thing to decide in it.

Two facts narrow the question. **Heldness is already gated:** the admission
gate refuses `input-not-held` from holdings observations (G2b), so "carries
the facet versus merely claims it" cannot be about whether the bytes are
here. And **today's correction paths do not reach a dataset:** `revise` and
`supersede` are propositions-only, so D2's "correct the facet's payload" arm
has never been reachable and D10's "ordinary node revision" has never
existed for the records it describes.

## 2. Decisions

1. **Bearer invariant.** The facet declares an acquisition boundary
   (computation §4.7: the most upstream held form), so no dataset may carry
   the facet and a producer. The invariant is over the **resulting corpus
   state** and is checked at every entry of either half: a dataset write
   carrying the facet is refused if any `produces` edge already targets it
   or it carries a lineage basis; **any write carrying a `produces` edge,
   whatever its carrier's kind**, is refused if a target resolves to a
   facet-bearing dataset — endpoint enforcement is deferred (§9 item 2), so
   the check keys on the edge, never on the carrier. `import_bundle`
   evaluates it over the existing corpus overlaid with every proposed member,
   so admission is order-independent; the production-run boundary evaluates
   it under the publication lock (§5.4); `corpus_check` reports it. Whether a
   produced dataset can inherit standing through its lineage basis is filed
   (§14), not decided.
2. **Payload.** A closed schema: `locator` (required, one string under the
   closed scheme set `accession`, `url`, `instrument`), `attested_by`
   (required, bound to the writer's actor at mint and on a changed
   declaration, preserved as provenance on import, relocation and unchanged
   revision), `retrieval` (optional, an `act-report` ref that must resolve
   to an `acquisition` operation when present). Unknown keys are refused. No
   boundary-kind enum: the locator's scheme carries it and nothing reads a
   finer distinction, which is rule 2.6's reader clause applied to this
   design's own field.
3. **Attestation is declaration data, not D10's forbidden operation.** D10
   forbids an API whose object is an individual facet payload. `attested_by`
   is a field inside the one payload written by the same act that writes the
   declaration; it cannot be addressed separately, and correcting it leaves
   no record of the prior claim, which is exactly the cost D10 states. The
   promotion trigger — independent authorship, competing alternatives,
   retraction — stays unfired: one declaration per dataset, one attester, and
   withdrawal of standing remains the correction lifecycle's open
   record-level question (its §9), so removing the facet is refused.
4. **Declarations live in the contracts.** The base contract gains `kinds:`
   (the thirteen world kinds), `relations:` (kernel §4.1's closed relation
   vocabulary with source and target kinds) and `facets:` (unnamespaced
   payload declarations). A domain contract gains `facets:` (namespaced,
   each naming the kinds it attaches to) and is refused if it declares
   `kinds:` or `relations:` (D8). Two contributions to one facet key are
   refused at compile.
5. **The grammar is closed and structural** (§3.4): six field types, an
   explicit `required` boolean, `kinds` only with `ref`, `schemes` only with
   `locator`, no patterns, no nesting, no defaults. Small enough that both
   languages parse it and Python alone validates payloads.
6. **Two facet shapes.** Every facet a builder writes is declared. The
   existing kernel facets are `shape: reader`: declared and covered, their
   payload shape enforced only as far as their named reader goes (§3.2 says
   exactly how far). `empirical-observation` is the one `shape: schema` facet
   in this slice; domain facets are schema-shaped from slice 2. `display`
   is declared reader-shaped on `proposition` and `dataset` and keeps its
   hand-coded check, because that check accepts an empty statement and a
   schema would change behaviour this slice has no ruling for.
7. **The compile produces the per-kind artifacts** (§4): compiled kinds,
   compiled facets, one `nodes` `KindSpec` registered per kind in one
   `Registry`, and one compiled validator per schema-shaped facet.
   Compilation reads kinds and relations from the parsed base contract only
   and imports nothing from `stored`.
8. **Coverage is contract-declared; consultation is separate.** The semantic
   stamp covers base-profile facets declared `covered`; domain facets enter
   node content identity and corpus state (D2) but not the stamp. This amends
   the composition-root adapter design's "coverage is code" to "coverage is
   contract-declared, never stored per node" — the defence it named, a
   per-node list an untrusted writer could shorten, is untouched. Consultation
   (D6) is the walk in `consulted.py`, which gains a facet arm keyed on
   facets a derivation **read**, never on facets present.
9. **The shipped base profile.** `stored.py`'s inventories become views over
   a profile compiled once, at import, from the base contract carried as
   package data. A writer's profile, a manifest's `science_contract` and a
   read view's corpus must pin that base identity or are refused, never
   reinterpreted — the same shape as `TAG_ENCODING`. This is why no read
   entry point gains an argument.
10. **The writer holds the profile** as a required keyword and rechecks pin
    agreement under the operation lock before every write (§5.1).
11. **`KIND_ACTS` stays authored** in `permit.py`, its static test comparing
    against the compiled inventory. D4's forbidden artifact is one describing
    a kind's shape — `KIND_DESCRIPTORS`' old role; act routing is write
    policy under E4, and compiling it would add scope without improving
    payload validation.
12. **Practices** get a minimal `PRACTICE.yaml` loader that refuses
    vocabulary, sorts, dimensions, operators, facets and kinds; `compile_profile`
    takes no practice, so D9's "contributes nothing" holds by construction.
13. **Identity consequences.** The base contract's content identity moves. No
    corpus migrates: the reproduction corpus is recreated by re-running the
    driver in a fresh directory, its hold step declaring
    `locator: accession:GSE179929`.
14. **The acquisition-boundary validity predicate** is one function, reused
    wherever a dataset's standing is judged: the facet is present, its
    payload validates under §6, the dataset has no producer and no lineage
    basis, and `retrieval`, when present, resolves to an `acquisition`
    report. Actor binding is a write rule (§5.3) and is **not** part of it.
    The write seams, `corpus_check` and `eligibility_refusal` all call it.
15. **TypeScript** parses the new sections with the same structural
    refusals and validates no payload. The second parity fixture is
    values-level over `identity.v1` with typed inputs (§7.3).
16. **Rows.** D2, D4, D5, D8, D9, D10 and G5 are targeted in full, D1 in part,
    D6 not on its facet arm; each discharges only on its full oracle. New rows
    take prefix `F` (§8).

## 3. Declarations and grammar

### 3.1 The base contract's `kinds:` and `relations:`

One `kinds:` entry per world kind, thirteen today, transcribed from
`stored.py` without change of meaning. A governed kind names its semantic
`domain` and its facets, each `required` or `optional` and `covered` or not.
The stamp facet `semantic-identity` is not declared per kind: it is minted by
the boundary on every governed kind and is implicit. The two deferred kinds,
`instrument-certification` and `coreference-attestation`, are declared with
no domain and no facets, so `world/epoch.py`'s ungoverned-kind refusal keeps
firing exactly as it does now and stops firing the day a charter declares a
domain.

> **2026-09-10:** `coreference-attestation` gained its domain and facet at world resolution slice 2; `instrument-certification` is the one kind still deferred.

```yaml
kinds:
  proposition:
    domain: science.proposition.v1
    facets:
      proposition: { required: true,  covered: true }
      display:     { required: false, covered: false }
  dataset:
    domain: science.dataset.v1
    facets:
      dataset:               { required: true,  covered: true }
      empirical-observation: { required: false, covered: true }
      lineage-basis:         { required: false, covered: true }
      display:               { required: false, covered: false }
  run:
    domain: science.run.v1
    facets:
      run:         { required: true,  covered: true }
      run-closure: { required: false, covered: true }
  instrument-certification: {}
  coreference-attestation: {}
  # source-assertion, assessment, analysis-spec, verification, source,
  # holdings-observation, retraction, act-report: one required covered facet
  # of the same name, under the domain stored.py names today.
```

The first covered facet of each kind is required, which is what
`_validate_import_bundle` already enforces by position; the declaration
makes it explicit. Coordination kinds keep coming from the coordination
contract and register in the same registry.

> **Amended 2026-09-05 (plan review): prose kinds and `role`.** Kernel §4.4's
> belief-inert notes — `interpretation`, `discussion`, `story` — are
> hand-authored records with no semantic domain that today's writer admits and
> a closed registry would refuse. They are declared under `kinds:` with
> `role: prose`: no domain, `display` optional, no other facet; a prose kind
> declaring a domain or another facet is refused at load. `role` defaults to
> `world`. `WORLD_KINDS` derives from the `world` kinds alone, so its membership
> is unchanged; a prose kind carries no stamp and enters no closure, as before,
> and a domain facet may not attach to one. `memo`, the test suites' prose
> kind, is not a kernel kind and the tests move to `discussion`.

`relations:` lists kernel §4.1's closed vocabulary in two named groups,
each relation with its source and target kind sets: the **`world`** group is
today's eleven (`assesses`, `observes`, `reads`, `transforms`, `produces`,
`produced_by`, `executes`, `targets`, `verifies`, `member_of`,
`grounded-in`), and the **`lifecycle`** group is `supersedes`, `retracts`,
`succeeded-by` and `anchored_in`. `WORLD_RELATIONS` derives from the `world`
group alone, so the coordination contract's query vocabulary is checked
against exactly the set it is checked against today, and a coordination
contract naming a lifecycle relation stays refused — a test holds that. Slice 1 compiles them and enforces
nothing new at write (§9 item 2); their declaration is what gives D8's
relation-signature refusal a declaration to refuse against, and what breaks
the import cycle §4.3 removes.

### 3.2 The base contract's `facets:`, two shapes

Every facet named under `kinds:` is declared here, in one of two shapes.

**`shape: reader`** declares that the key exists, whether the stamp covers
it, and which reader decodes it. It is **not** a payload guarantee, because
the readers are uneven, and the declaration names each one beside its
limit:

| facet | reader | what it refuses | what it accepts |
|---|---|---|---|
| `dataset` | `dataset_declaration` | a resource entry that is not an object (`MalformedRecord`) | a missing or non-list `resources` reads as an empty declaration; names coerced with `str`; the write-time refusal that bites is `_refuse_missing_basis` (every resource pinned) |
| `run` | `run_spec` | nothing | a non-string spec reads as `None` |
| `run-closure` | `runrecord`'s projection reader | a malformed projection at replay | — |
| `assessment` | `assessment_value` | an absent facet | five fields coerced with `str`; non-string optionals dropped; the closed outcome set is enforced at audit (`derivation-malformed`), not here |
| `verification` | `verification_value`, `verification_derivation` | an absent facet; a malformed `derivation` member (strict, M11) | `assessment`, `scope`, `verdict` coerced with `str` |
| `lineage-basis` | `_tagged_basis_routes`, `basis_routes` | a basis not shaped `{tag, routes}`; a route that is not an object | — |
| `holdings-observation` | `holdings_observation_value` | any shape fault (strict) | — |
| `retraction` | `_validated_retraction_facet` at write | a malformed target or arm | — |
| `proposition` | `decode.py`'s claim decoder | missing or extra keys, refused never repaired | — |
| `source` | `external_identifiers` | nothing at read; W3's refusal at write when no accepted identifier is present | unknown identifier names ignored |
| `identifier-correction` | `identifier_corrections`, `validate_source_history` | malformed entries, non-canonical identifiers, broken continuity, duplicate tokens, no-op events, terminal disagreement, or a redirect list differing from the history-derived held addresses | absence, as an empty correction history |
| `display` | `display_facet_malformed` | anything but the exact one-field shape `{display_statement: <str>}` | an empty statement; declared optional and uncovered on `proposition` and on `dataset`, which §5.3's revision arm may change |
| `source-assertion`, `analysis-spec`, `act-report` | their own value readers | as those readers do | this design does not audit them |

> **Amended 2026-09-10 (slice 2b):** `identifier-correction` is a reader-shaped,
> optional, uncovered source facet. Its named reader is `stored.identifier_corrections`;
> `stored.validate_source_history` applies the history and redirect contract together.

Reader strictness is recorded as a limitation (§9 item 1). No reader-shaped
facet migrates to a schema in this slice.

**`shape: schema`** carries `fields:` and gets a compiled validator. In
slice 1 exactly one facet is schema-shaped, `empirical-observation` (§6).
The grammar is still exercised on namespaced facets through the synthetic
`testing.yaml` contract, which gains two fixture facets for D2, D8 and F8.

### 3.3 A domain contract's `facets:`

Keys are `<namespace>/<name>`, the namespace being the contract's. Each
declares `attaches_to:`, a non-empty set of kernel kinds — an unknown kind or
a coordination kind is refused at compile — and `fields:` under §3.4. Domain
facets are always optional and never covered. A domain contract declaring
`kinds:` or `relations:` is refused at load.

### 3.4 The schema grammar

```yaml
fields:
  <name>: { type: <type>, required: <bool>, kinds: [...]?, schemes: [...]? }
```

- `name` matches `[a-z][a-z0-9_]*`; duplicates are unrepresentable.
- `type` is one of `string` (non-empty), `integer` (an int, never a bool),
  `boolean`, `ref` (`<kind>:<local>` with `kind` in `kinds` and a non-empty
  local), `locator` (`<scheme>:<rest>` with `scheme` in `schemes` and a
  non-empty rest), `actor` (a non-empty string; its binding is the writer's
  rule, §5.2).
- `required` is a mandatory boolean.
- `kinds` is required for `ref` and refused for every other type; `schemes`
  is required for `locator` and refused for every other type. Both are
  non-empty sets of distinct names. Declared `kinds` are resolved at compile
  against the compiled inventory; an unknown kind refuses the compile.
- A payload is refused for an unknown key, a missing required field, a null,
  or a nested value. No patterns, no defaults, no nesting.

A `ref` field's **resolution** — whether the named record exists and is of
the right sort — is a seam rule (§5.2), never the grammar's.

### 3.5 What enters `compiled_identity`

Every behavioural declaration: the kind inventory with each kind's role, its
domain **when it has one** (an undomained kind carries no `domain` key at all,
since `science.identity.v1` refuses null and a projection with a null could
never be digested), and each facet's `required` and `covered` flags; every relation's source and
target sets **and its group** (`world` or `lifecycle`, §3.1) — moving an
unchanged relation between groups changes coordination-vocabulary
acceptance, so a test moves one and asserts the compiled identity moves; every facet's shape discriminator; every schema field's
projection (`type`, `required`, `kinds`, `schemes`); every domain facet's
`attaches_to`. Changing which kind accepts a facet moves the compiled
identity with no field change. Descriptions stay out, as they do for
operators. Content identity is unchanged in kind: the raw root, as today.

### 3.6 Practices

`PRACTICE.yaml` carries `practice`, `version`, `description` and `guidance`
(a list of paths). Any other key — `vocabulary`, `sorts`, `dimensions`,
`operators`, `facets`, `kinds` included — is refused at load with
`MalformedContract`. Nothing consumes a practice at compile.

### 3.7 Document load refuses duplicate keys

PyYAML's `safe_load` keeps the last of two equal mapping keys, so a
duplicate facet, field, kind or relation declaration would vanish before
compilation ever reached D8's collision check. Both Python contract loaders
(`load_base_contract`, `load_domain_contract`, and the coordination and
practice loaders with them) parse under a loader that refuses a duplicate
key at **every** mapping level with `MalformedContract`, nested declarations
included. The TypeScript side's `yaml` parser already refuses duplicates by
default; the design keeps that default and tests it, so both languages
refuse the same document for the same reason.

## 4. The compile

### 4.1 Compiled products

`compile_profile` adds two read-only tables to `ProfileSpec`:

- **`kinds`**: `CompiledKind(name, domain | None, facets: {key: (required,
  covered)}, contract)`, the base's thirteen plus the coordination contract's
  kinds when one is compiled.
- **`facets`**: `CompiledFacet(key, shape, attaches_to, fields, contract)`.

A domain facet attaching to a kind the base does not declare, or two
contributions to one key, refuse the compile (`DuplicateContribution`,
`ProfileError`). From `kinds` the profile builds one `nodes` `Registry`,
calling `register` once per kind with the required and optional key sets.
That registry is what makes an unknown kind refusable (G5) and an undeclared
facet key refusable, with `nodes` learning nothing about what any key means
(D1): the keys it receives are opaque strings, as its own fixtures already
carry `bio-axes`. **The registry is private** (amended 2026-09-05, plan
review): a registry handed out exposes `register` and mutable `KindSpec`s, so
a caller could change validation behaviour without moving a pin or the
compiled identity. A writer refuses a port whose profile differs in base
identity, activated pins or compiled identity — any one of the three. The profile exposes `validate_document(node)` and
`document_violations(node)` and nothing else; every compiled mapping, the
nested ones included, is read-only. For each schema-shaped
facet the profile compiles a validator over §3.4; reader-shaped facets
validate no further here.

### 4.2 The shipped base profile

`beliefs.profile.shipped_base()` returns the profile compiled once, at
import, from the base contract carried as package data. A test holds the
packaged copy byte-identical to `contracts/science/CONTRACT.yaml`, which
stays the normative file both languages read; a drift is a failing test, not
a silent second contract.

**Coverage order is deterministic and not the authored order.**
`semantic_projection` emits `present` in coverage order, and a contract's
identity ignores mapping order, so deriving coverage from the authored map
would let one contract identity yield two stamps. Coverage is the kind's
`covered` facets **sorted by key, by code point** — which is exactly today's
`COVERED_FACETS` order for every kind (`dataset`, `empirical-observation`,
`lineage-basis`; `run`, `run-closure`), so no existing stamp moves. A test
reorders the declarations under `kinds:` and `facets:` and asserts the
compiled identity and every semantic stamp are unchanged. `stored.py` keeps the names `WORLD_KINDS`,
`WORLD_RELATIONS` (the `world` group only, §3.1), `SEMANTIC_DOMAINS` and
`COVERED_FACETS` as views over the shipped base's compiled kinds and
relations, so the twenty existing readers
of those names — `permit.py`'s static inventory test, `view_query.py`,
`world/epoch.py`, `relocation.py` among them — do not change.

### 4.3 No import cycle

`profile.py` currently imports `stored` for the coordination vocabulary
check. With `stored` initializing from `shipped_base()` that edge reverses:
compilation reads kinds and relations from the parsed base contract, checks
coordination query kinds and relations against them, and imports nothing
from `stored`. `stored` imports `profile`; `profile` imports `contract.*`
and `identity` only.

## 5. The seams

### 5.1 The writer and the pin recheck

`CorpusWriter` takes `profile: ProfileSpec` as a required keyword. At
construction it refuses a profile whose base identity is not the shipped
one (`ContractMismatch`) — an early failure only. Every write path rechecks
**under the operation lock, before any effect**: if the corpus has a
manifest, its `science_contract` must equal the profile's base identity and
its `domains` must equal the profile's activated contracts, or the write is
refused with `ContractMismatch` and nothing is written. `adopt_manifest`
writes only pins equal to the held profile. A mounted coordination resolver's
profile for this root must carry the same identities. A later manifest
change — raw, or adoption elsewhere — is caught at the next write.

> **Amended 2026-09-05 (plan review): every effect, every port method.** The
> recheck sits inside every lock-held primitive that reaches an effect — the
> ordinary writes, the relocation helpers (`_add_locked`, `_replace_locked`,
> `_delete_locked`, the report publication), the operation-intent append — and
> a static inventory over `corpus.py`, `relocation.py` and `root.py` holds that
> set closed, in the write-permits design's manner. The operation port holds
> the same profile (the writer refuses a port holding another) and
> `append_intent`, `execute`, `execute_fulfilling` and the guarded form each
> recheck under their own lock, so assessment publication and every refusal
> report are covered, not only guarded production publication. Holdings acts
> reach the chain through the store seam, which holds neither: the act context
> holds the profile, the seam carries the corpus lock, and the boundary rechecks
> under it before its intent and again before its publication.

### 5.2 `_refuse_facets`

One new preflight step, run in `_refuse` after document validation and
before the stamp check, and in `_preflight_replace_locked`:

1. **Registry validation**: the kind is registered and every facet key is
   declared for it (`ValidationRefused`, codes `kind-unknown`,
   `facet-unexpected`, `facet-missing`).
2. **Payload validation** of every schema-shaped facet present
   (`FacetPayloadRefused`, naming facet, field and reason).
3. **The bearer invariant** over the view the caller passes.
4. **Attestation binding** (§5.3).
5. **`retrieval` resolution**: when present, the ref resolves through the
   view to an `act-report` whose `operation` is `acquisition`; otherwise
   refused (`FacetPayloadRefused`, reason `retrieval-unresolved`).

`add` runs all five and binds the actor. `import_bundle` runs the same step
per member over the `_ImportView` with attestation exempt as provenance.
Relocation runs steps 1, 2, 3 and 5 against the **destination** corpus (its
pins, its view, its records: a `retrieval` that does not resolve there refuses
the move) and preserves the attestation.

> **Amended 2026-09-05 (plan review): provenance mode, and the producer read.**
> The exemption is a `provenance` flag threaded through every preflight and
> lock-held write helper (`_refuse`, `_preflight_add_locked`, `_add_locked`,
> `_preflight_replace_locked`, `_replace_locked`), set by import, by
> relocation's move at every one of its calls, and by consolidation's
> replacement of the survivor — never a separate exempt check beside a binding
> one, which the binding one would refuse first. The producer read cannot be
> `inbound`, which requires its target to resolve and so cannot see a dataset
> at its first write or a dangling `produces` edge; both views scan stored
> relations over the **resulting** index — existing records, arriving members,
> deprecated-id aliases, targets that resolve to the dataset — and the check's
> own view reads neighbours unvalidated (§5.5). The candidate is itself part of
> the resulting state: a facet-bearing dataset whose own `produces` names
> itself, by id or alias, is refused before the view is consulted.

### 5.3 Attestation and the dataset revision arm

`attested_by` must equal the authority's actor on `add`, and on a `revise`
whose declaration (`locator`, `retrieval`) differs from the stored one; on a
`revise` whose declaration is unchanged it must be unchanged; any other
combination is `ActorMismatch`. Concretely: Alice mints; Bob revises the
locator retaining Alice → refused; naming Bob → accepted; Alice revising her
own with Alice retained → accepted. Import and relocation keep a foreign
attester byte for byte.

`revise` gains a dataset arm. A dataset revision must preserve `id`, `uid`,
`kind`, `relations`, `deprecated_ids`, the `dataset` facet and the
`lineage-basis` facet byte for byte. It may change `title`, `body` and
`display`; add or change `empirical-observation`; add, change or remove
namespaced domain facets. Removing `empirical-observation` is refused (§2
item 3). Adding it to a previously unmarked dataset mints its declaration:
the bearer invariant applies and `attested_by` must be the bound actor. The
stamp is recomputed and is the only other field that moves; anything else is
`ReviseOutsideAllowlist`. Propositions keep today's prose-only arm.

### 5.4 Guarded production publication

The production-run boundary publishes through `execute_fulfilling`, which
takes the operation lock and writes a plan directly, never through
`CorpusWriter.add`. The port gains a guarded form: under the lock it first
rechecks pin agreement (§5.1), then evaluates a guard over the corpus at that
root, then executes exactly one plan — the run's publication plan, or on a
reason the refusal report's plan — both fulfilling the same intent. The
production boundary uses it with the bearer invariant as the guard,
converting a minted result into `RunRefused("acquisition-boundary")` exactly
as `recipe-identity-mismatch` converts one today. **Permitted effects on
refusal:** the `run-attempt` intent and its refusal report stand on the
chain; no run record and no produced-dataset publication occur; the store is
untouched.

**Pin failure after the intent exists.** A pin mismatch found under the lock
forbids publication of anything, the refusal report included, since the
report would pass through the same gate. The intent therefore stays
**unfulfilled**: the act-report design already derives an unfinished
operation from an intent without a report (its §6.6 reading), reconciliation
and the audit see it as such, and the boundary raises `ContractMismatch` to
its caller. This is stated rather than papered over; an authorized reporting
path that bypasses the gate is not designed here.

### 5.5 The check and the audit

`corpus_check(view, profile)` and `audit_corpus(view, evidence=, profile=)`
take the compiled profile. Both read through `iter_stored`, which stays
unvalidated, so a mismatch is reported without triggering the facade's
refusal on `get`. Two mismatch outcomes, one finding code:

- **Domain pins disagree, base agrees.** One `profile-mismatch` finding.
  **Withheld:** every judgment on a namespaced facet key — `facet-unexpected`
  and `facet-missing` for namespaced keys, domain payload validity — and,
  when the `coordination` pin is among those disagreeing, every judgment only
  the coordination contract can make: the kind and key judgments and the
  coordination-facet checks for a record whose kind is outside the shipped
  base's inventory (amended 2026-09-05, plan review: the shipped inventory,
  never the supplied profile's coordination kinds and never the facet's
  presence, decides which those are, so a base kind that gained a stray
  `coordination` facet keeps every base judgment and a coordination record
  that lost its facet is still withheld). **Still reported**, because the shipped base decides them alone:
  `manifest-malformed`; stamp findings; kind existence for unnamespaced
  kinds; `facet-unexpected` and `facet-missing` for unnamespaced keys;
  `empirical-observation` payload validity; the bearer invariant; retrieval
  resolution; eligibility; retraction-target and lineage findings.
- **`science_contract` disagrees.** One `profile-mismatch` finding and
  `manifest-malformed` if it applies; **everything else withheld**, stamp
  judgments included, since judging stamps under a base the corpus does not
  pin is the reinterpretation §7.1 forbids. `audit_corpus` performs **no
  recomputation** in this state: its helpers read through `view.get`, which
  would raise `ContractMismatch` on the first record, so the audit returns
  the mismatch finding and stops rather than letting the refusal escape.

Under an agreeing profile the check reports `kind-unknown`,
`facet-unexpected`, `facet-missing`, `facet-payload-malformed`,
`facet-bearer-produced` and `facet-retrieval-unresolved`, never raising.

`eligibility_refusal(view, node, profile)` reads **validity** through the
acquisition-boundary predicate (§2 item 14), so an observes input
qualifies only when the facet is present, its payload validates, the
dataset has neither producer nor lineage basis, and its `retrieval` resolves
if present. A raw-written dataset carrying both a valid facet and a basis,
or a declaration whose acquisition report has since been deleted, confers
nothing. The existential rule is preserved: an `assesses` edge is admissible
when at least one observes input qualifies; a second observes input with an
invalid facet does not make the edge inadmissible and is reported separately
as `facet-payload-malformed`. An edge with no qualifying input is refused
with a reason that distinguishes *absent* from *present but invalid*.

### 5.6 Consultation

`consulted_contracts` gains `facets_read`, the namespaced keys each
derivation read per closure node, resolved namespace to pin exactly as the
operator arm does. Evaluation and belief pass it empty in slice 1, which is
the honest state: no derivation reads a domain facet yet, and a
caller-selected consulted set would be exactly the digest that cannot fail.
`facets_read` must eventually come from the readers' own execution — a read
ledger the first domain reader fills in slice 2 — never from a caller.

> **Answered 2026-09-08** by the biology-pack design §5 and cut 22: the domain
> reader mints authenticated receipts from its own reads, and `gather` derives
> `facets_read` from those receipts.

### 5.7 Refusals

`FacetPayloadRefused(ValidationRefused)` naming facet, field and reason;
`AcquisitionBoundaryRefused(WriteRefused)` for the bearer invariant; the
existing `ActorMismatch`, `ContractMismatch`, `ReviseOutsideAllowlist` and
`ImportRefused` (which keeps wrapping a member's refusal with the member
named and the underlying refusal as `__cause__`). Every message is
prefix-stable.

## 6. The empirical-observation contract

In the base contract:

```yaml
facets:
  empirical-observation:
    shape: schema
    fields:
      locator:     { type: locator, required: true,  schemes: [accession, url, instrument] }
      attested_by: { type: actor,   required: true }
      retrieval:   { type: ref,     required: false, kinds: [act-report] }
```

Kernel §4.1 is amended to say what "declared acquisition boundary" means:
the locator names the most upstream form outside the held boundary; the
attester is the actor who declared it; `retrieval` is the boundary-minted
acquisition report when one exists, the member computation §4.7's provenance
record already reserves. The bearer invariant is written into §4.1 beside
the eligibility predicate. Kernel limitation 8 narrows to what stays
authored: that the locator is the true origin, and that the bytes are an
observation of the world rather than, say, a literature corpus with an
accession. Kernel §11's question closes; §14 records what it opens.

The reproduction's authored `{boundary, source, asserted_by}` is refused by
this contract on three counts (unknown keys, no locator, no attester), which
is the test F1 names.

## 7. The read side, TypeScript, and the second parity fixture

### 7.1 The read side

`ReadView._validated` keeps verifying stamps only, now under the shipped
base's declared coverage, and additionally refuses a corpus whose manifest
pins a different `science_contract` (`ContractMismatch`), never
reinterpreting. No read entry point gains an argument. The check is made on
**validated reads** (`get`), never at construction and never on `iter_stored`:
a construction-time check would refuse the very audit that reports the
mismatch (§5.5), and would miss a manifest changed after opening.

### 7.2 TypeScript

`parseBaseContract` accepts `kinds`, `relations` and `facets`;
`parseDomainContract` accepts `facets` and refuses `kinds` and `relations`.
Both carry the same closed-field, discriminator and type refusals as
Python, and `compileProfile` enforces the same declaration constraints:
`attaches_to` over declared kinds, one contribution per key, the grammar's
closure. Nothing validates a payload; the README's scope statement gains one
line saying so. This answers D §12's "parity for domains": declarations are
shared encoding, validation is Python-primary, sited with compilation.

### 7.3 The second parity fixture

`fixtures/identity-v1.json`, generated by a sibling of
`generate_claim_identity_fixture.py` and frozen. Each row carries **tagged
components** — `{"t": "int", "v": "12"}`, `{"t": "decimal", "v": "0.0"}`,
`{"t": "float", "v": "0.1"}`, strings, booleans, arrays and objects — with
every non-ASCII code point escaped, and names its digest domain. Python
reconstructs `int`, `Decimal`, `float`; TypeScript `bigint`, `Decimal`,
`number`. A successful row compares **both** canonical bytes and digest; a
refusal row names the expected refusal. Coverage: integers; decimals with one
spelling of zero per type (integer `0`, decimal `0.0`), no exponent, trailing
zeros stripped; a binary-float refusal row; every escape-table entry; an
astral key ordered after a high BMP key; a decomposed input whose canonical
output is NFC-composed; and one object carrying a namespaced facet key,
D4's own parity arm. Both suites build from the components and compare,
closing the "tested twice, compared never" gap the formal model records.

## 8. Guarantees

The `F` table. Rows are frozen; ids are never renumbered.

| # | guarantee | mutation test |
|---|---|---|
| **F1** | The payload contract is enforced at every entry and reported by the check | an unknown key, a missing required field, a wrong type, an unknown scheme, an empty remainder: each refused at `add`, `revise`, relocation with a prefix-stable `FacetPayloadRefused`, and at `import_bundle` as `ImportRefused` naming the member with `FacetPayloadRefused` as its cause; the reproduction's `{boundary, source, asserted_by}` refused at `add`; a raw-written malformation reported `facet-payload-malformed`. **Sabotage:** the validator accepts unknown keys → the reproduction-payload test fails |
| **F2** | The bearer invariant holds over the resulting corpus state, order-independently, for every carrier of a `produces` edge | facet dataset then producing run → run refused; producing run then facet dataset → dataset refused; a non-run record (a `source`, say) carrying `produces` to a facet-bearing dataset → refused on the edge, its kind notwithstanding; a bundle holding both refused in either member order, naming the pair; a production run whose produced address is a facet-bearing dataset → `RunRefused(acquisition-boundary)`, the intent and its refusal report on the chain, no run record, no output publication, store untouched; a raw-written pair reported `facet-bearer-produced`. **Sabotage:** the producer read dropped → the run-then-dataset test fails |
| **F3** | Attestation is bound at mint and on a changed declaration, preserved on import, relocation and unchanged revision | Alice mints; Bob revises the locator retaining Alice → `ActorMismatch`; naming Bob → accepted; Alice revising her own with Alice retained → accepted; Bob's revise with unchanged declaration and `attested_by: Bob` → refused; import and move keep a foreign attester byte-identical. **Sabotage:** the comparison skipped → Bob-retaining-Alice passes |
| **F4** | Eligibility reads the acquisition-boundary validity predicate under the existential rule | one valid and one invalid observes input → admissible, the invalid one reported `facet-payload-malformed`; only an invalid one → refused with a reason distinct from absence; only an absent one → refused with the absence reason; a raw-written observes dataset carrying a valid facet **and** a lineage basis → refused, reported `facet-bearer-produced`; an observes dataset whose `retrieval` names a deleted report → refused, reported `facet-retrieval-unresolved`. **Sabotage:** validity replaced by presence → the invalid-only test admits |
| **F5** | Profile agreement is rechecked under the lock; the check withholds what it cannot judge | manifest rewritten between construction and `add` → `ContractMismatch`, nothing written; rewritten between a run's intent and its publication → `ContractMismatch`, the intent unfulfilled, no report, no run record; domain-only mismatch → `profile-mismatch` with stamp findings still reported; base mismatch → `profile-mismatch` and no stamp finding. **Sabotage:** the recheck skipped under the lock → the rewritten-manifest test writes |
| **F6** | A dataset revision changes interpretation and prose only | each preserved field mutated in turn → `ReviseOutsideAllowlist`; removing `empirical-observation` → refused; removing a domain facet → accepted; adding the facet to an unmarked dataset binds the actor and runs the bearer check; the address is unchanged and node content identity and corpus state move (D2's asymmetry) |
| **F7** | `retrieval` resolves or refuses | present and unresolved → refused; resolving to a report whose operation is not `acquisition` → refused; resolving to an **imported, well-formed** `acquisition` report → accepted. The positive arm tests reference acceptance and claims nothing about URL acquisition, which `url-retrieval` owns |
| **F8** | Every facet a builder writes is declared, and an undeclared key is refused | each `stored.*_node` builder's output, and the writer's coordination node, validated against the compiled registry with no `facet-unexpected` or `facet-missing`; a static inventory of `stored.py`'s facet constants against the shipped base; an undeclared key at `add` → `ValidationRefused(facet-unexpected)`; an unknown kind → refused (G5). **Sabotage:** a builder writes a literal key the contract does not declare → its builder test fails |

**Frozen rows this slice targets**, each on its full oracle, partial rows
named: D2, D4, D5, D8, D9, D10 and G5 in full. D1 in part — the arms about
the `nodes` tree read the installed package (no API takes a domain, contract
or vocabulary argument; the registry receives opaque keys) and its "add a
`nodes` code path" negative is that repository's own review, named as the
remainder. At cut 20, D6 stayed partial on the facet arm and traveled to slice
2's first reader; cut 22 closes it. D8's
oracle covers a domain declaring `kinds:`, `relations:`, or a relation
signature by any spelling.

## 9. Limitations

1. **Reader-shaped facets are declared, not schema-validated**, and reader
   strictness is uneven, named per reader in §3.2. A payload the named
   reader coerces is a payload this slice accepts.
2. **Relation endpoints are compiled, not enforced at write.** Source and
   target sets enter `compiled_identity`; nothing new refuses an edge whose
   endpoints disagree with them. Validation scope for the contract cut.
3. **Answered at cut 22:** the biology-pack reader supplies `facets_read` and
   closes D6's facet arm (biology-pack design §5.6).
4. **F7's positive arm is reference acceptance**, not acquisition.
5. **The packaged base contract is a build-time copy**, held byte-identical
   by a test; the normative file stays at `contracts/science/CONTRACT.yaml`.
6. **Domain contract documents are supplied by the caller.** Distribution
   (D §12) stays open; the writer verifies pins, it does not locate
   contracts.
   Cut 22 ships the first byte-identical packaged domain contract; external
   distribution remains open (biology-pack design §6.1).
7. **The bearer invariant sees producers in this corpus only.** A producer
   in another corpus is `world-resolution`'s cross-corpus read.
8. **The locator's truth and the observation's nature stay authored** —
   kernel limitation 8, narrowed.
9. **A pin mismatch after a run's intent leaves the intent unfulfilled**
   (§5.4). Stated, not repaired.
10. **TypeScript validates no payload.**
11. **`display` keeps its hand-coded check**, accepting an empty statement.

## 10. Conformance cut 20

Sketch; the freeze is a separate document written after this design's
review clears, numbered after cut 19 (concurrency rule 1), serialized after
cut 19's discharge (rule 5). Selected in full: D2, D4, D5, D8, D9, D10, G5,
F1–F8, and the second parity fixture (`parity-fixture-2`, the formal model
§8 obligation). In part: D1. Not selected: D6's facet arm. N2 arms sabotage,
each with a named check that fails: the validator accepting unknown keys;
the producer read dropped from the bearer check; the attestation comparison
skipped; the pin recheck skipped under the lock; validity replaced by
presence in eligibility; a builder writing an undeclared key; the fixture
comparison reduced to bytes without digest; the domain parser accepting
`kinds:`; a domain facet attaching to an undeclared kind accepted at
compile; `WORLD_RELATIONS` widened to both relation groups → the
coordination-vocabulary refusal test fails; the duplicate-key loader
replaced by `safe_load` → the duplicate-declaration test fails; coverage
taken in authored order → the reorder-invariance test fails. Discharged on the certified tuple.

## 11. What changes elsewhere

- **Kernel** §4.1 (the declared boundary defined; the bearer invariant),
  limitation 8 (narrowed), §11 (question closed; lineage standing opened).
- **Computation** §13 (its first bullet closed by citation).
- **Domain design** §3.4 (payload schema travels with the facet — now
  literally), §6 (kinds and facets compiled; inventory widened again), §10
  (targeted rows discharged at cut 20, none amended), §12 (parity for
  domains answered; distribution open).
- **Composition-root adapter** §5: coverage is contract-declared, never
  stored per node.
- **Family-adapters**: `revise` gains the dataset arm; `supersede`
  unchanged.
- **Write-permits** limitation 2: closed by ruling — domains mint no kinds
  (D §3.3), `KIND_ACTS` needs no amendment.
- **Correction lifecycle** §9: cited unchanged; removal refused because the
  question is open.
- **Guide**: foundations (the facet contract; contracts compile into
  profiles), glossary (Facet, Declared), open-questions (closed and opened
  entries), contracts-and-adoption current state.
- **Ledger** current state; **roadmap** row 3 split into two slices and the
  `domain` lane marked open at `.worktrees/domain-boundary`.
- **`stored.py`** docstring (facet keys compiled, not named in code); the
  TypeScript README; `python/tests/test_designs_corpus.py`'s inventory (F).
- **The reproduction driver**: `hold.py` declares a locator and the bound
  actor, `vocabulary.py`'s pins recompute, `close.py` passes the profile.
- **Tasks**: `beliefs-bc3aff` attached to this spec; `beliefs-d245a9` its
  child, closed by this slice's landing.

## 12. Alternatives rejected

- **Evidence-bound eligibility** — the payload must name the boundary-minted
  record that established the hold. For locally held data it collapses to
  the holdings observation G2b already reads, duplicating heldness until
  URL acquisition exists. Kept as the reserved `retrieval` member instead.
- **A boundary-kind enum** in the payload. No reader; fails rule 2.6.
- **Inherit standing through lineage now.** Coherent, but it widens the
  slice into the closure and admission surface. Filed (§14).
- **Facet schemas only, kind tables staying in code.** Leaves the second
  authored per-kind artifact; D4 could close only by amending a frozen row to
  fit the code.
- **An explicit profile on every read entry point.** Purest, but it rewrites
  the world-read and mutation lanes' surfaces and every read site.
- **Compiling `KIND_ACTS` from the contract.** Act routing is write policy;
  scope without payload benefit.
- **A schema for `display`.** Changes behaviour (empty statement) without a
  ruling.
- **Bypassing the pin gate for a refusal report.** A second door through the
  gate the design just closed; the unfulfilled intent is the honest state.

## 13. Verification

`uv run --frozen pytest`, `ruff check .`, `pyright` from `python/`; `npm ci`,
`npm test`, `npm run typecheck`, `npm run check` from `ts/`; the designs
corpus guard on this document; the cut-20 acceptance runner's sabotage arms
on the certified tuple; a fresh reproduction run under the new base pin
reaching step 3 with the authored payload refused and the declared one
admitted.

## 14. Open questions this design files

- **Lineage-inherited observation standing.** Whether a produced dataset
  becomes observes-eligible when its lineage basis reaches an
  acquisition-boundary dataset, and what the eligibility walk then digests.
  Foundations; owned by whichever lane next rewrites the closure.
- **Relation endpoint enforcement at write** (§9 item 2). Contracts and
  adoption; the contract cut.
- ~~**The read ledger behind `facets_read`** (§5.6).~~ **ANSWERED 2026-09-08**
  by the biology-pack design §5 and cut 22: authenticated reader receipts are
  the ledger source.

## 15. Citation amendment — 2026-09-07

The `verification` facet's declaration in the base contract now names
`verify.decode_verification`, the reader the verification-publication slice
added over the whole stored record. §3.2's reader table row for that facet
reads, as of this amendment: **`verification_value`, `verification_derivation`,
`decode_verification`**.

The verification-publication design's §11 asks for that reader to be named "as
a third reader"; the compiled shape does not admit a list. `contract/facets.py`
permits exactly `{shape, description, reader}` for a reader-shaped facet,
requires `reader` to be one non-empty string, and then **discards it** —
`FacetDecl` keeps no reader name, so the declaration is documentation for a
reader of record and nothing consumes it. The line therefore names the reader
that decodes the whole facet today, and this table row is where all three are
recorded. Cut 21's results record carries the same substitution, dated.
