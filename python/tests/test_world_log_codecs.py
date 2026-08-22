from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fixtures_cut6 import PINS
from nodes.core.write_plan import DefaultExecutor

import science.world.registry as world_module
from science.errors import MalformedDomain, RegistryMalformed
from science.identity import v1
from science.world import anchors

# --- shared fixtures -----------------------------------------------------


def unread_chain(root: Path) -> tuple[str, str]:
    raise AssertionError(f"{root}: this test builds no epoch and reads no chain")


def make_world(tmp_path: Path) -> world_module.World:
    return world_module.World(
        world_module.WorldConfig(tmp_path / "world", "f" * 32, ()),
        DefaultExecutor,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
    )


CORPUS_ID = "1" * 32
STORE_ID = "2" * 32
WORLD_ID = "f" * 32
GENESIS = "3" * 64
HEAD = "4" * 64
PACKAGING_IDENTITY = "5" * 64

# a genesis/head whose digits are all-numeric, so a YAML loader that resolves
# bare-digit scalars to int (rather than preserving them as text) would
# silently corrupt this value instead of raising.
ALL_DIGIT_HEX = "0" * 64


def build_record(
    subject: anchors.CorpusSubject | anchors.StoreSubject | None = None,
    *,
    genesis: str = GENESIS,
    head: str = HEAD,
    origin: anchors.BuildOrigin | anchors.AnchorActOrigin | None = None,
) -> anchors.LogHeadRecord:
    return anchors.LogHeadRecord(
        subject if subject is not None else anchors.CorpusSubject(CORPUS_ID),
        genesis,
        head,
        origin if origin is not None else anchors.BuildOrigin(PACKAGING_IDENTITY),
    )


def write_raw_record(root: Path, record: anchors.LogHeadRecord) -> None:
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    digest = anchors.log_head_digest(record)
    (registry / f"{digest}.yaml").write_text(
        yaml.safe_dump(anchors.log_head_projection(record), sort_keys=True),
        encoding="utf-8",
    )


# --- LogHeadRecord: projection and digest ---------------------------------


def test_log_head_projection_is_exact():
    record = build_record()
    assert anchors.log_head_projection(record) == {
        "record_kind": "log-head",
        "subject": {"kind": "corpus", "corpus_id": CORPUS_ID},
        "genesis": GENESIS,
        "head": HEAD,
        "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
    }


def test_log_head_digest_matches_a_hand_computed_projection():
    record = build_record()
    expected = v1.digest(
        "science.log-head.v1",
        {
            "record_kind": "log-head",
            "subject": {"kind": "corpus", "corpus_id": CORPUS_ID},
            "genesis": GENESIS,
            "head": HEAD,
            "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
        },
    )
    assert anchors.log_head_digest(record) == expected


def test_log_head_digest_is_domain_separated_from_admission_and_status():
    record = build_record()
    assert anchors.LOG_HEAD_DOMAIN == "science.log-head.v1"
    # sanity: the digest domain check itself refuses a foreign domain.
    with pytest.raises(MalformedDomain):
        v1.digest("not-a-domain", anchors.log_head_projection(record))


# --- LogHeadRecord: YAML round-trip, byte stability -----------------------


def test_log_head_record_yaml_round_trip_is_byte_stable():
    record = build_record(origin=anchors.AnchorActOrigin("alice"))
    projection = anchors.log_head_projection(record)
    first_bytes = yaml.safe_dump(projection, sort_keys=True).encode("utf-8")
    second_bytes = yaml.safe_dump(anchors.log_head_projection(record), sort_keys=True).encode("utf-8")
    assert first_bytes == second_bytes

    decoded = yaml.safe_load(first_bytes)
    parsed = anchors.parse_log_head_record(decoded)
    assert parsed == record
    assert anchors.log_head_projection(parsed) == projection


def test_log_head_record_store_arm_round_trips():
    record = build_record(subject=anchors.StoreSubject(STORE_ID))
    projection = anchors.log_head_projection(record)
    assert projection["subject"] == {"kind": "store", "store_id": STORE_ID}
    parsed = anchors.parse_log_head_record(projection)
    assert parsed == record
    assert parsed.subject == anchors.StoreSubject(STORE_ID)


