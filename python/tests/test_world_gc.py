"""Whole-epoch garbage collection: §9's explicit `delete_epoch`.

**Deletion is consumer policy, and it is whole-epoch.** Nothing in the package
calls it, nothing schedules it, and there is no act whose subject is one member
of one epoch. An epoch is published by one transaction and removed by one
transaction, and the arms below assert both halves of that: the plan holds a
`DeleteOp` for each of the eleven members and nothing else, and no production
module reaches the act at all.

**The refusals come before the transaction, and in a fixed order.** Under one
acquisition of the world lock the act crosses the recovery barrier, reads
`current`, refuses the epoch the pointer names, and only then opens the target.
Every one of those refusals leaves the world byte-for-byte as it found it,
which is what the plan-count and tree comparisons below are for.

**Every carrier the report is computed over is read the strong way.** The
sever report answers "does another retained epoch still carry this identity?",
so it has to read those epochs — and §8.1's rule is that an epoch this world
cannot read refuses the act reading it. A damaged epoch *elsewhere* therefore
refuses the whole deletion, exactly as it refuses a rule removal: a report
computed over a scan that skipped one would be the silent unresolvability §4.3
exists to prevent.

**The emptied directory is nonsemantic, and that has teeth.** §9 leaves the
directory behind. An empty directory read as a carrier would be a carrier
missing all eleven members, so one deletion would make every later scan of
``epochs/`` refuse and would make §9's own "a repeated deletion raises
`EpochUnknown`" report `EpochMalformed` instead. Two arms hold that door open:
the sever scan still runs after a deletion, and the deleted bytes can be
published back into the directory they were deleted from.
"""

from __future__ import annotations

import inspect
import re
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from authority import ACTOR, narrowed
from nodes.core.write_plan import DefaultExecutor, DeleteOp
from test_world_build import ALPHA, BETA, GAMMA, ChainHeads
from test_world_epoch import (
    CountingLock,
    admitted_world,
    carrier_bytes,
    epochs_tree,
    publish,
)
from test_world_receipts import producer_successor

import beliefs
from beliefs.errors import EpochCurrent, EpochMalformed, EpochUnknown, PermitExceeded
from beliefs.world import epoch, read, registry, rules

# --- the harness -------------------------------------------------------------
#
# `test_world_epoch` owns world construction, publication and the recording
# executor; what this module adds is the two retained-epoch shapes deletion
# needs — several epochs at once, and a *sibling* publication that shares some
# of a target's identities without sharing all of them.

RECEIPT_MEMBERS = tuple(member for member in epoch.EPOCH_MEMBERS if member in epoch.RECEIPT_KINDS)


def three_retained(tmp_path: Path):
    """Three retained epochs over widening coverage, the last of them current.

    Widening coverage rather than repeated builds, because two epochs over the
    same corpora at the same states publish the same bytes: an arm about "some
    other retained epoch" needs the others to be genuinely other.
    """
    world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA, GAMMA))
    first = publish(world, (ALPHA,), bindings)
    second = publish(world, (ALPHA, BETA), bindings)
    third = publish(world, (ALPHA, BETA, GAMMA), bindings)
    return world, recorder, bindings, (first, second, third)


def test_e1_delete_epoch_under_a_permit_lacking_epoch_refuses_and_keeps_the_members(tmp_path):
    world, _recorder, _bindings, (first, _second, _third) = three_retained(tmp_path)
    narrowed_world = registry.World(
        world.config,
        world._executor_factory,
        chain_head=world._chain_head,
        corpus_executor_factory=world._corpus_executor_factory,
        authority=narrowed(families=("registry",)),
    )
    members = world.config.world_root / "epochs" / first.packaging_identity
    before = sorted(path.name for path in members.iterdir())
    with pytest.raises(PermitExceeded):
        epoch.delete_epoch(narrowed_world, first.packaging_identity)
    assert sorted(path.name for path in members.iterdir()) == before


