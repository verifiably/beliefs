"""The run-confinement values: the closed vocabulary, the two exact policies,
science.environment.v2, the instance attestation, and the receipt and run
domains (design §3, §4.1, §6.3)."""

import dataclasses

import pytest
from confinement_fixtures import ENV_IDENTITY, MOUNTS, confined_closure, confined_receipt, instance
from conftest import ENVIRONMENT, OTHER_ENVIRONMENT
from fixtures_cut3 import closure, occurrence

from beliefs.errors import BoundaryPolicyUnsupported, MalformedClosure
from beliefs.identity import v1
from beliefs.recipe import (
    BOUNDARY_RECEIPT_DOMAIN,
    CAPABILITIES,
    CONFINED_POLICY,
    CONFINED_RECEIPT_DOMAIN,
    CONFINED_RUN_DOMAIN,
    MINIMAL_POLICY,
    NAMESPACES,
    REQUIRED_FOR_CLEAN_ENVIRONMENT,
    RUN_DOMAIN,
    SUPPORTED_POLICIES,
    BoundaryPolicy,
    BoundaryReceipt,
    LaunchAttestation,
    _occurrence_projection,
    _receipt_projection,
    mount_plan_identity,
    run_domain_for,
    supported_policy,
)
from beliefs.replay import qualifies


# --- K1: the vocabulary and the two exact policies ----------------------------
def test_the_vocabulary_is_closed_and_the_requirement_is_its_own_explicit_tuple():
    assert CAPABILITIES == ("from-bundle", "closure-confined-filesystem", "network-denied")
    assert REQUIRED_FOR_CLEAN_ENVIRONMENT == CAPABILITIES
    assert REQUIRED_FOR_CLEAN_ENVIRONMENT is not CAPABILITIES
    with pytest.raises(MalformedClosure):
        BoundaryPolicy(identity="p", scope_rule="scope-derivation/v1", capabilities=("teleportation",))


def test_k1_a_duplicate_capability_is_unspellable():
    with pytest.raises(MalformedClosure):
        BoundaryPolicy(identity="p", scope_rule="scope-derivation/v1", capabilities=("from-bundle", "from-bundle"))


def test_k1_the_two_known_definitions_are_exact():
    assert MINIMAL_POLICY == BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")
    assert CONFINED_POLICY.capabilities == CAPABILITIES
    assert SUPPORTED_POLICIES == (MINIMAL_POLICY, CONFINED_POLICY)
    assert supported_policy(MINIMAL_POLICY) is MINIMAL_POLICY
    assert supported_policy(BoundaryPolicy(**dataclasses.asdict(CONFINED_POLICY))) == CONFINED_POLICY


def test_k1_a_known_identity_with_another_scope_rule_is_unsupported():
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(CONFINED_POLICY, scope_rule="scope-derivation/v2"))


def test_k1_a_reordered_spelling_of_a_known_capability_set_is_that_definition():
    reordered = BoundaryPolicy(
        identity=CONFINED_POLICY.identity,
        scope_rule=CONFINED_POLICY.scope_rule,
        capabilities=tuple(reversed(CAPABILITIES)),
    )
    assert reordered != CONFINED_POLICY
    assert supported_policy(reordered) is CONFINED_POLICY


def test_k1_a_known_identity_with_fewer_capabilities_is_unsupported():
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(CONFINED_POLICY, capabilities=CAPABILITIES[:2]))
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(MINIMAL_POLICY, capabilities=("network-denied",)))
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy("boundary-policy/confined-v1")


# --- K3: the instance attestation ---------------------------------------------
def test_k3_a_mount_plan_identity_disagreeing_with_its_mounts_is_malformed():
    with pytest.raises(MalformedClosure):
        instance(mount_plan_identity="sha256:" + "00" * 32)
    fewer = MOUNTS[:-1]
    assert instance(mounts=fewer, mount_plan_identity=mount_plan_identity(fewer)).mounts == fewer


def test_k3_an_instance_attests_every_namespace_and_no_other():
    with pytest.raises(MalformedClosure):
        instance(namespaces=NAMESPACES[:-1])
    with pytest.raises(MalformedClosure):
        instance(namespaces=(*NAMESPACES, "time"))
    assert instance(namespaces=tuple(reversed(NAMESPACES))).namespaces == tuple(reversed(NAMESPACES))


