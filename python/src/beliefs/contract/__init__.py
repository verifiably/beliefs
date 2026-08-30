"""Contracts — the normative source of truth.

D §6 is explicit that the contracts are the normative SSOT and ``ProfileSpec`` is
the sole *compiled* runtime profile. Nothing here is authored beside a contract.
"""

from beliefs.contract.base import BaseContract, ClaimGrammar, load_base_contract, parse_base_contract
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
    "DimensionDecl",
    "DomainContract",
    "OperatorDecl",
    "SortDecl",
    "VocabularyBinding",
    "check_succession",
    "load_base_contract",
    "load_domain_contract",
    "parse_base_contract",
    "parse_domain_contract",
]
