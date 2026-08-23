"""The audit boundary and the ordered-cuts predicate (design §6.1, §6.3, §7).

**Audit is the evaluator plus a report and nothing else.** It takes the world
*configuration* rather than an opened `World`, and an **explicit** target root,
and those two choices are what the arms below turn on: the act has to stay
callable on exactly the worlds `open_world` refuses, and it must reach the root
whose `corpus.yaml` was rewritten to another id — which a manifest-based lookup
by definition cannot find.

**The seam is a stand-in and the locks are real.** As in
`test_world_anchor_act`, every arm builds a `LogSeam` whose inspection and
capture answer from tables while `world_lock` and `corpus_lock` are the
production lookups, so an arm claiming a lock was held claims it about the very
object a writer or an opened `World` contends for. The one exception is the
`LogEvidenceRefused` arm at the foot of the module, which drives the production
seam itself with the engine command raising.

**Why the states are inert objects.** Replay compares path states by equality
and by nothing else, so the arms state a disk with `Opaque` values keyed by
path: a chain fabricated over the projection of a root agrees with a capture of
that same root exactly when nothing moved between them.
"""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml
from atoms.chain.errors import ChainStateInvalid
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads, corpus_at
from test_world_epoch import admitted_world, publish
from test_world_log_replay import Opaque

from science import root as science_root
from science.corpus import _operation_lock_for, _root_state_for
from science.errors import (
    AuditTargetUnconfigured,
    BuildContended,
    EpochUnknown,
    LogEvidenceRefused,
    StoreSubjectUnsupported,
    WorldIdMismatch,
)
from science.world import anchors, epoch, logmodel, registry, verify

WORLD_ID = "f" * 32
OTHER_WORLD_ID = "e" * 32


def digest(label: str) -> str:
    """A stand-in chain digest with the *form* a chain digest has — the
    64-character lowercase hexadecimal an entry envelope hashes to. Derived
    from a label so an arm can name the same entry twice and mean it."""
    return hashlib.sha256(label.encode()).hexdigest()


# --- the disk, as states that answer equality and nothing else ----------------

_STATES: dict[str, object] = {}
ABSENT = Opaque("absent")


def state(path: str) -> object:
    """One state object per path, so a chain fabricated over a projection and a
    capture of the same projection compare equal."""
    return _STATES.setdefault(path, Opaque(path))


def held_verification(slug: str, verdict: str) -> bytes:
    node = Node(
        id=f"verification:{slug}",
        uid="0" * 32,
        kind="verification",
        title="a held copy",
        facets={"verification": {"assessment": "assessment:a1", "scope": "clean-environment", "verdict": verdict}},
    )
    return node_to_markdown(node).encode("utf-8")


def keys_of(value: object) -> set[str]:
    """Every mapping key anywhere inside a parsed document."""
    if isinstance(value, dict):
        return set(map(str, value)) | {key for item in value.values() for key in keys_of(item)}
    if isinstance(value, list):
        return {key for item in value for key in keys_of(item)}
    return set()


# --- the seam ------------------------------------------------------------------


class Inspections:
    """The seam's `inspect_registered`, answering from a table per root.

    Per root rather than one answer for all: the audit must inspect the root it
    was *given*, and an arm configuring two roots could not tell that apart from
    a stub that answered every root alike.
    """

    def __init__(self) -> None:
        self.views: dict[Path, logmodel.ChainView] = {}
        self.roots: list[Path] = []
        self.probe: object = None

    def set(self, root: Path, view: logmodel.ChainView) -> None:
        self.views[Path(root).resolve()] = view

    def __call__(self, root: Path) -> logmodel.ChainView:
        resolved = Path(root).resolve()
        self.roots.append(resolved)
        if callable(self.probe):
            self.probe(resolved)
        view = self.views.get(resolved)
        assert view is not None, f"{resolved}: this arm set no chain for that root"
        return view


