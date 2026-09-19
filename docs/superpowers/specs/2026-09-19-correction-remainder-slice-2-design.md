# Correction remainder, slice 2 — the snapshot target

**Date:** 2026-09-19
**Status:** draft, under review
**Boundary:** `correction-remainder` (`beliefs-aa27da`), the mutation lane's only open boundary; slice 2 of 2, task `beliefs-d79ca4`
**Lane:** `mutation`, worktree `.worktrees/correction-remainder`
**Sources:** `../../designs/2026-08-03-correction-lifecycle-design.md` (§3, §4 "Semantic snapshot" and "Coverage narrowing", §6, C8, C9),
`2026-09-16-correction-remainder-slice-1-design.md` (§1, decisions 2, 4, 8, 9; §12),
`../../plans/2026-09-16-conformance-cut-33-results.md`,
`../../designs/2026-08-02-world-addressing-design.md` (§5, the snapshot/receipt split),
`../../designs/2026-08-20-world-index-slice-2-design.md` (§6.1, §7.3–§7.6, §8.2–§8.4),
`../../designs/2026-08-19-family-adapters-design.md` (§4.3),
`../../plans/2026-08-29-implementation-roadmap.md` (tier 1 off-path row 1, concurrency rules)
**Measured against:** `main` at `1958ec5`

## 1. What this slice is

Slice 1 (cut 33) made standing a property of the read for the node and route
arms: the enumeration is derived, a standing retraction's node target leaves
the read set before decoding, a route target retires its route. What no cut
has built is the fourth instantiation the correction design names — the
**semantic snapshot** — and the narrowing route that rests on it.

Today a producer snapshot has no retraction. `stored.retraction_node`
accepts a `NodeTarget` or a `RouteTarget` and nothing else;
`corpus._validated_retraction_target` refuses any other arm as malformed; a
producer snapshot is not a stored record, so the node arm cannot name it
(slice 1 §1 rejected a stored `producer-snapshot` kind: the epoch is the
derivation boundary, and a second representation of the same derived input
would be an authored one with a hash on it). `derive.RECEIPT_OUTCOMES` is
the closed four of world-index §7.5; `audit.SNAPSHOT_STATES` the closed
three; `import_epoch` refuses `malformed-receipt` and `refuted-receipt` and
nothing about standing; `evaluation.gather`'s world read checks that the
supplied `producer_snapshot_identity` is the bound epoch's
(`ProducerSnapshotMismatch`, slice 1 decision 2) and nothing about whether
anyone has retracted it. Coverage narrowing therefore has no legitimate
route: a curator who wants a narrower snapshot can build one, but nothing
records that the old one is no longer to be read, and every computation
bound to it proceeds.

This slice gives the retraction a third target arm, **`snapshot`**, naming
an epoch subject by kind and subject identity; reads that subject's standing
**live from the corpora its own coverage names**; and reports or refuses it
at exactly the sites the correction design lists — import refuses before any
write, audit and the diagnostic query report `retracted`, and a world read
whose supplied snapshot is retracted refuses. Narrowing is then the design's
own composition: build the successor under the narrower coverage, retract
the old snapshot with `successor` naming the new one. Mounting stays inert.

Rows read: **C8** and **C9** in full. The boundary closes with this cut and
the mutation lane has no further open boundary.

## 2. Decisions

