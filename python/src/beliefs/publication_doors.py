"""The publish doors (publication-records design §6): step 0 appends the
evidence-bearing intent; step 8 commits the binding revision with its report,
or the refusal report alone. Neither has a public route."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.frontmatter import node_from_bytes
from nodes.core.node import Node

from beliefs import boundary, stored
from beliefs.coordination import (
    Anchor,
    ChainBound,
    CoordinationAddress,
    CoordinationRefused,
    CoordinationRevision,
    MomentSeam,
    PositionRefused,
    bounds,
    present_records,
    standing_at,
)
from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import LogEvidenceRefused, MalformedRecord, PublicationRefused, ValidationRefused
from beliefs.intents import shapes
from beliefs.intents.publish import Destination, PublishIntent, decode_publish_intent, encode_publish_intent
from beliefs.publication import BINDING_KIND, binding_address, binding_record
from beliefs.report import (
    ActReport,
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    PublicationBindingEntry,
)
from beliefs.runrecord import OperationPort
from beliefs.world.logmodel import AbsentView, IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView

__all__ = [
    "PUBLISH_INSTRUMENT",
    "BindingOutcome",
    "OpenedPublication",
    "marker_tips_at",
]

PUBLISH_INSTRUMENT = "beliefs.publish"
"""The one instrument every publish report names; its observer is the intent's actor."""


@dataclass(frozen=True)
class OpenedPublication:
    intent: PublishIntent
    digest: str  # the intent entry's digest: its position in the written root


@dataclass(frozen=True)
class BindingOutcome:
    report: ActReport
    binding: Node | None  # present iff the outcome is BindingBound


def _reports_at(
    bound: ChainBound, view: CoordinationAddress, destination: Destination, seam: MomentSeam
) -> Iterator[tuple[PublishIntent, Mapping[str, object] | PositionRefused]]:
    """Every publish intent for (view, destination) within the bound, with the
    report its committed fulfilment created, read and matched (spec §6)."""
    entries = bound.view.entries[: bound.head + 1]
    committed = {e.registration for e in entries if type(e) is SettledEntryView and e.committed}
    fulfilments: dict[str, list[RegisteredEntryView]] = {}
    for e in entries:
        if type(e) is RegisteredEntryView and e.fulfills is not None and e.digest in committed:
            fulfilments.setdefault(e.fulfills, []).append(e)
    for entry in entries:
        if type(entry) is not IntentEntryView:
            continue
        try:
            intent = decode_publish_intent(entry.payload)
        except MalformedRecord:
            continue  # another shape's intent, or a malformed one: the audit's to report, not the fold's
        if intent.view.unpinned() != view.unpinned() or intent.destination != destination:
            continue
        found = fulfilments.get(entry.digest, [])
        if not found:
            continue
        if len(found) != 1:
            # one intent, one committed fulfilment: a second is a chain no door writes
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: intent {entry.digest} has {len(found)} committed fulfilments")
            continue
        registration = found[0]
        paths = [path for path, post in registration.final if path.startswith("act-report/") and seam.is_file(post)]
        if len(paths) != 1:
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: a publish fulfilment creates {len(paths)} reports")
            continue
        records = present_records(bound, paths[0], seam)
        if type(records) is PositionRefused:
            yield intent, records
            continue
        ((_, data),) = records
        try:
            facet = stored.act_report_facet(node_from_bytes(data))
        except (NodesValidationError, MalformedRecord) as caught:
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: {paths[0]}: {caught}")
            continue
        qualifies = shapes.mismatch(
            shapes.DecodedIntent(entry.digest, "publish", intent),
            shapes.ReportEvidence(facet["operation"], facet["event_token"]),
        )
        if qualifies is not None:
            # the audit's own qualification: a fulfilling report of the wrong kind
            # or token never folds — it refuses (user review, finding 2)
            yield intent, PositionRefused("report-unqualified", f"{bound.root}: {paths[0]}: {qualifies} for intent {entry.digest}")
            continue
        if len(facet["entries"]) != 1 or facet["entries"][0]["kind"] != "publication-binding":
            yield intent, PositionRefused("revision-malformed", f"{bound.root}: {paths[0]} is not a publish report")
            continue
        yield intent, facet["entries"][0]["outcome"]


