"""The acceptance runner: one process per module, probe first, old roots refused."""

from __future__ import annotations

import os
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
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def _record(
    monkeypatch,
    statuses: dict[str, int] | None = None,
    outputs: dict[str, str] | None = None,
) -> list[list[str]]:
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        assert kwargs.get("stdout") == runner.subprocess.PIPE
        assert kwargs.get("stderr") == runner.subprocess.STDOUT
        assert kwargs.get("text") is True
        commands.append(list(command))
        name = Path(command[3]).name
        return _Completed(
            (statuses or {}).get(name, 0),
            (outputs or {}).get(name, "1 passed in 0.10s\n"),
        )

    monkeypatch.setattr(runner.os, "environ", {"PATH": "/usr/bin", "HOME": "/tmp"})
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "_probe", lambda _run, _actor: None)
    return commands


def test_runs_every_acceptance_module_in_its_own_process_in_sorted_order(tmp_path, monkeypatch, capsys):
    root = _python_root(tmp_path, ["test_c.py", "test_a.py", "test_b.py"])
    commands = _record(
        monkeypatch,
        outputs={
            "test_a.py": "2 passed in 0.10s\n",
            "test_b.py": "3 passed in 0.20s\n",
            "test_c.py": "4 passed in 0.30s\n",
        },
    )
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work")
    out = capsys.readouterr().out
    assert status == 0
    assert [Path(c[3]).name for c in commands] == ["test_a.py", "test_b.py", "test_c.py"]
    assert all(c[1:3] == ["-m", "pytest"] for c in commands)
    assert [c[4:] for c in commands] == [[], [], []]
    assert "3 modules: 3 passed, 0 failed" in out
    assert "test_a.py" in out and "2 passed in 0.10s" in out
    assert "test_b.py" in out and "3 passed in 0.20s" in out
    assert "test_c.py" in out and "4 passed in 0.30s" in out


def test_runs_every_module_when_some_fail_and_reports_the_failing_set(tmp_path, monkeypatch, capsys):
    root = _python_root(tmp_path, ["test_a.py", "test_b.py", "test_c.py", "test_d.py"])
    commands = _record(
        monkeypatch,
        statuses={"test_b.py": 1, "test_d.py": 2},
        outputs={
            "test_a.py": "3 passed in 0.20s\n",
            "test_b.py": "FAILED tests/acceptance/test_b.py::test_x\n=== 1 failed, 2 passed in 0.40s ===\n",
            "test_c.py": "4 passed in 0.30s\n",
            "test_d.py": "=== 1 error in 0.10s ===\n",
        },
    )
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work")
    out = capsys.readouterr().out
    assert status == 1
    assert [Path(c[3]).name for c in commands] == ["test_a.py", "test_b.py", "test_c.py", "test_d.py"]
    assert "4 modules: 2 passed, 2 failed" in out
    for expected in (
        "PASS       0  test_a.py  3 passed in 0.20s",
        "FAIL       1  test_b.py  1 failed, 2 passed in 0.40s",
        "PASS       0  test_c.py  4 passed in 0.30s",
        "FAIL       2  test_d.py  1 error in 0.10s",
        "failed modules (2): test_b.py (exit 1), test_d.py (exit 2)",
    ):
        assert expected in out


def test_real_pytest_processes_continue_past_a_failing_module(tmp_path, monkeypatch, capsys):
    root = _python_root(tmp_path, ["test_a_fail.py", "test_b_pass.py"])
    (root / "tests" / "acceptance" / "test_a_fail.py").write_text("def test_boom():\n    assert False\n")
    (root / "tests" / "acceptance" / "test_b_pass.py").write_text("def test_ok():\n    assert True\n")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(runner.os, "environ", {"PATH": os.environ["PATH"], "HOME": str(home)})
    monkeypatch.setattr(runner, "_probe", lambda _run, _actor: None)
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work")
    out = capsys.readouterr().out
    assert status == 1
    assert "2 modules: 1 passed, 1 failed" in out
    assert "FAIL       1  test_a_fail.py  1 failed in " in out
    assert "PASS       0  test_b_pass.py  1 passed in " in out
    assert "failed modules (1): test_a_fail.py (exit 1)" in out


def test_probe_refusal_is_an_error_naming_the_variable(tmp_path, monkeypatch, capsys):
    root = _python_root(tmp_path, ["test_a.py"])
    commands = _record(monkeypatch)
    monkeypatch.setattr(runner, "_probe", lambda _run, _actor: "CapabilityUnavailable: tmpfs")
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work")
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


def test_arguments_are_refused_not_forwarded(monkeypatch, capsys):
    called: list[object] = []
    monkeypatch.setattr(runner, "run_acceptance", lambda **kw: called.append(kw) or 0)
    assert runner.main(["-k", "x"]) == runner.ARGUMENTS_REFUSED
    err = capsys.readouterr().err
    assert called == []
    assert "just test-one tests/acceptance/" in err and "-k x" in err
    assert runner.main([]) == 0 and len(called) == 1


@pytest.mark.parametrize("create", [True, False])
def test_no_acceptance_modules_is_an_error(tmp_path, monkeypatch, capsys, create):
    root = tmp_path / "python"
    if create:
        (root / "tests" / "acceptance").mkdir(parents=True)
    else:
        root.mkdir()
    commands = _record(monkeypatch)
    status = runner.run_acceptance(python_root=root, work=tmp_path / "work")
    err = capsys.readouterr().err
    assert status == runner.NO_MODULES and status != 0 and commands == []
    assert str(root / "tests" / "acceptance") in err
