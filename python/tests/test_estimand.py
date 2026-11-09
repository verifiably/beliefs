"""Construction refuses rather than flattens; role contrasts and R12 admission; the projection;
commensuration and scope."""

import re
from decimal import Decimal
from typing import cast

import pytest

from beliefs.claim import Claim, Member, Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.decode import estimand_from_stored
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    DimensionNotApplicabilitySide,
    EstimandError,
    EstimandFragmentRefused,
    EstimandNotAdmitted,
    EstimandSortMismatch,
    MeasureRefused,
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
    admit_estimand,
    applicability_projection,
    build_applicability,
    build_estimand,
    check_estimate,
    check_uncertainty,
    co_scoped,
    commensurable,
    estimand_projection,
    uncertainty_from_mapping,
)
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity
from beliefs.resolution import TermOutcome, build_snapshot

E, O, L, M, I = "testing/entity", "testing/outcome", "testing/level", "testing/measure", "testing/identification"
EV, PR = "testing/event", "testing/product"


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


GENE_X, PHENO_Y = Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")


def affects(profile, cause=GENE_X, effect=PHENO_Y):
    return build_claim(
        profile,
        operator="testing/affects",
        roles={"cause": cause, "effect": effect},
        layer="causal",
        polarity="positive",
    )


def correlates(profile, *parties):
    return build_claim(
        profile,
        operator="testing/correlates-with",
        roles={"parties": [Member(party) for party in parties]},
        layer="statistical",
        polarity="positive",
    )


@pytest.fixture()
def claim(profile):
    return affects(profile)


@pytest.fixture()
def other_claim(profile):
    return affects(profile, cause=Referent(E, "EX:gene-z"))


@pytest.fixture()
def unconsulted():
    return build_snapshot(readable={})


def levels(role="cause", member=None, baseline="EX:ndmm", comparison="EX:pd", sort=L):
    return LevelsContrast(
        role=role, member=member, baseline=Referent(sort, baseline), comparison=Referent(sort, comparison)
    )


def parts(**overrides):
    fields = {
        "contrast": levels(),
        "measure": Measure(quantity=Referent(M, "EX:tpm"), scale="additive"),
        "reference": Decimal(0),
        "control": Control(identification=Referent(I, "EX:observational"), conditioning=()),
    }
    fields.update(overrides)
    return fields


def build(profile, claim, snapshot, **overrides):
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


def stored(claim: Claim, **overrides) -> dict[str, object]:
    """A stored estimand projection, written by hand: the shape-only readers
    restore what no declaration admits, so `build_estimand` cannot make it."""

    def ref(sort, term):
        return {"sort": sort, "term": term}

    projection: dict[str, object] = {
        "claim": claim_identity(claim),
        "operator": claim.operator,
        "contrast": {
            "role": "cause",
            "kind": "levels",
            "baseline": ref(L, "EX:ndmm"),
            "comparison": ref(L, "EX:pd"),
        },
        "measure": {"quantity": ref(M, "EX:tpm"), "scale": "additive"},
        "reference": Decimal(0),
        "control": {"identification": ref(I, "EX:observational"), "conditioning": []},
    }
    projection.update(overrides)
    return projection


def test_a_levels_estimand_builds_and_names_its_claim(profile, claim, unconsulted):
    estimand, receipt = build_estimand(profile, claim, snapshot=unconsulted, **parts())
    assert estimand.claim == claim_identity(claim) and estimand.operator == "testing/affects"
    assert set(receipt.outcomes) == {
        "estimand:contrast.baseline",
        "estimand:contrast.comparison",
        "estimand:measure.quantity",
        "estimand:control.identification",
    }
    assert all(outcome is TermOutcome.NOT_CONSULTED for outcome in receipt.outcomes.values())


def test_a_continuous_estimand_carries_quantity_and_increment(profile, claim, unconsulted):
    estimand = build(
        profile,
        claim,
        unconsulted,
        contrast=ContinuousContrast(
            role="cause", member=None, quantity=Referent(M, "EX:log2-tpm"), increment=Decimal(1)
        ),
    )
    assert estimand_projection(estimand)["contrast"] == {
        "role": "cause",
        "kind": "continuous",
        "quantity": {"sort": M, "term": "EX:log2-tpm"},
        "increment": Decimal(1),
    }


