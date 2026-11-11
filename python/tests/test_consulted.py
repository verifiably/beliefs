"""The membership walk and the agreement rule, computed.

What is certified is agreement — not resolution: "the manifest of the corpus
holding the node" needs the index, and corpora exist here as supplied
node→corpus attributions plus per-corpus pins.
"""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from fixtures_cut3 import typed_target
from profiles import WITH_BIOLOGY, biology, pins_for

from beliefs.claim import Referent, build_claim
from beliefs.consulted import CorpusPins, assessed_target_contracts, claim_contracts, consulted_contracts
from beliefs.contract import domain
from beliefs.errors import ContractDisagreement, ContractMismatch, MalformedRecord
from beliefs.estimand import RoleTermLevels
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


ENTITY_OUTCOME = {
    "cause": Referent(sort="testing/entity", term="EX:gene-x"),
    "effect": Referent(sort="testing/outcome", term="EX:pheno-y"),
}
ENTITY_LOCAL = {
    "cause": Referent(sort="testing/entity", term="EX:gene-x"),
    "effect": Referent(sort="crossing/local-entity", term="EX:local-1"),
}


def _affects(profile, roles=ENTITY_OUTCOME, **qualifiers):
    return build_claim(
        profile=profile,
        operator="testing/affects",
        roles=roles,
        qualifiers=qualifiers,
        polarity="positive",
        layer="causal",
    )


@pytest.fixture()
def claim(profile):
    return _affects(profile)


@pytest.fixture()
def pins(profile):
    def _pins(**overrides: str) -> CorpusPins:
        real = pins_for(profile)
        return CorpusPins(
            science_contract=overrides.get("science", real.science_contract),
            domains={**real.domains, **{k: v for k, v in overrides.items() if k != "science"}},
        )

    return _pins


def test_an_activated_coordination_contract_is_never_a_belief_input(profile, pins):
    ordinary = pins()
    with_coordination = CorpusPins(
        science_contract=ordinary.science_contract,
        domains={**ordinary.domains, "coordination": "coordination:" + "c" * 64},
    )
    without = consulted_contracts(claims={}, profile=profile, node_corpus={}, pins={"c1": ordinary}, closure_nodes=())
    with_pin = consulted_contracts(
        claims={},
        profile=profile,
        node_corpus={},
        pins={"c1": with_coordination},
        closure_nodes=(),
    )
    assert with_pin == without
    assert "coordination" not in dict(with_pin)


def test_one_identity_held_in_two_corpora_consults_both_and_refuses_disagreement(profile, pins):
    same = pins()
    other = replace(same, science_contract="science:" + "0" * 64)
    node_corpus = {"a" * 64: ("c1", "c2")}

    consulted = consulted_contracts(
        claims={},
        profile=profile,
        node_corpus=node_corpus,
        pins={"c1": same, "c2": same},
        closure_nodes=("a" * 64,),
    )
    assert consulted[0][0] == "science"

    with pytest.raises(ContractDisagreement):
        consulted_contracts(
            claims={},
            profile=profile,
            node_corpus=node_corpus,
            pins={"c1": same, "c2": other},
            closure_nodes=("a" * 64,),
        )


class TestTheWalk:
    def test_the_base_contract_is_unconditional(self, profile, pins):
        consulted = consulted_contracts(
            claims={}, profile=profile, node_corpus={}, pins={"c1": pins()}, closure_nodes=()
        )
        assert ("science", pins_for(profile).science_contract) in consulted

    def test_a_claim_reaches_its_contract_through_the_operator(self, profile, claim, pins):
        from beliefs.projection import claim_identity

        consulted = consulted_contracts(
            claims={claim_identity(claim): claim},
            profile=profile,
            node_corpus={claim_identity(claim): ("c1",)},
            pins={"c1": pins()},
            closure_nodes=(claim_identity(claim),),
        )
        assert ("testing", pins_for(profile).domains["testing"]) in consulted

    def test_an_activated_but_unread_namespace_stays_out(self, profile, pins):
        with_extra = pins(unrelated="u1")
        consulted = consulted_contracts(
            claims={}, profile=profile, node_corpus={}, pins={"c1": with_extra}, closure_nodes=()
        )
        assert all(namespace != "unrelated" for namespace, _ in consulted)

    def test_a_node_attributed_to_a_corpus_with_no_pins_is_malformed(self, profile, pins):
        with pytest.raises(MalformedRecord, match="c2"):
            consulted_contracts(
                claims={},
                profile=profile,
                node_corpus={"n1": ("c2",)},
                pins={"c1": pins()},
                closure_nodes=("n1",),
            )


