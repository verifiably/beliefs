"""Datasets: the declaration, the basis projection, and the derived state.

The admission ramp, executable. Three states decided in
order — basis first, then holding — and the state is **derived, never stored**:
nothing here has a state field, `admission_state` recomputes from a declaration
and the byte observations *supplied to the call*, and no API accepts an authored
`held`.

Where a verified observation is *recorded* is not decided here; an argument's
type is not a storage design. That is why `ByteObservation` is two fields and no
timestamp: how long probe evidence stays valid is open, a supplied
observation's currency is the caller's assertion, and a field would invite
reading it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import final

from beliefs.errors import MalformedRecord
from beliefs.sealed import sealed

__all__ = [
    "ACCEPTED_ALGORITHMS",
    "ByteObservation",
    "CurationNote",
    "DatasetDeclaration",
    "Declared",
    "Held",
    "ResourceDeclaration",
    "ResourceFinding",
    "admission_state",
    "dataset_address",
]

# Which digest algorithms pin bytes is owed to the profile and not
# yet ruled; every digest in the measured corpus is sha256. The projection's
# algorithm prefix is what makes the set expressible when it is ruled.
ACCEPTED_ALGORITHMS: frozenset[str] = frozenset({"sha256"})

_DIGEST = re.compile(r"^(?P<algorithm>[a-z0-9-]+):(?P<hex>[0-9a-f]+)$")


def _require_digest(value: str, where: str) -> None:
    if not _DIGEST.fullmatch(value):
        raise MalformedRecord(f"{where}: {value!r} is not `<algorithm>:<lowercase hex>`")


@sealed
@final
@dataclass(frozen=True)
class ResourceDeclaration:
    """One declared resource. `digest is None` means the record declares no
    digest for it — an unpinned resource, which leaves the whole dataset
    without a content identity (all-or-nothing)."""

    name: str
    digest: str | None

    def __post_init__(self) -> None:
        if self.digest is not None:
            _require_digest(self.digest, "a resource's declared digest")


@sealed
@final
@dataclass(frozen=True)
class DatasetDeclaration:
    resources: tuple[ResourceDeclaration, ...]

    def __post_init__(self) -> None:
        if not all(isinstance(r, ResourceDeclaration) for r in self.resources):
            raise MalformedRecord("a declaration holds ResourceDeclaration values only")


@sealed
@final
@dataclass(frozen=True)
class ByteObservation:
    """A byte observation supplied as an argument: bytes were produced and
    hashed, and this is their digest. Location is reporting material and never
    the discriminator."""

    digest: str
    location: str

    def __post_init__(self) -> None:
        _require_digest(self.digest, "an observation's digest")


def _pinned(declaration: DatasetDeclaration) -> tuple[str, ...] | None:
    """The deduplicated, byte-wise-sorted declared digest set, or None when any
    resource is unpinned — missing, or recorded under an unaccepted algorithm —
    or nothing is declared. None is the curation-note case."""
    if not declaration.resources:
        return None
    digests: set[str] = set()
    for resource in declaration.resources:
        if resource.digest is None:
            return None
        algorithm = resource.digest.split(":", 1)[0]
        if algorithm not in ACCEPTED_ALGORITHMS:
            return None
        digests.add(resource.digest)
    return tuple(sorted(digests))


def dataset_address(declaration: DatasetDeclaration) -> str | None:
    """The dataset basis projection: dedupe, sort byte-wise, join
    with newlines and terminate with one, UTF-8, sha256. Names, order,
    repetition and byte counts do not participate. None = no content identity —
    the projection is never applied to an empty set, so sha256 of the empty
    string is never an address."""
    pinned = _pinned(declaration)
    if pinned is None:
        return None
    folded = "".join(digest + "\n" for digest in pinned).encode("utf-8")
    return f"dataset:sha256:{sha256(folded).hexdigest()}"


@sealed
@final
@dataclass(frozen=True)
class ResourceFinding:
    declared: str
    outcome: str
    """`matched` | `mismatch` | `no-matching-observation-in-coverage`.

    The third is never spelled `unheld`: a run over one coverage cannot
    conclude absence, only that it saw no matching bytes."""

    observed: tuple[str, ...] = ()


@sealed
@final
@dataclass(frozen=True)
class CurationNote:
    """No content identity: not a dataset entity, not addressable. The ramp's repair is explicit in
    both directions — pin the last resource, or narrow the declaration to what is pinned."""

    reason: str


@sealed
@final
@dataclass(frozen=True)
class Declared:
    """A world entity, addressable and authorable — and never belief-eligible
    (admission refuses it)."""

    findings: tuple[ResourceFinding, ...]


@sealed
@final
@dataclass(frozen=True)
class Held:
    """Every declared digest has a matching byte observation. Belief-eligible,
    subject to the rest of the admission rules."""

    digests: tuple[str, ...]


def admission_state(
    declaration: DatasetDeclaration, observations: tuple[ByteObservation, ...]
) -> CurationNote | Declared | Held:
    """Derive the ramp's state, per query, from the declaration and the
    observations supplied to this call. Held is quantified over the **whole**
    declaration — a proper subset does not promote — and an observation matches
    by digest alone: location is carried for reporting and never read here."""
    pinned = _pinned(declaration)
    if pinned is None:
        return CurationNote(reason="no content identity: a declared resource is unpinned or nothing is declared")
    observed = {o.digest for o in observations}
    if set(pinned) <= observed:
        return Held(digests=pinned)
    findings = [
        ResourceFinding(
            declared=digest,
            outcome="matched" if digest in observed else "no-matching-observation-in-coverage",
        )
        for digest in pinned
    ]
    stray = tuple(sorted(observed - set(pinned)))
    if stray:
        # Reported as a mismatch, never as a failure to retrieve: bytes were
        # produced and hashed, and the digest differs from every recorded one.
        findings.append(ResourceFinding(declared="", outcome="mismatch", observed=stray))
    return Declared(findings=tuple(findings))
