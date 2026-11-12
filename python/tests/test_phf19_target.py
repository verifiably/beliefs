from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from fixtures_cut3 import FixtureRecords
from phf19_fixtures import FIXTURE, selected
from reproduction import type_target, vocabulary

from beliefs import stored
from beliefs.claim import Member, Referent, build_claim
from beliefs.classification_rule import rule_identity
from beliefs.errors import ScienceError
from beliefs.procedure import procedure_identity
from beliefs.projection import claim_identity
from beliefs.referent_mapping import mapping_identity
from beliefs.resolution import build_snapshot


def context():
    inputs = selected()
    profile = vocabulary.profile()
    parser = "sha256:" + sha256((Path(type_target.__file__).parent / "analysis/labels.py").read_bytes()).hexdigest()
    estimator = "sha256:" + sha256((Path(type_target.__file__).parent / "analysis/assoc.py").read_bytes()).hexdigest()
    assert hasattr(type_target, "procedures"), "PHF19 procedures are missing"
    assay, estimate, rule = type_target.procedures(inputs, parser_digest=parser, estimator_digest=estimator)
    records = FixtureRecords()
    for node in (
        stored.procedure_node(assay),
        stored.procedure_node(estimate),
        stored.classification_rule_node(rule),
        stored.referent_mapping_node(inputs.mapping),
    ):
        records.nodes[node.id] = node
    readable = {}
    for name, sort in vocabulary.HELD_SORTS.items():
        readable[vocabulary.binding_for(sort).binding] = (
            (Path(vocabulary.__file__).parent / "phf19-vocabulary" / f"{name}.txt").read_text().splitlines()
        )
    from reproduction.analysis_inputs import hgnc_members

    readable[profile.sorts["biology/gene"].binding] = (
        hgnc_members((FIXTURE / "hgnc.tsv").read_bytes()).decode().splitlines()
    )
    args = {
        "profile": profile,
        "claim": type_target.typed(inputs, profile),
        "records": records,
        "snapshot": build_snapshot(readable=readable),
        "assay_id": procedure_identity(assay),
        "grouping_rule_id": rule_identity(rule),
        "parser_digest": parser,
        "estimator_digest": estimator,
    }
    return inputs, args


def test_target_is_gene_rna_and_keeps_the_unknown_validity_assumption():
    inputs, args = context()
    estimand, app = type_target.estimand(inputs, **args)
    assert estimand.bindings["response"].member == Referent("biology/gene", "hgnc:24566")
    assert estimand.bindings["response"].mapping == mapping_identity(inputs.mapping)
    assert tuple(x.term for x in estimand.bindings["grouping"].classes) == ("level:ndmm", "level:pd")
    assert estimand.assumptions[0].particulars == {
        "record": args["assay_id"],
        "co_scope": "unknown",
        "dimensions": "mm30/cohort",
    }
    assert len(estimand.assumptions) == 1
    assert app.values["mm30/cohort"].restriction.term == "cohort:gse179929"


