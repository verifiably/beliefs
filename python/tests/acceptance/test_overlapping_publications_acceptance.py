"""Cut 48: the 1b overlap on the certified tuple — a world holding its own records and
a publication that carries them (overlapping-publications design §1, §6–§8).

World *A* publishes P1 from its typed corpus; world *B* adopts P1 and publishes P2
carrying *A*'s records; *A* adopts P2 (the overlap), builds an epoch, publishes P3;
*B* adopts P3 keeping P1. Durable evidence beside the units; it adds no unit."""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from types import SimpleNamespace

import pytest
from authority import ACTOR
from dataset_fixtures import dataset_ref
from domain_facet_fixtures import kwargs_for, profile_with, seed_nodes, testing_contract
from fixtures_cut4 import path_for, raw_write
from nodes.core.node import new_uid
from profiles import biology
from test_publication_attribution_acceptance import (
    SETUP,
    _ops_tree,
    build,
    chain_tip,
    context_at,
    entries_at,
    publication_copy,
    publish,
    world_at,
)
from test_publication_attribution_acceptance import source as source  # noqa: PLC0414
from test_world_view import revise_in_place

from beliefs import belief, stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.corpus import lineage_snapshot
from beliefs.errors import AddressMapConflict, PublicationRefused, ResolutionRefused
from beliefs.evaluation import gather
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination
from beliefs.publication_arrival import admit_publication
from beliefs.publish import Published
from beliefs.root import open_world
from beliefs.view_query import parse_view_query
from beliefs.world import Fresh
from beliefs.world.live import evaluate_live_query
from beliefs.world.read import Resolved, current_epoch, reported_receipt, resolve_address, validate_receipt
from beliefs.world.selection import evaluate_query
from beliefs.world.view import open_world_view

_counter = count()
PROFILE = profile_with()
STAGING = compile_profile(
    shipped_base_contract(), [testing_contract(None), biology("fixture")], coordination=shipped_coordination(3)
)
"""The staging profile a publication of the typed records under coordination v3 derives."""
ASSESSMENT, RETRACTED = "assessment:a-1", "assessment:a-2"
ALL_KINDS = {
    "version": "science.view-query.v1",
    "clauses": [{"all": [{"kinds": ["dataset", "run", "proposition", "assessment", "verification", "retraction"]}]}],
}


def retracts(target, token: str, *, grounds=("verification:v-2",)):
    """A node-arm retraction of `target` whose grounds the publication closure holds."""
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    return stored.retraction_node(
        title=token,
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the record is invalid",
        grounds=grounds,
        actor=ACTOR,
        event_token=token,
    )


def context_over(s, world):
    """A v3 publishing context over `world` selecting every world kind, staging under
    the profile the typed records derive."""
    context = context_at(s, world, query=ALL_KINDS)
    context.profile = STAGING
    return context


def _published(outcome) -> Published:
    assert type(outcome) is Published, outcome
    return outcome


def world_a(s):
    """*A*: one typed corpus of the seeded evaluation records, R retracting a-2, its own
    world over it, and a v3 publishing context whose view selects every world kind."""
    cid, root, writer = s.corpus(profile=PROFILE, nodes=tuple(seed_nodes(axis="rows")))
    retraction = writer.retract(retracts(writer.read_view.get(RETRACTED), "r"))
    world = world_at(s, (root,))
    world.admit(root, provenance=Fresh())
    build(world)
    context = context_over(s, world)
    return SimpleNamespace(cid=cid, root=root, writer=writer, retraction=retraction, context=context)


def adopt(s, context, outcome):
    """A replica of `outcome`'s publication, restored beside `context`'s roots."""
    root, observers = publication_copy(s, context, outcome)
    return root, observers


def world_over(s, replicas, *, own=()):
    """A world admitting every `(root, observers)` publication in order, after `own`."""
    world = world_at(s, tuple(root for root, _ in replicas) + tuple(own))
    for root in own:
        world.admit(root, provenance=Fresh())
    for root, observers in replicas:
        admit_publication(world, root, observers)
    build(world)
    return world


