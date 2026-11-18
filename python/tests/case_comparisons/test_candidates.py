"""Candidate genesis, activation, bearer and scope verification (V1–V3, V6)."""

import re
from fractions import Fraction

import pytest
from candidate_contracts import (
    CASE_CANDIDATES,
    STATIC,
    candidate_document,
    candidate_history,
    case_profile,
    oracle,
    with_rows,
)

from beliefs import errors
from beliefs.claim import Qualifier, Referent
from beliefs.contract.domain import parse_domain_contract
from beliefs.projection import claim_identity
from beliefs.register import register_entry_keys
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.restriction import IntervalRestriction, RuleRestriction, TermRestriction, compare_scopes

from .cases import (
    CLASS,
    COMPARATOR,
    CONDITION,
    GENE,
    MECFS,
    MONDO_TERMS,
    ORIGINS,
    OTHER_GENE,
    OUTCOME,
    PTLDS,
    RULE_SCOPE,
    RULE_SORT,
    RULES,
    concept_claim,
    label,
    pair_claim,
    rule_claim,
    rule_id,
)

SOURCES = {
    "mondo": "urn:beliefs:source:mondo-disease-ontology",
    "case-comparisons": "urn:beliefs:definitions:case-outcome-comparison-admissions",
}
KEYS = {
    "mondo": {"sort:mondo/disease"},
    "case-comparisons": {
        "sort:case-comparisons/outcome-class",
        "sort:case-comparisons/case-definition",
        "dimension:case-comparisons/outcome",
        "dimension:case-comparisons/comparator",
        "dimension:case-comparisons/condition",
        "dimension:case-comparisons/case-definition-scope",
        "dimension:case-comparisons/since-infection-onset",
        "dimension:case-comparisons/since-symptom-onset",
        "dimension:case-comparisons/since-treatment-completion",
        "instantiation:case-comparisons/concept-covaries-with-gene",
        "instantiation:case-comparisons/rule-outcome-covaries-with-gene",
        "estimand:instantiation:case-comparisons/concept-covaries-with-gene",
        "estimand:instantiation:case-comparisons/rule-outcome-covaries-with-gene",
    },
}
SORT_MISSING = "roles.parties names sort {sort!r}, but no compiled contract declares sort {sort!r}"
OMISSIONS = [
    (
        "mondo",
        errors.MalformedContract,
        "case-comparisons: dimensions.condition: restriction_sort names sort 'mondo/disease', but no compiled contract declares sort 'mondo/disease'",
    ),
    (
        "biology",
        errors.MalformedContract,
        "case-comparisons: instantiations.concept-covaries-with-gene: " + SORT_MISSING.format(sort="biology/gene"),
    ),
    (
        "si-brochure",
        errors.ProfileError,
        "case-comparisons: restriction names 'si-brochure/duration', which no activated contract declares",
    ),
    (
        "general",
        errors.ProfileError,
        "biology: measurements quantity kind names 'general/relative-abundance', which no activated contract declares",
    ),
]


@pytest.mark.parametrize("namespace", CASE_CANDIDATES)
def test_genesis_matches_its_register_and_oracle(base_contract, namespace):
    revision = candidate_history(namespace, base_contract)
    pins = oracle()
    assert pins["status"].startswith("unshipped candidates")
    (row,) = [row for row in pins["static"] if row["contract_path"].endswith(f"/{namespace}/DOMAIN.yaml")]
    assert revision.contract.content_identity == row["contract_identity"]
    assert revision.contract.defining_source is not None
    assert revision.contract.defining_source.id == SOURCES[namespace]
    assert set(revision.register.entries) == register_entry_keys(revision.contract) == KEYS[namespace]
    assert revision.register.previous is None
    assert {entry.status for entry in revision.register.entries.values()} == {"provisional"}


def test_new_candidates_stay_out_of_the_shared_static_list():
    assert set(CASE_CANDIDATES).isdisjoint(STATIC)


