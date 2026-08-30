"""The registered-surface projection, replay, and the removal policy pass.

**Why the states here are inert objects.** Replay compares path states by
equality and by nothing else — the design's one-summary-model rule is a
mechanism only while Science cannot read a state. `Opaque` answers `==` and
raises on every attribute, so a replay that reached inside a state to
interpret or re-encode it fails these arms rather than passing them quietly.
The engine's real `PathState` values arrive through the seam and satisfy the
same contract; standing them in with objects that answer nothing else is what
makes the property assertable.
"""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest
from atoms.chain.inspect import STAGING_LEAF
from atoms.core.fingerprint import ABSENT as ENGINE_ABSENT
from atoms.core.scratch import CHAIN_LEAF, SCRATCH_SIGIL
from nodes.core.errors import PlanRefusedError
from nodes.core.frontmatter import node_to_markdown
from nodes.core.ids import KIND_RE, SLUG_RE
from nodes.core.node import Node
from nodes.core.store import Store
from nodes.core.write_plan import CreateOp
from test_world_log_codecs import (
    CUT8_CORPUS_ID,
    Chain,
    capture_at,
    four_state_classes,
    inspected,
    populated_corpus,
    removed_record,
    rewritten_tail,
    rolled_back_creation,
    settled_corpus,
)
from test_world_log_codecs import MANIFEST as MANIFEST_PATH
from test_world_log_codecs import RECORD as RECORD_PATH

from beliefs import root as science_root
from beliefs.world import verify
from beliefs.world.anchors import AnchorActOrigin, CorpusSubject, LogHeadRecord
from beliefs.world.epoch import CURRENT_POINTER, EPOCH_MEMBERS
from beliefs.world.logmodel import (
    GenesisEntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)
from beliefs.world.rules import _MEMBER_NAME

# --- the opaque state stand-in ------------------------------------------


class Opaque:
    """A path state that answers equality and nothing else."""

    __hash__ = None  # type: ignore[assignment]  # pyright: ignore[reportIncompatibleMethodOverride]
    """Unhashable on purpose: a state belongs in a comparison, never in a set
    or a dict key. Code that indexed by state fails here instead of quietly
    depending on an engine value's hash."""

    def __init__(self, label: str) -> None:
        # `label` is set through the instance dict, so `__getattr__` never
        # sees it; every *other* attribute read is a violation.
        object.__setattr__(self, "_label", label)

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"a path state was read for {name!r}: states are compared, never interpreted")

    def __repr__(self) -> str:
        return f"Opaque({self.__dict__['_label']!r})"


ABSENT = Opaque("absent")
MANIFEST = Opaque("corpus.yaml@0")
RECORD = Opaque("verification/v1.md@1")
OTHER = Opaque("verification/v2.md@1")


# --- chain fabrication ---------------------------------------------------


def genesis(*baseline: tuple[str, object]) -> GenesisEntryView:
    return GenesisEntryView(digest="g" * 64, payload=b"genesis", baseline=baseline)


def registration(
    digest: str,
    txid: str,
    initial: tuple[tuple[str, object], ...],
    final: tuple[tuple[str, object], ...],
) -> RegisteredEntryView:
    return RegisteredEntryView(
        digest=digest,
        txid=txid,
        intent_digest="sha256:" + "0" * 64,
        consumer_tag="science-corpus-write-v1",
        initial=initial,
        final=final,
        fulfills=None,
    )


def settlement(registration_digest: str, txid: str, *, committed: bool) -> SettledEntryView:
    return SettledEntryView(
        digest=f"s{registration_digest[1:]}", txid=txid, registration=registration_digest, committed=committed
    )


def chain(head: GenesisEntryView, *rest: IntentEntryView | RegisteredEntryView | SettledEntryView) -> WellFormedView:
    """R10's shape: the genesis is `entries[0]`, the same object."""
    entries = (head, *rest)
    return WellFormedView(genesis=head, entries=entries, tip=entries[-1].digest, pending=())


