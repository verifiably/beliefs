"""Dependency freezing follows typed normative fields and strict held readers."""

from fractions import Fraction

import pytest
from nodes.core.node import Node
from test_procedure import AID, OBS, PID, node_for, procedure
from test_proxy_model import proxy
from test_stored import _testing_writer

from beliefs import dependencies, errors, stored
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.dependencies import dependency_closure, read_record, record_references, record_terms, walk
from beliefs.measurement import Observable
from beliefs.procedure import SameAs, Scale, procedure_identity, procedure_projection
from beliefs.profile import compile_profile
from beliefs.proxy_model import Calibration, ProxySource, ProxyTarget, proxy_from_stored
from beliefs.register import AssumptionsRegister
from beliefs.restriction import (
    IntervalRestriction,
    RuleRestriction,
    TermRestriction,
    TimeIntervalRestriction,
    UnionRestriction,
)


@pytest.fixture()
def profile(base_contract, testing_document):
    from copy import deepcopy

    second = deepcopy(testing_document)
    second["contract"] = "secondpack"
    second["assumption_kinds"] = {}
    return compile_profile(
        base_contract,
        [
            parse_domain_contract(document, source="<dependencies>", base=base_contract, predecessor=None)
            for document in (testing_document, second)
        ],
    )


class Records:
    def __init__(self, *values):
        self.nodes = {}
        for value in values:
            self.put(value)

    def put(self, value):
        kind = {
            "Procedure": "procedure",
            "ReferentMapping": "referent_mapping",
            "ProxyModel": "proxy_model",
            "ClassificationRule": "classification_rule",
            "AssumptionsRegister": "assumptions_register",
        }[type(value).__name__]
        node = getattr(stored, kind + "_node")(value)
        self.nodes[node.id] = node
        return node.id

    def holds(self, id):
        return id in self.nodes

    def read(self, id):
        return self.nodes[id]

    def retraction_in_force(self, id):
        return False

    def observation_held(self, digest):
        return False

    def crosswalks(self, a, b):
        result = []
        for node in self.nodes.values():
            if node.kind == "proxy-model":
                value = proxy_from_stored(node)
                if value.crosswalk is not None and {value.source.procedure, value.target.scale_of} == {a, b}:
                    result.append(node.id)
        return tuple(sorted(result))


def test_closure_follows_same_as_and_proxy_references(profile):
    authority = procedure(name="authority", scale=Scale(Fraction(0), Fraction(1), "higher-is-more"))
    follower = procedure(name="follower", scale=SameAs(procedure_identity(authority)))
    source = procedure(name="source")
    records = Records(authority, follower, source)
    p = proxy(
        source=ProxySource(OBS, procedure_identity(source)), basis=Calibration(OBS, (AID,), ("opaque/rule",), None)
    )
    proxy_id = records.put(p)
    records.nodes[AID] = Node(id=AID, kind="assessment", title="Opaque calibration")
    closure = dependency_closure([procedure_identity(follower), proxy_id], records, profile)
    assert tuple(entry.id for entry in closure) == tuple(
        sorted([procedure_identity(authority), procedure_identity(follower), procedure_identity(source), proxy_id, AID])
    )
    assert next(entry.terms for entry in closure if entry.id == AID) == ()
    assert next(entry.terms for entry in closure if entry.id == proxy_id) == (
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
    )


def test_terms_are_the_records_namespaced_names(profile):
    value = procedure(definition="prose/fake", parameters={"x": "hidden/term"}, compatible_with=(PID,), evidence=(AID,))
    assert record_terms(value, profile) == (
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
        "testing/instrument",
    )
    assert record_references(value, profile) == ()
    assert walk(
        AssumptionInstance("testing/proxy-validity", {"record": PID, "hint": "other/sort"}), profile
    ).terms == frozenset({"testing/proxy-validity"})
    register = AssumptionsRegister("testing:" + "f" * 64, "assumptions-register:" + "e" * 64, {})
    assert walk(register, profile).terms == frozenset()
    records = Records(register)
    assert read_record(records, records.put(register)) == register


def test_a_rule_cited_only_inside_validated_in_is_frozen(profile):
    rule = ClassificationRule("testing/stage", (OBS,), "Classify.", None, None, None)
    records = Records(rule)
    rule_id = records.put(rule)
    restriction = RuleRestriction(rule_id, ("member/opaque",))
    proc = procedure(validated_in={"testing/population": restriction})
    proc_id = records.put(proc)
    p = proxy(
        source=ProxySource(OBS, proc_id),
        validity={"testing/population": UnionRestriction((restriction, RuleRestriction(rule_id, ("second",))))},
    )
    entries = dependency_closure([records.put(p)], records, profile)
    assert {entry.id for entry in entries} == {rule_id, proc_id, records.put(p)}
    assert next(entry.terms for entry in entries if entry.id == rule_id) == (
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
        "testing/stage",
    )
    assert "member/opaque" not in record_terms(proc, profile)


