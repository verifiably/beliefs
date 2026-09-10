# Implementation roadmap

**Ranked at:** cut 24, against the ledger's Current state (2026-09-10), updated
2026-09-10
**Method:** `../superpowers/specs/2026-08-29-implementation-roadmap-design.md`,
as amended 2026-09-05 — tier 1 is ordered by distance to the dogfood success
criterion (§4.0 there), open lanes are bounded, and a method amendment
re-ranks without a new cut. **Re-ranked 2026-09-05 under the second trigger
by the mm30 reproduction record** (`../designs/2026-09-05-mm30-reproduction.md`),
which measured the three questions the previous ranking left provisional.
**Recomputed by:** the commit that adds each conformance-cut results record,
or that amends the method.
This document is a current claim: it is rewritten whole at every re-ranking,
carries no dated corrections, and the previous ranking survives only in git
history.

The adoption ledger's `Current state` table
(`../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-10`)
is the authority for *what* is open; this document is the authority for *in
what order*. The two name the same boundaries by id, and
`test_the_roadmap_and_ledger_name_the_same_boundaries` holds them to it.
Design questions are never rows here; they appear only as a boundary's
*blocked on*, linking `../guide/open-questions.md`.

Ranking is dependency first. A boundary is **tier 1** when its entry point is
designed and nothing outside its own work must land first; **tier 2** when
another boundary here or a cross-repo seam must land first; **tier 3** when a
design question must be answered first. A prerequisite that is the boundary's
own work — its slice design included — is not a prerequisite.

Within tier 1 the order is **distance to the success criterion** the user and
autonomy layer design §8 states
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`): a
coding-agent session over a `beliefs` world holding a reproduced mm30 corpus,
where `next` ranks a proposition, `run` executes a real analysis under
confinement, `verify` reaches `clean-environment`, and `assess` admits the
result to a computed belief, every step a governed record. Boundaries the
criterion cannot be met without are **on the path**, in dependency order;
the rest are **off the path**, in breadth order. Whether a boundary is on the
path is measured where it can be, by the reproduction lane (§Lanes).

**This ranking (2026-09-10) discharges world-resolution slice 2.** Cut 24
closes W15 and W4 and reads the coreference arms of X12, W8a and M3. The
governed attestation now reaches a populated, coverage-bound balance through
the ledgered session route. `world-resolution` stays first on the path: source
re-addressing in slice 2b, the snapshot/import and audit callers, and view
evaluation remain. Its packaging ride-along is unchanged. W8b was measured,
repaired by `beliefs-fda0e5`, and not selected; a future cut must select it
before its conformance row can close.

The current accounting is 144 of 195 rows closed, with 51 open. The prior
single-corpus mm30 measurement still ranks this boundary on the path when a
second corpus enters; cut 24 adds coreference acceptance fixtures, not another
mm30 reproduction measurement. `domain-boundary` retains D1's cross-repository
negative. The remaining slices under `beliefs-d248ba` are source re-addressing
(`beliefs-b7994b`), snapshots/import/audit (`beliefs-46847c`), and view
evaluation (`beliefs-0e523a`), delivered serially in that order.

## Boundary index

Every boundary the ledger table lists, by id. This section is the guard's
join key and nothing else; the tiers below carry the ranking.

| id | rows it closes | tier |
|---|---|---|
| `domain-boundary` | D1's cross-repository negative | 2 |
| `world-resolution` | W1, W2 and W5a in slice 2b; W7, W8 and W8b; W13 less its two-projects negative; R23's snapshot, divergence and explicit-import clauses | 1, on the path |
| `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | 1, off the path |
| `url-retrieval` | H4, G9, R10, T5; T7's same-root case | 1, off the path |
| `event-level-l8` | L8 | 1, off the path |
| `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12, C10's certification arms; R23's rules-store clauses | 1, the join |
| `packaging-remainder` | X5 (relabel); W8a's import and audit arms | 1, rides with `world-resolution` |
| `act-report-remainder` | T1, T2, T4 | 1, rides with `url-retrieval` |
| `log-remainder` | L1, L4; L10 (relabel) | 1, rides with `event-level-l8` |
| `l13-preimage` | L13 | 2 |
| `persistence-cut` | X2 | 2 |
| `nodes-remainder` | `nodes` row 3's three items | 2 |
| `authority-labels` | W9, W14 | 3 |
| `weighted-belief` | S6 (h) | 3 |
| `extraction-path` | M12 | 3 |
| `cross-root-publication` | T7's cross-root case | 3 |

## Tier 1 — buildable now

### On the path

In dependency order. A boundary's rank says how far the success criterion is
from being met without it; its lane (§Lanes) says what it must wait for.

| # | id | rows | unblocks | placement |
|---|---|---|---|---|
| 1 | `world-resolution` | W1, W2 and W5a in slice 2b; W7, W8 and W8b; W13 less its two-projects negative; R23's snapshot, divergence and explicit-import clauses | source re-addressing; snapshot/import and audit callers; W7 view evaluation for `next` and `publish` | slices 1 and 2 discharged at cuts 23 and 24; slice 2b (`beliefs-b7994b`) is next. W8b is repaired by `beliefs-fda0e5` but remains unselected |

### Off the path

In breadth order. Each opens only when no on-path lane is startable
(§Concurrency rules, rule 6).

| # | id | rows | unblocks | placement |
|---|---|---|---|---|
| 2 | `correction-remainder` | C7, C8, C9; C3's coverage clauses; C10's audit arm | the correction lifecycle in full | C7's consolidate prerequisite landed at cut 16 and the deletion surface it shares at cut 18; the stored semantic-snapshot kind and evaluator are this boundary's own work. Off the path: the first belief retracts nothing |
| 3 | `url-retrieval` | H4, G9, R10, T5, T7's same-root case | the first acquisition of a dataset from outside the system; H4 in full | holdings design §2–§3 specify the canonicalization profile and network discipline. Off the path: mm30's data is held locally, so the first belief acquires nothing |
| 4 | `event-level-l8` | L8 | row 5 reads L8 in full; the log's last Science-only remainder | §7's ordered-cuts predicate is built; the event-level relation is its successor |
| 5 | `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12 and C10's `instrument-certification` arms; R23's rules-store clauses | the widest set: the conformance-package split (ledger §5), instrument-certification cadence, legacy-check disposition (N10), P1 | the join, last: N1 mints a successor contract identity for every oracle amended after the freeze, every lane above amends at least one, and the ledger's §2 already rules that the contract freezes after the operation set settles — which the dogfood will change |

