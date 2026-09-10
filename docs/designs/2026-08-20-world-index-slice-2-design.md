# World-index slice 2 — epoch carrier design

**Date:** 2026-08-20
**Status:** Banked 2026-08-20 with conformance cut 7. Amended 2026-08-21 to pin
the four receipt-subject projection identities and the member-content digest
algorithm; cut-7 accounting is unchanged. **Implemented on branch
`design/world-index-slice-2`, based on `f3a14bf` on `main` — see the branch's
close-out commit for the final documentation state — and cut 7's 48
declarations discharged on the certified tuple — see
`../plans/2026-08-20-conformance-cut-7-results.md`. That branch was merged into
`main` on 2026-08-22 with `--no-ff` (integration commit `83744e7`), preserving
history as results record §7 requires; that constraint outlives the merge.** §9's empty-directory sentence was corrected in the same
landing; it was wrong as banked.
**W8b amendment (2026-09-09, `beliefs-fda0e5`):** address-map derivation now
distinguishes uid corruption from duplicate location before publication.
This repairs the build defect measured at cut 23; it does not select W8b or
change either frozen cut's accounting.
**Scope:** adoption-ledger artifact 1; the build-time uniqueness half of
artifact 2; anchor carriage needed by artifact 5.
**Inherits:** `2026-08-02-world-addressing-design.md` §5 and §5.1;
`2026-08-03-world-index-packaging-design.md`; the fixture-bound rule contract
in `2026-08-03-normative-contract-design.md` §6; the coreference ruling in
`2026-08-08-world-address-ruling.md` §5.5; and
`2026-08-20-world-registry-design.md` (slice 1).

This design completes the world index's first durable carrier. It does not
change the semantic contracts those authorities already define. It decides
the code and storage boundary needed to implement them against the certified
`atoms` engine.

## 1. Decision and boundary

Slice 2 adds:

- epoch construction and crash-atomic publication;
- the address, producers, retraction-discovery, and coreference maps;
- the producer snapshot and its existing semantic identity;
- four derivation receipts on one receipt contract;
- a fixture-bound rules store and explicit install/removal acts;
- the `current` pointer and the bound-stamped staleness contract;
- explicit whole-epoch garbage collection and its sever report;
- corpus and world chain-head members in each epoch; and
- build-time refusal when declared coverage names a corpus that is unknown,
  not live, absent, or represented by more than one carrier root.

The build always receives an explicit set of stable `corpus_id` values.
"Every live corpus" is not an implicit build mode. The registry's
`duplicate-carrier` state is a build refusal, not merely a finding attached to
an otherwise published epoch.

The following remain outside this slice:

- log verification, L1–L13, the explicit anchor act, and the replay reader;
- genesis-to-mirror verification, pending the configuration-mismatch audit;
- the fork constructor, pending Plan B's root-fork command;
- artifact 11's pinned authority snapshot; and
- any use of chain reading to erase those deferrals.

*(Noted 2026-08-23, after the fact and without widening this slice.)* The first
two are no longer deferred anywhere: world-index slice 3
(`2026-08-22-log-verification-design.md`) built the explicit anchor act, the
replay reader, the one four-outcome log evaluator, and the genesis↔mirror
agreement check, discharging conformance cut 8 with five L rows read in full and
seven in part (L6 unread). This slice's own boundary is unchanged — the
statement above is what was outside *it*, and it stays accurate as such. The
fork constructor and the authority snapshot are still owed.

The one cross-repository prerequisite is the `atoms` command in §2. It lands
before Science implementation, under that repository's own design and review
discipline.

## 2. The `atoms` chain-read command

`atoms` adds a fourth public coordinator command beside `register_root`,
`append_intent`, and `run_transaction`:

```python
@dataclass(frozen=True)
class ChainView:
    genesis_digest: str
    entries: tuple[tuple[str, Entry], ...]
    tip: str


def read_chain(backend, project_root, metadata_root, storage) -> ChainView: ...
```

`Entry` is the existing entry union, promoted to the public surface unchanged.
`ChainView` has these invariants:

- `entries` is nonempty and in validated chain order;
- `entries[0][0] == genesis_digest`;
- `entries[0]` pairs `genesis_digest` with the genesis entry;
- `entries[-1][0] == tip`; and
- the command either returns the complete validated chain or raises the
  existing `ChainStateInvalid`; it never returns a partial view.

