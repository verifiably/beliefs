"""N2 over cut 7's 48 frozen epoch-carrier arms, and the acceptance nodes four of them name.

**Four things live here and they are not the same thing.**

1. **The declaration accounting.** `docs/designs/2026-08-20-conformance-cut-7.md`
   is the frozen authority: §3's `Selected` and `Labeled` bullets *are* the unit
   inventory, and §4 states the row accounting. `TestTheCut7InventoryIsExact`
   parses both out of that file and reconciles them against `CUT7_ARMS`, so a
   declaration table that drifted from the cut fails here rather than being
   recounted by hand at close-out.

2. **The N2 audit.** Every arm is run twice — unsabotaged, where its check must
   pass, and sabotaged, where it must fail — through the shared harness. Unlike
   cut 6, nothing is pinned to a historical tree: cut 7's arms are declared
   against the package as it stands, so both directions read the working tree.

3. **The acceptance nodes.** Four arms name a node in this module. Three are
   durable and run on the certified tuple through
   `tests/acceptance/conftest.py`'s gate: publication's committed registration
   entry, the recovery barrier's refusal to select a partial epoch, and the
   rule-install / rule-removal / GC-deletion transactions' entries. The fourth,
   `test_anchored_head_describes_the_captured_corpus_view`, is portable and is
   not a declared check — it is the **witness** X9's relocated-head arm is
   measured against, and §6.1 finding 6 is why it exists.

4. **The acceptance surface itself**, which is wider than the declarations. The
   *portable journey* walks one world end to end — four shipped rules held
   explicitly, two corpora admitted, two epochs published and read back, all
   four receipts validated, every arm of §8.3's resolution union and every
   §8.4 edge state this slice can reach, then the rule removal and the
   whole-epoch deletion with their sever reports — and asserts nothing about
   crashes. `test_published_anchors_name_the_committed_chains` is its durable
   counterpart: the anchored triples, compared against the engine's own
   committed entries rather than against the callback that produced them.
   Neither is a declared check; both are what `tools/cut7_acceptance.py`
   discharges the cut by running.

**Why the witness exists.** Cut 7 §3.1 requires the head-relocation sabotage to
interpose a real corpus write between the state capture and the relocated head
capture, "since without an interleaved write the sabotage passes vacuously",
and pins that vacuousness check to N2 declaration time. The declared check for
that arm is instrumented — it watches the operation lock — so it sees the
relocation itself and would fail either way. The witness sees only the
*consequence*: it compares the head the epoch anchored with the corpus state
the epoch captured, which is exactly the coherence the row is about. Under
relocation alone the witness passes, and that is the vacuity;
`TestTheRelocatedHeadSabotageIsNotVacuous` demonstrates both directions.
"""

from __future__ import annotations

import dataclasses
import os
import re
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import count
from pathlib import Path

import pytest
import test_n2
import test_world_build
from atoms.chain.model import RegisteredEntry
from authority import ACTOR, FULL
from fixtures_cut6 import PINS
from n2_arms import (
    CLASS_NODE_BY_CONSTRUCTION,
    MIXED_BY_CONSTRUCTION,
    STALE_BY_CONSTRUCTION,
    UNCOLLECTED_BY_CONSTRUCTION,
    VACUOUS_BY_CONSTRUCTION,
    Arm,
    Sabotage,
)
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import (
    CUT7_ARMS,
    INTERPOSED_WRITE,
    RELOCATED_HEAD_CHECK,
    RELOCATED_HEAD_WITNESS,
)
from nodes.core.corpus import Corpus
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY
from test_durable_families import chain_entries
from test_n2 import MalformedArm, audit, baseline
from test_world_build import ALPHA, BETA, corpus_at, genesis_of, sample_nodes, tip_of
from test_world_read import RETIRED, linked_nodes
from test_world_receipts import corpora, document, publish, world_over

from beliefs import root, stored
from beliefs.errors import EpochCurrent, EpochUnknown
from beliefs.world import derive, epoch, read, registry, rules

WORKERS = 8
_COUNTER = count()

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-20-conformance-cut-7.md"

CUT6_SOURCE_COMMIT = "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e"
"""The pre-promotion commit cut 6's declarations are audited against.

Cut 7 touches none of cut 5's or cut 6's surfaces; this pin is used here only
to assert that, byte for byte.
"""

