"""The sharing act doors on the scoped writer, over real roots on the certified
volume (sharing design §2 decisions 3–6, §4.4, §4.5, §6 "The sharing doors").

A publication exported by the local publish act is copied without its metadata
sibling; a recipient's attended session restores and admits it through
`ScopedWriter.restore_root` and `ScopedWriter.admit_publication`, each door
binding the caller's evidence to the root before its act and ledgering one
`sharing` line after it. `ScopedWriter.retire` retires the adopted publication
the same way (retirement door design §5), and a successor session recovers a
retirement whose line a failed append lost."""

from __future__ import annotations

import dataclasses
import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from authority import FULL
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from session_doors_fixture import (
    evidence_for,
    metadata_less_copy,
    publish_locally,
    published_source,
    recipient_session,
    successor_session,
)
from test_session_routes import TracingLock
from test_session_writer import DIGEST, make_session

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import (
    ArrivalRefused,
    PermitExceeded,
    PublicationArrivalRefused,
    PublicationReadingRefused,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
    SharingEvidenceDisagrees,
    StatusTargetUnknown,
    StatusTerminal,
    WriteRefused,
)
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities
from beliefs.publication import MARKER_KIND
from beliefs.root import LifecycleState, open_world, open_world_read, read_lifecycle_state
from beliefs.session import SharingEvidence, read_ledger_evidence
from beliefs.session import writer as writer_module
from beliefs.session.ledger import LedgerReader, ledger_path, open_ledger_reader
from beliefs.world import Fresh, ReplicaOf, World
from beliefs.world.anchors import CorpusSubject, StoreSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet

SHARING = RequiredCapabilities.sharing()
OTHER = {
    "corpus": "0" * 32,
    "artifact": "0" * 64,
    "marker": "0" * 32,
    "world": "0" * 32,
    "view": f"coord:{'1' * 32}@{'2' * 32}",
}
"""Another well-formed value for each verified field: none is the root's."""


def shared(work: Path, *, required: RequiredCapabilities = SHARING) -> SimpleNamespace:
    """One local publication, its metadata-less copy, the evidence for it, and a
    recipient session whose invocation `A` holds a writer scoped to `required`."""
    s = published_source(work)
    published = publish_locally(s)
    copy, sibling = metadata_less_copy(s, published, work / "copy")
    session, writer = recipient_session(work, required=required)
    return SimpleNamespace(
        s=s,
        published=published,
        cid=published.corpus_id,
        copy=copy,
        sibling=sibling,
        evidence=evidence_for(published, sibling, s),
        observers=ObserverSet((ArtifactCarrier.from_bytes(sibling),)),
        session=session,
        writer=writer,
    )


def tree(root: Path) -> list[tuple[str, bytes | None]]:
    return sorted((str(p.relative_to(root)), p.read_bytes() if p.is_file() else None) for p in root.rglob("*"))


def admissions(x: SimpleNamespace) -> tuple:
    config = x.session.world_config
    assert config is not None
    return open_world_read(config).registry().admissions


def marker_of(root: Path):
    (marker,) = (node for node in ReadView.opened_at(root).iter_stored() if node.kind == MARKER_KIND)
    return marker


def tamper_one_selected_record(root: Path) -> None:
    """Rewrite one selected record's body to another canonical text: the ids,
    and so the publication layout, still hold; the chain no longer covers the bytes."""
    first = marker_of(root).facets[stored.COORDINATION_FACET]["selection"][0]
    node = ReadView.opened_at(root).get(first)
    tampered = node.model_copy(update={"body": "a body the chain never recorded"})
    (root / path_for_node_id(first)).write_text(node_to_markdown(tampered), encoding="utf-8")


def corrupt_one_selected_record(root: Path) -> None:
    """Overwrite one selected record's file with bytes that parse as no record."""
    first = marker_of(root).facets[stored.COORDINATION_FACET]["selection"][0]
    (root / path_for_node_id(first)).write_bytes(b"---\nid: [unclosed\n---\nnot a record\n")


def refuse_any_read(monkeypatch) -> None:
    """The evidence binding is the doors' first read of the copy: an entry
    refusal must be raised before it is reached."""

    def reached(*_args, **_kwargs):
        raise AssertionError("the door read the copy")

    monkeypatch.setattr(writer_module, "_bind_sharing_evidence", reached)


