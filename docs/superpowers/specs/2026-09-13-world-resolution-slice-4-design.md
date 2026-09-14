# World resolution, slice 4 — view evaluation and the W8/W8b discharge

**Date:** 2026-09-13, revised three times 2026-09-14 after review (§11)
**Status:** approved 2026-09-14 at `0e8600b`; amended at plan review (§11 third entry)
**Boundary:** `world-resolution`, slice 4 of four (`beliefs-d248ba`); task `beliefs-0e523a`
**Lane:** `world-read`, worktree `.worktrees/world-resolution-slice-4`
**Sources:** `../../designs/2026-08-02-world-addressing-design.md` (§5, §7: W7, W8, W8b),
`../../designs/2026-08-08-world-address-ruling.md` (§4.3, §5.4),
`../../designs/2026-08-31-coordination-and-view-kinds-design.md` (§2, §6.2),
`2026-08-29-user-and-autonomy-layer-design.md` (§4.2, §4.4, §6.1, §8 item 5),
`2026-09-09-world-resolution-slice-1-design.md` (§1, §2, §3, §6, §7),
`2026-09-10-world-resolution-slice-2b-design.md` (§7, §12, §13),
`2026-09-13-world-resolution-slice-3-design.md` (§2 item 5, §11 item 3),
`../../plans/2026-08-29-implementation-roadmap.md` (Appendix B, concurrency rules)
**Measured against:** `main` at `98b92ec`

## 1. What this slice is

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

**Rows it closes or reads.** W7 closes. W8b closes. W8 is read in part:
its duplicate-location and address-conflict conflicts are selected; its
ambiguous-search-term conflict cannot run without the pinned authority
snapshot (ledger artifact 11, owed and undesigned) and is deferred to
`authority-labels` with the W9 arm it restates (§8).

**Rows it does not touch**, each named to its owner: W9 and W14
(`authority-labels`, tier 3 — §8 records why slice 2b's assignment of W14
to this slice does not stand); R23's rules-store clauses and W8a's
`instrument-certification` arm (`contract-cut`); dataset addressing
(`beliefs-48214e`) and divergent-history reconciliation (`beliefs-24b42b`),
which stay filed under `beliefs-d248ba` and are not prerequisites here.
`packaging-remainder` closed at cut 27 and is confirmed closed, not audited
again.

## 2. Decisions

1. **The evaluator is a pure function of `(query, view)` and opens
   nothing.** `evaluate_query(view: WorldReadView, query: ViewQuery)` takes
   a parsed query and an already-open world view and returns a
   `Selection`. It never opens a view, never names `current`, never reads a
   coordination record and never consults a profile or a resolution
   snapshot: the record is the caller's to resolve live (view-kinds §6.2),
   and every fact the answer depends on is in the capture. Two callers
   holding the same epoch and the same query get the same `Selection`, and
   its projection carries the packaging identity so a selection at another
   epoch has another identity. That equality needs one more refusal: the
   view serves the *captured* contents of every mapped record, and the open
   checks a mapped record's address, not its content, so a record edited
   after publication is served as edited and reported as drift, never
   refused. Two opens at one epoch can therefore hold different relations
   under one stamp, and a selection over either would be complete. The
   evaluator refuses a view whose capture moved at entry (§3.2), so a
   selection carries the epoch's stamp only when the capture is the epoch's
   state. The signal is the corpus-state pair on each `DriftReport`: a
   report whose captured state equals the published one lists records the
   map never held by construction — coordination and prose kinds, which the
   epoch captures for state identity and never addresses (view-kinds
   §11.5) — and every ordinary topic world carries one; it is not drift of
   the capture and does not refuse. The
   evaluator takes `WorldReadView` only —
   not the `ReadView | WorldReadView` union the walks accept — because a
   corpus-local selection is the `fb-2026-07-30-019` defect W7 exists to
   refuse, and a function that accepted both would let a consumer reach it
   by annotation.
2. **Each predicate denotes exactly, and a failure to look never denotes
   the empty set.** `kinds` denotes the mapped records of those kinds in
   present corpora. `references-term` denotes the propositions whose stored
   claim facet holds the term as an argument or a qualifier restriction,
   by exact string equality on the stored identifier — the claim layer's own
   rule (`identifiers.py`: no normalization) — with no profile and no
   vocabulary consulted, so the denotation is a function of the capture
   alone. `closure` denotes the reach from the anchor by the named
   predicates in the stated direction, excluding the anchor. `addresses`
   denotes the located records, a retired address resolving to its record
   and two addresses of one record selecting it once. An anchor or
   enumerated address whose `locate` is `Unknown` or `NotPresent` refuses
   the evaluation naming the address and the state, and the two states never
   share a reason (W6). This is view-kinds §2.2's pinned rule made concrete.
