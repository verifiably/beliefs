"""The snapshot target arm (correction-remainder slice 2)."""
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from authority import ACTOR
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder
from test_world_build import ALPHA, BETA
from test_world_receipts import publish, published_world

from beliefs import stored
from beliefs.corpus import CorpusWriter, _validated_retraction_target
from beliefs.errors import MalformedRecord, RetractionTargetUnresolvable, ValidationRefused
from beliefs.world.epoch import RetainedSnapshots

S = "a" * 64
S2 = "b" * 64


def snapshot_retraction(identity: str = S, *, successor: str | None = None, token: str = "t1"):
    return stored.retraction_node(
        title=token,
        target=stored.SnapshotTarget("producer", identity),
        reason="authored-error",
        rationale="the snapshot's coverage was too wide",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
        successor=successor,
    )


class TestTheStoredShape:
    def test_the_facet_carries_the_arm_and_no_target_edge(self):
        node = snapshot_retraction(successor=S2)
        facet = node.facets[stored.RETRACTION_FACET]
        assert facet["target"] == {"arm": "snapshot", "subject_kind": "producer", "subject_identity": S}
        assert facet["successor"] == S2
        predicates = {r.predicate for r in node.relations}
        assert predicates == {stored.GROUNDED_IN}

    def test_the_identity_moves_with_the_subject_and_the_successor(self):
        assert snapshot_retraction().id != snapshot_retraction(S2).id
        assert snapshot_retraction().id != snapshot_retraction(successor=S2).id

    @pytest.mark.parametrize("kind", ["retraction-enumeration", "certification-enumeration", "coreference-reduction", ""])
    def test_only_the_producer_kind_constructs(self, kind):
        with pytest.raises(MalformedRecord):
            stored.retraction_node(
                title="t", target=stored.SnapshotTarget(kind, S), reason="authored-error", rationale="r",
                grounds=("verification:v1",), actor=ACTOR, event_token="t",
            )

    @pytest.mark.parametrize("identity", ["a" * 63, "A" * 64, "g" * 64, ""])
    def test_the_identity_is_sixty_four_lower_hex(self, identity):
        with pytest.raises(MalformedRecord):
            stored.retraction_node(
                title="t", target=stored.SnapshotTarget("producer", identity), reason="authored-error",
                rationale="r", grounds=("verification:v1",), actor=ACTOR, event_token="t",
            )

    def test_the_arm_set_is_named_once(self):
        assert stored.RETRACTION_TARGET_ARMS == ("node", "route", "snapshot")
        assert stored.SNAPSHOT_SUBJECT_KINDS == ("producer",)


class TestTheValidatedTarget:
    def test_the_arm_validates_and_the_controlled_shape_holds(self):
        node = snapshot_retraction()
        assert _validated_retraction_target(node)["arm"] == "snapshot"
        assert CorpusWriter._validated_retraction(node)["target"]["subject_identity"] == S

    def test_an_extra_or_missing_field_is_malformed(self):
        node = snapshot_retraction()
        node.facets[stored.RETRACTION_FACET]["target"]["ref"] = "x"
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)
        node = snapshot_retraction()
        del node.facets[stored.RETRACTION_FACET]["target"]["subject_kind"]
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)

    def test_a_retracts_edge_fails_the_controlled_shape(self):
        node = snapshot_retraction()
        node.relations.append(Relation(source=node.id, predicate=stored.RETRACTS, target=f"producer-snapshot:{S}"))
        stored.stamp_semantic_identity(node)
        with pytest.raises(MalformedRecord):
            CorpusWriter._validated_retraction(node)


def test_the_discovery_map_keys_the_arm_by_identity():
    from beliefs.world.epoch import _retraction_target

    assert _retraction_target(snapshot_retraction().facets[stored.RETRACTION_FACET]) == S


class StubResolver:
    def __init__(self, retained):
        self._retained = retained

    def retained(self, subject_kind):
        assert subject_kind == "producer"
        return MappingProxyType(dict(self._retained))


