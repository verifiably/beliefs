"""The D §8 membership walk and the §8.1 agreement rule, computed.

What is certified is agreement — not resolution: "the manifest of the corpus
holding the node" needs the index, and corpora exist here as supplied
node→corpus attributions plus per-corpus pins (cut 2 §4.2, D7 row).
"""

from dataclasses import replace
from pathlib import Path

import pytest
from profiles import WITH_BIOLOGY, pins_for

from beliefs.claim import Referent, build_claim
from beliefs.consulted import CorpusPins, consulted_contracts
from beliefs.contract import domain
from beliefs.errors import ContractDisagreement, ContractMismatch, MalformedRecord
from beliefs.profile import compile_profile


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim(profile):
    return build_claim(
        profile=profile,
        operator="testing/affects",
        args=(Referent(sort="testing/entity", term="EX:gene-x"), Referent(sort="testing/outcome", term="EX:pheno-y")),
        qualifiers={},
        polarity="positive",
        layer="causal",
    )


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
    without = consulted_contracts(
        claims={}, profile=profile, node_corpus={}, pins={"c1": ordinary}, closure_nodes=()
    )
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
        assert set(parameters) == {"claims", "profile", "node_corpus", "pins", "closure_nodes", "facets_read"}


class TestSlotSorts:
    @pytest.fixture()
    def crossing_profile(self, base_contract, testing_document):
        import yaml

        path = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "crossing.yaml"
        crossing = domain.parse_domain_contract(
            yaml.safe_load(path.read_text(encoding="utf-8")), source="<crossing>", base=base_contract, predecessor=None
        )
        testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
        return compile_profile(base_contract, [crossing, testing])

    def test_a_claim_reaches_its_slot_sorts_contracts(self, crossing_profile):
        """`affects-local-entity` declares no dimension, so `testing` is
        reached through slot 1's argument sort or not at all."""
        from beliefs.projection import claim_identity

        assert crossing_profile.operator("crossing/affects-local-entity").dimensions == ()
        claim = build_claim(
            profile=crossing_profile,
            operator="crossing/affects-local-entity",
            args=(Referent(sort="crossing/local", term="EX:l"), Referent(sort="testing/entity", term="EX:gene-x")),
            qualifiers={},
            polarity="positive",
            layer="causal",
        )
        uid = claim_identity(claim)
        pins = pins_for(crossing_profile)
        consulted = dict(
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: ("c1",)},
                pins={"c1": CorpusPins(pins.science_contract, dict(pins.domains))},
                closure_nodes=(uid,),
            )
        )
        assert set(consulted) == {"science", "crossing", "testing"}

    def test_a_corpus_pinning_the_operators_contract_only_refuses(self, crossing_profile):
        from beliefs.projection import claim_identity

        claim = build_claim(
            profile=crossing_profile,
            operator="crossing/affects-local-entity",
            args=(Referent(sort="crossing/local", term="EX:l"), Referent(sort="testing/entity", term="EX:gene-x")),
            qualifiers={},
            polarity="positive",
            layer="causal",
        )
        uid = claim_identity(claim)
        pins = pins_for(crossing_profile)
        without_testing = CorpusPins(pins.science_contract, {"crossing": pins.domains["crossing"]})
        with pytest.raises(ContractDisagreement, match="'testing' is consulted but pinned by no corpus"):
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: ("c1",)},
                pins={"c1": without_testing},
                closure_nodes=(uid,),
            )


class TestPinAgreement:
    """Biology pack §5.3a (B7): a consulted namespace's pin must equal the
    validating profile's identity; an unconsulted pin is not compared."""

    def test_the_base_pin_must_agree_with_the_profile(self, profile, pins):
        with pytest.raises(ContractMismatch, match="profile-pin-mismatch: science"):
            consulted_contracts(
                claims={}, profile=profile, node_corpus={}, pins={"c1": pins(science="science:" + "0" * 64)}, closure_nodes=()
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
            claims={}, profile=profile, node_corpus={}, pins={"c1": pins(unrelated="unrelated:" + "2" * 64)}, closure_nodes=()
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