@pytest.mark.parametrize(
    "namespace,table,name,change,message",
    [
        ("case-comparisons", "dimensions", "outcome", None, "drops claim-vocabulary declaration"),
        (
            "case-comparisons",
            "estimands",
            "instantiation:concept-covaries-with-gene",
            None,
            "drops claim-vocabulary declaration",
        ),
        (
            "case-comparisons",
            "sorts",
            "outcome-class",
            {"identifier_class": {"prefix": "outcome-class", "pattern": "outcome-class:[a-z]+"}},
            "different canonical schema projection",
        ),
        (
            "mondo",
            "sorts",
            "disease",
            {"binding": {"kind": "release", "namespace": "mondo", "release": "2026-06-01"}},
            "different canonical schema projection",
        ),
        ("mondo", "sorts", "disease", None, "drops claim-vocabulary declaration"),
    ],
)
def test_a_changed_or_dropped_row_refuses_succession(base_contract, namespace, table, name, change, message):
    genesis = candidate_history(namespace, base_contract).contract
    successor = with_rows(candidate_document(namespace), genesis, {})
    if change is None:
        del successor[table][name]
    else:
        successor[table][name].update(change)
    with pytest.raises(errors.SuccessionViolation, match=message):
        parse_domain_contract(successor, source="<mutated successor>", base=base_contract, predecessor=genesis)


def test_an_unchanged_or_additive_successor_is_accepted(base_contract):
    genesis = candidate_history("mondo", base_contract).contract
    document = candidate_document("mondo")
    unchanged = with_rows(document, genesis, {})
    additive = with_rows(
        document,
        genesis,
        {
            "sorts": {
                "extra": {
                    "binding": {
                        "kind": "scheme",
                        "scheme": "extra",
                        "version": "1",
                    },
                    "identifier_class": {"prefix": "extra", "pattern": "extra:[a-z]+"},
                }
            }
        },
    )
    for successor in (unchanged, additive):
        parse_domain_contract(successor, source="<candidate successor>", base=base_contract, predecessor=genesis)


def test_profile_compiles_with_five_explicit_lineages(base_contract):
    profile = case_profile(base_contract)
    assert set(profile.activated_contracts) == {"general", "biology", "si-brochure", "mondo", "case-comparisons"}
    assert dict(profile.defining_sources) == {"si-brochure": "urn:beliefs:source:bipm-si-brochure", **SOURCES}
    assert profile.claim_dimensions("general/covaries-with") == (
        "case-comparisons/comparator",
        "case-comparisons/outcome",
    )


@pytest.mark.parametrize("omitted,error,message", OMISSIONS)
def test_each_omission_refuses_at_the_first_unresolved_reference(base_contract, omitted, error, message):
    with pytest.raises(error, match=re.escape(message)):
        case_profile(base_contract, omit=(omitted,))


@pytest.mark.parametrize(
    "omitted,instantiation,sort",
    [
        ("mondo", "concept-covaries-with-gene", "mondo/disease"),
        ("biology", "rule-outcome-covaries-with-gene", "biology/gene"),
    ],
)
def test_the_second_reference_refuses_once_the_first_is_removed(base_contract, omitted, instantiation, sort):
    document = candidate_document("case-comparisons")
    if omitted == "mondo":
        del document["dimensions"]["condition"]
    else:
        del document["instantiations"]["concept-covaries-with-gene"]
        del document["estimands"]["instantiation:concept-covaries-with-gene"]
    variant = parse_domain_contract(document, source="<omission variant>", base=base_contract, predecessor=None)
    message = f"instantiations.{instantiation}: " + SORT_MISSING.format(sort=sort)
    with pytest.raises(errors.MalformedContract, match=re.escape(message)):
        case_profile(base_contract, omit=(omitted,), replace={"case-comparisons": variant})


def test_mondo_compiles_without_the_comparison_candidate(base_contract):
    profile = case_profile(base_contract, omit=("case-comparisons",))
    assert "mondo" in profile.activated_contracts
    assert "case-comparisons" not in profile.activated_contracts


@pytest.fixture
def profile(base_contract):
    return case_profile(base_contract)


def test_mondo_terms_resolve_only_against_a_supplied_list(profile):
    disease = profile.sorts["mondo/disease"]
    empty = build_snapshot()
    # This list is synthetic and partial by construction.
    supplied = build_snapshot(readable={disease.binding: MONDO_TERMS})
    absent = "mondo:9999999"
    assert all(empty.resolve(disease, term) is TermOutcome.NOT_CONSULTED for term in (*MONDO_TERMS, absent))
    assert all(supplied.resolve(disease, term) is TermOutcome.MEMBER for term in MONDO_TERMS)
    assert supplied.resolve(disease, absent) is TermOutcome.NOT_MEMBER


def test_an_upstream_spelled_member_list_silently_excludes_the_canonical_term(profile):
    disease = profile.sorts["mondo/disease"]
    supplied = build_snapshot(readable={disease.binding: ["MONDO:0005404"]})
    assert supplied.resolve(disease, "mondo:0005404") is TermOutcome.NOT_MEMBER


