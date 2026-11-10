"""Measurement records mint only with canonical facets and profile-qualified meaning."""

from dataclasses import replace
from fractions import Fraction
from typing import Any, cast

import pytest
from authority import FULL
from fixtures_cut4 import raw_write, reopen
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from test_procedure import OBS, PID, procedure
from test_proxy_model import CROSSWALK, proxy
from test_stored import _testing_writer

from beliefs import errors, stored
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule, rule_from_stored
from beliefs.contract.base import parse_base_contract
from beliefs.contract.document import load_document
from beliefs.contract.domain import parse_domain_contract
from beliefs.corpus import CorpusWriter, corpus_check, retraction_standing
from beliefs.measurement import Aspect, Measure, check_measure_procedure
from beliefs.procedure import ModelInputs, SameAs, Scale, procedure_from_stored
from beliefs.profile import compile_profile
from beliefs.proxy_model import Calibration, ProxySource, ProxyTarget, proxy_from_stored
from beliefs.referent_mapping import ReferentMapping, mapping_from_stored
from beliefs.register import AssumptionsRegister
from beliefs.restriction import IntervalRestriction, TermRestriction, type_restriction_map

KINDS = ("procedure", "referent-mapping", "proxy-model", "classification-rule")
BASIS = AssumptionInstance("testing/proxy-validity", {"record": "proxy", "co_scope": "equal", "dimensions": "{}"})


def values():
    return (
        procedure(),
        ReferentMapping("testing/event", "testing/entity", {}, "many-to-one", "testing/sum", None),
        proxy(basis=BASIS),
        ClassificationRule("testing/stage", (OBS,), "Assign the observed stage.", None, None, None),
    )


def build(kind, value, **kwargs):
    return getattr(stored, kind.replace("-", "_") + "_node")(value, **kwargs)


def held_values(writer):
    items = values()
    source = writer.add(build("procedure", replace(items[0], name="Held source")))
    return (*items[:2], replace(items[2], source=ProxySource(OBS, source.id)), items[3])


@pytest.mark.parametrize(
    "kind,index,reader",
    [
        (k, i, r)
        for i, (k, r) in enumerate(
            zip(KINDS, (procedure_from_stored, mapping_from_stored, proxy_from_stored, rule_from_stored), strict=True)
        )
    ],
)
def test_each_kind_mints_through_add_and_reads_back(certified_work, kind, index, reader):
    writer = _testing_writer(certified_work / "corpus")
    writer.add(
        stored.assumptions_register_node(
            AssumptionsRegister("testing:" + writer.profile.activated_contracts["testing"], None, {})
        )
    )
    value = held_values(writer)[index]
    node = writer.add(build(kind, value))
    view = reopen(writer.root)
    assert reader(view.get(node.id)) == value
    assert corpus_check(view, writer.profile) == ()


@pytest.mark.parametrize("kind,index", list(zip(KINDS, range(4), strict=True)))
def test_byte_identical_facets_share_one_id_and_a_field_change_is_a_new_record(tmp_path, kind, index):
    value = values()[index]
    changes = (
        {"name": "Other"},
        {"cardinality": "one-to-one"},
        {"validity": {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(1), None, True, False)}},
        {"definition": "Other"},
    )
    assert build(kind, value).id == build(kind, value, body="Display only").id
    assert build(kind, value).id != build(kind, replace(value, **changes[index])).id


@pytest.mark.parametrize("kind", (*KINDS, "assumptions-register"))
def test_a_record_missing_its_required_facet_is_refused(tmp_path, kind):
    writer = _testing_writer(tmp_path / "corpus")
    with pytest.raises(errors.ValidationRefused, match="facet"):
        writer.add(Node(id=f"{kind}:" + "a" * 64, kind=kind, title="Missing"))


def test_staging_refuses_a_governed_kind_that_declares_no_facet(tmp_path, base_contract_path, monkeypatch):
    document = cast(dict[str, Any], load_document(base_contract_path, source="<facetless>"))
    document["kinds"]["procedure"]["facets"] = {}
    base = parse_base_contract(document, source="<facetless>")
    profile = compile_profile(base, [])
    monkeypatch.setattr("beliefs.corpus.shipped_base", lambda: profile)
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=profile)
    node = stored.stamp_semantic_identity(Node(id=PID, kind="procedure", title="Empty"))
    with pytest.raises(errors.KindNotMintedHere, match="procedure"):
        writer._stage_record(node_to_markdown(node))


