"""The four-outcome log evaluator: its precedence, its carriers, its report.

**One arm per exit.** Design §4.2 fixes four steps so that no state earns two
outcomes, which is only a property if every step is shown deciding *before* the
one after it: the pending arm proves replay is not reached by making a call to
it fail the test, and the malformed arms prove the anchor step is not reached by
supplying anchors that would refute if it were.

The path states here are the same inert stand-ins the replay arms use: replay
compares states by equality and by nothing else, and an evaluator that reached
inside one would fail rather than pass quietly.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
import yaml

from science import root as science_root
from science.errors import ObserverCarrierInvalid, StoreSubjectUnsupported
from science.identity import v1
from science.world import anchors as anchors_module
from science.world import verify
from science.world.anchors import (
    AnchorActOrigin,
    CorpusSubject,
    HeadArtifact,
    LogHeadRecord,
    StoreSubject,
    WorldSubject,
    head_artifact_bytes,
)
from science.world.epoch import EPOCH_MEMBERS, packaging_identity_of
from science.world.logmodel import (
    AbsentView,
    DefectView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)
from science.world.verify import (
    ArtifactCarrier,
    EpochCarrier,
    ObserverSet,
    RegistryCarrier,
    evaluate_log,
)

# --- identities and digests ----------------------------------------------

CORPUS_ID = "c" * 32
OTHER_CORPUS_ID = "d" * 32
WORLD_ID = "e" * 32
OTHER_WORLD_ID = "f" * 32
STORE_ID = "a" * 32

CORPUS_GENESIS = "a0" * 32
WORLD_GENESIS = "b0" * 32
FORK_GENESIS = "c0" * 32
E1 = "11" * 32
E2 = "22" * 32
E3 = "33" * 32
STRANGER = "99" * 32
FOREIGN = "88" * 32

CORPUS_GENESIS_PAYLOAD = v1.encode({"domain": "science.corpus-root.v1"})
WORLD_GENESIS_PAYLOAD = v1.encode({"domain": "science.world-root.v1", "world_id": WORLD_ID})
OTHER_WORLD_GENESIS_PAYLOAD = v1.encode({"domain": "science.world-root.v1", "world_id": OTHER_WORLD_ID})


# --- the opaque state stand-in -------------------------------------------


class Opaque:
    """A path state that answers equality and nothing else."""

    __hash__ = None  # type: ignore[assignment]  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, label: str) -> None:
        object.__setattr__(self, "_label", label)

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"a path state was read for {name!r}: states are compared, never interpreted")

    def __repr__(self) -> str:
        return f"Opaque({self.__dict__['_label']!r})"


ABSENT = Opaque("absent")
MANIFEST = Opaque("corpus.yaml@0")
OTHER = Opaque("corpus.yaml@1")


# --- chain fabrication ----------------------------------------------------


def genesis(payload: bytes = CORPUS_GENESIS_PAYLOAD, *baseline: tuple[str, object]) -> GenesisEntryView:
    return GenesisEntryView(digest=CORPUS_GENESIS, payload=payload, baseline=baseline)


def registration(digest: str, txid: str) -> RegisteredEntryView:
    return RegisteredEntryView(
        digest=digest,
        txid=txid,
        initial=(("corpus.yaml", ABSENT),),
        final=(("corpus.yaml", MANIFEST),),
        fulfills=None,
    )


def settlement(digest: str, registration_digest: str, txid: str) -> SettledEntryView:
    return SettledEntryView(digest=digest, txid=txid, registration=registration_digest, committed=True)


def chain(
    head: GenesisEntryView,
    *rest: IntentEntryView | RegisteredEntryView | SettledEntryView,
    pending: tuple[tuple[str, str], ...] = (),
) -> WellFormedView:
    """R10's shape: the genesis is `entries[0]`, the same object."""
    entries = (head, *rest)
    return WellFormedView(genesis=head, entries=entries, tip=entries[-1].digest, pending=pending)


