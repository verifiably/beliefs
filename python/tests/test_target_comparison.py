"""Compare whole targets before applying declared A-to-B numerical actions."""

from dataclasses import replace
from decimal import Context
from decimal import Decimal as D
from fractions import Fraction as F
from typing import Any, cast

import pytest
from fixtures_cut3 import MEASUREMENT_RECORDS, RESPONSE, TESTING_CLAIM, typed_estimand
from test_convert import compile_testing, snapshot
from test_dependencies import Records
from test_estimand import build
from test_estimand import context as context  # noqa: PLC0414
from test_procedure import procedure
from test_standing import calibrated_prediction

from beliefs import comparability as c
from beliefs import stored
from beliefs.applicability import Applicability, ScopedRestriction
from beliefs.claim import Member, Referent, build_claim
from beliefs.estimand import (
    Control,
    DatasetBinding,
    IncrementBinding,
    LagBinding,
    MeasuredBinding,
    NullReference,
    OutputSpec,
    RoleAnchor,
    RoleBinding,
    RoleTermLevels,
    ValueReference,
)
from beliefs.measurement import Measure, Observable
from beliefs.restriction import IntervalRestriction
from beliefs.target import AssessedTarget, target_projection


@pytest.fixture()
def lab(context, base_contract, testing_document, monkeypatch):
    row = testing_document["functionals"]["difference-of-means"]
    testing_document["functionals"]["temperature-level"] = {
        **row,
        "form": "quantity",
        "arity": "one",
        "reversal": "not-applicable",
        "increment": "not-applicable",
        "output": "response-level",
    }
    testing_document["functionals"]["undefined-reversal"] = {
        **testing_document["functionals"]["probability-of-superiority"],
        "response_reversal": "undefined",
    }
    testing_document["functionals"]["undefined-level-reversal"] = {
        **testing_document["functionals"]["probability-of-superiority"],
        "reversal": "undefined",
    }
    testing_document["dimensions"]["age"] = dict(testing_document["dimensions"]["follow-up"])
    testing_document["units"]["year"] = {
        "symbol": "yr",
        "quantity_kind": "duration",
        "calendar": True,
        "definition": "A civil year of age.",
    }
    lab = Lab(compile_testing(base_contract, testing_document))
    monkeypatch.setattr(lab.records, "observation_held", lambda digest: True)
    return lab


