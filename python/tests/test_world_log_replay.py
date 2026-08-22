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
from pathlib import Path

import pytest
from nodes.core.frontmatter import node_to_markdown
from nodes.core.ids import KIND_RE, SLUG_RE
from nodes.core.node import Node
from nodes.core.store import Store

from science.world import verify
from science.world.epoch import CURRENT_POINTER, EPOCH_MEMBERS
from science.world.logmodel import (
    GenesisEntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)
from science.world.rules import _MEMBER_NAME

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
    return RegisteredEntryView(digest=digest, txid=txid, initial=initial, final=final, fulfills=None)


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
    with pytest.raises(ValueError):
        verify.registered_surface_paths(tmp_path, "store")  # pyright: ignore[reportArgumentType]


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
