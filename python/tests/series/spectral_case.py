"""Finite held spectral apparatus; no fitter, real signal or empirical claim."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from beliefs import stored
from beliefs.applicability import Applicability, build_applicability
from beliefs.assessment_payload import Uncertainty
from beliefs.claim import Claim, Referent, build_claim
from beliefs.estimand import Estimand, ValueReference
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Implementation, Procedure, Scale
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue
from beliefs.resolution import build_snapshot
from beliefs.series.codec import series_ref_from_projection
from beliefs.series.types import SeriesRef
from beliefs.spec import FrozenSpec

from .fixtures import SeriesCase

NS_REVISION = "af622a8f6ffa7cf2537072b64aaf00e0bc53aae8"
OBSERVABLE = Observable("spectral-example/synthetic-amplitude", "general/series-view")
PARAMETERS = {
    "source_revision": NS_REVISION,
    "method": "illustrative-spectral-parameterization",
    "floor_model": "window-aware-plateau",
    "welch": "fs=1;window=periodic-hann;detrend=constant;scaling=density",
    "welch_version": "scipy-1.18.1;source-uv.lock;not-executed",
    "nperseg": "3",
    "n_source": "3",
    "robust_rule": "k=2.5-MAD;max-refits=5",
    "beta_bounds": "[-2,6]",
    "band_cycles_per_sample": "[0.1,0.2]",
    "band_hz": "[10,20]",
    "spacing_seconds": "0.01",
    "peak_support": "declared-middle-bin",
    "transformation": "general/identity",
}


@dataclass(frozen=True)
class SpectralCase:
    profile: ProfileSpec
    case: SeriesCase
    claim: Claim
    series: SeriesRef
    measure: Measure
    measuring: str
    estimator: str
    applicability: Applicability


def spectral_case(
    profile: ProfileSpec,
    *,
    axis_unit: str = "si-brochure/second",
    spacing: str = "0.01",
    estimator_parameters: Mapping[str, str] | None = None,
) -> SpectralCase:
    case = SeriesCase()
    assay = Procedure(
        kind="general/assay",
        name="Authored finite signal",
        definition="Author the finite synthetic levels; no instrument or physical observable.",
        yields=(OBSERVABLE,),
        scale=Scale(Fraction(-10), Fraction(10), "higher-is-more"),
        validated_in="unknown",
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters={},
        external=None,
    )
    node = stored.procedure_node(assay)
    case.records.nodes[node.id] = node
    measure = Measure(OBSERVABLE, None, node.id, "interval", "level", "general/identity", node.id)
    grid = {"kind": "regular", "spacing": spacing}
    if axis_unit == "si-brochure/second" and spacing == "0.01":
        grid["rate"] = "100"
    axis = {"kind": "elapsed", "unit": axis_unit, "origin": case.origin(), "basis": "synthetic", "grid": grid}
    table = case.table(
        [str(Decimal(spacing) * i) for i in range(3)],
        axis=axis,
        channels={
            "signal": {
                "coordinates": {
                    "quantity_kind": OBSERVABLE.quantity_kind,
                    "scale": node.id,
                    "value_type": "level",
                    "transformation": "general/identity",
                },
                "values": ["1", "2", "1"],
            }
        },
    )
    series = series_ref_from_projection(case.view(table, [0, 1, 2]))
    from beliefs.series.geometry import elapsed_factor

    factor, _ = elapsed_factor(profile, profile.time_roles, axis_unit)
    seconds = Fraction(Decimal(spacing)) * factor
    geometry = {
        "spacing_seconds": str(seconds),
        "band_hz": "[" + ",".join(str(Fraction(v) / seconds) for v in ("0.1", "0.2")) + "]",
    }
    estimator = stored.procedure_node(
        Procedure(
            kind="general/estimator",
            name="Illustrative spectral output",
            definition="Frozen illustrative parameters, never an executed Welch or fitted model.",
            yields=(OBSERVABLE,),
            scale=None,
            validated_in="unknown",
            compatible_with=(),
            evidence=(),
            implementation=Implementation("synthetic-fixture", "sha256:" + "c" * 64),
            inputs=None,
            parameters={**PARAMETERS, **geometry, "view": series.dataset, **(estimator_parameters or {})},
            external=None,
        )
    )
    case.records.nodes[estimator.id] = estimator
    claim = build_claim(
        profile,
        operator="spectral-example/has-spectral-summary",
        roles={"series": Referent("general/series-view", series.dataset)},
        form="polar",
        layer="statistical",
    )
    applicability, _ = build_applicability(profile, claim, {}, snapshot=build_snapshot(readable={}))
    return SpectralCase(profile, case, claim, series, measure, node.id, estimator.id, applicability)


def build_quantity(case: SpectralCase, *, functional: str, reference: ValueReference | None = None) -> Estimand:
    from beliefs.estimand import Control, MeasuredBinding, OutputSpec, build_estimand

    domain = case.profile.functionals[functional].declaration.domain
    return build_estimand(
        case.profile,
        case.claim,
        form="quantity",
        functional=functional,
        bindings={"response": MeasuredBinding("series", None, case.measure, None, None, case.series)},
        outputs={"estimate": OutputSpec("dimensionless", domain)},
        reference=reference,  # pyright: ignore[reportArgumentType] — None deliberately reaches the public refusal.
        control=Control("general/observational", (), "general/single-record-summary", "general/explicit-series-view"),
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=case.applicability,
        snapshot=build_snapshot(kinds={"dataset": (k for k in case.case.records.nodes if k.startswith("dataset:"))}),
        records=case.case.records,
        series_evidence=case.case.evidence(),
    )[0]


def fixture_rules():
    from fixtures_cut3 import spec_rules

    from beliefs.spec import RuleFixture, RuleImplementation

    return {
        "spectral-fixture-inconclusive/v1": RuleImplementation(
            identity="impl-spectral-fixture-inconclusive-v1",
            evaluate=lambda _: {"outcome": "inconclusive"},
            fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "inconclusive"}),),
        ),
        "content-identity-equality/v1": spec_rules()["content-identity-equality/v1"],
    }


def freeze_quantity(case: SpectralCase, estimand: Estimand) -> FrozenSpec:
    from beliefs.projection import claim_identity, project_claim
    from beliefs.spec import Deterministic, SpecDraft, freeze

    from .test_authoring import input_roles

    target = stored.proposition_node(
        claim_identity(case.claim), title="Fixture execution only", claim=project_claim(case.claim)
    )
    draft = SpecDraft(
        target=target.id,
        estimand=estimand,
        method="Illustrative spectral fixture; no fitter executed.",
        assumptions="Matched role/view is authored; validation unknown; zero is a fixture origin.",
        falsification="Fixture-only inconclusive rule makes no substantive claim.",
        input_roles=input_roles(estimand),
        applicability=case.applicability,
        interpretation_rule="spectral-fixture-inconclusive/v1",
        equivalence_rule="content-identity-equality/v1",
        parameters={},
        nondeterminism=Deterministic(),
        registers=(),
        standing="empirical",
        model=None,
    )
    return freeze(
        draft,
        held_rules=fixture_rules(),
        rule_procedures={draft.interpretation_rule: case.estimator},
        profile=case.profile,
        claim=case.claim,
        records=case.case.records,
        series_evidence=case.case.evidence(),
    )


def fixture_value(spec: FrozenSpec, *, estimate: Decimal, uncertainty: Uncertainty = None) -> AssessmentValue:
    from candidate_contracts import spectral_profile

    from beliefs.profile import shipped_base_contract

    # Single-output spectral reader profile; diagnostic quantities use their explicit diagnostic profile.
    node = stored.assessment_node(
        "spectral-fixture",
        title="Illustrative, never published",
        spec=spec.identity,
        run="run:" + "f" * 64,
        proposition=spec.target,
        outcome="inconclusive",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
        estimates={"estimate": estimate},
        uncertainty=uncertainty,
    )
    return stored.assessment_value(node, profile=spectral_profile(shipped_base_contract()))
