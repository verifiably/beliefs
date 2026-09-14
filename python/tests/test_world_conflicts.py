"""W8 and W8b read over existing code (slice 4 §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_cut4 import raw_write
from nodes.core.corpus import Corpus
from profiles import WITH_BIOLOGY
from test_identifier_correction import ADDR_B, REPORT, B
from test_relocation import CONSOLIDATE_FIELDS, MOVE_FIELDS, _recording_port, _writer
from test_world_build import ALPHA, BETA, make_world
from test_world_epoch import admitted_world, derivation_bindings, epochs_tree, publish

GAMMA = "c" * 32

from beliefs import relocation, stored
from beliefs.corpus import ReadView, corpus_check
from beliefs.errors import (
    AddressDisagreement,
    AddressMapConflict,
    DuplicateLocation,
    HistoryDisagreement,
    SourceAddressDisagreement,
)
from beliefs.world import registry
from beliefs.world.view import open_world_view


def root_tree(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def conflict_world(tmp_path: Path, *, coverage=(ALPHA, BETA), twin_of="dataset:a", same_address=True, same_uid=False):
    """Two admitted corpora, BETA holding a twin of ALPHA's record."""
    world, recorder, bindings, roots = admitted_world(tmp_path, coverage)
    original = Corpus(roots[coverage[0]]).get(twin_of)
    twin = original.model_copy(deep=True, update={
        "id": original.id if same_address else "dataset:twin",
        "uid": original.uid if same_uid else "d" * 32,
    })
    raw_write(roots[coverage[1]], twin)
    return world, recorder, bindings, roots, original, twin


class TestW8DuplicateLocation:
    def test_the_build_refuses_naming_both_claims_and_no_carrier(self, tmp_path):
        world, _r, bindings, roots, original, _twin = conflict_world(tmp_path)
        before = epochs_tree(world)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        finding = caught.value.finding
        assert finding.code == "duplicate-location" and finding.ref == original.id
        assert finding.detail == (
            f"corpus/uid claims=(('{ALPHA}', '{original.uid}'), ('{BETA}', '{_twin.uid}'))"
        )
        assert "resolve with consolidate" in finding.message and str(roots[ALPHA]) not in finding.detail
        assert epochs_tree(world) == before

    def test_the_other_registration_order_gives_the_same_code_ref_and_claims(self, tmp_path):
        _world, _r, _b, roots, _o, _t = conflict_world(tmp_path)
        findings = []
        for name, order in (("f", (roots[ALPHA], roots[BETA])), ("b", (roots[BETA], roots[ALPHA]))):
            world = make_world(tmp_path / name, *order)
            for corpus_root in order:
                world.admit(corpus_root, provenance=registry.Fresh())
            with pytest.raises(AddressMapConflict) as caught:
                publish(world, (ALPHA, BETA), derivation_bindings(world))
            findings.append(caught.value.finding)
        assert (findings[0].code, findings[0].ref, findings[0].detail) == (findings[1].code, findings[1].ref, findings[1].detail)
        assert findings[0].code == "duplicate-location"

    @pytest.mark.parametrize("keep_first", [True, False])
    def test_consolidate_repairs_with_the_authored_survivor_and_the_rebuild_publishes(self, tmp_path, keep_first):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        record = stored.source_node(title="kept", identifiers={"doi": "10.1234/abc"})
        left.add(record)
        right.add(record.model_copy(deep=True, update={"uid": "e" * 32}))
        keep, other = (left, right) if keep_first else (right, left)
        survivor, _, _ = relocation.consolidate((keep, record.id), (other, record.id), **CONSOLIDATE_FIELDS)
        assert survivor.uid == keep.read_view.get(record.id).uid
        assert other.read_view.resolve(record.id) is None
        world = make_world(tmp_path / "world", left.root, right.root)
        for writer in (left, right):
            world.admit(writer.root, provenance=registry.Fresh())
        published = publish(world, (left.corpus_id, right.corpus_id), derivation_bindings(world))
        view = open_world_view(world, published)
        assert view.get(record.id).uid == survivor.uid
        assert view.corpus_of(record.id) == keep.corpus_id
        assert [node.id for node in view.iter_stored()].count(record.id) == 1

    def test_move_into_the_occupied_destination_refuses_thereafter(self, tmp_path):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        record = stored.source_node(title="kept", identifiers={"doi": "10.1234/abc"})
        left.add(record)
        right.add(record.model_copy(deep=True))
        before = {id(writer): (root_tree(writer.root), list(_recording_port(writer).intents)) for writer in (left, right)}
        with pytest.raises(DuplicateLocation):
            relocation.move(left, right, record.id, **MOVE_FIELDS)
        for writer in (left, right):
            assert root_tree(writer.root) == before[id(writer)][0]
            assert _recording_port(writer).intents == before[id(writer)][1]


