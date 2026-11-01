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


_HYGIENE = ["ops-check", "ops-docs", "tasks"]
_CHECK_CODE = ["uv", "uv", "uv", "npm", "npm"]
_BROAD_CHILDREN = {
    "hook-pre-commit": {"check-code"},
    "check": {"check-code"},
    "hook-pre-push": {"check-code", "test"},
    "hook-pre-push-fast": {"check-code", "test-push"},
}


def _outcomes(rows: list[dict]) -> list[tuple[str, str, str]]:
    return [(row["target"], row["execution"], row["execution_reason"]) for row in rows]


@pytest.mark.parametrize("recipe", sorted(_BROAD_CHILDREN))
def test_policy_off_keeps_hygiene_and_skips_broad_children(tmp_path: Path, recipe: str) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    result = checkout.just(recipe)
    assert result.returncode == 0, result.stderr
    assert checkout.names() == _HYGIENE
    skipped = [row for row in checkout.rows() if row["execution"] == "skipped"]
    assert {row["target"] for row in skipped} == _BROAD_CHILDREN[recipe]
    assert all(row[key] is None for row in skipped for key in ("exit", "tests", "selection", "slowest"))


@pytest.mark.parametrize("recipe", ["hook-pre-commit", "hook-pre-push", "hook-pre-push-fast"])
def test_failing_hygiene_stops_the_broad_children(tmp_path: Path, recipe: str) -> None:
    # No policy, so a started check-code would log uv.
    checkout = Checkout(tmp_path)
    checkout.env["FAIL_STEP"] = "ops-check"
    assert checkout.just(recipe).returncode != 0
    assert checkout.names() == ["ops-check"]
    assert [(row["target"], row["exit"]) for row in checkout.rows()] == [(recipe, 7)]


@pytest.mark.parametrize("recipe", ["hook-pre-push", "hook-pre-push-fast"])
def test_failing_code_check_stops_the_suite(tmp_path: Path, recipe: str) -> None:
    checkout = Checkout(tmp_path)
    checkout.env["FAIL_STEP"] = "uv"
    assert checkout.just(recipe).returncode != 0
    assert "host-budget" not in checkout.names()
    assert ("check-code", 7) in [(row["target"], row["exit"]) for row in checkout.rows()]


@pytest.mark.parametrize(
    ("recipe", "events", "targets"),
    [
        ("hook-pre-commit", _HYGIENE + _CHECK_CODE, ["hook-pre-commit", "check-code"]),
        (
            "hook-pre-push",
            _HYGIENE + _CHECK_CODE + ["host-budget", "uv", "uv", "npm"],
            ["hook-pre-push", "check-code", "test"],
        ),
        (
            "hook-pre-push-fast",
            _HYGIENE + _CHECK_CODE + ["host-budget", "uv", "npm"],
            ["hook-pre-push-fast", "check-code", "test-push"],
        ),
    ],
)
def test_enabled_hooks_run_every_child_in_order(
    tmp_path: Path, recipe: str, events: list[str], targets: list[str]
) -> None:
    # No .tt.toml: the state before activation and after a lost policy file.
    checkout = Checkout(tmp_path)
    result = checkout.just(recipe)
    assert result.returncode == 0, result.stderr
    assert checkout.names() == events
    assert _outcomes(checkout.rows()) == [(target, "ran", "default") for target in targets]


def test_test_full_records_one_forced_test_row(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    result = checkout.just("test-full")
    assert result.returncode == 0, result.stderr
    assert _outcomes(checkout.rows()) == [("test", "ran", "forced")]
    checkout.env["FAIL_STEP"] = "uv"
    assert checkout.just("test-full").returncode != 0
    assert [(row["target"], row["exit"]) for row in checkout.rows()[1:]] == [("test", 7)]


def test_forced_gate_records_three_forced_rows(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    checkout.env["TT_FORCE"] = "1"
    result = checkout.just("gate")
    assert result.returncode == 0, result.stderr
    assert _outcomes(checkout.rows()) == [
        ("check-hygiene", "ran", "forced"),
        ("check-code", "ran", "forced"),
        ("test", "ran", "forced"),
    ]
    before = len(checkout.rows())
    checkout.env["FAIL_STEP"] = "npm"
    assert checkout.just("gate").returncode != 0
    assert [(row["target"], row["exit"]) for row in checkout.rows()[before:]] == [
        ("check-hygiene", 0),
        ("check-code", 7),
    ]


@pytest.mark.parametrize(("target", "tool"), [("ci-python", "uv"), ("ci-typescript", "npm")])
def test_hosted_refuses_missing_force(tmp_path: Path, target: str, tool: str) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    checkout.env["GITHUB_ACTIONS"] = "true"
    result = checkout.just(target)
    assert result.returncode != 0 and "TT_FORCE=1" in result.stderr
    assert checkout.events() == [] and checkout.rows() == []
    checkout.env.update(TT_FORCE="1", FAIL_STEP=tool)
    assert checkout.just(target).returncode != 0
    assert checkout.rows()[-1]["exit"] == 7


def test_nested_hosted_refuses_missing_force(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    with (checkout.root / "justfile").open("a") as justfile:
        justfile.write("\nnested:\n    {{tt}} outer -- just ci-python\n")
    checkout.env["GITHUB_ACTIONS"] = "true"
    result = checkout.just("nested")
    assert result.returncode != 0 and "TT_FORCE=1" in result.stderr
    assert checkout.events() == []
    rows = checkout.rows()
    assert [(row["target"], row["execution"]) for row in rows] == [("outer", "ran")] and rows[0]["exit"] != 0
    checkout.env.update(TT_FORCE="1", FAIL_STEP="uv")
    assert checkout.just("nested").returncode != 0
    assert checkout.rows()[-1]["exit"] == 7


def test_focused_route_runs_under_policy_off(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    checkout.policy()
    runner = _forwarding_runner(tmp_path)
    result = checkout.just("--set", "one_cmd", f"python3 {shlex.quote(str(runner))}", "test-one", "tests/a.py")
    assert result.returncode == 0, result.stderr
    assert _outcomes(checkout.rows()) == [("test-one", "ran", "default")]
