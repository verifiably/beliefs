"""Closed functional properties control parsing, compilation and conversion."""

import copy
from dataclasses import fields, replace
from typing import Any, cast

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedContract, SuccessionViolation
from beliefs.profile import compile_profile

PROPERTIES = (
    "form",
    "arity",
    "response_transformation",
    "reversal",
    "response_reversal",
    "exchange",
    "ties",
    "output",
    "domain",
    "null",
    "increment",
    "uncertainty",
)
ROWS = {
    "difference-of-means": (
        "contrast",
        "two",
        "equivariant-affine",
        "negate",
        "negate",
        "not-applicable",
        "not-applicable",
        "response-difference",
        "real",
        "zero",
        "linear",
        "exact",
    ),
    "ratio-of-means": (
        "contrast",
        "two",
        "invariant-positive-scaling",
        "reciprocal",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "dimensionless",
        "positive",
        "one",
        "none",
        "exact",
    ),
    "probability-of-superiority": (
        "contrast",
        "two",
        "invariant-strictly-increasing",
        "complement",
        "complement",
        "not-applicable",
        "midrank",
        "dimensionless",
        "unit-interval",
        "half",
        "none",
        "exact",
    ),
    "hodges-lehmann-shift": (
        "contrast",
        "two",
        "equivariant-positive-affine",
        "negate",
        "not-applicable",
        "not-applicable",
        "midrank",
        "response-difference",
        "real",
        "zero",
        "none",
        "exact",
    ),
    "log-odds-ratio": (
        "contrast",
        "two",
        "fixed",
        "negate",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "dimensionless",
        "real",
        "zero",
        "none",
        "exact",
    ),
    "spearman-correlation": (
        "association",
        "two",
        "invariant-strictly-increasing",
        "not-applicable",
        "negate",
        "symmetric",
        "midrank",
        "dimensionless",
        "signed-unit-interval",
        "zero",
        "not-applicable",
        "recompute",
    ),
    "transfer-entropy": (
        "association",
        "two",
        "invariant-strictly-increasing",
        "not-applicable",
        "invariant",
        "directed",
        "undefined",
        "dimensionless",
        "nonnegative",
        "zero",
        "not-applicable",
        "none",
    ),
    "peak-power-fraction": (
        "quantity",
        "one",
        "none",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "dimensionless",
        "unit-interval",
        "none",
        "not-applicable",
        "none",
    ),
    "arrhenius": (
        "law-parameters",
        "not-applicable",
        "by-parameters",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "not-applicable",
        "declared",
        "not-applicable",
        "none",
        "not-applicable",
        "exact",
    ),
}


def declaration(name) -> dict[str, Any]:
    value = dict(zip(PROPERTIES, ROWS[name], strict=True))
    value["parameters"] = (
        {"Ea": {"typing": "independent", "domain": "real"}, "lnA": {"typing": "response-log-level", "domain": "real"}}
        if name == "arrhenius"
        else "not-applicable"
    )
    return value


@pytest.mark.parametrize("name", ROWS)
def test_each_spec_functional_compiles_and_preserves_its_properties(base_contract, testing_document, name):
    from beliefs.comparability import functional_properties

    row = declaration(name)
    testing_document["functionals"] = {name: {**row, "definition": "Editorial prose."}}
    parsed = parse_domain_contract(testing_document, source="<functional>", base=base_contract, predecessor=None)
    compiled = compile_profile(base_contract, [parsed]).functionals[f"testing/{name}"]
    assert compiled.declaration.schema_projection() == row
    assert parsed.claim_vocabulary()[f"functional:{name}"] == row
    runtime = functional_properties(compiled)
    for field in fields(runtime):
        if field.name != "parameters":
            assert getattr(runtime, field.name) == row[field.name]
    if name == "arrhenius":
        assert runtime.parameters is not None
        assert runtime.parameters["Ea"].typing == "independent"
        assert runtime.parameters["lnA"].typing == "response-log-level"
    else:
        assert runtime.parameters is None


@pytest.mark.parametrize(
    ("name", "changes"),
    [
        ("probability-of-superiority", {"reversal": "negate"}),
        ("probability-of-superiority", {"response_reversal": "negate"}),
        ("arrhenius", {"response_transformation": "fixed"}),
        ("arrhenius", {"parameters": "not-applicable"}),
        ("arrhenius", {"parameters": {"p": {"typing": "declared", "domain": "real"}}}),
        ("arrhenius", {"parameters": {"p": {"typing": "independent", "domain": "not-applicable"}}}),
        ("ratio-of-means", {"domain": "real"}),
        ("peak-power-fraction", {"reversal": "negate"}),
        ("spearman-correlation", {"reversal": "invariant"}),
        ("spearman-correlation", {"arity": "one"}),
        ("hodges-lehmann-shift", {"response_reversal": "negate"}),
        ("difference-of-means", {"response_reversal": "not-applicable"}),
        ("difference-of-means", {"arity": "one"}),
        ("difference-of-means", {"exchange": "symmetric"}),
        ("difference-of-means", {"output": "declared"}),
        ("difference-of-means", {"unknown": "value"}),
        ("difference-of-means", {"form": "rank-contrast"}),
    ],
)
def test_invalid_functional_properties_refuse(name, changes):
    from beliefs.contract.functional import parse_functional

    with pytest.raises(MalformedContract):
        parse_functional({**declaration(name), **changes})


