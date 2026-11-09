"""beliefs-e48279: the pilot's surrogate-contrast estimand through
`build_estimand` and the `AssessmentValue` constructor — the
pilot fixture, its API half.

The fixture encodes the natural-systems v2 time-series pilot's opening surrogate
assessment as a corpus-local contract:
one operator, `departs-from-series-source-observation-procedure`, and one
`estimands:` declaration on it. `fixtures/natural-systems-pilot-fixture.yaml`
transcribes the contract's YAML exactly; this module builds the claim it states,
admits the estimand its member table describes, and checks
that every predicted refusal is the refusal the fragment actually gives,
named at its position. No kernel surface here is new: this is a test of the
fragment already shipped, read against a second inhabitant.
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
    admit_estimand,
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

RECORD = "ns-pilot-series:pilot-record-01"


def proc(local: str) -> str:
    return f"ns-pilot-procedures:{local}"


def stat(local: str) -> str:
    return f"ns-pilot-statistics:{local}"


def ident(local: str) -> str:
    return f"ns-pilot-identification:{local}"


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
        roles={"source": Referent(SERIES, RECORD), "procedure": Referent(PROC, proc("fourier-phase-randomized"))},
        layer="statistical",
        polarity="unsigned",
    )


@pytest.fixture()
def snapshot(profile):
    # Every referent the fixture and the refusal cases name resolves `member`: the series-source
    # term for the one held record; `identity`, `fourier-phase-randomized` and
    # `aaft` under `observation-procedure` (the third is the first refusal case's
    # arm); `co-trev-1-num` and a second statistic term under `statistic`
    # (the commensuration case); `within-series-surrogate` under
    # `identification`.
    return build_snapshot(
        readable={
            profile.sorts[SERIES].binding: [RECORD],
            profile.sorts[PROC].binding: [proc("identity"), proc("fourier-phase-randomized"), proc("aaft")],
            profile.sorts[STAT].binding: [stat("co-trev-1-num"), stat("co-trev-2-num")],
            profile.sorts[IDENT].binding: [ident("within-series-surrogate")],
        }
    )


def parts(**overrides):
    fields = {
        "contrast": LevelsContrast(
            role="procedure",
            member=None,
            baseline=Referent(PROC, proc("fourier-phase-randomized")),
            comparison=Referent(PROC, proc("identity")),
        ),
        "measure": Measure(quantity=Referent(STAT, stat("co-trev-1-num")), scale="additive"),
        "reference": Decimal(0),
        "control": Control(identification=Referent(IDENT, ident("within-series-surrogate")), conditioning=()),
    }
    fields.update(overrides)
    return fields


def build(profile, claim, snapshot, **overrides):
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


# --- admission ----------------------------------------------------------


class TestAdmission:
    def test_the_levels_contrast_on_the_procedure_role_is_admitted(self, profile, claim, snapshot):
        estimand, receipt = build_estimand(profile, claim, snapshot=snapshot, **parts())
        projection = estimand_projection(estimand)
        contrast = cast(dict, projection["contrast"])
        assert projection["claim"] == claim_identity(claim)
        assert projection["operator"] == OPERATOR
        assert contrast["role"] == "procedure" and "member" not in contrast
        assert admit_estimand(profile, estimand, claim, authoring=True) == frozenset({"natural-systems-pilot"})
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
            spec="spec-1",
            run="run-1",
            proposition=claim_identity(claim),
            outcome="supported",
            interpretation_rule="rank-comparison/v1",
            estimand=estimand,
            applicability=applicability,
            estimate=Decimal("-0.42"),
            uncertainty=StandardError(value=Decimal("0.013")),
        )
        assert value.estimate == Decimal("-0.42")
        assert value.uncertainty == StandardError(value=Decimal("0.013"))

    def test_a_signed_estimate_with_no_uncertainty_is_admitted(self, profile, claim, snapshot):
        estimand = build(profile, claim, snapshot)
        applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        value = AssessmentValue(
            spec="spec-1",
            run="run-1",
            proposition=claim_identity(claim),
            outcome="supported",
            interpretation_rule="rank-comparison/v1",
            estimand=estimand,
            applicability=applicability,
            estimate=Decimal("-0.42"),
        )
        assert value.estimate == Decimal("-0.42") and value.uncertainty is None


# --- what refuses, and that it should ------------------------------------


def test_a_surrogate_family_as_one_contrast_refuses_at_the_fragment(profile, claim, snapshot):
    # Refusal (a): identity against phase-randomized *and* AAFT is three levels on
    # one role. `LevelsContrast` has no third member to name the third level
    # (only `baseline`/`comparison`), so the family enters the only other way
    # it could — as a second contrast — and `build_estimand`'s `**richer`
    # refuses that by name rather than flattening it.
    with pytest.raises(EstimandFragmentRefused, match="one contrast") as excinfo:
        build_estimand(
            profile,
            claim,
            snapshot=snapshot,
            **parts(),
            second_contrast=LevelsContrast(
                role="procedure",
                member=None,
                baseline=Referent(PROC, proc("fourier-phase-randomized")),
                comparison=Referent(PROC, proc("aaft")),
            ),
        )
    assert "second_contrast" in str(excinfo.value)


def test_a_lag_range_as_a_continuous_contrast_over_an_absent_role_refuses_with_the_role_named(profile, claim, snapshot):
    # Refusal (b): a lag range has no role at all — the template's roles are
    # `source` and `procedure`, so a contrast on `lag` is outside them and the
    # refusal names the role and the roles there are.
    with pytest.raises(ContrastRefused, match="role 'lag'") as excinfo:
        build(
            profile,
            claim,
            snapshot,
            contrast=ContinuousContrast(
                role="lag", member=None, quantity=Referent(STAT, stat("co-trev-1-num")), increment=Decimal(1)
            ),
        )
    assert "['procedure', 'source']" in str(excinfo.value)


def test_a_data_dependent_looking_reference_is_admitted_because_the_type_cannot_tell(profile, claim, snapshot):
    # Refusal (c): `reference: E_Q[T]` would be data-dependent, but a finite
    # `Decimal` that merely *looks* like a value a run might compute is
    # admitted — the constructor has no way to see the order of events that
    # would make it a lie, only the shape of the number.
    estimand = build(profile, claim, snapshot, reference=Decimal("0.117"))
    assert estimand.reference == Decimal("0.117")


def test_the_nulls_central_band_refuses_a_rejecting_estimate_but_admits_a_non_rejecting_one(profile, claim, snapshot):
    # Refusal (d): the null's central band as `uncertainty` is caught by
    # `low <= estimate <= high` exactly when the rank rule rejects — a
    # rejecting estimate lies outside the band by construction, and a
    # non-rejecting one lies inside it (the check is structural and cannot tell
    # a true label from a false one when the estimate happens to sit inside
    # the band).
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
            spec="spec-1",
            run="run-1",
            proposition=claim_identity(claim),
            outcome="supported",
            interpretation_rule="rank-comparison/v1",
            estimand=estimand,
            applicability=applicability,
            estimate=Decimal("-0.42"),
            uncertainty=band,
        )

    # Admitted: inside the band, under a label that would in fact be false —
    # built as a real `AssessmentValue`, with its typed members asserted.
    check_uncertainty(band, Decimal("0.05"), "additive")
    value = AssessmentValue(
        spec="spec-1",
        run="run-1",
        proposition=claim_identity(claim),
        outcome="inconclusive",
        interpretation_rule="rank-comparison/v1",
        estimand=estimand,
        applicability=applicability,
        estimate=Decimal("0.05"),
        uncertainty=band,
    )
    assert value.estimate == Decimal("0.05")
    assert value.uncertainty == band


def test_a_float_estimate_refuses_and_is_never_coerced(profile, claim, snapshot):
    # A `float` estimate is refused at the boundary, not coerced to
    # `Decimal` — the same check `AssessmentValue.__post_init__` runs at
    # every construction, derived or stored.
    estimand = build(profile, claim, snapshot)
    applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
    with pytest.raises(MalformedRecord, match="Decimal"):
        AssessmentValue(
            spec="spec-1",
            run="run-1",
            proposition=claim_identity(claim),
            outcome="supported",
            interpretation_rule="rank-comparison/v1",
            estimand=estimand,
            applicability=applicability,
            estimate=-0.42,  # type: ignore[arg-type]
        )
    with pytest.raises(UncertaintyRefused, match="Decimal"):
        check_estimate(-0.42, "additive")  # type: ignore[arg-type]


# --- commensuration -------------------------------------------------


class TestCommensuration:
    def test_two_estimands_differing_only_in_the_statistic_are_not_commensurable(self, profile, claim, snapshot):
        a = build(
            profile, claim, snapshot, measure=Measure(quantity=Referent(STAT, stat("co-trev-1-num")), scale="additive")
        )
        b = build(
            profile, claim, snapshot, measure=Measure(quantity=Referent(STAT, stat("co-trev-2-num")), scale="additive")
        )
        assert not commensurable(a, b)

    def test_two_estimands_differing_only_in_identification_are_commensurable(self, profile, claim, snapshot):
        # `control.identification` is the one member `commensuration_key`
        # removes: it is corpus-local (the fixture's identification vocabulary
        # is local to its corpus), and the key a weight table reads is the one
        # member outside it. A second identification term is added to this
        # test's own snapshot to exercise the difference — the fixture names only
        # `within-series-surrogate`; a distinct scheme is legitimate test data
        # for the sort, not a member the fragment lacks.
        binding = profile.sorts[IDENT].binding
        readable = build_snapshot(
            readable={
                profile.sorts[SERIES].binding: [RECORD],
                profile.sorts[PROC].binding: [proc("identity"), proc("fourier-phase-randomized"), proc("aaft")],
                profile.sorts[STAT].binding: [stat("co-trev-1-num"), stat("co-trev-2-num")],
                binding: [ident("within-series-surrogate"), ident("block-bootstrap-surrogate")],
            }
        )
        a = build(
            profile,
            claim,
            readable,
            control=Control(identification=Referent(IDENT, ident("within-series-surrogate")), conditioning=()),
        )
        b = build(
            profile,
            claim,
            readable,
            control=Control(identification=Referent(IDENT, ident("block-bootstrap-surrogate")), conditioning=()),
        )
        assert commensurable(a, b)

    def test_co_scoped_holds_for_the_empty_applicability_on_both_pairs(self, profile, claim, snapshot):
        a, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        b, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
        assert co_scoped(a, b)
        assert applicability_projection(a) == {} and applicability_projection(b) == {}
