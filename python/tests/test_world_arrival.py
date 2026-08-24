"""Verified arrival, and the refusals that stand between a replica and the
registry (design §6.2, §6.3, §6.4).

**Arrival is the evaluator plus the one admission core.** `World.admit` refuses
`ReplicaOf` outright — a bare admit holds no verdict to report — and
`admit_arrival` is the route that has one: it loads the manifest itself, under
the arriving root's own lock, inspects that root **detached**, states its
surface, judges, and only then commits through the very core `World.admit`
commits through. Admission identity is not amended by any of it.

**Why the seam is a stand-in and the locks are real.** As in
`test_world_log_audit`, every arm below builds a `LogSeam` whose inspection and
capture answer from tables while `world_lock` and `corpus_lock` are the
production lookups, so an arm claiming a lock was held claims it about the very
object an opened `World` and a corpus writer contend for. The two exceptions
are at the foot of the module: the `LogEvidenceRefused` arm, which drives the
**production** seam over a real unrepresentable entry, and the pending-gate arm,
which drives the real `DurableExecutor`.

**The chain fabrication is `test_world_log_audit`'s**, imported rather than
restated: one module states how a chain that agrees with a scanned surface is
built, and both boundaries judge chains built that one way.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

import pytest
from atoms.chain.errors import PendingUnresolved
from atoms.chain.model import GenesisEntry
from atoms.core.errors import PreconditionRefused
from fixtures_cut6 import PINS
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import CreateOp, DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads, corpus_at
from test_world_log_audit import (
    ABSENT,
    Captures,
    Inspections,
    corpus_anchor,
    corpus_root,
    digest,
    state,
    surfaced,
    tree,
)
from test_world_log_codecs import write_chain

from science import errors as science_errors
from science import root as science_root
from science.corpus import _operation_lock_for
from science.errors import (
    ArrivalRefused,
    BuildContended,
    CorpusIdKnown,
    LogEvidenceRefused,
    ProvenanceMismatch,
    ReplicaAdmissionRequiresVerification,
    SubjectMismatch,
)
from science.world import anchors, logmodel, registry, verify

WORLD_ID = "f" * 32


# --- the world, the arriving root, and the act ---------------------------------


def make_world(tmp_path: Path, *corpus_roots: Path) -> registry.World:
    """A world whose executor really writes: the arms below compare the bytes an
    arrival left in `registry/` against the bytes a fixture admission projects."""
    return registry.World(
        registry.WorldConfig(tmp_path / "world", WORLD_ID, corpus_roots),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
    )


def unreached_registered(root: Path) -> logmodel.ChainView:
    raise AssertionError(f"{root}: arrival inspects an arriving root **detached** (§2.1, §6.2)")


def unreached_head(root: Path) -> logmodel.ChainHead:
    raise AssertionError(f"{root}: arrival inspects a chain — it does not read a head")


def make_seam(inspections: Inspections, captures: Captures) -> verify.LogSeam:
    @contextmanager
    def world_lock(root: Path) -> Iterator[None]:
        with registry._world_lock_for(Path(root)):
            yield

    return verify.LogSeam(
        inspect_registered=unreached_registered,
        inspect_detached=inspections,
        capture=captures,
        read_head=unreached_head,
        absent_state=ABSENT,
        world_lock=world_lock,
        corpus_lock=_operation_lock_for,
        # The arriving copies these arms fabricate are metadata-less, which
        # is also the state that keeps the detached inspection selected.
        lifecycle_state=lambda _root: "metadata-less",
    )


def arrive(
    world: registry.World,
    corpus_root_path: Path,
    view: logmodel.ChainView,
    *,
    parent: str = ALPHA,
    observers: tuple[verify.ObserverCarrier, ...] = (),
    actor: str = "alice",
    history: Mapping[str, bytes] | None = None,
    inspections: Inspections | None = None,
    captures: Captures | None = None,
) -> tuple[registry.AdmissionRecord, verify.LogReport]:
    inspections = inspections if inspections is not None else Inspections()
    captures = captures if captures is not None else Captures()
    inspections.set(corpus_root_path, view)
    return verify._admit_arrival(
        world,
        corpus_root_path,
        registry.ReplicaOf(parent),
        verify.ObserverSet(observers),
        actor=actor,
        history=history,
        seam=make_seam(inspections, captures),
    )


def replica_root(tmp_path: Path, corpus_id: str = ALPHA, *, name: str = "arriving") -> Path:
    """A copied corpus root: a replica carries its parent's own manifest, which
    is exactly what `_validate_provenance` already requires of `ReplicaOf`."""
    return corpus_root(tmp_path, corpus_id, name=name)


def fixture_admission(root: Path, parent: str = ALPHA, actor: str = "alice") -> registry.AdmissionRecord:
    """The record `World.admit` would mint from the same three inputs — the
    fixture arrival's identity is compared against, never derived from."""
    return registry.AdmissionRecord(registry.load_manifest(root), registry.ReplicaOf(parent), actor)


