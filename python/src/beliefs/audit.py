"""The corpus-local semantic audit.

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

from collections.abc import Container, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from nodes.core.errors import RefError
from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentValue, build_assessment
from beliefs.corpus import (
    ELIGIBILITY_CODES,
    EligibilityOutcome,
    Finding,
    MismatchScope,
    ReadView,
    _absence_of,
    _CapturedCheckView,
    _dataset_standing_outcome,
    _ImportView,
    _manifest_findings,
    _merged_capture,
    _producers_of,
    _record_findings,
    corpus_check,
    eligibility_outcome,
)
from beliefs.errors import (
    CorpusDamaged,
    IdentityError,
    MalformedRecord,
    PreGrammarAssessment,
    PreGrammarSpec,
    RecordError,
    RuleUnbound,
    ScienceError,
    SemanticHashMissing,
    SemanticHashStale,
)
from beliefs.evidence import NO_EVIDENCE, DerivationEvidence, DerivationOutcome
from beliefs.profile import ProfileSpec
from beliefs.recipe import RunClosure
from beliefs.reservation import (
    UNREAD,
    CheckRefusal,
    ReservationAssignment,
    Unread,
    assignment_record_refusal,
    assignment_succession_refusal,
    exposure_event_refusal,
)
from beliefs.runrecord import decode_run_closure
from beliefs.spec import FrozenSpec
from beliefs.verify import _derive, decode_verification

if TYPE_CHECKING:
    from beliefs.world.epoch import Epoch
    from beliefs.world.read import BoundStamp
    from beliefs.world.registry import World
    from beliefs.world.view import WorldReadView

__all__ = [
    "MALFORMEDNESS_CODES",
    "NO_EVIDENCE",
    "WORLD_AUDIT_CODES",
    "DerivationEvidence",
    "DerivationOutcome",
    "WorldAudit",
    "audit_corpus",
    "audit_world",
    "check_analysis_spec",
    "check_assessment",
    "check_assignment_chains",
    "check_composite",
    "check_exposure_event",
    "check_lineage_basis",
    "check_reservation_assignment",
    "check_spec_target",
    "check_supersedes_kinds",
    "check_verification",
    "stored_specs",
]


MALFORMEDNESS_CODES = frozenset(
    {
        "semantic-hash-missing",
        "semantic-hash-stale",
        "coordination-facet-malformed",
        "derivation-malformed",
        "facet-payload-malformed",
    }
)
"""Ω_valid's codes, and only those. A record one of these names is not read
again below the classification. A record flagged for anything **else** — a
malformed display facet, a supersession target that does not resolve locally,
an unmet eligibility predicate — is well formed, and skipping it would hide a
real contradiction behind an unrelated finding."""

WORLD_AUDIT_CODES = frozenset(
    {
        "epoch-malformed",
        "receipt-malformed",
        "receipt-refuted",
        "receipt-unresolvable",
        "snapshot-contradicted",
        "anchor-uncorroborated",
        "parse-error",
        "path-mismatch",
        "uid-collision",
        "id-collision",
        "corpus-damaged",
        "corpus-absent",
        "drift",
        "derivation-unreachable",
        "attestation-endpoint-unknown",
        "attestation-endpoint-unreachable",
        "source-identifier-shared",
        "composite-member-unresolvable",
        "composite-member-mismatch",
        "composite-relations-mismatch",
        "composite-malformed",
        "supersedes-cross-kind",
        "exposure-edge-mismatch",
        "exposure-ref-unresolved",
        "exposure-unit-sort-undeclared",
        "assignment-edge-mismatch",
        "assignment-ref-unresolved",
        "assignment-applies-scoped",
        "assignment-unit-sort-undeclared",
        "assignment-fork",
        "assignment-scope-mismatch",
        "assignment-changes-without-evidence",
        "assignment-suspension-unflagged",
        "assignment-flagged-without-suspension",
        "assignment-unchanged",
        "register-stale",
        "register-missing",
        "register-entry-unknown",
        "bridging-register-uncited",
    }
)
"""The closed set of codes a world audit may report, beside `MALFORMEDNESS_CODES`."""


@dataclass(frozen=True)
class WorldAudit:
    stamp: BoundStamp
    corpora: Mapping[str, tuple[Finding, ...]]
    world: tuple[Finding, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "corpora", MappingProxyType(dict(self.corpora)))


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


def _closure(view: ReadView | _ImportView | WorldReadView, ref: str) -> tuple[RunClosure | None, str]:
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
    view: ReadView | _ImportView | WorldReadView, node: Node, *, evidence: DerivationEvidence
) -> DerivationOutcome:
    """Recompute a stored verification's derivation from the two runs it names —
    verdict and assessment identity always; rule, scope rule, scope and report
    identity when the record carries its report."""
    decoded = decode_verification(
        node
    )  # MalformedRecord propagates: a present, malformed report is refused, never repaired
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
            original,
            replayed,
            specs=evidence.specs,
            held_rules=evidence.held_rules,
            certification=certification,
            citation=citation,
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
    view: ReadView | _ImportView | WorldReadView, node: Node, *, evidence: DerivationEvidence, profile: ProfileSpec
) -> DerivationOutcome:
    """Recompute a stored assessment's facet from the run it names."""
    stored_value = stored.assessment_value(node, profile=profile)
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
        name for name in _COMPARABLE_ASSESSMENT_MEMBERS if getattr(stored_value, name) != getattr(derived, name)
    ]
    if stored_value.run != derived.run:
        disagreements.append("run")
    if stored_value.spec != derived.spec:
        disagreements.append("spec")
    return sorted(disagreements)


def check_lineage_basis(view: ReadView | WorldReadView, node: Node) -> DerivationOutcome:
    """A stamped basis must name every resolved producer of its dataset. A
    producer the basis omits is what a raw-forged `single(A)` looks like while
    `B`'s run stands; once `B`'s run is gone, nothing contradicts it."""
    basis = stored.lineage_basis(node)
    if basis is None:
        return _unchecked("no stamped basis")
    routes = stored.basis_routes(node)
    named = set()
    for route in routes:
        run = route.get("run")
        if type(run) is not str:
            raise MalformedRecord(f"{node.id}: a stamped basis route names its producing run as a string")
        named.add(run)
    named_resolved = {view.resolve(run) for run in named}
    try:
        producer_entries = _producers_of(view, node.id)
    except _UNREADABLE_NEIGHBOUR as refused:
        return _unchecked(f"a producing run of {node.id} is malformed here: {refused}")
    single_transforms: tuple[str, ...] | None = None
    if basis.get("tag") == "single" and len(routes) == 1:
        single_transforms = tuple(str(entry) for entry in routes[0].get("transforms", []) or ())
    omitted_set: set[str] = set()
    for p in producer_entries:
        if p.resolved_run is None or p.resolved_run in named_resolved:
            continue
        if single_transforms is not None:
            closure, _ = _closure(view, p.stored_run)
            if closure is not None and p.transforms == single_transforms:
                continue
        omitted_set.add(p.resolved_run)
    omitted = sorted(omitted_set)
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


def check_spec_target(
    view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec
) -> DerivationOutcome:
    """The boundary's estimand-target comparison, over a stored record: the
    claim identity, the operator and, when both agree, admission of the
    estimand for the target's claim (`admit_estimand` over the decodable set),
    each a disagreement of its own."""
    from beliefs.decode import claim_from_stored
    from beliefs.errors import EstimandError
    from beliefs.estimand import admit_estimand
    from beliefs.projection import claim_identity
    from beliefs.resolution import build_snapshot

    spec = stored.analysis_spec_value(node, profile=profile)
    if not view.holds(spec.target):
        return _unchecked(f"{spec.target} does not resolve here")
    target = view.get(spec.target)
    if target.kind != "proposition":
        return _unchecked(f"{spec.target} is not a proposition")
    claim, _receipt = claim_from_stored(target, profile=profile, snapshot=build_snapshot(readable={}))
    disagreements = []
    if spec.estimand.claim != claim_identity(claim):
        disagreements.append("claim")
    if spec.estimand.operator != claim.operator:
        disagreements.append("operator")
    if not disagreements:
        try:
            admit_estimand(profile, spec.estimand, claim, authoring=False)
        except EstimandError:
            disagreements.append("admission")
    if not disagreements:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="spec-target-contradicted",
            ref=node.id,
            detail=",".join(disagreements),
            message=f"{node.id}: the spec's estimand does not answer the claim its target carries",
        ),
    )


def check_composite(
    view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec
) -> DerivationOutcome:
    """The boundary's four steps over the stored record, reported
    rather than raised. Form only — the audit holds no snapshot."""
    from beliefs import composite as composite_module
    from beliefs.errors import CompositeError
    from beliefs.world.view import WorldReadView

    def contradiction(code: str, detail: str) -> DerivationOutcome:
        return DerivationOutcome(
            checked=True,
            reason="",
            contradiction=Finding(
                severity="error", code=code, ref=node.id, detail=detail, message=f"{node.id}: {detail}"
            ),
        )

    facet = stored.composite_value(node)  # MalformedRecord → derivation-malformed, by the loop's catch
    composes = [r for r in node.relations if r.predicate == stored.COMPOSES]
    if reason := composite_module.check_composes_relations(node, facet):
        return contradiction("composite-relations-mismatch", reason)
    available = []
    absent = []
    if isinstance(view, WorldReadView):
        # Recorded elsewhere is not gone (module docstring, third case): a member
        # whose corpus has no carrier here would answer `RecordNotPresent` inside
        # `restore_members`, which translates `RefError` alone. Reporting
        # `composite-member-unresolvable` for it would convict the composite of
        # its neighbour's absence; the derivation is simply unchecked.
        for index, relation in enumerate(composes):
            if view.holds(relation.target):
                available.append(index)
                continue
            elsewhere = _absence_of(view, relation.target)
            if elsewhere is not None:
                absent.append((relation.target, elsewhere))
                continue
            available.append(index)
    else:
        available = list(range(len(composes)))
    try:
        checked_facet = composite_module.CompositeFacet(
            grammar=facet.grammar,
            shape=facet.shape,
            nodes=facet.nodes,
            members=tuple(facet.members[index] for index in available),
        )
        claims = composite_module.restore_members(
            view,
            checked_facet.members,
            tuple(composes[index].target for index in available),
            profile=profile,
            snapshot=composite_module.EMPTY_SNAPSHOT,
        )
        composite_module.classify(profile, checked_facet, claims)
    except CompositeError as refused:
        if refused.code in ("composite-member-unresolvable", "composite-member-mismatch"):
            return contradiction(refused.code, str(refused))
        return contradiction("composite-malformed", str(refused))
    if absent:
        return _unchecked(
            "; ".join(f"member {ref} is recorded in {corpus}, which has no carrier here" for ref, corpus in absent)
        )
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def _contradicted(node: Node, code: str, detail: str) -> DerivationOutcome:
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(severity="error", code=code, ref=node.id, detail=detail, message=f"{node.id}: {detail}"),
    )


class _CitedReader:
    """The audit's resolution for the shared reservation checks. A reference recorded in an absent corpus,
    or one whose own stamp or facet is unreadable here, is a neighbour's fault (module docstring, third
    case): it answers `UNREAD` (or None from `assignment_of`), is named in `skipped`, and the record's
    derivation is unchecked rather than convicted. `holds` before `get`, as `check_supersedes_kinds`
    does; a dangling reference answers None, the shared check's `*-ref-unresolved`."""

    def __init__(self, view: ReadView | _ImportView | WorldReadView) -> None:
        self._view = view
        self.skipped: list[str] = []
        self.unread: set[str] = set()

    def kind_of(self, ref: str) -> str | Unread | None:
        if not self._view.holds(ref):
            elsewhere = _absence_of(self._view, ref)
            if elsewhere is None:
                return None
            return self._skip(ref, f"{ref} is recorded in {elsewhere}, which has no carrier here")
        try:
            return self._view.get(ref).kind
        except _UNREADABLE_NEIGHBOUR as refused:
            return self._skip(ref, f"{ref} is malformed here: {refused}")

    def assignment_of(self, ref: str) -> ReservationAssignment | None:
        try:
            return stored.reservation_assignment_value(self._view.get(ref))
        except MalformedRecord as refused:
            self._skip(ref, f"{ref} is malformed here: {refused}")
            return None

    def _skip(self, ref: str, reason: str) -> Unread:
        self.unread.add(ref)
        self.skipped.append(reason)
        return UNREAD

    def outcome(self, node: Node, refusal: CheckRefusal | None) -> DerivationOutcome:
        if refusal is not None:
            return _contradicted(node, refusal.code, refusal.detail)
        if self.skipped:
            return _unchecked("; ".join(self.skipped))
        return DerivationOutcome(checked=True, reason="", contradiction=None)


def check_exposure_event(
    view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec
) -> DerivationOutcome:
    """The boundary's `exposure_event_refusal` over the stored record, reported rather than raised. The
    recorder's binding to an actor is a write-time authority check, not a derivation, and is not
    repeated here."""
    value = stored.exposure_event_value(node)  # MalformedRecord → derivation-malformed, by the loop's catch
    reader = _CitedReader(view)
    return reader.outcome(
        node, exposure_event_refusal(value, node.relations, kind_of=reader.kind_of, sorts=profile.sorts)
    )


def check_reservation_assignment(
    view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec
) -> DerivationOutcome:
    """The boundary's `assignment_record_refusal` and `assignment_succession_refusal` over the stored
    record, reported rather than raised. The chain's linearity between them is
    `check_assignment_chains`'s, one pass over the corpus; the assigner's binding is a write-time
    authority check and is not repeated. Without a readable predecessor no change is derived, so the
    succession checks are not judged."""
    value = stored.reservation_assignment_value(node)  # MalformedRecord → derivation-malformed, by the loop's catch
    reader = _CitedReader(view)
    refusal = assignment_record_refusal(
        value, node.relations, kind_of=reader.kind_of, assignment_of=reader.assignment_of, sorts=profile.sorts
    )
    if refusal is not None or value.predecessor is None:
        return reader.outcome(node, refusal or assignment_succession_refusal(value, None))
    if value.predecessor in reader.unread:
        return reader.outcome(node, None)
    predecessor = reader.assignment_of(value.predecessor)
    if predecessor is None:
        return reader.outcome(node, None)
    return reader.outcome(node, assignment_succession_refusal(value, predecessor))


