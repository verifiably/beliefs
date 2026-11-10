"""Measurement declarations preserve authored coefficients and compile explicit routes."""

import copy
from fractions import Fraction

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedContract, ProfileError, SuccessionViolation
from beliefs.profile import compile_profile


@pytest.fixture()
def parse(base_contract):
    def read(document, predecessor=None):
        return parse_domain_contract(document, source="<measurement>", base=base_contract, predecessor=predecessor)

    return read


def test_the_fixture_tables_parse_and_read_as_written(parse, testing_document):
    contract = parse(testing_document)
    assert tuple(
        len(getattr(contract, table))
        for table in ("quantity_kinds", "units", "constants", "conversions", "transformations")
    ) == (10, 16, 1, 7, 8)
    assert contract.quantity_kinds["energy"].dimension == {"M": 1, "L": 2, "T": -2}
    assert contract.constants["avogadro"].value == Fraction(602214076000000000000000)
    assert contract.conversions["hour-to-second"].factor == Fraction(3600)
    assert contract.conversions["kelvin-to-celsius"].offset == Fraction(-5463, 20)
    assert contract.transformations["identity"].fixed is True
    assert contract.transformations["standardize"].fixed is False
    assert contract.transformations["negated-standardize"].direction == "decreasing"


def test_a_unit_naming_an_undeclared_quantity_kind_refuses_at_compile(parse, testing_document, base_contract):
    testing_document["units"]["second"]["quantity_kind"] = "missing"
    contract = parse(testing_document)
    with pytest.raises(ProfileError, match="missing"):
        compile_profile(base_contract, [contract])


def test_a_conversion_between_kinds_needs_a_constant(parse, testing_document, base_contract):
    conversion = testing_document["conversions"]["electronvolt-to-kilojoule-per-mole"]
    del conversion["constant"]
    with pytest.raises(ProfileError, match="constant"):
        compile_profile(base_contract, [parse(testing_document)])
    conversion["constant"] = "avogadro"
    profile = compile_profile(base_contract, [parse(testing_document)])
    assert profile.conversions["testing/electronvolt-to-kilojoule-per-mole"].constant_role == "multiply"
    conversion["from"], conversion["to"] = conversion["to"], conversion["from"]
    profile = compile_profile(base_contract, [parse(testing_document)])
    assert profile.conversions["testing/electronvolt-to-kilojoule-per-mole"].constant_role == "divide"
    testing_document["constants"]["avogadro"]["unit"] = "second"
    with pytest.raises(ProfileError, match="dimensions do not reconcile"):
        compile_profile(base_contract, [parse(testing_document)])


@pytest.mark.parametrize("unit", ["tpm", "item", "unity"])
def test_a_constant_on_a_nonphysical_kind_refuses(parse, testing_document, base_contract, unit):
    testing_document["constants"]["avogadro"]["unit"] = unit
    with pytest.raises(ProfileError, match="dimensions do not reconcile"):
        compile_profile(base_contract, [parse(testing_document)])


def test_a_conversion_within_a_kind_refuses_a_constant(parse, testing_document, base_contract):
    testing_document["conversions"]["hour-to-second"]["constant"] = "avogadro"
    with pytest.raises(ProfileError, match="constant"):
        compile_profile(base_contract, [parse(testing_document)])


def test_two_conversions_joining_one_pair_refuse(parse, testing_document, base_contract):
    testing_document["conversions"]["second-to-hour"] = {
        "from": "second",
        "to": "hour",
        "kind": "multiplicative",
        "factor": "0.0002777777777777778",
        "exact": False,
    }
    with pytest.raises(ProfileError, match="pair"):
        compile_profile(base_contract, [parse(testing_document)])


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("negate", "scale", None),
        ("negate", "offset", None),
        ("log2", "base", None),
        ("logit", "direction", None),
        ("logit", "fixed", None),
        ("identity", "fixed", False),
        ("negate", "fixed", False),
        ("log2", "fixed", False),
        ("identity", "scale", "1"),
        ("negate", "base", "2"),
        ("log2", "direction", "increasing"),
        ("logit", "direction", "sideways"),
        ("identity", "domain", "missing"),
    ],
)
def test_transformation_shapes(parse, testing_document, name, field, value):
    decl = testing_document["transformations"][name]
    if value is None:
        del decl[field]
    else:
        decl[field] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    ("table", "name", "field", "value"),
    [
        ("conversions", "hour-to-second", "factor", "0"),
        ("conversions", "hour-to-second", "factor", "-1"),
        ("transformations", "negate", "scale", "0"),
        ("transformations", "log2", "base", "1"),
        ("transformations", "log2", "base", "0"),
        ("transformations", "log2", "base", "-2"),
        ("constants", "avogadro", "value", "0"),
    ],
)
def test_non_invertible_coefficients_refuse(parse, testing_document, table, name, field, value):
    testing_document[table][name][field] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize("value", [3600, 3.6, True, "NaN", "Infinity", "1/2", " 2", "1_000", "2\n"])