class TestAgreement:
    def test_two_corpora_pinning_different_identities_for_one_namespace_refuse(self, profile, claim, pins):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        with pytest.raises(ContractDisagreement):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: ("c1",), "other-node": ("c2",)},
                pins={"c1": pins(testing="t-v1"), "c2": pins(testing="t-v2")},
                closure_nodes=(uid, "other-node"),
            )

    def test_a_namespace_pinned_by_no_corpus_refuses_with_a_distinct_message(self, profile, claim):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        unpinned = CorpusPins(science_contract=pins_for(profile).science_contract, domains={})
        with pytest.raises(ContractDisagreement, match="pinned by no corpus"):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: ("c1",)},
                pins={"c1": unpinned},
                closure_nodes=(uid,),
            )

    def test_science_contract_agreement_is_unconditional(self, profile, pins):
        # No base-profile facet is read anywhere in this closure; the corpora
        # still must pin one science_contract.
        with pytest.raises(ContractDisagreement):
            consulted_contracts(
                claims={},
                profile=profile,
                node_corpus={"n1": ("c1",), "n2": ("c2",)},
                pins={"c1": pins(science="base-1"), "c2": pins(science="base-2")},
                closure_nodes=("n1", "n2"),
            )

    def test_agreement_is_never_resolved_by_recency(self, profile):
        # There is no ordering input at all: the signature takes no dates and
        # no priority — disagreement has exactly one outcome.
        import inspect

        parameters = inspect.signature(consulted_contracts).parameters
        assert set(parameters) == {
            "claims",
            "targets",
            "profile",
            "node_corpus",
            "pins",
            "closure_nodes",
            "facets_read",
            "collectors",
        }


def _parse(base_contract, document, source):
    return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=None)


def _crossing_document():
    import yaml

    path = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "crossing.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _walk(profile, claims, targets=None, pins=None):
    real = pins_for(profile)
    return dict(
        consulted_contracts(
            claims=claims,
            targets={ref: (proposition, typed_target(estimand=e)) for ref, (proposition, e) in (targets or {}).items()},
            profile=profile,
            node_corpus={},
            pins={"c1": pins or CorpusPins(real.science_contract, dict(real.domains))},
            closure_nodes=(),
        )
    )


