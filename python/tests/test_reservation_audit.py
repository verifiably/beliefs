"""Exposure events and reservation assignments under audit: the boundary's checks reported rather than
raised, chain forks found in one pass, malformed facets classified once, and the view helpers that read
both kinds back."""

from __future__ import annotations

from dataclasses import replace

import pytest
from authority import ACTOR, FULL
from fixtures_cut3 import carry_registers
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_reservation import _event
from test_reservation_boundary import (
    _T,
    _add,
    _group,
    _knowledge,
    _node,
    _proposition,
    _readdress_assignment,
    _root,
    _successor,
    _supersede,
)

from beliefs import audit, errors, reservation, stored
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.corpus import CorpusWriter
from beliefs.identity import v1
from beliefs.reservation import (
    EXPOSURE_EVENT_DOMAIN,
    OPEN,
    ReservationAssignment,
    TermUnit,
    assignment_changes,
)

GENE = "biology/gene"


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    root = tmp_path / "corpus"
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return carry_registers(w)


@pytest.fixture()
def events(writer: CorpusWriter) -> tuple[str, str]:
    """Two considered knowledge events, as the boundary tests mint them."""
    return writer.add(_knowledge("2026-11-01T00:00:00Z")).id, writer.add(_knowledge("2026-11-02T00:00:00Z")).id


def _findings(writer: CorpusWriter):
    return audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile)


def _codes(writer: CorpusWriter) -> list[tuple[str, str]]:
    return sorted((f.code, f.ref) for f in _findings(writer))


def _raw(writer: CorpusWriter, node: Node) -> Node:
    raw_write(writer.root, stored.stamp_semantic_identity(node))
    return node


def _raw_successor(writer: CorpusWriter, value: ReservationAssignment) -> Node:
    """A successor written behind the boundary, carrying the `supersedes` edge `supersede` would add."""
    assert value.predecessor is not None
    node = _node(value)
    node.relations.append(Relation(source=node.id, predicate=stored.SUPERSEDES, target=value.predecessor))
    return _raw(writer, node)


def _evidenced(of: ReservationAssignment, **changes: object) -> ReservationAssignment:
    return _successor(of, groups=(*of.groups, _group(_T[2], OPEN, "unresolved")), evidence=("task:x-1",), **changes)


