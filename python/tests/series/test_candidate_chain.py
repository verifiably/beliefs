"""Real candidate meanings exercised through the existing series boundaries."""

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256

import pytest
from candidate_contracts import candidate_profile
from test_audit import _stated_optionals, run_publication
from test_convert import snapshot

from beliefs import errors, stored
from beliefs.assess import build_assessment
from beliefs.claim import Referent, build_claim
from beliefs.classification_rule import ClassificationRule
from beliefs.estimand import MeasuredBinding, RoleAnchor, RuleAnchor, check_series
from beliefs.measurement import Aspect, Measure, Observable
from beliefs.procedure import Procedure
from beliefs.projection import claim_identity, project_claim
from beliefs.record import AssessmentValue
from beliefs.register import AssumptionsRegister
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.geometry import window_memberships
from beliefs.series.types import SeriesRefused
from beliefs.spec import SpecInput
from beliefs.standing import check_standing
from beliefs.target_comparison import convertibility

from .candidate_case import (
    ASPECT,
    EXPECTED,
    HALO,
    KM,
    NO_AXIS,
    POPULATION,
    RULES,
    WINDOWS,
    M,
    build,
    candidate_chain,
    checks_contract,
    freeze_chain,
    hold,
    proposition_of,
    run_chain,
    speed_values,
)
from .test_authoring import input_roles
from .test_chains import key_for
from .test_portability import writer_at


@pytest.fixture(scope="module")
def profile(base_contract):
    return candidate_profile(base_contract, extra=[checks_contract(base_contract)])


def test_fixture_values_have_the_stated_window_means():
    values = [Fraction(value) for value in speed_values()]
    means = [sum(values[low:high]) / (high - low) for low, high in ((0, 48), (72, 168), (200, 248), (272, 368))]
    assert means == [400, 410, 450, 447]
    assert ((means[1] - means[0]) + (means[3] - means[2])) / 2 == EXPECTED
    assert set(values[48:72] + values[168:200] + values[248:272]) == {Fraction(999)}


def test_chain_authors_and_windows_translate_per_anchor(profile):
    chain = candidate_chain(profile)
    (checked,) = check_series(
        chain.estimand, profile=profile, records=chain.case.records, evidence=chain.case.evidence()
    )
    windows = window_memberships(checked, ((Fraction(-172800), Fraction(0)), (Fraction(86400), Fraction(432000))))
    assert tuple(tuple((w.low, w.high) for w in anchor) for anchor in windows) == (
        ((-172800, 0), (86400, 432000)),
        ((547200, 720000), (806400, 1152000)),
    )
    assert tuple(tuple(len(w.positions) for w in anchor) for anchor in windows) == ((48, 96), (48, 96))
    (assumption,) = chain.estimand.assumptions
    assert assumption.kind == "general/procedure-validity"
    assert assumption.particulars == {
        "record": chain.measuring,
        "co_scope": "unknown",
        "dimensions": "catalogue-anchors/anchor-epoch",
    }


def test_another_token_is_refused_at_claim_building(profile):
    with pytest.raises(errors.IdentifierClassMismatch):
        build_claim(
            profile,
            operator="general/event-locked-change",
            roles={"anchor": HALO, "response": Referent(POPULATION.sort, "plasma-population:magnetosheath")},
            layer="statistical",
            form="polar",
            polarity="positive",
        )


def _response(chain, observable, unit, procedure):
    measure = Measure(observable, unit, None, "ratio", "level", "general/identity", procedure)
    return {**chain.bindings, "response": replace(chain.bindings["response"], measure=measure)}


def _assay(observable):
    return Procedure(
        kind="general/assay",
        name="Synthetic fixture assay",
        definition="Synthetic fixture measurement.",
        yields=(observable,),
        scale=None,
        validated_in="unknown",
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters={},
        external=None,
    )


def test_a_measure_on_another_bearer_needs_a_proxy(profile):
    chain = candidate_chain(profile)
    feature = Observable("si-brochure/speed", "candidate-checks/coronagraph-feature")
    with pytest.raises(errors.ProxyRequired, match="a bearer change requires a proxy model"):
        build(chain, bindings=_response(chain, feature, KM, hold(chain, _assay(feature))))