def test_party_order_is_canonical_and_selects_the_same_gene_response():
    inputs, args = context()
    original = args["claim"]
    args["claim"] = build_claim(
        args["profile"],
        operator=original.operator,
        roles={"parties": tuple(reversed(original.roles["parties"]))},
        qualifiers={},
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    assert claim_identity(args["claim"]) == claim_identity(original)
    assert type_target.estimand(inputs, **args)[0].bindings["response"].member.term == "hgnc:24566"


@pytest.mark.parametrize(
    "sort,terms",
    [("biology/gene", ("hgnc:24566", "hgnc:5")), ("mm30/clinical-factor", ("concept:disease-stage", "concept:other"))],
)
def test_kernel_admits_same_sort_pairs_but_driver_refuses(sort, terms):
    inputs, args = context()
    args["claim"] = build_claim(
        args["profile"],
        operator="general/covaries-with",
        roles={"parties": tuple(Member(Referent(sort, t)) for t in terms)},
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    with pytest.raises(ScienceError, match="selected"):
        type_target.estimand(inputs, **args)


def test_wrong_rule_of_right_class_sort_is_refused_by_driver():
    inputs, args = context()
    _, _, rule = type_target.procedures(
        inputs, parser_digest=args["parser_digest"], estimator_digest=args["estimator_digest"]
    )
    wrong = replace(rule, definition="A different classification with the same class sort")
    node = stored.classification_rule_node(wrong)
    args["records"].nodes[node.id] = node
    args["grouping_rule_id"] = node.id
    with pytest.raises(ScienceError, match="rule"):
        type_target.estimand(inputs, **args)


@pytest.mark.parametrize(
    "mutation",
    ["mapping-bytes", "mapping-sort", "missing-map", "missing-assay", "unknown-gene", "wrong-factor", "swapped-groups"],
)
def test_driver_refuses_broken_mapping_procedure_or_selected_question(mutation):
    inputs, args = context()
    if mutation == "mapping-bytes":
        inputs = replace(inputs, mapping_members=b"wrong\n")
    elif mutation == "mapping-sort":
        inputs = replace(inputs, mapping=replace(inputs.mapping, target_sort="biology/protein"))
    elif mutation == "missing-map":
        del args["records"].nodes[mapping_identity(inputs.mapping)]
    elif mutation == "missing-assay":
        del args["records"].nodes[args["assay_id"]]
    elif mutation == "unknown-gene":
        inputs = replace(inputs, gene="hgnc:5")
    elif mutation == "wrong-factor":
        inputs = replace(inputs, factor="concept:other")
    else:
        inputs = replace(inputs, baseline="level:pd", comparison="level:ndmm")
    with pytest.raises((ScienceError, KeyError)):
        type_target.estimand(inputs, **args)


def test_generic_builder_can_use_a_right_sort_wrong_rule_that_the_driver_refuses():
    from beliefs.estimand import RuleClassLevels, build_estimand

    inputs, args = context()
    original, app = type_target.estimand(inputs, **args)
    _, _, rule = type_target.procedures(
        inputs, parser_digest=args["parser_digest"], estimator_digest=args["estimator_digest"]
    )
    other = stored.classification_rule_node(replace(rule, definition="Another rule with identical class sort"))
    args["records"].nodes[other.id] = other
    changed = dict(original.bindings)
    changed["grouping"] = RuleClassLevels(other.id, original.bindings["grouping"].classes)
    rebuilt, _ = build_estimand(
        args["profile"],
        args["claim"],
        form=original.form,
        functional=original.functional,
        bindings=changed,
        outputs=original.outputs,
        reference=original.reference,
        control=original.control,
        uncertainty=original.uncertainty,
        assumptions=(),
        calibration=None,
        applicability=app,
        snapshot=args["snapshot"],
        records=args["records"],
    )
    assert rebuilt.bindings["grouping"].rule == other.id
    with pytest.raises(ScienceError, match="rule"):
        type_target.estimand(inputs, **{**args, "grouping_rule_id": other.id})


def test_wrong_class_sort_and_wrong_observable_refuse():
    inputs, args = context()
    from beliefs.procedure import procedure_from_stored

    assay = procedure_from_stored(args["records"].read(args["assay_id"]))
    wrong = stored.procedure_node(
        replace(assay, yields=(replace(type_target.OBSERVABLE, bearer_sort="biology/protein"),))
    )
    args["records"].nodes[wrong.id] = wrong
    with pytest.raises(ScienceError, match="assay"):
        type_target.estimand(inputs, **{**args, "assay_id": wrong.id})
    _, _, rule = type_target.procedures(
        inputs, parser_digest=args["parser_digest"], estimator_digest=args["estimator_digest"]
    )
    wrong_rule = stored.classification_rule_node(replace(rule, classes="mm30/clinical-factor"))
    args["records"].nodes[wrong_rule.id] = wrong_rule
    with pytest.raises(ScienceError, match="rule"):
        type_target.estimand(inputs, **{**args, "grouping_rule_id": wrong_rule.id})
