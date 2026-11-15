"""Linked claim classes and retained classes are checked with their own evidence."""

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F

import pytest
from fixtures_cut3 import TESTING_CLAIM, typed_estimand
from time_roles_fixture import time_contract

from beliefs import stored
from beliefs.claim import Member, Referent, build_claim
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import ScienceError
from beliefs.estimand import (
    LagBinding,
    RoleAnchor,
    RuleAnchor,
    admit_estimand,
    check_series,
    estimand_from_stored,
    estimand_projection,
)
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.restriction import IntervalRestriction
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.types import SeriesRefused

from .fixtures import raw_object
from .test_authoring import event_case

A = Referent("testing/entity", "EX:gene-x")
B = Referent("testing/entity", "EX:gene-z")


@pytest.fixture
def profiles(base_contract, testing_document):
    def make(*, linked=True, many=False, admit=True):
        doc = deepcopy(testing_document)
        doc["sorts"]["entity"]["categories"].append("class")
        template = doc["templates"]["affects"]
        template["event_anchor"] = {"role": "cause"} if linked else {"independent": True}
        template["roles"]["cause"] = (
            {"arity": "many", "min": 0, "constraint": ["class"]} if many else {"arity": "one", "constraint": ["class"]}
        )
        doc["functionals"]["window-difference-against-control"] = {
            **doc["functionals"]["difference-of-means"],
            "form": "event-locked",
            "increment": "not-applicable",
        }
        if not admit:
            doc["estimands"]["instantiation:affects-entity-outcome"]["forms"].remove("event-locked")
        return compile_profile(
            base_contract,
            [
                parse_domain_contract(doc, source="<anchor coherence>", base=base_contract, predecessor=None),
                time_contract(base_contract),
            ],
        )

    return make


def claim_for(profile, *, many=False, classes=(A, B)):
    return build_claim(
        profile,
        operator="testing/affects",
        roles={
            "cause": tuple(Member(ref) for ref in classes) if many else classes[0],
            "effect": TESTING_CLAIM.roles["effect"],
        },
        layer="causal",
        polarity="positive",
    )


def linked_case(profile, *, classes=(A,)):
    case, bindings = event_case(profile)
    node = stored.classification_rule_node(
        ClassificationRule(classes[0].sort, (), "Classify synthetic anchors", None, None, "synthetic")
    )
    case.records.nodes[node.id] = node
    ref = series_ref_projection(bindings["response"].series)
    assert isinstance(ref["resource"], str)
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])

    def change(obj):
        obj["rule"] = node.id
        for i, row in enumerate(obj["rows"]):
            ref = classes[i % len(classes)]
            row["class"] = {"sort": ref.sort, "term": ref.term}

    anchors = case.rewrite(view["anchors"], change)
    ref = case.rewrite(ref, lambda obj: obj.update(anchors=anchors))
    bindings["response"] = replace(bindings["response"], series=series_ref_from_projection(ref))
    bindings["anchor"] = RuleAnchor(node.id, classes)
    if profile.template_of(profile.operator("testing/affects")).roles["cause"].arity == "many":
        bindings["response"] = replace(bindings["response"], member=classes[0])
    return case, bindings


def build(case, bindings, profile, claim):
    return typed_estimand(
        profile=profile,
        claim=claim,
        records=case.records,
        form="event-locked",
        functional="testing/window-difference-against-control",
        bindings=bindings,
        series_evidence=case.evidence(),
        coverage_policy="complete-windows" if bindings["response"].series else None,
    )


@pytest.mark.parametrize("many", [False, True])
def test_linked_rule_anchor_requires_exact_role_classes(profiles, many):
    profile = profiles(many=many)
    classes = (A, B) if many else (A,)
    claim = claim_for(profile, many=many, classes=classes)
    case, bindings = linked_case(profile, classes=classes)
    build(case, bindings, profile, claim)
    other = claim_for(profile, many=many, classes=(Referent(A.sort, "EX:other"),))
    if many:
        bindings["response"] = replace(bindings["response"], member=Referent(A.sort, "EX:other"))
    with pytest.raises(ScienceError, match="linked"):
        build(case, bindings, profile, other)


def test_linked_class_must_retain_an_event(profiles):
    profile = profiles(many=True)
    claim = claim_for(profile, many=True)
    case, bindings = linked_case(profile, classes=(A, B))
    bindings["lag"] = LagBinding(
        "si-brochure/hour", (IntervalRestriction("si-brochure/hour", F(-49), F(0), True, False),) * 2
    )
    with pytest.raises(SeriesRefused, match="retained.*class|class.*retained"):
        build(case, bindings, profile, claim)
    independent = profiles(linked=False, many=True)
    value = build(case, bindings, independent, claim)
    restored = estimand_from_stored(estimand_projection(value), profile=profile)
    # No claim is available here: copied report shape alone cannot promise class coverage.
    with pytest.raises(SeriesRefused, match="retained.*class|class.*retained"):
        check_series(restored, profile=profile, records=case.records, evidence=case.evidence())


