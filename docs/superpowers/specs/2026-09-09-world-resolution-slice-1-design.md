# World resolution, slice 1 — the world read view and cross-corpus traversal

**Date:** 2026-09-09, revised twice the same day after review (§11)
**Status:** approved plan; conformance cut 23 frozen 2026-09-09 before implementation
**Boundary:** `world-resolution`, slice 1 of four (`beliefs-d248ba`)
**Lane:** `world-read`, worktree `.worktrees/world-resolution`
**Sources:** `../../designs/2026-08-02-world-addressing-design.md` (§5, §5.1, §7),
`../../designs/2026-08-08-world-address-ruling.md` (§9),
`../../designs/2026-08-03-world-index-packaging-design.md` (§5.1, §5.4),
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
world, captured at an explicit publication, that the kernel's existing walks,
snapshot builders and evaluators accept beside the corpus `ReadView`; and it
makes the three absence distinctions the code has banked producible.

**Rows it closes or reads.** D3's `not-present` arm and the remainder of the
five-way non-collapse; S1 and S1a's chain crossing corpora; S5's cross-corpus
reach; W10 in full; R19's cross-corpus recomputation; R23's coverage clause.
W6 is **measured** against the surface slice 2 landed and selected as an arm
over existing code. W8b is measured but not selected: both build-time halves
failed the pre-freeze probe, and the view's own duplicate-uid refusal remains a
boundary invariant rather than a W8b selection.

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
2. **Every read is bound, and the view is a per-corpus coherent capture.**
   The view is opened at an explicit `Epoch`, never at `current`
   (`world/read.py`'s rule: nothing belief-reachable names `current`).
   Addressing goes through the epoch's address map only. The records the view
   serves are read **once**, each corpus under its own capture hold, into
   memory; nothing the view answers rereads a file. The guarantee is per
   corpus: each corpus is captured coherently, and the captures are serial, so
   the view is a sequence of coherent corpus states and not one simultaneous
   world state. That is the epoch build's guarantee too, and the stamp names
   the publication, not a moment. An address the map records resolves to its captured record or reads
   `not-present`; an address the map never observed is `unknown` whatever a
   carrier holds today. A carrier record the map does not know is **drift**:
   reported on the view, never served, never silently dropped.
3. **Absence is a named corpus, everywhere it survives.** `NotPresent` carries
   a stamp and nothing else; that is right for one answer and wrong for a
   snapshot. Every structure this slice threads absence through carries the
   absent `corpus_id` beside the reference, in an identity-encodable form, so
   two availability states never share an identity. Only a `NotPresent`
   answer enters an absence structure; a fetch that refuses — corruption, a
   stale hash, an unreadable carrier — stays a refusal and never reads as
   absence.
4. **Published evidence outlives an absent carrier, and absence gates
   divergence.** A producer set built by scanning records loses a producer with
   its carrier. The world view's producer read consults the epoch's producers
   map as well, so an absent producing run is an absent producer and never an
   empty set; and an absent producer's inputs are unknown, not empty, so no
   divergence comparison is made over it.
5. **Fetches from the capture, facet reads from the corpus, and nothing
   served is shared.** `get` and enumeration serve captured records under the
   corpus facade's validation rule, as detached copies: `Node`, its facets
   and its relations are mutable, and a caller that could reach the retained
   object could rewrite the capture behind the inbound index. A facet read
   must go through a real corpus `ReadView` (B3), so it is routed to the
   holding corpus and the complete set it returns is checked against the
   capture before it is accepted.

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
    corpus_view(ref) -> ReadView
    published_producers(dataset) -> tuple[str, ...]
    absent() -> tuple[str, ...]                 # covered corpus ids with no carrier
    drift() -> tuple[DriftReport, ...]
```

`Resolved`, `NotPresent`, `Unknown`, `Location` and `BoundStamp` are
`world/read.py`'s existing types, unchanged. `DriftReport(corpus_id,
published_state, captured_state, unmapped: tuple[str, ...])` is new and
frozen: the corpus-state identity the epoch's coverage pair recorded, the one
the capture computed, and the uids the capture holds that the map does not
record for that corpus. A corpus whose two states agree has an empty
`unmapped` and appears in no report.

`resolve` answers the live address through the map, or `None` for `Unknown`
**and** for `NotPresent` — the corpus shape has one negative and keeps it, so
a consumer that needs the distinction calls `locate`. `holds` is
`resolve(ref) is not None`. `get` locates, then serves a detached deep copy of the captured record
through the corpus facade's validation rule — `semantic-hash-stale` and
`semantic-hash-missing` refuse exactly as `ReadView.get` refuses — factored
out of `ReadView._validated` into one module-level function both call. `get`
on a `NotPresent` ref raises `RecordNotPresent(ref, corpus_id, stamp)`, a new
`errors.py` class; on `Unknown` it raises the `RefError` the corpus view would.

Every object that leaves the view is detached: `get` and `iter_stored`
return deep copies (`model_copy(deep=True)`), and `inbound` returns edges
whose `relation` is a copy. Mutating a returned object changes no later
answer. The retained records are never handed out.

`corpus_of` answers from the map alone — an absent corpus's id is still an
answer. `corpus_view` returns the holding corpus's live `ReadView`, refusing
on `NotPresent` and `Unknown`; it is the route for `read_observed_facets`,
which accepts exactly `ReadView` (B3) and keeps doing so. §5.3 says how a read
through it is held to the capture.

### 3.2 Opening: the registry under the world lock, then one capture per corpus

`open_world_view` does, in order:

1. Under one hold of the world lock through `registry._locked_barrier`,
   rescan the registry and reduce status for every `corpus_id` in
   `published.coverage`. A `duplicate-carrier` finding or an unreadable
   manifest refuses with `ResolutionRefused`, as `resolve_address` does. The
   covered ids with no present carrier are the **absent set**, fixed here.
   The lock is released before any corpus is touched: what it protects is the
   registry's presence answer, and holding it across every carrier's capture
   would put every registry append behind one enumeration, which is the cost
   `world/read.py` refuses for receipt validation.
2. For each present covered corpus, in sorted `corpus_id` order and serially,
   under that corpus's `OperationLock.capture()` — which never waits; a
   writer holding the lock refuses the open with `BuildContended`, and the
   caller retries: read the corpus-state identity, read every record, read
   the state identity again, and refuse with `CaptureDrift` if the two differ.
   This is `epoch._capture`'s discipline, applied to a read, and it is what
   makes each corpus's part of the view coherent: after the hold, nothing the
   view answers touches that carrier again. The captures being serial, the
   view as a whole is per-corpus coherent and no more (§2.2). The base-pin check `ReadView.get` performs per
   fetch runs once here, per corpus.
3. Over the captured records, check every mapped `(corpus_id, uid)` of a
   present corpus is held under the mapped address; a disagreement is
   corruption and refuses with `ResolutionRefused`. Record as drift every
   captured uid the map does not record for that corpus, and every corpus
   whose captured state identity differs from the epoch's coverage pair.
4. Build the world inbound index (§4.1) over the mapped records.

The view holds the captured, mapped records per corpus; the drift reports; the
absent set; the epoch's address and producers maps; and one live `ReadView`
per present corpus, used only by `corpus_view`.

### 3.3 Enumeration

`iter_stored` yields, corpus by corpus in sorted `corpus_id` order, every
captured record the map records for that corpus, unvalidated, as the corpus
check's iteration is unvalidated. Records of absent corpora cannot be yielded
and are not; drift records are not yielded. A consumer that wants to know what
it could not see asks `absent()` and `drift()`.

## 4. Cross-corpus edges

### 4.1 The world inbound index

`nodes` keys inbound edges by the target's local uid, so a corpus never lists
an inbound edge to an address it does not hold; it records the edge as
dangling. Neither the local inbound index nor the dangling scan is the world's
answer: the first admits a drift record as a source, and the second loses an
edge the moment a carrier acquires a drift copy of a foreign target, because
the target then resolves locally and leaves the dangling set.

The world view therefore builds its own inbound index at open, over **mapped
records only**: for every captured record the map records, for every relation
it holds, resolve the relation's target string through the **world map** —
which carries every live and retired address — and file the edge under the
resolved address. A target string the map does not record files nowhere; it
is dangling at the world layer. World `inbound(ref)` answers from this index
for a `Resolved` or `NotPresent` ref (a run in a present corpus that produces a
dataset in an absent one is found) and is empty for an `Unknown` one.

Membership is on both ends: an edge is filed only if its source is mapped, and
it is filed under an address only if the map records that address. A drift
record contributes no edge, and a drift copy of a foreign target cannot
capture one.

`producers(dataset)` needs no change of rule: `_producer_ids` scans stored
records by target string and resolves through the view, and over the world
view's enumeration and map that already spans corpora and excludes drift.

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
cannot say whether it is unknown or held elsewhere. Three changes:

**`LineageSnapshot.not_present: Mapping[str, str]`**, stored ref → corpus
id. `lineage_snapshot(view, roots)` over a world view fills it: every stored
run, ancestor or observed root whose `locate` is `NotPresent` is entered under
its `corpus_of`, and its `resolved_*` field stays `None`. Only `NotPresent`
enters; a fetch that refuses propagates out of `lineage_snapshot` unchanged.
Over a corpus view the mapping is empty, which is the snapshot as today.
`snapshot_projection` gains a `not_present` member, a list of
`{"ref": …, "corpus_id": …}` objects sorted by ref — the encoder refuses tuples
and `None`, and this is the `_ref_projection` idiom. That projection is the
`lineage` member of the belief input digest (`closure.py`), so a closure with a
not-present ancestor and one with an unknown ancestor take different digests —
R23's coverage clause, "absence within coverage gives `not-present` rather than
a silent undiverged reading".

**Absent producers.** `Producer` gains `absent: tuple[str, ...]`, empty or
the one absent corpus id, projected as `"absent": [] | [corpus_id]`.
`_producers_of(view, dataset)` over a world view unions the view's inbound
index (§4.1) with the epoch's producers map through `published_producers`. A
published run the view cannot fetch because its corpus is absent becomes
`Producer(stored_run=address, resolved_run=None, transforms=(), absent=(corpus_id,))`
and is entered in `not_present`. A published run the map records in a
**present** corpus that the capture does not hold is corruption (§3.2 step 3)
and never reaches here.

**Absence gates divergence.** `divergence_state` today compares each
producer's literal `transforms` against the `single` route; an absent
producer's `()` would read as an observed empty input set and manufacture
`lineage-divergent`, which a probe confirmed. `divergence_state` gains a third
value, `"incomplete"`, returned before any comparison when the route's run or
ancestor is in `not_present` or any producer is `absent`. `certify` treats it
as step 2b: `lineage-incomplete`, no certificate, and no `lineage-divergent`
from that dataset. `snapshot_projection`'s `divergence` member records
`"incomplete"` for that dataset, so absence never projects as divergence.

**Absent roots.** An observed root that is `NotPresent` is inspected (§5
step 1 inspects the root explicitly), has no readable basis, is entered in
`not_present`, and yields `lineage-incomplete` with no certificate.

**Where the corpus survives in the result.** `Certification.findings` is a
closed set of two codes and stays one. `Certification` gains
`absent: tuple[Absence, ...]`, with `Absence(ref: str, corpus_id: str)` frozen,
sorted by ref. `certify` fills it from `not_present` over the **references the
inspected datasets make**, not over the inspected set itself: the inspected
set holds datasets the walk reached, and a missing run or ancestor is by
definition never reached, so a filter by membership would drop exactly the
references it exists to name. The rule is: every absent root; every route's
stored run and stored ancestor of every inspected dataset's basis; and every
absent producer of every inspected dataset. Consumers that read codes read the same codes; a consumer that wants to
say which corpus is missing reads `absent`.

### 5.2 The resolution snapshot

`resolution._BoundVocabulary` today has `readable: bool` and `terms`.
It becomes:

```
state: Literal["readable", "not-available", "not-present"]
terms: frozenset[str]        # empty unless readable
absent: tuple[str, ...]      # () or (corpus_id,), not-present only
```

`build_snapshot` gains `not_present: Mapping[VocabularyBinding, str]`
(binding → corpus id) beside `readable` and `unreadable`, and refuses with
`ResolutionError` any binding named in more than one of the three — the same
refusal it makes today for readable-and-unreadable, extended to every pair.
`_BoundVocabulary.projection()` becomes `{"state": …, "terms": […],
"absent": [] | [corpus_id]}`: no `None` and no tuple reaches the encoder, and
the snapshot identity moves between the three availability states of one
binding. `resolve` answers `NOT_PRESENT` for the third state. The five outcomes
are then all producible, which is D3's remaining arm.

### 5.3 The evaluation seam

This is the one place the slice reaches into evaluation, and its members are
listed so the boundary is exact:

- `gather(view, ...)` and `evaluate_over(view, ...)` widen to
  `ReadView | WorldReadView`.
- `run_value(view, ref)` widens likewise. Its input filter `if view.holds(target)`
  keeps its meaning — an input in an absent corpus is not in the value — and
  the absence is reported rather than swallowed: `gather` collects every run
  input whose `locate` is `NotPresent`, with its corpus, into the not-present
  set `evaluate_over` reads below.
- `read_observed_facets(profile, view, target)` keeps its exact-`ReadView`
  check. Over a world view `gather` calls it with `view.corpus_view(target)`,
  which rereads the file. The read is held to the capture **after** it
  returns, on what it returned: `gather` computes from the captured record
  the complete row set `read_observed_facets` would mint over it — every
  `(address, key, payload_digest)` under the profile's facet-read rule — and
  requires the live read's row set to equal it exactly, additions and
  removals included. Any difference refuses with `CaptureDrift`. Comparing
  identities would not do: a namespaced facet can change while the record's
  address and semantic hash both stand, which a probe reproduced, and a
  comparison made before the read leaves the read itself unchecked. Comparing
  the returned set closes both.
- **Attribution.** `consulted_contracts` is keyed by assessment **value
  identity**, not by stored address, so `corpus_of` cannot attribute an
  assessment after the fact. `gather` attributes at the read: while iterating
  stored assessments it holds the stored node and records
  `corpus_of(node.id)` against `value.identity()`; runs and datasets are
  attributed by their addresses. One identity may be held in more than one
  corpus — two stored records, two addresses, one value — and both corpora's
  pins are then consulted, so `SuppliedContext.node_corpus` and
  `consulted_contracts`'s `node_corpus` become `Mapping[str, tuple[str, ...]]`,
  sorted non-empty tuples, and the consulted set is their union. Existing
  single-corpus callers and fixtures pass one-tuples.
- **Who supplies it.** Over a corpus view, `node_corpus` is supplied as
  today. Over a world view, `evaluate_over` derives it from the read and
  requires `context.node_corpus` to be **empty**; a non-empty mapping refuses
  with `MalformedRecord`, because the world says where a record is and a
  caller may not relocate one.
- `evaluate_over` over a world view returns `unavailable-corpus-absent` — the
  reason `belief.py` banked at line 84 and has never returned — when an
  observed root, a closure member or a run input is `NotPresent`, naming the
  corpus. `unavailable-input-unheld` keeps its meaning for a held record whose
  bytes are not here.

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
| a writer holds a covered corpus's lock at open | `BuildContended` at open; the open never waits |
| a corpus's state moves inside its capture hold | `CaptureDrift` at open; nothing is served |
| a present carrier disagrees with the map on a mapped uid | `ResolutionRefused` at open — corruption, never absence |
| a covered corpus has no carrier | the absent set; `NotPresent` on its addresses, never a refusal |
| a ref the map never observed | `Unknown`; no carrier is consulted |
| a carrier record the map never observed, or a carrier state the epoch did not record | a `DriftReport`; never served, never a refusal |
| `get` / `corpus_view` on `NotPresent` | `RecordNotPresent` |
| a facet read returning a row set other than the captured record's | `CaptureDrift` at `gather` |
| a binding named in two availability states | `ResolutionError` at `build_snapshot` |
| a non-empty `node_corpus` supplied over a world view | `MalformedRecord` at `evaluate_over` |
| the epoch is not this world's | `EpochUnknown`, as `open_epoch` already raises |

No refusal here may borrow `NotPresent`: that answer tells a caller the record
is safely elsewhere, and none of the rows above is that. And nothing that
refuses may enter an absence structure: `not_present`, `absent` and the
resolution snapshot's third state are filled from `NotPresent` answers only.

## 7. What this slice measures rather than builds

W6 (the three states never collapse; removing a corpus does not convert its ids
to `unknown`) is answered by `resolve_address` as it stands, and the cut selects
an arm over that code. W8b is measured and not selected: the pre-freeze probe
found that the epoch build publishes one `uid` under two addresses and refuses
one address held in two corpora with a bare `ValueError`, not the promised
`duplicate-location` finding. That defect is filed as `beliefs-fda0e5`; repair
belongs to slice 2's code outside this cut. The view still refuses a `uid` held
under two corpora at open as its own boundary invariant.

## 8. Testing and the cut

**Fixtures.** `tests/test_world_build.py` already builds a two-corpus world
with `admitted_world`, publishes an epoch with `publish`, and pins the four
rule bindings. The acceptance module for this cut reuses those helpers on the
certified volume and adds two fixtures. The **chain**: `D0 → R1 → D1 → R2 → D2` with `R1` and
`D1` in corpus B and the rest in corpus A, plus a verification in A whose two
runs are in B. The **split producer**: a dataset `D3` in A carrying a `single`
basis whose route names run `R3`, with `R3` itself in B and its `produces`
edge to `D3` recorded in the published producers map. Absence is produced by dropping B's root from the
`WorldConfig` after publication and re-opening; never by deleting records.
Drift is produced by writing to a carrier after publication.

**Arms**, each with a two-corpus positive and a corpus-local negative:

- Capture: after opening, write a record to A and edit an existing one;
  `get`, `iter_stored` and `inbound` answer the captured content and the
  first view's `drift()` is unchanged — it reports what its capture saw and
  cannot see a later write. A second open reports the new record as unmapped
  and A's state pair as disagreeing. Open while a writer holds A's lock
  refuses at once.
- Isolation: mutate a node returned by `get`, a node yielded by
  `iter_stored` and a relation on an edge returned by `inbound`; assert every
  later answer from the view is unchanged, and that the retained records are
  not the returned objects.
- W10: the world closure over the chain is complete and clean; the corpus-local
  closure from A reports `lineage-incomplete` for the same chain.
- Edges under drift: a drift record in A holding a `produces` edge to a mapped
  dataset contributes no producer and no inbound edge; a drift copy in B of a
  dataset mapped to A does not remove B's mapped run from A's dataset's inbound
  set — the edge still files under A's address through the map.
- S1/S1a: relation and lineage closures cross the edge, full rather than
  truncated; the dangling-target case is distinguishable from the crossing.
- S5 / R23 coverage: with B absent, `lineage_snapshot` enters `R1` and `D1`
  in `not_present` under B's id, `certify` says `lineage-incomplete` with
  `absent` naming B, independence is `not-certified`, and the snapshot
  projection differs from the one with B present and from one with the
  ancestor unknown.
- Absent producer, over the split-producer fixture: with B absent, `D3` and
  its `single` basis are present, its producer set is one absent `Producer`
  from the published map, `divergence_state` is `"incomplete"`, the
  projection's `divergence` member reads `"incomplete"`, `absent` names `R3`
  under B, and no `lineage-divergent` is emitted — the probe's fabricated
  divergence is the negative. With B present, the same dataset compares
  normally and is `undiverged`.
- Absent dataset, over the chain: with B absent, `D1` has no readable basis,
  is in `not_present`, and yields incompleteness without any divergence
  comparison being reached.
- Absence named: over the chain with B absent, starting at `D2`, the readable
  basis names `R2` (present) and ancestor `D1` (absent), so
  `Certification.absent` names exactly `D1` under B — `R1` sits behind `D1`'s
  unreadable basis and no walk from `D2` can discover it, which the arm
  asserts by its absence from `absent`. Over the split-producer fixture with B
  absent, `absent` names the missing run `R3` under B. Starting at `D1` itself
  with B absent names the absent root `D1`.
- Refusal is not absence: corrupt a mapped record's stamp in a present corpus
  and assert `lineage_snapshot` refuses and `not_present` is untouched.
- D3: `build_snapshot` with a `not_present` binding resolves `NOT_PRESENT`; all
  five outcomes are produced in one test and pairwise distinct; the identity
  moves across the three availability states of one binding; every pair of
  overlapping inputs refuses.
- Evaluation: `evaluate_over` over the world view with B absent returns
  `unavailable-corpus-absent` naming B; with B present it reaches a belief
  with `node_corpus` derived at the read; one assessment value stored in both
  corpora consults both corpora's pins and refuses when they disagree; a
  non-empty supplied `node_corpus` over a world view refuses; a facet-read
  target edited after capture refuses with `CaptureDrift`.
- R19: `check_verification` over the world view recomputes across corpora. A
  well-formed forged verification whose runs are in B yields a checked outcome
  carrying `verification-derivation-contradicted`; a genuine one yields none.
  A malformed record raises, as today, and the arm keeps the two apart: the
  contradiction is a finding, never a refusal, and the refusal is never read
  as a finding.
- W6: the measured arm of §7. W8b remains measured and not selected; the
  view's duplicate-uid refusal is a boundary-invariant arm.
- Refusals: each row of §6.

**N2 sabotages**, one per mechanism: map-first resolution (fall through to a
carrier scan), the absent set (treat an absent covered corpus as unknown), the
capture (serve `get` from the live carrier), the inbound index's source
membership (file drift sources), its target resolution (resolve targets through
the local index), the published-producers union (inbound only), divergence
gating (compare over an absent producer), `not_present` in the lineage
projection (omit it), the three-way overlap refusal (drop one pair), attribution
at the read (attribute after the fact through `corpus_of`), `corpus_view`
routing (pass the world view to `read_observed_facets`), the facet-set
comparison (compare identities instead of the returned rows), boundary
isolation (return the retained node), and absence collection (filter
`not_present` by the inspected set).

**The cut.** This design freezes as the next conformance cut under the lane
rules: the number is claimed at freeze, the runner names the highest-numbered
acceptance runner, and the N2 arms are declared as data beside it. The cut
design names `corpus.py`, `lineage.py`, `resolution.py`, `evaluation.py`,
`belief.py`, `consulted.py`, `audit.py` and `errors.py` as shared surfaces it
rewrites, per concurrency rule 3.

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

## 11. Review log

**2026-09-09, six findings, all resolved in this revision.** (1) Opening
gave no point-in-time view: `Corpus.get` rereads the file and the world lock
excludes no corpus writer — the view is now a per-corpus capture under
`OperationLock.capture()` with `CaptureDrift` (§2.2, §3.2). (2) The inbound
union admitted drift sources and lost an edge when a carrier acquired a drift
copy of a foreign target — replaced by a world inbound index built over mapped
records with targets resolved through the world map (§4.1), with edge-level
drift arms (§8). (3) An absent producer's empty `transforms` fabricated
`lineage-divergent`, confirmed by probe — `divergence_state` gains
`"incomplete"` and absence gates the comparison; only `NotPresent` enters an
absence structure (§2.3, §2.4, §5.1). (4) `consulted_contracts` is keyed by
assessment value identity, which the map cannot resolve — attribution happens
at the read, identities held in two corpora consult both, and a supplied
`node_corpus` over a world view is refused (§5.3). (5) `Certification.findings`
is a closed code set — `absent` is a separate field (§5.1). (6) `None` and
tuples fail the identity encoder, confirmed by probe — every new projection
member uses the `[] | [value]` and object-list idioms (§5.1, §5.2).

**2026-09-09, second review, five findings, all resolved.** (1) Comparing a
record's content identity before a facet read neither bound the facet payload
— a namespaced facet can change under an unchanged address and semantic hash,
reproduced — nor closed the window; the live read's complete row set is now
compared to the rows the captured record would mint, after the read (§5.3),
and the limitation is withdrawn. (2) `Node` and its parts are mutable, so
serving retained objects let a caller rewrite the capture behind the inbound
index — the boundary returns detached copies, with an isolation arm (§2.5,
§3.1, §8). (3) Filtering `not_present` by the inspected set dropped every
missing run and ancestor, since the walk never reaches them — absence is
collected from the inspected datasets' route and producer references and the
absent roots (§5.1). (4) The capture arm expected an open view to report a
later write; it reports what it captured and the second open reports the
drift (§8). (5) The absent-producer arm had removed the `single` basis its
comparison needs — a split-producer fixture keeps the dataset and basis
present with the run in the absent corpus, and the absent-dataset case is its
own incompleteness arm (§8). The guarantee is stated as per-corpus coherent
capture throughout (§2.2, §3.2).

**2026-09-09, third pass, two acceptance details.** The absence-named arm
named a run no walk from its root can reach; it now names what each root can
discover and takes the missing run from the split-producer fixture. The R19
arm asserted a refusal where a well-formed forgery is a
`verification-derivation-contradicted` finding; the arm keeps finding and
refusal distinct (§8). No architectural finding remained; the design proceeds
to planning.
