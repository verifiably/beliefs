"""Closed corpus manifests, independent of the corpus engine."""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, NoReturn, TypeAlias, cast

import yaml
from nodes.core.projection import to_canonical_json
from nodes.core.write_plan import CreateOp, WritePlanExecutor

from science.consulted import CorpusPins
from science.corpus import Finding, ReadView
from science.errors import (
    CorpusIdKnown,
    CorpusStateMalformed,
    ForkParentUnknown,
    ManifestMalformed,
    ManifestMissing,
    ProvenanceMismatch,
    RegistryMalformed,
    ReplicaAdmissionRequiresVerification,
    StatusTargetUnknown,
    StatusTerminal,
    WorldUninitialized,
)
from science.identity import v1
from science.world import anchors

__all__ = [
    "AdmissionProvenance",
    "AdmissionRecord",
    "CorpusManifest",
    "CorpusStatus",
    "ForkOf",
    "ForkedFrom",
    "Fresh",
    "RegistryView",
    "ReplicaOf",
    "StatusRecord",
    "World",
    "WorldConfig",
    "admission_digest",
    "admission_projection",
    "corpus_state_identity",
    "load_manifest",
    "manifest_bytes",
    "manifest_projection",
    "provenance_projection",
    "status_digest",
    "status_projection",
]

_NAMESPACE = re.compile(r"^[a-z][a-z0-9-]*$")
_LOWER_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ForkedFrom:
    corpus_id: str
    corpus_state: str


@dataclass(frozen=True)
class CorpusManifest:
    manifest_version: Literal[2]
    corpus_id: str
    profile: CorpusPins
    forked_from: ForkedFrom | None = None


@dataclass(frozen=True)
class Fresh:
    pass


@dataclass(frozen=True)
class ReplicaOf:
    parent_corpus_id: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.parent_corpus_id, 32, "parent_corpus_id")


@dataclass(frozen=True)
class ForkOf:
    parent_corpus_id: str
    parent_corpus_state: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.parent_corpus_id, 32, "parent_corpus_id")
        _require_lower_hex(self.parent_corpus_state, 64, "parent_corpus_state")


AdmissionProvenance: TypeAlias = Fresh | ReplicaOf | ForkOf


@dataclass(frozen=True)
class AdmissionRecord:
    manifest: CorpusManifest
    provenance: AdmissionProvenance
    actor: str

    def __post_init__(self) -> None:
        if type(self.manifest) is not CorpusManifest:
            raise TypeError("manifest must be a CorpusManifest")
        _require_lower_hex(self.manifest.corpus_id, 32, "corpus_id")
        if type(self.provenance) not in {Fresh, ReplicaOf, ForkOf}:
            raise TypeError("provenance must be Fresh, ReplicaOf, or ForkOf")
        _require_actor(self.actor)

    @property
    def corpus_id(self) -> str:
        return self.manifest.corpus_id


@dataclass(frozen=True)
class StatusRecord:
    corpus_id: str
    status: Literal["retired", "departed"]
    actor: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.corpus_id, 32, "corpus_id")
        if self.status not in {"retired", "departed"}:
            raise ValueError("status must be 'retired' or 'departed'")
        _require_actor(self.actor)


@dataclass(frozen=True)
class WorldConfig:
    world_root: Path
    world_id: str
    corpus_roots: tuple[Path, ...]

    def __post_init__(self) -> None:
        if type(self.corpus_roots) is not tuple:
            raise TypeError("corpus_roots must be an exact tuple")
        if (
            type(self.world_id) is not str
            or len(self.world_id) != 32
            or any(character not in _LOWER_HEX for character in self.world_id)
        ):
            raise ValueError("world_id must be 32 lowercase hexadecimal characters")
        object.__setattr__(self, "world_root", Path(self.world_root).resolve())
        object.__setattr__(self, "corpus_roots", tuple(Path(root).resolve() for root in self.corpus_roots))


