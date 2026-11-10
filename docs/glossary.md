# Glossary

Type: glossary guide; document types 1. One- or two-line definitions of the terms
the beliefs documents use, each linking the document that specifies or explains it:
[guide.md](guide.md), [records.md](records.md), [contracts.md](contracts.md),
[writes.md](writes.md) and [development.md](development.md).

- <a id="acquisition-set"></a>**Acquisition set** — The files a program fetched or
  imported into a work area, with the acquisition log recording every request
  behind them; a [seal](#seal) holds them as one tree dataset.
  ([records](records.md#acquisition-logs))
- <a id="act-family"></a>**Act family** — One of the seven closed classes of write a
  permit names: `corpus-write`, `run`, `holdings`, `registry`, `epoch`, `lifecycle`
  and `publish`. ([writes](writes.md#authority-and-permits))
- <a id="act-report"></a>**Act report** — The inert record most operations close with:
  their member acts and outcomes. It never feeds a belief.
  ([records](records.md#other-world-records))
- <a id="actor"></a>**Actor** — Who is writing, bound with the permit when a writer is
  constructed and never supplied on a call. ([writes](writes.md#participants))
- <a id="analysis-spec"></a>**Analysis spec** — The frozen plan of an analysis: target
  proposition, estimand, method, input roles, rules and parameters, fixed before
  anything runs. ([records](records.md#specs-runs-and-assessments))
- <a id="aptness"></a>**Aptness** — A measured binding's admission, yield, scale,
  bearer and validity checks against a compiled profile and held records.
  ([records](records.md#binding-aptness))
- <a id="assessment"></a>**Assessment** — The outcome (`supported`, `refuted` or
  `inconclusive`) of one run of a spec against one proposition, with the typed
  estimand and estimate. ([records](records.md#specs-runs-and-assessments))
- <a id="aspect"></a>**Aspect** — A sort and term distinguishing which aspect of
  an observable is measured; the pack must admit its sort for the quantity kind.
  ([contracts](contracts.md#domain-contracts))
- <a id="assumptions-register"></a>**Assumptions register** — A content-addressed
  record of what a domain contract's declarations collapse, license and leave
  unestablished, entries keyed by typed declaration address (`sort:<ns>/<name>`, …).
  A spec cites the registers it relies on, and each must be current at the write door.
  ([records](records.md#assumptions-registers))
- <a id="authority"></a>**Authority** — A write permit bound to an actor.
  ([writes](writes.md#authority-and-permits))
- <a id="base-contract"></a>**Base contract** — The Science contract that declares the
  record kinds, relations, kernel facets and closed grammars.
  ([contracts](contracts.md#base-contract))
- <a id="bearer-sort"></a>**Bearer sort** — The declared sort of the thing an
  observable is a property of, independent of its role in a claim.
  ([contracts](contracts.md#domain-contracts))
- <a id="belief"></a>**Belief** — The answer `evaluate` computes for a proposition
  under an exact policy binding, never stored. ([records](records.md#beliefs))
- <a id="binding"></a>**Binding** — What a sort's terms are checked against: exactly one
  of six arms, `release`, `dataset`, `scheme`, `selection`, `run-output` or
  `world-kind`. It is in the contract's identity and never in a claim's.
  ([contracts](contracts.md#domain-contracts))
- <a id="bridge"></a>**Bridge** — An operator of its own that maps a literature verb to
  a template (`narrower` or `contextual`), with the template's roles and its own
  sorts per role. The kernel never follows the mapping.
  ([contracts](contracts.md#domain-contracts))
- <a id="capture-hold"></a>**Capture hold** — A corpus root's operation lock taken for
  one coherent read. It never waits: a capture while a writer holds the lock is
  refused (`BuildContended`), and so is a writer that arrives during a capture
  (`BuildHold`). Epoch builds, live queries and a session's read mounts read
  under it. ([writes](writes.md#citations-across-mounts))
- <a id="certified-host"></a>**Certified host** — A host whose kernel and volume form a
  configuration `atoms` certifies. Writes anywhere else fail with
  `CapabilityUnavailable`. ([development](development.md#the-certified-host))
- <a id="chain"></a>**Chain** — See [the root's log](#roots-log); for the sequence of
  reservation assignments, see [reservation chain](#reservation-chain).
- <a id="claim"></a>**Claim** — The typed content of a proposition: an operator,
  referents in its named [roles](#role), claim-side qualifiers, a [form](#form), a
  polarity and a layer. ([records](records.md#propositions-and-claims))
- <a id="claim-identity"></a>**Claim identity** — `I_claim`, the digest of the claim's
  canonical projection `π_claim`. Wording and contract releases never enter it.
  ([records](records.md#identity))
- <a id="classification-rule"></a>**Classification rule** — A content-addressed
  definition of how input observables produce classes of a declared sort.
  ([records](records.md#classification-rule))
- <a id="clean-environment"></a>**Clean environment** — The verification scope at which
  a passed verification admits an assessment. It is derived from the runs'
  receipts, never chosen. ([records](records.md#verifications))
- <a id="co-scope"></a>**Co-scope** — How one typed restriction map relates to
  another: equal, narrower, broader, overlapping, disjoint or unknown, computed per
  dimension and folded conservatively. ([contracts](contracts.md#typed-restrictions))
- <a id="composite"></a>**Composite** — A record of a structure over claims: a node set
  and member propositions read as directed edges, with no cycle. It never enters a
  belief. ([records](records.md#other-world-records))
- <a id="content-address"></a>**Content address** — An id derived from a record's
  content, as for datasets, sources, specs, act reports and retractions.
  ([records](records.md#identity))
- <a id="coordination-contract"></a>**Coordination contract** — The contract that
  declares view and coordination kinds (`project`, `task`, `publication` and
  others). ([contracts](contracts.md#coordination-contract))
- <a id="coreference-attestation"></a>**Coreference attestation** — An attributed
  record that two differently identified records name one thing, or do not; it
  never merges them. ([records](records.md#other-world-records))
- <a id="corpus"></a>**Corpus** — A directory of records under a `corpus.yaml` manifest
  that pins its contracts. ([records](records.md#corpus))
- <a id="dataset"></a>**Dataset** — A record that declares resources by digest. Its id
  is its content address. ([records](records.md#datasets-sources-and-holdings))
- <a id="dataset-production-run"></a>**Dataset-production run** — A run that makes a
  dataset. It records lineage and never yields an assessment.
  ([guide](guide.md#runs-and-reproducibility))
- <a id="declared"></a>**Declared** — A dataset that names its bytes by digest without
  an observation that holds them. It is a real record but never counts as
  evidence. ([records](records.md#datasets-sources-and-holdings))
- <a id="domain-contract"></a>**Domain contract** — A namespaced contract that adds
  sorts, dimensions, templates, instantiations, bridges, estimand declarations,
  duration conventions and facets.
  ([contracts](contracts.md#domain-contracts))
- <a id="duration-convention"></a>**Duration convention** — A named exact
  conversion from a calendar unit to a noncalendar unit of the same duration
  quantity kind. Calendar restrictions name it explicitly.
  ([contracts](contracts.md#typed-restrictions))
- <a id="epoch"></a>**Epoch** — An immutable, published index of a world over an
  explicit set of corpus states. A read bound to an epoch names it.
  ([guide](guide.md#worlds-identity-and-change))
- <a id="equivalence-rule"></a>**Equivalence rule** — The rule, frozen in the spec,
  that says when two runs gave the same result. ([guide](guide.md#runs-and-reproducibility))
- <a id="estimand"></a>**Estimand** — The typed quantity an analysis estimates, built
  against the claim it answers. ([records](records.md#specs-runs-and-assessments))
- <a id="exposure-event"></a>**Exposure event** — A record that some data, or knowledge
  of it, was seen on a channel (`read` or `knowledge`) over some units, with its effect
  and an account. It is content-addressed and append-only.
  ([records](records.md#exposure-events))
- <a id="facet"></a>**Facet** — A named block of fields on a record, declared by a
  contract. ([contracts](contracts.md#facet-fields))
- <a id="form"></a>**Form** — A claim's form, from those its template declares:
  `polar`, an effect with a polarity, or `"null"`, an absent effect, whose polarity is
  always `inapt`. ([records](records.md#propositions-and-claims))
- <a id="frozen-dependency"></a>**Frozen dependency** — A normative record id and
  its referenced contract terms, captured transitively by the dependency walk.
  ([records](records.md#binding-aptness))
- <a id="governed-kind"></a>**Governed kind** — A world kind with an identity domain;
  each of its records carries a `semantic-identity` stamp. ([records](records.md#identity))
- <a id="held"></a>**Held** — A dataset is held when holdings observations match every
  digest it declares; heldness is derived when read, never stored. A record is held
  by a corpus when that corpus contains it.
  ([records](records.md#datasets-sources-and-holdings))
- <a id="holdings-observation"></a>**Holdings observation** — A record of what one
  look at one location found: a digest, or absence.
  ([records](records.md#datasets-sources-and-holdings))
- <a id="identifier-class"></a>**Identifier class** — A sort's literal prefix and
  portable pattern; a term must match the whole pattern after NFC normalization.
  ([contracts](contracts.md#domain-contracts))
- <a id="instantiation"></a>**Instantiation** — A declaration of which sorts may fill
  each role of a template in one contract. Several may admit one claim; its name
  never enters claim identity. ([contracts](contracts.md#domain-contracts))
- <a id="interpretation-rule"></a>**Interpretation rule** — The rule, frozen in the
  spec, that turns a run's outputs into an outcome and estimate.
  ([guide](guide.md#runs-and-reproducibility))
- <a id="layer"></a>**Layer** — Which kind of claim a proposition makes, such as causal
  or statistical; the operator lists the layers it admits.
  ([records](records.md#propositions-and-claims))
- <a id="ledger"></a>**Ledger** — A writer session's append-only file, each line fsynced
  before the call that wrote it returns. ([writes](writes.md#writer-sessions))
- <a id="live-query"></a>**Live query** — `evaluate_live_query`: a view query over every
  live admitted corpus as it is now, stamped with the states it captured.
  ([guide](guide.md#worlds-identity-and-change))
- <a id="measure"></a>**Measure** — An observable with a unit or procedure-defined
  scale, resulting level of measurement, value type, transformation and producing
  procedure; represented by `measurement.Measure` alongside the interim estimand value.
  ([contracts](contracts.md#domain-contracts))
- <a id="nobelief"></a>**NoBelief** — The answer that no belief can be given, with its
  reason, such as `no-eligible-assessment`. ([records](records.md#beliefs))
- <a id="observable"></a>**Observable** — A quantity kind, bearer sort and optional
  aspect; two observables are equal only when all three parts match.
  ([contracts](contracts.md#domain-contracts))
- <a id="observes"></a>**Observes** — The run-input role for held data, the only role
  that can make an assessment count; `reads` never can.
  ([records](records.md#specs-runs-and-assessments))
- <a id="operation"></a>**Operation** — An act made of several member acts. It opens
  with an intent in the root's log and closes with one terminal record.
  ([writes](writes.md#operations))
- <a id="operator"></a>**Operator** — What a claim asserts: a [template](#template)
  or a [bridge](#bridge), named `<namespace>/<name>`. It fixes the claim's roles,
  sign aptness, forms and layers; its instantiations (or, for a bridge, its own
  role sorts) fix which sorts may fill each role.
  ([records](records.md#propositions-and-claims))
- <a id="polarity"></a>**Polarity** — The direction a claim asserts: `positive`,
  `negative` or `unsigned`, or the tag `inapt` for an operator with no sign and for a
  `"null"`-form claim.
  ([records](records.md#propositions-and-claims))
- <a id="policy-binding"></a>**Policy binding** — The exact pair of a belief policy's
  rule identity and implementation identity. ([records](records.md#beliefs))
- <a id="procedure"></a>**Procedure** — A content-addressed measurement definition
  with complete yield observables, validation scope and optional scale or pinned
  implementation. Its kind determines whether model inputs are required.
  ([records](records.md#procedure))
- <a id="profile"></a>**Profile** — The compiled combination of a base contract, domain
  contracts and optionally a coordination contract, against which every write is
  checked. ([contracts](contracts.md#profiles))
- <a id="proposition"></a>**Proposition** — The record that carries a claim.
  ([records](records.md#propositions-and-claims))
- <a id="proxy-model"></a>**Proxy model** — A content-addressed link from a source
  observable and held procedure to a target observable or authority scale, with
  validity scope and a calibration or assumption basis.
  ([records](records.md#proxy-model))
- <a id="publication"></a>**Publication** — A new corpus holding the records a view
  selected, with one `publication` marker; the source corpus keeps a
  `publication-binding`. ([writes](writes.md#publication))
- <a id="qualifier"></a>**Qualifier** — A restriction of a claim to one of its
  operator's dimensions, with a quantifier. ([records](records.md#propositions-and-claims))
- <a id="read-mount"></a>**Read mount** — A corpus a writer session reads but does not
  write; records may cite records in it. ([writes](writes.md#citations-across-mounts))
- <a id="referent-mapping"></a>**Referent mapping** — A content-addressed
  correspondence between two declared bearer sorts, with cardinality and an
  optional aggregation rule. ([records](records.md#referent-mapping))
- <a id="registration"></a>**Registration** — Two senses. A root is registered with
  the engine once (`init_corpus_root`), and writes to an unregistered root are
  refused. Each transaction is registered as an entry in the root's log before it
  is applied; that entry names what it writes and, when it fulfils an operation
  intent, carries the intent's token. ([writes](writes.md#operations))
- <a id="reservation-assignment"></a>**Reservation assignment** — A record that
  partitions units into groups, each with a role, under a named rule; one link of a
  chain. It is content-addressed and append-only, and a successor supersedes its
  predecessor. ([records](records.md#reservation-assignments))
- <a id="reservation-chain"></a>**Reservation chain** — The linear sequence of
  reservation assignments sharing a `chain` name and a `scope`, from one root to one
  head. ([records](records.md#chains-and-derived-changes))
- <a id="restriction"></a>**Restriction** — A typed term, numeric interval, time
  interval, rule class set or union limiting an applicability-side dimension.
  ([contracts](contracts.md#typed-restrictions))
- <a id="retraction"></a>**Retraction** — A record that withdraws the standing of a
  record, a dataset route or a producer snapshot without changing it.
  ([records](records.md#other-world-records))
- <a id="role"></a>**Role** — Two senses. In a claim, a named position its template
  declares, `one` (a referent) or `many` (members with coefficients, in canonical
  order), plus the reserved `within-model`, which any claim may carry
  ([records](records.md#propositions-and-claims)). In a reservation assignment, a
  group's standing: `open`, `reserved`, `unresolved` or `withheld`
  ([records](records.md#reservation-assignments)).
- <a id="roots-log"></a>**The root's log** — The append-only, hash-linked chain the
  `atoms` engine keeps for each registered root: intents, transaction registrations
  and their settlements. Operation completion and log audit are read from it.
  ([writes](writes.md#operations))
- <a id="run"></a>**Run** — The record of one complete execution: recipe, outputs and
  the facts of the occurrence. ([records](records.md#specs-runs-and-assessments))
- <a id="scale-authority"></a>**Scale authority** — A held procedure declaring its
  own scale range and orientation. Another procedure can name it with `same_as`.
  ([records](records.md#procedure))
- <a id="scoped-writer"></a>**Scoped writer** — The writer a session hands one
  invocation, with exactly the permit that invocation needs.
  ([writes](writes.md#writer-sessions))
- <a id="seal"></a>**Seal** — The `acquisition` operation that verifies an
  [acquisition set](#acquisition-set)'s log and files, writes the log and the
  [tree](#tree) into the store, and closes with the dataset and one act report.
  ([writes](writes.md#sealing-an-acquisition))
- <a id="sort"></a>**Sort** — The type of referent a role or qualifier dimension
  admits. It has a binding, an identifier class (unless bound to a world kind) and
  role categories. ([contracts](contracts.md#domain-contracts))
- <a id="source"></a>**Source** — A record of a published work, addressed by its first
  accepted external identifier. ([records](records.md#datasets-sources-and-holdings))
- <a id="source-assertion"></a>**Source assertion** — A record of what a source (a
  paper or other work) asserts. It has no route to belief.
  ([records](records.md#record-kinds))
- <a id="standing"></a>**Standing** — Whether a record is active, computed from the
  retractions that target it. ([guide](guide.md#worlds-identity-and-change))
- <a id="store-object"></a>**Store object** — A file a store keeps under its own
  digest at `objects/sha256/<hh>/<hex>`, created only by a create-only write; a
  tree's members and its tree file are store objects.
  ([records](records.md#datasets-sources-and-holdings))
- <a id="supersession"></a>**Supersession** — A `supersedes` link from a new record to
  the same-kind record it replaces. ([records](records.md#relations))
- <a id="target-observable"></a>**Target observable** — The measure's observable
  without a proxy, or the cited proxy's explicit target observable.
  ([records](records.md#binding-aptness))
- <a id="template"></a>**Template** — A relation template: named roles (`one` or `many`),
  sign aptness, layers, forms and an optional cause/effect edge. Its
  `<namespace>/<name>` is the operator a claim names.
  ([contracts](contracts.md#domain-contracts))
- <a id="unit"></a>**Unit** — One element a group or an exposure covers: a term
  (`{sort, term}`) or an interval (`{start, end}`); a list holds one shape.
  ([records](records.md#units))
- <a id="verification"></a>**Verification** — The record of a comparison between two
  runs, with a derived scope and a verdict. ([records](records.md#verifications))
- <a id="view"></a>**View** — A stored query over the world plus a label, such as a
  `project` or `question`; it selects records and owns none.
  ([contracts](contracts.md#coordination-contract))
- <a id="tree"></a>**Tree** — A dataset resource that is a directory: a sorted list of
  file members (path, `sha256:` digest, size), identified by its `sha256-tree:` digest.
  ([records](records.md#identity))
- <a id="world"></a>**World** — Every corpus a world registry admits.
  ([guide](guide.md#worlds-identity-and-change))
- <a id="write-permit"></a>**Write permit** — The record kinds and act families a writer
  may write. ([writes](writes.md#authority-and-permits))
- <a id="writer-session"></a>**Writer session** — An attended session that writes one
  corpus root and records every step in its ledger.
  ([writes](writes.md#writer-sessions))
