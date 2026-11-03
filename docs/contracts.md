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
TypeScript mirror in `ts/` reads only base and genesis domain contracts.

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
`relations` and `facets`.

- `claim_grammar` holds `version`, `tag_encoding` (`science.identity.v1`),
  `quantifiers`, `polarities`, `sign_inapt_tag` and `layers`. The sign-inapt tag
  must not also be a polarity.
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

Sorts, dimensions, operators and edges may carry `description` and `retired`.

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
- the successor drops an identifier its predecessor declared;
- the successor changes the meaning-bearing fields of a declaration;
- the successor un-retires an identifier.

`description` and `retired` are outside that comparison. A retired identifier can
still be decoded, so stored claims stay readable, but it can no longer be used to
author a new claim.

## Profiles

`compile_profile(base, domains, coordination=...)` accepts only parsed contracts.
It refuses in four cases:

- a domain contract was parsed against a different base contract;
- two contracts contribute to one namespace;
- a domain facet attaches to a kind that is not a world kind;
- a coordination contract's query vocabulary falls outside the kernel's world
  kinds and relations.

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

## Adding a domain contract

1. Write the document with `lineage: genesis`. Name each operator's sorts, layers
   and dimensions, and add `estimands` and `edges` where specs and composites need
   them.
2. Load it with `load_domain_contract(path, base=..., predecessor=None)`, then
   compile it with the base contract into a profile.
3. Pin the new contract in a corpus's manifest, by adopting the manifest under that
   profile.
4. To change the contract later, write a successor that names the old contract's
   identity, and retire identifiers instead of removing them.

A pack shipped with beliefs is read from
`python/src/beliefs/domains/<namespace>/DOMAIN.yaml`. The biology pack also has a
copy at `domains/biology/DOMAIN.yaml`, and a test checks that the two are
byte-identical.

## Versions

- **1 — 2026-11-02:** First public statement of the contract document rules, as
  the code at this revision implements them.