@dataclass(frozen=True)
class RegistryView:
    admissions: tuple[AdmissionRecord, ...] = ()
    statuses: tuple[StatusRecord, ...] = ()
    log_heads: tuple[anchors.LogHeadRecord, ...] = ()


@dataclass(frozen=True)
class CorpusStatus:
    known: bool
    live: bool
    present: bool
    findings: tuple[Finding, ...]


@dataclass
class _WorldState:
    lock: threading.Lock
    registry: RegistryView


_WORLD_STATES: dict[str, _WorldState] = {}
_WORLD_STATES_LOCK = threading.Lock()


def _world_state_for(world_root: Path) -> _WorldState:
    with _WORLD_STATES_LOCK:
        return _WORLD_STATES.setdefault(
            str(Path(world_root).resolve()), _WorldState(threading.Lock(), RegistryView())
        )


def _world_lock_for(world_root: Path) -> threading.Lock:
    """One world root's lock, without opening a `World`.

    The lock-only lookup exists because verification locks a world it never
    opened: constructing a `World` needs a `WorldConfig`, an executor factory
    and a chain reader, none of which an audit has or should invent. The
    corpus registry cannot serve here either — `_ROOT_STATES` and
    `_WORLD_STATES` are separate maps over different roots — so this is the
    world's own entry point, handing back the identical object an opened
    `World` holds.
    """
    return _world_state_for(world_root).lock


def _require_lower_hex(value: object, length: int, location: str) -> str:
    if type(value) is not str or len(value) != length or any(character not in _LOWER_HEX for character in value):
        raise ValueError(f"{location} must be {length} lowercase hexadecimal characters")
    return value


def _require_actor(actor: object) -> str:
    if type(actor) is not str:
        raise TypeError("actor must be an exact string")
    try:
        v1.encode(actor)
    except Exception as caught:
        raise ValueError(f"actor is not encodable: {caught}") from caught
    return actor


class World:
    """One world root, its registry, and the two capabilities a build needs.

    `chain_head` is the whole of Science's access to the engine's chain: it is
    handed a root and answers `(genesis_digest, tip)`, having completed
    recovery first. Nothing engine-shaped crosses this boundary — no
    `ChainView`, no backend, no storage profile — which is what keeps
    `science.root` the one module that imports `atoms`.

    `corpus_executor_factory` is the factory the *corpus* write API is built
    with, and it is here because a coherent capture must take the same
    per-root operation lock a writer takes. `corpus._root_state_for` keeps one
    state per root and refuses a second factory for a root it already holds, so
    a build reaching for a corpus with the world's own factory would be a build
    that could not run in a process that had also opened that corpus. It is
    never used to write: a capture reads.
    """

    def __init__(
        self,
        config: WorldConfig,
        executor_factory: Callable[[Path], WritePlanExecutor],
        *,
        chain_head: Callable[[Path], tuple[str, str]],
        corpus_executor_factory: Callable[[Path], WritePlanExecutor],
    ) -> None:
        self.config = config
        self._executor_factory = executor_factory
        self._chain_head = chain_head
        self._corpus_executor_factory = corpus_executor_factory
        self._state = _world_state_for(config.world_root)

    def registry(self) -> RegistryView:
        with self._state.lock:
            self._state.registry = _scan_registry(self.config.world_root)
            return self._state.registry

    def status(self, corpus_id: str) -> CorpusStatus:
        with self._state.lock:
            self._state.registry = _scan_registry(self.config.world_root)
            _require_lower_hex(corpus_id, 32, "corpus_id")
            return _reduce_status(self.config, self._state.registry, corpus_id)

    def admit(
        self,
        corpus_root: Path,
        *,
        provenance: AdmissionProvenance,
        actor: str,
    ) -> AdmissionRecord:
        """Admit a corpus root this world holds no verdict about.

        `ReplicaOf` is refused here (log-verification design §6.2): a replica's
        chain traveled, and admitting it is the one admission that asks a
        question about evidence. This call inspects nothing, so it has no
        answer to report — `science.root.admit_arrival` is the route that does,
        and it commits through the very core below.
        """
        if type(provenance) is ReplicaOf:
            raise ReplicaAdmissionRequiresVerification(
                f"{Path(corpus_root)}: a replica is admitted through admit_arrival, which verifies the chain "
                "it traveled with and reports the verdict beside the record"
            )
        with self._state.lock:
            return _locked_admit(
                self._state,
                self.config.world_root,
                self._executor_factory,
                lambda: load_manifest(corpus_root),
                provenance,
                actor,
            )

    def retire(self, corpus_id: str, *, actor: str) -> StatusRecord:
        return self._terminal(corpus_id, "retired", actor)

    def depart(self, corpus_id: str, *, actor: str) -> StatusRecord:
        return self._terminal(corpus_id, "departed", actor)

    def _terminal(self, corpus_id: str, status: Literal["retired", "departed"], actor: str) -> StatusRecord:
        with self._state.lock:
            self._state.registry = _scan_registry(self.config.world_root)
            if not any(record.corpus_id == corpus_id for record in self._state.registry.admissions):
                raise StatusTargetUnknown(f"corpus_id {corpus_id!r} is not admitted")
            candidate = StatusRecord(corpus_id, status, actor)
            digest = status_digest(candidate)
            for record in self._state.registry.statuses:
                if status_digest(record) == digest:
                    return record
            if any(record.corpus_id == corpus_id for record in self._state.registry.statuses):
                raise StatusTerminal(f"corpus_id {corpus_id!r} already has terminal status")
            self._executor_factory(self.config.world_root).execute(
                [CreateOp(f"registry/{digest}.yaml", _record_bytes(status_projection(candidate)))]
            )
            self._state.registry = _scan_registry(self.config.world_root)
            return next(record for record in self._state.registry.statuses if status_digest(record) == digest)


