"""The composition root's portable half: the metadata rule, the genesis
constant, and the write-intent encoding.

The **durable** half — registering a real root through the engine — is not here
and cannot be: it runs only on a certified volume, so it lives in the cut-4
acceptance command, which errors rather than skips when the tuple is not
certified. A test that quietly passed off a certified volume would be reporting
green for a guarantee it never exercised.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from atoms.chain.model import GenesisEntry
from atoms.core.errors import PreconditionRefused
from authority import FULL
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp

from beliefs import root
from beliefs.errors import CorpusRootRefused, PermitExceeded, PermitFact, WorldIdMismatch, WorldUninitialized
from beliefs.identity import v1
from beliefs.permit import READ_ONLY
from beliefs.world import Fresh, WorldConfig, _world_mirror_bytes


def patch_world_engine(monkeypatch, calls, world_id="1" * 32):
    """Stand in for the engine beneath a world root: registration, the world
    executor, and the chain read `open_world` makes.

    The chain read is here rather than per-arm because `open_world` now checks
    the genesis payload's `world_id` against the configuration and the mirror
    (log-verification design §6.3), so every arm that opens a world needs a
    genesis to read. It is **not** recorded in `calls`: the arms that assert
    `calls == []` are asserting that opening registers nothing, which is a
    different claim and still true.
    """

    def record_registration(_backend, _project_root, _metadata_root, _storage, payload, _surface):
        calls.append(("register", payload))

    class ChainView:
        genesis_digest = "0" * 64
        tip = "0" * 64
        entries = (("0" * 64, GenesisEntry(root._world_genesis_payload(world_id), ())),)

    monkeypatch.setattr(root, "read_chain", lambda *_args: ChainView())

    class Recorder:
        def __init__(self, world_root):
            self.root = world_root

        def execute(self, plan):
            calls.append(("execute", plan))
            for operation in plan:
                assert isinstance(operation, CreateOp)
                target = self.root / operation.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(operation.content)

    monkeypatch.setattr(root, "register_root", record_registration)
    monkeypatch.setattr(root, "_world_executor_factory", lambda: lambda world_root: Recorder(world_root))


class TestWorldRoots:
    def test_init_world_registers_genesis_then_creates_mirror(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())

        root.init_world_root(config, authority=FULL)

        assert calls[0] == (
            "register",
            v1.encode({"domain": "science.world-root.v1", "world_id": "1" * 32}),
        )
        assert calls[1] == ("execute", [CreateOp("world.yaml", _world_mirror_bytes("1" * 32))])

    def test_init_world_exact_mirror_retry_executes_no_transaction(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        root.init_world_root(config, authority=FULL)
        calls.clear()

        root.init_world_root(config, authority=FULL)

        assert [kind for kind, _value in calls] == ["register"]

    def test_init_world_refuses_a_file_root_before_registration(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        occupied = tmp_path / "world"
        occupied.write_text("not a world", encoding="utf-8")

        with pytest.raises(CorpusRootRefused):
            root.init_world_root(WorldConfig(occupied, "1" * 32, ()), authority=FULL)

        assert calls == []

    def test_init_world_refuses_a_malformed_mirror_after_registration(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        world_root = tmp_path / "world"
        world_root.mkdir()
        (world_root / "world.yaml").write_text("oops: true\n", encoding="utf-8")

        with pytest.raises(WorldUninitialized):
            root.init_world_root(WorldConfig(world_root, "1" * 32, ()), authority=FULL)

        assert [kind for kind, _value in calls] == ["register"]

    def test_init_world_refuses_a_mismatched_mirror_after_registration(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        world_root = tmp_path / "world"
        world_root.mkdir()
        (world_root / "world.yaml").write_bytes(_world_mirror_bytes("2" * 32))

        with pytest.raises(WorldIdMismatch):
            root.init_world_root(WorldConfig(world_root, "1" * 32, ()), authority=FULL)

        assert [kind for kind, _value in calls] == ["register"]

    def test_init_world_creates_only_the_mirror(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        world_root = tmp_path / "world"

        root.init_world_root(WorldConfig(world_root, "1" * 32, ()), authority=FULL)

        assert (world_root / "world.yaml").is_file()
        assert not any((world_root / name).exists() for name in ("registry", "epochs", "rules"))

    def test_open_world_returns_an_engine_free_world_without_registering(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))

        world = root.open_world(config, authority=FULL)

        assert world.config is config
        assert calls == []

    def test_open_world_refuses_a_mismatched_mirror_without_registering(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes("2" * 32))

        with pytest.raises(WorldIdMismatch):
            root.open_world(config, authority=FULL)

        assert calls == []

    def test_open_world_refuses_a_genesis_naming_another_world(self, monkeypatch, tmp_path):
        # The third claim: the configuration and the mirror can agree with each
        # other and still both be edits. The chain genesis is the one of the
        # three no operator rewrites in passing, and `open_world` is the surface
        # every ordinary consumer crosses, so the disagreement is refused here
        # (log-verification design §6.3).
        calls = []
        patch_world_engine(monkeypatch, calls, world_id="2" * 32)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))

        with pytest.raises(WorldIdMismatch) as caught:
            root.open_world(config, authority=FULL)

        assert "2" * 32 in str(caught.value)
        assert calls == []

    def test_open_world_refuses_a_root_that_was_never_initialized_as_a_world(self, monkeypatch, tmp_path):
        # The other half of the single-homed predicate the export act already
        # used: a payload that is not a Science world genesis at all says the
        # root was never initialized as one, which is a different fact from a
        # root that belongs to a different world.
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))

        class CorpusGenesis:
            genesis_digest = "0" * 64
            tip = "0" * 64
            entries = (("0" * 64, GenesisEntry(root.GENESIS_PAYLOAD, ())),)

        monkeypatch.setattr(root, "read_chain", lambda *_args: CorpusGenesis())

        with pytest.raises(WorldUninitialized):
            root.open_world(config, authority=FULL)

    def test_open_world_reads_the_genesis_through_read_chain_and_names_an_unregistered_root(
        self, monkeypatch, tmp_path
    ):
        # §6.3's "read through `read_chain`" makes opening touch the engine, and
        # the engine's answer for a root that was never registered is its only
        # `PreconditionRefused`. `WorldUninitialized` is already Science's name
        # for that state — it is what the mirror loader raises for a root
        # `init_world_root` never made — so the two arms of "never initialized"
        # meet under one name. The mapping is made in `open_world` and not in
        # the seam: §6.4's translation vocabulary is closed at three engine
        # states and this is not one of them.
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))
        unregistered = PreconditionRefused("the project root is not registered")

        def raising(*_args):
            raise unregistered

        monkeypatch.setattr(root, "read_chain", raising)

        with pytest.raises(WorldUninitialized) as caught:
            root.open_world(config, authority=FULL)

        assert caught.value.__cause__ is unregistered
        # The seam is untouched: the very same refusal keeps its own contract
        # for every other reader of a head, because nothing was translated there.
        with pytest.raises(PreconditionRefused):
            root._log_seam().read_head(config.world_root)

    def test_open_world_leaves_every_other_chain_read_refusal_alone(self, monkeypatch, tmp_path):
        # The mapping above is conditioned, not by type, and this is why.
        # `read_chain` resolves recovery *before* it reaches the registration
        # check, and resolution refuses with the same class for reasons of its
        # own — a namespace that moved under an observation, a create whose
        # target appeared while the plan ran. Renaming one of those "never
        # initialized as a world" would state something false about a registered
        # root that is mid-recovery, with the truth only on `__cause__`.
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))

        for message in (
            "the namespace no longer matches approval while opening 'registry': [Errno 2] ...",
            "'registry' stopped being a directory between lookup and open",
            "'epochs/current' already exists; CreateFileNoClobber refuses",
        ):
            mid_recovery = PreconditionRefused(message)

            def raising(*_args, refusal=mid_recovery):
                raise refusal

            monkeypatch.setattr(root, "read_chain", raising)

            with pytest.raises(PreconditionRefused) as caught:
                root.open_world(config, authority=FULL)

            assert caught.value is mid_recovery

    def test_the_unregistered_root_sentinel_is_the_engines_own_wording(self):
        # The one string the mapping turns on, pinned against `atoms`' source —
        # R27's treatment of a restated constant. Both of `_registered_root`'s
        # sites raise it, and a reword there turns this red rather than silently
        # disabling the mapping.
        from atoms.coordinator import recover

        source = inspect.getsource(recover)
        assert source.count(f'PreconditionRefused("{root.UNREGISTERED_ROOT}")') == 2

    def test_world_consumer_tag_is_the_world_executor_tag(self):
        assert root.WORLD_CONSUMER_TAG == "science-world-write-v1"


class TestTheMetadataRule:
    def test_the_metadata_root_is_the_sibling_of_the_corpus_root(self):
        assert root.metadata_root_for(Path("/corpora/mm30")) == Path("/corpora/mm30.metadata")

    def test_the_sibling_sits_outside_the_corpus_root(self):
        # A metadata store *inside* the corpus would be swept up by every copy
        # of it, which is exactly what makes the two cold-arrival cases
        # indistinguishable.
        corpus = Path("/corpora/mm30")
        assert corpus not in root.metadata_root_for(corpus).parents


class TestTheGenesisPayload:
    def test_it_is_the_canonical_bytes_of_the_constant_domain_object(self):
        assert root.GENESIS_PAYLOAD == v1.encode({"domain": "science.corpus-root.v1"})

    def test_it_carries_no_corpus_identity(self):
        # Corpus manifests and `corpus_id` minting are unbuilt; identity binds
        # through a later chain entry, never by rewriting genesis.
        assert root.GENESIS_PAYLOAD == b'{"domain":"science.corpus-root.v1"}'


class TestTheInitActRefusesANonDirectory:
    def test_a_file_at_the_corpus_root_path_is_refused(self, tmp_path):
        occupied = tmp_path / "corpus"
        occupied.write_text("not a corpus", encoding="utf-8")
        with pytest.raises(CorpusRootRefused):
            root.init_corpus_root(occupied, authority=FULL)

    def test_a_symlink_root_is_registered_under_its_resolved_path(self, tmp_path, monkeypatch):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)
        calls = []
        monkeypatch.setattr(root, "register_root", lambda *args: calls.append(args))

        root.init_corpus_root(link, authority=FULL)

        _, project_root, metadata_root, *_ = calls[0]
        assert project_root == str(real.resolve())
        assert metadata_root == str(real.resolve()) + ".metadata"


class TestTheCompositionRoot:
    def test_durable_factories_are_stable_module_level_callables(self):
        assert root.durable_executor_factory() is root._DURABLE_EXECUTOR_FACTORY
        assert root._world_executor_factory() is root._world_executor

    def test_a_symlink_root_binds_every_writer_component_to_the_resolved_path(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)

        writer = root.open_corpus(link, authority=FULL)
        executor = writer._corpus.executor
        port = writer._operation_port
        assert isinstance(executor, root.DurableExecutor)
        assert isinstance(port, root.DurableOperationPort)

        assert writer._corpus.store.root == real.resolve()
        assert executor.root == real.resolve()
        assert executor._metadata_root == real.resolve().with_name("real.metadata")
        assert port.root == real.resolve()
        assert port._metadata_root == real.resolve().with_name("real.metadata")


class TestTheWriteIntentEncoding:
    def test_each_operation_kind_projects_its_own_discriminated_shape(self):
        plan = [
            CreateOp(path="proposition/p.md", content=b"created"),
            ReplaceOp(path="run/r.md", content=b"replaced", expected_digest="ab" * 32),
            DeleteOp(path="dataset/d.md", expected_digest="cd" * 32),
        ]
        assert root.write_intent_projection(plan) == [
            {
                "op": "create",
                "path": "proposition/p.md",
                "content_sha256": "406effb1e9c59672c66a598c2b21e331b23b16c54024e96d6df3e7c173549791",
            },
            {
                "op": "replace",
                "path": "run/r.md",
                "expected_digest": "ab" * 32,
                "content_sha256": "6c1aa50442a93e42c0eb2907cf4e017cd19547891fa190f3ea473582b0479290",
            },
            {"op": "delete", "path": "dataset/d.md", "expected_digest": "cd" * 32},
        ]

    def test_a_create_omits_the_expected_digest_and_a_delete_the_content(self):
        # Omission, not a placeholder: the identity encoding refuses `null`, and
        # a present-and-empty stand-in would collide with a genuinely empty one.
        create, delete = root.write_intent_projection(
            [CreateOp(path="a.md", content=b""), DeleteOp(path="b.md", expected_digest="ef" * 32)]
        )
        assert "expected_digest" not in create
        assert "content_sha256" not in delete

    def test_the_digest_carries_the_mandatory_sha256_prefix(self):
        plan = [CreateOp(path="a.md", content=b"x")]
        assert root.write_intent_digest(plan) == "sha256:" + v1.digest(
            "science.corpus-write-intent.v1", root.write_intent_projection(plan)
        )

    def test_the_intent_is_domain_separated_from_a_bare_projection_digest(self):
        plan = [CreateOp(path="a.md", content=b"x")]
        projection = root.write_intent_projection(plan)
        assert root.write_intent_digest(plan)[len("sha256:") :] != v1.encode(projection).hex()

    def test_reordering_two_operations_moves_the_intent(self):
        first = CreateOp(path="a.md", content=b"x")
        second = CreateOp(path="b.md", content=b"y")
        assert root.write_intent_digest([first, second]) != root.write_intent_digest([second, first])

    def test_the_same_path_written_with_different_content_moves_the_intent(self):
        assert root.write_intent_digest([CreateOp(path="a.md", content=b"x")]) != root.write_intent_digest(
            [CreateOp(path="a.md", content=b"y")]
        )

    def test_an_empty_plan_projects_nothing(self):
        assert root.write_intent_projection([]) == []


class TestOpenWorldRead:
    """The permit-free read door (design §16): a `World` bound to `READ_ONLY`, so
    its read surface answers and every act refuses before any effect."""

    def test_open_world_read_binds_the_read_only_authority_without_registering(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))

        world = root.open_world_read(config)

        assert world.config is config
        assert world.authority is READ_ONLY
        assert calls == []

    def test_open_world_read_refuses_every_act_before_any_effect(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes(config.world_id))
        world = root.open_world_read(config)

        with pytest.raises(PermitExceeded) as caught:
            world.admit(tmp_path / "corpus", provenance=Fresh())

        assert caught.value.requirement == PermitFact("family", "registry")
        assert calls == []
        assert not (config.world_root / "registry").exists()

    def test_open_world_read_refuses_the_same_worlds_open_world_refuses(self, monkeypatch, tmp_path):
        calls = []
        patch_world_engine(monkeypatch, calls)
        config = WorldConfig(tmp_path / "world", "1" * 32, ())
        config.world_root.mkdir()
        (config.world_root / "world.yaml").write_bytes(_world_mirror_bytes("2" * 32))

        with pytest.raises(WorldIdMismatch):
            root.open_world_read(config)

        assert calls == []
