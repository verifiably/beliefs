"""Cut 47: restored own replicas, real scoped calls and frozen recovery."""

from dataclasses import replace

import pytest
from coordination_fixtures import coordination_profile
from durable_fixture import pinned
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.frontmatter import node_to_markdown
from test_publication_attribution_acceptance import (
    AUTHORITY,
    KINDS,
    REMOTE,
    SETUP,
    Crash,
    DirectoryTransport,
    _binding_files,
    _ops_tree,
    _publish_reports,
    build,
    carry_setup,
    chain_tip,
    context_at,
    crash,
    marker_at,
    markerless_replica,
    publish,
    resume,
    saved_marker,
    token_of_last_intent,
    unavailable,
)
from test_publication_attribution_acceptance import source as source  # noqa: PLC0414
from test_session_publish_door import _written, publishing_session
from test_world_view import damage

import beliefs.publish as act
from beliefs import stored
from beliefs.corpus import CoordinationResolver
from beliefs.errors import PublicationRefused
from beliefs.publication import BINDING_KIND
from beliefs.publish import Published, PublishRefused
from beliefs.publish_request import decode_request, decode_snapshot
from beliefs.root import open_corpus, open_world
from beliefs.world import Fresh, RegistryView, ReplicaOf, load_manifest
from beliefs.world.registry import admission_digest


def owned_context(source, *, version=3, query=KINDS, mount_replica=True, **replica_options):
    replica = markerless_replica(source, **replica_options)
    context = context_at(source, replica.world, version=version, query=query)
    config = replace(replica.world.config, corpus_roots=(replica.root, context.written))
    context.setup_world = open_world(config, authority=SETUP)
    context.setup_world.admit(context.written, provenance=Fresh())
    context.world = open_world(config, authority=AUTHORITY)
    context.config = config
    context.mounts = {context.written: context.profile}
    if mount_replica:
        context.mounts[replica.root] = replica.profile
    context.resolver = CoordinationResolver(context.mounts)
    context.writer = open_corpus(
        context.written, authority=AUTHORITY, profile=context.profile, coordination_resolver=context.resolver
    )
    context.written_id = load_manifest(context.written).corpus_id
    context.own = frozenset({replica.cid, context.written_id})
    context.replica = replica
    build(context.setup_world)
    return context


def admission_state(context):
    return tuple((row, admission_digest(row)) for row in context.world.registry().admissions)


def assert_closed(context, outcome) -> Published:
    assert type(outcome) is Published
    assert len(_binding_files(context)) == 1
    reports = _publish_reports(context, outcome.event_token)
    assert len(reports) == 1
    binding = reports[0]["entries"][-1]
    assert binding["kind"] == "publication-binding"
    assert binding["outcome"] == {
        "type": "bound",
        "binding": outcome.binding,
        "corpus_id": outcome.corpus_id,
        "marker": outcome.marker,
    }
    return outcome


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
def test_owned_replica_preview_and_publish(source, version):
    context = owned_context(source, version=version)
    before = admission_state(context)
    preview = act.publication_preview(
        context.world,
        context.resolver,
        context.view,
        own_pins=load_manifest(context.written).profile,
        own_corpora=context.own,
    )
    assert preview.contributing == (context.replica.cid,)
    assert preview.selected == (context.replica.nodes[0].id,)
    outcome = publish(context, own_corpora=context.own)
    outcome = assert_closed(context, outcome)
    op = context.ops / "publish" / outcome.event_token
    snapshot = decode_snapshot((op / "selection.v1").read_bytes())
    request = decode_request((op / "request.v1").read_bytes())
    assert (snapshot.records, snapshot.attributions) == (preview.records, preview.attributions)
    assert snapshot.attributions == (None if version == 2 else ())
    assert (request.view, request.epoch, request.world_id, request.pins) == (
        preview.view,
        preview.epoch,
        preview.world_id,
        preview.pins,
    )
    assert admission_state(context) == before
    assert any(
        row.corpus_id == context.replica.cid and row.provenance == ReplicaOf(context.replica.cid) for row, _ in before
    )
    assert load_manifest(context.replica.root).corpus_id == load_manifest(context.replica.original).corpus_id