**Ride-along closures**, tier 1 by the rule and unblocking no capability of
their own, each named to the cut that takes it:

| id | rows | rides with |
|---|---|---|
| `packaging-remainder` | X5 (relabel); W8a's import and audit arms | `world-resolution` |
| `act-report-remainder` | T1, T2, T4 | `url-retrieval` — the acquisition operation is the first new operation kind T2 needs |
| `log-remainder` | L1, L4; L10 (relabel) | `event-level-l8` |

A ride-along is named in the cut that takes it and never stands alone.

## Lanes — what may run concurrently

A **lane** is a set of boundaries that share a code surface and therefore
land serially; two lanes share no surface they both rewrite and may run at
the same time. Lanes are dependency- and surface-based, never goal-based; the
one goal above orders tier 1 and does not define a lane. The ranking still
holds within a lane, and tier membership is unchanged by lanes: a tier-2
boundary sits in the lane of its prerequisite and waits there.

| lane | boundaries, in order | shared surface | status |
|---|---|---|---|
| `write-path` | none — no open boundary | `corpus.py`, `report.py`, `intents/`, `session/`, `verify.py`, `evaluation.py`, `audit.py` | closed: `writer-session` discharged at cut 19 and `verification-publication` at cut 21 |
| `domain` | `domain-boundary` D1 cross-repository negative; slices 1 and 2 discharged at cuts 20 and 22 | the `nodes` registry | waits on the cross-repository seam |
| `world-read` | `world-resolution` slices 2b–4 (+ `packaging-remainder`) → `event-level-l8` (+ `log-remainder`) | `world/read.py`, `world/view.py`, `resolution.py`, `world/verify.py`; `corpus.py`, `lineage.py`, `evaluation.py`, `belief.py`, `consulted.py`, `audit.py` as each slice names | on the path at its head; slices 1 and 2 discharged at cuts 23 and 24, slice 2b next |
| `mutation` | `correction-remainder` | `adapter.py`, `corpus.py`, `audit.py`, `decode.py`, `evaluation.py`, `world/verify.py` | off the path; waits |
| `acquisition` | `url-retrieval` (+ `act-report-remainder`) | `holdings/`, `report.py` | off the path; waits |
| `reproduction` | none — a measurement: `../superpowers/specs/2026-09-05-mm30-reproduction-design.md` | no kernel surface; `python/tools/reproduction/`, a corpus on the certified volume beside the checkout, and the record it produces | **closed 2026-09-05**: ran to the evaluator's answer; its record (`../designs/2026-09-05-mm30-reproduction.md`) re-ranked this document, its five findings are filed through the owning lanes, and its corpus stays at `.mm30-reproduction/` as the seed of the dogfood's world |
| `cross-repo` | `l13-preimage`, `persistence-cut`, `nodes-remainder`, in any order | the `atoms` and `nodes` repositories, each behind its own design gate | as each seam lands |

