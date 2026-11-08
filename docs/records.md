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

The Science base contract (`contracts/science/CONTRACT.yaml`) declares sixteen
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
| `exposure-event` | `exposure-event` | `add`, `revise` |
| `reservation-assignment` | `reservation-assignment` | `add` (a chain root), `supersede`, `revise` |

The base contract names a reader for each kernel facet, but that name is not
resolved or called: the code checks each facet where it is used. At the write
boundary, `add` checks that a record's kind and facets are in the compiled profile,
checks every schema-shaped facet (`empirical-observation` and domain facets)
against its fields, and decodes the `display`, `analysis-spec`, `verification`,
`dataset`, `source`, `composite`, `run-closure`, `exposure-event` and
`reservation-assignment` facets. `retract` and
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
| `supersedes` | proposition, composite, reservation-assignment | a record of the same kind |
| `retracts` | retraction | assessment, retraction, verification |
| `succeeded-by` | retraction | retraction |
| `anchored_in` | source-assertion | source |
| `exposes` | exposure-event | dataset, source |
| `concerns` | exposure-event, reservation-assignment | proposition |
| `attested-by` | exposure-event | act-report, run, holdings-observation |
| `considers` | reservation-assignment | exposure-event |
| `evidenced-by` | reservation-assignment | exposure-event |
| `flags` | reservation-assignment | assessment |
| `reports` | reservation-assignment | run |
| `applies` | reservation-assignment | reservation-assignment |

The write boundary enforces these signatures:

- an `assesses` target must resolve in the corpus and be a proposition;
- a `supersedes` edge to a record of another kind is refused;
- each `composes` target must be a proposition, with one edge per member;
- a `verifies` target must be an assessment (when the verification carries a
  report and an assessment);
