"""Q3 (construction refuses rather than flattens), Q7's projection arms, Q9 (commensuration and scope)."""

from decimal import Decimal

import pytest

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    EstimandError,
    EstimandFragmentRefused,
    EstimandSortMismatch,
    MeasureRefused,
    ProfileError,
    ReferenceRefused,
    UnboundReferent,
    UncertaintyRefused,
)
from beliefs.estimand import (
    ContinuousContrast,
    Control,
    Estimand,
    Interval,
    LevelsContrast,
    Measure,
    StandardError,
    applicability_projection,
    build_applicability,
    build_estimand,
    check_estimate,
    check_uncertainty,
    co_scoped,
    commensurable,
    estimand_projection,
)
from beliefs.profile import compile_profile
from beliefs.resolution import TermOutcome, build_snapshot

E, O, L, M, I = "testing/entity", "testing/outcome", "testing/level", "testing/measure", "testing/identification"


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


@pytest.fixture()
def other_claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


@pytest.fixture()
def unconsulted():
    return build_snapshot(readable={})


def parts(**overrides):
    fields = {
        "contrast": LevelsContrast(slot=0, baseline=Referent(L, "EX:ndmm"), comparison=Referent(L, "EX:pd")),
        "measure": Measure(quantity=Referent(M, "EX:tpm"), scale="additive"),
        "reference": Decimal(0),
        "control": Control(identification=Referent(I, "EX:observational"), conditioning=()),
    }
    fields.update(overrides)
    return fields


def build(profile, claim, snapshot, **overrides):
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


def test_a_levels_estimand_builds_and_names_its_claim(profile, claim, unconsulted):
    from beliefs.projection import claim_identity

    estimand, receipt = build_estimand(profile, claim, snapshot=unconsulted, **parts())
    assert estimand.claim == claim_identity(claim) and estimand.operator == "testing/affects"
    assert set(receipt.outcomes) == {"estimand:contrast.baseline", "estimand:contrast.comparison", "estimand:measure.quantity", "estimand:control.identification"}
    assert all(outcome is TermOutcome.NOT_CONSULTED for outcome in receipt.outcomes.values())


def test_a_continuous_estimand_carries_quantity_and_increment(profile, claim, unconsulted):
    estimand = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:log2-tpm"), increment=Decimal(1)))
    assert estimand_projection(estimand)["contrast"] == {"slot": 0, "kind": "continuous", "quantity": {"sort": M, "term": "EX:log2-tpm"}, "increment": Decimal(1)}


def test_estimand_has_no_public_constructor():
    with pytest.raises(EstimandError, match="use build_estimand"):
        Estimand(claim="c", operator="o", contrast=None, measure=None, reference=Decimal(0), control=None)  # type: ignore[call-arg]


# Every invalid value is built **inside** the assertion: the sealed values refuse
# at construction, so a parametrization that constructed them at collection time
# would fail before `pytest.raises` ran.
@pytest.mark.parametrize("make,error,position", [
    (lambda: {"contrast": LevelsContrast(slot=2, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "slot 2"),
    (lambda: {"contrast": LevelsContrast(slot=True, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "integer"),
    (lambda: {"contrast": ContinuousContrast(slot=0.5, quantity=Referent(M, "EX:q"), increment=Decimal(1))}, ContrastRefused, "integer"),  # type: ignore[arg-type]
    (lambda: {"contrast": LevelsContrast(slot=1, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "no level sort"),
    (lambda: {"contrast": LevelsContrast(slot=0, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:a"))}, ContrastRefused, "distinct"),
    (lambda: {"contrast": LevelsContrast(slot=0, baseline=Referent(E, "EX:a"), comparison=Referent(L, "EX:b"))}, EstimandSortMismatch, "contrast.baseline"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(0))}, ContrastRefused, "increment"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(-1))}, ContrastRefused, "increment"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(E, "EX:q"), increment=Decimal(1))}, EstimandSortMismatch, "contrast.quantity"),
    (lambda: {"measure": Measure(quantity=Referent(E, "EX:tpm"), scale="additive")}, EstimandSortMismatch, "measure.quantity"),
    (lambda: {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="ordinal")}, MeasureRefused, "scale"),
    (lambda: {"measure": Measure(quantity=Referent(M, "EX:hr"), scale="multiplicative"), "reference": Decimal(0)}, ReferenceRefused, "multiplicative"),
    (lambda: {"reference": Decimal("NaN")}, ReferenceRefused, "finite"),
    (lambda: {"control": Control(identification=Referent(E, "EX:obs"), conditioning=())}, EstimandSortMismatch, "control.identification"),
    (lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(O, "EX:c"),))}, EstimandSortMismatch, "control.conditioning[0]"),
    (lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c"), Referent(E, "EX:c")))}, ControlRefused, "duplicate"),
])
def test_each_refusal_names_its_position(profile, claim, unconsulted, make, error, position):
    with pytest.raises(error, match=position):
        build(profile, claim, unconsulted, **make())


def test_a_float_reference_is_refused_before_the_digest(profile, claim, unconsulted):
    with pytest.raises(ReferenceRefused, match="Decimal"):
        build(profile, claim, unconsulted, reference=0.0)  # type: ignore[arg-type]


