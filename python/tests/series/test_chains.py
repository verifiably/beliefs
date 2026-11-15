"""Finite H/S engineering chains, with actual staging, replay and verification."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from typing import cast

import pytest
from fixtures_cut3 import RESPONSE, typed_estimand

from beliefs import audit, stored
from beliefs.assess import build_assessment
from beliefs.boundary import RunMinted, execute_assessment_run
from beliefs.contract.domain import parse_domain_contract
from beliefs.estimand import MeasuredBinding, check_series
from beliefs.profile import compile_profile
from beliefs.replay import CONTENT_EQUALITY, replay
from beliefs.series.codec import series_ref_from_projection
from beliefs.series.geometry import window_memberships
from beliefs.spec import SPEC_DOMAIN, frozen_projection, restore
from beliefs.verify import build_verification

from .fixtures import SeriesCase, raw_object
from .test_authoring import event_case
from .test_execution import launch_args
from .test_portability import persist_case, run_publication


@pytest.fixture
def chain_profile(base_contract, testing_document):
    from time_roles_fixture import time_contract

    testing_document["sorts"]["entity"]["categories"].append("class")
    row = testing_document["functionals"]["difference-of-means"]
    testing_document["functionals"]["series-contrast"] = {**row, "response_axis": "regular-elapsed"}
    testing_document["functionals"]["window-difference-against-control"] = {
        **row,
        "form": "event-locked",
        "increment": "not-applicable",
        "response_axis": "elapsed",
    }
    return compile_profile(
        base_contract,
        [
            parse_domain_contract(testing_document, source="<finite chain>", base=base_contract, predecessor=None),
            time_contract(base_contract),
        ],
    )


JOB = """import json, pathlib
from beliefs.seeds import bind
seed = bind(config)
rule transform:
    input: config["series_descriptor"], config["series_table"]
    output: "outputs/result.txt"
    run:
        seed(rule, wildcards, "model-initialization")
        view = json.loads(pathlib.Path(input[0]).read_bytes())
        table = json.loads(pathlib.Path(input[1]).read_bytes())
        assert max(view["selection"]) < len(table["coordinates"])
        pathlib.Path(output[0]).write_text(str(len(view["selection"])))
