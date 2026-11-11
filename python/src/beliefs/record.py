"""Run, assessment and source-assertion values for the belief seam.

Assessment values own a frozen target and named numerical payload. Their
execution identity, target key and complete facet digest serve different
purposes; each is computed from its declared canonical members.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import final

from beliefs.assessment_payload import CurvePoint, Uncertainty, check_payload, payload_projection
from beliefs.dataset import DatasetDeclaration
from beliefs.dependencies import ASSESSMENT_FACET_DOMAIN, assessment_facet_digest
from beliefs.errors import MalformedRecord, SignatureRefused
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.target import AssessedTarget, target_projection

__all__ = [
    "ASSESSMENT_DOMAIN",
    "ASSESSMENT_FACET_DOMAIN",
    "OUTCOMES",
    "ROLES",
    "SOURCE_ASSERTION_RELATIONS",
    "AssessmentValue",
    "RunInput",
    "RunValue",
    "SourceAssertion",
]

ROLES = ("observes", "reads", "transforms")
OUTCOMES = ("supported", "refuted", "inconclusive")
SOURCE_ASSERTION_RELATIONS = ("asserts", "denies", "hypothesizes")

ASSESSMENT_DOMAIN = "science.assessment.v2"


@sealed
@final
@dataclass(frozen=True)
class RunInput:
    role: str
    dataset: DatasetDeclaration

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise MalformedRecord(f"input role {self.role!r} is outside the closed set {ROLES}")
        if not isinstance(self.dataset, DatasetDeclaration):
            raise MalformedRecord("a run input names a DatasetDeclaration")


@sealed
@final
@dataclass(frozen=True)
class RunValue:
    ref: str
    spec: str
    inputs: tuple[RunInput, ...]

    def __post_init__(self) -> None:
        if not all(isinstance(i, RunInput) for i in self.inputs):
            raise MalformedRecord("a run's inputs are RunInput values only")


@sealed
@final
@dataclass(frozen=True)
class AssessmentValue:
    spec: str
    run: str
    proposition: str
    outcome: str
    interpretation_rule: str
    target: AssessedTarget
    estimates: Mapping[str, Decimal] = field(default_factory=dict)
    uncertainty: Uncertainty = None
    curves: Mapping[str, tuple[CurvePoint, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise MalformedRecord(f"outcome {self.outcome!r} is outside the closed set {OUTCOMES}")
        if not isinstance(self.target, AssessedTarget):
            raise MalformedRecord("assessment requires an AssessedTarget")
        check_payload(self.target.estimand, self.estimates, self.uncertainty, self.curves)
        object.__setattr__(self, "estimates", MappingProxyType(dict(self.estimates)))
        object.__setattr__(self, "curves", MappingProxyType(dict(self.curves)))
        if isinstance(self.uncertainty, Mapping):
            object.__setattr__(self, "uncertainty", MappingProxyType(dict(self.uncertainty)))

    @property
    def estimand(self):
        return self.target.estimand

    @property
    def applicability(self):
        return self.target.applicability

    @property
    def standing(self):
        return self.target.standing

    @property
    def dependencies(self):
        return self.target.dependencies

    @property
    def model(self):
        return self.target.model

    def identity(self) -> str:
        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "run": self.run, "proposition": self.proposition})

    def typed_projection(self) -> dict[str, object]:
        return {**target_projection(self.target), **payload_projection(self.estimates, self.uncertainty, self.curves)}

    def facet_digest(self) -> str:
        return assessment_facet_digest(
            proposition=self.proposition,
            outcome=self.outcome,
            interpretation_rule=self.interpretation_rule,
            standing=self.standing,
            typed=self.typed_projection(),
        )

    def key(self) -> str:
        return v1.digest(
            "science.assessed-proposition.v1",
            {
                "claim": self.estimand.claim,
                "target": target_projection(self.target),
                "interpretation_rule": self.interpretation_rule,
                "standing": self.standing,
            },
        )


@sealed
@final
@dataclass(frozen=True)
class SourceAssertion:
    """A source-assertion can assert, deny or hypothesize — never assess.

    The relation signatures are closed, and this constructor is where
    the closure is enforced here: there is no other authoring
    surface to refuse at. Inertness is the default; `assesses` is declared for
    assessments exactly once."""

    ref: str
    relation: str
    proposition: str
    payload: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.relation not in SOURCE_ASSERTION_RELATIONS:
            raise SignatureRefused(
                f"a source-assertion cannot carry {self.relation!r}; its closed signatures are "
                f"{SOURCE_ASSERTION_RELATIONS} — an `assesses` edge is the assessment's, by type"
            )
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
