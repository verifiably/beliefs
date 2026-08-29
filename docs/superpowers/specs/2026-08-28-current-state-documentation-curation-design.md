# Current-state documentation curation — design

**Date:** 2026-08-28
**Status:** approved in session; revised 2026-08-28 after written-spec review;
delivered 2026-08-28 on `docs/current-state-curation` (evidence at
`docs/plans/2026-08-28-current-state-evidence.md`)
**Scope:** live navigation and status surfaces only. A ranked roadmap and choice
of the next implementation slice are explicitly deferred to a separate
brainstorming session.

## 1. Problem

The documentation guards pass, but the live documentation has accumulated four
forms of drift:

1. README and several guide pages repeat the cut-by-cut implementation
   chronology even though the adoption ledger is declared to be the sole status
   authority.
2. Topic pages last refreshed early in the redesign still describe belief,
   runs, verification, and persistence as wholly unimplemented.
3. `open-questions.md` says it excludes deferred implementation, then carries
   cut history and implementation remainder alongside actual design questions.
4. Design headers carry implementation status, so each landing slice appends
   another dated correction to them. The tamper-evident-log design's header and
   body now hold 28 such corrections, world addressing 25, computation and
   reproducibility 14, and the epistemic kernel 12 — 79 across four designs.
   Two headers — act-report and verified-holdings-record — still say "Nothing
   here is implemented", which is false.

The result is not broken navigation. It is unnecessary duplication: a reader
must reconcile several current-state narratives before learning what exists.

Behind all four is one cause. Status is restated by hand on every surface that
mentions it, and no guard checks that two surfaces agree. Freshness, source
links, design counts and link targets are all guarded; agreement is not. A pass
that only rewrites the restatements will be needed again.

## 2. Decision

Do not add a status document. Instead, give each *kind* of fact exactly one
owner, and let every other surface link rather than restate.

| kind of fact | owner |
|---|---|
| what is built, what remains to build, and who owns each remainder | the adoption ledger's current-state summary |
| what is undecided | `docs/guide/open-questions.md` |
| what was run, and the evidence it establishes | the conformance-cut results records |
| when a design banked, and what it amended | that design's header |
| what the system means and how it fits together | README and the contributor guide |

This is the correction to the "one current-state authority" framing. Current
state is two irreducibly different things — what is built and what is undecided
— and a single summary holding both is what forces the disclaimer that the list
is "an inventory, not a recommendation". Split by kind, and the disclaimer is
unnecessary: the ledger never holds a design question, so it can never imply an
ordering over one.

The ledger gains a compact summary near its top with two parts:

- what is implemented through conformance cut 11;
- the remaining implementation boundaries already assigned to named owners.

It links to `open-questions.md` for unresolved design areas and lists none
itself.

Every other live surface becomes a projection of that summary:

- README gives a short capability snapshot and links to the ledger and results;
- guide topic pages state only the implemented and open facts specific to their
  topic, then link to the ledger for the complete status;
- `open-questions.md` lists unresolved design decisions only;
- design headers stop carrying implementation status (§3.3).

A projection that is only maintained by hand is duplication with a better name,
so §6 adds the one guard that makes the ledger summary's remainder
self-defending.

The pass does not choose the next slice. The curated ledger summary is the input
to a later, dedicated roadmap brainstorming session.

## 3. Authority and preservation rules

1. **Current state is evidence-backed.** A commit claim requires ancestry; an
   implementation claim requires the named tree surface; a discharge claim
   requires its results record.
2. **History remains history.** Frozen cut bodies, plans, execution ledgers,
   and results records are not edited. The detailed adoption rows and their
   dated corrections remain intact.
3. **Design headers record design facts, not implementation status.** A design
   document is history the moment it banks, so its header states when it banked
   and what it amended — not what has since been built. Implementation status
   belongs to the ledger and the results records.

   This rule is forward-only, because rule 2 governs what is already written.
   Implementation history already accreted in a header stays exactly as it is;
   no more is added. Where an existing header makes a present-tense claim that
   is now false, append one dated line marking it superseded and pointing at the
   ledger summary. Do not erase the earlier claim, and do not replace it with a
   fresh enumeration of what landed — that is the restatement this pass removes.

   Conformance-cut documents are the one exception. Freeze and discharge are
   that document's *own* lifecycle facts — the same kind as a design's banking
   date — so its header records both and links to its results record for the
   evidence. What it still does not carry is what has since been built
   elsewhere.
4. **Uncertainty fails closed.** If a current-state claim cannot be proved from
   the tree and ancestry, leave it unchanged and record it as unproved in the
   evidence record (§7).
5. **No roadmap by implication.** Ordering, priority, and "next slice" language
   do not appear in the curated summary.

