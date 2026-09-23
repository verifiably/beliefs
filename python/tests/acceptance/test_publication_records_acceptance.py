"""Conformance cut 39 — publication records (publication-records design §11.2).
Thirteen declaration units over real roots on the certified volume.

Each test is one unit of the cut's §3 table; the cut's §5 arms sabotage the
source each one reads, and §6's second reader checks the obligations the
docstrings name. Tests may import `atoms` (W17-p-f patches the engine's
create-file effect, as Task 0's probe does); only source modules may not."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from atoms.coordinator.effects import create_file  # W17-p-f's rollback, as Task 0 pinned it
from authority import FULL
from coordination_fixtures import content_for, coordination_profile, raw_add
from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_from_bytes, node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import ReplaceOp
from profiles import pins_for
from test_belief import scenario as belief_scenario
from test_n2_cut7 import shipped_bindings

from beliefs import stored
from beliefs.belief import Belief, evaluate
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationRefused, coordination_revision, standing_at
from beliefs.corpus import CoordinationResolver
from beliefs.errors import (
    CoordinationKindUnsupported,
    ImportRefused,
    KindNotMintedHere,
    MalformedRecord,
    PublicationRefused,
    ValidationRefused,
)
from beliefs.intents.publish import Destination, PublishIntent, decode_publish_intent
from beliefs.intents.reduce import record_paths_of, reduce_chain
from beliefs.publication import BINDING_KIND, binding_address, binding_record, binding_uid, marker_record
from beliefs.publication_doors import (
    BindingOutcome,
    OpenedPublication,
    _bind_publication,
    _open_publication,
    marker_tips_at,
)
from beliefs.report import (
    CLOSED,
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    Registration,
    completion,
)
from beliefs.root import (
    init_corpus_root,
    init_world_root,
    log_seam,
    metadata_root_for,
    moment_seam,
    open_corpus,
    open_world,
)
from beliefs.world import derive, epoch, load_manifest
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView
from beliefs.world.registry import Fresh, WorldConfig

LOCAL = Destination.local("/srv/published/mm30")
REMOTE = Destination.remote("https://example.org/published/mm30")
CORPUS_ID = "1" * 32  # the binding's bound corpus id: a stand-in, as the marker uid is
ARTIFACT = "2" * 64
_counter = count()


class Clock:
    """Advances one second on every read (Y2-a's sabotage is a clock read in the door)."""

    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-22T00:00:{self.n:02d}Z"


@contextmanager
def mounted(work_directory, base_contract, monkeypatch, ids: tuple[str, ...]) -> Iterator[SimpleNamespace]:
    """v2-mounted roots `-a`, `-b`, `-c`, … in path order, whose manifests carry
    `ids` in that order (`adopt_manifest` mints the corpus id with
    `secrets.token_hex(16)`, fixed here as `test_w12…` fixes minted ids)."""
    profile = coordination_profile(base_contract, version=2)
    stem = f"publication-{os.getpid()}-{next(_counter)}"
    # Resolved: the engine opens roots with no symlink in the path (ELOOP otherwise).
    roots = tuple((work_directory / f"{stem}-{letter}").resolve() for letter in "abcdefgh"[: len(ids)])
    try:
        for root, corpus_id in zip(roots, ids, strict=True):
            init_corpus_root(root, authority=FULL)
            monkeypatch.setattr("beliefs.corpus.secrets", SimpleNamespace(token_hex=lambda _, value=corpus_id: value))
            open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
            monkeypatch.undo()
        assert [load_manifest(root).corpus_id for root in roots] == list(ids)
        resolver = CoordinationResolver(dict.fromkeys(roots, profile))
        writers = tuple(
            open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=profile) for root in roots
        )
        project = writers[0].mint_coordination("project", content=content_for("project"))
        yield SimpleNamespace(
            roots=roots,
            resolver=resolver,
            writers=writers,
            profile=profile,
            view=coordination_revision(project).address,
        )
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


