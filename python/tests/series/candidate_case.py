"""Synthetic solar-wind targets; no data acquisition or scientific assessment."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from candidate_contracts import fragment
from fixtures_cut3 import MEMORY_PORT, UNCONSULTED, definition, seed_plan, spec_rules, stage

from beliefs import stored
from beliefs.applicability import Applicability, ScopedRestriction, build_applicability
from beliefs.boundary import RunMinted, execute_assessment_run
from beliefs.claim import Claim, Referent, build_claim
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.estimand import (
    Binding,
    Control,
    Estimand,
    LagBinding,
    MeasuredBinding,
    OutputSpec,
    RuleAnchor,
    ValueReference,
    build_estimand,
)
from beliefs.measurement import Aspect, Measure, Observable
from beliefs.procedure import Implementation, Procedure
from beliefs.profile import ProfileSpec
from beliefs.recipe import MINIMAL_POLICY
from beliefs.replay import CONTENT_EQUALITY, replay
from beliefs.restriction import IntervalRestriction, TimeIntervalRestriction
from beliefs.series.codec import series_ref_from_projection
from beliefs.spec import FrozenSpec, RuleFixture, RuleImplementation, Seeded, SpecDraft, freeze
from beliefs.verify import build_verification

from .fixtures import SeriesCase
from .test_authoring import input_roles as graph_input_roles

KM, M = "si-brochure/kilometre-per-second", "si-brochure/metre-per-second"
POPULATION = Referent("plasma-populations/near-earth-solar-wind", "plasma-population:near-earth-solar-wind")
HALO = Referent("catalogue-anchors/cdaw-halo-cme", "catalogue-class:cdaw-halo-cme")
ASPECT = Aspect("plasma-populations/bulk-flow-speed", "plasma-aspect:bulk-flow-speed")
OBSERVABLE = Observable("si-brochure/speed", POPULATION.sort, ASPECT)
FUNCTIONAL = "general/mean-within-anchor-window-difference"
NO_AXIS = "candidate-checks/window-difference-without-axis"
WINDOWS = ((-48, 0), (24, 120))
EPOCH = ("2000-01-01T00:00:00Z", "2000-01-17T00:00:00Z")
EXPECTED = Fraction(7, 2)
RULE_DEFINITION = "Synthetic fixture rule. It reproduces no catalogue label."
MEASURING_DEFINITION = "Synthetic fixture measurement. No instrument produced these values."
JOB = """import json, pathlib
from fractions import Fraction
from beliefs.seeds import bind
seed = bind(config)
rule transform:
    input: config["series_descriptor"], config["series_table"], config["series_anchors"]
    output: "outputs/result.txt"
    run:
        seed(rule, wildcards, "model-initialization")
        view, table, anchors = (json.loads(pathlib.Path(path).read_bytes()) for path in input)
        values = table["channels"][view["channel"]]["values"]
        samples = [(Fraction(table["coordinates"][i]), Fraction(values[i])) for i in view["selection"]]
        first = (Fraction(config["first_low"]), Fraction(config["first_high"]))
        second = (Fraction(config["second_low"]), Fraction(config["second_high"]))
        def mean(origin, window):
            chosen = [value for at, value in samples if origin + window[0] <= at < origin + window[1]]
            return sum(chosen) / len(chosen)
        differences = [
            mean(Fraction(row["coordinate"]), second) - mean(Fraction(row["coordinate"]), first)
            for row in anchors["rows"]
        ]
        pathlib.Path(output[0]).write_text(str(sum(differences) / len(differences)))
