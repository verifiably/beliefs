"""A mounted corpus's profile from its own manifest (session-mounts design §3.1,
decision 5; row J13), portable: manifests written into `tmp_path` roots."""

from __future__ import annotations

import pytest
from profiles import WITH_BIOLOGY, biology, pins_for

from beliefs.consulted import CorpusPins
from beliefs.corpus import CoordinationResolver
from beliefs.errors import ManifestMalformed, MountPinUnresolved, UnparsedContract
from beliefs.mount import compile_mount_profile
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world.registry import CorpusManifest, manifest_bytes

SHIPPED = compile_profile(
    shipped_base_contract(), [shipped_domain_contract("biology")], coordination=shipped_coordination(2)
)
LOCAL = compile_profile(shipped_base_contract(), [biology("fixture")], coordination=shipped_coordination(2))
COORD_ONLY = compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))


def _root(tmp_path, name, pins: CorpusPins, corpus_id: str = "c" * 32):
    root = tmp_path / name
    root.mkdir()
    (root / "corpus.yaml").write_bytes(manifest_bytes(CorpusManifest(2, corpus_id, pins)))
    return root


@pytest.mark.parametrize("version", (1, 2, 3))
def test_shipped_pins_compile_with_nothing_available(tmp_path, version):
    expected = compile_profile(
        shipped_base_contract(), [shipped_domain_contract("biology")], coordination=shipped_coordination(version)
    )
    root = _root(tmp_path, "a", pins_for(expected))
    assert compile_mount_profile(root).compiled_identity == expected.compiled_identity


def test_a_test_local_contract_resolves_when_available(tmp_path):
    """J13-a."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert compiled.compiled_identity == LOCAL.compiled_identity
    assert pins_for(compiled) == pins_for(LOCAL)


def test_the_mm30_shape_compiles_without_coordination(tmp_path):
    root = _root(tmp_path, "c", pins_for(WITH_BIOLOGY))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert compiled.compiled_identity == WITH_BIOLOGY.compiled_identity and not compiled.coordination_kinds


def test_an_unresolved_pin_names_root_namespace_and_pin(tmp_path):
    """J13-a, and Review Focus 2."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    with pytest.raises(MountPinUnresolved) as caught:
        compile_mount_profile(root)
    pin = pins_for(LOCAL).domains["biology"]
    assert (caught.value.root, caught.value.namespace, caught.value.pin) == (root, "biology", pin)
    assert str(root) in str(caught.value) and pin in str(caught.value)


def test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin(tmp_path):
    """J13-a's negative."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    with pytest.raises(MountPinUnresolved):
        compile_mount_profile(root, available=(biology("fixture, second variant"),))


def test_an_available_unpinned_document_is_never_activated(tmp_path):
    """J13-b."""
    root = _root(tmp_path, "coord", pins_for(COORD_ONLY))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert set(compiled.activated_contracts) == {"coordination"}
    assert compiled.compiled_identity == COORD_ONLY.compiled_identity


def test_duplicate_available_documents_are_harmless(tmp_path):
    """Review Focus 3."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    twice = compile_mount_profile(root, available=(biology("fixture"), biology("fixture")))
    shipped_too = compile_mount_profile(
        _root(tmp_path, "a", pins_for(SHIPPED)), available=(shipped_domain_contract("biology"),)
    )
    assert (
        twice.compiled_identity == LOCAL.compiled_identity
        and shipped_too.compiled_identity == SHIPPED.compiled_identity
    )


@pytest.mark.parametrize(
    "pins, namespace",
    [
        (CorpusPins("science:" + "0" * 64, {}), "science"),
        (
            CorpusPins(pins_for(COORD_ONLY).science_contract, {"coordination": "coordination:" + "0" * 64}),
            "coordination",
        ),
    ],
    ids=["unshipped-base", "unshipped-coordination"],
)
def test_well_formed_pins_nothing_carries_refuse(tmp_path, pins, namespace):
    with pytest.raises(MountPinUnresolved) as caught:
        compile_mount_profile(_root(tmp_path, "x", pins), available=(biology("fixture"),))
    assert caught.value.namespace == namespace


def test_a_malformed_pin_is_the_manifests_refusal(tmp_path):
    """§3.1: `load_manifest`'s refusals propagate; `MountPinUnresolved` is for well-formed pins."""
    pins = CorpusPins(pins_for(COORD_ONLY).science_contract, {"biology": "not-the-namespace:" + "0" * 64})
    with pytest.raises(ManifestMalformed):
        compile_mount_profile(_root(tmp_path, "x", pins), available=(biology("fixture"),))


def test_each_compiled_profile_is_accepted_by_the_resolver(tmp_path):
    roots = {
        _root(tmp_path, "a", pins_for(SHIPPED), "a" * 32): (),
        _root(tmp_path, "b", pins_for(LOCAL), "b" * 32): (biology("fixture"),),
        _root(tmp_path, "c", pins_for(WITH_BIOLOGY), "d" * 32): (biology("fixture"),),
    }
    resolver = CoordinationResolver({root: compile_mount_profile(root, available=docs) for root, docs in roots.items()})
    assert set(resolver.mounted()) == {root.resolve() for root in roots}


def test_arguments_are_typed(tmp_path):
    root = _root(tmp_path, "a", pins_for(SHIPPED))
    with pytest.raises(TypeError):
        compile_mount_profile(str(root))  # type: ignore[arg-type]
    with pytest.raises(UnparsedContract):
        compile_mount_profile(root, available=(object(),))  # type: ignore[arg-type]
