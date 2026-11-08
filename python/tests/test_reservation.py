"""Value types, units and the change derivation of exposure events and reservation assignments."""

from __future__ import annotations

from dataclasses import replace

import pytest

from beliefs import reservation, stored
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.reservation import (
    EXPOSURE_EVENT_DOMAIN,
    OPEN,
    RESERVATION_ASSIGNMENT_DOMAIN,
    ExposureEvent,
    Group,
    GroupChange,
    IntervalUnit,
    ReservationAssignment,
    TermUnit,
    assignment_changes,
    assignment_record_refusal,
    exposure_event_from_facet,
    exposure_event_refusal,
    reservation_assignment_from_facet,
    unit_facet,
    unit_from_facet,
    unit_shape,
    unit_sort_key,
)

_D = "sha256:" + "a" * 64
_SESSION = "session:" + "0" * 32


def _event(**overrides: object) -> ExposureEvent:
    fields: dict[str, object] = {
        "channel": "read",
        "subjects": ("source:" + "1" * 64,),
        "units": (TermUnit("mm/cohort", "uams-tt2-tt3"),),
        "effect": "exposing",
        "read_class": "unmask",
        "bound": (("freeze", _D),),
        "account": "phase-2 unmask completed - exploratory description (design 2026-10-18)",
        "observer": _SESSION,
        "recorded_by": _SESSION,
        "observed_at": "2026-11-06T10:00:00Z",
        "propositions": (),
        "evidence": ("atoms-event:" + "3" * 64,),
    }
    fields.update(overrides)
    return ExposureEvent(**fields)  # type: ignore[arg-type]


def _mm_unmask_event() -> ExposureEvent:
    return _event()


def _knowledge_event(observed_at: str = "2026-11-01T00:00:00Z", *, recorded_by: str = _SESSION) -> ExposureEvent:
    return _event(
        channel="knowledge",
        subjects=(),
        units=(IntervalUnit(OPEN, observed_at),),
        read_class="training-knowledge",
        bound=(),
        observer=recorded_by,
        recorded_by=recorded_by,
        observed_at=observed_at,
        evidence=(),
    )


def _sun_knowledge_event() -> ExposureEvent:
    return _event(
        channel="knowledge",
        subjects=(),
        units=(IntervalUnit(OPEN, "2026-11-07T14:40:51Z"),),
        read_class="training-knowledge",
        bound=(),
        account="Possible training exposure through the actual UTC date of use; no provider-stated cutoff.",
        observer="agy/gemini-4-argon",
        observed_at="2026-11-07T14:40:51Z",
        evidence=("task:sun-7bfa16",),
    )


def _g(term: str, role: str, label: str | None = None, basis: str | None = None) -> Group:
    return Group((TermUnit("mm/cohort", term),), role, label, basis)


def _assignment(**overrides: object) -> ReservationAssignment:
    fields: dict[str, object] = {
        "chain": "mm-roster",
        "rule_name": "mm-phase-1-protocol-8",
        "rule_version": "amendment-7",
        "inputs": (("roster.yaml", _D),),
        "events": (),
        "scope": None,
        "applies": None,
        "groups": (_g("a", "open", "discovery"), _g("b", "unresolved")),
        "predecessor": None,
        "evidence": (),
        "flagged": None,
        "account": None,
        "participants": (),
        "prior_runs": (),
        "assigned_at": "2026-11-06T10:00:00Z",
        "assigned_by": _SESSION,
    }
    fields.update(overrides)
    return ReservationAssignment(**fields)  # type: ignore[arg-type]


def _interval_group(start: str, end: str, role: str, label: str) -> Group:
    return Group((IntervalUnit(start, end),), role, label, None)


def _sun_assignment_17() -> ReservationAssignment:
    t = ["2007-11-01", "2008-12-01", "2019-12-01", "2021-01-01", "2025-09-29", "2026-10-29"]
    z = [f"{d}T00:00:00Z" for d in t]
    return _assignment(
        chain="sun-epochs",
        rule_name="epoch-reservation-rule",
        rule_version="3",
        inputs=(("boundary-table", _D), ("named-series", _D), ("rule", _D)),
        events=("exposure-event:" + "5" * 64,),
        groups=(
            _interval_group(OPEN, z[0], "open", "exploration"),
            _interval_group(z[0], z[1], "withheld", "guard"),
            _interval_group(z[1], z[2], "reserved", "reserved (retrospective)"),
            _interval_group(z[2], z[3], "withheld", "guard"),
            _interval_group(z[3], z[4], "open", "exploration"),
            _interval_group(z[4], z[5], "withheld", "guard"),
            _interval_group(z[5], OPEN, "reserved", "reserved pool"),
        ),
        account="Inherits bounds, guards, prospective start and named series from assignment 16.",
        assigned_at="2026-11-07T14:40:51Z",
    )


