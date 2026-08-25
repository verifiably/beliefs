"""The holdings acts boundary publishes only established store evidence."""

from __future__ import annotations

import inspect
import json
import shutil
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from nodes.core.errors import ExecutionError

from science import root as science_root
from science.errors import MalformedRecord, StoreIdMismatch
from science.holdings.boundary import (
    ActContext,
    InconclusiveAttempt,
    PublishedObservation,
    delete,
    intent_payload,
    move,
    recheck,
    write,
)
from science.holdings.records import Absent, Found, StoreLocator
from science.holdings.seam import FileStateView, StoreOutcomeView
from science.root import (
    LifecycleState,
    holdings_seam,
    init_corpus_root,
    init_store_root,
    read_lifecycle_state,
    replicate_root,
)
from science.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView


def context(certified_work):
    observer_root = certified_work / "observer"
    store_root = certified_work / "store"
    init_corpus_root(observer_root)
    store_id = init_store_root(store_root)
    return ActContext(observer_root, store_root, "observer", "instrument", "actor", holdings_seam()), store_id


def test_recheck_publishes_found_with_the_hash_the_engine_observed(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "held.bin", b"held bytes")

    result = recheck(ctx, StoreLocator(store_id, "held.bin"))

    assert isinstance(result, PublishedObservation)
    assert result.record.outcome == Found(f"sha256:{sha256(b'held bytes').hexdigest()}")


def test_recheck_publishes_absent_for_a_missing_path(certified_work):
    ctx, store_id = context(certified_work)

    result = recheck(ctx, StoreLocator(store_id, "missing.bin"))

    assert isinstance(result, PublishedObservation)
    assert result.record.outcome == Absent()


def test_recheck_appends_its_intent_before_reading(certified_work):
    ctx, store_id = context(certified_work)
    appended = False
    original_append = ctx.seam.append_intent
    original_read = ctx.seam.read_path

    def append(root, payload):
        nonlocal appended
        appended = True
        return original_append(root, payload)

    def read(root, path):
        assert appended
        return original_read(root, path)

    ctx = replace(ctx, seam=replace(ctx.seam, append_intent=append, read_path=read))

    recheck(ctx, StoreLocator(store_id, "missing.bin"))


def test_intent_payload_is_the_exact_canonical_json_shape():
    payload = intent_payload(location=StoreLocator("a" * 32, "held.bin"), act_kind="re-check", event_token="token", actor="actor")

    assert payload == b'{"actor":"actor","domain":"science.holdings-intent.v1","event_token":"token","kind":"re-check","location":{"relative_path":"held.bin","store_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","type":"store"}}'
    assert set(json.loads(payload)) == {"actor", "domain", "event_token", "kind", "location"}
    assert set(json.loads(payload)["location"]) == {"relative_path", "store_id", "type"}


@pytest.mark.parametrize("actor, token, kind", [("", "token", "re-check"), ("actor", "", "re-check"), ("actor", "token", "bad")])
def test_intent_payload_refuses_malformed_public_values(actor, token, kind):
    with pytest.raises(MalformedRecord):
        intent_payload(location=StoreLocator("a" * 32, "held.bin"), act_kind=kind, event_token=token, actor=actor)


def test_recheck_on_a_metadata_less_store_reports_byte_locator_untested_and_mints_nothing(certified_work):
    ctx, store_id = context(certified_work)
    cold = certified_work / "cold"
    shutil.copytree(ctx.store_root, cold, symlinks=True)
    ctx = replace(ctx, store_root=cold)
    standing = recheck(replace(ctx, store_root=certified_work / "store"), StoreLocator(store_id, "missing.bin"))
    assert isinstance(standing, PublishedObservation)
    standing_identity = standing.record.identity()
    assert read_lifecycle_state(cold) is LifecycleState.METADATA_LESS

    result = recheck(ctx, StoreLocator(store_id, "missing.bin"), standing=(standing.record,))

    assert isinstance(result, InconclusiveAttempt)
    assert result.report == "byte-locator-untested"
    assert result.reason == "lifecycle-state"
    assert result.detail == ""
    assert standing.record.identity() == standing_identity
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 2
    assert len([entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]) == 1


