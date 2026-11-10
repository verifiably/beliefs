"""The chain claim: one session per written chain per host (spec 4.2, row E15).

Each session holds an exclusive `flock` on its write root and on its store root
when it has one. A second session on either, from this process or another, is
refused `ChainClaimed`; `close()` and process death release the claim. The
opening path owns every claim and the ledger until it returns, so an opening
that fails after both claims leaves both roots claimable.
"""

from __future__ import annotations

import errno
import os
import select
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from authority import FULL
from profiles import BASE, pins_for

import beliefs.session as session_module
import beliefs.session.claim as claim_module
from beliefs.errors import ChainClaimed, SessionLedgerFailed, SessionRefused
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus
from beliefs.session import open_attended_session
from beliefs.session.claim import ChainRole, claim_chain
from beliefs.session.ledger import LedgerWriter, ledger_path
from beliefs.world.registry import WorldConfig

WORLD = "e" * 32


def _adopted(root: Path) -> Path:
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    return root


def _world(work: Path, *roots: Path) -> WorldConfig:
    config = WorldConfig(work / "world", WORLD, roots)
    init_world_root(config, authority=FULL)
    return config


def _one_corpus(work: Path) -> tuple[WorldConfig, Path]:
    root = _adopted(work / "corpus")
    return _world(work, root), root


def _store(work: Path, name: str = "store") -> Path:
    store = work / name
    init_store_root(store, authority=FULL)
    return store


def _session_dirs(ops: Path) -> list[str]:
    sessions = ops / "sessions"
    return sorted(entry.name for entry in sessions.iterdir()) if sessions.is_dir() else []


def _claimable(root: Path, role: ChainRole) -> bool:
    try:
        claim = claim_chain(root, role)
    except ChainClaimed:
        return False
    claim.release()
    return True


# --- in-process --------------------------------------------------------------
def test_a_second_session_on_the_write_root_is_refused(certified_work):
    config, root = _one_corpus(certified_work)
    ops = certified_work / "ops"
    first = open_attended_session(config, ops, write_root=root, profile=BASE)
    try:
        with pytest.raises(ChainClaimed) as refused:
            open_attended_session(config, ops, write_root=root, profile=BASE)
        assert isinstance(refused.value, SessionRefused)
        assert refused.value.role == "write root" and refused.value.root == root
        assert _session_dirs(ops) == [first.session_id]
    finally:
        first.close()


def test_close_releases_the_claim(certified_work):
    config, root = _one_corpus(certified_work)
    ops = certified_work / "ops"
    first = open_attended_session(config, ops, write_root=root, profile=BASE)
    assert not _claimable(root, "write root")
    first.close()
    assert _claimable(root, "write root")
    second = open_attended_session(config, ops, write_root=root, profile=BASE)
    second.close()
    first.close()  # idempotent: releases nothing a second time
    assert _claimable(root, "write root")


def test_close_after_a_ledger_failure_releases_the_claim(certified_work):
    config, root = _one_corpus(certified_work)
    store = _store(certified_work)
    session = open_attended_session(config, certified_work / "ops", write_root=root, profile=BASE, store_root=store)
    session._ledger.fail("injected")
    with pytest.raises(SessionLedgerFailed):
        session.close()
    assert _claimable(root, "write root") and _claimable(store, "store root")


def test_a_claimed_store_root_refuses_and_releases_the_write_root(certified_work):
    first_root, second_root = _adopted(certified_work / "a"), _adopted(certified_work / "b")
    config = _world(certified_work, first_root, second_root)
    store, ops = _store(certified_work), certified_work / "ops"
    first = open_attended_session(config, ops, write_root=first_root, profile=BASE, store_root=store)
    try:
        with pytest.raises(ChainClaimed) as refused:
            open_attended_session(config, ops, write_root=second_root, profile=BASE, store_root=store)
        assert refused.value.role == "store root" and refused.value.root == store
        assert _session_dirs(ops) == [first.session_id]
        assert _claimable(second_root, "write root")
    finally:
        first.close()