def check_assignment_chains(
    view: ReadView | _CapturedCheckView, *, malformed: Container[str] = ()
) -> tuple[Finding, ...]:
    """One pass over the view's reservation assignments: a predecessor named by two successors, or a
    chain (`chain` × `scope`) with two roots, is an `assignment-fork` the boundary refuses
    (`assignment-superseded`, `assignment-root-exists`), import included, so only a raw write (one made
    around the boundary) can make it. The finding names the later record by id order, its detail both.
    An assignment its reader refuses or `corpus_check` flagged malformed is not read here."""
    successors: dict[str, list[str]] = {}
    roots: dict[tuple[str, str | None], list[str]] = {}
    for node in view.iter_stored():
        if node.kind != "reservation-assignment" or node.id in malformed:
            continue
        try:
            value = stored.reservation_assignment_value(node)
        except MalformedRecord:
            continue
        if value.predecessor is None:
            roots.setdefault((value.chain, value.scope), []).append(node.id)
        else:
            successors.setdefault(value.predecessor, []).append(node.id)
    findings: list[Finding] = []

    def fork(ref: str, detail: str) -> None:
        findings.append(
            Finding(severity="error", code="assignment-fork", ref=ref, detail=detail, message=f"{ref}: {detail}")
        )

    for predecessor, refs in successors.items():
        first, *later = sorted(refs)
        for ref in later:
            fork(ref, f"{predecessor} has the successors {first} and {ref}; a chain is linear")
    for (chain, scope), refs in roots.items():
        first, *later = sorted(refs)
        for ref in later:
            fork(ref, f"chain {chain!r} (scope {scope!r}) has the roots {first} and {ref}")
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))


def check_supersedes_kinds(
    view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec
) -> Finding | None:
    """The `same_kind` rule, under audit: a raw-written edge the
    shared path would have refused.

    `holds` before `get`, as `check_spec_target` does: over a world view a
    predecessor recorded in an absent corpus answers `RecordNotPresent`, which is
    a `ScienceError` and not a `RecordError`, and an unguarded `get` would carry
    it out of the per-record loop and discard every finding collected so far.
    """
    rule = profile.relations.get(stored.SUPERSEDES)
    if rule is None or not rule.same_kind:
        return None
    for relation in node.relations:
        if relation.predicate != stored.SUPERSEDES:
            continue
        if not view.holds(relation.target):
            continue  # resolution is the supersession arm's finding, not this one's
        target = view.get(relation.target)
        if target.kind != node.kind:
            detail = f"a {node.kind!r} names a {target.kind!r} predecessor ({relation.target})"
            return Finding(
                severity="error",
                code="supersedes-cross-kind",
                ref=node.id,
                detail=detail,
                message=f"{node.id}: {detail}",
            )
    return None


def check_analysis_spec(node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """A stored spec restores or is malformed; `audit_corpus` reports the
    latter as `derivation-malformed` under the catch it already has."""
    stored.analysis_spec_value(node, profile=profile)
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def stored_specs(
    view: ReadView | _ImportView | WorldReadView, *, profile: ProfileSpec
) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]:
    """Every restorable stored spec keyed by identity, and one
    `derivation-malformed` finding per record that does not restore — the
    two halves travel together so a false spec never vanishes into an
    unchecked derivation. A pre-grammar spec is named by
    its own code (`spec-pre-grammar`), never folded into `derivation-malformed`."""
    specs: dict[str, FrozenSpec] = {}
    findings: list[Finding] = []
    for node in view.iter_stored():
        if node.kind != "analysis-spec":
            continue
        try:
            spec = stored.analysis_spec_value(node, profile=profile)
        except PreGrammarSpec as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="spec-pre-grammar",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: pre-grammar spec; the corpus was not recreated",
                )
            )
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
        specs[spec.identity] = spec
    return MappingProxyType(specs), tuple(findings)