def pending_view(view: logmodel.WellFormedView) -> logmodel.WellFormedView:
    """The same chain with one registration nothing settled.

    Detached inspection runs no recovery, so a copied root's staged registration
    survives into the view honestly — which is the state §6.2 refuses.
    """
    return logmodel.WellFormedView(
        genesis=view.genesis,
        entries=view.entries,
        tip=view.tip,
        pending=(("tx-9", digest("unsettled-registration")),),
    )


def unreachable_anchor(view: logmodel.WellFormedView, corpus_id: str = ALPHA) -> verify.RegistryCarrier:
    """An anchor stating a head under this chain's genesis that its ancestry
    cannot reach — §4.2 step 2's refutation."""
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.CorpusSubject(corpus_id),
            view.genesis.digest,
            digest("a head this chain never carried"),
            anchors.AnchorActOrigin("alice"),
        )
    )


def registry_files(world: registry.World) -> dict[str, bytes]:
    directory = world.config.world_root / "registry"
    if not directory.is_dir():
        return {}
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


# --- the four causes, ranked from the report's fields (§6.2) --------------------


class TestTheArrivalCauses:
    def test_arrival_cause_ranking_from_report_fields(self, tmp_path):
        # D2. The cause is read off the **report**, never off which precedence
        # step produced the outcome — and the four rank
        # `malformed > refuted > pending > chainless`.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        clean = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        # malformed, and it outranks a refuting anchor: step 1 stops there.
        malformed = logmodel.MalformedView(
            logmodel.DefectView(kind="cycle", subject=digest("x"), detail="a cycle")
        )
        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, malformed, observers=(unreachable_anchor(clean),))
        assert (caught.value.cause, caught.value.report.outcome) == ("malformed", "malformed")

        # refuted, and it outranks the pending set the same report carries.
        both = pending_view(clean)
        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, both, observers=(unreachable_anchor(clean),))
        assert (caught.value.cause, caught.value.report.outcome) == ("refuted", "refuted")
        assert caught.value.report.pending != ()

        # pending, from the **field**: with an empty observer set this chain is
        # `unresolvable` at step 2 (unanchored) and never reaches step 3, and it
        # still refuses `pending` — §6.2's own worked example.
        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, both)
        assert (caught.value.cause, caught.value.report.outcome) == ("pending", "unresolvable")
        assert caught.value.report.pending == (("tx-9", digest("unsettled-registration")),)

        # chainless: an `AbsentChain` is `unresolvable` exactly as a fresh
        # unanchored chain is, and only the report's own finding separates them.
        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, logmodel.AbsentView())
        assert (caught.value.cause, caught.value.report.outcome) == ("chainless", "unresolvable")
        assert verify.CHAIN_ABSENT in {finding.code for finding in caught.value.report.findings}

        # The same absent chain with something anchoring it is a *removal*, not
        # a replica that traveled light: the outcome is `refuted` and the cause
        # ranks above `chainless`, which is why the two are read off the report
        # rather than off the view.
        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, logmodel.AbsentView(), observers=(corpus_anchor(clean),))
        assert (caught.value.cause, caught.value.report.outcome) == ("refuted", "refuted")

        assert registry_files(world) == {}

    def test_a_refusal_carries_the_complete_report_and_names_the_remedy(self, tmp_path):
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        clean = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        with pytest.raises(ArrivalRefused) as caught:
            arrive(world, root, pending_view(clean))

        report = caught.value.report
        assert type(report) is verify.LogReport
        # The whole report, not a summary of it: the pending set, the intent
        # inventory §10.1 defers, and the findings all travel with the refusal.
        assert report.pending and report.intents_unevaluated == ()
        # And the pending set is the **field** the cause was read from, not a
        # finding: with no observer bound this report stopped at step 2, so it
        # states `unanchored` and never reaches step 3's pending finding at all.
        assert [finding.code for finding in report.findings] == ["unanchored"]
        assert caught.value.remedy in str(caught.value)
        assert "settlement evidence" in caught.value.remedy

        # Bind an anchor and the same chain reaches step 3, which is where the
        # finding is written. The cause is `pending` either way.
        with pytest.raises(ArrivalRefused) as anchored:
            arrive(world, root, pending_view(clean), observers=(corpus_anchor(clean),))
        assert anchored.value.cause == "pending"
        assert "pending-unresolved" in {finding.code for finding in anchored.value.report.findings}

    def test_the_cause_vocabulary_is_closed_and_every_member_names_a_remedy(self):
        # The vocabulary is closed by the remedy table itself: a fifth cause
        # with no remedy could not be raised, which is the point of §6.2's
        # "the remedy named".
        assert set(science_errors._ARRIVAL_REMEDIES) == {"malformed", "refuted", "pending", "chainless"}
        assert all(remedy for remedy in science_errors._ARRIVAL_REMEDIES.values())


