"""Cut 46: origins, release authorization and frozen publication selection."""
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_add
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import publication_arrival, stored
from beliefs.coordination import coordination_revision
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
    marker_uid,
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

from beliefs.consulted import CorpusPins
from beliefs.errors import PublicationRefused
from beliefs.identity import v1


def records():
    row = cast(dict[str, Any], v1.decode((FIXTURES / 'publication-v2-selection.v1').read_bytes()))['records'][0]
    return ((row['id'], row['text']),)


def test_y18_f_snapshot_formats():
    from beliefs.publish_request import Snapshot, decode_snapshot, encode_snapshot

    old = Snapshot('e'*32, records())
    assert encode_snapshot(old) == (FIXTURES / 'publication-v2-selection.v1').read_bytes()
    for entries in (None, (), (ORIGIN,)):
        value = Snapshot('e'*32, records(), entries)
        wire = encode_snapshot(value)
        assert decode_snapshot(wire) == value
        assert encode_snapshot(decode_snapshot(wire)) == wire
        projection = value.projection()
        assert ('attributions' in projection) == (entries is not None)
        for bad in ('bad', [[1, 'c'*32, 'd'*32]], [list(ORIGIN), list(ORIGIN)], [['run:extra', 'c'*32, 'd'*32]]):
            projection['attributions'] = bad
            with pytest.raises(MalformedRecord):
                decode_snapshot(v1.encode(projection))
        projection = value.projection()
        projection['extra'] = 'bad'
        with pytest.raises(MalformedRecord):
            decode_snapshot(v1.encode(projection))
    for bad in ([], [ORIGIN], (list(ORIGIN),), (('run:a','c'*32),)):
        with pytest.raises(MalformedRecord):
            Snapshot('e'*32, records(), cast(Any, bad))


def test_y18_g_snapshot_commitment():
    from beliefs.publish_request import Snapshot

    old, empty = Snapshot('e'*32, records()), Snapshot('e'*32, records(), ())
    a = Snapshot('e'*32, records(), (ORIGIN,))
    b = Snapshot('e'*32, records(), (('run:a','f'*32,'d'*32),))
    assert len({value.identity() for value in (old, empty, a, b)}) == 4
    assert 'attributions' not in old.projection() and empty.projection()['attributions'] == []


def pin(version):
    return 'coordination:' + shipped_coordination(version).content_identity


def test_y5_c_v3_destination_pins():
    from beliefs.publish_request import derive_pins

    base='science:'+'b'*64
    sources={'b':CorpusPins(base, {'coordination':pin(3),'physics':'physics:'+'a'*64}),
             'a':CorpusPins(base, {'coordination':pin(2),'biology':'biology:'+'c'*64})}
    value=derive_pins(sources,CorpusPins(base, {'coordination':pin(3), 'unused':'unused:'+'e'*64}))
    assert dict(value.domains) == {'coordination':pin(3),'physics':'physics:'+'a'*64,'biology':'biology:'+'c'*64}
    assert value.science_contract == base


@pytest.mark.parametrize('domain', ['science_contract','biology','physics'])
def test_y5_d_v3_disagreement(domain):
    from beliefs.publish_request import derive_pins

    base='science:'+'b'*64
    namespace = 'biology' if domain == 'science_contract' else domain
    a=CorpusPins(base,{'coordination':pin(2),namespace:namespace+':'+'a'*64})
    b=CorpusPins('science:'+'c'*64 if domain=='science_contract' else base,
                 {'coordination':pin(3),namespace:namespace+':' + ('a' if domain=='science_contract' else 'd')*64})
    with pytest.raises(PublicationRefused) as caught:
        derive_pins({'z':b,'a':a},CorpusPins(base,{'coordination':pin(3)}))
    assert caught.value.reason=='pins-disagree' and caught.value.field==domain and caught.value.corpus_ids==('a','z')

from types import SimpleNamespace

from beliefs.world import AdmissionRecord, CorpusManifest, ForkOf, Fresh, RegistryView, ReplicaOf