def corpus_chain(pending: tuple[tuple[str, str], ...] = ()) -> WellFormedView:
    """A registered corpus chain: genesis, one committed write, its settlement."""
    return chain(genesis(), registration(E1, "tx-1"), settlement(E2, E1, "tx-1"), pending=pending)


def _never(*args: object, **kwargs: object) -> verify.ReplayResult:
    """A `replay` stand-in for the arms that must not reach step 4."""
    raise AssertionError("replay was reached")


def world_chain(payload: bytes = WORLD_GENESIS_PAYLOAD) -> WellFormedView:
    world_genesis = GenesisEntryView(digest=WORLD_GENESIS, payload=payload, baseline=())
    return chain(world_genesis, registration(E1, "tx-1"), settlement(E2, E1, "tx-1"))


MATCHING_DISK: tuple[tuple[str, object], ...] = (("corpus.yaml", MANIFEST),)


# --- observers ------------------------------------------------------------


def record_carrier(head: str, *, corpus_id: str = CORPUS_ID, chain_genesis: str = CORPUS_GENESIS) -> RegistryCarrier:
    return RegistryCarrier.from_record(
        LogHeadRecord(CorpusSubject(corpus_id), chain_genesis, head, AnchorActOrigin("keith"))
    )


def artifact_carrier(
    subject: CorpusSubject | WorldSubject | StoreSubject, chain_genesis: str, head: str
) -> ArtifactCarrier:
    return ArtifactCarrier.from_bytes(head_artifact_bytes(HeadArtifact(subject, chain_genesis, head)))


def anchors_member(
    *,
    corpus_head: str = E1,
    world_head: str = E1,
    corpus_id: str = CORPUS_ID,
    corpus_genesis: str = CORPUS_GENESIS,
    world_genesis: str = WORLD_GENESIS,
) -> bytes:
    document = {
        "corpora": [
            {"subject": corpus_id, "genesis_digest": corpus_genesis, "head_digest": corpus_head},
        ],
        "world": {"subject": WORLD_ID, "genesis_digest": world_genesis, "head_digest": world_head},
    }
    return yaml.safe_dump(document, sort_keys=True, allow_unicode=True).encode("utf-8")


def epoch_members(**kwargs: str) -> dict[str, bytes]:
    """The eleven members. Only `anchors.yaml` is a real document: the packaging
    identity is over every member's bytes, and the carrier reads exactly one."""
    members = {member: f"# {member}\n".encode() for member in EPOCH_MEMBERS}
    members["anchors.yaml"] = anchors_member(**kwargs)
    return members


def supplied_epoch(**kwargs: str) -> EpochCarrier:
    members = epoch_members(**kwargs)
    return EpochCarrier.from_export(members, packaging_identity_of(members))


def local_epoch(directory: Path, **kwargs: str) -> EpochCarrier:
    members = epoch_members(**kwargs)
    carrier_root = directory / packaging_identity_of(members)
    carrier_root.mkdir(parents=True)
    for member, content in members.items():
        (carrier_root / member).write_bytes(content)
    return EpochCarrier.from_named_local(carrier_root)


def observers(*carriers: RegistryCarrier | EpochCarrier | ArtifactCarrier) -> ObserverSet:
    return ObserverSet(carriers)


def codes(report: verify.LogReport) -> list[str]:
    return [finding.code for finding in report.findings]


def evaluate(
    subject: CorpusSubject | WorldSubject | StoreSubject,
    view: WellFormedView | MalformedView | AbsentView,
    observer_set: ObserverSet,
    *,
    disk: tuple[tuple[str, object], ...] = MATCHING_DISK,
    presented: verify.PresentedIdentity | None = None,
    history: dict[str, bytes] | None = None,
) -> verify.LogReport:
    return evaluate_log(subject, view, observer_set, disk, presented, ABSENT, history)


# --- entry: the typed history and the store subject ------------------------


