"""Cut 5's family writes through the certified composition root."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from atoms.chain.model import (
    ChainOutcome,
    IntentEntry,
    RegisteredEntry,
    SettledEntry,
    decode_entry,
)
from authority import ACTOR, FULL
from fixtures_cut4 import path_for, reopen
from nodes.core.errors import ExecutionError

from beliefs import stored
from beliefs.corpus import standing_in_local_view, superseded_by
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus


def proposition(slug: str, operator: str = "affects"):
    return stored.proposition_node(slug, title=slug, claim={"operator": operator})


def chain_entries(root: Path):
    found = {}
    for path in (root / ".#~chain").iterdir():
        assert path.name != ".#~stage"
        previous, entry = decode_entry(path.read_bytes())
        found[path.name] = (previous, entry)

    successors = {previous: (digest, entry) for digest, (previous, entry) in found.items()}
    ordered = []
    previous = None
    while previous in successors:
        digest, entry = successors[previous]
        ordered.append((digest, entry))
        previous = digest
    assert len(ordered) == len(found)
    return tuple(ordered)


def test_supersede_survives_facade_reload(durable_writer, durable_root):
    predecessor = durable_writer.add(proposition("prior"))
    successor = durable_writer.supersede(proposition("successor", "causes"), of=predecessor.id)

    view = reopen(durable_root)
    assert view.get(successor.id) == successor
    assert superseded_by(view, predecessor.id) == (successor.id,)
    assert view.get(predecessor.id) == predecessor


def test_revise_survives_facade_reload_with_unchanged_stamp(durable_writer, durable_root):
    original = durable_writer.add(proposition("revised"))
    stamp = stored.stored_semantic_hash(original)

    durable_writer.revise(original.model_copy(update={"title": "revised title"}))

    reloaded = reopen(durable_root).get(original.id)
    assert reloaded.title == "revised title"
    assert stored.stored_semantic_hash(reloaded) == stamp


def test_retract_survives_facade_reload(durable_writer, durable_root):
    target = durable_writer.add(
        stored.verification_node(
            "retracted",
            title="retracted",
            assessment="assessment-identity",
            assessment_ref="assessment:a1",
            scope="clean-environment",
            verdict="passed",
        )
    )
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    retraction = stored.retraction_node(
        title="durable retraction",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=("source:acceptance",),
        actor=ACTOR,
        event_token="durable-retraction",
    )

    admitted = durable_writer.retract(retraction)

    view = reopen(durable_root)
    assert view.get(admitted.id) == admitted
    assert view.get(target.id) == target
    assert standing_in_local_view(view, target.id) is False


def test_import_bundle_records_the_exact_durable_chain(durable_root):
    writer = open_corpus(durable_root, authority=FULL)
    before = chain_entries(durable_root)

    report = writer.import_bundle(
        [proposition("imported-a"), proposition("imported-b")],
        observer="corpus",
        instrument="cut5",
        opened_at="T0",
        closed_at="T1",
    )

    after = chain_entries(durable_root)
    added = after[len(before) :]
    assert len(added) == 5
    assert tuple(type(entry) for _, entry in added) == (
        IntentEntry,
        RegisteredEntry,
        SettledEntry,
        RegisteredEntry,
        SettledEntry,
    )

    intent_digest, _ = added[0]
    payload_registration_digest, payload_registration = added[1]
    _, payload_settlement = added[2]
    report_registration_digest, report_registration = added[3]
    _, report_settlement = added[4]
    assert isinstance(payload_registration, RegisteredEntry)
    assert isinstance(payload_settlement, SettledEntry)
    assert isinstance(report_registration, RegisteredEntry)
    assert isinstance(report_settlement, SettledEntry)
    assert payload_registration.fulfills is None
    assert payload_settlement.registration == payload_registration_digest
    assert payload_settlement.outcome is ChainOutcome.COMMITTED
    assert report_registration.fulfills == intent_digest
    assert report_settlement.registration == report_registration_digest
    assert report_settlement.outcome is ChainOutcome.COMMITTED

    report_ref = f"act-report:{report.identity()}"
    reloaded_report = reopen(durable_root).get(report_ref)
    expected_report = stored.act_report_node(report)
    assert reloaded_report.facets == expected_report.facets
    assert stored.stored_semantic_hash(reloaded_report) == stored.stored_semantic_hash(expected_report)


def test_import_on_an_uncertified_tuple_refuses():
    shm = Path("/dev/shm")
    if not shm.is_dir():
        raise AssertionError(
            "/dev/shm is unavailable, so the uncertified-tuple family negative cannot run; "
            "this is an error and not a skip"
        )
    root = shm / f"science-cut5-uncertified-{os.getpid()}"
    try:
        with pytest.raises(Exception) as registration:
            init_corpus_root(root, authority=FULL)
        assert "allowlist" in str(registration.value) or "barrier-option" in str(registration.value)

        with pytest.raises(ExecutionError) as refused:
            open_corpus(root, authority=FULL).import_bundle(
                [proposition("uncertified")],
                observer="corpus",
                instrument="cut5",
                opened_at="T0",
                closed_at="T1",
            )
        assert (refused.value.index, refused.value.applied) == (None, 0)
        assert refused.value.__cause__ is not None
        assert not path_for(root, "proposition:uncertified").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)