def marker_tips_at(
    mounts: Mapping[Path, str],
    view: CoordinationAddress,
    destination: Destination,
    *,
    written: Path,
    position: str,
    anchors: Sequence[Anchor],
    seam: MomentSeam,
    binding_tips: tuple[CoordinationRevision, ...],
) -> tuple[tuple[str, str], ...] | PositionRefused:
    """`marker_tips` at the position (spec §6): the markers the present binding
    tips bind, plus the standing orphans — remotely revealed refusals no shared
    publish has since superseded."""
    found = bounds(mounts, written=written, position=position, anchors=anchors, seam=seam)
    if type(found) is PositionRefused:
        return found
    orphans: set[tuple[str, str]] = set()
    retired: set[tuple[str, str]] = set()
    for bound in found:
        for intent, outcome in _reports_at(bound, view, destination, seam):
            if type(outcome) is PositionRefused:
                return outcome
            shared = outcome["type"] == "bound" or outcome.get("remotely_revealed") is True
            if outcome["type"] != "bound" and outcome.get("remotely_revealed") is True:
                orphans.add((str(outcome["corpus_id"]), str(outcome["marker"])))
            if shared:
                retired.update(intent.marker_tips)
    bound_markers = {
        (revision.node.facets[stored.COORDINATION_FACET]["corpus_id"], revision.node.facets[stored.COORDINATION_FACET]["marker"])
        for revision in binding_tips
    }
    return tuple(sorted(bound_markers | (orphans - retired)))


def _require_the_opened_intent(view: object, opened: OpenedPublication) -> None:
    """The entry at `opened.digest` on the written root's chain is an intent
    whose payload is `opened.intent`'s encoding, byte for byte. `OpenedPublication`
    is a plain value: a guard that judged a value its position does not hold
    would commit a binding no intent recorded. A chain that is not well formed
    is `standing_at`'s to refuse as evidence."""
    if type(view) is not WellFormedView:
        return
    held = [entry for entry in view.entries if entry.digest == opened.digest]
    if len(held) != 1 or type(held[0]) is not IntentEntryView:
        raise MalformedRecord(f"the position {opened.digest} is no intent entry of the written chain")
    if held[0].payload != encode_publish_intent(opened.intent):
        raise MalformedRecord(f"the intent at {opened.digest} is not the opened publication's intent")


def _judge(
    writer: CorpusWriter, resolver: CoordinationResolver, opened: OpenedPublication, seam: MomentSeam
) -> tuple[tuple[CoordinationRevision, ...] | PositionRefused, tuple[tuple[str, str], ...] | PositionRefused | None]:
    """Both readings at the intent's own position. The engine's refusal to
    inspect a chain (`LogEvidenceRefused`) is the chain refused as evidence:
    the binding door records it as `chain-malformed`, like any evidence
    refusal, so a revealed marker still leaves its orphan (Ruling 6)."""
    intent = opened.intent
    mounts = resolver.mounted()
    written = Path(writer.root).resolve()
    address = binding_address(intent.view, intent.destination)
    try:
        # checked in the guard, before registration: a mismatch writes nothing
        _require_the_opened_intent(seam.inspect_written(written), opened)
        tips = standing_at(mounts, address, BINDING_KIND, written=written, position=opened.digest, anchors=intent.anchors, seam=seam)
        if type(tips) is PositionRefused:
            return tips, None
        markers = marker_tips_at(
            mounts, intent.view, intent.destination, written=written, position=opened.digest,
            anchors=intent.anchors, seam=seam, binding_tips=tips,
        )
    except LogEvidenceRefused as caught:
        return PositionRefused("chain-malformed", f"the engine refused to inspect a chain: {caught}"), None
    return tips, markers