class TestEntry:
    def test_a_corrupt_history_refuses_before_any_outcome(self) -> None:
        """Step 3 of the brief: history is validated before the chain is read at
        all, so a malformed chain does not get to answer first."""
        with pytest.raises(ValueError, match="not a content hash"):
            evaluate(
                CorpusSubject(CORPUS_ID),
                MalformedView(DefectView("cycle", E1, "an entry is its own ancestor")),
                observers(),
                history={"not-a-hash": b"held"},
            )

    def test_history_bytes_that_do_not_hash_to_their_key_refuse(self) -> None:
        with pytest.raises(ValueError, match="the held bytes hash to"):
            evaluate(
                CorpusSubject(CORPUS_ID),
                corpus_chain(),
                observers(),
                history={f"sha256:{'0' * 64}": b"held"},
            )

    def test_a_store_subject_is_unsupported(self) -> None:
        """§4.1: the evaluator's union is the one API that can spell a store, so
        the refusal lives here and only here."""
        with pytest.raises(StoreSubjectUnsupported):
            evaluate(StoreSubject(STORE_ID), corpus_chain(), observers())

    def test_the_store_refusal_outranks_the_chain(self) -> None:
        with pytest.raises(StoreSubjectUnsupported):
            evaluate(
                StoreSubject(STORE_ID),
                MalformedView(DefectView("cycle", E1, "an entry is its own ancestor")),
                observers(),
            )


# --- step 1: structure -----------------------------------------------------


class TestStructure:
    def test_a_malformed_chain_stops_at_step_one_with_the_defect_named(self) -> None:
        view = MalformedView(DefectView("sibling-branch", E2, "two entries claim one predecessor"))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(STRANGER)))
        assert report.outcome == "malformed"
        assert codes(report) == ["chain-malformed"]
        defect = report.findings[0]
        assert defect.ref == E2
        assert defect.detail == "kind=sibling-branch"
        assert defect.message == "two entries claim one predecessor"
        assert report.anchored_through is None
        assert report.unanchored_tail == ()
        assert report.pending == ()

    def test_an_unreachable_anchor_does_not_refute_a_malformed_chain(self) -> None:
        """Structure strictly before anchors: the same anchor refutes a
        well-formed chain and is never consulted for a verdict here."""
        anchor = observers(record_carrier(STRANGER))
        malformed = evaluate(
            CorpusSubject(CORPUS_ID), MalformedView(DefectView("cycle", E1, "a cycle")), anchor
        )
        well_formed = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), anchor)
        assert malformed.outcome == "malformed"
        assert well_formed.outcome == "refuted"

    def test_a_genesis_payload_of_the_wrong_form_is_malformed(self) -> None:
        view = chain(genesis(WORLD_GENESIS_PAYLOAD), registration(E1, "tx-1"), settlement(E2, E1, "tx-1"))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(E1)))
        assert report.outcome == "malformed"
        assert codes(report) == ["genesis-form-invalid"]

    def test_an_undecodable_genesis_payload_is_malformed(self) -> None:
        view = chain(genesis(b"\xff\xfe not json"), registration(E1, "tx-1"), settlement(E2, E1, "tx-1"))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(E1)))
        assert report.outcome == "malformed"
        assert codes(report) == ["genesis-form-invalid"]

    def test_a_non_empty_baseline_is_malformed(self) -> None:
        """§1.3: both initializers register `()`, so a populated baseline is a
        chain no Science path mints."""
        view = chain(
            genesis(CORPUS_GENESIS_PAYLOAD, ("corpus.yaml", MANIFEST)),
            registration(E1, "tx-1"),
            settlement(E2, E1, "tx-1"),
        )
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(E1)))
        assert report.outcome == "malformed"
        assert codes(report) == ["genesis-form-invalid"]
        assert "baseline" in report.findings[0].message

    def test_a_world_genesis_naming_another_world_is_a_mismatch_not_malformed(self) -> None:
        """§4.2 step 1's carve-out: a *valid* world genesis naming a different
        `world_id` is §6.3's subject mismatch, and the chain verdict stands."""
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(OTHER_WORLD_GENESIS_PAYLOAD),
            observers(artifact_carrier(WorldSubject(WORLD_ID), WORLD_GENESIS, E2)),
            presented=verify.PresentedWorldIds(configured=WORLD_ID, mirrored=WORLD_ID),
        )
        assert report.outcome == "validated"
        assert "subject-mismatch" in codes(report)
        assert [finding.ref for finding in report.findings if finding.code == "subject-mismatch"] == ["genesis"]

    def test_a_world_genesis_of_the_wrong_domain_is_malformed(self) -> None:
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(CORPUS_GENESIS_PAYLOAD),
            observers(),
        )
        assert report.outcome == "malformed"
        assert codes(report) == ["genesis-form-invalid"]

    def test_the_corpus_genesis_domain_is_the_composition_root_s(self) -> None:
        """The constant is restated in `anchors` because `science.world` may not
        import `science.root`; the two spellings are pinned equal so the
        restatement cannot drift into a second definition."""
        assert anchors_module.CORPUS_GENESIS_DOMAIN == science_root.GENESIS_DOMAIN

    def test_the_genesis_form_is_the_export_act_s_own_predicate(self) -> None:
        """One statement of each form (M-2): the evaluator's step-1 check and the
        export act's subject binding read the same two parsers, so the two
        cannot drift apart on what a Science genesis is."""
        assert anchors_module.parse_corpus_genesis(CORPUS_GENESIS_PAYLOAD) is None
        assert anchors_module.parse_world_genesis(WORLD_GENESIS_PAYLOAD) == WORLD_ID
        with pytest.raises(ValueError, match="world_id"):
            anchors_module.parse_world_genesis(v1.encode({"domain": "science.world-root.v1", "world_id": "nope"}))

    def test_a_world_genesis_naming_an_ungrammatical_id_is_malformed(self) -> None:
        """A `world_id` outside the identity grammar is a root that was never
        initialized as a Science world — not a *different* world, which is the
        stronger claim the bytes do not support."""
        payload = v1.encode({"domain": "science.world-root.v1", "world_id": "NOT-AN-ID"})
        report = evaluate(WorldSubject(WORLD_ID), world_chain(payload), observers())
        assert report.outcome == "malformed"
        assert codes(report) == ["genesis-form-invalid"]

    def test_the_chain_absent_code_is_a_named_constant(self) -> None:
        """Task 9 imports this name: §6.2's `chainless` cause is derived from it
        and a restated string on the other side could drift."""
        assert verify.CHAIN_ABSENT == "chain-absent"
        report = evaluate(CorpusSubject(CORPUS_ID), AbsentView(), observers())
        assert verify.CHAIN_ABSENT in codes(report)


