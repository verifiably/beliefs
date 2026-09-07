"""Confined-receipt value builders for the portable suite."""

from confinement_constants import CONFINED_MOUNTS as MOUNTS
from confinement_constants import ENVIRONMENT as ENV_IDENTITY
from confinement_constants import RENDERED_ENVIRONMENT, SANDBOX_MOUNTS
from fixtures_cut3 import closure, occurrence

from beliefs.recipe import (
    CAPABILITIES,
    NAMESPACES,
    BoundaryReceipt,
    InstanceAttestation,
    LaunchAttestation,
    mount_plan_identity,
)


def instance(**overrides) -> InstanceAttestation:
    fields = {
        "namespaces": NAMESPACES,
        "mounts": MOUNTS,
        "mount_plan_identity": mount_plan_identity(MOUNTS),
        "environment_identity": ENV_IDENTITY,
    }
    fields.update(overrides)
    return InstanceAttestation(**fields)


def confined_launch(**overrides) -> LaunchAttestation:
    fields = {
        "scratch_mapping": "/host/scratch/run-1",
        "argv": ("/science/env/venv/bin/python", "-m", "snakemake"),
        "rendered_config": (
            ("seed_derivation_rule", "seed-derivation/v1"),
            ("seed_roots", '{"model-initialization":"7"}'),
        ),
        "capabilities": CAPABILITIES,
        "instance": instance(),
        "rendered_environment": RENDERED_ENVIRONMENT,
        "mounts": SANDBOX_MOUNTS,
    }
    fields.update(overrides)
    return LaunchAttestation(**fields)


def confined_receipt(**overrides) -> BoundaryReceipt:
    launch = confined_launch(**overrides)
    return BoundaryReceipt(planning=launch, execution=launch)


def confined_closure(**overrides):
    return closure(occurrence=occurrence(receipt=confined_receipt(**overrides)))