# --- restore_root ----------------------------------------------------------------------
def test_restore_root_grants_read_serviceability_and_ledgers_fetched_validated(certified_work):
    x = shared(certified_work)
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    line = x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    assert read_lifecycle_state(x.copy) is LifecycleState.READ_ONLY_SERVICEABLE
    assert (line.transition, line.verdict, line.corpus) == ("fetched", "validated", x.cid)
    assert x.session.invocation_sharing("A") == (line,)
    assert (line.invocation, line.marker, line.artifact, line.world, line.view, line.source, line.location) == (
        "A",
        x.evidence.marker,
        x.evidence.artifact,
        x.evidence.world,
        x.evidence.view,
        x.evidence.source,
        x.evidence.location,
    )


def test_restore_root_of_a_disagreeing_copy_ledgers_the_refusing_verdict_and_grants_nothing(certified_work):
    """Ruling R3: the evidence names the right sibling, so the binding holds; one
    record's bytes in the copy disagree with its chain, so the act refuses."""
    x = shared(certified_work)
    tamper_one_selected_record(x.copy)
    line = x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    assert line.transition == "fetched" and line.verdict != "validated"
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert x.session.invocation_sharing("A") == (line,)


# --- admit_publication -------------------------------------------------------------------
def test_admit_publication_admits_a_replica_under_the_session_actor_and_ledgers_admitted(certified_work):
    x = shared(certified_work)
    fetched = x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    line = x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    (record,) = (r for r in admissions(x) if r.corpus_id == x.cid)
    assert record.provenance == ReplicaOf(x.cid) and record.actor == x.session.actor
    assert (line.transition, line.verdict, line.corpus) == ("admitted", "validated", x.cid)
    assert x.session.invocation_sharing("A") == (fetched, line)


def test_admit_publication_of_an_unrestored_metadata_less_copy_admits_through_detached_verification(certified_work):
    """Review Focus 2: restore-first is science's order, not the door's."""
    x = shared(certified_work)
    line = x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    (record,) = (r for r in admissions(x) if r.corpus_id == x.cid)
    assert record.provenance == ReplicaOf(x.cid) and record.actor == x.session.actor
    assert (line.transition, line.verdict) == ("admitted", "validated")
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert x.session.invocation_sharing("A") == (line,)


def test_admit_publication_of_a_refuted_chain_propagates_the_arrival_refusal_and_appends_nothing(certified_work):
    """Review Focus 2: verification refutes the copy's chain; the refusal is the
    act's, no transition was made, and no line follows."""
    x = shared(certified_work)
    fetched = x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    assert fetched.verdict == "validated"
    tamper_one_selected_record(x.copy)
    before = admissions(x)
    with pytest.raises(ArrivalRefused):
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    assert admissions(x) == before
    assert x.session.invocation_sharing("A") == (fetched,)


# --- the layout and the evidence binding --------------------------------------------------
@pytest.mark.parametrize("door", ["restore_root", "admit_publication", "retire"])
def test_a_copy_with_an_unparseable_record_refuses_capture_damaged_before_the_act(certified_work, door):
    """A record the copy's reader cannot parse is a typed refusal from the
    binding, never a raw reader exception; no act runs. The corpus is not
    admitted, so `retire` reaching its registry read would refuse otherwise."""
    x = shared(certified_work)
    corrupt_one_selected_record(x.copy)
    before = admissions(x)
    with pytest.raises(PublicationReadingRefused) as caught:
        if door == "restore_root":
            x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
        elif door == "admit_publication":
            x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
        else:
            x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert (caught.value.reason, caught.value.corpus_id) == ("capture-damaged", x.cid)
    assert caught.value.__cause__ is not None
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert admissions(x) == before
    assert x.session.invocation_sharing("A") == ()


def test_a_copy_without_its_marker_refuses_the_layout_before_either_act(certified_work):
    x = shared(certified_work)
    (x.copy / path_for_node_id(marker_of(x.copy).id)).unlink()
    before = admissions(x)
    with pytest.raises(PublicationArrivalRefused) as restoring:
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    with pytest.raises(PublicationArrivalRefused) as admitting:
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    assert restoring.value.reason == admitting.value.reason == "marker-absent"
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert admissions(x) == before
    assert x.session.invocation_sharing("A") == ()