1. **Snapshot standing is read live from the covered corpora, at every
   recomputation site.** A producer snapshot `S` is retracted iff a standing
   `snapshot`-arm retraction naming `("producer", S)` is held by a corpus
   that `S`'s own coverage names, **in that corpus's current state**.
   Import, `audit_epochs`, `snapshot_state` and `gather`'s world read each
   fold it afresh (§5). Two reasons fix "live". First, ordering: writing the
   retraction moves the covered corpus's state, so a check placed after
   `validate_receipt`'s availability phase ("every named corpus presently
   stands at the exact state the receipt named") is unreachable by
   construction — the very write that retracts makes the receipt
   `unresolvable`. Second, narrowing: the retraction's `successor` names the
   new identity, so it is written *after* the successor epoch is built and is
   captured by neither epoch. **Rejected:** reading snapshot retractions from
   retained epochs' enumerations only — C9's "a computation naming the old
   snapshot hits C8's refusal" would then need a third build nobody asked
   for, and the check would be against a receipted enumeration whose coverage
   may differ from `S`'s. **Rejected:** every corpus mounted in the world —
   the answer would then depend on the registry rather than on the
   snapshot's own declaration, and a corpus the snapshot never covered would
   decide its standing. The bound the design states ("a standing retraction
   in an uncovered corpus does not reach the computation") is made a refusal
   at authoring rather than a silent miss by decision 3.
2. **The arm names the subject by kind and identity, and the kind is closed
   to `producer`.** `target = {arm: "snapshot", subject_kind: "producer",
   subject_identity: <64 lower hex>}`. The other three receipt subjects —
   the retraction enumeration, the certification inventory, the coreference
   reduction — are not belief inputs (`derive.BELIEF_INPUT_KIND` names the
   one that is) and are not readable inputs in the correction design's sense
   (§4, "eligible targets are exactly the readable inputs"); a
   `subject_kind` outside `("producer",)` is `RetractionTargetIneligible`.
   The field exists so the arm says which subject family it means, as
   `ReceiptOutcome.kind` does. **Rejected:** omitting the kind — a retraction
   whose target is a bare digest would be a retraction the reader has to
   guess the namespace of.
3. **A snapshot-arm retraction resolves at authoring iff a retained epoch
   carries the identity and the writing corpus is in that snapshot's
   coverage.** The second clause is new to this arm: for node and route arms
   the target is in the corpus by construction (family adapters §4.3 refuses
   cross-corpus targets). For a snapshot the "target's corpus" is its
   coverage, and a retraction written outside it would stand nowhere
   decision 1 reads. The writer refuses it (`RetractionTargetUnresolvable`,
   "corpus … is outside the coverage of producer snapshot …") rather than
   admitting a record that never takes effect. The resolution needs the
   world's retained epochs, which `CorpusWriter` cannot see; it reaches them
   through an optional constructor port (§4), the `coordination_resolver`
   pattern. A writer without the port refuses the arm: it cannot resolve
   what it cannot read. **Rejected:** shape-only admission at the write with
   resolution deferred to import and audit — every other arm resolves at the
   write boundary (C10), and a snapshot retraction that resolves only at
   audit would be the raw-write disposition for an admitted act.
4. **`retracted` is decided before availability, for the producer receipt
   only.** In `validate_receipt`, after well-formedness and before the rule
   binding is resolved: the fold of §5 over the receipt's `corpus_states`
   corpora, read live. `retracted` names a retraction record; the receipt is
   otherwise untouched. The other three kinds never answer `retracted`
   (decision 2). Ordering follows decision 1's first reason. **Rejected:**
   `retracted` only where the receipt would otherwise validate — unreachable
   once the retraction is written, and audit would then report
   `unresolvable` for a snapshot the world has retracted.
5. **A retracted snapshot is history, not a defect.** `audit_epochs` adds
   no error or warning finding for `retracted`; the verdict's `state` and
   `EpochAudit.receipts` carry it, and `snapshot_state` is the diagnostic
   query the design names. The retained carrier is byte-unchanged (§6,
   "history is not erased") and `delete_epoch` is unaffected. **Rejected:**
   a warning finding — every retained epoch older than the current one would
   eventually carry it, and a finding nobody acts on is noise.
6. **The evaluator refuses, and the refusal is not a digest member.** A world
   read whose supplied `producer_snapshot_identity` is in the live retracted
   set raises `ProducerSnapshotRetracted` after `ProducerSnapshotMismatch`
   and before any input is read. Nothing about belief changes and no
   computation is performed, so nothing enters a closure: the identity is
   already a closure member (`closure.py:154`), which is what moves the
   digest between the old and the new snapshot in C9. **Rejected:**
   answering `NoBelief("snapshot-retracted")` — a retracted snapshot is not
   an evaluated state with no belief, it is a computation the design says
   may not run (C8: "refused where recomputation already happens").
7. **An absent covered corpus makes the snapshot's standing unreadable, and
   the read answers absence.** The fold runs over the present covered
   corpora; for every corpus in `view.absent()` the evaluator appends
   `(f"producer-snapshot:{identity}", corpus_id)` to `absent` and the
   existing path answers `NoBelief("unavailable-corpus-absent")`. Slice 1
   decision 4's rule — absence is not unreadability, and an absent covered
   corpus is an `absent` entry rather than an exception — is kept; the
   spelling is the one `declared_refs()` already uses for the snapshot. At
   `validate_receipt` an absent or unreadable covered corpus lets the phase
   fall through, and availability answers `unresolvable` as it does today.
   **Rejected:** folding over the present corpora and proceeding — a
   retraction written to a corpus that later departs would silently stop
   standing, and every other absence in a world read fails closed.
8. **A snapshot-arm retraction is out of every computation's closure
   scope, and `gather` does not resolve its target.** Slice 1 decision 10
   scopes `found` to retractions targeting this proposition's assessments,
   their verifications, the supplied snapshot's dataset keys, and
   transitively retractions targeting included retractions. A snapshot arm
   targets none of those, and a retraction targeting a snapshot-arm
   retraction is out of scope with it. In `gather`'s standing loop a
   snapshot-arm found retraction is facet-validated, entered in `facets` so
   the fold sees it as a vertex, and its target is not dereferenced: its only
   possible closure member is the bound snapshot, which decision 6 checks by
   identity. The retained-identity resolution stays the write boundary's
   (decision 3) and the audit's (§7). **Rejected:** resolving it through the
   view — a `WorldReadView` has no retained-epoch handle, and adding one to
   every open for a target the closure never contains is cost with no
   reader.
9. **`successor` for a snapshot arm is a producer subject identity, and no
   relation edge is emitted for the arm.** `retraction_node` emits no
   `retracts` edge for a snapshot target and no `succeeded-by` edge for its
   successor: relations name records, and a snapshot is not one. The facet
   carries both as text, projected into the identity as every arm's target
   is. The write boundary checks a present `successor` on a snapshot arm
   resolves as a retained producer identity through the same port, and
   refuses one that is the target itself. **Rejected:** a `succeeded-by`
   relation to a synthetic ref — a dangling edge the corpus check would have
   to learn to ignore.
10. **The correction design's "two arms" is amended, not contradicted.**
    §3 and §4 of the banked design say "the eligible-target set stays two
    arms" and place the semantic snapshot under the node arm; that was
    written when a stored snapshot record was assumed. The banking commit
    gains a dated note at both places: the snapshot has no stored record
    (slice 1 §1), so it is named by a third arm; the eligibility test — "a
    computed view reads its standing" — is unchanged and the semantic
    snapshot still passes it. `derive.RECEIPT_OUTCOMES` and
    `audit.SNAPSHOT_STATES` each gain `"retracted"` as the design's §4 says
    they do; the world-index design's §7.5 closed set is amended by the same
    dated-note discipline. Historical cut documents are not edited.
11. **The derivation rules are unchanged.** `_retraction_target` keys a
    snapshot arm by `subject_identity` in the discovery map (§6); the
    captured `CapturedRetraction.target` is opaque text to `rules_v1`, so no
    rule or implementation identity moves and no retained receipt becomes
    `unresolvable` by this slice. Stated here because a rule-identity change
    would re-rank every retained epoch, and the plan verifies it by running
    `validate_receipt` over a pre-slice epoch.

## 3. The arm — stored shape

`stored.py`:

```python
@dataclass(frozen=True)
class SnapshotTarget:
    subject_kind: str        # "producer"
    subject_identity: str    # 64 lower hex
```

`retraction_node(target: NodeTarget | RouteTarget | SnapshotTarget, ...)`
maps a `SnapshotTarget` to
`{"arm": "snapshot", "subject_kind": ..., "subject_identity": ...}`. Shape
refusals at construction (`MalformedRecord`): `subject_kind` not in
`SNAPSHOT_SUBJECT_KINDS = ("producer",)`; `subject_identity` not 64 lower
hex. Relations: `grounded-in` per ground as today; **no** `retracts` edge
and **no** `succeeded-by` edge (decision 9). The identity digest is
`v1.digest("science.retraction.v1", facet)` over the same facet keys, so
the arm's fields are in the identity basis as every arm's are.

`corpus._validated_retraction_target` accepts the third arm with field set
`{"arm", "subject_kind", "subject_identity"}`; every field a non-empty
string; `subject_kind` outside `SNAPSHOT_SUBJECT_KINDS` or an identity that
is not 64 lower hex is `MalformedRecord` (shape), as a malformed node ref is.
`CorpusWriter._validated_retraction` rebuilds the expected node through
`retraction_node` with a `SnapshotTarget` and compares id, facets and
relations as today — a raw-written snapshot retraction carrying a
`retracts` edge therefore fails the controlled-shape comparison.

`stored.RETRACTION_TARGET_ARMS = ("node", "route", "snapshot")` is named
once and read by `_validated_retraction_target`, `retraction_node`,
`epoch._retraction_target` and the guide's kinds table.

## 4. The write boundary — the resolver port

`corpus.py`:

```python
class SnapshotResolver(Protocol):
    def retained(self, subject_kind: str) -> Mapping[str, tuple[str, ...]]:
        """subject identity → sorted covered corpus ids, over every retained
        epoch whose receipt of that kind names a subject."""
```

`CorpusWriter.__init__` gains `snapshot_resolver: SnapshotResolver | None =
None`, stored as `self._snapshot_resolver`. The resolution is the writer's,
not the view's: `_resolve_retraction_target` is a `@staticmethod` taking a
view because node and route arms resolve through one, and the snapshot arm
takes what it needs explicitly. The signature becomes

```python
_resolve_retraction_target(
    record, view, *, snapshot_resolver: SnapshotResolver | None = None, corpus_id: str | None = None
)
```

The writer's call sites — `retract`, the import path's union view, the
corpus check's `_CheckView` path — pass `self._snapshot_resolver` and
`self.corpus_id` (the manifest's, through `load_manifest(self.root)`, the
property that exists today). `gather` passes neither and never reaches the
branch (decision 8); `standing_in_local_view` passes neither, and a
snapshot-arm retraction there is a vertex only (it names no node). A
snapshot arm reached with `corpus_id is None` is a programming error
(`TypeError`), never a refusal. The branch:

- `snapshot_resolver is None` → `RetractionTargetUnresolvable(f"{record.id}:
  a snapshot target needs the world's retained epochs, and this writer
  reaches none")`.
- `target["subject_kind"] not in SNAPSHOT_SUBJECT_KINDS` →
  `RetractionTargetIneligible`.
- `retained = snapshot_resolver.retained(target["subject_kind"])`;
  `target["subject_identity"] not in retained` →
  `RetractionTargetUnresolvable(f"{record.id}: no retained epoch carries
  producer snapshot {identity}")`.
- `corpus_id not in retained[identity]` →
  `RetractionTargetUnresolvable(f"{record.id}: corpus {corpus_id} is outside
  the coverage of producer snapshot {identity}")`.
- `successor` present: `successor not in retained` →
  `RetractionTargetUnresolvable(... "successor ... is not a retained producer
  snapshot")`; `successor == identity` → `ValidationRefused(... "a snapshot
  retraction's successor is not its target")`.

The world supplies the port. `world/epoch.py`:

```python
class RetainedSnapshots:
    def __init__(self, world: registry.World) -> None: ...
    def retained(self, subject_kind: str) -> Mapping[str, tuple[str, ...]]:
        with registry._locked_barrier(self._world) as world_root:
            carriers = _retained_receipt_bindings_locked(world_root)
        member = read._member_for(subject_kind)
        ...
```

Under the barrier it reads every retained carrier once; outside it, for
carriers whose `member` is the kind's, it maps `subject_identity` (skipping
carriers whose `subject_identity` or `corpus_states` is `None` — a
receipt-contract fault is the audit's to report, not a name to resolve
against) to the sorted corpus ids of `corpus_states`. Two carriers naming
one identity with different coverage cannot occur (the identity digests the
projection, which carries the coverage); the union is taken and the plan's
unit test pins that a hand-built pair with equal identity and different
coverage is `EpochMalformed` at the scan. A `subject_kind` outside
`epoch.RECEIPT_KINDS.values()` is `ValueError`. `_member_for` is moved from
`read.py` to `epoch.py` (`read` imports `epoch`; the reverse would cycle)
and re-exported from `read` under its name so no caller moves.

