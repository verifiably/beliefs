"""V2 estimand authoring, frozen records and refusals on the certified volume.

The final case retains the historical mm30 report as transition evidence;
it does not claim a base-v2 recreation before the biology genesis exists.
"""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
import yaml
from authority import FULL
from fixtures_cut3 import (
    MEASUREMENT_RECORDS,
    TESTING_CLAIM,
    TESTING_PROFILE,
    freeze_context,
    spec_draft,
    spec_rules,
    typed_applicability,
    typed_estimand,
    typed_target,
)
from fixtures_cut4 import raw_write, reopen
from profiles import pins_for
from test_audit import assessment_closure
from test_belief import scenario
from verification_fixtures import publish_corpus

from beliefs import stored
from beliefs.applicability import ScopedRestriction, applicability_from_stored, applicability_projection
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.belief import Belief, evaluate
from beliefs.claim import Referent, build_claim
from beliefs.contract import domain, parse_base_contract
from beliefs.errors import (
    DimensionNotApplicabilitySide,
    EstimandError,
    MalformedContract,
    PreGrammarAssessment,
    PreGrammarSpec,
    SuccessionViolation,
    ValidationRefused,
)
from beliefs.estimand import Estimand, ValueReference, estimand_from_stored, estimand_projection
from beliefs.identity import v1
from beliefs.profile import shipped_base_contract
from beliefs.projection import project_claim
from beliefs.record import AssessmentValue
from beliefs.restriction import IntervalRestriction
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.spec import SPEC_DOMAIN, RuleImplementation, freeze, frozen_projection, restore

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def corpora(work_directory):
    """A registered corpus root on the certified volume, under the profile that
    declares the operator every typed estimand here is built against."""
    roots: list[Path] = []

    def make(*, authority=FULL, profile=TESTING_PROFILE):
        root = Path(tempfile.mkdtemp(prefix="estimand-", dir=work_directory))
        roots.append(root)
        init_corpus_root(root, authority=authority)
        writer = open_corpus(root, authority=authority, profile=profile)
        writer.adopt_manifest(profile=pins_for(profile))
        return writer

    yield make
    for root in roots:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _base_document():
    return yaml.safe_load((REPO_ROOT / "contracts/science/CONTRACT.yaml").read_text())


def _testing_document():
    return yaml.safe_load((REPO_ROOT / "fixtures/contracts/testing.yaml").read_text())


def test_the_estimands_structure_is_kernel_owned_and_closed(corpora):
    writer = corpora()
    grammar = writer.profile.estimand_grammar
    assert grammar.version == 2 and len(grammar.forms) == 6
    assert grammar.uncertainty_kinds == ("interval", "standard-error", "covariance")
    for change in ["missing", "v1", "extra"]:
        document = _base_document()
        if change == "missing":
            del document["estimand_grammar"]
        elif change == "extra":
            document["estimand_grammar"]["forms"].append("rank-contrast")
        else:
            document["estimand_grammar"] = {
                "version": 1,
                "tag_encoding": "science.identity.v1",
                "contrast_kinds": ["levels", "continuous"],
                "scales": ["additive", "multiplicative"],
                "uncertainty_kinds": ["interval", "standard-error"],
            }
        with pytest.raises(MalformedContract):
            parse_base_contract(document, source="<refused>")


def test_estimands_is_domain_issued_operator_bound_and_succession_governed(corpora):
    writer = corpora()
    doc = _testing_document()
    prior = domain.parse_domain_contract(doc, source="<prior>", base=shipped_base_contract(), predecessor=None)
    next_doc = copy.deepcopy(doc)
    next_doc["version"] += 1
    next_doc["lineage"] = {"successor": prior.content_identity}
    next_doc["estimands"]["instantiation:affects-entity-outcome"]["forms"] = ["quantity"]
    with pytest.raises(SuccessionViolation):
        domain.parse_domain_contract(next_doc, source="<successor>", base=shipped_base_contract(), predecessor=prior)
    assert writer.profile.estimands["bridge:testing/promotes"].kind == "bridge"


def test_an_estimand_is_unconstructible_outside_its_claims_operator_declaration(corpora):
    writer = corpora()
    with pytest.raises(EstimandError):
        Estimand()
    with pytest.raises(EstimandError):
        typed_estimand(bindings={})
    with pytest.raises(EstimandError):
        typed_estimand(form="quantity")
    e = typed_estimand()
    assert estimand_from_stored(estimand_projection(e), profile=writer.profile) == e
    p = writer.add(stored.proposition_node("p", title="Claim", claim=project_claim(TESTING_CLAIM)))
    spec = freeze(spec_draft(target=p.id), held_rules=spec_rules(), **freeze_context())
    for entry in spec.assessed_target.dependencies:
        writer.add(MEASUREMENT_RECORDS.read(entry.id))
    node = writer.add(stored.analysis_spec_node(spec))
    assert stored.analysis_spec_value(reopen(writer.root).get(node.id), profile=writer.profile) == spec


