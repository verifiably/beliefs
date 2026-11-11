"""The instrumented resolver — the only corpus-backed belief evaluation path.

`gather` is **the** resolver: every value a belief evaluation obtains from a
corpus comes through it, and it appends to `read_trace` at the moment each
value is handed out. It filters at read time — matched assessments first,
then exactly what they reach — because `belief.Records` is an unfiltered
pool by contract, and a resolver that read the pool would record reads the
digest legitimately omits. `declared_refs` mirrors `build_closure`'s
filtering member for member, and containment is `read_trace ⊆ declared_refs`.

`read_trace` records selected values handed out and attempted dependency reads,
including missing frozen references. A missing optional claim yields no value;
its lookup is distinct from a required dependency attempt.

**The bound is real and stays stated:** the containment check is bounded by this resolver.
A read that never crosses it — a module-level constant, an environment
lookup, a cached global, a file opened directly — is invisible and passes.

One read *does* cross this resolver and is deliberately outside its traced
set, and it is named here rather than left for a reader to discover.
`corpus.run_value` builds a `RunValue` whose inputs carry the dataset
declaration for **every** role — `reads` and `transforms` as well as
`observes` — so a `reads` declaration is handed out inside a run value
without a `("dataset", …)` trace entry. That is not a gap in the
instrumentation but the closure's own shape: `declared_refs`
table admits dataset refs only under `observes`, mirroring `build_closure`'s
`observes` member, and no closure member consumes any other role's
declaration. Tracing one would record a read the digest cannot move for,
which is the mirror of the failure `declared_refs`' exclusions prevent.
`test_a_reads_input_declaration_crosses_gather_untraced` pins both halves:
the untraced hand-out, and the digest that does not move with it.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias, cast, final

from nodes.core.errors import RefError
from nodes.core.node import Node

from beliefs import stored
from beliefs.belief import (
    AcceptanceContext,
    AcceptancePolicy,
    Admission,
    Availability,
    Belief,
    NoBelief,
    NotReached,
    Records,
    Refused,
    SuppliedContext,
    evaluate_traced,
    standing_roots,
)
from beliefs.claim import Claim
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, Closure, RetractionEnumeration, build_closure
from beliefs.comparability import ComparabilitySnapshot
from beliefs.consulted import consulted_contracts
from beliefs.corpus import ReadView, _absence_of, retraction_standing, run_value
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.decode import claim_from_stored
from beliefs.dependencies import Record, dependency_closure, read_record
from beliefs.eligibility import AssessmentEligibilityReader, ClosureEligibility, Ineligible, closure_eligibility
from beliefs.errors import (
    AmbiguousCrosswalk,
    CaptureDrift,
    ContractDisagreement,
    ContractMismatch,
    CorpusDamaged,
    DependencyCycle,
    DependencyNotHeld,
    FacetPayloadRefused,
    FacetUndeclared,
    InputOutsideCorpus,
    MalformedRecord,
    ProducerSnapshotMismatch,
    ProducerSnapshotRetracted,
    RetractionResolutionDisagreement,
    RetractionUnreadable,
    ScienceError,
)
from beliefs.evidence import DependencyEvidence
from beliefs.facet_read import FACET_READ_DOMAIN, FacetRead, read_observed_facets
from beliefs.identity import v1
from beliefs.lineage import LineageSnapshot, absences, retire
from beliefs.measurement import Observable
from beliefs.policy import PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import ProxyModel, proxy_from_stored
from beliefs.record import AssessmentValue, RunValue
from beliefs.resolution import ResolutionSnapshot
from beliefs.sealed import sealed
from beliefs.target_comparison import (
    AssessedProposition,
    ConversionVerdict,
    SynthesisVerdict,
    TargetUnknown,
    convertibility,
    synthesis,
)
from beliefs.verification import Verification

if TYPE_CHECKING:
    from beliefs.world.view import WorldReadView

__all__ = [
    "READ_KINDS",
    "ClaimView",
    "EvaluationInputs",
    "PairVerdict",
    "ReadRef",
    "claim_view",
    "evaluate_over",
    "evaluate_over_traced",
    "gather",
]

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
    "procedure",
    "referent-mapping",
    "proxy-model",
    "classification-rule",
    "assumptions-register",
)


@sealed
@final
@dataclass(frozen=True)
class EvaluationInputs:
    """`build_closure`'s argument set, plus what was read to obtain it."""

    proposition: str
    key: str
    dependencies: DependencyEvidence
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    verifications: tuple[Verification, ...]
    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    consulted: tuple[tuple[str, str], ...]
    binding: tuple[str, str]
    observed_facets: tuple[FacetRead, ...]
    claim: Claim | None
    read_trace: tuple[ReadRef, ...]
    node_corpus: Mapping[str, tuple[str, ...]]
    """Attribution derived at the world read, or supplied for a corpus view."""
    absent: tuple[tuple[str, str], ...] = ()
    """`(ref, corpus_id)` for recorded inputs whose covered corpus has no carrier.
    These are reasons no closure was built, not closure members or declared reads."""
    acceptance: AcceptanceContext | None = None

    def closure(self) -> Closure:
        return build_closure(
            proposition=self.proposition,
            key=self.key,
            dependencies=self.dependencies,
            assessments=self.assessments,
            runs=self.runs,
            verifications=self.verifications,
            snapshot=self.snapshot,
            producer_snapshot_identity=self.producer_snapshot_identity,
            retractions=self.retractions,
            consulted=self.consulted,
            binding=self.binding,
            observed_facets=self.observed_facets,
            acceptance_statement=None if self.acceptance is None else self.acceptance.statement,
        )

    def declared_refs(self) -> frozenset[ReadRef]:
        """`build_closure`'s filtering, member for member, as `(kind, ref)`
        pairs. The two exclusions are the point: **not** every key of `runs`
        and **not** every verification — declaring those would admit a read
        of an unrelated run or verification that the digest omits, and the containment check
        would pass on exactly the code it exists to catch."""
        ours = tuple(a for a in self.assessments if a.proposition == self.proposition and a.key() == self.key)
        ids = {a.identity() for a in (*ours, *self.dependencies.assessments.values())}
        refs: set[ReadRef] = set()
        refs.update(("assessment", identity) for identity in ids)
        if ours:
            refs.update(("proposition", a.proposition) for a in ours)
        refs.update(("run", a.run) for a in (*ours, *self.dependencies.assessments.values()))
        refs.update((ref.partition(":")[0], ref) for ref in self.dependencies.closure.reads)
        refs.update(
            ("dataset", address)
            for run in self.dependencies.runs.values()
            for entry in run.inputs
            if entry.role == "observes" and (address := dataset_address(entry.dataset)) is not None
        )
        # The predicate is spelled out here rather than calling
        # `_verification_selected`: the sabotage flips that one predicate, and
        # a declaration sharing it would widen with the read it must catch.
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
            observed_facets=self.observed_facets,
        )


