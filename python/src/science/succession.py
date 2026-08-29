"""Successor admission over the durable evidence (successor-admission design §4).

`admit_spec_successor` is the deriving boundary: under the root's own
operation lock it reads the chain's qualification and the corpus's
verification and assessment records, composes G4's two blocker classes,
and calls the pure core with the derived sets — never a caller-invented
one. It lives here and not in `science.spec` because the derivation needs
the log seam, which imports `corpus`, which imports `spec` (design §2).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path

from nodes.core.errors import CollisionError
from nodes.core.node import Node
from nodes.core.structural_index import Index

from science import stored
from science import verification as verification_module
from science.errors import AdmissionEvidenceRefused, MalformedRecord, RecordUndecodable
from science.intents import shapes
from science.intents.evidence import decode_node
from science.intents.reduce import (
    IntentQualification,
    StateFacts,
    reduce_chain,
)
from science.record import AssessmentValue
from science.report import AssessmentRunIntent
from science.spec import FrozenSpec, SuccessorAdmitted, SuccessorRefused, admit_successor
from science.verification import Verification
from science.world.logmodel import IntentEntryView, WellFormedView
from science.world.records import RECORD_NAMESPACES, CapturedSurface, capture_surface
from science.world.verify import LogSeam

__all__ = ["admit_spec_successor"]

EVIDENCE_NAMESPACES = ("verification", "assessment")
"""The two namespaces class 1a reads beside cut 11's three. Module-level, not
exported: the tests import it by name."""

REASONS = (
    "root unreadable",
    "chain not well-formed",
    "namespace uninspectable",
    "verification unreadable",
    "assessment unreadable",
    "verification oversized",
    "verification edge cardinality",
    "verification target unreadable",
    "verification target mismatch",
    "record collision",
    "qualification unresolved for the superseded spec",
)
"""The closed reason set of `AdmissionEvidenceRefused` (design §5). Module-level,
not exported: the design's public surface is the one entrypoint."""


def admit_spec_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    *,
    seam: LogSeam,
    root: Path,
) -> SuccessorAdmitted | SuccessorRefused:
    """Admit or refuse `candidate` as a successor to `superseded`, over the
    evidence beneath `root` — one hold, one pinned order (design §4.2)."""
    root = Path(root)
    try:
        root = root.resolve()
    except (OSError, RuntimeError, ValueError) as failure:
        raise AdmissionEvidenceRefused("root unreadable", str(root)) from failure
    _require_openable_directory(root)
    with seam.corpus_lock(root):
        view = seam.inspect_registered(root)
        if type(view) is not WellFormedView:
            raise AdmissionEvidenceRefused("chain not well-formed", str(root))
        surface = capture_surface(root, RECORD_NAMESPACES + EVIDENCE_NAMESPACES)
        if surface.uninspectable:
            raise AdmissionEvidenceRefused("namespace uninspectable", surface.uninspectable[0])
        records = dict(surface.records)
        unfinished, report_failures = _chain_classes(
            superseded.identity, view, records, seam.state_facts
        )
        recorded_failures = _recorded_failures(surface, records) | report_failures
        return admit_successor(candidate, superseded, recorded_failures, unfinished)


def _require_openable_directory(root: Path) -> None:
    try:
        fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as failure:
        raise AdmissionEvidenceRefused("root unreadable", str(root)) from failure
    with suppress(OSError):
        os.close(fd)


# --- class 2 and class 1b, from the chain ----------------------------------------


def _chain_classes(
    superseded_identity: str,
    view: WellFormedView,
    records: Mapping[str, bytes],
    state_facts: StateFacts,
) -> tuple[frozenset[str], frozenset[str]]:
    """Unfinished attempts and run-attempt-recorded failures from the chain's
    qualification, with the unresolved gate (design §4.3, §4.4 1b)."""
    qualified = reduce_chain(view.entries, records, state_facts=state_facts)
    rows = qualified.rows
    matched_reductions = dict(qualified.matched_reductions)
    intents = {entry.digest: entry for entry in view.entries if type(entry) is IntentEntryView}
    unfinished: set[str] = set()
    failures: set[str] = set()
    for row in rows:
        if row.shape != "assessment-run":
            continue
        spec_identity = _spec_identity(row, intents[row.digest])
        if row.status == "unresolvable":
            if spec_identity == superseded_identity:
                raise AdmissionEvidenceRefused(
                    "qualification unresolved for the superseded spec", row.digest
                )
        elif row.status == "attempt-without-recorded-outcome":
            unfinished.add(spec_identity)
        elif row.status == "matched":
            assert row.fulfilled_by is not None, "a matched row names its registration"
            reduction = matched_reductions[row.fulfilled_by]
            assert reduction.match is not None, "the reducer called this registration matched"
            _, evidence = reduction.match
            if type(evidence) is shapes.ReportEvidence and evidence.operation == "run-attempt":
                failures.add(spec_identity)
    return frozenset(unfinished), frozenset(failures)


