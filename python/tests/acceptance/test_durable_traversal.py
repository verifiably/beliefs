"""S1, S1a, S5 and R23 over one durable corpus root.

The records were minted through the add path and are walked back out of the
store after reload. That is the whole difference from the portable traversal
tests, and it is the difference cut 4 selects these arms for: the fixture is
now a corpus on disk rather than a value set in memory.
"""

from __future__ import annotations

import pytest
from durable_fixture import (
    CHAIN,
    CITES,
    CYCLE,
    DANGLING_SOURCE,
    DERIVED,
    DIAMOND_BOTTOM,
    DIAMOND_TOP,
    LINEAGE_ABSENT_ANCESTOR,
    LINEAGE_ABSENT_RUN,
    LINEAGE_CONFLICT,
    LINEAGE_CYCLE,
    LINEAGE_LEAF,
    LINEAGE_LEFT,
    LINEAGE_MIDDLE,
    LINEAGE_RIGHT,
    LINEAGE_ROOT,
    RAW,
    RENAMED,
    RUN,
    SPEC,
    UNDIRECTED,
    UNRELATED,
    basis,
    pinned,
    route,
)
from fixtures_cut4 import raw_write, reopen

from beliefs import stored
from beliefs.corpus import LineageAdjacency, RelationAdjacency, derived_from, lineage_snapshot
from beliefs.lineage import certify
from beliefs.traversal import LineageEntry, RelationEntry, closure


def relation_walk(view, start, predicate=CITES, direction="outbound"):
    return closure(start, RelationAdjacency(view, predicate, direction))


@pytest.fixture()
def view(minted_corpus):
    """A fresh facade over the minted store — the read this cut runs."""
    return reopen(minted_corpus)


class TestS1TheRelationFixtureWalkedOutOfTheStore:
    def test_a_chain_minted_through_the_add_path_walks_transitively(self, view):
        first, second, third = CHAIN
        assert {second, third} <= set(relation_walk(view, first).reached)

    def test_a_diamond_reaches_its_bottom_once(self, view):
        reached = relation_walk(view, DIAMOND_TOP).reached
        assert reached.count(DIAMOND_BOTTOM) == 1
        assert set(reached) == {"note:diamond-left", "note:diamond-right", DIAMOND_BOTTOM}

    def test_a_cycle_terminates(self, view):
        first, second = CYCLE
        assert relation_walk(view, first).reached == (second,)

    def test_an_unrelated_predicate_is_not_followed(self, view):
        assert UNRELATED not in relation_walk(view, CHAIN[0]).reached

    def test_a_deprecated_ref_resolves_to_the_live_node(self, view):
        assert RENAMED in relation_walk(view, CHAIN[0]).reached

    def test_a_dangling_target_is_reported_with_its_source_and_position(self, view):
        # The dangling relation is stored **second**, so a report that lost the
        # position could not say which of the source's edges failed.
        assert relation_walk(view, DANGLING_SOURCE).unresolved == (
            RelationEntry(source=DANGLING_SOURCE, position=1, predicate=CITES, target="note:gone"),
        )

    def test_an_undirected_relation_is_reached_from_its_stored_source(self, view):
        source, target = UNDIRECTED
        assert relation_walk(view, source).reached == (target,)

    def test_an_undirected_relation_is_not_reached_from_its_stored_target(self, view):
        _, target = UNDIRECTED
        assert relation_walk(view, target).reached == ()

    def test_membership_traversal_agrees_with_what_the_container_stores(self, durable_writer, durable_root):
        # Corpus-local membership, walked as relations: what the walk reaches is
        # exactly what the container's own facet lists, so the two readings of
        # one structure agree rather than diverging silently.
        container = stored.dataset_node("cohort", title="cohort", resources=pinned())
        members = ["dataset:member-a", "dataset:member-b"]
        container.facets["membership"] = {"members": members}
        stored.stamp_semantic_identity(container)
        for member in members:
            container.relations.append(
                stored.Relation(source=container.id, predicate=stored.MEMBER_OF, target=member)
            )
            durable_writer.add(stored.dataset_node(member.split(":", 1)[1], title=member, resources=pinned()))
        durable_writer.add(container)
        view = reopen(durable_root)
        walked = closure(container.id, RelationAdjacency(view, stored.MEMBER_OF, "outbound")).reached
        assert sorted(walked) == sorted(members)
        assert sorted(view.get(container.id).facets["membership"]["members"]) == sorted(walked)


class TestS1aTheLineageFixtureWalkedAsAFacet:
    def test_a_basis_chain_walks_transitively(self, view):
        # Compared as an ordered tuple: the walk promises a sorted reached set,
        # and a comparison over sets could not see that promise broken.
        assert closure(LINEAGE_LEAF, LineageAdjacency(view)).reached == (LINEAGE_MIDDLE, LINEAGE_ROOT)

    def test_a_conflict_basis_yields_every_route(self, view):
        reached = closure(LINEAGE_CONFLICT, LineageAdjacency(view)).reached
        assert {LINEAGE_LEFT, LINEAGE_RIGHT} <= set(reached)

    def test_a_diamond_reaches_its_shared_ancestor_once(self, view):
        reached = closure(LINEAGE_CONFLICT, LineageAdjacency(view)).reached
        assert reached.count(LINEAGE_ROOT) == 1

    def test_a_cycle_terminates(self, view):
        first, second = LINEAGE_CYCLE
        assert closure(first, LineageAdjacency(view)).reached == (second,)

    def test_an_unresolvable_ancestor_is_reported_as_an_ancestor(self, view):
        assert closure(LINEAGE_ABSENT_ANCESTOR, LineageAdjacency(view)).unresolved == (
            LineageEntry(dataset=LINEAGE_ABSENT_ANCESTOR, route=0, position="ancestor", target="dataset:absent"),
        )

    def test_an_unresolvable_producing_run_is_told_apart_from_it(self, view):
        walk = closure(LINEAGE_ABSENT_RUN, LineageAdjacency(view))
        assert walk.unresolved == (
            LineageEntry(dataset=LINEAGE_ABSENT_RUN, route=0, position="run", target="run:absent"),
        )
        assert walk.reached == (LINEAGE_ROOT,)  # the ancestor still resolves

    def test_the_lineage_adapter_takes_no_predicate_and_no_direction(self):
        import inspect

        assert set(inspect.signature(LineageAdjacency.__init__).parameters) == {"self", "view"}

    def test_one_algorithm_serves_both_adapters_over_this_store(self, view):
        # Cycle-safety and start-exclusion, certified once: the same function
        # walks the relation cycle and the lineage cycle.
        assert closure(CYCLE[0], RelationAdjacency(view, CITES, "outbound")).reached == (CYCLE[1],)
        assert closure(LINEAGE_CYCLE[0], LineageAdjacency(view)).reached == (LINEAGE_CYCLE[1],)