def capture_fixture(holdings, *, source_version=2, carried=None):
    profile = coordination_profile(None, version=source_version)
    manifests, captures, owners, admissions = {}, {}, {}, []
    for cid, (provenance, refs) in holdings.items():
        manifests[cid] = CorpusManifest(2, cid, pins_for(profile))
        nodes = tuple(stored.run_node(ref.split(':',1)[1], title=ref, spec='s', produces=[]) if ref.startswith('run:') else
                      Node(id=ref, uid='9'*32, kind=ref.split(':',1)[0],title=ref,body='',facets={},relations=[]) for ref in refs)
        value = marker_record(intent(event_token=cid), world_id='d'*32, epoch='f'*64,
             selection=tuple(sorted(refs)), attributions=None if source_version==2 else (carried or {}).get(cid,()))
        captures[cid] = (*nodes, value)
        owners.update({ref:cid for ref in refs})
        admissions.append(AdmissionRecord(manifests[cid], provenance, 'actor'))
    read = SimpleNamespace(corpus_of=owners.get, captured_manifest=manifests.__getitem__,captured_records=captures.__getitem__,get=lambda ref:next(n for n in captures[owners[ref]] if n.id==ref))
    return cast(Any, read), RegistryView(tuple(admissions),()), captures


@pytest.mark.parametrize('version', [2,3])
def test_y17_a_local_holdings(version):
    import beliefs.publish as act

    read, registry, _ = capture_fixture({'a'*32:(Fresh(),('run:a',)), 'b'*32:(ForkOf('a'*32,'c'*64),('run:b',))})
    assert act._selected_attributions(read, registry, ('run:a','run:b'),pin(version)) == (None if version==2 else ())


@pytest.mark.parametrize('kind', sorted(stored.WORLD_KINDS))
def test_y17_b_first_carry(kind):
    import beliefs.publish as act

    cid='a'*32
    read, registry, _=capture_fixture({cid:(ReplicaOf(cid),(kind+':a',))})
    assert act._selected_attributions(read,registry,(kind+':a',),pin(3)) == ((kind+':a',cid,marker_uid(cid)),)


def test_y17_c_forwarded_origin():
    import beliefs.publish as act

    cid='a'*32
    read, registry, _=capture_fixture({cid:(ReplicaOf(cid),('run:a',))},source_version=3,carried={cid:(ORIGIN,)})
    assert act._selected_attributions(read,registry,('run:a',),pin(3)) == (ORIGIN,)


def test_y17_d_selection_scope():
    import beliefs.publish as act

    cid='a'*32
    extra=('run:b','e'*32,'f'*32)
    read, registry, _=capture_fixture({cid:(ReplicaOf(cid),('run:a','run:b'))},source_version=3,carried={cid:(ORIGIN,extra)})
    assert act._selected_attributions(read,registry,('run:a',),pin(3)) == (ORIGIN,)


def test_y17_e_distinct_holders():
    import beliefs.publish as act

    a,b='a'*32,'b'*32
    read, registry, _=capture_fixture({b:(ReplicaOf(b),('run:b',)),a:(ReplicaOf(a),('run:a',))})
    assert act._selected_attributions(read,registry,('run:a','run:b'),pin(3)) == (('run:a',a,marker_uid(a)),('run:b',b,marker_uid(b)))


def test_y17_f_v2_refusal():
    import beliefs.publish as act

    a,b='a'*32,'b'*32
    read, registry, _=capture_fixture({b:(ReplicaOf(b),('run:b',)),a:(ReplicaOf(a),('run:a',))})
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,registry,('run:a','run:b'),pin(2))
    assert caught.value.reason=='attribution-contract-unpinned' and caught.value.corpus_ids==(a,b)


def test_y17_h_markerless_replica():
    import beliefs.publish as act

    a='a'*32
    read, registry, captures=capture_fixture({a:(ReplicaOf(a),('run:a',))})
    captures[a]=captures[a][:-1]
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,registry,('run:a',),pin(3))
    assert (caught.value.reason,caught.value.corpus_ids,caught.value.refs,caught.value.field)==('attribution-source-invalid',(a,),('run:a',),'marker-absent')


@pytest.mark.parametrize('version',[2,3])
@pytest.mark.parametrize('provenance',[Fresh(),ReplicaOf('a'*32)])
def test_y17_i_missing_holder(version,provenance):
    import beliefs.publish as act

    a='a'*32
    read, _, _=capture_fixture({a:(provenance,('run:a','run:b'))})
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,RegistryView((),()),('run:b','run:a'),pin(version))
    assert (caught.value.reason,caught.value.corpus_ids,caught.value.refs)==('attribution-holder-unregistered',(a,),('run:a','run:b'))