def _verification_selected(value: Verification, ids: frozenset[str]) -> bool:
    """The one predicate the containment sabotage flips: an unrelated verification read
    through the resolver must fail containment while leaving the digest alone."""
    return value.assessment in ids


def _expected_facet_rows(node: Node, address: str) -> frozenset[tuple[str, str, str]]:
    """The complete facet rows the captured record would mint."""
    return frozenset(
        (address, key, v1.digest(FACET_READ_DOMAIN, node.facets[key])) for key in node.facets if "/" in key
    )


def _facets_held_to_capture(profile: ProfileSpec, view: WorldReadView, target: str) -> tuple[FacetRead, ...]:
    """Read through the holding corpus's exact ReadView, then bind its rows to the capture."""
    captured = view.get(target)
    address = dataset_address(stored.dataset_declaration(captured))
    rows = read_observed_facets(profile, view.corpus_view(target), target)
    returned = frozenset((row.address, row.key, row.payload_digest) for row in rows)
    assert address is not None  # gather calls the reader only for addressed datasets.
    expected = _expected_facet_rows(captured, address)
    if returned != expected:
        raise CaptureDrift(
            f"{target}: the facet read returned rows {sorted(returned - expected)} the capture lacks and lacked "
            f"rows {sorted(expected - returned)} the capture holds; a write landed after the capture"
        )
    return rows


def _captured_holders(view: WorldReadView, ref: str) -> tuple[str, ...]:
    """The captured corpora holding `ref`: the epoch's holders minus
    the absent ones; a damaged holder refused the read before any loop."""
    present = view.captured()
    return tuple(holder for holder in view.holders_of(ref) if holder in present)


def _absent_inputs(
    proposition: str,
    context: SuppliedContext,
    enumeration: RetractionEnumeration,
    absent: tuple[tuple[str, str], ...],
    trace: tuple[ReadRef, ...],
    binding: PolicyBinding,
    world: bool,
) -> EvaluationInputs:
    """No selection runs over a partial fold: an `EvaluationInputs` whose only
    content is the absence, which `evaluate_over_traced` answers as
    `unavailable-corpus-absent`."""
    return EvaluationInputs(
        proposition=proposition,
        key="",
        dependencies=DependencyEvidence(ClosureEligibility({}, ()), {}, {}, {}),
        assessments=(),
        runs={},
        verifications=(),
        snapshot=context.snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=RetractionEnumeration(found=(), coverage=enumeration.coverage),
        consulted=(),
        binding=(binding.rule, binding.implementation),
        claim=None,
        read_trace=trace,
        observed_facets=(),
        absent=absent,
        node_corpus=MappingProxyType({} if world else dict(context.node_corpus)),
    )


class _AcceptanceSelection:
    """Decisions and completion belong to one evaluation, never its read view."""

    def __init__(self, policy: AcceptancePolicy | None) -> None:
        self.policy = policy
        self._decisions: dict[tuple[str, str], bool] = {}
        self.report = None if policy is None else AcceptanceContext(policy.statement, (), False)

    def counts(self, corpus_id: str, address: str) -> bool:
        if self.policy is None:
            return True
        key = (corpus_id, address)
        if key not in self._decisions:
            result = self.policy.counts(corpus_id, address)
            if type(result) is not bool:
                raise MalformedRecord("acceptance-result-not-bool")
            self._decisions[key] = result
        return self._decisions[key]

    def finish(self) -> None:
        if self.policy is not None:
            self.report = AcceptanceContext(
                self.policy.statement,
                tuple(sorted(key for key, accepted in self._decisions.items() if not accepted)),
                True,
            )


def _check_filtered_world_standing(
    view: WorldReadView,
    enumeration: RetractionEnumeration,
    facets: Mapping[str, Mapping[str, object]],
    standing: Mapping[str, bool],
) -> None:
    """One comparison of the filtered fold against the receipt.

    `standing` is gather's own world fold over the accepted facets, resolved
    through the epoch's address map alone. The affected set is every rejected
    retraction and, transitively through the retraction-discovery map, every
    retraction one of them counters; for every surviving retraction outside
    it the fold must reproduce the receipt's resolution. An enumeration that
    records two resolutions for one ref (a v1-bound epoch over a split) is
    refused by rule, never reduced to whichever pair sorts last.
    """
    receipt: dict[str, str] = {}
    for ref, recorded in enumeration.found:
        canonical = view.resolve(ref)
        assert canonical is not None
        earlier = receipt.setdefault(canonical, recorded)
        if earlier != recorded:
            computed = RETRACTION_UPHELD if standing.get(canonical, True) else RETRACTION_OVERTURNED
            raise RetractionResolutionDisagreement(
                canonical,
                earlier,
                computed,
                detail=(
                    f"{canonical}: the enumeration records two resolutions, {earlier!r} and {recorded!r}; "
                    "one fold cannot reproduce both (the epoch folded per corpus over a split)"
                ),
            )
    affected = {ref for ref in receipt if ref not in facets}
    # Original counter dependencies come from the package, not rejected facets.
    parents: dict[str, set[str]] = {}
    for target, counters in view._retraction_discovery.items():
        resolved = view.resolve(target)
        if resolved not in receipt:
            continue
        for counter in counters:
            counted = view.resolve(counter)
            if counted in receipt:
                assert resolved is not None and counted is not None
                parents.setdefault(counted, set()).add(resolved)
    pending = list(affected)
    while pending:
        for parent in parents.get(pending.pop(), ()):
            if parent not in affected:
                affected.add(parent)
                pending.append(parent)
    for ref in facets:
        computed = RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED
        if ref not in affected and computed != receipt[ref]:
            raise RetractionResolutionDisagreement(ref, receipt[ref], computed)


