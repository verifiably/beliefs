# Contracts

Type: standard, data model; document types 1. This is version 1 of the rules that
contract documents must satisfy. A contract is a YAML document that declares the
vocabulary records may use. The Science base contract declares kinds, relations,
facets and the closed grammars. A domain contract declares sorts, dimensions,
relation templates, instantiations, bridges, estimand declarations, duration
conventions and namespaced facets. The coordination contract
declares view and coordination kinds. A compiled profile combines a base contract,
a set of domain contracts and optionally a coordination contract. The code accepts
base contract version 1 (claim, estimand and composite grammar version 1), any
positive domain contract version in a genesis or successor lineage, coordination
contract versions 1 to 3, and corpus manifest version 2. The records these
contracts govern are described in [records.md](records.md), and the writes that
check them in [writes.md](writes.md).

## Scope

These rules bind anyone who writes a contract document. That includes authors of
domain contracts kept outside this repository, such as the corpus-local contract
documents `science` loads, as well as the packs beliefs ships. The Python parser
in `beliefs.contract` checks each rule below when it loads a document. The
TypeScript mirror in `ts/` is narrower. It reads base contracts and the domain
grammar described below with the same refusals, and it compiles a profile with the
same compile refusals, but it computes no content identity and runs no succession
check. So it reads only a genesis domain contract: a `lineage` naming a predecessor,
and a `retired` field on any declaration, are refused with `UncheckableContract`. It
also refuses `description` at a domain contract's top level and on a sort or a
dimension, as an unknown field.

## Documents

- A contract is YAML. Every mapping key is a string, and a duplicate key at any
  depth is refused, never resolved in favour of the last occurrence.
- Unknown fields are refused, never ignored, and missing required fields are
  refused. An identifier matches `[a-z][a-z0-9-]*`.
- A contract's content identity is the `science.identity.v1` digest of the whole
  parsed document: under `science.contract.v1` for base and domain contracts, and
  under `science.coordination-contract.v1` for the coordination contract. Any edit,
  including an edit to a description, gives the contract a new identity.

## Base contract

The base contract has exactly these fields: `contract` (always `science`),
`version`, `claim_grammar`, `estimand_grammar`, `composite_grammar`, `kinds`,
`relations` and `facets`. The shipped base is version 2.

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
- `estimand_grammar` holds `version` and `tag_encoding`, plus `contrast_kinds`,
  `scales` and `uncertainty_kinds`. Those three must equal exactly the sets the
  implementation operates: `levels, continuous`, `additive, multiplicative` and
  `interval, standard-error`.
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

A writer accepts only the base contract the runtime ships.

## Domain contracts

A domain contract requires `contract` (its namespace), `version` (a positive
integer), `lineage`, `sorts` and `dimensions`. It may add `description`,
`templates`, `instantiations`, `bridges`, `estimands`, `duration_conventions` and
`facets`. Any other top-level field is refused, `kinds` and `relations` included,
and so are the v1 fields `operators` and `edges`: a v1 document cannot parse under
base v2. Its namespace may be neither `science` nor `coordination`. Each table is
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
  `?`, `{m}` and `{m,n}` (bounds up to 65535), and backslash escapes of the metacharacters; anything else, a
  non-NFC pattern, an unescaped `[` in a class and a doubled `&&`, `~~` or `||` in a class included, is refused as a malformed contract. Terms are normalized to NFC
  and matched whole, with `.` and negated classes matching any code point including line
  terminators: Python uses `re.DOTALL` with `fullmatch`, TypeScript uses
  `^(?:pattern)$` with the `s` and `u` flags, and authors set no flags.
  `fixtures/identifier-patterns-v1.json` is the oracle both implementations are tested
  against. Write a pattern as a single-quoted YAML scalar: a double-quoted scalar
  reads `\-` as an escape YAML does not define, and the document is refused.
- **Dimensions.** A dimension requires `restriction_sort`, `placement` (`claim` or
  `applicability`) and `applies_to`, a list of operators (templates or bridges) a
  claim over which may carry it.
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
- **Estimands.** An estimand declaration is keyed by the typed local address of its
  target, `instantiation:<name>` or `bridge:<name>`, which must name a declaration
  of that kind in the same document. It has `level_sorts` (keyed by role name),
  `measure_sort`, `identification_sort` and `conditioning_sort`, and may add
  `description`. These are the interim estimand fields; the estimand grammar's own
  design replaces them.
- **Duration conventions.** A duration convention is a mapping of fields, each a
  string or an integer. No field is validated yet; its projection is the mapping.
- **Facets.** A domain facet declares `attaches_to` (world kinds) and `fields`. Its
  key in a profile is `<namespace>/<name>`.

Estimand declarations and duration conventions carry no `retired`.

How to write, load and ship a domain contract is in
[development.md](development.md#adding-a-domain-contract).

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

The claim vocabulary is seven tables: sorts, dimensions, templates,
instantiations, bridges, estimand declarations and duration conventions. Each
declaration is keyed by its typed address, `sort:<name>`, `dimension:<name>`,
`template:<name>`, `instantiation:<name>`, `bridge:<name>`,
`estimand:instantiation:<name>` or `estimand:bridge:<name>`, and
`duration-convention:<name>`, so declarations sharing a local name in two tables
are compared separately. Sets (layers, forms, categories, constraints, `applies_to`,
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
- an estimand declaration's `level_sorts` names a role its target's template lacks.

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
when it is not retired and some live route (a live instantiation, or the live
bridge) lists a live sort for every role that must be filled.

The profile's compiled identity is taken over every table keyed by term (estimand
declarations by typed address), so activation order cannot move it; it changes
when a meaning-bearing field or a retirement changes, and stays the same after a
description or definition edit. A corpus manifest pins the base contract and every
activated contract by content identity. A writer whose profile disagrees with
those pins is refused.

No domain contract ships with the package under base v2:
`shipped_domain_contract(namespace)` refuses every namespace.

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
