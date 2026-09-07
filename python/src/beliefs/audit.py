"""The corpus-local semantic audit (world-changing families §6.3, §7).

Pure over a read view and caller-supplied evidence: it writes nothing, mints
nothing, and invokes no standing or belief evaluation. Ω_valid comes first —
`corpus_check` classifies what is malformed, and nothing malformed is read
again below it — and only then is a well-formed record's derivation
recomputed. A derivation that cannot be recomputed here is **unchecked**,
never contradicted and never validated; "cannot be checked here" is a reason,
not a verdict.

Like `corpus_check`, `audit_corpus` **reports and never raises**: a record whose
members refuse to be read becomes a `derivation-malformed` finding rather than
an exception that discards every finding already collected for its neighbours.
The single-record checks keep raising, because their callers — the stored layer
and the import boundary — refuse rather than report.

A **neighbour** that cannot be read is a third case, and neither of the first
two: a producing run or a named closure whose own stamp is missing or stale is
already classified by `corpus_check` under its own ref, so re-reporting it under
the audited record would double-count it, and refusing the audited record would
convict it of its neighbour's fault. The audited record's derivation is simply
**unchecked**, with the neighbour named in the reason.

The three value types live in `beliefs.evidence` and are re-exported here, so
one import serves a caller that only ever names the audit.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentValue, build_assessment
from beliefs.corpus import Finding, ReadView, _ImportView, _producers_of, corpus_check
from beliefs.errors import (
    IdentityError,
    MalformedRecord,
    RecordError,
    RuleUnbound,
    SemanticHashMissing,
    SemanticHashStale,
)
from beliefs.evidence import NO_EVIDENCE, DerivationEvidence, DerivationOutcome
from beliefs.recipe import RunClosure
from beliefs.runrecord import decode_run_closure
from beliefs.spec import FrozenSpec
from beliefs.verify import _derive, decode_verification

__all__ = [
    "MALFORMEDNESS_CODES",
    "NO_EVIDENCE",
    "DerivationEvidence",
    "DerivationOutcome",
    "audit_corpus",
    "check_analysis_spec",
    "check_assessment",
    "check_lineage_basis",
    "check_verification",
    "stored_specs",
]


MALFORMEDNESS_CODES = frozenset(
    {"semantic-hash-missing", "semantic-hash-stale", "coordination-facet-malformed", "derivation-malformed"}
)
"""Ω_valid's codes, and only those. A record one of these names is not read
again below the classification. A record flagged for anything **else** — a
malformed display facet, a supersession target that does not resolve locally,
an unmet eligibility predicate — is well formed, and skipping it would hide a
real contradiction behind an unrelated finding."""

_COMPARABLE_ASSESSMENT_MEMBERS = (
    "outcome",
    "interpretation_rule",
    "estimate",
    "uncertainty",
    "estimand",
    "applicability",
)
"""The assessment members a stored facet and a derived value state in the same
vocabulary. `proposition` is deliberately absent: the derived value carries the
spec's claim **target**, and the stored facet carries the corpus **ref** of the
proposition record — two namespaces, and comparing them would fire on
agreement. `spec` and `run` are compared separately, both spelled bare."""


def _unchecked(reason: str) -> DerivationOutcome:
    return DerivationOutcome(checked=False, reason=reason, contradiction=None)


_UNREADABLE_NEIGHBOUR = (IdentityError, SemanticHashMissing, SemanticHashStale)
"""What `ReadView.get` raises over a node whose own stamp is missing, stale, or
unrecomputable. Reaching one from a well-formed record leaves that record
unchecked; the neighbour is `corpus_check`'s to classify, under its own ref."""


def _closure(view: ReadView | _ImportView, ref: str) -> tuple[RunClosure | None, str]:
    if not view.holds(ref):
        return None, f"{ref} does not resolve here"
    try:
        node = view.get(ref)
    except _UNREADABLE_NEIGHBOUR as refused:
        return None, f"{ref} is malformed here: {refused}"
    if node.kind != "run":
        return None, f"{ref} is not a run"
    try:
        return decode_run_closure(node), ""
    except MalformedRecord as refused:
        return None, f"{ref} carries no run-closure projection: {refused}"


