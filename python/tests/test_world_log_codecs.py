from __future__ import annotations

import inspect
import shutil
from collections.abc import Callable
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
from science.errors import (
    LogEvidenceRefused,
    MalformedDomain,
    ObserverCarrierInvalid,
    RegistryMalformed,
)
from science.identity import v1
from science.world import anchors, logmodel, verify

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


def test_an_unwired_state_facts_seam_refuses_loudly():
    production = science_root._log_seam()
    seam = verify.LogSeam(
        inspect_registered=production.inspect_registered,
        inspect_detached=production.inspect_detached,
        capture=production.capture,
        read_head=production.read_head,
        absent_state=production.absent_state,
        world_lock=production.world_lock,
        corpus_lock=production.corpus_lock,
    )

    with pytest.raises(AssertionError, match="wires no path-state fact encoder"):
        seam.state_facts(object())


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
        intent_digest="sha256:" + "a" * 64,
        consumer_tag="science-corpus-write-v1",
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


# --- cut 8's on-disk chain fabrication -------------------------------------
#
# Cut 8 §5's first obligation: **every fabricated chain a declared arm rests on
# passes `inspect_chain` as well-formed**, asserted at declaration time, unless
# the arm's point is the defect — and then exactly that one defect class and no
# other. The builders below discharge it the only way the obligation can be
# discharged literally: they write **real canonical entry envelopes** into a
# real root's reserved chain directory, and every arm reads them back through
# the production seam's *detached* inspection, which needs no metadata root and
# so runs anywhere the suite runs. The engine's own validator, not a view
# nobody inspected, is what says the fabrication is well formed.
#
# `CUT8_FABRICATIONS` at the foot of this section is the catalogue
# `acceptance/test_n2_cut8.py` walks: one entry per fabrication a declared arm
# builds, naming the defect the engine must report over it (`None` for the
# well-formed ones). A builder used by an arm and missing from the catalogue is
# a fabrication nobody inspected, which the harness refuses.

SCIENCE_CORPUS_GENESIS = v1.encode({"domain": "science.corpus-root.v1"})
CONSUMER_TAG = "science-corpus-write-v1"
UNRESOLVED_INTENT = "sha256:" + "0" * 64
"""`RegisteredEntry.intent_digest` is the engine's own staging bookkeeping and
is not the `fulfills` referent the taxonomy validates; the arms that mean an
intent name one through `fulfills`."""

MANIFEST = "corpus.yaml"
RECORD = "verification/v1.md"


def corpus_root_at(base: Path, corpus_id: str, *, name: str = "corpus") -> Path:
    """A corpus root with the manifest the presented-identity read expects."""
    root = base / name
    root.mkdir(parents=True)
    (root / MANIFEST).write_text(f"corpus_id: {corpus_id}\nversion: 2\n", encoding="utf-8")
    return root


def capture_at(root: Path, *paths: str) -> tuple[tuple[str, object], ...]:
    """The engine's own states for exactly these paths, through the seam."""
    return science_root._log_seam().capture(root, paths)


def state_at(root: Path, path: str) -> object:
    return capture_at(root, path)[0][1]


def inspected(root: Path) -> logmodel.ChainView:
    """Detached inspection through the production seam — `inspect_chain`'s own
    verdict over the fabrication, which is what cut 8 §5's obligation 1 asks
    for."""
    return science_root._log_seam().inspect_detached(root)


