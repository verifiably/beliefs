"""Cut 36 acceptance: the event-level relation over real worlds.

Every test names its declaration unit. The worlds are real — `init_world_root`,
admitted corpora, `build_epoch` — and the chains are the engine's, read through
`root.log_seam()`. Two units are stand-ins and say so: L8-i fabricates the one
corpus view it hands the relation (a rollback needs a halted backend; cut 8
fabricated these by entry class too), and BI-3 alters an anchor, never a view.
"""

from __future__ import annotations

import inspect
import shutil
import threading
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp

import pytest
from atoms.chain.model import GenesisEntry, encode_entry, entry_digest
from atoms.core.scratch import CHAIN_LEAF
from authority import FULL
from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, run_assessment, spec_draft, spec_rules
from profiles import pins_for
from test_world_log_audit import ABSENT, chain, digest, registration, settlement, state
from test_world_receipts import hold_shipped, publish

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import _operation_lock_for
from beliefs.errors import (
    BuildHold,
    EpochMalformed,
    EventCorpusUnknown,
    EventCorpusUnresolvable,
    EventUnknown,
    SubjectMismatch,
)
from beliefs.intents.shapes import DecodedIntent, decode_intent
from beliefs.projection import project_claim
from beliefs.report import AssessmentRunIntent
from beliefs.root import (
    Event,
    admit_arrival,
    anchor_heads,
    audit_log,
    durable_operation_port,
    epochs_ordered,
    event_order,
    init_corpus_root,
    init_world_root,
    log_seam,
    metadata_root_for,
    open_corpus,
    open_world,
    replicate_root,
)
from beliefs.spec import freeze
from beliefs.world import Fresh, ReplicaOf, WorldConfig, anchors, epoch, events, registry, verify
from beliefs.world.logmodel import (
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)


def view_of(root: Path) -> WellFormedView:
    view = log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return view


def settlement_of(root: Path, registration_digest: str) -> SettledEntryView:
    (found,) = [
        e for e in view_of(root).entries if type(e) is SettledEntryView and e.registration == registration_digest
    ]
    return found


def chain_dir(root: Path) -> Path:
    return root / CHAIN_LEAF


def truncate_after(root: Path, keep_through: str) -> tuple[str, ...]:
    """Unlink every chain leaf after `keep_through`: a valid prefix (L3's arm)."""
    digests = [e.digest for e in view_of(root).entries]
    removed = tuple(digests[digests.index(keep_through) + 1 :])
    for entry_digest_ in removed:
        (chain_dir(root) / entry_digest_).unlink()
    assert type(log_seam().inspect_registered(root)) is WellFormedView
    return removed


def replace_chain_under_another_fork_genesis(root: Path) -> None:
    """Cut 9's L4u2 construction on a live carrier: the chain directory becomes
    one fork-genesis entry naming another parent, same subject (the manifest
    is untouched). The next write appends under the new genesis."""
    other = encode_entry(None, GenesisEntry(science_root._fork_corpus_genesis_payload(("d" * 64, "c" * 64)), ()))
    shutil.rmtree(chain_dir(root))
    chain_dir(root).mkdir()
    (chain_dir(root) / entry_digest(other)).write_bytes(other)