def _locked_admit(
    state: _WorldState,
    world_root: Path,
    executor_factory: Callable[[Path], WritePlanExecutor],
    manifest_of: Callable[[], CorpusManifest],
    provenance: AdmissionProvenance,
    actor: str,
) -> AdmissionRecord:
    """The whole of admission, assuming `state.lock` is already held.

    **One core, two callers** (log-verification design §6.2): `World.admit` and
    the verified arrival both commit through this and there is no second
    registration path, which is what makes admission identity byte-identical
    across the two routes. Nothing here is amended by verification — the
    observer bound is never a member of an `AdmissionRecord`.

    **The manifest arrives as a thunk**, and the two reasons are one thing said
    twice. The world's own registry is scanned *before* the candidate's manifest
    is read, so a malformed registry is reported ahead of a malformed manifest —
    the world's state is judged before the arriving corpus's claim, and that
    order is a claim of its own. And the verified arrival has already read that
    manifest, under the arriving root's lock and before its capture; passing it
    in rather than re-reading it here is what keeps the record's manifest and
    the judged manifest the same read.

    It is `_locked_*` for the reason every helper in this module is: the world
    lock is not reentrant, and the arrival already holds it when it arrives
    here — so this takes no lock and calls no `World` method (R12).
    """
    state.registry = _scan_registry(world_root)
    manifest = manifest_of()
    _validate_provenance(manifest, provenance)
    candidate = AdmissionRecord(manifest, provenance, actor)
    digest = admission_digest(candidate)
    for record in state.registry.admissions:
        if admission_digest(record) == digest:
            return record
    if any(record.corpus_id == candidate.corpus_id for record in state.registry.admissions):
        raise CorpusIdKnown(f"corpus_id {candidate.corpus_id!r} is already admitted")
    if isinstance(provenance, ForkOf) and not any(
        record.corpus_id == provenance.parent_corpus_id for record in state.registry.admissions
    ):
        raise ForkParentUnknown(f"fork parent {provenance.parent_corpus_id!r} is not admitted")
    executor_factory(world_root).execute(
        [CreateOp(f"registry/{digest}.yaml", _record_bytes(admission_projection(candidate)))]
    )
    state.registry = _scan_registry(world_root)
    return next(record for record in state.registry.admissions if admission_digest(record) == digest)


