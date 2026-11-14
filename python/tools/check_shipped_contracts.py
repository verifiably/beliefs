"""Validate shipped contracts, canonical assumptions registers, and reproduction contract sources.

Checks offline and without corpus writes:
1. `contracts/science/CONTRACT.yaml` and its packaged copy match byte-for-byte and parse cleanly.
2. Every shipped pack under `domains/<namespace>/` matches its packaged copy under
   `python/src/beliefs/domains/<namespace>/` for both `DOMAIN.yaml` and `REGISTER.json`,
   parses under the current base contract and carries a canonical assumptions register whose `describes`
   digest and typed key coverage match `register_entry_keys(contract)` exactly.
3. Every YAML file under `python/tools/reproduction/` whose top-level mapping carries
   `contract` either matches one of the five SHA-256-pinned pre-v2 heritage exclusions
   unchanged or passes current parsing and pinned source ownership admission. Changed,
   missing or renamed listed heritage files fail naming their owning tasks.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import yaml
from source_admission import metadata

from beliefs.contract.base import BaseContract, parse_base_contract
from beliefs.contract.document import parse_document
from beliefs.contract.domain import DomainContract, _defining_source_id, _name, parse_domain_contract
from beliefs.contract.shipped import _strict_json_object, load_domain_history
from beliefs.errors import ScienceError
from beliefs.register import AssumptionsRegister, register_entry_keys, register_from_projection, register_identity

HERITAGE_REPRODUCTION_EXCLUSIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "python/tools/reproduction/mm30.yaml": (
            "365db8e3d852f2d41dcf30586ff802323b1904e4992afdf1586f1cfb3bd6cd62",
            "beliefs-709bd9 and beliefs-dcce70",
        ),
        "python/tools/reproduction/mm30-reproduction.yaml": (
            "33bd70148c5793df5e7b9e2f26c236ff64ed40a5b9ed88622039c195aeae29b4",
            "beliefs-709bd9 and beliefs-dcce70",
        ),
        "python/tools/reproduction/mm30-cut22.yaml": (
            "284c8bd375ce0b725208971e2174ebce185b03a4c3f52a05458d0fd685cd8569",
            "beliefs-709bd9 and beliefs-dcce70",
        ),
        "python/tools/reproduction/mm30-cut31.yaml": (
            "f077671ff7520caacd2100b9084b46d8f04d1432249fa7f5206c398fdb15432e",
            "beliefs-709bd9 and beliefs-dcce70",
        ),
        "python/tools/reproduction/mm30-modal-sorted.yaml": (
            "d59574a68d5518f9a8e90ea13202dba1843867a5fa0cf3114a344918866aa2d7",
            "beliefs-709bd9 and beliefs-dcce70",
        ),
    }
)
"""Closed `(relative_path -> (sha256_hex, owner_tasks))` exclusion map for pre-v2 heritage inputs."""

SOURCE_INVENTORY_SHA256 = "38aa7074482a2e685de39082da4b0abe4a2ae08b8c9acd86f0ca83a35de48288"

RECEIPT_SHA256: dict[str, str] = {}

ADOPTED_SOURCE_REVISIONS = MappingProxyType(
    {
        ("biology", "05e6f4fd06de8112d8f13d235c0793b6767404208cbf4210b7b9b24fc1840aca"): (
            "assumptions-register:f81b9ad496b745d850a872260f3f691020ab5ab9e3eb2b64758aeaf5dd1cfb67",
            "11308699feb1d7f402b81b6ff1451806490b41ac71df9100658d74bbad85616c",
            "bf8d07f7367b82fbbb037116111c1fdb6fcac88146ca7e4a0aab009a3b607f27",
            "urn:beliefs:definitions:human-annotation-admissions",
        ),
        ("general", "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f"): (
            "assumptions-register:02642579cb0fe2330553586e4c22d56f76a227e14b0d2fe849c6917992c3dbf9",
            "d5e7ec6c792d12d9afb08cdc58f7ce15f8512d09f525769e6ee75369841ac6a7",
            "96946aaf8ee11ede7ecddbafd27348600dce9ecac35a236342389c1807d12c24",
            "urn:beliefs:definitions:shared-scientific-commitments",
        ),
        ("general", "e74a497975e4a536f1bcbef26de73558d8a528276f4754082c6dd2d399f447ee"): (
            "assumptions-register:6939b589ff96806160232b13cba8b32019c7fc80caba0b4b06b9e7d676c98095",
            "53f9036e01080d007db4f20db9b81acecf78548512b849b81a5b340d8240b05d",
            "dbf7a185d89d202304d8944971007c8b9dd3b82ed86393946b9fbab9bae46f79",
            "urn:beliefs:definitions:shared-scientific-commitments",
        ),
        ("mm30", "5d3f0b25bc6173e9321de2f3d020ff0e110fa00b1eebf2d5c5a3b2666a734c2d"): (
            "assumptions-register:eaafc4716d8ec208903e191fcd258eb0b1a5ba796dacb44c611293c1f058ad23",
            "0ea492b8fcd7681cbd6d2ac4e874dc00be4f50657694611728d0b55931e2bcaa",
            "df474e157913a8ed0e0d12d666e1265a80d5bb16cd91d50df2fb8f32737b50cf",
            "urn:beliefs:definitions:phf19-stage-contrast-admissions",
        ),
    }
)


@dataclass(frozen=True)
class _AdmissionRevision:
    contract_path: str
    register_path: str
    contract: DomainContract
    register: AssumptionsRegister
    genesis: str
    current: bool


def _check_shadow_general(contract: DomainContract, source_rel: str) -> list[str]:
    if (
        contract.namespace == "general"
        and source_rel != "domains/general/DOMAIN.yaml"
        and re.fullmatch(r"domains/general/history/[0-9a-f]{64}/DOMAIN\.yaml", source_rel) is None
    ):
        return [f"{source_rel}: shadow contract 'general' is forbidden outside domains/general/DOMAIN.yaml"]
    return []


def _load_base(root: Path, errors: list[str]) -> BaseContract | None:
    source_path = root / "contracts/science/CONTRACT.yaml"
    pkg_path = root / "python/src/beliefs/contracts/science/CONTRACT.yaml"
    if not source_path.is_file():
        errors.append("contracts/science/CONTRACT.yaml: missing base contract")
        return None
    if not pkg_path.is_file():
        errors.append("python/src/beliefs/contracts/science/CONTRACT.yaml: missing packaged base contract")
        return None
    source_bytes = source_path.read_bytes()
    if source_bytes != pkg_path.read_bytes():
        errors.append(
            "contracts/science/CONTRACT.yaml: differs from packaged copy "
            "python/src/beliefs/contracts/science/CONTRACT.yaml"
        )
    try:
        text = source_bytes.decode("utf-8")
        return parse_base_contract(
            parse_document(text, source="contracts/science/CONTRACT.yaml"),
            source="contracts/science/CONTRACT.yaml",
        )
    except (UnicodeDecodeError, ScienceError) as exc:
        errors.append(f"contracts/science/CONTRACT.yaml: {exc}")
        return None


def _domain_inventory(directory: Path, prefix: str) -> tuple[set[str], list[str]]:
    present: set[str] = set()
    errors: list[str] = []
    for path in sorted(directory.rglob("*")):
        rel = path.relative_to(directory).as_posix()
        present.add(rel)
        valid = (
            (rel in {"DOMAIN.yaml", "REGISTER.json"} and path.is_file())
            or (rel == "history" and path.is_dir())
            or (re.fullmatch(r"history/[0-9a-f]{64}", rel) is not None and path.is_dir())
            or (
                re.fullmatch(r"history/[0-9a-f]{64}/(?:DOMAIN\.yaml|REGISTER\.json)", rel) is not None
                and path.is_file()
            )
        )
        if path.is_symlink() or not valid:
            errors.append(f"{prefix}/{rel}: unexpected or invalid shipped domain entry")
    return present, errors


def _discover_shipped_domains(root: Path, base: BaseContract) -> tuple[tuple[_AdmissionRevision, ...], list[str]]:
    errors: list[str] = []
    discovered: list[_AdmissionRevision] = []
    domains_dir = root / "domains"
    pkg_domains_dir = root / "python/src/beliefs/domains"
    if not domains_dir.is_dir():
        return (), ["domains: missing directory"]
    if not pkg_domains_dir.is_dir():
        return (), ["python/src/beliefs/domains: missing directory"]

    for container, rel_label in ((domains_dir, "domains"), (pkg_domains_dir, "python/src/beliefs/domains")):
        for entry in sorted(container.iterdir()):
            if entry.is_file() and entry.name != ".gitkeep":
                errors.append(f"{rel_label}/{entry.name}: unexpected top-level file in domains directory")

    source_namespaces = {p.name for p in domains_dir.iterdir() if p.is_dir()}
    pkg_namespaces = {p.name for p in pkg_domains_dir.iterdir() if p.is_dir()}
    for only_source in sorted(source_namespaces - pkg_namespaces):
        errors.append(f"domains/{only_source}: missing packaged directory python/src/beliefs/domains/{only_source}")
    for only_pkg in sorted(pkg_namespaces - source_namespaces):
        errors.append(f"python/src/beliefs/domains/{only_pkg}: missing canonical directory domains/{only_pkg}")

    for namespace in sorted(source_namespaces & pkg_namespaces):
        src_dir = domains_dir / namespace
        pkg_dir = pkg_domains_dir / namespace
        src_present, src_errors = _domain_inventory(src_dir, f"domains/{namespace}")
        pkg_present, pkg_errors = _domain_inventory(pkg_dir, f"python/src/beliefs/domains/{namespace}")
        errors.extend(src_errors + pkg_errors)
        if src_errors or pkg_errors:
            continue
        try:
            revisions = load_domain_history(
                namespace,
                base=base,
                read_text=lambda path, directory=src_dir: (directory / path).read_text(encoding="utf-8"),
            )
        except ScienceError as exc:
            errors.append(str(exc))
            continue
        expected = {"DOMAIN.yaml", "REGISTER.json"}
        for revision in revisions:
            prefix = f"{revision.directory}/" if revision.directory else ""
            if revision.directory:
                expected.update({"history", revision.directory, prefix + "DOMAIN.yaml", prefix + "REGISTER.json"})
            cp = f"domains/{namespace}/{prefix}DOMAIN.yaml"
            rp = f"domains/{namespace}/{prefix}REGISTER.json"
            errors.extend(_check_shadow_general(revision.contract, cp))
            discovered.append(
                _AdmissionRevision(
                    cp,
                    rp,
                    revision.contract,
                    revision.register,
                    revisions[0].contract.content_identity,
                    not revision.directory,
                )
            )
        for present, prefix in (
            (src_present, f"domains/{namespace}"),
            (pkg_present, f"python/src/beliefs/domains/{namespace}"),
        ):
            for extra in sorted(present - expected):
                errors.append(f"{prefix}/{extra}: unexpected or unreachable history entry")
            for missing in sorted(expected - present):
                errors.append(f"{prefix}/{missing}: missing required shipped domain entry")
        for relative in sorted(expected & src_present & pkg_present):
            if relative.endswith(("DOMAIN.yaml", "REGISTER.json")) and (
                (src_dir / relative).read_bytes() != (pkg_dir / relative).read_bytes()
            ):
                errors.append(f"domains/{namespace}/{relative}: differs from packaged copy")

    return tuple(discovered), errors


def _discover_reproduction_sources(
    root: Path,
    base: BaseContract,
    *,
    exclusions: Mapping[str, tuple[str, str]],
    register_paths: Mapping[str, str],
) -> tuple[tuple[_AdmissionRevision, ...], list[str]]:
    errors: list[str] = []
    discovered: list[_AdmissionRevision] = []
    for rel_path, (expected_sha256, owner) in sorted(exclusions.items()):
        path = root / rel_path
        if not path.is_file():
            errors.append(
                f"{rel_path}: listed pre-v2 heritage source is missing or renamed (owned by {owner}); "
                "restore the unchanged heritage file or update/remove its exclusion entry in the replacement change"
            )
            continue
        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha256 != expected_sha256:
            errors.append(
                f"{rel_path}: listed pre-v2 heritage source bytes changed (expected {expected_sha256}, "
                f"found {actual_sha256}; owned by {owner}); remove its exclusion entry so the replacement "
                "enters current contract validation, or restore unchanged heritage bytes"
            )

    repro_dir = root / "python/tools/reproduction"
    if not repro_dir.is_dir():
        return (), errors

    yaml_paths = sorted({*repro_dir.rglob("*.yaml"), *repro_dir.rglob("*.yml")})
    for path in yaml_paths:
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if rel_path in exclusions:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            probed = yaml.safe_load(text)
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            errors.append(f"{rel_path}: invalid YAML: {exc}")
            continue
        if not (isinstance(probed, dict) and "contract" in probed):
            continue
        try:
            contract = parse_domain_contract(
                parse_document(text, source=rel_path),
                source=rel_path,
                base=base,
                predecessor=None,
            )
        except ScienceError as exc:
            errors.append(str(exc))
            continue
        errors.extend(_check_shadow_general(contract, rel_path))
        register_path = register_paths.get(rel_path)
        if register_path is None:
            errors.append(f"{rel_path}: unlisted reproduction contract; missing inventory register mapping")
            continue
        try:
            register = register_from_projection(_read_json(_admission_path(root, register_path)), source=register_path)
            if register.describes != f"{contract.namespace}:{contract.content_identity}":
                raise ValueError("stale register describes")
            if set(register.entries) != register_entry_keys(contract):
                raise ValueError("register entry coverage mismatch")
            if register.previous is not None:
                raise ValueError("genesis register must have no previous")
            discovered.append(
                _AdmissionRevision(rel_path, register_path, contract, register, contract.content_identity, True)
            )
        except (OSError, ValueError, ScienceError) as exc:
            errors.append(f"{register_path}: {exc}")

    return tuple(discovered), errors


def _read_json(path: Path) -> Any:
    def refuse_constant(value: str) -> None:
        raise ValueError(f"non-JSON constant {value}")

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_strict_json_object, parse_constant=refuse_constant
    )


def _reject_symlinks(root: Path) -> None:
    for relative in (
        "contracts",
        "domains",
        "python/src/beliefs/contracts",
        "python/src/beliefs/domains",
        "python/tools/reproduction",
    ):
        directory = root / relative
        for parent in (directory, *directory.parents):
            if parent == root:
                break
            if parent.is_symlink():
                raise ValueError(f"{parent.relative_to(root)}: symlink admission path refused")

        def failed(error: OSError) -> None:
            raise error

        for current, dirs, files in os.walk(directory, followlinks=False, onerror=failed):
            for name in dirs + files:
                path = Path(current) / name
                if path.is_symlink():
                    raise ValueError(f"{path.relative_to(root)}: symlink admission member refused")


_fields = metadata.fields
_hex = metadata.hex_digest
_canonical_path = metadata.canonical_path


def _admission_path(root: Path, relative: str) -> Path:
    """Validate inventory-selected paths too, including those outside scanned trees."""
    _canonical_path(relative)
    candidate = root
    for component in relative.split("/"):
        candidate = candidate / component
        if candidate.is_symlink():
            raise ValueError(f"{relative}: symlink admission path refused at {candidate.relative_to(root)}")
    if not candidate.resolve().is_relative_to(root):
        raise ValueError(f"{relative}: admission path escapes repository root")
    return candidate


def _validate_inventory(value: Any) -> dict[str, Any]:
    _fields(value, {"version", "sources", "lineages"}, "inventory")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("inventory version: expected integer 1")
    sources, lineages = value["sources"], value["lineages"]
    if not isinstance(sources, dict) or not isinstance(lineages, dict):
        raise TypeError("inventory sources/lineages: expected mappings")
    reserved: dict[str, str] = {}
    for sid, source in sources.items():
        _defining_source_id(sid, "inventory source id")
        _fields(source, {"aliases", "owner"}, sid)
        _fields(source["owner"], {"namespace", "genesis"}, f"{sid} owner")
        _name(source["owner"]["namespace"], f"{sid} owner namespace")
        _hex(source["owner"]["genesis"], f"{sid} owner genesis")
        aliases = source["aliases"]
        if not isinstance(aliases, list):
            raise TypeError(f"{sid}: aliases must be a list")
        for name in [sid, *aliases]:
            _defining_source_id(name, f"{sid} alias")
            if name in reserved:
                raise ValueError(f"{sid}: duplicate source/alias {name}, reserved by {reserved[name]}")
            reserved[name] = sid
    document_owners: dict[str, str] = {}
    paths: set[str] = set()
    identities: set[tuple[str, str]] = set()
    for namespace, lineage in lineages.items():
        _name(namespace, "inventory namespace")
        _fields(lineage, {"genesis", "source_id", "revisions"}, namespace)
        _hex(lineage["genesis"], f"{namespace} genesis")
        _defining_source_id(lineage["source_id"], f"{namespace} source_id")
        if not isinstance(lineage["revisions"], list) or not lineage["revisions"]:
            raise ValueError(f"{namespace}: revisions must be nonempty list")
        for row in lineage["revisions"]:
            _fields(
                row,
                {
                    "contract_path",
                    "register_path",
                    "contract_identity",
                    "register_identity",
                    "contract_sha256",
                    "register_sha256",
                    "source_pin",
                },
                namespace,
            )
            pin = row["source_pin"]
            if isinstance(pin, dict) and pin.get("kind") == "external":
                _fields(pin, {"kind", "documents"}, f"{namespace} external source_pin")
                metadata.validate_documents(pin["documents"])
                for document in pin["documents"]:
                    sid = lineage["source_id"]
                    previous = document_owners.setdefault(document["sha256"], sid)
                    if previous != sid:
                        raise ValueError(f"external normative digest shared by distinct sources: {previous}, {sid}")
            else:
                _fields(pin, {"kind"}, f"{namespace} source_pin")
                if pin["kind"] != "authored_pair":
                    raise ValueError(f"{namespace}: expected authored_pair or external source pin")
            for key in ("contract_identity", "contract_sha256", "register_sha256"):
                _hex(row[key], f"{namespace} {key}")
            _hex(row["register_identity"], f"{namespace} register_identity", "assumptions-register:")
            identity = (namespace, row["contract_identity"])
            if identity in identities:
                raise ValueError(f"{namespace}: duplicate revision identity")
            identities.add(identity)
            for key in ("contract_path", "register_path"):
                _canonical_path(row[key])
                if row[key] in paths:
                    raise ValueError(f"{namespace}: duplicate revision path {row[key]}")
                paths.add(row[key])
    return value


def _check_source_ownership(
    root: Path, inventory: Mapping[str, object], revisions: tuple[_AdmissionRevision, ...]
) -> list[str]:
    inv = cast(dict[str, Any], inventory)
    sources, lineages = inv["sources"], inv["lineages"]
    errors: list[str] = []
    by_path = {r.contract_path: r for r in revisions}
    listed = {row["contract_path"] for lineage in lineages.values() for row in lineage["revisions"]}
    for path in sorted(listed - by_path.keys()):
        errors.append(f"{path}: inventory revision not discovered")
    for path in sorted(by_path.keys() - listed):
        errors.append(f"{path}: discovered revision missing inventory row")
    for sid, source in sources.items():
        owner = source["owner"]
        lineage = lineages.get(owner["namespace"])
        if lineage is None or lineage["source_id"] != sid or lineage["genesis"] != owner["genesis"]:
            errors.append(
                f"{sid}: reserved owner {owner} disagrees with lineage at domains/{owner['namespace']}/DOMAIN.yaml"
            )
    for namespace, lineage in lineages.items():
        sid = lineage["source_id"]
        source = sources.get(sid)
        if source is None:
            errors.append(f"{namespace}: unknown canonical source {sid}")
            continue
        expected_owner = {"namespace": namespace, "genesis": lineage["genesis"]}
        if source["owner"] != expected_owner:
            errors.append(
                f"{sid}: claimant owner {expected_owner} at {lineage['revisions'][0]['contract_path']} conflicts with reserved owner {source['owner']}"
            )
        observed = [r for r in revisions if r.contract.namespace == namespace]
        if sum(r.current for r in observed) != 1:
            errors.append(f"{namespace}: expected exactly one current revision")
        if [r.contract.content_identity for r in observed] != [
            row["contract_identity"] for row in lineage["revisions"]
        ]:
            errors.append(f"{namespace}: revision order/coverage must match checked chain oldest-first")
        for row in lineage["revisions"]:
            cp = row["contract_path"]
            revision = by_path.get(cp)
            if revision is None:
                continue
            contract, register = revision.contract, revision.register
            if contract.namespace != namespace or revision.genesis != lineage["genesis"]:
                errors.append(f"{cp}: {sid} owner/genesis mismatch, expected {expected_owner}")
            if row["register_path"] != revision.register_path:
                errors.append(f"{cp}: register path is not discovered canonical pair")
            actual = (
                register_identity(register),
                hashlib.sha256((root / cp).read_bytes()).hexdigest(),
                hashlib.sha256((root / revision.register_path).read_bytes()).hexdigest(),
                sid,
            )
            if (row["register_identity"], row["contract_sha256"], row["register_sha256"], sid) != actual or row[
                "contract_identity"
            ] != contract.content_identity:
                errors.append(f"{cp}: authored pair identity/hash mismatch")
            if contract.defining_source is None:
                if ADOPTED_SOURCE_REVISIONS.get((namespace, contract.content_identity)) != actual:
                    errors.append(f"{cp}: missing defining_source outside exact adopted source revisions")
            elif contract.defining_source.id != sid:
                claimed = contract.defining_source.id
                canonical = next(
                    (key for key, info in sources.items() if claimed == key or claimed in info["aliases"]), None
                )
                errors.append(
                    f"{cp}: source {claimed} must use canonical {canonical or sid}; reserved owner {sources.get(canonical or sid, {}).get('owner')}, inventory owner {expected_owner}"
                )
    seen = {(r.contract.namespace, r.contract.content_identity) for r in revisions}
    for key in ADOPTED_SOURCE_REVISIONS:
        if key not in seen:
            errors.append(f"{key}: required adopted revision missing; fresh genesis cannot replace reserved owner")
    return errors


def _inspect(
    root: Path, inventory: dict, exclusions: Mapping[str, tuple[str, str]]
) -> tuple[list[str], tuple[_AdmissionRevision, ...]]:
    _reject_symlinks(root)
    for lineage in inventory["lineages"].values():
        for row in lineage["revisions"]:
            _admission_path(root, row["contract_path"])
            _admission_path(root, row["register_path"])
    errors: list[str] = []
    base = _load_base(root, errors)
    if base is None:
        return errors, ()
    shipped, shipped_errors = _discover_shipped_domains(root, base)
    register_paths = {
        r["contract_path"]: r["register_path"]
        for lineage in inventory["lineages"].values()
        for r in lineage["revisions"]
    }
    repro, repro_errors = _discover_reproduction_sources(
        root, base, exclusions=exclusions, register_paths=register_paths
    )
    revisions = shipped + repro
    return errors + shipped_errors + repro_errors + _check_source_ownership(root, inventory, revisions), revisions


def inspect_candidate(root: Path, inventory_bytes: bytes) -> list[str]:
    """Inspect structure only; never grants standing admission or executes candidate code."""
    try:
        inventory = _validate_inventory(metadata.decode(inventory_bytes))
        return _inspect(Path(root).resolve(), inventory, HERITAGE_REPRODUCTION_EXCLUSIONS)[0]
    except (OSError, UnicodeDecodeError, ValueError, TypeError, ScienceError) as exc:
        return [f"source admission: {exc}"]


def _check_receipts(root: Path, inventory: dict, revisions: tuple[_AdmissionRevision, ...]) -> None:
    directory = root / "contracts/source-ownership/receipts"
    actual = {p.relative_to(root).as_posix() for p in directory.rglob("*")} if directory.exists() else set()
    if actual != set(RECEIPT_SHA256):
        raise ValueError("receipt directory differs from pinned receipt inventory")
    covered: dict[tuple[str, str], dict] = {}
    contracts = {(r.contract.namespace, r.contract.content_identity): r.contract for r in revisions}
    for relative, expected in RECEIPT_SHA256.items():
        _hex(expected, "receipt pin")
        if relative != f"contracts/source-ownership/receipts/{expected}.json":
            raise ValueError("receipt path must use its exact digest filename")
        data = _admission_path(root, relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("receipt SHA-256 pin mismatch")
        receipt = metadata.parse_receipt(data)
        snapshots = {
            key: _validate_inventory(metadata.decode(receipt[key]["inventory_utf8"].encode()))
            for key in ("baseline", "candidate")
        }
        metadata.check_continuity(snapshots["baseline"], snapshots["candidate"])
        coverage = receipt["coverage"]
        sid, ns, row = coverage["source_id"], coverage["namespace"], coverage["row"]
        historical = snapshots["candidate"]
        if (
            historical["sources"].get(sid, {}).get("owner") != coverage["owner"]
            or historical["lineages"].get(ns, {}).get("source_id") != sid
            or row not in historical["lineages"].get(ns, {}).get("revisions", [])
        ):
            raise ValueError("receipt coverage absent from historical inventory")
        metadata.check_continuity(historical, inventory)
        identity = (ns, row["contract_identity"])
        previous = covered.setdefault(identity, receipt)
        if previous != receipt:
            raise ValueError("disagreeing receipts for one covered identity")
        contract = contracts.get(identity)
        if contract is None:
            raise ValueError("receipt covered contract missing from current history")
        fields = {
            key: {
                "ucum": result["ucum"]["code"],
                **({"qudt": result["qudt"]["iri"]} if result["qudt"] else {}),
            }
            for key, result in receipt["mappings"].items()
        }
        actual_mappings = {f"{ns}/{name}": dict(unit.external or {}) for name, unit in contract.units.items()}
        if fields != actual_mappings:
            raise ValueError("receipt mappings disagree with parsed unit fields")
    for ns, lineage in inventory["lineages"].items():
        for row in lineage["revisions"]:
            if row["source_pin"]["kind"] != "external":
                continue
            receipt = covered.get((ns, row["contract_identity"]))
            if receipt is None:
                raise ValueError(f"{ns}: external revision missing receipt")
            c = receipt["coverage"]
            sid = lineage["source_id"]
            if metadata.coverage_projection(
                sid, inventory["sources"][sid]["owner"], row
            ) != metadata.coverage_projection(c["source_id"], c["owner"], c["row"]):
                raise ValueError("external receipt coverage projection mismatch")


def check(root: Path, *, exclusions: Mapping[str, tuple[str, str]] = HERITAGE_REPRODUCTION_EXCLUSIONS) -> list[str]:
    root = Path(root).resolve()
    try:
        _reject_symlinks(root)
        data = (root / "contracts/source-ownership/INVENTORY.json").read_bytes()
        if hashlib.sha256(data).hexdigest() != SOURCE_INVENTORY_SHA256:
            raise ValueError("source inventory SHA-256 pin mismatch")
        inventory = _validate_inventory(metadata.decode(data))
        errors, revisions = _inspect(root, inventory, exclusions)
        if not errors:
            _check_receipts(root, inventory, revisions)
        return errors
    except (OSError, UnicodeDecodeError, ValueError, TypeError, ScienceError) as exc:
        return [f"source admission: {exc}"]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]).resolve() if args else REPO_ROOT
    errors = check(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
