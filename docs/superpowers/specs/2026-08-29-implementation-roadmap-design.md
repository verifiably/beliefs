# Implementation roadmap — design

**Date:** 2026-08-29
**Status:** approved in session; revised 2026-08-29 after written-spec review
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
(§3) finds the complete one is roughly three times larger. Second, several
remainders have had a designed entry point for weeks — G4's
successor-admission obligations, consolidate/move/deletion, the URL retrieval
boundary — with nothing recording that they are ready.

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
  order*. Every boundary the roadmap ranks is a row of the ledger table,
  joined by a stable id (§3.4). `open-questions.md` remains the authority for
  what is undecided; the roadmap cites a design question only in a row's
  *blocked on* column, linking its anchor.
- **The edits to the guarded section.** The ledger's `Current state` table
  gains an `id` column and the rows §3.3 promotes, and its entry rule is
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

### 3.1 A row is open iff no cut has read it in full

Guarantee rows close only through a conformance cut, and every cut records
which rows it read in full and in part (cut 1 §5; cuts 2 and 3 §4; cut 4 §4.1
and §4.2; cuts 5–7 their accounting tables; cuts 8–11 their results records
§1). A row's status is the highest it has reached across those records —
`full`, `part` at the last cut that read it, or `never` — under the
any-unrun-arm rule: a cut that reads some of a row's arms leaves it `part`,
and no later cut relabels a row it did not read. So the open remainder is
mechanical, and every open row is proven open by the accounting itself. There
is no "presumed" category.

At cut 11, 63 of 151 rows are closed. The open 88, by table:

| table | never selected | part — remainder stated by the last cut that read it |
|---|---|---|
| G | G5 | G2c, G8 (cut 5); G3 (cut 2); G9 (cut 10) |
| S | — | S1, S1a, S5 (cut 4); S6 (cut 2) |
| W | W1, W2, W4, W5, W5a, W6, W7, W8, W8b, W9, W10, W11, W12, W14, W15, W16 | W13 (cut 9); W8a (cut 7) |
| R | R15 | R2, R4, R10, R12, R13, R16, R21 (cut 3); R19, R22, R23 (cut 4); R20 (cut 5) |
| C | C7, C8, C9 | C3, C6, C10 (cut 5) |
| X | — | X2, X5, X12 (cut 7) |
| N | N1, N3, N4, N5, N6, N7, N8, N9, N10 | N2 (cut 4) |
| L | — | L1, L8, L13 (cut 8); L2, L4 (cut 9); L10 (cut 10); L7 (cut 11) |
| D | D1, D2, D4, D5, D8, D9, D10 | D3, D6, D7 (cut 2) |
| M | M1, M12 | M3, M5 (cut 5) |
| P | — | P1 (cut 2) |
| H | — | H4 (cut 10) |
| T | T7 | T1, T2 (cut 5); T4, T5 (cut 3) |

Two kinds of source prove what remains of an open row. A `never` row's
deferral is stated, with its unblocking dependency, by the most recent cut
that grouped it (cut 4 §5 for the W group; cut 3 §5 for the rest; cut 5's
deferred rows for C7–C9 and R19/R22/R23). A `part` row's remainder is stated
in the last cut that read it, in that row's own entry. The delivery's first
step (§7) reads each of the 88 and records, per row, the remainder and its
source in the roadmap's appendix.

### 3.2 A remainder is schedulable or it is a limitation

Some stated remainders are not work. A row read in part because one arm is
*banked as unrun by design* — G2a's out-of-band negative that "stands",
R12's chronology limit, L7 u8's surviving-observer bound — carries a
limitation, not a boundary. The any-unrun-arm rule keeps such a row `part`
forever, correctly, so coverage is never overstated; the roadmap must not
turn that honesty into phantom work. The adjudication classifies each open
row's remainder as **schedulable** (assigned to a boundary in §4) or
**limitation** (listed in the appendix with the design section that banks
it, ranked nowhere). A remainder whose design section is not found is
schedulable by default — the error runs toward listing work, never toward
hiding it.

### 3.3 Boundaries, and promotion into the ledger table

Rows are ranked as **boundaries**: the unit a cut is drawn against, each
owning the rows it closes. The ledger's `Current state` table lists every
boundary with a schedulable remainder — not the 88 rows — so the table stays
readable and stays the authority for what is open. Its entry rule is restated
from "only when §1's rows prove it still open" to "only when a cut's
accounting, a results record, or §1's rows prove it still open". The
delivery promotes these boundaries beside the four already there:

