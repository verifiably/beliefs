# Live view-query evaluation — design

**Status:** draft for review, 2026-09-24; revised after review the same day (uid
conflict contract, a focused conformance cut, never-published and qualified agreement
tests). **Task:** `beliefs-cc0aea`.
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
   so a `kinds` predicate still selects world records only.

7. **World-record conflicts keep publish's classification and precedence; one scoped
   check covers the rest.** `derive.address_map` raises `AddressMapConflict`: first
   `uid-corruption` (one uid under different canonical addresses), then
   `duplicate-location` (one canonical address held in more than one corpus). The live
   path calls it unchanged and lets both propagate as they are, so a live read and a
   publish over the same states refuse the same conflict with the same code. Any
   cross-corpus uid collision among world-kind records is one of those two, so no
   second check runs over world records.
   The map excludes coordination and prose records, which `open_world_view`'s W8b
   uniqueness check still covers. The live path keeps that check, scoped to what the
   map cannot see. **After** `address_map` returns, a uid held in two corpora where
   at least one holder is a record outside the map refuses `ResolutionRefused` with
   the view's W8b message. Running it only after the map succeeds means it can never
   re-classify a world-record conflict.

8. **Damage refuses; drift does not exist.** A present corpus whose construction fails
   (`CorpusStateMalformed`), or whose base pin disagrees (`ContractMismatch`), is
   collected. After every corpus is tried, the evaluation refuses
   `SelectionRefused("corpus-damaged")` naming each of them. `corpus-drifted` has no
   meaning without a publication and is never raised here.

9. **The denotation is shared, not copied.** The clause loop, `_denote`,
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

10. **A focused conformance cut for the live entry point; cut 28 stays as it is.**
    Cut 28 audits the shared denotation, and it keeps doing so unchanged. The live
    entry point adds paths cut 28 cannot see: which corpora are covered, how each is
    captured, how damage and conflicts are refused, and how the stamp is built. Every
    epoch check could pass while a live evaluation silently omitted a corpus or
    stamped states other than the ones it evaluated. The cut's rows (§6.3) are exactly
    those new guarantees. None of its arms sabotages the shared core, so no cut-28 arm
    is duplicated or re-targeted.

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
   corpus is captured, as in `open_world_view`. No epoch is read: coverage never comes
   from the current epoch, and a world that has never published evaluates.
3. **Capture.** For each present corpus in sorted order, inside its `capture()` hold,
   it records the state, reads through `ReadView.opened_at`, checks the base pin, and
   enumerates once and records the state again (decision 5). Damage is collected
   (decision 8).
4. **Refuse damage.** Any collected damage refuses `corpus-damaged`, before denotation.
5. **Maps.** It builds the address map (decision 6), whose conflicts propagate as
   `AddressMapConflict` (decision 7). It then runs the scoped uniqueness check over
   records outside the map (decision 7). It builds the held records (every captured
   world-kind record, keyed by corpus and uid) and the inbound edges over them,
   constructed as `open_world_view` constructs them.
6. **Denote.** It runs `_denoted` over the private live capture: `_require_located`,
   then the clause loop, then record validation of the selected records.
7. **Return.** It returns the `LiveSelection`. Its stamp is built from the state
   identities recorded inside each corpus's hold in step 3, never re-read afterwards,
   so the stamp names exactly the bytes that were denoted.

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

## 6. Testing and the cut

### 6.1 Unit — portable, `tests/test_live_selection.py`

- **Types.** A non-`World` or unparsed query raises `TypeError`.
- **Stamp separation.** `LiveSelection` is not a `Selection`, and a `CaptureStamp` is
  not a `BoundStamp`. The projection's keys are exactly `version`, `capture`, `query`,
  `selected`, `contributing`, `absent` and `unresolved`, with no `epoch` key.
  `identity()` digests under `science.live-selection.v1`.
- **`complete`.** It follows `Selection`'s rule over `absent` and `unresolved`.