@pytest.mark.parametrize("many", [False, True])
def test_nonseries_role_anchor_association(profiles, many):
    profile = profiles(many=many)
    claim = claim_for(profile, many=many)
    case, bindings = linked_case(profile)
    bindings["response"] = replace(bindings["response"], series=None)
    bindings["anchor"] = RoleAnchor("cause", A if many else None, A)
    if many:
        with pytest.raises(ScienceError, match="linked"):
            build(case, bindings, profile, claim)
    else:
        build(case, bindings, profile, claim)
        bindings["anchor"] = RoleAnchor("cause", None, B)
        with pytest.raises(ScienceError, match="linked"):
            build(case, bindings, profile, claim)


def test_nonseries_rule_anchor_and_empty_linked_role(profiles):
    profile = profiles(many=True)
    case, bindings = linked_case(profile)
    bindings["response"] = replace(bindings["response"], series=None)
    claim = claim_for(profile, many=True, classes=(A,))
    build(case, bindings, profile, claim)
    for classes in [(), (B,)]:
        with pytest.raises(ScienceError):
            build(case, bindings, profile, claim_for(profile, many=True, classes=classes))


def test_association_never_bypasses_whole_row_admission(profiles):
    profile = profiles(admit=False)
    case, bindings = linked_case(profile)
    with pytest.raises(ScienceError, match="no single admitting"):
        build(case, bindings, profile, claim_for(profile))


def test_claim_backed_admission_rechecks_stored_shape(profiles):
    profile = profiles()
    claim = claim_for(profile)
    case, bindings = linked_case(profile)
    value = build(case, bindings, profile, claim)
    body = raw_object(v1.encode(estimand_projection(value)))
    body["bindings"]["anchor"]["classes"][0]["term"] = B.term
    forged = estimand_from_stored(body, profile=profile)
    with pytest.raises(ScienceError, match="linked"):
        admit_estimand(profile, forged, claim, authoring=False)


@pytest.fixture
def linked_portable(profiles, tmp_path):
    from .test_portability import persist_case

    profile = profiles(many=True)
    claim = claim_for(profile, many=True)
    case, bindings = linked_case(profile, classes=(A, B))
    value = build(case, bindings, profile, claim)
    bindings["lag"] = LagBinding(
        "si-brochure/hour", (IntervalRestriction("si-brochure/hour", F(-49), F(0), True, False),) * 2
    )
    excluded = build(case, bindings, profiles(linked=False, many=True), claim)
    # The stored replacement never passed freeze under the linked contract.
    return persist_case(
        case,
        value,
        profile,
        tmp_path,
        claim=claim,
        stored_edit=lambda body: body.update(estimand=estimand_projection(excluded)),
    )


def test_same_term_in_another_sort_is_not_a_linked_class(profiles):
    profile = profiles()
    case, bindings = linked_case(profile)
    bindings["response"] = replace(bindings["response"], series=None)
    bindings["anchor"] = replace(bindings["anchor"], classes=(Referent("testing/level", A.term),))
    with pytest.raises(ScienceError, match="linked"):
        build(case, bindings, profile, claim_for(profile))


def test_independent_role_anchor_keeps_existing_checks(profiles):
    profile = profiles(linked=False)
    case, bindings = linked_case(profile)
    bindings["response"] = replace(bindings["response"], series=None)
    bindings["anchor"] = RoleAnchor("cause", None, B)
    build(case, bindings, profile, claim_for(profile))
    bindings["anchor"] = RoleAnchor("absent", None, B)
    with pytest.raises(ScienceError, match="unknown role"):
        build(case, bindings, profile, claim_for(profile))


def test_linked_role_coefficients_refuse_at_claim_authoring(profiles):
    with pytest.raises(ScienceError, match="coefficient"):
        build_claim(
            profiles(many=True),
            operator="testing/affects",
            roles={"cause": (Member(A, 2),), "effect": TESTING_CLAIM.roles["effect"]},
            layer="causal",
            polarity="positive",
        )


@pytest.mark.parametrize("route", ["freeze", "revise", "consulted", "corpus"])
def test_anchor_coherence_across_claim_boundaries(linked_portable, route):
    from fixtures_cut3 import ESTIMATOR_PROCEDURE, spec_draft, spec_rules

    from beliefs.consulted import assessed_target_contracts
    from beliefs.spec import SPEC_DOMAIN, freeze, frozen_projection, restore, revise

    p = linked_portable
    body = raw_object(v1.encode(frozen_projection(p.spec)))
    body["estimand"]["bindings"]["anchor"]["classes"].pop()
    forged = restore(v1.digest(SPEC_DOMAIN, body), v1.encode(body), profile=p.profile)
    claim = claim_for(p.profile, many=True)
    args = {
        "held_rules": spec_rules(),
        "rule_procedures": {"median-difference/v1": ESTIMATOR_PROCEDURE},
        "profile": p.profile,
        "claim": claim,
        "records": p.case.records,
        "series_evidence": p.case.evidence(),
    }
    with pytest.raises(ScienceError, match="linked"):
        if route == "freeze":
            freeze(spec_draft(estimand=forged.estimand), **args)
        elif route == "revise":
            revise(p.spec, edits={"estimand": forged.estimand}, recorded_failures=frozenset(), **args)
        elif route == "consulted":
            assessed_target_contracts(forged.assessed_target, p.profile, claim)
        else:
            p.writer.add(stored.analysis_spec_node(forged))
