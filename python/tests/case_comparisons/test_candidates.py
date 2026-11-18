"""Candidate genesis, activation, bearer and scope verification (V1–V3, V6)."""

import re

import pytest
from candidate_contracts import (
    CASE_CANDIDATES,
    STATIC,
    candidate_document,
    candidate_history,
    case_profile,
    oracle,
    with_rows,
)

from beliefs import errors
from beliefs.contract.domain import parse_domain_contract
from beliefs.register import register_entry_keys

SOURCES = {
    "mondo": "urn:beliefs:source:mondo-disease-ontology",
    "case-comparisons": "urn:beliefs:definitions:case-outcome-comparison-admissions",
}
KEYS = {
    "mondo": {"sort:mondo/disease"},
    "case-comparisons": {
        "sort:case-comparisons/outcome-class",
        "sort:case-comparisons/case-definition",
        "dimension:case-comparisons/outcome",
        "dimension:case-comparisons/comparator",
        "dimension:case-comparisons/condition",
        "dimension:case-comparisons/case-definition-scope",
        "dimension:case-comparisons/since-infection-onset",
        "dimension:case-comparisons/since-symptom-onset",
        "dimension:case-comparisons/since-treatment-completion",
        "instantiation:case-comparisons/concept-covaries-with-gene",
        "instantiation:case-comparisons/rule-outcome-covaries-with-gene",
        "estimand:instantiation:case-comparisons/concept-covaries-with-gene",
        "estimand:instantiation:case-comparisons/rule-outcome-covaries-with-gene",
    },
}
SORT_MISSING = "roles.parties names sort {sort!r}, but no compiled contract declares sort {sort!r}"
OMISSIONS = [
    (
        "mondo",
        errors.MalformedContract,
        "case-comparisons: dimensions.condition: restriction_sort names sort 'mondo/disease', but no compiled contract declares sort 'mondo/disease'",
    ),
    (
        "biology",
        errors.MalformedContract,
        "case-comparisons: instantiations.concept-covaries-with-gene: " + SORT_MISSING.format(sort="biology/gene"),
    ),
    (
        "si-brochure",
        errors.ProfileError,
        "case-comparisons: restriction names 'si-brochure/duration', which no activated contract declares",
    ),
    (
        "general",
        errors.ProfileError,
        "biology: measurements quantity kind names 'general/relative-abundance', which no activated contract declares",
    ),
]


@pytest.mark.parametrize("namespace", CASE_CANDIDATES)
def test_genesis_matches_its_register_and_oracle(base_contract, namespace):
    revision = candidate_history(namespace, base_contract)
    pins = oracle()
    assert pins["status"].startswith("unshipped candidates")
    (row,) = [row for row in pins["static"] if row["contract_path"].endswith(f"/{namespace}/DOMAIN.yaml")]
    assert revision.contract.content_identity == row["contract_identity"]
    assert revision.contract.defining_source is not None
    assert revision.contract.defining_source.id == SOURCES[namespace]
    assert set(revision.register.entries) == register_entry_keys(revision.contract) == KEYS[namespace]
    assert revision.register.previous is None
    assert {entry.status for entry in revision.register.entries.values()} == {"provisional"}


def test_new_candidates_stay_out_of_the_shared_static_list():
    assert set(CASE_CANDIDATES).isdisjoint(STATIC)


@pytest.mark.parametrize(
    "namespace,table,name,change,message",
    [
        ("case-comparisons", "dimensions", "outcome", None, "drops claim-vocabulary declaration"),
        (
            "case-comparisons",
            "estimands",
            "instantiation:concept-covaries-with-gene",
            None,
            "drops claim-vocabulary declaration",
        ),
        (
            "case-comparisons",
            "sorts",
            "outcome-class",
            {"identifier_class": {"prefix": "outcome-class", "pattern": "outcome-class:[a-z]+"}},
            "different canonical schema projection",
        ),
        (
            "mondo",
            "sorts",
            "disease",
            {"binding": {"kind": "release", "namespace": "mondo", "release": "2026-06-01"}},
            "different canonical schema projection",
        ),
        ("mondo", "sorts", "disease", None, "drops claim-vocabulary declaration"),
    ],
)
def test_a_changed_or_dropped_row_refuses_succession(base_contract, namespace, table, name, change, message):
    genesis = candidate_history(namespace, base_contract).contract
    successor = with_rows(candidate_document(namespace), genesis, {})
    if change is None:
        del successor[table][name]
    else:
        successor[table][name].update(change)
    with pytest.raises(errors.SuccessionViolation, match=message):
        parse_domain_contract(successor, source="<mutated successor>", base=base_contract, predecessor=genesis)


def test_an_unchanged_or_additive_successor_is_accepted(base_contract):
    genesis = candidate_history("mondo", base_contract).contract
    document = candidate_document("mondo")
    unchanged = with_rows(document, genesis, {})
    additive = with_rows(
        document,
        genesis,
        {
            "sorts": {
                "extra": {
                    "binding": {
                        "kind": "scheme",
                        "scheme": "extra",
                        "version": "1",
                    },
                    "identifier_class": {"prefix": "extra", "pattern": "extra:[a-z]+"},
                }
            }
        },
    )
    for successor in (unchanged, additive):
        parse_domain_contract(successor, source="<candidate successor>", base=base_contract, predecessor=genesis)


def test_profile_compiles_with_five_explicit_lineages(base_contract):
    profile = case_profile(base_contract)
    assert set(profile.activated_contracts) == {"general", "biology", "si-brochure", "mondo", "case-comparisons"}
    assert dict(profile.defining_sources) == {"si-brochure": "urn:beliefs:source:bipm-si-brochure", **SOURCES}
    assert profile.claim_dimensions("general/covaries-with") == (
        "case-comparisons/comparator",
        "case-comparisons/outcome",
    )


@pytest.mark.parametrize("omitted,error,message", OMISSIONS)
def test_each_omission_refuses_at_the_first_unresolved_reference(base_contract, omitted, error, message):
    with pytest.raises(error, match=re.escape(message)):
        case_profile(base_contract, omit=(omitted,))


@pytest.mark.parametrize(
    "omitted,instantiation,sort",
    [
        ("mondo", "concept-covaries-with-gene", "mondo/disease"),
        ("biology", "rule-outcome-covaries-with-gene", "biology/gene"),
    ],
)
def test_the_second_reference_refuses_once_the_first_is_removed(base_contract, omitted, instantiation, sort):
    document = candidate_document("case-comparisons")
    if omitted == "mondo":
        del document["dimensions"]["condition"]
    else:
        del document["instantiations"]["concept-covaries-with-gene"]
        del document["estimands"]["instantiation:concept-covaries-with-gene"]
    variant = parse_domain_contract(document, source="<omission variant>", base=base_contract, predecessor=None)
    message = f"instantiations.{instantiation}: " + SORT_MISSING.format(sort=sort)
    with pytest.raises(errors.MalformedContract, match=re.escape(message)):
        case_profile(base_contract, omit=(omitted,), replace={"case-comparisons": variant})


def test_mondo_compiles_without_the_comparison_candidate(base_contract):
    profile = case_profile(base_contract, omit=("case-comparisons",))
    assert "mondo" in profile.activated_contracts
    assert "case-comparisons" not in profile.activated_contracts