def sibling_published(tmp_path: Path):
    """Two epochs over one coverage, differing only in which implementation of
    the producer rule derived the snapshot.

    A *non-behavioural* successor: same symbol, same fixtures, same computed
    snapshot, different implementation identity. So the two epochs carry the
    same producer-snapshot identity and the same retraction, certification and
    coreference receipts, and disagree on exactly one thing — the producer
    receipt, whose identity digests the implementation that produced it. That
    is the only honest way to get a target some of whose identities survive it
    and some of which do not.
    """
    world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA,))
    first = publish(world, (ALPHA,), bindings)
    sibling = rules.install_rule_binding(world, producer_successor(behavioural=False))
    second = publish(
        world,
        (ALPHA,),
        epoch.DerivationBindings(
            producer=sibling,
            retraction=bindings.retraction,
            certification=bindings.certification,
            coreference=bindings.coreference,
        ),
    )
    return world, recorder, bindings, first, second


BARRIER_PREAMBLE = re.compile(r"with world\._state\.lock:\s*\n\s*world\._chain_head\(")
"""The hand-written preamble `_locked_barrier` replaced. Five acts carried a
copy of it, and the order of its two lines is the whole of §8.1's guarantee."""


# --- Step 1: the refusals, and the order they are decided in ------------------


class TestRefusalOrder:
    def test_delete_takes_one_lock_and_recovers_before_it_reads_current(self, monkeypatch, tmp_path):
        """§8.1's order, and the arm is written so it can fail.

        The barrier observation records whether the lock was *already held*
        when recovery ran, and the pointer read records that it ran after. A
        deletion that read `current` first, or that crossed the barrier outside
        the lock, changes this sequence rather than merely failing to reassure.
        """
        heads = ChainHeads()
        world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA), chain_head=heads)
        first = publish(world, (ALPHA,), bindings)
        publish(world, (ALPHA, BETA), bindings)
        counting = CountingLock()
        cast(Any, world._state).lock = counting
        order: list[tuple[str, bool]] = []
        cast(Any, heads).observe = lambda _target: order.append(("barrier", counting.locked()))
        pointer = epoch._locked_current_identity
        loader = epoch._locked_open_epoch
        monkeypatch.setattr(
            epoch,
            "_locked_current_identity",
            lambda world_root: (order.append(("pointer", counting.locked())), pointer(world_root))[1],
        )
        monkeypatch.setattr(
            epoch,
            "_locked_open_epoch",
            lambda world_root, identity: (
                order.append(("open", counting.locked())),
                loader(world_root, identity),
            )[1],
        )
        cast(Any, recorder).interpose = lambda root, plan: (
            order.append(("execute", counting.locked())),
            DefaultExecutor(root).execute(plan),
        )[1]

        epoch.delete_epoch(world, first.packaging_identity)

        assert [stage for stage, _held in order] == ["barrier", "pointer", "open", "open", "execute"]
        assert {held for _stage, held in order} == {True}
        assert counting.acquisitions == 1
        assert not counting.locked()
        assert heads.roots[-1] == world.config.world_root

    def test_delete_current_epoch_refuses(self, tmp_path):
        """The one epoch a world is pointing at is not garbage.

        The refusal is decided from `current` alone, *before* the target's
        bytes are read: the second half of this arm damages the current
        carrier and still gets `EpochCurrent`, because "you may not delete this
        one" is an answer about the world's state rather than about the
        carrier's health.
        """
        world, recorder, _bindings, (first, _second, third) = three_retained(tmp_path)
        before = epochs_tree(world)
        submitted = len(recorder.epoch_plans)

        with pytest.raises(EpochCurrent) as refusal:
            epoch.delete_epoch(world, third.packaging_identity)

        assert epoch.CURRENT_POINTER in str(refusal.value)
        assert third.packaging_identity in str(refusal.value)
        assert epochs_tree(world) == before
        assert len(recorder.epoch_plans) == submitted
        assert read.current_epoch(world).packaging_identity == third.packaging_identity
        # A non-current epoch of the same world deletes, so the refusal was
        # about the pointer rather than about deletion.
        epoch.delete_epoch(world, first.packaging_identity)

        (world.config.world_root / "epochs" / third.packaging_identity / "coverage.yaml").unlink()
        with pytest.raises(EpochCurrent):
            epoch.delete_epoch(world, third.packaging_identity)

    def test_an_unknown_identity_refuses(self, tmp_path):
        world, recorder, _bindings, _retained = three_retained(tmp_path)
        before = epochs_tree(world)
        submitted = len(recorder.epoch_plans)

        with pytest.raises(EpochUnknown):
            epoch.delete_epoch(world, "0" * 64)
        with pytest.raises(EpochUnknown):
            epoch.delete_epoch(world, "not-a-packaging-identity")

        assert epochs_tree(world) == before
        assert len(recorder.epoch_plans) == submitted

    @pytest.mark.parametrize(
        "sabotage",
        [
            "pointer-malformed",
            "target-member-missing",
            "other-member-missing",
            "other-identity-mismatch",
            "current-member-missing",
            "stray-epoch-entry",
        ],
    )
    def test_a_carrier_this_world_cannot_read_refuses_before_any_delete(self, tmp_path, sabotage):
        """§8.1's carrier rule, applied to every epoch a deletion has to read.

        `other-identity-mismatch` is the arm that pins the *strong* reading:
        the other carrier's member set is intact and its receipts parse, so the
        sever scan alone would sail past it. Only recomputing its packaging
        identity — which is what `_locked_open_epoch` does and what §8.1
        requires of every read of an epoch — catches it.
        """
        world, recorder, _bindings, (first, second, third) = three_retained(tmp_path)
        epochs = world.config.world_root / "epochs"

        if sabotage == "pointer-malformed":
            (epochs / epoch.CURRENT_POINTER).write_bytes(b"not-a-packaging-identity\n")
        elif sabotage == "target-member-missing":
            (epochs / first.packaging_identity / "coverage.yaml").unlink()
        elif sabotage == "other-member-missing":
            (epochs / second.packaging_identity / "anchors.yaml").unlink()
        elif sabotage == "other-identity-mismatch":
            path = epochs / second.packaging_identity / "anchors.yaml"
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document["world"]["head_digest"] = "tip:a-head-this-epoch-was-not-anchored-against"
            path.write_bytes(yaml.safe_dump(document, sort_keys=True, allow_unicode=True).encode("utf-8"))
        elif sabotage == "current-member-missing":
            (epochs / third.packaging_identity / "coverage.yaml").unlink()
        else:
            (epochs / "notes.yaml").write_bytes(b"note: extra\n")

        before = epochs_tree(world)
        submitted = len(recorder.epoch_plans)
        with pytest.raises(EpochMalformed):
            epoch.delete_epoch(world, first.packaging_identity)

        assert epochs_tree(world) == before
        assert len(recorder.epoch_plans) == submitted

