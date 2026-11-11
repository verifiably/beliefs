"""``evaluate`` — the belief evaluator, end to end.

Three answers: a computed `Belief`, a `NoBelief` (the computation
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
the belief input closure: nothing about which datasets happened to be
held here is digested, because two evaluators with different holdings must be
able to agree on the digest of the belief they each *could* compute.

The evaluator stores nothing. Every field of every answer is derived, fresh,
from the arguments of one call — there is no belief record, no "current
belief" selector, and no cache; the module namespace itself carries no
mutable state for the same reason `verification.lifecycle_state` takes no
memory of its own (a pure function of its argument, called again every time it
is asked).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import final

from beliefs import errors, stored
from beliefs.admission import AdmissionRefused, Admitted, admit
from beliefs.claim import Claim
from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.consulted import CorpusPins, consulted_contracts
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import ContractDisagreement, MalformedRecord
from beliefs.evidence import DependencyEvidence
from beliefs.facet_read import FacetRead
from beliefs.identity import v1
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
    "AcceptanceContext",
    "AcceptancePolicy",
    "Availability",
    "Belief",
    "NoBelief",
    "NotReached",
    "Reached",
    "Records",
    "Refused",
    "SuppliedContext",
    "admitted",
    "evaluate",
    "evaluate_traced",
    "standing_roots",
]

# Base outcome semantics — deliberately not the policy's to choose.
# `supported`, `refuted` and `inconclusive` already carry meanings fixed by
# the kernel's facet table, and a policy permitted to remap them would be
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
"""The closed set of `NoBelief` reasons. `unavailable-
corpus-absent` is returned by `evaluate_over` over a world read view whose
inputs reach a record the epoch maps to a covered corpus with no carrier."""


def _acceptance_statement(statement: str) -> None:
    if type(statement) is not str or not statement:
        raise MalformedRecord("acceptance-statement-not-text")
    v1.encode(statement)


@sealed
@final
@dataclass(frozen=True)
class AcceptancePolicy:
    """One caller-pinned selection predicate and its opaque identity statement."""

    counts: Callable[[str, str], bool]
    statement: str

    def __post_init__(self) -> None:
        if not callable(self.counts):
            raise MalformedRecord("acceptance-predicate-not-callable")
        _acceptance_statement(self.statement)


@sealed
@final
@dataclass(frozen=True)
class AcceptanceContext:
    statement: str
    excluded: tuple[tuple[str, str], ...]
    complete: bool

    def __post_init__(self) -> None:
        _acceptance_statement(self.statement)
        if not self.complete and self.excluded:
            raise MalformedRecord("incomplete-acceptance-exclusions")
        object.__setattr__(self, "excluded", tuple(sorted(set(self.excluded))))


@sealed
@final
@dataclass(frozen=True)
class Belief:
    value: int
    belief_input_digest: str
    """Accompanies the `Belief` arm only — a `NoBelief` or `Refused`
    answer has no committed input set to digest."""

    policy_binding: PolicyBinding
    acceptance: AcceptanceContext | None = None


@sealed
@final
@dataclass(frozen=True)
class NoBelief:
    reason: str
    detail: str = ""
    acceptance: AcceptanceContext | None = None

    def __post_init__(self) -> None:
        if self.reason not in NO_BELIEF_REASONS:
            raise MalformedRecord(f"NoBelief reason {self.reason!r} is outside the closed set {NO_BELIEF_REASONS}")


@sealed
@final
@dataclass(frozen=True)
class Refused:
    reason: str
    acceptance: AcceptanceContext | None = None


@sealed
@final
@dataclass(frozen=True)
class NotReached:
    """The answer was given before step 5: admission never ran, and no set —
    not even the empty one — describes what it would have found."""


@sealed
@final
@dataclass(frozen=True)
class Reached:
    """Step 5 ran; `admitted` is what it admitted, possibly nothing."""

    admitted: frozenset[str]


Admission = NotReached | Reached


def admitted(
    distinct: Sequence[AssessmentValue],
    *,
    runs: Mapping[str, RunValue],
    observations: Mapping[str, tuple[ByteObservation, ...]],
    verifications: tuple[Verification, ...],
    dependencies: DependencyEvidence,
) -> tuple[tuple[AssessmentValue, ...], tuple[AssessmentValue, ...]]:
    """Step 5's gate, once: `(eligible, unheld_only)` over the identity-collapsed pool."""
    eligible: list[AssessmentValue] = []
    unheld_only: list[AssessmentValue] = []
    for a in distinct:
        admission = admit(a, runs[a.run], observations, verifications, dependencies)
        if isinstance(admission, Admitted):
            eligible.append(a)
        elif isinstance(admission, AdmissionRefused) and admission.reason.startswith("input-not-held"):
            own_verifications = tuple(v for v in verifications if v.assessment == a.identity())
            if lifecycle_state(own_verifications) == ADMITTED:
                unheld_only.append(a)
    return tuple(eligible), tuple(unheld_only)


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
    """Never read below: a source-assertion asserts, denies or
    hypothesizes, and moves no belief output byte."""
    verifications: tuple[Verification, ...]
    observed_facets: tuple[FacetRead, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", MappingProxyType(dict(self.claims)))
        object.__setattr__(self, "runs", MappingProxyType(dict(self.runs)))
        object.__setattr__(self, "observed_facets", tuple(self.observed_facets))
        for row in self.observed_facets:
            if type(row) is not FacetRead:
                raise MalformedRecord(
                    f"observed_facets carries a {type(row).__name__}, not a FacetRead; only the reader mints one"
                )
        if list(self.observed_facets) != sorted(self.observed_facets, key=FacetRead.projection):
            raise MalformedRecord(
                "observed_facets is sorted by (address, key, digest); an unsorted carrier is not the reader's"
            )


@sealed
@final
@dataclass(frozen=True)
class Availability:
    """What is held **here**, supplied explicitly — never ambient.
    Keyed by dataset address, policy rule identity and
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
    node_corpus: Mapping[str, tuple[str, ...]]
    pins: Mapping[str, CorpusPins]
    acceptance: AcceptanceContext | None = None

    def __post_init__(self) -> None:
        if any(
            not isinstance(corpora, tuple)
            or not corpora
            or not all(isinstance(corpus, str) for corpus in corpora)
            or corpora != tuple(sorted(corpora))
            for corpora in self.node_corpus.values()
        ):
            raise MalformedRecord("node_corpus attributes each node to a non-empty tuple of corpus ids")
        object.__setattr__(self, "node_corpus", MappingProxyType(dict(self.node_corpus)))
        object.__setattr__(self, "pins", MappingProxyType(dict(self.pins)))


def _observes_roots(run: RunValue) -> tuple[str, ...]:
    """The addresses `certify`'s independence test compares — every
    `observes` input's dataset address. A `None` address never enters: it
    belongs to a dataset that already failed admission, so no assessment
    reaching this point can carry one."""
    return tuple(
        address for i in run.inputs if i.role == "observes" if (address := dataset_address(i.dataset)) is not None
    )


def standing_roots(assessment: AssessmentValue, run: RunValue, dependencies: DependencyEvidence) -> tuple[str, ...]:
    """Return the declared route's sources; computational repeats share a model."""
    from beliefs.errors import DependencyCycle, DependencyNotHeld
    from beliefs.procedure import Procedure
    from beliefs.proxy_model import Calibration, ProxyModel

    active: set[str] = set()

    def roots(value: AssessmentValue, execution: RunValue) -> set[str]:
        identity = value.identity()
        if identity in active:
            raise DependencyCycle("standing-roots: cyclic calibration assessment")
        if value.standing == "empirical":
            return set(_observes_roots(execution))
        model = dependencies.records.get(value.target.model or "")
        if not isinstance(model, Procedure) or model.inputs is None or value.target.model is None:
            raise DependencyNotHeld("standing-roots: model procedure and inputs are required")
        result = {value.target.model, *model.inputs.datasets, *model.inputs.code}
        if value.standing == "model":
            return result
        proxy = dependencies.records.get(value.estimand.calibration or "")
        if not isinstance(proxy, ProxyModel) or not isinstance(proxy.basis, Calibration):
            raise DependencyNotHeld("standing-roots: calibration proxy is required")
        active.add(identity)
        try:
            for ref in proxy.basis.assessments:
                basis = dependencies.assessments.get(ref)
                basis_run = None if basis is None else dependencies.runs.get(stored.typed_ref("run", basis.run))
                if basis is None or basis_run is None:
                    raise DependencyNotHeld(f"standing-roots: calibration assessment or run is absent: {ref}")
                result.update(roots(basis, basis_run))
        finally:
            active.difference_update((identity,))
        return result

    return tuple(sorted(roots(assessment, run)))


def evaluate_traced(
    *,
    proposition: str,
    key: str,
    dependencies: DependencyEvidence,
    records: Records,
    availability: Availability,
    context: SuppliedContext,
    retractions: RetractionEnumeration,
    binding: object,
    profile: ProfileSpec,
) -> tuple[Belief | NoBelief | Refused, Admission]:
    """Evaluate selected inputs and accompany every answer with its selection."""
    answer, admission = _evaluate_traced(
        proposition=proposition,
        key=key,
        dependencies=dependencies,
        records=records,
        availability=availability,
        context=context,
        retractions=retractions,
        binding=binding,
        profile=profile,
    )
    if context.acceptance is not None:
        answer = replace(answer, acceptance=context.acceptance)
    return answer, admission


def _evaluate_traced(
    *,
    proposition: str,
    key: str,
    dependencies: DependencyEvidence,
    records: Records,
    availability: Availability,
    context: SuppliedContext,
    retractions: RetractionEnumeration,
    binding: object,
    profile: ProfileSpec,
) -> tuple[Belief | NoBelief | Refused, Admission]:
    """The belief policy's evaluation order, exactly, top to bottom, and the
    admission the answer rests on — `not-reached` for every answer given
    before step 5 completed."""
    # 1. The binding is exact, or nothing computes.
    if not isinstance(binding, PolicyBinding):
        return Refused(
            f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair"
        ), NotReached()

    if context.acceptance is not None and not context.acceptance.complete:
        return Refused("acceptance-selection-incomplete"), NotReached()

    # 2. The consulted-contract walk, over the closure's assessments, runs and observed datasets
    # (a cross-corpus disagreement refuses, never merges).
    # `claims` is narrowed to the derivation's own claim — at most one entry,
    # keyed by `proposition` — never the whole record pool: membership in a
    # digested closure member must come from what this derivation reads, not
    # from whatever else the caller happened to pass in `records.claims`. A
    # proposition with no claim record consults only the base contract.
    candidates = tuple(a for a in records.assessments if a.proposition == proposition)
    facets_by_id: dict[str, str] = {}
    for a in candidates:
        previous = facets_by_id.setdefault(a.identity(), a.facet_digest())
        if previous != a.facet_digest():
            return Refused(f"assessment-identity-contradicted: {a.identity()} has disagreeing records"), NotReached()
    matched = tuple(a for a in candidates if a.key() == key)
    for row in records.observed_facets:
        namespace = row.key.partition("/")[0]
        if profile.activated_contracts.get(namespace) != row._contract_identity:
            return Refused(f"facet-read-profile-mismatch: {namespace}"), NotReached()
    observed = tuple(
        sorted(
            {
                address
                for a in matched
                for entry in records.runs[a.run].inputs
                if entry.role == "observes" and (address := dataset_address(entry.dataset)) is not None
            }
        )
    )
    closure_nodes = (
        tuple(a.identity() for a in matched) + tuple(stored.typed_ref("run", a.run) for a in matched) + observed
    )
    ledger: dict[str, list[str]] = {}
    for row in records.observed_facets:
        ledger.setdefault(row.address, []).append(row.key)
    read_claims = {proposition: records.claims[proposition]} if proposition in records.claims else {}
    try:
        consulted = consulted_contracts(
            claims=read_claims,
            targets={a.identity(): (a.proposition, a.target) for a in matched},
            profile=profile,
            node_corpus=context.node_corpus,
            pins=context.pins,
            closure_nodes=closure_nodes,
            facets_read={address: tuple(keys) for address, keys in ledger.items()},
        )
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}"), NotReached()
    except errors.ContractMismatch as exc:
        return Refused(str(exc)), NotReached()  # already prefixed `profile-pin-mismatch: <namespace>` by the walk

    # 3. The exact binding must be held here — fixtures, then implementation.
    if binding.rule not in availability.fixtures:
        return NoBelief("unavailable-fixtures-unheld"), NotReached()
    if binding.implementation not in availability.implementations:
        return NoBelief("unavailable-policy-unheld"), NotReached()

    # 4. A named implementation that fails its own fixtures is false, not
    # merely unresolved — installing a conforming one beside it changes
    # nothing, because the binding names the failing identity.
    implementation = availability.implementations[binding.implementation]
    fixtures = availability.fixtures[binding.rule]
    if not conforms(implementation, fixtures):
        return (
            Refused(
                f"implementation-fails-fixtures: {binding.implementation!r} does not conform to "
                f"{binding.rule!r}'s fixture set"
            ),
            NotReached(),
        )

    # 5. Collapse the record pool onto its identities, then gate what survives
    # through admission. Partition eligible from "would be
    # eligible, if only its input were held" (unheld_only) — the latter needs
    # its own verification-state check, since `admit` never reaches that check
    # for an input-not-held refusal. The gate is `admitted` above, called here
    # exactly once: what the answer rests on and what the trace reports are one
    # set by construction, never two derivations that could disagree.
    #
    # Two assessment records can carry one identity: the
    # graph at step 7 is over the identity, not the record, so a genuine twin
    # must contribute no second vertex and no self-edge — aggregating it twice
    # would double-count identical evidence, which is exactly what
    # `AggregationInput`'s distinctness check refuses. `identity()` alone does
    # not make two records the same fact, though: it digests only
    # `(spec, run, proposition)`, while `outcome` and the rest live in
    # `facet_digest()`, an independent write-path parameter with no
    # cross-check. So a shared identity is collapsed only when the kept
    # record's facet also agrees — an identity-equal, facet-disagreeing pair is
    # a corpus contradiction, refused loudly rather than silently resolved by
    # file order. First occurrence in `matched`'s existing order is what a
    # genuine twin collapses onto, keeping the belief *value* deterministic;
    # `records.assessments` and the closure at step 9 still carry every record
    # unfiltered.
    #
    # The collapse runs here, over the whole matched pool, and not over the
    # directional records at step 7: `outcome` is the very parameter the guard
    # cross-checks, so a pair disagreeing *across* the directional boundary —
    # a `supported` record and an `inconclusive` twin — is precisely a
    # contradiction, and a guard reading only the directional side would never
    # see it. Admission is no filter for it either: heldness and verification
    # state are supplied per call and move over time, and whether the corpus
    # contradicts itself must not depend on which observations this caller
    # happened to pass.
    kept_by_identity: dict[str, AssessmentValue] = {}
    distinct: list[AssessmentValue] = []
    for a in matched:
        identity = a.identity()
        kept = kept_by_identity.get(identity)
        if kept is None:
            kept_by_identity[identity] = a
            distinct.append(a)
        elif kept.facet_digest() != a.facet_digest():
            # Loud, and still an answer: `evaluate` is total over its three
            # arms, exactly as the cross-corpus contract contradiction at
            # step 2 is (`consulted-contracts-disagree`), which is no less
            # severe.
            return (
                Refused(
                    f"assessment-identity-contradicted: {identity!r} is claimed by disagreeing records "
                    f"{kept!r} and {a!r}"
                ),
                NotReached(),
            )

    eligible, unheld_only = admitted(
        distinct,
        runs=records.runs,
        observations=availability.observations,
        verifications=records.verifications,
        dependencies=dependencies,
    )
    reached = Reached(frozenset(a.identity() for a in eligible))

    # 6. Directional eligibility, and the absence precedence: a withheld directional input outranks plain absence of
    # eligibility, which outranks an eligible set with nothing directional.
    directional = [a for a in eligible if OUTCOME_SIGNS[a.outcome] != 0]
    if not directional:
        if unheld_only and any(OUTCOME_SIGNS[a.outcome] != 0 for a in unheld_only):
            return NoBelief("unavailable-input-unheld"), reached
        if not eligible:
            return NoBelief("no-eligible-assessment"), reached
        return NoBelief("no-directional-outcome"), reached

    # 7. The dependency graph: directional vertices, an edge for every pair
    # not certified independent — absence of an edge is a positive
    # claim of independence, never the default. Step 5 already collapsed the
    # pool onto its identities, so these records are distinct by identity and
    # the graph carries no second vertex and no self-edge for a genuine twin.
    graph_inputs = directional
    vertices = tuple(
        DirectionalInput(assessment=a.identity(), sign=OUTCOME_SIGNS[a.outcome], standing=a.standing)
        for a in graph_inputs
    )
    edges: list[tuple[str, str]] = []
    for a, b in itertools.combinations(graph_inputs, 2):
        certification = certify(
            context.snapshot,
            standing_roots(a, records.runs[a.run], dependencies),
            standing_roots(b, records.runs[b.run], dependencies),
        )
        if certification.state != "independent":
            edges.append((a.identity(), b.identity()))

    # 8. Aggregate, under the exact bound implementation.
    problem = AggregationInput(vertices=vertices, edges=tuple(edges))
    value = implementation.aggregate(problem)

    # 9. The belief input closure, and the answer it accompanies.
    closure = build_closure(
        proposition=proposition,
        key=key,
        dependencies=dependencies,
        assessments=records.assessments,
        runs=records.runs,
        verifications=records.verifications,
        snapshot=context.snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=retractions,
        consulted=consulted,
        binding=(binding.rule, binding.implementation),
        observed_facets=records.observed_facets,
        acceptance_statement=None if context.acceptance is None else context.acceptance.statement,
    )
    return Belief(value=value, belief_input_digest=closure.digest(), policy_binding=binding), reached


def evaluate(
    *,
    proposition: str,
    key: str,
    dependencies: DependencyEvidence,
    records: Records,
    availability: Availability,
    context: SuppliedContext,
    retractions: RetractionEnumeration,
    binding: object,
    profile: ProfileSpec,
) -> Belief | NoBelief | Refused:
    """The belief policy's evaluation order, exactly, top to bottom — the first
    projection of `evaluate_traced`, so the answer cannot differ from it."""
    return evaluate_traced(
        proposition=proposition,
        key=key,
        dependencies=dependencies,
        records=records,
        availability=availability,
        context=context,
        retractions=retractions,
        binding=binding,
        profile=profile,
    )[0]