class Captures:
    """The seam's `capture`: exactly the named paths, in the caller's order.

    `overrides` is how an arm states a disk that disagrees with the timeline;
    every other path answers the one state object it is keyed by.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[Path, tuple[str, ...]]] = []
        self.overrides: dict[str, object] = {}
        self.probe: object = None

    def __call__(self, root: Path, paths: tuple[str, ...]) -> tuple[tuple[str, object], ...]:
        self.calls.append((Path(root).resolve(), paths))
        if callable(self.probe):
            self.probe(Path(root).resolve())
        return tuple((path, self.overrides.get(path, state(path))) for path in paths)


def unreached_detached(root: Path) -> logmodel.ChainView:
    raise AssertionError(f"{root}: audit consumes registered mode, never detached (§2.1)")


def unreached_head(root: Path) -> logmodel.ChainHead:
    raise AssertionError(f"{root}: these acts inspect a chain — they do not read a head")


def make_seam(inspections: Inspections, captures: Captures) -> verify.LogSeam:
    """A seam over the production locks, with inspection and capture stubbed."""

    @contextmanager
    def world_lock(root: Path) -> Iterator[None]:
        with registry._world_lock_for(Path(root)):
            yield

    return verify.LogSeam(
        inspect_registered=inspections,
        inspect_detached=unreached_detached,
        capture=captures,
        read_head=unreached_head,
        absent_state=ABSENT,
        world_lock=world_lock,
        corpus_lock=_operation_lock_for,
    )


# --- chain fabrication over a real projection ----------------------------------


def genesis_entry(payload: bytes, *, label: str = "genesis") -> logmodel.GenesisEntryView:
    """A genesis with the **empty** baseline §1.3 requires: both Science
    initializers register `()`, so a populated baseline is a chain no Science
    path mints — and the evaluator calls one malformed."""
    return logmodel.GenesisEntryView(digest=digest(label), payload=payload, baseline=())


def chain(head: logmodel.GenesisEntryView, *rest: logmodel.EntryView) -> logmodel.WellFormedView:
    """R10's shape: the genesis is `entries[0]`, the same object."""
    entries = (head, *rest)
    return logmodel.WellFormedView(genesis=head, entries=entries, tip=entries[-1].digest, pending=())


def registration(
    entry_digest: str,
    txid: str,
    initial: tuple[tuple[str, object], ...],
    final: tuple[tuple[str, object], ...],
) -> logmodel.RegisteredEntryView:
    return logmodel.RegisteredEntryView(
        digest=entry_digest, txid=txid, initial=initial, final=final, fulfills=None
    )


def settlement(
    entry_digest: str, registration_digest: str, txid: str, *, committed: bool
) -> logmodel.SettledEntryView:
    return logmodel.SettledEntryView(
        digest=entry_digest, txid=txid, registration=registration_digest, committed=committed
    )


def surfaced(root: Path, kind: verify.RootKind, payload: bytes) -> logmodel.WellFormedView:
    """The chain that brought `root`'s present surface into existence.

    The empty genesis §1.3 requires, then one committed transaction creating
    every path the projection presently finds — which is the smallest timeline
    that agrees with a populated root, and the shape every arm wanting a
    verdict over one starts from.

    **The timeline is derived from the surface as the arm has already damaged
    it**, so replay cannot disagree by construction: an arm calling this after
    deleting or rewriting a file is stating a chain that cooperatively logged
    that change, and a `validated` outcome beneath it is evidence about the
    *claim* being judged, never evidence that the change was undetectable.
    Replay's own detection is `test_world_log_replay`'s to arm.
    """
    paths = verify.registered_surface_paths(root, kind)
    created = registration(
        digest(f"creation:{root}"),
        "tx-0",
        tuple((path, ABSENT) for path in paths),
        tuple((path, state(path)) for path in paths),
    )
    return chain(
        genesis_entry(payload, label=f"genesis:{root}"),
        created,
        settlement(digest(f"settled:{root}"), created.digest, "tx-0", committed=True),
    )


def publication(entry_digest: str, txid: str, packaging_identity: str) -> logmodel.RegisteredEntryView:
    """One epoch publication's registration, as the world chain carries it.

    The member named is the one the predicate reads on the other side — an
    epoch's `anchors.yaml` — so a layout change that stopped publishing it
    fails both halves of the predicate together rather than one silently.
    """
    path = f"epochs/{packaging_identity}/anchors.yaml"
    return registration(entry_digest, txid, ((path, ABSENT),), ((path, state(path)),))


# --- the roots and the act ------------------------------------------------------


def corpus_root(tmp_path: Path, corpus_id: str = ALPHA, *, name: str = "carrier") -> Path:
    return corpus_at(tmp_path / name, corpus_id)


def world_root(tmp_path: Path, *, mirrored: str = WORLD_ID, name: str = "world") -> Path:
    root = tmp_path / name
    root.mkdir(parents=True, exist_ok=True)
    (root / "world.yaml").write_bytes(registry._world_mirror_bytes(mirrored))
    return root


def config_for(
    tmp_path: Path, *corpus_roots: Path, world_id: str = WORLD_ID, name: str = "world"
) -> registry.WorldConfig:
    return registry.WorldConfig(tmp_path / name, world_id, corpus_roots)


def audit(
    config: registry.WorldConfig,
    subject: anchors.Subject,
    target_root: Path,
    inspections: Inspections,
    captures: Captures,
    *,
    observers: tuple[verify.ObserverCarrier, ...] = (),
    actor: str = "alice",
    history: Mapping[str, bytes] | None = None,
) -> verify.LogReport:
    return verify._audit_log(
        config,
        subject,
        target_root,
        verify.ObserverSet(observers),
        actor=actor,
        history=history,
        seam=make_seam(inspections, captures),
    )