# --- Step 2: the whole epoch, and the sever report ----------------------------


class TestWholeEpochDeletion:
    def test_one_plan_deletes_exactly_the_eleven_members(self, tmp_path):
        """One transaction, eleven `DeleteOp`s, and nothing else in it.

        Not the pointer, not another epoch's member, not a directory: §9 says
        the transaction contains a `DeleteOp` for every target member, and
        "every" is also "only". Each expected digest is recomputed here from
        the bytes on disk rather than taken from the module under test.
        """
        world, recorder, _bindings, (first, second, third) = three_retained(tmp_path)
        members = carrier_bytes(world, first.packaging_identity)
        submitted = len(recorder.epoch_plans)

        epoch.delete_epoch(world, first.packaging_identity)

        assert len(recorder.epoch_plans) == submitted + 1
        plan = cast(list[DeleteOp], recorder.epoch_plans[-1])
        assert [type(operation) for operation in plan] == [DeleteOp] * len(epoch.EPOCH_MEMBERS)
        assert [operation.path for operation in plan] == [
            f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS
        ]
        assert [operation.expected_digest for operation in plan] == [
            sha256(members[member]).hexdigest() for member in epoch.EPOCH_MEMBERS
        ]
        # The other two carriers are untouched, byte for byte.
        assert read.open_epoch(world, second.packaging_identity).members == second.members
        assert read.open_epoch(world, third.packaging_identity).members == third.members

    def test_delete_noncurrent_epoch_reports_severed_identities(self, tmp_path):
        """§9's report: the actor, the producer-snapshot identity, the four
        receipt identities, and which of them nothing else carries.

        The two retained epochs here differ in exactly one thing — which
        implementation of the producer rule derived the snapshot — so the
        target's producer receipt is uniquely its own while its snapshot and
        its other three receipts are also carried by the epoch that stays.
        A report that flagged all five, or none, would be describing a
        different world.
        """
        world, _recorder, _bindings, first, second = sibling_published(tmp_path)
        assert read.current_epoch(world).packaging_identity == second.packaging_identity

        report = epoch.delete_epoch(world, first.packaging_identity)

        assert report.actor == ACTOR
        assert report.packaging_identity == first.packaging_identity
        assert report.snapshot is not None
        assert report.snapshot.subject == epoch.SNAPSHOT_SUBJECT
        assert report.snapshot.identity == first.receipts["producer-receipt.yaml"].subject_identity
        assert report.snapshot.retained_elsewhere is True
        assert [entry.subject for entry in report.receipts] == list(epoch.DERIVATION_KINDS)
        assert [entry.identity for entry in report.receipts] == [
            first.receipts[member].identity for member in RECEIPT_MEMBERS
        ]
        assert {entry.subject: entry.retained_elsewhere for entry in report.receipts} == {
            "producer": False,
            "retraction-enumeration": True,
            "certification-enumeration": True,
            "coreference-reduction": True,
        }
        assert report.severed == (first.receipts["producer-receipt.yaml"].identity,)
        # And the survivor really does still carry the four it was credited with.
        surviving = read.open_epoch(world, second.packaging_identity)
        assert surviving.receipts["producer-receipt.yaml"].subject_identity == report.snapshot.identity
        assert {surviving.receipts[member].identity for member in RECEIPT_MEMBERS} >= {
            entry.identity for entry in report.receipts if entry.retained_elsewhere
        }

    def test_every_identity_of_a_uniquely_carried_epoch_is_severed(self, tmp_path):
        """The other half: an epoch whose coverage nothing else observed
        carries five identities of its own, and deleting it strands all five."""
        world, _recorder, _bindings, (first, _second, _third) = three_retained(tmp_path)

        report = epoch.delete_epoch(world, first.packaging_identity)

        assert report.actor == ACTOR
        assert report.snapshot is not None and report.snapshot.retained_elsewhere is False
        assert [entry.retained_elsewhere for entry in report.receipts] == [False] * 4
        assert report.severed == tuple(
            sorted(
                {report.snapshot.identity, *(entry.identity for entry in report.receipts)}
            )
        )
        assert len(report.severed) == 5

    def test_a_repeated_deletion_is_unknown_and_adds_no_tombstone(self, tmp_path):
        """§9 makes no exact-retry claim after commit. The second call is
        `EpochUnknown`, and nothing was written to say so."""
        world, recorder, _bindings, (first, _second, third) = three_retained(tmp_path)
        directory = world.config.world_root / "epochs" / first.packaging_identity

        epoch.delete_epoch(world, first.packaging_identity)
        submitted = len(recorder.epoch_plans)

        assert list(directory.iterdir()) == []
        with pytest.raises(EpochUnknown):
            epoch.delete_epoch(world, first.packaging_identity)
        with pytest.raises(EpochUnknown):
            read.open_epoch(world, first.packaging_identity)
        assert len(recorder.epoch_plans) == submitted
        assert read.current_epoch(world).packaging_identity == third.packaging_identity

    def test_an_emptied_directory_does_not_poison_the_epoch_scan(self, tmp_path):
        """The regression §9's "nonsemantic" sentence is really about.

        `rules.remove_rule_binding` scans every retained epoch and refuses on
        any carrier it cannot read. If the directory a deletion emptied read as
        a carrier, it would be a carrier missing all eleven members — and one
        deletion would make every rule removal in that world refuse for ever.
        """
        world, _recorder, bindings, (first, _second, _third) = three_retained(tmp_path)

        epoch.delete_epoch(world, first.packaging_identity)
        report = rules.remove_rule_binding(world, bindings.coreference)

        assert len(report.severed_receipts) == 2

    def test_a_deleted_epoch_republishes_into_the_directory_it_left(self, tmp_path):
        """Deletion is not a headstone either. The same bytes build again and
        land back in the emptied directory, because an empty directory is not
        a same-name carrier holding different bytes."""
        world, _recorder, bindings, (first, _second, _third) = three_retained(tmp_path)
        members = carrier_bytes(world, first.packaging_identity)

        epoch.delete_epoch(world, first.packaging_identity)
        rebuilt = publish(world, (ALPHA,), bindings)

        assert rebuilt.packaging_identity == first.packaging_identity
        assert carrier_bytes(world, rebuilt.packaging_identity) == members
        assert read.current_epoch(world).packaging_identity == first.packaging_identity

    def test_deleting_one_epoch_leaves_every_other_byte_alone(self, tmp_path):
        world, _recorder, _bindings, (first, second, third) = three_retained(tmp_path)
        before = epochs_tree(world)
        removed = {
            f"{first.packaging_identity}/{member}": before[f"{first.packaging_identity}/{member}"]
            for member in epoch.EPOCH_MEMBERS
        }

        epoch.delete_epoch(world, first.packaging_identity)

        assert epochs_tree(world) == {
            name: content for name, content in before.items() if name not in removed
        }
        assert second.packaging_identity in str(sorted(epochs_tree(world)))
        assert third.packaging_identity in str(sorted(epochs_tree(world)))