# --- what is admissible (§6.2) --------------------------------------------------


class TestWhatIsAdmitted:
    def test_an_unanchored_fresh_chain_is_admitted_with_its_bound_recorded(self, tmp_path):
        # An arrival at a world holding no anchor for the parent must be
        # possible, and the unanchored bound is what the report records.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        record, report = arrive(world, root, view)

        assert (report.outcome, report.observer_bound) == ("unresolvable", ())
        assert report.unanchored_tail == tuple(entry.digest for entry in view.entries)
        assert "unanchored" in {finding.code for finding in report.findings}
        assert record == fixture_admission(root)

    def test_a_validated_arrival_returns_the_record_and_the_report_side_by_side(self, tmp_path):
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        record, report = arrive(world, root, view, observers=(corpus_anchor(view),))

        assert report.outcome == "validated"
        assert report.anchored_through == view.tip
        # The bound is never discarded — and it never enters admission identity.
        assert len(report.observer_bound) == 1 and "registry-record" in report.observer_bound[0]
        assert record == fixture_admission(root)

    def test_bare_admit_refusal_and_shared_core_identity(self, tmp_path, monkeypatch):
        # D3. Two claims, and they are one claim: the verified route is the only
        # route for a replica, and it is not a second registration path.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)

        with pytest.raises(ReplicaAdmissionRequiresVerification):
            world.admit(root, provenance=registry.ReplicaOf(ALPHA), actor="alice")
        assert registry_files(world) == {}

        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        record, _report = arrive(world, root, view, observers=(corpus_anchor(view),))

        # Byte-identical to a fixture admission of the same inputs: the record,
        # its digest, the path it was filed at and the bytes filed there.
        expected = fixture_admission(root)
        expected_digest = registry.admission_digest(expected)
        assert record == expected
        assert registry.admission_digest(record) == expected_digest
        assert registry_files(world) == {
            f"{expected_digest}.yaml": registry._record_bytes(registry.admission_projection(expected))
        }

        # And the core is literally shared: both callers route through it.
        seen: list[str] = []
        real = registry._locked_admit
        monkeypatch.setattr(
            registry,
            "_locked_admit",
            lambda state_, world_root, factory, manifest_of, provenance, actor: seen.append(
                type(provenance).__name__
            )
            or real(state_, world_root, factory, manifest_of, provenance, actor),
        )
        fresh = corpus_at(tmp_path / "fresh", BETA)
        world.admit(fresh, provenance=registry.Fresh(), actor="alice")
        arrive(make_world(tmp_path / "second", root), root, view, observers=(corpus_anchor(view),))

        assert seen == ["Fresh", "ReplicaOf"]

    def test_the_admission_is_idempotent_through_the_shared_core(self, tmp_path):
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        first, _ = arrive(world, root, view, observers=(corpus_anchor(view),))
        before = registry_files(world)
        second, _ = arrive(world, root, view, observers=(corpus_anchor(view),))

        assert second == first
        assert registry_files(world) == before

    def test_an_id_already_admitted_under_another_provenance_still_refuses(self, tmp_path):
        # The core's own refusals are not weakened by the verified route.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        world.admit(root, provenance=registry.Fresh(), actor="alice")
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        with pytest.raises(CorpusIdKnown):
            arrive(world, root, view, observers=(corpus_anchor(view),))

    def test_retirement_appends_status_and_deletes_nothing(self, tmp_path):
        # L13u4. The registry is append-only: a terminal status is a *new*
        # content-addressed record beside the admission, never an edit of it.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)
        record, _ = arrive(world, root, view, observers=(corpus_anchor(view),))
        admitted = registry_files(world)

        status = world.retire(record.corpus_id, actor="alice")

        after = registry_files(world)
        assert set(admitted) < set(after)
        assert {name: after[name] for name in admitted} == admitted
        assert sorted(set(after) - set(admitted)) == [f"{registry.status_digest(status)}.yaml"]
        assert world.status(record.corpus_id).live is False