RENAME_COMMIT = "5a02ca2"
WRITE_PERMITS_MIGRATION_COMMIT = "659cc6e"
"""The whole-repo science→beliefs mechanical rename (ledger R7). Re-pins a
file whose only post-freeze edit was that rename's import strings."""

PROFILE_API_MIGRATION_COMMIT = "3c7f32ce64f324d4ee23f389755379b671314dab"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "1e92471",  # exact R20 matcher amendment, validated below
    "python/tests/n2_arms_cut6.py": CUT6_SOURCE_COMMIT,
    "python/tools/cut5_acceptance.py": RENAME_COMMIT,
    "python/tools/cut6_acceptance.py": RENAME_COMMIT,
    # Cut 6's *acceptance module* is not frozen in the same sense — slice 2
    # rewrote it, at `c8c0b12`, to audit the pre-move tree — but it is pinned by
    # that ruling and no later task may drift it either. So it is guarded
    # against the commit that gave it its present content rather than against
    # the pre-move tree it audits, which it has legitimately differed from since
    # `f703913`. Re-pinned again across the rename (ledger R7).
    # Write permits deliberately migrated this audit's lifecycle and world
    # seam calls; 659cc6e is the first commit holding the complete migration.
    # Compiled profiles mechanically added the required profile argument to
    # the live world opener; the historical sources and arm tables stay pinned.
    "python/tests/acceptance/test_n2_cut6.py": PROFILE_API_MIGRATION_COMMIT,
}
"""Each prior-cut surface and the commit whose content it must still hold."""

SYMBOL_KINDS = {
    "derive_producer_snapshot": "producer",
    "enumerate_retractions": "retraction-enumeration",
    "enumerate_certifications": "certification-enumeration",
    "reduce_coreference": "coreference-reduction",
}
"""Which receipt kind each shipped rule's symbol derives.

Duplicated from `test_world_build.SYMBOL_KINDS` rather than imported from
`science`, because no public shipped-symbol -> receipt-kind join exists: the
build input is keyed by §7.5's four kinds and the rules store is keyed by
identity and knows nothing of kinds. Task 9 deliberately did not add
`root.shipped_derivation_bindings`, so the join is the caller's here as it is
there. Two copies of one table is a defect waiting to happen and is reported as
a concern rather than hidden by a helper.
"""


def test_the_duplicated_symbol_kind_join_still_agrees_with_its_original():
    """The two copies of one table, pinned equal.

    There is no public shipped-symbol -> receipt-kind join in `science`, so this
    module carries a second copy of `test_world_build.SYMBOL_KINDS`. Two copies
    of one table is a defect waiting to happen: a rename that updated one of
    them would surface as a bare `KeyError` inside `shipped_bindings` rather
    than as "the two tables disagree". This says which it is.
    """
    assert SYMBOL_KINDS == test_world_build.SYMBOL_KINDS


def shipped_bindings(world: registry.World) -> epoch.DerivationBindings:
    """Hold this package's four rules in `world` and name them as one build input."""
    root.install_shipped_world_rules(world)
    held = {
        SYMBOL_KINDS[bundle.symbol]: rules.binding_for(bundle)
        for bundle in rules.shipped_rule_bundles()
    }
    return epoch.DerivationBindings(
        producer=held["producer"],
        retraction=held["retraction-enumeration"],
        certification=held["certification-enumeration"],
        coreference=held["coreference-reduction"],
    )


# --- the witness for X9's relocated head --------------------------------------


