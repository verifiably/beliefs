"""Pin the hosted workflow and its coverage evidence, and the coverage the push hook claims.

Recipe cases run in route_fixtures.Checkout; workflow cases read ci.yml and run its
shell steps in a fixture. Nothing here runs a real suite or a recipe at the root.
"""

import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from route_fixtures import BROAD, ROOT, Checkout, init_repo

WORKFLOW = ROOT / ".github/workflows/ci.yml"
PR_CONDITION = (
    "github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository"
)
REQUIRED = {
    "python": ["pytest.xml", "module-inventory.txt"],
    "typescript": ["vitest.xml", "module-inventory.txt"],
}
CAPABILITY_SKIP = "certified tuple unavailable on this host:"


def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def triggers(doc: dict) -> dict:
    """PyYAML reads the bare `on:` key as True; a missing block must fail, not pass."""
    for key in (True, "on"):
        if key in doc:
            return doc[key]
    raise AssertionError("ci.yml has no trigger block")


def step(job: dict, name: str) -> dict:
    return next(s for s in job["steps"] if s.get("name") == name)


def github_covers(ref_glob: str, branches: list[str]) -> bool:
    """Whether GitHub's push.branches cover a ci_suite_refs glob.

    GitHub's `*` stops at `/` and only `**` crosses it, unlike fnmatch, so
    `refs/heads/*` (every branch, slashes included, under the hook's fnmatch) needs
    `**`. Any other wildcard shape has no specified equivalent yet.
    """
    prefix = "refs/heads/"
    if not ref_glob.startswith(prefix):
        raise ValueError(f"no workflow equivalent is specified for {ref_glob}")
    name = ref_glob[len(prefix) :]
    if name == "*":
        return "**" in branches
    if any(char in name for char in "*?[]!"):
        raise ValueError(f"no workflow equivalent is specified for {ref_glob}")
    return name in branches or "**" in branches


def live_suite_refs() -> list[str]:
    match = re.search(r'^ci_suite_refs := "(.*)"$', (ROOT / "justfile").read_text(), flags=re.MULTILINE)
    assert match is not None
    return match.group(1).split()


@pytest.mark.parametrize("target", ["ci-python", "ci-typescript"])
@pytest.mark.parametrize("path", [None, "relative/path"])
def test_ci_requires_absolute_evidence_path(tmp_path: Path, target: str, path: str | None) -> None:
    checkout = Checkout(tmp_path)
    if path is None:
        del checkout.env["BELIEFS_CI_EVIDENCE_DIR"]
    else:
        checkout.env["BELIEFS_CI_EVIDENCE_DIR"] = path
    assert checkout.just(target).returncode != 0
    assert checkout.events() == []