# --- the ordered refusals (§6.2, §6.3) ------------------------------------------


class TestTheRefusalOrdering:
    def test_refusal_ordering_report_causes_then_mismatch_then_admission(self, tmp_path):
        # D4. Three positions, pinned in one arm: a report cause outranks the
        # subject mismatch, the mismatch is decided **before** the transaction,
        # and only what survives both is admitted.
        root = replica_root(tmp_path, BETA)  # a manifest that is not the parent
        world = make_world(tmp_path, root)
        clean = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        # Pending *and* mismatched: the report cause wins, so the caller is told
        # about the chain rather than about the identity.
        with pytest.raises(ArrivalRefused) as refused:
            arrive(world, root, pending_view(clean))
        assert refused.value.cause == "pending"

        # The same root, a clean chain: now the mismatch is what is left, and it
        # refuses before the transaction rather than being admitted and reported.
        with pytest.raises(SubjectMismatch):
            arrive(world, root, clean, observers=(corpus_anchor(clean, BETA),))
        assert registry_files(world) == {}

        # And a matching manifest over the same clean chain is admitted.
        parent = replica_root(tmp_path, ALPHA, name="parent-copy")
        parent_view = surfaced(parent, "corpus", science_root.GENESIS_PAYLOAD)
        record, _ = arrive(world, parent, parent_view, observers=(corpus_anchor(parent_view),))
        assert record.corpus_id == ALPHA

    def test_fresh_manifest_over_parent_chain_refuses_subject_mismatch(self, tmp_path):
        # L10u1. The arrival-identity arm: a copied root whose manifest was
        # re-minted to a new id still carries the **parent's** chain, and the
        # verdict on that chain is `validated`. §6.3 refuses it anyway — a
        # lifecycle-boundary refusal, on a validated report.
        root = replica_root(tmp_path, BETA)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        # The chain alone says nothing is wrong: judged against the parent it
        # validates, with the mismatch stated only as a finding.
        report = verify.evaluate_log(
            anchors.CorpusSubject(ALPHA),
            view,
            verify.ObserverSet((corpus_anchor(view),)),
            tuple((path, state(path)) for path in verify.registered_surface_paths(root, "corpus")),
            verify.PresentedManifest(BETA),
            ABSENT,
        )
        assert report.outcome == "validated"
        assert [finding.code for finding in report.findings] == ["subject-mismatch"]

        with pytest.raises(SubjectMismatch) as caught:
            arrive(world, root, view, observers=(corpus_anchor(view),))

        assert BETA in str(caught.value) and ALPHA in str(caught.value)
        assert registry_files(world) == {}
        assert _operation_lock_for(root)._holder is None

    def test_a_fork_manifest_refuses_provenance_through_the_public_arrival(self, tmp_path):
        # The core's own agreement check, reached end to end: the **public**
        # `admit_arrival` over the **production** seam, so the refusal is the one
        # a caller meets rather than one a private predicate can be shown.
        #
        # The manifest names the parent, so `SubjectMismatch` has nothing to say;
        # what disagrees is `forked_from`, which a replica never carries. The
        # chain is one genesis with the empty baseline §1.3 requires, and with no
        # observer supplied the report is `unresolvable` and admissible — so the
        # act reaches the transaction's own gate and refuses there.
        root = corpus_at(tmp_path / "forked", ALPHA)
        (root / "corpus.yaml").write_bytes(
            registry.manifest_bytes(
                registry.CorpusManifest(2, ALPHA, PINS, registry.ForkedFrom(BETA, "3" * 64))
            )
        )
        write_chain(root, [(None, GenesisEntry(payload=science_root.GENESIS_PAYLOAD, baseline=()))])
        world = make_world(tmp_path, root)
        assert type(science_root._log_seam().inspect_detached(root)) is logmodel.WellFormedView

        with pytest.raises(ProvenanceMismatch):
            science_root.admit_arrival(
                world, root, registry.ReplicaOf(ALPHA), verify.ObserverSet(()), actor="alice"
            )

        assert registry_files(world) == {}
        assert _operation_lock_for(root)._holder is None

    def test_the_mismatch_is_not_laundered_into_the_provenance_refusal(self, tmp_path):
        # `_validate_provenance` would also refuse this pair, one step later and
        # under a name that says "the caller composed the admission wrongly".
        # §6.3 rules it a lifecycle refusal, so it is decided first and said as
        # what it is.
        root = replica_root(tmp_path, BETA)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        with pytest.raises(SubjectMismatch):
            arrive(world, root, view, observers=(corpus_anchor(view),))
        with pytest.raises(ProvenanceMismatch):
            registry._validate_provenance(registry.load_manifest(root), registry.ReplicaOf(ALPHA))