| id | boundary | rows |
|---|---|---|
| `consolidate-family` | consolidate, move/rename, deletion — the last mutation family | W5, W16, G3's move arm, D7's W5-preservation arm, C7's consolidate surface |
| `correction-remainder` | the correction lifecycle's remainder | C7, C8, C9; C3, C6, C10 completion |
| `url-retrieval` | the URL retrieval boundary, acquisition orchestration, typed retrieval grants | H4's remote arm; T7's same-root case |
| `world-resolution` | the read side of the world: resolution states, views, cross-corpus edges, coreference balance | W1, W2, W4, W6, W7, W8, W8b, W10, W11, W12, W15, W5a; W13 and W8a completion |
| `domain-boundary` | facets, manifests, practices, the compiled registry | D1, D2, D4, D5, D8, D9, D10; D3, D6, D7 completion |
| `run-boundary-remainder` | confinement and explicit-import derivation | R15; R19, R22, R23; the schedulable arms of R2, R4, R10, R13, R16, R20, R21 |
| `formal-model-remainder` | the instrumented resolver; retraction graphs | M1; M3's unselected clauses; M5 completion |
| `substrate-remainder` | relation and lineage closure fixtures; eligibility at both boundaries | S1, S1a, S5, S6; G2c, G8, G9 completion |
| `packaging-remainder` | the persistence-cut publication arm; certification and coreference membership | X2, X5, X12 completion |
| `log-remainder` | the log rows' partial units outside L8 and L13 | L1, L2, L4, L10, L7 completion |
| `act-report-remainder` | the report layer's partial arms | T1, T2, T4, T5 completion |
| `authority-labels` | rendered labels, ambiguous-search refusal, renderer invariance | W9, W14 |
| `extraction-path` | the untypeable span end to end | M12 |
| `nodes-remainder` | reserved-path contract, recoverable construction, digest-id hazards | ledger row 3 (no science row) |
| `parity-fixture-2` | the second `science.identity.v1` parity fixture | formal model §8 (no row) |

