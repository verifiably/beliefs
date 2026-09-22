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
from nodes.core.write_plan import CreateOp
from test_world_log_codecs import (
    CUT8_CORPUS_ID,
    Chain,
    _record_state,
    capture_at,
    four_state_classes,
    inspected,
    populated_corpus,
    rewritten_tail,
    rolled_back_creation,
    settled_corpus,
)
from test_world_log_codecs import MANIFEST as MANIFEST_PATH
from test_world_log_codecs import RECORD as RECORD_PATH

from beliefs import root as science_root
from beliefs.errors import PreimageMismatch
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


# --- the seam's codec over the opaque stand-ins ----------------------------

FAILED_V1 = verification_bytes("v1", "failed")
"""What `RECORD`'s bytes are, as far as the codec below is concerned: the
removed state's declared digest is this payload's, so a held copy or a
preimage of exactly these bytes resolves and any other bytes do not."""


def opaque_facts(state: object) -> tuple[tuple[str, str], ...]:
    """The seam's `state_facts` over the inert stand-ins, by identity.

    Replay may hand a state to the seam's codec and read the codec's answer;
    it may not read the state itself (`Opaque` still raises on every
    attribute). `ABSENT` renders absent; `RECORD` renders as the file whose
    bytes are `FAILED_V1`; every other state is a file with no digest a test
    holds bytes for.
    """
    if state is ABSENT:
        return (("kind", "absent"),)
    if state is RECORD:
        return (
            ("kind", "file"),
            ("content_hash", hashlib.sha256(FAILED_V1).hexdigest()),
            ("mode", "0o644"),
            ("byte_len", str(len(FAILED_V1))),
        )
    label = state.__dict__["_label"]
    return (
        ("kind", "file"),
        ("content_hash", hashlib.sha256(label.encode()).hexdigest()),
        ("mode", "0o644"),
        ("byte_len", "0"),
    )


SYMLINKED = Opaque("verification/v1.md@symlink")


def symlink_facts(state: object) -> tuple[tuple[str, str], ...]:
    if state is SYMLINKED:
        return (("kind", "symlink"), ("target", "elsewhere"))
    return opaque_facts(state)


PRODUCTION_FACTS = science_root._log_seam().state_facts
"""For the chains fabricated over real engine states (`removed_record` and
its siblings): the codec the composition root wires."""


def removed_verification(base: Path) -> tuple[Chain, bytes]:
    """`removed_record`'s shape over bytes that *are* a failing verification:
    the manifest committed, the record created, then removed — so the removed
    state's digest is `FAILED_V1`'s and a copy of those bytes resolves."""
    chain = settled_corpus(base)
    chain.anchor = chain.tip
    record = _record_state(chain.root, FAILED_V1)
    chain.transaction("tx-2", ((RECORD_PATH, ENGINE_ABSENT),), ((RECORD_PATH, record),))
    (chain.root / RECORD_PATH).unlink()
    chain.transaction("tx-3", ((RECORD_PATH, record),), ((RECORD_PATH, ENGINE_ABSENT),))
    chain.paths = (MANIFEST_PATH, RECORD_PATH)
    return chain, FAILED_V1


def removals_txid(view) -> str:
    (removal,) = verify.committed_removals(view, ENGINE_ABSENT)
    return removal.txid


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


# --- replay --------------------------------------------------------------


def test_a_committed_history_validates_against_the_disk_it_produced():
    result = verify.replay(CREATED, MATCHING_DISK, ABSENT, None, state_facts=opaque_facts)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_a_raw_delete_refutes():
    result = verify.replay(CREATED, (("corpus.yaml", MANIFEST),), ABSENT, None, state_facts=opaque_facts)

    assert result.refuted
    assert result.disagreements == ("head:verification/v1.md",)


def test_a_raw_create_refutes():
    disk = MATCHING_DISK + (("verification/v2.md", OTHER),)

    result = verify.replay(CREATED, disk, ABSENT, None, state_facts=opaque_facts)

    assert result.refuted
    assert result.disagreements == ("head:verification/v2.md",)


