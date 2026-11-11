"""Local eligibility and complete dependency eligibility use the supplied snapshot."""

from fractions import Fraction

import pytest
import test_stored
from fixtures_cut3 import TESTING_PROFILE
from fixtures_cut4 import reopen
from test_dependencies import Records
from test_procedure import AID, DIGEST, OBS, PID, node_for, procedure
from test_proxy_model import proxy
from test_stored import _testing_writer

from beliefs import dependencies, eligibility, errors, stored
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.corpus import standing_in_local_view
from beliefs.dependencies import dependency_closure
from beliefs.eligibility import Eligible, Ineligible, closure_eligibility, dependency_eligibility
from beliefs.procedure import ModelInputs, SameAs, Scale, procedure_projection
from beliefs.profile import compile_profile
from beliefs.proxy_model import Calibration, Conversion, Crosswalk, Error, ProxySource, ProxyTarget
from beliefs.referent_mapping import ReferentMapping
from beliefs.register import AssumptionsRegister
from beliefs.restriction import RuleRestriction, UnionRestriction


class SnapshotRecords(Records):
    def __init__(self, view):
        super().__init__()
        # ReadView is live; capture validated records and folded standing together.
        self.nodes = {node.id: view.get(node.id) for node in view.iter_stored()}
        self.retracted = {id for id in self.nodes if not standing_in_local_view(view, id)}

    def retraction_in_force(self, id):
        return id in self.retracted


def retract(writer, target):
    ground = writer.add(stored.source_node(title="Ground", identifiers={"doi": "10.1234/eligibility"}))
    digest = stored.stored_semantic_hash(target)
    assert digest is not None
    writer.retract(
        stored.retraction_node(
            title="Retract dependency",
            target=stored.NodeTarget(target.id, target.id, digest),
            reason="authored-error",
            rationale="Incorrect dependency",
            grounds=(ground.id,),
            actor=writer.authority.actor,
            event_token=target.id,
        )
    )


@pytest.mark.parametrize(
    "kind", ["procedure", "classification-rule", "referent-mapping", "assumptions-register", "proxy-model"]
)
def test_retraction_changes_only_the_later_snapshot(certified_work, kind):
    writer = _testing_writer(certified_work / kind)
    register = AssumptionsRegister("testing:" + writer.profile.activated_contracts["testing"], None, {})
    if kind != "assumptions-register":
        writer.add(stored.assumptions_register_node(register))
    source = writer.add(stored.procedure_node(procedure(name="Source")))
    values = {
        "procedure": stored.procedure_node(procedure()),
        "classification-rule": stored.classification_rule_node(
            ClassificationRule("testing/level", (OBS,), "Classify.", None, None, None)
        ),
        "referent-mapping": stored.referent_mapping_node(
            ReferentMapping("testing/event", "testing/entity", {}, "many-to-one", "testing/sum", None)
        ),
        "assumptions-register": stored.assumptions_register_node(register),
        "proxy-model": stored.proxy_model_node(
            proxy(
                source=ProxySource(OBS, source.id),
                basis=AssumptionInstance(
                    "testing/proxy-validity", {"record": "proxy", "co_scope": "equal", "dimensions": "{}"}
                ),
            )
        ),
    }
    target = writer.add(values[kind])
    before = SnapshotRecords(reopen(writer.root))
    assert dependency_eligibility([target.id], before, writer.profile) == {target.id: Eligible()}
    retract(writer, target)
    after = SnapshotRecords(reopen(writer.root))
    assert dependency_eligibility([target.id], after, writer.profile) == {target.id: Ineligible("retracted")}
    assert dependency_eligibility([target.id], before, writer.profile) == {target.id: Eligible()}


def test_unheld_ids_are_not_held_and_requested_ids_appear_once():
    result = dependency_eligibility(iter([PID, AID, PID]), Records(), TESTING_PROFILE)
    assert result == {PID: Ineligible("not-held"), AID: Ineligible("not-held")}
    assert dependency_eligibility([], Records(), TESTING_PROFILE) == {}


@pytest.mark.parametrize("held", [(), (DIGEST,), ("sha256:" + "d" * 64,), (DIGEST, "sha256:" + "d" * 64)])
def test_model_specifications_need_every_dataset_and_code_observation(held):
    code = "sha256:" + "d" * 64

    class Observations(Records):
        def observation_held(self, digest):
            return digest in held

    records = Observations(procedure(kind="testing/model-specification", inputs=ModelInputs((DIGEST,), (code,))))
    id = next(iter(records.nodes))
    expected = Eligible() if len(held) == 2 else Ineligible("model-not-held")
    assert dependency_eligibility([id], records, TESTING_PROFILE) == {id: expected}


