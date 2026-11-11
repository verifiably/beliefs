"""Quantification stays in identity while geometry reuses restriction values."""

from fractions import Fraction

import pytest

from beliefs.applicability import (
    Applicability,
    ScopedRestriction,
    applicability_from_stored,
    applicability_projection,
    build_applicability,
    checked,
)
from beliefs.claim import Referent, build_claim
from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import (
    DimensionNotApplicabilitySide,
    MalformedRestriction,
    UnboundReferent,
    UndeclaredDimension,
    UnknownQuantifier,
    WithdrawnFromAuthoring,
)
from beliefs.profile import compile_profile
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.restriction import IntervalRestriction, RuleRestriction, TermRestriction, UnionRestriction, co_scope

RULE = "classification-rule:" + "a" * 64


@pytest.fixture()
def profile(base_contract, testing_document):
    testing_document["dimensions"]["union-stage"] = {
        **testing_document["dimensions"]["stage"],
        "restriction": {"form": "union", "of": {"form": "term", "sort": "stage"}},
    }
    return compile_profile(
        base_contract,
        [
            parse_domain_contract(
                testing_document,
                source="<applicability>",
                base=base_contract,
                predecessor=None,
            )
        ],
    )


def claim(profile):
    return build_claim(
        profile,
        operator="testing/affects",
        layer="causal",
        polarity="positive",
        roles={"cause": Referent("testing/entity", "EX:x"), "effect": Referent("testing/outcome", "EX:y")},
    )


def stage(quantifier="existential"):
    return ScopedRestriction(quantifier, TermRestriction("testing/stage", "EX:rem"))


def test_placement_and_quantifier(profile):
    values = {"testing/stage": stage()}
    value, receipt = build_applicability(profile, claim(profile), values, snapshot=build_snapshot())
    assert (
        applicability_from_stored(applicability_projection(value), profile=profile, operator="testing/affects") == value
    )
    assert receipt.outcomes == {"restriction:testing/stage": TermOutcome.NOT_CONSULTED}
    other = checked(profile, "testing/affects", {"testing/stage": stage("universal")}, authoring=True)
    assert applicability_projection(value) != applicability_projection(other)
    assert co_scope(value.restrictions(), other.restrictions(), profile) == "equal"
    values.clear()
    assert value.values["testing/stage"] == stage()
    with pytest.raises(TypeError):
        value.values["testing/stage"] = stage("universal")  # type: ignore[index]
    with pytest.raises(DimensionNotApplicabilitySide):
        checked(profile, "testing/affects", {"testing/population": stage()}, authoring=True)
    with pytest.raises(UnknownQuantifier):
        checked(profile, "testing/affects", {"testing/stage": stage("nope")}, authoring=True)
    with pytest.raises(UndeclaredDimension):
        checked(profile, "testing/affects", {"testing/unknown": stage()}, authoring=True)
    with pytest.raises(UndeclaredDimension):
        checked(profile, "testing/correlates-with", {"testing/stage": stage()}, authoring=True)


@pytest.mark.parametrize("retired", ["dimension", "sort"])
def test_retired_authoring_and_stored_decode(base_contract, testing_document, retired):
    testing_document["dimensions" if retired == "dimension" else "sorts"]["stage"]["retired"] = True
    profile = compile_profile(
        base_contract,
        [
            parse_domain_contract(
                testing_document,
                source="<retired>",
                base=base_contract,
                predecessor=None,
            )
        ],
    )
    values = {"testing/stage": stage()}
    with pytest.raises(WithdrawnFromAuthoring):
        build_applicability(profile, claim(profile), values, snapshot=build_snapshot())
    projection = {
        "testing/stage": {"quantifier": "existential", "restriction": {"sort": "testing/stage", "term": "EX:rem"}}
    }
    assert applicability_from_stored(projection, profile=profile, operator="testing/affects")


def test_rules_and_duration_terms_survive_projection(profile):
    values = {
        "testing/case-status": ScopedRestriction("existential", RuleRestriction(RULE, ("EX:a",))),
        "testing/follow-up": ScopedRestriction(
            "universal", IntervalRestriction("testing/calendar-month", Fraction(1), None, True, False, "mean-month")
        ),
    }
    authored, receipt = build_applicability(profile, claim(profile), values, snapshot=build_snapshot())
    restored = applicability_from_stored(
        applicability_projection(authored), profile=profile, operator="testing/affects"
    )
    assert restored == authored
    assert restored.rule_ids() == (RULE,)
    duration = restored.restrictions()["testing/follow-up"]
    assert isinstance(duration, IntervalRestriction)
    assert duration.convention == "testing/mean-month"
    assert set(receipt.outcomes) == {"restriction:testing/case-status:0"}


def test_membership_is_checked_for_every_union_member(profile):
    values = {
        "testing/union-stage": ScopedRestriction(
            "existential",
            UnionRestriction((TermRestriction("testing/stage", "EX:a"), TermRestriction("testing/stage", "EX:b"))),
        )
    }
    snapshot = build_snapshot(readable={profile.sorts["testing/stage"].binding: ["EX:a"]})
    with pytest.raises(UnboundReferent):
        build_applicability(profile, claim(profile), values, snapshot=snapshot)
    snapshot = build_snapshot(readable={profile.sorts["testing/stage"].binding: ["EX:a", "EX:b"]})
    _, receipt = build_applicability(profile, claim(profile), values, snapshot=snapshot)
    assert list(receipt.outcomes.values()) == [TermOutcome.MEMBER, TermOutcome.MEMBER]


@pytest.mark.parametrize(
    "value",
    [
        {},
        [],
        {"testing/stage": {}},
        {"testing/stage": {"quantifier": "existential", "restriction": {"sort": "testing/entity", "term": "EX:x"}}},
        {
            "testing/follow-up": {
                "quantifier": "existential",
                "restriction": {"unit": "testing/hour", "low": "NaN", "low_closed": True, "high_closed": False},
            }
        },
        {
            "testing/union-stage": {
                "quantifier": "existential",
                "restriction": [{"sort": "testing/stage", "term": "EX:b"}, {"sort": "testing/stage", "term": "EX:a"}],
            }
        },
    ],
)
def test_malformed_stored_values(profile, value):
    if value == {}:
        assert applicability_from_stored(value, profile=profile, operator="testing/affects") == Applicability({})
    else:
        with pytest.raises(MalformedRestriction):
            applicability_from_stored(value, profile=profile, operator="testing/affects")


def test_public_validation_imports():
    import beliefs.claim as module

    assert callable(module.check_referent)
    assert not hasattr(module, "_check_referent")
