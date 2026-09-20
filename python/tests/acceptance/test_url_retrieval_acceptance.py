"""Cut 35: URL retrieval and the acquisition operation through the certified durable boundary.

One test per declaration unit (H4-a–b, G9-a, R10-a, T5-a–c, T7-a–b, T1-a,
T2-a–d, T4-a–b, BI-1–11), each the slice's unit test re-composed over the
durable roots: registered observer and store roots on the certified volume,
the composition root's holdings seam, and — where the unit reads the
session — the attended session's ledgered context. The acceptance transport
is the production pinned connection over the in-process TLS server (spec
§11.2); the scripted fake is used only where a behaviour cannot be provoked
over real framing (the unpinnable context, the raised exception classes).
No test reaches the network.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import socket
import ssl
import subprocess
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

import pytest
from atoms.chain.model import SettledEntry
from atoms.core.errors import PreconditionRefused
from authority import FULL
from fixtures_cut4 import raw_write, reopen
from holdings_transport_fixtures import PUBLIC, LocalTlsServer, Scripted, Served, scripted_seam, tls_seam
from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_to_markdown
from profiles import BASE, pins_for
from test_deletion_acceptance import _audit_log
from test_holdings_acquire import BOUNDS, A, B, digest, ok, registrations_of, request, resource
from test_holdings_boundary import _intents, context
from test_holdings_transport import SIGNED_HOP, TOKEN_HOST_HOP
from test_operation_writes import proposition
from test_session_routes import ACQUIRES, ACQUIRES_AND_ADDS, _acquisition_request, _durable_session
from test_session_writer import DIGEST, make_session
from test_world_log_codecs import Chain, ChainOutcome, state_at

from beliefs import boundary as boundary_values
from beliefs import root as science_root
from beliefs import stored
from beliefs.acquisition import validity_refusal
from beliefs.corpus import CorpusWriter, _operation_lock_for, corpus_check
from beliefs.dataset import DatasetDeclaration, Declared, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.errors import (
    AcquisitionRefused,
    BuildContended,
    DeletionKindExcluded,
    SessionProtocolError,
    StoreWriteRefused,
)
from beliefs.holdings import qualify
from beliefs.holdings import transport as transport_module
from beliefs.holdings.acquire import SKIPPED_AFTER_STOP, Stop, acquire
from beliefs.holdings.adapter import DatasetAnswer, dataset_observations
from beliefs.holdings.boundary import ActContext, InconclusiveLook, PublishedLook, look, write
from beliefs.holdings.receipt import derive_holdings, output_digest, validate_holdings_receipt
from beliefs.holdings.records import Found, StoreLocator, url_locator
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.holdings.transport import (
    Approved,
    PinnedHTTPSConnection,
    PinningUnavailable,
    RetrievalBounds,
    pinned_connection,
)
from beliefs.intents import evidence
from beliefs.intents.shapes import DecodedIntent, ObservationEvidence, decode_intent
from beliefs.report import (
    CLOSED,
    UNFINISHED,
    ByteLocatorUntested,
    LocatorEntry,
    OperationIntent,
    PublishedObservation,
    RetrievalFailed,
    cite,
    completion,
)
from beliefs.root import (
    durable_executor_factory,
    durable_operation_port,
    init_corpus_root,
    init_store_root,
    open_corpus,
    open_world,
)
from beliefs.session import open_ledger_reader, reconcile_sessions
from beliefs.world import anchors, registry, rules, verify
from beliefs.world.logmodel import IntentEntryView, MalformedView, RegisteredEntryView, WellFormedView
from beliefs.world.registry import WorldConfig

DATA = url_locator("https://example.org/data")
CUT34_MERGE = "3873d16"
"""The main-checkout commit cut 34 was verified at: the holdings rule bundle before this lane's successor rule."""


# --- fixtures and helpers ----------------------------------------------------------


@dataclass(frozen=True)
class Observer:
    ctx: Any
    store_id: str
    writer: CorpusWriter


