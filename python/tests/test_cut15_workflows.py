import json

from fixtures_cut3 import seed_plan, seeded
from fixtures_cut15 import (
    SNAKEFILE_ONE_RULE_PIPELINE,
    SNAKEFILE_SCRATCH_KEYED_FANOUT,
    SNAKEFILE_TWO_FAMILIES,
    SNAKEFILE_TWO_TARGETS,
    SNAKEFILE_WILDCARD,
    SNAKEFILE_ZERO_JOB_FAMILY,
    fanout_width,
    run_workflow,
)

from beliefs.boundary import RunMinted
from beliefs.replay import CONFORMING, conformance
from beliefs.spec import Seeded
from beliefs.workflows import same_definition


def test_the_fixtures_determinism_is_pinned_not_folklore() -> None:
    assert fanout_width("base-a") == 1
    assert fanout_width("base-one") == 3
    assert fanout_width("base-a") == fanout_width("base-a")


def test_two_executions_of_one_recipe_differ_in_trace_and_job_ids(tmp_path) -> None:
    common = {
        "snakefile": SNAKEFILE_SCRATCH_KEYED_FANOUT,
        "targets": ("all",),
        "declared_outputs": ("outputs/a.done",),
        "family_streams": {"split": (), "fit": ("model-initialization",), "all": ()},
        "checkpoint_expanded_families": ("fit",),
        "nondeterminism": seeded(),
    }
    narrow = run_workflow(tmp_path / "narrow", scratch_base=tmp_path / "base-a", **common)
    wide = run_workflow(tmp_path / "wide", scratch_base=tmp_path / "base-one", **common)
    assert isinstance(narrow, RunMinted) and isinstance(wide, RunMinted)
    assert narrow.run.recipe.identity() == wide.run.recipe.identity()
    assert {job.job_id for job in narrow.run.occurrence.trace} != {
        job.job_id for job in wide.run.occurrence.trace
    }
    assert len(narrow.run.occurrence.trace) < len(wide.run.occurrence.trace)
    narrow_seeds = narrow.run.occurrence.realized_seeds.seeds
    wide_seeds = wide.run.occurrence.realized_seeds.seeds
    assert narrow_seeds != wide_seeds
    assert set(narrow_seeds) < set(wide_seeds)
    assert narrow.run.address() != wide.run.address()


def test_the_scratch_mapping_is_the_receipts_and_not_the_recipes(tmp_path) -> None:
    outcome = run_workflow(
        tmp_path / "narrow",
        scratch_base=tmp_path / "base-a",
        snakefile=SNAKEFILE_SCRATCH_KEYED_FANOUT,
        targets=("all",),
        declared_outputs=("outputs/a.done",),
        family_streams={"split": (), "fit": ("model-initialization",), "all": ()},
        checkpoint_expanded_families=("fit",),
        nondeterminism=seeded(),
    )
    assert isinstance(outcome, RunMinted)
    assert "base-a" in outcome.run.occurrence.receipt.execution.scratch_mapping
    assert "base-a" not in json.dumps(outcome.run.recipe._projection())


def test_runs_sharing_a_definition_are_the_same_pipeline(tmp_path) -> None:
    first = run_workflow(
        tmp_path / "1",
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/analysis.txt",),
        declared_outputs=("outputs/analysis.txt",),
    )
    second = run_workflow(
        tmp_path / "2",
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/report.txt",),
        declared_outputs=("outputs/report.txt",),
    )
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    grouped = same_definition([first.run, second.run])
    identity = first.run.recipe.workflow_definition.identity()
    assert list(grouped) == [identity]
    assert set(grouped[identity]) == {first.run.address(), second.run.address()}


def test_two_decompositions_of_one_computation_are_different_definitions(tmp_path) -> None:
    one_rule = run_workflow(
        tmp_path / "one",
        snakefile=SNAKEFILE_ONE_RULE_PIPELINE,
        targets=("outputs/report.txt",),
        declared_outputs=("outputs/report.txt",),
    )
    two_rules = run_workflow(
        tmp_path / "two",
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/report.txt",),
        declared_outputs=("outputs/report.txt",),
    )
    assert isinstance(one_rule, RunMinted) and isinstance(two_rules, RunMinted)
    assert one_rule.run.result.outputs == two_rules.run.result.outputs
    assert len(same_definition([one_rule.run, two_rules.run])) == 2


