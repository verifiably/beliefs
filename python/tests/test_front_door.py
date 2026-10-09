"""Exercise the adopted front door without running the gates inside the gates."""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def hook_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy(ROOT / "justfile", tmp_path / "justfile")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    just = bin_dir / "just"
    just.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = --evaluate ]; then exec {shlex.quote(str(shutil.which("just")))} "$@"; fi\n'
        'printf "%s\\n" "$1"\n'
        "cat\n"
    )
    just.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return tmp_path


@pytest.mark.parametrize(
    ("path", "recipe"),
    [
        ("AGENTS.md", "hook-pre-commit-docs"),
        ("tasks/task.md", "hook-pre-commit-docs"),
        ("justfile", "hook-pre-commit"),
        ("README.md", "hook-pre-commit"),
        ("docs/designs/cut.md", "hook-pre-commit"),
    ],
)
def test_staged_paths_choose_the_gate(hook_repo: Path, path: str, recipe: str) -> None:
    staged = hook_repo / path
    staged.parent.mkdir(parents=True, exist_ok=True)
    if path != "justfile":
        staged.write_text("document\n")
    subprocess.run(["git", "add", "--", path], cwd=hook_repo, check=True)
    result = subprocess.run(
        [str(ROOT / ".githooks/pre-commit")], cwd=hook_repo, input="", text=True, capture_output=True, check=True
    )
    assert result.stdout.strip() == recipe


@pytest.mark.parametrize(
    ("remote", "refs", "recipe"),
    [
        ("origin", ("main",), "hook-pre-push-fast"),
        ("origin", ("feature",), "hook-pre-push"),
        ("origin", ("main", "feature"), "hook-pre-push"),
        ("backup", ("main",), "hook-pre-push"),
        ("origin", (), "hook-pre-push"),
    ],
)
def test_push_refs_choose_the_gate(hook_repo: Path, remote: str, refs: tuple[str, ...], recipe: str) -> None:
    stdin = "".join(f"refs/heads/{ref} {'a' * 40} refs/heads/{ref} {'b' * 40}\n" for ref in refs)
    result = subprocess.run(
        [str(ROOT / ".githooks/pre-push"), remote, "https://example.test/repo"],
        cwd=hook_repo,
        input=stdin,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout == f"{recipe}\n{stdin}"


def test_one_preserves_arguments_and_records_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # CI has no host-budget. Exercise just/tt/runner forwarding without a host allocation.
    budget = tmp_path / "host-budget"
    budget.write_text('#!/bin/sh\n[ "$1" = run ] && [ "$2" = -- ] || exit 1\nshift 2\nexec "$@"\n')
    budget.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    runner = tmp_path / "runner.py"
    runner.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\nprint('1 passed in 0.01s')\n")
    log = tmp_path / "timings.jsonl"
    args = ["-k", "a and b", "tests/p q.py", "it's", "$HOME", "renders *"]
    command = ["just", "--set", "one_cmd", f"python3 {shlex.quote(str(runner))}", "test-one"]
    result = subprocess.run(
        [*command, *args], cwd=ROOT, env={**os.environ, "TT_LOG": str(log)}, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[0]) == args
    timing = json.loads(log.read_text().splitlines()[-1])
    assert (timing["target"], timing["tests"]) == ("test-one", 1)
    empty = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    assert empty.returncode != 0
