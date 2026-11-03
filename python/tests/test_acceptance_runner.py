"""The acceptance runner: one process per module, probe first, old roots refused."""

from __future__ import annotations

from pathlib import Path

import acceptance_runner as runner
import pytest


def _python_root(tmp_path: Path, names: list[str]) -> Path:
    acceptance = tmp_path / "python" / "tests" / "acceptance"
    acceptance.mkdir(parents=True)
    for name in names:
        (acceptance / name).write_text("")
    return tmp_path / "python"


class _Completed:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def _record(monkeypatch, statuses: dict[str, int] | None = None) -> list[list[str]]:
    commands: list[list[str]] = []

    def fake_run(command, **_kwargs):
        commands.append(list(command))
        return _Completed((statuses or {}).get(Path(command[3]).name, 0))

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "_probe", lambda _run, _actor: None)
    return commands


def test_runs_every_acceptance_module_in_its_own_process_in_sorted_order(tmp_path, monkeypatch):
    root = _python_root(tmp_path, ["test_c.py", "test_a.py", "test_b.py"])
    commands = _record(monkeypatch)
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work", argv=["-k", "x"])
    assert status == 0
    assert [Path(c[3]).name for c in commands] == ["test_a.py", "test_b.py", "test_c.py"]
    assert all(c[1:3] == ["-m", "pytest"] for c in commands)
    assert [c[4:] for c in commands] == [[], [], ["-k", "x"]]


def test_stops_at_the_first_failing_module_and_returns_its_status(tmp_path, monkeypatch):
    root = _python_root(tmp_path, ["test_a.py", "test_b.py", "test_c.py"])
    commands = _record(monkeypatch, {"test_b.py": 1})
    assert runner.run_acceptance(python_root=root, work=tmp_path / "work", argv=[]) == 1
    assert [Path(c[3]).name for c in commands] == ["test_a.py", "test_b.py"]


def test_probe_refusal_is_an_error_naming_the_variable(tmp_path, monkeypatch, capsys):
    root = _python_root(tmp_path, ["test_a.py"])
    commands = _record(monkeypatch)
    monkeypatch.setattr(runner, "_probe", lambda _run, _actor: "CapabilityUnavailable: tmpfs")
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work", argv=[])
    err = capsys.readouterr().err
    assert status == runner.PROBE_REFUSED and commands == []
    assert "BELIEFS_ACCEPTANCE_ROOT" in err and "not a skip" in err and "tmpfs" in err


def test_an_old_cut_root_variable_is_refused(tmp_path, monkeypatch, capsys):
    message = runner.refuse_old_roots({"SCIENCE_CUT4_ROOT": "/x"})
    assert message is not None
    assert "SCIENCE_CUT4_ROOT" in message and "BELIEFS_ACCEPTANCE_ROOT" in message
    ten = runner.refuse_old_roots({"SCIENCE_CUT10_ROOT": ""})
    assert ten is not None and "SCIENCE_CUT10_ROOT" in ten and "BELIEFS_TEST_ROOT" in ten
    other = runner.refuse_old_roots({"SCIENCE_CUT7_ROOT": "/x"})
    assert other is not None and "BELIEFS_ACCEPTANCE_ROOT" in other and "BELIEFS_TEST_ROOT" in other
    assert runner.refuse_old_roots({"BELIEFS_TEST_ROOT": "/x", "SCIENCE_ROOT": "/y"}) is None

    called: list[object] = []
    monkeypatch.setattr(runner, "run_acceptance", lambda **kw: called.append(kw) or 0)
    monkeypatch.setenv("SCIENCE_CUT4_ROOT", "/x")
    assert runner.main([]) == runner.OLD_ROOT_REFUSED
    assert called == [] and "SCIENCE_CUT4_ROOT" in capsys.readouterr().err


@pytest.mark.parametrize("create", [True, False])
def test_no_acceptance_modules_is_an_error(tmp_path, monkeypatch, capsys, create):
    root = tmp_path / "python"
    if create:
        (root / "tests" / "acceptance").mkdir(parents=True)
    else:
        root.mkdir()
    commands = _record(monkeypatch)
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work", argv=[])
    err = capsys.readouterr().err
    assert status == runner.NO_MODULES and status != 0 and commands == []
    assert str(root / "tests" / "acceptance") in err
