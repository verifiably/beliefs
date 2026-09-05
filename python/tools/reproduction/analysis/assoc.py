"""One within-dataset association, standard library only, refusing malformed input.

Reads a wide, tab-separated expression matrix (a header row of sample ids,
one row per feature, gzipped or not), takes the one row named `value_row`,
derives each sample's group from the token after the last `group_separator`
in its id, compares the two groups by a Mann-Whitney U (normal
approximation), and writes stats.tsv and outcome.txt — the latter exactly one
of supported/refuted/inconclusive. Any malformation exits non-zero, so the
boundary reports execution-failed and no outcome exists.
"""

from __future__ import annotations

import gzip
import math
import pathlib
import sys

ALPHA = 0.05
MIN_PER_GROUP = 3


class MalformedInput(Exception):
    pass


def _open(path):
    path = pathlib.Path(path)
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return open(path, encoding="utf-8", newline="")


def load(path, *, value_row: str, group_separator: str = "_") -> dict[str, list[float]]:
    with _open(path) as handle:
        header_line = handle.readline()
        if not header_line:
            raise MalformedInput("empty file: no header row")
        header = header_line.rstrip("\r\n").split("\t")
        if len(header) < 2:
            raise MalformedInput(f"header names no sample columns: {header}")
        samples = header[1:]
        groups_of: list[str] = []
        for sample in samples:
            group = sample.rsplit(group_separator, 1)[-1] if group_separator in sample else ""
            if not group:
                raise MalformedInput(f"sample {sample!r} carries no group token after {group_separator!r}")
            groups_of.append(group)
        row: list[str] | None = None
        for number, line in enumerate(handle, start=2):
            fields = line.rstrip("\r\n").split("\t")
            if fields and fields[0] == value_row:
                if row is not None:
                    raise MalformedInput(f"line {number}: row {value_row!r} appears more than once")
                row = fields
                row_number = number
    if row is None:
        raise MalformedInput(f"row {value_row!r} is absent from the matrix")
    if len(row) != len(header):
        raise MalformedInput(f"line {row_number}: {len(row) - 1} values for {len(samples)} samples")
    groups: dict[str, list[float]] = {}
    for sample, group, raw in zip(samples, groups_of, row[1:]):
        try:
            value = float(raw)
        except ValueError as error:
            raise MalformedInput(f"line {row_number}, sample {sample!r}: {raw!r} is not a number") from error
        if not math.isfinite(value):
            raise MalformedInput(f"line {row_number}, sample {sample!r}: {raw!r} is not finite")
        groups.setdefault(group, []).append(value)
    if not groups:
        raise MalformedInput("no data values")
    return groups


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float]:
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b], key=lambda t: t[0])
    ranks: dict[int, float] = {}
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    r_a = sum(ranks[k] for k, (_, g) in enumerate(pooled) if g == 0)
    n_a, n_b = len(a), len(b)
    u_a = r_a - n_a * (n_a + 1) / 2
    mu = n_a * n_b / 2
    sigma = math.sqrt(n_a * n_b * (n_a + n_b + 1) / 12)
    if sigma == 0:
        raise MalformedInput("degenerate groups: zero variance in the rank statistic")
    z = (u_a - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p


def decide(groups: dict[str, list[float]], *, positive_level: str) -> tuple[str, float, float, int]:
    levels = sorted(groups)
    if len(levels) != 2:
        raise MalformedInput(f"expected exactly two levels, found {levels}")
    if positive_level not in groups:
        raise MalformedInput(f"positive level {positive_level!r} is not among {levels}")
    for level, values in groups.items():
        if len(values) < MIN_PER_GROUP:
            raise MalformedInput(f"group {level!r} has {len(values)} values; at least {MIN_PER_GROUP} are required")
    other = next(level for level in levels if level != positive_level)
    z, p = mann_whitney(groups[positive_level], groups[other])
    outcome = "inconclusive" if p >= ALPHA else ("supported" if z > 0 else "refuted")
    return outcome, z, p, sum(len(v) for v in groups.values())


def main(inp: str, stats_out: str, outcome_out: str, value_row: str, group_separator: str, positive_level: str) -> int:
    try:
        groups = load(inp, value_row=value_row, group_separator=group_separator)
        outcome, z, p, n = decide(groups, positive_level=positive_level)
    except MalformedInput as error:
        print(f"malformed input: {error}", file=sys.stderr)
        return 3
    pathlib.Path(stats_out).write_text(f"z\tp\tn\n{z}\t{p}\t{n}\n")
    pathlib.Path(outcome_out).write_text(outcome + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("usage: assoc.py <matrix> <stats.tsv> <outcome.txt> <value_row> <group_separator> <positive_level>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:7]))