class Lab:
    def __init__(self, profile):
        self.profile = profile
        self.records = Records()
        self.records.nodes.update(MEASUREMENT_RECORDS.nodes)
        self.event = Referent("testing/event", "EX:event")
        self.product = Referent("testing/product", "EX:product")
        self.event_claim = build_claim(
            profile,
            operator="testing/correlates-with",
            roles={"parties": (Member(self.event), Member(self.product))},
            layer="statistical",
            polarity="positive",
        )

    def measured(
        self,
        *,
        role="cause",
        member=None,
        kind="abundance",
        unit="tpm",
        transformation="identity",
        aspect=None,
        procedure_id=None,
    ):
        ref = member if member is not None else TESTING_CLAIM.roles[role]
        assert isinstance(ref, Referent)
        sort = ref.sort
        observable = Observable("testing/" + kind, sort, aspect)
        pid = procedure_id or self.records.put(procedure(name=role, yields=(observable,)))
        return MeasuredBinding(
            role,
            member,
            Measure(observable, "testing/" + unit, None, "ratio", "level", "testing/" + transformation, pid),
            None,
            None,
        )

    def target(
        self,
        *,
        claim=TESTING_CLAIM,
        form="contrast",
        functional="difference-of-means",
        response=None,
        bindings=None,
        outputs=None,
        reference=None,
        scope=None,
        control=None,
        assumptions=(),
    ):
        from beliefs.target_comparison import AssessedProposition

        f = self.profile.functionals["testing/" + functional].declaration
        if bindings is None:
            bindings = {"response": response or RESPONSE}
            if form == "contrast":
                bindings["grouping"] = RoleTermLevels(
                    "cause", None, (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
                )
        if outputs is None:
            outputs = {"estimate": OutputSpec(f.output, f.domain)}
        if reference is None:
            reference = ValueReference({"half": D(".5"), "one": D(1)}.get(f.null, D(0)))
        if isinstance(reference, NullReference):
            claim = build_claim(
                self.profile,
                operator=claim.operator,
                roles=claim.roles,
                qualifiers=claim.qualifiers,
                layer=claim.layer,
                form="null",
            )
        kwargs = {} if control is None else {"control": control}
        app = Applicability({} if scope is None else scope)
        e = build(
            self.profile,
            claim,
            form=form,
            functional="testing/" + functional,
            bindings=bindings,
            outputs=outputs,
            reference=reference,
            applicability=app,
            records=self.records,
            uncertainty="covariance" if len(outputs) > 1 else "interval",
            assumptions=assumptions,
            **kwargs,
        )
        return AssessedProposition(claim, AssessedTarget(e, app, e.dependencies, None, "empirical"), "rule")

    def conversion_ctx(self):
        return {
            "profile": self.profile,
            "snapshot": snapshot(self.records, profile=self.profile),
            "snapshot_identity": "snapshot:comparison",
        }

    def synthesis_ctx(self, proxies=lambda _a, _b: ()):
        return {**self.conversion_ctx(), "observable_proxies": proxies}


from beliefs.target_comparison import (
    ConversionVerdict,
    PermittedUnder,
    SynthesisRefused,
    SynthesisVerdict,
    TargetConvertible,
    TargetNotConvertible,
    TargetUnknown,
)


def only_convertible(result: ConversionVerdict) -> TargetConvertible:
    assert isinstance(result, TargetConvertible), result
    return result


def only_refusal(
    result: ConversionVerdict | SynthesisVerdict,
) -> TargetNotConvertible | TargetUnknown | SynthesisRefused:
    assert isinstance(result, (TargetNotConvertible, TargetUnknown, SynthesisRefused)), result
    return result


def with_assumptions(result: ConversionVerdict | SynthesisVerdict) -> TargetConvertible | PermittedUnder:
    assert isinstance(result, (TargetConvertible, PermittedUnder)), result
    return result


def mapped(answer, value):
    assert answer.kind == "convertible"
    return c.apply_estimate(only_convertible(answer).outputs["estimate"].steps, D(value))


@pytest.mark.parametrize(
    "response_flip,level_flip,want",
    [(False, False, ".3"), (True, False, ".7"), (False, True, ".7"), (True, True, ".3")],
)
def test_probability_flips_compose_once(lab, response_flip, level_flip, want):
    from beliefs.target_comparison import convertibility

    source = lab.measured()
    target = (
        replace(source, measure=replace(source.measure, transformation="testing/negate")) if response_flip else source
    )
    a = lab.target(functional="probability-of-superiority", response=source)
    grouping = a.target.estimand.bindings["grouping"]
    b = lab.target(
        functional="probability-of-superiority",
        bindings={
            "response": target,
            "grouping": replace(grouping, levels=tuple(reversed(grouping.levels))) if level_flip else grouping,
        },
    )
    assert mapped(convertibility(a, b, **lab.conversion_ctx()), ".3") == D(want)


@pytest.mark.parametrize("change", ["level-set", "role", "member", "output-names", "functional"])
def test_correspondence_precedes_conversion(lab, monkeypatch, change):
    from beliefs import target_comparison as t

    a = lab.target()
    bindings = dict(a.target.estimand.bindings)
    kwargs = {}
    if change == "level-set":
        bindings["grouping"] = replace(
            bindings["grouping"], levels=(Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:c"))
        )
    elif change == "role":
        bindings["response"] = lab.measured(role="effect", kind="score", unit="point")
    elif change == "member":
        changed = build_claim(
            lab.profile,
            operator=TESTING_CLAIM.operator,
            roles={**TESTING_CLAIM.roles, "cause": Referent("testing/entity", "EX:another")},
            layer="causal",
            polarity="positive",
        )
        kwargs["claim"] = changed
        bindings["response"] = lab.measured()
    elif change == "functional":
        kwargs["functional"] = "hodges-lehmann-shift"
    b = lab.target(bindings=bindings, **kwargs)
    if change == "output-names":
        # A structurally readable stored target can carry an unrecognized output name.
        body = cast(dict[str, Any], target_projection(b.target))
        body["estimand"]["outputs"] = {"other": {"typing": "response-difference", "domain": "real"}}
        from beliefs.errors import EstimandError
        from beliefs.target import target_from_projection

        with pytest.raises(EstimandError, match="output names"):
            target_from_projection(body, standing="empirical", profile=lab.profile)
        return
    monkeypatch.setattr(t, "convert", lambda *_a, **_k: pytest.fail("numeric conversion preceded correspondence"))
    result = t.convertibility(a, b, **lab.conversion_ctx())
    assert result.kind == "not-convertible"
    assert only_refusal(result).reason == ("functional" if change == "functional" else "target")
    assert result.snapshot == "snapshot:comparison"


@pytest.mark.parametrize(
    "kind,low,high,want",
    [
        ("probability-of-superiority", ".45", ".55", "permitted"),
        ("ratio-of-means", ".8", "1.25", "permitted"),
        ("ratio-of-means", ".8", "1.5", "refused"),
    ],
)
def test_exact_region_invariance_under_level_reversal(lab, kind, low, high, want):
    from beliefs.target_comparison import synthesis

    a = lab.target(functional=kind, reference=NullReference(D(low), D(high)))
    bindings = dict(a.target.estimand.bindings)
    bindings["grouping"] = replace(bindings["grouping"], levels=tuple(reversed(bindings["grouping"].levels)))
    b = lab.target(functional=kind, bindings=bindings, reference=NullReference(D(low), D(high)))
    for left, right in ((a, b), (b, a)):
        result = synthesis(left, right, **lab.synthesis_ctx())
        assert result.kind == want
        if want == "refused":
            assert only_refusal(result).reason == "reference"


def test_offset_regions_compare_in_both_directions(lab):
    from beliefs.target_comparison import synthesis

    a_measure = lab.measured(role="parties", member=lab.event, kind="temperature", unit="kelvin")
    b_measure = replace(a_measure, measure=replace(a_measure.measure, unit="testing/celsius"))
    a = lab.target(
        claim=lab.event_claim,
        form="quantity",
        functional="temperature-level",
        response=a_measure,
        reference=NullReference(D(0), D(300)),
    )
    b = lab.target(
        claim=lab.event_claim,
        form="quantity",
        functional="temperature-level",
        response=b_measure,
        reference=NullReference(D("-273.15"), D("26.85")),
    )
    assert synthesis(a, b, **lab.synthesis_ctx()).kind == "permitted"
    assert synthesis(b, a, **lab.synthesis_ctx()).kind == "permitted"
    wrong = lab.target(
        claim=lab.event_claim,
        form="quantity",
        functional="temperature-level",
        response=b_measure,
        reference=NullReference(D(0), D(300)),
    )
    assert only_refusal(synthesis(a, wrong, **lab.synthesis_ctx())).reason == "reference"


def law(lab, *, temperature="kelvin", rate="per-second", energy="electronvolt", functional="arrhenius"):
    response = lab.measured(role="parties", member=lab.event, kind="rate", unit=rate)
    independent = lab.measured(role="parties", member=lab.event, kind="temperature", unit=temperature)
    outputs = {
        "Ea": OutputSpec(
            "independent", "real", lab.profile.units["testing/" + energy].quantity_kind, "testing/" + energy
        ),
        "lnA": OutputSpec("response-log-level", "real"),
    }
    if functional == "power-law-floor":
        outputs = {"beta": OutputSpec("dimensionless", "real")}
    return lab.target(
        claim=lab.event_claim,
        form="law-parameters",
        functional=functional,
        bindings={"response": response, "independent": (("temperature", independent),)},
        outputs=outputs,
        reference={n: ValueReference(D(0)) for n in outputs},
    )


def test_independent_variable_refuses_before_log_shift(lab, monkeypatch):
    from beliefs.target_comparison import convertibility, synthesis

    a, b = law(lab), law(lab, temperature="celsius", rate="per-hour")
    before = (target_projection(a.target), target_projection(b.target))
    calls = []
    original = c._output_steps

    def output_steps(*args):
        if args[2].typing == "response-log-level":
            calls.append(args)
        return original(*args)

    monkeypatch.setattr(c, "_output_steps", output_steps)
    for result in (convertibility(a, b, **lab.conversion_ctx()), synthesis(a, b, **lab.synthesis_ctx())):
        assert only_refusal(result).reason == "independent-variable map"
        assert result.snapshot == "snapshot:comparison"
    assert calls == []
    assert (target_projection(a.target), target_projection(b.target)) == before


def test_law_parameters_map_each_output_once_and_covariance_once(lab, monkeypatch):
    from beliefs import target_comparison as t

    a, b = law(lab), law(lab, rate="per-hour", energy="kilojoule-per-mole")
    independent_calls = []
    original = t.convert

    def convert(*args, **kwargs):
        if kwargs["binding"] == "certified" and kwargs["output"].typing == "independent":
            independent_calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(t, "convert", convert)
    result = t.convertibility(a, b, **lab.conversion_ctx())
    assert result.kind == "convertible" and len(independent_calls) == 1
    assert c.apply_estimate(only_convertible(result).outputs["Ea"].steps, D(1)) == D("96.48533212")
    assert c.apply_estimate(only_convertible(result).outputs["lnA"].steps, D(2)) == Context(prec=34).add(
        D(2), Context(prec=34).ln(D(3600))
    )
    assert c.apply_covariance(
        {n: v.steps for n, v in only_convertible(result).outputs.items()}, ("Ea", "lnA"), (D(1), D(2), D(2), D(3))
    ) == (D("9309.4193143067036944"), D("192.97066424"), D("192.97066424"), D(3))
    assert (
        only_convertible(
            t.convertibility(
                law(lab, functional="power-law-floor"),
                law(lab, rate="per-hour", functional="power-law-floor"),
                **lab.conversion_ctx(),
            )
        )
        .outputs["beta"]
        .steps
        == ()
    )


@pytest.mark.parametrize("flipped,want", [((), ".4"), (("x",), "-.4"), (("y",), "-.4"), (("x", "y"), ".4")])
def test_association_variable_actions_compose(lab, flipped, want):
    from beliefs.target_comparison import convertibility

    rows = (("x", lab.measured()), ("y", lab.measured(role="effect", kind="score", unit="point")))
    kwargs = {
        "form": "association",
        "functional": "spearman-correlation",
        "outputs": {"estimate": OutputSpec("dimensionless", "signed-unit-interval")},
    }
    a = lab.target(bindings={"variables": rows}, **kwargs)
    b = lab.target(
        bindings={
            "variables": tuple(
                (n, replace(v, measure=replace(v.measure, transformation="testing/negate"))) if n in flipped else (n, v)
                for n, v in rows
            )
        },
        **kwargs,
    )
    result = convertibility(a, b, **lab.conversion_ctx())
    assert mapped(result, ".4") == D(want)
    output = only_convertible(result).outputs["estimate"]
    assert output.map.decreasing == (len(flipped) % 2 == 1)
    assert output.flip == ("negate" if len(flipped) % 2 else None)
    if flipped:
        assert only_convertible(result).outputs["estimate"].uncertainty == "needs-operands"


def test_directed_variable_order_and_independent_names_correspond(lab):
    from beliefs.target_comparison import convertibility

    rows = (("x", lab.measured()), ("y", lab.measured(role="effect", kind="score", unit="point")))
    kwargs = {
        "form": "association",
        "functional": "transfer-entropy",
        "outputs": {"estimate": OutputSpec("dimensionless", "nonnegative")},
    }
    a = lab.target(bindings={"variables": rows}, **kwargs)
    b = lab.target(bindings={"variables": tuple(reversed(rows))}, **kwargs)
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"
    a = law(lab)
    rows = a.target.estimand.bindings["independent"]
    b = lab.target(
        claim=lab.event_claim,
        form="law-parameters",
        functional="arrhenius",
        bindings={"response": a.target.estimand.bindings["response"], "independent": (("other", rows[0][1]),)},
        outputs=a.target.estimand.outputs,
        reference=a.target.estimand.reference,
    )
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"


def test_undefined_reversal_and_unknown_keep_snapshot(lab):
    from beliefs.target_comparison import convertibility

    source = lab.measured()
    target = replace(source, measure=replace(source.measure, transformation="testing/negate"))
    a = lab.target(functional="undefined-reversal", response=source)
    b = lab.target(functional="undefined-reversal", response=target)
    result = convertibility(a, b, **lab.conversion_ctx())
    assert only_refusal(result).reason == "response reversal" and result.snapshot == "snapshot:comparison"
    a = lab.target(
        functional="probability-of-superiority",
        response=replace(source, measure=replace(source.measure, transformation="testing/standardize")),
    )
    b = lab.target(
        functional="probability-of-superiority",
        response=replace(source, measure=replace(source.measure, transformation="testing/log2-plus-one")),
    )
    result = convertibility(a, b, **lab.conversion_ctx())
    assert result.kind == "unknown" and result.snapshot == "snapshot:comparison"


def test_increment_scaling_and_event_anchor_lag_and_universe(lab):
    from beliefs.target_comparison import convertibility

    grouping = IncrementBinding("cause", None, RESPONSE.measure, D(1), "testing/tpm")
    a = lab.target(bindings={"response": RESPONSE, "grouping": grouping})
    b = lab.target(bindings={"response": RESPONSE, "grouping": replace(grouping, increment=D(10))})
    assert mapped(convertibility(a, b, **lab.conversion_ctx()), "2") == D(20)
    anchor = RoleAnchor("cause", None, Referent("testing/entity", "EX:a"))
    windows = (
        IntervalRestriction("testing/hour", F(0), F(1), True, False),
        IntervalRestriction("testing/hour", F(1), F(2), True, False),
    )
    kwargs = {"form": "event-locked", "functional": "window-difference-against-control"}
    a = lab.target(
        bindings={"response": RESPONSE, "anchor": anchor, "lag": LagBinding("testing/hour", windows)}, **kwargs
    )
    b = lab.target(
        bindings={
            "response": RESPONSE,
            "anchor": replace(anchor, category=Referent("testing/entity", "EX:b")),
            "lag": LagBinding("testing/hour", windows),
        },
        **kwargs,
    )
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"
    # An enrichment's reference set and universe are target meaning too.
    bindings = {
        "membership": RoleBinding("parties", None),
        "reference_set": RoleBinding("parties", lab.product),
        "universe": DatasetBinding("sha256:" + "a" * 64),
    }
    kwargs = {"claim": lab.event_claim, "form": "enrichment", "functional": "enrichment-score"}
    a = lab.target(bindings=bindings, **kwargs)
    b = lab.target(bindings={**bindings, "universe": DatasetBinding("sha256:" + "b" * 64)}, **kwargs)
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"


@pytest.mark.parametrize(
    "relation,want", [("equal", "permitted"), ("narrower", "permitted-under"), ("disjoint", "refused")]
)
def test_scope_transport_and_control(lab, relation, want):
    from beliefs.target_comparison import synthesis

    def scope(low, high):
        return {
            "testing/age": ScopedRestriction(
                "generic", IntervalRestriction("testing/hour", F(low), F(high), True, False)
            )
        }

    a = lab.target(scope=scope(1, 3))
    b = lab.target(scope=scope(*({"equal": (1, 3), "narrower": (1, 2), "disjoint": (4, 5)}[relation])))
    result = synthesis(a, b, **lab.synthesis_ctx())
    assert result.kind == want
    if relation == "narrower":
        assert with_assumptions(result).assumptions[0].kind == "testing/transport-exchangeability"
    if relation == "disjoint":
        assert only_refusal(result).reason == "scope"
    other = lab.target(
        control=Control("testing/instrumental", (), "testing/independent-groups", "testing/cohort-enrolment")
    )
    assert only_refusal(synthesis(lab.target(), other, **lab.synthesis_ctx())).reason == "control"


def test_standing_is_checked_after_all_other_synthesis_stages(lab):
    from beliefs.target_comparison import AssessedProposition, synthesis

    spec, claim, records, _ = calibrated_prediction()
    response = spec.estimand.bindings["response"]
    assert isinstance(response, MeasuredBinding)
    instrument = stored.procedure_node(
        procedure(name="empirical equivalent", yields=(response.measure.observable,), compatible_with=(spec.model,))
    )
    records.nodes[instrument.id] = instrument
    empirical = typed_estimand(
        claim=claim,
        form="quantity",
        functional=spec.estimand.functional,
        bindings={"response": replace(response, measure=replace(response.measure, procedure=instrument.id))},
        outputs=spec.estimand.outputs,
        reference=spec.estimand.reference,
        control=spec.estimand.control,
        records=records,
    )
    left = AssessedProposition(
        claim,
        AssessedTarget(empirical, spec.applicability, empirical.dependencies, None, "empirical"),
        spec.interpretation_rule,
    )
    right = AssessedProposition(claim, spec.assessed_target, spec.interpretation_rule)
    before = (target_projection(left.target), target_projection(right.target))
    ctx = {
        "profile": lab.profile,
        "snapshot": snapshot(records, profile=lab.profile),
        "snapshot_identity": "snapshot:standing",
        "observable_proxies": lambda _a, _b: (),
    }
    result = synthesis(left, right, **ctx)
    assert only_refusal(result).reason == "standing"
    assert (target_projection(left.target), target_projection(right.target)) == before


def test_comparison_is_read_only(lab, monkeypatch):
    from beliefs.corpus import CorpusWriter
    from beliefs.target_comparison import convertibility, synthesis

    a = lab.target()

    def write(*_a, **_k):
        pytest.fail("comparison attempted a write")

    monkeypatch.setattr(CorpusWriter, "add", write)
    monkeypatch.setattr(stored, "assessment_node", write)
    assert convertibility(a, a, **lab.conversion_ctx()).kind == "convertible"
    assert synthesis(a, a, **lab.synthesis_ctx()).kind == "permitted"


def test_axis_level_correspondence_uses_the_full_affine_map(lab):
    from beliefs.estimand import AxisLevels
    from beliefs.target_comparison import convertibility

    a_measure = lab.measured(role="parties", member=lab.event, kind="temperature", unit="kelvin")
    b_measure = replace(a_measure, measure=replace(a_measure.measure, unit="testing/celsius", level="interval"))

    def interval(unit, lo, hi):
        return IntervalRestriction("testing/" + unit, F(lo), F(hi), True, False)

    a_levels = AxisLevels((interval("kelvin", 0, "273.15"), interval("kelvin", "273.15", 300)))
    b_levels = AxisLevels((interval("celsius", "-273.15", 0), interval("celsius", 0, "26.85")))
    a = lab.target(claim=lab.event_claim, bindings={"response": a_measure, "grouping": a_levels})
    b = lab.target(claim=lab.event_claim, bindings={"response": b_measure, "grouping": b_levels})
    assert convertibility(a, b, **lab.conversion_ctx()).kind == "convertible"


def test_many_member_rule_classes_and_lag_correspond(lab):
    from beliefs.classification_rule import ClassificationRule
    from beliefs.estimand import RuleAnchor, RuleClassLevels
    from beliefs.target_comparison import convertibility

    extra = Referent("testing/event", "EX:other")
    claim = build_claim(
        lab.profile,
        operator="testing/correlates-with",
        roles={"parties": (Member(lab.event), Member(lab.product))},
        layer="statistical",
        polarity="positive",
    )
    x = lab.measured(role="parties", member=lab.event, kind="energy", unit="electronvolt")
    other = lab.measured(role="parties", member=extra, kind="energy", unit="electronvolt")
    y = lab.measured(role="parties", member=lab.product)
    kwargs = {
        "claim": claim,
        "form": "association",
        "functional": "spearman-correlation",
        "outputs": {"estimate": OutputSpec("dimensionless", "signed-unit-interval")},
    }
    a = lab.target(bindings={"variables": (("x", x), ("y", y))}, **kwargs)
    other_claim = build_claim(
        lab.profile,
        operator="testing/correlates-with",
        roles={"parties": (Member(extra), Member(lab.product))},
        layer="statistical",
        polarity="positive",
    )
    b = lab.target(bindings={"variables": (("x", other), ("y", y))}, **{**kwargs, "claim": other_claim})
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"
    rule = stored.classification_rule_node(
        ClassificationRule("testing/entity", (RESPONSE.measure.observable,), "Classify A/B", None, None, None)
    )
    another = stored.classification_rule_node(
        ClassificationRule("testing/entity", (RESPONSE.measure.observable,), "Another classification", None, None, None)
    )
    lab.records.nodes.update({n.id: n for n in (rule, another)})
    classes = (Referent("testing/entity", "EX:a"), Referent("testing/entity", "EX:b"))
    a = lab.target(bindings={"response": RESPONSE, "grouping": RuleClassLevels(rule.id, classes)})
    b = lab.target(bindings={"response": RESPONSE, "grouping": RuleClassLevels(another.id, classes)})
    assert only_refusal(convertibility(a, b, **lab.conversion_ctx())).reason == "target"
    windows = (
        IntervalRestriction("testing/hour", F(0), F(1), True, False),
        IntervalRestriction("testing/hour", F(1), F(2), True, False),
    )
    seconds = (
        IntervalRestriction("testing/second", F(0), F(3600), True, False),
        IntervalRestriction("testing/second", F(3600), F(7200), True, False),
    )
    kwargs = {"form": "event-locked", "functional": "window-difference-against-control"}
    a = lab.target(
        bindings={
            "response": RESPONSE,
            "anchor": RuleAnchor(rule.id, classes),
            "lag": LagBinding("testing/hour", windows),
        },
        **kwargs,
    )
    b = lab.target(
        bindings={
            "response": RESPONSE,
            "anchor": RuleAnchor(rule.id, classes),
            "lag": LagBinding("testing/second", seconds),
        },
        **kwargs,
    )
    assert convertibility(a, b, **lab.conversion_ctx()).kind == "convertible"
    wrong = lab.target(
        bindings={
            "response": RESPONSE,
            "anchor": RuleAnchor(another.id, classes),
            "lag": LagBinding("testing/hour", windows),
        },
        **kwargs,
    )
    assert only_refusal(convertibility(a, wrong, **lab.conversion_ctx())).reason == "target"


def test_monotone_rank_synthesis_and_symbolic_reference_unknown(lab):
    from beliefs.target_comparison import synthesis

    source = lab.measured()
    target = replace(source, measure=replace(source.measure, transformation="testing/log2-plus-one"))
    a = lab.target(functional="probability-of-superiority", response=source)
    b = lab.target(functional="probability-of-superiority", response=target)
    assert synthesis(a, b, **lab.synthesis_ctx()).kind == "permitted"
    a = lab.target(
        response=replace(source, measure=replace(source.measure, level="interval", transformation="testing/ln")),
        reference=ValueReference(D(1)),
    )
    b = lab.target(
        response=replace(source, measure=replace(source.measure, level="interval", transformation="testing/log2")),
        reference=ValueReference(D("1.442695040888963407359924681001892")),
    )
    result = synthesis(a, b, **lab.synthesis_ctx())
    assert result.kind == "unknown" and only_refusal(result).reason == "reference"


@pytest.mark.parametrize(
    "validity,eligible,want",
    [
        ("full", True, "permitted-under"),
        ("partial", True, "permitted-under"),
        ("disjoint", True, "refused"),
        ("full", False, "refused"),
    ],
)
def test_observable_proxy_validity_and_eligibility(lab, validity, eligible, want):
    from beliefs.assumptions import AssumptionInstance
    from beliefs.measurement import Aspect
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget
    from beliefs.target_comparison import convertibility, synthesis

    apparent = Observable("testing/energy", lab.event.sort, Aspect("testing/energy-aspect", "EX:apparent"))
    intrinsic = replace(apparent, aspect=Aspect("testing/energy-aspect", "EX:intrinsic"))
    proc = lab.records.put(procedure(yields=(apparent, intrinsic)))
    x = lab.measured(
        role="parties", member=lab.event, kind="energy", unit="electronvolt", aspect=apparent.aspect, procedure_id=proc
    )
    y = replace(x, measure=replace(x.measure, observable=intrinsic))

    def scope(lo, hi):
        return {
            "testing/age": ScopedRestriction("generic", IntervalRestriction("testing/hour", F(lo), F(hi), True, False))
        }

    a = lab.target(
        claim=lab.event_claim, form="quantity", functional="temperature-level", response=x, scope=scope(2, 4)
    )
    b = lab.target(
        claim=lab.event_claim, form="quantity", functional="temperature-level", response=y, scope=scope(2, 4)
    )
    assert convertibility(a, b, **lab.conversion_ctx()).kind == "convertible"
    assert only_refusal(synthesis(a, b, **lab.synthesis_ctx())).reason == "observable"
    bounds = {"full": (1, 5), "partial": (3, 5), "disjoint": (5, 6)}[validity]
    proxy = stored.proxy_model_node(
        ProxyModel(
            ProxySource(apparent, proc),
            ProxyTarget(intrinsic, None),
            Applicability(scope(*bounds)).restrictions(),
            AssumptionInstance("testing/proxy-validity", {"record": "bridge", "co_scope": "equal", "dimensions": ""}),
            None,
        )
    )
    lab.records.nodes[proxy.id] = proxy
    ctx = lab.synthesis_ctx(lambda _a, _b: (proxy.id,))
    ctx["snapshot"] = snapshot(lab.records, profile=lab.profile, refused=None if eligible else proxy.id)
    result = synthesis(a, b, **ctx)
    assert result.kind == want
    if want == "refused":
        assert only_refusal(result).reason == "observable"
    if validity == "partial":
        assert any(v.particulars.get("record") == proxy.id for v in with_assumptions(result).assumptions)


def crosswalk_targets(lab, *, validity=None):
    from beliefs.assumptions import AssumptionInstance
    from beliefs.procedure import Scale
    from beliefs.proxy_model import Conversion, Crosswalk, Error, ProxyModel, ProxySource, ProxyTarget

    observable = Observable("testing/score", "testing/outcome")
    a = lab.records.put(procedure(name="FACIT", yields=(observable,), scale=Scale(F(0), F(52), "higher-is-less")))
    b = lab.records.put(procedure(name="Chalder", yields=(observable,), scale=Scale(F(0), F(33), "higher-is-more")))
    model = stored.proxy_model_node(
        ProxyModel(
            ProxySource(observable, a),
            ProxyTarget(None, b),
            {} if validity is None else validity,
            AssumptionInstance(
                "testing/proxy-validity", {"record": "declared link", "co_scope": "equal", "dimensions": ""}
            ),
            Crosswalk({}, Conversion("affine", F(-2), F(10)), Error("standard-error", F("1.4"))),
        )
    )
    lab.records.nodes[model.id] = model
    left = MeasuredBinding(
        "effect", None, Measure(observable, None, a, "interval", "level", "testing/identity", a), None, None
    )
    right = replace(left, measure=replace(left.measure, scale=b, procedure=b))
    return left, right, model.id


def test_scale_crosswalk_keeps_recorded_error_and_drops_uncertainty(lab):
    from beliefs.target_comparison import convertibility, synthesis

    left, right, proxy = crosswalk_targets(lab)
    a = lab.target(functional="probability-of-superiority", response=left)
    b = lab.target(functional="probability-of-superiority", response=right)
    result = convertibility(a, b, **lab.conversion_ctx())
    assert only_convertible(result).outputs["estimate"].uncertainty == "not-carried: crosswalk"
    assert any(
        v.particulars.get("error") == "1.4" and v.particulars.get("record") == proxy
        for v in with_assumptions(result).assumptions
    )
    assert synthesis(a, b, **lab.synthesis_ctx()).kind == "permitted-under"


def test_one_variables_crosswalk_does_not_license_another_procedure(lab):
    from beliefs.target_comparison import synthesis

    left, right, _ = crosswalk_targets(lab)
    x = lab.measured()
    other = lab.records.put(procedure(name="Incompatible abundance method", yields=(x.measure.observable,)))
    y = replace(x, measure=replace(x.measure, procedure=other))
    kwargs = {
        "form": "association",
        "functional": "spearman-correlation",
        "outputs": {"estimate": OutputSpec("dimensionless", "signed-unit-interval")},
    }
    a = lab.target(bindings={"variables": (("score", left), ("abundance", x))}, **kwargs)
    b = lab.target(bindings={"variables": (("score", right), ("abundance", y))}, **kwargs)
    result = synthesis(a, b, **lab.synthesis_ctx())
    assert result.kind == "refused" and only_refusal(result).reason == "procedure"


def test_a_binding_proxy_is_checked_even_when_target_observables_match(lab):
    from beliefs.assumptions import AssumptionInstance
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget
    from beliefs.referent_mapping import ReferentMapping
    from beliefs.target_comparison import synthesis

    source = RESPONSE.measure.observable
    mapping = lab.records.put(ReferentMapping(source.bearer_sort, source.bearer_sort, {}, "one-to-one", None, None))
    proxy = lab.records.put(
        ProxyModel(
            ProxySource(source, RESPONSE.measure.procedure),
            ProxyTarget(source, None),
            {},
            AssumptionInstance(
                "testing/proxy-validity", {"record": "identity bridge", "co_scope": "equal", "dimensions": ""}
            ),
            None,
        )
    )
    target = lab.target(response=replace(RESPONSE, mapping=mapping, proxy=proxy))
    ctx = lab.synthesis_ctx()
    ctx["snapshot"] = snapshot(lab.records, profile=lab.profile, refused=proxy)
    result = synthesis(target, target, **ctx)
    assert only_refusal(result).reason == "dependency ineligible"


def test_a_qualified_observable_proxy_wins_over_an_undecidable_candidate(lab):
    from beliefs.assumptions import AssumptionInstance
    from beliefs.measurement import Aspect
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget
    from beliefs.restriction import TermRestriction
    from beliefs.target_comparison import synthesis

    source = Observable("testing/energy", lab.event.sort, Aspect("testing/energy-aspect", "EX:apparent"))
    target = replace(source, aspect=Aspect("testing/energy-aspect", "EX:intrinsic"))
    proc = lab.records.put(procedure(yields=(source, target)))
    left = lab.measured(
        role="parties", member=lab.event, kind="energy", unit="electronvolt", aspect=source.aspect, procedure_id=proc
    )
    right = replace(left, measure=replace(left.measure, observable=target))
    scope = {"testing/stage": ScopedRestriction("generic", TermRestriction("testing/stage", "EX:a"))}
    kwargs = {"claim": lab.event_claim, "form": "quantity", "functional": "temperature-level", "scope": scope}
    a, b = lab.target(response=left, **kwargs), lab.target(response=right, **kwargs)

    def bridge(validity, label):
        return ProxyModel(
            ProxySource(source, proc),
            ProxyTarget(target, None),
            validity,
            AssumptionInstance("testing/proxy-validity", {"record": label, "co_scope": "equal", "dimensions": ""}),
            None,
        )

    full = lab.records.put(bridge({}, "qualified"))
    # Choose a fixed fixture whose content id visits the undecidable candidate first.
    uncertain = lab.records.put(bridge({"testing/stage": TermRestriction("testing/stage", "EX:b")}, "uncertain"))
    assert uncertain < full
    result = synthesis(a, b, **lab.synthesis_ctx(lambda _a, _b: (uncertain, full)))
    assert result.kind == "permitted-under"


@pytest.mark.parametrize(
    "coverage,want",
    [("full", "permitted-under"), ("partial", "permitted-under"), ("disjoint", "refused"), ("unknown", "unknown")],
)
def test_synthesis_judges_the_consumed_crosswalks_actual_validity(lab, coverage, want):
    from beliefs.target_comparison import synthesis

    def interval(unit, lo, hi):
        return IntervalRestriction("testing/" + unit, F(lo), F(hi), True, False)

    validity = (
        {"testing/age": interval("calendar-month", 1, 2)}
        if coverage == "unknown"
        else {"testing/age": interval("hour", *{"full": (0, 5), "partial": (2, 4), "disjoint": (5, 6)}[coverage])}
    )
    left, right, ref = crosswalk_targets(lab, validity=validity)
    scope = {"testing/age": ScopedRestriction("generic", interval("hour", 1, 3))}
    a = lab.target(functional="probability-of-superiority", response=left, scope=scope)
    b = lab.target(functional="probability-of-superiority", response=right, scope=scope)
    result = synthesis(a, b, **lab.synthesis_ctx())
    assert result.kind == want
    if want == "permitted-under":
        assumption = next(v for v in with_assumptions(result).assumptions if v.particulars.get("record") == ref)
        assert assumption.particulars["co_scope"] == ("narrower" if coverage == "full" else "overlapping")
        assert assumption.particulars["error"] == "1.4"
    else:
        assert only_refusal(result).reason == "scope"


def test_age_threshold_against_universal_scope_and_calendar_unknown(lab):
    from beliefs.target_comparison import synthesis

    scope = {"testing/age": ScopedRestriction("generic", IntervalRestriction("testing/year", F(65), None, True, False))}
    result = synthesis(lab.target(scope=scope), lab.target(), **lab.synthesis_ctx())
    assert result.kind == "permitted-under"
    assumption = next(v for v in with_assumptions(result).assumptions if v.kind == "testing/transport-exchangeability")
    assert assumption.particulars["co_scope"] == "narrower"
    assert "65" in assumption.particulars["scopes"]

    def month(hi):
        return {
            "testing/age": ScopedRestriction(
                "generic", IntervalRestriction("testing/calendar-month", F(0), F(hi), True, False)
            )
        }

    result = synthesis(lab.target(scope=month(12)), lab.target(scope=month(24)), **lab.synthesis_ctx())
    assert result.kind == "unknown" and only_refusal(result).reason == "scope"


def test_authored_assumptions_are_unioned_and_interpretation_rules_still_must_match(lab):
    from beliefs.assumptions import AssumptionInstance
    from beliefs.target_comparison import synthesis

    alpha = AssumptionInstance("testing/transport-exchangeability", {"dimensions": "A", "co_scope": "narrower"})
    beta = AssumptionInstance("testing/transport-exchangeability", {"dimensions": "B", "co_scope": "overlapping"})
    a, b = lab.target(assumptions=(beta, alpha)), lab.target(assumptions=(beta,))
    result = synthesis(a, b, **lab.synthesis_ctx())
    assert with_assumptions(result).assumptions == (alpha, beta)
    result = synthesis(a, replace(b, interpretation_rule="another-rule"), **lab.synthesis_ctx())
    assert only_refusal(result).reason == "interpretation rule"


@pytest.mark.parametrize("reverse", [False, True])
def test_review_undefined_level_reversal_refuses(lab, reverse, monkeypatch):
    from beliefs.target_comparison import convertibility, synthesis

    a = lab.target(functional="undefined-level-reversal")
    grouping = a.target.estimand.bindings["grouping"]
    assert isinstance(grouping, RoleTermLevels)
    b = lab.target(
        functional="undefined-level-reversal",
        bindings={**a.target.estimand.bindings, "grouping": replace(grouping, levels=tuple(reversed(grouping.levels)))},
    )
    left, right = (b, a) if reverse else (a, b)
    import beliefs.target_comparison as comparison

    def numeric_conversion(*args, **kwargs):
        raise AssertionError("undefined level reversal reached numeric conversion")

    monkeypatch.setattr(comparison, "convert", numeric_conversion)
    assert convertibility(left, right, **lab.conversion_ctx()).kind == "not-convertible"
    assert synthesis(left, right, **lab.synthesis_ctx()).kind == "not-convertible"


@pytest.mark.parametrize("types", [("ratio", "level"), ("ratio", "difference"), ("level", "difference")])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("unit", ["tpm", "ktpm"])
def test_review_mixed_value_types_refuse(lab, types, reverse, unit):
    from beliefs.target_comparison import convertibility, synthesis

    response = lab.measured()
    a = lab.target(response=replace(response, measure=replace(response.measure, value_type=types[0])))
    b = lab.target(
        response=replace(response, measure=replace(response.measure, unit="testing/" + unit, value_type=types[1]))
    )
    left, right = (b, a) if reverse else (a, b)
    assert convertibility(left, right, **lab.conversion_ctx()).kind == "not-convertible"
    assert synthesis(left, right, **lab.synthesis_ctx()).kind == "not-convertible"
