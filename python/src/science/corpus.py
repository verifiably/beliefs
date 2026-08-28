"""The write API and the read side — the one module that holds a mutable corpus.

**S8's capability boundary is what this module's shape is for.** A `Corpus`
structurally satisfies any read-only `Protocol` despite carrying mutation
methods, so a protocol is not a capability boundary. What is one is a concrete
facade: `ReadView` holds its `Corpus` privately and exposes exactly the read
surface — `get`, one-hop `outbound`/`inbound`, and member iteration. Every module
outside this one receives a `ReadView`, and no mutable `Corpus` is constructed or
received anywhere else. That claim is checkable by AST, which is the point: a
roster of trusted writers has a hole by construction, and a new writer reaching
the filesystem through an unrecognized primitive is simply never discovered.

**Stale-hash validation lives on the facade's node-read path.** Every fetch —
`get`, and every node a traversal resolves — recomputes the semantic hash from
the stored fields and refuses a disagreement. Iteration is deliberately *not* a
fetch: the corpus check reads through it and must **report** what it finds
rather than raise, and a check that could not survive reaching a stale node
would report nothing about the corpus beyond it.

**A live `Corpus` indexes at construction, so a raw filesystem write is
invisible to it.** Every fixture that writes bytes behind the API reconstructs a
fresh facade before asserting read behaviour — reconstruction from disk is the
recovery posture the seam names, and it is the read this slice actually runs.

**Traversal is corpus-local throughout.** A walk truncates at the corpus edge;
reaching a target the holding corpus does not carry is the world index's, which
this slice does not build.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Literal, final

from nodes.core.corpus import Corpus
from nodes.core.errors import CollisionError, ExecutionError
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.structural_index import Index, ResolvedEdge
from nodes.core.write_plan import CreateOp, WritePlanExecutor
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import PydanticSerializationError
from yaml import YAMLError

from science import boundary as boundary_values
from science import report as report_values
from science import stored
from science.consulted import CorpusPins
from science.dataset import dataset_address
from science.errors import (
    BasisMissing,
    BuildContended,
    BuildHold,
    BundleMemberHeld,
    CollisionRefused,
    EligibilityUnmet,
    FamilyKindUnsupported,
    IdentityError,
    ImportRefused,
    LoneSurrogate,
    MalformedRecord,
    ManifestAlreadyPresent,
    ManifestMalformed,
    RecordAlreadyMinted,
    RetractionCycleMalformed,
    RetractionGroundsMissing,
    RetractionTargetIneligible,
    RetractionTargetUnresolvable,
    ReviseKindImmutable,
    ReviseOutsideAllowlist,
    RevisionTargetMissing,
    ScienceError,
    SemanticHashMissing,
    SemanticHashStale,
    SupersedeIdentityUnchanged,
    SupersedeTargetMissing,
    ValidationRefused,
    WriteRefused,
)
from science.identity import v1
from science.lineage import Basis, LineageSnapshot, Producer, Route
from science.record import RunInput, RunValue
from science.report import OperationIntent
from science.runrecord import OperationPort
from science.sealed import sealed
from science.spec import BITWISE_EQUIVALENCE_RULES
from science.traversal import LineageEntry, Reach, RelationEntry, Step, closure

if TYPE_CHECKING:
    from science.world import CorpusManifest

__all__ = [
    "DIRECTIONS",
    "ELIGIBLE_RETRACTION_TARGET_KINDS",
    "CorpusWriter",
    "Finding",
    "LineageAdjacency",
    "OperationLock",
    "OperationPort",
    "ReadView",
    "RelationAdjacency",
    "corpus_check",
    "derived_from",
    "lineage_snapshot",
    "run_value",
    "standing_in_local_view",
    "superseded_by",
]

DIRECTIONS = ("inbound", "outbound")
ELIGIBLE_RETRACTION_TARGET_KINDS = ("assessment", "retraction", "verification")


@sealed
@final
@dataclass(frozen=True)
class Finding:
    """`nodes`' finding envelope, under a Science-owned code namespace.

    The envelope is reused and the codes are not: `nodes`' seven structural
    codes cannot express a cross-node predicate, and a kind invariant surfaces
    there as `invariant-violated` with an empty detail. `message` is
    human-facing and normative for nothing — never used for ordering, never
    compared for parity.
    """

    severity: str
    code: str
    ref: str
    detail: str
    message: str

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.ref, self.code, self.detail)


class ReadView:
    """The read-only facade. Concrete, not a protocol — see the module docstring."""

    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    @classmethod
    def opened_at(cls, root: Path) -> ReadView:
        """Open a corpus root for reading alone. The mutable handle this builds
        never leaves the facade, which is what makes a read-only opener safe to
        hand to any module."""
        return cls(Corpus(Path(root)))

    # --- resolution ---------------------------------------------------------

    def resolve(self, ref: str) -> str | None:
        """The live id a ref names — through a deprecated id as `nodes`
        resolves one — or `None` when the corpus holds no such node."""
        uid = self._corpus.index.resolve_uid(ref)
        return None if uid is None else self._corpus.index.by_uid[uid].id

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    # --- fetching -----------------------------------------------------------

    def get(self, ref: str) -> Node:
        """Fetch one node, refusing a stale semantic hash (`semantic-hash-stale`)
        and an unstamped governed kind (`semantic-hash-missing`).

        The stale refusal is S3's read-side check; the missing refusal is the
        2026-08-18 review's strengthening — a governed kind is minted stamped
        without exception, so omission is statically detectable. What neither
        can see is an edit that moved the fields **and** the stamp together:
        the store compares a state against itself and has no record of what
        preceded it — substrate §4.3's bound, inherited here rather than
        papered over.
        """
        return self._validated(self._corpus.get(ref))

    def outbound(self, ref: str) -> list[ResolvedEdge]:
        return self._corpus.outbound(ref)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        return self._corpus.inbound(ref)

    def iter_stored(self) -> Iterator[Node]:
        """Every stored node, **unvalidated**. The corpus check's read: a
        reporting check that raised at the first stale node would report one
        finding and hide every other."""
        yield from self._corpus.all()

    def live_id(self, uid: str) -> str:
        return self._corpus.index.by_uid[uid].id

    @staticmethod
    def _validated(node: Node) -> Node:
        if stored.semantic_hash_missing(node):
            raise SemanticHashMissing(
                f"{node.id}: a {node.kind!r} carries no semantic-identity stamp "
                "(semantic-hash-missing); the boundary mints every governed record stamped, "
                "so an unstamped one is a raw write that skipped even self-stamping"
            )
        if stored.semantic_hash_disagrees(node):
            raise SemanticHashStale(
                f"{node.id}: the stored semantic hash disagrees with the fields it covers "
                "(semantic-hash-stale); the node is an untrusted import, not a guaranteed mutation"
            )
        return node


@final
class OperationLock:
    """The per-root operation lock, held either by a corpus writer or by an
    epoch build's coherent capture.

    One `threading.Condition` carries the whole state: which kind of holder has
    it, if any, and a capture generation that only ever counts up. Writers
    cooperate exactly as the bare lock made them — a writer behind a writer
    queues — but a capture is neither something to queue behind nor something
    that queues:

    - a capture arriving to any holder raises `BuildContended` at once. A build
      that waits on a corpus operation is a build that can park the whole
      writer queue behind itself, so it never waits.
    - a writer that sees a `capture` on arrival raises `BuildHold`, and so does
      a writer that wakes from the queue to find the generation moved. It never
      waits again after observing that capture.

    The generation is what makes the second refusal decidable at all: a woken
    writer cannot see a capture that has already released, only the count it
    left behind. A writer that already holds the lock is untouched by it — the
    snapshot and its comparison exist only on the not-yet-acquired path.

    All of this is in-process. Single-writer deployment across processes stays
    a stated obligation; no file lock here would make it otherwise.
    """

    __slots__ = ("_capture_generation", "_condition", "_holder")

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._holder: Literal["writer", "capture"] | None = None
        self._capture_generation = 0

    def __enter__(self) -> OperationLock:
        """Take it as a writer, queueing behind another writer but never
        behind — or across — a capture."""
        with self._condition:
            if self._holder == "capture":
                raise BuildHold(
                    "a corpus operation cannot proceed: an epoch build holds this root's "
                    "coherent capture (build-hold)"
                )
            snapshot = self._capture_generation
            while self._holder is not None:
                self._condition.wait()
                if self._holder == "capture" or self._capture_generation != snapshot:
                    raise BuildHold(
                        "a corpus operation cannot proceed: an epoch build's coherent capture "
                        "ran while it waited for this root's operation lock (build-hold)"
                    )
            self._holder = "writer"
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Release a writer's hold, refusing to release anyone else's.

        The bare `threading.Lock` this replaced raised on an unbalanced
        release, and losing that would be a regression: a writer's `__exit__`
        clearing a *capture's* hold is precisely the corruption the capture
        exists to prevent, and it would leave two holders believing they had
        the root. Only the pairing is checked, because only the pairing can be
        got wrong from outside.
        """
        with self._condition:
            if self._holder != "writer":
                raise RuntimeError(
                    f"operation lock released as a writer while held as {self._holder!r}: "
                    "an unbalanced release, not a state this lock can repair"
                )
            self._holder = None
            self._condition.notify_all()

    @contextmanager
    def capture(self) -> Iterator[None]:
        """Take it for one coherent capture, or refuse. This never waits.

        The release below carries no pairing guard, because there is no pairing
        to get wrong: it is inside this generator, reachable only past a `yield`
        that only a successful acquisition reaches. Guarding it would raise from
        a `finally` and mask whatever the build was already failing on.
        """
        with self._condition:
            if self._holder is not None:
                raise BuildContended(
                    f"an epoch build cannot capture this root: its operation lock is held as "
                    f"{self._holder!r} (build-contended); the build refuses rather than queue"
                )
            self._holder = "capture"
            self._capture_generation += 1
        try:
            yield
        finally:
            with self._condition:
                self._holder = None
                self._condition.notify_all()