class _InputRefused(MalformedRecord):
    pass


class _DiscoveryRefused(MalformedRecord):
    pass


@dataclass(frozen=True)
class _Discovery:
    view: ReadView | WorldReadView
    assessments: tuple[AssessmentValue, ...]
    enumeration: RetractionEnumeration
    facets: Mapping[str, Mapping[str, object]]
    subtracted: set[str]
    retired: Mapping[str, set[str]]
    history: tuple[tuple[str, str], ...]
    absent: tuple[tuple[str, str], ...]
    attribution: Mapping[str, set[str]]
    proposition_refs: tuple[str, ...]
    visited: set[str]
    assessment_refs: Mapping[str, str]
    verification_targets: Mapping[str, str]
    world: bool
    local_corpus: str | None


def _discover(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    context: SuppliedContext,
    binding: PolicyBinding,
    profile: ProfileSpec,
    selection: _AcceptanceSelection,
) -> _Discovery:
    from beliefs.corpus import CorpusWriter, local_retraction_enumeration
    from beliefs.world.view import WorldReadView

    if context.acceptance is not None:
        raise MalformedRecord("supplied-acceptance-context")
    if isinstance(view, WorldReadView) and context.node_corpus:
        raise MalformedRecord(
            "node_corpus is derived from a world read and must be supplied empty; a caller may not relocate a record"
        )
    if context.snapshot.retired:
        raise MalformedRecord("a supplied lineage snapshot carries no retirement; a caller may not pre-retire a route")
    if type(view) is ReadView:
        view = view.captured()
    world = isinstance(view, WorldReadView)
    counts = None if selection.policy is None else selection.counts
    local_corpus = view.corpus_id if counts is not None and not world else None
    absent: list[tuple[str, str]] = []
    history: tuple[tuple[str, str], ...] = ()
    if world:
        bound = view.producer_snapshot_identity()
        if context.producer_snapshot_identity != bound:
            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)
        for report in view.damaged():  # the first damaged corpus refuses; the rest are not reported
            raise CorpusDamaged(f"producer-snapshot:{bound}", report.corpus_id, view.stamp)
        for corpus_id in view.absent():
            absent.append((f"producer-snapshot:{bound}", corpus_id))
        snapshot_standing = view.snapshot_standing(counts=counts)
        if not absent and bound in snapshot_standing.retracted:
            raise ProducerSnapshotRetracted(bound)
        history = snapshot_standing.history.get(bound, ())
    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view, counts=counts)

    # --- standing, before any assessment is read ------------------------------
    trace: list[ReadRef] = []
    facets: dict[str, Mapping[str, object]] = {}
    for ref, _recorded in enumeration.found:
        if counts is not None:
            absent_corpus = _absence_of(view, ref)
            if absent_corpus is not None:
                absent.append((ref, absent_corpus))
                continue
            canonical = view.resolve(ref)
            if canonical is None:
                raise RetractionUnreadable(ref, "the inventoried reference does not resolve")
            # Accepted iff any captured holder's branch says so, every holder asked;
            # a damaged holder refused the read above, and an absent one is not captured.
            if isinstance(view, WorldReadView):
                holders = _captured_holders(view, ref)
            else:
                assert local_corpus is not None
                holders = (local_corpus,)
            decisions = [counts(holder, canonical) for holder in holders]
            if not any(decisions):
                continue
        else:
            canonical = ref
        try:
            corpus_id = _absence_of(view, ref)
            if corpus_id is not None:
                absent.append((ref, corpus_id))
                continue
            node = view.get(ref)  # a lookup; traced below only if the closure carries it
            facet = CorpusWriter._validated_retraction(node)
            target = cast(Mapping[str, str], facet["target"])
            if target["arm"] == "snapshot":
                facets[canonical] = (
                    facet  # a vertex only: its one possible closure member is the bound snapshot, checked above
                )
                continue
            target_ref = target["ref"] if target["arm"] == "node" else target["dataset"]
            corpus_id = _absence_of(view, target_ref)
            if corpus_id is not None:
                absent.append((target_ref, corpus_id))
                continue
            CorpusWriter._resolve_retraction_target(node, view)  # exact resolution, content identity, route presence
        except (ScienceError, RefError) as caught:
            raise RetractionUnreadable(ref, str(caught)) from caught
        facets[canonical] = facet
    if absent:
        return _Discovery(
            view,
            (),
            enumeration,
            facets,
            set(),
            {},
            history,
            tuple(sorted(set(absent))),
            {},
            (),
            set(),
            {},
            {},
            world,
            local_corpus,
        )
    standing = retraction_standing(view, facets)
    if counts is not None and world:
        _check_filtered_world_standing(view, enumeration, facets, standing)
        enumeration = replace(
            enumeration,
            found=tuple(sorted((ref, RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED) for ref in facets)),
        )
    else:
        for ref, recorded in enumeration.found:
            computed = RETRACTION_UPHELD if standing[ref] else RETRACTION_OVERTURNED
            if computed != recorded:
                raise RetractionResolutionDisagreement(ref, recorded, computed)
    subtracted: set[str] = set()
    retired: dict[str, set[str]] = {}
    for ref, facet in facets.items():
        if not standing[ref]:
            continue
        target = cast(Mapping[str, str], facet["target"])
        if target["arm"] == "node":
            subtracted.add(target["resolved"])
        elif target["arm"] == "route":
            retired.setdefault(target["resolved"], set()).add(target["route_identity"])
        # a snapshot arm names no node and no route

    assessment_refs: dict[str, str] = {}
    attribution: dict[str, set[str]] = {}
    matched: list[AssessmentValue] = []
    proposition_refs: list[str] = []
    visited: set[str] = set()  # this proposition's assessment ids, subtracted included
    verification_targets: dict[str, str] = {}
    candidates: Iterable[tuple[tuple[str | None, ...], Node]] = (
        view._mapped_holders() if world else (((local_corpus,), node) for node in view.iter_stored())
    )
    for holders, node in candidates:
        if node.kind != "assessment":
            continue
        # Accepted iff any captured holder's branch says so, every holder asked.
        decisions = None if counts is None else [counts(cast(str, holder), node.id) for holder in holders]
        accepted = decisions is None or any(decisions)
        # beliefs-010c6e: membership by the `assesses` edge, before any decode.
        targets = [r.target for r in node.relations if r.predicate == stored.ASSESSES]
        wanted = view.resolve(proposition) or proposition
        if not any((view.resolve(target) or target) == wanted for target in targets):
            continue  # a lookup, not a value handed out — membership by the edge, never by decoding
        try:
            verification_targets[node.id] = stored.assessment_reference(node).identity()
        except MalformedRecord:
            # Rejected/retracted facets need not be decodable even for identity.
            pass
        if not accepted:
            continue
        visited.add(node.id)
        if node.id in subtracted:
            continue  # a standing retraction names it: a lookup, never decoded
        try:
            value = stored.assessment_value(node, profile=profile)
        except MalformedRecord as exc:
            raise _DiscoveryRefused(f"unclassifiable-assessment: {node.id}: {exc}") from exc
        if value.proposition != proposition:
            raise MalformedRecord(
                f"{node.id}: the assesses edge names {proposition!r} but the facet names {value.proposition!r}"
            )
        previous = next((a for a in matched if a.identity() == value.identity()), None)
        if previous is not None and previous.facet_digest() != value.facet_digest():
            raise _DiscoveryRefused(f"assessment-identity-contradicted: {value.identity()} has disagreeing records")
        assessment_refs[node.id] = value.identity()
        matched.append(value)
        if world:
            accepting = holders if decisions is None else tuple(h for h, d in zip(holders, decisions) if d)
            attribution.setdefault(value.identity(), set()).update(cast(tuple[str, ...], accepting))
        trace.append(("assessment", value.identity()))
        proposition_refs.extend(targets)
    # Every holder decision is invocation-wide, including sibling verifications.
    if counts is not None:
        for holders, node in view._mapped_holders() if world else (((local_corpus,), n) for n in view.iter_stored()):
            if node.kind in {
                "verification",
                "procedure",
                "referent-mapping",
                "proxy-model",
                "classification-rule",
                "assumptions-register",
            }:
                for holder in holders:
                    counts(cast(str, holder), node.id)
    selection.finish()
    return _Discovery(
        view,
        tuple(matched),
        enumeration,
        facets,
        subtracted,
        retired,
        history,
        (),
        attribution,
        tuple(proposition_refs),
        visited,
        assessment_refs,
        verification_targets,
        world,
        local_corpus,
    )