"""


def exercise(case, value, profile, root):
    from fixtures_cut3 import definition

    from beliefs.identity import v1

    response = value.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    descriptor = raw_object(case.buffers[response.series.resource.split(":")[1]])
    parameters = {
        "series_descriptor": "inputs/" + response.series.resource.split(":")[1] + ".json",
        "series_table": "inputs/" + descriptor["table"]["resource"].split(":")[1] + ".json",
    }
    p = persist_case(case, value, profile, root, parameters=parameters)
    projection = v1.encode(frozen_projection(p.spec))
    restored = restore(v1.digest(SPEC_DOMAIN, frozen_projection(p.spec)), projection, profile=profile)
    assert restored == p.spec
    args = launch_args(p, root / "runtime")
    (args["code_roots"][0] / "workflow" / "Snakefile").write_text(JOB)
    args["definition"] = definition(snakefile=JOB)
    original = execute_assessment_run(**args)
    assert isinstance(original, RunMinted), original
    replayed = replay(original, **{key: arg for key, arg in args.items() if key != "boundary_policy"})
    assert isinstance(replayed, RunMinted), replayed
    assert original.run.result == replayed.run.result
    verification = build_verification(
        original.run,
        replayed.run,
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + profile.base_contract_identity,
        epoch="engineering-fixture",
        series_evidence=case.evidence(),
        profile=profile,
        records=case.records,
    )
    assert verification.verdict == "passed"
    assert verification.scope == "same-environment"  # minimal fixture runner grants no clean-environment claim
    assert {i.dataset for i in original.run.recipe.inputs} == {i.dataset for i in p.spec.input_roles}
    p.writer.add(run_publication(original.run))
    derived = build_assessment(original.run, specs=p.evidence.specs, implementations=p.evidence.implementations)
    from beliefs.record import AssessmentValue

    from .test_portability import _stated_optionals

    assert isinstance(derived, AssessmentValue)
    node = p.writer.add(
        stored.assessment_node(
            "actual-series-chain",
            title="Finite engineering chain",
            spec=derived.spec,
            run=stored.typed_ref("run", original.run.address()),
            proposition=p.proposition.id,
            outcome=derived.outcome,
            interpretation_rule=derived.interpretation_rule,
            **_stated_optionals(derived),
        )
    )
    outcome = audit.check_assessment(
        p.writer.read_view, node, evidence=replace(p.evidence, series_evidence=case.evidence()), profile=profile
    )
    assert outcome.checked and outcome.contradiction is None
    return p


def test_h_two_anchors_full_chain(chain_profile, tmp_path):
    case, bindings = event_case(chain_profile)
    value = typed_estimand(
        profile=chain_profile,
        records=case.records,
        form="event-locked",
        coverage_policy="complete-windows",
        functional="testing/window-difference-against-control",
        bindings=bindings,
        series_evidence=case.evidence(),
    )
    (checked,) = check_series(value, profile=chain_profile, records=case.records, evidence=case.evidence())
    # Frozen spec §4's exact translated windows, including both anchor occurrences.
    windows = window_memberships(checked, ((Fraction(-172800), Fraction(0)), (Fraction(86400), Fraction(432000))))
    assert tuple(tuple((w.low, w.high) for w in anchor) for anchor in windows) == (
        ((-172800, 0), (86400, 432000)),
        ((547200, 720000), (806400, 1152000)),
    )
    assert tuple(tuple(len(w.positions) for w in anchor) for anchor in windows) == ((48, 96), (48, 96))
    p = exercise(case, value, chain_profile, tmp_path)
    assert p.spec.estimand.bindings["anchor"] == bindings["anchor"]
    assert p.spec.estimand.bindings["lag"] == bindings["lag"]


def test_s_selected_grid_full_chain(chain_profile, tmp_path):
    from fixtures_cut3 import MEASUREMENT_RECORDS, Referent, RoleTermLevels

    case = SeriesCase()
    case.records.nodes.update(MEASUREMENT_RECORDS.nodes)
    coordinates = [str(Decimal(i) / 100) for i in range(1001)]
    table = case.table(
        coordinates,
        channels={
            "signal": {
                "coordinates": {
                    "quantity_kind": "testing/abundance",
                    "unit": "testing/tpm",
                    "value_type": "level",
                    "transformation": "testing/identity",
                },
                "values": ["1"] * len(coordinates),
            }
        },
    )
    full = case.view(table, list(range(1001)))
    selected = case.view(table, list(range(0, 1001, 2)), selection_procedure=case.procedure())

    def build(ref):
        return typed_estimand(
            profile=chain_profile,
            records=case.records,
            functional="testing/series-contrast",
            bindings={
                "response": replace(RESPONSE, series=series_ref_from_projection(ref)),
                "grouping": RoleTermLevels(
                    "cause",
                    None,
                    (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd")),
                ),
            },
            series_evidence=case.evidence(),
        )

    unselected, selected_value = build(full), build(selected)
    (baseline,) = check_series(unselected, profile=chain_profile, records=case.records, evidence=case.evidence())
    (checked,) = check_series(selected_value, profile=chain_profile, records=case.records, evidence=case.evidence())
    assert (baseline.count, baseline.span, baseline.rate_hz) == (1001, 10, 100)
    assert (checked.count, checked.span, checked.spacing_seconds, checked.rate_hz) == (501, 10, Fraction(1, 50), 50)
    assert unselected.claim == selected_value.claim
    assert unselected.series_graph != selected_value.series_graph
    exercise(case, selected_value, chain_profile, tmp_path)


def inherited_case(chain_profile, tmp_path, lineage_state):
    import lineage_fixtures as lineage
    from fixtures_cut3 import ESTIMATOR_PROCEDURE, TESTING_CLAIM, spec_draft, spec_rules

    from beliefs.corpus import _StandingRecords
    from beliefs.series.codec import series_ref_projection
    from beliefs.spec import SpecInput

    from .test_authoring import author_case, input_roles
    from .test_portability import writer_at

    case, value = author_case(chain_profile)
    response = value.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    descriptor = raw_object(case.buffers[response.series.resource.split(":")[1]])
    table = case.rewrite(descriptor["table"], lambda obj: obj["axis"].update(basis="native-elapsed"))
    selected = case.rewrite(series_ref_projection(response.series), lambda obj: obj.update(table=table))
    ancestor = lineage.acquired("series-ancestor")
    original = case.records.read(table["dataset"])
    derived = stored.dataset_node(
        title="Derived native series",
        resources=original.facets["dataset"]["resources"],
        basis={
            "tag": "single",
            "routes": [lineage.route("run:series-producer", ancestor.id, identity="route:series-producer")],
        },
    )
    assert derived.id == original.id
    case.records.nodes[derived.id] = derived
    value = typed_estimand(
        profile=chain_profile,
        records=case.records,
        functional=value.functional,
        bindings={**value.bindings, "response": replace(response, series=series_ref_from_projection(selected))},
        series_evidence=case.evidence(),
    )
    writer = writer_at(tmp_path / "corpus", chain_profile)
    for node in (*case.records.nodes.values(), ancestor):
        writer.add(node)
    if lineage_state != "missing-producer":
        writer.add(lineage.production("series-producer", ancestor.id, derived.id))
    if lineage_state == "diverged":
        other = writer.add(lineage.acquired("other-series-source"))
        writer.add(lineage.production("other-producer", other.id, derived.id))
    records = _StandingRecords(writer.read_view)
    inputs = tuple(
        SpecInput("observes", i.dataset, "observation") if i.dataset == derived.id else i for i in input_roles(value)
    )
    args = {
        "held_rules": spec_rules(),
        "rule_procedures": {"median-difference/v1": ESTIMATOR_PROCEDURE},
        "profile": chain_profile,
        "claim": TESTING_CLAIM,
        "records": records,
        "series_evidence": case.evidence(),
    }
    draft = spec_draft(estimand=value, input_roles=(*inputs, SpecInput("observes", ancestor.id, "observation")))
    return case, value, writer, records, draft, args, derived.id


@pytest.mark.parametrize("lineage_state", ["complete", "missing-producer", "diverged"])
def test_inherited_observation_is_preserved(chain_profile, tmp_path, lineage_state):
    from beliefs.errors import UnfreezableSpec
    from beliefs.spec import freeze

    _case, value, _writer, records, draft, args, dataset = inherited_case(chain_profile, tmp_path, lineage_state)
    if lineage_state == "complete":
        frozen = freeze(draft, **args)
        assert any(i.dataset == dataset and i.role == "observes" for i in frozen.input_roles)
        assert records.empirical_standing(dataset, chain_profile)
    else:
        with pytest.raises(UnfreezableSpec, match="empirical standing"):
            freeze(draft, **args)
    metadata = next(row.ref.dataset for row in value.series_graph if row.format == "science.series-origins.v2")
    assert not records.empirical_standing(metadata, chain_profile)


def native_verification_case(chain_profile, tmp_path):
    from authority import ACTOR
    from closure_fixtures import make_closure

    from beliefs.evidence import DerivationEvidence
    from beliefs.recipe import RecipeInput
    from beliefs.spec import HeldImplementation, freeze

    case, _value, writer, records, draft, args, dataset = inherited_case(chain_profile, tmp_path, "complete")
    from fixtures_cut3 import spec_rules

    rules: dict[str, HeldImplementation] = dict(spec_rules())
    rules[draft.equivalence_rule] = CONTENT_EQUALITY
    spec = freeze(draft, **{**args, "held_rules": rules})
    base = make_closure(shape="assessment", token="native-series")
    base = replace(base, occurrence=replace(base.occurrence, actor=ACTOR))
    original = replace(
        base,
        recipe=replace(
            base.recipe,
            spec_identity=spec.identity,
            inputs=tuple(
                RecipeInput(
                    i.role,
                    i.dataset,
                    cast(str, stored.dataset_declaration(records.read(i.dataset)).resources[0].digest),
                )
                for i in spec.input_roles
            ),
            rule_bindings=tuple((b.rule, b.implementation) for b in spec.rule_bindings),
        ),
    )
    replayed = replace(original, occurrence=replace(original.occurrence, event_token="native-replay"))
    evidence = DerivationEvidence(
        specs={spec.identity: spec},
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        implementations={},
        series_evidence=case.evidence(),
    )
    return case, writer, records, dataset, original, replayed, evidence


@pytest.mark.parametrize("condition", ["agree", "no-standing-adapter", "diverged"])
def test_native_observation_verification_and_audit(chain_profile, tmp_path, condition):
    import lineage_fixtures as lineage

    from beliefs.verify import publication_node

    case, writer, records, dataset, original, replayed, evidence = native_verification_case(chain_profile, tmp_path)
    if condition == "diverged":
        other = writer.add(lineage.acquired("new-series-source"))
        writer.add(lineage.production("new-series-producer", other.id, dataset))
        assert not records.empirical_standing(dataset, chain_profile)
    supplied_records = case.records if condition == "no-standing-adapter" else records
    derived = build_verification(
        original,
        replayed,
        specs=evidence.specs,
        held_rules=evidence.held_rules,
        contract_identity="science:" + chain_profile.base_contract_identity,
        epoch="fixture",
        series_evidence=evidence.series_evidence,
        profile=chain_profile,
        records=supplied_records,
    )
    assert (
        derived.verdict == {"agree": "passed", "no-standing-adapter": "inconclusive", "diverged": "failed"}[condition]
    )
    if condition == "agree":
        writer.add(run_publication(original))
        writer.add(run_publication(replayed))
        outcome = audit.check_verification(
            writer.read_view,
            publication_node(derived, assessment_ref="assessment:native"),
            evidence=evidence,
            profile=chain_profile,
        )
        assert outcome.checked and outcome.contradiction is None

        from test_world_receipts import hold_shipped, publish, world_over

        from beliefs.world.view import open_world_view

        world = world_over(tmp_path / "world-setup", {writer.read_view.corpus_id: tmp_path / "corpus"})
        epoch = publish(world, (writer.read_view.corpus_id,), hold_shipped(world))
        captured = open_world_view(world, epoch)
        outcome = audit.check_verification(
            captured,
            publication_node(derived, assessment_ref="assessment:native"),
            evidence=evidence,
            profile=chain_profile,
        )
        assert outcome.checked and outcome.contradiction is None


def key_for(spec):
    from beliefs.record import AssessmentValue

    return AssessmentValue(
        spec=spec.identity,
        run="fixture-run",
        proposition=spec.target,
        outcome="supported",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
    ).key()


@pytest.mark.parametrize(
    "change",
    ["source", "channel", "selection", "selection-procedure", "origin", "grid", "member", "yielding-procedure"],
)
def test_series_identity_perturbations_reach_the_frozen_target(chain_profile, change):
    from beliefs.series.codec import series_ref_projection

    from .test_authoring import author_case, frozen

    case, initial = author_case(chain_profile)
    original = initial.bindings["response"]
    assert isinstance(original, MeasuredBinding) and original.series is not None
    root = series_ref_projection(original.series)
    descriptor = raw_object(case.buffers[original.series.resource.split(":")[1]])

    def build(ref, measure=original.measure):
        return typed_estimand(
            profile=chain_profile,
            records=case.records,
            functional=initial.functional,
            bindings={
                **initial.bindings,
                "response": replace(original, measure=measure, series=series_ref_from_projection(ref)),
            },
            series_evidence=case.evidence(),
        )

    before = initial
    if change == "selection":
        updated = case.view(descriptor["table"], [0, 2], selection_procedure=case.procedure())
    elif change == "selection-procedure":
        before = build(case.view(descriptor["table"], [0, 2], selection_procedure=case.procedure()))
        updated = case.view(
            descriptor["table"], [0, 2], selection_procedure=case.procedure(name="Another selection procedure")
        )
    elif change == "member":
        refs = case.hold_tree({"first.json": descriptor, "second.json": descriptor})
        before = build(refs["first.json"])
        updated = refs["second.json"]
    elif change == "yielding-procedure":
        from beliefs.procedure import procedure_from_stored

        node = stored.procedure_node(
            replace(
                procedure_from_stored(case.records.read(original.measure.procedure)),
                definition="Another measuring method.",
            )
        )
        case.records.nodes[node.id] = node
        after = build(root, replace(original.measure, procedure=node.id))
        assert after.series_graph == before.series_graph
        assert key_for(frozen(case, before, chain_profile)) != key_for(frozen(case, after, chain_profile))
        return
    else:

        def mutate(table):
            if change == "source":
                table["channels"]["signal"]["values"][0] = "2"
            elif change == "channel":
                table["channels"]["second"] = table["channels"]["signal"]
            elif change == "origin":
                table["axis"]["origin"]["source"] = case.hold(
                    {"format": "science.series-origins.v2", "origins": {"zero": {"label": "Another relative zero"}}}
                )
            elif change == "grid":
                table["axis"]["grid"] = {"kind": "irregular"}

        table = case.rewrite(descriptor["table"], mutate)
        updated = case.rewrite(
            root, lambda obj: obj.update(table=table, **({"channel": "second"} if change == "channel" else {}))
        )
    after = build(updated)
    assert before.claim == after.claim
    assert key_for(frozen(case, before, chain_profile)) != key_for(frozen(case, after, chain_profile))


def test_anchor_occurrence_identity_reaches_the_frozen_target(chain_profile):
    from beliefs.series.codec import series_ref_projection

    from .test_authoring import frozen

    case, bindings = event_case(chain_profile)

    def build(roles):
        return typed_estimand(
            profile=chain_profile,
            records=case.records,
            form="event-locked",
            coverage_policy="complete-windows",
            functional="testing/window-difference-against-control",
            bindings=roles,
            series_evidence=case.evidence(),
        )

    before = build(bindings)
    response = bindings["response"]
    assert response.series is not None
    root = series_ref_projection(response.series)
    descriptor = raw_object(case.buffers[response.series.resource.split(":")[1]])
    anchors = case.rewrite(
        descriptor["anchors"], lambda obj: obj["rows"][0].update(key="another-occurrence", coordinate="3600")
    )
    root = case.rewrite(root, lambda obj: obj.update(anchors=anchors))
    after = build({**bindings, "response": replace(response, series=series_ref_from_projection(root))})
    assert before.claim == after.claim
    assert key_for(frozen(case, before, chain_profile)) != key_for(frozen(case, after, chain_profile))


def test_scale_authority_changes_table_and_target(chain_profile):
    from test_procedure import procedure

    from beliefs.procedure import Scale

    from .test_authoring import author_case, frozen

    case, value = author_case(chain_profile)
    root = value.bindings["response"]
    assert isinstance(root, MeasuredBinding) and root.series is not None
    original = raw_object(case.buffers[root.series.resource.split(":")[1]])
    targets, tables = [], []
    for name in ("First authority", "Second authority"):
        node = stored.procedure_node(
            procedure(
                name=name,
                yields=(RESPONSE.measure.observable,),
                scale=Scale(Fraction(0), Fraction(100), "higher-is-more"),
            )
        )
        case.records.nodes[node.id] = node
        table = case.rewrite(
            original["table"],
            lambda obj, authority=node.id: obj["channels"]["signal"].update(
                coordinates={
                    "quantity_kind": "testing/abundance",
                    "scale": authority,
                    "value_type": "level",
                    "transformation": "testing/identity",
                }
            ),
        )
        selected = case.view(table, [0, 1, 2])
        changed = typed_estimand(
            profile=chain_profile,
            records=case.records,
            functional=value.functional,
            bindings={
                **value.bindings,
                "response": replace(
                    root,
                    series=series_ref_from_projection(selected),
                    measure=replace(root.measure, unit=None, scale=node.id, procedure=node.id),
                ),
            },
            series_evidence=case.evidence(),
        )
        tables.append(table)
        targets.append(key_for(frozen(case, changed, chain_profile)))
    assert tables[0] != tables[1] and targets[0] != targets[1]
