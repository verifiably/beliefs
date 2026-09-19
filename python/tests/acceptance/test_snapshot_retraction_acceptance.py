"""Cut 34: the snapshot target arm through the certified durable boundary.

One test per declaration unit (C8-a–d, C9-a–d, BI-1–9), each the slice's
unit test re-composed over the durable world: registered roots on the
certified volume, the composition root's executors, and a session-shaped
writer holding the world's retained epochs.
"""

from __future__ import annotations

import shutil
from collections import Counter
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, cast

import pytest
from authority import FULL
from domain_facet_fixtures import over_kwargs
from fixtures_cut4 import raw_write
from test_local_standing import retracts
from test_snapshot_retraction import S as UNRETAINED
from test_snapshot_retraction import broken_counter, snapshot_retraction
from test_world_import_epoch import epochs_of, exported
from test_world_receipts import hold_shipped, publish
from test_world_view_acceptance import durable_world as durable_world  # noqa: PLC0414 - register the shared fixture
from test_world_view_acceptance import evaluation_world, world_kwargs

from beliefs.audit import NO_EVIDENCE, audit_world
from beliefs.belief import Belief
from beliefs.corpus import CorpusWriter, ReadView, corpus_check
from beliefs.errors import (
    EpochImportRefused,
    ProducerSnapshotMismatch,
    ProducerSnapshotRetracted,
    RetractionTargetUnresolvable,
    RetractionUnreadable,
)
from beliefs.evaluation import evaluate_over, gather
from beliefs.root import (
    durable_executor_factory,
    durable_operation_port,
    init_world_root,
    metadata_root_for,
    open_world,
)
from beliefs.world import Fresh, WorldConfig, read, registry
from beliefs.world.audit import audit_epochs, snapshot_state
from beliefs.world.epoch import RetainedSnapshots
from beliefs.world.importing import import_epoch
from beliefs.world.view import open_world_view

PRODUCER = "producer-receipt.yaml"


@pytest.fixture()
def replica(work_directory):
    """A second world of the same id over the same durable corpora, holding
    the shipped rules and publishing nothing: the import target."""
    made: list[Path] = []

    def make(world, roots):
        path = Path(mkdtemp(prefix="cut34-replica-", dir=work_directory))
        made.append(path)
        config = WorldConfig(path, world.config.world_id, tuple(roots.values()))
        init_world_root(config, authority=FULL)
        other = open_world(config, authority=FULL)
        for root in roots.values():
            other.admit(root, provenance=Fresh())
        hold_shipped(other)
        return other

    try:
        yield make
    finally:
        for path in made:
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)


def _world(durable_world):
    """BETA holds none of the lineage walk's own refs, so an epoch covering
    ALPHA alone still resolves `world_kwargs` — the narrowing route needs it."""
    return evaluation_world(durable_world, beta_refs=())


def _identity(epoch) -> str:
    identity = epoch.receipts[PRODUCER].subject_identity
    assert identity is not None
    return identity


def _writer(root: Path, profile, world) -> CorpusWriter:
    """A session's writer over one durable root, as `open_attended_session`'s
    factory constructs it, holding the world's retained epochs."""
    root = Path(root).resolve()
    return CorpusWriter(
        root,
        durable_executor_factory(),
        authority=FULL,
        profile=profile,
        operation_port=durable_operation_port(root, FULL, profile=profile),
        snapshot_resolver=RetainedSnapshots(world),
    )