Actors and locks: the port takes the world lock for the scan only and holds
no corpus lock; `retract` holds the per-root operation lock as today and
calls the port inside it, which is a world-lock acquisition under a corpus
lock — the order `build_epoch`'s preflight and `open_world_view` already
use (world barrier, then per-corpus capture holds, never the reverse), so
no new lock order is introduced. The `WriterSession` constructs writers
through `writer_factory`; a session in a world hands the factory a
`RetainedSnapshots(world)`; the reproduction driver's writers and every
corpus-only test writer pass none and cannot author the arm.

## 5. Snapshot standing — the fold

`corpus.py`:

```python
def retracted_snapshots(
    views: Mapping[str, ReadView], subject_kind: str = "producer"
) -> frozenset[str]:
```

For each `(corpus_id, view)` in sorted order: every stored retraction's
facet through `_validated_retraction_facet` (a refusal is
`RetractionUnreadable(node.id, cause)`, decision 4 of slice 1); the fold
`retraction_standing(view, facets)` (slice 1 §3.2, unchanged — snapshot
arms are vertices, never subtractors, exactly as route arms are); then
`{facet["target"]["subject_identity"] for id, facet in facets.items() if
facet["target"]["arm"] == "snapshot" and facet["target"]["subject_kind"] ==
subject_kind and standing[id]}`. The union over corpora is the answer.

