"""Declared scope graphs: one validated, finite relation graph per dimension.

Scope containment design §5. The live (nonretired) scope relations of a profile
are grouped by dimension. Equal endpoints are quotiented into equality classes,
named by a deterministic representative (the least atom); `narrower` relations
become strict edges between representatives. A strict edge inside one equality
class, a strict directed cycle, or equality or a strict path between two classes
of one exact classification rule refuses the profile. The check is finite
reachability over the admitted algebra, not a union solver and not scientific
validation of the authored definitions.

Undirected connected components over the original endpoint atoms are indexed so
a comparison can select exactly the declarations connected to its operands
(design §7.1). This module performs no world reads and imports no profile or
record reader.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from beliefs.contract.scope import CompiledScopeRelation, ScopeEndpoint, TermScopeEndpoint
from beliefs.errors import ProfileError

__all__ = ["ScopeAtom", "ScopeGraph", "compile_scope_graphs", "endpoint_atom"]

ScopeAtom = tuple[str, str, str]
"""``("term", sort, term)`` or ``("rule", rule id, class)``: one leaf scope."""


def endpoint_atom(endpoint: ScopeEndpoint) -> ScopeAtom:
    if isinstance(endpoint, TermScopeEndpoint):
        return ("term", endpoint.sort, endpoint.term)
    return ("rule", endpoint.rule, endpoint.classes[0])


@dataclass(frozen=True)
class ScopeGraph:
    """The validated relation graph of one dimension.

    ``representative`` maps every atom of a live declaration to its equality
    representative; ``above`` maps a representative to the representatives that
    strictly contain it (transitively). ``component`` indexes the undirected
    components of the original atoms and ``component_relations`` lists, per
    component, the sorted qualified terms of every live declaration in it.
    """

    dimension: str
    representative: Mapping[ScopeAtom, ScopeAtom]
    above: Mapping[ScopeAtom, frozenset[ScopeAtom]]
    component: Mapping[ScopeAtom, int]
    component_relations: tuple[tuple[str, ...], ...]

    def rep(self, atom: ScopeAtom) -> ScopeAtom:
        return self.representative.get(atom, atom)

    def strictly_below(self, lower: ScopeAtom, upper: ScopeAtom) -> bool:
        return self.rep(upper) in self.above.get(self.rep(lower), frozenset())

    def context(self, atoms: Iterable[ScopeAtom]) -> tuple[str, ...]:
        """Every live declaration in the components of ``atoms``, sorted; atoms
        absent from the graph contribute nothing."""
        touched = {self.component[atom] for atom in atoms if atom in self.component}
        return tuple(sorted({term for index in touched for term in self.component_relations[index]}))


EMPTY_GRAPH = ScopeGraph("", MappingProxyType({}), MappingProxyType({}), MappingProxyType({}), ())
"""The graph of a dimension no live declaration concerns."""


class _Partition:
    def __init__(self) -> None:
        self.parent: dict[ScopeAtom, ScopeAtom] = {}

    def find(self, atom: ScopeAtom) -> ScopeAtom:
        self.parent.setdefault(atom, atom)
        root = atom
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[atom] != root:
            self.parent[atom], atom = root, self.parent[atom]
        return root

    def join(self, a: ScopeAtom, b: ScopeAtom) -> None:
        first, second = self.find(a), self.find(b)
        if first != second:
            self.parent[max(first, second)] = min(first, second)


def _show(atom: ScopeAtom) -> str:
    return f"{atom[1]} {atom[2]}"


def _compile_dimension(dimension: str, relations: list[CompiledScopeRelation]) -> ScopeGraph:
    atoms = sorted(
        {endpoint_atom(e) for relation in relations for e in (relation.declaration.left, relation.declaration.right)}
    )
    equality = _Partition()
    components = _Partition()
    for atom in atoms:
        equality.find(atom)
        components.find(atom)
    for relation in relations:
        left, right = endpoint_atom(relation.declaration.left), endpoint_atom(relation.declaration.right)
        components.join(left, right)
        if relation.declaration.relation == "equal":
            equality.join(left, right)
    representative = {atom: equality.find(atom) for atom in atoms}

    edges: dict[ScopeAtom, set[ScopeAtom]] = {}
    for relation in relations:
        if relation.declaration.relation != "narrower":
            continue
        lower = representative[endpoint_atom(relation.declaration.left)]
        upper = representative[endpoint_atom(relation.declaration.right)]
        if lower == upper:
            raise ProfileError(
                f"{relation.term}: a strict relation between scopes the active declarations make equal (or a "
                "strict self-edge) contradicts proper containment"
            )
        edges.setdefault(lower, set()).add(upper)

    above: dict[ScopeAtom, frozenset[ScopeAtom]] = {}
    for start in sorted(set(representative.values())):
        reached: set[ScopeAtom] = set()
        pending = sorted(edges.get(start, ()))
        while pending:
            node = pending.pop()
            if node in reached:
                continue
            reached.add(node)
            pending.extend(edges.get(node, ()))
        if start in reached:
            raise ProfileError(f"{dimension}: the active scope relations contain a strict cycle through {_show(start)}")
        if reached:
            above[start] = frozenset(reached)

    by_rule: dict[str, list[ScopeAtom]] = {}
    for atom in atoms:
        if atom[0] == "rule":
            by_rule.setdefault(atom[1], []).append(atom)
    for rule, members in sorted(by_rule.items()):
        for first, second in ((a, b) for i, a in enumerate(members) for b in members[i + 1 :]):
            a, b = representative[first], representative[second]
            if a == b or b in above.get(a, frozenset()) or a in above.get(b, frozenset()):
                raise ProfileError(
                    f"{dimension}: classes {first[2]!r} and {second[2]!r} of the same rule {rule} are made equal or "
                    "nested by the active scope relations; same-rule class sets compare by inclusion, so one rule's "
                    "nested classes need separate rule definitions"
                )

    roots = sorted({components.find(atom) for atom in atoms})
    index = {root: position for position, root in enumerate(roots)}
    component = {atom: index[components.find(atom)] for atom in atoms}
    grouped: list[list[str]] = [[] for _ in roots]
    for relation in relations:
        grouped[component[endpoint_atom(relation.declaration.left)]].append(relation.term)
    return ScopeGraph(
        dimension=dimension,
        representative=MappingProxyType(representative),
        above=MappingProxyType(above),
        component=MappingProxyType(component),
        component_relations=tuple(tuple(sorted(terms)) for terms in grouped),
    )


def compile_scope_graphs(relations: Iterable[CompiledScopeRelation]) -> Mapping[str, ScopeGraph]:
    """Validate the live relations and return the per-dimension graph index.

    Retired declarations contribute no edge and no context; a retired fact cannot
    conflict with its live replacement. Refuses a contradictory profile with
    ``ProfileError`` instead of yielding an arbitrary verdict.
    """
    grouped: dict[str, list[CompiledScopeRelation]] = {}
    for relation in sorted(relations, key=lambda r: r.term):
        if not relation.declaration.retired:
            grouped.setdefault(relation.declaration.dimension, []).append(relation)
    return MappingProxyType(
        {dimension: _compile_dimension(dimension, members) for dimension, members in sorted(grouped.items())}
    )
