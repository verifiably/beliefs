"""S5's selected arms: certification computed from the supplied snapshot.

Deferred and absent here: the walk that *produces* a snapshot from a store
(S1a's and the write API's), and the negative's "indistinguishable from one
where that run never existed" clause, a store property (cut 2 §4.2).
"""

from typing import Any, cast

import pytest

from beliefs.errors import BasisTagMismatch, MalformedSnapshot
from beliefs.lineage import (
    Absence,
    Basis,
    Certification,
    LineageSnapshot,
    Producer,
    Route,
    absences,
    certify,
    divergence_state,
    effective_routes,
    effective_tag,
    retire,
    snapshot_projection,
)


def route(
    dataset: str,
    ancestor: str,
    *,
    resolved: bool = True,
    transforms: tuple[str, ...] = (),
    identity: str | None = None,
) -> Route:
    return Route(
        dataset=dataset,
        stored_run=f"run-{dataset}",
        resolved_run=f"run-{dataset}" if resolved else None,
        stored_ancestor=ancestor,
        resolved_ancestor=ancestor if resolved else None,
        transforms=transforms,
        identity=identity,
    )


class TestTheBasisIsTagged:
    def test_a_single_basis_holds_exactly_one_route(self):
        with pytest.raises(MalformedSnapshot):
            Basis(tag="single", routes=(route("d", "a"), route("d", "b")))

    def test_a_conflict_with_fewer_than_two_distinct_routes_is_unconstructible(self):
        with pytest.raises(MalformedSnapshot):
            Basis(tag="conflict", routes=(route("d", "a"),))


class TestIncompleteNeverCertifies:
    def test_an_unresolved_basis_entry_yields_lineage_incomplete(self):
        snapshot = LineageSnapshot(
            roots=("x", "y"),
            bases={"x": Basis(tag="single", routes=(route("x", "gone", resolved=False),))},
            producers={},
        )
        result = certify(snapshot, ("x",), ("y",))
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings

    def test_the_roots_own_parent_counts(self):
        # Start-excluding traversal plus the explicit root: the closure is
        # empty and the root itself carries the dangling entry.
        snapshot = LineageSnapshot(
            roots=("x",),
            bases={"x": Basis(tag="single", routes=(route("x", "parent", resolved=False),))},
            producers={},
        )
        assert certify(snapshot, ("x",), ("x",)).state == "not-certified"

    def test_a_cycle_is_incomplete(self):
        snapshot = LineageSnapshot(
            roots=("x", "y"),
            bases={
                "x": Basis(tag="single", routes=(route("x", "y"),)),
                "y": Basis(tag="single", routes=(route("y", "x"),)),
            },
            producers={},
        )
        assert certify(snapshot, ("x",), ("y",)).state == "not-certified"


class TestConflictShortCircuits:
    def test_a_conflict_is_divergent_on_the_tag_alone(self):
        snapshot = LineageSnapshot(
            roots=("x", "y"),
            bases={"x": Basis(tag="conflict", routes=(route("x", "a"), route("x", "b")))},
            producers={},
        )
        result = certify(snapshot, ("x",), ("y",))
        assert result.state == "not-certified"
        assert "lineage-divergent" in result.findings


class TestDivergenceStateIsBasisScoped:
    def test_a_conflict_basis_refuses_divergence_state(self):
        # Not in the brief: divergence_state's own domain guard. A conflict
        # has no one route to compare a producer's transforms against, and
        # certify's traversal never reaches this call for a conflict dataset
        # (it short-circuits on the tag first) — call it directly and it
        # must refuse, in the package's error hierarchy.
        snapshot = LineageSnapshot(
            roots=("x",),
            bases={"x": Basis(tag="conflict", routes=(route("x", "a"), route("x", "b")))},
            producers={},
        )
        with pytest.raises(BasisTagMismatch):
            divergence_state(snapshot, "x")


