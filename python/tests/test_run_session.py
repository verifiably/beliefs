"""The run-session constructor: an admissible ceiling, recorded, and no tree writes."""

from __future__ import annotations

import json

import pytest
from profiles import BASE
from test_session_claim import _claimable, _one_corpus, _session_dirs, _store

from beliefs.errors import RunSessionRefused, SessionClosed, SessionRefused
from beliefs.permit import RequiredCapabilities, WritePermit
from beliefs.root import log_seam
from beliefs.session import open_attended_session, open_ledger_reader, open_run_session
from beliefs.session.ledger import ledger_path

CEILING = WritePermit(
    frozenset({"proposition", "run", "act-report", "holdings-observation"}),
    frozenset({"corpus-write", "run", "holdings"}),
)
HOLDINGS = RequiredCapabilities.for_kinds({"holdings-observation"}, {})
DIGEST = "d" * 64


def test_the_ceiling_is_recorded_in_session_open(certified_work):
    config, root = _one_corpus(certified_work)
    session = open_run_session(config, certified_work / "ops", write_root=root, profile=BASE, ceiling=CEILING)
    try:
        assert session.run is True
        first = ledger_path(certified_work / "ops", session.session_id).read_text().splitlines()[0]
        assert WritePermit.from_json(json.loads(first)["permit"]) == CEILING
    finally:
        session.close()


def test_an_attended_session_is_not_a_run_session(certified_work):
    config, root = _one_corpus(certified_work)
    session = open_attended_session(config, certified_work / "ops", write_root=root, profile=BASE)
    try:
        assert session.run is False
    finally:
        session.close()


@pytest.mark.parametrize(
    "ceiling",
    [
        WritePermit(frozenset(), frozenset({"corpus-write"}), True),
        WritePermit(frozenset(), frozenset({"corpus-write", "publish"})),
        WritePermit(frozenset(), frozenset({"lifecycle"})),
        WritePermit(frozenset(), frozenset({"registry"})),
    ],
)
def test_an_inadmissible_ceiling_refuses_before_anything_is_created(certified_work, ceiling):
    config, root = _one_corpus(certified_work)
    store = _store(certified_work)
    ops = certified_work / "ops"
    with pytest.raises(SessionRefused):
        open_run_session(config, ops, write_root=root, profile=BASE, ceiling=ceiling, store_root=store)
    assert _session_dirs(ops) == []
    assert _claimable(root, "write root") and _claimable(store, "store root")


def test_tree_writes_are_refused_under_a_run_session(certified_work):
    config, root = _one_corpus(certified_work)
    store = _store(certified_work)
    ops = certified_work / "ops"
    session = open_run_session(config, ops, write_root=root, profile=BASE, ceiling=CEILING, store_root=store)
    try:
        session.claim_invocation("A", "hold", DIGEST)
        writer = session.scoped(HOLDINGS, "A")
        corpus_before = log_seam().inspect_detached(root)
        store_before = log_seam().inspect_detached(store)
        with pytest.raises(RunSessionRefused) as refused:
            writer.seal_acquisition(None, instrument="test")  # type: ignore[arg-type]
        assert refused.value.operation == "tree-write" and not isinstance(refused.value, SessionClosed)
        ctx = writer.holdings_context(instrument="test")
        with pytest.raises(RunSessionRefused) as refused:
            ctx.seam.store_create(store, "objects/sha256/aa/aa", b"x", "f" * 64)
        assert refused.value.operation == "tree-write"
        assert log_seam().inspect_detached(root) == corpus_before
        assert log_seam().inspect_detached(store) == store_before
        assert not session._ledger.failed
        assert open_ledger_reader(ops, session.session_id).acts() == ()
    finally:
        session.close()


def test_an_attended_seal_acquisition_is_not_refused_by_the_run_rule(certified_work):
    config, root = _one_corpus(certified_work)
    store = _store(certified_work)
    session = open_attended_session(config, certified_work / "ops", write_root=root, profile=BASE, store_root=store)
    try:
        session.claim_invocation("A", "hold", DIGEST)
        writer = session.scoped(HOLDINGS, "A")
        with pytest.raises(Exception) as caught:
            writer.seal_acquisition(None, instrument="test")  # type: ignore[arg-type]
        assert not isinstance(caught.value, RunSessionRefused)
    finally:
        session.close()
