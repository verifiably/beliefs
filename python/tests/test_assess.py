"""R22's in-cell arms and R7's constructor/admission halves.
Deferred: R22's unresolvable-rule clause (rules store), negative (b)'s
raw-write half and negative (c) (store, audit) — cut 3 §4.2.
"""

import dataclasses
import inspect
from types import SimpleNamespace

import pytest
from fixtures_cut3 import (
    DATA_ADDRESS,
    READS_ADDRESS,
    closure,
    closure_kwargs,
    interp,
    recipe,
    result_sensitive,
    runs_for,
    spec_draft,
    spec_rules,
)
from fixtures_cut3 import (
    memory_assessment as run_assessment,
)
from fixtures_cut3 import (
    memory_production as run_production,
)

from beliefs.admission import AdmissionRefused, admit
from beliefs.assess import AssessmentFinding, build_assessment, run_record
from beliefs.boundary import RunMinted
from beliefs.closure import build_closure
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import SignatureRefused
from beliefs.recipe import EnvironmentManifest, RecipeInput, project_recipe
from beliefs.record import AssessmentValue, RunValue
from beliefs.spec import (
    ExclusionCertification,
    RuleFixture,
    RuleImplementation,
    SpecInput,
    freeze,
    revise,
)
from beliefs.verification import Verification


def assessment_over(run: RunValue) -> AssessmentValue:
    return AssessmentValue(
        spec=run.spec,
        run=run.ref,
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="rule-1",
    )


def observations_for(run: RunValue) -> dict[str, tuple[ByteObservation, ...]]:
    observations = {}
    for run_input in run.inputs:
        address = dataset_address(run_input.dataset)
        assert address is not None
        observations[address] = tuple(
            ByteObservation(digest=resource.digest, location="repo://data")
            for resource in run_input.dataset.resources
            if resource.digest is not None
        )
    return observations


def admitting_for(run: RunValue) -> tuple[Verification, ...]:
    return (
        Verification(
            ref="v1",
            assessment=assessment_over(run).identity(),
            scope="clean-environment",
            verdict="passed",
        ),
    )


@pytest.fixture(scope="module")
def minted(tmp_path_factory):
    outcome = run_assessment(tmp_path_factory.mktemp("assess"))
    assert isinstance(outcome, RunMinted), outcome
    return outcome


def test_r22_the_constructor_takes_only_a_run_ref(minted):
    params = inspect.signature(build_assessment).parameters
    assert list(params) == ["run", "specs", "implementations"]
    assert not {
        "outcome",
        "estimate",
        "uncertainty",
        "estimand",
        "applicability",
        "interpretation_rule",
    } & set(params)


def test_r22_the_facet_derives_from_the_frozen_spec_and_the_manifest(minted):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    derived = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    assert isinstance(derived, AssessmentValue)
    assert derived.spec == spec.identity
    assert derived.proposition == spec.target
    assert derived.estimand == spec.estimand and derived.applicability == spec.applicability
    assert derived.interpretation_rule == spec.interpretation_rule
    assert derived.estimate == "0.4" and derived.uncertainty == "0.1"
    assert derived.outcome == "supported" and derived.run == minted.run.address()


def test_r22_the_evaluator_resolves_from_the_binding_frozen_in_the_recipe(minted):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    recipe_implementation = RuleImplementation(
        identity="impl-interp-2",
        evaluate=lambda manifest: {"outcome": "refuted"},
        fixtures=(),
    )
    bound_recipe = dataclasses.replace(
        minted.run.recipe,
        spec_identity=spec.identity,
        rule_bindings=tuple(
            (rule, "impl-interp-2" if rule == spec.interpretation_rule else identity)
            for rule, identity in spec.rule_bindings
        ),
    )
    synthetic = dataclasses.replace(minted.run, recipe=bound_recipe)
    derived = build_assessment(
        synthetic,
        specs={spec.identity: spec},
        implementations={**interp("supported"), "impl-interp-2": recipe_implementation},
    )
    assert isinstance(derived, AssessmentValue)
    assert derived.outcome == "refuted"
    assert derived.interpretation_rule == spec.interpretation_rule


