"""Turn receipt-committed holdings projections into one dataset's evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast, final

from beliefs.dataset import ByteObservation, DatasetDeclaration
from beliefs.sealed import sealed

__all__ = ["DatasetAnswer", "DatasetBlocked", "dataset_observations"]


@sealed
@final
@dataclass(frozen=True)
class DatasetAnswer:
    observations: tuple[ByteObservation, ...]


@sealed
@final
@dataclass(frozen=True)
class DatasetBlocked:
    locations: tuple[str, ...]
    reasons: tuple[str, ...]


def _algorithm(digest: str) -> str:
    return digest.split(":", 1)[0]


def _found(member: Mapping[str, object]) -> str | None:
    outcome = cast(Mapping[str, object], member["outcome"])
    if outcome["finding"] != "found":
        return None
    return cast(str, outcome["digest"])


def _matches(row: Mapping[str, object], declared: str) -> bool:
    found = _found(row)
    return found is not None and _algorithm(found) == _algorithm(declared) and (
        found == declared or row.get("expected") == declared
    )


def _joined(member: Mapping[str, object], declared: frozenset[str]) -> str | None:
    found = _found(member)
    if found is None:
        return None
    history = cast(Sequence[Mapping[str, object]], member["history"])
    for digest in declared:
        if _matches(member, digest) or (
            _algorithm(found) == _algorithm(digest) and any(_matches(row, digest) for row in history)
        ):
            return found
    return None


def dataset_observations(
    declaration: DatasetDeclaration,
    active: Sequence[Mapping[str, object]],
    blocked: Sequence[Mapping[str, object]],
) -> DatasetAnswer | DatasetBlocked:
    declared = frozenset(resource.digest for resource in declaration.resources if resource.digest is not None)
    blocked_locations: set[str] = set()
    blocked_reasons: set[str] = set()
    for entry in blocked:
        heads = cast(Sequence[Mapping[str, object]], entry["heads"])
        if any(_joined(head, declared) is not None for head in heads):
            blocked_locations.add(cast(str, entry["location"]))
            blocked_reasons.update(cast(Sequence[str], entry["reasons"]))
    if blocked_locations:
        return DatasetBlocked(tuple(sorted(blocked_locations)), tuple(sorted(blocked_reasons)))

    observations = {
        (found, cast(str, member["location"]))
        for member in active
        if (found := _joined(member, declared)) is not None
    }
    return DatasetAnswer(tuple(ByteObservation(digest, location) for digest, location in sorted(observations)))