def audit_corpus(view: ReadView, *, evidence: DerivationEvidence, profile: ProfileSpec) -> tuple[Finding, ...]:
    """Ω_valid first, then recomputation over what is well-formed. No standing,
    no belief, no write, no mint — and, like `corpus_check`, no raise: any
    `RecordError` a recomputation raises is reported as `derivation-malformed`,
    so one such record cannot discard the findings collected for every other.
    The catch is the base, not `MalformedRecord`: a recomputation refuses on
    the whole family — a signature that admits no such derivation
    (`SignatureRefused`), an undecodable closure (`MalformedClosure`) — and a
    narrower catch lets those siblings abort the audit."""
    findings = list(corpus_check(view, profile))
    if any(f.code == "profile-mismatch" and f.detail in ("base", "malformed") for f in findings):
        return tuple(findings)
    malformed = {finding.ref for finding in findings if finding.code in MALFORMEDNESS_CODES}
    for node in view.iter_stored():
        if node.id in malformed:
            continue
        try:
            cross = check_supersedes_kinds(view, node, profile=profile)
            if cross is not None:
                findings.append(cross)
            if node.kind == "verification":
                outcome = check_verification(view, node, evidence=evidence)
            elif node.kind == "assessment":
                outcome = check_assessment(view, node, evidence=evidence, profile=profile)
            elif node.kind == "dataset":
                outcome = check_lineage_basis(view, node)
            elif node.kind == "analysis-spec":
                outcome = check_spec_target(view, node, profile=profile)
            elif node.kind == "composite":
                outcome = check_composite(view, node, profile=profile)
            elif node.kind == "exposure-event":
                outcome = check_exposure_event(view, node, profile=profile)
            elif node.kind == "reservation-assignment":
                outcome = check_reservation_assignment(view, node, profile=profile)
            else:
                continue
        except PreGrammarSpec as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="spec-pre-grammar",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: pre-grammar spec; the corpus was not recreated",
                )
            )
            continue
        except PreGrammarAssessment as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="assessment-pre-grammar",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: pre-grammar assessment; the corpus was not recreated",
                )
            )
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
    findings.extend(check_assignment_chains(view, malformed=malformed))
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))


def _recompute(
    view: WorldReadView, node: Node, evidence: DerivationEvidence, profile: ProfileSpec
) -> DerivationOutcome | None:
    if node.kind == "verification":
        return check_verification(view, node, evidence=evidence)
    if node.kind == "assessment":
        return check_assessment(view, node, evidence=evidence, profile=profile)
    if node.kind == "dataset":
        return check_lineage_basis(view, node)
    if node.kind == "analysis-spec":
        check_analysis_spec(node, profile=profile)
        return check_spec_target(view, node, profile=profile)
    if node.kind == "composite":
        return check_composite(view, node, profile=profile)
    if node.kind == "exposure-event":
        return check_exposure_event(view, node, profile=profile)
    if node.kind == "reservation-assignment":
        return check_reservation_assignment(view, node, profile=profile)
    return None


class _CapturedCitations:
    """The total reader over the captured world, for one citing corpus:
    own corpus first, then the epoch's map; never a live read, never a raise."""

    def __init__(
        self,
        view: WorldReadView,
        citing: str,
        readable: Mapping[str, _CapturedCheckView],
        causes: Mapping[str, str],
        malformed: Mapping[str, Mapping[str, str]],
    ) -> None:
        self._view = view
        self._citing = citing
        self._own = readable[citing]
        self._readable = readable
        self._causes = causes
        self._malformed = malformed
        self._profile: ProfileSpec | None = None
        self.unreadable: dict[str, str] = {}
        self._judging_incomplete: set[str] = set()
        self._incomplete_memo: dict[str, bool] = {}
        self._fold_view: _CapturedCheckView | None = None

    def _holder(self, ref: str) -> _CapturedCheckView | None:
        if self._own.holds(ref):
            if self._incomplete(ref):
                self.unreadable[ref] = f"{self._citing} producers-incomplete:{','.join(sorted(self._causes))}"
                return None
            return self._own
        holders = [corpus_id for corpus_id in self._view.holders_of(ref) if corpus_id != self._citing]
        if not holders:
            return None
        # The first readable holder answers; unreadable only when none is, naming every cause.
        causes: list[str] = []
        for corpus_id in holders:
            cause = self._causes.get(corpus_id)
            holder = self._readable.get(corpus_id)
            if cause is None and holder is not None:
                canonical = holder.resolve(ref)  # an alias names the canonical record the map is keyed by
                if canonical is not None and canonical in self._malformed.get(corpus_id, {}):
                    cause = f"malformed:{self._malformed[corpus_id][canonical]}"
            if cause is None and holder is not None:
                return holder
            causes.append(f"{corpus_id} {cause if cause is not None else 'unreadable'}")
        self.unreadable[ref] = "; ".join(causes)
        return None

    def _incomplete(self, ref: str) -> bool:
        """Per dataset: an own dataset the epoch never mapped, while a
        covered corpus is unreadable, is uncertain only when it would otherwise
        have empirical standing, directly or inherited through its basis. A
        missing or malformed facet, a divergent or retired basis, a known
        producer, an unresolved report or an ancestor without standing each
        decide it definitely, and the scan goes on.

        Keyed by the canonical id, so an alias and its record are one dataset.
        While a dataset is judged it reads as held (`_judging_incomplete`); a
        distinct unmapped ancestor reached on the walk is judged the same way
        in turn. Each answer is kept for the current `eligibility()` pass: it
        does not depend on which datasets are being judged around it (a cycle
        is `lineage-incomplete` under any guard), so a drift chain costs one
        judgment per link rather than one per touch."""
        if not self._causes:
            return False
        node = self._own.get(ref)
        canonical = node.id
        if canonical in self._judging_incomplete or node.kind != "dataset":
            return False
        if self._view.corpus_of(canonical) is not None:
            return False
        known = self._incomplete_memo.get(canonical)
        if known is not None:
            return known
        assert self._profile is not None, "producer completeness is judged inside eligibility()"
        self._judging_incomplete.add(canonical)
        try:
            answer = _dataset_standing_outcome(self, ref, self._profile, judge=self, reports=self._holder) is None
        finally:
            self._judging_incomplete.discard(canonical)
        self._incomplete_memo[canonical] = answer
        return answer

    def holds(self, ref: str) -> bool:
        return self._holder(ref) is not None

    def resolve(self, ref: str) -> str | None:
        holder = self._holder(ref)
        return None if holder is None else holder.resolve(ref)

    def get(self, ref: str) -> Node:
        holder = self._holder(ref)
        if holder is None:
            raise RefError(f"{ref}: not readable in this capture")
        return holder.get(ref)

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        found = {producer for view in self._readable.values() for producer in view.producers(dataset, aliases=aliases)}
        found.update(self._view.published_producers(dataset))
        return tuple(sorted(found))

    def retraction_fold_view(self) -> _CapturedCheckView:
        """Every readable corpus's records, merged once per audit reader: the
        retractions a route fold can see."""
        if self._fold_view is None:
            self._fold_view = _merged_capture(self._readable)[0]
        return self._fold_view

    def absence_cause(self, ref: str) -> str | None:
        """Why `ref` did not resolve, when an unreadable holder is the reason."""
        return self.unreadable.get(ref)

    def note_retractions_incomplete(self, ref: str) -> bool:
        """A route-identitied basis judged while a covered corpus is unreadable:
        that corpus could hold a standing route retraction, or a counter to
        one, that the fold over the readable corpora missed. Records why `ref`
        is uncertain and answers `True`; a dataset being judged for producer
        completeness defers to that judgment."""
        if not self._causes or (self._own.resolve(ref) or ref) in self._judging_incomplete:
            return False
        self.unreadable[ref] = f"{self._citing} retractions-incomplete:{','.join(sorted(self._causes))}"
        return True

    def eligibility(self, node: Node, profile: ProfileSpec) -> EligibilityOutcome | None:
        self.unreadable = {}
        self._incomplete_memo = {}
        self._profile = profile
        outcome = eligibility_outcome(self, node, profile, reports=self._holder)
        if outcome is None or not outcome.unresolved:
            return outcome
        if not any(ref in self.unreadable for ref in outcome.unresolved):
            return EligibilityOutcome(outcome.reason)  # only unmapped references: unmet
        return EligibilityOutcome(
            outcome.reason,
            tuple(f"{ref} ({self.unreadable[ref]})" if ref in self.unreadable else ref for ref in outcome.unresolved),
        )