class Chain:
    """Canonical entry envelopes, written one at a time into a real root.

    Every mutator returns the digest the engine will name the entry by, so an
    arm can state a truncation, a sibling or an anchor over the very digests
    the chain carries rather than over stand-ins that merely look like them.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.digests: list[str] = []
        self.anchor = ""
        """The head a declared arm anchors at — set by the builders that mean one."""
        self.removed: tuple[str, ...] = ()
        """Digests the raw write deleted, in chain order."""
        self.replaced: tuple[bytes, ...] = ()
        self.added: tuple[bytes, ...] = ()
        """The envelope bytes a rewrite removed and the ones it wrote in their
        place — cut 8 §5's obligation 3 is asserted over exactly these."""
        self.paths: tuple[str, ...] = ()
        """The surface paths the arm judges this chain against."""

    # --- cooperative appends ---------------------------------------------
    def after(self, previous: str | None, entry: object) -> str:
        (digest,) = write_chain(self.root, [(previous, cast(Any, entry))])
        self.digests.append(digest)
        return digest

    def append(self, entry: object) -> str:
        return self.after(self.digests[-1] if self.digests else None, entry)

    def genesis(self, payload: bytes = SCIENCE_CORPUS_GENESIS) -> str:
        """§1.3's **empty** baseline: both Science initializers register `()`,
        so a populated one is a chain no Science path mints."""
        return self.append(GenesisEntry(payload=payload, baseline=()))

    def intent(self, payload: bytes = b"an intent") -> str:
        return self.append(IntentEntry(payload=payload))

    def registered(
        self,
        txid: str,
        initial: tuple[tuple[str, object], ...],
        final: tuple[tuple[str, object], ...],
        *,
        fulfills: str | None = None,
    ) -> RegisteredEntry:
        """The entry value, unwritten — for the arms that place it themselves."""
        return RegisteredEntry(
            txid=txid,
            intent_digest=UNRESOLVED_INTENT,
            consumer_tag=CONSUMER_TAG,
            initial=tuple((path, state_to_json(cast(Any, value))) for path, value in initial),
            final=tuple((path, state_to_json(cast(Any, value))) for path, value in final),
            fulfills=fulfills,
        )

    def registration(
        self,
        txid: str,
        initial: tuple[tuple[str, object], ...],
        final: tuple[tuple[str, object], ...],
        *,
        fulfills: str | None = None,
    ) -> str:
        return self.append(self.registered(txid, initial, final, fulfills=fulfills))

    def settlement(self, txid: str, registration: str, *, committed: bool = True) -> str:
        return self.append(
            SettledEntry(
                txid=txid,
                registration=registration,
                outcome=ChainOutcome.COMMITTED if committed else ChainOutcome.ROLLED_BACK,
            )
        )

    def transaction(
        self,
        txid: str,
        initial: tuple[tuple[str, object], ...],
        final: tuple[tuple[str, object], ...],
        *,
        committed: bool = True,
        fulfills: str | None = None,
    ) -> tuple[str, str]:
        registration = self.registration(txid, initial, final, fulfills=fulfills)
        return registration, self.settlement(txid, registration, committed=committed)

    # --- the raw-write licence (cut 8 §2) ---------------------------------
    def leaf(self, digest: str) -> Path:
        return self.root / CHAIN_LEAF / digest

    def drop(self, digest: str) -> None:
        self.leaf(digest).unlink()
        self.digests.remove(digest)

    def truncate_to(self, digest: str) -> tuple[str, ...]:
        """Delete every entry after `digest`, returning the digests removed."""
        removed = tuple(self.digests[self.digests.index(digest) + 1 :])
        for entry in removed:
            self.drop(entry)
        return removed

    @property
    def tip(self) -> str:
        return self.digests[-1]


# --- the builders every cut-8 declared arm fabricates through ---------------

CUT8_CORPUS_ID = "a" * 32
CUT8_SIBLING_ID = "b" * 32
CUT8_REMINTED_ID = "c" * 32


def _record_state(root: Path, content: bytes = b"# a held verification\n") -> object:
    """Write `verification/v1.md`, state it, and leave it on disk."""
    path = root / RECORD
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return state_at(root, RECORD)


