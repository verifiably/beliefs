"""Publishing an epoch, and opening one back: §6 and §8.1's carrier half.

**What an epoch is here.** Eleven deterministic closed documents in one
content-addressed directory, created by exactly one world-root transaction
together with the one-line `current` pointer beside it. The directory's name is
the digest of the members it holds, computed from the complete bytes *before*
anything is written, so the name is a claim the bytes themselves settle. Every
arm below turns on that: a member edited by hand does not merely disagree with
a stored digest, it makes the directory misnamed.

**The two layers §8.2 separates, exercised as two layers.** The carrier layer
refuses an epoch whose member set, YAML, or packaging identity is wrong. It
does *not* refuse a receipt whose document parses and then violates §7.5's
contract — that receipt opens, reaches Task 10's validator, and evaluates as
``malformed`` there. One arm below publishes a contract-violating receipt into
a well-formed carrier and proves it opens, because a carrier layer that
refused it would close the path §8.2 exists to keep open.

**Concurrency is event-driven.** The interleaving arms gate a transaction
half-applied and prove a reader blocks rather than reading the applied prefix.
Nothing sleeps: a sleep would turn "the reader could not observe it" into "the
reader did not observe it within a second".
"""

from __future__ import annotations

import inspect
import threading
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path
from typing import Any, Self

import pytest
import yaml
from authority import FULL
from coordination_fixtures import content_for, coordination_profile, mounted_root
from nodes.core.corpus import Corpus
from nodes.core.write_plan import CreateOp, DefaultExecutor, ReplaceOp, WriteOp, WritePlan
from test_world_build import (
    ALPHA,
    BETA,
    GAMMA,
    JOIN_TIMEOUT,
    ChainHeads,
    corpus_at,
    genesis_of,
    install_bindings,
    sample_nodes,
    slug_for,
    tip_of,
)

from beliefs import stored
from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import EpochMalformed, EpochUnknown
from beliefs.identity import v1
from beliefs.world import derive, epoch, read, registry