def test_r22_a_spec_mapping_key_cannot_substitute_a_different_frozen_spec(minted):
    expected = freeze(spec_draft(), held_rules=spec_rules())
    assert minted.run.recipe.spec_identity == expected.identity
    substitutions = (
        freeze(spec_draft(target="a substituted proposition"), held_rules=spec_rules()),
        SimpleNamespace(
            identity=expected.identity,
            target="a forged proposition",
            interpretation_rule=expected.interpretation_rule,
            estimand=expected.estimand,
            applicability=expected.applicability,
        ),
    )

    for substituted in substitutions:
        finding = build_assessment(
            minted.run,
            specs={expected.identity: substituted},  # type: ignore[dict-item]
            implementations=interp(),
        )

        assert isinstance(finding, AssessmentFinding)
        assert finding.reason.startswith("evaluation-failed:")


@pytest.mark.parametrize(
    "implementation",
    [
        SimpleNamespace(
            identity="impl-interp-1",
            evaluate=lambda manifest: {"outcome": "supported"},
            fixtures=(),
        ),
        RuleImplementation(
            identity="impl-substituted",
            evaluate=lambda manifest: {"outcome": "supported"},
            fixtures=(),
        ),
        RuleImplementation(
            identity="impl-interp-1",
            evaluate=lambda manifest: {"outcome": "refuted"},
            fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
        ),
    ],
    ids=("forged-type", "mismatched-identity", "nonconforming-fixtures"),
)
def test_r22_an_implementation_mapping_key_cannot_substitute_unbound_content(minted, implementation):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    bound = dict(minted.run.recipe.rule_bindings)[spec.interpretation_rule]

    finding = build_assessment(
        minted.run,
        specs={spec.identity: spec},
        implementations={bound: implementation},  # type: ignore[dict-item]
    )

    assert isinstance(finding, AssessmentFinding)
    assert finding.reason.startswith("evaluation-failed:")


def test_r22_the_derived_outcome_moves_only_with_the_result_or_the_rule(tmp_path):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    first = run_assessment(tmp_path / "a", data="hello")
    assert isinstance(first, RunMinted)
    baseline = build_assessment(first.run, specs={spec.identity: spec}, implementations=result_sensitive())
    again = build_assessment(first.run, specs={spec.identity: spec}, implementations=result_sensitive())
    assert isinstance(baseline, AssessmentValue) and isinstance(again, AssessmentValue)
    assert baseline == again  # same run, same rule: byte-identical facet
    # Same rule, changed RESULT: pick fixture bytes whose output-digest parity
    # differs from the first run's, so the derived outcome provably flips.
    first_parity = int(first.run.result.outputs[0][1].split(":", 1)[1], 16) % 2
    for candidate in ("hello-1", "hello-2", "hello-3", "hello-4", "hello-5"):
        other = run_assessment(tmp_path / candidate, data=candidate)
        assert isinstance(other, RunMinted)
        if int(other.run.result.outputs[0][1].split(":", 1)[1], 16) % 2 != first_parity:
            break
    else:
        pytest.fail("no candidate flipped the output-digest parity — widen the list")
    flipped = build_assessment(other.run, specs={spec.identity: spec}, implementations=result_sensitive())
    assert isinstance(flipped, AssessmentValue)
    assert {baseline.outcome, flipped.outcome} == {"supported", "refuted"}
    # Same RESULT, changed rule: a successor spec freezing the inverted rule
    # derives the other outcome over byte-identical result bytes.
    inverted = RuleImplementation(
        identity="impl-interp-2",
        evaluate=lambda manifest: {
            "outcome": ("refuted" if int(manifest.outputs[0][1].split(":", 1)[1], 16) % 2 == 0 else "supported"),
            "estimate": "0.4",
        },
        fixtures=(),
    )
    successor = revise(
        spec,
        edits={"interpretation_rule": "inverted-parity/v1"},
        held_rules={**spec_rules(), "inverted-parity/v1": inverted},
        recorded_failures=frozenset(),
    )
    rerun = run_assessment(tmp_path / "rerun", spec=successor, data="hello")
    assert isinstance(rerun, RunMinted)
    assert rerun.run.result == first.run.result  # the same result bytes…
    rederived = build_assessment(
        rerun.run,
        specs={successor.identity: successor},
        implementations={"impl-interp-2": inverted},
    )
    assert isinstance(rederived, AssessmentValue)
    assert rederived.outcome != baseline.outcome  # …and the rule alone moved the outcome
    # No API path produces an assessment carrying the un-derived outcome:
    assert "outcome" not in inspect.signature(build_assessment).parameters


