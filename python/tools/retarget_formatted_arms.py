"""Carry live N2 arms across a formatting-only change to the kernel.

An arm's sabotage is a `before` block that must occur exactly once in a kernel module. A
formatter that re-wraps the module leaves the block matching nothing, and the arm goes
stale. Its formatted twin is derived, not hand-written. Let `S0` be the module before
formatting, `S1` after, and `(b, a)` the audited sabotage. Then `T1 = ruff(S0.replace(b, a))`
is the formatted program the arm used to audit, and `(b', a')` is the smallest line-aligned
region where `S1` and `T1` differ, widened until `b'` is unique in `S1`. The derivation is
accepted only when `S1.replace(b', a') == T1` byte for byte, so the re-targeted arm mutates
exactly the formatted form of what its cut declared.

Spec: docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md §3.3. From `python/`:

    uv run --frozen python tools/retarget_formatted_arms.py derive --base <commit> --out <json> [--python]
    uv run --frozen python tools/retarget_formatted_arms.py verify --base <commit> --entries <json>

`derive` runs on the formatted tree before any re-target lands, with `--base` the commit
before formatting; `verify` runs after the guards carry the entries.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType

PYTHON_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PYTHON_ROOT.parent
TESTS = PYTHON_ROOT / "tests"
ACCEPTANCE = TESTS / "acceptance"

Formatter = Callable[[str], str]


class RetargetRefused(Exception):
    """An arm the derivation cannot carry across formatting without changing what it mutates."""


@dataclass(frozen=True)
class Retarget:
    """One live arm's formatted twin, with the sabotage it replaces."""

    guard: str
    index: int
    row: str
    module: str
    original_before: str
    original_after: str
    before: str
    after: str


def ruff_formatter(module: str) -> Formatter:
    """Format source as the project formats `src/beliefs/<module>`, with its own configuration."""

    def format_source(source: str) -> str:
        completed = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--stdin-filename", f"src/beliefs/{module}", "-"],
            input=source,
            capture_output=True,
            text=True,
            cwd=PYTHON_ROOT,
            check=False,
        )
        if completed.returncode != 0:
            raise RetargetRefused(f"{module}: ruff cannot format the sabotaged source: {completed.stderr.strip()}")
        return completed.stdout

    return format_source


def derive_one(original: str, formatted: str, before: str, after: str, format_source: Formatter) -> tuple[str, str]:
    """The `(before, after)` that applied to `formatted` yields `format_source(original.replace(before, after))`."""
    occurrences = original.count(before)
    if occurrences != 1:
        raise RetargetRefused(f"the sabotage's before occurs {occurrences} times in the source before formatting")
    target = format_source(original.replace(before, after))
    old = formatted.splitlines(keepends=True)
    new = target.splitlines(keepends=True)
    if old == new:
        raise RetargetRefused("the sabotage vanishes under formatting")
    shortest = min(len(old), len(new))
    head = 0
    while head < shortest and old[head] == new[head]:
        head += 1
    tail = 0
    while tail < shortest - head and old[-1 - tail] == new[-1 - tail]:
        tail += 1
    start, old_end, new_end = head, len(old) - tail, len(new) - tail
    while True:
        derived_before = "".join(old[start:old_end])
        if derived_before and formatted.count(derived_before) == 1:
            break
        if start == 0 and old_end == len(old):
            raise RetargetRefused("no unique region of the formatted source carries the sabotage")
        if start > 0:
            start -= 1
        if old_end < len(old):
            old_end += 1
            new_end += 1
    derived_after = "".join(new[start:new_end])
    if formatted.replace(derived_before, derived_after) != target:
        raise RetargetRefused("the derived arm does not reproduce the formatted sabotage")
    return derived_before, derived_after


def _machinery() -> tuple[ModuleType, ModuleType]:
    for directory in (TESTS, ACCEPTANCE):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    import arm_staleness
    import frozen_guards

    return arm_staleness, frozen_guards


