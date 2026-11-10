"""Binding aptness preserves admission, yield, scale, bearer and validity order."""

from dataclasses import replace
from fractions import Fraction

import pytest
from test_dependencies import Records
from test_procedure import OBS, procedure
from test_proxy_model import CROSSWALK, proxy

from beliefs import errors
from beliefs.aptness import check_aptness
from beliefs.assumptions import AssumptionInstance, check_instance
from beliefs.measurement import Aspect, Measure, Observable
from beliefs.procedure import SameAs, Scale
from beliefs.proxy_model import ProxySource, ProxyTarget
from beliefs.referent_mapping import ReferentMapping
from beliefs.restriction import IntervalRestriction


@pytest.fixture()
def profile(base_contract, testing_document):
    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile

    return compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<aptness>", base=base_contract, predecessor=None)],
    )


BASIS = AssumptionInstance("testing/proxy-validity", {"record": "hypothesis", "co_scope": "unknown", "dimensions": ""})
TARGET = Observable("testing/abundance", "testing/entity")
SCOPE = {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(0), Fraction(10), True, True)}


def setup_binding(*, observable=OBS, target=TARGET, validated_in=None, validity=None, scale=None):
    records = Records()
    proc = procedure(yields=(observable,), scale=scale, validated_in=validated_in or {})
    proc_id = records.put(proc)
    measure = Measure(observable, "testing/electronvolt", None, "ratio", "level", "testing/identity", proc_id)
    p = proxy(
        source=ProxySource(observable, proc_id), target=ProxyTarget(target, None), validity=validity or {}, basis=BASIS
    )
    proxy_id = records.put(p)
    mapping_id = records.put(
        ReferentMapping(observable.bearer_sort, target.bearer_sort, {}, "many-to-one", "testing/mean", None)
    )
    return records, measure, mapping_id, proxy_id


def apt(profile, records, measure, mapping=None, proxy=None, scope=None, role="testing/entity"):
    return check_aptness(profile, role, measure, mapping, proxy, scope or {}, records)


def test_an_unlisted_source_pair_refuses_even_with_proxy_and_mapping(profile):
    records, measure, mapping, proxy_id = setup_binding(observable=Observable("testing/energy", "testing/cohort"))
    with pytest.raises(errors.MeasurementNotAdmitted):
        apt(profile, records, measure, mapping, proxy_id)
    # Admission takes precedence even over unheld procedure/proxy records.
    records.nodes.clear()
    with pytest.raises(errors.MeasurementNotAdmitted):
        apt(profile, records, measure, mapping, proxy_id)


def test_an_unlisted_target_pair_refuses(profile):
    records, measure, mapping, proxy_id = setup_binding(target=Observable("testing/energy", "testing/entity"))
    del records.nodes[measure.procedure]
    with pytest.raises(errors.MeasurementNotAdmitted):
        apt(profile, records, measure, mapping, proxy_id)


@pytest.mark.parametrize("same_as", [False, True])
def test_yield_mismatch_through_authority_and_same_as(profile, same_as):
    records, measure, _, _ = setup_binding(scale=Scale(Fraction(0), Fraction(1), "higher-is-more"))
    authority = measure.procedure
    if same_as:
        measure = replace(measure, procedure=records.put(procedure(yields=(OBS,), scale=SameAs(authority))))
    # A missing authority and bearer mismatch must not hide the yield refusal.
    measure = replace(
        measure, observable=replace(OBS, aspect=Aspect("testing/energy-aspect", "EX:other")), unit=None, scale=authority
    )
    if same_as:
        del records.nodes[authority]
    with pytest.raises(errors.ProcedureYieldMismatch):
        apt(profile, records, measure)


def test_scale_authority_refuses_before_bearer(profile):
    records, measure, _, _ = setup_binding()
    measure = replace(measure, unit=None, scale=measure.procedure)
    with pytest.raises(errors.ScaleAuthorityMismatch):
        apt(profile, records, measure)


def test_bearer_mismatch_with_mapping_only_is_proxy_required(profile):
    records, measure, mapping, _ = setup_binding()
    with pytest.raises(errors.ProxyRequired):
        apt(profile, records, measure, mapping)


def test_bearer_mismatch_with_proxy_only_is_mapping_required(profile):
    records, measure, _, proxy_id = setup_binding()
    with pytest.raises(errors.MappingRequired):
        apt(profile, records, measure, proxy=proxy_id)


def test_proxy_and_mapping_build_with_the_target_observable_and_the_basis_assumption(profile):
    records, measure, mapping, proxy_id = setup_binding()
    result = apt(profile, records, measure, mapping, proxy_id)
    assert result.target_observable == TARGET
    assert result.assumptions == (BASIS,)
    assert tuple(entry.id for entry in result.dependencies) == tuple(sorted((measure.procedure, mapping, proxy_id)))
    assert next(entry.terms for entry in result.dependencies if entry.id == mapping) == (
        "testing/entity",
        "testing/event",
        "testing/mean",
    )


