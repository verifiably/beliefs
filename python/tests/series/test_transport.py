"""Canonical retained keys travel through the existing recipe, argv and engine config."""

import base64
import json
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest
from fixtures_cut3 import ESTIMATOR_PROCEDURE, definition, freeze_context, spec_draft, spec_rules
from test_estimand import context as context  # noqa: PLC0414

from beliefs.boundary import RunMinted, execute_assessment_run
from beliefs.errors import ScienceError
from beliefs.estimand import LagBinding
from beliefs.identity import v1
from beliefs.recipe import CONFINED_POLICY, MINIMAL_POLICY
from beliefs.restriction import IntervalRestriction
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.coverage import CoverageRow, EventCoverage
from beliefs.spec import SPEC_DOMAIN, freeze, frozen_projection, restore, revise

from .fixtures import raw_object
from .test_authoring import event_case, input_roles
from .test_coverage import build
from .test_execution import launch_args
from .test_portability import persist_case


def encoded(keys):
    return "event-keys.v1." + base64.urlsafe_b64encode(v1.encode(list(keys))).decode("ascii").rstrip("=")


def report(keys):
    return EventCoverage("complete-windows", tuple(CoverageRow(key, ("complete", "complete")) for key in keys))


def transport_case(profile, keys=("01", "a b", "é")):
    case, bindings = event_case(profile)
    root = series_ref_projection(bindings["response"].series)
    assert isinstance(root["resource"], str)
    view = raw_object(case.buffers[root["resource"].split(":")[1]])

    def rows(obj):
        template = obj["rows"][0]
        obj["rows"] = [{**template, "key": key, "coordinate": str(i * 360000)} for i, key in enumerate(keys)]

    anchors = case.rewrite(view["anchors"], rows)
    root = case.rewrite(root, lambda obj: obj.update(anchors=anchors))
    bindings["response"] = replace(bindings["response"], series=series_ref_from_projection(root))
    return case, bindings, build(case, bindings, profile)


def freeze_args(case, profile):
    from fixtures_cut3 import TESTING_CLAIM

    return {
        "held_rules": spec_rules(),
        "rule_procedures": {"median-difference/v1": ESTIMATOR_PROCEDURE},
        "profile": profile,
        "claim": TESTING_CLAIM,
        "records": case.records,
        "series_evidence": case.evidence(),
    }


def test_retained_key_transport_canonical_and_bounded():
    from beliefs.series.transport import event_retained_keys

    keys = ("01", "a b", "é")
    assert event_retained_keys(report(keys)) == encoded(keys)
    assert not event_retained_keys(report(keys)).endswith("=")
    assert json.loads(base64.urlsafe_b64decode(encoded(keys).removeprefix("event-keys.v1.") + "==")) == list(keys)
    near = encoded(("x" * 49130,))
    assert 65504 <= len(near.encode()) <= 65536
    assert event_retained_keys(report(("x" * 49130,))) == near
    with pytest.raises(ScienceError, match="64 KiB"):
        event_retained_keys(report(("x" * 49160,)))
    with pytest.raises(ScienceError, match="retained"):
        event_retained_keys(EventCoverage("complete-windows", (CoverageRow("a", ("outside-support",)),)))


@pytest.mark.parametrize(
    "bad",
    [
        None,
        1,
        ["01", "a b", "é"],
        "",
        "event-keys.v1.abc",
        encoded(("é", "a b", "01")),
        encoded(("01", "a b", "é")) + "=",
        encoded(("01", "other", "é")),
    ],
)
def test_spec_retained_keys_required_and_recomputed(context, bad):
    case, _bindings, value = transport_case(context)
    parameters = {} if bad is None else {"event_retained_keys": bad}
    with pytest.raises(ScienceError, match="event_retained_keys"):
        freeze(
            spec_draft(estimand=value, parameters=parameters, input_roles=input_roles(value)),
            **freeze_args(case, context),
        )


