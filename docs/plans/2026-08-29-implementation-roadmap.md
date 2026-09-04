# Implementation roadmap

**Ranked at:** cut 16, against the ledger's Current state (2026-09-04)
**Method:** `../superpowers/specs/2026-08-29-implementation-roadmap-design.md`
**Recomputed by:** the commit that adds each conformance-cut results record.
This document is a current claim: it is rewritten whole at every re-ranking,
carries no dated corrections, and the previous ranking survives only in git
history.

The adoption ledger's `Current state` table
(`../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-04`)
is the authority for *what* is open; this document is the authority for *in
what order*. The two name the same boundaries by id, and
`test_the_roadmap_and_ledger_name_the_same_boundaries` holds them to it.
Design questions are never rows here; they appear only as a boundary's
*blocked on*, linking `../guide/open-questions.md`.

Ranking is dependency first, then breadth of what a boundary unblocks. A
boundary is **tier 1** when its entry point is designed and nothing outside
its own work must land first; **tier 2** when another boundary here or a
cross-repo seam must land first; **tier 3** when a design question must be
answered first. A prerequisite that is the boundary's own work is not a
prerequisite.

Cut 16 delivered two-root `move` and `consolidate`: W5 now reads in full, G3
and D7 close, and T8 was re-read. `consolidate-family` remains live only for
managed deletion and the deletion cut's assigned ride-alongs. W16, C3, R23,
M3 and T2 keep only the remainders named below.

## Boundary index

Every boundary the ledger table lists, by id. This section is the guard's
join key and nothing else; the tiers below carry the ranking.

| id | rows it closes | tier |
|---|---|---|
| `consolidate-family` | G2c, G8, C6, R5; S5's deletion half; W16 and R23's deletion clauses; C1, T8, M11, M13 re-reads; then the assigned R19, R22, M1, M3 and M5 ride-alongs | 1 |
| `url-retrieval` | H4, G9, R10, T5; T7's same-root case | 1 |
| `world-resolution` | W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 (less one arm); W8a's coreference arms; S1, S1a, S5's cross-corpus reach; D3; X12 and M3's coreference arms; R23's snapshot clauses | 1 |
| `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | 1 |
| `event-level-l8` | L8 | 1 |
| `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12, C10's certification arms; R23's rules-store clauses | 1 |
| `run-boundary-remainder` | R19; R22's import and audit arms | 1, rides with `consolidate-family` |
| `formal-model-remainder` | M1; M3's audit and admission-order arms; M5 | 1, rides with `consolidate-family` |
| `log-remainder` | L1, L4; L10 (relabel) | 1, rides with `event-level-l8` |
| `act-report-remainder` | T1, T2, T4 | 1, rides with `url-retrieval` |
| `packaging-remainder` | X5 (relabel); W8a's import and audit arms | 1, rides with `world-resolution` |
| `parity-fixture-2` | the second `science.identity.v1` fixture | 1, rides with `domain-boundary` |
| `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | 1 |
| `l13-preimage` | L13 | 2 |
| `persistence-cut` | X2 | 2 |
| `verification-publication` | durable publication of verification records | 2 |
| `nodes-remainder` | `nodes` row 3's three items | 2 |
| `authority-labels` | W9, W14 | 3 |
| `weighted-belief` | S6 (h) | 3 |
| `extraction-path` | M12 | 3 |
| `cross-root-publication` | T7's cross-root case | 3 |

## Tier 1 — buildable now

Ordered by what a boundary unblocks, and grouped into **lanes** (§Lanes
below). A boundary's rank says how much it unblocks; its lane says what it
must wait for. Within a lane the order is strict; across lanes there is no
order, and lanes may run concurrently in separate worktrees.

| # | id | rows | unblocks | placement |
|---|---|---|---|---|
| 1 | `consolidate-family` | G2c, G8, C6, R5; S5's deletion half; W16 and R23's deletion clauses; C1, T8, M11, M13 re-reads; then R19, R22, M1, M3 and M5 | the last mutation family and the mutation lane's two assigned ride-alongs | relocation landed at cut 16; the same design now assigns managed deletion first, then its run-boundary and formal-model ride-alongs |
| 2 | `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | the correction lifecycle in full | C7's consolidate prerequisite landed at cut 16; the stored semantic-snapshot kind and evaluator are this boundary's own work. It follows `consolidate-family` only because the mutation lane is serial |
| 3 | `url-retrieval` | H4, G9, R10, T5, T7's same-root case | the first acquisition of a dataset from outside the system; H4 in full | holdings design §2–§3 specify the canonicalization profile and network discipline |
| 4 | `world-resolution` | W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 (less one arm), W8a's coreference arms; S1, S1a, S5's cross-corpus reach; D3; X12 and M3's coreference arms; R23's snapshot clauses | the read side of the world: resolution states, cross-corpus edges, views, the coreference balance over the map cut 7 published | cut 4 §5 deferred the group on "the write boundary and the index" — both landed; the address ruling supplies the oracles. W11/W12 are not here (§3.3) |
| 5 | `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | the first domain pack; D8's composition | cut 3 §5 deferred the group on "facets, manifests, and the registry compile"; `ProfileSpec` and the `nodes` registry exist |
| 6 | `event-level-l8` | L8 | row 5 reads L8 in full; the log's last Science-only remainder | §7's ordered-cuts predicate is built; the event-level relation is its successor |
| 7 | `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12 and C10's `instrument-certification` arms; R23's rules-store clauses | the widest set: the conformance-package split (ledger §5), instrument-certification cadence, legacy-check disposition (N10), P1 | last in the tier although it unblocks the most: N1 mints a successor contract identity for every oracle amended after the freeze, and rows 1–6 are Science-only closures that would each force one. Freeze after them |