def audit_world(
    world: World,
    published: Epoch,
    *,
    evidence: DerivationEvidence,
    profile: ProfileSpec,
) -> WorldAudit:
    """Judge the capture at `published`; writes nothing.

    Carrier and open refusals, including `CaptureDrift`, retain their documented
    behavior. Damage reached within the capture becomes findings.
    """
    from beliefs.world.view import open_world_view

    view = open_world_view(world, published, on_damage="report")
    damaged = {report.corpus_id: report for report in view.damaged()}
    drift = {report.corpus_id: report for report in view.drift()}
    corpora: dict[str, list[Finding]] = {}
    malformed: dict[str, set[str]] = {}
    malformed_codes: dict[str, dict[str, str]] = {}
    excluded: set[str] = set()
    excluded_scope: dict[str, str] = {}
    eligible: dict[str, tuple[_CapturedCheckView, MismatchScope, frozenset[str]]] = {}
    for corpus_id, _state in published.coverage:
        findings = corpora.setdefault(corpus_id, [])
        if corpus_id in view.absent():
            findings.append(
                Finding(
                    "warning",
                    "corpus-absent",
                    corpus_id,
                    "",
                    f"{corpus_id}: a covered corpus with no carrier here",
                )
            )
            continue
        manifest_findings, scope, disagreeing = _manifest_findings(view.captured_manifest(corpus_id), profile)
        findings.extend(manifest_findings)
        report = damaged.get(corpus_id)
        if report is not None and report.cause == "base-pin":
            findings.append(
                Finding(
                    "error",
                    "corpus-damaged",
                    corpus_id,
                    "base-pin",
                    f"{corpus_id}: the manifest pins a base this runtime does not ship; "
                    "no record was read and nothing was recomputed",
                )
            )
            continue
        if scope in ("base", "malformed"):
            excluded.add(corpus_id)
            excluded_scope[corpus_id] = scope
            continue
        captured = _CapturedCheckView(view.captured_records(corpus_id))
        eligible[corpus_id] = (captured, scope, disagreeing)
        findings.extend(
            f for f in _record_findings(captured, profile, scope, disagreeing) if f.code not in ELIGIBILITY_CODES
        )
        malformed[corpus_id] = {finding.ref for finding in findings if finding.code in MALFORMEDNESS_CODES}
        malformed_codes[corpus_id] = {f.ref: f.code for f in findings if f.code in MALFORMEDNESS_CODES}
        if report is not None:
            findings.extend(report.findings)
            excluded_count = len({finding.ref for finding in report.findings})
            findings.append(
                Finding(
                    "error",
                    "corpus-damaged",
                    corpus_id,
                    f"construction:{excluded_count}",
                    f"{corpus_id}: {excluded_count} file(s) failed construction; the remainder was audited, "
                    "nothing was recomputed and no drift comparison was made",
                )
            )
            continue
        moved = drift.get(corpus_id)
        if moved is not None:
            if moved.published_state != moved.captured_state:
                findings.append(
                    Finding(
                        "warning",
                        "drift",
                        corpus_id,
                        "state",
                        f"{corpus_id}: the carrier stands at {moved.captured_state[:12]}…, not the "
                        f"{moved.published_state[:12]}… this epoch recorded; rebuild to publish over it",
                    )
                )
            for uid in moved.unmapped:
                findings.append(
                    Finding(
                        "warning",
                        "drift",
                        corpus_id,
                        f"unmapped:{uid}",
                        f"{corpus_id}: uid {uid!r} is held but the epoch never mapped it; rebuild to publish it",
                    )
                )
    causes = {corpus_id: "absent" for corpus_id in view.absent()}
    causes.update({report.corpus_id: f"damaged:{report.cause}" for report in view.damaged()})
    causes.update({corpus_id: f"excluded:{scope}" for corpus_id, scope in excluded_scope.items()})
    readable = {corpus_id: captured for corpus_id, (captured, _scope, _disagreeing) in eligible.items()}
    for corpus_id, (captured, scope, disagreeing) in sorted(eligible.items()):
        reader = _CapturedCitations(view, corpus_id, readable, causes, malformed_codes)
        second = _record_findings(captured, profile, scope, disagreeing, citations=reader)
        corpora[corpus_id].extend(f for f in second if f.code in ELIGIBILITY_CODES)
        corpora[corpus_id].extend(check_assignment_chains(captured, malformed=malformed.get(corpus_id, ())))
    # A record held in several corpora is recomputed once and its findings are
    # filed under every captured holder whose audit is not excluded for it.
    for holders, node in view._mapped_holders():
        targets = [h for h in holders if h not in excluded and node.id not in malformed.get(h, set())]
        if not targets:
            continue
        found: list[Finding] = []
        corpus_id = targets[0]
        try:
            cross = check_supersedes_kinds(view, node, profile=profile)
            if cross is not None:
                found.append(cross)
            outcome = _recompute(view, node, evidence, profile)
        except CorpusDamaged as unreachable:
            found.append(
                Finding(
                    "warning",
                    "derivation-unreachable",
                    node.id,
                    unreachable.corpus_id,
                    f"{node.id}: its recomputation reaches {unreachable.corpus_id}, which this audit could not read whole",
                )
            )
            for holder in targets:
                corpora[holder].extend(found)
            continue
        except PreGrammarSpec as refused:
            found.append(
                Finding(
                    "error",
                    "spec-pre-grammar",
                    node.id,
                    str(refused),
                    f"{node.id}: pre-grammar spec; the corpus was not recreated",
                )
            )
            for holder in targets:
                corpora[holder].extend(found)
            continue
        except PreGrammarAssessment as refused:
            found.append(
                Finding(
                    "error",
                    "assessment-pre-grammar",
                    node.id,
                    str(refused),
                    f"{node.id}: pre-grammar assessment; the corpus was not recreated",
                )
            )
            for holder in targets:
                corpora[holder].extend(found)
            continue
        except RecordError as refused:
            found.append(
                Finding(
                    "error",
                    "derivation-malformed",
                    node.id,
                    str(refused),
                    f"{node.id}: the members a derivation recomputation reads are malformed",
                )
            )
            for holder in targets:
                corpora[holder].extend(found)
            continue
        if outcome is not None and outcome.contradiction is not None:
            found.append(outcome.contradiction)
        for holder in targets:
            corpora[holder].extend(found)
    world_findings = _world_findings(world, view, published, malformed, excluded)
    return WorldAudit(
        view.stamp,
        {
            corpus_id: tuple(sorted(findings, key=lambda finding: finding.sort_key))
            for corpus_id, findings in corpora.items()
        },
        tuple(sorted(world_findings, key=lambda finding: finding.sort_key)),
    )


