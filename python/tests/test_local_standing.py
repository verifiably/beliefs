from __future__ import annotations

import pytest
from authority import ACTOR
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import corpus, errors, stored
from beliefs.errors import (
    MalformedRecord,
    SemanticHashMissing,
    SemanticHashStale,
)


def seed(root, *nodes: Node):
    for node in nodes:
        raw_write(root, node)
    return reopen(root)


def assessment() -> Node:
    return stored.assessment_node(
        "a1",
        title="a1",
        spec="analysis-spec:s1",
        run="run:r1",
        proposition="proposition:p1",
        outcome="supported",
        interpretation_rule="rule:threshold",
    )


def retracts(target: Node, token: str) -> Node:
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    return stored.retraction_node(
        title=token,
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the record is invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
    )


def raw_retraction(node_id: str, target: str) -> Node:
    node = Node(
        id=node_id,
        kind="retraction",
        title=node_id,
        facets={
            stored.RETRACTION_FACET: {
                "target": {
                    "arm": "node",
                    "ref": target,
                    "resolved": target,
                    "content_identity": "sha256:" + "ab" * 32,
                },
                "reason": "defective-code",
                "rationale": "raw cycle fixture",
                "grounds": ["verification:v1"],
                "actor": "tester",
                "event_token": node_id,
            }
        },
        relations=[
            Relation(source=node_id, predicate=stored.RETRACTS, target=target),
            Relation(source=node_id, predicate=stored.GROUNDED_IN, target="verification:v1"),
        ],
    )
    return stored.stamp_semantic_identity(node)


def test_superseded_by_is_derived_inbound_and_sorted(tmp_path):
    old = stored.proposition_node("old", title="old", claim={"operator": "affects"})
    middle = stored.proposition_node("middle", title="middle", claim={"operator": "causes"})
    newest = stored.proposition_node("newest", title="newest", claim={"operator": "prevents"})
    side = stored.proposition_node("side", title="side", claim={"operator": "correlates"})
    middle.relations.append(Relation(source=middle.id, predicate=stored.SUPERSEDES, target=old.id))
    newest.relations.append(Relation(source=newest.id, predicate=stored.SUPERSEDES, target=middle.id))
    side.relations.append(Relation(source=side.id, predicate=stored.SUPERSEDES, target=old.id))

    view = seed(tmp_path, newest, side, middle, old)

    assert corpus.superseded_by(view, old.id) == (middle.id, newest.id, side.id)


def test_standing_is_subtracted_by_one_standing_retraction(tmp_path):
    target = assessment()
    retraction = retracts(target, "r1")

    view = seed(tmp_path, target, retraction)

    assert corpus.standing_in_local_view(view, target.id) is False
    assert corpus.standing_in_local_view(view, retraction.id) is True


def test_counter_retraction_restores_iff_no_standing_sibling_remains(tmp_path):
    target = assessment()
    first = retracts(target, "r1")
    sibling = retracts(target, "r2")
    first_counter = retracts(first, "c1")
    view_with_sibling = seed(tmp_path / "one", target, first, sibling, first_counter)

    assert corpus.standing_in_local_view(view_with_sibling, target.id) is False

    sibling_counter = retracts(sibling, "c2")
    view_without_standing_sibling = seed(
        tmp_path / "two", target, first, sibling, first_counter, sibling_counter
    )

    assert corpus.standing_in_local_view(view_without_standing_sibling, target.id) is True


def test_counter_counter_retraction_retracts_the_restoration(tmp_path):
    target = assessment()
    first = retracts(target, "r1")
    counter = retracts(first, "c1")
    counter_counter = retracts(counter, "cc1")
    view = seed(tmp_path, target, first, counter, counter_counter)

    assert corpus.standing_in_local_view(view, target.id) is False


def test_route_retractions_do_not_subtract_node_standing(tmp_path):
    dataset = stored.dataset_node(
        "d1",
        title="d1",
        resources=[{"name": "matrix", "digest": "sha256:" + "cd" * 32}],
        basis={"tag": "single", "routes": [{"identity": "route:one"}]},
    )
    content_identity = stored.stored_semantic_hash(dataset)
    assert content_identity is not None
    retraction = stored.retraction_node(
        title="route retraction",
        target=stored.RouteTarget(dataset.id, dataset.id, content_identity, "route:one"),
        reason="wrong-route",
        rationale="the route is invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="route-r1",
    )

    view = seed(tmp_path, dataset, retraction)

    assert corpus.standing_in_local_view(view, dataset.id) is True