3. **Absence and dangling are reported on the selection, never folded into
   it.** A `kinds` or `references-term` predicate over a world with an
   absent covered corpus scans what is present; a closure step whose target
   is `NotPresent` or `Unknown` is skipped and reported, as `traversal.closure`
   already does. The `Selection` carries the absent corpus ids and every
   unresolved step with its locate state and corpus, and `complete` is
   derived from them. Only a complete selection is *the* selection of
   `(query, epoch)`; an incomplete one has a different projection and
   identity, so two installations cannot agree on a selection one of them
   could not see whole. `publish` refuses an incomplete selection at its own
   boundary (§3.5); `next` may show one, saying so. The world view's inbound
   adjacency silently drops an edge from an absent corpus's record
   (`RelationAdjacency._inbound` skips `source_uid is None`); the evaluator's
   inbound walk reports that source as a not-present step instead, because a
   selection that lost a member without a word is the defect the slice-1
   drift rules exist to refuse.
4. **A record the read would refuse refuses the evaluation.** Every
   selected record and every record whose facet the evaluator reads passes
   the corpus facade's validation rule (`validated_node`), so a stale or
   missing semantic hash refuses here exactly as `get` refuses. A
   proposition whose claim facet is malformed under a `references-term` scan
   refuses naming the record; it is corruption, and corruption is never read
   as "does not reference". A view opened in report mode with a damaged
   corpus refuses at entry, because a damaged corpus cannot be enumerated
   honestly and `iter_stored` would silently omit it.
5. **The selection is a value with a projection and an identity.** Selected
   addresses are the live addresses, sorted; contributing corpus ids are
   sorted; absent corpora and unresolved steps are sorted. The projection is
   `science.view-selection.v1` over the packaging identity, the query
   projection and those four members, and the identity is `v1.digest` over
   it. `publish` freezes the selection list from that epoch (user layer
   §6.1); this is the value it freezes.
6. **W8b is selected over existing code, and W8 in part.** No new conflict
   handling is built. The arms run the build refusal, `consolidate`'s
   repair and refusals, and `move`'s occupied-destination refusal as they
   stand, on the certified volume, with N2 sabotages at each site. W8's
   search-term conflict is deferred, not deemed run.

## 3. The evaluator

### 3.1 Module and surface

New module `beliefs/world/selection.py`, exported from `beliefs.world`:

```
evaluate_query(view: WorldReadView, query: ViewQuery) -> Selection

@sealed @final @dataclass(frozen=True)
class Selection:
    stamp: BoundStamp                      # the view's; names the publication
    query: ViewQuery
    selected: tuple[str, ...]              # live addresses, sorted
    contributing: tuple[str, ...]          # corpus ids holding a selected record, sorted
    absent: tuple[str, ...]                # the view's absent set
    unresolved: tuple[Unresolved, ...]     # closure steps that reached nothing, sorted
    @property complete -> bool             # not absent and no not-present step
    def projection(self) -> dict[str, object]
    def identity(self) -> str              # v1.digest("science.view-selection.v1", projection)

@final @dataclass(frozen=True)
class Unresolved:
    source: str                            # the record whose relation was walked
    predicate: str
    target: str                            # the stored target string
    state: Literal["not-present", "unknown"]
    corpus_id: str | None                  # the absent corpus, not-present only
```

`view_query.py` gains `stored_query(node: Node) -> ViewQuery`: the parsed
query of a stored view revision, read from the coordination facet's `query`
member through `parse_view_query`. A node that is not a view kind, or whose
facet carries no `query`, refuses with `MalformedRecord`; the write boundary
already guarantees the stored form parses, so a parse failure here is
corruption and propagates as the `ValueError` `parse_view_query` raises,
wrapped in `MalformedRecord` naming the node. This is the only bridge from a
record to a query, and it reads the record the caller resolved live.

`Selection.projection()` is:

```
{"version": "science.view-selection.v1",
 "epoch": <stamp.packaging_identity>,
 "query": <query.projection()>,
 "selected": [...], "contributing": [...], "absent": [...],
 "unresolved": [{"source": …, "predicate": …, "target": …,
                 "state": …, "corpus_id": [] | [corpus_id]}, ...]}
```

No `None` and no tuple reaches the encoder (the slice-1 idiom). `complete`
is not a member: it is derived from `absent` and `unresolved`, and a
derived member in the projection would be a second copy that could
disagree.

### 3.2 Evaluation

`evaluate_query` does, in order:

1. Refuse if `view.damaged()` is non-empty: `SelectionRefused("corpus-damaged")`
   naming every damaged corpus. A damaged corpus is excluded from
   `iter_stored`, and a scan that ran over the remainder would answer for a
   world it did not see. Then refuse if any `DriftReport` carries
   `captured_state != published_state`: `SelectionRefused("corpus-drifted")`
   naming every such corpus. A moved capture is a state the epoch did not
   publish; the route is a rebuild and an evaluation at the new epoch. A
   report whose two states agree names only records outside the world map
   (decision 1) and does not refuse. Damage is checked first because a
   damaged corpus has no state identity to compare.
2. `locate` every address the query names — each `addresses` member and
   each `closure` anchor, across all clauses — before any denotation is
   computed. If any is `Unknown`, refuse `SelectionRefused("address-unknown")`
   naming every unknown address, sorted; otherwise, if any is `NotPresent`,
   refuse `SelectionRefused("address-not-present")` naming every such
   address and its corpus. The two states never share one refusal, and a
   refusal never names only the first offender. Anchor and enumerated
   address take the same reasons: what the caller needs is the address and
   its state, and the role is visible in the query it holds.
3. Denote each predicate as a set of live addresses:
   - `kinds`: every record `iter_stored` yields whose `kind` is in the set.
   - `references-term`: every `proposition` whose claim facet holds the
     term in `args` or as a qualifier's `restriction`. Each candidate
     proposition passes `validated_node` **before** its facet is read, so a
     stale or missing semantic hash refuses whether or not the edited claim
     would have matched — the scan is a facet read, and §2.4 admits no
     unvalidated facet read. The facet's shape is then checked by
     `decode.stored_claim_terms(node)`, the profile-independent shape check
     factored out of `claim_from_stored` — the five keys, `args` a sequence
     of identifiers, every qualifier body exactly `quantifier` and
     `restriction` — which returns the argument and restriction terms, and
     its `MalformedWireClaim` refuses with
     `SelectionRefused("record-malformed")` naming the record. No decode
     against a profile is performed: the term is compared as stored.
   - `closure`: `traversal.closure(live, adjacency)` from the anchor's
     **live** address — `view.resolve(anchor)`, which step 2 has already
     shown is `Resolved` — over a composite adjacency (§3.3); its `reached`
     set, which excludes the anchor's record. The walk seeds its visited
     set with the literal start, and every step resolves to a live id, so
     a retired address passed as-is would let a cycle back to the anchor
     select the anchor itself.
   - `addresses`: the `Resolved` records' live ids.
4. Intersect within a clause, union across clauses (view-kinds §2.1).
   `clauses: []` denotes the empty selection and is not a refusal.
5. Validate every selected record through `validated_node` on the
   captured record — a `kinds` or `closure` member is selected by its kind
   or its edges and has not been read as a facet yet — and let a refusal
   propagate unchanged. Record the holding corpus of each through
   `corpus_of`.
6. Build the `Selection`: sorted members, the view's `absent()`, the
   unresolved steps collected in step 3.

Every scan is over the mapped records of present corpora — the set
`iter_stored` yields — read through a module-private accessor the view
exposes within `beliefs.world` without copying, since the evaluator hands
out addresses and never a record; slice 1's isolation rule is about what
leaves the boundary, and nothing does here. Drift records are never
selected and a record of an absent corpus cannot be.

### 3.3 The closure adjacency

`closure` starts at the anchor's live address (§3.2 step 3) and walks
`RelationAdjacency(view, predicate, "outbound")` for
`out`, an evaluator-owned inbound adjacency for `in`, and both for `both`,
one adjacency per named predicate, composed by concatenating their steps in
predicate order then direction order. `traversal.closure` is unchanged:
cycle-safe, start-excluding, skip-and-report.

