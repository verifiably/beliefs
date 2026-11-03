"""World epoch publication, reading and recovery through the shipped derivation rules.

The portable journey walks one world end to end; the durable tests run on the certified tuple.
"""

from __future__ import annotations

import dataclasses
import os
import shutil
from itertools import count
from pathlib import Path

import pytest
import test_world_build
from atoms.chain.model import RegisteredEntry
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut6 import PINS
from nodes.core.corpus import Corpus
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY
from test_durable_families import chain_entries
from test_world_build import ALPHA, BETA, SYMBOL_KINDS, corpus_at, genesis_of, sample_nodes, tip_of
from test_world_read import RETIRED, linked_nodes
from test_world_receipts import corpora, document, publish, world_over

from beliefs import root, stored
from beliefs.errors import EpochCurrent, EpochUnknown
from beliefs.world import derive, epoch, read, registry, rules

_COUNTER = count()


def shipped_bindings(world: registry.World, *, retraction: str = "v2") -> epoch.DerivationBindings:
    """Hold this package's shipped rules in `world` and name one per kind as one
    build input; `retraction` picks the retraction-enumeration version."""
    root.install_shipped_world_rules(world)
    wanted = test_world_build.RETRACTION_VERSIONS[retraction]
    held = {
        SYMBOL_KINDS[bundle.symbol]: rules.binding_for(bundle)
        for bundle in rules.shipped_rule_bundles()
        if SYMBOL_KINDS[bundle.symbol] != "retraction-enumeration" or bundle.input_version == wanted
    }
    return epoch.DerivationBindings(
        producer=held["producer"],
        retraction=held["retraction-enumeration"],
        certification=held["certification-enumeration"],
        coreference=held["coreference-reduction"],
    )


# --- the witness for the relocated head --------------------------------------


class ContentHeads:
    """A chain-head callback that answers for a *corpus* with its present state.

    A real chain tip moves when a corpus commits, and that is the whole content
    of "the head and the state describe one view". The portable `ChainHeads`
    stub in `test_world_build` answers with a constant derived from the root's
    name, so it cannot see a corpus move at all — which is precisely why a test
    resting on it would pass under a relocated head that read a moved corpus.
    Here the corpus roots answer with `corpus_state_identity`, so the anchored
    head is comparable with the captured state, and the world root keeps the
    constant because it is not a corpus.

    The constant is `test_world_build`'s stand-in digest rather than a
    `genesis:<name>` label: publication mints registry log-head records from
    these values, and those validate the 64-character lowercase hexadecimal
    form a chain digest actually has.
    """

    def __init__(self, corpus_roots: tuple[Path, ...]) -> None:
        self.corpus_roots = {path.resolve() for path in corpus_roots}

    def __call__(self, target: Path) -> tuple[str, str]:
        target = Path(target).resolve()
        if target in self.corpus_roots:
            return (genesis_of(target), registry.corpus_state_identity(target))
        return (genesis_of(target), tip_of(target))


def test_anchored_head_describes_the_captured_corpus_view(tmp_path):
    """The head an epoch anchors is the head of the corpus whose state it captured.

    Not a declared check — the **witness** the head/state check is
    measured against. It observes nothing about locks: it compares the anchored
    head with the captured corpus state, which is what "one view" means at the
    published-artifact level. A head captured outside the hold still reads the
    same chain when nothing wrote in between, so this passes under relocation
    alone; it fails the moment a write is interposed, which is the interleaving
    a faulty implementation would have to carry.
    """
    corpus_root = corpus_at(tmp_path / "alpha", ALPHA, sample_nodes())
    world = registry.World(
        registry.WorldConfig(tmp_path / "world", "f" * 32, (corpus_root,)),
        DefaultExecutor,
        chain_head=ContentHeads((corpus_root,)),
        corpus_executor_factory=DefaultExecutor,
        authority=FULL,
    )
    world.admit(corpus_root, provenance=registry.Fresh())
    bindings = shipped_bindings(world)

    published = epoch.build_epoch(world, coverage=frozenset({ALPHA}), bindings=bindings)

    (anchor,) = published.anchors
    assert anchor.subject == ALPHA
    assert anchor.head_digest == dict(published.coverage)[ALPHA]
    assert published.world_anchor.subject == world.config.world_id