Per corpus and then union, because a counter-retraction lives beside the
retraction it counters: cross-corpus node targets are refused at the write
boundary (slice 1 decision 9), and `move` — the one operation that can
separate them — is slice 1 §11's named split, filed there and not widened
here. The fold takes no lock: each caller hands it views it already holds
under whatever hold that caller owns (§7, §8).

## 6. Capture — the discovery map

`epoch._retraction_target(facet)` returns `target["subject_identity"]` for
the snapshot arm. The docstring's argument extends: a snapshot-arm
retraction names a subject identity, disjoint from every ref and every route
identity by namespace, so the map key is the identity itself. Nothing else
in capture, `_captured_records`, `_standing_retractions` or the enumeration
projection changes; `CapturedRetraction.target` is text. A snapshot-arm
retraction captured by a later epoch therefore appears in that epoch's
retraction enumeration with its folded resolution, is a digest member of no
computation (decision 8), and is discoverable through the map by the
identity it names.

## 7. The recomputation sites

### 7.1 `validate_receipt`

`derive.RECEIPT_OUTCOMES = ("validated", "refuted", "unresolvable",
"malformed", "retracted")`; `ReceiptOutcome.validated` is unchanged, so
`coreference_edge`'s `indeterminate` treatment of any non-validated
outcome (§8.4) inherits `retracted` without a branch.

