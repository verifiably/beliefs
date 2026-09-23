from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, final

from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.node import Node

from beliefs import stored
from beliefs.errors import MalformedRecord
from beliefs.sealed import sealed

if TYPE_CHECKING:
    # `beliefs.world` imports `beliefs.corpus`, which imports this module: the
    # views and `place` are imported inside the functions that use them.
    from beliefs.world.logmodel import ChainView, RegisteredEntryView, WellFormedView

__all__ = [
    "COORDINATION_KINDS",
    "ORDINARY_COORDINATION_KINDS",
    "PUBLICATION_KINDS",
    "VIEW_KINDS",
    "Anchor",
    "ChainBound",
    "CoordinationAddress",
    "CoordinationRefused",
    "CoordinationRevision",
    "MomentSeam",
    "PositionRefusalReason",
    "PositionRefused",
    "bounds",
    "coordination_facet_malformed",
    "coordination_revision",
    "inventory",
    "present_records",
    "standing_at",
    "standing_tips",
]

VIEW_KINDS = ("project", "question", "hypothesis", "topic", "theme")
ORDINARY_COORDINATION_KINDS = (*VIEW_KINDS, "task", "decision", "note")
PUBLICATION_KINDS = ("publication", "publication-binding")
"""Minted only by the publish doors (publication-records design decision 6)."""
COORDINATION_KINDS = (*ORDINARY_COORDINATION_KINDS, *PUBLICATION_KINDS)
_ADDRESS = re.compile(r"coord:([0-9a-f]{32})(?:/([0-9a-f]{32}))?(?:@([0-9a-f]{32}))?")
_HEX = re.compile(r"[0-9a-f]{32}")
_ENTRY_DIGEST = re.compile(r"[0-9a-f]{64}")
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


@sealed
@final
@dataclass(frozen=True)
class Anchor:
    """One mounted root's head at a publish intent (publication-records design decision 3)."""

    corpus_id: str
    genesis: str
    head: str

    def __post_init__(self) -> None:
        # type first: `re.fullmatch` on a non-string raises TypeError, not MalformedRecord
        if type(self.corpus_id) is not str or _HEX.fullmatch(self.corpus_id) is None:
            raise MalformedRecord("anchor corpus_id must be 32 lowercase hexadecimal characters")
        for name in ("genesis", "head"):
            value = getattr(self, name)
            if type(value) is not str or _ENTRY_DIGEST.fullmatch(value) is None:
                raise MalformedRecord(f"anchor {name} must be a 64-lowercase-hex entry digest")


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


# --- the intent-position judgment (publication-records design §6) -------------

PositionRefusalReason = Literal[
    "mounts-changed",
    "anchor-unplaced",
    "chain-absent",
    "chain-malformed",
    "revision-missing",
    "revision-mismatch",
    "revision-malformed",
    "history-violated",
    "unregistered-revision",
    "report-unqualified",
]


@sealed
@final
@dataclass(frozen=True)
class PositionRefused:
    """The judgment cannot read the position: evidence refused, as a value."""

    reason: PositionRefusalReason
    detail: str


@sealed
@final
@dataclass(frozen=True)
class MomentSeam:
    """The engine's part of the judgment, as callables built in `root.py`
    (`moment_seam()`): this module compares `FileState`s and holds `ABSENT`
    only through them, and imports nothing of the engine."""

    inspect_written: Callable[[Path], ChainView]  # registered: the root this process locks and writes
    inspect_other: Callable[[Path], ChainView]  # detached: read-only, no recovery, for roots it does not lock
    absent_state: object
    is_file: Callable[[object], bool]
    file_matches: Callable[[object, bytes], bool]


@sealed
@final
@dataclass(frozen=True)
class ChainBound:
    """One mounted root read at its bound: `view.entries[: head + 1]` is what the position sees."""

    root: Path
    corpus_id: str
    view: WellFormedView
    head: int
    written: bool  # which inspector re-reads it


