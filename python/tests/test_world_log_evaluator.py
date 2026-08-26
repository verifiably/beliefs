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
from atoms.core.fingerprint import ABSENT as ENGINE_ABSENT
from atoms.core.scratch import CHAIN_LEAF
from test_world_log_codecs import (
    CUT8_CORPUS_ID,
    CUT8_REMINTED_ID,
    CUT8_SIBLING_ID,
    Chain,
    alternative_chain,
    capture_at,
    deleted_chain,
    deletion_plus_remint,
    duplicate_fulfillment,
    duplicate_settlement,
    foreign_world_genesis,
    forged_intent_beyond_the_anchor,
    fulfills_missing_intent,
    fulfills_non_intent,
    inspected,
    interior_deleted,
    interior_rewritten,
    manifest_remint,
    orphan_entry,
    pending_after_apply,
    pending_before_apply,
    populated_baseline,
    populated_corpus,
    settled_corpus,
    settled_world,
    sibling_branch,
    truncated_prefix,
    undecodable_genesis,
    wrong_form_genesis,
)
from test_world_log_codecs import MANIFEST as MANIFEST_PATH
from test_world_log_codecs import RECORD as RECORD_PATH

from science import root as science_root
from science.errors import ObserverCarrierInvalid
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
        intent_digest="sha256:" + "0" * 64,
        consumer_tag="science-corpus-write-v1",
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

    def test_a_store_subject_is_evaluated(self) -> None:
        """The root-lifecycle slice's widening: a store subject is judged, and
        a corpus-domain genesis under one is structural damage — the payload
        is not a store genesis at all."""
        report = evaluate(StoreSubject(STORE_ID), corpus_chain(), observers())
        assert report.outcome == "malformed"
        assert any(finding.code == "genesis-form-invalid" for finding in report.findings)

    def test_a_malformed_chain_answers_a_store_subject(self) -> None:
        report = evaluate(
            StoreSubject(STORE_ID),
            MalformedView(DefectView("cycle", E1, "an entry is its own ancestor")),
            observers(),
        )
        assert report.outcome == "malformed"


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
            intent_digest="sha256:" + "0" * 64,
            consumer_tag="science-corpus-write-v1",
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


# --- cut 8's declarations, over chains the engine itself calls well formed ---
#
# Cut 8 §5's obligation 1, in its literal form: every chain the arms below judge
# is a real directory of canonical entry envelopes, read back through the
# production seam's **detached** inspection — which takes no metadata root, so
# it runs wherever the suite runs. `test_world_log_codecs.CUT8_FABRICATIONS` is
# the catalogue of those fabrications with the engine's own verdict over each,
# and `acceptance/test_n2_cut8.py` walks it at declaration time. Every arm here
# names a builder from that catalogue, so no declaration rests on a chain
# nobody inspected.
#
# The view-level fabrications above remain the evaluator's *unit* arms — one
# arm per exit, per the module docstring. The declarations are these.


def judge(
    chain: Chain,
    *,
    subject: CorpusSubject | WorldSubject | StoreSubject | None = None,
    carriers: tuple[RegistryCarrier | EpochCarrier | ArtifactCarrier, ...] = (),
    presented: verify.PresentedIdentity | None = None,
    history: dict[str, bytes] | None = None,
    disk: tuple[tuple[str, object], ...] | None = None,
) -> verify.LogReport:
    """The evaluator over a real root: the engine's inspection, the engine's
    capture of the paths the arm judges, and the engine's own absent state."""
    return evaluate_log(
        subject if subject is not None else CorpusSubject(CUT8_CORPUS_ID),
        inspected(chain.root),
        ObserverSet(carriers),
        capture_at(chain.root, *chain.paths) if disk is None else disk,
        presented,
        ENGINE_ABSENT,
        history,
    )


def head_record(chain: Chain, head: str, *, corpus_id: str = CUT8_CORPUS_ID) -> RegistryCarrier:
    """A registry log-head record anchoring `head` under this chain's genesis."""
    return RegistryCarrier.from_record(
        LogHeadRecord(CorpusSubject(corpus_id), chain.digests[0], head, AnchorActOrigin("keith"))
    )


