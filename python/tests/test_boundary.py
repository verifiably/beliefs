"""G2a, R3, R10, R12, R21's boundary arms, T2's in-cell arms,
R16's mint arm, R17's execution halves, R2's execution-level negative.
Deferred: T2's committed-registration and ordering arms (persistence), R12's
boundary-mediated strengthening (tamper log), R21's two-target arm and
negative (d) (full workflow surface), write-outside-root fail-closed and
negative (c)'s clean-environment reachability (confinement)."""

import dataclasses
import inspect
import json
import os
import sys
from pathlib import Path

import pytest
from config_probe import run_config_probe
from fixtures_cut3 import (
    DATA_ADDRESS,
    MEMORY_PORT,
    READS_ADDRESS,
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_NONDETERMINISTIC,
    SNAKEFILE_PRODUCTION,
    SNAKEFILE_SCRATCHY,
    SNAKEFILE_SEED_VIOLATING,
    closure,
    definition,
    recipe,
    seed_plan,
    seeded,
    spec_draft,
    spec_rules,
    stage,
)
from fixtures_cut3 import (
    memory_assessment as run_assessment,
)
from fixtures_cut3 import (
    memory_production as run_production,
)

from beliefs.adapter import (
    LOG_HANDLER_SCRIPT,
    build_argv,
    capture_bundle,
    capture_environment,
    create_scratch_root,
    run_engine,
    validate_entrypoint,
)
from beliefs.boundary import (
    RunMinted,
    RunRefused,
    _render_config,
    build_manifest,
    check_checkpoint_declaration,
    execute_assessment_run,
    execute_production_run,
    mint_run,
    resolve_targets,
)
from beliefs.errors import (
    CheckpointDeclarationUnmet,
    MalformedClosure,
    TargetAmbiguous,
    TargetUnresolvable,
)
from beliefs.recipe import MINIMAL_POLICY, Occurrence, PlannedJob, RunClosure, WorkflowDefinitionSnapshot, job_key
from beliefs.report import ActReport, OperationIntent, RunAttemptEntry, RunRefusal
from beliefs.spec import Deterministic, Seeded, SeedPlan, SpecInput, derive_seed, freeze, revise

CHECKPOINT_DIGEST = "sha256:" + "22" * 32
TARGET_ALL = PlannedJob(job_key("all", ()), "all", (), False)
TARGET_FIT_A = PlannedJob(
    job_key("fit", (("s", "a"),)),
    "fit",
    ("outputs/a.done",),
    False,
)
TARGET_FIT_B = PlannedJob(
    job_key("fit", (("s", "b"),)),
    "fit",
    ("outputs/b.done",),
    False,
)


def test_a_rule_target_resolves_to_the_job_with_no_wildcards() -> None:
    assert resolve_targets(("all",), (TARGET_ALL, TARGET_FIT_A)) == (TARGET_ALL.job_key,)


def test_a_file_target_resolves_to_the_job_that_produces_it() -> None:
    assert resolve_targets(
        ("outputs/a.done",),
        (TARGET_ALL, TARGET_FIT_A, TARGET_FIT_B),
    ) == (TARGET_FIT_A.job_key,)


def test_two_targets_resolve_in_request_order() -> None:
    assert resolve_targets(
        ("outputs/b.done", "outputs/a.done"),
        (TARGET_FIT_A, TARGET_FIT_B),
    ) == (TARGET_FIT_B.job_key, TARGET_FIT_A.job_key)


def test_a_target_the_plan_does_not_name_is_unresolvable() -> None:
    with pytest.raises(TargetUnresolvable):
        resolve_targets(("outputs/zzz.done",), (TARGET_ALL, TARGET_FIT_A))


def test_a_target_matching_two_planned_jobs_is_ambiguous() -> None:
    twin = PlannedJob(
        job_key("copy", ()),
        "copy",
        ("outputs/a.done",),
        False,
    )
    with pytest.raises(TargetAmbiguous):
        resolve_targets(("outputs/a.done",), (TARGET_FIT_A, twin))