CREATED = chain(
    genesis(("corpus.yaml", MANIFEST)),
    registration("a" * 64, "tx-1", (("verification/v1.md", ABSENT),), (("verification/v1.md", RECORD),)),
    settlement("a" * 64, "tx-1", committed=True),
)

MATCHING_DISK: tuple[tuple[str, object], ...] = (
    ("corpus.yaml", MANIFEST),
    ("verification/v1.md", RECORD),
)


# --- held historical bytes -----------------------------------------------


def verification_bytes(slug: str, verdict: str) -> bytes:
    node = Node(
        id=f"verification:{slug}",
        uid="0" * 32,
        kind="verification",
        title="a held copy",
        facets={
            "verification": {
                "assessment": "assessment:a1",
                "scope": "clean-environment",
                "verdict": verdict,
            }
        },
    )
    return node_to_markdown(node).encode("utf-8")


def held(*payloads: bytes) -> dict[str, bytes]:
    return {f"sha256:{hashlib.sha256(payload).hexdigest()}": payload for payload in payloads}


# --- the projection ------------------------------------------------------


def write(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_the_corpus_projection_is_the_claimed_records_and_the_manifest(tmp_path):
    root = tmp_path / "corpus"
    write(root / "corpus.yaml")
    write(root / "verification" / "v1.md")
    write(root / "assessment" / "a1.md")
    write(root / "notes.txt")
    write(root / ".nodes-index" / "snapshot.py.json")
    write(root / ".nodes-index" / "stray.md")
    write(root / ".#~chain" / "0123")
    (root / "verification" / "squat.md").symlink_to(root / "verification" / "v1.md")

    assert verify.registered_surface_paths(root, "corpus") == (
        "assessment/a1.md",
        "corpus.yaml",
        "verification/squat.md",
        "verification/v1.md",
    )


def test_the_corpus_projection_is_sorted_over_whole_paths(tmp_path):
    # The walk's own order puts `verification/v.md` before `verification.md`;
    # the projection's order is the order its caller states paths in.
    root = tmp_path / "corpus"
    write(root / "verification" / "v.md")
    write(root / "verification.md")

    assert verify.registered_surface_paths(root, "corpus") == ("verification.md", "verification/v.md")


def test_the_corpus_projection_does_not_follow_a_symlinked_directory(tmp_path):
    root = tmp_path / "corpus"
    write(root / "verification" / "v1.md")
    write(tmp_path / "elsewhere" / "smuggled.md")
    (root / "mirror").symlink_to(tmp_path / "elsewhere")

    assert verify.registered_surface_paths(root, "corpus") == ("verification/v1.md",)


def test_the_world_projection_is_the_three_grammars_and_the_mirror(tmp_path):
    root = tmp_path / "world"
    write(root / "world.yaml")
    write(root / "registry" / "aa.yaml")
    write(root / "epochs" / "current")
    write(root / "epochs" / "ee" / "manifest.yaml")
    write(root / "rules" / "r1" / "rule.yaml")
    write(root / "rules" / "r1" / "fixtures" / "f.json")
    write(root / "verification" / "v1.md")
    write(root / "notes.txt")
    write(root / ".#~chain" / "0123")
    (root / "mirror").symlink_to(root / "epochs")
    # A broken symlink at a claimed path is a claimed path: absence and a
    # dangling link are different states, and only the surface can say which.
    (root / "registry" / "bb.yaml").symlink_to(root / "registry" / "gone.yaml")

    assert verify.registered_surface_paths(root, "world") == (
        "epochs/current",
        "epochs/ee/manifest.yaml",
        "registry/aa.yaml",
        "registry/bb.yaml",
        "rules/r1/fixtures/f.json",
        "rules/r1/rule.yaml",
        "world.yaml",
    )


def test_a_non_directory_occupying_a_grammars_name_is_a_claimed_path(tmp_path):
    # Squatting `registry` with a file is a surface disagreement to report,
    # not a namespace to look away from.
    root = tmp_path / "world"
    write(root / "world.yaml")
    write(root / "registry")

    assert verify.registered_surface_paths(root, "world") == ("registry", "world.yaml")


def test_an_unclaimed_kind_refuses(tmp_path):
    # "store" joined the projection with the root-lifecycle slice; "holdings"
    # is the next planned kind and stays unclaimed until its own slice.
    with pytest.raises(ValueError):
        verify.registered_surface_paths(tmp_path, "holdings")  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("kind", ["corpus", "world"])
def test_a_missing_root_refuses_rather_than_projecting_an_empty_surface(tmp_path, kind):
    with pytest.raises(FileNotFoundError):
        verify.registered_surface_paths(tmp_path / "gone", kind)


@pytest.mark.parametrize("kind", ["corpus", "world"])
def test_a_root_that_is_not_a_directory_refuses(tmp_path, kind):
    write(tmp_path / "a-file")

    with pytest.raises(FileNotFoundError):
        verify.registered_surface_paths(tmp_path / "a-file", kind)


def test_no_declared_layout_name_can_begin_with_a_dot():
    """The exclusion rule's safety, made load-bearing.

    Bookkeeping is excluded by its leading dot, which is only sound while no
    declared name can carry one. Every grammar that can name a leaf in a
    projected root is checked here, so a substrate or packaging change that
    admitted a dotted name fails this arm instead of silently shrinking the
    surface.
    """
    named = (
        verify.CORPUS_MANIFEST,
        verify.WORLD_MANIFEST,
        CURRENT_POINTER,
        *verify.WORLD_NAMESPACES,
        *EPOCH_MEMBERS,
    )
    assert [name for name in named if name.startswith(".")] == []
    for pattern in (KIND_RE, SLUG_RE, _MEMBER_NAME):
        assert pattern.fullmatch(".hidden") is None, pattern.pattern
        assert pattern.fullmatch(".") is None, pattern.pattern


def test_the_record_path_rule_is_the_substrates_own(tmp_path):
    # A layout change in `nodes` must fail here rather than quietly leaving
    # every held copy unresolved.
    node_id = "verification:a-b.c:d"

    assert verify._record_path(node_id) == Store(tmp_path).path_for(node_id).relative_to(tmp_path).as_posix()


# --- replay --------------------------------------------------------------


def test_a_committed_history_validates_against_the_disk_it_produced():
    result = verify.replay(CREATED, MATCHING_DISK, ABSENT, None)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_a_raw_delete_refutes():
    result = verify.replay(CREATED, (("corpus.yaml", MANIFEST),), ABSENT, None)

    assert result.refuted
    assert result.disagreements == ("head:verification/v1.md",)


def test_a_raw_create_refutes():
    disk = MATCHING_DISK + (("verification/v2.md", OTHER),)

    result = verify.replay(CREATED, disk, ABSENT, None)

    assert result.refuted
    assert result.disagreements == ("head:verification/v2.md",)


def test_a_rolled_back_creation_is_no_transition():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("b" * 64, "tx-2", (("verification/v2.md", ABSENT),), (("verification/v2.md", OTHER),)),
        settlement("b" * 64, "tx-2", committed=False),
    )

    result = verify.replay(view, (("corpus.yaml", MANIFEST),), ABSENT, None)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_an_unsettled_registration_is_no_transition():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("c" * 64, "tx-3", (("verification/v2.md", ABSENT),), (("verification/v2.md", OTHER),)),
    )

    result = verify.replay(view, (("corpus.yaml", MANIFEST),), ABSENT, None)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_an_initial_fingerprint_disagreement_refutes():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("d" * 64, "tx-4", (("corpus.yaml", OTHER),), (("corpus.yaml", RECORD),)),
        settlement("d" * 64, "tx-4", committed=True),
    )

    result = verify.replay(view, (("corpus.yaml", RECORD),), ABSENT, None)

    assert result.refuted
    assert result.disagreements == ("initial:corpus.yaml@tx-4",)


