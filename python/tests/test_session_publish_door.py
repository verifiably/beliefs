"""The publish act's preview and, later, its session door (sharing design §2
decisions 7, 9 and 10, §4.7, §6 "The preview").

The preview section runs `publication_preview` over Task 5's published-source
world on the certified volume: it returns exactly what a subsequent `publish`
freezes, pins a subordinate view, refuses as the act refuses, and needs no
authority. Its v3 case reuses the attribution module's wrapper fixture."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from authority import FULL
from coordination_fixtures import EMPTY_QUERY, content_for, raw_coordination_node
from session_doors_fixture import KINDS, PUBLISHES, V2, Clock, publish_locally, published_source
from test_publication_attribution import wrapper_fixture

import beliefs.publish as act
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.errors import PublicationRefused
from beliefs.publish import PublicationPreview, Published, publication_preview
from beliefs.publish_request import decode_request, decode_snapshot
from beliefs.root import moment_seam, open_corpus, open_world, open_world_read
from beliefs.world import load_manifest

# --- the preview ------------------------------------------------------------------


def _preview(s: SimpleNamespace, view: CoordinationAddress) -> PublicationPreview:
    """The dry run through the read door: no permit at all."""
    return publication_preview(open_world_read(s.config), s.resolver, view, own_pins=load_manifest(s.written).profile)


def _act(s: SimpleNamespace, view: CoordinationAddress) -> object:
    """The local act over `view` under exactly the publication permit."""
    writer = open_corpus(s.written, authority=PUBLISHES, profile=V2, coordination_resolver=s.resolver)
    return act.publish(
        writer,
        s.resolver,
        open_world(s.config, authority=PUBLISHES),
        view=view,
        destination=s.destination,
        operations_root=s.ops,
        staging_profile=V2,
        clock=Clock(),
        seam=moment_seam(),
    )


def _mint(s: SimpleNamespace, kind: str, *, query: dict, project: CoordinationAddress | None = None):
    """A new coordination record in the written root, as its address pinned to its revision."""
    writer = open_corpus(s.written, authority=FULL, profile=V2, coordination_resolver=s.resolver)
    content = content_for(kind, query=query)
    if project is None:
        node = writer.mint_coordination(kind, content=content)
    else:
        node = writer.mint_coordination(kind, project=project, content=content)
    return coordination_revision(node).address.pinned(node.uid)


def _files(root: Path) -> list[tuple[Path, bytes]]:
    return sorted((p.relative_to(root), p.read_bytes()) for p in root.rglob("*") if p.is_file())


def test_the_preview_returns_what_publish_freezes(certified_work):
    s = published_source(certified_work)
    preview = _preview(s, s.view)
    published = publish_locally(s)
    op = s.ops / "publish" / published.event_token
    snapshot = decode_snapshot((op / "selection.v1").read_bytes())
    request = decode_request((op / "request.v1").read_bytes())
    assert (snapshot.records, snapshot.attributions) == (preview.records, preview.attributions)
    assert (request.epoch, request.world_id, request.pins, request.view) == (
        preview.epoch,
        preview.world_id,
        preview.pins,
        preview.view,
    )
    assert preview.view.unpinned() == s.view and preview.view.revision is not None
    assert preview.attributions is None  # the written root pins coordination v2
    assert preview.selected == tuple(address for address, _ in preview.records) != ()
    assert preview.contributing == (s.alpha_id,)


def test_the_preview_of_a_subordinate_view_pins_it(certified_work):
    """Review Focus 5: a question under the project previews pinned to its revision,
    and the act freezes that pinned subordinate view."""
    s = published_source(certified_work)
    question = _mint(s, "question", query=KINDS, project=s.view.unpinned())
    preview = _preview(s, question.unpinned())
    assert preview.view == question
    assert preview.view.local is not None and preview.view.revision is not None
    published = _act(s, question.unpinned())
    assert type(published) is Published
    request = decode_request((s.ops / "publish" / published.event_token / "request.v1").read_bytes())
    assert request.view == preview.view


@pytest.mark.parametrize("case", ["view-unresolved", "empty-selection"])
def test_the_preview_refuses_as_publish_does(certified_work, case):
    s = published_source(certified_work)
    view = CoordinationAddress("1" * 32) if case == "view-unresolved" else _mint(s, "project", query=EMPTY_QUERY)
    with pytest.raises(PublicationRefused) as previewed:
        _preview(s, view)
    with pytest.raises(PublicationRefused) as acted:
        _act(s, view)
    assert previewed.value.reason == acted.value.reason == case
    assert str(previewed.value) == str(acted.value)
    assert not (s.ops / "publish").exists()


def test_the_preview_needs_no_authority(certified_work):
    s = published_source(certified_work)
    before = _files(s.base)
    preview = _preview(s, s.view)
    assert type(preview) is PublicationPreview and preview.records
    assert not (s.ops / "publish").exists()
    assert _files(s.base) == before


def test_the_v3_preview_attributions_are_what_publish_freezes(tmp_path: Path, monkeypatch):
    """Ruling R4: under a v3 coordination pin the preview's attribution entries are the
    ones the act freezes into its snapshot (the attribution module's wrapper fixture,
    with the intent stood in and the steps after the freeze stopped)."""
    s = wrapper_fixture(tmp_path, monkeypatch, writer_version=3)
    token = "1" * 32
    frozen: list[Any] = []
    project = raw_coordination_node("project", "f" * 32, "d" * 32)  # the wrapper fixture's view

    def opening(writer, resolver, *, expected_view, **kwargs):
        return SimpleNamespace(intent=SimpleNamespace(event_token=token, view=expected_view))

    monkeypatch.setattr(act, "_open_publication", opening)
    monkeypatch.setattr(act, "_run", lambda attempt: frozen.append(attempt) or "stopped")
    resolver = SimpleNamespace(mounted=lambda: (s.writer.root,), resolve=lambda address: project)
    preview = publication_preview(
        cast(Any, s.world),
        cast(Any, resolver),
        coordination_revision(project).address,
        own_pins=load_manifest(s.writer.root).profile,
    )
    assert preview.attributions is not None and len(preview.attributions) == 2
    assert s.run() == "stopped"
    snapshot = decode_snapshot((s.ops / "publish" / token / "selection.v1").read_bytes())
    assert snapshot.attributions == preview.attributions == frozen[0].snapshot.attributions
    assert snapshot.records == preview.records
    assert (frozen[0].request.pins, frozen[0].request.epoch) == (preview.pins, preview.epoch)