@pytest.mark.parametrize("property_name", (*PROPERTIES, "parameters"))
def test_missing_property_refuses(property_name):
    from beliefs.contract.functional import parse_functional

    row = declaration("difference-of-means")
    del row[property_name]
    with pytest.raises(MalformedContract):
        parse_functional(row)


def test_declared_parameters_and_input_mapping_are_immutable():
    from beliefs.contract.functional import parse_functional

    row = declaration("arrhenius")
    parsed = parse_functional(row)
    assert parsed.parameters is not None
    row["parameters"]["Ea"]["typing"] = "dimensionless"
    assert parsed.parameters["Ea"].typing == "independent"
    with pytest.raises(TypeError):
        cast(dict, parsed.parameters)["new"] = parsed.parameters["Ea"]


def test_other_estimand_tables_compile_and_enter_succession(base_contract, testing_document):
    testing_document["identification_classes"] = {"observational": {"licenses_layers": ["statistical"]}}
    testing_document["designs"] = {"independent-groups": {"definition": "Separate groups."}}
    testing_document["selection_mechanisms"] = {"cohort-enrolment": {}}
    parsed = parse_domain_contract(testing_document, source="<functional>", base=base_contract, predecessor=None)
    compiled = compile_profile(base_contract, [parsed])
    assert compiled.identification_classes["testing/observational"].licenses_layers == ("statistical",)
    assert compiled.designs["testing/independent-groups"].contract == "testing"
    assert compiled.selection_mechanisms["testing/cohort-enrolment"].term == "testing/cohort-enrolment"
    assert parsed.claim_vocabulary()["identification-class:observational"] == {"licenses_layers": ["statistical"]}
    successor = copy.deepcopy(testing_document)
    successor["version"] += 1
    successor["lineage"] = {"successor": parsed.content_identity}
    successor["identification_classes"]["observational"]["licenses_layers"] = ["causal"]
    with pytest.raises(SuccessionViolation):
        parse_domain_contract(successor, source="<successor>", base=base_contract, predecessor=parsed)


def test_compiled_estimand_declarations_name_their_kind(base_contract, testing_document):
    parsed = parse_domain_contract(testing_document, source="<functional>", base=base_contract, predecessor=None)
    profile = compile_profile(base_contract, [parsed])
    assert profile.estimands["bridge:testing/promotes"].kind == "bridge"
    assert profile.estimands["instantiation:testing/promotes"].kind == "instantiation"
    assert profile.instantiations["testing/promotes"].kind == "instantiation"


def test_roleless_template_refuses_at_parse(base_contract, testing_document):
    document = {
        "contract": "roleless",
        "version": 1,
        "lineage": "genesis",
        "sorts": {},
        "dimensions": {},
        "templates": {"empty": {"roles": {}, "sign_apt": False, "layers": ["statistical"], "forms": ["polar"]}},
    }
    with pytest.raises(MalformedContract, match="role"):
        parse_domain_contract(document, source="<roleless>", base=base_contract, predecessor=None)


def test_functional_value_copies_parameter_mapping():
    from beliefs.contract.functional import parse_functional

    parsed = parse_functional(declaration("arrhenius"))
    assert parsed.parameters is not None
    parameters = dict(parsed.parameters)
    value = replace(parsed, parameters=parameters)
    parameters.clear()
    assert value.parameters is not None
    assert value.parameters["Ea"].typing == "independent"


@pytest.mark.parametrize(
    ("form", "changes"),
    [
        ("event-locked", {"increment": "not-applicable"}),
        (
            "enrichment",
            {
                "arity": "not-applicable",
                "response_transformation": "fixed",
                "response_reversal": "not-applicable",
                "reversal": "not-applicable",
                "increment": "not-applicable",
            },
        ),
    ],
)
def test_remaining_form_matrix_rows_parse(form, changes):
    from beliefs.contract.functional import parse_functional

    row = {**declaration("difference-of-means"), **changes, "form": form}
    assert parse_functional(row).schema_projection() == row


def test_functional_tables_are_independent_of_activation_order(base_contract, testing_document):
    testing_document["functionals"] = {"probability": declaration("probability-of-superiority")}
    testing = parse_domain_contract(testing_document, source="<testing>", base=base_contract, predecessor=None)
    other = parse_domain_contract(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "functionals": {"shift": declaration("hodges-lehmann-shift")},
        },
        source="<other>",
        base=base_contract,
        predecessor=None,
    )
    a = compile_profile(base_contract, [testing, other])
    b = compile_profile(base_contract, [other, testing])
    assert a.compiled_identity == b.compiled_identity
    assert a.functionals["other/shift"].declaration.response_transformation == "equivariant-positive-affine"
    assert a.estimand_declarations("testing/promotes", ("bridge:testing/promotes",)) == b.estimand_declarations(
        "testing/promotes", ("bridge:testing/promotes",)
    )
