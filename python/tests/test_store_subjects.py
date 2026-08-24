"""Store subjects through anchor, export, and audit (plan Task 4).

The codecs have carried stores since the log slice; this module pins the
widening that makes them actable: the anchor act minting a store-subject
record from a supplied root, the export act binding a store head, and the
audit path judging a store root through the same four-outcome evaluator —
with the shape-only refusal deleted outright, not merely un-raised.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_world_anchor_act import (
    Heads,
    make_seam,
    registry_tree,
    stored_log_heads,
)
from test_world_epoch import admitted_world
from test_world_log_audit import (
    Captures,
    Inspections,
    audit,
    config_for,
    digest,
    surfaced,
)

from science import errors as science_errors
from science import root as science_root
from science.corpus import _operation_lock_for
from science.errors import BuildContended, StoreIdMismatch
from science.world import anchors, logmodel, verify

STORE_ID = "5" * 32
OTHER_STORE_ID = "6" * 32


def store_payload(store_id: str = STORE_ID) -> bytes:
    return science_root._store_genesis_payload(store_id, None)


def store_root(tmp_path: Path, name: str = "store") -> Path:
    root = tmp_path / name
    (root / "artifacts").mkdir(parents=True)
    (root / "artifacts" / "head.json").write_bytes(b"{}")
    (root / "blob.bin").write_bytes(b"opaque payload")
    return root


def store_record(genesis: str, head: str) -> anchors.LogHeadRecord:
    return anchors.LogHeadRecord(
        anchors.StoreSubject(STORE_ID), genesis, head, anchors.AnchorActOrigin("alice")
    )


def store_observer(view: logmodel.WellFormedView) -> verify.RegistryCarrier:
    return verify.RegistryCarrier.from_record(
        store_record(view.genesis.digest, view.tip)
    )


# --- the anchor and export acts ---------------------------------------------


def test_anchor_heads_mints_a_store_subject_record(tmp_path):
    world, _recorder, _bindings, _roots = admitted_world(tmp_path)
    heads = Heads()
    root = store_root(tmp_path)
    heads.set(root, digest("store-genesis"), digest("store-head"), store_payload())

    records = anchors._anchor_heads(
        world,
        frozenset(),
        store_roots=((STORE_ID, root),),
        actor="alice",
        seam=make_seam(heads),
    )

    expected = store_record(digest("store-genesis"), digest("store-head"))
    assert records == (expected,)
    assert expected in stored_log_heads(world)


def test_anchor_refuses_a_store_id_genesis_mismatch_before_registry_mutation(
    tmp_path,
):
    world, _recorder, _bindings, _roots = admitted_world(tmp_path)
    heads = Heads()
    root = store_root(tmp_path)
    heads.set(
        root,
        digest("store-genesis"),
        digest("store-head"),
        store_payload(OTHER_STORE_ID),
    )
    before = registry_tree(world)

    with pytest.raises(StoreIdMismatch):
        anchors._anchor_heads(
            world,
            frozenset(),
            store_roots=((STORE_ID, root),),
            actor="alice",
            seam=make_seam(heads),
        )
    assert registry_tree(world) == before


def test_export_head_artifact_round_trips_a_store_head(tmp_path):
    world, _recorder, _bindings, _roots = admitted_world(tmp_path)
    heads = Heads()
    root = store_root(tmp_path)
    heads.set(root, digest("store-genesis"), digest("store-head"), store_payload())

    data = anchors._export_head_artifact(
        world,
        anchors.StoreSubject(STORE_ID),
        store_root=root,
        seam=make_seam(heads),
    )

    assert anchors.decode_head_artifact(data) == anchors.HeadArtifact(
        anchors.StoreSubject(STORE_ID), digest("store-genesis"), digest("store-head")
    )


def test_export_refuses_a_store_genesis_mismatch(tmp_path):
    world, _recorder, _bindings, _roots = admitted_world(tmp_path)
    heads = Heads()
    root = store_root(tmp_path)
    heads.set(
        root,
        digest("store-genesis"),
        digest("store-head"),
        store_payload(OTHER_STORE_ID),
    )

    with pytest.raises(StoreIdMismatch):
        anchors._export_head_artifact(
            world,
            anchors.StoreSubject(STORE_ID),
            store_root=root,
            seam=make_seam(heads),
        )


# --- the audit path ----------------------------------------------------------


def store_audit(
    tmp_path,
    root: Path,
    view: logmodel.ChainView,
    *,
    observers: tuple = (),
) -> verify.LogReport:
    inspections, captures = Inspections(), Captures()
    inspections.set(root, view)
    return audit(
        config_for(tmp_path),
        anchors.StoreSubject(STORE_ID),
        root,
        inspections,
        captures,
        observers=observers,
    )


def test_store_audit_validated(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    report = store_audit(
        tmp_path, root, view, observers=(store_observer(view),)
    )
    assert report.outcome == "validated"
    assert not [finding for finding in report.findings if finding.severity == "error"]


def test_store_audit_refuted_on_truncation(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    # The anchor states the full head; the presented chain stops one short —
    # a valid prefix behind the store-subject registry anchor.
    truncated = logmodel.WellFormedView(
        genesis=view.genesis,
        entries=view.entries[:-1],
        tip=view.entries[-2].digest,
        pending=(),
    )
    report = store_audit(
        tmp_path, root, truncated, observers=(store_observer(view),)
    )
    assert report.outcome == "refuted"


def test_store_audit_refuted_on_chain_removal_under_registry_anchor(tmp_path):
    # Cut 9 L4 u1: the chain deleted outright, the store-subject record bound
    # by store_id still in the observer set.
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    report = store_audit(
        tmp_path, root, logmodel.AbsentView(), observers=(store_observer(view),)
    )
    assert report.outcome == "refuted"
    assert any(finding.code == "anchor-chain-absent" for finding in report.findings)


def test_store_audit_malformed_on_interior_damage(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    damaged = logmodel.MalformedView(
        logmodel.DefectView("cycle", view.tip, "an entry is its own ancestor")
    )
    report = store_audit(
        tmp_path, root, damaged, observers=(store_observer(view),)
    )
    assert report.outcome == "malformed"


def test_store_audit_unresolvable_on_empty_observers(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    report = store_audit(tmp_path, root, view)
    assert report.outcome == "unresolvable"


def test_store_audit_holds_one_boundary_across_inspect_capture_evaluate(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload())
    inspections, captures = Inspections(), Captures()
    inspections.set(root, view)
    held = _operation_lock_for(root)
    observed: list[str] = []

    def probe(_root: Path) -> None:
        with pytest.raises(BuildContended), held.capture():
            pass
        observed.append(str(held._holder))

    inspections.probe = probe
    captures.probe = probe

    audit(
        config_for(tmp_path),
        anchors.StoreSubject(STORE_ID),
        root,
        inspections,
        captures,
        observers=(store_observer(view),),
    )

    assert observed == ["writer", "writer"]
    assert held._holder is None


def test_store_genesis_form_is_validated(tmp_path):
    # A store subject over a corpus-domain genesis is structural damage: the
    # payload is not a store genesis at all.
    root = store_root(tmp_path)
    view = surfaced(root, "store", science_root.GENESIS_PAYLOAD)
    report = store_audit(
        tmp_path, root, view, observers=(store_observer(view),)
    )
    assert report.outcome == "malformed"
    assert any(finding.code == "genesis-form-invalid" for finding in report.findings)


def test_store_genesis_id_mismatch_is_a_subject_finding(tmp_path):
    root = store_root(tmp_path)
    view = surfaced(root, "store", store_payload(OTHER_STORE_ID))
    report = store_audit(
        tmp_path, root, view, observers=(store_observer(view),)
    )
    assert any(finding.code == "subject-mismatch" for finding in report.findings)


def test_store_subject_unsupported_is_deleted():
    assert not hasattr(science_errors, "StoreSubjectUnsupported")
    source = Path(verify.__file__).read_text(encoding="utf-8")
    assert "_refuse_store_subject" not in source
    assert "StoreSubjectUnsupported" not in source