**Ride-along closures**, tier 1 by the rule and unblocking no capability of
their own, each named to the cut that takes it:

| id | rows | rides with |
|---|---|---|
| `run-boundary-remainder` | R19; R22's import and audit arms | `consolidate-family` — the import family dialect is that cut's surface |
| `formal-model-remainder` | M1; M3's audit and admission-order arms; M5 | `consolidate-family` — retraction graphs over the same surface |
| `log-remainder` | L1, L4; L10 (relabel) | `event-level-l8` |
| `act-report-remainder` | T1, T2, T4 | `url-retrieval` — the acquisition operation is the first new operation kind T2 needs |
| `packaging-remainder` | X5 (relabel); W8a's import and audit arms | `world-resolution` |
| `parity-fixture-2` | formal model §8's second fixture | `domain-boundary` — D4's own parity arm exercises the same Python/TypeScript projection machinery |

A ride-along is named in the cut that takes it and never stands alone.

## Lanes — what may run concurrently

A **lane** is a set of boundaries that share a code surface and therefore
land serially; two lanes share no surface they both rewrite and may run at
the same time. Lanes are dependency- and surface-based, never goal-based:
the roadmap design rejected goal tracks (its §5) because one boundary would
sit under several goals, and no boundary below sits in two lanes. The
ranking above still holds within a lane — a lane's first boundary is its
highest-ranked one — and tier membership is unchanged by lanes: a tier-2
boundary sits in the lane of its prerequisite and waits there.

| lane | boundaries, in order | shared surface | touches another lane at |
|---|---|---|---|
| `acquisition` | `url-retrieval` (+ `act-report-remainder`) | `holdings/`, `report.py` | `boundary.py`, also used by the discharged workflow surface |
| `mutation` | `consolidate-family` (+ `run-boundary-remainder`, `formal-model-remainder`) → `correction-remainder` | `adapter.py`, `corpus.py`, `decode.py`, `evaluation.py`, `world/verify.py` | `world/verify.py`, which the `world-read` lane also owns |
| `world-read` | `world-resolution` (+ `packaging-remainder`) → `event-level-l8` (+ `log-remainder`) | `world/read.py`, `resolution.py`, `world/verify.py` | `world/registry.py` (above) |
| `domain` | `domain-boundary` (+ `parity-fixture-2`) | `profile.py`, `contract/`, `ts/`, `fixtures/`, the `nodes` registry | none in `python/src/beliefs/` |
| `cross-repo` | `l13-preimage`, `persistence-cut`, `nodes-remainder`, in any order | the `atoms` and `nodes` repositories, each behind its own design gate | none; Science consumes each seam after it lands |

`contract-cut` is in no lane. It is a **join**: it freezes after every lane
that amends an oracle has merged, for the reason tier 1's row 7 gives — N1
mints a successor contract identity for every oracle amended after the
freeze, and each lane above amends at least one. Tier 3 boundaries are in no
lane either; a design answer moves one into the lane of the surface it
lands on. `verification-publication` carries no design yet (its prerequisite,
below) and so sits in no lane, the same way `persistence-cut` did before its
cross-repo seam was named.

### Concurrency rules

