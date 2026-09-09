# World resolution, slice 1 — the world read view and cross-corpus traversal

**Date:** 2026-09-09
**Status:** draft for review; freezes as the next conformance cut once reviewed
**Boundary:** `world-resolution`, slice 1 of four (`beliefs-d248ba`)
**Lane:** `world-read`, worktree `.worktrees/world-resolution`
**Sources:** `../../designs/2026-08-02-world-addressing-design.md` (§5, §5.1, §7),
`../../designs/2026-08-08-world-address-ruling.md` (§9),
`../../designs/2026-08-03-world-index-packaging-design.md` (§5.4),
`../../designs/2026-08-20-world-index-slice-2-design.md` (§8.3),
`../../designs/2026-08-02-substrate-consolidation-design.md` (§5),
`../../designs/2026-08-04-formal-model-and-claim-calculus-design.md` (ρA7, D3)
**Measured against:** `main` at `197f517`

## 1. What this slice is

The world's read side exists at the epoch tier and stops there. Slice 2 of the
world index landed `world/read.py`: an address resolves through a published
epoch to `Resolved`, `NotPresent` or `Unknown`, a coreference edge answers
`active`, `inactive` or `indeterminate`, and every answer carries a
`BoundStamp`. Nothing below that tier can use it. `resolution.py` declares
`not-present` unreachable; `corpus.py` says in its docstring that traversal
truncates at the corpus edge; `lineage_snapshot` skips a dataset the corpus does
not hold without a word; `belief.py` banks `unavailable-corpus-absent` as a
reason it never returns. The mm30 reproduction record measured that a single
corpus needs none of this and that the dogfood needs all of it the day a second
corpus enters.

This slice connects the two tiers. It adds one concrete read handle over a
world, opened at an explicit publication, that the kernel's existing walks,
snapshot builders and evaluators accept beside the corpus `ReadView`; and it
makes the three absence distinctions the code has banked producible.

**Rows it closes or reads.** D3's `not-present` arm and the remainder of the
five-way non-collapse; S1 and S1a's chain crossing corpora; S5's cross-corpus
reach; W10 in full; R19's cross-corpus recomputation; R23's coverage clause.
W6 and W8b's duplicate-location arm are **measured** against the surface slice
2 landed and selected as arms over existing code.

**Rows it does not touch**, each named to its slice: the `coreference-attestation`
kind and every populated balance, omission-refutes and endpoint-refusal arm
(X12, W15, W8a's coreference arms, M3's coreference arm, W4's adjudication, W1,
W2, W5a) — slice 2; the snapshot import boundary, the audit and diagnostic-query
callers, R23's snapshot, divergence and explicit-import clauses, and the X5 and
W13 relabels — slice 3; view evaluation, W7 — slice 4.

## 2. Decisions

1. **A sibling view, not a protocol and not a subclass.** `ReadView` is sealed
   and final over exactly one `nodes` corpus (biology pack B3), and `corpus.py`'s
   docstring rules that a read-only protocol is not a capability boundary (S8).
   The world handle is therefore a second concrete, sealed, final class with the
   same method shape, and consumers that need world reach widen their annotation
   to the union `ReadView | WorldReadView`, exactly as `_ImportView` and
   `_CheckView` are admitted today.