def test_log_head_record_survives_all_digit_hex_fields_through_the_registry_loader(tmp_path):
    record = build_record(
        genesis=ALL_DIGIT_HEX,
        head=ALL_DIGIT_HEX,
        subject=anchors.StoreSubject(ALL_DIGIT_HEX[:32]),
        origin=anchors.BuildOrigin(ALL_DIGIT_HEX),
    )
    write_raw_record(tmp_path / "world", record)
    instance = make_world(tmp_path)
    view = instance.registry()
    assert view.log_heads == (record,)


# --- LogHeadRecord: world subject and other malformed inputs are refused --


def test_world_subject_is_rejected_by_the_record_codec():
    with pytest.raises(TypeError):
        anchors.LogHeadRecord(
            anchors.WorldSubject(WORLD_ID),  # type: ignore[arg-type]
            GENESIS,
            HEAD,
            anchors.BuildOrigin(PACKAGING_IDENTITY),
        )

    with pytest.raises(ValueError):
        anchors.parse_log_head_record(
            {
                "record_kind": "log-head",
                "subject": {"kind": "world", "world_id": WORLD_ID},
                "genesis": GENESIS,
                "head": HEAD,
                "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
            }
        )


@pytest.mark.parametrize(
    "construct",
    (
        lambda: anchors.CorpusSubject("x"),
        lambda: anchors.StoreSubject("x"),
        lambda: anchors.BuildOrigin("x"),
        lambda: anchors.AnchorActOrigin(True),  # type: ignore[arg-type]
        lambda: anchors.AnchorActOrigin("\ud800"),
        lambda: anchors.LogHeadRecord(anchors.CorpusSubject(CORPUS_ID), "x", HEAD, anchors.BuildOrigin(PACKAGING_IDENTITY)),
        lambda: anchors.LogHeadRecord(anchors.CorpusSubject(CORPUS_ID), GENESIS, "x", anchors.BuildOrigin(PACKAGING_IDENTITY)),
    ),
)
def test_log_head_values_refuse_malformed_fields(construct):
    with pytest.raises((TypeError, ValueError)):
        construct()


@pytest.mark.parametrize(
    "document",
    (
        "not-a-mapping",
        {"record_kind": "log-head"},
        {"record_kind": "status", "subject": {}, "genesis": GENESIS, "head": HEAD, "origin": {}},
        {
            "record_kind": "log-head",
            "subject": {"kind": "corpus", "corpus_id": "x"},
            "genesis": GENESIS,
            "head": HEAD,
            "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
        },
        {
            "record_kind": "log-head",
            "subject": {"kind": "corpus", "corpus_id": CORPUS_ID},
            "genesis": "x",
            "head": HEAD,
            "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
        },
        {
            "record_kind": "log-head",
            "subject": {"kind": "corpus", "corpus_id": CORPUS_ID},
            "genesis": GENESIS,
            "head": HEAD,
            "origin": {"kind": "nonsense"},
        },
        {
            "record_kind": "log-head",
            "subject": {"kind": "corpus", "corpus_id": CORPUS_ID, "extra": "y"},
            "genesis": GENESIS,
            "head": HEAD,
            "origin": {"kind": "build", "packaging_identity": PACKAGING_IDENTITY},
        },
    ),
)
def test_parse_log_head_record_refuses_malformed_documents(document):
    with pytest.raises(ValueError):
        anchors.parse_log_head_record(document)


# --- HeadArtifact: bytes and decode ----------------------------------------


def test_head_artifact_bytes_are_the_hand_computed_canonical_encoding():
    artifact = anchors.HeadArtifact(anchors.CorpusSubject(CORPUS_ID), GENESIS, HEAD)
    expected = v1.encode(
        {
            "domain": "science.head-artifact.v1",
            "subject": {"kind": "corpus", "corpus_id": CORPUS_ID},
            "genesis": GENESIS,
            "head": HEAD,
        }
    )
    assert anchors.head_artifact_bytes(artifact) == expected