def test_k3_the_confined_members_are_all_present_or_all_absent():
    with pytest.raises(MalformedClosure):
        confined_receipt(mounts=None)
    with pytest.raises(MalformedClosure):
        LaunchAttestation(scratch_mapping="s", argv=("a",), rendered_config=(), instance=instance())
    with pytest.raises(MalformedClosure):
        LaunchAttestation(scratch_mapping="s", argv=("a",), rendered_config=(), rendered_environment=(), mounts=())
    launch = LaunchAttestation(scratch_mapping="s", argv=("a",), rendered_config=())
    minimal = BoundaryReceipt(planning=launch, execution=launch)
    assert not minimal.confined and confined_receipt().confined


def test_a_receipt_capability_outside_the_vocabulary_is_unspellable():
    with pytest.raises(MalformedClosure):
        LaunchAttestation(scratch_mapping="s", argv=("a",), rendered_config=(), capabilities=("teleportation",))


# --- K4: the domains ----------------------------------------------------------
def test_k4_the_minimal_receipt_projection_is_byte_stable_under_v1():
    launch = LaunchAttestation(
        scratch_mapping="scratch-mount-a", argv=("snakemake",), rendered_config=(("alpha", "0.05"),)
    )
    receipt = BoundaryReceipt(planning=launch, execution=launch)
    assert _receipt_projection(receipt) == {
        "planning": {
            "scratch_mapping": "scratch-mount-a",
            "argv": ["snakemake"],
            "rendered_config": [["alpha", "0.05"]],
            "capabilities": [],
        },
        "execution": {
            "scratch_mapping": "scratch-mount-a",
            "argv": ["snakemake"],
            "rendered_config": [["alpha", "0.05"]],
            "capabilities": [],
        },
    }
    assert receipt.identity() == v1.digest(BOUNDARY_RECEIPT_DOMAIN, _receipt_projection(receipt))
    assert BOUNDARY_RECEIPT_DOMAIN == "science.boundary-receipt.v3"


def test_k4_a_confined_receipt_projects_its_three_members_under_v2():
    receipt = confined_receipt()
    projection = _receipt_projection(receipt)
    assert set(projection) == {"planning", "execution"}
    execution = projection["execution"]
    assert isinstance(execution, dict)
    instance_projection = execution["instance"]
    assert isinstance(instance_projection, dict)
    assert instance_projection["environment_identity"] == ENV_IDENTITY
    assert receipt.identity() == v1.digest(CONFINED_RECEIPT_DOMAIN, projection)
    assert CONFINED_RECEIPT_DOMAIN == "science.boundary-receipt.v4"


def test_k4_a_confined_receipt_makes_a_v2_run():
    assert run_domain_for(recipe_v2=False, confined=False) == RUN_DOMAIN == "science.run.v1"
    assert run_domain_for(recipe_v2=False, confined=True) == CONFINED_RUN_DOMAIN == "science.run.v2"
    minimal = closure()
    confined = confined_closure()
    assert minimal.address() == v1.digest(
        "science.run.v3",
        {"recipe": minimal.recipe._projection(), "result": [["outputs/result.txt", minimal.result.outputs[0][1]]],
         "occurrence": _occurrence_projection(minimal.occurrence)},
    )
    assert confined.address() != minimal.address()
    assert confined.address() == v1.digest(
        "science.run.v4",
        {"recipe": confined.recipe._projection(), "result": [["outputs/result.txt", confined.result.outputs[0][1]]],
         "occurrence": _occurrence_projection(confined.occurrence)},
    )


def test_the_cut_3_occurrence_fixture_still_spells_a_minimal_receipt():
    assert not occurrence().receipt.confined


def test_qualification_reads_the_execution_launch_and_not_the_planning_one(confined_launch):
    qualifying = confined_launch(capabilities=REQUIRED_FOR_CLEAN_ENVIRONMENT)
    short = confined_launch(capabilities=("from-bundle",))
    assert qualifies(BoundaryReceipt(planning=short, execution=qualifying), ENVIRONMENT) is True
    assert qualifies(BoundaryReceipt(planning=qualifying, execution=short), ENVIRONMENT) is False


def test_a_planning_launch_cannot_supply_the_execution_s_environment_agreement(confined_launch):
    qualifying = confined_launch(environment_identity=ENVIRONMENT)
    other = confined_launch(environment_identity=OTHER_ENVIRONMENT)
    assert qualifies(BoundaryReceipt(planning=qualifying, execution=other), ENVIRONMENT) is False