def test_estimand_has_no_public_constructor():
    with pytest.raises(EstimandError, match="use build_estimand"):
        Estimand(claim="c", operator="o", contrast=None, measure=None, reference=Decimal(0), control=None)  # type: ignore[call-arg]


# --- role contrasts (P8) ---------------------------------------------------


def test_contrast_names_a_role(profile, claim, unconsulted):
    contrast = cast(dict, estimand_projection(build(profile, claim, unconsulted))["contrast"])
    assert contrast == {
        "role": "cause",
        "kind": "levels",
        "baseline": {"sort": L, "term": "EX:ndmm"},
        "comparison": {"sort": L, "term": "EX:pd"},
    }
    assert "slot" not in contrast and "member" not in contrast  # absent, never null, on a `one` role


def test_many_role_contrast_names_a_member_by_key(profile, unconsulted):
    composed, decomposed = "EX:caf\u00e9", "EX:cafe\u0301"
    claim = correlates(profile, Referent(EV, composed), Referent(PR, "EX:p-1"))
    estimand, receipt = build_estimand(
        profile, claim, snapshot=unconsulted, **parts(contrast=levels(role="parties", member=Referent(EV, decomposed)))
    )
    assert admit_estimand(profile, estimand, claim, authoring=True) == frozenset({"testing"})
    assert estimand_projection(estimand)["contrast"]["member"] == {"sort": EV, "term": decomposed}  # type: ignore[index]
    assert "estimand:contrast.member" in receipt.outcomes


def test_member_outside_role_refuses(profile, unconsulted):
    claim = correlates(profile, Referent(EV, "EX:e-1"), Referent(PR, "EX:p-1"))
    with pytest.raises(ContrastRefused, match="not a member of the claim's role 'parties'"):
        build(profile, claim, unconsulted, contrast=levels(role="parties", member=Referent(EV, "EX:e-2")))


@pytest.mark.parametrize(
    "make,match",
    [
        (lambda: levels(role="parties", member=None), "is a `many` role"),
        (lambda: levels(member=Referent(E, "EX:gene-x")), "takes no member"),
    ],
)
def test_member_presence_follows_the_role_arity(profile, unconsulted, make, match):
    claims = {"parties": correlates(profile, Referent(EV, "EX:e-1"), Referent(PR, "EX:p-1")), "cause": affects(profile)}
    contrast = make()
    with pytest.raises(ContrastRefused, match=re.escape(match)):
        build(profile, claims[contrast.role], unconsulted, contrast=contrast)


# --- existential admission (R12, case 4b) ------------------------------------


def test_existential_admission_two_declarations(profile, claim, unconsulted):
    # `affects` over `cause: entity, effect: outcome` is admitted by both instantiations,
    # whose estimand declarations differ in their level sort and measure.
    assert profile.admitting("testing/affects", claim.assignment(), authoring=True) == (
        "instantiation:testing/affects-entity-entity",
        "instantiation:testing/affects-entity-outcome",
    )
    via_outcome = build(profile, claim, unconsulted)  # `affects-entity-outcome`: level `level`, measure `measure`
    assert admit_estimand(profile, via_outcome, claim, authoring=True) == frozenset({"testing"})
    via_entity = build(  # `affects-entity-entity`: level `outcome`, measure `outcome`
        profile,
        claim,
        unconsulted,
        contrast=levels(sort=O),
        measure=Measure(quantity=Referent(O, "EX:tpm"), scale="additive"),
    )
    assert admit_estimand(profile, via_entity, claim, authoring=True) == frozenset({"testing"})
    # Each field is admitted by one declaration or the other; the whole by neither.
    with pytest.raises(EstimandNotAdmitted, match="never combined"):
        build(profile, claim, unconsulted, measure=Measure(quantity=Referent(O, "EX:tpm"), scale="additive"))