def test_a_yaml_number_or_nondecimal_is_refused(parse, testing_document, value):
    testing_document["conversions"]["hour-to-second"]["factor"] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


def test_a_testing_namespaced_declaration_resolves_with_no_general_contract(parse, testing_document, base_contract):
    profile = compile_profile(base_contract, [parse(testing_document)])
    assert profile.units["testing/second"].quantity_kind == "testing/duration"
    assert profile.constants["testing/avogadro"].unit == "testing/per-mole"
    assert profile.conversions["testing/electronvolt-to-kilojoule-per-mole"].constant == "testing/avogadro"
    assert profile.transformations["testing/log2"].base == Fraction(2)
    assert profile.units["testing/second"].contract == "testing"


def test_the_tables_enter_the_schema_projection_and_succession_keys(parse, testing_document, base_contract):
    prior = parse(testing_document)
    vocabulary = prior.claim_vocabulary()
    assert vocabulary["quantity-kind:duration"] == {"dimension": {"T": 1}}
    assert vocabulary["unit:second"] == {"symbol": "s", "quantity_kind": "duration", "calendar": False}
    assert vocabulary["constant:avogadro"] == {"value": "6.02214076E23", "unit": "per-mole", "exact": True}
    assert vocabulary["conversion:hour-to-second"] == {
        "from": "hour",
        "to": "second",
        "kind": "multiplicative",
        "factor": "3600",
        "exact": True,
    }
    assert vocabulary["transformation:identity"] == {
        "kind": "identity",
        "domain": "real",
        "fixed": True,
        "invertible": True,
    }
    profile = compile_profile(base_contract, [prior])
    projected_units = profile.projection()["units"]
    assert isinstance(projected_units, dict)
    assert projected_units["testing/second"]["quantity_kind"] == "testing/duration"
    edited = copy.deepcopy(testing_document)
    edited["units"]["second"]["definition"] = "An editorial clarification."
    after = parse(edited)
    assert after.claim_vocabulary() == vocabulary
    assert after.content_identity != prior.content_identity  # T2-P28: document identity still covers prose.
    assert compile_profile(base_contract, [after]).compiled_identity == profile.compiled_identity
    edited["version"] += 1
    edited["lineage"] = {"successor": prior.content_identity}
    parse(edited, predecessor=prior)
    edited["conversions"]["hour-to-second"]["factor"] = "3600.0"
    with pytest.raises(SuccessionViolation, match="conversion:hour-to-second"):
        parse(edited, predecessor=prior)


def test_conversion_between_reads_either_direction(parse, testing_document, base_contract):
    profile = compile_profile(base_contract, [parse(testing_document)])
    conversion = profile.conversions["testing/hour-to-second"]
    assert profile.conversion_between("testing/hour", "testing/second") is conversion
    assert profile.conversion_between("testing/second", "testing/hour") is conversion
    assert profile.conversion_between("testing/hour", "testing/kelvin") is None


@pytest.mark.parametrize(
    ("table", "name", "field", "value"),
    [
        ("quantity_kinds", "duration", "dimension", {"X": 1}),
        ("quantity_kinds", "duration", "dimension", {"T": True}),
        ("quantity_kinds", "duration", "dimension", {"T": "1"}),
        ("conversions", "hour-to-second", "offset", "0"),
        ("conversions", "kelvin-to-celsius", "offset", None),
        ("conversions", "hour-to-second", "kind", "unknown"),
        ("conversions", "hour-to-second", "error", "-1"),
        ("constants", "avogadro", "exact", "true"),
        ("units", "second", "symbol", ""),
    ],
)
def test_malformed_measurement_fields_refuse(parse, testing_document, table, name, field, value):
    if value is None:
        del testing_document[table][name][field]
    else:
        testing_document[table][name][field] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    ("table", "name", "field"),
    [
        ("constants", "avogadro", "unit"),
        ("conversions", "hour-to-second", "from"),
        ("conversions", "hour-to-second", "to"),
        ("conversions", "electronvolt-to-kilojoule-per-mole", "constant"),
    ],
)
def test_undeclared_measurement_references_refuse_at_compile(
    parse, testing_document, base_contract, table, name, field
):
    testing_document[table][name][field] = "missing"
    with pytest.raises(ProfileError, match="missing"):
        compile_profile(base_contract, [parse(testing_document)])