def test_the_upstream_spelling_is_refused_where_a_claim_is_built(profile):
    term = "MONDO:0005404"
    disease = profile.sorts["mondo/disease"]
    supplied = build_snapshot(readable={disease.binding: MONDO_TERMS})
    assert supplied.resolve(disease, term) is TermOutcome.NOT_MEMBER
    assert build_snapshot().resolve(disease, term) is TermOutcome.NOT_CONSULTED
    with pytest.raises(errors.IdentifierClassMismatch, match="outside the identifier class of 'mondo/disease'"):
        pair_claim(profile, Referent("mondo/disease", term), GENE)


def test_a_class_label_is_a_member_beside_any_rule(profile):
    sort = profile.sorts[CLASS]
    snapshot = build_snapshot()
    for name in ("outcome-class:ptlds", "outcome-class:never-defined-anywhere"):
        assert snapshot.resolve(sort, name) is TermOutcome.MEMBER
    for name in ("outcome-class:PTLDS", "ptlds"):
        assert snapshot.resolve(sort, name) is TermOutcome.NOT_MEMBER


def test_a_case_definition_resolves_against_a_kinds_inventory(profile):
    sort = profile.sorts[RULE_SORT]
    rule = rule_id("case-a-study")
    assert build_snapshot().resolve(sort, rule) is TermOutcome.NOT_CONSULTED
    assert build_snapshot(kinds={"classification-rule": [rule]}).resolve(sort, rule) is TermOutcome.MEMBER
    other = build_snapshot(kinds={"classification-rule": [rule_id("case-b-fukuda")]})
    assert other.resolve(sort, rule) is TermOutcome.NOT_MEMBER
    with pytest.raises(
        errors.IdentifierClassMismatch, match="outside the identifier class of 'case-comparisons/case-definition'"
    ):
        pair_claim(profile, Referent(RULE_SORT, "source:" + "a" * 64), GENE)


def test_the_claims_of_case_a_type_with_distinct_identities(profile):
    claims = [
        concept_claim(profile),
        rule_claim(profile, "case-a-study", outcome="ptlds", comparator="return-to-health"),
        rule_claim(profile, "case-a-study", outcome="symptoms-only", comparator="return-to-health"),
        rule_claim(profile, "case-a-study", outcome="ptlds", comparator="symptoms-only"),
        rule_claim(profile, "case-c-recovered", outcome="ptlds", comparator="return-to-health"),
    ]
    assert len({claim_identity(claim) for claim in claims}) == len(claims)
    assert claim_identity(pair_claim(profile, GENE, PTLDS)) == claim_identity(claims[0])


def test_same_sort_pairs_type_and_a_cross_pair_does_not(profile):
    first = Referent(RULE_SORT, rule_id("case-a-study"))
    second = Referent(RULE_SORT, rule_id("case-b-fukuda"))
    for left, right in ((GENE, OTHER_GENE), (PTLDS, MECFS), (first, second)):
        assert pair_claim(profile, left, right).operator == "general/covaries-with"
    with pytest.raises(errors.UninstantiatedTemplate):
        pair_claim(profile, first, PTLDS)
    with pytest.raises(errors.DuplicateMember):
        pair_claim(profile, GENE, GENE)


def test_the_sign_convention_rests_on_the_author(profile):
    # The kernel permits missing qualifiers, an unanchored label, and a label absent from the rule.
    unqualified = rule_claim(profile, "case-a-study", outcome=None, comparator=None)
    assert not unqualified.qualifiers
    unanchored = Qualifier("generic", label("return-to-health"))
    assert concept_claim(profile, qualifiers={COMPARATOR: unanchored}).qualifiers[COMPARATOR] == unanchored
    unknown = rule_claim(profile, "case-a-study", outcome="never-defined-anywhere", comparator="ptlds")
    assert unknown.qualifiers[OUTCOME] == Qualifier("generic", label("never-defined-anywhere"))


def test_fixture_rules_are_synthetic_and_distinct():
    assert len({rule_id(name) for name in RULES}) == len(RULES) == 5
    for rule in RULES.values():
        assert rule.definition.startswith("SYNTHETIC summary.")
        assert rule.external is not None
        assert rule.external.mapping == "contextual"


def _rule_scope(rule: str, *labels: str) -> RuleRestriction:
    return RuleRestriction(rule_id(rule), tuple(sorted(label(name).term for name in labels)))