def test_a_rolled_back_creation_is_no_transition():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("b" * 64, "tx-2", (("verification/v2.md", ABSENT),), (("verification/v2.md", OTHER),)),
        settlement("b" * 64, "tx-2", committed=False),
    )

    result = verify.replay(view, (("corpus.yaml", MANIFEST),), ABSENT, None, state_facts=opaque_facts)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_an_unsettled_registration_is_no_transition():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("c" * 64, "tx-3", (("verification/v2.md", ABSENT),), (("verification/v2.md", OTHER),)),
    )

    result = verify.replay(view, (("corpus.yaml", MANIFEST),), ABSENT, None, state_facts=opaque_facts)

    assert result == verify.ReplayResult(refuted=False, disagreements=(), findings=())


def test_an_initial_fingerprint_disagreement_refutes():
    view = chain(
        genesis(("corpus.yaml", MANIFEST)),
        registration("d" * 64, "tx-4", (("corpus.yaml", OTHER),), (("corpus.yaml", RECORD),)),
        settlement("d" * 64, "tx-4", committed=True),
    )

    result = verify.replay(view, (("corpus.yaml", RECORD),), ABSENT, None, state_facts=opaque_facts)

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

    result = verify.replay(view, SURVIVING_DISK, ABSENT, None, state_facts=opaque_facts)

    assert result.refuted
    # The head comparison is skipped — every `head:` entry past a divergence
    # would be a consequence of it — and the first disagreement is the report.
    assert result.disagreements == ("initial:corpus.yaml@tx-4",)
    assert [(finding.code, finding.ref) for finding in result.findings] == [
        ("record-removed", "verification/v1.md"),
        ("removal-unclassified", "verification/v1.md"),
    ]


def test_the_baseline_is_replayed_from_the_genesis():
    view = chain(genesis(("corpus.yaml", MANIFEST)))

    assert not verify.replay(
        view, (("corpus.yaml", MANIFEST),), ABSENT, None, state_facts=opaque_facts
    ).refuted
    assert verify.replay(
        view, (("corpus.yaml", RECORD),), ABSENT, None, state_facts=opaque_facts
    ).disagreements == ("head:corpus.yaml",)


# --- the policy pass -----------------------------------------------------


REMOVED = chain(
    genesis(("corpus.yaml", MANIFEST), ("verification/v1.md", RECORD)),
    registration("e" * 64, "tx-5", (("verification/v1.md", RECORD),), (("verification/v1.md", ABSENT),)),
    settlement("e" * 64, "tx-5", committed=True),
)
SURVIVING_DISK: tuple[tuple[str, object], ...] = (("corpus.yaml", MANIFEST),)
REMOVED_DIGEST = f"sha256:{hashlib.sha256(FAILED_V1).hexdigest()}"


def replayed(
    view=REMOVED,
    disk=SURVIVING_DISK,
    history=None,
    *,
    preimages=verify.NO_PREIMAGES,
    state_facts=opaque_facts,
):
    return verify.replay(view, disk, ABSENT, history, state_facts=state_facts, preimages=preimages)


def test_committed_removals_are_the_declared_absent_finals_of_committed_transitions_in_chain_order():
    rolled = chain(
        genesis(("corpus.yaml", MANIFEST), ("verification/v1.md", RECORD), ("verification/v2.md", OTHER)),
        registration("e" * 64, "tx-5", (("verification/v1.md", RECORD),), (("verification/v1.md", ABSENT),)),
        settlement("e" * 64, "tx-5", committed=False),
        registration("f" * 64, "tx-6", (("verification/v2.md", OTHER),), (("verification/v2.md", ABSENT),)),
        settlement("f" * 64, "tx-6", committed=True),
        registration("d" * 64, "tx-7", (("verification/v1.md", RECORD),), (("verification/v1.md", ABSENT),)),
    )
    assert verify.committed_removals(rolled, ABSENT) == (
        verify.Removal(txid="tx-6", path="verification/v2.md", state=OTHER),
    )
    # A replacement and a creation are not removals.
    assert verify.committed_removals(CREATED, ABSENT) == ()


