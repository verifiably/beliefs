"""Invented mapped hourly events across the complete kernel boundary chain."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from candidate_contracts import candidate_profile

from beliefs.estimand import check_series, diagnose_event_coverage
from beliefs.series.types import ElapsedAxis

from .candidate_case import JOB, RULES, build, candidate_chain, checks_contract, freeze_chain
from .fixtures import raw_object


@pytest.fixture
def preparation_profile(base_contract):
    return candidate_profile(base_contract, extra=[checks_contract(base_contract)])


def preparation_chain(profile, *, epoch_definition="bin-start", contradiction=None):
    from beliefs.estimand import MeasuredBinding
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.transport import event_retained_keys

    chain = candidate_chain(profile)
    case = chain.case
    response = chain.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    old_view = raw_object(case.buffers[response.series.resource.split(":")[1]])
    old_table = raw_object(case.buffers[old_view["table"]["resource"].split(":")[1]])
    old_anchors = raw_object(case.buffers[old_view["anchors"]["resource"].split(":")[1]])
    epoch = datetime(2000, 1, 3, tzinfo=UTC)

    def label(seconds):
        return (epoch + timedelta(seconds=int(seconds))).isoformat().replace("+00:00", "Z")

    procedure = case.procedure(
        kind="general/estimator",
        name="Invented clock and anchor preparation",
        definition="Declared constant-offset map and " + epoch_definition + " effective epochs.",
    )
    clock = case.hold(
        {
            "format": "science.series-clock-map.v1",
            "convention": "utc-tai",
            "low": label(-172800),
            "high": label(20 * 86400),
            "procedure": procedure,
            "segments": [{"from": label(-172800), "tai_minus_utc": 32}],
        }
    )
    origin = {
        "source": case.hold(
            {
                "format": "science.series-origins.v2",
                "origins": {
                    "zero": {"label": "A freely named invented epoch", "clock": {"map": clock, "epoch": label(0)}}
                },
            }
        ),
        "key": "zero",
    }
    # Delete a genuine source bin, not a descriptor selection. It intersects only
    # the middle candidate's second window; the two retained estimates stay 7/2.
    keep = [i for i, support in enumerate(old_table["support"]) if support[0] != "450000"]
    table = deepcopy(old_table)
    table["coordinates"] = [old_table["coordinates"][i] for i in keep]
    table["support"] = [old_table["support"][i] for i in keep]
    table["channels"]["signal"]["values"] = [old_table["channels"]["signal"]["values"][i] for i in keep]
    table["axis"] = {**old_table["axis"], "origin": origin, "basis": "clock-mapped", "grid": {"kind": "irregular"}}
    absolute = {"kind": "absolute", "convention": "utc-label", "grid": "labels"}
    source_table = deepcopy(table)
    source_table["axis"] = absolute
    source_table["coordinates"] = [label(at) for at in table["coordinates"]]
    source_table["support"] = [[label(low), label(high)] for low, high in table["support"]]
    source_view = case.view(case.hold(source_table), list(range(len(keep))))
    provenance = {"procedure": procedure, "epoch_definition": epoch_definition}
    effective = (0 if epoch_definition == "bin-start" else 1800, 360000, 720000)
    raw_epochs = (label(1800), label(360000), label(720000))
    rows = [
        {"key": key, "class": old_anchors["rows"][0]["class"], "coordinate": str(at), "source_epoch": raw}
        for key, at, raw in zip(("aligned", "gapped", "late"), effective, raw_epochs, strict=True)
    ]
    source_anchors = {
        "format": "science.series-anchors.v2",
        "axis": absolute,
        "provenance": provenance,
        "rule": chain.rule,
        "rows": [{**row, "coordinate": label(row["coordinate"])} for row in rows],
    }
    anchors = {
        "format": "science.series-anchors.v2",
        "axis": {key: value for key, value in table["axis"].items() if key != "grid"},
        "rule": chain.rule,
        "rows": rows,
        "provenance": provenance,
        "transform": {"source": case.hold(source_anchors), "operation": "clock-map", "procedure": procedure},
    }
    if contradiction == "clock-arithmetic":
        table["coordinates"][0] = str(int(table["coordinates"][0]) + 1)
    elif contradiction == "copied-value":
        table["channels"]["signal"]["values"][0] = "123"
    elif contradiction == "support":
        table["support"][0][0] = str(int(table["support"][0][0]) - 1)
    elif contradiction == "provenance":
        anchors["provenance"] = {**provenance, "epoch_definition": "Undeclared second definition"}
    elif contradiction == "duplicate-epoch":
        anchors["rows"][1]["coordinate"] = anchors["rows"][0]["coordinate"]
    held_table, held_anchors = case.hold(table), case.hold(anchors)
    view = case.view(
        held_table,
        list(range(len(keep))),
        anchors=held_anchors,
        transform={"source": source_view, "operation": "clock-map", "procedure": procedure},
    )
    bindings = {**chain.bindings, "response": replace(response, series=series_ref_from_projection(view))}
    value = build(chain, bindings=bindings)
    assert value.event_coverage is not None
    parameters = {
        **chain.parameters,
        "event_retained_keys": event_retained_keys(value.event_coverage),
        "series_descriptor": "inputs/" + view["resource"].split(":")[1] + ".json",
        "series_table": "inputs/" + held_table["resource"].split(":")[1] + ".json",
        "series_anchors": "inputs/" + held_anchors["resource"].split(":")[1] + ".json",
    }
    return replace(chain, bindings=bindings, estimand=value, parameters=parameters)


def test_event_preparation_complete_chain(preparation_profile, tmp_path):
    chain = preparation_chain(preparation_profile)
    (series,) = check_series(
        chain.estimand, profile=chain.profile, records=chain.case.records, evidence=chain.case.evidence()
    )
    assert isinstance(series.axis, ElapsedAxis) and series.axis.basis == "clock-mapped"
    report = diagnose_event_coverage(
        **chain.bindings,
        coverage_policy="complete-windows",
        profile=chain.profile,
        records=chain.case.records,
        evidence=chain.case.evidence(),
    )
    assert report.retained_keys == ("aligned", "late")
    assert [row.windows for row in report.coverage.report] == [
        ("complete", "complete"),
        ("complete", "support-gap"),
        ("complete", "complete"),
    ]
    result = complete_chain(chain, tmp_path)
    assert Fraction(result.emitted) == Fraction(7, 2)
    assert result.verification.verdict == "passed"
    assert result.audit.checked and result.audit.contradiction is None
    from beliefs import audit
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.verify import build_verification

    absent = audit.check_assessment(
        result.writer.read_view,
        result.assessment,
        profile=chain.profile,
        evidence=replace(result.evidence, series_evidence=None),
    )
    assert not absent.checked and absent.contradiction is None
    unchecked = build_verification(
        result.original.run,
        result.replayed.run,
        specs=result.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + chain.profile.base_contract_identity,
        epoch="invented",
        profile=chain.profile,
        records=chain.case.records,
    )
    assert unchecked.verdict == "inconclusive"


def test_consumer_exact_label_and_bin_start_targets_differ(preparation_profile):
    aligned = preparation_chain(preparation_profile)
    exact = preparation_chain(preparation_profile, epoch_definition="exact-label")
    assert aligned.estimand != exact.estimand
    assert exact.estimand.event_coverage is not None
    assert exact.estimand.event_coverage.report[0].windows == ("partial-bin", "partial-bin")


def complete_chain(chain, work, *, writer=None, job=None):
    from authority import ACTOR
    from fixtures_cut3 import definition
    from test_audit import _stated_optionals, run_publication

    from beliefs import audit, stored
    from beliefs.assess import build_assessment
    from beliefs.boundary import RunMinted, execute_assessment_run
    from beliefs.evidence import DerivationEvidence
    from beliefs.projection import project_claim
    from beliefs.record import AssessmentValue
    from beliefs.register import AssumptionsRegister
    from beliefs.replay import CONTENT_EQUALITY, replay
    from beliefs.spec import SpecInput
    from beliefs.verify import build_verification

    from .test_execution import launch_args
    from .test_portability import writer_at

    writer = writer_at(work / "corpus", chain.profile) if writer is None else writer
    proposition = writer.add(
        stored.proposition_node("prepared-events", title="Invented prepared events", claim=project_claim(chain.claim))
    )
    observed = stored.dataset_node(
        title="Invented underlying observation",
        resources=({"name": "observation", "digest": "sha256:" + sha256(b"fixture observation").hexdigest()},),
        empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
    )
    chain.case.records.nodes[observed.id] = observed
    inputs = tuple(
        SpecInput("reads", row.ref.dataset, "derivation" if row.format == "science.series-table.v2" else "annotation")
        for row in chain.estimand.series_graph
    )
    spec = freeze_chain(
        chain, target=proposition.id, input_roles=(*inputs, SpecInput("observes", observed.id, "observation"))
    )
    for node in chain.case.records.nodes.values():
        writer.add(node)
    for namespace, identity in chain.profile.activated_contracts.items():
        writer.add(stored.assumptions_register_node(AssumptionsRegister(f"{namespace}:{identity}", None, {})))
    writer.add(stored.analysis_spec_node(spec))
    p = SimpleNamespace(case=chain.case, value=chain.estimand, spec=spec, profile=chain.profile)
    args = launch_args(p, work / "runtime")
    job = JOB if job is None else job
    (args["code_roots"][0] / "workflow" / "Snakefile").write_text(job)
    args["definition"] = definition(snakefile=job)
    original = execute_assessment_run(**args)
    assert isinstance(original, RunMinted), original
    replayed = replay(original, **{key: value for key, value in args.items() if key != "boundary_policy"})
    assert isinstance(replayed, RunMinted), replayed
    verification = build_verification(
        original.run,
        replayed.run,
        specs={spec.identity: spec},
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + chain.profile.base_contract_identity,
        epoch="invented",
        series_evidence=chain.case.evidence(),
        profile=chain.profile,
        records=chain.case.records,
    )
    run = writer.add(run_publication(original.run))
    evidence = DerivationEvidence(
        {spec.identity: spec},
        {},
        {RULES[spec.interpretation_rule].identity: RULES[spec.interpretation_rule]},
        series_evidence=chain.case.evidence(),
    )
    derived = build_assessment(original.run, specs=evidence.specs, implementations=evidence.implementations)
    assert isinstance(derived, AssessmentValue)
    assessment = writer.add(
        stored.assessment_node(
            "prepared-events",
            title="Invented event estimate",
            spec=spec.identity,
            run=run.id,
            proposition=proposition.id,
            outcome=derived.outcome,
            interpretation_rule=derived.interpretation_rule,
            **_stated_optionals(derived),
        )
    )
    outcome = audit.check_assessment(writer.read_view, assessment, profile=chain.profile, evidence=evidence)
    emitted = (Path(original.run.occurrence.receipt.execution.scratch_mapping) / "outputs/result.txt").read_text()
    return SimpleNamespace(
        chain=chain,
        writer=writer,
        spec=spec,
        original=original,
        replayed=replayed,
        verification=verification,
        audit=outcome,
        assessment=assessment,
        evidence=evidence,
        emitted=emitted,
    )


@pytest.mark.parametrize(
    "contradiction", ["clock-arithmetic", "copied-value", "support", "provenance", "duplicate-epoch"]
)
def test_event_preparation_rejects_inconsistent_held_pairs(preparation_profile, contradiction):
    from beliefs.series.types import SeriesRefused

    with pytest.raises(SeriesRefused):
        preparation_chain(preparation_profile, contradiction=contradiction)


def test_repeatability_does_not_certify_event_consumption(preparation_profile, tmp_path):
    from beliefs.procedure import Implementation, procedure_from_stored

    from .candidate_case import hold

    chain = preparation_chain(preparation_profile)
    ignoring = JOB.replace(' if row["key"] in retained', "")
    procedure = procedure_from_stored(chain.case.records.read(chain.estimator))
    estimator = hold(
        chain,
        replace(
            procedure,
            definition="Intentionally ignore the retained-key selection in this negative fixture.",
            implementation=Implementation(
                "candidate-chain/Snakefile", "sha256:" + sha256(ignoring.encode()).hexdigest()
            ),
        ),
    )
    chain = replace(chain, estimator=estimator)
    result = complete_chain(chain, tmp_path, job=ignoring)
    assert result.verification.verdict == "passed"
    assert result.audit.checked and result.audit.contradiction is None
    assert Fraction(result.emitted) != Fraction(7, 2)


def test_frozen_report_and_parameter_tampering_refuse(preparation_profile):
    from beliefs.errors import ScienceError
    from beliefs.estimand import estimand_from_stored, estimand_projection
    from beliefs.identity import v1
    from beliefs.spec import SPEC_DOMAIN, frozen_projection, restore

    chain = preparation_chain(preparation_profile)
    body = raw_object(v1.encode(estimand_projection(chain.estimand)))
    body["event_coverage"]["report"][1]["windows"] = ["complete", "complete"]
    forged = estimand_from_stored(body, profile=chain.profile)
    with pytest.raises(ScienceError, match="coverage"):
        check_series(forged, profile=chain.profile, records=chain.case.records, evidence=chain.case.evidence())
    from beliefs.spec import SpecInput

    inputs = tuple(
        SpecInput("reads", row.ref.dataset, "derivation" if row.format == "science.series-table.v2" else "annotation")
        for row in chain.estimand.series_graph
    )
    spec = freeze_chain(chain, input_roles=inputs)
    projection = raw_object(v1.encode(frozen_projection(spec)))
    projection["parameters"]["event_retained_keys"] += "="
    with pytest.raises(ScienceError, match="event_retained_keys"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=chain.profile)


@pytest.mark.parametrize("state", ["complete", "missing-producer", "diverged"])
def test_mapped_response_preserves_inherited_empirical_standing(preparation_profile, tmp_path, state):
    import lineage_fixtures as lineage

    from beliefs import stored
    from beliefs.corpus import _StandingRecords
    from beliefs.errors import UnfreezableSpec
    from beliefs.spec import SpecInput, revise

    from .test_portability import writer_at

    chain = preparation_chain(preparation_profile)
    (checked,) = check_series(
        chain.estimand, profile=chain.profile, records=chain.case.records, evidence=chain.case.evidence()
    )
    dataset = checked.descriptor.table.dataset
    ancestor = lineage.acquired("mapped-ancestor")
    original = chain.case.records.read(dataset)
    derived = stored.dataset_node(
        title="Invented mapped response with complete lineage",
        resources=original.facets["dataset"]["resources"],
        basis={
            "tag": "single",
            "routes": [lineage.route("run:mapped-producer", ancestor.id, identity="route:mapped-producer")],
        },
    )
    assert derived.id == dataset
    chain.case.records.nodes[dataset] = derived
    writer = writer_at(tmp_path / "corpus", chain.profile)
    for node in (*chain.case.records.nodes.values(), ancestor):
        writer.add(node)
    if state != "missing-producer":
        writer.add(lineage.production("mapped-producer", ancestor.id, dataset))
    if state == "diverged":
        other = writer.add(lineage.acquired("other-mapped-ancestor"))
        writer.add(lineage.production("other-mapped-producer", other.id, dataset))
    records = _StandingRecords(writer.read_view)
    inputs = tuple(
        SpecInput("reads", row.ref.dataset, "derivation" if row.format == "science.series-table.v2" else "annotation")
        for row in chain.estimand.series_graph
    )
    spec = freeze_chain(chain, input_roles=inputs)
    observed = tuple(SpecInput("observes", i.dataset, "observation") if i.dataset == dataset else i for i in inputs)
    args = {
        "edits": {"input_roles": (*observed, SpecInput("observes", ancestor.id, "observation"))},
        "held_rules": RULES,
        "rule_procedures": {spec.interpretation_rule: chain.estimator},
        "recorded_failures": frozenset(),
        "profile": chain.profile,
        "claim": chain.claim,
        "records": records,
        "series_evidence": chain.case.evidence(),
    }
    if state == "complete":
        assert revise(spec, **args).input_roles == args["edits"]["input_roles"]
    else:
        with pytest.raises(UnfreezableSpec, match="empirical standing"):
            revise(spec, **args)
    metadata = next(
        row.ref.dataset for row in chain.estimand.series_graph if row.format == "science.series-clock-map.v1"
    )
    assert not records.empirical_standing(metadata, chain.profile)