def settled_corpus(base: Path, *, corpus_id: str = CUT8_CORPUS_ID, name: str = "corpus") -> Chain:
    """A corpus root and the committed transaction that created its manifest."""
    root = corpus_root_at(base, corpus_id, name=name)
    chain = Chain(root)
    chain.genesis()
    chain.transaction("tx-1", ((MANIFEST, ABSENT),), ((MANIFEST, state_at(root, MANIFEST)),))
    chain.anchor = chain.tip
    chain.paths = (MANIFEST,)
    return chain


def populated_corpus(base: Path, *, corpus_id: str = CUT8_CORPUS_ID, name: str = "corpus") -> Chain:
    """The same, plus a second committed transaction creating one record."""
    chain = settled_corpus(base, corpus_id=corpus_id, name=name)
    chain.anchor = chain.tip
    record = _record_state(chain.root)
    chain.transaction("tx-2", ((RECORD, ABSENT),), ((RECORD, record),))
    chain.paths = (MANIFEST, RECORD)
    return chain


def rolled_back_creation(base: Path) -> Chain:
    """L2u1: a registration whose settlement rolled back, and the path it would
    have created genuinely absent from disk (cut 8 §5's obligation 2)."""
    chain = settled_corpus(base)
    record = _record_state(chain.root)
    (chain.root / RECORD).unlink()
    chain.registration("tx-2", ((RECORD, ABSENT),), ((RECORD, record),))
    chain.settlement("tx-2", chain.tip, committed=False)
    chain.paths = (MANIFEST, RECORD)
    return chain


def removed_record(base: Path) -> Chain:
    """L13: a cooperatively logged removal of a verification record."""
    chain = populated_corpus(base)
    record = state_at(chain.root, RECORD)
    (chain.root / RECORD).unlink()
    chain.transaction("tx-3", ((RECORD, record),), ((RECORD, ABSENT),))
    chain.paths = (MANIFEST, RECORD)
    return chain


def pending_before_apply(base: Path) -> Chain:
    """L2u4: a copy caught before apply — the registration is unsettled and the
    record it would create is **absent** from the copied root."""
    chain = settled_corpus(base)
    record = _record_state(chain.root)
    (chain.root / RECORD).unlink()
    chain.registration("tx-2", ((RECORD, ABSENT),), ((RECORD, record),))
    chain.paths = (MANIFEST, RECORD)
    return chain


def pending_after_apply(base: Path) -> Chain:
    """L2u4's other variant: the copy caught *after* apply — same unsettled
    registration, and the record present on disk."""
    chain = settled_corpus(base)
    record = _record_state(chain.root)
    chain.registration("tx-2", ((RECORD, ABSENT),), ((RECORD, record),))
    chain.paths = (MANIFEST, RECORD)
    return chain


def truncated_prefix(base: Path) -> Chain:
    """L3u1/L12u4: two committed transactions, truncated back to the first.

    `anchor` is the head that was anchored before the truncation, which the
    surviving prefix can no longer reach.
    """
    chain = populated_corpus(base)
    chain.anchor = chain.tip
    behind = chain.digests[2]
    chain.removed = chain.truncate_to(behind)
    (chain.root / RECORD).unlink()
    chain.paths = (MANIFEST,)
    return chain


def alternative_chain(base: Path) -> Chain:
    """L4u5: the same constant genesis, a self-consistent replacement tail.

    The corpus genesis payload carries no per-corpus identity, so a replacement
    chain shares the original's genesis digest exactly — which is why §1.2's
    mechanism for corpus replacement is anchored-head unreachability and not a
    genesis comparison.
    """
    chain = populated_corpus(base)
    chain.anchor = chain.tip
    genesis = chain.digests[0]
    chain.removed = chain.truncate_to(genesis)
    (chain.root / RECORD).unlink()
    chain.transaction("tx-9", ((MANIFEST, ABSENT),), ((MANIFEST, state_at(chain.root, MANIFEST)),))
    chain.paths = (MANIFEST,)
    return chain


