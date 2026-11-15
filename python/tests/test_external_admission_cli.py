"""CLI refusal cannot overwrite evidence or execute code from the candidate."""

import importlib
from pathlib import Path


def cli():
    assert (Path(__file__).parents[1] / "tools/admit_external_source.py").is_file()
    return importlib.import_module("admit_external_source")


def test_cli_missing_input_refuses_without_receipt(tmp_path):
    output = tmp_path / "receipt.json"
    args = [
        "--candidate",
        str(tmp_path),
        "--manifest",
        str(tmp_path / "missing"),
        "--bindings",
        str(tmp_path / "bindings"),
        "--refs-root",
        str(tmp_path / "refs"),
        "--refs-commit",
        "a" * 40,
        "--output",
        str(output),
    ]
    assert cli().main(args) == 1
    assert not output.exists()
    output.write_bytes(b"earlier receipt")
    assert cli().main(args) == 1
    assert output.read_bytes() == b"earlier receipt"


def test_staged_mode_is_check_only(tmp_path):
    assert cli().main(["--check-staged", str(tmp_path), "--receipt", str(tmp_path / "missing")]) == 1
    assert list(tmp_path.iterdir()) == []


def test_clean_cli_produces_deterministic_receipt_and_checks_index(tmp_path):
    import json

    from admission_fixtures import digest, mechanism_layout

    checkout, candidate, args, run = mechanism_layout(tmp_path)
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    result = run(args + ["--output", str(first)])
    assert result.returncode == 0, result.stderr
    result = run(args + ["--output", str(second)])
    assert result.returncode == 0, result.stderr
    assert first.read_bytes() == second.read_bytes()
    receipt = json.loads(first.read_bytes())
    assert receipt["verdict"] == "pass"
    assert str(tmp_path) not in first.read_text()
    assert "records/" not in first.read_text()
    relative = "contracts/source-ownership/receipts/" + digest(first.read_bytes()) + ".json"
    target = candidate / relative
    target.parent.mkdir()
    target.write_bytes(first.read_bytes())
    checker = candidate / "python/tools/check_shipped_contracts.py"
    checker.write_text(
        checker.read_text().replace(
            "RECEIPT_SHA256: dict[str, str] = {}",
            "RECEIPT_SHA256: dict[str, str] = " + repr({relative: digest(first.read_bytes())}),
        )
    )
    assert checkout.run("git", "add", ".", cwd=candidate).returncode == 0
    result = run(["--check-staged", str(candidate), "--receipt", str(target)])
    assert result.returncode == 0, result.stderr
    result = run(args + ["--output", str(tmp_path / "refused.json")])
    assert result.returncode == 1 and "staged" in result.stderr
    assert not (tmp_path / "refused.json").exists()
    checker.write_text(checker.read_text() + "# unreviewed checker change\n")
    assert checkout.run("git", "add", ".", cwd=candidate).returncode == 0
    result = run(["--check-staged", str(candidate), "--receipt", str(target)])
    assert result.returncode == 1 and "beyond literal pins" in result.stderr


def isolated_invocation(tmp_path, monkeypatch):
    import copy

    from admission_fixtures import INVENTORY, candidate, digest, encode, held_evidence
    from refs import Registry
    from test_external_admission_evidence import refs_root

    module = cli()
    root, manifest, bindings = held_evidence(tmp_path)
    _, _, model = candidate(tmp_path / "metadata")
    state = {
        "mechanism": model["mechanism"],
        "baseline": model["baseline"],
        "candidate_files": {},
        "pins": {"SOURCE_INVENTORY_SHA256": digest((root / INVENTORY).read_bytes()), "RECEIPT_SHA256": {}},
    }
    state["mechanism"]["registry_fingerprint"] = Registry.default().fingerprint
    monkeypatch.setattr(module.environment, "verify", lambda *args: copy.deepcopy(state))
    manifest_path, bindings_path = tmp_path / "manifest.json", tmp_path / "bindings.json"
    manifest_path.write_bytes(encode(manifest))
    bindings_path.write_bytes(encode({"version": 1, "files": {ref: str(path) for ref, path in bindings.items()}}))
    output = tmp_path / "out.json"
    args = [
        "--candidate",
        str(root),
        "--manifest",
        str(manifest_path),
        "--bindings",
        str(bindings_path),
        "--refs-root",
        str(refs_root()),
        "--refs-commit",
        "b" * 40,
        "--output",
        str(output),
    ]
    return module, args, output, state


def test_concurrent_candidate_change_refuses_before_publication(tmp_path, monkeypatch):
    module, args, output, state = isolated_invocation(tmp_path, monkeypatch)
    original = module.evidence.validate

    def changed(*args):
        result = original(*args)
        state["candidate_files"]["changed"] = "0" * 64
        return result

    monkeypatch.setattr(module.evidence, "validate", changed)
    assert module.main(args) == 1
    assert not output.exists()


def test_write_failure_removes_only_own_partial_output(tmp_path, monkeypatch):
    module, args, output, _ = isolated_invocation(tmp_path, monkeypatch)

    def failed(fd):
        raise OSError("synthetic write failure")

    monkeypatch.setattr(module.os, "fsync", failed)
    assert module.main(args) == 1
    assert not output.exists()


def test_write_failure_preserves_replaced_destination(tmp_path, monkeypatch):
    module, args, output, _ = isolated_invocation(tmp_path, monkeypatch)

    def replaced(fd):
        output.unlink(missing_ok=True)
        output.write_bytes(b"another writer owns these bytes")
        raise OSError("synthetic write failure after replacement")

    monkeypatch.setattr(module.os, "fsync", replaced)
    assert module.main(args) == 1
    assert output.read_bytes() == b"another writer owns these bytes"
