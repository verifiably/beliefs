"""Map the standalone PHF19 files into the shared domain history reader."""

import re
from itertools import pairwise
from pathlib import Path

from beliefs.contract.base import BaseContract
from beliefs.contract.shipped import ShippedDomainRevision, load_domain_history
from beliefs.errors import ProfileError

__all__ = ["load_phf19_history", "phf19_member_path"]

_HEAD_MEMBERS = {"DOMAIN.yaml": "mm30-phf19.yaml", "REGISTER.json": "mm30-phf19-register.json"}
_HISTORY = "mm30-phf19-history"


def phf19_member_path(logical: str) -> Path:
    """Translate a checked logical history path relative to the PHF19 head's directory."""
    if logical in _HEAD_MEMBERS:
        return Path(_HEAD_MEMBERS[logical])
    if logical == "history":
        return Path(_HISTORY)
    match = re.fullmatch(r"history/([0-9a-f]{64})/(DOMAIN\.yaml|REGISTER\.json)", logical)
    if match is None:
        raise ValueError(f"unknown PHF19 history member {logical!r}")
    return Path(_HISTORY, *match.groups())


def load_phf19_history(
    path: Path, *, base: BaseContract, root: Path | None = None
) -> tuple[ShippedDomainRevision, ...]:
    """Read a fresh PHF19 history from the supplied directory."""
    if path.name != _HEAD_MEMBERS["DOMAIN.yaml"]:
        raise ProfileError(f"{path}: unsupported reproduction contract; use mm30-phf19.yaml")

    def member(logical: str) -> Path:
        return path.parent / phf19_member_path(logical)

    def read_text(logical: str) -> str:
        selected = member(logical)
        if not selected.is_file():
            raise OSError("required regular file is missing or invalid")
        return selected.read_text(encoding="utf-8")

    def label(logical: str) -> str:
        selected = member(logical)
        return (selected if root is None else selected.relative_to(root)).as_posix()

    history = load_domain_history("mm30", base=base, read_text=read_text, source_label=label)
    for predecessor, successor in pairwise(history):
        if successor.contract.version <= predecessor.contract.version:
            logical = f"{successor.directory}/DOMAIN.yaml" if successor.directory else "DOMAIN.yaml"
            raise ProfileError(f"{label(logical)}: version must advance past {predecessor.contract.version}")
    return history
