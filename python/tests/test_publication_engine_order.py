"""The engine order the publication judgment relies on (publication-records
design §6): a registration is in the chain before its create effect runs, and
an effect failure after registration rolls back durably. Tests may import
`atoms`; only `root.py` does among the source modules."""

from __future__ import annotations

import os
import shutil
from hashlib import sha256
from itertools import count
from pathlib import Path

import pytest
from atoms.coordinator.effects import create_file  # the effect execute.py applies, patched as atoms' own tests do
from authority import FULL
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import CreateOp, ReplaceOp
from profiles import BASE, pins_for

from beliefs.corpus import CorpusWriter, OperationPort
from beliefs.root import init_corpus_root, log_seam, metadata_root_for, open_corpus
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView

_counter = count()


@pytest.fixture()
def durable_root(certified_work):
    """`certified_work` (tests/conftest.py:133) is the certified volume for the
    portable tree; `work_directory` exists only under tests/acceptance/."""
    # Resolved: the engine opens roots with no symlink in the path (ELOOP otherwise).
    root = (certified_work / f"engine-order-{os.getpid()}-{next(_counter)}").resolve()
    try:
        init_corpus_root(root, authority=FULL)
        open_corpus(root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _port(writer: CorpusWriter) -> OperationPort:
    port = writer._operation_port
    assert port is not None, "open_corpus binds the durable operation port"
    return port


def _registrations_unlocked(root: Path) -> list[RegisteredEntryView]:
    """The registrations the chain holds, read without the project lock the
    running lease already holds: the detached inspector is a read-only scan."""
    view = log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return [entry for entry in view.entries if type(entry) is RegisteredEntryView]


def test_a_registration_is_in_the_chain_before_its_create_effect_runs(durable_root, monkeypatch):
    seen: list[bool] = []
    apply = create_file.apply

    def observing(*args, **kwargs):
        # A detached inspection: a read-only scan that takes no lock (the lease holds
        # the project lock) and runs no recovery, so it sees only entries already appended.
        seen.append(
            any(path == "probe/a.md" for entry in _registrations_unlocked(durable_root) for path, _ in entry.final)
        )
        return apply(*args, **kwargs)

    monkeypatch.setattr(create_file, "apply", observing)
    port = _port(open_corpus(durable_root, authority=FULL, profile=BASE))
    port.execute([CreateOp(path="probe/a.md", content=b"probe\n")])
    assert seen == [True]


def test_an_effect_failure_after_registration_rolls_back_durably(durable_root, monkeypatch):
    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(create_file, "apply", failing)
    port = _port(open_corpus(durable_root, authority=FULL, profile=BASE))
    with pytest.raises(ExecutionError, match="cut after registration"):
        port.execute([CreateOp(path="probe/b.md", content=b"probe\n")])
    monkeypatch.undo()
    # Detached first: no recovery runs, so the rolled-back settlement read here was
    # written by the failing execution itself, not by a recovery at read time.
    for view in (log_seam().inspect_detached(durable_root), log_seam().inspect_registered(durable_root)):
        assert type(view) is WellFormedView
        assert view.pending == ()
        (registration,) = [
            e for e in view.entries if type(e) is RegisteredEntryView and any(p == "probe/b.md" for p, _ in e.final)
        ]
        (settlement,) = [
            e for e in view.entries if type(e) is SettledEntryView and e.registration == registration.digest
        ]
        assert settlement.committed is False
    assert not (durable_root / "probe/b.md").exists()


def test_a_rolled_back_fulfilment_leaves_the_intent_open_for_a_retry(durable_root, monkeypatch):
    """Probed through `execute_fulfilling_guarded`, the call the binding door
    makes. `execute_fulfilling` would misreport: its `_registration_for`
    (root.py:1062-1076) raises unless exactly one registration fulfils the
    intent, and after a rollback and a retry there are two. The engine itself
    refuses only a prior *committed* fulfilment (`atoms`
    `coordinator/commands.py` `_require_admissible_fulfills`, line 314)."""
    writer = open_corpus(durable_root, authority=FULL, profile=BASE)
    port = _port(writer)
    digest = writer._append_operation_intent("audit", "f" * 32, FULL.actor)
    plan = [CreateOp(path="probe/c.md", content=b"one\n")]

    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(create_file, "apply", failing)
    with pytest.raises(ExecutionError, match="cut after registration"):
        port.execute_fulfilling_guarded(plan, digest, guard=lambda _view: None, fallback=lambda _reason: plan)
    monkeypatch.undo()
    before = _fulfilling(durable_root, digest)
    assert [committed for _, committed in before] == [False]
    retry_refused = None
    try:
        port.execute_fulfilling_guarded(plan, digest, guard=lambda _view: None, fallback=lambda _reason: plan)
    except ExecutionError as caught:  # recorded, not swallowed: the verdict below reads it
        retry_refused = caught
    after = _fulfilling(durable_root, digest)
    if retry_refused is not None:
        # "refused" only when the engine appended nothing for the retry
        assert after == before, f"the retry failed after registering: {retry_refused!r}"
        pytest.fail(f"RETRY_AFTER_ROLLBACK = fresh intent: {retry_refused!r}")
    assert [committed for _, committed in after] == [False, True]
    assert (durable_root / "probe/c.md").read_bytes() == b"one\n"


def _fulfilling(root: Path, digest: str) -> list[tuple[str, bool | None]]:
    """Every registration fulfilling `digest`, in chain order, with its settlement."""
    view = log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    settled = {e.registration: e.committed for e in view.entries if type(e) is SettledEntryView}
    return [
        (e.digest, settled.get(e.digest))
        for e in view.entries
        if type(e) is RegisteredEntryView and e.fulfills == digest
    ]


def test_a_live_registered_root_reads_well_formed_detached(durable_root):
    """The judgment reads every mounted root but the written one with the
    read-only detached inspector (spec §6, planning note): no recovery runs,
    so nothing is appended to a root this process does not lock."""
    writer = open_corpus(durable_root, authority=FULL, profile=BASE)
    _port(writer).execute([CreateOp(path="probe/d.md", content=b"d\n")])
    registered, detached = log_seam().inspect_registered(durable_root), log_seam().inspect_detached(durable_root)
    assert type(registered) is WellFormedView
    assert type(detached) is WellFormedView
    assert [e.digest for e in detached.entries] == [e.digest for e in registered.entries]


def test_the_engine_rewrites_a_file_it_never_registered(durable_root):
    """REPLACE_UNREGISTERED: accepted iff this passes. The rewrite must commit a
    registration whose own `initial` is already a file."""
    path = durable_root / "probe" / "e.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"raw\n")  # no registration creates it
    port = _port(open_corpus(durable_root, authority=FULL, profile=BASE))
    port.execute([ReplaceOp(path="probe/e.md", content=b"rewritten\n", expected_digest=sha256(b"raw\n").hexdigest())])
    view = log_seam().inspect_registered(durable_root)
    assert type(view) is WellFormedView
    (entry,) = [
        e for e in view.entries if type(e) is RegisteredEntryView and any(p == "probe/e.md" for p, _ in e.final)
    ]
    assert dict(entry.initial)["probe/e.md"] != log_seam().absent_state  # the pre-state is a file
    (settlement,) = [e for e in view.entries if type(e) is SettledEntryView and e.registration == entry.digest]
    assert settlement.committed is True
    assert path.read_bytes() == b"rewritten\n"
