"""Verify the synthetic literature route and its limits (V4, V8, V9)."""

# These claims name a gene for a protein result, exposing what this route accepts unchecked.
import re
from hashlib import sha256
from typing import Any, cast

import pytest
from authority import FULL
from candidate_contracts import CASE_CANDIDATES, candidate_history, case_profile
from dataset_fixtures import pinned
from fixtures_cut4 import raw_write, reopen
from lineage_fixtures import derived, plain, production, route
from nodes.core.relations import Relation
from profiles import pins_for
from test_read_side import seed

from beliefs import errors, stored
from beliefs.belief import Availability, NoBelief, SuppliedContext
from beliefs.claim import Qualifier
from beliefs.contract.domain import parse_domain_contract
from beliefs.corpus import lineage_snapshot
from beliefs.decode import claim_from_stored
from beliefs.evaluation import evaluate_over
from beliefs.lineage import certify
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import compile_profile, shipped_domain_contract
from beliefs.projection import claim_identity
from beliefs.resolution import build_snapshot
from beliefs.root import init_corpus_root, open_corpus
from beliefs.source_assertion import source_assertion_from_stored, source_assertion_refusal
from beliefs.world import registry

from .cases import (
    COMPARATOR,
    ORIGINS,
    OUTCOME,
    assertion,
    concept_claim,
    label,
    locator,
    passages,
    portable_writer,
    proposition,
    report_text,
    representation,
    rule_claim,
    source,
)


@pytest.fixture
def profile(base_contract):
    return case_profile(base_contract)


def _rule_proposition(profile):
    return proposition(
        "case-a-rule", rule_claim(profile, "case-a-study", outcome="ptlds", comparator="return-to-health")
    )


def _assertion_node(value):
    return stored.source_assertion_node(value, title="SYNTHETIC reading")


def test_two_positive_visits_bear_on_one_claim(profile):
    src = source(1)
    concept = concept_claim(profile)
    rule = rule_claim(profile, "case-a-study", outcome="ptlds", comparator="return-to-health")
    for slug, claim, indices in (("case-a-concept", concept, (0,)), ("case-a-rule", rule, (0, 1))):
        prop = proposition(slug, claim)
        kinds = {src.id: "source", prop.id: "proposition"}
        values = [assertion(src, prop, n=1, index=i) for i in indices]
        assert len({a.id for a in values}) == len(indices)
        assert len({a.read.representation for a in values}) == 1
        assert len({a.read.span.locator for a in values}) == len(indices)
        for value in values:
            node = _assertion_node(value)
            assert node.id == value.id
            assert value.bears_on.proposition == prop.id
            assert source_assertion_refusal(value, node.relations, kind_of=kinds.get) is None
            assert stored.source_assertion_value(node) == value
            assert source_assertion_from_stored(value.facet(), value.relations()) == value
        back, _ = claim_from_stored(prop, profile=profile, snapshot=build_snapshot(readable={}))
        assert claim_identity(back) == claim_identity(claim)


def test_time_and_specimen_cannot_enter_the_claim(profile):
    assert profile.claim_dimensions("general/covaries-with") == (COMPARATOR, OUTCOME)
    with pytest.raises(errors.DimensionNotClaimSide, match="is placed 'applicability'"):
        concept_claim(profile, qualifiers={ORIGINS["treatment"]: Qualifier("generic", label("x"))})


def test_one_assertion_is_added_on_the_real_engine(certified_work, profile):
    root = certified_work / "corpus"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    src, prop = source(1), _rule_proposition(profile)
    value = assertion(src, prop, n=1)
    for node in (src, prop, _assertion_node(value)):
        assert writer.add(node).id == node.id
    assert stored.source_assertion_value(writer.read_view.get(value.id)) == value


def test_assertions_move_no_belief_output(tmp_path, profile):
    pins = pins_for(profile)
    (tmp_path / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, "c1" + "0" * 30, pins)))
    src, prop = source(1), _rule_proposition(profile)
    raw_write(tmp_path, prop)

    def evaluate():
        view = reopen(tmp_path)
        return evaluate_over(
            view,
            prop.id,
            availability=Availability(
                observations={},
                implementations={BELIEF_V1.identity: BELIEF_V1},
                fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
            ),
            context=SuppliedContext(
                snapshot=lineage_snapshot(view, ()),
                producer_snapshot_identity="producer-snapshot-1",
                node_corpus={},
                pins={"c1": pins},
            ),
            profile=profile,
            resolution=build_snapshot(readable={}),
            binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        )

    before = evaluate()
    raw_write(tmp_path, src)
    for index in (0, 1):
        raw_write(tmp_path, _assertion_node(assertion(src, prop, n=1, index=index)))
    assert evaluate() == before == NoBelief("no-eligible-assessment")


def test_fixture_sources_and_quotes_are_synthetic():
    for n in range(1, 5):
        assert source(n).facets["source"]["identifiers"]["doi"].startswith("10.5555/")
        for i, passage in enumerate(passages(n)):
            assert passage.startswith("SYNTHETIC")
            assert locator(n, i).startswith("SYNTHETIC")


def test_each_quote_occurs_in_its_representation():
    # The kernel cannot check the span against these bytes. The fixture can.
    for n in range(1, 5):
        document = report_text(n)
        assert all(passage.encode() in document for passage in passages(n))
        assert representation(n).sha256 == sha256(document).hexdigest()