def bounds(
    mounts: Mapping[Path, str], *, written: Path, position: str, anchors: Sequence[Anchor], seam: MomentSeam
) -> tuple[ChainBound, ...] | PositionRefused:
    """Each mounted root's bound (spec §6): the written root's is the entry
    `position`; every other root's is its anchor's placement."""
    from beliefs.world.events import place
    from beliefs.world.logmodel import AbsentView, MalformedView, WellFormedView

    written = Path(written).resolve()
    by_corpus = {anchor.corpus_id: anchor for anchor in anchors}
    if (
        written not in mounts
        or len(mounts) != len(anchors) + 1
        or set(mounts.values()) != {mounts[written], *by_corpus}
        or mounts[written] in by_corpus
    ):
        return PositionRefused("mounts-changed", "the mounted corpora are not the written root plus the anchored ones")
    found: list[ChainBound] = []
    for root, corpus_id in mounts.items():
        view = (seam.inspect_written if root == written else seam.inspect_other)(root)
        if type(view) is AbsentView:
            return PositionRefused("chain-absent", str(root))
        if type(view) is MalformedView:
            return PositionRefused("chain-malformed", f"{root}: {view.defect.kind}")
        if type(view) is not WellFormedView:  # the union is closed; an inspector answering anything else is a defect
            raise TypeError(f"{root}: the inspector answered {type(view).__name__}, not a chain view")
        if root == written:
            heads = [index for index, entry in enumerate(view.entries) if entry.digest == position]
            if len(heads) != 1:
                return PositionRefused("anchor-unplaced", f"{root}: the position {position} is no entry of the chain")
            found.append(ChainBound(root, corpus_id, view, heads[0], True))
            continue
        anchor = by_corpus[corpus_id]
        placement = place(view, genesis_digest=anchor.genesis, head_digest=anchor.head)
        if placement is None:
            return PositionRefused("anchor-unplaced", f"{root}: the anchor does not place in the live chain")
        found.append(ChainBound(root, corpus_id, view, placement.head, False))
    return tuple(found)


def _committed_in_order(view: WellFormedView, head: int) -> list[RegisteredEntryView]:
    """Committed registrations whose settlement is at or before `head`, in settlement order."""
    from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView

    registrations = {entry.digest: entry for entry in view.entries if type(entry) is RegisteredEntryView}
    ordered: list[RegisteredEntryView] = []
    for entry in view.entries[: head + 1]:
        if type(entry) is SettledEntryView and entry.committed and entry.registration in registrations:
            ordered.append(registrations[entry.registration])
    return ordered


def _creates(registration: RegisteredEntryView, path: str, seam: MomentSeam) -> bool:
    """An actual creation: the registration's own `initial` holds the path ABSENT
    and its `final` a file. The replay's prior state is not evidence of the
    registration's pre-state; the registration's `initial` is."""
    initial = dict(registration.initial)
    final = dict(registration.final)
    return initial.get(path, seam.absent_state) == seam.absent_state and seam.is_file(final[path])


def inventory(bound: ChainBound, prefix: str, seam: MomentSeam) -> dict[str, object] | PositionRefused:
    """Replay the committed registrations up to the bound over paths under `prefix` (spec §6).

    Only an ABSENT → file transition (on the registration's own `initial`) enters
    the inventory. Any other committed transition of an address path — a file
    rewritten, removed, or a file that was already present when its first
    committed registration touched it — is `history-violated`: the registration
    itself records an act on an immutable record that no door performs, whether
    or not the record's creation was ever registered."""
    state: dict[str, object] = {}
    for registration in _committed_in_order(bound.view, bound.head):
        initial = dict(registration.initial)
        for path, post in registration.final:
            if not path.startswith(prefix):
                continue
            pre = initial.get(path, seam.absent_state)
            prior = state.get(path, seam.absent_state)
            if pre == seam.absent_state and post == seam.absent_state and prior == seam.absent_state:
                continue
            if prior != seam.absent_state or not _creates(registration, path, seam):
                return PositionRefused("history-violated", f"{bound.root}: {path} was not created by this registration")
            state[path] = post
    return state


def _created_anywhere(view: WellFormedView, seam: MomentSeam) -> frozenset[str]:
    """Every path some registration, settled or not, *creates* (ABSENT → file on
    its own `initial`). A registration that rewrites a present file creates nothing,
    so an unaccounted file whose only registrations rewrite it is unregistered."""
    from beliefs.world.logmodel import RegisteredEntryView

    return frozenset(
        path
        for entry in view.entries
        if type(entry) is RegisteredEntryView
        for path, _post in entry.final
        if _creates(entry, path, seam)
    )


