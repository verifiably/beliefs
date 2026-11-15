"""Git provenance and candidate deltas, with fixture-only Git configuration."""

import importlib
from pathlib import Path

import pytest
from route_fixtures import Checkout

CHECKER = "python/tools/check_shipped_contracts.py"


def environment():
    assert (Path(__file__).parents[1] / "tools/source_admission/environment.py").is_file()
    return importlib.import_module("source_admission.environment")


def test_checker_allows_only_literal_pin_value_changes():
    module = environment()
    source = b'# keep comments\nSOURCE_INVENTORY_SHA256 = "' + b"a" * 64 + b'"\nRECEIPT_SHA256: dict[str, str] = {}\n'
    updated = source.replace(b"a" * 64, b"b" * 64).replace(
        b"= {}", b'= {"contracts/source-ownership/receipts/' + b"c" * 64 + b'.json": "' + b"c" * 64 + b'"}'
    )
    assert module.normalize_checker(source)[0] == module.normalize_checker(updated)[0]
    assert module.normalize_checker(source + b"# edited\n")[0] != module.normalize_checker(source)[0]
    for bad in (
        source + b'SOURCE_INVENTORY_SHA256 = "x"\n',
        source.replace(b"= {}", b"= dict()"),
        source.replace(b"RECEIPT_SHA256", b"OTHER"),
    ):
        with pytest.raises(ValueError):
            module.normalize_checker(bad)


def fixture_layout(tmp_path):
    checkout = Checkout(tmp_path)
    checker = checkout.root / CHECKER
    checker.write_text('SOURCE_INVENTORY_SHA256 = "' + "a" * 64 + '"\nRECEIPT_SHA256: dict[str, str] = {}\n')
    assert checkout.run("git", "add", ".").returncode == 0
    assert checkout.run("git", "commit", "-qm", "mechanism").returncode == 0
    candidate = tmp_path / "candidate"
    assert checkout.run("git", "worktree", "add", str(candidate), "-b", "candidate").returncode == 0
    return checkout, candidate


