"""The durable executor's build and its failure mapping, portably.

Every test here stops at the engine's door: `run_transaction` is replaced, and
what is asserted is the spec the adapter *hands* it. That is the whole of what
the adapter decides — the timeline, the digests, the effects, the surfaces, the
intent, the constants — and none of it needs a certified volume. What does need
one is that the engine then does what it says, which is the acceptance
command's, not this file's.
"""

from __future__ import annotations

from hashlib import sha256
from typing import cast

import pytest
from atoms.chain.errors import ChainStateInvalid
from atoms.core.effects import CreateDirectory, CreateFileNoClobber, DeletePath, MoveNoClobber, ReplaceFile
from atoms.core.errors import (
    CapabilityUnavailable,
    PreconditionRefused,
    ProjectApprovalRefused,
    ProtocolError,
    SpecValidationError,
    TransactionHalted,
)
from atoms.core.fingerprint import ABSENT, FileState
from atoms.core.spec import SCHEMA_VERSION
from atoms.fs.platform import select_backend
from atoms.store.errors import MetadataStoreInvalid
from nodes.core.errors import ExecutionError, PlanRefusedError
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp, WritePlan

from beliefs import root as science_root
from beliefs.identity import v1
from beliefs.root import CONSUMER_TAG, CREATED_FILE_MODE, PRODUCTION_STORAGE, DurableExecutor

CONTENT = b"# a node\n"
DIGEST = sha256(CONTENT).hexdigest()


@pytest.fixture()
def submitted(monkeypatch):
    """Every spec the adapter submits, with its payload source."""
    calls: list[tuple] = []

    def capture(backend, project_root, metadata_root, storage, spec, payloads):
        calls.append((project_root, metadata_root, spec, payloads))

    monkeypatch.setattr(science_root, "run_transaction", capture)
    return calls


def executor(tmp_path) -> DurableExecutor:
    # The real backend and the production profile: `select_backend` performs no
    # I/O, and no transaction is submitted here, so nothing about the volume is
    # touched. A stand-in would let the adapter be built with something the
    # engine would refuse.
    return DurableExecutor(
        tmp_path,
        backend=select_backend(),
        storage=PRODUCTION_STORAGE,
        metadata_root=tmp_path.with_name(tmp_path.name + ".metadata"),
        consumer_tag=CONSUMER_TAG,
        intent_domain=science_root.INTENT_DOMAIN,
    )


def existing(tmp_path, relative: str, content: bytes = CONTENT, mode: int = 0o600) -> str:
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    target.chmod(mode)
    return sha256(content).hexdigest()


class TestTheEmptyPlan:
    def test_an_empty_plan_applies_vacuously(self, tmp_path, submitted):
        executor(tmp_path).execute([])
        assert submitted == []


class TestTheEffectMapping:
    def test_a_create_maps_to_create_file_no_clobber(self, tmp_path, submitted):
        executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        (effect,) = submitted[0][2].effects
        assert effect == CreateFileNoClobber(
            effect_id="op-0",
            path="p.md",
            post=FileState(content_hash="sha256:" + DIGEST, mode=CREATED_FILE_MODE, byte_len=len(CONTENT)),
        )

    def test_a_replace_maps_to_replace_file_and_carries_the_observed_pre_state(self, tmp_path, submitted):
        digest = existing(tmp_path, "p.md", mode=0o600)
        executor(tmp_path).execute([ReplaceOp(path="p.md", content=b"next", expected_digest=digest)])
        (effect,) = submitted[0][2].effects
        assert isinstance(effect, ReplaceFile)
        assert effect.pre == FileState(content_hash="sha256:" + digest, mode=0o600, byte_len=len(CONTENT))
        assert effect.post.mode == CREATED_FILE_MODE  # the adapter's one constant, on posts only

    def test_a_delete_maps_to_delete_path(self, tmp_path, submitted):
        digest = existing(tmp_path, "p.md")
        executor(tmp_path).execute([DeleteOp(path="p.md", expected_digest=digest)])
        (effect,) = submitted[0][2].effects
        assert isinstance(effect, DeletePath)
        assert isinstance(effect.pre, FileState)
        assert effect.pre.content_hash == "sha256:" + digest

    def test_effect_ids_are_derived_from_the_operations_position(self, tmp_path, submitted):
        executor(tmp_path).execute(
            [CreateOp(path="a.md", content=CONTENT), CreateOp(path="b.md", content=CONTENT)]
        )
        assert [effect.effect_id for effect in submitted[0][2].effects] == ["op-0", "op-1"]

    def test_move_no_clobber_is_never_emitted(self, tmp_path, submitted):
        digest = existing(tmp_path, "old.md")
        executor(tmp_path).execute(
            [CreateOp(path="new.md", content=CONTENT), DeleteOp(path="old.md", expected_digest=digest)]
        )
        assert not any(isinstance(effect, MoveNoClobber) for effect in submitted[0][2].effects)

    def test_a_create_below_a_missing_directory_carries_its_parent(self, tmp_path, submitted):
        # The engine refuses a create whose parent neither exists nor is created
        # by this transaction, so the directory is created inside the same
        # transaction — see `_missing_ancestors`' recorded deviation.
        executor(tmp_path).execute([CreateOp(path="proposition/p.md", content=CONTENT)])
        effects = submitted[0][2].effects
        assert isinstance(effects[0], CreateDirectory) and effects[0].path == "proposition"
        assert isinstance(effects[1], CreateFileNoClobber)

    def test_an_existing_directory_is_not_recreated(self, tmp_path, submitted):
        (tmp_path / "proposition").mkdir()
        executor(tmp_path).execute([CreateOp(path="proposition/p.md", content=CONTENT)])
        assert not any(isinstance(effect, CreateDirectory) for effect in submitted[0][2].effects)