def _estimand(profile, claim, *, aspect=None):
    from fixtures_cut3 import MEASUREMENT_RECORDS, RESPONSE, typed_estimand

    from beliefs.measurement import Aspect
    from beliefs.procedure import Procedure

    measured = RESPONSE.measure
    if aspect is not None:
        measured = replace(measured, observable=replace(measured.observable, aspect=Aspect(aspect, "EX:m")))
        pid = MEASUREMENT_RECORDS.put_procedure(
            Procedure(
                "testing/assay",
                "Aspect assay",
                "Measure.",
                (measured.observable,),
                None,
                {},
                (),
                (),
                None,
                None,
                {},
                None,
            )
        )
        measured = replace(measured, procedure=pid)
    return typed_estimand(
        profile=profile,
        claim=claim,
        bindings={
            "response": replace(RESPONSE, measure=measured),
            "grouping": RoleTermLevels(
                "cause", None, (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
            ),
        },
    )


class TestRoleSorts:
    @pytest.fixture()
    def crossing_profile(self, base_contract, testing_document):
        crossing = _parse(base_contract, _crossing_document(), "<crossing>")
        testing = _parse(base_contract, testing_document, "<test>")
        return compile_profile(base_contract, [crossing, testing])

    def test_walk_reaches_admitting_instantiations_and_sorts(self, base_contract, testing_document, crossing_profile):
        """Case 12: `crossing` instantiates `testing`'s template; a claim it
        admits reads both namespaces."""
        claim = _affects(crossing_profile, ENTITY_LOCAL)
        assert crossing_profile.admitting(claim.operator, claim.assignment(), authoring=False) == (
            "instantiation:crossing/affects-local-entity",
        )
        assert set(_walk(crossing_profile, {claim_identity(claim): claim})) == {"science", "crossing", "testing"}

        # The admitting-instantiation arm alone: `crossing` instantiates `affects`
        # over `testing`'s own sorts, so a claim over those sorts reaches
        # `crossing` through that instantiation and through nothing else.
        document = _crossing_document()
        document["instantiations"]["affects-testing-sorts"] = {
            "template": "testing/affects",
            "roles": {"cause": ["testing/entity"], "effect": ["testing/outcome"]},
        }
        widened = compile_profile(
            base_contract,
            [_parse(base_contract, document, "<crossing+>"), _parse(base_contract, testing_document, "<t>")],
        )
        over_testing = _affects(widened)
        assert "instantiation:crossing/affects-testing-sorts" in widened.admitting(
            over_testing.operator, over_testing.assignment(), authoring=False
        )
        assert claim_contracts(over_testing, widened, over_testing) == {"testing", "crossing"}
        assert claim_contracts(_affects(crossing_profile), crossing_profile, None) == {"testing"}

    def test_a_retired_admitting_instantiation_is_still_consulted(self, base_contract, testing_document):
        """The walk reads the decodable admitting set: a historical claim reads the retired declaration that types it."""
        document = _crossing_document()
        crossing = _parse(base_contract, document, "<crossing>")
        successor = {**document, "lineage": {"successor": crossing.content_identity}}
        successor["instantiations"] = {
            "affects-local-entity": {**document["instantiations"]["affects-local-entity"], "retired": True}
        }
        retired = domain.parse_domain_contract(successor, source="<retired>", base=base_contract, predecessor=crossing)
        testing = _parse(base_contract, testing_document, "<t>")
        live = compile_profile(base_contract, [crossing, testing])
        claim = _affects(live, ENTITY_LOCAL)
        later = compile_profile(base_contract, [retired, testing])
        assert later.admitting(claim.operator, claim.assignment(), authoring=True) == ()
        assert claim_contracts(claim, later, claim) == {"testing", "crossing"}

    def test_within_model_sort_contract_is_consulted(self, base_contract, testing_document):
        """`crossing` declares only the procedure sort here: a claim reaches it
        through its `within-model` referent or not at all."""
        document = _crossing_document()
        document["sorts"]["model"] = {"binding": {"kind": "world-kind", "world_kind": "procedure"}}
        profile = compile_profile(
            base_contract,
            [_parse(base_contract, document, "<crossing>"), _parse(base_contract, testing_document, "<t>")],
        )
        plain = _affects(profile)
        scoped = _affects(
            profile, {**ENTITY_OUTCOME, "within-model": Referent("crossing/model", "procedure:" + "a" * 64)}
        )
        assert "crossing" not in _walk(profile, {"p": plain})
        assert set(_walk(profile, {"p": scoped})) == {"science", "testing", "crossing"}

    def test_a_qualifier_reaches_its_dimension_and_restriction_sort(self, crossing_profile):
        from beliefs.claim import Qualifier

        scoped = _affects(
            crossing_profile,
            ENTITY_OUTCOME,
            **{"crossing/scope": Qualifier("generic", Referent("testing/cohort", "EX:adults"))},
        )
        assert claim_contracts(scoped, crossing_profile, scoped) == {"testing", "crossing"}
        assert claim_contracts(_affects(crossing_profile), crossing_profile, None) == {"testing"}

    def test_disagreeing_closure_refuses(self, base_contract, testing_document, crossing_profile):
        """The agreement rule is unchanged over the widened set: `crossing`,
        reached through the admitting instantiation and the role sort, refuses
        when two corpora pin it differently."""
        claim = _affects(crossing_profile, ENTITY_LOCAL)
        uid = claim_identity(claim)
        real = pins_for(crossing_profile)
        other = CorpusPins(real.science_contract, {**real.domains, "crossing": "crossing:" + "0" * 64})
        with pytest.raises(ContractDisagreement, match="'crossing' resolves to"):
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: ("c1",), "other-node": ("c2",)},
                pins={"c1": real, "c2": other},
                closure_nodes=(uid, "other-node"),
            )

    def test_a_corpus_pinning_the_operators_contract_only_refuses(self, crossing_profile):
        claim = _affects(crossing_profile, ENTITY_LOCAL)
        uid = claim_identity(claim)
        pins = pins_for(crossing_profile)
        without_crossing = CorpusPins(pins.science_contract, {"testing": pins.domains["testing"]})
        with pytest.raises(ContractDisagreement, match="'crossing' is consulted but pinned by no corpus"):
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: ("c1",)},
                pins={"c1": without_crossing},
                closure_nodes=(uid,),
            )