def test_sharing_evidence_disagrees_is_a_write_refusal_naming_its_field():
    refused = SharingEvidenceDisagrees("marker", "0" * 32, "1" * 32)
    assert isinstance(refused, WriteRefused)
    assert (refused.field, refused.claimed, refused.found) == ("marker", "0" * 32, "1" * 32)
    assert str(refused) == f"sharing evidence marker is {'0' * 32!r}; the root holds {'1' * 32!r}"


@pytest.mark.parametrize("field", ["corpus", "artifact", "marker", "world", "view"])
def test_mismatched_evidence_refuses_naming_the_field_before_the_act(certified_work, field):
    x = shared(certified_work)
    wrong = dataclasses.replace(x.evidence, **{field: OTHER[field]})
    before = admissions(x)
    with pytest.raises(SharingEvidenceDisagrees) as restoring:
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=wrong)
    with pytest.raises(SharingEvidenceDisagrees) as admitting:
        x.writer.admit_publication(x.copy, x.observers, evidence=wrong)
    for caught in (restoring.value, admitting.value):
        assert (caught.field, caught.claimed, caught.found) == (field, OTHER[field], getattr(x.evidence, field))
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert admissions(x) == before
    assert x.session.invocation_sharing("A") == ()


@pytest.mark.parametrize("field", ["source", "location"])
def test_evidence_that_cannot_encode_never_exists_for_either_door(certified_work, field):
    """The ledger encodes a line only after the act, so evidence it could not
    encode would leave a transition with no line. Such evidence refuses at
    construction; both doors take only an exact `SharingEvidence`, so neither
    can be called with it, and the copy, the registry and the ledger are
    untouched."""
    x = shared(certified_work)
    before = (tree(x.copy), admissions(x))
    with pytest.raises(ValueError, match=f"{field} must encode as UTF-8"):
        dataclasses.replace(x.evidence, **{field: "copy-\udcff"})
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert (tree(x.copy), admissions(x)) == before
    assert x.session.invocation_sharing("A") == ()


def test_a_subject_naming_another_corpus_refuses_on_the_corpus_field(certified_work):
    x = shared(certified_work)
    with pytest.raises(SharingEvidenceDisagrees) as caught:
        x.writer.restore_root(x.copy, CorpusSubject("0" * 32), x.observers, evidence=x.evidence)
    assert (caught.value.field, caught.value.claimed, caught.value.found) == ("corpus", x.cid, "0" * 32)
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert x.session.invocation_sharing("A") == ()


def test_an_artifact_no_carrier_holds_names_none_found(certified_work):
    x = shared(certified_work)
    with pytest.raises(SharingEvidenceDisagrees) as caught:
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), ObserverSet(()), evidence=x.evidence)
    assert (caught.value.field, caught.value.found) == ("artifact", "none")
    assert x.session.invocation_sharing("A") == ()


def test_the_artifact_binding_searches_every_carrier(certified_work):
    """Review Focus 1: the first carrier is another publication's artifact; the
    publication's own is second, and the binding finds it."""
    x = shared(certified_work)
    other_dest = x.s.base / "dest-other"
    other_dest.mkdir()
    destination = Destination.local(str(other_dest))
    other = publish_locally(x.s, destination=destination)
    assert other.corpus_id != x.cid
    other_sibling = (other_dest / f"{other.corpus_id}.head-artifact.v1").read_bytes()
    observers = ObserverSet((ArtifactCarrier.from_bytes(other_sibling), ArtifactCarrier.from_bytes(x.sibling)))
    fetched = x.writer.restore_root(x.copy, CorpusSubject(x.cid), observers, evidence=x.evidence)
    assert (fetched.transition, fetched.verdict) == ("fetched", "validated")
    assert read_lifecycle_state(x.copy) is LifecycleState.READ_ONLY_SERVICEABLE
    admitted = x.writer.admit_publication(x.copy, observers, evidence=x.evidence)
    assert (admitted.transition, admitted.verdict) == ("admitted", "validated")


