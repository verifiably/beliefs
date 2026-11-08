"""The confined tests: every check that executes under confined-v1.

They need the confinement gate and no durable root. One snapshot serves the
module (`shared_scratch`), so the closure is materialized once."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from fixtures_cut3 import (
    DATA_ADDRESS,
    MEMORY_PORT,
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_TREE,
    TREE_MEMBERS,
    interp,
    lay_tree,
    replay_of,
    run_assessment,
    run_production,
    spec_draft,
    spec_rules,
)
from profiles import pins_for
from test_assess import observations_for
from test_belief import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PROFILE
from test_verify import verification_of

import beliefs.boundary as boundary_module
from beliefs.admission import AdmissionRefused, Admitted, admit
from beliefs.assess import build_assessment, run_record
from beliefs.belief import Availability, Belief, NoBelief, Records, SuppliedContext, evaluate
from beliefs.boundary import RunMinted, RunRefused
from beliefs.closure import RetractionEnumeration
from beliefs.dataset import dataset_address
from beliefs.identity import v1
from beliefs.lineage import LineageSnapshot
from beliefs.policy import PolicyBinding
from beliefs.recipe import CAPABILITIES, CONFINED_POLICY, MINIMAL_POLICY, NAMESPACES, RecipeInput
from beliefs.record import AssessmentValue
from beliefs.replay import CONFORMING, EquivalenceImplementation, conformance, derive_scope
from beliefs.spec import freeze
from beliefs.verify import AssessmentVerification, admission_record

pytestmark = pytest.mark.usefixtures("confined_host")

SNAKEFILE_UNDECLARED_READ = SNAKEFILE_DETERMINISTIC.replace(
    "        text = pathlib.Path(input[0]).read_text()",
    '        pathlib.Path("/etc/passwd").read_text()\n        text = pathlib.Path(input[0]).read_text()',
)
SNAKEFILE_WRITE_OUTSIDE = SNAKEFILE_DETERMINISTIC.replace(
    "        text = pathlib.Path(input[0]).read_text()",
    '        pathlib.Path("/escaped.txt").write_text("x")\n        text = pathlib.Path(input[0]).read_text()',
)
SNAKEFILE_TREE_WRITE_OUTSIDE = SNAKEFILE_TREE.replace(
    '        staged = pathlib.Path("inputs/data")',
    '        pathlib.Path("/escaped.txt").write_text("x")\n        staged = pathlib.Path("inputs/data")',
)
SNAKEFILE_CORES_SENSITIVE = """\
import json, pathlib
from beliefs.seeds import bind, record_digest_of

seed = bind(config)

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        value = seed(rule, wildcards, "model-initialization")
        if workflow.cores != 1:
            claim = next(pathlib.Path(".seeds").glob("*.json"))
            record = json.loads(claim.read_text())
            claim.unlink()
            record["seed"] = value + 1
            (claim.parent / f"{record_digest_of(record)}.json").write_text(
                json.dumps(record, sort_keys=True, separators=(",", ":")))
        pathlib.Path(output[0]).write_text(pathlib.Path(input[0]).read_text().upper())
