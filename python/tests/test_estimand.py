"""V2 forms bind complete measured targets, with no v1 authoring route."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
from typing import Any

import pytest
from fixtures_cut3 import (
    MEASUREMENT_RECORDS,
    RESPONSE,
    TESTING_CLAIM,
    TESTING_PROFILE,
    UNCONSULTED,
    FixtureRecords,
)

from beliefs.applicability import Applicability
from beliefs.claim import Member, Referent, build_claim
from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import (
    EstimandError,
    IdentificationNotLicensed,
    ReferenceRefused,
    UnboundReferent,
)
from beliefs.estimand import (
    AxisLevels,
    Control,
    DatasetBinding,
    Estimand,
    IncrementBinding,
    LagBinding,
    NullReference,
    OutputSpec,
    RoleAnchor,
    RoleBinding,
    RoleLevels,
    RoleTermLevels,
    ValueReference,
    build_estimand,
    estimand_from_stored,
    estimand_projection,
)
from beliefs.identity import v1
from beliefs.measurement import Observable
from beliefs.procedure import Procedure
from beliefs.profile import compile_profile
from beliefs.resolution import build_snapshot
from beliefs.restriction import IntervalRestriction


@pytest.fixture()
def context(base_contract, testing_document):
    testing_document["sorts"]["entity"]["categories"].append("class")
    row = dict(testing_document["functionals"]["difference-of-means"])
    testing_document["functionals"]["window-difference-against-control"] = {
        **row,
        "form": "event-locked",
        "increment": "not-applicable",
    }
    testing_document["functionals"]["enrichment-score"] = {
        **row,
        "form": "enrichment",
        "arity": "not-applicable",
        "response_transformation": "fixed",
        "reversal": "not-applicable",
        "response_reversal": "not-applicable",
        "increment": "not-applicable",
        "output": "dimensionless",
    }
    testing_document["functionals"]["power-law-floor"] = {
        **testing_document["functionals"]["arrhenius"],
        "parameters": {"beta": {"typing": "dimensionless", "domain": "real"}},
    }
    testing_document["functionals"]["k-level"] = {**row, "arity": "k"}
    return compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<v2 forms>", base=base_contract, predecessor=None)],
    )


def build(profile=TESTING_PROFILE, claim=TESTING_CLAIM, **overrides):
    fields: dict[str, Any] = {
        "form": "contrast",
        "functional": "testing/difference-of-means",
        "bindings": {
            "response": RESPONSE,
            "grouping": RoleTermLevels(
                "cause", None, (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd"))
            ),
        },
        "outputs": {"estimate": OutputSpec("response-difference", "real")},
        "reference": ValueReference(D(0)),
        "control": Control("testing/randomized", (), "testing/independent-groups", "testing/cohort-enrolment"),
        "uncertainty": "interval",
        "assumptions": (),
        "calibration": None,
        "applicability": Applicability({}),
        "snapshot": UNCONSULTED,
        "records": MEASUREMENT_RECORDS,
    }
    fields.update(overrides)
    return build_estimand(profile, claim, **fields)[0]


@pytest.mark.parametrize(
    "name",
    [
        "difference-of-means",
        "ratio-of-means",
        "probability-of-superiority",
        "hodges-lehmann-shift",
        "log-odds-ratio",
        "spearman-correlation",
        "transfer-entropy",
        "peak-power-fraction",
        "arrhenius",
        "power-law-floor",
        "window-difference-against-control",
        "enrichment-score",
    ],
)
def test_all_worked_forms_and_functional_rows_roundtrip(context, name):
    f = context.functionals["testing/" + name].declaration
    bindings: dict[str, Any] = {"response": RESPONSE}
    if f.form == "contrast":
        bindings["grouping"] = RoleTermLevels(
            "cause", None, (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
        )
    elif f.form == "law-parameters":
        bindings["independent"] = (("temperature", RESPONSE),)
    elif f.form == "association":
        bindings = {
            "variables": (
                ("x", RESPONSE),
                (
                    "y",
                    replace(
                        RESPONSE,
                        role="effect",
                        measure=replace(
                            RESPONSE.measure,
                            observable=Observable("testing/score", "testing/outcome"),
                            unit="testing/point",
                        ),
                    ),
                ),
            )
        }
    elif f.form == "event-locked":
        bindings.update(
            anchor=RoleAnchor("cause", None, Referent("testing/entity", "EX:a")),
            lag=LagBinding(
                "testing/hour",
                (
                    IntervalRestriction("testing/hour", Fraction(0), Fraction(1), True, False),
                    IntervalRestriction("testing/hour", Fraction(1), Fraction(2), True, False),
                ),
            ),
        )
    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    # An independent held yielding procedure is explicit for every different observable.
    if f.form == "association":
        other = bindings["variables"][1][1]
        pid = records.put_procedure(
            Procedure(
                "testing/assay",
                "Score assay",
                "Fixture measurement.",
                (other.measure.observable,),
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
        bindings["variables"] = (("x", RESPONSE), ("y", replace(other, measure=replace(other.measure, procedure=pid))))
    claim = TESTING_CLAIM
    if f.form == "enrichment":
        event = Referent("testing/event", "EX:event")
        product = Referent("testing/product", "EX:product")
        claim = build_claim(
            context,
            operator="testing/correlates-with",
            roles={"parties": (Member(event), Member(product))},
            layer="statistical",
            polarity="positive",
        )
        universe = "sha256:" + "a" * 64
        records.observation_held = lambda digest: digest == universe
        bindings = {
            "membership": RoleBinding("parties", None),
            "reference_set": RoleBinding("parties", product),
            "universe": DatasetBinding(universe),
        }
    outputs = (
        {
            n: OutputSpec(p.typing, p.domain, "testing/energy", "testing/electronvolt")
            if p.typing == "independent"
            else OutputSpec(p.typing, p.domain)
            for n, p in f.parameters.items()
        }
        if f.parameters
        else {"estimate": OutputSpec(f.output, f.domain)}
    )
    reference = (
        {n: ValueReference(D(0)) for n in outputs}
        if f.parameters
        else ValueReference({"one": D(1), "half": D(".5")}.get(f.null, D(0)))
    )
    e = build(
        context,
        claim,
        form=f.form,
        functional="testing/" + name,
        bindings=bindings,
        outputs=outputs,
        reference=reference,
        records=records,
        uncertainty="covariance" if len(outputs) > 1 else "interval",
    )
    assert estimand_from_stored(estimand_projection(e), profile=context) == e
    assert v1.encode(estimand_projection(e))
    assert e.form == f.form


@pytest.mark.parametrize(
    "change",
    [
        {"bindings": {}},
        {"bindings": {"response": RESPONSE}},
        {"form": "quantity"},
        {"outputs": {"wrong": OutputSpec("response-difference", "real")}},
        {"outputs": {"estimate": OutputSpec("dimensionless", "real")}},
        {"reference": NullReference(D(-1), D(1))},
        {"reference": ValueReference(D("NaN"))},
        {"uncertainty": "covariance"},
        {"uncertainty": "guess"},
    ],
)
def test_invalid_form_outputs_reference_and_uncertainty(change):
    with pytest.raises(EstimandError):
        build(**change)


def test_null_regions_and_causal_license():
    null = build_claim(
        TESTING_PROFILE, operator=TESTING_CLAIM.operator, roles=TESTING_CLAIM.roles, layer="causal", form="null"
    )
    assert build(claim=null, reference=NullReference(D(-1), D(1))).reference == NullReference(D(-1), D(1))
    for reference in [ValueReference(D(0)), NullReference(D(1), D(2)), NullReference(D(1), D(-1))]:
        with pytest.raises(ReferenceRefused):
            build(claim=null, reference=reference)
    with pytest.raises(IdentificationNotLicensed):
        build(control=Control("testing/observational", (), "testing/independent-groups", "testing/cohort-enrolment"))


def test_whole_row_admission_not_field_pooling():
    with pytest.raises(EstimandError):
        build(
            control=Control(
                "testing/randomized",
                (Referent("testing/outcome", "EX:y"),),
                "testing/independent-groups",
                "testing/cohort-enrolment",
            )
        )


def test_two_and_k_levels(context):
    grouping = RoleTermLevels("cause", None, tuple(Referent("testing/entity", "EX:" + v) for v in ["a", "b", "c"]))
    with pytest.raises(EstimandError):
        build(context, bindings={"response": RESPONSE, "grouping": grouping})
    assert build(context, functional="testing/k-level", bindings={"response": RESPONSE, "grouping": grouping})
    with pytest.raises(EstimandError):
        build(context, bindings={"response": RESPONSE, "grouping": replace(grouping, levels=grouping.levels[:1])})


def test_role_levels_increment_and_axis_units(context):
    for grouping in [
        IncrementBinding("cause", None, RESPONSE.measure, D(1), "testing/tpm"),
        AxisLevels(
            (
                IntervalRestriction("testing/tpm", Fraction(0), Fraction(1), True, False),
                IntervalRestriction("testing/tpm", Fraction(1), Fraction(2), True, False),
            )
        ),
    ]:
        assert build(context, bindings={"response": RESPONSE, "grouping": grouping})
    with pytest.raises(EstimandError):
        build(
            context,
            bindings={
                "response": RESPONSE,
                "grouping": AxisLevels(
                    (
                        IntervalRestriction("testing/hour", Fraction(0), Fraction(1), True, False),
                        IntervalRestriction("testing/hour", Fraction(1), Fraction(2), True, False),
                    )
                ),
            },
        )
    with pytest.raises(EstimandError):
        build(context, bindings={"response": RESPONSE, "grouping": RoleLevels((RESPONSE,))})  # type: ignore[arg-type]


def test_referent_membership_and_immutability():
    values = {
        "response": RESPONSE,
        "grouping": RoleTermLevels(
            "cause", None, (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
        ),
    }
    with pytest.raises(UnboundReferent):
        build(
            bindings=values,
            snapshot=build_snapshot(readable={TESTING_PROFILE.sorts["testing/entity"].binding: ["EX:a"]}),
        )
    e = build(bindings=values)
    values.clear()
    assert set(e.bindings) == {"response", "grouping"}
    with pytest.raises(TypeError):
        e.bindings["extra"] = RESPONSE  # type: ignore[index]
    with pytest.raises(TypeError):
        e.outputs["other"] = OutputSpec("dimensionless", "real")  # type: ignore[index]


def test_opaque_constructor():
    with pytest.raises(EstimandError):
        Estimand()


def test_event_anchor_requires_a_class_category_role(context):
    with pytest.raises(EstimandError, match="class"):
        build(
            context,
            form="event-locked",
            functional="testing/window-difference-against-control",
            bindings={
                "response": RESPONSE,
                "anchor": RoleAnchor("effect", None, Referent("testing/outcome", "EX:y")),
                "lag": LagBinding("testing/hour", ()),
            },
        )


def test_independent_output_scale_is_a_held_normative_root(context):
    from beliefs.errors import DependencyNotHeld

    with pytest.raises(DependencyNotHeld):
        build(
            context,
            form="law-parameters",
            functional="testing/arrhenius",
            bindings={"response": RESPONSE, "independent": (("x", RESPONSE),)},
            outputs={
                "Ea": OutputSpec("independent", "real", "testing/energy", scale="procedure:" + "f" * 64),
                "lnA": OutputSpec("response-log-level", "real"),
            },
            reference={"Ea": ValueReference(D(0)), "lnA": ValueReference(D(0))},
            uncertainty="covariance",
        )


def test_binding_sequences_must_be_immutable_tuples(context):
    grouping = RoleTermLevels("cause", None, [Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b")])  # type: ignore[arg-type]
    with pytest.raises(EstimandError):
        build(context, bindings={"response": RESPONSE, "grouping": grouping})


def test_axis_rejects_an_unresolved_duration_convention(context):
    levels = tuple(
        IntervalRestriction("testing/tpm", Fraction(i), Fraction(i + 1), True, False, "testing/missing")
        for i in range(2)
    )
    with pytest.raises(EstimandError, match="convention"):
        build(context, bindings={"response": RESPONSE, "grouping": AxisLevels(levels)})