@pytest.mark.parametrize("kind,index", list(zip(KINDS, range(4), strict=True)))
def test_a_malformed_facet_is_refused_at_add_and_reported_by_corpus_check(tmp_path, kind, index):
    writer = _testing_writer(tmp_path / "corpus")
    node = build(kind, values()[index])
    node.facets[kind]["extra"] = "noncanonical"
    with pytest.raises(errors.MalformedRecord):
        writer.add(node)
    raw_write(writer.root, node)
    findings = corpus_check(reopen(writer.root), writer.profile)
    assert any(f.code == "facet-payload-malformed" and kind in f.detail for f in findings)


@pytest.mark.parametrize(
    "changes,clause",
    [
        ({"kind": "testing/unknown"}, "kind"),
        ({"yields": (replace(OBS, aspect=Aspect("testing/stage", "EX:a")),)}, "yields"),
        ({"validated_in": {"testing/follow-up": TermRestriction("testing/stage", "EX:a")}}, "validated_in"),
        ({"inputs": ModelInputs((), ())}, "inputs"),
        ({"kind": "testing/model-specification"}, "inputs"),
        ({"scale": SameAs(PID)}, "same_as"),
    ],
)
def test_procedure_door_checks(tmp_path, changes, clause):
    writer = _testing_writer(tmp_path / "corpus")
    node = build("procedure", procedure(**changes))
    with pytest.raises(errors.MeasurementRecordRefused, match=clause) as raised:
        writer.add(node)
    assert node.id in str(raised.value)


