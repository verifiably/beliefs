# Contracts

Type: standard, data model; document types 1. This is version 1 of the rules that
contract documents must satisfy. A contract is a YAML document that declares the
vocabulary records may use. The Science base contract declares kinds, relations,
facets and the closed grammars. A domain contract declares sorts, dimensions,
relation templates, instantiations, bridges, estimand declarations, measurement
vocabulary and admissions, duration conventions and namespaced facets. The
coordination contract declares view and coordination kinds. A compiled profile
combines a base contract, a set of domain contracts and optionally a coordination
contract. The shipped base is version 3, with claim and estimand grammars 2 and
measurement and composite grammars 1. Domain contract versions are positive
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
with several faults the two sides can report different ones first. It computes no content identity and runs no succession check. So it reads
only a genesis domain contract: a `lineage` naming a predecessor, and a `retired`
field on any declaration, are refused with `UncheckableContract`. It
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
`composite_grammar`, `kinds`, `relations` and `facets`. The Python and TypeScript
parsers require a positive integer for the base and composite versions. Claim
and estimand grammars require version 2; measurement grammar requires version 1.

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
- `estimand_grammar` requires version 2 and `science.identity.v1` tag encoding.
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
- Each kind has a `role` of `world` (the default) or `prose`, an identity `domain`
  of the form `science.<kind>.v<n>`, and `facets`, which map each facet key to
  `{required, covered}`. A prose kind has no domain and no facet except `display`.
- Each relation has a `group` (`world` or `lifecycle`), `sources` and `targets`
  (declared kinds), and an optional `same_kind`, which requires `sources` and
  `targets` to be equal sets. `composes` must be composite → proposition.
- A base facet is either `reader`-shaped, naming its reader, or `schema`-shaped,
  declaring `fields`.

A writer requires the identity of the shipped base contract.

## Kernel commitments (Layer 0 register)

The kernel is domain-independent, but its representation is not assumption-free.
This register describes the shipped base version 3 and the operations that use it:
claim and estimand grammars 2, measurement and composite grammars 1. It records
what those choices preserve, what they leave unestablished, and the identity cost
of changing them. Update it when the corresponding behavior changes.

There are four places for commitments:

- **Kernel structure**, recorded here: the closed grammars, identity projections,
  admission and aggregation rules that every field uses.
- **Shared vocabulary**, declared by `general`: cross-domain meanings such as
  quantity kinds, units and relation templates. Activating the pack is explicit;
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
[succession](#succession-and-retirement) preserves meaning-bearing fields. New meanings need
new identifiers. Analysis particulars instead enter the frozen spec and assessed
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
`identification_classes`, `designs`, `selection_mechanisms`, `measurements`, `aspects` and
`facets`. Any other top-level field is refused, `kinds` and `relations` included,
and so are the v1 fields `operators` and `edges`: a v1 document cannot parse under
base v3. Its namespace may be neither `science` nor `coordination`. Each table is
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
  (`dataset:` and 64 lowercase hex characters), `rule` is a `classification-rule:`
  record id and `run` a `run:` record id, each a kind the base contract declares.
  `world_kind` names a world kind the base contract declares. A `world-kind` sort
  declares no `identifier_class` (the kernel's record-id grammar is its class);
  every other sort must declare one. A sort's schema projection is its binding
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
- **Dimensions.** A dimension requires `restriction_sort`, `placement` (`claim` or
  `applicability`) and `applies_to`, a list of operators (templates or bridges) a
  claim over which may carry it. An applicability-side dimension also requires
  `restriction`; a claim-side dimension refuses that field. Its closed forms are
  `{form: term, sort: <sort>}`, `{form: interval, quantity_kind: <quantity-kind>}`,
  `{form: time-interval}`, `{form: rule, classes: <sort>}`, and
  `{form: union, of: <one non-union restriction>}`. References resolve at compile.
  A `term` restriction's sort must match `restriction_sort`, which remains required
  for claim qualifiers and dimension metadata. Every form refuses fields belonging to another.
- **Templates.** A template requires `roles`, `sign_apt`, `layers` and `forms`, and
  may add `edge`, `definition`, `external`, `description` and `retired`.
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
  and its namespace for the conversion-property adapter.
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

Estimand declarations, duration conventions, the five numerical measurement tables,
the vocabulary tables and the two pack tables carry no `retired`. Templates
require at least one role at parse time. Compiled instantiations, bridges and
estimand declarations carry an explicit declaration kind.

The five measurement tables may be declared by any domain namespace; shipped packs
restrict them to `general` (see [Profiles](#profiles)). Their
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
- the successor drops a claim-vocabulary declaration its predecessor declared;
- the successor changes the schema projection of a claim-vocabulary declaration;
- the successor un-retires a claim-vocabulary declaration.

The claim vocabulary covers all 21 domain declaration families: sorts, dimensions,
templates, instantiations, bridges, estimand declarations, duration conventions,
the seven methodological tables (`functionals`, `identification_classes`, `designs`,
`selection_mechanisms`, `procedure_kinds`, `aggregation_rules` and
`assumption_kinds`), the two pack tables (`measurements` and `aspects`) and the
five numerical measurement tables (`quantity_kinds`, `units`, `constants`,
`conversions` and `transformations`). Under succession each declaration is keyed by
its local typed address: `sort:<name>`, `dimension:<name>`, `template:<name>`,
`instantiation:<name>`, `bridge:<name>`, `estimand:instantiation:<name>` or
`estimand:bridge:<name>`, `duration-convention:<name>`, `functional:<name>`,
`identification-class:<name>`, `design:<name>`, `selection-mechanism:<name>`,
`procedure-kind:<name>`, `aggregation-rule:<name>`, `assumption-kind:<name>`,
`measurement:<key>`, `aspect:<key>`, `quantity-kind:<name>`, `unit:<name>`,
`constant:<name>`, `conversion:<name>` and `transformation:<name>`.
Assumptions-register coverage (`register_entry_keys`, see
[records.md](records.md#assumptions-registers)) uses the same 21 family tags but
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

The package ships one genesis domain contract, `general` (`domains/general/DOMAIN.yaml`
and its byte-identical packaged copy `python/src/beliefs/domains/general/DOMAIN.yaml`),
together with its canonical assumptions register (`domains/general/REGISTER.json` and
`python/src/beliefs/domains/general/REGISTER.json`). `shipped_domain_contract("general")`
parses the contract against the shipped base, and `shipped_assumptions_register("general")`
decodes the canonical register projection while verifying its `describes` digest and
complete `register_entry_keys(contract)` coverage. Both helpers refuse every other
namespace with `ProfileError`. `shipped_base()` activates no domain contract: consumers
activate `general` explicitly in `compile_profile`. Distribution validation
(`python/tools/check_shipped_contracts.py`, run under `just check-hygiene`) rejects
non-`general` declarations in the numerical tables and shared methodological tables
except reviewed field-specific `functional` or `procedure-kind` classifications.

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
`targets=` and applies pin agreement to the resulting namespaces.
