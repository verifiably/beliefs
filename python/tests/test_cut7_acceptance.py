"""Portable guards for the cut-7 acceptance launcher.

The launcher itself is only exercised for real on the certified tuple, which
this suite is not allowed to require. What is portable is its *shape*: that it
refuses before probing when a required module is missing, that an uncertified
tuple is an error and not a skip, that cut 5 and cut 6 run first and stop the
command when they fail, and that only the third phase receives the caller's
arguments. Each of those is a way the command could silently report discharge it
did not earn.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "cut7_acceptance", Path(__file__).parents[1] / "tools" / "cut7_acceptance.py"
)
assert _SPEC is not None and _SPEC.loader is not None
cut7_acceptance = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cut7_acceptance)


def _surface(tmp_path: Path) -> Path:
    """A stand-in acceptance module and both prefix runners, so the command's
    own preconditions hold and the arm can be about something else."""
    n2 = tmp_path / "test_n2_cut7.py"
    n2.write_text("", encoding="utf-8")
    for runner in cut7_acceptance.PREFIX_RUNNERS:
        (tmp_path / runner).write_text("", encoding="utf-8")
    return n2


def _record(monkeypatch) -> list[dict[str, object]]:
    """Every `subprocess.run` the command makes, in order, recorded not run."""
    calls: list[dict[str, object]] = []

    def run(command, **keywords):
        calls.append({"command": command, **keywords})
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cut7_acceptance.subprocess, "run", run)
    return calls


def _staged(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cut7_acceptance, "ACCEPTANCE", tmp_path)
    monkeypatch.setattr(cut7_acceptance, "TOOLS", tmp_path)
    monkeypatch.setattr(cut7_acceptance, "work_directory", lambda: tmp_path)


def test_the_prefix_is_cut_five_then_cut_six():
    assert cut7_acceptance.PREFIX_RUNNERS == ("cut5_acceptance.py", "cut6_acceptance.py")


def test_missing_n2_module_refuses_before_certification_probe(tmp_path: Path, monkeypatch, capsys):
    _staged(tmp_path, monkeypatch)

    def unexpected_probe(_run: Path) -> str | None:
        raise AssertionError("certification probe ran without the required N2 module")

    monkeypatch.setattr(cut7_acceptance, "probe", unexpected_probe)

    assert cut7_acceptance.main([]) == 1
    assert "required acceptance module is missing" in capsys.readouterr().err


def test_missing_prefix_runner_refuses_before_certification_probe(tmp_path: Path, monkeypatch, capsys):
    _surface(tmp_path)
    (tmp_path / "cut6_acceptance.py").unlink()
    _staged(tmp_path, monkeypatch)

    def unexpected_probe(_run: Path) -> str | None:
        raise AssertionError("certification probe ran without both prefix runners")

    monkeypatch.setattr(cut7_acceptance, "probe", unexpected_probe)

    assert cut7_acceptance.main([]) == 1
    assert "required prefix runner is missing" in capsys.readouterr().err


def test_probe_refusal_returns_the_certification_error(tmp_path: Path, monkeypatch, capsys):
    _surface(tmp_path)
    _staged(tmp_path, monkeypatch)
    monkeypatch.setattr(cut7_acceptance, "probe", lambda _run: "PreconditionRefused: not certified")

    assert cut7_acceptance.main([]) == cut7_acceptance.PROBE_REFUSED
    refusal = capsys.readouterr().err
    assert "cut-7 acceptance cannot run here" in refusal
    assert "not a skip" in refusal
    assert not list(tmp_path.glob("run-*"))


def test_every_phase_runs_in_order_beneath_one_certified_run_directory(tmp_path: Path, monkeypatch):
    n2 = _surface(tmp_path)
    _staged(tmp_path, monkeypatch)
    probe_runs: list[Path] = []
    monkeypatch.setattr(cut7_acceptance, "probe", lambda run: probe_runs.append(run))
    calls = _record(monkeypatch)

    assert cut7_acceptance.main(["-k", "journey"]) == 0
    assert len(probe_runs) == 1
    run = probe_runs[0]

    assert [call["command"] for call in calls] == [
        [sys.executable, str(tmp_path / "cut5_acceptance.py")],
        [sys.executable, str(tmp_path / "cut6_acceptance.py")],
        [sys.executable, "-m", "pytest", str(n2), "-k", "journey"],
    ]
    for call in calls:
        assert call["cwd"] == cut7_acceptance.PYTHON_ROOT
        assert call["check"] is False
        environment = call["env"]
        assert isinstance(environment, dict)
        # The prior cuts are told only where to work, so their own defaults
        # cannot put them on a volume this command never probed.
        for name in ("SCIENCE_CUT5_ROOT", "SCIENCE_CUT6_ROOT"):
            assert environment[name] == str(run)

    phase_three = calls[-1]["env"]
    assert isinstance(phase_three, dict)
    for name in ("SCIENCE_CUT4_ROOT", "SCIENCE_CUT5_ROOT", "SCIENCE_CUT6_ROOT", "SCIENCE_CUT7_ROOT"):
        assert phase_three[name] == str(run)
    assert not list(tmp_path.glob("run-*"))


@pytest.mark.parametrize("failing", [0, 1])
def test_a_failing_prefix_stops_the_command_before_cut_sevens_arms(
    tmp_path: Path, monkeypatch, capsys, failing: int
):
    _surface(tmp_path)
    _staged(tmp_path, monkeypatch)
    monkeypatch.setattr(cut7_acceptance, "probe", lambda _run: None)
    attempted: list[str] = []

    def run_prefix(runner: str, _run: Path) -> int:
        attempted.append(runner)
        return 7 if runner == cut7_acceptance.PREFIX_RUNNERS[failing] else 0

    monkeypatch.setattr(cut7_acceptance, "run_prefix", run_prefix)

    def unexpected(_command, **_keywords):
        raise AssertionError("cut 7's arms ran behind a failing prefix")

    monkeypatch.setattr(cut7_acceptance.subprocess, "run", unexpected)

    assert cut7_acceptance.main([]) == 7
    assert attempted == list(cut7_acceptance.PREFIX_RUNNERS[: failing + 1])
    stopped = capsys.readouterr().err
    assert f"the {cut7_acceptance.PREFIX_RUNNERS[failing]} prefix exited 7" in stopped
    assert "cut 7 is\n  not discharged" in stopped
    assert not list(tmp_path.glob("run-*"))


@pytest.mark.parametrize("returncode", [0, 7])
def test_the_commands_result_is_cut_sevens_own_result(tmp_path: Path, monkeypatch, returncode: int):
    _surface(tmp_path)
    _staged(tmp_path, monkeypatch)
    monkeypatch.setattr(cut7_acceptance, "probe", lambda _run: None)
    monkeypatch.setattr(cut7_acceptance, "run_prefix", lambda _runner, _run: 0)

    def run(command, **_keywords):
        return subprocess.CompletedProcess(command, returncode)

    monkeypatch.setattr(cut7_acceptance.subprocess, "run", run)

    assert cut7_acceptance.main([]) == returncode


def test_probe_initializes_both_roots_and_removes_them_with_their_metadata(tmp_path: Path, monkeypatch):
    from beliefs import root
    from beliefs.world import WorldConfig

    worlds: list[WorldConfig] = []
    corpora: list[Path] = []

    def init_world(config: WorldConfig) -> None:
        worlds.append(config)
        config.world_root.mkdir()
        root.metadata_root_for(config.world_root).mkdir()

    def init_corpus(corpus_root: Path) -> None:
        corpora.append(Path(corpus_root))
        Path(corpus_root).mkdir()
        root.metadata_root_for(corpus_root).mkdir()

    monkeypatch.setattr(root, "init_world_root", init_world)
    monkeypatch.setattr(root, "init_corpus_root", init_corpus)

    assert cut7_acceptance.probe(tmp_path) is None
    assert len(worlds) == 1 and len(corpora) == 1
    assert worlds[0].world_root == (tmp_path / "probe-world").resolve()
    assert worlds[0].world_id == "0" * 32
    assert worlds[0].corpus_roots == ()
    assert corpora[0] == tmp_path / "probe-corpus"
    for probed in (tmp_path / "probe-world", tmp_path / "probe-corpus"):
        assert not probed.exists()
        assert not root.metadata_root_for(probed).exists()


def test_a_refusing_corpus_registration_is_reported_even_when_the_world_registers(
    tmp_path: Path, monkeypatch
):
    """A host can certify one act and refuse the other, and cut 7 writes to both."""
    from beliefs import root

    monkeypatch.setattr(root, "init_world_root", lambda config: config.world_root.mkdir())

    def refuse(_corpus_root: Path) -> None:
        raise RuntimeError("no barrier-option table")

    monkeypatch.setattr(root, "init_corpus_root", refuse)
    assert cut7_acceptance.probe(tmp_path) == "RuntimeError: no barrier-option table"
