# Contracts

Type: standard, data model; document types 1. This is version 3 of the rules that
contract documents must satisfy. A contract is a YAML document that declares the
vocabulary records may use. The Science base contract declares kinds, relations,
facets and the closed grammars. A domain contract declares sorts, dimensions,
relation templates, instantiations, bridges, estimand declarations, measurement
vocabulary and admissions, duration conventions and namespaced facets. The
coordination contract declares view and coordination kinds. A compiled profile
combines a base contract, a set of domain contracts and optionally a coordination
contract. The shipped base is version 6, with claim grammar 2, estimand grammar 4, and
measurement, composite and scope grammars 1. Domain contract versions are positive
integers in a genesis or successor lineage. The code supports coordination
contract versions 1 to 3 and corpus manifest version 2. The records these
contracts govern are described in [records.md](records.md), and the writes that
check them in [writes.md](writes.md).

## Scope

These rules bind anyone who writes a contract document. That includes authors of
domain contracts kept outside this repository, such as the corpus-local contract
documents `science` loads, as well as the packs beliefs ships. The Python parser
in `beliefs.contract` checks each rule below when it loads a document. The
TypeScript mirror in `ts/` is narrower. It reads a document under the same schema
(see [Documents](#documents)): a document both readers accept reads to the same
value in both. Four kinds of document are refused by one reader only: a `%TAG`
directive that restates the default `!!` handle and a tab after a mapping colon
(Python refuses them), and an alias used as a mapping key and a reserved directive
such as `%FOO` (TypeScript refuses them). It checks base contracts, the domain
grammar described below and profile compilation against the same rules, with two
known differences: the emptiness check on a `definition` strips JavaScript's
whitespace set rather than Python's, so a value of only U+FEFF, or only U+0085 or
U+001C–U+001F, is refused by one side and accepted by the other; and on a document
with several faults the two sides can report different ones first. It computes contract content identities and checks successor lineage against an
explicit predecessor through `parseDomainContract(text, source, base, predecessor?)`.
A `retired` field on any declaration other than a scope relation, even false, is refused
with `UncheckableContract`; scope relations carry retirement and its one-way succession rule
in both languages. It
also refuses `description` at a domain contract's top level and on a sort or a
dimension, as an unknown field, and carries no package resource loader,
`compiled_identity` calculation, assumptions-register reader or estimand
implementation — reading source `DOMAIN.yaml` documents directly to type and
project claims.

## Documents

- A contract is YAML, read under the YAML 1.2 core schema in both languages. A
  plain `null`, `Null`, `NULL`, `~` or empty scalar is null; `true` and `false`
  (also capitalized or upper case) are booleans; a decimal integer (a leading zero
  stays decimal, so `010` is 10), `0o` octal or `0x` hex is an integer; every other
  plain scalar is a string, `yes`, `on`, `0b11`, `1_000`, `12:30`, `2026-01-01` and
  `<<` included (there are no merge keys). Refused: a float (`24.0`, `1e3`, `.inf`),
  since no field carries one; an integer outside ±(2^53 − 1), or whose digit run
  (after any sign or `0o`/`0x` prefix, leading zeros included) is longer than 16
  characters; an explicit tag (`!!str`, `!` and every other); a `%YAML` or `%TAG`
  directive (one exception is named under [Scope](#scope)); more than one
  document; a mapping key that is not a string; a duplicate key at any depth, never
  resolved in favour of the last occurrence; and an anchor name defined twice.
  `fixtures/document-reading-v1.json` is the oracle both readers are tested
  against.
- Unknown fields are refused, never ignored, and missing required fields are
  refused. An identifier matches `[a-z][a-z0-9-]*`.
- A contract's content identity is the `science.identity.v1` digest of the whole
  parsed document: under `science.contract.v1` for base and domain contracts, and
  under `science.coordination-contract.v1` for the coordination contract. Any edit,
  including an edit to a description, gives the contract a new identity.

## Base contract

The base contract has exactly these fields: `contract` (always `science`),
`version`, `claim_grammar`, `estimand_grammar`, `measurement_grammar`,
`composite_grammar`, `scope_grammar`, `time_roles`, `kinds`, `relations` and `facets`. The
Python and TypeScript parsers require a positive integer for the base and composite versions.
Claim grammar requires version 2; estimand grammar requires version 4; measurement and scope
grammars require version 1. The shipped base is version 6. A base document without
`scope_grammar`, such as the version 4 and version 5 documents, is refused for that missing
field rather than read as an implicit upgrade.

- `claim_grammar` holds `version`, `tag_encoding` (`science.identity.v1`),
  `quantifiers`, `polarities`, `sign_inapt_tag`, `forms`, `layers`,
  `role_categories`, `binding_kinds`, `mapping_types`, `placements` and
  `reserved_roles`. Its `version` must be 2. The sign-inapt tag must not also be a
  polarity.
- Six of those fields must equal exactly the sets the implementation operates; a
  wider or a narrower set is refused:

  | Field | Value |
  |---|---|
  | `forms` | `polar`, `"null"` |
  | `role_categories` | `set`, `temporal`, `class`, `pattern` |
  | `binding_kinds` | `release`, `dataset`, `scheme`, `selection`, `run-output`, `world-kind` |
  | `mapping_types` | `exact`, `narrower`, `broader`, `contextual` |
  | `placements` | `claim`, `applicability` |
  | `reserved_roles` (its role names) | `within-model` |

  The form tag `"null"` is a string and is quoted in every document: an unquoted
  `null` is a YAML null value, which no closed set accepts.
- Each `reserved_roles` entry has exactly one field, `world_kind`, which must name
  a world kind the contract declares. The shipped base reserves
  `within-model: { world_kind: procedure }`.
- `estimand_grammar` requires version 4 and `science.identity.v1` tag encoding.
  Its closed sets are `forms`, `arities`, `response_transformations`, `reversals`,
  `response_reversals`, `exchanges`, `ties`, `outputs`, `parameter_typings`,
  `domains`, `nulls`, `increments`, `uncertainty_propagation`, `uncertainty_kinds`,
  `level_sources`, `reference_kinds`, `restriction_forms` and `standing_classes`.
  Each must equal the tags in the [shipped base](../contracts/science/CONTRACT.yaml);
  missing, duplicate, wider and narrower sets refuse. Forms are `contrast`,
  `quantity`, `law-parameters`, `event-locked`, `association` and `enrichment`;
  uncertainty representations are `interval`, `standard-error` and `covariance`.
  The v1 `contrast_kinds` and `scales` fields are refused.
- `measurement_grammar` holds `version` (exactly 1), `tag_encoding`
  (`science.identity.v1`) and nine closed sets. Each set must equal exactly the
  tags the implementation operates; missing, duplicate, wider and narrower sets
  are refused:

  | Field | Value |
  |---|---|
  | `value_types` | `level`, `difference`, `ratio` |
  | `levels_of_measurement` | `nominal`, `ordinal`, `interval`, `ratio` |
  | `scale_orientations` | `higher-is-more`, `higher-is-less` |
  | `transformation_kinds` | `identity`, `affine`, `logarithm`, `monotone` |
  | `monotone_directions` | `increasing`, `decreasing` |
  | `transformation_domains` | `real`, `nonnegative`, `positive`, `unit-interval` |
  | `conversion_kinds` | `multiplicative`, `affine` |
  | `cardinalities` | `one-to-one`, `many-to-one`, `one-to-many`, `many-to-many` |
  | `evidence_modes` | `observation`, `annotation`, `simulation`, `derivation`, `literature-extraction` |

  The grammar enters compiled profile identity with every set sorted; authored
  tag order is preserved in memory and does not affect that identity.
- `composite_grammar` holds `version` and `shapes`. The only supported shape is
  `dag`.
- `scope_grammar` holds `version` (exactly 1) and `relations`, which must equal
  exactly `equal` and `narrower`: the relations a domain may declare between two
  leaf scopes (see [scope relations](#scope-relations)). `broader` is the inverse
  comparison result, never a declaration. The grammar enters compiled profile
  identity with its set sorted.
- Each kind has a `role` of `world` (the default) or `prose`, an identity `domain`
  of the form `science.<kind>.v<n>`, and `facets`, which map each facet key to
  `{required, covered}`. A prose kind has no domain and no facet except `display`.
- Each relation has a `group` (`world` or `lifecycle`), `sources` and `targets`
  (declared kinds), and an optional `same_kind`, which requires `sources` and
  `targets` to be equal sets. `composes` must be composite → proposition.
- A base facet is either `reader`-shaped, naming its reader, or `schema`-shaped,
  declaring `fields`.

- `time_roles` is the closed mapping `source`, `duration`, `frequency`, `second`,
  `hertz`. The shipped assignments are `urn:beliefs:source:bipm-si-brochure` and
  `si-brochure/{duration,frequency,second,hertz}`. Python and TypeScript compile
  the same map into profile identity. The map names vocabulary; it supplies no
  vocabulary declarations or source-admission receipt. Elapsed series and every
  event lag require activated declarations at those identities and that defining
  source: duration dimension `{T: 1}`, frequency `{T: -1}`, noncalendar second
  and hertz, and a noncalendar duration unit from the same source. Conversion to
  seconds uses identity or one explicitly licensed exact multiplicative
  conversion; affine and approximate conversions refuse.

A writer requires the identity of the shipped base contract. A corpus pinned to an
earlier base refuses validated reads under the shipped one: base-v5 corpora refuse under
v6, as base-v3 corpora did under v4. There is no compatibility reader or in-place
migration tool; changing a manifest pin does not recreate a corpus's records.

## Kernel commitments (Layer 0 register)

The kernel separates field vocabulary from structural grammar, with an explicit
coupling to external time-role names at the series and lag boundaries.
This register describes shipped base version 6 and its operations: claim grammar 2,
estimand grammar 4, measurement, composite and scope grammars 1. It records
what those choices preserve, what they leave unestablished, and the identity cost
of changing them. Update it when the corresponding behavior changes.

There are four places for commitments:

- **Kernel structure**, recorded here: the closed grammars, identity projections,
  admission and aggregation rules that every field uses.
- **Shared vocabulary**, declared by `general`: cross-domain meanings such as
  quantity kinds and relation templates. Activating the pack is explicit;
  its terms are not built into a claim's grammar.
- **Field vocabulary**, declared by a field contract: its sorts, bindings,
  instantiations and bridges, with their scientific commitments.
- **Analysis particulars**, frozen in the spec: measured bindings, procedures,
  estimand, applicability, assumptions and dependencies.

Domain declarations have their own immutable
[assumptions registers](records.md#assumptions-registers), bound to the exact
contract they describe. Each entry says what it collapses, what it licenses and
what it does not establish. This Layer 0 reference is documentation, not a held
register record; editing its prose changes no semantic identity.

### Identity costs

Changing a contract document changes its content identity and requires matching
corpus pins. It does **not** by itself change every claim identity. The
[claim projection](records.md#identity) contains identifiers, tags and member
coefficients, not contract digests, sort bindings or compiled-profile identity.
A changed projected value changes that claim's identity; changing the projection
shape or its digest domain changes the identity scheme. The v1-to-v2 claim
projection change requires recreation, with no identity-preserving mapping.

Contracts consulted during evaluation enter the
[belief input digest](records.md#beliefs), so a changed consulted contract changes
that provenance even when the claim bytes stay the same. This separation does
not permit changing an identifier's meaning in place: domain
[succession](#succession-and-retirement) preserves the meaning-bearing schema
projection. It excludes definition prose, whose semantic consistency remains an
author and reviewer responsibility. New meanings need new identifiers.
Analysis particulars instead enter the frozen spec and assessed
target; changing them can change the spec and assessed-proposition key while
leaving the broader claim unchanged.

### Commitments and limits

| Commitment | What it preserves and leaves unestablished | Identity cost |
|---|---|---|
| **Claim shape and relation meaning.** A claim has an operator, named roles, qualifiers, form, polarity and layer. Templates separate relation meaning from the sort combinations admitted by instantiations; bridges declare their relation to a template. | A typed relation is distinct from its prose description. Typing and a declared bridge mapping do not establish that the relationship holds scientifically. Choosing an instantiation admits a claim; the instantiation's name is not a projected claim field. | Changing an operator, role name, role referent or member coefficient changes the claim. Changing admission declarations changes the contract and consulted provenance, without adding the instantiation name to the claim. |
| **Quantifiers, form and polarity.** Qualifiers use `generic`, `universal` or `existential`; claims use `polar` or `"null"`, with `positive`, `negative`, `unsigned`, or the sign-inapt tag as typing permits. | Generic is distinct from universal. Unsigned is distinct from having no applicable sign. A null claim is distinct from an inconclusive assessment; its quantitative margin belongs to the estimand. These tags do not prove an effect or its absence. | These tags enter the claim projection. Changing a projected tag changes the claim; changing the base declaration changes contract identity separately. |
| **Four layers.** `causal`, `structural`, `statistical` and `methodological` are the shipped layer vocabulary. | Layer separates kinds of question. Marking a claim causal is not causal identification; the analysis carries its identification, design and selection commitments. | Layer enters claim identity. The same roles and operator at different layers name different claims. |
| **Sorted referents and scoped questions.** A role referent carries both sort and term. Claim qualifiers remain a flat map with one quantified referent restriction per dimension. Numeric, interval, union, time and rule restrictions belong to typed applicability. | Distinct sorts preserve distinctions that a shared label could hide. A vocabulary binding does not equate a gene with a protein. Claim typing alone does not prove vocabulary membership; decoding reports resolution against an explicit snapshot. Applicability comparison does not infer undeclared containment. | Sort identifiers and claim-side restrictions enter claim identity; binding releases do not. Applicability enters the spec and assessed target. Moving a dimension between placements changes how the question is represented. |
| **One observable per measure.** An observable has one quantity kind, a bearer sort and an optional aspect. A measure adds a unit or procedure-defined scale, level, value type, transformation and yielding procedure. | Measurement identity keeps the bearer and method explicit. Coordinate conversion is separate from semantic comparability; convertible numbers need not estimate the same thing. Mappings and proxies carry their own assumptions and validity. | Measures and frozen procedure, mapping and proxy dependencies enter the spec and assessed target. Changing these does not automatically change the claim's projected roles. |
| **Six estimand forms and keyed assessment.** `contrast`, `quantity`, `law-parameters`, `event-locked`, `association` and `enrichment` have typed bindings, a functional, control, assumptions and output. | A claim names the shared question; the assessed target states what this analysis estimated. Evaluation is per claim and assessed-proposition key. Pairwise conversion and synthesis verdicts do not pool results. | Changing target content, applicability, standing or frozen dependencies changes the key as defined by its projection. A changed spec is a new spec; the broader claim may remain identical. |
| **Finite series and external time names.** Measured bindings can identify an immutable selected channel and its complete frozen graph; the base fixes the source and four time-role terms above. | Explicit byte checks establish exact geometry, support, linkage and declared materialized provenance. They do not establish clock calibration, event truth, honest extraction, numerical aggregate correctness or anti-aliasing. Index and absolute labels infer no physical rate. The name map is not external vocabulary admission; source ownership and complete genesis mappings remain separate. | Changing a source, member, channel, selection, origin, anchor, coordinate assertion or cited procedure changes the relevant held object or target. Renaming the base roles needs a base successor and consumer target/activation review. A measuring-procedure-only change affects the target without reminting the table. |
| **Three standing routes.** Empirical admission requires an observed input with empirical standing. Model admission binds the claim's model procedure. Calibrated-model admission requires eligible calibration dependencies. | Reproduction, current dependency eligibility and independence are separate checks. Model replication is not independent empirical corroboration. Empty dependency roots never certify independence. Source assertions have no direct counting route. | Standing and frozen dependency identities enter the assessed key. Later verification or retraction can change eligibility and belief provenance without changing that frozen key. |
| **DAG-only composites.** Members are polar causal claims with declared edges whose endpoint roles each hold one referent; cycles are refused. | A composite records a directed acyclic structure, not arbitrary feedback, a joint probability model or a separately assessable hypothesis. An assessment cannot target a composite. | Grammar, shape, sorted nodes and member claim identities enter composite identity. Changing these creates a different composite; changing a member's claim can change the composite that names it. |
| **Explicit aggregation policy.** `science.belief.v1` uses unit-weight directional assessments and certified dependency relationships, with an exact rule and implementation binding. | The result is a signed evidence balance, never a probability or odds. Counting does not validate a field label, a mechanism, a proxy interpretation or the appropriateness of an authored scientific assumption. | Changing the policy requires a different policy binding. It changes the derivation being requested, not the claim projection. |

The record-level rules are in [claims](records.md#propositions-and-claims),
[measurement records](records.md#measurement-records),
[standing](records.md#declared-standing-at-write-boundaries),
[composites](records.md#other-world-records) and [beliefs](records.md#beliefs).

## Domain contracts

A domain contract requires `contract` (its namespace), `version` (a positive
integer), `lineage`, `sorts` and `dimensions`. It may add `description`,
`templates`, `instantiations`, `bridges`, `estimands`, `duration_conventions`,
`quantity_kinds`, `units`, `constants`, `conversions`, `transformations`,
`procedure_kinds`, `aggregation_rules`, `assumption_kinds`, `functionals`,
`identification_classes`, `designs`, `selection_mechanisms`, `measurements`, `aspects`,
`scope_relations` and `facets`. Any other top-level field is refused, `kinds` and `relations`
included, and so are the v1 fields `operators` and `edges`: a v1 document cannot parse under
base v6. Its namespace may be neither `science` nor `coordination`. Each table is
its own namespace, so a sort and a dimension, or an instantiation and a bridge, may
share a local name; a bridge may not share a name with a template, since both are
operators.

Every value a domain draws from a base closed set (layers, forms, placements, role
categories, binding kinds, mapping types) must be one the base contract declares,
and a list of them may not repeat a value.

- **Sorts.** A sort requires `binding`. It may add `identifier_class`,
  `categories` (role categories, default none), `description` and `retired`. A
  binding names its arm by `kind` and carries exactly that arm's fields, each a
  non-empty NFC string; a field of another arm is refused:

  | `kind` | Fields |
  |---|---|
  | `release` | `namespace`, `release` |
  | `dataset` | `dataset` |
  | `scheme` | `scheme`, `version` |
  | `selection` | `dataset`, `rule`, `selected`, `annotator` |
  | `run-output` | `run`, `dataset` |
  | `world-kind` | `world_kind` |

  `dataset`, `selected` and the run-output `dataset` are dataset record ids
  (`dataset:sha256:` and 64 lowercase hex characters), `rule` is a `classification-rule:`
  record id and `run` a `run:` record id, each followed by 64 lowercase hex characters.
  The short `dataset:<64 hex>` spelling is refused. Grammar validation does not
  establish that a dataset is held or that a term is a member of it.
  `world_kind` names a world kind the base contract declares. A `world-kind` sort
  declares no `identifier_class`: its class is `dataset:sha256:` followed by
  64 lowercase hex characters for datasets, and `<kind>:` followed by 64 lowercase
  hex characters for every other world kind. Every other sort must declare an
  `identifier_class`. A sort's schema projection is its binding
  (with `kind`), its identifier class when it has one, and its categories as a
  sorted list.
- **Identifier classes.** An identifier class is a literal `prefix` and a `pattern`
  in the portable subset. The prefix is informational: the parser checks only that the
  pattern text begins with it and that it contains none of `\ . [ ] ( ) { } | * + ? ^ $`,
  not that every admitted term carries it. The subset is literals, `.`,
  character classes with ranges and `^` negation, `(?:...)`, `|`, the quantifiers `*`, `+`,
  `?`, `{m}` and `{m,n}` (bounds of at most five digits and up to 65535), and backslash escapes of the metacharacters; anything else, a
  non-NFC pattern, an unescaped `[` in a class and a doubled `&&`, `~~` or `||` in a class included, is refused as a malformed contract. Terms are normalized to NFC
  and matched whole, with `.` and negated classes matching any code point including line
  terminators: Python uses `re.DOTALL` with `fullmatch`, TypeScript uses
  `^(?:pattern)$` with the `s` and `u` flags, and authors set no flags.
  `fixtures/identifier-patterns-v1.json` is the oracle both implementations are tested
  against. Write a pattern as a single-quoted YAML scalar: a double-quoted scalar
  reads `\-` as an escape YAML does not define, and the document is refused.
- **Dimensions.** A dimension requires `placement` (`claim` or
  `applicability`) and `applies_to`, a list of operators (templates or bridges) a
  claim over which may carry it. An applicability-side dimension also requires
  `restriction`; a claim-side dimension refuses that field. Its closed forms are
  `{form: term, sort: <sort>}`, `{form: interval, quantity_kind: <quantity-kind>}`,
  `{form: time-interval}`, `{form: rule, classes: <sort>}`, and
  `{form: union, of: <one non-union restriction>}`. References resolve at compile.
  A `term` restriction's sort must match `restriction_sort`, which is required except for an applicability `time-interval` leaf (directly
  or within one union), where `restriction_sort` is forbidden. Claim qualifiers
  always require a sort. Every form refuses fields belonging to another.
- **Templates.** A template requires `roles`, `sign_apt`, `layers` and `forms`, and
  may add `edge`, `definition`, `external`, `description`, `retired` and `event_anchor`.
  The optional `event_anchor` is exactly `{role: <role-name>}` or `{independent: true}`.
  A linked role must exist, require category `class`, and refuse coefficients.
  This association declares meaning, not estimand admission.
  - Each role requires `arity`, `one` or `many`, and may add `constraint` (role
    categories a filling sort must declare). A `many` role may add `coefficients`
    (a boolean, default false), `min` (default 1, at least 0) and `max` (at least
    `min` and at least 1; absent is unbounded); a `one` role may declare none of
    the three. A role may not be named after a reserved role (`within-model`).
  - `layers` and `forms` are non-empty. A template that is not sign-apt may not
    declare the form `"null"`.
  - `edge` names two distinct roles of the template, `{cause, effect}`, and is
    admitted only when `causal` is among the layers.
  - `definition` is prose and stays outside the schema projection. `external`
    is `{reference, mapping}`, with `mapping` one of the base mapping types.
  - A role's projection is `arity`, `coefficients` and the sorted `constraint`,
    plus `min` and, when bounded, `max` for a `many` role.
- **Instantiations.** An instantiation requires `template` and `roles`, and may add
  `description` and `retired`. `roles` maps each role to a non-empty list of sorts
  that may fill it; a `many` role's members may have any listed sort.
- **Bridges.** A bridge requires `template`, `mapping` and `roles`, and may add
  `layers`, `description` and `retired`. `mapping` is `narrower` or
  `contextual`; `exact` and `broader` are refused. `roles` lists sorts as an
  instantiation's does, and `layers`, when present, narrows the template's.
- **References.** A sort or operator reference is a local name, or
  `<other-namespace>/<name>` for a declaration another activated contract makes;
  every reference is resolved at compile. A local sort name must be one this
  contract declares. The base namespace cannot be referenced, and neither can the
  contract's own namespace in prefixed form.
- **Estimands.** A declaration is keyed by `instantiation:<name>` or
  `bridge:<name>` in the same document. Its required fields are `forms`, a nonempty
  subset of the six kernel forms, and `conditioning_sorts`, possibly empty.
  References resolve at compile. Admission requires one whole row to admit both
  the form and every conditioning sort. The old level, measure and identification
  sort fields are refused. Compiled declarations retain their explicit `kind`.
  Every row admitting `event-locked` must resolve an instantiation or bridge whose
  template declares `event_anchor`; bridges inherit the template association.
- **Duration conventions.** A duration convention requires exactly `conversion`,
  a local or foreign-qualified conversion reference, plus optional editorial
  `definition` and `description`. Compilation resolves the reference and requires
  an exact multiplicative conversion without error or constant, joining exactly
  one calendar unit to one noncalendar unit of the same quantity kind. The
  convention adds no coefficients; its schema projection names the conversion.
  The provisional arbitrary scalar mapping is refused.
- **Quantity kinds.** A quantity kind requires `dimension`: a map of SI base
  dimensions (`L`, `M`, `T`, `I`, `Θ`, `N`, `J`) to integer exponents, or
  `dimensionless`, `counted` or `construct`. Dimensions validate an explicitly
  declared conversion through a constant; they never infer a conversion.
- **Units.** A unit requires `symbol` and `quantity_kind`, a reference resolved
  against activated quantity kinds at compile. Optional `external` maps `ucum`
  and/or `qudt` to citable reference text. Optional boolean `calendar` defaults to
  false and enters the schema projection as its resolved boolean. A calendar unit
  must have physical dimension exactly `{T: 1}`; no name or symbol implies it.
- **Constants.** A constant requires nonzero `value`, `unit` (resolved at compile)
  and `exact` (a boolean).
- **Conversions.** A conversion requires `from` and `to` unit references,
  `kind` (`multiplicative` or `affine`), positive `factor` and boolean `exact`.
  An affine conversion also requires `offset`; a multiplicative one refuses it.
  Optional `error` is nonnegative. A conversion between distinct quantity kinds
  requires a `constant` reference: adding or subtracting that constant's unit
  dimension exponents from the source must yield the target exponents. Compilation
  records whether the constant multiplies or divides; `dimensionless`, `counted`
  and `construct` kinds cannot participate in that reconciliation. A conversion
  within one kind refuses a constant. Ordinary `conversion_between` lookup excludes
  every conversion touching a calendar unit; a named duration convention selects
  those conversions explicitly. At most one declaration joins any unit pair,
  across both directions and every activated contract; `conversion_between`
  retrieves that declaration in either direction, without composing a route.
- **Transformations.** Every transformation requires `kind`, `domain` (`real`,
  `nonnegative`, `positive` or `unit-interval`) and boolean `invertible`. An
  `identity` needs no coefficients; `affine` requires nonzero `scale` and `offset`;
  `logarithm` requires positive `base` different from one. These three are fixed
  by construction and refuse `fixed: false`. A `monotone` transformation instead
  requires `direction` (`increasing` or `decreasing`) and boolean `fixed`, which
  distinguishes a declared map from one depending on the sample. Each kind refuses
  fields belonging only to another kind.
- **Functionals.** Each row supplies `form`, `arity`, `response_transformation`,
  `reversal`, `response_reversal`, `exchange`, `ties`, `output`, `domain`,
  `null`, `increment`, `uncertainty` and `parameters`. Both parsers enforce
  the closed property vocabularies and form matrix. Declared output requires a
  by-parameters certificate and named parameters with parameter typings and
  numerical domains. Other outputs use `parameters: not-applicable`. Null values
  must be fixed points of the declared reversal actions, and a reciprocal requires
  a positive domain. Editorial definition, description and external references
  stay outside the schema projection. Compilation retains the parsed declaration
  and its namespace for the conversion-property adapter. Optional `response_axis`
  is `index`, `elapsed` or `regular-elapsed`, only for `contrast`, `quantity`,
  `law-parameters` and `event-locked`. It requires a series on the measured
  response; absence imposes no axis requirement. It enters the immutable
  functional schema, so changing an existing requirement needs a new identifier.
- **Identification classes.** A row requires a nonempty `licenses_layers` list
  selected from the base's layers. The compiled declaration carries those layers.
- **Designs and selection mechanisms.** Rows declare names for identity comparisons
  and accept optional definition and description.
- **Procedure kinds.** Each `procedure_kinds` row requires boolean
  `fills_within_model`, stating whether the kind fills a within-model role.
- **Aggregation rules.** An `aggregation_rules` row declares a named rule and
  carries no required fields.
- **Assumption kinds.** Each `assumption_kinds` row requires non-empty NFC prose
  `collapses` and non-empty `particulars`, a list of distinct field names matching
  `[a-z][a-z0-9_]*`. Particulars are compared as a set in schema projections.
  These vocabulary tables accept optional `definition` and `description`;
  neither enters schema or compiled identity, while document identity covers both.
- **Measurements.** A `measurements` row maps a sort reference to a list of
  distinct quantity-kind references. An empty list explicitly declares that the
  sort bears none. References resolve at compile, including the row key. The
  profile folds all activated packs by set union; `admits_measurement` returns
  false for an undeclared sort or an unlisted quantity kind.
- **Aspects.** An `aspects` row maps a quantity-kind reference to a list of distinct
  aspect-sort references, all resolved at compile. `aspect_sorts` returns the
  union across activated packs, or an empty set when none is declared. Compiled
  pack rows retain the declaring contract as well as their resolved references;
  their projection keys combine that contract and the qualified target, preserving
  every contribution independently of activation order.
- **Facets.** A domain facet declares `attaches_to` (world kinds) and `fields`. Its
  key in a profile is `<namespace>/<name>`.
- <a id="scope-relations"></a>**Scope relations.** A `scope_relations` entry declares
  that two leaf scopes of one applicability dimension select exactly the same cases
  (`equal`) or that the left scope is properly contained in the right (`narrower`:
  every left case is a right case and the right admits a case the left does not),
  for the dimension's full intended universe. It has exactly `dimension`, `relation`,
  `left` and `right`, and may add `description` and `retired`. `relation` is one of
  the base's `scope_grammar` relations; `within`, `subclass`, `part-of` and `broader`
  are refused, and no ontology edge or label is interpreted. An endpoint is exactly
  `{sort, term}` (one term of the dimension's restriction sort, a canonical
  identifier) or `{rule, classes}` (an exact `classification-rule:` id and a list of
  exactly one canonical class); both endpoints take one form, and interval,
  time-interval, union, mixed and multi-class endpoints are refused. A local
  `dimension` or `sort` must be one this contract declares; foreign references
  resolve at compile. Compilation refuses a relation whose dimension no activated
  contract declares, is not on the applicability side, or restricts by anything but
  term or rule (a union dimension uses its `of` leaf form); a term endpoint whose
  sort is not the dimension's restriction sort or whose term is outside that sort's
  identifier class; and a rule endpoint whose class is outside the identifier class
  of the dimension's classes sort. A profile reads no record, so a rule endpoint's
  kind, body and classes sort are checked where a comparison uses it. Parsing cannot
  check whether a declared proper containment is scientifically justified; its
  assumptions-register entry carries that justification. A relation's compiled
  projection is its qualified `dimension`, `relation`, endpoints and `retired`.

Estimand declarations, duration conventions, the five numerical measurement tables,
the vocabulary tables and the two pack tables carry no `retired`. Templates
require at least one role at parse time. Compiled instantiations, bridges and
estimand declarations carry an explicit declaration kind.

The five measurement tables may be declared by any domain namespace with checked
source ownership for admission (see [Profiles](#profiles)). Their
references are local names or terms from other activated contracts, resolved in
dependency order at compile. Their optional `definition` is prose outside every
schema projection; the full document content identity still covers it. Numerical
coefficients (`value`, `factor`, `offset`, `scale`, `base`, `error`) must be quoted
decimal strings, never YAML numbers. Python reads exact rational values using
`Fraction(Decimal(text))`; TypeScript holds exact integer numerators and denominators.
Both parsers limit a coefficient's mantissa to 4,096 decimal digits (including
leading and trailing zeros, excluding the sign and decimal point) and its signed
exponent's absolute magnitude to 4,096. Leading zeros in the exponent do not
change its magnitude. They check these bounds before numeric construction and
refuse oversized coefficients or numeric construction errors as `MalformedContract`.
Accepted coefficients remain exact; no rounding or numeric fallback is used.
Projections preserve the authored decimal text, so `"1"` and `"1.0"` remain distinct
declarations for succession. Absent optional fields are omitted from projections.

How to write, load and ship a domain contract is in
[development.md](development.md#adding-a-domain-contract).

## Typed restrictions

`beliefs.applicability` wraps each typed restriction with a kernel quantifier.
`checked` verifies applicability placement, operator permission and the quantifier;
`build_applicability` also resolves every term and rule-class referent into a
binding receipt. Authoring refuses retired dimensions and sorts; stored decoding
retains their historical meaning. `Applicability.restrictions()` supplies the
operator-free geometry, while the projection preserves quantifiers and
`rule_ids()` supplies the cited classification rules. Union members are distinct
and ordered by their canonical encoded projections. `claim.check_referent` is the
public validation seam shared by these authoring and stored-reader paths.

`beliefs.restriction` types a map of applicability-side dimension terms to restriction
values, without an operator or quantifiers. It checks each dimension's declared
form, a term's sort and identifier class, an interval unit's quantity kind, and a
rule's class identifiers against the declared classes sort. Malformed shapes or
typings raise `MalformedRestriction`, a `MeasurementError`.

The value forms are `{sort, term}`, `{unit, low?, high?, low_closed, high_closed, convention?}`,
`{start, end}`, `{rule, classes}`, and a list of two or more values of one non-union
form. Numeric bounds are exact decimal strings on projection and `Fraction`s in
memory. At least one bound is required; equal bounds require both ends closed.
Authored bounds must have a finite decimal representation, and parsed mantissas
and exponent magnitudes are limited to 4096. Projection uses compact exact exponent
spelling when fixed-point text would exceed that budget; direct construction also
refuses a bound without an admitted exact projection. Time intervals use the
reservation assignment's whole-second UTC timestamps or `open` at one end and are half-open.
Rule classes are non-empty, sorted and distinct.

`co_scope` compares two restriction maps dimension by dimension: `equal`,
`narrower`, `broader`, `overlapping`, `disjoint` or `unknown`. A one-sided restriction
is narrower than an unrestricted dimension. Numeric intervals normalize through
an explicitly declared conversion using exact rational arithmetic; time intervals
and unions use endpoint-sensitive interval arithmetic. Matching terms and class
sets establish equality or containment; distinct terms and distinct rules stay
unknown. Per-dimension results fold with disjoint first, then unknown, then mixed
narrower/broader or overlapping, then a single containment direction or equality.
`co_scope_by_dimension` exposes those particulars.

Term and rule scopes may also use the profile's live [scope relations](#scope-relations).
Compilation builds one graph per dimension: equal endpoints are quotiented into
equality classes named by a deterministic representative (the least atom), and
`narrower` relations become strict edges. A strict edge within an equality class, a
strict cycle, or equality or a strict path (direct or through other rules) between
two classes of one rule refuses the profile with `ProfileError`, including when the
facts come from different contracts. Retired relations contribute no edge. Python and
TypeScript refuse the same graphs; only Python compares through them.
`compare_scopes(a, b, profile)` is the one structural comparison; it returns a
`ScopeComparison` (operands, per-dimension verdicts, folded verdict and the sorted
terms of the relations it selected), which only `compare_scopes` constructs, and
`co_scope` and `co_scope_by_dimension` project it. On a dimension where both sides
are term or rule leaves:

1. Each operand becomes its atoms: canonical terms, or one `(rule, class)` atom per
   rule class. When both operands name only the same rule, their class sets compare
   by inclusion as above and no relation is used.
2. The context is every live relation in the undirected graph components that
   contain any original operand atom, chosen before normalization. Each atom is
   replaced by its representative, and an atom strictly below another atom of the
   same operand is removed as redundant.
3. Terms then compare as label sets: identical sets are `equal`, a proper subset
   `narrower`, a proper superset `broader`. This keeps the inherited convention that
   an additional, nonredundant term label extends the scope; it is a modeling
   convention, not a proof about undeclared terms.
4. Otherwise identical normalized sets are `equal`; one left atom strictly below a
   right atom is `narrower`, and the inverse `broader`; anything else is `unknown`.
   Cross-rule sets never use label-set inclusion, and equality to one member of a
   larger union proves no strict containment.

So with A narrower than P, `A ∪ P` equals P and A is narrower than `P ∪ C`, while
A and B both narrower than P leave `A ∪ B` against P `unknown`: siblings may cover
their parent. The declared fragment holds only equality and proper containment, so
a curator who cannot establish properness declares nothing and the comparison stays
`unknown`; an ordinary subclass edge does not qualify. Because the same-rule
class-set arithmetic treats added classes as widening a scope, nested classes of one
definition (definite versus any case) need separate rule definitions. Context is
whole components, never a winning path: an edge joining a component changes the
selected context even when it changes no verdict, and a large component selects
many relations. A relation disconnected from both operands selects nothing. Numeric,
time, same-rule and one-sided comparisons select nothing. Structural comparison
reads no record and confers no checked authority; `scope_rule_ids` and
`scope_contracts` recompute a comparison's context under a profile (refusing one
computed under another table) and name its rule roots and the contracts whose
relation, dimension or endpoint sorts it used.

A calendar interval without a convention is admitted as unresolved. When both
scopes restrict the dimension, an unresolved calendar interval compares
`unknown` even against itself. A supplied `convention` must name a declared duration
convention whose conversion involves the interval's calendar unit; it is refused
on noncalendar units. Local convention references resolve in the dimension's
namespace when typed, and projections retain qualified references. Each calendar
interval, including every union member, normalizes exactly through its own named
conversion into that conversion's noncalendar unit before ordinary direct-unit
normalization. Missing subsequent direct routes stay unknown. This applies no
calendar arithmetic, date inference or automatic convention selection.

## Facet fields

A field name matches `[a-z][a-z0-9_]*`. Its `type` is one of `string`, `integer`,
`boolean`, `ref`, `locator` and `actor`, and `required` is mandatory. A `ref` field
must declare `kinds`, a `locator` field must declare `schemes`, and no other field
type may declare either. When a record is written, its payload is checked against
these declarations:

- unknown keys are refused, and so are null values and nested values;
- an `integer` field takes an integer and a `boolean` field takes a boolean;
- every other type takes a non-empty string;
- a `ref` value is `<kind>:<rest>`, where the kind is one the field declares;
- a `locator` value is `<scheme>:<rest>`, where the scheme is one the field
  declares.

## Succession and retirement

`lineage` is either `genesis` or `{successor: <predecessor content identity>}`.
A contract is loaded together with its predecessor, and the load is refused when
any of the following holds:

- a genesis contract is given a predecessor, or a successor contract is given none;
- the predecessor's identity or namespace differs from the one declared;
- the predecessor was typed under a different base content identity;
- a domain successor removes or changes a previously present defining source id;
- the successor drops a claim-vocabulary declaration its predecessor declared;
- the successor changes the schema projection of a claim-vocabulary declaration;
- the successor un-retires a claim-vocabulary declaration.

Both languages check additive succession; TypeScript refuses retirement fields
except on scope relations, where both languages admit retirement and refuse
un-retirement. Parsed TypeScript domains expose `contentIdentity` and `predecessor` metadata.
Schema equality does not validate the scientific meaning of changed editorial prose.

The claim vocabulary covers all 22 domain declaration families: sorts, dimensions,
templates, instantiations, bridges, estimand declarations, duration conventions,
the seven methodological tables (`functionals`, `identification_classes`, `designs`,
`selection_mechanisms`, `procedure_kinds`, `aggregation_rules` and
`assumption_kinds`), the two pack tables (`measurements` and `aspects`), the
five numerical measurement tables (`quantity_kinds`, `units`, `constants`,
`conversions` and `transformations`) and `scope_relations`. Under succession each declaration is keyed by
its local typed address: `sort:<name>`, `dimension:<name>`, `template:<name>`,
`instantiation:<name>`, `bridge:<name>`, `estimand:instantiation:<name>` or
`estimand:bridge:<name>`, `duration-convention:<name>`, `functional:<name>`,
`identification-class:<name>`, `design:<name>`, `selection-mechanism:<name>`,
`procedure-kind:<name>`, `aggregation-rule:<name>`, `assumption-kind:<name>`,
`measurement:<key>`, `aspect:<key>`, `quantity-kind:<name>`, `unit:<name>`,
`constant:<name>`, `conversion:<name>`, `transformation:<name>` and
`scope-relation:<name>`. A scope relation's schema projection is its `dimension`,
`relation`, `left` and `right` as authored; a corrected relation takes a new name and
the old one is retired.
Assumptions-register coverage (`register_entry_keys`, see
[records.md](records.md#assumptions-registers)) uses the same 22 family tags but
qualifies every target (`<kind>:<namespace>/<name>`, nested
`estimand:instantiation:<namespace>/<name>` or `estimand:bridge:<namespace>/<name>`,
each declared `measurement` sort, and each sort listed in `aspects`, with empty
aspect lists contributing no register key).
Declarations sharing a local name in two tables are compared separately. Sets (layers, forms, categories, constraints, `applies_to`,
the sorts a role lists) are compared as sets. Facets are not compared under
succession. `description`, `definition` and `retired` are outside the comparison. A retired identifier can
still be decoded, so stored claims stay readable, but it can no longer be used to
author a new claim.

## Profiles

`compile_profile(base, domains, coordination=...)` refuses, among others, in these
cases:

- an input was not produced by its parser;
- a domain contract was parsed against a different base contract;
- two contracts contribute to one namespace;
- a coordination kind, or the `coordination` facet, collides with one the base
  contract declares;
- a coordination contract's query vocabulary falls outside the kernel's world
  kinds and relations;
- a domain facet attaches to a kind that is not a world kind;
- a `ref` field names a kind outside the compiled inventory;
- a cross-contract sort reference names a sort no compiled contract declares;
- an instantiation or bridge names a template no activated contract declares;
- an instantiation or bridge names a role its template lacks, or omits one;
- a sort an instantiation or bridge lists does not declare every category the
  role's `constraint` requires;
- a bridge's `layers` include one its template does not;
- a dimension's `applies_to` names no operator an activated contract declares (a
  local name resolves against the declaring contract only);
- an estimand declaration's `conditioning_sorts` names an unresolved sort.

An unparsed input, a base mismatch and an unresolved sort reference are contract
errors; the rest are profile errors.

A compiled term is `<namespace>/<name>`, and that term is what enters a claim. An
operator is a compiled template or bridge; a bridge has its template's roles,
sign aptness, forms and edge, and its own sorts and effective layers. The profile
keeps an admission index from each template to the typed addresses
(`instantiation:<namespace>/<name>`) of its instantiations across every activated
contract. A claim's admitting set is every instantiation (or, for a bridge, the
bridge itself) whose sorts for each role include every sort the claim puts there;
authoring excludes retired declarations and decode does not. Estimand declarations
are keyed by the compiled typed address of their target and looked up for an
admitting set. A claim may carry a dimension only when it is claim-side and its
`applies_to` names the claim's operator. An operator is offered for authoring only
when it is not retired, its template is not retired (a bridge over a retired
template is withdrawn with it), and some live route (a live instantiation, or the
live bridge) lists a live sort for every role that must be filled.

The profile's compiled identity is taken over every table keyed by term (estimand
declarations by typed address), so activation order cannot move it; it changes
when a field the compiled tables carry or a retirement changes. It stays the same
after a `description`, `definition` or `external` edit, since the compiled tables
carry none of the three; succession compares `external`. A corpus manifest pins the base contract and every
activated contract by content identity. A writer whose profile disagrees with
those pins is refused.

The package ships `general` version 2 (`domains/general/DOMAIN.yaml`
and its byte-identical packaged copy `python/src/beliefs/domains/general/DOMAIN.yaml`),
together with its canonical assumptions register (`domains/general/REGISTER.json` and
`python/src/beliefs/domains/general/REGISTER.json`). `shipped_domain_contract("general")`
and `shipped_assumptions_register("general")` both return the current pair from one
checked contract/register history under the shipped base. Every register must have
the matching `describes` digest and exact `register_entry_keys(contract)` coverage.
A genesis register has no `previous`; a successor register names the immediate
contract predecessor's register identity. Both helpers are namespace-generic and
refuse absent packages with `ProfileError`. `shipped_base()` activates no domain contract: consumers
activate `general` explicitly in `compile_profile`. Distribution validation
(`python/tools/check_shipped_contracts.py`, run under `just check-hygiene`) checks
the complete pinned source inventory independently of activated profiles. Numerical
and methodological tables have the same ownership requirements as other declarations.

The human biology genesis ships alongside `general`: [DOMAIN.yaml](../domains/biology/DOMAIN.yaml)
and [REGISTER.json](../domains/biology/REGISTER.json), with identical packaged copies.
Activate both explicitly. Its five sorts distinguish HGNC gene nomenclature (2025-09-05),
unversioned human Ensembl gene annotations, versioned transcript and translation
annotations (Ensembl 115, GRCh38.p14), and the authored RNA aspect. Identifier syntax
is separate from held-release membership. Ensembl translations can over-split
identical sequences and identify neither measured proteins nor proteoforms.
`transcribed-from` relates transcript to Ensembl gene annotations; `translated-from`
relates translation to transcript annotations. Neither structural template has an
edge or implies expression, equivalence or another claim. The gene-only `regulates`
bridge narrows `general/changes-under-intervention` and inherits its causal edge;
it admits no estimand and supplies no observational support. Gene RNA measurement
uses an explicit procedure and checked Ensembl-to-HGNC correspondence. No protein
or Ensembl-gene measurement is admitted. Its twelve provisional register entries
state these commitments; aggregation does not establish their biological validity.
This is a new genesis replacing the retired v1 molecular-entity vocabulary, with
no cross-base succession or restoration of `affects` and `associates-with`.

Shipped successor archives use
`domains/<namespace>/history/<contract-content-hex>/DOMAIN.yaml` and `REGISTER.json`,
with byte-identical copies under `python/src/beliefs/domains/`. The current paths
stay unchanged. Loading follows only declared 64-lowercase-hex predecessor identities,
checks each ancestor before its successor, and refuses missing or mismatched files,
namespace mismatches, cycles and broken register links. The source checker also
refuses malformed or unreachable archive entries, symlinks, extra files, differing
package copies and missing source ownership evidence in ancestors. General's original
v1 contract and register are preserved under
`history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f/`.
Version 2 preserves all ten original register entries and adds an eleventh,
`assumption-kind:general/procedure-validity`. This provisional admission records
conditional acceptance of an unknown validation domain or recorded scope gap; it
does not establish procedure validity. The procedure record distinguishes unknown
validation from a known map whose restrictions cannot be compared.

Mounting resolves domain pins against the current shipped contract only. A corpus
pinned to general v1 therefore raises `MountPinUnresolved` from the package alone;
the caller must supply that exact predecessor through `available`. Shipping history
does not automatically make archived contracts candidates for mount resolution.

This layout has no independent register-only revision chain: a replacement citing
the prior register for the same contract as `previous` is refused. Prose-only
register history needs a separate route; the checker cannot infer an omitted
history from overwritten bytes. Loading a successor does not re-pin any corpus
manifest, and TypeScript still refuses retirement fields.

The current reproduction source `python/tools/reproduction/mm30-phf19.yaml` is
an ordinary corpus-local genesis, with its six-entry canonical register. Its three
literal dataset bindings are reproduced from the exact shipped local-list bytes.
Its covariance instantiation admits the Cartesian set of gene/factor sorts;
the driver alone enforces the selected heterogeneous PHF19 pair and exact
classification-rule/factor connection. The contrast admission belongs to mm30,
not biology. Its cohort term restricts applicability without asserting assay
validation. Full HGNC membership comes from the entire held release; the shared
Ensembl release remains unconsulted. Referent mapping records carry identifier
provenance and license no RNA-to-protein interpretation. The workflow's explicit
unknown procedure validation freezes a conditional general assumption, and
aggregation supplies neither assay validity nor independence. See the
[authored route](development.md#recreating-the-mm30-corpus) for custody and recovery.

## Coordination contract

The coordination contract requires `contract` (always `coordination`), `version`,
`lineage`, `address_root`, `query_vocabulary` (`kinds` and `relations`) and `kinds`.
It may add `description`. Each kind declares `fields` and `query_versions`. The
package ships versions 1 to 3, and each is parsed against its predecessor. Version 2
is the default, and it adds the `publication` and `publication-binding` kinds, which
only the publish act mints. Version 3 also requires attribution entries on
publication markers.

## Practices

A practice document has exactly four fields: `practice` (a non-empty name),
`version` (a positive integer), `description` and `guidance` (a list of paths).
A practice carries procedure only. It never compiles into a profile.

## Versions

- **3 — 2026-11-17:** Base v6 adds `scope_grammar`; domain contracts may declare
  `scope_relations`, the 22nd declaration family and assumptions-register key kind.
- **2 — 2026-11-13:** Base v4, estimand grammar 3, explicit time-role names and
  finite series boundaries; assessment identity tags stay v2.
- **1 — 2026-11-02:** First public statement of the contract document rules, as
  the code at this revision implements them.


### Contracts read by an assessed target

`consulted.assessed_target_contracts` collects the namespaces named by a complete
frozen target, including copied transitive dependency terms. Operator templates
are read even without a claim. With a claim, its admitting estimand declarations
are checked too. Measurement, functional, output, control, assumptions and scope
terms all count; a calendar convention also reads its conversion and endpoint
units. Authority validation scope and procedure kinds enter through the frozen
record terms. This traversal takes no world reader; `consulted_contracts` accepts
`targets=` and applies pin agreement to the resulting namespaces. Declared scope
context is never part of this body walk: `consulted_contracts` takes the checked
comparisons separately (`scope_comparisons=` with `scope_dependencies=`), recomputes
their selected context, and adds the selected relations', dimensions' and endpoint
sorts' owners and the selected rule bodies' term namespaces.

### Defining source metadata

A domain may declare `defining_source: {id: "urn:example:definitions"}`. The id
must match `^[a-z][a-z0-9+.-]*:[a-z0-9._~:/-]+$` over the entire string.
Both readers preserve an immutable value or explicit absence. Present null,
unknown members and noncanonical spellings refuse. Once present, the source id
must remain through succession; a metadata-free predecessor may acquire it.
The field changes contract content identity, while claim declarations, register
keys and compiled schema projections remain unchanged. Local parse and compile
success provide no global source ownership verdict.


### Source ownership admission

[The canonical inventory](../contracts/source-ownership/INVENTORY.json) binds every
admitted lineage to one canonical definitions source and checked genesis. Its
revision rows follow the checked chain oldest first and pin contract/register
identities and exact file hashes. The authored pair is the normative source:
contract definitions govern declarations and typing; register prose constrains
justified use. A contradiction requires semantic review and resolution, rather
than silently preferring either text. Aliases reserve spellings and appear in
collision diagnostics; contracts must use the canonical id.

The checker covers canonical and packaged domain histories plus contract-bearing
reproduction YAML, retaining five exact heritage exclusions. All sources and
owners are checked together, including owners never activated in the same profile.
Unknown sources, second owners, parallel genesis, unlisted revisions, missing
ancestors, malformed evidence and stale registers refuse. Shadow `general`
contracts remain forbidden outside the canonical general paths.

The four original general v1/v2, biology v1 and mm30 v1 revisions retain their
bytes and absent metadata through an independent immutable adoption map in the
checker. This exception follows exact historical bytes; a changed file or a new
metadata-free revision cannot qualify by updating the inventory. Their next
substantive successor must add the source field and preserve checked history.
The mm30 pair is frozen, including formatting and register prose, until checked
succession support is delivered; its current reproduction loader accepts genesis.
No immediate successor or corpus re-pin is required by this adoption.

Every admission edit requires a coordinated inventory and checker
`SOURCE_INVENTORY_SHA256` update. The checker verifies this exact-byte pin before
interpreting inventory contents. Review compares old/new reservations, aliases,
owners, adoption exceptions and historical pins; changing both editable files can
pass mechanically and does not prove reservation continuity. The inventory is
repository admission evidence, with no packaged mirror or runtime dependency.
A corpus manifest authenticates contract pins, not an inventory verdict.

External rows use `source_pin: {kind: external, documents: [...]}`. Each ordered
normative document pin has exactly `revision`, `sha256`, `held_ref` and `locator`:
a nonempty revision, a lowercase SHA-256 digest, its `sha256:` content address and
an absolute HTTP(S) publisher URL without credentials. Duplicate held references
within a row and equal normative digests across distinct source ids refuse; reuse
across revisions of the same source is allowed. Alias and owner checks still run
on the entire inventory.

Every external revision also requires a success receipt under
`contracts/source-ownership/receipts/<sha256>.json`, independently pinned by the
checker's `RECEIPT_SHA256`. Receipts and their embedded historical inventories are
repository-only metadata, outside the wheel. Hygiene checks strict receipt schema,
exact hashes, historical reservation continuity, source/owner/genesis, contract and
register identities/hashes, source pins and agreement with parsed unit mappings.
Unchanged predecessor bytes can move to history paths without replacing the
receipt. An unrelated authored successor needs no external payload or new receipt;
a new external revision does. Receipt coverage is per revision, while its complete
admission-time inventory remains embedded for audit.

Hygiene opens repository metadata only; it neither imports refs/RDFLib nor checks
held UCUM/QUDT membership or current custody. Portable receipts carry public
locators, content addresses and code provenance, never local evidence paths or
private review text. Coordinated pin edits remain reviewable assertions, not proof
of honest execution. The shipped inventory includes the SI Brochure time genesis
under `urn:beliefs:source:bipm-si-brochure`, with canonical domain/register files
in `domains/si-brochure/` and byte-identical packaged copies. Its six provisional
entries cover interval duration, periodic frequency, second, fixed elapsed hour,
hertz and the exact 3600 hour-to-second conversion. The register excludes civil and
calendar time, clock calibration, generic incidence and angular frequency.

The definitions and unit relation are adapted from the BIPM, *The International
System of Units (SI)*, ninth edition V4.01 (June 2026),
[DOI 10.59161/AUEZ1291](https://doi.org/10.59161/AUEZ1291), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Local quantity names,
dimension vectors and interval/calendar restrictions are beliefs encodings; they
do not reproduce the full Brochure definitions. The complete bilingual source
PDF is pinned in the inventory. UCUM 2.2 codes `s`, `h`, `Hz` and QUDT 3.5.3 unit
IRIs `http://qudt.org/vocab/unit/SEC`, `http://qudt.org/vocab/unit/HR`,
`http://qudt.org/vocab/unit/HZ` were checked against held release bytes and semantic
review before genesis. The public receipt records those evidence digests and
results. Mapping strings are immutable under succession; units cannot be retired.
Reissuing second or hertz under a new id also requires a base successor because
`time_roles` fixes their identifiers.

Existing unit parsing checks external mapping keys and nonempty strings; complete
release validation and human semantic review precede external genesis. Mechanical ownership
cannot detect copied meanings under different ids or prove semantic equivalence.
Unshipped candidates require joint review against the admitted inventory and
other candidates; local parse/compile success makes no global ownership claim.