class ContentHeads:
    """A chain-head callback that answers for a *corpus* with its present state.

    A real chain tip moves when a corpus commits, and that is the whole content
    of "the head and the state describe one view". The portable `ChainHeads`
    stub in `test_world_build` answers with a constant derived from the root's
    name, so it cannot see a corpus move at all — which is precisely why an arm
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

    Not a declared check — the **witness** cut 7 §3.1's X9 head/state bullet is
    measured against. It observes nothing about locks: it compares the anchored
    head with the captured corpus state, which is what "one view" means at the
    published-artifact level. A head captured outside the hold still reads the
    same chain when nothing wrote in between, so this passes under relocation
    alone; it fails the moment a write is interposed, which is the interleaving
    the cut requires the sabotage to carry.
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
# back, all four receipts validated, every arm of the resolution union and every
# edge state this slice can reach exercised, and then the two severing acts.
#
# It asserts nothing about crashes. Durability is the certified tuple's subject
# and it is claimed below, by arms that read the engine's own chain; what these
# arms claim is that the acts of the slice compose — that the epoch a build
# published is the epoch `current` selects, that the receipts it carries resolve
# against the store the build read them from, and that removing one of those
# inputs is reported rather than discovered later as an unresolvable receipt.


DERIVATION_KINDS: tuple[derive.ReceiptKind, ...] = (
    "producer",
    "retraction-enumeration",
    "certification-enumeration",
    "coreference-reduction",
)
"""§7.5's four kinds, spelled as the literal type `validate_receipt` takes.

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
    from `Unknown` — §7.2 records a `deprecated_ids` entry exactly as it
    records a live one, so the address survives its corpus going away. Exactly
    one corpus carries it: `derive.address_map` refuses a repeated address even
    when the two claims agree.
    """
    withdrawn = stored.dataset_node("a-successor", title="dataset a successor")
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
    """The whole build path, run for real, before any arm asserts anything.

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

    This is the baseline the two severing arms below are read against: a
    ``validated`` receipt is one whose exact pair is still held here and whose
    named corpora still stand where they stood, re-derived and compared byte for
    byte. An arm that only ever saw a broken receipt would not know which half
    of that the break was.
    """
    outcomes = {kind: read.validate_receipt(journey.world, journey.current, kind) for kind in DERIVATION_KINDS}
    assert len(outcomes) == 4
    for kind, outcome in outcomes.items():
        assert outcome.kind == kind
        assert outcome.outcome == "validated", (kind, outcome.detail)
        assert outcome.validated


def test_resolution_answers_resolved_not_present_and_unknown(journey: Journey):
    """§8.3's three arms, all three from one publication.

    The line between `NotPresent` and `Unknown` is what the epoch recorded and
    never what is here now, so both are taken against the *same* epoch: one
    address it recorded whose corpus has stopped being carried, and one address
    it never observed at all.
    """
    addresses = {
        entry["address"]: (entry["corpus_id"], entry["uid"])
        for entry in document(journey.current, "address-map.yaml")["addresses"]
    }
    stamp = read.BoundStamp(journey.current.packaging_identity, journey.current.coverage)

    resolved = read.resolve_address(journey.world, journey.current, "dataset:a")
    assert isinstance(resolved, read.Resolved)
    assert resolved.location == read.Location(*addresses["dataset:a"])
    assert resolved.stamp == stamp

    # A retired address is a recorded one, and resolves to its successor's uid.
    retired = read.resolve_address(journey.world, journey.current, RETIRED)
    assert isinstance(retired, read.Resolved)
    assert retired.location == read.Location(*addresses[RETIRED])

    unknown = read.resolve_address(journey.world, journey.current, "dataset:never-observed")
    assert isinstance(unknown, read.Unknown)
    assert unknown.stamp == stamp

    # Now BETA stops answering to its `corpus_id`. The epoch still records what
    # it carried, so those addresses are absent rather than unknown.
    (journey.roots[BETA] / "corpus.yaml").unlink()
    absent = read.resolve_address(journey.world, journey.current, "dataset:b")
    assert isinstance(absent, read.NotPresent)
    assert absent.stamp == stamp
    assert isinstance(read.resolve_address(journey.world, journey.current, "dataset:a"), read.Resolved)
    assert isinstance(
        read.resolve_address(journey.world, journey.current, "dataset:never-observed"), read.Unknown
    )


def test_edges_answer_active_inactive_and_indeterminate(journey: Journey):
    """§8.4's three states, and the expansion that refuses rather than guess.

    `active` and `inactive` come from the stored balance of a reduction this
    world can still stand behind. `indeterminate` is reached here through the
    coverage half of §8.4 — a live corpus the publication never observed — and
    through the receipt half in the removal arm below, which is the other input
    the section names.
    """
    assert read.EDGE_STATES == ("active", "inactive", "indeterminate")

    active = read.coreference_edge(journey.world, journey.current, "dataset:a", "dataset:a-b")
    assert active.state == "active"
    assert active.missing_coverage == () and active.receipt_outcome is None

    # A pair the reduction never recorded is established `inactive`, not unknown.
    inactive = read.coreference_edge(journey.world, journey.current, "dataset:a-b", "dataset:a-c")
    assert inactive.state == "inactive"
    assert read.expand_coreference(journey.world, journey.current, "dataset:a") == (
        "dataset:a-b",
        "dataset:a-c",
    )

    # An epoch over ALPHA alone did not observe BETA, which is live here.
    narrow = publish(journey.world, (ALPHA,), journey.bindings)
    narrowed = read.coreference_edge(journey.world, narrow, "dataset:a", "dataset:a-b")
    assert narrowed.state == "indeterminate"
    assert narrowed.missing_coverage == (BETA,)
    assert narrowed.receipt_outcome is None
    with pytest.raises(read.EdgeIndeterminate) as refusal:
        read.expand_coreference(journey.world, narrow, "dataset:a")
    assert refusal.value.missing_coverage == (BETA,)


def test_removing_a_binding_reports_the_receipts_it_severed(journey: Journey):
    """§4.3: the removal names what lost this store's resolution path.

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
    answer = read.coreference_edge(journey.world, journey.current, "dataset:a", "dataset:a-b")
    assert answer.state == "indeterminate"
    assert answer.receipt_outcome == "unresolvable"
    assert answer.missing_coverage == ()
    with pytest.raises(read.EdgeIndeterminate) as refusal:
        read.expand_coreference(journey.world, journey.current, "dataset:a")
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
    """§9's fifth identity: the producer snapshot's own subject identity.

    Taken from the producer receipt's `subject`, which is what digests the
    projection — not from the receipt's identity, which digests the capture as
    well and therefore moves whenever any covered corpus does.
    """
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    return subject