def corpus_anchor(view: logmodel.WellFormedView, corpus_id: str = ALPHA) -> verify.RegistryCarrier:
    """A registry log-head record anchoring `view`'s tip — `named-local`, which
    is an eligible provenance for a corpus subject."""
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.CorpusSubject(corpus_id),
            view.genesis.digest,
            view.tip,
            anchors.AnchorActOrigin("alice"),
        )
    )


def world_anchor(view: logmodel.WellFormedView, world_id: str = WORLD_ID) -> verify.ArtifactCarrier:
    """An exported head artifact anchoring `view`'s tip — the only eligible
    carrier for a world subject (L11)."""
    return verify.ArtifactCarrier.from_bytes(
        anchors.head_artifact_bytes(
            anchors.HeadArtifact(anchors.WorldSubject(world_id), view.genesis.digest, view.tip)
        )
    )


def tree(*roots: Path) -> dict[str, bytes]:
    return {
        str(path): path.read_bytes()
        for root in roots
        if root.exists()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


# --- the audit act (§6.1) -------------------------------------------------------


class TestTheAuditAct:
    def test_a_corpus_with_damaged_node_bytes_is_lockable_and_judged(self, tmp_path):
        # The lock-only lookup is the whole point: `_root_state_for` constructs
        # and parses a `Corpus`, so on exactly the damaged root an audit exists
        # to judge, asking it for the lock would raise before the verdict.
        root = corpus_root(tmp_path)
        (root / "verification").mkdir(parents=True, exist_ok=True)
        (root / "verification" / "v1.md").write_text("---\nnot: [a valid record\n---\n", encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            _root_state_for(root, DefaultExecutor)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config_for(tmp_path, root),
            anchors.CorpusSubject(ALPHA),
            root,
            inspections,
            captures,
            observers=(corpus_anchor(view),),
        )

        assert report.outcome == "validated"
        assert "verification/v1.md" in captures.calls[0][1]

    def test_the_target_root_is_never_associated_by_manifest(self, tmp_path):
        # The exact mismatch the audit exists to report: a `corpus.yaml`
        # rewritten to another id. Ordinary resolution associates a root to a
        # subject *by that manifest*, so it cannot locate this root at all —
        # which is why the target is explicit.
        root = corpus_root(tmp_path)
        (root / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, BETA, PINS)))
        config = config_for(tmp_path, root)
        assert registry._carrier_roots(config, ALPHA) == ()
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config,
            anchors.CorpusSubject(ALPHA),
            root,
            inspections,
            captures,
            observers=(corpus_anchor(view),),
        )

        assert [(finding.code, finding.ref, finding.detail) for finding in report.findings] == [
            ("subject-mismatch", "manifest", f"claims={BETA} subject=corpus:{ALPHA}")
        ]
        # §6.3: at audit the mismatch is a finding, never a refusal, and the
        # chain verdict is whatever the chain says — a cooperatively logged
        # rewrite replays consistently (§1.2).
        assert report.outcome == "validated"

    def test_the_presented_claim_is_the_one_the_recovered_root_makes(self, tmp_path):
        # Registered-mode inspection runs recovery, which applies a settled
        # transaction's finals to disk. A manifest read *before* that is a
        # pre-recovery claim standing beside a post-recovery surface: the two
        # reads in one hold would not be one view, and the report would name an
        # identity the act's own inspection had already replaced. The probe
        # rewrites the manifest during the inspection, exactly as recovering a
        # pending settled transaction over `corpus.yaml` would.
        root = corpus_root(tmp_path)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        def recover(_root: Path) -> None:
            (root / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, BETA, PINS)))

        inspections.probe = recover

        report = audit(
            config_for(tmp_path, root),
            anchors.CorpusSubject(ALPHA),
            root,
            inspections,
            captures,
            observers=(corpus_anchor(view),),
        )

        # Read before the inspection this would be `ALPHA`, agreeing with the
        # subject, and the mismatch would go unreported.
        assert [(finding.code, finding.ref, finding.detail) for finding in report.findings] == [
            ("subject-mismatch", "manifest", f"claims={BETA} subject=corpus:{ALPHA}")
        ]

    def test_a_manifest_that_cannot_be_read_states_no_claim(self, tmp_path):
        # `None` is "no claim was supplied", which is neither agreement nor
        # disagreement: an audit must not report a root as claiming something
        # its manifest never said.
        root = corpus_root(tmp_path)
        (root / "corpus.yaml").unlink()
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config_for(tmp_path, root),
            anchors.CorpusSubject(ALPHA),
            root,
            inspections,
            captures,
            observers=(corpus_anchor(view),),
        )

        assert [finding.code for finding in report.findings] == []
        assert report.outcome == "validated"

    def test_an_unconfigured_corpus_target_root_refuses(self, tmp_path):
        configured = corpus_root(tmp_path)
        stranger = corpus_root(tmp_path, ALPHA, name="stranger")
        inspections, captures = Inspections(), Captures()

        with pytest.raises(AuditTargetUnconfigured):
            audit(
                config_for(tmp_path, configured),
                anchors.CorpusSubject(ALPHA),
                stranger,
                inspections,
                captures,
            )

        assert inspections.roots == []
        assert captures.calls == []

    def test_a_world_target_that_is_not_the_configured_world_root_refuses(self, tmp_path):
        world_root(tmp_path)
        other = world_root(tmp_path, name="elsewhere")
        inspections, captures = Inspections(), Captures()

        with pytest.raises(AuditTargetUnconfigured):
            audit(
                config_for(tmp_path, world_id=WORLD_ID),
                anchors.WorldSubject(WORLD_ID),
                other,
                inspections,
                captures,
            )

        assert inspections.roots == []

    def test_a_store_subject_refuses_rather_than_producing_an_outcome(self, tmp_path):
        root = corpus_root(tmp_path)
        inspections, captures = Inspections(), Captures()

        with pytest.raises(StoreSubjectUnsupported):
            audit(config_for(tmp_path, root), anchors.StoreSubject("5" * 32), root, inspections, captures)

        assert inspections.roots == []

    def test_an_unencodable_actor_refuses_before_any_read(self, tmp_path):
        root = corpus_root(tmp_path)
        inspections, captures = Inspections(), Captures()

        with pytest.raises(TypeError):
            audit(
                config_for(tmp_path, root),
                anchors.CorpusSubject(ALPHA),
                root,
                inspections,
                captures,
                actor=object(),  # type: ignore[arg-type]
            )

        assert inspections.roots == []

    def test_the_audit_writes_nothing(self, tmp_path):
        root = corpus_root(tmp_path)
        world = world_root(tmp_path)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, surfaced(root, "corpus", science_root.GENESIS_PAYLOAD))
        inspections.set(world, surfaced(world, "world", science_root._world_genesis_payload(WORLD_ID)))
        config = config_for(tmp_path, root)
        before = tree(root, world)

        audit(config, anchors.CorpusSubject(ALPHA), root, inspections, captures)
        audit(config, anchors.WorldSubject(WORLD_ID), world, inspections, captures)

        assert tree(root, world) == before

    def test_it_holds_the_corpus_operation_lock_across_inspection_and_capture(self, tmp_path):
        root = corpus_root(tmp_path)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, surfaced(root, "corpus", science_root.GENESIS_PAYLOAD))
        held = _operation_lock_for(root)
        observed: list[str] = []

        def probe(_root: Path) -> None:
            # A build's capture arriving to any holder refuses at once, so this
            # is the writer hold observed from outside rather than inferred.
            with pytest.raises(BuildContended), held.capture():
                pass
            observed.append(str(held._holder))

        inspections.probe = probe
        captures.probe = probe

        audit(config_for(tmp_path, root), anchors.CorpusSubject(ALPHA), root, inspections, captures)

        assert observed == ["writer", "writer"]
        assert held._holder is None

    def test_it_holds_the_world_lock_across_inspection_and_capture(self, tmp_path):
        root = world_root(tmp_path)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, surfaced(root, "world", science_root._world_genesis_payload(WORLD_ID)))
        held = registry._world_lock_for(root)
        observed: list[bool] = []

        def probe(_root: Path) -> None:
            observed.append(held.acquire(blocking=False))

        inspections.probe = probe
        captures.probe = probe

        audit(config_for(tmp_path, world_id=WORLD_ID), anchors.WorldSubject(WORLD_ID), root, inspections, captures)

        assert observed == [False, False]
        assert held.acquire(blocking=False) is True
        held.release()

    def test_it_calls_no_world_method_under_the_world_lock(self, tmp_path):
        # R12: the seam's world lock is the very lock `World.registry()` takes,
        # and it is not reentrant. The audit is handed a configuration and never
        # a `World`, which is what makes the rule unbreakable here rather than
        # merely unbroken — and the opened world still answers afterwards.
        root = world_root(tmp_path)
        config = config_for(tmp_path, world_id=WORLD_ID)
        world = registry.World(
            config, DefaultExecutor, chain_head=ChainHeads(), corpus_executor_factory=DefaultExecutor
        )
        inspections, captures = Inspections(), Captures()
        inspections.set(root, surfaced(root, "world", science_root._world_genesis_payload(WORLD_ID)))

        report = audit(config, anchors.WorldSubject(WORLD_ID), root, inspections, captures)

        assert report.outcome == "unresolvable"
        assert "world" not in inspect.signature(verify._audit_log).parameters
        assert world.registry() == registry.RegistryView()

    def test_the_lock_is_released_when_the_act_refuses(self, tmp_path):
        root = corpus_root(tmp_path)
        inspections, captures = Inspections(), Captures()  # no view set: the stub refuses

        with pytest.raises(AssertionError):
            audit(config_for(tmp_path, root), anchors.CorpusSubject(ALPHA), root, inspections, captures)

        assert _operation_lock_for(root)._holder is None

    def test_a_missing_target_root_refuses_rather_than_judging_an_empty_surface(self, tmp_path):
        root = tmp_path / "gone"
        inspections, captures = Inspections(), Captures()
        inspections.set(
            root,
            chain(
                logmodel.GenesisEntryView(
                    digest=digest("g"), payload=science_root.GENESIS_PAYLOAD, baseline=()
                )
            ),
        )

        with pytest.raises(FileNotFoundError):
            audit(config_for(tmp_path, root), anchors.CorpusSubject(ALPHA), root, inspections, captures)

    def test_the_history_reaches_the_policy_pass(self, tmp_path):
        # The optional typed input is carried through to replay rather than
        # dropped: the classification names the digest the copy was filed under.
        root = corpus_root(tmp_path)
        removed = "verification/v1.md"
        payload = held_verification("v1", "failed")
        history = {f"sha256:{hashlib.sha256(payload).hexdigest()}": payload}
        created = registration(
            digest("create"),
            "tx-0",
            (("corpus.yaml", ABSENT), (removed, ABSENT)),
            (("corpus.yaml", state("corpus.yaml")), (removed, state(removed))),
        )
        view = chain(
            genesis_entry(science_root.GENESIS_PAYLOAD, label="history-genesis"),
            created,
            settlement(digest("settle-0"), created.digest, "tx-0", committed=True),
            registration(digest("r"), "tx-1", ((removed, state(removed)),), ((removed, ABSENT),)),
            settlement(digest("s"), digest("r"), "tx-1", committed=True),
        )
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config_for(tmp_path, root),
            anchors.CorpusSubject(ALPHA),
            root,
            inspections,
            captures,
            observers=(corpus_anchor(view),),
            history=history,
        )

        assert [finding.code for finding in report.findings] == [
            "record-removed",
            "failing-verification-removed",
        ]

    def test_a_corrupt_history_refuses_before_the_root_is_read_at_all(self, tmp_path):
        # §5.3: corrupt evidence is never silently ignored — and the pairs are
        # the caller's own input, so the refusal comes before the lock rather
        # than after a root has been inspected and stated.
        root = corpus_root(tmp_path)
        inspections, captures = Inspections(), Captures()

        with pytest.raises(ValueError):
            audit(
                config_for(tmp_path, root),
                anchors.CorpusSubject(ALPHA),
                root,
                inspections,
                captures,
                history={"sha256:nope": b"a record"},
            )

        assert inspections.roots == []
        assert captures.calls == []
        assert _operation_lock_for(root)._holder is None

    def test_the_audit_judges_through_the_one_evaluator_in_registered_mode(self, tmp_path, monkeypatch):
        # §4.1: one read-only function is the entire judgment surface. Audit
        # calls it exactly once, over the registered-mode view — the detached
        # stub in this module's seam refuses, which is the other half.
        root = corpus_root(tmp_path)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)
        seen: list[tuple[object, ...]] = []
        evaluate = verify.evaluate_log

        def recording(subject, chain_view, observers, disk, presented, absent_state, history=None):
            seen.append((subject, chain_view, disk, presented, absent_state, history))
            return evaluate(subject, chain_view, observers, disk, presented, absent_state, history)

        monkeypatch.setattr(verify, "evaluate_log", recording)

        report = audit(config_for(tmp_path, root), anchors.CorpusSubject(ALPHA), root, inspections, captures)

        assert len(seen) == 1
        subject, chain_view, disk, presented, absent_state, history = seen[0]
        assert (subject, chain_view, presented) == (
            anchors.CorpusSubject(ALPHA),
            view,
            verify.PresentedManifest(ALPHA),
        )
        assert disk == tuple((path, state(path)) for path in verify.registered_surface_paths(root, "corpus"))
        assert (absent_state, history) == (ABSENT, None)
        assert report.outcome == "unresolvable"


