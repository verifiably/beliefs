"""Verification as a value, and the derived lifecycle (kernel §3.3).

Consumed, never produced: no replay happens here, and the node is an argument.
The assessment has no verification field — its state is derived from the
verifications pointing at it, by the fail-closed table below, every time it is
asked. Only `(clean-environment, passed)` admits; the final row is a complement
so the table is total by construction.

"Active" here means **not superseded by a later verification that explicitly
references it**. The amended definition (correction-lifecycle §7a) also excludes
targets of a standing retraction; that clause needs retraction records and is
deferred with the C group — cut 2 §4.2 records the split, and this docstring is
the claim's stated bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from beliefs.errors import MalformedRecord
from beliefs.sealed import sealed

__all__ = [
    "ADMITTED",
    "INVALIDATED",
    "NOT_ADMITTED",
    "SCOPES",
    "VERDICTS",
    "Verification",
    "active",
    "lifecycle_state",
]

SCOPES = ("same-environment", "clean-environment", "independent-implementation", "not-certified")
VERDICTS = ("passed", "failed", "inconclusive")

ADMITTED = "admitted"
INVALIDATED = "invalidated"
NOT_ADMITTED = "not-admitted"


@sealed
@final
@dataclass(frozen=True)
class Verification:
    ref: str
    assessment: str
    """`verifies → assessment`: the assessment identity this node points at."""

    scope: str
    verdict: str
    supersedes: str | None = None
    """The ref of the verification this one explicitly resolves, or None."""

    def __post_init__(self) -> None:
        if self.scope not in SCOPES:
            raise MalformedRecord(f"scope {self.scope!r} is outside the closed set {SCOPES}")
        if self.verdict not in VERDICTS:
            raise MalformedRecord(f"verdict {self.verdict!r} is outside the closed set {VERDICTS}")


def active(verifications: tuple[Verification, ...]) -> tuple[Verification, ...]:
    """Not superseded (supersession only in this slice — see module docstring)."""
    superseded = {v.supersedes for v in verifications if v.supersedes is not None}
    return tuple(v for v in verifications if v.ref not in superseded)


def lifecycle_state(verifications: tuple[Verification, ...]) -> str:
    """Kernel §3.3's table, over the verifications for one assessment.

    A pure function of its argument: a cross-call memory here would make a
    deleted failure keep invalidating, contradicting the deletion negative G8
    pins (§3.2's undetectable-history limit)."""
    if not verifications:
        return NOT_ADMITTED
    live = active(verifications)
    if any(v.verdict == "failed" for v in live):
        return INVALIDATED
    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):
        return ADMITTED
    return NOT_ADMITTED
