"""The assessed key binds frozen target meaning rather than execution results."""

from dataclasses import replace
from decimal import Decimal
from typing import Any, cast

import pytest
from fixtures_cut3 import (
    ESTIMATOR_PROCEDURE,
    MEASUREMENT_RECORDS,
    TESTING_PROFILE,
    freeze_context,
    spec_draft,
    spec_rules,
    typed_estimand,
    typed_target,
)
from test_estimand import context as context  # noqa: PLC0414 — shared pytest fixture

from beliefs.errors import MalformedRecord, MalformedSpec, UnfreezableSpec
from beliefs.identity import v1
from beliefs.record import AssessmentValue
from beliefs.spec import freeze, frozen_projection, restore
from beliefs.target import target_from_projection, target_projection


def test_target_and_spec_roundtrip_without_optional_nulls():
    spec = freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())
    body = target_projection(spec.assessed_target)
    assert "model" not in body
    assert "calibration" not in cast(dict, body["estimand"])
    assert target_from_projection(body, standing="empirical", profile=TESTING_PROFILE) == spec.assessed_target
    assert restore(spec.identity, v1.encode(frozen_projection(spec)), profile=TESTING_PROFILE) == spec
    ids = {e.id for e in spec.assessed_target.dependencies}
    assert ESTIMATOR_PROCEDURE in ids
    assert {e.id for e in spec.estimand.dependencies} <= ids
    assert any(b.procedure == ESTIMATOR_PROCEDURE for b in spec.rule_bindings)
    with pytest.raises(MalformedRecord):
        target_from_projection({**body, "model": None}, standing="empirical", profile=TESTING_PROFILE)


def test_key_ignores_execution_and_payload_but_binds_standing():
    fields: dict[str, Any] = {
        "spec": "s",
        "run": "r",
        "proposition": "p",
        "outcome": "supported",
        "interpretation_rule": "rule",
        "target": typed_target(),
    }
    a = AssessmentValue(**fields)
    b = replace(a, spec="other", run="other", estimates={"estimate": Decimal(1)}, outcome="refuted")
    assert a.key() == b.key()
    assert a.identity() != b.identity()
    other = replace(a, target=typed_target(standing="model", model=ESTIMATOR_PROCEDURE))
    assert a.key() != other.key()
    assert a.facet_digest() != other.facet_digest()
    assert a.identity() == other.identity()


@pytest.mark.parametrize(
    "standing,model,error",
    [
        ("empirical", ESTIMATOR_PROCEDURE, UnfreezableSpec),
        ("model", None, UnfreezableSpec),
        ("folk", None, MalformedSpec),
    ],
)
def test_spec_route_agreement(standing, model, error):
    with pytest.raises(error):
        freeze(spec_draft(standing=standing, model=model), held_rules=spec_rules(), **freeze_context())


def test_target_cannot_drop_a_binding_dependency():
    body = target_projection(typed_target())
    body["dependencies"] = []
    with pytest.raises(MalformedRecord, match="dependency"):
        target_from_projection(body, standing="empirical", profile=TESTING_PROFILE)