def test_interval_units_sort_chronologically_with_open_ends():
    units = [
        IntervalUnit("2026-10-29T00:00:00Z", OPEN),
        IntervalUnit(OPEN, "2007-11-01T00:00:00Z"),
        IntervalUnit("2008-12-01T00:00:00Z", "2019-12-01T00:00:00Z"),
    ]
    assert sorted(units, key=unit_sort_key) == [units[1], units[2], units[0]]


@pytest.mark.parametrize(
    "start,end",
    [
        ("2008-12-01T00:00:00Z", "2008-12-01T00:00:00Z"),
        ("2019-12-01T00:00:00Z", "2008-12-01T00:00:00Z"),
        (OPEN, OPEN),
        ("2008-12-01T00:00:00.5Z", OPEN),
        ("2008-13-01T00:00:00Z", OPEN),
    ],
)
def test_degenerate_intervals_are_malformed(start, end):
    with pytest.raises(MalformedRecord):
        IntervalUnit(start, end)


@pytest.mark.parametrize("digest", ["sha256:ABCD" + "0" * 60, "sha256:" + "0" * 63, "md5:" + "0" * 64, "0" * 64])
def test_non_canonical_digests_are_malformed(digest):
    with pytest.raises(MalformedRecord):
        _event(bound=(("freeze", digest),))


def test_the_sun_event_round_trips_and_addresses_by_content():
    event = _sun_knowledge_event()
    assert exposure_event_from_facet(event.facet()) == event
    assert event.id == "exposure-event:" + v1.digest(EXPOSURE_EVENT_DOMAIN, event.facet())


def test_the_mm_event_round_trips_and_omits_empty_optionals():
    event = _mm_unmask_event()
    assert exposure_event_from_facet(event.facet()) == event
    bare = _event(bound=(), evidence=())
    assert "bound" not in bare.facet() and "evidence" not in bare.facet()


def test_kernel_evidence_selects_kernel_schemes():
    event = _event(evidence=("act-report:y", "holdings-observation:h", "run:x", "task:z"))
    assert event.kernel_evidence() == ("act-report:y", "holdings-observation:h", "run:x")


def test_a_read_event_names_a_subject_and_a_knowledge_event_none():
    with pytest.raises(MalformedRecord):
        _event(channel="read", subjects=())
    with pytest.raises(MalformedRecord):
        _event(channel="knowledge", subjects=("source:x",))


def test_event_lists_are_refused_not_tidied():
    with pytest.raises(MalformedRecord):
        _event(subjects=("source:b", "source:a"))
    with pytest.raises(MalformedRecord):
        _event(subjects=("source:a", "source:a"))
    with pytest.raises(MalformedRecord):
        _event(propositions=("claim:a",))
    with pytest.raises(MalformedRecord):
        _event(evidence=("nocolon",))
    with pytest.raises(MalformedRecord):
        _event(evidence=(":rest",))
    with pytest.raises(MalformedRecord):
        _event(observer="")
    with pytest.raises(MalformedRecord):
        _event(effect="maybe")
    with pytest.raises(MalformedRecord):
        _event(observed_at="2026-11-06T10:00:00.5Z")
    with pytest.raises(MalformedRecord):
        _event(account="")


def test_world_kind_schemes_outside_a_token_slot_allowlist_are_refused():
    from beliefs.profile import shipped_base

    world_kinds = {name for name, kind in shipped_base().kinds.items() if kind.role == "world"}
    for scheme in sorted(world_kinds - {"act-report", "run", "holdings-observation"}):
        with pytest.raises(MalformedRecord, match=scheme):
            _event(evidence=(f"{scheme}:a",))
    for scheme in sorted(world_kinds - {"exposure-event"}):
        with pytest.raises(MalformedRecord, match=scheme):
            _assignment(evidence=(f"{scheme}:a",))
    for scheme in sorted(world_kinds - {"run"}):
        with pytest.raises(MalformedRecord, match=scheme):
            _assignment(prior_runs=(f"{scheme}:a",))


