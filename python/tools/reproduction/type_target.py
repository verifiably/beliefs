"""The selected PHF19 gene RNA question, procedures and checked estimand authoring."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.applicability import ScopedRestriction, build_applicability
from beliefs.claim import Member, Referent, build_claim
from beliefs.classification_rule import ClassificationRule, rule_identity
from beliefs.dependencies import read_record
from beliefs.errors import EstimandError
from beliefs.estimand import Control, MeasuredBinding, OutputSpec, RuleClassLevels, ValueReference, build_estimand
from beliefs.measurement import Aspect, Measure, Observable
from beliefs.procedure import Implementation, Procedure, Scale, procedure_identity
from beliefs.projection import claim_identity, project_claim
from beliefs.referent_mapping import mapping_identity
from beliefs.resolution import TermOutcome
from beliefs.restriction import TermRestriction
from reproduction import state, vocabulary, world
from reproduction.analysis_inputs import PHF19Inputs

DISPLAY = "PHF19 gene-level RNA abundance is higher in PD than NDMM in this cohort comparison."
OBSERVABLE = Observable(
    "general/relative-abundance", "biology/gene", Aspect("biology/molecular-aspect", "biology-aspect:rna")
)


def implementation_digests(code: Path | None = None) -> tuple[str, str]:
    root = code if code is not None else Path(__file__).with_name("analysis")
    return tuple("sha256:" + sha256((root / name).read_bytes()).hexdigest() for name in ("labels.py", "assoc.py"))


def check_inputs(inputs: PHF19Inputs) -> None:
    if (
        inputs.source_proposition,
        inputs.source_dataset,
        inputs.feature,
        inputs.gene,
        inputs.factor,
        inputs.baseline,
        inputs.comparison,
        inputs.separator,
    ) != (
        "proposition:concept-disease-stage-affects-protein-phf19",
        "dataset:gse179929",
        "ENSG00000119403",
        "hgnc:24566",
        "concept:disease-stage",
        "level:ndmm",
        "level:pd",
        "_",
    ):
        raise EstimandError("inputs differ from the selected PHF19 question")
    mapping = inputs.mapping
    if (mapping.source_sort, mapping.target_sort, mapping.cardinality, mapping.aggregation) != (
        "biology/ensembl-gene",
        "biology/gene",
        "one-to-one",
        None,
    ):
        raise EstimandError("selected mapping sorts/cardinality/aggregation differ")
    if (
        inputs.mapping_members != b"ensembl:ENSG00000119403\thgnc:24566\n"
        or mapping.members != "sha256:" + sha256(inputs.mapping_members).hexdigest()
    ):
        raise EstimandError("selected mapping member bytes differ")
    for key, value in {
        "hgnc_release": "2025-09-05",
        "ensembl_release": "115",
        "assembly": "GRCh38.p14",
        "hgnc_sha256": inputs.digests["hgnc"],
        "ensembl_sha256": inputs.digests["ensembl"],
    }.items():
        if mapping.reference.get(key) != value:
            raise EstimandError("selected mapping reference release/digest differs")


def typed(inputs: PHF19Inputs, profile):
    check_inputs(inputs)
    return build_claim(
        profile,
        operator="general/covaries-with",
        roles={
            "parties": (
                Member(Referent("mm30/clinical-factor", inputs.factor)),
                Member(Referent("biology/gene", inputs.gene)),
            )
        },
        qualifiers={},
        form="polar",
        polarity="positive",
        layer="statistical",
    )


def procedures(
    inputs: PHF19Inputs, *, parser_digest: str, estimator_digest: str
) -> tuple[Procedure, Procedure, ClassificationRule]:
    check_inputs(inputs)
    provenance = {
        **dict(inputs.digests),
        "source_proposition": inputs.source_proposition,
        "source_dataset": inputs.source_dataset,
        "source_feature": inputs.feature,
        "mapping": mapping_identity(inputs.mapping),
        "hgnc_release": "2025-09-05",
        "ensembl_release": "115",
        "assembly": "GRCh38.p14",
        "historical_quantifier": "unknown",
        "historical_annotation_release": "unknown",
        "historical_aggregation": "unknown",
        "evidence": inputs.mapping.reference["evidence"],
    }
    for key, digest in inputs.digests.items():
        provenance[key + "_dataset"] = stored.dataset_node(
            title=key, resources=[{"name": key, "digest": "sha256:" + digest}]
        ).id
    provenance.update(
        {k: v for k, v in inputs.mapping.reference.items() if k.startswith(("hgnc_members_", "hgnc_derivation_"))}
    )
    assay = Procedure(
        kind="general/assay",
        name="PHF19 matrix gene RNA interpretation",
        definition="Gene-level RNA as represented by the held matrix, using an explicitly later identifier correspondence; upstream quantifier, annotation and aggregation are unknown.",
        yields=(OBSERVABLE,),
        scale=Scale(Fraction(0), Fraction(1000000), "higher-is-more"),
        validated_in="unknown",
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters=provenance,
        external=None,
    )
    estimator = Procedure(
        kind="general/estimator",
        name="PHF19 unpaired midrank estimator",
        definition="Engineering demonstration: independent-groups Mann-Whitney U, half-tie probability of superiority, untie-corrected normal diagnostics; no computed interval or certified independence.",
        yields=(),
        scale=None,
        validated_in="unknown",
        compatible_with=(),
        evidence=(),
        implementation=Implementation("analysis/assoc.py", estimator_digest),
        inputs=None,
        parameters={"label_parser": parser_digest, "comparison": "PD", "baseline": "NDMM", "alpha": "0.05"},
        external=None,
    )
    rule = ClassificationRule(
        classes="mm30/stage-level",
        reads=(),
        definition="For concept:disease-stage only: classify the final suffix after _ as NDMM -> level:ndmm or PD -> level:pd; refuse missing, empty or other tokens. This classifies supplied labels, not clinical diagnoses.",
        external=None,
        implementation=Implementation("analysis/labels.py", parser_digest),
        annotator=None,
    )
    return assay, estimator, rule


def estimand(
    inputs,
    *,
    profile,
    claim,
    records,
    snapshot,
    assay_id: str,
    grouping_rule_id: str,
    parser_digest: str,
    estimator_digest: str,
):
    expected_claim = typed(inputs, profile)
    if claim_identity(claim) != claim_identity(expected_claim):
        raise EstimandError("claim is not the selected gene/factor PHF19 shape")
    assay, _estimator, rule = procedures(inputs, parser_digest=parser_digest, estimator_digest=estimator_digest)
    if assay_id != procedure_identity(assay) or read_record(records, assay_id) != assay:
        raise EstimandError("held assay differs from the selected observable/provenance")
    if grouping_rule_id != rule_identity(rule) or read_record(records, grouping_rule_id) != rule:
        raise EstimandError("grouping rule differs from the selected factor/parser association")
    map_id = mapping_identity(inputs.mapping)
    if read_record(records, map_id) != inputs.mapping:
        raise EstimandError("held map differs from the checked PHF19 correspondence")
    if snapshot.resolve(profile.sorts["biology/gene"], inputs.gene) != TermOutcome.MEMBER:
        raise EstimandError("selected HGNC membership has not been established")
    app, _ = build_applicability(
        profile,
        claim,
        {"mm30/cohort": ScopedRestriction("generic", TermRestriction("mm30/cohort", "cohort:gse179929"))},
        snapshot=snapshot,
    )
    measure = Measure(OBSERVABLE, None, assay_id, "ratio", "level", "general/identity", assay_id)
    value, _ = build_estimand(
        profile,
        claim,
        form="contrast",
        functional="general/probability-of-superiority",
        bindings={
            "response": MeasuredBinding("parties", Referent("biology/gene", inputs.gene), measure, map_id, None),
            "grouping": RuleClassLevels(
                grouping_rule_id,
                (Referent("mm30/stage-level", inputs.baseline), Referent("mm30/stage-level", inputs.comparison)),
            ),
        },
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(Decimal("0.5")),
        control=Control("general/observational", (), "general/independent-groups", "general/cohort-enrolment"),
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=app,
        snapshot=snapshot,
        records=records,
    )
    return value, app


def main() -> int:
    from reproduction import hold

    inputs = hold.recover_inputs()
    claim = typed(inputs, vocabulary.profile())
    node = world.open_writer().add(
        stored.proposition_node(
            "phf19-rna-pd-vs-ndmm", title=DISPLAY, claim=project_claim(claim), display_statement=DISPLAY
        )
    )
    state.save(proposition_ref=node.id, claim_identity=claim_identity(claim))
    return 0