def test_a_disagreement_does_not_truncate_the_removal_inventory():
    # The disagreement is at entry 1 and the removal at entry 3: an inventory
    # that stopped at the first disagreement would report the removal as
    # never having happened.
    view = chain(
        genesis(("corpus.yaml", MANIFEST), ("verification/v1.md", RECORD)),
        registration("d" * 64, "tx-4", (("corpus.yaml", OTHER),), (("corpus.yaml", MANIFEST),)),
        settlement("d" * 64, "tx-4", committed=True),
        registration("e" * 64, "tx-5", (("verification/v1.md", RECORD),), (("verification/v1.md", ABSENT),)),
        settlement("e" * 64, "tx-5", committed=True),
    )

    result = verify.replay(view, SURVIVING_DISK, ABSENT, None)

    assert result.refuted
    # The head comparison is skipped — every `head:` entry past a divergence
    # would be a consequence of it — and the first disagreement is the report.
    assert result.disagreements == ("initial:corpus.yaml@tx-4",)
    assert [(finding.code, finding.ref) for finding in result.findings] == [
        ("record-removed", "verification/v1.md")
    ]


def test_the_baseline_is_replayed_from_the_genesis():
    view = chain(genesis(("corpus.yaml", MANIFEST)))

    assert not verify.replay(view, (("corpus.yaml", MANIFEST),), ABSENT, None).refuted
    assert verify.replay(view, (("corpus.yaml", RECORD),), ABSENT, None).disagreements == ("head:corpus.yaml",)


