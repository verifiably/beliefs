"""Disposable PHF19 successions with independently computed pair identities."""

import json
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.profile import shipped_base_contract
from beliefs.register import (
    AssumptionsRegister,
    RegisterEntry,
    register_from_projection,
    register_identity,
    register_projection,
)

__all__ = ["Pair", "phf19_history"]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTRACT = "mm30-phf19.yaml"
_REGISTER = "mm30-phf19-register.json"


@dataclass(frozen=True)
class Pair:
    contract_path: Path
    register_path: Path
    contract: DomainContract
    register: AssumptionsRegister


def phf19_history(
    directory: Path,
    *,
    source_root: Path = _REPO_ROOT,
    successors: int = 1,
    template_layer: str | None = None,
) -> tuple[Pair, ...]:
    directory.mkdir(parents=True, exist_ok=True)
    head = directory / _CONTRACT
    register_path = directory / _REGISTER
    inventory = json.loads((source_root / "contracts/source-ownership/INVENTORY.json").read_bytes())
    genesis = inventory["lineages"]["mm30"]["revisions"][0]
    head.write_bytes((source_root / genesis["contract_path"]).read_bytes())
    register_path.write_bytes((source_root / genesis["register_path"]).read_bytes())
    base = shipped_base_contract()
    document = yaml.safe_load(head.read_bytes())
    contract = parse_domain_contract(document, source=head.as_posix(), base=base, predecessor=None)
    register = register_from_projection(json.loads(register_path.read_bytes()), source=register_path.as_posix())
    pairs = []
    for _ in range(successors):
        archive = directory / "mm30-phf19-history" / contract.content_identity
        archive.mkdir(parents=True)
        archived_contract = head.rename(archive / "DOMAIN.yaml")
        archived_register = register_path.rename(archive / "REGISTER.json")
        pairs.append(Pair(archived_contract, archived_register, contract, register))

        document["version"] += 1
        document["lineage"] = {"successor": contract.content_identity}
        document["defining_source"] = {"id": "urn:beliefs:definitions:phf19-stage-contrast-admissions"}
        entries = dict(register.entries)
        if template_layer is not None:
            document["templates"] = {
                "fixture-template": {
                    "roles": {"subject": {"arity": "one"}},
                    "sign_apt": False,
                    "layers": [template_layer],
                    "forms": ["polar"],
                }
            }
            entries["template:mm30/fixture-template"] = RegisterEntry(
                "fixture only", "fixture only", "fixture only", status="provisional"
            )
        contract = parse_domain_contract(document, source=head.as_posix(), base=base, predecessor=contract)
        register = replace(
            register,
            describes=f"mm30:{contract.content_identity}",
            previous=register_identity(register),
            entries=entries,
        )
        head.write_text(yaml.safe_dump(document), encoding="utf-8")
        register_path.write_text(json.dumps(register_projection(register)), encoding="utf-8")
    return (*pairs, Pair(head, register_path, contract, register))
