# Overlapping publications in a recipient's world

## Problem

A recipient that holds two publications sharing records cannot read its world.
Every republication of a view keeps its selected records' addresses and uids, and
any publication that carries closure shares content-addressed records with its
sources. Once two such corpora are live, the world's address map refuses the
shared address (`duplicate-location`). No epoch can be captured, and every world
read and mount citation fails. Science commons milestone 1b (`sci-9104fb`)
depends on this directly (`beliefs-81367e`). Its first step overlaps by
construction: *A* adopts *B*'s derivation, which carries *A*'s own records.

## Current behaviour and evidence

Read on main at `8aefcbf`, 2026-10-09. No suites were run.

- `python/src/beliefs/world/derive.py` `address_map`: it refuses `uid-corruption`
  first (one uid, two canonical addresses), then `duplicate-location` (one
  address, several `(corpus_id, uid)` claims), whether the content is identical
  or not. The map it returns is singular, `address -> (corpus_id, uid)`
  ("the address map is singular (world §4.3)"). Epochs publish it as
  `address-map.yaml`, and `world/read.py` `_address_map` reads it back the same
  way.
- `python/src/beliefs/corpus.py` `_one`: a mount citation held by two session
  corpora refuses `duplicate-location` and never picks a holder by corpus order
  (mount-citations design decision 4; cut 44's J17). That design names
  `beliefs-81367e` as the change that amends this rule and the world map's rule
  together.
- `python/src/beliefs/publish.py` `_population`: publish stages each selected
  record's snapshot text verbatim. A republished record and its predecessor's
  copy are therefore byte-identical unless the record was revised between the
  two snapshots.
- `world/live.py` captures only corpora with no terminal status. `World.retire`
  exists (`world/registry.py`), and a retired corpus leaves the live span.
- `publication_tip` sidesteps the problem by reading held roots alone
  (publish-act-remote design decision 9, §13 item 3).
- Belief acceptance (`docs/superpowers/specs/2026-10-02-belief-acceptance-design.md`)
  evaluates `counts(corpus_id, address)` against a singleton holder set. The
  design states that overlap must try the predicate for every holding corpus,
  or compute an equivalent union, rather than take the first carrier.

## Constraints

- Science commons design §4.7 (science
  `docs/specs/2026-09-30-science-commons-design.md`) states three outcomes:
  identical records held under one address in several mounted corpora read
  once; conflicting content under one address refuses explicitly, never by
  corpus order; competing assessments with distinct `(spec, run, proposition)`
  identities stay distinct. Deduplication by `corpus_id` alone is insufficient.
- Commons §10 makes retirement surface policy, not the kernel's answer. A
  predecessor that something requires stays mounted beside its successor, and
  *A*'s write root cannot be retired. Retirement alone therefore cannot remove
  the overlap. §10.5 refuses a conflicting successor before admission, so the
  kernel's conflict refusal (outcome 2) only has to stay explicit.
- Neither violation is resolved by precedence (W8b). `uid-corruption` stays
  unconditional, and `consolidate` stays the exit for a real conflict.
  `uid-corruption` here is `derive.address_map`'s rule: one uid under two
  canonical addresses. The world view enforces a second, separate rule. Its
  owners loop (`world/view.py:382`) refuses any uid held by two corpora,
  whatever the address map says, and that is exactly the overlapping case.
  Changing the map alone leaves this refusal standing, so the design must rule
  on it explicitly: exempt equal-content holders, or keep it and say why.
  `world/live.py`'s copy (`beliefs-0e1acb`) follows the same ruling.
- Publishing chooses attribution through one holder. `_selected_attributions`
  (`publish.py:232`) groups the selected refs by `read.corpus_of(ref)`, a
  single corpus. Identical bytes can arrive through carriers with different
  provenance, so choosing among several holders could change or drop the
  attribution a republication carries.
- A frozen cut is never edited. Any change to the address-map shape or to J17
  supersedes those rows by citation in a new cut. That cut also adds its
  `test_recent_cut_acceptance.py` row, and only `root.py` imports `atoms`.
- Related open work in the same function: `beliefs-354eae` (the
  retired-address collision raises a plain `ValueError`) and `beliefs-0e1acb`
  (`live.py` duplicates the W8b code). The design should absorb or sequence
  both.

## Alternatives

1. **A multi-holder address map keyed by content identity (lean).** An address
   maps to a set of `(corpus_id, uid)` holders. Holders whose content identity
   is equal read as one record. Unequal content still refuses
   `duplicate-location` with `consolidate`. The epoch document, the
   `world/read.py` reader, mount citations (decision 4) and the acceptance
   predicate (try every holder) all change together. This is the only option
   that meets §4.7 for the write-root-plus-carrier case.
2. **Retirement only.** Supersession retires the predecessor, and the index
   stays singular. This fails §4.7 for 1b's first step and for any
   dependency-kept predecessor.
3. **Recipient consolidation.** The recipient folds the overlap into one
   corpus. This rewrites what was shared, and commons §10.1 forbids it. Keep it
   only as the exit for real conflicts.

## Unanswered questions

Each is for the design task `beliefs-918fd2` to settle against the code.

- What "identical" means: equal canonical record bytes, or equal uid plus
  semantic hash. Publish copies bytes verbatim, so byte equality may be enough,
  but deprecated-id lists and revisions need a ruling.
- Which corpus a read reports as the record's location (`node_corpus`, J20's
  attribution) when several hold it, and whether NotPresent or Unknown
  survives when one holder is absent and another is present.
- How the retraction-discovery map, the other location-bearing derivation,
  treats a shared address.
- The epoch format change for `address-map.yaml`, and how readers of older
  epochs are handled.
- Origin selection at publish: when several holders carry one record, which
  holder's provenance does a republication attribute it to, and is that
  choice independent of holder order? The design's arms include a publish →
  adopt → republish case with the holders reordered, and the republished
  attribution must not move.
- Whether the view's owners check (`world/view.py:382`, one uid in two
  corpora) admits equal-content holders, and how that stays distinct from
  real uid corruption.

(The last two questions were added 2026-10-09 from a review of this brief.)

## Proposed decomposition

- `beliefs-918fd2` — Design overlapping-publication reads from this brief: the
  cut spec covering the three outcomes, J17 and the singular-map rule
  superseded by citation, the acceptance predicate's per-holder
  evaluation, the view's owners check, and publication attribution's origin
  selection. Planned, high complexity. On approval its plan implements it,
  and `beliefs-81367e` closes with that cut.
- `beliefs-81367e` waits on it. `sci-9104fb` (milestone 1b) depends on
  `beliefs-81367e`.
