"""Steps 10a/10b, in a fresh process. Every input is labelled corpus / supplied / in-process.

10a's inputs: the corpus (assessment, run, dataset, verification, claim,
holdings observation) plus *supplied* context (producer snapshot identity,
retraction enumeration) plus *in-process* profile and binding. 10b's: the
corpus (two run publications, the verification record, the spec record's
identity) plus *in-process* spec and rule implementations, because no
kernel reader restores a FrozenSpec or a rule from a record.
"""

from __future__ import annotations

import json
import sys

from beliefs import stored
from beliefs.audit import check_verification
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification
from reproduction import answers, belief, close, findings, spec, state, world


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    # 10a — the same call as step 8, in a new process.
    rederived = answers.payload(belief.evaluate_here(view))
    equal = rederived == st["belief_answer"]
    state.save(rederived_belief=rederived, rederived_equal=equal)
    # 10b — evidence reconstruction, field by field, each labelled.
    node = view.get(st["verification_ref"])
    stored_value = stored.verification_value(node)
    facet = node.facets.get(stored.VERIFICATION_FACET, {})
    spec_facet = view.get(st["spec_ref"]).facets.get("analysis-spec", {}) if view.holds(st["spec_ref"]) else {}
    report: dict = {
        "inputs": {
            "corpus": ["verification record", "two run publications", "analysis-spec record (identity only)"],
            "in_process": [
                "FrozenSpec (no kernel reader for the record)",
                "interpretation and equivalence RuleImplementations",
            ],
        },
        "comparison_report_stored": "comparison" in facet,
        "derivation_named": False,
        "closures_decoded": False,
        "scope_recomputed": None,
        "scope_equal": None,
        "verdict_recomputed": None,
        "verdict_equal": None,
        "spec_record_present": bool(spec_facet),
        "spec_identity_matches_in_process": spec_facet.get("identity") == spec.frozen().identity,
        "audit_check": None,
    }
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        scope = derive_scope(original, replayed, certification=None)
        report["scope_recomputed"], report["scope_equal"] = scope, scope == stored_value.scope
        rebuilt = build_verification(
            original,
            replayed,
            specs={spec.frozen().identity: spec.frozen()},
            held_rules={spec.equivalence().identity: spec.equivalence()},
            contract_identity=writer.manifest_pins().science_contract,
            epoch="none-published",
        )
        if isinstance(rebuilt, AssessmentVerification):
            report["verdict_recomputed"], report["verdict_equal"] = rebuilt.verdict, rebuilt.verdict == stored_value.verdict
        else:
            report["verdict_recomputed"] = type(rebuilt).__name__
    outcome = check_verification(view, node, evidence=close.evidence())
    report["audit_check"] = {
        "checked": outcome.checked,
        "reason": outcome.reason,
        "contradiction": None
        if outcome.contradiction is None
        else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail},
    }
    if outcome.contradiction is not None:
        findings.record(
            10, "defect", f"check_verification: {outcome.contradiction.code}: {outcome.contradiction.detail}"
        )
    state.save(evidence_reconstruction=report)
    if not report["comparison_report_stored"]:
        findings.record(
            10,
            "design-gap",
            "no stored record carries the comparison report; scope and verdict recover only by recomputation over both "
            "stored closures with the in-process spec and rule implementations",
            filed="verification-publication (write-path lane)",
        )
    print(json.dumps({"10a": rederived, "equal": equal, "10b": report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
