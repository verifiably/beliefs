"""Run, assessment and source-assertion values for the belief seam.

Runs here are **values with role-typed inputs, not the execution boundary** —
begin/capture/replay is not built, `spec` is an opaque supplied identity, and
every R row stays at the run boundary (cut 2 §3). The roles are kernel §4.1's:
`observes` is what confers eligibility, `reads` never does in any quantity (G6),
`transforms` is dataset-production lineage input.

The assessment facet is kernel §4.2.1's table, with `estimand` and
`applicability` deliberately untyped prose (belief-policy §3.2 — typing them is
ρO3's open neighbourhood, not this module's to claim). Its identity is
`(spec, run, proposition)`; its keyed facet digest is what the closure pairs
with that identity (kernel §5.1's first member).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.dataset import DatasetDeclaration
from beliefs.errors import MalformedRecord, SignatureRefused
from beliefs.identity import v1
from beliefs.sealed import sealed

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

ASSESSMENT_DOMAIN = "science.assessment.v1"
ASSESSMENT_FACET_DOMAIN = "science.assessment-facet.v1"


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
    """The run's bare closure address — its world identity — on the derived and the stored side alike (verification-publication design §3)."""

    proposition: str
    """A cut-1 claim identity: propositions are typed claims, consumed here."""

    outcome: str
    interpretation_rule: str
    estimate: str | None = None
    uncertainty: str | None = None
    estimand: str | None = None
    applicability: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise MalformedRecord(f"outcome {self.outcome!r} is outside the closed set {OUTCOMES}")

    def identity(self) -> str:
        """`(spec, run, proposition)` — which is what puts run identity in the
        belief digest at all (kernel §5.1)."""
        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "run": self.run, "proposition": self.proposition})

    def facet_digest(self) -> str:
        facet: dict[str, object] = {
            "proposition": self.proposition,
            "outcome": self.outcome,
            "interpretation_rule": self.interpretation_rule,
        }
        # Absent optionals are omitted, never null: the encoder refuses null so
        # that {"estimate": absent} and {"estimate": present-and-empty} differ.
        for name in ("estimate", "uncertainty", "estimand", "applicability"):
            value = getattr(self, name)
            if value is not None:
                facet[name] = value
        return v1.digest(ASSESSMENT_FACET_DOMAIN, facet)


@sealed
@final
@dataclass(frozen=True)
class SourceAssertion:
    """A source-assertion can assert, deny or hypothesize — never assess.

    Kernel §4.1 closes the relation signatures, and this constructor is where
    the closure is enforced in this slice (G1): there is no other authoring
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
                f"{SOURCE_ASSERTION_RELATIONS} — an `assesses` edge is the assessment's, by type (G1)"
            )
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