# --- the subject-mismatch findings (§6.3) ----------------------------------


class TestSubjectMismatch:
    def test_a_manifest_naming_another_corpus_is_a_finding_on_a_validated_chain(self) -> None:
        """§1.2: a cooperatively logged identity rewrite replays consistently, so
        replay alone is not the guard — the finding stands beside `validated`."""
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E2)),
            presented=verify.PresentedManifest(corpus_id=OTHER_CORPUS_ID),
        )
        assert report.outcome == "validated"
        assert codes(report) == ["subject-mismatch"]
        assert report.findings[0].ref == "manifest"

    def test_a_matching_manifest_is_no_finding(self) -> None:
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E2)),
            presented=verify.PresentedManifest(corpus_id=CORPUS_ID),
        )
        assert report.outcome == "validated"
        assert report.findings == ()

    def test_a_disagreeing_world_mirror_is_a_finding(self) -> None:
        """§6.3's genesis↔mirror agreement check, on the audit's side of the
        split: `open_world` refuses it and the audit reports it."""
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(),
            observers(artifact_carrier(WorldSubject(WORLD_ID), WORLD_GENESIS, E2)),
            presented=verify.PresentedWorldIds(configured=WORLD_ID, mirrored=OTHER_WORLD_ID),
        )
        assert report.outcome == "validated"
        assert [finding.ref for finding in report.findings if finding.code == "subject-mismatch"] == ["mirror"]

    def test_mismatch_findings_never_filter_anchors(self) -> None:
        """The presented identity is a policy check, never a filter (§4.2 step 2:
        the subject is the sole filter)."""
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E2)),
            presented=verify.PresentedManifest(corpus_id=OTHER_CORPUS_ID),
        )
        assert report.anchored_through == E2
        assert len(report.observer_bound) == 1

    def test_a_presented_identity_of_the_wrong_kind_refuses(self) -> None:
        with pytest.raises(TypeError):
            evaluate(
                WorldSubject(WORLD_ID),
                world_chain(),
                observers(),
                presented=verify.PresentedManifest(corpus_id=CORPUS_ID),
            )