class TestNoOtherDeletionSurface:
    def test_no_individual_member_or_automatic_deletion_api_exists(self, tmp_path):
        """§9's two closures, asserted rather than described.

        *No individual-member deletion*: the one act takes a packaging identity,
        and no exported callable takes a member at all. *Nothing
        automatic*: no module of the package calls `delete_epoch`, so the only
        way an epoch is removed is a consumer deciding to remove it.
        """
        import beliefs.world as facade

        assert set(inspect.signature(epoch.delete_epoch).parameters) == {
            "world",
            "packaging_identity",
        }
        deleting = [
            name
            for name in facade.__all__
            if callable(getattr(facade, name)) and name.startswith(("delete", "remove", "prune", "collect"))
        ]
        assert sorted(deleting) == ["delete_epoch", "remove_rule_binding"]
        for name in facade.__all__:
            value = getattr(facade, name)
            if callable(value):
                assert not set(inspect.signature(value).parameters) & {
                    "member",
                    "member_name",
                    "epoch_member",
                }, name

        package = Path(beliefs.__file__).parent
        callers = sorted(
            path.relative_to(package).as_posix()
            for path in package.rglob("*.py")
            if "delete_epoch(" in path.read_text(encoding="utf-8")
        )
        assert callers == ["world/epoch.py"]
        source = (package / "world" / "epoch.py").read_text(encoding="utf-8")
        assert source.count("delete_epoch(") == 1, "the act is defined once and invoked nowhere"

    def test_a_deletion_plan_is_the_only_thing_that_removes_an_epoch_member(self, tmp_path):
        """No other act this package can perform submits a delete beneath
        ``epochs/``. Publishing three epochs and removing a rule binding
        exercises every writing act the world layer has."""
        world, recorder, bindings, (first, _second, _third) = three_retained(tmp_path)
        rules.remove_rule_binding(world, bindings.coreference)

        assert [
            operation.path
            for plan in recorder.plans
            for operation in plan
            if isinstance(operation, DeleteOp) and operation.path.startswith("epochs/")
        ] == []

        epoch.delete_epoch(world, first.packaging_identity)

        assert sorted(
            operation.path
            for plan in recorder.plans
            for operation in plan
            if isinstance(operation, DeleteOp) and operation.path.startswith("epochs/")
        ) == sorted(f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS)


class TestTheLockedBarrier:
    def test_every_epoch_act_crosses_the_barrier_through_one_context_manager(self):
        """The preamble is written once. Five acts had their own copy of "take
        the lock, then cross the barrier" and the order between those two lines
        is the whole of §8.1's guarantee — a copy that drifted would be a
        reader crossing a barrier a publication then invalidated."""
        package = Path(beliefs.__file__).parent / "world"
        for path in sorted(package.glob("*.py")):
            assert not BARRIER_PREAMBLE.search(path.read_text(encoding="utf-8")), path.name
        assert "world._state.lock" not in Path(read.__file__ or "").read_text(encoding="utf-8")
        assert inspect.isgeneratorfunction(registry._locked_barrier.__wrapped__)

    def test_the_barrier_yields_the_world_root_under_the_held_lock(self, tmp_path):
        heads = ChainHeads()
        world, _recorder, _bindings, _roots = admitted_world(tmp_path, (ALPHA,), chain_head=heads)
        counting = CountingLock()
        cast(Any, world._state).lock = counting

        with registry._locked_barrier(world) as world_root:
            assert world_root == world.config.world_root
            assert counting.locked()
            assert heads.roots[-1] == world.config.world_root
        assert not counting.locked()
        assert counting.acquisitions == 1