### 6.2 Acceptance — `tests/acceptance/test_live_selection_acceptance.py` (new)

These run on the certified tuple. The fixtures come from `test_world_selection.py` and
slice 4's acceptance. Each Z unit below has an N2 arm (§6.3).

| unit | row | assertion |
|---|---|---|
| Z1-a | Z1 | two present admitted corpora, each holding a record the query matches: both records are selected, `contributing` names both corpora, and the stamp's coverage is exactly those two `(corpus_id, state)` pairs |
| Z1-b | Z1 | a corpus with terminal status whose carrier is still configured and holds a matching record: it is not in the stamp's coverage and its record is never selected |
| Z1-c | Z1 | an admitted corpus whose carrier is missing is listed in `absent` and `complete` is false; an address held only there refuses `address-unknown`, never `address-not-present` |
| Z1-d | Z1 | coverage is the registry's, not an epoch's: in a world that has **never published**, the evaluation succeeds and selects its records; in a world whose current epoch covers only A, a corpus B admitted afterwards with a matching record is covered and its record selected |
| Z2-a | Z2 | a state that moves inside one corpus's capture hold (the `corpus_state_identity` monkeypatch `test_world_view.py` uses) raises `CaptureDrift`, and no selection is returned |
| Z2-b | Z2 | both state reads and the enumeration run inside that corpus's own capture hold. Wrappers around `registry.corpus_state_identity` and `ReadView.opened_at` record the carrier's operation-lock holder at each call, and every call for that carrier must see `"capture"`. A writer holding the corpus's operation lock makes the evaluation refuse `BuildContended`, because a capture never waits |
| Z3-a | Z3 | a record written into corpus A after A's hold releases and before the evaluation returns (injected at the capture of the next corpus): the new record is not selected, and the stamp names A's state from inside the hold, so selection and stamp describe the same bytes |
| Z4-a | Z4 | a present corpus with a malformed stored record refuses `corpus-damaged` naming it; the corpus is never silently left out of a returned selection |
| Z4-b | Z4 | a present corpus whose base pin disagrees refuses `corpus-damaged` naming it |
| Z5-a | Z5 | one canonical address held in two corpora **under the same uid** raises `AddressMapConflict` with code `duplicate-location`. The shared uid is what makes the scoped uniqueness check fire, so its Z5-a sabotage (running that check before `address_map`) turns the refusal into `ResolutionRefused`. A fixture with distinct uids would not see that sabotage |
| Z5-b | Z5 | one uid under two different addresses in two corpora raises `AddressMapConflict` with code `uid-corruption`, taking precedence over any duplicate location in the same capture |
| Z5-c | Z5 | a uid held by a coordination record in A and a world record in B refuses `ResolutionRefused` (W8b), and only after the address map has succeeded |

Beside the units, the module holds:

- **Live after a write.** Publish, then add a matching proposition. `evaluate_query` at
  the old epoch refuses `corpus-drifted`, while `evaluate_live_query` selects the new
  proposition, and its stamp carries the new state identity.
- **Agreement with an epoch, qualified.** The two evaluations are compared only when
  the epoch's declared coverage equals the live admitted set, every covered corpus is
  present, and every corpus state equals the epoch's. Under those three conditions they
  agree on `selected`, `contributing`, `absent` and `unresolved` for every query in
  slice 4's acceptance set, and their projections differ only in `version` and in
  `capture` against `epoch`. A counter-case shows why coverage is a separate
  condition: an epoch covering A alone, then B admitted with a matching record. A's
  state still equals the epoch's, yet the live selection holds B's record and the
  epoch-bound one does not.
- **Damage names every offender.** Two damaged corpora are named in one refusal.
- **Coordination records.** A `kinds` query over world kinds never selects a
  coordination record, and the address map holds no coordination address.
- **Duplicate carriers.** A corpus with two configured carriers refuses
  `ResolutionRefused`.