# --- step 2: anchors -------------------------------------------------------


class TestAnchors:
    def test_an_absent_chain_under_a_surviving_anchor_is_refuted(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), AbsentView(), observers(record_carrier(E1)))
        assert report.outcome == "refuted"
        assert codes(report) == ["anchor-chain-absent"]
        assert report.findings[0].ref == E1

    def test_an_absent_chain_without_an_anchor_is_unresolvable(self) -> None:
        """The absence is stated in the report: §6.2's arrival refuses a
        chainless replica and admits a fresh unanchored one, and those two are
        otherwise the same unresolvable verdict."""
        report = evaluate(CorpusSubject(CORPUS_ID), AbsentView(), observers())
        assert report.outcome == "unresolvable"
        assert codes(report) == ["chain-absent", "unanchored"]
        assert report.observer_bound == ()
        assert "chain-absent" not in codes(evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers()))

    def test_an_anchor_refutation_does_not_reach_replay(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(verify, "replay", _never)
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(record_carrier(STRANGER)))
        assert report.outcome == "refuted"

    def test_a_genesis_mismatch_refutes_replacement(self) -> None:
        """§1.2: the replacement arm fires for world subjects and future fork
        geneses — the corpus genesis is constant, so ancestry catches those."""
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(),
            observers(artifact_carrier(WorldSubject(WORLD_ID), FORK_GENESIS, E1)),
        )
        assert report.outcome == "refuted"
        assert "anchor-genesis-mismatch" in codes(report)

    def test_an_unreachable_anchored_head_refutes(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(record_carrier(STRANGER)))
        assert report.outcome == "refuted"
        assert "anchor-unreachable" in codes(report)

    def test_a_reachable_old_anchor_never_hides_a_missing_newer_one(self) -> None:
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E1), record_carrier(STRANGER)),
        )
        assert report.outcome == "refuted"
        assert "anchor-unreachable" in codes(report)

    def test_two_anchors_the_chain_cannot_order_are_incomparable(self) -> None:
        """Two heads this chain places nowhere: two claimed heads of one subject
        that no single chain here carries."""
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(STRANGER), record_carrier(FOREIGN)),
        )
        assert report.outcome == "refuted"
        incomparable = [finding for finding in report.findings if finding.code == "anchors-incomparable"]
        assert len(incomparable) == 1
        assert {incomparable[0].ref, incomparable[0].detail.removeprefix("other=")} == {STRANGER, FOREIGN}

    def test_an_unplaced_anchor_emits_no_pair_finding_against_placed_ones(self) -> None:
        """One fault among many anchors states itself once. Pairing the unplaced
        head against every surviving one would bury the fault under findings
        derived from it."""
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E1), record_carrier(E2), record_carrier(STRANGER)),
        )
        assert report.outcome == "refuted"
        assert codes(report) == ["anchor-unreachable"]

    def test_the_subject_filter_runs_first_and_alone(self) -> None:
        """An anchor for another corpus is filtered out, not refuted: the two
        chains share the identical genesis digest (§1.2), so a filter that
        looked at genesis alone would pool them."""
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(STRANGER, corpus_id=OTHER_CORPUS_ID), record_carrier(E2)),
        )
        assert report.outcome == "validated"
        assert len(report.observer_bound) == 1

    def test_an_empty_bound_set_is_unresolvable_from_genesis(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers())
        assert report.outcome == "unresolvable"
        assert report.observer_bound == ()
        assert report.anchored_through is None
        assert report.unanchored_tail == (CORPUS_GENESIS, E1, E2)
        assert codes(report) == ["unanchored"]

    def test_an_empty_bound_set_does_not_reach_replay(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(verify, "replay", _never)
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(), disk=())
        assert report.outcome == "unresolvable"

    def test_the_bound_records_each_carrier_s_provenance(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(record_carrier(E2)))
        expected = (
            f"registry-record provenance=named-local custody=read-from-root subject=corpus:{CORPUS_ID} "
            f"genesis={CORPUS_GENESIS} head={E2}"
        )
        assert report.observer_bound == (expected,)

    def test_the_bound_states_a_supplied_carrier_as_caller_attested(self) -> None:
        """§10.9: a factory name cannot prove custody, so `supplied-export` is
        caller-attested evidence and the bound says so."""
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(),
            observers(artifact_carrier(WorldSubject(WORLD_ID), WORLD_GENESIS, E1)),
        )
        assert "provenance=supplied-export custody=caller-attested" in report.observer_bound[0]


