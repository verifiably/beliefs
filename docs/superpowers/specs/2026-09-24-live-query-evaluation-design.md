# Live view-query evaluation — design

**Status:** draft for review, 2026-09-24. **Task:** `beliefs-cc0aea`.
**Requested by:** science's coordination command set design
(`science docs/specs/2026-09-24-coordination-command-set-design.md`, §8 S1,
decision 3, §5.5).
**Amends:** the coordination and view kinds design
(`docs/designs/2026-08-31-coordination-and-view-kinds-design.md`, §6.2), and adds to
world resolution slice 4's evaluator (`world/selection.py`).

## 1. Problem

`evaluate_query` denotes a `ViewQuery` only over a `WorldReadView`, which is opened at
a published epoch. It refuses `corpus-drifted` as soon as any covered corpus has moved
past that epoch. No science command may publish (science framework §4.4). A project's
`next` reads its project's query, so it would refuse after the first write in a
session and stay refused until an operator republished.

The queue is attention, not belief input. Coordination §6.2 gives the reason
coordination records resolve live: "no packaging step mediates seeing your own task
edit". The same reason covers seeing your own new proposition in your project's
queue. Science therefore asks for a query evaluation over the corpora's current state,
with no epoch built or published. The result must be stamped so that no consumer can
take it for an epoch-bound answer. Publishing and every epoch-bound read stay as they
are.

## 2. Decisions

1. **One function and a result type of its own, not a view.** The surface is
   `evaluate_live_query(world, query) -> LiveSelection`. It captures, denotes and
   returns. Science needs only the selection, and a public live view would invite the
   belief-adjacent reads §6.2 keeps epoch-bound.
   *Rejected:* a public `LiveWorldView` that `evaluate_query` would also accept.
   *Rejected:* widening `BoundStamp`, and the `Resolved`, `NotPresent` and `Unknown`
   types that carry it, to admit a capture stamp. Every epoch-bound consumer would then
   have to rule the capture case out.

2. **`LiveSelection` is a separate sealed type with a separate stamp.** It carries a
   `CaptureStamp(world_id, coverage)`, where `coverage` is the sorted
   `(corpus_id, corpus_state)` pairs captured, and no packaging identity. Its
   projection is versioned `science.live-selection.v1` and carries `capture` where
   `Selection` carries `epoch`. A consumer typed for `Selection` cannot receive one,
   and no live identity can collide with an epoch-bound one. `Unresolved` is shared,
   since it names a step, not a stamp.

3. **Live coverage is every corpus the world admits with no terminal status.** An
   epoch declares its coverage at build, and a live read has no declaration. The
   registry's live admitted set is the world's own answer to "which corpora are in
   this world", and science's world already admits its corpora. Each corpus in the set
   resolves to present or absent the way `open_world_view` resolves it: an unreadable
   manifest, or more than one carrier, refuses `ResolutionRefused` with the same
   messages. Absent corpora are listed in `absent`, so `complete` is false.

4. **An address in an absent corpus is `unknown` to a live read.** An epoch records
   the addresses of corpora that later go absent, and this is what makes `NotPresent`
   possible. A live capture has only what it read, so nothing it holds records an
   absent corpus's addresses. A query naming one refuses `address-unknown`, and a
   dangling closure step toward one is classified `unknown`. Borrowing the latest
   epoch's address map for absent corpora would mix the two regimes this design keeps
   apart. `address-not-present` is therefore never raised on this path.

5. **Coherence is per corpus, as a build's is.** Each present corpus is captured
   inside its own operation-lock `capture()` hold: state identity, one enumeration,
   state identity again, serially, in sorted corpus order. A state that moves inside
   the hold raises `CaptureDrift` and discards the whole evaluation, with no retry.
   This is `open_world_view`'s rule. There is no cross-corpus snapshot, as there is
   none in a build, and the stamp's per-corpus states say exactly what was read.