def test_admission_is_order_independent(base_contract, testing_document, crossing_document, unconsulted):
    # `crossing` also instantiates `affects` over `testing`'s own sorts, with the
    # declaration `affects-entity-outcome` carries: one claim, a fully admitting
    # declaration in each contract. A first-match or last-wins lookup would
    # answer one contract, and which one would follow activation order.
    import copy

    widened = copy.deepcopy(crossing_document)
    widened["instantiations"]["affects-testing-sorts"] = {
        "template": "testing/affects",
        "roles": {"cause": ["testing/entity"], "effect": ["testing/outcome"]},
    }
    widened["estimands"]["instantiation:affects-testing-sorts"] = dict(
        widened["estimands"]["instantiation:affects-local-entity"]
    )

    def admitted(order):
        contracts = {
            "testing": domain.parse_domain_contract(
                testing_document, source="<t>", base=base_contract, predecessor=None
            ),
            "crossing": domain.parse_domain_contract(widened, source="<c>", base=base_contract, predecessor=None),
        }
        profile = compile_profile(base_contract, [contracts[name] for name in order])
        claim = affects(profile)
        estimand = build(profile, claim, unconsulted)
        mixed = estimand_from_stored(
            stored(claim, measure={"quantity": {"sort": O, "term": "EX:tpm"}, "scale": "additive"}), profile=profile
        )
        with pytest.raises(EstimandNotAdmitted):
            admit_estimand(profile, mixed, claim, authoring=False)
        return (
            profile.admitting(claim.operator, claim.assignment(), authoring=False),
            admit_estimand(profile, estimand, claim, authoring=False),
            estimand_projection(estimand),
        )

    forward, backward = admitted(("testing", "crossing")), admitted(("crossing", "testing"))
    assert forward[1] == frozenset({"testing", "crossing"})  # a declaration from each contract admits
    assert "instantiation:crossing/affects-testing-sorts" in forward[0]
    assert forward == backward


def test_authoring_and_decodable_admission_at_the_call_sites(base_contract, testing_document, unconsulted):
    """A claim only a retired instantiation admits: `build_estimand` (authoring)
    refuses its estimand, while the three consumers that read the decodable set —
    the analysis-spec door, the audit's `check_spec_target` and the consulted
    walk — admit it."""
    import copy
    from types import SimpleNamespace

    from fixtures_cut3 import spec_draft, spec_rules

    from beliefs import stored as stored_records
    from beliefs.audit import check_spec_target
    from beliefs.consulted import estimand_contracts
    from beliefs.corpus import CorpusWriter
    from beliefs.projection import project_claim
    from beliefs.spec import freeze

    genesis = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
    document = copy.deepcopy(testing_document)
    document["lineage"] = {"successor": genesis.content_identity}
    document["version"] = genesis.version + 1
    document["instantiations"]["affects-entity-entity"]["retired"] = True
    retired = compile_profile(
        base_contract, [domain.parse_domain_contract(document, source="<r>", base=base_contract, predecessor=genesis)]
    )
    live = compile_profile(base_contract, [genesis])

    claim = affects(live, effect=Referent(E, "EX:gene-y"))  # only `affects-entity-entity` admits entity→entity
    via_entity = {"contrast": levels(sort=O), "measure": Measure(quantity=Referent(O, "EX:tpm"), scale="additive")}
    estimand = build(live, claim, unconsulted, **via_entity)
    assert retired.admitting(claim.operator, claim.assignment(), authoring=True) == ()

    with pytest.raises(EstimandNotAdmitted):
        build(retired, claim, unconsulted, **via_entity)  # authoring: retired excluded
    assert admit_estimand(retired, estimand, claim, authoring=False) == frozenset({"testing"})

    # The walk.
    assert estimand_contracts(estimand, retired, claim) == frozenset({"testing"})

    # The door and the audit, over a spec whose target carries the claim.
    target = stored_records.proposition_node("p-ee", title="p-ee", claim=project_claim(claim))
    spec = stored_records.analysis_spec_node(
        freeze(spec_draft(target=target.id, estimand=estimand), held_rules=spec_rules())
    )
    view = SimpleNamespace(holds=lambda ref: ref == target.id, get=lambda ref: target)
    CorpusWriter._refuse_estimand_target_mismatch(SimpleNamespace(_profile=retired), spec, view=view)  # type: ignore[arg-type]
    outcome = check_spec_target(view, spec, profile=retired)  # type: ignore[arg-type]
    assert outcome.checked and outcome.contradiction is None