- a `retracts` node target must be an assessment, a retraction or a verification;
- the edges of an exposure event or a reservation assignment must equal those its
  facet names, and each one's target must resolve to a record of the kind the table
  gives (see [Exposure events and reservation
  assignments](#exposure-events-and-reservation-assignments)).

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
- A tree is a dataset resource that is a directory. Its tree file is the line
  `science.dataset-tree.v1` and a newline, then the canonical `science.identity.v1`
  bytes of `{"members": [{"digest", "path", "size"}, ...]}`. Members are files only,
  sorted by path in code-point order. Each `path` is a store-relative path in NFC
  with no component beginning `.#~`, each `digest` is `sha256:`, each `size` is a
  non-negative integer, and no path is both a file and a directory. The tree's
  digest is `sha256-tree:<hex>`, the `science.identity.v1` digest of that member
  list under `science.dataset-tree.v1`, which is also the SHA-256 of the tree file's
  bytes. `sha256-tree:` carries exactly 64 hex digits.
- A source's id is `source:` followed by the digest of `{scheme, value}` under
  `science.source-address.v1`, where the scheme is its first accepted external
  identifier in the order `doi`, `pmid`, `isbn`, `accession`. There is no fallback
  to a title or year.
- An exposure event's id is `exposure-event:` and the digest of its facet under
  `science.exposure-event.v1`, and a reservation assignment's is
  `reservation-assignment:` and the digest of its facet under
  `science.reservation-assignment.v1`.
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

A run starts only from held inputs, which it copies into the `inputs/` directory of
the workflow's working directory. A file resource is staged at `inputs/<name>`. A
tree resource is staged as a directory, `inputs/<name>/<member path>`, that holds
exactly the tree's members: the tree file must hash to the tree's digest and parse,
and each member is copied from its store object, never linked, and its copy re-hashed
against the member's digest. A source that is a symbolic link or not a regular file
is refused. A tree's staged digest is its `sha256-tree:` digest, and an expected value
for that resource must equal it, so a one-tree dataset's content identity in the
recipe is that digest. Every staging destination is checked before the first copy,
whatever the input order: a file's name and a tree's root each reserve that path and
everything beneath it, so no other resource may be staged at it or under it. Any of
these refusals comes before anything executes. The staged tree is removed when the
run ends, after a production run's outputs are exported, and also when the run is
refused or fails closed; a removal that fails is ignored, as the planning
directory's is, so it never replaces the run's outcome.

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
refuses as `lineage-incomplete`. An observed dataset that carries the facet
together with a basis or a producing run is refused as before
(`facet-bearer-produced`); the walk passes through an intermediate ancestor in
that state, which `corpus_check` reports separately. Route retractions are
folded only when a route in the chain records an identity, which boundary-minted
routes never do; a malformed or cyclic retraction then refuses standing.
`corpus_check` reports an unmet rule as `eligibility-unmet`, and one resting on a
run, producer or ancestor the corpus does not hold as `eligibility-unresolved`.

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
`<algorithm>:<lowercase hex>`. The accepted algorithms are `sha256` and `sha256-tree`. A dataset
with any unpinned resource has no content identity and is refused. A dataset is
*held* only when an observation matches every declared digest, and heldness is
derived at read time, never stored. A `sha256-tree` resource is held by an
observation of that digest, which a store-tree location supplies.

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
one of three types:

- `{type: store, store_id, relative_path}`, a file in a store;
- `{type: store-tree, store_id, tree}`, a tree dataset held in a store, where
  `tree` is the 64 lowercase hex characters of a `sha256-tree` digest (canonical
  form `store-tree:<store_id>:<tree>`);
- `{type: url, url}`.

Its `outcome` is either `{finding: found, digest}` or `{finding: absent}`. At a
store-tree location a found digest is exactly `sha256-tree:<tree>`, and so is
`expected` when set. An absent observation at a store-tree location carries
`incomplete`, `{missing, mismatched}`, two non-negative integers whose sum is at
least 1: the count of members not in the store and the count whose stored bytes
do not match. At any other location `incomplete` is refused. A url location never
records absent. The observation also has the fields `observer`, `instrument`,
`event_token`, `observed_at` and `supersedes` (a list of observations), and an
optional `expected`. Holdings acts alone mint observations.

A tree dataset is held as a tree file plus its member objects. The store keeps each
object at `objects/sha256/<hh>/<hex>`, where `<hex>` is the object's digest and `<hh>`
its first two characters. The `objects/` directory is closed to ordinary acts: a
store locator refuses `objects` and every path under it. The store's ordinary write, delete and move primitives refuse
those paths again, and objects are created only by a create-only primitive that
refuses any path outside `objects/sha256/`; an existing object is a routine refusal.

The `tree-write` act writes a tree into a store. It announces a `tree-write` intent, then
for each member in tree order (and last for the tree file) reads the object's path.
An absent object is created from the member's source bytes, which must match the member's
digest and size; a present object is reused only when its digest and size are exactly the
tree's. Any other bytes, size or kind refuse the act, as does a read the engine does not
observe (the object could not be read), and so does a routine refusal of the
create whose object, read again, does not match exactly: a refusal alone never proves the
object exists. The act holds one member's bytes at a time, leaves only whole objects when
interrupted (with its intent unmatched), and on success publishes one `found` observation
of the tree's digest.

The re-check of a store-tree location is a `re-check` act that reads the tree file and
then each member object. An unreadable read is an inconclusive attempt that mints nothing.
A missing tree file, or one with other bytes or that does not parse, is an `absent`
observation counting one missing or one mismatched object; otherwise each missing member
counts as missing, and each member with other bytes, another size or a non-regular kind
counts as mismatched. The tree is `found` only when none is missing or mismatched.

### Acquisition logs

A sealed acquisition set carries one acquisition log, `science.acquisition-log.v1`: UTF-8 JSON
Lines, each line canonical `science.identity.v1` text and the file ending in a line feed. That
encoding refuses `null`, so an optional field is absent, never null. The parser
(`holdings/acquisition_log.py`) refuses a log with a `MalformedRecord`: one that does not end
with a line feed (an empty input included) names no line, and every other refusal names its line.

The first line is the header, with exactly these keys: `format`, `set` (the set's 32-hex token),
`origin` (`fetched` or `imported`) and `fetched_by`, then `plan` (the acquisition plan as given)
when the origin is `fetched`, or `source_journals` (a non-empty list of `{name, digest}`, the
original journals by name and `sha256:` digest) when it is `imported`, and neither otherwise.

Each later line is one request, in `seq` order from 1 with no gap:

- `seq`, `request` (exactly `{method: GET, url}`), `attempts` (always a list) and `result`;
- optional `parent`, the `seq` of an earlier `fetched` line, and `expected`, a `sha256:` digest;
- `digest`, `size` and `member` (the tree path), present if and only if `result` is `fetched`.

An attempt is `{started_at, completed_at, outcome, status?, headers?, failure?}`. `outcome` is
`fetched`, `failed` or `not-attempted`. `failure` is present exactly when the outcome is not
`fetched`: a refusal category for `not-attempted`, and a transport failure category or
`expected-mismatch` for `failed`. `headers` allows only `content-type`, `content-length`,
`last-modified` and `etag`. `result` is `fetched`, `failed` (its retry budget is spent) or
`abandoned` (never fetched, given up at a partial seal).

In a fetched-origin log every line has at least one attempt, each with `started_at` and
`completed_at`; a `fetched` line's last attempt is `fetched`, and a `failed` or `abandoned` line
has no `fetched` attempt. An imported log's lines carry only what the source journal recorded, so
an attempt may lack either time and `attempts` may be empty; each imported line also has
`recorded`, `{journal, line, digest?}`, naming the 0-based index into `source_journals`, the
journal's line number and, when the journal recorded one, its own digest of the bytes, which must
equal the line's `digest`. `recorded` is absent from a fetched-origin line.

`log_tree` is the tree of the `fetched` lines' members, and `log_summary` counts the requests by
result and reports the log's `sha256:` digest and the tree's `sha256-tree:` digest. Its
`traversal_complete` is false when the plan has a `traversal` and any line is `failed` or
`abandoned`, and true otherwise. The act report records that summary as an `acquisition-set` entry
whose subject is the set's store-tree location and whose `set-summary` outcome has the fields
`origin`, `fetched_by`, `requests`, `fetched`, `failed`, `abandoned` (non-negative integers with
`requests` their sum), `traversal_complete` (a boolean), `log` and `tree`. It is the one act-report
outcome with integer and boolean fields; the stored validator checks each field's type.

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
act's subject and outcome; the `acquisition-set` entry's outcome is described under
[Acquisition logs](#acquisition-logs). An act report never feeds a belief.

## Exposure events and reservation assignments

Two world kinds record what has been seen of a question and how its data is held
back. Both are content-addressed, append-only and governed (`science.exposure-event.v1`
and `science.reservation-assignment.v1`). `beliefs.reservation` holds their value
types, unit grammar and shared refusal functions; `stored.exposure_event_value` and
`stored.reservation_assignment_value` read a stored record whole. Neither kind
feeds a belief.

### Units

A unit is one of two shapes, and a list of units holds one shape only:

- a term unit, `{sort, term}`: `sort` is `<namespace>/<name>`, each half starting
  with a lowercase letter (`[a-z][a-z0-9-]*`), and `term` a non-empty string. The
  sort must be declared in the compiled profile;
- an interval unit, `{start, end}`: each end is a whole-second UTC timestamp
  (`YYYY-MM-DDTHH:MM:SSZ`) or the word `open`. The two ends cannot both be `open`, and a
  closed interval starts strictly before it ends.

Units sort by shape, then by sort and term, or by start and end with an open start
first and an open end last. A list of units is sorted and has no repeats.

### Exposure events

An `exposure-event` facet records one look at, or one piece of knowledge about,
some data. Its fields are:

- `channel`: `read` or `knowledge`. `subjects` is non-empty exactly when the channel
  is `read`; each subject is a `dataset:` or `source:` reference, sorted and
  distinct;
- `units`: the units exposed (a list that may be empty);
- `effect`: `exposing` or `non-exposing`;
- `class`: a non-empty string naming the kind of exposure;
- `bound` (optional): a mapping from a non-empty name to a `sha256:` or `sha256-tree:` digest;
- `account`: a non-empty string telling what happened;
- `observer` and `recorded_by`: actors, in the form the permit accepts;
- `observed_at`: a whole-second UTC timestamp;
- `propositions`: `proposition:` references, sorted and distinct;
- `evidence` (optional): sorted, distinct `<scheme>:<rest>` tokens. A token whose
  scheme names a world kind other than `act-report`, `run` or `holdings-observation`
  is refused.

The record's id is `exposure-event:` followed by the digest of its facet under
`science.exposure-event.v1`, so the same look recorded twice is one record. Its
edges mirror the facet: an `exposes` edge for each subject, a `concerns` edge for
each proposition, and an `attested-by` edge for each evidence token whose scheme is
`act-report`, `run` or `holdings-observation`. External evidence tokens (non-world
schemes) stay in the facet alone.

### Reservation assignments

A `reservation-assignment` facet partitions units into groups under a named rule,
as one link of a chain. Its fields are:

- `chain`: a name matching `[a-z][a-z0-9-]*`;
- `rule`: `{name, version}`, both non-empty strings;
- `inputs`: a non-empty mapping from name to a `sha256:` or `sha256-tree:` digest;
- `events`: `exposure-event:` references, sorted and distinct, one `considers` edge
  each;
- `scope` (optional): a `proposition:` reference, with a `concerns` edge. An
  assignment without `scope` is program-level;
- `applies` (optional): a `reservation-assignment:` reference, with an `applies`
  edge. Admitted only when `scope` is present; an unscoped assignment carrying
  `applies` is refused;
- `groups`: at least one group, each `{units, role, label?, basis?}`. `units` is a
  non-empty unit list. `role` is `open`, `reserved`, `unresolved` or `withheld`.
  `label` is a non-empty string and `basis` a `sha256:` digest (never
  `sha256-tree:`);
- `predecessor` (optional): a `reservation-assignment:` reference;
- `evidence` (optional): sorted, distinct `<scheme>:<rest>` tokens. Those with the
  scheme `exposure-event` also get an `evidenced-by` edge; a token whose scheme
  names any other world kind is refused;
- `flagged` (optional): sorted, distinct `assessment:` references, one `flags` edge
  each. Absent means no suspension was reported, and an empty list means a
  suspension was reported and no assessment was made;
- `account` (optional): a non-empty string;
- `participants` (optional): sorted, distinct actors;
- `prior_runs` (optional): sorted, distinct `<scheme>:<rest>` tokens. Those with
  the scheme `run` also get a `reports` edge; a token whose scheme names any other
  world kind is refused;
- `assigned_at`: a whole-second UTC timestamp, and `assigned_by`: an actor.

Groups are sorted by their first unit. Across all groups the units have one shape,
no unit sits in two groups, and interval units do not overlap (they may touch). A
record whose intervals overlap, whose `applies` is set without `scope`, or whose
`evidence` or `prior_runs` names a world kind the slot does not admit is refused by
the reader, so it reads as `facet-payload-malformed` and has no separate audit code. The id is
`reservation-assignment:` followed by the digest of the facet under
`science.reservation-assignment.v1`. A successor also carries one `supersedes` edge
to its `predecessor`; a chain root carries none.

### Chains and derived changes

A chain is the records sharing `chain` and `scope`; it is linear, with one root and
one head. `beliefs.reservation.assignment_head(view, chain, *, scope=None)` returns
the head, or None when the chain has no record, and raises `ChainAmbiguous` for two
roots or two heads rather than choose one (or `MalformedRecord` when a stored
assignment in the view is malformed).

A successor's group changes are derived at read time, never stored.
`assignment_changes_of(view, ref)` returns them (empty for a root). Groups are
matched by their first unit:

- a predecessor group whose first unit sits in no successor group is `absent`;
- a predecessor group whose first unit sits in a successor group that is not equal
  to it (any field of the group) is `changed`;
- a successor group whose first unit sits in no predecessor group is `added`.

A change is suspended when it is `absent` or `changed` and the predecessor group's
role was `reserved`. An `added` group is never suspended.

### Write rules

`add` mints a chain root or an exposure event; for a reservation assignment, a record
naming a predecessor, or carrying a `supersedes` edge, is refused there
(`FamilyKindUnsupported`).
`supersede` mints a successor: its facet's `predecessor` must name the record
superseded, and the adapter authors the `supersedes` edge, so the caller supplies
none. `revise` changes prose only (title, body, `display`) and refuses anything else
(`ReviseOutsideAllowlist`). `delete` refuses both kinds (`DeletionKindExcluded`),
and neither kind can be a coreference endpoint. `move` and `consolidate` carry them: `move` keeps
their edges in facet order, and `consolidate` writes the merged record's edges
sorted, which the set comparison below accepts.

The write boundary decodes the facet (a facet its reader refuses is
`MalformedRecord`) and then refuses with `ReservationRefused`, whose `code` is one
of the following, in this order. Edges are compared with the facet's as a
duplicate-free set, so order is free and a missing, extra or doubled edge is not.

- An event: `exposure-edge-mismatch`; `exposure-ref-unresolved` (a subject,
  proposition or kernel evidence reference that resolves to no record, or to a
  record of the wrong kind); `exposure-unit-sort-undeclared`.
- An assignment's own record: `assignment-edge-mismatch` (including a successor
  without exactly one `supersedes` edge to its predecessor, and a root with one);
  `assignment-ref-unresolved` (an event, an `exposure-event:` entry of `evidence`,
  a `flagged` assessment, a `run:` entry of `prior_runs`, or `scope`, `applies` or
  `predecessor`, that resolves to no record or the wrong kind); `assignment-applies-scoped` (`applies` names a scoped assignment);
  `assignment-unit-sort-undeclared`.
- Its chain, judged over the write root (or an import's union), never a read mount:
  `assignment-root-exists` (a second root for the same `chain` and `scope`) and
  `assignment-superseded` (the predecessor already has a successor).
- Its succession, against the predecessor: `assignment-scope-mismatch` (a different
  chain, scope or unit shape); `assignment-unchanged` (the facet with `predecessor`,
  `assigned_at` and `assigned_by` removed equals the predecessor's); `assignment-changes-without-evidence` (any derived change, an
  addition included, and no `evidence`); `assignment-suspension-unflagged` (a
  suspended group and no `flagged` list); `assignment-flagged-without-suspension`
  (`flagged` present and no suspension, a root's included).

Last, `recorded_by` (an event) or `assigned_by` (an assignment) must equal the bound
actor (`ActorMismatch` otherwise); import, `move` and `consolidate` keep the actor as
written.

### Audit

`audit_corpus` and `audit_world` recompute the same checks over stored records and
report them as findings, with these codes (all in `WORLD_AUDIT_CODES`):
`exposure-edge-mismatch`, `exposure-ref-unresolved`, `exposure-unit-sort-undeclared`,
`assignment-edge-mismatch`, `assignment-ref-unresolved`, `assignment-applies-scoped`,
`assignment-unit-sort-undeclared`, `assignment-fork`, `assignment-scope-mismatch`,
`assignment-changes-without-evidence`, `assignment-suspension-unflagged`,
`assignment-flagged-without-suspension` and `assignment-unchanged`.

`assignment-fork` reports the two chain conditions above (two successors of one
predecessor, or two roots of one chain and scope); `add`, `supersede` and `import`
refuse both, so only a raw write (one made around the boundary) can produce it, and
the finding names the later record by id. A record whose reader refuses it is
`facet-payload-malformed`. A reference recorded in a corpus not held here, or one
that is itself unreadable, is a neighbour's fault: the check is reported unchecked
rather than failed, and the succession checks need a readable predecessor. The
bound-actor rule is a write-time check and is not repeated.

### Reading them

Three module functions in `beliefs.reservation` read the kinds through any view with
`iter_stored` and `get` (they are not `ReadView` methods):

- `exposure_events(view, *, subject=None, proposition=None)` returns every stored
  event matching each of `subject` and `proposition` that is given, ordered by
  `observed_at` then id. A malformed event raises `MalformedRecord` instead of
  being skipped, since skipping would understate exposure;
- `assignment_head(view, chain, *, scope=None)`, above;
- `assignment_changes_of(view, ref)`, above.

### Publication

Publication closure follows each kind's world edges. A reservation assignment's
`supersedes` edge counts too, so a published successor carries its predecessor
chain, and a selection that lacks the chain is refused (`closure-incomplete`); the
`supersedes` edges of other kinds stay outside closure. See
[writes.md](writes.md#publication).

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
- An exposure event or reservation assignment whose fields break a value rule (such
  as overlapping intervals, `applies` without `scope`, or a disallowed world-kind
  scheme in `evidence` or `prior_runs`), whose stored facet is not the canonical
  form of the value it decodes to (for example an empty `evidence` or `bound`
  written out), or whose id does not recompute from the facet (`MalformedRecord`).
