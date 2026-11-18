"""Synthetic records for Cases A, B and C of the post-infection comparison design."""

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

from authority import ACTOR, FULL
from nodes.core.node import Node
from profiles import pins_for
from test_corpus_write import OperationRecorder
from test_stored import DefaultExecutor

from beliefs import stored
from beliefs.claim import Claim, Member, Qualifier, Referent, build_claim
from beliefs.classification_rule import ClassificationRule, rule_identity
from beliefs.corpus import CorpusWriter
from beliefs.procedure import External
from beliefs.profile import ProfileSpec
from beliefs.projection import project_claim
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span

CLASS = "case-comparisons/outcome-class"
RULE_SORT = "case-comparisons/case-definition"
OUTCOME = "case-comparisons/outcome"
COMPARATOR = "case-comparisons/comparator"
CONDITION = "case-comparisons/condition"
RULE_SCOPE = "case-comparisons/case-definition-scope"
ORIGINS = {
    "infection": "case-comparisons/since-infection-onset",
    "symptom": "case-comparisons/since-symptom-onset",
    "treatment": "case-comparisons/since-treatment-completion",
}

# Synthetic gene terms. Membership is not consulted.
GENE = Referent("biology/gene", "hgnc:99999901")
OTHER_GENE = Referent("biology/gene", "hgnc:99999902")
LONG_COVID = Referent("mondo/disease", "mondo:0100233")
MECFS = Referent("mondo/disease", "mondo:0005404")
PTLDS = Referent("mondo/disease", "mondo:0700280")
MONDO_TERMS = (LONG_COVID.term, MECFS.term, PTLDS.term)

RULES = {
    "case-a-study": ClassificationRule(
        CLASS,
        (),
        "SYNTHETIC summary. A study rule sorts treated participants into three classes: syndrome with functional "
        "impact (ptlds), symptoms only (symptoms-only), and neither (return-to-health).",
        External("https://doi.org/10.5555/pais-case-a-rule", "contextual"),
        None,
        None,
    ),
    "case-b-fukuda": ClassificationRule(
        CLASS,
        (),
        "SYNTHETIC summary. A research case definition places a participant in chronic fatigue syndrome (cfs) or in "
        "idiopathic chronic fatigue (icf).",
        External("Fukuda 1994 chronic fatigue syndrome research case definition; named, not reproduced", "contextual"),
        None,
        None,
    ),
    "case-b-ccc": ClassificationRule(
        CLASS,
        (),
        "SYNTHETIC summary. A clinical case definition designates a participant as a case (mecfs).",
        External("Canadian Consensus Criteria 2003 for ME/CFS; named, not reproduced", "contextual"),
        None,
        None,
    ),
    "case-c-threshold": ClassificationRule(
        CLASS,
        (),
        "SYNTHETIC summary. A study rule places participants at or above a symptom index threshold in long-covid "
        "and those below it in comparison-group; this comparison group is below a threshold and is not symptom- "
        "free.",
        External("https://doi.org/10.5555/pais-case-c-threshold-rule", "contextual"),
        None,
        None,
    ),
    "case-c-recovered": ClassificationRule(
        CLASS,
        (),
        "SYNTHETIC summary. A study rule places participants with the syndrome in long-covid and those who "
        "recovered without ever developing it in comparison-group; this comparison group has no history of the "
        "syndrome.",
        External("https://doi.org/10.5555/pais-case-c-recovered-rule", "contextual"),
        None,
        None,
    ),
}


def rule_id(name: str) -> str:
    return rule_identity(RULES[name])


def label(name: str) -> Referent:
    return Referent(CLASS, f"outcome-class:{name}")


def concept_claim(
    profile: ProfileSpec,
    disease: Referent = PTLDS,
    gene: Referent = GENE,
    *,
    qualifiers: Mapping[str, Qualifier] | None = None,
) -> Claim:
    return _association(profile, disease, gene, {} if qualifiers is None else qualifiers)


def rule_claim(
    profile: ProfileSpec, rule: str, *, outcome: str | None, comparator: str | None, gene: Referent = GENE
) -> Claim:
    qualifiers = {
        dimension: Qualifier("generic", label(name))
        for dimension, name in ((OUTCOME, outcome), (COMPARATOR, comparator))
        if name is not None
    }
    return _association(profile, Referent(RULE_SORT, rule_id(rule)), gene, qualifiers)


def pair_claim(profile: ProfileSpec, a: Referent, b: Referent) -> Claim:
    return _association(profile, a, b, {})


def _association(profile: ProfileSpec, a: Referent, b: Referent, qualifiers: Mapping[str, Qualifier]) -> Claim:
    return build_claim(
        profile,
        operator="general/covaries-with",
        roles={"parties": (Member(a), Member(b))},
        layer="statistical",
        form="polar",
        polarity="positive",
        qualifiers=qualifiers,
    )


VISITS = (
    "SYNTHETIC: at the second visit after treatment the analyte was higher "
    "in the syndrome class than in the return-to-health class.",
    "SYNTHETIC: at the fourth visit after treatment the analyte was higher "
    "in the syndrome class than in the return-to-health class.",
)


def source(n: int) -> Node:
    return stored.source_node(
        title=f"SYNTHETIC report {n} (invented)", identifiers={"doi": f"10.5555/pais-synthetic-{n:04d}"}
    )


def passages(n: int) -> tuple[str, ...]:
    if n == 1:
        return VISITS
    return (
        f"SYNTHETIC: report {n} states that the analyte was higher in the syndrome class than in the comparison class.",
    )


def report_text(n: int) -> bytes:
    return "\n".join((f"SYNTHETIC report {n} (invented). Results.", *passages(n))).encode("utf-8")


def locator(n: int, index: int) -> str:
    return f"SYNTHETIC report {n}, results, passage {index + 1}"


def representation(n: int) -> Representation:
    return Representation(sha256(report_text(n)).hexdigest(), "text/plain", "full")


def proposition(slug: str, claim: Claim) -> Node:
    return stored.proposition_node(slug, title=f"SYNTHETIC {slug}", claim=project_claim(claim))


def assertion(
    source: Node,
    proposition: Node,
    *,
    n: int,
    index: int = 0,
    sign: str = "asserts",
    extent: str = "full",
    quote: str | None = None,
) -> SourceAssertion:
    report = representation(n)
    if extent != report.extent:
        report = Representation(report.sha256, report.media_type, extent)
    return SourceAssertion(
        source.id,
        Reading(report, Span(passages(n)[index] if quote is None else quote, locator(n, index)), ACTOR),
        Bearing(sign, proposition.id),
        ACTOR,
    )


def portable_writer(path: Path, profile: ProfileSpec) -> CorpusWriter:
    port = OperationRecorder(path, authority=FULL, profile=profile)
    writer = CorpusWriter(path, DefaultExecutor, authority=FULL, profile=profile, operation_port=port)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer
