"""Sealing an acquisition set as a tree dataset."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest
from authority import FULL
from profiles import BASE, pins_for
from test_holdings_acquire import chain, registrations_of
from test_holdings_boundary import _intents, context

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.dataset import DatasetDeclaration, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.errors import AcquisitionRefused, MalformedRecord
from beliefs.holdings.acquisition_log import (
    AcquisitionLog,
    Attempt,
    LogHeader,
    Recorded,
    RequestLine,
    render_acquisition_log,
)
from beliefs.holdings.adapter import DatasetAnswer, dataset_observations
from beliefs.holdings.boundary import write
from beliefs.holdings.receipt import derive_holdings
from beliefs.holdings.records import Absent, Found, HoldingsObservation, Incomplete, StoreLocator, StoreTreeLocator
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.holdings.seal import SealRequest, seal_acquisition
from beliefs.holdings.seam import ReadUnestablishedView
from beliefs.identity import v1
from beliefs.report import (
    UNFINISHED,
    AcquisitionSetEntry,
    DeclarationPinEntry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    SetSummary,
    completion,
)
from beliefs.root import durable_executor_factory, init_corpus_root, init_world_root, open_corpus, open_world
from beliefs.tree import Tree, TreeMember, make_tree, object_path, tree_digest
from beliefs.world import registry, rules
from beliefs.world.registry import WorldConfig

SET = "5" * 32
FETCHED_BY = "program/fetch-dryad.py"
WHEN = "2026-11-08T00:00:00Z"
LOCATOR = "url:https://example.org/dataset/1"
TREE_NAME = "files"
LOG_NAME = "acquisition-log.jsonl"
JOURNAL_NAME = "journal.jsonl"
MEMBERS = {"a.txt": b"alpha", "d/b.txt": b"beta", "d/c.txt": b"gamma"}
JOURNAL = b'{"journal":"the original fetch"}\n'


def digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def tree_of(contents: dict[str, bytes]) -> Tree:
    return make_tree(TreeMember(path, digest(data), len(data)) for path, data in contents.items())


def tree_location(store_id: str, contents: dict[str, bytes]) -> StoreTreeLocator:
    return StoreTreeLocator(store_id, tree_digest(tree_of(contents)).split(":", 1)[1])


def _fetched_line(seq: int, path: str, data: bytes, *, size: int | None = None) -> RequestLine:
    return RequestLine(
        seq=seq,
        url=f"https://example.org/{path}",
        parent=None,
        expected=None,
        attempts=(Attempt(WHEN, WHEN, "fetched", 200, (), None),),
        result="fetched",
        digest=digest(data),
        size=len(data) if size is None else size,
        member=path,
        recorded=None,
    )


def _failed_line(seq: int) -> RequestLine:
    return RequestLine(
        seq=seq,
        url="https://example.org/missing",
        parent=None,
        expected=None,
        attempts=(Attempt(WHEN, WHEN, "failed", 500, (), "status"),),
        result="failed",
        digest=None,
        size=None,
        member=None,
        recorded=None,
    )


def fetched_log(
    contents: dict[str, bytes],
    *,
    failed: bool = True,
    sizes: dict[str, int] | None = None,
    set_token: str = SET,
) -> bytes:
    """A fetched-origin log: one fetched line per member, then one failed request."""
    lines = [
        _fetched_line(seq, path, data, size=(sizes or {}).get(path))
        for seq, (path, data) in enumerate(contents.items(), start=1)
    ]
    if failed:
        lines.append(_failed_line(len(lines) + 1))
    header = LogHeader(
        set=set_token,
        origin="fetched",
        fetched_by=FETCHED_BY,
        plan={"requests": [line.url for line in lines]},
        source_journals=(),
    )
    return render_acquisition_log(AcquisitionLog(header, tuple(lines)))


def imported_log(contents: dict[str, bytes], journal: bytes) -> bytes:
    """An imported log over one source journal, each line naming the journal line it came from."""
    lines = tuple(
        RequestLine(
            seq=seq,
            url=f"https://example.org/{path}",
            parent=None,
            expected=None,
            attempts=(),
            result="fetched",
            digest=digest(data),
            size=len(data),
            member=path,
            recorded=Recorded(journal=0, line=seq, digest=digest(data)),
        )
        for seq, (path, data) in enumerate(contents.items(), start=1)
    )
    header = LogHeader(
        set=SET,
        origin="imported",
        fetched_by=FETCHED_BY,
        plan=None,
        source_journals=((JOURNAL_NAME, digest(journal)),),
    )
    return render_acquisition_log(AcquisitionLog(header, lines))


def rewrite_line(log: bytes, index: int, change) -> bytes:
    """`log` with its line `index` (0-based) decoded, changed and re-encoded canonically."""
    lines = log[:-1].split(b"\n")
    row = v1.decode(lines[index])
    change(row)
    lines[index] = v1.encode(row)
    return b"\n".join(lines) + b"\n"


def request_for(
    work: Path,
    contents: dict[str, bytes],
    log: bytes,
    *,
    origin: str = "fetched",
    fetched_by: str = FETCHED_BY,
    journals: dict[str, bytes] | None = None,
) -> SealRequest:
    """Lay the work area a program leaves: each member file, the log and any source journal."""
    work.mkdir(parents=True, exist_ok=True)
    members: dict[str, Path] = {}
    for path, data in contents.items():
        source = work / "members" / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(data)
        members[path] = source
    log_path = work / LOG_NAME
    log_path.write_bytes(log)
    laid: list[tuple[str, Path]] = []
    for name, data in (journals or {}).items():
        (work / "journals").mkdir(parents=True, exist_ok=True)
        (work / "journals" / name).write_bytes(data)
        laid.append((name, work / "journals" / name))
    return SealRequest(
        title="Dryad record 1",
        locator=LOCATOR,
        tree_name=TREE_NAME,
        members=members,
        log=log_path,
        origin=origin,
        fetched_by=fetched_by,
        source_journals=tuple(laid),
    )


@pytest.fixture()
def sealing(certified_work, tmp_path):
    ctx, store_id = context(certified_work)
    writer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return ctx, store_id, writer, tmp_path / "work"


def world_over(certified_work: Path, root: Path):
    config = WorldConfig(certified_work / "world", "f" * 32, (root,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(root, provenance=registry.Fresh())
    return world, rules.install_rule_binding(world, holdings_rule_bundle())


@dataclass(frozen=True)
class Reduction:
    active: list[dict[str, object]]
    blocked: list[dict[str, object]]
    standing: dict[str, tuple[HoldingsObservation, ...]]
    unsettled: frozenset[str]


def reduce(world, binding, writer: CorpusWriter) -> Reduction:
    """One holdings reduction, and the caller's `standing` and `unsettled` read from it."""
    seam = science_root._log_seam()
    active, blocked, _ = derive_holdings(
        world,
        frozenset({writer.corpus_id}),
        binding,
        chain_view=seam.inspect_registered,
        state_facts=seam.state_facts,
    )
    view = ReadView.opened_at(writer.root)
    standing: dict[str, tuple[HoldingsObservation, ...]] = {}
    heads = [*active, *(head for entry in blocked for head in cast(list[dict[str, object]], entry["heads"]))]
    for head in heads:
        location = cast(str, head["location"])
        record = stored.holdings_observation_value(view.get(f"holdings-observation:{head['head']}"))
        standing[location] = (*standing.get(location, ()), record)
    unsettled = frozenset(
        cast(str, entry["location"]) for entry in blocked if "unsettled" in cast(list[str], entry["reasons"])
    )
    return Reduction(active, blocked, standing, unsettled)