# --- the policy pass -----------------------------------------------------


REMOVED = chain(
    genesis(("corpus.yaml", MANIFEST), ("verification/v1.md", RECORD)),
    registration("e" * 64, "tx-5", (("verification/v1.md", RECORD),), (("verification/v1.md", ABSENT),)),
    settlement("e" * 64, "tx-5", committed=True),
)
SURVIVING_DISK: tuple[tuple[str, object], ...] = (("corpus.yaml", MANIFEST),)


def test_a_committed_removal_is_a_finding_even_with_no_history():
    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, None)

    assert not result.refuted
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert (finding.code, finding.ref, finding.detail) == ("record-removed", "verification/v1.md", "txid=tx-5")


def test_a_held_failing_verification_classifies_the_removal_and_names_its_digest():
    payload = verification_bytes("v1", "failed")
    history = held(payload)
    digest = next(iter(history))

    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, history)

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "failing-verification-removed"]
    classified = result.findings[1]
    assert classified.severity == "error"
    assert classified.ref == "verification/v1.md"
    assert classified.detail == f"txid=tx-5 digest={digest}"


def test_a_held_passing_verification_classifies_the_removal_without_calling_it_failing():
    payload = verification_bytes("v1", "passed")
    history = held(payload)
    digest = next(iter(history))

    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, history)

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "removal-classified"]
    assert result.findings[1].detail == f"txid=tx-5 digest={digest} kind=verification verdict=passed"


def test_a_held_verification_whose_facet_does_not_validate_says_so(tmp_path):
    node = Node(
        id="verification:v1",
        uid="0" * 32,
        kind="verification",
        title="a held copy",
        facets={"verification": {"assessment": "assessment:a1", "scope": "invented", "verdict": "failed"}},
    )
    history = held(node_to_markdown(node).encode("utf-8"))
    digest = next(iter(history))

    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, history)

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "removal-classified"]
    classified = result.findings[1]
    assert classified.detail == f"txid=tx-5 digest={digest} kind=verification verdict=unreadable"
    assert "no verdict is read" in classified.message


def test_a_classification_speaks_about_the_held_copy_and_not_the_removed_bytes():
    # Path matching cannot establish that the *removed* record was not a
    # failing verification: the copy in hand may be another version of it.
    passing = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, held(verification_bytes("v1", "passed")))
    failing = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, held(verification_bytes("v1", "failed")))

    for result in (passing, failing):
        assert result.findings[1].message.startswith("a held copy filed under this digest claims the removed path")
    assert "the removed record" not in passing.findings[1].message