class TestDivergence:
    def test_a_second_producer_with_different_transforms_diverges(self):
        snapshot = LineageSnapshot(
            roots=("x",),
            bases={"x": Basis(tag="single", routes=(route("x", "a", transforms=("t1",)),))},
            producers={"x": (Producer(stored_run="r2", resolved_run="r2", transforms=("t2",)),)},
        )
        assert divergence_state(snapshot, "x") == "divergent"

    def test_the_replay_case_is_not_divergent(self):
        # A second producer whose transforms equal the basis route's is a
        # replay, and independence stays certifiable.
        snapshot = LineageSnapshot(
            roots=("x", "y"),
            bases={"x": Basis(tag="single", routes=(route("x", "a", transforms=("t1",)),))},
            producers={"x": (Producer(stored_run="r2", resolved_run="r2", transforms=("t1",)),)},
        )
        assert divergence_state(snapshot, "x") == "undiverged"
        assert certify(snapshot, ("x",), ("y",)).state != "not-certified"

    def test_a_divergent_producer_absent_from_the_snapshot_restores_the_certificate(self):
        # S5's selected negative half: over supplied snapshots this collapses
        # to purity of the certifier — the store's indistinguishability clause
        # is deferred with the store (cut 2 §4.2).
        divergent = LineageSnapshot(
            roots=("x", "y"),
            bases={"x": Basis(tag="single", routes=(route("x", "a", transforms=("t1",)),))},
            producers={"x": (Producer(stored_run="r2", resolved_run="r2", transforms=("t2",)),)},
        )
        without = LineageSnapshot(roots=("x", "y"), bases=divergent.bases, producers={"x": ()})
        assert certify(divergent, ("x",), ("y",)).state == "not-certified"
        assert certify(without, ("x",), ("y",)).state == "independent"


class TestTheThreeStates:
    def test_disjoint_complete_closures_are_independent(self):
        snapshot = LineageSnapshot(roots=("x", "y"), bases={}, producers={})
        assert certify(snapshot, ("x",), ("y",)) == Certification(state="independent", findings=())

    def test_demonstrated_common_ancestry_is_shared_source(self):
        snapshot = LineageSnapshot(
            roots=("x", "y"),
            bases={
                "x": Basis(tag="single", routes=(route("x", "shared"),)),
                "y": Basis(tag="single", routes=(route("y", "shared"),)),
            },
            producers={},
        )
        assert certify(snapshot, ("x",), ("y",)).state == "shared-source"

    def test_not_certified_is_not_a_synonym_for_shared_source(self):
        incomplete = LineageSnapshot(
            roots=("x", "y"),
            bases={"x": Basis(tag="single", routes=(route("x", "gone", resolved=False),))},
            producers={},
        )
        assert certify(incomplete, ("x",), ("y",)).state == "not-certified"


class TestTheProjectionRecordsBothHalves:
    def test_stored_ref_and_resolution_are_separate(self):
        resolved = LineageSnapshot(
            roots=("x",), bases={"x": Basis(tag="single", routes=(route("x", "a"),))}, producers={}
        )
        deleted = LineageSnapshot(
            roots=("x",),
            bases={"x": Basis(tag="single", routes=(route("x", "a", resolved=False),))},
            producers={},
        )
        # The stored ref is unchanged and the resolution flips: the projection
        # must differ, or a deletion is invisible to the digest (kernel §5.1).
        assert snapshot_projection(resolved) != snapshot_projection(deleted)

    def test_divergence_states_are_in_the_projection(self):
        base = {"x": Basis(tag="single", routes=(route("x", "a", transforms=("t1",)),))}
        quiet = LineageSnapshot(roots=("x",), bases=base, producers={"x": ()})
        loud = LineageSnapshot(
            roots=("x",),
            bases=base,
            producers={"x": (Producer(stored_run="r2", resolved_run="r2", transforms=("t2",)),)},
        )
        assert snapshot_projection(quiet) != snapshot_projection(loud)