class TestEstimandPairing:
    """P5 and P14: each estimand is paired with the claim of its assessment's
    target, never with the claim its own `claim` field names."""

    @pytest.fixture()
    def crossing_profile(self, base_contract, testing_document):
        crossing = _parse(base_contract, _crossing_document(), "<crossing>")
        testing = _parse(base_contract, testing_document, "<test>")
        return compile_profile(base_contract, [crossing, testing])

    def test_estimand_declaration_contract_is_consulted_with_claim(self, crossing_profile):
        local = _affects(crossing_profile, ENTITY_LOCAL)
        estimand = _estimand(crossing_profile, local)
        assert "crossing" in assessed_target_contracts(typed_target(estimand=estimand), crossing_profile, local)
        assert "crossing" not in assessed_target_contracts(typed_target(estimand=estimand), crossing_profile, None)

        # `crossing`'s declaration carries exactly these fields, but its
        # instantiation does not admit an entity→outcome claim.
        plain = _affects(crossing_profile)
        over_plain = _estimand(crossing_profile, plain)
        assert assessed_target_contracts(typed_target(estimand=over_plain), crossing_profile, plain) == {"testing"}
        assert assessed_target_contracts(typed_target(estimand=over_plain), crossing_profile, None) == {"testing"}

    def test_claimless_walk_reaches_no_declaration(self, crossing_profile):
        local = _affects(crossing_profile, ENTITY_LOCAL)
        estimand = _estimand(crossing_profile, local)
        claimless = _walk(crossing_profile, {}, {"a1": ("p", estimand)})
        assert set(claimless) == {"science", "testing"}  # operator and referent sorts only
        assert set(_walk(crossing_profile, {"p": local}, {"a1": ("p", estimand)})) == {"science", "testing", "crossing"}

    def test_unadmitted_estimand_in_walk_is_malformed(self, profile, claim):
        # Shape-valid, but neither `affects` declaration admits level sort
        # `level` with measure `outcome` in full.
        from beliefs.estimand import estimand_from_stored, estimand_projection

        # Stored shape may carry a conditioning sort admitted only by another row.
        body = estimand_projection(_estimand(profile, claim))
        cast(dict, body["control"])["conditioning"] = [{"sort": "testing/outcome", "term": "EX:y"}]
        unadmitted = estimand_from_stored(body, profile=profile)
        with pytest.raises(MalformedRecord, match="a1: the estimand is not admitted"):
            _walk(profile, {"p": claim}, {"a1": ("p", unadmitted)})

    def test_mismatched_claim_identity_is_malformed_not_claimless(self, profile, claim):
        other = _affects(
            profile,
            {"cause": Referent("testing/entity", "EX:other"), "effect": Referent("testing/outcome", "EX:pheno-y")},
        )
        estimand = _estimand(profile, other)  # its `claim` is another well-formed digest
        assert estimand.claim == claim_identity(other) != claim_identity(claim)
        with pytest.raises(MalformedRecord, match="different claim"):
            _walk(profile, {"p": claim}, {"a1": ("p", estimand)})
        assert set(_walk(profile, {}, {"a1": ("p", estimand)})) == {"science", "testing"}

    def test_collectors_ignore_foreign_artefacts(self, profile, claim):
        estimand = _estimand(profile, claim)
        assert claim_contracts(estimand, profile, None) == frozenset()
        assert assessed_target_contracts(claim, profile, claim) == frozenset()

    def test_every_collector_runs_over_every_paired_artefact(self, profile, claim):
        estimand = _estimand(profile, claim)
        seen: list[tuple[str, str]] = []

        def recording(artefact, _profile, paired):
            seen.append((type(artefact).__name__, type(paired).__name__))
            return frozenset()

        consulted_contracts(
            claims={"p": claim},
            targets={"a1": ("p", typed_target(estimand=estimand)), "a2": ("q", typed_target(estimand=estimand))},
            profile=profile,
            node_corpus={},
            pins={"c1": pins_for(profile)},
            closure_nodes=(),
            collectors=(recording, recording),
        )
        assert sorted(seen) == sorted(
            [("Claim", "Claim")] * 2 + [("AssessedTarget", "Claim")] * 2 + [("AssessedTarget", "NoneType")] * 2
        )


