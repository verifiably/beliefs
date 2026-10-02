"""Cut 46: real carried publications, frozen retries and source integrity."""
from __future__ import annotations

import shutil
from dataclasses import replace
from itertools import count
from types import SimpleNamespace

import pytest
from coordination_fixtures import content_for, coordination_profile
from durable_fixture import pinned
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from profiles import pins_for
from test_publish_act_acceptance import (
    AUTHORITY,
    KINDS,
    SETUP,
    Clock,
    Crash,
    _binding_files,
    _ops_tree,
    _publish_reports,
    chain_tip,
    crash,
    run,
    setup_writer,
    token_of_last_intent,
)
from test_publish_act_acceptance import (
    source as source,  # noqa: PLC0414 — explicit pytest fixture re-export
)
from test_publish_remote_acceptance import REMOTE, writable
from test_world_receipts import hold_shipped
from transport_fake import DirectoryTransport

from beliefs import publish as act
from beliefs import stored
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.errors import ManifestAlreadyPresent, PublicationRefused, SelectionRefused
from beliefs.intents.publish import Destination
from beliefs.publication import MARKER_KIND, marker_consistent, marker_record
from beliefs.publication_arrival import admit_publication
from beliefs.publication_doors import attempt_reading
from beliefs.publish import Published, PublishRefused
from beliefs.publish_request import decode_mark, decode_request, decode_snapshot, encode_snapshot
from beliefs.root import (
    admit_arrival,
    export_head_artifact,
    init_world_root,
    moment_seam,
    open_corpus,
    open_world,
    replicate_root,
    restore_root,
)
from beliefs.view_query import stored_query
from beliefs.world import Fresh, ReplicaOf, WorldConfig, epoch, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.world.read import current_epoch
from beliefs.world.selection import evaluate_query
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view

_counter = count()
V3 = coordination_profile(None, version=3)


def marker_at(root):
    (node,) = (node for node in ReadView.opened_at(root).iter_stored() if node.kind == MARKER_KIND)
    return node


def entries_at(root):
    return marker_at(root).facets['coordination']['published_from']['attributions']


def publication_copy(s, context, outcome):
    """Travel only root bytes and its external artifact, then restore the raw copy."""
    assert type(outcome) is Published
    original = context.dest / outcome.corpus_id
    copy = s.base / f'carried-{next(_counter)}'
    s.roots.append(copy)
    shutil.copytree(original, copy)
    data = (context.dest / f'{outcome.corpus_id}.head-artifact.v1').read_bytes()
    observers = ObserverSet((ArtifactCarrier.from_bytes(data),))
    assert restore_root(copy, CorpusSubject(outcome.corpus_id), observers, authority=SETUP).outcome == 'validated'
    return copy, observers


def world_at(s, roots):
    root = s.base / f'world-{next(_counter)}'
    s.roots.append(root)
    config = WorldConfig(root, 'c'*32, tuple(roots))
    init_world_root(config, authority=SETUP)
    return open_world(config, authority=SETUP)


def build(world):
    coverage = frozenset(record.corpus_id for record in world.registry().admissions)
    return epoch.build_epoch(world, coverage=coverage, bindings=hold_shipped(world))


def context_at(s, world, *, version=3, query=KINDS):
    profile = coordination_profile(None, version=version)
    _, written, _ = s.corpus(profile=profile)
    resolver = CoordinationResolver({written: profile})
    setup = open_corpus(written, authority=SETUP, profile=profile, coordination_resolver=resolver)
    project = setup.mint_coordination('project', content=content_for('project', query=query))
    ops, dest = s.base / f'ops-{next(_counter)}', s.base / f'dest-{next(_counter)}'
    ops.mkdir(); dest.mkdir()
    return SimpleNamespace(base=s.base, roots=s.roots, written=written,
        writer=open_corpus(written, authority=AUTHORITY, profile=profile, coordination_resolver=resolver),
        resolver=resolver, view=coordination_revision(project).address, profile=profile,
        world=open_world(world.config, authority=AUTHORITY), setup_world=world,
        ops=ops, dest=dest, destination=Destination.local(str(dest)), transport=None)


def publish(context):
    return act.publish(context.writer, context.resolver, context.world, view=context.view,
        destination=context.destination, operations_root=context.ops, staging_profile=context.profile,
        clock=Clock(), seam=moment_seam(), transport=context.transport)


def resume(context, token):
    fresh = open_corpus(context.written, authority=AUTHORITY, profile=context.profile, coordination_resolver=context.resolver)
    return act.resume_publish(fresh, context.resolver, event_token=token, operations_root=context.ops,
        staging_profile=context.profile, clock=Clock(), seam=moment_seam(), transport=context.transport)


