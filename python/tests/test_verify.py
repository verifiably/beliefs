"""R8, R11's in-cell arms, R18, R19's constructor arms, T6's R18
arm. Deferred: R19's import/availability-transition/audit arms and negatives
(c)–(e) (store, world resolver, audit); R11 composes with cut 2's prior
assessment binding and carries no assessment edge.
"""

import dataclasses
import inspect
from pathlib import Path

import pytest
from fixtures_cut3 import (
    SNAKEFILE_NONDETERMINISTIC,
    closure_with,
    interp,
    planned,
    report,
    spec_draft,
    spec_rules,
    traced,
)
from fixtures_cut3 import (
    memory_assessment as run_assessment,
)
from fixtures_cut3 import (
    memory_production as run_production,
)
from fixtures_cut3 import (
    memory_replay as replay_of,
)
from fixtures_cut15 import data_dependent_pair

from beliefs.assess import build_assessment
from beliefs.boundary import RunMinted
from beliefs.errors import CitationRefused, MixedShapes, NotAnAssessmentVerification
from beliefs.identity import v1
from beliefs.production import mint_dataset
from beliefs.recipe import job_key
from beliefs.replay import (
    CONFORMING,
    CONTENT_EQUALITY,
    DATASET_CONTENT_EQUALITY,
    CodeLineageCertification,
    EquivalenceImplementation,
    conformance,
    derive_scope,
)
from beliefs.spec import Deterministic, SpecInput, StochasticUnseeded, freeze, revise
from beliefs.verification import Verification
from beliefs.verify import (
    AssessmentVerification,
    ComparisonReport,
    DatasetProductionVerification,
    _job_diagnostics,
    _mint_verification,
    active_verifications,
    admission_record,
    build_verification,
)


def test_a_differing_job_set_is_reported_by_job_key() -> None:
    original = closure_with(trace=(traced("fit", {"s": "a"}),))
    replayed = closure_with(trace=(traced("fit", {"s": "a"}), traced("fit", {"s": "b"})))
    (message,) = _job_diagnostics(original, replayed)
    assert job_key("fit", (("s", "b"),)) in message


def test_a_data_dependent_replay_over_different_inputs_is_conforming(tmp_path) -> None:
    original, replayed = data_dependent_pair(tmp_path)
    assert conformance(original) == CONFORMING and conformance(replayed) == CONFORMING
    assert _job_diagnostics(original, replayed) != ()


def test_a_differing_job_set_alone_costs_no_scope() -> None:
    narrow = closure_with(
        trace=(traced("fit", {"n": "a"}),),
        planned=(planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),),
        target_keys=(job_key("fit", (("n", "a"),)),),
    )
    wide = closure_with(
        trace=(traced("fit", {"n": "a"}), traced("fit", {"n": "b"})),
        planned=(
            planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),
            planned("fit", ("outputs/b.done",), wildcards=(("n", "b"),)),
        ),
        target_keys=(job_key("fit", (("n", "a"),)),),
    )
    assert narrow.recipe.identity() == wide.recipe.identity()
    assert conformance(narrow) == CONFORMING and conformance(wide) == CONFORMING
    assert derive_scope(narrow, wide, certification=None) == "same-environment"


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    base = tmp_path_factory.mktemp("replay")
    scratch_base = base / "scratch"
    original = run_assessment(base / "original", scratch_base=scratch_base)
    replayed = replay_of(original, base / "replayed", scratch_base=scratch_base)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    return original, replayed


@pytest.fixture(scope="module")
def production_pair(tmp_path_factory):
    base = tmp_path_factory.mktemp("nondet")
    first = run_production(
        base / "a",
        snakefile=SNAKEFILE_NONDETERMINISTIC,
        nondeterminism=StochasticUnseeded(rationale="urandom transform"),
    )
    second = replay_of(first, base / "b", snakefile=SNAKEFILE_NONDETERMINISTIC)
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    return first, second


def verification_of(pair, **overrides) -> AssessmentVerification:
    original, replayed = pair
    spec = freeze(spec_draft(), held_rules=spec_rules())
    kwargs = {
        "specs": {spec.identity: spec},
        "held_rules": {
            "impl-eq-1": CONTENT_EQUALITY,
            "impl-dataset-eq-1": DATASET_CONTENT_EQUALITY,
        },
        "contract_identity": "contract-1",
        "epoch": "epoch-1",
    }
    kwargs.update(overrides)
    verification = build_verification(original.run, replayed.run, **kwargs)
    assert isinstance(verification, AssessmentVerification)
    return verification


