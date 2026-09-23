"""Portable behavior checks for the shared cut 23/24 acceptance runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import cut23_acceptance as cut23
import cut24_acceptance as cut24
import cut33_acceptance as cut33
import cut34_acceptance as cut34
import cut35_acceptance as cut35
import cut36_acceptance as cut36
import cut37_acceptance as cut37
import cut38_acceptance as cut38
import cut39_acceptance as cut39
import pytest

from beliefs import root


@pytest.mark.parametrize(
    ("runner", "cut", "accounting"),
    (
        (cut23, 23, (25, 8, 8)),
        (cut24, 24, (20, 5, 5)),
        (cut33, 33, (11, 11, 3)),
        (cut34, 34, (17, 17, 2)),
        (cut35, 35, (28, 27, 8)),
        (cut36, 36, (18, 16, 3)),
        (cut37, 37, (15, 11, 1)),
        (cut38, 38, (14, 12, 3)),
        (cut39, 39, (14, 13, 5)),
    ),
    ids=("cut23", "cut24", "cut33", "cut34", "cut35", "cut36", "cut37", "cut38", "cut39"),
)
def test_recent_runner_preserves_commands_environment_and_cleanup(
    runner, cut: int, accounting: tuple[int, int, int], tmp_path: Path, monkeypatch, capsys
) -> None:
    actors: list[str] = []
    calls: list[tuple[list[str], dict[str, Any]]] = []
    monkeypatch.setenv(f"SCIENCE_CUT{cut}_ROOT", str(tmp_path))
    monkeypatch.setattr(
        root,
        "init_corpus_root",
        lambda _corpus_root, *, authority: actors.append(authority.actor),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs))
        or subprocess.CompletedProcess(command, 0),
    )

    assert runner.main(["-k", "one"]) == 0

    prefix = runner.PREFIX_RUNNERS[0]
    modules = runner.PHASE_MODULES
    run = Path(calls[1][1]["env"][f"SCIENCE_CUT{cut}_ROOT"])
    assert actors == [f"cut{cut}-probe"]
    assert [call[0] for call in calls] == [
        [sys.executable, str(runner.TOOLS / prefix)],
        [sys.executable, "-m", "pytest", str(runner.ACCEPTANCE / modules[0])],
        [sys.executable, "-m", "pytest", str(runner.ACCEPTANCE / modules[1]), "-k", "one"],
    ]
    assert all(call[1]["cwd"] == runner.PYTHON_ROOT and call[1]["check"] is False for call in calls)
    assert calls[0][1]["env"][f"SCIENCE_CUT{cut - 1}_ROOT"] == str(run)
    for _command, keywords in calls[1:]:
        environment = keywords["env"]
        assert all(environment[f"SCIENCE_CUT{number}_ROOT"] == str(run) for number in range(4, cut + 1))
    assert not run.exists()
    output = capsys.readouterr().out
    assert [f"[cut{cut} phase {phase}/3]" in output for phase in range(1, 4)] == [True, True, True]
    assert f"declared arms: {accounting[0]} (= {accounting[1]} declaration units; {accounting[2]} guarantee rows)" in output

    if cut == 33:
        assert "guarantee rows exercised: 3 (2 newly closed: C7, C3; C10 remains partial)" in output
    if cut == 34:
        assert "guarantee rows exercised: 2 (2 newly closed: C8, C9; the mutation lane has no open boundary)" in output
    if cut == 35:
        assert "guarantee rows exercised: 8 (6 newly closed: H4, G9, R10, T5, T1, T4; T2 and T7 partial)" in output
    if cut == 36:
        assert "guarantee rows exercised: 3 (3 newly closed: L8, L4, L10; L1 re-homed to persistence-cut, partial)" in output
    if cut == 37:
        assert "guarantee rows exercised: 1 (1 newly closed: L13; row 5 partial for L1 under persistence-cut)" in output
    if cut == 38:
        assert (
            "guarantee rows exercised: 3 (1 newly closed: T2; T5 and T6 re-read for the new kinds; T7 partial under cross-root-publication)" in output
        )
    if cut == 39:
        assert "guarantee rows exercised: 5 (5 newly closed: W17, Y1, Y2, Y3, Y4)" in output


@pytest.mark.parametrize(("runner", "cut"), ((cut23, 23), (cut24, 24)), ids=("cut23", "cut24"))
def test_recent_runner_refuses_a_missing_module_before_work(
    runner, cut: int, tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv(f"SCIENCE_CUT{cut}_ROOT", str(tmp_path))
    monkeypatch.setattr(runner, "PHASE_MODULES", ("missing.py",))

    assert runner.main([]) == 1
    assert f"cut-{cut} required acceptance module is missing" in capsys.readouterr().err
    assert not list(tmp_path.glob("run-*"))


@pytest.mark.parametrize(("runner", "cut"), ((cut23, 23), (cut24, 24)), ids=("cut23", "cut24"))
def test_recent_runner_propagates_prefix_failure(runner, cut: int, tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setenv(f"SCIENCE_CUT{cut}_ROOT", str(tmp_path))
    monkeypatch.setattr(root, "init_corpus_root", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **_kwargs: calls.append(command) or subprocess.CompletedProcess(command, 9),
    )

    assert runner.main([]) == 9
    assert calls == [[sys.executable, str(runner.TOOLS / runner.PREFIX_RUNNERS[0])]]
    assert not list(tmp_path.glob("run-*"))
