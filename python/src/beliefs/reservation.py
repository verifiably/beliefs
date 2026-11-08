"""Exposure events and reservation assignments as pure values.

The field rules, the two unit shapes with their sort order, the facet round
trip, the content identity and the derived group changes of the two kinds
declared in the exposure and reservation kinds design (2026-11-08), and the
checks the write boundary raises and the audit reports (one pure function per
stage, over references the caller has already resolved), and the view helpers
that read both kinds back through any view's own `iter_stored` and `get`.
Nothing here writes a record or imports `beliefs.corpus` or `beliefs.audit`:
the readers, the write boundary and the audit build on these types.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Container, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from itertools import pairwise
from typing import TYPE_CHECKING, Protocol, final

from beliefs.errors import ChainAmbiguous, MalformedRecord
from beliefs.identity import v1
from beliefs.permit import require_actor
from beliefs.sealed import sealed

if TYPE_CHECKING:
    from nodes.core.node import Node
    from nodes.core.relations import Relation

__all__ = [
    "CHANNELS",
    "EFFECTS",
    "EXPOSURE_EVENT_DOMAIN",
    "OPEN",
    "RESERVATION_ASSIGNMENT_DOMAIN",
    "ROLES",
    "UNREAD",
    "CheckRefusal",
    "ExposureEvent",
    "Group",
    "GroupChange",
    "IntervalUnit",
    "RecordView",
    "ReservationAssignment",
    "TermUnit",
    "Unit",
    "Unread",
    "assignment_changes",
    "assignment_changes_of",
    "assignment_head",
    "assignment_record_refusal",
    "assignment_succession_refusal",
    "exposure_event_from_facet",
    "exposure_event_refusal",
    "exposure_events",
    "reservation_assignment_from_facet",
    "unit_facet",
    "unit_from_facet",
    "unit_shape",
    "unit_sort_key",
]

EXPOSURE_EVENT_DOMAIN = "science.exposure-event.v1"
RESERVATION_ASSIGNMENT_DOMAIN = "science.reservation-assignment.v1"
ROLES = ("open", "reserved", "unresolved", "withheld")
CHANNELS = ("read", "knowledge")
EFFECTS = ("exposing", "non-exposing")
OPEN = "open"

_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
_SORT = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")
_EVENT_KERNEL_EVIDENCE = ("act-report", "run", "holdings-observation")
_ASSIGNMENT_KERNEL_EVIDENCE = ("exposure-event",)
_PRIOR_RUN_KERNEL_REFS = ("run",)


def _refuse(message: str) -> MalformedRecord:
    return MalformedRecord(message)


def _text(value: object, where: str) -> str:
    if type(value) is not str or not value:
        raise _refuse(f"{where}: {value!r} is not a non-empty string")
    return value


def _timestamp(value: object, where: str) -> str:
    if type(value) is not str or _TIMESTAMP.fullmatch(value) is None:
        raise _refuse(f"{where}: {value!r} is not a whole-second YYYY-MM-DDTHH:MM:SSZ timestamp")
    try:
        datetime.fromisoformat(value)
    except ValueError as caught:
        raise _refuse(f"{where}: {value!r} is not a calendar time: {caught}") from caught
    return value


def _digest(value: object, where: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise _refuse(f"{where}: {value!r} is not `sha256:` and 64 lowercase hex digits")
    return value


def _one_of(value: object, allowed: tuple[str, ...], where: str) -> str:
    if type(value) is not str or value not in allowed:
        raise _refuse(f"{where}: {value!r} is not one of {allowed}")
    return value


def _prefixed(value: object, prefixes: tuple[str, ...], where: str) -> str:
    if type(value) is not str or not any(value.startswith(p) and len(value) > len(p) for p in prefixes):
        raise _refuse(f"{where}: {value!r} does not carry a {' or '.join(prefixes)} reference")
    return value


def _tuple(value: object, where: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise _refuse(f"{where}: {value!r} is not a tuple")
    return value


def _sorted_distinct(values: Sequence[object], where: str, key: object = None) -> None:
    keyed = [key(v) if callable(key) else v for v in values]  # pyright: ignore[reportUnknownVariableType]
    for before, after in pairwise(keyed):  # pyright: ignore[reportUnknownVariableType]
        if not before < after:  # pyright: ignore[reportUnknownVariableType, reportOperatorIssue]
            raise _refuse(f"{where} must be sorted and distinct; {before!r} is followed by {after!r}")


def _strings(
    value: object, where: str, prefixes: tuple[str, ...] | None = None, *, tokens: bool = False, actors: bool = False
) -> tuple[str, ...]:
    entries = _tuple(value, where)
    out: list[str] = []
    for entry in entries:
        if actors:
            try:
                out.append(require_actor(entry))
            except (TypeError, ValueError) as caught:
                raise _refuse(f"{where}: {entry!r} is not an actor: {caught}") from caught
        elif tokens:
            if type(entry) is not str or entry.find(":") < 1 or entry.endswith(":"):
                raise _refuse(f"{where}: {entry!r} is not `<scheme>:<rest>`")
            out.append(entry)
        else:
            assert prefixes is not None
            out.append(_prefixed(entry, prefixes, where))
    _sorted_distinct(out, where)
    return tuple(out)


def _digest_map(value: object, where: str) -> tuple[tuple[str, str], ...]:
    entries = _tuple(value, where)
    names: list[str] = []
    for entry in entries:
        if type(entry) is not tuple or len(entry) != 2:  # pyright: ignore[reportUnknownArgumentType]
            raise _refuse(f"{where}: {entry!r} is not a (name, digest) pair")
        name, digest = entry  # pyright: ignore[reportUnknownVariableType]
        names.append(_text(name, f"{where} name"))
        _digest(digest, f"{where}[{name}]")
    _sorted_distinct(names, f"{where} keys")
    return value  # type: ignore[return-value]


@sealed
@final
@dataclass(frozen=True)
class TermUnit:
    sort: str
    term: str

    def __post_init__(self) -> None:
        if type(self.sort) is not str or _SORT.fullmatch(self.sort) is None:
            raise _refuse(f"a term unit's sort {self.sort!r} is not `<namespace>/<name>`")
        _text(self.term, "a term unit's term")


@sealed
@final
@dataclass(frozen=True)
class IntervalUnit:
    start: str
    end: str

    def __post_init__(self) -> None:
        for where, value in (("start", self.start), ("end", self.end)):
            if value != OPEN:
                _timestamp(value, f"an interval unit's {where}")
        if self.start == OPEN and self.end == OPEN:
            raise _refuse("an interval unit may not be open at both ends")
        if self.start != OPEN and self.end != OPEN and not self.start < self.end:
            raise _refuse(f"an interval unit must start before it ends: {self.start!r} .. {self.end!r}")


Unit = TermUnit | IntervalUnit


def unit_shape(unit: Unit) -> str:
    return "term" if isinstance(unit, TermUnit) else "interval"


def unit_sort_key(unit: Unit) -> tuple[str, str, str]:
    if isinstance(unit, TermUnit):
        return ("term", unit.sort, unit.term)
    return ("interval", "" if unit.start == OPEN else unit.start, "~" if unit.end == OPEN else unit.end)


def unit_facet(unit: Unit) -> dict[str, str]:
    if isinstance(unit, TermUnit):
        return {"sort": unit.sort, "term": unit.term}
    return {"start": unit.start, "end": unit.end}


def unit_from_facet(value: Mapping[str, object]) -> Unit:
    if not isinstance(value, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise _refuse(f"a unit is a mapping, not {value!r}")
    keys = set(value)
    if keys == {"sort", "term"}:
        return TermUnit(value["sort"], value["term"])  # type: ignore[arg-type]
    if keys == {"start", "end"}:
        return IntervalUnit(value["start"], value["end"])  # type: ignore[arg-type]
    raise _refuse(f"a unit carries `sort` and `term` or `start` and `end`, not {sorted(keys)}")


def _units(value: object, where: str) -> tuple[Unit, ...]:
    entries = _tuple(value, where)
    for entry in entries:
        if not isinstance(entry, (TermUnit, IntervalUnit)):
            raise _refuse(f"{where}: {entry!r} is not a unit")
    units: tuple[Unit, ...] = entries  # type: ignore[assignment]
    _sorted_distinct(units, where, unit_sort_key)
    if len({unit_shape(u) for u in units}) > 1:
        raise _refuse(f"{where} mixes term and interval units")
    return units


@sealed
@final
@dataclass(frozen=True)
class Group:
    units: tuple[Unit, ...]
    role: str
    label: str | None
    basis: str | None

    def __post_init__(self) -> None:
        if not _units(self.units, "a group's units"):
            raise _refuse("a group holds at least one unit")
        _one_of(self.role, ROLES, "a group's role")
        if self.label is not None:
            _text(self.label, "a group's label")
        if self.basis is not None:
            _digest(self.basis, "a group's basis")

    @property
    def first(self) -> Unit:
        return self.units[0]

    def facet(self) -> dict[str, object]:
        out: dict[str, object] = {"units": [unit_facet(u) for u in self.units], "role": self.role}
        if self.label is not None:
            out["label"] = self.label
        if self.basis is not None:
            out["basis"] = self.basis
        return out


def _group_from_facet(value: object) -> Group:
    if not isinstance(value, Mapping):
        raise _refuse(f"a group is a mapping, not {value!r}")
    _only(value, {"units", "role"}, {"label", "basis"}, "a group")  # pyright: ignore[reportUnknownArgumentType]
    return Group(
        _unit_tuple(value["units"]),
        value["role"],  # type: ignore[arg-type]
        value.get("label"),  # type: ignore[arg-type]
        value.get("basis"),  # type: ignore[arg-type]
    )


def _only(value: Mapping[str, object], required: set[str], optional: set[str], where: str) -> None:
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise _refuse(f"{where} carries {sorted(required)} and optionally {sorted(optional)}, not {sorted(keys)}")


def _list(value: object, where: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise _refuse(f"{where}: {value!r} is not a list")
    return tuple(value)  # pyright: ignore[reportUnknownArgumentType]


def _unit_tuple(value: object) -> tuple[Unit, ...]:
    return tuple(unit_from_facet(v) for v in _list(value, "units"))  # type: ignore[arg-type]


def _pairs(value: object, where: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        raise _refuse(f"{where}: {value!r} is not a mapping")
    return tuple(sorted(value.items()))  # type: ignore[arg-type]


@sealed
@final
@dataclass(frozen=True)
class ExposureEvent:
    channel: str
    subjects: tuple[str, ...]
    units: tuple[Unit, ...]
    effect: str
    read_class: str
    bound: tuple[tuple[str, str], ...]
    account: str
    observer: str
    recorded_by: str
    observed_at: str
    propositions: tuple[str, ...]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _one_of(self.channel, CHANNELS, "an exposure event's channel")
        subjects = _strings(self.subjects, "subjects", ("dataset:", "source:"))
        if (self.channel == "read") != bool(subjects):
            raise _refuse("an exposure event names subjects exactly when its channel is `read`")
        _units(self.units, "an exposure event's units")
        _one_of(self.effect, EFFECTS, "an exposure event's effect")
        _text(self.read_class, "an exposure event's class")
        _digest_map(self.bound, "bound")
        _text(self.account, "an exposure event's account")
        _strings((self.observer,), "observer", actors=True)
        _strings((self.recorded_by,), "recorded_by", actors=True)
        _timestamp(self.observed_at, "observed_at")
        _strings(self.propositions, "propositions", ("proposition:",))
        _strings(self.evidence, "evidence", tokens=True)

    def facet(self) -> dict[str, object]:
        out: dict[str, object] = {
            "channel": self.channel,
            "subjects": list(self.subjects),
            "units": [unit_facet(u) for u in self.units],
            "effect": self.effect,
            "class": self.read_class,
        }
        if self.bound:
            out["bound"] = dict(self.bound)
        out["account"] = self.account
        out["observer"] = self.observer
        out["recorded_by"] = self.recorded_by
        out["observed_at"] = self.observed_at
        out["propositions"] = list(self.propositions)
        if self.evidence:
            out["evidence"] = list(self.evidence)
        return out

    def identity(self) -> str:
        return v1.digest(EXPOSURE_EVENT_DOMAIN, self.facet())

    @property
    def id(self) -> str:
        return f"exposure-event:{self.identity()}"

    def kernel_evidence(self) -> tuple[str, ...]:
        return _kernel_entries(self.evidence, _EVENT_KERNEL_EVIDENCE)


def _kernel_entries(entries: tuple[str, ...], schemes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(e for e in entries if e.split(":", 1)[0] in schemes)


def exposure_event_from_facet(facet: Mapping[str, object]) -> ExposureEvent:
    if not isinstance(facet, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise _refuse(f"an exposure-event facet is a mapping, not {facet!r}")
    _only(
        facet,
        {"channel", "subjects", "units", "effect", "class", "account", "observer", "recorded_by", "observed_at"}
        | {"propositions"},
        {"bound", "evidence"},
        "an exposure-event facet",
    )
    return ExposureEvent(
        channel=facet["channel"],  # type: ignore[arg-type]
        subjects=_list(facet["subjects"], "subjects"),  # type: ignore[arg-type]
        units=_unit_tuple(facet["units"]),
        effect=facet["effect"],  # type: ignore[arg-type]
        read_class=facet["class"],  # type: ignore[arg-type]
        bound=_pairs(facet.get("bound", {}), "bound"),
        account=facet["account"],  # type: ignore[arg-type]
        observer=facet["observer"],  # type: ignore[arg-type]
        recorded_by=facet["recorded_by"],  # type: ignore[arg-type]
        observed_at=facet["observed_at"],  # type: ignore[arg-type]
        propositions=_list(facet["propositions"], "propositions"),  # type: ignore[arg-type]
        evidence=_list(facet.get("evidence", []), "evidence"),  # type: ignore[arg-type]
    )


def _check_groups(groups: tuple[Group, ...]) -> None:
    if not groups or any(not isinstance(g, Group) for g in groups):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise _refuse("a reservation assignment holds at least one group")
    _sorted_distinct(groups, "groups", lambda g: unit_sort_key(g.first))
    every = [u for g in groups for u in g.units]
    if len({unit_shape(u) for u in every}) > 1:
        raise _refuse("a reservation assignment holds one unit shape")
    if len(set(every)) != len(every):
        raise _refuse("a unit sits in exactly one group")
    intervals = sorted((u for u in every if isinstance(u, IntervalUnit)), key=unit_sort_key)
    for before, after in pairwise(intervals):
        if not unit_sort_key(before)[2] <= unit_sort_key(after)[1]:
            raise _refuse(f"interval units overlap: {unit_facet(before)} and {unit_facet(after)}")


@sealed
@final
@dataclass(frozen=True)
class ReservationAssignment:
    chain: str
    rule_name: str
    rule_version: str
    inputs: tuple[tuple[str, str], ...]
    events: tuple[str, ...]
    scope: str | None
    applies: str | None
    groups: tuple[Group, ...]
    predecessor: str | None
    evidence: tuple[str, ...]
    flagged: tuple[str, ...] | None
    account: str | None
    participants: tuple[str, ...]
    prior_runs: tuple[str, ...]
    assigned_at: str
    assigned_by: str

    def __post_init__(self) -> None:
        if type(self.chain) is not str or _NAME.fullmatch(self.chain) is None:
            raise _refuse(f"chain {self.chain!r} does not match [a-z][a-z0-9-]*")
        _text(self.rule_name, "rule name")
        _text(self.rule_version, "rule version")
        if not _digest_map(self.inputs, "inputs"):
            raise _refuse("inputs may not be empty")
        _strings(self.events, "events", ("exposure-event:",))
        for where, value, prefix in (
            ("scope", self.scope, "proposition:"),
            ("applies", self.applies, "reservation-assignment:"),
            ("predecessor", self.predecessor, "reservation-assignment:"),
        ):
            if value is not None:
                _prefixed(value, (prefix,), where)
        _check_groups(_tuple(self.groups, "groups"))  # type: ignore[arg-type]
        _strings(self.evidence, "evidence", tokens=True)
        if self.flagged is not None:
            _strings(self.flagged, "flagged", ("assessment:",))
        if self.account is not None:
            _text(self.account, "account")
        _strings(self.participants, "participants", actors=True)
        _strings(self.prior_runs, "prior_runs", tokens=True)
        _timestamp(self.assigned_at, "assigned_at")
        _strings((self.assigned_by,), "assigned_by", actors=True)

    def facet(self) -> dict[str, object]:
        out: dict[str, object] = {
            "chain": self.chain,
            "rule": {"name": self.rule_name, "version": self.rule_version},
            "inputs": dict(self.inputs),
            "events": list(self.events),
        }
        if self.scope is not None:
            out["scope"] = self.scope
        if self.applies is not None:
            out["applies"] = self.applies
        out["groups"] = [g.facet() for g in self.groups]
        if self.predecessor is not None:
            out["predecessor"] = self.predecessor
        if self.evidence:
            out["evidence"] = list(self.evidence)
        if self.flagged is not None:
            out["flagged"] = list(self.flagged)
        if self.account is not None:
            out["account"] = self.account
        if self.participants:
            out["participants"] = list(self.participants)
        if self.prior_runs:
            out["prior_runs"] = list(self.prior_runs)
        out["assigned_at"] = self.assigned_at
        out["assigned_by"] = self.assigned_by
        return out

    def identity(self) -> str:
        return v1.digest(RESERVATION_ASSIGNMENT_DOMAIN, self.facet())

    @property
    def id(self) -> str:
        return f"reservation-assignment:{self.identity()}"

    @property
    def shape(self) -> str:
        return unit_shape(self.groups[0].first)

    def kernel_evidence(self) -> tuple[str, ...]:
        return _kernel_entries(self.evidence, _ASSIGNMENT_KERNEL_EVIDENCE)

    def kernel_prior_runs(self) -> tuple[str, ...]:
        return _kernel_entries(self.prior_runs, _PRIOR_RUN_KERNEL_REFS)


def reservation_assignment_from_facet(facet: Mapping[str, object]) -> ReservationAssignment:
    if not isinstance(facet, Mapping):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise _refuse(f"a reservation-assignment facet is a mapping, not {facet!r}")
    _only(
        facet,
        {"chain", "rule", "inputs", "events", "groups", "assigned_at", "assigned_by"},
        {"scope", "applies", "predecessor", "evidence", "flagged", "account", "participants", "prior_runs"},
        "a reservation-assignment facet",
    )
    rule = facet["rule"]
    if not isinstance(rule, Mapping):
        raise _refuse(f"rule: {rule!r} is not a mapping")
    _only(rule, {"name", "version"}, set(), "rule")  # pyright: ignore[reportUnknownArgumentType]
    flagged = facet.get("flagged")
    return ReservationAssignment(
        chain=facet["chain"],  # type: ignore[arg-type]
        rule_name=rule["name"],  # type: ignore[arg-type]
        rule_version=rule["version"],  # type: ignore[arg-type]
        inputs=_pairs(facet["inputs"], "inputs"),
        events=_list(facet["events"], "events"),  # type: ignore[arg-type]
        scope=facet.get("scope"),  # type: ignore[arg-type]
        applies=facet.get("applies"),  # type: ignore[arg-type]
        groups=tuple(_group_from_facet(g) for g in _list(facet["groups"], "groups")),
        predecessor=facet.get("predecessor"),  # type: ignore[arg-type]
        evidence=_list(facet.get("evidence", []), "evidence"),  # type: ignore[arg-type]
        flagged=None if flagged is None else _list(flagged, "flagged"),  # type: ignore[arg-type]
        account=facet.get("account"),  # type: ignore[arg-type]
        participants=_list(facet.get("participants", []), "participants"),  # type: ignore[arg-type]
        prior_runs=_list(facet.get("prior_runs", []), "prior_runs"),  # type: ignore[arg-type]
        assigned_at=facet["assigned_at"],  # type: ignore[arg-type]
        assigned_by=facet["assigned_by"],  # type: ignore[arg-type]
    )


@sealed
@final
@dataclass(frozen=True)
class GroupChange:
    unit: Unit
    kind: str
    previous_role: str | None
    suspended: bool


def assignment_changes(predecessor: ReservationAssignment, successor: ReservationAssignment) -> tuple[GroupChange, ...]:
    held: dict[Unit, Group] = {u: g for g in successor.groups for u in g.units}
    covered: set[Unit] = {u for g in predecessor.groups for u in g.units}
    changes: list[GroupChange] = []
    for group in predecessor.groups:
        found = held.get(group.first)
        if found is not None and found == group:
            continue
        changes.append(
            GroupChange(group.first, "absent" if found is None else "changed", group.role, group.role == "reserved")
        )
    for group in successor.groups:
        if group.first not in covered:
            changes.append(GroupChange(group.first, "added", None, False))
    return tuple(changes)


# --- the checks the boundary raises and the audit reports ----------------------


@sealed
@final
@dataclass(frozen=True)
class CheckRefusal:
    """One failed check: the stable code the reservation tables carry and the detail naming the position.
    The write boundary raises it as `ReservationRefused(code, f"{id}: {detail}")`; the audit reports it as
    a `Finding` with the same code and detail."""

    code: str
    detail: str


class Unread(Enum):
    """A cited reference its caller cannot read here (recorded in an absent corpus, or unreadable in its
    own right): the audit's neighbour case, never the boundary's. The checks that need it are skipped."""

    UNREAD = "unread"


UNREAD = Unread.UNREAD

KindOf = Callable[[str], "str | Unread | None"]
"""The caller's resolution: the kind of the record a reference names, None when it names no record here,
or `UNREAD` when it names one that cannot be read here."""


def exposure_event_refusal(
    value: ExposureEvent, relations: Sequence[Relation], *, kind_of: KindOf, sorts: Container[str]
) -> CheckRefusal | None:
    """An exposure event's edges mirror its facet exactly, every kernel reference resolves to a record of
    the kind its slot names, and each unit sort is declared; the first failure in that order."""
    from beliefs import stored  # local: `stored` imports this module

    if list(relations) != stored.exposure_event_relations(value):
        return CheckRefusal("exposure-edge-mismatch", "the relations differ from those the facet names")
    slots: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
        ("subject", value.subjects, ("dataset", "source")),
        ("proposition", value.propositions, ("proposition",)),
        ("evidence", value.kernel_evidence(), ("act-report", "run", "holdings-observation")),
    ]
    for slot, refs, kinds in slots:
        for ref in refs:
            found = kind_of(ref)
            if found is None:
                return CheckRefusal("exposure-ref-unresolved", f"the {slot} {ref!r} resolves to no record here")
            if found is UNREAD:
                continue
            if found not in kinds:
                return CheckRefusal(
                    "exposure-ref-unresolved", f"the {slot} {ref!r} is a {found}, not one of {', '.join(kinds)}"
                )
    for unit in value.units:
        if isinstance(unit, TermUnit) and unit.sort not in sorts:
            return CheckRefusal("exposure-unit-sort-undeclared", f"the unit sort {unit.sort!r} is not declared")
    return None


def assignment_record_refusal(
    value: ReservationAssignment,
    relations: Sequence[Relation],
    *,
    kind_of: KindOf,
    assignment_of: Callable[[str], ReservationAssignment | None],
    sorts: Container[str],
) -> CheckRefusal | None:
    """An assignment's own record, before its chain: edges mirror its facet (a successor's one
    `supersedes` edge names its `predecessor`, a root carries none), every kernel reference resolves to a
    record of the kind its slot names, `applies` names a program-level assignment, and each unit sort is
    declared; the first failure in that order. `assignment_of` reads a resolved `applies` whole (None
    when it cannot be read here, which skips the check); it is never asked for an `UNREAD` reference."""
    from beliefs import stored  # local: `stored` imports this module

    succession = [relation for relation in relations if relation.predicate == stored.SUPERSEDES]
    mirrored = [relation for relation in relations if relation.predicate != stored.SUPERSEDES]
    if mirrored != stored.reservation_assignment_relations(value):
        return CheckRefusal("assignment-edge-mismatch", "the relations differ from those the facet names")
    if value.predecessor is None and succession:
        return CheckRefusal("assignment-edge-mismatch", "a chain root carries no supersedes edge")
    if value.predecessor is not None and [r.target for r in succession] != [value.predecessor]:
        return CheckRefusal(
            "assignment-edge-mismatch",
            f"a successor carries exactly one supersedes edge, to its predecessor {value.predecessor!r}",
        )
    slots: list[tuple[str, tuple[str, ...], str]] = [
        ("event", value.events, "exposure-event"),
        ("evidence", value.kernel_evidence(), "exposure-event"),
        ("flagged assessment", value.flagged or (), "assessment"),
        ("prior run", value.kernel_prior_runs(), "run"),
        ("scope", () if value.scope is None else (value.scope,), "proposition"),
        ("applies", () if value.applies is None else (value.applies,), "reservation-assignment"),
        ("predecessor", () if value.predecessor is None else (value.predecessor,), "reservation-assignment"),
    ]
    unread: set[str] = set()
    for slot, refs, kind in slots:
        for ref in refs:
            found = kind_of(ref)
            if found is None:
                return CheckRefusal("assignment-ref-unresolved", f"the {slot} {ref!r} resolves to no record here")
            if found is UNREAD:
                unread.add(ref)
                continue
            if found != kind:
                return CheckRefusal("assignment-ref-unresolved", f"the {slot} {ref!r} is a {found}, not a {kind}")
    if value.applies is not None and value.applies not in unread:
        applied = assignment_of(value.applies)
        if applied is not None and applied.scope:
            return CheckRefusal(
                "assignment-applies-scoped",
                f"applies {value.applies!r}, a scoped assignment; it applies a program-level one",
            )
    for group in value.groups:
        for unit in group.units:
            if isinstance(unit, TermUnit) and unit.sort not in sorts:
                return CheckRefusal("assignment-unit-sort-undeclared", f"the unit sort {unit.sort!r} is not declared")
    return None


_SUCCESSION_KEYS = frozenset({"predecessor", "assigned_at", "assigned_by"})


def _derivation(value: ReservationAssignment) -> dict[str, object]:
    """The facet without the keys every succession changes or may change (`predecessor`, `assigned_at`,
    `assigned_by`): the door's semantic-identity check covers them, so it cannot see a successor whose
    facet otherwise equals its predecessor's (ruling R3a)."""
    return {key: field for key, field in value.facet().items() if key not in _SUCCESSION_KEYS}


