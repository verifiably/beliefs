"""The intent-position judgment (publication-records design §6, §11.1; row W17):
presence at a position is the chain's inventory at each root's bound, over a
fabricated `MomentSeam` whose states are plain tuples, plus one certified-volume
run through `root.moment_seam()` that agrees with the live tip rule."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterator
from itertools import count
from pathlib import Path

import pytest
from authority import FULL
from coordination_fixtures import content_for, coordination_profile
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.paths import path_for_node_id
from profiles import pins_for
from test_publish_intent import intent
from test_world_log_audit import chain, digest, genesis_entry, registration, settlement

from beliefs.coordination import Anchor, MomentSeam, PositionRefused, coordination_revision, standing_at
from beliefs.corpus import CoordinationResolver
from beliefs.profile import ProfileSpec
from beliefs.publication import BINDING_KIND, binding_address, binding_record, binding_uid
from beliefs.world.logmodel import AbsentView, ChainView, DefectView, MalformedView, WellFormedView

ABSENT = ("absent",)
WRITTEN_ID = "9" * 32
OTHER_ID = "7" * 32
ADDRESS = binding_address(intent().view, intent().destination)
TOKEN_A = "a" * 32
TOKEN_B = "b" * 32


def file_state(data: bytes) -> tuple[str, bytes]:
    return ("file", data)


def fake_seam(inspect_written: Callable[[Path], ChainView], inspect_other: Callable[[Path], ChainView]) -> MomentSeam:
    """States are plain tuples: `ABSENT`, or `("file", bytes)`."""
    return MomentSeam(
        inspect_written=inspect_written,
        inspect_other=inspect_other,
        absent_state=ABSENT,
        is_file=lambda state: type(state) is tuple and state[0] == "file",
        file_matches=lambda state, data: state == ("file", data),
    )


def creation(tx: str, path: str, data: bytes, *, committed: bool = True):
    """One create of `path` with `data`: `registration(entry_digest, txid, initial, final)` and its settlement."""
    reg = registration(digest(f"reg-{tx}"), tx, ((path, ABSENT),), ((path, file_state(data)),))
    return reg, settlement(digest(f"set-{tx}"), reg.digest, tx, committed=committed)


def seam_over(views: dict) -> MomentSeam:
    """Both inspectors answer from one fabricated view per root."""
    return fake_seam(views.__getitem__, views.__getitem__)


def revision_a() -> Node:
    return binding_record(intent(event_token=TOKEN_A, binding_tips=()), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)


def revision_b() -> Node:
    return binding_record(
        intent(event_token=TOKEN_B, binding_tips=(binding_uid(TOKEN_A),)), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64
    )


def place_file(root: Path, node: Node) -> tuple[str, bytes]:
    """Write `node`'s bytes at its address path under `root`; the relative path and the bytes."""
    path = path_for_node_id(node.id)
    data = node_to_markdown(node).encode()
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_bytes(data)
    return path, data


def _binding_file(root: Path) -> tuple[str, bytes]:
    return place_file(root, binding_record(intent(), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64))


def fake_root(tmp_path: Path, name: str = "w") -> Path:
    root = (tmp_path / name).resolve()
    root.mkdir()
    return root


def judge(root: Path, view, *, seam: MomentSeam | None = None, position: str | None = None):
    return standing_at(
        {root: WRITTEN_ID},
        ADDRESS,
        BINDING_KIND,
        written=root,
        position=view.tip if position is None else position,
        anchors=(),
        seam=seam_over({root: view}) if seam is None else seam,
    )


def refused(judged, reason: str) -> bool:
    return type(judged) is PositionRefused and judged.reason == reason


def uids(judged) -> tuple[str, ...]:
    assert type(judged) is tuple, judged
    return tuple(revision.node.uid for revision in judged)