class TestAbsenceGatesDivergence:
    def test_an_absent_producer_is_incomplete_never_divergent(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "a", transforms=("a",)),))},
            producers={
                "d": (Producer(stored_run="run:gone", resolved_run=None, transforms=(), absent=("beta",)),)
            },
            not_present={"run:gone": "beta"},
        )
        assert divergence_state(snapshot, "d") == "incomplete"
        result = certify(snapshot, ("d",), ())
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings and "lineage-divergent" not in result.findings
        assert result.absent == (Absence("run:gone", "beta"),)
        assert snapshot_projection(snapshot)["divergence"] == {"d": "incomplete"}

    def test_an_absent_producer_without_a_basis_is_still_incomplete(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={},
            producers={"d": (Producer("r", None, (), absent=("beta",)),)},
            not_present={"r": "beta"},
        )
        result = certify(snapshot, ("d",), ())
        assert result.state == "not-certified"
        assert result.findings == ("lineage-incomplete",)
        assert result.absent == (Absence("r", "beta"),)

    def test_a_present_producer_still_compares(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "a", transforms=("a",)),))},
            producers={"d": (Producer(stored_run="run-d", resolved_run="run-d", transforms=("other",)),)},
        )
        assert divergence_state(snapshot, "d") == "divergent"


class TestAbsenceIsCollectedFromReferences:
    def test_a_missing_ancestor_and_run_are_named_though_never_reached(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "dataset:anc", resolved=False),))},
            producers={},
            not_present={"run-d": "beta", "dataset:anc": "beta"},
        )
        result = certify(snapshot, ("d",), ())
        assert set(result.absent) == {Absence("run-d", "beta"), Absence("dataset:anc", "beta")}

    def test_an_absent_root_is_named(self):
        snapshot = LineageSnapshot(
            roots=("dataset:gone",), bases={}, producers={}, not_present={"dataset:gone": "beta"}
        )
        result = certify(snapshot, ("dataset:gone",), ())
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings
        assert result.absent == (Absence("dataset:gone", "beta"),)

    def test_findings_stay_the_closed_code_set(self):
        with pytest.raises(MalformedSnapshot):
            Certification(state="not-certified", findings=("lineage-incomplete: beta",))


class TestAbsenceIsProjected:
    def test_not_present_moves_the_projection_and_is_encodable(self):
        from beliefs.identity import v1

        with_absence = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "x", resolved=False),))},
            producers={},
            not_present={"x": "beta"},
        )
        unknown = LineageSnapshot(
            roots=("d",), bases={"d": Basis(tag="single", routes=(route("d", "x", resolved=False),))}, producers={}
        )
        a, b = snapshot_projection(with_absence), snapshot_projection(unknown)
        assert a["not_present"] == [{"ref": "x", "corpus_id": "beta"}] and b["not_present"] == []
        assert v1.encode(a) != v1.encode(b)
        producer = Producer(stored_run="r", resolved_run=None, transforms=(), absent=("beta",))
        assert v1.encode({"p": snapshot_projection(LineageSnapshot(roots=(), bases={}, producers={"d": (producer,)}))})

    def test_new_value_shapes_are_closed(self):
        with pytest.raises(MalformedSnapshot):
            Producer(stored_run="r", resolved_run=None, transforms=(), absent=["beta"])  # type: ignore[arg-type]
        with pytest.raises(MalformedSnapshot):
            Producer(stored_run="r", resolved_run=None, transforms=(), absent=("a", "b"))
        with pytest.raises(MalformedSnapshot):
            Certification(state="not-certified", findings=(), absent=("beta",))  # type: ignore[arg-type]


