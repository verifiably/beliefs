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
import tomllib
from hashlib import sha256
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
        "FROZEN_PRIOR_CUT_FILES = {\n"
        '    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",\n'
        '    "python/tests/n2_arms_cut3.py": "1e92471",\n'
        "}\n",
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


UNFORMATTED = b"ARMS = ('a',\n    'b')\n"
FORMATTED = b'ARMS = ("a", "b")\n'
CHANGED = b'ARMS = ("a", "c")\n'


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=pin-test",
            "-c",
            "user.email=pin-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit(root: Path, files: dict[str, bytes | None]) -> str:
    """Write (or, for None, delete) each file, commit everything, and return the commit."""
    for name, data in files.items():
        path = root / name
        if data is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--allow-empty", "-m", "step")
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def scratch_repo(tmp_path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    return root


def test_a_commit_pin_holds_through_formatting_and_breaks_on_a_change(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"arms.py": UNFORMATTED})
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)

    (scratch_repo / "arms.py").write_bytes(CHANGED)  # the working file, uncommitted
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_an_absence_pin_holds_only_while_the_target_stays_absent(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"other.py": FORMATTED})
    assert frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)

    (scratch_repo / "arms.py").symlink_to("missing.py")  # dangling, yet an entry exists
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)

    (scratch_repo / "arms.py").unlink()
    (scratch_repo / "arms.py").write_bytes(FORMATTED)
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_a_present_target_that_was_deleted_breaks(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"arms.py": FORMATTED})
    _commit(scratch_repo, {"arms.py": None})
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_a_commit_that_does_not_resolve_is_broken_not_absent(scratch_repo) -> None:
    _commit(scratch_repo, {"other.py": FORMATTED})
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", "0" * 40)


def test_a_content_pin_resolves_its_original_from_history(scratch_repo) -> None:
    digest = sha256(UNFORMATTED).hexdigest()
    _commit(scratch_repo, {"arms.py": UNFORMATTED})
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)

    (scratch_repo / "arms.py").write_bytes(CHANGED)  # the cache holds the original, not a verdict
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)


def test_a_content_pin_no_version_matches_is_broken(scratch_repo) -> None:
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", sha256(UNFORMATTED).hexdigest())


def test_a_content_pin_on_a_deleted_target_is_broken(scratch_repo) -> None:
    _commit(scratch_repo, {"arms.py": FORMATTED})
    digest = sha256(FORMATTED).hexdigest()
    (scratch_repo / "arms.py").unlink()
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)