@pytest.fixture()
def pair(work_directory, base_contract, monkeypatch) -> Iterator[SimpleNamespace]:
    """Two roots whose path order (-a, -b) is the reverse of their corpus-id order."""
    with mounted(work_directory, base_contract, monkeypatch, ("f" * 32, "0" * 32)) as roots:
        yield roots


def open_at(pair, side: int = 0, *, destination=LOCAL, resolver=None, clock=None, port=None) -> OpenedPublication:
    """Step 0 on one side."""
    return _open_publication(
        pair.writers[side],
        resolver or pair.resolver,
        view=pair.view,
        destination=destination,
        clock=clock or Clock(),
        seam=moment_seam(),
        port=port,
    )


def bind(
    pair, opened: OpenedPublication, side: int = 0, *, remotely_revealed=False, resolver=None, clock=None, port=None
) -> BindingOutcome:
    """Step 8 on one side, binding the stand-in marker the intent's own token names."""
    return _bind_publication(
        pair.writers[side],
        resolver or pair.resolver,
        opened,
        corpus_id=CORPUS_ID,
        marker=opened.intent.event_token,
        artifact=ARTIFACT,
        remotely_revealed=remotely_revealed,
        clock=clock or Clock(),
        seam=moment_seam(),
        port=port,
    )


def publish(pair, side: int = 0, *, destination=LOCAL, remotely_revealed=False, resolver=None, clock=None, port=None):
    """Steps 0 and 8 back to back: the slice's whole source-root write."""
    clock = clock or Clock()
    opened = open_at(pair, side, destination=destination, resolver=resolver, clock=clock, port=port)
    outcome = bind(pair, opened, side, remotely_revealed=remotely_revealed, resolver=resolver, clock=clock, port=port)
    return opened, outcome


def bound(outcome: BindingOutcome) -> Node:
    """The binding revision a bound outcome committed."""
    assert type(outcome.report.entries[0].outcome) is BindingBound and outcome.binding is not None
    return outcome.binding


def tips(pair, destination=LOCAL):
    return pair.resolver.resolve(binding_address(pair.view, destination))


def _chain(root: Path):
    view = log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return view.entries


def _payload_at(root: Path, digest: str) -> bytes:
    """The intent payload the chain holds at `digest`: what the door appended, read back."""
    (entry,) = [e for e in _chain(root) if type(e) is IntentEntryView and e.digest == digest]
    return entry.payload


def _intent_digest(root: Path, outcome: BindingOutcome) -> str:
    """The digest of the publish intent whose token the outcome's report carries."""
    token = outcome.report.event_token
    found = []
    for entry in _chain(root):
        if type(entry) is not IntentEntryView:
            continue
        try:
            decoded = decode_publish_intent(entry.payload)
        except MalformedRecord:
            continue  # another shape's intent
        if decoded.event_token == token:
            found.append(entry.digest)
    (digest,) = found
    return digest


def _intent_like(root: Path, outcome: BindingOutcome) -> PublishIntent:
    """The intent the outcome closed, with another token: a binding revision at the
    same address, superseding the same tips, that no registration created."""
    return replace(decode_publish_intent(_payload_at(root, _intent_digest(root, outcome))), event_token="7" * 32)


def _reduced(root: Path):
    """The audit's qualification of the root's chain: `{digest: status}` and its findings."""
    seam = log_seam()
    entries = _chain(root)
    records: dict[str, bytes] = {}
    for entry in entries:
        if type(entry) is RegisteredEntryView:
            for path in record_paths_of(entry, seam.state_facts):
                if (root / path).is_file():
                    records[path] = (root / path).read_bytes()
    reduced = reduce_chain(entries, records, state_facts=seam.state_facts)
    return {row.digest: row.status for row in reduced.rows}, reduced.findings


