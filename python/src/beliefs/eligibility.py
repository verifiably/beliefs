"""Snapshot eligibility of measurement records and their transitive dependencies."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.dependencies import (
    FrozenAssessmentDependency,
    HeldRecords,
    Record,
    dependency_closure,
    read_record,
    record_references,
)
from beliefs.errors import DependencyCycle, DependencyNotHeld
from beliefs.procedure import Procedure
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import Calibration, ProxyModel

if TYPE_CHECKING:
    from beliefs.record import RunValue
    from beliefs.verification import Verification

__all__ = [
    "AssessmentEligibility",
    "AssessmentEligibilityReader",
    "ClosureEligibility",
    "Eligible",
    "Ineligible",
    "closure_eligibility",
    "dependency_eligibility",
]


@dataclass(frozen=True)
class Eligible:
    pass


@dataclass(frozen=True)
class Ineligible:
    reason: str
    concerns: tuple[str, ...] = ()


AssessmentEligibility: TypeAlias = Callable[[str], Eligible | Ineligible]


@dataclass(frozen=True)
class ClosureEligibility:
    verdicts: Mapping[str, Eligible | Ineligible]
    reads: tuple[str, ...]


def _not_supplied(id: str) -> Ineligible:
    return Ineligible("basis-ineligible: assessment eligibility not supplied")


def dependency_eligibility(
    ids: Iterable[str],
    records: HeldRecords,
    profile: ProfileSpec,
    *,
    assessments: AssessmentEligibility = _not_supplied,
) -> Mapping[str, Eligible | Ineligible]:
    """Judge local conditions; only actual reference-cycle members inherit cycle."""
    requested = tuple(sorted(set(ids)))
    values: dict[str, Record] = {}
    visited: set[str] = set()
    path: list[str] = []
    cycles: set[str] = set()

    def follow(id: str) -> None:
        if id in path:
            cycles.update(path[path.index(id) :])
            return
        if id in visited or not records.holds(id):
            return
        visited.add(id)
        if id.startswith("assessment:"):
            record.address(id, "assessment")
            return
        value = read_record(records, id)
        values[id] = value
        path.append(id)
        for reference in record_references(value, profile):
            follow(reference)
        path.pop()

    for id in requested:
        follow(id)

    def judge(id: str) -> Eligible | Ineligible:
        if not records.holds(id):
            return Ineligible("not-held")
        if records.retraction_in_force(id):
            return Ineligible("retracted")
        if id in cycles:
            return Ineligible("cycle")
        if id.startswith("assessment:"):
            return assessments(id)
        value = values[id]
        if (
            isinstance(value, Procedure)
            and profile.procedure_kinds[value.kind].fills_within_model
            and (
                value.inputs is None
                or not all(records.observation_held(digest) for digest in (*value.inputs.datasets, *value.inputs.code))
            )
        ):
            return Ineligible("model-not-held")
        if isinstance(value, ProxyModel) and isinstance(value.basis, Calibration):
            for assessment in value.basis.assessments:
                verdict = assessments(assessment)
                if isinstance(verdict, Ineligible):
                    return Ineligible(f"basis-ineligible: {assessment}", verdict.concerns)
        return Eligible()

    return MappingProxyType({id: judge(id) for id in requested})


@dataclass
class _ObservedRecords:
    """Keep attempted members even when closure traversal raises before returning."""

    records: HeldRecords
    reads: set[str] = field(default_factory=set)

    def holds(self, id: str) -> bool:
        self.reads.add(id)
        return self.records.holds(id)

    def read(self, id: str) -> Node:
        self.reads.add(id)
        return self.records.read(id)

    def retraction_in_force(self, id: str) -> bool:
        return self.records.retraction_in_force(id)

    def observation_held(self, digest: str) -> bool:
        return self.records.observation_held(digest)

    def crosswalks(self, a: str, b: str) -> tuple[str, ...]:
        return self.records.crosswalks(a, b)


def closure_eligibility(
    ids: Iterable[str],
    records: HeldRecords,
    profile: ProfileSpec,
    *,
    assessments: AssessmentEligibility = _not_supplied,
    assessment_dependency: Callable[[str], FrozenAssessmentDependency] | None = None,
) -> ClosureEligibility:
    """Judge each full closure and return all observed ids, including failed reads."""
    observed = _ObservedRecords(records)
    verdicts: dict[str, Eligible | Ineligible] = {}
    for id in sorted(set(ids)):
        try:
            entries = dependency_closure((id,), observed, profile, assessment_dependency=assessment_dependency)
        except DependencyCycle:
            verdicts[id] = Ineligible("cycle")
            continue
        except DependencyNotHeld:
            verdicts[id] = Ineligible("not-held")
            continue
        members = dependency_eligibility((entry.id for entry in entries), observed, profile, assessments=assessments)
        first = next((member for member in sorted(members) if isinstance(members[member], Ineligible)), None)
        verdicts[id] = Eligible() if first is None else Ineligible(f"dependency-ineligible: {first}")
    return ClosureEligibility(MappingProxyType(verdicts), tuple(sorted(observed.reads)))


@dataclass
class AssessmentEligibilityReader:
    """One recursive snapshot walk shared across claims and keys.

    The boundary supplies captured runs and active verification records; this
    reader never resolves a spec or fetches an observed dataset's bytes.
    """

    records: HeldRecords
    profile: ProfileSpec
    run_of: Callable[[str], "RunValue"]
    verifications_of: Callable[[str], tuple["Verification", ...]]
    _active: set[str] = field(default_factory=set)
    _memo: dict[str, Eligible | Ineligible] = field(default_factory=dict)

    def __call__(self, id: str) -> Eligible | Ineligible:
        from beliefs import stored
        from beliefs.errors import ScienceError
        from beliefs.verification import ADMITTED, lifecycle_state

        if id in self._active:
            return Ineligible("cycle", (id,))
        if id in self._memo:
            return self._memo[id]
        if not self.records.holds(id) or self.records.retraction_in_force(id):
            return Ineligible("basis-not-held-or-retracted", (id,))
        self._active.add(id)
        try:
            value = stored.assessment_value(self.records.read(id), profile=self.profile)
            frozen = dependency_closure(
                (d.id for d in value.dependencies),
                self.records,
                self.profile,
                assessment_dependency=lambda ref: stored.frozen_assessment_dependency(
                    ref, records=self.records, profile=self.profile
                ),
            )
            if frozen != value.dependencies:
                return Ineligible("frozen-dependency-mismatch", (id,))
            run = self.run_of(value.run)
            if run.ref != stored.typed_ref("run", value.run):
                verdict = Ineligible("run-mismatch")
            elif value.standing == "empirical" and not any(i.role == "observes" for i in run.inputs):
                verdict = Ineligible("no-observes-input")
            elif any(not i.dataset.resources for i in run.inputs) or not all(
                d is not None and self.records.observation_held(d)
                for i in run.inputs
                for resource in i.dataset.resources
                for d in (resource.digest,)
            ):
                verdict = Ineligible("input-not-held")
            elif lifecycle_state(self.verifications_of(value.identity())) != ADMITTED:
                verdict = Ineligible("not-admitted-verification-state")
            else:
                closure = closure_eligibility(
                    (d.id for d in value.dependencies),
                    self.records,
                    self.profile,
                    assessments=self,
                    assessment_dependency=lambda ref: stored.frozen_assessment_dependency(
                        ref, records=self.records, profile=self.profile
                    ),
                )
                first = next((ref for ref, v in closure.verdicts.items() if isinstance(v, Ineligible)), None)
                verdict = Eligible() if first is None else Ineligible("dependency-ineligible", (first,))
            self._memo[id] = verdict
            return verdict
        except ScienceError as error:
            return Ineligible(str(error), (id,))
        finally:
            self._active.difference_update((id,))