def test_y17_j_invalid_source_order():
    import beliefs.publish as act

    a,b='a'*32,'b'*32
    read, registry, captures=capture_fixture({b:(ReplicaOf(b),('run:b',)),a:(ReplicaOf(a),('run:a',))})
    captures[a]=captures[a][:-1]
    captures[b]=(*captures[b],marker_record(intent(event_token='c'*32),world_id='d'*32,epoch='f'*64,selection=('run:b',)))
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,registry,('run:b','run:a'),pin(3))
    assert (caught.value.corpus_ids,caught.value.field)==((a,),'marker-absent')


def test_y17_k_admission_before_layout():
    import beliefs.publish as act

    a,b='a'*32,'b'*32
    read, registry, captures=capture_fixture({a:(ReplicaOf(a),('run:a',)),b:(ReplicaOf(b),('run:b',))})
    captures[a]=captures[a][:-1]
    registry=RegistryView((registry.admissions[0],),())
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,registry,('run:a','run:b'),pin(3))
    assert caught.value.reason=='attribution-holder-unregistered' and caught.value.corpus_ids==(b,)


def test_y17_l_held_capture(monkeypatch):
    import beliefs.publish as act

    a='a'*32
    read, registry, _=capture_fixture({a:(ReplicaOf(a),('run:a',))})
    calls=[]
    records_at=read.captured_records
    manifest_at=read.captured_manifest
    read.captured_records=lambda cid:calls.append(('records',cid)) or records_at(cid)
    read.captured_manifest=lambda cid:calls.append(('manifest',cid)) or manifest_at(cid)
    monkeypatch.setattr(act.ReadView,'opened_at',lambda *args:pytest.fail('live root reopened'))
    value = act._selected_attributions(read,registry,('run:a',),pin(3))
    assert value is not None and value[0][1]==a
    assert calls==[('records',a),('manifest',a)]


def test_y17_p_legacy_source():
    import beliefs.publish as act

    a='a'*32
    read, registry, _=capture_fixture({a:(ReplicaOf(a),('run:a',))})
    assert act._selected_attributions(read,registry,('run:a',),pin(3))==(('run:a',a,marker_uid(a)),)
    read,registry,_=capture_fixture({a:(ReplicaOf(a),('run:a',))},source_version=3,carried={a:(ORIGIN,)})
    assert act._selected_attributions(read,registry,('run:a',),pin(3))==(ORIGIN,)


@pytest.mark.parametrize('source_version,entries',[(2,(ORIGIN,)),(3,None)])
def test_y18_n_source_release(source_version,entries):
    import beliefs.publish as act

    a='a'*32
    read,registry,captures=capture_fixture({a:(ReplicaOf(a),('run:a',))},source_version=source_version)
    captures[a]=(*captures[a][:-1],marker(entries))
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read,registry,('run:a',),pin(3))
    assert (caught.value.reason,caught.value.field,caught.value.corpus_ids)==('attribution-source-invalid','marker-malformed',(a,))

from dataclasses import replace

from coordination_fixtures import raw_coordination_node

from beliefs.errors import RegistryMalformed
from beliefs.intents.publish import Destination
from beliefs.report import RequestCorrupt
from beliefs.world import StatusRecord, WorldConfig


class Prepared(Exception):
    pass


