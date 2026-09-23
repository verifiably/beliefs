"""The publish doors and the orphan fold (publication-records design §6, §11.1;
rows W17 and Y4), portable: two writers' worth of `tmp_path` roots under the v2
profile, a recording port whose appended intents are the written root's
fabricated chain, and a fake `MomentSeam` over it. The durable arms that need
real chains (W17-p-a's second writer, W17-p-c's anchor, Y4-a's counted port)
live in the acceptance module."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import ACTOR, FULL, lacking
from coordination_fixtures import coordination_profile, raw_add, raw_coordination_node
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_operation_writes import RecordingPort
from test_publish_intent import intent
from test_standing_at import ABSENT, creation, fake_seam, file_state, place_file, seam_over
from test_world_log_audit import chain, digest, genesis_entry, settlement

from beliefs import boundary, stored
from beliefs.coordination import CoordinationAddress, PositionRefused
from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import LogEvidenceRefused, MalformedRecord, PermitExceeded, PublicationRefused, ValidationRefused
from beliefs.intents.publish import Destination, decode_publish_intent, encode_publish_intent
from beliefs.publication import binding_address, binding_record
from beliefs.publication_doors import (
    PUBLISH_INSTRUMENT,
    OpenedPublication,
    _bind_publication,
    _open_publication,
    marker_tips_at,
)
from beliefs.report import (
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    PublicationBindingEntry,
)
from beliefs.world.logmodel import AbsentView, DefectView, IntentEntryView, MalformedView, RegisteredEntryView
from beliefs.world.registry import CorpusManifest, manifest_bytes

VIEW = CoordinationAddress("a" * 32, "b" * 32, "c" * 32)
HERE = Destination.local("/srv/published/mm30")


def _fold_chain(tmp_path, rows, *, corrupt: bytes | None = None, report_token: str | None = None):
    """One written root: per row, a publish intent, the report its committed
    fulfilment created, and that report's file. The k-th publish's marker uid
    is "ab"[k] * 32 and its corpus_id "1" * 32 (the parametrized cases' pairs)."""
    root = (tmp_path / "written").resolve()
    (root / "act-report").mkdir(parents=True)
    entries = [genesis_entry(b"g", label="fold-genesis")]
    for k, (kind, remote, carried) in enumerate(rows):
        marker = "ab"[k] * 32
        value = intent(event_token=str(k) * 32, binding_tips=(), marker_tips=tuple(carried))
        opened = IntentEntryView(digest=digest(f"fold-intent-{k}"), payload=encode_publish_intent(value))
        outcome = {
            "bound": BindingBound("c" * 32, "1" * 32, marker),
            "evidence-refused": BindingEvidenceRefused("1" * 32, marker, remote, "mounts-changed"),
            "predecessor-not-standing": BindingPredecessorNotStanding("1" * 32, marker, remote, ()),
        }[kind]
        report = boundary._mint_publish_report(
            value if report_token is None else replace(value, event_token=report_token),
            observer=value.actor, instrument="beliefs.publish", opened_at=value.at, closed_at=value.at,
            entry=PublicationBindingEntry("coord:" + "a" * 32 + "/" + "d" * 32, outcome),
        )
        node = stored.act_report_node(report)
        path = path_for_node_id(node.id)
        data = corrupt if corrupt is not None else node_to_markdown(node).encode("utf-8")
        (root / path).write_bytes(data)
        created = RegisteredEntryView(
            digest=digest(f"fold-reg-{k}"), txid=f"fold-{k}", initial=((path, ABSENT),), final=((path, file_state(data)),),
            fulfills=opened.digest,
        )
        entries += [opened, created, settlement(digest(f"fold-set-{k}"), created.digest, f"fold-{k}", committed=True)]
    return root, chain(*entries)


def _fold(root, view):
    return marker_tips_at(
        {root: "9" * 32}, VIEW, HERE, written=root, position=view.tip, anchors=(), seam=seam_over({root: view}), binding_tips=()
    )


# --- the orphan fold (spec §6 marker_tips; row Y4) ------------------------------


@pytest.mark.parametrize(
    "reports, expected",
    [
        # (outcome of each publish in chain order, the intent's marker_tips) -> the orphans the fold returns
        ([("evidence-refused", True, ())], {("1" * 32, "a" * 32)}),                            # remote reveal, refused: an orphan
        ([("predecessor-not-standing", True, ())], {("1" * 32, "a" * 32)}),                    # any refusal reason
        ([("evidence-refused", False, ())], set()),                                           # local reveal: never an orphan
        ([("evidence-refused", True, ()), ("bound", False, (("1" * 32, "a" * 32),))], set()),  # retired by a bound publish carrying it
        ([("evidence-refused", True, ()), ("evidence-refused", True, (("1" * 32, "a" * 32),))], {("1" * 32, "b" * 32)}),  # retired by a shared refusal; the second is itself an orphan
        ([("evidence-refused", True, ()), ("evidence-refused", False, (("1" * 32, "a" * 32),))], {("1" * 32, "a" * 32)}),  # a local refusal retires nothing
    ],
    ids=["remote-refusal", "any-reason", "local-refusal", "retired-by-bound", "retired-by-shared-refusal", "not-retired-by-local"],
)
def test_the_orphan_fold(tmp_path, reports, expected):
    root, view = _fold_chain(tmp_path, reports)
    folded = marker_tips_at(
        {root: "9" * 32}, VIEW, HERE, written=root, position=view.tip, anchors=(), seam=seam_over({root: view}), binding_tips=()
    )
    assert type(folded) is tuple and set(folded) == expected


def test_a_report_that_matches_but_does_not_decode_refuses(tmp_path):
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())], corrupt=b"not a node\n")
    folded = _fold(root, view)
    assert type(folded) is PositionRefused and folded.reason == "revision-malformed"


