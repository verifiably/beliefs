"""The closure-to-stored codec (spec §2.6 items 4–5)."""

from decimal import Decimal
from typing import cast

import pytest
from closure_fixtures import make_closure as build_closure
from nodes.core.frontmatter import node_from_markdown

from science import runrecord, stored
from science.errors import MalformedRecord
from science.identity import v1
from science.production import mint_dataset
from science.recipe import RunClosure


@pytest.fixture
def assessment_closure() -> RunClosure:
    return build_closure()


@pytest.fixture
def production_closure() -> RunClosure:
    return build_closure(shape="dataset-production")


@pytest.fixture
def make_closure():
    return build_closure


def test_projection_text_digests_to_the_address(assessment_closure) -> None:
    data = runrecord.projection_text(assessment_closure)
    assert v1.digest("science.run.v1", v1.decode(data)) == assessment_closure.address()


def test_decode_round_trip_reads_shape_spec_and_token(assessment_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    publication = runrecord.decode_run_record(node)
    assert publication == runrecord.RunPublication(
        address=assessment_closure.address(),
        shape="assessment",
        spec_identity=assessment_closure.recipe.spec_identity,
        event_token=assessment_closure.occurrence.event_token,
    )


def test_closure_member_mutation_diverges_from_the_id(assessment_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure)
    text = op.content.decode("utf-8")
    mutated = text.replace(assessment_closure.occurrence.actor, "someone-else", 1)
    node = node_from_markdown(mutated)
    node.facets["semantic-identity"] = {
        "digest": stored.recompute_semantic_hash(node)
    }
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)


def test_incomplete_closure_fails_the_view_not_the_codec() -> None:
    preimage = {
        "shape": "assessment",
        "spec_identity": "s" * 64,
        "event_token": "t" * 32,
    }
    data = v1.encode(preimage)
    assert v1.decode(data) == preimage
    assert len(v1.digest("science.run.v1", preimage)) == 64
    with pytest.raises(MalformedRecord):
        runrecord.decode_projection(data)


def test_reversed_result_pairs_fail_canonical_reprojection(
    production_closure,
) -> None:
    data = runrecord.projection_text(production_closure)
    parsed = v1.decode(data)
    assert isinstance(parsed, dict)
    pairs = cast("list[list[str]]", parsed["result"])
    assert len(pairs) == 2
    reordered = list(reversed(pairs))
    assert reordered != sorted(reordered)
    parsed["result"] = reordered
    reversed_bytes = v1.encode(parsed)
    assert v1.decode(reversed_bytes) == parsed
    assert len(v1.digest("science.run.v1", parsed)) == 64
    with pytest.raises(MalformedRecord):
        runrecord.decode_projection(reversed_bytes)


def test_decimal_wire_arms_project_decode_recompute(make_closure) -> None:
    values = [Decimal("0.5"), "0.5", 1, Decimal("1.0")]
    closures = [make_closure(parameters={"threshold": value}) for value in values]
    texts = [runrecord.projection_text(closure) for closure in closures]
    assert len(set(texts)) == 4
    addresses = [closure.address() for closure in closures]
    assert len(set(addresses)) == 4
    for closure, data, address in zip(closures, texts, addresses):
        parsed = runrecord.decode_projection(data)
        assert v1.digest("science.run.v1", parsed) == address
        recipe_view = cast("dict[str, object]", parsed["recipe"])
        parameters = cast("dict[str, object]", recipe_view["parameters"])
        threshold = parameters["threshold"]
        original = closure.recipe.parameters["threshold"]
        assert threshold == original and type(threshold) is type(original)


def test_shape_agreement_both_ways(
    assessment_closure, production_closure
) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run"]["spec"] = "not-the-closure-spec"
    node.facets["semantic-identity"] = {
        "digest": stored.recompute_semantic_hash(node)
    }
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)

    _, _, (op,) = runrecord.publication_plan(production_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run"]["spec"] = "s" * 64
    node.facets["semantic-identity"] = {
        "digest": stored.recompute_semantic_hash(node)
    }
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)


def test_run_facet_shapes_are_exact_not_get_based(
    assessment_closure, production_closure
) -> None:
    for closure in (assessment_closure, production_closure):
        _, _, (op,) = runrecord.publication_plan(closure)
        node = node_from_markdown(op.content.decode("utf-8"))
        node.facets["run"]["extra"] = "key"
        node.facets["semantic-identity"] = {
            "digest": stored.recompute_semantic_hash(node)
        }
        with pytest.raises(MalformedRecord):
            runrecord.decode_run_record(node)


def test_legacy_run_node_reads_and_never_qualifies() -> None:
    node = stored.run_node("legacy-slug", title="legacy", spec="s" * 64)
    assert stored.run_spec(node) == "s" * 64
    assert runrecord.decode_run_record(node) is None


def test_production_facet_is_exactly_empty_and_run_spec_reads_none(
    production_closure,
) -> None:
    _, _, (op,) = runrecord.publication_plan(production_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    assert node.facets["run"] == {}
    assert stored.run_spec(node) is None


def test_relations_are_role_preserving(
    assessment_closure, production_closure
) -> None:
    def edges(node, role, closure):
        expected = tuple(e.dataset for e in closure.recipe.inputs if e.role == role)
        assert expected, f"the fixture must carry a {role} input"
        assert stored.inputs_of(node, role) == expected

    _, _, (op,) = runrecord.publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    edges(node, "observes", assessment_closure)
    edges(node, "reads", assessment_closure)
    assert stored.inputs_of(node, "transforms") == ()
    assert stored.inputs_of(node, "produces") == ()

    _, _, (op,) = runrecord.publication_plan(production_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    edges(node, "transforms", production_closure)
    edges(node, "reads", production_closure)
    assert stored.inputs_of(node, "observes") == ()
    minted = mint_dataset(production_closure, existing_bases={})
    assert stored.inputs_of(node, "produces") == (minted.address,)


def test_the_bridge_is_closed_over_the_closure_address_domain() -> None:
    address = "a1" * 32
    assert runrecord.run_ref(address) == f"run:{address}"
    assert runrecord.bare_address(runrecord.run_ref(address)) == address
    for bad in ("", "run:x", "A" * 64, "a" * 63, "a" * 64 + ":b"):
        with pytest.raises(MalformedRecord):
            runrecord.run_ref(bad)
    for bad in (
        "run:",
        "run:a:b",
        "run:" + "A" * 64,
        "dataset:" + "a" * 64,
        "a" * 64,
    ):
        with pytest.raises(MalformedRecord):
            runrecord.bare_address(bad)


def test_publication_id_agrees_with_the_stored_node(assessment_closure) -> None:
    record_id, _, (op,) = runrecord.publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    assert node.id == record_id


def test_closure_facet_is_semantic_hash_covered(assessment_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run-closure"]["projection"] += " "
    assert stored.semantic_hash_disagrees(node)
    legacy = stored.run_node("legacy", title="legacy", spec="s" * 64)
    assert not stored.semantic_hash_disagrees(legacy)
