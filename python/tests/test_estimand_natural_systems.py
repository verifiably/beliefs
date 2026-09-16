"""beliefs-e48279: the pilot's surrogate-contrast estimand through
`build_estimand` and the `AssessmentValue` constructor — Appendix A of the
estimand-typing design, its API half.

A.2 encodes the natural-systems v2 time-series pilot's opening surrogate
assessment (§7 of that project's pilot design) as a corpus-local contract:
one operator, `departs-from-series-source-observation-procedure`, and one
`estimands:` declaration on it. `fixtures/natural-systems-pilot-fixture.yaml`
transcribes A.2's YAML exactly; this module builds the claim A.2 states,
admits the estimand A.2's member table describes, and — against A.4 — checks
that every refusal A.4 predicts is the refusal the fragment actually gives,
named at its position. No kernel surface here is new: this is a test of the
fragment cut 31 already shipped, read against a second inhabitant.
"""

import re
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from beliefs.claim import Referent, build_claim
from beliefs.contract import domain
from beliefs.contract.document import load_document
from beliefs.errors import (
    ContrastRefused,
    EstimandFragmentRefused,
    MalformedRecord,
    UncertaintyRefused,
)
from beliefs.estimand import (
    ContinuousContrast,
    Control,
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
from beliefs.projection import claim_identity
from beliefs.record import AssessmentValue
from beliefs.resolution import build_snapshot

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "natural-systems-pilot-fixture.yaml"

SERIES = "natural-systems-pilot/series-source"
PROC = "natural-systems-pilot/observation-procedure"
STAT = "natural-systems-pilot/statistic"
IDENT = "natural-systems-pilot/identification"
OPERATOR = "natural-systems-pilot/departs-from-series-source-observation-procedure"

RECORD = "pilot-record-01"


@pytest.fixture()
def profile(base_contract):
    document = load_document(FIXTURE_PATH, source=str(FIXTURE_PATH))
    pilot = domain.parse_domain_contract(document, source=str(FIXTURE_PATH), base=base_contract, predecessor=None)
    return compile_profile(base_contract, [pilot])


@pytest.fixture()
def claim(profile):
    return build_claim(
        profile,
        operator=OPERATOR,
        args=(Referent(SERIES, RECORD), Referent(PROC, "fourier-phase-randomized")),
        layer="statistical",
        polarity="unsigned",
    )


@pytest.fixture()
def snapshot(profile):
    # Every referent A.2 and A.4 name resolves `member`: the series-source
    # term for the one held record; `identity`, `fourier-phase-randomized` and
    # `aaft` under `observation-procedure` (the third is A.4(a)'s refusal
    # arm); `co-trev-1-num` and a second statistic term under `statistic`
    # (A.2/§7.3's commensuration arm); `within-series-surrogate` under
    # `identification`.
    return build_snapshot(
        readable={
            profile.sorts[SERIES].vocabulary: [RECORD],
            profile.sorts[PROC].vocabulary: ["identity", "fourier-phase-randomized", "aaft"],
            profile.sorts[STAT].vocabulary: ["co-trev-1-num", "co-trev-2-num"],
            profile.sorts[IDENT].vocabulary: ["within-series-surrogate"],
        }
    )


def parts(**overrides):
    fields = {
        "contrast": LevelsContrast(slot=1, baseline=Referent(PROC, "fourier-phase-randomized"), comparison=Referent(PROC, "identity")),
        "measure": Measure(quantity=Referent(STAT, "co-trev-1-num"), scale="additive"),
        "reference": Decimal(0),
        "control": Control(identification=Referent(IDENT, "within-series-surrogate"), conditioning=()),
    }
    fields.update(overrides)
    return fields


def build(profile, claim, snapshot, **overrides):
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


# --- A.2: admission ----------------------------------------------------------


class TestA2Admission:
    def test_the_levels_contrast_on_the_procedure_slot_is_admitted(self, profile, claim, snapshot):
        estimand, receipt = build_estimand(profile, claim, snapshot=snapshot, **parts())
        projection = estimand_projection(estimand)
        contrast = cast(dict, projection["contrast"])
        assert projection["claim"] == claim_identity(claim)
        assert projection["operator"] == OPERATOR
        assert contrast["slot"] == 1
        assert contrast["kind"] == "levels"
        assert projection["reference"] == Decimal(0)
        from beliefs.resolution import TermOutcome

        assert all(outcome is TermOutcome.MEMBER for outcome in receipt.outcomes.values())

    def test_the_empty_applicability_map_is_admitted(self, profile, claim, snapshot):
        applicability, _receipt = build_applicability(profile, claim, {}, snapshot=snapshot)
        assert applicability_projection(applicability) == {}

    def test_a_signed_estimate_with_a_standard_error_is_admitted_under_additive(self, profile, claim, snapshot):
        estimand = build(profile, claim, snapshot)
        applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        value = AssessmentValue(
            spec="spec-1", run="run-1", proposition=claim_identity(claim), outcome="supported",
            interpretation_rule="rank-comparison/v1", estimand=estimand, applicability=applicability,
            estimate=Decimal("-0.42"), uncertainty=StandardError(value=Decimal("0.013")),
        )
        assert value.estimate == Decimal("-0.42")
        assert value.uncertainty == StandardError(value=Decimal("0.013"))

    def test_a_signed_estimate_with_no_uncertainty_is_admitted(self, profile, claim, snapshot):
        estimand = build(profile, claim, snapshot)
        applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        value = AssessmentValue(
            spec="spec-1", run="run-1", proposition=claim_identity(claim), outcome="supported",
            interpretation_rule="rank-comparison/v1", estimand=estimand, applicability=applicability,
            estimate=Decimal("-0.42"),
        )
        assert value.estimate == Decimal("-0.42") and value.uncertainty is None


# --- A.4: what refuses, and that it should ------------------------------------


def test_a_surrogate_family_as_one_contrast_refuses_at_the_fragment(profile, claim, snapshot):
    # A.4(a): identity against phase-randomized *and* AAFT is three levels on
    # one slot. `LevelsContrast` has no third slot to name the third level
    # (only `baseline`/`comparison`), so the family enters the only other way
    # it could — as a second contrast — and `build_estimand`'s `**richer`
    # refuses that by name rather than flattening it (§3.3).
    with pytest.raises(EstimandFragmentRefused, match="one contrast") as excinfo:
        build_estimand(
            profile, claim, snapshot=snapshot,
            **parts(),
            second_contrast=LevelsContrast(slot=1, baseline=Referent(PROC, "fourier-phase-randomized"), comparison=Referent(PROC, "aaft")),
        )
    assert "second_contrast" in str(excinfo.value)


def test_a_lag_range_as_a_continuous_contrast_over_an_absent_slot_refuses_with_the_slot_named(profile, claim, snapshot):
    # A.4(b): a lag range has no argument slot at all — the operator's arity
    # is 2 (`Fin(2) = {0, 1}`), so slot 2 is outside it and the refusal names
    # the slot.
    with pytest.raises(ContrastRefused, match="slot 2") as excinfo:
        build(profile, claim, snapshot, contrast=ContinuousContrast(slot=2, quantity=Referent(STAT, "co-trev-1-num"), increment=Decimal(1)))
    assert "Fin(2)" in str(excinfo.value)


def test_a_data_dependent_looking_reference_is_admitted_because_the_type_cannot_tell(profile, claim, snapshot):
    # A.4(c): `reference: E_Q[T]` would be data-dependent, but a finite
    # `Decimal` that merely *looks* like a value a run might compute is
    # admitted — the constructor has no way to see the order of events that
    # would make it a lie, only the shape of the number.
    estimand = build(profile, claim, snapshot, reference=Decimal("0.117"))
    assert estimand.reference == Decimal("0.117")


def test_the_nulls_central_band_refuses_a_rejecting_estimate_but_admits_a_non_rejecting_one(profile, claim, snapshot):
    # A.4(d): the null's central band as `uncertainty` is caught by
    # `low <= estimate <= high` exactly when the rank rule rejects — a
    # rejecting estimate lies outside the band by construction, and a
    # non-rejecting one lies inside it (limitation 12's stated reach: the
    # check is structural and cannot tell a true label from a false one when
    # the estimate happens to sit inside the band).
    band = Interval(low=Decimal("-0.30"), high=Decimal("0.30"), level=Decimal("0.95"))
    estimand = build(profile, claim, snapshot)
    applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
    exact = re.escape("the interval [-0.30, 0.30] excludes the estimate -0.42")

    # The rejecting case, through both routes `check_uncertainty` (the shared
    # check) and `AssessmentValue` (which runs it in `__post_init__` and
    # re-raises as `MalformedRecord`) — the message itself is asserted, not
    # merely the exception type, so both bounds and the excluded estimate are
    # named.
    with pytest.raises(UncertaintyRefused, match=exact):
        check_uncertainty(band, Decimal("-0.42"), "additive")
    with pytest.raises(MalformedRecord, match=exact):
        AssessmentValue(
            spec="spec-1", run="run-1", proposition=claim_identity(claim), outcome="supported",
            interpretation_rule="rank-comparison/v1", estimand=estimand, applicability=applicability,
            estimate=Decimal("-0.42"), uncertainty=band,
        )

    # Admitted: inside the band, under a label that would in fact be false —
    # built as a real `AssessmentValue`, with its typed members asserted.
    check_uncertainty(band, Decimal("0.05"), "additive")
    value = AssessmentValue(
        spec="spec-1", run="run-1", proposition=claim_identity(claim), outcome="inconclusive",
        interpretation_rule="rank-comparison/v1", estimand=estimand, applicability=applicability,
        estimate=Decimal("0.05"), uncertainty=band,
    )
    assert value.estimate == Decimal("0.05")
    assert value.uncertainty == band


def test_a_float_estimate_refuses_and_is_never_coerced(profile, claim, snapshot):
    # A.4 / §6: a `float` estimate is refused at the boundary, not coerced to
    # `Decimal` — the same check `AssessmentValue.__post_init__` runs at
    # every construction, derived or stored.
    estimand = build(profile, claim, snapshot)
    applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
    with pytest.raises(MalformedRecord, match="Decimal"):
        AssessmentValue(
            spec="spec-1", run="run-1", proposition=claim_identity(claim), outcome="supported",
            interpretation_rule="rank-comparison/v1", estimand=estimand, applicability=applicability,
            estimate=-0.42,  # type: ignore[arg-type]
        )
    with pytest.raises(UncertaintyRefused, match="Decimal"):
        check_estimate(-0.42, "additive")  # type: ignore[arg-type]


# --- A.2/§7.3: commensuration -------------------------------------------------


class TestCommensuration:
    def test_two_estimands_differing_only_in_the_statistic_are_not_commensurable(self, profile, claim, snapshot):
        a = build(profile, claim, snapshot, measure=Measure(quantity=Referent(STAT, "co-trev-1-num"), scale="additive"))
        b = build(profile, claim, snapshot, measure=Measure(quantity=Referent(STAT, "co-trev-2-num"), scale="additive"))
        assert not commensurable(a, b)

    def test_two_estimands_differing_only_in_identification_are_commensurable(self, profile, claim, snapshot):
        # `control.identification` is the one member `commensuration_key`
        # removes (§7.3): it is corpus-local (A.2's identification vocabulary,
        # limitation 4), and the design key a weight table reads is the one
        # member outside it. A second identification term is added to this
        # test's own snapshot to exercise the difference — A.2 names only
        # `within-series-surrogate`; a distinct scheme is legitimate test data
        # for the sort, not a member the fragment lacks.
        binding = profile.sorts[IDENT].vocabulary
        readable = build_snapshot(readable={
            profile.sorts[SERIES].vocabulary: [RECORD],
            profile.sorts[PROC].vocabulary: ["identity", "fourier-phase-randomized", "aaft"],
            profile.sorts[STAT].vocabulary: ["co-trev-1-num", "co-trev-2-num"],
            binding: ["within-series-surrogate", "block-bootstrap-surrogate"],
        })
        a = build(profile, claim, readable, control=Control(identification=Referent(IDENT, "within-series-surrogate"), conditioning=()))
        b = build(profile, claim, readable, control=Control(identification=Referent(IDENT, "block-bootstrap-surrogate"), conditioning=()))
        assert commensurable(a, b)

    def test_co_scoped_holds_for_the_empty_applicability_on_both_pairs(self, profile, claim, snapshot):
        a, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        b, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        assert co_scoped(a, b)
        assert applicability_projection(a) == {} and applicability_projection(b) == {}