6. **The address map is derived by publish's own function, over world kinds only.**
   The captured world-kind records (`stored.WORLD_KINDS`, each with its address, uid,
   kind and deprecated ids) form a `derive.Capture`, and `derive.address_map` maps it.
   A live query and a later publish over the same states therefore resolve addresses
   identically. Coordination and prose records stay out of the map, as §6.2 requires,
   so a `kinds` predicate still selects world records only. An `AddressMapConflict`
   (`uid-corruption`, `duplicate-location`) propagates unchanged: it is the finding
   publish would refuse on.

7. **Damage refuses; drift does not exist.** A present corpus whose construction fails
   (`CorpusStateMalformed`), or whose base pin disagrees (`ContractMismatch`), is
   collected. After every corpus is tried, the evaluation refuses
   `SelectionRefused("corpus-damaged")` naming each of them. `corpus-drifted` has no
   meaning without a publication and is never raised here.

8. **The denotation is shared, not copied.** The clause loop, `_denote`,
   `_require_located`, `_classify` and the adjacencies run unchanged for both paths.
   Cut 28's arms W7-c to W7-h pin those bodies, and a copy would break the rule that
   each arm applies exactly once, as well as the point of having one evaluator.
   `evaluate_query` keeps its entry checks (type, damage, drift), which W7-a and W7-b
   pin, and then calls a private core, `_denoted(view, query)`. The helpers are typed
   over a private protocol that `WorldReadView` and the private live capture both
   satisfy: `resolve`, `get`, `inbound`, `live_id`, `corpus_of`, `_mapped_records`,
   and a private `_located_state(ref)` returning `"resolved"`, `"not-present"` or
   `"unknown"`. `_require_located` and `_classify` read the state instead of the
   `locate` result types, and their pinned `raise` bodies stay textually intact.
   `locate` and its public types do not change.

9. **No conformance cut.** The epoch path's guarantees stay held by cut 28's arms,
   which this change must leave green. The live path's guarantees are held by the
   tests in §6. *Rejected:* a cut. Its arms would re-sabotage the shared core, which
   cut 28 already audits. What the live path adds (coverage, per-corpus capture, the
   separate stamp) is a small surface that ordinary tests pin directly.

## 3. The API

```python
# beliefs/world/live.py
@sealed @final @dataclass(frozen=True)
class CaptureStamp:
    world_id: str                               # 32 lowercase hex
    coverage: tuple[tuple[str, str], ...]       # sorted (corpus_id, corpus_state), present corpora

@sealed @final @dataclass(frozen=True)
class LiveSelection:
    stamp: CaptureStamp
    query: ViewQuery
    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    absent: tuple[str, ...]
    unresolved: tuple[Unresolved, ...]
    @property
    def complete(self) -> bool: ...             # Selection's rule
    def projection(self) -> dict[str, object]: ...
    def identity(self) -> str: ...

def evaluate_live_query(world: registry.World, query: ViewQuery) -> LiveSelection: ...
```

The projection:
`{"version": "science.live-selection.v1", "capture": {"world": ..., "coverage": [[corpus_id, state], ...]}, "query": ..., "selected": ..., "contributing": ..., "absent": ..., "unresolved": ...}`.
`identity()` is `v1.digest("science.live-selection.v1", projection)`.

`evaluate_live_query` runs in this order:

1. **Types.** It takes an exact `registry.World` and a parsed `ViewQuery`; otherwise
   `TypeError`.
2. **Coverage.** Under the world barrier (`registry._locked_barrier`), it rescans the
   registry, takes the admitted, non-terminal corpus ids in sorted order, and resolves
   each to a carrier or to absent (decision 3). The barrier is released before any
   corpus is captured, as in `open_world_view`.
3. **Capture.** For each present corpus in sorted order, inside its `capture()` hold,
   it records the state, reads through `ReadView.opened_at`, checks the base pin, and
   enumerates once and records the state again (decision 5). Damage is collected
   (decision 7).