def test_a_report_that_does_not_qualify_its_intent_refuses(tmp_path):
    """User review, finding 2: a fulfilling report with another event token never folds."""
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())], report_token="e" * 32)
    folded = _fold(root, view)
    assert type(folded) is PositionRefused and folded.reason == "report-unqualified"


def test_a_lost_report_refuses(tmp_path):
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())])
    for report in (root / "act-report").iterdir():
        report.unlink()
    folded = _fold(root, view)
    assert type(folded) is PositionRefused and folded.reason == "revision-missing"


def test_an_intent_with_two_committed_fulfilments_refuses(tmp_path):
    """One intent, one committed fulfilment: the fold never picks one of two —
    here the later one is a well-formed local refusal that would hide the orphan."""
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())])
    opened = view.entries[1]
    assert type(opened) is IntentEntryView
    value = decode_publish_intent(opened.payload)
    report = boundary._mint_publish_report(
        value, observer=value.actor, instrument="beliefs.publish", opened_at=value.at, closed_at="2026-09-22T00:00:01Z",
        entry=PublicationBindingEntry("coord:" + "a" * 32 + "/" + "d" * 32, BindingEvidenceRefused("1" * 32, "a" * 32, False, "mounts-changed")),
    )
    node = stored.act_report_node(report)
    second, data = path_for_node_id(node.id), node_to_markdown(node).encode("utf-8")
    (root / second).write_bytes(data)
    again = RegisteredEntryView(
        digest=digest("fold-reg-again"), txid="fold-again", initial=((second, ABSENT),), final=((second, file_state(data)),),
        fulfills=opened.digest,
    )
    doubled = chain(view.genesis, *view.entries[1:], again, settlement(digest("fold-set-again"), again.digest, "fold-again", committed=True))
    folded = _fold(root, doubled)
    assert type(folded) is PositionRefused and folded.reason == "revision-malformed"

def test_an_intent_for_another_destination_does_not_fold(tmp_path):
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())])
    folded = marker_tips_at(
        {root: "9" * 32}, VIEW, Destination.local("/srv/published/other"), written=root, position=view.tip, anchors=(),
        seam=seam_over({root: view}), binding_tips=(),
    )
    assert folded == ()


def test_the_fold_reads_only_up_to_the_position(tmp_path):
    """The orphan is fulfilled after the position: the fold at the intent entry does not see it."""
    root, view = _fold_chain(tmp_path, [("evidence-refused", True, ())])
    intent_entry = view.entries[1]
    folded = marker_tips_at(
        {root: "9" * 32}, VIEW, HERE, written=root, position=intent_entry.digest, anchors=(), seam=seam_over({root: view}), binding_tips=()
    )
    assert folded == ()


# --- the doors, over a recording port and a fabricated written chain -------------

AT = "2026-09-23T00:00:00Z"
PROJECT = "5" * 32
REVISION = "6" * 32
PROJECT_VIEW = CoordinationAddress(PROJECT)
V2 = coordination_profile(None, version=2)
WRITTEN_ID = "9" * 32


def clock() -> str:
    return AT


class Advancing:
    """Advances one second on every read: a door that reads the clock into a
    record, rather than taking `at` from the intent, writes other bytes (Y2)."""

    def __init__(self) -> None:
        self.reads = 0

    def __call__(self) -> str:
        self.reads += 1
        return f"2026-09-23T00:00:{self.reads:02d}Z"


