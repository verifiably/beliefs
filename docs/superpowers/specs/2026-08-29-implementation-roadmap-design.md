# Implementation roadmap — design

**Date:** 2026-08-29
**Status:** approved in session
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
(§3) found seven more that it can. Second, several remainders have had a
designed entry point for weeks — G4's successor-admission obligations,
consolidate/move/deletion, the URL retrieval boundary — with nothing recording
that they are ready.

## 2. Decision

Write a dated, living roadmap at `docs/plans/2026-08-29-implementation-roadmap.md`
that ranks implementation boundaries in dependency tiers, orders within a tier
by what a boundary unblocks, labels each row's evidence, and is recomputed —
not accreted — whenever a cut discharges. It ranks implementation boundaries
only; design questions appear solely as a row's blocker.

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
  order*. Every roadmap row with `proven` evidence (§3) names a boundary that
  is in the ledger table or enters it in the same commit. `open-questions.md`
  remains the authority for what is undecided; the roadmap cites a design
  question only in a row's *blocked on* column, linking its anchor.
- **The one edit to the guarded section.** The ledger's `Current state` gains
  exactly one sentence — "Ordering over these rows lives in
  `../plans/2026-08-29-implementation-roadmap.md`." — plus the promoted rows
  §3.3 names. No ordering enters the ledger.

### 2.2 What it is not

It does not select cut scopes, freeze rows, or assign arms; a cut document does
that prospectively when its slice is drawn. It does not schedule `atoms` or
`nodes` work; it records cross-repo seams as prerequisites naming the owning
design. It carries no dates, estimates, or effort figures.

## 3. Adjudication and evidence tiers

Every ranked row carries one of two labels.

### 3.1 `proven`

**`proven`** — open by a named, current source: the newest results record's
`Remaining boundary` section, a design's own "not here, each a named
deferral" list, or a cut document's deferred table with the unblocking
dependency stated. As of cut 11:

| boundary | source |
|---|---|
| G4 / successor admission; event-level L8; L13 preimage resolver | cut 11 results §5; ledger row 5's dated note of 2026-08-28 |
| the first contract cut, executable suite, N1–N10 | ledger row 7 |
| consolidate / move / deletion | cut 5 §7 limitation 4; family-adapters design ("deferred to their own cut with the world index"); ledger §3 item 5 |
| C7, C8, C9 | cut 5's deferred rows, each with its unblocking dependency named |
| URL retrieval boundary, acquisition orchestration, typed retrieval grants | holdings design §1 "not here, each a named deferral" items 1–3; cut 11 §8 item 4 |
| D4 `KindSpec` compilation | ledger §3 item 10: "D4 is fully deferred" |

### 3.2 `presumed`

**`presumed`** — the guarantee row has never appeared in any cut document's
row table, or the only statement of its openness is a banking-era ledger
sentence that later cuts may have partly overtaken. As of cut 11: W1, W2, W4,
W5, W5a, W6, W7, W8, W8b, W9, W10, W11, W12, W14, W15, W16; D1, D2, D5, D8,
D9, D10; M1, M12, M3's unselected clauses, M2 and M5 completion; R15; G5; T7;
P1's resolver-negative arm; the `nodes` remainders (reserved-path contract,
recoverable construction, digest-id hazards); the second `science.identity.v1`
parity fixture (formal model §8).

A `presumed` row is ranked, and the cut that takes it re-adjudicates at
freeze. Finding it already closed is a results-record finding, not a roadmap
edit; finding it lapsed (as W4 may be, merge having been retired 2026-08-08)
is a design-lifecycle finding for the owning design.

### 3.3 Promotion into the ledger table

Only `proven` rows enter the ledger's `Current state` table, under that
section's own rule. This design's delivery adds four rows — consolidate /
move / deletion; C7–C9; the holdings deferrals as one row; D4 — each with
owner and what it blocks, in the table's existing format. `presumed` rows live
in the roadmap alone. The existing guard is unaffected: it constrains what the
table must name, never what else it may.

### 3.4 Excluded by construction

Design questions — artifact 11 (the pinned authority snapshot), ρO3, recency
as a projection rule, the extraction step (kernel limitation 3), the
act-report's cross-root publication residue, the agentic surface, salvage —
appear only in a row's *blocked on* column.

## 4. The ranking

Dependency first, then breadth of what a boundary unblocks.

### 4.1 Tier 1 — buildable now, entry point already designed

Strict order. Row 1 is the next cut.