def gather(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    key: str,
    observations: Mapping[str, tuple[ByteObservation, ...]],
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
    acceptance: AcceptancePolicy | None = None,
) -> EvaluationInputs:
    """Resolve exactly one key from a single captured claim discovery."""
    selection = _AcceptanceSelection(acceptance)
    discovery = _discover(view, proposition, context=context, binding=binding, profile=profile, selection=selection)
    return _gather(
        discovery,
        proposition,
        key=key,
        context=context,
        profile=profile,
        resolution=resolution,
        binding=binding,
        selection=selection,
        observations=observations,
    )


def _gather(
    discovery: _Discovery,
    proposition: str,
    *,
    key: str,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
    selection: _AcceptanceSelection,
    observations: Mapping[str, tuple[ByteObservation, ...]],
) -> EvaluationInputs:
    from beliefs.world.view import WorldReadView

    view = discovery.view
    world, local_corpus = discovery.world, discovery.local_corpus
    enumeration, facets = discovery.enumeration, discovery.facets
    subtracted, retired, history = discovery.subtracted, discovery.retired, discovery.history
    if discovery.absent:
        return replace(
            _absent_inputs(proposition, context, enumeration, discovery.absent, (), binding, world),
            key=key,
            acceptance=selection.report,
        )
    counts = None if selection.policy is None else selection.counts
    matched = tuple(a for a in discovery.assessments if a.key() == key)
    ids = frozenset(a.identity() for a in matched)
    visited = {ref for ref, identity in discovery.assessment_refs.items() if identity in ids}
    visited.update(discovery.visited - discovery.assessment_refs.keys())
    verification_targets = {ref for ref, identity in discovery.verification_targets.items() if identity in ids}
    attribution = {id: holders for id, holders in discovery.attribution.items() if id in ids}
    proposition_refs = discovery.proposition_refs if matched else ()
    trace: list[ReadRef] = [("assessment", a.identity()) for a in matched]
    absent: list[tuple[str, str]] = []
    # --- runs and observed facets: unchanged from the baseline ------------------
    runs: dict[str, RunValue] = {}
    observed: dict[tuple[str, str, str], FacetRead] = {}
    for a in matched:
        ref = stored.typed_ref("run", a.run)
        if a.run in runs:
            continue
        if not view.holds(ref):
            corpus_id = _absence_of(view, ref)
            if corpus_id is not None:
                absent.append((ref, corpus_id))
            else:
                # The refusal reaches the run itself: a session
                # writes an assessment over a read mount's run, so a corpus-local read
                # refuses it, never skipping a run `evaluate` then indexes.
                raise InputOutsideCorpus(a.identity(), ref, (ref,))
            continue
        try:
            run_node = view.get(ref)
            if run_node.kind != "run" or stored.run_spec(run_node) is None:
                raise MalformedRecord(f"{ref}: expected a run with a declared spec")
            runs[a.run] = run_value(view, ref)
        except MalformedRecord as exc:
            raise _InputRefused(f"malformed-input: {exc}") from exc
        trace.append(("run", a.run))
        if isinstance(view, WorldReadView):
            attribution.setdefault(ref, set()).update(_captured_holders(view, ref))
        outside: list[str] = []
        for role in stored.INPUT_ROLES:
            for target in stored.inputs_of(run_node, role):
                if not view.holds(target):
                    corpus_id = _absence_of(view, target)
                    if corpus_id is not None:
                        absent.append((target, corpus_id))
                    elif not world:
                        outside.append(target)
        if outside:
            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))
        for target in stored.inputs_of(run_node, stored.OBSERVES):
            if not view.holds(target):
                continue
            address = dataset_address(stored.dataset_declaration(view.get(target)))
            if address is None:
                continue
            trace.append(("dataset", address))
            if isinstance(view, WorldReadView):
                attribution.setdefault(address, set()).update(_captured_holders(view, target))
            for row in (
                _facets_held_to_capture(profile, view, target)
                if isinstance(view, WorldReadView)
                else read_observed_facets(profile, view, target)
            ):
                observed[(row.address, row.key, row.payload_digest)] = row
    reader = _CapturedComparisonRecords(discovery, selection, profile, observations)
    dependencies = reader.evidence(matched)
    trace.extend(reader.trace)
    absent.extend(reader.absent)
    snapshot = retire(context.snapshot, retired)
    roots: set[str] = set()
    for assessment in matched:
        if assessment.run not in runs:
            continue
        try:
            roots.update(standing_roots(assessment, runs[assessment.run], dependencies))
        except (DependencyNotHeld, DependencyCycle):
            pass  # admission reports the missing dependency; its attempted read remains declared
    if len({a.key() for a in discovery.assessments}) > 1:
        snapshot = _key_snapshot(snapshot, tuple(sorted(roots)))
    absent.extend((entry.ref, entry.corpus_id) for entry in absences(snapshot))
    rows = tuple(observed[key] for key in sorted(observed))

    verifications: list[Verification] = []
    verification_ids: set[str] = set()
    candidates = (
        view._mapped_holders()
        if isinstance(view, WorldReadView)
        else (((local_corpus,), node) for node in view.iter_stored())
    )
    for holders, node in candidates:
        if node.kind != "verification":
            continue
        if counts is not None:
            decided = [counts(cast(str, holder), node.id) for holder in holders]  # every holder asked
            if not any(decided):
                continue
        names = {r.target for r in node.relations if r.predicate == stored.VERIFIES}
        if not any(view.resolve(name) in verification_targets for name in names if view.resolve(name) is not None):
            continue  # membership by the `verifies` edge, never by decoding
        verification_ids.add(node.id)
        if node.id in subtracted:
            continue  # it leaves the read set; `active` recomputes over what remains
        try:
            value = stored.verification_value(node)
        except MalformedRecord as exc:
            raise _InputRefused(f"malformed-input: {node.id}: {exc}") from exc
        if _verification_selected(value, ids):
            verifications.append(value)
            trace.append(("verification", value.ref))

    verifications.extend(reader.verifications.values())
    verifications = list({v.ref: v for v in verifications}.values())
    visited.update(dependencies.closure.reads)
    verification_ids.update(reader.verification_ids)
    # --- the closure's enumeration: this proposition's inputs, transitively
    scope = visited | verification_ids | set(snapshot.bases)
    taken: set[str] = set()
    grew = True
    while grew:
        grew = False
        for ref, facet in facets.items():
            if ref in taken:
                continue
            target = cast(Mapping[str, str], facet["target"])
            target_key = None if target["arm"] == "snapshot" else target["resolved"]  # a snapshot arm is never in scope
            if target_key is not None and (target_key in scope or target_key in taken):
                taken.add(ref)
                grew = True
    scoped = RetractionEnumeration(
        found=tuple(sorted({*((ref, recorded) for ref, recorded in enumeration.found if ref in taken), *history})),
        coverage=enumeration.coverage,
    )
    trace.extend(("retraction", ref) for ref, _recorded in scoped.found)
    selection.finish()

    # --- the claim, consulted, attribution: unchanged from the baseline ----------
    claim: Claim | None = None
    for ref in dict.fromkeys(proposition_refs):
        corpus_id = _absence_of(view, ref)
        if corpus_id is not None:
            absent.append((ref, corpus_id))
        if view.holds(ref):
            claim, _receipt = claim_from_stored(view.get(ref), profile=profile, snapshot=resolution)
            # Trace the reference actually read.
            trace.append(("proposition", ref))
            break
    ledger: dict[str, list[str]] = {}
    for row in rows:
        ledger.setdefault(row.address, []).append(row.key)
    observed_addresses = tuple(
        sorted({row.address for row in rows} | {ref for kind, ref in trace if kind == "dataset"})
    )
    node_corpus = (
        {node: tuple(sorted(corpora)) for node, corpora in attribution.items()} if world else context.node_corpus
    )
    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        targets={a.identity(): (a.proposition, a.target) for a in matched},
        profile=profile,
        node_corpus=node_corpus,
        pins=context.pins,
        closure_nodes=tuple(sorted(ids)) + tuple(stored.typed_ref("run", a.run) for a in matched) + observed_addresses,
        facets_read={address: tuple(keys) for address, keys in ledger.items()},
    )
    return EvaluationInputs(
        proposition=proposition,
        key=key,
        dependencies=dependencies,
        assessments=tuple(matched),
        runs=runs,
        verifications=tuple(verifications),
        snapshot=snapshot,
        producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=scoped,
        consulted=consulted,
        binding=(binding.rule, binding.implementation),
        claim=claim,
        read_trace=tuple(trace),
        observed_facets=rows,
        absent=tuple(sorted(set(absent))),
        node_corpus=MappingProxyType(dict(node_corpus)),
        acceptance=selection.report,
    )


