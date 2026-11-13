"""Authoring and freezing require fresh bytes, complete graphs and exact inputs."""

from copy import deepcopy
from dataclasses import replace

import pytest
from fixtures_cut3 import (
    ESTIMATOR_PROCEDURE,
    MEASUREMENT_RECORDS,
    RESPONSE,
    TESTING_CLAIM,
    spec_draft,
    spec_rules,
    typed_estimand,
)

from beliefs.claim import Referent
from beliefs.errors import ScienceError
from beliefs.estimand import MeasuredBinding, RoleTermLevels, estimand_from_stored, estimand_projection
from beliefs.series.codec import series_ref_from_projection
from beliefs.spec import SpecInput, freeze
from beliefs.target import target_terms

from .fixtures import SeriesCase, raw_object


def author_case(profile, *, with_series=True, functional="testing/series-contrast", **kwargs):
    case = SeriesCase()
    case.records.nodes.update(MEASUREMENT_RECORDS.nodes)
    table = case.table(
        ["0", "0.01", "0.02"],
        channels={
            "signal": {
                "coordinates": {
                    "quantity_kind": "testing/abundance",
                    "unit": "testing/tpm",
                    "value_type": "level",
                    "transformation": "testing/identity",
                },
                "values": ["1", "2", "3"],
            }
        },
    )
    ref = series_ref_from_projection(case.view(table, [0, 1, 2]))
    bindings = {
        "response": replace(RESPONSE, series=ref if with_series else None),
        "grouping": RoleTermLevels(
            "cause", None, (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd"))
        ),
    }
    value = typed_estimand(
        profile=profile,
        records=case.records,
        functional=functional,
        bindings=bindings,
        series_evidence=case.evidence(),
        **kwargs,
    )
    return case, value


def input_roles(value):
    return tuple(
        SpecInput("reads", row.ref.dataset, "simulation" if row.format == "science.series-table.v1" else "annotation")
        for row in value.series_graph
    )


def frozen(case, value, profile, *, inputs=None, evidence=True):
    return freeze(
        spec_draft(estimand=value, input_roles=input_roles(value) if inputs is None else inputs),
        held_rules=spec_rules(),
        rule_procedures={"median-difference/v1": ESTIMATOR_PROCEDURE},
        profile=profile,
        claim=TESTING_CLAIM,
        records=case.records,
        series_evidence=case.evidence() if evidence else None,
    )


def test_series_is_mandatory_when_required(author_profile):
    from beliefs.series.types import SeriesRefused

    with pytest.raises(SeriesRefused, match="requires"):
        author_case(author_profile, with_series=False)
    _case, value = author_case(author_profile)
    assert value.series_graph
    assert isinstance(value.bindings["response"], MeasuredBinding)
    assert value.bindings["response"].series is not None
    assert "si-brochure/second" in {term for row in value.series_graph for term in row.terms}


def test_every_present_series_is_checked_and_evidence_is_not_a_receipt(author_profile):
    from beliefs.estimand import check_series
    from beliefs.series.evidence import SeriesEvidence
    from beliefs.series.types import SeriesRefused

    case, value = author_case(author_profile, functional="testing/difference-of-means")
    with pytest.raises(SeriesRefused) as caught:
        check_series(value, profile=author_profile, records=case.records, evidence=SeriesEvidence({}, {}))
    assert caught.value.code == "evidence-unavailable"
    assert check_series(value, profile=author_profile, records=case.records, evidence=case.evidence())[0].count == 3


def test_series_target_and_dependency_identity(author_profile):
    from beliefs.dependencies import series_dependency_closure
    from beliefs.estimand import binding_roots

    case, value = author_case(author_profile)
    dataset_ids = {row.ref.dataset for row in value.series_graph}
    entries = [entry for entry in value.dependencies if entry.id in dataset_ids]
    assert len(entries) == 3
    assert all(entry.terms == () and entry.facet_digest is None for entry in entries)
    assert (
        series_dependency_closure(binding_roots(value), value.series_graph, case.records, author_profile)
        == value.dependencies
    )
    projection = estimand_projection(value)
    assert estimand_from_stored(projection, profile=author_profile).series_graph == value.series_graph
    missing = next(iter(dataset_ids))
    case.records.nodes.pop(missing)
    with pytest.raises(ScienceError):
        series_dependency_closure(binding_roots(value), value.series_graph, case.records, author_profile)


def test_freeze_rechecks_all_series_bytes_and_inputs(author_profile):
    from beliefs.series.types import SeriesRefused

    case, value = author_case(author_profile)
    spec = frozen(case, value, author_profile)
    assert {row.dataset for row in spec.input_roles} == {row.ref.dataset for row in value.series_graph}
    assert "si-brochure/second" in target_terms(spec.assessed_target, author_profile)
    with pytest.raises(SeriesRefused):
        frozen(case, value, author_profile, evidence=False)
    case.buffers[next(iter(case.buffers))] = b"corrupt origin"
    with pytest.raises(SeriesRefused):
        frozen(case, value, author_profile)


@pytest.mark.parametrize(
    "change",
    [
        lambda inputs: inputs[1:],
        lambda inputs: (replace(inputs[0], mode="observation", role="observes"), *inputs[1:]),
        lambda inputs: (*inputs, inputs[0]),
    ],
)
def test_missing_misclassified_and_duplicate_graph_inputs_refuse(change, author_profile):
    case, value = author_case(author_profile)
    with pytest.raises(ScienceError):
        frozen(case, value, author_profile, inputs=tuple(change(input_roles(value))))


def test_world_free_graph_and_dependency_tampering_refuses(author_profile):
    _case, value = author_case(author_profile)
    body = estimand_projection(value)
    for change in (
        lambda b: b["dependencies"].pop(),
        lambda b: b["series_graph"].pop(),
        lambda b: b["series_graph"].append(b["series_graph"][0]),
    ):
        malformed = deepcopy(body)
        change(malformed)
        with pytest.raises(ScienceError):
            estimand_from_stored(malformed, profile=author_profile)


def test_selection_member_and_procedure_changes_reach_target_identity(author_profile):
    from beliefs import stored
    from beliefs.applicability import Applicability
    from beliefs.identity import v1
    from beliefs.procedure import procedure_from_stored
    from beliefs.target import AssessedTarget, target_projection

    case, value = author_case(author_profile)

    def rebuild(response):
        return typed_estimand(
            profile=author_profile,
            records=case.records,
            functional=value.functional,
            bindings={**value.bindings, "response": response},
            series_evidence=case.evidence(),
        )

    def identity(estimand):
        return v1.digest(
            "science.assessed-target.v1",
            target_projection(AssessedTarget(estimand, Applicability({}), estimand.dependencies, None, "empirical")),
        )

    original = value.bindings["response"]
    assert isinstance(original, MeasuredBinding) and original.series is not None
    procedure = procedure_from_stored(case.records.read(original.measure.procedure))
    node = stored.procedure_node(replace(procedure, definition="A different measuring procedure."))
    case.records.nodes[node.id] = node
    changed = rebuild(replace(original, measure=replace(original.measure, procedure=node.id)))
    assert isinstance(changed.bindings["response"], MeasuredBinding)
    assert changed.bindings["response"].series == original.series
    assert changed.series_graph == value.series_graph
    assert identity(changed) != identity(value)
    source = raw_object(case.buffers[original.series.resource.split(":")[1]])
    selected = case.view(source["table"], [0, 2], selection_procedure=case.procedure())
    changed = rebuild(replace(original, series=series_ref_from_projection(selected)))
    assert identity(changed) != identity(value)
    refs = case.hold_tree({"one.json": source, "two.json": source})
    one = rebuild(replace(original, series=series_ref_from_projection(refs["one.json"])))
    two = rebuild(replace(original, series=series_ref_from_projection(refs["two.json"])))
    assert one.series_graph != two.series_graph
    assert identity(one) != identity(two)


def event_case(profile):
    from fractions import Fraction

    from beliefs.estimand import LagBinding, RuleAnchor
    from beliefs.restriction import IntervalRestriction

    from .test_geometry import h_case

    case, ref = h_case()
    case.records.nodes.update(MEASUREMENT_RECORDS.nodes)
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])
    table = case.rewrite(
        view["table"],
        lambda obj: obj["channels"]["signal"].update(
            coordinates={
                "quantity_kind": "testing/abundance",
                "unit": "testing/tpm",
                "value_type": "level",
                "transformation": "testing/identity",
            }
        ),
    )
    ref = case.rewrite(ref, lambda obj: obj.update(table=table))
    anchors = raw_object(case.buffers[view["anchors"]["resource"].split(":")[1]])
    bindings = {
        "response": replace(RESPONSE, series=series_ref_from_projection(ref)),
        "anchor": RuleAnchor(anchors["rule"], (Referent("testing/level", "EX:event"),)),
        "lag": LagBinding(
            "si-brochure/hour",
            (
                IntervalRestriction("si-brochure/hour", Fraction(-48), Fraction(0), True, False),
                IntervalRestriction("si-brochure/hour", Fraction(24), Fraction(120), True, False),
            ),
        ),
    }
    return case, bindings


