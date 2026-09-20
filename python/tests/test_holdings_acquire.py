"""The acquisition operation (url-retrieval design §6)."""

from __future__ import annotations

import json
import threading
from dataclasses import replace
from hashlib import sha256

import pytest
from atoms.core.errors import PreconditionRefused
from authority import FULL
from holdings_transport_fixtures import Scripted, scripted_seam
from nodes.core.errors import ExecutionError
from profiles import BASE, WITH_BIOLOGY, pins_for
from test_holdings_boundary import _intents, context  # Task 4's helper and the store/observer context

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import CorpusWriter, _operation_lock_for
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import (
    AcquisitionRefused,
    BuildContended,
    MalformedRecord,
    SessionProtocolError,
    ValidationRefused,
)
from beliefs.holdings.acquire import SKIPPED_AFTER_STOP, AcquisitionRequest, ResourceRequest, Stop, acquire
from beliefs.holdings.adapter import DatasetAnswer, dataset_observations
from beliefs.holdings.records import Found, StoreLocator, url_locator
from beliefs.holdings.transport import RetrievalBounds
from beliefs.report import (
    CLOSED,
    ByteLocatorUntested,
    DeclarationPinEntry,
    LocatorEntry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    PublishedObservation,
    Registration,
    RetrievalFailed,
    completion,
)
from beliefs.root import durable_executor_factory, open_corpus
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView

BOUNDS = RetrievalBounds(timeout_seconds=5.0, max_bytes=1 << 20, max_redirects=3)
A, B, C = b"alpha bytes", b"beta bytes", b"gamma bytes"
REGISTERED_DOMAIN_FACETS = {"biology/gene-axis": {"axis": "rows"}}
"""A facet the biology fixture contract registers on `dataset` (`profiles.WITH_BIOLOGY`)."""


def digest(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def ok(body: bytes) -> Scripted:
    return Scripted(200, {"Content-Length": str(len(body))}, (body,))


def resource(name: str, path: str, *, expected=None, store_id=None) -> ResourceRequest:
    return ResourceRequest(
        name=name, url=url_locator(f"https://example.org/{path}"), expected=expected,
        materialize=None if store_id is None else StoreLocator(store_id, f"acquired/{name}.bin"),
    )


def request(*resources: ResourceRequest, title="Dryad record 1") -> AcquisitionRequest:
    return AcquisitionRequest(title=title, locator="url:https://example.org/dataset/1", resources=resources, bounds=BOUNDS)


@pytest.fixture()
def acquisition(certified_work, tmp_path):
    ctx, store_id = context(certified_work)
    writer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return ctx, store_id, writer, tmp_path / "scratch"


def chain(root):
    view = science_root._log_seam().inspect_registered(root)
    assert isinstance(view, WellFormedView)
    return view.entries


def registrations_of(entries, intent_digest: str, pointer: str) -> tuple[Registration, ...]:
    """The registrations fulfilling the operation intent, each pointing at the report the close published."""
    fulfilling = [e for e in entries if isinstance(e, RegisteredEntryView) and e.fulfills == intent_digest]
    token = json.loads(next(e for e in entries if isinstance(e, IntentEntryView) and e.digest == intent_digest).payload)["event_token"]
    return tuple(Registration(token, pointer) for _ in fulfilling)


def test_the_happy_path_mints_the_dataset_beside_its_report_in_one_transaction(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A)})
    assert not writer.read_view.holds("holdings-observation:" + "0" * 64)  # the index is built and cached before the looks publish past it
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert outcome.stop is None and outcome.dataset is not None
    address = dataset_address(DatasetDeclaration((ResourceDeclaration("a", digest(A)),)))
    assert address is not None
    assert outcome.dataset.id == address
    facet = outcome.dataset.facets["empirical-observation"]
    assert facet == {"locator": "url:https://example.org/dataset/1", "attested_by": ctx.actor, "retrieval": outcome.report_ref}
    kinds = [type(entry) for entry in outcome.entries]
    assert kinds == [LocatorEntry, ManagedMutationEntry, DeclarationPinEntry]
    assert outcome.entries[0].subject == "url:https://example.org/a"
    assert isinstance(outcome.entries[0], LocatorEntry)
    assert outcome.entries[0].instrument_inputs == BOUNDS.instrument_inputs()
    assert outcome.entries[2] == DeclarationPinEntry(address, PinnedDeclaration(address))
    view = writer.read_view
    assert view.holds(outcome.report_ref) and view.holds(address)
    entries = chain(ctx.observer_root)
    intents = [e for e in entries if isinstance(e, IntentEntryView)]
    assert json.loads(intents[0].payload)["kind"] == "acquisition"  # the operation intent precedes every act
    assert [json.loads(i.payload).get("kind") for i in intents[1:]] == ["re-check", "write"]
    closing = [e for e in entries if isinstance(e, RegisteredEntryView)][-1]
    paths = {path for path, _ in closing.final}
    assert paths == {writer._relative_path(outcome.dataset), writer._relative_path(view.get(outcome.report_ref))}
    registrations = registrations_of(entries, intents[0].digest, outcome.report_ref)
    assert len(registrations) == 1
    intent = OperationIntent("acquisition", json.loads(intents[0].payload)["event_token"], ctx.actor)
    assert completion(intent, registrations, {outcome.report_ref: outcome.report}) == CLOSED
    assert stored.act_report_facet(view.get(outcome.report_ref))["event_token"] == intent.event_token
    assert len(log.requests) == 1
    assert list(scratch.iterdir()) == []