def test_applicability_is_quantified_and_operator_scoped(corpora):
    writer = corpora()
    app = typed_applicability(
        {
            "testing/follow-up": ScopedRestriction(
                "universal",
                IntervalRestriction("testing/calendar-month", Fraction(6), None, True, False, "testing/mean-month"),
            )
        }
    )
    assert (
        applicability_from_stored(
            applicability_projection(app), profile=writer.profile, operator=TESTING_CLAIM.operator
        )
        == app
    )
    with pytest.raises(DimensionNotApplicabilitySide):
        typed_applicability(
            {
                "testing/population": ScopedRestriction(
                    "generic", IntervalRestriction("testing/hour", Fraction(1), None, True, False)
                )
            }
        )
    a = freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())
    b = freeze(spec_draft(applicability=app), held_rules=spec_rules(), **freeze_context())
    assert a.identity != b.identity


def test_estimates_and_uncertainty_are_named_and_domain_checked(corpora):
    writer = corpora()
    spec = freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())

    def derive(output):
        rule = RuleImplementation("impl-interp-1", lambda manifest: output, ())
        return build_assessment(
            assessment_closure(spec), specs={spec.identity: spec}, implementations={rule.identity: rule}
        )

    good = derive(
        {
            "outcome": "supported",
            "estimates": {"estimate": Decimal(".4")},
            "uncertainty": {
                "estimate": {"kind": "interval", "low": Decimal(".1"), "high": Decimal(".7"), "level": Decimal(".95")}
            },
        }
    )
    assert isinstance(good, AssessmentValue)
    assert good.target == spec.assessed_target and good.estimates == {"estimate": Decimal(".4")}
    for output in [
        {"outcome": "supported", "estimate": Decimal(".4")},
        {"outcome": "supported", "estimates": {"other": Decimal(1)}},
        {"outcome": "supported", "estimates": {"estimate": Decimal("NaN")}},
    ]:
        assert isinstance(derive(output), AssessmentFinding)
    assert writer.read_view is not None


def test_structural_match_is_checked_at_the_write_boundary_and_under_audit(corpora):
    writer = corpora()
    other = build_claim(
        TESTING_PROFILE,
        operator="testing/affects",
        roles={"cause": Referent("testing/entity", "EX:other"), "effect": Referent("testing/outcome", "EX:y")},
        layer="causal",
        polarity="positive",
    )
    p = writer.add(stored.proposition_node("other", title="Other", claim=project_claim(other)))
    spec = freeze(spec_draft(target=p.id), held_rules=spec_rules(), **freeze_context())
    node = stored.analysis_spec_node(spec)
    with pytest.raises(ValidationRefused, match="estimand-target-mismatch"):
        writer.add(node)
    raw_write(writer.root, node)
    assert any(
        f.ref == node.id and f.code == "spec-target-contradicted"
        for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile)
    )


def test_every_target_member_enters_the_key_and_payload_does_not(corpora):
    writer = corpora()
    a = AssessmentValue("s", "r", "p", "supported", "rule", typed_target())
    b = replace(a, spec="other", run="other", outcome="refuted", estimates={"estimate": Decimal(".5")})
    assert a.key() == b.key() and a.identity() != b.identity()
    changed = replace(a, target=typed_target(estimand=typed_estimand(reference=ValueReference(Decimal(1)))))
    assert a.key() != changed.key() and a.facet_digest() != changed.facet_digest()
    published = publish_corpus(writer, claim=project_claim(TESTING_CLAIM), publish=True)
    restored = stored.assessment_value(reopen(writer.root).get(published.assessment.id), profile=writer.profile)
    assert restored.key() == published.derived_value.key()


def test_one_answer_does_not_read_magnitude(corpora):
    corpora()
    before = evaluate(**scenario())
    context = scenario()
    first, second = context["records"].assessments
    context["records"] = replace(
        context["records"], assessments=(replace(first, estimates={"estimate": Decimal(".4")}), second)
    )
    after = evaluate(**context)
    assert isinstance(before, Belief) and isinstance(after, Belief)
    assert before.value == after.value and before.belief_input_digest != after.belief_input_digest