def _closed_durably(writer, opened: OpenedPublication, outcome: BindingOutcome) -> None:
    """Report alone, closed: the one committed fulfilment of the intent creates
    exactly the refusal report's file, whose bytes are the report's; the audit
    reads the intent `matched`; `completion` reads it closed."""
    root = Path(writer.root).resolve()
    entries = _chain(root)
    committed = {e.registration for e in entries if type(e) is SettledEntryView and e.committed}
    fulfilling = [
        e for e in entries if type(e) is RegisteredEntryView and e.fulfills == opened.digest and e.digest in committed
    ]
    report_node = stored.act_report_node(outcome.report)
    path = writer._relative_path(report_node)
    (registration,) = fulfilling
    assert [p for p, post in registration.final if moment_seam().is_file(post)] == [path]
    on_disk = node_from_bytes((root / path).read_bytes())
    assert on_disk.id == report_node.id and stored.act_report_facet(on_disk) == stored.act_report_facet(report_node)
    rows, _ = _reduced(root)
    assert rows[opened.digest] == "matched"
    held = {report_node.id: outcome.report}
    assert completion(opened.intent, (Registration(opened.intent.event_token, report_node.id),), held) == CLOSED


def _bindings_on_disk(root: Path) -> set[str]:
    directory = root / BINDING_KIND
    return {path.name for path in directory.iterdir()} if directory.is_dir() else set()


# --- W17: the intent-position rule, operationally --------------------------------


def test_w17_p_a_a_second_writer_between_tip_read_and_append_is_refused_durably(pair):
    """§6: the second writer commits between step 0's tip read and its
    `append_intent` — a port wrapper, not a thread — and the refusal is the
    guard's recomputation at the intent's position."""
    first, _ = publish(pair)  # B1, a first publication
    inner = pair.writers[0]._operation_port
    superseding: list[BindingOutcome] = []

    class SecondWriter:
        """Stands in for a second process on the same root (decision 11): before
        the intent is appended, it commits a whole publish superseding B1."""

        root, profile, authority = inner.root, inner.profile, inner.authority

        def append_intent(self, payload):
            if not superseding:
                superseding.append(publish(pair)[1])  # B3 supersedes B1, committed before this intent
            return inner.append_intent(payload)

        def __getattr__(self, name):
            return getattr(inner, name)

    opened = open_at(pair, port=SecondWriter())
    assert opened.intent.binding_tips == (binding_uid(first.intent.event_token),)  # the tip read before B3
    (b3,) = superseding
    assert type(b3.report.entries[0].outcome) is BindingBound
    before = _bindings_on_disk(pair.roots[0])
    outcome = bind(pair, opened)
    (entry,) = outcome.report.entries
    assert type(entry.outcome) is BindingPredecessorNotStanding and outcome.binding is None
    assert entry.outcome.tips == (bound(b3).uid,)
    assert _bindings_on_disk(pair.roots[0]) == before
    assert not any(name.endswith(f".{binding_uid(opened.intent.event_token)}.md") for name in before)
    _closed_durably(pair.writers[0], opened, outcome)


def test_w17_p_b_a_supersession_after_the_intent_commits_a_lawful_sibling_durably(pair):
    publish(pair)  # B1
    opened = open_at(pair)
    _, b3 = publish(pair)  # B3 supersedes B1, after this intent
    outcome = bind(pair, opened)
    assert type(outcome.report.entries[0].outcome) is BindingBound and outcome.binding is not None
    divergent = tips(pair)
    assert type(divergent) is CoordinationRefused and divergent.reason == "divergent-view"
    assert set(divergent.tips) == {outcome.binding.uid, bound(b3).uid}
    _, repair = publish(pair)  # the repair supersedes both
    assert repair.binding is not None
    resolved = tips(pair)
    assert resolved.kind == BINDING_KIND and resolved.uid == repair.binding.uid


def test_w17_p_c_a_revision_past_its_anchor_is_not_present_durably(pair):
    """§6: the anchor is the one the intent carries, read back from the chain."""
    _, earlier = publish(pair, side=1)  # B1 in the other root
    opened = open_at(pair)
    _, later = publish(pair, side=1)  # B3 in the other root, after the anchor
    decoded = decode_publish_intent(_payload_at(pair.roots[0], opened.digest))
    assert decoded.anchors == opened.intent.anchors and len(decoded.anchors) == 1
    present = standing_at(
        pair.resolver.mounted(),
        binding_address(pair.view, LOCAL),
        BINDING_KIND,
        written=pair.roots[0],
        position=opened.digest,
        anchors=decoded.anchors,
        seam=moment_seam(),
    )
    assert type(present) is tuple
    assert {r.node.uid for r in present} == set(opened.intent.binding_tips) == {bound(earlier).uid}
    assert bound(later).uid not in {r.node.uid for r in present}
    reopened = open_at(pair)
    assert reopened.intent.binding_tips == (bound(later).uid,)