def test_a_well_formed_chain_audits_clean(writer, events):
    source = writer.add(stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"}))
    proposition = _proposition(writer)
    read = _event(
        subjects=(source.id,),
        units=(TermUnit(GENE, "EX:a"),),
        observer=ACTOR,
        recorded_by=ACTOR,
        evidence=(),
        propositions=(proposition.id,),
    )
    writer.add(stored.exposure_event_node(read, title="read"))
    root = _root((events[0],))
    _add(writer, root)
    _supersede(writer, _evidenced(root))
    scoped = _root((events[0],), scope=proposition.id, applies=root.id)
    _add(writer, scoped)
    assert _codes(writer) == []
    assert audit.check_assignment_chains(reopen(writer.root)) == ()


def test_a_raw_written_fork_is_reported_once(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    first = _evidenced(root)
    _supersede(writer, first)
    second = _evidenced(root, events=tuple(sorted(events)))
    _raw_successor(writer, second)
    later, earlier = max(first.id, second.id), min(first.id, second.id)
    forks = [f for f in _findings(writer) if f.code == "assignment-fork"]
    assert [(f.ref, f.severity) for f in forks] == [(later, "error")]
    assert earlier in forks[0].detail and later in forks[0].detail
    assert _codes(writer) == [("assignment-fork", later)]


def test_two_raw_written_roots_of_one_chain_are_a_fork(writer, events):
    first = _root((events[0],))
    _add(writer, first)
    second = _root((events[0],), assigned_at="2026-11-06T11:00:00Z")
    _raw(writer, _node(second))
    later, earlier = max(first.id, second.id), min(first.id, second.id)
    forks = [f for f in _findings(writer) if f.code == "assignment-fork"]
    assert [f.ref for f in forks] == [later]
    assert earlier in forks[0].detail
    assert _codes(writer) == [("assignment-fork", later)]


def test_a_raw_written_successor_without_evidence_is_reported(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    bare = _successor(root, groups=(*root.groups, _group(_T[2], OPEN, "unresolved")))
    _raw_successor(writer, bare)
    assert _codes(writer) == [("assignment-changes-without-evidence", bare.id)]


def test_each_assignment_check_is_reported_rather_than_raised(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    released = _successor(
        root,
        groups=(_group(OPEN, _T[0], "open"), _group(_T[0], _T[1], "open"), _group(_T[1], _T[2], "open")),
        evidence=(events[1],),
        events=tuple(sorted(events)),
    )
    _raw_successor(writer, released)
    other_root = _root((events[0],), chain="other-program")
    _add(writer, other_root)
    unchanged = _successor(other_root)
    _raw_successor(writer, unchanged)
    dangling = _root(("exposure-event:" + "9" * 64,), chain="third")
    _raw(writer, _node(dangling))
    flagged = _root((events[0],), chain="fourth", flagged=())
    _raw(writer, _node(flagged))
    edge_mismatch = _node(_root((events[0],), chain="fifth")).model_copy(update={"relations": []})
    _raw(writer, edge_mismatch)
    proposition = _proposition(writer)
    scoped = _root((events[0],), chain="sixth", scope=proposition.id)
    _add(writer, scoped)
    applies_scoped = _root((events[0],), chain="seventh", scope=proposition.id, applies=scoped.id)
    _raw(writer, _node(applies_scoped))
    scope_mismatch_root = _root((events[0],), chain="eighth")
    _add(writer, scope_mismatch_root)
    scope_mismatch = _successor(scope_mismatch_root, chain="ninth", evidence=("task:x-1",))
    _raw_successor(writer, scope_mismatch)
    undeclared_sort = _root(
        (events[0],),
        chain="tenth",
        groups=(reservation.Group((TermUnit("mm/cohort", "a"),), "open", None, None),),
    )
    _raw(writer, _node(undeclared_sort))
    assert _codes(writer) == sorted(
        [
            ("assignment-suspension-unflagged", released.id),
            ("assignment-unchanged", unchanged.id),
            ("assignment-ref-unresolved", dangling.id),
            ("assignment-flagged-without-suspension", flagged.id),
            ("assignment-edge-mismatch", edge_mismatch.id),
            ("assignment-applies-scoped", applies_scoped.id),
            ("assignment-scope-mismatch", scope_mismatch.id),
            ("assignment-unit-sort-undeclared", undeclared_sort.id),
        ]
    )


def test_an_exposure_event_edge_mismatch_dangling_subject_and_undeclared_sort_are_reported(writer, events):
    proposition = _proposition(writer)
    event = _knowledge("2026-11-03T00:00:00Z")
    node = event.model_copy(
        update={"relations": [Relation(source=event.id, predicate="concerns", target=proposition.id)]}
    )
    _raw(writer, node)
    dangling = stored.exposure_event_node(
        _event(
            subjects=("source:" + "8" * 64,),
            units=(TermUnit(GENE, "EX:a"),),
            observer=ACTOR,
            recorded_by=ACTOR,
            evidence=(),
        ),
        title="dangling",
    )
    _raw(writer, dangling)
    source = writer.add(stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"}))
    undeclared = stored.exposure_event_node(
        _event(
            subjects=(source.id,),
            units=(TermUnit("mm/cohort", "a"),),
            observer=ACTOR,
            recorded_by=ACTOR,
            evidence=(),
        ),
        title="undeclared",
    )
    _raw(writer, undeclared)
    assert _codes(writer) == sorted(
        [
            ("exposure-edge-mismatch", node.id),
            ("exposure-ref-unresolved", dangling.id),
            ("exposure-unit-sort-undeclared", undeclared.id),
        ]
    )


def test_stale_or_missing_semantic_hash_assignments_are_skipped_by_chain_scan_and_malformed_neighbours_leave_checks_unchecked(
    writer, events
):
    root = _root((events[0],))
    _add(writer, root)
    stale_second = stored.stamp_semantic_identity(_node(_root((events[0],), assigned_at="2026-11-06T11:00:00Z")))
    stale_second.facets[stored.SEMANTIC_IDENTITY_FACET]["digest"] = "0" * 64
    raw_write(writer.root, stale_second)

    unstamped_third = _node(_root((events[0],), assigned_at="2026-11-06T12:00:00Z")).model_copy(deep=True)
    unstamped_third.facets.pop(stored.SEMANTIC_IDENTITY_FACET, None)
    raw_write(writer.root, unstamped_third)

    bad_predecessor = _node(_root((events[0],), chain="bad-pred"))
    bad_predecessor.facets[stored.RESERVATION_ASSIGNMENT_FACET]["groups"][0]["role"] = "bogus"
    _raw(writer, bad_predecessor)
    after_bad = _evidenced(_root((events[0],), chain="bad-pred"))
    _raw_successor(writer, after_bad)

    findings = _findings(writer)
    assert sorted((f.code, f.ref) for f in findings) == sorted(
        [
            ("semantic-hash-stale", stale_second.id),
            ("semantic-hash-missing", unstamped_third.id),
            ("facet-payload-malformed", bad_predecessor.id),
        ]
    )
    view = reopen(writer.root)
    assert audit.check_assignment_chains(view, malformed={stale_second.id, unstamped_third.id}) == ()
    outcome = audit.check_reservation_assignment(view, view.get(after_bad.id), profile=WITH_BIOLOGY)
    assert outcome.checked is False and outcome.contradiction is None
    assert bad_predecessor.id in outcome.reason


def test_a_malformed_facet_is_facet_payload_malformed_and_skipped_below(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    second = _node(_root((events[0],), assigned_at="2026-11-06T11:00:00Z"))
    second.facets[stored.RESERVATION_ASSIGNMENT_FACET]["groups"][0]["role"] = "bogus"
    _raw(writer, second)
    event = _knowledge("2026-11-03T00:00:00Z")
    event.facets[stored.EXPOSURE_EVENT_FACET]["channel"] = "bogus"
    _raw(writer, event)
    findings = _findings(writer)
    assert sorted((f.code, f.ref, f.detail) for f in findings if f.code == "facet-payload-malformed") == sorted(
        [
            ("facet-payload-malformed", second.id, stored.RESERVATION_ASSIGNMENT_FACET),
            ("facet-payload-malformed", event.id, stored.EXPOSURE_EVENT_FACET),
        ]
    )
    assert sorted((f.code, f.ref) for f in findings) == sorted(
        [("facet-payload-malformed", second.id), ("facet-payload-malformed", event.id)]
    )
    assert audit.check_assignment_chains(reopen(writer.root)) == ()


def test_misplaced_world_kind_tokens_and_unscoped_applies_audit_as_facet_payload_malformed(writer, events):
    root = _root((events[0],))
    _add(writer, root)

    bad_event = _knowledge("2026-11-03T00:00:00Z").model_copy(deep=True)
    event_facet = bad_event.facets[stored.EXPOSURE_EVENT_FACET]
    event_facet["evidence"] = ["assessment:" + "a" * 64]
    bad_event = bad_event.model_copy(update={"id": "exposure-event:" + v1.digest(EXPOSURE_EVENT_DOMAIN, event_facet)})
    _raw(writer, bad_event)

    bad_evidence = _readdress_assignment(_node(_root((events[0],), chain="second")), evidence=["run:" + "a" * 64])
    _raw(writer, bad_evidence)

    bad_prior = _readdress_assignment(
        _node(_root((events[0],), chain="third")), prior_runs=["exposure-event:" + "a" * 64]
    )
    _raw(writer, bad_prior)

    unscoped_applies = _readdress_assignment(_node(_root((events[0],), chain="fourth")), applies=root.id)
    _raw(writer, unscoped_applies)

    findings = _findings(writer)
    assert sorted((f.code, f.ref, f.detail) for f in findings) == sorted(
        [
            ("facet-payload-malformed", bad_event.id, stored.EXPOSURE_EVENT_FACET),
            ("facet-payload-malformed", bad_evidence.id, stored.RESERVATION_ASSIGNMENT_FACET),
            ("facet-payload-malformed", bad_prior.id, stored.RESERVATION_ASSIGNMENT_FACET),
            ("facet-payload-malformed", unscoped_applies.id, stored.RESERVATION_ASSIGNMENT_FACET),
        ]
    )


def _world_of(tmp_path, placement):
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    roots = corpora(tmp_path, placement)
    world = world_over(tmp_path, roots)
    return world, roots, publish(world, tuple(placement), hold_shipped(world))


def _owing_a_register(findings) -> tuple:
    """`findings` less the one `register-missing` warning a fixture world's
    corpus owes: its corpora carry no assumptions register, so each reports the
    activated `biology` contract (design section 9.2). Asserted, then set aside."""
    owed = [f for f in findings if f.code == "register-missing"]
    assert [(f.ref, f.detail) for f in owed] == [("corpus.yaml", "biology")]
    return tuple(f for f in findings if f.code != "register-missing")


def _stamped(value: ReservationAssignment) -> Node:
    return stored.stamp_semantic_identity(_node(value))


def test_world_audit_skips_a_considered_event_recorded_in_an_absent_corpus(tmp_path):
    from test_world_build import ALPHA, BETA
    from test_world_view import make_absent

    from beliefs.world.view import open_world_view

    event = stored.stamp_semantic_identity(_knowledge("2026-11-01T00:00:00Z"))
    assignment = _root((event.id,))
    world, roots, published = _world_of(tmp_path, {ALPHA: (_stamped(assignment),), BETA: (event,)})
    present = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert _owing_a_register(present.corpora[ALPHA]) == () and _owing_a_register(present.corpora[BETA]) == ()
    make_absent(roots, BETA)

    absent = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert _owing_a_register(absent.corpora[ALPHA]) == ()
    assert [f.code for f in absent.corpora[BETA]] == ["corpus-absent"]
    view = open_world_view(world, published, on_damage="report")
    outcome = audit.check_reservation_assignment(view, view.get(assignment.id), profile=WITH_BIOLOGY)
    assert outcome.checked is False and outcome.contradiction is None
    assert event.id in outcome.reason and BETA in outcome.reason


def test_world_audit_reports_dangling_refs_and_forks_under_the_holding_corpus(tmp_path):
    from test_world_build import ALPHA, BETA

    event = stored.stamp_semantic_identity(_knowledge("2026-11-01T00:00:00Z"))
    dangling = _root(("exposure-event:" + "9" * 64,), chain="third")
    first = _root((event.id,))
    second = _root((event.id,), assigned_at="2026-11-06T11:00:00Z")
    stale_fork = _stamped(_root((event.id,), assigned_at="2026-11-06T12:00:00Z"))
    stale_fork.facets[stored.SEMANTIC_IDENTITY_FACET]["digest"] = "0" * 64
    world, _roots, published = _world_of(
        tmp_path,
        {ALPHA: (event, _stamped(dangling)), BETA: (_stamped(first), _stamped(second), stale_fork)},
    )

    found = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert [(f.code, f.ref) for f in _owing_a_register(found.corpora[ALPHA])] == [
        ("assignment-ref-unresolved", dangling.id)
    ]
    assert sorted((f.code, f.ref) for f in _owing_a_register(found.corpora[BETA])) == sorted(
        [("assignment-fork", max(first.id, second.id)), ("semantic-hash-stale", stale_fork.id)]
    )


def test_assignment_head_returns_the_unsuperseded_record_and_refuses_a_fork(writer, events):
    root = _root((events[0],))
    _add(writer, root)
    assert reservation.assignment_head(reopen(writer.root), "sun-epochs") == root
    assert reservation.assignment_changes_of(reopen(writer.root), root.id) == ()
    successor = _evidenced(root)
    _supersede(writer, successor)
    view = reopen(writer.root)
    assert reservation.assignment_head(view, "sun-epochs") == successor
    assert reservation.assignment_head(view, "sun-epochs", scope="proposition:" + "0" * 64) is None
    assert reservation.assignment_head(view, "elsewhere") is None
    assert reservation.assignment_changes_of(view, successor.id) == assignment_changes(root, successor)
    assert reservation.assignment_changes_of(view, successor.id) != ()

    proposition = _proposition(writer)
    scoped = _root((events[0],), scope=proposition.id, applies=root.id)
    _add(writer, scoped)
    assert reservation.assignment_head(reopen(writer.root), "sun-epochs", scope=proposition.id) == scoped
    assert reservation.assignment_head(reopen(writer.root), "sun-epochs") == successor

    _raw_successor(writer, _evidenced(root, events=tuple(sorted(events))))
    with pytest.raises(errors.ChainAmbiguous):
        reservation.assignment_head(reopen(writer.root), "sun-epochs")
    assert issubclass(errors.ChainAmbiguous, errors.RecordError)


def test_assignment_head_refuses_two_roots(writer, events):
    _add(writer, _root((events[0],)))
    _raw(writer, _node(_root((events[0],), assigned_at="2026-11-06T11:00:00Z")))
    with pytest.raises(errors.ChainAmbiguous):
        reservation.assignment_head(reopen(writer.root), "sun-epochs")


def test_exposure_events_narrow_by_subject_and_proposition(writer):
    source = writer.add(stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"}))
    proposition = _proposition(writer)

    def knowledge(observed_at: str, propositions: tuple[str, ...]) -> Node:
        value = stored.exposure_event_value(_knowledge(observed_at))
        return stored.exposure_event_node(replace(value, propositions=propositions), title="k")

    read = _event(
        subjects=(source.id,),
        units=(TermUnit(GENE, "EX:a"),),
        observer=ACTOR,
        recorded_by=ACTOR,
        evidence=(),
        observed_at="2026-11-05T00:00:00Z",
        propositions=(proposition.id,),
    )
    later = writer.add(stored.exposure_event_node(read, title="read"))
    concerning = writer.add(knowledge("2026-11-02T00:00:00Z", (proposition.id,)))
    bare = writer.add(knowledge("2026-11-01T00:00:00Z", ()))
    view = reopen(writer.root)

    def ids(found: tuple[reservation.ExposureEvent, ...]) -> list[str]:
        return [event.id for event in found]

    assert ids(reservation.exposure_events(view)) == [bare.id, concerning.id, later.id]
    assert ids(reservation.exposure_events(view, subject=source.id)) == [later.id]
    assert ids(reservation.exposure_events(view, proposition=proposition.id)) == [concerning.id, later.id]
    assert ids(reservation.exposure_events(view, subject=source.id, proposition=proposition.id)) == [later.id]
    assert reservation.exposure_events(view, subject="source:" + "7" * 64) == ()


def test_every_new_code_is_in_world_audit_codes():
    codes = {
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
    }
    assert codes <= audit.WORLD_AUDIT_CODES
    assert not codes & audit.MALFORMEDNESS_CODES