def writer_at(root: Path, profile=BASE, *, resolver=None) -> CorpusWriter:
    """A manifest-bearing writer (ReadView.corpus_id reads one); reopening
    the same root adopts nothing a second time (ManifestAlreadyPresent)."""
    from authority import FULL

    writer = CorpusWriter(
        root, DefaultExecutor, authority=FULL, profile=profile,
        operation_port=OperationRecorder(root, authority=FULL, profile=profile), snapshot_resolver=resolver,
    )
    if not (Path(root) / "corpus.yaml").exists():
        writer.adopt_manifest(profile=pins_for(profile))
    return writer


def broken_counter(target, token: str = "counter"):
    """A *canonical* counter-retraction whose target content identity is wrong:
    the controlled shape holds (the id is derived from this facet), so only
    target resolution can refuse it — the recipe slice 1's plan used."""
    return stored.retraction_node(
        title=token,
        target=stored.NodeTarget(target.id, target.id, "0" * 64),
        reason="defective-code",
        rationale="a counter-retraction naming the wrong content",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
    )


class TestTheWriteBoundary:
    def test_a_writer_without_the_port_refuses_the_arm(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        with pytest.raises(RetractionTargetUnresolvable, match="reaches none"):
            writer.retract(snapshot_retraction())

    def test_an_unretained_identity_refuses(self, tmp_path):
        writer = writer_at(tmp_path / "c", resolver=StubResolver({}))
        with pytest.raises(RetractionTargetUnresolvable, match="no retained epoch carries"):
            writer.retract(snapshot_retraction())

    def test_a_corpus_outside_the_coverage_refuses_naming_it(self, tmp_path):
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: ("0" * 32,)}))
        with pytest.raises(RetractionTargetUnresolvable, match=f"corpus {writer.corpus_id} is outside the coverage"):
            writer.retract(snapshot_retraction())

    def test_a_successor_must_be_retained_and_not_the_target(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        cid = writer.corpus_id
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,)}))
        with pytest.raises(RetractionTargetUnresolvable, match="successor"):
            writer.retract(snapshot_retraction(successor=S2))
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,), S2: (cid,)}))
        with pytest.raises(ValidationRefused, match="not its target"):
            writer.retract(snapshot_retraction(successor=S))

    def test_the_happy_path_writes_one_record(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        cid = writer.corpus_id
        writer = writer_at(tmp_path / "c", resolver=StubResolver({S: (cid,), S2: (cid,)}))
        before = len(list(writer.read_view.iter_stored()))
        minted = writer.retract(snapshot_retraction(successor=S2))
        assert minted.kind == "retraction"
        assert len(list(writer.read_view.iter_stored())) == before + 1

    def test_a_snapshot_kind_outside_the_closed_set_is_ineligible_everywhere(self, tmp_path):
        node = snapshot_retraction()
        node.facets[stored.RETRACTION_FACET]["target"]["subject_kind"] = "coreference-reduction"
        # shape validation refuses first; the eligibility refusal is reached through the static method
        with pytest.raises(MalformedRecord):
            _validated_retraction_target(node)


class TestRetainedSnapshots:
    def test_two_epochs_of_different_coverage_answer_with_their_coverage(self, tmp_path):
        world, bindings, _roots, wide = published_world(tmp_path, (ALPHA, BETA))
        narrow = publish(world, (ALPHA,), bindings)
        retained = RetainedSnapshots(world).retained("producer")
        wide_id = wide.receipts["producer-receipt.yaml"].subject_identity
        narrow_id = narrow.receipts["producer-receipt.yaml"].subject_identity
        assert wide_id is not None
        assert narrow_id is not None
        assert wide_id != narrow_id
        assert retained[wide_id] == tuple(sorted((ALPHA, BETA)))
        assert retained[narrow_id] == (ALPHA,)

    def test_a_world_with_no_epochs_answers_empty_and_an_unknown_kind_refuses(self, tmp_path):
        from test_world_receipts import sample_corpora, world_over

        world = world_over(tmp_path, sample_corpora(tmp_path, (ALPHA,)))
        assert dict(RetainedSnapshots(world).retained("producer")) == {}
        with pytest.raises(ValueError):
            RetainedSnapshots(world).retained("weather")