# --- the hold, its order, and R12 -----------------------------------------------


class TestTheHold:
    def test_it_holds_both_locks_across_inspection_capture_and_the_transaction(self, tmp_path):
        root = replica_root(tmp_path)
        world_lock = registry._world_lock_for(tmp_path / "world")
        corpus_lock = _operation_lock_for(root)
        observed: list[tuple[str, bool, str | None]] = []

        def probe(label: str):
            def record(_root: Path) -> None:
                # A build's capture arriving to any holder refuses at once, so
                # the corpus hold is observed from outside rather than inferred.
                with pytest.raises(BuildContended), corpus_lock.capture():
                    pass
                observed.append((label, world_lock.acquire(blocking=False), corpus_lock._holder))

            return record

        class Watching:
            def __init__(self, target: Path) -> None:
                self.inner = DefaultExecutor(target)

            def execute(self, plan) -> None:
                probe("transaction")(Path())
                self.inner.execute(plan)

        world = registry.World(
            registry.WorldConfig(tmp_path / "world", WORLD_ID, (root,)),
            Watching,
            chain_head=ChainHeads(),
            corpus_executor_factory=DefaultExecutor,
        )
        inspections, captures = Inspections(), Captures()
        inspections.probe = probe("inspect")
        captures.probe = probe("capture")
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        arrive(world, root, view, inspections=inspections, captures=captures)

        assert observed == [
            ("inspect", False, "writer"),
            ("capture", False, "writer"),
            ("transaction", False, "writer"),
        ]
        assert corpus_lock._holder is None
        assert world_lock.acquire(blocking=False) is True
        world_lock.release()

    def test_the_in_hold_order_is_inspection_then_the_claim_then_the_capture(self, tmp_path, monkeypatch):
        # Task 8's pinned order, kept here for one reason: the manifest read and
        # the surface capture must stand on the same side of whatever the
        # inspection did to the root. Detached inspection runs no recovery, so
        # nothing here depends on it today — which is exactly why it is pinned
        # rather than rediscovered when the mode changes.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        events: list[str] = []
        real = registry.load_manifest

        def watched(target: Path) -> registry.CorpusManifest:
            events.append("manifest")
            return real(target)

        monkeypatch.setattr(registry, "load_manifest", watched)
        inspections, captures = Inspections(), Captures()
        inspections.probe = lambda _root: events.append("inspect")
        captures.probe = lambda _root: events.append("capture")

        arrive(
            world,
            root,
            surfaced(root, "corpus", science_root.GENESIS_PAYLOAD),
            inspections=inspections,
            captures=captures,
        )

        assert events == ["inspect", "manifest", "capture"]

    def test_the_manifest_is_never_supplied_and_the_subject_comes_from_the_provenance(self):
        parameters = inspect.signature(verify._admit_arrival).parameters
        assert list(parameters) == [
            "world",
            "corpus_root",
            "provenance",
            "observers",
            "actor",
            "history",
            "seam",
        ]
        assert "manifest" not in parameters
        assert "subject" not in parameters
        assert parameters["seam"].kind is inspect.Parameter.KEYWORD_ONLY

    def test_it_calls_no_world_method_under_the_world_lock(self, tmp_path):
        # R12: the seam's world lock is the very non-reentrant lock
        # `World.registry()` takes. An act that called one would not raise — it
        # would hang — so the arm is that the act *completes*, and that the same
        # world answers afterwards.
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        view = surfaced(root, "corpus", science_root.GENESIS_PAYLOAD)

        record, _ = arrive(world, root, view, observers=(corpus_anchor(view),))

        assert world.registry().admissions == (record,)
        source = inspect.getsource(verify._admit_arrival)
        assert "world.registry()" not in source and "world.status(" not in source

    def test_the_locks_are_released_when_the_act_refuses(self, tmp_path):
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)

        with pytest.raises(ArrivalRefused):
            arrive(world, root, logmodel.AbsentView())

        assert _operation_lock_for(root)._holder is None
        held = registry._world_lock_for(tmp_path / "world")
        assert held.acquire(blocking=False) is True
        held.release()

    def test_the_callers_own_inputs_refuse_before_the_root_is_touched(self, tmp_path):
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        inspections, captures = Inspections(), Captures()

        with pytest.raises(TypeError):
            verify._admit_arrival(
                world,
                root,
                registry.ReplicaOf(ALPHA),
                verify.ObserverSet(()),
                actor=object(),  # type: ignore[arg-type]
                seam=make_seam(inspections, captures),
            )
        with pytest.raises(TypeError):
            verify._admit_arrival(
                world,
                root,
                registry.Fresh(),  # type: ignore[arg-type]
                verify.ObserverSet(()),
                actor="alice",
                seam=make_seam(inspections, captures),
            )
        with pytest.raises(ValueError):
            verify._admit_arrival(
                world,
                root,
                registry.ReplicaOf(ALPHA),
                verify.ObserverSet(()),
                actor="alice",
                history={"sha256:nope": b"a record"},
                seam=make_seam(inspections, captures),
            )

        assert inspections.roots == [] and captures.calls == []
        assert _operation_lock_for(root)._holder is None