def _open_publication(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    *,
    view: CoordinationAddress,
    destination: Destination,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> OpenedPublication:
    """Step 0: judge at the written root's tip under its lock, freeze the reading
    into the intent, and append it. A `LogEvidenceRefused` propagates: nothing
    is revealed and nothing written yet (Ruling 6)."""
    writer.authority.require("publish", ("publication-binding",))
    writer.authority.require("corpus-write", ("act-report",))
    profile = resolver.profile(writer.root)
    if profile is None:
        # the written root is not mounted: refused up front, not later inside `bounds`
        raise PublicationRefused("mounts-changed")
    if BINDING_KIND not in profile.coordination_kinds:
        raise ValidationRefused("publication-binding is not declared by the mounted coordination contract")
    with writer._operation:
        resolved = resolver.resolve(view.unpinned())
        if resolved is None:
            raise PublicationRefused("view-unresolved")
        if type(resolved) is CoordinationRefused:
            raise PublicationRefused("divergent-view", tips=resolved.tips)
        assert type(resolved) is Node
        mounts = resolver.mounted()
        written = Path(writer.root).resolve()
        anchors: list[Anchor] = []
        for root, corpus_id in mounts.items():
            if root == written:
                continue
            other = seam.inspect_other(root)
            if type(other) is AbsentView:
                raise PublicationRefused("chain-absent")
            if type(other) is not WellFormedView:
                raise PublicationRefused("chain-malformed")
            anchors.append(Anchor(corpus_id, other.genesis.digest, other.tip))
        anchors.sort(key=lambda anchor: anchor.corpus_id)
        own = seam.inspect_written(written)
        if type(own) is not WellFormedView:
            raise PublicationRefused("chain-absent" if type(own) is AbsentView else "chain-malformed")
        address = binding_address(view, destination)
        tips = standing_at(mounts, address, BINDING_KIND, written=written, position=own.tip, anchors=anchors, seam=seam)
        if type(tips) is PositionRefused:
            raise PublicationRefused(tips.reason)
        markers = marker_tips_at(
            mounts, view, destination, written=written, position=own.tip, anchors=anchors, seam=seam, binding_tips=tips,
        )
        if type(markers) is PositionRefused:
            raise PublicationRefused(markers.reason)
        token = secrets.token_hex(16)
        intent = PublishIntent(
            kind="publish",
            event_token=token,
            actor=writer.authority.actor,
            at=clock(),
            view=view.unpinned().pinned(resolved.uid),
            destination=destination,
            binding_tips=tuple(sorted(revision.node.uid for revision in tips)),
            marker_tips=markers,
            anchors=tuple(anchors),
        )
        digest = writer._append_operation_intent("publish", token, intent.actor, port=port, payload=encode_publish_intent(intent))
        return OpenedPublication(intent, digest)


def _bind_publication(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    opened: OpenedPublication,
    *,
    corpus_id: str,
    marker: str,
    artifact: str,
    remotely_revealed: bool,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> BindingOutcome:
    """Step 8: one fulfilling transaction under the written root's lock — the
    binding revision and its report, or, when the guard's recomputation at the
    intent's position refuses, the refusal report alone in its place."""
    writer.authority.require("publish", ("publication-binding",))
    writer.authority.require("corpus-write", ("act-report",))
    if type(remotely_revealed) is not bool:
        raise MalformedRecord("remotely_revealed must be a bool")
    writer._require_pins_agree()
    operation_port = writer._require_bound_port(port)
    intent = opened.intent
    subject = str(binding_address(intent.view, intent.destination))
    binding = binding_record(intent, corpus_id=corpus_id, marker=marker, artifact=artifact)
    writer._refuse_rendering(binding)
    closed_at = clock()

    def report_of(outcome: BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused) -> ActReport:
        return boundary._mint_publish_report(
            intent, observer=intent.actor, instrument=PUBLISH_INSTRUMENT, opened_at=intent.at,
            closed_at=closed_at, entry=PublicationBindingEntry(subject, outcome),
        )

    success = report_of(BindingBound(binding.uid, corpus_id, marker))
    plan = [writer._create_op(binding), writer._create_op(stored.act_report_node(success))]
    judged: dict[str, BindingPredecessorNotStanding | BindingEvidenceRefused] = {}

    def guard(_view) -> str | None:
        tips, markers = _judge(writer, resolver, opened, seam)
        if type(tips) is PositionRefused or type(markers) is PositionRefused:
            refused = tips if type(tips) is PositionRefused else markers
            assert type(refused) is PositionRefused
            judged["outcome"] = BindingEvidenceRefused(corpus_id, marker, remotely_revealed, refused.reason)
            return type(judged["outcome"]).__name__
        assert type(tips) is tuple and type(markers) is tuple
        standing = tuple(sorted(revision.node.uid for revision in tips))
        if not set(intent.binding_tips) <= set(standing):
            judged["outcome"] = BindingPredecessorNotStanding(corpus_id, marker, remotely_revealed, standing)
        elif standing != intent.binding_tips or markers != intent.marker_tips:
            judged["outcome"] = BindingEvidenceRefused(corpus_id, marker, remotely_revealed, "tips-disagree")
        else:
            return None
        return type(judged["outcome"]).__name__

    def fallback(_reason: str):
        return [writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]

    writer._state.unresolved = True
    reason = operation_port.execute_fulfilling_guarded(plan, opened.digest, guard=guard, fallback=fallback)
    writer._reconstruct()
    if reason is None:
        return BindingOutcome(success, binding)
    return BindingOutcome(report_of(judged["outcome"]), None)
