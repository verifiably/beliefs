from __future__ import annotations

from pathlib import Path
from typing import Any, cast, get_args

import pytest
import yaml
from atoms.chain.errors import ChainStateInvalid
from atoms.chain.inspect import AbsentChain, MalformedChain
from atoms.chain.inspect import ChainDefect as EngineDefect
from atoms.chain.inspect import DefectKind as EngineDefectKind
from atoms.chain.model import (
    ChainOutcome,
    GenesisEntry,
    IntentEntry,
    RegisteredEntry,
    SettledEntry,
    encode_entry,
    entry_digest,
    state_to_json,
)
from atoms.coordinator.commands import ChainView as EngineChainView
from atoms.core.errors import PreconditionRefused, ProtocolError, TransactionHalted
from atoms.core.fingerprint import ABSENT, AbsentState, FileState
from atoms.core.scratch import CHAIN_LEAF
from fixtures_cut6 import PINS
from nodes.core.write_plan import DefaultExecutor

import science.world.registry as world_module
from science import corpus as corpus_module
from science import root as science_root
from science.errors import LogEvidenceRefused, MalformedDomain, RegistryMalformed
from science.identity import v1
from science.world import anchors, logmodel

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


# --- the log seam: chain views, capture pass-through, locks ----------------
#
# The conversion is exercised two ways on purpose. The parametrized arms drive
# `science.root`'s converter with fabricated `atoms` inspection results, which
# is the only way to reach all fourteen defect kinds without fourteen damaged
# chains; the end-to-end arms drive the seam's own callables over a chain
# written to disk as real canonical envelopes, so the fabrications are not the
# whole evidence.


def write_chain(root: Path, entries: list[tuple[str | None, object]]) -> list[str]:
    """Write canonical entry envelopes into the reserved chain directory."""
    chain = root / CHAIN_LEAF
    chain.mkdir(parents=True, exist_ok=True)
    digests: list[str] = []
    for previous, entry in entries:
        envelope = encode_entry(previous, cast(Any, entry))
        digest = entry_digest(envelope)
        (chain / digest).write_bytes(envelope)
        digests.append(digest)
    return digests