def test_four_sources_give_four_unrelated_records(profile):
    prop = proposition("case-a-concept", concept_claim(profile))
    nodes = [_assertion_node(assertion(source(n), prop, n=n)) for n in range(1, 5)]
    assert len({node.id for node in nodes}) == 4
    for n, node in enumerate(nodes, start=1):
        assert [(r.predicate, r.target) for r in node.relations] == [("anchored_in", source(n).id)]


def test_the_assertion_id_excludes_its_source(profile):
    # This collision probe deliberately attributes one reading to different sources.
    prop = _rule_proposition(profile)
    a, b = (assertion(source(n), prop, n=1) for n in (1, 2))
    assert a.source != b.source
    assert a.id == b.id


def test_unrecorded_ancestry_certifies_independent(tmp_path):
    # Two extracts of one synthetic cohort with no recorded ancestry.
    x, y = plain("extract-one"), plain("extract-two")
    view = seed(tmp_path, x, y)
    assert certify(lineage_snapshot(view, [x.id, y.id]), (x.id,), (y.id,)).state == "independent"


def test_a_recorded_common_basis_certifies_shared_source(tmp_path):
    parent = plain("cohort")
    x = derived("extract-one", route("run:make-one", parent.id))
    y = derived("extract-two", route("run:make-two", parent.id))
    view = seed(
        tmp_path, parent, x, y, production("make-one", parent.id, x.id), production("make-two", parent.id, y.id)
    )
    assert certify(lineage_snapshot(view, [x.id, y.id]), (x.id,), (y.id,)).state == "shared-source"


@pytest.mark.parametrize(
    "change,error,message",
    [
        *(
            ({"sign": name}, errors.SignatureRefused, "its closed signatures are ('asserts', 'denies', 'hypothesizes')")
            for name in (
                "tested-no-difference-detected",
                "inconclusive",
                "unreported-at-a-post-treatment-visit",
                "unreported-at-pretreatment",
            )
        ),
        ({"quote": ""}, errors.MalformedRecord, "span.quote: '' must be a non-empty string"),
        ({"extent": "partial"}, errors.MalformedRecord, "outside the closed set ('full', 'abstract')"),
    ],
)
def test_a_result_state_outside_the_three_signs_has_no_record(profile, change, error, message):
    with pytest.raises(error, match=re.escape(message)):
        assertion(source(1), _rule_proposition(profile), n=1, **change)


def test_a_stored_assertion_carries_no_number(profile):
    value = assertion(source(1), _rule_proposition(profile), n=1)
    facet = value.facet()
    cast(dict[str, Any], facet["read"])["estimate"] = 1
    with pytest.raises(errors.MalformedRecord, match=re.escape("unexpected keys ['estimate']")):
        source_assertion_from_stored(facet, value.relations())


def test_an_untyped_proposition_can_carry_an_assertion(tmp_path, profile):
    writer = portable_writer(tmp_path / "corpus", profile)
    src = source(1)
    prop = stored.proposition_node("untyped", title="SYNTHETIC untyped", claim={"operator": "affects"})
    with pytest.raises(errors.MalformedWireClaim):
        claim_from_stored(prop, profile=profile, snapshot=build_snapshot())
    value = assertion(src, prop, n=1)
    for node in (src, prop, _assertion_node(value)):
        writer.add(node)
    assert stored.source_assertion_value(writer.read_view.get(value.id)) == value


def test_a_member_of_edge_on_a_source_is_not_checked(tmp_path, profile):
    writer = portable_writer(tmp_path / "corpus", profile)
    held, unheld = plain("held"), plain("unheld")
    writer.add(held)
    assert not writer.read_view.holds(unheld.id)
    for n, target in enumerate((held.id, unheld.id), start=1):
        src = source(n)
        edge = Relation(source=src.id, predicate="member_of", target=target)
        node = stored.stamp_semantic_identity(src.model_copy(update={"relations": [edge]}))
        assert writer.add(node).id == src.id
        assert list(writer.read_view.get(src.id).relations) == [edge]


def test_a_facet_reference_to_a_dataset_does_not_reach_independence(tmp_path, base_contract):
    # In-memory probe apparatus for the existing facet route.
    probe = parse_domain_contract(
        {
            "contract": "probe-cohorts",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "facets": {
                "cohort-link": {
                    "attaches_to": ["source", "dataset"],
                    "fields": {"family": {"type": "ref", "required": True, "kinds": ["dataset"]}},
                },
            },
        },
        source="<cohort probe>",
        base=base_contract,
        predecessor=None,
    )
    domains = [shipped_domain_contract(name) for name in ("general", "biology", "si-brochure")]
    domains.extend(candidate_history(name, base_contract).contract for name in CASE_CANDIDATES)
    writer = portable_writer(tmp_path / "corpus", compile_profile(base_contract, [*domains, probe]))
    family = plain("cohort-family")
    writer.add(family)
    facet = {"probe-cohorts/cohort-link": {"family": family.id}}
    x, y = (
        stored.dataset_node(title=token, resources=pinned(token), domain_facets=facet)
        for token in ("extract-one", "extract-two")
    )
    for dataset in (x, y):
        writer.add(dataset)
        assert (
            writer.read_view.get(dataset.id).facets["probe-cohorts/cohort-link"] == facet["probe-cohorts/cohort-link"]
        )
    snapshot = lineage_snapshot(writer.read_view, [x.id, y.id])
    assert certify(snapshot, (x.id,), (y.id,)).state == "independent"
    src = source(1)
    node = stored.stamp_semantic_identity(src.model_copy(update={"facets": {**src.facets, **facet}}))
    assert writer.add(node).id == src.id
    assert writer.read_view.get(src.id).facets["probe-cohorts/cohort-link"] == facet["probe-cohorts/cohort-link"]
