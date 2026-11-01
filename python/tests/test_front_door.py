"""Exercise the adopted front door without running the gates inside the gates.

Every case runs in an isolated fixture checkout (route_fixtures.Checkout) with stub
tools and an environment built key by key, never at the repository root.
"""

import json
import shlex
from pathlib import Path

import pytest
from route_fixtures import Checkout


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
def test_staged_paths_choose_the_gate(tmp_path: Path, path: str, recipe: str) -> None:
    checkout = Checkout(tmp_path)
    checkout.capture_hook_recipe()
    staged = checkout.root / path
    staged.parent.mkdir(parents=True, exist_ok=True)
    if path != "justfile":
        staged.write_text("document\n")
    assert checkout.run("git", "add", "--", path).returncode == 0
    result = checkout.run("sh", ".githooks/pre-commit", stdin="")
    assert result.returncode == 0, result.stderr
    assert checkout.chosen() == recipe


def _push_lines(refs: tuple[str, ...]) -> str:
    return "".join(f"refs/heads/{ref} {'a' * 40} refs/heads/{ref} {'b' * 40}\n" for ref in refs)


@pytest.mark.parametrize(
    ("suite_refs", "remote", "refs", "recipe"),
    [
        ("refs/heads/main", "origin", ("main",), "hook-pre-push-fast"),
        ("refs/heads/main", "origin", ("feature",), "hook-pre-push"),
        ("refs/heads/main", "origin", ("main", "feature"), "hook-pre-push"),
        ("refs/heads/main", "backup", ("main",), "hook-pre-push"),
        ("refs/heads/main", "origin", (), "hook-pre-push"),
        ("refs/heads/*", "origin", ("feature/x",), "hook-pre-push-fast"),
        ("refs/heads/*", "backup", ("main",), "hook-pre-push"),
    ],
)
def test_push_refs_choose_the_gate(
    tmp_path: Path, suite_refs: str, remote: str, refs: tuple[str, ...], recipe: str
) -> None:
    # Each case declares its own coverage, so widening the live value moves no case.
    checkout = Checkout(tmp_path)
    checkout.set_suite_refs(suite_refs)
    checkout.capture_hook_recipe()
    stdin = _push_lines(refs)
    result = checkout.run("sh", ".githooks/pre-push", remote, "https://example.test/repo", stdin=stdin)
    assert result.returncode == 0, result.stderr
    assert checkout.chosen() == recipe
    assert (checkout.root / "refs.actual").read_text() == stdin


def _forwarding_runner(tmp_path: Path) -> Path:
    runner = tmp_path / "runner.py"
    runner.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\nprint('1 passed in 0.01s')\n")
    return runner


def test_one_preserves_arguments_and_records_the_run(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    command = ("--set", "one_cmd", f"python3 {shlex.quote(str(_forwarding_runner(tmp_path)))}", "test-one")
    args = ["-k", "a and b", "tests/p q.py", "it's", "$HOME", "renders *"]
    result = checkout.just(*command, *args)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[0]) == args
    row = checkout.rows()[-1]
    assert (row["target"], row["tests"]) == ("test-one", 1)
    assert [event[1][:2] for event in checkout.events() if event[0] == "host-budget"] == [["run", "--"]]
    assert checkout.just(*command).returncode != 0
