"""The reservation-assignment write boundary: a root enters through `add`, a successor through `supersede`,
and each chain (`chain` × `scope`) stays linear with its changes evidenced."""

from __future__ import annotations

from dataclasses import replace

import pytest
from authority import ACTOR, FULL
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_reservation import _event

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.corpus import CorpusWriter
from beliefs.errors import ActorMismatch, FamilyKindUnsupported, ReservationRefused, ValidationRefused
from beliefs.projection import project_claim
from beliefs.reservation import OPEN, Group, IntervalUnit, ReservationAssignment, TermUnit

GENE = "biology/gene"
AFFECTS = "biology/affects"
_D = "sha256:" + "a" * 64
_T = ("2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z")


@pytest.fixture()
def writer(tmp_path):
    root = tmp_path / "corpus"
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return w


def _proposition(writer: CorpusWriter, a: str = "EX:a", b: str = "EX:b") -> Node:
    claim = build_claim(
        WITH_BIOLOGY, operator=AFFECTS, args=(Referent(GENE, a), Referent(GENE, b)), layer="causal", polarity="positive"
    )
    return writer.add(stored.proposition_node(f"{a}-{b}", title="p", claim=project_claim(claim)))


def _knowledge(observed_at: str) -> Node:
    value = _event(
        channel="knowledge",
        subjects=(),
        units=(IntervalUnit(OPEN, observed_at),),
        read_class="training-knowledge",
        bound=(),
        observer=ACTOR,
        recorded_by=ACTOR,
        observed_at=observed_at,
        evidence=(),
    )
    return stored.exposure_event_node(value, title="e")


@pytest.fixture()
def events(writer) -> tuple[str, str]:
    first = writer.add(_knowledge("2026-11-01T00:00:00Z")).id
    second = writer.add(_knowledge("2026-11-02T00:00:00Z")).id
    return first, second


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


def _node(value: ReservationAssignment) -> Node:
    return stored.reservation_assignment_node(value, title="assignment")


def _add(writer: CorpusWriter, value: ReservationAssignment) -> Node:
    return writer.add(_node(value))


def _supersede(writer: CorpusWriter, value: ReservationAssignment) -> Node:
    assert value.predecessor is not None
    return writer.supersede(_node(value), of=value.predecessor)


def _code(caught: pytest.ExceptionInfo[ReservationRefused]) -> str:
    return caught.value.code


def _with_released(of: ReservationAssignment, **changes: object) -> ReservationAssignment:
    """A successor that releases the reserved group: a suspension."""
    groups = (_group(OPEN, _T[0], "open"), _group(_T[0], _T[1], "open"), _group(_T[1], _T[2], "open"))
    return _successor(of, groups=groups, **changes)


def test_a_root_assignment_enters_through_add_and_a_successor_is_refused_there(writer, events):
    root = _root((events[0],))
    minted = _add(writer, root)
    assert minted.id == root.id
    assert [(r.predicate, r.target) for r in writer.read_view.get(root.id).relations] == [("considers", events[0])]
    successor = _successor(root, events=tuple(sorted(events)))
    with pytest.raises(FamilyKindUnsupported, match="a successor enters through supersede"):
        _add(writer, successor)
    other_root = _root((events[0],), chain="other-program")
    node = _node(other_root)
    edge = Relation(source=node.id, predicate=stored.SUPERSEDES, target=root.id)
    with pytest.raises(FamilyKindUnsupported, match="a successor enters through supersede"):
        writer.add(node.model_copy(update={"relations": [*node.relations, edge]}))


def test_supersede_mints_a_successor_with_one_owned_edge_and_matching_predecessor_field(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    successor = _successor(root, events=tuple(sorted(events)))
    minted = _supersede(writer, successor)
    stored_relations = [(r.predicate, r.target) for r in writer.read_view.get(minted.id).relations]
    assert stored_relations == [
        *(("considers", e) for e in sorted(events)),
        (stored.SUPERSEDES, root.id),
    ]
    assert stored.reservation_assignment_value(writer.read_view.get(minted.id)).predecessor == root.id

    elsewhere = _root((events[0],), chain="other-program")
    _add(writer, elsewhere)
    misdirected = _successor(elsewhere, events=tuple(sorted(events)))
    with pytest.raises(ValidationRefused, match="predecessor"):
        writer.supersede(_node(misdirected), of=minted.id)

    node = _node(_successor(elsewhere, events=tuple(sorted(events))))
    edge = Relation(source=node.id, predicate=stored.SUPERSEDES, target=elsewhere.id)
    with pytest.raises(ValidationRefused, match="authored by the adapter"):
        writer.supersede(node.model_copy(update={"relations": [*node.relations, edge]}), of=elsewhere.id)


def test_a_second_root_for_the_same_chain_and_scope_is_refused(writer, events):
    _add(writer, _root((events[0],)))
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), assigned_at="2026-11-06T11:00:00Z"))
    assert _code(caught) == "assignment-root-exists"


def test_two_chains_sharing_a_rule_name_do_not_collide(writer, events):
    _add(writer, _root((events[0],)))
    other = _root((events[0],), chain="other-program")
    assert _add(writer, other).id == other.id


