"""Verify route M projections and admission (V5, V7) without freezing or running a target."""

from typing import Any, cast

import pytest
from candidate_contracts import case_profile
from reproduction.type_target import OBSERVABLE
from test_convert import snapshot as comparison_snapshot

from beliefs import errors
from beliefs.applicability import applicability_projection
from beliefs.claim import Claim, Referent
from beliefs.estimand import admit_estimand, estimand_projection
from beliefs.measurement import Aspect, Observable
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity, project_claim
from beliefs.restriction import RuleRestriction, compare_scopes
from beliefs.target import AssessedTarget, target_projection
from beliefs.target_comparison import (
    AssessedProposition,
    TargetConvertible,
    TargetNotConvertible,
    convertibility,
    synthesis,
)

from .cases import (
    GENE,
    LONG_COVID,
    MECFS,
    OTHER_GENE,
    RNA,
    RULE_SCOPE,
    RULE_SORT,
    assay,
    concept_claim,
    contrast,
    held,
    label,
    pair_claim,
    rule_claim,
    rule_id,
    scope,
    target,
)

THRESHOLD = "case-c-threshold"
RECOVERED = "case-c-recovered"


@pytest.fixture
def profile(base_contract):
    return case_profile(base_contract)


def _case_c_claim(profile, rule=THRESHOLD):
    return rule_claim(profile, rule, outcome="long-covid", comparator="comparison-group")


def case_c(
    profile: ProfileSpec,
    claim: Claim,
    *,
    procedure: str = "blood",
    rule: str = THRESHOLD,
    classes: tuple[str, str] = ("comparison-group", "long-covid"),
    origin: str | None = "infection",
    condition: Referent | None = LONG_COVID,
    window: tuple[int, int] = (720, 2160),
) -> AssessedTarget:
    records, resolution, assays = held(THRESHOLD, RECOVERED)
    applicability = scope(profile, claim, resolution, condition=condition, origin=origin, window=window)
    estimand = contrast(
        profile,
        claim,
        applicability,
        records=records,
        snapshot=resolution,
        assay_id=assays[procedure],
        rule=rule,
        classes=classes,
    )
    return target(profile, estimand, applicability, records)


def test_the_response_is_the_measurement_the_phf19_reproduction_uses():
    assert RNA == OBSERVABLE


def test_each_claim_takes_its_own_target(profile):
    claims = (_case_c_claim(profile), concept_claim(profile, LONG_COVID))
    rule_based, concept_based = (case_c(profile, claim) for claim in claims)
    for built, own, other in ((rule_based, *claims), (concept_based, *reversed(claims))):
        assert admit_estimand(profile, built.estimand, own, authoring=True) == frozenset({"case-comparisons"})
        with pytest.raises(errors.EstimandNotAdmitted, match="estimand names a different claim"):
            admit_estimand(profile, built.estimand, other, authoring=True)

    left, right = target_projection(rule_based), target_projection(concept_based)
    assert left != right
    for projection in (left, right):
        del cast(dict[str, Any], projection["estimand"])["claim"]
    assert left == right


@pytest.mark.parametrize(
    "change,estimand_equal,applicability_equal",
    [
        ({"procedure": "muscle"}, False, True),
        ({"window": (720, 4320)}, True, False),
        ({"origin": "symptom"}, False, False),
        ({"rule": RECOVERED}, False, True),
        ({"classes": ("never-defined-a", "never-defined-b")}, False, True),
    ],
    ids=["procedure", "window", "origin", "other-rule", "unknown-classes"],
)
def test_what_moves_a_target_on_the_fixed_rule_level_claim(profile, change, estimand_equal, applicability_equal):
    claim = _case_c_claim(profile)
    first = case_c(profile, claim)
    variant = case_c(profile, claim, **change)
    assert admit_estimand(profile, variant.estimand, claim, authoring=True) == frozenset({"case-comparisons"})
    first_projection, variant_projection = (estimand_projection(value.estimand) for value in (first, variant))
    assert (first_projection == variant_projection) is estimand_equal
    assert (
        applicability_projection(first.applicability) == applicability_projection(variant.applicability)
    ) is applicability_equal
    assert target_projection(first) != target_projection(variant)
    if "rule" in change:
        first_group, variant_group = (
            cast(dict[str, Any], projection["bindings"])["grouping"]
            for projection in (first_projection, variant_projection)
        )
        assert first_group.pop("rule") == rule_id(THRESHOLD)
        assert variant_group.pop("rule") == rule_id(RECOVERED)
        assert first_group == variant_group
        assert all(first_projection[key] == variant_projection[key] for key in ("bindings", "control", "functional"))


def test_a_grouping_on_another_rule_is_admitted_against_the_claim(profile):
    # The generic kernel omits the reproduction driver's check that the selected rule matches.
    claim = _case_c_claim(profile)
    built = case_c(profile, claim, rule=RECOVERED)
    assert admit_estimand(profile, built.estimand, claim, authoring=True) == frozenset({"case-comparisons"})


def test_neither_rows_are_equalities(profile):
    claim = _case_c_claim(profile)
    first, second = (case_c(profile, claim, condition=None, origin=None) for _ in range(2))
    # Absent scopes conflate scenarios whose scope is unspecified.
    assert target_projection(first) == target_projection(second)
    assert (
        compare_scopes(first.applicability.restrictions(), second.applicability.restrictions(), profile).verdict
        == "equal"
    )

    # Specimen is a scenario distinction with no typed place in the shared assay target.
    scenarios = {specimen: case_c(profile, claim, procedure="shared") for specimen in ("blood", "muscle")}
    assert target_projection(scenarios["blood"]) == target_projection(scenarios["muscle"])
    assert target_projection(case_c(profile, claim, procedure="blood")) != target_projection(
        case_c(profile, claim, procedure="muscle")
    )