def overlap(s):
    """The 1b overlap: *A* publishes P1, *B* adopts it and publishes P2, *A* adopts P2."""
    a = world_a(s)
    p1 = _published(publish(a.context))
    p1_root, p1_observers = adopt(s, a.context, p1)
    world_b = world_over(s, ((p1_root, p1_observers),))
    b = context_over(s, world_b)
    p2 = _published(publish(b))
    assert entries_at(b.dest / p2.corpus_id) == [
        [ref, p1.corpus_id, p1.marker] for ref in sorted(entry[0] for entry in entries_at(b.dest / p2.corpus_id))
    ]
    p2_root, p2_observers = adopt(s, b, p2)
    config = replace(a.context.setup_world.config, corpus_roots=(a.root, p2_root))
    setup_world = open_world(config, authority=SETUP)
    admit_publication(setup_world, p2_root, p2_observers)
    a.context.setup_world = setup_world
    a.context.world = open_world(config, authority=a.context.world.authority)
    return SimpleNamespace(
        a=a, p1=p1, p1_root=p1_root, p1_observers=p1_observers, b=b, p2=p2, p2_root=p2_root, p2_observers=p2_observers
    )


def _gather(view, acceptance=None):
    kwargs = kwargs_for(view, PROFILE)
    context = replace(
        kwargs["context"],
        snapshot=lineage_snapshot(view, (dataset_ref("d-a"), dataset_ref("d-b"))),
        producer_snapshot_identity=view.producer_snapshot_identity(),
        node_corpus={},
        pins={holder: kwargs["context"].pins["c1"] for holder in view.captured()},
    )
    return gather(
        view,
        "proposition:p",
        context=context,
        profile=PROFILE,
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
        acceptance=acceptance,
    )


def test_overlap_epoch_reads_once(source):
    o = overlap(source)
    world = o.a.context.setup_world
    published = build(world)
    holders = tuple(sorted((o.a.cid, o.p2.corpus_id)))
    view = open_world_view(world, published)
    assert view.holders_of(ASSESSMENT) == holders and view.corpus_of(ASSESSMENT) == holders[0]
    query = parse_view_query(ALL_KINDS)
    bound = evaluate_query(view, query)
    assert bound.selected.count(ASSESSMENT) == 1 and set(bound.contributing) == set(holders)
    live = evaluate_live_query(o.a.context.world, query)
    assert live.selected.count(ASSESSMENT) == 1 and set(live.contributing) == set(holders)
    located = resolve_address(world, published, ASSESSMENT)
    assert isinstance(located, Resolved)
    assert located.location.holders == holders and located.location.corpus_id == holders[0]
    identity = stored.assessment_value(view.get(ASSESSMENT), profile=PROFILE).identity()
    unfiltered = _gather(view)
    assert unfiltered.node_corpus[identity] == holders
    write_root_only = _gather(
        view, belief.AcceptancePolicy(lambda c, r: not (c == o.p2.corpus_id and r == ASSESSMENT), "accept A's root")
    )
    assert identity in {a.identity() for a in write_root_only.assessments}
    assert write_root_only.node_corpus[identity] == (o.a.cid,)
    assert write_root_only.acceptance is not None
    assert write_root_only.acceptance.excluded == ((o.p2.corpus_id, ASSESSMENT),)


def test_republish_attributes_own_and_earliest_origin(source):
    o = overlap(source)
    build(o.a.context.setup_world)
    p3 = _published(publish(o.a.context))
    assert entries_at(o.a.context.dest / p3.corpus_id) == []
    p3_root, p3_observers = adopt(source, o.a.context, p3)
    results = []
    for order in (
        ((o.p1_root, o.p1_observers), (p3_root, p3_observers)),
        ((p3_root, p3_observers), (o.p1_root, o.p1_observers)),
    ):
        world = world_over(source, order)
        b = context_over(source, world)
        outcome = _published(publish(b))
        results.append(entries_at(b.dest / outcome.corpus_id))
    assert results[0] == results[1]
    assert results[0] and all(row[1:] == [o.p1.corpus_id, o.p1.marker] for row in results[0])