class TestPinAgreement:
    """A consulted namespace's pin must equal the
    validating profile's identity; an unconsulted pin is not compared."""

    def test_the_base_pin_must_agree_with_the_profile(self, profile, pins):
        with pytest.raises(ContractMismatch, match="profile-pin-mismatch: science"):
            consulted_contracts(
                claims={},
                profile=profile,
                node_corpus={},
                pins={"c1": pins(science="science:" + "0" * 64)},
                closure_nodes=(),
            )

    def test_a_consulted_namespace_pinned_to_another_identity_refuses(self, profile, claim, pins):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        with pytest.raises(ContractMismatch, match="profile-pin-mismatch: testing"):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: ("c1",)},
                pins={"c1": pins(testing="testing:" + "1" * 64)},
                closure_nodes=(uid,),
            )

    def test_an_unconsulted_pin_is_not_compared(self, profile, pins):
        consulted = consulted_contracts(
            claims={},
            profile=profile,
            node_corpus={},
            pins={"c1": pins(unrelated="unrelated:" + "2" * 64)},
            closure_nodes=(),
        )
        assert dict(consulted) == {"science": pins_for(profile).science_contract}


def _biology_pins() -> dict[str, CorpusPins]:
    p = pins_for(WITH_BIOLOGY)
    return {"c": CorpusPins(p.science_contract, dict(p.domains))}


def test_a_read_domain_facet_enters_the_consulted_set():
    consulted = dict(
        consulted_contracts(
            claims={},
            profile=WITH_BIOLOGY,
            node_corpus={"dataset:d": ("c",)},
            pins=_biology_pins(),
            closure_nodes=("dataset:d",),
            facets_read={"dataset:d": ("biology/gene-axis",)},
        )
    )
    assert set(consulted) == {"science", "biology"}


def test_an_unread_activated_domain_stays_out():
    consulted = dict(
        consulted_contracts(
            claims={},
            profile=WITH_BIOLOGY,
            node_corpus={"dataset:d": ("c",)},
            pins=_biology_pins(),
            closure_nodes=("dataset:d",),
            facets_read={},
        )
    )
    assert set(consulted) == {"science"}


def test_an_unnamespaced_facet_read_adds_nothing_beyond_the_base():
    consulted = dict(
        consulted_contracts(
            claims={},
            profile=WITH_BIOLOGY,
            node_corpus={"dataset:d": ("c",)},
            pins=_biology_pins(),
            closure_nodes=("dataset:d",),
            facets_read={"dataset:d": ("empirical-observation",)},
        )
    )
    assert set(consulted) == {"science"}


def test_a_facet_read_outside_the_closure_is_malformed():
    with pytest.raises(MalformedRecord, match="not a closure node"):
        consulted_contracts(
            claims={},
            profile=WITH_BIOLOGY,
            node_corpus={"dataset:d": ("c",)},
            pins=_biology_pins(),
            closure_nodes=("dataset:d",),
            facets_read={"dataset:outside": ("biology/gene-axis",)},
        )


