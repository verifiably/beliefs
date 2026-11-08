"""Exposure events and reservation assignments across the doors that carry a record between roots:
`import_bundle`, `consolidate`, `move`, and a local publication admitted at an empty destination.

Every door but `add` and `supersede` judges a record that arrives with its edges and its attestation
(`provenance`), against a view that may already hold it: the chain scan excludes the record itself, and
`recorded_by` / `assigned_by` are kept as written. The publication test runs the real engine on the
certified volume, as the session publish-door tests do.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import ACTOR, FULL
from coordination_fixtures import content_for
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.relations import Relation
from profiles import BASE, WITH_BIOLOGY, pins_for
from session_doors_fixture import PUBLISHES, V2, Clock
from test_relocation import CONSOLIDATE_FIELDS, MOVE_FIELDS, _writer
from test_reservation import _event
from test_reservation import _knowledge_event as _shared_knowledge_event
from test_world_receipts import hold_shipped

from beliefs import relocation, stored
from beliefs.claim import Referent, build_claim
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.errors import ActorMismatch, RelocationKindExcluded
from beliefs.intents.publish import Destination
from beliefs.projection import project_claim
from beliefs.publication_arrival import admit_publication
from beliefs.publish import Published, publish
from beliefs.reservation import (
    OPEN,
    ExposureEvent,
    Group,
    IntervalUnit,
    ReservationAssignment,
    assignment_head,
    exposure_events,
)
from beliefs.root import init_corpus_root, init_world_root, moment_seam, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig, epoch
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view

GENE = "biology/gene"
AFFECTS = "biology/affects"
OTHER = "someone-else"
_D = "sha256:" + "a" * 64
_T = ("2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z")
IMPORT_FIELDS = {"observer": "o", "instrument": "i", "opened_at": "T0", "closed_at": "T1"}


@pytest.fixture()
def source_writer(tmp_path):
    return _writer(tmp_path / "source", domains=PINS.domains)


@pytest.fixture()
def destination_writer(tmp_path):
    return _writer(tmp_path / "destination", domains=PINS.domains)


def _proposition() -> Node:
    claim = build_claim(
        WITH_BIOLOGY,
        operator=AFFECTS,
        args=(Referent(GENE, "EX:a"), Referent(GENE, "EX:b")),
        layer="causal",
        polarity="positive",
    )
    return stored.proposition_node("EX:a-EX:b", title="p", claim=project_claim(claim))


def _source() -> Node:
    return stored.source_node(title="A paper", identifiers={"doi": "10.1234/abc"})


def _read_event(subject: str, proposition: str, *, recorded_by: str = ACTOR) -> ExposureEvent:
    """A read: an `exposes` edge to the source and a `concerns` edge to the proposition, in the facet's
    order, which is not the edges' sorted order."""
    return _event(
        subjects=(subject,),
        units=(IntervalUnit(_T[0], _T[1]),),
        observer=recorded_by,
        recorded_by=recorded_by,
        propositions=(proposition,),
        evidence=(),
    )


def _knowledge_event(observed_at: str, *, recorded_by: str = ACTOR) -> ExposureEvent:
    return _shared_knowledge_event(observed_at, recorded_by=recorded_by)


def _group(start: str, end: str, role: str) -> Group:
    return Group((IntervalUnit(start, end),), role, None, None)


def _root(events: tuple[str, ...], **changes: object) -> ReservationAssignment:
    fields: dict[str, object] = {
        "chain": "sun-epochs",
        "rule_name": "epoch-reservation-rule",
        "rule_version": "3",
        "inputs": (("rule", _D),),
        "events": events,
        "scope": None,
        "applies": None,
        "groups": (_group(OPEN, _T[0], "open"), _group(_T[0], _T[1], "reserved"), _group(_T[1], _T[2], "open")),
        "predecessor": None,
        "evidence": (),
        "flagged": None,
        "account": None,
        "participants": (),
        "prior_runs": (),
        "assigned_at": "2026-11-06T10:00:00Z",
        "assigned_by": ACTOR,
    }
    fields.update(changes)
    return ReservationAssignment(**fields)  # type: ignore[arg-type]


def _successor(of: ReservationAssignment, **changes: object) -> ReservationAssignment:
    return replace(of, predecessor=of.id, assigned_at="2026-11-07T10:00:00Z", **changes)  # type: ignore[arg-type]


def _event_node(value: ExposureEvent) -> Node:
    return stored.exposure_event_node(value, title="e")


def _assignment_node(value: ReservationAssignment) -> Node:
    return stored.reservation_assignment_node(value, title="assignment")