def test_deleting_a_noncurrent_epoch_reports_the_identities_it_severed(journey: Journey):
    """§9: the current epoch is undeletable, and the other one reports both answers.

    The record added between the two publications is a plain dataset, so it
    moved BETA's corpus state and changed no `produces` edge. That splits the
    report exactly along the line §9 draws. All four receipt identities digest
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


@pytest.fixture(scope="session")
def cut7_work_directory(work_directory) -> Path:
    configured = os.environ.get("SCIENCE_CUT7_ROOT")
    work = Path(configured) if configured else work_directory
    work.mkdir(parents=True, exist_ok=True)
    return work


@pytest.fixture()
def durable_world(cut7_work_directory):
    """One registered world root and one registered corpus root, on the tuple.

    Everything is the composition root's own product: `init_world_root` and
    `init_corpus_root` reach the engine's volume binding, so an uncertified
    tuple fails here rather than inside an assertion, and the executor the
    world writes with is `DurableExecutor` rather than the portable one.
    """
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = cut7_work_directory / f"world-{suffix}"
    corpus_root = cut7_work_directory / f"corpus-{suffix}"
    config = registry.WorldConfig(world_root, "7" * 32, (corpus_root,))
    try:
        root.init_world_root(config, authority=FULL)
        root.init_corpus_root(corpus_root, authority=FULL)
        root.open_corpus(corpus_root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
        # Stored records are placed with the `nodes` handle, exactly as the
        # portable fixtures place them: what these arms assert is committed
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


def _extra_record(corpus_root: Path, slug: str) -> None:
    """Move the corpus, so the next build has a different epoch to publish."""
    Corpus(corpus_root).add(stored.dataset_node(slug, title=f"dataset {slug}"))


def _target_identity(world, corpus_id: str, bindings: epoch.DerivationBindings) -> str:
    """The packaging identity the next build of this coverage would publish.

    Pure: a capture and a derivation, and no transaction. It is computed before
    each killed attempt so the attempt can be judged against a name rather than
    against whatever it happened to leave behind.
    """
    draft = epoch._capture_build_inputs(
        world, coverage=frozenset({corpus_id}), bindings=bindings.by_kind()
    )
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
"""Every Science-observable boundary of one publication, in the order §5.4
crosses them.