@contextmanager
def _locked_barrier(world: World) -> Iterator[Path]:
    """The one world-lock acquisition and the recovery barrier, in that order.

    Every act over ``epochs/`` — opening one, following ``current``, resolving
    an address, publishing, deleting — begins the same way: take
    `_WorldState.lock`, then hand the world root to the injected chain callback
    so recovery of any interrupted transaction completes *inside* the critical
    section. The order is the whole point (§8.1). Taking the lock second would
    let a reader cross a barrier that a publication then invalidated; crossing
    the barrier second, but outside the lock, would let two acts recover at
    once.

    The lock is not reentrant, so everything the body calls must be a
    `_locked_*` helper that assumes the hold rather than taking it again. The
    world root is yielded because every one of those helpers is keyed by it and
    reading it twice from the config is how the two could drift apart.
    """
    with world._state.lock:
        world_root = world.config.world_root
        world._chain_head(world_root)
        yield world_root


class _ManifestLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _ManifestLoader, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = (
            value_node.value
            if key in {"corpus_id", "corpus_state", "world_id", "store_id", "genesis", "head", "packaging_identity"}
            and isinstance(value_node, yaml.ScalarNode)
            and value_node.tag == "tag:yaml.org,2002:int"
            else loader.construct_object(value_node, deep=deep)
        )
    return mapping


_ManifestLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _world_mirror_bytes(world_id: str) -> bytes:
    return f"world_id: {world_id}\n".encode()


def _load_world_mirror(root: Path) -> str:
    path = Path(root) / "world.yaml"
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_ManifestLoader)
        if type(document) is not dict or set(document) != {"world_id"} or type(document["world_id"]) is not str:
            raise ValueError("world mirror must have exactly world_id")
        return _lower_hex(document["world_id"], 32, "world_id")
    except Exception as caught:
        raise WorldUninitialized(f"{path}: missing or malformed world mirror: {caught}") from caught


def _malformed(message: str) -> NoReturn:
    raise ManifestMalformed(message)


def _closed_mapping(value: object, expected: set[str], location: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected or any(type(key) is not str for key in value):
        _malformed(f"{location} must have exactly {sorted(expected)}")
    return cast(dict[str, object], value)


def _lower_hex(value: object, length: int, location: str) -> str:
    if type(value) is not str or len(value) != length or any(character not in _LOWER_HEX for character in value):
        _malformed(f"{location} must be {length} lowercase hexadecimal characters")
    return value


def _identity(value: object, namespace: str, location: str) -> str:
    if type(value) is not str:
        _malformed(f"{location} must be an identity string")
    prefix, separator, digest = value.partition(":")
    if separator != ":" or prefix != namespace or not _NAMESPACE.fullmatch(prefix):
        _malformed(f"{location} must be a {namespace!r} identity")
    _lower_hex(digest, 64, location)
    return value


def _profile(value: object) -> CorpusPins:
    profile = _closed_mapping(value, {"science_contract", "domains"}, "manifest profile")
    science_contract = _identity(profile["science_contract"], "science", "manifest profile science_contract")
    domains = profile["domains"]
    if type(domains) is not dict:
        _malformed("manifest profile domains must be a mapping")
    checked_domains: dict[str, str] = {}
    for namespace, identity in cast(dict[object, object], domains).items():
        if type(namespace) is not str or not _NAMESPACE.fullmatch(namespace) or namespace == "science":
            _malformed("manifest profile domain namespaces must be non-science namespaces")
        checked_domains[namespace] = _identity(identity, namespace, f"manifest profile domain {namespace!r}")
    try:
        return CorpusPins(science_contract=science_contract, domains=checked_domains)
    except Exception as caught:
        raise ManifestMalformed(f"manifest profile is invalid: {caught}") from caught


def _parse_manifest(value: object) -> CorpusManifest:
    fields = {"manifest_version", "corpus_id", "profile"}
    if type(value) is dict and "forked_from" in value:
        fields.add("forked_from")
    document = _closed_mapping(value, fields, "manifest")
    if type(document["manifest_version"]) is not int or document["manifest_version"] != 2:
        _malformed("manifest_version must be the exact integer 2")
    corpus_id = _lower_hex(document["corpus_id"], 32, "corpus_id")
    profile = _profile(document["profile"])
    forked_from = None
    if "forked_from" in document:
        fork = _closed_mapping(document["forked_from"], {"corpus_id", "corpus_state"}, "manifest forked_from")
        forked_from = ForkedFrom(
            corpus_id=_lower_hex(fork["corpus_id"], 32, "forked_from corpus_id"),
            corpus_state=_lower_hex(fork["corpus_state"], 64, "forked_from corpus_state"),
        )
    return CorpusManifest(manifest_version=2, corpus_id=corpus_id, profile=profile, forked_from=forked_from)


def load_manifest(root: Path) -> CorpusManifest:
    """Load the exact closed manifest at a corpus root."""
    path = Path(root) / "corpus.yaml"
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_ManifestLoader)
        return _parse_manifest(document)
    except FileNotFoundError as caught:
        raise ManifestMissing(f"{path}: manifest is missing") from caught
    except ManifestMalformed:
        raise
    except Exception as caught:
        raise ManifestMalformed(f"{path}: malformed manifest: {caught}") from caught