def test_r22_a_failing_evaluator_produces_a_finding_never_inconclusive(minted):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    finding = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp(fail=True))
    assert isinstance(finding, AssessmentFinding)
    assert "inconclusive" not in finding.reason  # machinery failure is not a scientific outcome


def test_r22_assessment_findings_are_immutable():
    finding = AssessmentFinding(run="run-1", reason="unparseable payload")
    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.reason = "changed"  # type: ignore[misc]


def test_r22_negative_a_narrowing_applicability_needs_a_successor_spec_and_a_new_run(
    minted,
):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    narrowed = revise(
        spec,
        edits={"applicability": "a narrower population"},
        held_rules=spec_rules(),
        recorded_failures=frozenset(),
    )
    assert narrowed.identity != spec.identity
    assert minted.run.recipe.spec_identity == spec.identity  # the recorded run stays attached
    derived = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    assert isinstance(derived, AssessmentValue)
    assert derived.applicability == spec.applicability  # never the successor's


def test_r22_negative_b_exchanged_facets_move_the_belief_digest(minted, tmp_path):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    other = run_assessment(tmp_path, data="different bytes")
    assert isinstance(other, RunMinted)
    a = build_assessment(
        minted.run,
        specs={spec.identity: spec},
        implementations=interp("supported"),
    )
    b = build_assessment(other.run, specs={spec.identity: spec}, implementations=interp("refuted"))
    assert isinstance(a, AssessmentValue) and isinstance(b, AssessmentValue)
    exchanged_a = dataclasses.replace(a, outcome=b.outcome)
    exchanged_b = dataclasses.replace(b, outcome=a.outcome)
    straight = build_closure(**closure_kwargs((a, b), runs_for((minted.run, other.run)))).digest()
    crossed = build_closure(**closure_kwargs((exchanged_a, exchanged_b), runs_for((minted.run, other.run)))).digest()
    bags = (
        sorted(value.facet_digest() for value in (a, b)),
        sorted(value.facet_digest() for value in (exchanged_a, exchanged_b)),
    )
    assert bags[0] == bags[1]  # the bag of facet digests is identical…
    assert straight != crossed  # …and the keyed pairing still moves the digest (cut 2's member)


