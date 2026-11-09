"""The assumptions register: what a domain contract's declarations collapse,
license and leave unestablished, as a content-addressed world record.

A register describes one domain contract by its content identity
(`describes: "<namespace>:<content identity>"`), optionally names the revision it
supersedes (`previous`), and carries entries keyed by the typed address of the
declaration each describes, `<kind>:<namespace>/<name>` with the kind one of
`ENTRY_KINDS`. The kind is part of the key because the declaration tables are
separate namespaces: a sort and a dimension sharing a local name are two
declarations with two sets of collapses.

Its id is `assumptions-register:` followed by the digest of its facet projection
under `REGISTER_DOMAIN`, so a revision is a new record and a cited revision can
always be read back. It has no relations: it names its contract by identity, and
a contract is not a record. Prose outside the entries is the record's `body`,
outside identity as for every record.

This module holds the value and its stored reader only. Whether a register is
current for a profile is the analysis-spec write door's question, and whether a
corpus's registers are complete and fresh is `corpus_check`'s.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from nodes.core.node import Node

from beliefs.errors import LoneSurrogate, MalformedRecord
from beliefs.identity import v1

__all__ = [
    "ENTRY_KINDS",
    "REGISTER_DOMAIN",
    "REGISTER_FACET",
    "REGISTER_KIND",
    "AssumptionsRegister",
    "RegisterEntry",
    "register_from_stored",
    "register_identity",
    "register_projection",
]

REGISTER_DOMAIN = "science.assumptions-register.v1"
REGISTER_KIND = "assumptions-register"
REGISTER_FACET = "assumptions-register"
ENTRY_KINDS = ("sort", "template", "instantiation", "bridge", "dimension")

_ENTRY_KEY = re.compile(r"(sort|template|instantiation|bridge|dimension):[a-z][a-z0-9-]*/[a-z][a-z0-9-]*")
_DESCRIBES = re.compile(r"[a-z][a-z0-9-]*:[0-9a-f]{64}")
_REGISTER_ID = re.compile(r"assumptions-register:[0-9a-f]{64}")
_ENTRY_FIELDS = frozenset({"collapses", "licenses", "not_established"})
_FACET_FIELDS = frozenset({"describes", "entries"})


@dataclass(frozen=True)
class RegisterEntry:
    """One declaration's three required prose fields."""

    collapses: str
    licenses: str
    not_established: str

    def __post_init__(self) -> None:
        for name in ("collapses", "licenses", "not_established"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise MalformedRecord(f"a register entry's {name} is a non-empty string, found {value!r}")

    def projection(self) -> dict[str, str]:
        return {"collapses": self.collapses, "licenses": self.licenses, "not_established": self.not_established}


@dataclass(frozen=True)
class AssumptionsRegister:
    """A register revision: the contract it describes, the revision it
    supersedes, and its entries keyed by typed declaration address."""

    describes: str
    previous: str | None
    entries: Mapping[str, RegisterEntry]

    def __post_init__(self) -> None:
        if type(self.describes) is not str or _DESCRIBES.fullmatch(self.describes) is None:
            raise MalformedRecord(
                f"describes is `<namespace>:<content identity>` — a contract namespace and 64 lowercase hex "
                f"characters; found {self.describes!r}"
            )
        if self.previous is not None and (
            type(self.previous) is not str or _REGISTER_ID.fullmatch(self.previous) is None
        ):
            raise MalformedRecord(
                f"previous is `assumptions-register:` followed by 64 lowercase hex characters; found {self.previous!r}"
            )
        if not isinstance(self.entries, Mapping):
            raise MalformedRecord("entries is a mapping from typed declaration addresses to register entries")
        checked: dict[str, RegisterEntry] = {}
        for key in sorted(self.entries, key=_order):
            if type(key) is not str or _ENTRY_KEY.fullmatch(key) is None:
                raise MalformedRecord(
                    f"entry key {key!r} is not a typed declaration address `<kind>:<namespace>/<name>`, "
                    f"with the kind one of {', '.join(ENTRY_KINDS)}"
                )
            entry = self.entries[key]
            if type(entry) is not RegisterEntry:
                raise MalformedRecord(f"entry {key!r} is a RegisterEntry, found {type(entry).__name__}")
            checked[key] = entry
        object.__setattr__(self, "entries", MappingProxyType(checked))


def _order(key: object) -> str:
    return key if isinstance(key, str) else repr(key)


def register_projection(register: AssumptionsRegister) -> dict[str, object]:
    """The facet a register is stored as and digested over. `previous` is
    absent, never null, for a first revision."""
    if type(register) is not AssumptionsRegister:
        raise MalformedRecord("register_projection requires an AssumptionsRegister")
    projection: dict[str, object] = {
        "describes": register.describes,
        "entries": {key: entry.projection() for key, entry in register.entries.items()},
    }
    if register.previous is not None:
        projection["previous"] = register.previous
    return projection


def register_identity(register: AssumptionsRegister) -> str:
    """`assumptions-register:` and the digest of the facet projection."""
    try:
        return f"{REGISTER_KIND}:" + v1.digest(REGISTER_DOMAIN, register_projection(register))
    except LoneSurrogate as refused:
        raise MalformedRecord("a register field is not canonically encodable") from refused


def _entry(key: str, value: object, where: str) -> RegisterEntry:
    if not isinstance(value, dict) or set(value) != _ENTRY_FIELDS:
        raise MalformedRecord(f"{where}: entry {key!r} is exactly {{collapses, licenses, not_established}}")
    fields: dict[str, Any] = value
    return RegisterEntry(fields["collapses"], fields["licenses"], fields["not_established"])


def register_from_stored(node: Node) -> AssumptionsRegister:
    """The facet reader the base contract names for the kind: the register a
    stored record carries, refused unless its facet is the canonical projection
    of that register and its id is the register's identity."""
    where = node.id
    if node.kind != REGISTER_KIND:
        raise MalformedRecord(f"{where}: not an {REGISTER_KIND} record")
    facet = node.facets.get(REGISTER_FACET)
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{where}: an assumptions register carries an {REGISTER_FACET!r} facet")
    if not _FACET_FIELDS <= set(facet) <= _FACET_FIELDS | {"previous"}:
        raise MalformedRecord(f"{where}: a register facet is describes, entries and an optional previous")
    entries = facet["entries"]
    if not isinstance(entries, dict):
        raise MalformedRecord(f"{where}: entries is a mapping")
    try:
        register = AssumptionsRegister(
            describes=facet["describes"],
            previous=facet.get("previous"),
            entries={key: _entry(key, value, where) for key, value in entries.items()},
        )
        if register_projection(register) != facet:
            raise MalformedRecord("the stored facet is not the canonical projection of the register it decodes to")
        identity = register_identity(register)
    except MalformedRecord as refused:
        raise MalformedRecord(f"{where}: {refused}") from refused
    if node.id != identity:
        raise MalformedRecord(f"{where}: the id does not recompute from the facet; its address is {identity}")
    return register