After `_contract_fault` returns `None` and before the rule binding is
resolved, for `kind == "producer"` only:

```python
standing = _snapshot_standing(world, receipt)
if standing is not None:
    return standing
```

`_snapshot_standing` opens each named corpus live: `registry._carrier_roots`
as the availability phase does (a malformed manifest or a carrier count
other than one → `None`, falling through to availability, which reports it
in its own words); under `_operation_lock_for(carrier).capture()`,
`ReadView.opened_at(carrier)` with `_require_base_pin()`
(`CorpusStateMalformed` or `ContractMismatch` → `None`, same fall-through;
an unreadable corpus cannot say what it holds); the views are collected, the
hold released per corpus, and `retracted_snapshots(views)` folded outside
every lock. `RetractionUnreadable` from the fold → `None`: a corpus whose
retractions do not read is one the availability phase and the corpus audit
both report, and the receipt's outcome remains the availability answer.
`receipt.subject_identity in retracted` → `ReceiptOutcome("producer",
"retracted", f"retraction(s) {sorted ids} in {corpus ids} stand against this
subject")`; else `None` and the phases continue unchanged.

The state read inside the hold is not compared to the receipt's — it has
moved, by construction, in every case this phase exists for. Drift inside
the hold is `CaptureDrift`, as in `_standing`.

### 7.2 `import_epoch`

`decisions` becomes `(("malformed-receipt", "malformed"),
("retracted-snapshot", "retracted"), ("refuted-receipt", "refuted"))`;
`EpochImportRefused.reason`'s literal gains `"retracted-snapshot"`. The
refusal is before `_locked_barrier` and creates no directory, as today. A
retracted producer subject is the only receipt that can carry the outcome
(decision 4), so the refusal's `outcomes` is that one verdict.

### 7.3 `audit_epochs` and `snapshot_state`

`SNAPSHOT_STATES = ("checked", "contradicted", "unchecked", "retracted")`.
`_reduce`: any outcome `retracted` → `"retracted"`, checked before the
`validated` test (a retracted subject's receipts are all `retracted`, so no
mixed case arises, and the order is stated so a future kind that could mix
them has a rule). No finding is added (decision 5). `EpochAudit.receipts`
carries the outcome per `(name, kind)`.

## 8. The evaluator — the world read

`WorldReadView` gains

```python
def retracted_snapshots(self) -> frozenset[str]
```

— `corpus.retracted_snapshots(self._live)` computed once and cached on the
view. `_live` holds the present covered corpora's `ReadView`s opened at
`open_world_view` under each corpus's capture hold; the records a
post-epoch retraction lives in are the "unmapped" ones `DriftReport` names,
and the open reports rather than refuses that drift, so the fold sees them.
`_live` excludes damaged corpora (`_damaged_ids`); a damaged covered corpus
in `report` mode is treated as absent for this read (decision 7), and in
`refuse` mode the open has already refused.

`gather`, in the `if world:` block after the mismatch check:

```python
for corpus_id in view.absent():
    absent.append((f"producer-snapshot:{bound}", corpus_id))
if not absent and bound in view.retracted_snapshots():
    raise ProducerSnapshotRetracted(bound)
```

with `absent` declared before the block. The existing `if absent:` return
then answers `NoBelief("unavailable-corpus-absent")` with the snapshot
spelling among the absent refs — the same shape a found retraction in an
absent corpus produces (slice 1 §8.1). A corpus-local read has no epoch and
is unchanged.

In the standing loop, the target branch becomes three-way: `node` and
`route` as today; `snapshot` → `facets[ref] = facet` and `continue` (no
absence probe, no `_resolve_retraction_target`; decision 8). Every
`ScienceError` from the facet validation is still wrapped as
`RetractionUnreadable`.

`errors.py`: `ProducerSnapshotRetracted(RecordError)` with `identity`;
message "the supplied producer snapshot {identity!r} is retracted in its
covered corpora".

## 9. Narrowing — C9

No new operation. The route is the design's composition, exercised by the
acceptance module and the reproduction (§13):

1. `build_epoch(world, coverage=narrower, bindings)` → `new`, with
   `new.receipts["producer-receipt.yaml"].subject_identity == S'`.
2. Through a session-held writer in a corpus both `S` and `S'` cover:
   `retract(retraction_node(target=SnapshotTarget("producer", S), ...,
   successor=S'))`.
