"""The registry log-head record, the exported head artifact, and the two acts
that write and read them.

Design: ``docs/superpowers/specs/2026-08-22-log-verification-design.md`` §3.1
(the registry log-head record, discriminated by ``record_kind: log-head``,
content-named by its digest under the minted domain ``science.log-head.v1``),
§3.2 (the standalone exported head artifact, canonical bytes via
``science.identity.v1`` encoding, minted under ``science.head-artifact.v1``,
produced by ``export_head_artifact``) and §3.3 (``anchor_heads``, the explicit
anchor act).

Both ruled forms share one subject grammar — ``corpus(corpus_id) |
world(world_id) | store(store_id)`` — though each admits a different subset.
The log-head record's subject is corpus-or-store only: a ``world`` subject is
not in that union at all (log design §5/L11). The head artifact's subject
spans all three, because a world artifact must carry ``world_id`` outside the
chain, where nothing else names it.

**The codecs are pure and the acts hold no capability of their own.** The two
act cores below reach the engine only through the ``LogSeam`` they are handed
— one head read and two locks — so this module imports neither ``atoms`` nor
``science.root``. It reaches ``science.world.registry`` in the module form
every edge of that cycle uses, and only at call time, because the registry
scan depends on this module's codec: a name-form import in either direction
would make one import order fail.

The small grammar helpers below (``_require_lower_hex``, ``_require_actor``,
``_closed_mapping``) are local restatements of ``registry.py``'s rather than
imports of them, and follow the same shape on purpose. The shape is what is
shared, not the refusal: ``registry.py``'s ``_closed_mapping`` raises
``ManifestMalformed`` where this one raises ``ValueError``, because a codec
refusal here is wrapped by whichever caller supplied the document.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, cast

import yaml
from nodes.core.write_plan import CreateOp

from science.errors import (
    AnchorSubjectUnknown,
    AnchorTargetUnresolvable,
    LogHeadCollision,
    WorldIdMismatch,
    WorldUninitialized,
)
from science.identity import v1
from science.world import registry
from science.world.verify import LogSeam

__all__ = [
    "HEAD_ARTIFACT_DOMAIN",
    "LOG_HEAD_DOMAIN",
    "WORLD_GENESIS_DOMAIN",
    "AnchorActOrigin",
    "BuildOrigin",
    "CorpusSubject",
    "HeadArtifact",
    "LogHeadOrigin",
    "LogHeadRecord",
    "StoreSubject",
    "Subject",
    "WorldSubject",
    "decode_head_artifact",
    "head_artifact_bytes",
    "log_head_digest",
    "log_head_projection",
    "log_head_record_bytes",
    "parse_log_head_record",
]

LOG_HEAD_DOMAIN = "science.log-head.v1"
HEAD_ARTIFACT_DOMAIN = "science.head-artifact.v1"

WORLD_GENESIS_DOMAIN = "science.world-root.v1"
"""The world chain's genesis domain, as the composition root mints it.