# --- R19 ----------------------------------------------------------------------
def test_r19_the_constructor_list_is_closed(pair):
    params = list(inspect.signature(build_verification).parameters)
    assert params == [
        "original",
        "replayed",
        "specs",
        "held_rules",
        "contract_identity",
        "epoch",
        "certification",
        "citation",
    ]
    for forbidden in (
        "report",
        "comparison_report",
        "conformance",
        "receipt",
        "evaluator",
        "implementation",
        "scope",
        "verdict",
        "tolerance",
    ):
        assert forbidden not in params
    with pytest.raises(TypeError):
        verification_of(pair, evaluator=lambda a, b: "passed")


def test_r19_the_evaluator_resolves_from_the_frozen_spec_and_rule_bindings(pair):
    # A second conforming implementation held BESIDE the bound one changes
    # nothing: the binding froze before execution, and no selection argument
    # exists (computation §4.2a, 5b §6).
    beside = EquivalenceImplementation(identity="impl-eq-2", evaluate=lambda a, b: "failed", fixtures=())
    with_beside = verification_of(
        pair,
        held_rules={"impl-eq-1": CONTENT_EQUALITY, "impl-eq-2": beside},
    )
    without = verification_of(pair)
    assert with_beside.rule == "content-identity-equality/v1"
    assert with_beside.verdict == without.verdict == "passed"


def test_r19_the_assessment_edge_is_derived_never_authored(pair):
    # The assessment shape carries the verifies → assessment edge (§5.3), and
    # the constructor derives it from the original run's frozen records — no
    # authored argument exists for it.
    verification = verification_of(pair)
    assert isinstance(verification, AssessmentVerification)
    spec = freeze(spec_draft(), held_rules=spec_rules())
    original, _ = pair
    derived = v1.digest(
        "science.assessment.v1",
        {
            "spec": spec.identity,
            "run": original.run.address(),
            "proposition": spec.target,
        },
    )
    assert verification.assessment == derived
    assert verification.basis()["assessment"] == derived
    assert "assessment" not in inspect.signature(build_verification).parameters


def test_r19_a_mixed_shape_pair_is_refused(pair, production_pair):
    assessment_run, _ = pair
    production_run, _ = production_pair
    with pytest.raises(MixedShapes):
        build_verification(
            assessment_run.run,
            production_run.run,
            specs={},
            held_rules={},
            contract_identity="c",
            epoch="e",
        )


# --- R18 ----------------------------------------------------------------------
def test_r18_two_certifications_yield_two_verification_addresses(pair):
    a = verification_of(
        pair,
        certification=CodeLineageCertification(rationale="independent rewrite", attribution="alice"),
    )
    b = verification_of(
        pair,
        certification=CodeLineageCertification(rationale="clean-room port", attribution="bob"),
    )
    assert a.identity() != b.identity()


def test_r18_the_report_carries_the_evidence_inline_and_the_basis_names_it_once(pair):
    certification = CodeLineageCertification(rationale="independent rewrite", attribution="alice")
    certified = verification_of(pair, certification=certification)
    report = certified.report
    assert report.certification == certification
    original, replayed = pair
    assert report.original_conformance == report.replay_conformance == "conforming"
    assert report.receipts == (
        original.run.occurrence.receipt.identity(),
        replayed.run.occurrence.receipt.identity(),
    )
    assert report.receipts[0] != original.run.address()
    assert report.receipts[1] != replayed.run.address()
    assert report.rule_bindings == (("content-identity-equality/v1", "impl-eq-1"),)
    basis = certified.basis()
    assert basis["report"] == report.identity()
    assert "receipts" not in basis and "certification" not in basis


def test_r18_mutating_any_receipt_field_moves_receipt_report_and_verification(pair):
    from beliefs.verify import _mint_comparison_report, _mint_verification

    # Locked carriers refuse dataclasses.replace; these private mints are the
    # test scalpel, as fixtures use report._mint_report for ActReport values.
    original, _ = pair
    receipt = original.run.occurrence.receipt
    baseline = receipt.identity()
    verification = verification_of(pair)
    assert isinstance(verification, AssessmentVerification)
    report = verification.report
    for field, value in [
        ("scratch_mapping", "some-other-mount"),
        ("argv", ("snakemake", "--other")),
        ("rendered_config", (("alpha", "0.5"),)),
        ("capabilities", ("network-denied",)),
    ]:
        moved_receipt = dataclasses.replace(receipt, **{field: value}).identity()
        assert moved_receipt != baseline
        moved_report = _mint_comparison_report(
            original_conformance=report.original_conformance,
            replay_conformance=report.replay_conformance,
            receipts=(moved_receipt, report.receipts[1]),
            rule_bindings=report.rule_bindings,
            certification=report.certification,
            citation=report.citation,
            diagnostics=report.diagnostics,
        )
        assert moved_report.identity() != report.identity()
        moved_verification = _mint_verification(
            original=verification.original,
            replayed=verification.replayed,
            assessment=verification.assessment,
            rule=verification.rule,
            report=moved_report,
            scope_rule=verification.scope_rule,
            scope=verification.scope,
            verdict=verification.verdict,
            supersedes=verification.supersedes,
        )
        assert moved_verification.identity() != verification.identity()