def test_decode_is_shape_only_admission_needs_claim(profile):
    # Only `affects-entity-entity` admits `cause: entity, effect: entity`; the
    # estimand carries the claim's true identity and operator but
    # `affects-entity-outcome`'s level sort and measure.
    claim = affects(profile, effect=Referent(E, "EX:gene-y"))
    assert profile.admitting("testing/affects", claim.assignment(), authoring=False) == (
        "instantiation:testing/affects-entity-entity",
    )
    restored = estimand_from_stored(stored(claim), profile=profile)
    assert restored.claim == claim_identity(claim) and restored.operator == claim.operator
    with pytest.raises(EstimandNotAdmitted, match="affects-entity-entity refuses contrast.baseline"):
        admit_estimand(profile, restored, claim, authoring=False)


def test_member_absent_from_claim_refuses(profile):
    claim = correlates(profile, Referent(EV, "EX:e-1"), Referent(PR, "EX:p-1"))
    projection = stored(
        claim,
        contrast={
            "role": "parties",
            "member": {"sort": EV, "term": "EX:e-3"},
            "kind": "levels",
            "baseline": {"sort": L, "term": "EX:ndmm"},
            "comparison": {"sort": L, "term": "EX:pd"},
        },
    )
    restored = estimand_from_stored(projection, profile=profile)
    assert restored.contrast.member == Referent(EV, "EX:e-3")
    with pytest.raises(ContrastRefused, match="not a member"):
        admit_estimand(profile, restored, claim, authoring=False)


def test_foreign_declaration_matching_fields_does_not_admit(
    base_contract, testing_document, crossing_document, unconsulted
):
    testing = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
    crossing = domain.parse_domain_contract(crossing_document, source="<c>", base=base_contract, predecessor=None)
    profile = compile_profile(base_contract, [testing, crossing])
    foreign = profile.estimands["instantiation:crossing/affects-local-entity"]
    native = profile.estimands["instantiation:testing/affects-entity-outcome"]
    assert foreign.schema_projection() == native.schema_projection()  # the same four fields
    claim = affects(profile)
    estimand = build(profile, claim, unconsulted)
    assert admit_estimand(profile, estimand, claim, authoring=True) == frozenset({"testing"})
    assert admit_estimand(profile, estimand, claim, authoring=False) == frozenset({"testing"})


def test_admission_requires_the_claims_identity_and_operator(profile, claim, other_claim, unconsulted):
    estimand = build(profile, claim, unconsulted)
    with pytest.raises(EstimandNotAdmitted, match="not this claim"):
        admit_estimand(profile, estimand, other_claim, authoring=True)