def rewrite_an_interior_entry(root: Path) -> None:
    """Flip one byte of the first registration's leaf: `MalformedView`."""
    interior = next(e for e in view_of(root).entries if type(e) is RegisteredEntryView)
    leaf = chain_dir(root) / interior.digest
    data = bytearray(leaf.read_bytes())
    data[len(data) // 2] ^= 0x01
    leaf.write_bytes(bytes(data))
    assert type(log_seam().inspect_registered(root)) is MalformedView


@pytest.fixture()
def world(work_directory):
    """Two corpora A < B (sorted by id) under `TESTING_PROFILE` — the spec
    draft's estimand is typed against `testing/affects` — one world, nothing
    published yet. Each corpus carries a target proposition so a frozen spec
    can be stored in it."""
    roots: list[Path] = []
    scratch = Path(mkdtemp(prefix="cut36-scratch-", dir=work_directory))
    roots.append(scratch)

    def corpus():
        path = Path(mkdtemp(prefix="cut36-corpus-", dir=work_directory))
        roots.append(path)
        init_corpus_root(path, authority=FULL)
        writer = open_corpus(path, authority=FULL, profile=TESTING_PROFILE)
        manifest = writer.adopt_manifest(profile=pins_for(TESTING_PROFILE))
        # Distinct per corpus: two corpora carrying one `proposition:target` address
        # would refuse every build covering both with `AddressMapConflict` (W8b).
        target = writer.add(
            stored.proposition_node(f"target-{manifest.corpus_id}", title="target", claim=project_claim(TESTING_CLAIM))
        )
        return manifest.corpus_id, path, writer, target.id

    class Built:
        def __init__(self):
            first, second = corpus(), corpus()
            (self.a, self.alpha, self.writer_a, self.target_a), (self.b, self.beta, self.writer_b, self.target_b) = sorted(
                (first, second), key=lambda c: c[0]
            )
            path = Path(mkdtemp(prefix="cut36-world-", dir=work_directory))
            roots.append(path)
            self.config = WorldConfig(path, "c" * 32, (self.alpha, self.beta))
            init_world_root(self.config, authority=FULL)
            self.world = open_world(self.config, authority=FULL)
            self.world.admit(self.alpha, provenance=Fresh())
            self.world.admit(self.beta, provenance=Fresh())
            self.bindings = hold_shipped(self.world)
            self.scratch = scratch
            self.freezes = 0

        def build(self, *corpus_ids: str) -> str:
            return publish(self.world, corpus_ids or (self.a, self.b), self.bindings).packaging_identity

        def freeze(self) -> Event:
            """The spec-freeze transition L8 names: a frozen analysis spec stored
            in A through an operation write. The event is the registration; its
            moment is the committed settlement."""
            self.freezes += 1
            spec = freeze(spec_draft(target=self.target_a, method=f"fit the model {self.freezes}"), held_rules=spec_rules())
            commit = self.writer_a.operations.add(stored.analysis_spec_node(spec))
            assert type(view_of(self.alpha).entries[-1]) is SettledEntryView
            assert settlement_of(self.alpha, commit.entry_digest).committed
            return Event(self.a, commit.entry_digest)

        def run_intent(self) -> Event:
            """The run intent L8 names, through the real assessment-run boundary
            over B's durable port. The intent is appended before the run
            executes, so it stands whether the run mints or is refused; the
            event is the intent entry and its payload decodes to an
            `AssessmentRunIntent`."""
            port = durable_operation_port(self.beta, FULL, profile=TESTING_PROFILE)
            work = Path(mkdtemp(prefix="run-", dir=self.scratch))
            run_assessment(work, port=port)
            entry = [e for e in view_of(self.beta).entries if type(e) is IntentEntryView][-1]
            decoded = decode_intent(entry.digest, entry.payload)
            assert type(decoded) is DecodedIntent and type(decoded.value) is AssessmentRunIntent
            return Event(self.b, entry.digest)

        def intent(self) -> Event:
            """An operation intent in B — cheap, real, and the same entry class
            as a run intent. The relation is kind-agnostic (spec decision 1);
            L8-a exercises the row's own pair through `run_intent`."""
            commit = self.writer_b.operations.add(
                stored.source_node(title="b", identifiers={"doi": f"10.1234/b{len(view_of(self.beta).entries)}"})
            )
            assert type(next(e for e in view_of(self.beta).entries if e.digest == commit.intent_digest)) is IntentEntryView
            return Event(self.b, commit.intent_digest)

        def freeze_in_b(self) -> Event:
            spec = freeze(spec_draft(target=self.target_b, method=f"fit the model b{len(view_of(self.beta).entries)}"), held_rules=spec_rules())
            return Event(self.b, self.writer_b.operations.add(stored.analysis_spec_node(spec)).entry_digest)

        def order(self, x: Event, y: Event) -> str:
            return event_order(self.config, x, y)

        def anchor_for(self, identity: str, corpus_id: str):
            with registry._world_lock_for(self.config.world_root):
                opened = epoch._locked_open_epoch(self.config.world_root, identity)
            (anchor,) = [x for x in opened.anchors if x.subject == corpus_id]
            return anchor

        def recorded_world_head(self, identity: str) -> str:
            with registry._world_lock_for(self.config.world_root):
                return epoch._locked_open_epoch(self.config.world_root, identity).world_anchor.head_digest

    built = Built()
    try:
        yield built
    finally:
        for path in roots:
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)