def test_history_naming_another_record_leaves_the_classification_absent():
    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, held(verification_bytes("v9", "failed")))

    assert [finding.code for finding in result.findings] == ["record-removed"]


def test_two_held_copies_of_one_path_do_not_resolve():
    history = held(verification_bytes("v1", "failed"), verification_bytes("v1", "passed"))

    result = verify.replay(REMOVED, SURVIVING_DISK, ABSENT, history)

    assert [finding.code for finding in result.findings] == ["record-removed"]


def test_a_creation_is_not_a_removal():
    assert verify.replay(CREATED, MATCHING_DISK, ABSENT, held(verification_bytes("v1", "failed"))).findings == ()


# --- the history input ---------------------------------------------------


def test_a_well_formed_history_validates():
    assert verify.validate_history(held(b"a record")) is None


@pytest.mark.parametrize(
    "key",
    [
        "a" * 64,
        "sha256:short",
        "sha256:" + "A" * 64,
        "sha1:" + "a" * 40,
        "sha256:" + "a" * 65,
        # A key whose form is right up to a trailing newline is malformed, and
        # says so: `$` would have matched before it.
        "sha256:" + "a" * 64 + "\n",
    ],
)
def test_a_malformed_history_key_refuses(key):
    with pytest.raises(ValueError, match="is not a content hash"):
        verify.validate_history({key: b"a record"})


def test_a_key_its_bytes_do_not_hash_to_refuses():
    with pytest.raises(ValueError):
        verify.validate_history({f"sha256:{hashlib.sha256(b'one').hexdigest()}": b"another"})


def test_a_history_value_that_is_not_bytes_refuses():
    with pytest.raises(ValueError):
        verify.validate_history({f"sha256:{hashlib.sha256(b'one').hexdigest()}": "one"})  # pyright: ignore[reportArgumentType]


def test_replay_refuses_a_corrupt_history_rather_than_naming_a_digest_it_never_checked():
    with pytest.raises(ValueError):
        verify.replay(REMOVED, SURVIVING_DISK, ABSENT, {"sha256:nope": b"a record"})


# --- cut 8's declarations, over chains the engine itself calls well formed ---
#
# Cut 8 §5's obligation 1: the chains below are real directories of canonical
# entry envelopes, built by `test_world_log_codecs`'s catalogued builders and
# read back through the production seam's detached inspection, so
# `inspect_chain` itself is what says they are well formed. The `Opaque` arms
# above stay the unit arms for replay's own comparison rule; these are the
# declarations, and their states are the engine's own.


def cut8_disk(chain: Chain) -> tuple[tuple[str, object], ...]:
    return capture_at(chain.root, *chain.paths)


def cut8_view(chain: Chain) -> WellFormedView:
    view = inspected(chain.root)
    assert type(view) is WellFormedView, f"the engine calls this fabrication {type(view).__name__}"
    return view


def cut8_anchor(chain: Chain, head: str) -> verify.RegistryCarrier:
    return verify.RegistryCarrier.from_record(
        LogHeadRecord(CorpusSubject(CUT8_CORPUS_ID), chain.digests[0], head, AnchorActOrigin("keith"))
    )


def cut8_judge(chain: Chain, *carriers: verify.ObserverCarrier) -> verify.LogReport:
    return verify.evaluate_log(
        CorpusSubject(CUT8_CORPUS_ID),
        cut8_view(chain),
        verify.ObserverSet(carriers),
        cut8_disk(chain),
        (),
        None,
        ENGINE_ABSENT,
        science_root._log_seam().state_facts,
        None,
    )


# --- L2: settlement gates every absence test ---------------------------------