def _checkpoint_snapshot(families, expanded):
    return WorkflowDefinitionSnapshot(
        snakefile_digest=CHECKPOINT_DIGEST,
        family_streams=families,
        checkpoint_expanded_families=expanded,
    )


def _planned_checkpoint(family, is_checkpoint=False):
    return PlannedJob(
        job_key=job_key(family, ()),
        family=family,
        outputs=(),
        is_checkpoint=is_checkpoint,
    )


def test_a_checkpoint_declaration_with_no_checkpoint_in_the_plan_is_refused() -> None:
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(
            _checkpoint_snapshot({"fit": ()}, ("fit",)),
            (_planned_checkpoint("fit"),),
        )


def test_a_checkpoint_declaration_for_an_absent_family_is_refused() -> None:
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(
            _checkpoint_snapshot({"fit": ()}, ("absent",)),
            (_planned_checkpoint("split", is_checkpoint=True),),
        )


def test_an_empty_checkpoint_declaration_permits_a_planned_checkpoint() -> None:
    check_checkpoint_declaration(
        _checkpoint_snapshot({"split": ()}, ()),
        (_planned_checkpoint("split", is_checkpoint=True),),
    )


@pytest.mark.parametrize("reserved", ("seed_roots", "seed_derivation_rule"))
@pytest.mark.parametrize("contract", (seeded(), Deterministic()))
def test_seed_config_members_cannot_be_shadowed_by_recipe_parameters(reserved, contract) -> None:
    value = recipe(parameters={reserved: "caller supplied"}, nondeterminism=contract)
    with pytest.raises(MalformedClosure):
        _render_config(value, value.workflow_definition)


def test_an_unsupported_seed_derivation_rule_is_refused_before_launch() -> None:
    value = recipe(
        nondeterminism=Seeded(
            plan=SeedPlan(
                derivation_rule="seed-derivation/future",
                streams=("model-initialization",),
                roots={"root-a": 11},
                stream_roots={"model-initialization": "root-a"},
            )
        )
    )
    with pytest.raises(MalformedClosure):
        _render_config(value, value.workflow_definition)


def test_a_checkpoint_declaration_with_a_planned_checkpoint_is_permitted() -> None:
    check_checkpoint_declaration(
        _checkpoint_snapshot({"split": (), "fit": ()}, ("fit",)),
        (
            _planned_checkpoint("split", is_checkpoint=True),
            _planned_checkpoint("fit"),
        ),
    )


def test_the_roots_are_rendered_as_one_mapping_never_per_stream_keys() -> None:
    config = _render_config(recipe(nondeterminism=seeded()), definition().snapshot())
    assert json.loads(config["seed_roots"]) == {"model-initialization": "11"}
    assert config["seed_derivation_rule"] == "seed-derivation/v1"
    assert not any(key.startswith("seed_model") for key in config)


def test_two_streams_differing_only_in_punctuation_do_not_collide() -> None:
    plan = seed_plan(
        streams=("a-b", "a_b"),
        roots={"r": 11},
        stream_roots={"a-b": "r", "a_b": "r"},
    )
    snapshot = definition(family_streams={"transform": ("a-b", "a_b")}).snapshot()
    config = _render_config(recipe(nondeterminism=Seeded(plan=plan)), snapshot)
    assert json.loads(config["seed_roots"]) == {"a-b": "11", "a_b": "11"}


def test_a_deterministic_recipe_renders_no_seed_material() -> None:
    config = _render_config(
        recipe(nondeterminism=Deterministic()),
        definition(family_streams={}).snapshot(),
    )
    assert "seed_roots" not in config and "seed_derivation_rule" not in config


def test_the_engine_coerces_a_structured_config_value_to_strings(tmp_path) -> None:
    observed = run_config_probe(tmp_path, {"seed_roots": '{"a": 11}', "plain": "11"})
    assert observed["seed_roots"] == ["dict", {"a": "11"}]
    assert observed["plain"] == ["int", 11]