3. Asserted: `old.members` byte-identical before and after (read back
   through `read.open_epoch`); every receipt of `old` byte-identical;
   `snapshot_state(world, "producer", S).state == "retracted"` and
   `snapshot_state(world, "producer", S').state == "checked"`; `gather`
   over `open_world_view(world, old)` with `producer_snapshot_identity=S`
   → `ProducerSnapshotRetracted`; over `open_world_view(world, new)` with
   `S'` → proceeds, and `answer.belief_input_digest` differs from the
   pre-narrowing answer over `old`.
4. **Negative:** over `open_world_view(world, new)` with
   `producer_snapshot_identity=S` → `ProducerSnapshotMismatch`, and over
   `old` with `S'` → likewise. Nothing resolves through the retraction to
   its successor; the successor is text in a facet.

Step 2's coverage clause is why the negative in §4 exists: a retraction
written to a corpus only `S'` covers is refused at authoring.

## 10. The mount negative — C8

`World.admit(corpus_root, provenance=...)` of a corpus root holding a
snapshot-arm retraction, and of a corpus root a retracted snapshot covers:
`epochs/` under the world root is byte-identical before and after (every
retained carrier's members compared), no `validate_receipt` call occurs (the
acceptance module wraps `read.validate_receipt` with a counting stub for the
duration of the admit), and the admission record is the only write. The
registry's admission inspects nothing (`World.admit`'s docstring); the
assertion pins that this slice adds nothing to it.

## 11. Testing and the cut

### 11.1 Unit

`python/tests/test_snapshot_retraction.py` (new):

- `retraction_node` with a `SnapshotTarget`: facet shape, no `retracts` or
  `succeeded-by` relation, `grounded-in` present; `subject_kind`
  `"retraction-enumeration"` refuses; a 63-hex identity refuses; the
  identity moves with `subject_identity` and with `successor`;
- `_validated_retraction_target` accepts the arm, refuses an extra field, a
  missing field, a `retracts` edge (controlled-shape comparison);
- a writer with no port: `retract` → `RetractionTargetUnresolvable`
  ("reaches none"); with a stub port: identity not retained →
  unresolvable; corpus outside coverage → unresolvable naming the corpus;
  successor not retained → unresolvable; successor equal to target →
  `ValidationRefused`; the happy path writes one record;
- `retracted_snapshots`: no retractions → `frozenset()`; one standing
  snapshot retraction → its identity; counter-retracted → empty; two
  corpora, one each → both; an unreadable facet → `RetractionUnreadable`;
  a route-arm and a node-arm retraction alongside change nothing;
- `RetainedSnapshots(world).retained("producer")` over a world with two
  epochs of different coverage → both identities with their coverage; a
  carrier with a `None` subject skipped; an unknown kind → `ValueError`;
- `_retraction_target` on a snapshot facet is the identity.

`python/tests/test_world_audit.py` (or the module that holds `audit_epochs`
tests today; the plan names it): `_reduce` with a `retracted` member is
`retracted`; `SNAPSHOT_STATES` and `RECEIPT_OUTCOMES` carry the new value
last; `ReceiptOutcome(kind, "retracted", ...)` constructs.

`python/tests/test_world_standing.py` (extended): a world read whose bound
snapshot is retracted in a covered corpus → `ProducerSnapshotRetracted`;
retracted in a corpus outside coverage cannot be authored (the writer
refuses), and a raw-written one there leaves the read unchanged; an absent
covered corpus → `inputs.absent` carries
`(f"producer-snapshot:{S}", corpus_id)` and the answer is
`NoBelief("unavailable-corpus-absent")`; a snapshot-arm retraction captured
in the bound epoch's enumeration (naming an older snapshot) is in `facets`,
not in `found`, and the digest is unchanged by it.

### 11.2 Acceptance

`python/tests/acceptance/test_snapshot_retraction_acceptance.py` (new), on
the certified tuple through the durable writer, one check per clause:

- **C8-a** `import_epoch` of a carrier whose producer subject is retracted
  in a covered corpus → `EpochImportRefused` with `reason ==
  "retracted-snapshot"`, `outcomes == (ReceiptOutcome("producer",
  "retracted", ...),)`, and `epochs/` byte-identical (no directory);
- **C8-b** `audit_epochs`: the retained old epoch's producer receipt is
  `retracted`, its verdict `state == "retracted"`, and `findings` carries no
  code naming it;
- **C8-c** `snapshot_state(world, "producer", S)` is `retracted` with the
  receipts listed; for `S'` it is `checked`;
- **C8-d** the mount negative of §10, both corpora;
- **C9-a** narrowing: `gather` bound to `old` refuses
  `ProducerSnapshotRetracted`;
