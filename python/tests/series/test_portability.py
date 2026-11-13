"""Copied series declarations stay portable; byte evidence has an explicit verdict."""

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest
from authority import ACTOR, FULL
from closure_fixtures import make_closure
from fixtures_cut3 import ESTIMATOR_PROCEDURE, TESTING_CLAIM, spec_draft, spec_rules, typed_estimand
from profiles import pins_for
from test_audit import _stated_optionals, run_publication
from test_corpus_write import OperationRecorder
from test_stored import DefaultExecutor

from beliefs import audit, stored
from beliefs.assess import build_assessment, run_record
from beliefs.corpus import CorpusWriter, _StandingRecords, standing_outcome
from beliefs.eligibility import (
    AssessmentEligibilityReader,
    Eligible,
    Ineligible,
    closure_eligibility,
    dependency_eligibility,
)
from beliefs.evidence import NO_EVIDENCE, DerivationEvidence
from beliefs.projection import project_claim
from beliefs.recipe import RecipeInput
from beliefs.record import AssessmentValue
from beliefs.register import AssumptionsRegister
from beliefs.series.evidence import SeriesEvidence
from beliefs.spec import SpecInput, freeze
from beliefs.verification import Verification

from .fixtures import digest, raw_object
from .test_authoring import author_case, input_roles


def writer_at(path, profile):
    port = OperationRecorder(path, authority=FULL, profile=profile)
    writer = CorpusWriter(path, DefaultExecutor, authority=FULL, profile=profile, operation_port=port)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer


@pytest.fixture
def portable(tmp_path, author_profile, request):
    from beliefs.estimand import MeasuredBinding
    from beliefs.series.codec import series_ref_from_projection, series_ref_projection
    from beliefs.tree import object_path

    case, value = author_case(author_profile)
    variant = getattr(request, "param", "file")
    missing_path = None
    if variant != "file":
        response = value.bindings["response"]
        assert isinstance(response, MeasuredBinding) and response.series is not None
        original = series_ref_projection(response.series)
        descriptor = raw_object(case.buffers[response.series.resource.split(":")[1]])
        if variant == "tree":
            root = case.hold_tree({"view.json": descriptor})["view.json"]
            missing_path = object_path(root["resource"])
        else:
            root = case.view(
                descriptor["table"],
                [0, 1, 2],
                transform={
                    "source": original,
                    "procedure": case.procedure(),
                    "operation": "select",
                    "mapping": [0, 1, 2],
                },
            )
            missing_path = response.series.resource.split(":")[1]
        value = typed_estimand(
            profile=author_profile,
            records=case.records,
            functional=value.functional,
            bindings={**value.bindings, "response": replace(response, series=series_ref_from_projection(root))},
            series_evidence=case.evidence(),
        )
    return persist_case(case, value, author_profile, tmp_path, missing_path=missing_path)


def persist_case(case, value, profile, root, *, missing_path=None, parameters=None):
    writer = writer_at(root / "corpus", profile)
    proposition = writer.add(stored.proposition_node("p1", title="P", claim=project_claim(TESTING_CLAIM)))
    observed = stored.dataset_node(
        title="Observed source",
        resources=({"name": "observed", "digest": digest(b"fixture observation")},),
        empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
    )
    case.records.nodes[observed.id] = observed
    frozen = freeze(
        spec_draft(
            target=proposition.id,
            estimand=value,
            input_roles=(SpecInput("observes", observed.id, "observation"), *input_roles(value)),
            **({"parameters": parameters} if parameters is not None else {}),
        ),
        held_rules=spec_rules(),
        rule_procedures={"median-difference/v1": ESTIMATOR_PROCEDURE},
        profile=profile,
        claim=TESTING_CLAIM,
        records=case.records,
        series_evidence=case.evidence(),
    )
    for node in case.records.nodes.values():
        writer.add(node)
    for namespace, identity in profile.activated_contracts.items():
        writer.add(stored.assumptions_register_node(AssumptionsRegister(f"{namespace}:{identity}", None, {})))
    writer.add(stored.analysis_spec_node(frozen))
    base = make_closure(shape="assessment", token="portable-series")
    closure = replace(
        base,
        recipe=replace(
            base.recipe,
            spec_identity=frozen.identity,
            inputs=tuple(
                RecipeInput(
                    i.role,
                    i.dataset,
                    cast(str, stored.dataset_declaration(case.records.read(i.dataset)).resources[0].digest),
                )
                for i in frozen.input_roles
            ),
            rule_bindings=tuple((b.rule, b.implementation) for b in frozen.rule_bindings),
        ),
        occurrence=replace(base.occurrence, actor=ACTOR),
    )
    rule = spec_rules()[frozen.interpretation_rule]
    evidence = DerivationEvidence({frozen.identity: frozen}, {}, {rule.identity: rule})
    derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
    assert isinstance(derived, AssessmentValue)
    run = writer.add(run_publication(closure))
    assessment = writer.add(
        stored.assessment_node(
            "series",
            title="Series assessment",
            spec=frozen.identity,
            run=run.id,
            proposition=proposition.id,
            outcome=derived.outcome,
            interpretation_rule=derived.interpretation_rule,
            **_stated_optionals(derived),
        )
    )
    verification = writer.add(
        stored.verification_node(
            "portable-verification",
            title="Imported evidence",
            assessment=derived.identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        )
    )
    return SimpleNamespace(
        case=case,
        value=value,
        writer=writer,
        spec=frozen,
        closure=closure,
        evidence=evidence,
        derived=derived,
        assessment=assessment,
        verification=verification,
        proposition=proposition,
        profile=profile,
        missing_path=missing_path,
    )


