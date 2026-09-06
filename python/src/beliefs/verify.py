"""Derived run verification values with their scope evidence embedded inline.

The ``build_verification`` constructor owns the comparison report, equivalence verdict,
scope, and assessment edge. Explicit import and audit validation remain
deferred with the store and world resolver (cut 3 §4.2, R19).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeAlias, cast, final

from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import record, stored
from beliefs.errors import MalformedClosure, MalformedRecord, MixedShapes, NotAnAssessmentVerification, RuleUnbound
from beliefs.identity import v1
from beliefs.recipe import RunClosure
from beliefs.replay import (
    CodeLineageCertification,
    EquivalenceImplementation,
    conformance,
    derive_scope,
)
from beliefs.report import ActReport, _entry_facet, cite
from beliefs.sealed import sealed
from beliefs.spec import DATASET_EQUIVALENCE_RULE, FrozenSpec
from beliefs.verification import SCOPES, VERDICTS, Verification

__all__ = [
    "COMPARISON_REPORT_DOMAIN",
    "RUN_VERIFICATION_DOMAIN",
    "AssessmentVerification",
    "ComparisonReport",
    "DatasetProductionVerification",
    "EmbeddedCitation",
    "RunVerification",
    "StoredVerification",
    "active_verifications",
    "admission_record",
    "build_verification",
    "decode_verification",
    "publication_node",
]

COMPARISON_REPORT_DOMAIN = "science.comparison-report.v1"
RUN_VERIFICATION_DOMAIN = "science.run-verification.v1"


def _require_str(value: object, where: str) -> None:
    if type(value) is not str:
        raise MalformedRecord(f"{where} must be a string")


def _require_strings(value: object, where: str) -> None:
    if type(value) is not tuple or any(type(member) is not str for member in value):
        raise MalformedRecord(f"{where} must be a tuple of strings")


def _require_pairs(value: object, where: str) -> None:
    if type(value) is not tuple or any(
        type(pair) is not tuple or len(pair) != 2 or any(type(member) is not str for member in pair) for pair in value
    ):
        raise MalformedRecord(f"{where} must be a tuple of string pairs")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(member) for key, member in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(member) for member in value)
    return value


def _project(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _project(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_project(member) for member in value]
    return value


@sealed
@final
@dataclass(frozen=True)
class EmbeddedCitation:
    report_ref: str
    index: int
    content: Mapping[str, object]

    def __post_init__(self) -> None:
        _require_str(self.report_ref, "embedded citation report ref")
        if type(self.index) is not int or self.index < 0:
            raise MalformedRecord("an embedded citation index must be a zero-based unsigned integer")
        if not isinstance(self.content, Mapping):
            raise MalformedRecord("embedded citation content must be a mapping")
        content = cast(Mapping[str, object], _freeze(self.content))
        v1.encode(_project(content))
        object.__setattr__(self, "content", content)


def _certification_projection(certification: CodeLineageCertification) -> dict[str, object]:
    return {
        "rationale": certification.rationale,
        "attribution": certification.attribution,
    }


def _citation_projection(citation: EmbeddedCitation) -> dict[str, object]:
    return {
        "report_ref": citation.report_ref,
        "index": citation.index,
        "content": _project(citation.content),
    }


@sealed
@final
@dataclass(frozen=True, init=False)
class ComparisonReport:
    original_conformance: str
    replay_conformance: str
    receipts: tuple[str, str]
    rule_bindings: tuple[tuple[str, str], ...]
    certification: CodeLineageCertification | None
    citation: EmbeddedCitation | None
    diagnostics: tuple[str, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("ComparisonReport values are minted only by build_verification and restored by decode_verification")

    def projection(self) -> dict[str, object]:
        """The canonical mapping `identity()` digests — and what a published
        verification stores under `report` (design §4.1)."""
        projection: dict[str, object] = {
            "original_conformance": self.original_conformance,
            "replay_conformance": self.replay_conformance,
            "receipts": list(self.receipts),
            "rule_bindings": [list(pair) for pair in self.rule_bindings],
            "diagnostics": list(self.diagnostics),
        }
        if self.certification is not None:
            projection["certification"] = _certification_projection(self.certification)
        if self.citation is not None:
            projection["citation"] = _citation_projection(self.citation)
        return projection

    def identity(self) -> str:
        return v1.digest(COMPARISON_REPORT_DOMAIN, self.projection())


def _mint_comparison_report(
    *,
    original_conformance: str,
    replay_conformance: str,
    receipts: tuple[str, str],
    rule_bindings: tuple[tuple[str, str], ...],
    certification: CodeLineageCertification | None,
    citation: EmbeddedCitation | None,
    diagnostics: tuple[str, ...],
) -> ComparisonReport:
    _require_str(original_conformance, "original conformance")
    _require_str(replay_conformance, "replay conformance")
    _require_strings(receipts, "comparison report receipts")
    if len(receipts) != 2:
        raise MalformedRecord("comparison report receipts must contain exactly two identities")
    _require_pairs(rule_bindings, "comparison report rule bindings")
    _require_strings(diagnostics, "comparison report diagnostics")
    if certification is not None and type(certification) is not CodeLineageCertification:
        raise MalformedRecord("comparison report certification must be a code-lineage certification")
    if citation is not None and type(citation) is not EmbeddedCitation:
        raise MalformedRecord("comparison report citation must be an EmbeddedCitation")
    report = object.__new__(ComparisonReport)
    for name, value in (
        ("original_conformance", original_conformance),
        ("replay_conformance", replay_conformance),
        ("receipts", receipts),
        ("rule_bindings", rule_bindings),
        ("certification", certification),
        ("citation", citation),
        ("diagnostics", diagnostics),
    ):
        object.__setattr__(report, name, value)
    return report


def _validate_verification(members: Mapping[str, object]) -> None:
    for name in ("original", "replayed", "rule", "scope_rule", "scope", "verdict"):
        _require_str(members[name], f"verification {name}")
    if "assessment" in members:
        _require_str(members["assessment"], "verification assessment")
    if type(members["report"]) is not ComparisonReport:
        raise MalformedRecord("verification report must be a ComparisonReport")
    if members["scope"] not in SCOPES:
        raise MalformedRecord(f"scope {members['scope']!r} is outside the closed set {SCOPES}")
    if members["verdict"] not in VERDICTS:
        raise MalformedRecord(f"verdict {members['verdict']!r} is outside the closed set {VERDICTS}")
    supersedes = members["supersedes"]
    if supersedes is not None:
        _require_str(supersedes, "verification supersedes")


def _basis(members: dict[str, object]) -> dict[str, object]:
    report = cast(ComparisonReport, members["report"])
    basis: dict[str, object] = {
        "original": members["original"],
        "replayed": members["replayed"],
    }
    if "assessment" in members:
        basis["assessment"] = members["assessment"]
    basis |= {
        "rule": members["rule"],
        "report": report.identity(),
        "scope_rule": members["scope_rule"],
        "scope": members["scope"],
        "verdict": members["verdict"],
    }
    if members["supersedes"] is not None:
        basis["supersedes"] = members["supersedes"]
    return basis


@sealed
@final
@dataclass(frozen=True, init=False)
class AssessmentVerification:
    original: str
    replayed: str
    assessment: str
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("AssessmentVerification values are minted only by build_verification")

    def basis(self) -> dict[str, object]:
        return _basis(vars(self))

    def identity(self) -> str:
        return v1.digest(RUN_VERIFICATION_DOMAIN, self.basis())


@sealed
@final
@dataclass(frozen=True, init=False)
class DatasetProductionVerification:
    original: str
    replayed: str
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("DatasetProductionVerification values are minted only by build_verification")

    def basis(self) -> dict[str, object]:
        return _basis(vars(self))

    def identity(self) -> str:
        return v1.digest(RUN_VERIFICATION_DOMAIN, self.basis())


RunVerification: TypeAlias = AssessmentVerification | DatasetProductionVerification


@sealed
@final
@dataclass(frozen=True, init=False)
class StoredVerification:
    """A published verification read back: the same basis as the derived
    value, minted only by `decode_verification` after the record's id
    recomputes from its members (design §4.2). Distinct from the derived
    types on purpose — R19 admits no constructor that accepts a report — and
    closed the same way they are."""

    original: str
    replayed: str
    assessment: str | None
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("StoredVerification values are minted only by decode_verification")

    def basis(self) -> dict[str, object]:
        members: dict[str, object] = {
            "original": self.original,
            "replayed": self.replayed,
            "rule": self.rule,
            "report": self.report,
            "scope_rule": self.scope_rule,
            "scope": self.scope,
            "verdict": self.verdict,
            "supersedes": self.supersedes,
        }
        if self.assessment is not None:
            members["assessment"] = self.assessment
        return _basis(members)

    def identity(self) -> str:
        return v1.digest(RUN_VERIFICATION_DOMAIN, self.basis())


def _mint_stored_verification(*, assessment: str | None, **members: object) -> StoredVerification:
    """The reader's private mint: `_validate_verification` over the same
    member set the derived mint validates, then the sealed value."""
    checked: dict[str, object] = dict(members)
    if assessment is not None:
        checked["assessment"] = assessment
    _validate_verification(checked)
    value = object.__new__(StoredVerification)
    for name, member in (*members.items(), ("assessment", assessment)):
        object.__setattr__(value, name, member)
    return value


_REPORT_REQUIRED = frozenset({"original_conformance", "replay_conformance", "receipts", "rule_bindings", "diagnostics"})
_REPORT_OPTIONAL = frozenset({"certification", "citation"})
_PUBLISHED_REQUIRED = frozenset({"scope", "verdict", "derivation", "rule", "scope_rule", "report"})
_PUBLISHED_OPTIONAL = frozenset({"assessment", "supersedes"})


def _string_list(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(type(member) is not str for member in value):
        raise MalformedRecord(f"{where} must be a list of strings")
    return tuple(value)


def _restore_report(node_id: str, member: object) -> ComparisonReport:
    if not isinstance(member, Mapping) or not _REPORT_REQUIRED <= set(member) <= _REPORT_REQUIRED | _REPORT_OPTIONAL:
        raise MalformedRecord(f"{node_id}: a report member carries exactly the comparison report's projection")
    bindings = member["rule_bindings"]
    if not isinstance(bindings, list) or any(
        not isinstance(pair, list) or len(pair) != 2 or any(type(half) is not str for half in pair) for pair in bindings
    ):
        raise MalformedRecord(f"{node_id}: report rule bindings must be a list of string pairs")
    certification = None
    if "certification" in member:
        claim = member["certification"]
        if not isinstance(claim, Mapping) or set(claim) != {"rationale", "attribution"}:
            raise MalformedRecord(f"{node_id}: a report certification names exactly rationale and attribution")
        certification = CodeLineageCertification(rationale=claim["rationale"], attribution=claim["attribution"])
    citation = None
    if "citation" in member:
        cited = member["citation"]
        if not isinstance(cited, Mapping) or set(cited) != {"report_ref", "index", "content"}:
            raise MalformedRecord(f"{node_id}: a report citation names exactly report_ref, index and content")
        citation = EmbeddedCitation(report_ref=cited["report_ref"], index=cited["index"], content=cited["content"])
    receipts = _string_list(member["receipts"], f"{node_id}: report receipts")
    if len(receipts) != 2:
        raise MalformedRecord(f"{node_id}: report receipts must contain exactly two identities")
    return _mint_comparison_report(
        original_conformance=member["original_conformance"],
        replay_conformance=member["replay_conformance"],
        # Narrowed by the length check above: a real 2-tuple literal, not a
        # cast, is what gives `receipts` its `tuple[str, str]` type here.
        receipts=(receipts[0], receipts[1]),
        rule_bindings=tuple((pair[0], pair[1]) for pair in bindings),
        certification=certification,
        citation=citation,
        diagnostics=_string_list(member["diagnostics"], f"{node_id}: report diagnostics"),
    )


def decode_verification(node: Node) -> StoredVerification | None:
    """A published verification read back, or `None` for one that carries no
    report (cut 18 ruling R2: not malformed, only unchecked for scope). A
    present member that is malformed — a null derivation included — or an id
    that does not recompute from the members is refused, never repaired
    (M11). Pure over the node."""
    if node.kind != "verification":
        raise MalformedRecord(f"{node.id}: not a verification record")
    facet = node.facets.get(stored.VERIFICATION_FACET)
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{node.id}: a verification carries a {stored.VERIFICATION_FACET!r} facet")
    if "report" not in facet:
        return None
    keys = set(facet)
    if not _PUBLISHED_REQUIRED <= keys or not keys <= _PUBLISHED_REQUIRED | _PUBLISHED_OPTIONAL:
        raise MalformedRecord(f"{node.id}: a published verification carries exactly its basis members")
    if facet["derivation"] is None:
        raise MalformedRecord(f"{node.id}: a published verification names its derivation")
    derivation = stored.verification_derivation(node)
    if derivation is None:
        raise MalformedRecord(f"{node.id}: a published verification names its derivation")
    edges = [relation for relation in node.relations if relation.predicate == stored.VERIFIES]
    if len(edges) > 1:
        raise MalformedRecord(f"{node.id}: a verification carries at most one verifies edge")
    if ("assessment" in facet) != bool(edges):
        raise MalformedRecord(f"{node.id}: the assessment member and the verifies edge are present together or not at all")
    for name in ("rule", "scope_rule", "scope", "verdict"):
        if type(facet[name]) is not str:
            raise MalformedRecord(f"{node.id}: verification {name} must be a string")
    assessment = facet.get("assessment")
    if "assessment" in facet and type(assessment) is not str:
        raise MalformedRecord(f"{node.id}: verification assessment must be a string")
    supersedes = facet.get("supersedes")
    if supersedes is not None:
        supersedes = stored.local_id("verification", supersedes)
    decoded = _mint_stored_verification(
        assessment=assessment,
        original=stored.local_id("run", derivation[0]),
        replayed=stored.local_id("run", derivation[1]),
        rule=facet["rule"],
        report=_restore_report(node.id, facet["report"]),
        scope_rule=facet["scope_rule"],
        scope=facet["scope"],
        verdict=facet["verdict"],
        supersedes=supersedes,
    )
    if decoded.identity() != stored.local_id("verification", node.id):
        raise MalformedRecord(f"{node.id}: the recomputed identity is not the record id")
    return decoded


def publication_node(derived: RunVerification, *, assessment_ref: str | None = None) -> Node:
    """The stored record of a derived verification, total over both shapes
    (design §5.1). Pure: reads no view, holds no lock; `decode_verification`
    over the result restores the same basis."""
    if type(derived) is AssessmentVerification:
        if assessment_ref is None:
            raise MalformedRecord("an assessment verification publishes against its assessment's corpus ref")
        stored.local_id("assessment", assessment_ref)
        title = f"verification of {assessment_ref}"
    elif type(derived) is DatasetProductionVerification:
        if assessment_ref is not None:
            raise MalformedRecord("a dataset-production verification has no assessment to verify")
        title = "dataset-production verification"
    else:
        raise MalformedRecord("publication_node requires a derived RunVerification")
    facet: dict[str, object] = {
        "scope": derived.scope,
        "verdict": derived.verdict,
        "derivation": {
            "original": stored.typed_ref("run", derived.original),
            "replayed": stored.typed_ref("run", derived.replayed),
        },
        "rule": derived.rule,
        "scope_rule": derived.scope_rule,
        "report": derived.report.projection(),
    }
    if type(derived) is AssessmentVerification:
        facet["assessment"] = derived.assessment
    if derived.supersedes is not None:
        facet["supersedes"] = stored.typed_ref("verification", derived.supersedes)
    identity = derived.identity()
    relations: list[Relation] = []
    if assessment_ref is not None:
        relations.append(Relation(source=f"verification:{identity}", predicate=stored.VERIFIES, target=assessment_ref))
    return stored.governed_node("verification", identity, title, {stored.VERIFICATION_FACET: facet}, relations)


def _mint_verification(
    *,
    original: str,
    replayed: str,
    assessment: str | None,
    rule: str,
    report: ComparisonReport,
    scope_rule: str,
    scope: str,
    verdict: str,
    supersedes: str | None = None,
) -> RunVerification:
    members: dict[str, object] = {
        "original": original,
        "replayed": replayed,
        "rule": rule,
        "report": report,
        "scope_rule": scope_rule,
        "scope": scope,
        "verdict": verdict,
        "supersedes": supersedes,
    }
    verification_type: type[AssessmentVerification | DatasetProductionVerification]
    if assessment is None:
        verification_type = DatasetProductionVerification
    else:
        members["assessment"] = assessment
        verification_type = AssessmentVerification
    _validate_verification(members)
    verification = object.__new__(verification_type)
    for name, value in members.items():
        object.__setattr__(verification, name, value)
    return verification


def active_verifications(verifications: tuple[RunVerification, ...]) -> tuple[RunVerification, ...]:
    superseded = {verification.supersedes for verification in verifications if verification.supersedes is not None}
    return tuple(verification for verification in verifications if verification.identity() not in superseded)


def admission_record(derived: AssessmentVerification) -> Verification:
    """The total projection from a derived assessment verification to the
    record `admit()` and belief evaluation read (design §7.2). No
    caller-supplied field. A production verification has no assessment to
    admit and is refused early."""
    if type(derived) is not AssessmentVerification:
        raise NotAnAssessmentVerification(f"{type(derived).__name__} has no assessment to admit")
    return Verification(
        ref=derived.identity(),
        assessment=derived.assessment,
        scope=derived.scope,
        verdict=derived.verdict,
        supersedes=derived.supersedes,
    )


def _job_diagnostics(original: RunClosure, replayed: RunClosure) -> tuple[str, ...]:
    left = {job.job_key() for job in original.occurrence.trace}
    right = {job.job_key() for job in replayed.occurrence.trace}
    if left == right:
        return ()
    return (f"job-set differs: original={sorted(left)!r}; replayed={sorted(right)!r}",)


def _resolve_rule(
    original: RunClosure,
    *,
    specs: Mapping[str, FrozenSpec],
    held_rules: Mapping[str, EquivalenceImplementation],
) -> tuple[str, str, EquivalenceImplementation, FrozenSpec | None]:
    spec = None
    if original.recipe.shape == "assessment":
        try:
            spec = specs[cast(str, original.recipe.spec_identity)]
        except KeyError as error:
            raise RuleUnbound("the original run's frozen spec is not held") from error
        if type(spec) is not FrozenSpec or spec.identity != original.recipe.spec_identity:
            raise RuleUnbound("the held spec does not match the original run's frozen spec")
        rule = spec.equivalence_rule
    else:
        rule = DATASET_EQUIVALENCE_RULE

    try:
        implementation_identity = dict(original.recipe.rule_bindings)[rule]
        implementation = held_rules[implementation_identity]
    except KeyError as error:
        raise RuleUnbound(f"the original recipe's implementation for {rule!r} is not held") from error
    if type(implementation) is not EquivalenceImplementation or implementation.identity != implementation_identity:
        raise RuleUnbound(f"the held implementation does not match {implementation_identity!r}")
    return rule, implementation_identity, implementation, spec


def build_verification(
    original: RunClosure,
    replayed: RunClosure,
    *,
    specs: Mapping[str, FrozenSpec],
    held_rules: Mapping[str, EquivalenceImplementation],
    contract_identity: str,
    epoch: str,
    certification: CodeLineageCertification | None = None,
    citation: tuple[ActReport, int] | None = None,
) -> RunVerification:
    """Derive a verification from the selected records available in this slice.

    ``contract_identity`` and ``epoch`` select certification discovery at the
    future world/store seam. That seam is deferred here, and packaging
    selection is deliberately absent from both derived value shapes (W5).
    """
    if type(original) is not RunClosure or type(replayed) is not RunClosure:
        raise MalformedClosure("build_verification requires two RunClosure values")
    if original.recipe.shape != replayed.recipe.shape:
        raise MixedShapes("one run is assessment-shaped and the other is dataset-production-shaped")
    _require_str(contract_identity, "verification contract identity")
    _require_str(epoch, "verification epoch")

    rule, implementation_identity, implementation, spec = _resolve_rule(original, specs=specs, held_rules=held_rules)
    verdict = implementation.evaluate(original.result, replayed.result)
    if verdict not in VERDICTS:
        raise MalformedRecord(f"equivalence evaluator returned {verdict!r}, outside {VERDICTS}")
    embedded_citation = None
    if citation is not None:
        published, index = citation
        entry = cite(published, index)
        embedded_citation = EmbeddedCitation(
            report_ref=published.identity(),
            index=index,
            content=_entry_facet(entry),
        )
    comparison = _mint_comparison_report(
        original_conformance=conformance(original),
        replay_conformance=conformance(replayed),
        receipts=(original.occurrence.receipt.identity(), replayed.occurrence.receipt.identity()),
        rule_bindings=((rule, implementation_identity),),
        certification=certification,
        citation=embedded_citation,
        diagnostics=_job_diagnostics(original, replayed),
    )
    common = {
        "original": original.address(),
        "replayed": replayed.address(),
        "rule": rule,
        "report": comparison,
        "scope_rule": original.recipe.boundary_policy.scope_rule,
        "scope": derive_scope(original, replayed, certification=certification),
        "verdict": verdict,
    }
    if spec is None:
        return _mint_verification(assessment=None, supersedes=None, **common)
    assessment = v1.digest(
        record.ASSESSMENT_DOMAIN,
        {
            "spec": spec.identity,
            "run": original.address(),
            "proposition": spec.target,
        },
    )
    return _mint_verification(assessment=assessment, supersedes=None, **common)