def manifest_projection(manifest: CorpusManifest) -> dict[str, object]:
    projection: dict[str, object] = {
        "manifest_version": manifest.manifest_version,
        "corpus_id": manifest.corpus_id,
        "profile": {
            "science_contract": manifest.profile.science_contract,
            "domains": dict(sorted(manifest.profile.domains.items())),
        },
    }
    if manifest.forked_from is not None:
        projection["forked_from"] = {
            "corpus_id": manifest.forked_from.corpus_id,
            "corpus_state": manifest.forked_from.corpus_state,
        }
    return projection


def manifest_bytes(manifest: CorpusManifest) -> bytes:
    return yaml.safe_dump(manifest_projection(manifest), sort_keys=True, allow_unicode=True).encode("utf-8")


def provenance_projection(provenance: AdmissionProvenance) -> dict[str, str]:
    if isinstance(provenance, Fresh):
        return {"kind": "fresh"}
    if isinstance(provenance, ReplicaOf):
        return {"kind": "replica-of", "parent_corpus_id": provenance.parent_corpus_id}
    if isinstance(provenance, ForkOf):
        return {
            "kind": "fork-of",
            "parent_corpus_id": provenance.parent_corpus_id,
            "parent_corpus_state": provenance.parent_corpus_state,
        }
    raise TypeError("provenance must be Fresh, ReplicaOf, or ForkOf")


def admission_projection(record: AdmissionRecord) -> dict[str, object]:
    return {
        "record_kind": "admission",
        "corpus_id": record.corpus_id,
        "manifest": manifest_projection(record.manifest),
        "provenance": provenance_projection(record.provenance),
        "actor": record.actor,
    }


def admission_digest(record: AdmissionRecord) -> str:
    return v1.digest("science.world-admission.v1", admission_projection(record))


def status_projection(record: StatusRecord) -> dict[str, object]:
    return {
        "record_kind": "status",
        "corpus_id": record.corpus_id,
        "status": record.status,
        "actor": record.actor,
    }


def status_digest(record: StatusRecord) -> str:
    return v1.digest("science.world-status.v1", status_projection(record))


def _record_bytes(projection: dict[str, object]) -> bytes:
    return yaml.safe_dump(projection, sort_keys=True, allow_unicode=True).encode("utf-8")


