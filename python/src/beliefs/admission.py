"""Route-specific admission over frozen targets and explicitly supplied evidence.

Every route checks the run, heldness of every run input, verification and frozen
normative dependencies. Empirical assessments also require observes inputs;
model routes require the model and its declared input digests held. Recursive
calibration eligibility is supplied by the captured dependency evidence.
Refusal reasons retain their ordered, stable prefixes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from beliefs.dataset import ByteObservation, DatasetDeclaration, Held, admission_state, dataset_address
from beliefs.eligibility import Eligible
from beliefs.evidence import DependencyEvidence
from beliefs.procedure import Procedure
from beliefs.record import AssessmentValue, RunValue
from beliefs.sealed import sealed
from beliefs.stored import typed_ref
from beliefs.verification import ADMITTED, Verification, lifecycle_state

__all__ = ["AdmissionRefused", "Admitted", "admit", "vocabulary_availability"]


@sealed
@final
@dataclass(frozen=True)
class Admitted:
    assessment: str


@sealed
@final
@dataclass(frozen=True)
class AdmissionRefused:
    assessment: str
    reason: str
    """Prefix-stable: `run-mismatch` | `no-observes-input` | `input-not-held` |
    `not-admitted-verification-state`, followed by `: detail`."""


def admit(
    assessment: AssessmentValue,
    run: RunValue,
    observations: Mapping[str, tuple[ByteObservation, ...]],
    verifications: tuple[Verification, ...],
    dependencies: DependencyEvidence,
) -> Admitted | AdmissionRefused:
    """The gate, in a fixed order the evaluator's absence-reasons rely on:
    run-mismatch, then observes-presence, then heldness of every input, then verification state."""
    uid = assessment.identity()
    if run.ref != typed_ref("run", assessment.run):
        # Both sides in the typed spelling: `assessment.run` is the bare closure
        # address and `run.ref` the typed reference, so printing them as stored
        # reads "names 'run-1', given 'run-1'" of two values that really do differ.
        return AdmissionRefused(
            uid, f"run-mismatch: assessment names {typed_ref('run', assessment.run)!r}, given {run.ref!r}"
        )
    if assessment.standing == "empirical" and not any(i.role == "observes" for i in run.inputs):
        return AdmissionRefused(uid, "no-observes-input: reads inputs never confer eligibility, in any quantity")
    for run_input in run.inputs:
        address = dataset_address(run_input.dataset)
        supplied = observations.get(address, ()) if address is not None else ()
        state = admission_state(run_input.dataset, supplied)
        if not isinstance(state, Held):
            return AdmissionRefused(
                uid, f"input-not-held: a {run_input.role} input reads {type(state).__name__} under these observations"
            )
    if lifecycle_state(tuple(v for v in verifications if v.assessment == uid)) != ADMITTED:
        return AdmissionRefused(uid, "not-admitted-verification-state: only clean-environment passes are admitted")
    if assessment.standing != "empirical":
        model = dependencies.records.get(assessment.model or "")
        held = {o.digest for observations_at in observations.values() for o in observations_at}
        if (
            not isinstance(model, Procedure)
            or model.inputs is None
            or not all(digest in held for digest in (*model.inputs.datasets, *model.inputs.code))
        ):
            return AdmissionRefused(uid, "model-not-held: model procedure or input digest is not held")
    for dependency in assessment.dependencies:
        if not isinstance(dependencies.closure.verdicts.get(dependency.id), Eligible):
            return AdmissionRefused(uid, f"dependency-ineligible: {dependency.id}")
        if dependency.facet_digest is not None:
            basis = dependencies.assessments.get(dependency.id)
            if basis is None or basis.facet_digest() != dependency.facet_digest:
                return AdmissionRefused(uid, f"dependency-ineligible: frozen facet mismatch {dependency.id}")
    return Admitted(uid)


def vocabulary_availability(
    declaration: DatasetDeclaration,
    observations: tuple[ByteObservation, ...],
    *,
    members: tuple[str, ...],
) -> tuple[bool, tuple[str, ...]]:
    """The holding half, derived: a vocabulary bound to a dataset whose bytes
    are not held here is `not-available` — never `not-present`, which is the
    world index's finding, and never a membership finding. The members are
    supplied by the fixture because reading held bytes is IO this module does
    not perform."""
    state = admission_state(declaration, observations)
    if isinstance(state, Held):
        return True, members
    return False, ()
