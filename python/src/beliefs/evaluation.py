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

One read *does* cross this resolver and is deliberately outside its traced
set, and it is named here rather than left for a reader to discover.
`corpus.run_value` builds a `RunValue` whose inputs carry the dataset
declaration for **every** role — `reads` and `transforms` as well as
`observes` — so a `reads` declaration is handed out inside a run value
without a `("dataset", …)` trace entry. That is not a gap in the
instrumentation but the closure's own shape: the design's `declared_refs`
table admits dataset refs only under `observes`, mirroring `build_closure`'s
`observes` member, and no closure member consumes any other role's
declaration. Tracing one would record a read the digest cannot move for,
which is the mirror of the failure `declared_refs`' exclusions prevent.
`test_a_reads_input_declaration_crosses_gather_untraced` pins both halves:
the untraced hand-out, and the digest that does not move with it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias, cast, final

from nodes.core.node import Node

from beliefs import stored
from beliefs.belief import (
    Admission,
    Availability,
    Belief,
    NoBelief,
    NotReached,
    Records,
    Refused,
    SuppliedContext,
    evaluate_traced,
)
from beliefs.claim import Claim
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, Closure, RetractionEnumeration, build_closure
from beliefs.consulted import consulted_contracts
from beliefs.corpus import ReadView, _absence_of, retraction_standing, run_value
from beliefs.dataset import dataset_address
from beliefs.decode import claim_from_stored
from beliefs.errors import (
    CaptureDrift,
    ContractDisagreement,
    ContractMismatch,
    FacetPayloadRefused,
    FacetUndeclared,
    MalformedRecord,
    ProducerSnapshotMismatch,
    RetractionResolutionDisagreement,
    RetractionUnreadable,
    ScienceError,
)
from beliefs.facet_read import FACET_READ_DOMAIN, FacetRead, read_observed_facets
from beliefs.identity import v1
from beliefs.lineage import LineageSnapshot, absences, retire
from beliefs.policy import PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue, RunValue
from beliefs.resolution import ResolutionSnapshot
from beliefs.sealed import sealed
from beliefs.verification import Verification

if TYPE_CHECKING:
    from beliefs.world.view import WorldReadView

__all__ = ["READ_KINDS", "EvaluationInputs", "ReadRef", "evaluate_over", "evaluate_over_traced", "gather"]

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
    observed_facets: tuple[FacetRead, ...]
    claim: Claim | None
    read_trace: tuple[ReadRef, ...]
    node_corpus: Mapping[str, tuple[str, ...]]
    """Attribution derived at the world read, or supplied for a corpus view."""
    absent: tuple[tuple[str, str], ...] = ()
    """`(ref, corpus_id)` for recorded inputs whose covered corpus has no carrier.
    These are reasons no closure was built, not closure members or declared reads."""

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
            observed_facets=self.observed_facets,
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
    """The one predicate M1's sabotage flips: an unrelated verification read
    through the resolver must fail containment while leaving the digest alone."""
    return value.assessment in ids


def _expected_facet_rows(node: Node, address: str) -> frozenset[tuple[str, str, str]]:
    """The complete facet rows the captured record would mint."""
    return frozenset(
        (address, key, v1.digest(FACET_READ_DOMAIN, node.facets[key])) for key in node.facets if "/" in key
    )


def _facets_held_to_capture(profile: ProfileSpec, view: WorldReadView, target: str) -> tuple[FacetRead, ...]:
    """Read through the holding corpus's exact ReadView, then bind its rows to the capture (§5.3)."""
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


