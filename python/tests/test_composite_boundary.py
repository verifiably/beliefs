"""The composite write boundary (design §4.2, U3, U6, U9)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from authority import ACTOR, FULL
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeError, CompositeNode, build_composite
from beliefs.contract.domain import VocabularyBinding
from beliefs.corpus import CorpusWriter, superseded_by
from beliefs.errors import FamilyKindUnsupported, ImportRefused, SignatureRefused, SupersedeIdentityUnchanged
from beliefs.estimand import Control, LevelsContrast, Measure, build_estimand
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import build_snapshot

GENE = "biology/gene"
AFFECTS = "biology/affects"
EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
# Every biology-fixture sort binds `EX/2026-01-01`, so one binding carries the nodes and the estimand's terms.
SNAPSHOT = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:c", "EX:lo", "EX:hi", "EX:expr", "EX:observational"]})
A, B, C = (CompositeNode(GENE, f"EX:{t}") for t in "abc")
IMPORT: dict[str, Any] = {"observer": "o", "instrument": "i", "opened_at": "2026-09-12T00:00:00Z", "closed_at": "2026-09-12T00:00:01Z"}


def _estimand(claim):
    """A typed estimand for a biology-fixture `affects` claim, under the profile that stores and restores it —
    the fixture's `estimands:` row for `affects` (Task 2) names `biology/level`, `biology/measure`, `biology/identification`."""
    estimand, _ = build_estimand(
        WITH_BIOLOGY, claim, snapshot=SNAPSHOT,
        contrast=LevelsContrast(slot=0, baseline=Referent("biology/level", "EX:lo"), comparison=Referent("biology/level", "EX:hi")),
        measure=Measure(quantity=Referent("biology/measure", "EX:expr"), scale="additive"),
        reference=Decimal(0),
        control=Control(identification=Referent("biology/identification", "EX:observational"), conditioning=()),
    )
    return estimand


def _writer(root):
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return writer


def _claim(cause: str, effect: str, polarity: str = "positive"):
    return build_claim(WITH_BIOLOGY, operator=AFFECTS, args=(Referent(GENE, cause), Referent(GENE, effect)), layer="causal", polarity=polarity)


def _proposition(writer, slug: str, claim) -> Node:
    return writer.add(stored.proposition_node(slug, title=slug, claim=project_claim(claim)))


@pytest.fixture()
def writer(tmp_path):
    w = _writer(tmp_path / "corpus")
    _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    _proposition(w, "ca", _claim("EX:c", "EX:a"))
    return w


def _build(writer, members, nodes=(A, B, C), slug="g"):
    value, _ = build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=list(nodes), members=list(members), snapshot=SNAPSHOT, slug=slug)
    return value


def test_add_admits_a_signed_chain_and_the_reading_view_resolves_its_members(writer):
    minted = writer.add(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="a→b⊣c"))
    node = writer.read_view.get(minted.id)
    assert {r.target for r in node.relations} == {"proposition:ab", "proposition:bc"}
    assert {e.sign for e in _build(writer, ["proposition:ab", "proposition:bc"]).edges} == {"positive", "negative"}


def test_a_cycle_through_the_negative_edge_refuses_at_construction_and_at_add(writer):
    with pytest.raises(CompositeError) as caught:
        _build(writer, ["proposition:ab", "proposition:bc", "proposition:ca"])
    assert caught.value.code == "composite-cyclic" and "EX:b" in str(caught.value)
    # Hand-assemble the same record behind the constructor and push it through `add`.
    acyclic = stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="x")
    facet = acyclic.facets[stored.COMPOSITE_FACET]
    ca = claim_identity(_claim("EX:c", "EX:a"))
    facet["members"] = sorted([*facet["members"], ca])
    refs = {claim_identity(_claim("EX:a", "EX:b")): "proposition:ab", claim_identity(_claim("EX:b", "EX:c", "negative")): "proposition:bc", ca: "proposition:ca"}
    acyclic.relations = [Relation(source=acyclic.id, predicate=stored.COMPOSES, target=refs[m]) for m in facet["members"]]
    stored.stamp_semantic_identity(acyclic)
    with pytest.raises(CompositeError) as caught:
        writer.add(acyclic)
    assert caught.value.code == "composite-cyclic"


def test_add_checks_form_and_never_vocabulary(writer):
    excluding = build_snapshot(readable={EX: ["EX:a", "EX:b"]})
    with pytest.raises(CompositeError) as caught:
        build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=[A, B, C], members=["proposition:ab"], snapshot=excluding, slug="iso")
    assert caught.value.code == "composite-node-not-member"
    value, _ = build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=[A, B, C], members=["proposition:ab"], snapshot=build_snapshot(), slug="iso")
    minted = writer.add(stored.composite_node(value, title="iso"))  # the boundary holds no snapshot (§4.2 step 1)
    assert writer.read_view.get(minted.id).kind == "composite"


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda n: n.relations.pop(), "composite-relations-mismatch"),
        (lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-member-mismatch"),
        (lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:missing")), "composite-member-unresolvable"),
        (lambda n: n.relations.append(Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-relations-mismatch"),
        (lambda n: n.facets[stored.COMPOSITE_FACET].__setitem__("shape", "pag"), "composite-shape"),
    ],
)
def test_the_boundary_re_derives_every_check_from_the_stored_record(writer, mutate, code):
    node = stored.composite_node(_build(writer, ["proposition:ab"]), title="x")
    mutate(node)
    stored.stamp_semantic_identity(node)
    with pytest.raises(CompositeError) as caught:
        writer.add(node)
    assert caught.value.code == code


def test_a_dataset_member_refuses_with_its_code(writer):
    dataset = writer.add(stored.dataset_node(title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}]))
    node = stored.composite_node(_build(writer, ["proposition:ab"]), title="x")
    node.relations[0] = Relation(source=node.id, predicate=stored.COMPOSES, target=dataset.id)
    stored.stamp_semantic_identity(node)
    with pytest.raises(CompositeError) as caught:
        writer.add(node)
    assert caught.value.code == "composite-member-kind"