The command composes existing internals only. It acquires the same recovery
lease used by every mutating coordinator command, receives `_registered_root`'s
already-computed `ValidatedChain`, projects it, and returns after releasing the
lease. It adds no validation path, bypass, lease type, or consumer-visible
lease. If acquiring the lease completes recovery survivors, that is the
lease's existing meaning, not special read-command behavior.

Science consumes `read_chain` only at these four boundaries in slice 2:

1. for each covered corpus, inside that corpus's capture hold, paired with
   corpus-state capture;
2. on the world root under the world lock, to record the build-start world
   chain head;
3. before `open_epoch` reads epoch files, under the world lock, as a recovery
   barrier, discarding the returned view; and
4. before `current_epoch` or `delete_epoch` reads epoch files, under the world
   lock, as the same view-discarding recovery barrier.

The third and fourth uses prevent an epoch entry point from observing the
filesystem before `atoms` has recovered an interrupted world transaction.
They do not verify anchors or replay the chain.

## 3. Package promotion and module boundary

Before new behavior lands, `python/src/science/world.py` is moved to the
`python/src/science/world/` package. The move is its own task and leaves the
full suite green.

```text
science/world/
├── __init__.py   public surface; re-exports the existing slice-1 names
├── registry.py   slice 1: types, loaders, projections, state identity,
│                 registry scan/reduction, admission, status, and presence
├── rules.py      fixture-bound rule storage and resolution
├── epoch.py      coherent capture, build, publication, current, and GC
├── derive.py     four pure map derivations and producer snapshot
└── read.py       epoch opening, address resolution, stamps, and edge query
```

The promotion is a plain `git mv` plus import fixes. There is no compatibility
module or semantic edit. `science.world.__init__` preserves the public import
surface, so existing `from science.world import ...` imports remain valid.
Cut 6's committed `world.py` sabotage paths remain historical evidence; no
file is recreated to satisfy them.

Cut 6 therefore keeps running by reading that evidence where it lives. Its
declaration table and both acceptance runners are frozen, so the amendment is
confined to `tests/acceptance/test_n2_cut6.py`, which is neither. Its `findings`
fixture `git archive`s the repository at the commit that discharged cut 6 into a
temporary directory and points the harness's `PACKAGE` and `TESTS` globals at
it for the length of the audit. Both move together: a check taken from the
current suite imports `science.world.registry`, which the pre-promotion package
does not have. The pinned run carries both halves of the pairing — every
declared check is also run against an unmutated copy of that package, so a
`sound` verdict still means "fails with the sabotage, passes without it" — and
a third direction runs every declared check against the working tree unpinned,
so a check that is renamed away or that stops passing under later slice-2 work
still turns cut 6 red. What the pin gives up is that weakening a current check
while leaving it green is no longer caught by cut 6's mutation direction.
Moving the pin forward is only correct as a new conformance cut with
re-declared arms, and the branch must be integrated preserving that commit in
history.

`root.py` remains the only module importing `atoms`. It gains the chain-read
and epoch-publication wiring, using the existing durable executor vocabulary,
including `CreateOp`, `ReplaceOp`, and `DeleteOp`. It injects required chain
capture and recovery-barrier callbacks into the world surface; the world
package has no engine import or fallback path. `_WorldState` gains only the
lock choreography needed by the build. Slice 1's registry retains no second
state or lock.

## 4. Rules store

### 4.1 Identity and layout

The normative contract defines a rule identity as the digest of
`(symbol, fixture-set identity)` but does not assign domains to either digest.
This design pins both:

- a fixture-set identity is the digest under `science.fixture-set.v1` of
  sorted `(member name, member content digest)` pairs; and
- a rule identity is the digest under `science.enumeration-rule.v1` of
  `(symbol, fixture-set identity)`.

For both the fixture-set formula above and the epoch-packaging formula in
§6.2, a **member content digest** is the 64-character lowercase SHA-256 hex
digest of that member's exact bytes.

Both domain strings are minted here. The fixture set is the normative half.
Each conforming implementation has a separate implementation content
identity. A runnable binding is the exact pair:

```text
(rule_identity, implementation_identity)
```

The world root stores it as:

```text
rules/<rule_identity>/rule.yaml
rules/<rule_identity>/fixtures/<fixture members>
rules/<rule_identity>/implementations/<implementation_identity>
```

`rule.yaml` is a closed document carrying exactly the rule symbol. The symbol
is also the entry point invoked from the selected implementation content. This
shape permits several conforming implementations of one rule to be held at
once without pretending they are one implementation.

The held check is self-contained: recompute the fixture-set identity from the
fixture member bytes; recompute the rule identity from the stored symbol and
that fixture-set identity; require it to equal the directory name; recompute
the selected implementation's content identity; and run that implementation's
stored-symbol entry point against the fixtures. An exact binding is **held
iff** every check succeeds.

A receipt resolves the exact pair it names from this store. It never resolves
"the implementation this installation would choose today" and never silently
substitutes another conforming implementation.

### 4.2 Shipped rules and explicit installation

Slice 2 ships package content for four v1 enumeration rules and their
contract-normative fixtures:

- producer derivation, including the snapshot and address sourcing;
- retraction enumeration;
- certification enumeration; and
- coreference reduction.

`init_world_root` installs none of them. The composition root explicitly calls
`install_rule_binding` for shipped content, mirroring the explicit adoption
act for a corpus.

Installation validates identities and runs the implementation against every
fixture before submitting one create-only world-root transaction. Exact,
byte-identical reinstallation is idempotent success. An existing `rule.yaml`,
fixture, or implementation path with different bytes raises `RuleCollision`.
Nonconformance raises `RuleNonconformant` before publication.

### 4.3 Explicit removal

`remove_rule_binding` unholds one exact pair. An unknown pair raises
`RuleBindingUnknown`. The world-root transaction deletes the implementation
member and, when it was the final implementation for that rule, `rule.yaml`
and the fixture members. The emptied directory remains: the executor deletes
files, not directories. Nothing enumerates `rules/`, so no scan can read an
emptied directory as a holding — every resolution here is by exact path, and a
rule whose `rule.yaml` is gone is simply not held.

The return value reports every receipt in this world that names the removed
pair and therefore loses this store's resolution path. Receipt validation is
`unresolvable` where no other consulted store holds the pair. The act may make
evidence unresolvable; it may not do so silently. Nothing is removed as a side
effect of installing a successor rule or implementation.

## 5. Coherent capture and build

### 5.1 One operation lock

The corpus lock is `_RootState.lock` in `corpus.py`, obtained through
`_root_state_for(root, executor_factory)`. It is the same object exposed to
`CorpusWriter._operation`; a second per-root lock would not exclude writers
and is forbidden.

The existing bare lock becomes `OperationLock`, an in-process context manager
with a holder kind and a monotonically increasing capture generation:

- A writer finding the lock free holds it as `writer`.
- A writer finding another writer waits, preserving today's cooperating-writer
  queue.
- A writer that observes a `capture` on arrival, or discovers from the
  generation that a capture began and ended while it waited, raises
  `BuildHold`. It never waits again after observing that capture.
- A capture finding the lock free holds it as `capture`.
- A capture finding either holder kind raises `BuildContended` immediately.
  The build never queues behind a corpus operation.

`CorpusWriter` retains `with self._operation:` as its writer-kind acquisition.
Only the epoch build uses capture acquisition.

### 5.2 Build input and preflight

The build input names:

- the declared set of covered `corpus_id` values; and
- one exact `(rule_identity, implementation_identity)` pair for each of the
  four derivations.

Preflight runs while holding `_WorldState.lock`:

1. call `read_chain` on the world root, completing recovery before any world
   file is inspected, and retain its tip as the build-start world-chain head;
2. rescan and reduce the registry;
3. for every covered id, require admission, live status, and exactly one
   presently resolvable carrier root;
4. resolve, identity-check, and fixture-check the four exact rule bindings;
   and
5. retain the `corpus_id -> carrier root` mapping for the rest of this build.

An unadmitted id raises `CoverageUnknown`; a non-live id raises
`CoverageNotLive`; no carrier or more than one carrier raises
`CoverageUnresolvable`; an absent binding raises `RuleNotHeld`. No build
defaults coverage to the registry's live set.

The world lock is a plain blocking lock. Registry appends and these short world
critical sections serialize. The no-queueing rule applies to corpus capture,
not to the world root.