def test_resolution_in_one_repository_is_not_evidence_about_another(tmp_path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    for root in (first, second):
        root.mkdir()
        _git(root, "init", "-q")
    digest = sha256(UNFORMATTED).hexdigest()
    _commit(first, {"arms.py": UNFORMATTED})
    _commit(first, {"arms.py": FORMATTED})
    _commit(second, {"arms.py": FORMATTED})

    assert frozen_guards.content_pin_holds(first, "arms.py", digest)
    assert not frozen_guards.content_pin_holds(second, "arms.py", digest)


def test_the_scalar_declaration_readers_find_the_digest_and_commit(tmp_path) -> None:
    guard = tmp_path / "test_n2_cut99.py"
    guard.write_text(
        'FROZEN_DECLARATION = "python/tests/n2_arms_cut99.py"\n'
        'CUT99_DECLARATION_SHA256 = "' + "a" * 64 + '"\n'
        'CUT99_DECLARATION_COMMIT = "abc1234"\n'
        'CUT99_FROZEN_SHA256 = "' + "b" * 64 + '"\n',
        encoding="utf-8",
    )

    assert frozen_guards.declaration_digest(guard) == "a" * 64
    assert frozen_guards.declaration_commit(guard) == "abc1234"


def test_every_declaration_pin_in_a_live_guard_holds(git_checkout) -> None:
    """The scalar freeze: each live guard's `FROZEN_DECLARATION` against its digest and,
    for cuts 27-30, its declaring commit. Formatting touches ten of these files, and no
    portable check read them before doctrine §8."""
    checked, broken = 0, []
    for guard in frozen_guards.live_guards(REPO_ROOT):
        declaration = frozen_guards.declaration_pin(guard)
        if declaration is None:
            continue
        digest = frozen_guards.declaration_digest(guard)
        assert digest is not None, f"{guard.name} names FROZEN_DECLARATION without its digest"
        checked += 1
        if not frozen_guards.content_pin_holds(REPO_ROOT, declaration, digest):
            broken.append(f"{guard.name}::digest")
        commit = frozen_guards.declaration_commit(guard)
        if commit is not None and not frozen_guards.commit_pin_holds(REPO_ROOT, declaration, commit):
            broken.append(f"{guard.name}::commit")

    assert checked >= 21  # cuts 26-46 at the time of writing
    assert not broken


PYPROJECT = REPO_ROOT / "python" / "pyproject.toml"


def test_the_protected_set_reads_both_freeze_forms_and_cited_surfaces(tmp_path) -> None:
    """A freeze claims a file by table pin or by `FROZEN_DECLARATION`; either one protects it.

    The synthetic tree holds one guard using both forms. Cited-not-run surfaces are read from
    the real registry and filtered to files that exist, so none appears here.
    """
    python = tmp_path / "python"
    (python / "tests" / "acceptance").mkdir(parents=True)
    (python / "tools").mkdir()
    for name in ("tests/n2_arms_cut99.py", "tests/acceptance/test_n2_cut98.py", "tools/cut98_acceptance.py"):
        (python / name).write_text("x = 1\n", encoding="utf-8")
    (python / "tests" / "acceptance" / "test_n2_cut99.py").write_text(
        'FROZEN_DECLARATION = "python/tests/n2_arms_cut99.py"\n'
        "FROZEN_PRIOR_CUT_FILES = {\n"
        '    "python/tests/acceptance/test_n2_cut98.py": "abc1234",\n'
        '    "python/tools/cut98_acceptance.py": "abc1234",\n'
        '    "python/tests/n2_arms_cut97.py": "abc1234",\n'
        '    "docs/plans/cut-98-results.md": "abc1234",\n'
        "}\n",
        encoding="utf-8",
    )

    assert frozen_guards.declaration_pin(python / "tests" / "acceptance" / "test_n2_cut99.py") == (
        "python/tests/n2_arms_cut99.py"
    )
    assert frozen_guards.protected_paths(tmp_path) == frozenset(
        {"tests/n2_arms_cut99.py", "tests/acceptance/test_n2_cut98.py", "tools/cut98_acceptance.py"}
    )


def test_the_format_exclude_is_exactly_the_protected_set() -> None:
    """Formatting must not touch a file a freeze claims (spec 2026-10-09 §3.1).

    Pins are byte-exact, so ruff format excludes every file a guard pins, by table or by its
    scalar `FROZEN_DECLARATION`, plus every cited-not-run surface the doctrine makes evidence
    whether or not a pin names it. beliefs-ea5ec7 retires this list and this test together.
    """
    ruff = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["ruff"]
    exclude = ruff["format"]["exclude"]
    protected = frozen_guards.protected_paths(REPO_ROOT)

    assert ruff["force-exclude"] is True
    assert exclude == sorted(set(exclude))
    assert "tests/n2_arms_cut46.py" in protected  # the scalar form: no table pins it
    assert "tests/acceptance/test_n2_cut4.py" in protected  # cited, and no pin names it
    assert "tests/n2_arms_cut25.py" not in protected  # a falsified pin on a removed file
    assert set(exclude) == protected


def test_an_explicit_path_cannot_format_a_protected_file() -> None:
    """An editor formats by explicit path; `force-exclude` keeps the exclude in force there."""
    completed = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "tests/n2_arms_cut46.py"],
        cwd=REPO_ROOT / "python",
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
