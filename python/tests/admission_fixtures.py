"""Entirely synthetic admission records; never publisher or semantic evidence."""

import copy
import hashlib
import json

import yaml
from conftest import REPO_ROOT
from test_shipped_contract_checks import _admit, _copy_fixture_root, _inventory, _save_inventory, _write_shipped_pack

SID = "urn:beliefs:source:bipm-si-brochure"
NS = "si-brochure"
INVENTORY = "contracts/source-ownership/INVENTORY.json"
QUDT = "http://qudt.org/vocab/unit/"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def pin(label):
    value = digest(label.encode())
    return {
        "revision": "fixture-1",
        "sha256": value,
        "held_ref": "sha256:" + value,
        "locator": "https://example.invalid/" + label,
    }


def candidate(tmp_path):
    root = _copy_fixture_root(tmp_path)
    baseline = (root / INVENTORY).read_bytes()
    doc = yaml.safe_load((REPO_ROOT / "fixtures/contracts/series-time.yaml").read_text())
    for name, code, local in (("second", "s", "SEC"), ("hour", "h", "HR"), ("hertz", "Hz", "HZ")):
        doc["units"][name]["external"] = {"ucum": code, "qudt": QUDT + local}
    _write_shipped_pack(root, NS, yaml.safe_dump(doc))
    _admit(root, NS)
    inv = _inventory(root)
    row = inv["lineages"][NS]["revisions"][0]
    row["source_pin"] = {"kind": "external", "documents": [pin("normative")]}
    _save_inventory(root, inv)
    manifest = {
        "version": 1,
        "source_id": SID,
        "namespace": NS,
        "contract_identity": row["contract_identity"],
        "documents": copy.deepcopy(row["source_pin"]["documents"]),
        "resources": {"ucum": pin("ucum"), "qudt": pin("qudt")},
        "units": {NS + "/" + k: v["external"] for k, v in doc["units"].items()},
        "semantic_review_sha256": digest(b"synthetic semantic review"),
    }
    receipt = {
        "version": 1,
        "verdict": "pass",
        "mechanism": {
            "beliefs_commit": "a" * 40,
            "refs_commit": "b" * 40,
            "registry_fingerprint": "c" * 64,
            "tracked_inputs": {"beliefs/" + INVENTORY: digest(baseline)},
            "registry_files": {"grammars.toml": "d" * 64},
            "distributions": {"rdflib": "7.6.0"},
        },
        "baseline": {"commit": "a" * 40, "sha256": digest(baseline), "inventory_utf8": baseline.decode()},
        "candidate": {
            "sha256": digest((root / INVENTORY).read_bytes()),
            "inventory_utf8": (root / INVENTORY).read_text(),
        },
        "coverage": {
            "source_id": SID,
            "owner": inv["sources"][SID]["owner"],
            "namespace": NS,
            "row": copy.deepcopy(row),
        },
        "manifest_sha256": digest(encode(manifest)),
        "semantic_review_sha256": manifest["semantic_review_sha256"],
        "resources": manifest["resources"],
        "mappings": {},
    }
    for key, mapping in manifest["units"].items():
        receipt["mappings"][key] = {
            "ucum": {
                "code": mapping["ucum"],
                "reference": "ucum:" + mapping["ucum"],
                "release": "fixture-1",
                "evidence_sha256": manifest["resources"]["ucum"]["sha256"],
                "verdict": "pass",
            },
            "qudt": {
                "iri": mapping["qudt"],
                "reference": "qudt.unit:" + mapping["qudt"][len(QUDT) :],
                "release": "fixture-1",
                "evidence_sha256": manifest["resources"]["qudt"]["sha256"],
                "verdict": "pass",
            },
        }
    return root, manifest, receipt


def install(checker, root, receipt):
    data = encode(receipt)
    relative = "contracts/source-ownership/receipts/" + digest(data) + ".json"
    path = root / relative
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data)
    checker.RECEIPT_SHA256 = {relative: digest(data)}
    checker.SOURCE_INVENTORY_SHA256 = digest((root / INVENTORY).read_bytes())
    return path


def held_evidence(tmp_path):
    root, manifest, _receipt = candidate(tmp_path)
    held = tmp_path / "held"
    held.mkdir()
    payloads = {
        "normative": b"synthetic normative document",
        "ucum": (REPO_ROOT / "python/tests/fixtures/admission/ucum-essence.xml").read_bytes(),
        "qudt": (REPO_ROOT / "python/tests/fixtures/admission/qudt.ttl").read_bytes(),
        "review": b"synthetic semantic review",
    }
    bindings = {}
    for key, data in payloads.items():
        sha = digest(data)
        path = held / key
        path.write_bytes(data)
        bindings["sha256:" + sha] = path
        if key == "review":
            manifest["semantic_review_sha256"] = sha
        else:
            value = {
                "revision": "fixture-1",
                "sha256": sha,
                "held_ref": "sha256:" + sha,
                "locator": "https://example.invalid/" + key,
            }
            if key == "normative":
                manifest["documents"] = [value]
            else:
                manifest["resources"][key] = value
    inv = _inventory(root)
    inv["lineages"][NS]["revisions"][0]["source_pin"]["documents"] = manifest["documents"]
    _save_inventory(root, inv)
    return root, manifest, bindings


