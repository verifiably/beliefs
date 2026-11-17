"""Source assertion routes across import, move, read mounts, source correction, coreference, and delete."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

import pytest
from authority import ACTOR, FULL
from fixtures_cut4 import path_for, raw_write
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_relocation import MOVE_FIELDS
from test_world_receipts import hold_shipped, publish, world_over

from beliefs import relocation, stored
from beliefs import root as science_root
from beliefs.claim import Referent, build_claim
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.errors import ActorMismatch, ImportRefused, SourceAssertionRefused
from beliefs.projection import project_claim
from beliefs.root import init_corpus_root, open_corpus
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from beliefs.world import derive, read, registry
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView

GENE = "biology/gene"
AFFECTS = "biology/affects"
OTHER = "someone-else"
IDENTIFIERS_A = {"pmid": "1"}
IDENTIFIERS_B = {"doi": "10.1234/abc"}


class _BundleFields(TypedDict):
    observer: str
    instrument: str
    opened_at: str
    closed_at: str


BUNDLE_FIELDS: _BundleFields = {
    "observer": MOVE_FIELDS["observer"],
    "instrument": MOVE_FIELDS["instrument"],
    "opened_at": MOVE_FIELDS["opened_at"],
    "closed_at": MOVE_FIELDS["closed_at"],
}


def _writer(root: Path) -> CorpusWriter:
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return writer


def _source(identifiers: dict[str, str] | None = None, *, title: str = "s") -> Node:
    return stored.source_node(title=title, identifiers=IDENTIFIERS_A if identifiers is None else identifiers)


def _proposition() -> Node:
    claim = build_claim(
        WITH_BIOLOGY,
        operator=AFFECTS,
        roles={"cause": Referent(GENE, "EX:a"), "effect": Referent(GENE, "EX:b")},
        layer="causal",
        polarity="positive",
    )
    return stored.proposition_node("ab", title="ab", claim=project_claim(claim))


def _assertion(source: Node, proposition: Node, /, **changes: object) -> SourceAssertion:
    fields: dict[str, object] = {
        "source": source.id,
        "sha256": "a" * 64,
        "media_type": "application/pdf",
        "extent": "full",
        "quote": "PHF19 is overexpressed",
        "locator": "Results, para 2",
        "extracted_by": ACTOR,
        "attributed_to": None,
        "sign": "asserts",
        "proposition": proposition.id,
        "recorded_by": ACTOR,
    }
    unknown = set(changes) - set(fields)
    if unknown:
        raise ValueError(f"unknown _assertion fields: {sorted(unknown)}")
    fields.update(changes)
    return SourceAssertion(
        source=cast(str, fields["source"]),
        read=Reading(
            representation=Representation(
                sha256=cast(str, fields["sha256"]),
                media_type=cast(str, fields["media_type"]),
                extent=cast(str, fields["extent"]),
            ),
            span=Span(
                quote=cast(str, fields["quote"]),
                locator=cast(str, fields["locator"]),
            ),
            extracted_by=cast(str, fields["extracted_by"]),
            attributed_to=cast(str | None, fields["attributed_to"]),
        ),
        bears_on=Bearing(
            sign=cast(str, fields["sign"]),
            proposition=cast(str, fields["proposition"]),
        ),
        recorded_by=cast(str, fields["recorded_by"]),
    )


def _with_assesses(value: SourceAssertion, proposition: Node) -> Node:
    node = stored.source_assertion_node(value, title="t")
    return stored.stamp_semantic_identity(
        node.model_copy(
            update={
                "relations": [*node.relations, Relation(source=value.id, predicate="assesses", target=proposition.id)]
            }
        )
    )


def test_import_keeps_a_recorder_of_another_actor(tmp_path):
    writer = _writer(tmp_path / "corpus")
    src = writer.add(_source())
    prop = writer.add(_proposition())
    value = _assertion(src, prop, recorded_by=OTHER)
    node = stored.source_assertion_node(value, title="t")

    with pytest.raises(ActorMismatch):
        writer.add(node)

    writer.import_bundle([node], **BUNDLE_FIELDS)

    assert writer.read_view.holds(value.id)
    restored = stored.source_assertion_value(writer.read_view.get(value.id))
    assert restored == value
    assert restored.recorded_by == OTHER


def test_import_refuses_an_assesses_edge_as_edge_mismatch(tmp_path):
    writer = _writer(tmp_path / "corpus")
    src = writer.add(_source())
    prop = writer.add(_proposition())
    value = _assertion(src, prop)
    with_assesses = _with_assesses(value, prop)

    with pytest.raises(ImportRefused) as caught:
        writer.import_bundle([with_assesses], **BUNDLE_FIELDS)

    assert caught.value.member == value.id
    assert isinstance(caught.value.__cause__, SourceAssertionRefused)
    assert caught.value.__cause__.code == "source-assertion-edge-mismatch"
    assert not writer.read_view.holds(value.id)


def test_import_resolves_a_source_and_proposition_arriving_in_the_same_bundle(tmp_path):
    writer = _writer(tmp_path / "corpus")
    src = _source()
    prop = _proposition()
    value = _assertion(src, prop, recorded_by=OTHER)
    node = stored.source_assertion_node(value, title="t")

    with pytest.raises(ImportRefused) as caught:
        writer.import_bundle([node], **BUNDLE_FIELDS)
    assert caught.value.member == value.id
    assert isinstance(caught.value.__cause__, SourceAssertionRefused)
    assert caught.value.__cause__.code == "source-assertion-ref-unresolved"
    assert not writer.read_view.holds(value.id)

    writer.import_bundle([node, src, prop], **BUNDLE_FIELDS)

    assert writer.read_view.holds(src.id)
    assert writer.read_view.holds(prop.id)
    assert writer.read_view.holds(value.id)
    assert stored.source_assertion_value(writer.read_view.get(value.id)) == value


def test_move_carries_an_assertion_into_a_corpus_holding_its_source_and_proposition(tmp_path):
    source_writer = _writer(tmp_path / "source")
    destination_writer = _writer(tmp_path / "destination")
    src = source_writer.add(_source())
    prop = source_writer.add(_proposition())
    destination_writer.add(_source())
    destination_writer.add(_proposition())
    value = _assertion(src, prop)
    minted = source_writer.add(stored.source_assertion_node(value, title="t"))

    moved, destination_report, source_report = relocation.move(
        source_writer, destination_writer, minted.id, **MOVE_FIELDS
    )

    assert moved.id == minted.id
    assert destination_writer.read_view.holds(minted.id)
    assert stored.source_assertion_value(destination_writer.read_view.get(minted.id)) == value
    assert [(r.predicate, r.target) for r in destination_writer.read_view.get(minted.id).relations] == [
        (stored.ANCHORED_IN, src.id)
    ]
    assert not source_writer.read_view.holds(minted.id)
    assert source_writer.read_view.resolve(minted.id) is None
    assert destination_report.operation == "move" and source_report.operation == "move"


def test_move_into_a_corpus_lacking_the_source_is_refused_as_unresolved(tmp_path):
    source_writer = _writer(tmp_path / "source")
    destination_writer = _writer(tmp_path / "destination")
    src = source_writer.add(_source())
    prop = source_writer.add(_proposition())
    destination_writer.add(_proposition())
    value = _assertion(src, prop)
    minted = source_writer.add(stored.source_assertion_node(value, title="t"))

    with pytest.raises(SourceAssertionRefused) as caught:
        relocation.move(source_writer, destination_writer, minted.id, **MOVE_FIELDS)

    assert caught.value.code == "source-assertion-ref-unresolved"
    assert "the source " in str(caught.value)
    assert source_writer.read_view.holds(minted.id)
    assert not destination_writer.read_view.holds(minted.id)


def test_move_refuses_an_assertion_with_an_extra_edge(tmp_path):
    source_writer = _writer(tmp_path / "source")
    destination_writer = _writer(tmp_path / "destination")
    src = source_writer.add(_source())
    prop = source_writer.add(_proposition())
    destination_writer.add(_source())
    destination_writer.add(_proposition())
    value = _assertion(src, prop)
    with_assesses = _with_assesses(value, prop)
    raw_write(source_writer.root, with_assesses)
    source_writer._reconstruct()
    source_path = path_for(source_writer.root, with_assesses.id)
    before_bytes = source_path.read_bytes()

    with pytest.raises(SourceAssertionRefused) as caught:
        relocation.move(source_writer, destination_writer, with_assesses.id, **MOVE_FIELDS)

    assert caught.value.code == "source-assertion-edge-mismatch"
    assert source_path.read_bytes() == before_bytes
    assert source_writer.read_view.holds(with_assesses.id)
    assert not destination_writer.read_view.holds(with_assesses.id)


def test_a_source_and_proposition_held_only_through_a_read_mount_resolve(tmp_path):
    mount_root = (tmp_path / "mount").resolve()
    write_root = (tmp_path / "write").resolve()
    mount = _writer(mount_root)
    src = mount.add(_source())
    prop = mount.add(_proposition())
    unmounted = _writer(write_root)
    value = _assertion(src, prop)
    node = stored.source_assertion_node(value, title="t")

    with pytest.raises(SourceAssertionRefused) as caught:
        unmounted.add(node)
    assert caught.value.code == "source-assertion-ref-unresolved"
    assert not ReadView.opened_at(write_root).holds(value.id)

    mounted = CorpusWriter(
        write_root,
        DefaultExecutor,
        authority=FULL,
        profile=WITH_BIOLOGY,
        read_mounts=[mount_root],
    )
    held = mounted.add(node)

    assert held.id == value.id
    write_view = ReadView.opened_at(write_root)
    mount_view = ReadView.opened_at(mount_root)
    assert write_view.holds(held.id)
    assert stored.source_assertion_value(write_view.get(held.id)) == value
    assert not mount_view.holds(held.id)
    assert not write_view.holds(src.id)
    assert not write_view.holds(prop.id)


def test_an_assertion_stays_byte_unchanged_and_resolves_after_its_source_is_corrected(tmp_path):
    writer = _writer(tmp_path / "corpus")
    source_a = writer.add(_source(IDENTIFIERS_A))
    prop = writer.add(_proposition())
    value = _assertion(source_a, prop)
    minted = writer.add(stored.source_assertion_node(value, title="t"))
    assertion_path = path_for(writer.root, minted.id)
    bytes_before = assertion_path.read_bytes()

    corrected = writer.correct_identifier(source_a.id, IDENTIFIERS_B, grounds="canonical DOI")

    assert corrected.id != source_a.id
    assert corrected.deprecated_ids == [source_a.id]
    assert assertion_path.read_bytes() == bytes_before
    (edge,) = writer.read_view.get(minted.id).relations
    assert (edge.predicate, edge.target) == (stored.ANCHORED_IN, source_a.id)
    assert writer.read_view.resolve(edge.target) == corrected.id

    world = world_over(tmp_path, {writer.corpus_id: writer.root})
    published = publish(world, (writer.corpus_id,), hold_shipped(world))
    address_map = read._address_map(published)
    assert address_map[source_a.id] == address_map[corrected.id]
    assert address_map[source_a.id] == derive.AddressEntry(
        corrected.uid, registry.content_identity(corrected), (writer.corpus_id,)
    )
    resolved_a = read.resolve_address(world, published, edge.target)
    resolved_b = read.resolve_address(world, published, corrected.id)
    assert type(resolved_a) is read.Resolved
    assert resolved_a == resolved_b
    assert resolved_a.location == read.Location(writer.corpus_id, corrected.uid, (writer.corpus_id,))


def test_minting_against_a_deprecated_address_gives_the_same_id(tmp_path):
    writer = _writer(tmp_path / "corpus")
    source_a = writer.add(_source(IDENTIFIERS_A))
    prop = writer.add(_proposition())
    corrected = writer.correct_identifier(source_a.id, IDENTIFIERS_B, grounds="canonical DOI")
    assert corrected.deprecated_ids == [source_a.id]

    against_a = _assertion(source_a, prop)
    against_b = _assertion(corrected, prop)
    assert against_a.id == against_b.id

    minted = writer.add(stored.source_assertion_node(against_a, title="t"))

    assert minted.id == against_a.id
    assert writer.read_view.holds(against_a.id)
    back = writer.read_view.get(against_a.id)
    assert [(r.predicate, r.target) for r in back.relations] == [(stored.ANCHORED_IN, source_a.id)]
    assert writer.read_view.resolve(source_a.id) == corrected.id


def test_coreference_over_two_sources_renames_no_assertion(tmp_path):
    writer = _writer(tmp_path / "corpus")
    first = writer.add(_source(IDENTIFIERS_A, title="s1"))
    second = writer.add(_source(IDENTIFIERS_B, title="s2"))
    prop = writer.add(_proposition())
    first_assertion = writer.add(stored.source_assertion_node(_assertion(first, prop, sha256="a" * 64), title="t1"))
    second_assertion = writer.add(stored.source_assertion_node(_assertion(second, prop, sha256="b" * 64), title="t2"))
    first_path = path_for(writer.root, first_assertion.id)
    second_path = path_for(writer.root, second_assertion.id)
    first_bytes = first_path.read_bytes()
    second_bytes = second_path.read_bytes()

    attestation = writer.attest_coreference(
        stored.coreference_attestation_node(
            title="same source",
            endpoints=(first.id, second.id),
            stance=1,
            actor=ACTOR,
            grounds="same underlying paper",
            event_token="event-1",
        )
    )

    assert writer.read_view.holds(attestation.id)
    assert first_path.read_bytes() == first_bytes
    assert second_path.read_bytes() == second_bytes
    assert [(r.predicate, r.target) for r in writer.read_view.get(first_assertion.id).relations] == [
        (stored.ANCHORED_IN, first.id)
    ]
    assert [(r.predicate, r.target) for r in writer.read_view.get(second_assertion.id).relations] == [
        (stored.ANCHORED_IN, second.id)
    ]
    assert writer.read_view.resolve(first.id) == first.id
    assert writer.read_view.resolve(second.id) == second.id


def test_delete_is_admitted_and_logged(certified_work):
    root = certified_work / "corpus"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    src = writer.add(_source())
    prop = writer.add(_proposition())
    minted = writer.add(stored.source_assertion_node(_assertion(src, prop), title="t"))
    rel_path = path_for(root, minted.id).relative_to(root).as_posix()

    seam = science_root._log_seam()
    before = seam.inspect_registered(root)
    assert type(before) is WellFormedView
    before_count = len(before.entries)

    writer.delete(minted.id)

    assert writer.read_view.resolve(minted.id) is None
    assert not writer.read_view.holds(minted.id)
    assert not path_for(root, minted.id).exists()
    reloaded = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    assert reloaded.read_view.resolve(minted.id) is None

    after = seam.inspect_registered(root)
    assert type(after) is WellFormedView
    added = after.entries[before_count:]
    assert [type(entry) for entry in added] == [RegisteredEntryView, SettledEntryView]
    registration, settlement = added
    assert isinstance(registration, RegisteredEntryView) and isinstance(settlement, SettledEntryView)
    assert registration.fulfills is None
    assert len(registration.final) == 1 and registration.final[0][0] == rel_path
    assert seam.state_facts(registration.final[0][1]) == (("kind", "absent"),)
    assert settlement.registration == registration.digest and settlement.committed is True
    assert writer.read_view.holds(src.id) and writer.read_view.holds(prop.id)