"""


@dataclass(frozen=True)
class CandidateChain:
    case: SeriesCase
    profile: ProfileSpec
    claim: Claim
    applicability: Applicability
    bindings: Mapping[str, Binding]
    estimand: Estimand
    measuring: str
    estimator: str
    rule: str
    parameters: dict[str, Any]


def checks_contract(base):
    row = dict(fragment("general-event-locked")["rows"]["functionals"]["mean-within-anchor-window-difference"])
    row.pop("response_axis")
    row.pop("definition")
    return parse_domain_contract(
        {
            "contract": "candidate-checks",
            "version": 1,
            "lineage": "genesis",
            "sorts": {
                "coronagraph-feature": {
                    "binding": {"kind": "scheme", "scheme": "candidate-checks", "version": "1"},
                    "identifier_class": {
                        "prefix": "candidate-checks",
                        "pattern": "candidate-checks:coronagraph-feature",
                    },
                }
            },
            "dimensions": {},
            "functionals": {"window-difference-without-axis": row},
            "measurements": {"coronagraph-feature": ["si-brochure/speed"]},
        },
        source="<test-only checks>",
        base=base,
        predecessor=None,
    )


def speed_values(outside: str = "999") -> list[str]:
    values = [outside] * 368
    for low, high, body, last in (
        (0, 48, "399", "447"),
        (72, 168, "408", "600"),
        (200, 248, "449", "497"),
        (272, 368, "445", "637"),
    ):
        values[low : high - 1] = [body] * (high - 1 - low)
        values[high - 1] = last
    return values


def _hold(case: SeriesCase, value: Procedure | ClassificationRule) -> str:
    node = stored.procedure_node(value) if isinstance(value, Procedure) else stored.classification_rule_node(value)
    case.records.nodes[node.id] = node
    return node.id


def hold(chain: CandidateChain, value: Procedure | ClassificationRule) -> str:
    return _hold(chain.case, value)


def candidate_chain(
    profile,
    *,
    unit=KM,
    windows=WINDOWS,
    second_anchor=720000,
    rule_definition=RULE_DEFINITION,
    measuring_definition=MEASURING_DEFINITION,
    outside="999",
    epoch=EPOCH,
    functional=FUNCTIONAL,
    with_series=True,
) -> CandidateChain:
    case = SeriesCase()
    rule = _hold(
        case,
        ClassificationRule(
            classes=HALO.sort,
            reads=(),
            definition=rule_definition,
            external=None,
            implementation=None,
            annotator="synthetic fixture author, not the CDAW catalogue team",
        ),
    )
    measuring = _hold(
        case,
        Procedure(
            kind="general/assay",
            name="Synthetic fixture assay",
            definition=measuring_definition,
            yields=(OBSERVABLE,),
            scale=None,
            validated_in="unknown",
            compatible_with=(),
            evidence=(),
            implementation=None,
            inputs=None,
            parameters={},
            external=None,
        ),
    )
    estimator = _hold(
        case,
        Procedure(
            kind="general/estimator",
            name="Synthetic mean window difference",
            definition="Synthetic fixture estimator.",
            yields=(),
            scale=None,
            validated_in="unknown",
            compatible_with=(),
            evidence=(),
            implementation=Implementation("candidate-chain/Snakefile", "sha256:" + sha256(JOB.encode()).hexdigest()),
            inputs=None,
            parameters={},
            external=None,
        ),
    )
    series = None
    parameters = {}
    if with_series:
        axis = {
            "kind": "elapsed",
            "unit": "si-brochure/second",
            "origin": case.origin(),
            "basis": "synthetic",
            "grid": {"kind": "regular", "spacing": "3600"},
        }
        lows = list(range(-172800, 1152000, 3600))
        values = speed_values(outside)
        if unit == M:
            values = [str(int(value) * 1000) for value in values]
        table = case.table(
            [str(low + 1800) for low in lows],
            axis=axis,
            support=[[str(low), str(low + 3600)] for low in lows],
            channels={
                "signal": {
                    "coordinates": {
                        "quantity_kind": "si-brochure/speed",
                        "unit": unit,
                        "value_type": "level",
                        "transformation": "general/identity",
                    },
                    "values": values,
                }
            },
        )
        anchors = case.hold(
            {
                "format": "science.series-anchors.v2",
                "provenance": {
                    "procedure": case.procedure(
                        kind="general/estimator",
                        name="Synthetic anchor preparation",
                        definition="Declare the synthetic elapsed onsets.",
                    ),
                    "epoch_definition": "Synthetic onset",
                },
                "axis": {key: value for key, value in axis.items() if key != "grid"},
                "rule": rule,
                "rows": [
                    {"key": "synthetic-1", "class": {"sort": HALO.sort, "term": HALO.term}, "coordinate": "0"},
                    {
                        "key": "synthetic-2",
                        "class": {"sort": HALO.sort, "term": HALO.term},
                        "coordinate": str(second_anchor),
                    },
                ],
            }
        )
        view = case.view(table, list(range(len(lows))), anchors=anchors)
        series = series_ref_from_projection(view)
        seconds = [int(Fraction(bound) * 3600) for window in windows for bound in window]
        parameters = {
            "series_descriptor": "inputs/" + view["resource"].split(":")[1] + ".json",
            "series_table": "inputs/" + table["resource"].split(":")[1] + ".json",
            "series_anchors": "inputs/" + anchors["resource"].split(":")[1] + ".json",
            "first_low": seconds[0],
            "first_high": seconds[1],
            "second_low": seconds[2],
            "second_high": seconds[3],
        }
    claim = build_claim(
        profile,
        operator="general/event-locked-change",
        roles={"anchor": HALO, "response": POPULATION},
        layer="statistical",
        form="polar",
        polarity="positive",
    )
    applicability = build_applicability(
        profile,
        claim,
        {"catalogue-anchors/anchor-epoch": ScopedRestriction("generic", TimeIntervalRestriction(*epoch))},
        snapshot=UNCONSULTED,
    )[0]
    bindings = {
        "response": MeasuredBinding(
            "response",
            None,
            Measure(OBSERVABLE, unit, None, "ratio", "level", "general/identity", measuring),
            None,
            None,
            series,
        ),
        "anchor": RuleAnchor(rule, (HALO,)),
        "lag": LagBinding(
            "si-brochure/hour",
            tuple(
                IntervalRestriction("si-brochure/hour", Fraction(low), Fraction(high), True, False)
                for low, high in windows
            ),
        ),
    }
    estimand = _build(profile, claim, case, applicability, bindings, functional)
    return CandidateChain(
        case, profile, claim, applicability, bindings, estimand, measuring, estimator, rule, parameters
    )


def _build(profile, claim, case, initial_applicability, initial_bindings, initial_functional, **overrides) -> Estimand:
    response = initial_bindings["response"]
    assert isinstance(response, MeasuredBinding)
    arguments = {
        "form": "event-locked",
        "coverage_policy": "complete-windows" if response.series is not None else None,
        "functional": initial_functional,
        "bindings": initial_bindings,
        "outputs": {"estimate": OutputSpec("response-difference", "real")},
        "reference": ValueReference(Decimal(0)),
        "control": Control(
            "general/observational", (), "general/within-anchor-windows", "general/annotation-defined-anchors"
        ),
        "uncertainty": "interval",
        "assumptions": (),
        "calibration": None,
        "applicability": initial_applicability,
        "snapshot": UNCONSULTED,
        "records": case.records,
        "series_evidence": case.evidence() if response.series is not None else None,
    }
    arguments.update(overrides)
    return build_estimand(profile, claim, **arguments)[0]


def build(chain: CandidateChain, **overrides) -> Estimand:
    return _build(
        chain.profile,
        chain.claim,
        chain.case,
        chain.applicability,
        chain.bindings,
        chain.estimand.functional,
        **overrides,
    )


RULES = {
    "fixture-constant-supported/v1": RuleImplementation(
        identity="impl-candidate-interp-1",
        evaluate=lambda manifest: {"outcome": "supported"},
        fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
    ),
    "content-identity-equality/v1": spec_rules()["content-identity-equality/v1"],
}


def freeze_chain(chain: CandidateChain, *, target="candidate-proposition", input_roles=None) -> FrozenSpec:
    draft = SpecDraft(
        target=target,
        estimand=chain.estimand,
        method="Synthetic fixture method.",
        assumptions="Synthetic fixture assumptions.",
        falsification="Synthetic fixture falsification.",
        input_roles=graph_input_roles(chain.estimand) if input_roles is None else input_roles,
        applicability=chain.applicability,
        interpretation_rule="fixture-constant-supported/v1",
        equivalence_rule="content-identity-equality/v1",
        parameters=chain.parameters,
        nondeterminism=Seeded(plan=seed_plan()),
        registers=(),
        standing="empirical",
        model=None,
    )
    return freeze(
        draft,
        held_rules=RULES,
        rule_procedures={"fixture-constant-supported/v1": chain.estimator},
        profile=chain.profile,
        claim=chain.claim,
        records=chain.case.records,
        series_evidence=chain.case.evidence(),
    )


def run_chain(chain: CandidateChain, spec: FrozenSpec, root: Path, *, with_replay=True) -> SimpleNamespace:
    code, held = stage(root, snakefile=JOB)
    inputs = {}
    for row in chain.estimand.series_graph:
        name = row.ref.resource.split(":")[1]
        path = held / (name + ".json")
        path.write_bytes(chain.case.buffers[name])
        inputs[row.ref.dataset] = path
    args = {
        "spec": spec,
        "port": MEMORY_PORT,
        "boundary_policy": MINIMAL_POLICY,
        "definition": definition(snakefile=JOB),
        "code_roots": (code,),
        "held_inputs": inputs,
        "entrypoint": "code/workflow/Snakefile",
        "targets": ("outputs/result.txt",),
        "declared_outputs": ("outputs/result.txt",),
        "observer": "fixture",
        "started_at": "2026-11-13T00:00:00Z",
        "host_realization": "fixture",
        "scratch_base": root / "scratch",
        "series_evidence": chain.case.evidence(),
        "profile": chain.profile,
        "records": chain.case.records,
    }
    original = execute_assessment_run(**args)
    assert isinstance(original, RunMinted), original
    emitted = (Path(original.run.occurrence.receipt.execution.scratch_mapping) / "outputs" / "result.txt").read_text()
    replayed = verification = None
    if with_replay:
        replayed = replay(original, **{key: value for key, value in args.items() if key != "boundary_policy"})
        assert isinstance(replayed, RunMinted), replayed
        verification = build_verification(
            original.run,
            replayed.run,
            specs={spec.identity: spec},
            held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
            contract_identity="science:" + chain.profile.base_contract_identity,
            epoch="candidate-fixture",
            series_evidence=chain.case.evidence(),
            profile=chain.profile,
            records=chain.case.records,
        )
    return SimpleNamespace(original=original, replayed=replayed, verification=verification, emitted=emitted)


def proposition_of(chain: CandidateChain):
    from beliefs.target import AssessedTarget
    from beliefs.target_comparison import AssessedProposition

    return AssessedProposition(
        chain.claim,
        AssessedTarget(chain.estimand, chain.applicability, chain.estimand.dependencies, None, "empirical"),
        "fixture-constant-supported/v1",
    )