def gather(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
) -> EvaluationInputs:
    """Resolve one proposition's belief inputs from a corpus, tracing each
    value at the moment it is handed out.

    Standing is decided here, before any assessment is read (correction-
    remainder slice 1 §4): the retraction enumeration is the view's — the
    bound epoch's for a world read, the corpus's own fold for a corpus-local
    read — never the caller's; every found retraction is dereferenced and the
    fold recomputed over what it names; a node-arm target of a standing
    retraction is skipped before it is decoded; a route-arm target retires
    its route in the lineage snapshot. Dereferencing a retraction outside the
    closure is a lookup; membership is decided by relation edges.
    """
    from beliefs.corpus import CorpusWriter, local_retraction_enumeration
    from beliefs.world.view import WorldReadView

    world = isinstance(view, WorldReadView)
    if world and context.node_corpus:
        raise MalformedRecord(
            "node_corpus is derived from a world read and must be supplied empty; a caller may not relocate a record"
        )
    if context.snapshot.retired:
        raise MalformedRecord("a supplied lineage snapshot carries no retirement; a caller may not pre-retire a route")
    if world:
        bound = view.producer_snapshot_identity()
        if context.producer_snapshot_identity != bound:
            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)
    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)

    # --- standing, before any assessment is read ------------------------------
    absent: list[tuple[str, str]] = []
    trace: list[ReadRef] = []
    facets: dict[str, Mapping[str, object]] = {}
    for ref, _recorded in enumeration.found:
        corpus_id = _absence_of(view, ref)
        if corpus_id is not None:
            absent.append((ref, corpus_id))
            continue
        try:
            node = view.get(ref)  # a lookup; traced below only if the closure carries it
            facet = CorpusWriter._validated_retraction(node)
            target = cast(Mapping[str, str], facet["target"])
            target_ref = target["ref"] if target["arm"] == "node" else target["dataset"]
            corpus_id = _absence_of(view, target_ref)
            if corpus_id is not None:
                absent.append((target_ref, corpus_id))
                continue
            CorpusWriter._resolve_retraction_target(node, view)  # exact resolution, content identity, route presence
        except ScienceError as caught:
            raise RetractionUnreadable(ref, str(caught)) from caught
        facets[ref] = facet
    if absent:
        return _absent_inputs(proposition, context, enumeration, tuple(sorted(set(absent))), tuple(trace), binding, world)
    standing = retraction_standing(view, facets)
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
        else:
            retired.setdefault(target["resolved"], set()).add(target["route_identity"])

    attribution: dict[str, set[str]] = {}
    matched: list[AssessmentValue] = []
    proposition_refs: list[str] = []
    visited: set[str] = set()  # this proposition's assessment ids, subtracted included (decision 10)
    for node in view.iter_stored():
        if node.kind != "assessment":
            continue
        # beliefs-010c6e: membership by the `assesses` edge, before any decode.
        targets = [r.target for r in node.relations if r.predicate == stored.ASSESSES]
        wanted = view.resolve(proposition) or proposition
        if not any((view.resolve(target) or target) == wanted for target in targets):
            continue  # a lookup, not a value handed out — membership by the edge, never by decoding
        visited.add(node.id)
        if node.id in subtracted:
            continue  # a standing retraction names it: a lookup, never decoded
        value = stored.assessment_value(node, profile=profile)
        if value.proposition != proposition:
            raise MalformedRecord(
                f"{node.id}: the assesses edge names {proposition!r} but the facet names {value.proposition!r}"
            )
        matched.append(value)
        if world:
            corpus_id = view.corpus_of(node.id)
            assert corpus_id is not None  # A served record has a location in this epoch.
            attribution.setdefault(value.identity(), set()).add(corpus_id)
        trace.append(("assessment", value.identity()))
        proposition_refs.extend(targets)
    ids = frozenset(a.identity() for a in matched)

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
            continue
        run_node = view.get(ref)
        runs[a.run] = run_value(view, ref)
        trace.append(("run", a.run))
        if world:
            corpus_id = view.corpus_of(ref)
            assert corpus_id is not None
            attribution.setdefault(ref, set()).add(corpus_id)
        for role in stored.INPUT_ROLES:
            for target in stored.inputs_of(run_node, role):
                if not view.holds(target):
                    corpus_id = _absence_of(view, target)
                    if corpus_id is not None:
                        absent.append((target, corpus_id))
        for target in stored.inputs_of(run_node, stored.OBSERVES):
            if not view.holds(target):
                continue
            address = dataset_address(stored.dataset_declaration(view.get(target)))
            if address is None:
                continue
            trace.append(("dataset", address))
            if world:
                corpus_id = view.corpus_of(target)
                assert corpus_id is not None
                attribution.setdefault(address, set()).add(corpus_id)
            for row in (
                _facets_held_to_capture(profile, view, target) if world else read_observed_facets(profile, view, target)
            ):
                observed[(row.address, row.key, row.payload_digest)] = row
    snapshot = retire(context.snapshot, retired)
    absent.extend((entry.ref, entry.corpus_id) for entry in absences(snapshot))
    rows = tuple(observed[key] for key in sorted(observed))

    verifications: list[Verification] = []
    verification_ids: set[str] = set()
    for node in view.iter_stored():
        if node.kind != "verification":
            continue
        names = {r.target for r in node.relations if r.predicate == stored.VERIFIES}
        if not any(view.resolve(name) in visited for name in names if view.resolve(name) is not None):
            continue  # membership by the `verifies` edge, never by decoding (decision 10)
        verification_ids.add(node.id)
        if node.id in subtracted:
            continue  # the amended G8 clause (§7a): it leaves the read set; `active` recomputes over what remains
        value = stored.verification_value(node)
        if _verification_selected(value, ids):
            verifications.append(value)
            trace.append(("verification", value.ref))

    # --- the closure's enumeration: this proposition's inputs, transitively (decision 10)
    scope = visited | verification_ids | set(snapshot.bases)
    taken: set[str] = set()
    grew = True
    while grew:
        grew = False
        for ref, facet in facets.items():
            if ref in taken:
                continue
            target = cast(Mapping[str, str], facet["target"])
            if target["resolved"] in scope or target["resolved"] in taken:
                taken.add(ref)
                grew = True
    scoped = RetractionEnumeration(
        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),
        coverage=enumeration.coverage,
    )
    trace.extend(("retraction", ref) for ref, _recorded in scoped.found)

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
    observed_addresses = tuple(sorted({row.address for row in rows} | {ref for kind, ref in trace if kind == "dataset"}))
    node_corpus = (
        {node: tuple(sorted(corpora)) for node, corpora in attribution.items()} if world else context.node_corpus
    )
    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        estimands={a.identity(): a.estimand for a in matched},
        profile=profile,
        node_corpus=node_corpus,
        pins=context.pins,
        closure_nodes=tuple(sorted(ids)) + tuple(stored.typed_ref("run", a.run) for a in matched) + observed_addresses,
        facets_read={address: tuple(keys) for address, keys in ledger.items()},
    )
    return EvaluationInputs(
        proposition=proposition,
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
    )

