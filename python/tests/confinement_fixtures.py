"""Confined-receipt value builders for the portable suite."""

import importlib.util
from pathlib import Path

from fixtures_cut3 import closure, occurrence

from beliefs.recipe import (
    CAPABILITIES,
    NAMESPACES,
    BoundaryReceipt,
    InstanceAttestation,
    LaunchAttestation,
    mount_plan_identity,
)

# `conftest` is not a globally unique module name: an acceptance-scoped
# collection (`tests/acceptance/...`) also loads `tests/acceptance/conftest.py`
# under the same bare name, and whichever conftest pytest loads last wins the
# `sys.modules['conftest']` slot — leaving a plain `from conftest import ...`
# here dependent on collection scope. Load this file's own sibling by path so
# `MOUNTS` and friends always come from `tests/conftest.py`, not whichever
# module last claimed the name.
_SPEC = importlib.util.spec_from_file_location("_confinement_fixtures_conftest", Path(__file__).with_name("conftest.py"))
assert _SPEC is not None and _SPEC.loader is not None
_conftest = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_conftest)
MOUNTS = _conftest.CONFINED_MOUNTS
ENV_IDENTITY = _conftest.ENVIRONMENT
RENDERED_ENVIRONMENT = _conftest.RENDERED_ENVIRONMENT
SANDBOX_MOUNTS = _conftest.SANDBOX_MOUNTS


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