@dataclass
class _RootState:
    lock: OperationLock
    corpus: Corpus
    view: ReadView
    executor_factory: Callable[[Path], WritePlanExecutor]


class _ImportView:
    """The arriving bundle overlaid on the current local read view."""

    def __init__(self, local: ReadView, records: Sequence[Node], index: Index) -> None:
        self._local = local
        self._records = {record.uid: record for record in records}
        self._index = index

    def resolve(self, ref: str) -> str | None:
        uid = self._index.resolve_uid(ref)
        return None if uid is None else self._index.by_uid[uid].id

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    def get(self, ref: str) -> Node:
        uid = self._index.resolve_uid(ref)
        if uid in self._records:
            return self._records[uid]
        return self._local.get(ref)

    def iter_stored(self) -> Iterator[Node]:
        yield from self._local.iter_stored()
        yield from self._records.values()


_ROOT_STATES: dict[str, _RootState] = {}
_OPERATION_LOCKS: dict[str, OperationLock] = {}
_ROOT_STATES_LOCK = threading.Lock()
"""One mutex over both registries, which is what keeps them one registry.

The lock a root's writers take and the lock an auditor takes must be the same
object or they serialize nothing, so the two entry points below hand out
entries of the same per-root map and `_root_state_for` takes its lock from it
rather than minting one of its own.
"""


def _locked_operation_lock(key: str) -> OperationLock:
    """The per-root lock, with `_ROOT_STATES_LOCK` already held."""
    lock = _OPERATION_LOCKS.get(key)
    if lock is None:
        lock = OperationLock()
        _OPERATION_LOCKS[key] = lock
    return lock


def _operation_lock_for(root: Path) -> OperationLock:
    """One root's operation lock, constructing no `Corpus`.

    Verification locks roots it does not open. `_root_state_for` cannot serve
    it: that entry point builds a `Corpus`, which reads and validates every
    node under the root — so on exactly the damaged root an audit exists to
    judge, asking for the lock would raise before the audit could say what was
    wrong. The lock is per-root state, not corpus state, so it is handed out
    without one.
    """
    with _ROOT_STATES_LOCK:
        return _locked_operation_lock(str(Path(root).resolve()))


def _root_state_for(root: Path, executor_factory: Callable[[Path], WritePlanExecutor]) -> _RootState:
    resolved = Path(root).resolve()
    key = str(resolved)
    with _ROOT_STATES_LOCK:
        state = _ROOT_STATES.get(key)
        if state is None:
            lock = _locked_operation_lock(key)
            corpus = Corpus(resolved, executor_factory=executor_factory)
            state = _RootState(lock, corpus, ReadView(corpus), executor_factory)
            _ROOT_STATES[key] = state
        elif state.executor_factory is not executor_factory:
            raise ScienceError(f"corpus root {key!r} is already open with a different executor factory")
        return state


# --- the two adjacency adapters ---------------------------------------------


class RelationAdjacency:
    """Stored relations under one predicate, in one direction.

    `directed` is **not reinterpreted**: an undirected relation is reached from
    its stored source and not from its stored target, exactly as it is stored.
    Reading it both ways would invent an edge the author did not write, and the
    fixture that pins this is why the flag is read at all.
    """

    def __init__(self, view: ReadView, predicate: str, direction: str) -> None:
        if direction not in DIRECTIONS:
            raise ValueError(f"direction {direction!r} is outside {DIRECTIONS}")
        self._view = view
        self._predicate = predicate
        self._direction = direction

    def steps(self, ref: str) -> tuple[Step, ...]:
        if self._direction == "outbound":
            return self._outbound(ref)
        return self._inbound(ref)

    def _outbound(self, ref: str) -> tuple[Step, ...]:
        node = self._view.get(ref)
        steps: list[Step] = []
        for position, relation in enumerate(node.relations):
            if relation.predicate != self._predicate or relation.source != node.id:
                continue
            steps.append(
                Step(
                    stored=relation.target,
                    resolved=self._view.resolve(relation.target),
                    entry=RelationEntry(
                        source=node.id,
                        position=position,
                        predicate=relation.predicate,
                        target=relation.target,
                    ),
                )
            )
        return tuple(steps)

    def _inbound(self, ref: str) -> tuple[Step, ...]:
        steps: list[Step] = []
        for edge in self._view.inbound(ref):
            if edge.relation.predicate != self._predicate or edge.source_uid is None:
                continue
            source_id = self._view.live_id(edge.source_uid)
            source = self._view.get(source_id)
            position = next(
                (index for index, relation in enumerate(source.relations) if relation == edge.relation),
                0,
            )
            steps.append(
                Step(
                    stored=source_id,
                    resolved=source_id,
                    entry=RelationEntry(
                        source=source_id,
                        position=position,
                        predicate=edge.relation.predicate,
                        target=edge.relation.target,
                    ),
                )
            )
        return tuple(steps)


