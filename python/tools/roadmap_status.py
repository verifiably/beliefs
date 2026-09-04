"""Live status of every guarantee row, from the cuts' own accounting.

Spec: docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md §3.1.
A row's historical status is the highest it reached across the cuts' full/part
accounting; its live status overrides that to open where a later source names
the row open at a widened obligation. Run from `python/`:

    uv run python tools/roadmap_status.py
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location(
    "test_designs_corpus", ROOT / "python" / "tests" / "test_designs_corpus.py"
)
assert _spec is not None and _spec.loader is not None
_corpus = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_corpus)
GUARANTEE_TABLES: dict[str, list[str]] = _corpus.GUARANTEE_TABLES

#: Each cut's rows read in full and in part, with the section that states them.
#: Cut 3's live table is §4 (15 full, 19 part); its Appendix A preserves the
#: pre-amendment 17/17 table and is not a source.
ACCOUNTING: dict[int, tuple[str, str, str]] = {
    1: ("review-disposition-and-conformance-cut-1 §5", "M4, M7, M9, M10, M11, M13", "M5"),
    2: ("conformance-cut-2 §4", "G1, G2b, G6, P2–P9, M6, M8", "G2c, G3, G8, G9, S5, S6, P1, D3, D6, D7, N2"),
    3: ("conformance-cut-3 §4 (not Appendix A)",
        "G2a, G4, M2, R1, R3, R6, R7, R8, R11, R14, R17, R18, T3, T6, T8",
        "G9, N2, R2, R4, R5, R9, R10, R12, R13, R16, R19, R20, R21, R22, R23, T1, T2, T4, T5"),
    4: ("conformance-cut-4 §4.1 and §4.2", "S7, S8, W3", "G9, N2, R19, R22, R23, S1, S1a, S5"),
    5: ("conformance-cut-5 accounting", "S2, S3, S4, G7, C1, C2, C4, C5", "M5, T1, T2, M3, R20, C3, C6, C10, G2c, G8"),
    6: ("conformance-cut-6 accounting", "X4, X6", "X5, W13"),
    7: ("conformance-cut-7 accounting", "X1, X3, X7, X8, X9, X10, X11", "X2, X5, X12, W8a"),
    8: ("conformance-cut-8-results §1", "L3, L5, L9, L11, L12", "L1, L2, L4, L7, L8, L10, L13"),
    9: ("conformance-cut-9-results §1", "L6", "L2, L4, L10, W13"),
    10: ("conformance-cut-10-results §1", "H1, H2, H3", "H4, G9, L7, L10"),
    11: ("conformance-cut-11-results §1", "", "L7"),
    12: ("conformance-cut-12-results §1", "G4, R12", "L7"),
    13: ("conformance-cut-13-results §1", "R4, R9, R13, R15", "R16, R21"),
    14: ("conformance-cut-14-results §1", "W11, W12, W18", "W13, W17"),
    15: ("conformance-cut-15-results §1", "R2, R16, R20, R21", "R23"),
    16: ("conformance-cut-16-results §2", "W5, G3, D7, T8", "W16, C3, R23, M3, T2"),
}

#: Rows a later source names open at a widened obligation, overriding a full read.
REOPENED: dict[str, tuple[str, int]] = {}

_RANGE = re.compile(r"([GSWRCXNLDMPHT])([0-9]+[a-z]?)–\1?([0-9]+[a-z]?)")


def _expand(cell: str) -> set[str]:
    rows: set[str] = set()
    for token in (t.strip() for t in cell.split(",") if t.strip()):
        span = _RANGE.fullmatch(token)
        if span:
            table = GUARANTEE_TABLES[span.group(1)]
            start = table.index(span.group(1) + span.group(2))
            end = table.index(span.group(1) + span.group(3))
            rows.update(table[start : end + 1])
        else:
            rows.add(token)
    return rows


KNOWN_ROWS: frozenset[str] = frozenset(r for t in GUARANTEE_TABLES.values() for r in t)


def _check_known(rows: set[str], where: str) -> None:
    unknown = sorted(rows - KNOWN_ROWS)
    if unknown:
        raise SystemExit(f"{where} names rows that are not guarantee rows: {unknown}")


def live_status() -> dict[str, tuple[str, int]]:
    status: dict[str, tuple[str, int]] = {}
    for source, full, part in ACCOUNTING.values():
        _check_known(_expand(full) | _expand(part), source)
    _check_known(set(REOPENED), "REOPENED")
    for cut, (_, full, part) in ACCOUNTING.items():
        for row in _expand(full):
            status[row] = ("full", cut)
        for row in _expand(part):
            if status.get(row, ("", 0))[0] != "full":
                status[row] = ("part", cut)
    for row, (_, cut) in REOPENED.items():
        status[row] = ("reopened", cut)
    for table in GUARANTEE_TABLES.values():
        for row in table:
            status.setdefault(row, ("never", 0))
    return status


def main() -> None:
    status = live_status()
    total = sum(len(t) for t in GUARANTEE_TABLES.values())
    closed = sum(1 for s, _ in status.values() if s == "full")
    print("| table | never selected | part — last cut that read it | reopened |")
    print("|---|---|---|---|")
    for prefix, table in GUARANTEE_TABLES.items():
        never = ", ".join(r for r in table if status[r][0] == "never") or "—"
        part = ", ".join(f"{r} (cut {status[r][1]})" for r in table if status[r][0] == "part") or "—"
        reopened = ", ".join(f"{r} (cut {status[r][1]})" for r in table if status[r][0] == "reopened") or "—"
        print(f"| {prefix} | {never} | {part} | {reopened} |")
    print()
    print(f"Closed {closed} of {total}; open {total - closed}.")


if __name__ == "__main__":
    main()
