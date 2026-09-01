"""Confined-receipt value builders for the portable suite."""

from fixtures_cut3 import closure, occurrence

from beliefs.recipe import (
    CAPABILITIES,
    NAMESPACES,
    BoundaryReceipt,
    InstanceAttestation,
    mount_plan_identity,
)

ENV_IDENTITY = "sha256:" + "ab" * 32

MOUNTS = (
    ("/", "root", "ro"),
    ("/lib64/ld-linux-x86-64.so.2", "loader", "ro"),
    ("/science/env", "env", "ro"),
    ("/science/bundle", "bundle", "ro"),
    ("/science/out", "output", "rw"),
    ("/science/out/inputs", "inputs", "ro"),
    ("/dev/null", "device", "rw"),
    ("/dev/urandom", "device", "rw"),
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


def confined_receipt(**overrides) -> BoundaryReceipt:
    fields = {
        "scratch_mapping": "/host/scratch/run-1",
        "argv": ("/science/env/venv/bin/python", "-m", "snakemake"),
        "rendered_config": (("seed_model_initialization", "7"),),
        "capabilities": CAPABILITIES,
        "instance": instance(),
        "rendered_environment": (("env:PATH", "value", "/science/env/venv/bin"), ("hostname", "value", "science")),
        "mounts": (("/science/bundle", "/host/scratch/run-1/bundle"), ("/science/out", "/host/scratch/run-1/out")),
    }
    fields.update(overrides)
    return BoundaryReceipt(**fields)


def confined_closure(**overrides):
    return closure(occurrence=occurrence(receipt=confined_receipt(**overrides)))