# --- the L11 eligibility square --------------------------------------------


class TestEligibility:
    def test_a_named_local_epoch_anchors_a_corpus(self, tmp_path: Path) -> None:
        report = evaluate(
            CorpusSubject(CORPUS_ID), corpus_chain(), observers(local_epoch(tmp_path, corpus_head=E1))
        )
        assert report.outcome == "validated"
        assert len(report.observer_bound) == 1
        assert "provenance=named-local" in report.observer_bound[0]

    def test_a_supplied_epoch_anchors_a_corpus(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(supplied_epoch(corpus_head=E1)))
        assert report.outcome == "validated"
        assert "provenance=supplied-export" in report.observer_bound[0]

    def test_a_named_local_epoch_anchors_no_world(self, tmp_path: Path) -> None:
        """L11's point: identical epoch bytes, different eligibility. No local
        act anchors the world chain."""
        report = evaluate(
            WorldSubject(WORLD_ID), world_chain(), observers(local_epoch(tmp_path, world_head=E1))
        )
        assert report.outcome == "unresolvable"
        assert report.observer_bound == ()
        assert "observer-ineligible" in codes(report)

    def test_a_supplied_epoch_anchors_a_world(self) -> None:
        report = evaluate(WorldSubject(WORLD_ID), world_chain(), observers(supplied_epoch(world_head=E1)))
        assert report.outcome == "validated"
        assert "provenance=supplied-export" in report.observer_bound[0]

    def test_a_head_artifact_is_supplied_export(self) -> None:
        report = evaluate(
            WorldSubject(WORLD_ID),
            world_chain(),
            observers(artifact_carrier(WorldSubject(WORLD_ID), WORLD_GENESIS, E1)),
        )
        assert report.outcome == "validated"
        assert "provenance=supplied-export" in report.observer_bound[0]


# --- step 3: pending -------------------------------------------------------


class TestPending:
    def test_pending_is_unresolvable_and_replay_is_not_reached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(verify, "replay", _never)
        view = corpus_chain(pending=(("tx-2", E3),))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(E2)))
        assert report.outcome == "unresolvable"
        assert report.pending == (("tx-2", E3),)
        assert codes(report) == ["pending-unresolved"]

    def test_an_unanchored_pending_chain_keeps_its_pending_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """§6.2's worked example: an empty observer set makes this `unresolvable`
        at step 2, before the pending step runs at all — and the pending set is
        still in the report, because arrival ranks the cause `pending` from the
        report's *fields* and not from the step that produced the outcome."""
        monkeypatch.setattr(verify, "replay", _never)
        view = corpus_chain(pending=(("tx-2", E3),))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers())
        assert report.outcome == "unresolvable"
        assert report.pending == (("tx-2", E3),)
        assert report.observer_bound == ()
        assert codes(report) == ["unanchored"]
        assert report.unanchored_tail == (CORPUS_GENESIS, E1, E2)

    def test_the_anchor_step_outranks_pending(self) -> None:
        view = corpus_chain(pending=(("tx-2", E3),))
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(STRANGER)))
        assert report.outcome == "refuted"