def wrapper_fixture(tmp_path, monkeypatch, *, writer_version=3, source_version=2):
    import beliefs.publish as act

    a,b='a'*32,'b'*32
    read,registry,captures=capture_fixture({b:(ReplicaOf(b),('run:b',)),a:(ReplicaOf(a),('run:a',))},source_version=source_version)
    writer=writer_at(tmp_path / 'written',writer_version)
    calls=[]
    world=SimpleNamespace(config=WorldConfig(tmp_path/'world','e'*32,()),registry=lambda:calls.append('scan') or registry)
    project=raw_coordination_node('project','f'*32,'d'*32)
    resolver=SimpleNamespace(mounted=lambda:(writer.root,),resolve=lambda address:project)
    view=coordination_revision(project).address
    selection=SimpleNamespace(complete=True,selected=('run:a','run:b'),contributing=(a,b),absent=(),unresolved=())
    read.resolve=lambda ref:ref if ref in selection.selected else None
    monkeypatch.setattr(act,'current_epoch',lambda world:SimpleNamespace(packaging_identity='c'*64))
    monkeypatch.setattr(act,'open_world_view',lambda world,epoch:read)
    monkeypatch.setattr(act,'evaluate_query',lambda read,query:selection)
    def opening(*args,**kwargs):
        calls.append('intent')
        raise Prepared
    monkeypatch.setattr(act,'_open_publication',opening)
    ops,dest=tmp_path/'ops',tmp_path/'dest'
    ops.mkdir();dest.mkdir()
    def run():
        return act.publish(writer,cast(Any,resolver),cast(Any,world),view=view,destination=Destination.local(str(dest)),operations_root=ops,
            staging_profile=coordination_profile(None,version=writer_version),clock=lambda:'2026-10-02T00:00:00Z',seam=cast(Any,None))
    return SimpleNamespace(run=run,read=read,registry=registry,captures=captures,calls=calls,world=world,ops=ops,writer=writer,a=a,b=b)


def test_y5_e_v2_pin_precedence(tmp_path,monkeypatch):
    s=wrapper_fixture(tmp_path,monkeypatch,writer_version=2,source_version=3)
    before=tuple(s.writer.read_view.iter_stored())
    with pytest.raises(PublicationRefused) as caught:s.run()
    assert caught.value.reason=='pins-disagree' and caught.value.field=='coordination'
    assert s.calls==[] and list(s.ops.iterdir())==[] and tuple(s.writer.read_view.iter_stored())==before


def test_y17_g_before_intent(tmp_path,monkeypatch):
    s=wrapper_fixture(tmp_path,monkeypatch,writer_version=2)
    before=tuple(s.writer.read_view.iter_stored())
    with pytest.raises(PublicationRefused) as caught:s.run()
    assert caught.value.reason=='attribution-contract-unpinned' and caught.value.corpus_ids==(s.a,s.b)
    assert s.calls==['scan'] and list(s.ops.iterdir())==[] and tuple(s.writer.read_view.iter_stored())==before


@pytest.mark.parametrize('scenario',['retired','scan-error','missing-replica','missing-fresh-v2','missing-fresh-v3'])
def test_y17_o_registry_boundary(tmp_path,monkeypatch,scenario):
    import beliefs.publish as act

    version=2 if scenario=='missing-fresh-v2' else 3
    s=wrapper_fixture(tmp_path,monkeypatch,writer_version=version)
    registry=s.registry
    if scenario=='retired':registry=RegistryView(registry.admissions,(StatusRecord(s.a,'retired','actor'),))
    elif scenario.startswith('missing'):
        if 'fresh' in scenario:registry=RegistryView(tuple(replace(row,provenance=Fresh()) for row in registry.admissions[1:]),())
        else:registry=RegistryView(registry.admissions[1:],())
    error=RegistryMalformed('preparation scan')
    def scan():
        s.calls.append('scan')
        if scenario=='scan-error':raise error
        return registry
    s.world.registry=scan
    if scenario=='retired':
        seen=[]
        original=act._selected_attributions
        def selected(read,scanned,refs,coordination_pin):
            assert scanned.statuses==(StatusRecord(s.a,'retired','actor'),)
            result=original(read,scanned,refs,coordination_pin)
            assert result is not None
            seen.extend(result)
            return result
        monkeypatch.setattr(act,'_selected_attributions',selected)
        with pytest.raises(Prepared):s.run()
        assert len(seen)==2 and seen[0][1]==s.a
        assert s.calls==['scan','intent']
    elif scenario=='scan-error':
        with pytest.raises(RegistryMalformed) as caught:s.run()
        assert caught.value is error and s.calls==['scan']
    else:
        with pytest.raises(PublicationRefused) as caught:s.run()
        assert caught.value.reason=='attribution-holder-unregistered' and caught.value.corpus_ids==(s.b,)
        assert s.calls==['scan']
    assert list(s.ops.iterdir())==[]


def frozen_attempt(tmp_path, *, destination=None, entries=(ORIGIN,), coordination_pin=None):
    from beliefs.publish_request import PublishRequest, Snapshot, staging_world_id_for

    value=intent(destination=destination or intent().destination)
    snapshot=Snapshot(value.event_token,records(),entries)
    request=PublishRequest(value.event_token,value.view,value.destination,'b'*64,'a'*32,
           CorpusPins('science:'+'b'*64,{'coordination':coordination_pin or pin(3)}),snapshot.identity(),staging_world_id_for(value.event_token))
    return cast(Any,SimpleNamespace(opened=SimpleNamespace(intent=value),request=request,snapshot=snapshot,op=tmp_path))