def test_w17_p_d_mount_order_moves_neither_anchors_nor_tips_durably(work_directory, base_contract, monkeypatch):
    """Three roots: the written `-a`, then `-b` and `-c`, whose ids ("8"*32, "0"*32)
    run opposite to their path order. `CoordinationResolver` sorts its own mounts
    by path, so mount order is varied where the judgment takes it: the mapping
    handed to `standing_at` and `marker_tips_at`."""
    with mounted(work_directory, base_contract, monkeypatch, ("f" * 32, "8" * 32, "0" * 32)) as three:
        publish(three, side=1)
        publish(three, side=2)
        opened = open_at(three)
        assert [a.corpus_id for a in opened.intent.anchors] == ["0" * 32, "8" * 32]  # corpus-id order, not path order
        forward = dict(three.resolver.mounted())
        assert list(forward.values()) == ["f" * 32, "8" * 32, "0" * 32]
        backward = dict(reversed(list(forward.items())))
        address = binding_address(three.view, LOCAL)
        judged = [
            standing_at(
                mounts,
                address,
                BINDING_KIND,
                written=three.roots[0],
                position=opened.digest,
                anchors=opened.intent.anchors,
                seam=moment_seam(),
            )
            for mounts in (forward, backward)
        ]
        present = [value for value in judged if type(value) is tuple]
        assert len(present) == 2
        assert [tuple(sorted(r.node.uid for r in value)) for value in present] == [opened.intent.binding_tips] * 2
        folded = [
            marker_tips_at(
                mounts,
                three.view,
                LOCAL,
                written=three.roots[0],
                position=opened.digest,
                anchors=opened.intent.anchors,
                seam=moment_seam(),
                binding_tips=value,
            )
            for mounts, value in zip((forward, backward), present, strict=True)
        ]
        assert folded == [opened.intent.marker_tips] * 2


@pytest.mark.parametrize("damage", ["missing", "mismatch", "unregistered", "rewritten"])
def test_w17_p_e_the_chain_not_the_directory_says_which_revisions_exist_durably(pair, damage):
    """§6: each refusal is raised by the chain's inventory (and its re-read), not
    by the resolver's live read of the directory — which would, in every case,
    answer a standing tip."""
    publish(pair)  # A
    _, second = publish(pair)  # B supersedes A
    writer = pair.writers[0]
    path = pair.roots[0] / writer._relative_path(bound(second))
    assert path.is_file()
    if damage == "missing":
        path.unlink()
        expected = "revision-missing"
    elif damage == "mismatch":
        path.chmod(0o644)  # the engine creates records read-only
        path.write_bytes(path.read_bytes() + b"\n")
        expected = "revision-mismatch"
    elif damage == "unregistered":
        stray = binding_record(
            _intent_like(pair.roots[0], second), corpus_id="3" * 32, marker="4" * 32, artifact="5" * 64
        )
        raw_add(pair.roots[0], stray)
        expected = "unregistered-revision"
    else:
        # user review, finding 1: a file no registration created, then rewritten *through
        # the engine* — a committed registration whose own `initial` is already a file.
        like = _intent_like(pair.roots[0], second)
        stray = binding_record(like, corpus_id="3" * 32, marker="4" * 32, artifact="5" * 64)
        raw_add(pair.roots[0], stray)
        stray_path = writer._relative_path(stray)
        old = (pair.roots[0] / stray_path).read_bytes()
        rewritten = binding_record(like, corpus_id="6" * 32, marker="4" * 32, artifact="5" * 64)
        writer._operation_port.execute(
            [
                ReplaceOp(
                    path=stray_path,
                    content=node_to_markdown(rewritten).encode("utf-8"),
                    expected_digest=sha256(old).hexdigest(),
                )
            ]
        )
        assert (pair.roots[0] / stray_path).read_bytes() == node_to_markdown(rewritten).encode("utf-8")
        expected = "history-violated"
    with pytest.raises(PublicationRefused) as refused:
        open_at(pair)
    assert refused.value.reason == expected