def test_model_with_no_observations_to_require_is_eligible():
    records = Records(procedure(kind="testing/model-specification", inputs=ModelInputs((), ())))
    id = next(iter(records.nodes))
    assert dependency_eligibility([id], records, TESTING_PROFILE) == {id: Eligible()}


def test_assumption_basis_proxy_needs_only_its_own_heldness():
    records = Records(proxy())  # Its source is deliberately absent.
    id = next(iter(records.nodes))
    assert dependency_eligibility([id], records, TESTING_PROFILE) == {id: Eligible()}
    assert closure_eligibility([id], records, TESTING_PROFILE).verdicts == {id: Ineligible("not-held")}


def calibration_records(*assessment_ids):
    records = Records(procedure())
    source = next(iter(records.nodes))
    id = records.put(
        proxy(source=ProxySource(OBS, source), basis=Calibration(OBS, assessment_ids, ("opaque/rule",), None))
    )
    from fixtures_cut3 import MEASUREMENT_RECORDS, typed_target

    target = typed_target()
    for entry in target.dependencies:
        records.nodes[entry.id] = MEASUREMENT_RECORDS.nodes[entry.id]
    for assessment in assessment_ids:
        records.nodes[assessment] = stored.assessment_node(
            assessment.partition(":")[2],
            title="Calibration",
            spec="s",
            run="run:r",
            proposition="p",
            outcome="supported",
            interpretation_rule="rule",
            target=target,
        )
    return records, id


def test_calibration_without_supplied_assessment_eligibility_fails_closed():
    records, id = calibration_records(AID)
    assert dependency_eligibility([id], records, TESTING_PROFILE) == {id: Ineligible(f"basis-ineligible: {AID}")}
    assert dependency_eligibility([AID], records, TESTING_PROFILE) == {
        AID: Ineligible("basis-ineligible: assessment eligibility not supplied")
    }
    result = closure_eligibility(
        [id],
        records,
        TESTING_PROFILE,
        assessment_dependency=lambda aid: stored.frozen_assessment_dependency(
            aid, records=records, profile=TESTING_PROFILE
        ),
    )
    assert result.verdicts == {id: Ineligible(f"dependency-ineligible: {AID}")}
    assert result.reads == tuple(sorted((*records.nodes,)))


@pytest.mark.parametrize("accepted", [True, False])
def test_calibration_follows_supplied_assessment_eligibility(accepted):
    other = "assessment:" + "d" * 64
    records, id = calibration_records(other, AID)

    def assessments(assessment):
        assert assessment in (AID, other)
        return Eligible() if accepted or assessment == AID else Ineligible("not-verified", ("verification:missing",))

    expected = Eligible() if accepted else Ineligible(f"basis-ineligible: {other}", ("verification:missing",))
    assert dependency_eligibility([id], records, TESTING_PROFILE, assessments=assessments) == {id: expected}
    result = closure_eligibility(
        [id],
        records,
        TESTING_PROFILE,
        assessments=assessments,
        assessment_dependency=lambda aid: stored.frozen_assessment_dependency(
            aid, records=records, profile=TESTING_PROFILE
        ),
    )
    assert result.verdicts == {id: Eligible() if accepted else Ineligible(f"dependency-ineligible: {other}")}
    assert result.reads == tuple(sorted(records.nodes))


def test_calibration_reports_first_ineligible_assessment_in_id_order():
    other = "assessment:" + "d" * 64
    records, id = calibration_records(other, AID)
    result = dependency_eligibility([id], records, TESTING_PROFILE, assessments=lambda _: Ineligible("refused"))
    assert result == {id: Ineligible(f"basis-ineligible: {AID}")}