# --- the public wrapper ----------------------------------------------------------


class TestThePublicWrapper:
    def test_the_wrapper_hands_the_core_the_production_seam(self, tmp_path, monkeypatch):
        seen: list[tuple[object, ...]] = []
        monkeypatch.setattr(
            science_root,
            "_admit_arrival",
            lambda world, corpus_root, provenance, observers, *, actor, history, seam: seen.append(
                (world, corpus_root, provenance, observers, actor, history, seam)
            ),
        )
        root = replica_root(tmp_path)
        world = make_world(tmp_path, root)
        observers = verify.ObserverSet(())
        provenance = registry.ReplicaOf(ALPHA)

        science_root.admit_arrival(world, root, provenance, observers, actor="alice")

        assert seen == [(world, root, provenance, observers, "alice", None, science_root._log_seam())]

    def test_the_wrapper_signature_is_the_ruled_one(self):
        parameters = inspect.signature(science_root.admit_arrival).parameters
        assert list(parameters) == ["world", "corpus_root", "provenance", "observers", "actor", "history"]
        assert parameters["actor"].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters["history"].default is None
        assert "admit_arrival" in science_root.__all__


# --- §6.4's engine refusal, in the arrival's context ------------------------------


def test_an_unrepresentable_entry_at_a_modeled_path_refuses_with_no_report(tmp_path):
    """R11/§6.4's `PreconditionRefused` arm, reached through arrival.

    Not injected: a FIFO at `verification/v1.md` is a real entry outside the
    engine's closed path-state vocabulary, sitting at a path the corpus
    projection genuinely claims. The production seam is driven end to end, so
    what is armed is the whole path — the projection claiming it, capture
    refusing it, the adapter translating it — reaching the caller as a refusal
    to judge: **no report, no admission**, outside every precedence.
    """
    root = corpus_at(tmp_path / "arriving", ALPHA)
    (root / "verification").mkdir()
    os.mkfifo(root / "verification" / "v1.md")
    assert "verification/v1.md" in verify.registered_surface_paths(root, "corpus")
    world = make_world(tmp_path, root)

    with pytest.raises(LogEvidenceRefused) as caught:
        science_root.admit_arrival(
            world, root, registry.ReplicaOf(ALPHA), verify.ObserverSet(()), actor="alice"
        )

    assert (caught.value.phase, caught.value.engine_error) == ("capture", "PreconditionRefused")
    assert type(caught.value.__cause__) is PreconditionRefused
    assert not isinstance(caught.value, ArrivalRefused)
    assert registry_files(world) == {}
    assert _operation_lock_for(root)._holder is None