def head_export(chain: Chain, head: str, *, world_id: str = WORLD_ID) -> ArtifactCarrier:
    """An exported head artifact — L11's only eligible carrier for a world."""
    return ArtifactCarrier.from_bytes(
        head_artifact_bytes(HeadArtifact(WorldSubject(world_id), chain.digests[0], head))
    )


def logged_surface(view: WellFormedView) -> dict[str, object]:
    """The surface the chain's own committed transitions leave behind."""
    surface = dict(view.genesis.baseline)
    committed = {
        entry.registration
        for entry in view.entries
        if type(entry) is SettledEntryView and entry.committed
    }
    for entry in view.entries:
        if type(entry) is RegisteredEntryView and entry.digest in committed:
            surface.update(entry.final)
    return surface


def well_formed(chain: Chain) -> WellFormedView:
    view = inspected(chain.root)
    assert type(view) is WellFormedView, f"the engine calls this fabrication {type(view).__name__}"
    return view


def defect_of(chain: Chain) -> DefectView:
    view = inspected(chain.root)
    assert type(view) is MalformedView, f"the engine calls this fabrication {type(view).__name__}"
    return view.defect


# --- L2 ---------------------------------------------------------------------


def test_duplicate_settlement_is_malformed_at_step_one(tmp_path: Path) -> None:
    """L2u3. Two settlements for one registration → malformed at step 1.

    The arm's point *is* the defect, so §5's obligation 1 is discharged the
    other way: the engine reports exactly `duplicate-settlement` and no other
    defect, and the anchor supplied would refute a well-formed chain — so the
    `malformed` verdict is step 1 deciding before step 2, not step 2 finding
    nothing to say.
    """
    chain = duplicate_settlement(tmp_path)
    defect = defect_of(chain)
    assert defect.kind == "duplicate-settlement"
    assert defect.subject == chain.tip

    report = judge(chain, carriers=(head_record(chain, STRANGER),))

    assert report.outcome == "malformed"
    assert codes(report) == ["chain-malformed"]
    assert report.findings[0].detail == "kind=duplicate-settlement"
    assert report.findings[0].ref == chain.tip
    assert report.anchored_through is None


