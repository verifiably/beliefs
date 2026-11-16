"""Synthetic spectral views check held bytes and exact elapsed geometry, not science."""

from dataclasses import replace
from fractions import Fraction as F

import pytest
from candidate_contracts import spectral_profile

from beliefs import errors, stored
from beliefs.claim import Referent, build_claim
from beliefs.decode import WireClaim, decode_claim
from beliefs.procedure import procedure_from_stored
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.geometry import elapsed_factor
from beliefs.series.reader import read_series
from beliefs.series.types import SeriesRefused

from .fixtures import raw_object
from .spectral_case import spectral_case


@pytest.fixture(scope="module")
def profile(base_contract):
    return spectral_profile(base_contract)


def read(s, ref=None, *, profile=None):
    return read_series(
        s.series if ref is None else series_ref_from_projection(ref),
        profile=profile or s.profile,
        records=s.case.records,
        evidence=s.case.evidence(),
    )


def raw(s, ref):
    return raw_object(s.case.buffers[ref["resource"].split(":")[1]])


def table(s):
    return raw(s, series_ref_projection(s.series))["table"]


def view_of(s, table_ref, selection=(0, 1, 2), **extra):
    return s.case.view(table_ref, list(selection), **extra)


def test_two_descriptors_share_one_sort(profile):
    a, b = spectral_case(profile), spectral_case(profile)
    t = b.case.rewrite(table(b), lambda d: d["channels"]["signal"].update(values=["1", "3", "1"]))
    b_ref = series_ref_from_projection(view_of(b, t))
    b_claim = build_claim(
        profile,
        operator=a.claim.operator,
        roles={"series": Referent("general/series-view", b_ref.dataset)},
        form="polar",
        layer="statistical",
    )
    assert a.series != b_ref
    assert claim_identity(a.claim) != claim_identity(b_claim)
    assert a.claim.roles["series"].sort == b_claim.roles["series"].sort == "general/series-view"
    assert len({row.ref.dataset for row in read(a).graph}) == 3
    snapshot = build_snapshot(
        readable={}, kinds={"dataset": frozenset(k for k in a.case.records.nodes if k.startswith("dataset:"))}
    )
    assert decode_claim(WireClaim(**project_claim(a.claim)), profile=profile, snapshot=snapshot)
    absent = build_snapshot(readable={}, kinds={"dataset": frozenset()})
    with pytest.raises(errors.UnboundReferent):
        decode_claim(WireClaim(**project_claim(a.claim)), profile=profile, snapshot=absent)
    unknown = build_snapshot(readable={})
    decoded = decode_claim(WireClaim(**project_claim(a.claim)), profile=profile, snapshot=unknown)
    assert decoded[1].outcomes["role:series"] is TermOutcome.NOT_CONSULTED
    with pytest.raises(errors.IdentifierClassMismatch):
        build_claim(
            profile,
            operator=a.claim.operator,
            roles={"series": Referent("general/series-view", "dataset:" + "a" * 64)},
            form="polar",
            layer="statistical",
        )


def test_axis_arithmetic(profile):
    s = spectral_case(profile)
    checked = read(s)
    assert checked.count == 3
    assert checked.values == (F(1), F(2), F(1))
    assert checked.spacing_seconds == F(1, 100)
    assert checked.rate_hz == 100
    assert checked.coordinates[-1] - checked.coordinates[0] == F(1, 50)
    hours = spectral_case(profile, axis_unit="si-brochure/hour", spacing="1")
    seconds = spectral_case(profile, spacing="3600")
    assert read(hours).spacing_seconds == read(seconds).spacing_seconds == F(3600)
    assert read(hours).rate_hz == read(seconds).rate_hz == F(1, 3600)
    factor, _ = elapsed_factor(profile, profile.time_roles, "si-brochure/hour")
    assert factor == 3600


@pytest.mark.parametrize("damage", ["table-location", "digest", "table-record"])
def test_missing_held_bytes_refuses(profile, damage):
    s = spectral_case(profile)
    t = table(s)
    if damage == "table-location":
        del s.case.locations[series_ref_from_projection(t)]
    elif damage == "digest":
        s.case.buffers[t["resource"].split(":")[1]] = b"damaged"
    else:
        del s.case.records.nodes[t["dataset"]]
    with pytest.raises(errors.DependencyNotHeld if damage == "table-record" else SeriesRefused):
        read(s)