def _key_snapshot(snapshot: LineageSnapshot, roots: tuple[str, ...]) -> LineageSnapshot:
    """Project only lineage reachable from this key's standing roots."""
    reached: set[str] = set()
    pending = list(roots)
    while pending:
        ref = pending.pop()
        if ref in reached:
            continue
        reached.add(ref)
        basis = snapshot.bases.get(ref)
        if basis is not None:
            pending.extend(r.resolved_ancestor for r in basis.routes if r.resolved_ancestor is not None)
    return LineageSnapshot(
        roots,
        {k: v for k, v in snapshot.bases.items() if k in reached},
        {k: v for k, v in snapshot.producers.items() if k in reached},
        {k: v for k, v in snapshot.not_present.items() if k in reached},
        {k: v for k, v in snapshot.retired.items() if k in reached},
    )


def _capture_identity(
    discovery: _Discovery,
    context: SuppliedContext,
    selection: _AcceptanceSelection,
    observations: Mapping[str, tuple[ByteObservation, ...]],
) -> str:
    from beliefs.lineage import snapshot_projection

    view = discovery.view
    return v1.digest(
        "science.claim-view.v1",
        {
            "producer_snapshot": context.producer_snapshot_identity,
            "observation_digests": sorted({o.digest for values in observations.values() for o in values}),
            "records": sorted(
                [n.id, v1.digest("science.captured-record.v1", n.model_dump_json(exclude_none=True))]
                for n in view.iter_stored()
            ),
            "lineage": snapshot_projection(retire(context.snapshot, discovery.retired)),
            "retractions": [list(pair) for pair in discovery.enumeration.found],
            "absent": [list(pair) for pair in discovery.absent],
            "acceptance": []
            if selection.report is None
            else [selection.report.statement, [list(pair) for pair in selection.report.excluded]],
        },
    )