- **C9-b** bound to `new`: proceeds; `belief_input_digest` differs from the
  pre-narrowing digest over `old`; `inputs.closure()["producer_snapshot"]
  == S'`;
- **C9-c** `old.members` and every receipt byte-identical across the
  retraction, read back through `read.open_epoch`;
- **C9-d** the two mismatch negatives of §9 step 4;
- **BI-1** a snapshot retraction written to a corpus outside the target's
  coverage is refused at authoring, and one written inside is admitted;
- **BI-2** a writer constructed without the port refuses the arm;
- **BI-3** `retracted` precedes availability: after the retraction is
  written the covered corpus's state has moved, and `validate_receipt` still
  answers `retracted`, not `unresolvable` (a pre-slice validator would
  answer `unresolvable`);
- **BI-4** a counter-retraction of the snapshot retraction restores the
  snapshot: `snapshot_state` returns to `checked`, `gather` proceeds, and the
  digest equals the pre-retraction digest (standing is a read; nothing was
  stored on the target);
- **BI-5** a snapshot-arm retraction is out of the closure: with a snapshot
  retraction of an older epoch captured in the bound epoch's enumeration,
  the closure's `found` and the digest are unchanged from a world without it.

### 11.3 N2 sabotages

`python/tests/acceptance/n2_arms_cut34.py`, one `Arm` per clause above;
every `before` string occurs exactly once in its module at freeze; the
mutated module is `ast.parse`d (the guard `beliefs-1b0827` lifts into the
shared audit if it lands first, else carried per cut as cuts 31–33 did).