def test_w17_p_f_a_rolled_back_creation_is_absent_and_its_retry_present_once_durably(pair, monkeypatch):
    """ROLLBACK_MEANS = patched create effect; RETRY_AFTER_ROLLBACK = same intent (Task 0)."""
    _, first = publish(pair, side=1)  # B1 in the other root
    opened = open_at(pair, side=1)

    def failing(*args, **kwargs):
        raise RuntimeError("cut after registration")

    monkeypatch.setattr(create_file, "apply", failing)
    with pytest.raises(ExecutionError, match="cut after registration"):
        bind(pair, opened, side=1)
    monkeypatch.undo()
    other = pair.roots[1]
    entries = _chain(other)
    settled = {e.registration: e.committed for e in entries if type(e) is SettledEntryView}
    rolled = [e for e in entries if type(e) is RegisteredEntryView and e.fulfills == opened.digest]
    assert [settled.get(e.digest) for e in rolled] == [False]  # registered, then rolled back durably
    would_be = binding_record(opened.intent, corpus_id=CORPUS_ID, marker=opened.intent.event_token, artifact=ARTIFACT)
    would_be_path = other / pair.writers[1]._relative_path(would_be)
    assert not would_be_path.exists()

    # B1 alone: the rolled-back binding is not present, and nothing refused
    assert open_at(pair).intent.binding_tips == (bound(first).uid,)

    # its file, if left: classified by the rolled-back registration — not present, no refusal
    would_be_path.write_bytes(node_to_markdown(would_be).encode("utf-8"))
    left = open_at(pair)
    assert left.intent.binding_tips == (bound(first).uid,)
    would_be_path.unlink()

    retried = bind(pair, opened, side=1)  # the same intent, retried
    assert type(retried.report.entries[0].outcome) is BindingBound and retried.binding is not None
    assert retried.binding.uid == would_be.uid
    again = open_at(pair)
    assert again.intent.binding_tips == (retried.binding.uid,)  # present once, not ambiguous


# --- Y1: the kinds are declared, gated and inert ---------------------------------


def test_y1_a_version_and_door_refusals_durably(work_directory, base_contract, pair):
    v1_profile = coordination_profile(base_contract, version=1)
    root = (work_directory / f"publication-v1-{os.getpid()}-{next(_counter)}").resolve()
    try:
        init_corpus_root(root, authority=FULL)
        open_corpus(root, authority=FULL, profile=v1_profile).adopt_manifest(profile=pins_for(v1_profile))
        resolver = CoordinationResolver({root: v1_profile})
        writer = open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=v1_profile)
        project = writer.mint_coordination("project", content=content_for("project"))
        with pytest.raises(ValidationRefused):
            _open_publication(
                writer,
                resolver,
                view=coordination_revision(project).address,
                destination=LOCAL,
                clock=Clock(),
                seam=moment_seam(),
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)
    writer = pair.writers[0]
    for kind in ("publication", "publication-binding"):
        with pytest.raises(KindNotMintedHere):
            writer.mint_coordination(kind, project=pair.view, content={})
        with pytest.raises(KindNotMintedHere):  # spec §11.3's sabotaged door
            writer.revise_coordination(kind, binding_address(pair.view, LOCAL), predecessors=("0" * 32,), content={})
    _, outcome = publish(pair)
    assert outcome.binding is not None
    with pytest.raises(
        CoordinationKindUnsupported
    ):  # the ordinary add refuses coordination kinds (_refuse_family_kinds)
        writer.add(outcome.binding)
    with pytest.raises(ImportRefused):
        writer.import_bundle(
            [outcome.binding],
            observer="o",
            instrument="i",
            opened_at="2026-09-22T00:00:00Z",
            closed_at="2026-09-22T00:00:01Z",
        )