def test_r19_only_build_verification_mints_the_carriers():
    import beliefs
    import beliefs.verify as verify_module

    assert "_mint_comparison_report" not in verify_module.__all__
    assert "_mint_verification" not in verify_module.__all__
    carrier_fields = (
        {field.name for field in dataclasses.fields(ComparisonReport)}
        | {field.name for field in dataclasses.fields(AssessmentVerification)}
        | {field.name for field in dataclasses.fields(DatasetProductionVerification)}
    )
    for name in verify_module.__all__:
        value = getattr(verify_module, name)
        if callable(value) and not isinstance(value, type) and name != "build_verification":
            params = set(inspect.signature(value).parameters)
            assert not (carrier_fields & params), name
    src = Path(beliefs.__file__).parent
    callers = [
        path.name for path in sorted(src.rglob("*.py")) if "_mint_verification" in path.read_text(encoding="utf-8")
    ]
    assert callers == ["verify.py"]

    with pytest.raises(TypeError):
        ComparisonReport(
            original_conformance="conforming",
            replay_conformance="conforming",
            receipts=("receipt-a", "receipt-b"),
            rule_bindings=(),
            certification=None,
            citation=None,
            diagnostics=(),
        )
    with pytest.raises(TypeError):
        AssessmentVerification(
            original="run-a",
            replayed="run-b",
            assessment="assessment-a",
            rule="rule-a",
            report=object(),
            scope_rule="scope-rule-a",
            scope="exact",
            verdict="passed",
        )
    with pytest.raises(TypeError):
        DatasetProductionVerification(
            original="run-a",
            replayed="run-b",
            rule="rule-a",
            report=object(),
            scope_rule="scope-rule-a",
            scope="exact",
            verdict="passed",
        )


def test_r18_deleting_the_external_certification_leaves_the_verification_unchanged(pair):
    external = {"cert-1": CodeLineageCertification(rationale="independent rewrite", attribution="alice")}
    verification = verification_of(pair, certification=external["cert-1"])
    frozen_identity = verification.identity()
    external.clear()
    assert verification.identity() == frozen_identity
    assert verification.report.certification is not None


def test_t6_r18_deleting_the_cited_report_leaves_the_verification_unchanged(pair):
    published = report()
    verification = verification_of(pair, citation=(published, 1))
    assert verification.report.citation is not None
    assert verification.report.citation.report_ref == published.identity()
    assert verification.report.citation.index == 1
    held = {published.identity(): published}
    frozen_identity = verification.identity()
    held.clear()
    assert verification.identity() == frozen_identity
    assert verification.report.citation.content


def test_t6_an_out_of_range_citation_is_refused_at_the_citing_site(pair):
    published = report()
    with pytest.raises(CitationRefused):
        verification_of(pair, citation=(published, 99))


# --- R11 ----------------------------------------------------------------------
def test_r11_a_tolerance_on_a_dataset_production_replay_is_refused(production_pair):
    # Two spellability routes, both absent: no tolerance argument exists on the
    # constructor, and no equivalence-rule member exists on a production recipe.
    assert "tolerance" not in inspect.signature(build_verification).parameters
    first, _ = production_pair
    assert first.run.recipe.spec_identity is None


