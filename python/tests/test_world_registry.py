from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from authority import ACTOR, FULL, narrowed
from fixtures_cut6 import PINS
from nodes.core.write_plan import CreateOp, DefaultExecutor

import beliefs.world.registry as world_module
from beliefs.errors import (
    CorpusIdKnown,
    ForkParentUnknown,
    ManifestMalformed,
    PermitExceeded,
    PermitFact,
    ProvenanceMismatch,
    RegistryMalformed,
    ReplicaAdmissionRequiresVerification,
    StatusTargetUnknown,
    StatusTerminal,
)
from beliefs.identity import v1


def write_manifest(root: Path, corpus_id: str, forked_from: tuple[str, str] | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    manifest = world_module.CorpusManifest(
        2,
        corpus_id,
        PINS,
        None if forked_from is None else world_module.ForkedFrom(*forked_from),
    )
    (root / "corpus.yaml").write_bytes(world_module.manifest_bytes(manifest))


def unread_chain(root: Path) -> tuple[str, str]:
    """The chain reader a world that never builds an epoch is handed.

    A `World` takes the reader explicitly, so these arms have to say something
    about it; saying "nothing here reads a chain" out loud is stronger than a
    stub that quietly answers, because a chain read creeping into one of these
    acts would then be a failure rather than a pair of invented digests.
    """
    raise AssertionError(f"{root}: this arm builds no epoch and reads no chain")


def make_world(tmp_path: Path, *corpus_roots: Path, authority=FULL) -> world_module.World:
    return world_module.World(
        world_module.WorldConfig(tmp_path / "world", "f" * 32, corpus_roots),
        DefaultExecutor,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
        authority=authority,
    )


def _registry_files(world_root):
    directory = world_root / "registry"
    return sorted(path.name for path in directory.glob("*.yaml")) if directory.exists() else []


def test_e1_admit_under_a_permit_lacking_registry_refuses_and_writes_nothing(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    world = world_module.World(
        world_module.WorldConfig(tmp_path / "world", "f" * 32, (corpus,)),
        DefaultExecutor,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
        authority=narrowed(families=("epoch",)),
    )
    with pytest.raises(PermitExceeded) as caught:
        world.admit(corpus, provenance=world_module.Fresh())
    assert caught.value.requirement == PermitFact("family", "registry")
    assert _registry_files(tmp_path / "world") == []


def test_e3_an_admission_carries_the_bound_actor_and_takes_none(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    world = make_world(tmp_path, corpus)
    record = world.admit(corpus, provenance=world_module.Fresh())
    assert record.actor == ACTOR
    with pytest.raises(TypeError):
        world.retire(record.corpus_id, actor="alice")  # type: ignore[call-arg]
    assert world.retire(record.corpus_id).actor == ACTOR


def test_e2_open_world_and_world_require_an_authority(tmp_path):
    with pytest.raises(TypeError):
        world_module.World(
            world_module.WorldConfig(tmp_path / "world", "f" * 32, ()),
            DefaultExecutor,
            chain_head=unread_chain,
            corpus_executor_factory=DefaultExecutor,
        )  # type: ignore[call-arg]


def registry_paths(instance: world_module.World) -> tuple[Path, ...]:
    registry = instance.config.world_root / "registry"
    return tuple(registry.iterdir()) if registry.exists() else ()


def write_raw_admission(
    root: Path,
    corpus_id: str = "1" * 32,
    *,
    actor: str = "alice",
) -> world_module.AdmissionRecord:
    manifest = world_module.CorpusManifest(2, corpus_id, PINS)
    record = world_module.AdmissionRecord(manifest, world_module.Fresh(), actor)
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / f"{world_module.admission_digest(record)}.yaml").write_text(
        yaml.safe_dump(world_module.admission_projection(record), sort_keys=True),
        encoding="utf-8",
    )
    return record


def test_registry_record_projections_and_content_names_are_exact():
    manifest = world_module.CorpusManifest(2, "1" * 32, PINS)
    admission = world_module.AdmissionRecord(manifest, world_module.Fresh(), "alice")
    status = world_module.StatusRecord(manifest.corpus_id, "retired", "alice")

    admission_projection = {
        "record_kind": "admission",
        "corpus_id": manifest.corpus_id,
        "manifest": world_module.manifest_projection(manifest),
        "provenance": {"kind": "fresh"},
        "actor": "alice",
    }
    status_projection = {
        "record_kind": "status",
        "corpus_id": manifest.corpus_id,
        "status": "retired",
        "actor": "alice",
    }
    assert world_module.admission_projection(admission) == admission_projection
    assert world_module.admission_digest(admission) == v1.digest("science.world-admission.v1", admission_projection)
    assert world_module.status_projection(status) == status_projection
    assert world_module.status_digest(status) == v1.digest("science.world-status.v1", status_projection)


def test_all_provenance_projections_are_exact():
    assert world_module.provenance_projection(world_module.Fresh()) == {"kind": "fresh"}
    assert world_module.provenance_projection(world_module.ReplicaOf("1" * 32)) == {
        "kind": "replica-of",
        "parent_corpus_id": "1" * 32,
    }
    assert world_module.provenance_projection(world_module.ForkOf("2" * 32, "3" * 64)) == {
        "kind": "fork-of",
        "parent_corpus_id": "2" * 32,
        "parent_corpus_state": "3" * 64,
    }


@pytest.mark.parametrize(
    "construct",
    (
        lambda: world_module.ReplicaOf("x"),
        lambda: world_module.ForkOf("1" * 32, "x"),
        lambda: world_module.AdmissionRecord(world_module.CorpusManifest(2, "x", PINS), world_module.Fresh(), "alice"),
        lambda: world_module.StatusRecord("x", "retired", "alice"),
        lambda: world_module.StatusRecord("1" * 32, cast(Any, "other"), "alice"),
        lambda: world_module.StatusRecord("1" * 32, "retired", cast(Any, True)),
        lambda: world_module.StatusRecord("1" * 32, "retired", "\ud800"),
    ),
)
def test_record_values_refuse_malformed_ids_statuses_and_actors(construct):
    with pytest.raises((TypeError, ValueError)):
        construct()


def test_registry_accepts_projection_equivalent_yaml(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    record = instance.admit(corpus, provenance=world_module.Fresh())
    path = registry_paths(instance)[0]
    path.write_text(
        yaml.safe_dump(world_module.admission_projection(record), default_flow_style=True, sort_keys=False),
        encoding="utf-8",
    )

    assert instance.registry() == world_module.RegistryView((record,), ())


def test_exact_admission_retry_is_success_without_second_file(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)

    first = instance.admit(corpus, provenance=world_module.Fresh())
    second = instance.admit(corpus, provenance=world_module.Fresh())

    assert second == first
    assert len(registry_paths(instance)) == 1


def test_known_id_refuses_fresh_and_replica_provenance(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())
    other_actor = make_world(tmp_path, corpus, authority=narrowed(families=("registry",), actor="bob"))

    with pytest.raises(CorpusIdKnown):
        other_actor.admit(corpus, provenance=world_module.Fresh())
    # A replica refuses too, and now it refuses *sooner*: the log-verification
    # design (§6.2) moved the replica route to `admit_arrival`, so a bare admit
    # never reaches the known-id check for one. The known-id refusal itself
    # still stands on that route, over the same shared core — armed in
    # `test_world_arrival.py::test_an_id_already_admitted_under_another_provenance_still_refuses`.
    with pytest.raises(ReplicaAdmissionRequiresVerification):
        instance.admit(corpus, provenance=world_module.ReplicaOf("1" * 32))

    assert len(registry_paths(instance)) == 1


def test_replica_parent_is_the_retained_manifest_id(tmp_path):
    # The predicate is unchanged; only its reachable caller moved. A bare admit
    # refuses a replica before it (§6.2), so the rule is armed where it now
    # runs — the shared core's own validation, reached through `admit_arrival`.
    corpus = tmp_path / "replica"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    manifest = world_module.load_manifest(corpus)

    with pytest.raises(ReplicaAdmissionRequiresVerification):
        instance.admit(corpus, provenance=world_module.ReplicaOf("1" * 32))

    with pytest.raises(ProvenanceMismatch):
        world_module._validate_provenance(manifest, world_module.ReplicaOf("2" * 32))
    assert world_module._validate_provenance(manifest, world_module.ReplicaOf("1" * 32)) is None


def test_non_fork_provenance_refuses_a_fork_manifest(tmp_path):
    corpus = tmp_path / "fork"
    write_manifest(corpus, "1" * 32, ("2" * 32, "3" * 64))
    instance = make_world(tmp_path, corpus)

    with pytest.raises(ProvenanceMismatch):
        instance.admit(corpus, provenance=world_module.Fresh())
    # The replica arm of the same rule: a bare admit refuses a replica first
    # (§6.2), so the fork-manifest refusal is armed over the predicate the
    # shared core applies on either route.
    with pytest.raises(ProvenanceMismatch):
        world_module._validate_provenance(
            world_module.load_manifest(corpus), world_module.ReplicaOf("1" * 32)
        )

    assert registry_paths(instance) == ()


@pytest.mark.parametrize(
    "provenance",
    (
        world_module.ForkOf("4" * 32, "3" * 64),
        world_module.ForkOf("2" * 32, "5" * 64),
    ),
)
def test_fork_provenance_must_match_both_manifest_parent_facts(tmp_path, provenance):
    corpus = tmp_path / "fork"
    write_manifest(corpus, "1" * 32, ("2" * 32, "3" * 64))
    instance = make_world(tmp_path, corpus)

    with pytest.raises(ProvenanceMismatch):
        instance.admit(corpus, provenance=provenance)

    assert registry_paths(instance) == ()


def test_fork_provenance_requires_a_known_parent(tmp_path):
    parent = tmp_path / "parent"
    fork = tmp_path / "fork"
    write_manifest(parent, "2" * 32)
    write_manifest(fork, "1" * 32, ("2" * 32, "3" * 64))
    instance = make_world(tmp_path, parent, fork)
    provenance = world_module.ForkOf("2" * 32, "3" * 64)

    with pytest.raises(ForkParentUnknown):
        instance.admit(fork, provenance=provenance)
    assert registry_paths(instance) == ()

    instance.admit(parent, provenance=world_module.Fresh())
    assert instance.admit(fork, provenance=provenance).corpus_id == "1" * 32


def test_malformed_manifest_wins_before_exact_admission_retry(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())
    (corpus / "corpus.yaml").write_text("manifest_version: broken\n", encoding="utf-8")

    with pytest.raises(ManifestMalformed):
        instance.admit(corpus, provenance=world_module.Fresh())

    assert len(registry_paths(instance)) == 1


def test_registry_scan_wins_before_manifest_loading(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    write_raw_admission(instance.config.world_root)
    (instance.config.world_root / "registry" / "foreign.txt").write_text("x", encoding="utf-8")
    (corpus / "corpus.yaml").write_text("manifest_version: broken\n", encoding="utf-8")

    with pytest.raises(RegistryMalformed):
        instance.admit(corpus, provenance=world_module.Fresh())


def test_provenance_mismatch_wins_before_known_id_refusal(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())
    write_manifest(corpus, "1" * 32, ("2" * 32, "3" * 64))

    with pytest.raises(ProvenanceMismatch):
        instance.admit(corpus, provenance=world_module.Fresh())

    assert len(registry_paths(instance)) == 1


def test_admission_uses_one_create_only_plan_through_the_supplied_executor(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    plans = []

    class Recorder:
        def __init__(self, root: Path) -> None:
            self.inner = DefaultExecutor(root)

        def execute(self, plan) -> None:
            plans.append(tuple(plan))
            self.inner.execute(plan)

    instance = world_module.World(
        world_module.WorldConfig(tmp_path / "world", "f" * 32, (corpus,)),
        Recorder,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
        authority=FULL,
    )
    record = instance.admit(corpus, provenance=world_module.Fresh())

    assert plans == [
        (
            CreateOp(
                f"registry/{world_module.admission_digest(record)}.yaml",
                yaml.safe_dump(world_module.admission_projection(record), sort_keys=True, allow_unicode=True).encode(
                    "utf-8"
                ),
            ),
        )
    ]


def test_terminal_target_must_be_known_and_refusal_writes_nothing(tmp_path):
    instance = make_world(tmp_path)

    with pytest.raises(StatusTargetUnknown):
        instance.retire("1" * 32)

    assert registry_paths(instance) == ()


def test_status_retry_is_idempotent_and_a_differing_terminal_act_refuses(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())

    first = instance.retire("1" * 32)
    assert instance.retire("1" * 32) == first
    with pytest.raises(StatusTerminal):
        instance.depart("1" * 32)

    assert len(registry_paths(instance)) == 2


def test_retired_corpus_has_no_return_to_live_act(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())
    instance.retire("1" * 32)
    other_actor = make_world(tmp_path, corpus, authority=narrowed(families=("registry",), actor="bob"))

    with pytest.raises(CorpusIdKnown):
        other_actor.admit(corpus, provenance=world_module.Fresh())
    assert not hasattr(instance, "unretire")


def test_depart_appends_the_other_terminal_status(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())

    assert instance.depart("1" * 32).status == "departed"
    assert instance.status("1" * 32).live is False


@pytest.mark.parametrize(
    ("admitted", "terminal", "configured", "expected"),
    (
        (False, False, False, (False, False, False)),
        (False, False, True, (False, False, True)),
        (True, False, True, (True, True, True)),
        (True, False, False, (True, True, False)),
        (True, True, False, (True, False, False)),
        (True, True, True, (True, False, True)),
    ),
)
def test_computed_status_facts_are_independent(tmp_path, admitted, terminal, configured, expected):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, *(corpus,) if configured else ())
    if admitted:
        instance.admit(corpus, provenance=world_module.Fresh())
    if terminal:
        instance.retire("1" * 32)

    status = instance.status("1" * 32)

    assert (status.known, status.live, status.present) == expected
    assert status.findings == ()


def test_missing_configured_manifest_is_a_non_carrier(tmp_path):
    instance = make_world(tmp_path, tmp_path / "missing")

    assert instance.status("1" * 32).present is False


def test_malformed_configured_manifest_propagates(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "corpus.yaml").write_text("manifest_version: broken\n", encoding="utf-8")
    instance = make_world(tmp_path, corpus)

    with pytest.raises(ManifestMalformed):
        instance.status("1" * 32)


def test_resolved_duplicate_configured_roots_count_once(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus, corpus / ".")

    assert instance.status("1" * 32).present is True


def test_duplicate_carriers_are_a_distinct_finding(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    write_manifest(first, "1" * 32)
    write_manifest(second, "1" * 32)
    instance = make_world(tmp_path, first, second)

    status = instance.status("1" * 32)

    assert status.present is False
    assert [(finding.severity, finding.code, finding.ref) for finding in status.findings] == [
        ("error", "duplicate-carrier", "1" * 32)
    ]
    assert status.findings[0].detail == "carriers=" + ",".join(sorted((str(first.resolve()), str(second.resolve()))))


def test_reads_rescan_for_raw_registry_arrival(tmp_path):
    instance = make_world(tmp_path)
    assert instance.registry() == world_module.RegistryView()
    record = write_raw_admission(instance.config.world_root)

    assert instance.registry() == world_module.RegistryView((record,), ())
    assert instance.status(record.corpus_id).known is True


def test_status_reduction_is_record_order_invariant(tmp_path):
    manifest = world_module.CorpusManifest(2, "1" * 32, PINS)
    admissions = (
        world_module.AdmissionRecord(manifest, world_module.Fresh(), "alice"),
        world_module.AdmissionRecord(manifest, world_module.ReplicaOf("1" * 32), "bob"),
    )
    statuses = (
        world_module.StatusRecord("1" * 32, "retired", "alice"),
        world_module.StatusRecord("2" * 32, "departed", "bob"),
    )
    config = world_module.WorldConfig(tmp_path / "world", "f" * 32, ())

    forward = world_module._reduce_status(config, world_module.RegistryView(admissions, statuses), "1" * 32)
    reverse = world_module._reduce_status(
        config,
        world_module.RegistryView(tuple(reversed(admissions)), tuple(reversed(statuses))),
        "1" * 32,
    )

    assert forward == reverse == world_module.CorpusStatus(True, False, False, ())


def test_replica_restoration_recomputes_presence_without_admission(tmp_path):
    original = tmp_path / "original"
    restoration = tmp_path / "restoration"
    write_manifest(original, "1" * 32)
    config = world_module.WorldConfig(tmp_path / "world", "f" * 32, (restoration,))
    instance = world_module.World(
        config,
        DefaultExecutor,
        chain_head=unread_chain,
        corpus_executor_factory=DefaultExecutor,
        authority=FULL,
    )
    instance.admit(original, provenance=world_module.Fresh())
    before = instance.registry()

    assert instance.status("1" * 32).present is False
    shutil.copytree(original, restoration)
    assert instance.status("1" * 32).present is True
    assert instance.registry() == before


def test_raw_admission_deletion_is_undetected(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    instance = make_world(tmp_path, corpus)
    instance.admit(corpus, provenance=world_module.Fresh())
    registry_paths(instance)[0].unlink()

    status = instance.status("1" * 32)

    assert (status.known, status.live, status.present) == (False, False, True)
    assert status.findings == ()


@pytest.mark.parametrize(
    "damage",
    (
        "foreign-file",
        "directory",
        "duplicate-key",
        "unknown-field",
        "wrong-record-kind",
        "invalid-id",
        "provenance-mismatch",
        "wrong-digest-filename",
    ),
)
def test_any_malformed_registry_member_refuses_the_complete_scan(tmp_path, damage):
    instance = make_world(tmp_path)
    record = write_raw_admission(instance.config.world_root)
    registry = instance.config.world_root / "registry"
    path = registry / f"{world_module.admission_digest(record)}.yaml"
    if damage == "foreign-file":
        (registry / "foreign.txt").write_text("x", encoding="utf-8")
    elif damage == "directory":
        (registry / "member.yaml").mkdir()
    elif damage == "duplicate-key":
        path.write_text(path.read_text(encoding="utf-8") + "actor: bob\n", encoding="utf-8")
    elif damage == "unknown-field":
        path.write_text(path.read_text(encoding="utf-8") + "extra: x\n", encoding="utf-8")
    elif damage == "wrong-record-kind":
        path.write_text(path.read_text(encoding="utf-8").replace("admission", "other", 1), encoding="utf-8")
    elif damage == "invalid-id":
        path.write_text(path.read_text(encoding="utf-8").replace("1" * 32, "x", 1), encoding="utf-8")
    elif damage == "provenance-mismatch":
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "kind: fresh", f"kind: replica-of\n  parent_corpus_id: {'2' * 32}"
            ),
            encoding="utf-8",
        )
    else:
        path.rename(registry / ("0" * 64 + ".yaml"))

    for read in (instance.registry, lambda: instance.status("1" * 32)):
        with pytest.raises(RegistryMalformed) as raised:
            read()
        assert raised.value.__cause__ is not None


def test_registry_returns_records_sorted_by_content_digest(tmp_path):
    instance = make_world(tmp_path)
    second = write_raw_admission(instance.config.world_root, "2" * 32, actor="bob")
    first = write_raw_admission(instance.config.world_root, "1" * 32, actor="alice")

    assert instance.registry().admissions == tuple(sorted((first, second), key=world_module.admission_digest))


def test_content_named_raw_admission_with_contradictory_provenance_is_malformed(tmp_path):
    instance = make_world(tmp_path)
    record = world_module.AdmissionRecord(
        world_module.CorpusManifest(2, "1" * 32, PINS),
        world_module.ReplicaOf("2" * 32),
        "alice",
    )
    registry = instance.config.world_root / "registry"
    registry.mkdir(parents=True)
    (registry / f"{world_module.admission_digest(record)}.yaml").write_text(
        yaml.safe_dump(world_module.admission_projection(record), sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(RegistryMalformed):
        instance.registry()


def test_world_public_surface_has_no_registry_mutator():
    assert {
        name for name, value in vars(world_module.World).items() if not name.startswith("_") and callable(value)
    } == {"admit", "depart", "registry", "retire", "status"}