The frozen cell says "kill the writer at every stage of publication". Cut 7's
selection states the narrowing outright: the stages *inside* the transaction
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
        f"{stage}: publication submitted {len(calls)} transactions; §5.4 publishes in one, and a "
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
    """X2. `current` names the prior epoch or the new, complete one — never else.

    The writer is killed at every Science-observable stage boundary of the
    one-transaction write, and after each kill a **fresh** world crosses the
    recovery barrier and follows `current`. The answer is always a complete
    epoch: the prior one where the kill preceded the commit, and the new one
    where a committed transaction rolled forward. Nothing is ever missing and
    nothing ever names incomplete content.

    The intra-transaction stages are not exercised and are not claimed: they
    belong to the engine's certified recovery and Science cannot observe them
    (cut 7 §7 limitation 2). What *is* claimed here about the transaction is
    that there is one of it — `second-transaction` kills the second commit, and
    a correct publication never reaches it.
    """
    case = durable_world
    bindings = shipped_bindings(case["world"])
    first = epoch.build_epoch(
        case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings
    )
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
    # from one of the two loops above is a boundary this arm claims to cover and
    # does not, which nothing else here would notice.
    assert tuple(attempted) == PUBLICATION_STAGES


def test_publication_registration_names_epoch_and_current(durable_world):
    """X2. The publication transaction commits an entry naming every member and `current`.

    Decoded from the engine-owned chain, not from the write plan: what is being
    asserted is that the committed record of the act names the paths it wrote,
    which is the durable half of "one transaction" and the only crash-atomicity
    evidence this cut claims (§7 limitation 2).

    Both shapes are exercised. The first publication *creates* the pointer; the
    second *replaces* it, and both entries name the eleven members of their own
    epoch alongside it.

    Slice 3's build-origin log-head record joins the same transaction
    (log-verification design §3.3), so the committed entry names one
    `registry/` path per covered corpus beside the epoch's own. The record is
    admitted by name rather than by content — X2's claim is about *this*
    transaction naming what it wrote, and the record's own form is covered
    where it is written.
    """
    case = durable_world
    bindings = shipped_bindings(case["world"])
    pointer = f"epochs/{epoch.CURRENT_POINTER}"

    before = chain_entries(case["world_root"])
    first = epoch.build_epoch(
        case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings
    )
    (created,) = _registrations(chain_entries(case["world_root"])[len(before) :])
    created_records = {path for path in dict(created.final) if path.startswith("registry/")}
    assert len(created_records) == 1
    assert set(dict(created.final)) == {
        f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS
    } | {pointer} | created_records

    _extra_record(case["corpus_root"], "second-publication")
    before = chain_entries(case["world_root"])
    second = epoch.build_epoch(
        case["world"], coverage=frozenset({case["corpus_id"]}), bindings=bindings
    )
    assert second.packaging_identity != first.packaging_identity
    (replaced,) = _registrations(chain_entries(case["world_root"])[len(before) :])
    replaced_records = {path for path in dict(replaced.final) if path.startswith("registry/")}
    assert len(replaced_records) == 1 and replaced_records != created_records
    assert set(dict(replaced.final)) == {
        f"epochs/{second.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS
    } | {pointer} | replaced_records
    assert read.current_epoch(case["world"]).packaging_identity == second.packaging_identity


def _chain_bounds(chain_root: Path) -> tuple[str, str]:
    """One root's `(genesis_digest, tip)`, decoded from the engine's own entries.

    Read off the committed chain files rather than through
    `root.chain_head_reader()`, which is the very callback the anchoring layer
    was handed: asking that callback again would compare the world's answer with
    itself. `atoms` states the correspondence — a `ChainView`'s genesis digest is
    its first entry's and its tip is the last — and consuming it here is the
    consumption cut 7 §5 allows, not a second certification of `read_chain`.
    """
    entries = chain_entries(chain_root)
    assert entries, f"{chain_root}: the engine's chain carries no entry to anchor against"
    return (entries[0][0], entries[-1][0])


def test_published_anchors_name_the_committed_chains(durable_world):
    """X2/X9 durably: the anchored tuple names the chains the engine actually kept.

    Portably the head callback is a stub, so "the epoch anchored a head" is a
    statement about a fixture. Here the world is the composition root's own
    product, its callback is the engine's chain reader, and the triples the
    carrier published are compared against the entries on disk.

    The world anchor is taken **before** the publication because §5.2 captures
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
    assert dict(published.coverage) == {
        case["corpus_id"]: registry.corpus_state_identity(case["corpus_root"])
    }


def test_world_transactions_register_every_path(durable_world):
    """The labeled durable declaration: rule install, rule removal, GC deletion.

    Committed registration-entry evidence for each of the three world acts that
    are not publication — publication's own entry is X2's selected unit. Every
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
    assert set(dict(deleted.final)) == {
        f"epochs/{first.packaging_identity}/{member}" for member in epoch.EPOCH_MEMBERS
    }

    before = chain_entries(world_root)
    removed = rules.remove_rule_binding(world, bindings.coreference)
    (unheld,) = _registrations(chain_entries(world_root)[len(before) :])
    assert set(dict(unheld.final)) == {
        path
        for bundle in rules.shipped_rule_bundles()
        if rules.binding_for(bundle) == removed.binding
        for path, _content in rules._member_bytes(bundle, removed.binding)
    }