def rewritten_tail(base: Path) -> Chain:
    """L5: the tail beyond the maximal anchor rewritten into a self-consistent
    alternative, **and the registered surface rewritten to match**.

    `replaced` and `added` are the entry envelopes either side of the rewrite,
    so cut 8 §5's obligation 3 — a byte difference beyond the anchor, over at
    least one entry — is asserted over the bytes themselves.
    """
    chain = populated_corpus(base)
    chain.anchor = chain.digests[2]
    original = tuple(chain.leaf(digest).read_bytes() for digest in chain.digests[3:])
    chain.removed = chain.truncate_to(chain.anchor)
    rewritten = _record_state(chain.root, b"# a different verification\n")
    chain.transaction("tx-2b", ((RECORD, ABSENT),), ((RECORD, rewritten),))
    chain.replaced = original
    chain.added = tuple(chain.leaf(digest).read_bytes() for digest in chain.digests[3:])
    chain.paths = (MANIFEST, RECORD)
    return chain


def forged_intent_beyond_the_anchor(base: Path) -> Chain:
    """L12u5: a structurally valid raw append past the maximal anchor."""
    chain = settled_corpus(base)
    chain.anchor = chain.tip
    chain.intent(b"an intent no act ever appended")
    chain.paths = (MANIFEST,)
    return chain


def four_state_classes(base: Path) -> Chain:
    """L12u1: one committed transaction creating one path of each state class."""
    root = base / "states"
    root.mkdir(parents=True)
    (root / "f.txt").write_bytes(b"hello\n")
    (root / "d").mkdir()
    (root / "link").symlink_to("f.txt")
    paths = ("d", "f.txt", "gone", "link")
    """Sorted, because the engine's own envelope grammar requires a surface to
    be — the four classes are `DirectoryState`, `FileState` (which carries the
    mode), `AbsentState` and `SymlinkState` (which carries the target)."""
    chain = Chain(root)
    chain.genesis()
    chain.transaction(
        "tx-1",
        tuple((path, ABSENT) for path in paths),
        capture_at(root, *paths),
    )
    chain.paths = paths
    return chain


def deleted_chain(base: Path) -> Chain:
    """L4u1: the chain directory removed from an anchored corpus root."""
    chain = settled_corpus(base)
    chain.anchor = chain.tip
    chain.removed = tuple(chain.digests)
    for digest in chain.removed:
        chain.leaf(digest).unlink()
    (chain.root / CHAIN_LEAF).rmdir()
    return chain


def deletion_plus_remint(base: Path) -> Chain:
    """L4u7: A's chain deleted **and** its `corpus.yaml` re-minted as B."""
    chain = deleted_chain(base)
    (chain.root / MANIFEST).write_text(f"corpus_id: {CUT8_REMINTED_ID}\nversion: 2\n", encoding="utf-8")
    return chain


def manifest_remint(base: Path) -> Chain:
    """L4u3: the manifest raw re-minted A → B with the chain present, and
    **nothing else touched** — cut 8 §6's first freeze obligation."""
    chain = populated_corpus(base)
    chain.anchor = chain.tip
    (chain.root / MANIFEST).write_text(f"corpus_id: {CUT8_REMINTED_ID}\nversion: 2\n", encoding="utf-8")
    return chain


def duplicate_settlement(base: Path) -> Chain:
    """L2u3: two settlements for one registration."""
    chain = settled_corpus(base)
    chain.settlement("tx-1", chain.digests[1])
    return chain


def interior_deleted(base: Path) -> Chain:
    """L3u2/L12u4: an interior entry deleted, breaking the linkage."""
    chain = populated_corpus(base)
    chain.removed = (chain.digests[1],)
    chain.drop(chain.removed[0])
    return chain


def interior_rewritten(base: Path) -> Chain:
    """L3u2/L12u4: an interior entry's bytes edited under its content name."""
    chain = populated_corpus(base)
    leaf = chain.leaf(chain.digests[1])
    leaf.write_bytes(leaf.read_bytes() + b" ")
    return chain