@pytest.mark.parametrize("binding_kind", ["grouping", "anchor"])
def test_direct_rule_bindings_are_in_both_frozen_sets_and_cannot_be_dropped(binding_kind, context):
    from fixtures_cut3 import RESPONSE, FixtureRecords
    from test_estimand import build

    from beliefs import stored
    from beliefs.claim import Referent
    from beliefs.classification_rule import ClassificationRule
    from beliefs.estimand import LagBinding, RuleAnchor, RuleClassLevels, estimand_from_stored, estimand_projection

    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    node = stored.classification_rule_node(
        ClassificationRule("testing/entity", (RESPONSE.measure.observable,), "Classify.", None, None, None)
    )
    records.nodes[node.id] = node
    classes = (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
    binding = RuleClassLevels(node.id, classes) if binding_kind == "grouping" else RuleAnchor(node.id, classes)
    bindings = {"response": RESPONSE, binding_kind: binding}
    overrides: dict[str, Any] = {}
    if binding_kind == "anchor":
        bindings["lag"] = LagBinding("testing/hour", ())
        overrides = {"form": "event-locked", "functional": "testing/window-difference-against-control"}
    e = build(context, bindings=bindings, records=records, **overrides)
    spec = freeze(
        spec_draft(estimand=e), held_rules=spec_rules(), **{**freeze_context(), "profile": context, "records": records}
    )
    assert node.id in {d.id for d in e.dependencies}
    assert node.id in {d.id for d in spec.assessed_target.dependencies}
    body = estimand_projection(e)
    body["dependencies"] = []
    with pytest.raises(MalformedRecord):
        estimand_from_stored(body, profile=context)
    body = target_projection(spec.assessed_target)
    body["dependencies"] = [d for d in cast(list[dict], body["dependencies"]) if d["id"] != node.id]
    with pytest.raises(MalformedRecord):
        target_from_projection(body, standing="empirical", profile=context)


def test_measured_proxy_calibration_binds_actual_facet_and_reaches_eligibility():
    from fixtures_cut3 import MEASUREMENT_RECORDS, FixtureRecords, event_estimand

    from beliefs import stored
    from beliefs.claim import Member, Referent, build_claim
    from beliefs.eligibility import Eligible, closure_eligibility
    from beliefs.errors import DependencyNotHeld
    from beliefs.estimand import MeasuredBinding
    from beliefs.proxy_model import Calibration, ProxyModel, ProxySource, ProxyTarget
    from beliefs.referent_mapping import ReferentMapping

    claim = build_claim(
        TESTING_PROFILE,
        operator="testing/correlates-with",
        roles={"parties": (Member(Referent("testing/event", "EX:e")), Member(Referent("testing/product", "EX:p")))},
        layer="statistical",
        polarity="positive",
    )
    prior = event_estimand(claim)
    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    basis_target = typed_target(estimand=prior)
    basis = stored.assessment_node(
        "d" * 64,
        title="Empirical calibration",
        spec="s",
        run="run:r",
        proposition="p",
        outcome="supported",
        interpretation_rule="rule",
        target=basis_target,
    )
    records.nodes[basis.id] = basis
    response = prior.bindings["response"]
    assert isinstance(response, MeasuredBinding)
    observable = response.measure.observable
    mapping = stored.referent_mapping_node(
        ReferentMapping(
            observable.bearer_sort, observable.bearer_sort, {"release": "fixture"}, "one-to-one", None, None
        )
    )
    proxy = stored.proxy_model_node(
        ProxyModel(
            ProxySource(observable, response.measure.procedure),
            ProxyTarget(observable, None),
            {},
            Calibration(observable, (basis.id,), ("rule",), None),
            None,
        )
    )
    records.nodes.update({mapping.id: mapping, proxy.id: proxy})
    bindings = {**prior.bindings, "response": replace(response, mapping=mapping.id, proxy=proxy.id)}
    kwargs: dict[str, Any] = {
        "profile": TESTING_PROFILE,
        "claim": claim,
        "bindings": bindings,
        "control": prior.control,
        "records": records,
    }
    with pytest.raises(DependencyNotHeld, match="assessment.*callback"):
        typed_estimand(**kwargs)

    def callback(id):
        return stored.frozen_assessment_dependency(id, records=records, profile=TESTING_PROFILE)

    e = typed_estimand(**kwargs, assessment_dependency=callback)
    entry = next(d for d in e.dependencies if d.id == basis.id)
    assert entry.facet_digest == stored.assessment_value(basis, profile=TESTING_PROFILE).facet_digest()
    assert {d.id for d in basis_target.dependencies} <= {d.id for d in e.dependencies}
    spec = freeze(
        spec_draft(estimand=e),
        held_rules=spec_rules(),
        **{**freeze_context(), "claim": claim, "records": records},
        assessment_dependency=callback,
    )
    assert restore(spec.identity, v1.encode(frozen_projection(spec)), profile=TESTING_PROFILE) == spec
    seen = []

    def eligibility(id):
        seen.append(id)
        return Eligible()

    result = closure_eligibility(
        [proxy.id], records, TESTING_PROFILE, assessments=eligibility, assessment_dependency=callback
    )
    assert result.verdicts == {proxy.id: Eligible()} and basis.id in seen