### 5.3 Serial coherent capture

Corpora are captured serially in sorted `corpus_id` order. For one corpus, the
entire following sequence occurs within its capture hold:

1. call `read_chain`, completing recovery, and retain its `genesis_digest` and
   tip digest;
2. compute the pre-enumeration corpus-state identity;
3. enumerate the stored nodes once, feeding the captured records to every
   derivation and the producer snapshot; and
4. recompute the corpus-state identity.

Before a captured record feeds any derivation, the build requires its declared
kind to have a governed stored-kind definition. A record naming a kind that
one of the four maps enumerates but that exists only as contract prose raises
`EnumeratedKindUngoverned` during capture. The build discards the complete
capture and publishes nothing; it neither derives from the unvalidated record
nor silently omits it. Absence of records for an enumerated source kind is an
ordinary empty enumeration — the refusal requires a record that claims the
ungoverned kind.

The state identities and chain head are therefore captured together under the
same exclusion as corpus writes. The second state computation is only a raw
drift check. A mismatch raises `CaptureDrift`, discards the entire capture,
publishes nothing, and does not retry silently.

Only captured values leave the hold. No corpus is re-read during derivation or
publication.

### 5.4 Pure derivation and publication recheck

After all captures complete, the build holds no corpus lock. `derive.py`
computes the four maps, the producer snapshot, and four receipts solely from
the captured values and the preflight rule bytes.

Before publication, the build reacquires the world lock and rechecks that all
four exact bindings remain held. If removal won the race, it raises
`RuleNotHeld`. Otherwise it publishes the epoch in the single transaction
defined by §6. This gives binding removal and epoch publication a determined
order without holding the world lock during corpus enumeration.

Covered corpora may change between capture and publication. That is the
staleness contract: receipts name the exact captured states, and publication
makes no freshness claim about later corpus activity.

## 6. Epoch layout, identity, publication, and `current`

### 6.1 Closed layout

An epoch is stored at `epochs/<packaging_identity>/`. It contains exactly:

```text
address-map.yaml
producers-map.yaml
retraction-discovery-map.yaml
coreference-map.yaml
producer-snapshot.yaml
producer-receipt.yaml
retraction-receipt.yaml
certification-receipt.yaml
coreference-receipt.yaml
anchors.yaml
coverage.yaml
```

Nothing else writes beneath `epochs/`. Every file is a deterministic, closed
YAML document using the same duplicate-key, unknown-field, and malformed-value
discipline as the registry, subject to the receipt distinction in §8.2.

`anchors.yaml` contains sorted
`(subject, genesis_digest, head_digest)` triples, one per covered corpus, and
the build-start world-chain head. `coverage.yaml` contains the declared stable
corpus ids and each one's captured corpus-state identity. It is the source of
the bound stamp.

The retraction enumeration projection and certification inventory are receipt
subjects (§7.5), not additional epoch files.

### 6.2 Packaging identity

The packaging identity is the digest under `science.epoch.v1` of sorted
`(member name, member content digest)` pairs. It is computed from the complete
member bytes before publication, then names the directory in which those exact
members are created.

The packaging identity identifies publication bytes for reads, receipts, and
GC. It is neither a semantic identity nor a belief input. The producer
snapshot retains its independently defined semantic identity; no map location,
epoch path, or packaging digest enters that identity.

### 6.3 Publication and exact rebuild

First publication is one world-root transaction containing a `CreateOp` for
every epoch member and a `CreateOp` for `epochs/current`. Later publication
uses the same member creates and a `ReplaceOp` for `current`. The one-line,
closed `current` file names a packaging identity; it is not a symlink.

If the content-addressed epoch already exists, the build validates its complete
closed layout and byte identity. An identical epoch is an idempotent rebuild:
only the pointer swap is needed, and a pointer already naming it is success.
A same-name collision with different or malformed content raises
`EpochMalformed`. No member is overwritten.

Crash atomicity and durability are inherited engine properties of that one
transaction. Science adds no interim writer or second commit protocol.

There is no sequence number. Packaging identity and the explicit `current`
pointer cover the required behavior without an implicit-latest side channel.

## 7. Derivations and receipts

### 7.1 One enumeration pass

