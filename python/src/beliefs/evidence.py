"""What a derivation recomputation is handed, and what it answers with.

These three values sit in their own module because both sides of the audit
seam will need them: `beliefs.audit` recomputes with them now, and
`beliefs.corpus` names them at the import boundary from the explicit-import
work on. A module that imported `beliefs.corpus` to name `Finding` would close
that loop, so the reference is a type-checking one and nothing here imports the
corpus at run time.

Evidence is **supplied**, never ambient: a recomputation that
reached for a registry of held specs would decide by process state, and two
holders of the same bytes would reach different verdicts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, final

from beliefs.dependencies import Record
from beliefs.eligibility import ClosureEligibility, Eligible, Ineligible
from beliefs.errors import DependencyNotHeld, ScopeDependencyIneligible, ScopeEvidenceIncomplete
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue, RunValue
from beliefs.replay import EquivalenceImplementation
from beliefs.restriction import ScopeComparison
from beliefs.scope_checks import ScopeReader
from beliefs.sealed import sealed
from beliefs.series.evidence import SeriesEvidence
from beliefs.spec import FrozenSpec, RuleImplementation
from beliefs.target_validity import SCOPE_REASONS, scope_eligibility

if TYPE_CHECKING:
    from beliefs.corpus import Finding

__all__ = ["NO_EVIDENCE", "DependencyEvidence", "DerivationEvidence", "DerivationOutcome", "scope_evidence"]


@sealed
@final
@dataclass(frozen=True)
class DerivationEvidence:
    """What the caller holds: frozen specs, equivalence-rule implementations
    keyed by identity, and interpretation-rule implementations keyed by
    identity. Supplied explicitly, never ambient."""

    specs: Mapping[str, FrozenSpec]
    held_rules: Mapping[str, EquivalenceImplementation]
    implementations: Mapping[str, RuleImplementation]
    series_evidence: SeriesEvidence | None = None


NO_EVIDENCE = DerivationEvidence(specs={}, held_rules={}, implementations={})
"""Every mapping empty — an explicit *nothing held*, so a caller that holds no
evidence says so rather than defaulting into one."""


@sealed
@final
@dataclass(frozen=True)
class DerivationOutcome:
    """Checked and agreeing, checked and contradicted, or not checked at all.

    `reason` is why a recomputation could not run, and it is never a verdict:
    an unchecked derivation is neither validated nor contradicted.
    """

    checked: bool
    reason: str
    contradiction: Finding | None


@sealed
@final
@dataclass(frozen=True)
class DependencyEvidence:
    """Only the dependency values and eligibility read from one supplied snapshot."""

    closure: ClosureEligibility
    records: Mapping[str, Record]
    assessments: Mapping[str, AssessmentValue]
    runs: Mapping[str, RunValue]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "closure",
            ClosureEligibility(MappingProxyType(dict(self.closure.verdicts)), tuple(self.closure.reads)),
        )
        for name in ("records", "assessments", "runs"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


def _incomplete(detail: str) -> ScopeEvidenceIncomplete:
    return ScopeEvidenceIncomplete(f"scope-evidence-incomplete: {detail}")


def scope_evidence(
    assessments: tuple[AssessmentValue, ...], dependencies: DependencyEvidence, *, profile: ProfileSpec
) -> tuple[ScopeComparison, ...]:
    """Recompute every required scope check from supplied targets and typed bodies.

    Scope containment design §7.4. The required assessment states and contextual
    reads are derived from the supplied matched targets and the captured nested
    assessments, never from the verdict map. Each state must be present, a success
    included. A computed failure cannot sit beside a final Eligible, and a recorded
    scope-layer reason must equal the recomputed one exactly; for a nested
    assessment a recorded intrinsic failure may win. A missing body is admitted only
    for an explicitly failed read with its attempted read and ineligible state.
    Anything else raises ``ScopeEvidenceIncomplete``. No world is read.
    Returns the recomputed comparisons, for the consulted-contract walk.
    """
    verdicts = dependencies.closure.verdicts
    reads = frozenset(dependencies.closure.reads)

    def read(id: str) -> Record:
        if id not in reads:
            raise _incomplete(f"{id} is read by the scope check but has no attempted read")
        if id in dependencies.records:
            return dependencies.records[id]
        if isinstance(verdicts.get(id), Ineligible):
            raise DependencyNotHeld(f"recorded failed read: {id}")
        raise _incomplete(f"{id} has no supplied body and no recorded failed read")

    def require(roots: tuple[str, ...]) -> None:
        failed: list[str] = []
        for root in roots:
            if root not in reads:
                raise _incomplete(f"selected scope rule {root} has no attempted read")
            verdict = verdicts.get(root)
            if verdict is None:
                raise _incomplete(f"selected scope rule {root} has no state")
            if isinstance(verdict, Ineligible):
                failed.append(root)
        if failed:
            raise ScopeDependencyIneligible(
                f"scope-dependency-ineligible: selected scope rules are ineligible ({', '.join(failed)})", tuple(failed)
            )

    reader = ScopeReader(profile, read, require)
    targets: dict[str, tuple[AssessmentValue, bool]] = {}
    for value in dependencies.assessments.values():
        targets[value.identity()] = (value, False)
    for value in assessments:
        targets[value.identity()] = (value, True)
    for identity, (value, matched) in sorted(targets.items()):
        computed = scope_eligibility(value.target, reader)
        recorded = verdicts.get(identity)
        if recorded is None:
            raise _incomplete(f"assessment {identity} has no recorded scope state")
        if matched:
            consistent = recorded == computed
        elif isinstance(computed, Ineligible):
            consistent = isinstance(recorded, Ineligible) and (
                recorded.reason not in SCOPE_REASONS or recorded == computed
            )
        else:
            consistent = isinstance(recorded, Eligible) or recorded.reason not in SCOPE_REASONS
        if not consistent:
            raise _incomplete(f"assessment {identity} records {recorded!r}, but its scope recomputes to {computed!r}")
    return reader.comparisons