def test_the_reproduction_recreates_re_authors_and_re_derives_from_disk(corpora):
    """The driver's own recorded report, read by name, beside the
    transition checks this module can exercise on a successor-pinned corpus."""
    from reproduction.paths import STATE

    assert STATE.is_file(), (
        f"the mm30 reproduction's recorded state is not at {STATE}; set SCIENCE_MM30_ROOT to the work root "
        "beside the main checkout. This is an error and not a skip: the row is read from the driver's run."
    )
    state = json.loads(STATE.read_text(encoding="utf-8"))
    report = state["fresh_process_restoration"]
    for key in ("spec_restored", "assessment_restored", "belief_equal", "prior_pre_grammar"):
        assert report[key] is True, key
    assert state["spec_identity"] == "10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714"
    assert state["spec_prose_identity"] == "86aaa1a8a8edda8217a1d6f5f6ae28c89fae7362176a214f9fd9fdf95e3f2b1d"
    # Re-targeted 2026-09-16: the composite-claims lane recreated the corpus again under its own successor
    # contracts and the assessment identity derives from the run closure, so a new run moves
    # it. This is the live pin.
    assert state["assessment_identity_derived"] == "27bd9753ffa77bf604957537bd6497724ce14d9682c0bc3291d594a99e20c4f9"
    assert state["assessment_identity_stored"] == state["assessment_identity_derived"]
    assert state["belief_answer"] == state["rederived_belief"]
    assert state["belief_answer"]["kind"] == "NoBelief" and state["belief_answer"]["reason"] == "no-directional-outcome"
    assert state["corpus_check_findings"] == 0 and state["audit_findings"] == 0

    # The transition, as measured: the prior state's assessment
    # refuses by name, its spec returns no typed value, and the audit reports
    # `profile-mismatch: base` and nothing else.
    prior = state["prior_corpus_state"]
    assert prior["prior_pre_grammar"] is True
    assert prior["assessment_refusal"] == "PreGrammarAssessment"
    assert prior["spec_refusal"] == "MalformedRecord"  # pre-projection, so `restore`'s gate is never reached
    assert prior["audit"] == ["profile-mismatch: base"]
    # The digest half is measured at the two identities that move, the
    # belief value being equal and carrying no digest of its own.
    assert prior["spec_ref"].endswith(state["spec_prose_identity"])
    assert prior["assessment_ref"] == "assessment:316272987716ac4f"

    # The same refusals, reachable here: a pre-grammar projection is refused by
    # its own name, never coerced into the typed reader.
    spec = freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())
    projection = frozen_projection(spec)
    del projection["estimand_grammar"]
    projection["estimand"] = "the effect of x on y"
    projection["applicability"] = "the sampled population"
    with pytest.raises(PreGrammarSpec, match="pre-grammar spec"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=TESTING_PROFILE)

    # And both codes fire on a corpus pinned to the successor holding
    # raw-written pre-grammar records — never `derivation-malformed`.
    writer = corpora()
    pre_grammar_spec = stored._node(
        "analysis-spec",
        "old",
        "old",
        {
            stored.ANALYSIS_SPEC_FACET: {
                "identity": "old",
                "projection": v1.encode(
                    {
                        "target": "proposition:p",
                        "estimand": "prose",
                        "method": "m",
                        "assumptions": "a",
                        "falsification": "f",
                        "input_roles": [],
                        "applicability": "prose",
                        "interpretation_rule": "r",
                        "equivalence_rule": "e",
                        "parameters": {},
                        "nondeterminism": {"variant": "deterministic"},
                        "rule_bindings": [],
                    }
                ).decode(),
            }
        },
        (),
    )
    pre_grammar_assessment = stored._node(
        "assessment",
        "old",
        "old",
        {
            stored.ASSESSMENT_FACET: {
                "spec": "old",
                "run": "run:x",
                "proposition": "proposition:p",
                "outcome": "supported",
                "interpretation_rule": "r",
                "estimand": "prose",
            }
        },
        (),
    )
    raw_write(writer.root, stored.stamp_semantic_identity(pre_grammar_spec))
    raw_write(writer.root, stored.stamp_semantic_identity(pre_grammar_assessment))
    codes = {f.ref: f.code for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)}
    assert codes[pre_grammar_spec.id] == "spec-pre-grammar"
    assert codes[pre_grammar_assessment.id] == "assessment-pre-grammar"
    assert "derivation-malformed" not in codes.values()

    # The stored readers themselves refuse by name, over the unvalidated route
    # `audit_corpus` takes — no reader returns a typed value for either.
    unvalidated = {node.id: node for node in reopen(writer.root).iter_stored()}
    with pytest.raises(PreGrammarAssessment, match="pre-grammar assessment"):
        stored.assessment_value(unvalidated[pre_grammar_assessment.id], profile=TESTING_PROFILE)
    with pytest.raises(PreGrammarSpec, match="pre-grammar spec"):
        stored.analysis_spec_value(unvalidated[pre_grammar_spec.id], profile=TESTING_PROFILE)


def test_baseline_sort_roleless_template_and_disjoint_scope_refuse():
    from beliefs.estimand import RoleTermLevels
    from beliefs.restriction import co_scope

    with pytest.raises(EstimandError):
        typed_estimand(
            bindings={
                "response": typed_estimand().bindings["response"],
                "grouping": RoleTermLevels(
                    "cause", None, (Referent("testing/entity", "EX:a"), Referent("testing/outcome", "EX:b"))
                ),
            }
        )
    document = _testing_document()
    document["templates"]["affects"]["roles"] = {}
    with pytest.raises(MalformedContract):
        domain.parse_domain_contract(document, source="<roleless>", base=shipped_base_contract(), predecessor=None)
    left = {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(0), Fraction(1), True, True)}
    right = {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(2), Fraction(3), True, True)}
    assert co_scope(left, right, TESTING_PROFILE) == "disjoint"
