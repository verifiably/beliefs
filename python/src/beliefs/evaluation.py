"""The instrumented resolver — the only corpus-backed belief evaluation path
(world-changing families §6.3, formal model M1).

`gather` is **the** resolver: every value a belief evaluation obtains from a
corpus comes through it, and it appends to `read_trace` at the moment each
value is handed out. It filters at read time — matched assessments first,
then exactly what they reach — because `belief.Records` is an unfiltered
pool by contract, and a resolver that read the pool would record reads the
digest legitimately omits. `declared_refs` mirrors `build_closure`'s
filtering member for member, and containment is `read_trace ⊆ declared_refs`.

`read_trace` records values **handed out**, not lookups attempted: a key that
resolves to nothing yields no value and traces nothing, which is why a
proposition carrying no claim record needs no declaration for the attempt.

**M1's bound is real and stays stated:** the row is bounded by this resolver.
A read that never crosses it — a module-level constant, an environment
lookup, a cached global, a file opened directly — is invisible and passes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias, final

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, Records, Refused, SuppliedContext, evaluate
from beliefs.claim import Claim
from beliefs.closure import Closure, RetractionEnumeration, build_closure
from beliefs.consulted import consulted_contracts
from beliefs.corpus import ReadView, run_value
from beliefs.dataset import dataset_address
from beliefs.decode import claim_from_stored
from beliefs.errors import ContractDisagreement
from beliefs.lineage import LineageSnapshot
from beliefs.policy import PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue, RunValue
from beliefs.resolution import ResolutionSnapshot
from beliefs.sealed import sealed
from beliefs.verification import Verification

__all__ = ["READ_KINDS", "EvaluationInputs", "ReadRef", "evaluate_over", "gather"]

ReadRef: TypeAlias = tuple[str, str]
READ_KINDS = (
    "assessment",
    "proposition",
    "run",
    "verification",
    "dataset",
    "retraction",
    "contract",
    "producer-snapshot",
)


@sealed
@final
@dataclass(frozen=True)
class EvaluationInputs:
    """`build_closure`'s argument set, plus what was read to obtain it."""

    proposition: str
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    verifications: tuple[Verification, ...]
    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    consulted: tuple[tuple[str, str], ...]
    binding: tuple[str, str]
    claim: Claim | None
    read_trace: tuple[ReadRef, ...]

    def closure(self) -> Closure:
        return build_closure(
            proposition=self.proposition,
            assessments=self.assessments,
            runs=self.runs,
            verifications=self.verifications,
            snapshot=self.snapshot,
            producer_snapshot_identity=self.producer_snapshot_identity,
            retractions=self.retractions,
            consulted=self.consulted,
            binding=self.binding,
        )

    def declared_refs(self) -> frozenset[ReadRef]:
        """`build_closure`'s filtering, member for member, as `(kind, ref)`
        pairs. The two exclusions are the point: **not** every key of `runs`
        and **not** every verification — declaring those would admit a read
        of an unrelated run or verification that the digest omits, and M1
        would pass on exactly the code it exists to catch."""
        ours = tuple(a for a in self.assessments if a.proposition == self.proposition)
        ids = {a.identity() for a in ours}
        refs: set[ReadRef] = set()
        refs.update(("assessment", identity) for identity in ids)
        if ours:
            refs.update(("proposition", a.proposition) for a in ours)
        refs.update(("run", a.run) for a in ours)
        refs.update(("verification", v.ref) for v in self.verifications if v.assessment in ids)
        for a in ours:
            run = self.runs.get(a.run)
            if run is None:
                continue
            for entry in run.inputs:
                if entry.role == stored.OBSERVES and (address := dataset_address(entry.dataset)) is not None:
                    refs.add(("dataset", address))
        refs.update(("retraction", ref) for ref, _ in self.retractions.found)
        refs.update(("contract", identity) for _, identity in self.consulted)
        refs.add(("producer-snapshot", self.producer_snapshot_identity))
        return frozenset(refs)

    def records(self) -> Records:
        return Records(
            claims={self.proposition: self.claim} if self.claim is not None else {},
            assessments=self.assessments,
            runs=self.runs,
            source_assertions=(),
            verifications=self.verifications,
        )


def _verification_selected(value: Verification, ids: frozenset[str]) -> bool:
    """The one predicate M1's sabotage flips: an unrelated verification read
    through the resolver must fail containment while leaving the digest alone."""
    return value.assessment in ids


def gather(
    view: ReadView,
    proposition: str,
    *,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
) -> EvaluationInputs:
    """Resolve one proposition's belief inputs from a corpus, tracing each
    value at the moment it is handed out."""
    trace: list[ReadRef] = []
    matched: list[AssessmentValue] = []
    proposition_refs: list[str] = []
    for node in view.iter_stored():
        if node.kind != "assessment":
            continue
        value = stored.assessment_value(node)
        if value.proposition != proposition:
            continue  # a lookup, not a value handed out
        matched.append(value)
        trace.append(("assessment", value.identity()))
        proposition_refs.extend(r.target for r in node.relations if r.predicate == stored.ASSESSES)
    ids = frozenset(a.identity() for a in matched)

    runs: dict[str, RunValue] = {}
    for a in matched:
        if a.run in runs or not view.holds(a.run):
            continue
        runs[a.run] = run_value(view, a.run)
        trace.append(("run", a.run))
        for entry in runs[a.run].inputs:
            if entry.role == stored.OBSERVES and (address := dataset_address(entry.dataset)) is not None:
                trace.append(("dataset", address))

    verifications: list[Verification] = []
    for node in view.iter_stored():
        if node.kind != "verification":
            continue
        value = stored.verification_value(node)
        if _verification_selected(value, ids):
            verifications.append(value)
            trace.append(("verification", value.ref))

    claim: Claim | None = None
    for ref in dict.fromkeys(proposition_refs):
        if view.holds(ref):
            claim, _receipt = claim_from_stored(view.get(ref), profile=profile, snapshot=resolution)
            trace.append(("proposition", proposition))
            break

    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        profile=profile,
        node_corpus=context.node_corpus,
        pins=context.pins,
        closure_nodes=tuple(sorted(ids)),
    )
    return EvaluationInputs(
        proposition=proposition,
        assessments=tuple(matched),
        runs=runs,
        verifications=tuple(verifications),
        snapshot=context.snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=context.retractions,
        consulted=consulted,
        binding=(binding.rule, binding.implementation),
        claim=claim,
        read_trace=tuple(trace),
    )


def evaluate_over(
    view: ReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
) -> Belief | NoBelief | Refused:
    """`evaluate`'s step-1 guard first, then `gather`, then `evaluate`.

    The guard runs before anything is read: without it the wrapper would open
    the corpus, or crash projecting `.rule` off a `None` or a string, before
    `evaluate` ever got to refuse — turning a clean refusal into reads and an
    exception."""
    if not isinstance(binding, PolicyBinding):
        return Refused(f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair")
    try:
        inputs = gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=binding)
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    return evaluate(
        proposition=proposition,
        records=inputs.records(),
        availability=availability,
        context=context,
        binding=binding,
        profile=profile,
    )