def carry_setup(s, *, own=()):
    a = run(s)
    assert type(a) is Published
    root, observers = publication_copy(s, s, a)
    roots = [root]
    own_writer = None
    if own:
        _, own_root, own_writer = s.corpus(nodes=own)
        roots.append(own_root)
    world = world_at(s, roots)
    admit_publication(world, root, observers)
    if own_writer is not None: world.admit(own_writer.root, provenance=Fresh())
    build(world)
    b = context_at(s, world)
    carried = tuple(sorted(node.id for node in ReadView.opened_at(root).iter_stored() if node.kind != MARKER_KIND))
    expected = [[ref, a.corpus_id, a.marker] for ref in carried]
    return a, root, b, expected, own_writer


def unavailable(monkeypatch, context, root):
    shutil.rmtree(root)
    def forbidden(*args, **kwargs): pytest.fail('retry consulted origin inputs')
    monkeypatch.setattr(act, '_selected_attributions', forbidden)
    monkeypatch.setattr(act, 'open_world_view', forbidden)
    monkeypatch.setattr(act, 'current_epoch', forbidden)
    monkeypatch.setattr(context.world, 'registry', forbidden)


def saved_marker(context, token):
    op = context.ops / 'publish' / token
    snapshot = decode_snapshot((op/'selection.v1').read_bytes())
    request = decode_request((op/'request.v1').read_bytes())
    reading = attempt_reading(context.writer, token, moment_seam())
    assert reading is not None
    marker = marker_record(reading.opened.intent, world_id=request.world_id, epoch=request.epoch,
        selection=tuple(ref for ref,_ in snapshot.records), attributions=snapshot.attributions)
    return op, snapshot, marker


def test_first_carry_durably(source):
    a, carrier, b, expected, _ = carry_setup(source)
    view = open_world_view(b.world, current_epoch(b.world))
    assert any(report.unmapped and report.captured_state == report.published_state for report in view.drift())
    outcome = publish(b)
    assert type(outcome) is Published
    assert entries_at(b.dest / outcome.corpus_id) == expected
    assert expected and all(row[1:] == [a.corpus_id, a.marker] for row in expected)
    assert carrier.exists()


def test_forwarding_without_origin_durably(source):
    own = stored.dataset_node(title='b-owned', resources=pinned())
    a, _, b, expected, _ = carry_setup(source, own=(own,))
    b_outcome = publish(b)
    assert type(b_outcome) is Published
    assert entries_at(b.dest / b_outcome.corpus_id) == expected
    root, observers = publication_copy(source, b, b_outcome)
    world = world_at(source, (root,))
    admit_publication(world, root, observers); build(world)
    c = context_at(source, world)
    outcome = publish(c)
    assert type(outcome) is Published
    wanted = sorted([*expected, [own.id, b_outcome.corpus_id, b_outcome.marker]])
    assert entries_at(c.dest / outcome.corpus_id) == wanted
    assert any(row[1] == a.corpus_id for row in wanted)
    assert {r.corpus_id for r in world.registry().admissions} == {b_outcome.corpus_id}


def test_two_carriers_and_selection_durably(source):
    a = run(source)
    assert type(a) is Published
    ar, ao = publication_copy(source, source, a)
    d1 = stored.dataset_node(title='d-one', resources=pinned()); d1.deprecated_ids=['dataset:carried-old']
    d2 = stored.dataset_node(title='d-two', resources=pinned())
    r1 = stored.run_node('d-one', title='d-one', spec='s', produces=[d1.id])
    r2 = stored.run_node('d-two', title='d-two', spec='s', produces=[d2.id])
    _, dr, _ = source.corpus(nodes=(d1,d2,r1,r2))
    dw = world_at(source,(dr,)); dw.admit(dr, provenance=Fresh()); build(dw)
    d = context_at(source,dw,version=2); d_outcome=publish(d)
    assert type(d_outcome) is Published
    dc, do = publication_copy(source,d,d_outcome)
    world = world_at(source,(ar,dc))
    admit_publication(world,ar,ao); admit_publication(world,dc,do); build(world)
    a_run=ReadView.opened_at(ar).get('run:r-a')
    a_dataset=next(edge.target for edge in a_run.relations if edge.predicate=='produces')
    selected=tuple(sorted((a_run.id,a_dataset,d1.id,r1.id)))
    query={'version':'science.view-query.v1','clauses':[{'all':[{'addresses':[a_run.id,a_dataset,'dataset:carried-old',r1.id]}]}]}
    old=context_at(source,world,version=2,query=query)
    before=chain_tip(old),_ops_tree(old)
    with pytest.raises(PublicationRefused) as refused: publish(old)
    assert refused.value.reason=='attribution-contract-unpinned'
    assert refused.value.corpus_ids==tuple(sorted((a.corpus_id,d_outcome.corpus_id)))
    assert (chain_tip(old),_ops_tree(old))==before
    b=context_at(source,world,query=query)
    outcome=publish(b); assert type(outcome) is Published
    expected=sorted([[ref,a.corpus_id,a.marker] for ref in (a_run.id,a_dataset)]+[[ref,d_outcome.corpus_id,d_outcome.marker] for ref in (d1.id,r1.id)])
    assert entries_at(b.dest/outcome.corpus_id)==expected
    assert tuple(row[0] for row in expected)==selected and 'dataset:carried-old' not in selected
    assert d2.id not in selected and r2.id not in selected