@pytest.mark.parametrize(
    "mutation", ["allowed", "checker-code", "config", "untracked-python", "staged", "different-head", "same-root"]
)
def test_candidate_delta_policy(tmp_path, monkeypatch, mutation):
    module = environment()
    checkout, candidate = fixture_layout(tmp_path)
    for name in list(__import__("os").environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", checkout.env["GIT_CONFIG_GLOBAL"])
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    if mutation == "allowed":
        (candidate / CHECKER).write_text((candidate / CHECKER).read_text().replace("a" * 64, "b" * 64))
    if mutation == "checker-code":
        (candidate / CHECKER).write_text((candidate / CHECKER).read_text() + "print('wrong')\n")
    if mutation == "config":
        (candidate / "python/pyproject.toml").write_text("[project]")
    if mutation == "untracked-python":
        (candidate / "python/tools/override.py").write_text("bad = True")
    if mutation == "staged":
        (candidate / CHECKER).write_text((candidate / CHECKER).read_text().replace("a" * 64, "b" * 64))
        assert checkout.run("git", "add", CHECKER, cwd=candidate).returncode == 0
    if mutation == "different-head":
        assert checkout.run("git", "commit", "--allow-empty", "-qm", "advance", cwd=candidate).returncode == 0
    if mutation == "same-root":
        candidate = checkout.root
    if mutation == "allowed":
        assert module.verify_candidate(checkout.root, candidate)
    else:
        with pytest.raises(ValueError):
            module.verify_candidate(checkout.root, candidate)


def test_clean_rejects_ignored_override_and_changed_registry(tmp_path):
    module = environment()
    checkout, _ = fixture_layout(tmp_path)
    (checkout.root / ".gitignore").write_text("python/src/refs/data/\npython/tools/ignored.py\n")
    registry = checkout.root / "registry"
    registry.mkdir()
    (registry / "grammars.toml").write_text("tracked registry")
    assert checkout.run("git", "add", ".").returncode == 0
    assert checkout.run("git", "commit", "-qm", "registry").returncode == 0
    data = checkout.root / "python/src/refs/data"
    data.mkdir(parents=True)
    (data / "grammars.toml").write_text("tracked registry")
    assert module.check_registry(checkout.root)
    (data / "grammars.toml").write_text("stale registry")
    with pytest.raises(ValueError, match="registry"):
        module.check_registry(checkout.root)
    (checkout.root / "python/tools/ignored.py").write_text("override = True")
    with pytest.raises(ValueError, match="override"):
        module.clean(checkout.root)


@pytest.mark.parametrize("mutation", ["clean", "wrong-revision", "dirty-dependency", "wrong-import", "baseline-pin"])
def test_verified_provenance_binds_git_and_import_roots(tmp_path, monkeypatch, mutation):
    import shutil

    from admission_fixtures import digest
    from route_fixtures import init_repo

    module = environment()
    checkout, candidate = fixture_layout(tmp_path)
    inv = b'{"version":1,"sources":{},"lineages":{}}\n'
    path = checkout.root / module.INVENTORY
    path.parent.mkdir(parents=True)
    path.write_bytes(inv)
    checker = checkout.root / CHECKER
    checker.write_text(checker.read_text().replace("a" * 64, digest(inv)))
    assert checkout.run("git", "add", ".").returncode == 0
    assert checkout.run("git", "commit", "-qm", "baseline").returncode == 0
    assert checkout.run("git", "reset", "--hard", "master", cwd=candidate).returncode == 0
    roots = {"beliefs": checkout.root}
    for name in ("refs", "atoms", "nodes"):
        root = tmp_path / name
        root.mkdir()
        init_repo(root, checkout.env)
        (root / "code.py").write_text("fixture = True")
        if name == "refs":
            (root / "registry").mkdir()
            (root / "registry/grammars.toml").write_text("fixture")
            (root / ".gitignore").write_text("python/src/refs/data/\n")
        assert checkout.run("git", "add", ".", cwd=root).returncode == 0
        assert checkout.run("git", "commit", "-qm", "dependency", cwd=root).returncode == 0
        roots[name] = root
    (roots["refs"] / "python/src/refs").mkdir(parents=True)
    shutil.copytree(roots["refs"] / "registry", roots["refs"] / "python/src/refs/data")
    monkeypatch.setattr(module, "import_root", lambda name: roots[name] if mutation != "wrong-import" else tmp_path)
    monkeypatch.setattr(module.importlib.metadata, "version", lambda name: "fixture-version")
    refs_sha = checkout.run("git", "rev-parse", "HEAD", cwd=roots["refs"]).stdout.strip()
    if mutation == "wrong-revision":
        refs_sha = "0" * 40
    if mutation == "dirty-dependency":
        (roots["atoms"] / "code.py").write_text("changed = True")
    if mutation == "baseline-pin":
        checker.write_text(checker.read_text().replace(digest(inv), "a" * 64))
        assert checkout.run("git", "add", CHECKER).returncode == 0
        assert checkout.run("git", "commit", "-qm", "bad pin").returncode == 0
        assert checkout.run("git", "reset", "--hard", "master", cwd=candidate).returncode == 0
    if mutation == "clean":
        result = module.verify(checkout.root, candidate, roots["refs"], refs_sha)
        assert result["baseline"]["sha256"] == digest(inv)
        assert result["mechanism"]["refs_commit"] == refs_sha
        assert any(p.startswith("atoms/") and p.endswith("code.py") for p in result["mechanism"]["tracked_inputs"])
    else:
        with pytest.raises(ValueError):
            module.verify(checkout.root, candidate, roots["refs"], refs_sha)


def test_staged_check_rejects_code_and_unstaged_change(tmp_path):
    module = environment()
    checkout, candidate = fixture_layout(tmp_path)
    path = candidate / CHECKER
    path.write_text(path.read_text().replace("a" * 64, "b" * 64))
    assert checkout.run("git", "add", CHECKER, cwd=candidate).returncode == 0
    assert module.verify_staged(checkout.root, candidate)
    path.write_text(path.read_text() + "# unstaged\n")
    with pytest.raises(ValueError, match="unstaged"):
        module.verify_staged(checkout.root, candidate)
    assert checkout.run("git", "add", CHECKER, cwd=candidate).returncode == 0
    with pytest.raises(ValueError, match="beyond literal pins"):
        module.verify_staged(checkout.root, candidate)


def test_candidate_refuses_executable_domain_input(tmp_path):
    module = environment()
    checkout, candidate = fixture_layout(tmp_path)
    path = candidate / "domains/si-brochure/DOMAIN.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("not executable data")
    path.chmod(0o755)
    with pytest.raises(ValueError, match="executable"):
        module.verify_candidate(checkout.root, candidate)


def test_actual_namespace_dependencies_have_one_resolved_root():
    import atoms
    import nodes

    for name, package in (("atoms", atoms), ("nodes", nodes)):
        paths = list(package.__path__)
        assert len(paths) == 1
        assert environment().import_root(name) == Path(paths[0]).resolve().parents[2]


def test_malformed_checker_is_a_validation_refusal():
    with pytest.raises(ValueError, match="syntax"):
        environment().normalize_checker(b"this is not valid Python !!!")