def test_the_planning_launch_writes_nothing_into_the_execution_scratch(tmp_path) -> None:
    outcome = run_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(outcome, RunMinted)
    scratch = Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    planning = Path(outcome.run.occurrence.receipt.planning.scratch_mapping)
    assert scratch.exists() and planning != scratch and not planning.exists()


def test_the_plan_is_carried_by_the_occurrence(tmp_path) -> None:
    outcome = run_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(outcome, RunMinted)
    assert {job.family for job in outcome.run.occurrence.planned} == {"transform"}


def test_an_unknown_target_is_a_planning_refusal_not_a_resolution_one(tmp_path) -> None:
    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_PRODUCTION,
        targets=("outputs/zzz.txt",),
    )
    assert isinstance(outcome, RunRefused)
    assert "plan" in outcome.reason and "target" not in outcome.reason


def test_a_definition_disagreement_refuses_before_a_planning_effect(tmp_path) -> None:
    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_PRODUCTION,
        definition_override=definition(
            snakefile=SNAKEFILE_PRODUCTION,
            family_streams={"transform": ("model-initialization",)},
        ),
    )
    assert isinstance(outcome, RunRefused)
    assert "definition" in outcome.reason
    assert not list((tmp_path / "scratch").glob("planning-*"))


@pytest.fixture(scope="module")
def minted(tmp_path_factory):
    outcome = run_assessment(tmp_path_factory.mktemp("happy"))
    assert isinstance(outcome, RunMinted), outcome
    return outcome


def test_the_boundary_mints_a_run_over_the_held_fixture(minted):
    assert minted.run.recipe.shape == "assessment"
    assert minted.run.result.outputs[0][0] == "outputs/result.txt"
    assert minted.registration.pointer == minted.run.address()


def test_the_recorded_environment_is_the_executing_environment(minted):
    assert minted.run.recipe.environment == capture_environment()


def test_the_boundary_refuses_a_definition_the_entrypoint_does_not_embody(tmp_path):
    code, held = stage(tmp_path, snakefile=SNAKEFILE_DETERMINISTIC)
    mismatched = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_NONDETERMINISTIC),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        actor="tester",
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(mismatched, RunRefused) and mismatched.reason == "definition-mismatch"


# --- G2a / R12 ----------------------------------------------------------------
def test_g2a_a_run_naming_no_frozen_spec_is_refused_not_downgraded(tmp_path):
    outcome = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"
    assert outcome.intent is None and outcome.registration is None
    assert isinstance(outcome.report, ActReport)


def test_g2a_a_spec_frozen_mid_execution_is_refused_not_downgraded(tmp_path):
    draft = spec_draft()
    refused = run_assessment(tmp_path, spec=draft)
    assert isinstance(refused, RunRefused)
    frozen_later = freeze(draft, held_rules=spec_rules())
    assert isinstance(refused, RunRefused)
    assert frozen_later.identity


def test_r12_the_boundary_refuses_a_bare_spec_identity_string(tmp_path):
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    outcome = run_assessment(tmp_path, spec=frozen.identity)
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"


def test_g2a_r12_an_out_of_band_run_with_a_spec_frozen_afterwards_is_undetectable(tmp_path):
    code, _ = stage(tmp_path)
    scratch = create_scratch_root(tmp_path / "s")
    (scratch / "inputs").mkdir()
    (scratch / "inputs" / "data.txt").write_text("hello")
    bundle = tmp_path / "bundle"
    code_id = capture_bundle((code,), bundle)
    entry = validate_entrypoint(bundle, "code/workflow/Snakefile")
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    handler = trace_dir / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    argv = build_argv(
        interpreter=sys.executable,
        snakefile=str(entry),
        directory=str(scratch),
        targets=("outputs/result.txt",),
        config={
            "seed_derivation_rule": "seed-derivation/v1",
            "seed_roots": '{"model-initialization":"7"}',
        },
        log_handler=str(handler),
        cores=1,
        in_process_jobs=False,
    )
    returncode, _ = run_engine(
        argv,
        cwd=scratch,
        env={**os.environ, "SCIENCE_TRACE_FILE": str(trace_dir / "events.jsonl")},
    )
    assert returncode == 0
    spec = freeze(spec_draft(), held_rules=spec_rules())
    attached = closure(recipe=recipe(spec_identity=spec.identity, code_identity=code_id))
    assert attached.address()
    assert "boundary_mediated" not in {f.name for f in dataclasses.fields(RunClosure)}
    assert "boundary_mediated" not in {f.name for f in dataclasses.fields(Occurrence)}