@pytest.mark.parametrize(
    ("table", "name"),
    [
        ("quantity_kinds", "duration"),
        ("units", "second"),
        ("constants", "avogadro"),
        ("conversions", "hour-to-second"),
        ("transformations", "identity"),
    ],
)
def test_measurement_tables_do_not_declare_retirement(parse, testing_document, table, name):
    testing_document[table][name]["retired"] = True
    with pytest.raises(MalformedContract, match="unknown field"):
        parse(testing_document)


def test_measurement_references_resolve_across_contracts(parse, testing_document, base_contract):
    testing_document["units"]["second"]["external"] = {"ucum": "s (release 2.2)", "qudt": "unit:SEC (release 3.1)"}
    testing = parse(testing_document)
    other = parse(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "units": {"tick": {"symbol": "tick", "quantity_kind": "testing/duration"}},
            "conversions": {
                "tick-to-second": {
                    "from": "tick",
                    "to": "testing/second",
                    "kind": "multiplicative",
                    "factor": "0.5",
                    "exact": True,
                }
            },
        }
    )
    profile = compile_profile(base_contract, [other, testing])
    assert profile.units["other/tick"].quantity_kind == "testing/duration"
    assert profile.conversions["other/tick-to-second"].to_unit == "testing/second"
    assert profile.conversions["other/tick-to-second"].factor == Fraction(1, 2)
    assert profile.compiled_identity == compile_profile(base_contract, [testing, other]).compiled_identity
    assert testing.units["second"].schema_projection()["external"] == {
        "ucum": "s (release 2.2)",
        "qudt": "unit:SEC (release 3.1)",
    }
    with pytest.raises(TypeError):
        profile.quantity_kinds["testing/duration"].dimension["T"] = 2  # type: ignore[index]


@pytest.mark.parametrize("external", [{"unknown": "ref"}, {"ucum": 1}, {"qudt": ""}, None])
def test_malformed_external_unit_references_refuse(parse, testing_document, external):
    testing_document["units"]["second"]["external"] = external
    with pytest.raises(MalformedContract):
        parse(testing_document)


def test_a_monotone_direction_cannot_be_null(parse, testing_document):
    testing_document["transformations"]["logit"]["direction"] = None
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    "value",
    [
        "1e9999999999999999999",
        "1e-9999999999999999999",
        "1e4097",
        "1e-4097",
        "1e+00004097",
        "1e-00004097",
        "1e" + "9" * 5000,
        "1e-" + "9" * 5000,
        "1" * 4097,
        "0." + "0" * 4095 + "1",
    ],
    ids=[
        "huge-positive-exponent",
        "huge-negative-exponent",
        "positive-exponent-over-limit",
        "negative-exponent-over-limit",
        "padded-positive-over-limit",
        "padded-negative-over-limit",
        "long-positive-exponent",
        "long-negative-exponent",
        "integer-mantissa-over-limit",
        "fractional-mantissa-over-limit",
    ],
)
def test_oversized_coefficients_refuse_before_numeric_construction(parse, testing_document, value):
    testing_document["conversions"]["hour-to-second"]["factor"] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1e4096", Fraction(10**4096)),
        ("1e-4096", Fraction(1, 10**4096)),
        ("1e+00004096", Fraction(10**4096)),
        ("1e-00004096", Fraction(1, 10**4096)),
        ("1e" + "0" * 5000 + "1", Fraction(10)),
        ("1" * 4096, Fraction(int("1" * 4096))),
        ("0." + "0" * 4094 + "1e-4096", Fraction(1, 10**8191)),
    ],
    ids=[
        "positive-exponent-limit",
        "negative-exponent-limit",
        "padded-positive-exponent-limit",
        "padded-negative-exponent-limit",
        "long-padded-small-exponent",
        "integer-mantissa-limit",
        "fractional-mantissa-and-negative-exponent-limit",
    ],
)
def test_supported_coefficient_boundaries_stay_exact_and_keep_authored_text(parse, testing_document, value, expected):
    testing_document["conversions"]["hour-to-second"]["factor"] = value
    conversion = parse(testing_document).conversions["hour-to-second"]
    assert conversion.factor == expected
    assert conversion.schema_projection()["factor"] == value