def test_a_scoped_root_beside_the_program_root_is_admitted(writer, events):
    program = _root((events[0],))
    _add(writer, program)
    proposition = _proposition(writer)
    scoped = _root((events[0],), scope=proposition.id, applies=program.id)
    minted = _add(writer, scoped)
    assert [(r.predicate, r.target) for r in writer.read_view.get(minted.id).relations] == [
        ("considers", events[0]),
        ("concerns", proposition.id),
        ("applies", program.id),
    ]
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, replace(scoped, assigned_at="2026-11-06T11:00:00Z"))
    assert _code(caught) == "assignment-root-exists"


def test_superseding_a_predecessor_that_already_has_a_successor_is_refused(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    _supersede(writer, _successor(root, events=tuple(sorted(events))))
    fork = _successor(root, evidence=("task:x-1",), groups=(*root.groups, _group(_T[2], OPEN, "unresolved")))
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, fork)
    assert _code(caught) == "assignment-superseded"


def test_changes_without_evidence_are_refused_and_additions_count(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    changed = (_group(OPEN, _T[0], "withheld"), *root.groups[1:])
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, _successor(root, groups=changed))
    assert _code(caught) == "assignment-changes-without-evidence"
    added = (*root.groups, _group(_T[2], OPEN, "unresolved"))
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, _successor(root, groups=added))
    assert _code(caught) == "assignment-changes-without-evidence"
    admitted = _successor(root, groups=added, evidence=("task:roster-commit",))
    assert _supersede(writer, admitted).id == admitted.id


def test_a_suspended_reserved_group_needs_flagged_and_an_empty_list_means_none_made(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, _with_released(root, evidence=(events[1],), events=tuple(sorted(events))))
    assert _code(caught) == "assignment-suspension-unflagged"
    released = _with_released(root, evidence=(events[1],), events=tuple(sorted(events)), flagged=())
    minted = _supersede(writer, released)
    assert ("evidenced-by", events[1]) in [(r.predicate, r.target) for r in minted.relations]


def test_flagged_without_a_suspension_is_refused(writer, events):
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), flagged=()))
    assert _code(caught) == "assignment-flagged-without-suspension"
    root = _root((events[0],))
    _add(writer, root)
    changed = (_group(OPEN, _T[0], "withheld"), *root.groups[1:])
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, _successor(root, groups=changed, evidence=("task:x-1",), flagged=()))
    assert _code(caught) == "assignment-flagged-without-suspension"


def test_a_successor_in_another_chain_scope_or_unit_shape_is_refused(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    proposition = _proposition(writer)
    terms = (Group((TermUnit(GENE, "EX:a"),), "open", None, None),)
    for changes in ({"chain": "other-program"}, {"scope": proposition.id}, {"groups": terms}):
        with pytest.raises(ReservationRefused) as caught:
            _supersede(writer, _successor(root, evidence=("task:x-1",), **changes))
        assert _code(caught) == "assignment-scope-mismatch", changes


def test_an_undeclared_unit_sort_is_refused(writer, events):
    terms = (Group((TermUnit("mm/cohort", "x"),), "open", None, None),)
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), groups=terms))
    assert _code(caught) == "assignment-unit-sort-undeclared"


def test_applies_must_name_a_program_level_assignment(writer, events):
    program = _root((events[0],))
    _add(writer, program)
    proposition = _proposition(writer)
    scoped = _root((events[0],), scope=proposition.id, applies=program.id)
    _add(writer, scoped)
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), chain="other-program", scope=proposition.id, applies=scoped.id))
    assert _code(caught) == "assignment-applies-scoped"
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), chain="third", applies="reservation-assignment:" + "9" * 64))
    assert _code(caught) == "assignment-ref-unresolved"


def test_an_unresolved_considered_event_is_refused(writer, events):
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root(("exposure-event:" + "9" * 64,)))
    assert _code(caught) == "assignment-ref-unresolved"
    proposition = _proposition(writer)
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root(("exposure-event:" + proposition.id.partition(":")[2],)))
    assert _code(caught) == "assignment-ref-unresolved"
    with pytest.raises(ReservationRefused) as caught:
        _add(writer, _root((events[0],), scope="proposition:" + events[1].partition(":")[2]))
    assert _code(caught) == "assignment-ref-unresolved"


def test_assigned_by_must_be_the_bound_actor(writer, events):
    node = _node(_root((events[0],), assigned_by="someone-else"))
    with pytest.raises(ActorMismatch):
        writer.add(node)
    assert writer._add_locked(node, provenance=True).id == node.id


def test_an_identical_derivation_is_refused_as_unchanged(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    with pytest.raises(ReservationRefused) as caught:
        _supersede(writer, _successor(root))
    assert _code(caught) == "assignment-unchanged"


def test_an_imported_chain_arrives_with_its_edges(writer, events):
    root = _root((events[0],), assigned_by="someone-else")
    successor = _successor(root, events=tuple(sorted(events)))
    node = _node(successor)
    edge = Relation(source=node.id, predicate=stored.SUPERSEDES, target=root.id)
    bundle = [_node(root), node.model_copy(update={"relations": [*node.relations, edge]})]
    writer.import_bundle(bundle, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert writer.read_view.holds(root.id) and writer.read_view.holds(successor.id)


def test_revising_the_prose_of_a_chain_member_is_admitted(writer, events):
    root = _root((events[0],))
    minted_root = _add(writer, root)
    successor = _supersede(writer, _successor(root, events=tuple(sorted(events))))
    assert writer.revise(minted_root.model_copy(update={"body": "more"})).body == "more"
    assert writer.revise(successor.model_copy(update={"body": "more"})).body == "more"
