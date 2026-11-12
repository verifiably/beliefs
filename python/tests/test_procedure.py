"""Procedure values preserve their full normative facet and exact scales."""

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from typing import Any, cast

import pytest
from nodes.core.node import Node

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.measurement import Aspect, Observable
from beliefs.procedure import (
    External,
    Implementation,
    ModelInputs,
    Procedure,
    SameAs,
    Scale,
    procedure_from_stored,
    procedure_identity,
    procedure_projection,
)
from beliefs.restriction import IntervalRestriction

OBS = Observable("testing/energy", "testing/event", Aspect("testing/energy-aspect", "EX:a"))
PID = "procedure:" + "a" * 64
DIGEST = "sha256:" + "b" * 64
AID = "assessment:" + "c" * 64


def procedure(**changes):
    fields = {
        "kind": "testing/instrument",
        "name": "An instrument",
        "definition": "How to measure it.",
        "yields": (OBS,),
        "scale": None,
        "validated_in": {},
        "compatible_with": (),
        "evidence": (),
        "implementation": None,
        "inputs": None,
        "parameters": {},
        "external": None,
    }
    return Procedure(**(fields | changes))


def node_for(kind, identity, facet):
    return Node(id=identity, kind=kind, title="Measurement record", facets={kind: facet})


def test_identity_is_content_addressed():
    value = procedure()
    assert procedure_identity(value) == procedure_identity(procedure())
    assert procedure_identity(value) == "procedure:" + v1.digest("science.procedure.v1", procedure_projection(value))
    for change in ({"definition": "Other normative prose"}, {"name": "Other"}, {"parameters": {"x": "1"}}):
        assert procedure_identity(procedure(**change)) != procedure_identity(value)


def test_projection_has_no_nulls_and_round_trips():
    scope = {"testing/duration": IntervalRestriction("testing/year", Fraction(1), Fraction(2), True, False, "civil")}
    value = procedure(
        scale=Scale(Fraction(0), Fraction(52), "higher-is-less"),
        validated_in=scope,
        compatible_with=(PID,),
        evidence=(AID,),
        implementation=Implementation("code", DIGEST),
        inputs=ModelInputs((DIGEST,), (DIGEST,)),
        parameters={"x": "1"},
        external=External("uri", "exact"),
    )
    facet: dict[str, Any] = procedure_projection(value)
    assert facet["scale"] == {"range": ["0", "52"], "orientation": "higher-is-less"}
    assert facet["definition"] == "How to measure it."
    v1.encode(facet)
    assert procedure_from_stored(node_for("procedure", procedure_identity(value), facet)) == value
    assert (
        procedure_from_stored(node_for("procedure", procedure_identity(procedure()), procedure_projection(procedure())))
        == procedure()
    )
    scope.clear()
    assert value.validated_in
    with pytest.raises(TypeError):
        cast(dict[str, str], value.parameters)["x"] = "2"
    with pytest.raises(FrozenInstanceError):
        value.name = "changed"  # pyright: ignore[reportAttributeAccessIssue]


def test_from_stored_refuses_a_non_canonical_facet_and_a_wrong_id():
    facet: dict[str, Any] = procedure_projection(procedure())
    for bad in (
        facet | {"scale": None},
        facet | {"extra": 1},
        facet | {"yields": [facet["yields"][0]] * 2},
        facet | {"name": "e\u0301"},
        facet | {"yields": [{"quantity_kind": "bad"}]},
    ):
        with pytest.raises(MalformedRecord):
            procedure_from_stored(node_for("procedure", procedure_identity(procedure()), bad))
    with pytest.raises(MalformedRecord):
        procedure_from_stored(node_for("procedure", PID, facet))


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "bad"},
        {"name": ""},
        {"definition": None},
        {"yields": ("bad",)},
        {"scale": {}},
        {"compatible_with": ("procedure:abc",)},
        {"evidence": (PID,)},
        {"parameters": {"x": 1}},
        {"parameters": {1: "x"}},
        {"validated_in": {"bad": IntervalRestriction("testing/year", Fraction(0), None, True, False)}},
        {"implementation": {}},
        {"inputs": {}},
        {"external": {}},
        {"parameters": {"x": "e\u0301"}},
    ],
)
def test_field_grammar(changes):
    with pytest.raises(MalformedRecord):
        procedure(**changes)