- **No writes.** The world root's and every corpus root's file trees, and their state
  identities, are unchanged by an evaluation.

### 6.3 Guarantee rows and N2 sabotages — `n2_arms_cut42.py`

| row | guarantee |
|---|---|
| Z1 | a live evaluation covers exactly the world's admitted, non-terminal corpora, read from the registry; each present corpus is captured and each absent one is listed |
| Z2 | each corpus's state reads and enumeration run inside its own capture hold, and a state that moves there discards the evaluation |
| Z3 | the stamp names exactly the per-corpus states whose records were denoted |
| Z4 | a damaged present corpus refuses the evaluation and is never omitted from it |
| Z5 | world-record conflicts refuse with publish's classification and precedence; the scoped check covers only records outside the map |

| unit | sabotage (all in `world/live.py`) |
|---|---|
| Z1-a | the capture loop skips the last covered corpus |
| Z1-b | the terminal-status filter is dropped from coverage |
| Z1-c | absent corpora are dropped from `absent` |
| Z1-d | coverage is read from the current epoch's declared coverage |
| Z2-a | the before/after state comparison inside the hold is dropped |
| Z2-b | the capture hold is bypassed (`nullcontext()` in place of `capture()`), with the before/after comparison kept |
| Z3-a | the stamp re-reads `corpus_state_identity` after every capture instead of keeping the in-hold state |
| Z4-a | a construction failure omits the corpus instead of collecting its damage |
| Z4-b | the base-pin check is skipped |
| Z5-a | the scoped uniqueness check runs over every record before `address_map` |
| Z5-b | the capture keeps one record per uid before calling `address_map` |
| Z5-c | the scoped uniqueness check is dropped |

The plan fixes the declared accounting: 12 arms, 12 units, 5 rows (Z1–Z5). A unit
whose check does not see its sabotage is rehomed at Task 0, never dropped. No arm
touches `world/selection.py`, so cut 28's W7 arms and their evidence stay unchanged,
and `test_arm_staleness.py` must stay green.

### 6.4 The cut

The cut is numbered 42, because `beliefs-3ce305` holds 41. The cut document is
`docs/designs/<freeze date>-conformance-cut-42.md`, dated by the commit that freezes
it after review. Under the roadmap's concurrency rule 5, a cut names the
highest-numbered acceptance runner, so the prefix is read when cut 42 freezes and
never written into the plan in advance. If cut 41 has been frozen by then, discharged
or not, `python/tools/cut42_acceptance.py` sets `PREFIX_RUNNERS =
("cut41_acceptance.py",)`, and while cut 41 is undischarged, cut 42's discharge is
serialized after cut 41's. The plan's freeze task checks which runners exist and
records in the cut document which one it chained. The runner also sets
`PHASE_MODULES =
("test_live_selection_acceptance.py", "test_n2_cut42.py")`. The cut also needs its row
in `test_recent_cut_acceptance.py`, with the declared arm, unit and guarantee-row
counts and the guarantee-rows-exercised line, and a results record.

`world/live.py` imports nothing from `atoms`, so `root.py` stays the one `atoms`
importer. The live path calls no write primitive, so `WRITE_ENTRY_POINTS` and
`test_permit_entry_points.py`'s `CASES` do not change. The plan states both
obligations in its Global Constraints verbatim, as AGENTS.md requires.

### 6.5 The epoch path

Slice 4's selection tests and acceptance pass unmodified, and cut 28's runner passes.
Each of W7-a to W7-i still applies exactly once.

## 7. What changes elsewhere

- Coordination §6.2 gets the amendment in §5.
- The adoption ledger opens rows Z1–Z5 and closes them at cut 42's results record.
- The roadmap names cut 42 beside cut 41, and records its serialization behind cut 41
  under rule 5 when cut 41 is frozen first.
- Science's part 2 (`sci-f95f8b`) calls `evaluate_live_query` for `next` under a
  selection and renders `complete`, `absent` and the stamp.
