from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from authority import FULL
from coordination_fixtures import AT, content_for, raw_add, raw_coordination_node
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation
from test_belief import scenario as belief_scenario
from test_n2_cut7 import shipped_bindings

from beliefs import stored
from beliefs.belief import Belief, evaluate
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress, CoordinationRefused, coordination_revision
from beliefs.corpus import CoordinationResolver, ReadView, corpus_check
from beliefs.errors import (
    CoordinationKindUnsupported,
    ImportRefused,
    PredecessorMismatch,
    PredecessorNotStanding,
    ProjectNotResolvable,
    RecordAlreadyMinted,
    ValidationRefused,
)
from beliefs.profile import ProfileSpec
from beliefs.root import open_corpus
from beliefs.view_query import parse_view_query
from beliefs.world import derive, epoch, load_manifest


def writers(case: tuple[tuple[Path, Path], ProfileSpec]):
    roots, profile = case
    resolver = CoordinationResolver(dict.fromkeys(roots, profile))
    return roots, resolver, tuple(open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=profile) for root in roots)


def test_w11a_view_queries_reject_coordination_addresses():
    with pytest.raises(ValueError, match="world-tier"):
        parse_view_query(
            {
                "version": "science.view-query.v1",
                "clauses": [{"all": [{"addresses": ["coord:" + "a" * 32]}]}],
            }
        )


def test_w11b_coordination_fields_reject_world_addresses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused):
        writer.mint_coordination(
            "task",
            project=coordination_revision(project).address,
            content=content_for("task", depends=["dataset:x"]),
        )


def test_w12_renaming_a_project_preserves_every_subordinate_address(
    durable_coordination_roots, monkeypatch
):
    _roots, resolver, (writer, _other) = writers(durable_coordination_roots)
    values = iter(("a" * 32, "b" * 32, "c" * 32, "d" * 32, "e" * 32))
    monkeypatch.setattr("beliefs.corpus.secrets", SimpleNamespace(token_hex=lambda _: next(values)))
    project = writer.mint_coordination(
        "project", content=content_for("project", name="a" * 32)
    )
    project_address = coordination_revision(project).address
    task = writer.mint_coordination(
        "task", project=project_address, content=content_for("task")
    )
    renamed = writer.revise_coordination(
        "project",
        project_address,
        predecessors=(project.uid,),
        content=content_for("project", name="different"),
    )
    assert resolver.resolve(project_address) == renamed
    assert resolver.resolve(coordination_revision(task).address) == task
    assert coordination_revision(task).address.project == project_address.project


def test_w13_project_identity_is_independent_of_corpus_identity_and_mount(
    durable_coordination_roots,
):
    (left, right), profile = durable_coordination_roots
    left_resolver = CoordinationResolver({left: profile})
    writer = open_corpus(left, authority=FULL, coordination_resolver=left_resolver, profile=profile)
    first = writer.mint_coordination("project", content=content_for("project", name="one"))
    second = writer.mint_coordination("project", content=content_for("project", name="two"))
    left_manifest = load_manifest(left)
    right_manifest = load_manifest(right)
    assert coordination_revision(first).address.project != coordination_revision(second).address.project
    assert left_manifest.corpus_id == load_manifest(left).corpus_id
    Corpus(right).add(first.model_copy(deep=True))
    assert CoordinationResolver({right: profile}).resolve(coordination_revision(first).address) == first
    assert load_manifest(left).corpus_id == left_manifest.corpus_id
    assert load_manifest(right).corpus_id == right_manifest.corpus_id