# --- §2.3's pending gate, as the executor reports it ------------------------------


def test_pending_root_refuses_further_mutation_via_the_gate(tmp_path, monkeypatch):
    """L2u5, **partial**. A root carrying an unsettled registration refuses
    further mutation through the engine's shared pending gate.

    The refusal is the **engine's** (§2.3), which is why arrival refuses
    `pending` from the report rather than adopting and then hoping: the
    registry's status vocabulary is monotone and holds nothing liftable, so the
    gate is the standing write-refusal authority. The engine's decision to raise
    is injected, on the same ground the audit's `ChainStateInvalid` arm is
    injected: whether that disk state produces `PendingUnresolved` is `atoms`'
    own certified contract. What is Science's to arm is the **mapping** — and
    that the gate runs before any mutation, so the seam reports `applied=0`
    rather than leaving restoration unproved.

    **Two of the three commands cut 8's L2 bullet enumerates are run here**, and
    they are the two Science maps: `run_transaction` through the durable
    executor, and `append_intent` through the operation port. `root.py`'s own
    comment beside the second says the two mappings "must not drift", so they
    are asserted **equal** rather than each asserted alone — a claim about one
    mapping would leave the drift the comment warns about unarmed.

    **Unrun, and named rather than argued around:** `register_root`'s
    existing-chain arm. Both initializers call `register_root` bare — there is
    no Science mapping there to arm, so the engine's refusal reaches the caller
    as it stands, and nothing on this side of the seam can be falsified. The
    unit is therefore partial: cut 8 §1's rule is that any unrun arm makes the
    claim partial, never full on an argument for why the arm should not count.
    """
    root = tmp_path / "corpus"
    root.mkdir()
    unresolved = PendingUnresolved("the chain carries unsettled registrations: tx-9 at 0f")

    def raising(*_args, **_kwargs):
        raise unresolved

    monkeypatch.setattr(science_root, "run_transaction", raising)
    monkeypatch.setattr(science_root, "append_intent", raising)
    executor = science_root._durable_executor(root)
    port = science_root.DurableOperationPort(
        root,
        backend=science_root._PRODUCTION_BACKEND,
        storage=science_root.PRODUCTION_STORAGE,
        metadata_root=science_root.metadata_root_for(root),
    )

    with pytest.raises(ExecutionError) as submitted:
        executor.execute([CreateOp("verification/v1.md", b"a record")])
    with pytest.raises(ExecutionError) as appended:
        port.append_intent(b"an intent this root may not append")

    for caught in (submitted, appended):
        assert caught.value.__cause__ is unresolved
        assert caught.value.applied == 0
    # The two mappings state one engine contract, so they are compared rather
    # than each read on its own: a drift between them is the defect the
    # production comment names, and one assertion per site could not see it.
    assert (submitted.value.applied, submitted.value.index) == (
        appended.value.applied,
        appended.value.index,
    )
    assert tree(root) == {}
    assert not science_root.metadata_root_for(root).exists()

    # The third command's arm, stated as unrun rather than implied: no Science
    # mapping stands between `register_root` and its caller.
    registrations = inspect.getsource(science_root.init_corpus_root) + inspect.getsource(
        science_root.init_world_root
    )
    assert "PendingUnresolved" not in registrations