# --- R10 ----------------------------------------------------------------------
def test_r10_a_url_valued_input_is_refused_as_a_run_input(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="https://example.org/series"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"


def test_r10_an_accession_is_refused_and_no_fallback_synthesizes_a_dataset(tmp_path):
    spec = freeze(
        spec_draft(input_roles=(SpecInput(role="observes", dataset="accession:GSE00001"),)),
        held_rules=spec_rules(),
    )
    outcome = run_assessment(tmp_path, spec=spec)
    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-not-a-run"
    assert outcome.report is not None and not hasattr(outcome, "dataset")


# --- R3 (and R2's execution-level negative) -----------------------------------
def test_r3_two_executions_of_one_recipe_are_two_runs(tmp_path):
    first = run_assessment(tmp_path / "a")
    second = run_assessment(tmp_path / "b")
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.recipe.identity() == second.run.recipe.identity()
    assert first.run.address() != second.run.address()
    assert {first.run.address(), second.run.address()} == {
        first.run.address(),
        second.run.address(),
    }


def test_r3_identical_timestamp_actor_and_host_still_yield_distinct_addresses(tmp_path):
    first = run_assessment(
        tmp_path / "a",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-x",
    )
    second = run_assessment(
        tmp_path / "b",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-x",
    )
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    twinned = dataclasses.replace(
        second.run.occurrence,
        started_at=first.run.occurrence.started_at,
        actor=first.run.occurrence.actor,
        host_realization=first.run.occurrence.host_realization,
        trace=first.run.occurrence.trace,
        realized_seeds=first.run.occurrence.realized_seeds,
        receipt=first.run.occurrence.receipt,
    )
    rebuilt = RunClosure(
        recipe=second.run.recipe,
        result=second.run.result,
        occurrence=twinned,
    )
    assert rebuilt.address() != first.run.address()
    assert twinned.event_token != first.run.occurrence.event_token


# --- T2's in-cell arms ---------------------------------------------------------
def test_t2_a_dataset_production_attempt_opens_the_operation_intent(tmp_path):
    outcome = run_production(tmp_path)
    assert isinstance(outcome, RunMinted)
    assert isinstance(outcome.intent, OperationIntent) and outcome.intent.kind == "run-attempt"


def test_t2_negative_b_a_complete_non_conforming_execution_mints_a_run_never_an_act_report(
    tmp_path,
):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)


def test_t2_a_missing_spec_refusal_publishes_an_unfulfilling_report(tmp_path):
    outcome = run_assessment(tmp_path, spec=None.__class__)
    assert isinstance(outcome, RunRefused)
    assert outcome.intent is None
    assert outcome.report is not None
    entry = outcome.report.entries[0]
    assert isinstance(entry, RunAttemptEntry) and entry.subject == "absent"
    assert outcome.registration is None


