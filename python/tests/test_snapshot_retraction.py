"""The snapshot target arm (correction-remainder slice 2)."""
from __future__ import annotations

import pytest
from authority import ACTOR
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import CorpusWriter, _validated_retraction_target
from beliefs.errors import MalformedRecord

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