def no_store(*args, **kwargs):
    raise AssertionError("a record-only boundary opened a series store")


@pytest.mark.parametrize(
    "boundary", ["decode-add", "standing", "eligibility", "recursive", "aptness", "evaluator", "audit", "import"]
)
def test_spec_boundary_table(boundary, portable, monkeypatch, tmp_path):
    p = portable
    monkeypatch.setattr("beliefs.root.open_series_store", no_store)
    p.case.buffers.clear()
    records = _StandingRecords(p.writer.read_view)
    if boundary == "decode-add":
        assert stored.analysis_spec_value(stored.analysis_spec_node(p.spec), profile=p.profile) == p.spec
        assert stored.assessment_value(p.assessment, profile=p.profile).target == p.spec.assessed_target
    elif boundary == "standing":
        assert standing_outcome(p.writer.read_view, p.assessment, p.profile) is None
    elif boundary == "eligibility":
        result = closure_eligibility(
            (d.id for d in p.derived.dependencies),
            records,
            p.profile,
            graph=p.value.series_graph,
        )
        assert all(isinstance(v, Eligible) for v in result.verdicts.values())
        assert {row.ref.dataset for row in p.value.series_graph} <= set(result.reads)
    elif boundary == "recursive":
        reader = AssessmentEligibilityReader(
            records,
            p.profile,
            lambda _: run_record(p.closure),
            lambda _: (Verification(p.verification.id, p.derived.identity(), "clean-environment", "passed"),),
        )
        assert isinstance(reader(p.assessment.id), Eligible)
    elif boundary == "aptness":
        from fixtures_cut3 import RESPONSE

        from beliefs.aptness import check_aptness

        check_aptness(p.profile, "testing/entity", RESPONSE.measure, None, None, {}, records)
    elif boundary == "evaluator":
        from beliefs.belief import SuppliedContext
        from beliefs.corpus import lineage_snapshot
        from beliefs.evaluation import gather
        from beliefs.policy import BELIEF_V1, BELIEF_V1_RULE, PolicyBinding
        from beliefs.resolution import build_snapshot

        context = SuppliedContext(
            lineage_snapshot(p.writer.read_view, tuple(i.dataset for i in p.spec.input_roles if i.role == "observes")),
            "portable-snapshot",
            {p.derived.identity(): ("fixture",)},
            {"fixture": pins_for(p.profile)},
        )
        result = gather(
            p.writer.read_view,
            p.proposition.id,
            key=p.derived.key(),
            observations={},
            context=context,
            profile=p.profile,
            resolution=build_snapshot(readable={}),
            binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        )
        assert result.assessments == (p.derived,)
        assert all(isinstance(v, Eligible) for v in result.dependencies.closure.verdicts.values())
        assert not any(id.startswith("dataset:") for id in result.dependencies.records)
    elif boundary == "audit":
        result = audit.check_assessment(p.writer.read_view, p.assessment, evidence=p.evidence, profile=p.profile)
        assert not result.checked and result.contradiction is None and "series" in result.reason
    else:
        target = writer_at(tmp_path / "imported", p.profile)
        target.import_bundle(
            list(p.writer.read_view.iter_stored()),
            evidence=NO_EVIDENCE,
            observer="fixture",
            instrument="fixture",
            opened_at="2026-11-13T00:00:00Z",
            closed_at="2026-11-13T00:00:01Z",
        )
        assert target.read_view.holds(p.assessment.id)
        assert standing_outcome(target.read_view, target.read_view.get(p.assessment.id), p.profile) is None


