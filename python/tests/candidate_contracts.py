"""Unshipped contracts composed against the current tree, never admission roots."""

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import yaml
from time_roles_fixture import time_document

from beliefs.contract.base import BaseContract
from beliefs.contract.document import load_document
from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.contract.shipped import ShippedDomainRevision, load_domain_history
from beliefs.profile import ProfileSpec, shipped_assumptions_register, shipped_domain_contract
from beliefs.register import AssumptionsRegister, register_from_projection, register_identity, register_projection

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "fixtures/contracts/candidates"
STATIC = ("plasma-populations", "catalogue-anchors")
CASE_CANDIDATES = ("mondo", "case-comparisons")
GENERAL_SOURCE_ID = "urn:beliefs:definitions:shared-scientific-commitments"


def oracle() -> dict[str, Any]:
    return json.loads((ROOT / "fixtures/candidate-contracts.json").read_text())


def candidate_history(namespace: str, base: BaseContract) -> ShippedDomainRevision:
    (revision,) = load_domain_history(
        namespace, base=base, read_text=lambda path: (CANDIDATES / namespace / path).read_text()
    )
    return revision


def fragment(name: str) -> dict[str, Any]:
    path = CANDIDATES / "fragments" / f"{name}.yaml"
    return cast(dict[str, Any], load_document(path, source=str(path)))


def with_rows(
    document: dict[str, Any],
    predecessor: DomainContract,
    rows: Mapping[str, Mapping[str, object]],
    **top_level: object,
) -> dict[str, Any]:
    result = deepcopy(document)
    for table, added in rows.items():
        destination = result.setdefault(table, {})
        for name, value in added.items():
            if name in destination:
                raise ValueError(f"{predecessor.namespace} already declares {table}.{name}; retire the fragment row")
            destination[name] = deepcopy(value)
    result.update(version=predecessor.version + 1, lineage={"successor": predecessor.content_identity})
    result.update(top_level)
    return result


def general_successor_document(
    base: BaseContract, *, fragments=("general-event-locked",)
) -> tuple[dict[str, Any], DomainContract]:
    predecessor = shipped_domain_contract("general")
    path = ROOT / "domains/general/DOMAIN.yaml"
    document = cast(dict[str, Any], load_document(path, source=str(path)))
    for name in fragments:
        document = with_rows(document, predecessor, fragment(name)["rows"], defining_source={"id": GENERAL_SOURCE_ID})
    return document, predecessor


def general_successor_history(
    base: BaseContract, *, fragments=("general-event-locked",)
) -> tuple[ShippedDomainRevision, ...]:
    document, predecessor = general_successor_document(base, fragments=fragments)
    contract = parse_domain_contract(document, source="<candidate general>", base=base, predecessor=predecessor)
    previous = shipped_assumptions_register("general")
    entries = register_from_projection(
        {
            "describes": f"general:{contract.content_identity}",
            "entries": {key: value for name in fragments for key, value in fragment(name)["register_entries"].items()},
        },
        source="<candidate general register>",
    ).entries
    register = AssumptionsRegister(
        f"general:{contract.content_identity}", register_identity(previous), {**previous.entries, **entries}
    )

    def read(path: str) -> str:
        if path == "DOMAIN.yaml":
            return yaml.safe_dump(document)
        if path == "REGISTER.json":
            return json.dumps(register_projection(register))
        prefix = f"history/{predecessor.content_identity}/"
        if path.startswith(prefix):
            path = path.removeprefix(prefix)
        return (ROOT / "domains/general" / path).read_text()

    return load_domain_history("general", base=base, read_text=read)


def time_successor_document(
    base: BaseContract, genesis_document: dict[str, Any] | None = None
) -> tuple[dict[str, Any], DomainContract]:
    document = time_document() if genesis_document is None else genesis_document
    predecessor = parse_domain_contract(document, source="<time genesis>", base=base, predecessor=None)
    return with_rows(document, predecessor, fragment("si-brochure-speed")["rows"]), predecessor


def time_successor(
    base: BaseContract, genesis_document: dict[str, Any] | None = None
) -> tuple[DomainContract, DomainContract]:
    document, predecessor = time_successor_document(base, genesis_document)
    return predecessor, parse_domain_contract(document, source="<candidate speed>", base=base, predecessor=predecessor)


def candidate_profile(base, *, omit=(), extra=()):
    from beliefs.profile import compile_profile

    general = (
        shipped_domain_contract("general")
        if "general-successor" in omit
        else general_successor_history(base)[-1].contract
    )
    domains = [general]
    if "si-brochure" not in omit:
        genesis, successor = time_successor(base)
        domains.append(genesis if "speed" in omit else successor)
    domains.extend(candidate_history(name, base).contract for name in STATIC if name not in omit)
    return compile_profile(base, [*domains, *extra])


def spectral_profile(
    base: BaseContract, *, joint: bool = False, omit: tuple[str, ...] = (), extra: tuple[DomainContract, ...] = ()
) -> ProfileSpec:
    from beliefs.profile import compile_profile

    names = ("general-event-locked", "general-spectral") if joint else ("general-spectral",)
    active = tuple(name for name in names if name not in omit)
    general = (
        general_successor_history(base, fragments=active)[-1].contract if active else shipped_domain_contract("general")
    )
    domains = [general]
    if "si-brochure" not in omit:
        domains.append(
            time_successor(base)[0 if "speed" in omit else 1] if joint else shipped_domain_contract("si-brochure")
        )
    for name in (*STATIC, "spectral-example") if joint else ("spectral-example",):
        if name not in omit:
            domains.append(candidate_history(name, base).contract)
    return compile_profile(base, [*domains, *extra])


def candidate_document(namespace: str) -> dict[str, Any]:
    path = CANDIDATES / namespace / "DOMAIN.yaml"
    return cast(dict[str, Any], load_document(path, source=str(path)))


def case_profile(
    base: BaseContract, *, omit: tuple[str, ...] = (), replace: Mapping[str, DomainContract] | None = None
) -> ProfileSpec:
    from beliefs.profile import compile_profile

    replacements = {} if replace is None else replace
    shipped = ("general", "biology", "si-brochure")
    domains = [
        replacements[name] if name in replacements else shipped_domain_contract(name)
        for name in shipped
        if name not in omit
    ]
    domains.extend(
        replacements[name] if name in replacements else candidate_history(name, base).contract
        for name in CASE_CANDIDATES
        if name not in omit
    )
    return compile_profile(base, domains)
