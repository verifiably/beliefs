---
title: Glossary
status: living
created: 2026-08-08
updated: 2026-09-11
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-09-04-write-permits-design.md
  - ../designs/2026-09-05-writer-session-design.md
---

# Glossary

Terms are defined in their Science-specific sense. Follow the topic link for
context and the linked design references for normative detail.

- **Act family** — One of the six closed classes of write in `beliefs` —
  `corpus-write`, `run`, `holdings`, `registry`, `epoch`, `lifecycle` — that a
  write permit names. `KIND_ACTS` maps each record kind to the families
  admissible as its minting route; only the first three are reachable from a
  command. ([write-permits design](../designs/2026-09-04-write-permits-design.md))
- **Act report** — The boundary-minted terminal record of one opened
  operation — acquisition, audit, import, re-check, or a run attempt that
  minted no run — or the refusal record of a run request rejected before
  an operation can open. Inert by type; its entries record each member
  act's subject, explicit instrument inputs, and outcome in that act
  kind's own vocabulary, citable as (act-report ref, entry index).
  ([act-report design](../designs/2026-08-11-act-report-design.md))
- **Address** — A canonical lookup key, `kind:<basis-digest>`, distinct from
  label, location, and historical continuity. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Analysis spec** — An immutable preregistered plan naming a proposition,
  estimand, interpretation, inputs, parameters, nondeterminism, and equivalence
  rule for an assessment run. ([computation](computation-and-reproducibility.md#the-analysis-spec-freezes-the-scientific-plan))
- **Applicability** — The scope an estimand licenses, declared in the spec and
  possibly narrower than the proposition it targets. ([computation](computation-and-reproducibility.md#the-analysis-spec-freezes-the-scientific-plan))
- **Assessment** — A run-derived result that evaluates one proposition and is
  the only record kind allowed to enter empirical belief. ([claims](claims-and-belief.md#assessments-are-the-only-empirical-route))
- **Audit wrapper** — The boundary operation that runs the read-only
  audit evaluator and publishes its findings as entries in an inert act
  report, under the wrapper's own operation intent. The evaluator's
  contract is unchanged: it inspects any configuration, returns
  validation or findings, and mints nothing.
  ([act-report design](../designs/2026-08-11-act-report-design.md))
- **Atoms** — The bottom layer of the stack: durable atomic filesystem
  effects, including the pre-mutation registration boundary. Its own
  repository. ([foundations](foundations.md#ownership-follows-the-nature-of-the-rule))
- **Authority** — The frozen pair of a write permit and an actor, bound once
  at a construction seam (`open_corpus`, `open_world`, the operation port,
  the holdings act context, the lifecycle acts) and never per call. Every
  write entry point requires its act family and emitted kinds of the bound
  authority before any effect, and reads the actor from it.
  ([write-permits design](../designs/2026-09-04-write-permits-design.md))
- **Autonomy** — The top layer of the stack: the envelope, orchestrator,
  behavioral profiles and priority function that run the daily surface
  unattended. A separate repository, split from `science` on code-lineage
  independence. ([user and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md))
- **Belief** — A policy-bound computed view over a complete set of eligible,
  directional, independence-filtered assessments; v1 returns a signed integer.
  ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Belief input digest** — The identity of the exact world, records, standing,
  rules, and bindings consulted by a belief computation. ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Beliefs** — The epistemic kernel: this repository and its `beliefs`
  package — kernel kinds, world, runs, log, holdings, correction, conformance
  cuts, and the `domains/` and `practices/` packs. Named `science` until
  2026-08-30. ([foundations](foundations.md#ownership-follows-the-nature-of-the-rule))
- **Canonical projection** — The prescribed meaning-bearing representation
  hashed for an identity, excluding presentation and location fields.
  ([foundations](foundations.md#contracts-compile-into-profiles))
- **Claim** — The opaque runtime value of a proposition after its operator,
  arguments, qualifiers, polarity, and layer pass the active profile.
  ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Claim layer** — Which kind of claim a proposition makes — causal,
  structural, statistical, or methodological. The base contract fixes the set,
  each operator declares which layers it may inhabit, and the layer enters claim
  identity. ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Clean-environment verification** — A passed comparison of equal recipes
  with qualifying fresh-environment and confinement evidence; the only scope
  that can admit an assessment. ([computation](computation-and-reproducibility.md#replay-verification-and-belief-are-different-decisions))
- **Completion reading** — The three-valued, derived, never stored state
  of a boundary operation, read per root from its operation intent under
  the log's reduction: unfinished (unmatched intent), indeterminate
  (qualification unresolved — never collapsed into unfinished), and
  closed (fulfilled).
  ([act-report design](../designs/2026-08-11-act-report-design.md))
- **Conformance cut** — A prospectively selected subset of guarantee assertion
  arms that one implementation slice can exercise without crossing an
  undesigned boundary. ([adoption](contracts-and-adoption.md#adoption-follows-legal-partial-states))
- **Contract cut** — An immutable, content-addressed version of the normative
  Science contract and its exact oracle-case identities. ([contracts](contracts-and-adoption.md#designs-explain-contract-cuts-will-govern))
- **Corpus** — An admitted collection with a durable opaque `corpus_id`, a
  profile-pinning manifest, and identity-changing states. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
- **Corpus state identity** — A digest of the complete canonical corpus manifest
  plus the sorted identities of its nodes. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
- **Coreference attestation** — An attributed, additive record that two
  distinctly identified records of one kind are believed to name one thing. Its
  stance is `+1` or `-1`, its weight is one regardless of who authored it, and the
  pair's balance is derived rather than stored. A positive balance activates a
  query-layer coreference edge; nothing merges.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Dataset-production run** — A run shape that transforms data and produces one
  dataset without a proposition, spec, or assessment. ([computation](computation-and-reproducibility.md#one-run-kind-has-two-shapes))
- **Domain contract** — A namespaced declaration of domain sorts, operators,
  qualifier dimensions, facets, and vocabulary bindings. ([foundations](foundations.md#contracts-compile-into-profiles))
- **Epoch** — An immutable world-index publication over explicit corpus states,
  world records, rules, and derivation receipts. ([identity](identity-world-and-change.md#the-world-index-is-a-named-covered-view))
- **Estimand** — What quantity an analysis estimates, and at what scope. Frozen
  in the analysis spec and copied into the assessment rather than authored
  there. ([computation](computation-and-reproducibility.md#the-analysis-spec-freezes-the-scientific-plan))
- **Facet** — A named block of typed fields carried by a record. Base-profile
  facets are unnamespaced; domain facets are namespaced and may extend
  interpretation without redefining kernel relations. A dataset's
  empirical-observation facet is what lets a run's `observes` edge confer
  eligibility. ([facet-contracts design](../designs/2026-09-05-facet-contracts-design.md),
  [foundations](foundations.md#contracts-compile-into-profiles))
- **Declared** — A dataset carrying a content identity without a matching byte
  observation of every resource it declares. A world entity, authorable and
  referenceable, and never belief-eligible. Not the same as *unheld*: a run that
  looked in one place and found nothing has measured its own coverage. The
  route out is a matching holdings observation (G9).
  ([foundations](foundations.md#the-epistemic-invariant))
- **Held** — Exactly reproducible bytes available on demand under a content
  identity; not a synonym for raw, public, local, or checked into Git. Distinct
  from **declared**, which has the identity and not the bytes. Derived from
  active **holdings observations** under a declared coverage since
  2026-08-10.
  ([foundations](foundations.md#the-epistemic-invariant))
- **Holdings observation** — A world record of what one act found at one
  canonical location: `found` with an algorithm-qualified digest, or
  `absent` where a completed dereference answered. Act-minted, append-only,
  revised only by supersession, never expired by age; heldness is derived
  from the active observations under a declared coverage.
  ([holdings design](../designs/2026-08-10-verified-holdings-record-design.md))
- **Identifier correction** — An attributed source-identity event that replaces
  one canonical identifier map with another for the same work. It preserves the
  source UID, renames the address only when the selected basis changes, and keeps
  every retired address resolvable without rewriting referrers.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Identity basis** — The kind-specific semantic fields whose canonical
  projection determines a record's content identity. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Independence** — A pairwise, three-valued judgment derived from complete
  dataset-lineage closure: independent, shared-source, or not-certified.
  ([claims](claims-and-belief.md#assessments-are-the-only-empirical-route))
- **Instrument certification** — A recomputable witness that a specific rule and
  implementation binding conforms and can reach its required outcomes.
  ([contracts](contracts-and-adoption.md#rules-bind-meaning-to-the-code-that-ran))
- **Interpretation rule** — The versioned rule identity, frozen in the spec,
  that maps a run's result to the assessment's outcome. It is declared before
  the result exists. ([computation](computation-and-reproducibility.md#the-analysis-spec-freezes-the-scientific-plan))
- **Label** — A human-facing name computed on read from immutable record content
  and a pinned authority snapshot. It is never stored, never part of identity, and
  never resolved against.
  ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Mutation log** — A per-root hash-linked chain registering boundary
  transactions and destructive intent, with heads observed outside their own
  deletable set. ([identity](identity-world-and-change.md#mutation-history-is-detectable-relative-to-observers))
- **Nodes** — The entity/relation substrate beneath `beliefs`: generic
  storage, relation closure, traversal and mechanism, knowing no scientific
  semantics. Its own repository. ([foundations](foundations.md#ownership-follows-the-nature-of-the-rule))
- **NoBelief** — A successful answer saying belief cannot be produced because
  inputs are unavailable, no assessment is eligible, or only non-directional
  outcomes remain. ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Operation intent** — The tamper log's third intent consumer: appended
  once per boundary operation, after the observer-corpus root freezes and
  before any member act, carrying the operation kind, the minted event
  token, and the actor. It blocks nothing — completion visibility only —
  and its qualifying fulfillment is the operation's terminal record.
  ([act-report design](../designs/2026-08-11-act-report-design.md))
- **Operator** — A contract-declared claim predicate whose arity, argument
  sorts, qualifiers, polarity aptitude, and layers determine valid claims.
  ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Oracle** — A frozen guarantee obligation identified by a permanent label
  and made executable through a check plus a mutation that must break it.
  ([contracts](contracts-and-adoption.md#every-oracle-must-be-falsifiable))
- **Policy binding** — The required pair of belief-policy rule identity and
  implementation content identity used for one belief computation.
  ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Profile** — The runtime specification compiled from one Science base
  contract and the domain contracts pinned by a corpus manifest.
  ([foundations](foundations.md#contracts-compile-into-profiles))
- **Proposition** — An immutable record whose semantic identity is its typed
  claim structure, not its prose rendering. ([claims](claims-and-belief.md#structure-not-prose-determines-identity))
- **Published verification** — A verification record carrying its whole basis
  with the comparison report embedded under an id that is its identity; the
  audit and the import recompute its scope, and a record without a report is
  checked for verdict and identity only.
  ([verification publication](../designs/2026-09-06-verification-publication-design.md#41-the-facet))
- **Qualifier** — A restriction on one of an operator's declared dimensions,
  sorted exactly as an argument is. The v1 fragment is flat: one restriction per
  dimension, with a quantifier. ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Reads** — A run-input role for literature, configuration, ontologies, and
  other context that never confers empirical eligibility. ([foundations](foundations.md#closed-routes-inert-by-default))
- **Refused** — A fail-early boundary outcome for malformed, contradictory, or
  out-of-contract input; it never guesses or repairs. ([foundations](foundations.md#valid-transitions-refuse-audit-detects-bypasses))
- **Retraction** — An immutable, attributed record that subtracts an exact
  target's standing at read time without deleting or modifying it.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Rule binding** — The exact pair of a fixture-defined rule identity and the
  held implementation content identity that executed it. ([contracts](contracts-and-adoption.md#rules-bind-meaning-to-the-code-that-ran))
- **Run** — A complete immutable execution closure consisting of a recipe,
  result, and occurrence. ([computation](computation-and-reproducibility.md#a-run-has-three-complete-parts))
- **Science** — Two senses, deliberately: the name of the whole stack
  (`atoms`, `nodes`, `beliefs`, `science`, `autonomy`), which is how the
  banked designs use it; and the daily-surface layer above `beliefs` —
  harness-neutral commands and skills, generated adapters, the CLI and MCP,
  the derived work queue and publish — which is its own repository.
  ([user and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md))
- **Scoped writer** — The writer a session hands one invocation: bound to that
  invocation, refusing every act outside it, and holding an effective permit
  that is *exactly* the declared requirement rather than the session's ceiling.
  An act beyond the requirement is `PermitExceeded`, raised by the kernel entry
  point itself with nothing written.
  ([writer-session design](../designs/2026-09-05-writer-session-design.md))
- **Session ledger** — The append-then-fsync file a writer session keeps at
  `<operations root>/sessions/<session-id>/ledger.v1`: five typed canonical
  JSON lines — `session-open`, `claim`, `act`, `close`, `session-close` — each
  durable before its call returns. It is the session's own evidence of what it
  did; reconciliation reads it against the corpus chain, and an I/O failure
  ends the session with the bytes preserved as the failure left them.
  ([writer-session design](../designs/2026-09-05-writer-session-design.md))
- **Sort** — The type of referent a slot admits. Operators declare a sort per
  argument position and per qualifier dimension, so a term of one sort cannot
  fill a slot of another. ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Source assertion** — A record of what a source asserts, denies, or
  hypothesizes about a proposition; it is useful but has no edge into belief.
  ([foundations](foundations.md#the-epistemic-invariant))
- **Source address** — The `source:<digest>` lookup key derived under
  `science.source-address.v1` from the selected normalized external identifier,
  using fixed precedence DOI, PMID, ISBN, then accession.
  ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Standing** — The active status calculated from an acyclic retraction graph,
  including counter-retractions, rather than stored as a mutable flag.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Supersession** — An additive relation naming a replacement or continuation;
  unlike retraction, it does not subtract the predecessor's standing.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **UID** — A durable continuity identifier used when addresses change through
  correction, or when duplicate storage is consolidated. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Verification** — An immutable comparison of two runs under a frozen
  equivalence rule, with a derived scope and verdict. ([computation](computation-and-reproducibility.md#replay-verification-and-belief-are-different-decisions))
- **Write permit** — A closed set of record kinds and a closed set of act
  families a holder may emit. A launcher binds one inside the writer endpoint;
  `science` compiles a declaration to a `RequiredCapabilities` value and never
  holds a permit. Exceeding one is `PermitExceeded`, refused before any effect.
  ([write-permits design](../designs/2026-09-04-write-permits-design.md))
- **Writer session** — An attended session over one corpus root: a fresh
  session identity that fixes the actor as `session:<id>`, a session ledger,
  the claim protocol that makes an invocation replayable, and every
  session-mediated ordinary write performed as one `corpus-write` operation
  intent followed by exactly one committed registration fulfilling it. It is
  the `beliefs` half of the command framework's write boundary beyond permits.
  ([writer-session design](../designs/2026-09-05-writer-session-design.md))
- **World** — The union of admitted corpora and world-level records; projects
  are views over it, not separate epistemic universes. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
