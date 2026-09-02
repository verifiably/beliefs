from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import final

import yaml

from beliefs.errors import MalformedContract, SuccessionViolation, UnparsedContract
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "CoordinationContract",
    "CoordinationKindDecl",
    "check_coordination_succession",
    "load_coordination_contract",
    "parse_coordination_contract",
]

COORDINATION_CONTRACT_DOMAIN = "science.coordination-contract.v1"
_MINT = object()
_NAME = re.compile(r"[a-z][a-z0-9-]*")
_IDENTITY = re.compile(r"[0-9a-f]{64}")
_ROOT_REQUIRED = frozenset(
    {"contract", "version", "lineage", "address_root", "query_vocabulary", "kinds"}
)


@dataclass(frozen=True)
class CoordinationKindDecl:
    fields: tuple[str, ...]
    query_versions: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"fields": list(self.fields), "query_versions": list(self.query_versions)}


@sealed
@final
@dataclass(frozen=True, init=False)
class CoordinationContract:
    namespace: str
    version: int
    predecessor: str | None
    address_root: str
    query_kinds: tuple[str, ...]
    query_relations: tuple[str, ...]
    kinds: Mapping[str, CoordinationKindDecl]
    content_identity: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise UnparsedContract(
            "CoordinationContract is parsed, never authored — use "
            "parse_coordination_contract(document, source=..., predecessor=...)."
        )

    @classmethod
    def _parsed(
        cls,
        token: object,
        *,
        version: int,
        predecessor: str | None,
        address_root: str,
        query_kinds: tuple[str, ...],
        query_relations: tuple[str, ...],
        kinds: dict[str, CoordinationKindDecl],
        content_identity: str,
    ) -> CoordinationContract:
        if token is not _MINT:
            raise UnparsedContract(
                "CoordinationContract._parsed is the parser's own route; use "
                "parse_coordination_contract or load_coordination_contract."
            )
        contract = object.__new__(cls)
        for name, value in (
            ("namespace", "coordination"),
            ("version", version),
            ("predecessor", predecessor),
            ("address_root", address_root),
            ("query_kinds", query_kinds),
            ("query_relations", query_relations),
            ("kinds", MappingProxyType({name: kinds[name] for name in sorted(kinds)})),
            ("content_identity", content_identity),
        ):
            object.__setattr__(contract, name, value)
        return contract

    def schema_projection(self) -> dict[str, object]:
        return {
            "address_root": self.address_root,
            "kinds": {name: self.kinds[name].projection() for name in sorted(self.kinds)},
            "query_vocabulary": {
                "kinds": sorted(self.query_kinds),
                "relations": sorted(self.query_relations),
            },
        }


class _CoordinationLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: _CoordinationLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_CoordinationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MalformedContract(f"{where}: expected a mapping, found {type(value).__name__}")
    if any(not isinstance(key, str) for key in value):
        raise MalformedContract(f"{where}: every key must be a string")
    return value  # type: ignore[return-value]


def _fields(
    value: dict[str, object], required: frozenset[str], optional: frozenset[str], where: str
) -> None:
    if not required <= set(value) or set(value) - required - optional:
        raise MalformedContract(
            f"{where}: expected exactly {', '.join(sorted(required))}"
            + (f" with optional {', '.join(sorted(optional))}" if optional else "")
        )


def _strings(value: object, where: str, *, empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not empty):
        raise MalformedContract(f"{where}: expected {'a' if empty else 'a non-empty'} list of strings")
    members = tuple(value)
    if any(not isinstance(member, str) or not member for member in members):
        raise MalformedContract(f"{where}: every member must be a non-empty string")
    if len(set(members)) != len(members):
        raise MalformedContract(f"{where}: duplicate members are refused")
    return tuple(sorted(members))  # type: ignore[arg-type]


def _lineage(value: object, where: str) -> str | None:
    if value == "genesis":
        return None
    lineage = _mapping(value, where)
    _fields(lineage, frozenset({"successor"}), frozenset(), where)
    predecessor = lineage["successor"]
    if not isinstance(predecessor, str) or _IDENTITY.fullmatch(predecessor) is None:
        raise MalformedContract(f"{where}: successor must be a 64-lowercase-hex contract identity")
    return predecessor