def unordered_both_ways(built, x: Event, y: Event) -> None:
    assert built.order(x, y) == "unordered" and built.order(y, x) == "unordered"


def seam_with_view(root: Path, view) -> verify.LogSeam:
    """The production seam, answering `view` for `root` and the engine's
    inspection for every other root."""
    production = log_seam()
    return replace(
        production,
        inspect_registered=lambda target: view if Path(target).resolve() == root.resolve() else production.inspect_registered(target),
    )

def overlapping_builds(world) -> tuple[Event, Event, str, str, str, str]:
    """Spec §4.3: E3 preflights at h0 and captures A; `a` commits; E1
    preflights at h0, captures A then B, publishes; `b` appends; E3 captures B
    and publishes; E2 and E4 follow. Returns (a, b, e1, e2, e3, e4)."""
    reached_b = threading.Event()
    release_b = threading.Event()
    e3_thread_id: list[int] = []
    original = epoch._root_state_for

    def gated(carrier: Path, factory):
        if threading.get_ident() in e3_thread_id and Path(carrier).resolve() == world.beta.resolve():
            reached_b.set()
            assert release_b.wait(60), "the gated build was never released"
        return original(carrier, factory)

    outcome: dict[str, object] = {}

    def build_e3() -> None:
        e3_thread_id.append(threading.get_ident())
        try:
            outcome["e3"] = world.build()
        except BaseException as caught:  # noqa: BLE001 - surfaced by the join below
            outcome["error"] = caught

    epoch._root_state_for = gated  # restored in the finally
    thread = threading.Thread(target=build_e3, name="cut36-e3")
    try:
        thread.start()
        assert reached_b.wait(60), "E3 never reached B's capture"
        a = world.freeze()          # after E3's A capture, before E1's
        e1 = world.build()          # preflight at h0: nothing is published yet
        b = world.intent()          # after E1's B capture, before E3's
    finally:
        # Whatever failed above, the gated thread is released and joined
        # before the fixture tears the roots down under it.
        release_b.set()
        thread.join(120)
        epoch._root_state_for = original
    assert not thread.is_alive() and "error" not in outcome, outcome.get("error")
    e3 = str(outcome["e3"])
    e2 = world.build()
    e4 = world.build()
    # The schedule's own obligations, asserted rather than assumed.
    assert world.recorded_world_head(e1) == world.recorded_world_head(e3)  # both built from h0
    assert epochs_ordered(world.config, e1, e3) == "unordered" and epochs_ordered(world.config, e3, e1) == "unordered"
    assert epochs_ordered(world.config, e1, e2) == "ordered" and epochs_ordered(world.config, e3, e4) == "ordered"
    live_a, live_b = view_of(world.alpha), view_of(world.beta)
    a_moment, b_moment = events.moment(live_a, a.digest), events.moment(live_b, b.digest)
    assert a_moment is not None and b_moment is not None
    for identity, on_a, on_b in ((e1, True, False), (e3, False, True)):
        pa = events.place(live_a, genesis_digest=world.anchor_for(identity, world.a).genesis_digest, head_digest=world.anchor_for(identity, world.a).head_digest)
        pb = events.place(live_b, genesis_digest=world.anchor_for(identity, world.b).genesis_digest, head_digest=world.anchor_for(identity, world.b).head_digest)
        assert pa is not None and pb is not None
        assert events.contains(pa, a_moment) is on_a and events.contains(pb, b_moment) is on_b
    return a, b, e1, e2, e3, e4