def test_r22_the_reach_arm_an_inline_exclusion_moves_the_digest_with_identical_facets(
    tmp_path,
):
    # Two FROZEN SPECS differing only in the reads entry's inline exclusion
    # certification, both executed for real: byte-identical facet values, a
    # differing belief digest — and editing the certification alone mints a
    # recipe (a description), never a run.
    observes = SpecInput(role="observes", dataset=DATA_ADDRESS)
    certified_spec = freeze(
        spec_draft(
            input_roles=(
                observes,
                SpecInput(
                    role="reads",
                    dataset=READS_ADDRESS,
                    exclusion=ExclusionCertification(rationale="plotting palette", attribution="tester"),
                ),
            )
        ),
        held_rules=spec_rules(),
    )
    plain_spec = freeze(
        spec_draft(input_roles=(observes, SpecInput(role="reads", dataset=READS_ADDRESS))),
        held_rules=spec_rules(),
    )
    certified_run = run_assessment(tmp_path / "certified", spec=certified_spec)
    plain_run = run_assessment(tmp_path / "plain", spec=plain_spec)
    assert isinstance(certified_run, RunMinted) and isinstance(plain_run, RunMinted)
    assert certified_run.run.recipe.inputs[1].exclusion is not None
    a = build_assessment(
        certified_run.run,
        specs={certified_spec.identity: certified_spec},
        implementations=interp(),
    )
    b = build_assessment(
        plain_run.run,
        specs={plain_spec.identity: plain_spec},
        implementations=interp(),
    )
    assert isinstance(a, AssessmentValue) and isinstance(b, AssessmentValue)
    assert a.facet_digest() == b.facet_digest()  # byte-identical derived facet values
    # Reach ISOLATION: derive a controlled pair sharing one spec identity,
    # result and occurrence. Their recipes differ only in the reads exclusion,
    # whose path is recipe → run address → assessment identity → belief digest.
    isolated_plain = plain_run.run
    isolated_certified = dataclasses.replace(
        isolated_plain,
        recipe=dataclasses.replace(
            isolated_plain.recipe,
            inputs=tuple(
                dataclasses.replace(
                    entry,
                    exclusion=ExclusionCertification(rationale="plotting palette", attribution="tester"),
                )
                if entry.role == "reads"
                else entry
                for entry in isolated_plain.recipe.inputs
            ),
        ),
    )
    assert isolated_certified.recipe.spec_identity == isolated_plain.recipe.spec_identity
    assert isolated_certified.result == isolated_plain.result
    assert isolated_certified.occurrence == isolated_plain.occurrence
    reach_certified = build_assessment(
        isolated_certified,
        specs={plain_spec.identity: plain_spec},
        implementations=interp(),
    )
    reach_plain = build_assessment(
        isolated_plain,
        specs={plain_spec.identity: plain_spec},
        implementations=interp(),
    )
    assert isinstance(reach_certified, AssessmentValue)
    assert isinstance(reach_plain, AssessmentValue)
    assert reach_certified.facet_digest() == reach_plain.facet_digest()
    assert reach_certified.identity() != reach_plain.identity()
    assert (
        build_closure(**closure_kwargs((reach_certified,), runs_for((isolated_certified,)))).digest()
        != build_closure(**closure_kwargs((reach_plain,), runs_for((isolated_plain,)))).digest()
    )
    # Editing the certification alone re-projects to exactly the other spec's
    # recipe — a different description, and no run until executed:
    assert isinstance(certified_run.run.recipe.environment, EnvironmentManifest)
    reprojected = project_recipe(
        plain_spec,
        held={entry.dataset: entry.content for entry in plain_run.run.recipe.inputs},
        code_identity=certified_run.run.recipe.code_identity,
        environment=certified_run.run.recipe.environment,
        workflow_definition=certified_run.run.recipe.workflow_definition,
        invocation=certified_run.run.recipe.invocation,
        boundary_policy=certified_run.run.recipe.boundary_policy,
    )
    assert reprojected.identity() == plain_run.run.recipe.identity()  # the same description…
    assert reprojected.identity() != certified_run.run.recipe.identity()
    assert not hasattr(reprojected, "address")  # and only executing mints a run


def test_r7_a_dataset_production_run_with_an_assesses_descendant_is_refused(tmp_path):
    outcome = run_production(tmp_path)
    assert isinstance(outcome, RunMinted)
    with pytest.raises(SignatureRefused):
        build_assessment(outcome.run, specs={}, implementations={})


def test_r7_zero_observes_inputs_admit_nothing_at_any_quantity_of_reads():
    reads = tuple(
        RecipeInput(
            role="reads",
            dataset=f"dataset:r{i}",
            content="sha256:" + f"{i:02x}" * 32,
        )
        for i in range(1, 6)
    )
    run = closure(recipe=recipe(inputs=reads))
    bridged = run_record(run)
    verdict = admit(
        assessment_over(bridged),
        bridged,
        observations_for(bridged),
        admitting_for(bridged),
    )
    assert isinstance(verdict, AdmissionRefused)
    assert verdict.reason.startswith("no-observes-input")