def test_recheck_of_an_unserviceable_root_mints_nothing_never_absent(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "held.bin", b"payload")
    replica = certified_work / "replica"
    replicate_root(ctx.store_root, replica)
    (replica / "held.bin").unlink()
    ctx = replace(ctx, store_root=replica)
    assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    result = recheck(ctx, StoreLocator(store_id, "held.bin"))

    assert isinstance(result, InconclusiveAttempt)
    assert result.report == "byte-locator-untested"
    assert result.reason == "lifecycle-state"
    assert result.detail == ""
    assert not (ctx.observer_root / "holdings-observation").exists()
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]


def test_a_final_directory_is_established_neither(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "directory/payload.bin", b"held bytes")

    result = recheck(ctx, StoreLocator(store_id, "directory"))

    assert isinstance(result, InconclusiveAttempt)
    assert result.report == "retrieval-failed"
    assert result.reason == "established-neither"
    assert result.detail == "directory"


def test_store_id_mismatch_refuses_after_the_intent(certified_work):
    ctx, store_id = context(certified_work)
    other = certified_work / "other"
    init_store_root(other)
    ctx = replace(ctx, store_root=other)

    with pytest.raises(StoreIdMismatch):
        recheck(ctx, StoreLocator(store_id, "missing.bin"))

    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]


def test_a_seam_raise_aborts_the_act_without_a_report(certified_work):
    ctx, store_id = context(certified_work)

    def raise_read(_root, _path):
        raise RuntimeError("engine alarm")

    ctx = replace(ctx, seam=replace(ctx.seam, read_path=raise_read))
    with pytest.raises(RuntimeError, match="engine alarm"):
        recheck(ctx, StoreLocator(store_id, "missing.bin"))
    assert not (ctx.observer_root / "holdings-observation").exists()
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]


def test_publication_failure_after_an_established_outcome_raises(certified_work):
    ctx, store_id = context(certified_work)

    def raise_publish(_root, _plan, _fulfills):
        raise ExecutionError("cannot publish", index=None, applied=0)

    ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=raise_publish))
    with pytest.raises(ExecutionError, match="cannot publish"):
        recheck(ctx, StoreLocator(store_id, "missing.bin"))
    assert not (ctx.observer_root / "holdings-observation").exists()
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]


def test_the_published_transaction_registers_the_stored_path(certified_work):
    ctx, store_id = context(certified_work)

    result = recheck(ctx, StoreLocator(store_id, "missing.bin"))

    assert isinstance(result, PublishedObservation)
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    registration = next(entry for entry in chain.entries if isinstance(entry, RegisteredEntryView))
    assert f"holdings-observation/{result.record.identity()}.md" in dict(registration.final)


def test_supersedes_carries_exactly_the_supplied_standing_heads(certified_work):
    ctx, store_id = context(certified_work)
    location = StoreLocator(store_id, "missing.bin")
    first = recheck(ctx, location)
    assert isinstance(first, PublishedObservation)

    second = recheck(ctx, location, standing=(first.record,))

    assert isinstance(second, PublishedObservation)
    assert second.record.supersedes == (first.record.identity(),)


def test_no_caller_supplied_fulfills_path_exists():
    for act in (recheck, write, delete, move):
        assert "fulfills" not in inspect.signature(act).parameters


def test_write_records_the_engine_final_row_not_the_payload_digest(certified_work):
    ctx, store_id = context(certified_work)
    doctored = "sha256:" + "d" * 64
    original_write = ctx.seam.store_write

    def write_with_doctored_evidence(root, path, content):
        outcome = original_write(root, path, content)
        return StoreOutcomeView(outcome.txid, ((path, FileStateView(doctored)),))

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=write_with_doctored_evidence))
    result = write(ctx, StoreLocator(store_id, "held.bin"), b"payload")

    assert result.record.outcome == Found(doctored)


def test_delete_records_absent_from_the_final_row_never_the_return(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "held.bin", b"payload")

    result = delete(ctx, StoreLocator(store_id, "held.bin"))

    assert result.record.outcome == Absent()


def test_write_validates_expected_before_its_intent_or_mutation(certified_work):
    ctx, store_id = context(certified_work)

    with pytest.raises(MalformedRecord, match="algorithm"):
        write(ctx, StoreLocator(store_id, "held.bin"), b"payload", expected="sha512:" + "a" * 40)

    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert not [entry for entry in chain.entries if isinstance(entry, IntentEntryView)]
    assert not (ctx.store_root / "held.bin").exists()