# --- the portable journey -----------------------------------------------------
#
# One world, walked end to end with the portable executor: the four shipped
# rules explicitly held, two corpora admitted, two epochs published, both read
# back, all four receipts validated, every case of the resolution union and every
# edge state this journey can reach exercised, and then the two severing acts.
#
# It asserts nothing about crashes. Durability is the certified tuple's subject
# and it is claimed below, by tests that read the engine's own chain; what these
# tests claim is that the acts of the slice compose — that the epoch a build
# published is the epoch `current` selects, that the receipts it carries resolve
# against the store the build read them from, and that removing one of those
# inputs is reported rather than discovered later as an unresolvable receipt.


DERIVATION_KINDS: tuple[derive.ReceiptKind, ...] = (
    "producer",
    "retraction-enumeration",
    "certification-enumeration",
    "coreference-reduction",
)
"""The four kinds, spelled as the literal type `validate_receipt` takes.

`epoch.DERIVATION_KINDS` is the same four as plain text, and
`test_the_receipt_kinds_walked_here_are_the_four_the_carrier_declares` pins the
two equal. They are written out rather than cast because a cast would make a
fifth kind — or a renamed one — a runtime surprise instead of a type error.
"""


@dataclasses.dataclass(frozen=True)
class Journey:
    """One walked world: its corpora, its build input, and its two epochs.

    `superseded` is the first publication, still retained and still openable by
    identity; `current` is the second, which the pointer names. Two are needed
    rather than one because the two acts at the end of the walk are about the
    difference: an epoch may be deleted only when it is not the current one, and
    a sever report is a statement about what the *other* retained epochs still
    carry.
    """

    world: registry.World
    roots: dict[str, Path]
    bindings: epoch.DerivationBindings
    superseded: epoch.Epoch
    current: epoch.Epoch


def journey_corpora(tmp_path: Path) -> dict[str, Path]:
    """Two corpora: one carrying a retired address, both carrying linked datasets.

    Stored attestations link each dataset chain for the shipped coreference
    rule, and the retired address is what makes `NotPresent` distinguishable
    from `Unknown` — the epoch records a `deprecated_ids` entry exactly as it
    records a live one, so the address survives its corpus going away. Exactly
    one corpus carries it: `derive.address_map` refuses a repeated address even
    when the two claims agree.
    """
    withdrawn = stored.dataset_node(title="dataset a successor", resources=pinned("a-successor"))
    return corpora(
        tmp_path,
        {
            ALPHA: (*linked_nodes("a"), withdrawn.model_copy(update={"deprecated_ids": [RETIRED]})),
            BETA: linked_nodes("b"),
        },
        prefix="journey",
    )


@pytest.fixture()
def journey(tmp_path) -> Journey:
    """The whole build path, run for real, before any test asserts anything.

    The four shipped rules are held by the composition root's own explicit
    act. The shipped coreference rule reduces the stored attestations above,
    reaching an active edge without a test-only implementation.
    """
    roots = journey_corpora(tmp_path)
    world = world_over(tmp_path, roots, name="journey-world")
    bindings = shipped_bindings(world)
    superseded = publish(world, (ALPHA, BETA), bindings)
    _extra_record(roots[BETA], "b-later")
    current = publish(world, (ALPHA, BETA), bindings)
    assert current.packaging_identity != superseded.packaging_identity
    return Journey(world, roots, bindings, superseded, current)


def test_the_receipt_kinds_walked_here_are_the_four_the_carrier_declares():
    assert DERIVATION_KINDS == epoch.DERIVATION_KINDS