def assignment_succession_refusal(
    value: ReservationAssignment, predecessor: ReservationAssignment | None
) -> CheckRefusal | None:
    """An assignment against its predecessor, after the chain's linearity: a successor keeps its
    predecessor's chain, scope and unit shape, changes the derivation, and evidences every derived
    change; then, for a root or a successor alike, every suspension is flagged and a flag needs one. The
    first failure in that order. `predecessor` is the record `value.predecessor` names, read whole, and
    None exactly for a root."""
    if (predecessor is None) != (value.predecessor is None):
        raise ValueError("assignment_succession_refusal takes the predecessor exactly when the value names one")
    changes: tuple[GroupChange, ...] = ()
    if predecessor is not None:
        if (predecessor.chain, predecessor.scope, predecessor.shape) != (value.chain, value.scope, value.shape):
            return CheckRefusal(
                "assignment-scope-mismatch",
                f"chain, scope and unit shape {(value.chain, value.scope, value.shape)!r} differ "
                f"from the predecessor's {(predecessor.chain, predecessor.scope, predecessor.shape)!r}",
            )
        if _derivation(predecessor) == _derivation(value):
            return CheckRefusal(
                "assignment-unchanged",
                "the facet, but for predecessor, assigned_at and assigned_by, equals the predecessor's",
            )
        changes = assignment_changes(predecessor, value)
        if changes and not value.evidence:
            return CheckRefusal(
                "assignment-changes-without-evidence",
                f"{len(changes)} group change(s) from the predecessor and no evidence",
            )
    suspended = any(change.suspended for change in changes)
    if suspended and value.flagged is None:
        return CheckRefusal(
            "assignment-suspension-unflagged",
            "a reserved group changes and no flagged list names the assessments made",
        )
    if not suspended and value.flagged is not None:
        return CheckRefusal("assignment-flagged-without-suspension", "flagged is present and no reserved group changes")
    return None