Each covered corpus is enumerated once during capture. That pass produces an
immutable captured view sufficient for all four derivations. Derivation after
capture is pure and cannot inspect a corpus root, registry, current pointer, or
installed default.

### 7.2 Address map

The address map contains every live address and every `deprecated_ids` entry,
each mapped to `(corpus_id, uid)`. The mapping is singular under world §4.3's
invariant. Retired addresses are publication members rather than corpus-local
redirects, so their answer survives corpus absence.

**W8b amendment (2026-09-09):** `derive.address_map` raises
`AddressMapConflict`, a `ScienceError` carrying the existing `Finding` envelope.
One uid at different canonical addresses produces `uid-corruption`, naming
the uid and its corpus/address claims, with no repair offered. One canonical
address held in multiple covered corpora produces `duplicate-location`, naming
the address and its corpus/uid claims and directing the caller to `consolidate`.
Shared and distinct uids produce the same duplicate-location code. Corruption
is checked first across the complete capture, so a duplicate pair cannot hide
a third conflicting canonical address. Claims are ordered by the capture,
never selected by precedence. A record's deprecated addresses are additional
map keys, not additional canonical claims; their collision refusal is unchanged.

The refusal happens during pure derivation: no publication plan is submitted,
and the existing epochs and `current` remain untouched. `build_epoch` still
returns an `Epoch` on success. This is a finding attached to the refused build,
not an epoch sweep or a persistent diagnostics channel.

### 7.3 Producers map and snapshot

The producers map maps each dataset address to a sorted list of run addresses,
one entry for each run holding a `produces` edge to that dataset.

The producer snapshot consists of that map plus the declared coverage expressed
as stable `corpus_id` values, not captured states. Its semantic snapshot
identity is exactly the identity already defined by world §5. Slice 2 computes
that identity and does not redefine it. This snapshot identity is the epoch's
only belief input.

### 7.4 Retraction and coreference maps

The retraction-discovery map maps a target identity to a sorted list of
retraction addresses. Enumeration generalizes the record reading already used
by `standing_in_local_view`: it visits every retraction record in each covered
corpus rather than starting from one target. Several retractions may name one
target.

The coreference map maps each sorted endpoint pair to
`(derived balance, distinct-key count)`. It stores the reduced values only.
`active`, `inactive`, and `indeterminate` are query-time states and never epoch
members.

### 7.5 Four receipts, one contract

The producer, retraction-enumeration, certification-enumeration, and
coreference-reduction receipts are immutable epoch members on one contract.
Each carries:

- its receipt kind as a discriminant — `producer`,
  `retraction-enumeration`, `certification-enumeration`, or
  `coreference-reduction`;
- the projection identity of its subject;
- the exact captured corpus-state identity for every covered corpus; and
- the exact `(rule_identity, implementation_identity)` that ran.

All four carry identical per-corpus states within one epoch. This design mints
one domain for the family: a receipt identity is the digest under
`science.derivation-receipt.v1` of the canonical projection
`(receipt kind, subject projection identity, sorted corpus-state pairs,
rule identity, implementation identity)`. The kind member keeps the four
receipt subjects disjoint under one domain.

The retraction receipt carries its retraction enumeration projection — found
references, resolutions, and coverage — inside the receipt. The certification
receipt likewise carries its location-free, resolution-free inventory of
sorted, by-kind certification references under coverage. Neither projection
adds another epoch member class.

Receipt validation rebuilds the named subject with the named binding against
corpora standing at the named states. An omission or wrong reduction refutes.
An unavailable named state or unheld exact binding is `unresolvable`. An
unsound receipt contract is `malformed`. The outcomes remain:

```text
validated | refuted | unresolvable | malformed
```

The coreference receipt carries no semantic identity and is never a belief
input. Any outcome other than `validated` makes every covered edge
`indeterminate` at query time.

### 7.6 Subject projection identities (amended 2026-08-21)

The inherited contracts define what belongs to each receipt subject, but did
not assign digest domains or one canonical encoding. This amendment pins both.
The definitions are those contracts'; the four domain strings are minted here.
Each identity is `science.identity.v1`'s digest of the following exact
projection under the named domain:

**Producer snapshot — `science.producer-snapshot.v1`:**

