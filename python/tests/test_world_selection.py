"""View-query evaluation over the world read view (slice 4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from coordination_fixtures import raw_coordination_node
from nodes.core.corpus import Corpus
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from test_evaluation import CLAIM_FACET, GENE, PHENO
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import SelectionRefused, SemanticHashStale
from beliefs.view_query import ViewQuery, parse_view_query, stored_query
from beliefs.world.selection import SELECTION_VERSION, evaluate_query
from beliefs.world.view import open_world_view

PROJECT = "1" * 32
TOPIC = "2" * 32
REVISION = "3" * 32


def query(*clauses: list[dict]) -> ViewQuery:
    return parse_view_query({"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]})


def topic_nodes():
    """ALPHA: d_a (carrying a `produces` relation whose declared source is
    BETA's r_b — the world inbound index files edges from held records only,
    so the edge that must survive BETA's absence lives on d_a), r_a (produces
    d_b), the project and topic records. BETA: d_b, r_b, p_b (claim binding
    GENE and PHENO)."""
    d_a = stored.dataset_node("d-a", title="d-a")
    d_b = stored.dataset_node("d-b", title="d-b")
    r_a = stored.run_node("r-a", title="r-a", spec="s", produces=[d_b.id])
    r_b = stored.run_node("r-b", title="r-b", spec="s", produces=[])
    d_a.relations.append(Relation(source=r_b.id, predicate="produces", target=d_a.id))
    p_b = stored.proposition_node("p-b", title="p-b", claim=CLAIM_FACET)
    project = raw_coordination_node("project", PROJECT, "4" * 32)
    return (d_a, r_a, project), (d_b, r_b, p_b)


def topic_world(tmp_path: Path, *clauses: list[dict], alpha_extra=(), beta_extra=(), without=()):
    """The topic world; `without` drops fixture records by id before publication."""
    alpha, beta = topic_nodes()
    alpha = tuple(n for n in alpha if n.id not in without)
    beta = tuple(n for n in beta if n.id not in without)
    topic = raw_coordination_node(
        "topic", PROJECT, REVISION, local=TOPIC,
        query={"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]},
    )
    roots = corpora(tmp_path, {ALPHA: (*alpha, *alpha_extra, topic), BETA: (*beta, *beta_extra)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    return world, roots, published, topic


def evaluate_topic(world, roots, published, topic):
    """The caller's half: resolve the record live, then evaluate bound."""
    record = Corpus(roots[ALPHA]).get(topic.id)
    return evaluate_query(open_world_view(world, published), stored_query(record))