def conflict_snapshot(
    *, retired_routes: dict[str, tuple[str, ...]] | None = None, not_present: dict[str, str] | None = None
) -> LineageSnapshot:
    """x with two routes to distinct ancestors a and b, y with one route to c."""
    snapshot = LineageSnapshot(
        roots=("x", "y"),
        bases={
            "x": Basis(
                tag="conflict",
                routes=tuple(
                    sorted(
                        (route("x", "a", identity="route:a"), route("x", "b", identity="route:b")),
                        key=lambda r: r.stored_ancestor,
                    )
                ),
            ),
            "y": Basis(tag="single", routes=(route("y", "c", identity="route:c"),)),
        },
        producers={},
        not_present=not_present or {},
    )
    return retire(snapshot, retired_routes or {})


class TestRetirement:
    def test_effective_tag_follows_the_survivors(self):
        assert effective_tag(conflict_snapshot(), "x") == "conflict"
        assert effective_tag(conflict_snapshot(retired_routes={"x": ("route:a",)}), "x") == "single"
        assert effective_tag(conflict_snapshot(retired_routes={"x": ("route:a", "route:b")}), "x") == "retired"
        assert effective_tag(conflict_snapshot(retired_routes={"y": ("route:c",)}), "y") == "retired"
        assert [
            r.stored_ancestor
            for r in effective_routes(conflict_snapshot(retired_routes={"x": ("route:a",)}), "x")
        ] == ["b"]

    def test_retiring_one_conflicting_route_certifies_over_the_survivor(self):
        assert certify(conflict_snapshot(), ("x",), ("y",)).findings == ("lineage-divergent",)
        result = certify(conflict_snapshot(retired_routes={"x": ("route:a",)}), ("x",), ("y",))
        assert result.state == "independent" and result.findings == ()

    def test_retiring_every_route_is_incomplete_never_single(self):
        result = certify(
            conflict_snapshot(retired_routes={"x": ("route:a", "route:b")}), ("x",), ("y",)
        )
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings and "lineage-divergent" not in result.findings

    def test_divergence_runs_against_the_survivor(self):
        snapshot = conflict_snapshot(retired_routes={"x": ("route:a",)})
        producers = {"x": (Producer(stored_run="run-x", resolved_run="run-x", transforms=("t",)),)}
        snapshot = LineageSnapshot(
            roots=snapshot.roots, bases=snapshot.bases, producers=producers, retired=snapshot.retired
        )
        assert divergence_state(snapshot, "x") == "divergent"
        with pytest.raises(BasisTagMismatch):
            divergence_state(conflict_snapshot(), "x")
        with pytest.raises(BasisTagMismatch):
            divergence_state(conflict_snapshot(retired_routes={"x": ("route:a", "route:b")}), "x")

    def test_the_projection_carries_retired_and_identities_and_moves(self):
        plain = snapshot_projection(conflict_snapshot())
        plain_bases = cast(dict[str, Any], plain["bases"])
        plain_divergence = cast(dict[str, str], plain["divergence"])
        assert plain_bases["x"]["retired"] == [] and plain_bases["y"]["retired"] == []
        assert [r["identity"] for r in plain_bases["x"]["routes"]] == [["route:a"], ["route:b"]]
        assert plain_divergence["x"] == "divergent"
        one = snapshot_projection(conflict_snapshot(retired_routes={"x": ("route:a",)}))
        one_bases = cast(dict[str, Any], one["bases"])
        one_divergence = cast(dict[str, str], one["divergence"])
        assert one_bases["x"]["retired"] == ["route:a"] and one_divergence["x"] == "undiverged"
        both = snapshot_projection(conflict_snapshot(retired_routes={"x": ("route:a", "route:b")}))
        assert cast(dict[str, str], both["divergence"])["x"] == "incomplete"
        assert plain != one != both
        no_identity = snapshot_projection(
            LineageSnapshot(
                roots=("z",), bases={"z": Basis(tag="single", routes=(route("z", "w"),))}, producers={}
            )
        )
        no_identity_bases = cast(dict[str, Any], no_identity["bases"])
        assert no_identity_bases["z"]["routes"][0]["identity"] == []

    def test_swapping_identities_changes_survivor_certification_and_digest(self):
        from beliefs.identity import v1

        bases = {
            "x": Basis(
                tag="conflict",
                routes=(route("x", "a", identity="route:a"), route("x", "b", identity="route:b")),
            ),
            "y": Basis(tag="single", routes=(route("y", "a", identity="route:y"),)),
        }
        swapped_bases = {
            **bases,
            "x": Basis(
                tag="conflict",
                routes=(route("x", "a", identity="route:b"), route("x", "b", identity="route:a")),
            ),
        }
        original = retire(LineageSnapshot(roots=("x", "y"), bases=bases, producers={}), {"x": ("route:a",)})
        swapped = retire(
            LineageSnapshot(roots=("x", "y"), bases=swapped_bases, producers={}), {"x": ("route:a",)}
        )
        assert [r.stored_ancestor for r in effective_routes(original, "x")] == ["b"]
        assert [r.stored_ancestor for r in effective_routes(swapped, "x")] == ["a"]
        assert certify(original, ("x",), ("y",)).state == "independent"
        assert certify(swapped, ("x",), ("y",)).state == "shared-source"
        assert v1.digest("science.lineage-snapshot.v1", snapshot_projection(original)) != v1.digest(
            "science.lineage-snapshot.v1", snapshot_projection(swapped)
        )

    def test_retire_keeps_only_datasets_with_a_basis_and_refuses_unsorted(self):
        snapshot = retire(
            conflict_snapshot(), {"x": ("route:b", "route:a"), "elsewhere": ("route:z",)}
        )
        assert dict(snapshot.retired) == {"x": ("route:a", "route:b")}
        with pytest.raises(MalformedSnapshot):
            LineageSnapshot(roots=("x",), bases={}, producers={}, retired={"x": ("route:b", "route:a")})
        with pytest.raises(MalformedSnapshot):
            LineageSnapshot(roots=("x",), bases={}, producers={}, retired={"x": ("route:a", "route:a")})