def _observer(certified_work: Path, name: str) -> Observer:
    """A registered observer root with a manifest, a store root, the production seam."""
    observer_root, store_root = certified_work / name, certified_work / f"{name}-store"
    init_corpus_root(observer_root, authority=FULL)
    store_id = init_store_root(store_root, authority=FULL)
    ctx = ActContext(observer_root, store_root, "observer", "instrument", FULL, science_root.holdings_seam(), profile=BASE)
    writer = open_corpus(observer_root, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return Observer(ctx, store_id, writer)


@pytest.fixture()
def observer(certified_work) -> Observer:
    """Task 5's `acquisition` fixture shape over the durable root."""
    ctx, store_id = context(certified_work)
    writer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return Observer(ctx, store_id, writer)


@pytest.fixture()
def session(certified_work):
    """Task 6's `_durable_session`, under its own directory so its roots never collide with the observer's."""
    base = certified_work / "session"
    base.mkdir()
    return _durable_session(base)


@contextmanager
def served(script: dict[str, Served]) -> Iterator[Any]:
    """The production pinned connection over the in-process TLS server (spec §11.2)."""
    with LocalTlsServer(script) as server:
        yield tls_seam(server)


def chain(root: Path):
    view = science_root._log_seam().inspect_registered(root)
    assert isinstance(view, WellFormedView)
    return view.entries


def intents(root: Path) -> list[IntentEntryView]:
    return _intents(root)


def kinds(root: Path) -> list[str | None]:
    return [json.loads(entry.payload).get("kind") for entry in intents(root)]


def registrations(root: Path) -> list[RegisteredEntryView]:
    return [entry for entry in chain(root) if isinstance(entry, RegisteredEntryView)]


def operation_intent(root: Path) -> IntentEntryView:
    (entry,) = [entry for entry in intents(root) if json.loads(entry.payload).get("kind") == "acquisition"]
    return entry


def stored_kinds(writer: CorpusWriter) -> list[str]:
    return sorted(node.kind for node in writer.read_view.iter_stored())


def observation_files(root: Path) -> list[Path]:
    directory = root / "holdings-observation"
    return sorted(directory.iterdir()) if directory.exists() else []


def observation_values(writer: CorpusWriter):
    return [stored.holdings_observation_value(node) for node in writer.read_view.iter_stored() if node.kind == "holdings-observation"]


def read_only_store(ctx, certified_work: Path):
    """A store the engine refuses to mutate, from the production seam (Task 5)."""
    replica = certified_work / "replica"
    science_root.replicate_root(ctx.store_root, replica, authority=FULL)
    return replace(ctx, store_root=replica)


def world_over(certified_work: Path, *roots: Path):
    config = WorldConfig(certified_work / "world", "f" * 32, tuple(roots))
    science_root.init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    for root in roots:
        world.admit(root, provenance=registry.Fresh())
    binding = rules.install_rule_binding(world, holdings_rule_bundle())
    return world, binding


def reduce(world, corpus_id: str, binding):
    seam = science_root._log_seam()
    return derive_holdings(world, frozenset({corpus_id}), binding, chain_view=seam.inspect_registered, state_facts=seam.state_facts)


def _raise_publish(_root, _plan, _fulfills):
    raise ExecutionError("cannot publish", index=None, applied=0)


# --- H4 ----------------------------------------------------------------------------


def test_h4a_an_established_remote_found_publishes_or_the_look_raises(observer, session, tmp_path):
    """H4-a: an established remote `found` publishes; a publication failure after
    `Retrieved` raises and the chain carries the unmatched re-check intent, no transient report."""
    ctx = observer.ctx
    with served({"/data": Served(body=b"payload")}) as (seam, log):
        result = look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
        assert isinstance(result, PublishedLook)
        assert result.record.outcome == Found(digest(b"payload"))
        result.retrieved.path.unlink()
        assert len(observation_files(ctx.observer_root)) == 1
        ((method, target, headers),) = log.requests
        assert (method, target, headers["Host"], headers["Accept-Encoding"]) == ("GET", "/data", "example.org", "identity")

        # The publication failure, through the durable session's ledgered context.
        session.claim_invocation("A", "acquire", DIGEST)
        scoped = session.scoped(ACQUIRES, "A")
        sctx = scoped.holdings_context(instrument="inst")
        failing = replace(sctx, seam=replace(sctx.seam, publish_fulfilling=_raise_publish))
        before = len(intents(session.corpus_root))
        with pytest.raises(ExecutionError, match="cannot publish"):
            look(failing, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "s2")
        assert len(log.requests) == 2
    assert not (session.corpus_root / "holdings-observation").exists()
    after = intents(session.corpus_root)
    assert len(after) == before + 1
    unmatched = after[-1]
    assert json.loads(unmatched.payload)["kind"] == "re-check"
    assert not any(entry.fulfills == unmatched.digest for entry in registrations(session.corpus_root))
    assert not any(node.kind == "act-report" for node in reopen(session.corpus_root).iter_stored())
    assert list((tmp_path / "s2").iterdir()) == []


def test_h4b_an_inconclusive_remote_attempt_mints_nothing_and_never_absent(observer, tmp_path):
    """H4-b: timeout, truncation, the ceiling, 404, 500, a refused hop, an unpinnable
    context — each mints nothing, never `absent`, carries no digest, and the standing
    URL observation's identity is unchanged."""
    ctx = observer.ctx
    scratch = tmp_path / "s"
    script = {
        "/data": Served(body=b"payload"),
        "/partial": Served(body=b"partial", truncate_chunked=True),
        "/five": Served(body=b"12345"),
        "/missing": Served(404),
        "/broken": Served(500),
        "/hop": Served(302, {"Location": "https://mirror.example.org/x"}),
    }
    with served(script) as (seam, _log):
        standing = look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=scratch)
        assert isinstance(standing, PublishedLook)
        standing.retrieved.path.unlink()
        identity = standing.record.identity()
        timeout, _ = scripted_seam({"/data": Scripted(200, {}, (b"ab",), raise_on_read=socket.timeout("timed out"))})  # noqa: UP041
        unpinnable, _ = scripted_seam({}, unpinnable=True)
        private = replace(seam, resolve=lambda host, _p: [PUBLIC] if host == "example.org" else ["10.0.0.1"])
        attempts = [
            ("timeout", timeout, DATA, BOUNDS, InconclusiveLook("retrieval-failed", "transport failure: timeout")),
            ("truncated", seam, url_locator("https://example.org/partial"), BOUNDS, InconclusiveLook("retrieval-failed", "transport failure: protocol")),
            ("ceiling", seam, url_locator("https://example.org/five"), RetrievalBounds(5.0, 4, 3), InconclusiveLook("retrieval-failed", "exceeded the 4-byte streaming ceiling")),
            ("404", seam, url_locator("https://example.org/missing"), BOUNDS, InconclusiveLook("retrieval-failed", "status 404")),
            ("500", seam, url_locator("https://example.org/broken"), BOUNDS, InconclusiveLook("retrieval-failed", "status 500")),
            ("refused hop", private, url_locator("https://example.org/hop"), BOUNDS, InconclusiveLook("retrieval-failed", "redirect hop 1 refused: non-public-address")),
            ("unpinnable", unpinnable, DATA, BOUNDS, InconclusiveLook("byte-locator-untested", "unpinnable")),
        ]
        for label, attempt, locator, bounds, expected in attempts:
            standing_for = (standing.record,) if locator == DATA else ()
            result = look(ctx, locator, bounds=bounds, seam=attempt, scratch=scratch, standing=standing_for)
            assert result == expected, label
            assert not hasattr(result, "digest"), label
            files = observation_files(ctx.observer_root)
            assert len(files) == 1 and files[0].stem == identity, label
            assert standing.record.identity() == identity
    for node in reopen(ctx.observer_root).iter_stored():
        if node.kind == "holdings-observation":
            assert cast(dict[str, object], stored.holdings_observation_value(node).facet()["outcome"])["finding"] == "found"
    assert len(intents(ctx.observer_root)) == 1 + len(attempts)
    assert len([e for e in registrations(ctx.observer_root) if e.fulfills is not None]) == 1  # the manifest's registration fulfills nothing
    assert list(scratch.iterdir()) == []


# --- G9 ----------------------------------------------------------------------------