def test_same_label_under_two_rules_is_two_claims(profile):
    first, second = (_case_c_claim(profile, name) for name in (THRESHOLD, RECOVERED))
    assert claim_identity(first) != claim_identity(second)
    first_wire, second_wire = project_claim(first), project_claim(second)
    assert {k for k in first_wire if first_wire[k] != second_wire[k]} == {"roles"}
    scopes = [
        {RULE_SCOPE: RuleRestriction(rule_id(name), (label("comparison-group").term,))}
        for name in (THRESHOLD, RECOVERED)
    ]
    assert compare_scopes(scopes[0], scopes[1], profile).verdict == "unknown"


def test_aspect_and_tissue_on_the_observable(profile):
    claim = _case_c_claim(profile)
    records, resolution, _ = held(THRESHOLD)
    applicability = scope(profile, claim, resolution)
    unqualified = Observable(RNA.quantity_kind, RNA.bearer_sort)
    procedure = records.put(assay("blood", yields=(RNA, unqualified)))
    projections = []
    for response in (RNA, unqualified):
        built = contrast(
            profile,
            claim,
            applicability,
            records=records,
            snapshot=resolution,
            assay_id=procedure,
            rule=THRESHOLD,
            observable=response,
        )
        assert admit_estimand(profile, built, claim, authoring=True) == frozenset({"case-comparisons"})
        projections.append(target_projection(target(profile, built, applicability, records)))
    assert projections[0] != projections[1]
    both = cast(Any, (RNA.aspect, RNA.aspect))
    with pytest.raises(errors.MalformedMeasure, match="observable aspect must be an Aspect"):
        Observable(RNA.quantity_kind, RNA.bearer_sort, aspect=both)
    tissue = Observable(RNA.quantity_kind, RNA.bearer_sort, Aspect("anatomy/tissue", "tissue:muscle"))
    tissue_assay = records.put(assay("blood", yields=(tissue,)))
    with pytest.raises(errors.UndeclaredSort, match="anatomy/tissue"):
        contrast(
            profile,
            claim,
            applicability,
            records=records,
            snapshot=resolution,
            assay_id=tissue_assay,
            rule=THRESHOLD,
            observable=tissue,
        )


@pytest.mark.parametrize(
    "observable,member,error,message",
    [
        (
            Observable("general/concentration", "biology/gene"),
            GENE,
            errors.UndeclaredQuantityKind,
            "undeclared quantity kind 'general/concentration'",
        ),
        (
            Observable("general/relative-abundance", "biology/protein"),
            GENE,
            errors.MeasurementNotAdmitted,
            "the source bearer and quantity kind are not admitted",
        ),
        (
            RNA,
            Referent(RULE_SORT, rule_id("case-a-study")),
            errors.ProxyRequired,
            "a bearer change requires a proxy model",
        ),
    ],
    ids=["concentration", "protein-bearer", "proxy"],
)
def test_case_a_protein_response_has_no_admitted_route(profile, observable, member, error, message):
    rule = "case-a-study"
    claim = rule_claim(profile, rule, outcome="ptlds", comparator="return-to-health")
    records, resolution, _ = held(rule)
    applicability = scope(profile, claim, resolution, condition=None, origin=None)
    procedure = records.put(assay(None, yields=(observable,)))
    with pytest.raises(error, match=message):
        contrast(
            profile,
            claim,
            applicability,
            records=records,
            snapshot=resolution,
            assay_id=procedure,
            rule=rule,
            classes=("return-to-health", "ptlds"),
            observable=observable,
            member=member,
        )


def test_only_a_claim_with_a_gene_party_carries_the_response(profile):
    genes = pair_claim(profile, GENE, OTHER_GENE)
    assert admit_estimand(profile, case_c(profile, genes).estimand, genes, authoring=True) == frozenset(
        {"case-comparisons"}
    )
    diseases = pair_claim(profile, LONG_COVID, MECFS)
    rule_pair = pair_claim(profile, Referent(RULE_SORT, rule_id(THRESHOLD)), Referent(RULE_SORT, rule_id(RECOVERED)))
    for claim in (diseases, rule_pair):
        with pytest.raises(errors.ContrastRefused, match="the bound member is not in the claim role"):
            case_c(profile, claim)


def test_whole_target_verdicts(profile):
    claim = _case_c_claim(profile)
    records, _, _ = held(THRESHOLD, RECOVERED)
    snap = comparison_snapshot(records, profile=profile)
    original = AssessedProposition(claim, case_c(profile, claim), "rule")
    for variant, expected_type, expected_reason in (
        (case_c(profile, claim, window=(720, 4320)), TargetConvertible, None),
        (case_c(profile, claim, procedure="muscle"), TargetNotConvertible, "no conversion between scales"),
        (case_c(profile, claim, rule=RECOVERED), TargetNotConvertible, "target"),
    ):
        other = AssessedProposition(claim, variant, "rule")
        result = convertibility(original, other, profile=profile, snapshot=snap, snapshot_identity="synthetic")
        assert isinstance(result, expected_type)
        if isinstance(result, TargetNotConvertible):
            assert result.reason == expected_reason
    # The candidate profile lacks the transport-exchangeability assumption kind.
    other = AssessedProposition(claim, case_c(profile, claim, origin="symptom"), "rule")
    with pytest.raises(errors.ProfileError, match="exactly one transport-exchangeability assumption kind"):
        synthesis(
            original,
            other,
            profile=profile,
            snapshot=snap,
            snapshot_identity="synthetic",
            observable_proxies=lambda _a, _b: (),
        )
