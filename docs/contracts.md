# Contracts

Type: standard, data model; document types 1. This is version 1 of the rules that
contract documents must satisfy. A contract is a YAML document that declares the
vocabulary records may use. The Science base contract declares kinds, relations,
facets and the closed grammars. A domain contract declares operators, sorts,
dimensions, estimands, edges and namespaced facets. The coordination contract
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
TypeScript mirror in `ts/` is narrower. It reads only base contracts and genesis
domain contracts. It refuses `retired` on any declaration, and it refuses a
`description` at the top level of a domain contract and on its sorts and
dimensions, although the Python parser accepts all of these.

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
integer), `lineage`, `sorts`, `dimensions` and `operators`. It may add
`description`, `facets`, `estimands` and `edges`. It declares no `kinds` or
`relations`. Its namespace may be neither `science` nor `coordination`.

- **Sorts.** A sort has a `vocabulary`, bound either to `{namespace, release}` or
  to `dataset:<content identity>`. A bare namespace is refused.
- **Dimensions.** A dimension has a `restriction_sort`.
- **Operators.** An operator has `arity`, `arg_sorts` (one per slot), `sign_apt`,
  `layers` and `dimensions`. `layers` must be non-empty and drawn from the base
  contract's layers. Each dimension must be one this contract declares.
- **Sort references.** A sort reference is a local sort name, or
  `<other-namespace>/<sort>` for a sort another activated contract declares. The
  base namespace cannot be referenced, and neither can the contract's own
  namespace in prefixed form.
- **Estimands.** An estimand declaration is keyed by one of this contract's
  operators, which must have an arity of at least 1. It has `level_sorts` (keyed by
  slot index, written as decimal text), `measure_sort`, `identification_sort` and
  `conditioning_sort`.
- **Edges.** An edge declaration is keyed by one of this contract's operators. That
  operator must admit the `causal` layer, and the declaration names distinct
  `cause` and `effect` slots.
- **Facets.** A domain facet declares `attaches_to` (world kinds) and `fields`. Its
  key in a profile is `<namespace>/<name>`.
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
  against.

Sorts, dimensions, operators and edges may carry `description` and `retired`.

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
- the successor drops a claim-vocabulary identifier its predecessor declared;
- the successor changes the meaning-bearing fields of a claim-vocabulary
  declaration;
- the successor un-retires a claim-vocabulary identifier.

The claim vocabulary is the contract's sorts, dimensions, operators, estimands and
edges. Facets are not compared under succession. `description` and `retired` are
outside the comparison. A retired identifier can
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
- a cross-contract sort reference names a sort no compiled contract declares.

A compiled term is `<namespace>/<name>`, and that term is what enters a claim. The
profile's compiled identity changes when a meaning-bearing field changes, and stays
the same after a description edit. A corpus manifest pins the base contract and
every activated contract by content identity. A writer whose profile disagrees with
those pins is refused.

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
