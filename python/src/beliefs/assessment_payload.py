"""Named decimal outputs and their interval, SE, covariance or curve payloads."""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import TypeAlias

from beliefs import _measurement_record as wire
from beliefs.errors import MalformedRecord, ReferenceRefused
from beliefs.estimand import Estimand, LagBinding, finite, in_domain


@dataclass(frozen=True)
class Interval:
    low: Decimal
    high: Decimal
    level: Decimal

    def __post_init__(self) -> None:
        if _number(self.low) > _number(self.high) or not 0 < _number(self.level) < 1:
            raise MalformedRecord("interval bounds must be ordered and confidence level strictly between zero and one")


@dataclass(frozen=True)
class StandardError:
    value: Decimal

    def __post_init__(self) -> None:
        if _number(self.value) < 0:
            raise MalformedRecord("standard error must be nonnegative")


@dataclass(frozen=True)
class Covariance:
    parameters: tuple[str, ...]
    matrix: tuple[tuple[Decimal, ...], ...]

    def __post_init__(self) -> None:
        names = tuple(self.parameters)
        rows = tuple(tuple(row) for row in self.matrix)
        size = len(names)
        if size < 2 or len(set(names)) != size or any(not isinstance(n, str) or not n for n in names):
            raise MalformedRecord("covariance requires two or more distinct named parameters")
        if len(rows) != size or any(len(row) != size for row in rows):
            raise MalformedRecord("covariance matrix shape must match its parameters")
        for i in range(size):
            for j in range(size):
                if _number(rows[i][j]) != _number(rows[j][i]):
                    raise MalformedRecord("covariance must be symmetric")
            if rows[i][i] < 0:
                raise MalformedRecord("covariance diagonal must be nonnegative")
        order = sorted(range(size), key=lambda i: names[i])
        object.__setattr__(self, "parameters", tuple(names[i] for i in order))
        object.__setattr__(self, "matrix", tuple(tuple(rows[i][j] for j in order) for i in order))


ScalarUncertainty: TypeAlias = Interval | StandardError
Uncertainty: TypeAlias = Mapping[str, ScalarUncertainty] | Covariance | None


@dataclass(frozen=True)
class CurvePoint:
    lag: Decimal
    estimate: Decimal
    uncertainty: ScalarUncertainty | None

    def __post_init__(self) -> None:
        _number(self.lag)
        _number(self.estimate)
        if self.uncertainty is not None and not isinstance(self.uncertainty, (Interval, StandardError)):
            raise MalformedRecord("curve uncertainty must be an interval or standard error")


def _number(value: object) -> Decimal:
    try:
        return finite(value, "payload number")
    except ReferenceRefused as error:
        raise MalformedRecord(str(error)) from error


def _domain(value: object, domain: str) -> Decimal:
    try:
        return in_domain(value, domain)
    except ReferenceRefused as error:
        raise MalformedRecord(str(error)) from error


def _check_scalar(value: ScalarUncertainty, estimate: Decimal, domain: str, representation: str) -> None:
    if isinstance(value, Interval) and representation == "interval":
        if not _domain(value.low, domain) <= estimate <= _domain(value.high, domain):
            raise MalformedRecord("interval must contain its estimate")
    elif isinstance(value, StandardError) and representation == "standard-error":
        if _number(value.value) < 0:
            raise MalformedRecord("standard error must be nonnegative")
    else:
        raise MalformedRecord("uncertainty disagrees with the estimand's representation")


def check_outputs(estimates: Mapping[str, Decimal], uncertainty: Uncertainty, estimand: Estimand) -> None:
    if not isinstance(estimates, Mapping):
        raise MalformedRecord("estimates must be a named mapping")
    if estimates and set(estimates) != set(estimand.outputs):
        raise MalformedRecord("estimate names must exactly match the output set")
    for name, value in estimates.items():
        _domain(value, estimand.outputs[name].domain)
    if uncertainty is None or uncertainty == {}:
        return
    if not estimates:
        raise MalformedRecord("uncertainty requires estimates")
    if isinstance(uncertainty, Covariance):
        if estimand.uncertainty != "covariance" or set(uncertainty.parameters) != set(estimand.outputs):
            raise MalformedRecord("covariance parameter names and representation must match the estimand")
    elif isinstance(uncertainty, Mapping):
        if set(uncertainty) != set(estimates):
            raise MalformedRecord("uncertainty names must match estimates")
        for name, value in uncertainty.items():
            _check_scalar(value, estimates[name], estimand.outputs[name].domain, estimand.uncertainty)
    else:
        raise MalformedRecord("unsupported uncertainty payload")


