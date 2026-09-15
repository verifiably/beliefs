"""Run, assessment and source-assertion values for the belief seam.

Runs here are **values with role-typed inputs, not the execution boundary** —
begin/capture/replay is not built, `spec` is an opaque supplied identity, and
every R row stays at the run boundary (cut 2 §3). The roles are kernel §4.1's:
`observes` is what confers eligibility, `reads` never does in any quantity (G6),
`transforms` is dataset-production lineage input.

The assessment facet is kernel §4.2.1's table. `estimand` and `applicability`
are typed against the spec they derive from (estimand-typing design §6, §9):
`estimate` and `uncertainty` are checked against the estimand's scale at
**every** construction, never coerced. Its identity is `(spec, run,
proposition)`; its keyed facet digest is what the closure pairs with that
identity (kernel §5.1's first member).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import final

from beliefs.claim import Qualifier
from beliefs.dataset import DatasetDeclaration
from beliefs.errors import MalformedRecord, SignatureRefused, UncertaintyRefused
from beliefs.estimand import (
    Estimand,
    Interval,
    StandardError,
    applicability_projection,
    check_estimate,
    check_uncertainty,
    estimand_projection,
    uncertainty_projection,
)
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
    estimand: Estimand
    applicability: Mapping[str, Qualifier]
    estimate: Decimal | None = None
    uncertainty: Interval | StandardError | None = None

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise MalformedRecord(f"outcome {self.outcome!r} is outside the closed set {OUTCOMES}")
        if type(self.estimand) is not Estimand:
            raise MalformedRecord(f"estimand is a typed Estimand, found {type(self.estimand).__name__}")
        if not isinstance(self.applicability, Mapping) or not all(isinstance(q, Qualifier) for q in self.applicability.values()):
            raise MalformedRecord("applicability is a mapping of dimension → Qualifier")
        if self.estimate is not None and type(self.estimate) is not Decimal:
            raise MalformedRecord(f"estimate is a Decimal or absent, found {type(self.estimate).__name__}")
        if self.uncertainty is not None and not isinstance(self.uncertainty, (Interval, StandardError)):
            raise MalformedRecord(f"uncertainty is an Interval, a StandardError or absent, found {type(self.uncertainty).__name__}")
        # The numerical invariants (estimand-typing §6) hold at **every**
        # construction — the constructor's, the stored reader's, a test's — so a
        # stored record cannot carry a negative standard error or an interval
        # that excludes its estimate any more than a derived one can.
        try:
            if self.estimate is not None:
                check_estimate(self.estimate, self.estimand.measure.scale)
            if self.uncertainty is not None:
                if self.estimate is None:
                    raise UncertaintyRefused("an uncertainty with no estimate to be uncertain about")
                check_uncertainty(self.uncertainty, self.estimate, self.estimand.measure.scale)
        except UncertaintyRefused as refused:
            raise MalformedRecord(str(refused)) from refused
        object.__setattr__(self, "applicability", MappingProxyType(dict(self.applicability)))

    def identity(self) -> str:
        """`(spec, run, proposition)` — which is what puts run identity in the
        belief digest at all (kernel §5.1)."""
        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "run": self.run, "proposition": self.proposition})

    def typed_projection(self) -> dict[str, object]:
        """The typed members, as one canonical mapping: what the stored record
        carries as text and what the facet digest covers. Absent optionals are
        omitted, never null."""
        typed: dict[str, object] = {
            "estimand": estimand_projection(self.estimand),
            "applicability": applicability_projection(self.applicability),
        }
        if self.estimate is not None:
            typed["estimate"] = self.estimate
        if self.uncertainty is not None:
            typed["uncertainty"] = uncertainty_projection(self.uncertainty)
        return typed

    def facet_digest(self) -> str:
        return v1.digest(
            ASSESSMENT_FACET_DOMAIN,
            {"proposition": self.proposition, "outcome": self.outcome, "interpretation_rule": self.interpretation_rule, **self.typed_projection()},
        )


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
