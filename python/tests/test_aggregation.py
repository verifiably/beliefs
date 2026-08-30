"""S6(a)–(g): only certified independence confers multiplicity.

Arm (h) — the weak-D/strong-B regression — is recorded, not run: its own
amended text makes it a named acceptance condition binding the first successor
policy that admits unequal weights, and under v1's unit weight the case cannot
be constructed (cut 2 §4.2). What binds v1 today is P5, below.
"""

import pytest

from beliefs.errors import MalformedRecord
from beliefs.policy import (
    BELIEF_V1,
    BELIEF_V1_FIXTURES,
    AggregationInput,
    DirectionalInput,
    PolicyImplementation,
    aggregate_v1,
    conforms,
)


def graph(signs: dict[str, int], *edges: tuple[str, str]) -> AggregationInput:
    return AggregationInput(
        vertices=tuple(DirectionalInput(assessment=a, sign=s) for a, s in signs.items()),
        edges=edges,
    )


class TestS6TheDependencyGraph:
    def test_a_multiplicity_is_two_not_a_partition_and_not_components(self):
        # A={x}, B={x,y}, C={y}: A–B and B–C share, A–C disjoint.
        assert aggregate_v1(graph({"A": 1, "B": 1, "C": 1}, ("A", "B"), ("B", "C"))) == 2

    def test_b_non_selection_is_not_exclusion(self):
        # B disagrees: not selected, still contests — 2 becomes 1.
        assert aggregate_v1(graph({"A": 1, "B": -1, "C": 1}, ("A", "B"), ("B", "C"))) == 1

    def test_c_adding_a_certified_independent_of_nothing_assessment_cannot_raise(self):
        before = aggregate_v1(graph({"A": 1, "C": 1}))
        universal = graph({"A": 1, "C": 1, "U": 1}, ("U", "A"), ("U", "C"))
        assert aggregate_v1(universal) <= before  # addition only; deletion is §3.2's

    def test_d_the_clique_case(self):
        # Every singleton is maximum; the added vertex may be selected, and
        # displacement still cannot rise.
        clique_before = aggregate_v1(graph({"A": 1, "B": -1}, ("A", "B")))
        clique_after = aggregate_v1(graph({"A": 1, "B": -1, "U": 1}, ("A", "B"), ("A", "U"), ("B", "U")))
        assert abs(clique_after) <= abs(clique_before)

    def test_e_non_amplification_the_value_half(self):
        # Duplicate a dependent contrary assessment N times: the value is
        # identical. (The digest half — the inputs changed — is test_belief's.)
        base = graph({"A": 1, "C": 1, "B": -1}, ("A", "B"), ("B", "C"))
        dupes = graph(
            {"A": 1, "C": 1, "B": -1, "B2": -1, "B3": -1},
            ("A", "B"),
            ("B", "C"),
            ("B", "B2"),
            ("B", "B3"),
            ("B2", "B3"),
            ("A", "B2"),
            ("A", "B3"),
            ("B2", "C"),
            ("B3", "C"),
        )
        assert aggregate_v1(base) == aggregate_v1(dupes)

    def test_f_the_double_contest_tie_does_not_hang_on_a_uid(self):
        # A={x1,x2}, C={y1,y2} vs B={x1,y1}, D={x2,y2}: both candidates land
        # at the prior; renaming every vertex must not change that.
        signs = {"A": 1, "C": 1, "B": -1, "D": -1}
        edges = (("A", "B"), ("A", "D"), ("C", "B"), ("C", "D"))
        assert aggregate_v1(graph(signs, *edges)) == 0
        renamed = {"Z" + k: v for k, v in signs.items()}
        redges = tuple(("Z" + a, "Z" + b) for a, b in edges)
        assert aggregate_v1(graph(renamed, *redges)) == 0

    def test_g_contestation_clamps_at_the_prior(self):
        # {A,B,C} and {D,E,F}: no edge within either triple, every cross pair
        # an edge, so the only maximum selections are the two triples
        # themselves — each mixed (net +1 and -1). Each faces two independent
        # objections (the other side's two opposing vertices, mutually
        # independent), so contestation would cross the prior and is clamped
        # to land exactly at it. Without the clamp both candidates finish at
        # +/-1 and the sorted-uid tie-break would choose the SIGN of the
        # result — the exact defect kernel §4.2.1's reduction exists to
        # prevent.
        crossing = graph(
            {"A": 1, "B": 1, "C": -1, "D": -1, "E": -1, "F": 1},
            ("A", "D"),
            ("A", "E"),
            ("A", "F"),
            ("B", "D"),
            ("B", "E"),
            ("B", "F"),
            ("C", "D"),
            ("C", "E"),
            ("C", "F"),
        )
        assert aggregate_v1(crossing) == 0
        balanced = graph({"A": 1, "B": -1})  # independent, displacement 0
        assert aggregate_v1(balanced) == 0

    def test_independent_objections_are_the_selection_not_only_contestation(self):
        # Two mutually-independent disputes beat one support on cardinality:
        # they ARE the maximum selection (independence is the licence to
        # multiply), and the support contests it once — the value is -1,
        # not a clamped 0 measured from the support's side.
        assert aggregate_v1(graph({"A": 1, "B": -1, "D": -1}, ("A", "B"), ("A", "D"))) == -1


class TestP5UnequalWeightsAreUnspellable:
    def test_no_input_shape_carries_a_magnitude(self):
        # The vertex is (uid, sign) and nothing else; weight has no field.
        import dataclasses

        assert {f.name for f in dataclasses.fields(DirectionalInput)} == {"assessment", "sign"}

    def test_a_zero_sign_is_refused(self):
        with pytest.raises(MalformedRecord):
            DirectionalInput(assessment="A", sign=0)

    def test_the_fixtures_catch_a_weighted_implementation(self):
        # P5's sabotage, run as a live check: an implementation weighting one
        # assessment double fails the fixture set.
        def weighted(problem: AggregationInput) -> int:
            value = aggregate_v1(problem)
            first = min((v.assessment for v in problem.vertices), default=None)
            return value + (
                1 if first is not None and any(v.assessment == first and v.sign > 0 for v in problem.vertices) else 0
            )

        assert not conforms(PolicyImplementation(identity="weighted", aggregate=weighted), BELIEF_V1_FIXTURES)


class TestTheFixtureSetBindsTheReference:
    def test_the_reference_conforms(self):
        assert conforms(BELIEF_V1, BELIEF_V1_FIXTURES)

    def test_every_fixture_case_is_exercised(self):
        # A fixture set with fewer than five cases could not cover selection,
        # contestation, the clamp, the tie and the two-independent-supports
        # case P5's detector needs.
        assert len(BELIEF_V1_FIXTURES) >= 5