def test_a_published_epoch_opens_by_identity_and_through_current(journey: Journey):
    """Both ways in, and they reach the same bytes.

    Opening by identity is a question about one carrier; opening through
    `current` is a question about the pointer *and* that carrier. A world where
    the two disagreed would publish one epoch and serve another, so the two
    routes are asserted to land on the same eleven members rather than merely on
    the same name.
    """
    by_identity = read.open_epoch(journey.world, journey.current.packaging_identity)
    through_current = read.current_epoch(journey.world)
    assert by_identity.packaging_identity == journey.current.packaging_identity
    assert through_current.packaging_identity == journey.current.packaging_identity
    assert dict(by_identity.members) == dict(through_current.members)
    assert set(by_identity.members) == set(epoch.EPOCH_MEMBERS)
    assert epoch.packaging_identity_of(by_identity.members) == by_identity.packaging_identity

    # The superseded epoch is retained, not overwritten: publication replaces a
    # pointer and nothing else.
    earlier = read.open_epoch(journey.world, journey.superseded.packaging_identity)
    assert earlier.packaging_identity == journey.superseded.packaging_identity
    assert earlier.packaging_identity != through_current.packaging_identity

    with pytest.raises(EpochUnknown):
        read.open_epoch(journey.world, "0" * 64)


def test_all_four_receipts_validate_against_the_world_that_published_them(journey: Journey):
    """Nothing has moved since capture, so every receipt rebuilds to its subject.

    This is the baseline the two severing tests below are read against: a
    ``validated`` receipt is one whose exact pair is still held here and whose
    named corpora still stand where they stood, re-derived and compared byte for
    byte. A test that only ever saw a broken receipt would not know which half
    of that the break was.
    """
    outcomes = {kind: read.validate_receipt(journey.world, journey.current, kind) for kind in DERIVATION_KINDS}
    assert len(outcomes) == 4
    for kind, outcome in outcomes.items():
        assert outcome.kind == kind
        assert outcome.outcome == "validated", (kind, outcome.detail)
        assert outcome.validated


def test_resolution_answers_resolved_not_present_and_unknown(journey: Journey):
    """The three resolution cases, all three from one publication.

    The line between `NotPresent` and `Unknown` is what the epoch recorded and
    never what is here now, so both are taken against the *same* epoch: one
    address it recorded whose corpus has stopped being carried, and one address
    it never observed at all.
    """
    addresses = {
        entry["address"]: (entry["holders"][0], entry["uid"])
        for entry in document(journey.current, "address-map.yaml")["addresses"]
    }
    stamp = read.BoundStamp(journey.current.packaging_identity, journey.current.coverage)

    resolved = read.resolve_address(journey.world, journey.current, dataset_ref("a"))
    assert isinstance(resolved, read.Resolved)
    assert resolved.location == read.Location(*addresses[dataset_ref("a")], (addresses[dataset_ref("a")][0],))
    assert resolved.stamp == stamp

    # A retired address is a recorded one, and resolves to its successor's uid.
    retired = read.resolve_address(journey.world, journey.current, RETIRED)
    assert isinstance(retired, read.Resolved)
    assert retired.location == read.Location(*addresses[RETIRED], (addresses[RETIRED][0],))

    unknown = read.resolve_address(journey.world, journey.current, "dataset:never-observed")
    assert isinstance(unknown, read.Unknown)
    assert unknown.stamp == stamp

    # Now BETA stops answering to its `corpus_id`. The epoch still records what
    # it carried, so those addresses are absent rather than unknown.
    (journey.roots[BETA] / "corpus.yaml").unlink()
    absent = read.resolve_address(journey.world, journey.current, dataset_ref("b"))
    assert isinstance(absent, read.NotPresent)
    assert absent.stamp == stamp
    assert isinstance(read.resolve_address(journey.world, journey.current, dataset_ref("a")), read.Resolved)
    assert isinstance(read.resolve_address(journey.world, journey.current, "dataset:never-observed"), read.Unknown)


