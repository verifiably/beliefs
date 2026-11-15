"""Real candidate meanings exercised through the existing series boundaries."""

from dataclasses import replace
from fractions import Fraction

import pytest
from candidate_contracts import candidate_profile

from beliefs import errors
from beliefs.claim import Referent, build_claim
from beliefs.classification_rule import ClassificationRule
from beliefs.estimand import RoleAnchor, RuleAnchor, check_series
from beliefs.measurement import Aspect, Measure, Observable
from beliefs.procedure import Procedure
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.geometry import window_memberships
from beliefs.series.types import SeriesRefused

from .candidate_case import (
    ASPECT,
    EXPECTED,
    HALO,
    KM,
    POPULATION,
    build,
    candidate_chain,
    checks_contract,
    hold,
    speed_values,
)


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
    with pytest.raises(SeriesRefused, match="support does not exactly tile the event window"):
        candidate_chain(profile, windows=((Fraction(-97, 2), 0), (24, 120)))


def test_a_missing_anchor_table_refuses(profile):
    chain = candidate_chain(profile)
    response = chain.bindings["response"]
    bare = chain.case.rewrite(series_ref_projection(response.series), lambda view: view.pop("anchors"))
    bindings = {**chain.bindings, "response": replace(response, series=series_ref_from_projection(bare))}
    with pytest.raises(SeriesRefused, match="event series requires RuleAnchor and an anchor table"):
        build(chain, bindings=bindings)


def test_a_role_anchor_refuses_on_a_series_bearing_target(profile):
    chain = candidate_chain(profile)
    with pytest.raises(SeriesRefused, match="event series requires RuleAnchor and an anchor table"):
        build(chain, bindings={**chain.bindings, "anchor": RoleAnchor("anchor", None, HALO)})