# Every invalid value is built **inside** the assertion: the sealed values refuse
# at construction, so a parametrization that constructed them at collection time
# would fail before `pytest.raises` ran.
@pytest.mark.parametrize(
    "make,error,position",
    [
        (lambda: {"contrast": levels(role="dose")}, ContrastRefused, "role 'dose'"),
        (
            lambda: {
                "contrast": LevelsContrast(
                    role=True,  # type: ignore[arg-type]
                    member=None,
                    baseline=Referent(L, "EX:a"),
                    comparison=Referent(L, "EX:b"),
                )
            },
            ContrastRefused,
            "role name",
        ),
        (
            lambda: {
                "contrast": ContinuousContrast(
                    role=0,  # type: ignore[arg-type]
                    member=None,
                    quantity=Referent(M, "EX:q"),
                    increment=Decimal(1),
                )
            },
            ContrastRefused,
            "role name",
        ),
        (lambda: {"contrast": levels(role="effect")}, EstimandNotAdmitted, "contrast.baseline"),
        (lambda: {"contrast": levels(comparison="EX:ndmm")}, ContrastRefused, "distinct"),
        (
            lambda: {
                "contrast": LevelsContrast(
                    role="cause", member=None, baseline=Referent(E, "EX:a"), comparison=Referent(L, "EX:b")
                )
            },
            EstimandSortMismatch,
            "share a sort",
        ),
        (
            lambda: {
                "contrast": ContinuousContrast(
                    role="cause", member=None, quantity=Referent(M, "EX:q"), increment=Decimal(0)
                )
            },
            ContrastRefused,
            "increment",
        ),
        (
            lambda: {
                "contrast": ContinuousContrast(
                    role="cause", member=None, quantity=Referent(M, "EX:q"), increment=Decimal(-1)
                )
            },
            ContrastRefused,
            "increment",
        ),
        (
            lambda: {
                "contrast": ContinuousContrast(
                    role="cause", member=None, quantity=Referent(E, "EX:q"), increment=Decimal(1)
                )
            },
            EstimandNotAdmitted,
            "contrast.quantity",
        ),
        (
            lambda: {"measure": Measure(quantity=Referent(E, "EX:tpm"), scale="additive")},
            EstimandNotAdmitted,
            "measure.quantity",
        ),
        (
            lambda: {"measure": Measure(quantity=Referent("testing/nowhere", "EX:tpm"), scale="additive")},
            EstimandSortMismatch,
            "does not declare",
        ),
        (lambda: {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="ordinal")}, MeasureRefused, "scale"),
        (
            lambda: {
                "measure": Measure(quantity=Referent(M, "EX:hr"), scale="multiplicative"),
                "reference": Decimal(0),
            },
            ReferenceRefused,
            "multiplicative",
        ),
        (lambda: {"reference": Decimal("NaN")}, ReferenceRefused, "finite"),
        (
            lambda: {"control": Control(identification=Referent(E, "EX:obs"), conditioning=())},
            EstimandNotAdmitted,
            "control.identification",
        ),
        (
            lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(O, "EX:c"),))},
            EstimandNotAdmitted,
            "control.conditioning[0]",
        ),
        (
            lambda: {
                "control": Control(
                    identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c"), Referent(E, "EX:c"))
                )
            },
            ControlRefused,
            "duplicate",
        ),
    ],
)
def test_each_refusal_names_its_position(profile, claim, unconsulted, make, error, position):
    # `position` is matched as a literal substring, not a hand-written regex: an
    # index like `control.conditioning[0]` names a `[0]` character class to an
    # unescaped pattern, matching "the digit 0" rather than the literal brackets.
    with pytest.raises(error, match=re.escape(position)):
        build(profile, claim, unconsulted, **make())


def test_a_float_reference_is_refused_before_the_digest(profile, claim, unconsulted):
    with pytest.raises(ReferenceRefused, match="Decimal"):
        build(profile, claim, unconsulted, reference=0.0)  # type: ignore[arg-type]


def test_an_operator_without_a_declaration_refuses(profile, unconsulted):
    # `measured-by-entity-method` admits this claim and declares no estimand; the
    # other `measured-by` instantiation's declaration does not admit it, so it is not read.
    measured = build_claim(
        profile,
        operator="testing/measured-by",
        roles={"subject": Referent(E, "EX:a"), "instrument": Referent("testing/method", "EX:b")},
        layer="methodological",
    )
    with pytest.raises(EstimandNotAdmitted, match="declares an estimand"):
        build(profile, measured, unconsulted, contrast=levels(role="subject"))


def test_not_member_refuses_and_not_consulted_mints(profile, claim, unconsulted):
    # `level`, `measure` and `identification` all bind the same `{EX, 2026-01-01}`
    # vocabulary in fixtures/contracts/testing.yaml
    # — one SortBinding, shared by value. Declaring it
    # readable makes it readable for every sort built on it, so `parts()`'s
    # measure and control terms must be present too, or they resolve `not-member`
    # against a vocabulary that was in fact read.
    binding = profile.sorts[L].binding
    readable = build_snapshot(readable={binding: ["EX:ndmm", "EX:pd", "EX:tpm", "EX:observational"]})
    estimand, receipt = build_estimand(profile, claim, snapshot=readable, **parts())
    assert receipt.outcomes["estimand:contrast.baseline"] is TermOutcome.MEMBER
    with pytest.raises(UnboundReferent, match="estimand:contrast.comparison"):
        build(
            profile,
            claim,
            readable,
            contrast=levels(comparison="EX:mgus"),
        )
    assert estimand_projection(build(profile, claim, unconsulted)) == estimand_projection(estimand)


def test_the_fragment_refuses_a_second_measure_or_reference(profile, claim, unconsulted):
    with pytest.raises(EstimandFragmentRefused, match="one measure"):
        build_estimand(
            profile, claim, snapshot=unconsulted, **parts(), measures=(parts()["measure"], parts()["measure"])
        )  # type: ignore[arg-type]