def populated_root(tmp_path: Path) -> tuple[Path, tuple[tuple[str, object], ...], list[str]]:
    """A root holding one file, and a four-entry chain over its captured state."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "f.txt").write_bytes(b"hello\n")
    captured = science_root._log_seam().capture(root, ("f.txt",))
    surface = ("f.txt", state_to_json(cast(Any, captured[0][1])))
    genesis = GenesisEntry(payload=b'{"domain":"science.corpus-root.v1"}', baseline=(surface,))
    digests = write_chain(root, [(None, genesis)])
    intent = IntentEntry(payload=b"an intent")
    digests += write_chain(root, [(digests[-1], intent)])
    registered = RegisteredEntry(
        txid="tx-one",
        intent_digest="sha256:" + "a" * 64,
        consumer_tag="science-corpus-write-v1",
        initial=(surface,),
        final=(surface,),
        fulfills=digests[-1],
    )
    digests += write_chain(root, [(digests[-1], registered)])
    settled = SettledEntry(txid="tx-one", registration=digests[-1], outcome=ChainOutcome.COMMITTED)
    digests += write_chain(root, [(digests[-1], settled)])
    return root, captured, digests


DEFECT_SUBJECTS = {
    engine_kind: ("d" * 64 if engine_kind is not EngineDefectKind.GENESIS_COUNT else None)
    for engine_kind in EngineDefectKind
}

DEFECT_MAPPING = [
    (EngineDefectKind.FOREIGN_LEAF, "foreign-leaf"),
    (EngineDefectKind.NAME_BYTES_MISMATCH, "name-mismatch"),
    (EngineDefectKind.UNDECODABLE_ENTRY, "undecodable-entry"),
    (EngineDefectKind.GENESIS_COUNT, "genesis-count"),
    (EngineDefectKind.MISSING_PREDECESSOR, "missing-predecessor"),
    (EngineDefectKind.SIBLING_BRANCH, "sibling-branch"),
    (EngineDefectKind.CYCLE, "cycle"),
    (EngineDefectKind.ORPHAN_HISTORY, "orphan-history"),
    (EngineDefectKind.SETTLEMENT_WITHOUT_REGISTRATION, "settlement-unregistered"),
    (EngineDefectKind.SETTLEMENT_TXID_MISMATCH, "settlement-txid-mismatch"),
    (EngineDefectKind.DUPLICATE_SETTLEMENT, "duplicate-settlement"),
    (EngineDefectKind.DUPLICATE_REGISTRATION, "duplicate-registration"),
    (EngineDefectKind.FULFILLS_UNRESOLVED, "fulfills-invalid"),
    (EngineDefectKind.DUPLICATE_FULFILLMENT, "duplicate-fulfillment"),
]


def test_the_defect_mapping_is_closed_over_the_engines_taxonomy():
    assert set(science_root._DEFECT_KINDS) == set(EngineDefectKind)
    assert set(science_root._DEFECT_KINDS.values()) == set(get_args(logmodel.DefectKind))
    assert len(science_root._DEFECT_KINDS) == 14
    assert logmodel.DEFECT_KINDS == tuple(get_args(logmodel.DefectKind))


def test_this_files_mapping_table_is_the_whole_taxonomy():
    # Otherwise the parametrization below could quietly cover thirteen.
    assert [engine_kind for engine_kind, _science_kind in DEFECT_MAPPING] == list(EngineDefectKind)


@pytest.mark.parametrize(("engine_kind", "science_kind"), DEFECT_MAPPING, ids=lambda value: str(value))
def test_each_engine_defect_kind_converts_to_its_view(engine_kind, science_kind):
    subject = DEFECT_SUBJECTS[engine_kind]
    inspection = MalformedChain(EngineDefect(engine_kind, subject, "the engine's own wording"))

    view = science_root._chain_view(inspection)

    assert view == logmodel.MalformedView(
        logmodel.DefectView(science_kind, subject, "the engine's own wording")
    )


def test_the_absent_chain_converts_to_the_absent_view():
    assert science_root._chain_view(AbsentChain()) == logmodel.AbsentView()


def test_the_well_formed_chain_converts_entry_by_entry(tmp_path):
    root, captured, digests = populated_root(tmp_path)

    view = science_root._log_seam().inspect_detached(root)

    assert isinstance(view, logmodel.WellFormedView)
    assert view.tip == digests[-1]
    assert view.pending == ()
    assert view.genesis is view.entries[0]
    assert view.genesis == logmodel.GenesisEntryView(
        digest=digests[0],
        payload=b'{"domain":"science.corpus-root.v1"}',
        baseline=(("f.txt", captured[0][1]),),
    )
    assert view.entries[1] == logmodel.IntentEntryView(digest=digests[1], payload=b"an intent")
    assert view.entries[2] == logmodel.RegisteredEntryView(
        digest=digests[2],
        txid="tx-one",
        initial=(("f.txt", captured[0][1]),),
        final=(("f.txt", captured[0][1]),),
        fulfills=digests[1],
    )
    assert view.entries[3] == logmodel.SettledEntryView(
        digest=digests[3], txid="tx-one", registration=digests[2], committed=True
    )


def test_a_rolled_back_settlement_is_the_uncommitted_view(tmp_path):
    root, _captured, digests = populated_root(tmp_path)
    (root / CHAIN_LEAF / digests[3]).unlink()
    rolled = SettledEntry(txid="tx-one", registration=digests[2], outcome=ChainOutcome.ROLLED_BACK)
    write_chain(root, [(digests[2], rolled)])

    view = science_root._log_seam().inspect_detached(root)

    assert isinstance(view, logmodel.WellFormedView)
    settlement = view.entries[3]
    assert isinstance(settlement, logmodel.SettledEntryView)
    assert settlement.committed is False


def test_capture_states_exactly_the_named_paths_in_order(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "f.txt").write_bytes(b"hello\n")

    captured = science_root._log_seam().capture(root, ("f.txt", "absent-here"))

    assert [path for path, _state in captured] == ["f.txt", "absent-here"]
    assert type(captured[0][1]) is FileState
    assert captured[1][1] == AbsentState()


def test_the_capture_pass_through_is_the_engines_own_object(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    minted = FileState(content_hash="sha256:" + "b" * 64, mode=0o644, byte_len=7)
    monkeypatch.setattr(science_root, "capture_states", lambda backend, root, paths: (("f.txt", minted),))

    captured = science_root._log_seam().capture(root, ("f.txt",))

    assert captured[0][1] is minted


def test_a_decoded_entry_state_equals_the_capture_of_the_same_disk_state(tmp_path):
    root, captured, _digests = populated_root(tmp_path)

    view = science_root._log_seam().inspect_detached(root)

    assert isinstance(view, logmodel.WellFormedView)
    decoded = view.genesis.baseline[0][1]
    # Two atoms forms — the chain's `PathStateJSON` and capture's `PathState` —
    # meeting in one comparable value, which is what makes replay's comparison
    # a comparison rather than a re-encoding.
    assert decoded == captured[0][1]
    assert type(decoded) is FileState


def test_detached_inspect_over_a_metadata_less_root_returns_rather_than_raises(tmp_path):
    root = tmp_path / "arriving"
    root.mkdir()
    (root / "corpus.yaml").write_bytes(b"corpus_id: " + b"1" * 32 + b"\n")

    assert science_root._log_seam().inspect_detached(root) == logmodel.AbsentView()
    assert not (root / ".metadata").exists()


def test_a_foreign_chain_leaf_reaches_the_view_as_a_defect(tmp_path):
    root, _captured, _digests = populated_root(tmp_path)
    (root / CHAIN_LEAF / "not-a-digest").write_bytes(b"")

    view = science_root._log_seam().inspect_detached(root)

    assert isinstance(view, logmodel.MalformedView)
    assert view.defect.kind == "foreign-leaf"
    assert view.defect.subject == "not-a-digest"
    assert view.defect.detail


def test_a_registered_inspect_translates_a_halted_transaction(tmp_path, monkeypatch):
    halted = TransactionHalted("the transaction stopped mid-flight")

    def raising(backend, project_root, metadata_root, storage):
        raise halted

    monkeypatch.setattr(science_root, "inspect_chain", raising)

    with pytest.raises(LogEvidenceRefused) as caught:
        science_root._log_seam().inspect_registered(tmp_path)

    assert caught.value.phase == "inspect"
    assert caught.value.engine_error == "TransactionHalted"
    assert caught.value.detail == "the transaction stopped mid-flight"
    assert caught.value.__cause__ is halted


def test_a_registered_inspect_translates_a_chain_record_contradiction(tmp_path, monkeypatch):
    invalid = ChainStateInvalid("a live transaction record exists without its project chain")

    def raising(backend, project_root, metadata_root, storage):
        raise invalid

    monkeypatch.setattr(science_root, "inspect_chain", raising)

    with pytest.raises(LogEvidenceRefused) as caught:
        science_root._log_seam().inspect_registered(tmp_path)

    assert (caught.value.phase, caught.value.engine_error) == ("inspect", "ChainStateInvalid")
    assert caught.value.__cause__ is invalid


def test_a_capture_refusal_translates_at_the_capture_phase(tmp_path, monkeypatch):
    refused = PreconditionRefused("a modeled path holds an unrepresentable entry")

    def raising(backend, root, paths):
        raise refused

    monkeypatch.setattr(science_root, "capture_states", raising)

    with pytest.raises(LogEvidenceRefused) as caught:
        science_root._log_seam().capture(tmp_path, ("f.txt",))

    assert (caught.value.phase, caught.value.engine_error) == ("capture", "PreconditionRefused")
    assert caught.value.detail == "a modeled path holds an unrepresentable entry"
    assert caught.value.__cause__ is refused


def test_a_protocol_error_passes_through_untranslated(tmp_path, monkeypatch):
    def raising(backend, project_root, metadata_root, storage):
        raise ProtocolError("the caller misused the command")

    monkeypatch.setattr(science_root, "inspect_chain", raising)

    with pytest.raises(ProtocolError):
        science_root._log_seam().inspect_registered(tmp_path)


def test_read_head_carries_the_genesis_payload(tmp_path, monkeypatch):
    payload = b'{"domain":"science.world-root.v1","world_id":"' + b"f" * 32 + b'"}'
    entries = (
        ("a" * 64, GenesisEntry(payload=payload, baseline=())),
        ("b" * 64, IntentEntry(payload=b"i")),
    )
    monkeypatch.setattr(
        science_root,
        "read_chain",
        lambda backend, project_root, metadata_root, storage: EngineChainView(
            genesis_digest="a" * 64, entries=entries, tip="b" * 64
        ),
    )

    head = science_root._log_seam().read_head(tmp_path)

    assert head == logmodel.ChainHead(genesis_digest="a" * 64, genesis_payload=payload, tip="b" * 64)


def test_the_seam_carries_the_engines_absent_singleton(tmp_path):
    assert science_root._log_seam().absent_state is ABSENT


def test_the_seam_is_one_stable_object():
    # The same sense of stable as `chain_head_reader`: a caller may assert that
    # an act holds *this* seam, not one that merely behaves like it.
    assert science_root._log_seam() is science_root._log_seam()


def test_the_world_lock_lookup_yields_the_lock_an_opened_world_holds(tmp_path):
    root = tmp_path / "world"
    root.mkdir()

    looked_up = world_module._world_lock_for(root)
    instance = make_world(tmp_path)

    assert instance._state.lock is looked_up
    assert world_module._world_lock_for(root) is looked_up


def test_the_seams_world_lock_holds_that_very_lock(tmp_path):
    root = tmp_path / "world"
    root.mkdir()
    held = world_module._world_lock_for(root)

    with science_root._log_seam().world_lock(root):
        assert held.acquire(blocking=False) is False

    assert held.acquire(blocking=False) is True
    held.release()


def test_the_seams_corpus_lock_is_the_write_apis_own(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()

    assert science_root._log_seam().corpus_lock(root) is corpus_module._operation_lock_for(root)