def observations(root: Path) -> list[HoldingsObservation]:
    return [
        stored.holdings_observation_value(node)
        for node in ReadView.opened_at(root).iter_stored()
        if node.kind == "holdings-observation"
    ]


def stored_kinds(root: Path) -> Counter[str]:
    return Counter(
        node.kind
        for node in ReadView.opened_at(root).iter_stored()
        if node.kind in ("dataset", "act-report", "holdings-observation")
    )


def store_files(store_root: Path) -> list[tuple[str, bytes]]:
    return sorted(
        (path.relative_to(store_root).as_posix(), path.read_bytes()) for path in store_root.rglob("*") if path.is_file()
    )


def kinds_of_intents(root: Path) -> list[str | None]:
    return [json.loads(entry.payload).get("kind") for entry in _intents(root)]


def declaration_of(contents: dict[str, bytes]) -> DatasetDeclaration:
    return DatasetDeclaration((ResourceDeclaration(TREE_NAME, tree_digest(tree_of(contents))),))


def test_seal_holds_a_fetched_set_with_four_records(sealing, certified_work):
    ctx, store_id, writer, work = sealing
    log = fetched_log(MEMBERS)
    location = tree_location(store_id, MEMBERS)
    log_location = StoreLocator(store_id, f"{location.tree}/{SET}/{LOG_NAME}")

    outcome = seal_acquisition(ctx, writer, request_for(work, MEMBERS, log))

    address = dataset_address(declaration_of(MEMBERS))
    assert address is not None and outcome.address == address
    assert outcome.dataset is not None and outcome.dataset.id == address
    assert outcome.dataset.facets["empirical-observation"] == {
        "locator": LOCATOR,
        "attested_by": ctx.actor,
        "retrieval": outcome.report_ref,
    }
    assert stored_kinds(ctx.observer_root) == {"dataset": 1, "act-report": 1, "holdings-observation": 2}
    assert [type(entry) for entry in outcome.entries] == [
        ManagedMutationEntry,
        ManagedMutationEntry,
        AcquisitionSetEntry,
        DeclarationPinEntry,
    ]
    assert [entry.subject for entry in outcome.entries[:3]] == [
        log_location.canonical(),
        location.canonical(),
        location.canonical(),
    ]
    assert outcome.entries[2].outcome == SetSummary(
        origin="fetched",
        fetched_by=FETCHED_BY,
        requests=4,
        fetched=3,
        failed=1,
        abandoned=0,
        traversal_complete=True,
        log=digest(log),
        tree=tree_digest(tree_of(MEMBERS)),
    )
    assert outcome.entries[3] == DeclarationPinEntry(address, PinnedDeclaration(address))
    # The sealing tool is the instrument of every record; the fetching program is named only in the set entry.
    assert outcome.report.instrument == ctx.instrument != FETCHED_BY
    assert {value.instrument for value in observations(ctx.observer_root)} == {ctx.instrument}
    assert (ctx.store_root / log_location.relative_path).read_bytes() == log
    assert kinds_of_intents(ctx.observer_root) == ["acquisition", "write", "tree-write"]

    world, binding = world_over(certified_work, ctx.observer_root)
    reduced = reduce(world, binding, writer)
    answer = dataset_observations(declaration_of(MEMBERS), reduced.active, reduced.blocked)
    assert isinstance(answer, DatasetAnswer)
    assert isinstance(admission_state(declaration_of(MEMBERS), answer.observations), Held)