class LineageAdjacency:
    """The stamped lineage basis, walked as a facet.

    **No predicate and no direction argument**, and that is a claim rather than
    an omission: a lineage step has neither, so a relation adapter's clauses are
    category errors here. What it can express that the relation adapter cannot
    is the difference between an unresolvable **ancestor** and an unresolvable
    **producing run** — the route's two positions, both resolution-checked,
    only one of them an edge of the closure.
    """

    def __init__(self, view: ReadView) -> None:
        self._view = view

    def steps(self, ref: str) -> tuple[Step, ...]:
        node = self._view.get(ref)
        steps: list[Step] = []
        for index, route in enumerate(stored.basis_routes(node)):
            run = route.get("run")
            if isinstance(run, str):
                steps.append(
                    Step(
                        stored=run,
                        resolved=self._view.resolve(run),
                        entry=LineageEntry(dataset=node.id, route=index, position="run", target=run),
                        # Checked, never followed: a producing run is not an
                        # ancestor, and walking into it would put runs in a
                        # dataset closure.
                        follow=False,
                    )
                )
            ancestor = route.get("ancestor")
            if isinstance(ancestor, str):
                steps.append(
                    Step(
                        stored=ancestor,
                        resolved=self._view.resolve(ancestor),
                        entry=LineageEntry(dataset=node.id, route=index, position="ancestor", target=ancestor),
                    )
                )
        return tuple(steps)


# --- the walks the arms run over ---------------------------------------------


def derived_from(view: ReadView, dataset: str) -> Reach:
    """`derived_from` as a **view** over `produces ∘ transforms`, walked out of
    the store — stored nowhere, and no API accepts an authored ancestry list.

    One step: the runs whose `produces` edge names this dataset, and what each
    of those runs `transforms`. Independence does not read this view — it walks
    the stamped basis — and the two are allowed to disagree, which is the
    disagreement R23's fixture constructs.
    """
    return closure(dataset, _DerivedFromAdjacency(view))


def superseded_by(view: ReadView, ref: str) -> tuple[str, ...]:
    """The sorted, transitive successors derived from inbound `supersedes` edges."""
    return closure(ref, RelationAdjacency(view, stored.SUPERSEDES, "inbound")).reached


def standing_in_local_view(view: ReadView, ref: str) -> bool:
    """Whether `ref` has no standing node-arm retraction in this corpus.

    This is deliberately non-authoritative and corpus-local. Route-arm targets
    name an embedded route, not a record, so they never subtract node standing.
    """
    targets: dict[str, list[str]] = {}
    for stored_node in view.iter_stored():
        if stored_node.kind != "retraction":
            continue
        retraction = view.get(stored_node.id)
        target = CorpusWriter._validated_retraction(retraction)["target"]
        CorpusWriter._resolve_retraction_target(retraction, view)
        if target["arm"] != "node":
            continue
        resolved = view.resolve(target["ref"])
        if resolved is not None:
            targets.setdefault(resolved, []).append(retraction.id)

    graph = {target: tuple(sorted(retractions)) for target, retractions in targets.items()}
    standing: dict[str, bool] = {}
    for target in _acyclic_postorder(graph):
        standing[target] = not any(standing[retraction] for retraction in graph.get(target, ()))
    return standing.get(view.resolve(ref) or ref, True)