def sibling_branch(base: Path) -> Chain:
    """L3u3: a second successor raw-appended beside the retained original."""
    chain = settled_corpus(base)
    chain.after(chain.digests[0], chain.registered("tx-9", ((MANIFEST, ABSENT),), ((MANIFEST, ABSENT),)))
    return chain


def orphan_entry(base: Path) -> Chain:
    """L3u4: an entry naming a predecessor this chain does not carry.

    The engine names it `missing-predecessor`: `orphan-history` is reserved for
    a disconnected component with valid *internal* linkage, which no
    content-named directory fixture can construct (a digest fixed point), and
    is certified in atoms through the typed validation core.
    """
    chain = settled_corpus(base)
    chain.after("f" * 64, chain.registered("tx-9", ((MANIFEST, ABSENT),), ((MANIFEST, ABSENT),)))
    return chain


def fulfills_missing_intent(base: Path) -> Chain:
    """L7u1: a `fulfills` naming an intent this chain does not carry."""
    chain = settled_corpus(base)
    chain.registration("tx-2", ((RECORD, ABSENT),), ((RECORD, ABSENT),), fulfills="e" * 64)
    return chain


def fulfills_non_intent(base: Path) -> Chain:
    """L7u1: a `fulfills` naming a present entry that is not an intent."""
    chain = settled_corpus(base)
    chain.registration("tx-2", ((RECORD, ABSENT),), ((RECORD, ABSENT),), fulfills=chain.digests[1])
    return chain


def duplicate_fulfillment(base: Path) -> Chain:
    """L7u2: a second committed registration fulfilling one intent."""
    root = corpus_root_at(base, CUT8_CORPUS_ID)
    chain = Chain(root)
    chain.genesis()
    intent = chain.intent()
    manifest = state_at(root, MANIFEST)
    chain.transaction("tx-1", ((MANIFEST, ABSENT),), ((MANIFEST, manifest),), fulfills=intent)
    chain.transaction("tx-2", ((MANIFEST, manifest),), ((MANIFEST, manifest),), fulfills=intent)
    chain.paths = (MANIFEST,)
    return chain


CUT8_WORLD_ID = "e" * 32
CUT8_OTHER_WORLD_ID = "d" * 32
WORLD_MIRROR = "world.yaml"


def settled_world(base: Path, *, world_id: str = CUT8_WORLD_ID, name: str = "world", genesis_id: str | None = None) -> Chain:
    """A world root, its mirror, and the transaction that created it.

    `genesis_id` names the world the *chain* was minted under when it differs
    from the configured one — D1's subject-mismatch split and L4u6's rewritten
    world both turn on exactly that disagreement.
    """
    root = base / name
    root.mkdir(parents=True)
    (root / WORLD_MIRROR).write_bytes(world_module._world_mirror_bytes(world_id))
    chain = Chain(root)
    chain.genesis(payload=science_root._world_genesis_payload(genesis_id if genesis_id is not None else world_id))
    chain.transaction(
        "tx-1", ((WORLD_MIRROR, ABSENT),), ((WORLD_MIRROR, state_at(root, WORLD_MIRROR)),)
    )
    chain.anchor = chain.tip
    chain.paths = (WORLD_MIRROR,)
    return chain


def foreign_world_genesis(base: Path) -> Chain:
    """D1: a *valid* world genesis naming another world — subject mismatch, and
    never step 1's malformed exit (§4.2, §1.3)."""
    return settled_world(base, world_id=CUT8_WORLD_ID, genesis_id=CUT8_OTHER_WORLD_ID)