```python
{
    "producers": [
        {"dataset": dataset, "runs": list(sorted(runs))}
        for dataset, runs in sorted(producers.items())
    ],
    "coverage": list(sorted(coverage)),
}
```

This is the semantic snapshot identity and the only belief input among the
four.

**Retraction enumeration — `science.retraction-enumeration.v1`:**

```python
{
    "found": [list(pair) for pair in sorted(found)],
    "coverage": list(sorted(coverage)),
}
```

Each `pair` is exactly `(retraction_ref, resolution)`, keeping every found ref
attached to its resolution.

**Certification inventory — `science.certification-inventory.v1`:**

```python
{
    "by_kind": [
        {"kind": kind, "refs": list(sorted(refs))}
        for kind, refs in sorted(by_kind.items())
    ],
    "coverage": list(sorted(coverage)),
}
```

It remains location-free and resolution-free.

**Coreference map — `science.coreference-map.v1`:**

```python
{
    "pairs": [
        {
            "endpoints": [left, right],
            "balance": balance,
            "distinct_key_count": count,
        }
        for (left, right), (balance, count) in sorted(coreference.items())
    ],
}
```

Each endpoint pair is stored with `left < right`; no coverage, edge state, or
belief member enters this subject identity.

These projections use mappings, lists, strings, and integers exactly as shown;
there is no tuple-versus-list, map-order, or installation-local encoding choice
left to an implementation. The receipt identity in §7.5 digests the resulting
subject projection identity, not the subject bytes a second time.

## 8. Read surface and staleness

### 8.1 Opening an epoch

`open_epoch(world, packaging_identity)` opens one explicitly named epoch.
`current_epoch(world)` follows the operational pointer and then performs the
same open. `open_epoch`, `current_epoch`, and `delete_epoch` acquire the one
`_WorldState.lock` before the recovery barrier and hold it through every
carrier read and validation. The latter two use the same private locked loader
rather than reacquiring the non-reentrant lock. Publication and deletion use
that lock too, so a reader cannot mistake an in-flight transaction for a
malformed epoch.

Opening requires the exact member set, parses every closed document, recomputes
every member digest and the directory's packaging identity, and rejects any
failure as `EpochMalformed`. `current` is operational convenience only. An API
that accepts belief inputs accepts an explicit producer-snapshot identity,
never the word or function `current`; the snapshot is retrievable by identity
from any retained epoch carrying it.

### 8.2 Carrier failure is not receipt outcome

Carrier validation and receipt validation are separate layers:

- invalid YAML, a missing or extra epoch member, a bad member content name, or
  a packaging-identity mismatch is an epoch carrier failure and raises
  `EpochMalformed`; but
- a receipt document that reaches the receipt validator yet violates the
  receipt contract yields receipt outcome `malformed`.

Opening does not upgrade a semantically malformed receipt into a carrier
failure. This keeps the coreference consequence reachable: a malformed
coreference receipt opens, evaluates as `malformed`, and makes its edges
`indeterminate`.

### 8.3 Bound stamps and address resolution

Every returned answer contains the epoch packaging identity and its complete
coverage declaration. The result type is closed:

```text
Resolved(location, stamp) | NotPresent(stamp) | Unknown(stamp)
```

An address recorded by the epoch returns `Resolved` when its singular current
carrier produces the mapped `uid`, and `NotPresent` when that corpus has no
present carrier. An address outside the epoch's observed coverage returns
`Unknown`. A retired address remains recorded, so absence of its corpus is
`NotPresent`, not `Unknown`.

Carrier ambiguity or corruption never impersonates absence. A duplicate
carrier, malformed present manifest, or present carrier that fails to produce
the mapped `uid` raises `ResolutionRefused`.

The stamp means only "from this publication over this declared coverage."
Nothing measures changes after capture, and no recency of the epoch implies a
fresh world.

### 8.4 Coreference edge query

The querying world's span is the set of live `corpus_id` values obtained from
the registry reduction, not the configured carrier-root tuple. For an endpoint
pair, the query derives:

- `active` or `inactive` from the stored reduced balance under that span when
  the receipt outcome is `validated` and the epoch coverage contains the
  complete live-id set; otherwise
- `indeterminate`.

