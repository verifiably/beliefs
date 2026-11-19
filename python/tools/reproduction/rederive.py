"""Reconstruct current PHF19 comparison evidence from stored records."""

from __future__ import annotations

from beliefs import stored
from beliefs.audit import check_verification
from beliefs.corpus import _StandingRecords
from beliefs.evidence import DerivationEvidence
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification, decode_verification
from reproduction.vocabulary import profile

__all__ = ["reconstruct"]


def reconstruct(view, st: dict, evidence: DerivationEvidence) -> dict:
    """10b, field by field, each labelled. Reads the verification record, the
    two run publications and the spec record; recomputes only through
    `evidence`, which names no in-process spec."""
    node = view.get(st["verification_ref"])
    stored_value = stored.verification_value(node)
    decoded = decode_verification(node)
    report: dict = {
        "inputs": {
            "corpus": [
                "verification record (basis, comparison report, scope, verdict read)",
                "two run publications",
                "analysis-spec record",
            ],
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
        report["scope_read"], report["verdict_read"], report["report_identity_read"] = (
            decoded.scope,
            decoded.verdict,
            decoded.report.identity(),
        )
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        certification = None if decoded is None else decoded.report.certification
        scope = derive_scope(original, replayed, certification=certification)
        report["scope_recomputed"], report["scope_equal"] = scope, scope == stored_value.scope
        rebuilt = build_verification(
            original,
            replayed,
            specs=evidence.specs,
            held_rules=evidence.held_rules,
            contract_identity="none-consulted",
            epoch="none-published",
            certification=certification,
            series_evidence=evidence.series_evidence,
            profile=profile(),
            records=_StandingRecords(view),
        )
        if isinstance(rebuilt, AssessmentVerification):
            report["verdict_recomputed"], report["verdict_equal"] = (
                rebuilt.verdict,
                rebuilt.verdict == stored_value.verdict,
            )
            if decoded is not None:
                report["report_identity_equal"] = rebuilt.report.identity() == decoded.report.identity()
        if view.holds(st["spec_ref"]):
            restored = stored.analysis_spec_value(view.get(st["spec_ref"]), profile=profile())
            report["spec_restored_identity_matches_run"] = restored.identity == original.recipe.spec_identity
    outcome = check_verification(view, node, evidence=evidence, profile=profile())
    report["audit_check"] = {
        "checked": outcome.checked,
        "reason": outcome.reason,
        "contradiction": None
        if outcome.contradiction is None
        else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail},
    }
    return report