The outbound adjacency is the corpus one, because its `resolve` already
answers `None` for both non-resolving states and the evaluator classifies
each unresolved entry afterward through `locate` on the entry's target.
The inbound adjacency is the evaluator's own: over `view.inbound(ref)`
filtered to the predicate, an edge with a held source steps to it, and an
edge whose `source_uid` is `None` — a mapped source in an absent corpus —
yields a step with `resolved=None` whose entry names the source, so it is
reported as `not-present` under that corpus rather than dropped. A relation
whose target string the world map does not record files no inbound edge at
all (slice 1 §4.1) and is reachable only outbound, where it reports
`unknown`.

Prose kinds are not world kinds and hold no address in the map, so a
relation to one is `unknown` at the world layer and never selected; the
evaluator adds no rule for them.

### 3.4 Refusals

```
class SelectionRefused(ScienceError):
    REASONS = ("corpus-damaged", "corpus-drifted", "address-unknown",
               "address-not-present", "record-malformed")
    reason: str
    refs: tuple[str, ...]        # sorted addresses, records or corpus ids
    corpus_ids: tuple[str, ...]  # not-present reasons: the absent corpora, sorted
```

One class, a closed reason set, the offending references sorted — the
`IdentifierMalformed` shape. No reason borrows `NotPresent`, `Unknown` or
`RecordNotPresent`: those say where a record is, and a refused evaluation
says the question could not be answered.

### 3.5 What the consumers read

`publish(view, destination)` (user layer §6.1) resolves the view record
live, reads its query with `stored_query`, opens the world view at the
frozen epoch, calls `evaluate_query`, and refuses `Refused(empty-selection)`
on an empty `selected` and — new here, and the rule this slice pins for it —
refuses an incomplete selection naming the absent corpora and not-present
steps, since a publication of a selection the publisher could not see whole
would publish a different corpus at every installation. `closure-incomplete`
and `pins-disagree` remain `publish`'s own checks over `selected` and
`contributing`. `next` (user layer §4.4) evaluates the current project's
query at the newest epoch and reads `selected`; what it ranks is
`science`'s. Neither consumer is built here.

## 4. The W8 and W8b discharge

The three §5 conflicts and the two W8b violations are already handled on
`main`; this slice reads them as arms. Each arm asserts its own handling and
that no precedence is applied: the same inputs registered, mounted or
supplied in the other order give the same finding with the same claims, and
where a repair is offered it is authored (`keep` is an argument), never
inferred.

### 4.1 W8 — no conflict is resolved by precedence

- **Duplicate location.** Two records at one canonical address in two
  corpora: `build_epoch` refuses with `AddressMapConflict` whose finding is
  `duplicate-location`, whose detail names both `(corpus, uid)` claims in
  the capture's sorted order and no preferred carrier, and no epoch is
  published; the same code, ref and claims in the other registration
  order. `consolidate(keep, other)` repairs it with the
  authored survivor, the rebuild publishes, the view serves one record;
  swapping `keep` gives the mirror outcome. Thereafter `move` into the
  occupied destination refuses `DuplicateLocation` before any intent.
  **Selected.**
- **Ambiguous search term.** A term the pinned authority snapshot maps to
  two identifiers refuses naming both. No pinned snapshot exists to decide
  against (ledger artifact 11); the arm is W9's restated, and the roadmap
  homes W9 in `authority-labels`. **Deferred to `authority-labels`**, with
  the cut naming it as W8's unrun arm. Under the any-unrun-arm rule W8 is
  partial, and the accounting says so instead of leaving the row "never
  selected" a fifth time.
- **Address conflict.** One derived address, disagreeing bases: two
  `source` records at one address (same selected identifier, hence one
  digest) whose identifier maps differ. The build refuses
  `duplicate-location` at the address before any basis is read;
  `consolidate` refuses `HistoryDisagreement` and writes nothing, whichever
  record is `keep`; and a source whose stored id is not its derived address
  refuses `SourceAddressDisagreement` at the write boundary. No survivor's
  basis wins. **Selected.** Reconciling the histories is `beliefs-24b42b`,
  filed, and not this arm's claim.

### 4.2 W8b — world `uid` uniqueness, two violations distinguished

Over `derive.address_map` and `consolidate` as they stand:

- one `uid` under two canonical addresses: `uid-corruption`, the message
  offers no repair, and `consolidate` over the pair refuses
  `AddressDisagreement` — the operation is unavailable, not merely
  unadvised;