class TestWalkAbsences:
    def test_an_absence_on_a_retired_branch_blocks_nothing(self):
        snapshot = conflict_snapshot(retired_routes={"x": ("route:a",)}, not_present={"a": "c2"})
        assert absences(snapshot) == ()
        assert certify(snapshot, ("x",), ("y",)).state == "independent"

    def test_an_absence_on_the_surviving_route_blocks(self):
        snapshot = conflict_snapshot(retired_routes={"x": ("route:a",)}, not_present={"b": "c2"})
        assert absences(snapshot) == (Absence("b", "c2"),)

    def test_an_absence_beneath_an_unretired_conflict_is_not_reached(self):
        snapshot = conflict_snapshot(not_present={"a": "c2"})
        assert absences(snapshot) == ()
        result = certify(snapshot, ("x",), ("y",))
        assert result.state == "not-certified" and result.findings == ("lineage-divergent",)

    def test_an_absent_root_and_a_producer_absence_are_still_reached(self):
        snapshot = LineageSnapshot(
            roots=("x",),
            bases={},
            producers={
                "x": (Producer(stored_run="run-x", resolved_run=None, transforms=(), absent=("c9",)),)
            },
            not_present={"x": "c2"},
        )
        assert absences(snapshot) == (Absence("run-x", "c9"), Absence("x", "c2"))


@pytest.mark.parametrize("identities", [("route:a", "route:b"), ("route:a", None)])
def test_identity_only_routes_have_one_canonical_order(identities):
    routes = tuple(route("x", "a", identity=identity) for identity in identities)
    basis = Basis(tag="conflict", routes=routes)
    snapshot = LineageSnapshot(roots=("x",), bases={"x": basis}, producers={})
    projected = cast(dict[str, Any], snapshot_projection(snapshot)["bases"])["x"]["routes"]
    assert [item["identity"] for item in projected] == [
        [] if identity is None else [identity] for identity in identities
    ]
    with pytest.raises(MalformedSnapshot, match="routes sorted"):
        Basis(tag="conflict", routes=tuple(reversed(routes)))