def test_broader_scope_than_validated_in_adds_procedure_validity(profile):
    narrow = {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(1), Fraction(2), True, True)}
    records, measure, _, _ = setup_binding(validated_in=narrow)
    result = apt(profile, records, measure, scope=SCOPE, role="testing/event")
    assert result.assumptions == (
        AssumptionInstance(
            "testing/procedure-validity",
            {"record": measure.procedure, "co_scope": "broader", "dimensions": "testing/follow-up"},
        ),
    )
    check_instance(profile, result.assumptions[0])
    assert apt(profile, records, measure, scope=narrow, role="testing/event").assumptions == ()
    records2, measure2, _, _ = setup_binding(validated_in=SCOPE)
    assert apt(profile, records2, measure2, scope=narrow, role="testing/event").assumptions == ()


def test_broader_scope_than_proxy_validity_adds_proxy_validity(profile):
    narrow = {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(1), Fraction(2), True, True)}
    records, measure, mapping, proxy_id = setup_binding(validated_in=narrow, validity=narrow)
    result = apt(profile, records, measure, mapping, proxy_id, SCOPE)
    expected = (
        AssumptionInstance(
            "testing/procedure-validity",
            {"record": measure.procedure, "co_scope": "broader", "dimensions": "testing/follow-up"},
        ),
        AssumptionInstance(
            "testing/proxy-validity", {"record": proxy_id, "co_scope": "broader", "dimensions": "testing/follow-up"}
        ),
        BASIS,
    )
    assert result.assumptions == expected
    for instance in result.assumptions:
        check_instance(profile, instance)


def test_a_cross_quantity_proxy_builds(base_contract, testing_document):
    from copy import deepcopy

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile

    document = deepcopy(testing_document)
    document["quantity_kinds"].update(
        {"rna-abundance": {"dimension": "construct"}, "protein-abundance": {"dimension": "construct"}}
    )
    document["units"]["rna-tpm"] = {"symbol": "TPM", "quantity_kind": "rna-abundance"}
    document["measurements"]["product"].append("rna-abundance")
    document["measurements"]["entity"].append("protein-abundance")
    profile = compile_profile(
        base_contract,
        [parse_domain_contract(document, source="<cross-quantity>", base=base_contract, predecessor=None)],
    )
    target = Observable("testing/protein-abundance", "testing/entity")
    records, measure, mapping, proxy_id = setup_binding(
        observable=Observable("testing/rna-abundance", "testing/product"), target=target
    )
    measure = replace(measure, unit="testing/rna-tpm")
    assert apt(profile, records, measure, mapping, proxy_id).target_observable == target


def test_dependencies_are_frozen_with_terms(profile):
    records, measure, mapping, proxy_id = setup_binding()
    result = apt(profile, records, measure, mapping, proxy_id)
    assert next(entry.terms for entry in result.dependencies if entry.id == proxy_id) == (
        "testing/abundance",
        "testing/energy",
        "testing/energy-aspect",
        "testing/entity",
        "testing/event",
        "testing/proxy-validity",
    )
    assert next(entry.terms for entry in result.dependencies if entry.id == measure.procedure) == (
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
        "testing/instrument",
    )


def test_a_scale_of_proxy_is_not_a_bearer_bridge(profile):
    records, measure, mapping, _ = setup_binding()
    proxy_id = records.put(
        proxy(
            source=ProxySource(OBS, measure.procedure),
            target=ProxyTarget(None, measure.procedure),
            basis=BASIS,
            crosswalk=CROSSWALK,
        )
    )
    with pytest.raises(errors.MappingRequired):
        apt(profile, records, measure, mapping, proxy_id)


@pytest.mark.parametrize(
    "change",
    [
        {"unit": "testing/missing"},
        {"unit": "testing/second"},
        {"transformation": "testing/missing"},
        {"observable": Observable("testing/energy", "testing/event", Aspect("testing/stage", "EX:a"))},
    ],
)
def test_authoring_aptness_checks_measure_typing(profile, change):
    records, measure, _, _ = setup_binding()
    with pytest.raises((errors.MalformedMeasure, errors.AspectNotAdmitted)):
        apt(profile, records, replace(measure, **change), role="testing/event")