_WORLD_MEMBERS = (
    "address-map.yaml",
    "producers-map.yaml",
    "retraction-discovery-map.yaml",
    "coreference-map.yaml",
    "producer-snapshot.yaml",
)


def test_y1_b_publication_records_are_inert_to_the_world_and_to_belief_durably(work_directory, base_contract, pair):
    corpus_root = pair.roots[0]
    world_root = (work_directory / f"publication-world-{os.getpid()}-{next(_counter)}").resolve()
    config = WorldConfig(world_root, "e" * 32, (corpus_root,))
    try:
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus_root, provenance=Fresh())
        bindings = shipped_bindings(world)
        corpus_id = load_manifest(corpus_root).corpus_id
        before = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
        _, outcome = publish(pair)
        assert outcome.binding is not None and (corpus_root / pair.writers[0]._relative_path(outcome.binding)).is_file()
        marker = marker_record(
            decode_publish_intent(_payload_at(corpus_root, _intent_digest(corpus_root, outcome))),
            world_id="e" * 32,
            epoch=before.packaging_identity,
            selection=("proposition:p1",),
        )
        raw_add(corpus_root, marker)
        after = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
        assert before.packaging_identity != after.packaging_identity
        # The door commits the binding beside its act report, and an act report is a
        # world record: its one address-map entry is the only move. No entry names
        # the binding or the marker; every other map is byte-unchanged.
        report_id = stored.act_report_node(outcome.report).id
        earlier = yaml.safe_load(before.members["address-map.yaml"])["addresses"]
        later = yaml.safe_load(after.members["address-map.yaml"])["addresses"]
        assert [entry["address"] for entry in later if entry not in earlier] == [report_id]
        assert [entry for entry in later if entry["address"] != report_id] == earlier
        for member in _WORLD_MEMBERS[1:]:
            assert before.members[member] == after.members[member]
        snapshots = [
            derive.producer_snapshot(yaml.safe_load(value.members["producer-snapshot.yaml"])).identity()
            for value in (before, after)
        ]
        ordinary = belief_scenario()
        pin = ordinary["context"].pins["c1"]
        pinned = {
            "c1": CorpusPins(
                pin.science_contract,
                {**pin.domains, "coordination": "coordination:" + pair.profile.activated_contracts["coordination"]},
            )
        }
        answers = [
            evaluate(
                **{
                    **ordinary,
                    "context": replace(ordinary["context"], producer_snapshot_identity=snapshot, pins=pinned),
                }
            )
            for snapshot in snapshots
        ]
        first, second = answers
        assert isinstance(first, Belief) and isinstance(second, Belief)
        assert first.belief_input_digest == second.belief_input_digest
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(world_root), ignore_errors=True)


# --- Y2: byte-functions of the intent ---------------------------------------------


def test_y2_a_the_committed_binding_is_the_factory_of_its_decoded_intent_durably(pair):
    """§6: the clock advances on every read, so a door that read it into the
    record would commit bytes the factory over the decoded intent does not make."""
    clock = Clock()
    opened, outcome = publish(pair, clock=clock)
    assert clock.n >= 2  # step 0 and step 8 each read it, and each read moved it
    decoded = decode_publish_intent(_payload_at(pair.roots[0], opened.digest))
    assert decoded == opened.intent
    rebuilt = binding_record(decoded, corpus_id=CORPUS_ID, marker=opened.intent.event_token, artifact=ARTIFACT)
    assert outcome.binding is not None
    on_disk = (pair.roots[0] / pair.writers[0]._relative_path(outcome.binding)).read_bytes()
    assert on_disk == node_to_markdown(rebuilt).encode("utf-8")
    assert on_disk == node_to_markdown(
        binding_record(decoded, corpus_id=CORPUS_ID, marker=opened.intent.event_token, artifact=ARTIFACT)
    ).encode("utf-8")


# --- Y3: the audit reads publish intents by their domain ----------------------------


