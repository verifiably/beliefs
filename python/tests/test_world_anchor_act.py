"""The anchor act, the exported head artifact, and the build's registry half.

Three writers of the same ruled record and one reader of the same chain head,
covered together because they share one resolution rule and one idempotency
discipline (log-verification design §3.1–§3.3).

**The seam is a stand-in and the locks are real.** Every arm builds a
`LogSeam` whose `read_head` answers from a table and whose two locks are the
production lookups — `registry._world_lock_for` and `corpus._operation_lock_for`
— so an arm that claims a lock was held claims it about the very object a
writer or an audit would contend for. Nothing here touches `atoms`: the act
cores see a chain only through the seam, which is what makes that substitution
possible at all.

**R12 is enforced by construction, not by inspection.** The world lock is not
reentrant, so an act core that called a `World` method under it would hang
rather than fail. The arms therefore hand the cores a world whose `registry()`
and `status()` refuse: a core reaching for either turns a deadlock into a
failure with a name.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, corpus_at
from test_world_epoch import Recorder, admitted_world, publish

from beliefs import root as science_root
from beliefs.corpus import _operation_lock_for
from beliefs.errors import (
    AnchorSubjectUnknown,
    AnchorTargetUnresolvable,
    BuildContended,
    BuildHold,
    LogEvidenceRefused,
    LogHeadCollision,
    WorldIdMismatch,
    WorldUninitialized,
)
from beliefs.identity import v1
from beliefs.world import anchors, epoch, logmodel, registry, verify

WORLD_ID = "f" * 32
OTHER_WORLD_ID = "e" * 32

GENESIS = {ALPHA: "a" * 64, BETA: "b" * 64}
TIP = {ALPHA: "1" * 64, BETA: "2" * 64}
WORLD_GENESIS = "d" * 64
WORLD_TIP = "9" * 64
MOVED_TIP = "7" * 64

CORPUS_GENESIS_PAYLOAD = v1.encode({"domain": "science.corpus-root.v1"})


def world_genesis_payload(world_id: str = WORLD_ID) -> bytes:
    """The payload `init_world_root` registers, from its own producer.

    Rebuilding the expression here would make the export arms agree with a
    second author's idea of the genesis: a key added or renamed at
    initialization would leave these arms passing against bytes no world root
    carries.
    """
    return science_root._world_genesis_payload(world_id)


# --- the harness -------------------------------------------------------------


class Heads:
    """The seam's `read_head`, answering from a table and recording its calls.

    A head is *set* per root rather than derived from one, because several arms
    turn on the act reading the carrier's chain and not the world's — a stub
    that answered every root alike could not tell those apart.
    """

    def __init__(self) -> None:
        self.heads: dict[Path, logmodel.ChainHead] = {}
        self.roots: list[Path] = []
        self.probe: Callable[[Path], None] | None = None

    def set(self, root: Path, genesis: str, tip: str, payload: bytes = CORPUS_GENESIS_PAYLOAD) -> None:
        self.heads[Path(root).resolve()] = logmodel.ChainHead(
            genesis_digest=genesis, genesis_payload=payload, tip=tip
        )

    def __call__(self, root: Path) -> logmodel.ChainHead:
        resolved = Path(root).resolve()
        self.roots.append(resolved)
        if self.probe is not None:
            self.probe(resolved)
        head = self.heads.get(resolved)
        assert head is not None, f"{resolved}: this arm set no head for that root"
        return head


def unreached_inspection(root: Path) -> logmodel.ChainView:
    raise AssertionError(f"{root}: these acts inspect no chain — they read a head")


def unreached_capture(root: Path, paths: tuple[str, ...]) -> tuple[tuple[str, object], ...]:
    raise AssertionError(f"{root}: these acts state no surface ({paths})")


def make_seam(heads: Heads) -> verify.LogSeam:
    """A seam over the production locks, with the head read stubbed.

    The two locks are deliberately *not* stubbed: an arm asserting that the act
    held a lock is asserting it about the object a corpus writer takes and an
    opened `World` takes, which a stand-in lock could not witness.
    """

    @contextmanager
    def world_lock(root: Path):
        with registry._world_lock_for(Path(root)):
            yield

    return verify.LogSeam(
        inspect_registered=unreached_inspection,
        inspect_detached=unreached_inspection,
        capture=unreached_capture,
        read_head=heads,
        absent_state=object(),
        world_lock=world_lock,
        corpus_lock=_operation_lock_for,
    )


def unread_chain(root: Path) -> tuple[str, str]:
    raise AssertionError(f"{root}: these acts read the chain through the seam, never through the world")


class RefusingWorld(registry.World):
    """A world whose two registry readers refuse. See the module docstring."""

    def registry(self) -> registry.RegistryView:
        raise AssertionError("an act core called World.registry() — R12 forbids it under the world lock")

    def status(self, corpus_id: str) -> registry.CorpusStatus:
        raise AssertionError("an act core called World.status() — R12 forbids it under the world lock")


def anchorable_world(
    tmp_path: Path,
    *corpus_ids: str,
    admitted: tuple[str, ...] | None = None,
    world_id: str = WORLD_ID,
) -> tuple[RefusingWorld, Recorder, Heads, dict[str, Path]]:
    """A world configured with one carrier per id, each with a head to read."""
    roots = {corpus_id: corpus_at(tmp_path / corpus_id[:6], corpus_id) for corpus_id in corpus_ids}
    recorder = Recorder()
    world_root = tmp_path / "world"
    world_root.mkdir(parents=True, exist_ok=True)
    world = RefusingWorld(
        registry.WorldConfig(world_root, world_id, tuple(roots.values())),
        recorder,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
    )
    for corpus_id in admitted if admitted is not None else corpus_ids:
        world.admit(roots[corpus_id], provenance=registry.Fresh(), actor="alice")
    heads = Heads()
    for corpus_id, root in roots.items():
        heads.set(root, GENESIS[corpus_id], TIP[corpus_id])
    heads.set(world_root, WORLD_GENESIS, WORLD_TIP, world_genesis_payload(world_id))
    return world, recorder, heads, roots


def anchor(world: registry.World, heads: Heads, *corpus_ids: str, actor: str = "alice"):
    return anchors._anchor_heads(world, frozenset(corpus_ids), actor=actor, seam=make_seam(heads))


def export(world: registry.World, heads: Heads, subject: anchors.CorpusSubject | anchors.WorldSubject) -> bytes:
    return anchors._export_head_artifact(world, subject, seam=make_seam(heads))


def registry_tree(world: registry.World) -> dict[str, bytes]:
    directory = world.config.world_root / "registry"
    if not directory.exists():
        return {}
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def stored_log_heads(world: registry.World) -> tuple[anchors.LogHeadRecord, ...]:
    """The records as the registry scan reads them back — never as the act
    returned them, so a record that could not be re-read would fail here."""
    return registry._scan_registry(world.config.world_root).log_heads


# --- the anchor act (§3.3) ----------------------------------------------------


class TestTheAnchorAct:
    def test_it_records_one_head_per_named_corpus(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, BETA)

        recorded = anchor(world, heads, BETA, ALPHA, actor="alice")

        assert recorded == (
            anchors.LogHeadRecord(
                anchors.CorpusSubject(ALPHA), GENESIS[ALPHA], TIP[ALPHA], anchors.AnchorActOrigin("alice")
            ),
            anchors.LogHeadRecord(
                anchors.CorpusSubject(BETA), GENESIS[BETA], TIP[BETA], anchors.AnchorActOrigin("alice")
            ),
        )
        assert stored_log_heads(world) == tuple(sorted(recorded, key=anchors.log_head_digest))

    def test_each_record_is_content_named_under_the_registry_grammar(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        (record,) = anchor(world, heads, ALPHA)

        name = f"{anchors.log_head_digest(record)}.yaml"
        assert set(registry_tree(world)) >= {name}
        document = yaml.safe_load(registry_tree(world)[name].decode("utf-8"))
        assert document == anchors.log_head_projection(record)
        assert document["record_kind"] == "log-head"

    def test_the_head_is_read_from_the_carrier_and_never_from_the_world_root(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)

        anchor(world, heads, ALPHA)

        assert heads.roots == [roots[ALPHA].resolve()]

    def test_an_unadmitted_corpus_id_refuses_as_an_unknown_subject(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, admitted=())

        with pytest.raises(AnchorSubjectUnknown):
            anchor(world, heads, ALPHA)

        assert stored_log_heads(world) == ()

    def test_a_corpus_with_no_configured_carrier_refuses_as_unresolvable(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        (roots[ALPHA] / "corpus.yaml").unlink()

        with pytest.raises(AnchorTargetUnresolvable):
            anchor(world, heads, ALPHA)

        assert stored_log_heads(world) == ()

    def test_two_configured_carriers_of_one_id_refuse_as_unresolvable(self, tmp_path):
        world, recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        second = corpus_at(tmp_path / "twin", ALPHA)
        heads.set(second, GENESIS[ALPHA], TIP[ALPHA])
        world.config = registry.WorldConfig(world.config.world_root, WORLD_ID, (roots[ALPHA], second))
        submitted = len(recorder.plans)

        with pytest.raises(AnchorTargetUnresolvable):
            anchor(world, heads, ALPHA)

        assert stored_log_heads(world) == ()
        assert len(recorder.plans) == submitted

    def test_an_unknown_subject_is_reported_before_an_unresolvable_carrier(self, tmp_path):
        # Both faults at once on one id: the subject refusal is decided first,
        # so an act that resolved carriers before reading the registry would
        # report the other one.
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA, admitted=())
        (roots[ALPHA] / "corpus.yaml").unlink()

        with pytest.raises(AnchorSubjectUnknown):
            anchor(world, heads, ALPHA)

    def test_a_refusal_writes_no_record_for_the_corpora_that_resolved(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, BETA, admitted=(ALPHA,))

        with pytest.raises(AnchorSubjectUnknown):
            anchor(world, heads, ALPHA, BETA)

        assert stored_log_heads(world) == ()

    def test_re_anchoring_an_unmoved_head_is_success_with_no_transaction(self, tmp_path):
        world, recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        first = anchor(world, heads, ALPHA)
        before = registry_tree(world)
        submitted = len(recorder.plans)

        again = anchor(world, heads, ALPHA)

        assert again == first
        assert registry_tree(world) == before
        assert len(recorder.plans) == submitted

    def test_a_same_name_record_holding_different_bytes_refuses_as_a_collision(self, tmp_path):
        # The reachable collision is a *hand-edited* record: a comment leaves
        # the document — and so the content name — unchanged while the bytes
        # move, which is precisely the case an overwrite would erase.
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        record = anchors.LogHeadRecord(
            anchors.CorpusSubject(ALPHA), GENESIS[ALPHA], TIP[ALPHA], anchors.AnchorActOrigin("alice")
        )
        edited = b"# anchored by hand\n" + anchors.log_head_record_bytes(record)
        squatter = world.config.world_root / "registry" / f"{anchors.log_head_digest(record)}.yaml"
        squatter.parent.mkdir(parents=True, exist_ok=True)
        squatter.write_bytes(edited)

        with pytest.raises(LogHeadCollision):
            anchor(world, heads, ALPHA)

        assert squatter.read_bytes() == edited

    def test_a_terminal_corpus_may_be_anchored(self, tmp_path):
        # §3.3 rules this in: anchoring immediately before retirement or
        # departure cleanup is the archetypal use of the act.
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, BETA)
        world.retire(ALPHA, actor="alice")
        world.depart(BETA, actor="alice")

        recorded = anchor(world, heads, ALPHA, BETA)

        assert [record.subject for record in recorded] == [
            anchors.CorpusSubject(ALPHA),
            anchors.CorpusSubject(BETA),
        ]
        assert len(stored_log_heads(world)) == 2

    def test_a_moved_head_is_a_second_record_beside_the_first(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        anchor(world, heads, ALPHA)
        heads.set(roots[ALPHA], GENESIS[ALPHA], MOVED_TIP)

        anchor(world, heads, ALPHA)

        assert sorted(record.head for record in stored_log_heads(world)) == sorted([TIP[ALPHA], MOVED_TIP])

    def test_it_holds_the_world_lock_across_the_head_read(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        observed: list[bool] = []
        held = registry._world_lock_for(world.config.world_root)
        heads.probe = lambda _root: observed.append(held.acquire(blocking=False))

        anchor(world, heads, ALPHA)

        assert observed == [False]
        assert held.acquire(blocking=False) is True
        held.release()

    def test_it_calls_no_world_method_under_the_world_lock(self, tmp_path):
        # R12: the seam's world lock is the very lock `registry()` takes, and
        # it is not reentrant. The double proves the act reads registry state
        # some other way rather than proving it merely did not deadlock here.
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        recorded = anchor(world, heads, ALPHA)

        assert len(recorded) == 1
        with pytest.raises(AssertionError):
            world.registry()

    def test_an_engine_refusal_from_the_head_read_propagates_untranslated(self, tmp_path):
        # R11: `read_head` translates the engine escapes, and the act core lets
        # the refusal past — it sits outside every precedence.
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        refusal = LogEvidenceRefused("inspect", "ChainStateInvalid", "the chain contradicts the store")
        heads.probe = lambda _root: (_ for _ in ()).throw(refusal)

        with pytest.raises(LogEvidenceRefused) as caught:
            anchor(world, heads, ALPHA)

        assert caught.value is refusal
        assert stored_log_heads(world) == ()

    def test_the_act_releases_the_world_lock_when_it_refuses(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, admitted=())

        with pytest.raises(AnchorSubjectUnknown):
            anchor(world, heads, ALPHA)

        held = registry._world_lock_for(world.config.world_root)
        assert held.acquire(blocking=False) is True
        held.release()

    def test_an_unencodable_actor_refuses_before_any_read(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        with pytest.raises(TypeError):
            anchor(world, heads, ALPHA, actor=object())  # type: ignore[arg-type]

        assert heads.roots == []


# --- the exported head artifact (§3.2) ----------------------------------------


class TestTheHeadExport:
    def test_a_corpus_artifact_decodes_to_the_head_the_seam_read(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)

        exported = export(world, heads, anchors.CorpusSubject(ALPHA))

        assert anchors.decode_head_artifact(exported) == anchors.HeadArtifact(
            anchors.CorpusSubject(ALPHA), GENESIS[ALPHA], TIP[ALPHA]
        )
        assert heads.roots == [roots[ALPHA].resolve()]

    def test_a_world_artifact_carries_the_world_id_and_the_world_chain_head(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        exported = export(world, heads, anchors.WorldSubject(WORLD_ID))

        assert anchors.decode_head_artifact(exported) == anchors.HeadArtifact(
            anchors.WorldSubject(WORLD_ID), WORLD_GENESIS, WORLD_TIP
        )
        assert heads.roots == [world.config.world_root.resolve()]

    def test_it_holds_the_world_lock_and_the_corpus_lock_across_the_tip_read(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        world_held = registry._world_lock_for(world.config.world_root)
        corpus_held = _operation_lock_for(roots[ALPHA])
        observed: list[tuple[bool, str | None]] = []

        def probe(_root: Path) -> None:
            with pytest.raises(BuildContended), corpus_held.capture():
                pass
            observed.append((world_held.acquire(blocking=False), corpus_held._holder))

        heads.probe = probe

        export(world, heads, anchors.CorpusSubject(ALPHA))

        assert observed == [(False, "writer")]
        assert world_held.acquire(blocking=False) is True
        world_held.release()
        assert corpus_held._holder is None

    def test_a_world_subject_takes_no_corpus_operation_lock(self, tmp_path):
        # The corpus lock is held as a build's capture throughout: an export
        # that reached for it would refuse rather than answer.
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        corpus_held = _operation_lock_for(roots[ALPHA])

        with corpus_held.capture():
            exported = export(world, heads, anchors.WorldSubject(WORLD_ID))

        assert anchors.decode_head_artifact(exported).subject == anchors.WorldSubject(WORLD_ID)

    def test_a_corpus_subject_refuses_while_a_build_holds_the_carriers_capture(self, tmp_path):
        # The mirror of the writer-mode hold: the export never waits across a
        # capture, because a tip read from the far side of one would describe a
        # corpus the capture had already finished reporting on.
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)

        with _operation_lock_for(roots[ALPHA]).capture(), pytest.raises(BuildHold):
            export(world, heads, anchors.CorpusSubject(ALPHA))

        assert heads.roots == []
        assert registry._world_lock_for(world.config.world_root).acquire(blocking=False) is True
        registry._world_lock_for(world.config.world_root).release()

    def test_a_world_subject_naming_another_world_refuses(self, tmp_path):
        # `World(W2)` over W1's chain: the subject binds, it never decorates.
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        with pytest.raises(WorldIdMismatch):
            export(world, heads, anchors.WorldSubject(OTHER_WORLD_ID))

        assert heads.roots == []

    def test_a_genesis_naming_another_world_refuses(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        heads.set(world.config.world_root, WORLD_GENESIS, WORLD_TIP, world_genesis_payload(OTHER_WORLD_ID))

        with pytest.raises(WorldIdMismatch):
            export(world, heads, anchors.WorldSubject(WORLD_ID))

    def test_a_genesis_that_is_not_a_world_root_genesis_refuses(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        heads.set(world.config.world_root, WORLD_GENESIS, WORLD_TIP, CORPUS_GENESIS_PAYLOAD)

        with pytest.raises(WorldUninitialized):
            export(world, heads, anchors.WorldSubject(WORLD_ID))

    def test_an_undecodable_genesis_payload_refuses(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        heads.set(world.config.world_root, WORLD_GENESIS, WORLD_TIP, b"\x00 not a payload")

        with pytest.raises(WorldUninitialized):
            export(world, heads, anchors.WorldSubject(WORLD_ID))

    def test_an_unadmitted_corpus_subject_refuses_as_an_unknown_subject(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA, admitted=())

        with pytest.raises(AnchorSubjectUnknown):
            export(world, heads, anchors.CorpusSubject(ALPHA))

    def test_a_corpus_subject_with_no_carrier_refuses_as_unresolvable(self, tmp_path):
        world, _recorder, heads, roots = anchorable_world(tmp_path, ALPHA)
        (roots[ALPHA] / "corpus.yaml").unlink()

        with pytest.raises(AnchorTargetUnresolvable):
            export(world, heads, anchors.CorpusSubject(ALPHA))

    def test_a_store_subject_is_not_exportable_by_this_slice(self, tmp_path):
        world, _recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)

        with pytest.raises(TypeError):
            export(world, heads, anchors.StoreSubject("5" * 32))  # type: ignore[arg-type]

    def test_the_export_writes_nothing(self, tmp_path):
        world, recorder, heads, _roots = anchorable_world(tmp_path, ALPHA)
        before = registry_tree(world)
        submitted = len(recorder.plans)

        export(world, heads, anchors.CorpusSubject(ALPHA))
        export(world, heads, anchors.WorldSubject(WORLD_ID))

        assert registry_tree(world) == before
        assert len(recorder.plans) == submitted


# --- the build's registry-record half (§3.3) ----------------------------------


class TestPublicationWritesBuildOriginRecords:
    def test_publication_leaves_one_build_origin_record_per_covered_corpus(self, tmp_path):
        world, _recorder, bindings, roots = admitted_world(tmp_path, (ALPHA, BETA))

        published = publish(world, (ALPHA, BETA), bindings)

        anchored = {entry.subject: entry for entry in published.anchors}
        assert stored_log_heads(world) == tuple(
            sorted(
                (
                    anchors.LogHeadRecord(
                        anchors.CorpusSubject(corpus_id),
                        anchored[corpus_id].genesis_digest,
                        anchored[corpus_id].head_digest,
                        anchors.BuildOrigin(published.packaging_identity),
                    )
                    for corpus_id in (ALPHA, BETA)
                ),
                key=anchors.log_head_digest,
            )
        )
        assert set(roots) == {ALPHA, BETA}

    def test_no_record_names_the_world_subject(self, tmp_path):
        # A `world` subject is not in the record's union at all (§3.1/L11):
        # only an export can anchor the world chain.
        world, _recorder, bindings, _roots = admitted_world(tmp_path)

        published = publish(world, (ALPHA,), bindings)

        assert published.world_anchor.subject == world.config.world_id
        assert [record.subject for record in stored_log_heads(world)] == [anchors.CorpusSubject(ALPHA)]

    def test_the_records_ride_in_the_publication_transaction(self, tmp_path):
        world, recorder, bindings, _roots = admitted_world(tmp_path)

        publish(world, (ALPHA,), bindings)

        (plan,) = recorder.epoch_plans
        paths = [operation.path for operation in plan]
        assert sum(path.startswith("registry/") for path in paths) == 1
        assert sum(path.startswith("epochs/") for path in paths) == len(epoch.EPOCH_MEMBERS) + 1

    def test_republishing_the_same_epoch_writes_no_second_record(self, tmp_path):
        world, _recorder, bindings, _roots = admitted_world(tmp_path)
        first = publish(world, (ALPHA,), bindings)
        before = registry_tree(world)

        again = publish(world, (ALPHA,), bindings)

        assert again.packaging_identity == first.packaging_identity
        assert registry_tree(world) == before

    def test_a_build_origin_record_and_an_anchor_act_record_stand_side_by_side(self, tmp_path):
        world, _recorder, bindings, roots = admitted_world(tmp_path)
        published = publish(world, (ALPHA,), bindings)
        heads = Heads()
        anchored = published.anchors[0]
        heads.set(roots[ALPHA], anchored.genesis_digest, anchored.head_digest)

        anchor(world, heads, ALPHA, actor="alice")

        origins = sorted(type(record.origin).__name__ for record in stored_log_heads(world))
        assert origins == ["AnchorActOrigin", "BuildOrigin"]


# --- the public wrappers ------------------------------------------------------


class TestThePublicWrappers:
    def test_the_wrappers_hand_the_cores_the_production_seam(self, tmp_path, monkeypatch):
        seen: list[object] = []
        monkeypatch.setattr(
            science_root,
            "_anchor_heads",
            lambda world, corpus_ids, *, store_roots, actor, seam: seen.append(
                ("anchor", world, corpus_ids, store_roots, actor, seam)
            )
            or (),
        )
        monkeypatch.setattr(
            science_root,
            "_export_head_artifact",
            lambda world, subject, *, store_root, seam: seen.append(
                ("export", world, subject, store_root, seam)
            )
            or b"",
        )
        world, _recorder, _heads, _roots = anchorable_world(tmp_path, ALPHA)

        science_root.anchor_heads(world, frozenset({ALPHA}), actor="alice")
        science_root.export_head_artifact(world, anchors.CorpusSubject(ALPHA))

        assert seen == [
            ("anchor", world, frozenset({ALPHA}), (), "alice", science_root._log_seam()),
            ("export", world, anchors.CorpusSubject(ALPHA), None, science_root._log_seam()),
        ]

    def test_the_wrapper_signatures_are_the_ruled_ones(self):
        anchor_parameters = inspect.signature(science_root.anchor_heads).parameters
        assert list(anchor_parameters) == ["world", "corpus_ids", "store_roots", "actor"]
        assert anchor_parameters["store_roots"].kind is inspect.Parameter.KEYWORD_ONLY
        assert anchor_parameters["store_roots"].default == ()
        assert anchor_parameters["actor"].kind is inspect.Parameter.KEYWORD_ONLY

        export_parameters = inspect.signature(science_root.export_head_artifact).parameters
        assert list(export_parameters) == ["world", "subject", "store_root"]
        assert export_parameters["store_root"].kind is inspect.Parameter.KEYWORD_ONLY
        assert export_parameters["store_root"].default is None
        # No `actor`: the ruled artifact has no member to record one, and the
        # function writes nothing.
        assert "actor" not in export_parameters

    def test_both_wrappers_are_exported_by_the_composition_root(self):
        assert {"anchor_heads", "export_head_artifact"} <= set(science_root.__all__)


# --- the codec seams these acts rest on ---------------------------------------


def test_the_world_genesis_domain_is_the_composition_roots_own():
    # The world export validates a genesis the composition root mints. The
    # constant is restated in `anchors` because the world package may not
    # import `beliefs.root`; this arm is what keeps the restatement honest.
    assert anchors.WORLD_GENESIS_DOMAIN == science_root.WORLD_GENESIS_DOMAIN


def test_the_record_bytes_are_the_registry_grammar(tmp_path):
    record = anchors.LogHeadRecord(
        anchors.CorpusSubject(ALPHA), GENESIS[ALPHA], TIP[ALPHA], anchors.AnchorActOrigin("alice")
    )

    content = anchors.log_head_record_bytes(record)

    assert content == yaml.safe_dump(
        anchors.log_head_projection(record), sort_keys=True, allow_unicode=True
    ).encode("utf-8")
    assert anchors.parse_log_head_record(yaml.safe_load(content.decode("utf-8"))) == record


def test_the_act_cores_take_the_seam_as_a_parameter():
    for core in (anchors._anchor_heads, anchors._export_head_artifact):
        parameters = inspect.signature(core).parameters
        assert parameters["seam"].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters["seam"].default is inspect.Parameter.empty


def test_the_act_cores_hold_no_engine_capability():
    # The bans themselves are `test_capability_boundary`'s, over every world
    # module. What is stated here, where the acts are covered, is the property
    # that makes them satisfiable: the seam is the whole of the engine an act
    # core can reach, so a stand-in seam is a complete substitution.
    parameters = set(inspect.signature(anchors._anchor_heads).parameters) | set(
        inspect.signature(anchors._export_head_artifact).parameters
    )
    assert parameters == {
        "world",
        "corpus_ids",
        "store_roots",
        "store_root",
        "actor",
        "seam",
        "subject",
    }


# --- cut 8's labeled declarations 7 and 8 -------------------------------------


def test_export_binds_subject_and_takes_no_actor(tmp_path):
    """D7. The export act's four clauses, together because they are one claim:
    the subject **binds**, it never decorates.

    `export_head_artifact` refuses a `World(world_id)` disagreeing with the
    configuration *or* with the genesis the chain was minted under; a corpus
    subject resolves under the exactly-one-carrier rule — zero carriers and two
    both refuse `AnchorTargetUnresolvable`; the function takes **no actor** and
    writes nothing, which is what makes it the one act that can anchor the
    world chain (§3.2, L11); and the bytes it returns decode under
    `science.head-artifact.v1`.
    """
    world, recorder, heads, _roots = anchorable_world(tmp_path / "bound", ALPHA)
    before, submitted = registry_tree(world), len(recorder.plans)

    # Neither act takes an actor: export mints no record, so there is nobody to
    # attribute — the anchor act beside it does take one, which is the contrast
    # that makes the absence a choice rather than an oversight.
    assert "actor" not in inspect.signature(anchors._export_head_artifact).parameters
    assert "actor" not in inspect.signature(science_root.export_head_artifact).parameters
    assert "actor" in inspect.signature(anchors._anchor_heads).parameters

    exported = export(world, heads, anchors.WorldSubject(WORLD_ID))
    assert json.loads(exported.decode("utf-8"))["domain"] == anchors.HEAD_ARTIFACT_DOMAIN
    assert exported == v1.encode(
        {
            "domain": anchors.HEAD_ARTIFACT_DOMAIN,
            "subject": {"kind": "world", "world_id": WORLD_ID},
            "genesis": WORLD_GENESIS,
            "head": WORLD_TIP,
        }
    )
    assert anchors.decode_head_artifact(exported) == anchors.HeadArtifact(
        anchors.WorldSubject(WORLD_ID), WORLD_GENESIS, WORLD_TIP
    )
    corpus_bytes = export(world, heads, anchors.CorpusSubject(ALPHA))
    assert anchors.decode_head_artifact(corpus_bytes) == anchors.HeadArtifact(
        anchors.CorpusSubject(ALPHA), GENESIS[ALPHA], TIP[ALPHA]
    )

    # Writes nothing: no record, no transaction.
    assert registry_tree(world) == before
    assert len(recorder.plans) == submitted

    # The subject binds against the configuration...
    with pytest.raises(WorldIdMismatch):
        export(world, heads, anchors.WorldSubject(OTHER_WORLD_ID))
    # ...and against the genesis the chain itself carries.
    heads.set(world.config.world_root, WORLD_GENESIS, WORLD_TIP, world_genesis_payload(OTHER_WORLD_ID))
    with pytest.raises(WorldIdMismatch):
        export(world, heads, anchors.WorldSubject(WORLD_ID))

    # The corpus arm's exactly-one-carrier rule, both ways it can fail.
    none_world, _recorder, none_heads, none_roots = anchorable_world(tmp_path / "none", ALPHA)
    (none_roots[ALPHA] / "corpus.yaml").unlink()
    with pytest.raises(AnchorTargetUnresolvable):
        export(none_world, none_heads, anchors.CorpusSubject(ALPHA))

    two_world, _recorder, two_heads, two_roots = anchorable_world(tmp_path / "two", ALPHA)
    twin = corpus_at(tmp_path / "twin", ALPHA)
    two_heads.set(twin, GENESIS[ALPHA], TIP[ALPHA])
    two_world.config = registry.WorldConfig(two_world.config.world_root, WORLD_ID, (two_roots[ALPHA], twin))
    with pytest.raises(AnchorTargetUnresolvable):
        export(two_world, two_heads, anchors.CorpusSubject(ALPHA))


def test_anchor_act_refusals_idempotency_and_terminal_corpora(tmp_path):
    """D8. The anchor act's refusal set and its idempotency discipline.

    `AnchorSubjectUnknown` for an id the registry does not carry;
    `AnchorTargetUnresolvable` for zero or multiple carriers; byte-identical
    re-anchoring is **success submitting no transaction**, while a same-name
    record holding different bytes is a **collision** rather than an overwrite;
    and a terminal corpus is anchorable — anchoring immediately before
    retirement or departure cleanup is the archetypal use of the act (§3.1,
    §3.3).
    """
    unknown, _recorder, unknown_heads, _unknown_roots = anchorable_world(
        tmp_path / "unknown", ALPHA, admitted=()
    )
    with pytest.raises(AnchorSubjectUnknown):
        anchor(unknown, unknown_heads, ALPHA)
    assert stored_log_heads(unknown) == ()

    none_world, _recorder, none_heads, none_roots = anchorable_world(tmp_path / "none", ALPHA)
    (none_roots[ALPHA] / "corpus.yaml").unlink()
    with pytest.raises(AnchorTargetUnresolvable):
        anchor(none_world, none_heads, ALPHA)

    two_world, two_recorder, two_heads, two_roots = anchorable_world(tmp_path / "two", ALPHA)
    twin = corpus_at(tmp_path / "twin", ALPHA)
    two_heads.set(twin, GENESIS[ALPHA], TIP[ALPHA])
    two_world.config = registry.WorldConfig(two_world.config.world_root, WORLD_ID, (two_roots[ALPHA], twin))
    submitted = len(two_recorder.plans)
    with pytest.raises(AnchorTargetUnresolvable):
        anchor(two_world, two_heads, ALPHA)
    assert stored_log_heads(two_world) == ()
    assert len(two_recorder.plans) == submitted

    # Idempotency: the same head twice is one record and one transaction.
    world, recorder, heads, _roots = anchorable_world(tmp_path / "idempotent", ALPHA)
    first = anchor(world, heads, ALPHA)
    tree_after_first = registry_tree(world)
    submitted = len(recorder.plans)
    assert anchor(world, heads, ALPHA) == first
    assert registry_tree(world) == tree_after_first
    assert len(recorder.plans) == submitted

    # ...and a same-name record holding *different* bytes is a collision, never
    # an overwrite: a hand-edited comment leaves the document, and so the
    # content name, unchanged while the bytes move.
    (record,) = first
    squatter = world.config.world_root / "registry" / f"{anchors.log_head_digest(record)}.yaml"
    edited = b"# anchored by hand\n" + anchors.log_head_record_bytes(record)
    squatter.write_bytes(edited)
    with pytest.raises(LogHeadCollision):
        anchor(world, heads, ALPHA)
    assert squatter.read_bytes() == edited

    # Terminal corpora are anchorable.
    terminal, _recorder, terminal_heads, _roots = anchorable_world(tmp_path / "terminal", ALPHA, BETA)
    terminal.retire(ALPHA, actor="alice")
    terminal.depart(BETA, actor="alice")
    recorded = anchor(terminal, terminal_heads, ALPHA, BETA)
    assert [entry.subject for entry in recorded] == [
        anchors.CorpusSubject(ALPHA),
        anchors.CorpusSubject(BETA),
    ]
    assert len(stored_log_heads(terminal)) == 2