def test_g9a_a_url_location_holds_without_a_store_copy(observer, certified_work, tmp_path):
    """G9-a: `found` at a URL, no store copy → held; the URL then fails → still held."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None and outcome.stop is None
    assert not any(isinstance(value.location, StoreLocator) for value in observation_values(writer))
    world, binding = world_over(certified_work, ctx.observer_root)
    declaration = DatasetDeclaration((ResourceDeclaration("a", digest(A)),))
    active, blocked, _ = reduce(world, writer.corpus_id, binding)
    answer = dataset_observations(declaration, active, blocked)
    assert isinstance(answer, DatasetAnswer)
    assert answer.observations[0].location == "url:https://example.org/a"
    assert isinstance(admission_state(declaration, answer.observations), Held)

    failing, log = scripted_seam({"/a": Scripted(500, {}, (b"",))})
    relook = look(ctx, url_locator("https://example.org/a"), bounds=BOUNDS, seam=failing, scratch=tmp_path / "s")
    assert relook == InconclusiveLook("retrieval-failed", "status 500") and len(log.requests) == 1
    again, blocked_again, _ = reduce(world, writer.corpus_id, binding)
    assert output_digest(again) == output_digest(active) and blocked_again == []
    after = dataset_observations(declaration, again, blocked_again)
    assert isinstance(after, DatasetAnswer) and isinstance(admission_state(declaration, after.observations), Held)


# --- R10 ---------------------------------------------------------------------------


def test_r10a_the_acquisition_records_dataset_provenance(observer, tmp_path):
    """R10-a: the minted dataset's facet carries `locator`, `attested_by` = actor and
    `retrieval` → the acquisition report whose entries reference the observations;
    `validity_refusal` is `None`. The run boundary's refusal of a URL input is cut 3's
    R10 arm (`n2_arms_cut3.py`), cited and not re-run here."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    req = request(resource("a", "a", store_id=observer.store_id))
    outcome = acquire(ctx, writer, req, seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None
    dataset = writer.read_view.get(outcome.dataset.id)
    assert dataset.facets["empirical-observation"] == {"locator": req.locator, "attested_by": ctx.actor, "retrieval": outcome.report_ref}
    report = writer.read_view.get(outcome.report_ref)
    assert stored.act_report_facet(report)["operation"] == "acquisition"
    refs = [entry.outcome.ref for entry in outcome.report.entries if isinstance(entry.outcome, PublishedObservation)]
    assert len(refs) == 2
    for ref in refs:
        assert writer.read_view.get(ref).kind == "holdings-observation"
    assert validity_refusal(writer.read_view, dataset, BASE) is None


# --- T5 ----------------------------------------------------------------------------


def test_t5a_a_began_request_never_spells_untested(observer, tmp_path):
    """T5-a: a `Failed` retrieval spells `retrieval-failed`; the classification is read
    from the transport's phase value, never from a message."""
    ctx, writer = observer.ctx, observer.writer
    with served({"/a": Served(500)}) as (seam, log):
        outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert len(log.requests) == 1
    (entry,) = outcome.entries
    assert entry.outcome == RetrievalFailed("status 500")
    assert type(entry.outcome) is not ByteLocatorUntested
    assert outcome.stop == Stop("a", "look", "status 500") and outcome.dataset is None


def test_t5b_a_preflight_refusal_and_a_post_stop_skip_spell_distinct_reasons(observer, tmp_path):
    """T5-b: a preflight refusal and a post-stop skip: both `byte-locator-untested`, reasons distinct."""
    ctx, writer = observer.ctx, observer.writer
    seam, log = scripted_seam({}, unpinnable=True)
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b"), resource("c", "c")), seam=seam, scratch=tmp_path / "s")
    outcomes = [entry.outcome for entry in outcome.entries]
    assert outcomes == [ByteLocatorUntested("unpinnable"), ByteLocatorUntested(SKIPPED_AFTER_STOP), ByteLocatorUntested(SKIPPED_AFTER_STOP)]
    assert ByteLocatorUntested("unpinnable").reason != ByteLocatorUntested(SKIPPED_AFTER_STOP).reason
    assert log.requests == []
    assert kinds(ctx.observer_root) == ["acquisition", "re-check"]


def test_t5c_no_entry_outcome_constructs_an_observation(observer, tmp_path, monkeypatch):
    """T5-c: a report whose ref resolves to no observation refuses at the close and the
    operation reads unfinished; every published ref in a real report resolves to an
    observation an act published under a chain intent's token."""
    ctx, writer = observer.ctx, observer.writer
    from beliefs.holdings import acquire as module

    real = module.look

    def forged(*args, **kwargs):
        return replace(real(*args, **kwargs), ref="holdings-observation:" + "0" * 64)

    monkeypatch.setattr(module, "look", forged)
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(AcquisitionRefused, match="no act published"):
        acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert "act-report" not in stored_kinds(writer)
    entry = operation_intent(ctx.observer_root)
    intent = OperationIntent("acquisition", json.loads(entry.payload)["event_token"], ctx.actor)
    assert completion(intent, registrations_of(chain(ctx.observer_root), entry.digest, "act-report:" + "0" * 64), {}) == UNFINISHED

    monkeypatch.setattr(module, "look", real)
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=observer.store_id)), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None
    tokens = {json.loads(e.payload)["event_token"] for e in intents(ctx.observer_root) if json.loads(e.payload).get("kind") in ("re-check", "write")}
    published = [entry.outcome.ref for entry in outcome.report.entries if isinstance(entry.outcome, PublishedObservation)]
    assert len(published) == 2
    for ref in published:
        node = writer.read_view.get(ref)
        assert node.kind == "holdings-observation"
        assert stored.holdings_observation_value(node).event_token in tokens


# --- T7 ----------------------------------------------------------------------------


def test_t7a_the_dataset_and_its_report_publish_in_one_transaction_in_one_root(observer, certified_work, tmp_path):
    """T7-a: dataset and report in one registered transaction; a wrong-root writer refuses before the intent."""
    ctx, writer = observer.ctx, observer.writer
    seam, log = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=observer.store_id)), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None
    entries = chain(ctx.observer_root)
    intent = operation_intent(ctx.observer_root)
    fulfilling = [e for e in entries if isinstance(e, RegisteredEntryView) and e.fulfills == intent.digest]
    assert len(fulfilling) == 1
    closing = fulfilling[0]
    assert closing is [e for e in entries if isinstance(e, RegisteredEntryView)][-1]
    view = writer.read_view
    assert {path for path, _ in closing.final} == {writer._relative_path(outcome.dataset), writer._relative_path(view.get(outcome.report_ref))}

    other_root = certified_work / "other"
    init_corpus_root(other_root, authority=FULL)
    other = open_corpus(other_root, authority=FULL, profile=BASE)
    other.adopt_manifest(profile=pins_for(BASE))
    before_observer, before_other = chain(ctx.observer_root), chain(other_root)
    requests = len(log.requests)
    with pytest.raises(AcquisitionRefused, match="one root"):
        acquire(ctx, other, request(resource("b", "b")), seam=seam, scratch=tmp_path / "s")
    assert chain(ctx.observer_root) == before_observer and chain(other_root) == before_other
    assert len(log.requests) == requests
    assert "act-report" not in stored_kinds(other)