# --- the world genesis↔mirror agreement, as audit reports it (§6.3) -------------


class TestTheWorldMirrorIsReportedAndNeverRaised:
    def test_mirror_branch_refuses_open_world_and_audit_stays_callable(self, tmp_path):
        # The detection/refusal split: `open_world` refuses the disagreement,
        # and the audit of exactly that world answers, with the mismatch stated
        # as a finding. Auditing a broken world is the point.
        root = world_root(tmp_path, mirrored=OTHER_WORLD_ID)
        config = config_for(tmp_path, world_id=WORLD_ID)
        view = surfaced(root, "world", science_root._world_genesis_payload(WORLD_ID))
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        with pytest.raises(WorldIdMismatch):
            science_root.open_world(config)

        report = audit(
            config,
            anchors.WorldSubject(WORLD_ID),
            root,
            inspections,
            captures,
            observers=(world_anchor(view),),
        )

        assert [(finding.code, finding.ref, finding.detail) for finding in report.findings] == [
            ("subject-mismatch", "mirror", f"claims={OTHER_WORLD_ID} subject=world:{WORLD_ID}")
        ]
        assert report.outcome == "validated"

    def test_a_genesis_naming_another_world_is_a_finding_and_not_malformed(self, tmp_path):
        # A valid world genesis naming a different `world_id` is §6.3's subject
        # mismatch, never step 1's malformed exit.
        root = world_root(tmp_path)
        view = surfaced(root, "world", science_root._world_genesis_payload(OTHER_WORLD_ID))
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config_for(tmp_path, world_id=WORLD_ID),
            anchors.WorldSubject(WORLD_ID),
            root,
            inspections,
            captures,
            observers=(world_anchor(view),),
        )

        assert [(finding.code, finding.ref) for finding in report.findings] == [("subject-mismatch", "genesis")]
        assert report.outcome == "validated"

    def test_a_world_root_with_no_mirror_at_all_claims_nothing(self, tmp_path):
        root = world_root(tmp_path)
        (root / "world.yaml").unlink()
        view = surfaced(root, "world", science_root._world_genesis_payload(WORLD_ID))
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)

        report = audit(
            config_for(tmp_path, world_id=WORLD_ID),
            anchors.WorldSubject(WORLD_ID),
            root,
            inspections,
            captures,
            observers=(world_anchor(view),),
        )

        assert [finding.code for finding in report.findings] == []
        assert report.outcome == "validated"


