"""The admission gate: where a constructed assessment meets eligibility.

Kernel §4.1's predicate over values: an `assesses` edge is admissible only if
its run has at least one `observes` input, **all** inputs are held under the
observations supplied to this call, and the assessment is in the admitted
verification state (§3.3). `reads` inputs never confer eligibility, in any
quantity (G6). A refusal is an **outcome**, not an error — the reasons stay
distinct so no gate can silently cover for another.

The gate takes declarations and observations and derives heldness itself; it
accepts no state value, because no API accepts an authored `held` (G9).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from beliefs.dataset import ByteObservation, DatasetDeclaration, Held, admission_state, dataset_address
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
) -> Admitted | AdmissionRefused:
    """The gate, in a fixed order the evaluator's absence-reasons rely on:
    run-mismatch, then observes-presence (G6), then heldness of every input
    (G2b), then verification state (G2c)."""
    uid = assessment.identity()
    if run.ref != typed_ref("run", assessment.run):
        # Both sides in the typed spelling: `assessment.run` is the bare closure
        # address and `run.ref` the typed reference, so printing them as stored
        # reads "names 'run-1', given 'run-1'" of two values that really do differ.
        return AdmissionRefused(
            uid, f"run-mismatch: assessment names {typed_ref('run', assessment.run)!r}, given {run.ref!r}"
        )
    if not any(i.role == "observes" for i in run.inputs):
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
        return AdmissionRefused(uid, "not-admitted-verification-state: kernel 3.3 admits only clean-environment passes")
    return Admitted(uid)


def vocabulary_availability(
    declaration: DatasetDeclaration,
    observations: tuple[ByteObservation, ...],
    *,
    members: tuple[str, ...],
) -> tuple[bool, tuple[str, ...]]:
    """D3's holding half, derived: a vocabulary bound to a dataset whose bytes
    are not held here is `not-available` — never `not-present`, which is the
    world index's finding, and never a membership finding. The members are
    supplied by the fixture because reading held bytes is IO this slice does
    not perform."""
    state = admission_state(declaration, observations)
    if isinstance(state, Held):
        return True, members
    return False, ()