class TestAddressesAndKinds:
    def test_addresses_select_exactly_the_named_record_and_contribute_its_corpus(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-b",)
        assert selection.contributing == (BETA,)
        assert selection.complete and selection.absent == () and selection.unresolved == ()
        assert selection.stamp.packaging_identity == published.packaging_identity

    def test_kinds_select_both_corpora_and_contribute_both(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-a", "dataset:d-b")
        assert selection.contributing == (ALPHA, BETA)

    def test_clauses_union_and_predicates_intersect(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path,
            [{"kinds": ["dataset"]}, {"addresses": ["dataset:d-b"]}],
            [{"kinds": ["run"]}],
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-b", "run:r-a", "run:r-b")

    def test_empty_clauses_are_a_complete_empty_selection(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path)
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == () and selection.contributing == () and selection.complete

    def test_a_retired_and_a_live_address_select_the_record_once(self, tmp_path):
        renamed = stored.dataset_node("d-new", title="d-new")
        renamed.deprecated_ids = ["dataset:d-old"]
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:d-old", "dataset:d-new"]}], alpha_extra=(renamed,)
        )
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("dataset:d-new",)


class TestReferencesTerm:
    def test_a_term_in_an_argument_selects_the_proposition_and_never_a_dataset(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("proposition:p-b",) and selection.contributing == (BETA,)

    def test_a_term_in_a_qualifier_restriction_selects(self, tmp_path):
        qualified = stored.proposition_node(
            "p-q", title="p-q",
            claim={**CLAIM_FACET, "qualifiers": {"tissue": {"quantifier": "some", "restriction": "EX:liver"}}},
        )
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": "EX:liver"}], beta_extra=(qualified,))
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == ("proposition:p-q",)

    def test_a_term_absent_everywhere_selects_nothing_and_refuses_nothing(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": "EX:nothing"}])
        selection = evaluate_topic(world, roots, published, topic)
        assert selection.selected == () and selection.complete

    def test_the_term_is_compared_as_stored_without_normalization(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE.upper()}])
        assert evaluate_topic(world, roots, published, topic).selected == ()

    @pytest.mark.parametrize(
        "claim",
        [
            {**CLAIM_FACET, "args": "not-a-list"},
            {**CLAIM_FACET, "args": [GENE, 7]},
            {**CLAIM_FACET, "qualifiers": {"tissue": {"restriction": "EX:liver"}}},
            {**CLAIM_FACET, "qualifiers": {"tissue": {"quantifier": "some", "restriction": "EX:liver", "extra": 1}}},
            {k: v for k, v in CLAIM_FACET.items() if k != "layer"},
        ],
    )
    def test_a_malformed_claim_facet_refuses_naming_the_record(self, tmp_path, claim):
        broken = stored.proposition_node("p-x", title="p-x", claim=claim)
        world, roots, published, topic = topic_world(tmp_path, [{"references-term": GENE}], beta_extra=(broken,))
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "record-malformed" and caught.value.refs == ("proposition:p-x",)

    def test_a_stale_edit_that_removed_the_term_refuses_rather_than_yielding_empty(self, tmp_path):
        stale = stored.proposition_node("p-s", title="p-s", claim=CLAIM_FACET)
        stale.facets["proposition"]["args"] = ["EX:other", PHENO]
        world, roots, published, topic = topic_world(
            tmp_path, [{"references-term": GENE}], beta_extra=(stale,), without=("proposition:p-b",),
        )
        with pytest.raises(SemanticHashStale):
            evaluate_topic(world, roots, published, topic)


class TestIdentityAndDeterminism:
    def test_the_projection_is_the_documented_shape_and_the_identity_is_its_digest(self, tmp_path):
        from beliefs.identity import v1

        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        selection = evaluate_topic(world, roots, published, topic)
        projection = selection.projection()
        assert projection == {
            "version": SELECTION_VERSION,
            "epoch": published.packaging_identity,
            "query": selection.query.projection(),
            "selected": ["dataset:d-b"],
            "contributing": [BETA],
            "absent": [],
            "unresolved": [],
        }
        assert selection.identity() == v1.digest(SELECTION_VERSION, projection)

    def test_two_opens_at_one_epoch_and_reordered_authoring_agree(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"kinds": ["dataset"]}, {"addresses": ["dataset:d-b"]}], [{"kinds": ["run"]}]
        )
        first = evaluate_topic(world, roots, published, topic)
        reordered = query([{"kinds": ["run"]}], [{"addresses": ["dataset:d-b"]}, {"kinds": ["dataset"]}])
        second = evaluate_query(open_world_view(world, published), reordered)
        assert first.projection() == second.projection() and first.identity() == second.identity()

    def test_registration_order_does_not_move_the_projection(self, tmp_path):
        alpha, beta = topic_nodes()
        forward = corpora(tmp_path / "f", {ALPHA: alpha, BETA: beta})
        backward = corpora(tmp_path / "b", {BETA: beta, ALPHA: alpha})
        selections = []
        for roots in (forward, backward):
            world = world_over(roots[ALPHA].parent, roots)
            published = publish(world, (ALPHA, BETA), hold_shipped(world))
            selections.append(evaluate_query(open_world_view(world, published), query([{"kinds": ["dataset"]}])))
        assert selections[0].selected == selections[1].selected == ("dataset:d-a", "dataset:d-b")
        assert selections[0].contributing == selections[1].contributing