class TestProjection:
    def test_conditioning_order_is_inert(self, profile, claim, unconsulted):
        a = build(
            profile,
            claim,
            unconsulted,
            control=Control(
                identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c1"), Referent(E, "EX:c2"))
            ),
        )
        b = build(
            profile,
            claim,
            unconsulted,
            control=Control(
                identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c2"), Referent(E, "EX:c1"))
            ),
        )
        assert estimand_projection(a) == estimand_projection(b)

    def test_swapped_levels_are_two_estimands(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(
            profile,
            claim,
            unconsulted,
            contrast=levels(baseline="EX:pd", comparison="EX:ndmm"),
        )
        assert estimand_projection(a) != estimand_projection(b)

    @pytest.mark.parametrize(
        "override",
        [
            {"measure": Measure(quantity=Referent(M, "EX:other"), scale="additive")},
            {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="multiplicative"), "reference": Decimal(1)},
            {"reference": Decimal("0.5")},
            {"control": Control(identification=Referent(I, "EX:longitudinal"), conditioning=())},
            {"control": Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),))},
        ],
    )
    def test_each_member_moves_the_projection(self, profile, claim, unconsulted, override):
        assert estimand_projection(build(profile, claim, unconsulted)) != estimand_projection(
            build(profile, claim, unconsulted, **override)
        )