def test_rolled_back_creation_absence_is_not_refuted(tmp_path):
    """L2u1. A registered creation that **rolled back**: the record's absence is
    not refuted, because a rolled-back settlement is no transition at all.

    Cut 8 §5's obligation 2 is asserted before anything is evaluated — the
    fabricated entry is genuinely `settled(rolled-back)` and the path it would
    have created is genuinely absent from disk. A refusal before registration,
    or a missing settlement, would make this arm vacuous: it would then be
    asserting that a chain saying nothing implies nothing.
    """
    chain = rolled_back_creation(tmp_path)
    view = cut8_view(chain)
    (creation,) = [
        entry
        for entry in view.entries
        if type(entry) is RegisteredEntryView and RECORD_PATH in dict(entry.final)
    ]
    settlements = [
        entry
        for entry in view.entries
        if type(entry) is SettledEntryView and entry.registration == creation.digest
    ]
    assert [entry.committed for entry in settlements] == [False]
    assert not (chain.root / RECORD_PATH).exists()
    disk = cut8_disk(chain)
    assert dict(disk)[RECORD_PATH] == ENGINE_ABSENT

    result = verify.replay(view, disk, ENGINE_ABSENT, None)
    report = cut8_judge(chain, cut8_anchor(chain, chain.tip))

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())
    assert report.outcome == "validated"
    assert report.findings == ()


def test_committed_creation_raw_deleted_is_refuted(tmp_path):
    """L2u2. A **committed** creation whose record is then raw-deleted → refuted
    at replay, the disagreement naming the head state of the deleted path.

    The contrast with L2u1 is the whole claim: the same absent path is innocent
    under a rolled-back settlement and refuting under a committed one, so it is
    the settlement — never the disk — that gates the absence test.
    """
    chain = populated_corpus(tmp_path)
    view = cut8_view(chain)
    assert (chain.root / RECORD_PATH).exists()
    settled = [
        entry
        for entry in view.entries
        if type(entry) is SettledEntryView and entry.committed
    ]
    assert len(settled) == 2

    (chain.root / RECORD_PATH).unlink()
    disk = cut8_disk(chain)
    result = verify.replay(view, disk, ENGINE_ABSENT, None)
    report = cut8_judge(chain, cut8_anchor(chain, chain.tip))

    assert result.refuted
    assert result.disagreements == (f"head:{RECORD_PATH}",)
    assert report.outcome == "refuted"
    assert [finding.code for finding in report.findings] == ["replay-disagreement"]


# --- L5: the unanchored tail is the pinned residue ---------------------------


def test_consistent_tail_rewrite_beyond_anchor_validates(tmp_path):
    """L5u1, the pinned negative. The tail beyond the maximal anchor rewritten
    into a self-consistent alternative, **and the affected registered surface
    rewritten to match** → `validated`, undetected. The bound is anchor cadence,
    and the negative is the claim.

    Cut 8 §5's obligation 3 is asserted before the verdict is read: at least one
    entry beyond the anchor was rewritten, and the entry envelopes differ
    byte-wise from the ones they replaced. An empty rewrite would validate
    vacuously.
    """
    chain = rewritten_tail(tmp_path)
    view = cut8_view(chain)
    beyond = tuple(entry.digest for entry in view.entries)[view.entries.index(view.genesis) + 3 :]
    assert len(chain.added) >= 1
    assert len(chain.added) == len(chain.replaced)
    assert set(chain.added).isdisjoint(chain.replaced)
    assert chain.removed and chain.anchor not in chain.removed
    assert len(beyond) == len(chain.added)

    report = cut8_judge(chain, cut8_anchor(chain, chain.anchor))

    assert report.outcome == "validated"
    assert report.findings == ()
    assert report.anchored_through == chain.anchor


def test_unanchored_tail_extent_covers_the_rewrite(tmp_path):
    """L5u2. The report's unanchored-tail extent covers the rewritten span
    exactly — the residue is stated, never left for a caller to infer."""
    chain = rewritten_tail(tmp_path)
    view = cut8_view(chain)
    digests = tuple(entry.digest for entry in view.entries)
    rewritten = digests[digests.index(chain.anchor) + 1 :]
    assert len(rewritten) == len(chain.added)

    report = cut8_judge(chain, cut8_anchor(chain, chain.anchor))

    assert report.outcome == "validated"
    assert report.unanchored_tail == rewritten
    assert chain.anchor not in report.unanchored_tail


# --- L12: one state vocabulary, and the log path is bookkeeping --------------