def test_an_operator_without_a_declaration_refuses(profile, unconsulted):
    structural = build_claim(profile, operator="testing/subtype-of", args=(Referent(E, "EX:a"), Referent(E, "EX:b")), layer="structural")
    with pytest.raises(ProfileError, match="declares no estimand"):
        build(profile, structural, unconsulted)


def test_not_member_refuses_and_not_consulted_mints(profile, claim, unconsulted):
    # `level`, `measure` and `identification` all bind the same `{EX, 2026-01-01}`
    # vocabulary in fixtures/contracts/testing.yaml (landed in Task 3, after this
    # test was written) — one VocabularyBinding, shared by value. Declaring it
    # readable makes it readable for every sort built on it, so `parts()`'s
    # measure and control terms must be present too, or they resolve `not-member`
    # against a vocabulary that was in fact read.
    binding = profile.sorts[L].vocabulary
    readable = build_snapshot(readable={binding: ["EX:ndmm", "EX:pd", "EX:tpm", "EX:observational"]})
    estimand, receipt = build_estimand(profile, claim, snapshot=readable, **parts())
    assert receipt.outcomes["estimand:contrast.baseline"] is TermOutcome.MEMBER
    with pytest.raises(UnboundReferent, match="estimand:contrast.comparison"):
        build(profile, claim, readable, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:ndmm"), comparison=Referent(L, "EX:mgus")))
    assert estimand_projection(build(profile, claim, unconsulted)) == estimand_projection(estimand)


def test_the_fragment_refuses_a_second_measure_or_reference(profile, claim, unconsulted):
    with pytest.raises(EstimandFragmentRefused, match="one measure"):
        build_estimand(profile, claim, snapshot=unconsulted, **parts(), measures=(parts()["measure"], parts()["measure"]))  # type: ignore[arg-type]


class TestProjection:
    def test_conditioning_order_is_inert(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c1"), Referent(E, "EX:c2"))))
        b = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c2"), Referent(E, "EX:c1"))))
        assert estimand_projection(a) == estimand_projection(b)

    def test_swapped_levels_are_two_estimands(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm")))
        assert estimand_projection(a) != estimand_projection(b)

    @pytest.mark.parametrize("override", [
        {"measure": Measure(quantity=Referent(M, "EX:other"), scale="additive")},
        {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="multiplicative"), "reference": Decimal(1)},
        {"reference": Decimal("0.5")},
        {"control": Control(identification=Referent(I, "EX:longitudinal"), conditioning=())},
        {"control": Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),))},
    ])
    def test_each_member_moves_the_projection(self, profile, claim, unconsulted, override):
        assert estimand_projection(build(profile, claim, unconsulted)) != estimand_projection(build(profile, claim, unconsulted, **override))


class TestPredicates:
    def test_identification_alone_is_outside_the_key(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:longitudinal"), conditioning=()))
        assert commensurable(a, b)

    def test_two_claims_at_one_operator_are_two_keys(self, profile, claim, other_claim, unconsulted):
        assert not commensurable(build(profile, claim, unconsulted), build(profile, other_claim, unconsulted))

    def test_swapped_levels_and_different_increments_are_not_commensurable(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm")))
        assert not commensurable(a, b)
        c1 = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(1)))
        c10 = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(10)))
        assert not commensurable(c1, c10)

    def test_the_scope_counterexample(self, profile, claim, unconsulted):
        adults, _ = build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))}, snapshot=unconsulted)
        everyone, _ = build_applicability(profile, claim, {}, snapshot=unconsulted)
        a, b = build(profile, claim, unconsulted), build(profile, claim, unconsulted)
        assert commensurable(a, b) and not co_scoped(adults, everyone)
        assert applicability_projection(everyone) == {}

    def test_applicability_refuses_an_undeclared_dimension_and_a_wrong_sort(self, profile, claim, unconsulted):
        from beliefs.errors import RestrictionSortMismatch, UndeclaredDimension

        with pytest.raises(UndeclaredDimension):
            build_applicability(profile, claim, {"testing/regime": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted)
        with pytest.raises(RestrictionSortMismatch):
            build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted)


class TestEstimateAndUncertainty:
    def test_a_multiplicative_estimate_must_be_positive(self):
        check_estimate(Decimal("1.2"), "multiplicative")
        with pytest.raises(UncertaintyRefused, match="multiplicative"):
            check_estimate(Decimal(0), "multiplicative")

    @pytest.mark.parametrize("uncertainty,scale", [
        (Interval(Decimal("0.5"), Decimal("0.3"), Decimal("0.95")), "additive"),
        (Interval(Decimal(-1), Decimal(1), Decimal(1)), "additive"),
        (Interval(Decimal(0), Decimal(2), Decimal("0.95")), "multiplicative"),
        (StandardError(Decimal("-0.1")), "additive"),
    ])
    def test_ill_formed_uncertainty_is_refused(self, uncertainty, scale):
        with pytest.raises(UncertaintyRefused):
            check_uncertainty(uncertainty, Decimal("0.4") if scale == "additive" else Decimal("1.1"), scale)

    def test_well_formed_uncertainty_passes(self):
        check_uncertainty(Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95")), Decimal("0.4"), "additive")
        check_uncertainty(StandardError(Decimal("0.2")), Decimal("1.1"), "multiplicative")
