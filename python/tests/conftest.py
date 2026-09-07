"""Shared fixtures.

The repository-relative paths below are the *only* place a test resolves one.
Nothing in `science` locates a contract for itself: the belief policy's §2.3
refuses an implicit selector on the ground that it would make belief follow the
checkout, and a contract loader that guessed its own path would have the same
defect one layer down.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from confinement_constants import CONFINED_MOUNTS, ENVIRONMENT, RENDERED_ENVIRONMENT, SANDBOX_MOUNTS

from beliefs.recipe import (
    NAMESPACES,
    REQUIRED_FOR_CLEAN_ENVIRONMENT,
    InstanceAttestation,
    LaunchAttestation,
    mount_plan_identity,
)

OTHER_ENVIRONMENT = "sha256:" + "cd" * 32
CONFINED_NAMESPACES = NAMESPACES

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def confined_launch():
    def build(
        *,
        capabilities=REQUIRED_FOR_CLEAN_ENVIRONMENT,
        environment_identity=ENVIRONMENT,
        scratch_mapping="/science/out",
        argv=("snakemake",),
    ):
        instance = InstanceAttestation(
            namespaces=CONFINED_NAMESPACES,
            mounts=CONFINED_MOUNTS,
            mount_plan_identity=mount_plan_identity(CONFINED_MOUNTS),
            environment_identity=environment_identity,
        )
        return LaunchAttestation(
            scratch_mapping=scratch_mapping,
            argv=argv,
            rendered_config=(),
            capabilities=tuple(capabilities),
            instance=instance,
            rendered_environment=RENDERED_ENVIRONMENT,
            mounts=SANDBOX_MOUNTS,
        )

    return build


@pytest.fixture()
def certified_work() -> "Iterator[Path]":
    """A fresh directory on the selected certified volume, removed afterwards.

    The lifecycle-wrapper tests run the real engine, whose durability
    allowlist requires an exact configuration tuple. Cut 10 supplies its run
    root; ordinary tests use the repository-relative fallback. Every root a
    test creates lives inside this directory, which keeps the derived metadata
    siblings inside it too.
    """
    import shutil
    import tempfile

    configured = (
        os.environ.get("SCIENCE_CUT10_ROOT")
        or os.environ.get("SCIENCE_CUT12_ROOT")
        or os.environ.get("SCIENCE_CUT13_ROOT")
    )
    base = Path(configured) if configured else REPO_ROOT / ".lifecycle-wrappers-test"
    base.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="t-", dir=base))
    yield work
    shutil.rmtree(work, ignore_errors=True)


@pytest.fixture(scope="session")
def base_contract_path() -> Path:
    return REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return REPO_ROOT / "fixtures"


@pytest.fixture(scope="session")
def testing_contract_path() -> Path:
    return REPO_ROOT / "fixtures" / "contracts" / "testing.yaml"


@pytest.fixture(scope="session")
def parity_fixture_path() -> Path:
    return REPO_ROOT / "fixtures" / "claim-identity-v1.json"


@pytest.fixture(scope="session")
def base_contract(base_contract_path):
    from beliefs.contract import load_base_contract

    return load_base_contract(base_contract_path)


@pytest.fixture()
def testing_document(testing_contract_path) -> dict:
    import yaml

    return yaml.safe_load(testing_contract_path.read_text(encoding="utf-8"))
