# Implementation roadmap — design

**Date:** 2026-08-29
**Status:** approved in session; revised 2026-08-29 across four written-spec review rounds
**Scope:** an ordered statement of the remaining implementation boundaries and
the discipline that keeps it current. It selects no cut scope, freezes no row,
and ranks no design question. The next cut's own design is a separate
brainstorming session.

**Inherits:** the current-state documentation curation design
(`2026-08-28-current-state-documentation-curation-design.md`), whose §2
split current-state authority by kind of fact and whose §7 deferred ranking to
this session; the adoption ledger's `Current state (2026-08-28)` section and
its guard, `test_the_ledger_summary_names_the_newest_remaining_boundary`.

## 1. Problem

The curation pass left one owner for what is built and what remains (the
ledger's `Current state` table) and one for what is undecided
(`open-questions.md`), and deliberately kept ordering out of both — the
ledger's rule 5. Nothing now says in what order the remainders are taken. The
last such statement was the ledger's §3 "order of work", which stopped being an
order around item 6 and became history.

Two smaller facts sharpen it. First, the ledger table is the *proven*
remainder, not the complete one: the curation's rule 4 kept out every
remainder the tree could not prove still open, and this session's adjudication
(§3) finds 89 open rows behind the table's four boundaries. Second, several
remainders have had a designed entry point for weeks — G4's
successor-admission obligations, consolidate/move/deletion, the URL retrieval
boundary, run confinement — with nothing recording that they are ready.

## 2. Decision

Write a dated, living roadmap at `docs/plans/2026-08-29-implementation-roadmap.md`
that ranks implementation boundaries in dependency tiers, orders within a tier
by what a boundary unblocks, and is recomputed — not accreted — whenever a cut
discharges. It ranks implementation boundaries only; design questions appear
solely as a row's blocker.

### 2.1 What the roadmap is

- **Home and lifecycle.** A plan-record under `docs/plans/`, beside the
  results and evidence records. Not a design: not swept into the README
  catalog or the guide-citation guard, and not amended with dated
  corrections. Its header carries `**Ranked at:** cut N, against the ledger's
  Current state (date)`. On re-ranking the whole document is recomputed; the
  previous ranking survives in git history only. A roadmap is a current claim,
  not a historical one, and the accretion the curation pass removed from
  design headers is not reintroduced here.
- **Two owners, one order.** The ledger's `Current state` table remains the
  authority for *what* is open; the roadmap is the authority for *in what
  order*. The two documents name the same set of boundaries, joined by stable
  ids (§3.5) and held equal by the guard (§6). `open-questions.md` remains
  the authority for what is undecided; the roadmap cites a design question
  only in a boundary's *blocked on* column, linking its anchor.
- **The edits to the guarded section.** The ledger's `Current state` table
  gains an `id` column and the rows §3.4 promotes, and its entry rule is
  restated to name the sources §3.1 admits. It gains exactly one sentence of
  prose — "Ordering over these rows lives in
  `../plans/2026-08-29-implementation-roadmap.md`." No ordering enters the
  ledger.

### 2.2 What it is not

It does not select cut scopes, freeze rows, or assign arms; a cut document does
that prospectively when its slice is drawn. It does not schedule `atoms` or
`nodes` work; it records cross-repo seams as prerequisites naming the owning
design. It carries no dates, estimates, or effort figures.

## 3. Adjudication

### 3.1 A row is open iff its live obligation has not been read in full

Guarantee rows close only through a conformance cut, and every cut records
which rows it read in full and in part (cut 1 §5; cuts 2 and 3 §4; cut 4 §4.1
and §4.2; cuts 5–7 their accounting tables; cuts 8–11 their results records
§1). A row's **historical** status is the highest it has reached across those
records — `full`, `part` at the last cut that read it, or `never` — under
the any-unrun-arm rule.

Historical status is not enough, because a row's obligation can widen after
a cut read it. G4 is the instance: cut 3 read it in full over the slice's
value state, the tamper-evident log and the intent boundary then widened what
G4 asserts, and cut 11 §3.2 and ledger row 5's dated note of 2026-08-28 name
it open at that width. So the rule is: a row's **live** status is its
historical status, overridden to open by the most recent cut document,
results record, or ledger row that names it as open or unread. The newest
results record's `Remaining boundary` and the ledger's row-level remainders
are the override sources; a row is closed only when no later source reopens
it.

At cut 11, 62 of 151 rows are closed and 89 open. The open rows, by table:

| table | never selected | part — remainder stated by the last cut that read it | reopened |
|---|---|---|---|
| G | G5 | G2c, G8 (cut 5); G3 (cut 2); G9 (cut 10) | G4 (full at cut 3; open per cut 11 §3.2) |
| S | — | S1, S1a, S5 (cut 4); S6 (cut 2) | — |
| W | W1, W2, W4, W5, W5a, W6, W7, W8, W8b, W9, W10, W11, W12, W14, W15, W16 | W13 (cut 9); W8a (cut 7) | — |
| R | R15 | R2, R4, R5, R9, R10, R12, R13, R16, R21 (cut 3); R19, R22, R23 (cut 4, restated cut 5); R20 (cut 5) | — |
| C | C7, C8, C9 | C3, C6, C10 (cut 5) | — |
| X | — | X2, X5, X12 (cut 7) | — |
| N | N1, N3–N10 | N2 (cut 4) | — |
| L | — | L1, L8, L13 (cut 8); L2, L4 (cut 9); L10 (cut 10); L7 (cut 11) | — |
| D | D1, D2, D4, D5, D8, D9, D10 | D3, D6, D7 (cut 2) | — |
| M | M1, M12 | M3, M5 (cut 5) | — |
| P | — | P1 (cut 2) | — |
| H | — | H4 (cut 10) | — |
| T | T7 | T1, T2 (cut 5); T4, T5 (cut 3) | — |

The delivery recomputes this table by script from the same sources and pins
the output in the roadmap's appendix.

### 3.2 A remainder is schedulable, a relabel, or a limitation

A stated remainder is one of three things. **Schedulable**: unrun arms whose
dependency has landed or is a boundary in §4 — assigned to that boundary.
**Relabel**: every arm has since run under some later cut without the row
being relabeled (cut 10 says this of L10 in so many words: "no named
cross-cut remainder … though this cut's row label remains partial") — the
next cut over that surface reads the row and relabels it, minting nothing
new. **Limitation**: an arm banked as unrun by design — L7 u1's directory-unconstructible non-ancestor
spelling, L2 u5's `register_root` arm with no Science mapping, X2's lapsed
best-effort-writer negative — listed in the appendix with the banking
section, ranked nowhere. The any-unrun-arm rule keeps such rows `part`
forever, correctly; the roadmap must not turn that honesty into phantom
work. A remainder whose banking section is not found is schedulable by
default — the error runs toward listing work, never toward hiding it.

### 3.3 Classification of every open row

Each open row, its remainder as the last cut states it, and where it goes.
"Rides with" names the tier-1 cut that takes a closure with no capability of
its own (§4.1).

| row | remainder (source) | classification → boundary |
|---|---|---|
| G4 | successor admission, the two-class blocker derivation, `admit_spec_successor` (intent-boundary §5; cut 11 §3.2) | `successor-admission` |
| G5 | "no such kind exists" checkable only at the registry compile (cut 4 §5) | rides with `domain-boundary` |
| G2c | the standing-retraction clause of "active" (cut 2 §4.2); raw-deletion negative (cut 5) | `consolidate-family` (deletion) |
| G8 | raw-deletion negative, the deletion/history limit (cut 5) | `consolidate-family` (deletion) |
| G3 | move an entity between corpora, digest unchanged (cut 2 §4.2; cut 4 §5) | `consolidate-family` (move) |
| G9 | the `url` locator arm beside H4's remote arm (cut 10 results §1) | `url-retrieval` |
| S1, S1a | the chain crossing corpora, resolvable only through the world index (cut 4 §4.2) | `world-resolution` |
| S5 | cross-corpus reach (cut 4 §4.2) → `world-resolution`; the deletion-surface transition and "never existed" clause (cut 4 §4.2) → `consolidate-family` | split as stated |
| S6 | arm (h), "the first successor policy admitting unequal weights" (cut 2 §4.2; cut 4 §5) | `weighted-belief` — tier 3 |
| W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15 | the world resolver over the write boundary and the index (cut 4 §5); W4 to be adjudicated against the merge retirement (address ruling §5) | `world-resolution` |
| W5, W16 | move and consolidate over stored records (cut 4 §5) | `consolidate-family` |
| W9, W14 | rendered labels and the ambiguous-search refusal against a pinned authority snapshot (ledger artifact 11) | `authority-labels` — tier 3 |
| W11, W12 | the project/coordination surface, "whether coordination records are minted through the corpus-write adapter at all is underdetermined" (cut 4 §5) | `coordination-addressing` — tier 3 |
| W13 | coverage-declaration and digest-invariance clauses; manifest-only re-mint detection and the forgery variants; replica-restore's declaration half; the fork copy act (cut 6 §3.2) — every named dependency has since landed → relabel candidates; the two-projects negative → `coordination-addressing` | `world-resolution`, less the two-projects negative |
| W8a | coreference omission-refutes and coverage arms → `world-resolution` (the `coreference-attestation` kind); certification omission-refutes → `contract-cut` (the `instrument-certification` kind); import-boundary and audit arms (cut 7 §3.2) → `packaging-remainder` | split as stated |
| R15 | the confinement-capable boundary policy (cut 3 §3, §5) | `run-confinement` |
| R4, R9, R13, R16, R21 | their `clean-environment` and confinement arms — R9's *admission does not follow* conjunct among them (cut 3 §4.2) | `run-confinement` |
| R5 | negative (a), destroying the last held copy through a managed deletion recording an `absent` observation (cut 3 §4.2; holdings §3) — the intent-bearing delete act landed with cut 10 | `consolidate-family` (deletion) |
| R2, R16, R20, R21 | their full-workflow-surface arms: trace/job-ID components, per-family obligations, the two-target arm (cut 3 §4.2; cut 5) | `workflow-surface` |
| R10 | "the acquisition path records dataset provenance instead" (cut 3 §4.2) | `url-retrieval` |
| R12 | the boundary-mediated strengthening, an intent entry as removal-detectable witness (cut 3 §4.2) — built by cut 11's intent-before-execution, unread → relabel | `successor-admission` |
| R19 | explicit-import derivation validation over complete closure evidence; cross-corpus recomputation; contradiction discovery under audit; log-backed raw-write detection (cut 5) — every named dependency has landed | `run-boundary-remainder`, rides with `consolidate-family` (the import family dialect) |
| R22 | the unresolvable-interpretation-rule refusal → `contract-cut` (the rules store and resolver, 5b §6); explicit-import recomputation and the raw-written assessment under audit (cut 4 §4.2; cut 5) → `run-boundary-remainder` | split as stated |
| R23 | the second dataset-production run → `workflow-surface`; producer snapshots and receipts, coverage, cross-corpus divergence → `world-resolution`; move/consolidate/deletion clauses → `consolidate-family`; rules-store clauses → `contract-cut` (cut 5) | split as stated |
| C3 | uncovered-corpus behavior and the coverage declaration over the global retraction map; exact-state receipts and move invariance (cut 5) | `correction-remainder`; the move clause with `consolidate-family` |
| C6 | raw-deletion negative (cut 5) | `consolidate-family` (deletion) |
| C7 | route-standing evaluator, conflict semantics, consolidate surface (cut 5) | `correction-remainder`, after `consolidate-family` |
| C8, C9 | the stored semantic-snapshot kind, its evaluator and succession; world-index-backed digest enumeration; audit reporting; the mount negative on the managed holdings root (cut 5) | `correction-remainder` |
| C10 | `instrument-certification` eligibility → `contract-cut`; raw-written refused cases under audit → `correction-remainder` (cut 5) | split as stated |
| X2 | the persistence-cut arm at every stage, "a Science-side persistence-cut harness or an extension of the `atoms` A8 certification to this consumer path" (cut 7) → `persistence-cut`, tier 2; the interim best-effort-writer negative → limitation (lapsed) | as stated |
| X5 | admission arm read by cut 6, build arm by cut 7, neither relabeling (cut 7's X5 entry) → relabel | rides with `world-resolution` |
| X12 | `instrument-certification` membership → `contract-cut`; `coreference-attestation` membership → `world-resolution` (cut 7) | split as stated |
| N1, N3–N10 | the first contract cut, certification machinery, the adoption gate (cut 3 §5) | `contract-cut` |
| N2 | the doctrine over the rows no cut selects (cut 4 §4.2) — closes with the contract cut | `contract-cut` |
| L1, L4 | the partial units cuts 8 and 9 record in their row entries | `log-remainder`, rides with `event-level-l8` |
| L2 | u5's `register_root` arm, no Science mapping (cut 8 results §1.1) | limitation |
| L7 | u1's non-ancestor spelling (cut 8 results §1.1) → limitation; every other arm read by cuts 10–11 → relabel | `successor-admission` |
| L8 | event-level cross-chain order (cut 11 §3.2) | `event-level-l8` |
| L10 | "no named cross-cut remainder … row label remains partial" (cut 10 results §1) → relabel | rides with `event-level-l8` |
| L13 | the preimage resolver over the `atoms` blob-read seam (cut 11 §3.2; log design §5.3) | `l13-preimage` — tier 2 |
| D1, D2, D4, D5, D8, D9, D10 | facets, manifests, practices, the registry compile (cut 3 §5) | `domain-boundary` |
| D3 | `not-present` and the five-way non-collapse over the world index (cut 2 §4.2) | `world-resolution` |
| D6 | the domain-facet derivation over the compiled registry (cut 2 §4.2) | `domain-boundary` |
| D7 | the W5-preservation move and both move refusals (cut 2 §4.2) | `consolidate-family` |
| M1 | the instrumented resolver (cut 3 §5) | `formal-model-remainder` |
| M3 | coreference-attestation arm → `world-resolution`; equal-basis replica arm → `consolidate-family`; raw-written-cycle classification under audit and the admission-order negative → `formal-model-remainder`; the concrete-cycle arms needing "a spellable controlled identity construction … a circular fixed point" (cut 5) → limitation unless a construction is found | split as stated |
| M5 | the remainder cut 5's M5 entry states | `formal-model-remainder` |
| M12 | the extraction path (cut 3 §5; kernel limitation 3) | `extraction-path` — tier 3 |
| P1 | the resolver half of the negative, 5b §6's deterministic resolution (cut 4 §5) | `contract-cut` |
| H4 | the `url` / remote arm (cut 10 results §1) | `url-retrieval` |
| T1 | the import arm; the raw-write negative under audit and an anchored observer set (cut 5) — both landed | `act-report-remainder`, rides with `url-retrieval` |
| T2 | root-selection failure at the root-selecting boundary; success for the other operation kinds; second-fulfillment classification over the durable-log consumer (cut 5) | `act-report-remainder` |
| T4 | the coverage projection clause (built by cut 10) → relabel; the observation-deletion negative (cut 3 §4.2) | `act-report-remainder` |
| T5 | the acquisition operation's began-ness and preflight refusals (cut 3 §4.2) | `url-retrieval` |
| T7 | publish-together over an acquisition (cut 4 §5) → `url-retrieval`; the cross-root case → `cross-root-publication`, tier 3 | split as stated |

Two boundaries carry no guarantee row and enter on the ledger's own
statements: `nodes-remainder` (row 3: reserved-path contract, recoverable
construction, digest-id hazards) and `parity-fixture-2` (§3 item 8: the
second `science.identity.v1` fixture).

### 3.4 Boundaries, and promotion into the ledger table

Rows are ranked as **boundaries**: the unit a cut is drawn against, each
owning the rows it closes. The ledger's `Current state` table lists every
boundary with a schedulable or relabel remainder, so it stays readable and
stays the authority for what is open. Its entry rule is restated from "only
when §1's rows prove it still open" to "only when a cut's accounting, a
results record, or §1's rows prove it still open". Beside the existing four
— `successor-admission`, `event-level-l8`, `l13-preimage`, `contract-cut` —
the delivery promotes:

`run-confinement`, `consolidate-family`, `url-retrieval`,
`world-resolution`, `domain-boundary`, `workflow-surface`,
`run-boundary-remainder`, `correction-remainder`, `formal-model-remainder`,
`packaging-remainder`, `log-remainder`, `act-report-remainder`,
`persistence-cut`, `parity-fixture-2`, `nodes-remainder`, `authority-labels`,
`coordination-addressing`, `weighted-belief`, `extraction-path`,
`cross-root-publication`.

Each row of the table names the boundary, its owner (the design whose rows
it closes, or the cross-repo design), and what it blocks, in the table's
existing format.

### 3.5 Stable ids

Every ledger-table boundary carries a short kebab-case id in the table's first
column, in backticks. The roadmap carries a `## Boundary index` table whose
first column is the same id set, and names boundaries by id everywhere else.
The guard (§6) asserts the two id sets are equal, so a boundary that leaves
the ledger cannot linger in the roadmap and one that enters cannot be
forgotten by it.

### 3.6 Excluded by construction

Design questions — artifact 11 (the pinned authority snapshot), ρO3, recency
as a projection rule, the extraction step (kernel limitation 3), the
act-report's cross-root publication residue, the coordination-record
question, the agentic surface, salvage — are never boundaries. They appear
only in a boundary's *blocked on* column, linking their `open-questions.md`
anchor. The coordination-record question has no anchor yet: cut 4 §5 and cut
6 §3.2 both name it and `open-questions.md` does not carry it, so the
delivery adds it as one bullet under *Identity, world, and change* — the
question exists in two frozen documents already; the guide is only catching
up.

## 4. The ranking

Dependency first, then breadth of what a boundary unblocks. A boundary is
**tier 1** when its entry point is designed and nothing outside the boundary's
own work must land first; **tier 2** when another boundary in this roadmap or
a cross-repo seam must land first; **tier 3** when a design question must be
answered first. A prerequisite that is the boundary's own work — an
instrumented resolver for M1, a confinement-capable policy for R15 — is not a
prerequisite.

### 4.1 Tier 1 — buildable now

Strict order. Row 1 is the next cut.

| # | id | rows | unblocks | placement |
|---|---|---|---|---|
| 1 | `successor-admission` | G4; R12's strengthening arm and L7's relabel, both read off the intent chain this cut qualifies | kernel §8.7's fourth recorded-mutation consequence — the kernel's invariant story closes; rows 5 and 7 read G4 in full | designed across nine readings with five opening obligations written (intent-boundary §5); Science-only; smallest of the tier |
| 2 | `run-confinement` | R15; R4, R9, R13, R16, R21's confinement arms | `clean-environment` becomes reachable, so a real verification can admit a real assessment to belief — the invariant operable end to end rather than over supplied values; every `clean-environment` arm in the R table | the confinement-capable boundary policy is computation §4.4b's, designed; cut 3 §3 states exactly what a scratch root is not |
| 3 | `workflow-surface` | R2, R16, R20, R21's workflow arms; R23's second-production arm | multi-rule, family, wildcard and definition-equality workflows — real analyses rather than fixture-held single-rule definitions | cut 3 §3 built "the minimal adapter only" and deferred every such arm to the full workflow surface, computation §6.4's, designed; with `run-confinement` it completes the execution boundary |
| 4 | `consolidate-family` | W5, W16; G3, D7; the deletion negatives of G2c, G8, C6, R5; S5's deletion half; R23 and C3's move clauses; M3's replica arm | C7's surface; the last mutation family; six rows' last arms | family-adapters design deferred it "to its own cut with the world index", which now exists |
| 5 | `url-retrieval` | H4, G9, R10, T5, T7's same-root case | the first acquisition of a dataset from outside the system; H4 in full | holdings design §2–§3 specify the canonicalization profile and network discipline |
| 6 | `world-resolution` | W1, W2, W4, W5a, W6, W7, W8, W8b, W10, W15; W13 (less one arm), W8a's coreference arms; S1, S1a, S5's cross-corpus reach; D3; X12 and M3's coreference arms; R23's snapshot clauses | the read side of the world: resolution states, cross-corpus edges, views, the coreference balance over the map cut 7 published | cut 4 §5 deferred the group on "the write boundary and the index" — both landed; the address ruling supplies the oracles. W11/W12 are not here (§3.3) |
| 7 | `domain-boundary` | D1, D2, D4, D5, D6, D8, D9, D10; G5 | the first domain pack; D8's composition | cut 3 §5 deferred the group on "facets, manifests, and the registry compile"; `ProfileSpec` and the `nodes` registry exist |
| 8 | `event-level-l8` | L8 | row 5 reads L8 in full; the log's last Science-only remainder | §7's ordered-cuts predicate is built; the event-level relation is its successor |
| 9 | `contract-cut` | N1, N3–N10, N2; P1; R22's resolver arm; W8a, X12 and C10's `instrument-certification` arms; R23's rules-store clauses | the widest set: the conformance-package split (ledger §5), instrument-certification cadence, legacy-check disposition (N10), P1 | last in the tier although it unblocks the most: N1 mints a successor contract identity for every oracle amended after the freeze, and rows 1–8 are Science-only closures that would each force one. Freeze after them |

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

### 4.2 Tier 2 — after a named prerequisite lands

| id | rows | prerequisite | unblocks |
|---|---|---|---|
| `correction-remainder` | C7; C8, C9; C3's coverage clauses; C10's audit arm | `consolidate-family` for C7; the stored semantic-snapshot kind and evaluator are the boundary's own work | the correction lifecycle in full |
| `l13-preimage` | L13 | an `atoms` blob-read seam behind its own design gate; `atoms`' deferred-obligation ledger carries no such entry today | row 5 in full; the held-copy match strengthened from path to bytes |
| `persistence-cut` | X2 | the `atoms` A8 certification extended to the publication path, behind `atoms`' own design gate. Cut 7 admits a Science-side harness as the alternative; it is rejected here (§5), so the prerequisite is cross-repo and the tier is 2 | X2 in full |
| `nodes-remainder` | — | `nodes`' own design gate | audits over damaged corpora; manifest safety |

### 4.3 Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| id | rows | blocked on |
|---|---|---|
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot |
| `coordination-addressing` | W11, W12; W13's two-projects negative | whether coordination records are minted through the corpus-write adapter (cut 4 §5; cut 6 §3.2) — the bullet §3.6 adds |
| `weighted-belief` | S6 (h) | ρO3, estimand typing — the first successor policy admitting unequal weights |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 |
| `cross-root-publication` | T7's cross-root case | the act-report's cross-root publication residue |

## 5. Alternatives rejected

- **A linear queue of numbered future cuts.** Fakes precision: it must place
  tier-3 rows whose order depends on unscheduled design work, and it goes
  stale the moment a scope shifts.
- **Goal tracks** ("first external installation", "first domain pack"). The
  same boundary appears under several goals, and cross-track ranking needs
  the dependency logic underneath anyway.
- **Ranking inside the ledger.** Rule 5 of the curation design exists to keep
  ordering out of the guarded summary; a ranking next to it would be an
  unguarded restatement of the guarded rows.
- **A banked design under `docs/designs/`.** Every re-ranking would be a dated
  amendment, which is the accretion the curation pass just removed.
- **A `proven`/`presumed` split.** The first draft ranked rows it could not
  prove open under a weaker label. The accounting proves every open row; the
  split hid that the ledger table was incomplete rather than fixing it.
- **Historical status alone.** The second draft closed G4 because cut 3 once
  read it in full. A row's obligation can widen after the cut that read it;
  the latest source wins.
- **Ranking rows rather than boundaries.** 89 rows in a ledger table is not a
  summary, and a cut is drawn against a boundary, not a row.
- **A one-directional guard.** Checking that every ledger id appears in the
  roadmap cannot see a discharged id left behind in it; set equality can.
- **A Science-side persistence-cut harness for X2.** Cut 7 allows it, but
  the corpus's rule is cut 4's: crash atomicity is the certified engine's
  property, relied on and never re-run, and ledger row 4 is the single
  authority for `atoms` implementation state. A second certifier in Science
  would re-run what the engine certifies and split that authority; the A8
  extension keeps one.
- **A guard on tier placement or order.** Those are judgment; a test asserting
  judgment is a restatement with an assert in front.

## 6. Verification

**Re-ranking trigger.** A cut's discharge. The commit adding a results record
re-ranks the roadmap in the same change: the discharged boundary leaves both
documents, any newly named remainder enters both, tier membership is
recomputed, and `Ranked at` advances. The contributor guide's "Maintaining
the guide" section gains one sentence naming this obligation.

**One guard, minimal.** `test_the_roadmap_and_ledger_name_the_same_boundaries`
in `python/tests/test_designs_corpus.py`:

1. reads the ledger's `Current state` section with the curation guard's
   `_h2_section` helper and collects every backticked id in the first column
   of its table rows, pattern `^\|\s*`([a-z0-9-]+)`\s*\|`, **as a list**,
   **failing if it collects none or if any id repeats**;
2. reads `docs/plans/2026-08-29-implementation-roadmap.md`, **failing if the
   file is absent**, takes its `Boundary index` section with the same helper,
   **failing if the section is absent**, and collects ids with the same
   pattern as a list, **failing if it collects none or if any id repeats**;
3. asserts the two id sets are **equal**, reporting both differences by
   name — after the uniqueness checks, so a duplicate cannot collapse into a
   passing set;
4. asserts the roadmap's `**Ranked at:**` line names `cut N` for the newest
   results record's N, selected as the curation guard selects it.

It joins on ids, never on prose, so rewording a boundary label breaks
nothing, and it refuses a duplicated id, so the ids stay usable as join keys. It reads two sections of two files and catches the drift this
document invites in both directions — a cut lands and the roadmap is
forgotten, or a boundary is discharged and lingers in it. It asserts nothing
about tiers or order.

**After editing:** `python/tools/check_guide.py`; `test_designs_corpus.py` and
`test_check_guide.py`; `git diff --check`; a diff review confirming only the
ledger, the guide index, `open-questions.md` (the one added bullet), the test
file, the new roadmap, and this design's status line changed.

## 7. Delivery

1. **Adjudicate.** Recompute §3.1's status table by script from the cut
   documents and results records, applying the live-width overrides, and pin
   the output in the roadmap's appendix beside §3.3's classification with its
   sources. Where the reading disagrees with §3.3, the source wins and the
   disagreement is recorded there.
2. **Promote.** Add the `id` column and §3.4's boundaries to the ledger's
   `Current state` table; restate the entry rule; add the one link sentence.
3. **Guard.** Add the test; watch it fail on the missing roadmap, then pass.
4. **Rank.** Write the roadmap with its `Boundary index`, §4's tiers under
   `Ranked at: cut 11`, every boundary by id, every prerequisite and blocker
   cited by document and section, the ride-along table, and the appendix.
5. **Maintain.** Add the maintenance sentence to `docs/guide/README.md` and
   the coordination-record bullet to `open-questions.md`; bump both `updated`
   dates.
6. **Gate.** Run the gates and the diff review.
7. **Close.** Correct this design's `**Status:**` line to record delivery in
   the same commit — a status header that says "approved" after the work
   lands is the drift the curation pass exists to prevent.
8. Commit as documentation-only work; the `--no-ff` merge into `main` is the
   human partner's.

The next cut — `successor-admission` — begins as its own brainstorming
session against the intent-boundary design's §5, and is not part of this
delivery.
