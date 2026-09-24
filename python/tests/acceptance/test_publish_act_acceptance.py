"""Conformance cut 40 — the publish act, local (publish-act-local design §14.2).
Fifteen declaration units over real roots on the certified volume, each run
under exactly the publication permit (decision 6).

Crashes are injected at step boundaries by monkeypatching the act's named step
functions, which raise and discard in-memory state; a fresh `resume_publish`
then reads only disk. Tests may import `atoms` (the foreign-replica refusal's
type); only source modules may not."""

from __future__ import annotations

import json
import shutil
from itertools import count
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace
from typing import Any

import pytest
from atoms.coordinator.lifecycle import RootOperationMismatch
from authority import ACTOR, FULL
from coordination_fixtures import content_for, coordination_profile, raw_add
from durable_fixture import pinned
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from profiles import BASE, WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for
from test_world_receipts import hold_shipped
from test_world_selection import topic_nodes

from beliefs import publish as act
from beliefs import stored
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.errors import PublicationArrivalRefused, PublicationRefused, SelectionRefused, ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publication import binding_record, marker_record, marker_uid
from beliefs.publication_arrival import admit_publication
from beliefs.publication_doors import _open_publication, attempt_reading
from beliefs.publish import Published, PublishRefused, PublishUnresolved, pending_publishes, publish, resume_publish
from beliefs.publish_request import Snapshot, decode_snapshot, encode_snapshot
from beliefs.root import (
    LifecycleState,
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    moment_seam,
    open_corpus,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, epoch, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.world.logmodel import IntentEntryView, WellFormedView
from beliefs.world.read import current_epoch
from beliefs.world.selection import evaluate_query
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view

AUTHORITY = scoped_authority(RequiredCapabilities.publishes(), ACTOR)
"""Exactly the publication permit: the writers that call `publish` and `resume_publish` bind it."""
SETUP = FULL
"""Fixture construction — corpora, worlds, epochs, the view's revisions — is not
the act under test and runs under the full permit (finding 6)."""
FOREIGN_REPLICA = RootOperationMismatch
"""What `replicate_root` raises over a destination another operation occupies (Task 0's probe)."""
V2 = coordination_profile(None, version=2)
KINDS = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset", "run"]}]}]}
_counter = count()


class Clock:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-23T00:00:{self.n:02d}Z"


class Crash(Exception):
    """A process death at a step boundary: in-memory state is discarded after it."""


def crash(monkeypatch, name: str, *, before: bool = False, on_call: int = 1) -> None:
    """Replace the act's step `name` with one that dies before or after its `on_call`th call."""
    original = getattr(act, name)
    calls = {"n": 0}

    def crashing(*args, **kwargs):
        calls["n"] += 1
        if before and calls["n"] == on_call:
            raise Crash(name)
        result = original(*args, **kwargs)
        if not before and calls["n"] == on_call:
            raise Crash(name)
        return result

    monkeypatch.setattr(act, name, crashing)


@pytest.fixture()
def source(work_directory):
    """A source world of two BASE corpora (topic_nodes), a written root under
    coordination v2 holding the view (a project whose query selects datasets and
    runs), an operations root and a destination — all on the certified volume."""
    base = Path(mkdtemp(prefix="cut40-", dir=work_directory)).resolve()
    roots: list[Path] = []

    def corpus(profile=BASE, nodes=()):
        path = base / f"corpus-{next(_counter)}"
        roots.append(path)
        init_corpus_root(path, authority=SETUP)
        writer = open_corpus(path, authority=SETUP, profile=profile)
        manifest = writer.adopt_manifest(profile=pins_for(profile))
        for node in nodes:
            writer.add(node.model_copy(deep=True))
        return manifest.corpus_id, path, writer

    try:
        alpha_nodes, beta_nodes = topic_nodes()
        a, alpha, alpha_writer = corpus(nodes=tuple(n for n in alpha_nodes if n.kind != "project"))
        b, beta, _ = corpus(nodes=beta_nodes)
        world_root = base / "world"
        roots.append(world_root)
        config = WorldConfig(world_root, "e" * 32, (alpha, beta))
        init_world_root(config, authority=SETUP)
        world = open_world(config, authority=SETUP)
        world.admit(alpha, provenance=Fresh())
        world.admit(beta, provenance=Fresh())
        epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
        written = base / "written"
        roots.append(written)
        init_corpus_root(written, authority=SETUP)
        open_corpus(written, authority=SETUP, profile=V2).adopt_manifest(profile=pins_for(V2))
        resolver = CoordinationResolver({written: V2})
        writer = open_corpus(written, authority=SETUP, profile=V2, coordination_resolver=resolver)
        project = writer.mint_coordination("project", content=content_for("project", query=KINDS))
        ops, dest = base / "ops", base / "dest"
        ops.mkdir()
        dest.mkdir()
        yield SimpleNamespace(
            base=base,
            roots=roots,
            world=open_world(config, authority=AUTHORITY),
            setup_world=world,
            alpha=alpha,
            alpha_writer=alpha_writer,
            corpus=corpus,
            written=written,
            writer=open_corpus(written, authority=AUTHORITY, profile=V2, coordination_resolver=resolver),
            resolver=resolver,
            view=coordination_revision(project).address,
            ops=ops,
            dest=dest,
            a=a,
            b=b,
            destination=Destination.local(str(dest)),
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)
        for root in roots:
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def run(s, **changes):
    """Step 0 onward, under exactly the publication permit."""
    arguments: dict[str, Any] = {
        "view": s.view,
        "destination": s.destination,
        "operations_root": s.ops,
        "staging_profile": V2,
        "clock": Clock(),
        "seam": moment_seam(),
    }
    arguments.update(changes)
    return publish(s.writer, s.resolver, s.world, **arguments)


def fresh_writer(s) -> CorpusWriter:
    """A new publishing writer over the written root: in-memory state discarded, as after a crash."""
    return open_corpus(s.written, authority=AUTHORITY, profile=V2, coordination_resolver=s.resolver)


def setup_writer(s) -> CorpusWriter:
    """A setup writer over the written root, for the view's revisions."""
    return open_corpus(s.written, authority=SETUP, profile=V2, coordination_resolver=s.resolver)


def resume(s, token: str):
    return resume_publish(
        fresh_writer(s),
        s.resolver,
        event_token=token,
        operations_root=s.ops,
        staging_profile=V2,
        clock=Clock(),
        seam=moment_seam(),
    )


def _chain(s) -> WellFormedView:
    view = moment_seam().inspect_written(s.written)
    assert type(view) is WellFormedView
    return view


def _payloads(s) -> list[dict]:
    """The written chain's intent payloads, decoded, in chain order."""
    return [json.loads(e.payload) for e in _chain(s).entries if type(e) is IntentEntryView]


def token_of_last_intent(s) -> str:
    """The newest publish intent's token on the written chain."""
    return [p for p in _payloads(s) if p.get("domain") == "science.publish-intent.v1"][-1]["event_token"]


def chain_tip(s) -> str:
    return _chain(s).tip


def _project(s):
    """The view's current revision, resolved live."""
    return s.resolver.resolve(s.view.unpinned())


def _revise_query(s, query) -> None:
    """Revise the view's query (a new project revision superseding the tip) and repoint `s.view`."""
    revised = setup_writer(s).revise_coordination(
        "project", s.view.unpinned(), predecessors=(_project(s).uid,), content=content_for("project", query=query)
    )
    s.view = coordination_revision(revised).address


def published_records(root: Path) -> dict[str, bytes]:
    return {n.id: (root / path_for_node_id(n.id)).read_bytes() for n in ReadView.opened_at(root).iter_stored()}


def _publish_reports(s, token: str) -> list:
    """The stored act-report facets of this attempt on the written root."""
    facets = (stored.act_report_facet(n) for n in ReadView.opened_at(s.written).iter_stored() if n.kind == "act-report")
    return [f for f in facets if f["operation"] == "publish" and f["event_token"] == token]


def _binding_files(s) -> list[Path]:
    """The binding revisions on the written root."""
    folder = s.written / "publication-binding"
    return sorted(folder.iterdir()) if folder.is_dir() else []


def _ops_tree(s) -> list[tuple[str, bytes | None]]:
    return sorted((str(p.relative_to(s.ops)), p.read_bytes() if p.is_file() else None) for p in s.ops.rglob("*"))


# --- Y5 -------------------------------------------------------------------------


def _query(*kinds):
    return {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": list(kinds)}]}]}


def _pins_disagree(s):
    """Two more corpora whose biology pins disagree, both covered, their datasets
    selected by the view's own query (datasets and runs, so the closure is complete)."""
    ids = []
    for profile, title in ((WITH_BIOLOGY, "bio-1"), (WITH_BIOLOGY_OTHER, "bio-2")):
        corpus_id, root, _ = s.corpus(profile, nodes=(stored.dataset_node(title=title, resources=pinned()),))
        config = WorldConfig(s.world.config.world_root, s.world.config.world_id, (*s.world.config.corpus_roots, root))
        s.setup_world = open_world(config, authority=SETUP)
        s.setup_world.admit(root, provenance=Fresh())
        s.world = open_world(config, authority=AUTHORITY)
        ids.append(corpus_id)
    epoch.build_epoch(s.setup_world, coverage=frozenset({s.a, s.b, *ids}), bindings=hold_shipped(s.setup_world))
    return {}


def _coordination_v1(s):
    """The view on a written root pinning coordination v1, which declares no `publication`."""
    v1 = coordination_profile(None, version=1)
    written = s.base / "written-v1"
    s.roots.append(written)
    init_corpus_root(written, authority=SETUP)
    open_corpus(written, authority=SETUP, profile=v1).adopt_manifest(profile=pins_for(v1))
    s.resolver = CoordinationResolver({written: v1})
    minted = open_corpus(written, authority=SETUP, profile=v1, coordination_resolver=s.resolver).mint_coordination(
        "project", content=content_for("project", query=KINDS)
    )
    s.writer = open_corpus(written, authority=AUTHORITY, profile=v1, coordination_resolver=s.resolver)
    s.written = written
    s.view = coordination_revision(minted).address
    return {}


def _drift(s):
    s.alpha_writer.add(stored.dataset_node(title="late", resources=pinned()))
    return {}


def _absent(s):
    (s.alpha / "corpus.yaml").unlink()
    return {}


STEP_0 = {
    "empty-selection": (lambda s: _revise_query(s, _query("verification")) or {}, PublicationRefused, ()),
    "closure-incomplete": (lambda s: _revise_query(s, _query("dataset")) or {}, PublicationRefused, ("run:r-b",)),
    "pins-disagree": (_pins_disagree, PublicationRefused, ()),
    "coordination-unpinned": (_coordination_v1, PublicationRefused, ()),
    "selection-incomplete": (_absent, PublicationRefused, ()),
    "destination-unusable": (
        lambda s: {"destination": Destination.local(str(s.base / "missing"))},
        PublicationRefused,
        (),
    ),
    "operations-root-unusable": (lambda s: {"operations_root": s.written}, PublicationRefused, ()),
    "profile-disagrees": (lambda s: {"staging_profile": BASE}, PublicationRefused, ()),
    "corpus-drifted": (_drift, SelectionRefused, ()),
}


@pytest.mark.parametrize("reason", list(STEP_0))
def test_y5_a_every_step_0_refusal_writes_nothing_durably(source, reason):
    """Y5-a: each pre-intent refusal leaves the chain's tip and the operations root byte-unchanged."""
    prepare, refusal, refs = STEP_0[reason]
    changes = prepare(source)
    tip, ops = chain_tip(source), _ops_tree(source)
    with pytest.raises(refusal) as caught:
        run(source, **changes)
    assert caught.value.reason == reason
    if refs:
        assert caught.value.refs == refs
    assert chain_tip(source) == tip and _ops_tree(source) == ops == []


def test_y5_b_a_view_revised_between_evaluation_and_lock_refuses_durably(source, monkeypatch):
    """Y5-b: a view revised between evaluation and lock refuses `view-revised`; nothing is appended."""
    original = act._open_publication
    evaluated = _project(source).uid

    def revising(writer, resolver, **kwargs):
        setup_writer(source).revise_coordination(
            "project",
            source.view.unpinned(),
            predecessors=(evaluated,),
            content=content_for("project", query=KINDS, body="revised"),
        )
        return original(writer, resolver, **kwargs)

    monkeypatch.setattr(act, "_open_publication", revising)
    before = _payloads(source)
    with pytest.raises(PublicationRefused) as caught:
        run(source)
    assert caught.value.reason == "view-revised"
    assert not any(source.ops.rglob("*"))
    assert all(p.get("domain") != "science.publish-intent.v1" for p in _payloads(source))
    assert len(_payloads(source)) == len(before)


# --- Y6 -------------------------------------------------------------------------


def test_y6_a_the_selection_is_fixed_before_the_intent_and_a_drift_after_it_strands_nothing_durably(
    source, monkeypatch
):
    """Y6-a: the world drifts after the intent; re-evaluation refuses `corpus-drifted`;
    the resume publishes the step-0 selection byte for byte."""
    original = act._open_publication

    def drifting(writer, resolver, **kwargs):
        opened = original(writer, resolver, **kwargs)
        source.alpha_writer.add(stored.dataset_node(title="late", resources=pinned()))  # the world drifts
        return opened

    monkeypatch.setattr(act, "_open_publication", drifting)
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    with pytest.raises(SelectionRefused) as drifted:
        evaluate_query(open_world_view(source.world, current_epoch(source.world)), stored_query(_project(source)))
    assert drifted.value.reason == "corpus-drifted"
    outcome = resume(source, token)
    assert type(outcome) is Published
    snapshot = decode_snapshot((source.ops / "publish" / token / "selection.v1").read_bytes())
    held = published_records(source.dest / outcome.corpus_id)
    assert {i: t.encode() for i, t in snapshot.records} == {
        i: b for i, b in held.items() if not i.startswith("publication:")
    }


def test_y6_b_a_rewritten_snapshot_is_request_corrupt_durably(source, monkeypatch):
    """Y6-b: the snapshot rewritten with other bytes → `request-corrupt`, closed, no binding."""
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    snapshot = source.ops / "publish" / token / "selection.v1"
    original = decode_snapshot(snapshot.read_bytes())
    # A valid, canonically encoded snapshot of other bytes: it decodes, so only
    # the identity check against the request refuses it.
    rewritten = encode_snapshot(Snapshot(token, original.records[:-1]))
    assert rewritten != snapshot.read_bytes() and decode_snapshot(rewritten).records == original.records[:-1]
    snapshot.chmod(0o644)
    snapshot.write_bytes(rewritten)
    outcome = resume(source, token)
    assert outcome == PublishRefused(token, "request-corrupt")
    (report,) = _publish_reports(source, token)
    (entry,) = report["entries"]
    assert entry["outcome"]["reason"] == "snapshot-mismatch", entry
    reading = attempt_reading(fresh_writer(source), token, moment_seam())
    assert reading is not None and reading.reading == "closed"
    assert _binding_files(source) == [] and not list(source.dest.iterdir())


# --- Y7 -------------------------------------------------------------------------


def test_y7_a_a_crash_after_k_staged_records_resumes_at_k_plus_one_durably(source, monkeypatch):
    """Y7-a: a crash after one staged record → the resume writes records 2 … 4 once each."""
    staged = {"n": 0}
    original = CorpusWriter._stage_record

    def failing(self, text):
        staged["n"] += 1
        if staged["n"] == 2:
            raise Crash("after one record")
        return original(self, text)

    monkeypatch.setattr(CorpusWriter, "_stage_record", failing)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    written: list[str] = []

    def counting(self, text):
        written.append(text)
        return original(self, text)

    monkeypatch.setattr(CorpusWriter, "_stage_record", counting)
    token = token_of_last_intent(source)
    snapshot = decode_snapshot((source.ops / "publish" / token / "selection.v1").read_bytes())
    outcome = resume(source, token)
    assert len(snapshot.records) == 4  # d-a, d-b, r-a, r-b
    assert type(outcome) is Published and written == [text for _, text in snapshot.records[1:]]


def test_y7_b_an_extra_staged_record_is_staging_corrupt_and_staging_is_retained_durably(source, monkeypatch):
    """Y7-b: an extra record raw-written into staging → `staging-corrupt` naming it,
    the report alone, staging retained."""
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    raw_add(source.ops / "publish" / token / "staging", extra)
    assert resume(source, token) == PublishRefused(token, "staging-corrupt")
    (report,) = _publish_reports(source, token)
    (entry,) = report["entries"]
    assert entry["kind"] == "publication-staging" and extra.id in json.dumps(entry["outcome"])
    assert _binding_files(source) == []
    assert (source.ops / "publish" / token / "staging").is_dir() and not list(source.dest.iterdir())


# --- Y8 -------------------------------------------------------------------------


def test_y8_a_a_publication_lands_at_its_corpus_id_and_a_second_lands_beside_it_durably(source):
    """Y8-a: read-only-serviceable at `<destination>/<corpus_id>` with the sibling
    beside it; a second publish lands beside it, and its marker supersedes the first's."""
    first = run(source)
    assert type(first) is Published
    root = source.dest / first.corpus_id
    assert read_lifecycle_state(root) is LifecycleState.READ_ONLY_SERVICEABLE
    assert (source.dest / f"{first.corpus_id}.head-artifact.v1").is_file()
    second = run(source)
    assert type(second) is Published and second.corpus_id != first.corpus_id
    assert read_lifecycle_state(source.dest / second.corpus_id) is LifecycleState.READ_ONLY_SERVICEABLE
    marker = next(
        n for n in ReadView.opened_at(source.dest / second.corpus_id).iter_stored() if n.kind == "publication"
    )
    assert [first.corpus_id, first.marker] in marker.facets[stored.COORDINATION_FACET]["supersedes_markers"]
    assert read_lifecycle_state(root) is LifecycleState.READ_ONLY_SERVICEABLE


def test_two_attempts_do_not_share_directories(source, monkeypatch):
    """Review Focus 3: a crashed attempt's staging is never touched by the next."""
    crash(monkeypatch, "_populate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    stale = token_of_last_intent(source)
    before = sorted(
        (str(p.relative_to(source.ops)), p.read_bytes() if p.is_file() else None)
        for p in (source.ops / "publish" / stale).rglob("*")
    )
    done = run(source)
    assert type(done) is Published and done.event_token != stale
    after = sorted(
        (str(p.relative_to(source.ops)), p.read_bytes() if p.is_file() else None)
        for p in (source.ops / "publish" / stale).rglob("*")
    )
    assert after == before


def test_y8_b_a_colliding_sibling_is_export_collision_and_binds_nothing_durably(source, monkeypatch):
    """Y8-b: a pre-existing sibling with other bytes → `export-collision`, no binding."""
    crash(monkeypatch, "_write_sibling", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    sibling = source.dest / f"{corpus_id}.head-artifact.v1"
    sibling.write_bytes(b"someone else's artifact")
    assert resume(source, token) == PublishRefused(token, "export-collision")
    assert sibling.read_bytes() == b"someone else's artifact"
    assert not (source.dest / corpus_id).exists() and _binding_files(source) == []


def test_a_foreign_root_at_the_export_path_binds_nothing_durably(source, monkeypatch):
    """Finding 2: a serviceable replica of another corpus occupying
    `<destination>/<corpus_id>` is refused by `replicate_root`, never taken as
    this attempt's copy; the attempt stays pending (spec §16 item 6)."""
    crash(monkeypatch, "_replicate", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    other_id, other, _ = source.corpus(nodes=(stored.run_node("o", title="o", spec="s", produces=[]),))
    foreign_root = source.base / "foreign-world"
    source.roots.append(foreign_root)
    config = WorldConfig(foreign_root, "a" * 32, (other,))
    init_world_root(config, authority=SETUP)
    foreign_world = open_world(config, authority=SETUP)
    foreign_world.admit(other, provenance=Fresh())
    artifact = export_head_artifact(foreign_world, CorpusSubject(other_id))
    occupant = source.dest / corpus_id
    source.roots.append(occupant)
    replicate_root(other, occupant, authority=SETUP)
    restore_root(
        occupant, CorpusSubject(other_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=SETUP
    )
    assert read_lifecycle_state(occupant) is LifecycleState.READ_ONLY_SERVICEABLE
    tip = chain_tip(source)
    with pytest.raises(FOREIGN_REPLICA):
        resume(source, token)
    assert _binding_files(source) == [] and chain_tip(source) == tip
    reading = attempt_reading(fresh_writer(source), token, moment_seam())
    assert reading is not None and reading.reading == "unfinished"
    assert token in pending_publishes(fresh_writer(source), operations_root=source.ops, seam=moment_seam())


# --- Y9 -------------------------------------------------------------------------


BOUNDARIES = [
    ("_initialize", True),
    ("_initialize", False),
    ("_populate", False),
    ("_admit_and_export", False),
    ("_write_sibling", False),
    ("_replicate", False),
    ("_restore", False),
    ("_bind", True),
]


@pytest.mark.parametrize("step, before", BOUNDARIES, ids=[f"{'before' if b else 'after'}{s}" for s, b in BOUNDARIES])
def test_y9_a_a_crash_at_every_local_step_resumes_to_one_binding_and_one_report_durably(
    source, monkeypatch, step, before
):
    """Y9-a: for each step boundary 1–6 and 8, crash then resume → `Published`,
    exactly one binding revision and one report, its entries in step order."""
    crash(monkeypatch, step, before=before)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    outcome = resume(source, token)
    assert type(outcome) is Published
    (report,) = _publish_reports(source, token)
    assert [e["kind"] for e in report["entries"]] == [
        "publication-staging",
        "publication-export",
        "publication-reveal",
        "publication-binding",
    ]
    assert len(_binding_files(source)) == 1
    assert read_lifecycle_state(source.dest / outcome.corpus_id) is LifecycleState.READ_ONLY_SERVICEABLE


def test_y9_a_a_lost_sibling_after_replication_is_rewritten_byte_identically_durably(source, monkeypatch):
    """Y9-a's `stamped copy, sibling missing` row: export (pure) and step 5 again."""
    crash(monkeypatch, "_replicate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    corpus_id = load_manifest(source.ops / "publish" / token / "staging").corpus_id
    sibling = source.dest / f"{corpus_id}.head-artifact.v1"
    kept = sibling.read_bytes()
    sibling.unlink()
    assert type(resume(source, token)) is Published and sibling.read_bytes() == kept


def test_y9_b_a_binding_beside_an_unfinished_intent_is_unresolved_durably(source, monkeypatch):
    """Y9-b: a binding revision raw-written beside an unfinished intent →
    `PublishUnresolved("binding-without-report")`, nothing written."""
    crash(monkeypatch, "_bind", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    reading = attempt_reading(fresh_writer(source), token, moment_seam())
    assert reading is not None and reading.reading == "unfinished"
    raw_add(
        source.written,
        binding_record(reading.opened.intent, corpus_id="1" * 32, marker=marker_uid(token), artifact="3" * 64),
    )
    tip, ops = chain_tip(source), _ops_tree(source)
    assert resume(source, token) == PublishUnresolved(token, "binding-without-report")
    assert chain_tip(source) == tip and _ops_tree(source) == ops and _publish_reports(source, token) == []


def test_y9_c_pending_lists_crashed_attempts_only_durably(source, monkeypatch):
    """Y9-c: `pending_publishes` lists a crashed attempt and omits a done one and a
    requestless intent; the requestless intent resumes to `no-request`."""
    done = run(source)
    assert type(done) is Published
    crash(monkeypatch, "_populate")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    crashed = token_of_last_intent(source)
    bare = _open_publication(
        fresh_writer(source),
        source.resolver,
        view=source.view.unpinned(),
        destination=source.destination,
        clock=Clock(),
        seam=moment_seam(),
    )
    assert pending_publishes(fresh_writer(source), operations_root=source.ops, seam=moment_seam()) == (crashed,)
    tip = chain_tip(source)
    assert resume(source, bare.intent.event_token) == PublishUnresolved(bare.intent.event_token, "no-request")
    assert chain_tip(source) == tip
    assert done.event_token not in pending_publishes(
        fresh_writer(source), operations_root=source.ops, seam=moment_seam()
    )


def test_y9_d_a_crash_inside_step_9_is_finished_by_the_resume_durably(source, monkeypatch):
    """Y9-d: done, then a crash inside step 9 → the resume discards staging and answers `Published`."""
    crash(monkeypatch, "_discard", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    assert (source.ops / "publish" / token / "staging").is_dir()
    tip = chain_tip(source)
    outcome = resume(source, token)
    assert type(outcome) is Published and outcome.event_token == token
    assert not (source.ops / "publish" / token / "staging").exists()
    assert not (source.ops / "publish" / token / "world").exists()
    assert (source.ops / "publish" / token / "request.v1").is_file()
    assert (source.ops / "publish" / token / "selection.v1").is_file()
    assert chain_tip(source) == tip and len(_binding_files(source)) == 1


def test_y9_e_the_next_publish_reads_success_and_pre_binding_reports_durably(source, monkeypatch):
    """Y9-e: the next publish's step-0 fold reads a successful report (its marker is
    carried) and a pre-binding refused one (its marker is not), and binds."""
    first = run(source)
    second = run(source)
    assert type(first) is Published and type(second) is Published
    reading = attempt_reading(fresh_writer(source), second.event_token, moment_seam())
    assert reading is not None and (first.corpus_id, first.marker) in reading.opened.intent.marker_tips
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    refused_token = token_of_last_intent(source)
    raw_add(
        source.ops / "publish" / refused_token / "staging", stored.run_node("zz", title="zz", spec="s", produces=[])
    )
    assert resume(source, refused_token) == PublishRefused(refused_token, "staging-corrupt")
    third = run(source)
    assert type(third) is Published
    reading = attempt_reading(fresh_writer(source), third.event_token, moment_seam())
    assert reading is not None
    assert (second.corpus_id, second.marker) in reading.opened.intent.marker_tips
    assert all(marker != marker_uid(refused_token) for _, marker in reading.opened.intent.marker_tips)


def test_resume_refuses_another_actor_and_another_profile_writing_nothing(source, monkeypatch):
    """Review Focus 4 (decision 9 and the staging-profile planning note)."""
    crash(monkeypatch, "_initialize", before=True)
    with pytest.raises(Crash):
        run(source)
    monkeypatch.undo()
    token = token_of_last_intent(source)
    tip, ops = chain_tip(source), _ops_tree(source)
    other = open_corpus(
        source.written,
        authority=scoped_authority(RequiredCapabilities.publishes(), "someone-else"),
        profile=V2,
        coordination_resolver=source.resolver,
    )
    with pytest.raises(ValidationRefused):
        resume_publish(
            other,
            source.resolver,
            event_token=token,
            operations_root=source.ops,
            staging_profile=V2,
            clock=Clock(),
            seam=moment_seam(),
        )
    with pytest.raises(ValidationRefused):
        resume_publish(
            fresh_writer(source),
            source.resolver,
            event_token=token,
            operations_root=source.ops,
            staging_profile=BASE,
            clock=Clock(),
            seam=moment_seam(),
        )
    assert chain_tip(source) == tip and _ops_tree(source) == ops
    assert not (source.ops / "publish" / token / "staging").exists()


# --- Y10 ------------------------------------------------------------------------


def _recipient(source, published_root: Path):
    """The recipient's world: a different world, under its own (setup) authority."""
    world_root = source.base / f"recipient-{next(_counter)}"
    source.roots.append(world_root)
    config = WorldConfig(world_root, "c" * 32, (published_root,))
    init_world_root(config, authority=SETUP)
    return open_world(config, authority=SETUP)


def _world_tree(world) -> list[tuple[str, bytes | None]]:
    root = world.config.world_root
    return sorted((str(p.relative_to(root)), p.read_bytes() if p.is_file() else None) for p in root.rglob("*"))


def test_y10_a_a_second_world_admits_a_publication_and_nothing_without_a_marker_durably(source):
    """Y10-a: a second world admits the published root through `admit_publication`,
    and its epoch sees the selection; a plain replica with no marker is refused `marker-absent`."""
    outcome = run(source)
    assert type(outcome) is Published
    root = source.dest / outcome.corpus_id
    world = _recipient(source, root)
    observers = ObserverSet(
        (ArtifactCarrier.from_bytes((source.dest / f"{outcome.corpus_id}.head-artifact.v1").read_bytes()),)
    )
    _, report = admit_publication(world, root, observers)
    assert report.outcome == "validated"
    published = epoch.build_epoch(world, coverage=frozenset({outcome.corpus_id}), bindings=hold_shipped(world))
    view = open_world_view(world, published)
    snapshot = decode_snapshot((source.ops / "publish" / outcome.event_token / "selection.v1").read_bytes())
    assert all(node_to_markdown(view.get(i)) == text for i, text in snapshot.records)
    _, plain, _ = source.corpus(nodes=(stored.run_node("p", title="p", spec="s", produces=[]),))
    other = _recipient(source, plain)
    before = _world_tree(other)
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication(other, plain, observers)
    assert caught.value.reason == "marker-absent"
    assert _world_tree(other) == before


def test_y10_b_a_verified_root_with_records_beyond_its_selection_is_refused_before_admission_durably(source):
    """Y10-b: a root built through the staging doors with one record beyond its
    marker's selection, exported, replicated and restored against its own
    artifact → `selection-mismatch`, and the recipient's registry is unchanged."""
    forged = source.base / "forged-staging"
    source.roots.append(forged)
    init_corpus_root(forged, authority=SETUP)
    writer = open_corpus(forged, authority=SETUP, profile=V2)
    manifest = writer.adopt_manifest(profile=pins_for(V2))
    kept, extra = (stored.run_node(name, title=name, spec="s", produces=[]) for name in ("kept", "extra"))
    writer._stage_record(node_to_markdown(kept))
    writer._stage_record(node_to_markdown(extra))
    opened = _open_publication(
        source.writer,
        source.resolver,
        view=source.view.unpinned(),
        destination=source.destination,
        clock=Clock(),
        seam=moment_seam(),
    )
    writer._stage_marker(marker_record(opened.intent, world_id="e" * 32, epoch="f" * 64, selection=(kept.id,)))
    staging_root = source.base / "forged-world"
    source.roots.append(staging_root)
    config = WorldConfig(staging_root, "b" * 32, (forged,))
    init_world_root(config, authority=SETUP)
    staging_world = open_world(config, authority=SETUP)
    staging_world.admit(forged, provenance=Fresh())
    artifact = export_head_artifact(staging_world, CorpusSubject(manifest.corpus_id))
    copy = source.dest / "forged"
    source.roots.append(copy)
    replicate_root(forged, copy, authority=SETUP)
    observers = ObserverSet((ArtifactCarrier.from_bytes(artifact),))
    assert restore_root(copy, CorpusSubject(manifest.corpus_id), observers, authority=SETUP).outcome == "validated"
    assert read_lifecycle_state(copy) is LifecycleState.READ_ONLY_SERVICEABLE
    recipient = _recipient(source, copy)
    registry_before = _world_tree(recipient)
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication(recipient, copy, observers)
    assert caught.value.reason == "selection-mismatch" and caught.value.refs == (extra.id,)
    assert _world_tree(recipient) == registry_before
