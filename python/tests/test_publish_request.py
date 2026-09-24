"""Step 0's pure pieces (publish-act-local design §4)."""

from __future__ import annotations

from dataclasses import replace

import pytest
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress
from beliefs.errors import MalformedRecord, PublicationRefused
from beliefs.intents.publish import Destination
from beliefs.profile import shipped_coordination
from beliefs.publish_request import (
    PublishRequest,
    Snapshot,
    closure_missing,
    decode_request,
    decode_snapshot,
    derive_pins,
    encode_request,
    encode_snapshot,
    require_usable,
    staging_world_id_for,
)

V2 = "coordination:" + shipped_coordination(2).content_identity
V1 = "coordination:" + shipped_coordination(1).content_identity
BASE_PIN = "science:" + "b" * 64
PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]
"""A dataset needs at least one accepted digest to mint an id (`test_audit.py`'s fixture)."""


class FakeView:
    """`get` and `resolve` over a dict; an alias maps to a live id."""

    def __init__(self, nodes, aliases=None):
        self._nodes = {n.id: n for n in nodes}
        self._aliases = aliases or {}

    def get(self, ref):
        return self._nodes[ref]

    def resolve(self, ref):
        ref = self._aliases.get(ref, ref)
        return ref if ref in self._nodes else None


def _run(name, produces=()):
    return stored.run_node(name, title=name, spec="s", produces=list(produces))


def test_a_complete_closure_misses_nothing():
    d = stored.dataset_node(title="d", resources=PINNED)
    r = _run("r", produces=[d.id])
    assert closure_missing(FakeView([d, r]), (d.id, r.id)) == ()


def test_an_unselected_relation_target_is_missing():
    d = stored.dataset_node(title="d", resources=PINNED)
    r = _run("r", produces=[d.id])
    assert closure_missing(FakeView([d, r]), (r.id,)) == (d.id,)


def test_closure_reads_both_endpoints_and_resolves_aliases():
    """Review Focus 1: a relation carried by its target names its source; an alias resolves first."""
    d = stored.dataset_node(title="d", resources=PINNED)
    r = _run("r")
    d.relations.append(Relation(source=r.id, predicate="produces", target=d.id))
    assert closure_missing(FakeView([d, r]), (d.id,)) == (r.id,)
    assert closure_missing(FakeView([d, r], aliases={"run:old": r.id}), (d.id, r.id)) == ()


def test_a_composite_missing_a_member_is_closure_incomplete():
    """The 2026-09-16 amendment: `composes` is a world relation, read by the one rule."""
    p1 = stored.proposition_node("p1", title="p1", claim={"terms": []})
    composite = stored.proposition_node("c", title="c", claim={"terms": []}).model_copy(update={"kind": "composite", "id": "composite:c"})
    composite.relations.append(Relation(source=composite.id, predicate="composes", target=p1.id))
    assert closure_missing(FakeView([p1, composite]), (composite.id,)) == (p1.id,)


def test_an_unresolvable_endpoint_is_missing_by_its_stored_spelling():
    r = _run("r", produces=["dataset:gone"])
    assert closure_missing(FakeView([r]), (r.id,)) == ("dataset:gone",)


def test_pins_union_domains_and_add_the_written_coordination_pin():
    derived = derive_pins(
        {"a" * 32: CorpusPins(BASE_PIN, {"biology": "biology:1"}), "b" * 32: CorpusPins(BASE_PIN, {})},
        CorpusPins(BASE_PIN, {"coordination": V2}),
    )
    assert derived == CorpusPins(BASE_PIN, {"biology": "biology:1", "coordination": V2})


@pytest.mark.parametrize(
    "manifests, written, reason, field",
    [
        ({"a" * 32: CorpusPins(BASE_PIN, {}), "b" * 32: CorpusPins("science:" + "c" * 64, {})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "science_contract"),
        ({"a" * 32: CorpusPins(BASE_PIN, {"biology": "biology:1"}), "b" * 32: CorpusPins(BASE_PIN, {"biology": "biology:2"})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "biology"),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins(BASE_PIN, {}), "coordination-unpinned", ""),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins(BASE_PIN, {"coordination": V1}), "coordination-unpinned", ""),
        ({"a" * 32: CorpusPins(BASE_PIN, {"coordination": V1})}, CorpusPins(BASE_PIN, {"coordination": V2}), "pins-disagree", "coordination"),
        ({"a" * 32: CorpusPins(BASE_PIN, {})}, CorpusPins("science:" + "c" * 64, {"coordination": V2}), "pins-disagree", "science_contract"),
    ],
    ids=["contract", "domain", "no-coordination", "v1-coordination", "coordination-disagrees", "written-contract"],
)
def test_pins_refusals(manifests, written, reason, field):
    with pytest.raises(PublicationRefused) as caught:
        derive_pins(manifests, written)
    assert caught.value.reason == reason and caught.value.field == field