def test_an_unadmitted_bearer_and_quantity_pair_refuses(profile):
    chain = candidate_chain(profile)
    duration = Observable("si-brochure/duration", POPULATION.sort)
    with pytest.raises(errors.MeasurementNotAdmitted, match="the source bearer and quantity kind are not admitted"):
        build(chain, bindings=_response(chain, duration, "si-brochure/second", hold(chain, _assay(duration))))


def test_an_unadmitted_aspect_refuses(profile):
    chain = candidate_chain(profile)
    wrong = Observable("si-brochure/speed", POPULATION.sort, Aspect(HALO.sort, HALO.term))
    with pytest.raises(errors.AspectNotAdmitted, match="is not admitted for 'si-brochure/speed'"):
        build(chain, bindings=_response(chain, wrong, KM, chain.measuring))


def _rule(classes, definition):
    return ClassificationRule(
        classes=classes, reads=(), definition=definition, external=None, implementation=None, annotator="synthetic"
    )


def test_a_rule_over_another_sort_refuses(profile):
    chain = candidate_chain(profile)
    other = hold(chain, _rule(ASPECT.sort, "Synthetic rule over another sort."))
    with pytest.raises(errors.ContrastRefused, match="held rule classes disagree with the bound classes sort"):
        build(chain, bindings={**chain.bindings, "anchor": RuleAnchor(other, (HALO,))})


def test_an_anchor_table_citing_another_rule_refuses(profile):
    chain = candidate_chain(profile)
    other = hold(chain, _rule(HALO.sort, "Synthetic rule, a different wording."))
    with pytest.raises(SeriesRefused, match="RuleAnchor rule/classes disagree with the anchor table"):
        build(chain, bindings={**chain.bindings, "anchor": RuleAnchor(other, (HALO,))})


def test_a_window_not_tiled_by_support_refuses(profile):
    with pytest.raises(SeriesRefused, match="event target requires at least one retained candidate"):
        candidate_chain(profile, windows=((Fraction(-97, 2), 0), (24, 120)))


def test_a_missing_anchor_table_refuses(profile):
    chain = candidate_chain(profile)
    response = chain.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    bare = chain.case.rewrite(series_ref_projection(response.series), lambda view: view.pop("anchors"))
    bindings = {**chain.bindings, "response": replace(response, series=series_ref_from_projection(bare))}
    with pytest.raises(SeriesRefused, match="event series requires RuleAnchor and an anchor table"):
        build(chain, bindings=bindings)


def test_a_role_anchor_refuses_on_a_series_bearing_target(profile):
    chain = candidate_chain(profile)
    with pytest.raises(SeriesRefused, match="event series requires RuleAnchor and an anchor table"):
        build(chain, bindings={**chain.bindings, "anchor": RoleAnchor("anchor", None, HALO)})


@pytest.fixture(scope="module")
def ran(profile, tmp_path_factory):
    chain = candidate_chain(profile)
    proposition = stored.proposition_node(
        "candidate-solar-wind", title="Synthetic candidate proposition", claim=project_claim(chain.claim)
    )
    spec = freeze_chain(chain, target=proposition.id)
    result = run_chain(chain, spec, tmp_path_factory.mktemp("candidate-chain"))
    result.chain, result.spec, result.proposition = chain, spec, proposition
    return result


def test_chain_emits_the_hand_derived_estimate_and_replays(ran):
    assert ran.emitted == "7/2"
    assert Fraction(ran.emitted) == EXPECTED
    assert dict(ran.original.run.result.outputs) == {"outputs/result.txt": "sha256:" + sha256(b"7/2").hexdigest()}
    assert ran.original.run.result == ran.replayed.run.result
    assert ran.verification.verdict == "passed"
    assert ran.verification.scope == "same-environment"


def test_inputs_take_the_synthetic_modes_and_nothing_is_observed(ran):
    assert sorted((i.role, i.mode) for i in ran.spec.input_roles) == [("reads", "annotation")] * 3 + [
        ("reads", "simulation")
    ]
    assert {i.dataset for i in ran.original.run.recipe.inputs} == {i.dataset for i in ran.spec.input_roles}


def test_swapped_windows_negate_the_estimate(ran, profile, tmp_path):
    swapped = candidate_chain(profile, windows=(WINDOWS[1], WINDOWS[0]))
    spec = freeze_chain(swapped)
    assert spec.identity != ran.spec.identity
    assert run_chain(swapped, spec, tmp_path, with_replay=False).emitted == "-7/2"