def _source_at(commit: str, module: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:python/src/beliefs/{module}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RetargetRefused(f"{module} is not in {commit}")
    return completed.stdout


def derive(base: str) -> tuple[tuple[Retarget, ...], tuple[str, ...]]:
    """Every stale arm a live guard audits, carried across formatting from `base`; and the refusals."""
    arm_staleness, frozen_guards = _machinery()
    working = arm_staleness.working_tree(REPO_ROOT)
    entries: list[Retarget] = []
    refusals: list[str] = []
    for guard in frozen_guards.live_guards(REPO_ROOT):
        arms = arm_staleness.audited_arms(guard, repo_root=REPO_ROOT)
        audited = arm_staleness.audited_tree(guard, repo_root=REPO_ROOT)
        for stale in arm_staleness.stale_arms(guard.name, arms, audited):
            index = int(stale.key.rpartition("[")[2].removesuffix("]"))
            sabotage = arms[index].sabotage
            try:
                if sabotage.package != "beliefs":
                    raise RetargetRefused(f"a {sabotage.package} arm; only the beliefs kernel was formatted")
                formatted = working(sabotage.module)
                if formatted is None:
                    raise RetargetRefused(f"{sabotage.module} is not in the working tree")
                before, after = derive_one(
                    _source_at(base, sabotage.module),
                    formatted,
                    sabotage.before,
                    sabotage.after,
                    ruff_formatter(sabotage.module),
                )
            except RetargetRefused as refused:
                refusals.append(f"{guard.name}::{stale.key}: {refused}")
                continue
            entries.append(
                Retarget(
                    guard=guard.name,
                    index=index,
                    row=arms[index].row,
                    module=sabotage.module,
                    original_before=sabotage.before,
                    original_after=sabotage.after,
                    before=before,
                    after=after,
                )
            )
    return tuple(entries), tuple(refusals)


def verify(base: str, entries: Sequence[Retarget]) -> tuple[str, ...]:
    """Problems with the landed re-targets: each must re-derive identically and be what its guard audits."""
    arm_staleness, _ = _machinery()
    working = arm_staleness.working_tree(REPO_ROOT)
    problems: list[str] = []
    for entry in entries:
        label = f"{entry.guard}[{entry.index}] {entry.row}"
        try:
            expected = derive_one(
                _source_at(base, entry.module),
                working(entry.module) or "",
                entry.original_before,
                entry.original_after,
                ruff_formatter(entry.module),
            )
        except RetargetRefused as refused:
            problems.append(f"{label}: {refused}")
            continue
        if expected != (entry.before, entry.after):
            problems.append(f"{label}: re-derivation differs from the recorded entry")
        arm = arm_staleness.audited_arms(ACCEPTANCE / entry.guard, repo_root=REPO_ROOT)[entry.index]
        landed = (arm.row, arm.sabotage.module, arm.sabotage.before, arm.sabotage.after)
        if landed != (entry.row, entry.module, entry.before, entry.after):
            problems.append(f"{label}: the guard audits a different sabotage than the derived one")
    return tuple(problems)


def _literal(text: str, indent: str) -> str:
    lines = text.splitlines(keepends=True)
    if len(lines) <= 1:
        return repr(text)
    body = "".join(f"{indent}    {line!r}\n" for line in lines)
    return f"(\n{body}{indent})"


def render(entries: Sequence[Retarget]) -> str:
    """The entries as `_LIVE_SABOTAGES` dictionary items, grouped under a comment per guard."""
    out: list[str] = []
    for guard in dict.fromkeys(entry.guard for entry in entries):
        out.append(f"    # {guard}\n")
        for entry in (entry for entry in entries if entry.guard == guard):
            out.append(
                f"    {entry.row!r}: Sabotage(\n"
                f"        module={entry.module!r},\n"
                f"        before={_literal(entry.before, '        ')},\n"
                f"        after={_literal(entry.after, '        ')},\n"
                "    ),\n"
            )
    return "".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    derive_command = commands.add_parser("derive")
    derive_command.add_argument("--base", required=True)
    derive_command.add_argument("--out", required=True, type=Path)
    derive_command.add_argument("--python", action="store_true", help="also print the entries as table items")
    verify_command = commands.add_parser("verify")
    verify_command.add_argument("--base", required=True)
    verify_command.add_argument("--entries", required=True, type=Path)
    arguments = parser.parse_args(argv)

    if arguments.command == "derive":
        entries, refusals = derive(arguments.base)
        arguments.out.write_text(json.dumps([asdict(entry) for entry in entries], indent=1) + "\n", encoding="utf-8")
        if arguments.python:
            print(render(entries), end="")
        for refusal in refusals:
            print(f"refused: {refusal}", file=sys.stderr)
        print(f"{len(entries)} arms derived, {len(refusals)} refused", file=sys.stderr)
        return 1 if refusals else 0

    entries = tuple(Retarget(**item) for item in json.loads(arguments.entries.read_text(encoding="utf-8")))
    problems = verify(arguments.base, entries)
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    print(f"{len(entries)} entries verified, {len(problems)} problems", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