def test_event_units_are_sorted_distinct_and_one_shape():
    a, b = TermUnit("mm/cohort", "a"), TermUnit("mm/cohort", "b")
    assert _event(units=(a, b)).units == (a, b)
    with pytest.raises(MalformedRecord):
        _event(units=(b, a))
    with pytest.raises(MalformedRecord):
        _event(units=(a, a))
    with pytest.raises(MalformedRecord):
        _event(units=(a, IntervalUnit(OPEN, "2026-11-07T14:40:51Z")))


def test_term_unit_grammar():
    for sort in ("cohort", "Mm/cohort", "mm/", "mm/cohort/x"):
        with pytest.raises(MalformedRecord):
            TermUnit(sort, "x")
    with pytest.raises(MalformedRecord):
        TermUnit("mm/cohort", "")
    TermUnit("mm/cohort", "Any Term")


def test_unit_facet_round_trip_and_shape():
    for unit in (TermUnit("mm/cohort", "a"), IntervalUnit(OPEN, "2007-11-01T00:00:00Z")):
        assert unit_from_facet(unit_facet(unit)) == unit
    assert unit_shape(TermUnit("mm/cohort", "a")) == "term"
    assert unit_shape(IntervalUnit(OPEN, "2007-11-01T00:00:00Z")) == "interval"
    with pytest.raises(MalformedRecord):
        unit_from_facet({"sort": "mm/cohort"})


def test_assignments_round_trip_and_address_by_content():
    for assignment in (_assignment(), _sun_assignment_17()):
        assert reservation_assignment_from_facet(assignment.facet()) == assignment
        assert assignment.id == "reservation-assignment:" + v1.digest(RESERVATION_ASSIGNMENT_DOMAIN, assignment.facet())


def test_assignment_facet_omissions():
    facet = _assignment().facet()
    assert facet["events"] == []
    for key in ("scope", "applies", "predecessor", "account", "evidence", "participants", "prior_runs", "flagged"):
        assert key not in facet
    assert facet["rule"] == {"name": "mm-phase-1-protocol-8", "version": "amendment-7"}
    assert _assignment(flagged=()).facet()["flagged"] == []
    assert reservation_assignment_from_facet(_assignment(flagged=()).facet()).flagged == ()


def test_assignment_kernel_references_and_shape():
    a = _assignment(
        evidence=("atoms-event:y", "exposure-event:x", "task:t"),
        prior_runs=("commit:a", "ext:e", "run:r"),
    )
    assert a.kernel_evidence() == ("exposure-event:x",)
    assert a.kernel_prior_runs() == ("run:r",)
    assert a.shape == "term"
    assert _sun_assignment_17().shape == "interval"


def test_every_unit_sits_in_exactly_one_group_and_intervals_do_not_overlap():
    with pytest.raises(MalformedRecord):
        _assignment(
            groups=(
                _g("a", "open"),
                Group((TermUnit("mm/cohort", "a"), TermUnit("mm/cohort", "b")), "open", None, None),
            )
        )
    with pytest.raises(MalformedRecord):
        _assignment(groups=(_g("a", "open"), _g("a", "reserved")))
    z = "2008-12-01T00:00:00Z"
    adjacent = (_interval_group(OPEN, z, "open", "x"), _interval_group(z, OPEN, "reserved", "y"))
    _assignment(groups=adjacent)
    overlap = (
        _interval_group(OPEN, "2009-01-01T00:00:00Z", "open", "x"),
        _interval_group(z, OPEN, "reserved", "y"),
    )
    with pytest.raises(MalformedRecord):
        _assignment(groups=overlap)
    with pytest.raises(MalformedRecord):
        _assignment(
            groups=(_interval_group(OPEN, z, "open", "x"), _interval_group(OPEN, "2007-01-01T00:00:00Z", "open", "y"))
        )


def test_one_record_holds_one_unit_shape():
    with pytest.raises(MalformedRecord):
        _assignment(groups=(_g("a", "open"), _interval_group("2008-12-01T00:00:00Z", OPEN, "reserved", "y")))