@pytest.mark.parametrize('version',[2,3])
def test_markerless_replica_durably(source,version):
    node=stored.run_node('restored-own', title='restored-own', spec='s', produces=[])
    cid, original, _=source.corpus(nodes=(node,))
    origin_world=world_at(source,(original,)); origin_world.admit(original,provenance=Fresh())
    artifact=export_head_artifact(origin_world,CorpusSubject(cid))
    copy=source.base/f'markerless-{next(_counter)}'; source.roots.append(copy)
    replicate_root(original,copy,authority=SETUP)
    observers=ObserverSet((ArtifactCarrier.from_bytes(artifact),))
    assert restore_root(copy,CorpusSubject(cid),observers,authority=SETUP).outcome=='validated'
    world=world_at(source,(copy,))  # original cid is deliberately not admitted here
    admit_arrival(world,copy,ReplicaOf(cid),observers); build(world)
    context=context_at(source,world,version=version)
    selected=evaluate_query(open_world_view(context.world,current_epoch(context.world)),stored_query(context.resolver.resolve(context.view)))
    assert selected.complete and selected.selected==(node.id,)
    before=chain_tip(context),_ops_tree(context)
    with pytest.raises(PublicationRefused) as refused: publish(context)
    assert refused.value.reason==('attribution-contract-unpinned' if version==2 else 'attribution-source-invalid')
    assert refused.value.corpus_ids==(cid,)
    if version==3: assert refused.value.field=='marker-absent'
    assert (chain_tip(context),_ops_tree(context))==before


@pytest.mark.parametrize('scenario',['retired','drift','unmapped'])
def test_retirement_after_capture_durably(source,monkeypatch,scenario):
    own=stored.run_node('own-retirement',title='own-retirement',spec='s',produces=[])
    a, _, b, expected, own_writer=carry_setup(source,own=(own,))
    observed=[]
    original=act.open_world_view
    def capture(world,published):
        read=original(world,published)
        if scenario=='retired':
            b.setup_world.retire(a.corpus_id)
            assert not world.status(a.corpus_id).live
        elif scenario=='unmapped':
            assert any(report.unmapped and report.captured_state==report.published_state for report in read.drift())
        return read
    monkeypatch.setattr(act,'open_world_view',capture)
    prepare=act._selected_attributions
    def scanned(read,registry,refs,pin):
        if scenario=='retired':
            assert any(status.corpus_id==a.corpus_id and status.status=='retired' for status in registry.statuses)
            observed.append('retired')
        return prepare(read,registry,refs,pin)
    monkeypatch.setattr(act,'_selected_attributions',scanned)
    if scenario=='drift':
        assert own_writer is not None
        own_writer.add(stored.run_node('actual-drift',title='actual-drift',spec='s',produces=[]))
        with pytest.raises(SelectionRefused) as refused: publish(b)
        assert refused.value.reason=='corpus-drifted' and not observed
    else:
        outcome=publish(b); assert type(outcome) is Published
        assert entries_at(b.dest/outcome.corpus_id)==expected
        assert observed==(['retired'] if scenario=='retired' else [])


def test_local_retry_frozen_durably(source,monkeypatch):
    _, carrier, b, expected, _=carry_setup(source)
    stage=CorpusWriter._stage_record
    def partial(writer,text):
        stage(writer,text)
        raise Crash('partial-population')
    monkeypatch.setattr(CorpusWriter,'_stage_record',partial)
    with pytest.raises(Crash): publish(b)
    monkeypatch.undo()
    token=token_of_last_intent(b)
    _, snapshot, wanted=saved_marker(b,token)
    assert snapshot.attributions is not None
    assert [list(row) for row in snapshot.attributions]==expected
    unavailable(monkeypatch,b,carrier)
    outcome=resume(b,token); assert type(outcome) is Published
    assert node_to_markdown(marker_at(b.dest/outcome.corpus_id))==node_to_markdown(wanted)
    assert entries_at(b.dest/outcome.corpus_id)==expected
    assert len(_binding_files(b))==1 and len(_publish_reports(b,token))==1