def _world_findings(
    world: World,
    view: WorldReadView,
    published: Epoch,
    malformed: Mapping[str, set[str]],
    excluded: set[str],
) -> list[Finding]:
    """Ω_valid first: malformed and excluded records are not decoded again."""
    from beliefs import source as source_basis
    from beliefs.errors import IdentifierMalformed
    from beliefs.world import audit as epoch_audit
    from beliefs.world.read import Unknown, reported_receipt

    findings: list[Finding] = []
    identifiers: dict[tuple[str, str], list[str]] = {}
    for holders, node in view._mapped_holders():
        if all(corpus_id in excluded or node.id in malformed.get(corpus_id, set()) for corpus_id in holders):
            continue
        if node.kind == "coreference-attestation":
            try:
                endpoints = stored.coreference_attestation_value(node).endpoints
            except MalformedRecord:
                continue
            for endpoint in endpoints:
                try:
                    located = view.locate(endpoint)
                except CorpusDamaged:
                    findings.append(
                        Finding(
                            "warning",
                            "attestation-endpoint-unreachable",
                            node.id,
                            endpoint,
                            f"{node.id}: endpoint {endpoint} sits in a corpus this audit could not read whole",
                        )
                    )
                    continue
                if type(located) is Unknown:
                    findings.append(
                        Finding(
                            "warning",
                            "attestation-endpoint-unknown",
                            node.id,
                            endpoint,
                            f"{node.id}: endpoint {endpoint} is an address this epoch never observed; "
                            "the attestation names nothing the world holds or held",
                        )
                    )
        elif node.kind == "source":
            try:
                normalized = source_basis.normalized_identifiers(
                    cast(Mapping[object, object], dict(stored._source_identifiers(node)))
                )
            except IdentifierMalformed:
                continue
            for scheme, value in normalized.items():
                identifiers.setdefault((scheme, value), []).append(node.id)
    for (scheme, value), holders in sorted(identifiers.items()):
        distinct = sorted(set(holders))
        if len(distinct) > 1:
            findings.append(
                Finding(
                    "warning",
                    "source-identifier-shared",
                    distinct[0],
                    f"{scheme}:{value}",
                    f"{distinct[0]}: shares {scheme}:{value} with {', '.join(distinct[1:])}; "
                    "precedence made these two addresses and they may be one work",
                )
            )
    from beliefs.corpus import _validated_retraction_target
    from beliefs.errors import EpochMalformed
    from beliefs.world.epoch import RetainedSnapshots

    snapshot_arms: list[tuple[str, Node]] = []
    for corpus_id, _state in published.coverage:
        if corpus_id in view.absent() or corpus_id in excluded:
            continue
        for node in view.captured_records(corpus_id):  # unmapped post-build records included
            if node.kind != "retraction":
                continue
            try:
                target = _validated_retraction_target(node)
            except ScienceError:
                continue  # shape faults are corpus_check's
            if target["arm"] == "snapshot":
                snapshot_arms.append((corpus_id, node))
    retained: Mapping[str, tuple[str, ...]] | None = None
    if snapshot_arms:  # the retained inventory is read only when something names it
        try:
            retained = RetainedSnapshots(world).retained("producer")
        except EpochMalformed as caught:
            findings.append(
                Finding(
                    "error",
                    "retained-epochs-unreadable",
                    published.packaging_identity,
                    str(caught),
                    f"{published.packaging_identity}: the retained epochs do not read whole, so "
                    f"{len(snapshot_arms)} snapshot-arm retraction(s) cannot be resolved here: {caught}",
                )
            )
    for corpus_id, node in snapshot_arms:
        if retained is None:
            break
        target = _validated_retraction_target(node)
        faults = []
        if target["subject_identity"] not in retained:
            faults.append(f"no retained epoch carries producer snapshot {target['subject_identity']}")
        elif corpus_id not in retained[target["subject_identity"]]:
            faults.append(
                f"corpus {corpus_id} is outside the coverage of producer snapshot {target['subject_identity']}"
            )
        successor = node.facets[stored.RETRACTION_FACET].get("successor")
        if successor is not None and successor not in retained:
            faults.append(f"successor {successor} is not a retained producer snapshot")
        for fault in faults:
            findings.append(Finding("error", "retraction-target-invalid", node.id, "target", f"{node.id}: {fault}"))

    opened = {published.packaging_identity: published}
    outcomes = []
    for kind in epoch_audit._KINDS:
        outcome, unreadable = reported_receipt(world, published, kind)
        outcomes.append((published.packaging_identity, kind, outcome))
        if unreadable is not None:
            findings.append(unreadable)
        finding = epoch_audit._receipt_finding(published.packaging_identity, outcome)
        if finding is not None:
            findings.append(finding)
    for verdict in epoch_audit._verdicts(opened, outcomes, ()):
        state = epoch_audit.snapshot_state(world, verdict.kind, verdict.subject_identity).state
        if state == "contradicted":
            findings.append(
                Finding(
                    "error",
                    "snapshot-contradicted",
                    verdict.subject_identity,
                    verdict.kind,
                    f"{verdict.subject_identity}: no receipt naming this {verdict.kind} subject validates "
                    "and at least one is refuted",
                )
            )
    return findings
