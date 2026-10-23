"""The sharing act doors on the scoped writer, over real roots on the certified
volume (sharing design §2 decisions 3–6, §4.4, §4.5, §6 "The sharing doors").

A publication exported by the local publish act is copied without its metadata
sibling; a recipient's attended session restores and admits it through
`ScopedWriter.restore_root` and `ScopedWriter.admit_publication`, each door
binding the caller's evidence to the root before its act and ledgering one
`sharing` line after it."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from types import SimpleNamespace

import pytest
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from session_doors_fixture import (
    evidence_for,
    metadata_less_copy,
    publish_locally,
    published_source,
    recipient_session,
)
from test_session_writer import DIGEST, make_session

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import (
    ArrivalRefused,
    PermitExceeded,
    PublicationArrivalRefused,
    PublicationReadingRefused,
    SessionClosed,
    SessionProtocolError,
    SharingEvidenceDisagrees,
    WriteRefused,
)
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities
from beliefs.publication import MARKER_KIND
from beliefs.root import LifecycleState, open_world_read, read_lifecycle_state
from beliefs.session import SharingEvidence
from beliefs.session import writer as writer_module
from beliefs.world import ReplicaOf
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
@pytest.mark.parametrize("door", ["restore_root", "admit_publication"])
def test_a_copy_with_an_unparseable_record_refuses_capture_damaged_before_the_act(certified_work, door):
    """A record the copy's reader cannot parse is a typed refusal from the
    binding, never a raw reader exception; neither act runs."""
    x = shared(certified_work)
    corrupt_one_selected_record(x.copy)
    before = admissions(x)
    with pytest.raises(PublicationReadingRefused) as caught:
        if door == "restore_root":
            x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
        else:
            x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
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


@pytest.mark.parametrize("door", ["restore_root", "admit_publication"])
@pytest.mark.parametrize("field", ["source", "location"])
def test_evidence_that_cannot_encode_refuses_before_either_door_acts(certified_work, field, door):
    """The ledger encodes a line only after the act; evidence it could not
    encode would leave a transition with no line. The evidence refuses first,
    so neither door is reached and the copy, the registry and the ledger
    are untouched."""
    x = shared(certified_work)
    before = (tree(x.copy), admissions(x))
    with pytest.raises(ValueError, match=f"{field} must encode as UTF-8"):
        evidence = dataclasses.replace(x.evidence, **{field: "copy-\udcff"})
        if door == "restore_root":
            x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=evidence)
        else:
            x.writer.admit_publication(x.copy, x.observers, evidence=evidence)
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
    assert x.session.invocation_sharing("A") == ()
    x.session.close()
    with pytest.raises(SessionClosed):
        x.writer.restore_root(x.copy, CorpusSubject(x.cid), x.observers, evidence=x.evidence)
    with pytest.raises(SessionClosed):
        x.writer.admit_publication(x.copy, x.observers, evidence=x.evidence)
    assert tree(x.copy) == copied and read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS


def test_a_store_subject_is_a_type_error(certified_work, monkeypatch):
    x = shared(certified_work)
    refuse_any_read(monkeypatch)
    with pytest.raises(TypeError):
        x.writer.restore_root(x.copy, StoreSubject(x.cid), x.observers, evidence=x.evidence)  # type: ignore[arg-type]
    assert read_lifecycle_state(x.copy) is LifecycleState.METADATA_LESS
    assert x.session.invocation_sharing("A") == ()


def test_a_session_without_a_world_configuration_refuses_admit_publication(tmp_path, monkeypatch):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "share", DIGEST)
    writer = session.scoped(SHARING, "A")
    refuse_any_read(monkeypatch)
    evidence = SharingEvidence(
        "c" * 32, "5" * 32, "6" * 64, "b" * 32, f"coord:{'1' * 32}@{'2' * 32}", "provider:https://r/a", "https://r/a"
    )
    with pytest.raises(SessionProtocolError, match="no world configuration"):
        writer.admit_publication(tmp_path / "copy", ObserverSet(()), evidence=evidence)
    assert session.invocation_sharing("A") == ()