"""


def snakefile_connecting_to(port: int) -> str:
    return SNAKEFILE_DETERMINISTIC.replace(
        "        text = pathlib.Path(input[0]).read_text()",
        f'        __import__("socket").create_connection(("127.0.0.1", {port}), timeout=2).close()\n'
        "        text = pathlib.Path(input[0]).read_text()",
    )


def snakefile_importing_from(directory: Path) -> str:
    return SNAKEFILE_DETERMINISTIC.replace(
        "import pathlib, random",
        f'import sys; sys.path.insert(0, "{directory}"); import secret\nimport pathlib, random',
    )


@pytest.fixture(scope="module")
def shared_scratch(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("confined-scratch")


def confined(tmp_path: Path, shared_scratch: Path, **kwargs):
    return run_assessment(
        tmp_path, port=MEMORY_PORT, boundary_policy=CONFINED_POLICY, scratch_base=shared_scratch, **kwargs
    )


def minimal(tmp_path: Path, **kwargs):
    return run_assessment(tmp_path, port=MEMORY_PORT, boundary_policy=MINIMAL_POLICY, **kwargs)


def test_a_confined_run_attests_both_launches_over_one_snapshot(tmp_path):
    outcome = run_production(
        tmp_path,
        port=MEMORY_PORT,
        boundary_policy=CONFINED_POLICY,
    )
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    assert receipt.planning.instance is not None and receipt.execution.instance is not None
    assert receipt.planning.instance.environment_identity == receipt.execution.instance.environment_identity
    assert receipt.planning.instance.mount_plan_identity == receipt.execution.instance.mount_plan_identity
    assert receipt.planning.mounts != receipt.execution.mounts
    assert receipt.confined is True


def test_each_confined_launch_executes_exactly_one_engine_argv(tmp_path):
    outcome = run_production(
        tmp_path,
        port=MEMORY_PORT,
        boundary_policy=CONFINED_POLICY,
    )
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    for launch in (receipt.planning, receipt.execution):
        assert launch.argv.count("-m") == 1 and "snakemake" in launch.argv
    assert "--dryrun" in receipt.planning.argv
    assert "--dryrun" not in receipt.execution.argv


def confined_pair(tmp_path: Path, shared_scratch: Path, *, snakefile=SNAKEFILE_DETERMINISTIC, replay_cores=1):
    original = confined(tmp_path / "original", shared_scratch, snakefile=snakefile)
    assert isinstance(original, RunMinted), original
    replayed = replay_of(
        original,
        tmp_path / "replayed",
        port=MEMORY_PORT,
        snakefile=snakefile,
        scratch_base=shared_scratch,
        cores=replay_cores,
    )
    assert isinstance(replayed, RunMinted), replayed
    return original, replayed


def belief_over(minted: RunMinted, verification) -> Belief | NoBelief:
    spec = freeze(spec_draft(), held_rules=spec_rules())
    assessment = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    assert isinstance(assessment, AssessmentValue), assessment
    run_value = run_record(minted.run)
    observed = tuple(dataset_address(entry.dataset) for entry in run_value.inputs if entry.role == "observes")
    records = Records(
        claims={},
        assessments=(assessment,),
        runs={assessment.run: run_value},
        source_assertions=(),
        verifications=(verification,) if verification is not None else (),
    )
    availability = Availability(
        observations=observations_for(run_value),
        implementations={BELIEF_V1.identity: BELIEF_V1},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )
    context = SuppliedContext(
        snapshot=LineageSnapshot(roots=tuple(root for root in observed if root is not None), bases={}, producers={}),
        producer_snapshot_identity="snap-1",
        node_corpus={assessment.identity(): ("c1",)},
        pins={"c1": pins_for(PROFILE)},
    )
    outcome = evaluate(
        proposition=assessment.proposition,
        records=records,
        availability=availability,
        context=context,
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        profile=PROFILE,
    )
    assert isinstance(outcome, (Belief, NoBelief)), outcome
    return outcome


def admission_of(minted: RunMinted, verification):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    assessment = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    assert isinstance(assessment, AssessmentValue), assessment
    run_value = run_record(minted.run)
    return admit(assessment, run_value, observations_for(run_value), (verification,))


def test_a_bundled_file_edited_after_capture_yields_no_run_and_the_engine_never_starts(
    tmp_path, shared_scratch, monkeypatch
):
    real_capture = boundary_module.capture_bundle
    real_launch = boundary_module.launch_confined
    launched: list[bool] = []

    def capture_then_edit(code_roots, bundle_dir):
        identity = real_capture(code_roots, bundle_dir)
        (bundle_dir / "code" / "helper.py").write_text("VALUE = 2\n")
        return identity

    def spy(**kwargs):
        launched.append(True)
        return real_launch(**kwargs)

    monkeypatch.setattr(boundary_module, "capture_bundle", capture_then_edit)
    monkeypatch.setattr(boundary_module, "launch_confined", spy)
    outcome = confined(tmp_path, shared_scratch)
    assert isinstance(outcome, RunRefused) and outcome.reason == "closure-mutated", outcome
    assert outcome.intent is not None and outcome.report is not None
    assert launched == []


def test_a_bundled_file_edited_after_exit_yields_no_run(tmp_path, shared_scratch, monkeypatch):
    real_launch = boundary_module.launch_confined
    launches = 0

    def launch_then_edit(*, plan, environment, inner_argv, captured):
        nonlocal launches
        result = real_launch(plan=plan, environment=environment, inner_argv=inner_argv, captured=captured)
        launches += 1
        if launches == 2:
            bundle = Path(dict(plan.host_mapping())["/science/bundle"])
            (bundle / "code" / "helper.py").write_text("VALUE = 3\n")
        return result

    monkeypatch.setattr(boundary_module, "launch_confined", launch_then_edit)
    outcome = confined(tmp_path, shared_scratch)
    assert isinstance(outcome, RunRefused) and outcome.reason == "closure-mutated", outcome


def test_an_undeclared_file_read_fails_closed(tmp_path, shared_scratch):
    assert isinstance(minimal(tmp_path / "host", snakefile=SNAKEFILE_UNDECLARED_READ), RunMinted)
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=SNAKEFILE_UNDECLARED_READ)
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "FileNotFoundError" in outcome.detail or "No such file" in outcome.detail


def test_an_undeclared_network_connection_fails_closed(tmp_path, shared_scratch):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(4)
    port = listener.getsockname()[1]
    try:
        assert isinstance(minimal(tmp_path / "host", snakefile=snakefile_connecting_to(port)), RunMinted)
        outcome = confined(tmp_path / "confined", shared_scratch, snakefile=snakefile_connecting_to(port))
    finally:
        listener.close()
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "ConnectionRefused" in outcome.detail or "Errno 111" in outcome.detail


def test_the_receipt_names_the_capabilities_observed_in_force(tmp_path, shared_scratch):
    outcome = confined(tmp_path / "confined", shared_scratch)
    assert isinstance(outcome, RunMinted), outcome
    receipt = outcome.run.occurrence.receipt
    execution = receipt.execution
    assert receipt.confined and execution.capabilities == CAPABILITIES
    assert execution.instance is not None
    assert tuple(sorted(execution.instance.namespaces)) == NAMESPACES
    assert execution.instance.environment_identity == outcome.run.recipe.environment.identity()
    assert all(part.startswith("/science/") or not part.startswith("/") for part in execution.argv)
    assert execution.mounts is not None and execution.rendered_environment is not None
    assert dict(execution.mounts)["/science/bundle"].startswith(str(shared_scratch))
    assert not any(str(shared_scratch) in value for _, _, value in execution.rendered_environment)
    plain = minimal(tmp_path / "host")
    assert (
        isinstance(plain, RunMinted)
        and plain.run.occurrence.receipt.execution.capabilities == ()
        and plain.run.occurrence.receipt.execution.instance is None
    )


def test_a_minimal_run_is_valid_and_a_minimal_pair_stays_same_environment(tmp_path):
    original = minimal(tmp_path / "original")
    assert isinstance(original, RunMinted)
    replayed = replay_of(original, tmp_path / "replayed", port=MEMORY_PORT)
    assert isinstance(replayed, RunMinted)
    assert conformance(original.run) == CONFORMING and conformance(replayed.run) == CONFORMING
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"


def test_a_confined_pair_derives_clean_environment(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert derive_scope(original.run, replayed.run, certification=None) == "clean-environment"


def test_end_to_end_a_passing_clean_environment_verification_admits_and_yields_belief(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    verification = verification_of((original, replayed))
    assert isinstance(verification, AssessmentVerification)
    assert verification.scope == "clean-environment" and verification.verdict == "passed"
    record = admission_record(verification)
    assert isinstance(admission_of(original, record), Admitted)
    assert isinstance(belief_over(original, record), Belief)


def test_an_inconclusive_verification_admits_nothing(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    unreadable = EquivalenceImplementation(
        identity="impl-eq-1", evaluate=lambda left, right: "inconclusive", fixtures=()
    )
    verification = verification_of((original, replayed), held_rules={"impl-eq-1": unreadable})
    assert isinstance(verification, AssessmentVerification)
    assert verification.verdict == "inconclusive" and verification.scope == "clean-environment"
    verdict = admission_of(original, admission_record(verification))
    assert isinstance(verdict, AdmissionRefused) and verdict.reason.startswith("not-admitted-verification-state")


def test_an_import_outside_the_closure_is_refused_under_confinement_and_minted_under_minimal(tmp_path, shared_scratch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("VALUE = 42\n")
    snakefile = snakefile_importing_from(outside)
    assert isinstance(minimal(tmp_path / "host", snakefile=snakefile), RunMinted)
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=snakefile)
    assert isinstance(outcome, RunRefused), outcome  # a refusal, and nothing about its diagnostic


def test_a_not_certified_pair_admits_nothing(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch, snakefile=SNAKEFILE_CORES_SENSITIVE, replay_cores=2)
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert original.run.occurrence.receipt.confined and replayed.run.occurrence.receipt.confined
    assert original.run.result == replayed.run.result
    assert conformance(original.run) == CONFORMING and conformance(replayed.run) != CONFORMING
    verification = verification_of((original, replayed))
    assert isinstance(verification, AssessmentVerification)
    assert verification.scope == "not-certified" and verification.verdict == "passed"
    record = admission_record(verification)
    assert isinstance(admission_of(original, record), AdmissionRefused)
    assert belief_over(original, record) == belief_over(original, None)
    assert isinstance(belief_over(original, record), NoBelief)


def test_a_write_outside_the_output_root_fails_closed(tmp_path, shared_scratch):
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=SNAKEFILE_WRITE_OUTSIDE)
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "Read-only file system" in outcome.detail or "EROFS" in outcome.detail


def test_two_differently_mounted_scratch_roots_yield_equal_recipes_and_clean_environment(tmp_path, shared_scratch):
    other_scratch = tmp_path / "other-mount"
    original = confined(tmp_path / "original", shared_scratch)
    assert isinstance(original, RunMinted), original
    replayed = replay_of(original, tmp_path / "replayed", port=MEMORY_PORT, scratch_base=other_scratch)
    assert isinstance(replayed, RunMinted), replayed
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert (
        original.run.occurrence.receipt.execution.scratch_mapping
        != replayed.run.occurrence.receipt.execution.scratch_mapping
    )
    assert original.run.occurrence.receipt.execution.argv == replayed.run.occurrence.receipt.execution.argv
    assert derive_scope(original.run, replayed.run, certification=None) == "clean-environment"
    assert str(other_scratch) not in v1.encode(replayed.run.recipe._projection()).decode("utf-8")


def confined_tree_production(tmp_path: Path, shared_scratch: Path, *, snakefile=SNAKEFILE_TREE, output_dir=None):
    held = lay_tree(tmp_path / "store", TREE_MEMBERS)
    outcome = run_production(
        tmp_path,
        port=MEMORY_PORT,
        boundary_policy=CONFINED_POLICY,
        snakefile=snakefile,
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content=held.digest),),
        held_inputs={DATA_ADDRESS: {"data": held}},
        scratch_base=shared_scratch,
        output_dir=output_dir,
    )
    return held, outcome


def test_a_confined_tree_input_runs_and_replays_to_the_same_outputs(tmp_path, shared_scratch):
    output_dir = tmp_path / "exported"
    output_dir.mkdir()
    held, original = confined_tree_production(tmp_path / "original", shared_scratch, output_dir=output_dir)
    assert isinstance(original, RunMinted), original
    replayed = replay_of(
        original,
        tmp_path / "replayed",
        port=MEMORY_PORT,
        snakefile=SNAKEFILE_TREE,
        held_inputs={DATA_ADDRESS: {"data": lay_tree(tmp_path / "another-store", TREE_MEMBERS)}},
        scratch_base=shared_scratch,
    )
    assert isinstance(replayed, RunMinted), replayed
    assert replayed.run.result == original.run.result
    for minted in (original, replayed):
        assert minted.run.occurrence.receipt.confined
        assert minted.run.recipe.inputs[0].content == held.digest
        assert held.digest.startswith("sha256-tree:")
        scratch = Path(minted.run.occurrence.receipt.execution.scratch_mapping)
        assert (scratch / "out" / "inputs").is_dir()
        assert not (scratch / "out" / "inputs" / "data").exists()
        for name, digest in minted.run.result.outputs:
            assert boundary_module._digest(scratch / "out" / name) == digest
    assert original.run.result.outputs
    for name, digest in original.run.result.outputs:
        assert boundary_module._digest(output_dir / name) == digest
    assert (output_dir / "outputs" / "result.txt").read_text() == "ALPHA\n|BETA\n"


def test_a_confined_tree_run_that_fails_closed_leaves_no_staged_tree(tmp_path, shared_scratch):
    before = set(shared_scratch.iterdir())
    _, outcome = confined_tree_production(tmp_path, shared_scratch, snakefile=SNAKEFILE_TREE_WRITE_OUTSIDE)
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "Read-only file system" in outcome.detail or "EROFS" in outcome.detail
    (scratch,) = set(shared_scratch.iterdir()) - before - {shared_scratch / "environments"}
    assert (scratch / "out" / "inputs").is_dir()
    assert not (scratch / "out" / "inputs" / "data").exists()