`contract-cut` is in no lane. It is a **join**: it freezes after every lane
that amends an oracle has merged, for the reason tier 1's row 5 gives. Tier 3
boundaries are in no lane either; a design answer moves one into the lane of
the surface it lands on.

### Concurrency rules

Every rule the corpus already has stays in force when lanes run at once —
a cut is frozen before its code exists, discharged on the certified volume,
and merged `--no-ff`. Six rules are added by concurrency itself:

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
6. **At most two kernel lanes are open at once while the success criterion
   is unmet, both on the path**, beside the reproduction lane. An off-path
   lane opens only when no on-path lane is startable. The reproduction lane
   rewrites no kernel surface and is not counted; a finding it produces
   lands as a design amendment or an `open-questions.md` entry through the
   lane that owns the surface, never as a direct edit from the reproduction
   worktree.

## Tier 2 — after a named prerequisite lands

| id | rows | prerequisite | unblocks |
|---|---|---|---|
| `domain-boundary` | D1 | `nodes`' own design gate for the cross-repository negative | D1 in full |
| `l13-preimage` | L13 | an `atoms` blob-read seam behind its own design gate; `atoms`' deferred-obligation ledger carries no such entry today | row 6 in full; the held-copy match strengthened from path to bytes |
| `persistence-cut` | X2 | the `atoms` A8 certification extended to the publication path, behind `atoms`' own design gate. Cut 7 admits a Science-side harness as the alternative; it is rejected by the method (§5 there), so the prerequisite is cross-repo and the tier is 2 | X2 in full |
| `nodes-remainder` | — | `nodes`' own design gate | audits over damaged corpora; manifest safety |

## Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| id | rows | blocked on |
|---|---|---|
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot — [which external authorities are accepted](../guide/open-questions.md#identity-world-and-change) |
| `weighted-belief` | S6 (h) | ρO3, estimand typing — [weighted belief](../guide/open-questions.md#claims-and-belief) |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 — [higher-order records and extraction](../guide/open-questions.md#claims-and-belief) |
| `cross-root-publication` | T7's cross-root case | [the act-report's residue](../guide/open-questions.md#contracts-and-adoption) |

One design question the success criterion meets on its first day is not a row
and is carried by the lane that owns its surface: where a typed claim is authored
for a corpus that has none — distinct from the extraction step M12 names — answered by the
reproduction record's §5 (what it cost, what `build_claim` refused, what a
`claim` command must do and refuse), which is the input to the layer design's
sub-project 4. The empirical-observation payload question closed in domain
slice 1 (facet-contracts §6). Another question raised by the record is carried by no lane yet:
where an interpretation rule reads content
([computation](../guide/open-questions.md#computation-and-reproducibility)).

## Appendix A — live status of every guarantee row at cut 24

Produced by `python/tools/roadmap_status.py` from the cuts' own accounting
(spec §3.1); a row is closed only when no later source reopens it. Cut 24
closes W15 and W4 and leaves X12, W8a and M3 partial. W8b remains never
selected despite its repaired measured defect; measurement is not selection.

| table | never selected | part — last cut that read it | reopened |
|---|---|---|---|
| G | — | G9 (cut 10) | — |
| S | — | S6 (cut 2) | — |
| W | W1, W2, W7, W8, W9, W14, W5a, W8b | W13 (cut 14), W17 (cut 14), W8a (cut 24) | — |
| R | — | R10 (cut 3), R22 (cut 18), R23 (cut 23) | — |
| C | C7, C8, C9 | C3 (cut 16), C10 (cut 5) | — |
| X | — | X2 (cut 7), X5 (cut 7), X12 (cut 24) | — |
| N | N1, N3, N4, N5, N6, N7, N8, N9, N10 | N2 (cut 4) | — |
| L | — | L1 (cut 8), L2 (cut 9), L4 (cut 9), L7 (cut 12), L8 (cut 8), L10 (cut 10), L13 (cut 8) | — |
| D | — | D1 (cut 22) | — |
| M | M12 | M3 (cut 24) | — |
| P | — | P1 (cut 2) | — |
| H | — | H4 (cut 10) | — |
| T | T7 | T1 (cut 5), T2 (cut 16), T4 (cut 3), T5 (cut 3) | — |
| E | — | — | — |
| F | — | — | — |
| J | — | — | — |
| V | — | — | — |
| B | — | — | — |

Closed 144 of 195; open 51.

## Appendix B — classification of every open row

Each open row, its remainder as the last cut states it, and where it goes
(spec §3.2's three classes: schedulable, relabel, limitation).

| row | remainder (source) | classification → boundary |
|---|---|---|
| G9 | the `url` locator arm beside H4's remote arm (cut 10 results §1) | `url-retrieval` |
| S6 | arm (h), "the first successor policy admitting unequal weights" (cut 2 §4.2; cut 4 §5) | `weighted-belief` — tier 3 |
| W1, W2, W5a | source addresses derived from the normalized external identifier (cut 24 results §5) | `world-resolution` slice 2b, `beliefs-b7994b` |
| W7, W8 | the remaining world resolver and view evaluation (cut 24 results §5) | `world-resolution` |
| W8b | measured but not selected; `beliefs-fda0e5` repaired the measured build defect with distinct `uid-corruption` and `duplicate-location` findings on refusal. Conformance selection remains open | `world-resolution` |
| W9, W14 | rendered labels and the ambiguous-search refusal against a pinned authority snapshot (ledger artifact 11) | `authority-labels` — tier 3 |
| W17 | intent-position evidence over the publication-binding revision family (cut 14 results §1) | `publish`; the ordinary coordination revision family is closed |
| W13 | coverage-declaration and digest-invariance clauses; manifest-only re-mint detection and the forgery variants; replica-restore's declaration half; the fork copy act (cut 6 §3.2) — every named dependency has since landed → relabel candidates | `world-resolution`; the two-projects negative is closed by cut 14 |
| W8a | the coreference omission-refutes and coverage arms are read at cut 24; certification omission-refutes → `contract-cut` (the `instrument-certification` kind); import-boundary and audit arms (cut 7 §3.2) → `packaging-remainder` | split as stated |
| R10 | "the acquisition path records dataset provenance instead" (cut 3 §4.2) | `url-retrieval` |
| R22 | the unresolvable-interpretation-rule refusal → `contract-cut` (the rules store and resolver, 5b §6); the explicit-import recomputation and raw-written-under-audit arms are closed by cut 18 | `contract-cut` |
| R23 | producer snapshots and receipts, cross-corpus divergence and explicit-import clauses → `world-resolution`; rules-store clauses → `contract-cut`. Cut 23 closes the coverage clause; replay cardinality, local basis/composition disagreement, move/consolidate, deletion and audit clauses retain their prior closure | split as stated |
| C3 | uncovered-corpus behavior and the coverage declaration over the global retraction map (cut 16 §2); the exact-state move clause is read | `correction-remainder` |
| C7 | route-standing evaluator and conflict semantics; its consolidate prerequisite landed at cut 16 | `correction-remainder` |
| C8, C9 | the stored semantic-snapshot kind, its evaluator and succession; world-index-backed digest enumeration; audit reporting; the mount negative on the managed holdings root (cut 5) | `correction-remainder` |
| C10 | `instrument-certification` eligibility → `contract-cut`; raw-written refused cases under audit → `correction-remainder` (cut 5) | split as stated |
| X2 | the persistence-cut arm at every stage, "a Science-side persistence-cut harness or an extension of the `atoms` A8 certification to this consumer path" (cut 7) → `persistence-cut`, tier 2; the interim best-effort-writer negative → limitation (lapsed) | as stated |
| X5 | admission arm read by cut 6, build arm by cut 7, neither relabeling (cut 7's X5 entry) → relabel | rides with `world-resolution` |
| X12 | the `coreference-attestation` membership and omission-refutes arms are read at cut 24; `instrument-certification` membership and omission-refutes → `contract-cut` | `contract-cut` |
| N1, N3–N10 | the first contract cut, certification machinery, the adoption gate (cut 3 §5) | `contract-cut` |
| N2 | the doctrine over the rows no cut selects (cut 4 §4.2) — closes with the contract cut | `contract-cut` |
| L1, L4 | the partial units cuts 8 and 9 record in their row entries | `log-remainder`, rides with `event-level-l8` |
| L2 | u5's `register_root` arm, no Science mapping (cut 8 results §1.1) | limitation |
| L7 | u1's non-ancestor spelling (cut 8 results §1.1) → limitation; every other arm read by cuts 10–12 | limitation only — ranked nowhere |
| L8 | event-level cross-chain order (cut 11 §3.2) | `event-level-l8` |
| L10 | "no named cross-cut remainder … row label remains partial" (cut 10 results §1) → relabel | rides with `event-level-l8` |
| L13 | the preimage resolver over the `atoms` blob-read seam (cut 11 §3.2; log design §5.3); cut 18 closes nothing here — removal classification stays a path match | `l13-preimage` — tier 2 |
| D1 | the cross-repository negative that adds a domain-aware code path to `nodes` (cut 22 §2) | `domain-boundary` |
| M3 | the coreference-attestation arm is read at cut 24; the concrete-cycle arms needing "a spellable controlled identity construction … a circular fixed point" (cut 5) remain a limitation unless a construction is found. The equal-basis replica arm is read by cut 16; the raw-written-cycle classification and admission-order negative are closed by cut 18 | limitation only — ranked nowhere |
| M12 | the extraction path (cut 3 §5; kernel limitation 3) | `extraction-path` — tier 3 |
| P1 | the resolver half of the negative, 5b §6's deterministic resolution (cut 4 §5) | `contract-cut` |
| H4 | the `url` / remote arm (cut 10 results §1) | `url-retrieval` |
| T1 | the import arm; the raw-write negative under audit and an anchored observer set (cut 5) — both landed | `act-report-remainder`, rides with `url-retrieval` |
| T2 | success for operation kinds other than `move` and `consolidate`; root-selection failure, second-fulfillment, missing-spec and non-conforming-execution clauses (cut 16 §2); `delete` contributes no arm, opening no operation and minting no report (cut 18 §4) | `act-report-remainder` |
| T4 | the coverage projection clause (built by cut 10) → relabel; the observation-deletion negative (cut 3 §4.2) | `act-report-remainder` |
| T5 | the acquisition operation's began-ness and preflight refusals (cut 3 §4.2) | `url-retrieval` |
| T7 | publish-together over an acquisition (cut 4 §5) → `url-retrieval`; the cross-root case → `cross-root-publication`, tier 3 | split as stated |

One boundary carries no guarantee row and enters on the ledger's own
statements: `nodes-remainder` (row 3: reserved-path contract, recoverable
construction, digest-id hazards). Two others did and are gone:
`writer-session`, which carried J1–J11 and left when cut 19 closed every row
of it, and `verification-publication`, which entered on cut 13 §2's own named
exclusion, acquired the `V` table at its freeze, and left when cut 21 closed
all eight.

## Appendix C — limitations, ranked nowhere

Arms banked as unrun by design, and the scope bounds a row carries in its own
text. R19's scope-recomputation entry left this table at cut 21, which gave a
stored verification the comparison report it lacked. The any-unrun-arm rule keeps the affected rows `part` — except where the
bound is written into the row itself, as M1's resolver bound is, and the row
closes carrying it. Nothing here is work.

| row | arm | banked by |
|---|---|---|
| L7 | u1's non-ancestor spelling — directory-unconstructible on a linear content-addressed chain | cut 8 results §1.1 |
| L2 | u5's `register_root` existing-chain arm — no Science mapping | cut 8 results §1.1 |
| X2 | the interim best-effort-writer negative — the writer was never built | cut 7, X2's entry (lapsed) |
| M3 | the concrete-cycle arms needing a circular fixed point in a controlled identity | cut 5, M3's entry — a limitation unless a construction is found |
| M1 | the resolver bound — a read that never crosses the instrumented resolver (a module constant, an environment lookup, a cached global, a file opened directly) is invisible and passes, so M1 does not assert that every undeclared read is detected | cut 18 §7, preserving M1's own scope clause; lifting it needs an exhaustive capability or sandbox boundary the formal model does not propose |