In particular, `refuted`, `unresolvable`, and `malformed` all produce
`indeterminate`, as does insufficient coverage. An edge-state inspection may
return that state. Query expansion that would traverse an indeterminate edge
raises `EdgeIndeterminate`; it never treats the edge as inactive. The exception
names every unestablished input: the sorted live `corpus_id` values missing
from coverage and/or the exact non-`validated` receipt outcome. A generic
indeterminacy message without those members does not satisfy the contract.

## 9. Whole-epoch garbage collection

The public act is:

```python
delete_epoch(world, packaging_identity, *, actor)
```

It is explicit consumer policy. Nothing invokes it automatically and no API
deletes an individual epoch member.

While holding the world lock, the act first runs the recovery barrier, validates
`current`, and checks the target. Deleting the identity named by `current`
raises `EpochCurrent`; an unknown identity raises `EpochUnknown`. It then opens
the target and scans the other retained epochs needed to compute the sever
report.

One world-root transaction contains a `DeleteOp` for every target member.
The emptied directory remains — the executor deletes files, not directories —
**and every scan of `epochs/` ignores it.** Nonsemantic has to mean *ignored*
rather than merely unfilled: an empty directory read as a carrier is a carrier
missing all eleven members, so one deletion would otherwise make every later
scan of `epochs/` refuse forever, would make the repeated deletion below report
`EpochMalformed` instead of `EpochUnknown`, and would block republishing the
same bytes into that name. The consequence is stated rather than hidden: an
externally destroyed carrier — `rm epochs/<id>/*` with the directory left
standing — is indistinguishable from a deleted one, so `open_epoch` answers
`EpochUnknown` where it once answered `EpochMalformed`. That is forced by this
section's own no-tombstone decision. The returned report names
the actor, producer-snapshot identity, and four receipt identities carried by
the deleted epoch, flagging each identity not carried by any other epoch in
this world after the deletion.

`atoms` owns recovery of an interrupted deletion transaction. Slice 2 makes no
exact-retry claim after commit: a repeated deletion raises `EpochUnknown`.
Durable tombstones and replayable sever reports wait until exact GC retry is a
real requirement.

## 10. Failure surface and findings

All new exceptions subclass `ScienceError`. When Science translates a
lower-level failure, it raises from the caught exception. Direct contract
refusals have no synthetic cause.

| owner | error | meaning |
|---|---|---|
| lock | `BuildContended` | capture found any current holder and refused immediately |
| lock | `BuildHold` | a writer observed a capture, on arrival or by capture generation after waking |
| build | `CoverageUnknown` | coverage names no admitted corpus |
| build | `CoverageNotLive` | coverage names an admitted, non-live corpus |
| build | `CoverageUnresolvable` | coverage has no carrier or duplicate carriers at preflight |
| build | `CaptureDrift` | the post-enumeration state identity differs; the capture is discarded |
| build | `EnumeratedKindUngoverned` | capture found a record of an enumerated map kind with no governed stored-kind definition; the record is neither derived nor skipped |
| derivation | `AddressMapConflict` | W8b amendment: the captured uid/address claims yield a `uid-corruption` or `duplicate-location` finding; nothing is published |
| build | `RuleNotHeld` | an exact binding is absent at preflight or the pre-publication recheck |
| rules | `RuleCollision` | a content-addressed rule path exists with different bytes |
| rules | `RuleBindingUnknown` | explicit removal names no held exact pair |
| rules | `RuleNonconformant` | an implementation fails the normative fixtures at install |
| epoch | `EpochMalformed` | the epoch carrier fails its closed layout or packaging identity |
| epoch | `EpochUnknown` | an explicitly named epoch does not exist — including an emptied `epochs/<id>/` directory, which §9 ignores rather than reading as an eleven-member-short carrier |
| epoch | `EpochCurrent` | GC attempted to delete the current epoch |
| read | `ResolutionRefused` | carrier ambiguity or corruption prevents an honest resolution state |
| read | `EdgeIndeterminate` | expansion reaches an edge the epoch cannot establish; carries uncovered corpus ids and/or the non-`validated` receipt outcome |

Byte-identical reinstallation is success, not `RuleBindingKnown` or another
exception. Receipt `malformed` is a validation outcome, not `EpochMalformed`.

Slice 2 adds no world-level epoch findings channel. Slice 1's
`duplicate-carrier` and `manifest-malformed` findings remain. A damaged epoch
refuses when explicitly opened. An epoch-enumeration sweep is a dated non-goal,
not a partial diagnostic API.

