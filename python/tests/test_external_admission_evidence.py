"""Held-file checks use synthetic format fixtures and the real pinned refs parser."""

import importlib
import os
from pathlib import Path

import pytest
from admission_fixtures import NS, digest, held_evidence


def evidence():
    assert (Path(__file__).parents[1] / "tools/source_admission/evidence.py").is_file()
    return importlib.import_module("source_admission.evidence")


def refs_root():
    import refs

    return Path(refs.__file__).resolve().parents[3]


def test_real_parsers_use_held_bytes_without_fetches(tmp_path, monkeypatch):
    import socket
    import urllib.request

    _, manifest, bindings = held_evidence(tmp_path)

    def refuse(*args, **kwargs):
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    result = evidence().validate(manifest, bindings, refs_root())
    assert set(result["mappings"]) == set(manifest["units"])
    assert result["mappings"][NS + "/second"]["ucum"]["reference"] == "ucum:s"
    assert result["mappings"][NS + "/hour"]["qudt"]["reference"] == "qudt.unit:HR"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "changed",
        "symlink",
        "directory",
        "fifo",
        "unreadable",
        "wrong-release",
        "unknown-unit",
        "absent-qudt",
        "wrong-root",
    ],
)
def test_evidence_refusals(tmp_path, monkeypatch, mutation):
    _, manifest, bindings = held_evidence(tmp_path)
    ref = manifest["resources"]["ucum"]["held_ref"]
    path = bindings[ref]
    root = refs_root()
    if mutation == "missing":
        bindings.pop(ref)
    if mutation == "extra":
        bindings["sha256:" + "0" * 64] = tmp_path / "extra"
    if mutation == "changed":
        path.write_bytes(b"different")
    if mutation == "symlink":
        target = tmp_path / "target"
        path.rename(target)
        path.symlink_to(target)
    if mutation == "directory":
        path.unlink()
        path.mkdir()
    if mutation == "fifo":
        path.unlink()
        os.mkfifo(path)
    if mutation == "unreadable":
        path.chmod(0)
    if mutation == "wrong-release":
        manifest["resources"]["ucum"]["revision"] = "not-this-table"
    if mutation == "unknown-unit":
        manifest["units"][NS + "/second"]["ucum"] = "unknownSymbol"
    if mutation == "absent-qudt":
        manifest["units"][NS + "/second"]["qudt"] = "http://qudt.org/vocab/unit/MISSING"
    if mutation == "wrong-root":
        root = tmp_path
    with pytest.raises((ValueError, OSError)):
        evidence().validate(manifest, bindings, root)


@pytest.mark.parametrize(
    "body",
    [
        "<http://qudt.org/vocab/unit/SEC> <http://example.invalid/type> <http://qudt.org/schema/qudt/Unit> .",
        "<http://example.invalid/s> <http://example.invalid/p> <http://qudt.org/vocab/unit/SEC> .",
        '<http://example.invalid/s> <http://example.invalid/p> "http://qudt.org/vocab/unit/SEC" .',
        "# http://qudt.org/vocab/unit/SEC a qudt:Unit .",
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>',
        "invalid turtle",
    ],
)
def test_qudt_requires_exact_typed_subject(tmp_path, body):
    _, manifest, bindings = held_evidence(tmp_path)
    resource = manifest["resources"]["qudt"]
    path = bindings.pop(resource["held_ref"])
    path.write_text(body)
    resource.update(sha256=digest(path.read_bytes()), held_ref="sha256:" + digest(path.read_bytes()))
    bindings[resource["held_ref"]] = path
    with pytest.raises(ValueError):
        evidence().validate(manifest, bindings, refs_root())


def test_bindings_strict_and_read_once(tmp_path, monkeypatch):
    _, manifest, bindings = held_evidence(tmp_path)
    module = evidence()
    with pytest.raises(ValueError):
        module.parse_bindings(b'{"version":1,"version":1,"files":{}}')
    with pytest.raises(ValueError):
        module.parse_bindings(b'{"version":1,"files":{"sha256:x":"relative"}}')
    calls = []
    original = module.read_regular

    def observed(path):
        calls.append(path)
        data = original(path)
        path.write_bytes(b"changed after the one read")
        return data

    monkeypatch.setattr(module, "read_regular", observed)
    assert module.validate(manifest, bindings, refs_root())["mappings"]
    assert len(calls) == len(bindings) == len(set(calls))


def test_held_paths_must_be_explicitly_resolved(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    file = real / "evidence"
    file.write_bytes(b"fixture")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="resolved"):
        evidence().read_regular(alias / "evidence")