from test_estimand import context as context  # noqa: PLC0414


def test_event_binding_requires_exact_anchor_linkage_and_fixed_lags(context):
    from beliefs.estimand import RoleAnchor
    from beliefs.series.types import SeriesRefused

    case, bindings = event_case(context)

    def build(roles):
        return typed_estimand(
            profile=context,
            records=case.records,
            form="event-locked",
            functional="testing/window-difference-against-control",
            bindings=roles,
            series_evidence=case.evidence(),
        )

    value = build(bindings)
    assert len(value.series_graph) == 4
    with pytest.raises(SeriesRefused):
        build({**bindings, "anchor": replace(bindings["anchor"], classes=(Referent("testing/level", "EX:other"),))})
    with pytest.raises(SeriesRefused):
        build({**bindings, "anchor": RoleAnchor("cause", None, Referent("testing/entity", "EX:a"))})
    original = bindings["response"].series
    assert original is not None
    from beliefs.series.codec import series_ref_projection

    no_anchors = case.rewrite(series_ref_projection(original), lambda obj: obj.pop("anchors"))
    with pytest.raises(SeriesRefused):
        build({**bindings, "response": replace(bindings["response"], series=series_ref_from_projection(no_anchors))})


def test_lag_semantics_checked_at_authoring_and_decoding(context):
    from beliefs.estimand import LagBinding
    from beliefs.identity import v1

    case, bindings = event_case(context)
    good = typed_estimand(
        profile=context,
        records=case.records,
        form="event-locked",
        functional="testing/window-difference-against-control",
        bindings=bindings,
        series_evidence=case.evidence(),
    )
    for unit in ("testing/hour", "testing/calendar-month", "si-brochure/hertz"):
        with pytest.raises(ScienceError):
            typed_estimand(
                profile=context,
                records=case.records,
                form="event-locked",
                functional="testing/window-difference-against-control",
                bindings={**bindings, "lag": LagBinding(unit, ())},
                series_evidence=case.evidence(),
            )
        body = raw_object(v1.encode(estimand_projection(good)))
        body["bindings"]["lag"]["unit"] = unit
        with pytest.raises(ScienceError):
            estimand_from_stored(body, profile=context)