class ChainPort(RecordingPort):
    """The recording port, whose appended intents are the written root's chain."""

    def __init__(self, authority, root, profile) -> None:
        super().__init__(authority, root)
        self.profile = profile
        self.entries: list = [genesis_entry(b"w", label="doors-written")]

    def append_intent(self, payload: bytes) -> str:
        appended = super().append_intent(payload)
        self.entries.append(IntentEntryView(digest=appended, payload=payload))
        return appended

    def view(self):
        return chain(*self.entries)


def mount(root: Path, corpus_id: str, profile=V2) -> Path:
    """A root whose manifest carries a chosen corpus id, so the tests can run ids against paths."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "corpus.yaml").write_bytes(manifest_bytes(CorpusManifest(2, corpus_id, pins_for(profile))))
    return root


class Doors:
    """The written root `w` and any other mounts, each other mount's chain a lone genesis."""

    def __init__(self, tmp_path: Path, *, others: dict[str, str] | None = None, profile=V2, project: bool = True) -> None:
        self.root = mount((tmp_path / "w").resolve(), WRITTEN_ID, profile)
        self.others = {
            mount((tmp_path / name).resolve(), corpus_id, profile): chain(genesis_entry(corpus_id.encode(), label=f"other-{name}"))
            for name, corpus_id in (others or {}).items()
        }
        self.resolver = CoordinationResolver({self.root: profile, **{other: profile for other in self.others}})
        self.port = ChainPort(FULL, self.root, profile)
        self.profile = profile
        if project:
            raw_add(self.root, raw_coordination_node("project", PROJECT, REVISION))

    def writer(self, authority=FULL) -> CorpusWriter:
        self.port.authority = authority  # a writer's own port binds its authority
        return CorpusWriter(
            self.root, DefaultExecutor, authority=authority, operation_port=self.port,
            coordination_resolver=self.resolver, profile=self.profile,
        )

    def seam(self, *, written=None, other=None):
        def inspect_written(path):
            assert path == self.root
            return self.port.view()

        return fake_seam(written or inspect_written, other or self.others.__getitem__)

    def open(self, authority=FULL, *, view=PROJECT_VIEW, seam=None) -> OpenedPublication:
        return _open_publication(
            self.writer(authority), self.resolver, view=view, destination=HERE, clock=clock, seam=seam or self.seam()
        )

    def bind(self, opened, authority=FULL, *, remotely_revealed=False, seam=None):
        return _bind_publication(
            self.writer(authority), self.resolver, opened, corpus_id="1" * 32, marker="2" * 32, artifact="9" * 64,
            remotely_revealed=remotely_revealed, clock=Advancing(), seam=seam or self.seam(),
        )

    def appended(self) -> list[bytes]:
        return [payload for kind, payload in self.port.calls if kind == "append_intent"]

    def files(self, directory: str) -> list[str]:
        folder = self.root / directory
        return sorted(path.name for path in folder.iterdir()) if folder.is_dir() else []


def _raises_log_evidence(_path):
    raise LogEvidenceRefused("inspect", "ChainStateInvalid", "the chain contradicts its record")


# step 0: every pre-intent refusal appends nothing


def test_a_v1_pinned_writer_refuses_before_the_intent(tmp_path):
    doors = Doors(tmp_path, profile=coordination_profile(None))
    with pytest.raises(ValidationRefused, match="publication-binding is not declared by the mounted coordination contract"):
        doors.open()
    assert doors.port.calls == []


def test_a_view_that_does_not_resolve_refuses_before_the_intent(tmp_path):
    doors = Doors(tmp_path, project=False)
    with pytest.raises(PublicationRefused) as caught:
        doors.open()
    assert caught.value.reason == "view-unresolved" and caught.value.tips == ()
    assert doors.port.calls == []


def test_a_divergent_view_refuses_with_its_tips_before_the_intent(tmp_path):
    doors = Doors(tmp_path)
    raw_add(doors.root, raw_coordination_node("project", PROJECT, "7" * 32))
    with pytest.raises(PublicationRefused) as caught:
        doors.open()
    assert caught.value.reason == "divergent-view" and caught.value.tips == (REVISION, "7" * 32)
    assert doors.port.calls == []


def test_an_authority_without_publish_refuses_before_the_intent(tmp_path):
    doors = Doors(tmp_path)
    with pytest.raises(PermitExceeded):
        doors.open(lacking(families=("publish",)))
    assert doors.port.calls == []


