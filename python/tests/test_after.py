"""`read_after`: a chain's entries after a tip, read detached (spec 4.4).

Real engine, real volume: every root lives under `certified_work`. Pending and
malformed chains are fabricated by chain surgery, as the lifecycle suite does.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from atoms.chain.model import SettledEntry, decode_entry
from authority import FULL
from nodes.core.write_plan import CreateOp

from beliefs import root as science_root
from beliefs.after import AfterEntries, AfterUnavailable, read_after
from beliefs.root import init_corpus_root, log_seam
from beliefs.world.logmodel import WellFormedView


def _write(root: Path, name: str) -> None:
    science_root.durable_executor_factory()(root).execute([CreateOp(f"verification/{name}.md", f"# {name}\n".encode())])


def _corpus(work: Path, adds: int = 3, name: str = "corpus") -> tuple[Path, WellFormedView]:
    root = work / name
    init_corpus_root(root, authority=FULL)
    for index in range(adds):
        _write(root, f"v{index}")
    view = log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return root, view


def _listing(root: Path) -> dict[str, bytes]:
    directory = root / ".#~chain"
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def _unsettle(root: Path, tip: str) -> None:
    """Remove the tip settlement's leaf: its registration is left unsettled."""
    names = [name for name in _listing(root) if tip in name]
    assert len(names) == 1, names
    assert type(decode_entry(_listing(root)[names[0]])[1]) is SettledEntry
    (root / ".#~chain" / names[0]).unlink()


def test_after_genesis_returns_everything_after_it(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after=view.genesis.digest)
    assert result == AfterEntries(view.entries[1:], view.tip, view.pending)
    assert isinstance(result, AfterEntries)
    assert len(result.entries) == len(view.entries) - 1 > 1


def test_after_the_tip_is_empty(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after=view.tip)
    assert result == AfterEntries((), view.tip, view.pending)


def test_after_a_middle_entry_returns_the_rest(certified_work) -> None:
    root, view = _corpus(certified_work)
    middle = view.entries[2]
    result = read_after(root, genesis=view.genesis.digest, after=middle.digest)
    assert isinstance(result, AfterEntries)
    assert result.entries == view.entries[3:]


def test_through_bounds_the_slice(certified_work) -> None:
    root, view = _corpus(certified_work)
    after, through = view.entries[1].digest, view.entries[3].digest
    result = read_after(root, genesis=view.genesis.digest, after=after, through=through)
    assert result == AfterEntries(view.entries[2:4], through, view.pending)


def test_through_equal_to_after_is_empty(certified_work) -> None:
    root, view = _corpus(certified_work)
    digest = view.entries[2].digest
    result = read_after(root, genesis=view.genesis.digest, after=digest, through=digest)
    assert result == AfterEntries((), digest, view.pending)


def test_through_before_after(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after=view.entries[3].digest, through=view.entries[1].digest)
    assert isinstance(result, AfterUnavailable) and result.reason == "through-before-after"


def test_through_not_on_chain(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after=view.genesis.digest, through="f" * 64)
    assert isinstance(result, AfterUnavailable) and result.reason == "through-not-on-chain"


def test_tip_not_on_chain(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after="f" * 64)
    assert isinstance(result, AfterUnavailable) and result.reason == "tip-not-on-chain"


def test_genesis_mismatch(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis="f" * 64, after=view.tip)
    assert isinstance(result, AfterUnavailable) and result.reason == "genesis-mismatch"


def test_a_root_with_no_chain_is_an_absent_chain(certified_work) -> None:
    root = certified_work / "bare"
    root.mkdir()
    result = read_after(root, genesis="0" * 64, after="0" * 64)
    assert isinstance(result, AfterUnavailable) and result.reason == "chain-absent"


def test_a_missing_root_is_an_absent_chain(certified_work) -> None:
    result = read_after(certified_work / "nowhere", genesis="0" * 64, after="0" * 64)
    assert isinstance(result, AfterUnavailable) and result.reason == "chain-absent"


def test_a_malformed_chain(certified_work) -> None:
    root, view = _corpus(certified_work)
    victim = next(iter(_listing(root)))
    (root / ".#~chain" / victim).write_bytes(b"not an entry")
    result = read_after(root, genesis=view.genesis.digest, after=view.genesis.digest)
    assert isinstance(result, AfterUnavailable) and result.reason == "chain-malformed"


def test_read_after_appends_nothing(certified_work) -> None:
    root, view = _corpus(certified_work)
    before = _listing(root)
    read_after(root, genesis=view.genesis.digest, after=view.genesis.digest)
    assert _listing(root) == before


def test_read_after_appends_nothing_on_an_unsettled_registration(certified_work) -> None:
    root, full = _corpus(certified_work)
    _unsettle(root, full.tip)
    pending_view = log_seam().inspect_detached(root)
    assert type(pending_view) is WellFormedView and pending_view.pending
    before = _listing(root)
    result = read_after(root, genesis=pending_view.genesis.digest, after=pending_view.genesis.digest)
    assert isinstance(result, AfterEntries)
    assert result.pending == pending_view.pending
    assert _listing(root) == before
    bounded = read_after(
        root,
        genesis=pending_view.genesis.digest,
        after=pending_view.genesis.digest,
        through=pending_view.entries[2].digest,
    )
    assert isinstance(bounded, AfterEntries)
    assert bounded.entries == pending_view.entries[1:3]
    assert bounded.pending == pending_view.pending
    unavailable = read_after(root, genesis=pending_view.genesis.digest, after="f" * 64)
    assert isinstance(unavailable, AfterUnavailable) and unavailable.reason == "tip-not-on-chain"
    assert _listing(root) == before
    again = log_seam().inspect_detached(root)
    assert type(again) is WellFormedView and again.pending == pending_view.pending


def test_through_at_the_tip_returns_the_full_slice_after_genesis(certified_work) -> None:
    root, view = _corpus(certified_work)
    result = read_after(root, genesis=view.genesis.digest, after=view.genesis.digest, through=view.tip)
    assert isinstance(result, AfterEntries)
    assert [e.digest for e in result.entries] == [e.digest for e in view.entries[1:]]


def test_read_after_does_not_classify_a_mid_read_file_not_found_as_chain_absent(tmp_path, monkeypatch) -> None:
    from types import SimpleNamespace

    import beliefs.after as after_module

    root = tmp_path / "root"
    root.mkdir()

    def vanishing_leaf(_root: Path) -> object:
        raise FileNotFoundError("a chain leaf vanished mid-read")

    monkeypatch.setattr(after_module, "log_seam", lambda: SimpleNamespace(inspect_detached=vanishing_leaf))
    with pytest.raises(FileNotFoundError, match="vanished mid-read"):
        read_after(root, genesis="0" * 64, after="0" * 64)


def test_read_after_refuses_an_unexpected_view_type(tmp_path, monkeypatch) -> None:
    from types import SimpleNamespace

    import beliefs.after as after_module

    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(after_module, "log_seam", lambda: SimpleNamespace(inspect_detached=lambda _r: object()))
    with pytest.raises(TypeError, match="unexpected chain view"):
        read_after(root, genesis="0" * 64, after="0" * 64)