class TestS5TheWalkThatProducesTheSnapshot:
    def test_the_inspected_set_is_the_observed_root_plus_its_closure(self, view):
        snapshot = lineage_snapshot(view, [LINEAGE_LEAF])
        assert set(snapshot.producers) == {LINEAGE_LEAF, LINEAGE_MIDDLE, LINEAGE_ROOT}

    def test_a_conflict_tag_short_circuits_on_the_tag_alone(self, view):
        certification = certify(lineage_snapshot(view, [LINEAGE_CONFLICT]), (LINEAGE_CONFLICT,), (LINEAGE_ROOT,))
        assert certification.state == "not-certified"
        assert certification.findings == ("lineage-divergent",)

    def test_an_unresolvable_basis_entry_yields_incomplete_and_no_certificate(self, view):
        certification = certify(
            lineage_snapshot(view, [LINEAGE_ABSENT_ANCESTOR]), (LINEAGE_ABSENT_ANCESTOR,), (LINEAGE_ROOT,)
        )
        assert certification.state == "not-certified"
        assert certification.findings == ("lineage-incomplete",)

    def test_an_unresolvable_entry_with_an_empty_closure_still_yields_incomplete(self, view):
        certification = certify(
            lineage_snapshot(view, [LINEAGE_ABSENT_RUN]), (LINEAGE_ABSENT_RUN,), (LINEAGE_ABSENT_RUN,)
        )
        assert "lineage-incomplete" in certification.findings

    def test_two_roots_meeting_at_one_ancestor_certify_shared_source(self, view):
        snapshot = lineage_snapshot(view, [LINEAGE_LEFT, LINEAGE_RIGHT])
        assert certify(snapshot, (LINEAGE_LEFT,), (LINEAGE_RIGHT,)).state == "shared-source"

    def test_the_producer_set_comes_from_the_stores_produces_edges(self, view):
        snapshot = lineage_snapshot(view, [DERIVED])
        assert [producer.stored_run for producer in snapshot.producers[DERIVED]] == [RUN]
        assert snapshot.producers[DERIVED][0].transforms == (RAW,)
        # The same run `observes` and `transforms` the raw dataset and produces
        # nothing into it, so a producer set read off every inbound edge rather
        # than off `produces` would name a producer here.
        assert snapshot.producers[RAW] == ()


class TestR23DerivedFromIsAView:
    def test_derived_from_resolves_over_produces_then_transforms(self, view):
        assert derived_from(view, DERIVED).reached == (RAW,)

    def test_no_derived_from_edge_is_stored_in_the_corpus(self, view):
        predicates = {relation.predicate for node in view.iter_stored() for relation in node.relations}
        assert "derived_from" not in predicates

    def test_no_ordinary_api_accepts_an_authored_ancestry_list(self):
        import inspect

        from beliefs.corpus import CorpusWriter

        assert set(inspect.signature(CorpusWriter.add).parameters) == {"self", "node"}
        assert "derived_from" not in inspect.getsource(CorpusWriter)

    def test_independence_follows_the_stamped_basis_not_the_composition(self, durable_writer, durable_root):
        # Basis and composition made to disagree by the raw-write fixture act:
        # the run transforms one dataset and the stamped basis names another.
        durable_writer.add(stored.dataset_node("composed", title="composed", resources=pinned()))
        durable_writer.add(stored.dataset_node("stamped", title="stamped", resources=pinned()))
        durable_writer.add(
            stored.run_node(
                "r23", title="r23", spec=SPEC, transforms=["dataset:composed"], produces=["dataset:out"]
            )
        )
        # The route records what the producing run transformed, so the only
        # disagreement is the one this arm is about: the ancestor.
        disagreeing = stored.dataset_node(
            "out",
            title="out",
            resources=pinned(),
            basis=basis(route("run:r23", "dataset:stamped", ["dataset:composed"])),
        )
        raw_write(durable_root, disagreeing)

        view = reopen(durable_root)
        assert derived_from(view, "dataset:out").reached == ("dataset:composed",)
        snapshot = lineage_snapshot(view, ["dataset:out"])
        assert snapshot.bases["dataset:out"].routes[0].resolved_ancestor == "dataset:stamped"
        # Independence walks the basis: the closure meets `stamped` and misses
        # `composed`, which is the opposite of what the view says. A build that
        # certified off the view would answer both of these the other way round.
        assert certify(snapshot, ("dataset:out",), ("dataset:stamped",)).state == "shared-source"
        assert certify(snapshot, ("dataset:out",), ("dataset:composed",)).state == "independent"