def test_time_role_wrong_dimension_refuses_at_lag_entry(context, base_contract, testing_document):
    from time_roles_fixture import time_document

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile

    document = time_document()
    document["quantity_kinds"]["duration"]["dimension"] = {"T": -1}
    profile = compile_profile(
        base_contract,
        [
            parse_domain_contract(testing_document, source="<event>", base=base_contract, predecessor=None),
            parse_domain_contract(document, source="<wrong dimension>", base=base_contract, predecessor=None),
        ],
    )
    case, bindings = event_case(profile)
    with pytest.raises(ScienceError, match="dimension"):
        typed_estimand(
            profile=profile,
            records=case.records,
            form="event-locked",
            functional="testing/window-difference-against-control",
            bindings=bindings,
            series_evidence=case.evidence(),
        )


def test_wrong_channel_measure_refuses(author_profile):
    from beliefs.series.codec import series_ref_projection
    from beliefs.series.types import SeriesRefused

    case, value = author_case(author_profile)
    response = value.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    view = raw_object(case.buffers[response.series.resource.split(":")[1]])
    table = case.rewrite(
        view["table"],
        lambda obj: obj["channels"]["signal"]["coordinates"].update(quantity_kind="testing/count", unit="testing/item"),
    )
    bad = case.rewrite(series_ref_projection(response.series), lambda obj: obj.update(table=table))
    with pytest.raises(SeriesRefused, match="coordinates"):
        typed_estimand(
            profile=author_profile,
            records=case.records,
            functional=value.functional,
            bindings={**value.bindings, "response": replace(response, series=series_ref_from_projection(bad))},
            series_evidence=case.evidence(),
        )


def test_anchors_on_non_event_form_refuse(context):
    from beliefs.series.types import SeriesRefused

    case, bindings = event_case(context)
    with pytest.raises(SeriesRefused, match="event-locked"):
        typed_estimand(
            profile=context,
            records=case.records,
            bindings={
                "response": bindings["response"],
                "grouping": RoleTermLevels(
                    "cause", None, (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd"))
                ),
            },
            series_evidence=case.evidence(),
        )
