"""Checked, content-addressed domain/register histories shared by package and tooling."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass

from beliefs.contract.base import BaseContract
from beliefs.contract.document import parse_document
from beliefs.contract.domain import DomainContract, _name, _parse_lineage, parse_domain_contract
from beliefs.errors import MalformedContract, ProfileError, ScienceError
from beliefs.register import (
    AssumptionsRegister,
    register_entry_keys,
    register_from_projection,
    register_identity,
)


@dataclass(frozen=True)
class ShippedDomainRevision:
    directory: str
    contract: DomainContract
    register: AssumptionsRegister


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_domain_history(
    namespace: str, *, base: BaseContract, read_text: Callable[[str], str]
) -> tuple[ShippedDomainRevision, ...]:
    """Read only declared ancestors; return oldest first after checking every pair.

    Paths passed to the reader are relative to this namespace. Inventory and byte
    equality between source and packaged resources belong to the source checker.
    """
    try:
        _name(namespace, "shipped domain namespace")
    except MalformedContract as exc:
        raise ProfileError(str(exc)) from exc
    pending: list[tuple[str, dict[str, object]]] = []
    visited: set[str] = set()
    directory = ""
    while True:
        path = f"{directory}/DOMAIN.yaml" if directory else "DOMAIN.yaml"
        source = f"domains/{namespace}/{path}"
        try:
            document = parse_document(read_text(path), source=source)
            if not isinstance(document, dict):
                raise MalformedContract("a domain document is a mapping")
            predecessor = _parse_lineage(document.get("lineage"), f"{source}: lineage")
            pending.append((directory, document))
            if predecessor is None:
                break
            if re.fullmatch(r"[0-9a-f]{64}", predecessor) is None:
                raise MalformedContract("lineage requires a 64-lowercase-hex content identity")
            if predecessor in visited:
                raise MalformedContract(f"lineage cycle at {predecessor}")
            visited.add(predecessor)
            directory = f"history/{predecessor}"
        except (OSError, UnicodeDecodeError, ScienceError) as exc:
            raise ProfileError(f"{source}: {exc}") from exc

    checked: list[ShippedDomainRevision] = []
    for directory, document in reversed(pending):
        prefix = f"{directory}/" if directory else ""
        source = f"domains/{namespace}/{prefix}DOMAIN.yaml"
        try:
            contract = parse_domain_contract(
                document, source=source, base=base, predecessor=checked[-1].contract if checked else None
            )
            if contract.namespace != namespace:
                raise MalformedContract(f"declares namespace {contract.namespace!r}, expected {namespace!r}")
            if directory and contract.content_identity != directory.removeprefix("history/"):
                raise MalformedContract("content identity differs from its history directory")
        except ScienceError as exc:
            raise ProfileError(f"{source}: {exc}") from exc
        path = f"{prefix}REGISTER.json"
        source = f"domains/{namespace}/{path}"
        try:
            payload = json.loads(read_text(path), object_pairs_hook=_strict_json_object)
            register = register_from_projection(payload, source=source)
            expected_describes = f"{namespace}:{contract.content_identity}"
            if register.describes != expected_describes:
                raise ProfileError(f"describes {register.describes!r}, expected {expected_describes!r}")
            expected_keys = register_entry_keys(contract)
            actual_keys = frozenset(register.entries)
            if actual_keys != expected_keys:
                raise ProfileError(
                    f"entry coverage mismatch (missing={sorted(expected_keys - actual_keys)}, "
                    f"extra={sorted(actual_keys - expected_keys)})"
                )
            expected_previous = register_identity(checked[-1].register) if checked else None
            if register.previous != expected_previous:
                raise ProfileError(
                    f"previous {register.previous!r}, expected immediate contract predecessor register {expected_previous!r}; "
                    "independent register-only history is unsupported"
                )
        except (OSError, UnicodeDecodeError, ValueError, ScienceError) as exc:
            raise ProfileError(f"{source}: {exc}") from exc
        checked.append(ShippedDomainRevision(directory, contract, register))
    return tuple(checked)
