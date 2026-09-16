"""Composite claims (composite-claims design §3–§5): a declared node set over
propositions whose typed claims form the directed edges of one shape.

The value is built, never authored; its members are corpus refs resolved
through a read view; its nodes are resolved through a `ResolutionSnapshot`
that is a required argument, for the reason `decode_claim`'s is. `classify`
is the one classification the constructor, the write boundary and the audit
share, so the three cannot disagree about what a member contributes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from nodes.core.errors import RefError

from beliefs.claim import Claim, require_identifier
from beliefs.contract.base import COMPOSITE_GRAMMAR
from beliefs.decode import claim_from_stored
from beliefs.errors import ClaimError, CompositeError, DecodeError, MalformedRecord, ProfileError
from beliefs.identity import v1
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import ReferentPosition, ResolutionSnapshot, TermOutcome, build_snapshot
from beliefs.sealed import sealed

COMPOSITE_DOMAIN = "science.composite.v1"
EMPTY_SNAPSHOT = build_snapshot()
"""The consult-nothing snapshot. The boundary and the audit restore member
claims under it (design §4.2 step 1): every referent resolves
`not-consulted`, nothing refuses, and membership is left to the constructor
and the reading, which take a caller's snapshot."""

_MINT = object()


@sealed
@final
@dataclass(frozen=True)
class CompositeNode:
    sort: str
    term: str

    def __post_init__(self) -> None:
        require_identifier(self.sort, "a node's sort")
        require_identifier(self.term, "a node's term")

    def projection(self) -> dict[str, str]:
        return {"sort": self.sort, "term": self.term}


@sealed
@final
@dataclass(frozen=True)
class Edge:
    cause: CompositeNode
    effect: CompositeNode
    sign: str
    member: str


@sealed
@final
@dataclass(frozen=True)
class CompositeFacet:
    grammar: str
    shape: str
    nodes: tuple[CompositeNode, ...]
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.grammar != COMPOSITE_GRAMMAR:
            raise MalformedRecord(f"a composite facet carries grammar {COMPOSITE_GRAMMAR!r}, found {self.grammar!r}")
        if type(self.shape) is not str or not self.shape:
            raise MalformedRecord("a composite's shape is a non-empty tag")
        if type(self.nodes) is not tuple or any(type(n) is not CompositeNode for n in self.nodes):
            raise MalformedRecord("a composite's nodes are CompositeNode values")
        if not self.nodes:
            raise MalformedRecord("a composite declares at least one node")
        if type(self.members) is not tuple or any(type(m) is not str or not m for m in self.members):
            raise MalformedRecord("a composite's members are non-empty claim-identity strings")
        # Types first, order second: sorting a list holding a non-string raises
        # TypeError, which is not a refusal anything downstream translates.
        keys = [(n.sort, n.term) for n in self.nodes]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise MalformedRecord("a composite's nodes are sorted by (sort, term) and distinct; refused, never tidied")
        if list(self.members) != sorted(self.members) or len(set(self.members)) != len(self.members):
            raise MalformedRecord("a composite's members are sorted and distinct; refused, never tidied")

    def projection(self) -> dict[str, object]:
        return {
            "grammar": self.grammar,
            "shape": self.shape,
            "nodes": [n.projection() for n in self.nodes],
            "members": list(self.members),
        }


def composite_identity(facet: CompositeFacet) -> str:
    """The content identity, taken over exactly what `stored.semantic_projection`
    digests for the node `composite_node` writes, so the stamp agrees."""
    return v1.digest(COMPOSITE_DOMAIN, {"kind": "composite", "present": ["composite"], "facets": {"composite": facet.projection()}})


@sealed
@final
@dataclass(frozen=True, init=False)
class Composite:
    facet: CompositeFacet
    refs: tuple[str, ...]
    edges: tuple[Edge, ...]
    slug: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise CompositeError("composite-unbuilt", "Composite is built, never authored — use build_composite(...)")

    @classmethod
    def _checked(cls, token: object, **fields: object) -> Composite:
        if token is not _MINT:
            raise CompositeError("composite-unbuilt", "Composite._checked is build_composite's own route")
        value = object.__new__(cls)
        for name, field in fields.items():
            object.__setattr__(value, name, field)
        return value

    @property
    def identity(self) -> str:
        return composite_identity(self.facet)


@dataclass(frozen=True)
class CompositeReceipt:
    identity: str
    snapshot_identity: str
    outcomes: Mapping[str, TermOutcome]

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcomes", MappingProxyType(dict(self.outcomes)))