## 4. Document changes

### 4.1 Adoption ledger

Add an unnumbered section before §1's artifact inventory — after §0's
clean-start ruling — so existing numbered anchors do not move. Its heading
begins with the exact words `Current state`, followed by the refresh date, so
§6's guard can locate it by prefix while a reader still sees its freshness.

The summary names capabilities, not every commit:

- typed claims, admission and belief computation;
- run closure, execution, replay, reports, and qualification;
- certified persistence and mutation families;
- world registry, epochs, anchoring, lifecycle, and verified holdings.

The remaining-implementation list is limited to already named owners. At
minimum it preserves successor admission/G4, event-level L8, and the L13
preimage resolver — the three that ledger §1's dated note 11 and cut 11's
results record §5 both name. Other items enter only when the detailed ledger
proves they are still open.

Write that list as one row per boundary, each naming the boundary, its owner,
and what it blocks. That is the format the later roadmap session ranks, so it
ranks rows rather than re-deriving them from ledger prose. Ordering within the
list carries no priority (rule 5).

The summary lists no unresolved design areas. It links once to
`open-questions.md`, which owns them.

### 4.2 README

Keep the complete design catalog. Keep the two phrases
`test_the_readme_states_the_corpus_row_total` pins — **151 rows** and
**thirteen frozen tables** — which are acceptance criteria, not chronology. The
test pins nothing else, and the rest of that paragraph is fair game: it
continues into cut-1 chronology ("Cut 1 selects 11 of the 126 rows across the
ten tables that existed when it was drawn"), which goes with the rest. Keeping
the paragraph whole would carry chronology straight through the pass.

Replace the cut 1–11 narrative under `Status` with:

- a concise implemented-capability summary;
- the latest discharged boundary, cut 11;
- a link to the ledger's current-state summary;
- a link to the cut results records as the historical evidence trail.

README does not become a second ledger and carries no ranked next step.

### 4.3 Contributor guide

- `docs/guide/README.md`: refresh metadata and link its authority statement to
  the ledger's new summary.
- `foundations.md`, `identity-world-and-change.md`, and
  `contracts-and-adoption.md`: replace shared cut chronology with short
  topic-specific current-state paragraphs.
- `claims-and-belief.md` (§ Current state) and
  `computation-and-reproducibility.md` (§ Current state): both freeze at cut 1.
  Their statements are cut-1-scoped — "outside *that cut*", "the *current*
  conformance cut" — so they were true when written and are not falsehoods to
  repair. Replace each historically-scoped snapshot with the topic's current
  state: belief computation, assessment eligibility and persistence for the
  first; spec persistence, closure construction, execution, replay,
  verification and assessment admission for the second.
- `open-questions.md`: retain unresolved design questions; remove the cut
  history and implementation-remainder inventories now owned by the ledger
  summary. Preserve the section headings — other guide pages link to their
  anchors.
- Update every changed page's `updated` date and source list. Change the
  glossary only if a definition is factually stale; freshness alone is not a
  reason to touch it.

**The displaced citations.** Four designs are cited by no guide page other than
`open-questions.md`, and three of them appear only inside the chronology bullet
being removed: `2026-08-17-conformance-cut-4.md`,
`2026-08-18-composition-root-adapter-design.md`,
`2026-08-19-conformance-cut-5.md`, and `2026-08-19-family-adapters-design.md`.
`test_the_guide_cites_every_design` fails if they lose their last citation.

Leaving them in the page's `sources:` list would satisfy that guard while the
body no longer draws on them — a citation of convenience, which is the drift
this pass exists to remove. Instead, carry all four into
`contracts-and-adoption.md`'s `## References` list, which already cites
conformance cuts by name and is the topic page that owns adoption.

### 4.4 Design headers

Under rule 3, the correction set is smaller than an audit of stale claims would
suggest, because most stale headers are corrected by the rule ceasing to apply
rather than by another round of edits.

- **act-report design** and **verified-holdings-record design**: both headers
  assert "Nothing here is implemented, and no conformance arm is claimed",
  which is false. Append one dated line to each marking the claim superseded and
  pointing at the ledger summary. Do not enumerate what landed.
- **contributor-guide design**: `Approved for implementation` is a
  design-lifecycle fact and it is stale — the guide exists and is maintained.
  Correct it in place.
- **conformance cut 4**: its header records the freeze but not the discharge.
  Append the discharge with a link to its results record. The frozen body
  remains untouched.
- **tamper-evident-log**, **computation**, and every other design whose header
  already carries implementation history: leave untouched. Rule 2 governs what
  is written; rule 3 stops the accretion going forward.

Four designs carry a bare lifecycle label and are out of scope. Two read
exactly `**Status:** design` — world addressing and computation and
reproducibility — and two read `**Status:** design, approved in session`:
substrate consolidation and the epistemic kernel, the latter followed by its
own dated amendment. Grep for the short form alone and you will find two, not
four. A bare lifecycle label makes no implementation claim, so rule 3 does not
reach any of them, and correcting one while leaving three would be an arbitrary
asymmetry. If the label is itself wrong, it is a design-lifecycle question for
its own pass.

## 5. Alternatives rejected

### A new current-state document

Rejected because it would compete with the adoption ledger and create another
surface to synchronize.

### Mechanical wording corrections only

Rejected because the repeated chronology would remain and drift again.

### A full contributor-guide rewrite

Rejected because the topic structure still works. The problem is status
duplication, not the explanatory model.

### One summary holding both built state and open design questions

Rejected because `open-questions.md` already owns unresolved design questions.
Two inventories of the same facts is the duplication this pass removes, rebuilt
on the day it lands.

### Keeping implementation status in design headers, corrected as it drifts

Rejected on its measured cost. Four designs carry 79 dated corrections between
them across header and body, and each landing slice adds more; extracting one
current fact now means reading a header in date order. Appending to them again
buys one accurate day and guarantees the next pass.

### Hand-maintained projections with no agreement guard

Rejected because it is the status quo under a new name. Every drifted surface in
§1 was written accurately and then left behind, and no guard noticed.

### Ranking next work in this pass

Rejected by scope. Ranking deserves its own session after the current-state
authority is trustworthy.

## 6. Verification

Before editing, verify every changed status claim against commit ancestry,
named implementation surfaces, and results records.

**A new guard.** Add `test_the_ledger_summary_names_the_newest_remaining_boundary`
to `python/tests/test_designs_corpus.py`. It:

1. selects the newest `docs/plans/*-conformance-cut-N-results.md` by cut number;
2. reads that record's `Remaining boundary` section, and **fails if the heading
   is absent**;
3. collects the guarantee-row labels it names with a *prose* label pattern,
   `\b([GSWRCXNLDMPHT][0-9]+[a-z]?)\b`, and **fails if that collects nothing**;
4. asserts the ledger's `Current state` section names that cut number and every
   one of those labels.

Steps 2 and 3 must fail closed, and this is the part to get right. The corpus's
existing row patterns cannot be reused here: `_ROW` anchors on a table cell
(`^| **G4** |`) and `_ROW_RANGE` matches only ranges, so both return the empty
list against cut 11's Remaining boundary, which is prose. A guard that collects
nothing and then asserts over the empty set passes vacuously — it would report
green on exactly the drift it exists to catch.

The heading is a convention this guard establishes, not one it inherits. Cut 11
is the only results record of the eight that carries a `Remaining boundary`
section; the other seven have none. So the guard binds the newest record only,
and a future record that omits or renames the section fails rather than
silently satisfying it (rule 4).

For cut 11 the prose pattern collects G4, L8 and L13 — exactly the three §4.1
requires. The guard is otherwise deliberately minimal: it reads one section of
one file, so it cannot catch every disagreement, only the one that actually
happened — a cut lands, names its remainder, and the summary is never updated.
It constrains what the summary must name, never what else it may say.

After editing:

1. search live surfaces for superseded current-state phrases. At minimum:
   `outside that cut`, `current conformance cut`, `Nothing here is implemented`,
   `Design complete`, and any `cut N` in README or a guide page outside a
   reference list;
2. run `python/tools/check_guide.py`;
3. run `python/tests/test_designs_corpus.py` and
   `python/tests/test_check_guide.py`;
4. run `git diff --check`;
5. review the diff to confirm frozen cut bodies and historical plans/results
   are untouched, with cut 4 changed only in its status header.

## 7. Delivery

1. Verify the current-state evidence and record it at
   `docs/plans/2026-08-28-current-state-evidence.md` — a tracked path, because
   this pass runs in a worktree that is removed on merge and the design's whole
   authority rests on that verification having happened. The record names each
   checked claim, the ancestry or tree surface that proves it, and any claim
   rule 4 left unproved.
2. Add the ledger summary and its two-part structure.
3. Add the agreement guard, and watch it fail before it passes.
4. Collapse README and guide chronology into projections of that summary.
5. Prune `open-questions.md` to design questions, carrying the four displaced
   citations into `contracts-and-adoption.md`.
6. Append the four header corrections §4.4 allows.
7. Run the documentation gates and a final frozen-history diff review.
8. Commit the curation as documentation-only work.

The later roadmap session starts from the merged ledger summary's
remaining-implementation rows and is not part of this delivery.
