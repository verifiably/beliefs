# Records

Type: data model; document types 1. This document describes the records a beliefs
corpus holds: their fields, how each is identified, the invariants the write boundary
and the readers enforce, and what decoding rejects. The code accepts one identity
encoding, `science.identity.v1`, and one version of each grammar the base contract
declares (claim grammar 1, estimand grammar 1, composite grammar 1). The other
reference documents are [contracts.md](contracts.md), which covers the contracts
that declare kinds, facets and vocabulary, and [writes.md](writes.md), which covers
how a record reaches a corpus.

## Corpus

A corpus is a directory of records with a `corpus.yaml` manifest. The manifest has
exactly three fields: `manifest_version` (the integer `2`), `corpus_id` (32 lowercase
hexadecimal characters) and `profile`. A fork adds a fourth, `forked_from`, with
exactly `corpus_id` (32 hex) and `corpus_state` (64 hex). `profile` has exactly
`science_contract`, which pins the base contract as `science:<64 hex>`, and
`domains`, which maps each domain namespace to `<namespace>:<64 hex>`. When the
pins disagree with the profile a writer holds, the write is refused before any
effect, and a read through a `ReadView` is refused when the pinned base is not the
one the runtime ships.

Each record is a `nodes` node. The fields this document uses are `id`, written
`<kind>:<local>`; `uid`; `kind`; `title`; `body`; `relations`; and `facets`, a
mapping from facet key to payload. A record must render to Markdown and parse back
to an equal node, and one that does not is refused.

## Record kinds

The Science base contract (`contracts/science/CONTRACT.yaml`) declares fourteen
world kinds and three prose kinds. A world kind is either governed, meaning the
contract names an identity domain for it, or ungoverned (only
`instrument-certification`). A kind's required facet is present on every record of
that kind.

| Kind | Required facet | Enters through |
|---|---|---|
| `proposition` | `proposition` (the claim) | `add`, `supersede`, `revise` |
| `source-assertion` | `source-assertion` | `add` |
| `assessment` | `assessment` | `add` |
| `analysis-spec` | `analysis-spec` | `add` |
| `run` | `run` (optional `run-closure`) | `add`, run routes |
| `verification` | `verification` | `add` |
| `dataset` | `dataset` (optional `empirical-observation`, `lineage-basis`) | `add`, `revise`, acquisition |
| `source` | `source` (optional `identifier-correction`) | `add`, `correct_identifier` |
| `holdings-observation` | `holdings-observation` | holdings acts only |
| `retraction` | `retraction` | `retract` only |
| `instrument-certification` | none | `add` |
| `coreference-attestation` | `coreference-attestation` | `attest_coreference` only |
| `act-report` | `act-report` | operations only (and import) |
| `composite` | `composite` | `add`, `supersede` |

The base contract names a reader for each kernel facet, but that name is not
resolved or called: the code checks each facet where it is used. At the write
boundary, `add` checks that a record's kind and facets are in the compiled profile,
checks every schema-shaped facet (`empirical-observation` and domain facets)
against its fields, and decodes the `display`, `analysis-spec`, `verification`,
`dataset`, `source`, `composite` and `run-closure` facets. `retract` and
`attest_coreference` decode their own records, and import decodes act reports. A
proposition's claim, an assessment's facet, a `lineage-basis` and a run without a
closure are checked only when read. A `source-assertion` record must carry its
facet, as the profile requires, but the facet's payload is never checked: its
declared reader does not exist.

