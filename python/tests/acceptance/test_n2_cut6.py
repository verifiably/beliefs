"""N2 over cut 6's 22 frozen world-registry arms.

**The sabotage direction is audited against the commit that discharged cut 6.**
Cut 6's declarations name `world.py`, and slice 2 promoted that module to the
`science/world/` package. The declaration table and both runners are frozen, and
the design forbids recreating `world.py` as a shim: cut 6's committed sabotage
paths "remain historical evidence; no file is recreated to satisfy them". So the
sabotage half of the audit runs against the repository as it stood at
`CUT6_SOURCE_COMMIT` — the pre-promotion tree the 22 arms were written against,
package and suite together, because a sabotage of the historical package has to
be checked by the tests that shipped with it.

**Both halves of the pairing are run on the pinned tree.** "Exit 1 with the
sabotage applied" is only evidence when the same check exits 0 without it, on
the same tree — otherwise a check that has stopped passing for an unrelated
reason scores every arm that names it `sound`. The historical package is frozen
source. Its recorded `nodes` dependency is pinned with it; the interpreter and
the remaining installed dependencies are still live, so that failure mode is
live rather than theoretical.
`test_every_check_passes_against_the_unsabotaged_historical_package` runs each
declared check against an unmutated copy of the pinned package, under the pin,
and is what makes the `sound` verdicts below mean something.

**The live tree is still audited, by a third direction.**
`test_every_check_resolves_and_passes_without_the_sabotage` runs every declared
check against the working tree with no sabotage and no override, so a check that
is renamed away, or that stops passing because slice-2 work broke the behaviour
it names, still turns this module red.

**What the pin gives up, stated plainly.** Weakening a *current* check — leaving
its name and its green result in place while removing what it asserts — is no
longer caught here, because the mutation direction reads the historical copy of
that check. That is the one gap; the clean-run pairing above closes the other.
"""

from __future__ import annotations

import dataclasses
import io
import os
import shutil
import subprocess
import tarfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from itertools import count
from pathlib import Path

import pytest
import test_n2
from atoms.chain.model import RegisteredEntry
from atoms.core.errors import PreconditionRefused
from authority import FULL
from fixtures_cut6 import PINS
from n2_arms import (
    CLASS_NODE_BY_CONSTRUCTION,
    MIXED_BY_CONSTRUCTION,
    STALE_BY_CONSTRUCTION,
    UNCOLLECTED_BY_CONSTRUCTION,
    VACUOUS_BY_CONSTRUCTION,
    Arm,
    Sabotage,
    installed_nodes_root,
)
from n2_arms_cut6 import CUT6_ARMS
from profiles import WITH_BIOLOGY
from test_durable_families import chain_entries
from test_n2 import MalformedArm, audit, baseline

from beliefs import root
from beliefs.world import Fresh, WorldConfig, admission_digest, status_digest

WORKERS = 8
_COUNTER = count()

REPO_ROOT = Path(__file__).resolve().parents[3]

CUT6_SOURCE_COMMIT = "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e"
"""The last commit whose tree holds `python/src/science/world.py`.

Every cut-6 sabotage is a literal substring of a file in this tree. Moving the
pin forward is only correct when the arms are re-declared against a newer tree,
which is a new conformance cut rather than an edit to this one.
"""

CUT6_NODES_COMMIT = "5a00bba51df8bb2a06ec8a2fdc3c56ac8959e619"
"""The post-discharge `nodes` source recorded by cut 6's results."""

NODES_REPO = installed_nodes_root().parents[2]


def _historical_tree(destination: Path) -> Path:
    """Materialize the repository at `CUT6_SOURCE_COMMIT`, read-only evidence.

    `git archive` rather than a checkout or a worktree: nothing is written into
    the repository, the extraction is a plain tarball into a temporary
    directory, and the whole repository comes along so that a test resolving a
    repo-relative path finds the same layout it was written against.
    """
    archive = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", CUT6_SOURCE_COMMIT],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")
    nodes_destination = destination / ".nodes-source"
    nodes_archive = subprocess.run(
        ["git", "-C", str(NODES_REPO), "archive", CUT6_NODES_COMMIT],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    nodes_destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(nodes_archive)) as tar:
        tar.extractall(nodes_destination, filter="data")
    python_root = destination / "python"
    if not (python_root / "src" / "science" / "world.py").is_file():
        raise AssertionError(
            f"{CUT6_SOURCE_COMMIT} does not hold python/src/science/world.py, so it is not the tree "
            "cut 6's sabotages were declared against"
        )
    if not (nodes_destination / "python" / "src" / "nodes").is_dir():
        raise AssertionError(f"{CUT6_NODES_COMMIT} does not hold python/src/nodes")
    return python_root


