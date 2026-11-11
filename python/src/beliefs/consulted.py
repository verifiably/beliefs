"""The consulted-contract set — computed, never supplied.

A digest over a supplied consulted set cannot fail when a contract that should
have entered it was withheld, and a check that cannot fail proves nothing. So
membership is walked here: the base contract unconditionally, each domain
contract only if the derivation actually read something it declares, plus the
explicit facet-read arm. What an artefact reads is a collector's answer (§10):
`claim_contracts` for a claim — its operator (and a bridge's template), every
instantiation admitting it, each role referent's sort (`within-model`
included), each qualifier's dimension and restriction sort — and
`assessed_target_contracts` for the complete frozen target, including copied
dependency terms and, with its claim, the declarations admitting its estimand. Every
collector sees every artefact, paired with the claim the caller associates with
it, and returns nothing for one it does not read. Resolution runs against
supplied per-corpus pins; the agreement rule refuses a closure whose corpora
disagree.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.claim import Claim, Member, Referent
from beliefs.errors import ContractDisagreement, ContractMismatch, EstimandError, MalformedRecord
from beliefs.estimand import admit_estimand
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed
from beliefs.target import AssessedTarget, target_terms

__all__ = [
    "BASE_NAMESPACE",
    "Collector",
    "CorpusPins",
    "assessed_target_contracts",
    "claim_contracts",
    "consulted_contracts",
]

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


Collector = Callable[[object, ProfileSpec, Claim | None], AbstractSet[str]]
"""What one artefact of a derivation reads: `(artefact, profile, claim) -> namespaces`.

`claim` is the claim the walk pairs the artefact with — a claim itself, or the
claim of an assessment's target proposition, `None` when that target has none.
The artefact is typed `object` so that every collector is one `Callable`; a
collector narrows it by `isinstance` and returns an empty set for an artefact
it does not read."""


def _referents(value: Referent | tuple[Member, ...]) -> tuple[Referent, ...]:
    if isinstance(value, Referent):
        return (value,)
    return tuple(member.referent for member in value)


def claim_contracts(artefact: object, profile: ProfileSpec, claim: Claim | None) -> frozenset[str]:
    """The namespaces a claim reads (§10): the operator's contract, and a
    bridge's template's; every instantiation admitting the claim, retired ones
    included (the decodable set: a historical claim reads the declaration that
    types it); each role referent's sort, `within-model` included; each
    qualifier's dimension and its restriction sort. `claim` is the artefact
    itself and unused."""
    if not isinstance(artefact, Claim):
        return frozenset()
    operator = profile.operator(artefact.operator)
    read = {operator.contract, profile.template_of(operator).contract}
    read |= {
        profile.declaration_at(address).contract
        for address in profile.admitting(artefact.operator, artefact.assignment(), authoring=False)
    }
    read |= {
        profile.sorts[referent.sort].contract for value in artefact.roles.values() for referent in _referents(value)
    }
    for dimension in artefact.qualifiers:
        declared = profile.dimensions[dimension]
        read |= {declared.contract, profile.sorts[declared.restriction_sort].contract}
    return frozenset(read)


def assessed_target_contracts(artefact: object, profile: ProfileSpec, claim: Claim | None = None) -> set[str]:
    """Read every frozen target term, plus its operator's template and admitting declarations.

    Transitive record terms were copied during freezing. This collector neither
    resolves those records nor reads a world to rediscover their vocabulary.
    """
    if not isinstance(artefact, AssessedTarget):
        return set()
    read = {term.partition("/")[0] for term in target_terms(artefact, profile)}
    operator = profile.operator(artefact.estimand.operator)
    read.update((operator.contract, profile.template_of(operator).contract))
    if claim is not None:
        read.update(admit_estimand(profile, artefact.estimand, claim, authoring=False))
    return read


def consulted_contracts(
    *,
    claims: Mapping[str, Claim],
    targets: Mapping[str, tuple[str, AssessedTarget]] = MappingProxyType({}),
    profile: ProfileSpec,
    node_corpus: Mapping[str, tuple[str, ...]],
    pins: Mapping[str, CorpusPins],
    closure_nodes: tuple[str, ...],
    facets_read: Mapping[str, tuple[str, ...]] = MappingProxyType({}),
    collectors: tuple[Collector, ...] = (claim_contracts, assessed_target_contracts),
) -> tuple[tuple[str, str], ...]:
    """The consulted set, as sorted ``(namespace, identity)`` pairs.

    ``claims`` is keyed by proposition ref; ``targets`` by assessment identity,
    each value the assessment's ``(target proposition ref, assessed target)``. Each
    claim is paired with itself and each estimand with ``claims.get(target)``,
    never with the claim its own ``claim`` field names: that field is what
    admission judges. Every collector runs over every paired artefact. An
    `EstimandError` a collector raises (an estimand naming another claim, or one
    its claim does not admit) is a malformed walk input, `MalformedRecord`."""
    corpora = sorted(
        {corpus for node in closure_nodes if node in node_corpus for corpus in node_corpus[node]}
    ) or sorted(pins)
    if not corpora:
        raise MalformedRecord("a derivation consults at least one corpus's pins")
    unpinned_corpora = sorted(set(corpora) - set(pins))
    if unpinned_corpora:
        raise MalformedRecord(
            f"corpus/corpora {unpinned_corpora} hold a closure node but have no entry in pins; "
            "a node attributed to a corpus whose pins were not supplied is a malformed walk input"
        )

    # Exactly one science_contract, always — agreement unconditional, whether
    # or not any base-profile facet is read.
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
            "never two"
        )
    consulted: dict[str, str] = {BASE_NAMESPACE: base_identity}

    # Each domain contract only if actually read: what every collector reads
    # over every artefact, each paired with its claim, plus the facet reads.
    paired: list[tuple[str, object, Claim | None]] = [(ref, claim, claim) for ref, claim in claims.items()]
    paired.extend(
        (assessment, assessed, claims.get(proposition)) for assessment, (proposition, assessed) in targets.items()
    )
    read: set[str] = set()
    for key, artefact, claim in paired:
        for collector in collectors:
            try:
                read |= collector(artefact, profile, claim)
            except EstimandError as caught:
                raise MalformedRecord(
                    f"{key}: the estimand is not admitted for the claim of the proposition it targets ({caught}); "
                    "a malformed walk input"
                ) from caught
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
                "one derivation, one identity per namespace"
            )
        identity = identities.pop()
        expected = profile.activated_contracts.get(namespace)
        if identity != f"{namespace}:{expected}":
            raise ContractMismatch(
                f"profile-pin-mismatch: {namespace} is pinned {identity[:20]}… but the profile carries "
                f"{namespace}:{str(expected)[:12]}…; a derivation validates and digests under one identity, "
                "never two"
            )
        consulted[namespace] = identity
    return tuple(sorted(consulted.items()))