The prose kinds, `interpretation`, `discussion` and `story`, carry only an optional
`display` facet. They have no identity domain and never enter a belief's inputs.
View and coordination kinds (`project`, `task` and others) come from the coordination
contract; see [contracts.md](contracts.md#coordination-contract).

## Relations

A relation is a `(source, predicate, target)` triple. The base contract declares
each predicate's signature:

| Predicate | From | To |
|---|---|---|
| `assesses` | assessment | proposition |
| `observes`, `reads`, `transforms`, `produces` | run | dataset |
| `produced_by` | assessment | run |
| `executes` | run | analysis-spec |
| `targets` | analysis-spec | proposition |
| `verifies` | verification | assessment |
| `member_of` | source | dataset |
| `composes` | composite | proposition |
| `grounded-in` | retraction | retraction, verification, source |
| `supersedes` | proposition, composite | a record of the same kind |
| `retracts` | retraction | assessment, retraction, verification |
| `succeeded-by` | retraction | retraction |
| `anchored_in` | source-assertion | source |

The write boundary enforces these signatures:

- an `assesses` target must resolve in the corpus and be a proposition;
- a `supersedes` edge to a record of another kind is refused;
- each `composes` target must be a proposition, with one edge per member;
- a `verifies` target must be an assessment (when the verification carries a
  report and an assessment);
- a `retracts` node target must be an assessment, a retraction or a verification.

The other signatures are declarations that the write boundary does not check.
Audit reports a `supersedes` edge across kinds that was written around the
boundary.

## Identity

Identity values are encoded under `science.identity.v1`:

- The admissible values are strings, booleans, integers, decimals, lists and
  objects. `null`, binary floats, non-finite decimals and any other type are
  refused.
- A string is normalised to NFC. An unpaired surrogate is refused. Only `"`, `\`
  and the C0 controls are escaped: `\b \t \n \f \r` take their short forms and every
  other control takes `\u00xx`. Everything else, including non-ASCII characters
  and `/`, is literal UTF-8.
- Object keys are strings, sorted by code point. Two keys that become equal after
  NFC normalisation are refused, never merged.
- An integer has no decimal point. A decimal is written in plain notation, keeps at
  least one fractional digit and has trailing zeros removed. Zero is `0.0`.
- `digest(domain, value)` is the lowercase hexadecimal SHA-256 of the domain's UTF-8
  bytes, a newline, and the canonical bytes. The domain must match
  `science.<kind>.v<n>` with a positive version.

A governed record carries a `semantic-identity` facet whose `digest` field is taken
under the kind's domain (for example `science.proposition.v1`). It covers the kind, the
list of covered facets present on the record, and their payloads. It never covers
`id`, `uid`, `title`, `body` or the `display` facet, so editing prose leaves a
record's identity unchanged. A governed record with a missing or stale stamp is
refused at the write boundary and refused again when `ReadView.get` reads it. If a
raw edit changes the fields and the stamp together, this check cannot detect it.

Some records are content-addressed: their id is derived from their content.

- A dataset's id is `dataset:sha256:<hex>`. The hex is the SHA-256 of its declared
  resource digests, deduplicated, sorted, and each terminated by a newline.
- A source's id is `source:` followed by the digest of `{scheme, value}` under
  `science.source-address.v1`, where the scheme is its first accepted external
  identifier in the order `doi`, `pmid`, `isbn`, `accession`. There is no fallback
  to a title or year.
- An analysis spec's id is its spec identity under `science.spec.v1`. An act
  report's id is the digest of its facet under `science.act-report.v1`, and a
  retraction's is the digest of its facet under `science.retraction.v1`.
- A run that carries a `run-closure` facet has the id `run:<digest>`, taken over
  the closure projection under `science.run.v1` to `science.run.v4` (chosen by the
  recipe version and whether the run was confined).
- A verification that carries a report has the id `verification:<digest>`, taken
  under `science.run-verification.v1` over its two runs, its assessment if any,
  its rule, the report's identity, its scope rule, scope and verdict, and
  `supersedes` when present.

A record whose id does not match its derived address is refused.

A claim's identity is `I_claim = digest("science.claim.v1", π_claim)`. Here
`π_claim` is `{operator, args, qualifiers, polarity, layer}`, and every value in it
is an identifier. The arguments are listed as their terms in slot order, and each
qualifier as `{quantifier, restriction}`. The polarity of a sign-inapt operator is
always present as the tag `inapt`. Contract releases, sorts and prose never enter
`π_claim`.

## Propositions and claims

When read, a proposition's `proposition` facet must have exactly the fields
`operator`, `args`, `qualifiers`, `polarity` and `layer`. A typed claim satisfies
the following rules:

- the number of arguments equals the operator's arity, and each argument's sort is
  the one its slot declares;
- each qualifier uses a dimension the operator permits, a quantifier from `generic`,
  `universal` and `existential`, and a restriction of the dimension's sort;
- a sign-apt operator has a polarity of `positive`, `negative` or `unsigned`. A
  sign-inapt operator is stored with the tag `inapt`; an author supplies no
  polarity for it, and supplying one is refused;
- the layer is one of the layers the operator admits.

`add` does not type the claim. It is typed whenever it is read through
`claim_from_stored`: when an analysis spec that targets the proposition is written
or audited, and when belief or a composite reads it. A semantic change is made by
superseding the proposition: the successor is a new record linked to it by
`supersedes`. `revise` changes only `title`, `body` and the `display` facet.

## Specs, runs and assessments

An `analysis-spec` facet has exactly two fields: `identity` and `projection`. The
`projection` is the canonical text of the frozen spec: its target, estimand,
method, input roles, applicability, rules and parameters. The text, the identity
and the record id must all agree. The spec's estimand must name the claim identity
and the operator of the proposition it targets, which must resolve in the same
corpus.

A `run` facet names the spec the run executes, when it has one. A run's inputs are
typed by role. `observes` names held data and is the only role that can make an
assessment eligible. `reads` never makes one eligible, in any quantity. `transforms` and
`produces` record dataset lineage.

When read, an `assessment` facet must have exactly six text fields: `spec`, `run`,
`proposition`, `outcome`, `interpretation_rule` and `typed`. `outcome` is
`supported`, `refuted` or `inconclusive`. `typed` is canonical
`science.identity.v1` text that carries the estimand and the applicability, and
optionally the estimate (a decimal) and its uncertainty (an interval with a level,
or a standard error). A record minted before
the estimand grammar is refused by name (`PreGrammarAssessment`) and is never
converted. At the write boundary, a record that carries an `assesses` edge must
name a run that resolves, and at least one of the run's `observes` inputs must
have empirical standing — either carrying a valid `empirical-observation` facet
directly or inheriting standing through a complete, undiverged `lineage-basis`
chain from an ancestor dataset that carries one. The chain is the one
independence certification walks: a `conflict` basis or a producer whose
`transforms` differ from the route refuses as `lineage-divergent`, and a missing
producing run or ancestor, a cycle, or a basis whose every route is retired
refuses as `lineage-incomplete`. A dataset carrying the facet and a basis, or
produced by a run, is refused as before. Route retractions are folded only when
a route in the chain records an identity, which boundary-minted routes never do;
a malformed or cyclic retraction then refuses standing. `corpus_check` reports an
unmet rule as `eligibility-unmet`, and one resting on a run, producer or ancestor
the corpus does not hold as `eligibility-unresolved`.

## Verifications

A verification has one of two shapes:

- **Published**, carrying a `report`. Its facet has exactly the required fields
  `scope`, `verdict`, `derivation`, `rule`, `scope_rule` and `report`, and the
  optional fields `assessment` and `supersedes`. `derivation` names exactly two
  runs, `original` and `replayed`. `report` is the comparison report:
  `original_conformance`, `replay_conformance`, two `receipts`, `rule_bindings`
  and `diagnostics`, optionally with `certification` and `citation`. An assessment
  verification carries `assessment` (the assessment's identity) and exactly one
  `verifies` edge. A dataset-production verification carries neither. The id must
  recompute from the fields (see [Identity](#identity)).
- **Without a report.** The facet is expected to carry `assessment`, `scope`,
  `verdict` and, optionally, `supersedes` and `derivation`. The write boundary
  admits it without decoding it further. When it is read for admission or belief,
  only `scope` and `verdict` are checked, and a missing `assessment` reads as
  empty. Audit also reads `derivation` and reports a malformed one as an error.

The scope is one of `same-environment`, `clean-environment`,
`independent-implementation` and `not-certified`. The verdict is one of `passed`,
`failed` and `inconclusive`. A published verification is checked against these
sets when it is written, and one without a report when it is read. When a
verification carries both a report and an assessment, its `verifies` target must
resolve and must be an assessment that carries the named identity.

An assessment's verification state is derived and never stored. It is `invalidated`
if any active verification failed. It is `admitted` if one active verification
passed in a clean environment. Otherwise it is `not-admitted`.

## Datasets, sources and holdings

A `dataset` facet lists `resources`, each with a `name` and a `digest` written as
`<algorithm>:<lowercase hex>`. The only accepted algorithm is `sha256`. A dataset
with any unpinned resource has no content identity and is refused. A dataset is
*held* only when an observation matches every declared digest, and heldness is
derived at read time, never stored.

The `empirical-observation` facet has three fields:

- `locator` (required) uses the `accession`, `url` or `instrument` scheme;
- `attested_by` (required) must equal the writer's actor, except on import, where
  an arriving record keeps its attestation;
- `retrieval` (optional) is an `act-report:` reference.

`revise` may change only a dataset's prose, its `empirical-observation` facet and
its domain facets. It cannot remove an existing `empirical-observation` facet.

A `source` facet holds `identifiers`, each stored in canonical form. An ordinary
`add` refuses a correction history: `correct_identifier` writes one, and import and
relocation carry it.

A `holdings-observation` records one look at one location. Its `location` is
either `{type: store, store_id, relative_path}` or `{type: url, url}`. Its `outcome`
is either `{finding: found, digest}` or `{finding: absent}`. It also has the fields
`observer`, `instrument`, `event_token`, `observed_at` and `supersedes` (a list of
observations), and an optional `expected`. Holdings acts alone mint observations.

## Other world records

A `retraction` targets one of three arms:

- `node`: a record;
- `route`: a dataset route;
- `snapshot`: a producer's snapshot identity.

Its `reason` is one of `authored-error`, `corrupt-input`, `defective-code`,
`environment-miscapture`, `false-certification`, `upstream-retraction` and
`wrong-route`. It also carries a non-empty `rationale`, at least one ground, its
`actor` and `event_token`, and an optional `successor`.

A `coreference-attestation` names exactly two distinct endpoints, sorted and in NFC.
It also carries a `stance` of `1` or `-1`, an `actor`, `grounds` and an
`event_token`.

A `composite` facet has exactly four fields: `grammar`, `shape` (`dag`), `nodes` (a
list of `{sort, term}`) and `members` (claim identities), plus one `composes` edge
per member. Each member must be a causal-layer claim whose operator declares an edge
in a domain contract, and every argument of the claim must be a declared node. A
cycle is refused, whatever the signs of its edges. An assessment cannot assess a
composite.

An `act-report` carries only its `act-report` facet and its identity stamp, and has
no relations. The facet's fields are `operation` (one of the operation kinds in
[writes.md](writes.md#operations)), `event_token`, `actor`, `observer`,
`instrument`, `opened_at`, `closed_at` and `entries`. Each entry records one member
act's subject and outcome. An act report never feeds a belief.

## Beliefs

A belief is not a record. `evaluate` takes an exact `PolicyBinding` (a rule identity
and an implementation identity) and returns one of three answers:

- `Belief(value, belief_input_digest, policy_binding)`, whose value is an
  integer; the shipped policy is `science.belief.v1`;
- `NoBelief(reason)`, where the reason is one of `unavailable-policy-unheld`,
  `unavailable-fixtures-unheld`, `unavailable-input-unheld`,
  `unavailable-corpus-absent`, `no-eligible-assessment` and
  `no-directional-outcome`;
- `Refused(reason)`.

An assessment counts only when it is admitted. That requires its run to have an
`observes` input, every input to be held, and its verification state to be
`admitted`. A `supported` assessment counts `+1`, a `refuted` one `-1`, and an
`inconclusive` one `0`.

## Encoding and parity

`ts/` is a second implementation of `science.identity.v1`, `π_claim` and `I_claim`,
together with the claim typing those require. `fixtures/` is the parity corpus that
both test suites read and neither writes:

- `fixtures/identity-v1.json` holds encoding vectors (value, canonical bytes,
  digest);
- `fixtures/claim-identity-v1.json` holds claims built from their components under
  the base contract and `fixtures/contracts/testing.yaml`.

The TypeScript side computes neither contract nor profile identity. It refuses any
contract that declares a predecessor or a retired identifier.

## What decoding rejects

- `science.identity.v1` text whose re-encoding differs from its bytes: this covers
  malformed UTF-8 or JSON, `NaN` and `Infinity`, keys out of order or duplicated,
  and non-canonical numbers (`CanonicalTextRefused`).
- A stored claim facet with missing or extra fields, or with `args` that is not a
  sequence or `qualifiers` that is not a mapping (`MalformedWireClaim`).
- A claim that breaks a typing rule (`ArityMismatch`, `ArgumentSortMismatch`,
  `UndeclaredDimension`, `UnknownQuantifier`, `RestrictionSortMismatch`,
  `PolarityRefused`, `InadmissibleLayer`).
- A claim whose referent was checked against a vocabulary the decoder holds and is
  not in it (`UnboundReferent`). Decoding a claim does not refuse retired
  identifiers; authoring a new one does (`WithdrawnFromAuthoring`).
- A stored estimand or applicability that does not restore against the profile
  (`MalformedWireEstimand`, `MalformedRecord`).