def test_w17a_genesis_names_zero_predecessors(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    assert coordination_revision(project).predecessors == ()


def test_w17n_every_edit_is_a_new_whole_revision(durable_coordination_roots):
    _roots, resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project", name="old"))
    address = coordination_revision(project).address
    revised = writer.revise_coordination(
        "project",
        address,
        predecessors=(project.uid,),
        content=content_for("project", name="new"),
    )
    assert revised.uid != project.uid
    assert revised.relations[0].target == project.id
    assert resolver.resolve(address) == revised
    assert resolver.resolve(address.pinned(project.uid)) == project


def test_w17b_every_ordinary_door_refuses_coordination(durable_coordination_roots):
    (root, _), _profile = durable_coordination_roots
    writer = open_corpus(root, authority=FULL, profile=_profile)
    node = Node(id="note:old", kind="note", title="old")
    calls = (
        lambda: writer.add(node),
        lambda: writer.revise(node),
        lambda: writer.supersede(node, of=node.id),
        lambda: writer.retract(node),
    )
    for call in calls:
        with pytest.raises(CoordinationKindUnsupported):
            call()


def test_w17c_import_refuses_and_names_the_coordination_member(durable_coordination_roots):
    (root, _), _profile = durable_coordination_roots
    writer = open_corpus(root, authority=FULL, profile=_profile)
    member = Node(id="note:old", kind="note", title="old")
    with pytest.raises(ImportRefused) as caught:
        writer.import_bundle(
            [member], observer="o", instrument="i", opened_at=AT, closed_at=AT
        )
    assert caught.value.member == member.id


def test_w17d_coordination_door_refuses_world_kinds(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    for kind in stored.WORLD_KINDS:
        with pytest.raises(CoordinationKindUnsupported):
            writer.mint_coordination(kind, content=content_for("project"))


def test_w17e_reusing_an_existing_revision_pair_refuses_before_a_plan(
    durable_coordination_roots, monkeypatch
):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    values = iter(("a" * 32, "b" * 32, "a" * 32, "b" * 32))
    monkeypatch.setattr("beliefs.corpus.secrets", SimpleNamespace(token_hex=lambda _: next(values)))
    writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(RecordAlreadyMinted):
        writer.mint_coordination("project", content=content_for("project"))


def test_w17f_a_superseded_predecessor_refuses_at_commit(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    writer.revise_coordination(
        "project",
        address,
        predecessors=(first.uid,),
        content=content_for("project", name="next"),
    )
    with pytest.raises(PredecessorNotStanding):
        writer.revise_coordination(
            "project",
            address,
            predecessors=(first.uid,),
            content=content_for("project", name="stale"),
        )


def test_w17g_continuity_refuses_a_standing_predecessor_of_another_address_or_kind(
    durable_coordination_roots,
):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    other = writer.mint_coordination("project", content=content_for("project", name="other"))
    task = writer.mint_coordination(
        "task", project=coordination_revision(project).address, content=content_for("task")
    )
    for predecessor in (other.uid, task.uid):
        with pytest.raises(PredecessorMismatch):
            writer.revise_coordination(
                "project",
                coordination_revision(project).address,
                predecessors=(predecessor,),
                content=content_for("project"),
            )


def divergent(case):
    (left, right), profile = case
    left_writer = open_corpus(left, authority=FULL, coordination_resolver=CoordinationResolver({left: profile}), profile=profile)
    genesis = left_writer.mint_coordination("project", content=content_for("project"))
    Corpus(right).add(genesis.model_copy(deep=True))
    address = coordination_revision(genesis).address
    left_tip = left_writer.revise_coordination(
        "project",
        address,
        predecessors=(genesis.uid,),
        content=content_for("project", name="left"),
    )
    right_writer = open_corpus(right, authority=FULL, coordination_resolver=CoordinationResolver({right: profile}), profile=profile)
    right_tip = right_writer.revise_coordination(
        "project",
        address,
        predecessors=(genesis.uid,),
        content=content_for("project", name="right"),
    )
    resolver = CoordinationResolver({left: profile, right: profile})
    repair_writer = open_corpus(left, authority=FULL, coordination_resolver=resolver, profile=profile)
    return address, resolver, repair_writer, left_tip, right_tip


def test_w17h_siblings_refuse_with_sorted_tips_independent_of_mount_order(
    durable_coordination_roots,
):
    address, resolver, _writer, left_tip, right_tip = divergent(durable_coordination_roots)
    expected = CoordinationRefused("divergent-view", (left_tip.uid, right_tip.uid))
    assert resolver.resolve(address) == expected
    roots, profile = durable_coordination_roots
    assert CoordinationResolver({roots[1]: profile, roots[0]: profile}).resolve(address) == expected


def test_w17i_all_tip_repair_restores_resolution_and_retains_siblings(
    durable_coordination_roots,
):
    address, resolver, writer, left_tip, right_tip = divergent(durable_coordination_roots)
    repair = writer.revise_coordination(
        "project",
        address,
        predecessors=(right_tip.uid, left_tip.uid),
        content=content_for("project", name="repair"),
    )
    assert resolver.resolve(address) == repair
    assert resolver.resolve(address.pinned(left_tip.uid)) == left_tip
    assert resolver.resolve(address.pinned(right_tip.uid)) == right_tip


def test_w17j_a_raw_cycle_has_no_tip_and_an_audit_finding(durable_coordination_roots):
    root, profile = durable_coordination_roots[0][0], durable_coordination_roots[1]
    first = raw_coordination_node("project", "a" * 32, "b" * 32)
    second = raw_coordination_node("project", "a" * 32, "c" * 32)
    first.relations = [
        Relation(source=first.id, predicate=stored.SUPERSEDES, target=second.id)
    ]
    second.relations = [
        Relation(source=second.id, predicate=stored.SUPERSEDES, target=first.id)
    ]
    raw_add(root, first, second)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress("a" * 32)) is None
    assert any(
        finding.code == "coordination-supersession-cycle"
        for finding in corpus_check(open_corpus(root, authority=FULL, profile=profile).read_view)
    )


def test_w17k_a_malformed_facet_is_reported_and_excluded(durable_coordination_roots):
    root, profile = durable_coordination_roots[0][0], durable_coordination_roots[1]
    valid = raw_coordination_node("project", "a" * 32, "b" * 32)
    malformed = raw_coordination_node("project", "a" * 32, "c" * 32)
    malformed.facets[stored.COORDINATION_FACET]["project"] = "bad"
    raw_add(root, valid, malformed)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress("a" * 32)) == valid
    assert any(
        finding.code == "coordination-facet-malformed" and finding.ref == malformed.id
        for finding in corpus_check(open_corpus(root, authority=FULL, profile=profile).read_view)
    )


def test_w17l_a_subordinate_under_a_missing_project_refuses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination(
            "task", project=CoordinationAddress("a" * 32), content=content_for("task")
        )
    assert caught.value.tips == ()


def test_w17m_a_subordinate_under_a_divergent_project_names_the_project_tips(
    durable_coordination_roots,
):
    address, _resolver, writer, left_tip, right_tip = divergent(durable_coordination_roots)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=address, content=content_for("task"))
    assert caught.value.tips == tuple(sorted((left_tip.uid, right_tip.uid)))