| arm | module | sabotage | check |
|---|---|---|---|
| C8-a | `world/importing.py` | the `("retracted-snapshot", "retracted")` decision is removed | acceptance C8-a |
| C8-b | `world/audit.py` | `_reduce`'s `retracted` test → `if False:` | acceptance C8-b |
| C8-c | `world/read.py` | `_snapshot_standing` returns `None` unconditionally | acceptance C8-c (and C8-a, C8-b fail with it; the arm's check is C8-c) |
| C8-d | `world/registry.py` | `_locked_admit` calls `read.validate_receipt` on the world's current epoch after the append | acceptance C8-d (the counting stub records one call) |
| C9-a | `evaluation.py` | `raise ProducerSnapshotRetracted(bound)` → `pass` | acceptance C9-a |
| C9-b | `closure.py` | `"producer_snapshot": producer_snapshot_identity` → `"producer_snapshot": ""` | acceptance C9-b (the digest no longer moves) |
| C9-c | `world/epoch.py` | `RetainedSnapshots.retained`, under the barrier it already holds, appends a `retracted: true` line to the named subject's `producer-receipt.yaml` in its retained carrier — standing stored on the target, the shape §4 of the design forbids | acceptance C9-c (the receipt is no longer byte-identical) |
| C9-d | `evaluation.py` | the mismatch check consults `view.retracted_snapshots()` and accepts the successor named by a standing retraction | acceptance C9-d |
| BI-1 | `corpus.py` | the coverage clause of `_resolve_retraction_target`'s snapshot branch is removed | acceptance BI-1 |
| BI-2 | `corpus.py` | `snapshot_resolver is None` → returns instead of raising | acceptance BI-2 |
| BI-3 | `world/read.py` | `_snapshot_standing` is called after the availability phase | acceptance BI-3 |
| BI-4 | `corpus.py` | `retracted_snapshots` collects every snapshot-arm retraction regardless of `standing[id]` | acceptance BI-4 |
| BI-5 | `evaluation.py` | the snapshot branch of the standing loop resolves the target and adds the retraction to the closure's `found` | acceptance BI-5 |

### 11.4 The cut

Conformance cut **34**, claimed at freeze (rule 1); no worktree or branch
holds a cut-34 document at 2026-09-19 (scanned: `main`,
`design/correction-remainder`, `.worktrees/audio-baseline`, every ref of
`git branch -a`). The runner `python/tools/cut34_acceptance.py` names
`"cut33_acceptance.py"` in `PREFIX_RUNNERS` (rule 5) and carries
`PHASE_MODULES = ("test_snapshot_retraction_acceptance.py",
"test_n2_cut34.py")`. Declaration units: C8-a–d, C9-a–d, BI-1–BI-5 —
thirteen, eight against rows and five boundary invariants. Frozen by dated
commit after review clears; invalidated frozen evidence is pinned and cited,
never edited.

### 11.5 Frozen evidence and live tests

Cut 5's pinned line in `standing_in_local_view` is untouched. Cut 33's
arms pin lines in `evaluation.py`'s standing loop (BI-1–BI-5) and
`corpus.py`'s `retract`; the three-way target branch of §8 is added
*around* the pinned `target_ref = ...` line, which stays verbatim, and the
staleness probe's baseline is the tree's own output at freeze. Frozen
acceptance modules that construct `EpochImportRefused` reasons or read
`SNAPSHOT_STATES`/`RECEIPT_OUTCOMES` by length are checked at the freeze
(`grep -rn "RECEIPT_OUTCOMES\|SNAPSHOT_STATES\|reason ==" tests/`); a
module asserting the closed set's length is edited to the successor
contract, as cuts 31–33 edited frozen modules, and the frozen cut documents
are not.

## 12. Shared files, under roadmap concurrency rule 3

`errors.py` (`ProducerSnapshotRetracted`; `EpochImportRefused.reason`),
`python/tests/test_designs_corpus.py`, the ledger, the roadmap and the
guide index, as every lane. Beyond those this slice rewrites `stored.py`
(`SnapshotTarget`, `retraction_node`, `RETRACTION_TARGET_ARMS`),
`corpus.py` (`_validated_retraction_target`, `_resolve_retraction_target`,
`CorpusWriter.__init__`, `retracted_snapshots`, `SnapshotResolver`),
`evaluation.py` (§8), `world/derive.py` (`RECEIPT_OUTCOMES`),
`world/epoch.py` (`_retraction_target`, `RetainedSnapshots`, `_member_for`),
`world/read.py` (`_snapshot_standing`, the phase), `world/view.py`
(`retracted_snapshots`), `world/audit.py`, `world/importing.py`,
`session/writer.py` (the factory hands the port through), the correction
design and world-index slice-2 design (dated notes, decision 10), and the
guide's kinds and outcomes tables. Both `CONTRACT.yaml` copies are
unchanged: the contract names the `retraction` kind's reader
(`corpus.CorpusWriter._validated_retraction`) and its facet, not the arm
set, so no contract identity moves; the plan verifies that claim by
comparing the contract identities before and after. No lane is open beside
this one.

## 13. The reproduction

The reproduction re-runs under this slice into the corpus at
`.work/reproduction/mm30` (cut 33's state moved aside to
`.work/reproduction/mm30.cut33`) and appends §13 to its record: no digest
moves (no closure member changes — decision 11 and §8), the retraction
enumeration is derived as at cut 33, and the transition section states that
the one new arm is exercised by the acceptance module and not by mm30's
corpus, which retracts nothing. If a digest moves, that is a finding
against decision 11 and the cut does not freeze until it is explained.

## 14. Limitations and open questions this slice files

1. **A retraction's corpus can depart.** Decision 7 fails the read closed
   (`NoBelief`), and audit answers `unresolvable`. A departed corpus that
   held the only retraction of a snapshot therefore neither restores nor
   confirms it; the design's "detected at audit" holds and nothing here
   re-admits the snapshot. Filed as a limitation on the correction design.
2. **`move` of a snapshot retraction away from its counter-retraction** is
   slice 1 §11's split, unchanged; it now covers three arms.
3. **A raw computation that ignores retraction records** can still bind to
   a retracted epoch's bytes (`read.open_epoch` does not refuse). The
   design bounds "unusable" to boundaries and audit; the kernel has no
   process-level enforcement and this slice adds none. Recorded, not filed.
4. **Retracting the current epoch's snapshot with no successor** makes every
   world read bound to `current_epoch` refuse until a new epoch is built.
   Intended: the alternative — `current_epoch` skipping retracted epochs —
   is the implicit resolution C9's negative forbids. Recorded in the guide.
5. **Other receipt subjects are not retractable** (decision 2). A
   certification inventory or a coreference reduction is corrected by
   retracting the records it derives from. Recorded in the correction
   design's note.

## 15. Design amendments and records this slice lands

- Correction-lifecycle design §3 (the target union) and §4 ("Eligible
  targets"): dated notes for the third arm (decision 10).
- World-index slice-2 design §7.5 (the outcome set) and the audit's state
  set: dated notes naming `retracted`.
- Adoption ledger `Current state`: C8 and C9 close; `correction-remainder`
  leaves the open table; the mutation lane closes.
- Roadmap: tier 1 off-path row 1 discharged; the lanes table's `mutation`
  row reads closed at cut 34; Appendix A rows C8, C9.
- Guide: the kinds table's retraction arms, the epoch outcomes and snapshot
  states, limitation 4 above.

## 16. Task linkage

`beliefs-d79ca4` is the slice task and carries `--spec
correction-remainder-slice-2` for this document; the implementation plan
attaches to it, its `### Task N:` headings becoming step children with
explicit complexity and `--process direct`. `beliefs-aa27da` closes at the
cut with both slices discharged. The limitation of §14 item 1 is filed as an
idea at the cut; `beliefs-2d5ada` ("should the audit report a certification
that retirement would change") is read at the cut and closed or re-noted.

## 17. Review log

- 2026-09-19 — drafted against `main` at `1958ec5`.