def test_y3_a_the_audit_reads_publish_intents_by_their_domain_durably(pair):
    opened, _ = publish(pair)
    unclosed = open_at(pair)
    port = pair.writers[0]._operation_port
    malformed = port.append_intent(b'{"domain":"science.publish-intent.v1","kind":"publish"}')
    bare = port.append_intent(b'{"actor":"actor","event_token":"' + b"c" * 32 + b'","kind":"publish"}')
    rows, findings = _reduced(pair.roots[0])
    assert rows[opened.digest] == "matched"
    assert rows[unclosed.digest] == "attempt-without-recorded-outcome"
    codes = {(f.ref, f.code) for f in findings}
    assert (malformed, "intent-payload-malformed") in codes
    assert (bare, "intent-payload-malformed") in codes


# --- Y4: step 8 is all-or-nothing; orphans ------------------------------------------


class _CountingPort:
    """Forwards to the writer's durable port and counts fulfilling submissions."""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.guarded = 0

    root = property(lambda self: self._inner.root)
    profile = property(lambda self: self._inner.profile)
    authority = property(lambda self: self._inner.authority)

    def execute_fulfilling_guarded(self, plan, fulfills, *, guard, fallback):
        self.guarded += 1
        return self._inner.execute_fulfilling_guarded(plan, fulfills, guard=guard, fallback=fallback)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def test_y4_a_one_fulfilling_submission_each_way_and_no_binding_on_refusal_durably(pair):
    """§6: the count is of `execute_fulfilling_guarded` calls on a wrapper over the durable port."""
    writer = pair.writers[0]
    success_port = _CountingPort(writer._operation_port)
    _, success = publish(pair, port=success_port)
    assert success_port.guarded == 1 and success.binding is not None
    assert (pair.roots[0] / writer._relative_path(success.binding)).is_file()

    refusal_port = _CountingPort(writer._operation_port)
    opened = open_at(pair, port=refusal_port)
    one_root = CoordinationResolver({pair.roots[0]: pair.profile})  # the intent anchored two roots: mounts-changed
    refused = bind(pair, opened, resolver=one_root, port=refusal_port)
    assert refusal_port.guarded == 1 and refused.binding is None
    (entry,) = refused.report.entries
    assert type(entry.outcome) is BindingEvidenceRefused and entry.outcome.reason == "mounts-changed"
    uid = binding_uid(opened.intent.event_token)
    assert not any(name.endswith(f".{uid}.md") for name in _bindings_on_disk(pair.roots[0]))
    _closed_durably(pair.writers[0], opened, refused)


def test_y4_b_a_remotely_revealed_refusal_is_an_orphan_until_a_shared_publish_retires_it_durably(pair):
    one_root = CoordinationResolver({pair.roots[0]: pair.profile})
    opened = open_at(pair, destination=REMOTE)
    refused = bind(pair, opened, resolver=one_root, remotely_revealed=True)
    assert type(refused.report.entries[0].outcome) is BindingEvidenceRefused
    orphan = (CORPUS_ID, opened.intent.event_token)
    carrying, bound = publish(pair, destination=REMOTE)
    assert orphan in carrying.intent.marker_tips
    assert type(bound.report.entries[0].outcome) is BindingBound
    after = open_at(pair, destination=REMOTE)
    assert orphan not in after.intent.marker_tips
    local = open_at(pair)
    bind(pair, local, resolver=one_root)
    assert (CORPUS_ID, local.intent.event_token) not in publish(pair)[0].intent.marker_tips


def test_y4_c_a_lost_refusal_report_refuses_rather_than_dropping_the_orphan_durably(pair):
    one_root = CoordinationResolver({pair.roots[0]: pair.profile})
    opened = open_at(pair, destination=REMOTE)
    refused = bind(pair, opened, resolver=one_root, remotely_revealed=True)
    assert (CORPUS_ID, opened.intent.event_token) in open_at(pair, destination=REMOTE).intent.marker_tips
    (pair.roots[0] / pair.writers[0]._relative_path(stored.act_report_node(refused.report))).unlink()
    with pytest.raises(PublicationRefused) as caught:
        open_at(pair, destination=REMOTE)
    assert caught.value.reason == "revision-missing"
