from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, final

from nodes.core.node import Node

from beliefs import stored
from beliefs.errors import MalformedRecord
from beliefs.sealed import sealed

__all__ = [
    "COORDINATION_KINDS",
    "VIEW_KINDS",
    "CoordinationAddress",
    "CoordinationRefused",
    "CoordinationRevision",
    "coordination_facet_malformed",
    "coordination_revision",
    "standing_tips",
]

VIEW_KINDS = ("project", "question", "hypothesis", "topic", "theme")
COORDINATION_KINDS = (*VIEW_KINDS, "task", "decision", "note")
_ADDRESS = re.compile(r"coord:([0-9a-f]{32})(?:/([0-9a-f]{32}))?(?:@([0-9a-f]{32}))?")
_HEX = re.compile(r"[0-9a-f]{32}")
_RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")


@sealed
@final
@dataclass(frozen=True)
class CoordinationAddress:
    project: str
    local: str | None = None
    revision: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("project", self.project),
            ("local", self.local),
            ("revision", self.revision),
        ):
            if value is not None and _HEX.fullmatch(value) is None:
                raise ValueError(
                    f"coordination address {name} must be 32 lowercase hexadecimal characters"
                )

    @classmethod
    def parse(cls, value: str) -> CoordinationAddress:
        match = _ADDRESS.fullmatch(value) if type(value) is str else None
        if match is None:
            raise ValueError(f"{value!r} is not a canonical coordination address")
        return cls(*match.groups())

    def unpinned(self) -> CoordinationAddress:
        return CoordinationAddress(self.project, self.local)

    def pinned(self, revision: str) -> CoordinationAddress:
        return CoordinationAddress(self.project, self.local, revision)

    def __str__(self) -> str:
        value = f"coord:{self.project}"
        if self.local is not None:
            value += f"/{self.local}"
        return value if self.revision is None else f"{value}@{self.revision}"


CoordinationRefusalReason = Literal["divergent-view", "predecessor-not-standing"]


@sealed
@final
@dataclass(frozen=True)
class CoordinationRefused:
    reason: CoordinationRefusalReason
    tips: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.reason not in ("divergent-view", "predecessor-not-standing"):
            raise ValueError(f"unknown coordination refusal reason {self.reason!r}")
        if any(_HEX.fullmatch(tip) is None for tip in self.tips):
            raise ValueError("coordination refusal tips are 32 lowercase hexadecimal revision ids")
        object.__setattr__(self, "tips", tuple(sorted(set(self.tips))))


@sealed
@final
@dataclass(frozen=True)
class CoordinationRevision:
    node: Node
    address: CoordinationAddress
    predecessors: tuple[str, ...]


def coordination_revision(node: Node) -> CoordinationRevision:
    if set(node.facets) != {stored.COORDINATION_FACET}:
        raise MalformedRecord(f"{node.id}: a coordination revision carries exactly the coordination facet")
    facet = node.facets[stored.COORDINATION_FACET]
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{node.id}: the coordination facet must be a mapping")
    for field in ("project", "author", "at"):
        if field not in facet:
            raise MalformedRecord(f"{node.id}: the coordination facet is missing {field!r}")

    project = facet["project"]
    local = facet.get("local")
    if not isinstance(project, str) or _HEX.fullmatch(project) is None:
        raise MalformedRecord(f"{node.id}: coordination project must be 32 lowercase hexadecimal characters")
    if local is not None and (not isinstance(local, str) or _HEX.fullmatch(local) is None):
        raise MalformedRecord(f"{node.id}: coordination local must be 32 lowercase hexadecimal characters")
    address = CoordinationAddress(project=facet["project"], local=facet.get("local"))
    if _HEX.fullmatch(node.uid) is None:
        raise MalformedRecord(f"{node.id}: revision uid must be 32 lowercase hexadecimal characters")
    expected_id = (
        f"{node.kind}:{address.project}.{node.uid}"
        if address.local is None
        else f"{node.kind}:{address.project}.{address.local}.{node.uid}"
    )
    if node.id != expected_id:
        raise MalformedRecord(f"{node.id}: coordination node id does not match its address and revision")
    if not isinstance(facet["author"], str) or not facet["author"]:
        raise MalformedRecord(f"{node.id}: coordination author must be a non-empty string")
    at = facet["at"]
    if not isinstance(at, str) or _RFC3339.fullmatch(at) is None:
        raise MalformedRecord(f"{node.id}: coordination at must be an RFC3339 timestamp")
    try:
        datetime.fromisoformat(at)
    except ValueError as caught:
        raise MalformedRecord(f"{node.id}: coordination at must be a calendar timestamp") from caught

    prefix = (
        f"{node.kind}:{address.project}."
        if address.local is None
        else f"{node.kind}:{address.project}.{address.local}."
    )
    predecessors: list[str] = []
    for relation in node.relations:
        if (
            relation.predicate != stored.SUPERSEDES
            or relation.source != node.id
            or relation.directed is not True
            or relation.weight is not None
            or relation.attrs
            or not relation.target.startswith(prefix)
            or _HEX.fullmatch(relation.target.removeprefix(prefix)) is None
        ):
            raise MalformedRecord(f"{node.id}: coordination revisions carry only directed supersedes edges")
        predecessors.append(relation.target)
    if len(predecessors) != len(set(predecessors)):
        raise MalformedRecord(f"{node.id}: coordination predecessors must be distinct")
    return CoordinationRevision(node=node, address=address, predecessors=tuple(sorted(predecessors)))


def coordination_facet_malformed(node: Node) -> bool:
    try:
        coordination_revision(node)
    except MalformedRecord:
        return True
    return False


def standing_tips(revisions: Sequence[CoordinationRevision]) -> tuple[CoordinationRevision, ...]:
    by_id = {revision.node.id: revision for revision in revisions}
    superseded = {
        predecessor
        for revision in revisions
        for predecessor in revision.predecessors
        if predecessor in by_id
    }
    return tuple(
        sorted(
            (revision for revision in revisions if revision.node.id not in superseded),
            key=lambda revision: revision.node.uid,
        )
    )