def test_t7b_the_address_is_unchanged_while_the_record_bytes_move(certified_work, tmp_path):
    """T7-b: two roots, the same bytes: equal dataset ids, distinct node-content and corpus-state identities."""
    one, two = _observer(certified_work, "one"), _observer(certified_work, "two")
    outcomes = []
    for index, observer in enumerate((one, two)):
        seam, _ = scripted_seam({"/a": ok(A)})
        outcomes.append(acquire(observer.ctx, observer.writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / f"s{index}"))
    first, second = outcomes
    assert first.dataset is not None and second.dataset is not None
    assert first.dataset.id == second.dataset.id == dataset_address(DatasetDeclaration((ResourceDeclaration("a", digest(A)),)))
    assert first.report_ref != second.report_ref
    assert first.dataset.facets["empirical-observation"]["retrieval"] != second.dataset.facets["empirical-observation"]["retrieval"]
    assert node_to_markdown(one.writer.read_view.get(first.dataset.id)) != node_to_markdown(two.writer.read_view.get(second.dataset.id))
    assert registry.corpus_state_identity(one.ctx.observer_root) != registry.corpus_state_identity(two.ctx.observer_root)


# --- T1 ----------------------------------------------------------------------------


def test_t1a_a_raw_written_report_is_undetected_on_read_and_refuted_under_anchors(observer):
    """T1-a: a raw-written self-consistent report: readable, `corpus_check` silent; log
    verification under an anchored observer set refutes; under none, unresolvable."""
    ctx, writer = observer.ctx, observer.writer
    token = secrets.token_hex(16)
    writer._append_operation_intent("acquisition", token, ctx.actor)
    now = "2026-09-20T00:00:00Z"
    report = boundary_values._mint_acquisition_report(
        OperationIntent("acquisition", token, ctx.actor), observer=ctx.observer, instrument=ctx.instrument,
        opened_at=now, closed_at=now,
        entries=(LocatorEntry("url:https://example.org/a", RetrievalFailed("status 500"), BOUNDS.instrument_inputs()),),
    )
    node = stored.act_report_node(report)
    path = raw_write(ctx.observer_root, node)
    relative = path.relative_to(ctx.observer_root).as_posix()
    view = reopen(ctx.observer_root)
    assert view.holds(node.id)
    assert stored.act_report_facet(view.get(node.id))["event_token"] == token
    assert corpus_check(view, BASE) == ()
    writer._reconstruct()
    assert writer.read_view.holds(node.id)

    anchored = _audit_log(writer)
    assert anchored.outcome == "refuted"
    assert f"head:{relative}" in {finding.ref for finding in anchored.findings if finding.code == "replay-disagreement"}
    config = WorldConfig(writer.root.parent / f"{writer.root.name}-world", "f" * 32, (writer.root,))
    unanchored = science_root.audit_log(config, anchors.CorpusSubject(writer.corpus_id), writer.root, verify.ObserverSet(()), actor="alice")
    assert unanchored.outcome == "unresolvable"


# --- T2 ----------------------------------------------------------------------------


def test_t2a_an_acquisition_closes_through_exactly_one_report_after_its_intent(observer, tmp_path):
    """T2-a: acquisition to success: one intent, one qualifying report, closed, the intent before every act."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=observer.store_id)), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None
    reports = [node for node in writer.read_view.iter_stored() if node.kind == "act-report"]
    assert len(reports) == 1 and reports[0].id == outcome.report_ref
    entries = chain(ctx.observer_root)
    intent_entry = operation_intent(ctx.observer_root)
    intent = OperationIntent("acquisition", json.loads(intent_entry.payload)["event_token"], ctx.actor)
    fulfilling = registrations_of(entries, intent_entry.digest, outcome.report_ref)
    assert len(fulfilling) == 1
    assert completion(intent, fulfilling, {outcome.report_ref: outcome.report}) == CLOSED
    position = entries.index(intent_entry)
    acts = [i for i, e in enumerate(entries) if isinstance(e, IntentEntryView) and json.loads(e.payload).get("kind") in ("re-check", "write")]
    registered = [i for i, e in enumerate(entries) if isinstance(e, RegisteredEntryView) and e.fulfills is not None]
    assert acts and registered and position < min(acts) and position < min(registered)  # the manifest's registration precedes and fulfills nothing


def test_t2b_root_selection_failure_begins_no_act(observer, tmp_path):
    """T2-b: a store-less session with materialization, and a port-less writer: no request, no intent, no record."""
    (tmp_path / "session").mkdir()
    session, ports = make_session(tmp_path / "session")
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({"/a": ok(A)})
    req = _acquisition_request()
    with pytest.raises(SessionProtocolError, match="no store"):
        scoped.acquire(req, instrument="inst", scratch=tmp_path / "s", seam=transport)
    assert ports[-1].calls == [] and log.requests == []

    ctx = observer.ctx
    portless = CorpusWriter(ctx.observer_root, durable_executor_factory(), authority=FULL, profile=BASE)
    before = chain(ctx.observer_root)
    with pytest.raises(AcquisitionRefused, match="no operation port"):
        acquire(ctx, portless, request(resource("a", "a", store_id=observer.store_id)), seam=transport, scratch=tmp_path / "s")
    assert chain(ctx.observer_root) == before and log.requests == []
    assert not any(node.kind in ("act-report", "dataset", "holdings-observation") for node in reopen(ctx.observer_root).iter_stored())


class RefusingPort:
    """A durable port whose intent append the engine refuses."""

    def __init__(self, inner) -> None:
        self._inner = inner

    @property
    def profile(self):
        return self._inner.profile

    @property
    def authority(self):
        return self._inner.authority

    def append_intent(self, payload: bytes) -> str:
        raise ExecutionError("refused", index=None, applied=0)

    def preflight(self, plan) -> None:
        self._inner.preflight(plan)

    def execute(self, plan) -> None:
        self._inner.execute(plan)

    def execute_fulfilling(self, plan, fulfills: str) -> str:
        return self._inner.execute_fulfilling(plan, fulfills)

    def execute_fulfilling_guarded(self, plan, fulfills: str, *, guard, fallback):
        return self._inner.execute_fulfilling_guarded(plan, fulfills, guard=guard, fallback=fallback)


def test_t2c_intent_append_failure_begins_no_act(observer, tmp_path):
    """T2-c: the intent append refused by the port: no request, no record."""
    ctx, writer = observer.ctx, observer.writer
    port = RefusingPort(durable_operation_port(ctx.observer_root, FULL, profile=BASE))
    seam, log = scripted_seam({"/a": ok(A)})
    before, files = chain(ctx.observer_root), sorted(p for p in ctx.observer_root.rglob("*") if p.is_file())
    with pytest.raises(ExecutionError, match="refused"):
        acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s", port=port)
    assert log.requests == []
    assert chain(ctx.observer_root) == before
    assert sorted(p for p in ctx.observer_root.rglob("*") if p.is_file()) == files
    assert not any(node.kind in ("act-report", "dataset", "holdings-observation") for node in reopen(ctx.observer_root).iter_stored())


def test_t2d_a_second_fulfillment_is_refused_and_a_raw_one_is_malformed(observer, certified_work, tmp_path):
    """T2-d: a second `execute_fulfilling` on the operation intent is refused by the coordinator;
    a raw second fulfillment reads `MalformedView` with kind `duplicate-fulfillment`."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    intent_digest = operation_intent(ctx.observer_root).digest
    with pytest.raises(ExecutionError, match="already fulfills"):
        writer._publish_operation_report(outcome.report, intent_digest, operations=(writer._create_op(proposition("p")),))
    assert len([e for e in registrations(ctx.observer_root) if e.fulfills == intent_digest]) == 1

    copy = certified_work / "copy"
    shutil.copytree(ctx.observer_root, copy, symlinks=True)
    forged = Chain(copy)
    forged.digests = [entry.digest for entry in chain(ctx.observer_root)]
    report_path = writer._relative_path(writer.read_view.get(outcome.report_ref))
    state = state_at(copy, report_path)
    registration = forged.registration("tx-raw", ((report_path, state),), ((report_path, state),), fulfills=intent_digest)
    forged.append(SettledEntry(txid="tx-raw", registration=registration, outcome=ChainOutcome.COMMITTED))
    view = science_root._log_seam().inspect_registered(copy)
    assert isinstance(view, MalformedView), view
    assert view.defect.kind == "duplicate-fulfillment"


