"""Claim discovery never pools targets or reads a sibling key's evidence."""

from dataclasses import replace

import pytest
from fixtures_cut3 import only_assessed_key, typed_estimand
from fixtures_cut4 import raw_write, reopen
from test_belief import PROFILE
from test_evaluation import PROPOSITION_REF, _fixture

from beliefs import stored
from beliefs.belief import Belief, NotReached, Refused, evaluate
from beliefs.evaluation import claim_view, evaluate_over, evaluate_over_traced, gather
from beliefs.identity import v1
from beliefs.target import target_projection


def two_keys(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    node = fixture.view.get("assessment:a-2")
    value = stored.assessment_value(node, profile=PROFILE)
    target = replace(value.target, estimand=typed_estimand(uncertainty="standard-error"))
    node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(target_projection(target)).decode()
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    return replace(fixture, view=reopen(tmp_path))


def test_required_key_and_dependencies():
    with pytest.raises(TypeError, match="key"):
        evaluate(  # pyright: ignore[reportCallIssue]
            proposition="p",
            records=None,
            availability=None,
            context=None,
            retractions=None,
            binding=None,
            profile=PROFILE,
        )


def test_claim_view_isolates_keys_and_convenience_refuses(tmp_path):
    fixture = two_keys(tmp_path)
    result = claim_view(fixture.view, fixture.proposition, **fixture.kwargs)
    assert len(result.beliefs) == 2
    assert list(result.beliefs) == sorted(result.beliefs)
    assert all(isinstance(answer, Belief) and answer.value == 1 for answer in result.beliefs.values())
    assert len(result.pairs) == 1
    assert result.pairs[0].left < result.pairs[0].right
    answer, admission = evaluate_over_traced(fixture.view, fixture.proposition, **fixture.kwargs)
    assert isinstance(answer, Refused)
    assert answer.reason == "multiple-assessed-propositions: use claim_view"
    assert admission == NotReached()
    for key in result.beliefs:
        inputs = gather(
            fixture.view,
            fixture.proposition,
            key=key,
            observations=fixture.availability.observations,
            **fixture.gather_kwargs,
        )
        assert len(inputs.assessments) == 1
        own = inputs.assessments[0]
        other = "run-b" if own.run == "run-a" else "run-a"
        assert ("run", other) not in inputs.declared_refs()
        assert set(inputs.read_trace) <= inputs.declared_refs()
        answer = result.beliefs[key]
        assert isinstance(answer, Belief)
        assert inputs.closure().digest() == answer.belief_input_digest


def test_one_key_trace_parity(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    result = claim_view(fixture.view, fixture.proposition, **fixture.kwargs)
    assert len(result.beliefs) == 1
    key, answer = next(iter(result.beliefs.items()))
    inputs = gather(
        fixture.view,
        fixture.proposition,
        key=key,
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    actual, admission = evaluate_over_traced(fixture.view, fixture.proposition, **fixture.kwargs)
    assert actual == answer == evaluate_over(fixture.view, fixture.proposition, **fixture.kwargs)
    assert inputs.key == key
    assert inputs.dependencies.records
    from beliefs.belief import Reached

    assert isinstance(admission, Reached)
    assert admission.admitted == frozenset(a.identity() for a in inputs.assessments)


def test_absent_sibling_run_preserves_other_key(tmp_path):
    fixture = two_keys(tmp_path)
    selected = fixture.assessments[0].key()
    before = claim_view(fixture.view, fixture.proposition, **fixture.kwargs).beliefs[selected]
    path = next(p for p in tmp_path.rglob("*.md") if "id: run:run-b\n" in p.read_text())
    path.unlink()
    fixture = replace(fixture, view=reopen(tmp_path))
    after = claim_view(fixture.view, fixture.proposition, **fixture.kwargs)
    assert after.beliefs[selected] == before
    assert len(after.beliefs) == 2


def test_identity_contradiction_across_standing_precedes_run_reads(tmp_path, monkeypatch):
    from fixtures_cut3 import YIELDING_PROCEDURE

    from beliefs import evaluation

    fixture = _fixture(tmp_path, PROPOSITION_REF)
    first = fixture.assessments[0]
    twin = replace(first, target=replace(first.target, standing="model", model=YIELDING_PROCEDURE))
    from test_belief import scenario

    from beliefs.belief import Records, evaluate_traced

    ordinary = scenario()

    class NoRunReads(dict):
        def __getitem__(self, key):
            raise AssertionError("contradiction must precede run reads")

    for key in (first.key(), twin.key()):
        answer, admission = evaluate_traced(
            **{
                **ordinary,
                "proposition": fixture.proposition,
                "key": key,
                "records": Records({}, (first, twin), NoRunReads(), (), ()),
            }
        )
        assert isinstance(answer, Refused) and answer.reason.startswith("assessment-identity-contradicted")
        assert admission == NotReached()
    node = fixture.view.get("assessment:a-1").model_copy(deep=True)
    import uuid

    node.uid = uuid.uuid4().hex
    node.id = "assessment:twin"
    node.facets[stored.ASSESSMENT_FACET]["standing"] = "model"
    node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(target_projection(twin.target)).decode()
    # Keep relation sources consistent while preserving assessment semantic identity.
    node.relations = [r.model_copy(update={"source": node.id}) for r in node.relations]
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    monkeypatch.setattr(evaluation, "run_value", lambda *_: pytest.fail("read a run before discovery refused"))
    answer = claim_view(reopen(tmp_path), fixture.proposition, **fixture.kwargs)
    assert isinstance(answer.claim_answer, Refused)
    assert answer.claim_answer.reason.startswith("assessment-identity-contradicted")


# Reuse the declaration-driven comparison lab, with no evaluation mocks.
from test_estimand import context as context  # noqa: PLC0414
from test_target_comparison import lab as lab  # noqa: PLC0414


def pair_corpus(tmp_path, lab, left, right):
    from profiles import pins_for
    from test_evaluation import _address

    from beliefs.belief import SuppliedContext
    from beliefs.lineage import LineageSnapshot
    from beliefs.projection import project_claim
    from beliefs.world import registry

    fixture = _fixture(tmp_path, PROPOSITION_REF)
    (tmp_path / "corpus.yaml").write_bytes(
        registry.manifest_bytes(registry.CorpusManifest(2, fixture.view.corpus_id, pins_for(lab.profile)))
    )
    proposition = stored.proposition_node("pair", title="Pair", claim=project_claim(left.claim))
    raw_write(tmp_path, proposition)
    for node in lab.records.nodes.values():
        if not fixture.view.holds(node.id):
            raw_write(tmp_path, node)
    for suffix, assessed in (("a", left), ("b", right)):
        node = stored.assessment_node(
            "pair-" + suffix,
            title=suffix,
            spec="spec-" + suffix,
            run="run:run-" + suffix,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule=assessed.interpretation_rule,
            target=assessed.target,
        )
        value = stored.assessment_value(node, profile=lab.profile)
        raw_write(tmp_path, node)
        raw_write(
            tmp_path,
            stored.verification_node(
                "pair-" + suffix,
                title=suffix,
                assessment=value.identity(),
                assessment_ref=node.id,
                scope="clean-environment",
                verdict="passed",
            ),
        )
    view = reopen(tmp_path)
    kwargs = {
        **fixture.kwargs,
        "profile": lab.profile,
        "context": SuppliedContext(
            LineageSnapshot((_address("a"), _address("b")), {}, {}), "pair-capture", {}, {"c1": pins_for(lab.profile)}
        ),
    }
    return view, proposition.id, kwargs


def test_pair_crosswalk_lookup_is_captured_and_outside_keyed_closures(tmp_path, lab):
    from test_local_standing import retracts
    from test_target_comparison import crosswalk_targets

    left, right, proxy = crosswalk_targets(lab)
    a = lab.target(functional="probability-of-superiority", response=left)
    b = lab.target(functional="probability-of-superiority", response=right)
    assert proxy not in {d.id for t in (a, b) for d in t.target.dependencies}
    view, proposition, kwargs = pair_corpus(tmp_path, lab, a, b)
    captured = view.captured()
    before = claim_view(captured, proposition, **kwargs)
    pair = before.pairs[0]
    assert pair.convertibility.kind == "convertible" and pair.synthesis.kind == "permitted-under"
    assert pair.convertibility.snapshot == pair.synthesis.snapshot == before.snapshot
    for key, answer in before.beliefs.items():
        inputs = gather(
            captured,
            proposition,
            key=key,
            observations=kwargs["availability"].observations,
            **{k: v for k, v in kwargs.items() if k != "availability"},
        )
        assert ("proxy-model", proxy) not in inputs.declared_refs()
        assert isinstance(answer, Belief)
        assert inputs.closure().digest() == answer.belief_input_digest
    raw_write(tmp_path, retracts(view.get(proxy), "crosswalk-retracted"))
    after = claim_view(reopen(tmp_path), proposition, **kwargs)
    assert after.pairs[0].convertibility.kind != "convertible"
    assert after.snapshot != before.snapshot
    assert after.beliefs == before.beliefs
    assert claim_view(captured, proposition, **kwargs) == before


def test_observable_bridge_is_discovered_in_both_orders(tmp_path, lab):
    from test_procedure import procedure

    from beliefs.assumptions import AssumptionInstance
    from beliefs.measurement import Aspect, Observable
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget

    apparent = Observable("testing/energy", lab.event.sort, Aspect("testing/energy-aspect", "EX:apparent"))
    intrinsic = replace(apparent, aspect=Aspect("testing/energy-aspect", "EX:intrinsic"))
    proc = lab.records.put(procedure(yields=(apparent, intrinsic)))
    first = lab.measured(
        role="parties", member=lab.event, kind="energy", unit="electronvolt", aspect=apparent.aspect, procedure_id=proc
    )
    second = replace(first, measure=replace(first.measure, observable=intrinsic))
    a = lab.target(claim=lab.event_claim, form="quantity", functional="temperature-level", response=first)
    b = lab.target(claim=lab.event_claim, form="quantity", functional="temperature-level", response=second)
    proxy = stored.proxy_model_node(
        ProxyModel(
            ProxySource(apparent, proc),
            ProxyTarget(intrinsic, None),
            {},
            AssumptionInstance("testing/proxy-validity", {"record": "bridge", "co_scope": "equal", "dimensions": ""}),
            None,
        )
    )
    lab.records.nodes[proxy.id] = proxy
    view, proposition, kwargs = pair_corpus(tmp_path, lab, a, b)
    from beliefs.evaluation import _AcceptanceSelection, _CapturedComparisonRecords, _discover

    discovery = _discover(
        view,
        proposition,
        context=kwargs["context"],
        binding=kwargs["binding"],
        profile=lab.profile,
        selection=_AcceptanceSelection(None),
    )
    reader = _CapturedComparisonRecords(
        discovery, _AcceptanceSelection(None), lab.profile, kwargs["availability"].observations
    )
    assert (
        reader.observable_proxies(apparent, intrinsic) == reader.observable_proxies(intrinsic, apparent) == (proxy.id,)
    )
    result = claim_view(view, proposition, **kwargs)
    assert result.pairs[0].synthesis.kind == "permitted-under"


def test_claimless_pair_preserves_keyed_answers(tmp_path, lab):
    from fixtures_cut4 import path_for
    from test_target_comparison import crosswalk_targets

    left, right, _ = crosswalk_targets(lab)
    a = lab.target(functional="probability-of-superiority", response=left)
    b = lab.target(functional="probability-of-superiority", response=right)
    _view, proposition, kwargs = pair_corpus(tmp_path, lab, a, b)
    path_for(tmp_path, proposition).unlink()
    result = claim_view(reopen(tmp_path), proposition, **kwargs)
    assert len(result.beliefs) == 2 and all(isinstance(v, Belief) for v in result.beliefs.values())
    assert result.pairs[0].convertibility.kind == result.pairs[0].synthesis.kind == "unknown"
    assert result.pairs[0].convertibility.snapshot == result.snapshot


def test_unclassifiable_candidate_refuses_before_runs(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    node = fixture.view.get("assessment:a-1")
    node.facets[stored.ASSESSMENT_FACET]["outcome"] = "unclassifiable"
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    from beliefs import evaluation

    monkeypatch.setattr(evaluation, "run_value", lambda *_: pytest.fail("discovery read a run"))
    result = claim_view(reopen(tmp_path), fixture.proposition, **fixture.kwargs)
    assert isinstance(result.claim_answer, Refused)
    assert result.claim_answer.reason.startswith("unclassifiable-assessment")


def test_malformed_sibling_run_preserves_other_key(tmp_path):
    fixture = two_keys(tmp_path)
    selected = fixture.assessments[0].key()
    before = claim_view(fixture.view, fixture.proposition, **fixture.kwargs).beliefs[selected]
    node = fixture.view.get("run:run-b")
    node.facets["run"]["spec"] = 42
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    after = claim_view(reopen(tmp_path), fixture.proposition, **fixture.kwargs)
    assert after.beliefs[selected] == before
    other = next(v for k, v in after.beliefs.items() if k != selected)
    assert isinstance(other, Refused) and other.reason.startswith("malformed-input")
    assert len(after.beliefs) == 2


@pytest.mark.parametrize("citation", ["event-anchor", "applicability-only"])
def test_rule_citation_survives_round_trip_and_retraction_changes_eligibility(tmp_path, lab, citation):
    from fractions import Fraction

    from fixtures_cut3 import RESPONSE
    from test_local_standing import retracts

    from beliefs.applicability import ScopedRestriction
    from beliefs.claim import Referent
    from beliefs.classification_rule import ClassificationRule
    from beliefs.estimand import LagBinding, RuleAnchor
    from beliefs.restriction import IntervalRestriction, RuleRestriction

    sort = "testing/entity" if citation == "event-anchor" else "testing/level"
    rule = stored.classification_rule_node(
        ClassificationRule(sort, (RESPONSE.measure.observable,), "Event rule", None, None, None)
    )
    lab.records.nodes[rule.id] = rule
    if citation == "event-anchor":
        assessed = lab.target(
            form="event-locked",
            functional="window-difference-against-control",
            bindings={
                "response": RESPONSE,
                "anchor": RuleAnchor(rule.id, (Referent(sort, "EX:a"),)),
                "lag": LagBinding(
                    "testing/hour",
                    (
                        IntervalRestriction("testing/hour", Fraction(0), Fraction(1), True, False),
                        IntervalRestriction("testing/hour", Fraction(1), Fraction(2), True, False),
                    ),
                ),
            },
        )
    else:
        from beliefs.applicability import Applicability
        from beliefs.dependencies import dependency_closure

        assessed = lab.target()
        app = Applicability(
            {"testing/case-status": ScopedRestriction("universal", RuleRestriction(rule.id, ("EX:a",)))}
        )
        deps = dependency_closure((*[d.id for d in assessed.target.dependencies], rule.id), lab.records, lab.profile)
        assessed = replace(assessed, target=replace(assessed.target, applicability=app, dependencies=deps))
    view, proposition, kwargs = pair_corpus(tmp_path, lab, assessed, assessed)
    captured = view.captured()
    key = only_assessed_key(view, proposition, profile=lab.profile)
    args = {k: v for k, v in kwargs.items() if k != "availability"}
    before = gather(captured, proposition, key=key, observations=kwargs["availability"].observations, **args)
    assert rule.id in before.dependencies.records
    raw_write(tmp_path, retracts(view.get(rule.id), citation + "-retracted"))
    after = gather(reopen(tmp_path), proposition, key=key, observations=kwargs["availability"].observations, **args)
    assert before.key == after.key
    assert before.closure().digest() != after.closure().digest()
    assert (
        "retraction",
        next(n.id for n in reopen(tmp_path).iter_stored() if n.kind == "retraction"),
    ) in after.declared_refs()
    assert set(after.read_trace) <= after.declared_refs()
    assert (
        gather(captured, proposition, key=key, observations=kwargs["availability"].observations, **args)
        .closure()
        .digest()
        == before.closure().digest()
    )