def test_edges_answer_active_inactive_and_indeterminate(journey: Journey):
    """The three edge states, and the expansion that refuses rather than guess.

    `active` and `inactive` come from the stored balance of a reduction this
    world can still stand behind. `indeterminate` is reached here through the
    coverage half — a live corpus the publication never observed — and
    through the receipt half in the removal test below, which is the other input
    the section names.
    """
    assert read.EDGE_STATES == ("active", "inactive", "indeterminate")

    active = read.coreference_edge(journey.world, journey.current, dataset_ref("a"), dataset_ref("a-b"))
    assert active.state == "active"
    assert active.missing_coverage == () and active.receipt_outcome is None

    # A pair the reduction never recorded is established `inactive`, not unknown.
    inactive = read.coreference_edge(journey.world, journey.current, dataset_ref("a-b"), dataset_ref("a-c"))
    assert inactive.state == "inactive"
    assert read.expand_coreference(journey.world, journey.current, dataset_ref("a")) == (
        dataset_ref("a-b"),
        dataset_ref("a-c"),
    )

    # An epoch over ALPHA alone did not observe BETA, which is live here.
    narrow = publish(journey.world, (ALPHA,), journey.bindings)
    narrowed = read.coreference_edge(journey.world, narrow, dataset_ref("a"), dataset_ref("a-b"))
    assert narrowed.state == "indeterminate"
    assert narrowed.missing_coverage == (BETA,)
    assert narrowed.receipt_outcome is None
    with pytest.raises(read.EdgeIndeterminate) as refusal:
        read.expand_coreference(journey.world, narrow, dataset_ref("a"))
    assert refusal.value.missing_coverage == (BETA,)


def test_removing_a_binding_reports_the_receipts_it_severed(journey: Journey):
    """The removal names what lost this store's resolution path.

    Both retained epochs carry a coreference receipt naming the removed pair, so
    both identities are severed, and the report is the *only* place that is said
    — after the act, the receipts are simply ``unresolvable`` and nothing
    remains to say what made them so.
    """
    severed_here = set()
    for published in (journey.superseded, journey.current):
        identity = published.receipts["coreference-receipt.yaml"].identity
        assert identity is not None
        severed_here.add(identity)

    report = rules.remove_rule_binding(journey.world, journey.bindings.coreference)
    assert report.binding == journey.bindings.coreference
    assert set(report.severed_receipts) == severed_here
    assert report.severed_receipts == tuple(sorted(severed_here))

    # The consequence the report predicted, now observable.
    outcome = read.validate_receipt(journey.world, journey.current, "coreference-reduction")
    assert outcome.outcome == "unresolvable"
    answer = read.coreference_edge(journey.world, journey.current, dataset_ref("a"), dataset_ref("a-b"))
    assert answer.state == "indeterminate"
    assert answer.receipt_outcome == "unresolvable"
    assert answer.missing_coverage == ()
    with pytest.raises(read.EdgeIndeterminate) as refusal:
        read.expand_coreference(journey.world, journey.current, dataset_ref("a"))
    assert refusal.value.receipt_outcome == "unresolvable"

    # The three receipts whose pairs are still held are untouched: removal is
    # the inverse of one installation and nothing wider.
    for kind in ("producer", "retraction-enumeration", "certification-enumeration"):
        still = read.validate_receipt(journey.world, journey.current, kind)
        assert still.outcome == "validated", (kind, still.detail)


def _receipt_identities(published: epoch.Epoch) -> set[str]:
    """The four receipt identities one epoch carries, read off its carriers."""
    identities = set()
    for member in sorted(epoch.RECEIPT_KINDS):
        identity = published.receipts[member].identity
        assert identity is not None, member
        identities.add(identity)
    assert len(identities) == 4
    return identities