# --- entry refusals -----------------------------------------------------------------------
def test_the_doors_require_their_family_first(certified_work, monkeypatch):
    x = shared(certified_work, required=RequiredCapabilities.coordination())
    copied = tree(x.copy)
    before = admissions(x)
    refuse_any_read(monkeypatch)
    with pytest.raises(PermitExceeded) as restoring:
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    assert "lifecycle" in str(restoring.value)
    with pytest.raises(PermitExceeded) as admitting:
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    assert "registry" in str(admitting.value)
    with pytest.raises(PermitExceeded) as retiring:
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert "registry" in str(retiring.value)
    assert tree(x.copy) == copied and read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert admissions(x) == before
    assert x.session.invocation_sharing("A") == ()


def test_stale_and_closed_writers_refuse_before_reading_the_copy(certified_work, monkeypatch):
    x = shared(certified_work)
    copied = tree(x.copy)
    refuse_any_read(monkeypatch)
    x.session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    with pytest.raises(SessionProtocolError):
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    with pytest.raises(SessionProtocolError):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert x.session.invocation_sharing("A") == ()
    x.session.close()
    with pytest.raises(SessionClosed):
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    with pytest.raises(SessionClosed):
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    with pytest.raises(SessionClosed):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert tree(x.copy) == copied and read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS


def test_a_store_subject_is_a_type_error(certified_work, monkeypatch):
    x = shared(certified_work)
    refuse_any_read(monkeypatch)
    with pytest.raises(TypeError):
        x.writer.restore_root(x.copy, StoreSubject(x.cid), x.observers, evidence=x.evidence)  # type: ignore[arg-type]
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert x.session.invocation_sharing("A") == ()


def test_a_session_without_a_world_configuration_refuses_admit_publication_and_retire(tmp_path, monkeypatch):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "share", DIGEST)
    writer = session.scoped(SHARING, "A")
    refuse_any_read(monkeypatch)
    evidence = SharingEvidence(
        "c" * 32, "5" * 32, "6" * 64, "b" * 32, f"coord:{'1' * 32}@{'2' * 32}", "provider:https://r/a", "https://r/a"
    )
    with pytest.raises(SessionProtocolError, match="no world configuration"):
        writer.admit_publication(tmp_path / "copy", ObserverSet(()), evidence=evidence)
    with pytest.raises(SessionProtocolError, match="no world configuration"):
        writer.retire(tmp_path / "copy", ObserverSet(()), evidence=evidence)
    assert session.invocation_sharing("A") == ()


# --- retire (retirement door design §5) ----------------------------------------------------
def adopted(work: Path) -> SimpleNamespace:
    """`shared`, with the copy admitted through the door as a replica of itself
    under invocation `A`; `x.admitted` is that line."""
    x = shared(work)
    x.admitted = x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    return x


def statuses(x: SimpleNamespace) -> tuple:
    """The registry's status records for the publication, read afresh."""
    config = x.session.world_config
    assert config is not None
    return tuple(r for r in open_world_read(config).registry().statuses if r.corpus_id == x.cid)


def full_world(x: SimpleNamespace) -> World:
    """The recipient world under another actor's full authority."""
    config = x.session.world_config
    assert config is not None
    return open_world(config, authority=FULL)


def ledger_sharing(session) -> tuple:
    return open_ledger_reader(session.operations_root, session.session_id).sharing()


def test_retire_retires_an_adopted_publication_under_the_session_actor_and_ledgers_retired(certified_work):
    x = adopted(certified_work)
    line = x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert (line.transition, line.verdict) == ("retired", "retired")
    assert (
        line.invocation,
        line.corpus,
        line.marker,
        line.artifact,
        line.world,
        line.view,
        line.source,
        line.location,
    ) == (
        "A",
        x.evidence.corpus,
        x.evidence.marker,
        x.evidence.artifact,
        x.evidence.world,
        x.evidence.view,
        x.evidence.source,
        x.evidence.location,
    )
    config = x.session.world_config
    assert config is not None
    status = open_world_read(config).status(x.cid)
    assert status.known and not status.live
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("retired", x.session.actor)
    assert x.session.invocation_sharing("A") == (x.admitted, line)
    assert ledger_sharing(x.session) == (x.admitted, line)


