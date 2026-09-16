"""Cut 31: the typed estimand, row by row, over registered durable corpora.

One test per guarantee row of the estimand-typing design's §8 table Q, named
`test_q<n>_<slug>` and composed from the unit tests' own constructions rather
than from a second set — the `corpora` fixture is `test_facet_acceptance.py`'s,
re-pointed at the profile whose domain declares `testing/affects` and its
`estimands:` entry, because a stored spec restores only under the profile that
wrote it.

Q10 is the exception by design: the mm30 reproduction's re-run is the driver's,
executed once against the corpus on the certified volume, and this row reads
what it recorded (`docs/designs/2026-09-05-mm30-reproduction.md` §10) beside
the transition arms it can exercise here. It reads the driver's report by name
and asserts nothing the addendum does not record.
"""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from authority import FULL
from fixtures_cut3 import (
    TESTING_CLAIM,
    TESTING_PROFILE,
    UNCONSULTED,
    spec_draft,
    spec_rules,
    typed_applicability,
    typed_estimand,
)
from fixtures_cut4 import raw_write, reopen
from profiles import pins_for
from test_audit import assessment_closure
from test_belief import scenario
from test_estimand import E, I, L, M, O, parts

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.belief import Belief, evaluate
from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import domain, parse_base_contract
from beliefs.decode import applicability_from_stored, estimand_from_stored
from beliefs.errors import (
    ContractDisagreement,
    ContrastRefused,
    ControlRefused,
    EstimandError,
    EstimandFragmentRefused,
    EstimandSortMismatch,
    ImportRefused,
    MalformedContract,
    MalformedWireEstimand,
    MeasureRefused,
    PreGrammarAssessment,
    PreGrammarSpec,
    ProfileError,
    ReferenceRefused,
    RestrictionSortMismatch,
    SuccessionViolation,
    TagCollision,
    UnboundReferent,
    UncertaintyRefused,
    UndeclaredDimension,
    UntypedEstimandMember,
    ValidationRefused,
)
from beliefs.estimand import (
    ContinuousContrast,
    Control,
    Estimand,
    Interval,
    LevelsContrast,
    Measure,
    StandardError,
    applicability_projection,
    build_applicability,
    build_estimand,
    co_scoped,
    commensurable,
    estimand_projection,
    uncertainty_from_mapping,
)
from beliefs.identity import v1
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.projection import claim_identity, project_claim
from beliefs.record import AssessmentValue
from beliefs.resolution import TermOutcome, build_snapshot
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