# --- R21's boundary arms -------------------------------------------------------
def test_r21_manifest_missing_output_mints_no_run(tmp_path):
    code, held = stage(tmp_path)
    spec = freeze(spec_draft(), held_rules=spec_rules())
    outcome = execute_assessment_run(
        spec=spec,
        port=MEMORY_PORT,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs={
            DATA_ADDRESS: held / "data.txt",
            READS_ADDRESS: held / "palette.txt",
        },
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt", "outputs/never-written.txt"),
        actor="tester",
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    assert isinstance(outcome, RunRefused) and outcome.reason.startswith("manifest")
    assert outcome.intent is not None and outcome.report is not None


def test_r21_the_manifest_is_constructed_by_the_boundary_and_no_supplied_path_exists():
    for fn in (execute_assessment_run, execute_production_run):
        params = set(inspect.signature(fn).parameters)
        assert not {"manifest", "outputs", "result"} & params


def test_r21_a_digest_disagreeing_with_the_bytes_on_disk_mints_no_run(tmp_path, minted):
    scratch = create_scratch_root(tmp_path)
    (scratch / "outputs").mkdir()
    (scratch / "outputs" / "result.txt").write_text("HELLO")
    manifest = build_manifest(("outputs/result.txt",), scratch)
    (scratch / "outputs" / "result.txt").write_text("TAMPERED")
    with pytest.raises(MalformedClosure):
        mint_run(minted.run.recipe, manifest, minted.run.occurrence, scratch)


def test_r21_intermediates_are_excluded_and_scratch_files_leave_the_manifest_equal(tmp_path):
    first = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_SCRATCHY)
    second = run_assessment(tmp_path / "b", snakefile=SNAKEFILE_SCRATCHY)
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.result == second.run.result


def test_r21_negative_a_a_scheduling_only_option_leaves_the_recipe_identity_unchanged(tmp_path):
    one = run_assessment(tmp_path / "a", cores=1)
    two = run_assessment(tmp_path / "b", cores=2)
    assert isinstance(one, RunMinted) and isinstance(two, RunMinted)
    assert one.run.recipe.identity() == two.run.recipe.identity()


def test_r21_negative_c_two_differently_mounted_scratch_roots_yield_equal_recipe_identities(
    tmp_path,
):
    a = run_assessment(tmp_path / "mount-a")
    b = run_assessment(tmp_path / "mount-b")
    assert isinstance(a, RunMinted) and isinstance(b, RunMinted)
    assert a.run.recipe.identity() == b.run.recipe.identity()
    assert a.run.occurrence.receipt.execution.scratch_mapping != b.run.occurrence.receipt.execution.scratch_mapping
    import json

    assert a.run.occurrence.receipt.execution.scratch_mapping not in json.dumps(a.run.recipe.identity())