# --- T4 ----------------------------------------------------------------------------


def test_t4a_reports_leave_the_projection_unchanged_and_an_unfinished_operation_blocks_nothing(observer, certified_work, tmp_path):
    """T4-a: reports added and removed: reducer outputs byte-identical; an unmatched
    acquisition intent blocks nothing."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    first = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert first.dataset is not None
    world, binding = world_over(certified_work, ctx.observer_root)
    active, blocked, receipt = reduce(world, writer.corpus_id, binding)
    assert len(active) == 1 and blocked == []
    digests = (output_digest(active), output_digest(blocked))

    unpinnable, log = scripted_seam({}, unpinnable=True)
    second = acquire(ctx, writer, request(resource("a", "a")), seam=unpinnable, scratch=tmp_path / "s")
    assert second.dataset is None and log.requests == []
    assert kinds(ctx.observer_root) == ["acquisition", "re-check", "acquisition", "re-check"]
    assert len([node for node in writer.read_view.iter_stored() if node.kind == "act-report"]) == 2
    assert len(observation_files(ctx.observer_root)) == 1
    added_active, added_blocked, added_receipt = reduce(world, writer.corpus_id, binding)
    assert (output_digest(added_active), output_digest(added_blocked)) == digests
    assert added_receipt.coverage != receipt.coverage

    with pytest.raises(DeletionKindExcluded):  # T8: no ordinary API deletes a report (families design §3.0)
        writer.delete(second.report_ref)
    os.unlink(writer.root / writer._relative_path(writer.read_view.get(second.report_ref)))
    writer._reconstruct()
    assert not writer.read_view.holds(second.report_ref)
    removed_active, removed_blocked, _ = reduce(world, writer.corpus_id, binding)
    assert (output_digest(removed_active), output_digest(removed_blocked)) == digests

    writer._append_operation_intent("acquisition", secrets.token_hex(16), ctx.actor)
    assert kinds(ctx.observer_root)[-1] == "acquisition"
    open_active, open_blocked, _ = reduce(world, writer.corpus_id, binding)
    assert open_blocked == []
    assert output_digest(open_active) == digests[0]


def test_t4b_deleting_a_referenced_observation_moves_the_active_set_and_not_the_report(observer, certified_work, tmp_path):
    """T4-b: deleting a referenced URL observation moves the active set; the report is
    byte-unchanged and `cite` resolves. The managed `delete` refuses a
    `holdings-observation` by static kind exclusion (families design §3.0) whether or
    not a report references it — the report confers nothing — so the removal that
    exercises the record layer is raw, as cut 18's G8 arm removes a record."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A), "/lone": ok(B)})
    unreferenced = look(ctx, url_locator("https://example.org/lone"), bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
    assert isinstance(unreferenced, PublishedLook)
    unreferenced.retrieved.path.unlink()
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    (entry,) = outcome.entries[:1]
    assert isinstance(entry.outcome, PublishedObservation)
    ref = entry.outcome.ref
    world, binding = world_over(certified_work, ctx.observer_root)
    active, blocked, _ = reduce(world, writer.corpus_id, binding)
    assert sorted(str(member["head"]) for member in active) == sorted((ref.partition(":")[2], unreferenced.record.identity())) and blocked == []
    report_bytes = node_to_markdown(writer.read_view.get(outcome.report_ref))

    for target in (ref, unreferenced.ref):  # the refusal is the kind's, referenced or not
        with pytest.raises(DeletionKindExcluded):
            writer.delete(target)
    os.unlink(writer.root / writer._relative_path(writer.read_view.get(ref)))
    writer._reconstruct()

    assert not writer.read_view.holds(ref)
    after_active, after_blocked, _ = reduce(world, writer.corpus_id, binding)
    assert [member["head"] for member in after_active] == [unreferenced.record.identity()] and after_blocked == []
    assert node_to_markdown(writer.read_view.get(outcome.report_ref)) == report_bytes
    assert cite(outcome.report, 0) == entry
    assert ref in str(stored.act_report_facet(writer.read_view.get(outcome.report_ref))["entries"][0])


# --- boundary invariants -----------------------------------------------------------


def test_bi1_two_spellings_of_one_url_are_one_location(observer, certified_work, tmp_path):
    """BI-1: the canonicalization table through the durable path: two spellings of one URL are one location."""
    ctx, writer = observer.ctx, observer.writer
    seam, log = scripted_seam({"/a/b": ok(A)})
    for spelling in ("https://EXAMPLE.org:443/a/./b", "https://example.org/a/b"):
        result = look(ctx, url_locator(spelling), bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
        assert isinstance(result, PublishedLook)
        result.retrieved.path.unlink()
    assert [headers["Host"] for _m, _t, headers in log.requests] == ["example.org", "example.org"]
    world, binding = world_over(certified_work, ctx.observer_root)
    active, blocked, _ = reduce(world, writer.corpus_id, binding)
    assert blocked == []
    assert len(active) == 2
    assert {member["location"] for member in active} == {"url:https://example.org/a/b"}
    assert {cast(dict[str, str], member["outcome"])["digest"] for member in active} == {digest(A)}


def test_bi2_no_hop_bytes_enter_any_record_or_reason(observer, tmp_path):
    """BI-2: a presigned hop and a token-bearing-hostname hop, refused at preflight and
    by certificate validation: the query, the token and the host occur in no published
    record, no entry, no reason and no exception text; the entry names ordinal and category."""
    ctx, writer = observer.ctx, observer.writer
    scratch = tmp_path / "s"
    secrets_ = ("X-Amz-Signature", "deadbeefcafe", "AKIA", "tok3n-9f2a", "bucket.s3.example", "tok3n-9f2a.example.net")

    def private_resolver(host: str, _port: int) -> list[str]:
        return [PUBLIC] if host == "example.org" else ["10.1.1.1"]

    runs = []
    for hop in (SIGNED_HOP, TOKEN_HOST_HOP):
        seam, log = scripted_seam({"/a": Scripted(302, {"Location": hop})})
        runs.append((replace(seam, resolve=private_resolver), log, "redirect hop 1 refused: non-public-address"))
    for transport, log, reason in runs:
        outcome = acquire(ctx, writer, request(resource("a", "a")), seam=transport, scratch=scratch)
        assert outcome.stop == Stop("a", "look", reason) and outcome.dataset is None
        assert len(log.requests) == 1
        _assert_no_secret(ctx, writer, outcome, secrets_, scratch)
    with served({"/a": Served(302, {"Location": TOKEN_HOST_HOP})}) as (seam, log):
        outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert outcome.stop == Stop("a", "look", "transport failure: tls") and outcome.dataset is None
    assert len(log.requests) == 1 and [host for host, _a, _p in log.dialled] == ["example.org", "tok3n-9f2a.example.net"]
    _assert_no_secret(ctx, writer, outcome, secrets_, scratch)


def _assert_no_secret(ctx, writer, outcome, secrets_, scratch: Path) -> None:
    (entry,) = outcome.entries
    assert isinstance(entry.outcome, RetrievalFailed)
    haystacks = [entry.subject, entry.outcome.reason, outcome.stop.reason, node_to_markdown(writer.read_view.get(outcome.report_ref))]
    for root in (ctx.observer_root, scratch):
        if root.exists():
            haystacks.extend(path.read_bytes().decode("utf-8", "replace") for path in root.rglob("*") if path.is_file())
    for secret in secrets_:
        for text in haystacks:
            assert secret not in text, secret


def test_bi3_the_pinned_connection_dials_the_validated_address(observer, tmp_path, monkeypatch):
    """BI-3: the pinned connection dials the validated address with name validation; an unpinnable context issues no request."""
    dialled: list[tuple[str, int]] = []
    wrapped: list[str] = []
    sentinel = object()

    class FakeContext:
        check_hostname = True
        verify_mode = ssl.CERT_REQUIRED

        def wrap_socket(self, sock, *, server_hostname: str):
            assert sock is sentinel
            wrapped.append(server_hostname)
            return sentinel

    monkeypatch.setattr(transport_module.socket, "create_connection", lambda address, timeout: dialled.append(address) or sentinel)
    connection = PinnedHTTPSConnection("host.example", PUBLIC, 443, 5.0, FakeContext())  # type: ignore[arg-type]
    connection.connect()
    assert dialled == [(PUBLIC, 443)] and wrapped == ["host.example"]

    for check_hostname, verify_mode in ((False, ssl.CERT_REQUIRED), (True, ssl.CERT_NONE)):
        class Lax:
            pass

        lax = Lax()
        lax.check_hostname = check_hostname  # type: ignore[attr-defined]
        lax.verify_mode = verify_mode  # type: ignore[attr-defined]
        monkeypatch.setattr(transport_module.ssl, "create_default_context", lambda lax=lax: lax)
        with pytest.raises(PinningUnavailable):
            pinned_connection(Approved("host.example", 443, "/a", "host.example", PUBLIC), 5.0)

    monkeypatch.setattr(transport_module.socket, "create_connection", lambda *a, **k: pytest.fail("a socket was opened"))
    ctx, writer = observer.ctx, observer.writer
    seam, log = scripted_seam({"/a": ok(A)}, unpinnable=True)
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert outcome.entries[0].outcome == ByteLocatorUntested("unpinnable")
    assert log.requests == [] and log.dialled == []


def test_bi4_the_ceiling_finalizes_no_digest(observer, tmp_path):
    """BI-4: the ceiling ends the stream; no digest is finalized or published; the bound is named on the entry."""
    ctx, writer = observer.ctx, observer.writer
    scratch = tmp_path / "s"
    bounds = RetrievalBounds(timeout_seconds=5.0, max_bytes=64, max_redirects=3)
    req = replace(request(resource("a", "a")), bounds=bounds)
    with served({"/a": Served(body=b"z" * 4096)}) as (seam, log):
        outcome = acquire(ctx, writer, req, seam=seam, scratch=scratch)
    (entry,) = outcome.entries
    assert entry.outcome == RetrievalFailed("exceeded the 64-byte streaming ceiling")
    assert outcome.dataset is None and outcome.stop == Stop("a", "look", "exceeded the 64-byte streaming ceiling")
    assert observation_files(ctx.observer_root) == []
    assert not scratch.exists() or list(scratch.iterdir()) == []
    assert len(log.requests) == 1
    assert "holdings-observation" not in stored_kinds(writer)


def test_bi5_an_expectation_mismatch_mints_no_dataset_and_reports_mismatch(observer, certified_work, tmp_path):
    """BI-5: `found(D')` with `expected = D`: no dataset; the adapter over the real reduction reports `mismatch`."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a", expected=digest(B))), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is None and outcome.stop is None
    (entry,) = outcome.entries
    assert isinstance(entry.outcome, PublishedObservation)
    record = stored.holdings_observation_value(writer.read_view.get(entry.outcome.ref))
    assert record.outcome == Found(digest(A)) and record.expected == digest(B)
    assert "dataset" not in stored_kinds(writer)
    world, binding = world_over(certified_work, ctx.observer_root)
    active, blocked, _ = reduce(world, writer.corpus_id, binding)
    declaration = DatasetDeclaration((ResourceDeclaration("a", digest(B)),))
    answer = dataset_observations(declaration, active, blocked)
    assert isinstance(answer, DatasetAnswer) and answer.observations[0].digest == digest(A)
    state = admission_state(declaration, answer.observations)
    assert isinstance(state, Declared)
    assert [finding.outcome for finding in state.findings] == ["no-matching-observation-in-coverage", "mismatch"]


def test_bi6_an_already_held_address_mints_no_second_dataset(observer, tmp_path):
    """BI-6: an already-held address: no second dataset, observation and report published, the old `retrieval` unchanged."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    first = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    second = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert first.dataset is not None
    assert second.dataset is None and second.stop is None
    assert [type(e) for e in second.entries] == [LocatorEntry]
    assert writer.read_view.holds(second.report_ref)
    assert writer.read_view.get(first.dataset.id).facets["empirical-observation"]["retrieval"] == first.report_ref
    assert len(observation_files(ctx.observer_root)) == 2
    assert stored_kinds(writer).count("dataset") == 1


def test_bi7_the_url_looks_intent_blocks_nothing(observer, certified_work, tmp_path):
    """BI-7: a crash between the URL look's intent and its publication: the reducer reports no blocked entry."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    crashing = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=_raise_publish))
    with pytest.raises(ExecutionError, match="cannot publish"):
        look(crashing, url_locator("https://example.org/a"), bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
    (intent,) = intents(ctx.observer_root)
    assert json.loads(intent.payload)["kind"] == "re-check"
    assert not any(e.fulfills == intent.digest for e in registrations(ctx.observer_root))
    world, binding = world_over(certified_work, ctx.observer_root)
    active, blocked, _ = reduce(world, writer.corpus_id, binding)
    assert blocked == [] and active == []
    row = {"digest": intent.digest, "entry": {"payload": intent.payload.hex(), "kind": "intent"}}
    decoded = qualify.decode_holdings_intent(row)
    assert decoded is not None and decoded["location"] == "url:https://example.org/a"
    assert qualify.qualify_intent(decoded, (), {}) == "unmatched"  # the rule's own qualification over the chain: no registration, no unresolved row


def test_bi8_no_lock_is_held_across_the_request(observer, session, tmp_path, monkeypatch):
    """BI-8: no lock across the request — the root lock (a helper-thread probe) and the session lock (a concurrent add)."""
    from beliefs import corpus as corpus_module

    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    seen: list[bool] = []
    inner = seam.connect

    def probe() -> None:
        lock = _operation_lock_for(ctx.observer_root)
        try:
            with lock.capture():
                seen.append(True)
        except BuildContended:
            seen.append(False)

    def probing(approved, timeout):
        thread = threading.Thread(target=probe)
        thread.start()
        thread.join(5)
        return inner(approved, timeout)

    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=replace(seam, connect=probing), scratch=tmp_path / "s")
    assert outcome.dataset is not None and seen == [True]

    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES_AND_ADDS, "A")
    owned: list[bool] = []
    real_enter = corpus_module._SettlingHold.__enter__

    def entering(self):
        owned.append(session._lock._is_owned())  # type: ignore[attr-defined]
        return real_enter(self)

    monkeypatch.setattr(corpus_module._SettlingHold, "__enter__", entering)
    transport, _ = scripted_seam({"/a": ok(A)})
    opened, added = threading.Event(), threading.Event()

    def gated_connect(approved, timeout):
        opened.set()
        assert added.wait(30), "the concurrent add did not complete while the request was open"
        return transport.connect(approved, timeout)

    def add_while_open():
        assert opened.wait(30)
        scoped.add(proposition("p"))
        added.set()

    partner = threading.Thread(target=add_while_open, daemon=True)
    partner.start()
    routed = scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "s2", seam=replace(transport, connect=gated_connect))
    partner.join(30)
    assert not partner.is_alive() and routed.dataset is not None
    assert owned and all(owned)
    session.close_invocation("A", {"done": []})
    session.close()
    assert len(open_ledger_reader(session.operations_root, session.session_id).acts()) == 3


def _show(path: str) -> bytes:
    repo = Path(__file__).resolve().parents[3]
    return subprocess.run(["git", "-C", str(repo), "show", f"{CUT34_MERGE}:{path}"], check=True, capture_output=True).stdout


def _cut34_bundle() -> rules.RuleBundle:
    """The holdings rule bundle exactly as the tree held it before this lane's successor rule."""
    package = "python/src/beliefs/holdings"
    names = ("holdings.basic.yaml", "holdings.blocked.yaml", "holdings.empty.yaml", "holdings.unresolved.yaml")
    fixtures = tuple((name, _show(f"{package}/rules_v1/fixtures/{name}")) for name in names)
    implementation = _show(f"{package}/qualify.py") + b"\n\n" + _show(f"{package}/rules_v1/holdings.py")
    return rules.RuleBundle(symbol="reduce_holdings", fixtures=fixtures, implementation=implementation)


def test_bi9_the_successor_rule_keeps_old_receipts_validatable(observer, certified_work, tmp_path):
    """BI-9: the successor rule: the old binding's receipt still validates where held; the new fixture reduces."""
    ctx, writer = observer.ctx, observer.writer
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=tmp_path / "s")
    assert outcome.dataset is not None
    held = _observer(certified_work, "held")
    published = write(held.ctx, StoreLocator(held.store_id, "held.bin"), b"held bytes")
    assert isinstance(published.record.outcome, Found)

    world, binding = world_over(certified_work, ctx.observer_root, held.ctx.observer_root)
    seam_ = science_root._log_seam()
    new_receipt = reduce(world, writer.corpus_id, binding)[2]
    assert validate_holdings_receipt(world, new_receipt, chain_view=seam_.inspect_registered, state_facts=seam_.state_facts).outcome == "validated"

    old_bundle = _cut34_bundle()
    assert any(name == "holdings.url.yaml" for name, _ in holdings_rule_bundle().fixtures)
    assert not any(name == "holdings.url.yaml" for name, _ in old_bundle.fixtures)
    old_identity = rules.binding_for(old_bundle)
    assert old_identity.rule_identity != binding.rule_identity
    assert old_identity.implementation_identity != binding.implementation_identity
    old_binding = rules.install_rule_binding(world, old_bundle)
    assert old_binding == old_identity
    old_active, _, old_receipt = reduce(world, held.writer.corpus_id, old_binding)
    assert len(old_active) == 1 and old_receipt.rule_identity == old_identity.rule_identity
    assert validate_holdings_receipt(world, old_receipt, chain_view=seam_.inspect_registered, state_facts=seam_.state_facts).outcome == "validated"


def test_bi10_url_intents_and_observations_decode_and_reconcile(session, certified_work, tmp_path):
    """BI-10: a URL re-check intent and its fulfilling observation decode through
    `intents/evidence.py` and the generated helper; `reconcile` reports nothing."""
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({"/a": ok(A)})
    outcome = scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "s", seam=transport)
    assert outcome.dataset is not None and len(log.requests) == 1
    session.close_invocation("A", {"done": []})
    session.close()
    config = WorldConfig(certified_work / "session" / "world", session.world_id, (session.corpus_root,))
    assert reconcile_sessions(config, session.operations_root) == ()

    (recheck,) = [e for e in intents(session.corpus_root) if json.loads(e.payload).get("kind") == "re-check"]
    decoded = decode_intent(recheck.digest, recheck.payload)
    assert isinstance(decoded, DecodedIntent) and decoded.shape == "holdings"
    value = cast(Mapping[str, str], decoded.value)
    assert value["location"] == "url:https://example.org/a" and value["kind"] == "re-check"
    token = value["event_token"]
    (path,) = observation_files(session.corpus_root)
    relative = path.relative_to(session.corpus_root).as_posix()
    assert evidence.record_layout_path(relative)
    assert evidence.decode_record(relative, path.read_bytes()) == ObservationEvidence("url:https://example.org/a", token)