def test_y17_m_local_frozen_marker(tmp_path,monkeypatch):
    import beliefs.publish as act

    a=frozen_attempt(tmp_path)
    monkeypatch.setattr(act,'_selected_attributions',lambda *args:pytest.fail('origin lookup on reconstruction'))
    for name in ('open_world_view', 'current_epoch', 'load_manifest'):
        monkeypatch.setattr(act,name,lambda *args:pytest.fail('source read on reconstruction'))
    node=act._expected_marker(a)
    assert node.facets['coordination']['published_from']['attributions']==[list(ORIGIN)]


def test_y17_n_remote_frozen_marker(tmp_path,monkeypatch):
    import beliefs.publish as act

    a=frozen_attempt(tmp_path,destination=Destination.remote('https://remote.test/pub'))
    monkeypatch.setattr(act,'_selected_attributions',lambda *args:pytest.fail('origin lookup on remote reconstruction'))
    for name in ('open_world_view', 'current_epoch', 'load_manifest'):
        monkeypatch.setattr(act,name,lambda *args:pytest.fail('source read on remote reconstruction'))
    node=act._expected_marker(a)
    assert node.facets['coordination']['published_from']['attributions']==[list(ORIGIN)]


@pytest.mark.parametrize('change',['origin','malformed'])
def test_y18_h_snapshot_tamper(tmp_path,change):
    import beliefs.publish as act
    from beliefs.publish_request import encode_request

    a=frozen_attempt(tmp_path)
    (tmp_path/'request.v1').write_bytes(encode_request(a.request))
    value=a.snapshot.projection()
    value['attributions']=[['run:a','e'*32,'d'*32]] if change=='origin' else [['run:a','bad','d'*32]]
    (tmp_path/'selection.v1').write_bytes(v1.encode(value))
    assert act._load(tmp_path,a.opened)==RequestCorrupt('snapshot-mismatch' if change=='origin' else 'snapshot-undecodable')


@pytest.mark.parametrize('entries,version', [(None,3),((),2),((),1),(None,1),((),None),(None,None),((),'unsupported')])
def test_y18_i_snapshot_pin(tmp_path,entries,version):
    import beliefs.publish as act
    from beliefs.publish_request import encode_request, encode_snapshot

    a=frozen_attempt(tmp_path,entries=entries)
    domains={} if version is None else {'coordination':'unsupported' if version=='unsupported' else pin(version)}
    request=replace(a.request,pins=CorpusPins(a.request.pins.science_contract,domains))
    (tmp_path/'request.v1').write_bytes(encode_request(request))
    (tmp_path/'selection.v1').write_bytes(encode_snapshot(a.snapshot))
    assert act._load(tmp_path,a.opened)==RequestCorrupt('snapshot-pin-disagrees')
    good=replace(request,pins=CorpusPins(request.pins.science_contract,{'coordination':pin(2 if entries is None else 3)}))
    (tmp_path/'request.v1').write_bytes(encode_request(good))
    assert act._load(tmp_path,a.opened)==(good,a.snapshot)


@pytest.mark.parametrize('version,entries',[(2,(ORIGIN,)),(3,None),(2,None),(3,())])
def test_y18_o_remote_release(tmp_path,monkeypatch,version,entries):
    import beliefs.publish as act
    from beliefs.publish_request import TransportMark

    node=marker(entries)
    path=tmp_path/'marker.md';path.write_text(node_to_markdown(node))
    manifest=CorpusManifest(2,'a'*32,pins_for(coordination_profile(None,version=version)))
    mark=TransportMark(intent().event_token,Destination.remote('https://remote.test/pub'),'a'*32,node.uid,'b'*64,1)
    monkeypatch.setattr(act,'_marker_path',lambda *args:path)
    monkeypatch.setattr(act,'load_manifest',lambda *args:manifest)
    remote=SimpleNamespace(op=tmp_path)
    assert act._marker_agrees(cast(Any,remote),mark)==((version==3)==(entries is not None))