def undecodable_genesis(base: Path) -> Chain:
    """D1: a genesis payload that is not a Science genesis document at all.

    The engine calls this chain well formed — an entry payload is opaque bytes
    to the validator — so the malformation is the evaluator's own step-1 finding
    and this fabrication belongs in the catalogue as well formed.
    """
    root = corpus_root_at(base, CUT8_CORPUS_ID)
    chain = Chain(root)
    chain.genesis(payload=b"\xff\xfe not a document")
    chain.transaction("tx-1", ((MANIFEST, ABSENT),), ((MANIFEST, state_at(root, MANIFEST)),))
    chain.paths = (MANIFEST,)
    return chain


def wrong_form_genesis(base: Path) -> Chain:
    """D1: a well-formed *world* genesis carried by a corpus root."""
    root = corpus_root_at(base, CUT8_CORPUS_ID)
    chain = Chain(root)
    chain.genesis(payload=science_root._world_genesis_payload(CUT8_WORLD_ID))
    chain.transaction("tx-1", ((MANIFEST, ABSENT),), ((MANIFEST, state_at(root, MANIFEST)),))
    chain.paths = (MANIFEST,)
    return chain


def populated_baseline(base: Path) -> Chain:
    """D1: §1.3's non-empty baseline — a chain no Science initializer mints."""
    root = corpus_root_at(base, CUT8_CORPUS_ID)
    manifest = state_at(root, MANIFEST)
    chain = Chain(root)
    chain.append(
        GenesisEntry(
            payload=SCIENCE_CORPUS_GENESIS,
            baseline=((MANIFEST, state_to_json(cast(Any, manifest))),),
        )
    )
    chain.transaction("tx-1", ((MANIFEST, manifest),), ((MANIFEST, manifest),))
    chain.paths = (MANIFEST,)
    return chain


def rewritten_world(base: Path) -> Chain:
    """L4u6: a world root minted under W1, then rewritten — chain **and** mirror
    — to W2.

    `removed` is the superseded W1 chain's digests, its genesis first, and
    `anchor` is the W1 head an external holder exported before the rewrite.
    """
    first = settled_world(base, world_id=CUT8_WORLD_ID)
    root = first.root
    superseded = tuple(first.digests)
    for digest in superseded:
        first.leaf(digest).unlink()
    (root / WORLD_MIRROR).write_bytes(world_module._world_mirror_bytes(CUT8_OTHER_WORLD_ID))
    chain = Chain(root)
    chain.genesis(payload=science_root._world_genesis_payload(CUT8_OTHER_WORLD_ID))
    chain.transaction(
        "tx-1", ((WORLD_MIRROR, ABSENT),), ((WORLD_MIRROR, state_at(root, WORLD_MIRROR)),)
    )
    chain.removed = superseded
    chain.anchor = superseded[-1]
    chain.paths = (WORLD_MIRROR,)
    return chain


IN_ROOT_EPOCH = "1" * 64
IN_ROOT_RECORD = "a" * 64
IN_ROOT_CARRIERS = (f"epochs/{IN_ROOT_EPOCH}/anchors.yaml", f"registry/{IN_ROOT_RECORD}.yaml")
"""The two in-root carriers L11's negative truncates beside the chain itself —
an epoch stored in the world root and a registry record. Sorted, because the
envelope grammar requires a surface to be."""


def coordinated_truncation(base: Path) -> Chain:
    """L11u3/L11u4: world chain, registry and in-root epochs truncated together.

    `removed` is the chain entries deleted and `anchor` the world head the
    deleted tip carried — the head an *exported* epoch would still hold. The
    two in-root carriers are gone from disk, so the surviving prefix replays
    against the surviving surface with nothing left over.
    """
    root = base / "world"
    root.mkdir(parents=True)
    (root / WORLD_MIRROR).write_bytes(world_module._world_mirror_bytes(CUT8_WORLD_ID))
    chain = Chain(root)
    chain.genesis(payload=science_root._world_genesis_payload(CUT8_WORLD_ID))
    chain.transaction(
        "tx-1", ((WORLD_MIRROR, ABSENT),), ((WORLD_MIRROR, state_at(root, WORLD_MIRROR)),)
    )
    behind = chain.tip
    for carrier in IN_ROOT_CARRIERS:
        target = root / carrier
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {carrier}\n", encoding="utf-8")
    chain.transaction(
        "tx-2",
        tuple((carrier, ABSENT) for carrier in IN_ROOT_CARRIERS),
        capture_at(root, *IN_ROOT_CARRIERS),
    )
    chain.anchor = chain.tip

    chain.removed = chain.truncate_to(behind)
    shutil.rmtree(root / "registry")
    shutil.rmtree(root / "epochs")
    chain.paths = (WORLD_MIRROR,)
    return chain


