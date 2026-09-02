"""Contracts — the normative source of truth.

D §6 is explicit that the contracts are the normative SSOT and ``ProfileSpec`` is
the sole *compiled* runtime profile. Nothing here is authored beside a contract.
"""

from beliefs.contract.base import BaseContract, ClaimGrammar, load_base_contract, parse_base_contract
from beliefs.contract.coordination import (
    CoordinationContract,
    CoordinationKindDecl,
    check_coordination_succession,
    load_coordination_contract,
    parse_coordination_contract,
)
from beliefs.contract.domain import (
    DimensionDecl,
    DomainContract,
    OperatorDecl,
    SortDecl,
    VocabularyBinding,
    check_succession,
    load_domain_contract,
    parse_domain_contract,
)

__all__ = [
    "BaseContract",
    "ClaimGrammar",
    "CoordinationContract",
    "CoordinationKindDecl",
    "DimensionDecl",
    "DomainContract",
    "OperatorDecl",
    "SortDecl",
    "VocabularyBinding",
    "check_coordination_succession",
    "check_succession",
    "load_base_contract",
    "load_coordination_contract",
    "load_domain_contract",
    "parse_base_contract",
    "parse_coordination_contract",
    "parse_domain_contract",
]