class TestW8AddressConflict:
    def test_disagreeing_bases_at_one_address_refuse_the_build_before_any_basis_is_read(self, tmp_path):
        world, _r, bindings, roots = admitted_world(tmp_path, (ALPHA, BETA))
        raw_write(roots[ALPHA], stored.source_node(title="p", identifiers=B))
        raw_write(roots[BETA], stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        assert caught.value.finding.code == "duplicate-location" and caught.value.finding.ref == ADDR_B

    @pytest.mark.parametrize("keep_first", [True, False])
    def test_consolidate_refuses_and_no_basis_wins(self, tmp_path, keep_first):
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        left.add(stored.source_node(title="p", identifiers=B))
        right.add(stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        keep, other = (left, right) if keep_first else (right, left)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        before_state = {
            id(writer): (root_tree(writer.root), list(_recording_port(writer).intents)) for writer in (left, right)
        }
        with pytest.raises(HistoryDisagreement):
            relocation.consolidate((keep, ADDR_B), (other, ADDR_B), rationale="r", **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before
        for writer in (left, right):
            assert root_tree(writer.root) == before_state[id(writer)][0]
            assert _recording_port(writer).intents == before_state[id(writer)][1]

    def test_a_source_at_the_wrong_address_refuses_at_the_write_boundary(self, tmp_path):
        writer = _writer(tmp_path / "only")
        forged = stored.source_node(title="p", identifiers=B).model_copy(update={"id": "source:Chen2023"})
        with pytest.raises(SourceAddressDisagreement):
            writer.add(forged)


class TestW8b:
    def test_one_uid_under_two_addresses_is_corruption_and_no_repair_is_offered(self, tmp_path):
        world, _r, bindings, _roots, original, _twin = conflict_world(tmp_path, same_address=False, same_uid=True)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        finding = caught.value.finding
        assert finding.code == "uid-corruption" and finding.ref == original.uid
        assert "no repair is offered" in finding.message and "consolidate" not in finding.message
        left = _writer(tmp_path / "left")
        right = _writer(tmp_path / "right")
        keep = left.add(stored.source_node(title="kept", identifiers={"doi": "10.1234/kept"}))
        other = right.add(stored.source_node(title="other", identifiers={"doi": "10.1234/other"}).model_copy(update={"uid": keep.uid}))
        with pytest.raises(AddressDisagreement):
            relocation.consolidate((left, keep.id), (right, other.id), **CONSOLIDATE_FIELDS)

    @pytest.mark.parametrize("same_uid", [True, False])
    def test_two_records_at_one_address_are_duplicate_location_with_shared_or_distinct_uids(self, tmp_path, same_uid):
        world, _r, bindings, _roots, original, _twin = conflict_world(tmp_path, same_uid=same_uid)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA), bindings)
        assert (caught.value.finding.code, caught.value.finding.ref) == ("duplicate-location", original.id)

    def test_corruption_outranks_duplication(self, tmp_path):
        world, _r, bindings, roots, original, _twin = conflict_world(tmp_path, coverage=(ALPHA, BETA, GAMMA), same_uid=True)
        third = original.model_copy(deep=True, update={"id": "dataset:third"})
        raw_write(roots[GAMMA], third)
        with pytest.raises(AddressMapConflict) as caught:
            publish(world, (ALPHA, BETA, GAMMA), bindings)
        assert caught.value.finding.code == "uid-corruption"

    def test_each_corpus_alone_reports_neither(self, tmp_path):
        world, _r, bindings, roots, _o, _t = conflict_world(tmp_path)
        for corpus_id in (ALPHA, BETA):
            publish(world, (corpus_id,), bindings)
            findings = corpus_check(ReadView.opened_at(roots[corpus_id]), WITH_BIOLOGY)
            assert not [f for f in findings if f.code in ("uid-corruption", "duplicate-location")]