def test_same_as_refuses_a_held_non_authority_and_a_non_procedure(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    target = writer.add(build("procedure", procedure()))
    with pytest.raises(errors.MeasurementRecordRefused, match="same_as"):
        writer.add(build("procedure", procedure(name="Copy", scale=SameAs(target.id))))
    with pytest.raises(errors.MalformedRecord):
        SameAs("source:" + "a" * 64)


def test_a_same_as_procedure_measures_on_the_authority_scale(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    authority = procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-more"))
    target = writer.add(build("procedure", authority))
    copy = procedure(name="Copy", scale=SameAs(target.id))
    writer.add(build("procedure", copy))
    measure = Measure(OBS, None, target.id, "interval", "level", "testing/identity", build("procedure", copy).id)
    check_measure_procedure(measure, copy, authority)


def test_procedure_scope_does_not_acquire_operator_semantics(tmp_path, base_contract, testing_document):
    testing_document["dimensions"]["follow-up"]["applies_to"] = []
    contract = parse_domain_contract(testing_document, source="<no-operator>", base=base_contract, predecessor=None)
    profile = compile_profile(base_contract, [contract])
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=profile)
    value = procedure(
        validated_in={"testing/follow-up": IntervalRestriction("testing/hour", Fraction(1), None, True, False)}
    )
    assert writer.add(build("procedure", value)).id == build("procedure", value).id


@pytest.mark.parametrize("kind", ["procedure", "proxy-model"])
def test_scope_requires_pretyping_a_local_calendar_convention(tmp_path, kind):
    writer = _testing_writer(tmp_path / "corpus")
    source = writer.add(build("procedure", procedure()))
    scope = {
        "testing/follow-up": IntervalRestriction("testing/calendar-month", Fraction(1), None, True, False, "mean-month")
    }
    field = "validated_in" if kind == "procedure" else "validity"
    value = (
        procedure(**{field: scope})
        if kind == "procedure"
        else proxy(source=ProxySource(OBS, source.id), basis=BASIS, **{field: scope})
    )
    node = build(kind, value)
    with pytest.raises(errors.MeasurementRecordRefused, match="type_restriction_map"):
        writer.add(node)
    raw = node.facets[kind][field]
    typed = type_restriction_map(writer.profile, raw)
    resolved = replace(value, **{field: typed})
    minted = writer.add(build(kind, resolved))
    assert minted.facets[kind][field]["testing/follow-up"]["convention"] == "testing/mean-month"
    assert build(kind, value).id != minted.id


@pytest.mark.parametrize(
    "changes,clause",
    [
        ({"source": ProxySource(OBS, PID)}, "source.procedure"),
        ({"basis": AssumptionInstance("testing/proxy-validity", {})}, "basis"),
        ({"target": ProxyTarget(None, PID), "crosswalk": CROSSWALK}, "scale_of"),
        ({"target": ProxyTarget(replace(OBS, quantity_kind="testing/unknown"), None)}, "target.observable"),
        ({"validity": {"testing/follow-up": TermRestriction("testing/stage", "EX:a")}}, "validity"),
    ],
)
def test_proxy_door_checks(tmp_path, changes, clause):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    node = build("proxy-model", replace(value, **changes))
    with pytest.raises(errors.MeasurementRecordRefused, match=clause):
        writer.add(node)


def test_proxy_refuses_invalid_transfer_particulars(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    value = replace(
        value,
        target=ProxyTarget(replace(OBS, aspect=None), None),
        basis=Calibration(
            OBS, (), ("beliefs/outcome-file/v1",), AssumptionInstance("testing/calibration-transfer", {})
        ),
    )
    with pytest.raises(errors.MeasurementRecordRefused, match="transfer"):
        writer.add(build("proxy-model", value))


@pytest.mark.parametrize(
    "kind,index,changes,clause",
    [
        ("referent-mapping", 1, {"source_sort": "testing/unknown"}, "source_sort"),
        ("referent-mapping", 1, {"target_sort": "testing/unknown"}, "target_sort"),
        ("referent-mapping", 1, {"aggregation": "testing/unknown"}, "aggregation"),
        ("classification-rule", 3, {"classes": "testing/unknown"}, "classes"),
        ("classification-rule", 3, {"reads": (replace(OBS, aspect=Aspect("testing/stage", "EX:a")),)}, "reads"),
    ],
)
def test_mapping_and_classification_doors_check_the_profile(tmp_path, kind, index, changes, clause):
    writer = _testing_writer(tmp_path / "corpus")
    with pytest.raises(errors.MeasurementRecordRefused, match=clause):
        writer.add(build(kind, replace(values()[index], **changes)))


@pytest.mark.parametrize("kind,index", list(zip((*KINDS, "assumptions-register"), range(5), strict=True)))
def test_retraction_of_each_kind_writes_and_is_in_force(tmp_path, kind, index):
    writer = _testing_writer(tmp_path / "corpus")
    register = AssumptionsRegister("testing:" + writer.profile.activated_contracts["testing"], None, {})
    value = (*held_values(writer), register)[index]
    target = writer.add(build(kind, value))
    if kind != "assumptions-register":
        writer.add(stored.assumptions_register_node(register))
    writer.add(stored.source_node(title="Ground", identifiers={"doi": "10.1234/ground"}))
    # Retraction grounds are held and admissible evidence.
    ground = next(n.id for n in writer.read_view.iter_stored() if n.kind == "source")
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    retraction = stored.retraction_node(
        title="Retract",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="authored-error",
        rationale="Incorrect",
        grounds=(ground,),
        actor=writer.authority.actor,
        event_token="one",
    )
    result = writer.retract(retraction)
    standing = retraction_standing(writer.read_view, {result.id: writer._validated_retraction(result)})
    assert standing[target.id] is False and standing[result.id] is True
    assert corpus_check(reopen(writer.root), writer.profile) == ()


def test_procedure_accepts_model_inputs_and_well_formed_unheld_compatibility_and_evidence(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    value = procedure(
        kind="testing/model-specification",
        inputs=ModelInputs((), ()),
        compatible_with=(PID,),
        evidence=("assessment:" + "a" * 64,),
    )
    assert procedure_from_stored(writer.add(stored.procedure_node(value))) == value


def test_proxy_scale_target_requires_authority_and_accepts_held_authority(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    source = writer.add(stored.procedure_node(procedure()))
    value = proxy(
        source=ProxySource(OBS, source.id), target=ProxyTarget(None, source.id), crosswalk=CROSSWALK, basis=BASIS
    )
    with pytest.raises(errors.MeasurementRecordRefused, match="scale_of"):
        writer.add(stored.proxy_model_node(value))
    authority = writer.add(stored.procedure_node(procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-more"))))
    source = writer.add(stored.procedure_node(procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-less"))))
    value = replace(value, source=ProxySource(OBS, source.id), target=ProxyTarget(None, authority.id))
    assert proxy_from_stored(writer.add(stored.proxy_model_node(value))) == value


def test_proxy_checks_source_and_calibration_transfer_particulars(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    source = writer.add(stored.procedure_node(procedure()))
    basis = held_calibration(writer, tmp_path / "run")
    value = proxy(source=ProxySource(OBS, source.id), basis=basis)
    assert proxy_from_stored(writer.add(stored.proxy_model_node(value))) == value
    bad_source = replace(value, source=ProxySource(replace(OBS, quantity_kind="testing/unknown"), source.id))
    with pytest.raises(errors.MeasurementRecordRefused, match="source.observable"):
        writer.add(stored.proxy_model_node(bad_source))
    target = replace(OBS, aspect=None)
    transfer = AssumptionInstance(
        "testing/calibration-transfer",
        {"proxy": "model", "calibrated_observable": "energy", "target_observable": "energy without aspect"},
    )
    value = replace(value, target=ProxyTarget(target, None), basis=replace(basis, transfer=transfer))
    assert proxy_from_stored(writer.add(stored.proxy_model_node(value))) == value


def held_calibration(writer, work, *, outcome="supported", applicability=None):
    """Carry a real interim spec/run/assessment derivation into the held fixture."""
    from fixtures_cut3 import interp, memory_assessment, spec_draft, spec_rules, typed_applicability

    from beliefs.assess import AssessmentFinding, build_assessment
    from beliefs.boundary import RunMinted
    from beliefs.spec import freeze

    spec = freeze(spec_draft(applicability=typed_applicability(applicability)), held_rules=spec_rules())
    raw_write(writer.root, stored.analysis_spec_node(spec))
    executed = memory_assessment(work, spec=spec)
    assert isinstance(executed, RunMinted), executed
    assessment = build_assessment(executed.run, specs={spec.identity: spec}, implementations=interp(outcome))
    assert not isinstance(assessment, AssessmentFinding), assessment
    node = stored.assessment_node(
        assessment.identity(),
        title="Calibration evidence",
        spec=assessment.spec,
        run=stored.typed_ref("run", assessment.run),
        proposition=assessment.proposition,
        outcome=assessment.outcome,
        interpretation_rule=assessment.interpretation_rule,
        estimand=assessment.estimand,
        applicability=assessment.applicability,
        estimate=assessment.estimate,
        uncertainty=assessment.uncertainty,
    )
    raw_write(writer.root, node)
    writer._reconstruct()
    return Calibration(OBS, (node.id,), (assessment.interpretation_rule,), None)


@pytest.mark.parametrize("outcome", ["refuted", "inconclusive"])
def test_a_calibration_needs_supported_assessments(tmp_path, outcome):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = held_calibration(writer, tmp_path / "run", outcome=outcome)
    with pytest.raises(errors.MeasurementRecordRefused, match="calibration-not-supported"):
        writer.add(build("proxy-model", replace(value, basis=basis)))


@pytest.mark.parametrize(
    "assessment_stage,validity_stage,admitted",
    [
        ("EX:early", None, False),
        (None, "EX:early", True),
        ("EX:early", "EX:late", False),
        ("EX:early", "EX:early", True),
    ],
)
def test_a_calibration_scope_narrower_than_validity_refuses(tmp_path, assessment_stage, validity_stage, admitted):
    from beliefs.claim import Qualifier, Referent

    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    applicability = (
        {}
        if assessment_stage is None
        else {"testing/stage": Qualifier("generic", Referent("testing/stage", assessment_stage))}
    )
    basis = held_calibration(writer, tmp_path / "run", applicability=applicability)
    validity = {} if validity_stage is None else {"testing/stage": TermRestriction("testing/stage", validity_stage)}
    node = build("proxy-model", replace(value, basis=basis, validity=validity))
    if admitted:
        assert writer.add(node).id == node.id
    else:
        with pytest.raises(errors.MeasurementRecordRefused, match="calibration-scope-overstated"):
            writer.add(node)


def test_a_v1_term_on_an_interval_dimension_is_undecidable(tmp_path):
    from beliefs.claim import Qualifier, Referent

    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = held_calibration(
        writer,
        tmp_path / "run",
        applicability={"testing/follow-up": Qualifier("generic", Referent("testing/level", "EX:five-years"))},
    )
    with pytest.raises(errors.MeasurementRecordRefused, match="calibration-scope-undecidable"):
        writer.add(build("proxy-model", replace(value, basis=basis)))


def test_a_qualified_proxy_mints(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = held_calibration(writer, tmp_path / "run")
    transfer = AssumptionInstance(
        "testing/calibration-transfer",
        {"proxy": "model", "calibrated_observable": "energy", "target_observable": "without aspect"},
    )
    value = replace(value, basis=replace(basis, transfer=transfer), target=ProxyTarget(replace(OBS, aspect=None), None))
    assert proxy_from_stored(writer.add(build("proxy-model", value))) == value


@pytest.mark.parametrize("empty", [True, False])
def test_a_calibration_needs_held_assessments(tmp_path, empty):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = Calibration(OBS, () if empty else ("assessment:" + "f" * 64,), ("beliefs/outcome-file/v1",), None)
    with pytest.raises(errors.MeasurementRecordRefused, match="calibration"):
        writer.add(build("proxy-model", replace(value, basis=basis)))


def test_a_calibration_needs_a_held_spec(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = held_calibration(writer, tmp_path / "run")
    assessment = writer.read_view.get(basis.assessments[0])
    assessment.facets["assessment"]["spec"] = "f" * 64
    raw_write(writer.root, assessment)
    writer._reconstruct()
    with pytest.raises(errors.MeasurementRecordRefused, match="calibration"):
        writer.add(build("proxy-model", replace(value, basis=basis)))


@pytest.mark.parametrize("reverse_yields", [False, True])
@pytest.mark.parametrize(
    "calibrated_is_yield,transfer_present,admitted",
    [(True, False, True), (True, True, False), (False, True, True), (False, False, False)],
)
def test_scale_calibration_transfer_uses_all_authority_yields(
    tmp_path, calibrated_is_yield, transfer_present, admitted, reverse_yields
):
    writer = _testing_writer(tmp_path / "corpus")
    other = replace(OBS, aspect=None)
    source = writer.add(build("procedure", procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-less"))))
    authority = writer.add(
        build(
            "procedure",
            procedure(
                name="Target",
                yields=((OBS, other) if reverse_yields else (other, OBS)) if calibrated_is_yield else (other,),
                scale=Scale(Fraction(0), Fraction(100), "higher-is-more"),
            ),
        )
    )
    basis = held_calibration(writer, tmp_path / "run")
    transfer = (
        AssumptionInstance(
            "testing/calibration-transfer",
            {"proxy": "model", "calibrated_observable": "energy", "target_observable": "authority yields"},
        )
        if transfer_present
        else None
    )
    value = proxy(
        source=ProxySource(OBS, source.id),
        target=ProxyTarget(None, authority.id),
        crosswalk=CROSSWALK,
        basis=replace(basis, transfer=transfer),
    )
    if admitted:
        assert proxy_from_stored(writer.add(build("proxy-model", value))) == value
    else:
        with pytest.raises(errors.MeasurementRecordRefused, match="calibration-transfer"):
            writer.add(build("proxy-model", value))


def test_a_crosswalk_proxy_mints_between_two_authorities(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    source = writer.add(build("procedure", procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-less"))))
    authority = writer.add(build("procedure", procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-more"))))
    value = proxy(
        source=ProxySource(OBS, source.id), target=ProxyTarget(None, authority.id), crosswalk=CROSSWALK, basis=BASIS
    )
    assert proxy_from_stored(writer.add(build("proxy-model", value))) == value


def test_calibrated_observable_is_profile_checked(tmp_path):
    writer = _testing_writer(tmp_path / "corpus")
    value = held_values(writer)[2]
    basis = Calibration(replace(OBS, quantity_kind="testing/unknown"), (), ("beliefs/outcome-file/v1",), BASIS)
    value = replace(value, basis=basis)
    with pytest.raises(errors.MeasurementRecordRefused, match="calibrated"):
        writer.add(build("proxy-model", value))


@pytest.mark.parametrize("factor", [0, 2])
def test_crosswalk_sign_is_checked_at_the_door(tmp_path, factor):
    from beliefs.proxy_model import Conversion

    writer = _testing_writer(tmp_path / "corpus")
    source = writer.add(build("procedure", procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-less"))))
    target = writer.add(build("procedure", procedure(scale=Scale(Fraction(0), Fraction(100), "higher-is-more"))))
    value = proxy(
        source=ProxySource(OBS, source.id),
        target=ProxyTarget(None, target.id),
        basis=BASIS,
        crosswalk=replace(CROSSWALK, conversion=Conversion("affine", Fraction(factor), Fraction(0))),
    )
    with pytest.raises(errors.MeasurementRecordRefused, match="crosswalk-sign"):
        writer.add(build("proxy-model", value))


@pytest.mark.parametrize("outcome", ["supported", "refuted"])
def test_calibration_reads_assessments_and_specs_through_read_mounts(tmp_path, outcome):
    local = _testing_writer(tmp_path / "local")
    value = held_values(local)[2]
    remote = _testing_writer(tmp_path / "remote")
    basis = held_calibration(remote, tmp_path / "run", outcome=outcome)
    writer = CorpusWriter(
        local.root,
        DefaultExecutor,
        authority=FULL,
        profile=local.profile,
        operation_port=local._operation_port,
        read_mounts=[remote.root],
    )
    node = build("proxy-model", replace(value, basis=basis))
    if outcome == "supported":
        assert writer.add(node).id == node.id
        assert not writer.read_view.holds(basis.assessments[0])
    else:
        with pytest.raises(errors.CalibrationNotQualified, match="calibration-not-supported"):
            writer.add(node)