def _historical_nodes(historical: Path) -> Path:
    return historical.parent / ".nodes-source" / "python" / "src" / "nodes"


def _historical_audit(arm: Arm, workspace: Path, historical: Path):
    shutil.copytree(_historical_nodes(historical), workspace / "nodes")
    return audit(arm, workspace)


@contextmanager
def _pinned(historical: Path):
    """Point the harness's package and test roots at the historical tree.

    `test_n2.PACKAGES["beliefs"]` is what `_sabotage` copies and mutates;
    `test_n2.TESTS` is where `_run_check` resolves node ids from. Both have to
    move together: a check taken from the live suite imports
    `beliefs.world.registry`, which the pre-promotion package does not have, and
    would exit 4 against it.
    """
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(test_n2.PACKAGES, "beliefs", historical / "src" / "science")
        patch.setattr(test_n2, "TESTS", historical / "tests")
        yield


@pytest.fixture(scope="session")
def historical_tree(tmp_path_factory) -> Path:
    """The pinned tree, extracted once and shared by every audit below."""
    return _historical_tree(tmp_path_factory.mktemp("cut6-source"))


# Declared here, immediately after `_historical_tree` and before anything that
# uses it, because the order is load-bearing: this test names the pin's one
# unrecoverable failure — a history that no longer holds the commit — and pytest
# runs it before the fixtures below, so the run reports *that* rather than a
# bare `git archive` error from inside a session fixture.
def test_the_pinned_cut6_source_commit_is_an_ancestor_of_the_working_tree():
    """The pin has to belong to this history, or the audit is against a stranger."""
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT6_SOURCE_COMMIT, "HEAD"],
        check=False,
    )
    assert completed.returncode == 0, (
        f"{CUT6_SOURCE_COMMIT} is not an ancestor of HEAD, so cut 6's sabotage direction would be "
        "auditing a tree this branch never had"
    )


def test_the_pinned_cut6_nodes_commit_is_an_ancestor_of_the_installed_tree():
    completed = subprocess.run(
        ["git", "-C", str(NODES_REPO), "merge-base", "--is-ancestor", CUT6_NODES_COMMIT, "HEAD"],
        check=False,
    )
    assert completed.returncode == 0, f"{CUT6_NODES_COMMIT} is not an ancestor of the installed nodes tree"


@pytest.fixture(scope="session")
def cut6_work_directory(work_directory) -> Path:
    configured = os.environ.get("SCIENCE_CUT6_ROOT")
    work = Path(configured) if configured else work_directory
    work.mkdir(parents=True, exist_ok=True)
    return work


@pytest.fixture()
def world_case(cut6_work_directory):
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = cut6_work_directory / f"world-{suffix}"
    corpus_root = cut6_work_directory / f"corpus-{suffix}"
    config = WorldConfig(world_root, "6" * 32, (corpus_root,))
    try:
        root.init_world_root(config, authority=FULL)
        assert {path.name for path in world_root.iterdir()} == {".#~chain", "world.yaml"}
        root.init_corpus_root(corpus_root, authority=FULL)
        root.open_corpus(corpus_root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
        assert not any((world_root / name).exists() for name in ("registry", "epochs", "rules"))
        before_admission = chain_entries(world_root)
        world = root.open_world(config, authority=FULL)
        admission = world.admit(corpus_root, provenance=Fresh())
        assert (world_root / "registry").is_dir()
        assert not any((world_root / name).exists() for name in ("epochs", "rules"))
        yield {
            "world": world,
            "world_root": world_root,
            "admission": admission,
            "before_admission": before_admission,
            "after_admission": chain_entries(world_root),
            "corpus_entries": chain_entries(corpus_root),
        }
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(world_root), ignore_errors=True)
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(corpus_root), ignore_errors=True)


def _registrations(entries):
    return tuple(entry for _, entry in entries if isinstance(entry, RegisteredEntry))