def _as_imported(value: ReservationAssignment) -> Node:
    """The record as it arrives from another root: a successor carries the edge `supersede` authored."""
    node = _assignment_node(value)
    if value.predecessor is None:
        return node
    edge = Relation(source=node.id, predicate=stored.SUPERSEDES, target=value.predecessor)
    return node.model_copy(update={"relations": [*node.relations, edge]})


def _edges(writer: CorpusWriter, ref: str) -> list[tuple[str, str]]:
    return [(r.predicate, r.target) for r in writer.read_view.get(ref).relations]


def test_import_bundle_carries_a_chain_whose_records_do_not_collide_with_themselves(destination_writer):
    """A whole chain in one bundle: each record is judged against the import's union, which holds it,
    so the root does not find itself as a second root nor the successor itself as a fork."""
    first, second = (_knowledge_event(f"2026-11-0{day}T00:00:00Z") for day in (1, 2))
    root = _root((first.id,))
    successor = _successor(root, events=tuple(sorted((first.id, second.id))))
    bundle = [_event_node(first), _event_node(second), _as_imported(root), _as_imported(successor)]

    destination_writer.import_bundle(bundle, **IMPORT_FIELDS)

    view = destination_writer.read_view
    assert all(view.holds(node.id) for node in bundle)
    assert _edges(destination_writer, successor.id) == [
        *(("considers", e) for e in sorted((first.id, second.id))),
        (stored.SUPERSEDES, root.id),
    ]
    assert assignment_head(view, "sun-epochs") == successor


def test_import_keeps_recorded_by_and_assigned_by_of_another_actor(destination_writer):
    event = _knowledge_event("2026-11-01T00:00:00Z", recorded_by=OTHER)
    root = _root((event.id,), assigned_by=OTHER)
    with pytest.raises(ActorMismatch):
        destination_writer.add(_event_node(event))

    destination_writer.import_bundle([_event_node(event), _as_imported(root)], **IMPORT_FIELDS)

    view = destination_writer.read_view
    assert stored.exposure_event_value(view.get(event.id)).recorded_by == OTHER
    assert stored.reservation_assignment_value(view.get(root.id)).assigned_by == OTHER
    assert exposure_events(view) == (event,)


def _seed(writer: CorpusWriter) -> tuple[Node, Node]:
    """The source and the proposition a read event names, in `writer`'s root."""
    return writer.add(_source()), writer.add(_proposition())


def _scoped_chain(subject: str, proposition: str) -> tuple[ExposureEvent, ReservationAssignment]:
    """A read event and a root scoped to the proposition: each record carries edges of two predicates,
    in facet order (`exposes` before `concerns`; `considers` before `concerns`)."""
    event = _read_event(subject, proposition)
    return event, _root((event.id,), scope=proposition)


def test_consolidate_moves_an_event_and_an_assignment_between_corpora(source_writer, destination_writer):
    """Both roots hold the same event, root and successor; consolidating keeps each in `keep`, judging
    it against a root that already holds it, and removes the other location. The union of edges is stored
    sorted, as for every kind, which the boundary admits since edges mirror the facet as a set (ruling R5)."""
    subject, proposition = _source(), _proposition()
    event, root = _scoped_chain(subject.id, proposition.id)
    successor = _successor(root, evidence=("task:roster-commit",), groups=root.groups[:2])
    for writer in (source_writer, destination_writer):
        _seed(writer)
        writer.add(_event_node(event))
        writer.add(_assignment_node(root))
        writer.supersede(_assignment_node(successor), of=root.id)
    refs = (successor.id, root.id, event.id)
    before = {ref: _edges(destination_writer, ref) for ref in refs}
    assert before[successor.id][-1] == (stored.SUPERSEDES, root.id)
    assert any(edges != sorted(edges) for edges in before.values())

    for ref in refs:
        survivor, _, _ = relocation.consolidate((destination_writer, ref), (source_writer, ref), **CONSOLIDATE_FIELDS)
        assert survivor.id == ref

    for ref in refs:
        assert _edges(destination_writer, ref) == sorted(before[ref])
        assert not source_writer.read_view.holds(ref)
    assert stored.exposure_event_value(destination_writer.read_view.get(event.id)) == event
    assert assignment_head(destination_writer.read_view, "sun-epochs", scope=proposition.id) == successor


