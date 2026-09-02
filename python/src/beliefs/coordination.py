from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, final

from beliefs.sealed import sealed

__all__ = ["COORDINATION_KINDS", "VIEW_KINDS", "CoordinationAddress", "CoordinationRefused"]

VIEW_KINDS = ("project", "question", "hypothesis", "topic", "theme")
COORDINATION_KINDS = (*VIEW_KINDS, "task", "decision", "note")
_ADDRESS = re.compile(r"coord:([0-9a-f]{32})(?:/([0-9a-f]{32}))?(?:@([0-9a-f]{32}))?")
_HEX = re.compile(r"[0-9a-f]{32}")


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