def _read(world, epoch, profile, a, b, *, identity: str | None = None):
    """`gather` bound to `epoch`, with the identity the caller supplies (the
    view's own unless overridden) — no test-side selection of the epoch."""
    view = open_world_view(world, epoch)
    kwargs = world_kwargs(view, profile, a, b)
    if identity is not None:
        kwargs["context"] = replace(kwargs["context"], producer_snapshot_identity=identity)
    inputs = gather(view, "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})
    return view, inputs


def _answer(world, epoch, profile, a, b) -> Belief:
    view = open_world_view(world, epoch)
    answer = evaluate_over(view, "proposition:p", **over_kwargs(world_kwargs(view, profile, a, b)))
    assert isinstance(answer, Belief), answer
    return answer


def _inventory(root: Path) -> dict[str, bytes]:
    root = Path(root)
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def _members_and_receipts(world, epoch):
    reopened = read.open_epoch(world, epoch.packaging_identity)
    return dict(reopened.members), {member: carrier.document for member, carrier in reopened.receipts.items()}


def _findings(report) -> list[tuple[str, str, str, str, str]]:
    rows = [("world", f.severity, f.code, f.ref, f.message) for f in report.world]
    for corpus_id, findings in report.corpora.items():
        rows.extend((corpus_id, f.severity, f.code, f.ref, f.message) for f in findings)
    return sorted(rows)


# --- C8: a retracted snapshot is refused where recomputation already happens -----


def test_c8a_import_of_a_retracted_producer_subject_refuses_before_any_write(durable_world, replica, tmp_path):
    world, roots, old, a, _b, profile = _world(durable_world)
    other = replica(world, roots)
    _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(old)))
    before = _inventory(other.config.world_root)
    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(other, exported(old, tmp_path / "export"))
    assert refused.value.reason == "retracted-snapshot"
    assert [(o.kind, o.outcome) for o in refused.value.outcomes] == [("producer", "retracted")]
    assert epochs_of(other) == set()
    assert _inventory(other.config.world_root) == before


