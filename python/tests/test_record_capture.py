"""The no-follow, classified, bounded captured-record surface (spec §3.1)."""

import errno
import os
from pathlib import Path

from science.world import records


def _corpus(root: Path) -> Path:
    for namespace in records.RECORD_NAMESPACES:
        (root / namespace).mkdir(parents=True)
    return root


def test_captures_each_record_file_sorted(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    (root / "act-report" / "b.md").write_bytes(b"report-bytes")
    assert records.capture_records(root, "corpus") == (
        ("act-report/b.md", b"report-bytes"),
        ("run/a.md", b"run-bytes"),
    )


def test_world_and_store_kinds_capture_nothing(certified_work) -> None:
    assert records.capture_records(certified_work, "world") == ()
    assert records.capture_records(certified_work, "store") == ()


def test_leaf_symlink_is_classified_and_withheld(certified_work) -> None:
    root = _corpus(certified_work / "root")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    (root / "run" / "a.md").symlink_to(outside)
    assert records.capture_records(root, "corpus") == ()


def test_intermediate_symlink_directory_is_withheld(certified_work) -> None:
    root = _corpus(certified_work / "root")
    elsewhere = certified_work / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "x.md").write_bytes(b"OUTSIDE")
    (root / "run").rmdir()
    (root / "run").symlink_to(elsewhere)
    assert records.capture_records(root, "corpus") == ()


def test_fifo_is_classified_never_opened_readable(certified_work) -> None:
    root = _corpus(certified_work / "root")
    os.mkfifo(root / "run" / "a.md")
    assert records.capture_records(root, "corpus") == ()


def test_swap_race_is_lost_by_the_attacker(certified_work, monkeypatch) -> None:
    root = _corpus(certified_work / "root")
    target = root / "run" / "a.md"
    target.write_bytes(b"genuine")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    orderings: list[str] = []
    real_seam = records._leaf_seam

    def swap(path: str) -> None:
        orderings.append(f"enumerated:{path}")
        target.unlink()
        target.symlink_to(outside)
        orderings.append(f"swapped:{path}")
        real_seam(path)

    monkeypatch.setattr(records, "_leaf_seam", swap)
    captured = records.capture_records(root, "corpus")
    assert captured == ()
    assert orderings == ["enumerated:run/a.md", "swapped:run/a.md"]
    assert b"OUTSIDE" not in b"".join(payload for _, payload in captured)


def test_ceiling_boundary_exact_captures_one_over_withholds(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "exact.md").write_bytes(b"x" * records.RECORD_CEILING)
    (root / "run" / "over.md").write_bytes(
        b"x" * (records.RECORD_CEILING + 1)
    )
    captured = dict(records.capture_records(root, "corpus"))
    assert set(captured) == {"run/exact.md"}
    assert len(captured["run/exact.md"]) == records.RECORD_CEILING


def _five(root: Path) -> Path:
    for namespace in (*records.RECORD_NAMESPACES, "verification", "assessment"):
        (root / namespace).mkdir(parents=True, exist_ok=True)
    return root


def test_capture_surface_records_equal_capture_records_over_the_default_namespaces(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    (root / "act-report" / "b.md").write_bytes(b"report-bytes")
    surface = records.capture_surface(root, records.RECORD_NAMESPACES)
    assert surface.records == records.capture_records(root, "corpus")
    assert surface.withheld == surface.unreadable == surface.uninspectable == ()


def test_capture_surface_reads_the_namespaces_it_is_given(certified_work) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    (root / "assessment" / "a.md").write_bytes(b"a")
    (root / "run" / "r.md").write_bytes(b"r")
    surface = records.capture_surface(root, ("verification", "assessment"))
    assert surface.records == (("assessment/a.md", b"a"), ("verification/v.md", b"v"))
    assert records.capture_records(root, "corpus") == (("run/r.md", b"r"),)


def test_a_non_corpus_root_holding_run_records_still_captures_nothing(certified_work) -> None:
    root = _corpus(certified_work / "not-a-corpus")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    assert records.capture_records(root, "world") == ()
    assert records.capture_records(root, "store") == ()


def test_an_oversized_regular_file_is_withheld_and_named(certified_work) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "exact.md").write_bytes(b"x" * records.RECORD_CEILING)
    (root / "verification" / "big.md").write_bytes(b"x" * (records.RECORD_CEILING + 1))
    surface = records.capture_surface(root, ("verification",))
    assert [path for path, _ in surface.records] == ["verification/exact.md"]
    assert surface.withheld == ("verification/big.md",)
    assert surface.unreadable == surface.uninspectable == ()