def test_the_synthetic_table_cannot_be_declared_observed(profile):
    chain = candidate_chain(profile)
    roles = tuple(
        SpecInput("observes", i.dataset, "observation") if i.mode == "simulation" else i
        for i in input_roles(chain.estimand)
    )
    with pytest.raises(
        errors.UnfreezableSpec, match="series datasets require exactly one compatible explicit input role/mode"
    ):
        freeze_chain(chain, input_roles=roles)


def test_empirical_standing_refuses_without_an_observed_input(ran, profile):
    with pytest.raises(
        errors.StandingRefused, match="empirical needs an observes input of mode observation with empirical standing"
    ):
        check_standing(
            ran.spec,
            ran.chain.claim,
            profile=profile,
            records=ran.chain.case.records,
            empirical=lambda _: True,
            assessments=lambda _: True,
        )


def test_the_assessment_write_refuses_for_want_of_an_observed_input(ran, profile, tmp_path):
    writer = writer_at(tmp_path / "corpus", profile)
    writer.add(ran.proposition)
    for node in ran.chain.case.records.nodes.values():
        writer.add(node)
    for namespace, identity in profile.activated_contracts.items():
        writer.add(stored.assumptions_register_node(AssumptionsRegister(f"{namespace}:{identity}", None, {})))
    writer.add(stored.analysis_spec_node(ran.spec))
    writer.add(run_publication(ran.original.run))
    rule = RULES[ran.spec.interpretation_rule]
    derived = build_assessment(
        ran.original.run, specs={ran.spec.identity: ran.spec}, implementations={rule.identity: rule}
    )
    assert isinstance(derived, AssessmentValue)
    node = stored.assessment_node(
        "candidate-solar-wind-assessment",
        title="Synthetic candidate assessment",
        spec=derived.spec,
        run=stored.typed_ref("run", ran.original.run.address()),
        proposition=ran.proposition.id,
        outcome=derived.outcome,
        interpretation_rule=derived.interpretation_rule,
        **_stated_optionals(derived),
    )
    with pytest.raises(errors.EligibilityUnmet, match="has no observes input; reads inputs never confer eligibility"):
        writer.add(node)


CHANGES = {
    "anchor-epoch": {"epoch": ("2000-01-01T00:00:00Z", "2000-02-01T00:00:00Z")},
    "rule": {"rule_definition": "Synthetic fixture rule, second wording."},
    "anchor-row": {"second_anchor": 716400},
    "lag-window": {"windows": ((-48, 0), (24, 96))},
    "procedure": {"measuring_definition": "Synthetic fixture measurement, second wording."},
    "unit": {"unit": M},
    "table-byte": {"outside": "998"},
}


@pytest.mark.parametrize("name", CHANGES)
def test_each_change_keeps_the_claim_and_moves_the_frozen_target(profile, name):
    base, changed = candidate_chain(profile), candidate_chain(profile, **CHANGES[name])
    before, after = freeze_chain(base), freeze_chain(changed)
    assert claim_identity(base.claim) == claim_identity(changed.claim) == base.estimand.claim == changed.estimand.claim
    assert before.identity != after.identity
    assert key_for(before) != key_for(after)
    assert (before.assessed_target.applicability != after.assessed_target.applicability) == (name == "anchor-epoch")


def _context(profile, *chains):
    records = chains[0].case.records
    for chain in chains[1:]:
        records.nodes.update(chain.case.records.nodes)
    return {
        "profile": profile,
        "snapshot": snapshot(records, profile=profile),
        "snapshot_identity": "snapshot:candidate",
    }


def test_series_free_targets_in_km_and_m_compare_convertible(profile):
    km = candidate_chain(profile, functional=NO_AXIS, with_series=False)
    m = candidate_chain(profile, functional=NO_AXIS, with_series=False, unit=M)
    assert convertibility(proposition_of(km), proposition_of(m), **_context(profile, km, m)).kind == "convertible"


def test_series_bound_targets_in_km_and_m_are_not_convertible(profile):
    km, m = candidate_chain(profile), candidate_chain(profile, unit=M)
    verdict = convertibility(proposition_of(km), proposition_of(m), **_context(profile, km, m))
    assert verdict.kind == "not-convertible"
    assert verdict.reason == "target"