def test_c8b_the_audit_reports_retracted_without_a_finding(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    identity = _identity(old)
    _writer(roots[a], profile, world).retract(snapshot_retraction(identity))
    audit = audit_epochs(world)
    assert (old.packaging_identity, "producer", "retracted") in [(n, k, o.outcome) for n, k, o in audit.receipts]
    verdict = next(v for v in audit.snapshots if v.kind == "producer" and v.subject_identity == identity)
    assert verdict.state == "retracted"
    assert [f for f in audit.findings if f.ref == identity or "retract" in f.code] == []


def test_c8c_the_query_reports_retracted_and_the_successor_unchecked(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    new = publish(world, (a,), hold_shipped(world))
    old_identity, new_identity = _identity(old), _identity(new)
    assert old_identity != new_identity
    # §9 step 1: the only moment the successor is `checked` — before the retraction moves a corpus both cover.
    assert snapshot_state(world, "producer", new_identity).state == "checked"
    _writer(roots[a], profile, world).retract(snapshot_retraction(old_identity, successor=new_identity))
    retracted = snapshot_state(world, "producer", old_identity)
    assert retracted.state == "retracted"
    assert [(name, o.outcome) for name, o in retracted.receipts] == [(old.packaging_identity, "retracted")]
    successor = snapshot_state(world, "producer", new_identity)
    assert successor.state == "unchecked"
    assert [(name, o.outcome) for name, o in successor.receipts] == [(new.packaging_identity, "unresolvable")]
    assert "no longer stands at the state" in successor.receipts[0][1].detail


def test_c8d_mounting_writes_nothing_and_validates_nothing(durable_world, monkeypatch):
    world, roots, old, a, _b, profile = _world(durable_world)
    identity = _identity(old)
    _writer(roots[a], profile, world).retract(snapshot_retraction(identity))
    fresh_id, fresh, _writer_over_fresh = durable_world.corpus(profile)
    raw_write(fresh, snapshot_retraction(identity, token="unmounted"))  # unmounted: no writer resolves it
    calls: list[tuple[object, ...]] = []

    def counting(*args, **kwargs):
        calls.append(args)  # counted, never answered: admission has no receipt to validate

    monkeypatch.setattr(read, "validate_receipt", counting)
    epochs = world.config.world_root / "epochs"
    before_epochs, before_root = _inventory(epochs), _inventory(world.config.world_root)
    admitted = world.admit(fresh, provenance=Fresh())  # a root holding a snapshot-arm retraction
    world.admit(roots[a], provenance=Fresh())  # a root a retracted snapshot covers
    assert admitted.corpus_id == fresh_id
    assert _inventory(epochs) == before_epochs
    added = [path for path in _inventory(world.config.world_root) if path not in before_root]
    # The admission record is the only write; the engine's own transaction chain records it.
    assert [path.partition("/")[0] for path in added if not path.startswith(".#~")] == ["registry"]
    assert calls == []


# --- C9: narrowing is snapshot succession plus retraction --------------------------


def _narrowed(durable_world):
    """The route of §9: `new` under (ALPHA,), then `old` retracted naming it."""
    world, roots, old, a, b, profile = _world(durable_world)
    new = publish(world, (a,), hold_shipped(world))
    old_identity, new_identity = _identity(old), _identity(new)
    _view, before = _read(world, old, profile, a, b)
    answer_before = _answer(world, old, profile, a, b)
    retraction = _writer(roots[a], profile, world).retract(snapshot_retraction(old_identity, successor=new_identity))
    return world, roots, old, new, a, b, profile, before, answer_before, retraction


def test_c9a_a_computation_bound_to_the_old_snapshot_refuses(durable_world):
    world, _roots, old, _new, a, b, profile, _before, _answer_before, _r = _narrowed(durable_world)
    with pytest.raises(ProducerSnapshotRetracted) as refused:
        _read(world, old, profile, a, b)
    assert refused.value.identity == _identity(old)


def test_c9b_bound_to_the_new_snapshot_proceeds_and_the_digest_moves(durable_world):
    world, _roots, old, new, a, b, profile, before, answer_before, _r = _narrowed(durable_world)
    _view, inputs = _read(world, new, profile, a, b)
    assert inputs.producer_snapshot_identity == _identity(new)
    assert cast(dict[str, Any], inputs.closure().projection)["producer_snapshot"] == _identity(new)
    assert before.closure().projection["producer_snapshot"] == _identity(old)
    answer = _answer(world, new, profile, a, b)
    assert answer.belief_input_digest == inputs.closure().digest()
    assert answer.belief_input_digest != answer_before.belief_input_digest


def test_c9c_the_old_epoch_is_byte_unchanged(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    new = publish(world, (a,), hold_shipped(world))
    members, receipts = _members_and_receipts(world, old)
    carrier = world.config.world_root / "epochs" / old.packaging_identity
    inventory = _inventory(carrier)
    assert members == dict(old.members)
    _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(old), successor=_identity(new)))
    after_members, after_receipts = _members_and_receipts(world, old)
    assert after_members == members == dict(old.members)
    assert after_receipts == receipts
    assert _inventory(carrier) == inventory


def test_c9d_nothing_resolves_through_the_retraction_to_its_successor(durable_world):
    world, _roots, old, new, a, b, profile, _before, _answer_before, _r = _narrowed(durable_world)
    with pytest.raises(ProducerSnapshotMismatch) as refused:
        _read(world, new, profile, a, b, identity=_identity(old))
    assert (refused.value.supplied, refused.value.bound) == (_identity(old), _identity(new))
    with pytest.raises(ProducerSnapshotMismatch) as refused:
        _read(world, old, profile, a, b, identity=_identity(new))
    assert (refused.value.supplied, refused.value.bound) == (_identity(new), _identity(old))


# --- boundary invariants ----------------------------------------------------------


def test_bi1_a_snapshot_retraction_outside_the_targets_coverage_is_refused_at_authoring(durable_world):
    world, roots, _old, a, b, profile = _world(durable_world)
    new = publish(world, (a,), hold_shipped(world))
    with pytest.raises(RetractionTargetUnresolvable, match=f"corpus {b} is outside the coverage"):
        _writer(roots[b], profile, world).retract(snapshot_retraction(_identity(new)))
    assert not any(n.kind == "retraction" for n in ReadView.opened_at(roots[b]).iter_stored())
    admitted = _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(new)))
    assert admitted.kind == "retraction"
    assert ReadView.opened_at(roots[a]).get(admitted.id).id == admitted.id


