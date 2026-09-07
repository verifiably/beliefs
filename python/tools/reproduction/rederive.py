"""Steps 10a/10b, in a fresh process. Every input is labelled corpus / supplied / in-process.

10a's inputs: the corpus (assessment, run, dataset, verification, claim,
holdings observation) plus *supplied* context (producer snapshot identity,
retraction enumeration) plus *in-process* profile and binding. 10b's: the
corpus (verification record, two run publications, analysis-spec record)
plus *in-process* interpretation and equivalence rule implementations — the
only thing no kernel reader restores from a record.
"""

from __future__ import annotations

import json
import sys

from beliefs import stored
from beliefs.audit import check_verification
from beliefs.evidence import DerivationEvidence
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification, decode_verification
from reproduction import answers, belief, close, findings, state, world


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
            restored = stored.analysis_spec_value(view.get(st["spec_ref"]))
            report["spec_restored_identity_matches_run"] = restored.identity == original.recipe.spec_identity
    outcome = check_verification(view, node, evidence=evidence)
    report["audit_check"] = {
        "checked": outcome.checked,
        "reason": outcome.reason,
        "contradiction": None if outcome.contradiction is None else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail},
    }
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
    report = reconstruct(view, st, close.evidence_for(view))
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
    print(json.dumps({"10a": rederived, "equal": equal, "10b": report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
