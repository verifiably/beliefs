"""Steps 10a/10b/10c, in a fresh process. Every input is labelled corpus / supplied / in-process.

10a's inputs: the corpus (assessment, run, dataset, verification, claim,
holdings observation) plus *supplied* context (producer snapshot identity,
retraction enumeration) plus *in-process* profile and binding. 10b's: the
corpus (verification record, two run publications, analysis-spec record)
plus *in-process* interpretation and equivalence rule implementations — the
only thing no kernel reader restores from a record.

10c is Q10's own arm: the frozen spec and the assessment restored from the
records on disk through the typed readers, the assessment re-derived from its
run and the belief from its closure, both compared with what the driver's
process derived — and then the **prior** corpus state, opened read-only under
the successor profile, which no successor reader accepts.
"""

from __future__ import annotations

import json
import sys

from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.audit import audit_corpus, check_verification
from beliefs.corpus import ReadView
from beliefs.errors import MalformedRecord, PreGrammarAssessment, PreGrammarSpec, RecordError
from beliefs.evidence import DerivationEvidence
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification, decode_verification
from reproduction import answers, belief, close, findings, paths, spec, state, world
from reproduction.vocabulary import profile


def reconstruct(view, st: dict, evidence: DerivationEvidence) -> dict:
    """10b, field by field, each labelled. Reads the verification record, the
    two run publications and the spec record; recomputes only through
    `evidence`, which names no in-process spec."""
    node = view.get(st["verification_ref"])
    stored_value = stored.verification_value(node)
    decoded = decode_verification(node)
    report: dict = {
        "inputs": {
            "corpus": ["verification record (basis, comparison report, scope, verdict read)", "two run publications", "analysis-spec record"],
            "in_process": ["interpretation and equivalence RuleImplementations"],
        },
        "comparison_report_stored": decoded is not None,
        "derivation_named": False,
        "closures_decoded": False,
        "scope_recomputed": None,
        "scope_equal": None,
        "verdict_recomputed": None,
        "verdict_equal": None,
        "report_identity_equal": None,
        "spec_restored_identity_matches_run": None,
        "audit_check": None,
    }
    if decoded is not None:
        report["scope_read"], report["verdict_read"], report["report_identity_read"] = decoded.scope, decoded.verdict, decoded.report.identity()
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        certification = None if decoded is None else decoded.report.certification
        scope = derive_scope(original, replayed, certification=certification)
        report["scope_recomputed"], report["scope_equal"] = scope, scope == stored_value.scope
        rebuilt = build_verification(
            original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
            contract_identity="none-consulted", epoch="none-published", certification=certification,
        )
        if isinstance(rebuilt, AssessmentVerification):
            report["verdict_recomputed"], report["verdict_equal"] = rebuilt.verdict, rebuilt.verdict == stored_value.verdict
            if decoded is not None:
                report["report_identity_equal"] = rebuilt.report.identity() == decoded.report.identity()
        if view.holds(st["spec_ref"]):
            restored = stored.analysis_spec_value(view.get(st["spec_ref"]), profile=profile())
            report["spec_restored_identity_matches_run"] = restored.identity == original.recipe.spec_identity
    outcome = check_verification(view, node, evidence=evidence)
    report["audit_check"] = {
        "checked": outcome.checked,
        "reason": outcome.reason,
        "contradiction": None if outcome.contradiction is None else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail},
    }
    return report


def restored(view, st: dict, *, belief_equal: bool, prior_pre_grammar: bool) -> dict:
    """10c. The spec and the assessment come off disk through the typed
    readers; the assessment is re-derived from its run and the belief from its
    closure; each is compared with what the driver's process derived. Nothing
    in this process was carried over from the driver's except the rule
    implementations, which no reader restores from a record. The fourth key
    cut 31 §5 names, `prior_pre_grammar`, travels with them so all four are
    read by name from one mapping."""
    frozen = stored.analysis_spec_value(view.get(st["spec_ref"]), profile=profile())
    value = stored.assessment_value(view.get(st["assessment_ref"]), profile=profile())
    rebuilt = build_assessment(
        decode_run_closure(view.get(st["original_run_ref"])),
        specs={frozen.identity: frozen},
        implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION},
    )
    return {
        "spec_restored": frozen.identity == st["spec_identity"],
        "assessment_restored": value.identity() == st["assessment_identity_stored"],
        "assessment_equal": (
            not isinstance(rebuilt, AssessmentFinding) and rebuilt.identity() == st["assessment_identity_derived"]
        ),
        "belief_equal": belief_equal,
        "prior_pre_grammar": prior_pre_grammar,
    }


def _answer(read) -> tuple[str, str]:
    """What a successor reader answers over one prior-corpus record: the
    refusal's class and its text, or an empty class when it returns a typed
    value — the one answer the transition rules out. Which refusal arrives is
    measured, not assumed."""
    try:
        read()
    except RecordError as refusal:
        return type(refusal).__name__, f"{type(refusal).__name__}: {refusal}"
    return "", "returned a typed value: the successor reader did not refuse"


