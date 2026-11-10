"""Every line a session writes reads under autonomy's `ledger.v1` key sets.

autonomy reads beliefs's session ledgers with its own reader. The key sets below
are copied from that reader as a literal fixture rather than imported, so a
change on either side shows up here as a failure to reconcile by hand."""

from __future__ import annotations

import json
from typing import Any

import pytest
from test_operation_writes import proposition
from test_run_session import CEILING
from test_session_routes import BOTH, STORE_ID, FakeSeam
from test_session_seal import GENESIS_DIGEST, STUB_VIEW, WAIT
from test_session_writer import DIGEST, make_session

from beliefs.holdings.boundary import write
from beliefs.holdings.records import StoreLocator
from beliefs.session import writer as writer_module
from beliefs.session.ledger import ledger_path

AUTONOMY_KEYS: dict[str, frozenset[str]] = {
    "session-open": frozenset({"line", "session", "actor", "world", "permit", "at"}),
    "invocation-open": frozenset({"line", "invocation", "command", "input_digest", "at"}),
    "act": frozenset({"line", "invocation", "corpus", "entry", "intent", "records"}),
    "invocation-close": frozenset({"line", "invocation", "outcome"}),
    "session-close": frozenset({"line", "at"}),
    "select": frozenset({"line", "invocation", "project"}),
}


@pytest.mark.parametrize("run", [False, True], ids=["attended", "run"])
def test_every_line_a_session_writes_has_autonomys_key_set(tmp_path, monkeypatch, run: bool):
    seam = FakeSeam(tmp_path / "corpus")
    session, _ports = make_session(
        tmp_path,
        ceiling=CEILING if run else None,
        store_root=tmp_path / "store",
        store_id=STORE_ID,
        holdings_seam=seam.build(),
        run=run,
    )
    session.claim_invocation("A", "hold", DIGEST)
    scoped = session.scoped(BOTH, "A")
    scoped.add(proposition("p"))
    write(scoped.holdings_context(instrument="test"), StoreLocator(STORE_ID, "p.bin"), b"bytes")
    if run:
        from types import SimpleNamespace

        monkeypatch.setattr(writer_module, "log_seam", lambda: SimpleNamespace(inspect_detached=lambda _r: STUB_VIEW))
        tips = session.seal(WAIT)
        assert tips.corpus.tip == GENESIS_DIGEST
    session.close_invocation("A", {"done": []})
    session.close()

    raw = ledger_path(session.operations_root, session.session_id).read_bytes()
    assert raw.endswith(b"\n")
    lines: list[dict[str, Any]] = [json.loads(chunk) for chunk in raw.split(b"\n")[:-1]]
    kinds = [line["line"] for line in lines]
    assert kinds == ["session-open", "invocation-open", "act", "act", "act", "invocation-close", "session-close"]
    for line in lines:
        assert line["line"] in AUTONOMY_KEYS, line
        expected = AUTONOMY_KEYS[line["line"]]
        if line["line"] == "session-open" and "project" in line:
            expected = expected | {"project"}
        assert set(line) == expected, line
    if run:
        assert lines[0]["permit"]["ungoverned"] is False
    assert [line["corpus"] for line in lines if line["line"] == "act"] == [
        session.corpus_id,
        STORE_ID,
        session.corpus_id,
    ]