# --- the ordered-cuts predicate (§7) --------------------------------------------


class MovingWorldHead(ChainHeads):
    """`ChainHeads`, with the world root's tip under the arm's control.

    Every build reads the world head at preflight and stores it in its
    `anchors.yaml`, and the predicate compares exactly that recorded value
    against the chain. An arm that could not move the tip between two builds
    could not state a sequence at all.
    """

    def __init__(self, target: Path) -> None:
        super().__init__()
        self.target = Path(target).resolve()
        self.tip: str | None = None

    def __call__(self, target: Path) -> tuple[str, str]:
        genesis_digest, tip = super().__call__(target)
        if Path(target).resolve() == self.target and self.tip is not None:
            return (genesis_digest, self.tip)
        return (genesis_digest, tip)


WORLD_GENESIS = digest("world-genesis")
FIRST_REGISTRATION = digest("registration-1")
FIRST_SETTLEMENT = digest("settlement-1")
LATER_ENTRY = digest("registration-2")


class Sequence:
    """Two epochs published in sequence over one world.

    The heads the builds record are this module's own digests, so the
    fabricated world chain and the published `anchors.yaml` members name the
    same entries — which is the whole of what the predicate joins.
    """

    def __init__(self, tmp_path: Path) -> None:
        self.heads = MovingWorldHead(tmp_path / "world")
        self.world, _recorder, self.bindings, _roots = admitted_world(
            tmp_path, (ALPHA,), chain_head=self.heads
        )
        self.heads.tip = WORLD_GENESIS
        self.first = publish(self.world, (ALPHA,), self.bindings).packaging_identity
        self.heads.tip = FIRST_SETTLEMENT
        self.second = publish(self.world, (ALPHA,), self.bindings).packaging_identity
        assert self.first != self.second

    @property
    def config(self) -> registry.WorldConfig:
        return self.world.config

    def build_at(self, tip: str) -> str:
        self.heads.tip = tip
        return publish(self.world, (ALPHA,), self.bindings).packaging_identity

    def recorded_head(self, packaging_identity: str) -> str:
        with registry._world_lock_for(self.config.world_root):
            return epoch._locked_open_epoch(
                self.config.world_root, packaging_identity
            ).world_anchor.head_digest


