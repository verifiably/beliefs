"""Vocabulary declarations validate schemas and survive compilation and succession."""

import copy

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedContract, SuccessionViolation
from beliefs.profile import compile_profile


@pytest.fixture()
def parse(base_contract):
    def read(document, predecessor=None):
        return parse_domain_contract(document, source="<vocabulary>", base=base_contract, predecessor=predecessor)

    return read


def test_vocabulary_readback_and_projection(parse, testing_document, base_contract):
    contract = parse(testing_document)
    assert (len(contract.procedure_kinds), len(contract.aggregation_rules), len(contract.assumption_kinds)) == (5, 2, 4)
    assert contract.procedure_kinds["model-specification"].fills_within_model is True
    assert contract.assumption_kinds["proxy-validity"].particulars == ("record", "co_scope", "dimensions")
    vocabulary = contract.claim_vocabulary()
    assert vocabulary["procedure-kind:assay"] == {"fills_within_model": False}
    assert vocabulary["aggregation-rule:sum"] == {}
    assert vocabulary["assumption-kind:proxy-validity"]["particulars"] == ["co_scope", "dimensions", "record"]
    profile = compile_profile(base_contract, [contract])
    assert profile.aggregation_rules["testing/sum"].contract == "testing"
    assert (
        profile.assumption_kinds["testing/proxy-validity"].collapses
        == contract.assumption_kinds["proxy-validity"].collapses
    )
    edited = copy.deepcopy(testing_document)
    for table, name in [
        ("procedure_kinds", "assay"),
        ("aggregation_rules", "sum"),
        ("assumption_kinds", "proxy-validity"),
    ]:
        edited[table][name]["definition"] = "Editorial prose."
    after = parse(edited)
    assert after.claim_vocabulary() == vocabulary
    assert after.content_identity != contract.content_identity
    assert compile_profile(base_contract, [after]).compiled_identity == profile.compiled_identity
    edited["version"] += 1
    edited["lineage"] = {"successor": contract.content_identity}
    edited["procedure_kinds"]["assay"]["fills_within_model"] = True
    with pytest.raises(SuccessionViolation, match="procedure-kind:assay"):
        parse(edited, predecessor=contract)


@pytest.mark.parametrize("value", ["false", 0, None])
def test_fills_within_model_requires_bool(parse, testing_document, value):
    testing_document["procedure_kinds"]["assay"]["fills_within_model"] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize("value", [[], ["record", "record"], [1], ["bad field"], "record"])
def test_particulars_requires_distinct_field_names(parse, testing_document, value):
    testing_document["assumption_kinds"]["proxy-validity"]["particulars"] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    "table,name", [("procedure_kinds", "assay"), ("aggregation_rules", "sum"), ("assumption_kinds", "proxy-validity")]
)
def test_new_vocabularies_do_not_declare_retirement(parse, testing_document, table, name):
    testing_document[table][name]["retired"] = True
    with pytest.raises(MalformedContract):
        parse(testing_document)


def test_vocabulary_compiles_beside_a_foreign_namespace(parse, testing_document, crossing_document, base_contract):
    testing, crossing = parse(testing_document), parse(crossing_document)
    forward = compile_profile(base_contract, [testing, crossing])
    reverse = compile_profile(base_contract, [crossing, testing])
    assert forward.aggregation_rules["testing/sum"].term == "testing/sum"
    assert forward.procedure_kinds["testing/assay"].fills_within_model is False
    assert forward.projection() == reverse.projection()
    assert forward.compiled_identity == reverse.compiled_identity