def evaluate_over_traced(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
) -> tuple[Belief | NoBelief | Refused, Admission]:
    """`evaluate`'s step-1 guard first, then `gather`, then `evaluate_traced`,
    carrying the admission the answer rests on (design §6.2).

    The guard runs before anything is read: without it the wrapper would open
    the corpus, or crash projecting `.rule` off a `None` or a string, before
    `evaluate` ever got to refuse — turning a clean refusal into reads and an
    exception. Every answer this wrapper gives itself precedes step 5, so it
    is `NotReached`; only the evaluator's own answer carries a set."""
    if not isinstance(binding, PolicyBinding):
        return Refused(f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair"), NotReached()
    try:
        inputs = gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=binding)
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}"), NotReached()
    except ContractMismatch as exc:
        return Refused(str(exc)), NotReached()
    except FacetPayloadRefused as exc:
        return Refused(f"facet-payload-refused: {exc}"), NotReached()
    except FacetUndeclared as exc:
        return Refused(str(exc)), NotReached()
    if inputs.absent:
        corpora = ", ".join(sorted({corpus_id for _, corpus_id in inputs.absent}))
        return NoBelief("unavailable-corpus-absent", detail=f"inputs recorded in absent corpora: {corpora}"), NotReached()
    context = replace(context, node_corpus=inputs.node_corpus, snapshot=inputs.snapshot)
    return evaluate_traced(
        proposition=proposition,
        records=inputs.records(),
        availability=availability,
        context=context,
        retractions=inputs.retractions,
        binding=binding,
        profile=profile,
    )


def evaluate_over(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
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
    )[0]
