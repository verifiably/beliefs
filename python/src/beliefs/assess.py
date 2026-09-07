"""Derive an assessment from one completed assessment run (R22, R7).

Computation §5.1 has one constructor: it resolves the run's frozen spec and
bound interpretation implementation, evaluates only the result manifest, and
derives every assessment facet. No facet is authored through this API.

Assessments have no revisions: changing the rule or applicability requires a
successor spec and a new run. Explicit import, raw-write, and audit negatives
remain deferred with the store and audit (cut 3 §4.2).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast, final

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
from beliefs.errors import MalformedClosure, MalformedRecord, SignatureRefused
from beliefs.recipe import RunClosure
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.sealed import sealed
from beliefs.spec import FrozenSpec, RuleImplementation, implementation_conforms
from beliefs.stored import typed_ref

__all__ = ["AssessmentFinding", "build_assessment", "run_record"]


@sealed
@final
@dataclass(frozen=True)
class AssessmentFinding:
    """A machinery failure over a completed run, never a scientific outcome."""

    run: str
    reason: str

    def __post_init__(self) -> None:
        if type(self.run) is not str or type(self.reason) is not str:
            raise MalformedRecord("an assessment finding's run and reason must be strings")


def build_assessment(
    run: RunClosure,
    *,
    specs: Mapping[str, FrozenSpec],
    implementations: Mapping[str, RuleImplementation],
) -> AssessmentValue | AssessmentFinding:
    """Derive the only assessment facet available for ``run``."""
    if type(run) is not RunClosure:
        raise MalformedClosure("build_assessment requires a RunClosure")
    if run.recipe.shape == "dataset-production":
        raise SignatureRefused("a dataset-production run has no `assesses` descendant (R7)")

    run_address = run.address()
    try:
        spec_identity = cast(str, run.recipe.spec_identity)
        spec = specs[spec_identity]
        if type(spec) is not FrozenSpec or spec.identity != spec_identity:
            raise TypeError("the resolved spec does not match the run's frozen spec identity")
        implementation_identity = dict(run.recipe.rule_bindings)[spec.interpretation_rule]
        implementation = implementations[implementation_identity]
        if (
            type(implementation) is not RuleImplementation
            or implementation.identity != implementation_identity
            or not implementation_conforms(implementation)
        ):
            raise TypeError("the resolved interpretation implementation does not match its frozen binding")
        raw = implementation.evaluate(run.result)
        if not isinstance(raw, Mapping):
            raise TypeError("the interpretation rule returned no facet mapping")
        derived = cast(Mapping[str, object], raw)
        outcome = derived.get("outcome")
        estimate = derived.get("estimate")
        uncertainty = derived.get("uncertainty")
        if type(outcome) is not str:
            raise TypeError("the interpretation rule returned no string outcome")
        if estimate is not None and type(estimate) is not str:
            raise TypeError("the interpretation rule returned a non-string estimate")
        if uncertainty is not None and type(uncertainty) is not str:
            raise TypeError("the interpretation rule returned non-string uncertainty")
        return AssessmentValue(
            spec=spec.identity,
            run=run_address,
            proposition=spec.target,
            outcome=outcome,
            interpretation_rule=spec.interpretation_rule,
            estimate=estimate,
            uncertainty=uncertainty,
            estimand=spec.estimand,
            applicability=spec.applicability,
        )
    except Exception as error:  # noqa: BLE001 — arbitrary rule machinery records a finding
        return AssessmentFinding(run=run_address, reason=f"evaluation-failed: {error}")


def run_record(run: RunClosure) -> RunValue:
    """Bridge a run closure into the cut-2 admission record."""
    if type(run) is not RunClosure:
        raise MalformedClosure("run_record requires a RunClosure")
    return RunValue(
        ref=typed_ref("run", run.address()),
        spec=run.recipe.spec_identity or "",
        inputs=tuple(
            RunInput(
                role=entry.role,
                dataset=DatasetDeclaration(resources=(ResourceDeclaration(name=entry.dataset, digest=entry.content),)),
            )
            for entry in run.recipe.inputs
        ),
    )