@pytest.mark.parametrize("damage", ["non-time", "zero", "negative", "rate", "irregular", "channel", "range", "order"])
def test_geometry_and_selection_refusals(profile, damage):
    s = spectral_case(profile)
    if damage in ("channel", "range", "order"):
        changes = {
            "channel": lambda d: d.update(channel="other"),
            "range": lambda d: d.update(selection=[0, 3]),
            "order": lambda d: d.update(selection=[1, 0]),
        }
        ref = s.case.rewrite(series_ref_projection(s.series), changes[damage])
    else:

        def change(d):
            if damage == "non-time":
                d["axis"]["unit"] = "si-brochure/hertz"
            elif damage in ("zero", "negative"):
                d["axis"]["grid"]["spacing"] = "0" if damage == "zero" else "-1"
            elif damage == "rate":
                d["axis"]["grid"]["rate"] = "99"
            else:
                d["coordinates"][-1] = "0.025"

        ref = view_of(s, s.case.rewrite(table(s), change))
    with pytest.raises(SeriesRefused) as caught:
        read(s, ref)
    assert caught.value.code == "invalid-series"


def test_index_and_absolute_labels_do_not_imply_elapsed_rate(profile):
    for axis, coords in (
        ({"kind": "index"}, [0, 1, 2]),
        (
            {"kind": "absolute", "convention": "utc-label", "grid": "labels"},
            ["2000-01-01T00:00:00Z", "2000-01-01T00:00:00.01Z", "2000-01-01T00:00:00.02Z"],
        ),
    ):
        s = spectral_case(profile)
        t = s.case.rewrite(table(s), lambda d, axis=axis, coords=coords: d.update(axis=axis, coordinates=coords))
        checked = read(s, view_of(s, t))
        assert checked.rate_hz is checked.spacing_seconds is None


def test_missing_time_activation_refuses_in_reader(profile, base_contract):
    s = spectral_case(profile)
    missing_time = spectral_profile(base_contract, omit=("si-brochure",))
    with pytest.raises(
        SeriesRefused, match="time quantity/unit defining source disagrees with the base time roles"
    ) as caught:
        read(s, profile=missing_time)
    assert caught.value.code == "invalid-series"


def test_select_and_rebin_provenance(profile):
    s = spectral_case(profile)
    selected = view_of(s, table(s), (0, 2), selection_procedure=s.estimator)
    checked = read(s, selected)
    assert checked.values == (F(1), F(1)) and checked.rate_hz == 50
    assert series_ref_from_projection(selected) != s.series
    selected_table = s.case.rewrite(
        table(s),
        lambda d: (
            d.update(coordinates=["0", "0.02"]),
            d["axis"].update(grid={"kind": "regular", "spacing": "0.02"}),
            d["channels"]["signal"].update(values=["1", "1"]),
        ),
    )
    materialized = view_of(
        s,
        selected_table,
        (0, 1),
        transform={
            "source": series_ref_projection(s.series),
            "procedure": s.estimator,
            "operation": "select",
            "mapping": [0, 2],
        },
    )
    assert read(s, materialized).values == checked.values
    assert read(s, materialized).predecessors[0].ref == s.series
    with pytest.raises(SeriesRefused, match="selection"):
        read(s, view_of(s, table(s), (0, 2)))
    t = raw(s, table(s))
    t["support"] = [["0", "0.01"], ["0.01", "0.02"], ["0.02", "0.03"]]
    source = view_of(s, s.case.hold(t))
    t.update(coordinates=["0", "0.02"], support=[["0", "0.02"], ["0.02", "0.03"]])
    t["axis"]["grid"] = {"kind": "regular", "spacing": "0.02"}
    t["channels"]["signal"]["values"] = ["1.5", "1"]
    output = s.case.hold(t)
    ref = view_of(
        s,
        output,
        (0, 1),
        transform={"source": source, "procedure": s.estimator, "operation": "rebin", "mapping": [[0, 1], [2]]},
    )
    assert read(s, ref).values == (F(3, 2), F(1))
    del s.case.records.nodes[s.estimator]
    with pytest.raises(errors.DependencyNotHeld):
        read(s, ref)