def _hours(low: int, high: int) -> IntervalRestriction:
    # These invented hours exercise interval arithmetic.
    return IntervalRestriction("si-brochure/hour", Fraction(low), Fraction(high), True, False)


def test_rule_scopes_compare_by_rule_and_inclusion(profile):
    fukuda = {RULE_SCOPE: _rule_scope("case-b-fukuda", "cfs")}
    ccc = {RULE_SCOPE: _rule_scope("case-b-ccc", "mecfs")}
    pooled = {RULE_SCOPE: _rule_scope("case-b-fukuda", "cfs", "icf")}
    other_class = {RULE_SCOPE: _rule_scope("case-b-fukuda", "icf")}
    assert compare_scopes(fukuda, ccc, profile).verdict == "unknown"
    assert compare_scopes(fukuda, pooled, profile).verdict == "narrower"
    assert compare_scopes(fukuda, fukuda, profile).verdict == "equal"
    assert compare_scopes(fukuda, other_class, profile).verdict == "unknown"


def test_interval_scopes_compare_by_span_and_origin(profile):
    infection = ORIGINS["infection"]
    a = {infection: _hours(0, 720)}
    assert compare_scopes(a, a, profile).verdict == "equal"
    assert compare_scopes({infection: _hours(0, 48)}, {infection: _hours(24, 720)}, profile).verdict == "overlapping"
    assert compare_scopes(a, {ORIGINS["symptom"]: _hours(0, 720)}, profile).verdict == "overlapping"
    assert compare_scopes({}, {}, profile).verdict == "equal"
    lyme = {CONDITION: TermRestriction(PTLDS.sort, PTLDS.term)}
    fatigue = {CONDITION: TermRestriction(MECFS.sort, MECFS.term)}
    assert compare_scopes(lyme, fatigue, profile).verdict == "unknown"
    assert compare_scopes(lyme, lyme, profile).verdict == "equal"


_RELATION = "ccc-mecfs-within-fukuda-cfs"


def _scope_successor(base_contract, **change):
    namespace = "case-comparisons"
    genesis = candidate_history(namespace, base_contract).contract
    # This invented declaration exercises the mechanism. It makes no claim about the definitions.
    relation = {
        "dimension": "case-definition-scope",
        "relation": "narrower",
        "left": {"rule": rule_id("case-b-ccc"), "classes": ["outcome-class:mecfs"]},
        "right": {"rule": rule_id("case-b-fukuda"), "classes": ["outcome-class:cfs"]},
        **change,
    }
    document = with_rows(candidate_document(namespace), genesis, {"scope_relations": {_RELATION: relation}})
    return parse_domain_contract(document, source="<scope successor>", base=base_contract, predecessor=genesis)


def test_a_declared_narrower_relation_changes_the_verdict(base_contract, profile):
    ccc = {RULE_SCOPE: _rule_scope("case-b-ccc", "mecfs")}
    fukuda = {RULE_SCOPE: _rule_scope("case-b-fukuda", "cfs")}
    before = compare_scopes(ccc, fukuda, profile)
    assert (before.verdict, before.relations) == ("unknown", ())
    successor = case_profile(base_contract, replace={"case-comparisons": _scope_successor(base_contract)})
    after = compare_scopes(ccc, fukuda, successor)
    assert (after.verdict, after.relations) == ("narrower", (f"case-comparisons/{_RELATION}",))


@pytest.mark.parametrize("relation", ["disjoint", "excludes"])
def test_relations_the_grammar_cannot_state_are_refused(base_contract, relation):
    message = "is not one of the base contract's scope relations ['equal', 'narrower']"
    with pytest.raises(errors.MalformedContract, match=re.escape(message)):
        _scope_successor(base_contract, relation=relation)


def test_mixed_scope_endpoints_are_refused(base_contract):
    with pytest.raises(errors.MalformedContract, match="both endpoints have one form, term or rule"):
        _scope_successor(base_contract, left={"sort": MECFS.sort, "term": MECFS.term})


def test_a_class_set_cannot_be_a_scope_endpoint(base_contract):
    message = "a rule scope endpoint names exactly one class; a class set is not a declared endpoint"
    with pytest.raises(errors.MalformedContract, match=re.escape(message)):
        _scope_successor(
            base_contract,
            right={"rule": rule_id("case-b-fukuda"), "classes": ["outcome-class:cfs", "outcome-class:icf"]},
        )