def _prior_node(view: ReadView, ref: str) -> Node:
    """One stored node of the prior corpus, through `iter_stored`. Not
    `view.get`: that validates the base pin and refuses this whole corpus
    before any record is reached, while `iter_stored` yields store nodes
    unvalidated — the route `audit_corpus` itself takes, and the one that puts
    the record in front of its reader."""
    for node in view.iter_stored():
        if node.id == ref:
            return node
    raise RuntimeError(f"the prior corpus state holds no stored node {ref}")


def prior_state() -> dict:
    """10c's transition arm: the prior corpus state, read-only, under the
    successor profile. Its base contract predates the grammar, so
    `audit_corpus`'s profile-disagreement rule fires before any record is read;
    the two record readers are handed their nodes directly and answer by
    name."""
    root = paths.PRIOR
    if not (root / "corpus" / "corpus.yaml").is_file():
        raise RuntimeError(
            f"the prior corpus state is not at {root.name}; it is moved aside, never deleted, when the corpus is "
            "recreated under the successor contracts (estimand-typing decision 10)"
        )
    prior = json.loads((root / "state.json").read_text())
    view = ReadView.opened_at(root / "corpus")
    spec_class, spec_answer = _answer(
        lambda: stored.analysis_spec_value(_prior_node(view, prior["spec_ref"]), profile=profile())
    )
    assessment_class, assessment_answer = _answer(
        lambda: stored.assessment_value(_prior_node(view, prior["assessment_ref"]), profile=profile())
    )
    evidence = DerivationEvidence(
        specs={},
        held_rules={spec.EQUIVALENCE.identity: spec.EQUIVALENCE},
        implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION},
    )
    audit = [f"{f.code}: {f.detail}" for f in audit_corpus(view, evidence=evidence, profile=profile())]
    report: dict[str, object] = {
        "spec": spec_answer,
        "spec_refusal": spec_class,
        "assessment": assessment_answer,
        "assessment_refusal": assessment_class,
        "audit": audit,
        "spec_ref": prior["spec_ref"],
        "assessment_ref": prior["assessment_ref"],
        # Cited as text. The re-authored spec carries no `supersedes` edge to
        # it (design §9): it lives in the prior corpus state, not in this
        # lineage.
        "spec_prose_identity": prior["spec_identity"],
    }
    # Cut 31 §5's fourth key: the assessment refuses by its own pre-grammar
    # name, the spec returns no typed value, and the audit reports exactly the
    # one profile disagreement.
    report["prior_pre_grammar"] = (
        assessment_class == PreGrammarAssessment.__name__
        and spec_class in (PreGrammarSpec.__name__, MalformedRecord.__name__)
        and audit == ["profile-mismatch: base"]
    )
    return report


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    # 10a — the same call as step 8, in a new process.
    rederived = answers.payload(belief.evaluate_here(view))
    equal = rederived == st["belief_answer"]
    state.save(rederived_belief=rederived, rederived_equal=equal)
    # 10b — the report, read from the corpus; evidence names no in-process spec.
    report = reconstruct(view, st, close.evidence_for(view, profile()))
    contradiction = report["audit_check"]["contradiction"]
    if contradiction is not None:
        findings.record(10, "defect", f"check_verification: {contradiction['code']}: {contradiction['detail']}")
    state.save(evidence_reconstruction=report)
    if not report["comparison_report_stored"]:
        findings.record(
            10,
            "design-gap",
            "no stored record carries the comparison report; scope and verdict recover only by recomputation over both "
            "stored closures with the corpus's analysis-spec record and in-process rule implementations",
            filed="verification-publication (write-path lane)",
        )
    # 10c — Q10's own arm, and the prior corpus state beside it.
    prior = prior_state()
    restoration = restored(view, st, belief_equal=equal, prior_pre_grammar=bool(prior["prior_pre_grammar"]))
    state.save(
        fresh_process_restoration=restoration,
        prior_corpus_state=prior,
        spec_prose_identity=prior["spec_prose_identity"],
    )
    for key, held in sorted(restoration.items()):
        if not held:
            findings.record(10, "defect", f"fresh-process restoration: {key} is false")
    findings.record(
        10,
        "closed",
        f"the prior corpus state under the successor profile: spec {prior['spec']}; assessment {prior['assessment']}; "
        f"audit_corpus {prior['audit']}",
    )
    if prior["spec_refusal"] != PreGrammarSpec.__name__:
        findings.record(
            10,
            "design-gap",
            "Q10's transition arm, measured: the assessment half fires as asked — the prior corpus's assessment "
            f"record refuses with {prior['assessment']}. The spec half cannot fire at any level: the 2026-09-05 "
            "analysis-spec record predates the projection form, so its reader refuses earlier with "
            f"{prior['spec']}, and `restore`'s estimand_grammar check — the only place PreGrammarSpec is raised — "
            "is never reached. Pre-projection, not merely pre-grammar",
            filed="estimand-typing design (Q10's transition arm, §9)",
        )
    print(json.dumps({"10a": rederived, "equal": equal, "10b": report, "10c": restoration, "prior": prior}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