def test_seal_import_holds_its_source_journals(sealing):
    ctx, store_id, writer, work = sealing
    log = imported_log(MEMBERS, JOURNAL)
    location = tree_location(store_id, MEMBERS)
    journal_location = StoreLocator(store_id, f"{location.tree}/{SET}/{JOURNAL_NAME}")

    outcome = seal_acquisition(
        ctx, writer, request_for(work, MEMBERS, log, origin="imported", journals={JOURNAL_NAME: JOURNAL})
    )

    assert outcome.dataset is not None
    assert stored_kinds(ctx.observer_root) == {"dataset": 1, "act-report": 1, "holdings-observation": 3}
    assert [type(entry) for entry in outcome.entries] == [
        ManagedMutationEntry,
        ManagedMutationEntry,
        ManagedMutationEntry,
        AcquisitionSetEntry,
        DeclarationPinEntry,
    ]
    assert outcome.entries[1].subject == journal_location.canonical()
    assert (ctx.store_root / journal_location.relative_path).read_bytes() == JOURNAL
    summary = outcome.entries[3].outcome
    assert isinstance(summary, SetSummary)
    assert summary.origin == "imported" and summary.fetched_by == FETCHED_BY


def _spoiled(spoil: str, ctx, store_id: str, writer: CorpusWriter, work: Path, certified_work: Path):
    """The request, writer and keyword arguments of one refused seal."""
    kwargs: dict[str, Any] = {}
    log = fetched_log(MEMBERS)
    contents = dict(MEMBERS)
    request_kwargs: dict[str, Any] = {}
    if spoil == "log-members-mismatch":
        contents.pop("d/c.txt")
    elif spoil == "member-hash-mismatch":
        contents["d/c.txt"] = b"other bytes"
    elif spoil == "member-size-mismatch":
        log = fetched_log(MEMBERS, sizes={"d/c.txt": len(MEMBERS["d/c.txt"]) + 1})
    elif spoil == "origin-mismatch":
        request_kwargs["origin"] = "imported"
    elif spoil == "fetched-by-mismatch":
        request_kwargs["fetched_by"] = "program/another.py"
    elif spoil == "failure-outside-the-set":
        log = rewrite_line(log, 4, lambda row: row["attempts"][0].update(failure="bogus"))
    elif spoil == "recorded-digest-mismatch":
        log = rewrite_line(
            imported_log(MEMBERS, JOURNAL), 1, lambda row: row["recorded"].update(digest=digest(b"another"))
        )
        request_kwargs = {"origin": "imported", "journals": {JOURNAL_NAME: JOURNAL}}
    elif spoil == "journal-digest-mismatch":
        log = imported_log(MEMBERS, JOURNAL)
        request_kwargs = {"origin": "imported", "journals": {JOURNAL_NAME: b"another journal\n"}}
    elif spoil == "non-canonical-log":
        log = rewrite_line(log, 1, lambda row: row["attempts"][0].update(headers={}))
    elif spoil == "empty-tree":
        log = fetched_log({}, failed=True)
        contents = {}
    elif spoil == "work-area-under-store":
        work = ctx.store_root / "work"
    elif spoil == "wrong-root":
        other = certified_work / "other"
        init_corpus_root(other, authority=FULL)
        writer = open_corpus(other, authority=FULL, profile=BASE)
    elif spoil == "no-port":
        writer = CorpusWriter(ctx.observer_root, durable_executor_factory(), authority=FULL, profile=BASE)
    elif spoil == "misplaced-standing":
        # a head at another location, keyed as the log's: the log write would refuse it after the intent
        stray = write(ctx, StoreLocator(store_id, "elsewhere.bin"), b"elsewhere").record
        log_location = StoreLocator(store_id, f"{tree_location(store_id, MEMBERS).tree}/{SET}/{LOG_NAME}")
        kwargs["standing"] = {log_location.canonical(): (stray,)}
    else:
        raise AssertionError(spoil)
    return request_for(work, contents, log, **request_kwargs), writer, kwargs