def test_bi11_the_materialization_classification(observer, certified_work, tmp_path):
    """BI-11: the materialization classification, five blocks: a production store
    refusal on the first and on the last resource stops with no dataset; a publication
    failure after a committed materialization propagates and reads unfinished; a
    terminal session failure propagates; an unexpected engine failure propagates."""
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    scratch = tmp_path / "s"

    # (1) the production refusal on the first resource: a stop, the rest skipped, nothing minted
    read_only = read_only_store(ctx, certified_work)
    with pytest.raises(StoreWriteRefused) as refused:
        write(read_only, StoreLocator(store_id, "probe.bin"), b"x")
    cause = refused.value.__cause__
    assert isinstance(cause, ExecutionError) and cause.applied == 0
    assert type(cause.__cause__) is PreconditionRefused  # the replica's refusal, in the routine set (decision 10)
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    first = acquire(read_only, writer, request(resource("a", "a", store_id=store_id), resource("b", "b")), seam=seam, scratch=scratch)
    assert first.dataset is None
    assert first.stop is not None and (first.stop.resource, first.stop.phase) == ("a", "materialize")
    assert [type(e) for e in first.entries] == [LocatorEntry, LocatorEntry]
    assert first.entries[1].outcome == ByteLocatorUntested(SKIPPED_AFTER_STOP)
    assert len(log.requests) == 1 and writer.read_view.holds(first.report_ref)
    assert list(scratch.iterdir()) == []

    # (2) on the last resource: the earlier entries kept, nothing minted
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    last = acquire(read_only, writer, request(resource("a", "a"), resource("b", "b", store_id=store_id)), seam=seam, scratch=scratch)
    assert last.dataset is None and last.stop is not None
    assert (last.stop.resource, last.stop.phase) == ("b", "materialize")
    assert all(type(e.outcome) is PublishedObservation for e in last.entries) and len(log.requests) == 2

    # (3) a publication failure after a committed materialization: propagates, unfinished
    calls = {"n": 0}
    inner = ctx.seam.publish_fulfilling

    def flaky(root, plan, fulfills):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ExecutionError("publish", index=None, applied=0) from PreconditionRefused("shape")
        return inner(root, plan, fulfills)

    flaky_ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=flaky))
    reports = stored_kinds(writer).count("act-report")
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="publish"):
        acquire(flaky_ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert kinds(ctx.observer_root)[-3:] == ["acquisition", "re-check", "write"]
    assert (ctx.store_root / "acquired" / "a.bin").read_bytes() == A
    assert stored_kinds(writer).count("act-report") == reports
    entry = [e for e in intents(ctx.observer_root) if json.loads(e.payload).get("kind") == "acquisition"][-1]
    intent = OperationIntent("acquisition", json.loads(entry.payload)["event_token"], ctx.actor)
    assert completion(intent, registrations_of(chain(ctx.observer_root), entry.digest, "act-report:" + "0" * 64), {}) == UNFINISHED
    assert list(scratch.iterdir()) == []

    # (4) a terminal session failure propagates and is never a stop
    def closed(_root, _path, _content):
        raise SessionProtocolError("the invocation is no longer current")

    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(SessionProtocolError):
        acquire(replace(ctx, seam=replace(ctx.seam, store_write=closed)), writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert stored_kinds(writer).count("act-report") == reports

    # (5) negative: an unexpected engine failure propagates and reads unfinished, never a stop
    def internal(_root, _path, _content):
        raise ExecutionError("internal", index=None, applied=None) from RuntimeError("boom")

    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="internal"):
        acquire(replace(ctx, seam=replace(ctx.seam, store_write=internal)), writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert stored_kinds(writer).count("act-report") == reports
    assert "dataset" not in stored_kinds(writer)
