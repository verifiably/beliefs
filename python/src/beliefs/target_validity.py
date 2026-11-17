"""Current-profile scope validity of an existing assessed target.

Scope containment design §7.3. A frozen target keeps its bytes, key and
body-derived dependency entries under every profile. Its current use is still
refused when the scope-dependent validity assumptions its held bindings now
require, under this profile's checked comparisons, are not all represented in
its frozen estimand: a retired proof must not silently preserve a waiver.
Additional explicit assumptions remain allowed. Nothing here mints or rewrites a
target.
"""

from __future__ import annotations

from dataclasses import dataclass

from beliefs.aptness import validity_requirements
from beliefs.assumptions import AssumptionInstance, instance_projection
from beliefs.errors import MalformedRecord
from beliefs.estimand import MeasuredBinding, measured_bindings
from beliefs.identity import v1
from beliefs.procedure import Procedure
from beliefs.proxy_model import ProxyModel
from beliefs.scope_checks import ScopeReader
from beliefs.target import AssessedTarget

__all__ = ["ScopeRequirements", "target_scope_requirements"]


@dataclass(frozen=True)
class ScopeRequirements:
    """The scope-dependent validity assumptions a target requires now, and those
    of them its frozen estimand does not carry; both sorted by canonical projection."""

    required: tuple[AssumptionInstance, ...]
    missing: tuple[AssumptionInstance, ...]


def target_scope_requirements(target: AssessedTarget, *, reader: ScopeReader) -> ScopeRequirements:
    """Rederive the target's scope-dependent validity requirements from its actual
    held procedure and proxy bodies and its applicability, under ``reader``'s profile."""
    scope = target.applicability.restrictions()
    required: dict[bytes, AssumptionInstance] = {}
    for binding in measured_bindings(target.estimand):
        procedure = reader.held(binding.measure.procedure)
        if not isinstance(procedure, Procedure):
            raise MalformedRecord("a measured binding's procedure reference must name a procedure")
        proxy_id = binding.proxy if isinstance(binding, MeasuredBinding) else None
        proxy = None
        if proxy_id is not None:
            proxy = reader.held(proxy_id)
            if not isinstance(proxy, ProxyModel):
                raise MalformedRecord("a measured binding's proxy reference must name a proxy model")
        for instance in validity_requirements(scope, binding.measure.procedure, procedure, proxy_id, proxy, reader):
            required[v1.encode(instance_projection(instance))] = instance
    present = {v1.encode(instance_projection(instance)) for instance in target.estimand.assumptions}
    keys = sorted(required)
    return ScopeRequirements(
        tuple(required[key] for key in keys), tuple(required[key] for key in keys if key not in present)
    )
