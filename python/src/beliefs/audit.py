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
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentValue, build_assessment
from beliefs.corpus import (
    Finding,
    ReadView,
    _absence_of,
    _CapturedCheckView,
    _ImportView,
    _manifest_findings,
    _producers_of,
    _record_findings,
    corpus_check,
)
from beliefs.errors import (
    CorpusDamaged,
    IdentityError,
    MalformedRecord,
    PreGrammarAssessment,
    PreGrammarSpec,
    RecordError,
    RuleUnbound,
    SemanticHashMissing,
    SemanticHashStale,
)
from beliefs.evidence import NO_EVIDENCE, DerivationEvidence, DerivationOutcome
from beliefs.profile import ProfileSpec
from beliefs.recipe import RunClosure
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
    "check_composite",
    "check_lineage_basis",
    "check_spec_target",
    "check_supersedes_kinds",
    "check_verification",
    "stored_specs",
]


MALFORMEDNESS_CODES = frozenset(
    {"semantic-hash-missing", "semantic-hash-stale", "coordination-facet-malformed", "derivation-malformed", "facet-payload-malformed"}
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
    }
)
"""Slice 3 design §5.5's closed set, beside `MALFORMEDNESS_CODES`."""


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
        name
        for name in _COMPARABLE_ASSESSMENT_MEMBERS
        if getattr(stored_value, name) != getattr(derived, name)
    ]
    if stored_value.run != derived.run:
        disagreements.append("run")
    if stored_value.spec != derived.spec:
        disagreements.append("spec")
    return sorted(disagreements)


def check_lineage_basis(view: ReadView | WorldReadView, node: Node) -> DerivationOutcome:
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


def check_spec_target(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """The boundary's estimand-target comparison, over a stored record (§7.2)."""
    from beliefs.decode import claim_from_stored
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
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True, reason="",
        contradiction=Finding(severity="error", code="spec-target-contradicted", ref=node.id, detail=",".join(disagreements),
                              message=f"{node.id}: the spec's estimand does not answer the claim its target carries"),
    )


def check_composite(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """Design §4.3: the boundary's four steps over the stored record, reported
    rather than raised. Form only — the audit holds no snapshot."""
    from beliefs import composite as composite_module
    from beliefs.errors import CompositeError
    from beliefs.world.view import WorldReadView

    def contradiction(code: str, detail: str) -> DerivationOutcome:
        return DerivationOutcome(
            checked=True,
            reason="",
            contradiction=Finding(severity="error", code=code, ref=node.id, detail=detail, message=f"{node.id}: {detail}"),
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


def check_supersedes_kinds(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> Finding | None:
    """Design §3.1's `same_kind` rule, under audit: a raw-written edge the
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
            return Finding(severity="error", code="supersedes-cross-kind", ref=node.id, detail=detail, message=f"{node.id}: {detail}")
    return None


def check_analysis_spec(node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """A stored spec restores or is malformed; `audit_corpus` reports the
    latter as `derivation-malformed` under the catch R11 already has."""
    stored.analysis_spec_value(node, profile=profile)
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def stored_specs(
    view: ReadView | _ImportView | WorldReadView, *, profile: ProfileSpec
) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]:
    """Every restorable stored spec keyed by identity, and one
    `derivation-malformed` finding per record that does not restore — the
    two halves travel together so a false spec never vanishes into an
    unchecked derivation (design decision 15). A pre-grammar spec is named by
    its own code (`spec-pre-grammar`), never folded into `derivation-malformed`
    (decision 10)."""
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
                    message=f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)",
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
            else:
                continue
        except PreGrammarSpec as refused:
            findings.append(
                Finding(severity="error", code="spec-pre-grammar", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)")
            )
            continue
        except PreGrammarAssessment as refused:
            findings.append(
                Finding(severity="error", code="assessment-pre-grammar", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar assessment; the corpus was not recreated (decision 10)")
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
    return None


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
    excluded: set[str] = set()
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
            continue
        findings.extend(
            _record_findings(_CapturedCheckView(view.captured_records(corpus_id)), profile, scope, disagreeing)
        )
        malformed[corpus_id] = {finding.ref for finding in findings if finding.code in MALFORMEDNESS_CODES}
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
    for node in view.iter_stored():
        corpus_id = view.corpus_of(node.id)
        assert corpus_id is not None
        if corpus_id in excluded or node.id in malformed.get(corpus_id, set()):
            continue
        try:
            cross = check_supersedes_kinds(view, node, profile=profile)
            if cross is not None:
                corpora[corpus_id].append(cross)
            outcome = _recompute(view, node, evidence, profile)
        except CorpusDamaged as unreachable:
            corpora[corpus_id].append(
                Finding(
                    "warning",
                    "derivation-unreachable",
                    node.id,
                    unreachable.corpus_id,
                    f"{node.id}: its recomputation reaches {unreachable.corpus_id}, which this audit could not read whole",
                )
            )
            continue
        except PreGrammarSpec as refused:
            corpora[corpus_id].append(
                Finding("error", "spec-pre-grammar", node.id, str(refused), f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)")
            )
            continue
        except PreGrammarAssessment as refused:
            corpora[corpus_id].append(
                Finding("error", "assessment-pre-grammar", node.id, str(refused), f"{node.id}: pre-grammar assessment; the corpus was not recreated (decision 10)")
            )
            continue
        except RecordError as refused:
            corpora[corpus_id].append(
                Finding(
                    "error",
                    "derivation-malformed",
                    node.id,
                    str(refused),
                    f"{node.id}: the members a derivation recomputation reads are malformed",
                )
            )
            continue
        if outcome is not None and outcome.contradiction is not None:
            corpora[corpus_id].append(outcome.contradiction)
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
    from beliefs.world.read import Unknown, validate_receipt

    findings: list[Finding] = []
    identifiers: dict[tuple[str, str], list[str]] = {}
    for node in view.iter_stored():
        corpus_id = view.corpus_of(node.id)
        if corpus_id in excluded or node.id in malformed.get(corpus_id or "", set()):
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
    opened = {published.packaging_identity: published}
    outcomes = []
    for kind in epoch_audit._KINDS:
        outcome = validate_receipt(world, published, kind)
        outcomes.append((published.packaging_identity, kind, outcome))
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