@pytest.fixture()
def measured(base_contract, testing_document):
    """`testing` whose `affects` estimand measures in `measures/assay`, compiled
    beside the `measures` fixture: a contract reached through the estimand and
    through nothing else, so the arm below cannot pass on the claim walk."""
    import copy

    fixture = Path(__file__).resolve().parent / "fixtures" / "measures-fixture.yaml"
    from beliefs.contract.document import load_document

    measures = domain.parse_domain_contract(
        load_document(fixture, source=str(fixture)), source=str(fixture), base=base_contract, predecessor=None
    )
    document = copy.deepcopy(testing_document)
    document["aspects"]["abundance"] = ["measures/assay"]
    testing = domain.parse_domain_contract(document, source="<measured>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing, measures])


def test_an_estimand_reaches_a_contract_no_claim_reaches(measured, claim):

    claim = build_claim(
        profile=measured,
        operator="testing/affects",
        roles=claim.roles,
        qualifiers={},
        polarity="positive",
        layer="causal",
    )
    estimand = _estimand(measured, claim, aspect="measures/assay")
    pins = pins_for(measured)
    claim_only = consulted_contracts(
        claims={"p": claim}, profile=measured, node_corpus={}, pins={"c1": pins}, closure_nodes=()
    )
    with_estimand = consulted_contracts(
        claims={"p": claim},
        targets={"a1": ("p", typed_target(estimand=estimand))},
        profile=measured,
        node_corpus={},
        pins={"c1": pins},
        closure_nodes=(),
    )
    assert "measures" not in dict(claim_only) and dict(with_estimand)["measures"] == pins.domains["measures"]


def test_an_estimand_under_an_unpinned_namespace_refuses(base_contract, testing_document):
    # A cross-contract measure sort pinned by no corpus is `ContractDisagreement`, as an operator's sort would be.
    import copy

    document = copy.deepcopy(testing_document)
    document["aspects"]["abundance"] = ["biology/gene"]
    testing = domain.parse_domain_contract(document, source="<unpinned>", base=base_contract, predecessor=None)
    bio = biology("fixture")
    profile = compile_profile(base_contract, [testing, bio])

    claim = build_claim(
        profile=profile,
        operator="testing/affects",
        roles=ENTITY_OUTCOME,
        qualifiers={},
        polarity="positive",
        layer="causal",
    )
    estimand = _estimand(profile, claim, aspect="biology/gene")
    real = pins_for(profile)
    pins_without_biology = CorpusPins(
        science_contract=real.science_contract, domains={"testing": real.domains["testing"]}
    )
    with pytest.raises(ContractDisagreement, match="'biology' is consulted but pinned by no corpus"):
        consulted_contracts(
            claims={"p": claim},
            targets={"a1": ("p", typed_target(estimand=estimand))},
            profile=profile,
            node_corpus={},
            pins={"c1": pins_without_biology},
            closure_nodes=(),
        )


@pytest.fixture()
def collector_profile(base_contract, testing_document):
    from copy import deepcopy

    extra = deepcopy(testing_document)
    extra["contract"] = "extra"
    for name in ("tpm", "ktpm"):
        extra["units"][name]["quantity_kind"] = "testing/abundance"
    extra["duration_conventions"]["mean-month"]["conversion"] = "testing/mean-month-to-second"
    return compile_profile(
        base_contract,
        [
            domain.parse_domain_contract(doc, source="<collector>", base=base_contract, predecessor=None)
            for doc in (testing_document, extra)
        ],
    )


@pytest.mark.parametrize("field", ["functional", "identification", "design", "selection", "unit", "assumptions"])
def test_each_target_declaration_contract_is_read_without_a_claim(collector_profile, field):
    from fixtures_cut3 import typed_target

    from beliefs.consulted import assessed_target_contracts
    from beliefs.estimand import estimand_from_stored, estimand_projection

    claim = _affects(collector_profile)
    body = estimand_projection(_estimand(collector_profile, claim))
    if field == "functional":
        body["functional"] = "extra/difference-of-means"
    elif field in {"identification", "design", "selection"}:
        control = cast(dict, body["control"])
        control[field] = "extra/" + control[field].partition("/")[2]
    elif field == "unit":
        cast(dict, body["bindings"])["response"]["measure"]["unit"] = "extra/tpm"
    else:
        body["assumptions"] = [
            {
                "kind": "extra/proxy-validity",
                "particulars": {"record": "fixture", "co_scope": "equal", "dimensions": ""},
            }
        ]
    target = typed_target(estimand=estimand_from_stored(body, profile=collector_profile))
    assert "extra" in assessed_target_contracts(target, collector_profile, None)


def test_complete_duration_and_increment_terms_are_pure(collector_profile, monkeypatch):
    from fractions import Fraction

    from fixtures_cut3 import RESPONSE, typed_estimand, typed_target

    from beliefs.applicability import Applicability, ScopedRestriction
    from beliefs.consulted import assessed_target_contracts
    from beliefs.corpus import ReadView
    from beliefs.estimand import IncrementBinding
    from beliefs.restriction import IntervalRestriction
    from beliefs.target import target_terms

    claim = _affects(collector_profile)
    app = Applicability(
        {
            "testing/follow-up": ScopedRestriction(
                "generic",
                IntervalRestriction("testing/calendar-month", Fraction(1), None, True, False, "extra/mean-month"),
            )
        }
    )
    e = typed_estimand(
        profile=collector_profile,
        claim=claim,
        bindings={
            "response": RESPONSE,
            "grouping": IncrementBinding("cause", None, RESPONSE.measure, Decimal(1), "extra/tpm"),
        },
    )
    target = typed_target(estimand=e, applicability=app)

    def fail(*args, **kwargs):
        pytest.fail("pure target collector read a corpus")

    monkeypatch.setattr(ReadView, "get", fail)
    assert {
        "extra/tpm",
        "extra/mean-month",
        "testing/mean-month-to-second",
        "testing/calendar-month",
        "testing/second",
    } <= target_terms(target, collector_profile)
    assert assessed_target_contracts(target, collector_profile, None) == {"testing", "extra"}


def test_copied_authority_kind_and_validation_unit_contracts_need_no_reader(collector_profile, monkeypatch):
    from fractions import Fraction

    from fixtures_cut3 import MEASUREMENT_RECORDS, FixtureRecords, typed_target
    from test_procedure import procedure

    from beliefs import stored
    from beliefs.consulted import assessed_target_contracts
    from beliefs.dependencies import dependency_closure
    from beliefs.procedure import SameAs, Scale
    from beliefs.restriction import IntervalRestriction

    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    authority = stored.procedure_node(
        procedure(
            kind="extra/instrument",
            scale=Scale(Fraction(0), Fraction(1), "higher-is-more"),
            validated_in={
                "testing/follow-up": IntervalRestriction("extra/hour", Fraction(1), Fraction(2), True, False)
            },
        )
    )
    follower = stored.procedure_node(procedure(scale=SameAs(authority.id)))
    records.nodes.update({n.id: n for n in (authority, follower)})
    base = typed_target()
    closure = dependency_closure((*[d.id for d in base.dependencies], follower.id), records, collector_profile)
    target = replace(base, dependencies=closure)
    assert {"extra/instrument", "extra/hour"} <= set(next(d.terms for d in closure if d.id == authority.id))
    monkeypatch.setattr(records, "read", lambda *_: pytest.fail("collector reread frozen dependency"))
    assert assessed_target_contracts(target, collector_profile, None) == {"testing", "extra"}


def test_claimless_bridge_target_reads_its_template_contract(base_contract, testing_document):
    document = _crossing_document()
    document["bridges"] = {
        "local-affects": {
            "template": "testing/affects",
            "mapping": "contextual",
            "roles": {"cause": ["testing/entity"], "effect": ["testing/outcome"]},
        }
    }
    document["estimands"]["bridge:local-affects"] = {"forms": ["contrast"], "conditioning_sorts": ["testing/entity"]}
    profile = compile_profile(
        base_contract,
        [_parse(base_contract, testing_document, "<testing>"), _parse(base_contract, document, "<bridge>")],
    )
    claim = build_claim(
        profile, operator="crossing/local-affects", roles=ENTITY_OUTCOME, layer="causal", polarity="positive"
    )
    e = _estimand(profile, claim)
    target = typed_target(estimand=e)
    from beliefs.consulted import assessed_target_contracts

    assert profile.template_of(profile.operator(e.operator)).contract in assessed_target_contracts(target, profile)
    assert assessed_target_contracts(target, profile) == {"testing", "crossing"}
