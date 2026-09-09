"""The consulted-contract set — computed, never supplied (cut 2 §3).

A digest over a supplied consulted set cannot fail when a contract that should
have entered it was withheld, and an arm that cannot fail is malformed under
N2. So membership is walked here: the base contract unconditionally, each
domain contract only if the derivation actually read something it declares —
which in this slice means the claim schema: the proposition's operator, whose
compiled declaration carries the namespace that declared it (formal model ρA6:
a facet-only walk would miss exactly this), plus the explicit facet-read arm.
Resolution runs against supplied
per-corpus pins; §8.1's agreement rule refuses a closure whose corpora disagree.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.claim import Claim
from beliefs.errors import ContractDisagreement, ContractMismatch, MalformedRecord
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed

__all__ = ["BASE_NAMESPACE", "CorpusPins", "consulted_contracts"]

BASE_NAMESPACE = "science"
"""The reserved key the base contract is consulted under. Never a domain's."""


@sealed
@final
@dataclass(frozen=True)
class CorpusPins:
    science_contract: str
    domains: Mapping[str, str]

    def __post_init__(self) -> None:
        if BASE_NAMESPACE in self.domains:
            raise MalformedRecord("the base contract is pinned by its own field, never as a domain")
        object.__setattr__(self, "domains", MappingProxyType(dict(self.domains)))


def consulted_contracts(
    *,
    claims: Mapping[str, Claim],
    profile: ProfileSpec,
    node_corpus: Mapping[str, tuple[str, ...]],
    pins: Mapping[str, CorpusPins],
    closure_nodes: tuple[str, ...],
    facets_read: Mapping[str, tuple[str, ...]] = MappingProxyType({}),
) -> tuple[tuple[str, str], ...]:
    corpora = sorted({corpus for node in closure_nodes if node in node_corpus for corpus in node_corpus[node]}) or sorted(pins)
    if not corpora:
        raise MalformedRecord("a derivation consults at least one corpus's pins")
    unpinned_corpora = sorted(set(corpora) - set(pins))
    if unpinned_corpora:
        raise MalformedRecord(
            f"corpus/corpora {unpinned_corpora} hold a closure node but have no entry in pins; "
            "a node attributed to a corpus whose pins were not supplied is a malformed walk input"
        )

    # Exactly one science_contract, always — agreement unconditional, whether
    # or not any base-profile facet is read (D §8).
    base_identities = {pins[corpus].science_contract for corpus in corpora}
    if len(base_identities) != 1:
        raise ContractDisagreement(
            f"corpora {corpora} pin different science_contracts {sorted(base_identities)}; "
            "refused, never merged, never resolved by recency"
        )
    base_identity = base_identities.pop()
    if base_identity != "science:" + profile.base_contract_identity:
        raise ContractMismatch(
            f"profile-pin-mismatch: science is pinned {base_identity[:20]}… but the profile carries "
            f"science:{profile.base_contract_identity[:12]}…; a derivation validates and digests under one identity, "
            "never two (biology pack §5.3a)"
        )
    consulted: dict[str, str] = {BASE_NAMESPACE: base_identity}

    # Each domain contract only if actually read. A claim reaches its
    # contract through the operator, and through every sort and dimension the
    # operator declares (D §8, ρA6); a facet read reaches its namespace.
    read: set[str] = set()
    for claim in claims.values():
        operator = profile.operator(claim.operator)
        read.add(operator.contract)
        for sort in operator.arg_sorts:
            read.add(profile.sorts[sort].contract)
        for dimension in operator.dimensions:
            declared = profile.dimensions[dimension]
            read.add(declared.contract)
            read.add(profile.sorts[declared.restriction_sort].contract)
    for node, keys in facets_read.items():
        if node not in closure_nodes:
            raise MalformedRecord(
                f"{node} is reported read but is not a closure node; a read ledger names closure members only"
            )
        for key in keys:
            namespace, separator, _ = key.partition("/")
            if separator:
                read.add(namespace)
    for namespace in sorted(read):
        identities = {pins[corpus].domains[namespace] for corpus in corpora if namespace in pins[corpus].domains}
        if not identities:
            raise ContractDisagreement(
                f"namespace {namespace!r} is consulted but pinned by no corpus in {corpora}; "
                "unresolvable, not merely disputed"
            )
        if len(identities) != 1:
            raise ContractDisagreement(
                f"namespace {namespace!r} resolves to {sorted(identities)} across corpora {corpora}; "
                "one derivation, one identity per namespace (D §8.1)"
            )
        identity = identities.pop()
        expected = profile.activated_contracts.get(namespace)
        if identity != f"{namespace}:{expected}":
            raise ContractMismatch(
                f"profile-pin-mismatch: {namespace} is pinned {identity[:20]}… but the profile carries "
                f"{namespace}:{str(expected)[:12]}…; a derivation validates and digests under one identity, "
                "never two (biology pack §5.3a)"
            )
        consulted[namespace] = identity
    return tuple(sorted(consulted.items()))