| # | boundary | evidence | unblocks | placement |
|---|---|---|---|---|
| 1 | **G4 / successor admission** | proven | kernel §8.7's fourth recorded-mutation consequence — the kernel's invariant story closes; rows 5 and 7 read G4 in full | designed across nine readings with five opening obligations written (intent-boundary design §5); Science-only; smallest of the tier |
| 2 | **Consolidate / move / deletion** — the last mutation family | proven | C7's consolidate surface; W5 (move); W16 (consolidate); completes the family-adapter set | deferred "to its own cut with the world index", which now exists |
| 3 | **URL retrieval boundary, acquisition orchestration, typed retrieval grants** | proven | H4 in full; T7's same-root case; the first acquisition of a dataset from outside the system | holdings design §2–§3 specify the canonicalization profile and network discipline |
| 4 | **Event-level L8** | proven | row 5 reads L8 in full; the log's last Science-only remainder | §7's ordered-cuts predicate is built; the event-level relation is its successor |
| 5 | **The first contract cut, executable suite, N1–N10**, carrying P1's resolver-negative arm | proven (P1 arm presumed) | the widest set: the conformance-package split (ledger §5), instrument-certification cadence, legacy-check disposition (N10), P1 | last in the tier although it unblocks the most: N1 mints a successor contract identity for every oracle amended after the freeze, and rows 1–4 are Science-only closures that would each force one. Freeze after them |

### 4.2 Tier 2 — after a named prerequisite lands

Ordered only where dependency forces it.

| boundary | evidence | prerequisite | unblocks |
|---|---|---|---|
| C7–C9 | proven | tier-1 #2 for C7; a stored semantic-snapshot kind and evaluator for C8–C9 — 5a's own remainder | the correction lifecycle in full |
| L13 preimage resolver | proven | an `atoms` blob-read seam behind its own design gate; `atoms`' deferred-obligation ledger carries no such entry today | row 5 in full; the held-copy match strengthened from path to bytes |
| World resolution: W1, W2, W6, W7, W8, W8b, W10, W11, W12, W15, W5a; W4 adjudicated | presumed | a slice design — the registry and epoch designs cover the write side only | the read side of the world: resolution states, cross-corpus edges, views, coreference balance |
| D remainder: D4; D1, D2, D5, D8, D9, D10 | D4 proven, rest presumed | none hard | the first domain pack |
| M1, M3's unselected clauses, M2 and M5 completion | presumed | an instrumented resolver (M1) | refinement evidence for M\* |
| R15; S5, S6, G2c, G3, G8 partials; G5; the second parity fixture | presumed | confined execution (R15); the rest ride with whichever cut touches their surface | row closures, no new capability |
| `nodes`: reserved-path contract, recoverable construction, digest-id hazards | presumed | `nodes`' own design gate | audits over damaged corpora; manifest safety |

### 4.3 Tier 3 — blocked on a design question

Unordered. Each row links its `open-questions.md` anchor.

| boundary | blocked on |
|---|---|
| W9, W14, every rendered label | artifact 11, the pinned authority snapshot |
| recency as a successor projection rule | the holdings residue |
| weighted belief | ρO3, estimand typing |
| M12 end to end | the extraction step, kernel limitation 3 |
| T7's cross-root publication case | the act-report residue |
| the agentic surface; salvage | the two undesigned sub-problems (kernel §10) |

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
- **Ranking only `proven` rows.** Leaves the largest unbuilt surface — world
  resolution — invisible because no cut happened to table it.
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

1. reads the ledger's `Current state` section (the curation guard's
   `_h2_section` helper) and collects the bold boundary labels from its
   table's first column — the `**…**` span at the start of each row;
2. reads `docs/plans/2026-08-29-implementation-roadmap.md` and asserts each
   label appears in it;
3. asserts the roadmap's `Ranked at` line names the newest results record's
   cut number, selected the way the curation guard selects it.

Both reads fail closed: a missing section, a missing roadmap file, or an empty
label collection is a failure. The guard reads two sections of two files and
catches the one drift this document invites — a cut lands, the ledger table
updates under its guard, and the roadmap is forgotten. It asserts nothing
about tiers or order.

**After editing:** `python/tools/check_guide.py`; `test_designs_corpus.py` and
`test_check_guide.py`; `git diff --check`; a diff review confirming only the
ledger, the guide index, the test file, and the new roadmap changed.

## 7. Delivery

1. Write the roadmap with §4's content, each row citing its evidence source by
   document and section, under the header `Ranked at: cut 11`.
2. Promote §3.3's four rows into the ledger's `Current state` table; add the
   one link sentence.
3. Add the guard; watch it fail on the missing roadmap, then pass.
4. Add the maintenance sentence to `docs/guide/README.md`; bump `updated`.
5. Run the gates and the diff review.
6. Commit as documentation-only work; the `--no-ff` merge into `main` is the
   human partner's.

The next cut — G4 / successor admission — begins as its own brainstorming
session against the intent-boundary design's §5, and is not part of this
delivery.