def _base_document() -> dict:
    return yaml.safe_load((REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml").read_text(encoding="utf-8"))


def _testing_document() -> dict:
    return yaml.safe_load((REPO_ROOT / "fixtures" / "contracts" / "testing.yaml").read_text(encoding="utf-8"))


def _parse_testing(document, *, predecessor=None):
    return domain.parse_domain_contract(
        document, source="<cut31>", base=shipped_base_contract(), predecessor=predecessor
    )


def _built(claim=TESTING_CLAIM, *, snapshot=UNCONSULTED, profile=TESTING_PROFILE, **overrides) -> Estimand:
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


def _build_with(overrides: dict) -> Estimand:
    """One refusal fixture's overrides, applied to the shared parts. Spread at
    the call site instead would make the overrides candidates for `_built`'s
    own keywords, which is a type error and not what the fixture means."""
    estimand, _receipt = build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=UNCONSULTED, **parts(**overrides))
    return estimand


def _proposition(writer, claim):
    return writer.add(stored.proposition_node(f"p-{claim_identity(claim)[:8]}", title="p", claim=project_claim(claim)))


def _rule(output):
    return {"impl-interp-1": RuleImplementation(identity="impl-interp-1", evaluate=lambda manifest: output, fixtures=())}


def _derive(spec, output):
    return build_assessment(assessment_closure(spec), specs={spec.identity: spec}, implementations=_rule(output))


# --- Q1 ---------------------------------------------------------------------


def test_q1_the_estimands_structure_is_kernel_owned_and_closed(corpora):
    """Q1: the closed sets live in the base contract and nowhere else, and the
    implementation cannot widen one without the contract saying so."""
    writer = corpora()
    grammar = TESTING_PROFILE.estimand_grammar
    assert grammar.contrast_kinds == ("levels", "continuous")
    assert grammar.scales == ("additive", "multiplicative")
    assert grammar.uncertainty_kinds == ("interval", "standard-error")
    assert writer.read_view is not None

    missing = _base_document()
    del missing["estimand_grammar"]
    with pytest.raises(MalformedContract, match="estimand_grammar"):
        parse_base_contract(missing, source="<no-grammar>")

    unknown = _base_document()
    unknown["estimand_grammar"]["identification_kinds"] = ["observational"]
    with pytest.raises(MalformedContract, match="unknown field"):
        parse_base_contract(unknown, source="<unknown-key>")

    encoding = _base_document()
    encoding["estimand_grammar"]["tag_encoding"] = "science.identity.v2"
    with pytest.raises(MalformedContract, match="tag_encoding"):
        parse_base_contract(encoding, source="<encoding>")

    duplicated = _base_document()
    duplicated["estimand_grammar"]["scales"] = ["additive", "additive"]
    with pytest.raises(TagCollision):
        parse_base_contract(duplicated, source="<duplicate>")

    for member in ("estimand_grammar", "contrast_kinds", "scales", "uncertainty_kinds"):
        document = _testing_document()
        document[member] = {"version": 1}
        with pytest.raises(MalformedContract):
            _parse_testing(document)

    # The shipped fixture is what fails when a closed set is widened in code:
    # `ordinal` is not on the contract's list, so the build must refuse.
    with pytest.raises(MeasureRefused, match="closed set"):
        _built(measure=Measure(quantity=Referent(M, "EX:tpm"), scale="ordinal"))
    with pytest.raises(UncertaintyRefused, match="neither interval nor standard-error"):
        uncertainty_from_mapping(
            {"kind": "confidence-band", "value": Decimal("0.1")}, estimate=Decimal("0.4"), scale="additive"
        )
    projection = estimand_projection(_built())
    projection["contrast"]["kind"] = "levels-and-continuous"  # type: ignore[index]
    with pytest.raises(MalformedWireEstimand):
        estimand_from_stored(projection, profile=TESTING_PROFILE)

    # And an admitted scale still reaches disk under the same grammar.
    target = _proposition(writer, TESTING_CLAIM)
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    node = writer.add(stored.analysis_spec_node(spec))
    restored = stored.analysis_spec_value(reopen(writer.root).get(node.id), profile=TESTING_PROFILE)
    assert restored.estimand.measure.scale in grammar.scales


# --- Q2 ---------------------------------------------------------------------


def test_q2_estimands_is_domain_issued_operator_bound_and_succession_governed(corpora):
    """Q2: the declaration is the domain's, keyed by an operator it declares,
    and governed by the four succession rules M6 already carries."""
    writer = corpora()
    assert writer.read_view is not None
    contract = _parse_testing(_testing_document())
    assert set(contract.estimands) == {"affects", "correlates-with"}
    assert TESTING_PROFILE.estimand("testing/affects").level_sorts == {"0": "testing/level"}

    undeclared = _testing_document()
    undeclared["estimands"]["regulates"] = undeclared["estimands"]["affects"]
    with pytest.raises(MalformedContract, match="regulates"):
        _parse_testing(undeclared)

    outside = _testing_document()
    outside["estimands"]["affects"]["level_sorts"] = {"2": "level"}
    with pytest.raises(MalformedContract, match="Fin"):
        _parse_testing(outside)

    not_a_slot = _testing_document()
    not_a_slot["estimands"]["affects"]["level_sorts"] = {"first": "level"}
    with pytest.raises(MalformedContract, match="slot index"):
        _parse_testing(not_a_slot)

    nullary = _testing_document()
    nullary["operators"]["holds"] = {"arity": 0, "arg_sorts": [], "sign_apt": False, "layers": ["structural"], "dimensions": []}
    nullary["estimands"]["holds"] = {"level_sorts": {}, "measure_sort": "measure", "identification_sort": "identification", "conditioning_sort": "entity"}
    with pytest.raises(MalformedContract, match="arity 0"):
        _parse_testing(nullary)

    unresolved = _testing_document()
    unresolved["estimands"]["affects"]["measure_sort"] = "biology/assay"
    with pytest.raises(MalformedContract, match="namespace 'biology'"):
        compile_profile(shipped_base_contract(), [_parse_testing(unresolved)])

    # Succession: adding an entry for an operator that had none is accepted,
    # and the operator's own projection does not move (M6 unamended).
    prior_document = _testing_document()
    del prior_document["estimands"]["correlates-with"]
    prior = _parse_testing(prior_document)
    successor_document = _testing_document()
    successor_document["lineage"] = {"successor": prior.content_identity}
    successor = _parse_testing(successor_document, predecessor=prior)
    assert "correlates-with" in successor.estimands
    assert successor.operators["correlates-with"].schema_projection() == prior.operators["correlates-with"].schema_projection()

    settled = _parse_testing(_testing_document())
    for member, value in (
        ("level_sorts", {}),
        ("measure_sort", "entity"),
        ("identification_sort", "entity"),
        ("conditioning_sort", "outcome"),
    ):
        changed = _testing_document()
        changed["lineage"] = {"successor": settled.content_identity}
        changed["estimands"]["affects"][member] = value
        with pytest.raises(SuccessionViolation, match="estimand:affects"):
            _parse_testing(changed, predecessor=settled)

    dropped = _testing_document()
    dropped["lineage"] = {"successor": settled.content_identity}
    del dropped["estimands"]["affects"]
    with pytest.raises(SuccessionViolation, match="estimand:affects"):
        _parse_testing(dropped, predecessor=settled)

    retired = _testing_document()
    retired["lineage"] = {"successor": settled.content_identity}
    retired["operators"]["affects"]["retired"] = True
    assert "affects" in _parse_testing(retired, predecessor=settled).estimands

    # Negative: key order is inert in both the projection and the identity.
    two_slots = _testing_document()
    two_slots["estimands"]["affects"]["level_sorts"] = {"1": "level", "0": "level"}
    reordered = copy.deepcopy(two_slots)
    reordered["estimands"]["affects"]["level_sorts"] = {"0": "level", "1": "level"}
    assert _parse_testing(two_slots).estimands["affects"].schema_projection() == _parse_testing(reordered).estimands["affects"].schema_projection()
    assert _parse_testing(two_slots).content_identity == _parse_testing(reordered).content_identity


# --- Q3 ---------------------------------------------------------------------


def test_q3_an_estimand_is_unconstructible_outside_its_claims_operator_declaration(corpora):
    """Q3: every §7.1 refusal names its position, the fragment refuses rather
    than flattens, and `claim` and `operator` come from the `Claim` handed in."""
    writer = corpora()
    other_claim = build_claim(
        TESTING_PROFILE,
        operator="testing/affects",
        args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")),
        layer="causal",
        polarity="positive",
    )

    for make, error, position in (
        (lambda: {"contrast": LevelsContrast(slot=2, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "slot 2"),
        (lambda: {"contrast": LevelsContrast(slot=1, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "no level sort"),
        (lambda: {"contrast": LevelsContrast(slot=0, baseline=Referent(E, "EX:a"), comparison=Referent(L, "EX:b"))}, EstimandSortMismatch, "contrast.baseline"),
        (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(E, "EX:q"), increment=Decimal(1))}, EstimandSortMismatch, "contrast.quantity"),
        (lambda: {"measure": Measure(quantity=Referent(E, "EX:tpm"), scale="additive")}, EstimandSortMismatch, "measure.quantity"),
        (lambda: {"control": Control(identification=Referent(E, "EX:obs"), conditioning=())}, EstimandSortMismatch, "control.identification"),
        (lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(O, "EX:c"),))}, EstimandSortMismatch, "control.conditioning[0]"),
    ):
        with pytest.raises(error) as caught:
            _build_with(make())
        assert position in str(caught.value)

    # A slot the operator declares no level sort for admits only a continuous
    # contrast; the continuous one there builds.
    assert _built(contrast=ContinuousContrast(slot=1, quantity=Referent(M, "EX:log2-tpm"), increment=Decimal(1)))

    with pytest.raises(ControlRefused, match="duplicate"):
        _built(control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c"), Referent(E, "EX:c"))))
    with pytest.raises(ContrastRefused, match="increment"):
        _built(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(0)))
    with pytest.raises(ContrastRefused, match="increment"):
        _built(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal(-1)))
    with pytest.raises(ContrastRefused, match="Decimal"):
        _built(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=1.0))  # type: ignore[arg-type]
    with pytest.raises(ReferenceRefused, match="Decimal"):
        _built(reference=0.0)  # type: ignore[arg-type]
    with pytest.raises(ReferenceRefused, match="multiplicative"):
        _built(measure=Measure(quantity=Referent(M, "EX:hr"), scale="multiplicative"), reference=Decimal(0))
    with pytest.raises(ProfileError, match="declares no estimand"):
        _built(build_claim(TESTING_PROFILE, operator="testing/subtype-of", args=(Referent(E, "EX:a"), Referent(E, "EX:b")), layer="structural"))

    # D3's five outcomes stay distinct: `not-member` refuses, `not-consulted`
    # mints with a receipt, and the minted value is the same either way.
    binding = TESTING_PROFILE.sorts[L].vocabulary
    readable = build_snapshot(readable={binding: ["EX:ndmm", "EX:pd", "EX:tpm", "EX:observational"]})
    member_estimand, receipt = build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=readable, **parts())
    assert receipt.outcomes["estimand:contrast.baseline"] is TermOutcome.MEMBER
    with pytest.raises(UnboundReferent, match="estimand:contrast.comparison"):
        _built(snapshot=readable, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:ndmm"), comparison=Referent(L, "EX:mgus")))
    unconsulted, unconsulted_receipt = build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=UNCONSULTED, **parts())
    assert all(outcome is TermOutcome.NOT_CONSULTED for outcome in unconsulted_receipt.outcomes.values())
    assert estimand_projection(unconsulted) == estimand_projection(member_estimand)

    # The fragment: nothing richer is flattened into it.
    with pytest.raises(EstimandFragmentRefused, match="one measure"):
        build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=UNCONSULTED, **parts(), measures=(parts()["measure"],) * 2)  # type: ignore[arg-type]
    for keyword in ("references", "arms", "attenuation"):
        with pytest.raises(EstimandFragmentRefused, match=keyword):
            build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=UNCONSULTED, **parts(), **{keyword: object()})  # type: ignore[arg-type]

    # Opacity: no public field-wise constructor, and the claim member is the
    # identity of the `Claim` handed in — never a string a caller supplies.
    with pytest.raises(EstimandError, match="use build_estimand"):
        Estimand(claim="c", operator="o", contrast=None, measure=None, reference=Decimal(0), control=None)  # type: ignore[call-arg]
    with pytest.raises(UntypedEstimandMember, match="built against a Claim"):
        build_estimand(TESTING_PROFILE, claim_identity(TESTING_CLAIM), snapshot=UNCONSULTED, **parts())  # type: ignore[arg-type]
    here, there = _built(), _built(other_claim)
    assert here.claim == claim_identity(TESTING_CLAIM) and there.claim == claim_identity(other_claim)
    assert here.claim != there.claim
    assert here.operator == there.operator == TESTING_CLAIM.operator

    # And the admitted value reaches disk and comes back the same.
    target = _proposition(writer, TESTING_CLAIM)
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    node = writer.add(stored.analysis_spec_node(spec))
    assert stored.analysis_spec_value(reopen(writer.root).get(node.id), profile=TESTING_PROFILE).estimand == spec.estimand


