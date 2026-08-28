"""The no-follow, classified, bounded captured-record surface (spec §3.1)."""

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