ABSENT_CHAIN = "absent"
"""The catalogue's marker for a fabrication with no chain at all — an
`AbsentView` is neither well formed nor a defect, and cut 8's L4 arms mean it."""

CUT8_FABRICATIONS: tuple[tuple[str, Callable[[Path], Chain], str | None], ...] = (
    ("settled_corpus", settled_corpus, None),
    ("settled_world", settled_world, None),
    ("rewritten_world", rewritten_world, None),
    ("coordinated_truncation", coordinated_truncation, None),
    ("foreign_world_genesis", foreign_world_genesis, None),
    ("undecodable_genesis", undecodable_genesis, None),
    ("wrong_form_genesis", wrong_form_genesis, None),
    ("populated_baseline", populated_baseline, None),
    ("populated_corpus", populated_corpus, None),
    ("rolled_back_creation", rolled_back_creation, None),
    ("removed_record", removed_record, None),
    ("pending_before_apply", pending_before_apply, None),
    ("pending_after_apply", pending_after_apply, None),
    ("truncated_prefix", truncated_prefix, None),
    ("alternative_chain", alternative_chain, None),
    ("rewritten_tail", rewritten_tail, None),
    ("forged_intent_beyond_the_anchor", forged_intent_beyond_the_anchor, None),
    ("four_state_classes", four_state_classes, None),
    ("manifest_remint", manifest_remint, None),
    ("deleted_chain", deleted_chain, ABSENT_CHAIN),
    ("deletion_plus_remint", deletion_plus_remint, ABSENT_CHAIN),
    ("duplicate_settlement", duplicate_settlement, "duplicate-settlement"),
    ("interior_deleted", interior_deleted, "missing-predecessor"),
    ("interior_rewritten", interior_rewritten, "name-mismatch"),
    ("sibling_branch", sibling_branch, "sibling-branch"),
    ("orphan_entry", orphan_entry, "missing-predecessor"),
    ("fulfills_missing_intent", fulfills_missing_intent, "fulfills-invalid"),
    ("fulfills_non_intent", fulfills_non_intent, "fulfills-invalid"),
    ("duplicate_fulfillment", duplicate_fulfillment, "duplicate-fulfillment"),
)
"""Every on-disk fabrication a cut-8 declared arm rests on, with the engine's
own verdict over it. `acceptance/test_n2_cut8.py` walks this table and runs
`inspect_chain` over each — §5's obligation 1, discharged by the validator."""


# --- cut 8's declarations homed here ---------------------------------------