def test_copied_root_pending_is_unresolvable_in_both_variants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L2u4. A pending entry on a copied root is `unresolvable` at step 3 in
    **both** variants — the copy caught before apply (record absent) and after
    apply (record present) — never refuted as a disk mismatch, and never
    inferred from disk: `replay` is made to fail the test if it is reached.
    """
    monkeypatch.setattr(verify, "replay", _never)
    reports: list[verify.LogReport] = []
    for build, present in ((pending_before_apply, False), (pending_after_apply, True)):
        chain = build(tmp_path / build.__name__)
        assert (chain.root / RECORD_PATH).exists() is present
        view = well_formed(chain)
        assert len(view.pending) == 1

        report = judge(chain, carriers=(head_record(chain, view.tip),))

        assert report.outcome == "unresolvable"
        assert report.pending == view.pending
        assert codes(report) == ["pending-unresolved"]
        reports.append(report)

    # The two variants differ on disk and nowhere in the verdict: the state of
    # the record the transaction would have written is not consulted at all.
    assert codes(reports[0]) == codes(reports[1])
    assert [report.outcome for report in reports] == ["unresolvable", "unresolvable"]


# --- L3 ---------------------------------------------------------------------


def test_valid_prefix_truncation_refutes_naming_the_unreachable_head(tmp_path: Path) -> None:
    """L3u1. Truncated to a valid prefix behind the anchored head → refuted at
    step 2, the finding naming the head the surviving chain cannot reach."""
    chain = truncated_prefix(tmp_path)
    view = well_formed(chain)
    assert chain.anchor in chain.removed
    assert chain.anchor not in [entry.digest for entry in view.entries]

    report = judge(chain, carriers=(head_record(chain, chain.anchor),))

    assert report.outcome == "refuted"
    assert codes(report) == ["anchor-unreachable"]
    assert report.findings[0].ref == chain.anchor


def test_interior_damage_is_malformed(tmp_path: Path) -> None:
    """L3u2. An interior entry **deleted or rewritten** → broken linkage,
    malformed at step 1 — which is the row's "never silently validated" clause:
    `malformed` is an outcome no other step can overwrite, and the contrast
    against a chain the same anchor set *does* validate is L9u5's arm.

    Both spellings, because the row states both: a deletion leaves a successor
    naming a predecessor that is gone, and a rewrite moves the bytes out from
    under the content name the chain files them by.
    """
    for build, kind in ((interior_deleted, "missing-predecessor"), (interior_rewritten, "name-mismatch")):
        chain = build(tmp_path / build.__name__)
        assert defect_of(chain).kind == kind

        report = judge(chain, carriers=(head_record(chain, chain.digests[0]),))

        assert report.outcome == "malformed"
        assert codes(report) == ["chain-malformed"]
        assert report.findings[0].detail == f"kind={kind}"


def test_sibling_branch_is_malformed(tmp_path: Path) -> None:
    """L3u3. A sibling branch raw-appended beside the retained original →
    malformed at step 1 (§3's linearity invariant), never a silently ignored
    fork: the engine names the fork itself, and `malformed` is the outcome."""
    chain = sibling_branch(tmp_path)
    defect = defect_of(chain)
    assert defect.kind == "sibling-branch"
    assert defect.subject == chain.digests[0]

    report = judge(chain, carriers=(head_record(chain, chain.digests[0]),))

    assert report.outcome == "malformed"
    assert codes(report) == ["chain-malformed"]


def test_orphan_entry_is_malformed(tmp_path: Path) -> None:
    """L3u4. An orphan entry → malformed at step 1, never silently validated.


    The engine names the directory spelling `missing-predecessor`: its
    `orphan-history` kind is reserved for a disconnected component with valid
    *internal* linkage, which needs a digest fixed point no content-named
    directory fixture can honestly construct and which the atoms suite
    certifies through the typed validation core. The row's claim — an orphan
    entry is malformed at step 1 — is what is asserted here.
    """
    chain = orphan_entry(tmp_path)
    assert defect_of(chain).kind == "missing-predecessor"

    report = judge(chain, carriers=(head_record(chain, chain.digests[0]),))

    assert report.outcome == "malformed"
    assert codes(report) == ["chain-malformed"]


# --- L4 ---------------------------------------------------------------------


def test_chain_deletion_refutes_against_a_registry_anchor(tmp_path: Path) -> None:
    """L4u1. Kernel §8.7's "detectable journal removal", discharged: the chain
    deleted while a registry log-head record survives in the observer set →
    refuted, the finding naming the head that no longer exists."""
    chain = deleted_chain(tmp_path)
    assert inspected(chain.root) == AbsentView()

    report = judge(chain, carriers=(head_record(chain, chain.anchor),))

    assert report.outcome == "refuted"
    assert codes(report) == ["anchor-chain-absent"]
    assert report.findings[0].ref == chain.anchor
    assert len(report.observer_bound) == 1


def test_two_anchored_corpora_refute_exactly_the_chainless_one(tmp_path: Path) -> None:
    """L4u2. Two anchored corpora, one arriving chainless: the subject binding
    refutes exactly the arriving one and never the sibling.

    §5's obligation 4 is asserted here rather than assumed — two *distinct*
    roots under two *distinct* `corpus_id`s, both anchored, before either chain
    is removed. The two share a genesis digest exactly, because the Science
    corpus genesis payload carries no per-corpus identity: an anchor matched by
    opaque genesis digest alone, or by elimination, would pool them.
    """
    arriving = settled_corpus(tmp_path, corpus_id=CUT8_CORPUS_ID, name="arriving")
    sibling = settled_corpus(tmp_path, corpus_id=CUT8_SIBLING_ID, name="sibling")
    assert arriving.root != sibling.root
    assert CUT8_CORPUS_ID != CUT8_SIBLING_ID
    assert arriving.digests[0] == sibling.digests[0]
    assert arriving.tip != sibling.tip
    bound = (
        head_record(arriving, arriving.tip, corpus_id=CUT8_CORPUS_ID),
        head_record(sibling, sibling.tip, corpus_id=CUT8_SIBLING_ID),
    )
    assert well_formed(arriving).tip == arriving.tip
    assert well_formed(sibling).tip == sibling.tip

    for digest in tuple(arriving.digests):
        arriving.leaf(digest).unlink()
    (arriving.root / CHAIN_LEAF).rmdir()

    refuted = judge(arriving, subject=CorpusSubject(CUT8_CORPUS_ID), carriers=bound)
    survivor = judge(sibling, subject=CorpusSubject(CUT8_SIBLING_ID), carriers=bound)

    assert refuted.outcome == "refuted"
    assert [finding.ref for finding in refuted.findings] == [arriving.tip]
    assert len(refuted.observer_bound) == 1
    assert sibling.tip not in refuted.observer_bound[0]
    assert survivor.outcome == "validated"
    assert survivor.findings == ()


def test_manifest_remint_reports_mismatch_and_replay_refutes(tmp_path: Path) -> None:
    """L4u3. The manifest raw re-minted A → B with the chain present, verified
    selecting **A**: A-bound anchors stay admitted by the selected subject, the
    manifest mismatch is reported separately, and replay **refutes** the edit —
    never `unresolvable` by subject disqualification.

    Cut 8 §6's first freeze obligation is asserted, not assumed: the re-mint is
    the **only** delta between the surface the chain logged and the surface on
    disk, so the refutation is that edit and nothing interposed beside it.
    """
    chain = manifest_remint(tmp_path)
    view = well_formed(chain)
    disk = capture_at(chain.root, *chain.paths)
    logged = logged_surface(view)
    assert [path for path, state in disk if logged[path] != state] == [MANIFEST_PATH]

    report = judge(
        chain,
        carriers=(head_record(chain, chain.anchor),),
        presented=verify.PresentedManifest(corpus_id=CUT8_REMINTED_ID),
    )

    assert report.outcome == "refuted"
    assert "subject-mismatch" in codes(report)
    assert "replay-disagreement" in codes(report)
    assert [finding.ref for finding in report.findings if finding.code == "subject-mismatch"] == ["manifest"]
    assert [finding.ref for finding in report.findings if finding.code == "replay-disagreement"] == [
        f"head:{MANIFEST_PATH}"
    ]
    assert len(report.observer_bound) == 1
    assert report.anchored_through == chain.anchor


def test_same_genesis_alternative_chain_refutes_by_ancestry(tmp_path: Path) -> None:
    """L4u5. A self-consistent alternative chain under the **same constant
    genesis** and the same `corpus_id` → refuted through anchored-head
    unreachability — spec §1.2's stated mechanism for corpus replacement, since
    a fabricated distinct genesis would be malformed at genesis-form validation
    before any anchor judgment (D1's arm)."""
    chain = alternative_chain(tmp_path)
    view = well_formed(chain)
    assert view.genesis.digest == chain.digests[0]
    assert chain.anchor in chain.removed
    assert chain.anchor not in [entry.digest for entry in view.entries]

    report = judge(chain, carriers=(head_record(chain, chain.anchor),))

    assert report.outcome == "refuted"
    assert codes(report) == ["anchor-unreachable"]
    assert "anchor-genesis-mismatch" not in codes(report)


def test_deletion_plus_remint_refutes_as_removal_under_selected_subject(tmp_path: Path) -> None:
    """L4u7. A's chain deleted **and** its `corpus.yaml` re-minted as B, verified
    explicitly selecting A with A's anchor supplied → refuted as removal. The
    selected subject associates the anchor; the presented manifest never
    discards it into an empty-set `unresolvable`."""
    chain = deletion_plus_remint(tmp_path)
    assert inspected(chain.root) == AbsentView()

    report = judge(
        chain,
        carriers=(head_record(chain, chain.anchor),),
        presented=verify.PresentedManifest(corpus_id=CUT8_REMINTED_ID),
    )

    assert report.outcome == "refuted"
    assert "anchor-chain-absent" in codes(report)
    assert "subject-mismatch" in codes(report)
    assert len(report.observer_bound) == 1
    assert CUT8_REMINTED_ID != CUT8_CORPUS_ID


# --- L7 ---------------------------------------------------------------------


def test_fulfills_naming_missing_or_nonancestor_intent_is_malformed(tmp_path: Path) -> None:
    """L7u1, **partial**. A `fulfills` naming an intent the chain does not carry
    — missing, or present but not an intent — is `fulfills-invalid`, malformed
    at step 1, before any anchor judgment.

    The **non-ancestor** spelling is not run here and cannot be: in a linear
    chain every *existing* earlier entry is an ancestor, and a later digest
    depends on the referencing entry, so a directory fixture cannot honestly
    construct one. The atoms chain-inspection design names it one of three
    classes certified through the typed validation core only, and that is where
    it is certified.
    """
    for build in (fulfills_missing_intent, fulfills_non_intent):
        chain = build(tmp_path / build.__name__)
        assert defect_of(chain).kind == "fulfills-invalid"

        report = judge(chain, carriers=(head_record(chain, STRANGER),))

        assert report.outcome == "malformed"
        assert codes(report) == ["chain-malformed"]
        assert report.findings[0].detail == "kind=fulfills-invalid"


def test_duplicate_committed_fulfillment_is_malformed(tmp_path: Path) -> None:
    """L7u2. A second committed registration fulfilling one intent → malformed,
    classified before any qualification reduction is attempted (T2's arm)."""
    chain = duplicate_fulfillment(tmp_path)
    defect = defect_of(chain)
    assert defect.kind == "duplicate-fulfillment"
    assert defect.subject == chain.tip

    report = judge(chain, carriers=(head_record(chain, STRANGER),))

    assert report.outcome == "malformed"
    assert codes(report) == ["chain-malformed"]
    assert report.intents_unevaluated == ()


# --- L9 ---------------------------------------------------------------------


def test_old_anchor_never_validates_past_a_missing_newer_head(tmp_path: Path) -> None:
    """L9u1. An observer set holding an old *reachable* anchor and a newer
    anchored head absent from the chain → refuted, never validated-through-the
    -old. The contrast is the arm: the old anchor alone validates."""
    chain = settled_corpus(tmp_path)
    old = chain.digests[1]
    assert old in [entry.digest for entry in well_formed(chain).entries]

    through_the_old = judge(chain, carriers=(head_record(chain, old),))
    with_the_newer = judge(chain, carriers=(head_record(chain, old), head_record(chain, STRANGER)))

    assert through_the_old.outcome == "validated"
    assert through_the_old.anchored_through == old
    assert with_the_newer.outcome == "refuted"
    assert codes(with_the_newer) == ["anchor-unreachable"]
    assert with_the_newer.findings[0].ref == STRANGER


def test_incomparable_anchored_heads_refute(tmp_path: Path) -> None:
    """L9u2. Two mutually incomparable anchored heads for one genesis → refuted.

    R22: `entries` is a linearization and a sibling branch is a defect, so two
    *reachable* heads are always ordered — the incomparable arm fires exactly
    when the chain can place neither of a differing pair.
    """
    chain = settled_corpus(tmp_path)

    report = judge(chain, carriers=(head_record(chain, STRANGER), head_record(chain, FOREIGN)))

    assert report.outcome == "refuted"
    incomparable = [finding for finding in report.findings if finding.code == "anchors-incomparable"]
    assert len(incomparable) == 1
    assert {incomparable[0].ref, incomparable[0].detail.removeprefix("other=")} == {STRANGER, FOREIGN}


def test_empty_observer_set_is_unresolvable_with_bound_recorded(tmp_path: Path) -> None:
    """L9u3. The empty observer set → `unresolvable`, with the observer bound
    recorded as the empty bound rather than omitted, and replay not reached."""
    chain = settled_corpus(tmp_path)
    view = well_formed(chain)

    report = judge(chain)

    assert report.outcome == "unresolvable"
    assert report.observer_bound == ()
    assert report.anchored_through is None
    assert report.unanchored_tail == tuple(entry.digest for entry in view.entries)
    assert codes(report) == ["unanchored"]


def test_anchored_through_and_observer_set_are_report_fields(tmp_path: Path) -> None:
    """L9u4. `anchored-through` and the observer set are **fields of the
    report**, present in every outcome and never derived by a caller."""
    chain = populated_corpus(tmp_path)
    view = well_formed(chain)
    fields = {field.name for field in dataclasses.fields(verify.LogReport)}
    assert {"anchored_through", "observer_bound"} <= fields

    report = judge(chain, carriers=(head_record(chain, chain.anchor),))

    assert report.outcome == "validated"
    assert report.anchored_through == chain.anchor
    assert report.observer_bound == (
        (
            f"registry-record provenance=named-local custody=read-from-root "
            f"subject=corpus:{CUT8_CORPUS_ID} genesis={view.genesis.digest} head={chain.anchor}"
        ),
    )
    # And in a refuted outcome too, so the fields are not a validated-only
    # decoration: the bound is reported whatever the verdict (R25).
    refuted = judge(chain, carriers=(head_record(chain, chain.anchor), head_record(chain, STRANGER)))
    assert refuted.outcome == "refuted"
    assert refuted.anchored_through == chain.anchor
    assert len(refuted.observer_bound) == 2


def test_malformed_structure_stops_before_anchor_judgment(tmp_path: Path) -> None:
    """L9u5. Malformed structure stops evaluation before any anchor judgment.

    The same observer set, over the damaged chain and over the chain it was
    damaged from: it refutes the well-formed one and is never consulted for a
    verdict about the malformed one — which is what makes this an ordering
    claim rather than a claim that nothing happened to be found.
    """
    damaged = interior_deleted(tmp_path / "damaged")
    healthy = populated_corpus(tmp_path / "healthy")
    assert defect_of(damaged).kind == "missing-predecessor"

    malformed = judge(damaged, carriers=(head_record(damaged, STRANGER),))
    refuted = judge(healthy, carriers=(head_record(healthy, STRANGER),))

    assert malformed.outcome == "malformed"
    assert codes(malformed) == ["chain-malformed"]
    assert malformed.anchored_through is None
    assert malformed.unanchored_tail == ()
    assert refuted.outcome == "refuted"
    assert codes(refuted) == ["anchor-unreachable"]


# --- L11 --------------------------------------------------------------------


def test_in_root_epoch_ineligible_for_world_subject_but_eligible_for_corpus(tmp_path: Path) -> None:
    """L11u1. Eligibility is carrier-specific, not a property of the epoch.

    One epoch's **byte-identical** members, presented three ways: stored inside
    the world root and offered for the world subject → not accepted, an
    `observer-ineligible` finding and an empty bound; the same bytes supplied as
    an **export** → accepted; and the same stored epoch offered for a **corpus**
    subject → accepted. The provenance discriminator (§4.1) is the whole of the
    difference.
    """
    world = settled_world(tmp_path)
    corpus = settled_corpus(tmp_path)
    members = epoch_members(
        corpus_head=corpus.tip,
        world_head=world.tip,
        corpus_id=CUT8_CORPUS_ID,
        corpus_genesis=corpus.digests[0],
        world_genesis=world.digests[0],
    )
    identity = packaging_identity_of(members)
    stored = tmp_path / "in-root" / identity
    stored.mkdir(parents=True)
    for member, content in members.items():
        (stored / member).write_bytes(content)
    in_root = EpochCarrier.from_named_local(stored)
    exported = EpochCarrier.from_export(members, identity)
    assert {member: (stored / member).read_bytes() for member in members} == members

    refused = judge(world, subject=WorldSubject(WORLD_ID), carriers=(in_root,))
    accepted = judge(world, subject=WorldSubject(WORLD_ID), carriers=(exported,))
    for_corpus = judge(corpus, subject=CorpusSubject(CUT8_CORPUS_ID), carriers=(in_root,))

    assert refused.outcome == "unresolvable"
    assert refused.observer_bound == ()
    assert "observer-ineligible" in codes(refused)
    assert accepted.outcome == "validated"
    assert "provenance=supplied-export" in accepted.observer_bound[0]
    assert for_corpus.outcome == "validated"
    assert "provenance=named-local" in for_corpus.observer_bound[0]


# --- L12 --------------------------------------------------------------------


def test_raw_log_edit_within_anchored_prefix_is_malformed_or_refuted(tmp_path: Path) -> None:
    """L12u4. A raw edit of the log path **within the anchored prefix** is
    caught at step 1 (interior damage, malformed) or at step 2 (prefix
    truncation, refuted) — the log path is bookkeeping, and editing it is not a
    way through."""
    damaged = interior_rewritten(tmp_path / "damaged")
    assert defect_of(damaged).kind == "name-mismatch"
    malformed = judge(damaged, carriers=(head_record(damaged, damaged.digests[0]),))

    truncated = truncated_prefix(tmp_path / "truncated")
    well_formed(truncated)
    refuted = judge(truncated, carriers=(head_record(truncated, truncated.anchor),))

    assert malformed.outcome == "malformed"
    assert codes(malformed) == ["chain-malformed"]
    assert refuted.outcome == "refuted"
    assert codes(refuted) == ["anchor-unreachable"]


def test_valid_raw_append_beyond_anchor_passes_as_the_residue(tmp_path: Path) -> None:
    """L12u5, the pinned negative. A structurally valid raw append beyond the
    maximal anchor — most sharply a **forged intent** — passes steps 1 and 2 and
    is reported as L5's unanchored residue. This is why every
    entry-proves-an-act claim holds only under the cooperative-write
    assumption."""
    chain = forged_intent_beyond_the_anchor(tmp_path)
    view = well_formed(chain)
    forged = view.entries[-1]
    assert type(forged) is IntentEntryView
    assert forged.payload == b"an intent no act ever appended"

    report = judge(chain, carriers=(head_record(chain, chain.anchor),))

    assert report.outcome == "validated"
    assert report.anchored_through == chain.anchor
    assert report.unanchored_tail == (forged.digest,)
    assert report.intents_unevaluated == (forged.digest,)


# --- D1 ---------------------------------------------------------------------


def test_genesis_form_malformation_and_world_id_mismatch_split(tmp_path: Path) -> None:
    """D1. An undecodable genesis payload, a wrong-form one, or a non-empty
    baseline → **malformed before anchor evaluation**; a *valid* world genesis
    naming a different `world_id` → **subject mismatch, never malformed**.

    All four chains are well formed to the engine — an entry payload is opaque
    bytes to the validator — so every verdict below is the evaluator's own
    step-1 reading of Science's genesis form (spec §4.2, §1.3).
    """
    for build in (undecodable_genesis, wrong_form_genesis, populated_baseline):
        chain = build(tmp_path / build.__name__)
        well_formed(chain)

        report = judge(chain, carriers=(head_record(chain, chain.tip),))

        assert report.outcome == "malformed", build.__name__
        assert codes(report) == ["genesis-form-invalid"], build.__name__
        assert report.anchored_through is None
    assert "baseline" in judge(
        populated_baseline(tmp_path / "again"), carriers=()
    ).findings[0].message

    other = foreign_world_genesis(tmp_path)
    well_formed(other)

    mismatch = judge(
        other,
        subject=WorldSubject(WORLD_ID),
        carriers=(head_export(other, other.tip),),
        presented=verify.PresentedWorldIds(configured=WORLD_ID, mirrored=WORLD_ID),
    )

    assert mismatch.outcome == "validated"
    assert [finding.ref for finding in mismatch.findings if finding.code == "subject-mismatch"] == ["genesis"]
    assert "genesis-form-invalid" not in codes(mismatch)
