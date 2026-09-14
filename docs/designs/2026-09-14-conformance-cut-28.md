# Conformance cut 28 — view evaluation and the W8/W8b discharge

**Status:** frozen 2026-09-14 before implementation.
**Frozen:** 2026-09-14, before implementation, on `design/world-resolution-slice-4`
**Design:** `../superpowers/specs/2026-09-13-world-resolution-slice-4-design.md`, approved 2026-09-14; amended at plan review (§11)
**Numbered after** cut 27 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The baseline below describes `main` at `98b92ec` before implementation.

A view record stores a query. Cut 14 landed the language — `view_query.py`
parses `science.view-query.v1` into sorted, deduplicated clauses of `kinds`,
`references-term`, `closure` and `addresses` predicates — and the write
boundary admits a query by form and vocabulary alone (`corpus.py`'s
`_coordination_query`). The view-kinds design §2.2 pins the semantics
denotationally, over the world at a named epoch, and says the evaluator is
the `world-read` lane's to build. Nothing on `main` evaluates a query: no
function takes a `ViewQuery` and answers with records, and the only consumer
of a parsed query is the validator that checks it against the coordination
contract's vocabulary.

The read side it needs is complete. `open_world_view(world, published)`
captures every present covered corpus at an explicit epoch, serves mapped
records as detached copies, answers `locate` with the three states and
refuses corruption; `RelationAdjacency` and `traversal.closure` already walk
relations across corpora over it. The coordination resolver
(`ReadView.resolve(CoordinationAddress)`) answers which revision of a view
record stands, live and unbound, and refuses `divergent-view` rather than
choosing. The two regimes the view-kinds design §6.2 keeps apart — the
*record* resolves live, the *query* evaluates bound — are both in place and
have never been joined.

W7 asks for exactly the join: a topic view evaluated over an entity held in
another corpus is found. It has never been selected. The user and autonomy
layer design §8 item 5 makes `publish` wait on this lane because "view
queries resolve through it", and §4.4 derives `next` from a query through
the current view. This slice builds the evaluator and selects W7.

The slice also carries the discharge audit slice 3 §11 item 3 assigned it:
W8 and W8b, retained and unselected through cuts 23, 24, 25 and 27.
`beliefs-fda0e5` repaired the build so the epoch derivation refuses both
uid violations with distinct findings (`derive.address_map`), and
`consolidate` (cut 16) repairs a duplicate location and refuses everything
else; every document since has said "measurement is not selection". This
slice selects W8b in full and W8 in part over that existing code, and says
in the accounting which arm of W8 no lane can run and why.

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-14-conformance-cut-28.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/errors.py`: `SelectionRefused`;
- `python/src/beliefs/view_query.py`: `stored_query`;
- `python/src/beliefs/decode.py`: `stored_claim_terms`, the profile-independent shape check factored out of `claim_from_stored`;
- `python/src/beliefs/world/view.py`: `_mapped_records`, the private enumeration;
- `python/src/beliefs/world/selection.py`: `SELECTION_VERSION`, `Unresolved`, `Selection` and `evaluate_query`;
- `python/src/beliefs/world/__init__.py`: the `Selection`, `Unresolved` and `evaluate_query` exports;
- `python/tests/test_view_query.py`, `python/tests/test_world_selection.py` and `python/tests/test_world_conflicts.py`: focused behavior;
- `python/tests/acceptance/test_world_selection_acceptance.py`, `python/tests/acceptance/n2_arms_cut28.py` and `python/tests/acceptance/test_n2_cut28.py`: durable arms, declarations and guard;
- `python/tests/test_designs_corpus.py`: the design-count guard;
- `python/tools/cut28_acceptance.py` and `python/tools/roadmap_status.py`: runner and accounting;
- `docs/designs/2026-08-02-world-addressing-design.md`: dated notes on W7, W8 and W8b;
- `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md`: the dated §13 note;
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/foundations.md`, `README.md` and the cut 28 results record: discharge and navigation.

Out of scope:

- W9 and W14 (`authority-labels`, tier 3): slice 2b's assignment of W14 to slice 4 does not stand (spec §8 item 1);
- W8's ambiguous-search-term conflict: deferred to `authority-labels` with W9, ledger artifact 11, and re-homed at discharge (spec §8 item 2);
- R23's rules-store clauses and W8a's `instrument-certification` arm (`contract-cut`);
- `beliefs-48214e` and `beliefs-24b42b`: filed, not prerequisites;
- `derive.py`, `relocation.py`, `corpus.py` and every served method of `world/view.py`: read and not rewritten;
- `next` and `publish`: consumers of the evaluator, not built here.

## 3. Selection