- two records at one canonical address in two corpora, run twice, sharing a
  `uid` and with distinct `uid`s: `duplicate-location` both times, the same
  code and ref;
- corruption outranks duplication when one `uid` does both;
- negative: each corpus's own `corpus_check` reports neither — the
  invariant is the world's, and a corpus cannot see it.

The unit coverage exists (`test_world_derive.py`, `test_world_epoch.py`,
`test_relocation.py`); the cut adds the durable arm on the certified volume
and the N2 declarations, which is what selection is.

## 5. Refusals

| condition | answer |
|---|---|
| the view has a damaged corpus | `SelectionRefused("corpus-damaged")` at entry |
| a drift report's captured state differs from the published state | `SelectionRefused("corpus-drifted")` at entry, every such corpus named; rebuild, then evaluate at the new epoch |
| a drift report whose states agree (records outside the world map) | not a refusal; the records are never selected |
| an address the query names is `Unknown` | `SelectionRefused("address-unknown")`, every such address named |
| an address the query names is `NotPresent`, none `Unknown` | `SelectionRefused("address-not-present")`, every such address and its corpus named |
| a proposition's claim facet is malformed under `references-term` | `SelectionRefused("record-malformed")` naming the record |
| a selected record fails the facade's validation rule | the facade's refusal, unchanged |
| a closure step reaches `NotPresent` or `Unknown` | reported in `unresolved`; never a refusal, never dropped |
| a covered corpus has no carrier | reported in `absent`; `complete` is false |
| `clauses: []` | an empty, complete selection |
| a stored view node without a query | `MalformedRecord` from `stored_query` |
| `evaluate_query` given anything but a `WorldReadView` | `TypeError` at entry, checked at runtime; the evaluator is world-only |

No refusal borrows `NotPresent`, and nothing that refuses enters `absent` or
`unresolved`.

## 6. What this slice measures rather than builds

W8's two selected conflicts and W8b are read over code that landed at cuts
16, 23 and 25 and in `beliefs-fda0e5`; nothing in `derive.py`,
`relocation.py` or `world/view.py` changes. The world view's duplicate-uid
refusal at open stays slice 1's boundary invariant and is not read as
W8b's build half (slice 3 §11 item 3): W8b's arms run the build, not the
open.

## 7. Testing and the cut

**Fixtures.** The two-corpus world of `test_world_view.py` (`ALPHA`, `BETA`)
gains a **topic** fixture: a coordination contract pinned in `ALPHA` under
the reserved namespace, a `project` record and a `topic` record in `ALPHA`
whose query names records in `BETA` — by `addresses`, by `kinds`, by
`closure` from a run in `ALPHA` over `produces` to a dataset in `BETA`, and
by `references-term` against a proposition in `BETA` whose claim facet
carries the term. Absence is produced by dropping `BETA`'s root from the
config after publication; a dangling target by a relation to an address the
map never recorded; a not-present inbound source by a relation stored on a
present `ALPHA` record whose declared `source` is `BETA`'s run — the world
inbound index files an edge only from held records, so the edge must live on
the record that stays. The W8/W8b fixtures are the duplicate-address
and shared-uid worlds `test_world_epoch.py` builds, and a pair of `source`
records at one address with differing identifier maps.

**Arms**, each with a two-corpus positive and a corpus-local or
order-reversed negative:

- W7, one arm per predicate form, each a topic record in `ALPHA` whose
  query reaches `BETA`, each complete and each with the identity equal
  across two opens at the same epoch:
  - `addresses` naming `BETA`'s dataset selects exactly it; `contributing`
    is `(BETA,)` — the topic's own corpus contributes nothing, since a
    coordination record is never selected;
  - `kinds: [dataset]` selects `ALPHA`'s and `BETA`'s datasets;
    `contributing` is `(ALPHA, BETA)`;
  - `closure` from `ALPHA`'s run over `produces`, `out`, selects `BETA`'s
    dataset and not the run; `contributing` is `(BETA,)`;
  - `references-term` selects `BETA`'s proposition, never a dataset;
    `contributing` is `(BETA,)`;
  - one query with two clauses, `addresses` over `ALPHA`'s dataset and
    `references-term` over `BETA`'s proposition, selects both and
    contributes both.
  Negative, with `BETA` absent: the `addresses` form refuses
  `address-not-present` naming `BETA`; the `closure` form from `ALPHA`'s
  run still resolves its anchor, reaches nothing, and returns an
  incomplete selection with one `not-present` unresolved step naming the
  dataset under `BETA` and `BETA` in `absent`; the `kinds` form returns an
  incomplete selection with `BETA` in `absent`. Each incomplete identity
  differs from the complete one — never the empty set, never `unknown`.
  A sixth form, `closure` anchored at `BETA`'s dataset over `produces`,
  `in`, selects `ALPHA`'s run when `BETA` is present and refuses
  `address-not-present` naming the anchor under `BETA` when it is absent:
  the missing-anchor refusal, distinct from the traversed-target report.