def test_two_targets_over_one_definition_are_two_recipes(tmp_path) -> None:
    analysis = run_workflow(
        tmp_path / "a",
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/analysis.txt",),
        declared_outputs=("outputs/analysis.txt",),
    )
    report = run_workflow(
        tmp_path / "b",
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/report.txt",),
        declared_outputs=("outputs/analysis.txt",),
    )
    assert isinstance(analysis, RunMinted) and isinstance(report, RunMinted)
    assert analysis.run.recipe.workflow_definition == report.run.recipe.workflow_definition
    assert analysis.run.recipe.identity() != report.run.recipe.identity()


def test_a_manifest_is_built_across_outputs_of_several_rules(tmp_path) -> None:
    outcome = run_workflow(
        tmp_path,
        snakefile=SNAKEFILE_TWO_TARGETS,
        targets=("outputs/report.txt",),
        declared_outputs=("outputs/analysis.txt", "outputs/report.txt"),
    )
    assert isinstance(outcome, RunMinted)
    assert {name for name, _ in outcome.run.result.outputs} == {
        "outputs/analysis.txt",
        "outputs/report.txt",
    }


def test_a_wildcard_run_records_one_seed_per_instance(tmp_path) -> None:
    outcome = run_workflow(
        tmp_path,
        snakefile=SNAKEFILE_WILDCARD,
        targets=("all",),
        declared_outputs=("outputs/a.txt", "outputs/b.txt"),
        family_streams={"fit": ("model-initialization",), "all": ()},
        nondeterminism=seeded(),
    )
    assert isinstance(outcome, RunMinted)
    assert len(outcome.run.occurrence.realized_seeds.seeds) == 2
    assert conformance(outcome.run) == CONFORMING


def test_the_family_rule_binds_for_a_production_recipe_with_no_spec(tmp_path) -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    outcome = run_workflow(
        tmp_path,
        snakefile=SNAKEFILE_TWO_FAMILIES,
        targets=("all",),
        declared_outputs=("outputs/a.txt", "outputs/b.txt"),
        family_streams={
            "a": ("model-initialization",),
            "b": ("resample-draws",),
            "all": (),
        },
        nondeterminism=Seeded(plan=plan),
    )
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.spec_identity is None
    assert conformance(outcome.run) == CONFORMING


def test_a_declared_family_producing_zero_jobs_is_non_conforming(tmp_path) -> None:
    plan = seed_plan(
        streams=("model-initialization", "resample-draws"),
        roots={"r": 11},
        stream_roots={"model-initialization": "r", "resample-draws": "r"},
    )
    outcome = run_workflow(
        tmp_path,
        snakefile=SNAKEFILE_ZERO_JOB_FAMILY,
        targets=("outputs/used.txt",),
        declared_outputs=("outputs/used.txt",),
        family_streams={
            "used": ("model-initialization",),
            "unused": ("resample-draws",),
        },
        nondeterminism=Seeded(plan=plan),
    )
    assert isinstance(outcome, RunMinted)
    assert conformance(outcome.run).startswith("non-conforming")


def test_the_invocation_does_not_enumerate_jobs_a_target_implies(tmp_path) -> None:
    outcome = run_workflow(
        tmp_path,
        snakefile=SNAKEFILE_WILDCARD,
        targets=("all",),
        declared_outputs=("outputs/a.txt", "outputs/b.txt"),
        family_streams={"fit": ("model-initialization",), "all": ()},
        nondeterminism=seeded(),
    )
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.invocation.targets == ("all",)
    assert not hasattr(outcome.run.recipe.invocation, "jobs")
    assert len(outcome.run.occurrence.planned) > len(outcome.run.recipe.invocation.targets)