SPOILS = {
    "log-members-mismatch": "not exactly the paths of the log's fetched lines",
    "member-hash-mismatch": "d/c.txt: the work area's file is not the log's digest and size",
    "member-size-mismatch": "d/c.txt: the work area's file is not the log's digest and size",
    "origin-mismatch": "names origin 'fetched'",
    "fetched-by-mismatch": "not the request's 'fetched' and 'program/another.py'",
    "failure-outside-the-set": "failure 'bogus' is outside",
    "recorded-digest-mismatch": "the recorded digest differs from the line's digest",
    "journal-digest-mismatch": "journal.jsonl: the journal's bytes are not the digest",
    "non-canonical-log": "not its own canonical rendering",
    "empty-tree": "a tree holds a non-empty tuple of members",
    "work-area-under-store": "outside the corpus and store roots",
    "wrong-root": "not the act context's observer root",
    "no-port": "no operation port",
    "misplaced-standing": "standing holds only HoldingsObservation values at that location",
}


@pytest.mark.parametrize("spoil", sorted(SPOILS))
def test_seal_refuses_before_the_intent(sealing, certified_work, spoil):
    ctx, store_id, writer, work = sealing
    request, writer, kwargs = _spoiled(spoil, ctx, store_id, writer, work, certified_work)
    before_chain = chain(ctx.observer_root)
    before_store = store_files(ctx.store_root)
    before_kinds = stored_kinds(ctx.observer_root)

    with pytest.raises(AcquisitionRefused, match=re.escape(SPOILS[spoil])):
        seal_acquisition(ctx, writer, request, **kwargs)

    assert chain(ctx.observer_root) == before_chain
    assert store_files(ctx.store_root) == before_store
    assert stored_kinds(ctx.observer_root) == before_kinds


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"locator": "dataset-1"}, "a seal's locator is `<scheme>:<rest>`"),
        ({"locator": "ftp:example.org/1"}, "a seal's locator is `<scheme>:<rest>`"),
        ({"domain_facets": {"unnamespaced": {"k": 1}}}, "namespaced"),
        ({"origin": "copied"}, "origin 'copied' is outside"),
        ({"source_journals": (("j", Path("a")), ("j", Path("b")))}, "source journal names are unique"),
        ({"source_journals": ((LOG_NAME, Path("a")),)}, "source journal names are unique"),
        ({"members": {"a.txt": "a.txt"}}, "maps each tree path to a file Path"),
    ],
)
def test_the_request_refuses_a_malformed_value(change, message):
    fields = {
        "title": "t",
        "locator": LOCATOR,
        "tree_name": TREE_NAME,
        "members": {"a.txt": Path("a.txt")},
        "log": Path(LOG_NAME),
        "origin": "fetched",
        "fetched_by": FETCHED_BY,
    }
    with pytest.raises(MalformedRecord, match=re.escape(message)):
        SealRequest(**{**fields, **change})