def check_payload(
    estimand: Estimand,
    estimates: Mapping[str, Decimal],
    uncertainty: Uncertainty,
    curves: Mapping[str, tuple[CurvePoint, ...]],
) -> None:
    check_outputs(estimates, uncertainty, estimand)
    if not isinstance(curves, Mapping):
        raise MalformedRecord("curves must be a mapping")
    if not curves:
        return
    lag = estimand.bindings.get("lag")
    if estimand.form != "event-locked" or not isinstance(lag, LagBinding) or lag.windows:
        raise MalformedRecord("curves require event-locked targets without window contrasts")
    if set(curves) != set(estimand.outputs):
        raise MalformedRecord("curve names must match the output set")
    for name, points in curves.items():
        if not isinstance(points, tuple) or not points or any(not isinstance(p, CurvePoint) for p in points):
            raise MalformedRecord("a curve is a nonempty tuple of CurvePoints")
        if any(a.lag >= b.lag for a, b in itertools.pairwise(points)):
            raise MalformedRecord("curve lags must be strictly increasing")
        for point in points:
            _domain(point.estimate, estimand.outputs[name].domain)
            if point.uncertainty is not None:
                _check_scalar(point.uncertainty, point.estimate, estimand.outputs[name].domain, estimand.uncertainty)


def uncertainty_projection(value: Uncertainty | ScalarUncertainty) -> object:
    if isinstance(value, Interval):
        return {"kind": "interval", "low": value.low, "high": value.high, "level": value.level}
    if isinstance(value, StandardError):
        return {"kind": "standard-error", "value": value.value}
    if isinstance(value, Covariance):
        return {
            "kind": "covariance",
            "parameters": list(value.parameters),
            "matrix": [list(row) for row in value.matrix],
        }
    if isinstance(value, Mapping):
        return {name: uncertainty_projection(row) for name, row in value.items()}
    raise MalformedRecord("absent uncertainty has no projection")


def _scalar_from(value: object) -> ScalarUncertainty:
    if not isinstance(value, Mapping):
        raise MalformedRecord("uncertainty must be a mapping")
    if value.get("kind") == "interval":
        row = wire.shape(value, {"kind", "low", "high", "level"})
        return Interval(_number(row["low"]), _number(row["high"]), _number(row["level"]))
    row = wire.shape(value, {"kind", "value"})
    if row["kind"] != "standard-error":
        raise MalformedRecord("unsupported scalar uncertainty kind")
    return StandardError(_number(row["value"]))


def uncertainty_from_projection(value: object) -> Uncertainty:
    if not isinstance(value, Mapping):
        raise MalformedRecord("uncertainty must be a mapping")
    if value.get("kind") == "covariance":
        row = wire.shape(value, {"kind", "parameters", "matrix"})
        return Covariance(
            wire.sequence(row["parameters"], lambda n: wire.text(n, "parameter")),
            wire.sequence(row["matrix"], lambda row: wire.sequence(row, _number)),
        )
    return MappingProxyType({wire.text(name, "parameter"): _scalar_from(row) for name, row in value.items()})


def payload_projection(
    estimates: Mapping[str, Decimal], uncertainty: Uncertainty, curves: Mapping[str, tuple[CurvePoint, ...]]
) -> dict[str, object]:
    body: dict[str, object] = {}
    if estimates:
        body["estimates"] = dict(estimates)
    if uncertainty is not None and uncertainty != {}:
        body["uncertainty"] = uncertainty_projection(uncertainty)
    if curves:
        body["curves"] = {
            name: [
                {
                    "lag": p.lag,
                    "estimate": p.estimate,
                    **({"uncertainty": uncertainty_projection(p.uncertainty)} if p.uncertainty is not None else {}),
                }
                for p in points
            ]
            for name, points in curves.items()
        }
    return body


def payload_from_projection(
    value: object, estimand: Estimand
) -> tuple[Mapping[str, Decimal], Uncertainty, Mapping[str, tuple[CurvePoint, ...]]]:
    body = wire.shape(value, set(), {"estimates", "uncertainty", "curves"})
    raw_estimates = body.get("estimates", {})
    raw_curves = body.get("curves", {})
    if not isinstance(raw_estimates, Mapping) or not isinstance(raw_curves, Mapping):
        raise MalformedRecord("estimates and curves must be mappings")
    estimates = MappingProxyType(
        {wire.text(name, "output name"): _number(value) for name, value in raw_estimates.items()}
    )
    uncertainty = uncertainty_from_projection(body["uncertainty"]) if "uncertainty" in body else None

    def point(value: object) -> CurvePoint:
        row = wire.shape(value, {"lag", "estimate"}, {"uncertainty"})
        return CurvePoint(
            _number(row["lag"]),
            _number(row["estimate"]),
            _scalar_from(row["uncertainty"]) if "uncertainty" in row else None,
        )

    curves = MappingProxyType(
        {wire.text(name, "output name"): wire.sequence(rows, point) for name, rows in raw_curves.items()}
    )
    check_payload(estimand, estimates, uncertainty, curves)
    return estimates, uncertainty, curves