def check_verification(
    view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence
) -> DerivationOutcome:
    """Recompute a stored verification's derivation from the two runs it names —
    verdict and assessment identity always; rule, scope rule, scope and report
    identity when the record carries its report (design §6)."""
    decoded = decode_verification(node)  # MalformedRecord propagates: a present, malformed report is refused, never repaired
    derivation = stored.verification_derivation(node)
    if derivation is None:
        return _unchecked("no derivation member")
    original, why = _closure(view, derivation[0])
    if original is None:
        return _unchecked(why)
    replayed, why = _closure(view, derivation[1])
    if replayed is None:
        return _unchecked(why)
    if original.recipe.shape != replayed.recipe.shape:
        return _unchecked("mixed shapes")
    certification = None if decoded is None else decoded.report.certification
    citation = None if decoded is None else decoded.report.citation
    try:
        derived = _derive(
            original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
            certification=certification, citation=citation,
        )
    except RuleUnbound as unbound:
        return _unchecked(str(unbound))
    stored_value = stored.verification_value(node)
    disagreements: list[str] = []
    if derived.verdict != stored_value.verdict:
        disagreements.append(f"verdict stored={stored_value.verdict!r} recomputed={derived.verdict!r}")
    if derived.assessment is not None and derived.assessment != stored_value.assessment:
        disagreements.append("assessment identity differs from the original run's derivation")
    if decoded is not None:
        if decoded.rule != derived.rule:
            disagreements.append(f"rule stored={decoded.rule!r} recomputed={derived.rule!r}")
        scope_rule = original.recipe.boundary_policy.scope_rule
        if decoded.scope_rule != scope_rule:
            disagreements.append(f"scope_rule stored={decoded.scope_rule!r} recomputed={scope_rule!r}")
        if decoded.scope != derived.scope:
            disagreements.append(f"scope stored={decoded.scope!r} recomputed={derived.scope!r}")
        if decoded.report.identity() != derived.report.identity():
            disagreements.append("report identity differs from the recomputed report")
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
    closure, why = _closure(view, stored.typed_ref("run", stored_value.run))
    if closure is None:
        return _unchecked(why)
    derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
    if not isinstance(derived, AssessmentValue):
        return _unchecked(derived.reason)
    disagreements = _assessment_disagreements(stored_value, derived)
    if not disagreements:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="assessment-derivation-contradicted",
            ref=node.id,
            detail=",".join(disagreements),
            message=f"{node.id}: the stored assessment facet contradicts the facet derived from its run",
        ),
    )


def _assessment_disagreements(stored_value: AssessmentValue, derived: AssessmentValue) -> list[str]:
    """The members on which a stored facet and its recomputation disagree.

    `run` and `spec` are part of the comparison, not exempt from it: a facet
    naming a run or a spec its own closure does not is contradicted by that
    alone.
    """
    disagreements = [
        name
        for name in _COMPARABLE_ASSESSMENT_MEMBERS
        if getattr(stored_value, name) != getattr(derived, name)
    ]
    if stored_value.run != derived.run:
        disagreements.append("run")
    if stored_value.spec != derived.spec:
        disagreements.append("spec")
    return sorted(disagreements)


def check_lineage_basis(view: ReadView, node: Node) -> DerivationOutcome:
    """A stamped basis must name every resolved producer of its dataset. A
    producer the basis omits is what a raw-forged `single(A)` looks like while
    `B`'s run stands; once `B`'s run is gone, nothing contradicts it (§7)."""
    if stored.lineage_basis(node) is None:
        return _unchecked("no stamped basis")
    named = set()
    for route in stored.basis_routes(node):
        run = route.get("run")
        if type(run) is not str:
            raise MalformedRecord(f"{node.id}: a stamped basis route names its producing run as a string")
        named.add(run)
    named_resolved = {view.resolve(run) for run in named}
    try:
        producers = {p.resolved_run for p in _producers_of(view, node.id) if p.resolved_run is not None}
    except _UNREADABLE_NEIGHBOUR as refused:
        return _unchecked(f"a producing run of {node.id} is malformed here: {refused}")
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


def check_analysis_spec(node: Node) -> DerivationOutcome:
    """A stored spec restores or is malformed; `audit_corpus` reports the
    latter as `derivation-malformed` under the catch R11 already has."""
    stored.analysis_spec_value(node)
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def stored_specs(view: ReadView | _ImportView) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]:
    """Every restorable stored spec keyed by identity, and one
    `derivation-malformed` finding per record that does not restore — the
    two halves travel together so a false spec never vanishes into an
    unchecked derivation (design decision 15)."""
    specs: dict[str, FrozenSpec] = {}
    findings: list[Finding] = []
    for node in view.iter_stored():
        if node.kind != "analysis-spec":
            continue
        try:
            spec = stored.analysis_spec_value(node)
        except RecordError as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="derivation-malformed",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: the members a derivation recomputation reads are malformed",
                )
            )
            continue
        specs[spec.identity] = spec
    return MappingProxyType(specs), tuple(findings)


def audit_corpus(view: ReadView, *, evidence: DerivationEvidence) -> tuple[Finding, ...]:
    """Ω_valid first, then recomputation over what is well-formed. No standing,
    no belief, no write, no mint — and, like `corpus_check`, no raise: any
    `RecordError` a recomputation raises is reported as `derivation-malformed`,
    so one such record cannot discard the findings collected for every other.
    The catch is the base, not `MalformedRecord`: a recomputation refuses on
    the whole family — a signature that admits no such derivation
    (`SignatureRefused`), an undecodable closure (`MalformedClosure`) — and a
    narrower catch lets those siblings abort the audit."""
    findings = list(corpus_check(view))
    malformed = {finding.ref for finding in findings if finding.code in MALFORMEDNESS_CODES}
    for node in view.iter_stored():
        if node.id in malformed:
            continue
        try:
            if node.kind == "verification":
                outcome = check_verification(view, node, evidence=evidence)
            elif node.kind == "assessment":
                outcome = check_assessment(view, node, evidence=evidence)
            elif node.kind == "dataset":
                outcome = check_lineage_basis(view, node)
            elif node.kind == "analysis-spec":
                outcome = check_analysis_spec(node)
            else:
                continue
        except RecordError as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="derivation-malformed",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: the members a derivation recomputation reads are malformed",
                )
            )
            continue
        if outcome.contradiction is not None:
            findings.append(outcome.contradiction)
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))