class TestTheTimeline:
    def test_a_paths_second_occurrence_derives_its_pre_state_from_the_first_post(self, tmp_path, submitted):
        first = b"one"
        second_digest = sha256(first).hexdigest()
        executor(tmp_path).execute(
            [
                CreateOp(path="p.md", content=first),
                ReplaceOp(path="p.md", content=b"two", expected_digest=second_digest),
            ]
        )
        create, replace = submitted[0][2].effects
        assert replace.pre == create.post  # continuous timeline, no second read

    def test_a_second_occurrence_whose_expected_digest_names_the_disk_state_is_refused(self, tmp_path, submitted):
        # The disk digest is *stale* after the first operation, and an executor
        # that re-read disk for every occurrence would accept this plan.
        on_disk = existing(tmp_path, "p.md")
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute(
                [
                    ReplaceOp(path="p.md", content=b"one", expected_digest=on_disk),
                    ReplaceOp(path="p.md", content=b"two", expected_digest=on_disk),
                ]
            )
        assert (refused.value.index, refused.value.applied) == (1, 0)
        assert submitted == []

    def test_a_create_on_a_path_an_earlier_operation_made_present_is_refused(self, tmp_path, submitted):
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute(
                [CreateOp(path="p.md", content=CONTENT), CreateOp(path="p.md", content=CONTENT)]
            )
        assert (refused.value.index, refused.value.applied) == (1, 0)
        assert submitted == []

    def test_a_replace_after_a_delete_is_refused_as_unsatisfiable(self, tmp_path, submitted):
        digest = existing(tmp_path, "p.md")
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute(
                [
                    DeleteOp(path="p.md", expected_digest=digest),
                    ReplaceOp(path="p.md", content=b"x", expected_digest=digest),
                ]
            )
        assert (refused.value.index, refused.value.applied) == (1, 0)


class TestThePreconditionChecks:
    def test_a_digest_mismatch_refuses_before_any_effect(self, tmp_path, submitted):
        existing(tmp_path, "p.md")
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute([ReplaceOp(path="p.md", content=b"x", expected_digest="ab" * 32)])
        assert (refused.value.index, refused.value.applied) == (0, 0)
        assert submitted == []

    def test_a_replace_on_an_absent_path_is_refused(self, tmp_path, submitted):
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute([ReplaceOp(path="gone.md", content=b"x", expected_digest="ab" * 32)])
        assert (refused.value.index, refused.value.applied) == (0, 0)

    def test_a_delete_on_an_absent_path_is_refused(self, tmp_path, submitted):
        with pytest.raises(ExecutionError) as refused:
            executor(tmp_path).execute([DeleteOp(path="gone.md", expected_digest="ab" * 32)])
        assert (refused.value.index, refused.value.applied) == (0, 0)


class TestTheSurfaces:
    def test_the_initial_surface_holds_each_touched_paths_first_pre_state(self, tmp_path, submitted):
        digest = existing(tmp_path, "p.md")
        executor(tmp_path).execute(
            [
                ReplaceOp(path="p.md", content=b"one", expected_digest=digest),
                CreateOp(path="q.md", content=CONTENT),
            ]
        )
        initial = {entry.path: entry.state for entry in submitted[0][2].initial_surface}
        assert initial["p.md"].content_hash == "sha256:" + digest
        assert initial["q.md"] == ABSENT

    def test_the_final_surface_holds_each_touched_paths_last_post_state(self, tmp_path, submitted):
        digest = existing(tmp_path, "p.md")
        executor(tmp_path).execute([DeleteOp(path="p.md", expected_digest=digest)])
        final = {entry.path: entry.state for entry in submitted[0][2].final_surface}
        assert final["p.md"] == ABSENT


