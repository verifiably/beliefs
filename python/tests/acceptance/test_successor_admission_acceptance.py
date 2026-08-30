"""Cut 12's durable arms that need a live boundary, a chain mutation, or a
second writer: G4u11 (snapshot coherence), R12u1–u2, L7u14."""

from __future__ import annotations

import dataclasses
import threading
import time

import pytest
from closure_fixtures import make_closure
from succession_fixtures import (
    admit,
    append_assessment_intent,
    assessment,
    corpus,
    publish,
    seam,
    specs,
    verification,
)
from test_world_log_audit import corpus_anchor, real_audit

from beliefs.errors import AdmissionEvidenceRefused
from beliefs.runrecord import publication_plan
from beliefs.spec import SuccessorAdmitted, SuccessorRefused
from beliefs.succession import admit_spec_successor
from beliefs.world import anchors, registry
from beliefs.world.logmodel import MalformedView, RegisteredEntryView, WellFormedView

CHAIN_LEAF = ".#~chain"
CORPUS_ID = "a" * 32


def test_u11_a_writer_arriving_during_the_act_waits_and_is_not_consulted(certified_work) -> None:
    """The writer starts only once the act holds the root's operation lock —
    the seam's `inspect_registered` runs inside that hold, and the interposed
    seam starts the writer there. The writer queues behind the act (the lock
    admits one holder); the act's derivation never sees the blocker; the
    writer lands after the verdict; the next act consults it."""
    root, port = corpus(certified_work, "snapshot")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    blocker = verification("v1", target, "failed")
    order: list[str] = []

    def write_blocker() -> None:
        # The exported durable port is itself a production writer. Its raw
        # mutation must queue on the exact lock the admission act holds.
        order.append("writer-started")
        publish(port, target, blocker)
        order.append("writer-done")

    production = seam()
    writer = threading.Thread(target=write_blocker)

    def inspect_then_start_writer(path):
        view = production.inspect_registered(path)  # we are inside the act's hold
        writer.start()
        while "writer-started" not in order:
            time.sleep(0.01)
        time.sleep(0.5)  # the writer has had every chance to publish; the hold denies it
        assert "writer-done" not in order, "the writer published while the act held the lock"
        order.append("act-read")
        return view

    interposed = dataclasses.replace(production, inspect_registered=inspect_then_start_writer)
    verdict = admit_spec_successor(unreferenced, original, seam=interposed, root=root)
    order.append("act-done")
    writer.join(timeout=60)
    assert not writer.is_alive(), "the writer never got the lock after the act released it"
    assert isinstance(verdict, SuccessorAdmitted)
    assert order.index("act-read") < order.index("act-done") < order.index("writer-done")
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_u14_a_kill_between_append_and_execution_blocks_the_successor(certified_work) -> None:
    # The port seam is the kill point: the intent is durable, no member act ran.
    root, port = corpus(certified_work, "kill")
    original, unreferenced, referencing = specs()
    intent = append_assessment_intent(port, original.identity)
    view = seam().inspect_registered(root)
    assert type(view) is WellFormedView
    assert view.tip == intent
    assert not (root / "run").exists()
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def _leaf(root, digest: str):
    return root / CHAIN_LEAF / digest


def test_r12u1_an_excised_intent_entry_reads_malformed_and_the_act_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "excised")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity)
    _, _, plan = publication_plan(make_closure(spec=original.identity))
    port.execute_fulfilling(plan, intent)  # a registration now follows the intent
    intact = seam().inspect_registered(root)
    assert type(intact) is WellFormedView
    successor = next(
        entry.digest
        for entry in intact.entries
        if type(entry) is RegisteredEntryView and entry.fulfills == intent
    )
    _leaf(root, intent).unlink()
    view = seam().inspect_registered(root)
    assert type(view) is MalformedView, view
    # Cut 12 §5 item 5: the defect names the excised entry's successor — the
    # registration whose predecessor is now missing — and its class.
    assert (view.defect.kind, view.defect.subject) == ("missing-predecessor", successor)
    with pytest.raises(AdmissionEvidenceRefused) as refused:
        admit(root, unreferenced, original)
    assert refused.value.reason == "chain not well-formed"


def test_r12u2_a_truncated_chain_reads_refuted_under_an_anchor_and_the_act_admits(certified_work) -> None:
    root, port = corpus(certified_work, "truncated")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity)
    before = seam().inspect_registered(root)
    assert type(before) is WellFormedView and before.tip == intent
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)
    anchor = corpus_anchor(before, CORPUS_ID)
    _leaf(root, intent).unlink()  # the intent was the tip: a valid prefix remains
    after = seam().inspect_registered(root)
    assert type(after) is WellFormedView and after.tip == before.genesis.digest
    config = registry.WorldConfig(certified_work / "world", "0" * 32, (root,))
    report = real_audit(config, anchors.CorpusSubject(CORPUS_ID), root, observers=(anchor,))
    assert report.outcome == "refuted"
    assert "anchor-unreachable" in [finding.code for finding in report.findings]
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)