def test_removed_digest_is_the_file_content_hash_in_history_key_form_and_none_otherwise():
    assert verify.removed_digest(RECORD, opaque_facts) == REMOVED_DIGEST
    assert verify.removed_digest(SYMLINKED, symlink_facts) is None
    assert verify.removed_digest(ABSENT, opaque_facts) is None


def test_a_committed_removal_is_a_finding_even_with_no_history():
    result = replayed()

    assert not result.refuted
    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "removal-unclassified"]
    finding = result.findings[0]
    assert (finding.severity, finding.ref, finding.detail) == ("warning", "verification/v1.md", "txid=tx-5")
    assert finding.message == "a committed transaction removed a registered-surface record"
    absent = result.findings[1]
    assert absent.severity == "warning"
    assert absent.ref == "verification/v1.md"
    assert absent.detail == f"txid=tx-5 digest={REMOVED_DIGEST} preimage=not-consulted"
    assert "the classification is absent" in absent.message


def test_a_held_copy_resolves_by_the_removed_digest_and_classifies_the_removed_bytes():
    result = replayed(history=held(FAILED_V1))

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "failing-verification-removed"]
    classified = result.findings[1]
    assert classified.severity == "error"
    assert classified.ref == "verification/v1.md"
    assert classified.detail == f"txid=tx-5 digest={REMOVED_DIGEST} source=held-copy"
    assert classified.message.startswith("the removed record's bytes, resolved by digest")
    assert "held copy" not in classified.message


def test_a_held_copy_of_another_version_of_the_same_record_resolves_nothing():
    # Same id, so the same claimed path — the R16 misclassification, reversed.
    other_version = verification_bytes("v1", "passed")

    result = replayed(history=held(other_version))

    assert [finding.code for finding in result.findings] == ["record-removed", "removal-unclassified"]
    assert result.findings[1].detail == f"txid=tx-5 digest={REMOVED_DIGEST} preimage=not-consulted"
    assert hashlib.sha256(other_version).hexdigest() not in result.findings[1].detail


def test_two_held_copies_resolve_from_the_matching_one_alone():
    result = replayed(history=held(FAILED_V1, verification_bytes("v1", "passed")))

    assert [finding.code for finding in result.findings] == ["record-removed", "failing-verification-removed"]
    assert f"digest={REMOVED_DIGEST}" in result.findings[1].detail


def test_a_preimage_resolves_and_is_named_as_the_source():
    preimages = {("tx-5", "verification/v1.md"): verify.PreimageRead(FAILED_V1)}

    result = replayed(preimages=preimages)

    assert [finding.code for finding in result.findings] == ["record-removed", "failing-verification-removed"]
    assert result.findings[1].detail == f"txid=tx-5 digest={REMOVED_DIGEST} source=preimage"


def test_a_preimage_and_a_held_copy_together_classify_once_from_the_preimage():
    preimages = {("tx-5", "verification/v1.md"): verify.PreimageRead(FAILED_V1)}

    result = replayed(history=held(FAILED_V1), preimages=preimages)

    assert [finding.code for finding in result.findings] == ["record-removed", "failing-verification-removed"]
    assert result.findings[1].detail.endswith("source=preimage")


def test_a_preimage_that_does_not_hash_to_the_declared_digest_refuses_before_any_finding():
    preimages = {("tx-5", "verification/v1.md"): verify.PreimageRead(verification_bytes("v1", "passed"))}

    with pytest.raises(PreimageMismatch, match="tx-5"):
        replayed(preimages=preimages)


def test_an_unavailable_preimage_is_the_absence_finding_with_the_engine_reason():
    preimages = {
        ("tx-5", "verification/v1.md"): verify.PreimageUnavailable(
            "root lifecycle state read-only-serviceable does not grant writability"
        )
    }

    result = replayed(preimages=preimages)

    assert [finding.code for finding in result.findings] == ["record-removed", "removal-unclassified"]
    absent = result.findings[1]
    assert absent.detail == f"txid=tx-5 digest={REMOVED_DIGEST} preimage=refused"
    assert "read-only-serviceable does not grant writability" in absent.message