def mechanism_layout(tmp_path):
    """Build a clean disposable sibling layout with its own frozen Python environment."""
    import importlib
    import shutil
    import subprocess
    import sysconfig
    import venv
    from pathlib import Path

    from route_fixtures import Checkout, init_repo

    checkout = Checkout(tmp_path)
    ignore = shutil.ignore_patterns(
        ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".testmondata*", "*.egg-info"
    )
    for name in ("contracts", "domains", "fixtures", "python", "docs", ".githooks"):
        shutil.copytree(REPO_ROOT / name, checkout.root / name, dirs_exist_ok=True, ignore=ignore)
    for name in (".gitignore", ".tt.toml", "justfile", "README.md", "AGENTS.md"):
        shutil.copyfile(REPO_ROOT / name, checkout.root / name)
    # The real hook and shipped-contract checker run. Unrelated host-wide hygiene
    # commands remain the route fixture's explicit stubs.
    (checkout.root / "python/tools/check_doc_links.py").write_text(
        "# fixture: doc links are outside this admission test\n"
    )
    for name in ("refs", "atoms", "nodes"):
        source = Path(next(iter(importlib.import_module(name).__path__))).resolve().parents[2]
        root = tmp_path / name
        root.mkdir()
        init_repo(root, checkout.env)
        (root / "python").mkdir()
        for file in ("pyproject.toml", "uv.lock", "README.md", "LICENSE"):
            if (source / "python" / file).exists():
                shutil.copyfile(source / "python" / file, root / "python" / file)
        shutil.copytree(source / "python/src", root / "python/src", ignore=ignore)
        (root / ".gitignore").write_text(".venv/\n__pycache__/\npython/src/refs/data/\n")
        if name == "refs":
            shutil.copytree(source / "registry", root / "registry")
        assert checkout.run("git", "add", ".", cwd=root).returncode == 0
        result = checkout.run("git", "commit", "-qm", "synthetic dependency snapshot", cwd=root)
        assert result.returncode == 0, result.stderr
    checkout._stub(
        checkout.root / "bin/uv",
        "import os, sys\nfrom pathlib import Path\n"
        + "assert sys.argv[1:4] == ['run', '--frozen', 'python']\n"
        + "python = "
        + repr(str(checkout.root / "python/.venv/bin/python"))
        + "\n"
        + "os.execv(python, [python, str(Path.cwd() / sys.argv[4]), *sys.argv[5:]])\n",
        executable=True,
    )
    assert checkout.run("git", "add", ".").returncode == 0
    result = checkout.run("git", "commit", "-qm", "synthetic mechanism snapshot")
    assert result.returncode == 0, result.stderr
    # Reuse only the distributions installed by this test run's frozen uv route.
    # A new venv excludes editable .pth files; its own sibling .pth supplies the
    # four fixture checkouts. No user config, package download or shared edit.
    virtual = checkout.root / "python/.venv"
    venv.EnvBuilder(with_pip=False).create(virtual)
    libraries = list((virtual / "lib").glob("python*/site-packages"))
    assert len(libraries) == 1
    library = libraries[0]
    for entry in Path(sysconfig.get_paths()["purelib"]).iterdir():
        if entry.suffix == ".pth" or entry.name == "__pycache__":
            continue
        (library / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
    (library / "admission-siblings.pth").write_text(
        "\n".join(
            str(p / "python/src") for p in (checkout.root, tmp_path / "refs", tmp_path / "atoms", tmp_path / "nodes")
        )
        + "\n"
    )
    run_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(checkout.root / "home"),
        "GIT_CONFIG_GLOBAL": checkout.env["GIT_CONFIG_GLOBAL"],
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    candidate_root = tmp_path / "candidate"
    assert checkout.run("git", "worktree", "add", str(candidate_root), "-b", "candidate").returncode == 0
    generated_root, manifest, bindings = held_evidence(tmp_path / "inputs")
    for relative in ("domains/si-brochure", "python/src/beliefs/domains/si-brochure"):
        shutil.copytree(generated_root / relative, candidate_root / relative)
    shutil.copyfile(generated_root / INVENTORY, candidate_root / INVENTORY)
    checker = candidate_root / "python/tools/check_shipped_contracts.py"
    checker.write_text(
        checker.read_text().replace(
            digest((checkout.root / INVENTORY).read_bytes()), digest((candidate_root / INVENTORY).read_bytes())
        )
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(encode(manifest))
    bindings_path = tmp_path / "bindings.json"
    bindings_path.write_bytes(encode({"version": 1, "files": {ref: str(path) for ref, path in bindings.items()}}))
    refs_sha = checkout.run("git", "rev-parse", "HEAD", cwd=tmp_path / "refs").stdout.strip()
    python = checkout.root / "python/.venv/bin/python"
    command = [str(python), "-I", str(checkout.root / "python/tools/admit_external_source.py")]
    args = [
        "--candidate",
        str(candidate_root),
        "--manifest",
        str(manifest_path),
        "--bindings",
        str(bindings_path),
        "--refs-root",
        str(tmp_path / "refs"),
        "--refs-commit",
        refs_sha,
    ]

    def run(extra):
        return subprocess.run(command + extra, env=run_env, capture_output=True, text=True, check=False, timeout=120)

    return checkout, candidate_root, args, run