# --- the N2 audit -------------------------------------------------------------


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    """The 48 arms, audited against the tree they were declared against.

    No pin. Cut 6's declarations name `world.py`, which slice 2 promoted away,
    so its audit reads a historical tree; cut 7's name the present package and
    are audited against it in both directions.
    """
    root_path = tmp_path_factory.mktemp("n2-cut7")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root_path / f"arm{pair[0]}"), enumerate(CUT7_ARMS)))


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason + "\n" + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut7ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-7 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-7 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-7 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-7 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-7 check resolves and passes against the real package",
            sabotage=CUT7_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT7_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


class TestTheRelocatedHeadSabotageIsNotVacuous:
    """Cut 7 §6.1 finding 6, discharged at declaration time.

    The finding: "X9's head-relocation sabotage could pass vacuously without an
    interleaved corpus write between state capture and the relocated head
    capture. The bullet now requires the interposed write and pins the
    vacuousness check to N2 declaration time." This is that check, and it is run
    against a *witness* rather than against the declared node — the declared
    node watches the operation lock, so it sees the relocation itself and cannot
    show what the write adds. The witness compares the anchored head with the
    captured corpus state, sees only the consequence, and is therefore the thing
    the interleaving is for.
    """

    def test_the_declared_mutation_carries_a_real_interposed_write(self):
        arm = _relocated_head_arm()
        assert arm.sabotage.after.count(INTERPOSED_WRITE) == 1
        relocated = arm.sabotage.after.split(INTERPOSED_WRITE)[1]
        assert "world._chain_head(carrier)" in relocated, (
            "the interposed write must sit between the state capture and the relocated head capture"
        )
        assert "world._chain_head(carrier)" not in arm.sabotage.after.split(INTERPOSED_WRITE)[0]
        assert arm.sabotage.before.count("world._chain_head(carrier)") == 1, (
            "the mutation must move the sole head-capture call, not one of several"
        )

    def test_the_witness_passes_against_the_unsabotaged_package(self):
        assert test_n2._run_check(RELOCATED_HEAD_WITNESS, None).returncode == test_n2.PASSED

    def test_relocation_alone_passes_the_witness_and_the_interposed_write_fails_it(self, tmp_path):
        arm = _relocated_head_arm()
        relocation_only = dataclasses.replace(
            arm,
            sabotage=Sabotage(
                module=arm.sabotage.module,
                before=arm.sabotage.before,
                after=arm.sabotage.after.replace(INTERPOSED_WRITE, ""),
            ),
        )
        without = test_n2._sabotage(relocation_only, tmp_path / "relocation-only")
        assert without is not None
        assert test_n2._run_check(RELOCATED_HEAD_WITNESS, without).returncode == test_n2.PASSED, (
            "the relocation alone is vacuous against the witness, which is what the frozen cut says "
            "and what the interposed write exists to fix"
        )

        with_write = test_n2._sabotage(arm, tmp_path / "interposed")
        assert with_write is not None
        assert test_n2._run_check(RELOCATED_HEAD_WITNESS, with_write).returncode == test_n2.FAILED, (
            "with a corpus write interposed the anchored head no longer describes the captured "
            "state, which is the mismatch the arm asserts is unconstructible"
        )

    def test_the_declared_check_is_the_instrumented_one_and_still_fails(self, tmp_path):
        arm = _relocated_head_arm()
        assert audit(arm, tmp_path / "declared").verdict == "sound"


def _relocated_head_arm() -> Arm:
    (arm,) = [arm for arm in CUT7_ARMS if arm.checks == (RELOCATED_HEAD_CHECK,)]
    return arm


# --- the inventory, reconciled against the frozen cut -------------------------