def test_groups_are_sorted_non_empty_and_well_formed():
    with pytest.raises(MalformedRecord):
        _assignment(groups=())
    with pytest.raises(MalformedRecord):
        _assignment(groups=(_g("b", "open"), _g("a", "open")))
    with pytest.raises(MalformedRecord):
        Group((), "open", None, None)
    with pytest.raises(MalformedRecord):
        _g("a", "banished")
    with pytest.raises(MalformedRecord):
        _g("a", "open", label="")
    with pytest.raises(MalformedRecord):
        _g("a", "open", basis="sha256:xyz")
    assert _g("a", "reserved", "reserved (A1)", _D).first == TermUnit("mm/cohort", "a")


@pytest.mark.parametrize(
    "overrides",
    [
        {"chain": "Mm"},
        {"chain": ""},
        {"chain": "1mm"},
        {"rule_name": ""},
        {"rule_version": ""},
        {"inputs": ()},
        {"inputs": (("b", _D), ("a", _D))},
        {"inputs": (("a", "sha256:00"),)},
        {"events": ("exposure-event:b", "exposure-event:a")},
        {"events": ("event:a",)},
        {"scope": "claim:a"},
        {"applies": "reservation-assignment:a"},
        {"scope": "proposition:p", "applies": "proposition:a"},
        {"predecessor": "exposure-event:a"},
        {"evidence": ("run:a",)},
        {"evidence": ("act-report:a",)},
        {"flagged": ("proposition:a",)},
        {"account": ""},
        {"participants": ("",)},
        {"participants": ("b", "a")},
        {"prior_runs": ("noscheme",)},
        {"prior_runs": ("act-report:a",)},
        {"prior_runs": ("exposure-event:a",)},
        {"assigned_at": "yesterday"},
    ],
)
def test_assignment_field_refusals(overrides):
    with pytest.raises(MalformedRecord):
        _assignment(**overrides)


def test_changes_report_changed_absent_and_added_groups():
    before = _assignment(groups=(_g("a", "reserved"), _g("b", "open"), _g("c", "unresolved")))
    after = _assignment(groups=(_g("a", "open"), _g("c", "unresolved"), _g("d", "open")), predecessor=before.id)
    changes = assignment_changes(before, after)
    assert [(c.kind, c.suspended) for c in changes] == [("changed", True), ("absent", False), ("added", False)]
    assert [c.previous_role for c in changes] == ["reserved", "open", None]
    assert [c.unit for c in changes] == [TermUnit("mm/cohort", t) for t in "abd"]


def test_an_unchanged_successor_derives_no_changes():
    before = _sun_assignment_17()
    after = replace(before, events=())
    assert assignment_changes(before, after) == ()


def test_module_exports_cover_reservation_and_stored_symbols():
    assert "KindOf" in reservation.__all__
    expected_stored = {
        "APPLIES",
        "ATTESTED_BY",
        "CONCERNS",
        "CONSIDERS",
        "EVIDENCED_BY",
        "EXPOSES",
        "EXPOSURE_EVENT_FACET",
        "FLAGS",
        "REPORTS",
        "RESERVATION_ASSIGNMENT_FACET",
        "exposure_event_node",
        "exposure_event_relations",
        "exposure_event_value",
        "reservation_assignment_node",
        "reservation_assignment_relations",
        "reservation_assignment_value",
    }
    assert expected_stored <= set(stored.__all__)


def test_non_string_keys_and_malformed_facet_mappings_raise_malformed_record():
    with pytest.raises(MalformedRecord):
        unit_from_facet({1: "mm/cohort", "term": "a"})  # pyright: ignore[reportArgumentType]
    with pytest.raises(MalformedRecord):
        exposure_event_from_facet({1: "read"})  # pyright: ignore[reportArgumentType]
    with pytest.raises(MalformedRecord):
        reservation_assignment_from_facet({1: "mm-roster"})  # pyright: ignore[reportArgumentType]
    event_facet = _mm_unmask_event().facet()
    with pytest.raises(MalformedRecord, match="bound"):
        exposure_event_from_facet({**event_facet, "bound": {1: _D}})
    with pytest.raises(MalformedRecord, match="exposure-event facet is missing"):
        exposure_event_from_facet({k: v for k, v in event_facet.items() if k != "channel"})
    with pytest.raises(MalformedRecord, match="exposure-event facet has unexpected keys"):
        exposure_event_from_facet({**event_facet, "bogus": 1})
    assignment_facet = _assignment().facet()
    with pytest.raises(MalformedRecord, match="reservation-assignment facet is missing"):
        reservation_assignment_from_facet({k: v for k, v in assignment_facet.items() if k != "chain"})
    with pytest.raises(MalformedRecord, match="reservation-assignment facet has unexpected keys"):
        reservation_assignment_from_facet({**assignment_facet, "bogus": 1})
    with pytest.raises(MalformedRecord, match="rule is missing"):
        reservation_assignment_from_facet({**assignment_facet, "rule": {"name": "r"}})
    with pytest.raises(MalformedRecord, match="rule has unexpected keys"):
        reservation_assignment_from_facet({**assignment_facet, "rule": {"name": "r", "version": "1", "extra": "x"}})
    with pytest.raises(MalformedRecord, match="group is missing"):
        reservation_assignment_from_facet(
            {**assignment_facet, "groups": [{"units": [{"sort": "mm/cohort", "term": "a"}]}]}
        )
    with pytest.raises(MalformedRecord, match="group has unexpected keys"):
        reservation_assignment_from_facet(
            {
                **assignment_facet,
                "groups": [{"units": [{"sort": "mm/cohort", "term": "a"}], "role": "open", "extra": 1}],
            }
        )