@pytest.mark.parametrize("condition", ["complete", "absent", "unreadable", "corrupt"])
def test_audit_series_evidence_outcomes(portable, condition):
    p = portable
    supplied = p.case.evidence()
    if condition == "absent":
        supplied = SeriesEvidence({}, {})
    elif condition == "unreadable":
        supplied = SeriesEvidence(
            {key: lambda path, limit: (_ for _ in ()).throw(OSError("offline")) for key in supplied.stores},
            supplied.locations,
        )
    elif condition == "corrupt":
        p.case.buffers[next(iter(p.case.buffers))] = b"changed"
    result = audit.check_assessment(
        p.writer.read_view,
        p.assessment,
        evidence=replace(p.evidence, series_evidence=supplied),
        profile=p.profile,
    )
    assert result.checked == (condition in {"complete", "corrupt"})
    assert (result.contradiction is not None) == (condition == "corrupt")
    if not result.checked:
        assert "series" in result.reason


def test_dataset_terminals_and_retractions(author_profile):
    case, value = author_case(author_profile)
    ids = tuple(row.ref.dataset for row in value.series_graph)
    original = case.records.retraction_in_force

    def reject_dataset_retraction(id):
        assert not id.startswith("dataset:"), "dataset terminal entered unsupported retraction lookup"
        return original(id)

    case.records.retraction_in_force = reject_dataset_retraction
    result = dependency_eligibility(ids, case.records, author_profile)
    assert all(isinstance(v, Eligible) for v in result.values())
    missing = ids[0]
    node = case.records.nodes.pop(missing)
    assert isinstance(closure_eligibility((missing,), case.records, author_profile).verdicts[missing], Ineligible)
    case.records.nodes[missing] = node.model_copy(update={"kind": "procedure"})
    assert isinstance(closure_eligibility((missing,), case.records, author_profile).verdicts[missing], Ineligible)


@pytest.mark.parametrize("corrupt", [False, True])
def test_explicit_import_uses_supplied_series_evidence(portable, tmp_path, corrupt):
    from beliefs.errors import ImportRefused

    p = portable
    evidence = replace(p.evidence, series_evidence=p.case.evidence())
    if corrupt:
        p.case.buffers[next(iter(p.case.buffers))] = b"wrong held origin"
    target = writer_at(tmp_path / "explicit-import", p.profile)

    def run():
        return target.import_bundle(
            list(p.writer.read_view.iter_stored()),
            evidence=evidence,
            observer="fixture",
            instrument="fixture",
            opened_at="2026-11-13T00:00:00Z",
            closed_at="2026-11-13T00:00:01Z",
        )

    if corrupt:
        with pytest.raises(ImportRefused):
            run()
        assert not target.read_view.holds(p.assessment.id)
    else:
        run()
        assert target.read_view.holds(p.assessment.id)
        assert audit.check_assessment(target.read_view, p.assessment, evidence=evidence, profile=p.profile).checked


def test_consistent_false_graph_is_only_a_structural_declaration(portable):
    from beliefs.estimand import check_series, estimand_from_stored, estimand_projection
    from beliefs.identity import v1
    from beliefs.series.types import SeriesRefused

    from .fixtures import raw_object

    p = portable
    body = raw_object(v1.encode(estimand_projection(p.value)))
    body["series_graph"][0]["terms"] = sorted(set(body["series_graph"][0]["terms"]) | {"testing/entity"})
    forged = estimand_from_stored(body, profile=p.profile)
    assert forged.series_graph != p.value.series_graph
    with pytest.raises(SeriesRefused, match="graph"):
        check_series(forged, profile=p.profile, records=p.case.records, evidence=p.case.evidence())


@pytest.mark.parametrize("portable", ["tree", "transform"], indirect=True)
def test_missing_manifest_or_predecessor_is_unchecked(portable):
    p = portable
    supplied = p.case.evidence()
    del p.case.buffers[p.missing_path]
    result = audit.check_assessment(
        p.writer.read_view,
        p.assessment,
        evidence=replace(p.evidence, series_evidence=supplied),
        profile=p.profile,
    )
    assert not result.checked and result.contradiction is None and "series" in result.reason