## 11. Prospective conformance cut 7

Cut 7 performs its own row reading and selection. This design only records the
candidate set implied by the slice:

- X1;
- X2's deferred epoch half;
- X3;
- X5's deferred build arm;
- X7;
- X8, X9, X10, X11, and X12;
- W8a; and
- W5's producers-map arm as a candidate labeled declaration.

The cut document owns verbatim frozen quotations, mutation/assertion pairs,
selection decisions, and full/part accounting. The design constrains; the cut
declares.

The executable surfaces are:

```text
python/tests/n2_arms_cut7.py
python/tests/acceptance/test_n2_cut7.py
python/tools/cut7_acceptance.py
```

Cut 5 and cut 6 runners remain historical and are never edited; they may run as
a prefix. Durable claims use committed registration-entry evidence and the
published epoch under the certified tuple. Replay-grade refutation remains
artifact 5 work.

## 12. Review, banking, and implementation choreography

The order is fixed:

1. Author and self-review this draft in
   `.worktrees/world-index-slice-2-design`, then hand it to the design owner.
2. Close the owner's review. The owner authors cut 7; an independent second
   reader reviews it; all findings close; then the cut freezes.
3. Bank both documents in one change by promoting them to `docs/designs/`.
   That change updates the design corpus from 28 to 30, the README count and
   table rows, the corpus guard's `_COUNT_WORDS` entries for 29 and 30, the
   adoption-ledger rows, and affected guide citations.
4. In the same banking change, recast the stale slice-1 and cut-6 statements
   that no chain-read API is specified. The public reader contract now exists
   and its implementation remains prospective; genesis-to-mirror verification
   stays deferred on audit ownership rather than reader design.
5. Write the implementation plan under the writing-plans discipline. Its first
   task lands `atoms.read_chain` in the `atoms` repository, including the
   `ChainView` invariants and unchanged public `Entry` union.
6. Land the pure package promotion as its own task with the complete suite
   green.
7. Implement, in order, `OperationLock`; rules storage; coherent capture and
   build; epoch publication/read; GC; then cut-7 arms, N2, and acceptance.
8. After certified acceptance, bank the cut-7 results record and close the
   ledger claims supported by the evidence.

The final ledger disposition is constrained as follows:

- row 1 closes because artifact 1 is complete;
- row 2 closes its build-time uniqueness half while the fork constructor
  remains open;
- row 4 records the new coordinator chain-read command; and
- row 5 records that the anchor carrier now exists while verification, the
  anchor act, and replay remain open.

Status headers and checkboxes are updated only when those acts have actually
landed. The banking grep includes user-facing docs carrying the stale
chain-reader premise.

## 13. Limitations and dated deferrals

- **Log verification, explicit anchor act, and replay reader:** artifact 5,
  designed later against this epoch carrier.
- **Genesis-to-mirror verification:** waits on the configuration-mismatch
  audit and its ownership decision.
- **Fork constructor:** waits on Plan B's root-fork command.
- **Cross-process writers:** `OperationLock` and its capture generation are
  in-process; deployment remains single-writer across processes.
- **GC tombstone and replayable sever report:** deferred until exact GC retry
  is required. A post-commit retry is `EpochUnknown`; `atoms` owns transaction
  recovery.
- **Sequence-number decoration:** omitted by decision. Identity plus `current`
  is sufficient.
- **Epoch-enumeration sweep and world-level epoch findings:** explicit dated
  non-goal until a consumer requires it.
- **Two enumerated kinds remain prose:** `coreference-attestation` and
  `instrument-certification` have no governed stored-kind definitions in this
  slice. Their empty enumerations are supported, but every populated
  membership, reduction, and omission-refutes arm waits on the kinds' own
  charters. A raw record claiming either kind refuses capture with
  `EnumeratedKindUngoverned`; it cannot turn this deferral into unchecked
  derived content.
  > **2026-09-10:** `coreference-attestation` gained its domain and facet at world resolution slice 2; `instrument-certification` is the one kind still deferred.
- **Pinned authority snapshot:** artifact 11 is untouched.

These deferrals do not license production use of private `atoms` readers or a
compatibility carrier. Each remains explicit until its owning design lands.