def world_chain(first_identity: str, *, committed: bool = True, trailing: bool = False) -> logmodel.WellFormedView:
    """A world chain that published `first_identity` and settled it."""
    genesis = logmodel.GenesisEntryView(
        digest=WORLD_GENESIS, payload=science_root._world_genesis_payload(WORLD_ID), baseline=()
    )
    entries: list[logmodel.EntryView] = [
        publication(FIRST_REGISTRATION, "tx-1", first_identity),
        settlement(FIRST_SETTLEMENT, FIRST_REGISTRATION, "tx-1", committed=committed),
    ]
    if trailing:
        entries.append(publication(LATER_ENTRY, "tx-2", "9" * 64))
    return chain(genesis, *entries)


def ordered(config: registry.WorldConfig, first: str, second: str, view: logmodel.ChainView) -> str:
    inspections, captures = Inspections(), Captures()
    inspections.set(config.world_root, view)
    return verify._epochs_ordered(config, first, second, seam=make_seam(inspections, captures))


class TestTheOrderedCutsPredicate:
    def test_epochs_ordered_by_descent_and_unordered_without_settled_publication(self, tmp_path):
        sequence = Sequence(tmp_path)
        assert sequence.recorded_head(sequence.first) == WORLD_GENESIS
        assert sequence.recorded_head(sequence.second) == FIRST_SETTLEMENT

        assert ordered(sequence.config, sequence.first, sequence.second, world_chain(sequence.first)) == "ordered"

        # The same pair and the same recorded heads, one fact changed: E1's
        # publication settled as a rollback. Asserted by entry class, because
        # "rolled back" is a property of the settlement entry rather than of a
        # string in a report.
        rolled_back = world_chain(sequence.first, committed=False)
        (settled,) = [entry for entry in rolled_back.entries if type(entry) is logmodel.SettledEntryView]
        assert settled.committed is False
        assert ordered(sequence.config, sequence.first, sequence.second, rolled_back) == "unordered"

    def test_a_head_strictly_beyond_the_settlement_descends_from_it(self, tmp_path):
        sequence = Sequence(tmp_path)

        third = sequence.build_at(LATER_ENTRY)

        assert sequence.recorded_head(third) == LATER_ENTRY
        assert ordered(sequence.config, sequence.first, third, world_chain(sequence.first, trailing=True)) == "ordered"

    def test_an_unpublished_first_epoch_is_unordered(self, tmp_path):
        sequence = Sequence(tmp_path)

        # A chain that published something else can place no settlement for E1.
        assert ordered(sequence.config, sequence.first, sequence.second, world_chain("8" * 64)) == "unordered"

    def test_a_build_start_head_the_chain_does_not_carry_is_unordered(self, tmp_path):
        sequence = Sequence(tmp_path)
        # E1 recorded `WORLD_GENESIS` as its own build-start head, and this
        # chain — a replacement under another genesis — carries no such entry,
        # though it does carry E1's publication and its settlement.
        replaced = chain(
            logmodel.GenesisEntryView(
                digest=digest("another-genesis"),
                payload=science_root._world_genesis_payload(WORLD_ID),
                baseline=(),
            ),
            publication(FIRST_REGISTRATION, "tx-1", sequence.first),
            settlement(FIRST_SETTLEMENT, FIRST_REGISTRATION, "tx-1", committed=True),
        )

        assert ordered(sequence.config, sequence.first, sequence.first, replaced) == "unordered"

    def test_an_absent_or_malformed_world_chain_is_unordered(self, tmp_path):
        sequence = Sequence(tmp_path)

        assert ordered(sequence.config, sequence.first, sequence.second, logmodel.AbsentView()) == "unordered"
        malformed = logmodel.MalformedView(
            logmodel.DefectView(kind="cycle", subject=digest("x"), detail="a cycle")
        )
        assert ordered(sequence.config, sequence.first, sequence.second, malformed) == "unordered"

    def test_an_unknown_second_epoch_refuses(self, tmp_path):
        sequence = Sequence(tmp_path)

        with pytest.raises(EpochUnknown):
            ordered(sequence.config, sequence.first, "4" * 64, world_chain(sequence.first))

    def test_a_first_value_that_is_not_a_packaging_identity_refuses(self, tmp_path):
        sequence = Sequence(tmp_path)

        with pytest.raises(EpochUnknown):
            ordered(sequence.config, "not-an-identity", sequence.second, world_chain(sequence.first))

    def test_it_holds_the_world_lock_across_the_inspection_and_the_epoch_read(self, tmp_path):
        sequence = Sequence(tmp_path)
        held = registry._world_lock_for(sequence.config.world_root)
        inspections, captures = Inspections(), Captures()
        inspections.set(sequence.config.world_root, world_chain(sequence.first))
        observed: list[bool] = []
        inspections.probe = lambda _root: observed.append(held.acquire(blocking=False))

        answer = verify._epochs_ordered(
            sequence.config, sequence.first, sequence.second, seam=make_seam(inspections, captures)
        )

        assert answer == "ordered"
        assert observed == [False]
        assert held.acquire(blocking=False) is True
        held.release()

    def test_epoch_sequence_numbers_are_read_by_nothing(self, tmp_path):
        sequence = Sequence(tmp_path)

        # No published member carries one, and no sequence file sits beside the
        # carriers: `epochs/` holds the two content-addressed directories and
        # the one-line pointer.
        base = sequence.config.world_root / "epochs"
        assert sorted(entry.name for entry in base.iterdir()) == sorted(
            [sequence.first, sequence.second, epoch.CURRENT_POINTER]
        )
        for identity in (sequence.first, sequence.second):
            for member in epoch.EPOCH_MEMBERS:
                document = yaml.safe_load((base / identity / member).read_text(encoding="utf-8"))
                assert "sequence" not in keys_of(document), (identity, member)

        # And the predicate reads none: its answer follows the chain's own
        # ancestry, so the pair published second-then-first in the chain is
        # `unordered` in the order the epochs were actually built.
        reversed_chain = world_chain(sequence.second)
        assert ordered(sequence.config, sequence.second, sequence.first, reversed_chain) == "unordered"

        # Nothing in the epoch type or in the predicate's code names one; the
        # docstring is stripped because it says so in prose, which is the one
        # place the word belongs.
        assert [name for name in dir(epoch.Epoch) if "sequence" in name] == []
        code, _docstring, rest = inspect.getsource(verify._epochs_ordered).split('"""')
        assert "sequence" not in code + rest