def test_chain_gap_refuses_and_retention_resolves(source):
    o = overlap(source)
    build(o.a.context.setup_world)
    p3 = _published(publish(o.a.context))
    p7 = _published(publish(o.a.context))
    p3_root, p3_observers = adopt(source, o.a.context, p3)
    p7_root, p7_observers = adopt(source, o.a.context, p7)
    gap = context_over(source, world_over(source, ((o.p1_root, o.p1_observers), (p7_root, p7_observers))))
    before = chain_tip(gap), _ops_tree(gap)
    with pytest.raises(PublicationRefused) as refused:
        publish(gap)
    assert refused.value.reason == "attribution-ambiguous"
    assert refused.value.corpus_ids == tuple(sorted((o.p1.corpus_id, p7.corpus_id)))
    assert len(refused.value.refs) == 1
    assert refused.value.field == ",".join(
        f"{cid}:{marker}" for cid, marker in sorted(((o.p1.corpus_id, o.p1.marker), (p7.corpus_id, p7.marker)))
    )
    assert (chain_tip(gap), _ops_tree(gap)) == before
    kept = context_over(
        source, world_over(source, ((o.p1_root, o.p1_observers), (p3_root, p3_observers), (p7_root, p7_observers)))
    )
    outcome = _published(publish(kept))
    entries = entries_at(kept.dest / outcome.corpus_id)
    assert entries and all(row[1:] == [o.p1.corpus_id, o.p1.marker] for row in entries)


def test_differing_copy_refuses_and_consolidate_is_the_exit(source):
    o = overlap(source)
    world = o.a.context.setup_world
    retained = build(world)
    revise_in_place(o.a.root, ASSESSMENT)
    with pytest.raises(AddressMapConflict) as refused:
        build(world)
    assert refused.value.finding.code == "duplicate-location" and refused.value.finding.ref == ASSESSMENT
    with pytest.raises(ResolutionRefused):
        open_world_view(world, retained)
    assert current_epoch(world).packaging_identity == retained.packaging_identity


def test_counter_after_publishing_folds_once(source):
    o = overlap(source)
    retraction = o.a.retraction
    counter = o.a.writer.retract(retracts(retraction, "c"))
    world = o.a.context.setup_world
    published = build(world)
    view = open_world_view(world, published)
    assert view.holders_of(retraction.id) == tuple(sorted((o.a.cid, o.p2.corpus_id)))
    assert view.holders_of(counter.id) == (o.a.cid,)
    found = view.retraction_enumeration().found
    assert sorted(pair for pair in found if pair[0] == retraction.id) == [(retraction.id, RETRACTION_OVERTURNED)]
    assert dict(found)[counter.id] == RETRACTION_UPHELD
    assert validate_receipt(world, published, "retraction-enumeration").outcome == "validated"
    inputs = _gather(view)
    assert dict(inputs.retractions.found) == dict(found)
    restored = stored.assessment_value(view.get(RETRACTED), profile=PROFILE).identity()
    assert restored in {a.identity() for a in inputs.assessments}


@pytest.mark.parametrize("conflict", ("differing-content", "differing-address", "distinct-uids"))
def test_receipt_path_merge_refusals(source, conflict):
    o = overlap(source)
    world = o.a.context.setup_world
    published = build(world)
    assert validate_receipt(world, published, "producer").outcome == "validated"
    original = next(n for n in open_world_view(world, published).captured_records(o.a.cid) if n.id == ASSESSMENT)
    if conflict == "differing-content":
        copy, code, ref = original.model_copy(update={"title": "a-1, revised"}), "duplicate-location", ASSESSMENT
    elif conflict == "differing-address":
        copy, code, ref = original.model_copy(update={"id": "assessment:a-1-elsewhere"}), "uid-corruption", original.uid
        path_for(o.p2_root, ASSESSMENT).unlink()  # the carried copy moves under another address, one uid
    else:
        copy, code, ref = original.model_copy(update={"uid": new_uid()}), "duplicate-location", ASSESSMENT
    raw_write(o.p2_root, copy)
    outcome, finding = reported_receipt(world, published, "producer")
    assert outcome.outcome == "unresolvable" and code in outcome.detail
    assert finding is not None and (finding.code, finding.ref) == (code, ref)
    assert o.a.cid in finding.detail and o.p2.corpus_id in finding.detail
    assert validate_receipt(world, published, "producer") == outcome