def test_a_repeat_in_a_later_invocation_ledgers_already_retired_with_no_second_record(certified_work):
    x = adopted(certified_work)
    first = x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    x.session.close_invocation("A", {"done": []})
    x.session.claim_invocation("B", "share", DIGEST)
    again = x.session.scoped(SHARING, "B").retire(x.copy, x.observers, evidence=x.evidence)
    assert (again.invocation, again.transition, again.verdict) == ("B", "retired", "already-retired")
    assert dataclasses.replace(again, invocation="A", verdict="retired", at=first.at) == first
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("retired", x.session.actor)
    assert x.session.invocation_sharing("B") == (again,)


@pytest.mark.parametrize("field", ["corpus", "artifact", "marker", "world", "view"])
def test_retire_with_mismatched_evidence_refuses_naming_the_field_before_the_act(certified_work, field):
    x = adopted(certified_work)
    wrong = dataclasses.replace(x.evidence, **{field: OTHER[field]})
    with pytest.raises(SharingEvidenceDisagrees) as caught:
        x.writer.retire(x.copy, x.observers, evidence=wrong)
    assert (caught.value.field, caught.value.claimed, caught.value.found) == (
        field,
        OTHER[field],
        getattr(x.evidence, field),
    )
    assert statuses(x) == ()
    assert x.session.invocation_sharing("A") == (x.admitted,)


def test_retire_of_a_corpus_never_admitted_refuses_status_target_unknown(certified_work):
    x = shared(certified_work)
    with pytest.raises(StatusTargetUnknown, match="not admitted"):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert statuses(x) == ()
    assert x.session.invocation_sharing("A") == ()


def test_retire_of_a_publication_admitted_fresh_refuses_status_target_unknown(certified_work):
    """Decision 2, step 6: the root has the publication layout and the evidence
    binds, but the corpus was not adopted through the sharing doors."""
    x = shared(certified_work)
    full_world(x).admit(x.copy, provenance=Fresh())
    with pytest.raises(StatusTargetUnknown, match="Fresh"):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert statuses(x) == ()
    assert x.session.invocation_sharing("A") == ()


def test_retire_of_a_departed_corpus_refuses_status_terminal_and_keeps_its_record(certified_work):
    x = adopted(certified_work)
    departed = full_world(x).depart(x.cid)
    with pytest.raises(StatusTerminal, match="departed"):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert statuses(x) == (departed,)
    assert x.session.invocation_sharing("A") == (x.admitted,)
    assert ledger_sharing(x.session) == (x.admitted,)


def racing(monkeypatch, status: str) -> None:
    """Another actor writes `status` for the corpus between the door's
    registry read and its act; the act then runs and refuses `StatusTerminal`."""
    original = World.retire

    def raced(self: World, corpus_id: str):
        full = open_world(self.config, authority=FULL)
        if status == "retired":
            original(full, corpus_id)
        else:
            full.depart(corpus_id)
        return original(self, corpus_id)

    monkeypatch.setattr(World, "retire", raced)


def test_a_racing_retirement_by_another_actor_ledgers_already_retired(certified_work, monkeypatch):
    x = adopted(certified_work)
    racing(monkeypatch, "retired")
    line = x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert (line.transition, line.verdict) == ("retired", "already-retired")
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("retired", FULL.actor)
    assert x.session.invocation_sharing("A") == (x.admitted, line)


def test_a_racing_departure_reraises_the_acts_status_terminal_and_appends_nothing(certified_work, monkeypatch):
    x = adopted(certified_work)
    racing(monkeypatch, "departed")
    with pytest.raises(StatusTerminal, match="already has terminal status"):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("departed", FULL.actor)
    assert x.session.invocation_sharing("A") == (x.admitted,)
    assert ledger_sharing(x.session) == (x.admitted,)