def test_a_failing_second_look_closes_with_no_dataset_and_a_look_stop(acquisition):
    ctx, _, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A), "/b": Scripted(500, {}, (b"",))})
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b")), seam=seam, scratch=scratch)
    assert outcome.dataset is None
    assert outcome.stop == Stop("b", "look", "status 500")
    assert [type(e.outcome) for e in outcome.entries] == [PublishedObservation, RetrievalFailed]
    assert writer.read_view.holds(outcome.report_ref)
    assert len(log.requests) == 2


def test_a_preflight_refusal_on_the_first_resource_skips_the_rest_with_zero_requests(acquisition):
    ctx, _, writer, scratch = acquisition
    seam, log = scripted_seam({}, unpinnable=True)
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b"), resource("c", "c")), seam=seam, scratch=scratch)
    assert [e.outcome for e in outcome.entries] == [
        ByteLocatorUntested("unpinnable"), ByteLocatorUntested(SKIPPED_AFTER_STOP), ByteLocatorUntested(SKIPPED_AFTER_STOP)
    ]
    assert log.requests == []
    assert [json.loads(i.payload).get("kind") for i in _intents(ctx.observer_root)] == ["acquisition", "re-check"]


def test_an_expectation_mismatch_mints_no_dataset_and_the_adapter_reports_mismatch(acquisition):
    ctx, _, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a", expected=digest(B))), seam=seam, scratch=scratch)
    assert outcome.dataset is None and outcome.stop is None
    first = outcome.entries[0].outcome
    assert isinstance(first, PublishedObservation)
    record = stored.holdings_observation_value(writer.read_view.get(first.ref))
    assert record.outcome == Found(digest(A)) and record.expected == digest(B)
    answer = dataset_observations(
        DatasetDeclaration((ResourceDeclaration("a", digest(B)),)),
        [{"head": "h", "location": "url:https://example.org/a", "outcome": {"finding": "found", "digest": digest(A)}, "expected": digest(B), "history": []}],
        [],
    )
    assert isinstance(answer, DatasetAnswer) and answer.observations[0].digest == digest(A)


def test_an_already_held_address_mints_no_second_dataset(acquisition):
    ctx, _, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    first = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    second = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert second.dataset is None and second.stop is None
    assert [type(e) for e in second.entries] == [LocatorEntry]
    assert first.dataset is not None
    assert writer.read_view.get(first.dataset.id).facets["empirical-observation"]["retrieval"] == first.report_ref
    assert len(list((ctx.observer_root / "holdings-observation").iterdir())) == 2