def _canonical_nodes(nodes: Iterable[object]) -> tuple[CompositeNode, ...]:
    listed: list[CompositeNode] = []
    for node in nodes:
        if type(node) is not CompositeNode:
            raise CompositeError("composite-node", f"{node!r} is not a CompositeNode")
        listed.append(node)
    if not listed:
        raise CompositeError("composite-nodes-empty", "a composite over no nodes asserts nothing")
    keys = [(n.sort, n.term) for n in listed]
    if len(set(keys)) != len(keys):
        dup = next(k for k in keys if keys.count(k) > 1)
        raise CompositeError("composite-duplicate", f"node {dup} appears twice")
    return tuple(sorted(listed, key=lambda n: (n.sort, n.term)))


def require_node_sorts(profile: ProfileSpec, nodes: Sequence[CompositeNode]) -> None:
    """Every node's sort is one the profile declares — isolated nodes included,
    since no member's claim ever names them and nothing else would look."""
    for index, node in enumerate(nodes):
        if node.sort not in profile.sorts:
            raise CompositeError("composite-node-sort", f"node {index}: {node.sort!r} is not a sort this profile declares")


def classify(profile: ProfileSpec, facet: CompositeFacet, claims: Mapping[str, Claim]) -> tuple[Edge, ...]:
    """§3.4's table for `shape: dag`. `claims` is keyed by member identity and
    must cover every member; a missing key is the caller's defect. The whole
    node-set contract is checked here, because this is the one function the
    constructor, the boundary and the audit share."""
    if facet.shape not in profile.composite_grammar.shapes:
        raise CompositeError("composite-shape", f"{facet.shape!r} is not a shape the base contract declares ({profile.composite_grammar.shapes})")
    require_node_sorts(profile, facet.nodes)
    declared = {(n.sort, n.term): n for n in facet.nodes}
    edges: list[Edge] = []
    for member in facet.members:
        claim = claims[member]
        edge = profile.edges.get(claim.operator)
        if edge is None:
            raise CompositeError("composite-member-undeclared", f"member {member}: operator {claim.operator!r} declares no edge")
        if edge.retired:
            raise CompositeError("composite-member-retired", f"member {member}: the edge declaration for {claim.operator!r} is retired; a retired row types history and admits no new structure (§7.3a)")
        if claim.layer != "causal":
            raise CompositeError("composite-member-layer", f"member {member}: layer {claim.layer!r} forms no edge in a dag; the inhabited fragment is the causal layer")
        # Every argument must be a declared node, not only the two the edge
        # reads: a ternary operator's third slot is part of the claim the
        # composite asserts over these nodes.
        for slot, referent in enumerate(claim.args):
            if (referent.sort, referent.term) not in declared:
                raise CompositeError("composite-member-outside-nodes", f"member {member}: argument {slot} ({referent.sort}, {referent.term}) is not a declared node")
        cause, effect = (declared[(claim.args[slot].sort, claim.args[slot].term)] for slot in (edge.cause, edge.effect))
        edges.append(Edge(cause=cause, effect=effect, sign=claim.polarity, member=member))
    _refuse_cycle(facet.nodes, edges)
    return tuple(edges)


def _refuse_cycle(nodes: Sequence[CompositeNode], edges: Sequence[Edge]) -> None:
    """Every member is an arrow, whatever its sign (§3.4); a cycle through a
    negative edge is a cycle. Depth-first, reporting the first cycle found."""
    out: dict[CompositeNode, list[CompositeNode]] = {n: [] for n in nodes}
    for edge in edges:
        out[edge.cause].append(edge.effect)
    state: dict[CompositeNode, int] = {}
    stack: list[CompositeNode] = []

    def visit(node: CompositeNode) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in out[node]:
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):] + [nxt]
                raise CompositeError("composite-cyclic", "cycle " + " -> ".join(f"({n.sort}, {n.term})" for n in cycle))
            if nxt not in state:
                visit(nxt)
        stack.pop()
        state[node] = 2

    for node in nodes:
        if node not in state:
            visit(node)