@pytest.mark.parametrize("change", ["observable", "procedure", "target", "mapping"])
def test_proxy_bridge_requires_every_correspondence(profile, change):
    records, measure, mapping, proxy_id = setup_binding()
    p = records.read(proxy_id)
    from beliefs.proxy_model import proxy_from_stored

    value = proxy_from_stored(p)
    if change == "observable":
        value = replace(value, source=replace(value.source, observable=replace(OBS, aspect=None)))
    elif change == "procedure":
        value = replace(value, source=replace(value.source, procedure=records.put(procedure(name="other"))))
    elif change == "target":
        value = replace(value, target=ProxyTarget(Observable("testing/abundance", "testing/product"), None))
    else:
        mapping = records.put(ReferentMapping("testing/product", "testing/entity", {}, "one-to-one", None, None))
    with pytest.raises(errors.MappingRequired):
        apt(profile, records, measure, mapping, records.put(value))


def test_proxy_source_may_use_measure_same_as_authority(profile):
    records, measure, mapping, proxy_id = setup_binding(scale=Scale(Fraction(0), Fraction(1), "higher-is-more"))
    authority = measure.procedure
    measure = replace(measure, procedure=records.put(procedure(scale=SameAs(authority))), unit=None, scale=authority)
    assert apt(profile, records, measure, mapping, proxy_id).target_observable == TARGET


def test_invalid_basis_and_ambiguous_validity_kind_refuse(profile, base_contract, testing_document):
    records, measure, mapping, _ = setup_binding()
    bad = records.put(
        proxy(
            source=ProxySource(OBS, measure.procedure),
            target=ProxyTarget(TARGET, None),
            basis=AssumptionInstance("testing/proxy-validity", {}),
        )
    )
    with pytest.raises(errors.MalformedRecord):
        apt(profile, records, measure, mapping, bad)
    from copy import deepcopy

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile

    second = deepcopy(testing_document)
    second["contract"] = "secondpack"
    ambiguous = compile_profile(
        base_contract,
        [
            parse_domain_contract(document, source="<ambiguous>", base=base_contract, predecessor=None)
            for document in (testing_document, second)
        ],
    )
    measure = replace(measure, procedure=records.put(procedure(validated_in=SCOPE)))
    with pytest.raises(errors.ProfileError):
        apt(ambiguous, records, measure, role="testing/event")


@pytest.mark.parametrize(
    "low,high,verdict,combined", [(11, 12, "disjoint", "disjoint"), (5, 15, "overlapping", "unknown")]
)
def test_validity_preserves_nonequal_verdict_and_sorted_dimensions(profile, low, high, verdict, combined):
    from beliefs.restriction import TermRestriction

    validated = SCOPE | {"testing/stage": TermRestriction("testing/stage", "EX:a")}
    scope = {
        "testing/follow-up": IntervalRestriction("testing/hour", Fraction(low), Fraction(high), True, True),
        "testing/stage": TermRestriction("testing/stage", "EX:b"),
    }
    records, measure, _, _ = setup_binding(validated_in=validated)
    result = apt(profile, records, measure, scope=scope, role="testing/event")
    # Unequal terms are unknown; a disjoint interval still takes precedence.
    assert result.assumptions[0].particulars == {
        "record": measure.procedure,
        "co_scope": combined,
        "dimensions": "testing/follow-up,testing/stage",
    }
    only_interval = apt(
        profile,
        records,
        replace(measure, procedure=records.put(procedure(validated_in=SCOPE))),
        scope={"testing/follow-up": scope["testing/follow-up"]},
        role="testing/event",
    )
    assert only_interval.assumptions[0].particulars["co_scope"] == verdict


def test_validity_unknown_requires_activated_kind_and_particulars(base_contract, testing_document):
    from copy import deepcopy

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile
    from beliefs.restriction import TermRestriction

    document = deepcopy(testing_document)
    document["assumption_kinds"]["procedure-validity"]["particulars"].append("extra_required")
    profile = compile_profile(
        base_contract,
        [parse_domain_contract(document, source="<required-particulars>", base=base_contract, predecessor=None)],
    )
    records, measure, _, _ = setup_binding(validated_in=SCOPE)
    with pytest.raises(errors.MalformedRecord, match="missing required particulars"):
        apt(
            profile,
            records,
            measure,
            scope={"testing/follow-up": TermRestriction("testing/level", "EX:a")},
            role="testing/event",
        )
    del document["assumption_kinds"]["procedure-validity"]
    profile = compile_profile(
        base_contract, [parse_domain_contract(document, source="<missing-kind>", base=base_contract, predecessor=None)]
    )
    with pytest.raises(errors.ProfileError):
        apt(profile, records, measure, role="testing/event")


def test_yield_is_checked_without_any_scale(profile):
    records, measure, _, _ = setup_binding()
    measure = replace(measure, observable=replace(OBS, aspect=None))
    with pytest.raises(errors.ProcedureYieldMismatch):
        apt(profile, records, measure, role="testing/event")