def test_world_subject_registry_record_is_unconstructible():
    """L11u2. A registry log-head record carrying a `world` subject is
    unconstructible through the anchor act **and** is never accepted as an
    anchor: the value type refuses it, the parser refuses it, the act's own
    signature cannot spell one, and the observer carrier refuses a record whose
    subject was forced past the constructor."""
    with pytest.raises(TypeError):
        anchors.LogHeadRecord(
            anchors.WorldSubject(WORLD_ID),  # pyright: ignore[reportArgumentType]
            GENESIS,
            HEAD,
            anchors.AnchorActOrigin("alice"),
        )
    with pytest.raises(ValueError):
        anchors.parse_log_head_record(
            {
                "record_kind": "log-head",
                "subject": {"kind": "world", "world_id": WORLD_ID},
                "genesis": GENESIS,
                "head": HEAD,
                "origin": {"kind": "anchor-act", "actor": "alice"},
            }
        )
    assert anchors._LOG_HEAD_SUBJECT_KINDS == frozenset({"corpus", "store"})

    # The act takes corpus ids and nothing else, so no caller can hand it a
    # world subject to record in the first place.
    parameters = inspect.signature(anchors._anchor_heads).parameters
    assert str(parameters["corpus_ids"].annotation) == "frozenset[str]"
    assert "subject" not in parameters

    # And the last door: a record forced past its constructor is refused by the
    # carrier rather than admitted as a world anchor.
    forced = anchors.LogHeadRecord(anchors.CorpusSubject(CORPUS_ID), GENESIS, HEAD, anchors.AnchorActOrigin("alice"))
    object.__setattr__(forced, "subject", anchors.WorldSubject(WORLD_ID))
    with pytest.raises(ObserverCarrierInvalid):
        verify.RegistryCarrier.from_record(forced)


def test_no_entry_class_records_preimage_gc():
    """L13u5, at the width the cut declares: a **taxonomy** fact over the entry
    classes.

    Preimage-blob collection is engine bookkeeping over content-addressed
    payloads, and the chain's vocabulary has no way to say it happened: the four
    entry classes carry a genesis payload and baseline, a transaction's
    before/after path states, a settlement outcome, and an intent payload —
    nothing that names a blob, a preimage or a collection. Asserted over the
    closed union rather than over one chain, because a chain that happens to
    carry no such entry says nothing about whether one could exist.
    """
    classes = get_args(logmodel.EntryView)
    assert set(classes) == {
        logmodel.GenesisEntryView,
        logmodel.RegisteredEntryView,
        logmodel.SettledEntryView,
        logmodel.IntentEntryView,
    }
    fields = {
        f"{entry.__name__}.{name}"
        for entry in classes
        for name in getattr(entry, "__dataclass_fields__", {})
    }
    assert not [name for name in fields if any(word in name.lower() for word in ("blob", "preimage", "gc"))]

    # The same width from the engine's side: the taxonomy of things a chain can
    # be malformed *about* names no collection either, so there is no defect
    # class standing in for one.
    assert not [kind for kind in logmodel.DEFECT_KINDS if "blob" in kind or "preimage" in kind]


def test_store_subject_is_carried_by_codecs_and_judged_by_the_evaluator():
    """D6, as the root-lifecycle slice leaves it: the store arm is carried by
    both codecs, and the evaluator judges a store subject through the same
    four-outcome precedence — the shape-only refusal is deleted, not merely
    un-raised (`test_store_subjects.py` pins the deletion)."""
    record = build_record(subject=anchors.StoreSubject(STORE_ID))
    assert anchors.parse_log_head_record(anchors.log_head_projection(record)) == record
    artifact = anchors.HeadArtifact(anchors.StoreSubject(STORE_ID), GENESIS, HEAD)
    assert anchors.decode_head_artifact(anchors.head_artifact_bytes(artifact)) == artifact

    report = verify.evaluate_log(
        anchors.StoreSubject(STORE_ID),
        logmodel.AbsentView(),
        verify.ObserverSet(()),
        (),
        None,
        ABSENT,
        None,
    )
    assert report.outcome == "unresolvable"

    # Both acts now spell a store: the anchor act through its (store_id, root)
    # pairs — still never a bare subject parameter — and the export act
    # through the full subject union with a supplied root.
    assert "subject" not in inspect.signature(anchors._anchor_heads).parameters
    assert "store_roots" in inspect.signature(anchors._anchor_heads).parameters
    exported = inspect.signature(anchors._export_head_artifact).parameters["subject"]
    assert str(exported.annotation) == "Subject"