def _snapshot_identity(published: epoch.Epoch) -> str:
    """The fifth identity: the producer snapshot's own subject identity.

    Taken from the producer receipt's `subject`, which is what digests the
    projection — not from the receipt's identity, which digests the capture as
    well and therefore moves whenever any covered corpus does.
    """
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    return subject


def test_deleting_a_noncurrent_epoch_reports_the_identities_it_severed(journey: Journey):
    """The current epoch is undeletable, and the other one reports both answers.

    The record added between the two publications is a plain dataset, so it
    moved BETA's corpus state and changed no `produces` edge. That splits the
    report exactly along the line that separates them. All four receipt identities digest
    the captured `corpus_states`, so all four are severed — including the
    *producer receipt*. The *producer snapshot* identity digests the projection
    instead, the projection did not move, and the current epoch still carries
    it: `retained_elsewhere`, and not severed.

    Both answers in one report is the point. A fixture where everything severed
    would leave the flag asserted in one direction only, which is how a report
    that always said `False` would go unnoticed.
    """
    with pytest.raises(EpochCurrent):
        epoch.delete_epoch(journey.world, journey.current.packaging_identity)

    report = epoch.delete_epoch(journey.world, journey.superseded.packaging_identity)
    assert report.actor == ACTOR
    assert report.packaging_identity == journey.superseded.packaging_identity
    assert report.snapshot is not None
    assert report.snapshot.subject == epoch.SNAPSHOT_SUBJECT
    assert report.snapshot.retained_elsewhere is True
    assert report.snapshot.identity == _snapshot_identity(journey.current)

    assert {entry.subject for entry in report.receipts} == set(DERIVATION_KINDS)
    assert not any(entry.retained_elsewhere for entry in report.receipts)
    severed_receipts = {entry.identity for entry in report.receipts}
    assert severed_receipts == _receipt_identities(journey.superseded)
    assert severed_receipts.isdisjoint(_receipt_identities(journey.current))
    assert report.severed == tuple(sorted(severed_receipts))

    # Deleted whole, and the pointer is untouched.
    with pytest.raises(EpochUnknown):
        read.open_epoch(journey.world, journey.superseded.packaging_identity)
    assert read.current_epoch(journey.world).packaging_identity == journey.current.packaging_identity


# --- the certified tuple ------------------------------------------------------


@pytest.fixture()
def durable_world(work_directory):
    """One registered world root and one registered corpus root, on the tuple.

    Everything is the composition root's own product: `init_world_root` and
    `init_corpus_root` reach the engine's volume binding, so an uncertified
    tuple fails here rather than inside an assertion, and the executor the
    world writes with is `DurableExecutor` rather than the portable one.
    """
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = work_directory / f"world-{suffix}"
    corpus_root = work_directory / f"corpus-{suffix}"
    config = registry.WorldConfig(world_root, "7" * 32, (corpus_root,))
    try:
        root.init_world_root(config, authority=FULL)
        root.init_corpus_root(corpus_root, authority=FULL)
        root.open_corpus(corpus_root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
        # Stored records are placed with the `nodes` handle, exactly as the
        # portable fixtures place them: what these tests assert is committed
        # evidence of *world-root* transactions, and the admission gate the
        # write API applies to a dataset is another slice's subject.
        for node in sample_nodes():
            Corpus(corpus_root).add(node)
        corpus_id = registry.load_manifest(corpus_root).corpus_id
        world = root.open_world(config, authority=FULL)
        world.admit(corpus_root, provenance=registry.Fresh())
        yield {
            "world": world,
            "config": config,
            "world_root": world_root,
            "corpus_root": corpus_root,
            "corpus_id": corpus_id,
        }
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(world_root), ignore_errors=True)
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(corpus_root), ignore_errors=True)


def _registrations(entries) -> tuple[RegisteredEntry, ...]:
    return tuple(entry for _digest, entry in entries if isinstance(entry, RegisteredEntry))