@pytest.mark.parametrize("placement", ["proxy", "authority"])
def test_closure_sees_a_rule_retracted_only_inside_a_nested_scope(
    certified_work, placement, base_contract, testing_document, monkeypatch
):
    declaration = testing_document["dimensions"]["case-status"]
    declaration["restriction"] = {"form": "union", "of": declaration["restriction"]}
    profile = compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<eligibility-union>", base=base_contract, predecessor=None)],
    )
    monkeypatch.setattr(test_stored, "TESTING_PROFILE", profile)
    writer = _testing_writer(certified_work / placement)
    writer.add(
        stored.assumptions_register_node(
            AssumptionsRegister("testing:" + writer.profile.activated_contracts["testing"], None, {})
        )
    )
    rule = writer.add(
        stored.classification_rule_node(ClassificationRule("testing/level", (OBS,), "Classify.", None, None, None))
    )
    scope = {
        "testing/case-status": UnionRestriction(
            (RuleRestriction(rule.id, ("EX:a",)), RuleRestriction(rule.id, ("EX:b",)))
        )
    }
    scale = Scale(Fraction(0), Fraction(100), "higher-is-more")
    a = writer.add(
        stored.procedure_node(procedure(name="A", scale=scale, validated_in=scope if placement == "authority" else {}))
    )
    b = writer.add(stored.procedure_node(procedure(name="B", scale=scale)))
    crosswalk = writer.add(
        stored.proxy_model_node(
            proxy(
                source=ProxySource(OBS, a.id),
                target=ProxyTarget(None, b.id),
                validity=scope if placement == "proxy" else {},
                basis=AssumptionInstance(
                    "testing/proxy-validity", {"record": "crosswalk", "co_scope": "equal", "dimensions": "{}"}
                ),
                crosswalk=Crosswalk(
                    {}, Conversion("affine", Fraction(1), Fraction(0)), Error("standard-error", Fraction(0))
                ),
            )
        )
    )
    before = SnapshotRecords(reopen(writer.root))
    frozen = dependency_closure([crosswalk.id], before, writer.profile)
    expected_reads = tuple(sorted((crosswalk.id, a.id, b.id, rule.id)))
    assert closure_eligibility([crosswalk.id], before, writer.profile).verdicts == {crosswalk.id: Eligible()}
    retract(writer, rule)
    after = SnapshotRecords(reopen(writer.root))
    assert dependency_eligibility([crosswalk.id], after, writer.profile) == {crosswalk.id: Eligible()}
    result = closure_eligibility([crosswalk.id], after, writer.profile)
    assert result.verdicts == {crosswalk.id: Ineligible(f"dependency-ineligible: {rule.id}")}
    assert result.reads == expected_reads
    assert closure_eligibility([crosswalk.id], before, writer.profile).verdicts == {crosswalk.id: Eligible()}
    assert dependency_closure([crosswalk.id], after, writer.profile) == frozen
    assert next(entry.terms for entry in frozen if entry.id == rule.id) == (
        "testing/energy",
        "testing/energy-aspect",
        "testing/event",
        "testing/level",
    )


def test_cycle_members_are_locally_ineligible_and_ancestor_is_only_aggregate_ineligible(monkeypatch):
    other = "procedure:" + "b" * 64
    ancestor = "procedure:" + "e" * 64
    # Hash-valid same_as cycles require a fixed point: replace only typed decoding.
    decoded = {
        PID: procedure(scale=SameAs(other)),
        other: procedure(scale=SameAs(PID)),
        ancestor: procedure(scale=SameAs(PID)),
    }
    records = Records()
    records.nodes = {id: node_for("procedure", id, procedure_projection(value)) for id, value in decoded.items()}

    def decode(records, id):
        assert records.holds(id)
        return decoded[id]

    monkeypatch.setattr(dependencies, "read_record", decode)
    monkeypatch.setattr(eligibility, "read_record", decode)
    assert dependency_eligibility(decoded, records, TESTING_PROFILE) == {
        PID: Ineligible("cycle"),
        other: Ineligible("cycle"),
        ancestor: Eligible(),
    }
    result = closure_eligibility([ancestor], records, TESTING_PROFILE)
    assert result.verdicts == {ancestor: Ineligible("cycle")}
    assert result.reads == tuple(sorted(decoded))


def test_forged_raw_addresses_still_refuse():
    records = Records()
    records.nodes[PID] = node_for("procedure", PID, procedure_projection(procedure(scale=SameAs(PID))))
    for check in (dependency_eligibility, closure_eligibility):
        with pytest.raises(errors.MalformedRecord):
            check([PID], records, TESTING_PROFILE)


def test_failed_closure_retains_unheld_members_and_other_requested_roots():
    records = Records(procedure(name="Independent"), proxy())
    ids = tuple(records.nodes)
    result = closure_eligibility(iter([*ids, ids[0]]), records, TESTING_PROFILE)
    assert result.verdicts == {ids[0]: Eligible(), ids[1]: Ineligible("not-held")}
    assert result.reads == tuple(sorted((*ids, PID)))
    missing = closure_eligibility([AID, AID], Records(), TESTING_PROFILE)
    assert missing.verdicts == {AID: Ineligible("not-held")}
    assert missing.reads == (AID,)
    assert closure_eligibility([], records, TESTING_PROFILE).reads == ()


def test_closure_names_first_ineligible_member_in_id_order():
    class Retracted(Records):
        def retraction_in_force(self, id):
            return True

    records = Retracted(procedure())
    source = next(iter(records.nodes))
    records.put(proxy(source=ProxySource(OBS, source)))
    ids = tuple(records.nodes)
    result = closure_eligibility([ids[1]], records, TESTING_PROFILE)
    assert result.verdicts == {ids[1]: Ineligible(f"dependency-ineligible: {min(ids)}")}
    assert result.reads == tuple(sorted(ids))