# --- the public wrappers ---------------------------------------------------------


class TestThePublicWrappers:
    def test_the_wrappers_hand_the_cores_the_production_seam(self, tmp_path, monkeypatch):
        seen: list[tuple[object, ...]] = []
        monkeypatch.setattr(
            science_root,
            "_audit_log",
            lambda config, subject, target_root, observers, *, actor, history, seam: seen.append(
                ("audit", config, subject, target_root, observers, actor, history, seam)
            ),
        )
        monkeypatch.setattr(
            science_root,
            "_epochs_ordered",
            lambda config, e1, e2, *, seam: seen.append(("ordered", config, e1, e2, seam)) or "unordered",
        )
        root = corpus_root(tmp_path)
        config = config_for(tmp_path, root)
        observers = verify.ObserverSet(())

        science_root.audit_log(config, anchors.CorpusSubject(ALPHA), root, observers, actor="alice")
        science_root.epochs_ordered(config, "1" * 64, "2" * 64)

        assert seen == [
            (
                "audit",
                config,
                anchors.CorpusSubject(ALPHA),
                root,
                observers,
                "alice",
                None,
                science_root._log_seam(),
            ),
            ("ordered", config, "1" * 64, "2" * 64, science_root._log_seam()),
        ]

    def test_the_wrapper_signatures_are_the_ruled_ones(self):
        audit_parameters = inspect.signature(science_root.audit_log).parameters
        assert list(audit_parameters) == ["config", "subject", "target_root", "observers", "actor", "history"]
        assert audit_parameters["actor"].kind is inspect.Parameter.KEYWORD_ONLY
        assert audit_parameters["history"].default is None
        # The configuration, never an opened `World`: the audit must run on the
        # very worlds `open_world` refuses.
        assert "world" not in audit_parameters

        ordered_parameters = inspect.signature(science_root.epochs_ordered).parameters
        assert list(ordered_parameters) == ["config", "e1", "e2"]

    def test_both_wrappers_are_exported_by_the_composition_root(self):
        assert {"audit_log", "epochs_ordered"} <= set(science_root.__all__)

    def test_the_act_cores_take_the_seam_as_a_parameter(self):
        for core in (verify._audit_log, verify._epochs_ordered):
            parameters = inspect.signature(core).parameters
            assert parameters["seam"].kind is inspect.Parameter.KEYWORD_ONLY
            assert parameters["seam"].default is inspect.Parameter.empty