def test_a_position_refusal_from_the_judgment_refuses_before_the_intent(tmp_path):
    """An unregistered binding revision at the address: the step-0 judgment refuses."""
    doors = Doors(tmp_path)
    stray = intent(view=CoordinationAddress(PROJECT, None, REVISION), destination=HERE, binding_tips=(), marker_tips=(), anchors=())
    place_file(doors.root, binding_record(stray, corpus_id="1" * 32, marker="2" * 32, artifact="9" * 64))
    with pytest.raises(PublicationRefused) as caught:
        doors.open()
    assert caught.value.reason == "unregistered-revision"
    assert doors.port.calls == []


def test_an_engine_refusal_to_inspect_at_step_0_propagates_before_the_intent(tmp_path):
    """Ruling 6: at step 0 nothing is revealed and nothing written, so the engine's
    refusal to produce the log evidence propagates as itself."""
    doors = Doors(tmp_path)
    with pytest.raises(LogEvidenceRefused):
        doors.open(seam=doors.seam(written=_raises_log_evidence))
    assert doors.port.calls == []


_MALFORMED = MalformedView(DefectView("cycle", digest("x"), "a cycle"))


@pytest.mark.parametrize("inspector", ["written", "other"])
@pytest.mark.parametrize("answer, reason", [(AbsentView(), "chain-absent"), (_MALFORMED, "chain-malformed")], ids=["absent", "malformed"])
def test_an_unreadable_chain_refuses_before_the_intent(tmp_path, inspector, answer, reason):
    doors = Doors(tmp_path, others={"a-other": "e" * 32})
    with pytest.raises(PublicationRefused) as caught:
        doors.open(seam=doors.seam(**{inspector: lambda _path: answer}))
    assert caught.value.reason == reason
    assert doors.port.calls == []


# step 0: the intent's bytes


def test_the_appended_intent_is_the_opened_intent_with_anchors_in_corpus_id_order(tmp_path):
    # mount paths "a-other" < "b-other" < "w"; corpus ids run against them
    doors = Doors(tmp_path, others={"a-other": "e" * 32, "b-other": "2" * 32})
    opened = doors.open()
    (payload,) = doors.appended()
    assert decode_publish_intent(payload) == opened.intent
    assert opened.digest == doors.port.entries[-1].digest
    value = opened.intent
    assert [anchor.corpus_id for anchor in value.anchors] == ["2" * 32, "e" * 32]
    by_id = {doors.resolver.mounted()[root]: view for root, view in doors.others.items()}
    assert [(anchor.genesis, anchor.head) for anchor in value.anchors] == [
        (by_id[anchor.corpus_id].genesis.digest, by_id[anchor.corpus_id].tip) for anchor in value.anchors
    ]
    assert value.binding_tips == () and value.marker_tips == ()
    assert value.view == CoordinationAddress(PROJECT, None, REVISION)
    assert (value.kind, value.actor, value.at, value.destination) == ("publish", ACTOR, AT, HERE)


# `_append_operation_intent(payload=…)`


def _payload(**changes) -> bytes:
    return encode_publish_intent(intent(**{"event_token": "d" * 32, "actor": ACTOR, **changes}))


@pytest.mark.parametrize(
    "kind, token, payload",
    [
        ("move", "d" * 32, _payload()),
        ("publish", "e" * 32, _payload()),
        ("publish", "d" * 32, _payload(actor="someone-else")),
    ],
    ids=["another-kind", "another-token", "another-actor"],
)
def test_a_pre_encoded_intent_that_disagrees_with_its_arguments_is_refused(tmp_path, kind, token, payload):
    doors = Doors(tmp_path)
    with pytest.raises(MalformedRecord):
        doors.writer()._append_operation_intent(kind, token, ACTOR, payload=payload)
    assert doors.port.calls == []


def test_a_pre_encoded_intent_is_appended_byte_exactly(tmp_path):
    doors = Doors(tmp_path)
    payload = _payload()
    appended = doors.writer()._append_operation_intent("publish", "d" * 32, ACTOR, payload=payload)
    assert doors.appended() == [payload] and appended == doors.port.entries[-1].digest


# step 8


def test_the_binding_door_refuses_an_authority_without_publish_before_any_effect(tmp_path):
    doors = Doors(tmp_path)
    opened = doors.open()
    calls = list(doors.port.calls)
    with pytest.raises(PermitExceeded):
        doors.bind(opened, lacking(families=("publish",)))
    assert doors.port.calls == calls
    assert doors.files("act-report") == [] and doors.files("publication-binding") == []


