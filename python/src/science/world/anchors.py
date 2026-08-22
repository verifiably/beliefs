"""The registry log-head record and the exported head artifact — pure codecs.

Design: ``docs/superpowers/specs/2026-08-22-log-verification-design.md`` §3.1
(the registry log-head record, discriminated by ``record_kind: log-head``,
content-named by its digest under the minted domain ``science.log-head.v1``)
and §3.2 (the standalone exported head artifact, canonical bytes via
``science.identity.v1`` encoding, minted under ``science.head-artifact.v1``).

Both ruled forms share one subject grammar — ``corpus(corpus_id) |
world(world_id) | store(store_id)`` — though each admits a different subset.
The log-head record's subject is corpus-or-store only: a ``world`` subject is
not in that union at all (log design §5/L11). The head artifact's subject
spans all three, because a world artifact must carry ``world_id`` outside the
chain, where nothing else names it.

This module is pure: it mints its two domains and decides nothing about when
to write them. It imports neither ``atoms`` nor ``science.root``, and — so
that ``science.world.registry`` can depend on it for the registry scan without
a import cycle — it does not import ``science.world.registry`` either. The
small grammar helpers below (``_require_lower_hex``, ``_closed_mapping``) are
therefore local restatements of ``registry.py``'s, not imports of them; they
follow the same shape on purpose.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeAlias, cast

from science.identity import v1

__all__ = [
    "HEAD_ARTIFACT_DOMAIN",
    "LOG_HEAD_DOMAIN",
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
    "parse_log_head_record",
]

LOG_HEAD_DOMAIN = "science.log-head.v1"
HEAD_ARTIFACT_DOMAIN = "science.head-artifact.v1"

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