def test_coordination_bytes_move_corpus_state_but_never_become_captured_world_records(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    writer = CorpusWriter(
        root,
        DefaultExecutor, authority=FULL,
        coordination_resolver=CoordinationResolver({root: profile}),
        profile=profile,
    )
    before = registry.corpus_state_identity(root)
    project = writer.mint_coordination("project", content=content_for("project"))
    after = registry.corpus_state_identity(root)
    assert after != before
    assert project.id not in {record.address for record in epoch._captured_records(root)}


def test_world_records_are_still_captured_beside_coordination_records(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    Corpus(root).add(
        stored.dataset_node(
            "world",
            title="world",
            resources=[{"name": "x", "digest": "sha256:" + "a" * 64}],
        )
    )
    writer = CorpusWriter(
        root,
        DefaultExecutor, authority=FULL,
        coordination_resolver=CoordinationResolver({root: profile}),
        profile=profile,
    )
    writer.mint_coordination("project", content=content_for("project"))
    assert {record.address for record in epoch._captured_records(root)} == {"dataset:world"}

# --- the harness -------------------------------------------------------------


class Recorder:
    """The world's write-plan executor factory, recording every plan submitted.

    A build's whole publication is one plan, and several arms below assert its
    exact contents, so the factory has to be the seam that sees it. `interpose`
    replaces the write for the one arm that needs a transaction to be observed
    half-applied; every other arm delegates to `DefaultExecutor` unchanged.
    """

    def __init__(self) -> None:
        self.plans: list[list[WriteOp]] = []
        self.interpose: Callable[[Path, list[WriteOp]], None] | None = None

    def __call__(self, root: Path) -> _RecordingExecutor:
        return _RecordingExecutor(Path(root), self)

    @property
    def epoch_plans(self) -> list[list[WriteOp]]:
        """Only the plans that touch ``epochs/``. Rule installation submits
        create-only plans through the same factory, and an arm counting *epoch*
        transactions must not count those."""
        return [plan for plan in self.plans if any(operation.path.startswith("epochs/") for operation in plan)]


class _RecordingExecutor:
    def __init__(self, root: Path, recorder: Recorder) -> None:
        self.root = root
        self._recorder = recorder

    def execute(self, plan: WritePlan) -> None:
        self._recorder.plans.append(list(plan))
        if self._recorder.interpose is not None:
            self._recorder.interpose(self.root, list(plan))
            return
        DefaultExecutor(self.root).execute(plan)


class CountingLock:
    """A `threading.Lock` that counts acquisitions.

    `current_epoch` must take the world lock exactly once and reach the private
    locked loader without re-entering it. The non-reentrant lock would deadlock
    on a second acquisition, so counting is what turns "it did not deadlock"
    into the stronger "it acquired once".
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.acquisitions = 0

    def acquire(self, *args: object, **kwargs: object) -> bool:
        taken = self._lock.acquire(*args, **kwargs)  # type: ignore[arg-type]
        if taken:
            self.acquisitions += 1
        return taken

    def release(self) -> None:
        self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()

    def __enter__(self) -> Self:
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


def make_world(
    tmp_path: Path,
    *corpus_roots: Path,
    chain_head: ChainHeads | None = None,
) -> tuple[registry.World, Recorder]:
    recorder = Recorder()
    world = registry.World(
        registry.WorldConfig(tmp_path / "world", "f" * 32, corpus_roots),
        recorder,
        chain_head=chain_head or ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
        authority=FULL,
    )
    return world, recorder


def derivation_bindings(world: registry.World) -> epoch.DerivationBindings:
    """Hold the four shipped rules and name them as one build input."""
    held = install_bindings(world)
    return epoch.DerivationBindings(
        producer=held["producer"],
        retraction=held["retraction-enumeration"],
        certification=held["certification-enumeration"],
        coreference=held["coreference-reduction"],
    )


def admitted_world(
    tmp_path: Path,
    coverage: tuple[str, ...] = (ALPHA,),
    *,
    chain_head: ChainHeads | None = None,
) -> tuple[registry.World, Recorder, epoch.DerivationBindings, dict[str, Path]]:
    roots = {
        corpus_id: corpus_at(tmp_path / corpus_id[:6], corpus_id, sample_nodes(slug_for(corpus_id, coverage)))
        for corpus_id in coverage
    }
    world, recorder = make_world(tmp_path, *roots.values(), chain_head=chain_head)
    for corpus_root in roots.values():
        world.admit(corpus_root, provenance=registry.Fresh())
    return world, recorder, derivation_bindings(world), roots


def publish(world: registry.World, coverage: tuple[str, ...], bindings: epoch.DerivationBindings) -> epoch.Epoch:
    return epoch.build_epoch(world, coverage=frozenset(coverage), bindings=bindings)


def carrier_bytes(world: registry.World, packaging_identity: str) -> dict[str, bytes]:
    directory = world.config.world_root / "epochs" / packaging_identity
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def epochs_tree(world: registry.World) -> dict[str, bytes]:
    """Every regular file beneath ``epochs/``, by root-relative path.

    The no-overwrite arms compare this before and after a refused rebuild: a
    refusal that left one member rewritten would be a refusal that had already
    published half an epoch.
    """
    base = world.config.world_root / "epochs"
    if not base.exists():
        return {}
    return {
        str(path.relative_to(base)): path.read_bytes() for path in sorted(base.rglob("*")) if path.is_file()
    }


def document(world: registry.World, packaging_identity: str, member: str) -> dict[str, Any]:
    """One epoch member, parsed. Every member §6 defines is a mapping keyed by
    string, so the arms below may index the result without re-asserting it."""
    path = world.config.world_root / "epochs" / packaging_identity / member
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict), member
    return parsed


def formula_packaging_identity(members: dict[str, bytes]) -> str:
    """§6.2, written out here rather than borrowed from the module under test."""
    return v1.digest(
        "science.epoch.v1",
        [[name, sha256(content).hexdigest()] for name, content in sorted(members.items())],
    )


# --- Step 1: the deterministic carrier ----------------------------------------


class TestTheDeterministicCarrier:
    def test_the_published_carrier_holds_exactly_the_eleven_members(self, tmp_path):
        world, _recorder, bindings, _roots = admitted_world(tmp_path)

        published = publish(world, (ALPHA,), bindings)

        base = world.config.world_root / "epochs"
        assert sorted(entry.name for entry in base.iterdir()) == sorted(
            [published.packaging_identity, epoch.CURRENT_POINTER]
        )
        assert set(carrier_bytes(world, published.packaging_identity)) == set(epoch.EPOCH_MEMBERS)
        assert len(epoch.EPOCH_MEMBERS) == 11
        assert set(published.members) == set(epoch.EPOCH_MEMBERS)

    def test_every_member_is_a_closed_deterministic_yaml_document(self, tmp_path):
        """Deterministic means the bytes are the canonical dump of their own
        value: re-dumping what the member parses to reproduces it exactly. A
        member that merely *happened* to be sorted would fail this the first
        time a key was inserted out of order."""
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))

        published = publish(world, (ALPHA, BETA), bindings)

        for member, content in carrier_bytes(world, published.packaging_identity).items():
            parsed = yaml.safe_load(content.decode("utf-8"))
            assert type(parsed) is dict, member
            canonical = yaml.safe_dump(parsed, sort_keys=True, allow_unicode=True).encode("utf-8")
            assert content == canonical, member
            assert content.endswith(b"\n"), member

    def test_the_anchors_member_carries_sorted_triples_and_the_world_head(self, tmp_path):
        heads = ChainHeads()
        world, _recorder, bindings, roots = admitted_world(tmp_path, (GAMMA, ALPHA, BETA), chain_head=heads)

        published = publish(world, (BETA, ALPHA, GAMMA), bindings)

        anchors = document(world, published.packaging_identity, "anchors.yaml")
        assert set(anchors) == {"corpora", "world"}
        assert anchors["corpora"] == [
            {
                "subject": corpus_id,
                "genesis_digest": genesis_of(roots[corpus_id]),
                "head_digest": tip_of(roots[corpus_id]),
            }
            for corpus_id in (ALPHA, BETA, GAMMA)
        ]
        assert [entry["subject"] for entry in anchors["corpora"]] == sorted(
            entry["subject"] for entry in anchors["corpora"]
        )
        assert anchors["world"] == {
            "subject": world.config.world_id,
            "genesis_digest": genesis_of(world.config.world_root),
            "head_digest": tip_of(world.config.world_root),
        }

    def test_the_coverage_member_carries_sorted_ids_and_captured_states(self, tmp_path):
        world, _recorder, bindings, roots = admitted_world(tmp_path, (BETA, ALPHA))
        states = {corpus_id: registry.corpus_state_identity(root) for corpus_id, root in roots.items()}

        published = publish(world, (BETA, ALPHA), bindings)

        coverage = document(world, published.packaging_identity, "coverage.yaml")
        assert coverage == {
            "coverage": [
                {"corpus_id": ALPHA, "corpus_state": states[ALPHA]},
                {"corpus_id": BETA, "corpus_state": states[BETA]},
            ]
        }
        assert published.coverage == ((ALPHA, states[ALPHA]), (BETA, states[BETA]))

    def test_the_packaging_identity_is_the_digest_of_sorted_member_pairs(self, tmp_path):
        world, _recorder, bindings, _roots = admitted_world(tmp_path)

        published = publish(world, (ALPHA,), bindings)

        members = carrier_bytes(world, published.packaging_identity)
        assert epoch.EPOCH_DOMAIN == "science.epoch.v1"
        assert published.packaging_identity == formula_packaging_identity(members)
        assert epoch.packaging_identity_of(members) == published.packaging_identity
        # And the directory in which those exact members were created is the
        # one the identity names.
        assert (world.config.world_root / "epochs" / published.packaging_identity).is_dir()

    def test_the_retraction_and_certification_subjects_live_only_inside_receipts(self, tmp_path):
        """§7.5 puts the retraction enumeration projection and the
        certification inventory *inside* their receipts. Neither is a twelfth
        epoch member, and neither leaks into any other member."""
        world, _recorder, bindings, _roots = admitted_world(tmp_path)

        published = publish(world, (ALPHA,), bindings)

        members = carrier_bytes(world, published.packaging_identity)
        carrying = {
            member: sorted(key for key in yaml.safe_load(content) if key in {"enumeration", "inventory"})
            for member, content in members.items()
        }
        assert {member: keys for member, keys in carrying.items() if keys} == {
            "retraction-receipt.yaml": ["enumeration"],
            "certification-receipt.yaml": ["inventory"],
        }
        assert "retraction-enumeration.yaml" not in members
        assert "certification-inventory.yaml" not in members

        draft = epoch._capture_build_inputs(world, coverage=frozenset({ALPHA}), bindings=bindings.by_kind())
        enumeration = derive.retraction_enumeration(draft.run("retraction-enumeration"))
        inventory = derive.certification_inventory(draft.run("certification-enumeration"))
        assert document(world, published.packaging_identity, "retraction-receipt.yaml")[
            "enumeration"
        ] == derive.retraction_enumeration_projection(enumeration)
        assert (
            document(world, published.packaging_identity, "certification-receipt.yaml")["inventory"]
            == inventory.projection()
        )

    def test_the_four_receipts_carry_one_identical_state_declaration(self, tmp_path):
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))

        published = publish(world, (ALPHA, BETA), bindings)

        declared = {
            member: document(world, published.packaging_identity, member)["corpus_states"]
            for member in epoch.RECEIPT_KINDS
        }
        assert len({repr(value) for value in declared.values()}) == 1
        assert declared["producer-receipt.yaml"] == [
            {"corpus_id": corpus_id, "corpus_state": state} for corpus_id, state in published.coverage
        ]
        assert {
            member: document(world, published.packaging_identity, member)["kind"]
            for member in epoch.RECEIPT_KINDS
        } == dict(epoch.RECEIPT_KINDS)

    def test_an_empty_declared_coverage_is_not_publishable(self, tmp_path):
        """The decision this task owed: an epoch over no corpus is refused.

        Nothing in §5 or §6 makes an empty capture *unrepresentable*, so the
        refusal is a choice and is written as one. An epoch declaring no
        coverage answers `Unknown` for every address (§8.3) and
        `indeterminate` for every edge in any world holding a live corpus
        (§8.4), so publishing one — and above all pointing `current` at one —
        would silently disable every read the epoch exists to serve. A caller
        that reached here with an empty set filtered its coverage down to
        nothing and wants to know.
        """
        world, recorder, bindings, _roots = admitted_world(tmp_path)

        with pytest.raises(ValueError, match="at least one"):
            publish(world, (), bindings)

        assert recorder.epoch_plans == []
        assert not (world.config.world_root / "epochs").exists()


# --- Step 2: publication is one transaction -----------------------------------


class TestPublicationIsOneTransaction:
    def test_first_publication_is_one_plan_of_eleven_creates_the_pointer_and_the_records(self, tmp_path):
        # Slice 3 (log-verification design §3.3) adds the build's registry-record
        # half to this very plan: one log-head record per covered corpus, created
        # after the pointer. The count is stated as `members + pointer + coverage`
        # so a build that quietly stopped writing them would fail here.
        world, recorder, bindings, _roots = admitted_world(tmp_path)

        published = publish(world, (ALPHA,), bindings)

        assert len(recorder.epoch_plans) == 1
        plan = recorder.epoch_plans[0]
        assert all(type(operation) is CreateOp for operation in plan)
        creates = [operation for operation in plan if isinstance(operation, CreateOp)]
        assert len(creates) == len(plan)
        records = [operation for operation in creates if operation.path.startswith("registry/")]
        assert len(records) == 1
        assert [operation.path for operation in creates] == [
            *(f"epochs/{published.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS),
            f"epochs/{epoch.CURRENT_POINTER}",
            *(operation.path for operation in records),
        ]
        assert creates[len(epoch.EPOCH_MEMBERS)].content == f"{published.packaging_identity}\n".encode()
        assert [operation.content for operation in creates[: len(epoch.EPOCH_MEMBERS)]] == [
            published.members[member] for member in epoch.EPOCH_MEMBERS
        ]

    def test_later_publication_creates_members_and_replaces_the_pointer(self, tmp_path):
        world, recorder, bindings, roots = admitted_world(tmp_path, (ALPHA, BETA))
        first = publish(world, (ALPHA,), bindings)

        second = publish(world, (ALPHA, BETA), bindings)

        assert second.packaging_identity != first.packaging_identity
        assert len(recorder.epoch_plans) == 2
        plan = recorder.epoch_plans[1]
        # Eleven members, the pointer replacement, and the two build-origin
        # records: BETA's is new, and ALPHA's differs from the first build's
        # only in the packaging identity its origin names.
        assert [type(operation) for operation in plan] == [CreateOp] * 11 + [ReplaceOp] + [CreateOp] * 2
        assert [operation.path for operation in plan[:11]] == [
            f"epochs/{second.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS
        ]
        assert all(operation.path.startswith("registry/") for operation in plan[12:])
        pointer = plan[11]
        assert isinstance(pointer, ReplaceOp), pointer
        assert pointer.path == f"epochs/{epoch.CURRENT_POINTER}"
        assert pointer.content == f"{second.packaging_identity}\n".encode()
        assert pointer.expected_digest == sha256(f"{first.packaging_identity}\n".encode()).hexdigest()
        # The first epoch is retained untouched beside the second.
        assert set(carrier_bytes(world, first.packaging_identity)) == set(epoch.EPOCH_MEMBERS)
        assert roots  # the two corpora both still stand

    def test_a_corpus_may_move_between_capture_and_publication(self, monkeypatch, tmp_path):
        """§5.4's staleness contract. Receipts name the exact captured states,
        and publication makes no freshness claim, so a corpus that moves after
        its hold is released is not a reason to refuse."""
        world, _recorder, bindings, roots = admitted_world(tmp_path)
        captured_state = registry.corpus_state_identity(roots[ALPHA])
        capture = epoch._capture_build_inputs

        def capture_then_move(world_, **keywords):
            draft = capture(world_, **keywords)
            from nodes.core.corpus import Corpus

            Corpus(roots[ALPHA]).add(stored.dataset_node("later", title="later"))
            return draft

        monkeypatch.setattr(epoch, "_capture_build_inputs", capture_then_move)

        published = publish(world, (ALPHA,), bindings)

        assert registry.corpus_state_identity(roots[ALPHA]) != captured_state
        assert published.coverage == ((ALPHA, captured_state),)
        assert document(world, published.packaging_identity, "producer-receipt.yaml")["corpus_states"] == [
            {"corpus_id": ALPHA, "corpus_state": captured_state}
        ]


# --- Step 3: exact rebuild, and the same-name carrier -------------------------


class TestExactRebuild:
    def test_exact_epoch_rebuild_swaps_only_current(self, tmp_path):
        """X1's pointer half. The content-addressed epoch already exists and is
        byte-identical, so the rebuild has nothing to create: the whole
        transaction is the pointer swap, and no member is rewritten."""
        world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        first = publish(world, (ALPHA,), bindings)
        publish(world, (ALPHA, BETA), bindings)
        before = epochs_tree(world)

        rebuilt = publish(world, (ALPHA,), bindings)

        assert rebuilt.packaging_identity == first.packaging_identity
        assert len(recorder.epoch_plans) == 3
        plan = recorder.epoch_plans[2]
        assert [type(operation) for operation in plan] == [ReplaceOp]
        rewrite = plan[0]
        assert isinstance(rewrite, ReplaceOp), rewrite
        assert rewrite.path == f"epochs/{epoch.CURRENT_POINTER}"
        assert rewrite.content == f"{first.packaging_identity}\n".encode()
        assert epochs_tree(world) == {
            **before,
            epoch.CURRENT_POINTER: f"{first.packaging_identity}\n".encode(),
        }

    def test_a_pointer_already_naming_the_epoch_submits_nothing(self, tmp_path):
        world, recorder, bindings, _roots = admitted_world(tmp_path)
        first = publish(world, (ALPHA,), bindings)
        before = epochs_tree(world)

        rebuilt = publish(world, (ALPHA,), bindings)

        assert rebuilt.packaging_identity == first.packaging_identity
        assert len(recorder.epoch_plans) == 1
        assert epochs_tree(world) == before
        assert rebuilt.members == first.members

    def test_publication_takes_the_world_lock_once_and_rechecks_inside_it(self, monkeypatch, tmp_path):
        """§5.4's ordering, counted rather than inferred.

        Two acquisitions in the whole build and no more: preflight takes the
        world lock and releases it before any corpus is captured, and
        publication takes it once and holds it across the recheck, the
        same-name inspection, the transaction and the read-back. The count is
        the assertion that matters. `remove_rule_binding` computes its sever
        report and submits its delete plan under one hold of this same lock, so
        a publication that released and reacquired between the recheck and the
        commit could be straddled entirely by one removal — and unlike a
        re-entrant call, which would deadlock loudly, that edit would leave
        every other arm here green.
        """
        world, recorder, bindings, _roots = admitted_world(tmp_path)
        counting = CountingLock()
        # A duck-typed stand-in for the state's `threading.Lock`; the arm counts
        # acquisitions, which the real lock does not expose.
        world._state.lock = counting  # pyright: ignore[reportAttributeAccessIssue]
        marks: list[tuple[str, int, bool]] = []

        def mark(stage: str) -> None:
            marks.append((stage, counting.acquisitions, counting.locked()))

        recheck = epoch._locked_recheck_rule_bindings
        planner = epoch._locked_publication_plan
        loader = epoch._locked_open_epoch
        monkeypatch.setattr(
            epoch,
            "_locked_recheck_rule_bindings",
            lambda world_root, draft: (mark("recheck"), recheck(world_root, draft))[1],
        )
        monkeypatch.setattr(
            epoch,
            "_locked_publication_plan",
            lambda world_root, identity, members: (
                mark("plan"),
                planner(world_root, identity, members),
            )[1],
        )
        monkeypatch.setattr(
            epoch,
            "_locked_open_epoch",
            lambda world_root, identity: (mark("open"), loader(world_root, identity))[1],
        )
        recorder.interpose = lambda root, plan: (mark("execute"), DefaultExecutor(root).execute(plan))[1]

        published = publish(world, (ALPHA,), bindings)

        assert counting.acquisitions == 2, "the build took the world lock more than preflight and publication"
        assert [stage for stage, _count, _locked in marks] == ["recheck", "plan", "execute", "open"]
        assert {(count, locked) for _stage, count, locked in marks} == {(2, True)}
        assert not counting.locked()
        assert published.packaging_identity in {path.name for path in (world.config.world_root / "epochs").iterdir()}

    @pytest.mark.parametrize("damage", ["incomplete", "malformed", "extra-member", "byte-different"])
    def test_a_differing_same_name_carrier_refuses_without_overwriting(self, tmp_path, damage):
        world, recorder, bindings, _roots = admitted_world(tmp_path)
        first = publish(world, (ALPHA,), bindings)
        directory = world.config.world_root / "epochs" / first.packaging_identity
        if damage == "incomplete":
            (directory / "coverage.yaml").unlink()
        elif damage == "malformed":
            (directory / "anchors.yaml").write_bytes(b"corpora: [\nworld: ]\n")
        elif damage == "extra-member":
            (directory / "notes.yaml").write_bytes(b"note: extra\n")
        else:
            (directory / "producers-map.yaml").write_bytes(b"producers: []\n")
        before = epochs_tree(world)
        submitted = len(recorder.epoch_plans)

        with pytest.raises(EpochMalformed):
            publish(world, (ALPHA,), bindings)

        assert epochs_tree(world) == before, "a refused rebuild rewrote a member"
        assert len(recorder.epoch_plans) == submitted, "a refused rebuild submitted a plan"


# --- Step 5: opening, under the one lock --------------------------------------


class TestOpening:
    def test_retained_epochs_open_by_packaging_identity(self, tmp_path):
        """X1. Publication retains; it does not supersede.

        The second epoch moves `current` and leaves the first exactly where it
        was, and the first opens by name afterwards. That is what makes an
        explicit packaging identity — never the word `current` — usable as the
        way a caller names the publication it means.
        """
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        first = publish(world, (ALPHA,), bindings)
        second = publish(world, (ALPHA, BETA), bindings)

        opened_first = read.open_epoch(world, first.packaging_identity)
        opened_second = read.open_epoch(world, second.packaging_identity)

        assert opened_first.packaging_identity == first.packaging_identity
        assert dict(opened_first.members) == dict(first.members)
        assert opened_second.packaging_identity == second.packaging_identity
        assert read.current_epoch(world).packaging_identity == second.packaging_identity
        assert [entry.subject for entry in opened_first.anchors] == [ALPHA]
        assert [entry.subject for entry in opened_second.anchors] == [ALPHA, BETA]
        assert opened_first.world_anchor.subject == world.config.world_id

    @pytest.mark.parametrize("member", epoch.EPOCH_MEMBERS)
    def test_open_epoch_refuses_raw_member_edit(self, tmp_path, member):
        """X1. The edit below changes no value the document parses to — it
        appends a YAML comment — and the epoch still refuses.

        That is the point of a packaging identity over *member bytes*: a
        carrier's name is a claim about the bytes, so an edit nobody's parser
        would notice still makes the directory misnamed. A digest over parsed
        values would let exactly this edit through.
        """
        world, _recorder, bindings, _roots = admitted_world(tmp_path)
        published = publish(world, (ALPHA,), bindings)
        path = world.config.world_root / "epochs" / published.packaging_identity / member
        before = yaml.safe_load(path.read_text(encoding="utf-8"))
        path.write_bytes(path.read_bytes() + b"# an edit no parser notices\n")
        assert yaml.safe_load(path.read_text(encoding="utf-8")) == before

        with pytest.raises(EpochMalformed) as refusal:
            read.open_epoch(world, published.packaging_identity)

        assert published.packaging_identity in str(refusal.value)
        with pytest.raises(EpochMalformed):
            read.current_epoch(world)

    @pytest.mark.parametrize(
        ("coverage", "fault"),
        [
            (
                [{"corpus_id": BETA, "corpus_state": ""}, {"corpus_id": ALPHA, "corpus_state": "x"}],
                "not sorted",
            ),
            (
                [{"corpus_id": ALPHA, "corpus_state": ""}, {"corpus_id": ALPHA, "corpus_state": "x"}],
                "covered twice",
            ),
        ],
    )
    def test_an_unstamped_coverage_entry_does_not_escape_the_declaration_checks(
        self, tmp_path, coverage, fault
    ):
        """The bound stamp's source is checked entry by entry, not entry by
        entry *that happens to carry a state*.

        Both carriers below are impeccable everywhere else — eleven members,
        closed documents, a directory name their own bytes recompute — and both
        declare a coverage that is unsorted or repeats a `corpus_id`, with the
        offending entry carrying an empty `corpus_state`. An empty string is
        text, so it passes validation; it is also falsy, so a check written as
        a comprehension *filter* would drop that entry before sortedness and
        distinctness were decided and hand §8.3 a stamp nobody vouched for.
        """
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        published = publish(world, (ALPHA, BETA), bindings)
        members = dict(carrier_bytes(world, published.packaging_identity))
        members["coverage.yaml"] = yaml.safe_dump(
            {"coverage": coverage}, sort_keys=True, allow_unicode=True
        ).encode("utf-8")
        forged = formula_packaging_identity(members)
        directory = world.config.world_root / "epochs" / forged
        directory.mkdir()
        for name, content in members.items():
            (directory / name).write_bytes(content)

        with pytest.raises(EpochMalformed) as refusal:
            read.open_epoch(world, forged)

        assert fault in str(refusal.value)
        assert "coverage.yaml" in str(refusal.value)

    def test_public_surface_has_no_individual_epoch_member_mutation(self, tmp_path):
        """An epoch is written whole and read whole. There is no act that
        touches one member of one epoch, and the absence is asserted at two
        levels: no public callable takes a member as its subject, and no
        transaction this package can submit ever rewrites or removes a member
        of a carrier that already stands.
        """
        import beliefs.world as facade

        world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        first = publish(world, (ALPHA,), bindings)
        second = publish(world, (ALPHA, BETA), bindings)
        rebuilt = publish(world, (ALPHA,), bindings)

        for name in facade.__all__:
            value = getattr(facade, name)
            if not callable(value):
                continue
            parameters = set(inspect.signature(value).parameters)
            assert not parameters & {"member", "member_name", "epoch_member"}, name
        # The read surface is pinned closed rather than sampled. Task 10 grew
        # it — receipt validation, the two bound queries and the answer types —
        # and what it must never gain is an act whose subject is one member of
        # one epoch, so the list is restated here every time it changes.
        assert sorted(read.__all__) == [
            "BoundStamp",
            "EDGE_STATES",
            "EdgeAnswer",
            "Location",
            "NotPresent",
            "Resolved",
            "Unknown",
            "coreference_edge",
            "current_epoch",
            "expand_coreference",
            "open_epoch",
            "resolve_address",
            "validate_receipt",
        ]
        assert [
            name
            for name in vars(epoch.Epoch)
            if name.startswith(("set", "add", "write", "replace", "delete", "update"))
        ] == []

        members = {f"epochs/{one.packaging_identity}/{member}" for one in (first, second) for member in epoch.EPOCH_MEMBERS}
        for plan in recorder.epoch_plans:
            for operation in plan:
                if operation.path == f"epochs/{epoch.CURRENT_POINTER}":
                    continue
                assert type(operation) is CreateOp, operation
                # The build's log-head records ride in the same plan (§3.3) and
                # are creates into `registry/`, never touches of a member.
                if operation.path.startswith("registry/"):
                    continue
                assert operation.path in members, operation.path
        assert rebuilt.packaging_identity == first.packaging_identity

        opened = read.open_epoch(world, first.packaging_identity)
        # Four deliberate static-contract violations, each exercising the runtime
        # refusal that an opened epoch is immutable through and through.
        with pytest.raises(FrozenInstanceError):
            opened.packaging_identity = "x" * 64  # pyright: ignore[reportAttributeAccessIssue]
        with pytest.raises(TypeError):
            opened.members["anchors.yaml"] = b""  # pyright: ignore[reportIndexIssue]
        with pytest.raises(TypeError):
            opened.documents["coverage.yaml"]["coverage"] = ()  # pyright: ignore[reportIndexIssue]
        with pytest.raises(TypeError):
            opened.receipts["producer-receipt.yaml"] = None  # pyright: ignore[reportIndexIssue]

    def test_a_contract_violating_receipt_still_opens(self, tmp_path):
        """§8.2's reachability requirement, and the one arm that proves it.

        The carrier here is impeccable — eleven members, closed documents, a
        name its bytes recompute — and one receipt inside it violates §7.5 in
        three ways at once: its discriminant disagrees with the member holding
        it, it carries a key outside `RECEIPT_KEYS`, and its corpus states are
        unsorted. Opening hands all of that on intact. A carrier layer that
        refused it would make outcome `malformed` unreachable, and with it the
        coreference consequence §8.2 exists to keep open.
        """
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        published = publish(world, (ALPHA, BETA), bindings)
        members = dict(carrier_bytes(world, published.packaging_identity))
        sound = yaml.safe_load(members["coreference-receipt.yaml"].decode("utf-8"))
        members["coreference-receipt.yaml"] = yaml.safe_dump(
            {
                **sound,
                "kind": "producer",
                "corpus_states": list(reversed(sound["corpus_states"])),
                "note": "a key no receipt kind declares",
            },
            sort_keys=True,
            allow_unicode=True,
        ).encode("utf-8")
        forged = formula_packaging_identity(members)
        directory = world.config.world_root / "epochs" / forged
        directory.mkdir()
        for name, content in members.items():
            (directory / name).write_bytes(content)

        opened = read.open_epoch(world, forged)

        carrier = opened.receipts["coreference-receipt.yaml"]
        assert carrier.kind == "producer" != epoch.RECEIPT_KINDS["coreference-receipt.yaml"]
        assert carrier.missing == ()
        assert set(opened.documents["coreference-receipt.yaml"]) != epoch.RECEIPT_KEYS["coreference-receipt.yaml"]
        assert opened.documents["coreference-receipt.yaml"]["note"] == "a key no receipt kind declares"
        assert carrier.corpus_states is not None
        assert list(carrier.corpus_states) == sorted(carrier.corpus_states, reverse=True)

    def test_an_absent_epoch_is_unknown_and_a_damaged_one_is_malformed(self, tmp_path):
        world, _recorder, bindings, _roots = admitted_world(tmp_path)
        published = publish(world, (ALPHA,), bindings)
        epochs = world.config.world_root / "epochs"

        with pytest.raises(EpochUnknown):
            read.open_epoch(world, "0" * 64)
        with pytest.raises(EpochUnknown):
            read.open_epoch(world, "not-a-packaging-identity")
        (epochs / published.packaging_identity / "coverage.yaml").unlink()
        with pytest.raises(EpochMalformed):
            read.open_epoch(world, published.packaging_identity)

    def test_a_world_with_no_pointer_has_no_current_epoch(self, tmp_path):
        world, _recorder, _bindings, _roots = admitted_world(tmp_path)

        with pytest.raises(EpochUnknown):
            read.current_epoch(world)

    @pytest.mark.parametrize(
        ("content", "refusal"),
        [
            (b"", EpochMalformed),
            (b"a" * 64, EpochMalformed),
            (b"epoch: " + b"a" * 64 + b"\n", EpochMalformed),
            (b"a" * 64 + b"\nb" * 64 + b"\n", EpochMalformed),
            (b"0" * 64 + b"\n", EpochUnknown),
        ],
    )
    def test_the_pointer_is_one_line_naming_one_retained_epoch(self, tmp_path, content, refusal):
        world, _recorder, bindings, _roots = admitted_world(tmp_path)
        publish(world, (ALPHA,), bindings)
        (world.config.world_root / "epochs" / epoch.CURRENT_POINTER).write_bytes(content)

        with pytest.raises(refusal):
            read.current_epoch(world)


class TestTheLockedOpen:
    def test_open_epoch_locks_before_the_barrier_and_holds_it_through_every_read(
        self, monkeypatch, tmp_path
    ):
        heads = ChainHeads()
        world, _recorder, bindings, _roots = admitted_world(tmp_path, chain_head=heads)
        published = publish(world, (ALPHA,), bindings)
        order: list[tuple[str, bool]] = []
        heads.observe = lambda _target: order.append(("barrier", world._state.lock.locked()))
        members = epoch._carrier_members
        parse = epoch._parse_member
        receipt = epoch._parse_receipt
        monkeypatch.setattr(
            epoch,
            "_carrier_members",
            lambda directory: (order.append(("carrier", world._state.lock.locked())), members(directory))[1],
        )
        monkeypatch.setattr(
            epoch,
            "_parse_member",
            lambda identity, member, content: (
                order.append(("parse", world._state.lock.locked())),
                parse(identity, member, content),
            )[1],
        )
        monkeypatch.setattr(
            epoch,
            "_parse_receipt",
            lambda identity, member, content: (
                order.append(("receipt", world._state.lock.locked())),
                receipt(identity, member, content),
            )[1],
        )

        read.open_epoch(world, published.packaging_identity)

        assert order[0] == ("barrier", True), "the barrier ran before the lock was taken"
        assert [stage for stage, _locked in order] == ["barrier", "carrier"] + ["parse"] * 5 + [
            "receipt"
        ] * 4 + ["parse"] * 2
        assert {locked for _stage, locked in order} == {True}
        assert not world._state.lock.locked()
        assert heads.roots[-1] == world.config.world_root

    def test_current_epoch_makes_one_acquisition_and_recovers_before_the_pointer(
        self, monkeypatch, tmp_path
    ):
        """§8.1's `current_epoch`: one lock, the barrier, the pointer, then the
        *same* private locked loader `open_epoch` uses. A second acquisition
        would deadlock on the non-reentrant lock, so counting is what turns
        "it did not hang" into "it took the lock exactly once"."""
        heads = ChainHeads()
        world, _recorder, bindings, _roots = admitted_world(tmp_path, chain_head=heads)
        published = publish(world, (ALPHA,), bindings)
        counting = CountingLock()
        # Same duck-typed stand-in: this arm counts that `open_epoch` acquires once.
        world._state.lock = counting  # pyright: ignore[reportAttributeAccessIssue]
        order: list[str] = []
        heads.observe = lambda _target: order.append("barrier")
        pointer = epoch._locked_current_identity
        loader = epoch._locked_open_epoch
        monkeypatch.setattr(
            epoch,
            "_locked_current_identity",
            lambda world_root: (order.append("pointer"), pointer(world_root))[1],
        )
        monkeypatch.setattr(
            epoch,
            "_locked_open_epoch",
            lambda world_root, identity: (order.append("loader"), loader(world_root, identity))[1],
        )

        opened = read.current_epoch(world)

        assert counting.acquisitions == 1
        assert order == ["barrier", "pointer", "loader"]
        assert opened.packaging_identity == published.packaging_identity
        assert not counting.locked()

    def test_no_reader_observes_a_publication_in_flight(self, monkeypatch, tmp_path):
        """The interleaving §8.1 exists for: a reader arriving while a
        publication transaction is half applied sees the finished epoch, never
        the applied prefix."""
        heads = ChainHeads()
        world, recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA), chain_head=heads)
        publish(world, (ALPHA,), bindings)
        halfway = threading.Event()
        arrived = threading.Event()
        release = threading.Event()

        def half_apply(root: Path, plan: list[WriteOp]) -> None:
            DefaultExecutor(root).execute(plan[:5])
            halfway.set()
            assert release.wait(JOIN_TIMEOUT), "the gated publication was never released"
            DefaultExecutor(root).execute(plan[5:])

        recorder.interpose = half_apply
        observed: list[tuple[str, tuple[str, ...]]] = []
        members = epoch._carrier_members
        monkeypatch.setattr(
            epoch,
            "_carrier_members",
            lambda directory: (
                observed.append(
                    (threading.current_thread().name, tuple(sorted(path.name for path in directory.iterdir())))
                ),
                members(directory),
            )[1],
        )
        outcome: list[object] = []

        def build() -> None:
            try:
                outcome.append(publish(world, (ALPHA, BETA), bindings))
            except BaseException as caught:  # noqa: BLE001 — the arm reports whatever the build did
                outcome.append(caught)

        def reader() -> None:
            arrived.set()
            try:
                outcome.append(read.current_epoch(world))
            except BaseException as caught:  # noqa: BLE001 — the arm reports whatever the reader saw
                outcome.append(caught)

        builder = threading.Thread(target=build, name="publisher")
        builder.start()
        try:
            assert halfway.wait(JOIN_TIMEOUT), "the publication never reached its transaction"
            directory = world.config.world_root / "epochs"
            partial = next(
                path for path in directory.iterdir() if path.is_dir() and len(list(path.iterdir())) == 5
            )
            consumer = threading.Thread(target=reader, name="reader")
            consumer.start()
            assert arrived.wait(JOIN_TIMEOUT), "the reader never started"
        finally:
            release.set()
            builder.join(JOIN_TIMEOUT)
            consumer.join(JOIN_TIMEOUT)

        assert not builder.is_alive() and not consumer.is_alive()
        assert [type(one) for one in outcome] == [epoch.Epoch, epoch.Epoch]
        opened_pair = [one for one in outcome if isinstance(one, epoch.Epoch)]
        assert {one.packaging_identity for one in opened_pair} == {partial.name}
        assert [names for name, names in observed if name == "reader"] == [tuple(sorted(epoch.EPOCH_MEMBERS))]

    def test_no_reader_observes_a_deletion_in_flight(self, tmp_path):
        """The same discipline from the other side. A whole-epoch removal
        holding the world lock is never observed half done: the reader waits,
        and then finds the epoch honestly gone rather than damaged."""
        world, _recorder, bindings, _roots = admitted_world(tmp_path, (ALPHA, BETA))
        first = publish(world, (ALPHA,), bindings)
        publish(world, (ALPHA, BETA), bindings)
        directory = world.config.world_root / "epochs" / first.packaging_identity
        halfway = threading.Event()
        arrived = threading.Event()
        release = threading.Event()
        outcome: list[object] = []

        def remove() -> None:
            with world._state.lock:
                for path in sorted(directory.iterdir())[:6]:
                    path.unlink()
                halfway.set()
                assert release.wait(JOIN_TIMEOUT), "the gated removal was never released"
                for path in sorted(directory.iterdir()):
                    path.unlink()
                directory.rmdir()

        def reader() -> None:
            arrived.set()
            try:
                outcome.append(read.open_epoch(world, first.packaging_identity))
            except BaseException as caught:  # noqa: BLE001 — the arm reports whatever the reader saw
                outcome.append(caught)

        remover = threading.Thread(target=remove, name="remover")
        remover.start()
        try:
            assert halfway.wait(JOIN_TIMEOUT), "the removal never began"
            assert len(list(directory.iterdir())) == 5
            consumer = threading.Thread(target=reader, name="reader")
            consumer.start()
            assert arrived.wait(JOIN_TIMEOUT), "the reader never started"
        finally:
            release.set()
            remover.join(JOIN_TIMEOUT)
            consumer.join(JOIN_TIMEOUT)

        assert not remover.is_alive() and not consumer.is_alive()
        assert isinstance(outcome[0], EpochUnknown), outcome[0]
