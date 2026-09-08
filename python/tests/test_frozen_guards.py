"""The guard modules' own guard.

Every conformance cut leaves behind a guard module, `tests/acceptance/test_n2_cutN.py`,
carrying `FROZEN_*` pin tables that name prior-cut files and the commit or content they
were cited at. A guard is **live** — reachable from the newest cut's runner — or
**cited, not run**, and which one it is decides what its pin table means: machinery that
must track the tree, or evidence about the tree the cut discharged on. The doctrine is
`docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`; this module is what
holds the tree to it.

The checks live here, in the portable suite, and not beside the guards they read:
`addopts` ignores `tests/acceptance`, so a check placed there would run only during a
discharge — which is exactly how five live pins came to be broken for a week without
anything reporting it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cited_not_run
import frozen_guards
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def git_checkout() -> None:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-dir"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        pytest.skip("pin resolution needs the git checkout")


def test_the_pin_checker_reports_a_table_the_tree_has_falsified(tmp_path, git_checkout) -> None:
    """The detector's own proof.

    Every live pin holds today, so the check over the real guards passes whether or not
    it works. This arm falsifies a table on purpose: `n2_arms_cut5.py` moved at
    `1e92471`, so a table pinning it at its predecessor is broken, and a checker that
    cannot see that is worth nothing.
    """
    guard = tmp_path / "test_n2_cut99.py"
    guard.write_text(
        'FROZEN_PRIOR_CUT_FILES = {\n'
        '    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",\n'
        '    "python/tests/n2_arms_cut3.py": "1e92471",\n'
        '}\n',
        encoding="utf-8",
    )

    broken = frozen_guards.broken_pins(guard, repo_root=REPO_ROOT)

    assert [pin.target for pin in broken] == ["python/tests/n2_arms_cut5.py"]
    assert broken[0].table == "FROZEN_PRIOR_CUT_FILES"


def test_the_inventory_walk_reaches_a_prefix_runners_own_prefix(tmp_path) -> None:
    """A runner names its prefix runner, not the whole chain, so the walk has to be
    transitive: cut 21 names cut 20, which reaches cut 17's inventory five links down."""
    (tmp_path / "cut1_acceptance.py").write_text(
        'PREFIX_RUNNERS = ()\nPHASE_MODULES = ("test_n2_cut1.py",)\n', encoding="utf-8"
    )
    (tmp_path / "cut2_acceptance.py").write_text(
        'PREFIX_RUNNERS = ("cut1_acceptance.py",)\nPHASE_MODULES = ("test_n2_cut2.py",)\n', encoding="utf-8"
    )

    reached = frozen_guards.live_inventory(tmp_path / "cut2_acceptance.py")

    assert reached == frozenset({"test_n2_cut1.py", "test_n2_cut2.py"})


def test_every_pin_in_a_live_guard_holds(git_checkout) -> None:
    """A live guard's pin table is machinery: it must track the tree.

    This is the arm that reports a broken live pin the day it breaks. Before it existed,
    five of them survived a whole slice unreported, because nothing outside a discharge
    reads these tables.
    """
    broken = {
        f"{pin.guard}::{pin.table}::{pin.target}"
        for guard in frozen_guards.live_guards(REPO_ROOT)
        for pin in frozen_guards.broken_pins(guard, repo_root=REPO_ROOT)
    }

    assert not broken, (
        "a live guard pins a file the tree has moved; fix the arm, never the source, "
        "then re-pin every live table in the same commit"
    )


def test_every_guard_module_is_either_live_or_declared_cited_not_run() -> None:
    """The partition, which is the whole point.

    A guard that is in no runner's inventory and in no registry entry is a module nobody
    can say the standing of — and its red, when the tree moves under it, gets read as a
    regression by the next person who runs it. A module that is both is worse: the
    registry would be excusing failures the chain is still relying on.
    """
    live = {guard.name for guard in frozen_guards.live_guards(REPO_ROOT)}
    declared = set(cited_not_run.CITED_NOT_RUN)
    every = {guard.name for guard in frozen_guards.guard_modules(REPO_ROOT)}

    assert live & declared == set(), "declared cited-not-run while the chain still runs it"
    assert every - (live | declared) == set(), "in no runner inventory and in no registry entry"


def test_a_cited_not_run_guard_is_refused_collection_with_its_ruling_named() -> None:
    """Running one is a category error, and it says so.

    Not a skip: `tests/acceptance/conftest.py` rules that a skip reports green for a
    guarantee that was not exercised, and that rule holds here. The module is refused
    collection instead, and the reason names the ruling and the discharge that stands —
    so the red that used to be read as a regression is now a sentence.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/acceptance/test_n2_cut8.py", "--collect-only"],
        cwd=REPO_ROOT / "python",
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr

    assert completed.returncode == pytest.ExitCode.NO_TESTS_COLLECTED, output
    assert "cited, not run" in output, output
    assert "docs/plans/2026-08-22-conformance-cut-8-results.md" in output, output


def test_every_registry_entry_names_documents_that_exist() -> None:
    """A citation nobody can follow is not a citation."""
    for module, entry in cited_not_run.CITED_NOT_RUN.items():
        assert (REPO_ROOT / entry.standing_record).is_file(), f"{module}: {entry.standing_record}"
        assert (REPO_ROOT / entry.ruled_by).is_file(), f"{module}: {entry.ruled_by}"
        assert entry.reason.strip(), module


def test_every_pin_the_registry_records_as_falsified_really_is(git_checkout) -> None:
    """The registry records what the tree has falsified, and nothing else.

    An entry claiming a pin is broken when it holds would excuse a repair nobody made;
    the same check is what retires an entry when a file is restored, as cut 14's content
    pin on cut 5's guard was.
    """
    for module, entry in cited_not_run.CITED_NOT_RUN.items():
        guard = REPO_ROOT / "python" / "tests" / "acceptance" / module
        broken = {pin.target for pin in frozen_guards.broken_pins(guard, repo_root=REPO_ROOT)}

        assert set(entry.falsified_pins) == broken, module