# --- step 4: replay --------------------------------------------------------


class TestReplay:
    def test_a_replay_disagreement_refutes(self) -> None:
        report = evaluate(
            CorpusSubject(CORPUS_ID),
            corpus_chain(),
            observers(record_carrier(E2)),
            disk=(("corpus.yaml", OTHER),),
        )
        assert report.outcome == "refuted"
        assert codes(report) == ["replay-disagreement"]
        assert report.findings[0].ref == "head:corpus.yaml"

    def test_a_removal_finding_survives_a_validated_verdict(self) -> None:
        """The policy pass is a report field in every case: occurrence is not
        authorization, and a removal is neither a disagreement nor a refutation."""
        removal = RegisteredEntryView(
            digest=E3,
            txid="tx-2",
            initial=(("corpus.yaml", MANIFEST),),
            final=(("corpus.yaml", ABSENT),),
            fulfills=None,
        )
        view = chain(
            genesis(),
            registration(E1, "tx-1"),
            settlement(E2, E1, "tx-1"),
            removal,
            settlement("44" * 32, E3, "tx-2"),
        )
        report = evaluate(
            CorpusSubject(CORPUS_ID), view, observers(record_carrier(E1)), disk=()
        )
        assert report.outcome == "validated"
        assert codes(report) == ["record-removed"]

    def test_the_validated_exit_states_the_unanchored_tail(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers(record_carrier(E1)))
        assert report.outcome == "validated"
        assert report.anchored_through == E1
        assert report.unanchored_tail == (E2,)
        assert report.pending == ()
        assert report.findings == ()

    def test_the_maximal_anchor_is_by_ancestry_and_not_by_record_order(self) -> None:
        report = evaluate(
            CorpusSubject(CORPUS_ID), corpus_chain(), observers(record_carrier(E2), record_carrier(E1))
        )
        assert report.anchored_through == E2
        assert report.unanchored_tail == ()

    def test_the_intent_inventory_is_reported_unevaluated(self) -> None:
        """§10.1: intent qualification is deferred, and the deferral is stated in
        the report itself rather than in a document beside it."""
        view = chain(
            genesis(),
            IntentEntryView(digest=E3, payload=b"an intent"),
            registration(E1, "tx-1"),
            settlement(E2, E1, "tx-1"),
        )
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(E2)))
        assert report.outcome == "validated"
        assert report.intents_unevaluated == (E3,)


# --- the carriers ----------------------------------------------------------


class TestRegistryCarrier:
    def test_a_record_of_another_type_refuses(self) -> None:
        artifact = HeadArtifact(CorpusSubject(CORPUS_ID), CORPUS_GENESIS, E1)
        with pytest.raises(ObserverCarrierInvalid):
            RegistryCarrier.from_record(artifact)  # pyright: ignore[reportArgumentType]

    def test_a_record_edited_past_its_grammar_refuses(self) -> None:
        record = LogHeadRecord(CorpusSubject(CORPUS_ID), CORPUS_GENESIS, E1, AnchorActOrigin("keith"))
        object.__setattr__(record, "head", "not a digest")
        with pytest.raises(ObserverCarrierInvalid):
            RegistryCarrier.from_record(record)

    def test_the_provenance_is_fixed_by_the_factory(self) -> None:
        carrier = record_carrier(E1)
        assert carrier.provenance == "named-local"
        assert [anchor.provenance for anchor in carrier.observed] == ["named-local"]


class TestArtifactCarrier:
    def test_bytes_that_are_not_an_artifact_refuse(self) -> None:
        with pytest.raises(ObserverCarrierInvalid):
            ArtifactCarrier.from_bytes(b"{}")

    def test_non_canonical_bytes_refuse(self) -> None:
        canonical = head_artifact_bytes(HeadArtifact(CorpusSubject(CORPUS_ID), CORPUS_GENESIS, E1))
        with pytest.raises(ObserverCarrierInvalid):
            ArtifactCarrier.from_bytes(canonical + b" ")

    def test_the_canonical_bytes_are_retained(self) -> None:
        canonical = head_artifact_bytes(HeadArtifact(CorpusSubject(CORPUS_ID), CORPUS_GENESIS, E1))
        carrier = ArtifactCarrier.from_bytes(canonical)
        assert carrier.data == canonical
        assert carrier.provenance == "supplied-export"
        assert [anchor.provenance for anchor in carrier.observed] == ["supplied-export"]


