# Event-level L8 — the presence/exclusion relation across captured corpus heads

**Date:** 2026-09-21
**Status:** discharged at conformance cut 36 on 2026-09-21; results: ../../plans/2026-09-21-conformance-cut-36-results.md
**Boundary:** `event-level-l8` (`beliefs-b34652`), the `world-read` lane's head, tier 1 off the path; `log-remainder` rides with it
**Lane:** `world-read`, worktree `.worktrees/event-level-l8`
**Sources:** `../../designs/2026-08-03-tamper-evident-log-design.md` (§3.3's granularity, §7, L1, L4, L8, L10, limitation 4),
`../../designs/2026-08-22-log-verification-design.md` (§7, §10.7),
`../../designs/2026-08-22-conformance-cut-8.md` (§3.1's L1, L4, L8 and L10 dispositions),
`../../designs/2026-08-23-conformance-cut-9.md` (§3.1's L4 and L10 dispositions),
`../../plans/2026-08-24-conformance-cut-10-results.md` (§1, L10's "no named cross-cut remainder"),
`../../designs/2026-09-13-conformance-cut-27.md` (§3's relabel shape),
`../../designs/2026-08-20-world-index-slice-2-design.md` (§5.2–§5.3, head capture; §6.1, `anchors.yaml`),
`../../plans/2026-08-29-implementation-roadmap.md` (tier 1 off the path rows 1 and 4, Appendix B, concurrency rules)
**Measured against:** `main` at `acf4692`

## 1. What this slice is

The baseline below describes `main` at `acf4692` before implementation.

The log design §7 states cross-chain order at one granularity: within a
chain, order is ancestry; across chains, order exists only through
**ordered epoch cuts**, and an event `a` in chain A precedes an event `b`
in chain B only when an earlier cut's captured A-head contains `a` and its
captured B-head excludes `b`, and a later, world-ancestry-ordered cut
contains `b`. Two events first appearing in one cut, or either root outside
a cut's coverage, are unordered; the earlier cut's build window is the
residual uncertainty. §3.3's cross-corpus chronology claim is made at
exactly this granularity, and "unknown" is the default answer.

Cut 8 built half of it. `world/verify.py:_epochs_ordered` (log-verification
design §7, execution rulings R29–R31) answers whether E2 orders after E1:
E1's publication is the world-chain registration that created
`epochs/<e1>/anchors.yaml`, its moment the earliest committed settlement of
that registration, and E2 orders after it iff E2's recorded build-start
world head is at or after that settlement in the world chain. A missing or
rolled-back publication, an unplaceable head, or an absent or malformed
world chain answers `unordered`; a name that is not a packaging identity or
names no retained epoch refuses `EpochUnknown`; epoch sequence numbers are
read by nothing. Cut 8 read this as L8's two units and deferred "the
event-level relation — presence/exclusion reasoning across captured corpus
heads" as the design's own successor work (cut 8 §3.1; log-verification
§10.7). Every later cut left it there (cut 11 results §5).

The evidence the relation needs is already published. Every epoch's
`anchors.yaml` carries one `(subject, genesis_digest, head_digest)` per
covered corpus, captured under that corpus's coherent-capture hold at build
(`epoch.py:_capture`, serially in sorted `corpus_id` order), beside the
world anchor recorded at preflight. A corpus chain is readable through the
log seam as a `WellFormedView` whose `entries` are genesis, registered,
settled and intent entry views in chain order, each carrying its digest;
`_retained_identities_locked` enumerates a world's retained epochs; and
`_locked_open_epoch` parses one.

Three things are missing, and this slice builds them: the **event
domain** — what an event is and where its moment lies in its chain; the
**witness predicate** over two cuts and two chains, with coverage and
placeability made explicit; and the **relation** the caller asks, searched
over the world's retained epochs and answered with a direction or
`unordered`. It closes L8 in full, closes L4 and L10 as relabels, re-homes
L1's remainder to `persistence-cut`, and builds no consumer.

## 2. Decisions

1. **An event is `(corpus_id, entry_digest)`.** Its chain is the corpus's;
   its digest names one entry of that chain. The relation is agnostic of
   what the entry did — L8's spec-freeze transition and run intent are two
   instantiations of one domain, not two kinds the relation knows.
2. **Every event has at most one moment, and the moment is what is
   compared.** An intent entry's moment is itself. A genesis entry's moment
   is itself. A committed settlement's moment is itself. A **registration's
   moment is its committed settlement** — a transition happened when it
   committed, not when it was declared. A registration whose settlement is
   absent from the chain (pending) or settled as a rollback has **no
   moment**, and so does a rolled-back settlement named directly. Every
   comparison path normalizes to moments first; an event without a moment
   makes the pair `unordered`.
3. **Equal moments are unordered.** The same event twice, or a registration
   and its own settlement, name one moment; nothing precedes itself.
4. **Same-chain pairs are ordered by ancestry and open no epoch.** A
   same-chain question inspects the world chain (for recovery, decision
   10), resolves its carrier, inspects that one corpus chain, and compares
   moments by position. The world inspection's classification is not
   consulted and no retained epoch is opened, so a malformed world chain
   or a malformed retained epoch cannot defeat an answer corpus ancestry
   establishes on its own.
5. **Cross-chain order is the witness predicate, and the relation is
   witness-asymmetric.** `W(a, b)` holds when some ordered pair of retained
   epochs witnesses `a` before `b` (§4). The relation answers
   `a-precedes-b` exactly when `W(a, b) and not W(b, a)`, `b-precedes-a`
   exactly when `W(b, a) and not W(a, b)`, and `unordered` otherwise —
   including the double witness, which two overlapping builds can produce
   (§4.3) and which is §7's build-window residual made visible. This is a
   dated amendment to the log design's §7 wording ("only when ordered cuts
   establish it"), recorded as such (§9).
6. **Coverage and placeability are explicit, and establish presence or
   exclusion only together.** A cut speaks about a chain only when its
   `anchors.yaml` carries an anchor for that corpus, that anchor's
   `genesis_digest` equals the live chain's genesis, and its `head_digest`
   is an entry of the live chain. A missing anchor, a genesis mismatch, or
   an unplaceable head establishes **neither** presence nor exclusion for
   that cut and that chain. Both witness cuts must cover **both** corpora
   this way (§7: "either root outside a cut's coverage … is unordered").
7. **Ordered cuts are decided by one pure helper over one captured world
   view.** `_epochs_ordered`'s body factors into `_ordered_by_descent(view,
   e1, built_from, absent_state)`, a pure function over an already-read
   `WellFormedView`; `_epochs_ordered` keeps its signature and contract and
   calls it. The relation reads the world chain **once** and asks the helper
   for every candidate pair, so no pair is judged against a different
   observation of the chain and no lock is reacquired per pair.
8. **Refusals are caller-input facts; `unordered` is an evidence fact.** A
   corpus the world has not admitted refuses `EventCorpusUnknown`; an
   admitted corpus with zero or several configured carrier roots refuses
   `EventCorpusUnresolvable`; a digest absent from a **well-formed** chain
   refuses `EventUnknown` — including a digest a valid-prefix truncation
   removed, since the truncated chain is still well-formed and the caller
   named an entry it does not carry. A **terminal** (retired or departed) corpus is
   still queryable when its carrier resolves: the relation is about the
   past, and a status event is an append that deletes nothing (log design
   §8). A malformed or absent corpus chain, an unplaceable or mismatched
   anchor, a pending or rolled-back moment, and the absence of any witness
   answer `unordered`; the relation never emits a verdict — verification's
   findings stay verification's.
9. **The reads' own refusals propagate untranslated.** `EpochMalformed`
   from the retained-epoch scan or from opening a carrier, `BuildHold` from
   a corpus lock met during a capture, and `LogEvidenceRefused` from
   inspection each mean the relation refused to judge; none is an answer and
   none is mapped to `unordered`. (The corpus hold is the seam's
   `corpus_lock` **writer-style** hold — the one `audit_log` and
   `admit_arrival` take — which queues behind a writer and refuses across a
   capture with `BuildHold`; `BuildContended` is the capture hold's own
   refusal and the relation takes no capture hold.)
10. **Lock order is the audit's: the world lock first, released before any
    corpus lock; recovery before resolution.** Under the world lock, on
    both paths: `inspect_registered` on the world root **first**, because
    it completes recovery and recovery can rewrite the registry files a
    scan reads (`_preflight` reads the chain before
    `_locked_resolve_coverage` for the same reason); then a fresh registry
    scan and carrier resolution; then, for a cross-chain question only,
    enumerate and open the retained epochs. Then, per corpus in sorted
    `corpus_id` order and never nested, under that corpus's operation lock:
    inspect the chain once. No `World` method is called under the world
    lock (R12).
11. **The composition root exports the relation; the core takes the seam.**
    `root.event_order(config, a, b)` wraps
    `verify._event_order(config, a, b, *, seam)` exactly as
    `epochs_ordered` wraps `_epochs_ordered`; `root.py` stays the one
    `atoms` importer, and the relation calls no write primitive, so
    `WRITE_ENTRY_POINTS` and `CASES` are unchanged (AGENTS.md, Cut plans).
12. **L1 leaves `log-remainder` for `persistence-cut`, and stays partial.**
    Its deferred arms — kill the executor between entry durability and
    apply at every stage; crash after entry durability but before the
    transaction record stores the entry digest; cut persistence at every
    stage of the settlement sequence for **both terminal arms**, converging
    on one registration and one settlement with neither outcome returned
    nor the lease released before the settlement is durable — are the
    persistence-cut harness's arms (cut 8 §3.1: "A7/A8's certified
    productions; Science holds no persistence-cut harness (the cut-7 X2
    gap, named, not argued around)"). Cut 36 does not argue them full by
    citing the `atoms` suite; the results record re-homes them, and
    `beliefs-3ea822` gains them as obligations while `beliefs-b34652`
    drops them (§10).
13. **L4 and L10 close as relabels, deferred nothing.** Cut 8 read seven L4
    units and cut 9 the two it deferred (the store subject, the distinct
    fork genesis); cut 8 read L10's arrival-identity arm, cut 9 its fork,
    replica, restore and store arms, and cut 10 its two holdings-read
    clauses, leaving "no named cross-cut remainder … though the row label
    remains partial" (cut 10 results §1). Cut 36 selects one unit per row
    that cites every prior clause by cut and unit and adds no fixture — cut
    27's X5 shape.
14. **Nothing sharper than §7 is built.** The build's sorted capture order
    could disambiguate the double witness (§4.3); using it would strengthen
    the relation past the banked text, so it is filed as an open question,
    not built. No consumer is built: comp §3.3's chronology finding has
    none today and gains none here.

## 3. The event domain — `world/events.py`

A new module, `beliefs.world.events`, holding the domain and the pure
comparisons; it imports the log model's view types and nothing of the
engine.

```python
@dataclass(frozen=True)
class Event:
    corpus_id: str
    digest: str

Order: TypeAlias = Literal["a-precedes-b", "b-precedes-a", "unordered"]
```

`moment(view: WellFormedView, digest: str) -> int | None` — the position in
`view.entries` of the event's moment, or `None` where decision 2 gives it
none. It raises `EventUnknown` when `digest` names no entry of the
well-formed view; it is never called on a malformed view. The rules,
exhaustively over the four entry classes:

| entry class of `digest` | moment |
|---|---|
| `GenesisEntryView` | its own position |
| `IntentEntryView` | its own position |
| `SettledEntryView`, `committed` | its own position |
| `SettledEntryView`, rolled back | `None` |
| `RegisteredEntryView` with a committed settlement naming it | that settlement's position |
| `RegisteredEntryView` with a rolled-back settlement, or none | `None` |

A well-formed chain carries at most one settlement per registration (L2's
malformed arm, classified before this module is reached), so "the
settlement naming it" is a lookup, not a choice.

`Placement` — one cut's reading of one chain, decision 6 made a value:

```python
@dataclass(frozen=True)
class Placement:
    head: int          # the captured head's position in the live chain
```

`place(view, anchor) -> Placement | None` answers `None` when the epoch
carries no anchor for the corpus, when `anchor.genesis_digest` differs from
the view's genesis digest, or when `anchor.head_digest` is no entry of the
view. `contains(placement, moment) -> bool` is `moment <= placement.head`;
`excludes` is its negation over the same `Placement`. Neither is ever asked
of a `None` placement: the witness predicate requires both placements
first.

## 4. The witness predicate and the relation — `world/verify.py`

### 4.1 `_ordered_by_descent` — the pure half of `_epochs_ordered`

```python
def _ordered_by_descent(view: WellFormedView, e1: str, built_from: str, absent_state: object) -> Ordering
```

Exactly the tail of today's `_epochs_ordered` after its lock block:
`_publication_settlement(view, e1, absent_state)`, the positions map, and
the `>=` comparison including the settlement (R29). `_epochs_ordered` keeps
its signature, its docstring's contract, its lock block and its
`EpochUnknown` refusals, and returns this helper's answer;
`test_world_log_audit.py`'s predicate tests hold it byte-for-byte in
behaviour, and cut 36's guard carries the R29 sabotage that cut 8's cited
guard can no longer run (§8.3, §8.5).

### 4.2 `W(a, b)` over one observation

Given one world view, the opened retained epochs, and one inspected view
per chain, `_witnessed(a, b)` holds iff there exist retained epochs `E1`,
`E2` such that:

1. `_ordered_by_descent(world_view, E1, E2.world_anchor.head_digest) == "ordered"`;
2. `place(view_A, E1.anchor(A))`, `place(view_B, E1.anchor(B))`,
   `place(view_A, E2.anchor(A))` and `place(view_B, E2.anchor(B))` are all
   non-`None` (decision 6: both corpora, both cuts);
3. `contains(E1 on A, moment(a))`, `excludes(E1 on B, moment(b))`, and
   `contains(E2 on B, moment(b))`.

`E1 != E2` follows from 1 (no epoch descends from its own publication's
settlement before it exists) and is asserted anyway. The search is over
the sorted retained identities, first-found sufficing; it is a predicate,
and no witness pair is returned or recorded.

### 4.3 The relation

```python
def _event_order(config: WorldConfig, a: Event, b: Event, *, seam: LogSeam) -> Order
```

In order:

1. **Under the world lock:** `seam.inspect_registered(config.world_root)`
   first — recovery completes here, and the registry files scanned next
   are the files recovery left (`LogEvidenceRefused` propagates). Then a
   fresh `_scan_registry`, and for each of `{a.corpus_id, b.corpus_id}`
   the admission check (`EventCorpusUnknown`) and the carrier check
   (`EventCorpusUnresolvable`), terminal status permitted (decision 8).
   For a **cross-chain** question, additionally the retained identities
   with their opened epochs (`EpochMalformed` propagates). A same-chain
   question opens no epoch and does not consult the world view's
   classification. Release.
2. **Per corpus, sorted, under `seam.corpus_lock(carrier)`:**
   `seam.inspect_registered(carrier)` once (`BuildHold` and
   `LogEvidenceRefused` propagate). A view that is not `WellFormedView`
   answers `unordered` at once — no `EventUnknown` is derivable from a
   chain that cannot place anything.
3. **Moments:** `moment(view_A, a.digest)`, `moment(view_B, b.digest)`
   (`EventUnknown` propagates). Either `None` → `unordered`.
4. **Same chain** (`a.corpus_id == b.corpus_id`, one inspection): equal
   moments → `unordered`; else the smaller position precedes.
5. **Cross chain:** if the world view is not `WellFormedView` →
   `unordered` (no cut can be ordered). Else `w_ab = _witnessed(a, b)`,
   `w_ba = _witnessed(b, a)`; `a-precedes-b` iff `w_ab and not w_ba`,
   `b-precedes-a` iff `w_ba and not w_ab`, else `unordered`.

Whether the question is same-chain is known from its arguments before any
read. The world inspection is taken on both paths for recovery's sake, and
what decision 4 guarantees is exactly that a malformed world chain, or a
malformed retained epoch, does not defeat corpus ancestry: the same-chain
path reads the world view's classification nowhere and opens no epoch.
§8.2's independence case is built on both.

**Valid-prefix truncation** of a corpus chain (L3's refuted arm) leaves a
well-formed chain, so the contract splits it in two: an event the
truncation removed refuses `EventUnknown` (the caller named an entry the
chain does not carry), and two retained events whose cut's captured head
now lies beyond the tip answer `unordered` (the head is unplaceable, so
the cut establishes nothing). Both are tested (§8.1, §8.2).

**The double witness is realizable**, and the fixture demonstrates it
(decision 5). With corpora `A < B` in sorted order and builds capturing
serially in that order:

| step | actor |
|---|---|
| 1 | build E3 preflights (world head `h0`) and captures A |
| 2 | writer commits `a` to A |
| 3 | build E1 preflights (world head still `h0`) and captures A, then B |
| 4 | writer appends `b` to B |
| 5 | build E3 captures B and publishes |
| 6 | build E1 publishes (or before step 5 — either order) |
| 7 | build E2 preflights after E1's publication, captures both, publishes |
| 8 | build E4 preflights after E3's publication, captures both, publishes |

E1 contains `a`, excludes `b`; E2 orders after E1 and contains `b`: `W(a, b)`.
E3 excludes `a`, contains `b`; E4 orders after E3 and contains `a`: `W(b, a)`.
E1 and E3 are mutually unordered (both built from `h0`). In fact `a`
preceded `b` (E1's A-capture preceded its B-capture), which the sorted
capture order could recover and §7 does not claim; the relation answers
`unordered`. Every step is a real act — preflight, capture and publish are
`build_epoch`'s own phases driven one at a time, and the writes are
`CorpusWriter` acts — so the schedule is one the locks admit, not a
fabricated view.

### 4.4 `root.event_order`

```python
def event_order(config: WorldConfig, a: Event, b: Event) -> Order:
    return _event_order(config, a, b, seam=_log_seam())
```

Exported in `root.__all__` beside `epochs_ordered`; `Event` and `Order`
are re-exported from `beliefs.world.events`. The signature test that pins
`epochs_ordered`'s parameters gains this wrapper's.

## 5. Errors — `errors.py`

Three classes, each a caller-input fact (decision 8):

- `EventCorpusUnknown(ScienceError)` — the event names a `corpus_id` this
  world has never admitted. Presence on a configured root is the corpus's
  own claim, not the world's (`AnchorSubjectUnknown`'s reasoning).
- `EventCorpusUnresolvable(ScienceError)` — the corpus is admitted but has
  no presently configured carrier root, or more than one; the relation
  cannot say which chain it would read (`CoverageUnresolvable`'s reasoning,
  without the build's liveness clause).
- `EventUnknown(ScienceError)` — the digest names no entry of the corpus's
  well-formed chain, a valid-prefix truncation's removed entries included.
  Raised only over a `WellFormedView`: a malformed chain answers
  `unordered` before any digest is looked up.

`CoverageUnknown` and `CoverageUnresolvable` are not reused: their
docstrings state the build's contract, and a relation query is not a
declared coverage.

## 6. What does not change

- `anchors.yaml`'s shape, the epoch build, the capture order, the head
  artifact, the anchor act, the evaluator and replay. The relation reads
  published evidence and writes nothing.
- `_epochs_ordered`'s signature, contract and refusals (decision 7 moves
  its body, not its behaviour).
- Both `CONTRACT.yaml` copies and their identities. No TypeScript changes.
- `science.belief.v1`'s answers over every fixture; P1–P9.
- The reproduction: cut 36 reads the mm30 corpus in place and re-derives
  the same answer; the relation is exercised only by the acceptance module
  (the corpus has one chain and its world's epochs order nothing new).

## 7. Shared files, under roadmap concurrency rule 3

`errors.py`, `python/tests/test_designs_corpus.py`, the ledger, the roadmap
and the guide index are rewritten by every lane. This slice also rewrites
`world/verify.py` (the `world-read` lane's own column), `root.py` (one
wrapper and two re-exports), and `test_world_log_audit.py`. No other lane
is open; the `cross-repo` lane's `l13-preimage`, if opened beside this
one, names `world/verify.py` in its own design and its merge resolves
toward this one.

## 8. Testing and the cut

### 8.1 Unit — `test_world_events.py` (new) and `test_world_log_audit.py`

`test_world_events.py`, over fabricated well-formed views (the
`test_world_log_audit.py` builders, imported):

- `moment`: every row of §3's table, including a registration with a
  rolled-back settlement and one with none; `EventUnknown` for an absent
  digest; the settlement lookup is by `registration` digest.
- `place`: `None` for a missing anchor, a genesis mismatch, an unplaceable
  head; the position for a placeable one; `contains`/`excludes` at the
  head exactly (inclusive).

`test_world_log_audit.py` gains a class for the relation over injected
seams (the existing `Inspections`/`Captures` doubles):

- same chain: precedes, reverse, equal moments, a registration and its own
  settlement, a pending registration, a rolled-back one, genesis as an
  event;
- cross chain: the L8 positive; both first in one cut; E2 not ordered after
  E1; a cut missing one corpus's anchor; a genesis mismatch; an unplaceable
  head; a malformed corpus chain; a malformed world chain; the double
  witness over fabricated views (the real schedule is §8.2's);
- same chain opens no epoch and ignores the world view: a same-chain
  question answers over a `MalformedView` world chain and with a retained
  carrier the scan would refuse, and the epoch opener is never called;
- recovery before resolution: the world inspection precedes the registry
  scan on both paths (a probe that rewrites the registry inside the
  inspection double, observed by the resolution);
- valid-prefix truncation: a removed event → `EventUnknown`; two retained
  events with an unplaceable captured head → `unordered`;
- `place` with a placeable head and a mismatched declared genesis →
  `None` (the isolated genesis comparison, decision 6);
- the refusals: `EventCorpusUnknown`, `EventCorpusUnresolvable` (zero and
  two carriers), `EventUnknown`, and the propagation of `EpochMalformed`,
  `BuildHold` and `LogEvidenceRefused` untranslated;
- lock discipline: the world lock is released before the first corpus lock
  is taken; corpus locks are taken sorted and never nested (the existing
  lock-probe pattern); the world chain is inspected exactly once per call;
- `_epochs_ordered` still answers every existing case, now through
  `_ordered_by_descent`; the sequence-number source assertion extends to
  `_ordered_by_descent`, `_witnessed` and `_event_order`;
- the composition-root wrapper: signature `["config", "a", "b"]`, the seam
  injected, exported.

### 8.2 Acceptance — `test_event_order_acceptance.py` (new)

Real worlds on the certified volume, through `root` only: `init_world_root`,
two admitted corpora `A < B`, a **spec freeze** committed to A
(`CorpusWriter` — the transition L8 names) and a **run intent** appended to
B, epochs built with `build_epoch`. Cases:

1. L8 positive: freeze in A → E1 → intent in B → E2 → `a-precedes-b`; the
   reverse question (`event_order(config, b, a)`) answers `b-precedes-a`
   over the same facts — the relation is antisymmetric in its arguments.
2. Both first appearing in one cut → `unordered`, and no positive answer is
   ever emitted for the pair in either argument order ("spec predates run"
   is not emitted).
3. Coverage: E1 built covering A only → `unordered` for the pair, while a
   later pair of covering cuts orders it.
4. Genesis mismatch, two checks. **Replacement:** after E1, replace A's
   chain with a self-consistent chain under a different fork genesis
   presenting the same subject (cut 9's L4u2 fixture), commit a fresh `a`
   there, build E2 → `unordered` — E1's anchor for A neither matches the
   genesis nor places its head. **Isolated:** a `WellFormedView`'s
   `genesis` is `entries[0]`, the same object, so no inspected chain —
   real or stand-in — can carry live entries under another genesis; and
   an epoch's packaging identity binds the anchor bytes it declares
   without proving they agree with any chain. The genesis comparison is
   therefore isolated on the **anchor's** side: a genuine well-formed
   view, an anchor with the same subject and a reachable head, and only
   `anchor.genesis_digest` replaced → `place(...) is None`, asserted
   beside `place` of the unaltered anchor being non-`None` so that the
   genesis clause alone decides. This is §8.1's isolated `place` check,
   carried in the acceptance module over a real chain; the genesis
   sabotage (§8.3) is bound to it and to no other.
5. Equal moments: `(A, registration digest)` against `(A, its settlement
   digest)` → `unordered`; the same event twice → `unordered`.
6. Same-chain independence: two events in A while the world retains an
   epoch whose carrier is malformed (a member removed after publication)
   **and** the world chain is malformed (an interior entry rewritten, L3's
   arm) → ordered by ancestry; the same question across chains →
   `EpochMalformed` with the carrier alone, `unordered` with the world
   chain alone.
6a. Valid-prefix truncation of A behind E1's captured head: the removed
   event → `EventUnknown`; two retained events against B → `unordered`.
7. The double witness, by §4.3's schedule → `unordered`.
8. Refusals: an unadmitted id → `EventCorpusUnknown`; an admitted id whose
   carrier configuration is removed, and one claimed by **two distinct
   configured roots** → `EventCorpusUnresolvable` (one root configured
   twice is one carrier — `_carrier_roots` deduplicates resolved paths —
   and stays resolvable, asserted); a digest of another chain →
   `EventUnknown`; a corpus lock held by a capture → `BuildHold`.
9. Sequence numbers: no epoch member, no `Epoch` attribute and no line of
   the relation's source names one (cut 8's L8u2 shape, extended).
10. `_epochs_ordered` through the composition root over the same worlds
    answers as cut 8 certified.

Every case asserts the answer and, for `unordered`, that neither positive
answer is obtainable by swapping the arguments.

### 8.3 N2 sabotages — `n2_arms_cut36.py`

One sabotage per declaration unit, each named to a real source site with a
`before` occurring exactly once in its module, following cut 35's
discipline:

- `moment` returns the registration's own position (a pending registration
  gains a moment);
- `moment` returns a rolled-back settlement's position;
- `place` ignores the genesis digest — bound to case 4's isolated `place`
  check over a replaced `anchor.genesis_digest`, the one check the
  replacement fixture cannot stand in for (§8.2);
- `place` accepts a head absent from the chain as the chain's tip;
- `_witnessed` drops the E1-on-B exclusion clause;
- `_witnessed` reads `E1`'s own world anchor instead of `E2`'s;
- `_event_order` returns `a-precedes-b` on `w_ab` alone (the double witness
  becomes a positive);
- `_event_order` opens the retained epochs for a same-chain pair (the
  independence case refuses `EpochMalformed` instead of answering);
- `_event_order` maps `EpochMalformed` to `unordered`;
- `_event_order` reuses `_epochs_ordered` per pair (the world chain is
  inspected more than once);
- `_ordered_by_descent` compares strictly (R29 regresses; caught by the
  L8 positive, whose E2 was built the instant E1 published);
- an L4 and an L10 sabotage each re-run one prior clause's site (the
  relabel's live guard).

The staleness gate is `test_arm_staleness.py`'s: **every arm a live guard
audits applies exactly once** — zero stale live arms, after any
`_LIVE_SABOTAGES` re-targeting. Cited-not-run guards (cuts 4, 8 and 10
among them) keep their historical staleness recorded in
`cited_not_run.py`, never repaired, and are not part of that gate.

### 8.4 The cut

Conformance cut 36, `docs/designs/2026-09-21-conformance-cut-36.md`, frozen
before implementation after this spec's review. Rows: **L8** in full —
cut 8's two units (the ordered-cuts predicate, the sequence-number
negative) **cited** to its standing record, never re-run, since
`test_n2_cut8.py` is cited-not-run by ruling R15 (`cited_not_run.py`), and
the event-level units above selected; **L4** and **L10** close as relabels
(decision 13); **L1** is not read, and its re-homing is stated in §3.2
(rows not read) so the results record can carry it. Runner
`cut36_acceptance.py` chains **cut 35's** runner in `PREFIX_RUNNERS` — the
live certified chain continues, never re-roots — with phase modules
`test_event_order_acceptance.py` and `test_n2_cut36.py`; the focused L8
checks and every sabotage §8.3 names live in cut 36's own guard.
`test_recent_cut_acceptance.py` gains the cut-36 row with its accounting
triple and guarantee-rows-exercised line (AGENTS.md, Cut plans).

### 8.5 Frozen evidence and live tests

Every frozen declaration stays byte-exact. Cut 8's `n2_arms_cut8.py`
declares two L8 arms against `_epochs_ordered`; the tail decision 7 moves
into `_ordered_by_descent` may leave one of them stale, and because cut 8
is cited-not-run that staleness is **recorded** in `cited_not_run.py`'s
`stale_arms` with the moving commit, never re-targeted and never repaired
(its guard is not in the staleness gate, and the pinned command would be
refused at collection — `addopts` ignores `tests/acceptance`, and the
module is not on the live chain). A pinned line in a **live** guard's
declaration (cuts 17–35) that the refactor moves is re-targeted in that
guard's `_LIVE_SABOTAGES`. After the refactor task, run
`cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py -q`
and record or re-target whatever moved.

## 9. Documentation amendments

- The log design's L8 row gains an `(amended 2026-09-21 …)` marker stating
  the witness-asymmetric relation (decision 5) and the coverage rule
  (decision 6), and §7 a dated note beneath its text; limitation 4 stays.
  L4 and L10 gain closure markers naming cut 36; L1's row gains a marker
  naming `persistence-cut` as its remainder's owner.
- The log-verification design §7 gains a dated note (the event-level
  relation built; `_ordered_by_descent`), and §10.7 closes.
- The ledger's `Current state` table drops `event-level-l8` and
  `log-remainder`, and its `persistence-cut` row gains L1's arms; the
  roadmap re-ranks at cut 36 (Appendix A and B rows for L1, L4, L8, L10;
  the `world-read` lane's head becomes `act-report-remainder`); the guide's
  contracts-and-adoption page and `README.md` state the count.
- `open-questions.md` gains the capture-order sharpening (decision 14).

## 10. Task linkage

- `beliefs-b34652` is this slice's task; its body's "closes the assigned L1,
  L4, and L10 log remainder" is amended to L4 and L10, with L1's re-homing
  noted (`tasks edit`/`tasks note`, committed with the freeze).
- `beliefs-3ea822` (`persistence-cut`) gains L1's exact obligations: kill
  between entry durability and apply at every stage → entry present,
  pending; recovery settles it and the surface matches; crash after entry
  durability but before the transaction record stores the entry digest →
  no second registration; cut persistence at every stage of the settlement
  sequence for **both terminal arms** → one registration, one settlement,
  the binding backfilled, and neither outcome returned nor the lease
  released before the settlement is durable.
- Plan steps become children of `beliefs-b34652` with `--plan` and
  `--step`, each `--complexity` and `--process direct`.

## 11. Limitations and open questions this slice files

1. **The build window remains the residual uncertainty** (log design
   limitation 4), now visible as the double witness answering `unordered`.
2. **Capture-order sharpening** — the build captures serially in sorted
   `corpus_id` order, so "E1's A-head contains `a` and its B-head excludes
   `b`" implies `a` before `b` in real time exactly when `A < B`; using it
   would order the double witness. Filed in `open-questions.md`, not built.
3. **No consumer.** Comp §3.3's chronology claim has no finding that
   consults the relation; one is the owning lane's, when a boundary needs
   it.
4. **L1's persistence arms** are `persistence-cut`'s, behind
   `atoms-f5779f`.

## 12. Review log

- **2026-09-21, outline review (six tightenings, all taken):** coverage
  and exclusion explicit (decision 6); the witness predicate separated
  from the witness-asymmetric relation, with the double witness realizable
  (decision 5, §4.3); the event domain completed with equal-moment and
  genesis rules (decisions 2–3); same-chain ordering independent of
  epochs and a pure ordered-cuts helper (decisions 4, 7); the refusal
  contract completed with terminal corpora queryable (decisions 8–9);
  L1's task ownership transferred with its documentation (decision 12,
  §10). One correction to the review's own list: the corpus hold is the
  writer-style hold, so the preserved refusal is `BuildHold`, not
  `BuildContended`.
- **2026-09-21, spec review (two blockers, three corrections, all
  taken):** P1 — cut 8's guard is cited-not-run (R15), so cut 36 chains
  cut 35, cites cut 8's frozen evidence, and carries the focused L8 checks
  and sabotages itself; the staleness rule restated as zero stale live
  arms with historical staleness recorded (§8.3–§8.5). P2 — the world
  inspection precedes the registry scan on both paths so resolution reads
  the registry recovery left; the same-chain path opens no epoch and
  ignores the world view's classification (decisions 4, 10; §4.3). P3 —
  valid-prefix truncation splits into `EventUnknown` for a removed event
  and `unordered` for retained events under an unplaceable head (decision
  8, §4.3, §5). P4 — `EventCorpusUnresolvable`'s fixture is two distinct
  roots claiming one id; a root configured twice is one carrier (§8.2).
  P5 — the genesis sabotage is bound to an isolated `place` check with a
  placeable head and a mismatched declared genesis (§8.2 case 4, §8.3).
- **2026-09-21, spec review round 2 (one P2, taken):** the isolated
  genesis check alters the **anchor's** declared genesis over a genuine
  well-formed view, not the inspected chain — `WellFormedView.genesis` is
  `entries[0]`, so the stand-in first proposed was a state the seam cannot
  produce; the packaging-identity argument is corrected to "binds the
  declared anchor bytes, proves no agreement with a chain" (§8.2 case 4).
- **2026-09-21, final whole-branch review (two Important, both taken; one
  drift noted):** the tree's `place` takes `genesis_digest` and
  `head_digest` keywords with the anchor lookup in `verify._placement`
  (§3 wrote `place(view, anchor)`), and `_witnessed` skips `E1 == E2` with
  a `continue` rather than asserting it (§4.2); both are the reviewed
  plan's choices and the acceptance module reads them. `root.epochs_ordered`'s
  docstring now names `event_order`; the unit class gained the
  `LogEvidenceRefused` propagation case §8.1 lists.
