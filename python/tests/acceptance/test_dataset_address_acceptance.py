"""Cut 29: dataset ids derived from the content identity, over certified durable roots."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut4 import raw_write
from profiles import BASE
from test_world_receipts import hold_shipped
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.
from beliefs import relocation, stored
from beliefs.corpus import _forget_roots_under
from beliefs.errors import BasisMissing, CollisionRefused, DatasetAddressDisagreement, ImportRefused
from beliefs.permit import Authority, WritePermit
from beliefs.root import init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig, epoch

MOVE_FIELDS = {"observer": "o", "instrument": "i", "opened_at": "2026-09-14T00:00:00Z", "closed_at": "2026-09-14T00:00:01Z"}
CONSOLIDATE_FIELDS = {**MOVE_FIELDS, "rationale": "keep holds the authored record"}
OBSERVED = {"locator": "instrument:fixture", "attested_by": ACTOR}


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut29-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def handle(seed: str, node_id: str = "dataset:handle"):
    return stored.governed_node("dataset", node_id.partition(":")[2], seed, {stored.DATASET_FACET: {"resources": pinned(seed)}}, ())


# --- W2, the dataset arm ---------------------------------------------------------

def test_w2_two_corpora_mint_one_address_from_one_declaration_durably(durable_world):
    _, _, left = durable_world.corpus(BASE)
    _, beta, _ = durable_world.corpus(BASE)
    # A second attester: the observation facet names its writer's actor (plan review finding 3).
    right = open_corpus(beta, authority=Authority(WritePermit.full(), "other"), profile=BASE)
    a = left.add(stored.dataset_node(title="DepMap 24Q2", resources=pinned("depmap"), empirical_observation=OBSERVED))
    b = right.add(stored.dataset_node(title="depmap release", resources=pinned("depmap"), empirical_observation={**OBSERVED, "attested_by": "other"}))
    assert a.id == b.id == dataset_ref("depmap")
    assert stored.dataset_address_of(left.read_view.get(a.id)) == a.id


def test_w2_order_repetition_and_names_do_not_move_the_address_and_one_digest_does_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    x, y = pinned("x")[0], pinned("y")[0]
    one = stored.dataset_node(title="one", resources=[x, y])
    two = stored.dataset_node(title="two", resources=[y, {"name": "renamed", "digest": x["digest"]}, {"name": "copy", "digest": x["digest"]}])
    assert one.id == two.id
    assert stored.dataset_node(title="three", resources=[x, pinned("z")[0]]).id != one.id
    minted = writer.add(one)
    with pytest.raises(CollisionRefused):
        writer.add(two)
    assert writer.read_view.get(minted.id).title == "one"


def test_w2_the_producers_map_and_the_observes_closure_name_the_derived_address_durably(durable_world, scratch):
    a, alpha, left = durable_world.corpus(BASE)
    raw = left.add(stored.dataset_node(title="raw", resources=pinned("raw"), empirical_observation=OBSERVED))
    run = left.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[raw.id], transforms=[raw.id], produces=[dataset_ref("derived")]))
    left.add(stored.dataset_node(title="derived", resources=pinned("derived"), basis={"tag": "single", "routes": [{"run": run.id, "ancestor": raw.id, "transforms": [raw.id]}]}))
    config = WorldConfig(scratch / "world", "e" * 32, (alpha,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(alpha, provenance=Fresh())
    published = epoch.build_epoch(world, coverage=frozenset((a,)), bindings=hold_shipped(world))
    producers = {entry["dataset"]: list(entry["runs"]) for entry in published.documents["producers-map.yaml"]["producers"]}  # pyright: ignore[reportGeneralTypeIssues]
    assert producers == {dataset_ref("derived"): [run.id]}
    assert stored.inputs_of(left.read_view.get(run.id), stored.OBSERVES) == (dataset_ref("raw"),)


def test_w2_an_unaccepted_algorithm_has_no_address_at_the_builder_or_the_boundary_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    md5 = [{"name": "m", "digest": "md5:" + "0" * 32}]
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="md5", resources=md5)
    with pytest.raises(BasisMissing):
        writer.add(stored.governed_node("dataset", "md5", "md5", {stored.DATASET_FACET: {"resources": md5}}, ()))


# --- W3, the builder arm ---------------------------------------------------------

def test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="empty", resources=[])
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="half", resources=[*pinned("p"), {"name": "unpinned"}])
    minted = writer.add(stored.dataset_node(title="declared, held nowhere", resources=pinned("nowhere")))
    assert writer.read_view.holds(minted.id)


def test_w3_the_boundary_refuses_a_hand_built_unpinned_record_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    with pytest.raises(BasisMissing):
        writer.add(stored.governed_node("dataset", "d1", "d1", {stored.DATASET_FACET: {"resources": []}}, ()))
    assert not any(n.kind == "dataset" for n in writer.read_view.iter_stored())


# --- W8, the address conflict on datasets ---------------------------------------

def test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably(durable_world):
    _, alpha, left = durable_world.corpus(BASE)
    _, _, right = durable_world.corpus(BASE)
    bad = handle("h")
    with pytest.raises(DatasetAddressDisagreement):
        left.add(bad)
    with pytest.raises(ImportRefused) as caught:
        right.import_bundle([bad], **MOVE_FIELDS)
    assert caught.value.member == bad.id
    raw_write(alpha, bad)
    _forget_roots_under(alpha)
    left = open_corpus(alpha, authority=FULL, profile=BASE)
    with pytest.raises(DatasetAddressDisagreement):
        relocation.move(left, right, bad.id, **MOVE_FIELDS)
    assert not right.read_view.holds(bad.id)
    good = right.add(stored.dataset_node(title="h", resources=pinned("h")))
    assert good.id == dataset_ref("h")


def test_w8_consolidate_at_one_derived_address_gives_one_address_and_no_redirect_durably(durable_world):
    _, _, left = durable_world.corpus(BASE)
    _, _, right = durable_world.corpus(BASE)
    keep = left.add(stored.dataset_node(title="kept", resources=pinned("shared")))
    other = right.add(stored.dataset_node(title="other", resources=pinned("shared")))
    merged, _, _ = relocation.consolidate((left, keep.id), (right, other.id), **CONSOLIDATE_FIELDS)
    assert merged.id == keep.id == dataset_ref("shared")
    assert merged.deprecated_ids == []
    assert not right.read_view.holds(other.id)


@pytest.mark.parametrize("invalid", ["other", "keep"])
def test_w8_consolidate_judges_both_declarations_before_it_discards_one_durably(durable_world, invalid):
    _, alpha, left = durable_world.corpus(BASE)
    _, beta, _ = durable_world.corpus(BASE)
    valid = left.add(stored.dataset_node(title="kept", resources=pinned("shared")))
    raw = handle("different", node_id=valid.id)   # same id, different bytes: derives another address
    raw_write(beta, raw)
    _forget_roots_under(beta)
    right_reopened = open_corpus(beta, authority=FULL, profile=BASE)   # a fresh view sees the raw write
    keep, lose = (left, valid.id), (right_reopened, raw.id)
    if invalid == "keep":
        keep, lose = lose, keep

    def snapshot(root):
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(Path(root).rglob("*.md"))}

    before = (snapshot(alpha), snapshot(beta))
    with pytest.raises(DatasetAddressDisagreement) as caught:
        relocation.consolidate(keep, lose, **CONSOLIDATE_FIELDS)
    assert invalid in str(caught.value)
    assert (snapshot(alpha), snapshot(beta)) == before
