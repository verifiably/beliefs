"""Consolidation of `source-assertion` replicas across corpus roots."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from authority import ACTOR, FULL
from coordination_fixtures import content_for
from fixtures_cut4 import path_for, raw_write
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, biology, pins_for
from session_doors_fixture import PUBLISHES, V2, Clock
from test_corpus_write import OperationRecorder
from test_relocation import CONSOLIDATE_FIELDS, MOVE_FIELDS, _files, _recording_port, _writer
from test_reservation_relocation import _addresses, _corpus
from test_source_assertion_routes import (
    BUNDLE_FIELDS,
    IDENTIFIERS_A,
    IDENTIFIERS_B,
    _assertion,
    _proposition,
    _source,
    _with_assesses,
)
from test_world_receipts import hold_shipped

from beliefs import relocation, stored
from beliefs import root as science_root
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.errors import RelocationRefused, SourceAssertionRefused, SourceAssertionReplicasDisagree
from beliefs.intents.publish import Destination
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination
from beliefs.publication_arrival import admit_publication
from beliefs.publish import Published, publish
from beliefs.report import Consolidated, RecordMutationEntry
from beliefs.root import init_corpus_root, init_world_root, moment_seam, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig, epoch
from beliefs.world.logmodel import WellFormedView
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view


@pytest.fixture()
def source_writer(tmp_path):
    return _writer(tmp_path / "source", domains=PINS.domains)


@pytest.fixture()
def destination_writer(tmp_path):
    return _writer(tmp_path / "destination", domains=PINS.domains)


def _seed(writer: CorpusWriter, *, identifiers: dict[str, str] | None = None) -> tuple[Node, Node]:
    return writer.add(_source(identifiers)), writer.add(_proposition())


def _assert_nothing_written(
    keep_writer: CorpusWriter,
    other_writer: CorpusWriter,
    before_files: tuple[dict[str, bytes], dict[str, bytes]],
    before_intents: tuple[list[object], list[object]],
    assertion_id: str,
) -> None:
    assert (_files(keep_writer), _files(other_writer)) == before_files
    assert (list(_recording_port(keep_writer).intents), list(_recording_port(other_writer).intents)) == before_intents
    assert keep_writer.read_view.holds(assertion_id)
    assert other_writer.read_view.holds(assertion_id)


def test_equal_replicas_consolidate(source_writer, destination_writer):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    value = _assertion(src, prop)
    keep = source_writer.add(stored.source_assertion_node(value, title="kept", body="keep body"))
    other = destination_writer.add(stored.source_assertion_node(value, title="other", body="other body"))
    assert keep.uid != other.uid

    survivor, keep_report, other_report = relocation.consolidate(
        (source_writer, keep.id),
        (destination_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == value.id
    assert survivor.uid == keep.uid
    assert survivor.title == "kept"
    assert survivor.body == "keep body"
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, src.id)]
    restored = stored.source_assertion_value(source_writer.read_view.get(value.id))
    assert restored == value
    assert restored.recorded_by == ACTOR
    assert not destination_writer.read_view.holds(value.id)
    assert destination_writer.read_view.resolve(value.id) is None
    assert isinstance(keep_report.entries[0], RecordMutationEntry)
    expected_outcome = Consolidated(
        source_writer.corpus_id,
        keep.id,
        destination_writer.corpus_id,
        other.id,
        (other.uid,),
        CONSOLIDATE_FIELDS["rationale"],
    )
    assert keep_report.entries[0].outcome == expected_outcome
    assert other_report.entries[0].outcome == expected_outcome


def test_replicas_from_two_sessions_consolidate_keeping_the_survivor_writer(source_writer, destination_writer):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    session_b = "session:" + "b" * 32
    session_c = "session:" + "c" * 32
    keep_value = _assertion(src, prop, recorded_by=session_b)
    other_value = _assertion(src, prop, recorded_by=session_c)
    assert keep_value.id == other_value.id

    source_writer.import_bundle([stored.source_assertion_node(keep_value, title="session-b")], **BUNDLE_FIELDS)
    other_node = stored.source_assertion_node(other_value, title="session-c")
    raw_write(destination_writer.root, other_node)
    destination_writer._reconstruct()

    survivor, _, _ = relocation.consolidate(
        (source_writer, keep_value.id),
        (destination_writer, other_value.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep_value.id
    assert survivor.title == "session-b"
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, src.id)]
    restored = stored.source_assertion_value(source_writer.read_view.get(keep_value.id))
    assert restored == keep_value
    assert restored.recorded_by == session_b
    assert not destination_writer.read_view.holds(other_value.id)


def test_replicas_anchored_at_old_and_new_addresses_consolidate_to_one_edge(source_writer, destination_writer):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    corrected = source_writer.correct_identifier(src_a.id, IDENTIFIERS_B, grounds="canonical DOI")
    _seed(destination_writer, identifiers=IDENTIFIERS_A)

    keep_value = _assertion(corrected, prop)
    other_value = _assertion(src_a, prop)
    assert keep_value.id == other_value.id

    keep_node = source_writer.add(stored.source_assertion_node(keep_value, title="corrected"))
    other_node = destination_writer.add(stored.source_assertion_node(other_value, title="old"))
    assert [(r.predicate, r.target) for r in keep_node.relations] == [(stored.ANCHORED_IN, corrected.id)]
    assert [(r.predicate, r.target) for r in other_node.relations] == [(stored.ANCHORED_IN, src_a.id)]

    survivor, _, _ = relocation.consolidate(
        (source_writer, keep_node.id),
        (destination_writer, other_node.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep_value.id
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, corrected.id)]
    restored = stored.source_assertion_value(source_writer.read_view.get(keep_value.id))
    assert restored == keep_value
    assert not destination_writer.read_view.holds(other_node.id)


def test_replicas_anchored_at_old_and_new_addresses_consolidate_keeping_deprecated_edge(
    source_writer, destination_writer
):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    source_writer.correct_identifier(src_a.id, IDENTIFIERS_B, grounds="canonical DOI")
    other_src_b, _ = _seed(destination_writer, identifiers=IDENTIFIERS_B)

    keep_value = _assertion(src_a, prop)
    other_value = _assertion(other_src_b, prop)
    assert keep_value.id == other_value.id

    keep_node = source_writer.add(stored.source_assertion_node(keep_value, title="kept-old-edge"))
    other_node = destination_writer.add(stored.source_assertion_node(other_value, title="other-new-edge"))

    survivor, _, _ = relocation.consolidate(
        (source_writer, keep_node.id),
        (destination_writer, other_node.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep_value.id
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, src_a.id)]
    assert stored.source_assertion_value(source_writer.read_view.get(keep_value.id)) == keep_value
    assert not destination_writer.read_view.holds(other_node.id)


@pytest.mark.parametrize("position", ["keep", "other"])
def test_an_extra_assesses_edge_on_either_replica_refuses_before_anything_is_written(
    position, source_writer, destination_writer
):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    value = _assertion(src, prop)
    valid = stored.source_assertion_node(value, title="valid")
    with_assesses = _with_assesses(value, prop)

    if position == "keep":
        raw_write(source_writer.root, with_assesses)
        source_writer._reconstruct()
        destination_writer.add(valid)
    else:
        source_writer.add(valid)
        raw_write(destination_writer.root, with_assesses)
        destination_writer._reconstruct()

    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(SourceAssertionRefused) as caught:
        relocation.consolidate(
            (source_writer, value.id),
            (destination_writer, value.id),
            **CONSOLIDATE_FIELDS,
        )

    assert caught.value.code == "source-assertion-edge-mismatch"
    assert position in str(caught.value)
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, value.id)


@pytest.mark.parametrize("position", ["keep", "other"])
def test_a_malformed_replica_in_either_position_refuses(position, source_writer, destination_writer):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    value = _assertion(src, prop)
    valid = stored.source_assertion_node(value, title="valid")
    damaged = stored.source_assertion_node(value, title="damaged").model_copy(deep=True)
    del cast(dict[str, object], damaged.facets[stored.SOURCE_ASSERTION_FACET])["recorded_by"]
    damaged = stored.stamp_semantic_identity(damaged)

    if position == "keep":
        raw_write(source_writer.root, damaged)
        source_writer._reconstruct()
        destination_writer.add(valid)
    else:
        source_writer.add(valid)
        raw_write(destination_writer.root, damaged)
        destination_writer._reconstruct()

    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(SourceAssertionRefused) as caught:
        relocation.consolidate(
            (source_writer, value.id),
            (destination_writer, value.id),
            **CONSOLIDATE_FIELDS,
        )

    assert caught.value.code == "source-assertion-malformed"
    assert position in str(caught.value)
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, value.id)


def test_replicas_anchored_in_different_sources_are_refused(source_writer, destination_writer):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    src_b = source_writer.add(_source(IDENTIFIERS_B, title="s2"))
    _seed(destination_writer, identifiers=IDENTIFIERS_B)

    keep_value = _assertion(src_a, prop)
    other_value = _assertion(src_b, prop)
    assert keep_value.id == other_value.id

    source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
    destination_writer.add(stored.source_assertion_node(other_value, title="other"))
    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(SourceAssertionReplicasDisagree) as caught:
        relocation.consolidate(
            (source_writer, keep_value.id),
            (destination_writer, other_value.id),
            **CONSOLIDATE_FIELDS,
        )

    assert src_a.id in str(caught.value)
    assert src_b.id in str(caught.value)
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, keep_value.id)


@pytest.mark.parametrize("case", ["other-unresolved", "keep-unresolved", "both-unresolved"])
def test_a_replica_whose_source_does_not_resolve_is_refused(case, source_writer, destination_writer):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    other_src_b, _ = _seed(destination_writer, identifiers=IDENTIFIERS_B)

    if case == "other-unresolved":
        keep_value = _assertion(src_a, prop)
        other_value = _assertion(other_src_b, prop)
        source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
        destination_writer.add(stored.source_assertion_node(other_value, title="other"))
        expected_side, expected_target = "other", other_src_b.id
    elif case == "keep-unresolved":
        keep_src_b = source_writer.add(_source(IDENTIFIERS_B, title="s2"))
        destination_writer.add(_source(IDENTIFIERS_A, title="s1"))
        keep_value = _assertion(keep_src_b, prop)
        other_value = _assertion(src_a, prop)
        source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
        source_writer.delete(keep_src_b.id)
        destination_writer.add(stored.source_assertion_node(other_value, title="other"))
        expected_side, expected_target = "keep", keep_src_b.id
    else:
        destination_writer.add(_source(IDENTIFIERS_A, title="s1"))
        keep_value = _assertion(src_a, prop)
        other_value = _assertion(src_a, prop)
        source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
        source_writer.delete(src_a.id)
        destination_writer.add(stored.source_assertion_node(other_value, title="other"))
        expected_side, expected_target = "keep", src_a.id

    assert keep_value.id == other_value.id
    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(SourceAssertionReplicasDisagree) as caught:
        relocation.consolidate(
            (source_writer, keep_value.id),
            (destination_writer, other_value.id),
            **CONSOLIDATE_FIELDS,
        )

    assert expected_side in str(caught.value)
    assert expected_target in str(caught.value)
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, keep_value.id)


@pytest.mark.parametrize("position", ["keep", "other"])
def test_a_replica_whose_source_resolves_to_another_kind_is_refused(position, source_writer, destination_writer):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    _seed(destination_writer, identifiers=IDENTIFIERS_A)
    alias = "source:" + "8" * 64
    dataset = stored.dataset_node(title="d", resources=[{"name": "r", "digest": "sha256:" + "d" * 32}])
    raw_write(
        source_writer.root, stored.stamp_semantic_identity(dataset.model_copy(update={"deprecated_ids": [alias]}))
    )
    source_writer._reconstruct()

    alias_target = Node(id=alias, kind="source", title="alias")
    bad_value = _assertion(alias_target, prop)
    good_value = _assertion(src_a, prop)
    assert bad_value.id == good_value.id

    if position == "keep":
        raw_write(source_writer.root, stored.source_assertion_node(bad_value, title="bad"))
        source_writer._reconstruct()
        destination_writer.add(stored.source_assertion_node(good_value, title="good"))
    else:
        source_writer.add(stored.source_assertion_node(good_value, title="good"))
        raw_write(destination_writer.root, stored.source_assertion_node(bad_value, title="bad"))
        destination_writer._reconstruct()

    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(SourceAssertionReplicasDisagree) as caught:
        relocation.consolidate(
            (source_writer, bad_value.id),
            (destination_writer, bad_value.id),
            **CONSOLIDATE_FIELDS,
        )

    assert position in str(caught.value)
    assert "dataset" in str(caught.value)
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, bad_value.id)


@pytest.mark.parametrize("rationale", ["", "\ud800"], ids=["empty", "unencodable"])
def test_rationale_refusal_precedes_replica_disagreement(rationale, source_writer, destination_writer):
    src_a, prop = _seed(source_writer, identifiers=IDENTIFIERS_A)
    src_b = source_writer.add(_source(IDENTIFIERS_B, title="s2"))
    _seed(destination_writer, identifiers=IDENTIFIERS_B)

    keep_value = _assertion(src_a, prop)
    other_value = _assertion(src_b, prop)
    source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
    destination_writer.add(stored.source_assertion_node(other_value, title="other"))

    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))

    with pytest.raises(RelocationRefused, match="rationale") as caught:
        relocation.consolidate(
            (source_writer, keep_value.id),
            (destination_writer, other_value.id),
            **MOVE_FIELDS,
            rationale=rationale,
        )

    assert type(caught.value) is RelocationRefused
    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, keep_value.id)


def test_disagreeing_judgment_refuses_even_at_matching_ids(source_writer, destination_writer, monkeypatch):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    keep_value = _assertion(src, prop, sign="asserts")
    other_value = _assertion(src, prop, sign="denies")
    keep_node = source_writer.add(stored.source_assertion_node(keep_value, title="keep"))
    other_node = destination_writer.add(stored.source_assertion_node(keep_value, title="other"))

    before_files = (_files(source_writer), _files(destination_writer))
    before_intents = (list(_recording_port(source_writer).intents), list(_recording_port(destination_writer).intents))
    monkeypatch.setattr(
        stored,
        "source_assertion_value",
        lambda node: keep_value if node.uid == keep_node.uid else other_value,
    )
    monkeypatch.setattr(relocation, "source_assertion_refusal", lambda value, relations, *, kind_of: None)

    with pytest.raises(SourceAssertionReplicasDisagree, match="disagree on reading or proposition bearing"):
        relocation.consolidate(
            (source_writer, keep_node.id),
            (destination_writer, other_node.id),
            **CONSOLIDATE_FIELDS,
        )

    _assert_nothing_written(source_writer, destination_writer, before_files, before_intents, keep_node.id)


def test_consolidation_unites_deprecated_ids_without_mutating_keep_facets(source_writer, destination_writer):
    src, prop = _seed(source_writer)
    _seed(destination_writer)
    value = _assertion(src, prop)
    dep_keep = "source-assertion:" + "2" * 64
    dep_other = "source-assertion:" + "1" * 64
    keep_node = stored.source_assertion_node(value, title="keep").model_copy(update={"deprecated_ids": [dep_keep]})
    other_node = stored.source_assertion_node(value, title="other").model_copy(update={"deprecated_ids": [dep_other]})
    raw_write(source_writer.root, keep_node)
    source_writer._reconstruct()
    raw_write(destination_writer.root, other_node)
    destination_writer._reconstruct()

    keep_facets_snapshot = dict(keep_node.facets)
    merged = relocation._merge_source_assertion(keep_node, other_node)
    assert keep_node.facets == keep_facets_snapshot
    assert merged.facets is not keep_node.facets
    assert merged.deprecated_ids == [dep_other, dep_keep]

    survivor, _, _ = relocation.consolidate(
        (source_writer, keep_node.id),
        (destination_writer, other_node.id),
        **CONSOLIDATE_FIELDS,
    )
    assert survivor.deprecated_ids == [dep_other, dep_keep]
    assert not destination_writer.read_view.holds(other_node.id)


def test_replicas_consolidate_through_a_read_mount(tmp_path):
    mount = _writer(tmp_path / "mount", domains=PINS.domains)
    src_a, prop = _seed(mount, identifiers=IDENTIFIERS_A)
    corrected = mount.correct_identifier(src_a.id, IDENTIFIERS_B, grounds="canonical DOI")
    keep_root = (tmp_path / "keep").resolve()
    keep_writer = CorpusWriter(
        keep_root,
        DefaultExecutor,
        authority=FULL,
        profile=WITH_BIOLOGY,
        read_mounts=[mount.root.resolve()],
        operation_port=OperationRecorder(keep_root, authority=FULL, profile=WITH_BIOLOGY),
    )
    keep_writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    other_writer = _writer(tmp_path / "other", domains=PINS.domains)
    _seed(other_writer, identifiers=IDENTIFIERS_A)

    session_c = "session:" + "c" * 32
    keep_value = _assertion(corrected, prop)
    other_value = _assertion(src_a, prop, recorded_by=session_c)
    keep_writer.add(stored.source_assertion_node(keep_value, title="mounted"))
    raw_write(other_writer.root, stored.source_assertion_node(other_value, title="other"))
    other_writer._reconstruct()

    survivor, _, _ = relocation.consolidate(
        (keep_writer, keep_value.id),
        (other_writer, other_value.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep_value.id
    assert stored.source_assertion_value(keep_writer.read_view.get(keep_value.id)).recorded_by == ACTOR
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, corrected.id)]
    assert not other_writer.read_view.holds(other_value.id)


def test_consolidate_source_assertions_durably_on_certified_volume(certified_work: Path):
    keep_root = certified_work / "keep"
    other_root = certified_work / "other"
    for root in (keep_root, other_root):
        init_corpus_root(root, authority=FULL)
        open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=pins_for(WITH_BIOLOGY))

    keep_writer = open_corpus(keep_root, authority=FULL, profile=WITH_BIOLOGY)
    other_writer = open_corpus(other_root, authority=FULL, profile=WITH_BIOLOGY)
    src_a = keep_writer.add(_source(IDENTIFIERS_A))
    corrected = keep_writer.correct_identifier(src_a.id, IDENTIFIERS_B, grounds="canonical DOI")
    prop = keep_writer.add(_proposition())
    other_writer.add(_source(IDENTIFIERS_A))
    other_writer.add(_proposition())

    session_b = "session:" + "b" * 32
    keep_value = _assertion(corrected, prop, recorded_by=session_b)
    other_value = _assertion(src_a, prop, recorded_by=ACTOR)
    keep_writer.import_bundle([stored.source_assertion_node(keep_value, title="keep")], **BUNDLE_FIELDS)
    other_writer.add(stored.source_assertion_node(other_value, title="other"))

    seam = science_root._log_seam()
    other_before = seam.inspect_registered(other_root)
    assert type(other_before) is WellFormedView
    other_before_count = len(other_before.entries)

    survivor, keep_report, other_report = relocation.consolidate(
        (keep_writer, keep_value.id),
        (other_writer, other_value.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep_value.id
    assert [(r.predicate, r.target) for r in survivor.relations] == [(stored.ANCHORED_IN, corrected.id)]
    assert keep_report.operation == "consolidate" and other_report.operation == "consolidate"

    reloaded_keep = open_corpus(keep_root, authority=FULL, profile=WITH_BIOLOGY)
    reloaded_other = open_corpus(other_root, authority=FULL, profile=WITH_BIOLOGY)
    assert stored.source_assertion_value(reloaded_keep.read_view.get(keep_value.id)) == keep_value
    assert not reloaded_other.read_view.holds(other_value.id)
    assert reloaded_other.read_view.resolve(other_value.id) is None
    assert not path_for(other_root, other_value.id).exists()

    other_after = seam.inspect_registered(other_root)
    assert type(other_after) is WellFormedView
    assert len(other_after.entries) > other_before_count


def test_a_published_assertion_with_its_source_and_proposition_admits_at_an_empty_destination(certified_work: Path):
    base = Path(certified_work).resolve()
    alpha_id, alpha_writer = _corpus(base / "alpha", WITH_BIOLOGY)
    src = alpha_writer.add(_source())
    prop = alpha_writer.add(_proposition())
    value = _assertion(src, prop, quote="caf\u00e9")
    assertion = alpha_writer.add(stored.source_assertion_node(value, title="assertion"))
    selected = (assertion.id, src.id, prop.id)

    written = base / "written"
    _corpus(written, V2)
    config = WorldConfig(base / "world", "e" * 32, (base / "alpha", written))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(base / "alpha", provenance=Fresh())
    world.admit(written, provenance=Fresh())
    epoch.build_epoch(world, coverage=frozenset({alpha_id}), bindings=hold_shipped(world))
    resolver = CoordinationResolver({config.corpus_roots[0]: WITH_BIOLOGY, config.corpus_roots[1]: V2})
    project = open_corpus(written, authority=FULL, profile=V2, coordination_resolver=resolver).mint_coordination(
        "project", content=content_for("project", query=_addresses(*selected))
    )
    staging_profile = compile_profile(
        shipped_base_contract(), [biology("fixture")], coordination=shipped_coordination(2)
    )
    ops, dest = base / "ops", base / "dest"
    ops.mkdir()
    dest.mkdir()

    outcome = publish(
        open_corpus(written, authority=PUBLISHES, profile=V2, coordination_resolver=resolver),
        resolver,
        open_world(config, authority=PUBLISHES),
        view=coordination_revision(project).address,
        destination=Destination.local(str(dest)),
        operations_root=ops,
        staging_profile=staging_profile,
        clock=Clock(),
        seam=moment_seam(),
    )
    assert type(outcome) is Published, outcome

    exported = dest / outcome.corpus_id
    recipient = WorldConfig(base / "recipient", "c" * 32, (exported,))
    init_world_root(recipient, authority=FULL)
    recipient_world = open_world(recipient, authority=FULL)
    observers = ObserverSet(
        (ArtifactCarrier.from_bytes((dest / f"{outcome.corpus_id}.head-artifact.v1").read_bytes()),)
    )
    _, report = admit_publication(recipient_world, exported, observers)
    assert report.outcome == "validated"
    built = epoch.build_epoch(
        recipient_world, coverage=frozenset({outcome.corpus_id}), bindings=hold_shipped(recipient_world)
    )
    view = open_world_view(recipient_world, built)
    for ref in selected:
        assert node_to_markdown(view.get(ref)) == node_to_markdown(alpha_writer.read_view.get(ref))
    published = ReadView.opened_at(exported)
    assert stored.source_assertion_value(published.get(value.id)) == value
    assert stored.source_assertion_value(published.get(value.id)).read.span.quote == "caf\u00e9"
    assert stored.source_assertion_value(view.get(value.id)) == value
