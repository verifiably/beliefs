"""Synthetic records for Cases A, B and C of the post-infection comparison design."""

from collections.abc import Mapping

from beliefs.claim import Claim, Member, Qualifier, Referent, build_claim
from beliefs.classification_rule import ClassificationRule, rule_identity
from beliefs.procedure import External
from beliefs.profile import ProfileSpec

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