def mapped(s, *, damage=None):
    """Authored bounded constant-offset map, never a clock authority claim."""
    epoch = "2000-01-01T00:00:00Z"
    labels = [epoch, "2000-01-01T00:00:00.01Z", "2000-01-01T00:00:00.02Z"]
    clock_doc = {
        "format": "science.series-clock-map.v1",
        "convention": "utc-tai",
        "low": epoch,
        "high": "2000-01-02T00:00:00Z",
        "procedure": s.estimator,
        "segments": [{"from": epoch, "tai_minus_utc": 32}],
    }
    if damage == "transition":
        labels = ["2000-01-01T23:59:59Z", "2000-01-02T00:00:00Z", "2000-01-02T00:00:01Z"]
        clock_doc["high"] = "2000-01-03T00:00:00Z"
        clock_doc["segments"].append({"from": "2000-01-02T00:00:00Z", "tai_minus_utc": 33})
    clock = s.case.hold(clock_doc)
    row = {
        "label": "Authored clock epoch",
        "clock": {"map": clock, "epoch": "1999-12-31T23:59:59Z" if damage == "epoch" else labels[0]},
    }
    if damage == "origin":
        row.pop("clock")
    origin = {"source": s.case.hold({"format": "science.series-origins.v2", "origins": {"zero": row}}), "key": "zero"}
    t = raw(s, table(s))
    t.update(
        axis={"kind": "absolute", "convention": "utc-label", "grid": "labels"},
        coordinates=labels,
        support=[
            [labels[0], labels[1]],
            [labels[1], labels[2]],
            [
                labels[2],
                "2000-01-02T00:00:00Z"
                if damage == "endpoint"
                else ("2000-01-02T00:00:02Z" if damage == "transition" else "2000-01-01T00:00:00.03Z"),
            ],
        ],
    )
    source = view_of(s, s.case.hold(t))
    if damage == "source-transform":
        source = view_of(
            s,
            s.case.hold(t),
            transform={"source": source, "procedure": s.estimator, "operation": "select", "mapping": [0, 1, 2]},
        )
    t.update(
        axis={
            "kind": "elapsed",
            "unit": "si-brochure/second",
            "origin": origin,
            "basis": "clock-mapped",
            "grid": {"kind": "regular", "spacing": "1" if damage == "transition" else "0.01"},
        },
        coordinates=["0", "1", "3"] if damage == "transition" else ["0", "0.01", "0.02"],
        support=[["0", "1"], ["1", "3"], ["3", "4"]]
        if damage == "transition"
        else [["0", "0.01"], ["0.01", "0.02"], ["0.02", "0.03"]],
    )
    if damage == "coordinate":
        t["coordinates"][1] = "0.011"
        t["axis"]["grid"] = {"kind": "irregular"}
    if damage == "support":
        t["support"][-1][-1] = "0.04"
    ref = view_of(s, s.case.hold(t), transform={"source": source, "procedure": s.estimator, "operation": "clock-map"})
    return ref, clock


def test_checked_clock_mapping(profile):
    s = spectral_case(profile)
    ref, clock = mapped(s)
    checked = read(s, ref)
    assert checked.coordinates == (F(0), F(1, 100), F(1, 50))
    assert checked.spacing_seconds == F(1, 100) and checked.rate_hz == 100
    assert checked.values == (F(1), F(2), F(1))
    assert checked.support == ((F(0), F(1, 100)), (F(1, 100), F(1, 50)), (F(1, 50), F(3, 100)))
    assert checked.descriptor.selection == (0, 1, 2)
    row = next(row for row in checked.graph if row.ref == series_ref_from_projection(clock))
    assert row.records == (s.estimator,)


@pytest.mark.parametrize(
    "damage",
    [
        "procedure-node",
        "clock-node",
        "implementation",
        "origin",
        "locator",
        "epoch",
        "endpoint",
        "coordinate",
        "support",
        "source-transform",
        "transition",
    ],
)
def test_clock_mapping_refusals(profile, damage):
    s = spectral_case(profile)
    if damage == "implementation":
        procedure = procedure_from_stored(s.case.records.nodes[s.estimator])
        node = stored.procedure_node(replace(procedure, implementation=None))
        s.case.records.nodes[node.id] = node
        s = replace(s, estimator=node.id)
    ref, clock = mapped(s, damage=damage)
    if damage == "procedure-node":
        del s.case.records.nodes[s.estimator]
    if damage == "clock-node":
        del s.case.records.nodes[clock["dataset"]]
    if damage == "locator":
        del s.case.locations[series_ref_from_projection(clock)]
    error = errors.DependencyNotHeld if damage in ("procedure-node", "clock-node") else SeriesRefused
    with pytest.raises(error) as caught:
        read(s, ref)
    if error is SeriesRefused:
        expected = {
            "implementation": "requires a held procedure with Implementation",
            "origin": "requires a clock-bearing origin",
            "epoch": "outside clock coverage",
            "endpoint": "outside clock coverage",
            "coordinate": "coordinates contradict clock map",
            "support": "support contradicts clock map",
            "source-transform": "requires an untransformed absolute view",
            "transition": "regular",
        }
        if damage in expected:
            assert expected[damage] in str(caught.value)
        assert caught.value.code == ("evidence-unavailable" if damage == "locator" else "invalid-series")