class TestTheSpecConstants:
    def test_the_spec_carries_the_adapters_constants(self, tmp_path, submitted):
        executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        spec = submitted[0][2]
        assert spec.consumer_tag == CONSUMER_TAG
        assert (spec.dependencies, spec.fulfills, spec.registered_paths) == ((), None, ("p.md",))

    def test_every_plan_path_is_registered(self, tmp_path, submitted):
        executor(tmp_path).execute(
            [
                CreateOp("corpus.yaml", b"manifest"),
                CreateOp("registry/a.yaml", b"record"),
            ]
        )
        assert submitted[0][2].registered_paths == ("corpus.yaml", "registry/a.yaml")

    def test_duplicate_plan_paths_register_once_in_first_occurrence_order(self, tmp_path, submitted):
        executor(tmp_path).execute(
            [
                CreateOp(path="x", content=b"one"),
                ReplaceOp(path="x", content=b"two", expected_digest=sha256(b"one").hexdigest()),
            ]
        )
        assert submitted[0][2].registered_paths == ("x",)

    def test_world_executor_uses_world_consumer_and_intent_domains(self, tmp_path, submitted):
        root = tmp_path / "world"
        root.mkdir()
        science_root._world_executor_factory()(root).execute([CreateOp("world.yaml", b"world")])
        spec = submitted[0][2]
        assert spec.consumer_tag == "science-world-write-v1"
        assert spec.intent_digest == "sha256:" + v1.digest(
            "science.world-write-intent.v1",
            [{"op": "create", "path": "world.yaml", "content_sha256": sha256(b"world").hexdigest()}],
        )

    def test_the_schema_version_comes_from_the_engines_own_constant(self, tmp_path, submitted):
        executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        assert submitted[0][2].schema_version == SCHEMA_VERSION

    def test_the_intent_digest_is_the_plans_own(self, tmp_path, submitted):
        plan = [CreateOp(path="p.md", content=CONTENT)]
        executor(tmp_path).execute(plan)
        assert submitted[0][2].intent_digest == science_root.write_intent_digest(plan)

    def test_the_payload_source_is_keyed_by_content_digest(self, tmp_path, submitted):
        executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        payloads = submitted[0][3]
        assert payloads.open("sha256:" + DIGEST).read() == CONTENT
        with pytest.raises(KeyError):
            payloads.open("sha256:" + "ab" * 32)

    def test_the_root_and_the_sibling_metadata_root_are_what_is_submitted(self, tmp_path, submitted):
        executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        project_root, metadata_root, _, _ = submitted[0]
        assert project_root == str(tmp_path)
        assert metadata_root == str(tmp_path) + ".metadata"


class TestTheMalformednessChecks:
    @pytest.mark.parametrize(
        "path",
        ["/absolute.md", "../escape.md", "a/../../escape.md", ".nodes-index/x.md", ""],
    )
    def test_a_lexically_malformed_path_is_refused_before_any_read(self, tmp_path, submitted, path):
        with pytest.raises(PlanRefusedError):
            executor(tmp_path).execute([CreateOp(path=path, content=CONTENT)])
        assert submitted == []

    def test_an_engine_reserved_leaf_is_refused(self, tmp_path, submitted):
        with pytest.raises(PlanRefusedError):
            executor(tmp_path).execute([CreateOp(path=".#~chain/entry", content=CONTENT)])
        assert submitted == []

    def test_an_unknown_operation_kind_is_refused(self, tmp_path, submitted):
        with pytest.raises(PlanRefusedError):
            executor(tmp_path).execute(cast("WritePlan", [object()]))


class TestTheFailureMapping:
    """§4's table, every row. `applied=0` is licensed only where the engine's
    own contract proves pre-mutation state; everything else says restoration is
    unproved."""

    @pytest.mark.parametrize(
        ("raised", "applied"),
        [
            (ProjectApprovalRefused("rooted proof"), 0),
            (SpecValidationError("adapter bug"), 0),
            (PreconditionRefused("clean refusal"), 0),
            (CapabilityUnavailable("not certified"), 0),
            (MetadataStoreInvalid("stop and preserve"), None),
            (ChainStateInvalid("stop and preserve"), None),
            (TransactionHalted("unattributable"), None),
            (ProtocolError("engine contract"), None),
            (RuntimeError("unrecognized"), None),
        ],
    )
    def test_each_engine_failure_maps_to_its_row(self, tmp_path, monkeypatch, raised, applied):
        def fail(*_args, **_kwargs):
            raise raised

        monkeypatch.setattr(science_root, "run_transaction", fail)
        with pytest.raises(ExecutionError) as mapped:
            executor(tmp_path).execute([CreateOp(path="p.md", content=CONTENT)])
        assert mapped.value.index is None
        assert mapped.value.applied == applied
        assert mapped.value.__cause__ is raised