def test_l8a_a_freeze_before_a_run_intent_across_ordered_cuts_orders_and_is_antisymmetric_durably(world):
    a = world.freeze()
    e1 = world.build()
    b = world.run_intent()
    e2 = world.build()
    assert epochs_ordered(world.config, e1, e2) == "ordered"
    assert world.order(a, b) == "a-precedes-b"
    assert world.order(b, a) == "b-precedes-a"


def test_l8b_co_appearance_is_unordered_and_later_cuts_holding_both_do_not_reverse_a_witness_durably(world):
    """Two claims, and the second is what the exclusion clause defends: with
    exclusion dropped, E2 and E3 (both holding both events) would witness
    `b` before `a` too, and the answer would collapse to `unordered`."""
    a, b = world.freeze(), world.intent()
    world.build()
    world.build()
    unordered_both_ways(world, a, b)
    c = world.freeze()
    world.build()
    d = world.intent()
    world.build()
    world.build()
    assert world.order(c, d) == "a-precedes-b" and world.order(d, c) == "b-precedes-a"


def test_l8c_epoch_sequence_numbers_are_read_by_nothing_durably(world):
    assert [name for name in dir(epoch.Epoch) if "sequence" in name] == []
    for core in (verify._ordered_by_descent, verify._witnessed, verify._event_order):
        code, _docstring, rest = inspect.getsource(core).split('"""', 2)
        assert "sequence" not in code + rest, core.__name__


def test_l8d_a_cut_covering_one_corpus_establishes_nothing_durably(world):
    a = world.freeze()
    world.build(world.a)          # A only: no anchor for B
    b = world.intent()
    world.build(world.a)          # A only again
    unordered_both_ways(world, a, b)
    c = world.freeze()
    world.build()                 # both: the covering pair begins
    d = world.intent()
    world.build()
    assert world.order(c, d) == "a-precedes-b"
    unordered_both_ways(world, a, b)  # b was in every covering cut that holds a: still unwitnessed


def test_l8e_a_chain_replaced_under_another_fork_genesis_establishes_nothing_durably(world):
    a = world.freeze()
    e1 = world.build()
    b = world.intent()
    world.build()
    assert world.order(a, b) == "a-precedes-b"
    replace_chain_under_another_fork_genesis(world.alpha)
    a2 = world.freeze()            # appends under the new genesis
    e3 = world.build()             # E3 places A (new genesis) and B; holds both
    live_genesis = view_of(world.alpha).genesis.digest
    assert world.anchor_for(e3, world.a).genesis_digest == live_genesis
    assert world.anchor_for(e1, world.a).genesis_digest != live_genesis
    unordered_both_ways(world, a2, b)
    with pytest.raises(EventUnknown):
        world.order(a, b)          # the old chain's registration is gone


def test_l8f_the_double_witness_is_unordered_durably(world):
    a, b, _e1, _e2, _e3, _e4 = overlapping_builds(world)
    unordered_both_ways(world, a, b)


def test_l8g_valid_prefix_truncation_invalidates_every_witness_and_unknowns_the_removed_event_durably(world):
    a = world.freeze()
    a_settled = settlement_of(world.alpha, a.digest).digest
    later = world.freeze()         # E1's A head will sit after this
    e1 = world.build()
    b = world.intent()
    e2 = world.build()
    assert world.order(a, b) == "a-precedes-b"
    truncate_after(world.alpha, keep_through=a_settled)   # every cut's A head is now beyond the tip
    for identity in (e1, e2):
        anchor = world.anchor_for(identity, world.a)
        assert events.place(view_of(world.alpha), genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) is None
    unordered_both_ways(world, a, b)
    with pytest.raises(EventUnknown):
        world.order(later, b)


def test_l8h_same_chain_orders_by_ancestry_and_equal_moments_are_unordered_durably(world):
    first = world.freeze()
    second = world.freeze()
    assert world.order(first, second) == "a-precedes-b" and world.order(second, first) == "b-precedes-a"
    settled = Event(world.a, settlement_of(world.alpha, second.digest).digest)
    unordered_both_ways(world, second, settled)
    assert world.order(second, second) == "unordered"
    genesis = Event(world.a, view_of(world.alpha).genesis.digest)
    assert world.order(genesis, first) == "a-precedes-b"