@pytest.mark.parametrize(
    ("spoil", "refusal"),
    [
        ("wrong-root", AcquisitionRefused),
        ("no-port", AcquisitionRefused),
        ("store-less-materialize", PreconditionRefused),  # the engine's own refusal of a genesis read over no root
        ("scratch-under-root", MalformedRecord),
        ("foreign-store", AcquisitionRefused),
        ("malformed-facet", ValidationRefused),
    ],
)
def test_every_pre_intent_refusal_leaves_the_chain_and_corpus_untouched_and_issues_no_request(
    acquisition, certified_work, spoil, refusal
):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A)})
    before = chain(ctx.observer_root)
    req = request(resource("a", "a", store_id=store_id))
    kwargs = {"seam": seam, "scratch": scratch}
    if spoil == "wrong-root":
        other = certified_work / "other"
        science_root.init_corpus_root(other, authority=FULL)
        writer = open_corpus(other, authority=FULL, profile=BASE)
    elif spoil == "no-port":
        # The same (singleton) durable factory the fixture's writer opened the root with; a different one refuses at construction.
        writer = CorpusWriter(ctx.observer_root, durable_executor_factory(), authority=FULL, profile=BASE)
    elif spoil == "store-less-materialize":
        ctx = replace(ctx, store_root=certified_work / "nowhere")
    elif spoil == "scratch-under-root":
        kwargs["scratch"] = ctx.observer_root / "scratch"
    elif spoil == "foreign-store":
        req = request(replace(resource("a", "a"), materialize=StoreLocator("f" * 32, "x.bin")))
    elif spoil == "malformed-facet":
        req = AcquisitionRequest(
            title="t", locator="url:https://example.org/dataset/1", resources=(resource("a", "a"),), bounds=BOUNDS,
            domain_facets={"ns/x": {"k": object()}},  # namespaced, so the request accepts it; the profile's payload validation does not
        )
    with pytest.raises(refusal):
        acquire(ctx, writer, req, **kwargs)
    assert chain(ctx.observer_root) == before
    assert log.requests == []
    assert not any(node.kind in ("act-report", "dataset", "holdings-observation") for node in writer.read_view.iter_stored())


def test_the_request_refuses_an_unnamespaced_domain_facet_as_a_value():
    with pytest.raises(MalformedRecord, match="namespaced"):
        AcquisitionRequest(
            title="t", locator="url:https://example.org/d", resources=(resource("a", "a"),), bounds=BOUNDS,
            domain_facets={"unnamespaced": {"k": 1}},
        )


def test_a_registered_domain_facet_lands_on_the_minted_dataset(certified_work, tmp_path):
    ctx, _ = context(certified_work)
    ctx = replace(ctx, profile=WITH_BIOLOGY)
    writer = open_corpus(ctx.observer_root, authority=FULL, profile=WITH_BIOLOGY)
    writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    seam, _ = scripted_seam({"/a": ok(A)})
    facets = REGISTERED_DOMAIN_FACETS
    req = AcquisitionRequest(title="t", locator="url:https://example.org/d", resources=(resource("a", "a"),), bounds=BOUNDS, domain_facets=facets)
    outcome = acquire(ctx, writer, req, seam=seam, scratch=tmp_path / "scratch")
    assert outcome.dataset is not None
    for key, payload in facets.items():
        assert outcome.dataset.facets[key] == dict(payload)
    assert set(outcome.dataset.facets) == {"dataset", "empirical-observation", "semantic-identity", *facets}


def _read_only_store(ctx, certified_work):
    """A store the engine refuses to mutate, from the production seam (Task 4's last test)."""
    replica = certified_work / "replica"
    science_root.replicate_root(ctx.store_root, replica, authority=FULL)
    return replace(ctx, store_root=replica)


def test_a_store_refusal_on_the_first_resource_stops_skips_and_mints_nothing(acquisition, certified_work):
    ctx, store_id, writer, scratch = acquisition
    ctx = _read_only_store(ctx, certified_work)
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=store_id), resource("b", "b")), seam=seam, scratch=scratch)
    assert outcome.dataset is None
    assert outcome.stop is not None and (outcome.stop.resource, outcome.stop.phase) == ("a", "materialize")
    assert [type(e) for e in outcome.entries] == [LocatorEntry, LocatorEntry]
    assert outcome.entries[1].outcome == ByteLocatorUntested(SKIPPED_AFTER_STOP)
    assert len(log.requests) == 1
    assert writer.read_view.holds(outcome.report_ref)
    assert list(scratch.iterdir()) == []


def test_a_store_refusal_on_the_last_resource_keeps_the_earlier_entries_and_mints_nothing(acquisition, certified_work):
    ctx, store_id, writer, scratch = acquisition
    ctx = _read_only_store(ctx, certified_work)
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b", store_id=store_id)), seam=seam, scratch=scratch)
    assert outcome.dataset is None and outcome.stop is not None
    assert outcome.stop.phase == "materialize" and outcome.stop.resource == "b"
    assert [type(e) for e in outcome.entries] == [LocatorEntry, LocatorEntry]
    assert all(type(e.outcome) is PublishedObservation for e in outcome.entries)
    assert len(log.requests) == 2