# --- Q4 ---------------------------------------------------------------------


def test_q4_applicability_is_a_qualifier_map_over_the_target_operators_dimensions(corpora):
    """Q4: the map is the claim grammar's flat fragment over the operator's own
    dimensions, comparable in both directions, and read by no P row."""
    writer = corpora()
    assert writer.read_view is not None
    adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
    everyone = typed_applicability()

    with pytest.raises(UndeclaredDimension):
        build_applicability(TESTING_PROFILE, TESTING_CLAIM, {"testing/regime": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=UNCONSULTED)
    with pytest.raises(RestrictionSortMismatch):
        build_applicability(TESTING_PROFILE, TESTING_CLAIM, {"testing/population": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=UNCONSULTED)
    with pytest.raises(UndeclaredDimension):
        applicability_from_stored(
            {"testing/regime": applicability_projection(adults)["testing/population"]},
            profile=TESTING_PROFILE, operator="testing/affects",
        )
    # Two restrictions on one dimension is unspellable: the map is keyed by
    # dimension, and the stored form refuses anything but one qualifier body.
    with pytest.raises(MalformedWireEstimand):
        applicability_from_stored(
            {"testing/population": [applicability_projection(adults)["testing/population"]] * 2},
            profile=TESTING_PROFILE, operator="testing/affects",
        )
    cohort = TESTING_PROFILE.sorts["testing/cohort"].vocabulary
    with pytest.raises(UnboundReferent, match="restriction"):
        build_applicability(
            TESTING_PROFILE, TESTING_CLAIM,
            {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:absent"))},
            snapshot=build_snapshot(readable={cohort: ["EX:adults"]}),
        )

    assert applicability_projection(everyone) == {}
    assert co_scoped(adults, adults) and not co_scoped(adults, everyone)
    assert not co_scoped(everyone, adults)  # decidable in both directions
    qualified = build_claim(
        TESTING_PROFILE,
        operator="testing/affects",
        args=TESTING_CLAIM.args,
        qualifiers={"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))},
        layer="causal",
        polarity="positive",
    )
    assert co_scoped(adults, qualified.qualifiers)
    assert not co_scoped(everyone, qualified.qualifiers)

    # P6 verbatim: change only `applicability` and the belief value stands
    # while the digest moves — and no mismatch finding exists to be emitted.
    from dataclasses import replace

    import beliefs.belief as belief_module

    base = evaluate(**scenario())
    kwargs = scenario()
    first, second = kwargs["records"].assessments
    moved = evaluate(**scenario(records=replace(kwargs["records"], assessments=(replace(first, applicability=adults), second))))
    assert isinstance(base, Belief) and isinstance(moved, Belief)
    assert moved.value == base.value
    assert moved.belief_input_digest != base.belief_input_digest
    assert not any("mismatch" in name.lower() for name in vars(belief_module))


# --- Q5 ---------------------------------------------------------------------


def test_q5_estimate_and_uncertainty_are_typed_on_the_specs_scale(corpora):
    """Q5: the rule yields decimals on the spec's scale and nothing else; each
    violation is an `AssessmentFinding` naming it, and never `inconclusive`."""
    writer = corpora()
    assert writer.read_view is not None
    spec = freeze(spec_draft(), held_rules=spec_rules())

    string_estimate = _derive(spec, {"outcome": "supported", "estimate": "0.4"})
    assert isinstance(string_estimate, AssessmentFinding)
    assert "binary floats are refused at the boundary" in string_estimate.reason
    assert "inconclusive" not in string_estimate.reason

    float_estimate = _derive(spec, {"outcome": "supported", "estimate": 0.4})
    assert isinstance(float_estimate, AssessmentFinding)
    assert "binary floats are refused at the boundary" in float_estimate.reason

    excluding = _derive(spec, {
        "outcome": "supported", "estimate": Decimal("0.4"),
        "uncertainty": {"kind": "interval", "low": Decimal("0.5"), "high": Decimal("0.7"), "level": Decimal("0.95")},
    })
    assert isinstance(excluding, AssessmentFinding) and "excludes the estimate" in excluding.reason

    below = _derive(spec, {
        "outcome": "supported", "estimate": Decimal("0.4"),
        "uncertainty": {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.2"), "level": Decimal("0.95")},
    })
    assert isinstance(below, AssessmentFinding) and "excludes the estimate" in below.reason

    for output, reason in (
        ({"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.7"), "level": Decimal(1)}}, "level"),
        ({"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "standard-error", "value": Decimal("-0.1")}}, "non-negative"),
        ({"outcome": "supported", "uncertainty": {"kind": "standard-error", "value": Decimal("0.1")}}, "estimate"),
    ):
        finding = _derive(spec, output)
        assert isinstance(finding, AssessmentFinding) and reason in finding.reason
        assert "inconclusive" not in finding.reason

    multiplicative = freeze(
        spec_draft(estimand=typed_estimand(measure=Measure(Referent(M, "EX:hr"), "multiplicative"), reference=Decimal(1))),
        held_rules=spec_rules(),
    )
    non_positive = _derive(multiplicative, {"outcome": "supported", "estimate": Decimal(0)})
    assert isinstance(non_positive, AssessmentFinding) and "multiplicative" in non_positive.reason

    # A rule that restates the spec's own reference or scale is a rule that lies.
    for restated in ("reference", "scale"):
        lying = _derive(spec, {"outcome": "supported", "estimate": Decimal("0.4"), restated: Decimal(0) if restated == "reference" else "additive"})
        assert isinstance(lying, AssessmentFinding), restated
        assert "a rule yields outcome, estimate and uncertainty only" in lying.reason

    # Negative: a rule yielding nothing but `outcome` mints as it always has,
    # and the reproduction's own rule identity is untouched.
    minted = _derive(spec, {"outcome": "supported"})
    assert isinstance(minted, AssessmentValue)
    assert minted.estimate is None and minted.uncertainty is None
    typed = _derive(spec, {
        "outcome": "supported", "estimate": Decimal("0.4"),
        "uncertainty": {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.7"), "level": Decimal("0.95")},
    })
    assert isinstance(typed, AssessmentValue) and isinstance(typed.uncertainty, Interval)
    assert typed.estimand == spec.estimand
    driver_spec = (REPO_ROOT / "python" / "tools" / "reproduction" / "spec.py").read_text(encoding="utf-8")
    assert 'INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"' in driver_spec


# --- Q6 ---------------------------------------------------------------------


def test_q6_structural_match_is_checked_at_the_write_boundary_and_under_audit(corpora):
    """Q6: the spec's estimand must name its target's claim **and** operator at
    the write boundary and at import, and the audit contradicts what a raw
    write got past. Semantic match is not claimed."""
    writer = corpora()
    other_claim = build_claim(
        TESTING_PROFILE,
        operator="testing/affects",
        args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")),
        layer="causal",
        polarity="positive",
    )

    admitted_target = _proposition(writer, TESTING_CLAIM)
    admitted = freeze(spec_draft(target=admitted_target.id), held_rules=spec_rules())
    assert writer.add(stored.analysis_spec_node(admitted)).id == f"analysis-spec:{admitted.identity}"

    elsewhere = corpora()
    other_target = _proposition(elsewhere, other_claim)
    same_operator = freeze(spec_draft(target=other_target.id), held_rules=spec_rules())
    with pytest.raises(ValidationRefused, match="estimand-target-mismatch"):
        elsewhere.add(stored.analysis_spec_node(same_operator))
    unresolvable = freeze(spec_draft(target="proposition:elsewhere"), held_rules=spec_rules())
    with pytest.raises(ValidationRefused, match="estimand-target-unresolvable"):
        elsewhere.add(stored.analysis_spec_node(unresolvable))
    with pytest.raises(ImportRefused, match="estimand-target-unresolvable"):
        elsewhere.import_bundle(
            [stored.analysis_spec_node(unresolvable)], observer="o", instrument="i",
            opened_at="2026-09-15T00:00:00Z", closed_at="2026-09-15T00:00:01Z",
        )

    # The inconsistent stored pair: the target's true claim identity beside a
    # different declared operator, everything else correctly typed under it.
    correlates = build_claim(
        TESTING_PROFILE, operator="testing/correlates-with",
        args=(Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")), layer="statistical", polarity="positive",
    )
    foreign, _receipt = build_estimand(
        TESTING_PROFILE, correlates, snapshot=UNCONSULTED,
        contrast=ContinuousContrast(0, Referent(M, "EX:tpm"), Decimal(1)),
        measure=Measure(Referent(M, "EX:tpm"), "additive"), reference=Decimal(0),
        control=Control(Referent(I, "EX:observational"), ()),
    )
    forged_projection = frozen_projection(freeze(spec_draft(target=admitted_target.id, estimand=foreign), held_rules=spec_rules()))
    forged_projection["estimand"]["claim"] = claim_identity(TESTING_CLAIM)  # type: ignore[index]
    forged_identity = v1.digest(SPEC_DOMAIN, forged_projection)
    forged = stored._node(
        "analysis-spec", forged_identity, "forged",
        {stored.ANALYSIS_SPEC_FACET: {"identity": forged_identity, "projection": v1.encode(forged_projection).decode()}},
        (),
    )
    with pytest.raises(ValidationRefused, match="estimand-target-mismatch.*operator"):
        writer.add(forged)

    raw = corpora()
    raw_target = _proposition(raw, TESTING_CLAIM)
    assert raw_target.id == admitted_target.id
    raw_write(raw.root, forged)
    # It decodes without refusal: comparing claim identities only lets it through.
    decoded = stored.analysis_spec_value(reopen(raw.root).get(forged.id), profile=TESTING_PROFILE)
    assert decoded.estimand.claim == claim_identity(TESTING_CLAIM)
    assert decoded.estimand.operator == "testing/correlates-with"
    importer = corpora()
    _proposition(importer, TESTING_CLAIM)  # the target resolves here, so only the operator disagrees
    with pytest.raises(ImportRefused, match="estimand-target-mismatch"):
        importer.import_bundle(
            [forged], observer="o", instrument="i",
            opened_at="2026-09-15T00:00:00Z", closed_at="2026-09-15T00:00:01Z",
        )
    [operator_finding] = [f for f in audit_corpus(reopen(raw.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE) if f.ref == forged.id]
    assert operator_finding.code == "spec-target-contradicted" and operator_finding.detail == "operator"

    # A raw-written same-operator mismatch is caught only under audit.
    contradicted = corpora()
    contradicted_target = _proposition(contradicted, other_claim)
    mismatching = stored.analysis_spec_node(freeze(spec_draft(target=contradicted_target.id), held_rules=spec_rules()))
    raw_write(contradicted.root, mismatching)
    assert reopen(contradicted.root).get(mismatching.id).id == mismatching.id  # not refused on read
    [claim_finding] = [f for f in audit_corpus(reopen(contradicted.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE) if f.ref == mismatching.id]
    assert claim_finding.code == "spec-target-contradicted" and claim_finding.detail == "claim"

    # Negative: a measured quantity that does not in fact operationalize the
    # claim's argument is admitted — the check is structural and says so.
    other_measure = corpora()
    other_measure_target = _proposition(other_measure, TESTING_CLAIM)
    unrelated = freeze(
        spec_draft(target=other_measure_target.id, estimand=typed_estimand(measure=Measure(Referent(M, "EX:unrelated-assay"), "additive"))),
        held_rules=spec_rules(),
    )
    assert other_measure.add(stored.analysis_spec_node(unrelated)).id == f"analysis-spec:{unrelated.identity}"
    assert not [f for f in audit_corpus(reopen(other_measure.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE) if f.code == "spec-target-contradicted"]


# --- Q7 ---------------------------------------------------------------------


def test_q7_every_member_enters_identity_and_only_members_do(corpora):
    """Q7: each estimand and applicability member moves the spec identity;
    conditioning order and decimal spelling do not; on the assessment the facet
    digest moves and the belief value does not."""
    writer = corpora()
    assert writer.read_view is not None
    base_identity = freeze(spec_draft(), held_rules=spec_rules()).identity

    def moved(**overrides) -> bool:
        return freeze(spec_draft(estimand=typed_estimand(**overrides)), held_rules=spec_rules()).identity != base_identity

    assert moved(contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm")))
    assert moved(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:tpm"), increment=Decimal(1)))
    assert moved(measure=Measure(quantity=Referent(M, "EX:other"), scale="additive"))
    assert moved(measure=Measure(quantity=Referent(M, "EX:tpm"), scale="multiplicative"), reference=Decimal(1))
    assert moved(reference=Decimal("0.5"))
    assert moved(control=Control(identification=Referent(I, "EX:longitudinal"), conditioning=()))
    assert moved(control=Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),)))

    # `claim` is a member: the same structure against another claim is another spec.
    other_claim = build_claim(
        TESTING_PROFILE, operator="testing/affects",
        args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive",
    )
    against_other, _receipt = build_estimand(TESTING_PROFILE, other_claim, snapshot=UNCONSULTED, **parts())
    assert freeze(spec_draft(estimand=against_other), held_rules=spec_rules()).identity != base_identity

    # `increment` is a member; its decimal spelling is not.
    def continuous(increment):
        return freeze(
            spec_draft(estimand=typed_estimand(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:tpm"), increment=increment))),
            held_rules=spec_rules(),
        ).identity

    assert continuous(Decimal(1)) != continuous(Decimal(10))
    assert continuous(Decimal(1)) == continuous(Decimal("1.0"))

    # `applicability` is a member; conditioning order is not.
    adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
    assert freeze(spec_draft(applicability=adults), held_rules=spec_rules()).identity != base_identity
    forwards = typed_estimand(control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c1"), Referent(E, "EX:c2"))))
    backwards = typed_estimand(control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c2"), Referent(E, "EX:c1"))))
    assert freeze(spec_draft(estimand=forwards), held_rules=spec_rules()).identity == freeze(spec_draft(estimand=backwards), held_rules=spec_rules()).identity

    # The grammar member is in the projection, so a pre-grammar spec and a
    # typed one can never share an identity.
    from beliefs.contract.base import ESTIMAND_GRAMMAR

    projection = frozen_projection(freeze(spec_draft(), held_rules=spec_rules()))
    assert projection["estimand_grammar"] == ESTIMAND_GRAMMAR
    assert projection["estimand"] == estimand_projection(typed_estimand())
    assert projection["applicability"] == applicability_projection(typed_applicability())

    # On the assessment: each typed member moves the facet digest and no P row's
    # value moves with it (P6's four arms, now per member).
    from dataclasses import replace

    def assessment(**overrides) -> AssessmentValue:
        fields = {
            "spec": "spec-a", "run": "run-a", "proposition": "prop-1", "outcome": "supported",
            "interpretation_rule": "rule-1", "estimand": typed_estimand(), "applicability": typed_applicability(),
        }
        fields.update(overrides)
        return AssessmentValue(**fields)  # type: ignore[arg-type]

    reference = assessment()
    assert reference.facet_digest() != assessment(estimand=typed_estimand(reference=Decimal(1))).facet_digest()
    assert reference.facet_digest() != assessment(applicability=adults).facet_digest()
    assert reference.facet_digest() != assessment(estimate=Decimal("0.4")).facet_digest()
    assert reference.facet_digest() != assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("0.1"))).facet_digest()

    baseline = evaluate(**scenario())
    kwargs = scenario()
    first, second = kwargs["records"].assessments
    for override in (
        {"estimand": typed_estimand(reference=Decimal(1))},
        {"applicability": adults},
        {"estimate": Decimal("0.4")},
        {"estimate": Decimal("0.4"), "uncertainty": StandardError(Decimal("0.1"))},
    ):
        mutated = evaluate(**scenario(records=replace(kwargs["records"], assessments=(replace(first, **override), second))))
        assert isinstance(baseline, Belief) and isinstance(mutated, Belief)
        assert mutated.value == baseline.value
        assert mutated.belief_input_digest != baseline.belief_input_digest

    # Negative: an editorial change to a consulted contract leaves I_claim alone.
    editorial = _testing_document()
    editorial["description"] = "an editorial change that touches no declaration"
    editorial_profile = compile_profile(shipped_base_contract(), [_parse_testing(editorial)])
    editorial_claim = build_claim(
        editorial_profile, operator="testing/affects", args=TESTING_CLAIM.args, layer="causal", polarity="positive",
    )
    assert claim_identity(editorial_claim) == claim_identity(TESTING_CLAIM)


# --- Q8 ---------------------------------------------------------------------


def test_q8_the_estimands_contracts_are_consulted(corpora):
    """Q8: an assessment reaches the contracts its estimand binds, and only
    those — D6's third trigger."""
    from beliefs.consulted import CorpusPins, consulted_contracts

    writer = corpora()
    assert writer.read_view is not None
    fixture = REPO_ROOT / "python" / "tests" / "fixtures" / "measures-fixture.yaml"
    measures = domain.parse_domain_contract(
        yaml.safe_load(fixture.read_text(encoding="utf-8")), source=str(fixture),
        base=shipped_base_contract(), predecessor=None,
    )
    document = _testing_document()
    document["estimands"]["affects"]["measure_sort"] = "measures/assay"
    measured = compile_profile(shipped_base_contract(), [_parse_testing(document), measures])
    claim = build_claim(
        measured, operator="testing/affects", args=TESTING_CLAIM.args, qualifiers={}, polarity="positive", layer="causal",
    )
    estimand, _receipt = build_estimand(
        measured, claim, snapshot=UNCONSULTED,
        contrast=LevelsContrast(0, Referent(L, "EX:a"), Referent(L, "EX:b")),
        measure=Measure(Referent("measures/assay", "EX:m"), "additive"), reference=Decimal(0),
        control=Control(Referent(I, "EX:obs"), ()),
    )
    pins = pins_for(measured)
    claim_only = consulted_contracts(claims={"p": claim}, profile=measured, node_corpus={}, pins={"c1": pins}, closure_nodes=())
    with_estimand = consulted_contracts(
        claims={"p": claim}, estimands={"a1": estimand}, profile=measured, node_corpus={}, pins={"c1": pins}, closure_nodes=(),
    )
    assert "measures" not in dict(claim_only)
    assert dict(with_estimand)["measures"] == pins.domains["measures"]
    # Bumping a contract the estimand does not reach leaves the set alone.
    assert dict(with_estimand)["testing"] == pins.domains["testing"]
    assert set(dict(with_estimand)) == {"science", "testing", "measures"}

    # A sort pinned by no corpus is unresolvable, not merely disputed.
    unpinned = CorpusPins(science_contract=pins.science_contract, domains={"testing": pins.domains["testing"]})
    with pytest.raises(ContractDisagreement, match="'measures' is consulted but pinned by no corpus"):
        consulted_contracts(
            claims={"p": claim}, estimands={"a1": estimand}, profile=measured,
            node_corpus={}, pins={"c1": unpinned}, closure_nodes=(),
        )


# --- Q9 ---------------------------------------------------------------------


def test_q9_commensuration_is_total_decidable_and_unread_by_v1(corpora):
    """Q9: both predicates are total over admitted values, `identification` is
    the one member outside the key, and v1's evaluator reads neither."""
    import inspect

    import beliefs.belief as belief_module
    import beliefs.evaluation as evaluation_module

    writer = corpora()
    assert writer.read_view is not None
    other_claim = build_claim(
        TESTING_PROFILE, operator="testing/affects",
        args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive",
    )

    here = _built()
    identification = _built(control=Control(identification=Referent(I, "EX:longitudinal"), conditioning=()))
    assert commensurable(here, identification) is True

    for other in (
        _built(contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm"))),
        _built(measure=Measure(quantity=Referent(M, "EX:other"), scale="additive")),
        _built(reference=Decimal("0.5")),
        _built(control=Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),))),
        _built(other_claim),
    ):
        assert commensurable(here, other) is False

    per_unit = _built(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:tpm"), increment=Decimal(1)))
    per_ten = _built(contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:tpm"), increment=Decimal(10)))
    assert commensurable(per_unit, per_ten) is False
    assert commensurable(per_unit, per_unit) is True

    adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
    everyone = typed_applicability()
    assert commensurable(_built(), _built()) is True and co_scoped(adults, everyone) is False

    # Both are exposed from `beliefs.estimand`, both are total, and neither is
    # named anywhere v1 reads.
    import beliefs.estimand as estimand_module

    assert {"commensurable", "co_scoped"} <= set(estimand_module.__all__)
    for module in (belief_module, evaluation_module):
        source = inspect.getsource(module)
        assert "commensurable" not in source and "co_scoped" not in source
    assert isinstance(evaluate(**scenario()), Belief)


# --- Q10 --------------------------------------------------------------------


def test_q10_the_reproduction_recreates_re_authors_and_re_derives_from_disk(corpora):
    """Q10: the driver's own recorded report, read by name, beside the
    transition arms this module can exercise on a successor-pinned corpus."""
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
    assert state["assessment_identity_derived"] == "618c6c584da64b62bbd4c5cd0d5625a95f43367a12b5957b6bdb29e94119957e"
    assert state["assessment_identity_stored"] == state["assessment_identity_derived"]
    assert state["belief_answer"] == state["rederived_belief"]
    assert state["belief_answer"]["kind"] == "NoBelief" and state["belief_answer"]["reason"] == "no-directional-outcome"
    assert state["corpus_check_findings"] == 0 and state["audit_findings"] == 0

    # The transition, as §10.8 measured it: the prior state's assessment
    # refuses by name, its spec returns no typed value, and the audit reports
    # `profile-mismatch: base` and nothing else.
    prior = state["prior_corpus_state"]
    assert prior["prior_pre_grammar"] is True
    assert prior["assessment_refusal"] == "PreGrammarAssessment"
    assert prior["spec_refusal"] == "MalformedRecord"  # pre-projection, so `restore`'s gate is never reached
    assert prior["audit"] == ["profile-mismatch: base"]
    # §8.2: the digest half is measured at the two identities that move, the
    # belief value being equal and carrying no digest of its own.
    assert prior["spec_ref"].endswith(state["spec_prose_identity"])
    assert prior["assessment_ref"] == "assessment:316272987716ac4f"

    # The same refusals, reachable here: a pre-grammar projection is refused by
    # its own name, never coerced into the typed reader.
    spec = freeze(spec_draft(), held_rules=spec_rules())
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
        "analysis-spec", "old", "old",
        {stored.ANALYSIS_SPEC_FACET: {"identity": "old", "projection": v1.encode({
            "target": "proposition:p", "estimand": "prose", "method": "m", "assumptions": "a",
            "falsification": "f", "input_roles": [], "applicability": "prose",
            "interpretation_rule": "r", "equivalence_rule": "e", "parameters": {},
            "nondeterminism": {"variant": "deterministic"}, "rule_bindings": [],
        }).decode()}},
        (),
    )
    pre_grammar_assessment = stored._node(
        "assessment", "old", "old",
        {stored.ASSESSMENT_FACET: {
            "spec": "old", "run": "run:x", "proposition": "proposition:p",
            "outcome": "supported", "interpretation_rule": "r", "estimand": "prose",
        }},
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
