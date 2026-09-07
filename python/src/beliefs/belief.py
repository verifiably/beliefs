"""``evaluate`` — the belief evaluator, end to end (kernel §5, belief-policy §4).

Three answers, as banked: a computed `Belief`, a `NoBelief` (the computation
succeeded and found none), or a `Refused` (the computation could not be
trusted to run at all). Reasons are discriminants *within* an arm, never a
fourth answer.

`sum(∅) = 0` is never a reportable answer. The empty-selection case is caught
at step 6, before `aggregate` is ever called — a proposition with no eligible
or no directional assessment never reaches the aggregator. What *does* reach
it and publish `Belief(0)` is a genuinely **balanced** directional set (one
support, one independent refutation): the sum really is zero, computed, not
defaulted.

Heldness selects the *shape* of the answer — whether a held-eligible input is
even available to weigh — never the answer's value, and it is not a member of
the belief input closure (ρA8): nothing about which datasets happened to be
held here is digested, because two evaluators with different holdings must be
able to agree on the digest of the belief they each *could* compute.

The evaluator stores nothing. Every field of every answer is derived, fresh,
from the arguments of one call — there is no belief record, no "current
belief" selector, and no cache; the module namespace itself carries no
mutable state for the same reason `verification.lifecycle_state` takes no
memory of its own (kernel §3.3's non-negotiable: a pure function of its
argument, called again every time it is asked).
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.admission import AdmissionRefused, Admitted, admit
from beliefs.claim import Claim
from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.consulted import CorpusPins, consulted_contracts
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import ContractDisagreement, MalformedRecord
from beliefs.lineage import LineageSnapshot, certify
from beliefs.policy import (
    AggregationInput,
    DirectionalInput,
    FixtureCase,
    PolicyBinding,
    PolicyImplementation,
    conforms,
)
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue, RunValue, SourceAssertion
from beliefs.sealed import sealed
from beliefs.verification import ADMITTED, Verification, lifecycle_state

__all__ = [
    "NO_BELIEF_REASONS",
    "OUTCOME_SIGNS",
    "Availability",
    "Belief",
    "NoBelief",
    "Records",
    "Refused",
    "SuppliedContext",
    "evaluate",
]

# Base outcome semantics — deliberately not the policy's to choose (D §8).
# `supported`, `refuted` and `inconclusive` already carry meanings fixed by
# kernel §4.2.1's facet table, and a policy permitted to remap them would be
# a policy permitted to reverse them, which is reinterpreting an outcome, not
# aggregating it. In a full system this mapping is the `science_contract`'s
# meaning-bearing content; here it is pinned as a module constant because
# that contract does not yet own a place to declare it.
OUTCOME_SIGNS: Mapping[str, int] = MappingProxyType({"supported": 1, "refuted": -1, "inconclusive": 0})

NO_BELIEF_REASONS = (
    "unavailable-policy-unheld",
    "unavailable-fixtures-unheld",
    "unavailable-input-unheld",
    "unavailable-corpus-absent",
    "no-eligible-assessment",
    "no-directional-outcome",
)
"""The closed set of `NoBelief` reasons (belief-policy §4). `unavailable-
corpus-absent` is banked but **unreachable in this slice**: records arrive as
call arguments, so there is no corpus for this evaluator to find absent — the
same defined-but-unreachable pattern cut 1 used for `not-present`."""


@sealed
@final
@dataclass(frozen=True)
class Belief:
    value: int
    belief_input_digest: str
    """Accompanies the `Belief` arm only (ρA8) — a `NoBelief` or `Refused`
    answer has no committed input set to digest."""

    policy_binding: PolicyBinding


@sealed
@final
@dataclass(frozen=True)
class NoBelief:
    reason: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.reason not in NO_BELIEF_REASONS:
            raise MalformedRecord(f"NoBelief reason {self.reason!r} is outside the closed set {NO_BELIEF_REASONS}")


@sealed
@final
@dataclass(frozen=True)
class Refused:
    reason: str


@sealed
@final
@dataclass(frozen=True)
class Records:
    """The belief-input record pool, unfiltered — `evaluate` filters
    `assessments`, `runs` and `verifications` to `proposition` internally (as
    does the closure it builds), and reads at most **one** entry of `claims`:
    the derivation's own claim, keyed by `proposition` itself, never the
    whole pool — an unrelated claim present here must move neither the value
    nor the digest."""

    claims: Mapping[str, Claim]
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    source_assertions: tuple[SourceAssertion, ...]
    """Never read below (G1): a source-assertion asserts, denies or
    hypothesizes, and moves no belief output byte."""
    verifications: tuple[Verification, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", MappingProxyType(dict(self.claims)))
        object.__setattr__(self, "runs", MappingProxyType(dict(self.runs)))


@sealed
@final
@dataclass(frozen=True)
class Availability:
    """What is held **here**, supplied explicitly — never ambient (M11's
    doctrine, cut 1). Keyed by dataset address, policy rule identity and
    implementation content identity respectively."""

    observations: Mapping[str, tuple[ByteObservation, ...]]
    implementations: Mapping[str, PolicyImplementation]
    fixtures: Mapping[str, tuple[FixtureCase, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", MappingProxyType(dict(self.observations)))
        object.__setattr__(self, "implementations", MappingProxyType(dict(self.implementations)))
        object.__setattr__(self, "fixtures", MappingProxyType(dict(self.fixtures)))


@sealed
@final
@dataclass(frozen=True)
class SuppliedContext:
    """The closure members this evaluator does not compute itself — already
    resolved, and digested rather than derived (`closure.py`'s module
    docstring)."""

    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    node_corpus: Mapping[str, str]
    pins: Mapping[str, CorpusPins]

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_corpus", MappingProxyType(dict(self.node_corpus)))
        object.__setattr__(self, "pins", MappingProxyType(dict(self.pins)))


def _observes_roots(run: RunValue) -> tuple[str, ...]:
    """The addresses `certify`'s independence test compares — every
    `observes` input's dataset address. A `None` address never enters: it
    belongs to a dataset that already failed admission (G2b), so no assessment
    reaching this point can carry one."""
    return tuple(
        address for i in run.inputs if i.role == "observes" if (address := dataset_address(i.dataset)) is not None
    )


def evaluate(
    *,
    proposition: str,
    records: Records,
    availability: Availability,
    context: SuppliedContext,
    binding: object,
    profile: ProfileSpec,
) -> Belief | NoBelief | Refused:
    """Belief-policy §4's evaluation order, exactly, top to bottom."""
    # 1. The binding is exact, or nothing computes (P1).
    if not isinstance(binding, PolicyBinding):
        return Refused(f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair")

    # 2. The consulted-contract walk, over the closure's assessment nodes
    # (D7, unchanged: a cross-corpus disagreement refuses, never merges).
    # `claims` is narrowed to the derivation's own claim — at most one entry,
    # keyed by `proposition` — never the whole record pool: membership in a
    # digested closure member must come from what this derivation reads, not
    # from whatever else the caller happened to pass in `records.claims`. A
    # proposition with no claim record consults only the base contract.
    matched = tuple(a for a in records.assessments if a.proposition == proposition)
    closure_nodes = tuple(a.identity() for a in matched)
    read_claims = {proposition: records.claims[proposition]} if proposition in records.claims else {}
    try:
        consulted = consulted_contracts(
            claims=read_claims,
            profile=profile,
            node_corpus=context.node_corpus,
            pins=context.pins,
            closure_nodes=closure_nodes,
        )
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")

    # 3. The exact binding must be held here — fixtures, then implementation.
    if binding.rule not in availability.fixtures:
        return NoBelief("unavailable-fixtures-unheld")
    if binding.implementation not in availability.implementations:
        return NoBelief("unavailable-policy-unheld")

    # 4. A named implementation that fails its own fixtures is false, not
    # merely unresolved (P2) — installing a conforming one beside it changes
    # nothing, because the binding names the failing identity.
    implementation = availability.implementations[binding.implementation]
    fixtures = availability.fixtures[binding.rule]
    if not conforms(implementation, fixtures):
        return Refused(
            f"implementation-fails-fixtures: {binding.implementation!r} does not conform to "
            f"{binding.rule!r}'s fixture set"
        )

    # 5. Gate every assessment on the proposition through admission (G2b, G6,
    # G2c). Partition eligible from "would be eligible, if only its input
    # were held" (unheld_only) — the latter needs its own verification-state
    # check, since `admit` never reaches that check for an input-not-held
    # refusal.
    eligible: list[AssessmentValue] = []
    unheld_only: list[AssessmentValue] = []
    for a in matched:
        admission = admit(a, records.runs[a.run], availability.observations, records.verifications)
        if isinstance(admission, Admitted):
            eligible.append(a)
        elif isinstance(admission, AdmissionRefused) and admission.reason.startswith("input-not-held"):
            own_verifications = tuple(v for v in records.verifications if v.assessment == a.identity())
            if lifecycle_state(own_verifications) == ADMITTED:
                unheld_only.append(a)

    # 6. Directional eligibility, and the absence precedence (belief-policy
    # §4, P4, P9): a withheld directional input outranks plain absence of
    # eligibility, which outranks an eligible set with nothing directional.
    directional = [a for a in eligible if OUTCOME_SIGNS[a.outcome] != 0]
    if not directional:
        if unheld_only and any(OUTCOME_SIGNS[a.outcome] != 0 for a in unheld_only):
            return NoBelief("unavailable-input-unheld")
        if not eligible:
            return NoBelief("no-eligible-assessment")
        return NoBelief("no-directional-outcome")

    # 7. The dependency graph: directional vertices, an edge for every pair
    # not certified independent (S6, S5) — absence of an edge is a positive
    # claim of independence, never the default.
    #
    # Two assessment records can carry one identity (design decision 17):
    # the graph is over the identity, not the record, so a twin contributes
    # no second vertex and no self-edge — aggregating it twice would
    # double-count identical evidence, which is exactly what
    # `AggregationInput`'s distinctness check refuses. First occurrence in
    # `directional`'s existing order wins, so the belief input digest stays
    # deterministic; `records.assessments` and the closure at step 9 still
    # carry every record unfiltered.
    seen_identities: set[str] = set()
    graph_inputs: list[AssessmentValue] = []
    for a in directional:
        identity = a.identity()
        if identity not in seen_identities:
            seen_identities.add(identity)
            graph_inputs.append(a)
    vertices = tuple(DirectionalInput(assessment=a.identity(), sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs)
    edges: list[tuple[str, str]] = []
    for a, b in itertools.combinations(graph_inputs, 2):
        certification = certify(
            context.snapshot, _observes_roots(records.runs[a.run]), _observes_roots(records.runs[b.run])
        )
        if certification.state != "independent":
            edges.append((a.identity(), b.identity()))

    # 8. Aggregate, under the exact bound implementation.
    problem = AggregationInput(vertices=vertices, edges=tuple(edges))
    value = implementation.aggregate(problem)

    # 9. The belief input closure (task 7), and the answer it accompanies.
    closure = build_closure(
        proposition=proposition,
        assessments=records.assessments,
        runs=records.runs,
        verifications=records.verifications,
        snapshot=context.snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=context.retractions,
        consulted=consulted,
        binding=(binding.rule, binding.implementation),
    )
    return Belief(value=value, belief_input_digest=closure.digest(), policy_binding=binding)
