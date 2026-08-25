"""Portable guards for the cut-6 acceptance launcher."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "cut6_acceptance", Path(__file__).parents[1] / "tools" / "cut6_acceptance.py"
)
assert _SPEC is not None and _SPEC.loader is not None
cut6_acceptance = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cut6_acceptance)


def _n2_module(directory: Path) -> Path:
    n2 = directory / "test_n2_cut6.py"
    n2.write_text("", encoding="utf-8")
    return n2


def test_missing_n2_module_refuses_before_certification_probe(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cut6_acceptance, "ACCEPTANCE", tmp_path)
    monkeypatch.setattr(cut6_acceptance, "work_directory", lambda: tmp_path)

    def unexpected_probe(_run: Path) -> str | None:
        raise AssertionError("certification probe ran without the required N2 module")

    monkeypatch.setattr(cut6_acceptance, "probe", unexpected_probe)

    assert cut6_acceptance.main([]) == 1
    assert "required acceptance module is missing" in capsys.readouterr().err


def test_probe_refusal_returns_the_certification_error(tmp_path: Path, monkeypatch, capsys):
    _n2_module(tmp_path)
    monkeypatch.setattr(cut6_acceptance, "ACCEPTANCE", tmp_path)
    monkeypatch.setattr(cut6_acceptance, "work_directory", lambda: tmp_path)
    monkeypatch.setattr(cut6_acceptance, "probe", lambda _run: "PreconditionRefused: not certified")

    assert cut6_acceptance.main([]) == cut6_acceptance.PROBE_REFUSED
    assert "cut-6 acceptance cannot run here" in capsys.readouterr().err
    assert not list(tmp_path.glob("run-*"))


@pytest.mark.parametrize("returncode", [0, 7])
def test_pytest_receives_the_certified_run_directory_and_its_result(
    tmp_path: Path, monkeypatch, returncode: int
):
    n2 = _n2_module(tmp_path)
    monkeypatch.setattr(cut6_acceptance, "ACCEPTANCE", tmp_path)
    monkeypatch.setattr(cut6_acceptance, "work_directory", lambda: tmp_path)
    probe_runs: list[Path] = []

    def probe(run: Path) -> None:
        probe_runs.append(run)

    monkeypatch.setattr(cut6_acceptance, "probe", probe)
    captured: dict[str, object] = {}

    def run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, returncode)

    monkeypatch.setattr(cut6_acceptance.subprocess, "run", run)

    assert cut6_acceptance.main(["-q"]) == returncode
    assert len(probe_runs) == 1
    run_root = probe_runs[0]
    command = captured["command"]
    assert command == [sys.executable, "-m", "pytest", str(n2), "-q"]
    assert captured["cwd"] == cut6_acceptance.PYTHON_ROOT
    assert captured["check"] is False
    environment = captured["env"]
    assert isinstance(environment, dict)
    for name in ("SCIENCE_CUT4_ROOT", "SCIENCE_CUT5_ROOT", "SCIENCE_CUT6_ROOT"):
        assert environment[name] == str(run_root)
    assert not list(tmp_path.glob("run-*"))


def test_probe_initializes_a_world_and_removes_its_root_and_metadata(tmp_path: Path, monkeypatch):
    from science import root
    from science.world import WorldConfig

    seen: list[WorldConfig] = []

    def initialize(config: WorldConfig) -> None:
        seen.append(config)
        config.world_root.mkdir()
        root.metadata_root_for(config.world_root).mkdir()

    monkeypatch.setattr(root, "init_world_root", initialize)

    assert cut6_acceptance.probe(tmp_path) is None
    assert len(seen) == 1
    assert seen[0].world_root == (tmp_path / "probe-world").resolve()
    assert seen[0].world_id == "0" * 32
    assert seen[0].corpus_roots == ()
    assert not (tmp_path / "probe-world").exists()
    assert not root.metadata_root_for(tmp_path / "probe-world").exists()