def test_non_group_element_and_group_change_invariants_raise_malformed_record():
    with pytest.raises(MalformedRecord, match="groups entry must be a Group"):
        _assignment(groups=("not-a-group",))  # type: ignore[arg-type]
    unit = TermUnit("mm/cohort", "a")
    assert GroupChange(unit, "changed", "reserved", True).suspended is True
    assert GroupChange(unit, "added", None, False).previous_role is None
    with pytest.raises(MalformedRecord, match="unit"):
        GroupChange("not-a-unit", "added", None, False)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="kind"):
        GroupChange(unit, "bogus", "open", False)
    with pytest.raises(MalformedRecord, match="added"):
        GroupChange(unit, "added", "open", False)
    with pytest.raises(MalformedRecord, match="added"):
        GroupChange(unit, "added", None, True)
    with pytest.raises(MalformedRecord, match="previous_role"):
        GroupChange(unit, "changed", None, False)
    with pytest.raises(MalformedRecord, match="previous_role"):
        GroupChange(unit, "absent", "bogus", False)


def test_changes_cover_non_reserved_role_changes_absent_reserved_and_field_or_member_edits():
    before = _assignment(
        groups=(
            _g("a", "open", label="old"),
            _g("b", "reserved"),
            _g("c", "open", basis=_D),
            Group((TermUnit("mm/cohort", "d"), TermUnit("mm/cohort", "e")), "open", None, None),
        )
    )
    after = _assignment(
        groups=(
            _g("a", "withheld", label="old"),
            _g("c", "open", label="renamed", basis=_D),
            Group((TermUnit("mm/cohort", "d"),), "open", None, None),
        ),
        predecessor=before.id,
    )
    changes = assignment_changes(before, after)
    assert [(c.unit, c.kind, c.previous_role, c.suspended) for c in changes] == [
        (TermUnit("mm/cohort", "a"), "changed", "open", False),
        (TermUnit("mm/cohort", "b"), "absent", "reserved", True),
        (TermUnit("mm/cohort", "c"), "changed", "open", False),
        (TermUnit("mm/cohort", "d"), "changed", "open", False),
    ]


def test_refusal_functions_report_wrong_kind_with_single_and_multi_kind_grammar():
    event = _event(propositions=("proposition:p",))
    relations = stored.exposure_event_relations(event)
    multi = exposure_event_refusal(event, relations, kind_of=lambda _ref: "proposition", sorts={"mm/cohort"})
    assert multi is not None and multi.code == "exposure-ref-unresolved"
    assert "is a proposition, not one of dataset, source" in multi.detail

    single = exposure_event_refusal(
        event,
        relations,
        kind_of=lambda ref: "dataset" if ref.startswith("source:") else "source",
        sorts={"mm/cohort"},
    )
    assert single is not None and single.code == "exposure-ref-unresolved"
    assert "is a source, not a proposition" in single.detail

    assignment = _assignment(events=("exposure-event:e",))
    assignment_refusal = assignment_record_refusal(
        assignment,
        stored.reservation_assignment_relations(assignment),
        kind_of=lambda _ref: "source",
        assignment_of=lambda _ref: None,
        sorts={"mm/cohort"},
    )
    assert assignment_refusal is not None and assignment_refusal.code == "assignment-ref-unresolved"
    assert "is a source, not a exposure-event" in assignment_refusal.detail
