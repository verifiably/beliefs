"""The D §8 membership walk and the §8.1 agreement rule, computed.

What is certified is agreement — not resolution: "the manifest of the corpus
holding the node" needs the index, and corpora exist here as supplied
node→corpus attributions plus per-corpus pins (cut 2 §4.2, D7 row).
"""

import pytest
from profiles import WITH_BIOLOGY, pins_for

from beliefs.claim import Referent, build_claim
from beliefs.consulted import CorpusPins, consulted_contracts
from beliefs.contract import domain
from beliefs.errors import ContractDisagreement, MalformedRecord
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


BASE = "science-contract-id-1"


def pins(domain_id: str = "testing-contract-id-1", science: str = BASE) -> CorpusPins:
    return CorpusPins(science_contract=science, domains={"testing": domain_id})


def test_an_activated_coordination_contract_is_never_a_belief_input(profile):
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


class TestTheWalk:
    def test_the_base_contract_is_unconditional(self, profile):
        consulted = consulted_contracts(
            claims={}, profile=profile, node_corpus={}, pins={"c1": pins()}, closure_nodes=()
        )
        assert ("science", BASE) in consulted

    def test_a_claim_reaches_its_contract_through_the_operator(self, profile, claim):
        from beliefs.projection import claim_identity

        consulted = consulted_contracts(
            claims={claim_identity(claim): claim},
            profile=profile,
            node_corpus={claim_identity(claim): "c1"},
            pins={"c1": pins()},
            closure_nodes=(claim_identity(claim),),
        )
        assert ("testing", "testing-contract-id-1") in consulted

    def test_an_activated_but_unread_namespace_stays_out(self, profile):
        with_extra = CorpusPins(science_contract=BASE, domains={"testing": "t1", "unrelated": "u1"})
        consulted = consulted_contracts(
            claims={}, profile=profile, node_corpus={}, pins={"c1": with_extra}, closure_nodes=()
        )
        assert all(namespace != "unrelated" for namespace, _ in consulted)

    def test_a_node_attributed_to_a_corpus_with_no_pins_is_malformed(self, profile):
        with pytest.raises(MalformedRecord, match="c2"):
            consulted_contracts(
                claims={},
                profile=profile,
                node_corpus={"n1": "c2"},
                pins={"c1": pins()},
                closure_nodes=("n1",),
            )


class TestAgreement:
    def test_two_corpora_pinning_different_identities_for_one_namespace_refuse(self, profile, claim):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        with pytest.raises(ContractDisagreement):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: "c1", "other-node": "c2"},
                pins={"c1": pins("t-v1"), "c2": pins("t-v2")},
                closure_nodes=(uid, "other-node"),
            )

    def test_a_namespace_pinned_by_no_corpus_refuses_with_a_distinct_message(self, profile, claim):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        unpinned = CorpusPins(science_contract=BASE, domains={})
        with pytest.raises(ContractDisagreement, match="pinned by no corpus"):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: "c1"},
                pins={"c1": unpinned},
                closure_nodes=(uid,),
            )

    def test_science_contract_agreement_is_unconditional(self, profile):
        # No base-profile facet is read anywhere in this closure; the corpora
        # still must pin one science_contract.
        with pytest.raises(ContractDisagreement):
            consulted_contracts(
                claims={},
                profile=profile,
                node_corpus={"n1": "c1", "n2": "c2"},
                pins={"c1": pins(science="base-1"), "c2": pins(science="base-2")},
                closure_nodes=("n1", "n2"),
            )

    def test_agreement_is_never_resolved_by_recency(self, profile):
        # There is no ordering input at all: the signature takes no dates and
        # no priority — disagreement has exactly one outcome.
        import inspect

        parameters = inspect.signature(consulted_contracts).parameters
        assert set(parameters) == {"claims", "profile", "node_corpus", "pins", "closure_nodes", "facets_read"}


def _biology_pins() -> dict[str, CorpusPins]:
    p = pins_for(WITH_BIOLOGY)
    return {"c": CorpusPins(p.science_contract, dict(p.domains))}


def test_a_read_domain_facet_enters_the_consulted_set():
    consulted = dict(
        consulted_contracts(
            claims={},
            profile=WITH_BIOLOGY,
            node_corpus={"dataset:d": "c"},
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
            node_corpus={"dataset:d": "c"},
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
            node_corpus={"dataset:d": "c"},
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
            node_corpus={"dataset:d": "c"},
            pins=_biology_pins(),
            closure_nodes=("dataset:d",),
            facets_read={"dataset:outside": ("biology/gene-axis",)},
        )