def test_scale_is_range_or_same_as():
    assert not procedure(scale=SameAs(PID)).is_authority
    for low, high, orientation in ((1, 1, "higher-is-more"), (2, 1, "higher-is-more"), (0, 1, "up")):
        with pytest.raises(MalformedRecord):
            Scale(Fraction(low), Fraction(high), orientation)
    facet: dict[str, Any] = procedure_projection(procedure()) | {
        "scale": {"range": ["0", "1"], "orientation": "higher-is-more", "same_as": PID}
    }
    with pytest.raises(MalformedRecord):
        procedure_from_stored(node_for("procedure", PID, facet))


def test_authority_flag():
    assert procedure(scale=Scale(Fraction(0), Fraction(1), "higher-is-more")).is_authority
    assert not procedure().is_authority


@pytest.mark.parametrize("value", [Fraction(1, 3), Fraction(10**8192), Fraction(1, 10**8193), 1, "1"])
def test_scale_refuses_unpersistable_or_untyped_numbers(value):
    with pytest.raises(MalformedRecord):
        Scale(value, Fraction(10**4096), "higher-is-more")


@pytest.mark.parametrize("value", [Fraction(1, 10**4096), Fraction(10**4096), Fraction(123, 10**4098)])
def test_exact_scale_projection_reloads_at_decimal_budget(value):
    record = procedure(scale=Scale(Fraction(0), value, "higher-is-more"))
    assert (
        procedure_from_stored(node_for("procedure", procedure_identity(record), procedure_projection(record))) == record
    )


def test_yields_are_distinct_and_sorted_by_projection():
    other = replace(OBS, aspect=None)
    one = procedure(yields=(OBS, other, OBS))
    two = procedure(yields=(other, OBS))
    assert one == two
    assert procedure_identity(one) == procedure_identity(two)


@pytest.mark.parametrize(
    "factory,args",
    [
        (SameAs, ("procedure:" + "A" * 64,)),
        (Implementation, ("code", "bad")),
        (ModelInputs, (("bad",), ())),
        (External, ("uri", "bad")),
    ],
)
def test_nested_field_grammar(factory, args):
    with pytest.raises(MalformedRecord):
        factory(*args)


@pytest.mark.parametrize(
    "observable",
    [
        replace(OBS, aspect=Aspect("testing/energy-aspect", "e\u0301")),
        replace(OBS, aspect=Aspect("testing/energy-aspect", "\ud800")),
    ],
)
def test_yield_text_must_be_canonical_at_construction(observable):
    with pytest.raises(MalformedRecord):
        procedure(yields=(observable,))


def test_yield_constructor_requires_typed_observables():
    with pytest.raises(MalformedRecord):
        procedure(yields=({"quantity_kind": "testing/energy", "bearer_sort": "testing/event"},))


def test_scope_constructor_requires_typed_restrictions_and_canonical_text():
    from beliefs.restriction import TermRestriction

    for bad in ({"sort": "testing/cohort", "term": "x"}, TermRestriction("testing/cohort", "e\u0301")):
        with pytest.raises(MalformedRecord):
            procedure(validated_in={"testing/population": bad})


@pytest.mark.parametrize("kind", ["procedure", "referent-mapping", "proxy-model", "classification-rule"])
def test_record_readers_require_every_projected_field_and_their_kind(kind):
    from test_classification_rule import rule
    from test_proxy_model import proxy
    from test_referent_mapping import mapping

    from beliefs.classification_rule import rule_from_stored, rule_identity, rule_projection
    from beliefs.proxy_model import proxy_from_stored, proxy_identity, proxy_projection
    from beliefs.referent_mapping import mapping_from_stored, mapping_identity, mapping_projection

    factory, project, identify, read = {
        "procedure": (procedure, procedure_projection, procedure_identity, procedure_from_stored),
        "referent-mapping": (mapping, mapping_projection, mapping_identity, mapping_from_stored),
        "proxy-model": (proxy, proxy_projection, proxy_identity, proxy_from_stored),
        "classification-rule": (rule, rule_projection, rule_identity, rule_from_stored),
    }[kind]
    value = factory()
    facet = project(value)
    for key in facet:
        with pytest.raises(MalformedRecord):
            read(node_for(kind, identify(value), {k: v for k, v in facet.items() if k != key}))
    node = node_for(kind, identify(value), facet)
    node.kind = "dataset"
    with pytest.raises(MalformedRecord):
        read(node)


