"""`PRACTICE.yaml` — procedure without vocabulary (design §3.6)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from beliefs.errors import MalformedContract

__all__ = ["Practice", "load_practice", "parse_practice"]

_FIELDS = frozenset({"practice", "version", "description", "guidance"})
_REFUSED = ("vocabulary", "sorts", "dimensions", "operators", "facets", "kinds", "relations")


@dataclass(frozen=True)
class Practice:
    name: str
    version: int
    description: str
    guidance: tuple[str, ...]


def parse_practice(document: object, *, source: str) -> Practice:
    if not isinstance(document, dict):
        raise MalformedContract(f"{source}: a practice is a mapping")
    for key in document:
        if not isinstance(key, str):
            raise MalformedContract(f"{source}: key {key!r} is {type(key).__name__}, not a string")
    for section in _REFUSED:
        if section in document:
            raise MalformedContract(
                f"{source}: {section} is not a practice field; a practice carries procedure only (D §3.5)"
            )
    unknown = sorted(set(document) - _FIELDS)
    if unknown:
        raise MalformedContract(f"{source}: unknown field(s) {', '.join(unknown)}")
    missing = sorted(_FIELDS - set(document))
    if missing:
        raise MalformedContract(f"{source}: missing field(s) {', '.join(missing)}")
    name, version, description, guidance = (document[key] for key in ("practice", "version", "description", "guidance"))
    if not isinstance(name, str) or not name:
        raise MalformedContract(f"{source}: practice is a non-empty string")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MalformedContract(f"{source}: version is a positive integer")
    if not isinstance(description, str):
        raise MalformedContract(f"{source}: description is a string")
    if not isinstance(guidance, list) or not all(isinstance(entry, str) and entry for entry in guidance):
        raise MalformedContract(f"{source}: guidance is a list of paths")
    return Practice(name, version, description, tuple(guidance))


def load_practice(path: Path) -> Practice:
    from beliefs.contract.document import load_document

    return parse_practice(load_document(path, source=str(path)), source=str(path))