def test_world_initialization_recovers_between_genesis_and_mirror(cut6_work_directory, monkeypatch):
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = cut6_work_directory / f"crash-world-{suffix}"
    config = WorldConfig(world_root, "7" * 32, ())
    execute = root.DurableExecutor.execute
    raised = False

    def crash_once(self, plan):
        nonlocal raised
        if not raised:
            raised = True
            raise RuntimeError("crash before mirror transaction")
        return execute(self, plan)

    try:
        monkeypatch.setattr(root.DurableExecutor, "execute", crash_once)
        with pytest.raises(RuntimeError, match="crash before mirror"):
            root.init_world_root(config, authority=FULL)
        assert (world_root / ".#~chain").is_dir()
        assert not (world_root / "world.yaml").exists()
        monkeypatch.setattr(root.DurableExecutor, "execute", execute)
        root.init_world_root(config, authority=FULL)
        entries = chain_entries(world_root)
        root.init_world_root(config, authority=FULL)
        assert chain_entries(world_root) == entries
        with pytest.raises(PreconditionRefused):
            root.init_world_root(WorldConfig(world_root, "8" * 32, ()), authority=FULL)
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(world_root), ignore_errors=True)


def test_world_mirror_registration_names_world_yaml(world_case):
    (registration,) = _registrations(world_case["before_admission"])
    assert "world.yaml" in dict(registration.final)


def test_manifest_registration_names_corpus_yaml(world_case):
    (registration,) = _registrations(world_case["corpus_entries"])
    assert "corpus.yaml" in dict(registration.final)


def test_registry_registrations_name_each_record_path(world_case):
    added = world_case["after_admission"][len(world_case["before_admission"]) :]
    (registration,) = _registrations(added)
    admission = world_case["admission"]
    assert set(dict(registration.final)) == {f"registry/{admission_digest(admission)}.yaml"}

    before_status = chain_entries(world_case["world_root"])
    status = world_case["world"].retire(admission.corpus_id)
    (status_registration,) = _registrations(chain_entries(world_case["world_root"])[len(before_status) :])
    assert set(dict(status_registration.final)) == {f"registry/{status_digest(status)}.yaml"}


def _declared_checks() -> tuple[str, ...]:
    return tuple(dict.fromkeys(check for arm in CUT6_ARMS for check in arm.checks))


@pytest.fixture(scope="session")
def findings(tmp_path_factory, historical_tree) -> tuple:
    """The 22 arms, audited against the tree they were declared against.

    The pin is held only for the length of the audit, which is what keeps
    `test_every_check_resolves_and_passes_without_the_sabotage` pointed at the
    working tree.
    """
    root_path = tmp_path_factory.mktemp("n2-cut6")
    with _pinned(historical_tree), ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: _historical_audit(pair[1], root_path / f"arm{pair[0]}", historical_tree),
                enumerate(CUT6_ARMS),
            )
        )


@pytest.fixture(scope="session")
def historical_clean_runs(tmp_path_factory, historical_tree) -> tuple:
    """Every declared check, run against an **unmutated** copy of the pinned package.

    The other half of the pairing `audit` only ever performs one side of. `audit`
    concludes `sound` from "the check exited 1 with the sabotage applied", and on
    the live tree `baseline` supplies the matching "and exits 0 without it". Under
    the pin that pairing came apart: `baseline` runs the live package and the live
    suite, so nothing said the *historical* check still passes on the *historical*
    package. It is the interpreter and the installed dependencies that make this a
    real risk rather than a pedantic one — they are not pinned, and a check that
    has begun failing underneath frozen source would hand every arm naming it a
    free `sound`.

    A plain copy is used rather than `_sabotage`, because there is no arm here and
    nothing to mutate — the copy exists only so the child runs against the same
    `PYTHONPATH` shape the sabotaged runs use.
    """
    clean = tmp_path_factory.mktemp("cut6-clean") / "science"
    shutil.copytree(historical_tree / "src" / "science", clean)
    shutil.copytree(_historical_nodes(historical_tree), clean.parent / "nodes")
    with _pinned(historical_tree), ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda check: test_n2._run_check(check, clean), _declared_checks()))


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason + "\n" + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut6ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-6 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-6 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-6 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-6 sabotages no longer match exactly once:", findings, "stale")

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT6_ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"
                assert len(check.split("::")) >= 2, f"{arm.label}: {check}"

    def test_labeled_declarations_cite_their_frozen_specification(self):
        assert all(
            "specification §" in arm.asserts for arm in CUT6_ARMS if arm.row.startswith("labeled:")
        )

    def test_every_check_passes_against_the_unsabotaged_historical_package(self, historical_clean_runs):
        failed = [run for run in historical_clean_runs if run.returncode != test_n2.PASSED]
        assert not failed, (
            "these cut-6 checks do not pass against the pinned package with no sabotage applied, so "
            "every arm naming one of them scores `sound` on a check that was already red:\n"
            + "\n".join(f"  {run.check} exited {run.returncode}" for run in failed)
        )

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-6 check resolves and passes against the real package",
            sabotage=CUT6_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT6_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