class TestEpochCarrier:
    def test_a_supplied_export_revalidates_its_packaging_identity(self) -> None:
        members = epoch_members()
        with pytest.raises(ObserverCarrierInvalid, match="recompute"):
            EpochCarrier.from_export(members, "0" * 64)

    def test_one_edited_member_byte_refuses(self) -> None:
        """The identity covers all eleven members, which is why the factory takes
        the complete mapping: one `bytes` value could never revalidate it."""
        members = epoch_members()
        identity = packaging_identity_of(members)
        members["coverage.yaml"] = members["coverage.yaml"] + b"\n"
        with pytest.raises(ObserverCarrierInvalid):
            EpochCarrier.from_export(members, identity)

    def test_a_short_member_set_refuses(self) -> None:
        members = epoch_members()
        del members["coverage.yaml"]
        with pytest.raises(ObserverCarrierInvalid, match="closed epoch layout"):
            EpochCarrier.from_export(members, packaging_identity_of(members))

    def test_an_unreadable_anchors_member_refuses(self) -> None:
        members = epoch_members()
        members["anchors.yaml"] = b"corpora: []\n"
        with pytest.raises(ObserverCarrierInvalid):
            EpochCarrier.from_export(members, packaging_identity_of(members))

    def test_a_named_local_epoch_is_read_from_its_directory(self, tmp_path: Path) -> None:
        carrier = local_epoch(tmp_path)
        assert carrier.provenance == "named-local"
        assert {anchor.provenance for anchor in carrier.observed} == {"named-local"}
        assert carrier.packaging_identity == packaging_identity_of(epoch_members())

    def test_the_provenance_a_reader_sees_is_the_one_eligibility_reads(self, tmp_path: Path) -> None:
        """One copy of the fact, not two. `provenance` is derived from the very
        anchors the eligibility rule consults, so there is no second field a
        `dataclasses.replace` could rewrite while the anchors stayed local — and
        no arm that could assert on the copy the verdict does not turn on."""
        carrier = local_epoch(tmp_path, world_head=E1)
        with pytest.raises(TypeError):
            dataclasses.replace(carrier, provenance="supplied-export")  # pyright: ignore[reportCallIssue]
        report = evaluate(WorldSubject(WORLD_ID), world_chain(), observers(carrier))
        assert report.outcome == "unresolvable"
        assert "observer-ineligible" in codes(report)

    def test_a_named_local_directory_that_lies_about_its_identity_refuses(self, tmp_path: Path) -> None:
        carrier_root = tmp_path / ("0" * 64)
        carrier_root.mkdir()
        for member, content in epoch_members().items():
            (carrier_root / member).write_bytes(content)
        with pytest.raises(ObserverCarrierInvalid, match="recompute"):
            EpochCarrier.from_named_local(carrier_root)

    def test_a_missing_epoch_directory_refuses(self, tmp_path: Path) -> None:
        with pytest.raises(ObserverCarrierInvalid):
            EpochCarrier.from_named_local(tmp_path / "nothing")


class TestConstruction:
    def test_a_carrier_is_unspellable_without_the_module_s_token(self) -> None:
        record = LogHeadRecord(CorpusSubject(CORPUS_ID), CORPUS_GENESIS, E1, AnchorActOrigin("keith"))
        with pytest.raises(TypeError):
            RegistryCarrier(record)  # pyright: ignore[reportCallIssue]
        with pytest.raises(ObserverCarrierInvalid):
            RegistryCarrier(object(), record, ())

    def test_an_observer_set_takes_carriers_only(self) -> None:
        with pytest.raises(TypeError):
            ObserverSet((object(),))  # pyright: ignore[reportArgumentType]