def test_bi2_a_writer_without_the_port_refuses_the_arm(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    root = Path(roots[a]).resolve()
    without = CorpusWriter(
        root,
        durable_executor_factory(),
        authority=FULL,
        profile=profile,
        operation_port=durable_operation_port(root, FULL, profile=profile),
    )
    count = len(tuple(without.read_view.iter_stored()))
    with pytest.raises(RetractionTargetUnresolvable, match="reaches none"):
        without.retract(snapshot_retraction(_identity(old)))
    assert len(tuple(ReadView.opened_at(roots[a]).iter_stored())) == count
    assert _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(old))).kind == "retraction"


def test_bi3_retracted_precedes_availability(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    assert registry.corpus_state_identity(roots[a]) == dict(old.coverage)[a]
    _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(old)))
    assert registry.corpus_state_identity(roots[a]) != dict(old.coverage)[a]  # the write moved the covered corpus
    assert read.validate_receipt(world, old, "retraction-enumeration").outcome == "unresolvable"
    assert read.validate_receipt(world, old, "producer").outcome == "retracted"  # decided before availability
    assert next(v for v in audit_epochs(world).snapshots if v.subject_identity == _identity(old)).state == "retracted"


def test_bi4_a_counter_retraction_restores_the_snapshot(durable_world):
    world, roots, old, a, b, profile = _world(durable_world)
    identity = _identity(old)
    members, receipts = _members_and_receipts(world, old)
    writer = _writer(roots[a], profile, world)
    retraction = writer.retract(snapshot_retraction(identity))
    with pytest.raises(ProducerSnapshotRetracted):
        _read(world, old, profile, a, b)
    writer.retract(retracts(retraction, "counter"))
    verdict = snapshot_state(world, "producer", identity)
    assert verdict.state != "retracted" and verdict.state == "unchecked"
    assert all(o.outcome == "unresolvable" for _n, o in verdict.receipts)
    _view, inputs = _read(world, old, profile, a, b)
    assert inputs.producer_snapshot_identity == identity
    assert _members_and_receipts(world, old) == (members, receipts)


def test_bi5_an_older_snapshots_retraction_is_out_of_the_closure(durable_world):
    world, roots, old, a, b, profile = _world(durable_world)
    _view, baseline = _read(world, old, profile, a, b)
    narrow = publish(world, (a,), hold_shipped(world))  # a different identity
    assert _identity(narrow) != _identity(old)
    retraction = _writer(roots[a], profile, world).retract(snapshot_retraction(_identity(narrow)))
    later = publish(world, (a, b), hold_shipped(world))  # captures that retraction
    view, inputs = _read(world, later, profile, a, b)
    assert retraction.id in dict(view.retraction_enumeration().found)
    assert inputs.retractions.found == baseline.retractions.found == ()
    assert inputs.closure().digest() == baseline.closure().digest()


def test_bi6_a_raw_written_snapshot_retraction_is_reported_by_audit_world_from_captured_records(durable_world):
    world, roots, old, a, _b, profile = _world(durable_world)
    node = snapshot_retraction(UNRETAINED)  # retained nowhere; the epoch predates the write
    raw_write(roots[a], node)
    report = audit_world(world, old, evidence=NO_EVIDENCE, profile=profile)
    assert [(f.code, f.ref) for f in report.world if f.ref == node.id] == [("retraction-target-invalid", node.id)]
    assert [f for f in corpus_check(ReadView.opened_at(roots[a]), profile) if f.ref == node.id] == []


def test_bi7_history_is_in_the_digest(durable_world):
    world, roots, old, a, b, profile = _world(durable_world)
    _view, never = _read(world, old, profile, a, b)
    writer = _writer(roots[a], profile, world)
    r = writer.retract(snapshot_retraction(_identity(old)))
    c = writer.retract(retracts(r, "counter"))
    _view, inputs = _read(world, old, profile, a, b)
    assert set(inputs.retractions.found) == {(r.id, "overturned"), (c.id, "upheld")}
    assert ("retraction", r.id) in inputs.read_trace and ("retraction", c.id) in inputs.read_trace
    assert inputs.closure().digest() != never.closure().digest()
    assert _answer(world, old, profile, a, b).belief_input_digest == inputs.closure().digest()


