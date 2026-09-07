"""Step 8: store the verification, admit, and evaluate over the corpus.

Same path, both times: step 8 evaluates through `evaluation.evaluate_over`,
and step 10a calls the same function in a fresh process. The verification
names the derived assessment identity `admission_record` gives it,
unaltered; whether admission over the corpus accepts it is measured.
"""

from __future__ import annotations

import sys

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.dataset import ByteObservation
from beliefs.evaluation import evaluate_over, gather
from beliefs.holdings.records import Found
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, admission_record, build_verification, publication_node
from reproduction import answers, findings, spec, state, vocabulary, world

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


def observations_from_corpus(view: ReadView) -> dict[str, tuple[ByteObservation, ...]]:
    """Every stored holdings observation with a Found outcome, keyed by the
    dataset address it satisfies. Corpus evidence, not a sidecar. The holdings
    reduction rule (supersession, coverage) is not applied: one observation,
    no history — stated in the record."""
    st = state.load()
    found = []
    for node in view.iter_stored():
        if node.kind == "holdings-observation":
            value = stored.holdings_observation_value(node)
            if isinstance(value.outcome, Found):
                found.append(ByteObservation(digest=value.outcome.digest, location=value.location.canonical()))
    return {st["dataset_address"]: tuple(found)}


def context(view: ReadView) -> SuppliedContext:
    st = state.load()
    return SuppliedContext(
        snapshot=lineage_snapshot(view, [st["dataset_address"]]),
        producer_snapshot_identity="no-epoch-published",  # supplied: this exercise builds no epoch (record §3)
        retractions=RetractionEnumeration(found=(), coverage=(st["corpus_id"],)),
        node_corpus={st["assessment_identity_stored"]: st["corpus_id"]},
        pins={st["corpus_id"]: world.open_writer().manifest_pins()},
    )


def availability(view: ReadView) -> Availability:
    return Availability(
        observations=observations_from_corpus(view),
        implementations={BELIEF_V1.identity: BELIEF_V1},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )


def evaluate_here(view: ReadView):
    return evaluate_over(
        view,
        state.load()["proposition_ref"],
        availability=availability(view),
        context=context(view),
        profile=vocabulary.profile(),
        resolution=vocabulary.snapshot(),
        binding=BINDING,
    )


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    original = decode_run_closure(view.get(st["original_run_ref"]))
    replayed = decode_run_closure(view.get(st["replayed_run_ref"]))
    frozen = spec.frozen()
    verification = build_verification(
        original,
        replayed,
        specs={frozen.identity: frozen},
        held_rules={spec.equivalence().identity: spec.equivalence()},
        contract_identity=writer.manifest_pins().science_contract,
        epoch="none-published",
    )
    assert isinstance(verification, AssessmentVerification)
    record = admission_record(verification)
    if record.assessment != st["assessment_identity_derived"]:
        findings.record(
            8,
            "defect",
            f"admission_record names {record.assessment}, not the derived identity {st['assessment_identity_derived']}",
        )
    minted = writer.add(publication_node(verification, assessment_ref=st["assessment_ref"]))
    view = world.open_writer().read_view
    inputs = gather(
        view,
        st["proposition_ref"],
        context=context(view),
        profile=vocabulary.profile(),
        resolution=vocabulary.snapshot(),
        binding=BINDING,
    )
    if len(inputs.assessments) != 1 or inputs.assessments[0].run not in inputs.runs:
        findings.record(
            8,
            "design-gap",
            f"gather matched {len(inputs.assessments)} assessments for {st['proposition_ref']} "
            f"with runs {sorted(inputs.runs)}; the spec target / stored proposition ref do not meet",
        )
        state.save(
            verification_ref=minted.id, admission="not-evaluated: gather mismatch", belief_answer={"kind": "not-evaluated"}
        )
        return 2
    a = inputs.assessments[0]
    verdict = admit(a, inputs.runs[a.run], observations_from_corpus(view), inputs.verifications)
    admission = "Admitted" if isinstance(verdict, Admitted) else f"AdmissionRefused: {verdict.reason}"
    if (
        not isinstance(verdict, Admitted)
        and verdict.reason.startswith("not-admitted-verification-state")
        and record.assessment != a.identity()
        and record.scope == "clean-environment"
        and record.verdict == "passed"
    ):
        findings.record(
            8,
            "design-gap",
            f"a clean-environment pass was refused at admission: the verification names the derived identity "
            f"{record.assessment} and the gathered assessment carries {a.identity()}; the audit accepts only the former",
            filed="assessment/run-record design (one spelling for the run member)",
        )
    answer = answers.payload(evaluate_here(view))
    if answer["kind"] == "Refused":
        findings.record(8, "design-gap", f"evaluate refused: {answer['reason']}")
    state.save(verification_ref=minted.id, admission=admission, belief_answer=answer)
    print(f"admission {admission}; answer {answer}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