def test_an_unreadable_regular_file_is_named_not_dropped(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user: root ignores file modes"
    root = _five(certified_work / "root")
    target = root / "verification" / "locked.md"
    target.write_bytes(b"secret")
    target.chmod(0)
    try:
        surface = records.capture_surface(root, ("verification",))
    finally:
        target.chmod(0o644)
    assert surface.records == ()
    assert surface.unreadable == ("verification/locked.md",)
    assert surface.withheld == surface.uninspectable == ()


def test_an_unenumerable_namespace_is_uninspectable_and_an_absent_one_is_silent(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user: root ignores directory modes"
    root = _five(certified_work / "root")
    (root / "assessment").rmdir()
    locked = root / "verification"
    (locked / "v.md").write_bytes(b"v")
    locked.chmod(0)
    try:
        surface = records.capture_surface(root, ("verification", "assessment"))
    finally:
        locked.chmod(0o755)
    assert surface.records == ()
    assert surface.uninspectable == ("verification",)
    assert surface.withheld == surface.unreadable == ()


def test_symlinks_and_fifos_stay_silent_in_capture_surface(certified_work) -> None:
    root = _five(certified_work / "root")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    (root / "verification" / "link.md").symlink_to(outside)
    os.mkfifo(root / "verification" / "pipe.md")
    surface = records.capture_surface(root, ("verification",))
    assert surface == records.CapturedSurface((), (), (), ())


class _FailingEntry:
    """A directory entry whose classification raises — the `DirEntry.is_dir`
    failure the descent must name rather than leak."""

    def __init__(self, name: str, error: OSError) -> None:
        self.name = name
        self._error = error

    def is_dir(self, follow_symlinks: bool = True) -> bool:
        raise self._error


class _Scan:
    def __init__(self, entries) -> None:
        self._entries = entries

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def __iter__(self):
        return iter(self._entries)


def test_a_directory_entry_whose_classification_fails_is_unreadable(certified_work, monkeypatch) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    real_scandir = os.scandir

    def scandir(fd):
        with real_scandir(fd) as scan:
            names = [entry.name for entry in scan]
        return _Scan([_FailingEntry(name, OSError(errno.EIO, "injected")) for name in names])

    monkeypatch.setattr(records.os, "scandir", scandir)
    surface = records.capture_surface(root, ("verification",))
    assert surface.records == ()
    assert surface.unreadable == ("verification/v.md",)
    assert surface.withheld == surface.uninspectable == ()


def test_a_scandir_failure_is_uninspectable_unless_it_is_enoent(certified_work, monkeypatch) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    for code, expected in ((errno.EACCES, ("verification",)), (errno.ENOENT, ())):

        def scandir(fd, code=code):
            raise OSError(code, "injected")

        monkeypatch.setattr(records.os, "scandir", scandir)
        surface = records.capture_surface(root, ("verification",))
        assert surface.records == ()
        assert surface.uninspectable == expected, code


def test_close_failures_are_silent_without_retries(certified_work, monkeypatch) -> None:
    root = _five(certified_work / "root")
    (root / "verification" / "v.md").write_bytes(b"v")
    real_close = os.close
    for failure_at in range(4):
        calls = 0

        def close(fd: int, failure_at: int = failure_at) -> None:
            nonlocal calls
            calls += 1
            real_close(fd)
            if calls == failure_at + 1:
                raise OSError(errno.EIO, "injected close failure")

        monkeypatch.setattr(records.os, "close", close)
        assert records.capture_surface(root, ("verification",)) == records.CapturedSurface(
            (("verification/v.md", b"v"),), (), (), ()
        )
        assert calls == 4


def test_the_log_evaluator_surface_is_pinned(certified_work) -> None:
    # cut 11's captured surface: the three namespaces, silent on every failure.
    root = _five(certified_work / "root")
    (root / "run" / "ok.md").write_bytes(b"ok")
    (root / "run" / "big.md").write_bytes(b"x" * (records.RECORD_CEILING + 1))
    (root / "verification" / "v.md").write_bytes(b"v")
    assert records.capture_records(root, "corpus") == (("run/ok.md", b"ok"),)