@pytest.mark.parametrize("fault", ["write", "flush", "fsync"])
def test_a_failed_retired_append_ends_the_session_and_a_successor_ledgers_already_retired(
    certified_work, monkeypatch, fault
):
    """Decision 6: the status commits, then the `retired` append fails. Each
    fault is armed for the ledger's file alone, since `World.retire` writes
    and fsyncs the registry inside the same call."""
    x = adopted(certified_work)
    handle = x.session._ledger._file
    ledger_fd = handle.fileno()

    def failing(*_args):
        raise OSError(f"{fault} failed")

    if fault == "write":
        real_write = handle.write
        monkeypatch.setattr(handle, "write", lambda data: real_write(data[:17]))  # a short write
    elif fault == "flush":
        monkeypatch.setattr(handle, "flush", failing)
    else:
        real_fsync = os.fsync

        def fsync(fd: int) -> None:
            if fd == ledger_fd:
                failing()
            real_fsync(fd)

        monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(SessionLedgerFailed):
        x.writer.retire(x.copy, x.observers, evidence=x.evidence)
    monkeypatch.undo()

    assert x.session._index["A"].sharing == [x.admitted]
    for call in (
        lambda: x.writer.retire(x.copy, x.observers, evidence=x.evidence),
        lambda: x.session.invocation_sharing("A"),
        lambda: x.session.close_invocation("A", {"done": []}),
        x.session.close,
    ):
        with pytest.raises(SessionLedgerFailed):
            call()
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("retired", x.session.actor)

    first = open_ledger_reader(x.session.operations_root, x.session.session_id)
    if fault == "write":
        assert first.torn_tail
        assert first.sharing() == (x.admitted,)
    else:
        assert not first.torn_tail
        (admitted, lost) = first.sharing()
        assert admitted == x.admitted
        assert (lost.invocation, lost.corpus, lost.transition, lost.verdict) == ("A", x.cid, "retired", "retired")

    successor, writer = successor_session(x.session, required=SHARING)
    assert successor.actor != x.session.actor
    recovered = writer.retire(x.copy, x.observers, evidence=x.evidence)
    assert (recovered.corpus, recovered.transition, recovered.verdict) == (x.cid, "retired", "already-retired")
    (record,) = statuses(x)
    assert (record.status, record.actor) == ("retired", x.session.actor)
    evidence = read_ledger_evidence(successor.operations_root, successor.session_id)
    assert type(evidence) is LedgerReader and evidence.sharing() == (recovered,)
    if fault != "write":
        both = (*first.sharing()[1:], *evidence.sharing())
        assert [(line.corpus, line.transition, line.verdict) for line in both] == [
            (x.cid, "retired", "retired"),
            (x.cid, "retired", "already-retired"),
        ]


def test_close_waits_while_retire_holds_the_session_lock_and_completes_after_the_line(certified_work, monkeypatch):
    """Decision 5: a close from another thread while the door is inside
    `World.retire` waits on the session lock and runs after the line."""
    x = adopted(certified_work)
    retiring, release, close_waiting = threading.Event(), threading.Event(), threading.Event()
    order: list[str] = []

    def on_attempt(name: str, outcome: str) -> None:
        if name == "close" and outcome == "held-by-another":
            close_waiting.set()

    monkeypatch.setattr(x.session, "_lock", TracingLock(on_attempt))
    original = World.retire

    def blocking(self: World, corpus_id: str):
        retiring.set()
        assert release.wait(10)
        record = original(self, corpus_id)
        order.append("act")
        return record

    monkeypatch.setattr(World, "retire", blocking)
    lines: list = []

    def retire() -> None:
        lines.append(x.writer.retire(x.copy, x.observers, evidence=x.evidence))

    def close() -> None:
        assert retiring.wait(10)
        x.session.close_invocation("A", {"done": []})
        order.append("close")

    retirer = threading.Thread(target=retire, name="retire")
    closer = threading.Thread(target=close, name="close")
    retirer.start()
    assert retiring.wait(10)
    closer.start()
    assert close_waiting.wait(10)
    assert closer.is_alive()
    release.set()
    retirer.join(10)
    closer.join(10)

    assert not retirer.is_alive() and not closer.is_alive()
    assert order == ["act", "close"]
    (line,) = lines
    assert line.verdict == "retired"
    kinds = [
        json.loads(raw)["line"]
        for raw in ledger_path(x.session.operations_root, x.session.session_id).read_bytes().splitlines()
    ]
    assert kinds[-2:] == ["sharing", "invocation-close"]
