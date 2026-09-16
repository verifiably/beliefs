"""`beliefs.composite` — construction, classification, identity, the stored shape (design §3–§5, U3, U5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node

from beliefs import composite, stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeError, CompositeNode, build_composite
from beliefs.contract import parse_base_contract, parse_domain_contract
from beliefs.contract.domain import VocabularyBinding
from beliefs.errors import MalformedRecord
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import TermOutcome, build_snapshot

REPO = Path(__file__).resolve().parents[2]
BASE = parse_base_contract(__import__("yaml").safe_load((REPO / "contracts/science/CONTRACT.yaml").read_text()), source="<base>")
TESTING = parse_domain_contract(__import__("yaml").safe_load((REPO / "fixtures/contracts/testing.yaml").read_text()), source="<t>", base=BASE, predecessor=None)
PROFILE = compile_profile(BASE, [TESTING])
EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)

ENTITY, OUTCOME = "testing/entity", "testing/outcome"
A, B, C = CompositeNode(ENTITY, "EX:a"), CompositeNode(ENTITY, "EX:b"), CompositeNode(OUTCOME, "EX:y")
CONSULTED = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:y", "EX:isolated"]})
EXCLUDING = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:y"]})
UNCONSULTED = build_snapshot()


def _claim(operator: str, cause: str, effect: str, *, polarity: str | None = "positive", layer: str = "causal"):
    sorts = PROFILE.operator(operator).arg_sorts
    return build_claim(PROFILE, operator=operator, args=(Referent(sorts[0], cause), Referent(sorts[1], effect)), layer=layer, polarity=polarity)


def _proposition(slug: str, claim) -> Node:
    return stored.proposition_node(slug, title=slug, claim=project_claim(claim))


def _corpus(tmp_path: Path, *nodes: Node):
    root = tmp_path / "corpus"
    root.mkdir()
    for node in nodes:
        raw_write(root, node)
    return reopen(root)


AB = _claim("testing/affects", "EX:a", "EX:y")            # a → y, positive
NEG = _claim("testing/affects", "EX:b", "EX:y", polarity="negative")


class TestConstruction:
    def test_a_dag_of_two_edges_builds_and_reports_signs(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        value, receipt = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="two")
        assert value.facet.nodes == (A, B, C)  # sorted by (sort, term): entity before outcome
        assert value.facet.members == tuple(sorted([claim_identity(AB), claim_identity(NEG)]))
        assert {(e.cause, e.effect, e.sign) for e in value.edges} == {(A, C, "positive"), (B, C, "negative")}
        assert receipt.identity == value.identity
        assert receipt.outcomes == {"node:0": TermOutcome.MEMBER, "node:1": TermOutcome.MEMBER, "node:2": TermOutcome.MEMBER}

    def test_authoring_order_does_not_move_identity_but_an_isolated_node_does(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        one, _ = build_composite(PROFILE, view, shape="dag", nodes=[C, B, A], members=["proposition:neg", "proposition:ab"], snapshot=CONSULTED, slug="one")
        two, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="two")
        three, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="three")
        assert one.identity == two.identity != three.identity

    def test_nodes_and_no_members_is_legal(self, tmp_path):
        value, receipt = build_composite(PROFILE, _corpus(tmp_path), shape="dag", nodes=[A, B], members=[], snapshot=CONSULTED, slug="empty")
        assert value.edges == () and value.facet.members == ()
        assert set(receipt.outcomes) == {"node:0", "node:1"}

    @pytest.mark.parametrize(
        ("nodes", "members", "code"),
        [
            ([], [], "composite-nodes-empty"),
            ([A, A], [], "composite-duplicate"),
            ([A, C], ["proposition:ab", "proposition:ab"], "composite-duplicate"),
            ([A], ["proposition:ab"], "composite-member-outside-nodes"),
            ([A, C], ["proposition:missing"], "composite-member-unresolvable"),
        ],
    )
    def test_form_refusals(self, tmp_path, nodes, members, code):
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=nodes, members=members, snapshot=CONSULTED, slug="x")
        assert caught.value.code == code

    def test_an_unknown_shape_refuses(self, tmp_path):
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, _corpus(tmp_path), shape="pag", nodes=[A], members=[], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-shape"

    def test_a_member_that_is_not_a_proposition_refuses(self, tmp_path):
        dataset = stored.dataset_node(title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}])
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, _corpus(tmp_path, dataset), shape="dag", nodes=[A, C], members=[dataset.id], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-kind"

    def test_an_undeclared_operator_and_a_non_causal_layer_refuse(self, tmp_path):
        stat = _claim("testing/correlates-with", "EX:a", "EX:y", layer="statistical")
        structural = _claim("testing/subtype-of", "EX:a", "EX:b", polarity=None, layer="structural")
        view = _corpus(tmp_path, _proposition("stat", stat), _proposition("sub", structural))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:stat"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-undeclared"
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, B], members=["proposition:sub"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-undeclared"  # subtype-of has no edges: row; the layer check never runs

    def test_a_causal_operator_member_at_another_layer_refuses_on_layer(self, tmp_path):
        # `affects` declares an edge, but this claim asserts it at the statistical layer.
        member = _claim("testing/affects", "EX:a", "EX:y", layer="statistical") if "statistical" in PROFILE.operator("testing/affects").layers else None
        if member is None:
            pytest.skip("the fixture's affects admits causal only; the layer arm is exercised by the biology fixture in test_composite_boundary")
        view = _corpus(tmp_path, _proposition("m", member))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:m"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-layer"

    def test_a_cycle_through_a_negative_edge_refuses(self, tmp_path):
        # entity → outcome only exists under `affects`; a cycle needs an entity-sorted effect, so use `regulates`-shaped
        # claims from the biology fixture: see test_composite_boundary. Here: a two-node cycle over the testing
        # fixture is unconstructible (arg sorts differ), which is itself the assertion.
        pytest.skip("cycle detection is exercised in test_composite_boundary under the biology fixture (gene → gene)")

    def test_an_isolated_node_with_an_undeclared_sort_refuses_in_shared_classification(self, tmp_path):
        from beliefs.composite import CompositeFacet, classify
        from beliefs.contract.base import COMPOSITE_GRAMMAR

        facet = CompositeFacet(grammar=COMPOSITE_GRAMMAR, shape="dag", nodes=(CompositeNode("nowhere/sort", "EX:z"),), members=())
        with pytest.raises(CompositeError) as caught:
            classify(PROFILE, facet, {})
        assert caught.value.code == "composite-node-sort"

    def test_a_retired_edge_declaration_refuses(self, tmp_path):
        import copy

        import yaml

        document = yaml.safe_load((REPO / "fixtures/contracts/testing.yaml").read_text())
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": TESTING.content_identity}
        successor["edges"]["affects"]["retired"] = True
        retired = compile_profile(BASE, [parse_domain_contract(successor, source="<r>", base=BASE, predecessor=TESTING)])
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(retired, view, shape="dag", nodes=[A, C], members=["proposition:ab"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-retired"

    def test_a_member_whose_stored_claim_fails_typing_is_unrestorable_not_an_escape(self, tmp_path):
        node = _proposition("bad", AB)
        node.facets[stored.PROPOSITION_FACET]["layer"] = "methodological"  # affects admits causal only
        stored.stamp_semantic_identity(node)
        view = _corpus(tmp_path, node)
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:bad"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-unrestorable"

    def test_an_isolated_node_a_consulted_vocabulary_excludes_refuses(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab"], snapshot=EXCLUDING, slug="x")
        assert caught.value.code == "composite-node-not-member"
        assert "EX:isolated" in str(caught.value)

    def test_an_isolated_node_under_an_unconsulted_vocabulary_is_admitted_and_recorded(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB))
        value, receipt = build_composite(PROFILE, view, shape="dag", nodes=[A, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab"], snapshot=UNCONSULTED, slug="x")
        assert receipt.outcomes["node:1"] == TermOutcome.NOT_CONSULTED  # (entity, EX:isolated) sorts after (entity, EX:a)
        assert receipt.snapshot_identity == UNCONSULTED.identity
        assert len(value.facet.nodes) == 3

    def test_a_snapshot_is_required(self, tmp_path):
        with pytest.raises(TypeError):
            build_composite(PROFILE, _corpus(tmp_path), shape="dag", nodes=[A], members=[], slug="x")  # type: ignore[call-arg]

    def test_the_value_has_no_public_constructor(self):
        with pytest.raises(CompositeError):
            composite.Composite()  # type: ignore[call-arg]


class TestStoredShape:
    def test_composite_node_writes_the_facet_and_one_composes_edge_per_member(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        value, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:neg", "proposition:ab"], snapshot=CONSULTED, slug="two")
        node = stored.composite_node(value, title="two")
        assert node.id == "composite:two" and node.kind == "composite"
        facet = stored.composite_value(node)
        assert facet == value.facet
        assert [r.predicate for r in node.relations] == [stored.COMPOSES, stored.COMPOSES]
        assert [r.target for r in node.relations] == list(value.refs)  # facet order, i.e. sorted by member identity
        assert stored.stored_semantic_hash(node) == value.identity == composite.composite_identity(value.facet)

    def test_composite_node_refuses_a_hand_built_value(self):
        with pytest.raises(MalformedRecord):
            stored.composite_node(object(), title="x")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda f: f.__setitem__("grammar", "science.composite.v2"),
            lambda f: f.__setitem__("shape", 1),
            lambda f: f.__setitem__("nodes", []),
            lambda f: f.__setitem__("nodes", [{"sort": ENTITY, "term": "EX:a"}, {"sort": ENTITY, "term": "EX:a"}]),
            lambda f: f.__setitem__("nodes", [{"sort": OUTCOME, "term": "EX:y"}, {"sort": ENTITY, "term": "EX:a"}]),  # unsorted
            lambda f: f.__setitem__("members", ["b", "a"]),
            lambda f: f.__setitem__("members", ["a", 7]),
            lambda f: f.__setitem__("extra", 1),
            lambda f: f.pop("members"),
        ],
    )
    def test_composite_value_refuses_a_malformed_facet(self, tmp_path, mutate):
        view = _corpus(tmp_path, _proposition("ab", AB))
        value, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:ab"], snapshot=CONSULTED, slug="x")
        node = stored.composite_node(value, title="x")
        mutate(node.facets[stored.COMPOSITE_FACET])
        with pytest.raises(MalformedRecord):
            stored.composite_value(node)