def test_the_same_root_through_a_symlink_conflicts(certified_work):
    """The claim binds the directory, not the name it was reached by: a write
    root through a link resolves to the claimed root, and a claim taken through
    a link conflicts with the session's."""
    first_root, second_root = _adopted(certified_work / "a"), _adopted(certified_work / "b")
    config = _world(certified_work, first_root, second_root)
    store, ops = _store(certified_work), certified_work / "ops"
    root_link, store_link = certified_work / "a-link", certified_work / "store-link"
    root_link.symlink_to(first_root)
    store_link.symlink_to(store)
    first = open_attended_session(config, ops, write_root=first_root, profile=BASE, store_root=store)
    try:
        with pytest.raises(ChainClaimed) as through_root_link:
            claim_chain(root_link, "write root")
        assert through_root_link.value.root == root_link
        with pytest.raises(ChainClaimed) as through_write_link:
            open_attended_session(config, ops, write_root=root_link, profile=BASE)
        assert through_write_link.value.role == "write root"
        # A store root reached through a link is refused before any claim (the
        # engine opens it without following links), so the claim is probed directly.
        with pytest.raises(ChainClaimed) as through_store_link:
            claim_chain(store_link, "store root")
        assert through_store_link.value.root == store_link
        assert _session_dirs(ops) == [first.session_id]
    finally:
        first.close()


def test_two_corpora_without_a_store_both_open(certified_work):
    first_root, second_root = _adopted(certified_work / "a"), _adopted(certified_work / "b")
    config = _world(certified_work, first_root, second_root)
    ops = certified_work / "ops"
    first = open_attended_session(config, ops, write_root=first_root, profile=BASE)
    second = open_attended_session(config, ops, write_root=second_root, profile=BASE)
    first.close()
    second.close()


# --- across processes ------------------------------------------------------------
_CHILD = textwrap.dedent(
    """
    import sys
    from pathlib import Path

    from beliefs.errors import ChainClaimed
    from beliefs.profile import shipped_base
    from beliefs.session import open_attended_session
    from beliefs.world.registry import WorldConfig

    world, world_id, root, ops, mode = sys.argv[1:]
    config = WorldConfig(Path(world), world_id, (Path(root),))
    try:
        session = open_attended_session(config, Path(ops), write_root=Path(root), profile=shipped_base())
    except ChainClaimed as refused:
        print(f"refused {refused.role}", flush=True)
        sys.exit(3)
    print("held", flush=True)
    if mode == "hold":
        sys.stdin.read()
    session.close()
    """
)


def _child(work: Path, config: WorldConfig, root: Path, mode: str, **kwargs) -> subprocess.Popen[str]:
    home = work / "child-home"
    home.mkdir(exist_ok=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(home)}
    kwargs.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(config.world_root), config.world_id, str(root), str(work / "ops"), mode],
        env=env,
        cwd=str(home),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **kwargs,
    )


def _communicate_bounded(child: subprocess.Popen[str], timeout: float = 120) -> tuple[str, str]:
    try:
        return child.communicate(timeout=timeout)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=60)
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream is not None:
                stream.close()


def test_a_second_session_from_another_process_is_refused(certified_work):
    config, root = _one_corpus(certified_work)
    first = open_attended_session(config, certified_work / "ops", write_root=root, profile=BASE)
    try:
        child = _child(certified_work, config, root, "once")
        out, err = _communicate_bounded(child)
        assert child.returncode == 3, err
        assert out.strip() == "refused write root"
    finally:
        first.close()
    child = _child(certified_work, config, root, "once")
    out, err = _communicate_bounded(child)
    assert child.returncode == 0 and out.strip() == "held", err