def restore_members(view: object, facet_members: Sequence[str], refs: Sequence[str], *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> dict[str, Claim]:
    """Resolve each member ref to a proposition and restore its claim; refuse a
    non-proposition, an unresolvable ref, or an unrestorable claim. Shared by
    the boundary and the audit (`EMPTY_SNAPSHOT`) and by the reading."""
    claims: dict[str, Claim] = {}
    for member, ref in zip(facet_members, refs, strict=True):
        try:
            node = view.get(ref)  # type: ignore[attr-defined]
        except RefError as caught:
            raise CompositeError("composite-member-unresolvable", f"member {ref} does not resolve in this corpus") from caught
        if node.kind != "proposition":
            raise CompositeError("composite-member-kind", f"member {ref} is a {node.kind!r}, not a proposition")
        try:
            claim, _ = claim_from_stored(node, profile=profile, snapshot=snapshot)
        except (DecodeError, ClaimError, ProfileError) as caught:
            # `claim_from_stored` raises all three families: a malformed wire
            # claim, a claim that fails typing (`InadmissibleLayer`, an arity or
            # sort mismatch), an operator no contract declares. None is a
            # `RecordError`, so each is translated here or it escapes the audit.
            raise CompositeError("composite-member-unrestorable", f"member {ref}: {caught}") from caught
        if claim_identity(claim) != member:
            raise CompositeError("composite-member-mismatch", f"member {ref} carries claim {claim_identity(claim)}, the facet names {member}")
        claims[member] = claim
    return claims


def build_composite(
    profile: ProfileSpec,
    view: object,
    *,
    shape: str,
    nodes: Iterable[CompositeNode],
    members: Iterable[str],
    snapshot: ResolutionSnapshot,
    slug: str,
) -> tuple[Composite, CompositeReceipt]:
    if not isinstance(profile, ProfileSpec):
        raise CompositeError("composite-profile", f"profile is a {type(profile).__name__}, not a compiled ProfileSpec")
    if not isinstance(snapshot, ResolutionSnapshot):
        raise CompositeError("composite-snapshot", f"snapshot is a {type(snapshot).__name__}, not a ResolutionSnapshot — use build_snapshot(...); availability is a parameter, never ambient")
    if type(slug) is not str or not slug:
        raise CompositeError("composite-slug", "a composite's local id is a non-empty string")
    canonical_nodes = _canonical_nodes(nodes)
    if shape not in profile.composite_grammar.shapes:
        raise CompositeError("composite-shape", f"{shape!r} is not a shape the base contract declares ({profile.composite_grammar.shapes})")

    refs = list(members)
    if len(set(refs)) != len(refs):
        raise CompositeError("composite-duplicate", "a member ref appears twice")
    # Resolve first under the caller's snapshot: a member whose own referents
    # the snapshot excludes cannot be classified, and says so.
    by_ref: dict[str, Claim] = {}
    for ref in refs:
        try:
            node = view.get(ref)  # type: ignore[attr-defined]
        except RefError as caught:
            raise CompositeError("composite-member-unresolvable", f"member {ref} does not resolve in this corpus") from caught
        if node.kind != "proposition":
            raise CompositeError("composite-member-kind", f"member {ref} is a {node.kind!r}, not a proposition")
        try:
            claim, _ = claim_from_stored(node, profile=profile, snapshot=snapshot)
        except (DecodeError, ClaimError, ProfileError) as caught:
            raise CompositeError("composite-member-unrestorable", f"member {ref}: {caught}") from caught
        by_ref[ref] = claim
    identities = {ref: claim_identity(claim) for ref, claim in by_ref.items()}
    if len(set(identities.values())) != len(identities):
        raise CompositeError("composite-duplicate", "two member refs carry one claim identity")
    ordered_refs = tuple(sorted(refs, key=identities.__getitem__))
    facet = CompositeFacet(
        grammar=COMPOSITE_GRAMMAR,
        shape=shape,
        nodes=canonical_nodes,
        members=tuple(identities[ref] for ref in ordered_refs),
    )

    require_node_sorts(profile, canonical_nodes)
    outcomes: dict[str, TermOutcome] = {}
    for index, node in enumerate(canonical_nodes):
        outcomes[ReferentPosition.node(index).label()] = snapshot.resolve(profile.sorts[node.sort].vocabulary, node.term)
    refused = [label for label, outcome in outcomes.items() if outcome.refuses]
    if refused:
        named = ", ".join(f"{label} ({canonical_nodes[int(label.partition(':')[2])].term})" for label in refused)
        raise CompositeError("composite-node-not-member", f"{named}: the term is not in the vocabulary its sort binds, and the vocabulary was read")

    edges = classify(profile, facet, {identities[ref]: claim for ref, claim in by_ref.items()})
    value = Composite._checked(_MINT, facet=facet, refs=ordered_refs, edges=edges, slug=slug)
    return value, CompositeReceipt(identity=value.identity, snapshot_identity=snapshot.identity, outcomes=outcomes)
