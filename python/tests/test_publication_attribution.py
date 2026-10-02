"""Cut 46: origins, release authorization and frozen publication selection."""
from __future__ import annotations

from pathlib import Path

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_add
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import publication_arrival, stored
from beliefs.corpus import CorpusWriter, corpus_check
from beliefs.errors import (
    MalformedRecord,
    ManifestAlreadyPresent,
    PublicationArrivalRefused,
    PublicationReadingRefused,
    ValidationRefused,
)
from beliefs.profile import shipped_coordination
from beliefs.publication import (
    _marker_release_malformed,
    marker_consistent,
    marker_record,
    publication_content_malformed,
)
from beliefs.publication_arrival import admit_publication, publication_tip

FIXTURES = Path(__file__).parent / 'fixtures'
ORIGIN = ('run:a', 'c' * 32, 'd' * 32)


def marker(entries=None, selection=('run:a',)):
    return marker_record(intent(), world_id='a' * 32, epoch='b' * 64, selection=selection, attributions=entries)


def test_y18_a_closed_shapes():
    old = marker_record(intent(), world_id='a' * 32, epoch='b' * 64, selection=('run:a',))
    assert node_to_markdown(old).encode() == (FIXTURES / 'publication-v2-marker.md').read_bytes()
    for entries in (None, (), (ORIGIN,)):
        node = marker(entries)
        assert not publication_content_malformed(node)
        node.facets['coordination']['published_from']['extra'] = 'bad'
        assert publication_content_malformed(node)


@pytest.mark.parametrize('entries', [[], [ORIGIN], (list(ORIGIN),), (('run:a', 'c'*32),), (('run:a', 'c'*32, 1),), 'bad'])
def test_y18_b_member_types(entries):
    with pytest.raises(MalformedRecord):
        marker(entries)
    node = marker(())
    node.facets['coordination']['published_from']['attributions'] = entries
    assert publication_content_malformed(node) == (entries != [])


@pytest.mark.parametrize('entries', [(ORIGIN, ORIGIN), (('run:b', 'c'*32, 'd'*32), ORIGIN)])
def test_y18_c_strict_order(entries):
    assert not publication_content_malformed(marker(()))
    with pytest.raises(MalformedRecord):
        marker(entries, ('run:a', 'run:b'))
    node = marker(())
    node.facets['coordination']['published_from']['attributions'] = [list(row) for row in entries]
    assert publication_content_malformed(node)


@pytest.mark.parametrize('ref', ['run:b', 'bad', 'project:a', ''])
def test_y18_d_selected_addresses(ref):
    with pytest.raises(MalformedRecord):
        marker(((ref, 'c'*32, 'd'*32),))
    node = marker(())
    node.facets['coordination']['published_from']['attributions'] = [[ref, 'c'*32, 'd'*32]]
    assert publication_content_malformed(node)


def test_y18_e_identity_split():
    old, carried = marker(), marker((ORIGIN,))
    other = marker((('run:a', 'e'*32, 'f'*32),))
    assert old.id == carried.id == other.id and old.uid == carried.uid == other.uid
    assert all(marker_consistent(node) for node in (old, carried, other))
    assert len({node_to_markdown(node) for node in (old, carried, other)}) == 3


def test_y18_p_v3_succession():
    v2, v3 = shipped_coordination(2), shipped_coordination(3)
    assert v3.predecessor == v2.content_identity
    assert v3.schema_projection() == v2.schema_projection()
    assert v3.content_identity != v2.content_identity


def writer_at(tmp_path, version):
    profile = coordination_profile(None, version=version)
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer


def test_y18_q_explicit_activation(tmp_path):
    assert shipped_coordination() is shipped_coordination(2)
    writer = writer_at(tmp_path / 'new', 3)
    writer._stage_marker(marker(()))
    assert writer.read_view.get(marker(()).id).id == marker(()).id
    old = writer_at(tmp_path / 'old', 2)
    with pytest.raises(ManifestAlreadyPresent):
        old.adopt_manifest(profile=pins_for(coordination_profile(None, version=3)))


@pytest.mark.parametrize('version,entries', [(2, (ORIGIN,)), (3, None)])
def test_y18_j_staged_release(tmp_path, version, entries):
    node = marker(entries)
    assert all(_marker_release_malformed(node, pin) for pin in (None, 'unsupported', 'coordination:' + shipped_coordination(1).content_identity))
    correct_pin = 'coordination:' + shipped_coordination(3 if entries is not None else 2).content_identity
    assert not _marker_release_malformed(node, correct_pin)
    writer = writer_at(tmp_path, version)
    with pytest.raises(ValidationRefused, match='staged marker'):
        writer._stage_marker(marker(entries))
    assert list(writer.read_view.iter_stored()) == []


@pytest.mark.parametrize('version,entries', [(2, (ORIGIN,)), (3, None)])
def test_y18_k_audit_release(tmp_path, version, entries):
    writer = writer_at(tmp_path, version)
    raw_add(writer.root, marker(entries))
    findings = corpus_check(writer.read_view, coordination_profile(None, version=version))
    assert any(f.code == 'coordination-facet-malformed' for f in findings)
    assert not any(f.code == 'profile-mismatch' for f in findings)


@pytest.mark.parametrize('version,entries', [(2, (ORIGIN,)), (3, None)])
def test_y18_l_arrival_release(tmp_path, monkeypatch, version, entries):
    writer = writer_at(tmp_path, version)
    raw_add(writer.root, stored.run_node('a', title='a', spec='s', produces=[]), marker(entries))
    calls = []
    monkeypatch.setattr(publication_arrival, 'admit_arrival', lambda *args: calls.append(args))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication('world', writer.root, 'observers')
    assert caught.value.reason == 'marker-malformed' and not calls


@pytest.mark.parametrize('version,entries', [(2, (ORIGIN,)), (3, None)])
def test_y18_m_tip_release(tmp_path, version, entries):
    writer = writer_at(tmp_path, version)
    raw_add(writer.root, stored.run_node('a', title='a', spec='s', produces=[]), marker(entries))
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((writer.root,), intent().view, intent().destination)
    assert caught.value.reason == 'marker-malformed' and caught.value.corpus_id == writer.corpus_id
