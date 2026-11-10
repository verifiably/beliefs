"""A-to-B maps and admission come from declarations, including held crosswalks."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from typing import Any, cast

import pytest
import test_stored
from fixtures_cut3 import TESTING_PROFILE
from fixtures_cut4 import reopen
from functionals_fixture import (
    ARRHENIUS,
    DIFFERENCE_OF_MEANS,
    HODGES_LEHMANN_SHIFT,
    OUTPUT_OF,
    PROBABILITY_OF_SUPERIORITY,
    RATIO_OF_MEANS,
    TRANSFER_ENTROPY,
)
from test_dependencies import Records
from test_eligibility import SnapshotRecords, retract
from test_procedure import AID, OBS, procedure
from test_proxy_model import proxy
from test_stored import _testing_writer

from beliefs import stored
from beliefs.assumptions import AssumptionInstance, check_instance
from beliefs.classification_rule import ClassificationRule
from beliefs.comparability import (
    Binding,
    ComparabilitySnapshot,
    Convertible,
    NotConvertible,
    OutputTyping,
    ParameterTyping,
    Unknown,
    convert,
)
from beliefs.contract.domain import parse_domain_contract
from beliefs.eligibility import ClosureEligibility, Eligible, Ineligible, closure_eligibility
from beliefs.errors import MalformedContract, ProfileError
from beliefs.measurement import Coordinates
from beliefs.procedure import SameAs, Scale
from beliefs.profile import compile_profile
from beliefs.proxy_model import Calibration, Conversion, Crosswalk, Error, ProxySource, ProxyTarget
from beliefs.register import AssumptionsRegister
from beliefs.restriction import RuleRestriction, UnionRestriction


def coords(unit: str | None = "tpm", transformation="identity", value_type="level", *, scale=None):
    term = "testing/" + unit if unit else None
    kind = TESTING_PROFILE.units[term].quantity_kind if term else OBS.quantity_kind
    return Coordinates(kind, term, scale, value_type, "testing/" + transformation)


def snapshot(records=None, *, profile=TESTING_PROFILE, refused=None, extra_reads=()):
    records = records if records is not None else Records()

    def eligibility(id):
        return ClosureEligibility({id: Ineligible("retracted") if id == refused else Eligible()}, (id, *extra_reads))

    return ComparabilitySnapshot(profile, records, eligibility)


def result(a, b, functional=PROBABILITY_OF_SUPERIORITY, *, snap=None, binding: Binding = "certified", output=None):
    return convert(
        a,
        b,
        binding=binding,
        functional=functional,
        output=output or OUTPUT_OF(functional),
        snapshot=snap or snapshot(),
    )


@pytest.mark.parametrize("a,b", [("tpm", "celsius"), ("electronvolt", "kelvin")])
def test_quantity_kind_mismatch(a, b):
    answer = result(coords(a), coords(b))
    assert isinstance(answer, NotConvertible) and answer.reason == "quantity kind"
    assert answer.concerns == (coords(a).quantity_kind, coords(b).quantity_kind)


@pytest.mark.parametrize("typing", ["independent", "response-level"])
def test_a_constant_mediated_conversion_crosses_kinds(typing):
    a, b = coords("electronvolt"), coords("kilojoule-per-mole")
    forward = result(a, b, DIFFERENCE_OF_MEANS, output=OutputTyping(typing, "real"))
    assert isinstance(forward, Convertible)
    assert (forward.map.cls, forward.map.scale, forward.map.offset) == ("affine", Fraction("96.48533212"), 0)
    assert forward.exact is False and forward.error == Fraction("0.0000000005")
    reverse = result(b, a, DIFFERENCE_OF_MEANS, output=OutputTyping(typing, "real"))
    assert isinstance(reverse, Convertible)
    assert reverse.map.scale == 1 / Fraction("96.48533212")
    assert reverse.error == forward.error and reverse.exact is False


def test_a_constant_with_incompatible_dimensions_never_compiles(base_contract, testing_document):
    testing_document["constants"]["avogadro"]["unit"] = "kelvin"
    with pytest.raises(ProfileError):
        compile_profile(
            base_contract,
            [parse_domain_contract(testing_document, source="<bad-constant>", base=base_contract, predecessor=None)],
        )


def test_same_unit_is_identity():
    answer = result(coords(), coords())
    assert isinstance(answer, Convertible)
    assert (answer.map.cls, answer.map.scale, answer.map.offset, answer.map.decreasing) == ("identity", 1, 0, False)
    assert answer.exact is True and answer.error is None


def test_a_declared_conversion_serves_both_directions_and_no_chain_is_derived(base_contract, testing_document):
    for a, b, scale in [("hour", "second", Fraction(3600)), ("second", "hour", Fraction(1, 3600))]:
        answer = result(coords(a), coords(b), DIFFERENCE_OF_MEANS)
        assert isinstance(answer, Convertible) and answer.map.scale == scale and answer.exact
    for name in ("x", "y", "z"):
        testing_document["units"][name] = {"symbol": name, "quantity_kind": "duration", "definition": name}
    for a, b in [("x", "y"), ("y", "z")]:
        testing_document["conversions"][a + "-to-" + b] = {
            "from": a,
            "to": b,
            "kind": "multiplicative",
            "factor": "2",
            "exact": True,
            "definition": "Scale.",
        }
    profile = compile_profile(
        base_contract, [parse_domain_contract(testing_document, source="<chain>", base=base_contract, predecessor=None)]
    )
    answer = result(
        Coordinates("testing/duration", "testing/x", None, "level", "testing/identity"),
        Coordinates("testing/duration", "testing/z", None, "level", "testing/identity"),
        snap=snapshot(profile=profile),
    )
    assert isinstance(answer, NotConvertible) and answer.reason == "no conversion between units"


def authorities(*, calibration=False):
    records = Records()
    a = records.put(procedure(name="A", scale=Scale(Fraction(0), Fraction(10), "higher-is-more")))
    b = records.put(procedure(name="B", scale=Scale(Fraction(0), Fraction(10), "higher-is-less"), compatible_with=(a,)))
    model = proxy(
        source=ProxySource(OBS, a),
        target=ProxyTarget(None, b),
        basis=Calibration(OBS, (AID,), (), None)
        if calibration
        else AssumptionInstance(
            "testing/proxy-validity", {"record": "crosswalk", "co_scope": "equal", "dimensions": ""}
        ),
        crosswalk=Crosswalk(
            {}, Conversion("affine", Fraction(-2), Fraction(10)), Error("standard-error", Fraction("1.4"))
        ),
    )
    return records, a, b, model


def test_scale_against_unit_and_two_authorities_without_crosswalk():
    records, a, b, _ = authorities()
    answer = result(coords(None, scale=a), coords("electronvolt"), snap=snapshot(records))
    assert isinstance(answer, NotConvertible) and answer.reason == "unit against scale"
    answer = result(coords(None, scale=a), coords(None, scale=b), snap=snapshot(records))
    assert isinstance(answer, NotConvertible) and answer.reason == "no conversion between scales"


@pytest.mark.parametrize("refuse", [None, "proxy", "a", "b"])
def test_a_crosswalk_must_be_eligible(refuse):
    records, a, b, model = authorities()
    proxy_id = records.put(model)
    ids = {"proxy": proxy_id, "a": a, "b": b}
    before = snapshot(records)
    expected = result(coords(None, scale=a), coords(None, scale=b), DIFFERENCE_OF_MEANS, snap=before)
    assert isinstance(expected, Convertible)
    assert (expected.map.scale, expected.map.offset, expected.exact, expected.error) == (-2, 10, False, Fraction("1.4"))
    check_instance(TESTING_PROFILE, expected.assumptions[0])
    assert expected.assumptions[0].particulars["error"] == "1.4"
    extra = "classification-rule:" + "e" * 64
    after = snapshot(records, refused=ids[refuse] if refuse else None, extra_reads=(extra,))
    answer = result(coords(None, scale=a), coords(None, scale=b), DIFFERENCE_OF_MEANS, snap=after)
    if refuse:
        assert isinstance(answer, NotConvertible) and answer.reason == "dependency ineligible"
        assert ids[refuse] in answer.concerns
    else:
        assert answer == expected
    assert {a, b, proxy_id, extra} <= set(after.reads)
    assert result(coords(None, scale=a), coords(None, scale=b), DIFFERENCE_OF_MEANS, snap=before) == expected
    inverse = result(coords(None, scale=b), coords(None, scale=a), DIFFERENCE_OF_MEANS, snap=snapshot(records))
    assert isinstance(inverse, Convertible) and (inverse.map.scale, inverse.map.offset) == (Fraction(-1, 2), 5)


def test_a_calibration_crosswalk_fails_closed_without_assessment_eligibility():
    records, a, b, model = authorities(calibration=True)
    id = records.put(model)
    records.nodes[AID] = stored.Node(id=AID, kind="assessment", title="Calibration")
    snap = ComparabilitySnapshot(
        TESTING_PROFILE, records, lambda id: closure_eligibility((id,), records, TESTING_PROFILE)
    )
    answer = result(coords(None, scale=a), coords(None, scale=b), snap=snap)
    assert isinstance(answer, NotConvertible) and answer.reason == "dependency ineligible"
    assert {a, b, id, AID} <= set(snap.reads)


@pytest.mark.parametrize("placement", ["proxy", "authority"])
def test_a_crosswalk_whose_nested_rule_is_retracted_is_ineligible(
    certified_work, placement, base_contract, testing_document, monkeypatch
):
    declaration = testing_document["dimensions"]["case-status"]
    declaration["restriction"] = {"form": "union", "of": declaration["restriction"]}
    profile = compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<convert-union>", base=base_contract, predecessor=None)],
    )
    monkeypatch.setattr(test_stored, "TESTING_PROFILE", profile)
    writer = _testing_writer(certified_work / placement)
    writer.add(
        stored.assumptions_register_node(
            AssumptionsRegister("testing:" + profile.activated_contracts["testing"], None, {})
        )
    )
    rule = writer.add(
        stored.classification_rule_node(ClassificationRule("testing/level", (OBS,), "Classify.", None, None, None))
    )
    scope = {
        "testing/case-status": UnionRestriction(
            (RuleRestriction(rule.id, ("EX:a",)), RuleRestriction(rule.id, ("EX:b",)))
        )
    }
    scale = Scale(Fraction(0), Fraction(100), "higher-is-more")
    a = writer.add(
        stored.procedure_node(procedure(name="A", scale=scale, validated_in=scope if placement == "authority" else {}))
    )
    b = writer.add(stored.procedure_node(procedure(name="B", scale=scale)))
    model = writer.add(
        stored.proxy_model_node(
            proxy(
                source=ProxySource(OBS, a.id),
                target=ProxyTarget(None, b.id),
                validity=scope if placement == "proxy" else {},
                basis=AssumptionInstance(
                    "testing/proxy-validity", {"record": "crosswalk", "co_scope": "equal", "dimensions": ""}
                ),
                crosswalk=Crosswalk(
                    {}, Conversion("affine", Fraction(1), Fraction(0)), Error("standard-error", Fraction(0))
                ),
            )
        )
    )
    before = SnapshotRecords(reopen(writer.root))
    old = ComparabilitySnapshot(profile, before, lambda id: closure_eligibility((id,), before, profile))
    expected = result(coords(None, scale=a.id), coords(None, scale=b.id), snap=old)
    assert isinstance(expected, Convertible)
    retract(writer, rule)
    after = SnapshotRecords(reopen(writer.root))
    new = ComparabilitySnapshot(profile, after, lambda id: closure_eligibility((id,), after, profile))
    answer = result(coords(None, scale=a.id), coords(None, scale=b.id), snap=new)
    assert isinstance(answer, NotConvertible) and answer.reason == "dependency ineligible"
    assert rule.id in answer.concerns and {model.id, a.id, b.id, rule.id} <= set(new.reads)
    assert result(coords(None, scale=a.id), coords(None, scale=b.id), snap=old) == expected


def test_same_as_identity_checks_both_authority_closures_and_records_reads():
    records, a, _, _ = authorities()
    follower = records.put(procedure(name="Follower", scale=SameAs(a)))
    snap = snapshot(records)
    answer = result(coords(None, scale=follower), coords(None, scale=a), snap=snap)
    assert isinstance(answer, Convertible) and answer.map.cls == "identity"
    assert {a, follower} <= set(snap.reads)
    refused = snapshot(records, refused=a)
    answer = result(coords(None, scale=follower), coords(None, scale=a), snap=refused)
    assert isinstance(answer, NotConvertible) and answer.reason == "dependency ineligible"
    assert a in answer.concerns


def test_ratio_across_affine_change():
    answer = result(coords("kelvin", value_type="ratio"), coords("celsius", value_type="ratio"))
    assert isinstance(answer, NotConvertible) and answer.reason == "ratio across affine change"
    answer = result(coords("tpm", value_type="ratio"), coords("ktpm", value_type="ratio"))
    assert isinstance(answer, Convertible) and answer.map.cls == "identity"


def test_difference_drops_the_raw_offset():
    answer = result(
        coords("kelvin", value_type="difference"), coords("celsius", value_type="difference"), DIFFERENCE_OF_MEANS
    )
    assert isinstance(answer, Convertible) and answer.map.cls == "identity"


@pytest.mark.parametrize(
    "ta,tb,cls,decreasing",
    [
        ("identity", "log2-plus-one", "strictly-increasing", False),
        ("log2-plus-one", "log2-plus-one", "identity", False),
        ("standardize", "standardize", "strictly-increasing", False),
        ("negated-standardize", "negated-standardize", "strictly-increasing", False),
        ("negate", "identity", "affine", True),
        ("negate", "negate", "identity", False),
        ("negate", "standardize", "strictly-decreasing", True),
    ],
)
def test_composed_map_classes(ta, tb, cls, decreasing):
    answer = result(coords(transformation=ta), coords(transformation=tb))
    assert isinstance(answer, Convertible) and (answer.map.cls, answer.map.decreasing) == (cls, decreasing)


def test_logarithms_compose_in_a_to_b_direction():
    answer = result(coords(transformation="log2"), coords("ktpm", "log2"))
    assert isinstance(answer, Convertible) and answer.map.cls == "affine" and answer.map.scale == 1
    assert isinstance(answer.map.offset, Decimal)
    assert Decimal("-9.965784284662087044") < answer.map.offset < Decimal("-9.965784284662087043")
    for ta, tb, low, high in [
        ("ln", "log2", "1.44269504088896340", "1.44269504088896341"),
        ("log2", "ln", "0.69314718055994530", "0.69314718055994531"),
    ]:
        answer = result(coords(transformation=ta), coords(transformation=tb), DIFFERENCE_OF_MEANS)
        assert isinstance(answer, Convertible) and answer.map.cls == "affine" and answer.map.offset == 0
        assert isinstance(answer.map.scale, Decimal) and Decimal(low) < answer.map.scale < Decimal(high)


@pytest.mark.parametrize(
    "a,b,reason",
    [
        (coords(transformation="log2-plus-one"), coords("ktpm", "log2-plus-one"), "transformation under unit change"),
        (coords(transformation="logit"), coords(transformation="standardize"), "distinct monotone kinds"),
        (coords(transformation="logit"), coords(transformation="log2"), "distinct monotone kinds"),
        (coords("kelvin", "log2"), coords("celsius", "log2"), "logarithms under offset"),
    ],
)
def test_unknown_maps(a, b, reason):
    answer = result(a, b)
    assert isinstance(answer, Unknown) and answer.reason == reason


def test_domain_containment_is_unknown_under_an_offset():
    answer = result(coords("kelvin", "ln"), coords("celsius"))
    assert isinstance(answer, Unknown) and answer.reason == "domain"


@pytest.mark.parametrize(
    "ta,tb,functional,reason",
    [
        ("identity", "log2-plus-one", HODGES_LEHMANN_SHIFT, "transformation"),
        ("standardize", "standardize", DIFFERENCE_OF_MEANS, "transformation"),
        ("negate", "identity", RATIO_OF_MEANS, "transformation"),
        ("negate", "identity", replace(PROBABILITY_OF_SUPERIORITY, response_reversal="undefined"), "response reversal"),
    ],
)
def test_admission_by_certificate(ta, tb, functional, reason):
    answer = result(coords(transformation=ta), coords(transformation=tb), functional)
    assert isinstance(answer, NotConvertible) and answer.reason == reason


def test_response_reversal_is_separate_from_level_reversal():
    answer = result(coords(transformation="negate"), coords(), TRANSFER_ENTROPY)
    assert isinstance(answer, Convertible) and answer.flip == "invariant"
    answer = result(coords(transformation="negate"), coords())
    assert isinstance(answer, Convertible) and answer.flip == "complement"


def test_by_parameters_admission():
    output = OutputTyping("response-log-level", "real")
    answer = result(coords("per-second"), coords("per-hour"), ARRHENIUS, output=output)
    assert isinstance(answer, Convertible) and answer.map.scale == 3600
    answer = result(coords("kelvin"), coords("celsius"), ARRHENIUS, output=output)
    assert isinstance(answer, NotConvertible) and answer.reason == "transformation"


@pytest.mark.parametrize("unit,admitted", [("millikelvin", False), ("celsius", False), ("kelvin", True)])
def test_independent_binding_admits_identity_only(unit, admitted):
    answer = result(coords("kelvin"), coords(unit), binding="independent")
    if admitted:
        assert isinstance(answer, Convertible) and answer.map.cls == "identity"
    else:
        assert isinstance(answer, NotConvertible) and answer.reason == "independent-variable map"


def test_a_crosswalk_with_error_refuses_undefined_ties():
    records, a, b, model = authorities()
    records.put(model)
    answer = result(coords(None, scale=a), coords(None, scale=b), TRANSFER_ENTROPY, snap=snapshot(records))
    assert isinstance(answer, NotConvertible) and answer.reason == "ties"


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_functional_properties_membership(field):
    with pytest.raises(MalformedContract):
        replace(DIFFERENCE_OF_MEANS, **{field: "foreign"})


@pytest.mark.parametrize(
    "change",
    [
        {"parameters": {}},
        {"output": "declared"},
        {"response_transformation": "by-parameters"},
    ],
)
def test_functional_parameter_coupling(change: dict[str, Any]):
    with pytest.raises(MalformedContract):
        replace(DIFFERENCE_OF_MEANS, **change)


def test_parameter_and_output_typing_membership():
    for cls in (ParameterTyping, OutputTyping):
        with pytest.raises(MalformedContract):
            cls(cast(Any, "foreign"), "real")
        with pytest.raises(MalformedContract):
            cls("independent", cast(Any, "foreign"))


def compile_testing(base_contract, document):
    return compile_profile(
        base_contract,
        [parse_domain_contract(document, source="<convert-domains>", base=base_contract, predecessor=None)],
    )


@pytest.mark.parametrize("side", ["a", "b"])
@pytest.mark.parametrize("base", ["2", "0.5"])
def test_logarithm_against_affine_needs_a_whole_domain_proof(base_contract, testing_document, side, base):
    testing_document["transformations"]["identity"]["domain"] = "positive"
    testing_document["transformations"]["log2"]["base"] = base
    profile = compile_testing(base_contract, testing_document)
    a, b = coords(transformation="log2"), coords()
    if side == "b":
        a, b = b, a
    answer = result(a, b, snap=snapshot(profile=profile))
    assert isinstance(answer, Convertible)
    assert answer.map.cls == ("strictly-increasing" if base == "2" else "strictly-decreasing")
    assert answer.map.decreasing is (base == "0.5")
    # A real-domain identity offers no whole-domain guarantee in either direction.
    answer = result(a, b)
    assert isinstance(answer, Unknown) and answer.reason == "domain"


@pytest.mark.parametrize("offset,expected", [("0", "strictly-increasing"), ("-1", "domain")])
def test_monotone_shared_domain_does_not_assert_unprovided_sample_values(
    base_contract, testing_document, offset, expected
):
    testing_document["conversions"]["tpm-to-ktpm"].update(kind="affine", offset=offset)
    profile = compile_testing(base_contract, testing_document)
    answer = result(coords(), coords("ktpm", "log2-plus-one"), snap=snapshot(profile=profile))
    if expected == "domain":
        assert isinstance(answer, Unknown) and answer.reason == expected
    else:
        assert isinstance(answer, Convertible) and answer.map.cls == expected


def test_negative_raw_map_with_disjoint_positive_domains_is_unknown(base_contract, testing_document):
    testing_document["transformations"]["identity"]["domain"] = "positive"
    testing_document["transformations"]["standardize"]["domain"] = "positive"
    profile = compile_testing(base_contract, testing_document)
    records, a, b, model = authorities()
    model = replace(
        model,
        crosswalk=Crosswalk({}, Conversion("multiplicative", Fraction(-1), None), Error("standard-error", Fraction(0))),
    )
    records.put(model)
    answer = result(
        coords(None, scale=a), coords(None, "standardize", scale=b), snap=snapshot(records, profile=profile)
    )
    assert isinstance(answer, Unknown) and answer.reason == "domain"
    # The same negative raw factor is meaningful on two real domains; sign still applies.
    answer = result(coords(None, scale=a), coords(None, "standardize", scale=b), snap=snapshot(records))
    assert isinstance(answer, Convertible) and answer.map.cls == "strictly-decreasing" and answer.map.decreasing


def test_logarithm_domain_is_not_proven_by_a_positive_offset_alone(base_contract, testing_document):
    testing_document["transformations"]["identity"]["domain"] = "positive"
    testing_document["transformations"]["log2"]["domain"] = "unit-interval"
    testing_document["conversions"]["tpm-to-ktpm"].update(kind="affine", offset="0.1")
    profile = compile_testing(base_contract, testing_document)
    answer = result(coords(), coords("ktpm", "log2"), snap=snapshot(profile=profile))
    assert isinstance(answer, Unknown) and answer.reason == "domain"


def test_affine_coefficients_are_exactly_composed_and_inverted(base_contract, testing_document):
    testing_document["transformations"]["shift-scale"] = {
        "kind": "affine",
        "scale": "2",
        "offset": "3",
        "domain": "real",
        "invertible": True,
        "definition": "Affine.",
    }
    testing_document["transformations"]["other-affine"] = {
        "kind": "affine",
        "scale": "-4",
        "offset": "5",
        "domain": "real",
        "invertible": True,
        "definition": "Affine.",
    }
    profile = compile_testing(base_contract, testing_document)
    a, b = coords(transformation="shift-scale"), coords("ktpm", "other-affine")
    forward = result(a, b, DIFFERENCE_OF_MEANS, snap=snapshot(profile=profile))
    backward = result(b, a, DIFFERENCE_OF_MEANS, snap=snapshot(profile=profile))
    assert isinstance(forward, Convertible) and isinstance(backward, Convertible)
    assert forward.map.scale == Fraction(-1, 500) and forward.map.offset == Fraction(2503, 500)
    assert backward.map.scale == -500 and backward.map.offset == 2503


def test_transcendental_context_does_not_depend_on_the_callers_context():
    from decimal import localcontext

    with localcontext() as context:
        context.prec = 6
        answer = result(coords(transformation="log2"), coords("ktpm", "log2"))
    assert isinstance(answer, Convertible)
    assert isinstance(answer.map.offset, Decimal)
    assert Decimal("-9.965784284662087044") < answer.map.offset < Decimal("-9.965784284662087043")


def test_functional_parameter_mapping_is_frozen():
    parameters = {"x": ParameterTyping("dimensionless", "real")}
    functional = replace(ARRHENIUS, parameters=parameters)
    parameters["x"] = ParameterTyping("response-log-level", "real")
    assert functional.parameters == {"x": ParameterTyping("dimensionless", "real")}


@pytest.mark.parametrize("same_as", [False, True])
def test_an_unheld_scale_dependency_is_a_refusal_with_provenance(same_as):
    records = Records()
    missing = "procedure:" + "f" * 64
    a = records.put(procedure(name="Held authority", scale=Scale(Fraction(0), Fraction(1), "higher-is-more")))
    b = records.put(procedure(name="Follower", scale=SameAs(missing))) if same_as else missing
    snap = ComparabilitySnapshot(
        TESTING_PROFILE, records, lambda id: closure_eligibility((id,), records, TESTING_PROFILE)
    )
    answer = result(coords(None, scale=a), coords(None, scale=b), snap=snap)
    assert isinstance(answer, NotConvertible) and answer.reason == "dependency ineligible"
    assert missing in snap.reads and {a, b} <= set(snap.reads)


def test_a_snapshot_read_uses_the_strict_content_addressed_reader():
    from test_procedure import node_for

    from beliefs.errors import MalformedRecord
    from beliefs.procedure import procedure_projection

    records = Records()
    id = "procedure:" + "f" * 64
    records.nodes[id] = node_for("procedure", id, procedure_projection(procedure()))
    snap = snapshot(records)
    with pytest.raises(MalformedRecord):
        snap.read(id)
    assert snap.reads == (id,)


@pytest.mark.parametrize("factor", [Fraction(-2), Fraction(-3)])
@pytest.mark.parametrize("reverse", [False, True])
def test_distinct_crosswalks_are_ambiguous_even_when_their_maps_agree(factor, reverse):
    from beliefs.errors import MeasurementError

    records, a, b, model = authorities()
    first = records.put(model)
    second = records.put(
        replace(
            model,
            crosswalk=Crosswalk(
                {"population": "other"},
                Conversion("affine", factor, Fraction(10)),
                Error("standard-error", Fraction("1.4")),
            ),
        )
    )
    candidates = (second, first) if reverse else (first, second)
    records.crosswalks = lambda a, b: candidates
    snap = snapshot(records)
    with pytest.raises(MeasurementError, match="ambiguous direct crosswalks") as raised:
        result(coords(None, scale=a), coords(None, scale=b), snap=snap)
    assert type(raised.value).__name__ == "AmbiguousCrosswalk"
    assert str(raised.value).endswith(", ".join(sorted((first, second))))
    assert {a, b} <= set(snap.reads)
    assert not {first, second} & set(snap.reads)


def test_repeated_index_entries_for_one_crosswalk_are_unambiguous():
    records, a, b, model = authorities()
    id = records.put(model)
    records.crosswalks = lambda a, b: (id, id)
    answer = result(coords(None, scale=a), coords(None, scale=b), snap=snapshot(records))
    assert isinstance(answer, Convertible) and answer.map.scale == -2


def test_evaluated_logarithmic_coefficients_stay_decimal_even_for_rational_results(base_contract, testing_document):
    testing_document["transformations"]["base-four"] = {
        "kind": "logarithm",
        "base": "4",
        "domain": "positive",
        "invertible": True,
        "definition": "Logarithm.",
    }
    testing_document["conversions"]["tpm-to-ktpm"]["factor"] = "4"
    profile = compile_testing(base_contract, testing_document)
    base_change = result(
        coords(transformation="base-four"), coords(transformation="log2"), snap=snapshot(profile=profile)
    )
    factor_change = result(coords(transformation="log2"), coords("ktpm", "log2"), snap=snapshot(profile=profile))
    assert isinstance(base_change, Convertible) and isinstance(factor_change, Convertible)
    assert isinstance(base_change.map.scale, Decimal) and isinstance(factor_change.map.offset, Decimal)
    assert (
        Decimal("1.99999999999999999999999999999999")
        < base_change.map.scale
        < Decimal("2.00000000000000000000000000000001")
    )
    assert (
        Decimal("1.99999999999999999999999999999999")
        < factor_change.map.offset
        < Decimal("2.00000000000000000000000000000001")
    )
    assert factor_change.map.scale == Fraction(1) and base_change.map.offset == Fraction(0)