def _validate_provenance(manifest: CorpusManifest, provenance: AdmissionProvenance) -> None:
    if isinstance(provenance, Fresh):
        matches = manifest.forked_from is None
    elif isinstance(provenance, ReplicaOf):
        matches = manifest.forked_from is None and provenance.parent_corpus_id == manifest.corpus_id
    elif isinstance(provenance, ForkOf):
        matches = manifest.forked_from == ForkedFrom(provenance.parent_corpus_id, provenance.parent_corpus_state)
    else:
        raise TypeError("provenance must be Fresh, ReplicaOf, or ForkOf")
    if not matches:
        raise ProvenanceMismatch("admission provenance does not match the corpus manifest")


def _parse_provenance(value: object) -> AdmissionProvenance:
    if type(value) is not dict or type(value.get("kind")) is not str:
        raise ValueError("admission provenance must be a closed mapping")
    kind = value["kind"]
    if kind == "fresh" and set(value) == {"kind"}:
        return Fresh()
    if kind == "replica-of" and set(value) == {"kind", "parent_corpus_id"}:
        return ReplicaOf(value["parent_corpus_id"])
    if kind == "fork-of" and set(value) == {"kind", "parent_corpus_id", "parent_corpus_state"}:
        return ForkOf(value["parent_corpus_id"], value["parent_corpus_state"])
    raise ValueError(f"unknown or malformed admission provenance {kind!r}")


def _parse_registry_record(value: object) -> AdmissionRecord | StatusRecord | anchors.LogHeadRecord:
    if type(value) is not dict or type(value.get("record_kind")) is not str:
        raise ValueError("registry record must be a closed mapping selected by record_kind")
    if value["record_kind"] == "admission":
        expected = {"record_kind", "corpus_id", "manifest", "provenance", "actor"}
        if set(value) != expected:
            raise ValueError(f"admission record must have exactly {sorted(expected)}")
        manifest = _parse_manifest(value["manifest"])
        corpus_id = _require_lower_hex(value["corpus_id"], 32, "corpus_id")
        if corpus_id != manifest.corpus_id:
            raise ValueError("admission corpus_id must match its manifest")
        provenance = _parse_provenance(value["provenance"])
        _validate_provenance(manifest, provenance)
        return AdmissionRecord(manifest, provenance, value["actor"])
    if value["record_kind"] == "status":
        expected = {"record_kind", "corpus_id", "status", "actor"}
        if set(value) != expected:
            raise ValueError(f"status record must have exactly {sorted(expected)}")
        return StatusRecord(value["corpus_id"], value["status"], value["actor"])
    if value["record_kind"] == "log-head":
        return anchors.parse_log_head_record(value)
    raise ValueError(f"unknown registry record_kind {value['record_kind']!r}")


def _scan_registry(root: Path) -> RegistryView:
    registry = Path(root) / "registry"
    if not registry.exists() and not registry.is_symlink():
        return RegistryView()
    try:
        if registry.is_symlink() or not registry.is_dir():
            raise ValueError("registry must be a regular directory")
        admissions: list[AdmissionRecord] = []
        statuses: list[StatusRecord] = []
        log_heads: list[anchors.LogHeadRecord] = []
        for path in registry.iterdir():
            if path.is_symlink() or not path.is_file() or path.suffix != ".yaml":
                raise ValueError(f"{path.name!r} is not a regular *.yaml registry member")
            document = yaml.load(path.read_text(encoding="utf-8"), Loader=_ManifestLoader)
            record = _parse_registry_record(document)
            if isinstance(record, AdmissionRecord):
                digest = admission_digest(record)
            elif isinstance(record, StatusRecord):
                digest = status_digest(record)
            else:
                digest = anchors.log_head_digest(record)
            if path.name != f"{digest}.yaml":
                raise ValueError(f"{path.name!r} is not the record's content name")
            if isinstance(record, AdmissionRecord):
                admissions.append(record)
            elif isinstance(record, StatusRecord):
                statuses.append(record)
            else:
                log_heads.append(record)
        return RegistryView(
            tuple(sorted(admissions, key=admission_digest)),
            tuple(sorted(statuses, key=status_digest)),
            tuple(sorted(log_heads, key=anchors.log_head_digest)),
        )
    except Exception as caught:
        raise RegistryMalformed(f"{registry}: malformed registry: {caught}") from caught