def _extra_record(corpus_root: Path, seed: str) -> None:
    """Move the corpus, so the next build has a different epoch to publish."""
    Corpus(corpus_root).add(stored.dataset_node(title=f"dataset {seed}", resources=pinned(seed)))


def _target_identity(world, corpus_id: str, bindings: epoch.DerivationBindings) -> str:
    """The packaging identity the next build of this coverage would publish.

    Pure: a capture and a derivation, and no transaction. It is computed before
    each killed attempt so the attempt can be judged against a name rather than
    against whatever it happened to leave behind.
    """
    draft = epoch._capture_build_inputs(world, coverage=frozenset({corpus_id}), bindings=bindings.by_kind())
    return epoch.packaging_identity_of(epoch._derived_members(draft))


class Killed(Exception):
    """The writer, killed at one Science-observable stage boundary."""


def _killer(stage: str):
    def kill(*_args, **_keywords):
        raise Killed(stage)

    return kill


PUBLICATION_STAGES = (
    "capture",
    "derive",
    "recheck",
    "plan",
    "pre-commit",
    "second-transaction",
    "post-commit",
    "read-back",
)
"""Every Science-observable boundary of one publication, in the order the publication
crosses them.

The requirement is to kill the writer at every stage of publication, narrowed:
the stages *inside* the transaction
belong to the engine's certified recovery and are not Science-observable, so
"every stage" resolves to these eight — the four pure phases, the two sides of
the single commit, the read-back, and `second-transaction`, which under a
correct publication never happens at all and is how "one transaction" is
observed rather than assumed.
"""


def _attempt(case, bindings, stage: str, standing: str, attempted: list[str]) -> str:
    """Kill one publication at `stage`, then re-enter through the barrier."""
    attempted.append(stage)
    world, config = case["world"], case["config"]
    target = _target_identity(world, case["corpus_id"], bindings)
    calls: list[int] = []
    execute = root.DurableExecutor.execute

    def counted(self, plan):
        calls.append(len(plan))
        if stage == "pre-commit":
            raise Killed(stage)
        if stage == "second-transaction" and len(calls) > 1:
            raise Killed(stage)
        applied = execute(self, plan)
        if stage == "post-commit":
            raise Killed(stage)
        return applied

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(root.DurableExecutor, "execute", counted)
        for name, seam in (
            ("capture", "_capture_build_inputs"),
            ("derive", "_derived_members"),
            ("recheck", "_locked_recheck_rule_bindings"),
            ("plan", "_locked_publication_plan"),
            ("read-back", "_locked_open_epoch"),
        ):
            if stage == name:
                patch.setattr(epoch, seam, _killer(stage))
        try:
            epoch.build_epoch(world, coverage=frozenset({case["corpus_id"]}), bindings=bindings)
        except Killed:
            pass

    assert len(calls) <= 1, (
        f"{stage}: publication submitted {len(calls)} transactions; publication is one transaction, and a "
        "kill between two of them is exactly how `current` comes to name incomplete content"
    )
    # A fresh world, so the barrier is crossed by an act that did not survive
    # the killed one's process state.
    selected = read.current_epoch(root.open_world(config, authority=FULL))
    assert selected.packaging_identity in {standing, target}, stage
    assert set(selected.members) == set(epoch.EPOCH_MEMBERS), stage
    assert epoch.packaging_identity_of(selected.members) == selected.packaging_identity, stage
    return selected.packaging_identity


