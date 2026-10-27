"""Cut 47: explicit ownership, full-capture veto and frozen own-only formats."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from nodes.core.frontmatter import node_to_markdown
from test_publication_attribution import capture_fixture, frozen_attempt, pin, wrapper_fixture

import beliefs.publish as act
from beliefs.errors import PublicationRefused
from beliefs.intents.publish import Destination
from beliefs.publication import MARKER_KIND, marker_record
from beliefs.world import ForkOf, Fresh, RegistryView, ReplicaOf

A, B, C = "a" * 32, "b" * 32, "c" * 32


class StringSubclass(str):
    pass


@pytest.mark.parametrize(
    "declaration,error",
    [
        ([], TypeError),
        ({A}, TypeError),
        (None, TypeError),
        (frozenset({1}), TypeError),
        (frozenset({StringSubclass(A)}), TypeError),
        (frozenset({A.upper()}), ValueError),
        (frozenset({"a" * 31}), ValueError),
        (frozenset({"a" * 33}), ValueError),
        (frozenset({A + "\n"}), ValueError),
        (frozenset({A, "unused-invalid"}), ValueError),
    ],
)
def test_y5_f_declaration_validation(declaration, error):
    resolver = SimpleNamespace(resolve=lambda *a: pytest.fail("resolved before validation"))
    with pytest.raises(error) as caught:
        act.publication_preview(
            cast(Any, None), cast(Any, resolver), cast(Any, None), own_pins=cast(Any, None), own_corpora=declaration
        )
    assert "own_corpora" in str(caught.value) and "unexpected keyword" not in str(caught.value)


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
def test_y17_q_owned_replica(version):
    read, registry, captures = capture_fixture({A: (ReplicaOf(A), ("run:a",))})
    captures[A] = captures[A][:-1]
    before = registry
    origins = act._selected_attributions(read, registry, ("run:a",), pin(version), own_corpora=frozenset({A}))
    assert origins == (None if version == 2 else ())
    assert registry == before and registry.admissions[0].provenance == ReplicaOf(A)
    assert read.corpus_of("run:a") == A


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
@pytest.mark.parametrize("declaration", [frozenset(), frozenset({C})])
def test_y17_r_explicit_scope(version, declaration):
    read, registry, captures = capture_fixture({A: (ReplicaOf(A), ("run:a",))})
    captures[A] = captures[A][:-1]
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read, registry, ("run:a",), pin(version), own_corpora=declaration)
    assert caught.value.reason == ("attribution-contract-unpinned" if version == 2 else "attribution-source-invalid")
    assert caught.value.corpus_ids == (A,)
    assert caught.value.field == ("" if version == 2 else "marker-absent")


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
@pytest.mark.parametrize("provenance", [Fresh(), ForkOf(A, "d" * 64), ReplicaOf(A)])
@pytest.mark.parametrize("malformed", [False, True])
def test_y17_s_captured_marker_veto(version, provenance, malformed):
    read, registry, captures = capture_fixture({A: (provenance, ("run:a",))})
    marker = captures[A][-1]
    assert marker.kind == MARKER_KIND and read.corpus_of(marker.id) is None
    if malformed:
        marker.facets.clear()
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read, registry, ("run:a",), pin(version), own_corpora=frozenset({A}))
    assert (caught.value.reason, caught.value.corpus_ids, caught.value.refs, caught.value.field) == (
        "attribution-own-source-invalid",
        (A,),
        ("run:a",),
        "marker-present",
    )


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
def test_y17_t_refusal_order(version):
    read, registry, captures = capture_fixture(
        {C: (ReplicaOf(C), ("run:c",)), B: (ReplicaOf(B), ("run:b",)), A: (ReplicaOf(A), ("run:a",))}
    )
    selected = ("run:c", "run:b", "run:a")
    own = frozenset({A, B, C})
    missing = RegistryView(tuple(r for r in registry.admissions if r.corpus_id != C), ())
    with pytest.raises(PublicationRefused) as caught:
        act._selected_attributions(read, missing, selected, pin(version), own_corpora=own)
    assert (caught.value.reason, caught.value.corpus_ids) == ("attribution-holder-unregistered", (C,))
    captures[C] = captures[C][:-1]
    for rows in (registry.admissions, tuple(reversed(registry.admissions))):
        with pytest.raises(PublicationRefused) as caught:
            act._selected_attributions(
                read, RegistryView(rows, ()), selected, pin(version), own_corpora=frozenset({A, B})
            )
        assert (caught.value.reason, caught.value.corpus_ids, caught.value.refs, caught.value.field) == (
            "attribution-own-source-invalid",
            (A,),
            ("run:a",),
            "marker-present",
        )


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
def test_y17_u_mixed_origins(version):
    origin = ("run:b", C, "d" * 32)
    read, registry, captures = capture_fixture(
        {A: (ReplicaOf(A), ("run:a",)), B: (ReplicaOf(B), ("run:b",))}, source_version=3, carried={B: (origin,)}
    )
    captures[A] = captures[A][:-1]
    if version == 2:
        with pytest.raises(PublicationRefused) as caught:
            act._selected_attributions(read, registry, ("run:a", "run:b"), pin(version), own_corpora=frozenset({A}))
        assert (caught.value.reason, caught.value.corpus_ids) == ("attribution-contract-unpinned", (B,))
    else:
        assert act._selected_attributions(
            read, registry, ("run:a", "run:b"), pin(version), own_corpora=frozenset({A})
        ) == (origin,)


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
def test_y17_v_preview_matches_freeze(tmp_path, monkeypatch, version):
    s = wrapper_fixture(tmp_path, monkeypatch, writer_version=version)
    for cid in (A, B):
        s.captures[cid] = s.captures[cid][:-1]
    own = frozenset({A, B})
    preview = act.publication_preview(
        s.world, s.resolver, s.view, own_pins=act.load_manifest(s.writer.root).profile, own_corpora=own
    )
    attempt = frozen_attempt(tmp_path, entries=None if version == 2 else (), coordination_pin=pin(version))
    monkeypatch.setattr(act, "_open_publication", lambda *a, **kw: attempt.opened)
    monkeypatch.setattr(act, "_run", lambda a: a)
    published = s.run(own_corpora=own)
    assert published.snapshot.records == preview.records
    assert published.snapshot.attributions == preview.attributions == (None if version == 2 else ())
    assert published.request.pins == preview.pins
    assert s.world.registry() == s.registry


@pytest.mark.parametrize("version", [2, 3], ids=["v2", "v3"])
@pytest.mark.parametrize(
    "destination",
    [Destination.local("/publication"), Destination.remote("https://remote.test/pub")],
    ids=["local", "remote-with-snapshot"],
)
def test_y17_x_frozen_owned_marker(tmp_path, monkeypatch, version, destination):
    entries = None if version == 2 else ()
    a = frozen_attempt(tmp_path, destination=destination, entries=entries, coordination_pin=pin(version))
    expected = marker_record(
        a.opened.intent,
        world_id=a.request.world_id,
        epoch=a.request.epoch,
        selection=tuple(ref for ref, _ in a.snapshot.records),
        attributions=entries,
    )
    for name in ("_selected_attributions", "open_world_view", "current_epoch", "load_manifest"):
        monkeypatch.setattr(act, name, lambda *a, **kw: pytest.fail("source read on recovery"))
    node = act._expected_marker(a)
    assert node_to_markdown(node) == node_to_markdown(expected)
    source = node.facets["coordination"]["published_from"]
    assert ("attributions" in source) == (version == 3)
    if version == 3:
        assert source["attributions"] == []


@pytest.mark.parametrize("scenario", ["marker", "missing", "pins", "closure"])
def test_ownership_refusals_before_intent(tmp_path, monkeypatch, scenario):
    s = wrapper_fixture(tmp_path, monkeypatch, writer_version=2, source_version=3 if scenario == "pins" else 2)
    before = tuple(s.writer.read_view.iter_stored())
    if scenario == "missing":
        s.world.registry = lambda: RegistryView((), ())
    if scenario == "closure":
        monkeypatch.setattr(act, "closure_missing", lambda *a: ("run:missing",))
    with pytest.raises(PublicationRefused) as caught:
        s.run(own_corpora=frozenset({A, B}))
    assert (
        caught.value.reason
        == {
            "marker": "attribution-own-source-invalid",
            "missing": "attribution-holder-unregistered",
            "pins": "pins-disagree",
            "closure": "closure-incomplete",
        }[scenario]
    )
    assert "intent" not in s.calls and list(s.ops.iterdir()) == []
    assert tuple(s.writer.read_view.iter_stored()) == before
