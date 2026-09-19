"""The snapshot target arm (correction-remainder slice 2)."""
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from authority import ACTOR
from fixtures_cut4 import raw_write
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder
from test_local_standing import retracts
from test_world_build import ALPHA, BETA
from test_world_receipts import publish, published_world

from beliefs import stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.corpus import CorpusWriter, ReadView, _validated_retraction_target, snapshot_standing
from beliefs.errors import MalformedRecord, RetractionTargetUnresolvable, RetractionUnreadable, ValidationRefused
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


def corpus_with(tmp_path, *nodes, resolver):
    writer = writer_at(tmp_path, resolver=resolver)
    minted = [writer.retract(n) if n.kind == "retraction" else writer.add(n) for n in nodes]
    return writer, minted


class TestSnapshotStanding:
    def _resolver(self, writer_root):
        cid = writer_at(writer_root).corpus_id
        return StubResolver({S: (cid,), S2: (cid,)}), cid

    def test_no_retractions_is_empty(self, tmp_path):
        writer = writer_at(tmp_path / "c")
        standing = snapshot_standing({writer.corpus_id: writer.read_view})
        assert standing.retracted == frozenset() and dict(standing.history) == {}

    def test_one_standing_retraction_names_its_identity_with_history(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == {S}
        assert standing.history[S] == ((r.id, RETRACTION_UPHELD),)

    def test_a_counter_retraction_restores_and_the_history_carries_both(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        c = writer.retract(retracts(r, "counter"))
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == frozenset()
        assert standing.history[S] == tuple(sorted([(c.id, RETRACTION_UPHELD), (r.id, RETRACTION_OVERTURNED)]))
        cc = writer.retract(retracts(c, "counter-counter"))
        standing = snapshot_standing({cid: writer.read_view})
        assert standing.retracted == {S}
        assert len(standing.history[S]) == 3 and (cc.id, RETRACTION_UPHELD) in standing.history[S]

    def test_two_corpora_union(self, tmp_path):
        a = writer_at(tmp_path / "a"); b = writer_at(tmp_path / "b")
        ra = StubResolver({S: (a.corpus_id,)}); rb = StubResolver({S2: (b.corpus_id,)})
        a = writer_at(tmp_path / "a", resolver=ra); b = writer_at(tmp_path / "b", resolver=rb)
        a.retract(snapshot_retraction(S)); b.retract(snapshot_retraction(S2, token="t2"))
        standing = snapshot_standing({a.corpus_id: a.read_view, b.corpus_id: b.read_view})
        assert standing.retracted == {S, S2}

    def test_an_unreadable_facet_refuses(self, tmp_path):
        from test_local_standing import raw_retraction

        writer = writer_at(tmp_path / "c")
        raw = raw_retraction("retraction:raw", "assessment:x")
        del raw.facets[stored.RETRACTION_FACET]["grounds"]      # raw_retraction alone is shape-valid; this is not
        raw_write(tmp_path / "c", raw)
        with pytest.raises(RetractionUnreadable):
            snapshot_standing({writer.corpus_id: ReadView.opened_at(tmp_path / "c")})

    def test_a_broken_counter_retraction_refuses_rather_than_restores(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        _writer, (r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        broken = broken_counter(r)                       # canonical shape, wrong target identity
        raw_write(tmp_path / "c", broken)
        with pytest.raises(RetractionUnreadable) as caught:
            snapshot_standing({cid: ReadView.opened_at(tmp_path / "c")})
        assert caught.value.ref == broken.id

    def test_a_broken_retraction_outside_every_chain_raises_nothing(self, tmp_path):
        resolver, cid = self._resolver(tmp_path / "c")
        _writer, (_r,) = corpus_with(tmp_path / "c", snapshot_retraction(), resolver=resolver)
        unrelated = stored.retraction_node(
            title="elsewhere", target=stored.NodeTarget("assessment:nobody", "assessment:nobody", "0" * 64),
            reason="defective-code", rationale="names nothing", grounds=("verification:v1",), actor=ACTOR,
            event_token="elsewhere",
        )
        raw_write(tmp_path / "c", unrelated)
        standing = snapshot_standing({cid: ReadView.opened_at(tmp_path / "c")})
        assert standing.retracted == {S}
