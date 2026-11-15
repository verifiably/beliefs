"""Validate an offline candidate from this clean checkout; never execute candidate code."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

MECHANISM = Path(__file__).resolve().parents[2]
# Isolated Python ignores PYTHONPATH; only the clean launcher's own source is added.
sys.path[:0] = [str(MECHANISM / "python/tools"), str(MECHANISM / "python/src")]

import check_shipped_contracts as checker
from source_admission import environment, evidence, metadata

from beliefs.errors import ScienceError

__all__ = ["main"]
INVENTORY = "contracts/source-ownership/INVENTORY.json"


def _inventory(data: bytes) -> dict:
    return checker._validate_inventory(metadata.decode(data))


def _candidate(root: Path, manifest: dict, baseline: dict) -> tuple[bytes, dict]:
    data = (root / INVENTORY).read_bytes()
    inventory = _inventory(data)
    errors = checker.inspect_candidate(root, data)
    if errors:
        raise ValueError("; ".join(errors))
    metadata.check_continuity(baseline, inventory)
    ns, sid = manifest["namespace"], manifest["source_id"]
    if ns != "si-brochure" or sid != "urn:beliefs:source:bipm-si-brochure":
        raise ValueError("this route admits only the accepted SI Brochure lineage")
    lineage = inventory["lineages"].get(ns)
    if lineage is None or lineage["source_id"] != sid:
        raise ValueError("manifest source/namespace absent from candidate")
    matches = [row for row in lineage["revisions"] if row["contract_identity"] == manifest["contract_identity"]]
    if len(matches) != 1:
        raise ValueError("manifest revision absent from candidate")
    row = matches[0]
    if row["source_pin"] != {"kind": "external", "documents": manifest["documents"]}:
        raise ValueError("manifest documents disagree with candidate")
    existing = {r["contract_identity"] for line in baseline["lineages"].values() for r in line["revisions"]}
    if row["contract_identity"] in existing:
        raise ValueError("already admitted revision cannot be readmitted as changed history")
    for other_ns, line in inventory["lineages"].items():
        for other in line["revisions"]:
            if (
                other["source_pin"]["kind"] == "external"
                and other["contract_identity"] not in existing
                and (other_ns, other["contract_identity"]) != (ns, row["contract_identity"])
            ):
                raise ValueError("candidate contains another uncovered external revision")
    base = checker._load_base(root, [])
    revisions, errors = checker._discover_shipped_domains(root, base)
    if errors:
        raise ValueError("; ".join(errors))
    revision = next(
        r for r in revisions if r.contract.namespace == ns and r.contract.content_identity == row["contract_identity"]
    )
    actual = {
        f"{ns}/{name}": {
            "ucum": unit.external.get("ucum") if unit.external else None,
            "qudt": unit.external.get("qudt") if unit.external else None,
        }
        for name, unit in revision.contract.units.items()
    }
    if actual != manifest["units"]:
        raise ValueError("manifest unit mappings incomplete or disagree with candidate")
    return data, {"source_id": sid, "namespace": ns, "owner": inventory["sources"][sid]["owner"], "row": row}


def _retained_pins(candidate_pins: dict) -> None:
    for path, sha in checker.RECEIPT_SHA256.items():
        if candidate_pins["RECEIPT_SHA256"].get(path) != sha:
            raise ValueError("historical receipt pin changed or removed")


def _staged(candidate: Path, receipt_path: Path) -> None:
    state = environment.verify_staged(MECHANISM, candidate)
    relative = receipt_path.resolve().relative_to(candidate.resolve()).as_posix()
    if relative not in state["files"]:
        raise ValueError("receipt is absent from index")
    receipt = metadata.parse_receipt(state["files"][relative])
    if receipt["mechanism"]["beliefs_commit"] != state["head"]:
        raise ValueError("receipt mechanism is not candidate HEAD")
    baseline = environment.git(MECHANISM, "show", "HEAD:" + INVENTORY)
    if (
        receipt["baseline"]["inventory_utf8"].encode() != baseline
        or hashlib.sha256(baseline).hexdigest() != checker.SOURCE_INVENTORY_SHA256
    ):
        raise ValueError("receipt baseline differs from clean mechanism")
    data = state["files"][INVENTORY]
    if (
        receipt["candidate"]["inventory_utf8"].encode() != data
        or state["pins"]["SOURCE_INVENTORY_SHA256"] != hashlib.sha256(data).hexdigest()
    ):
        raise ValueError("staged candidate inventory differs from receipt/pin")
    _retained_pins(state["pins"])
    if state["pins"]["RECEIPT_SHA256"].get(relative) != hashlib.sha256(state["files"][relative]).hexdigest():
        raise ValueError("staged receipt is not independently pinned")
    # Materialize index bytes as data for existing parsers; no executable is run.
    with tempfile.TemporaryDirectory(prefix="beliefs-admission-index-") as directory:
        root = Path(directory)
        for path, payload in state["files"].items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        inventory = _inventory(data)
        errors, revisions = checker._inspect(root, inventory, checker.HERITAGE_REPRODUCTION_EXCLUSIONS)
        if errors:
            raise ValueError("; ".join(errors))
        checker._check_receipts(root, inventory, revisions, pins=state["pins"]["RECEIPT_SHA256"])
    if environment.verify_staged(MECHANISM, candidate) != state:
        raise ValueError("candidate index changed during staged check")


def _admit(args) -> None:
    candidate, refs_root = Path(args.candidate).resolve(), Path(args.refs_root).resolve()
    output = Path(args.output).absolute()
    if output.resolve().is_relative_to(candidate):
        raise ValueError("receipt output must be outside candidate")
    if output.exists() or output.is_symlink():
        raise ValueError("receipt output already exists")
    manifest_path, bindings_path = Path(args.manifest).absolute(), Path(args.bindings).absolute()
    manifest_bytes, bindings_bytes = evidence.read_regular(manifest_path), evidence.read_regular(bindings_path)
    manifest = metadata.parse_manifest(manifest_bytes)
    bindings = evidence.parse_bindings(bindings_bytes)
    state = environment.verify(MECHANISM, candidate, refs_root, args.refs_commit)
    baseline = _inventory(state["baseline"]["inventory_utf8"].encode())
    candidate_bytes, coverage = _candidate(candidate, manifest, baseline)
    if state["pins"]["SOURCE_INVENTORY_SHA256"] != hashlib.sha256(candidate_bytes).hexdigest():
        raise ValueError("candidate inventory pin mismatch")
    _retained_pins(state["pins"])
    result = evidence.validate(manifest, bindings, refs_root)
    if result["registry_fingerprint"] != state["mechanism"]["registry_fingerprint"]:
        raise ValueError("registry changed during validation")
    receipt = {
        "version": 1,
        "verdict": "pass",
        "mechanism": state["mechanism"],
        "baseline": state["baseline"],
        "candidate": {
            "sha256": hashlib.sha256(candidate_bytes).hexdigest(),
            "inventory_utf8": candidate_bytes.decode(),
        },
        "coverage": coverage,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "semantic_review_sha256": manifest["semantic_review_sha256"],
        "resources": manifest["resources"],
        "mappings": result["mappings"],
    }
    encoded = metadata.encode(receipt)
    metadata.parse_receipt(encoded)
    if environment.verify(MECHANISM, candidate, refs_root, args.refs_commit) != state:
        raise ValueError("frozen environment or candidate changed during validation")
    if evidence.read_regular(manifest_path) != manifest_bytes or evidence.read_regular(bindings_path) != bindings_bytes:
        raise ValueError("manifest or bindings changed during validation")
    # Write privately, then publish an exclusive hard link. A failed write never
    # exposes a partial receipt, and we never unlink the requested destination.
    with tempfile.TemporaryDirectory(prefix=".beliefs-receipt-", dir=output.parent) as directory:
        temporary = Path(directory) / "receipt.json"
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--candidate")
    modes.add_argument("--check-staged")
    for name in ("manifest", "bindings", "refs-root", "refs-commit", "output", "receipt"):
        parser.add_argument("--" + name)
    args = parser.parse_args(argv)
    producing = ("manifest", "bindings", "refs_root", "refs_commit", "output")
    if args.candidate and (not all(getattr(args, key) for key in producing) or args.receipt):
        parser.error("--candidate requires manifest, bindings, refs-root, refs-commit and output only")
    if args.check_staged and (not args.receipt or any(getattr(args, key) for key in producing)):
        parser.error("--check-staged requires --receipt only")
    try:
        if args.check_staged:
            _staged(Path(args.check_staged).resolve(), Path(args.receipt))
        else:
            _admit(args)
    except (OSError, ValueError, TypeError, ScienceError) as exc:
        print(f"admission refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