def test_l8i_a_pending_or_rolled_back_registration_has_no_moment_durably(world):
    """Stand-in inspection for A only: the live chain plus a pending and a
    rolled-back registration, by entry class; the world and B are the engine's."""
    first = world.freeze()
    world.build()
    live = view_of(world.alpha)
    pending = registration(digest("cut36-pending"), "tx-p", (("p.md", ABSENT),), (("p.md", state("p.md")),))
    rolled = registration(digest("cut36-rolled"), "tx-r", (("r.md", ABSENT),), (("r.md", state("r.md")),))
    rolled_back = settlement(digest("cut36-rolled-settled"), rolled.digest, "tx-r", committed=False)
    fabricated = chain(live.genesis, *live.entries[1:], pending, rolled, rolled_back)
    seam = seam_with_view(world.alpha, fabricated)
    for digest_ in (pending.digest, rolled.digest, rolled_back.digest):
        assert verify._event_order(world.config, first, Event(world.a, digest_), seam=seam) == "unordered"
        assert verify._event_order(world.config, Event(world.a, digest_), first, seam=seam) == "unordered"


def test_l8j_same_chain_independence_from_a_malformed_carrier_and_world_chain_durably(world, work_directory):
    first = world.freeze()
    second = world.freeze()
    identity = world.build()
    b = world.intent()
    (world.config.world_root / "epochs" / identity / "anchors.yaml").unlink()   # a malformed retained carrier
    assert world.order(first, second) == "a-precedes-b"
    with pytest.raises(EpochMalformed):
        world.order(first, b)
    aside = Path(mkdtemp(prefix="cut36-aside-", dir=work_directory))
    shutil.move(str(world.config.world_root / "epochs" / identity), str(aside / identity))  # out of `epochs/`
    rewrite_an_interior_entry(world.config.world_root)                            # a malformed world chain
    assert world.order(first, second) == "a-precedes-b"
    assert world.order(first, b) == "unordered"
    shutil.rmtree(aside, ignore_errors=True)


def test_l8k_the_refusals_and_a_terminal_corpus_durably(world, work_directory):
    first = world.freeze()
    second = world.freeze()
    with pytest.raises(EventCorpusUnknown):
        world.order(Event("0" * 32, first.digest), second)
    with pytest.raises(EventUnknown):
        world.order(Event(world.a, world.intent().digest), second)      # B's digest asked of A
    twin = Path(mkdtemp(prefix="cut36-twin-", dir=work_directory))
    shutil.copytree(world.alpha, twin, dirs_exist_ok=True, symlinks=True)   # a second root claiming A's id
    try:
        with pytest.raises(EventCorpusUnresolvable):
            event_order(replace(world.config, corpus_roots=(*world.config.corpus_roots, twin)), first, second)
    finally:
        shutil.rmtree(twin, ignore_errors=True)
    assert event_order(replace(world.config, corpus_roots=(*world.config.corpus_roots, world.alpha)), first, second) == "a-precedes-b"
    with pytest.raises(EventCorpusUnresolvable):
        event_order(replace(world.config, corpus_roots=(world.beta,)), first, second)
    with _operation_lock_for(world.alpha).capture(), pytest.raises(BuildHold):
        world.order(first, second)
    world.world.retire(world.a)
    assert world.order(first, second) == "a-precedes-b"