def parse_coordination_contract(
    document: object,
    *,
    source: str,
    predecessor: CoordinationContract | None,
) -> CoordinationContract:
    if predecessor is not None and not isinstance(predecessor, CoordinationContract):
        raise UnparsedContract(
            f"predecessor is a {type(predecessor).__name__}, not a parsed CoordinationContract"
        )
    root = _mapping(document, source)
    _fields(root, _ROOT_REQUIRED, frozenset({"description"}), source)
    if root["contract"] != "coordination":
        raise MalformedContract(f"{source}: contract must be 'coordination'")
    version = root["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MalformedContract(f"{source}: version must be a positive integer")
    if "description" in root and not isinstance(root["description"], str):
        raise MalformedContract(f"{source}: description must be a string")
    address_root = root["address_root"]
    if not isinstance(address_root, str) or _NAME.fullmatch(address_root) is None:
        raise MalformedContract(f"{source}: address_root must be a lowercase identifier")

    vocabulary = _mapping(root["query_vocabulary"], f"{source}: query_vocabulary")
    _fields(
        vocabulary,
        frozenset({"kinds", "relations"}),
        frozenset(),
        f"{source}: query_vocabulary",
    )
    query_kinds = _strings(vocabulary["kinds"], f"{source}: query_vocabulary.kinds")
    query_relations = _strings(
        vocabulary["relations"], f"{source}: query_vocabulary.relations"
    )

    raw_kinds = _mapping(root["kinds"], f"{source}: kinds")
    if not raw_kinds:
        raise MalformedContract(f"{source}: kinds must not be empty")
    kinds: dict[str, CoordinationKindDecl] = {}
    for name, value in raw_kinds.items():
        if _NAME.fullmatch(name) is None:
            raise MalformedContract(f"{source}: kinds.{name} is not a lowercase identifier")
        declaration = _mapping(value, f"{source}: kinds.{name}")
        _fields(
            declaration,
            frozenset({"fields", "query_versions"}),
            frozenset(),
            f"{source}: kinds.{name}",
        )
        kinds[name] = CoordinationKindDecl(
            fields=_strings(declaration["fields"], f"{source}: kinds.{name}.fields"),
            query_versions=_strings(
                declaration["query_versions"],
                f"{source}: kinds.{name}.query_versions",
                empty=True,
            ),
        )

    contract = CoordinationContract._parsed(
        _MINT,
        version=version,
        predecessor=_lineage(root["lineage"], f"{source}: lineage"),
        address_root=address_root,
        query_kinds=query_kinds,
        query_relations=query_relations,
        kinds=kinds,
        content_identity=v1.digest(COORDINATION_CONTRACT_DOMAIN, root),
    )
    check_coordination_succession(contract, predecessor)
    return contract


def check_coordination_succession(
    contract: CoordinationContract, predecessor: CoordinationContract | None
) -> None:
    if contract.predecessor is None:
        if predecessor is not None:
            raise SuccessionViolation("coordination genesis cannot have a supplied predecessor")
        return
    if predecessor is None:
        raise SuccessionViolation("coordination successor requires its declared predecessor")
    if predecessor.content_identity != contract.predecessor:
        raise SuccessionViolation("coordination successor names a different predecessor identity")
    if predecessor.namespace != contract.namespace:
        raise SuccessionViolation("coordination successor changes namespace")
    if predecessor.address_root != contract.address_root:
        raise SuccessionViolation("coordination successor changes address_root")

    dropped = set(predecessor.kinds) - set(contract.kinds)
    if dropped:
        raise SuccessionViolation(f"coordination successor drops kinds {sorted(dropped)}")
    for name in predecessor.kinds:
        prior = predecessor.kinds[name]
        current = contract.kinds[name]
        if prior.fields != current.fields:
            raise SuccessionViolation(f"coordination successor changes fields for {name}")
        if not set(prior.query_versions) <= set(current.query_versions):
            raise SuccessionViolation(f"coordination successor drops query versions for {name}")
    if not set(predecessor.query_kinds) <= set(contract.query_kinds):
        raise SuccessionViolation("coordination successor drops query kinds")
    if not set(predecessor.query_relations) <= set(contract.query_relations):
        raise SuccessionViolation("coordination successor drops query relations")


def load_coordination_contract(
    path: Path, *, predecessor: CoordinationContract | None
) -> CoordinationContract:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_CoordinationLoader)
    except yaml.YAMLError as caught:
        raise MalformedContract(f"{path}: not well-formed YAML: {caught}") from caught
    return parse_coordination_contract(document, source=str(path), predecessor=predecessor)
