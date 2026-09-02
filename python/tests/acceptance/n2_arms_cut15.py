"""Cut 15: 17 selected + 8 labeled = 25 units, carried by 30 arms."""

from n2_arms import Arm, Sabotage

_RECIPE, _BOUNDARY = "recipe.py", "boundary.py"
_REPLAY, _RUNRECORD, _SEEDS = "replay.py", "runrecord.py", "seeds.py"
_VERIFY, _LINEAGE = "verify.py", "lineage.py"

_W = "test_cut15_workflows.py"
_R = "test_replay.py"
_B = "test_boundary.py"
_REC = "test_recipe.py"
_RUN = "test_runrecord.py"

CUT15_ARMS = (
    Arm(
        row="R2a",
        asserts="two executions of one recipe keep equal recipe identities and distinct addresses",
        sabotage=Sabotage(
            module=_RECIPE,
            before='                "occurrence": _occurrence_projection(self.occurrence),\n',
            after="",
        ),
        checks=(f"{_W}::test_two_executions_of_one_recipe_differ_in_trace_and_job_ids",),
    ),
    Arm(
        row="R2b",
        asserts="the family-stream declaration is a definition and recipe identity member",
        sabotage=Sabotage(
            module=_RECIPE,
            before='            "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},\n',
            after="",
        ),
        checks=(f"{_REC}::test_changing_a_family_declaration_moves_the_recipe_identity",),
    ),
    Arm(
        row="R2c",
        asserts="the checkpoint-expanded declaration is a definition identity member",
        sabotage=Sabotage(
            module=_RECIPE,
            before='            "checkpoint_expanded_families": sorted(self.checkpoint_expanded_families),\n',
            after="",
        ),
        checks=("test_adapter.py::test_declaring_a_checkpoint_expanded_family_moves_the_identity",),
    ),
    Arm(
        row="R16a",
        asserts="a job realizing a stream its family does not declare is non-conforming",
        sabotage=Sabotage(module=_REPLAY, before="        if set(claims) != declared:", after="        if False:"),
        checks=(f"{_R}::test_a_job_realizing_a_stream_its_family_does_not_declare_is_non_conforming",),
    ),
    Arm(
        row="R16b",
        asserts="a job omitting a stream its family declares is non-conforming",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        if set(claims) != declared:",
            after="        if set(claims) - declared:",
        ),
        checks=(f"{_R}::test_a_job_omitting_a_stream_its_family_declares_is_non_conforming",),
    ),
    Arm(
        row="R16c",
        asserts="two streams in one job are both keyed and both checked",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        claims = realized.get(key, {})",
            after="        claims = dict(list(realized.get(key, {}).items())[:1])",
        ),
        checks=(f"{_R}::test_two_streams_in_one_job_are_both_checked",),
    ),
    Arm(
        row="R16d",
        asserts="conformance reads each job's own family, so over-claiming does not satisfy it",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after="        declared = {s for streams in snapshot.family_streams.values() for s in streams}",
        ),
        checks=(f"{_R}::test_an_over_claiming_record_does_not_conform",),
    ),
    Arm(
        row="R16e",
        asserts="a wildcard instance is judged against its family",
        sabotage=Sabotage(
            module=_RECIPE,
            before="        return job_key(self.rule, self.wildcards)",
            after="        return job_key(self.rule, ())",
        ),
        checks=(f"{_R}::test_a_wildcard_instance_is_judged_against_its_family",),
    ),
    Arm(
        row="R16f",
        asserts="the both-directions equality is refused at the boundary, before any effect",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before="    if reason := definition_agrees_with_plan(definition.snapshot(), plan):",
            after="    if False:",
        ),
        checks=(f"{_B}::test_a_definition_disagreement_refuses_before_a_planning_effect",),
    ),
    Arm(
        row="R16g",
        asserts="the same predicate states the disagreement about a constructed closure",
        sabotage=Sabotage(
            module=_REPLAY,
            before="    if reason := definition_agrees_with_plan(snapshot, plan):",
            after="    if False:",
        ),
        checks=(f"{_R}::test_a_constructed_closure_whose_definition_disagrees_is_non_conforming",),
    ),
    Arm(
        row="R16h",
        asserts="the family rule reads the recipe, so it binds for a production shape with no spec",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after=(
                "        declared = set(snapshot.family_streams.get(job.rule, ())) "
                "if run.recipe.spec_identity else set()"
            ),
        ),
        checks=(f"{_W}::test_the_family_rule_binds_for_a_production_recipe_with_no_spec",),
    ),
    Arm(
        row="R16i",
        asserts="execution coverage: a declared stream no executed job realized",
        sabotage=Sabotage(
            module=_REPLAY,
            before="    if union != expected_streams:",
            after="    if union - expected_streams:",
        ),
        checks=(f"{_W}::test_a_declared_family_producing_zero_jobs_is_non_conforming",),
    ),
    Arm(
        row="R16j",
        asserts="trace membership, with the checkpoint-expanded admission",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        if job.job_key() not in planned_keys and job.rule not in expanded:",
            after="        if False:",
        ),
        checks=(
            f"{_R}::test_an_executed_job_outside_the_plan_is_non_conforming",
            f"{_R}::test_an_unexpanded_family_gets_no_checkpoint_admission",
        ),
    ),
    Arm(
        row="R16k",
        asserts="target satisfaction over the resolved target job keys",
        sabotage=Sabotage(
            module=_REPLAY,
            before="    if missing := sorted(set(run.occurrence.target_keys) - executed):",
            after="    if False:",
        ),
        checks=(f"{_R}::test_a_resolved_target_missing_from_the_trace_is_non_conforming",),
    ),
    Arm(
        row="R16l",
        asserts="a legitimately different job set is conforming, and its difference is reported",
        sabotage=Sabotage(
            module=_VERIFY,
            before="    if left == right:\n        return ()\n",
            after="    return ()\n",
        ),
        checks=("test_verify.py::test_a_data_dependent_replay_over_different_inputs_is_conforming",),
    ),
    Arm(
        row="R16m",
        asserts="a job-set difference contributes to no scope",
        sabotage=Sabotage(
            module=_REPLAY,
            before="    if original.recipe.identity() == replayed.recipe.identity():",
            after=(
                "    if original.recipe.identity() == replayed.recipe.identity() and "
                "{j.job_key() for j in original.occurrence.trace} == "
                "{j.job_key() for j in replayed.occurrence.trace}:"
            ),
        ),
        checks=("test_verify.py::test_a_differing_job_set_alone_costs_no_scope",),
    ),
    Arm(
        row="R20a",
        asserts="the obligation is per family, and no global per-job obligation is spellable",
        sabotage=Sabotage(
            module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after="        declared = set()",
        ),
        checks=(f"{_R}::test_different_families_realizing_different_streams_conforms",),
    ),
    Arm(
        row="R20b",
        asserts="two decompositions of one computation are two definitions",
        sabotage=Sabotage(module=_RECIPE, before='            "snakefile": self.snakefile_digest,\n', after=""),
        checks=(f"{_W}::test_two_decompositions_of_one_computation_are_different_definitions",),
    ),
    Arm(
        row="R21a",
        asserts="two targets over one definition are two recipes",
        sabotage=Sabotage(
            module=_RECIPE,
            before='                "targets": list(self.invocation.targets),',
            after='                "targets": [],',
        ),
        checks=(f"{_W}::test_two_targets_over_one_definition_are_two_recipes",),
    ),
    Arm(
        row="R21b",
        asserts="the manifest is constructed across the outputs of several rules",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs))"
            ),
            after=(
                "    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) "
                "for name in declared_outputs[:1]))"
            ),
        ),
        checks=(f"{_W}::test_a_manifest_is_built_across_outputs_of_several_rules",),
    ),
    Arm(
        row="R21c",
        asserts="invocation enumerates no jobs a target implies",
        sabotage=Sabotage(
            module=_RECIPE,
            before="    declared_outputs: tuple[str, ...]\n",
            after="    declared_outputs: tuple[str, ...]\n    jobs: tuple[str, ...] = ()\n",
        ),
        checks=(f"{_W}::test_the_invocation_does_not_enumerate_jobs_a_target_implies",),
    ),
    Arm(
        row="R23",
        asserts="independence walks the stamped basis, not the composition",
        sabotage=Sabotage(
            module=_LINEAGE,
            before='        if divergence_state(snapshot, dataset) == "divergent":',
            after="        if False:",
        ),
        checks=("acceptance/test_cut15_lineage.py::test_independence_walks_the_basis_and_not_the_composition",),
    ),
    Arm(
        row="K1",
        asserts="every cross-pair of the run-domain matrix is malformed",
        sabotage=Sabotage(module=_RECIPE, before="    if recipe_v2 != composed:", after="    if False:"),
        checks=(f"{_RUN}::test_every_cross_pair_is_malformed",),
    ),
    Arm(
        row="K2",
        asserts="the recipe's shape is read from its own key, never inferred from the receipt",
        sabotage=Sabotage(
            module=_RECIPE,
            before=(
                '    recipe_v2 = "workflow_definition" in recipe\n'
                '    if recipe_v2 == ("workflow_definition_identity" in recipe):'
            ),
            after=(
                "    recipe_v2 = composed\n"
                '    if ("workflow_definition" in recipe) == ("workflow_definition_identity" in recipe):'
            ),
        ),
        checks=(
            f"{_RUN}::test_every_cross_pair_is_malformed",
            f"{_RUN}::test_the_recipe_shape_is_read_from_its_own_key_never_inferred_from_the_receipt",
        ),
    ),
    Arm(
        row="K3",
        asserts="a v1 recipe is refused rather than given an invented declaration",
        sabotage=Sabotage(
            module=_RUNRECORD,
            before='    if "workflow_definition_identity" in recipe:',
            after="    if False:",
        ),
        checks=(f"{_RUN}::test_decode_run_closure_refuses_a_v1_identity_only_recipe",),
    ),
    Arm(
        row="K4",
        asserts="the job key is canonical text, so no wildcard value can collide",
        sabotage=Sabotage(
            module=_RECIPE,
            before=(
                '    return v1.encode({"rule": rule, "wildcards": {name: value for name, value in wildcards}})'
                '.decode("utf-8")'
            ),
            after='    return rule + "|" + "|".join(f"{name}={value}" for name, value in wildcards)',
        ),
        checks=(f"{_REC}::test_a_wildcard_value_containing_a_separator_cannot_collide",),
    ),
    Arm(
        row="K5",
        asserts="a repeated (job, stream) claim fails inside the job",
        sabotage=Sabotage(
            module=_SEEDS,
            before="            handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)",
            after="            handle = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)",
        ),
        checks=("test_seeds.py::test_a_repeated_claim_fails_inside_the_job_rather_than_overwriting",),
    ),
    Arm(
        row="K6",
        asserts="seed roots are parsed explicitly, whatever the engine coerced them to",
        sabotage=Sabotage(
            module=_SEEDS, before='        if not text.lstrip("-").isdigit():', after="        if False:"
        ),
        checks=("test_seeds.py::test_a_non_integral_root_is_refused_rather_than_coerced",),
    ),
    Arm(
        row="K7",
        asserts="the planning launch touches no execution scratch",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before='    planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))',
            after="    planning_dir = scratch",
        ),
        checks=(f"{_B}::test_the_planning_launch_writes_nothing_into_the_execution_scratch",),
    ),
    Arm(
        row="K8",
        asserts="qualification reads the execution launch's evidence, never the planning launch's",
        sabotage=Sabotage(
            module=_REPLAY,
            before=("    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.execution.capabilities):"),
            after=("    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.planning.capabilities):"),
        ),
        checks=("test_confinement_values.py::test_qualification_reads_the_execution_launch_and_not_the_planning_one",),
    ),
)

_UNIT_OF_LETTERED = {
    "R2a": "R2",
    "R2b": "R2",
    "R2c": "R2",
    **{f"R16{letter}": "R16" for letter in "abcdefghijklm"},
    "R20a": "R20",
    "R20b": "R20",
    "R21a": "R21",
    "R21b": "R21",
    "R21c": "R21",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"R2": 2, "R16": 10, "R20": 2, "R21": 2, "R23": 1}
LABELED_UNITS: tuple[str, ...] = tuple(f"K{number}" for number in range(1, 9))
CO_CITED: dict[str, tuple[str, ...]] = {}
