"""The corpus-local semantic audit (world-changing families §6.3, §7).

Pure over a read view and caller-supplied evidence: it writes nothing, mints
nothing, and invokes no standing or belief evaluation. Ω_valid comes first —
`corpus_check` classifies what is malformed, and nothing malformed is read
again below it — and only then is a well-formed record's derivation
recomputed. A derivation that cannot be recomputed here is **unchecked**,
never contradicted and never validated; "cannot be checked here" is a reason,
not a verdict.

The three value types live in `beliefs.evidence` and are re-exported here, so
one import serves a caller that only ever names the audit.
"""

from __future__ import annotations

from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentValue, build_assessment
from beliefs.corpus import Finding, ReadView, _ImportView, _producers_of, corpus_check
from beliefs.errors import MalformedRecord, RuleUnbound
from beliefs.evidence import NO_EVIDENCE, DerivationEvidence, DerivationOutcome
from beliefs.identity import v1
from beliefs.recipe import RunClosure
from beliefs.record import ASSESSMENT_DOMAIN
from beliefs.runrecord import decode_run_closure
from beliefs.verify import _resolve_rule

__all__ = [
    "NO_EVIDENCE",
    "DerivationEvidence",
    "DerivationOutcome",
    "audit_corpus",
    "check_assessment",
    "check_lineage_basis",
    "check_verification",
]


def _unchecked(reason: str) -> DerivationOutcome:
    return DerivationOutcome(checked=False, reason=reason, contradiction=None)


def _closure(view: ReadView | _ImportView, ref: str) -> tuple[RunClosure | None, str]:
    if not view.holds(ref):
        return None, f"{ref} does not resolve here"
    node = view.get(ref)
    if node.kind != "run":
        return None, f"{ref} is not a run"
    try:
        return decode_run_closure(node), ""
    except MalformedRecord as refused:
        return None, f"{ref} carries no run-closure projection: {refused}"


def check_verification(
    view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence
) -> DerivationOutcome:
    """Recompute a stored verification's verdict from the two runs it names."""
    derivation = stored.verification_derivation(node)  # MalformedRecord propagates: refuse, never repair
    if derivation is None:
        return _unchecked("no derivation member")
    original, why = _closure(view, derivation[0])
    if original is None:
        return _unchecked(why)
    replayed, why = _closure(view, derivation[1])
    if replayed is None:
        return _unchecked(why)
    try:
        _rule, _implementation_identity, implementation, spec = _resolve_rule(
            original, specs=evidence.specs, held_rules=evidence.held_rules
        )
    except RuleUnbound as unbound:
        return _unchecked(str(unbound))
    if original.recipe.shape != replayed.recipe.shape:
        return _unchecked("mixed shapes")
    stored_value = stored.verification_value(node)
    verdict = implementation.evaluate(original.result, replayed.result)
    assessment = None
    if spec is not None:
        assessment = v1.digest(
            ASSESSMENT_DOMAIN,
            {"spec": spec.identity, "run": original.address(), "proposition": spec.target},
        )
    disagreements: list[str] = []
    if verdict != stored_value.verdict:
        disagreements.append(f"verdict stored={stored_value.verdict!r} recomputed={verdict!r}")
    if assessment is not None and assessment != stored_value.assessment:
        disagreements.append("assessment identity differs from the original run's derivation")
    if not disagreements:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="verification-derivation-contradicted",
            ref=node.id,
            detail="; ".join(disagreements),
            message=f"{node.id}: the stored verification contradicts its recomputed derivation",
        ),
    )


def check_assessment(
    view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence
) -> DerivationOutcome:
    """Recompute a stored assessment's facet from the run it names."""
    stored_value = stored.assessment_value(node)
    closure, why = _closure(view, stored_value.run)
    if closure is None:
        return _unchecked(why)
    derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
    if not isinstance(derived, AssessmentValue):
        return _unchecked(derived.reason)
    if derived == stored_value:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="assessment-derivation-contradicted",
            ref=node.id,
            detail=f"stored outcome={stored_value.outcome!r} recomputed={derived.outcome!r}",
            message=f"{node.id}: the stored assessment facet contradicts the facet derived from its run",
        ),
    )


def check_lineage_basis(view: ReadView, node: Node) -> DerivationOutcome:
    """A stamped basis must name every resolved producer of its dataset. A
    producer the basis omits is what a raw-forged `single(A)` looks like while
    `B`'s run stands; once `B`'s run is gone, nothing contradicts it (§7)."""
    if stored.lineage_basis(node) is None:
        return _unchecked("no stamped basis")
    named = {route.get("run") for route in stored.basis_routes(node)}
    named_resolved = {view.resolve(str(run)) for run in named}
    producers = {p.resolved_run for p in _producers_of(view, node.id) if p.resolved_run is not None}
    omitted = sorted(producers - named_resolved)
    if not omitted:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="lineage-basis-contradicted",
            ref=node.id,
            detail=",".join(omitted),
            message=f"{node.id}: the stamped basis omits a producing run that resolves here",
        ),
    )


def audit_corpus(view: ReadView, *, evidence: DerivationEvidence) -> tuple[Finding, ...]:
    """Ω_valid first, then recomputation over what is well-formed. No standing,
    no belief, no write, no mint."""
    findings = list(corpus_check(view))
    flagged = {finding.ref for finding in findings}
    for node in view.iter_stored():
        if node.id in flagged:
            continue
        if node.kind == "verification":
            outcome = check_verification(view, node, evidence=evidence)
        elif node.kind == "assessment":
            outcome = check_assessment(view, node, evidence=evidence)
        elif node.kind == "dataset":
            outcome = check_lineage_basis(view, node)
        else:
            continue
        if outcome.contradiction is not None:
            findings.append(outcome.contradiction)
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))