class TestEntryRefusals:
    def test_a_corpus_read_view_is_refused_by_type(self, tmp_path):
        _world, roots, _published, _topic = topic_world(tmp_path)
        with pytest.raises(TypeError, match="WorldReadView"):
            evaluate_query(ReadView.opened_at(roots[ALPHA]), query([{"kinds": ["dataset"]}]))  # type: ignore[arg-type]

    def test_a_drifted_view_refuses_and_the_earlier_capture_still_evaluates(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        before = open_world_view(world, published)
        node = Corpus(roots[BETA]).get("dataset:d-b")
        node.relations.append(Relation(source=node.id, predicate="cites", target="dataset:d-a"))
        (roots[BETA] / "dataset" / "d-b.md").write_text(node_to_markdown(node), encoding="utf-8")
        after = open_world_view(world, published)
        moved = [report.corpus_id for report in after.drift() if report.captured_state != report.published_state]
        assert moved == [BETA]
        with pytest.raises(SelectionRefused) as caught:
            evaluate_query(after, stored_query(Corpus(roots[ALPHA]).get(topic.id)))
        assert caught.value.reason == "corpus-drifted" and caught.value.refs == (BETA,)
        assert evaluate_query(before, stored_query(Corpus(roots[ALPHA]).get(topic.id))).complete

    def test_records_outside_the_map_report_unmapped_under_equal_states_and_do_not_refuse(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        view = open_world_view(world, published)
        (report,) = [r for r in view.drift() if r.corpus_id == ALPHA]
        assert report.captured_state == report.published_state and report.unmapped  # the project and topic uids
        assert evaluate_query(view, stored_query(Corpus(roots[ALPHA]).get(topic.id))).complete

    def test_a_damaged_view_refuses_before_drift_is_read(self, tmp_path):
        from test_world_view import damage

        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        damage(roots[BETA], "parse-error")
        view = open_world_view(world, published, on_damage="report")
        with pytest.raises(SelectionRefused) as caught:
            evaluate_query(view, stored_query(Corpus(roots[ALPHA]).get(topic.id)))
        assert caught.value.reason == "corpus-damaged" and caught.value.refs == (BETA,)

    def test_an_unknown_address_refuses_naming_every_unknown_one(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:never", "dataset:d-b"]}], [{"addresses": ["run:never"]}]
        )
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-unknown"
        assert caught.value.refs == ("dataset:never", "run:never") and caught.value.corpus_ids == ()

    def test_a_not_present_address_refuses_naming_its_corpus_and_never_reads_as_empty(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"addresses": ["dataset:d-b"]}])
        make_absent(roots, BETA)
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-not-present"
        assert caught.value.refs == ("dataset:d-b",) and caught.value.corpus_ids == (BETA,)

    def test_unknown_outranks_not_present_and_the_two_never_share_a_refusal(self, tmp_path):
        world, roots, published, topic = topic_world(
            tmp_path, [{"addresses": ["dataset:d-b", "dataset:never"]}]
        )
        make_absent(roots, BETA)
        with pytest.raises(SelectionRefused) as caught:
            evaluate_topic(world, roots, published, topic)
        assert caught.value.reason == "address-unknown" and caught.value.refs == ("dataset:never",)


class TestAbsenceAndValidation:
    def test_kinds_over_an_absent_corpus_is_incomplete_and_names_it(self, tmp_path):
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        complete = evaluate_topic(world, roots, published, topic)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert partial.selected == ("dataset:d-a",) and partial.absent == (BETA,) and not partial.complete
        assert partial.projection()["absent"] == [BETA]  # the member itself, not only the identity
        assert partial.identity() != complete.identity()

    def test_absent_alone_moves_the_identity(self, tmp_path):
        """`clauses: []` selects nothing either way, so only `absent` differs."""
        world, roots, published, topic = topic_world(tmp_path)
        complete = evaluate_topic(world, roots, published, topic)
        make_absent(roots, BETA)
        partial = evaluate_topic(world, roots, published, topic)
        assert complete.selected == partial.selected == () and complete.contributing == partial.contributing == ()
        assert partial.projection()["absent"] == [BETA] and partial.identity() != complete.identity()

    def test_a_selected_record_with_a_stale_hash_refuses(self, tmp_path):
        stale = stored.dataset_node("d-s", title="d-s")
        stale.facets["dataset"]["resources"] = [{"digest": "f" * 64}]  # edited after stamping: stale on disk
        world, roots, published, topic = topic_world(tmp_path, [{"kinds": ["dataset"]}], alpha_extra=(stale,))
        with pytest.raises(SemanticHashStale):
            evaluate_topic(world, roots, published, topic)