Every rule the corpus already has stays in force when lanes run at once —
a cut is frozen before its code exists, discharged on the certified volume,
and merged `--no-ff`. Five rules are added by concurrency itself:

1. **A cut number is claimed at freeze, not at discharge.** Two lanes that
   freeze on the same day take consecutive numbers in freeze order, and a
   lane that discharges first does not renumber. Results records may
   therefore land out of numeric order; the guard selects the newest by
   number, so a re-rank is against the highest-numbered discharged cut.
2. **Results record and re-rank land one at a time.** The commit that adds
   a results record rewrites the ledger's `Current state` table and this
   roadmap, and `test_the_roadmap_and_ledger_name_the_same_boundaries`
   holds `Ranked at` to the newest record — so a second lane's discharge
   commit rebases onto the first's and re-ranks again. A lane's code may
   merge before its results record does; the record is what re-ranks.
3. **Shared files are named, not discovered in the merge.** `errors.py`,
   `python/tests/test_designs_corpus.py`, the ledger, this roadmap, and the
   guide index are rewritten by every lane; a lane's design names any other
   file it will rewrite that another lane's shared-surface column lists,
   and the later merge resolves toward the earlier one.
4. **A lane holds one worktree under `.worktrees/`**, named for its first
   open boundary, and a lane's boundaries are not split across worktrees.
5. **A cut names the highest-numbered acceptance runner.** A cut frozen while
   a lower-numbered cut is undischarged serializes its discharge after that
   cut's discharge.

## Tier 2 — after a named prerequisite lands

| id | rows | prerequisite | unblocks |
|---|---|---|---|
| `l13-preimage` | L13 | an `atoms` blob-read seam behind its own design gate; `atoms`' deferred-obligation ledger carries no such entry today | row 5 in full; the held-copy match strengthened from path to bytes |
| `persistence-cut` | X2 | the `atoms` A8 certification extended to the publication path, behind `atoms`' own design gate. Cut 7 admits a Science-side harness as the alternative; it is rejected here (§5), so the prerequisite is cross-repo and the tier is 2 | X2 in full |
| `verification-publication` | — | the persistence seam — a design for durable verification records behind the store's own gate; cut 13 §7.2 kept the join value-level | admission over stored verifications rather than in-memory records |
| `nodes-remainder` | — | `nodes`' own design gate | audits over damaged corpora; manifest safety |

## Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| id | rows | blocked on |
|---|---|---|
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot — [which external authorities are accepted](../guide/open-questions.md#identity-world-and-change) |
| `weighted-belief` | S6 (h) | ρO3, estimand typing — [weighted belief](../guide/open-questions.md#claims-and-belief) |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 — [higher-order records and extraction](../guide/open-questions.md#claims-and-belief) |
| `cross-root-publication` | T7's cross-root case | [the act-report's residue](../guide/open-questions.md#contracts-and-adoption) |

## Appendix A — live status of every guarantee row at cut 16

Produced by `python/tools/roadmap_status.py` from the cuts' own accounting
(spec §3.1); a row is closed only when no later source reopens it.

| table | never selected | part — last cut that read it | reopened |
|---|---|---|---|
| G | G5 | G2c (cut 5), G8 (cut 5), G9 (cut 10) | — |
| S | — | S1 (cut 4), S1a (cut 4), S5 (cut 4), S6 (cut 2) | — |
| W | W1, W2, W4, W6, W7, W8, W9, W10, W14, W15, W5a, W8b | W13 (cut 14), W16 (cut 16), W17 (cut 14), W8a (cut 7) | — |
| R | — | R5 (cut 3), R10 (cut 3), R19 (cut 4), R22 (cut 4), R23 (cut 16) | — |
| C | C7, C8, C9 | C3 (cut 16), C6 (cut 5), C10 (cut 5) | — |
| X | — | X2 (cut 7), X5 (cut 7), X12 (cut 7) | — |
| N | N1, N3, N4, N5, N6, N7, N8, N9, N10 | N2 (cut 4) | — |
| L | — | L1 (cut 8), L2 (cut 9), L4 (cut 9), L7 (cut 12), L8 (cut 8), L10 (cut 10), L13 (cut 8) | — |
| D | D1, D2, D4, D5, D8, D9, D10 | D3 (cut 2), D6 (cut 2) | — |
| M | M1, M12 | M3 (cut 16), M5 (cut 5) | — |
| P | — | P1 (cut 2) | — |
| H | — | H4 (cut 10) | — |
| T | T7 | T1 (cut 5), T2 (cut 16), T4 (cut 3), T5 (cut 3) | — |

Closed 78 of 153; open 75.

## Appendix B — classification of every open row

Each open row, its remainder as the last cut states it, and where it goes
(spec §3.2's three classes: schedulable, relabel, limitation).

| row | remainder (source) | classification → boundary |
|---|---|---|
| G5 | "no such kind exists" checkable only at the registry compile (cut 4 §5) | rides with `domain-boundary` |
| G2c | the standing-retraction clause of "active" (cut 2 §4.2); raw-deletion negative (cut 5) | `consolidate-family` (deletion) |
| G8 | raw-deletion negative, the deletion/history limit (cut 5) | `consolidate-family` (deletion) |
| G9 | the `url` locator arm beside H4's remote arm (cut 10 results §1) | `url-retrieval` |
| S1, S1a | the chain crossing corpora, resolvable only through the world index (cut 4 §4.2) | `world-resolution` |
| S5 | cross-corpus reach (cut 4 §4.2) → `world-resolution`; the deletion-surface transition and "never existed" clause (cut 4 §4.2) → `consolidate-family` | split as stated |
| S6 | arm (h), "the first successor policy admitting unequal weights" (cut 2 §4.2; cut 4 §5) | `weighted-belief` — tier 3 |
| W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15 | the world resolver over the write boundary and the index (cut 4 §5); W4 to be adjudicated against the merge retirement (address ruling §5) | `world-resolution` |
| W16 | the conflict surviving deletion of either producing run (cut 16 §2) | `consolidate-family` (deletion) |
| W9, W14 | rendered labels and the ambiguous-search refusal against a pinned authority snapshot (ledger artifact 11) | `authority-labels` — tier 3 |
| W17 | intent-position evidence over the publication-binding revision family (cut 14 results §1) | `publish`; the ordinary coordination revision family is closed |
| W13 | coverage-declaration and digest-invariance clauses; manifest-only re-mint detection and the forgery variants; replica-restore's declaration half; the fork copy act (cut 6 §3.2) — every named dependency has since landed → relabel candidates | `world-resolution`; the two-projects negative is closed by cut 14 |
| W8a | coreference omission-refutes and coverage arms → `world-resolution` (the `coreference-attestation` kind); certification omission-refutes → `contract-cut` (the `instrument-certification` kind); import-boundary and audit arms (cut 7 §3.2) → `packaging-remainder` | split as stated |
| R5 | negative (a), destroying the last held copy through a managed deletion recording an `absent` observation (cut 3 §4.2; holdings §3) — the intent-bearing delete act landed with cut 10 | `consolidate-family` (deletion) |
| R10 | "the acquisition path records dataset provenance instead" (cut 3 §4.2) | `url-retrieval` |
| R19 | explicit-import derivation validation over complete closure evidence; cross-corpus recomputation; contradiction discovery under audit; log-backed raw-write detection (cut 5) — every named dependency has landed | `run-boundary-remainder`, rides with `consolidate-family` (the import family dialect) |
| R22 | the unresolvable-interpretation-rule refusal → `contract-cut` (the rules store and resolver, 5b §6); explicit-import recomputation and the raw-written assessment under audit (cut 4 §4.2; cut 5) → `run-boundary-remainder` | split as stated |
| R23 | producer snapshots and receipts, coverage and cross-corpus divergence → `world-resolution`; deletion and audit clauses → `consolidate-family`; rules-store clauses → `contract-cut`. Replay cardinality, local basis/composition disagreement, and the move/consolidate clauses are closed by cuts 3, 15 and 16 respectively | split as stated |
| C3 | uncovered-corpus behavior and the coverage declaration over the global retraction map (cut 16 §2); the exact-state move clause is read | `correction-remainder` |
| C6 | raw-deletion negative (cut 5) | `consolidate-family` (deletion) |
| C7 | route-standing evaluator and conflict semantics; its consolidate prerequisite landed at cut 16 | `correction-remainder` — tier 1, after `consolidate-family` only in the serial mutation lane |
| C8, C9 | the stored semantic-snapshot kind, its evaluator and succession; world-index-backed digest enumeration; audit reporting; the mount negative on the managed holdings root (cut 5) | `correction-remainder` |
| C10 | `instrument-certification` eligibility → `contract-cut`; raw-written refused cases under audit → `correction-remainder` (cut 5) | split as stated |
| X2 | the persistence-cut arm at every stage, "a Science-side persistence-cut harness or an extension of the `atoms` A8 certification to this consumer path" (cut 7) → `persistence-cut`, tier 2; the interim best-effort-writer negative → limitation (lapsed) | as stated |
| X5 | admission arm read by cut 6, build arm by cut 7, neither relabeling (cut 7's X5 entry) → relabel | rides with `world-resolution` |
| X12 | `instrument-certification` membership → `contract-cut`; `coreference-attestation` membership → `world-resolution` (cut 7) | split as stated |
| N1, N3–N10 | the first contract cut, certification machinery, the adoption gate (cut 3 §5) | `contract-cut` |
| N2 | the doctrine over the rows no cut selects (cut 4 §4.2) — closes with the contract cut | `contract-cut` |
| L1, L4 | the partial units cuts 8 and 9 record in their row entries | `log-remainder`, rides with `event-level-l8` |
| L2 | u5's `register_root` arm, no Science mapping (cut 8 results §1.1) | limitation |
| L7 | u1's non-ancestor spelling (cut 8 results §1.1) → limitation; every other arm read by cuts 10–12 | limitation only — ranked nowhere |
| L8 | event-level cross-chain order (cut 11 §3.2) | `event-level-l8` |
| L10 | "no named cross-cut remainder … row label remains partial" (cut 10 results §1) → relabel | rides with `event-level-l8` |
| L13 | the preimage resolver over the `atoms` blob-read seam (cut 11 §3.2; log design §5.3) | `l13-preimage` — tier 2 |
| D1, D2, D4, D5, D8, D9, D10 | facets, manifests, practices, the registry compile (cut 3 §5) | `domain-boundary` |
| D3 | `not-present` and the five-way non-collapse over the world index (cut 2 §4.2) | `world-resolution` |
| D6 | the domain-facet derivation over the compiled registry (cut 2 §4.2) | `domain-boundary` |
| M1 | the instrumented resolver (cut 3 §5) | `formal-model-remainder` |
| M3 | coreference-attestation arm → `world-resolution`; raw-written-cycle classification under audit and the admission-order negative → `formal-model-remainder`; the concrete-cycle arms needing "a spellable controlled identity construction … a circular fixed point" (cut 5) → limitation unless a construction is found. The equal-basis replica arm is read by cut 16 | split as stated |
| M5 | the remainder cut 5's M5 entry states | `formal-model-remainder` |
| M12 | the extraction path (cut 3 §5; kernel limitation 3) | `extraction-path` — tier 3 |
| P1 | the resolver half of the negative, 5b §6's deterministic resolution (cut 4 §5) | `contract-cut` |
| H4 | the `url` / remote arm (cut 10 results §1) | `url-retrieval` |
| T1 | the import arm; the raw-write negative under audit and an anchored observer set (cut 5) — both landed | `act-report-remainder`, rides with `url-retrieval` |
| T2 | success for operation kinds other than `move` and `consolidate`; root-selection failure, second-fulfillment, missing-spec and non-conforming-execution clauses (cut 16 §2) | `act-report-remainder` |
| T4 | the coverage projection clause (built by cut 10) → relabel; the observation-deletion negative (cut 3 §4.2) | `act-report-remainder` |
| T5 | the acquisition operation's began-ness and preflight refusals (cut 3 §4.2) | `url-retrieval` |
| T7 | publish-together over an acquisition (cut 4 §5) → `url-retrieval`; the cross-root case → `cross-root-publication`, tier 3 | split as stated |

Two boundaries carry no guarantee row and enter on the ledger's own
statements: `nodes-remainder` (row 3: reserved-path contract, recoverable
construction, digest-id hazards) and `parity-fixture-2` (§3 item 8: the
second `science.identity.v1` fixture). A third, `verification-publication`,
enters the same way: cut 13 §2's own named exclusion, no guarantee row
naming it.

## Appendix C — limitations, ranked nowhere

Arms banked as unrun by design. The any-unrun-arm rule keeps their rows
`part`; nothing here is work.

| row | arm | banked by |
|---|---|---|
| L7 | u1's non-ancestor spelling — directory-unconstructible on a linear content-addressed chain | cut 8 results §1.1 |
| L2 | u5's `register_root` existing-chain arm — no Science mapping | cut 8 results §1.1 |
| X2 | the interim best-effort-writer negative — the writer was never built | cut 7, X2's entry (lapsed) |
| M3 | the concrete-cycle arms needing a circular fixed point in a controlled identity | cut 5, M3's entry — a limitation unless a construction is found |