def a_then_b(root: Path, *, b_committed: bool = True):
    """A created, then B (superseding A) created; both files on disk."""
    path_a, data_a = place_file(root, revision_a())
    path_b, data_b = place_file(root, revision_b())
    reg_a, set_a = creation("a", path_a, data_a)
    reg_b, set_b = creation("b", path_b, data_b, committed=b_committed)
    return (path_a, data_a, reg_a, set_a), (path_b, data_b, reg_b, set_b)


GENESIS = genesis_entry(b"g", label="standing-genesis")


# --- the inventory's replay ---------------------------------------------------


def test_a_first_publication_has_no_tips(tmp_path):
    root = fake_root(tmp_path)
    assert judge(root, chain(GENESIS)) == ()


def test_b_superseding_a_before_the_bound_leaves_b_the_one_tip(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (_, _, reg_b, set_b) = a_then_b(root)
    assert uids(judge(root, chain(GENESIS, reg_a, set_a, reg_b, set_b))) == (revision_b().uid,)


def test_a_rolled_back_b_leaves_a_standing_and_its_file_absent(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (path_b, _, reg_b, set_b) = a_then_b(root, b_committed=False)
    (root / path_b).unlink()  # the rollback removed what the effect created
    assert uids(judge(root, chain(GENESIS, reg_a, set_a, reg_b, set_b))) == (revision_a().uid,)


def test_a_file_whose_only_creating_registration_rolled_back_is_not_present_and_not_refused(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (_, _, reg_b, set_b) = a_then_b(root, b_committed=False)  # B's file left on disk
    assert uids(judge(root, chain(GENESIS, reg_a, set_a, reg_b, set_b))) == (revision_a().uid,)


def test_a_pending_creation_is_not_present_and_not_refused(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (_, _, reg_b, _) = a_then_b(root)
    assert uids(judge(root, chain(GENESIS, reg_a, set_a, reg_b))) == (revision_a().uid,)


def test_a_rolled_back_then_retried_creation_is_present_once(tmp_path):
    root = fake_root(tmp_path)
    path_a, data_a = place_file(root, revision_a())
    rolled, rolled_settled = creation("a-1", path_a, data_a, committed=False)
    retried, retried_settled = creation("a-2", path_a, data_a)
    judged = judge(root, chain(GENESIS, rolled, rolled_settled, retried, retried_settled))
    assert uids(judged) == (revision_a().uid,)


def test_b_committed_after_the_written_position_leaves_a_standing(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (_, _, reg_b, set_b) = a_then_b(root)
    view = chain(GENESIS, reg_a, set_a, reg_b, set_b)
    assert uids(judge(root, view, position=set_a.digest)) == (revision_a().uid,)


# --- the three per-revision refusals and the history rule ---------------------


def test_b_deleted_is_revision_missing_never_a_over_a(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (path_b, _, reg_b, set_b) = a_then_b(root)
    (root / path_b).unlink()
    assert refused(judge(root, chain(GENESIS, reg_a, set_a, reg_b, set_b)), "revision-missing")


def test_b_overwritten_is_revision_mismatch(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (path_b, _, reg_b, set_b) = a_then_b(root)
    (root / path_b).write_bytes(b"other bytes\n")
    assert refused(judge(root, chain(GENESIS, reg_a, set_a, reg_b, set_b)), "revision-mismatch")


def test_inventoried_bytes_that_are_no_revision_are_revision_malformed(tmp_path):
    root = fake_root(tmp_path)
    path_b = path_for_node_id(revision_b().id)
    (root / path_b).parent.mkdir(parents=True)
    (root / path_b).write_bytes(b"not a revision\n")
    reg_b, set_b = creation("b", path_b, b"not a revision\n")
    assert refused(judge(root, chain(GENESIS, reg_b, set_b)), "revision-malformed")


def test_a_committed_removal_of_an_inventoried_path_is_history_violated(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (path_b, data_b, reg_b, set_b) = a_then_b(root)
    (root / path_b).unlink()
    removal = registration(digest("reg-rm"), "rm", ((path_b, file_state(data_b)),), ((path_b, ABSENT),))
    view = chain(GENESIS, reg_a, set_a, reg_b, set_b, removal, settlement(digest("set-rm"), removal.digest, "rm", committed=True))
    assert refused(judge(root, view), "history-violated")


def test_a_committed_rewrite_of_an_inventoried_path_is_history_violated(tmp_path):
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (path_b, data_b, reg_b, set_b) = a_then_b(root)
    (root / path_b).write_bytes(b"rewritten\n")
    rewrite = registration(digest("reg-rw"), "rw", ((path_b, file_state(data_b)),), ((path_b, file_state(b"rewritten\n")),))
    view = chain(GENESIS, reg_a, set_a, reg_b, set_b, rewrite, settlement(digest("set-rw"), rewrite.digest, "rw", committed=True))
    assert refused(judge(root, view), "history-violated")


def test_a_first_committed_rewrite_of_an_unregistered_file_is_history_violated(tmp_path):
    root = fake_root(tmp_path)
    path, data = _binding_file(root)  # a real binding revision's bytes at its address path
    rewrite = registration(digest("reg-rw"), "rw", ((path, file_state(b"older\n")),), ((path, file_state(data)),))
    view = chain(genesis_entry(b"g", label="rw-genesis"), rewrite, settlement(digest("set-rw"), rewrite.digest, "rw", committed=True))
    judged = standing_at({root: WRITTEN_ID}, ADDRESS, BINDING_KIND, written=root, position=view.tip, anchors=(), seam=seam_over({root: view}))
    assert type(judged) is PositionRefused and judged.reason == "history-violated"


# --- files the chain does not account for -------------------------------------


def test_a_file_no_registration_creates_is_unregistered_revision(tmp_path):
    root = fake_root(tmp_path)
    place_file(root, revision_a())
    assert refused(judge(root, chain(GENESIS)), "unregistered-revision")


def test_an_unaccounted_file_whose_only_registration_rewrites_it_is_unregistered(tmp_path):
    root = fake_root(tmp_path)
    path, data = _binding_file(root)
    rewrite = registration(digest("reg-rw"), "rw", ((path, file_state(b"older\n")),), ((path, file_state(data)),))
    view = chain(genesis_entry(b"g", label="rw-genesis"), rewrite)  # never settled: outside the inventory
    judged = standing_at({root: WRITTEN_ID}, ADDRESS, BINDING_KIND, written=root, position=view.tip, anchors=(), seam=seam_over({root: view}))
    assert type(judged) is PositionRefused and judged.reason == "unregistered-revision"


def test_a_file_whose_registration_only_the_re_read_sees_is_classified_by_it(tmp_path):
    """Write-ahead (Task 0): a file seen on disk has its registration in any later
    read, so the re-read — not the first read — classifies it."""
    root = fake_root(tmp_path)
    (_, _, reg_a, set_a), (_, _, reg_b, _) = a_then_b(root)
    first, later = chain(GENESIS, reg_a, set_a), chain(GENESIS, reg_a, set_a, reg_b)
    reads = iter((first, later))
    seam = fake_seam(lambda _root: next(reads), lambda _root: pytest.fail("no other root"))
    assert uids(judge(root, first, seam=seam)) == (revision_a().uid,)


def test_a_re_read_that_is_not_well_formed_refuses(tmp_path):
    root = fake_root(tmp_path)
    place_file(root, revision_a())
    reads = iter((chain(GENESIS), AbsentView()))
    seam = fake_seam(lambda _root: next(reads), lambda _root: pytest.fail("no other root"))
    assert refused(judge(root, chain(GENESIS), seam=seam), "chain-malformed")


# --- bounds: positions, anchors, mounts, chains --------------------------------


def two_roots(tmp_path: Path):
    written, other = fake_root(tmp_path, "w"), fake_root(tmp_path, "o")
    (_, _, reg_a, set_a), (_, _, reg_b, set_b) = a_then_b(other)
    other_genesis = genesis_entry(b"o", label="other-genesis")
    views = {written: chain(GENESIS), other: chain(other_genesis, reg_a, set_a, reg_b, set_b)}
    return written, other, views, set_a


def judge_two(written: Path, other: Path, views: dict, anchor: Anchor, *, mounts: dict | None = None):
    return standing_at(
        {written: WRITTEN_ID, other: OTHER_ID} if mounts is None else mounts,
        ADDRESS,
        BINDING_KIND,
        written=written,
        position=views[written].tip,
        anchors=(anchor,),
        seam=seam_over(views),
    )


def test_an_other_root_is_bounded_by_its_anchor_not_its_live_head(tmp_path):
    written, other, views, set_a = two_roots(tmp_path)
    genesis = views[other].genesis.digest
    assert uids(judge_two(written, other, views, Anchor(OTHER_ID, genesis, set_a.digest))) == (revision_a().uid,)
    assert uids(judge_two(written, other, views, Anchor(OTHER_ID, genesis, views[other].tip))) == (revision_b().uid,)


def test_an_other_root_is_read_detached_and_the_written_root_registered(tmp_path):
    written, other, views, _ = two_roots(tmp_path)
    read: list[tuple[str, Path]] = []

    def reader(label: str):
        return lambda root: read.append((label, root)) or views[root]

    seam = fake_seam(reader("written"), reader("other"))
    standing_at(
        {written: WRITTEN_ID, other: OTHER_ID},
        ADDRESS,
        BINDING_KIND,
        written=written,
        position=views[written].tip,
        anchors=(Anchor(OTHER_ID, views[other].genesis.digest, views[other].tip),),
        seam=seam,
    )
    assert ("written", written) in read and ("other", other) in read
    assert ("written", other) not in read and ("other", written) not in read


def test_an_anchor_naming_another_genesis_is_anchor_unplaced(tmp_path):
    written, other, views, set_a = two_roots(tmp_path)
    assert refused(judge_two(written, other, views, Anchor(OTHER_ID, digest("elsewhere"), set_a.digest)), "anchor-unplaced")


def test_an_anchor_head_no_longer_in_the_chain_is_anchor_unplaced(tmp_path):
    written, other, views, _ = two_roots(tmp_path)
    assert refused(judge_two(written, other, views, Anchor(OTHER_ID, views[other].genesis.digest, digest("gone"))), "anchor-unplaced")


def test_a_position_that_is_no_entry_of_the_written_chain_is_anchor_unplaced(tmp_path):
    root = fake_root(tmp_path)
    assert refused(judge(root, chain(GENESIS), position=digest("nowhere")), "anchor-unplaced")


def test_an_absent_chain_is_chain_absent(tmp_path):
    root = fake_root(tmp_path)
    assert refused(judge(root, chain(GENESIS), seam=seam_over({root: AbsentView()})), "chain-absent")


def test_a_malformed_chain_is_chain_malformed(tmp_path):
    root = fake_root(tmp_path)
    malformed = MalformedView(DefectView("cycle", digest("x"), "a cycle"))
    assert refused(judge(root, chain(GENESIS), seam=seam_over({root: malformed})), "chain-malformed")


def test_an_extra_mounted_corpus_is_mounts_changed(tmp_path):
    written, other, views, set_a = two_roots(tmp_path)
    anchor = Anchor(OTHER_ID, views[other].genesis.digest, set_a.digest)
    extra = fake_root(tmp_path, "x")
    mounts = {written: WRITTEN_ID, other: OTHER_ID, extra: "5" * 32}
    assert refused(judge_two(written, other, views, anchor, mounts=mounts), "mounts-changed")


@pytest.mark.parametrize(
    "mounts",
    [
        pytest.param(lambda w, o: {w: WRITTEN_ID}, id="an-anchored-corpus-unmounted"),
        pytest.param(lambda w, o: {o: OTHER_ID}, id="the-written-root-unmounted"),
        pytest.param(lambda w, o: {w: WRITTEN_ID, o: WRITTEN_ID}, id="two-roots-one-corpus"),
        pytest.param(lambda w, o: {w: OTHER_ID, o: OTHER_ID}, id="the-written-corpus-anchored"),
    ],
)
def test_every_other_mount_set_is_mounts_changed(tmp_path, mounts):
    written, other, views, set_a = two_roots(tmp_path)
    anchor = Anchor(OTHER_ID, views[other].genesis.digest, set_a.digest)
    assert refused(judge_two(written, other, views, anchor, mounts=mounts(written, other)), "mounts-changed")


def test_unequal_copies_of_one_revision_across_mounts_are_revision_mismatch(tmp_path):
    written, other = fake_root(tmp_path, "w"), fake_root(tmp_path, "o")
    path, data = place_file(written, revision_a())
    other_copy = binding_record(
        intent(event_token=TOKEN_A, binding_tips=(), at="2026-09-23T00:00:00Z"), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64
    )
    other_path, other_data = place_file(other, other_copy)
    assert other_path == path and other_data != data
    reg_w, set_w = creation("w", path, data)
    reg_o, set_o = creation("o", other_path, other_data)
    views = {written: chain(GENESIS, reg_w, set_w), other: chain(genesis_entry(b"o", label="o"), reg_o, set_o)}
    anchor = Anchor(OTHER_ID, views[other].genesis.digest, views[other].tip)
    assert refused(judge_two(written, other, views, anchor), "revision-mismatch")


# --- the production seam, over real roots on the certified volume -------------

_counter = count()


@pytest.fixture()
def coordination_pair(certified_work) -> Iterator[tuple[tuple[Path, Path], ProfileSpec]]:
    """Two registered coordination roots, created the way the acceptance
    tree's `durable_coordination_roots` creates its pair."""
    from beliefs.root import init_corpus_root, metadata_root_for, open_corpus

    profile = coordination_profile(None)
    # Resolved: the engine opens roots with no symlink in the path (ELOOP otherwise).
    roots = tuple((certified_work / f"standing-{os.getpid()}-{next(_counter)}-{side}").resolve() for side in ("left", "right"))
    try:
        for root in roots:
            init_corpus_root(root, authority=FULL)
            open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
        yield roots, profile
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def test_the_judgment_agrees_with_the_live_tip_rule_when_nothing_moved(coordination_pair):
    from beliefs.root import moment_seam, open_corpus

    (left, right), profile = coordination_pair
    resolver = CoordinationResolver({left: profile, right: profile})
    first, second = (open_corpus(root, authority=FULL, coordination_resolver=resolver, profile=profile) for root in (left, right))
    project = first.mint_coordination("project", content=content_for("project"))
    task = first.mint_coordination("task", project=coordination_revision(project).address, content=content_for("task"))
    address = coordination_revision(task).address
    revised = second.revise_coordination("task", address, predecessors=(task.uid,), content=content_for("task", name="next"))

    seam = moment_seam()
    mounted = resolver.mounted()
    assert tuple(mounted) == (left, right)
    written_view, other_view = seam.inspect_written(left), seam.inspect_other(right)
    assert type(written_view) is WellFormedView and type(other_view) is WellFormedView
    judged = standing_at(
        mounted,
        address,
        "task",
        written=left,
        position=written_view.tip,
        anchors=(Anchor(mounted[right], other_view.genesis.digest, other_view.tip),),
        seam=seam,
    )
    assert judged == resolver.tips(address)
    assert uids(judged) == (revised.uid,)
    # bounded before the other root's revision, the minted task stands alone
    before = standing_at(
        mounted,
        address,
        "task",
        written=left,
        position=written_view.tip,
        anchors=(Anchor(mounted[right], other_view.genesis.digest, other_view.genesis.digest),),
        seam=seam,
    )
    assert uids(before) == (task.uid,)