@pytest.mark.parametrize("case", ["undeclared-v2", "undeclared-v3", "marker", "missing", "closure", "pins", "damage"])
def test_owned_replica_refusal_preserves_intent_and_ops(source, monkeypatch, case):
    if case == "marker":
        outcome, carrier, context, _, _ = carry_setup(source)
        own = frozenset({outcome.corpus_id})
        assert marker_at(carrier).uid == outcome.marker
    elif case == "closure":
        dataset = stored.dataset_node(title="closure-member", resources=pinned())
        run = stored.run_node("owned-run", title="owned-run", spec="s", produces=[dataset.id])
        query = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["run"]}]}]}
        context = owned_context(source, nodes=(dataset, run), query=query)
        own = context.own
    elif case == "pins":
        context = owned_context(source, version=2, profile=coordination_profile(None, version=3))
        own = context.own
    else:
        context = owned_context(source, version=2 if case == "undeclared-v2" else 3)
        own = frozenset() if case.startswith("undeclared") else context.own
    if case == "missing":
        registry = context.world.registry()
        monkeypatch.setattr(
            context.world,
            "registry",
            lambda: RegistryView(
                tuple(row for row in registry.admissions if row.corpus_id != context.replica.cid), registry.statuses
            ),
        )
    if case == "damage":
        damage(context.replica.root, "parse-error")
    before = chain_tip(context), _ops_tree(context)
    if case == "damage":
        with pytest.raises(NodesValidationError, match="invalid frontmatter YAML"):
            publish(context, own_corpora=own)
    else:
        with pytest.raises(PublicationRefused) as caught:
            publish(context, own_corpora=own)
        assert (
            caught.value.reason
            == {
                "undeclared-v2": "attribution-contract-unpinned",
                "undeclared-v3": "attribution-source-invalid",
                "marker": "attribution-own-source-invalid",
                "missing": "attribution-holder-unregistered",
                "closure": "closure-incomplete",
                "pins": "pins-disagree",
            }[case]
        )
    assert (chain_tip(context), _ops_tree(context)) == before


def test_owned_replica_scoped_publish(source):
    context = owned_context(source, version=2)
    before = admission_state(context)
    session, writer = publishing_session(context)
    try:
        outcome = writer.publish(
            view=context.view,
            destination=context.destination,
            operations_root=context.ops,
            staging_profile=context.profile,
            own_corpora=context.own,
        )
        outcome = assert_closed(context, outcome)
        (line,) = session.invocation_acts("A")
        assert set(line.record_ids) == _written(context, BINDING_KIND) | _written(context, "act-report")
        assert outcome.binding in {uid for uid, _ in line.record_ids}
        assert admission_state(context) == before
        session.close_invocation("A", {"done": [list(pair) for pair in line.record_ids]})
    finally:
        session.close()


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
@pytest.mark.parametrize("mount_replica", [False, True], ids=["writer-only", "source-anchored"])
def test_owned_replica_local_resume(source, monkeypatch, version, mount_replica):
    context = owned_context(source, version=version, mount_replica=mount_replica)
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        publish(context, own_corpora=context.own)
    monkeypatch.undo()
    token = token_of_last_intent(context)
    _, snapshot, wanted = saved_marker(context, token)
    assert snapshot.attributions == (None if version == 2 else ())
    context.own = frozenset()
    context.resolver = CoordinationResolver({context.written: context.profile})
    unavailable(monkeypatch, context, context.replica.root)
    outcome = resume(context, token)
    monkeypatch.undo()
    if mount_replica:
        assert outcome == PublishRefused(token, "evidence-refused")
        (report,) = _publish_reports(context, token)
        assert report["entries"][-1]["outcome"]["reason"] == "mounts-changed"
        assert not _binding_files(context)
        return
    outcome = assert_closed(context, outcome)
    assert node_to_markdown(marker_at(context.dest / outcome.corpus_id)) == node_to_markdown(wanted)


def test_owned_replica_remote_mark_only_resume(source, monkeypatch):
    context = owned_context(source, mount_replica=False)
    remote = source.base / "owned-remote"
    remote.mkdir()
    context.destination = REMOTE
    context.transport = DirectoryTransport(remote)
    crash(monkeypatch, "_mark")
    with pytest.raises(Crash):
        publish(context, own_corpora=context.own)
    monkeypatch.undo()
    token = token_of_last_intent(context)
    op, snapshot, wanted = saved_marker(context, token)
    assert snapshot.attributions == ()
    (op / "selection.v1").unlink()
    (op / "request.v1").unlink()
    context.own = frozenset()
    context.resolver = CoordinationResolver({context.written: context.profile})
    unavailable(monkeypatch, context, context.replica.root)
    outcome = resume(context, token)
    monkeypatch.undo()
    outcome = assert_closed(context, outcome)
    assert node_to_markdown(marker_at(op / "export" / outcome.corpus_id)) == node_to_markdown(wanted)
    assert context.transport.pushes == 1