def test_stale_retraction_refuses_the_whole_evaluation(tmp_path):
    target = assessment()
    retraction = retracts(target, "r1")
    retraction.facets[stored.RETRACTION_FACET]["rationale"] = "changed after stamping"
    view = seed(tmp_path, target, retraction)

    with pytest.raises(SemanticHashStale):
        corpus.standing_in_local_view(view, "assessment:unrelated")


def test_unstamped_retraction_refuses_the_whole_evaluation(tmp_path):
    target = assessment()
    retraction = retracts(target, "r1")
    del retraction.facets[stored.SEMANTIC_IDENTITY_FACET]
    view = seed(tmp_path, target, retraction)

    with pytest.raises(SemanticHashMissing):
        corpus.standing_in_local_view(view, "assessment:unrelated")


def test_malformed_retraction_facet_refuses_the_whole_evaluation(tmp_path):
    target = assessment()
    retraction = retracts(target, "r1")
    del retraction.facets[stored.RETRACTION_FACET]["target"]["resolved"]
    stored.stamp_semantic_identity(retraction)
    view = seed(tmp_path, target, retraction)

    with pytest.raises(MalformedRecord):
        corpus.standing_in_local_view(view, "assessment:unrelated")


def test_raw_written_cycle_shape_is_malformed_before_evaluation(tmp_path):
    first = raw_retraction("retraction:r1", "retraction:r2")
    second = raw_retraction("retraction:r2", "retraction:r1")
    assert not stored.semantic_hash_disagrees(first)
    assert not stored.semantic_hash_disagrees(second)
    view = seed(tmp_path, first, second)

    with pytest.raises(errors.MalformedRecord):
        corpus.standing_in_local_view(view, "assessment:unrelated")


def test_corpus_check_reports_a_raw_retraction_with_a_missing_local_target(tmp_path):
    retraction = raw_retraction("retraction:r1", "assessment:missing")
    raw_write(tmp_path, retraction)

    findings = corpus.corpus_check(reopen(tmp_path))

    assert [(finding.severity, finding.code) for finding in findings] == [
        ("error", "retraction-target-invalid")
    ]


def test_corpus_check_reports_an_ungoverned_node_with_a_semantic_stamp(tmp_path):
    malformed = Node(
        id="discussion:bad-domain",
        kind="discussion",
        title="bad domain",
        facets={stored.SEMANTIC_IDENTITY_FACET: {"digest": "x"}},
    )
    view = seed(tmp_path, malformed)

    findings = corpus.corpus_check(view)

    assert [(finding.code, finding.ref, finding.detail) for finding in findings] == [
        ("semantic-hash-stale", malformed.id, "unencodable")
    ]


def test_wrong_retraction_target_content_identity_is_invalid_and_not_applied(tmp_path):
    target = assessment()
    retraction = stored.retraction_node(
        title="wrong content identity",
        target=stored.NodeTarget(target.id, target.id, "sha256:" + "ab" * 32),
        reason="defective-code",
        rationale="wrong target identity",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="wrong-content",
    )
    view = seed(tmp_path, target, retraction)

    with pytest.raises(errors.RetractionTargetUnresolvable):
        corpus.standing_in_local_view(view, target.id)

    assert "retraction-target-invalid" in {finding.code for finding in corpus.corpus_check(view)}


def test_corpus_check_rejects_raw_cycle_shapes_before_cycle_classification(tmp_path):
    first = raw_retraction("retraction:r1", "retraction:r2")
    second = raw_retraction("retraction:r2", "retraction:r1")
    raw_write(tmp_path, first)
    raw_write(tmp_path, second)

    findings = corpus.corpus_check(reopen(tmp_path))

    assert [(finding.severity, finding.code) for finding in findings] == [
        ("error", "retraction-target-invalid"),
        ("error", "retraction-target-invalid"),
    ]