def test_move_publishes_two_observations_fulfilling_two_intents(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "source.bin", b"payload")

    source, destination = move(ctx, StoreLocator(store_id, "source.bin"), StoreLocator(store_id, "destination.bin"))

    assert source.record.outcome == Absent()
    assert isinstance(destination.record.outcome, Found)
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    intents = [entry.digest for entry in chain.entries if isinstance(entry, IntentEntryView)]
    registrations = [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert len(intents) == len(registrations) == 2
    assert [entry.fulfills for entry in registrations] == intents


def test_a_kill_between_intent_and_mutation_leaves_the_intent_unmatched(certified_work):
    ctx, store_id = context(certified_work)

    def kill_before_write(_root, _path, _content):
        raise RuntimeError("kill")

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=kill_before_write))
    with pytest.raises(RuntimeError, match="kill"):
        write(ctx, StoreLocator(store_id, "held.bin"), b"payload")
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert not (ctx.store_root / "held.bin").exists()
    assert not (ctx.observer_root / "holdings-observation").exists()


def test_a_move_killed_between_the_two_appends(certified_work):
    ctx, store_id = context(certified_work)
    original_append = ctx.seam.append_intent
    calls = 0

    def kill_second_append(root, payload):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("kill")
        return original_append(root, payload)

    ctx = replace(ctx, seam=replace(ctx.seam, append_intent=kill_second_append))
    with pytest.raises(RuntimeError, match="kill"):
        move(ctx, StoreLocator(store_id, "source.bin"), StoreLocator(store_id, "destination.bin"))
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 1
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert not (ctx.store_root / "source.bin").exists()
    assert not (ctx.store_root / "destination.bin").exists()


def test_a_move_killed_after_both_appends_before_the_mutation(certified_work):
    ctx, store_id = context(certified_work)

    def kill_before_move(_root, _source, _destination):
        raise RuntimeError("kill")

    ctx = replace(ctx, seam=replace(ctx.seam, store_move=kill_before_move))
    with pytest.raises(RuntimeError, match="kill"):
        move(ctx, StoreLocator(store_id, "source.bin"), StoreLocator(store_id, "destination.bin"))
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 2
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert not (ctx.store_root / "source.bin").exists()
    assert not (ctx.store_root / "destination.bin").exists()


def test_a_move_killed_between_the_publications(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "source.bin", b"payload")
    original_publish = ctx.seam.publish_fulfilling
    calls = 0

    def kill_second_publish(root, plan, fulfills):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("kill")
        return original_publish(root, plan, fulfills)

    ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=kill_second_publish))
    with pytest.raises(RuntimeError, match="kill"):
        move(ctx, StoreLocator(store_id, "source.bin"), StoreLocator(store_id, "destination.bin"))
    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    registrations = [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert len(registrations) == 1
    intents = [entry.digest for entry in chain.entries if isinstance(entry, IntentEntryView)]
    assert registrations[0].fulfills == intents[0]
    assert registrations[0].fulfills != intents[1]
    assert not (ctx.store_root / "source.bin").exists()
    assert (ctx.store_root / "destination.bin").read_bytes() == b"payload"


def test_a_mixed_store_move_refuses_before_mutating(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "source.bin", b"payload")

    with pytest.raises(StoreIdMismatch):
        move(ctx, StoreLocator(store_id, "source.bin"), StoreLocator("b" * 32, "destination.bin"))

    chain = science_root._log_seam().inspect_registered(ctx.observer_root)
    assert isinstance(chain, WellFormedView)
    assert len([entry for entry in chain.entries if isinstance(entry, IntentEntryView)]) == 2
    assert not [entry for entry in chain.entries if isinstance(entry, RegisteredEntryView)]
    assert (ctx.store_root / "source.bin").read_bytes() == b"payload"
    assert not (ctx.store_root / "destination.bin").exists()
    assert not (ctx.observer_root / "holdings-observation").exists()


def test_boundary_never_hashes_payloads_it_did_not_observe():
    assert "sha256(" not in (Path(__file__).parents[1] / "src/science/holdings/boundary.py").read_text()