def test_head_artifact_encode_decode_round_trip_is_byte_stable():
    artifact = anchors.HeadArtifact(anchors.WorldSubject(WORLD_ID), GENESIS, HEAD)
    first_bytes = anchors.head_artifact_bytes(artifact)
    second_bytes = anchors.head_artifact_bytes(anchors.decode_head_artifact(first_bytes))
    assert first_bytes == second_bytes
    assert anchors.decode_head_artifact(first_bytes) == artifact


def test_head_artifact_store_arm_round_trips():
    artifact = anchors.HeadArtifact(anchors.StoreSubject(STORE_ID), GENESIS, HEAD)
    data = anchors.head_artifact_bytes(artifact)
    decoded = anchors.decode_head_artifact(data)
    assert decoded == artifact
    assert decoded.subject == anchors.StoreSubject(STORE_ID)


def test_head_artifact_accepts_world_subject_unlike_the_record_codec():
    artifact = anchors.HeadArtifact(anchors.WorldSubject(WORLD_ID), GENESIS, HEAD)
    decoded = anchors.decode_head_artifact(anchors.head_artifact_bytes(artifact))
    assert decoded.subject == anchors.WorldSubject(WORLD_ID)


@pytest.mark.parametrize(
    "data",
    (
        b"not json at all",
        b'{"domain": "science.head-artifact.v1"}',
        b'{"domain": "science.head-artifact.v1", "subject": {"kind": "corpus", "corpus_id": "'
        + b"1" * 32
        + b'"}, "genesis": "'
        + b"3" * 64
        + b'", "head": "x"}',
        b'{"domain": "not-the-right-domain", "subject": {"kind": "corpus", "corpus_id": "'
        + b"1" * 32
        + b'"}, "genesis": "'
        + b"3" * 64
        + b'", "head": "'
        + b"4" * 64
        + b'"}',
        # decodable JSON, but not canonical (extra whitespace) — refused as
        # not-the-canonical-encoding, never silently accepted.
        b'{"domain": "science.head-artifact.v1", "subject": {"kind": "corpus", "corpus_id": "'
        + b"1" * 32
        + b'"}, "genesis": "'
        + b"3" * 64
        + b'", "head": "'
        + b"4" * 64
        + b'" }',
    ),
)
def test_decode_head_artifact_refuses_malformed_bytes(data):
    with pytest.raises(ValueError):
        anchors.decode_head_artifact(data)


def test_decode_head_artifact_requires_exact_bytes_type():
    with pytest.raises(TypeError):
        anchors.decode_head_artifact("not bytes")  # type: ignore[arg-type]


# --- registry scan learns record_kind: log-head ----------------------------


def test_registry_scan_carries_log_heads_alongside_admissions_and_statuses(tmp_path):
    manifest = world_module.CorpusManifest(2, CORPUS_ID, PINS)
    root = tmp_path / "world"
    (root / "registry").mkdir(parents=True)
    admission = world_module.AdmissionRecord(manifest, world_module.Fresh(), "alice")
    (root / "registry" / f"{world_module.admission_digest(admission)}.yaml").write_text(
        yaml.safe_dump(world_module.admission_projection(admission), sort_keys=True), encoding="utf-8"
    )
    status = world_module.StatusRecord(CORPUS_ID, "retired", "alice")
    (root / "registry" / f"{world_module.status_digest(status)}.yaml").write_text(
        yaml.safe_dump(world_module.status_projection(status), sort_keys=True), encoding="utf-8"
    )
    log_head = build_record()
    write_raw_record(root, log_head)

    instance = make_world(tmp_path)
    view = instance.registry()

    assert view.admissions == (admission,)
    assert view.statuses == (status,)
    assert view.log_heads == (log_head,)


def test_registry_scan_refuses_a_log_head_file_with_a_wrong_content_name(tmp_path):
    root = tmp_path / "world"
    record = build_record()
    registry = root / "registry"
    registry.mkdir(parents=True)
    (registry / f"{'0' * 64}.yaml").write_text(
        yaml.safe_dump(anchors.log_head_projection(record), sort_keys=True), encoding="utf-8"
    )
    instance = make_world(tmp_path)

    with pytest.raises(RegistryMalformed):
        instance.registry()
