# beliefs

The epistemic kernel of **Science** — a system for recording scientific belief
and the evidence it rests on. This repository is the `beliefs` layer: the
typed kernel kinds, the world, runs and their verification, the mutation log,
holdings, the correction lifecycle, and the conformance cuts that certify
them. It is built on two substrates, [`nodes`](https://github.com/khughitt/nodes)
(the logical entity/relation kernel) and [`atoms`](https://github.com/khughitt/atoms)
(durable atomic filesystem effects), and it is consumed by the two layers above
it — `science`, the daily surface people and agents use, and `autonomy`, the
envelope and orchestrator — whose design is
`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`.
"Science" names the whole stack; the rename of this repository from `science`
to `beliefs` is that design's §3.1 (2026-08-30), and its contract and rule
identities (`contract: science`, `science.identity.v1`, …) are the names of
rules, not of this repository, and did not change.

This repository is a clean start. Its predecessor is preserved, public and
unchanged, as [`proto-science`](https://github.com/khughitt/proto-science) —
where the design work below was done and reviewed. Nothing here imports it, and
records are reproduced under this system rather than migrated into it; the
reasoning is recorded in the adoption ledger's §0.

Start with the concise [contributor guide](docs/guide/README.md) for the system's
key ideas, reading paths, glossary, and open questions. Use the design corpus
below for rationale and frozen guarantees.

## The designs

Sixty documents in `docs/designs/`: the banked redesigns, review disposition,
adoption ledger, measurements, rulings, and contributor-guide design written
2026-08-02 through 2026-09-10. Read them in this order:

| document | what it rules |
|---|---|
| `2026-08-02-epistemic-kernel-design.md` | what belief is, what may change it, and what the system does not claim (guarantees G1–G9) |
| `2026-08-02-substrate-consolidation-design.md` | the `nodes`/`atoms` seam and the profile a corpus runs under (S1–S8) |
| `2026-08-02-world-addressing-design.md` | addresses, corpora, and the world index (W1–W16) |
| `2026-08-02-computation-reproducibility-design.md` | runs, recipes, replay, and lineage (R1–R23) |
| `2026-08-03-correction-lifecycle-design.md` | retraction and correction — subtracting standing without deleting a record (C1–C10) |
| `2026-08-03-world-index-packaging-design.md` | where the index lives, who writes it, and what freshness a consumer may assume (X1–X12) |
| `2026-08-03-normative-contract-design.md` | the versioned contract, its conformance oracles, and instrument certification (N1–N10) |
| `2026-08-03-tamper-evident-log-design.md` | pre-mutation registration and detectable removal (L1–L13) |
| `2026-08-04-domain-extension-boundary-design.md` | where domain-specific material lives, and how interpretation stays separable from identity (D1–D10) |
| `2026-08-04-formal-model-and-claim-calculus-design.md` | a formal model of the whole system, and what a claim *is* — typed, with identity over its structure rather than its prose (M1–M13) |
| `2026-08-05-review-disposition-and-conformance-cut-1.md` | disposition of an external review, measured against the trees, and the frozen first conformance cut |
| `2026-08-05-belief-policy-design.md` | what a belief *value* is, the exact binding it is pinned under, and the three answers to asking for one (P1–P9) |
| `2026-08-07-corpus-survey-and-vocabulary-admission-design.md` | what eight predecessor corpora actually contain, and what earns a vocabulary a place in the base profile |
| `2026-08-07-multi-corpus-typing-exercise.md` | the first executable multi-corpus claim-typing measurement and its vocabulary-admission result |
| `2026-08-03-redesign-adoption-ledger.md` | dependency order between the above, and the legal partial states in between |
| `2026-08-08-contributor-guide-design.md` | the organization, authority, freshness, and verification rules for the concise contributor guide |
| `2026-08-08-world-address-ruling.md` | closes docket §4.1: basis-derived addressing upheld, labels rendered rather than stored, coreference graded rather than merged |
| `2026-08-09-admission-ramp-design.md` | how externally sourced input reaches held — the measurement, and the ruling downstream of it: three states, `W3` narrowed, `G9` appended, F2 closed |
| `2026-08-09-conformance-cut-2.md` | the second frozen conformance cut, drawn at the belief seam over the 139-row corpus, with the admission ramp's three open questions as boundary conditions |
| `2026-08-10-verified-holdings-record-design.md` | where verified holdings are recorded: a per-location world record in the observer's corpus, act-minted, superseded never expired, projected under a declared coverage — H1–H4 |
| `2026-08-11-act-report-design.md` | the run boundary's report seam: the act-report, boundary-minted terminal record of an opened operation or pre-intent refusal record of a rejected run request; the operation intent's derived three-valued completion reading; the durable home of a look's non-report — T1–T8 |
| `2026-08-11-conformance-cut-3.md` | the third frozen conformance cut, drawn at the run boundary over the 151-row corpus: 15 rows selected in full and 19 in part, amended across three readings with the frozen text preserved verbatim, and the persistence seam's H1–H4 and T7 deferred on the holdings design's own assignment |
| `2026-08-17-conformance-cut-4.md` | the fourth conformance cut, frozen 2026-08-18 against the certified `atoms` engine adopted at Science's composition root: the first persistence slice, add-only, corpus-write minting alone, selecting 3 rows in full and 8 in part |
| `2026-08-18-composition-root-adapter-design.md` | Science's composition root, durable executor adapter, add-only write boundary, read capability boundary, and cut-4 acceptance suite |
| `2026-08-19-family-adapters-design.md` | supersede, retraction, and explicit-import families at Science's certified composition root |
| `2026-08-19-conformance-cut-5.md` | the fifth frozen conformance cut, selecting the family-adapter implementation surface |
| `2026-08-20-world-registry-design.md` | the world-index authoritative slice: world root and mirror, corpus manifest and fresh adoption, corpus-state identity, registry admission, and lifecycle status |
| `2026-08-20-conformance-cut-6.md` | the sixth frozen conformance cut, selecting the world-registry slice's registry-side and identity arms: 2 rows full, 2 part, 1 deferred, with 8 labeled declarations |
| `2026-08-20-world-index-slice-2-design.md` | the world-index epoch carrier: rules, coherent capture, four derived maps and receipts, publication, bounded reads, and whole-epoch GC |
| `2026-08-20-conformance-cut-7.md` | the seventh frozen conformance cut, selecting the epoch carrier: 7 rows full, 4 part, with 38 selected and 10 labeled declarations |
| `2026-08-22-log-verification-design.md` | world-index slice 3, the Science half of the tamper-evident mutation log: the registry log-head record and exported head artifact, the explicit anchor act, the one four-outcome log evaluator behind an audit act and a verified `ReplicaOf` arrival act, replay with its removal policy pass, the world genesis↔mirror check, and the ordered-cuts predicate |
| `2026-08-22-conformance-cut-8.md` | the eighth frozen conformance cut, selecting log verification and anchoring: 5 rows full, 7 part, L6 unread, with 43 selected and 10 labeled declarations |
| `2026-08-23-world-index-root-lifecycle-design.md` | world-index slice 4, the root lifecycle and store substrate: the atoms fail-closed writer state and lifecycle commands (replicate, restore admission, fork, migrate), the store root kind with genesis-bound store subjects, the fork acts with act-derived `forked_from`, and lifecycle-aware arrival modes |
| `2026-08-23-conformance-cut-9.md` | the ninth frozen conformance cut, selecting the root lifecycle and store substrate: 1 row full, 4 part, with 19 selected and 11 labeled declarations, successor to cut 8's retired store-refusal label |
| `2026-08-24-world-index-holdings-design.md` | world-index slice 5, verified store-side holdings: the governed observation kind, intent-bearing store acts, mechanical coverage, fixture-bound reduction and receipt, and dataset admission adapter |
| `2026-08-24-conformance-cut-10.md` | the tenth frozen conformance cut, selecting verified store-side holdings: 3 rows full, 4 part, with 20 selected and 11 labeled declarations |
| `2026-08-26-world-index-intent-boundary-design.md` | world-index slice 6, general intent qualification: the three-shape reduction, bounded captured evidence, durable run publication, verifier lift, regenerated holdings interior, and completion re-base |
| `2026-08-27-conformance-cut-11.md` | the eleventh frozen conformance cut, selecting general intent qualification: 1 row part, with 13 selected and 13 labeled declarations; G4 deliberately unread, owned by the successor-admission slice |
| `2026-08-29-conformance-cut-12.md` | the twelfth frozen conformance cut, selecting successor admission: 2 rows full, 1 part, with 19 selected and 5 labeled declarations; G4 read at persistence width |
| `2026-08-29-successor-admission-design.md` | the successor-admission slice: the two-set core, the deriving boundary `admit_spec_successor` over the chain's qualification and the corpus's verification evidence under one hold, the superseder-side oversized rule, and the named evidence refusal |
| `2026-08-30-conformance-cut-13.md` | the thirteenth frozen conformance cut, selecting run confinement: 4 rows full, 2 part, with 15 selected and 7 labeled declarations; `clean-environment` reachable |
| `2026-08-30-run-confinement-design.md` | the run-confinement slice: the confined boundary policy, the per-file runtime closure and its snapshot, the probe-gated bubblewrap launch observed from the boundary's own `/proc`, the confined receipt and run domains, `derive_scope`'s `clean-environment` row, and the value-level admission join |
| `2026-08-31-coordination-and-view-kinds-design.md` | the coordination tier: closed view-query grammar, versioned coordination contract, opaque project/local addressing, immutable multi-corpus revision family, and world-inert storage; cut 14 discharges it except W17 intent-position |
| `2026-09-03-world-changing-families-design.md` | the two-root `move` and `consolidate` operations, managed deletion, their lock and crash discipline, and the two cuts that discharge them |
| `2026-09-03-conformance-cut-16.md` | the discharged relocation cut: W5 in full, G3 and D7 closed, five partial rows, and T8 re-read against both relocation operations |
| `2026-09-04-conformance-cut-18.md` | the discharged deletion cut: managed `delete` as an ordinary write, the audit and import ride-alongs, 7 rows closed, 5 partial, 4 closed-row re-reads |
| `2026-09-04-write-permits-design.md` | the discharged write-permits slice: closed act families and kind routes, `Authority` bound once at every construction seam, checks before effects across the static entry-point inventory, and E1–E8 closed at cut 17 |
| `2026-09-05-mm30-reproduction.md` | the mm30 reproduction measurement: one real proposition pushed through the kernel as a library to the belief evaluator's answer, with its predictions, findings and re-rank |
| `2026-09-05-facet-contracts-design.md` | the first `domain-boundary` slice, anchored on the empirical-observation facet's payload contract: facet and kind declarations in the base and domain contracts, the compiled per-kind registry and payload validators, the bearer invariant and attestation binding, the shipped base profile and the pin recheck under the operation lock, and the second `science.identity.v1` parity fixture (F1–F8, cut 20 to freeze) |
| `2026-09-05-conformance-cut-20.md` | the twentieth frozen conformance cut, selecting the facet-contracts slice: 15 rows full, 1 part, with 18 declaration units |
| `2026-09-05-writer-session-design.md` | the writer-session slice: the attended session and its fixed actor, the append-then-fsync session ledger and claim protocol, the scoped writer bound to one invocation and exactly its requirement, `corpus-write` as an operation intent fulfilled by its registration, and reconciliation over ledgers and chains (J1–J11, closed at cut 19) |
| `2026-09-09-session-routes-design.md` | the public store identity reader, the scoped writer's ledgered run and holdings routes, reconciliation over their intent shapes, and reference rules under kernel-scoped identities |
| `2026-09-05-conformance-cut-19.md` | the frozen writer-session cut: J1–J11 selected in full, 11 declaration units, the cut 18 runner as prefix; discharged 2026-09-05 |
| `2026-09-06-verification-publication-design.md` | the verification-publication slice: a derived verification published as an ordinary `add` carrying its whole basis with the comparison report embedded, one spelling for the assessment's run member, admission over records read back, scope recomputed by the audit and the import, and the stored analysis-spec builder and reader (V1–V8, closed at cut 21) |
| `2026-09-06-conformance-cut-21.md` | the frozen verification-publication cut: V1–V8 selected in full, 8 declaration units, the cut 20 runner as prefix; discharged 2026-09-07 |
| `2026-09-08-biology-pack-design.md` | the second domain-boundary slice: cross-contract slot sorts, consulted-profile pin agreement, domain-facet reads, and the packaged biology contract (B1–B7, closed at cut 22) |
| `2026-09-08-conformance-cut-22.md` | the discharged biology-pack cut: B1–B7, the cross-contract consulted walk, domain-facet read, and packaged biology contract |
| `2026-09-09-conformance-cut-23.md` | the discharged world-read cut: the world read view, cross-corpus traversal, covered absence, and cross-corpus verification |
| `2026-09-10-conformance-cut-24.md` | the discharged coreference-attestation cut: the governed record, populated balance, receipt completeness, endpoint refusals, and unchanged read side |
| `2026-09-10-conformance-cut-25.md` | the discharged source-address cut: normalized identifier-derived addresses, attributed identifier correction, W1/W2/W5a closed, and 24 N2 arms |

The ledger is the entry point for "what is built, what is not, and what waits on
what." Every guarantee table is frozen under its identifiers: designs extend and
amend in place, never renumber.

## Status

Every conformance cut through **cut 25** is implemented and discharged. What
runs today: typed claims, admission and belief computation; run closure,
execution, replay, act reports, general intent qualification and successor
admission; certified persistence through the composition root, with the
supersede, revise, retraction and import families; the world registry with
epochs, mutation-log anchoring and verification, root lifecycle, and verified
store-side holdings; run confinement, a run executing inside a fresh
namespaced materialization of a digest-verified runtime closure with
`clean-environment` reachable; and the coordination/view family with opaque
addresses, contract authorization, multi-corpus tip resolution, and world-inert
storage; the full workflow surface with planning-derived job and target
sets, semantic wildcard jobs, per-family seed obligations, and composed
planning/execution launch attestations; two-root `move` and `consolidate`
with root-local durable operation evidence; write permits bound at every
write seam, with no caller-supplied actor; and managed deletion — `delete` as
an ordinary write under the root's lock, the corpus-local semantic audit,
explicit-import derivation validation, the claim restore seam, and the
instrumented belief resolver; and the writer session — an attended session
whose identity fixes the actor, an append-then-fsync session ledger with its
claim protocol, an invocation-bound scoped writer whose effective permit is
exactly its requirement, every session-mediated ordinary write as one
`corpus-write` operation intent fulfilled by its registration, unresolved-root
settlement before every prepare, and reconciliation over ledgers and chains;
facet contracts — closed facet schemas declared by the base and domain
contracts, profiles compiling kinds, relations and facets, and every write seam
validating the caller-held profile; and verification publication — a derived
verification published as an ordinary `add` carrying its whole basis with the
comparison report embedded, one spelling for the assessment's run member,
admission evaluated over records read back, scope recomputed from a stored
verification, forgery refused before the intent, and the stored analysis-spec
builder and reader.
The biology pack now supplies cross-contract slots, consulted-pin agreement,
domain-facet reads, and the packaged `biology` contract. The world read view
now captures records at an explicit published epoch, traverses across corpora,
and carries named absence into lineage and evaluation. Coreference attestations
are now governed, minted through the ledgered session route, and reduced into
the published coverage-bound balance. Source addresses are now derived from
normalized identifiers, and identifier correction preserves attributed history.
The latest discharged boundary is cut 25
([cut](docs/designs/2026-09-10-conformance-cut-25.md),
[design](docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md)).

The guarantee tables are the acceptance criteria — each row must be a failing
test before it is a passing one. There are **195 rows** across **eighteen frozen
tables** (G, S, W, R, C, X, N, L, D, M, P, H, T, E, F, J, V, B), and every cut is frozen
*before* its code exists so that a row which fails is a failure rather than a
redefinition.

What is built and what remains to build, each remainder with its named owner,
is stated once, in the
[adoption ledger's current-state summary](docs/designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-11).
The per-cut results records under [`docs/plans/`](docs/plans/) are the
evidence trail, and unresolved design questions live in the guide's
[open questions](docs/guide/open-questions.md).

```
python/     the implementation, package `beliefs` (substrate §11 puts the composition root here)
ts/         the one shared encoding, and nothing else (formal model lim. 9)
fixtures/   the cross-language parity corpus, owned by neither
contracts/  the science base contract
```