# --- §6.4's engine refusal, in the audit's context -------------------------------


def test_a_chain_record_contradiction_at_audit_refuses_with_no_report(tmp_path, monkeypatch):
    """R11/§6.4's `ChainStateInvalid` arm, reached through the audit.

    The state being modelled is a live transaction record standing beside an
    empty chain — the engine's own chain/store contradiction, which keeps
    raising rather than returning `AbsentChain`.

    **The engine's decision to raise is injected, deliberately.** Whether that
    disk state produces `ChainStateInvalid` is the engine's own contract,
    certified in `atoms` and outside this cut's mutation surface; what is
    Science's to arm is what the audit does with the exception — the seam
    adapter's §6.4 translation reaching the caller as a refusal to judge,
    outside every precedence, with no `LogReport` produced and the lock
    released. Task 4's `TransactionHalted` and `PreconditionRefused` arms are
    injected on the same ground.
    """
    root = corpus_root(tmp_path)
    invalid = ChainStateInvalid("a live transaction record exists without its project chain")

    def raising(backend, project_root, metadata_root, storage):
        raise invalid

    monkeypatch.setattr(science_root, "inspect_chain", raising)

    with pytest.raises(LogEvidenceRefused) as caught:
        science_root.audit_log(
            config_for(tmp_path, root),
            anchors.CorpusSubject(ALPHA),
            root,
            verify.ObserverSet(()),
            actor="alice",
        )

    assert (caught.value.phase, caught.value.engine_error) == ("inspect", "ChainStateInvalid")
    assert caught.value.__cause__ is invalid
    assert _operation_lock_for(root)._holder is None