class _CapturedComparisonRecords:
    """Measurement and assessment reads from one captured fold, never specs or bytes.

    Each keyed gather owns a reader; pair comparison owns a separate reader over
    the same capture, so its lookup reads cannot widen a keyed belief closure.
    """

    def __init__(
        self,
        discovery: _Discovery,
        selection: _AcceptanceSelection,
        profile: ProfileSpec,
        observations: Mapping[str, tuple[ByteObservation, ...]],
    ) -> None:
        self.discovery, self.selection, self.profile = discovery, selection, profile
        self.view = discovery.view
        self.digests = frozenset(o.digest for values in observations.values() for o in values)
        self.reads: set[str] = set()
        self.trace: list[ReadRef] = []
        self.assessments: dict[str, AssessmentValue] = {}
        self.runs: dict[str, RunValue] = {}
        self.verifications: dict[str, Verification] = {}
        self.verification_ids: set[str] = set()
        self.absent: list[tuple[str, str]] = []
        self.assessment_eligibility = AssessmentEligibilityReader(self, profile, self.run_of, self.verifications_of)

    def _attempt(self, id: str) -> None:
        self.reads.add(id)
        self.trace.append((id.partition(":")[0], id))
        absent = _absence_of(self.view, id)
        if absent is not None:
            self.absent.append((id, absent))

    def _accepted(self, id: str) -> bool:
        if self.selection.policy is None:
            return True
        from beliefs.world.view import WorldReadView

        holders = _captured_holders(self.view, id) if isinstance(self.view, WorldReadView) else (self.view.corpus_id,)
        decisions = [self.selection.counts(holder, self.view.resolve(id) or id) for holder in holders]
        return any(decisions)

    def holds(self, id: str) -> bool:
        self._attempt(id)
        return self.view.holds(id) and self._accepted(id)

    def read(self, id: str) -> Node:
        if not self.holds(id):
            raise DependencyNotHeld(f"dependency not held: {id}")
        node = self.view.get(id)
        if node.kind == "assessment":
            self.assessments[id] = stored.assessment_value(node, profile=self.profile)
        return node

    def retraction_in_force(self, id: str) -> bool:
        return (self.view.resolve(id) or id) in self.discovery.subtracted

    def observation_held(self, digest: str) -> bool:
        return digest in self.digests

    def run_of(self, id: str) -> RunValue:
        ref = stored.typed_ref("run", id)
        self.trace.append(("run", id))
        if not self.view.holds(ref):
            absent = _absence_of(self.view, ref)
            if absent is not None:
                self.absent.append((ref, absent))
            raise DependencyNotHeld(f"calibration run not held: {ref}")
        if self.retraction_in_force(ref):
            raise DependencyNotHeld(f"calibration run retracted: {ref}")
        for role in stored.INPUT_ROLES:
            for target in stored.inputs_of(self.view.get(ref), role):
                self._attempt(target)
                if not self.view.holds(target) or self.retraction_in_force(target):
                    raise DependencyNotHeld(f"calibration input not held: {target}")
        value = run_value(self.view, ref)
        self.runs[ref] = value
        for entry in value.inputs:
            address = dataset_address(entry.dataset)
            if entry.role == "observes" and address is not None:
                self.trace.append(("dataset", address))
        return value

    def verifications_of(self, identity: str) -> tuple[Verification, ...]:
        selected: list[Verification] = []
        for node in self.view.iter_stored():
            if node.kind != "verification":
                continue
            # Membership is relation-first, before decoding unrelated facets.
            targets = [r.target for r in node.relations if r.predicate == stored.VERIFIES]
            if not any(
                (self.view.resolve(ref) or ref) in self.assessments
                and self.assessments[self.view.resolve(ref) or ref].identity() == identity
                for ref in targets
            ):
                continue
            self.verification_ids.add(node.id)
            if self.retraction_in_force(node.id) or not self._accepted(node.id):
                continue
            self._attempt(node.id)
            value = stored.verification_value(self.view.get(node.id))
            if value.assessment == identity:
                self.verifications[value.ref] = value
                self.trace.append(("verification", value.ref))
                selected.append(value)
        return tuple(selected)

    def eligibility(self, id: str) -> ClosureEligibility:
        try:
            return closure_eligibility(
                (id,),
                self,
                self.profile,
                assessments=self.assessment_eligibility,
                assessment_dependency=lambda ref: stored.frozen_assessment_dependency(
                    ref, records=self, profile=self.profile
                ),
            )
        except MalformedRecord as exc:
            return ClosureEligibility({id: Ineligible("malformed-record", (str(exc),))}, tuple(sorted(self.reads)))

    def evidence(self, assessments: tuple[AssessmentValue, ...]) -> DependencyEvidence:
        frozen = tuple(sorted({d.id: d for a in assessments for d in a.dependencies}.values(), key=lambda d: d.id))
        verdicts = {d.id: self.eligibility(d.id).verdicts[d.id] for d in frozen}
        for assessment in assessments:
            try:
                actual = dependency_closure(
                    (d.id for d in assessment.dependencies),
                    self,
                    self.profile,
                    assessment_dependency=lambda ref: stored.frozen_assessment_dependency(
                        ref, records=self, profile=self.profile
                    ),
                )
                if actual != assessment.dependencies:
                    for dependency in assessment.dependencies:
                        verdicts[dependency.id] = Ineligible("frozen-dependency-mismatch")
            except (DependencyNotHeld, DependencyCycle, MalformedRecord):
                pass  # closure eligibility records the failed traversal
        records: dict[str, Record] = {}
        for id in tuple(sorted(self.reads)):
            if (
                id.partition(":")[0]
                in {"procedure", "referent-mapping", "proxy-model", "classification-rule", "assumptions-register"}
                and self.view.holds(id)
                and self._accepted(id)
            ):
                try:
                    records[id] = read_record(self, id)
                except MalformedRecord as exc:
                    verdicts[id] = Ineligible("malformed-record", (str(exc),))
        return DependencyEvidence(
            ClosureEligibility(verdicts, tuple(sorted(self.reads))), records, self.assessments, self.runs
        )

    def _proxies(self) -> tuple[tuple[str, ProxyModel], ...]:
        proxies: list[tuple[str, ProxyModel]] = []
        for node in self.view.iter_stored():
            if node.kind != "proxy-model" or not self._accepted(node.id) or self.retraction_in_force(node.id):
                continue
            try:
                proxies.append((node.id, proxy_from_stored(self.view.get(node.id))))
            except MalformedRecord as exc:
                raise _InputRefused(f"malformed-input: {node.id}: {exc}") from exc
        return tuple(proxies)

    def crosswalks(self, a: str, b: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                id
                for id, proxy in self._proxies()
                if {proxy.source.procedure, proxy.target.scale_of} == {a, b} and proxy.crosswalk is not None
            )
        )

    def observable_proxies(self, a: Observable, b: Observable) -> tuple[str, ...]:
        return tuple(
            sorted(
                id
                for id, proxy in self._proxies()
                if proxy.target.observable is not None
                and (
                    (proxy.source.observable == a and proxy.target.observable == b)
                    or (proxy.source.observable == b and proxy.target.observable == a)
                )
            )
        )