def test_destination_checks(tmp_path):
    """Review Focus 2: every unusable destination refuses before the intent."""
    ops, dest, corpus = tmp_path / "ops", tmp_path / "dest", tmp_path / "corpus"
    for directory in (ops, dest, corpus):
        directory.mkdir()
    (tmp_path / "file").write_bytes(b"")
    (tmp_path / "link").symlink_to(dest)
    assert require_usable(ops, Destination.local(str(dest)), forbidden=(corpus,)) == (ops.resolve(), dest.resolve())
    # finding 4: a symlinked destination answers its resolved target, which step 0 freezes
    assert require_usable(ops, Destination.local(str(tmp_path / "link")), forbidden=(corpus,)) == (ops.resolve(), dest.resolve())
    for bad in (tmp_path / "missing", tmp_path / "file", ops, ops / "inner", corpus / "inner"):
        if bad == ops / "inner":
            bad.mkdir()
        if bad == corpus / "inner":
            bad.mkdir()
        with pytest.raises(PublicationRefused) as caught:
            require_usable(ops, Destination.local(str(bad)), forbidden=(corpus,))
        assert caught.value.reason == "destination-unusable", bad
    with pytest.raises(PublicationRefused) as caught:
        require_usable(dest / "ops-inside", Destination.local(str(dest)), forbidden=())
    assert caught.value.reason == "operations-root-unusable"
    with pytest.raises(PublicationRefused) as caught:
        require_usable(corpus, Destination.local(str(dest)), forbidden=(corpus,))
    assert caught.value.reason == "operations-root-unusable"


def _snapshot():
    d = stored.dataset_node(title="d", resources=PINNED)
    r = _run("r", produces=[d.id])
    records = tuple(sorted((n.id, node_to_markdown(n)) for n in (d, r)))
    return Snapshot("e" * 32, records)


def test_the_snapshot_round_trips_and_its_identity_is_stable():
    snapshot = _snapshot()
    assert decode_snapshot(encode_snapshot(snapshot)) == snapshot
    assert snapshot.identity() == decode_snapshot(encode_snapshot(snapshot)).identity()


def test_a_record_with_hand_edited_prose_is_accepted_and_round_trips():
    """`body` is hand-editable prose on world records (stored.py), outside the
    semantic hash; a snapshot record carrying one is not malformed."""
    d = stored.dataset_node(title="d", resources=PINNED)
    r = _run("r", produces=[d.id]).model_copy(update={"body": "A note."})
    assert node_from_markdown(node_to_markdown(r)).body == "A note."
    records = tuple(sorted((n.id, node_to_markdown(n)) for n in (d, r)))
    snapshot = Snapshot("e" * 32, records)
    assert decode_snapshot(encode_snapshot(snapshot)) == snapshot


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: replace(s, records=()),
        lambda s: replace(s, records=tuple(reversed(s.records))),
        lambda s: replace(s, records=(s.records[0], s.records[0])),
        lambda s: replace(s, records=((s.records[0][0], s.records[1][1]), s.records[1])),     # text is another id's
        # parses to the same id but is not the canonical rendering: an extra
        # space after `title:` is legal YAML and does not survive re-encoding
        lambda s: replace(s, records=((s.records[0][0], s.records[0][1].replace("\ntitle:", "\ntitle: ", 1)), s.records[1])),
        lambda s: replace(s, event_token="x"),
    ],
)
def test_a_malformed_snapshot_is_refused(mutate):
    with pytest.raises(MalformedRecord):
        mutate(_snapshot())


def test_a_non_canonical_snapshot_encoding_is_refused():
    with pytest.raises(MalformedRecord):
        decode_snapshot(encode_snapshot(_snapshot()) + b" ")


def _request(**changes):
    value = PublishRequest(
        event_token="e" * 32,
        view=CoordinationAddress("a" * 32, "b" * 32, "c" * 32),
        destination=Destination.local("/srv/published"),
        epoch="f" * 64,
        world_id="d" * 32,
        pins=CorpusPins(BASE_PIN, {"coordination": V2}),
        selection="0" * 64,
        staging_world_id=staging_world_id_for("e" * 32),
    )
    return replace(value, **changes) if changes else value


def test_the_request_round_trips():
    assert decode_request(encode_request(_request())) == _request()


@pytest.mark.parametrize(
    "changes",
    [
        {"event_token": "E" * 32},
        {"view": CoordinationAddress("a" * 32, "b" * 32)},       # unpinned
        {"epoch": "f" * 63},
        {"world_id": "d" * 31},
        {"selection": "0" * 63},
        {"staging_world_id": "1" * 32},                           # not the token's
    ],
)
def test_a_malformed_request_is_refused(changes):
    with pytest.raises(MalformedRecord):
        _request(**changes)


def test_staging_world_id_is_a_domain_separated_function_of_the_token():
    assert staging_world_id_for("e" * 32) == staging_world_id_for("e" * 32) != staging_world_id_for("f" * 32)
    assert len(staging_world_id_for("e" * 32)) == 32
