"""An isolated checkout for exercising the justfile and hooks without running the gates.

Every tool a recipe reaches is a stub that logs its argv to an events file, so a case
asserts which steps ran, in order, and which tt rows were recorded, without a real
suite, check, host budget or network call. Nothing here inherits the caller's
environment: a hosted job sets TT_FORCE and GITHUB_ACTIONS, and an inherited copy
would decide the skip and warning cases for them.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: The broad targets the adopted policy lists.
BROAD = ["test", "test-fast", "test-push", "check-code", "ci-python", "ci-typescript"]

_STUB = r"""
import json, os, pathlib, sys
name = NAME
args = sys.argv[1:]
root = pathlib.Path(os.environ["FIXTURE_ROOT"])
if name == "tasks" and args != ["check"]:
    print(json.dumps({"project": {"root": str(root), "prefix": "fixture", "linked": False}}))
    sys.exit(0)
with open(os.environ["EVENTS"], "a") as f:
    f.write(json.dumps([name, args, os.getcwd(), os.environ.get("GIT_DIR")]) + "\n")
if os.environ.get("FAIL_STEP") == name:
    sys.exit(7)
if name == "ssh":
    print("serveraliveinterval " + os.environ.get("SSH_INTERVAL", "60"))
"""

_HOST_BUDGET = r"""
import json, os, sys
args = sys.argv[1:]
with open(os.environ["EVENTS"], "a") as f:
    f.write(json.dumps(["host-budget", args, os.getcwd(), os.environ.get("GIT_DIR")]) + "\n")
if args[:2] != ["run", "--"] or len(args) < 3:
    sys.exit(1)
os.execvp(args[2], args[2:])
"""

_FIXTURE_IDENTITY = {
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def _just_binary() -> str:
    just = shutil.which("just")
    assert just is not None, "the route tests need just on PATH"
    return just


class Checkout:
    """A git checkout holding copies of the justfile, tt and the hooks, with stub tools."""

    def __init__(self, tmp: Path) -> None:
        self.root = tmp / "checkout"
        self.root.mkdir()
        for directory in ("python", "ts", "tools", ".githooks", "bin", "home", "evidence"):
            (self.root / directory).mkdir()
        for path in ("justfile", "tools/tt", ".githooks/pre-commit", ".githooks/pre-push"):
            shutil.copy(ROOT / path, self.root / path)
        self.env = {
            "PATH": f"{self.root / 'bin'}:{Path(_just_binary()).parent}:/usr/bin:/bin",
            "HOME": str(self.root / "home"),
            "GIT_CONFIG_GLOBAL": str(self.root / "home/gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            **_FIXTURE_IDENTITY,
            "FIXTURE_ROOT": str(self.root),
            "EVENTS": str(self.root / "events.jsonl"),
            "TT_LOG": str(self.root / "runs.jsonl"),
            "BELIEFS_CI_EVIDENCE_DIR": str(self.root / "evidence"),
            "PYTEST_XDIST_AUTO_NUM_WORKERS": "1",
        }
        init_repo(self.root, self.env)
        for name in ("uv", "npm", "npx", "tasks", "ssh"):
            self._stub(self.root / "bin" / name, _STUB.replace("NAME", repr(name)), executable=True)
        self._stub(self.root / "bin/host-budget", _HOST_BUDGET, executable=True)
        for name in ("ops-check", "ops-docs"):
            self._stub(self.root / "tools" / name, _STUB.replace("NAME", repr(name)), executable=False)
        (self.root / "python" / "tools").mkdir()
        self._stub(
            self.root / "python/tools/check_doc_links.py",
            _STUB.replace("NAME", repr("check-doc-links")),
            executable=False,
        )

    @staticmethod
    def _stub(path: Path, source: str, *, executable: bool) -> None:
        path.write_text((f"#!{sys.executable}\n" if executable else "") + source)
        if executable:
            path.chmod(0o755)

    def run(self, *args: str, stdin: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=cwd or self.root,
            env=self.env,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def just(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run("just", *args)

    def policy(self, enabled: bool = False, targets: list[str] = BROAD) -> None:
        (self.root / ".tt.toml").write_text(
            f"automatic_broad = {str(enabled).lower()}\nbroad_targets = {json.dumps(targets)}\n"
        )

    def events(self) -> list[list]:
        path = self.root / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def names(self) -> list[str]:
        return [event[0] for event in self.events()]

    def rows(self) -> list[dict]:
        path = self.root / "runs.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def set_suite_refs(self, value: str) -> None:
        path = self.root / "justfile"
        text, count = re.subn(
            r'^ci_suite_refs := ".*"$', f'ci_suite_refs := "{value}"', path.read_text(), flags=re.MULTILINE
        )
        assert count == 1
        path.write_text(text)

    def capture_hook_recipe(self) -> None:
        """Replace just at the hook boundary only, keeping its own variable evaluation."""
        wrapper = self.root / "bin/just"
        wrapper.write_text(
            f'#!/bin/sh\nif [ "$1" = --evaluate ]; then exec "{_just_binary()}" "$@"; fi\n'
            'printf "%s" "$1" > chosen\ncat > refs.actual\n'
        )
        wrapper.chmod(0o755)

    def chosen(self) -> str | None:
        path = self.root / "chosen"
        return path.read_text() if path.exists() else None


def init_repo(path: Path, env: dict[str, str]) -> None:
    """Create an isolated repository and prove that git writes stay inside it."""
    subprocess.run(["git", "init", "-q", str(path)], env=env, check=True)

    def ask(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=path, env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

    assert ask("rev-parse", "--show-toplevel") == str(path)
    assert Path(ask("rev-parse", "--absolute-git-dir")).is_relative_to(path)