def test_restore_revise_and_non_event_parameter_contract(context):
    case, bindings, value = transport_case(context)
    params = {"event_retained_keys": encoded(("01", "a b", "é"))}
    spec = freeze(
        spec_draft(estimand=value, parameters=params, input_roles=input_roles(value)), **freeze_args(case, context)
    )
    body = raw_object(v1.encode(frozen_projection(spec)))
    body["parameters"]["event_retained_keys"] += "="
    with pytest.raises(ScienceError, match="event_retained_keys"):
        restore(v1.digest(SPEC_DOMAIN, body), v1.encode(body), profile=context)
    bindings["lag"] = LagBinding(
        "si-brochure/hour", (IntervalRestriction("si-brochure/hour", F(-49), F(0), True, False),) * 2
    )
    new_value = build(case, bindings, context)
    with pytest.raises(ScienceError, match="event_retained_keys"):
        revise(spec, edits={"estimand": new_value}, recorded_failures=frozenset(), **freeze_args(case, context))
    revised = revise(
        spec,
        edits={"estimand": new_value, "parameters": {"event_retained_keys": encoded(("a b", "é"))}},
        recorded_failures=frozenset(),
        **freeze_args(case, context),
    )
    assert revised.parameters["event_retained_keys"] == encoded(("a b", "é"))
    with pytest.raises(ScienceError, match="event_retained_keys"):
        freeze(spec_draft(parameters=params), held_rules=spec_rules(), **freeze_context())


JOB = """import base64, json, pathlib
from beliefs.seeds import bind
seed = bind(config)
rule transform:
    output: "outputs/result.txt"
    run:
        seed(rule, wildcards, "model-initialization")
        text = config["event_retained_keys"]
        assert isinstance(text, str) and text.startswith("event-keys.v1.")
        payload = text[len("event-keys.v1."):]
        keys = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode("utf-8"))
        pathlib.Path(output[0]).write_text(json.dumps({"type": type(text).__name__, "value": text, "keys": keys}))
"""


@pytest.mark.parametrize("policy", [MINIMAL_POLICY, CONFINED_POLICY], ids=["minimal", "confined"])
@pytest.mark.parametrize("near_limit", [False, True], ids=["unicode", "near-64KiB"])
def test_real_workflow_observes_exact_key_string(context, certified_work, policy, near_limit):
    from authority import FULL
    from profiles import pins_for

    from beliefs.root import init_corpus_root, open_corpus
    from beliefs.series.transport import event_retained_keys

    keys = ("x" * 49120, "a b", "é") if near_limit else ("01", "a b", "é")
    case, _bindings, value = transport_case(context, keys)
    assert value.event_coverage is not None
    text = event_retained_keys(value.event_coverage)
    if near_limit:
        assert 65504 <= len(text.encode()) <= 65536
    corpus = certified_work / "corpus"
    init_corpus_root(corpus, authority=FULL)
    writer = open_corpus(corpus, authority=FULL, profile=context)
    writer.adopt_manifest(profile=pins_for(context))
    p = persist_case(case, value, context, certified_work, parameters={"event_retained_keys": text}, writer=writer)
    args = launch_args(p, certified_work / "runtime")
    (args["code_roots"][0] / "workflow" / "Snakefile").write_text(JOB)
    args["definition"] = definition(snakefile=JOB)
    args["boundary_policy"] = policy
    outcome = execute_assessment_run(**args)
    assert isinstance(outcome, RunMinted), outcome
    assert outcome.run.recipe.parameters["event_retained_keys"] == text
    receipt = outcome.run.occurrence.receipt.execution
    assert ("event_retained_keys", text) in receipt.rendered_config
    assert "event_retained_keys=" + text in receipt.argv
    output_root = Path(receipt.scratch_mapping)
    if outcome.run.occurrence.receipt.confined:
        output_root /= "out"
    observed = json.loads((output_root / "outputs/result.txt").read_bytes())
    assert observed == {"type": "str", "value": text, "keys": list(keys)}


def test_oversized_canonical_value_refuses_freeze_before_launch(context):
    case, _bindings, value = transport_case(context, ("x" * 49160,))
    with pytest.raises(ScienceError, match="64 KiB"):
        freeze(
            spec_draft(
                estimand=value,
                parameters={"event_retained_keys": encoded(("x" * 49160,))},
                input_roles=input_roles(value),
            ),
            **freeze_args(case, context),
        )