with the existing four carrying ids `successor-admission` (G4),
`event-level-l8` (L8), `l13-preimage` (L13), and `contract-cut` (N1, N3–N10;
N2 completion; P1's resolver-negative arm). Where the first-step reading finds
a `part` row's whole remainder is a limitation, that row leaves its boundary;
a boundary left with no rows leaves the table.

### 3.4 Stable ids

Every ledger-table boundary carries a short kebab-case id in the table's first
column, in backticks. The roadmap names boundaries by that id and nothing
else, so the guard (§6) joins the two documents on ids rather than on prose
labels that drift the first time one is reworded.

### 3.5 Excluded by construction

Design questions — artifact 11 (the pinned authority snapshot), ρO3, recency
as a projection rule, the extraction step (kernel limitation 3), the
act-report's cross-root publication residue, the agentic surface, salvage —
are never rows. They appear only in a boundary's *blocked on* column, linking
their `open-questions.md` anchor.

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

| # | id | unblocks | placement |
|---|---|---|---|
| 1 | `successor-admission` | kernel §8.7's fourth recorded-mutation consequence — the kernel's invariant story closes; rows 5 and 7 read G4 in full | designed across nine readings with five opening obligations written (intent-boundary design §5); Science-only; smallest of the tier |
| 2 | `consolidate-family` | `correction-remainder`'s C7 surface; G3 and D7 in full; the family-adapter set complete | family-adapters design deferred it "to its own cut with the world index", which now exists |
| 3 | `url-retrieval` | H4 in full; T7's same-root case; the first acquisition of a dataset from outside the system | holdings design §2–§3 specify the canonicalization profile and network discipline |
| 4 | `world-resolution` | the read side of the world; W15's coreference balance over the map cut 7 published | cut 4 §5 deferred the group on "the write boundary and the index" — both landed; the address ruling supplies the oracles |
| 5 | `domain-boundary` | the first domain pack; D8's composition | cut 3 §5 deferred the group on "facets, manifests, and the registry compile"; `ProfileSpec` and the `nodes` registry exist |
| 6 | `event-level-l8` | row 5 reads L8 in full; the log's last Science-only remainder | §7's ordered-cuts predicate is built; the event-level relation is its successor |
| 7 | `contract-cut` | the widest set: the conformance-package split (ledger §5), instrument-certification cadence, legacy-check disposition (N10), P1 | last in the tier although it unblocks the most: N1 mints a successor contract identity for every oracle amended after the freeze, and rows 1–6 are Science-only closures that would each force one. Freeze after them |

`run-boundary-remainder`, `formal-model-remainder`, `substrate-remainder`,
`packaging-remainder`, `log-remainder`, `act-report-remainder` and
`parity-fixture-2` are tier 1 by the rule and unblock no capability of their
own; they are **ride-along closures**, each attached to the tier-1 cut whose
surface it touches and taken with it: `substrate-remainder` and
`formal-model-remainder` with `consolidate-family` (both concern the
retraction and move surfaces); `act-report-remainder` and
`packaging-remainder`'s X2 arm with `url-retrieval`; `log-remainder` with
`event-level-l8`; `run-boundary-remainder`'s confinement with whichever cut
next opens the execution boundary, and its explicit-import arms with
`consolidate-family`; `parity-fixture-2` with the first cut that touches
`science.identity.v1`. A ride-along is named in the cut that takes it and
never stands alone as a cut.

### 4.2 Tier 2 — after a named prerequisite lands

Ordered only where dependency forces it.

| id | prerequisite | unblocks |
|---|---|---|
| `correction-remainder` | `consolidate-family` for C7; a stored semantic-snapshot kind and evaluator for C8–C9 — the correction lifecycle design's own remainder, with `world-resolution` supplying the digest enumeration C9 names | the correction lifecycle in full |
| `l13-preimage` | an `atoms` blob-read seam behind its own design gate; `atoms`' deferred-obligation ledger carries no such entry today | row 5 in full; the held-copy match strengthened from path to bytes |
| `packaging-remainder`'s X12 membership arms | the `instrument-certification` kind from `contract-cut`; the `coreference-attestation` kind from `world-resolution` | X12 in full |
| `nodes-remainder` | `nodes`' own design gate | audits over damaged corpora; manifest safety |

### 4.3 Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| id | rows | blocked on |
|---|---|---|
| `authority-labels` | W9, W14 | artifact 11, the pinned authority snapshot |
| `extraction-path` | M12 | the extraction step, kernel limitation 3 |
| `url-retrieval`'s cross-root T7 arm | T7 | the act-report's cross-root publication residue |

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
- **Ranking rows rather than boundaries.** 88 rows in a ledger table is not a
  summary, and a cut is drawn against a boundary, not a row.
- **A guard on tier placement or order.** Those are judgment; a test asserting
  judgment is a restatement with an assert in front.

## 6. Verification

**Re-ranking trigger.** A cut's discharge. The commit adding a results record
re-ranks the roadmap in the same change: the discharged boundary leaves, any
newly named remainder enters (the ledger table under its guard, then the
roadmap), tier membership is recomputed, and `Ranked at` advances. The
contributor guide's "Maintaining the guide" section gains one sentence naming
this obligation.

**One guard, minimal.** `test_the_roadmap_ranks_every_ledger_boundary` in
`python/tests/test_designs_corpus.py`:

1. reads the ledger's `Current state` section with the curation guard's
   `_h2_section` helper and collects every backticked id in the first column
   of its table rows, pattern `^\|\s*`([a-z0-9-]+)`\s*\|`, **failing if it
   collects none**;
2. reads `docs/plans/2026-08-29-implementation-roadmap.md`, **failing if the
   file is absent**, and asserts every collected id appears in it as the same
   backticked token;
3. asserts the roadmap's `**Ranked at:**` line names `cut N` for the newest
   results record's N, selected as the curation guard selects it.

It joins on ids, never on prose, so rewording a boundary label breaks
nothing. It reads two sections of two files and catches the one drift this
document invites — a cut lands, the ledger table updates under its guard, and
the roadmap is forgotten. It asserts nothing about tiers or order.

**After editing:** `python/tools/check_guide.py`; `test_designs_corpus.py` and
`test_check_guide.py`; `git diff --check`; a diff review confirming only the
ledger, the guide index, the test file, the new roadmap, and this design's
status line changed.

## 7. Delivery

1. **Adjudicate.** Recompute §3.1's status table from the cut documents and
   results records and pin the script's output in the roadmap's appendix.
   For each of the open rows, read its remainder from the source §3.1 names
   and classify it under §3.2, recording the source section. Rows whose
   remainder is a limitation are listed with the banking section and leave
   their boundary.
2. **Promote.** Add the `id` column and §3.3's boundaries to the ledger's
   `Current state` table; restate the entry rule; add the one link sentence.
3. **Guard.** Add the test; watch it fail on the missing roadmap, then pass.
4. **Rank.** Write the roadmap with §4's tiers under `Ranked at: cut 11`,
   every boundary by id, every prerequisite and blocker cited by document and
   section, the ride-along assignments, and the appendix from step 1.
5. **Maintain.** Add the maintenance sentence to `docs/guide/README.md`; bump
   `updated`.
6. **Gate.** Run the gates and the diff review.
7. **Close.** Correct this design's `**Status:**` line to record delivery,
   in the same commit — a status header that says "approved" after the work
   lands is the drift the curation pass exists to prevent.
8. Commit as documentation-only work; the `--no-ff` merge into `main` is the
   human partner's.

The next cut — `successor-admission` — begins as its own brainstorming
session against the intent-boundary design's §5, and is not part of this
delivery.