@dataclass(frozen=True)
class PairVerdict:
    left: str
    right: str
    convertibility: ConversionVerdict
    synthesis: SynthesisVerdict


@dataclass(frozen=True)
class ClaimView:
    proposition: str
    snapshot: str | None
    beliefs: Mapping[str, Belief | NoBelief | Refused]
    pairs: tuple[PairVerdict, ...]
    claim_answer: NoBelief | Refused | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "beliefs", MappingProxyType(dict(self.beliefs)))


_EvaluationTrace: TypeAlias = tuple[Belief | NoBelief | Refused, Admission, EvaluationInputs | None]


@dataclass(frozen=True)
class _ClaimEvaluation:
    view: ClaimView
    traces: Mapping[str, _EvaluationTrace]
    claim_trace: _EvaluationTrace | None
    acceptance: AcceptanceContext | None


def _evaluate_claim(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
    acceptance: AcceptancePolicy | None = None,
) -> _ClaimEvaluation:
    selection = _AcceptanceSelection(acceptance)
    snapshot_identity: str | None = None

    def failure(answer: NoBelief | Refused) -> _ClaimEvaluation:
        answer = replace(answer, acceptance=selection.report)
        return _ClaimEvaluation(
            ClaimView(proposition, snapshot_identity, {}, (), answer),
            {},
            (answer, NotReached(), None),
            selection.report,
        )

    if not isinstance(binding, PolicyBinding):
        return failure(Refused(f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair"))
    try:
        discovery = _discover(view, proposition, context=context, binding=binding, profile=profile, selection=selection)
        snapshot_identity = _capture_identity(discovery, context, selection, availability.observations)
        keys = sorted({a.key() for a in discovery.assessments})
        traces: dict[str, _EvaluationTrace] = {}
        for key in keys or [""]:
            try:
                inputs = _gather(
                    discovery,
                    proposition,
                    key=key,
                    context=context,
                    profile=profile,
                    resolution=resolution,
                    binding=binding,
                    selection=selection,
                    observations=availability.observations,
                )
            except InputOutsideCorpus as exc:
                traces[key] = Refused(f"input-outside-corpus: {exc}", acceptance=selection.report), NotReached(), None
                continue
            except _InputRefused as exc:
                traces[key] = Refused(str(exc), acceptance=selection.report), NotReached(), None
                continue
            if inputs.absent:
                corpora = ", ".join(sorted({id for _, id in inputs.absent}))
                return failure(
                    NoBelief("unavailable-corpus-absent", detail=f"inputs recorded in absent corpora: {corpora}")
                )
            selected_context = replace(
                context, node_corpus=inputs.node_corpus, snapshot=inputs.snapshot, acceptance=inputs.acceptance
            )
            answer, admission = evaluate_traced(
                proposition=proposition,
                key=key,
                dependencies=inputs.dependencies,
                records=inputs.records(),
                availability=availability,
                context=selected_context,
                retractions=inputs.retractions,
                binding=binding,
                profile=profile,
            )
            traces[key] = answer, admission, inputs
        if not keys:
            answer, admission, inputs = traces[""]
            assert isinstance(answer, (NoBelief, Refused))
            return _ClaimEvaluation(
                ClaimView(proposition, snapshot_identity, {}, (), answer),
                {},
                (answer, admission, inputs),
                selection.report,
            )
        pairs: list[PairVerdict] = []
        comparison_records = _CapturedComparisonRecords(discovery, selection, profile, availability.observations)
        comparison = ComparabilitySnapshot(profile, comparison_records, comparison_records.eligibility)
        for left, right in itertools.combinations(keys, 2):
            a_inputs, b_inputs = traces[left][2], traces[right][2]
            if a_inputs is None or b_inputs is None:
                unknown = TargetUnknown("keyed inputs unavailable", snapshot_identity)
                pairs.append(PairVerdict(left, right, unknown, unknown))
                continue
            if any(
                isinstance(verdict, Ineligible)
                for inputs in (a_inputs, b_inputs)
                for verdict in inputs.dependencies.closure.verdicts.values()
            ):
                unknown = TargetUnknown("keyed dependencies ineligible", snapshot_identity)
                pairs.append(PairVerdict(left, right, unknown, unknown))
                continue
            a, b = a_inputs.assessments[0], b_inputs.assessments[0]
            if a_inputs.claim is None or b_inputs.claim is None:
                conversion = TargetUnknown("claim referents unavailable", snapshot_identity)
                combined = conversion
            else:
                first = AssessedProposition(a_inputs.claim, a.target, a.interpretation_rule)
                second = AssessedProposition(b_inputs.claim, b.target, b.interpretation_rule)
                try:
                    conversion = convertibility(
                        first, second, profile=profile, snapshot=comparison, snapshot_identity=snapshot_identity
                    )
                    combined = synthesis(
                        first,
                        second,
                        profile=profile,
                        snapshot=comparison,
                        snapshot_identity=snapshot_identity,
                        observable_proxies=comparison_records.observable_proxies,
                    )
                except (AmbiguousCrosswalk, _InputRefused) as exc:
                    conversion = TargetUnknown(str(exc), snapshot_identity)
                    combined = conversion
            pairs.append(PairVerdict(left, right, conversion, combined))
        return _ClaimEvaluation(
            ClaimView(proposition, snapshot_identity, {key: traces[key][0] for key in keys}, tuple(pairs), None),
            MappingProxyType(traces),
            None,
            selection.report,
        )
    except ContractDisagreement as exc:
        return failure(Refused(f"consulted-contracts-disagree: {exc}"))
    except (ContractMismatch, FacetUndeclared, _DiscoveryRefused) as exc:
        return failure(Refused(str(exc)))
    except FacetPayloadRefused as exc:
        return failure(Refused(f"facet-payload-refused: {exc}"))
    except InputOutsideCorpus as exc:
        return failure(Refused(f"input-outside-corpus: {exc}"))


def claim_view(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
    acceptance: AcceptancePolicy | None = None,
) -> ClaimView:
    """Evaluate each assessed key once, then compare pairs without pooling them."""
    return _evaluate_claim(
        view,
        proposition,
        availability=availability,
        context=context,
        profile=profile,
        resolution=resolution,
        binding=binding,
        acceptance=acceptance,
    ).view


def _evaluate_over_inputs(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
    acceptance: AcceptancePolicy | None = None,
) -> _EvaluationTrace:
    result = _evaluate_claim(
        view,
        proposition,
        availability=availability,
        context=context,
        profile=profile,
        resolution=resolution,
        binding=binding,
        acceptance=acceptance,
    )
    if result.claim_trace is not None:
        return result.claim_trace
    if len(result.traces) == 1:
        return next(iter(result.traces.values()))
    return Refused("multiple-assessed-propositions: use claim_view", acceptance=result.acceptance), NotReached(), None


def evaluate_over_traced(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
    acceptance: AcceptancePolicy | None = None,
) -> tuple[Belief | NoBelief | Refused, Admission]:
    """Return the answer and its single traced admission."""
    answer, admission, _inputs = _evaluate_over_inputs(
        view,
        proposition,
        availability=availability,
        context=context,
        profile=profile,
        resolution=resolution,
        binding=binding,
        acceptance=acceptance,
    )
    return answer, admission


def evaluate_over(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
    acceptance: AcceptancePolicy | None = None,
) -> Belief | NoBelief | Refused:
    """`evaluate`'s step-1 guard first, then `gather`, then `evaluate` — the
    first projection of `evaluate_over_traced`."""
    return evaluate_over_traced(
        view,
        proposition,
        availability=availability,
        context=context,
        profile=profile,
        resolution=resolution,
        binding=binding,
        acceptance=acceptance,
    )[0]