def test_recovery_barrier_never_selects_partial_epoch(durable_world):
    """`current` names the prior epoch or the new, complete one — never else.

    The writer is killed at every Science-observable stage boundary of the
    one-transaction write, and after each kill a **fresh** world crosses the
    recovery barrier and follows `current`. The answer is always a complete
    epoch: the prior one where the kill preceded the commit, and the new one
    where a committed transaction rolled forward. Nothing is ever missing and
    nothing ever names incomplete content.

    The intra-transaction stages are not exercised and are not claimed: they
    belong to the engine's certified recovery and Science cannot observe them
    (a known limitation). What *is* claimed here about the transaction is
    that there is one of it — `second-transaction` kills the second commit, and
    a correct publication never reaches it.
    """
    case = durable_world
    bindings = shipped_bindings(case["world"])
    first = epoch.build_epoch(case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings)
    assert read.current_epoch(case["world"]).packaging_identity == first.packaging_identity

    _extra_record(case["corpus_root"], "before-the-commit-side")
    standing = first.packaging_identity
    attempted: list[str] = []
    for stage in ("capture", "derive", "recheck", "plan", "pre-commit", "second-transaction"):
        standing = _attempt(case, bindings, stage, standing, attempted)
    assert standing != first.packaging_identity, (
        "`second-transaction` never fired, so the publication that followed it published nothing "
        "and the commit-side stages below would be exact rebuilds"
    )

    # The commit-side kills need a target this world does not already hold, or
    # they would fire against an empty plan and observe nothing.
    _extra_record(case["corpus_root"], "after-the-commit-side")
    for stage in ("post-commit", "read-back"):
        standing = _attempt(case, bindings, stage, standing, attempted)

    # Every boundary was actually killed at, in order. A stage silently dropped
    # from one of the two loops above is a boundary this test claims to cover and
    # does not, which nothing else here would notice.
    assert tuple(attempted) == PUBLICATION_STAGES


