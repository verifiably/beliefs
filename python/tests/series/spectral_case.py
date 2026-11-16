"""Finite held spectral apparatus; no fitter, real signal or empirical claim."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from beliefs import stored
from beliefs.applicability import Applicability, build_applicability
from beliefs.claim import Claim, Referent, build_claim
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Implementation, Procedure, Scale
from beliefs.profile import ProfileSpec
from beliefs.resolution import build_snapshot
from beliefs.series.codec import series_ref_from_projection
from beliefs.series.types import SeriesRef

from .fixtures import SeriesCase

NS_REVISION = "af622a8f6ffa7cf2537072b64aaf00e0bc53aae8"
OBSERVABLE = Observable("spectral-example/synthetic-amplitude", "general/series-view")
PARAMETERS = {
    "source_revision": NS_REVISION,
    "method": "illustrative-spectral-parameterization",
    "floor_model": "window-aware-plateau",
    "welch": "fs=1;window=periodic-hann;detrend=constant;scaling=density",
    "welch_version": "source-pinned;not-executed",
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
            parameters={**PARAMETERS, "view": series.dataset, **(estimator_parameters or {})},
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