4. **Refuse damage.** Any collected damage refuses `corpus-damaged`, before denotation.
5. **Maps.** It builds the address map (decision 6), the held records (every captured
   world-kind record, keyed by corpus and uid), and inbound edges over held records,
   constructed as `open_world_view` constructs them. World uid uniqueness across
   corpora is checked as the view checks it, and a violation refuses
   `ResolutionRefused`.
6. **Denote.** It runs `_denoted` over the private live capture: `_require_located`,
   then the clause loop, then record validation of the selected records.
7. **Return.** It returns the `LiveSelection` stamped with the captured states.

It writes nothing: no epoch, no receipt, no world-log entry, no index.

## 4. What does not change

- `evaluate_query`, `Selection`, `SELECTION_VERSION`, `WorldReadView`,
  `open_world_view`, `BoundStamp`, `locate` and its result types, publish, and every
  epoch-bound read. An epoch-bound selection's projection and identity stay
  byte-identical.
- The query language and its vocabulary check. Like `evaluate_query`, the live path
  consults no profile.
- Coordination §6.2's regime for publication. A view query inside a published epoch
  is still evaluated at that epoch. This design adds the attention read that §6.2's
  own argument for live resolution covers, and the amendment below says so.

## 5. Amendment to coordination §6.2

A dated paragraph goes after the two regimes:

> *Amended 2026-09-24 (`beliefs-cc0aea`).* A third regime, attention reads: a view's
> query may also be denoted live by `evaluate_live_query`, over every admitted corpus's
> current state, for queue-like attention surfaces such as science's `next` under a
> selected project. Its result is a `LiveSelection` stamped with the captured corpus
> states and never an epoch identity, so it cannot stand in for an epoch-bound
> selection. Belief reads and publication stay epoch-bound.

## 6. Testing

A new `tests/test_live_selection.py`, reusing `test_world_selection.py`'s world fixtures:

- **Live after a write.** Publish an epoch, add a proposition matching a project's
  `kinds`/`references_term` query, then:
  - `evaluate_query` at the old epoch refuses `corpus-drifted`;
  - `evaluate_live_query` selects the new proposition;
  - the stamp's coverage carries the new state identity.
- **Agreement with an epoch.** Over states that equal a fresh publication,
  `evaluate_live_query` and `evaluate_query` agree on `selected`, `contributing`,
  `absent` and `unresolved` for every query in slice 4's acceptance set, and their
  projections differ exactly in `version` and `capture`/`epoch`.
- **Stamp separation.** `LiveSelection` is not a `Selection`. Its projection has no
  `epoch` key. Its identity differs from the epoch-bound identity over the same
  records.
- **Coverage.** A terminal corpus is not covered. An admitted corpus whose carrier is
  missing is listed in `absent` and makes `complete` false. An address held only in
  that corpus refuses `address-unknown`, never `address-not-present`. A duplicate
  carrier refuses `ResolutionRefused`.
- **Coordination records.** A `kinds` query naming world kinds never selects a
  coordination record, and the address map holds no coordination address.
- **Damage.** A corpus with a malformed stored record, and a corpus with a
  disagreeing base pin, each refuse `corpus-damaged` naming that corpus. Two damaged
  corpora are named together.
- **Capture drift.** A write injected inside one corpus's capture hold, through the
  same seam slice 2's drift tests use, raises `CaptureDrift` and returns nothing.
- **Address conflicts.** One canonical address held in two corpora propagates
  `AddressMapConflict` (`duplicate-location`).
- **No writes.** The world root's and each corpus root's file trees, and their state
  identities, are unchanged by an evaluation.
- **Epoch path unchanged.** Slice 4's selection tests and acceptance pass unmodified,
  and `test_arm_staleness.py` stays green. W7-a to W7-i each still apply exactly once.

## 7. What changes elsewhere

- Coordination §6.2 gets the amendment in §5.
- The adoption ledger gets a line naming the live attention read.
- Science's part 2 (`sci-f95f8b`) calls `evaluate_live_query` for `next` under a
  selection and renders `complete`, `absent` and the stamp.