def test_publication_registration_names_epoch_and_current(durable_world):
    """The publication transaction commits an entry naming every member and `current`.

    Decoded from the engine-owned chain, not from the write plan: what is being
    asserted is that the committed record of the act names the paths it wrote,
    which is the durable half of "one transaction" and the only crash-atomicity
    evidence claimed here.

    Both shapes are exercised. The first publication *creates* the pointer; the
    second *replaces* it, and both entries name the eleven members of their own
    epoch alongside it.

    The build-origin log-head record joins the same transaction
    so the committed entry names one
    `registry/` path per covered corpus beside the epoch's own. The record is
    admitted by name rather than by content — the claim is about *this*
    transaction naming what it wrote, and the record's own form is covered
    where it is written.
    """
    case = durable_world
    bindings = shipped_bindings(case["world"])
    pointer = f"epochs/{epoch.CURRENT_POINTER}"

    before = chain_entries(case["world_root"])
    first = epoch.build_epoch(case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings)
    (created,) = _registrations(chain_entries(case["world_root"])[len(before) :])
    created_records = {path for path in dict(created.final) if path.startswith("registry/")}
    assert len(created_records) == 1
    assert (
        set(dict(created.final))
        == {f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS}
        | {pointer}
        | created_records
    )

    _extra_record(case["corpus_root"], "second-publication")
    before = chain_entries(case["world_root"])
    second = epoch.build_epoch(case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings)
    assert second.packaging_identity != first.packaging_identity
    (replaced,) = _registrations(chain_entries(case["world_root"])[len(before) :])
    replaced_records = {path for path in dict(replaced.final) if path.startswith("registry/")}
    assert len(replaced_records) == 1 and replaced_records != created_records
    assert (
        set(dict(replaced.final))
        == {f"epochs/{second.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS}
        | {pointer}
        | replaced_records
    )
    assert read.current_epoch(case["world"]).packaging_identity == second.packaging_identity


def _chain_bounds(chain_root: Path) -> tuple[str, str]:
    """One root's `(genesis_digest, tip)`, decoded from the engine's own entries.

    Read off the committed chain files rather than through
    `root.chain_head_reader()`, which is the very callback the anchoring layer
    was handed: asking that callback again would compare the world's answer with
    itself. `atoms` states the correspondence — a `ChainView`'s genesis digest is
    its first entry's and its tip is the last — and consuming it here is the
    consumption the epoch tests allow, not a second certification of `read_chain`.
    """
    entries = chain_entries(chain_root)
    assert entries, f"{chain_root}: the engine's chain carries no entry to anchor against"
    return (entries[0][0], entries[-1][0])


def test_published_anchors_name_the_committed_chains(durable_world):
    """The anchored tuple names the chains the engine actually kept.

    Portably the head callback is a stub, so "the epoch anchored a head" is a
    statement about a fixture. Here the world is the composition root's own
    product, its callback is the engine's chain reader, and the triples the
    carrier published are compared against the entries on disk.

    The world anchor is taken **before** the publication because the build captures
    it at build start: the transaction that writes the epoch moves the world
    chain past the head that epoch anchored, and an anchor that had followed it
    would be naming the act rather than its starting point. The corpus anchor is
    taken after, and must not have moved — nothing wrote to the corpus.
    """
    case = durable_world
    world = case["world"]
    bindings = shipped_bindings(world)
    world_at_build_start = _chain_bounds(case["world_root"])
    corpus_chain = _chain_bounds(case["corpus_root"])

    published = epoch.build_epoch(world, coverage=frozenset({case["corpus_id"]}), bindings=bindings)

    (anchor,) = published.anchors
    assert anchor.subject == case["corpus_id"]
    assert (anchor.genesis_digest, anchor.head_digest) == corpus_chain
    assert _chain_bounds(case["corpus_root"]) == corpus_chain, (
        "nothing wrote to the corpus, so the chain the epoch anchored is still its chain"
    )

    assert published.world_anchor.subject == case["config"].world_id
    assert (
        published.world_anchor.genesis_digest,
        published.world_anchor.head_digest,
    ) == world_at_build_start

    genesis, moved_tip = _chain_bounds(case["world_root"])
    assert genesis == world_at_build_start[0]
    assert moved_tip != world_at_build_start[1], (
        "the publication committed, so the world chain moved past the head the epoch anchored"
    )

    # The captured state and the anchored head describe one view of one corpus,
    # which is what the portable witness above asserts against a stub.
    assert dict(published.coverage) == {case["corpus_id"]: registry.corpus_state_identity(case["corpus_root"])}


def test_world_transactions_register_every_path(durable_world):
    """The labeled durable declaration: rule install, rule removal, GC deletion.

    Committed registration-entry evidence for each of the three world acts that
    are not publication — publication's own entry is tested separately. Every
    assertion is over an entry decoded from the engine-owned chain, never over
    the portable write plan's shape: a plan that named a path it never
    registered would satisfy the plan and not the chain.
    """
    case = durable_world
    world, world_root = case["world"], case["world_root"]

    before = chain_entries(world_root)
    bindings = shipped_bindings(world)
    installed: set[str] = set()
    for entry in _registrations(chain_entries(world_root)[len(before) :]):
        installed |= set(dict(entry.final))
    expected = {
        path
        for bundle in rules.shipped_rule_bundles()
        for path, _content in rules._member_bytes(bundle, rules.binding_for(bundle))
    }
    assert installed == expected
    assert all(path.startswith("rules/") for path in expected)

    first = epoch.build_epoch(world, coverage=frozenset({case["corpus_id"]}), bindings=bindings)
    _extra_record(case["corpus_root"], "before-deletion")
    second = epoch.build_epoch(world, coverage=frozenset({case["corpus_id"]}), bindings=bindings)
    assert read.current_epoch(world).packaging_identity == second.packaging_identity

    before = chain_entries(world_root)
    epoch.delete_epoch(world, first.packaging_identity)
    (deleted,) = _registrations(chain_entries(world_root)[len(before) :])
    assert set(dict(deleted.final)) == {f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS}

    before = chain_entries(world_root)
    removed = rules.remove_rule_binding(world, bindings.coreference)
    (unheld,) = _registrations(chain_entries(world_root)[len(before) :])
    assert set(dict(unheld.final)) == {
        path
        for bundle in rules.shipped_rule_bundles()
        if rules.binding_for(bundle) == removed.binding
        for path, _content in rules._member_bytes(bundle, removed.binding)
    }