def test_same_as_projects_only_the_authority_and_round_trips():
    value = procedure(scale=SameAs(PID))
    facet = procedure_projection(value)
    assert facet["scale"] == {"same_as": PID}
    assert procedure_from_stored(node_for("procedure", procedure_identity(value), facet)) == value


def test_all_restriction_forms_round_trip_without_a_profile():
    from beliefs.restriction import RuleRestriction, TermRestriction, TimeIntervalRestriction, UnionRestriction

    for restriction in (
        TermRestriction("testing/cohort", "EX:a"),
        TimeIntervalRestriction("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"),
        RuleRestriction("classification-rule:" + "d" * 64, ("EX:a",)),
        UnionRestriction((TermRestriction("testing/cohort", "EX:a"), TermRestriction("testing/cohort", "EX:b"))),
    ):
        value = procedure(validated_in={"testing/dimension": restriction})
        assert (
            procedure_from_stored(node_for("procedure", procedure_identity(value), procedure_projection(value)))
            == value
        )


def test_scale_reader_refuses_numeric_bounds_and_noncanonical_numeric_spelling():
    value = procedure(scale=Scale(Fraction(0), Fraction(1), "higher-is-more"))
    for bounds in ([0, "1"], ["0.0", "1"], ["0", "1.0"], ["0", "Infinity"], ["0", "1e4097"]):
        facet = procedure_projection(value) | {"scale": {"range": bounds, "orientation": "higher-is-more"}}
        with pytest.raises(MalformedRecord):
            procedure_from_stored(node_for("procedure", procedure_identity(value), facet))


def test_unknown_validation_is_distinct_and_round_trips():
    from beliefs.restriction import TermRestriction

    universal = procedure()
    known = procedure(validated_in={"testing/stage": TermRestriction("testing/stage", "EX:a")})
    assert procedure_identity(universal) == "procedure:9f77d7564f00e17fa0119331b4de3c1d347d58d8f1b83031b679044e3abff4ce"
    assert procedure_identity(known) == "procedure:2b015237ba6c2f55d80dc48dc42fd47067b3187eba82f7e8e2750c0a338d90e5"
    unknown = procedure(validated_in="unknown")
    facet = procedure_projection(unknown)
    assert facet["validated_in"] == "unknown"
    v1.encode(facet)
    assert len({procedure_identity(v) for v in (universal, known, unknown)}) == 3
    assert procedure_from_stored(node_for("procedure", procedure_identity(unknown), facet)) == unknown
    with pytest.raises(MalformedRecord):
        procedure_from_stored(node_for("procedure", procedure_identity(universal), facet))


@pytest.mark.parametrize("value", [None, "", "UNKNOWN", "unvalidated", 0, False, [], ["unknown"]])
def test_only_exact_unknown_tag_or_restriction_map_is_valid(value):
    with pytest.raises(MalformedRecord):
        procedure(validated_in=value)
    facet = procedure_projection(procedure()) | {"validated_in": value}
    with pytest.raises(MalformedRecord):
        procedure_from_stored(node_for("procedure", PID, facet))


def test_validation_is_required_and_null_is_not_identity_encodable():
    from beliefs.errors import IdentityError

    facet = procedure_projection(procedure())
    del facet["validated_in"]
    with pytest.raises(MalformedRecord):
        procedure_from_stored(node_for("procedure", PID, facet))
    with pytest.raises(IdentityError):
        v1.encode(procedure_projection(procedure()) | {"validated_in": None})