def _acyclic_postorder(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Return child-first order, refusing cycles with iterative DFS."""
    state: dict[str, int] = {}
    ordered: list[str] = []
    vertices = sorted(set(graph).union(retraction for retractions in graph.values() for retraction in retractions))
    for start in vertices:
        if state.get(start) is not None:
            continue
        state[start] = 1
        stack = [(start, iter(graph.get(start, ())))]
        while stack:
            target, successors = stack[-1]
            try:
                successor = next(successors)
            except StopIteration:
                state[target] = 2
                ordered.append(target)
                stack.pop()
                continue
            if state.get(successor) == 1:
                raise RetractionCycleMalformed(
                    f"retraction graph contains a cycle through {target!r} -> {successor!r}"
                )
            if state.get(successor) is None:
                state[successor] = 1
                stack.append((successor, iter(graph.get(successor, ()))))
    return tuple(ordered)


def _cycle_edges(graph: dict[str, tuple[str, ...]]) -> tuple[tuple[str, str], ...]:
    """Return one deterministic directed cycle, or the empty tuple."""
    state: dict[str, int] = {}
    parent: dict[str, str] = {}
    vertices = sorted(set(graph).union(child for children in graph.values() for child in children))
    for start in vertices:
        if start in state:
            continue
        state[start] = 1
        stack = [(start, iter(graph.get(start, ())))]
        while stack:
            node, children = stack[-1]
            try:
                child = next(children)
            except StopIteration:
                state[node] = 2
                stack.pop()
                continue
            if state.get(child) == 1:
                path = [node]
                while path[-1] != child:
                    path.append(parent[path[-1]])
                path.reverse()
                return tuple(sorted((*pairwise(path), (node, child))))
            if child not in state:
                parent[child] = node
                state[child] = 1
                stack.append((child, iter(graph.get(child, ()))))
    return ()


def _validated_retraction_facet(record: Node) -> dict:
    facet = record.facets.get(stored.RETRACTION_FACET)
    required = {"target", "reason", "rationale", "grounds", "actor", "event_token"}
    if not isinstance(facet, dict) or set(facet) not in (required, required | {"successor"}):
        raise MalformedRecord(f"{record.id}: malformed retraction facet")
    _validated_retraction_target(record)
    if type(facet["reason"]) is not str or facet["reason"] not in stored.RETRACTION_REASONS:
        raise MalformedRecord(f"{record.id}: malformed retraction reason")
    if type(facet["rationale"]) is not str or not facet["rationale"]:
        raise MalformedRecord(f"{record.id}: malformed retraction rationale")
    if type(facet["actor"]) is not str or not facet["actor"]:
        raise MalformedRecord(f"{record.id}: malformed retraction actor")
    if type(facet["event_token"]) is not str or not facet["event_token"]:
        raise MalformedRecord(f"{record.id}: malformed retraction event token")
    grounds = facet["grounds"]
    if (
        not isinstance(grounds, list)
        or not grounds
        or not all(type(ground) is str and ground for ground in grounds)
    ):
        raise MalformedRecord(f"{record.id}: malformed retraction grounds")
    successor = facet.get("successor")
    if successor is not None and (type(successor) is not str or not successor):
        raise MalformedRecord(f"{record.id}: malformed retraction successor")
    return facet


def _validated_retraction_target(record: Node) -> dict:
    facet = record.facets.get(stored.RETRACTION_FACET)
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{record.id}: malformed retraction facet")
    target = facet.get("target")
    if not isinstance(target, dict) or target.get("arm") not in ("node", "route"):
        raise MalformedRecord(f"{record.id}: malformed retraction target arm")
    target_fields = (
        {"arm", "ref", "resolved", "content_identity"}
        if target["arm"] == "node"
        else {"arm", "dataset", "resolved", "content_identity", "route_identity"}
    )
    if set(target) != target_fields or not all(type(target[field]) is str and target[field] for field in target):
        raise MalformedRecord(f"{record.id}: malformed retraction target")
    return target


class _DerivedFromAdjacency:
    def __init__(self, view: ReadView) -> None:
        self._view = view

    def steps(self, ref: str) -> tuple[Step, ...]:
        steps: list[Step] = []
        for producer in RelationAdjacency(self._view, stored.PRODUCES, "inbound").steps(ref):
            if producer.resolved is None:
                continue
            steps.extend(RelationAdjacency(self._view, stored.TRANSFORMS, "outbound").steps(producer.resolved))
        return tuple(steps)


def run_value(view: ReadView, ref: str) -> RunValue:
    """A stored run as cut 2's value: its spec, and its role-partitioned inputs
    with each input dataset's declaration read from the dataset itself.

    **Corpus-local**: an input naming a dataset this corpus does not hold is not
    in the value, because its declaration lives wherever that dataset does and
    resolving an address to the corpus holding it is the world index's job. A
    walk truncating at the corpus edge is this layer's documented property.
    """
    node = view.get(ref)
    inputs = tuple(
        RunInput(role=role, dataset=stored.dataset_declaration(view.get(target)))
        for role in stored.INPUT_ROLES
        for target in stored.inputs_of(node, role)
        if view.holds(target)
    )
    return RunValue(ref=ref, spec=stored.run_spec(node) or "", inputs=inputs)


def lineage_snapshot(view: ReadView, roots: Sequence[str]) -> LineageSnapshot:
    """Produce substrate §5's snapshot from a store, corpus-locally.

    The inspected set is `{observed root} ∪ closure` — the union written out,
    because the walk is start-excluding and a root whose own immediate parent is
    gone must still be inspected. Nothing here decides anything: `certify` reads
    the tags, the resolutions and the producer sets this assembles.
    """
    adjacency = LineageAdjacency(view)
    inspected: list[str] = []
    for root in roots:
        for dataset in (root, *closure(root, adjacency).reached):
            if dataset not in inspected:
                inspected.append(dataset)

    bases: dict[str, Basis] = {}
    producers: dict[str, tuple[Producer, ...]] = {}
    for dataset in inspected:
        if not view.holds(dataset):
            continue
        node = view.get(dataset)
        routes = tuple(
            Route(
                dataset=dataset,
                stored_run=str(route.get("run", "")),
                resolved_run=view.resolve(str(route.get("run", ""))),
                stored_ancestor=str(route.get("ancestor", "")),
                resolved_ancestor=view.resolve(str(route.get("ancestor", ""))),
                transforms=tuple(str(entry) for entry in route.get("transforms", []) or ()),
            )
            for route in stored.basis_routes(node)
        )
        facet = stored.lineage_basis(node)
        if facet is not None and routes:
            bases[dataset] = Basis(tag=str(facet.get("tag", "single")), routes=routes)
        producers[dataset] = tuple(_producers_of(view, dataset))
    return LineageSnapshot(roots=tuple(roots), bases=bases, producers=producers)


def _producers_of(view: ReadView, dataset: str) -> list[Producer]:
    """The runs holding a `produces` edge to `dataset`, with what each of them
    `transforms`. The producer set is the divergence test's input; the basis
    route is what it is compared against, and the two are separate reads on
    purpose — a build that derived one from the other could not disagree."""
    producers: list[Producer] = []
    for edge in view.inbound(dataset):
        if edge.relation.predicate != stored.PRODUCES:
            continue
        run_ref = edge.relation.source
        resolved = view.resolve(run_ref)
        transforms = () if resolved is None else stored.inputs_of(view.get(resolved), stored.TRANSFORMS)
        producers.append(Producer(stored_run=run_ref, resolved_run=resolved, transforms=transforms))
    return producers


# --- the §6.2 corpus check ---------------------------------------------------


def eligibility_refusal(view: ReadView | _ImportView, node: Node) -> str | None:
    """S7's cross-node predicate, in one implementation for both boundaries.

    assessment → run → `observes` → dataset → facet. `reads` inputs never
    confer eligibility, in any quantity, and no clause of this reaches the
    registry compile: the kinds are the kernel's and the facet is the `science`
    base profile's own.

    Returns the reason the `assesses` edge is inadmissible, or `None`.
    """
    if not any(relation.predicate == stored.ASSESSES for relation in node.relations):
        return None
    facet = node.facets.get(stored.ASSESSMENT_FACET)
    run_ref = facet.get("run") if isinstance(facet, dict) else None
    if not isinstance(run_ref, str) or not run_ref:
        return "the assessment names no run"
    if not view.holds(run_ref):
        return f"the run {run_ref!r} resolves to no node in this corpus"
    run = view.get(run_ref)
    observed = stored.inputs_of(run, stored.OBSERVES)
    if not observed:
        return f"the run {run_ref!r} has no observes input; reads inputs never confer eligibility"
    for dataset_ref in observed:
        if view.holds(dataset_ref) and stored.is_empirical_observation(view.get(dataset_ref)):
            return None
    return f"no observes input of {run_ref!r} carries the empirical-observation facet"


def corpus_check(view: ReadView) -> tuple[Finding, ...]:
    """The profile-level check (substrate §6.2 item 2), reported and never raised.

    Files are canonical and hand-editable, so a node can reach the store without
    passing the write boundary. What this reports is what such a node can be
    caught by: stamp faults, unsupported `assesses` edges, and the corpus-local
    family faults this module can resolve. What it is silent on is a raw write
    that is **self-consistent** — the hash agrees because the writer computed
    it, and nothing structural is wrong because nothing is. That silence is
    §4.2.1's stated bound, not a gap here.
    """
    findings: list[Finding] = []
    manifest_path = view._corpus.store.root / "corpus.yaml"
    if manifest_path.exists():
        from science.world import load_manifest

        try:
            load_manifest(view._corpus.store.root)
        except ManifestMalformed as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="manifest-malformed",
                    ref="corpus.yaml",
                    detail=str(refused),
                    message=str(refused),
                )
            )
    retraction_targets: dict[str, list[str]] = {}
    for node in view.iter_stored():
        base_valid = True
        if stored.semantic_hash_missing(node):
            base_valid = False
            findings.append(
                Finding(
                    severity="error",
                    code="semantic-hash-missing",
                    ref=node.id,
                    detail="unstamped",
                    message=f"{node.id}: a {node.kind!r} carries no semantic-identity stamp",
                )
            )
        try:
            if stored.semantic_hash_disagrees(node):
                base_valid = False
                findings.append(
                    Finding(
                        severity="error",
                        code="semantic-hash-stale",
                        ref=node.id,
                        detail="mismatch",
                        message=f"{node.id}: the stored semantic hash disagrees with the fields it covers",
                    )
                )
        except (IdentityError, MalformedRecord) as refused:
            base_valid = False
            findings.append(
                Finding(
                    severity="error",
                    code="semantic-hash-stale",
                    ref=node.id,
                    detail="unencodable",
                    message=f"{node.id}: the covered fields do not encode, so no hash can be recomputed: {refused}",
                )
            )
        if not base_valid:
            continue
        if stored.display_facet_malformed(node):
            findings.append(
                Finding(
                    severity="error",
                    code="display-malformed",
                    ref=node.id,
                    detail="display",
                    message=f"{node.id}: the display facet is not its exact one-field shape",
                )
            )
        for relation in node.relations:
            if relation.predicate == stored.SUPERSEDES and not view.holds(relation.target):
                findings.append(
                    Finding(
                        severity="error",
                        code="supersession-target-missing",
                        ref=node.id,
                        detail=relation.target,
                        message=f"{node.id}: supersedes target {relation.target!r} does not resolve locally",
                    )
                )
        if node.kind == "retraction":
            try:
                target = CorpusWriter._validated_retraction(node)["target"]
                CorpusWriter._resolve_retraction_target(node, view)
            except ScienceError as refused:
                findings.append(
                    Finding(
                        severity="error",
                        code="retraction-target-invalid",
                        ref=node.id,
                        detail="target",
                        message=str(refused),
                    )
                )
            else:
                if target["arm"] == "node":
                    resolved = view.resolve(target["ref"])
                    assert resolved is not None
                    retraction_targets.setdefault(resolved, []).append(node.id)
        try:
            reason = eligibility_refusal(view, node)
        except (IdentityError, SemanticHashMissing, SemanticHashStale):
            reason = None
        if reason is not None:
            for relation in node.relations:
                if relation.predicate == stored.ASSESSES:
                    findings.append(
                        Finding(
                            severity="error",
                            code="eligibility-unmet",
                            ref=node.id,
                            detail=relation.target,
                            message=f"{node.id}: assesses {relation.target!r} but {reason}",
                        )
                    )
    graph = {target: tuple(sorted(retractions)) for target, retractions in retraction_targets.items()}
    try:
        _acyclic_postorder(graph)
    except RetractionCycleMalformed as refused:
        findings.append(
            Finding(
                severity="error",
                code="retraction-cycle",
                ref="corpus",
                detail=str(refused),
                message=str(refused),
            )
        )
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))


class CorpusWriter:
    """The write API — the sole constructor and holder of a mutable `Corpus`.

    Its public surface is `add` plus the explicit supersede, revise, retract,
    and import families. What this package decides — basis, eligibility,
    collisions, stored shape, and family invariants — refuses in Science's
    vocabulary as a `WriteRefused`; what the executor layer decides — plan
    validity, engine refusal, halt — crosses the boundary as the seam's
    `PlanRefusedError` and `ExecutionError`. A third vocabulary wrapping those
    two would add a layer with no added discrimination.

    **Every mutation is serialized end to end under a per-root operation lock** —
    read, refuse, plan, execute. The refusals read corpus state before the
    engine lease exists, and only some of those reads are safe under concurrency:
    the **monotone** predicates (W3, S7) cannot be invalidated by another
    admitted mutation, because nothing removes a basis or an `observes` edge, but the
    **collision** predicates can — two planners can each pass `assert_addable`
    for one uid under different ids, plan creates at two different paths, and
    both no-clobber effects succeed. `CreateFileNoClobber` backstops only the
    same-path race. So the ruling is a single-planner restriction: in-process it
    is this lock, and cross-process it is a **stated deployment obligation**
    whose violation is detected loudly rather than prevented — strict
    construction refuses the duplicate uid with `CollisionError`.

    A future deletion-capable family must re-own this question; neither argument
    transfers to it.
    """

    def __init__(
        self,
        root: Path,
        executor_factory: Callable[[Path], WritePlanExecutor],
        operation_port: OperationPort | None = None,
    ) -> None:
        self._state = _root_state_for(root, executor_factory)
        self._operation = self._state.lock
        self._operation_port = operation_port

    @property
    def _corpus(self) -> Corpus:
        return self._state.corpus

    @property
    def _view(self) -> ReadView:
        return self._state.view

    @property
    def read_view(self) -> ReadView:
        """The facade every other module receives. The mutable handle stays
        here."""
        return self._view

    def add(self, node: Node) -> Node:
        """Mint one record, returning it as `nodes` mints it.

        A write against an unregistered root surfaces as the executor's
        `ExecutionError(index=None, applied=0)` with the engine's registration
        refusal as cause — init is an explicit act, not a fallback this
        performs.
        """
        with self._operation:
            self._refuse_family_kinds(node)
            self._refuse(node)
            return self._corpus.add(node)

    def adopt_manifest(self, *, profile: CorpusPins) -> CorpusManifest:
        """Create this corpus's first closed manifest."""
        from science.world import CorpusManifest, _parse_manifest, manifest_bytes

        with self._operation:
            manifest_path = self._corpus.store.root / "corpus.yaml"
            if manifest_path.exists() or manifest_path.is_symlink():
                raise ManifestAlreadyPresent(f"{manifest_path}: manifest already present")
            checked_profile = _parse_manifest(
                {
                    "manifest_version": 2,
                    "corpus_id": "0" * 32,
                    "profile": {
                        "science_contract": profile.science_contract,
                        "domains": dict(profile.domains),
                    },
                }
            ).profile
            manifest = CorpusManifest(2, secrets.token_hex(16), checked_profile)
            self._state.executor_factory(self._corpus.store.root).execute(
                [CreateOp("corpus.yaml", manifest_bytes(manifest))]
            )
            return manifest

    def import_bundle(
        self,
        records: Sequence[Node],
        *,
        actor: str,
        observer: str,
        instrument: str,
        opened_at: str,
        closed_at: str,
    ) -> report_values.ActReport:
        """Admit one validated bundle in one payload transaction."""
        with self._operation:
            try:
                bundle = tuple(records)
            except TypeError as caught:
                raise ImportRefused("an import bundle must be a sequence of records") from caught
            if not bundle:
                raise ImportRefused("an import bundle must not be empty")
            for name, value in (
                ("actor", actor),
                ("observer", observer),
                ("instrument", instrument),
                ("opened_at", opened_at),
                ("closed_at", closed_at),
            ):
                if type(value) is not str or not value:
                    raise ImportRefused(f"import {name} must be a non-empty string")
            try:
                v1.encode(
                    {
                        "actor": actor,
                        "observer": observer,
                        "instrument": instrument,
                        "opened_at": opened_at,
                        "closed_at": closed_at,
                        "subject": self._corpus.store.root.name,
                    }
                )
            except LoneSurrogate as caught:
                raise ImportRefused(f"import report fields are not canonically encodable: {caught}") from caught
            if self._operation_port is None:
                raise ImportRefused("this corpus has no operation port; import is a boundary operation")

            intent = OperationIntent("import", secrets.token_hex(16), actor)
            intent_digest = self._operation_port.append_intent(
                v1.encode({"kind": intent.kind, "event_token": intent.event_token, "actor": intent.actor})
            )
            if (
                type(intent_digest) is not str
                or len(intent_digest) != 64
                or any(character not in "0123456789abcdef" for character in intent_digest)
            ):
                raise ExecutionError(
                    "operation port returned a malformed intent digest; expected 64 lowercase hexadecimal characters",
                    index=None,
                    applied=0,
                )
            try:
                findings, payload = self._validate_import_bundle(bundle)
                report = self._import_report(
                    intent,
                    observer=observer,
                    instrument=instrument,
                    opened_at=opened_at,
                    closed_at=closed_at,
                    refs=tuple(record.id for record in bundle),
                    findings=findings,
                )
                try:
                    report_op = self._validated_import_op(stored.act_report_node(report))
                except MalformedRecord as caught:
                    raise ImportRefused("import success report is not canonically storable") from caught
            except ScienceError as caught:
                refused = caught if isinstance(caught, ImportRefused) else ImportRefused(str(caught))
                finding = str(refused).encode("utf-8", "backslashreplace").decode("utf-8")
                report = self._import_report(
                    intent,
                    observer=observer,
                    instrument=instrument,
                    opened_at=opened_at,
                    closed_at=closed_at,
                    refs=(),
                    findings=(finding,),
                )
                report_node = stored.act_report_node(report)
                self._operation_port.execute_fulfilling([self._create_op(report_node)], intent_digest)
                self._reconstruct()
                refused.report_ref = report_node.id
                if refused is caught:
                    raise
                raise refused from caught

            self._corpus.executor.execute(payload)
            self._reconstruct()
            self._operation_port.execute_fulfilling([report_op], intent_digest)
            self._reconstruct()
            return report

    def retract(self, record: Node) -> Node:
        """Mint one locally resolvable retraction without touching its target."""
        with self._operation:
            try:
                self._validated_retraction(record)
            except MalformedRecord as caught:
                facet = record.facets.get(stored.RETRACTION_FACET)
                if isinstance(facet, dict):
                    grounds = facet.get("grounds")
                    if "grounds" not in facet or (
                        isinstance(grounds, list)
                        and (
                            not grounds
                            or all(type(ground) is str and not ground for ground in grounds)
                        )
                    ):
                        raise RetractionGroundsMissing(
                            f"{record.id}: a retraction names at least one grounds reference"
                        ) from caught
                raise ValidationRefused(f"{record.id}: refused by retraction shape validation: {caught}") from caught
            self._resolve_retraction_target(record, self._view)

            self._refuse(record, document_validated=True)
            return self._corpus.add(record)

    def supersede(self, successor: Node, *, of: str) -> Node:
        """Mint a proposition successor without touching its predecessor."""
        with self._operation:
            predecessor_id = self._view.resolve(of)
            if predecessor_id is None:
                raise SupersedeTargetMissing(f"{of!r}: predecessor does not resolve locally")
            predecessor = self._view.get(predecessor_id)
            if predecessor.kind != "proposition" or successor.kind != "proposition":
                raise FamilyKindUnsupported("supersede operates on propositions only")
            self._refuse_already_minted(successor)
            self._refuse_malformed_supersede_successor(successor)
            if any(relation.predicate == stored.SUPERSEDES for relation in successor.relations):
                raise ValidationRefused(f"{successor.id}: supersedes relations are authored by the adapter")
            try:
                successor_identity = stored.recompute_semantic_hash(successor)
            except IdentityError as caught:
                raise ValidationRefused(f"{successor.id}: refused by document validation: {caught}") from caught
            if successor_identity == stored.recompute_semantic_hash(predecessor):
                raise SupersedeIdentityUnchanged(
                    f"{successor.id}: successor semantic identity is unchanged; use revise instead"
                )
            candidate = successor.model_copy(
                update={
                    "relations": [
                        *successor.relations,
                        Relation(source=successor.id, predicate=stored.SUPERSEDES, target=predecessor_id),
                    ]
                }
            )
            self._refuse(candidate)
            return self._corpus.add(candidate)

    def revise(self, node: Node) -> Node:
        """Replace a proposition after changing display prose alone."""
        with self._operation:
            self._refuse_invalid(node)
            if not all(isinstance(relation, Relation) for relation in node.relations):
                raise ValidationRefused(f"{node.id}: refused by document validation: malformed relation")
            existing = self._corpus.index.by_uid.get(node.uid)
            if existing is None or existing.id != node.id:
                raise RevisionTargetMissing(f"{node.id}: exact uid and id do not identify a local node")
            current = self._view.get(node.id)
            if current.kind != "proposition" or node.kind != "proposition":
                raise ReviseKindImmutable("revise operates on propositions only")
            if stored.display_facet_malformed(node):
                raise ValidationRefused(f"{node.id}: refused by document validation: malformed display facet")
            try:
                candidate_digest = stored.recompute_semantic_hash(node)
            except IdentityError as caught:
                raise ValidationRefused(f"{node.id}: refused by document validation: {caught}") from caught
            if candidate_digest != stored.recompute_semantic_hash(current):
                raise ReviseOutsideAllowlist(f"{node.id}: semantic fields require supersede")

            candidate_fields = node.model_dump()
            current_fields = current.model_dump()
            for fields in (candidate_fields, current_fields):
                fields.pop("title")
                fields.pop("body")
                fields["facets"].pop(stored.DISPLAY_FACET, None)
            if candidate_fields != current_fields:
                raise ReviseOutsideAllowlist(f"{node.id}: revision changes a field outside display prose")
            self._refuse_rendering(node)
            return self._corpus.add(node)

    def _validate_import_bundle(self, records: tuple[Node, ...]) -> tuple[tuple[str, ...], list[CreateOp]]:
        seen_ids: set[str] = set()
        seen_uids: set[str] = set()
        seen_paths: set[str] = set()
        for record in records:
            if type(record) is not Node:
                raise ImportRefused("an import member must be a Node")
            try:
                self._refuse_invalid(record)
                path = self._relative_path(record)
                self._refuse_governed_stamp(record)
                covered = stored.COVERED_FACETS.get(record.kind)
                if covered and covered[0] not in record.facets:
                    raise ValidationRefused(f"{record.id}: required {covered[0]!r} facet is missing")
            except ScienceError as caught:
                raise ImportRefused(str(caught), member=record.id) from caught
            seen_deprecated_ids: set[str] = set()
            for deprecated_id in record.deprecated_ids:
                if deprecated_id == record.id:
                    raise ImportRefused(
                        f"{record.id}: identity claim {deprecated_id!r} is both live and deprecated in one member",
                        member=record.id,
                    )
                if deprecated_id in seen_deprecated_ids:
                    raise ImportRefused(
                        f"{record.id}: duplicate deprecated identity claim {deprecated_id!r} in one member",
                        member=record.id,
                    )
                seen_deprecated_ids.add(deprecated_id)
            if record.id in seen_ids:
                raise ImportRefused(f"{record.id}: duplicate id in import bundle", member=record.id)
            if record.uid in seen_uids:
                raise ImportRefused(f"{record.id}: duplicate uid in import bundle", member=record.id)
            if path in seen_paths:
                raise ImportRefused(f"{record.id}: duplicate destination path in import bundle", member=record.id)
            if path in self._corpus.manifest:
                raise BundleMemberHeld(f"{record.id}: destination path is already held", member=record.id)
            seen_ids.add(record.id)
            seen_uids.add(record.uid)
            seen_paths.add(path)

        union_index = Index.build(self._view.iter_stored())
        for record in records:
            try:
                union_index.assert_addable(record)
            except CollisionError as caught:
                raise BundleMemberHeld(str(caught), member=record.id) from caught
            union_index.upsert(record)
        union = _ImportView(self._view, records, union_index)
        for record in records:
            try:
                self._refuse(record, view=union)
                if record.kind == "act-report":
                    self._refuse_malformed_act_report(record)
                self._refuse_r20_contradiction(record)
            except (RecordAlreadyMinted, CollisionRefused) as caught:
                raise BundleMemberHeld(str(caught), member=record.id) from caught
            except ScienceError as caught:
                raise ImportRefused(str(caught), member=record.id) from caught

        for record in records:
            if record.kind == "retraction":
                try:
                    self._validated_retraction(record)
                    self._resolve_retraction_target(record, union)
                except ScienceError as caught:
                    raise ImportRefused(str(caught), member=record.id) from caught

        cycle_edges = self._import_cycle_edges(records)
        if cycle_edges:
            raise ImportRefused(
                f"retraction graph contains a cycle through {cycle_edges!r}",
                cycle_edges=cycle_edges,
            )

        findings = {
            f"unresolved: {record.id} -> {relation.target}"
            for record in records
            for relation in record.relations
            if not union.holds(relation.target)
        }
        payload = [self._validated_import_op(record) for record in records]
        return tuple(sorted(findings)), payload

    def _import_cycle_edges(self, records: tuple[Node, ...]) -> tuple[tuple[str, str], ...]:
        targets: dict[str, list[str]] = {}
        for record in (*tuple(self._view.iter_stored()), *records):
            if record.kind != "retraction":
                continue
            try:
                target = self._validated_retraction(record)["target"]
            except ScienceError as caught:
                raise ImportRefused(str(caught), member=record.id) from caught
            if target["arm"] == "node":
                targets.setdefault(target["resolved"], []).append(record.id)
        graph = {target: tuple(sorted(children)) for target, children in targets.items()}
        return _cycle_edges(graph)

    @staticmethod
    def _resolve_retraction_target(record: Node, view: ReadView | _ImportView) -> None:
        target = _validated_retraction_target(record)
        if target["arm"] == "node":
            if target["resolved"].partition(":")[0] not in ELIGIBLE_RETRACTION_TARGET_KINDS:
                raise RetractionTargetIneligible(
                    f"{record.id}: node target kind is outside {ELIGIBLE_RETRACTION_TARGET_KINDS}"
                )
            resolved = view.resolve(target["ref"])
            if resolved is None or resolved != target["resolved"]:
                raise RetractionTargetUnresolvable(f"{record.id}: node target does not resolve exactly")
            resolved_target = view.get(resolved)
            if resolved_target.kind not in ELIGIBLE_RETRACTION_TARGET_KINDS:
                raise RetractionTargetIneligible(
                    f"{record.id}: resolved node target kind is outside {ELIGIBLE_RETRACTION_TARGET_KINDS}"
                )
            if stored.stored_semantic_hash(resolved_target) != target["content_identity"]:
                raise RetractionTargetUnresolvable(f"{record.id}: node target content identity does not resolve")
            return
        resolved = view.resolve(target["dataset"])
        if target["resolved"].partition(":")[0] != "dataset":
            raise RetractionTargetIneligible(f"{record.id}: a route target must name a dataset")
        if resolved is None or resolved != target["resolved"]:
            raise RetractionTargetUnresolvable(f"{record.id}: route dataset does not resolve exactly")
        dataset = view.get(resolved)
        if dataset.kind != "dataset":
            raise RetractionTargetIneligible(f"{record.id}: a route target must resolve to a dataset")
        if stored.stored_semantic_hash(dataset) != target["content_identity"]:
            raise RetractionTargetUnresolvable(f"{record.id}: route dataset content identity does not resolve")
        if not any(route.get("identity") == target["route_identity"] for route in stored.basis_routes(dataset)):
            raise RetractionTargetUnresolvable(
                f"{record.id}: route identity {target['route_identity']!r} is absent from the stamped basis"
            )

    @staticmethod
    def _refuse_r20_contradiction(record: Node) -> None:
        if record.kind != "analysis-spec":
            return
        facet = record.facets.get("analysis-spec")
        nondeterminism = facet.get("nondeterminism") if isinstance(facet, dict) else None
        equivalence_rule = facet.get("equivalence_rule") if isinstance(facet, dict) else None
        variant = nondeterminism.get("variant") if isinstance(nondeterminism, dict) else None
        if type(equivalence_rule) is not str or type(variant) is not str:
            raise ValidationRefused(f"{record.id}: malformed analysis-spec contract fields")
        if (
            variant == "stochastic-unseeded"
            and equivalence_rule in BITWISE_EQUIVALENCE_RULES
        ):
            raise ValidationRefused(f"{record.id}: stochastic-unseeded cannot support a bitwise equivalence rule")

    @staticmethod
    def _refuse_malformed_act_report(record: Node) -> None:
        try:
            stored.act_report_facet(record)
        except MalformedRecord as caught:
            raise ValidationRefused(str(caught)) from caught

    def _import_report(
        self,
        intent: OperationIntent,
        *,
        observer: str,
        instrument: str,
        opened_at: str,
        closed_at: str,
        refs: tuple[str, ...],
        findings: tuple[str, ...],
    ) -> report_values.ActReport:
        return boundary_values._mint_import_report(  # pyright: ignore[reportPrivateUsage]
            intent,
            subject=self._corpus.store.root.name,
            observer=observer,
            instrument=instrument,
            opened_at=opened_at,
            closed_at=closed_at,
            refs=refs,
            findings=findings,
        )

    def _relative_path(self, record: Node) -> str:
        return self._corpus.store.path_for(record.id).relative_to(self._corpus.store.root).as_posix()

    def _create_op(self, record: Node) -> CreateOp:
        return CreateOp(path=self._relative_path(record), content=node_to_markdown(record).encode("utf-8"))

    def _validated_import_op(self, record: Node) -> CreateOp:
        try:
            content = self._refuse_rendering(record)
        except ValidationRefused as caught:
            raise ImportRefused(str(caught), member=record.id) from caught
        return CreateOp(path=self._relative_path(record), content=content)

    def _reconstruct(self) -> None:
        corpus = Corpus(self._corpus.store.root, executor_factory=self._state.executor_factory)
        self._state.corpus = corpus
        self._state.view = ReadView(corpus)

    # --- the refusals, in order ---------------------------------------------

    @staticmethod
    def _validated_retraction(record: Node) -> dict:
        CorpusWriter._refuse_invalid(record)
        if record.kind != "retraction":
            raise ValidationRefused(f"{record.id}: retract accepts a stored retraction only")
        facet = _validated_retraction_facet(record)
        target = facet["target"]
        successor = facet.get("successor")
        stamp = record.facets.get(stored.SEMANTIC_IDENTITY_FACET)
        if not isinstance(stamp, dict) or set(stamp) != {"digest"} or type(stamp["digest"]) is not str:
            raise ValidationRefused(f"{record.id}: refused by retraction stamp validation")
        try:
            if stored.semantic_hash_missing(record) or stored.semantic_hash_disagrees(record):
                raise ValidationRefused(f"{record.id}: refused by retraction stamp validation")
        except IdentityError as caught:
            raise ValidationRefused(f"{record.id}: refused by retraction stamp validation: {caught}") from caught
        target_value: stored.NodeTarget | stored.RouteTarget
        if target["arm"] == "node":
            target_value = stored.NodeTarget(target["ref"], target["resolved"], target["content_identity"])
        else:
            target_value = stored.RouteTarget(
                target["dataset"],
                target["resolved"],
                target["content_identity"],
                target["route_identity"],
            )
        expected = stored.retraction_node(
            title=record.title,
            target=target_value,
            reason=facet["reason"],
            rationale=facet["rationale"],
            grounds=facet["grounds"],
            actor=facet["actor"],
            event_token=facet["event_token"],
            successor=successor,
        )
        if record.id != expected.id or record.facets != expected.facets or record.relations != expected.relations:
            raise MalformedRecord(f"{record.id}: retraction does not match the controlled stored shape")
        return facet

    @staticmethod
    def _refuse_family_kinds(node: Node) -> None:
        if node.kind == "holdings-observation":
            raise WriteRefused("a holdings observation is minted only by the acts boundary")
        if node.kind == "retraction":
            raise WriteRefused("a retraction enters through retract")
        if node.kind == "act-report":
            raise WriteRefused("an act-report is minted by the boundary and stored by import")

    def _refuse_malformed_supersede_successor(self, successor: Node) -> None:
        if not all(isinstance(relation, Relation) for relation in successor.relations):
            raise ValidationRefused(f"{successor.id}: refused by document validation: malformed relation")
        self._refuse_invalid(successor)

    def _refuse(
        self,
        node: Node,
        *,
        document_validated: bool = False,
        view: ReadView | _ImportView | None = None,
    ) -> None:
        self._refuse_already_minted(node)
        self._refuse_missing_basis(node)
        self._refuse_ineligible(node, view=view)
        if stored.display_facet_malformed(node):
            raise ValidationRefused(f"{node.id}: refused by document validation: malformed display facet")
        if not document_validated:
            self._refuse_invalid(node)
        self._refuse_governed_stamp(node)
        self._refuse_rendering(node)
        self._refuse_collision(node)

    @staticmethod
    def _refuse_governed_stamp(node: Node) -> None:
        if node.kind not in stored.SEMANTIC_DOMAINS:
            if stored.SEMANTIC_IDENTITY_FACET in node.facets:
                raise ValidationRefused(f"{node.id}: kind {node.kind!r} has no semantic-identity domain")
            return
        try:
            if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):
                raise ValidationRefused(f"{node.id}: semantic-identity stamp is missing or stale")
        except IdentityError as caught:
            raise ValidationRefused(f"{node.id}: semantic-identity stamp cannot be recomputed: {caught}") from caught

    @staticmethod
    def _refuse_rendering(node: Node) -> bytes:
        try:
            content = node_to_markdown(node).encode("utf-8")
            reparsed = node_from_markdown(content.decode("utf-8"))
        except (
            NodesValidationError,
            PydanticValidationError,
            PydanticSerializationError,
            YAMLError,
            UnicodeError,
        ) as caught:
            raise ValidationRefused(f"{node.id}: record is not losslessly renderable") from caught
        if reparsed != node:
            raise ValidationRefused(f"{node.id}: record rendering is lossy")
        return content

    def _refuse_already_minted(self, node: Node) -> None:
        """The create-path guard, **before plan construction**: an existing
        `(uid, id)` pair is the pair `nodes`' own `add` would answer with a
        `ReplaceOp`, so ordinary add and create-shaped family members cannot
        silently replace it. Display-only replacement enters through `revise`."""
        existing = self._corpus.index.by_uid.get(node.uid)
        if existing is not None and existing.id == node.id:
            raise RecordAlreadyMinted(
                f"{node.id} is already minted under uid {node.uid}; use revise for a display-only replacement"
            )

    def _refuse_missing_basis(self, node: Node) -> None:
        """W3 as narrowed, over the record being minted and nothing else."""
        if node.kind == "source" and not stored.external_identifiers(node):
            raise BasisMissing(
                f"{node.id}: a source carries an accepted external identifier "
                f"({', '.join(stored.ACCEPTED_EXTERNAL_IDENTIFIERS)}); a curation note is its own explicit add, "
                "and no title-and-year fallback exists"
            )
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:
            raise BasisMissing(
                f"{node.id}: a dataset carries a content identity — every declared resource pinned by an "
                "accepted digest. Supplying it later is a second, separate mint"
            )

    def _refuse_ineligible(self, node: Node, *, view: ReadView | _ImportView | None = None) -> None:
        """S7's write boundary, reading the cross-node predicate through this
        corpus's own read view."""
        reason = eligibility_refusal(self._view if view is None else view, node)
        if reason is not None:
            raise EligibilityUnmet(f"{node.id}: the assesses edge is inadmissible because {reason}")

    @staticmethod
    def _refuse_invalid(node: Node) -> None:
        """`nodes`' document validation, wrapped so no `nodes` exception escapes
        raw. The registry half is unexercised here: no kind registry is compiled
        in this slice, and G5's kind-existence check waits with it."""
        try:
            Node.model_validate(node.model_dump(warnings="error"))
        except (NodesValidationError, PydanticValidationError, PydanticSerializationError) as caught:
            raise ValidationRefused(f"{node.id}: refused by document validation: {caught}") from caught

    def _refuse_collision(self, node: Node) -> None:
        try:
            self._corpus.index.assert_addable(node)
        except CollisionError as caught:
            raise CollisionRefused(str(caught)) from caught