SELECTED_BULLET = re.compile(r"^- \*\*Selected\b")
LABELED_BULLET = re.compile(r"^- \*\*Labeled\b")
ROW_HEADING = re.compile(r"^#### (\S+) — (full|part|deferred)$")
LABELED_HEADING = re.compile(r"^### 3\.3 ")
W8A_HEADING = re.compile(r"^### 3\.2 ")
ACCOUNTING_ROW = re.compile(r"^\| (full|part|deferred) \| (.+?) \| +(\d+) \|$")


def frozen_bullets() -> tuple[Counter, int]:
    """§3's `Selected` bullets per row, and its `Labeled` bullet count.

    Parsed out of the frozen cut rather than restated: §5 makes those bullets
    the declaration inventory, so a table that agreed with a copy of them would
    be agreeing with itself.
    """
    selected: Counter = Counter()
    labeled = 0
    row: str | None = None
    for line in FROZEN_CUT.read_text(encoding="utf-8").splitlines():
        heading = ROW_HEADING.match(line)
        if heading:
            row = heading.group(1)
        elif W8A_HEADING.match(line):
            row = "W8a"
        elif LABELED_HEADING.match(line):
            row = None
        if SELECTED_BULLET.match(line):
            assert row is not None, f"a Selected bullet outside a row: {line}"
            selected[row] += 1
        if LABELED_BULLET.match(line):
            assert row is None, f"a Labeled bullet inside row {row}: {line}"
            labeled += 1
    return selected, labeled


def frozen_row_states() -> dict[str, tuple[str, ...]]:
    """§4's accounting table: which rows are full, part, and deferred."""
    states: dict[str, tuple[str, ...]] = {}
    for line in FROZEN_CUT.read_text(encoding="utf-8").splitlines():
        entry = ACCOUNTING_ROW.match(line)
        if entry:
            rows = () if entry.group(2).strip() == "—" else tuple(
                name.strip() for name in entry.group(2).split(",")
            )
            assert len(rows) == int(entry.group(3)), line
            states[entry.group(1)] = rows
    return states


def declared_rows() -> Counter:
    """`CUT7_ARMS` by frozen row, with every labeled declaration under one key."""
    return Counter("labeled" if arm.row.startswith("labeled:") else arm.row for arm in CUT7_ARMS)