def test_move_refuses_nothing_for_the_new_kinds_but_still_refuses_an_act_report(source_writer, destination_writer):
    subject, proposition = _seed(source_writer)
    _seed(destination_writer)
    event, root = _scoped_chain(subject.id, proposition.id)
    source_writer.add(_event_node(event))
    source_writer.add(_assignment_node(root))
    successor = _successor(root, events=(event.id,), evidence=("task:roster-commit",), groups=(*root.groups[:2],))
    source_writer.supersede(_assignment_node(successor), of=root.id)

    reports = []
    for ref in (event.id, root.id, successor.id):
        moved, _, source_report = relocation.move(source_writer, destination_writer, ref, **MOVE_FIELDS)
        assert moved.id == ref and not source_writer.read_view.holds(ref)
        reports.append(source_report)

    assert assignment_head(destination_writer.read_view, "sun-epochs", scope=proposition.id) == successor
    assert _edges(destination_writer, successor.id)[-1] == (stored.SUPERSEDES, root.id)
    with pytest.raises(RelocationKindExcluded):
        relocation.move(source_writer, destination_writer, f"act-report:{reports[0].identity()}", **MOVE_FIELDS)


def _addresses(*refs: str) -> dict[str, object]:
    """A view query selecting exactly `refs`: the coordination query vocabulary predates the new kinds,
    while an address is validated against the world kinds directly."""
    return {"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": sorted(refs)}]}]}


def _corpus(path: Path, profile) -> tuple[str, CorpusWriter]:
    init_corpus_root(path, authority=FULL)
    writer = open_corpus(path, authority=FULL, profile=profile)
    return writer.adopt_manifest(profile=pins_for(profile)).corpus_id, writer


def test_a_published_assignment_and_its_events_admit_at_an_empty_destination(certified_work):
    """A root, its successor and the three events they name publish into an empty destination
    directory, and a second world admits the publication; the chain reads back whole there."""
    base = Path(certified_work).resolve()
    alpha_id, alpha_writer = _corpus(base / "alpha", BASE)
    events = [_knowledge_event(f"2026-11-0{day}T00:00:00Z") for day in (1, 2, 3)]
    for event in events:
        alpha_writer.add(_event_node(event))
    first, second, third = (event.id for event in events)
    root = _root((first,))
    alpha_writer.add(_assignment_node(root))
    successor = _successor(root, events=tuple(sorted((first, second))), evidence=(third,), groups=root.groups[:2])
    alpha_writer.supersede(_assignment_node(successor), of=root.id)
    selected = (root.id, successor.id, first, second, third)

    written = base / "written"
    _corpus(written, V2)
    config = WorldConfig(base / "world", "e" * 32, (base / "alpha", written))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(base / "alpha", provenance=Fresh())
    world.admit(written, provenance=Fresh())
    epoch.build_epoch(world, coverage=frozenset({alpha_id}), bindings=hold_shipped(world))
    resolver = CoordinationResolver({config.corpus_roots[0]: BASE, config.corpus_roots[1]: V2})
    project = open_corpus(written, authority=FULL, profile=V2, coordination_resolver=resolver).mint_coordination(
        "project", content=content_for("project", query=_addresses(*selected))
    )
    ops, dest = base / "ops", base / "dest"
    ops.mkdir()
    dest.mkdir()

    outcome = publish(
        open_corpus(written, authority=PUBLISHES, profile=V2, coordination_resolver=resolver),
        resolver,
        open_world(config, authority=PUBLISHES),
        view=coordination_revision(project).address,
        destination=Destination.local(str(dest)),
        operations_root=ops,
        staging_profile=V2,
        clock=Clock(),
        seam=moment_seam(),
    )
    assert type(outcome) is Published, outcome

    exported = dest / outcome.corpus_id
    recipient = WorldConfig(base / "recipient", "c" * 32, (exported,))
    init_world_root(recipient, authority=FULL)
    recipient_world = open_world(recipient, authority=FULL)
    observers = ObserverSet(
        (ArtifactCarrier.from_bytes((dest / f"{outcome.corpus_id}.head-artifact.v1").read_bytes()),)
    )
    _, report = admit_publication(recipient_world, exported, observers)
    assert report.outcome == "validated"
    built = epoch.build_epoch(
        recipient_world, coverage=frozenset({outcome.corpus_id}), bindings=hold_shipped(recipient_world)
    )
    view = open_world_view(recipient_world, built)
    for ref in selected:
        assert node_to_markdown(view.get(ref)) == node_to_markdown(alpha_writer.read_view.get(ref))
    published = ReadView.opened_at(exported)
    assert assignment_head(published, "sun-epochs") == successor
    assert exposure_events(published) == tuple(events)
