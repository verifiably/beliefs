"""``science.belief.v1`` — the reference aggregation policy.

Belief-policy §2–§3: `V = ℤ`, prior `0`, distance `|a − b|`, unit weight, sum.
The value is a **signed evidence balance** — independent corroboration minus
effective contestation — and must **never be rendered as odds or a
probability** (belief-policy §3.1). Implementations use unbounded integers; a
fixed-width implementation that would overflow must **refuse**, not saturate
(§3.5).

The policy identity binds `aggregate` **end to end**, not a decomposition of
it (§2.1): every step of kernel §4.2.1's algorithm — the independent-set
selection, the contestation reduction, the clamp, the candidate ordering, the
tie-break — is normative, and a change to any of them changes belief. That is
what the fixture set below exists to pin (§2.2), and what P5 (see
`tests/test_aggregation.py`) exercises as a live check: an implementation that
smuggles in a per-assessment weight is a different policy, and must fail these
fixtures even though it is *called* `science.belief.v1`.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from typing import final

from beliefs.errors import MalformedRecord
from beliefs.sealed import sealed

__all__ = [
    "BELIEF_V1",
    "BELIEF_V1_FIXTURES",
    "BELIEF_V1_RULE",
    "AggregationInput",
    "DirectionalInput",
    "FixtureCase",
    "PolicyBinding",
    "PolicyImplementation",
    "aggregate_v1",
    "conforms",
]


@sealed
@final
@dataclass(frozen=True)
class PolicyBinding:
    """`(policy rule identity, implementation content identity)` (belief-policy
    §2.2) — the exact pair a belief computation carries, never the rule alone:
    finite fixtures cannot force two conforming implementations to agree
    outside them, so a derivation names the implementation it actually used."""

    rule: str
    implementation: str

    def __post_init__(self) -> None:
        if not self.rule:
            raise MalformedRecord("a policy binding's rule identity must be a non-empty string")
        if not self.implementation:
            raise MalformedRecord("a policy binding's implementation identity must be a non-empty string")


@sealed
@final
@dataclass(frozen=True)
class DirectionalInput:
    """A vertex of the dependency graph: an assessment uid and its direction.

    `sign` is `+1` or `-1` only. `inconclusive` (`direction = 0`) is not a
    vertex (belief-policy §3.4): a zero-weight vertex would still compete for
    cardinality in a cardinality-first selection, displacing a contributing
    assessment from the winning selection through a channel with no evidential
    content. Weight has no field here — P5 turns on that absence."""

    assessment: str
    sign: int

    def __post_init__(self) -> None:
        if self.sign not in (1, -1):
            raise MalformedRecord(
                f"a directional input's sign must be +1 or -1, got {self.sign!r}; "
                "inconclusive (0) is not a vertex (belief-policy §3.4)"
            )


@sealed
@final
@dataclass(frozen=True)
class AggregationInput:
    """The dependency graph kernel §4.2.1 aggregates over: directional vertices
    and the certified-dependency edges between them. An edge joins every pair
    of assessments *not* certified independent — so its absence is a positive
    claim of independence, not the default state of ignorance."""

    vertices: tuple[DirectionalInput, ...]
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        ids = tuple(v.assessment for v in self.vertices)
        if len(set(ids)) != len(ids):
            raise MalformedRecord("an aggregation input's vertices must have distinct assessment ids")
        known = set(ids)
        for a, b in self.edges:
            if a == b:
                raise MalformedRecord(f"an aggregation input's edges cannot be self-edges, got ({a!r}, {b!r})")
            if a not in known or b not in known:
                raise MalformedRecord(f"an edge endpoint must be a declared vertex id, got ({a!r}, {b!r})")

    def edge_set(self) -> frozenset[frozenset[str]]:
        """Edges normalized to unordered pairs — `("A", "B")` and `("B", "A")`
        are the same certified dependency."""
        return frozenset(frozenset(pair) for pair in self.edges)


def _independent(combo: tuple[str, ...], edges: frozenset[frozenset[str]]) -> bool:
    return not any(frozenset(pair) in edges for pair in itertools.combinations(combo, 2))


def _maximum_selections(ids: tuple[str, ...], edges: frozenset[frozenset[str]]) -> list[tuple[str, ...]]:
    """Every maximum-cardinality independent set. Exact, always — no bound, no
    greedy fallback: a lower bound on cardinality is not a lower bound on
    belief (kernel §4.2.1)."""
    for size in range(len(ids), 0, -1):
        found = [c for c in itertools.combinations(ids, size) if _independent(c, edges)]
        if found:
            return found
    return [()]


def aggregate_v1(problem: AggregationInput) -> int:
    signs = {v.assessment: v.sign for v in problem.vertices}
    ids = tuple(sorted(signs))
    edges = problem.edge_set()
    candidates = _maximum_selections(ids, edges)

    def final(candidate: tuple[str, ...]) -> int:
        value = sum(signs[a] for a in candidate)
        if value == 0:
            return 0  # displacement already zero; contestation does nothing
        direction = 1 if value > 0 else -1
        contrary = tuple(a for a in ids if a not in candidate and signs[a] == -direction)
        if not contrary:
            return value
        # The same exact enumerator over the contrary subgraph. Under unit
        # weight every maximum contrary selection has the same magnitude, so
        # inheriting the outer objective is invisible here — that edge is
        # S6(h), a named acceptance condition binding the first successor
        # policy admitting unequal weights, recorded rather than run.
        magnitude = len(_maximum_selections(contrary, edges)[0])
        return value - direction * min(magnitude, abs(value))  # clamped at the prior

    # Lexicographic: maximum cardinality (already), minimal final displacement,
    # canonical tie-break by sorted member uid. Minimizing displacement rather
    # than the signed value keeps the rule symmetric at both poles.
    chosen = min(candidates, key=lambda c: (abs(final(c)), c))
    return final(chosen)


@sealed
@final
@dataclass(frozen=True)
class FixtureCase:
    """One conformance fixture: a problem and the value the reference policy
    must produce for it."""

    problem: AggregationInput
    expected: int


def _fixture(signs: dict[str, int], edges: tuple[tuple[str, str], ...], expected: int) -> FixtureCase:
    return FixtureCase(
        problem=AggregationInput(
            vertices=tuple(DirectionalInput(assessment=a, sign=s) for a, s in signs.items()),
            edges=edges,
        ),
        expected=expected,
    )


BELIEF_V1_FIXTURES: tuple[FixtureCase, ...] = (
    # Two independent supports: no edge between A and C, so both are
    # selected and the value is 2. P5's detector — a per-assessment weight on
    # either vertex changes this away from the plain count.
    _fixture({"A": 1, "C": 1}, (), 2),
    # A—B—C chain, all supporting: {A, C} is the unique maximum independent
    # set (size 2), B excluded but non-contesting (same sign). Kills a
    # component/partition reading of the graph, which would also give 2 but
    # for the wrong reason — this fixture only distinguishes it from an
    # implementation that stops at the first maximal (not maximum) set.
    _fixture({"A": 1, "B": 1, "C": 1}, (("A", "B"), ("B", "C")), 2),
    # A+, C+ independent of each other; B− adjacent to both. {A, C} is the
    # maximum selection (value 2), B contests as the sole contrary vertex,
    # magnitude 1, clamped toward the prior: 2 - 1 = 1.
    _fixture({"A": 1, "B": -1, "C": 1}, (("A", "B"), ("B", "C")), 1),
    # One support, one adjacent dispute: the clique {A, B} has no independent
    # pair, so both singleton selections tie at |final| = 0 (contestation
    # fully clamps A's value of 1 to 0, and B's selection is symmetric) —
    # pins both the clamp and the candidate tie.
    _fixture({"A": 1, "B": -1}, (("A", "B"),), 0),
    # The double-contest case: A+, C+ independent; B−, D− independent; each
    # of B, D adjacent to both A and C. Both maximum selections ({A, C} and
    # {B, D}) land at the prior after their contrary reduction.
    _fixture(
        {"A": 1, "C": 1, "B": -1, "D": -1},
        (("A", "B"), ("A", "D"), ("C", "B"), ("C", "D")),
        0,
    ),
)


@sealed
@final
@dataclass(frozen=True)
class PolicyImplementation:
    """A named `aggregate` callable — the exact content identity a
    `PolicyBinding` pins (belief-policy §2.2)."""

    identity: str
    aggregate: Callable[[AggregationInput], int]


def conforms(implementation: PolicyImplementation, fixtures: tuple[FixtureCase, ...]) -> bool:
    """Every fixture, exact integer comparison. An implementation that raises
    on a fixture does not conform — a refusal is not a match."""
    for case in fixtures:
        try:
            value = implementation.aggregate(case.problem)
        except Exception:  # noqa: BLE001 — any raise from an arbitrary implementation is non-conformance
            return False
        if value != case.expected:
            return False
    return True


BELIEF_V1_RULE = "science.belief.v1"
BELIEF_V1 = PolicyImplementation(identity="science.belief.v1/reference", aggregate=aggregate_v1)
