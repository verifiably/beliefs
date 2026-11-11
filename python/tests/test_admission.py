"""The assessment admission gate, over constructed records.

And one further case: a dataset identified whose bytes are not held here
resolves `not-available` — derived from the admission state — and is never
reported as `not-present` (world-index territory) nor as `not-member` (a
finding nobody's look supports).
"""

import pytest
from fixtures_cut3 import TESTING_PROFILE, dependency_evidence, typed_applicability, typed_estimand, typed_target

from beliefs.admission import AdmissionRefused, Admitted, admit, vocabulary_availability
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.verification import Verification

D1 = "sha256:" + "11" * 32
D2 = "sha256:" + "22" * 32


def dataset(digest: str | None = D1) -> DatasetDeclaration:
    return DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=digest),))


def run(*inputs: RunInput) -> RunValue:
    return RunValue(ref="run:run-1", spec="spec-1", inputs=inputs)


def assessment() -> AssessmentValue:
    return AssessmentValue(
        spec="spec-1",
        run="run-1",
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="rule-1",
        target=typed_target(estimand=typed_estimand(), applicability=typed_applicability()),
    )


def held(*declarations: DatasetDeclaration) -> dict[str, tuple[ByteObservation, ...]]:
    table = {}
    for declaration in declarations:
        address = dataset_address(declaration)
        assert address is not None
        table[address] = tuple(
            ByteObservation(digest=r.digest, location="repo://data") for r in declaration.resources if r.digest
        )
    return table


ADMITTING = (Verification(ref="v1", assessment=assessment().identity(), scope="clean-environment", verdict="passed"),)


class TestHeldObservesInputs:
    def test_a_held_observes_input_admits(self):
        d = dataset()
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d)),
            held(d),
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, Admitted)

    def test_a_declared_input_is_refused(self):
        d = dataset()
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d)),
            {},
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")

    def test_a_curation_note_input_is_refused(self):
        # "so is one whose input carries no digest" — the no-digest case.
        d = dataset(digest=None)
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d)),
            {},
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")

    def test_every_input_must_be_held_not_only_observes(self):
        d, aux = dataset(), dataset(digest=D2)
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d), RunInput(role="reads", dataset=aux)),
            held(d),
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")


class TestReadsOnlyInputs:
    def test_reads_only_inputs_admit_nothing(self):
        # A literature corpus and an ontology, both held, in any quantity.
        corpus, ontology = dataset(), dataset(digest=D2)
        result = admit(
            assessment(),
            run(RunInput(role="reads", dataset=corpus), RunInput(role="reads", dataset=ontology)),
            held(corpus, ontology),
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("no-observes-input")

    def test_qa_state_does_not_rescue_it(self):
        # Regardless of verification state: the gate refuses before reading it.
        corpus = dataset()
        result = admit(
            assessment(),
            run(RunInput(role="reads", dataset=corpus)),
            held(corpus),
            ADMITTING,
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("no-observes-input")


class TestTheGateReadsItsArguments:
    def test_a_run_that_is_not_the_assessments_run_is_refused(self):
        d = dataset()
        other = RunValue(ref="run:run-2", spec="spec-1", inputs=(RunInput(role="observes", dataset=d),))
        result = admit(assessment(), other, held(d), ADMITTING, dependencies=dependency_evidence((assessment(),)))
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("run-mismatch")

    def test_the_verification_state_gates_last(self):
        d = dataset()
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d)),
            held(d),
            (),
            dependencies=dependency_evidence((assessment(),)),
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("not-admitted-verification-state")


class TestNotAvailableIsDerived:
    def test_an_unheld_vocabulary_dataset_reads_not_available(self):
        sort = TESTING_PROFILE.sorts["testing/entity"]
        readable, _members = vocabulary_availability(dataset(), (), members=("EX:term-1",))
        assert not readable
        snapshot = build_snapshot(unreadable=[sort.binding])
        outcome = snapshot.resolve(sort, "EX:term-1")
        assert outcome is TermOutcome.NOT_AVAILABLE
        assert outcome is not TermOutcome.NOT_PRESENT
        # The named clause of the five-way arm: never reported as a membership
        # finding — the term IS in the vocabulary nobody could read.
        assert outcome is not TermOutcome.NOT_MEMBER
        assert not outcome.refuses

    def test_a_held_vocabulary_dataset_reads_its_members(self):
        d = dataset()
        obs = tuple(ByteObservation(digest=r.digest, location="repo://v") for r in d.resources if r.digest)
        readable, members = vocabulary_availability(d, obs, members=("EX:term-1",))
        assert readable and members == ("EX:term-1",)


# --- admit resolves the bare run through the typed ref ------
def test_admit_matches_a_typed_run_ref_to_the_bare_member():
    from beliefs.admission import AdmissionRefused, admit
    from beliefs.record import AssessmentValue, RunValue

    assessment = AssessmentValue(
        spec="s",
        run="r1",
        proposition="p",
        outcome="supported",
        interpretation_rule="rule-1",
        target=typed_target(estimand=typed_estimand(), applicability=typed_applicability()),
    )
    other = RunValue(ref="run:r2", spec="s", inputs=())
    refused = admit(assessment, other, {}, (), dependencies=dependency_evidence((assessment,)))
    assert isinstance(refused, AdmissionRefused) and refused.reason.startswith("run-mismatch")
    same = RunValue(ref="run:r1", spec="s", inputs=())
    refused = admit(assessment, same, {}, (), dependencies=dependency_evidence((assessment,)))
    assert isinstance(refused, AdmissionRefused) and refused.reason.startswith("no-observes-input")


def test_model_without_observes_and_missing_model_input(tmp_path):
    from dataclasses import replace

    from fixtures_cut3 import freeze_context, spec_draft, spec_rules, typed_estimand
    from fixtures_cut4 import raw_write, reopen
    from test_evaluation import PROPOSITION_REF, _fixture
    from test_standing import model_context

    from beliefs import stored
    from beliefs.belief import Belief
    from beliefs.claim import Referent, build_claim
    from beliefs.evaluation import evaluate_over, gather
    from beliefs.lineage import LineageSnapshot
    from beliefs.procedure import ModelInputs, procedure_from_stored
    from beliefs.projection import project_claim
    from beliefs.spec import freeze

    fixture = _fixture(tmp_path, PROPOSITION_REF)
    records, model, claim = model_context()
    code, data = "sha256:" + "d" * 64, "sha256:" + "c" * 64
    model = stored.procedure_node(replace(procedure_from_stored(model), inputs=ModelInputs((data,), (code,))))
    records.nodes[model.id] = model
    claim = build_claim(
        TESTING_PROFILE,
        operator=claim.operator,
        roles={**claim.roles, "within-model": Referent("testing/procedure-spec", model.id)},
        layer=claim.layer,
        polarity=claim.polarity,
    )
    spec = freeze(
        spec_draft(
            target="proposition:model",
            standing="model",
            model=model.id,
            input_roles=(),
            estimand=typed_estimand(claim=claim, records=records),
        ),
        held_rules=spec_rules(),
        **{**freeze_context(), "records": records, "claim": claim},
    )
    for node in records.nodes.values():
        if not fixture.view.holds(node.id):
            raw_write(tmp_path, node)
    a_node = stored.assessment_node(
        "model",
        title="model",
        spec=spec.identity,
        run="run:model",
        proposition="proposition:model",
        outcome="supported",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
    )
    a = stored.assessment_value(a_node, profile=TESTING_PROFILE)
    for node in (
        stored.proposition_node("model", title="model", claim=project_claim(claim)),
        stored.run_node("model", title="model", spec=spec.identity),
        a_node,
        stored.verification_node(
            "model",
            title="model",
            assessment=a.identity(),
            assessment_ref=a_node.id,
            scope="clean-environment",
            verdict="passed",
        ),
    ):
        raw_write(tmp_path, node)
    view = reopen(tmp_path)
    observations = {"model inputs": (ByteObservation(data, "repo://model"), ByteObservation(code, "repo://code"))}
    context = replace(fixture.context, snapshot=LineageSnapshot(tuple(sorted((model.id, code, data))), {}, {}))
    inputs = gather(
        view, a.proposition, key=a.key(), observations=observations, **{**fixture.gather_kwargs, "context": context}
    )
    assert isinstance(admit(a, inputs.runs[a.run], observations, inputs.verifications, inputs.dependencies), Admitted)
    answer = evaluate_over(
        view,
        a.proposition,
        **{
            **fixture.kwargs,
            "context": context,
            "availability": replace(fixture.availability, observations=observations),
        },
    )
    assert isinstance(answer, Belief), answer
    unheld = {"model inputs": observations["model inputs"][:1]}
    missing = gather(
        view, a.proposition, key=a.key(), observations=unheld, **{**fixture.gather_kwargs, "context": context}
    )
    refused = admit(a, missing.runs[a.run], unheld, missing.verifications, missing.dependencies)
    assert isinstance(refused, AdmissionRefused) and refused.reason.startswith("model-not-held")
    refused_answer = evaluate_over(
        view,
        a.proposition,
        **{**fixture.kwargs, "context": context, "availability": replace(fixture.availability, observations=unheld)},
    )
    from beliefs.belief import NoBelief

    assert isinstance(refused_answer, NoBelief)
    assert refused_answer.reason == "no-eligible-assessment"


@pytest.mark.parametrize("standing", ["empirical", "model", "calibrated-model"])
def test_all_routes_require_every_run_input_held(standing):
    from dataclasses import replace

    from fixtures_cut3 import YIELDING_PROCEDURE

    value = assessment()
    if standing != "empirical":
        value = replace(value, target=replace(value.target, standing=standing, model=YIELDING_PROCEDURE))
    observed, read = dataset(), dataset(D2)
    execution = run(RunInput("observes", observed), RunInput("reads", read))
    result = admit(value, execution, held(observed), ADMITTING, dependency_evidence((value,)))
    assert isinstance(result, AdmissionRefused) and result.reason.startswith("input-not-held")