### W7 — closes
A topic record in one corpus whose query names records in the other is found under every predicate form — `addresses` selects exactly the named dataset and contributes its corpus alone; `kinds` selects both corpora's datasets and contributes both; `closure` from the first corpus's run over `produces` selects the second's dataset and not the run; `references-term` selects the second's proposition and never a dataset; a two-clause query selects and contributes both — each complete, each with the identity equal across two opens at one epoch. With the second corpus absent, `addresses` refuses `address-not-present` naming it, `closure` from the present anchor returns an incomplete selection with one not-present step naming the dataset, `kinds` returns an incomplete selection naming the corpus in `absent`, and a closure anchored in the absent corpus refuses `address-not-present` naming the anchor; every incomplete identity differs from the complete one and none is the empty set or `unknown`. Reordered clauses, predicates and corpus registration give one projection. A drifted view refuses `corpus-drifted` and a damaged one `corpus-damaged`; a retired anchor over a cycle selects what the live anchor selects; a dangling target is `unknown` and an absent inbound source `not-present`, both reported and neither dropped; a retired and a live address of one record select it once; a term in an argument and in a restriction both select, a malformed claim facet refuses naming the record, and a stale-hash proposition whose edit removed the term refuses rather than yielding empty; a stale selected record refuses; `clauses: []` is complete and empty; a `ReadView` is a `TypeError`. Selected: unit `W7`. **Deferred:** nothing.

### W8 — part, duplicate-location and address-conflict conflicts
Two records at one canonical address in two corpora refuse the build with a `duplicate-location` finding naming both claims in the capture's sorted order and no carrier, the same code, ref and claims in the other registration order; `consolidate` with the authored survivor repairs it, the rebuild publishes, the view serves one record, and swapping `keep` gives the mirror; `move` into the occupied destination refuses `DuplicateLocation` thereafter. Two `source` records at one derived address whose identifier maps differ refuse the build as `duplicate-location` before any basis is read, `consolidate` refuses `HistoryDisagreement` whichever is `keep` and writes nothing, and a source whose stored id is not its derived address refuses `SourceAddressDisagreement` at the write boundary. Selected: unit `W8`. **Deferred:** the ambiguous-search-term conflict, which needs the pinned authority snapshot (ledger artifact 11) and is W9's arm restated (`authority-labels`).

### W8b — closes, over existing code
One `uid` under two canonical addresses is `uid-corruption`, offers no repair, and `consolidate` over the pair refuses `AddressDisagreement`; two records at one canonical address in two corpora are `duplicate-location` both with a shared `uid` and with distinct `uid`s, the same code and ref; corruption outranks duplication when one `uid` does both; each corpus's own `corpus_check` reports neither. Selected: unit `W8b`. **Deferred:** nothing.

### Boundary invariants
No refusal borrows `NotPresent`, `Unknown` or `RecordNotPresent`; the evaluator opens nothing and reads no coordination record; every record read or selected passes the facade's validation rule; nothing is written by evaluation; the world view's served surface is unchanged.

## 4. Accounting

Three guarantee rows are read, **2 full/closed** (W7, W8b), 1 partial (W8), and **3 declaration units** carry them: `W7`, `W8`, `W8b`. W8's remainder is its ambiguous-search-term conflict, re-homed to `authority-labels` at discharge (§2); `world-resolution` then retains no guarantee row.

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the three units `W7`, `W8` and `W8b`, each single-homed to the test that exercises it.
2. Every durable arm runs on the certified volume. Capability refusal is an error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut27_acceptance.py",)` and `PHASE_MODULES = ("test_world_selection_acceptance.py", "test_n2_cut28.py")`.
4. The 23 declared arms cover every sabotage site: in `world/selection.py` (the entry damage check skipped; the entry drift check skipped; an unknown address no longer refusing; not-present collapsed into unknown; clauses intersected instead of unioned; the anchor included in its closure; the closure started from the literal anchor string; an absent inbound source dropped; `unresolved` omitted from the projection; `absent` omitted from the projection; selected records served unvalidated; candidate propositions read unvalidated; `references-term` matched on arguments only; a malformed claim facet read as not referencing; the world-only type check widened), in `decode.py` (claim terms normalized before comparison), in `world/derive.py` (the uid check dropped; the address check dropped; addresses checked before uids; `duplicate-location` keyed on `uid` equality), and in `relocation.py` (`consolidate` accepting two addresses; `consolidate` choosing a survivor when histories differ; `move` overwriting an occupied destination).
5. `test_n2_cut28.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree.
6. Prior declarations remain frozen and no check is reclaimed.
7. This document and its declaration inventory are pinned by digest before discharge.

The sites in item 4 count fifteen in `selection.py`, one in `decode.py`, four in `derive.py` and three in `relocation.py`: **23 arms**.

## 6. Second reader

The spec's two review passes on 2026-09-14 resolved four findings, then one
(§11 there). Plan review then amended the spec's drift rule, claim-shape
check and absent-inbound fixture. The plan's two reviews resolved eight
findings, then one; its review log records the resolutions. The user
authorized the freeze and Task 1 on 2026-09-14.

## 7. Limitations

1. Every predicate enumerates the capture, with no per-epoch index (spec §9 item 1).
2. There is no closure-over-selection predicate (spec §9 item 2).
3. W8's search-term conflict is unrun and re-homed, not closed.
4. `next` and `publish` are not built; their refusal rules over `Selection` are stated, not exercised.
5. The world view uses serial per-corpus coherent captures, not one simultaneous world state (slice 1 limitation 1).