def test_an_unavailable_preimage_still_resolves_through_a_held_copy():
    preimages = {("tx-5", "verification/v1.md"): verify.PreimageUnavailable("refused")}

    result = replayed(history=held(FAILED_V1), preimages=preimages)

    assert [finding.code for finding in result.findings] == ["record-removed", "failing-verification-removed"]
    assert result.findings[1].detail.endswith("source=held-copy")


def test_a_removed_pre_state_that_is_not_a_file_has_no_digest_and_is_not_classified():
    view = chain(
        genesis(("corpus.yaml", MANIFEST), ("verification/v1.md", SYMLINKED)),
        registration(
            "e" * 64,
            "tx-5",
            (("verification/v1.md", SYMLINKED),),
            (("verification/v1.md", ABSENT),),
        ),
        settlement("e" * 64, "tx-5", committed=True),
    )

    result = replayed(view, history=held(FAILED_V1), state_facts=symlink_facts)

    assert [finding.code for finding in result.findings] == ["record-removed", "removal-unclassified"]
    assert result.findings[1].detail == "txid=tx-5 digest=none preimage=not-consulted"


@pytest.mark.parametrize("source", ["preimage", "held-copy"])
def test_the_classification_table_over_both_channels(source):
    def resolved(payload: bytes):
        digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        facts = lambda state: (
            (
                ("kind", "file"),
                ("content_hash", digest.removeprefix("sha256:")),
                ("mode", "0o644"),
                ("byte_len", str(len(payload))),
            )
            if state is RECORD
            else opaque_facts(state)
        )
        if source == "preimage":
            return (
                replayed(
                    preimages={("tx-5", "verification/v1.md"): verify.PreimageRead(payload)},
                    state_facts=facts,
                ),
                digest,
            )
        return replayed(history={digest: payload}, state_facts=facts), digest

    passing, digest = resolved(verification_bytes("v1", "passed"))
    assert passing.findings[1].code == "removal-classified"
    assert passing.findings[1].detail == (
        f"txid=tx-5 digest={digest} source={source} kind=verification verdict=passed"
    )

    unreadable = Node(
        id="verification:v1",
        uid="0" * 32,
        kind="verification",
        title="a held copy",
        facets={"verification": {"assessment": "assessment:a1", "scope": "invented", "verdict": "failed"}},
    )
    result, digest = resolved(node_to_markdown(unreadable).encode("utf-8"))
    assert result.findings[1].detail == (
        f"txid=tx-5 digest={digest} source={source} kind=verification verdict=unreadable"
    )
    assert "no verdict is read" in result.findings[1].message

    discussion = Node(id="discussion:v1", uid="0" * 32, kind="discussion", title="not a verification", facets={})
    result, digest = resolved(node_to_markdown(discussion).encode("utf-8"))
    assert result.findings[1].detail == f"txid=tx-5 digest={digest} source={source} kind=discussion"
    assert result.findings[1].severity == "warning"

    result, digest = resolved(b"\x00not a record\n")
    assert result.findings[1].detail == f"txid=tx-5 digest={digest} source={source} kind=none"
    assert "not a Science record" in result.findings[1].message

    for result in (passing,):
        assert "held copy" not in result.findings[1].message


