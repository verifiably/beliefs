"""The assessment admission gate: G2b and G6, over constructed records.

And D3's one further arm: a dataset identified whose bytes are not held here
resolves `not-available` — derived from the admission state — and is never
reported as `not-present` (world-index territory) nor as `not-member` (a
finding nobody's look supports).
"""

from beliefs.admission import AdmissionRefused, Admitted, admit, vocabulary_availability
from beliefs.contract.domain import VocabularyBinding
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
        spec="spec-1", run="run-1", proposition="prop-1", outcome="supported", interpretation_rule="rule-1"
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


class TestG2b:
    def test_a_held_observes_input_admits(self):
        d = dataset()
        result = admit(assessment(), run(RunInput(role="observes", dataset=d)), held(d), ADMITTING)
        assert isinstance(result, Admitted)

    def test_a_declared_input_is_refused(self):
        d = dataset()
        result = admit(assessment(), run(RunInput(role="observes", dataset=d)), {}, ADMITTING)
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")

    def test_a_curation_note_input_is_refused(self):
        # "so is one whose input carries no digest" — the no-digest case.
        d = dataset(digest=None)
        result = admit(assessment(), run(RunInput(role="observes", dataset=d)), {}, ADMITTING)
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")

    def test_every_input_must_be_held_not_only_observes(self):
        d, aux = dataset(), dataset(digest=D2)
        result = admit(
            assessment(),
            run(RunInput(role="observes", dataset=d), RunInput(role="reads", dataset=aux)),
            held(d),
            ADMITTING,
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("input-not-held")


class TestG6:
    def test_reads_only_inputs_admit_nothing(self):
        # A literature corpus and an ontology, both held, in any quantity.
        corpus, ontology = dataset(), dataset(digest=D2)
        result = admit(
            assessment(),
            run(RunInput(role="reads", dataset=corpus), RunInput(role="reads", dataset=ontology)),
            held(corpus, ontology),
            ADMITTING,
        )
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("no-observes-input")

    def test_qa_state_does_not_rescue_it(self):
        # Regardless of verification state: the gate refuses before reading it.
        corpus = dataset()
        result = admit(assessment(), run(RunInput(role="reads", dataset=corpus)), held(corpus), ADMITTING)
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("no-observes-input")


class TestTheGateReadsItsArguments:
    def test_a_run_that_is_not_the_assessments_run_is_refused(self):
        d = dataset()
        other = RunValue(ref="run:run-2", spec="spec-1", inputs=(RunInput(role="observes", dataset=d),))
        result = admit(assessment(), other, held(d), ADMITTING)
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("run-mismatch")

    def test_the_verification_state_gates_last(self):
        d = dataset()
        result = admit(assessment(), run(RunInput(role="observes", dataset=d)), held(d), ())
        assert isinstance(result, AdmissionRefused)
        assert result.reason.startswith("not-admitted-verification-state")


class TestD3NotAvailableIsDerived:
    def test_an_unheld_vocabulary_dataset_reads_not_available(self):
        binding = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
        readable, _members = vocabulary_availability(dataset(), (), members=("EX:term-1",))
        assert not readable
        snapshot = build_snapshot(unreadable=[binding])
        outcome = snapshot.resolve(binding, "EX:term-1")
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


# --- V2: admit resolves the bare run through the typed ref (design §3.2) ------
def test_v2_admit_matches_a_typed_run_ref_to_the_bare_member():
    from beliefs.admission import AdmissionRefused, admit
    from beliefs.record import AssessmentValue, RunValue

    assessment = AssessmentValue(spec="s", run="r1", proposition="p", outcome="supported", interpretation_rule="rule-1")
    other = RunValue(ref="run:r2", spec="s", inputs=())
    refused = admit(assessment, other, {}, ())
    assert isinstance(refused, AdmissionRefused) and refused.reason.startswith("run-mismatch")
    same = RunValue(ref="run:r1", spec="s", inputs=())
    assert admit(assessment, same, {}, ()).reason.startswith("no-observes-input")  # type: ignore[union-attr]
