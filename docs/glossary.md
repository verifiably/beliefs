# Glossary

Type: glossary guide; document types 1. One- or two-line definitions of the terms
the beliefs documents use, each linking the document that specifies or explains it:
[guide.md](guide.md), [records.md](records.md), [contracts.md](contracts.md),
[writes.md](writes.md) and [development.md](development.md).

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
- <a id="assessment"></a>**Assessment** — The outcome (`supported`, `refuted` or
  `inconclusive`) of one run of a spec against one proposition, with the typed
  estimand and estimate. ([records](records.md#specs-runs-and-assessments))
- <a id="authority"></a>**Authority** — A write permit bound to an actor.
  ([writes](writes.md#authority-and-permits))
- <a id="base-contract"></a>**Base contract** — The Science contract that declares the
  record kinds, relations, kernel facets and closed grammars.
  ([contracts](contracts.md#base-contract))
- <a id="belief"></a>**Belief** — The answer `evaluate` computes for a proposition
  under an exact policy binding, never stored. ([records](records.md#beliefs))
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
- <a id="claim"></a>**Claim** — The typed content of a proposition: operator,
  arguments, qualifiers, polarity and layer. ([records](records.md#propositions-and-claims))
- <a id="claim-identity"></a>**Claim identity** — `I_claim`, the digest of the claim's
  canonical projection `π_claim`. Wording and contract releases never enter it.
  ([records](records.md#identity))
- <a id="clean-environment"></a>**Clean environment** — The verification scope at which
  a passed verification admits an assessment. It is derived from the runs'
  receipts, never chosen. ([records](records.md#verifications))
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
  sorts, dimensions, operators, estimands, edges and facets.
  ([contracts](contracts.md#domain-contracts))
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
- <a id="governed-kind"></a>**Governed kind** — A world kind with an identity domain;
  each of its records carries a `semantic-identity` stamp. ([records](records.md#identity))
- <a id="held"></a>**Held** — A dataset is held when holdings observations match every
  digest it declares; heldness is derived when read, never stored. A record is held
  by a corpus when that corpus contains it.
  ([records](records.md#datasets-sources-and-holdings))
- <a id="holdings-observation"></a>**Holdings observation** — A record of what one
  look at one location found: a digest, or absence.
  ([records](records.md#datasets-sources-and-holdings))
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
- <a id="nobelief"></a>**NoBelief** — The answer that no belief can be given, with its
  reason, such as `no-eligible-assessment`. ([records](records.md#beliefs))
- <a id="observes"></a>**Observes** — The run-input role for held data, the only role
  that can make an assessment count; `reads` never can.
  ([records](records.md#specs-runs-and-assessments))
- <a id="operation"></a>**Operation** — An act made of several member acts. It opens
  with an intent in the root's log and closes with one terminal record.
  ([writes](writes.md#operations))
- <a id="operator"></a>**Operator** — A domain contract's claim predicate. It fixes the
  arity, the argument sorts, the qualifier dimensions, the sign and the layers.
  ([contracts](contracts.md#domain-contracts))
- <a id="polarity"></a>**Polarity** — The direction a claim asserts: `positive`,
  `negative` or `unsigned`, or the tag `inapt` for an operator with no sign.
  ([records](records.md#propositions-and-claims))
- <a id="policy-binding"></a>**Policy binding** — The exact pair of a belief policy's
  rule identity and implementation identity. ([records](records.md#beliefs))
- <a id="profile"></a>**Profile** — The compiled combination of a base contract, domain
  contracts and optionally a coordination contract, against which every write is
  checked. ([contracts](contracts.md#profiles))
- <a id="proposition"></a>**Proposition** — The record that carries a claim.
  ([records](records.md#propositions-and-claims))
- <a id="publication"></a>**Publication** — A new corpus holding the records a view
  selected, with one `publication` marker; the source corpus keeps a
  `publication-binding`. ([writes](writes.md#publication))
- <a id="qualifier"></a>**Qualifier** — A restriction of a claim to one of its
  operator's dimensions, with a quantifier. ([records](records.md#propositions-and-claims))
- <a id="read-mount"></a>**Read mount** — A corpus a writer session reads but does not
  write; records may cite records in it. ([writes](writes.md#citations-across-mounts))
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
- <a id="retraction"></a>**Retraction** — A record that withdraws the standing of a
  record, a dataset route or a producer snapshot without changing it.
  ([records](records.md#other-world-records))
- <a id="role"></a>**Role** — A group's standing in a reservation assignment: `open`,
  `reserved`, `unresolved` or `withheld`.
  ([records](records.md#reservation-assignments))
- <a id="roots-log"></a>**The root's log** — The append-only, hash-linked chain the
  `atoms` engine keeps for each registered root: intents, transaction registrations
  and their settlements. Operation completion and log audit are read from it.
  ([writes](writes.md#operations))
- <a id="run"></a>**Run** — The record of one complete execution: recipe, outputs and
  the facts of the occurrence. ([records](records.md#specs-runs-and-assessments))
- <a id="scoped-writer"></a>**Scoped writer** — The writer a session hands one
  invocation, with exactly the permit that invocation needs.
  ([writes](writes.md#writer-sessions))
- <a id="sort"></a>**Sort** — The type of referent an argument slot or qualifier
  dimension admits, bound to a vocabulary. ([contracts](contracts.md#domain-contracts))
- <a id="source"></a>**Source** — A record of a published work, addressed by its first
  accepted external identifier. ([records](records.md#datasets-sources-and-holdings))
- <a id="source-assertion"></a>**Source assertion** — A record of what a source (a
  paper or other work) asserts. It has no route to belief.
  ([records](records.md#record-kinds))
- <a id="standing"></a>**Standing** — Whether a record is active, computed from the
  retractions that target it. ([guide](guide.md#worlds-identity-and-change))
- <a id="supersession"></a>**Supersession** — A `supersedes` link from a new record to
  the same-kind record it replaces. ([records](records.md#relations))
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