def test_terms_reached_only_through_nested_values_are_present(profile):
    value = procedure(
        yields=(Observable("testing/energy", "secondpack/entity"),),
        validated_in={
            "testing/follow-up": IntervalRestriction("secondpack/hour", Fraction(0), None, True, False),
            "testing/population": TermRestriction("secondpack/cohort", "EX:a"),
            "testing/period": TimeIntervalRestriction("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"),
        },
    )
    assert record_terms(value, profile) == (
        "secondpack/cohort",
        "secondpack/duration",
        "secondpack/entity",
        "secondpack/hour",
        "testing/energy",
        "testing/follow-up",
        "testing/instrument",
        "testing/period",
        "testing/population",
    )


def test_calendar_convention_freezes_conversion_endpoints_and_quantity_kind(profile):
    scope = {
        "testing/follow-up": UnionRestriction(
            (
                IntervalRestriction(
                    "testing/calendar-month", Fraction(0), Fraction(1), True, True, "testing/mean-month"
                ),
                IntervalRestriction("testing/calendar-month", Fraction(2), None, True, False, "testing/mean-month"),
            )
        )
    }
    result = walk(scope, profile)
    assert result.references == frozenset()
    assert result.terms == frozenset(
        {
            "testing/follow-up",
            "testing/calendar-month",
            "testing/mean-month",
            "testing/mean-month-to-second",
            "testing/second",
            "testing/duration",
        }
    )


def test_an_unheld_reference_refuses(profile):
    records = Records(procedure(scale=SameAs(PID)))
    with pytest.raises(errors.DependencyNotHeld):
        dependency_closure(records.nodes, records, profile)
    with pytest.raises(errors.DependencyNotHeld):
        dependency_closure([AID], records, profile)


def test_a_cycle_refuses(profile, monkeypatch):
    # Real content hashes cannot encode a same_as cycle without a hash fixed point.
    other = "procedure:" + "b" * 64
    decoded = {PID: procedure(scale=SameAs(other)), other: procedure(scale=SameAs(PID))}

    def decode(records, id):
        return decoded[id]

    monkeypatch.setattr(dependencies, "read_record", decode)
    with pytest.raises(errors.DependencyCycle):
        dependency_closure([PID], Records(), profile)


def test_forged_raw_addresses_still_refuse(profile):
    records = Records()
    records.nodes[PID] = node_for("procedure", PID, procedure_projection(procedure(scale=SameAs(PID))))
    with pytest.raises(errors.MalformedRecord):
        dependency_closure([PID], records, profile)


def test_real_held_view_freezes_transitive_rule_and_authority(certified_work):
    writer = _testing_writer(certified_work / "dependency-world")
    rule = writer.add(
        stored.classification_rule_node(ClassificationRule("testing/level", (OBS,), "Classify.", None, None, None))
    )
    authority = writer.add(
        stored.procedure_node(procedure(name="held authority", scale=Scale(Fraction(0), Fraction(1), "higher-is-more")))
    )
    follower = writer.add(
        stored.procedure_node(
            procedure(
                scale=SameAs(authority.id), validated_in={"testing/case-status": RuleRestriction(rule.id, ("EX:a",))}
            )
        )
    )

    class HeldView(Records):
        def holds(self, id):
            return writer.read_view.holds(id)

        def read(self, id):
            return writer.read_view.get(id)

    result = dependency_closure([follower.id], HeldView(), writer.profile)
    assert {entry.id for entry in result} == {follower.id, authority.id, rule.id}
    assert next(entry.terms for entry in result if entry.id == follower.id) == (
        "testing/case-status",
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
        "testing/instrument",
    )


def test_calibration_transfer_walks_kind_but_not_opaque_particulars(profile):
    transfer = AssumptionInstance(
        "testing/calibration-transfer",
        {"proxy": "opaque/world", "calibrated_observable": "prose/value", "target_observable": "another/opaque"},
    )
    value = proxy(
        target=ProxyTarget(Observable("testing/abundance", "testing/entity"), None),
        basis=Calibration(OBS, (AID,), ("not/a-term",), transfer),
    )
    assert walk(value, profile).terms == frozenset(
        {
            "testing/energy",
            "testing/event",
            "testing/energy-aspect",
            "testing/abundance",
            "testing/entity",
            "testing/calibration-transfer",
        }
    )
    assert record_references(value, profile) == (AID, PID)


def test_reader_refuses_misdirected_node_and_unsupported_kind():
    records = Records(procedure())
    records.nodes[PID] = next(iter(records.nodes.values()))
    with pytest.raises(errors.MalformedRecord):
        read_record(records, PID)
    other = "dataset:" + "d" * 64
    records.nodes[other] = Node(id=other, kind="dataset", title="Not a measurement dependency")
    with pytest.raises(errors.MalformedRecord):
        read_record(records, other)