def _carrier_roots(config: WorldConfig, corpus_id: str) -> tuple[Path, ...]:
    """Every configured root whose manifest presently claims `corpus_id`.

    One authority for "which bytes are this corpus", read by the status
    reduction and by a build's preflight alike. A root configured twice is one
    carrier; a root with no manifest is not a carrier, because a directory that
    has not yet adopted one has made no claim. A *malformed* manifest is
    neither, and refuses: a root that claims something unreadable is a
    configuration fault, not an absence.
    """
    carriers: list[Path] = []
    for root in dict.fromkeys(path.resolve() for path in config.corpus_roots):
        try:
            if load_manifest(root).corpus_id == corpus_id:
                carriers.append(root)
        except ManifestMissing:
            continue
    return tuple(carriers)


def _reduce_status(config: WorldConfig, view: RegistryView, corpus_id: str) -> CorpusStatus:
    known = any(record.corpus_id == corpus_id for record in view.admissions)
    live = known and not any(record.corpus_id == corpus_id for record in view.statuses)
    carriers = _carrier_roots(config, corpus_id)
    findings: tuple[Finding, ...] = ()
    if len(carriers) > 1:
        detail = "carriers=" + ",".join(sorted(str(root) for root in carriers))
        findings = (
            Finding(
                severity="error",
                code="duplicate-carrier",
                ref=corpus_id,
                detail=detail,
                message="multiple configured roots carry this corpus id",
            ),
        )
    return CorpusStatus(known, live, len(carriers) == 1, findings)


def _live_corpus_ids(view: RegistryView) -> tuple[str, ...]:
    """This world's live span: every admitted `corpus_id` with no terminal
    status, sorted and distinct.

    The registry's reduction and nothing else. A `corpus_id` this world has
    been *configured* with a carrier root for is not in the span — a directory
    on disk is a claim, and §2's admission is what grants one — and a corpus
    that has been retired or departed has left it, which is exactly the fact
    that makes an epoch built over a wider coverage keep answering.

    `_reduce_status` answers the same question one `corpus_id` at a time and
    reads the filesystem to do it, because it also reports presence. This does
    not touch the filesystem at all: a span is a statement about the registry.
    """
    terminal = {record.corpus_id for record in view.statuses}
    return tuple(sorted({record.corpus_id for record in view.admissions} - terminal))


def _lift_json(value: object) -> object:
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["boolean", value]
    if isinstance(value, Decimal):
        return ["number", value]
    if type(value) is str:
        return ["string", value]
    if type(value) is list:
        return ["array", [_lift_json(member) for member in value]]
    if type(value) is dict:
        lifted: dict[str, object] = {}
        for key, member in value.items():
            if type(key) is not str:
                raise TypeError(f"JSON object key {key!r} is not a string")
            lifted[key] = _lift_json(member)
        return ["object", lifted]
    raise TypeError(f"{type(value).__name__} is not a JSON value")


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


def corpus_state_identity(corpus_root: Path) -> str:
    manifest = load_manifest(corpus_root)
    members: list[dict[str, str]] = []
    try:
        view = ReadView.opened_at(corpus_root)
        for node in view.iter_stored():
            projection_text = to_canonical_json(node)
            value = json.loads(
                projection_text,
                parse_int=Decimal,
                parse_float=Decimal,
                parse_constant=_reject_json_constant,
            )
            node_identity = v1.digest("science.node-content.v1", _lift_json(value))
            members.append({"uid": node.uid, "content_identity": node_identity})
    except Exception as caught:
        raise CorpusStateMalformed(f"{corpus_root}: malformed corpus state: {caught}") from caught
    projection = {
        "manifest": manifest_projection(manifest),
        "nodes": sorted(members, key=lambda member: member["uid"]),
    }
    return v1.digest("science.corpus-state.v1", projection)