def test_bi8_an_unreadable_counter_retraction_refuses_rather_than_restores(durable_world, replica, tmp_path):
    world, roots, old, a, b, profile = _world(durable_world)
    identity = _identity(old)
    r = _writer(roots[a], profile, world).retract(snapshot_retraction(identity))
    readable = _findings(audit_world(world, old, evidence=NO_EVIDENCE, profile=profile))
    broken = broken_counter(r)
    raw_write(roots[a], broken)
    with pytest.raises(RetractionUnreadable) as refused:
        _read(world, old, profile, a, b)
    assert refused.value.ref == broken.id
    other = replica(world, roots)
    with pytest.raises(EpochImportRefused) as import_refused:
        import_epoch(other, exported(old, tmp_path / "export"))
    assert import_refused.value.reason == "unreadable-standing" and epochs_of(other) == set()
    verdict = snapshot_state(world, "producer", identity)
    assert verdict.state == "unchecked"
    assert [o.outcome for _n, o in verdict.receipts] == ["unresolvable"]
    assert "cannot be decided" in verdict.receipts[0][1].detail
    epochs = audit_epochs(world)
    assert [f.code for f in epochs.findings if f.ref == broken.id] == ["retraction-unreadable"]
    report = _findings(audit_world(world, old, evidence=NO_EVIDENCE, profile=profile))
    # The same record, two diagnostics: the chain it breaks and the record itself — and the
    # producer receipt it leaves undecidable, reported with the cause (the verdict above).
    assert sorted(row[2] for row in report if row[3] == broken.id) == [
        "retraction-target-invalid",
        "retraction-unreadable",
    ]
    about = [row for row in report if row[3] == broken.id or broken.id in row[4]]
    assert sorted(row[2] for row in about) == [
        "receipt-unresolvable",
        "retraction-target-invalid",
        "retraction-unreadable",
    ]
    assert next(row for row in about if row[2] == "receipt-unresolvable")[3] == old.packaging_identity
    assert "the producer receipt" in next(row for row in about if row[2] == "receipt-unresolvable")[4]
    # Every other finding equals the readable-chain run's. The raw write is itself drift in
    # ALPHA — one more unmapped-uid warning, and the state the carrier stands at moved — and
    # that is the whole of what the corpus-level drift rows may differ by.
    rest = [row for row in report if row not in about]
    assert [row for row in rest if row[2] != "drift"] == [row for row in readable if row[2] != "drift"]
    assert Counter(row[:4] for row in rest) - Counter(row[:4] for row in readable) == Counter(
        {(a, "warning", "drift", a): 1}
    )
    assert Counter(row[:4] for row in readable) - Counter(row[:4] for row in rest) == Counter()
    assert sum("never mapped" in row[4] for row in rest) == sum("never mapped" in row[4] for row in readable) + 1


def test_bi9_a_rebuild_restores_nothing_and_duplicates_nothing(durable_world):
    world, roots, old, a, b, profile = _world(durable_world)
    identity = _identity(old)
    writer = _writer(roots[a], profile, world)
    r = writer.retract(snapshot_retraction(identity))
    rebuilt = publish(world, (a, b), hold_shipped(world))
    assert _identity(rebuilt) == identity and rebuilt.packaging_identity != old.packaging_identity
    with pytest.raises(ProducerSnapshotRetracted):
        _read(world, rebuilt, profile, a, b)
    assert read.validate_receipt(world, rebuilt, "producer").outcome == "retracted"
    c = writer.retract(retracts(r, "counter"))
    rebuilt_again = publish(world, (a, b), hold_shipped(world))
    assert _identity(rebuilt_again) == identity
    _view, over_rebuilt = _read(world, rebuilt_again, profile, a, b)
    _view, over_old = _read(world, old, profile, a, b)
    assert over_rebuilt.retractions.found == over_old.retractions.found
    assert sorted(over_rebuilt.retractions.found) == sorted([(r.id, "overturned"), (c.id, "upheld")])
    assert len(over_rebuilt.retractions.found) == 2