def test_the_binding_door_refuses_a_non_bool_reveal_before_any_effect(tmp_path):
    doors = Doors(tmp_path)
    opened = doors.open()
    calls = list(doors.port.calls)
    with pytest.raises(MalformedRecord):
        doors.bind(opened, remotely_revealed=1)  # pyright: ignore[reportArgumentType]
    assert doors.port.calls == calls
    assert doors.files("act-report") == [] and doors.files("publication-binding") == []


def test_the_binding_door_commits_the_binding_and_its_report_in_one_fulfilment(tmp_path):
    doors = Doors(tmp_path)
    opened = doors.open()
    outcome = doors.bind(opened)
    binding = outcome.binding
    assert binding is not None
    assert binding == binding_record(opened.intent, corpus_id="1" * 32, marker="2" * 32, artifact="9" * 64)
    report = outcome.report
    assert (report.operation, report.event_token, report.observer, report.instrument) == (
        "publish", opened.intent.event_token, opened.intent.actor, PUBLISH_INSTRUMENT,
    )
    assert report.entries == (
        PublicationBindingEntry(
            str(binding_address(opened.intent.view, opened.intent.destination)), BindingBound(binding.uid, "1" * 32, "2" * 32)
        ),
    )
    kind, (plan, fulfills) = doors.port.calls[-1]
    assert (kind, fulfills) == ("execute_fulfilling", opened.digest)
    assert [op.path for op in plan] == [path_for_node_id(binding.id), path_for_node_id(stored.act_report_node(report).id)]
    assert (doors.root / path_for_node_id(binding.id)).read_bytes() == node_to_markdown(binding).encode("utf-8")


def test_a_revision_committed_after_the_intents_position_does_not_move_the_judgment(tmp_path):
    """The guard judges at the intent's own position, not the written root's
    current tip (W17): a sibling binding committed between step 0 and step 8
    is invisible at the position, so the attempt commits beside it."""
    doors = Doors(tmp_path)
    opened = doors.open()
    sibling = replace(opened.intent, event_token="8" * 32, binding_tips=(), marker_tips=())
    path, data = place_file(doors.root, binding_record(sibling, corpus_id="1" * 32, marker="3" * 32, artifact="9" * 64))
    doors.port.entries.extend(creation("sibling", path, data))
    outcome = doors.bind(opened)
    assert outcome.binding is not None
    assert type(outcome.report.entries[0].outcome) is BindingBound


def _refused_alone(doors, opened, outcome, expected) -> None:
    """The refusal report alone, in the success plan's place (row Y4)."""
    assert outcome.binding is None
    assert outcome.report.entries[0].outcome == expected
    kind, (plan, fulfills) = doors.port.calls[-1]
    assert (kind, fulfills) == ("execute_fulfilling", opened.digest)
    assert [op.path for op in plan] == [path_for_node_id(stored.act_report_node(outcome.report).id)]
    assert doors.files("publication-binding") == []


def test_a_binding_tip_the_position_does_not_hold_is_predecessor_not_standing(tmp_path):
    doors = Doors(tmp_path)
    opened = doors.open()
    stale = OpenedPublication(replace(opened.intent, binding_tips=("3" * 32,)), opened.digest)
    outcome = doors.bind(stale, remotely_revealed=True)
    _refused_alone(doors, stale, outcome, BindingPredecessorNotStanding("1" * 32, "2" * 32, True, ()))


def test_marker_tips_the_position_does_not_yield_are_tips_disagree(tmp_path):
    doors = Doors(tmp_path)
    opened = doors.open()
    frozen = OpenedPublication(replace(opened.intent, marker_tips=(("1" * 32, "4" * 32),)), opened.digest)
    outcome = doors.bind(frozen)
    _refused_alone(doors, frozen, outcome, BindingEvidenceRefused("1" * 32, "2" * 32, False, "tips-disagree"))


@pytest.mark.parametrize("inspector", ["written", "other"])
def test_an_engine_refusal_to_inspect_at_step_8_is_an_evidence_refusal_that_keeps_the_orphan(tmp_path, inspector):
    """Ruling 6: at step 8 the marker may already be revealed, so the engine's
    refusal is recorded like any evidence refusal — `chain-malformed`, carrying
    the corpus id, the marker and `remotely_revealed` — and the attempt stays an
    orphan the next publish supersedes."""
    doors = Doors(tmp_path, others={"a-other": "e" * 32})
    opened = doors.open()
    seam = doors.seam(**{inspector: _raises_log_evidence})
    outcome = doors.bind(opened, remotely_revealed=True, seam=seam)
    _refused_alone(doors, opened, outcome, BindingEvidenceRefused("1" * 32, "2" * 32, True, "chain-malformed"))