def test_remote_retry_export_only_durably(source,monkeypatch):
    _, carrier, b, expected, _=carry_setup(source)
    remote=source.base/f'remote-{next(_counter)}'; remote.mkdir()
    b.destination=REMOTE; b.transport=DirectoryTransport(remote)
    crash(monkeypatch,'_mark')
    with pytest.raises(Crash): publish(b)
    monkeypatch.undo()
    token=token_of_last_intent(b)
    op,snapshot,wanted=saved_marker(b,token)
    assert snapshot.attributions is not None
    assert [list(row) for row in snapshot.attributions]==expected
    mark=decode_mark((op/'transport.v1').read_bytes())
    exported=op/'export'/mark.corpus_id
    assert node_to_markdown(marker_at(exported))==node_to_markdown(wanted)
    (op/'selection.v1').unlink(); (op/'request.v1').unlink()
    unavailable(monkeypatch,b,carrier)
    outcome=resume(b,token); assert type(outcome) is Published
    copied, artifact=b.transport.materialize(REMOTE,outcome.corpus_id,source.base/f'received-{next(_counter)}')
    source.roots.append(copied)
    assert restore_root(copied,CorpusSubject(outcome.corpus_id),ObserverSet((ArtifactCarrier.from_bytes(artifact),)),authority=SETUP).outcome=='validated'
    assert entries_at(copied)==expected and node_to_markdown(marker_at(copied))==node_to_markdown(wanted)
    assert len(_binding_files(b))==1 and len(_publish_reports(b,token))==1


def test_new_roots_and_arrival_releases_durably(source):
    with pytest.raises(ManifestAlreadyPresent): setup_writer(source).adopt_manifest(profile=pins_for(V3))
    assert load_manifest(source.written).profile.domains['coordination']==pins_for(source.writer.profile).domains['coordination']
    _,_,b,expected,_=carry_setup(source)
    outcome=publish(b); assert type(outcome) is Published
    root,observers=publication_copy(source,b,outcome)
    world=world_at(source,(root,)); admitted,_=admit_publication(world,root,observers)
    assert admitted.corpus_id==outcome.corpus_id and load_manifest(root).profile==pins_for(V3)
    assert entries_at(root)==expected


@pytest.mark.parametrize('damage',['snapshot','staged-marker'])
def test_snapshot_and_staged_marker_tamper_durably(source,monkeypatch,damage):
    _,_,b,expected,_=carry_setup(source)
    crash(monkeypatch,'_initialize' if damage=='snapshot' else '_populate',before=damage=='snapshot')
    with pytest.raises(Crash): publish(b)
    monkeypatch.undo()
    token=token_of_last_intent(b)
    op,snapshot,_=saved_marker(b,token)
    assert snapshot.attributions is not None
    assert [list(row) for row in snapshot.attributions]==expected
    if damage=='snapshot':
        rows=list(snapshot.attributions); rows[0]=(rows[0][0],'f'*32,rows[0][2])
        path=op/'selection.v1'; path.chmod(0o644)
        path.write_bytes(encode_snapshot(replace(snapshot,attributions=tuple(rows))))
    else:
        node=marker_at(op/'staging'); original_id=node.id
        node.facets['coordination']['published_from']['attributions'][0][1]='f'*32
        assert node.id==original_id and marker_consistent(node)
        path=op/'staging'/path_for_node_id(node.id); path.chmod(0o644); path.write_text(node_to_markdown(node))
    assert resume(b,token)==PublishRefused(token,'request-corrupt' if damage=='snapshot' else 'staging-corrupt')
    (report,)=_publish_reports(b,token)
    assert report['entries'][-1]['outcome']['reason']==('snapshot-mismatch' if damage=='snapshot' else 'marker')
    assert _binding_files(b)==[]


def test_remote_export_origin_tamper_durably(source,monkeypatch):
    _,_,b,expected,_=carry_setup(source)
    remote=source.base/f'remote-{next(_counter)}'; remote.mkdir()
    b.destination=REMOTE; b.transport=DirectoryTransport(remote)
    crash(monkeypatch,'_mark')
    with pytest.raises(Crash): publish(b)
    monkeypatch.undo()
    token=token_of_last_intent(b); op=b.ops/'publish'/token
    mark=decode_mark((op/'transport.v1').read_bytes()); exported=op/'export'/mark.corpus_id
    node=marker_at(exported); assert entries_at(exported)==expected
    node.facets['coordination']['published_from']['attributions'][0][1]='f'*32
    assert marker_consistent(node)
    writable(exported); (exported/path_for_node_id(node.id)).write_text(node_to_markdown(node))
    assert resume(b,token)==PublishRefused(token,'transport-incomplete')
    (report,)=_publish_reports(b,token)
    assert report['entries'][-1]['outcome']['reason']=='export-damaged'
    assert b.transport.pushes==0 and _binding_files(b)==[]