Restated rather than imported: the world package may not import
``science.root``, and a world export must bind its subject to the ``world_id``
the genesis payload carries. The two spellings are pinned equal by a test, so
the restatement cannot drift into a second definition."""

_LOWER_HEX = frozenset("0123456789abcdef")


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


def _closed_mapping(value: object, expected: set[str], location: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected or any(type(key) is not str for key in value):
        raise ValueError(f"{location} must have exactly {sorted(expected)}")
    return cast(dict[str, object], value)


# --- subjects (§3.1, §3.2) ----------------------------------------------------


@dataclass(frozen=True)
class CorpusSubject:
    corpus_id: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.corpus_id, 32, "corpus_id")


@dataclass(frozen=True)
class WorldSubject:
    world_id: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.world_id, 32, "world_id")


@dataclass(frozen=True)
class StoreSubject:
    store_id: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.store_id, 32, "store_id")


Subject: TypeAlias = CorpusSubject | WorldSubject | StoreSubject


# --- the log-head record's origin (§3.1) --------------------------------------


@dataclass(frozen=True)
class BuildOrigin:
    packaging_identity: str

    def __post_init__(self) -> None:
        _require_lower_hex(self.packaging_identity, 64, "packaging_identity")


@dataclass(frozen=True)
class AnchorActOrigin:
    actor: str

    def __post_init__(self) -> None:
        _require_actor(self.actor)


LogHeadOrigin: TypeAlias = BuildOrigin | AnchorActOrigin


# --- the registry log-head record (§3.1) --------------------------------------


@dataclass(frozen=True)
class LogHeadRecord:
    """The registry's log-head record: content-named by `log_head_digest`
    under `record_kind: log-head`. Records are immutable and unordered —
    "maximal anchor" is computed by chain ancestry, never record order.

    The store arm is decodable and constructible here, and nothing this slice
    ships reaches it: the anchor act's corpus-only signature makes a store
    unspellable there. A `world` subject is not in the union at all.
    """

    subject: CorpusSubject | StoreSubject
    genesis: str
    head: str
    origin: BuildOrigin | AnchorActOrigin

    def __post_init__(self) -> None:
        if type(self.subject) not in {CorpusSubject, StoreSubject}:
            raise TypeError("subject must be CorpusSubject or StoreSubject")
        _require_lower_hex(self.genesis, 64, "genesis")
        _require_lower_hex(self.head, 64, "head")
        if type(self.origin) not in {BuildOrigin, AnchorActOrigin}:
            raise TypeError("origin must be BuildOrigin or AnchorActOrigin")


# --- the exported head artifact (§3.2) ----------------------------------------


@dataclass(frozen=True)
class HeadArtifact:
    """The exported head artifact: a standalone file, canonical bytes via
    `science.identity.v1` encoding. Unlike the registry record, the subject
    spans all three kinds — the world arm carries `world_id` because the id
    must survive outside the chain, where nothing else names it."""

    subject: Subject
    genesis: str
    head: str

    def __post_init__(self) -> None:
        if type(self.subject) not in {CorpusSubject, WorldSubject, StoreSubject}:
            raise TypeError("subject must be CorpusSubject, WorldSubject, or StoreSubject")
        _require_lower_hex(self.genesis, 64, "genesis")
        _require_lower_hex(self.head, 64, "head")


# --- shared subject/origin projections and parsers ----------------------------

_LOG_HEAD_SUBJECT_KINDS = frozenset({"corpus", "store"})
_HEAD_ARTIFACT_SUBJECT_KINDS = frozenset({"corpus", "world", "store"})


def _subject_projection(subject: Subject) -> dict[str, str]:
    if isinstance(subject, CorpusSubject):
        return {"kind": "corpus", "corpus_id": subject.corpus_id}
    if isinstance(subject, WorldSubject):
        return {"kind": "world", "world_id": subject.world_id}
    if isinstance(subject, StoreSubject):
        return {"kind": "store", "store_id": subject.store_id}
    raise TypeError("subject must be CorpusSubject, WorldSubject, or StoreSubject")


def _parse_subject(value: object, *, kinds: frozenset[str]) -> Subject:
    if type(value) is not dict or type(value.get("kind")) is not str:
        raise ValueError("subject must be a closed mapping selected by kind")
    kind = value["kind"]
    if kind not in kinds:
        raise ValueError(f"subject kind {kind!r} is not permitted here")
    if kind == "corpus" and set(value) == {"kind", "corpus_id"}:
        return CorpusSubject(value["corpus_id"])
    if kind == "world" and set(value) == {"kind", "world_id"}:
        return WorldSubject(value["world_id"])
    if kind == "store" and set(value) == {"kind", "store_id"}:
        return StoreSubject(value["store_id"])
    raise ValueError(f"malformed subject for kind {kind!r}")


def _origin_projection(origin: BuildOrigin | AnchorActOrigin) -> dict[str, str]:
    if isinstance(origin, BuildOrigin):
        return {"kind": "build", "packaging_identity": origin.packaging_identity}
    if isinstance(origin, AnchorActOrigin):
        return {"kind": "anchor-act", "actor": origin.actor}
    raise TypeError("origin must be BuildOrigin or AnchorActOrigin")


def _parse_origin(value: object) -> BuildOrigin | AnchorActOrigin:
    if type(value) is not dict or type(value.get("kind")) is not str:
        raise ValueError("origin must be a closed mapping selected by kind")
    kind = value["kind"]
    if kind == "build" and set(value) == {"kind", "packaging_identity"}:
        return BuildOrigin(value["packaging_identity"])
    if kind == "anchor-act" and set(value) == {"kind", "actor"}:
        return AnchorActOrigin(value["actor"])
    raise ValueError(f"unknown or malformed log-head origin {kind!r}")


# --- the log-head record codec ------------------------------------------------


def log_head_projection(record: LogHeadRecord) -> dict[str, object]:
    return {
        "record_kind": "log-head",
        "subject": _subject_projection(record.subject),
        "genesis": record.genesis,
        "head": record.head,
        "origin": _origin_projection(record.origin),
    }


def log_head_digest(record: LogHeadRecord) -> str:
    return v1.digest(LOG_HEAD_DOMAIN, log_head_projection(record))


def log_head_record_bytes(record: LogHeadRecord) -> bytes:
    """One record's registry bytes: the canonical dump of its projection.

    The same deterministic encoding admission and status records are written
    with, because the registry scan reads all three with one loader and a
    log-head record filed under a second grammar would be a second registry.
    """
    return yaml.safe_dump(log_head_projection(record), sort_keys=True, allow_unicode=True).encode("utf-8")


def parse_log_head_record(value: object) -> LogHeadRecord:
    """The decode half of the log-head record codec: a decoded YAML mapping in,
    a validated `LogHeadRecord` out, or a `ValueError` refusal. Consumed by
    `science.world.registry`'s registry scan, which supplies the already
    `yaml.load`-ed document — this function does no byte-level parsing of its
    own, so the registry's digit-preserving loader protects `genesis`, `head`,
    `store_id`, and `packaging_identity` exactly as it protects `corpus_id`.
    """
    fields = _closed_mapping(value, {"record_kind", "subject", "genesis", "head", "origin"}, "log-head record")
    if fields["record_kind"] != "log-head":
        raise ValueError("log-head record record_kind must be 'log-head'")
    subject = _parse_subject(fields["subject"], kinds=_LOG_HEAD_SUBJECT_KINDS)
    genesis = _require_lower_hex(fields["genesis"], 64, "genesis")
    head = _require_lower_hex(fields["head"], 64, "head")
    origin = _parse_origin(fields["origin"])
    return LogHeadRecord(cast("CorpusSubject | StoreSubject", subject), genesis, head, origin)


# --- the head artifact codec ---------------------------------------------------


def _head_artifact_projection(artifact: HeadArtifact) -> dict[str, object]:
    return {
        "domain": HEAD_ARTIFACT_DOMAIN,
        "subject": _subject_projection(artifact.subject),
        "genesis": artifact.genesis,
        "head": artifact.head,
    }


def head_artifact_bytes(artifact: HeadArtifact) -> bytes:
    """The artifact's canonical bytes: `science.identity.v1`-encoded, carrying
    its own domain so the bytes are self-describing (there is no directory
    convention or sibling `record_kind` discriminant to lean on, unlike the
    registry record)."""
    return v1.encode(_head_artifact_projection(artifact))


def decode_head_artifact(data: bytes) -> HeadArtifact:
    """The inverse of `head_artifact_bytes`, refusing anything that is not
    itself the exact canonical encoding of the payload it decodes to — a
    tamper-evident export is only as good as a decoder that refuses bytes a
    permissive JSON parser would accept but `science.identity.v1` never
    emits."""
    if type(data) is not bytes:
        raise TypeError("data must be exact bytes")
    try:
        document = json.loads(data.decode("utf-8"))
    except Exception as caught:
        raise ValueError(f"head artifact is not valid canonical JSON: {caught}") from caught
    fields = _closed_mapping(document, {"domain", "subject", "genesis", "head"}, "head artifact")
    if fields["domain"] != HEAD_ARTIFACT_DOMAIN:
        raise ValueError(f"head artifact domain must be {HEAD_ARTIFACT_DOMAIN!r}")
    subject = _parse_subject(fields["subject"], kinds=_HEAD_ARTIFACT_SUBJECT_KINDS)
    genesis = _require_lower_hex(fields["genesis"], 64, "genesis")
    head = _require_lower_hex(fields["head"], 64, "head")
    artifact = HeadArtifact(subject, genesis, head)
    if head_artifact_bytes(artifact) != data:
        raise ValueError("head artifact is not the canonical encoding of its own payload")
    return artifact


# --- the two acts (§3.2, §3.3) ------------------------------------------------
#
# Both cores take the seam as a parameter and hold no capability of their own,
# and both resolve a corpus subject by the one rule below. `science.root` is
# the only constructor of a production seam, and its `anchor_heads` /
# `export_head_artifact` wrappers are the only public callers of these two.


def _resolve_carrier(config: registry.WorldConfig, view: registry.RegistryView, corpus_id: str) -> Path:
    """§3.3's resolution rule: one admitted id, exactly one configured carrier.

    The two refusals are distinct and ordered. An id this world never admitted
    is not a resolution failure at all — no set of roots would make it
    anchorable — so it is decided first, from the registry the caller already
    scanned. Zero carriers and two carriers are then the same failure and
    refuse alike: an act that picked whichever root sorted first would anchor a
    chain whose provenance depended on configuration order.

    Terminal status is deliberately not consulted. §3.3 rules that terminal
    corpora may be anchored, because anchoring immediately before retirement or
    departure cleanup is the archetypal use of the act.
    """
    if not any(record.corpus_id == corpus_id for record in view.admissions):
        raise AnchorSubjectUnknown(f"{corpus_id}: this world has not admitted the named corpus")
    roots = registry._carrier_roots(config, corpus_id)
    if len(roots) != 1:
        detail = ",".join(sorted(str(root) for root in roots)) or "none"
        raise AnchorTargetUnresolvable(
            f"{corpus_id}: exactly one configured carrier root is required; carriers={detail}"
        )
    return roots[0]


def _log_head_member(world_root: Path, record: LogHeadRecord) -> CreateOp | None:
    """§3.1's idempotency rule, as one create-or-nothing decision.

    `None` means the record already stands, byte for byte, and there is
    nothing to submit — the rules store's discipline verbatim, and the reason
    re-anchoring an unmoved head opens no transaction at all.
    """
    path = f"registry/{log_head_digest(record)}.yaml"
    content = log_head_record_bytes(record)
    target = Path(world_root) / path
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise LogHeadCollision(f"{target}: a content-addressed log-head record path is not a regular file")
    if target.exists():
        if target.read_bytes() != content:
            raise LogHeadCollision(f"{target}: a content-addressed log-head record path holds different bytes")
        return None
    return CreateOp(path, content)


def _anchor_heads(
    world: registry.World,
    corpus_ids: frozenset[str],
    *,
    actor: str,
    seam: LogSeam,
) -> tuple[LogHeadRecord, ...]:
    """§3.3: anchor each named corpus's present chain head, in one transaction.

    Under the world lock throughout, in sorted id order so that a world with
    two faults reports the one that is decided first rather than the one that
    happens to be met first. Per corpus: resolve the carrier by §3.3's rule,
    read that carrier's validated head through the seam — chain validation
    only, no registered-surface scan and no corpus-state identity — and mint
    the record. The plan is submitted once, at the end, so a refusal over the
    third named corpus leaves no record standing for the first two.

    **No `World` method is called under the lock (R12).** The seam's
    `world_lock` hands back the very non-reentrant lock `World.registry()`
    takes, so the registry is scanned here directly, exactly as an epoch
    build's preflight scans it.

    A `LogEvidenceRefused` from the head read propagates untranslated: it is a
    refusal to judge, not a judgment, and it sits outside every precedence.
    """
    _require_actor(actor)
    if type(corpus_ids) is not frozenset:
        raise TypeError("corpus_ids must be an exact frozenset")
    targets = sorted(_require_lower_hex(corpus_id, 32, "corpus_id") for corpus_id in corpus_ids)
    origin = AnchorActOrigin(actor)
    config = world.config
    with seam.world_lock(config.world_root):
        view = registry._scan_registry(config.world_root)
        world._state.registry = view
        records: list[LogHeadRecord] = []
        plan: list[CreateOp] = []
        for corpus_id in targets:
            carrier = _resolve_carrier(config, view, corpus_id)
            head = seam.read_head(carrier)
            record = LogHeadRecord(CorpusSubject(corpus_id), head.genesis_digest, head.tip, origin)
            records.append(record)
            member = _log_head_member(config.world_root, record)
            if member is not None:
                plan.append(member)
        if plan:
            world._executor_factory(config.world_root).execute(plan)
        return tuple(records)


def _require_world_genesis(world_root: Path, payload: bytes, world_id: str) -> None:
    """The world export's binding half: the genesis must be *this* world's.

    Two distinct refusals, because they are two different facts. A payload
    that is not a Science world genesis at all says the root was never
    initialized as one; a well-formed genesis naming another `world_id` says
    the subject and the chain disagree, which is exactly the mismatch that
    stops `World(W2)` being encoded over W1's chain.
    """
    try:
        document = json.loads(payload.decode("utf-8"))
    except Exception as caught:
        raise WorldUninitialized(
            f"{world_root}: the chain genesis payload is not a Science world genesis: {caught}"
        ) from caught
    if (
        type(document) is not dict
        or set(document) != {"domain", "world_id"}
        or document["domain"] != WORLD_GENESIS_DOMAIN
    ):
        raise WorldUninitialized(
            f"{world_root}: the chain genesis payload is not a {WORLD_GENESIS_DOMAIN} genesis"
        )
    if document["world_id"] != world_id:
        raise WorldIdMismatch(
            f"{world_root}: the chain genesis names world_id {document['world_id']!r}, not {world_id!r}"
        )


def _export_head_artifact(
    world: registry.World,
    subject: CorpusSubject | WorldSubject,
    *,
    seam: LogSeam,
) -> bytes:
    """§3.2: the canonical bytes of one subject's present head. Writes nothing.

    Export *is* the return of the value: storing the bytes with an external
    holder is the holder's job, and it is that holding — an epoch copy or an
    artifact reaching a holder outside the world root — that anchors the world
    chain, since no local act can (log design §5, L11). Hence no `actor`: the
    ruled artifact has no member to record one.

    **The subject binds, never decorates.** A world subject must agree with the
    configuration *and* with the genesis payload the head was read alongside; a
    corpus subject resolves under §3.3's rule, so an unknown id or an
    unresolvable carrier refuses exactly as the anchor act refuses.

    The world lock is held across the whole act and, for a corpus subject, the
    carrier's operation lock across the tip read — taken in the existing
    world→corpus order. It is taken as a *writer* rather than as a build's
    capture: an export is a short read, and a capture hold would turn a corpus
    write already waiting in the queue into a `BuildHold` refusal.
    """
    if type(subject) not in {CorpusSubject, WorldSubject}:
        raise TypeError("subject must be CorpusSubject or WorldSubject")
    config = world.config
    with seam.world_lock(config.world_root):
        if type(subject) is WorldSubject:
            if subject.world_id != config.world_id:
                raise WorldIdMismatch(
                    f"the exported subject names world_id {subject.world_id!r}, "
                    f"but this world is configured as {config.world_id!r}"
                )
            head = seam.read_head(config.world_root)
            _require_world_genesis(config.world_root, head.genesis_payload, subject.world_id)
            return head_artifact_bytes(HeadArtifact(subject, head.genesis_digest, head.tip))
        view = registry._scan_registry(config.world_root)
        world._state.registry = view
        carrier = _resolve_carrier(config, view, cast(CorpusSubject, subject).corpus_id)
        with seam.corpus_lock(carrier):
            head = seam.read_head(carrier)
            return head_artifact_bytes(HeadArtifact(subject, head.genesis_digest, head.tip))