def test_pytest_junit_persists_skip_reasons(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    # The real pytest, from this environment, behind the uv stub's argv.
    (checkout.root / "bin/uv").write_text(
        f"#!{sys.executable}\nimport os, sys\n"
        "os.execv(sys.executable, [sys.executable, '-m', 'pytest', *sys.argv[4:]])\n"
    )
    tests = checkout.root / "python/tests"
    tests.mkdir()
    (tests / "test_some.py").write_text(
        f"import pytest\n\ndef test_pass():\n    pass\n\ndef test_capability():\n"
        f"    pytest.skip({CAPABILITY_SKIP + ' fixture'!r})\n"
    )
    evidence = checkout.root / "evidence with spaces"
    evidence.mkdir()
    checkout.env["BELIEFS_CI_EVIDENCE_DIR"] = str(evidence)
    result = checkout.just("--set", "py_check_cmd", "true", "ci-python")
    assert result.returncode == 0, result.stdout + result.stderr
    cases = ET.parse(evidence / "pytest.xml").findall(".//testcase")
    assert sorted(case.attrib["name"] for case in cases) == ["test_capability", "test_pass"]
    assert all(case.attrib["classname"].endswith("test_some") for case in cases)
    skips = [skip for case in cases if (skip := case.find("skipped")) is not None]
    assert [skip.attrib["message"] for skip in skips] == [CAPABILITY_SKIP + " fixture"]
    assert checkout.rows()[-1]["target"] == "ci-python"
    # A failing static check after the suite must not erase the reports it produced.
    assert checkout.just("--set", "py_check_cmd", "false", "ci-python").returncode != 0
    assert (evidence / "pytest.xml").is_file()


def test_vitest_reporter_arguments(tmp_path: Path) -> None:
    checkout = Checkout(tmp_path)
    result = checkout.just("--set", "ts_check_cmd", "true", "ci-typescript")
    assert result.returncode == 0, result.stderr
    evidence = checkout.env["BELIEFS_CI_EVIDENCE_DIR"]
    assert [event[1:3] for event in checkout.events()] == [
        [
            ["test", "--", "--reporter=default", "--reporter=junit", f"--outputFile.junit={evidence}/vitest.xml"],
            str(checkout.root / "ts"),
        ]
    ]


def test_triggers_concurrency_and_jobs() -> None:
    doc = workflow()
    on = triggers(doc)
    assert set(on) == {"push", "pull_request", "workflow_dispatch"}
    assert on["push"] == {"branches": ["**"]}
    assert doc["concurrency"] == {"group": "${{ github.workflow }}-${{ github.ref }}", "cancel-in-progress": True}
    jobs = doc["jobs"]
    for name, timeout in (("python", 30), ("typescript", 10)):
        assert jobs[name]["if"] == PR_CONDITION
        assert jobs[name]["env"]["TT_FORCE"] == "1"
        assert jobs[name]["timeout-minutes"] == timeout
    assert jobs["python"]["strategy"]["matrix"] == {"python-version": ["3.11", "3.13"]}
    assert jobs["typescript"]["strategy"]["matrix"] == {"node-version": ["20", "24"]}
    python = jobs["python"]
    assert python["env"]["PYTEST_XDIST_AUTO_NUM_WORKERS"] == "4"
    run = next(s for s in python["steps"] if s.get("run") == "just ci-python")
    assert run["env"] == {"VERIFIABLY_UNCERTIFIED_HOST": "1"}
    checkouts = [s["with"] for s in python["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
    assert {c.get("repository") for c in checkouts} == {None, "verifiably/atoms", "verifiably/nodes"}
    assert next(c for c in checkouts if "repository" not in c)["fetch-depth"] == 0


@pytest.mark.parametrize(("job", "missing"), [(job, name) for job, names in REQUIRED.items() for name in names])
def test_required_evidence_check_fails_when_a_file_is_missing(tmp_path: Path, job: str, missing: str) -> None:
    steps = workflow()["jobs"][job]
    check = step(steps, "Require coverage evidence")
    upload = next(s for s in steps["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    assert check["if"] == "always()" and upload["if"] == "always()"
    version = "python-version" if job == "python" else "node-version"
    assert upload["with"] == {
        "name": f"{job}-${{{{ matrix.{version} }}}}-coverage",
        "path": "${{ env.BELIEFS_CI_EVIDENCE_DIR }}",
        "retention-days": 30,
        "if-no-files-found": "error",
    }
    checkout = Checkout(tmp_path)
    evidence = Path(checkout.env["BELIEFS_CI_EVIDENCE_DIR"])
    for name in REQUIRED[job]:
        (evidence / name).write_text("<testsuites/>\n")
    assert checkout.run("sh", "-eu", "-c", check["run"]).returncode == 0
    (evidence / missing).unlink()
    assert checkout.run("sh", "-eu", "-c", check["run"]).returncode != 0


@pytest.mark.parametrize("job", ["python", "typescript"])
def test_inventory_lists_eligible_modules_and_siblings(tmp_path: Path, job: str) -> None:
    checkout = Checkout(tmp_path)
    package = checkout.root / ("python" if job == "python" else "ts")
    if job == "python":
        files = ["tests/test_a b.py", "tests/test_d.py", "tests/acceptance/test_c.py", "tests/conftest.py"]
        files += ["tests/x_fixtures.py"]
        eligible, manifest = ["tests/test_a b.py", "tests/test_d.py"], "pyproject.toml"
    else:
        files, eligible, manifest = ["tests/a.test.ts", "tests/helper.ts"], ["tests/a.test.ts"], "package.json"
    for name in files:
        (package / name).parent.mkdir(parents=True, exist_ok=True)
        (package / name).write_text("")
    (package / manifest).write_bytes((ROOT / package.name / manifest).read_bytes())
    assert checkout.run("git", "add", ".").returncode == 0
    assert checkout.run("git", "commit", "-qm", "fixture").returncode == 0
    heads = {}
    for sibling in ("atoms", "nodes") if job == "python" else ():
        repo = tmp_path / sibling
        repo.mkdir()
        init_repo(repo, checkout.env)
        assert checkout.run("git", "commit", "-q", "--allow-empty", "-m", sibling, cwd=repo).returncode == 0
        heads[sibling] = checkout.run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    checkout.env["RUNNER_TEMP"] = str(checkout.root / "runner temp")
    checkout.env["GITHUB_ENV"] = str(checkout.root / "github-env")
    prepare = step(workflow()["jobs"][job], "Prepare coverage evidence")
    result = checkout.run("sh", "-eu", "-c", prepare["run"], cwd=package)
    assert result.returncode == 0, result.stderr
    assignment = Path(checkout.env["GITHUB_ENV"]).read_text().strip()
    assert assignment.startswith("BELIEFS_CI_EVIDENCE_DIR=")
    directory = Path(assignment.split("=", 1)[1])
    assert directory.is_relative_to(Path(checkout.env["RUNNER_TEMP"]))
    lines = (directory / "module-inventory.txt").read_text().splitlines()
    beliefs = checkout.run("git", "rev-parse", "HEAD").stdout.strip()
    assert lines[0] == f"beliefs {beliefs}"
    assert lines[1 : 1 + len(heads)] == [f"{name} {head}" for name, head in heads.items()]
    modules = [line for line in lines if line.startswith("tests/")]
    assert modules == eligible


def test_github_covers_semantics() -> None:
    assert github_covers("refs/heads/*", ["**"])
    assert not github_covers("refs/heads/*", ["*"])
    assert github_covers("refs/heads/main", ["main"])
    assert github_covers("refs/heads/main", ["**"])
    assert not github_covers("refs/heads/main", ["dev"])
    with pytest.raises(ValueError):
        github_covers("refs/heads/release/*", ["**"])


def test_live_suite_refs_are_covered_by_push_branches() -> None:
    branches = triggers(workflow())["push"]["branches"]
    refs = live_suite_refs()
    assert refs
    assert all(github_covers(ref, branches) for ref in refs)


def test_broad_targets_name_tt_targets() -> None:
    justfile = (ROOT / "justfile").read_text()
    for target in BROAD:
        assert f"{{{{tt}}}} {target} --" in justfile, target
    policy = ROOT / ".tt.toml"
    if policy.exists():
        listed = tomllib.loads(policy.read_text())["broad_targets"]
        assert listed == BROAD


def test_ci_suites_are_the_local_suites(tmp_path: Path) -> None:
    # Hosted CI is the routine full-suite route under policy-off, so its selection must
    # be exactly `test`'s: the CI commands may add reporting flags and nothing else.
    checkout = Checkout(tmp_path)

    def evaluate(name: str) -> str:
        result = checkout.just("--evaluate", name)
        assert result.returncode == 0, result.stderr
        return result.stdout

    # `test` itself is exactly the two package suites the CI jobs carry.
    assert evaluate("test_cmd") == evaluate("py_test_cmd") + " && " + evaluate("ts_test_cmd")
    junit = r' --junitxml="\$BELIEFS_CI_EVIDENCE_DIR/[^"/]+\.xml"'
    assert re.sub(junit, "", evaluate("ci_py_test_cmd")) == evaluate("py_test_cmd")
    reporters = ' -- --reporter=default --reporter=junit --outputFile.junit="$BELIEFS_CI_EVIDENCE_DIR/vitest.xml"'
    assert evaluate("ci_ts_test_cmd").replace(reporters, "") == evaluate("ts_test_cmd")
