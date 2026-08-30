"""Lineage snapshot values and independence certification (substrate §5, S5).

Consumes a **supplied** snapshot only. The walk that *produces* a snapshot from
a store — resolving refs against `nodes`, following the boundary-minted basis
across a live corpus — is S1a's and the write API's, and stays out of this
module by cut 2 §4.2. What lives here is the pure computation substrate §5
specifies once a snapshot is in hand: the tagged basis, the divergence test,
and the certification procedure over it.

**Orientation and the basis.** `derived_from` is a *view* over a run's
`produces ∘ transforms`, not a stored edge, so what is durable is the
**lineage basis** stamped on the descendant: a producing-run ref and its
resolved ancestor, tagged `single(route)` when the boundary minted it, or
`conflict([route, ...])` — at least two, sorted — when two records at one
content address disagree. `Basis` enforces the tagging at construction: a
`single` holding more than one route, or a `conflict` holding fewer than two
distinct sorted routes, is refused (`MalformedSnapshot`) so that a conflict
that never occurred cannot be spelled (one representation per fact).

**Certification (substrate §5's procedure, condensed to the supplied-snapshot
form).** For each side's roots: the inspected set is `{root} ∪ closure`,
walked through basis routes' resolved ancestors — start-excluding traversal
plus the explicit root, because deleting the root's own immediate parent must
still be seen (§5 step 1). Then, in order: any `conflict` basis in the
inspected set decides `lineage-divergent` on the **tag alone**, before any
resolution or comparison (§5 step 2, short-circuit); any unresolved basis
entry — either resolution `None` — or a cycle decides `lineage-incomplete`
(§5 step 2b); any `single` basis whose producer set holds a `transforms`
divergence from the route decides `lineage-divergent` (§5 step 3, and *only*
against `single` — a conflict has no one route to diverge from, already
decided). Only complete, undiverged, **disjoint** closures certify
`independent`; complete, undiverged, overlapping closures certify
`shared-source`; anything else is `not-certified` — never a synonym for
`shared-source`, which asserts *demonstrated* common ancestry.

**The projection (kernel §5.1).** `snapshot_projection` renders the snapshot
as content the identity contract can digest: roots, basis tuples with the tag
inside, producer sets, and derived divergence states. Every stored ref and its
resolution are recorded **separately** — `{"stored": ref, "resolved": [] |
[uid]}` — because that pair is what makes a deletion visible in the digest:
the stored ref is unchanged, the resolution flips to the empty list, and the
digest moves. Recording either half alone loses the deletion. The identity
contract refuses `None`, so the unresolved half is spelled as an empty list,
never a null.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.errors import BasisTagMismatch, MalformedSnapshot
from beliefs.sealed import sealed

__all__ = [
    "BASIS_TAGS",
    "CERTIFICATION_FINDINGS",
    "CERTIFICATION_STATES",
    "DIVERGENCE_STATES",
    "Basis",
    "Certification",
    "LineageSnapshot",
    "Producer",
    "Route",
    "certify",
    "divergence_state",
    "snapshot_projection",
]

BASIS_TAGS = ("conflict", "single")
CERTIFICATION_FINDINGS = ("lineage-divergent", "lineage-incomplete")
CERTIFICATION_STATES = ("independent", "not-certified", "shared-source")
DIVERGENCE_STATES = ("divergent", "undiverged")


@sealed
@final
@dataclass(frozen=True)
class Route:
    """One basis route: a producing run and the ancestor it names, each as a
    stored ref plus its resolution — `None` when the referent is gone."""

    dataset: str
    stored_run: str
    resolved_run: str | None
    stored_ancestor: str
    resolved_ancestor: str | None
    transforms: tuple[str, ...]


def _route_sort_key(route: Route) -> tuple[object, ...]:
    """A total order over routes for `conflict`'s sortedness check and the
    projection: `None` sorts before every string, at its own field, rather
    than being coerced into one — coercion could make two genuinely different
    routes compare equal."""
    return (
        route.dataset,
        route.stored_run,
        route.resolved_run is None,
        route.resolved_run or "",
        route.stored_ancestor,
        route.resolved_ancestor is None,
        route.resolved_ancestor or "",
        route.transforms,
    )


@sealed
@final
@dataclass(frozen=True)
class Basis:
    """`single` (exactly one route) or `conflict` (at least two, distinct,
    sorted) — anything else is refused at construction, so a conflict that
    never occurred cannot be spelled (substrate §5, sub-problem 4 §5.2)."""

    tag: str
    routes: tuple[Route, ...]

    def __post_init__(self) -> None:
        if not all(isinstance(r, Route) for r in self.routes):
            raise MalformedSnapshot("a basis holds Route values only")
        if self.tag == "single":
            if len(self.routes) != 1:
                raise MalformedSnapshot("a `single` basis holds exactly one route")
        elif self.tag == "conflict":
            if len(self.routes) < 2:
                raise MalformedSnapshot("a `conflict` basis holds at least two routes")
            if len({*self.routes}) != len(self.routes):
                raise MalformedSnapshot("a `conflict` basis holds distinct routes")
            if list(self.routes) != sorted(self.routes, key=_route_sort_key):
                raise MalformedSnapshot("a `conflict` basis holds its routes sorted")
        else:
            raise MalformedSnapshot(f"basis tag {self.tag!r} is outside the closed set {BASIS_TAGS}")


@sealed
@final
@dataclass(frozen=True)
class Producer:
    """One run holding a `produces` edge to a dataset — the input to the
    divergence test, and (with its resolution) a projected producer-set
    member."""

    stored_run: str
    resolved_run: str | None
    transforms: tuple[str, ...]


@sealed
@final
@dataclass(frozen=True)
class LineageSnapshot:
    """The supplied snapshot: observed roots, one basis per dataset that has
    one, and the producer set per dataset. A root absent from `bases` is a
    root whose own basis names nothing — not an error, and not incompleteness
    on its own (§5 step 1 still inspects it)."""

    roots: tuple[str, ...]
    bases: Mapping[str, Basis]
    producers: Mapping[str, tuple[Producer, ...]]

    def __post_init__(self) -> None:
        if not all(isinstance(b, Basis) for b in self.bases.values()):
            raise MalformedSnapshot("a snapshot's bases map holds Basis values only")
        if not all(
            isinstance(entries, tuple) and all(isinstance(p, Producer) for p in entries)
            for entries in self.producers.values()
        ):
            raise MalformedSnapshot("a snapshot's producers map holds tuples of Producer values only")
        object.__setattr__(self, "bases", MappingProxyType(dict(self.bases)))
        object.__setattr__(self, "producers", MappingProxyType(dict(self.producers)))


@sealed
@final
@dataclass(frozen=True)
class Certification:
    state: str
    """`independent` | `shared-source` | `not-certified` — computed, never
    authored, and `not-certified` is never a synonym for `shared-source`."""

    findings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.state not in CERTIFICATION_STATES:
            raise MalformedSnapshot(
                f"certification state {self.state!r} is outside the closed set {CERTIFICATION_STATES}"
            )
        if not all(f in CERTIFICATION_FINDINGS for f in self.findings):
            raise MalformedSnapshot(f"a finding is outside the closed set {CERTIFICATION_FINDINGS}")


def divergence_state(snapshot: LineageSnapshot, dataset: str) -> str:
    """`"divergent"` if any producer's `transforms` differ from the dataset's
    `single` basis route; `"undiverged"` otherwise. A replay — a producer
    whose transforms *equal* the route's — is not divergence.

    Defined **only** against a `single` basis: a `conflict` has no one route
    to diverge from, and that case is decided on the tag alone, before this is
    ever reached for that dataset (certify's traversal short-circuits a
    `conflict` before calling this). An unresolved producer's `transforms` are
    still literal, stored data and participate in the comparison the same as
    a resolved one's — whether the *run* itself still resolves is
    `lineage-incomplete` ground, and that finding belongs to the traversal
    that walks the basis, not to this comparison.

    Raises `BasisTagMismatch` for a `conflict` basis: the snapshot itself is
    well-formed, this is a call outside the domain the comparison is defined
    over, and it stays inside the package's error hierarchy rather than a
    bare `ValueError` — see that class's docstring.
    """
    basis = snapshot.bases[dataset]
    if basis.tag != "single":
        raise BasisTagMismatch(
            f"divergence_state is defined only against a `single` basis; {dataset!r} carries {basis.tag!r}"
        )
    route = basis.routes[0]
    for producer in snapshot.producers.get(dataset, ()):
        if producer.transforms != route.transforms:
            return "divergent"
    return "undiverged"


def _closure(snapshot: LineageSnapshot, root: str) -> tuple[frozenset[str], tuple[str, ...]]:
    """Inspected set and findings for one root: `{root} ∪` transitive
    ancestors through basis routes. Start-excluding traversal plus the
    explicit root — a root whose own parent is gone must still be inspected
    (substrate §5 step 1).

    A `single` basis gives each dataset exactly one route, so one root's walk
    through `single` bases is a single chain: a dataset reached a second time
    within this walk can only mean the chain looped back on itself, which is
    a cycle. (A diamond would need two routes out of one dataset, which
    `single` cannot spell; two different roots meeting at one ancestor is the
    shared-source case, and that is caught by intersecting two *separate*
    closures, not by this one walk repeating a dataset.) So the plain
    "seen twice" check below is exact, and no path-coloring is needed.
    """
    findings: list[str] = []
    inspected: set[str] = set()
    stack = [root]
    while stack:
        dataset = stack.pop()
        if dataset in inspected:
            findings.append("lineage-incomplete")  # a cycle: see the docstring's argument
            continue
        inspected.add(dataset)
        basis = snapshot.bases.get(dataset)
        if basis is None:
            continue  # a root whose basis names nothing
        if basis.tag == "conflict":
            findings.append("lineage-divergent")
            continue  # decided on the tag alone, before resolution or comparison
        for r in basis.routes:
            if r.resolved_run is None or r.resolved_ancestor is None:
                findings.append("lineage-incomplete")
                continue
            stack.append(r.resolved_ancestor)
        if divergence_state(snapshot, dataset) == "divergent":
            findings.append("lineage-divergent")
    return frozenset(inspected), tuple(findings)


def _walk_all(snapshot: LineageSnapshot, roots: tuple[str, ...]) -> tuple[frozenset[str], tuple[str, ...]]:
    """`_closure` unioned over a root tuple: the closure is the union of
    reached sets, and findings are concatenated in root order (deduplicated
    later, order-stable)."""
    closure: frozenset[str] = frozenset()
    findings: list[str] = []
    for root in roots:
        reached, root_findings = _closure(snapshot, root)
        closure |= reached
        findings.extend(root_findings)
    return closure, tuple(findings)


def certify(snapshot: LineageSnapshot, roots_a: tuple[str, ...], roots_b: tuple[str, ...]) -> Certification:
    """Substrate §5's procedure over the supplied snapshot: walk each side's
    roots, and decide in order — conflict (tag alone), then
    incomplete/cycle, then single-basis divergence, folded together per
    dataset by `_closure`; findings are deduplicated order-stably. Only
    complete, undiverged, disjoint closures certify `independent`."""
    closure_a, findings_a = _walk_all(snapshot, roots_a)
    closure_b, findings_b = _walk_all(snapshot, roots_b)
    findings = tuple(dict.fromkeys(findings_a + findings_b))  # dedupe, keep first-seen order
    if findings:
        return Certification(state="not-certified", findings=findings)
    if closure_a & closure_b:
        return Certification(state="shared-source", findings=())
    return Certification(state="independent", findings=())


def _ref_projection(stored: str, resolved: str | None) -> dict[str, object]:
    """`{"stored": ref, "resolved": [] | [uid]}` — the identity encoder
    refuses `None`, and recording either half alone loses a deletion (kernel
    §5.1)."""
    return {"stored": stored, "resolved": [] if resolved is None else [resolved]}


def _route_projection(route: Route) -> dict[str, object]:
    return {
        "dataset": route.dataset,
        "producing_run": _ref_projection(route.stored_run, route.resolved_run),
        "ancestor": _ref_projection(route.stored_ancestor, route.resolved_ancestor),
        "transforms": list(route.transforms),
    }


def _producer_projection(producer: Producer) -> dict[str, object]:
    return {
        "run": _ref_projection(producer.stored_run, producer.resolved_run),
        "transforms": list(producer.transforms),
    }


def snapshot_projection(snapshot: LineageSnapshot) -> dict[str, object]:
    """The kernel §5.1 snapshot components as identity-encodable content:
    sorted roots; every basis, tagged, with each route's stored ref and
    resolution recorded separately; every producer set, the same way, with
    transforms; and the derived divergence state per basis — `"divergent"` on
    the tag alone for a `conflict`, else `divergence_state`'s result.

    Deferred: the producer-snapshot identity member (the covered corpora's
    stable ids) — this cut's `LineageSnapshot` carries no corpus concept to
    project (cut 2 §4.2)."""
    bases = {
        dataset: {"tag": basis.tag, "routes": [_route_projection(r) for r in basis.routes]}
        for dataset, basis in snapshot.bases.items()
    }
    producers = {dataset: [_producer_projection(p) for p in entries] for dataset, entries in snapshot.producers.items()}
    divergence = {
        dataset: "divergent" if basis.tag == "conflict" else divergence_state(snapshot, dataset)
        for dataset, basis in snapshot.bases.items()
    }
    return {
        "roots": sorted(snapshot.roots),
        "bases": bases,
        "producers": producers,
        "divergence": divergence,
    }
