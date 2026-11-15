"""Git and import provenance for a clean mechanism and a separate candidate."""

from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import importlib.util
import os
import re
import subprocess
from pathlib import Path

from source_admission import metadata

__all__ = ["check_registry", "git", "normalize_checker", "tracked_bytes", "verify", "verify_candidate", "verify_staged"]
CHECKER = "python/tools/check_shipped_contracts.py"
INVENTORY = "contracts/source-ownership/INVENTORY.json"
PINS = {"SOURCE_INVENTORY_SHA256", "RECEIPT_SHA256"}


def git(root: Path, *args: str) -> bytes:
    # A surrounding Git hook must never redirect a fixture/candidate operation.
    env = {"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    result = subprocess.run(["git", "-C", str(root), *args], env=env, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"Git refused {args[0]} in selected checkout")
    return result.stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_checker(data: bytes) -> tuple[bytes, dict]:
    try:
        tree = ast.parse(data)
    except SyntaxError as exc:
        raise ValueError("invalid checker syntax") from exc
    lines = data.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    spans = []
    pins = {}
    # Only top-level single assignments qualify; duplicates anywhere refuse.
    for node in ast.walk(tree):
        targets = (
            node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        )
        names = {n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name)} & PINS
        if not names:
            continue
        if (
            node not in tree.body
            or len(targets) != 1
            or not isinstance(targets[0], ast.Name)
            or len(names) != 1
            or node.value is None
        ):
            raise ValueError("checker pin must be a single top-level literal assignment")
        name = names.pop()
        if name in pins:
            raise ValueError("duplicate checker pin assignment")
        try:
            pins[name] = ast.literal_eval(node.value)
        except (ValueError, TypeError) as exc:
            raise ValueError("checker pin is not literal") from exc
        value = node.value
        spans.append(
            (offsets[value.lineno - 1] + value.col_offset, offsets[value.end_lineno - 1] + value.end_col_offset)
        )
    if set(pins) != PINS:
        raise ValueError("missing checker pin assignment")
    metadata.hex_digest(pins["SOURCE_INVENTORY_SHA256"], "inventory pin")
    if not isinstance(pins["RECEIPT_SHA256"], dict):
        raise TypeError("receipt pins must be a map")
    for name, sha in pins["RECEIPT_SHA256"].items():
        metadata.hex_digest(sha, "receipt pin")
        if name != f"contracts/source-ownership/receipts/{sha}.json":
            raise ValueError("receipt pin path must be digest-named")
    normalized = data
    for start, end in sorted(spans, reverse=True):
        normalized = normalized[:start] + b"None" + normalized[end:]
    return normalized, pins


def allowed(path: str, status: str) -> bool:
    if path in {
        CHECKER,
        INVENTORY,
        "python/tests/time_roles_fixture.py",
        "ts/tests/parity.test.ts",
        "docs/contracts.md",
        "docs/development.md",
    }:
        return True
    if path == "fixtures/contracts/series-time.yaml":
        return status == "D"
    if re.fullmatch(r"contracts/source-ownership/receipts/[0-9a-f]{64}\.json", path):
        return status in {"A", "?"}
    return (
        re.fullmatch(
            r"(?:python/src/beliefs/)?domains/si-brochure/(?:history/[0-9a-f]{64}/)?(?:DOMAIN\.yaml|REGISTER\.json)",
            path,
        )
        is not None
    )


def tracked_bytes(root: Path, *, index: bool = False) -> dict[str, bytes]:
    paths = git(root, "ls-files", "-z").decode().split("\0")[:-1]
    result = {}
    for path in paths:
        metadata.canonical_path(path)
        file = root / path
        if index:
            result[path] = git(root, "show", ":" + path)
        elif file.exists():
            if file.is_symlink():
                raise ValueError(f"tracked symlink input refused: {path}")
            result[path] = file.read_bytes()
    return result


def clean(root: Path) -> str:
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
        raise ValueError("expected checkout root")
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("dirty tracked mechanism/dependency files")
    # Include ignored import overrides: ordinary --others --exclude-standard misses them.
    for relative in git(root, "ls-files", "--others", "-z").decode().split("\0")[:-1]:
        parts = Path(relative).parts
        if any(p in {".venv", "node_modules", "__pycache__", ".git"} for p in parts):
            continue
        if relative.startswith("python/src/refs/data/"):
            continue  # exact equality checked separately
        if Path(relative).suffix in {".py", ".pyc", ".so", ".pth", ".pyd", ".toml"} or os.access(
            root / relative, os.X_OK
        ):
            raise ValueError(f"untracked importable/executable override: {relative}")
    return git(root, "rev-parse", "HEAD").decode().strip()