def _spec_identity(row: IntentQualification, entry: IntentEntryView) -> str:
    decoded = shapes.decode_intent(row.digest, entry.payload)
    assert type(decoded) is shapes.DecodedIntent, "an assessment-run row decodes"
    value = decoded.value
    assert isinstance(value, AssessmentRunIntent), "an assessment-run row carries a spec"
    return value.spec_identity


# --- class 1a, from the verification evidence ---------------------------------------


def _recorded_failures(surface: CapturedSurface, records: Mapping[str, bytes]) -> frozenset[str]:
    """The specs of every active, coherent, failing verification (design
    §4.4 steps 1–5, §4.5)."""
    _refuse_unreadable(surface)
    nodes = _decoded_evidence(records)
    verifications, assessments = _typed(nodes)
    index = _index(nodes)
    withheld = _withheld_ids(surface)
    for ref in withheld:
        if index.resolve_uid(ref) is not None:
            raise AdmissionEvidenceRefused("record collision", ref)

    failing = {path: value for path, value in verifications.items() if value.verdict == "failed"}
    blockers = {value.ref for value in failing.values()} | {
        ref for ref in withheld if ref.startswith("verification:")
    }
    gated = {
        path: value
        for path, value in verifications.items()
        if path in failing or value.supersedes in blockers
    }
    by_uid = {node.uid: path for path, node in nodes.items()}
    targets: dict[str, AssessmentValue] = {}
    for path, value in gated.items():
        edges = [
            edge
            for edge in index.outbound_edges(nodes[path].uid)
            if edge.relation.predicate == stored.VERIFIES
        ]
        if len(edges) != 1:
            raise AdmissionEvidenceRefused("verification edge cardinality", path)
        edge = edges[0]
        if edge.relation.target in withheld:
            raise AdmissionEvidenceRefused("verification target unreadable", path)
        target_path = by_uid.get(edge.target_uid) if edge.target_uid is not None else None
        if target_path is None or target_path not in assessments:
            raise AdmissionEvidenceRefused("verification target unreadable", path)
        target = assessments[target_path]
        if target.identity() != value.assessment:
            raise AdmissionEvidenceRefused("verification target mismatch", path)
        targets[path] = target

    for ref, path in withheld.items():
        if ref.startswith("verification:") and not any(
            value.supersedes == ref for value in gated.values()
        ):
            raise AdmissionEvidenceRefused("verification oversized", path)

    active = {value.ref for value in verification_module.active(tuple(verifications.values()))}
    return frozenset(targets[path].spec for path, value in failing.items() if value.ref in active)


def _refuse_unreadable(surface: CapturedSurface) -> None:
    for path in surface.unreadable:
        kind = path.partition("/")[0]
        if kind in EVIDENCE_NAMESPACES:
            raise AdmissionEvidenceRefused(f"{kind} unreadable", path)


def _decoded_evidence(records: Mapping[str, bytes]) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for path in sorted(records):
        kind = path.partition("/")[0]
        if kind not in EVIDENCE_NAMESPACES:
            continue
        try:
            nodes[path] = decode_node(path, records[path])
        except RecordUndecodable as caught:
            raise AdmissionEvidenceRefused(f"{kind} unreadable", path) from caught
    return nodes


def _typed(nodes: Mapping[str, Node]) -> tuple[dict[str, Verification], dict[str, AssessmentValue]]:
    verifications: dict[str, Verification] = {}
    assessments: dict[str, AssessmentValue] = {}
    for path, node in nodes.items():
        try:
            if node.kind == "verification":
                verifications[path] = stored.verification_value(node)
            else:
                assessments[path] = stored.assessment_value(node)
        except MalformedRecord as caught:
            raise AdmissionEvidenceRefused(f"{node.kind} unreadable", path) from caught
    return verifications, assessments


def _index(nodes: Mapping[str, Node]) -> Index:
    """`Index.build`'s loop, admitting nodes in path order so the colliding
    record is the one named (design §5: the ref is the colliding id)."""
    index = Index()
    for path in sorted(nodes):
        node = nodes[path]
        try:
            index.assert_addable(node)
        except CollisionError as caught:
            raise AdmissionEvidenceRefused("record collision", node.id) from caught
        index.upsert(node)
    return index


def _withheld_ids(surface: CapturedSurface) -> dict[str, str]:
    """`kind:slug` for every withheld evidence path — the id the layout rule
    determines from the path alone (design §4.5)."""
    ids: dict[str, str] = {}
    for path in surface.withheld:
        kind, _, rest = path.partition("/")
        if kind in EVIDENCE_NAMESPACES and rest.endswith(".md"):
            ids[f"{kind}:{rest[:-3]}"] = path
    return ids