def test_all_four_state_classes_round_trip(tmp_path):
    """L12u1. Each typed state class — **absence, directory, symlink target,
    mode** — round-trips through registration fingerprints and replay.

    Cut 8 §5's obligation 6: all four, asserted as four distinct engine classes
    over one committed transaction. A subset pass is malformed declaration
    content, not a pass, so the class set is compared for equality rather than
    for containment. Each is then shown load-bearing: rotating the four states
    among the four paths refutes at every one of them, and the two clauses the
    row names by their *content* — a symlink's target and a file's mode — refute
    on their own.
    """
    chain = four_state_classes(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)
    assert {type(state).__name__ for _path, state in disk} == {
        "AbsentState",
        "DirectoryState",
        "FileState",
        "SymlinkState",
    }

    (created,) = [entry for entry in view.entries if type(entry) is RegisteredEntryView]
    assert created.final == disk
    assert verify.replay(view, disk, ENGINE_ABSENT, None) == verify.ReplayResult(False, (), ())

    for index, (path, _state) in enumerate(disk):
        rotated = disk[:index] + ((path, disk[(index + 1) % len(disk)][1]),) + disk[index + 1 :]
        result = verify.replay(view, rotated, ENGINE_ABSENT, None)
        assert result.refuted, path
        assert result.disagreements == (f"head:{path}",)

    (chain.root / "link").unlink()
    (chain.root / "link").symlink_to("d")
    (chain.root / "f.txt").chmod(0o755)
    moved = cut8_disk(chain)
    result = verify.replay(view, moved, ENGINE_ABSENT, None)
    assert result.refuted
    assert set(result.disagreements) == {"head:link", "head:f.txt"}


def test_log_appends_are_not_recursively_registered(tmp_path):
    """L12u3. Appending the log is not itself registered.

    Three facts, and together they close the cooperative side: a transaction's
    registered paths are derived from **the plan's own operation paths** and from
    nothing else; no cooperative plan can name a path under the engine's
    reserved sigil, and the chain and staging leaves both live under it; and the
    registered-surface projection never claims them, over a root that really
    holds a chain.

    The first is the load-bearing link and is read out of the composition root's
    own source: if the registration set were assembled from anywhere but the
    plan, banning the sigil in the plan would ban nothing.

    A fourth reading — that the chain's own entries name only surface paths — is
    deliberately **not** counted: this fixture authored those entries, so it
    would be re-reading its own construction. The engine's appending is atoms's
    certified interior (cut 8 §2), and that is where it is certified.
    """
    submitted = inspect.getsource(science_root.DurableExecutor.execute)
    assert "registered_paths=tuple(dict.fromkeys(operation.path for operation in plan))" in submitted

    chain = settled_corpus(tmp_path)
    assert (chain.root / CHAIN_LEAF).is_dir()
    assert CHAIN_LEAF.startswith(SCRATCH_SIGIL)
    assert STAGING_LEAF.startswith(SCRATCH_SIGIL)
    assert verify.registered_surface_paths(chain.root, "corpus") == (MANIFEST_PATH,)

    with pytest.raises(PlanRefusedError, match="engine-reserved leaf"):
        science_root._refuse_malformed([CreateOp(path=f"{CHAIN_LEAF}/{'a' * 64}", content=b"forged")])


# --- L13: logged is not permitted --------------------------------------------


def test_cooperative_verification_removal_is_in_timeline_with_finding(tmp_path):
    """L13u1. A log-visible removal of a verification via a cooperative act is
    **in the replayed timeline** *and* draws the policy finding naming the
    deleted record. Occurrence is not authorization, so the removal is a
    finding beside a verdict that does not refute."""
    chain = removed_record(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)
    assert not (chain.root / RECORD_PATH).exists()

    removals = [
        entry
        for entry in view.entries
        if type(entry) is RegisteredEntryView and dict(entry.final).get(RECORD_PATH) == ENGINE_ABSENT
    ]
    assert len(removals) == 1
    settlements = [
        entry
        for entry in view.entries
        if type(entry) is SettledEntryView and entry.registration == removals[0].digest
    ]
    assert [entry.committed for entry in settlements] == [True]

    result = verify.replay(view, disk, ENGINE_ABSENT, None)

    assert not result.refuted
    assert [(finding.code, finding.ref, finding.detail) for finding in result.findings] == [
        ("record-removed", RECORD_PATH, f"txid={removals[0].txid}")
    ]
    assert result.findings[0].severity == "warning"