def test_l4a_a_deleted_chain_refutes_against_its_registry_anchor_bound_by_corpus_id_durably(world):
    """Relabel unit; the cut document cites every clause of cuts 8 and 9."""
    world.freeze()
    records = anchor_heads(world.world, frozenset({world.a, world.b}))
    assert {record.subject for record in records} == {anchors.CorpusSubject(world.a), anchors.CorpusSubject(world.b)}
    shutil.rmtree(chain_dir(world.alpha))
    observers = verify.ObserverSet(tuple(verify.RegistryCarrier.from_record(record) for record in records))
    report = audit_log(world.config, anchors.CorpusSubject(world.a), world.alpha, observers, actor="alice")
    assert report.outcome == "refuted"
    assert report.observer_bound and all(world.a in label for label in report.observer_bound)  # bound to A's subject, never B's
    sibling = audit_log(world.config, anchors.CorpusSubject(world.b), world.beta, observers, actor="alice")
    assert sibling.outcome == "validated"

def test_l10a_a_replica_under_a_fresh_manifest_refuses_subject_mismatch_at_arrival_durably(world, work_directory):
    """Relabel unit; cut 8's L10u1 construction: replicate A, rewrite the copy's
    `corpus.yaml` to a fresh id, arrive as a replica of A."""
    world.freeze()
    copy = Path(mkdtemp(prefix="cut36-replica-", dir=work_directory)) / "copy"
    replicate_root(world.alpha, copy, authority=FULL)
    fresh_id = "f" * 32
    manifest = registry.load_manifest(copy)
    (copy / "corpus.yaml").write_bytes(registry.manifest_bytes(replace(manifest, corpus_id=fresh_id)))
    try:
        with pytest.raises(SubjectMismatch):
            admit_arrival(world.world, copy, ReplicaOf(world.a), verify.ObserverSet(()))
    finally:
        shutil.rmtree(copy.parent, ignore_errors=True)
        shutil.rmtree(metadata_root_for(copy), ignore_errors=True)

def test_bi1_recovery_precedes_resolution_on_both_paths_durably(world, monkeypatch):
    first, second = world.freeze(), world.freeze()
    b = world.intent()
    order: list[str] = []
    production = log_seam()
    seam = replace(
        production,
        inspect_registered=lambda root: order.append("inspect-world" if Path(root).resolve() == world.config.world_root else "inspect-corpus") or production.inspect_registered(root),
    )
    original = registry._scan_registry
    monkeypatch.setattr(registry, "_scan_registry", lambda root: order.append("scan") or original(root))
    assert verify._event_order(world.config, first, second, seam=seam) == "a-precedes-b"
    assert order[:2] == ["inspect-world", "scan"]
    order.clear()
    verify._event_order(world.config, first, b, seam=seam)
    assert order[:2] == ["inspect-world", "scan"]


def test_bi2_one_world_inspection_and_the_world_lock_released_before_sorted_unnested_corpus_locks_durably(world):
    a = world.freeze()
    world.build()
    b = world.intent()
    world.build()
    seen: list[Path] = []
    world_free: list[bool] = []
    corpus_free: list[bool] = []
    world_lock = registry._world_lock_for(world.config.world_root)
    production = log_seam()

    def inspect_registered(root: Path):
        seen.append(Path(root).resolve())
        if Path(root).resolve() != world.config.world_root:
            free = world_lock.acquire(blocking=False)
            world_free.append(free)
            if free:
                world_lock.release()
            other = world.beta if Path(root).resolve() == world.alpha.resolve() else world.alpha
            corpus_free.append(_operation_lock_for(other)._holder is None)
        return production.inspect_registered(root)

    assert verify._event_order(world.config, a, b, seam=replace(production, inspect_registered=inspect_registered)) == "a-precedes-b"
    assert seen.count(world.config.world_root) == 1
    assert world_free == [True, True]
    assert corpus_free == [True, True]
    assert seen[1:] == [world.alpha.resolve(), world.beta.resolve()]


def test_bi3_the_genesis_clause_alone_decides_a_placement_durably(world):
    """Spec §8.2 case 4, isolated on the anchor's side: a genuine well-formed
    view, the epoch's own anchor with its reachable head, only the declared
    genesis replaced."""
    world.freeze()
    identity = world.build()
    live = view_of(world.alpha)
    anchor = world.anchor_for(identity, world.a)
    assert events.place(live, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) is not None
    assert events.place(live, genesis_digest=digest("cut36-other-genesis"), head_digest=anchor.head_digest) is None