def test_w18a_an_undeclared_kind_mints_nothing(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination(
            "publication",
            project=coordination_revision(project).address,
            content=content_for("decision"),
        )
    assert all(
        node.kind != "publication"
        for root in durable_coordination_roots[0]
        for node in ReadView.opened_at(root).iter_stored()
    )


def test_w18b_malformed_query_refuses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    query = {
        "version": "science.view-query.v1",
        "clauses": [{"all": []}],
    }
    with pytest.raises(ValidationRefused):
        writer.mint_coordination("project", content=content_for("project", query=query))


def test_w18e_an_unresolved_anchor_is_accepted(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    query = {
        "version": "science.view-query.v1",
        "clauses": [{"all": [{"addresses": ["dataset:not-held"]}]}],
    }
    accepted = writer.mint_coordination("project", content=content_for("project", query=query))
    assert accepted.kind == "project"


def test_w18i_coordination_moves_epoch_identity_not_world_maps_or_belief_input(
    durable_coordination_world,
):
    world, corpus_root, profile = durable_coordination_world
    bindings = shipped_bindings(world)
    corpus_id = load_manifest(corpus_root).corpus_id
    before = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
    resolver = CoordinationResolver({corpus_root: profile})
    open_corpus(corpus_root, authority=FULL, coordination_resolver=resolver, profile=profile).mint_coordination(
        "project", content=content_for("project")
    )
    after = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
    assert before.packaging_identity != after.packaging_identity
    for member in (
        "address-map.yaml",
        "producers-map.yaml",
        "retraction-discovery-map.yaml",
        "coreference-map.yaml",
        "producer-snapshot.yaml",
    ):
        assert before.members[member] == after.members[member]
    assert (
        before.documents["certification-receipt.yaml"]["inventory"]
        == after.documents["certification-receipt.yaml"]["inventory"]
    )
    before_snapshot = derive.producer_snapshot(
        yaml.safe_load(before.members["producer-snapshot.yaml"])
    ).identity()
    after_snapshot = derive.producer_snapshot(
        yaml.safe_load(after.members["producer-snapshot.yaml"])
    ).identity()
    assert before_snapshot == after_snapshot
    ordinary = belief_scenario()
    pin = ordinary["context"].pins["c1"]
    pinned = {
        "c1": CorpusPins(
            pin.science_contract,
            {
                **pin.domains,
                "coordination": "coordination:"
                + profile.activated_contracts["coordination"],
            },
        )
    }
    first = evaluate(
        **{
            **ordinary,
            "context": replace(
                ordinary["context"],
                producer_snapshot_identity=before_snapshot,
                pins=pinned,
            ),
        }
    )
    second = evaluate(
        **{
            **ordinary,
            "context": replace(
                ordinary["context"],
                producer_snapshot_identity=after_snapshot,
                pins=pinned,
            ),
        }
    )
    assert isinstance(first, Belief) and isinstance(second, Belief)
    assert first.belief_input_digest == second.belief_input_digest
