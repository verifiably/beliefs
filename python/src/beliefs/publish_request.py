"""Step 0's pure pieces (publish-act-local design §4): the publication closure,
the destination pins, the usable operations root and destination, and the two
records the operations root holds — the selection snapshot and the request."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from nodes.core.frontmatter import node_from_markdown, node_to_markdown

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress
from beliefs.errors import CanonicalTextRefused, MalformedRecord, PublicationRefused
from beliefs.identity import v1
from beliefs.intents.publish import Destination
from beliefs.profile import ProfileSpec, shipped_coordination

__all__ = [
    "PUBLISHING_COORDINATION",
    "PublishRequest",
    "Snapshot",
    "closure_missing",
    "decode_request",
    "decode_snapshot",
    "derive_pins",
    "encode_request",
    "encode_snapshot",
    "pins_of",
    "require_usable",
    "staging_world_id_for",
]

SELECTION_DOMAIN = "science.publish-selection.v1"
REQUEST_DOMAIN = "science.publish-request.v1"
_STAGING_WORLD_DOMAIN = "science.publish-staging-world.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")

PUBLISHING_COORDINATION = frozenset(
    f"coordination:{shipped_coordination(version).content_identity}"
    for version in (1, 2)
    if "publication" in shipped_coordination(version).kinds
)
"""The coordination pins that authorize a publication marker (spec §4.1 item 6)."""


def closure_missing(view, selected: tuple[str, ...]) -> tuple[str, ...]:
    """Every world-relation endpoint of a selected record outside the selection
    (spec §4.1 item 5), by its live address, or by its stored spelling when it
    does not resolve. `view` answers `get(id)` and `resolve(ref)`."""
    chosen = set(selected)
    missing: set[str] = set()
    for address in selected:
        node = view.get(address)
        for relation in node.relations:
            if relation.predicate not in stored.WORLD_RELATIONS:
                continue
            for endpoint in (relation.source, relation.target):
                if endpoint == node.id:
                    continue
                live = view.resolve(endpoint)
                if live is None:
                    missing.add(endpoint)
                elif live not in chosen:
                    missing.add(live)
    return tuple(sorted(missing))


def derive_pins(manifests: Mapping[str, CorpusPins], written: CorpusPins) -> CorpusPins:
    """The destination's one `CorpusPins` (spec §4.1 item 6): one base contract,
    the union of the contributing domains, and the written root's coordination
    pin, which must authorize `publication`."""
    corpus_ids = tuple(sorted(manifests))
    contracts = {pins.science_contract for pins in manifests.values()} | {written.science_contract}
    if len(contracts) != 1:
        raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field="science_contract")
    domains: dict[str, str] = {}
    for corpus_id in corpus_ids:
        for namespace, pin in sorted(manifests[corpus_id].domains.items()):
            if domains.setdefault(namespace, pin) != pin:
                raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field=namespace)
    coordination = written.domains.get("coordination")
    if coordination not in PUBLISHING_COORDINATION:
        raise PublicationRefused("coordination-unpinned")
    if domains.setdefault("coordination", coordination) != coordination:
        raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field="coordination")
    (science_contract,) = contracts
    return CorpusPins(science_contract, domains)


def pins_of(profile: ProfileSpec) -> CorpusPins:
    """The pins a writer holding `profile` adopts (`CorpusWriter.adopt_manifest`'s rule)."""
    return CorpusPins(
        "science:" + profile.base_contract_identity,
        {namespace: f"{namespace}:{identity}" for namespace, identity in profile.activated_contracts.items()},
    )


def _inside(path: Path, other: Path) -> bool:
    return path == other or other in path.parents


def require_usable(operations_root: Path, destination: Destination, *, forbidden: Sequence[Path]) -> tuple[Path, Path]:
    """The resolved operations root and local destination directory (spec §3,
    §4.1 item 7): both existing directories, neither inside the other, neither
    inside a mounted corpus root or the world root (`forbidden`)."""
    closed = tuple(Path(path).resolve() for path in forbidden)
    ops = Path(operations_root)
    if not ops.is_absolute() or not ops.is_dir() or any(_inside(ops.resolve(), path) for path in closed):
        raise PublicationRefused("operations-root-unusable")
    ops = ops.resolve()
    target = Path(destination.locator)
    if not target.is_dir():
        raise PublicationRefused("destination-unusable")
    target = target.resolve()
    if _inside(target, ops) or _inside(ops, target) or any(_inside(target, path) for path in closed):
        if _inside(ops, target) and not _inside(target, ops):
            raise PublicationRefused("operations-root-unusable")
        raise PublicationRefused("destination-unusable")
    return ops, target


def staging_world_id_for(event_token: str) -> str:
    return v1.digest(_STAGING_WORLD_DOMAIN, event_token)[:32]


def _hex(value: object, pattern: re.Pattern[str], where: str) -> None:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise MalformedRecord(f"{where} is {'32' if pattern is _HEX32 else '64'} lowercase hex")


@dataclass(frozen=True)
class Snapshot:
    """The selected records' canonical text, frozen at step 0 (spec §4.3)."""

    event_token: str
    records: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _hex(self.event_token, _HEX32, "a snapshot's event token")
        if type(self.records) is not tuple or not self.records:
            raise MalformedRecord("a snapshot holds a non-empty tuple of records")
        for row in self.records:
            if type(row) is not tuple or len(row) != 2 or any(type(member) is not str for member in row):
                raise MalformedRecord("a snapshot record is an (id, text) pair of strings")
            try:
                node = node_from_markdown(row[1])
            except Exception as caught:  # nodes and pydantic raise several types for unparseable text
                raise MalformedRecord(f"{row[0]}: a snapshot record's text does not parse: {caught}") from caught
            if node.id != row[0] or node.body != "" or node_to_markdown(node) != row[1]:
                raise MalformedRecord(f"{row[0]}: a snapshot record's text is not that record's canonical rendering")
        ids = [row[0] for row in self.records]
        if ids != sorted(set(ids)):
            raise MalformedRecord("a snapshot's records are strictly ascending by id")

    def projection(self) -> dict[str, object]:
        return {
            "domain": SELECTION_DOMAIN,
            "event_token": self.event_token,
            "records": [{"id": record_id, "text": text} for record_id, text in self.records],
        }

    def identity(self) -> str:
        return v1.digest(SELECTION_DOMAIN, self.projection())


def encode_snapshot(snapshot: Snapshot) -> bytes:
    return v1.encode(snapshot.projection())


def _decoded(data: bytes, where: str) -> dict:
    try:
        value = v1.decode(data)
    except CanonicalTextRefused as caught:
        raise MalformedRecord(f"{where} is not canonical text: {caught}") from caught
    if not isinstance(value, dict):
        raise MalformedRecord(f"{where} is a mapping")
    return value


def decode_snapshot(data: bytes) -> Snapshot:
    value = _decoded(data, "a snapshot")
    if set(value) != {"domain", "event_token", "records"} or value["domain"] != SELECTION_DOMAIN or type(value["records"]) is not list:
        raise MalformedRecord("a snapshot carries exactly its closed field set under its domain")
    if any(type(row) is not dict or set(row) != {"id", "text"} for row in value["records"]):
        raise MalformedRecord("a snapshot record carries exactly id and text")
    snapshot = Snapshot(value["event_token"], tuple((row["id"], row["text"]) for row in value["records"]))
    if encode_snapshot(snapshot) != data:
        raise MalformedRecord("a snapshot is not its canonical encoding")
    return snapshot


@dataclass(frozen=True)
class PublishRequest:
    """Every identity-bearing input of one attempt, frozen at step 0 (spec §4.5)."""

    event_token: str
    view: CoordinationAddress
    destination: Destination
    epoch: str
    world_id: str
    pins: CorpusPins
    selection: str
    staging_world_id: str

    def __post_init__(self) -> None:
        _hex(self.event_token, _HEX32, "a request's event token")
        if type(self.view) is not CoordinationAddress or self.view.revision is None:
            raise MalformedRecord("a request names its view pinned to the resolved revision")
        if type(self.destination) is not Destination:
            raise MalformedRecord("a request's destination is a Destination")
        _hex(self.epoch, _HEX64, "a request's epoch")
        _hex(self.world_id, _HEX32, "a request's world id")
        if type(self.pins) is not CorpusPins:
            raise MalformedRecord("a request's pins are CorpusPins")
        _hex(self.selection, _HEX64, "a request's selection identity")
        if self.staging_world_id != staging_world_id_for(self.event_token):
            raise MalformedRecord("a request's staging world id is its token's")

    def projection(self) -> dict[str, object]:
        return {
            "domain": REQUEST_DOMAIN,
            "event_token": self.event_token,
            "view": str(self.view),
            "destination": self.destination.projection(),
            "epoch": self.epoch,
            "world_id": self.world_id,
            "pins": {"science_contract": self.pins.science_contract, "domains": dict(self.pins.domains)},
            "selection": self.selection,
            "staging_world_id": self.staging_world_id,
        }


_REQUEST_FIELDS = frozenset({"domain", "event_token", "view", "destination", "epoch", "world_id", "pins", "selection", "staging_world_id"})


def encode_request(request: PublishRequest) -> bytes:
    return v1.encode(request.projection())


def decode_request(data: bytes) -> PublishRequest:
    value = _decoded(data, "a request")
    if set(value) != _REQUEST_FIELDS or value["domain"] != REQUEST_DOMAIN:
        raise MalformedRecord("a request carries exactly its closed field set under its domain")
    pins = value["pins"]
    if type(pins) is not dict or set(pins) != {"science_contract", "domains"} or type(pins["domains"]) is not dict:
        raise MalformedRecord("a request's pins carry science_contract and a domains mapping")
    try:
        request = PublishRequest(
            event_token=value["event_token"],
            view=CoordinationAddress.parse(value["view"]),
            destination=Destination.from_projection(value["destination"]),
            epoch=value["epoch"],
            world_id=value["world_id"],
            pins=CorpusPins(pins["science_contract"], pins["domains"]),
            selection=value["selection"],
            staging_world_id=value["staging_world_id"],
        )
    except (TypeError, ValueError) as caught:
        raise MalformedRecord(f"a request field is malformed: {caught}") from caught
    if encode_request(request) != data:
        raise MalformedRecord("a request is not its canonical encoding")
    return request