def test_a_killed_holder_releases(certified_work):
    config, root = _one_corpus(certified_work)
    ops = certified_work / "ops"
    holder = _child(certified_work, config, root, "hold", stdin=subprocess.PIPE)
    try:
        assert holder.stdout is not None
        ready, _, _ = select.select([holder.stdout], [], [], 60)
        assert ready, "holder child did not report readiness within 60 s"
        line = holder.stdout.readline()
        assert line.strip() == "held", holder.stderr.read() if holder.stderr else ""
        with pytest.raises(ChainClaimed):
            open_attended_session(config, ops, write_root=root, profile=BASE)
        holder.send_signal(signal.SIGKILL)
        holder.wait(timeout=60)
        assert holder.returncode == -signal.SIGKILL
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=60)
        for stream in (holder.stdin, holder.stdout, holder.stderr):
            if stream is not None:
                stream.close()
    open_attended_session(config, ops, write_root=root, profile=BASE).close()


# --- the opening path owns what it acquires -------------------------------------------
def _fail_session_directory(monkeypatch, ops: Path) -> None:
    original = Path.mkdir

    def mkdir(self, *args, **kwargs):
        if self.parent == ops / "sessions":
            raise OSError(errno.EIO, "injected session-directory failure", str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)


def _fail_session_open(monkeypatch, _ops: Path) -> None:
    original = LedgerWriter.append
    calls = []

    def append(self, line):
        calls.append(line)
        if len(calls) == 1:
            raise OSError(errno.EIO, "injected session-open failure")
        return original(self, line)

    monkeypatch.setattr(LedgerWriter, "append", append)


def _fail_reconciliation(monkeypatch, _ops: Path) -> None:
    def reconcile_sessions(*_args, **_kwargs):
        raise RuntimeError("injected reconciliation failure")

    monkeypatch.setattr(session_module, "reconcile_sessions", reconcile_sessions)


def _open_fd_targets() -> set[Path]:
    targets: set[Path] = set()
    for entry in os.listdir("/proc/self/fd"):
        try:
            targets.add(Path(os.readlink(f"/proc/self/fd/{entry}")))
        except OSError:
            continue
    return targets


@pytest.mark.parametrize(
    ("inject", "raised", "ledger_written"),
    [
        (_fail_session_directory, OSError, False),
        (_fail_session_open, OSError, True),
        (_fail_reconciliation, RuntimeError, True),
    ],
    ids=["session-directory", "session-open", "reconciliation"],
)
def test_an_opening_failure_after_both_claims_releases_them(
    certified_work, monkeypatch, inject, raised, ledger_written
):
    config, root = _one_corpus(certified_work)
    store, ops = _store(certified_work), certified_work / "ops"
    with monkeypatch.context() as patch:
        inject(patch, ops)
        with pytest.raises(raised, match="injected"):
            open_attended_session(config, ops, write_root=root, profile=BASE, store_root=store)
    write_claim = claim_chain(root, "write root")
    store_claim = claim_chain(store, "store root")
    write_claim.release()
    store_claim.release()
    ids = _session_dirs(ops)
    if ledger_written:
        (failed,) = ids
        failed_ledger = ledger_path(ops, failed)
        assert failed_ledger.is_file()  # an unclosed ledger reads as an interrupted session
        assert failed_ledger.resolve() not in _open_fd_targets()
    else:
        assert ids == []
    open_attended_session(config, ops, write_root=root, profile=BASE, store_root=store).close()


def test_a_failed_flock_leaks_no_descriptor(certified_work, monkeypatch):
    root = certified_work / "root"
    root.mkdir()

    def flock(_fd, _operation):
        raise OSError(errno.EIO, "injected flock failure")

    before = len(os.listdir("/proc/self/fd"))
    monkeypatch.setattr(claim_module.fcntl, "flock", flock)
    with pytest.raises(OSError, match="injected flock failure"):
        claim_chain(root, "write root")
    assert len(os.listdir("/proc/self/fd")) == before


def test_a_refused_claim_leaks_no_descriptor(certified_work):
    root = certified_work / "root"
    root.mkdir()
    held = claim_chain(root, "write root")
    try:
        before = len(os.listdir("/proc/self/fd"))
        with pytest.raises(ChainClaimed):
            claim_chain(root, "write root")
        assert len(os.listdir("/proc/self/fd")) == before
    finally:
        held.release()
    held.release()  # idempotent
    assert _claimable(root, "write root")