def test_failing_classification_resolves_through_history_naming_digest(tmp_path):
    """L13u2. Where the supplied `history` bytes resolve, the removal is
    classified as a *failing* verification's and the finding names the matched
    digest.

    **R16, stated here because L13 is partial for it:** the match is by *path*,
    not by digest — the seam exposes no state→digest accessor, so the pass
    decodes the held bytes, derives the path the copy's identity claims, and
    matches the removed path. The finding therefore speaks about the held copy
    and never about the removed bytes, and a held copy of another version of the
    same record could misclassify a removal in either direction.
    """
    chain = removed_record(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)
    history = held(verification_bytes("v1", "failed"))
    digest = next(iter(history))

    result = verify.replay(view, disk, ENGINE_ABSENT, history)

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "failing-verification-removed"]
    classified = result.findings[1]
    assert classified.severity == "error"
    assert classified.ref == RECORD_PATH
    assert classified.detail.endswith(f"digest={digest}")
    assert classified.message.startswith("a held copy filed under this digest claims the removed path")
    assert "the removed record" not in classified.message


def test_without_history_deletion_detected_classification_absent(tmp_path):
    """L13u3. With no copy held the deletion is **still detected** and the
    semantic classification is honestly **absent** — never guessed from the
    entry, which retains a state digest and not a verdict.

    The two other ways the evidence fails to resolve are the same answer: a
    history naming another record, and two copies claiming one path (R16's
    weakened match refuses to choose between them).
    """
    chain = removed_record(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)

    for history in (
        None,
        held(verification_bytes("v9", "failed")),
        held(verification_bytes("v1", "failed"), verification_bytes("v1", "passed")),
    ):
        result = verify.replay(view, disk, ENGINE_ABSENT, history)

        assert not result.refuted
        assert [finding.code for finding in result.findings] == ["record-removed"]
        assert result.findings[0].ref == RECORD_PATH


# --- D9: history evidence is validated ---------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "a" * 64,
        "sha256:short",
        "sha256:" + "A" * 64,
        "sha1:" + "a" * 40,
        "sha256:" + "a" * 65,
        "sha256:" + "a" * 64 + "\n",
    ],
)
def test_history_validation_refusals_and_digest_named_findings(tmp_path, key):
    """D9. A malformed `history` key, or bytes that do not hash to their key,
    **refuses the act**; keys are exactly `sha256:<64 lowercase hex>`; and every
    classified finding names the matched digest (spec §5.3)."""
    with pytest.raises(ValueError, match="is not a content hash"):
        verify.validate_history({key: b"a record"})
    assert verify.CONTENT_HASH.pattern == r"^sha256:[0-9a-f]{64}$"
    assert verify.validate_history(held(b"a record")) is None
    with pytest.raises(ValueError):
        verify.validate_history({f"sha256:{hashlib.sha256(b'one').hexdigest()}": b"another"})

    chain = removed_record(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)

    # The refusal reaches the act itself, before any digest is named.
    with pytest.raises(ValueError):
        verify.replay(view, disk, ENGINE_ABSENT, {key: b"a record"})

    # And every classification that *is* produced names the digest it matched.
    for verdict, code in (("failed", "failing-verification-removed"), ("passed", "removal-classified")):
        history = held(verification_bytes("v1", verdict))
        matched = next(iter(history))
        result = verify.replay(view, disk, ENGINE_ABSENT, history)
        assert [finding.code for finding in result.findings] == ["record-removed", code]
        assert f"digest={matched}" in result.findings[1].detail
