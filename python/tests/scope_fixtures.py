"""Synthetic scope-relation declarations shared by the scope tests.

Endpoint vocabulary comes from the synthetic `testing` contract; the relations
are owned by a separate synthetic `scope-relations` contract, so composition
across owners is exercised. Neither is an admitted production contract.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from conftest import REPO_ROOT

from beliefs.contract.base import BaseContract
from beliefs.contract.document import load_document
from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.profile import ProfileSpec, compile_profile

VECTOR: dict[str, Any] = json.loads((REPO_ROOT / "fixtures/scope-relations.json").read_text(encoding="utf-8"))
TESTING_PATH = REPO_ROOT / "fixtures/contracts/testing.yaml"
RULE_A = "classification-rule:" + "a" * 64
RULE_B = "classification-rule:" + "b" * 64


def endpoint_document() -> dict[str, Any]:
    document = load_document(TESTING_PATH, source=str(TESTING_PATH))
    assert isinstance(document, dict)
    return document


def scope_document() -> dict[str, Any]:
    return copy.deepcopy(VECTOR["document"])


def apply_change(document: dict[str, Any], change: dict[str, Any]) -> None:
    target = document
    for key in change["path"][:-1]:
        target = target[key]
    if change.get("delete"):
        del target[change["path"][-1]]
    else:
        target[change["path"][-1]] = copy.deepcopy(change["value"])


def endpoint_contract(base: BaseContract, document: dict[str, Any] | None = None) -> DomainContract:
    return parse_domain_contract(
        endpoint_document() if document is None else document, source="testing", base=base, predecessor=None
    )


def scope_contract(
    base: BaseContract, document: dict[str, Any] | None = None, *, predecessor: DomainContract | None = None
) -> DomainContract:
    return parse_domain_contract(
        scope_document() if document is None else document,
        source="scope-relations",
        base=base,
        predecessor=predecessor,
    )


def scope_profile(base: BaseContract, *contracts: DomainContract) -> ProfileSpec:
    return compile_profile(base, [endpoint_contract(base), *contracts])


# --- declared graph builders --------------------------------------------------------

STAGE = "testing/stage"
CASES = "testing/case-status"
RULES = {
    "R": "classification-rule:" + "1" * 64,
    "S": "classification-rule:" + "2" * 64,
    "T": "classification-rule:" + "3" * 64,
}
OWNERS = ("scope-relations", "scope-relations-b", "scope-relations-c")


def term(name: str):
    from beliefs.restriction import TermRestriction

    return TermRestriction(STAGE, f"EX:{name}")


def rule(name: str, *classes: str):
    from beliefs.restriction import RuleRestriction

    return RuleRestriction(RULES[name], tuple(sorted(f"EX:{c}" for c in classes)))


def union(*members):
    from beliefs.restriction import UnionRestriction

    return members[0] if len(members) == 1 else UnionRestriction(tuple(members))


def endpoint(atom: str | tuple[str, str]) -> dict[str, Any]:
    if isinstance(atom, tuple):
        return {"rule": RULES[atom[0]], "classes": [f"EX:{atom[1]}"]}
    return {"sort": STAGE, "term": f"EX:{atom}"}


def relation(left, kind: str, right, *, dimension: str | None = None, retired: bool = False) -> dict[str, Any]:
    if dimension is None:
        dimension = CASES if isinstance(left, tuple) else STAGE
    declared: dict[str, Any] = {
        "dimension": dimension,
        "relation": kind,
        "left": endpoint(left),
        "right": endpoint(right),
    }
    if retired:
        declared["retired"] = True
    return declared


def relations_document(table: dict[str, Any], *, namespace: str = OWNERS[0]) -> dict[str, Any]:
    return {
        "contract": namespace,
        "version": 1,
        "lineage": "genesis",
        "sorts": {},
        "dimensions": {},
        "scope_relations": copy.deepcopy(table),
    }


def graph_profile(
    base: BaseContract, *tables: dict[str, Any], endpoint_doc: dict[str, Any] | None = None
) -> ProfileSpec:
    """`testing` plus one relation-owning contract per table, in owner order."""
    contracts = [
        parse_domain_contract(relations_document(table, namespace=owner), source=owner, base=base, predecessor=None)
        for owner, table in zip(OWNERS, tables, strict=False)
    ]
    return compile_profile(base, [endpoint_contract(base, endpoint_doc), *contracts])
