"""Validate shipped contracts, canonical assumptions registers, and reproduction contract sources.

Checks offline and without corpus writes:
1. `contracts/science/CONTRACT.yaml` and its packaged copy match byte-for-byte and parse cleanly.
2. Every shipped pack under `domains/<namespace>/` matches its packaged copy under
   `python/src/beliefs/domains/<namespace>/` for both `DOMAIN.yaml` and `REGISTER.json`,
   parses under the current base contract, satisfies the one-registry shared-table
   placement rule, and carries a canonical assumptions register whose `describes`
   digest and typed key coverage match `register_entry_keys(contract)` exactly.
3. Every YAML file under `python/tools/reproduction/` whose top-level mapping carries
   `contract` either matches one of the five SHA-256-pinned pre-v2 heritage exclusions
   unchanged or passes current contract parsing and shared-table placement. Changed,
   missing or renamed listed heritage files fail naming their owning tasks.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import yaml

from beliefs.contract.base import BaseContract, parse_base_contract
from beliefs.contract.document import parse_document
from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.errors import ScienceError
from beliefs.register import register_entry_keys, register_from_projection

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

REVIEWED_FIELD_SPECIFIC_EXCEPTIONS: Mapping[tuple[str, str, str], str] = MappingProxyType({})
"""Reviewed `(source_rel_path, kind, local_name) -> reason` exceptions for field-specific
`functional` or `procedure-kind` declarations outside `general`. Empty in genesis."""

_SHARED_ONLY_TABLES: tuple[tuple[str, str], ...] = (
    ("quantity-kind", "quantity_kinds"),
    ("unit", "units"),
    ("constant", "constants"),
    ("conversion", "conversions"),
    ("transformation", "transformations"),
    ("duration-convention", "duration_conventions"),
    ("identification-class", "identification_classes"),
    ("design", "designs"),
    ("selection-mechanism", "selection_mechanisms"),
    ("aggregation-rule", "aggregation_rules"),
    ("assumption-kind", "assumption_kinds"),
)

_EXCEPTION_ELIGIBLE_TABLES: tuple[tuple[str, str], ...] = (
    ("functional", "functionals"),
    ("procedure-kind", "procedure_kinds"),
)


def _check_exception_inventory(
    placement_exceptions: Mapping[tuple[str, str, str], str],
) -> list[str]:
    errors: list[str] = []
    allowed_kinds = {kind for kind, _ in _EXCEPTION_ELIGIBLE_TABLES}
    for key, reason in sorted(placement_exceptions.items()):
        if len(key) != 3 or not all(isinstance(part, str) and part.strip() for part in key):
            errors.append(f"placement_exceptions: invalid key {key!r}; expected (source_path, kind, name)")
            continue
        source_rel, kind, name = key
        if "*" in source_rel or "*" in kind or "*" in name:
            errors.append(f"placement_exceptions: wildcards are refused in {key!r}")
        if kind not in allowed_kinds:
            errors.append(
                f"placement_exceptions: {source_rel} {kind}:{name} cannot be exempted; only "
                f"{sorted(allowed_kinds)} admit reviewed field-specific exceptions"
            )
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"placement_exceptions: {source_rel} {kind}:{name} requires a non-empty reviewed reason")
    return errors


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _check_placement(
    contract: DomainContract,
    *,
    source_rel: str,
    placement_exceptions: Mapping[tuple[str, str, str], str],
) -> list[str]:
    if contract.namespace == "general":
        if source_rel != "domains/general/DOMAIN.yaml":
            return [f"{source_rel}: shadow contract 'general' is forbidden outside domains/general/DOMAIN.yaml"]
        return []
    errors: list[str] = []
    for kind, attr in _SHARED_ONLY_TABLES:
        for name in sorted(getattr(contract, attr)):
            errors.append(
                f"{source_rel}: non-general contract {contract.namespace!r} declares shared {kind} {name!r}; "
                "shared numerical and methodological vocabulary belongs in `general`"
            )
    for kind, attr in _EXCEPTION_ELIGIBLE_TABLES:
        for name in sorted(getattr(contract, attr)):
            reason = placement_exceptions.get((source_rel, kind, name))
            if reason is None or not reason.strip():
                errors.append(
                    f"{source_rel}: non-general contract {contract.namespace!r} declares {kind} {name!r} "
                    "without a reviewed field-specific classification in REVIEWED_FIELD_SPECIFIC_EXCEPTIONS"
                )
    return errors


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


def _check_shipped_domains(
    root: Path,
    base: BaseContract,
    *,
    placement_exceptions: Mapping[tuple[str, str, str], str],
) -> list[str]:
    errors: list[str] = []
    domains_dir = root / "domains"
    pkg_domains_dir = root / "python/src/beliefs/domains"
    if not domains_dir.is_dir():
        return ["domains: missing directory"]
    if not pkg_domains_dir.is_dir():
        return ["python/src/beliefs/domains: missing directory"]

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
        expected_files = {"DOMAIN.yaml", "REGISTER.json"}
        for check_dir, prefix in (
            (src_dir, f"domains/{namespace}"),
            (pkg_dir, f"python/src/beliefs/domains/{namespace}"),
        ):
            present = {p.name for p in check_dir.iterdir()}
            for extra in sorted(present - expected_files):
                errors.append(f"{prefix}/{extra}: unexpected file in shipped domain directory")
            for missing in sorted(expected_files - present):
                errors.append(f"{prefix}/{missing}: missing required shipped domain file")

        src_domain = src_dir / "DOMAIN.yaml"
        pkg_domain = pkg_dir / "DOMAIN.yaml"
        src_reg = src_dir / "REGISTER.json"
        pkg_reg = pkg_dir / "REGISTER.json"
        if not (src_domain.is_file() and pkg_domain.is_file() and src_reg.is_file() and pkg_reg.is_file()):
            continue

        domain_bytes = src_domain.read_bytes()
        if domain_bytes != pkg_domain.read_bytes():
            errors.append(
                f"domains/{namespace}/DOMAIN.yaml: differs from packaged copy "
                f"python/src/beliefs/domains/{namespace}/DOMAIN.yaml"
            )
        reg_bytes = src_reg.read_bytes()
        if reg_bytes != pkg_reg.read_bytes():
            errors.append(
                f"domains/{namespace}/REGISTER.json: differs from packaged copy "
                f"python/src/beliefs/domains/{namespace}/REGISTER.json"
            )

        domain_rel = f"domains/{namespace}/DOMAIN.yaml"
        try:
            contract = parse_domain_contract(
                parse_document(domain_bytes.decode("utf-8"), source=domain_rel),
                source=domain_rel,
                base=base,
                predecessor=None,
            )
        except (UnicodeDecodeError, ScienceError) as exc:
            errors.append(f"{domain_rel}: {exc}")
            continue

        if contract.namespace != namespace:
            errors.append(f"{domain_rel}: declares contract {contract.namespace!r}, expected directory {namespace!r}")
        errors.extend(_check_placement(contract, source_rel=domain_rel, placement_exceptions=placement_exceptions))

        reg_rel = f"domains/{namespace}/REGISTER.json"
        try:
            raw_reg = json.loads(reg_bytes.decode("utf-8"), object_pairs_hook=_strict_json_object)
            register = register_from_projection(raw_reg, source=reg_rel)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, ScienceError) as exc:
            errors.append(f"{reg_rel}: {exc}")
            continue

        expected_describes = f"{namespace}:{contract.content_identity}"
        if register.describes != expected_describes:
            errors.append(f"{reg_rel}: describes {register.describes!r}, expected {expected_describes!r}")
        expected_keys = register_entry_keys(contract)
        actual_keys = frozenset(register.entries)
        if actual_keys != expected_keys:
            missing_keys = sorted(expected_keys - actual_keys)
            extra_keys = sorted(actual_keys - expected_keys)
            errors.append(
                f"{reg_rel}: entry coverage mismatch against {domain_rel} (missing={missing_keys}, extra={extra_keys})"
            )

    return errors


def _check_reproduction_sources(
    root: Path,
    base: BaseContract,
    *,
    exclusions: Mapping[str, tuple[str, str]],
    placement_exceptions: Mapping[tuple[str, str, str], str],
) -> list[str]:
    errors: list[str] = []
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
        return errors

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
        errors.extend(_check_placement(contract, source_rel=rel_path, placement_exceptions=placement_exceptions))

    return errors


def check(
    root: Path,
    *,
    exclusions: Mapping[str, tuple[str, str]] = HERITAGE_REPRODUCTION_EXCLUSIONS,
    placement_exceptions: Mapping[tuple[str, str, str], str] = REVIEWED_FIELD_SPECIFIC_EXCEPTIONS,
) -> list[str]:
    resolved_root = Path(root).resolve()
    errors = _check_exception_inventory(placement_exceptions)
    base = _load_base(resolved_root, errors)
    if base is None:
        return errors
    errors.extend(_check_shipped_domains(resolved_root, base, placement_exceptions=placement_exceptions))
    errors.extend(
        _check_reproduction_sources(
            resolved_root,
            base,
            exclusions=exclusions,
            placement_exceptions=placement_exceptions,
        )
    )
    return errors


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