- Drift: edit a mapped record's relations in `BETA` after publication and
  reopen at the same epoch; the second open reports drift on `BETA` and
  the evaluation refuses `corpus-drifted` naming it, while the first open,
  captured before the edit, still evaluates. Negative: the rebuilt epoch
  evaluates clean and its selection identity differs from the first's; and
  the ordinary topic world, whose coordination records make every open
  report unmapped uids under equal states, evaluates without refusal.
- Projection members: `absent` and `unresolved` are asserted as projected
  literals, not only through identity inequality — `selected` and
  `contributing` also move when a corpus goes absent, so inequality alone
  cannot show the member is present. For `absent`, `clauses: []` with and
  without `BETA` selects nothing both times and the identities differ.
- Determinism: the same query with clauses and predicates authored in
  another order, and the corpora registered in another order, gives an
  identical projection.
- Closure: `out`, `in` and `both` over the chain; the anchor is excluded;
  a dangling target is reported `unknown`; an absent inbound source is
  reported `not-present` under `BETA` and not dropped; a retired address
  as anchor over a cycle `A → B → A` selects exactly `B`, the same as the
  live anchor does.
- Addresses: a retired and a live address of one record select it once.
- References-term: a term in an argument slot and one in a qualifier
  restriction both select; a proposition with a malformed facet refuses
  naming it; a term absent everywhere selects nothing and refuses nothing.
- Validation: a selected record with a stale semantic hash refuses; a
  proposition whose stale-hash edit removed the requested term from its
  arguments refuses under `references-term` rather than yielding an empty
  selection — the corrupt non-match is the arm, and it is written so that
  the unvalidated scan would pass it.
- Damage: a report-mode view with a damaged corpus refuses at entry.
- Empty: `clauses: []` is complete and empty.
- W8 duplicate location, address conflict; W8b's four arms; §4 as written.
- Refusals: each row of §5.

**N2 sabotages**, one per mechanism: the entry damage check (skip it);
the entry drift check (skip it); address pre-check (denote an unknown
address as empty); not-present collapsed into unknown (one reason for
both); clause composition (intersect across clauses); closure anchor
included; closure started from the literal anchor string; inbound absent
source dropped (use `RelationAdjacency` inbound as-is); unresolved omitted
from the projection; `absent` omitted from the projection; selected
records served unvalidated; candidate propositions read unvalidated;
`references-term` matched on arguments only;
`references-term` normalized before comparison; world-only typing widened
to `ReadView`; and for W8/W8b: the uid check dropped, the address check
dropped, addresses checked before uids (corruption masked as duplication),
`duplicate-location` keyed on `uid` equality, `consolidate` accepting two
addresses, `consolidate` choosing a survivor when histories differ, `move`
overwriting an occupied destination.

**The cut.** This design freezes as **conformance cut 28**, numbered after
cut 27 and serialized after its discharge, which is in the branch ancestry.
`PREFIX_RUNNERS = ("cut27_acceptance.py",)`; `PHASE_MODULES =
("test_world_selection_acceptance.py", "test_n2_cut28.py")`. Declaration
units `W7`, `W8` and `W8b`. W8's search-term arm is named in §3 of the cut
as deferred to `authority-labels`. The cut names `errors.py`,
`view_query.py`, `decode.py`, `world/__init__.py`, `python/tools/roadmap_status.py`,
`python/tests/test_designs_corpus.py`, the ledger, the roadmap and the guide
index as shared surfaces it rewrites, per concurrency rule 3; `corpus.py`,
`derive.py`, `relocation.py` and `world/view.py` are read and not rewritten.

## 8. Adjudications this slice records

