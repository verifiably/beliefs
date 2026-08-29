# Current-state documentation curation — design

**Date:** 2026-08-28
**Status:** approved in session; awaiting written-spec review before planning
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
4. A small set of design status headers still make present-tense implementation
   claims contradicted by later discharged cuts.

The result is not broken navigation. It is unnecessary duplication: a reader
must reconcile several current-state narratives before learning what exists.

## 2. Decision

Use the existing adoption ledger as the one current-state authority. Do not add
a status document.

The ledger gains a compact summary near its top with three parts:

- what is implemented through conformance cut 11;
- the remaining implementation boundaries already assigned to named owners;
- unresolved design areas, linked to their authorities but neither ranked nor
  selected.

Every other live surface becomes a projection of that summary:

- README gives a short capability snapshot and links to the ledger and results;
- guide topic pages state only the implemented and open facts specific to their
  topic, then link to the ledger for the complete status;
- `open-questions.md` lists unresolved design decisions only;
- stale design headers gain dated corrections while retaining their historical
  text.

The pass does not choose the next slice. The curated ledger summary is the input
to a later, dedicated roadmap brainstorming session.

## 3. Authority and preservation rules

1. **Current state is evidence-backed.** A commit claim requires ancestry; an
   implementation claim requires the named tree surface; a discharge claim
   requires its results record.
2. **History remains history.** Frozen cut bodies, plans, execution ledgers,
   and results records are not edited. The detailed adoption rows and their
   dated corrections remain intact.
3. **Headers append; they do not rewrite.** Where an old header truthfully
   records its original state, append a dated current-state correction. Do not
   erase the earlier claim.
4. **Uncertainty fails closed.** If a current-state claim cannot be proved from
   the tree and ancestry, leave it unchanged and report it rather than infer a
   closure.
5. **No roadmap by implication.** Ordering, priority, and “next slice” language
   do not appear in the curated summary.

## 4. Document changes

### 4.1 Adoption ledger

Add an unnumbered `Current state — 2026-08-28` section before the detailed
artifact inventory so existing numbered anchors do not move.

The summary names capabilities, not every commit:

- typed claims, admission and belief computation;
- run closure, execution, replay, reports, and qualification;
- certified persistence and mutation families;
- world registry, epochs, anchoring, lifecycle, and verified holdings.

The remaining-implementation list is limited to already named owners. At
minimum it preserves successor admission/G4, event-level L8, and the L13
preimage resolver. Other items enter only when the detailed ledger proves they
are still open.

The unresolved-design list links to existing questions or authority rows. It is
an inventory, not a recommendation.

### 4.2 README

Keep the complete design catalog. Replace the cut 1–11 narrative under
`Status` with:

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
- `claims-and-belief.md`: correct the statement that belief computation,
  assessment eligibility, and persistence are outside the implemented cuts.
- `computation-and-reproducibility.md`: correct the statement that spec
  persistence, closure construction, execution, replay, verification, and
  assessment admission are unimplemented.
- `open-questions.md`: retain unresolved design questions; remove cut history
  and implementation-remainder inventories now owned by the ledger summary.
- Update every changed page's `updated` date and source list. Change the
  glossary only if a definition is factually stale; freshness alone is not a
  reason to touch it.

### 4.4 Dated status-header corrections

The evidence audit covers these known stale or incomplete headers:

- contributor-guide design: the guide exists and is maintained;
- act-report design: the stored kind, report codecs, completion reading, and
  run-boundary publication have landed, while its named orchestration deferrals
  remain;
- computation design: the implemented cuts cover substantial portions of the
  run, replay, verification, and admission surface, without claiming the whole
  R table;
- tamper-evident-log design: qualification is evaluated after cut 11, while G4
  remains with successor admission;
- verified-holdings-record design: the store-side record, acts, reduction,
  receipt, and adapter landed with cut 10, while URL and orchestration
  deferrals remain;
- conformance cut 4: its frozen selection was discharged; the body remains
  untouched.

An additional header may change only when the same evidence rule proves a
present-tense claim stale. Header corrections do not relabel a partially
implemented guarantee table as complete.

## 5. Alternatives rejected

### A new current-state document

Rejected because it would compete with the adoption ledger and create another
surface to synchronize.

### Mechanical wording corrections only

Rejected because the repeated chronology would remain and drift again.

### A full contributor-guide rewrite

Rejected because the topic structure still works. The problem is status
duplication, not the explanatory model.

### Ranking next work in this pass

Rejected by scope. Ranking deserves its own session after the current-state
authority is trustworthy.

## 6. Verification

Before editing, verify every changed status claim against commit ancestry,
named implementation surfaces, and results records. After editing:

1. search live surfaces for superseded current-state phrases;
2. run `python/tools/check_guide.py`;
3. run `python/tests/test_designs_corpus.py` and
   `python/tests/test_check_guide.py`;
4. run `git diff --check`;
5. review the diff to confirm frozen cut bodies and historical plans/results
   are untouched, with cut 4 changed only in its status header.

No new mechanical guard is required. Existing checks already cover guide
freshness, source links, design counts, and local Markdown targets.

## 7. Delivery

1. Verify and record the current-state evidence.
2. Add the ledger summary.
3. Collapse README and guide chronology into projections of that summary.
4. Prune `open-questions.md` to design questions.
5. Append the evidence-backed header corrections.
6. Run the documentation gates and a final frozen-history diff review.
7. Commit the curation as documentation-only work.

The later roadmap session starts from the merged ledger summary and is not part
of this delivery.
