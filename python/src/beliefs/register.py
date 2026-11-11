"""The assumptions register: what a domain contract's declarations collapse,
license and leave unestablished, as a content-addressed world record.

A register describes one domain contract by its content identity
(`describes: "<namespace>:<content identity>"`), optionally names the revision it
supersedes (`previous`), and carries entries keyed by the typed address of the
declaration each describes across all 21 `ENTRY_KINDS` families. Ordinary keys
are `<kind>:<namespace>/<name>`; estimand keys qualify their inner target as
`estimand:instantiation:<namespace>/<name>` or `estimand:bridge:<namespace>/<name>`.
The kind is part of the key because the declaration tables are separate
namespaces: a sort and a dimension sharing a local name are two declarations
with two sets of collapses.

Each entry carries three non-empty prose strings (`collapses`, `licenses`,
`not_established`) and an explicit identity-bearing `status` (`"provisional"` or
`"established"`). Its id is `assumptions-register:` followed by the digest of its
facet projection under `REGISTER_DOMAIN`, so a revision or status promotion is a
new record and a cited revision can always be read back. It has no relations: it
names its contract by identity, and a contract is not a record. Prose outside
the entries is the record's `body`, outside identity as for every record.

This module holds the value, its projection and stored readers, and contract
register-coverage key enumeration. Whether a register is current for a profile
is the analysis-spec write door's question, and whether a corpus's registers are
complete and fresh is `corpus_check`'s.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

from nodes.core.node import Node

from beliefs.contract.domain import DECLARATION_FAMILIES, DomainContract
from beliefs.errors import LoneSurrogate, MalformedRecord
from beliefs.identity import v1

__all__ = [
    "ENTRY_KINDS",
    "REGISTER_DOMAIN",
    "REGISTER_FACET",
    "REGISTER_KIND",
    "AssumptionsRegister",
    "RegisterEntry",
    "RegisterStatus",
    "register_entry_keys",
    "register_from_projection",
    "register_from_stored",
    "register_identity",
    "register_projection",
]

RegisterStatus = Literal["provisional", "established"]

REGISTER_DOMAIN = "science.assumptions-register.v2"
REGISTER_KIND = "assumptions-register"
REGISTER_FACET = "assumptions-register"
ENTRY_KINDS: tuple[str, ...] = tuple(kind for kind, _ in DECLARATION_FAMILIES)

_ORDINARY_KINDS = tuple(kind for kind in ENTRY_KINDS if kind != "estimand")
_ENTRY_KEY = re.compile(
    rf"(?:({'|'.join(re.escape(kind) for kind in _ORDINARY_KINDS)}):[a-z][a-z0-9-]*/[a-z][a-z0-9-]*"
    r"|estimand:(?:instantiation|bridge):[a-z][a-z0-9-]*/[a-z][a-z0-9-]*)"
)
_DESCRIBES = re.compile(r"[a-z][a-z0-9-]*:[0-9a-f]{64}")
_REGISTER_ID = re.compile(r"assumptions-register:[0-9a-f]{64}")
_STATUSES = frozenset({"provisional", "established"})
_ENTRY_FIELDS = frozenset({"collapses", "licenses", "not_established", "status"})
_FACET_FIELDS = frozenset({"describes", "entries"})


@dataclass(frozen=True)
class RegisterEntry:
    """One declaration's three required prose fields and identity-bearing status."""

    collapses: str
    licenses: str
    not_established: str
    status: RegisterStatus = field(kw_only=True)

    def __post_init__(self) -> None:
        for name in ("collapses", "licenses", "not_established"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise MalformedRecord(f"a register entry's {name} is a non-empty string, found {value!r}")
        if type(self.status) is not str or self.status not in _STATUSES:
            raise MalformedRecord(f"a register entry's status is 'provisional' or 'established', found {self.status!r}")

    def projection(self) -> dict[str, str]:
        return {
            "collapses": self.collapses,
            "licenses": self.licenses,
            "not_established": self.not_established,
            "status": self.status,
        }


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
                    f"entry key {key!r} is not a typed declaration address (`<kind>:<namespace>/<name>`, or "
                    f"`estimand:instantiation:<namespace>/<name>` / `estimand:bridge:<namespace>/<name>`), "
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


def _entry(key: object, value: object, where: str) -> RegisterEntry:
    if not isinstance(value, dict) or set(value) != _ENTRY_FIELDS:
        raise MalformedRecord(f"{where}: entry {key!r} is exactly {{collapses, licenses, not_established, status}}")
    fields: dict[str, Any] = value
    return RegisterEntry(
        fields["collapses"],
        fields["licenses"],
        fields["not_established"],
        status=fields["status"],
    )


def register_from_projection(value: object, *, source: str) -> AssumptionsRegister:
    """Decode a canonical register projection from a stored facet or packaged resource."""
    if not isinstance(value, dict):
        raise MalformedRecord(f"{source}: a register projection is a mapping")
    if not _FACET_FIELDS <= set(value) <= _FACET_FIELDS | {"previous"}:
        raise MalformedRecord(f"{source}: a register facet is describes, entries and an optional previous")
    if "previous" in value and value["previous"] is None:
        raise MalformedRecord(f"{source}: previous is absent on a first revision, never null")
    entries = value["entries"]
    if not isinstance(entries, dict):
        raise MalformedRecord(f"{source}: entries is a mapping")
    try:
        register = AssumptionsRegister(
            describes=value["describes"],
            previous=value.get("previous"),
            entries={key: _entry(key, entry_value, source) for key, entry_value in entries.items()},
        )
        if register_projection(register) != value:
            raise MalformedRecord("the facet is not the canonical projection of the register it decodes to")
        register_identity(register)
    except MalformedRecord as refused:
        if str(refused).startswith(f"{source}: "):
            raise
        raise MalformedRecord(f"{source}: {refused}") from refused
    return register


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
    register = register_from_projection(facet, source=where)
    identity = register_identity(register)
    if node.id != identity:
        raise MalformedRecord(f"{where}: the id does not recompute from the facet; its address is {identity}")
    return register


def _qualify(namespace: str, ref: str) -> str:
    return ref if "/" in ref else f"{namespace}/{ref}"


def register_entry_keys(contract: DomainContract) -> frozenset[str]:
    """Every typed register-coverage key owed by `contract` across `DECLARATION_FAMILIES`.

    Distinct from succession keys: estimands qualify their inner target
    (`estimand:instantiation:<namespace>/<name>` or `estimand:bridge:<namespace>/<name>`),
    measurements address each declared sort without double-prefixing external
    sort references, and aspects expand each declared aspect sort while empty
    aspect lists contribute no address.
    """
    if type(contract) is not DomainContract:
        raise MalformedRecord("register_entry_keys requires a DomainContract")
    namespace = contract.namespace
    keys: set[str] = set()
    for kind, attr in DECLARATION_FAMILIES:
        if kind == "estimand":
            for target in contract.estimands:
                target_kind, _, local_name = target.partition(":")
                keys.add(f"estimand:{target_kind}:{namespace}/{local_name}")
        elif kind == "measurement":
            for measurement_decl in contract.measurements.values():
                keys.add(f"measurement:{_qualify(namespace, measurement_decl.sort)}")
        elif kind == "aspect":
            for aspect_decl in contract.aspects.values():
                for aspect_sort in aspect_decl.aspect_sorts:
                    keys.add(f"aspect:{_qualify(namespace, aspect_sort)}")
        else:
            for name in getattr(contract, attr):
                keys.add(f"{kind}:{namespace}/{name}")
    return frozenset(keys)