1. **W14 stays in `authority-labels`.** Slice 2b §12 and §13 assigned the
   label renderer and W14 to "slice 4's read side". The roadmap's boundary
   index and Appendix B home W9 and W14 in `authority-labels`, tier 3,
   blocked on artifact 11, and the ledger's owner row agrees. The roadmap
   is the ranking's source of truth (roadmap §Boundary index); a renderer
   without a pinned snapshot to render against could only assert invariance
   over a snapshot that does not exist. Slice 2b's design is amended with a
   dated note pointing here; nothing else moves.
2. **W8's remainder is re-homed at discharge.** After cut 28 W8 is partial
   on one arm, the ambiguous-search refusal, which is W9's arm under
   another row. The results record and the re-rank move that remainder to
   `authority-labels` beside W9, so `world-resolution` retains no guarantee
   row and only its two filed follow-ups; `beliefs-d248ba` stays open for
   those and closes when they land or are explicitly re-filed elsewhere.
3. **`packaging-remainder` is closed**, confirmed against cut 27's
   accounting; the task text's "audit all packaging-remainder labels" is
   discharged by that confirmation.

## 9. Open questions this design files

1. **Whether `next` needs an index.** Every predicate is an `iter_stored`
   scan over the capture, which is what a per-corpus coherent capture
   affords and what a dogfood-sized world costs nothing for. A world where
   `next` at every command is too slow would want a per-epoch kind and
   term index derived at publication; that is a packaging question, not an
   evaluation one, and is filed for the `publish` lane's evidence.
2. **A closure-over-selection predicate.** View-kinds §2.5's no-join
   limitation stands; this slice adds no v2 predicate. `publish`'s
   `closure-incomplete` refusal is the evidence that would open one.

## 10. Task linkage

`beliefs-0e523a` carries this spec (`tasks edit --spec`). The
implementation plan's tasks become its children. `beliefs-d248ba` remains
open for `beliefs-48214e` and `beliefs-24b42b`. Lane admission is recorded
on the task: slice 3 merged at cut 27, no kernel lane open, this is the
on-path head (roadmap rule 6).

## 11. Review log

**2026-09-14, first review, four findings, all resolved in this revision.**
(1) The open verifies a mapped record's address and not its content, so a
record edited after publication is served as edited and reported as drift;
two opens at one stamp yielded different closures with neither absent nor
damaged, reproduced — the evaluator now refuses a drifted view at entry
with `corpus-drifted` (§2.1, §3.2, §3.4, §5, §7). (2) `traversal.closure`
seeds its visited set with the literal start while every step resolves to
a live id, so a retired anchor over a cycle selected the anchor's own
record, reproduced — the walk starts from the anchor's live address, with a
retired-anchor cycle arm (§3.2, §3.3, §7). (3) The ordered algorithm
validated only selected records while `references-term` read facets off
unvalidated held records, contradicting §2.4; a stale edit removing the
term produced an empty selection without refusal — every candidate
proposition is validated before its facet is read, with a corrupt
non-match arm (§3.2, §7). (4) The W7 arm claimed the dataset was found
"under each predicate form" and that `contributing` named both corpora,
but `references-term` selects propositions and an `addresses` query over
`BETA` contributes `BETA` alone — the arm now states each form's selected
records and contributing corpora separately (§7).

**2026-09-14, second review, one finding, resolved.** The W7 negative had
the `closure` form refusing `address-not-present` with `BETA` absent, but
its anchor is `ALPHA`'s run and stays resolved; only the traversed dataset
is `NotPresent`, which §3.2 reports as an unresolved step — reproduced
against the existing traversal. The negative now expects an incomplete
selection with one not-present step, and a sixth form anchored at `BETA`'s
dataset carries the missing-anchor refusal (§7).

**2026-09-14, plan review, three amendments to this spec.** (1) Every
ordinary topic world reports drift: the view lists coordination records as
unmapped uids under equal corpus states, reproduced with a fresh project
record — the refusal now keys on `captured_state != published_state`, and
an equal-state report names records outside the map by construction
(§2.1, §3.2, §5, §7). (2) The claim-shape check as written admitted a
qualifier lacking `quantifier` — the shape check is `decode`'s own,
factored into `stored_claim_terms` (§3.2, §7 shared files). (3) The
absent-inbound fixture carried the edge on the absent run, which the
inbound index never files — the edge lives on the present record with a
foreign `source` (§7).