def test_sealing_an_already_held_tree_mints_no_second_dataset(sealing, certified_work):
    ctx, _, writer, work = sealing
    request = request_for(work, MEMBERS, fetched_log(MEMBERS))
    first = seal_acquisition(ctx, writer, request)
    world, binding = world_over(certified_work, ctx.observer_root)
    reduced = reduce(world, binding, writer)

    second = seal_acquisition(ctx, writer, request, standing=reduced.standing, unsettled=reduced.unsettled)

    assert first.dataset is not None
    assert second.dataset is None and second.address == first.address
    assert [type(entry) for entry in second.entries] == [
        ManagedMutationEntry,
        ManagedMutationEntry,
        AcquisitionSetEntry,
    ]
    assert stored_kinds(ctx.observer_root) == {"dataset": 1, "act-report": 2, "holdings-observation": 4}
    after = reduce(world, binding, writer)
    assert after.blocked == []
    assert sorted(Counter(head["location"] for head in after.active).values()) == [1, 1]  # one head per location


def test_two_sets_of_one_tree_keep_their_own_logs_beside_one_dataset(sealing, certified_work, tmp_path):
    """Two acquisitions of identical bytes: one dataset, two act reports, each binding its own log."""
    ctx, store_id, writer, work = sealing
    other_set = "6" * 32
    location = tree_location(store_id, MEMBERS)
    logs = {SET: fetched_log(MEMBERS), other_set: fetched_log(MEMBERS, failed=False, set_token=other_set)}
    first = seal_acquisition(ctx, writer, request_for(work, MEMBERS, logs[SET]))
    world, binding = world_over(certified_work, ctx.observer_root)
    reduced = reduce(world, binding, writer)

    second = seal_acquisition(
        ctx,
        writer,
        request_for(tmp_path / "other-work", MEMBERS, logs[other_set]),
        standing=reduced.standing,
        unsettled=reduced.unsettled,
    )

    assert first.dataset is not None and second.dataset is None and second.address == first.address
    assert stored_kinds(ctx.observer_root)["dataset"] == 1
    after = reduce(world, binding, writer)
    assert after.blocked == []
    active = {cast(str, head["location"]): head["outcome"] for head in after.active}
    for set_token, outcome in ((SET, first), (other_set, second)):
        mutation, summary = outcome.entries[0], outcome.entries[2].outcome
        assert isinstance(summary, SetSummary) and summary.log == digest(logs[set_token])  # its own log's digest
        relative_path = mutation.subject.split(":", 2)[2]  # the log location this set's report names
        assert (ctx.store_root / relative_path).read_bytes() == logs[set_token]  # still held, never replaced
        assert active[mutation.subject] == {"finding": "found", "digest": digest(logs[set_token])}
        assert relative_path == f"{location.tree}/{set_token}/{LOG_NAME}"