2. **Every read is bound.** The view is opened at an explicit `Epoch`, never at
   `current` (`world/read.py`'s rule: nothing belief-reachable names `current`).
   Addressing goes through the epoch's address map only. An address the map
   records resolves to its carrier or reads `not-present`; an address the map
   never observed is `unknown` whatever a carrier holds today. Enumeration
   yields mapped records only. A carrier record the map does not know is
   **drift**: reported on the view, never silently included, never silently
   dropped.
3. **Absence is a named corpus, everywhere it survives.** `NotPresent` carries
   a stamp and nothing else; that is right for one answer and wrong for a
   snapshot. Every structure this slice threads absence through carries the
   absent `corpus_id` beside the reference, and every such structure's
   projection includes it, so two availability states never share an identity.
4. **Published evidence outlives an absent carrier.** A producer set built by
   scanning stored records loses a producer with its carrier. The world view's
   producer read consults the epoch's producers map as well, so an absent
   producing run is a `not-present` route and never an empty set.
5. **Fetches stay corpus-local.** `get`, facet reads and hash validation run on
   the holding corpus's own `ReadView`. The world view routes; it never
   re-implements a validated read.

## 3. The world read view

### 3.1 Module and surface

New module `beliefs/world/view.py`, exporting:

```
open_world_view(world: registry.World, published: epoch.Epoch) -> WorldReadView

class WorldReadView:           # @sealed @final, no public constructor
    stamp: BoundStamp
    # the corpus read shape
    resolve(ref) -> str | None
    holds(ref) -> bool
    get(ref) -> Node
    inbound(ref) -> list[ResolvedEdge]
    producers(dataset, *, aliases=()) -> tuple[str, ...]
    iter_stored() -> Iterator[Node]
    live_id(uid) -> str
    # world-only
    locate(ref) -> Resolved | NotPresent | Unknown
    corpus_of(ref) -> str | None
    published_producers(dataset) -> tuple[str, ...]   # the epoch's producers map
    corpus_view(ref) -> ReadView
    drift() -> tuple[DriftFinding, ...]
```

`Resolved`, `NotPresent`, `Unknown`, `Location` and `BoundStamp` are
`world/read.py`'s existing types, unchanged. `DriftFinding(corpus_id, uid,
address)` is new and frozen.

`resolve` answers the live address through the map, or `None` for `Unknown`
**and** for `NotPresent` — the corpus shape has one negative and keeps it, so
a consumer that needs the distinction calls `locate`. `holds` is
`resolve(ref) is not None`. `get` locates, then delegates to the holding
corpus view's `get`, so `semantic-hash-stale`, `semantic-hash-missing` and the
base-pin check are the corpus's own. `get` on a `NotPresent` ref raises
`RecordNotPresent(ref, corpus_id, stamp)`, a new `errors.py` class; on
`Unknown` it raises the `RefError` the corpus view would.

`corpus_of` answers from the map alone — an absent corpus's id is still an
answer. `corpus_view` returns the holding corpus's `ReadView`, refusing on
`NotPresent` and `Unknown`; it is the route for `read_observed_facets`, which
accepts exactly `ReadView` (B3) and keeps doing so.

### 3.2 Opening

`open_world_view` does, under one hold of the world lock through
`registry._locked_barrier`, following `resolve_address` rather than receipt
validation:

1. rescan the registry and reduce status for every `corpus_id` in
   `published.coverage`; a `duplicate-carrier` finding or an unreadable
   manifest refuses with `ResolutionRefused`, as `resolve_address` does;
2. open one `ReadView` per **present** covered corpus at its carrier root;
3. for every mapped `(corpus_id, uid)` whose corpus is present, check the
   carrier's index holds that `uid` under the mapped address; a disagreement is
   corruption and refuses with `ResolutionRefused`;
4. record as drift every `uid` a present carrier holds that the map does not
   record for that corpus.

The lock is released before the view is returned; every later read is on the
already-opened corpus views and takes no world lock. Opening is a point-in-time
composite by construction — a `ReadView` indexes at construction — and the
stamp says which publication it is bound to.

Coverage minus present carriers is the view's **absent set**, a
`Mapping[corpus_id, ()]` fixed at open. `locate` on a mapped address in the
absent set is `NotPresent(stamp)`; `corpus_of` still names it.

### 3.3 Enumeration

`iter_stored` yields, corpus by corpus in sorted `corpus_id` order, every
record the map records for that corpus, through the corpus view's own
unvalidated iteration. Records from absent corpora cannot be yielded and are
not; drift records are not yielded. A consumer that wants to know what it
could not see asks `drift()` and the absent set — `iter_stored` is silent by
the same rule that makes the corpus check's iteration silent: it reports
through findings, not by raising.

## 4. Cross-corpus edges

### 4.1 Inbound

`nodes` keys inbound edges by the target's local uid, so a corpus never lists
an inbound edge to an address it does not hold; it records the edge as
dangling. World `inbound(ref)` is therefore:

- the holding corpus's `inbound(ref)`, when the ref is `Resolved`; plus
- for every **other** present corpus view, each dangling edge whose target
  string resolves through the map to the same address.

A `NotPresent` ref has no holding corpus; its inbound is the dangling union
alone, so a run in a present corpus that produces a dataset in an absent one
is still found. An `Unknown` ref has an empty inbound.

`producers(dataset)` needs no change of rule: `_producer_ids` scans stored
records by target string and resolves through the view, and over the world
view's enumeration and map that already spans corpora.

### 4.2 The three adjacencies

`RelationAdjacency`, `LineageAdjacency` and `_DerivedFromAdjacency` in
`corpus.py`, and `superseded_by`, widen to `ReadView | WorldReadView`. Their
bodies do not change: they reach the view through `get`, `resolve`, `inbound`
and `live_id`, and the world view answers each across corpora. `closure` is
untouched. This is W10: a lineage chain spanning two corpora, as `produces` and
`transforms` edges on runs, returns its full closure at the world layer and
emits no `lineage-incomplete`; the corpus-local view still truncates, which is
W10's negative.

## 5. Absence reaches the readers

### 5.1 The lineage snapshot

`lineage.Route` and `lineage.Producer` today carry `resolved_run: str | None`
and `resolved_ancestor: str | None`; `None` says the referent is gone and
cannot say whether it is unknown or held elsewhere. `LineageSnapshot` gains
one field:

```
not_present: Mapping[str, str]   # stored ref -> corpus_id, per §2 decision 3
```

`lineage_snapshot(view, roots)` over a world view fills it: every stored run,
ancestor or observed root whose `locate` is `NotPresent` is entered under its
`corpus_of`, and its `resolved_*` field stays `None`. Over a corpus view the
mapping is empty, which is the snapshot as today. `not_present` enters
`snapshot_projection` as a sorted list of `(ref, corpus_id)` pairs. That
projection is the `lineage` member of the belief input digest (`closure.py`),
so a closure with a not-present ancestor and one with an unknown ancestor take
different digests — R23's coverage clause, "absence within coverage gives
`not-present` rather than a silent undiverged reading".

**Absent producers.** `_producers_of(view, dataset)` over a world view unions
two sources: the view's `inbound` (§4.1) and the epoch's producers map, read
through a new `WorldReadView.published_producers(dataset)`. A published run the
view cannot fetch is a `Producer(stored_run=address, resolved_run=None,
transforms=())` and enters `not_present`. `certify` therefore sees the route
and reports it, instead of a silently empty set that would let step 3's
divergence comparison pass.

**Absent roots.** An observed root that is `NotPresent` is inspected (§5
step 1 inspects the root explicitly), has no readable basis, and is entered in
`not_present`. `certify` emits `lineage-incomplete` for it and issues no
certificate.

**Findings name the corpus.** `certify`'s `lineage-incomplete` for a route or
root in `not_present` is emitted with the corpus id in its detail, so a reader
can tell "an ancestor this world has never seen" from "an ancestor held in
corpus X, which is not here".

### 5.2 The resolution snapshot

`resolution._BoundVocabulary` today has `readable: bool` and `terms`.
It becomes:

```
state: Literal["readable", "not-available", "not-present"]
terms: frozenset[str]        # empty unless readable
corpus_id: str | None        # the absent corpus, not-present only
```

`build_snapshot` gains `not_present: Mapping[VocabularyBinding, str]`
(binding → corpus id) beside `readable` and `unreadable`, and refuses with
`ResolutionError` any binding named in more than one of the three — the same
refusal it makes today for readable-and-unreadable, extended to every pair.
`_BoundVocabulary.projection()` includes `state` and `corpus_id`, so the
snapshot identity moves between availability states; a snapshot that differed
only in `resolve()`'s answer would let two states share one identity. `resolve`
answers `NOT_PRESENT` for the third state. The five outcomes are then all
producible, which is D3's remaining arm: the five-way non-collapse asserted with
every member reachable.

### 5.3 The evaluation seam

This is the one place the slice reaches into evaluation, and its members are
listed so the boundary is exact:

- `gather(view, ...)` and `evaluate_over(view, ...)` widen to
  `ReadView | WorldReadView`.
- `run_value(view, ref)` widens likewise. Its input filter `if view.holds(target)`
  keeps its meaning — an input in an absent corpus is not in the value — and
  the absence is reported through `evaluate_over` rather than swallowed: an
  input whose `locate` is `NotPresent` is collected into the not-present set
  below.
- `read_observed_facets(profile, view, target)` keeps its exact-`ReadView` check.
  `gather` calls it with `view.corpus_view(target)` when the view is a world
  view, and with the view itself otherwise. Facet receipts keep proving a read
  of a real corpus.
- `evaluate_over` over a world view returns `unavailable-corpus-absent` — the
  reason `belief.py` banked at line 84 and has never returned — when an
  observed root, a closure member or a run input is `NotPresent`, naming the
  corpus. `unavailable-input-unheld` keeps its meaning for a held record whose
  bytes are not here.
- `evaluate_over` supplies `SuppliedContext.node_corpus` from `corpus_of` over
  the closure when the caller passes none, so a two-corpus closure reaches
  `consulted_contracts` with a real attribution rather than fixture data. A
  caller-supplied `node_corpus` that disagrees with `corpus_of` on any node
  refuses; the world does not let the caller relocate a record.

Everything else in `belief.py`, `closure.py` and `consulted.py` is untouched:
retraction coverage stays supplied, the producer snapshot identity stays an
explicit argument, and belief still cannot name `current`.

### 5.4 The audit seam

`audit.check_verification` widens to `ReadView | _ImportView | WorldReadView`
and is exercised over a verification whose runs and spec sit in the other
corpus — R19's cross-corpus recomputation. `check_assessment`,
`check_lineage_basis`, `audit_corpus` and `corpus_check` are **not** widened
here: the world-scale audit is one of slice 3's three evaluator callers, and
`corpus_check` reaches the corpus root through `view._corpus`, which a world
view does not have and should not fake.

## 6. Refusals

| condition | answer |
|---|---|
| two configured carriers claim one covered corpus | `ResolutionRefused` at open |
| a present carrier's manifest cannot be read | `ResolutionRefused` at open |
| a present carrier disagrees with the map on a mapped uid | `ResolutionRefused` at open — corruption, never absence |
| a covered corpus has no carrier | the absent set; `NotPresent` on its addresses, never a refusal |
| a ref the map never observed | `Unknown`; no carrier is consulted |
| a carrier record the map never observed | a `DriftFinding`; never yielded, never a refusal |
| `get` / `corpus_view` on `NotPresent` | `RecordNotPresent` |
| a binding named in two availability states | `ResolutionError` at `build_snapshot` |
| a caller's `node_corpus` disagreeing with the map | `MalformedRecord` at `evaluate_over` |
| the epoch is not this world's | `EpochUnknown`, as `open_epoch` already raises |

No refusal here may borrow `NotPresent`: that answer tells a caller the record
is safely elsewhere, and none of the rows above is that.

## 7. What this slice measures rather than builds

W6 (the three states never collapse; removing a corpus does not convert its ids
to `unknown`) and W8b's duplicate-location half (two records at one address in
two corpora → a `duplicate-location` finding resolvable by `consolidate`) are
answered by `resolve_address` and the epoch build as they stand. The cut
selects arms over that code and records the reading. W8b's corruption half
(one `uid` under two addresses, no repair offered) is likewise read at build.
If a selected arm fails on the tree, that is a finding against slice 2's code
and is filed as such; it is not this slice's to repair inside the cut.

## 8. Testing and the cut

**Fixtures.** `tests/test_world_build.py` already builds a two-corpus world
with `admitted_world`, publishes an epoch with `publish`, and pins the four
rule bindings. The acceptance module for this cut reuses those helpers on the
certified volume and adds one fixture: a lineage chain `D0 → R1 → D1 → R2 → D2`
with `R1` and `D1` in corpus B and the rest in corpus A, plus a verification in
A whose two runs are in B. Absence is produced by dropping B's root from the
`WorldConfig` after publication and re-opening; never by deleting records.

**Arms**, each with a two-corpus positive and a corpus-local negative:

- W10: the world closure over the chain is complete and clean; the corpus-local
  closure from A reports `lineage-incomplete` for the same chain.
- S1/S1a: relation and lineage closures cross the edge, full rather than
  truncated; the dangling-target case is distinguishable from the crossing.
- S5 / R23 coverage: with B absent, `lineage_snapshot` enters `R1` and `D1`
  in `not_present` under B's id, `certify` says `lineage-incomplete` naming B,
  independence is `not-certified`, and the snapshot identity differs from the
  one with B present and from one with the ancestor unknown.
- Absent producer: with B absent, `D1`'s producer set is one not-present
  `Producer` from the published map, not empty; step 3 does not pass.
- D3: `build_snapshot` with a `not_present` binding resolves `NOT_PRESENT`; all
  five outcomes are produced in one test and pairwise distinct; the identity
  moves across the three availability states of one binding; overlapping
  inputs refuse.
- Evaluation: `evaluate_over` over the world view with B absent returns
  `unavailable-corpus-absent` naming B; with B present it reaches a belief
  with `node_corpus` attributed from the map.
- R19: `check_verification` over the world view recomputes across corpora and
  refuses a forged verification whose runs are in B.
- W6, W8b: the measured arms of §7.
- Drift: a record added to A after publication is in `drift()`, is `Unknown`
  to `locate`, and is not yielded by `iter_stored`.
- Refusals: each row of §6.

**N2 sabotages**, one per mechanism: map-first resolution (fall through to a
carrier scan), the absent set (treat an absent covered corpus as unknown), the
dangling-edge union (holding corpus only), the published-producers union
(inbound only), `not_present` in the lineage projection (omit it), the
three-way overlap refusal (drop one pair), and `corpus_view` routing (pass the
world view to `read_observed_facets`).

**The cut.** This design freezes as the next conformance cut under the lane
rules: the number is claimed at freeze, the runner names the highest-numbered
acceptance runner, and the N2 arms are declared as data beside it. The cut
design names `corpus.py`, `lineage.py`, `resolution.py`, `evaluation.py`,
`audit.py` and `errors.py` as shared surfaces it rewrites, per concurrency rule
3.

## 9. Open questions this design files

1. **Whether the absent set is a digest member of its own.** This slice
   reaches the belief input digest through the `lineage` member alone, and
   leaves the producer-snapshot identity as the explicit belief input the
   packaging design made it. A world with an absent corpus that no inspected
   lineage touches is therefore indistinguishable by digest from the same
   world complete. Whether the absent set should be a named member, so the
   difference shows in the inputs alone, is a question for slice 3, which
   owns the coverage and divergence clauses.
2. **Drift as an audit finding.** `drift()` is a view-level report. Whether
   the world-scale audit (slice 3) should emit it as a finding with a code, and
   whether a rebuild should be advised, is left to that slice.

## 10. Task linkage

`beliefs-d248ba` carries this spec. The implementation plan's tasks become its
children; the remaining three slices are filed as siblings under the same
parent when this slice's cut discharges, per the roadmap's one-lane rule.