def present_records(bound: ChainBound, prefix: str, seam: MomentSeam) -> tuple[tuple[str, bytes], ...] | PositionRefused:
    """Every inventoried path's bytes, read and matched; every unaccounted file
    classified by a re-read of the chain (spec §6): a file some registration in
    the re-read creates — pending, rolled back, or committed after the bound —
    is not present and not a refusal; any other is `unregistered-revision`."""
    from beliefs.world.logmodel import AbsentView, MalformedView, WellFormedView

    expected = inventory(bound, prefix, seam)
    if type(expected) is PositionRefused:
        return expected
    found: list[tuple[str, bytes]] = []
    for path in sorted(expected):
        file = bound.root / path
        if not file.is_file():
            return PositionRefused("revision-missing", f"{bound.root}: {path}")
        data = file.read_bytes()
        if not seam.file_matches(expected[path], data):
            return PositionRefused("revision-mismatch", f"{bound.root}: {path}")
        found.append((path, data))
    directory, _, stem = prefix.rpartition("/")
    listed = (
        sorted(f"{directory}/{candidate.name}" for candidate in (bound.root / directory).glob(f"{stem}*") if candidate.is_file())
        if (bound.root / directory).is_dir()
        else []
    )
    unaccounted = [path for path in listed if path not in expected]
    if unaccounted:
        reread = (seam.inspect_written if bound.written else seam.inspect_other)(bound.root)
        if type(reread) is AbsentView:
            return PositionRefused("chain-absent", f"{bound.root}: the re-read found no chain")
        if type(reread) is MalformedView:
            return PositionRefused("chain-malformed", f"{bound.root}: the re-read is {reread.defect.kind}")
        if type(reread) is not WellFormedView:  # the union is closed; an inspector answering anything else is a defect
            raise TypeError(f"{bound.root}: the inspector answered {type(reread).__name__}, not a chain view")
        created = _created_anywhere(reread, seam)
        for path in unaccounted:
            if path not in created:
                return PositionRefused("unregistered-revision", f"{bound.root}: {path}")
    return tuple(found)


def standing_at(
    mounts: Mapping[Path, str],
    address: CoordinationAddress,
    kind: str,
    *,
    written: Path,
    position: str,
    anchors: Sequence[Anchor],
    seam: MomentSeam,
) -> tuple[CoordinationRevision, ...] | PositionRefused:
    """The standing tips of `address` at the intent's position (spec §6): the
    family's one tip rule over the chain's inventory at each root's bound."""
    from nodes.core.frontmatter import node_from_bytes

    from beliefs.publication import publication_content_malformed

    if kind not in COORDINATION_KINDS:
        raise ValueError(f"{kind!r} is not a coordination kind")
    address = address.unpinned()
    found = bounds(mounts, written=written, position=position, anchors=anchors, seam=seam)
    if type(found) is PositionRefused:
        return found
    # `nodes`' `path_for_node_id` over the coordination id form
    prefix = f"{kind}/{address.project}." if address.local is None else f"{kind}/{address.project}.{address.local}."
    by_uid: dict[str, CoordinationRevision] = {}
    for bound in found:
        records = present_records(bound, prefix, seam)
        if type(records) is PositionRefused:
            return records
        for path, data in records:
            try:
                node = node_from_bytes(data)
                revision = coordination_revision(node)
            except (NodesValidationError, MalformedRecord):
                return PositionRefused("revision-malformed", f"{bound.root}: {path}")
            if (
                node.kind != kind
                or revision.address != address
                or (kind in PUBLICATION_KINDS and publication_content_malformed(node))
            ):
                return PositionRefused("revision-malformed", f"{bound.root}: {path}")
            prior = by_uid.get(node.uid)
            if prior is not None and prior.node != node:
                return PositionRefused("revision-mismatch", f"{node.uid}: unequal copies across mounts")
            by_uid[node.uid] = revision
    return standing_tips(tuple(by_uid.values()))
