"""Temporary shipped histories; these fixtures never change installed resources."""

import json

import yaml

from beliefs.contract.domain import parse_domain_contract
from beliefs.profile import shipped_base_contract
from beliefs.register import (
    AssumptionsRegister,
    RegisterEntry,
    register_entry_keys,
    register_identity,
    register_projection,
)


def history_resources(count=3, namespace="general"):
    documents, contracts, registers = [], [], []
    designs = {}
    for version in range(1, count + 1):
        designs[f"stage-{version}"] = {}
        document = {
            "contract": namespace,
            "version": version,
            "lineage": "genesis" if not contracts else {"successor": contracts[-1].content_identity},
            "sorts": {},
            "dimensions": {},
            "designs": dict(designs),
        }
        contract = parse_domain_contract(
            document, source="fixture", base=shipped_base_contract(), predecessor=contracts[-1] if contracts else None
        )
        register = AssumptionsRegister(
            describes=f"{namespace}:{contract.content_identity}",
            previous=register_identity(registers[-1]) if registers else None,
            entries={key: RegisterEntry("c", "l", "n", status="provisional") for key in register_entry_keys(contract)},
        )
        documents.append(document)
        contracts.append(contract)
        registers.append(register)
    resources = {}
    for index, (document, contract, register) in enumerate(zip(documents, contracts, registers, strict=True)):
        prefix = "" if index == count - 1 else f"history/{contract.content_identity}/"
        resources[prefix + "DOMAIN.yaml"] = yaml.safe_dump(document)
        resources[prefix + "REGISTER.json"] = json.dumps(register_projection(register))
    return resources, contracts, registers


def read_resource(resources, path):
    try:
        return resources[path]
    except KeyError:
        raise FileNotFoundError(path) from None