def verify_candidate(mechanism: Path, candidate: Path, *, staged: bool = False) -> dict:
    mechanism, candidate = mechanism.resolve(), candidate.resolve()
    head = clean(mechanism)
    if candidate == mechanism:
        raise ValueError("candidate must be a separate linked worktree")
    if Path(git(candidate, "rev-parse", "--show-toplevel").decode().strip()).resolve() != candidate:
        raise ValueError("candidate must be checkout root")

    def common(root):
        return Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip()).resolve()

    if common(mechanism) != common(candidate):
        raise ValueError("candidate must be a linked worktree of mechanism repository")
    if git(candidate, "rev-parse", "HEAD").decode().strip() != head:
        raise ValueError("candidate HEAD must equal mechanism HEAD")
    if not staged and git(candidate, "diff", "--cached", "--name-only").strip():
        raise ValueError("staged candidate changes refused before admission")
    if staged and git(candidate, "diff", "--name-only").strip():
        raise ValueError("unstaged changes refused during final staged check")
    options = ["--cached"] if staged else []
    changes = git(candidate, "diff", *options, "--name-status", "--no-renames", "-z").decode().split("\0")[:-1]
    for status, path in zip(changes[::2], changes[1::2], strict=True):
        if not allowed(path, status):
            raise ValueError(f"candidate path not permitted: {path}")
    files = tracked_bytes(candidate, index=staged)
    for path in git(candidate, "ls-files", "--others", "-z").decode().split("\0")[:-1]:
        parts = Path(path).parts
        if any(p in {".venv", "node_modules", "__pycache__", ".git"} for p in parts):
            continue
        if not allowed(path, "?"):
            raise ValueError(f"untracked candidate path not permitted: {path}")
        if staged:
            raise ValueError("untracked admission input absent from candidate index")
        file = candidate / path
        if file.is_symlink() or not file.is_file():
            raise ValueError("candidate input must be regular file")
        if os.access(file, os.X_OK):
            raise ValueError("untracked executable candidate input refused")
        files[path] = file.read_bytes()
    if staged:
        for entry in git(candidate, "ls-files", "--stage", "-z").split(b"\0")[:-1]:
            mode, _, stage_path = entry.split(b" ", 2)
            if mode not in {b"100644", b"100755"} or not stage_path.startswith(b"0\t"):
                raise ValueError("candidate index has nonregular or unmerged entry")
    original = git(mechanism, "show", "HEAD:" + CHECKER)
    if CHECKER not in files or normalize_checker(original)[0] != normalize_checker(files[CHECKER])[0]:
        raise ValueError("candidate checker differs beyond literal pins")
    return {"head": head, "files": files, "pins": normalize_checker(files[CHECKER])[1]}


def check_registry(root: Path) -> dict[str, str]:
    tracked = git(root, "ls-files", "-z", "registry").decode().split("\0")[:-1]
    expected = {Path(p).name: (root / p).read_bytes() for p in tracked}
    data = root / "python/src/refs/data"
    actual = (
        {p.name: p.read_bytes() for p in data.iterdir() if p.is_file() and not p.is_symlink()} if data.is_dir() else {}
    )
    if not expected or actual != expected or {p.name for p in data.iterdir()} != set(expected):
        raise ValueError("refs generated registry differs from tracked inputs")
    return {name: digest(data) for name, data in expected.items()}


def import_root(name: str) -> Path:
    spec = importlib.util.find_spec(name)
    locations = [] if spec is None else list(spec.submodule_search_locations or [])
    if len(locations) != 1:
        raise ValueError(f"unresolved or ambiguous imported package: {name}")
    return Path(locations[0]).resolve().parents[2]


def verify(mechanism: Path, candidate: Path, refs_root: Path, refs_commit: str) -> dict:
    state = verify_candidate(mechanism, candidate)
    metadata.commit(refs_commit, "refs revision")
    roots = {
        "beliefs": mechanism.resolve(),
        "refs": refs_root.resolve(),
        "atoms": mechanism.resolve().parent / "atoms",
        "nodes": mechanism.resolve().parent / "nodes",
    }
    tracked = {}
    for name, root in roots.items():
        root = root.resolve()
        revision = clean(root)
        if name == "refs" and revision != refs_commit:
            raise ValueError("refs HEAD differs from expected revision")
        if import_root(name) != root:
            raise ValueError(f"wrong imported {name} root")
        for path, data in tracked_bytes(root).items():
            qualifier = name if name in {"beliefs", "refs"} else f"{name}/{revision}"
            tracked[f"{qualifier}/{path}"] = digest(data)
    registry_files = check_registry(refs_root)
    baseline = git(mechanism, "show", "HEAD:" + INVENTORY)
    baseline_pin = normalize_checker(git(mechanism, "show", "HEAD:" + CHECKER))[1]["SOURCE_INVENTORY_SHA256"]
    if digest(baseline) != baseline_pin:
        raise ValueError("baseline inventory differs from mechanism pin")
    from refs import Registry

    distributions = {
        name: importlib.metadata.version(name)
        for name in (
            "verifiably-beliefs",
            "verifiably-refs",
            "verifiably-atoms",
            "verifiably-nodes",
            "rdflib",
            "pyparsing",
            "pydantic",
            "PyYAML",
            "rfc8785",
        )
    }
    return {
        "mechanism": {
            "beliefs_commit": state["head"],
            "refs_commit": refs_commit,
            "registry_fingerprint": Registry.default().fingerprint,
            "tracked_inputs": tracked,
            "registry_files": registry_files,
            "distributions": distributions,
        },
        "baseline": {"commit": state["head"], "sha256": digest(baseline), "inventory_utf8": baseline.decode()},
        "candidate_files": {path: digest(data) for path, data in state["files"].items()},
        "pins": state["pins"],
    }


def verify_staged(mechanism: Path, candidate: Path) -> dict:
    return verify_candidate(mechanism, candidate, staged=True)