def test_r11_a_nondeterministic_transform_yields_all_four(tmp_path):
    from test_belief import scenario as belief_scenario

    from beliefs.belief import evaluate

    belief_inputs = belief_scenario()
    prior_belief = evaluate(**belief_inputs)
    first = run_production(
        tmp_path / "a",
        snakefile=SNAKEFILE_NONDETERMINISTIC,
        nondeterminism=StochasticUnseeded(rationale="urandom transform"),
    )
    assert isinstance(first, RunMinted)
    first_dataset = mint_dataset(first.run, existing_bases={})
    # A separate ASSESSMENT run observes the first produced dataset — the
    # belief that must not move is a belief about THIS evidence:
    produced = Path(first.run.occurrence.receipt.execution.scratch_mapping) / "outputs" / "result.txt"
    observing_spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset=first_dataset.address),)),
        held_rules=spec_rules(),
    )
    observing = run_assessment(
        tmp_path / "obs",
        spec=observing_spec,
        held_inputs={first_dataset.address: produced},
    )
    assert isinstance(observing, RunMinted)
    prior = build_assessment(
        observing.run,
        specs={observing_spec.identity: observing_spec},
        implementations=interp(),
    )
    # Now replay the nondeterministic production run:
    second = replay_of(first, tmp_path / "b", snakefile=SNAKEFILE_NONDETERMINISTIC)
    assert isinstance(second, RunMinted)
    bases = {first_dataset.address: first_dataset.basis}
    second_dataset = mint_dataset(second.run, existing_bases=bases)
    assert second_dataset.address != first_dataset.address
    verification = build_verification(
        first.run,
        second.run,
        specs={},
        held_rules={"impl-dataset-eq-1": DATASET_CONTENT_EQUALITY},
        contract_identity="contract-1",
        epoch="epoch-1",
    )
    assert verification.verdict == "failed"
    assert verification.rule == "dataset-content-equality/v1"
    assert prior.run == observing.run.address()
    assert observing.run.recipe.inputs[0].dataset == first_dataset.address
    assert evaluate(**belief_inputs) == prior_belief


def test_r11_the_dataset_production_verification_carries_no_verifies_assessment_edge(
    production_pair,
):
    first, second = production_pair
    verification = build_verification(
        first.run,
        second.run,
        specs={},
        held_rules={"impl-dataset-eq-1": DATASET_CONTENT_EQUALITY},
        contract_identity="contract-1",
        epoch="epoch-1",
    )
    assert isinstance(verification, DatasetProductionVerification)
    assert "assessment" not in {f.name for f in dataclasses.fields(DatasetProductionVerification)}
    assert "assessment" not in verification.basis()


# --- R8 -----------------------------------------------------------------------
def test_r8_the_rule_cannot_be_chosen_after_the_outputs_are_seen(tmp_path):
    # A deterministic-declared spec over a byte-nondeterministic definition is
    # the honest way to obtain a failing replay on the minimal surface.
    spec = freeze(spec_draft(nondeterminism=Deterministic()), held_rules=spec_rules())
    original = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_NONDETERMINISTIC, spec=spec)
    replayed = replay_of(original, tmp_path / "b", snakefile=SNAKEFILE_NONDETERMINISTIC)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    failing = build_verification(
        original.run,
        replayed.run,
        specs={spec.identity: spec},
        held_rules={"impl-eq-1": CONTENT_EQUALITY},
        contract_identity="contract-1",
        epoch="epoch-1",
    )
    assert failing.verdict == "failed"
    rules = {
        **spec_rules(),
        "tolerance-1e-6/v1": spec_rules()["content-identity-equality/v1"],
    }
    successor = revise(
        spec,
        edits={"equivalence_rule": "tolerance-1e-6/v1"},
        held_rules=rules,
        recorded_failures=frozenset({spec.identity}),
    )
    assert successor.identity != spec.identity
    assert original.run.recipe.spec_identity == spec.identity
    assert successor.supersedes == spec.identity
    assert active_verifications((failing,)) == (failing,)


# --- K5: the admission join ---------------------------------------------------
def test_k5_admission_record_is_the_total_projection_of_a_derived_verification(pair):
    verification = verification_of(pair)
    record = admission_record(verification)
    assert record == Verification(
        ref=verification.identity(),
        assessment=verification.assessment,
        scope=verification.scope,
        verdict=verification.verdict,
        supersedes=None,
    )
    assert set(inspect.signature(admission_record).parameters) == {"derived"}


def test_k5_admission_record_carries_supersedes(pair):
    base = verification_of(pair)
    superseding = _mint_verification(
        original=base.original,
        replayed=base.replayed,
        assessment=base.assessment,
        rule=base.rule,
        report=base.report,
        scope_rule=base.scope_rule,
        scope=base.scope,
        verdict=base.verdict,
        supersedes=base.identity(),
    )
    assert isinstance(superseding, AssessmentVerification)
    assert admission_record(superseding).supersedes == base.identity()


def test_k5_a_production_verification_is_refused_by_the_join(production_pair):
    first, second = production_pair
    verification = build_verification(
        first.run,
        second.run,
        specs={},
        held_rules={"impl-dataset-eq-1": DATASET_CONTENT_EQUALITY},
        contract_identity="contract-1",
        epoch="epoch-1",
    )
    with pytest.raises(NotAnAssessmentVerification):
        admission_record(verification)  # pyright: ignore[reportArgumentType]