def test_a_publication_failure_after_a_committed_materialization_propagates_and_reads_unfinished(acquisition):
    ctx, store_id, writer, scratch = acquisition
    calls = {"n": 0}
    inner = ctx.seam.publish_fulfilling

    def flaky(root, plan, fulfills):
        calls["n"] += 1
        if calls["n"] == 2:  # the look's observation published; the write's does not
            raise ExecutionError("publish", index=None, applied=0) from PreconditionRefused("shape")
        return inner(root, plan, fulfills)

    ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=flaky))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="publish"):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    intents = _intents(ctx.observer_root)
    assert [json.loads(i.payload).get("kind") for i in intents] == ["acquisition", "re-check", "write"]
    assert (ctx.store_root / "acquired" / "a.bin").read_bytes() == A
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
    assert list(scratch.iterdir()) == []


def test_an_unexpected_engine_failure_in_the_store_propagates_and_is_never_a_stop(acquisition):
    ctx, store_id, writer, scratch = acquisition

    def internal(_root, _path, _content):
        raise ExecutionError("internal", index=None, applied=None) from RuntimeError("boom")

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=internal))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="internal"):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_a_session_failure_between_the_look_and_the_write_propagates(acquisition):
    ctx, store_id, writer, scratch = acquisition

    def closed(_root, _path, _content):
        raise SessionProtocolError("the invocation is no longer current")

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=closed))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(SessionProtocolError):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)


def test_no_lock_is_held_across_the_request(acquisition):
    """The probe runs on a helper thread: the root lock nests on its owning
    thread, so only another thread can tell a held lock from a free one. A
    capture never waits — it refuses with `BuildContended` when anyone holds it."""
    ctx, _, writer, scratch = acquisition
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

    acquire(ctx, writer, request(resource("a", "a")), seam=replace(seam, connect=probing), scratch=scratch)
    assert seen == [True]


def test_a_report_naming_an_observation_no_act_published_refuses_at_the_close(acquisition, monkeypatch):
    """T5-c: the close checks every PublishedObservation ref resolves."""
    ctx, _, writer, scratch = acquisition
    from beliefs.holdings import acquire as module

    real = module.look

    def forged(*args, **kwargs):
        result = real(*args, **kwargs)
        return replace(result, ref="holdings-observation:" + "0" * 64)

    monkeypatch.setattr(module, "look", forged)
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(AcquisitionRefused, match="no act published"):
        acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_the_close_rebuilds_the_writers_view_before_it_resolves_the_looks_observations(acquisition, monkeypatch):
    """The looks publish through the holdings seam, past the writer's cached index;
    without `_reconstruct` under the closing lock the close refuses its own observations."""
    ctx, _, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    rebuilt: list[int] = []
    real = type(writer)._reconstruct

    def counting(self):
        rebuilt.append(1)
        return real(self)

    monkeypatch.setattr(type(writer), "_reconstruct", counting)
    assert writer.read_view is not None  # cache the index
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert outcome.dataset is not None and rebuilt  # the close rebuilt at least once before resolving


def test_a_stop_mints_nothing_and_the_hold_enters_before_the_root_lock(acquisition):
    """`hold` is entered at the close only, before `writer._operation`, and exited after it."""
    ctx, _, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    events: list[str] = []
    lock = _operation_lock_for(ctx.observer_root)

    class Hold:
        def __enter__(self):
            events.append("hold-enter:" + ("held" if _held(lock) else "free"))
            return self

        def __exit__(self, *_exc):
            events.append("hold-exit:" + ("held" if _held(lock) else "free"))

    def _held(lock) -> bool:
        seen: list[bool] = []

        def probe() -> None:
            try:
                with lock.capture():
                    seen.append(False)
            except BuildContended:
                seen.append(True)

        thread = threading.Thread(target=probe)
        thread.start()
        thread.join(5)
        return seen == [True]

    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch, hold=Hold)
    assert outcome.dataset is not None
    assert events == ["hold-enter:free", "hold-exit:free"]
