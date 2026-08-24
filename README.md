# science

A system for recording scientific belief and the evidence it rests on, built on
two substrates: [`nodes`](https://github.com/khughitt/nodes) (the logical
entity/relation kernel) and [`atoms`](https://github.com/khughitt/atoms)
(durable atomic filesystem effects).

This repository is a clean start. Its predecessor is preserved, public and
unchanged, as [`proto-science`](https://github.com/khughitt/proto-science) —
where the design work below was done and reviewed. Nothing here imports it, and
records are reproduced under this system rather than migrated into it; the
reasoning is recorded in the adoption ledger's §0.

Start with the concise [contributor guide](docs/guide/README.md) for the system's
key ideas, reading paths, glossary, and open questions. Use the design corpus
below for rationale and frozen guarantees.

## The designs

Thirty-four documents in `docs/designs/`: the banked redesigns, review disposition,
adoption ledger, measurements, rulings, and contributor-guide design written
2026-08-02 through 2026-08-23. Read them in this order:

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

The ledger is the entry point for "what is built, what is not, and what waits on
what." Every guarantee table is frozen under its identifiers: designs extend and
amend in place, never renumber.

## Status

Design complete. The **conformance cut 1 vertical slice** (ledger §3, item 10)
landed 2026-08-07 — typed claim construction, canonical projection, identity,
decode and cross-language parity. It crosses no persistence boundary and
computes no belief, which is where the disposition record's §5.5 stop rule puts
its edge. Cut 1 itself built nothing beyond that edge.

The guarantee tables are the acceptance criteria — each row must be a failing
test before it is a passing one. There are **151 rows** across **thirteen frozen
tables** (G, S, W, R, C, X, N, L, D, M, P, H, T). Cut 1 selects **11 of the 126 rows**
across the ten tables that existed when it was drawn, frozen *before* any code
existed so that a row which fails is a failure rather than a redefinition.
**Conformance cut 2** was frozen 2026-08-09 on the same discipline, before its
slice existed: it is drawn at the **belief seam** — the derived admission state,
the assessment admission gate, the belief input closure digest, and
`science.belief.v1` under an exact binding — selecting **13 rows in full and 11
in part**, including the belief policy's P1–P9 and the admission ramp's G9,
whose verified-holdings observations enter as supplied arguments because where
they are recorded was, at the freeze, an open design — closed 2026-08-10 by the
verified-holdings record design. Its slice landed 2026-08-09: derived admission
state, the assessment admission gate, the belief input closure digest, and
`science.belief.v1` under an exact binding now compute.

**Conformance cut 3** was frozen 2026-08-11, before any of its implementation
existed, at the **run boundary**: spec freezing and closure construction, the
execution boundary through the minimal Snakemake adapter, dataset production,
replay and verification-as-value, and the completion and report layer —
selecting **15 rows in full and 19 in part**, with every H arm and T7 deferred
to the persistence seam. Its slice landed 2026-08-12: spec freezing, the execution closure, the
minimal Snakemake adapter's boundary, dataset production, replay,
verification-as-value, and the report layer's completion reading now run as
real subprocess executions over held fixtures.

**Conformance cut 4** froze 2026-08-18 when the composition-root adapter
design banked, selecting **3 rows in full and 8 in part**. Its implementation
landed and the cut was discharged on the certified volume that day.

**Conformance cut 5** froze and was discharged 2026-08-19. The family adapters
now implement supersede, revise, retraction, and explicit import through the
certified composition root, with **28 selected declarations** across **8 rows
in full and 10 in part**; 6 rows remain fully deferred.

**Conformance cut 6** froze and was discharged 2026-08-20. The authoritative
world root, corpus manifest and fresh adoption, corpus-state identity, registry
admission, lifecycle status, and presence core now run, with **14 selected + 8
labeled = 22 declarations** across **2 rows in full and 2 in part**; X7 remains
fully deferred. See the [results](docs/plans/2026-08-20-conformance-cut-6-results.md).

**Conformance cut 7** froze 2026-08-20 and was discharged 2026-08-22. The
world-index epoch carrier — the rules store, coherent capture, four derived maps
and their receipts, epoch publication with `current`, bounded reads, whole-epoch
GC, and anchor carriage — now runs, with **38 selected + 10 labeled = 48
declarations** across **7 rows in full and 4 in part**. See the
[results](docs/plans/2026-08-20-conformance-cut-7-results.md). The work **merged
into `main` on 2026-08-22 preserving history**; the results record's §7 names a
history constraint that outlives that merge.

**Conformance cut 8** froze 2026-08-22 and was discharged 2026-08-23.
World-index slice 3 implements the Science half of the
tamper-evident mutation log: the registry log-head record and the exported head
artifact, the explicit anchor act, the one read-only four-outcome evaluator
behind an audit act and a verified `ReplicaOf` arrival act, registered-surface
replay with its removal policy pass, the world genesis↔mirror agreement check,
and the ordered-cuts predicate — **43 selected + 10 labeled = 53 declarations**
across **5 rows in full and 7 in part**, with L6 unread and 51 of the 53 units
certified in full. See the
[results](docs/plans/2026-08-22-conformance-cut-8-results.md). The work
**merged into `main` on 2026-08-23 with `--no-ff`** (integration commit
`10cc84b`), inheriting cut 7's reachability constraint and adding cut 8's
freeze commit to it.
Three of kernel §8.7's four recorded-mutation consequences close there; G4 does
not.

```
python/     the implementation (substrate §11 puts the composition root here)
ts/         the one shared encoding, and nothing else (formal model lim. 9)
fixtures/   the cross-language parity corpus, owned by neither
contracts/  the science base contract
```