class TestSupersession:
    def test_a_same_kind_successor_is_admitted_and_the_relation_is_authored_by_the_adapter(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
        assert superseded_by(writer.read_view, first.id) == (second.id,)
        assert any(r.predicate == stored.SUPERSEDES and r.target == first.id for r in writer.read_view.get(second.id).relations)

    def test_an_identity_unchanged_successor_refuses(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        with pytest.raises(SupersedeIdentityUnchanged):
            writer.supersede(stored.composite_node(_build(writer, ["proposition:ab"], slug="v2"), title="v2"), of=first.id)

    def test_supersede_refuses_a_cross_kind_pair_before_the_shared_check(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        with pytest.raises(FamilyKindUnsupported):
            writer.supersede(stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c"))), of=first.id)

    @pytest.mark.parametrize("direction", ["composite-over-proposition", "proposition-over-composite"])
    def test_add_and_import_refuse_a_cross_kind_supersedes_edge_on_the_shared_path(self, writer, tmp_path, direction):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        if direction == "composite-over-proposition":
            record = stored.composite_node(_build(writer, ["proposition:bc"], slug="v2"), title="v2")
            target = "proposition:ab"
        else:
            record = stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c")))
            target = first.id
        record.relations.append(Relation(source=record.id, predicate=stored.SUPERSEDES, target=target))
        stored.stamp_semantic_identity(record)
        with pytest.raises(SignatureRefused, match="supersedes-cross-kind"):
            writer.add(record)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite"}) + (record,)
        with pytest.raises(ImportRefused, match="supersedes-cross-kind") as caught:
            other.import_bundle(members, **IMPORT)
        assert caught.value.member == record.id

    def _typed_assessment(self, writer, slug: str, target: str):
        """Otherwise valid evidence: an attested, held-shaped dataset, an observing run, and an assessment typed
        under the fixture profile (the estimand lane's constructor requires `estimand` and `applicability`)."""
        from test_evaluation import _address, _resources

        address = _address("a")  # dataset ids are content addresses (slice 5); `dataset_node` takes no slug
        if not writer.read_view.holds(address):
            writer.add(stored.dataset_node(title="d-a", resources=_resources("a"), empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}))
        run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=f"spec-{slug}", observes=[address]))
        return stored.assessment_node(
            slug, title=slug, spec=f"spec-{slug}", run=run.id, proposition=target, outcome="supported", interpretation_rule="rule-1",
            estimand=_estimand(_claim("EX:a", "EX:b")), applicability={},
        )

    def test_an_assessment_targeting_a_composite_is_refused_by_kind_at_add_and_at_import(self, writer, tmp_path):
        composite = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        assessment = self._typed_assessment(writer, "a-x", composite.id)
        # The typed constructor admits it; only the target's kind is wrong.
        assert stored.assessment_value(assessment, profile=writer.profile).proposition == composite.id
        with pytest.raises(SignatureRefused, match="assesses-target-kind"):
            writer.add(assessment)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite", "dataset", "run"}) + (assessment,)
        with pytest.raises(ImportRefused, match="assesses-target-kind"):
            other.import_bundle(members, **IMPORT)

    def test_an_assessment_whose_target_resolves_nowhere_is_refused_at_add_and_at_import(self, writer, tmp_path):
        assessment = self._typed_assessment(writer, "a-y", "composite:future")
        with pytest.raises(SignatureRefused, match="assesses-target-unresolvable"):
            writer.add(assessment)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset", "run"}) + (assessment,)
        with pytest.raises(ImportRefused, match="assesses-target-unresolvable"):
            other.import_bundle(members, **IMPORT)
        # And a target arriving in the same bundle resolves through the union view. The bundle is rebuilt
        # after `ok` exists, so it carries `run:run-a-z` too — eligibility refuses an assessment whose run
        # is in neither the destination nor the bundle.
        ok = self._typed_assessment(writer, "a-z", "proposition:ab")
        bundle = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset", "run"}) + (ok,)
        other.import_bundle(bundle, **IMPORT)
        assert other.read_view.holds("assessment:a-z") and other.read_view.holds("run:run-a-z")

    def test_a_same_kind_supersedes_edge_imports(self, writer, tmp_path):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite"})
        other.import_bundle(members, **IMPORT)
        assert superseded_by(other.read_view, first.id) == (second.id,)