class TestPredicates:
    def test_identification_alone_is_outside_the_key(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(
            profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:longitudinal"), conditioning=())
        )
        assert commensurable(a, b)

    def test_two_claims_at_one_operator_are_two_keys(self, profile, claim, other_claim, unconsulted):
        assert not commensurable(build(profile, claim, unconsulted), build(profile, other_claim, unconsulted))

    def test_swapped_levels_and_different_increments_are_not_commensurable(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(
            profile,
            claim,
            unconsulted,
            contrast=levels(baseline="EX:pd", comparison="EX:ndmm"),
        )
        assert not commensurable(a, b)
        c1 = build(
            profile,
            claim,
            unconsulted,
            contrast=ContinuousContrast(role="cause", member=None, quantity=Referent(M, "EX:q"), increment=Decimal(1)),
        )
        c10 = build(
            profile,
            claim,
            unconsulted,
            contrast=ContinuousContrast(role="cause", member=None, quantity=Referent(M, "EX:q"), increment=Decimal(10)),
        )
        assert not commensurable(c1, c10)

    def test_the_scope_counterexample(self, profile, claim, unconsulted):
        six_months, _ = build_applicability(
            profile,
            claim,
            {"testing/follow-up": Qualifier("generic", Referent(L, "EX:six-months"))},
            snapshot=unconsulted,
        )
        everyone, _ = build_applicability(profile, claim, {}, snapshot=unconsulted)
        a, b = build(profile, claim, unconsulted), build(profile, claim, unconsulted)
        assert commensurable(a, b) and not co_scoped(six_months, everyone)
        assert applicability_projection(everyone) == {}

    def test_applicability_refuses_an_undeclared_dimension_and_a_wrong_sort(self, profile, claim, unconsulted):
        from beliefs.errors import RestrictionSortMismatch, UndeclaredDimension

        with pytest.raises(UndeclaredDimension):
            build_applicability(
                profile, claim, {"testing/regime": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted
            )
        with pytest.raises(RestrictionSortMismatch):
            build_applicability(
                profile, claim, {"testing/follow-up": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted
            )

    def test_applicability_side_dimension_typed_without_claim_recheck(self, profile, claim, unconsulted, monkeypatch):
        def refuse(*args, **kwargs):
            raise AssertionError("build_applicability re-typed the claim")

        monkeypatch.setattr(Claim, "_checked", classmethod(refuse))
        applicability, receipt = build_applicability(
            profile,
            claim,
            {"testing/follow-up": Qualifier("generic", Referent(L, "EX:six-months"))},
            snapshot=unconsulted,
        )
        assert applicability_projection(applicability) == {
            "testing/follow-up": {"quantifier": "generic", "restriction": {"sort": L, "term": "EX:six-months"}}
        }
        assert set(receipt.outcomes) == {"restriction:testing/follow-up"}

    def test_claim_side_dimension_in_applicability_refuses(self, profile, claim, unconsulted):
        with pytest.raises(DimensionNotApplicabilitySide, match="testing/population"):
            build_applicability(
                profile,
                claim,
                {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))},
                snapshot=unconsulted,
            )

    def test_an_applicability_dimension_must_apply_to_the_operator(self, profile, unconsulted):
        from beliefs.errors import UndeclaredDimension

        claim = correlates(profile, Referent(EV, "EX:e-1"), Referent(PR, "EX:p-1"))
        with pytest.raises(UndeclaredDimension, match="does not apply"):
            build_applicability(
                profile,
                claim,
                {"testing/follow-up": Qualifier("generic", Referent(L, "EX:six-months"))},
                snapshot=unconsulted,
            )


class TestEstimateAndUncertainty:
    def test_an_unoperable_scale_is_refused(self):
        with pytest.raises(UncertaintyRefused, match="log"):
            check_estimate(Decimal(1), "log")

    def test_a_multiplicative_estimate_must_be_positive(self):
        check_estimate(Decimal("1.2"), "multiplicative")
        with pytest.raises(UncertaintyRefused, match="multiplicative"):
            check_estimate(Decimal(0), "multiplicative")

    @pytest.mark.parametrize(
        "uncertainty,scale",
        [
            (Interval(Decimal("0.5"), Decimal("0.3"), Decimal("0.95")), "additive"),
            (Interval(Decimal(-1), Decimal(1), Decimal(1)), "additive"),
            (Interval(Decimal(0), Decimal(2), Decimal("0.95")), "multiplicative"),
            (StandardError(Decimal("-0.1")), "additive"),
        ],
    )
    def test_ill_formed_uncertainty_is_refused(self, uncertainty, scale):
        with pytest.raises(UncertaintyRefused):
            check_uncertainty(uncertainty, Decimal("0.4") if scale == "additive" else Decimal("1.1"), scale)

    def test_well_formed_uncertainty_passes(self):
        check_uncertainty(Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95")), Decimal("0.4"), "additive")
        check_uncertainty(StandardError(Decimal("0.2")), Decimal("1.1"), "multiplicative")

    def test_uncertainty_from_mapping_decodes_and_checks_in_one_call(self):
        # The one decoder `assess.build_assessment` and `stored.assessment_value`
        # both call, so a rule's raw `{"kind": ...}` output and a stored record's
        # restored `typed` member decode identically and are checked identically.
        interval = uncertainty_from_mapping(
            {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.7"), "level": Decimal("0.95")},
            estimate=Decimal("0.4"),
            scale="additive",
        )
        assert interval == Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95"))
        standard_error = uncertainty_from_mapping(
            {"kind": "standard-error", "value": Decimal("0.2")}, estimate=Decimal("1.1"), scale="multiplicative"
        )
        assert standard_error == StandardError(Decimal("0.2"))

    def test_uncertainty_from_mapping_refuses_an_unrecognized_kind(self):
        with pytest.raises(UncertaintyRefused, match="neither interval nor standard-error"):
            uncertainty_from_mapping(
                {"kind": "confidence-band", "value": Decimal("0.1")}, estimate=Decimal("0.4"), scale="additive"
            )
        with pytest.raises(UncertaintyRefused):
            uncertainty_from_mapping("not-a-mapping", estimate=Decimal("0.4"), scale="additive")

    def test_uncertainty_from_mapping_refuses_no_estimate(self):
        with pytest.raises(UncertaintyRefused, match="no estimate"):
            uncertainty_from_mapping(
                {"kind": "standard-error", "value": Decimal("0.1")}, estimate=None, scale="additive"
            )

    def test_uncertainty_from_mapping_refuses_what_check_uncertainty_refuses(self):
        # The shared decoder runs `check_uncertainty` itself — a decoded interval
        # that excludes the estimate is refused at decode, not deferred to a
        # later construction.
        with pytest.raises(UncertaintyRefused, match="excludes"):
            uncertainty_from_mapping(
                {"kind": "interval", "low": Decimal("0.5"), "high": Decimal("0.7"), "level": Decimal("0.95")},
                estimate=Decimal("0.4"),
                scale="additive",
            )
