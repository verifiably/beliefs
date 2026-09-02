import importlib.util
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "cut14_acceptance", Path(__file__).parents[1] / "tools" / "cut14_acceptance.py"
)
assert _SPEC is not None and _SPEC.loader is not None
cut14 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cut14)

EXPECTED = (
    "test_n2_cut6.py",
    "test_n2_cut7.py",
    "test_n2_cut9.py",
    "test_n2_cut10.py",
    "test_intent_boundary_acceptance.py",
    "test_n2_cut11.py",
    "test_successor_admission_acceptance.py",
    "test_n2_cut12.py",
    "test_confinement_acceptance.py",
    "test_n2_cut13.py",
    "test_coordination_acceptance.py",
    "test_n2_cut14.py",
)


def test_cut14_has_no_aggregate_prefix_and_the_exact_frozen_phase_order():
    assert cut14.PREFIX_RUNNERS == ()
    assert cut14.PHASE_MODULES == EXPECTED


def test_every_phase_receives_one_probed_environment_and_only_n2_receives_arguments(
    tmp_path, monkeypatch
):
    acceptance = tmp_path / "acceptance"
    acceptance.mkdir()
    for module in EXPECTED:
        (acceptance / module).write_text("", encoding="utf-8")
    monkeypatch.setattr(cut14, "ACCEPTANCE", acceptance)
    monkeypatch.setattr(cut14, "work_directory", lambda: tmp_path)
    monkeypatch.setattr(cut14, "probe", lambda _run: None)
    calls = []
    monkeypatch.setattr(
        cut14.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs))
        or subprocess.CompletedProcess(command, 0),
    )
    monkeypatch.setattr(cut14, "declared_arm_count", lambda: 29)
    assert cut14.main(["-k", "one"]) == 0
    assert [Path(call[0][3]).name for call in calls] == list(EXPECTED)
    assert calls[-1][0][-2:] == ["-k", "one"]
    assert all(call[1]["env"]["SCIENCE_CUT14_ROOT"] for call in calls)
    assert all(
        Path(call[1]["env"]["XDG_CACHE_HOME"])
        == Path(call[1]["env"]["SCIENCE_CUT14_ROOT"]) / "cache"
        for call in calls
    )


def test_declared_arm_count_imports_both_test_roots():
    assert cut14.declared_arm_count() == 29