def test_a_creation_is_not_a_removal():
    assert replayed(CREATED, MATCHING_DISK, held(FAILED_V1)).findings == ()


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
        verify.replay(
            REMOVED,
            SURVIVING_DISK,
            ABSENT,
            {"sha256:nope": b"a record"},
            state_facts=opaque_facts,
        )


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

    result = verify.replay(view, disk, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS)
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
    result = verify.replay(view, disk, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS)
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
    assert verify.replay(view, disk, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS) == verify.ReplayResult(
        False, (), ()
    )

    for index, (path, _state) in enumerate(disk):
        rotated = disk[:index] + ((path, disk[(index + 1) % len(disk)][1]),) + disk[index + 1 :]
        result = verify.replay(view, rotated, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS)
        assert result.refuted, path
        assert result.disagreements == (f"head:{path}",)

    (chain.root / "link").unlink()
    (chain.root / "link").symlink_to("d")
    (chain.root / "f.txt").chmod(0o755)
    moved = cut8_disk(chain)
    result = verify.replay(view, moved, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS)
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
    """L13u1 (cut 8, superseded by cut 37's L13-a). A log-visible removal of a
    verification via a cooperative act is **in the replayed timeline** *and*
    draws the policy finding naming the deleted record."""
    chain, _removed_bytes = removed_verification(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)
    assert not (chain.root / RECORD_PATH).exists()

    removals = [
        entry
        for entry in view.entries
        if type(entry) is RegisteredEntryView and dict(entry.final).get(RECORD_PATH) == ENGINE_ABSENT
    ]
    assert len(removals) == 1

    result = verify.replay(view, disk, ENGINE_ABSENT, None, state_facts=PRODUCTION_FACTS)

    assert not result.refuted
    assert [(finding.code, finding.ref, finding.detail) for finding in result.findings[:1]] == [
        ("record-removed", RECORD_PATH, f"txid={removals[0].txid}")
    ]
    assert result.findings[0].severity == "warning"
    assert result.findings[1].code == "removal-unclassified"


def test_failing_classification_resolves_through_history_naming_digest(tmp_path):
    """L13u2 (cut 8, superseded by cut 37's L13-b/L13-c). Where the supplied
    `history` bytes resolve **by the removed state's digest**, the removal is
    classified as a *failing* verification's and the finding names that digest.
    R16's path match is gone: the copy that resolves is the copy of the removed
    bytes, and the finding speaks about them."""
    chain, removed_bytes = removed_verification(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)
    history = held(removed_bytes)
    digest = next(iter(history))

    result = verify.replay(view, disk, ENGINE_ABSENT, history, state_facts=PRODUCTION_FACTS)

    codes = [finding.code for finding in result.findings]
    assert codes == ["record-removed", "failing-verification-removed"]
    classified = result.findings[1]
    assert classified.severity == "error"
    assert classified.ref == RECORD_PATH
    assert classified.detail == f"txid={removals_txid(view)} digest={digest} source=held-copy"
    assert classified.message.startswith("the removed record's bytes, resolved by digest")


def test_without_history_deletion_detected_classification_absent(tmp_path):
    """L13u3 (cut 8, superseded by cut 37's L13-d). With no copy held the
    deletion is **still detected** and the classification is honestly
    **absent** — stated by `removal-unclassified`, never guessed from a copy of
    another record or another version."""
    chain, _removed_bytes = removed_verification(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)

    for history in (None, held(verification_bytes("v9", "failed")), held(verification_bytes("v1", "passed"))):
        result = verify.replay(view, disk, ENGINE_ABSENT, history, state_facts=PRODUCTION_FACTS)

        assert not result.refuted
        assert [finding.code for finding in result.findings] == ["record-removed", "removal-unclassified"]
        assert result.findings[1].ref == RECORD_PATH
        assert result.findings[1].detail.endswith("preimage=not-consulted")


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

    chain, removed_bytes = removed_verification(tmp_path)
    view = cut8_view(chain)
    disk = cut8_disk(chain)

    # The refusal reaches the act itself, before any digest is named.
    with pytest.raises(ValueError):
        verify.replay(view, disk, ENGINE_ABSENT, {key: b"a record"}, state_facts=PRODUCTION_FACTS)

    # And every classification that *is* produced names the digest it matched.
    for payload, code in ((removed_bytes, "failing-verification-removed"), (verification_bytes("v1", "passed"), "removal-unclassified")):
        history = held(payload)
        matched = next(iter(history))
        result = verify.replay(view, disk, ENGINE_ABSENT, history, state_facts=PRODUCTION_FACTS)
        assert [finding.code for finding in result.findings] == ["record-removed", code]
        if code == "failing-verification-removed":
            assert f"digest={matched}" in result.findings[1].detail
        else:
            assert result.findings[1].detail.endswith("preimage=not-consulted")