def test_r21_negative_e_the_two_failure_states_are_distinct(tmp_path):
    disobeyed = run_assessment(tmp_path / "a", snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(disobeyed, RunMinted)
    incompletable = run_assessment(
        tmp_path / "b",
        snakefile=SNAKEFILE_NONDETERMINISTIC.replace(
            'output: "outputs/result.txt"',
            'output: "outputs/other.txt"',
        ),
    )
    assert isinstance(incompletable, RunRefused)


# --- R16's mint arm ------------------------------------------------------------
def test_r16_a_seed_violating_execution_still_mints_a_run(tmp_path):
    outcome = run_assessment(tmp_path, snakefile=SNAKEFILE_SEED_VIOLATING)
    assert isinstance(outcome, RunMinted)
    key = job_key("transform", ())
    realized = outcome.run.occurrence.realized_seeds.seeds[key]["model-initialization"]
    assert realized != derive_seed(11, key, "model-initialization")


# --- R17's execution halves ----------------------------------------------------
def test_r17_no_path_supplies_inputs_parameters_or_contract_on_an_assessment_run():
    params = set(inspect.signature(execute_assessment_run).parameters)
    assert (
        not {
            "inputs",
            "parameters",
            "nondeterminism",
            "seed",
            "seeds",
            "root_seed",
            "config",
            "options",
            "environment",
            "env_root",
            "manifest",
        }
        & params
    )


def test_r17_the_boundary_renders_the_configuration_from_the_projected_members(minted):
    rendered = dict(minted.run.occurrence.receipt.execution.rendered_config)
    assert rendered["alpha"] == "0.05"
    assert json.loads(rendered["seed_roots"]) == {"model-initialization": "11"}
    assert rendered["seed_derivation_rule"] == "seed-derivation/v1"


def test_r17_seed_shopping_cannot_occur_at_all(minted):
    successor = revise(
        freeze(spec_draft(), held_rules=spec_rules()),
        edits={
            "nondeterminism": Seeded(
                plan=SeedPlan(
                    derivation_rule="seed-derivation/v1",
                    streams=("model-initialization",),
                    roots={"root-a": 99},
                    stream_roots={"model-initialization": "root-a"},
                )
            )
        },
        held_rules=spec_rules(),
        recorded_failures=frozenset(),
    )
    assert successor.identity != minted.run.recipe.spec_identity
    assert minted.run.recipe.spec_identity == freeze(spec_draft(), held_rules=spec_rules()).identity


def test_r17_a_deleted_or_never_recorded_attempt_is_undetectable(tmp_path):
    refused = run_assessment(tmp_path, spec=spec_draft())
    assert isinstance(refused, RunRefused)
    assert refused.report is not None
    held_records = {refused.report.identity(): refused.report}
    held_records.clear()
    assert held_records == {}


def test_r17_negative_b_a_dataset_production_recipe_is_authored_directly(tmp_path):
    params = set(inspect.signature(execute_production_run).parameters)
    assert {"inputs", "parameters", "nondeterminism"} <= params
    outcome = run_production(tmp_path, nondeterminism=seeded())
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.nondeterminism == seeded()


# --- cut 13: the policy parameter, pre-intent refusals, stable reasons ---------
import dataclasses as _dc

from fixtures_cut3 import replay_of as _replay_of

import beliefs.boundary as _boundary
from beliefs.errors import ClosureUnsupported
from beliefs.recipe import CONFINED_POLICY
from beliefs.replay import replay as _replay


def test_the_boundary_policy_has_no_default_and_no_ambient_constant():
    for fn in (execute_assessment_run, execute_production_run):
        parameter = inspect.signature(fn).parameters["boundary_policy"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert not hasattr(_boundary, "_POLICY")


def test_k1_an_unsupported_policy_refuses_before_intent(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=_dc.replace(CONFINED_POLICY, scope_rule="scope-derivation/v2"))
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "boundary-policy-unsupported"
    assert outcome.intent is None and outcome.registration is None and outcome.report is not None
    assert "scope-derivation/v2" in outcome.detail


def test_a_minimal_run_carries_a_composed_unconfined_receipt(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=MINIMAL_POLICY)
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    assert not receipt.confined and receipt.execution.capabilities == () and receipt.execution.instance is None
    assert outcome.run.recipe.boundary_policy == MINIMAL_POLICY


def test_replay_carries_the_originals_policy_and_takes_none_of_its_own(tmp_path):
    assert "boundary_policy" not in inspect.signature(_replay).parameters
    original = run_assessment(tmp_path / "a")
    replayed = _replay_of(original, tmp_path / "b", port=MEMORY_PORT)
    assert isinstance(original, RunMinted) and isinstance(replayed, RunMinted)
    assert replayed.run.recipe.boundary_policy == original.run.recipe.boundary_policy == MINIMAL_POLICY


def test_a_confinement_refusal_keeps_its_stable_reason_and_its_detail(tmp_path, monkeypatch):
    def unsupported():
        raise ClosureUnsupported("synthetic: SONAME collision")

    monkeypatch.setattr(_boundary, "capture_closure", unsupported)
    outcome = run_assessment(tmp_path)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "closure-unsupported"
    assert outcome.detail == "synthetic: SONAME collision"
    assert outcome.intent is not None  # post-intent: the intent was fulfilled by a refusal
    assert outcome.report is not None
    report_outcome = outcome.report.entries[0].outcome
    assert isinstance(report_outcome, RunRefusal) and report_outcome.missing_member == "closure-unsupported"