def _killed_after_two_objects(ctx):
    created: list[str] = []
    original = ctx.seam.store_create

    def interrupted(root, path, content):
        if len(created) == 2:
            raise RuntimeError("kill")
        created.append(path)
        return original(root, path, content)

    return replace(ctx, seam=replace(ctx.seam, store_create=interrupted)), created


def _interrupted_seal(ctx, writer, request):
    killed, created = _killed_after_two_objects(ctx)
    with pytest.raises(RuntimeError, match="kill"):
        seal_acquisition(killed, writer, request)
    assert len(created) == 2


def test_an_interrupted_seal_recovers_held_and_not_contested(sealing, certified_work):
    ctx, store_id, writer, work = sealing
    location = tree_location(store_id, MEMBERS)
    request = request_for(work, MEMBERS, fetched_log(MEMBERS))
    _interrupted_seal(ctx, writer, request)
    assert stored_kinds(ctx.observer_root) == {"holdings-observation": 1}  # the log's, no tree's, no report
    world, binding = world_over(certified_work, ctx.observer_root)

    reduced = reduce(world, binding, writer)
    assert reduced.blocked == [{"location": location.canonical(), "reasons": ["unsettled"], "heads": []}]
    assert reduced.unsettled == {location.canonical()}

    outcome = seal_acquisition(ctx, writer, request, standing=reduced.standing, unsettled=reduced.unsettled)

    assert outcome.dataset is not None
    assert kinds_of_intents(ctx.observer_root) == [
        "acquisition",
        "write",
        "tree-write",
        "acquisition",
        "re-check",
        "write",
        "tree-write",
    ]
    at_tree = {value.identity(): value for value in observations(ctx.observer_root) if value.location == location}
    (absent,) = [value for value in at_tree.values() if isinstance(value.outcome, Absent)]
    (found,) = [value for value in at_tree.values() if isinstance(value.outcome, Found)]
    assert absent.outcome == Absent(Incomplete(1, 0))  # the tree file was never written
    assert found.supersedes == (absent.identity(),)
    after = reduce(world, binding, writer)
    assert after.blocked == []
    heads = [head for head in after.active if head["location"] == location.canonical()]
    assert [head["outcome"] for head in heads] == [{"finding": "found", "digest": location.digest()}]
    assert len([head for head in after.active if cast(str, head["location"]).endswith(LOG_NAME)]) == 1
    answer = dataset_observations(declaration_of(MEMBERS), after.active, after.blocked)
    assert isinstance(answer, DatasetAnswer)
    assert isinstance(admission_state(declaration_of(MEMBERS), answer.observations), Held)


def test_an_inconclusive_repair_recheck_refuses_the_seal(sealing, certified_work):
    ctx, store_id, writer, work = sealing
    location = tree_location(store_id, MEMBERS)
    request = request_for(work, MEMBERS, fetched_log(MEMBERS))
    _interrupted_seal(ctx, writer, request)
    world, binding = world_over(certified_work, ctx.observer_root)
    reduced = reduce(world, binding, writer)
    tree_file = object_path(location.digest())
    inner = ctx.seam.read_path

    def unreadable(root, path):
        if path == tree_file:
            return ReadUnestablishedView("io-failure", "device returned EIO")
        return inner(root, path)

    unreadable_ctx = replace(ctx, seam=replace(ctx.seam, read_path=unreadable))
    with pytest.raises(AcquisitionRefused):
        seal_acquisition(unreadable_ctx, writer, request, standing=reduced.standing, unsettled=reduced.unsettled)

    assert stored_kinds(ctx.observer_root) == {"holdings-observation": 1}  # no dataset, no report, no new observation
    assert kinds_of_intents(ctx.observer_root)[3:] == ["acquisition", "re-check"]  # nothing written after the repair
    entries = chain(ctx.observer_root)
    for intent in [
        entry for entry in _intents(ctx.observer_root) if json.loads(entry.payload)["kind"] == "acquisition"
    ]:
        token = json.loads(intent.payload)["event_token"]
        registrations = registrations_of(entries, intent.digest, "act-report:" + "0" * 64)
        assert completion(OperationIntent("acquisition", token, ctx.actor), registrations, {}) == UNFINISHED