class TestTheCut7InventoryIsExact:
    def test_the_frozen_cut_states_seven_full_and_four_part_rows(self):
        states = frozen_row_states()
        assert len(states["full"]) == 7
        assert len(states["part"]) == 4
        assert states["deferred"] == ()
        assert len(states["full"]) + len(states["part"]) == 11

    def test_every_selected_and_labeled_bullet_is_declared_exactly_once(self):
        selected, labeled = frozen_bullets()
        assert sum(selected.values()) == 38
        assert labeled == 10
        assert sum(selected.values()) + labeled == 48
        assert declared_rows() == Counter({**selected, "labeled": labeled})

    def test_exactly_one_declaration_exists_per_bullet(self):
        assert len(CUT7_ARMS) == 48

    def test_the_declared_rows_are_the_rows_the_cut_reads(self):
        states = frozen_row_states()
        assert set(declared_rows()) - {"labeled"} == set(states["full"]) | set(states["part"])

    def test_every_labeled_declaration_is_distinct_and_named(self):
        labels = [arm.row for arm in CUT7_ARMS if arm.row.startswith("labeled:")]
        assert len(labels) == 10
        assert len(set(labels)) == 10

    def test_labeled_declarations_cite_their_frozen_specification(self):
        assert all(
            "specification §" in arm.asserts for arm in CUT7_ARMS if arm.row.startswith("labeled:")
        )

    def test_every_arm_has_one_source_mutation_and_one_exact_check_node(self):
        for arm in CUT7_ARMS:
            assert type(arm.sabotage) is Sabotage, arm.label
            assert arm.sabotage.before and arm.sabotage.after, arm.label
            assert arm.sabotage.before != arm.sabotage.after, arm.label
            assert len(arm.checks) == 1, arm.label

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT7_ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"
                assert len(check.split("::")) >= 2, f"{arm.label}: {check}"

    def test_every_sabotage_names_a_present_module_and_applies_exactly_once(self):
        for arm in CUT7_ARMS:
            target = test_n2.PACKAGE / arm.sabotage.module
            assert target.is_file(), f"{arm.label}: {arm.sabotage.module}"
            assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.label

    def test_no_arm_names_the_pre_promotion_world_module(self):
        # Cut 6's paths are historical evidence and are not recreated; a cut-7
        # arm naming `world.py` would silently apply to nothing (`_sabotage`
        # returns `None`) and score `stale` rather than `sound`.
        assert not [arm for arm in CUT7_ARMS if arm.sabotage.module == "world.py"]
        assert {arm.sabotage.module for arm in CUT7_ARMS} <= {
            "belief.py",
            "closure.py",
            "corpus.py",
            "root.py",
            "world/derive.py",
            "world/epoch.py",
            "world/read.py",
            "world/rules.py",
        }

    def test_deferred_and_lapsed_bullets_are_not_declared(self):
        text = FROZEN_CUT.read_text(encoding="utf-8")
        assert text.count("\n- **Deferred:**") == 6
        assert text.count("\n- **Lapsed:**") == 1
        assert text.count("\n- **Prior-cut evidence:**") == 1
        # None of them adds a unit: 38 + 10 is the whole inventory.
        assert len(CUT7_ARMS) == 48


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_cut_files_are_byte_identical_to_their_pinned_versions(self):
        assert_cut5_matcher_migration(REPO_ROOT)
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, (
                f"{path} has moved since {pin}; cut 5's and cut 6's declarations, runners and pinned "
                "audit are frozen, and cut 7 edits none of them"
            )

    def test_the_guard_covers_cut_6s_pinned_acceptance_module(self):
        # Named rather than implied: it is the one prior-cut surface slice 2 did
        # change, so a guard that quietly omitted it would stay green through a
        # later edit to the very file an earlier ruling pinned.
        assert "python/tests/acceptance/test_n2_cut6.py" in FROZEN_PRIOR_CUT_FILES

    def test_no_cut7_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {check for arm in (*CUT5_ARMS, *CUT6_ARMS) for check in arm.checks}
        ours = {check for arm in CUT7_ARMS for check in arm.checks}
        assert not prior & ours

    def test_no_prior_cut_arm_claims_a_cut7_row(self):
        # Cut 6 read X4, X5, X6 and W13; cut 7 reads X5 as well, and its X5 unit
        # is the *build* arm, which cut 6 recorded prospectively rather than ran.
        assert {arm.row for arm in CUT6_ARMS} & {arm.row for arm in CUT7_ARMS} == {"X5"}
        assert not {arm.row for arm in CUT5_ARMS} & {arm.row for arm in CUT7_ARMS}


@pytest.mark.parametrize(
    ("arm", "verdict"),
    [
        (VACUOUS_BY_CONSTRUCTION, "vacuous"),
        (MIXED_BY_CONSTRUCTION, "mixed"),
        (UNCOLLECTED_BY_CONSTRUCTION, "uncollected"),
        (STALE_BY_CONSTRUCTION, "stale"),
    ],
)
def test_the_harness_preserves_each_malformed_verdict(tmp_path, arm, verdict):
    assert audit(arm, tmp_path / verdict).verdict == verdict


def test_the_harness_rejects_a_class_node(tmp_path):
    with pytest.raises(MalformedArm, match="one test function"):
        audit(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")


def assert_cut5_matcher_migration(root: Path) -> None:
    """The upstream R20 matcher amendment changes no declaration or check."""
    path = "python/tests/n2_arms_cut5.py"
    original = subprocess.run(
        ["git", "-C", str(root), "show", "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e:" + path],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    amended = subprocess.run(
        ["git", "-C", str(root), "show", "1e92471:" + path], check=True, capture_output=True, text=True
    ).stdout
    before = '                "        if (\\n"\n                \'            variant == "stochastic-unseeded"\\n\'\n                "            and equivalence_rule in BITWISE_EQUIVALENCE_RULES\\n"\n                "        ):"\n            ),\n            after="        if False:",\n'
    after = '                "        except UnfreezableSpec as caught:\\n"\n                \'            raise ValidationRefused(f"{record.id}: {caught}") from caught\'\n            ),\n            after="        except UnfreezableSpec:\\n            pass",\n'
    assert original.count(before) == amended.count(after) == 1
    assert original.replace(before, after) == amended