class RecordView(Protocol):
    """What the view helpers read: a corpus `ReadView`, a captured check view or any other view with
    these two methods."""

    def iter_stored(self) -> Iterator[Node]: ...

    def get(self, ref: str) -> Node: ...


def exposure_events(
    view: RecordView, *, subject: str | None = None, proposition: str | None = None
) -> tuple[ExposureEvent, ...]:
    """Every stored exposure event, narrowed to those whose `exposes` edges name `subject` and whose
    `concerns` edges name `proposition` (the facet's `subjects` and `propositions`, which the edges
    mirror), ordered by `observed_at` then id. A malformed event refuses (`MalformedRecord`): a reader
    that skipped it would understate exposure."""
    from beliefs import stored  # local: `stored` imports this module

    found: list[ExposureEvent] = []
    for node in view.iter_stored():
        if node.kind != "exposure-event":
            continue
        event = stored.exposure_event_value(node)
        if subject is not None and subject not in event.subjects:
            continue
        if proposition is not None and proposition not in event.propositions:
            continue
        found.append(event)
    return tuple(sorted(found, key=lambda event: (event.observed_at, event.id)))


def assignment_head(view: RecordView, chain: str, *, scope: str | None = None) -> ReservationAssignment | None:
    """The record of chain `chain` × `scope` that no other record of it supersedes, or None when the
    chain has no record. Two roots or two heads are a fork, refused as `ChainAmbiguous` rather than
    resolved by choosing one; a malformed assignment refuses (`MalformedRecord`), since it may be a
    member of the chain asked for."""
    from beliefs import stored  # local: `stored` imports this module

    members = {
        value.id: value
        for value in (
            stored.reservation_assignment_value(node)
            for node in view.iter_stored()
            if node.kind == "reservation-assignment"
        )
        if (value.chain, value.scope) == (chain, scope)
    }
    roots = sorted(ref for ref, value in members.items() if value.predecessor is None)
    if len(roots) > 1:
        raise ChainAmbiguous(f"chain {chain!r} (scope {scope!r}) has two roots: {roots[0]} and {roots[1]}")
    superseded = {value.predecessor for value in members.values()}
    heads = sorted(ref for ref in members if ref not in superseded)
    if len(heads) > 1:
        raise ChainAmbiguous(f"chain {chain!r} (scope {scope!r}) has two heads: {heads[0]} and {heads[1]}")
    return members[heads[0]] if heads else None


def assignment_changes_of(view: RecordView, ref: str) -> tuple[GroupChange, ...]:
    """The group changes the assignment at `ref` makes from its predecessor; empty for a chain root."""
    from beliefs import stored  # local: `stored` imports this module

    value = stored.reservation_assignment_value(view.get(ref))
    if value.predecessor is None:
        return ()
    return assignment_changes(stored.reservation_assignment_value(view.get(value.predecessor)), value)