class TestTheCut6InventoryIsExact:
    def test_exactly_one_declaration_exists_per_selected_or_labeled_bullet(self):
        assert len(CUT6_ARMS) == 22

    def test_declarations_match_the_frozen_row_histogram(self):
        assert Counter(arm.row for arm in CUT6_ARMS) == {
            "X4": 2,
            "X5": 1,
            "X6": 3,
            "W13": 8,
            "labeled:admission-idempotency": 1,
            "labeled:status-idempotency": 1,
            "labeled:initialization-idempotency": 1,
            "labeled:durable-mirror": 1,
            "labeled:durable-manifest": 1,
            "labeled:durable-registry": 1,
            "labeled:duplicate-carrier": 1,
            "labeled:manifest-malformed": 1,
        }

    def test_x7_and_slice_2_build_rows_are_absent(self):
        rows = {arm.row for arm in CUT6_ARMS}
        assert "X7" not in rows
        assert not any("build" in row for row in rows)


@pytest.mark.parametrize(
    ("arm", "verdict"),
    [
        (VACUOUS_BY_CONSTRUCTION, "vacuous"),
        (MIXED_BY_CONSTRUCTION, "mixed"),
        (UNCOLLECTED_BY_CONSTRUCTION, "uncollected"),
        (STALE_BY_CONSTRUCTION, "stale"),
    ],
)
def test_the_harness_preserves_each_malformed_verdict(tmp_path, arm, verdict):
    assert audit(arm, tmp_path / verdict).verdict == verdict


class TestTheAuditStillDiscriminatesUnderThePin:
    """The `sound` verdicts above are only worth their name if this run can withhold them.

    The two tests below are the pin's own version of the by-construction rows: a
    malformed arm, audited through exactly the configuration the 22 arms are
    audited through — historical package, historical suite, real subprocesses —
    and reported as malformed rather than scored `sound`. Without them the
    discrimination is something a person checked once by hand, which is the
    condition this whole harness exists to refuse.
    """

    def test_a_neutralized_cut6_sabotage_is_reported_rather_than_scored_sound(self, tmp_path, historical_tree):
        # The declaration is frozen, so the demonstration mutates a *copy* of it:
        # same module, same site, replacement equal to the original. The arm's
        # check then passes with the "sabotage" applied, which is vacuity — and
        # the point is that the pinned run says so instead of saying `sound`.
        arm = CUT6_ARMS[0]
        assert arm.sabotage.module == "world.py"
        neutralized = dataclasses.replace(
            arm,
            sabotage=Sabotage(
                module=arm.sabotage.module,
                before=arm.sabotage.before,
                after=arm.sabotage.before,
            ),
        )
        with _pinned(historical_tree):
            assert _historical_audit(arm, tmp_path / "real", historical_tree).verdict == "sound"
            assert _historical_audit(neutralized, tmp_path / "neutralized", historical_tree).verdict == "vacuous"

    def test_a_by_construction_malformed_arm_keeps_its_verdict_under_the_pin(self, tmp_path, historical_tree):
        # Its sabotage names `resolution.py`, which the pinned tree holds
        # unchanged, so this says the pin degrades none of the harness's
        # machinery — only which tree it reads.
        with _pinned(historical_tree):
            assert (
                _historical_audit(VACUOUS_BY_CONSTRUCTION, tmp_path / "vacuous", historical_tree).verdict == "vacuous"
            )


def test_the_harness_rejects_a_class_node(tmp_path):
    with pytest.raises(MalformedArm, match="one test function"):
        audit(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")
